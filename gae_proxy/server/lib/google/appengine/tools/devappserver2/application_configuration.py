#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Stores application configuration taken from e.g. app.yaml, index.yaml."""

# TODO: Support more than just app.yaml.



import datetime
import errno
import logging
import os
import os.path
import random
import string
import threading
import types

from google.appengine.api import appinfo
from google.appengine.api import appinfo_includes
from google.appengine.api import backendinfo
from google.appengine.api import dispatchinfo
from google.appengine.client.services import port_manager
from google.appengine.tools import app_engine_web_xml_parser
from google.appengine.tools import java_quickstart
from google.appengine.tools import queue_xml_parser
from google.appengine.tools import web_xml_parser
from google.appengine.tools import xml_parser_utils
from google.appengine.tools import yaml_translator
from google.appengine.tools.devappserver2 import errors

# Constants passed to functions registered with
# ModuleConfiguration.add_change_callback.
NORMALIZED_LIBRARIES_CHANGED = 1
SKIP_FILES_CHANGED = 2
HANDLERS_CHANGED = 3
INBOUND_SERVICES_CHANGED = 4
ENV_VARIABLES_CHANGED = 5
ERROR_HANDLERS_CHANGED = 6
NOBUILD_FILES_CHANGED = 7






_HEALTH_CHECK_DEFAULTS = {
    'enable_health_check': True,
    'check_interval_sec': 5,
    'timeout_sec': 4,
    'unhealthy_threshold': 2,
    'healthy_threshold': 2,
    'restart_threshold': 60,
    'host': '127.0.0.1'
}


def java_supported():
  """True if this SDK supports running Java apps in the dev appserver."""
  java_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'java')
  return os.path.isdir(java_dir)


