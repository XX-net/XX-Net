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
"""Invoke PHP after setting up the App Engine environment."""



import argparse
import os
import subprocess
import sys
import tempfile
import wsgiref.util

import google
from google.appengine.api import request_info
from google.appengine.datastore import datastore_stub_util
from google.appengine.tools.devappserver2 import api_server
from google.appengine.tools.devappserver2 import gcs_server
from google.appengine.tools.devappserver2.php import runtime


def _get_gcs_server():
  server = gcs_server.GCSServer('localhost', 0)
  server.start()
  return server


class APIRequestInfo(request_info.RequestInfo):
  """Allows stubs to lookup state linked to the request making the API call."""

  def __init__(self):
    self._environ = {}
    wsgiref.util.setup_testing_defaults(self._environ)

  def get_request_url(self, request_id):
    """Returns the URL the request e.g. 'http://localhost:8080/foo?bar=baz'.

    Args:
      request_id: The string id of the request making the API call.

    Returns:
      The URL of the request as a string.
    """
    return wsgiref.util.request_uri(self._environ)

  def get_request_environ(self, request_id):
    """Returns a dict containing the WSGI environ for the request."""
    return self._environ

  def get_module(self, request_id):
    """Returns the name of the module serving this request.

    Args:
      request_id: The string id of the request making the API call.

    Returns:
      A str containing the module name.
    """
    return 'default'

  def get_version(self, request_id):
    """Returns the version of the module serving this request.

    Args:
      request_id: The string id of the request making the API call.

    Returns:
      A str containing the version.
    """
    return '1'

  def get_instance(self, request_id):
    """Returns the instance serving this request.

    Args:
      request_id: The string id of the request making the API call.

    Returns:
      An opaque representation of the instance serving this request. It should
      only be passed to dispatcher methods expecting an instance.
    """
    return object()

  def get_dispatcher(self):
    """Returns the Dispatcher.

    Returns:
      The Dispatcher instance.
    """
    return request_info._LocalFakeDispatcher()


def _get_api_server(app_id):
  """Return a configured and started api_server.APIServer."""
  tmp_dir = tempfile.mkdtemp()
  os.environ['APPLICATION_ID'] = app_id
  api_server.setup_stubs(
      request_data=APIRequestInfo(),
      app_id=app_id,
      application_root=os.getcwd(),
      trusted=False,
      appidentity_email_address=None,
      appidentity_private_key_path=None,
      blobstore_path=tmp_dir,
      datastore_consistency=
      datastore_stub_util.PseudoRandomHRConsistencyPolicy(),
      datastore_path=':memory:',
      datastore_require_indexes=False,
      datastore_auto_id_policy=datastore_stub_util.SCATTERED,
      images_host_prefix='http://localhost:8080',
      logs_path=':memory:',
      mail_smtp_host='',
      mail_smtp_port=25,
      mail_smtp_user='',
      mail_smtp_password='',
      mail_enable_sendmail=False,
      mail_show_mail_body=False,
      mail_allow_tls=False,
      matcher_prospective_search_path=tmp_dir,
      search_index_path=None,
      taskqueue_auto_run_tasks=False,
      taskqueue_default_http_server='http://localhost:8080',
      user_login_url='/_ah/login?continue=%s',
      user_logout_url='/_ah/login?continue=%s',
      default_gcs_bucket_name=None)

  server = api_server.APIServer('localhost', 0, app_id)
  server.start()
  return server


def _get_default_php_cli_path():
  """Returns the path to the siloed php cli binary or None if not present."""
  default_php_executable_path = None
  google_package_directory = os.path.dirname(google.__file__)
  sdk_directory = os.path.dirname(google_package_directory)

  if sys.platform == 'win32':
    default_php_executable_path = os.path.abspath(
        os.path.join(sdk_directory, 'php/php-5.4-Win32-VC9-x86/php.exe'))
  elif sys.platform == 'darwin':
    default_php_executable_path = os.path.abspath(
        os.path.join(os.path.dirname(sdk_directory), 'php'))

  if (default_php_executable_path and
      os.path.exists(default_php_executable_path)):
    return default_php_executable_path
  return None


def _parse_path(value):
  """Returns the given path with ~ and environment variables expanded."""
  return os.path.expanduser(os.path.expandvars(value))


def _create_command_line_parser():
  """Returns an argparse.ArgumentParser to parse command line arguments."""
  parser = argparse.ArgumentParser(
      usage='usage: %(prog)s [execution options] <script> [script_args]',
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      'script',
      help='the path to the PHP script that should be executed')
  parser.add_argument(
      'script_args',
      help='the command arguments that will be passed to the script',
      nargs=argparse.REMAINDER)

  execution_group = parser.add_argument_group('Execution Options')

  php_cli_path = _get_default_php_cli_path()
  execution_group.add_argument('--php_executable_path', metavar='PATH',
                               type=_parse_path,
                               default=php_cli_path,
                               required=php_cli_path is None,
                               help='path to the PHP executable')
  return parser


def main():
  parser = _create_command_line_parser()
  options = parser.parse_args()

  if not options.php_executable_path:
    parser.error('--php_executable_path must be set')
  elif not os.path.exists(options.php_executable_path):
    parser.error('--php_executable_path=%s, %s does not exist' % (
        options.php_executable_path, options.php_executable_path))

  php_script = os.path.abspath(_parse_path(options.script))
  if not os.path.exists(php_script):
    parser.error('%s does not exist' % php_script)

  api_srver = _get_api_server(app_id='dummy_app_id')
  gcs_srver = _get_gcs_server()

  include_paths = [runtime.SDK_PATH]
  if sys.platform == 'win32':

    include_path = 'include_path="%s"' % ';'.join(include_paths)
  else:
    include_path = 'include_path=%s' % ':'.join(include_paths)

  php_args = [options.php_executable_path,
              '-d', include_path,
              '-f', runtime.SETUP_PHP_PATH,]
  php_args.extend(options.script_args)


  env = dict(HTTP_HOST='localhost:%d' % gcs_srver.port,
             SERVER_SOFTWARE='Development/CLI',
             REAL_SCRIPT_FILENAME=php_script,
             REMOTE_API_HOST='localhost',
             REMOTE_API_PORT=str(api_srver.port),
             REMOTE_REQUEST_ID='51',
             APPLICATION_ROOT=os.path.dirname(php_script))
  if 'SYSTEMROOT' in os.environ:
    env['SYSTEMROOT'] = os.environ['SYSTEMROOT']

  php_process = subprocess.Popen(php_args, env=env)
  script_return = php_process.wait()

  api_srver.quit()
  gcs_srver.quit()
  sys.exit(script_return)


if __name__ == '__main__':
  main()
