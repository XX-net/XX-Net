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




"""A Python 2.7 runtime module.

Provides a Python 2.7 runtime that calls into user-provided code using a CGI or
WSGI interface.
"""








import cStringIO
import thread
import threading
import urlparse

from google.appengine.api.logservice import logservice
from google.appengine.runtime import cgi
from google.appengine.runtime import request_environment
from google.appengine.runtime import wsgi


def _MakeStartNewThread(base_start_new_thread):
  """Returns a replacement for start_new_thread that inherits environment.

  Returns a function with an interface that matches thread.start_new_thread
  where the new thread inherits the request environment of
  request_environment.current_request and cleans it up when it terminates.

  Args:
    base_start_new_thread: The thread.start_new_thread function to call to
        create a new thread.

  Returns:
    A replacement for start_new_thread.
  """

  def StartNewThread(target, args, kw=None):
    """A replacement for thread.start_new_thread.

    A replacement for thread.start_new_thread that inherits RequestEnvironment
    state from its creator and cleans up that state when it terminates.

    Args:
      See thread.start_new_thread.

    Returns:
      See thread.start_new_thread.
    """
    if kw is None:
      kw = {}
    cloner = request_environment.current_request.CloneRequestEnvironment()

    def Run():
      try:
        cloner()
        target(*args, **kw)
      finally:
        request_environment.current_request.Clear()
    return base_start_new_thread(Run, ())
  return StartNewThread


def PatchStartNewThread(thread_module=thread, threading_module=threading):
  """Installs a start_new_thread replacement created by _MakeStartNewThread."""
  thread_module.start_new_thread = _MakeStartNewThread(
      thread_module.start_new_thread)
  reload(threading_module)


def HandleRequest(environ, handler_name, url, post_data, application_root,
                  python_lib, import_hook=None):
  """Handles a single request.

  Handles a single request for handler_name by dispatching to the appropriate
  server interface implementation (CGI or WSGI) depending on the form of
  handler_name. The arguments are processed to fill url and post-data related
  environ members.

  Args:
    environ: A dict containing the environ for this request (i.e. for
        os.environ).
    handler_name: A str containing the user-specified handler to use for this
        request, i.e. the script parameter for a handler in app.yaml; e.g.
        'package.module.application' for a WSGI handler or 'path/to/handler.py'
        for a CGI handler.
    url: The requested url.
    post_data: The post data for this request.
    application_root: A str containing the root path of the application.
    python_lib: A str containing the root the Python App Engine library.
    import_hook: Optional import hook (PEP 302 style loader).

  Returns:
    A dict containing:
      error: App Engine error code. 0 for OK, 1 for error.
      response_code: The HTTP response code.
      headers: A list of str tuples (key, value) of HTTP headers.
      body: A str of the body of the response
      logs: A list of tuples (timestamp_usec, severity, message) of log entries.
          timestamp_usec is a long, severity is int and message is str. Severity
          levels are 0..4 for Debug, Info, Warning, Error, Critical.
  """
  try:
    error = logservice.LogsBuffer()
    request_environment.current_request.Init(error, environ)
    url = urlparse.urlsplit(url)
    environ.update(CgiDictFromParsedUrl(url))
    if post_data:









      environ['CONTENT_LENGTH'] = str(len(post_data))
      if 'HTTP_CONTENT_TYPE' in environ:
        environ['CONTENT_TYPE'] = environ['HTTP_CONTENT_TYPE']
      else:
        environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
    post_data = cStringIO.StringIO(post_data)

    if '/' in handler_name or handler_name.endswith('.py'):
      response = cgi.HandleRequest(environ, handler_name, url, post_data, error,
                                   application_root, python_lib, import_hook)
    else:
      response = wsgi.HandleRequest(environ, handler_name, url, post_data,
                                    error)
    response['logs'] = error.parse_logs()
    return response
  finally:
    request_environment.current_request.Clear()


def CgiDictFromParsedUrl(url):
  """Extract CGI variables from a parsed url into a dict.

  Returns a dict containing the following CGI variables for the provided url:
  SERVER_PORT, QUERY_STRING, SERVER_NAME and PATH_INFO.

  Args:
    url: An instance of urlparse.SplitResult.

  Returns:
    A dict containing the CGI variables derived from url.
  """
  environ = {}
  if url.port is not None:
    environ['SERVER_PORT'] = str(url.port)
  elif url.scheme == 'https':
    environ['SERVER_PORT'] = '443'
  elif url.scheme == 'http':
    environ['SERVER_PORT'] = '80'
  environ['QUERY_STRING'] = url.query
  environ['SERVER_NAME'] = url.hostname
  if url.path:
    environ['PATH_INFO'] = urlparse.unquote(url.path)
  else:
    environ['PATH_INFO'] = '/'
  return environ