class ModuleConfiguration(object):
  """Stores module configuration information.

  Most configuration options are mutable and may change any time
  check_for_updates is called. Client code must be able to cope with these
  changes.

  Other properties are immutable (see _IMMUTABLE_PROPERTIES) and are guaranteed
  to be constant for the lifetime of the instance.
  """

  _IMMUTABLE_PROPERTIES = [
      ('application', 'application'),
      ('version', 'major_version'),
      ('runtime', 'runtime'),
      ('threadsafe', 'threadsafe'),
      ('module', 'module_name'),
      ('basic_scaling', 'basic_scaling'),
      ('manual_scaling', 'manual_scaling'),
      ('automatic_scaling', 'automatic_scaling')]

  def __init__(self, config_path, app_id=None):
    """Initializer for ModuleConfiguration.

    Args:
      config_path: A string containing the full path of the yaml or xml file
          containing the configuration for this module.
      app_id: A string that is the application id, or None if the application id
          from the yaml or xml file should be used.

    Raises:
      errors.DockerfileError: Raised if a user supplied a Dockerfile and a
        non-custom runtime.
    """
    self._config_path = config_path
    self._forced_app_id = app_id
    root = os.path.dirname(config_path)
    self._is_java = os.path.normpath(config_path).endswith(
        os.sep + 'WEB-INF' + os.sep + 'appengine-web.xml')
    if self._is_java:
      # We assume Java's XML-based config files only if config_path is
      # something like /foo/bar/WEB-INF/appengine-web.xml. In this case,
      # the application root is /foo/bar. Other apps, configured with YAML,
      # have something like /foo/bar/app.yaml, with application root /foo/bar.
      root = os.path.dirname(root)
    self._application_root = os.path.realpath(root)
    self._last_failure_message = None

    self._app_info_external, files_to_check = self._parse_configuration(
        self._config_path)

    # TODO: As in AppengineApiClient._CreateVersionResource,
    # add deprecation warnings and remove this code
    if self._app_info_external.service:
      self._app_info_external.module = self._app_info_external.service

    self._mtimes = self._get_mtimes(files_to_check)
    self._application = '%s~%s' % (self.partition,
                                   self.application_external_name)
    self._api_version = self._app_info_external.api_version
    self._module_name = self._app_info_external.module
    self._version = self._app_info_external.version
    self._threadsafe = self._app_info_external.threadsafe
    self._basic_scaling = self._app_info_external.basic_scaling
    self._manual_scaling = self._app_info_external.manual_scaling
    self._automatic_scaling = self._app_info_external.automatic_scaling
    self._runtime = self._app_info_external.runtime
    self._effective_runtime = self._app_info_external.GetEffectiveRuntime()

    dockerfile_dir = os.path.dirname(self._config_path)
    dockerfile = os.path.join(dockerfile_dir, 'Dockerfile')

    if self._effective_runtime != 'custom' and os.path.exists(dockerfile):
      raise errors.DockerfileError(
          'When there is a Dockerfile in the current directory, the only '
          'supported runtime is runtime: custom.  Please switch to runtime: '
          'custom.  The devappserver does not actually use your Dockerfile, so '
          'please use either the --runtime flag to specify the runtime you '
          'want or use the --custom_entrypoint flag to describe how to start '
          'your application.')

    if self._runtime == 'python':
      logging.warning(
          'The "python" runtime specified in "%s" is not supported - the '
          '"python27" runtime will be used instead. A description of the '
          'differences between the two can be found here:\n'
          'https://developers.google.com/appengine/docs/python/python25/diff27',
          self._config_path)
    self._minor_version_id = ''.join(random.choice(string.digits) for _ in
                                     range(18))

    self._forwarded_ports = {}
    if self.runtime == 'vm':
      # Java uses an api_version of 1.0 where everyone else uses just 1.
      # That doesn't matter much elsewhere, but it does pain us with VMs
      # because they recognize api_version 1 not 1.0.
      # TODO: sort out this situation better, probably by changing
      # Java to use 1 like everyone else.
      if self._api_version == '1.0':
        self._api_version = '1'
      vm_settings = self._app_info_external.vm_settings
      ports = None
      if vm_settings:
        ports = vm_settings.get('forwarded_ports')
      if not ports:
        if (self._app_info_external.network and
            self._app_info_external.network.forwarded_ports):
          # Depending on the YAML formatting, these may be strings or ints.
          # Force them to be strings.
          ports = ','.join(
              str(p) for p in self._app_info_external.network.forwarded_ports)
      if ports:
        logging.debug('setting forwarded ports %s', ports)
        pm = port_manager.PortManager()
        pm.Add(ports, 'forwarded')
        self._forwarded_ports = pm.GetAllMappedPorts()['tcp']

    self._translate_configuration_files()

    # vm_health_check is deprecated but it still needs to be taken into account
    # if it is populated.
    if self._app_info_external.health_check is not None:
      health_check = self._app_info_external.health_check
    else:
      health_check = self._app_info_external.vm_health_check

    self._health_check = _set_health_check_defaults(health_check)

  @property
  def application_root(self):
    """The directory containing the application e.g. "/home/user/myapp"."""
    return self._application_root

  @property
  def application(self):
    return self._application

  @property
  def partition(self):
    return 'dev'

  @property
  def application_external_name(self):
    return self._app_info_external.application

  @property
  def api_version(self):
    return self._api_version

  @property
  def module_name(self):
    return self._module_name or appinfo.DEFAULT_MODULE

  @property
  def major_version(self):
    return self._version

  @property
  def minor_version(self):
    return self._minor_version_id

  @property
  def version_id(self):
    if self.module_name == appinfo.DEFAULT_MODULE:
      return '%s.%s' % (
          self.major_version,
          self._minor_version_id)
    else:
      return '%s:%s.%s' % (
          self.module_name,
          self.major_version,
          self._minor_version_id)

  @property
  def env(self):
    return self._app_info_external.env

  @property
  def runtime(self):
    return self._runtime

  @property
  def effective_runtime(self):
    return self._effective_runtime

  @effective_runtime.setter
  def effective_runtime(self, value):
    self._effective_runtime = value

  @property
  def forwarded_ports(self):
    """A dictionary with forwarding rules as host_port => container_port."""
    return self._forwarded_ports

  @property
  def threadsafe(self):
    return self._threadsafe

  @property
  def basic_scaling(self):
    return self._basic_scaling

  @property
  def manual_scaling(self):
    return self._manual_scaling

  @property
  def automatic_scaling(self):
    return self._automatic_scaling

  @property
  def normalized_libraries(self):
    return self._app_info_external.GetNormalizedLibraries()

  @property
  def skip_files(self):
    return self._app_info_external.skip_files

  @property
  def nobuild_files(self):
    return self._app_info_external.nobuild_files

  @property
  def error_handlers(self):
    return self._app_info_external.error_handlers

  @property
  def handlers(self):
    return self._app_info_external.handlers

  @property
  def inbound_services(self):
    return self._app_info_external.inbound_services

  @property
  def env_variables(self):
    return self._app_info_external.env_variables

  @property
  def is_backend(self):
    return False

  @property
  def config_path(self):
    return self._config_path

  @property
  def health_check(self):
    return self._health_check

  def check_for_updates(self):
    """Return any configuration changes since the last check_for_updates call.

    Returns:
      A set containing the changes that occured. See the *_CHANGED module
      constants.
    """
    new_mtimes = self._get_mtimes(self._mtimes.keys())
    if new_mtimes == self._mtimes:
      return set()

    try:
      app_info_external, files_to_check = self._parse_configuration(
          self._config_path)
    except Exception, e:
      failure_message = str(e)
      if failure_message != self._last_failure_message:
        logging.error('Configuration is not valid: %s', failure_message)
      self._last_failure_message = failure_message
      return set()
    self._last_failure_message = None

    self._mtimes = self._get_mtimes(files_to_check)

    for app_info_attribute, self_attribute in self._IMMUTABLE_PROPERTIES:
      app_info_value = getattr(app_info_external, app_info_attribute)
      self_value = getattr(self, self_attribute)
      if (app_info_value == self_value or
          app_info_value == getattr(self._app_info_external,
                                    app_info_attribute)):
        # Only generate a warning if the value is both different from the
        # immutable value *and* different from the last loaded value.
        continue

      if isinstance(app_info_value, types.StringTypes):
        logging.warning('Restart the development module to see updates to "%s" '
                        '["%s" => "%s"]',
                        app_info_attribute,
                        self_value,
                        app_info_value)
      else:
        logging.warning('Restart the development module to see updates to "%s"',
                        app_info_attribute)

    changes = set()
    if (app_info_external.GetNormalizedLibraries() !=
        self.normalized_libraries):
      changes.add(NORMALIZED_LIBRARIES_CHANGED)
    if app_info_external.skip_files != self.skip_files:
      changes.add(SKIP_FILES_CHANGED)
    if app_info_external.nobuild_files != self.nobuild_files:
      changes.add(NOBUILD_FILES_CHANGED)
    if app_info_external.handlers != self.handlers:
      changes.add(HANDLERS_CHANGED)
    if app_info_external.inbound_services != self.inbound_services:
      changes.add(INBOUND_SERVICES_CHANGED)
    if app_info_external.env_variables != self.env_variables:
      changes.add(ENV_VARIABLES_CHANGED)
    if app_info_external.error_handlers != self.error_handlers:
      changes.add(ERROR_HANDLERS_CHANGED)

    self._app_info_external = app_info_external
    if changes:
      self._minor_version_id = ''.join(random.choice(string.digits) for _ in
                                       range(18))
    return changes

  @staticmethod
  def _get_mtimes(filenames):
    filename_to_mtime = {}
    for filename in filenames:
      try:
        filename_to_mtime[filename] = os.path.getmtime(filename)
      except OSError as e:
        # Ignore deleted includes.
        if e.errno != errno.ENOENT:
          raise
    return filename_to_mtime

  def _parse_configuration(self, configuration_path):
    """Parse a configuration file (like app.yaml or appengine-web.xml).

    Args:
      configuration_path: A string containing the full path of the yaml file
          containing the configuration for this module.

    Returns:
      A tuple where the first element is the parsed appinfo.AppInfoExternal
      object and the second element is a list of the paths of the files that
      were used to produce it, namely the input configuration_path and any
      other file that was included from that one.
    """
    if self._is_java:
      config, files = self._parse_java_configuration(configuration_path)
    else:
      with open(configuration_path) as f:
        config, files = appinfo_includes.ParseAndReturnIncludePaths(f)
    if self._forced_app_id:
      config.application = self._forced_app_id

    if config.runtime == 'vm' and not config.version:
      config.version = generate_version_id()
      logging.info('No version specified. Generated version id: %s',
                   config.version)
    return config, [configuration_path] + files

  def _parse_java_configuration(self, app_engine_web_xml_path):
    """Parse appengine-web.xml and web.xml.

    Args:
      app_engine_web_xml_path: A string containing the full path of the
          .../WEB-INF/appengine-web.xml file. The corresponding
          .../WEB-INF/web.xml file must also be present.

    Returns:
      A tuple where the first element is the parsed appinfo.AppInfoExternal
      object and the second element is a list of the paths of the files that
      were used to produce it, namely the input appengine-web.xml file and the
      corresponding web.xml file.
    """
    with open(app_engine_web_xml_path) as f:
      app_engine_web_xml_str = f.read()
    app_engine_web_xml = (
        app_engine_web_xml_parser.AppEngineWebXmlParser().ProcessXml(
            app_engine_web_xml_str))

    quickstart = xml_parser_utils.BooleanValue(
        app_engine_web_xml.beta_settings.get('java_quickstart', 'false'))

    web_inf_dir = os.path.dirname(app_engine_web_xml_path)
    if quickstart:
      app_dir = os.path.dirname(web_inf_dir)
      web_xml_str, web_xml_path = java_quickstart.quickstart_generator(app_dir)
      webdefault_xml_str = java_quickstart.get_webdefault_xml()
      web_xml_str = java_quickstart.remove_mappings(
          web_xml_str, webdefault_xml_str)
    else:
      web_xml_path = os.path.join(web_inf_dir, 'web.xml')
      with open(web_xml_path) as f:
        web_xml_str = f.read()

    has_jsps = False
    for _, _, filenames in os.walk(self.application_root):
      if any(f.endswith('.jsp') for f in filenames):
        has_jsps = True
        break

    web_xml = web_xml_parser.WebXmlParser().ProcessXml(web_xml_str, has_jsps)
    app_yaml_str = yaml_translator.TranslateXmlToYamlForDevAppServer(
        app_engine_web_xml, web_xml, self.application_root)
    config = appinfo.LoadSingleAppInfo(app_yaml_str)
    return config, [app_engine_web_xml_path, web_xml_path]

  def _translate_configuration_files(self):
    """Writes YAML equivalents of certain XML configuration files."""
    # For the most part we translate files in memory rather than writing out
    # translations. But since the task queue stub (taskqueue_stub.py)
    # reads queue.yaml directly rather than being configured with it, we need
    # to write a translation for the stub to find.
    # This means that we won't detect a change to the queue.xml, but we don't
    # currently have logic to react to changes to queue.yaml either.
    web_inf = os.path.join(self._application_root, 'WEB-INF')
    queue_xml_file = os.path.join(web_inf, 'queue.xml')
    if os.path.exists(queue_xml_file):
      appengine_generated = os.path.join(web_inf, 'appengine-generated')
      if not os.path.exists(appengine_generated):
        os.mkdir(appengine_generated)
      queue_yaml_file = os.path.join(appengine_generated, 'queue.yaml')
      with open(queue_xml_file) as f:
        queue_xml = f.read()
      queue_yaml = queue_xml_parser.GetQueueYaml(None, queue_xml)
      with open(queue_yaml_file, 'w') as f:
        f.write(queue_yaml)


