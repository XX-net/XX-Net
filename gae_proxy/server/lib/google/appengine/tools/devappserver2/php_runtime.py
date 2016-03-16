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
"""Serves content for "script" handlers using the PHP runtime."""



import cgi
import logging
import os
import re
import subprocess
import sys

import google
from google.appengine.api import appinfo
from google.appengine.tools.devappserver2 import http_runtime
from google.appengine.tools.devappserver2 import instance

from google.appengine.tools.devappserver2 import safe_subprocess


_RUNTIME_PATH = os.path.abspath(



os.path.join(os.path.dirname(sys.argv[0]), '_php_runtime.py')
    )
_CHECK_ENVIRONMENT_SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__), 'php', 'check_environment.php')
_RUNTIME_ARGS = [sys.executable, _RUNTIME_PATH]

GAE_EXTENSION_NAME = 'GAE Runtime Module'

# OS-specific file naming for bundled PHP binaries. Assume empty string
# if no corresponding OS is found.
_EXECUTABLE_EXT = {'win32': '.exe'}
_EXTENSION_PREFIX = {'win32': 'php_'}
_DYNAMIC_LIB_EXT = {'win32': '.dll', 'darwin': '.so'}


def _get_php_executable_path(runtime):
  filename = 'php-cgi%s' % _EXECUTABLE_EXT.get(sys.platform, '')
  return _get_php_binary_path(filename, runtime)


def _get_php_extension_path(extension_stem, runtime):
  filename = '%s%s%s' % (_EXTENSION_PREFIX.get(sys.platform, ''),
                         extension_stem,
                         _DYNAMIC_LIB_EXT.get(sys.platform, ''))
  return _get_php_binary_path(filename, runtime)


def _get_php_binary_path(filename, runtime):
  """Returns the path to the siloed php-cgi binary or None if not present."""
  php_binary_dir = None
  if sys.platform == 'win32':
    if runtime == 'php55':
      php_binary_dir = 'php/php-5.5-Win32-VC11-x86'
  elif sys.platform == 'darwin':
    if runtime == 'php55':
      php_binary_dir = '../php55'

  if php_binary_dir:
    # The Cloud SDK uses symlinks in its packaging of the Mac Launcher.  First
    # try to find PHP relative to the absolute path of this executable.  If that
    # doesn't work, try using the path without dereferencing all symlinks.
    base_paths = [os.path.realpath(sys.argv[0]), sys.argv[0]]
    for base_path in base_paths:
      root = os.path.dirname(base_path)
      abs_path = os.path.abspath(os.path.join(root, php_binary_dir, filename))
      if os.path.exists(abs_path):
        return abs_path

  return None


class _PHPBinaryError(Exception):
  pass


class _PHPEnvironmentError(Exception):
  pass


class _BadPHPEnvironmentRuntimeProxy(instance.RuntimeProxy):
  """Serves an error page describing the problem with the user's PHP setup."""

  def __init__(self, php_executable_path, exception):
    self._php_executable_path = php_executable_path
    self._exception = exception

  def start(self):
    pass

  def quit(self):
    pass

  def handle(self, environ, start_response, url_map, match, request_id,
             request_type):
    """Serves a request by displaying an error page.

    Args:
      environ: An environ dict for the request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.
      url_map: An appinfo.URLMap instance containing the configuration for the
          handler matching this request.
      match: A re.MatchObject containing the result of the matched URL pattern.
      request_id: A unique string id associated with the request.
      request_type: The type of the request. See instance.*_REQUEST module
          constants.

    Yields:
      A sequence of strings containing the body of the HTTP response.
    """
    start_response('500 Internal Server Error',
                   [('Content-Type', 'text/html')])
    yield '<html><head><title>Invalid PHP Configuration</title></head>'
    yield '<body>'
    yield '<title>Invalid PHP Configuration</title>'
    if isinstance(self._exception, _PHPEnvironmentError):
      yield '<b>The PHP interpreter specified with the --php_executable_path '
      yield ' flag (&quot;%s&quot;) is not compatible with the App Engine ' % (
          self._php_executable_path)
      yield 'PHP development environment.</b><br>'
      yield '<br>'
      yield '<pre>%s</pre>' % self._exception
    else:
      yield '<b>%s</b>' % cgi.escape(str(self._exception))

    yield '</body></html>'


