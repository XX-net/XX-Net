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
"""Manage the lifecycle of runtime processes and dispatch requests to them."""



import cgi
import collections
import cStringIO
import functools
import httplib
import logging
import math
import os.path
import random
import re
import string
import threading
import time
import urllib
import urlparse
import wsgiref.headers

from concurrent import futures

from google.appengine.api import api_base_pb
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import appinfo
from google.appengine.api import request_info
from google.appengine.api.logservice import log_service_pb
from google.appengine.tools.devappserver2 import application_configuration
from google.appengine.tools.devappserver2 import blob_image
from google.appengine.tools.devappserver2 import blob_upload
from google.appengine.tools.devappserver2 import channel
from google.appengine.tools.devappserver2 import constants
from google.appengine.tools.devappserver2 import endpoints
from google.appengine.tools.devappserver2 import errors
from google.appengine.tools.devappserver2 import file_watcher
from google.appengine.tools.devappserver2 import gcs_server
from google.appengine.tools.devappserver2 import http_proxy
from google.appengine.tools.devappserver2 import http_runtime
from google.appengine.tools.devappserver2 import http_runtime_constants
from google.appengine.tools.devappserver2 import instance
from google.appengine.tools.devappserver2 import login
from google.appengine.tools.devappserver2 import request_rewriter
from google.appengine.tools.devappserver2 import runtime_config_pb2
from google.appengine.tools.devappserver2 import runtime_factories
from google.appengine.tools.devappserver2 import start_response_utils
from google.appengine.tools.devappserver2 import static_files_handler
from google.appengine.tools.devappserver2 import thread_executor
from google.appengine.tools.devappserver2 import url_handler
from google.appengine.tools.devappserver2 import util
from google.appengine.tools.devappserver2 import wsgi_handler
from google.appengine.tools.devappserver2 import wsgi_server


_LOWER_HEX_DIGITS = string.hexdigits.lower()
_UPPER_HEX_DIGITS = string.hexdigits.upper()
_REQUEST_ID_HASH_LENGTH = 8

_THREAD_POOL = thread_executor.ThreadExecutor()
_RESTART_INSTANCES_CONFIG_CHANGES = frozenset(
    [application_configuration.NORMALIZED_LIBRARIES_CHANGED,
     application_configuration.SKIP_FILES_CHANGED,
     application_configuration.NOBUILD_FILES_CHANGED,
     # The server must be restarted when the handlers change because files
     # appearing in static content handlers make them unavailable to the
     # runtime.
     application_configuration.HANDLERS_CHANGED,
     application_configuration.ENV_VARIABLES_CHANGED])

_REQUEST_LOGGING_BLACKLIST_RE = re.compile(
    r'^/_ah/(?:channel/(?:dev|jsapi)|img|login|upload)')

# Fake arguments for _handle_script_request for request types that don't use
# user-specified handlers.
_EMPTY_MATCH = re.match('', '')
_DUMMY_URLMAP = appinfo.URLMap(script='/')
_SHUTDOWN_TIMEOUT = 30

_MAX_UPLOAD_MEGABYTES = 32
_MAX_UPLOAD_BYTES = _MAX_UPLOAD_MEGABYTES * 1024 * 1024
_MAX_UPLOAD_NO_TRIGGER_BAD_CLIENT_BYTES = 64 * 1024 * 1024

_REDIRECT_HTML = '''\
<HTML><HEAD><meta http-equiv="content-type" content="%(content-type)s">
<TITLE>%(status)d Moved</TITLE></HEAD>
<BODY><H1>%(status)d Moved</H1>
The document has moved'
<A HREF="%(correct-url)s">here</A>.
</BODY></HTML>'''

_TIMEOUT_HTML = '<HTML><BODY>503 - This request has timed out.</BODY></HTML>'

# Factor applied to the request timeouts to compensate for the
# long vmengines reloads. TODO eventually remove that once we have
# optimized the vm_engine reload.
_VMENGINE_SLOWDOWN_FACTOR = 2

# polling time on module changes.
_CHANGE_POLLING_MS = 1000

# specific resources prefixes we don't want to see pollute the info level on
# access.
_QUIETER_RESOURCES = ('/_ah/health',)

# TODO: Remove after the Files API is really gone.
_FILESAPI_DEPRECATION_WARNING_PYTHON = (
    'The Files API is deprecated and will soon be removed. Further information'
    ' is available here: https://cloud.google.com/appengine/docs/deprecations'
    '/files_api')
_FILESAPI_DEPRECATION_WARNING_JAVA = (
    'The Files API is deprecated and will soon be removed. Further information'
    ' is available here: https://cloud.google.com/appengine/docs/deprecations'
    '/files_api')
_FILESAPI_DEPRECATION_WARNING_GO = (
    'The Files API is deprecated and will soon be removed. Further information'
    ' is available here: https://cloud.google.com/appengine/docs/deprecations'
    '/files_api')

_ALLOWED_RUNTIMES_ENV2 = (
    'python-compat', 'java', 'java7', 'go', 'custom')

def _static_files_regex_from_handlers(handlers):
  patterns = []
  for url_map in handlers:
    handler_type = url_map.GetHandlerType()
    if url_map.application_readable:
      continue
    if handler_type == appinfo.STATIC_FILES:
      patterns.append(r'(%s)' % url_map.upload)
    elif handler_type == appinfo.STATIC_DIR:
      patterns.append('(%s%s%s)' % (url_map.static_dir.rstrip(os.path.sep),
                                    re.escape(os.path.sep), r'.*'))
  return r'^%s$' % '|'.join(patterns)


class InteractiveCommandError(errors.Error):
  pass


class _ScriptHandler(url_handler.UserConfiguredURLHandler):
  """A URL handler that will cause the request to be dispatched to an instance.

  This handler is special in that it does not have a working handle() method
  since the Module's dispatch logic is used to select the appropriate Instance.
  """

  def __init__(self, url_map):
    """Initializer for _ScriptHandler.

    Args:
      url_map: An appinfo.URLMap instance containing the configuration for this
          handler.
    """
    try:
      url_pattern = re.compile('%s$' % url_map.url)
    except re.error, e:
      raise errors.InvalidAppConfigError(
          'invalid url %r in script handler: %s' % (url_map.url, e))

    super(_ScriptHandler, self).__init__(url_map, url_pattern)
    self.url_map = url_map

  def handle(self, match, environ, start_response):
    """This is a dummy method that should never be called."""
    raise NotImplementedError()