def _set_health_check_defaults(health_check):
  """Sets default values for any missing attributes in HealthCheck.

  These defaults need to be kept up to date with the production values in
  health_check.cc

  Args:
    health_check: An instance of appinfo.HealthCheck or None.

  Returns:
    An instance of appinfo.HealthCheck
  """
  if not health_check:
    health_check = appinfo.HealthCheck()
  for k, v in _HEALTH_CHECK_DEFAULTS.iteritems():
    if getattr(health_check, k) is None:
      setattr(health_check, k, v)
  return health_check


class BackendsConfiguration(object):
  """Stores configuration information for a backends.yaml file."""

  def __init__(self, app_config_path, backend_config_path, app_id=None):
    """Initializer for BackendsConfiguration.

    Args:
      app_config_path: A string containing the full path of the yaml file
          containing the configuration for this module.
      backend_config_path: A string containing the full path of the
          backends.yaml file containing the configuration for backends.
      app_id: A string that is the application id, or None if the application id
          from the yaml or xml file should be used.
    """
    self._update_lock = threading.RLock()
    self._base_module_configuration = ModuleConfiguration(
        app_config_path, app_id)
    backend_info_external = self._parse_configuration(
        backend_config_path)

    self._backends_name_to_backend_entry = {}
    for backend in backend_info_external.backends or []:
      self._backends_name_to_backend_entry[backend.name] = backend
      self._changes = dict(
          (backend_name, set())
          for backend_name in self._backends_name_to_backend_entry)

  @staticmethod
  def _parse_configuration(configuration_path):
    # TODO: It probably makes sense to catch the exception raised
    # by Parse() and re-raise it using a module-specific exception.
    with open(configuration_path) as f:
      return backendinfo.LoadBackendInfo(f)

  def get_backend_configurations(self):
    return [BackendConfiguration(self._base_module_configuration, self, entry)
            for entry in self._backends_name_to_backend_entry.values()]

  def check_for_updates(self, backend_name):
    """Return any configuration changes since the last check_for_updates call.

    Args:
      backend_name: A str containing the name of the backend to be checked for
          updates.

    Returns:
      A set containing the changes that occured. See the *_CHANGED module
      constants.
    """
    with self._update_lock:
      module_changes = self._base_module_configuration.check_for_updates()
      if module_changes:
        for backend_changes in self._changes.values():
          backend_changes.update(module_changes)
      changes = self._changes[backend_name]
      self._changes[backend_name] = set()
    return changes


