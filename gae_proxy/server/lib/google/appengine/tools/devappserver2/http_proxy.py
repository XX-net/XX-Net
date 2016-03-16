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
"""Forwards HTTP requests to an application instance on a given host and port.

An instance (also referred to as a runtime process) handles dynamic content
only. Static files are handled separately.
"""

import contextlib
import httplib
import logging
import urllib
import wsgiref.headers

from google.appengine.tools.devappserver2 import http_runtime_constants
from google.appengine.tools.devappserver2 import http_utils
from google.appengine.tools.devappserver2 import instance
from google.appengine.tools.devappserver2 import login
from google.appengine.tools.devappserver2 import util


class HttpProxy:
  """Forwards HTTP requests to an application instance."""
  def __init__(self, host, port, instance_died_unexpectedly,
               instance_logs_getter, error_handler_file, prior_error=None,
               request_id_header_name=None):
    """Initializer for HttpProxy.

    Args:
      host: A hostname or an IP address of where application instance is
          running.
      port: Port that application instance is listening on.
      instance_died_unexpectedly: Function returning True if instance has
          unexpectedly died.
      instance_logs_getter: Function returning logs from the instance.
      error_handler_file: Application specific error handler for default error
          code if specified (only default error code is supported by
          Dev AppServer).
      prior_error: Errors occurred before (for example during creation of an
          instance). In case prior_error is not None handle will always return
          corresponding error message without even trying to connect to the
          instance.
      request_id_header_name: Optional string name used to pass request ID to
          API server.  Defaults to http_runtime_constants.REQUEST_ID_HEADER.
    """
    self._host = host
    self._port = port
    self._instance_died_unexpectedly = instance_died_unexpectedly
    self._instance_logs_getter = instance_logs_getter
    self._error_handler_file = error_handler_file
    self._prior_error = prior_error
    self.request_id_header_name = request_id_header_name
    if self.request_id_header_name is None:
      self.request_id_header_name = http_runtime_constants.REQUEST_ID_HEADER

  def _respond_with_error(self, message, start_response):
    instance_logs = self._instance_logs_getter()
    if instance_logs:
      message += '\n\n' + instance_logs
    # TODO: change 'text/plain' to 'text/plain; charset=utf-8'
    # throughout devappserver2.
    start_response('500 Internal Server Error',
                   [('Content-Type', 'text/plain'),
                    ('Content-Length', str(len(message)))])
    return message

  def wait_for_connection(self, retries=100000):
    """Waits while instance is booting.

    Args:
      retries: int, Number of connection retries.

    Raises:
      http_utils.HostNotReachable: if host:port can't be reached after given
          number of retries.
    """
    # If there was a prior error, we don't need to wait for a connection.
    if self._prior_error:
      return

    http_utils.wait_for_connection(self._host, self._port, retries)

  def handle(self, environ, start_response, url_map, match, request_id,
             request_type):
    """Serves this request by forwarding it to the runtime process.

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

    if self._prior_error:
      logging.error(self._prior_error)
      yield self._respond_with_error(self._prior_error, start_response)
      return

    environ[http_runtime_constants.SCRIPT_HEADER] = match.expand(url_map.script)
    if request_type == instance.BACKGROUND_REQUEST:
      environ[http_runtime_constants.REQUEST_TYPE_HEADER] = 'background'
    elif request_type == instance.SHUTDOWN_REQUEST:
      environ[http_runtime_constants.REQUEST_TYPE_HEADER] = 'shutdown'
    elif request_type == instance.INTERACTIVE_REQUEST:
      environ[http_runtime_constants.REQUEST_TYPE_HEADER] = 'interactive'

    for name in http_runtime_constants.ENVIRONS_TO_PROPAGATE:
      if http_runtime_constants.APPENGINE_ENVIRON_PREFIX + name not in environ:
        value = environ.get(name, None)
        if value is not None:
          environ[
              http_runtime_constants.APPENGINE_ENVIRON_PREFIX + name] = value
    headers = util.get_headers_from_environ(environ)
    if environ.get('QUERY_STRING'):
      url = '%s?%s' % (urllib.quote(environ['PATH_INFO']),
                       environ['QUERY_STRING'])
    else:
      url = urllib.quote(environ['PATH_INFO'])
    if 'CONTENT_LENGTH' in environ:
      headers['CONTENT-LENGTH'] = environ['CONTENT_LENGTH']
      data = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))
    else:
      data = None

    cookies = environ.get('HTTP_COOKIE')
    user_email, admin, user_id = login.get_user_info(cookies)
    if user_email:
      nickname, organization = user_email.split('@', 1)
    else:
      nickname = ''
      organization = ''
    headers[self.request_id_header_name] = request_id
    headers[http_runtime_constants.APPENGINE_HEADER_PREFIX + 'User-Id'] = (
        user_id)
    headers[http_runtime_constants.APPENGINE_HEADER_PREFIX + 'User-Email'] = (
        user_email)
    headers[
        http_runtime_constants.APPENGINE_HEADER_PREFIX + 'User-Is-Admin'] = (
            str(int(admin)))
    headers[
        http_runtime_constants.APPENGINE_HEADER_PREFIX + 'User-Nickname'] = (
            nickname)
    headers[http_runtime_constants.APPENGINE_HEADER_PREFIX +
            'User-Organization'] = organization
    headers['X-AppEngine-Country'] = 'ZZ'
    connection = httplib.HTTPConnection(self._host, self._port)
    with contextlib.closing(connection):
      try:
        connection.connect()
        connection.request(environ.get('REQUEST_METHOD', 'GET'),
                           url,
                           data,
                           dict(headers.items()))

        try:
          response = connection.getresponse()
        except httplib.HTTPException as e:
          # The runtime process has written a bad HTTP response. For example,
          # a Go runtime process may have crashed in app-specific code.
          yield self._respond_with_error(
              'the runtime process gave a bad HTTP response: %s' % e,
              start_response)
          return

        # Ensures that we avoid merging repeat headers into a single header,
        # allowing use of multiple Set-Cookie headers.
        headers = []
        for name in response.msg:
          for value in response.msg.getheaders(name):
            headers.append((name, value))

        response_headers = wsgiref.headers.Headers(headers)

        if self._error_handler_file and (
            http_runtime_constants.ERROR_CODE_HEADER in response_headers):
          try:
            with open(self._error_handler_file) as f:
              content = f.read()
          except IOError:
            content = 'Failed to load error handler'
            logging.exception('failed to load error file: %s',
                              self._error_handler_file)
          start_response('500 Internal Server Error',
                         [('Content-Type', 'text/html'),
                          ('Content-Length', str(len(content)))])
          yield content
          return
        del response_headers[http_runtime_constants.ERROR_CODE_HEADER]
        start_response('%s %s' % (response.status, response.reason),
                       response_headers.items())

        # Yield the response body in small blocks.
        while True:
          try:
            block = response.read(512)
            if not block:
              break
            yield block
          except httplib.HTTPException:
            # The runtime process has encountered a problem, but has not
            # necessarily crashed. For example, a Go runtime process' HTTP
            # handler may have panicked in app-specific code (which the http
            # package will recover from, so the process as a whole doesn't
            # crash). At this point, we have already proxied onwards the HTTP
            # header, so we cannot retroactively serve a 500 Internal Server
            # Error. We silently break here; the runtime process has presumably
            # already written to stderr (via the Tee).
            break
      except Exception:
        if self._instance_died_unexpectedly():
          yield self._respond_with_error(
              'the runtime process for the instance running on port %d has '
              'unexpectedly quit' % self._port, start_response)
        else:
          raise