class Module(object):
  """The abstract base for all instance pool implementations."""

  _MAX_REQUEST_WAIT_TIME = 10

  def _get_wait_time(self):
    """Gets the wait time before timing out a request.

    Returns:
      The timeout value in seconds.
    """
    return self._MAX_REQUEST_WAIT_TIME

  def _create_instance_factory(self,
                               module_configuration):
    """Create an instance.InstanceFactory.

    Args:
      module_configuration: An application_configuration.ModuleConfiguration
          instance storing the configuration data for a module.

    Returns:
      A instance.InstanceFactory subclass that can be used to create instances
      with the provided configuration.

    Raises:
      RuntimeError: if the configuration specifies an unknown runtime.
      errors.InvalidAppConfigError: if using removed runtimes for env: 2
    """
    runtime = module_configuration.runtime
    if runtime == 'vm':
      runtime = module_configuration.effective_runtime
      # NOTE(bryanmau): b/24139391
      # If in env: 2, users either use a compat runtime or custom.
      if module_configuration.env == '2':
        if runtime not in _ALLOWED_RUNTIMES_ENV2:
          raise errors.InvalidAppConfigError(
              'In env: 2, only the following runtimes '
              'are allowed: {0}'.format(allowed_runtimes))

    if runtime not in runtime_factories.FACTORIES:
      raise RuntimeError(
          'Unknown runtime %r; supported runtimes are %s.' %
          (runtime,
           ', '.join(
               sorted(repr(k) for k in runtime_factories.FACTORIES))))
    instance_factory = runtime_factories.FACTORIES[runtime]
    return instance_factory(
        request_data=self._request_data,
        runtime_config_getter=self._get_runtime_config,
        module_configuration=module_configuration)

  def _create_url_handlers(self):
    """Constructs URLHandlers based on the module configuration.

    Returns:
      A list of url_handler.URLHandlers corresponding that can react as
      described in the given configuration.
    """
    handlers = []
    # Add special URL handlers (taking precedence over user-defined handlers)
    url_pattern = '/%s$' % login.LOGIN_URL_RELATIVE
    handlers.append(wsgi_handler.WSGIHandler(login.application,
                                             url_pattern))
    url_pattern = '/%s' % blob_upload.UPLOAD_URL_PATH
    # The blobstore upload handler forwards successful requests to the
    # dispatcher.
    handlers.append(
        wsgi_handler.WSGIHandler(blob_upload.Application(self._dispatcher),
                                 url_pattern))

    url_pattern = '/%s' % blob_image.BLOBIMAGE_URL_PATTERN
    handlers.append(
        wsgi_handler.WSGIHandler(blob_image.Application(), url_pattern))

    url_pattern = '/%s' % channel.CHANNEL_URL_PATTERN
    handlers.append(
        wsgi_handler.WSGIHandler(channel.application, url_pattern))

    url_pattern = '/%s' % gcs_server.GCS_URL_PATTERN
    handlers.append(
        wsgi_handler.WSGIHandler(gcs_server.Application(), url_pattern))

    url_pattern = '/%s' % endpoints.API_SERVING_PATTERN
    handlers.append(
        wsgi_handler.WSGIHandler(
            endpoints.EndpointsDispatcher(self._dispatcher), url_pattern))

    found_start_handler = False
    found_warmup_handler = False
    # Add user-defined URL handlers
    for url_map in self._module_configuration.handlers:
      handler_type = url_map.GetHandlerType()
      if handler_type == appinfo.HANDLER_SCRIPT:
        handlers.append(_ScriptHandler(url_map))
        if not found_start_handler and re.match('%s$' % url_map.url,
                                                '/_ah/start'):
          found_start_handler = True
        if not found_warmup_handler and re.match('%s$' % url_map.url,
                                                 '/_ah/warmup'):
          found_warmup_handler = True
      elif handler_type == appinfo.STATIC_FILES:
        handlers.append(
            static_files_handler.StaticFilesHandler(
                self._module_configuration.application_root,
                url_map))
      elif handler_type == appinfo.STATIC_DIR:
        handlers.append(
            static_files_handler.StaticDirHandler(
                self._module_configuration.application_root,
                url_map))
      else:
        assert 0, 'unexpected handler %r for %r' % (handler_type, url_map)
    # Add a handler for /_ah/start if no script handler matches.
    if not found_start_handler:
      handlers.insert(0, _ScriptHandler(self._instance_factory.START_URL_MAP))
    # Add a handler for /_ah/warmup if no script handler matches and warmup is
    # enabled.
    if (not found_warmup_handler and
        'warmup' in (self._module_configuration.inbound_services or [])):
      handlers.insert(0, _ScriptHandler(self._instance_factory.WARMUP_URL_MAP))
    return handlers

  def _get_runtime_config(self):
    """Returns the configuration for the runtime.

    Returns:
      A runtime_config_pb2.Config instance representing the configuration to be
      passed to an instance. NOTE: This does *not* include the instance_id
      field, which must be populated elsewhere.
    """
    runtime_config = runtime_config_pb2.Config()
    runtime_config.app_id = self._module_configuration.application
    runtime_config.version_id = self._module_configuration.version_id
    if self._threadsafe_override is None:
      runtime_config.threadsafe = self._module_configuration.threadsafe or False
    else:
      runtime_config.threadsafe = self._threadsafe_override
    runtime_config.application_root = (
        self._module_configuration.application_root)
    if not self._allow_skipped_files:
      runtime_config.skip_files = str(self._module_configuration.skip_files)
      runtime_config.static_files = _static_files_regex_from_handlers(
          self._module_configuration.handlers)
    runtime_config.api_host = self._api_host
    runtime_config.api_port = self._api_port
    runtime_config.server_port = self._balanced_port
    runtime_config.stderr_log_level = self._runtime_stderr_loglevel
    runtime_config.datacenter = 'us1'
    runtime_config.auth_domain = self._auth_domain
    if self._max_instances is not None:
      runtime_config.max_instances = self._max_instances

    for library in self._module_configuration.normalized_libraries:
      runtime_config.libraries.add(name=library.name, version=library.version)

    for key, value in (self._module_configuration.env_variables or {}).items():
      runtime_config.environ.add(key=str(key), value=str(value))

    if self._cloud_sql_config:
      runtime_config.cloud_sql_config.CopyFrom(self._cloud_sql_config)

    if (self._php_config and
        self._module_configuration.runtime.startswith('php')):
      runtime_config.php_config.CopyFrom(self._php_config)
    if (self._python_config and
        self._module_configuration.runtime.startswith('python')):
      runtime_config.python_config.CopyFrom(self._python_config)
    if (self._java_config and
        (self._module_configuration.runtime.startswith('java') or
         self._module_configuration.effective_runtime.startswith('java'))):
      runtime_config.java_config.CopyFrom(self._java_config)

    if self._vm_config:
      runtime_config.vm_config.CopyFrom(self._vm_config)
      if self._module_configuration.effective_runtime == 'custom':
        runtime_config.custom_config.CopyFrom(self._custom_config)

    runtime_config.vm = self._module_configuration.runtime == 'vm'

    return runtime_config

  def _maybe_restart_instances(self, config_changed, file_changed):
    """Restarts instances. May avoid some restarts depending on policy.

    If neither config_changed or file_changed is True, returns immediately.

    Args:
      config_changed: True if the configuration for the application has changed.
      file_changed: True if any file relevant to the application has changed.
    """
    if not config_changed and not file_changed:
      return

    logging.debug('Restarting instances.')
    policy = self._instance_factory.FILE_CHANGE_INSTANCE_RESTART_POLICY
    assert policy is not None, 'FILE_CHANGE_INSTANCE_RESTART_POLICY not set'

    with self._condition:
      instances_to_quit = set()
      for inst in self._instances:
        if (config_changed or
            (policy == instance.ALWAYS) or
            (policy == instance.AFTER_FIRST_REQUEST and inst.total_requests)):
          instances_to_quit.add(inst)
      self._instances -= instances_to_quit

    for inst in instances_to_quit:
      inst.quit(allow_async=True)

  def _handle_changes(self, timeout=0):
    """Handle file or configuration changes."""
    # Check for file changes first, because they can trigger config changes.
    file_changes = self._watcher.changes(timeout)
    if file_changes:
      logging.info(
          '[%s] Detected file changes:\n  %s', self.name,
          '\n  '.join(sorted(file_changes)))
      self._instance_factory.files_changed()

    # Always check for config and file changes because checking also clears
    # pending changes.
    config_changes = self._module_configuration.check_for_updates()
    if application_configuration.HANDLERS_CHANGED in config_changes:
      handlers = self._create_url_handlers()
      with self._handler_lock:
        self._handlers = handlers

    if config_changes & _RESTART_INSTANCES_CONFIG_CHANGES:
      self._instance_factory.configuration_changed(config_changes)

    self._maybe_restart_instances(
        config_changed=bool(config_changes & _RESTART_INSTANCES_CONFIG_CHANGES),
        file_changed=bool(file_changes))

  def __init__(self,
               module_configuration,
               host,
               balanced_port,
               api_host,
               api_port,
               auth_domain,
               runtime_stderr_loglevel,
               php_config,
               python_config,
               java_config,
               custom_config,
               cloud_sql_config,
               vm_config,
               default_version_port,
               port_registry,
               request_data,
               dispatcher,
               max_instances,
               use_mtime_file_watcher,
               automatic_restarts,
               allow_skipped_files,
               threadsafe_override):
    """Initializer for Module.
    Args:
      module_configuration: An application_configuration.ModuleConfiguration
          instance storing the configuration data for a module.
      host: A string containing the host that any HTTP servers should bind to
          e.g. "localhost".
      balanced_port: An int specifying the port where the balanced module for
          the pool should listen.
      api_host: The host that APIModule listens for RPC requests on.
      api_port: The port that APIModule listens for RPC requests on.
      auth_domain: A string containing the auth domain to set in the environment
          variables.
      runtime_stderr_loglevel: An int reprenting the minimum logging level at
          which runtime log messages should be written to stderr. See
          devappserver2.py for possible values.
      php_config: A runtime_config_pb2.PhpConfig instances containing PHP
          runtime-specific configuration. If None then defaults are used.
      python_config: A runtime_config_pb2.PythonConfig instance containing
          Python runtime-specific configuration. If None then defaults are used.
      java_config: A runtime_config_pb2.JavaConfig instance containing
          Java runtime-specific configuration. If None then defaults are used.
      custom_config: A runtime_config_pb2.CustomConfig instance. If 'runtime'
          is set then we switch to another runtime.  Otherwise, we use the
          custom_entrypoint to start the app.  If neither or both are set,
          then we will throw an error.
      cloud_sql_config: A runtime_config_pb2.CloudSQL instance containing the
          required configuration for local Google Cloud SQL development. If None
          then Cloud SQL will not be available.
      vm_config: A runtime_config_pb2.VMConfig instance containing
          VM runtime-specific configuration. If None all docker-related stuff
          is disabled.
      default_version_port: An int containing the port of the default version.
      port_registry: A dispatcher.PortRegistry used to provide the Dispatcher
          with a mapping of port to Module and Instance.
      request_data: A wsgi_request_info.WSGIRequestInfo that will be provided
          with request information for use by API stubs.
      dispatcher: A Dispatcher instance that can be used to make HTTP requests.
      max_instances: The maximum number of instances to create for this module.
          If None then there is no limit on the number of created instances.
      use_mtime_file_watcher: A bool containing whether to use mtime polling to
          monitor file changes even if other options are available on the
          current platform.
      automatic_restarts: If True then instances will be restarted when a
          file or configuration change that effects them is detected.
      allow_skipped_files: If True then all files in the application's directory
          are readable, even if they appear in a static handler or "skip_files"
          directive.
      threadsafe_override: If not None, ignore the YAML file value of threadsafe
          and use this value instead.

    Raises:
      errors.InvalidAppConfigError: For runtime: custom, either mistakenly set
        both --custom_entrypoint and --runtime or neither.
    """
    self._module_configuration = module_configuration
    self._name = module_configuration.module_name
    self._version = module_configuration.major_version
    self._app_name_external = module_configuration.application_external_name
    self._host = host
    self._api_host = api_host
    self._api_port = api_port
    self._auth_domain = auth_domain
    self._runtime_stderr_loglevel = runtime_stderr_loglevel
    self._balanced_port = balanced_port
    self._php_config = php_config
    self._python_config = python_config
    self._java_config = java_config
    self._custom_config = custom_config
    self._cloud_sql_config = cloud_sql_config
    self._vm_config = vm_config
    self._request_data = request_data
    self._allow_skipped_files = allow_skipped_files
    self._threadsafe_override = threadsafe_override
    self._dispatcher = dispatcher
    self._max_instances = max_instances
    self._automatic_restarts = automatic_restarts
    self._use_mtime_file_watcher = use_mtime_file_watcher
    self._default_version_port = default_version_port
    self._port_registry = port_registry

    if self.effective_runtime == 'custom':
      if self._custom_config.runtime and self._custom_config.custom_entrypoint:
        raise errors.InvalidAppConfigError(
            'Cannot set both --runtime and --custom_entrypoint.')
      elif self._custom_config.runtime:
        actual_runtime = self._custom_config.runtime
        self._module_configuration.effective_runtime = actual_runtime
      elif not self._custom_config.custom_entrypoint:
        raise errors.InvalidAppConfigError(
            'Must set either --runtime or --custom_entrypoint.  For a '
            'standard runtime, set the --runtime flag with one of %s.  '
            'For a custom runtime, set the --custom_entrypoint with a '
            'command to start your app.' % runtime_factories.valid_runtimes())

    self._instance_factory = self._create_instance_factory(
        self._module_configuration)
    if self._automatic_restarts:
      self._watcher = file_watcher.get_file_watcher(
          [self._module_configuration.application_root] +
          self._instance_factory.get_restart_directories(),
          self._use_mtime_file_watcher)
    else:
      self._watcher = None
    self._handler_lock = threading.Lock()
    self._handlers = self._create_url_handlers()
    self._balanced_module = wsgi_server.WsgiServer(
        (self._host, self._balanced_port), self)
    self._quit_event = threading.Event()  # Set when quit() has been called.

    # TODO: Remove after the Files API is really gone.
    if self._module_configuration.runtime.startswith('python'):
      self._filesapi_warning_message = _FILESAPI_DEPRECATION_WARNING_PYTHON
    elif self._module_configuration.runtime.startswith('java'):
      self._filesapi_warning_message = _FILESAPI_DEPRECATION_WARNING_JAVA
    elif self._module_configuration.runtime.startswith('go'):
      self._filesapi_warning_message = _FILESAPI_DEPRECATION_WARNING_GO
    else:
      self._filesapi_warning_message = None

  @property
  def name(self):
    """The name of the module, as defined in app.yaml.

    This value will be constant for the lifetime of the module even if the
    module configuration changes.
    """
    return self._name

  @property
  def version(self):
    """The version of the module, as defined in app.yaml.

    This value will be constant for the lifetime of the module even if the
    module configuration changes.
    """
    return self._version

  @property
  def app_name_external(self):
    """The external application name of the module, as defined in app.yaml.

    This value will be constant for the lifetime of the module even if the
    module configuration changes.
    """
    return self._app_name_external

  @property
  def ready(self):
    """The module is ready to handle HTTP requests."""
    return self._balanced_module.ready

  @property
  def balanced_port(self):
    """The port that the balanced HTTP server for the Module is listening on."""
    assert self._balanced_module.ready, 'balanced module not running'
    return self._balanced_module.port

  @property
  def host(self):
    """The host that the HTTP server(s) for this Module is listening on."""
    return self._host

  @property
  def balanced_address(self):
    """The address of the balanced HTTP server e.g. "localhost:8080"."""
    if self.balanced_port != 80:
      return '%s:%s' % (self.host, self.balanced_port)
    else:
      return self.host

  @property
  def max_instance_concurrent_requests(self):
    """The number of concurrent requests that each Instance can handle."""
    return self._instance_factory.max_concurrent_requests

  @property
  def module_configuration(self):
    """The application_configuration.ModuleConfiguration for this module."""
    return self._module_configuration

  @property
  def runtime(self):
    """Runtime property for this module."""
    return self._module_configuration.runtime

  @property
  def effective_runtime(self):
    """Effective_runtime property for this module."""
    return self._module_configuration.effective_runtime

  @property
  def mvm_logs_enabled(self):
    """Returns True iff it's a Managed VM module and logs are enabled."""
    return self._vm_config and self._vm_config.enable_logs

  @property
  def supports_interactive_commands(self):
    """True if the module can evaluate arbitrary code and return the result."""
    return self._instance_factory.SUPPORTS_INTERACTIVE_REQUESTS

  def _handle_script_request(self,
                             environ,
                             start_response,
                             url_map,
                             match,
                             inst=None):
    """Handles a HTTP request that has matched a script handler.

    Args:
      environ: An environ dict for the request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.
      url_map: An appinfo.URLMap instance containing the configuration for the
          handler that matched.
      match: A re.MatchObject containing the result of the matched URL pattern.
      inst: The Instance to send the request to. If None then an appropriate
          Instance will be chosen.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    raise NotImplementedError()

  def _no_handler_for_request(self, environ, start_response, request_id):
    """Handle a HTTP request that does not match any user-defined handlers."""
    self._insert_log_message('No handlers matched this URL.', 2, request_id)
    start_response('404 Not Found', [('Content-Type', 'text/html')])
    return [
        '<html><head><title>Not Found</title></head>',
        ('<body>The url "%s" does not match any handlers.</body></html>' %
         cgi.escape(environ['PATH_INFO']))
    ]

  def _error_response(self, environ, start_response, status, body=None):
    if body:
      start_response(
          '%d %s' % (status, httplib.responses[status]),
          [('Content-Type', 'text/html'),
           ('Content-Length', str(len(body)))])
      return body
    start_response('%d %s' % (status, httplib.responses[status]), [])
    return []

  def _handle_request(self, environ, start_response, inst=None,
                      request_type=instance.NORMAL_REQUEST):
    """Handles a HTTP request.

    Args:
      environ: An environ dict for the request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.
      inst: The Instance to send the request to. If None then an appropriate
          Instance will be chosen. Setting inst is not meaningful if the
          request does not match a "script" handler.
      request_type: The type of the request. See instance.*_REQUEST module
          constants.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    if inst:
      try:
        environ['SERVER_PORT'] = str(self.get_instance_port(inst.instance_id))
      except request_info.NotSupportedWithAutoScalingError:
        environ['SERVER_PORT'] = str(self.balanced_port)
    else:
      environ['SERVER_PORT'] = str(self.balanced_port)
    if 'HTTP_HOST' in environ:
      environ['SERVER_NAME'] = environ['HTTP_HOST'].split(':', 1)[0]
    environ['DEFAULT_VERSION_HOSTNAME'] = '%s:%s' % (
        environ['SERVER_NAME'], self._default_version_port)

    runtime_config = self._get_runtime_config()
    # Python monkey-patches out os.environ because some environment variables
    # are set per-request (REQUEST_ID_HASE and REQUEST_LOG_ID for example).
    # This means that although these environment variables could be set once
    # at startup, they must be passed in during each request.
    if (runtime_config.vm and
        self._module_configuration.effective_runtime == 'python27'):
      environ.update(http_runtime.get_vm_environment_variables(
          self._module_configuration, runtime_config))

    with self._request_data.request(
        environ,
        self._module_configuration) as request_id:
      should_log_request = not _REQUEST_LOGGING_BLACKLIST_RE.match(
          environ['PATH_INFO'])
      environ['REQUEST_ID_HASH'] = self.generate_request_id_hash()
      if should_log_request:
        environ['REQUEST_LOG_ID'] = self.generate_request_log_id()
        if 'HTTP_HOST' in environ:
          hostname = environ['HTTP_HOST']
        elif environ['SERVER_PORT'] == '80':
          hostname = environ['SERVER_NAME']
        else:
          hostname = '%s:%s' % (environ['SERVER_NAME'], environ['SERVER_PORT'])

        if environ.get('QUERY_STRING'):
          resource = '%s?%s' % (urllib.quote(environ['PATH_INFO']),
                                environ['QUERY_STRING'])
        else:
          resource = urllib.quote(environ['PATH_INFO'])
        email, _, _ = login.get_user_info(environ.get('HTTP_COOKIE', ''))
        method = environ.get('REQUEST_METHOD', 'GET')
        http_version = environ.get('SERVER_PROTOCOL', 'HTTP/1.0')

        logservice = apiproxy_stub_map.apiproxy.GetStub('logservice')
        logservice.start_request(
            request_id=request_id,
            user_request_id=environ['REQUEST_LOG_ID'],
            ip=environ.get('REMOTE_ADDR', ''),
            app_id=self._module_configuration.application,
            version_id=self._module_configuration.major_version,
            nickname=email.split('@', 1)[0],
            user_agent=environ.get('HTTP_USER_AGENT', ''),
            host=hostname,
            method=method,
            resource=resource,
            http_version=http_version,
            module=self._module_configuration.module_name)

      def wrapped_start_response(status, response_headers, exc_info=None):
        response_headers.append(('Server',
                                 http_runtime_constants.SERVER_SOFTWARE))
        if should_log_request:
          headers = wsgiref.headers.Headers(response_headers)
          status_code = int(status.split(' ', 1)[0])
          content_length = int(headers.get('Content-Length', 0))
          # TODO: Remove after the Files API is really gone.
          if (self._filesapi_warning_message is not None
              and self._request_data.was_filesapi_used(request_id)):
            logging.warning(self._filesapi_warning_message)
            self._insert_log_message(self._filesapi_warning_message,
                                     2, request_id)
          logservice.end_request(request_id, status_code, content_length)
          if any(resource.startswith(prefix) for prefix in _QUIETER_RESOURCES):
            level = logging.DEBUG
          else:
            level = logging.INFO
          logging.log(level, '%(module_name)s: '
                      '"%(method)s %(resource)s %(http_version)s" '
                      '%(status)d %(content_length)s',
                      {'module_name': self.name,
                       'method': method,
                       'resource': resource,
                       'http_version': http_version,
                       'status': status_code,
                       'content_length': content_length or '-'})
        return start_response(status, response_headers, exc_info)

      content_length = int(environ.get('CONTENT_LENGTH', '0'))

      if (environ['REQUEST_METHOD'] in ('GET', 'HEAD', 'DELETE', 'TRACE') and
          content_length != 0):
        # CONTENT_LENGTH may be empty or absent.
        wrapped_start_response('400 Bad Request', [])
        return ['"%s" requests may not contain bodies.' %
                environ['REQUEST_METHOD']]

      # Do not apply request limits to internal _ah handlers (known to break
      # blob uploads).
      # TODO: research if _ah handlers need limits.
      if (not environ.get('REQUEST_URI', '/').startswith('/_ah/') and
          content_length > _MAX_UPLOAD_BYTES):
        # As allowed by the RFC, cherrypy closes the connection for 413 errors.
        # Most clients do not handle this correctly and treat the page as
        # unavailable if the connection is closed before the client can send
        # all the data. To match the behavior of production, for large files
        # < 64M read the data to prevent the client bug from being triggered.







        if content_length <= _MAX_UPLOAD_NO_TRIGGER_BAD_CLIENT_BYTES:
          environ['wsgi.input'].read(content_length)
        status = '%d %s' % (httplib.REQUEST_ENTITY_TOO_LARGE,
                            httplib.responses[httplib.REQUEST_ENTITY_TOO_LARGE])
        wrapped_start_response(status, [])
        return ['Upload limited to %d megabytes.' % _MAX_UPLOAD_MEGABYTES]

      with self._handler_lock:
        handlers = self._handlers

      try:
        path_info = environ['PATH_INFO']
        path_info_normal = self._normpath(path_info)
        if path_info_normal != path_info:
          # While a 301 Moved Permanently makes more sense for non-normal
          # paths, prod issues a 302 so we do the same.
          return self._redirect_302_path_info(path_info_normal,
                                              environ,
                                              wrapped_start_response)
        if request_type in (instance.BACKGROUND_REQUEST,
                            instance.INTERACTIVE_REQUEST,
                            instance.SHUTDOWN_REQUEST):
          app = functools.partial(self._handle_script_request,
                                  url_map=_DUMMY_URLMAP,
                                  match=_EMPTY_MATCH,
                                  request_id=request_id,
                                  inst=inst,
                                  request_type=request_type)
          return request_rewriter.frontend_rewriter_middleware(app)(
              environ, wrapped_start_response)
        for handler in handlers:
          match = handler.match(path_info)
          if match:
            auth_failure = handler.handle_authorization(environ,
                                                        wrapped_start_response)
            if auth_failure is not None:
              return auth_failure

            if isinstance(handler, _ScriptHandler):
              app = functools.partial(self._handle_script_request,
                                      url_map=handler.url_map,
                                      match=match,
                                      request_id=request_id,
                                      inst=inst,
                                      request_type=request_type)
              return request_rewriter.frontend_rewriter_middleware(app)(
                  environ, wrapped_start_response)
            else:
              ret = handler.handle(match, environ, wrapped_start_response)
              if ret is not None:
                return ret
        return self._no_handler_for_request(environ, wrapped_start_response,
                                            request_id)
      except StandardError, e:
        if logging.getLogger('').isEnabledFor(logging.DEBUG):
          logging.exception('Request to %r failed', path_info)
        else:
          logging.error('Request to %r failed', path_info)
        wrapped_start_response('500 Internal Server Error', [], e)
        return []

  def _async_shutdown_instance(self, inst, port):
    return _THREAD_POOL.submit(self._shutdown_instance, inst, port)

  def _shutdown_instance(self, inst, port):
    force_shutdown_time = time.time() + _SHUTDOWN_TIMEOUT
    try:
      environ = self.build_request_environ(
          'GET', '/_ah/stop', [], '', '0.1.0.3', port, fake_login=True)
      self._handle_request(environ,
                           start_response_utils.null_start_response,
                           inst=inst,
                           request_type=instance.SHUTDOWN_REQUEST)
      logging.debug('Sent shutdown request: %s', inst)
    except:
      logging.exception('Internal error while handling shutdown request.')
    finally:
      time_to_wait = force_shutdown_time - time.time()
      self._quit_event.wait(time_to_wait)
      inst.quit(force=True)

  @staticmethod
  def _quote_querystring(qs):
    """Quote a query string to protect against XSS."""

    parsed_qs = urlparse.parse_qs(qs, keep_blank_values=True)
    # urlparse.parse returns a dictionary with values as lists while
    # urllib.urlencode does not handle those. Expand to a list of
    # key values.
    expanded_qs = []
    for key, multivalue in parsed_qs.items():
      for value in multivalue:
        expanded_qs.append((key, value))
    return urllib.urlencode(expanded_qs)

  def _redirect_302_path_info(self, updated_path_info, environ, start_response):
    """Redirect to an updated path.

    Respond to the current request with a 302 Found status with an updated path
    but preserving the rest of the request.

    Notes:
    - WSGI does not make the fragment available so we are not able to preserve
      it. Luckily prod does not preserve the fragment so it works out.

    Args:
      updated_path_info: the new HTTP path to redirect to.
      environ: WSGI environ object.
      start_response: WSGI start response callable.

    Returns:
      WSGI-compatible iterable object representing the body of the response.
    """
    correct_url = urlparse.urlunsplit(
        (environ['wsgi.url_scheme'],
         environ['HTTP_HOST'],
         urllib.quote(updated_path_info),
         self._quote_querystring(environ['QUERY_STRING']),
         None))

    content_type = 'text/html; charset=utf-8'
    output = _REDIRECT_HTML % {
        'content-type': content_type,
        'status': httplib.FOUND,
        'correct-url': correct_url
    }

    start_response('%d %s' % (httplib.FOUND, httplib.responses[httplib.FOUND]),
                   [('Content-Type', content_type),
                    ('Location', correct_url),
                    ('Content-Length', str(len(output)))])
    return output

  @staticmethod
  def _normpath(path):
    """Normalize the path by handling . and .. directory entries.

    Normalizes the path. A directory entry of . is just dropped while a
    directory entry of .. removes the previous entry. Note that unlike
    os.path.normpath, redundant separators remain in place to match prod.

    Args:
      path: an HTTP path.

    Returns:
      A normalized HTTP path.
    """
    normalized_path_entries = []
    for entry in path.split('/'):
      if entry == '..':
        if normalized_path_entries:
          normalized_path_entries.pop()
      elif entry != '.':
        normalized_path_entries.append(entry)
    return '/'.join(normalized_path_entries)

  def _insert_log_message(self, message, level, request_id):
    logs_group = log_service_pb.UserAppLogGroup()
    log_line = logs_group.add_log_line()
    log_line.set_timestamp_usec(int(time.time() * 1e6))
    log_line.set_level(level)
    log_line.set_message(message)
    request = log_service_pb.FlushRequest()
    request.set_logs(logs_group.Encode())
    response = api_base_pb.VoidProto()
    logservice = apiproxy_stub_map.apiproxy.GetStub('logservice')
    logservice._Dynamic_Flush(request, response, request_id)

  @staticmethod
  def generate_request_log_id():
    """Generate a random REQUEST_LOG_ID.

    Returns:
      A string suitable for use as a REQUEST_LOG_ID. The returned string is
      variable length to emulate the production values, which encapsulate
      the application id, version and some log state.
    """
    return ''.join(random.choice(_LOWER_HEX_DIGITS)
                   for _ in range(random.randrange(30, 100)))

  @staticmethod
  def generate_request_id_hash():
    """Generate a random REQUEST_ID_HASH."""
    return ''.join(random.choice(_UPPER_HEX_DIGITS)
                   for _ in range(_REQUEST_ID_HASH_LENGTH))

  def set_num_instances(self, instances):
    """Sets the number of instances for this module to run.

    Args:
      instances: An int containing the number of instances to run.
    Raises:
      request_info.NotSupportedWithAutoScalingError: Always.
    """
    raise request_info.NotSupportedWithAutoScalingError()

  def get_num_instances(self):
    """Returns the number of instances for this module to run."""
    raise request_info.NotSupportedWithAutoScalingError()

  def suspend(self):
    """Stops the module from serving requests."""
    raise request_info.NotSupportedWithAutoScalingError()

  def resume(self):
    """Restarts the module."""
    raise request_info.NotSupportedWithAutoScalingError()

  def get_instance_address(self, instance_id):
    """Returns the address of the HTTP server for an instance."""
    return '%s:%s' % (self.host, self.get_instance_port(instance_id))

  def get_instance_port(self, instance_id):
    """Returns the port of the HTTP server for an instance."""
    raise request_info.NotSupportedWithAutoScalingError()

  def get_instance(self, instance_id):
    """Returns the instance with the provided instance ID."""
    raise request_info.NotSupportedWithAutoScalingError()

  @property
  def supports_individually_addressable_instances(self):
    return False

  def create_interactive_command_module(self):
    """Returns a InteractiveCommandModule that can be sent user commands."""
    if self._instance_factory.SUPPORTS_INTERACTIVE_REQUESTS:
      return InteractiveCommandModule(self._module_configuration,
                                      self._host,
                                      self._balanced_port,
                                      self._api_host,
                                      self._api_port,
                                      self._auth_domain,
                                      self._runtime_stderr_loglevel,
                                      self._php_config,
                                      self._python_config,
                                      self._java_config,
                                      self._custom_config,
                                      self._cloud_sql_config,
                                      self._vm_config,
                                      self._default_version_port,
                                      self._port_registry,
                                      self._request_data,
                                      self._dispatcher,
                                      self._use_mtime_file_watcher,
                                      self._allow_skipped_files,
                                      self._threadsafe_override)
    else:
      raise NotImplementedError('runtime does not support interactive commands')

  def build_request_environ(self, method, relative_url, headers, body,
                            source_ip, port, fake_login=False):
    if isinstance(body, unicode):
      body = body.encode('ascii')

    url = urlparse.urlsplit(relative_url)
    if port != 80:
      host = '%s:%s' % (self.host, port)
    else:
      host = self.host
    environ = {constants.FAKE_IS_ADMIN_HEADER: '1',
               'CONTENT_LENGTH': str(len(body)),
               'PATH_INFO': url.path,
               'QUERY_STRING': url.query,
               'REQUEST_METHOD': method,
               'REMOTE_ADDR': source_ip,
               'SERVER_NAME': self.host,
               'SERVER_PORT': str(port),
               'SERVER_PROTOCOL': 'HTTP/1.1',
               'wsgi.version': (1, 0),
               'wsgi.url_scheme': 'http',
               'wsgi.errors': cStringIO.StringIO(),
               'wsgi.multithread': True,
               'wsgi.multiprocess': True,
               'wsgi.input': cStringIO.StringIO(body)}
    if fake_login:
      environ[constants.FAKE_LOGGED_IN_HEADER] = '1'
    util.put_headers_in_environ(headers, environ)
    environ['HTTP_HOST'] = host
    return environ