class BackendConfiguration(object):
  """Stores backend configuration information.

  This interface is and must remain identical to ModuleConfiguration.
  """

  def __init__(self, module_configuration, backends_configuration,
               backend_entry):
    """Initializer for BackendConfiguration.

    Args:
      module_configuration: A ModuleConfiguration to use.
      backends_configuration: The BackendsConfiguration that tracks updates for
          this BackendConfiguration.
      backend_entry: A backendinfo.BackendEntry containing the backend
          configuration.
    """
    self._module_configuration = module_configuration
    self._backends_configuration = backends_configuration
    self._backend_entry = backend_entry

    if backend_entry.dynamic:
      self._basic_scaling = appinfo.BasicScaling(
          max_instances=backend_entry.instances or 1)
      self._manual_scaling = None
    else:
      self._basic_scaling = None
      self._manual_scaling = appinfo.ManualScaling(
          instances=backend_entry.instances or 1)
    self._minor_version_id = ''.join(random.choice(string.digits) for _ in
                                     range(18))

  @property
  def application_root(self):
    """The directory containing the application e.g. "/home/user/myapp"."""
    return self._module_configuration.application_root

  @property
  def application(self):
    return self._module_configuration.application

  @property
  def partition(self):
    return self._module_configuration.partition

  @property
  def application_external_name(self):
    return self._module_configuration.application_external_name

  @property
  def api_version(self):
    return self._module_configuration.api_version

  @property
  def module_name(self):
    return self._backend_entry.name

  @property
  def major_version(self):
    return self._module_configuration.major_version

  @property
  def minor_version(self):
    return self._minor_version_id

  @property
  def version_id(self):
    return '%s:%s.%s' % (
        self.module_name,
        self.major_version,
        self._minor_version_id)

  @property
  def env(self):
    return self._module_configuration.env

  @property
  def runtime(self):
    return self._module_configuration.runtime

  @property
  def effective_runtime(self):
    return self._module_configuration.effective_runtime

  @property
  def forwarded_ports(self):
    return self._module_configuration.forwarded_ports

  @property
  def threadsafe(self):
    return self._module_configuration.threadsafe

  @property
  def basic_scaling(self):
    return self._basic_scaling

  @property
  def manual_scaling(self):
    return self._manual_scaling

  @property
  def automatic_scaling(self):
    return None

  @property
  def normalized_libraries(self):
    return self._module_configuration.normalized_libraries

  @property
  def skip_files(self):
    return self._module_configuration.skip_files

  @property
  def nobuild_files(self):
    return self._module_configuration.nobuild_files

  @property
  def error_handlers(self):
    return self._module_configuration.error_handlers

  @property
  def handlers(self):
    if self._backend_entry.start:
      return [appinfo.URLMap(
          url='/_ah/start',
          script=self._backend_entry.start,
          login='admin')] + self._module_configuration.handlers
    return self._module_configuration.handlers

  @property
  def inbound_services(self):
    return self._module_configuration.inbound_services

  @property
  def env_variables(self):
    return self._module_configuration.env_variables

  @property
  def is_backend(self):
    return True

  @property
  def config_path(self):
    return self._module_configuration.config_path

  @property
  def health_check(self):
    return self._module_configuration.health_check

  def check_for_updates(self):
    """Return any configuration changes since the last check_for_updates call.

    Returns:
      A set containing the changes that occured. See the *_CHANGED module
      constants.
    """
    changes = self._backends_configuration.check_for_updates(
        self._backend_entry.name)
    if changes:
      self._minor_version_id = ''.join(random.choice(string.digits) for _ in
                                       range(18))
    return changes