class PHPRuntimeInstanceFactory(instance.InstanceFactory):
  """A factory that creates new PHP runtime Instances."""

  # A mapping from a php executable path to the _BadPHPEnvironmentRuntimeProxy
  # descriping why it is not useable. If the php executable is usable then the
  # path will map to None. Only one PHP executable will be used in a run of the
  # development server but that is not necessarily the case for tests.
  _php_binary_to_error_proxy = {}

  # TODO: Use real script values.
  START_URL_MAP = appinfo.URLMap(
      url='/_ah/start',
      script='$PHP_LIB/default_start_handler',
      login='admin')
  WARMUP_URL_MAP = appinfo.URLMap(
      url='/_ah/warmup',
      script='$PHP_LIB/default_warmup_handler',
      login='admin')
  SUPPORTS_INTERACTIVE_REQUESTS = True
  FILE_CHANGE_INSTANCE_RESTART_POLICY = instance.NEVER

  def __init__(self, request_data, runtime_config_getter, module_configuration):
    """Initializer for PHPRuntimeInstanceFactory.

    Args:
      request_data: A wsgi_request_info.WSGIRequestInfo that will be provided
          with request information for use by API stubs.
      runtime_config_getter: A function that can be called without arguments
          and returns the runtime_config_pb2.Config containing the configuration
          for the runtime.
      module_configuration: An application_configuration.ModuleConfiguration
          instance respresenting the configuration of the module that owns the
          runtime.
    """
    super(PHPRuntimeInstanceFactory, self).__init__(
        request_data, 8 if runtime_config_getter().threadsafe else 1)
    self._runtime_config_getter = runtime_config_getter
    self._module_configuration = module_configuration
    self._bad_environment_proxy = None

  @classmethod
  def _check_php_version(cls, php_executable_path, env):
    """Check if php-cgi has the correct version."""
    version_process = safe_subprocess.start_process([php_executable_path, '-v'],
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE,
                                                    env=env)
    version_stdout, version_stderr = version_process.communicate()
    if version_process.returncode:
      raise _PHPEnvironmentError(
          '"%s -v" returned an error [%d]\n%s%s' % (
              php_executable_path,
              version_process.returncode,
              version_stderr,
              version_stdout))

    version_match = re.search(r'PHP (\d+).(\d+)', version_stdout)
    if version_match is None:
      raise _PHPEnvironmentError(
          '"%s -v" returned an unexpected version string:\n%s%s' % (
              php_executable_path,
              version_stderr,
              version_stdout))

    version = tuple(int(v) for v in version_match.groups())
    if version < (5, 4):
      raise _PHPEnvironmentError(
          'The PHP interpreter must be version >= 5.4, %d.%d found' % version)

  @classmethod
  def _check_gae_extension(cls, php_executable_path, gae_extension_path, env):
    """Check if GAE extension can be loaded."""
    if not os.path.exists(gae_extension_path):
      raise _PHPBinaryError('The path specified with the '
                            '--php_gae_extension_path flag (%s) does not '
                            'exist.' % gae_extension_path)

    # The GAE extension requires APPLICATION_ROOT to be set.
    env['APPLICATION_ROOT'] = os.getcwd()

    args = [php_executable_path, '-m',
            '-d', 'extension="%s"' % os.path.basename(gae_extension_path),
            '-d', 'extension_dir="%s"' % os.path.dirname(gae_extension_path)]

    ext_process = safe_subprocess.start_process(args,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE,
                                                env=env)
    ext_stdout, ext_stderr = ext_process.communicate()
    if ext_process.returncode:
      raise _PHPEnvironmentError('"%s -m" returned an error [%d]\n%s%s' % (
          php_executable_path,
          ext_process.returncode,
          ext_stderr,
          ext_stdout))

    if GAE_EXTENSION_NAME not in ext_stdout:
      raise _PHPEnvironmentError('Unable to load GAE runtime module at %s' %
                                 gae_extension_path)

  @classmethod
  def _check_environment(cls, php_executable_path, env):
    # Clear auto_prepend_file & auto_append_file ini directives as they can
    # trigger error and cause non-zero return.
    args = [php_executable_path, '-f', _CHECK_ENVIRONMENT_SCRIPT_PATH,
            '-d', 'auto_prepend_file=NULL', '-d', 'auto_append_file=NULL']
    check_process = safe_subprocess.start_process(args,
                                                  stdout=subprocess.PIPE,
                                                  stderr=subprocess.PIPE,
                                                  env=env)
    check_process_stdout, _ = check_process.communicate()
    if check_process.returncode:
      raise _PHPEnvironmentError(check_process_stdout)

  @classmethod
  def _check_binaries(cls, php_executable_path, gae_extension_path):
    """Perform sanity check on php-cgi & gae extension."""
    if not php_executable_path:
      raise _PHPBinaryError('The development server must be started with the '
                            '--php_executable_path flag set to the path of the '
                            'php-cgi binary.')

    if not os.path.exists(php_executable_path):
      raise _PHPBinaryError('The path specified with the --php_executable_path '
                            'flag (%s) does not exist.' % php_executable_path)

    if not os.access(php_executable_path, os.X_OK):
      raise _PHPBinaryError('The path specified with the --php_executable_path '
                            'flag (%s) is not executable' % php_executable_path)

    env = {}
    # On Windows, in order to run a side-by-side assembly the specified env
    # must include a valid SystemRoot.
    if 'SYSTEMROOT' in os.environ:
      env['SYSTEMROOT'] = os.environ['SYSTEMROOT']

    cls._check_php_version(php_executable_path, env)
    cls._check_environment(php_executable_path, env)
    if gae_extension_path:
      cls._check_gae_extension(php_executable_path, gae_extension_path, env)

  def _GenerateConfigForRuntime(self):
    """Return a copy of runtime config for starting a PHP runtime instance.

    The returned config uses the bundled PHP binaries if none is specified
    already through the command line arguments.

    Returns:
      The created runtime_config_pb2.Config protobuf object.
    """
    def setattr_if_empty(obj, field, value):
      if not getattr(obj, field) and value:
        setattr(obj, field, value)

    runtime = self._module_configuration.runtime
    runtime_config = self._runtime_config_getter()

    setattr_if_empty(runtime_config.php_config,
                     'php_executable_path',
                     _get_php_executable_path(runtime))

    setattr_if_empty(runtime_config.php_config,
                     'gae_extension_path',
                     _get_php_extension_path('gae_runtime_module', runtime))
    setattr_if_empty(runtime_config.php_config,
                     'xdebug_extension_path',
                     _get_php_extension_path('xdebug', runtime))

    return runtime_config

  def new_instance(self, instance_id, expect_ready_request=False):
    """Create and return a new Instance.

    Args:
      instance_id: A string or integer representing the unique (per module) id
          of the instance.
      expect_ready_request: If True then the instance will be sent a special
          request (i.e. /_ah/warmup or /_ah/start) before it can handle external
          requests.

    Returns:
      The newly created instance.Instance.
    """

    def instance_config_getter():
      runtime_config = self._GenerateConfigForRuntime()
      runtime_config.instance_id = str(instance_id)
      return runtime_config

    php_executable_path = (
        self._GenerateConfigForRuntime().php_config.php_executable_path)

    gae_extension_path = (
        self._GenerateConfigForRuntime().php_config.gae_extension_path)

    if php_executable_path not in self._php_binary_to_error_proxy:
      try:
        self._check_binaries(php_executable_path, gae_extension_path)
      except Exception as e:
        self._php_binary_to_error_proxy[php_executable_path] = (
            _BadPHPEnvironmentRuntimeProxy(php_executable_path, e))
        logging.exception('The PHP runtime is not available')
      else:
        self._php_binary_to_error_proxy[php_executable_path] = None

    proxy = self._php_binary_to_error_proxy[php_executable_path]
    if proxy is None:
      proxy = http_runtime.HttpRuntimeProxy(_RUNTIME_ARGS,
                                            instance_config_getter,
                                            self._module_configuration)
    return instance.Instance(self.request_data,
                             instance_id,
                             proxy,
                             self.max_concurrent_requests,
                             self.max_background_threads,
                             expect_ready_request)