class AutoScalingModule(Module):
  """A pool of instances that is autoscaled based on traffic."""

  # The minimum number of seconds to wait, after quitting an idle instance,
  # before quitting another idle instance.
  _MIN_SECONDS_BETWEEN_QUITS = 60
  # The time horizon to use when calculating the number of instances required
  # to serve the current level of traffic.
  _REQUIRED_INSTANCE_WINDOW_SECONDS = 60

  _DEFAULT_AUTOMATIC_SCALING = appinfo.AutomaticScaling(
      min_pending_latency='0.1s',
      max_pending_latency='0.5s',
      min_idle_instances=1,
      max_idle_instances=1000)

  @staticmethod
  def _parse_pending_latency(timing):
    """Parse a pending latency string into a float of the value in seconds.

    Args:
      timing: A str of the form 1.0s or 1000ms.

    Returns:
      A float representation of the value in seconds.
    """
    if timing.endswith('ms'):
      return float(timing[:-2]) / 1000
    else:
      return float(timing[:-1])

  @classmethod
  def _populate_default_automatic_scaling(cls, automatic_scaling):
    for attribute in automatic_scaling.ATTRIBUTES:
      if getattr(automatic_scaling, attribute) in ('automatic', None):
        setattr(automatic_scaling, attribute,
                getattr(cls._DEFAULT_AUTOMATIC_SCALING, attribute))

  def _process_automatic_scaling(self, automatic_scaling):
    if automatic_scaling:
      self._populate_default_automatic_scaling(automatic_scaling)
    else:
      automatic_scaling = self._DEFAULT_AUTOMATIC_SCALING
    self._min_pending_latency = self._parse_pending_latency(
        automatic_scaling.min_pending_latency)
    self._max_pending_latency = self._parse_pending_latency(
        automatic_scaling.max_pending_latency)
    self._min_idle_instances = int(automatic_scaling.min_idle_instances)
    self._max_idle_instances = int(automatic_scaling.max_idle_instances)

  def __init__(self, **kwargs):
    """Initializer for AutoScalingModule.

    Args:
      **kwargs: Arguments to forward to Module.__init__.
    """
    kwargs['vm_config'] = None
    super(AutoScalingModule, self).__init__(**kwargs)

    self._process_automatic_scaling(
        self._module_configuration.automatic_scaling)

    self._instances = set()  # Protected by self._condition.
    # A deque containg (time, num_outstanding_instance_requests) 2-tuples.
    # This is used to track the maximum number of outstanding requests in a time
    # period. Protected by self._condition.
    self._outstanding_request_history = collections.deque()
    self._num_outstanding_instance_requests = 0  # Protected by self._condition.
    # The time when the last instance was quit in seconds since the epoch.
    self._last_instance_quit_time = 0  # Protected by self._condition.

    self._condition = threading.Condition()  # Protects instance state.
    self._instance_adjustment_thread = threading.Thread(
        target=self._loop_adjusting_instances,
        name='Instance Adjustment')

  def start(self):
    """Start background management of the Module."""
    self._balanced_module.start()
    self._port_registry.add(self.balanced_port, self, None)
    if self._watcher:
      self._watcher.start()
    self._instance_adjustment_thread.start()

  def quit(self):
    """Stops the Module."""
    self._quit_event.set()
    self._instance_adjustment_thread.join()
    # The instance adjustment thread depends on the balanced module and the
    # watcher so wait for it exit before quitting them.
    if self._watcher:
      self._watcher.quit()
    self._balanced_module.quit()
    with self._condition:
      instances = self._instances
      self._instances = set()
      self._condition.notify_all()
    for inst in instances:
      inst.quit(force=True)

  @property
  def instances(self):
    """A set of all the instances currently in the Module."""
    with self._condition:
      return set(self._instances)

  @property
  def num_outstanding_instance_requests(self):
    """The number of requests that instances are currently handling."""
    with self._condition:
      return self._num_outstanding_instance_requests

  def _handle_instance_request(self,
                               environ,
                               start_response,
                               url_map,
                               match,
                               request_id,
                               inst,
                               request_type):
    """Handles a request routed a particular Instance.

    Args:
      environ: An environ dict for the request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.
      url_map: An appinfo.URLMap instance containing the configuration for the
          handler that matched.
      match: A re.MatchObject containing the result of the matched URL pattern.
      request_id: A unique string id associated with the request.
      inst: The instance.Instance to send the request to.
      request_type: The type of the request. See instance.*_REQUEST module
          constants.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    if request_type != instance.READY_REQUEST:
      with self._condition:
        self._num_outstanding_instance_requests += 1
        self._outstanding_request_history.append(
            (time.time(), self.num_outstanding_instance_requests))
    try:
      logging.debug('Dispatching request to %s', inst)
      return inst.handle(environ, start_response, url_map, match, request_id,
                         request_type)
    finally:
      with self._condition:
        if request_type != instance.READY_REQUEST:
          self._num_outstanding_instance_requests -= 1
        self._condition.notify()

  def _handle_script_request(self,
                             environ,
                             start_response,
                             url_map,
                             match,
                             request_id,
                             inst=None,
                             request_type=instance.NORMAL_REQUEST):
    """Handles a HTTP request that has matched a script handler.

    Args:
      environ: An environ dict for the request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.
      url_map: An appinfo.URLMap instance containing the configuration for the
          handler that matched.
      match: A re.MatchObject containing the result of the matched URL pattern.
      request_id: A unique string id associated with the request.
      inst: The instance.Instance to send the request to. If None then an
          appropriate instance.Instance will be chosen.
      request_type: The type of the request. See instance.*_REQUEST module
          constants.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    if inst is not None:
      return self._handle_instance_request(
          environ, start_response, url_map, match, request_id, inst,
          request_type)

    with self._condition:
      self._num_outstanding_instance_requests += 1
      self._outstanding_request_history.append(
          (time.time(), self.num_outstanding_instance_requests))

    try:
      start_time = time.time()
      timeout_time = start_time + self._min_pending_latency
      # Loop until an instance is available to handle the request.
      while True:
        if self._quit_event.is_set():
          return self._error_response(environ, start_response, 404)
        inst = self._choose_instance(timeout_time)
        if not inst:
          inst = self._add_instance(permit_warmup=False)
          if not inst:
            # No instance is available nor can a new one be created, so loop
            # waiting for one to be free.
            timeout_time = time.time() + 0.2
            continue

        try:
          logging.debug('Dispatching request to %s after %0.4fs pending',
                        inst, time.time() - start_time)
          return inst.handle(environ,
                             start_response,
                             url_map,
                             match,
                             request_id,
                             request_type)
        except instance.CannotAcceptRequests:
          continue
    finally:
      with self._condition:
        self._num_outstanding_instance_requests -= 1
        self._condition.notify()

  def _add_instance(self, permit_warmup):
    """Creates and adds a new instance.Instance to the Module.

    Args:
      permit_warmup: If True then the new instance.Instance will be sent a new
          warmup request if it is configured to receive them.

    Returns:
      The newly created instance.Instance. Returns None if no new instance
      could be created because the maximum number of instances have already
      been created.
    """
    if self._max_instances is not None:
      with self._condition:
        if len(self._instances) >= self._max_instances:
          return None

    perform_warmup = permit_warmup and (
        'warmup' in (self._module_configuration.inbound_services or []))

    inst = self._instance_factory.new_instance(
        self.generate_instance_id(),
        expect_ready_request=perform_warmup)

    with self._condition:
      if self._quit_event.is_set():
        return None
      self._instances.add(inst)

    if not inst.start():
      return None

    if perform_warmup:
      self._async_warmup(inst)
    else:
      with self._condition:
        self._condition.notify(self.max_instance_concurrent_requests)
    logging.debug('Created instance: %s', inst)
    return inst

  @staticmethod
  def generate_instance_id():
    return ''.join(random.choice(_LOWER_HEX_DIGITS) for _ in range(36))

  def _warmup(self, inst):
    """Send a warmup request to the given instance."""

    try:
      environ = self.build_request_environ(
          'GET', '/_ah/warmup', [], '', '0.1.0.3', self.balanced_port,
          fake_login=True)
      self._handle_request(environ,
                           start_response_utils.null_start_response,
                           inst=inst,
                           request_type=instance.READY_REQUEST)
      with self._condition:
        self._condition.notify(self.max_instance_concurrent_requests)
    except:
      logging.exception('Internal error while handling warmup request.')

  def _async_warmup(self, inst):
    """Asynchronously send a markup request to the given Instance."""
    return _THREAD_POOL.submit(self._warmup, inst)

  def _trim_outstanding_request_history(self):
    """Removes obsolete entries from _outstanding_request_history."""
    window_start = time.time() - self._REQUIRED_INSTANCE_WINDOW_SECONDS
    with self._condition:
      while self._outstanding_request_history:
        t, _ = self._outstanding_request_history[0]
        if t < window_start:
          self._outstanding_request_history.popleft()
        else:
          break

  def _get_num_required_instances(self):
    """Returns the number of Instances required to handle the request load."""
    with self._condition:
      self._trim_outstanding_request_history()
      if not self._outstanding_request_history:
        return 0
      else:
        peak_concurrent_requests = max(
            current_requests
            for (t, current_requests)
            in self._outstanding_request_history)
        return int(math.ceil(peak_concurrent_requests /
                             self.max_instance_concurrent_requests))

  def _split_instances(self):
    """Returns a 2-tuple representing the required and extra Instances.

    Returns:
      A 2-tuple of (required_instances, not_required_instances):
        required_instances: The set of the instance.Instances, in a state that
                            can handle requests, required to handle the current
                            request load.
        not_required_instances: The set of the Instances contained in this
                                Module that not are not required.
    """
    with self._condition:
      num_required_instances = self._get_num_required_instances()

      available = [inst for inst in self._instances
                   if inst.can_accept_requests]
      available.sort(key=lambda inst: -inst.num_outstanding_requests)

      required = set(available[:num_required_instances])
      return required, self._instances - required

  def _choose_instance(self, timeout_time):
    """Returns the best Instance to handle a request or None if all are busy."""
    with self._condition:
      while time.time() < timeout_time:
        required_instances, not_required_instances = self._split_instances()
        if required_instances:
          # Pick the instance with the most remaining capacity to handle
          # requests.
          required_instances = sorted(
              required_instances,
              key=lambda inst: inst.remaining_request_capacity)
          if required_instances[-1].remaining_request_capacity:
            return required_instances[-1]

        available_instances = [inst for inst in not_required_instances
                               if inst.remaining_request_capacity > 0 and
                               inst.can_accept_requests]
        if available_instances:
          # Pick the instance with the *least* capacity to handle requests
          # to avoid using unnecessary idle instances.
          available_instances.sort(
              key=lambda instance: instance.num_outstanding_requests)
          return available_instances[-1]
        else:
          self._condition.wait(timeout_time - time.time())
    return None

  def _adjust_instances(self):
    """Creates new Instances or deletes idle Instances based on current load."""
    now = time.time()
    with self._condition:
      _, not_required_instances = self._split_instances()

    if len(not_required_instances) < self._min_idle_instances:
      self._add_instance(permit_warmup=True)
    elif (len(not_required_instances) > self._max_idle_instances and
          now >
          (self._last_instance_quit_time + self._MIN_SECONDS_BETWEEN_QUITS)):
      for inst in not_required_instances:
        if not inst.num_outstanding_requests:
          try:
            inst.quit()
          except instance.CannotQuitServingInstance:
            pass
          else:
            self._last_instance_quit_time = now
            logging.debug('Quit instance: %s', inst)
            with self._condition:
              self._instances.discard(inst)
              break

  def _loop_adjusting_instances(self):
    """Loops until the Module exits, reloading, adding or removing Instances."""
    while not self._quit_event.is_set():
      if self.ready:
        if self._automatic_restarts:
          self._handle_changes(_CHANGE_POLLING_MS)
        else:
          time.sleep(_CHANGE_POLLING_MS/1000.0)
        self._adjust_instances()

  def __call__(self, environ, start_response):
    return self._handle_request(environ, start_response)