class DispatchConfiguration(object):
  """Stores dispatcher configuration information."""

  def __init__(self, config_path):
    self._config_path = config_path
    self._mtime = os.path.getmtime(self._config_path)
    self._process_dispatch_entries(self._parse_configuration(self._config_path))

  @staticmethod
  def _parse_configuration(configuration_path):
    # TODO: It probably makes sense to catch the exception raised
    # by LoadSingleDispatch() and re-raise it using a module-specific exception.
    with open(configuration_path) as f:
      return dispatchinfo.LoadSingleDispatch(f)

  def check_for_updates(self):
    mtime = os.path.getmtime(self._config_path)
    if mtime > self._mtime:
      self._mtime = mtime
      try:
        dispatch_info_external = self._parse_configuration(self._config_path)
      except Exception, e:
        failure_message = str(e)
        logging.error('Configuration is not valid: %s', failure_message)
        return
      self._process_dispatch_entries(dispatch_info_external)

  def _process_dispatch_entries(self, dispatch_info_external):
    path_only_entries = []
    hostname_entries = []
    for entry in dispatch_info_external.dispatch:
      parsed_url = dispatchinfo.ParsedURL(entry.url)
      if parsed_url.host:
        hostname_entries.append(entry)
      else:
        path_only_entries.append((parsed_url, entry.module))
    if hostname_entries:
      logging.warning(
          'Hostname routing is not supported by the development server. The '
          'following dispatch entries will not match any requests:\n%s',
          '\n\t'.join(str(entry) for entry in hostname_entries))
    self._entries = path_only_entries

  @property
  def dispatch(self):
    return self._entries


