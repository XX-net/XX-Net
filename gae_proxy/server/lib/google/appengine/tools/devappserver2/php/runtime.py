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
"""A PHP devappserver2 runtime."""



import base64
import cStringIO
import httplib
import logging
import os
import subprocess
import sys
import time
import urllib

import google

from google.appengine.api import appinfo
from google.appengine.tools.devappserver2 import environ_utils
from google.appengine.tools.devappserver2 import http_runtime_constants
from google.appengine.tools.devappserver2 import php
from google.appengine.tools.devappserver2 import request_rewriter
from google.appengine.tools.devappserver2 import runtime_config_pb2
from google.appengine.tools.devappserver2 import safe_subprocess
from google.appengine.tools.devappserver2 import wsgi_server

SDK_PATH = os.path.abspath(







os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'php/sdk'))






if not os.path.exists(SDK_PATH):
  SDK_PATH = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),
                                          'php/sdk'))

SETUP_PHP_PATH = os.path.join(os.path.dirname(php.__file__), 'setup.php')


class PHPRuntime(object):
  """A WSGI application that runs PHP scripts using the PHP CGI binary."""

  def __init__(self, config):
    logging.debug('Initializing runtime with %s', config)
    self.config = config
    if appinfo.MODULE_SEPARATOR not in config.version_id:
      module_id = appinfo.DEFAULT_MODULE
      version_id = config.version_id
    else:
      module_id, version_id = config.version_id.split(appinfo.MODULE_SEPARATOR)
    self.environ_template = {
        'APPLICATION_ID': str(config.app_id),
        'CURRENT_MODULE_ID': module_id,
        'CURRENT_VERSION_ID': version_id,
        'DATACENTER': str(config.datacenter),
        'INSTANCE_ID': str(config.instance_id),
        'APPENGINE_RUNTIME': 'php',
        'AUTH_DOMAIN': str(config.auth_domain),
        'HTTPS': 'off',
        # By default php-cgi does not allow .php files to be run directly so
        # REDIRECT_STATUS must be set. See:
        # http://php.net/manual/en/security.cgi-bin.force-redirect.php
        'REDIRECT_STATUS': '1',
        'REMOTE_API_HOST': str(config.api_host),
        'REMOTE_API_PORT': str(config.api_port),
        'SERVER_SOFTWARE': http_runtime_constants.SERVER_SOFTWARE,
        'STDERR_LOG_LEVEL': str(config.stderr_log_level),
        'TZ': 'UTC',
        }
    self.environ_template.update((env.key, env.value) for env in config.environ)

  def make_php_cgi_environ(self, environ):
    """Returns a dict of environ for php-cgi based off the wsgi environ."""

    user_environ = self.environ_template.copy()

    environ_utils.propagate_environs(environ, user_environ)
    user_environ['REQUEST_METHOD'] = environ.get('REQUEST_METHOD', 'GET')
    user_environ['PATH_INFO'] = environ['PATH_INFO']
    user_environ['QUERY_STRING'] = environ['QUERY_STRING']

    # Construct the partial URL that PHP expects for REQUEST_URI
    # (http://php.net/manual/en/reserved.variables.server.php) using part of
    # the process described in PEP-333
    # (http://www.python.org/dev/peps/pep-0333/#url-reconstruction).
    user_environ['REQUEST_URI'] = urllib.quote(user_environ['PATH_INFO'])
    if user_environ['QUERY_STRING']:
      user_environ['REQUEST_URI'] += '?' + user_environ['QUERY_STRING']

    # Modify the SCRIPT_FILENAME to specify the setup script that readies the
    # PHP environment. Put the user script in REAL_SCRIPT_FILENAME.
    user_environ['REAL_SCRIPT_FILENAME'] = os.path.normpath(
        os.path.join(self.config.application_root,
                     environ[http_runtime_constants.SCRIPT_HEADER].lstrip('/')))
    user_environ['SCRIPT_FILENAME'] = SETUP_PHP_PATH
    user_environ['REMOTE_REQUEST_ID'] = environ[
        http_runtime_constants.REQUEST_ID_ENVIRON]

    # Pass the APPLICATION_ROOT so we can use it in the setup script. We will
    # remove it from the environment before we execute the user script.
    user_environ['APPLICATION_ROOT'] = self.config.application_root

    if 'CONTENT_TYPE' in environ:
      user_environ['CONTENT_TYPE'] = environ['CONTENT_TYPE']
      user_environ['HTTP_CONTENT_TYPE'] = environ['CONTENT_TYPE']

    if 'CONTENT_LENGTH' in environ:
      user_environ['CONTENT_LENGTH'] = environ['CONTENT_LENGTH']
      user_environ['HTTP_CONTENT_LENGTH'] = environ['CONTENT_LENGTH']

    # On Windows, in order to run a side-by-side assembly the specified env
    # must include a valid SystemRoot.
    if 'SYSTEMROOT' in os.environ:
      user_environ['SYSTEMROOT'] = os.environ['SYSTEMROOT']

    # On Windows, TMP & TEMP environmental variables are used by GetTempPath
    # http://msdn.microsoft.com/library/windows/desktop/aa364992(v=vs.85).aspx
    if 'TMP' in os.environ:
      user_environ['TMP'] = os.environ['TMP']
    if 'TEMP' in os.environ:
      user_environ['TEMP'] = os.environ['TEMP']

    if self.config.php_config.enable_debugger:
      user_environ['XDEBUG_CONFIG'] = environ.get('XDEBUG_CONFIG', '')

    return user_environ

  def make_php_cgi_args(self):
    """Returns an array of args for php-cgi based on self.config."""

    # See http://www.php.net/manual/en/ini.core.php#ini.include-path.
    include_paths = ['.', self.config.application_root, SDK_PATH]
    if sys.platform == 'win32':
      # See https://bugs.php.net/bug.php?id=46034 for quoting requirements.
      include_path = 'include_path="%s"' % ';'.join(include_paths)
    else:
      include_path = 'include_path=%s' % ':'.join(include_paths)

    args = [self.config.php_config.php_executable_path, '-d', include_path]

    # Load php.ini from application's root.
    args.extend(['-c', self.config.application_root])

    if self.config.php_config.enable_debugger:
      args.extend(['-d', 'xdebug.default_enable="1"'])
      args.extend(['-d', 'xdebug.overload_var_dump="1"'])
      args.extend(['-d', 'xdebug.remote_enable="1"'])

    if self.config.php_config.xdebug_extension_path:
      args.extend(['-d', 'zend_extension="%s"' %
                   self.config.php_config.xdebug_extension_path])

    if self.config.php_config.gae_extension_path:
      args.extend(['-d', 'extension="%s"' % os.path.basename(
          self.config.php_config.gae_extension_path)])
      args.extend(['-d', 'extension_dir="%s"' % os.path.dirname(
          self.config.php_config.gae_extension_path)])

    return args

  def __call__(self, environ, start_response):
    """Handles an HTTP request for the runtime using a PHP executable.

    Args:
      environ: An environ dict for the request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    user_environ = self.make_php_cgi_environ(environ)

    if 'CONTENT_LENGTH' in environ:
      content = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))
    else:
      content = ''

    args = self.make_php_cgi_args()

    # Handles interactive request.
    request_type = environ.pop(http_runtime_constants.REQUEST_TYPE_HEADER, None)
    if request_type == 'interactive':
      args.extend(['-d', 'html_errors="0"'])
      user_environ[http_runtime_constants.REQUEST_TYPE_HEADER] = request_type

    try:
      # stderr is not captured here so that it propagates to the parent process
      # and gets printed out to consle.
      p = safe_subprocess.start_process(args,
                                        input_string=content,
                                        env=user_environ,
                                        cwd=self.config.application_root,
                                        stdout=subprocess.PIPE)
      stdout, _ = p.communicate()
    except Exception as e:
      logging.exception('Failure to start PHP with: %s', args)
      start_response('500 Internal Server Error',
                     [(http_runtime_constants.ERROR_CODE_HEADER, '1')])
      return ['Failure to start the PHP subprocess with %r:\n%s' % (args, e)]

    if p.returncode:
      if request_type == 'interactive':
        start_response('200 OK', [('Content-Type', 'text/plain')])
        message = httplib.HTTPMessage(cStringIO.StringIO(stdout))
        return [message.fp.read()]
      else:
        logging.error('php failure (%r) with:\nstdout:\n%s',
                      p.returncode, stdout)
        start_response('500 Internal Server Error',
                       [(http_runtime_constants.ERROR_CODE_HEADER, '1')])
        message = httplib.HTTPMessage(cStringIO.StringIO(stdout))
        return [message.fp.read()]

    message = httplib.HTTPMessage(cStringIO.StringIO(stdout))

    if 'Status' in message:
      status = message['Status']
      del message['Status']
    else:
      status = '200 OK'

    # Ensures that we avoid merging repeat headers into a single header,
    # allowing use of multiple Set-Cookie headers.
    headers = []
    for name in message:
      for value in message.getheaders(name):
        headers.append((name, value))

    start_response(status, headers)
    return [message.fp.read()]


def main():
  config = runtime_config_pb2.Config()
  config.ParseFromString(base64.b64decode(sys.stdin.read()))
  server = wsgi_server.WsgiServer(
      ('localhost', 0),
      request_rewriter.runtime_rewriter_middleware(PHPRuntime(config)))
  server.start()
  print server.port
  sys.stdout.close()
  sys.stdout = sys.stderr
  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    pass
  finally:
    server.quit()


if __name__ == '__main__':
  main()