class ManualScalingModule(Module):
  """A pool of instances that is manually-scaled."""

  _DEFAULT_MANUAL_SCALING = appinfo.ManualScaling(instances='1')

  @classmethod
  def _populate_default_manual_scaling(cls, manual_scaling):
    for attribute in manual_scaling.ATTRIBUTES:
      if getattr(manual_scaling, attribute) in ('manual', None):
        setattr(manual_scaling, attribute,
                getattr(cls._DEFAULT_MANUAL_SCALING, attribute))

  def _process_manual_scaling(self, manual_scaling):
    if manual_scaling:
      self._populate_default_manual_scaling(manual_scaling)
    else:
      manual_scaling = self._DEFAULT_MANUAL_SCALING
    self._initial_num_instances = int(manual_scaling.instances)

  def __init__(self, **kwargs):
    """Initializer for ManualScalingModule.

    Args:
      **kwargs: Arguments to forward to Module.__init__.
    """
    super(ManualScalingModule, self).__init__(**kwargs)

    self._process_manual_scaling(self._module_configuration.manual_scaling)

    self._instances = []  # Protected by self._condition.
    self._wsgi_servers = []  # Protected by self._condition.
    # Whether the module has been stopped. Protected by self._condition.
    self._suspended = False

    self._condition = threading.Condition()  # Protects instance state.

    # Serializes operations that modify the serving state of or number of
    # instances.
    self._instances_change_lock = threading.RLock()

    self._change_watcher_thread = threading.Thread(
        target=self._loop_watching_for_changes, name='Change Watcher')

  def start(self):
    """Start background management of the Module."""
    self._balanced_module.start()
    self._port_registry.add(self.balanced_port, self, None)
    if self._watcher:
      self._watcher.start()
    self._change_watcher_thread.start()
    with self._instances_change_lock:
      if self._max_instances is not None:
        initial_num_instances = min(self._max_instances,
                                    self._initial_num_instances)
      else:
        initial_num_instances = self._initial_num_instances
      for _ in xrange(initial_num_instances):
        self._add_instance()

  def quit(self):
    """Stops the Module."""
    self._quit_event.set()
    # The instance adjustment thread depends on the balanced module and the
    # watcher so wait for it exit before quitting them.
    if self._watcher:
      self._watcher.quit()
    self._change_watcher_thread.join()
    self._balanced_module.quit()
    for wsgi_servr in self._wsgi_servers:
      wsgi_servr.quit()
    with self._condition:
      instances = self._instances
      self._instances = []
      self._condition.notify_all()
    for inst in instances:
      inst.quit(force=True)

  def get_instance_port(self, instance_id):
    """Returns the port of the HTTP server for an instance."""
    try:
      instance_id = int(instance_id)
    except ValueError:
      raise request_info.InvalidInstanceIdError()
    with self._condition:
      if 0 <= instance_id < len(self._instances):
        wsgi_servr = self._wsgi_servers[instance_id]
      else:
        raise request_info.InvalidInstanceIdError()
    return wsgi_servr.port

  @property
  def instances(self):
    """A set of all the instances currently in the Module."""
    with self._condition:
      return set(self._instances)

  def _handle_instance_request(self,
                               environ,
                               start_response,
                               url_map,
                               match,
                               request_id,
                               inst,
                               request_type):
    """Handles a request routed a particular Instance.

    Args:
      environ: An environ dict for the request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.
      url_map: An appinfo.URLMap instance containing the configuration for the
          handler that matched.
      match: A re.MatchObject containing the result of the matched URL pattern.
      request_id: A unique string id associated with the request.
      inst: The instance.Instance to send the request to.
      request_type: The type of the request. See instance.*_REQUEST module
          constants.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    start_time = time.time()
    timeout_time = start_time + self._get_wait_time()
    try:
      while time.time() < timeout_time:
        logging.debug('Dispatching request to %s after %0.4fs pending',
                      inst, time.time() - start_time)
        try:
          return inst.handle(environ, start_response, url_map, match,
                             request_id, request_type)
        except instance.CannotAcceptRequests:
          pass
        inst.wait(timeout_time)
        if inst.has_quit:
          return self._error_response(environ, start_response, 503)
      else:
        return self._error_response(environ, start_response, 503)
    finally:
      with self._condition:
        self._condition.notify()

  def _handle_script_request(self,
                             environ,
                             start_response,
                             url_map,
                             match,
                             request_id,
                             inst=None,
                             request_type=instance.NORMAL_REQUEST):
    """Handles a HTTP request that has matched a script handler.

    Args:
      environ: An environ dict for the request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.
      url_map: An appinfo.URLMap instance containing the configuration for the
          handler that matched.
      match: A re.MatchObject containing the result of the matched URL pattern.
      request_id: A unique string id associated with the request.
      inst: The instance.Instance to send the request to. If None then an
          appropriate instance.Instance will be chosen.
      request_type: The type of the request. See instance.*_REQUEST module
          constants.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    if ((request_type in (instance.NORMAL_REQUEST, instance.READY_REQUEST) and
         self._suspended) or self._quit_event.is_set()):
      return self._error_response(environ, start_response, 404)
    if self._module_configuration.is_backend:
      environ['BACKEND_ID'] = self._module_configuration.module_name
    else:
      environ['BACKEND_ID'] = (
          self._module_configuration.version_id.split('.', 1)[0])

    if inst is not None:
      return self._handle_instance_request(
          environ, start_response, url_map, match, request_id, inst,
          request_type)

    start_time = time.time()
    timeout_time = start_time + self._get_wait_time()

    while time.time() < timeout_time:
      if ((request_type in (instance.NORMAL_REQUEST, instance.READY_REQUEST) and
           self._suspended) or self._quit_event.is_set()):
        return self._error_response(environ, start_response, 404)
      inst = self._choose_instance(timeout_time)
      if inst:
        try:
          logging.debug('Dispatching request to %s after %0.4fs pending',
                        inst, time.time() - start_time)
          return inst.handle(environ, start_response, url_map, match,
                             request_id, request_type)
        except instance.CannotAcceptRequests:
          continue
        finally:
          with self._condition:
            self._condition.notify()
    else:
      return self._error_response(environ, start_response, 503, _TIMEOUT_HTML)

  def _add_instance(self):
    """Creates and adds a new instance.Instance to the Module.

    This must be called with _instances_change_lock held.
    """
    instance_id = self.get_num_instances()
    assert self._max_instances is None or instance_id < self._max_instances
    inst = self._instance_factory.new_instance(instance_id,
                                               expect_ready_request=True)
    wsgi_servr = wsgi_server.WsgiServer(
        (self._host, 0), functools.partial(self._handle_request, inst=inst))
    wsgi_servr.start()
    self._port_registry.add(wsgi_servr.port, self, inst)

    with self._condition:
      if self._quit_event.is_set():
        return
      self._wsgi_servers.append(wsgi_servr)
      self._instances.append(inst)
      suspended = self._suspended
    if not suspended:
      self._async_start_instance(wsgi_servr, inst)

  def _async_start_instance(self, wsgi_servr, inst):
    return _THREAD_POOL.submit(self._start_instance, wsgi_servr, inst)

  def _start_instance(self, wsgi_servr, inst):
    try:
      if not inst.start():
        return
    except:
      logging.exception('Internal error while starting instance.')
      raise

    logging.debug('Started instance: %s at http://%s:%s', inst, self.host,
                  wsgi_servr.port)
    logging.info('New instance for module "%s" serving on:\nhttp://%s\n',
                 self.name, self.balanced_address)
    try:
      environ = self.build_request_environ(
          'GET', '/_ah/start', [], '', '0.1.0.3', wsgi_servr.port,
          fake_login=True)
      self._handle_request(environ,
                           start_response_utils.null_start_response,
                           inst=inst,
                           request_type=instance.READY_REQUEST)
      logging.debug('Sent start request: %s', inst)
      with self._condition:
        self._condition.notify(self.max_instance_concurrent_requests)
    except Exception, e:  # pylint: disable=broad-except
      logging.exception('Internal error while handling start request: %s', e)

  def _choose_instance(self, timeout_time):
    """Returns an Instance to handle a request or None if all are busy."""
    with self._condition:
      while time.time() < timeout_time:
        for inst in self._instances:
          if inst.can_accept_requests:
            return inst
        self._condition.wait(timeout_time - time.time())
      return None

  def _handle_changes(self, timeout=0):
    """Handle file or configuration changes."""
    # Always check for config and file changes because checking also clears
    # pending changes.
    config_changes = self._module_configuration.check_for_updates()
    if application_configuration.HANDLERS_CHANGED in config_changes:
      handlers = self._create_url_handlers()
      with self._handler_lock:
        self._handlers = handlers

    file_changes = self._watcher.changes(timeout)
    if file_changes:
      logging.info(
          '[%s] Detected file changes:\n  %s', self.name,
          '\n  '.join(sorted(file_changes)))
      self._instance_factory.files_changed()

    if config_changes & _RESTART_INSTANCES_CONFIG_CHANGES:
      self._instance_factory.configuration_changed(config_changes)

    if config_changes & _RESTART_INSTANCES_CONFIG_CHANGES or file_changes:
      with self._instances_change_lock:
        if not self._suspended:
          self.restart()

  def _loop_watching_for_changes(self):
    """Loops until the InstancePool is done watching for file changes."""
    while not self._quit_event.is_set():
      if self.ready:
        if self._automatic_restarts:
          self._handle_changes(_CHANGE_POLLING_MS)
        else:
          time.sleep(_CHANGE_POLLING_MS/1000.0)

  def get_num_instances(self):
    with self._instances_change_lock:
      with self._condition:
        return len(self._instances)

  def set_num_instances(self, instances):
    if self._max_instances is not None:
      instances = min(instances, self._max_instances)

    with self._instances_change_lock:
      with self._condition:
        running_instances = self.get_num_instances()
        if running_instances > instances:
          wsgi_servers_to_quit = self._wsgi_servers[instances:]
          del self._wsgi_servers[instances:]
          instances_to_quit = self._instances[instances:]
          del self._instances[instances:]
      if running_instances < instances:
        for _ in xrange(instances - running_instances):
          self._add_instance()
    if running_instances > instances:
      for inst, wsgi_servr in zip(instances_to_quit, wsgi_servers_to_quit):
        self._async_quit_instance(inst, wsgi_servr)

  def _async_quit_instance(self, inst, wsgi_servr):
    return _THREAD_POOL.submit(self._quit_instance, inst, wsgi_servr)

  def _quit_instance(self, inst, wsgi_servr):
    port = wsgi_servr.port
    wsgi_servr.quit()
    inst.quit(expect_shutdown=True)
    self._shutdown_instance(inst, port)

  def suspend(self):
    """Suspends serving for this module, quitting all running instances."""
    with self._instances_change_lock:
      if self._suspended:
        raise request_info.VersionAlreadyStoppedError()
      self._suspended = True
      with self._condition:
        instances_to_stop = zip(self._instances, self._wsgi_servers)
        for wsgi_servr in self._wsgi_servers:
          wsgi_servr.set_error(404)
    for inst, wsgi_servr in instances_to_stop:
      self._async_suspend_instance(inst, wsgi_servr.port)

  def _async_suspend_instance(self, inst, port):
    return _THREAD_POOL.submit(self._suspend_instance, inst, port)

  def _suspend_instance(self, inst, port):
    inst.quit(expect_shutdown=True)
    self._shutdown_instance(inst, port)

  def resume(self):
    """Resumes serving for this module."""
    with self._instances_change_lock:
      if not self._suspended:
        raise request_info.VersionAlreadyStartedError()
      self._suspended = False
      with self._condition:
        if self._quit_event.is_set():
          return
        wsgi_servers = self._wsgi_servers
      instances_to_start = []
      for instance_id, wsgi_servr in enumerate(wsgi_servers):
        inst = self._instance_factory.new_instance(instance_id,
                                                   expect_ready_request=True)
        wsgi_servr.set_app(functools.partial(self._handle_request, inst=inst))
        self._port_registry.add(wsgi_servr.port, self, inst)
        with self._condition:
          if self._quit_event.is_set():
            return
          self._instances[instance_id] = inst

        instances_to_start.append((wsgi_servr, inst))
    for wsgi_servr, inst in instances_to_start:
      self._async_start_instance(wsgi_servr, inst)

  def restart(self):
    """Restarts the module, replacing all running instances."""
    with self._instances_change_lock:
      with self._condition:
        if self._quit_event.is_set():
          return
        instances_to_stop = self._instances[:]
        wsgi_servers = self._wsgi_servers[:]
      instances_to_start = []
      for instance_id, wsgi_servr in enumerate(wsgi_servers):
        inst = self._instance_factory.new_instance(instance_id,
                                                   expect_ready_request=True)
        wsgi_servr.set_app(functools.partial(self._handle_request, inst=inst))
        self._port_registry.add(wsgi_servr.port, self, inst)
        instances_to_start.append(inst)
      with self._condition:
        if self._quit_event.is_set():
          return
        self._instances[:] = instances_to_start

    # Just force instances to stop for a faster restart.
    for inst in instances_to_stop:
      inst.quit(force=True)

    start_futures = [
        self._async_start_instance(wsgi_servr, inst)
        for wsgi_servr, inst in zip(wsgi_servers, instances_to_start)]
    logging.info('Waiting for instances to restart')

    _, not_done = futures.wait(start_futures, timeout=_SHUTDOWN_TIMEOUT)
    if not_done:
      logging.warning('All instances may not have restarted')
    else:
      logging.info('Instances restarted')

  def _restart_instance(self, inst):
    """Restarts the specified instance."""
    with self._instances_change_lock:
      # Quit the old instance.
      inst.quit(force=True)
      # Create the new instance.
      new_instance = self._instance_factory.new_instance(inst.instance_id)
      wsgi_servr = self._wsgi_servers[inst.instance_id]
      wsgi_servr.set_app(
          functools.partial(self._handle_request, inst=new_instance))
      self._port_registry.add(wsgi_servr.port, self, new_instance)
      # Start the new instance.
      self._start_instance(wsgi_servr, new_instance)
      # Replace it in the module registry.
      with self._condition:
        self._instances[new_instance.instance_id] = new_instance

  def get_instance(self, instance_id):
    """Returns the instance with the provided instance ID."""
    try:
      with self._condition:
        return self._instances[int(instance_id)]
    except (ValueError, IndexError):
      raise request_info.InvalidInstanceIdError()

  def __call__(self, environ, start_response, inst=None):
    return self._handle_request(environ, start_response, inst)

  @property
  def supports_individually_addressable_instances(self):
    return True