class ApplicationConfiguration(object):
  """Stores application configuration information."""

  def __init__(self, config_paths, app_id=None):
    """Initializer for ApplicationConfiguration.

    Args:
      config_paths: A list of strings containing the paths to yaml files,
          or to directories containing them.
      app_id: A string that is the application id, or None if the application id
          from the yaml or xml file should be used.
    Raises:
      InvalidAppConfigError: On invalid configuration.
    """
    self.modules = []
    self.dispatch = None
    # It's really easy to add a test case that passes in a string rather than
    # a list of strings, so guard against that.
    assert not isinstance(config_paths, basestring)
    config_paths = self._config_files_from_paths(config_paths)
    for config_path in config_paths:
      # TODO: add support for backends.xml and dispatch.xml here
      if (config_path.endswith('backends.yaml') or
          config_path.endswith('backends.yml')):
        # TODO: Reuse the ModuleConfiguration created for the app.yaml
        # instead of creating another one for the same file.
        app_yaml = config_path.replace('backends.y', 'app.y')
        self.modules.extend(
            BackendsConfiguration(
                app_yaml, config_path, app_id).get_backend_configurations())
      elif (config_path.endswith('dispatch.yaml') or
            config_path.endswith('dispatch.yml')):
        if self.dispatch:
          raise errors.InvalidAppConfigError(
              'Multiple dispatch.yaml files specified')
        self.dispatch = DispatchConfiguration(config_path)
      else:
        module_configuration = ModuleConfiguration(config_path, app_id)
        self.modules.append(module_configuration)
    application_ids = set(module.application
                          for module in self.modules)
    if len(application_ids) > 1:
      raise errors.InvalidAppConfigError(
          'More than one application ID found: %s' %
          ', '.join(sorted(application_ids)))

    self._app_id = application_ids.pop()
    module_names = set()
    for module in self.modules:
      if module.module_name in module_names:
        raise errors.InvalidAppConfigError('Duplicate module: %s' %
                                           module.module_name)
      module_names.add(module.module_name)
    if self.dispatch:
      if appinfo.DEFAULT_MODULE not in module_names:
        raise errors.InvalidAppConfigError(
            'A default module must be specified.')
      missing_modules = (
          set(module_name for _, module_name in self.dispatch.dispatch) -
          module_names)
      if missing_modules:
        raise errors.InvalidAppConfigError(
            'Modules %s specified in dispatch.yaml are not defined by a yaml '
            'file.' % sorted(missing_modules))

  def _config_files_from_paths(self, config_paths):
    """Return a list of the configuration files found in the given paths.

    For any path that is a directory, the returned list will contain the
    configuration files (app.yaml and optionally backends.yaml) found in that
    directory. If the directory is a Java app (contains a subdirectory
    WEB-INF with web.xml and application-web.xml files), then the returned
    list will contain the path to the application-web.xml file, which is treated
    as if it included web.xml. Paths that are not directories are added to the
    returned list as is.

    Args:
      config_paths: a list of strings that are file or directory paths.

    Returns:
      A list of strings that are file paths.
    """
    config_files = []
    for path in config_paths:
      config_files += (
          self._config_files_from_dir(path) if os.path.isdir(path) else [path])
    return config_files

  def _config_files_from_dir(self, dir_path):
    """Return a list of the configuration files found in the given directory.

    If the directory contains a subdirectory WEB-INF then we expect to find
    web.xml and application-web.xml in that subdirectory. The returned list
    will consist of the path to application-web.xml, which we treat as if it
    included web.xml.

    Otherwise, we expect to find an app.yaml and optionally a backends.yaml,
    and we return those in the list.

    Args:
      dir_path: a string that is the path to a directory.

    Raises:
      AppConfigNotFoundError: If the application configuration is not found.

    Returns:
      A list of strings that are file paths.
    """
    web_inf = os.path.join(dir_path, 'WEB-INF')
    if java_supported() and os.path.isdir(web_inf):
      return self._config_files_from_web_inf_dir(web_inf)
    app_yamls = self._files_in_dir_matching(dir_path, ['app.yaml', 'app.yml'])
    if not app_yamls:
      or_web_inf = ' or a WEB-INF subdirectory' if java_supported() else ''
      raise errors.AppConfigNotFoundError(
          '"%s" is a directory but does not contain app.yaml or app.yml%s' %
          (dir_path, or_web_inf))
    backend_yamls = self._files_in_dir_matching(
        dir_path, ['backends.yaml', 'backends.yml'])
    return app_yamls + backend_yamls

  def _config_files_from_web_inf_dir(self, web_inf):
    required = ['appengine-web.xml', 'web.xml']
    missing = [f for f in required
               if not os.path.exists(os.path.join(web_inf, f))]
    if missing:
      raise errors.AppConfigNotFoundError(
          'The "%s" subdirectory exists but is missing %s' %
          (web_inf, ' and '.join(missing)))
    return [os.path.join(web_inf, required[0])]

  @staticmethod
  def _files_in_dir_matching(dir_path, names):
    abs_names = [os.path.join(dir_path, name) for name in names]
    files = [f for f in abs_names if os.path.exists(f)]
    if len(files) > 1:
      raise errors.InvalidAppConfigError(
          'Directory "%s" contains %s' % (dir_path, ' and '.join(names)))
    return files

  @property
  def app_id(self):
    return self._app_id


def get_app_error_file(module_configuration):
  """Returns application specific file to handle errors.

  Dev AppServer only supports 'default' error code.

  Args:
    module_configuration: ModuleConfiguration.

  Returns:
      A string containing full path to error handler file or
      None if no 'default' error handler is specified.
  """
  for error_handler in module_configuration.error_handlers or []:
    if not error_handler.error_code or error_handler.error_code == 'default':
      return os.path.join(module_configuration.application_root,
                          error_handler.file)
  return None


def generate_version_id(datetime_getter=datetime.datetime.now):
  """Generates a version id based off the current time.

  Args:
    datetime_getter: A function that returns a datetime.datetime instance.

  Returns:
    A version string based.
  """
  return datetime_getter().isoformat().lower().translate(None, ':-')[:15]