class ExternalModule(Module):
  """A module with a single instance that is run externally on a given port."""
  # TODO: reduce code duplication between the various Module classes.

  def __init__(self, **kwargs):
    """Initializer for ManualScalingModule.

    Args:
      **kwargs: Arguments to forward to Module.__init__.
    """
    super(ExternalModule, self).__init__(**kwargs)

    self._instance = None  # Protected by self._condition.
    self._wsgi_server = None  # Protected by self._condition.
    # Whether the module has been stopped. Protected by self._condition.
    self._suspended = False

    self._condition = threading.Condition()  # Protects instance state.

    # Serializes operations that modify the serving state of the instance.
    self._instance_change_lock = threading.RLock()

    self._change_watcher_thread = threading.Thread(
        target=self._loop_watching_for_changes, name='Change Watcher')

  # Override this method from the parent class
  def _create_instance_factory(self, module_configuration):
    return _ExternalInstanceFactory(
        request_data=self._request_data,
        module_configuration=module_configuration)

  def start(self):
    """Start background management of the Module."""
    self._balanced_module.start()
    self._port_registry.add(self.balanced_port, self, None)
    if self._watcher:
      self._watcher.start()
    self._change_watcher_thread.start()
    with self._instance_change_lock:
      self._add_instance()

  def quit(self):
    """Stops the Module."""
    self._quit_event.set()
    # The instance adjustment thread depends on the balanced module and the
    # watcher so wait for it exit before quitting them.
    if self._watcher:
      self._watcher.quit()
    self._change_watcher_thread.join()
    self._balanced_module.quit()
    self._wsgi_server.quit()

  def get_instance_port(self, instance_id):
    """Returns the port of the HTTP server for an instance."""
    if instance_id != 0:
      raise request_info.InvalidInstanceIdError()
    return self._wsgi_server.port

  @property
  def instances(self):
    """A set of all the instances currently in the Module."""
    return {self._instance}

  def _handle_instance_request(self,
                               environ,
                               start_response,
                               url_map,
                               match,
                               request_id,
                               inst,
                               request_type):
    """Handles a request routed a particular Instance.

    Args:
      environ: An environ dict for the request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.
      url_map: An appinfo.URLMap instance containing the configuration for the
          handler that matched.
      match: A re.MatchObject containing the result of the matched URL pattern.
      request_id: A unique string id associated with the request.
      inst: The instance.Instance to send the request to.
      request_type: The type of the request. See instance.*_REQUEST module
          constants.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    start_time = time.time()
    timeout_time = start_time + self._get_wait_time()
    try:
      while time.time() < timeout_time:
        logging.debug('Dispatching request to %s after %0.4fs pending',
                      inst, time.time() - start_time)
        try:
          return inst.handle(environ, start_response, url_map, match,
                             request_id, request_type)
        except instance.CannotAcceptRequests:
          pass
        inst.wait(timeout_time)
        if inst.has_quit:
          return self._error_response(environ, start_response, 503)
      return self._error_response(environ, start_response, 503)
    finally:
      with self._condition:
        self._condition.notify()

  def _handle_script_request(self,
                             environ,
                             start_response,
                             url_map,
                             match,
                             request_id,
                             inst=None,
                             request_type=instance.NORMAL_REQUEST):
    """Handles a HTTP request that has matched a script handler.

    Args:
      environ: An environ dict for the request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.
      url_map: An appinfo.URLMap instance containing the configuration for the
          handler that matched.
      match: A re.MatchObject containing the result of the matched URL pattern.
      request_id: A unique string id associated with the request.
      inst: The instance.Instance to send the request to. If None then an
          appropriate instance.Instance will be chosen.
      request_type: The type of the request. See instance.*_REQUEST module
          constants.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    if ((request_type in (instance.NORMAL_REQUEST, instance.READY_REQUEST) and
         self._suspended) or self._quit_event.is_set()):
      return self._error_response(environ, start_response, 404)
    environ['BACKEND_ID'] = (
        self._module_configuration.module_name
        if self._module_configuration.is_backend
        else self._module_configuration.version_id.split('.', 1)[0])
    return self._handle_instance_request(
        environ, start_response, url_map, match, request_id,
        inst or self._instance, request_type)

  def _add_instance(self):
    """Creates and adds a new instance.Instance to the Module.

    This must be called with _instances_change_lock held.
    """
    inst = self._instance_factory.new_instance(0)
    wsgi_servr = wsgi_server.WsgiServer(
        (self._host, 0), functools.partial(self._handle_request, inst=inst))
    wsgi_servr.start()
    self._port_registry.add(wsgi_servr.port, self, inst)

    with self._condition:
      if self._quit_event.is_set():
        return
      self._wsgi_server = wsgi_servr
      self._instance = inst
      suspended = self._suspended
    if not suspended:
      self._async_start_instance(wsgi_servr, inst)

  def _async_start_instance(self, wsgi_servr, inst):
    return _THREAD_POOL.submit(self._start_instance, wsgi_servr, inst)

  def _start_instance(self, wsgi_servr, inst):
    try:
      if not inst.start():
        return
    except:
      logging.exception('Internal error while starting instance.')
      raise

    logging.debug('Started instance: %s at http://%s:%s', inst, self.host,
                  wsgi_servr.port)
    logging.info('New instance for module "%s" serving on:\nhttp://%s\n',
                 self.name, self.balanced_address)

  def _handle_changes(self, timeout=0):
    """Handle file or configuration changes."""
    # Always check for config changes because checking also clears
    # pending changes.
    config_changes = self._module_configuration.check_for_updates()
    if application_configuration.HANDLERS_CHANGED in config_changes:
      handlers = self._create_url_handlers()
      with self._handler_lock:
        self._handlers = handlers

    if config_changes & _RESTART_INSTANCES_CONFIG_CHANGES:
      self._instance_factory.configuration_changed(config_changes)
      with self._instances_change_lock:
        if not self._suspended:
          self.restart()

  def _loop_watching_for_changes(self):
    """Loops until the InstancePool is done watching for file changes."""
    while not self._quit_event.is_set():
      if self.ready:
        if self._automatic_restarts:
          self._handle_changes(_CHANGE_POLLING_MS)
        else:
          time.sleep(_CHANGE_POLLING_MS/1000.0)

  def get_num_instances(self):
    return 1

  def set_num_instances(self, instances):
    pass

  def _async_quit_instance(self, inst, wsgi_servr):
    return _THREAD_POOL.submit(self._quit_instance, inst, wsgi_servr)

  def _quit_instance(self, inst, wsgi_servr):
    port = wsgi_servr.port
    wsgi_servr.quit()
    inst.quit(expect_shutdown=True)
    self._shutdown_instance(inst, port)

  def suspend(self):
    """Suspends serving for this module, quitting all running instances."""
    with self._instance_change_lock:
      if self._suspended:
        raise request_info.VersionAlreadyStoppedError()
      self._suspended = True
      with self._condition:
        self._wsgi_server.set_error(404)
    return _THREAD_POOL.submit(
        self._suspend_instance, self._instance, self._wsgi_server.port)

  def _suspend_instance(self, inst, port):
    inst.quit(expect_shutdown=True)
    self._shutdown_instance(inst, port)

  def resume(self):
    """Resumes serving for this module."""
    with self._instance_change_lock:
      if not self._suspended:
        raise request_info.VersionAlreadyStartedError()
      self._suspended = False
      with self._condition:
        if self._quit_event.is_set():
          return
      inst = self._instance_factory.new_instance(0, expect_ready_request=True)
      self._instance = inst
      self._wsgi_server.set_app(
          functools.partial(self._handle_request, inst=inst))
      self._port_registry.add(self._wsgi_server.port, self, inst)
    self._async_start_instance(self._wsgi_server, inst)

  def restart(self):
    """Restarts the module, replacing all running instances."""
    with self._instance_change_lock:
      with self._condition:
        if self._quit_event.is_set():
          return
      inst = self._instance_factory.new_instance(0, expect_ready_request=True)
      self._wsgi_server.set_app(
          functools.partial(self._handle_request, inst=inst))
      self._port_registry.add(self._wsgi_server.port, self, inst)
      self._instance = inst

    # Just force instance to stop for a faster restart.
    inst.quit(force=True)

    logging.info('Waiting for instances to restart')
    self._start_instance(self._wsgi_server, inst)
    logging.info('Instances restarted')

  def get_instance(self, instance_id):
    """Returns the instance with the provided instance ID."""
    if instance_id == 0:
      return self._instance
    raise request_info.InvalidInstanceIdError()

  def __call__(self, environ, start_response, inst=None):
    return self._handle_request(environ, start_response, inst)

  @property
  def supports_individually_addressable_instances(self):
    return True


class _ExternalInstanceFactory(instance.InstanceFactory):
  """Factory for instances that are started externally rather than by us."""

  _MAX_CONCURRENT_REQUESTS = 20

  # TODO: reconsider this
  START_URL_MAP = appinfo.URLMap(
      url='/_ah/start',
      script='ignored',
      login='admin')
  WARMUP_URL_MAP = appinfo.URLMap(
      url='/_ah/warmup',
      script='ignored',
      login='admin')

  def __init__(self, request_data, module_configuration):
    super(_ExternalInstanceFactory, self).__init__(
        request_data, self._MAX_CONCURRENT_REQUESTS)
    self._module_configuration = module_configuration

  def new_instance(self, instance_id, expect_ready_request=False):
    assert instance_id == 0
    proxy = _ExternalRuntimeProxy(self._module_configuration)
    return instance.Instance(self.request_data,
                             instance_id,
                             proxy,
                             self.max_concurrent_requests,
                             self.max_background_threads,
                             expect_ready_request)


class _ExternalRuntimeProxy(instance.RuntimeProxy):

  def __init__(self, module_configuration):
    super(_ExternalRuntimeProxy, self).__init__()
    self._module_configuration = module_configuration

  def start(self):
    self._proxy = http_proxy.HttpProxy(
        host='localhost', port=self._module_configuration.external_port,
        instance_died_unexpectedly=lambda: False,
        instance_logs_getter=lambda: '',
        error_handler_file=application_configuration.get_app_error_file(
            self._module_configuration),
        prior_error=None)
    self.handle = self._proxy.handle


class BasicScalingModule(Module):
  """A pool of instances that is basic-scaled."""

  _DEFAULT_BASIC_SCALING = appinfo.BasicScaling(max_instances='1',
                                                idle_timeout='15m')

  @staticmethod
  def _parse_idle_timeout(timing):
    """Parse a idle timeout string into an int of the value in seconds.

    Args:
      timing: A str of the form 1m or 10s.

    Returns:
      An int representation of the value in seconds.
    """
    if timing.endswith('m'):
      return int(timing[:-1]) * 60
    else:
      return int(timing[:-1])

  @classmethod
  def _populate_default_basic_scaling(cls, basic_scaling):
    for attribute in basic_scaling.ATTRIBUTES:
      if getattr(basic_scaling, attribute) in ('basic', None):
        setattr(basic_scaling, attribute,
                getattr(cls._DEFAULT_BASIC_SCALING, attribute))

  def _process_basic_scaling(self, basic_scaling):
    if basic_scaling:
      self._populate_default_basic_scaling(basic_scaling)
    else:
      basic_scaling = self._DEFAULT_BASIC_SCALING
    if self._max_instances is not None:
      self._max_instances = min(self._max_instances,
                                int(basic_scaling.max_instances))
    else:
      self._max_instances = int(basic_scaling.max_instances)
    self._instance_idle_timeout = self._parse_idle_timeout(
        basic_scaling.idle_timeout)

  def __init__(self, **kwargs):
    """Initializer for BasicScalingModule.

    Args:
      **kwargs: Arguments to forward to Module.__init__.
    """
    super(BasicScalingModule, self).__init__(**kwargs)

    self._process_basic_scaling(self._module_configuration.basic_scaling)

    self._instances = []  # Protected by self._condition.
    self._wsgi_servers = []  # Protected by self._condition.
    # A list of booleans signifying whether the corresponding instance in
    # self._instances has been or is being started.
    self._instance_running = []  # Protected by self._condition.

    for instance_id in xrange(self._max_instances):
      inst = self._instance_factory.new_instance(instance_id,
                                                 expect_ready_request=True)
      self._instances.append(inst)
      self._wsgi_servers.append(wsgi_server.WsgiServer(
          (self._host, 0), functools.partial(self._handle_request, inst=inst)))
      self._instance_running.append(False)

    self._condition = threading.Condition()  # Protects instance state.

    self._change_watcher_thread = threading.Thread(
        target=self._loop_watching_for_changes_and_idle_instances,
        name='Change Watcher')

  def start(self):
    """Start background management of the Module."""
    self._balanced_module.start()
    self._port_registry.add(self.balanced_port, self, None)
    if self._watcher:
      self._watcher.start()
    self._change_watcher_thread.start()
    for wsgi_servr, inst in zip(self._wsgi_servers, self._instances):
      wsgi_servr.start()
      self._port_registry.add(wsgi_servr.port, self, inst)

  def quit(self):
    """Stops the Module."""
    self._quit_event.set()
    self._change_watcher_thread.join()
    # The instance adjustment thread depends on the balanced module and the
    # watcher so wait for it exit before quitting them.
    if self._watcher:
      self._watcher.quit()
    self._balanced_module.quit()
    for wsgi_servr in self._wsgi_servers:
      wsgi_servr.quit()
    with self._condition:
      instances = self._instances
      self._instances = []
      self._condition.notify_all()
    for inst in instances:
      inst.quit(force=True)

  def get_instance_port(self, instance_id):
    """Returns the port of the HTTP server for an instance."""
    try:
      instance_id = int(instance_id)
    except ValueError:
      raise request_info.InvalidInstanceIdError()
    with self._condition:
      if 0 <= instance_id < len(self._instances):
        wsgi_servr = self._wsgi_servers[instance_id]
      else:
        raise request_info.InvalidInstanceIdError()
    return wsgi_servr.port

  @property
  def instances(self):
    """A set of all the instances currently in the Module."""
    with self._condition:
      return set(self._instances)

  def _handle_instance_request(self,
                               environ,
                               start_response,
                               url_map,
                               match,
                               request_id,
                               inst,
                               request_type):
    """Handles a request routed a particular Instance.

    Args:
      environ: An environ dict for the request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.
      url_map: An appinfo.URLMap instance containing the configuration for the
          handler that matched.
      match: A re.MatchObject containing the result of the matched URL pattern.
      request_id: A unique string id associated with the request.
      inst: The instance.Instance to send the request to.
      request_type: The type of the request. See instance.*_REQUEST module
          constants.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    instance_id = inst.instance_id
    start_time = time.time()
    timeout_time = start_time + self._get_wait_time()
    try:
      while time.time() < timeout_time:
        logging.debug('Dispatching request to %s after %0.4fs pending',
                      inst, time.time() - start_time)
        try:
          return inst.handle(environ, start_response, url_map, match,
                             request_id, request_type)
        except instance.CannotAcceptRequests:
          pass
        if inst.has_quit:
          return self._error_response(environ, start_response, 503)
        with self._condition:
          if self._instance_running[instance_id]:
            should_start = False
          else:
            self._instance_running[instance_id] = True
            should_start = True
        if should_start:
          self._start_instance(instance_id)
        else:
          inst.wait(timeout_time)
      else:
        return self._error_response(environ, start_response, 503)
    finally:
      with self._condition:
        self._condition.notify()

  def _handle_script_request(self,
                             environ,
                             start_response,
                             url_map,
                             match,
                             request_id,
                             inst=None,
                             request_type=instance.NORMAL_REQUEST):
    """Handles a HTTP request that has matched a script handler.

    Args:
      environ: An environ dict for the request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.
      url_map: An appinfo.URLMap instance containing the configuration for the
          handler that matched.
      match: A re.MatchObject containing the result of the matched URL pattern.
      request_id: A unique string id associated with the request.
      inst: The instance.Instance to send the request to. If None then an
          appropriate instance.Instance will be chosen.
      request_type: The type of the request. See instance.*_REQUEST module
          constants.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    if self._quit_event.is_set():
      return self._error_response(environ, start_response, 404)
    if self._module_configuration.is_backend:
      environ['BACKEND_ID'] = self._module_configuration.module_name
    else:
      environ['BACKEND_ID'] = (
          self._module_configuration.version_id.split('.', 1)[0])
    if inst is not None:
      return self._handle_instance_request(
          environ, start_response, url_map, match, request_id, inst,
          request_type)

    start_time = time.time()
    timeout_time = start_time + self._get_wait_time()
    while time.time() < timeout_time:
      if self._quit_event.is_set():
        return self._error_response(environ, start_response, 404)
      inst = self._choose_instance(timeout_time)
      if inst:
        try:
          logging.debug('Dispatching request to %s after %0.4fs pending',
                        inst, time.time() - start_time)
          return inst.handle(environ, start_response, url_map, match,
                             request_id, request_type)
        except instance.CannotAcceptRequests:
          continue
        finally:
          with self._condition:
            self._condition.notify()
    else:
      return self._error_response(environ, start_response, 503, _TIMEOUT_HTML)

  def _start_any_instance(self):
    """Choose an inactive instance and start it asynchronously.

    Returns:
      An instance.Instance that will be started asynchronously or None if all
      instances are already running.
    """
    with self._condition:
      for instance_id, running in enumerate(self._instance_running):
        if not running:
          self._instance_running[instance_id] = True
          inst = self._instances[instance_id]
          break
      else:
        return None
    self._async_start_instance(instance_id)
    return inst

  def _async_start_instance(self, instance_id):
    return _THREAD_POOL.submit(self._start_instance, instance_id)

  def _start_instance(self, instance_id):
    with self._condition:
      if self._quit_event.is_set():
        return
      wsgi_servr = self._wsgi_servers[instance_id]
      inst = self._instances[instance_id]
    if inst.start():
      logging.debug('Started instance: %s at http://%s:%s', inst, self.host,
                    wsgi_servr.port)
      try:
        environ = self.build_request_environ(
            'GET', '/_ah/start', [], '', '0.1.0.3', wsgi_servr.port,
            fake_login=True)
        self._handle_request(environ,
                             start_response_utils.null_start_response,
                             inst=inst,
                             request_type=instance.READY_REQUEST)
        logging.debug('Sent start request: %s', inst)
        with self._condition:
          self._condition.notify(self.max_instance_concurrent_requests)
      except:
        logging.exception('Internal error while handling start request.')

  def _choose_instance(self, timeout_time):
    """Returns an Instance to handle a request or None if all are busy."""
    with self._condition:
      while time.time() < timeout_time and not self._quit_event.is_set():
        for inst in self._instances:
          if inst.can_accept_requests:
            return inst
        else:
          inst = self._start_any_instance()
          if inst:
            break
          self._condition.wait(timeout_time - time.time())
      else:
        return None
    if inst:
      inst.wait(timeout_time)
    return inst

  def _handle_changes(self, timeout=0):
    """Handle file or configuration changes."""
    # Always check for config and file changes because checking also clears
    # pending changes.
    config_changes = self._module_configuration.check_for_updates()

    if application_configuration.HANDLERS_CHANGED in config_changes:
      handlers = self._create_url_handlers()
      with self._handler_lock:
        self._handlers = handlers

    file_changes = self._watcher.changes(timeout)
    if file_changes:
      self._instance_factory.files_changed()

    if config_changes & _RESTART_INSTANCES_CONFIG_CHANGES:
      self._instance_factory.configuration_changed(config_changes)

    if config_changes & _RESTART_INSTANCES_CONFIG_CHANGES or file_changes:
      self.restart()

  def _loop_watching_for_changes_and_idle_instances(self):
    """Loops until the InstancePool is done watching for file changes."""
    while not self._quit_event.is_set():
      if self.ready:
        self._shutdown_idle_instances()
        if self._automatic_restarts:
          self._handle_changes(_CHANGE_POLLING_MS)
        else:
          time.sleep(_CHANGE_POLLING_MS/1000.0)

  def _shutdown_idle_instances(self):
    instances_to_stop = []
    with self._condition:
      for instance_id, inst in enumerate(self._instances):
        if (self._instance_running[instance_id] and
            inst.idle_seconds > self._instance_idle_timeout):
          instances_to_stop.append((self._instances[instance_id],
                                    self._wsgi_servers[instance_id]))
          self._instance_running[instance_id] = False
          new_instance = self._instance_factory.new_instance(
              instance_id, expect_ready_request=True)
          self._instances[instance_id] = new_instance
          wsgi_servr = self._wsgi_servers[instance_id]
          wsgi_servr.set_app(
              functools.partial(self._handle_request, inst=new_instance))
          self._port_registry.add(wsgi_servr.port, self, new_instance)
    for inst, wsgi_servr in instances_to_stop:
      logging.debug('Shutting down %r', inst)
      self._stop_instance(inst, wsgi_servr)

  def _stop_instance(self, inst, wsgi_servr):
    inst.quit(expect_shutdown=True)
    self._async_shutdown_instance(inst, wsgi_servr.port)

  def restart(self):
    """Restarts the module, replacing all running instances."""
    instances_to_stop = []
    instances_to_start = []
    with self._condition:
      if self._quit_event.is_set():
        return
      for instance_id, inst in enumerate(self._instances):
        if self._instance_running[instance_id]:
          instances_to_stop.append((inst, self._wsgi_servers[instance_id]))
          new_instance = self._instance_factory.new_instance(
              instance_id, expect_ready_request=True)
          self._instances[instance_id] = new_instance
          instances_to_start.append(instance_id)
          wsgi_servr = self._wsgi_servers[instance_id]
          wsgi_servr.set_app(
              functools.partial(self._handle_request, inst=new_instance))
          self._port_registry.add(wsgi_servr.port, self, new_instance)
    for instance_id in instances_to_start:
      self._async_start_instance(instance_id)
    for inst, wsgi_servr in instances_to_stop:
      self._stop_instance(inst, wsgi_servr)

  def get_instance(self, instance_id):
    """Returns the instance with the provided instance ID."""
    try:
      with self._condition:
        return self._instances[int(instance_id)]
    except (ValueError, IndexError):
      raise request_info.InvalidInstanceIdError()

  def __call__(self, environ, start_response, inst=None):
    return self._handle_request(environ, start_response, inst)

  @property
  def supports_individually_addressable_instances(self):
    return True


class InteractiveCommandModule(Module):
  """A Module that can evaluate user commands.

  This module manages a single Instance which is started lazily.
  """

  _MAX_REQUEST_WAIT_TIME = 15

  def __init__(self,
               module_configuration,
               host,
               balanced_port,
               api_host,
               api_port,
               auth_domain,
               runtime_stderr_loglevel,
               php_config,
               python_config,
               java_config,
               custom_config,
               cloud_sql_config,
               vm_config,
               default_version_port,
               port_registry,
               request_data,
               dispatcher,
               use_mtime_file_watcher,
               allow_skipped_files,
               threadsafe_override):
    """Initializer for InteractiveCommandModule.

    Args:
      module_configuration: An application_configuration.ModuleConfiguration
          instance storing the configuration data for this module.
      host: A string containing the host that will be used when constructing
          HTTP headers sent to the Instance executing the interactive command
          e.g. "localhost".
      balanced_port: An int specifying the port that will be used when
          constructing HTTP headers sent to the Instance executing the
          interactive command e.g. "localhost".
      api_host: The host that APIServer listens for RPC requests on.
      api_port: The port that APIServer listens for RPC requests on.
      auth_domain: A string containing the auth domain to set in the environment
          variables.
      runtime_stderr_loglevel: An int reprenting the minimum logging level at
          which runtime log messages should be written to stderr. See
          devappserver2.py for possible values.
      php_config: A runtime_config_pb2.PhpConfig instances containing PHP
          runtime-specific configuration. If None then defaults are used.
      python_config: A runtime_config_pb2.PythonConfig instance containing
          Python runtime-specific configuration. If None then defaults are used.
      java_config: A runtime_config_pb2.JavaConfig instance containing
          Java runtime-specific configuration. If None then defaults are used.
      custom_config: A runtime_config_pb2.CustomConfig instance. If None, or
          'custom_entrypoint' is not set, then attempting to instantiate a
          custom runtime module will result in an error.
      cloud_sql_config: A runtime_config_pb2.CloudSQL instance containing the
          required configuration for local Google Cloud SQL development. If None
          then Cloud SQL will not be available.
      vm_config: A runtime_config_pb2.VMConfig instance containing
          VM runtime-specific configuration. If None all docker-related stuff
          is disabled.
      default_version_port: An int containing the port of the default version.
      port_registry: A dispatcher.PortRegistry used to provide the Dispatcher
          with a mapping of port to Module and Instance.
      request_data: A wsgi_request_info.WSGIRequestInfo that will be provided
          with request information for use by API stubs.
      dispatcher: A Dispatcher instance that can be used to make HTTP requests.
      use_mtime_file_watcher: A bool containing whether to use mtime polling to
          monitor file changes even if other options are available on the
          current platform.
      allow_skipped_files: If True then all files in the application's directory
          are readable, even if they appear in a static handler or "skip_files"
          directive.
      threadsafe_override: If not None, ignore the YAML file value of threadsafe
          and use this value instead.
    """
    super(InteractiveCommandModule, self).__init__(
        module_configuration,
        host,
        balanced_port,
        api_host,
        api_port,
        auth_domain,
        runtime_stderr_loglevel,
        php_config,
        python_config,
        java_config,
        custom_config,
        cloud_sql_config,
        vm_config,
        default_version_port,
        port_registry,
        request_data,
        dispatcher,
        max_instances=1,
        use_mtime_file_watcher=use_mtime_file_watcher,
        automatic_restarts=True,
        allow_skipped_files=allow_skipped_files,
        threadsafe_override=threadsafe_override)
    # Use a single instance so that state is consistent across requests.
    self._inst_lock = threading.Lock()
    self._inst = None

  @property
  def balanced_port(self):
    """The port that the balanced HTTP server for the Module is listening on.

    The InteractiveCommandModule does not actually listen on this port but it is
    used when constructing the "SERVER_PORT" in the WSGI-environment.
    """
    return self._balanced_port

  def quit(self):
    """Stops the InteractiveCommandModule."""
    if self._inst:
      self._inst.quit(force=True)
      self._inst = None

  def _handle_script_request(self,
                             environ,
                             start_response,
                             url_map,
                             match,
                             request_id,
                             inst=None,
                             request_type=instance.INTERACTIVE_REQUEST):
    """Handles a interactive request by forwarding it to the managed Instance.

    Args:
      environ: An environ dict for the request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.
      url_map: An appinfo.URLMap instance containing the configuration for the
          handler that matched.
      match: A re.MatchObject containing the result of the matched URL pattern.
      request_id: A unique string id associated with the request.
      inst: The instance.Instance to send the request to.
      request_type: The type of the request. See instance.*_REQUEST module
          constants. This must be instance.INTERACTIVE_REQUEST.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    assert inst is None
    assert request_type == instance.INTERACTIVE_REQUEST

    start_time = time.time()
    timeout_time = start_time + self._get_wait_time()

    while time.time() < timeout_time:
      new_instance = False
      with self._inst_lock:
        if not self._inst:
          self._inst = self._instance_factory.new_instance(
              AutoScalingModule.generate_instance_id(),
              expect_ready_request=False)
          new_instance = True
        inst = self._inst

      if new_instance:
        self._inst.start()

      try:
        return inst.handle(environ, start_response, url_map, match,
                           request_id, request_type)
      except instance.CannotAcceptRequests:
        inst.wait(timeout_time)
      except Exception:
        # If the instance is restarted while handling a request then the
        # exception raises is unpredictable.
        if inst != self._inst:
          start_response('503 Service Unavailable', [])
          return ['Instance was restarted while executing command']
        logging.exception('Unexpected exception handling command: %r', environ)
        raise
    else:
      start_response('503 Service Unavailable', [])
      return ['The command timed-out while waiting for another one to complete']

  def restart(self):
    """Restarts the module."""
    with self._inst_lock:
      if self._inst:
        self._inst.quit(force=True)
        self._inst = None

  def send_interactive_command(self, command):
    """Sends an interactive command to the module.

    Args:
      command: The command to send e.g. "print 5+5".

    Returns:
      A string representing the result of the command e.g. "10\n".

    Raises:
      InteractiveCommandError: if the command failed for any reason.
    """
    start_response = start_response_utils.CapturingStartResponse()

    # 192.0.2.0 is an example address defined in RFC 5737.
    environ = self.build_request_environ(
        'POST', '/', [], command, '192.0.2.0', self.balanced_port)

    try:
      response = self._handle_request(
          environ,
          start_response,
          request_type=instance.INTERACTIVE_REQUEST)
    except Exception as e:
      raise InteractiveCommandError('Unexpected command failure: ', str(e))

    if start_response.status != '200 OK':
      raise InteractiveCommandError(start_response.merged_response(response))

    return start_response.merged_response(response)
