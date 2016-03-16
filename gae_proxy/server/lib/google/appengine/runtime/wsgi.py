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




"""WSGI server interface to Python runtime.

WSGI-compliant interface between the Python runtime and user-provided Python
code.
"""








import logging
import sys
import types

from google.appengine import runtime
from google.appengine.api import lib_config




_DEADLINE_DURING_LOADING = 22


class Error(Exception):
  pass


class InvalidResponseError(Error):
  """An error indicating that the response is invalid."""
  pass


def _GetTypeName(x):
  """Returns a user-friendly name descriping the given object's type."""
  if type(x) is types.InstanceType:
    return x.__class__.__name__
  else:
    return type(x).__name__






def LoadObject(object_name):
  """Find and return a Python object specified by object_name.

  Packages and modules are imported as necessary.

  Args:
    object_name: (string) An object specification.

  Returns:
    A tuple of the form (object, string, error).  If object_name can be
    fully traversed, object is the specified object, string is the filename
    containing the object, and error is None. Otherwise, object_name is
    maximal partial match specified by object_name, string is the filename
    containing object, and error is an ImportError.
  """
  containing_file = None
  path = object_name.split('.')
  obj = __import__(path[0])
  is_parent_package = True
  cumulative_path = path[0]
  for name in path[1:]:
    if hasattr(obj, '__file__'):
      containing_file = obj.__file__
    is_parent_package = is_parent_package and hasattr(obj, '__path__')
    cumulative_path += '.' + name
    if hasattr(obj, name):
      obj = getattr(obj, name)
    elif is_parent_package:
      __import__(cumulative_path)
      obj = getattr(obj, name)
    else:
      return obj, containing_file, ImportError(
          '%s has no attribute %s' % (obj, name))



  return obj, containing_file, None


class WsgiRequest(object):
  """A single WSGI request."""

  def __init__(self, environ, handler_name, url, post_data, error):
    """Creates a single WSGI request.

    Creates a request for handler_name in the form 'path.to.handler' for url
    with the environment contained in environ.

    Args:
      environ: A dict containing the environ for this request (e.g. like from
          os.environ).
      handler_name: A str containing the user-specified handler to use for this
          request as specified in the script field of a handler in app.yaml
          using the Python dot notation; e.g. 'package.module.application'.
      url: An urlparse.SplitResult instance containing the request url.
      post_data: A stream containing the post data for this request.
      error: A stream into which errors are to be written.
    """
    self._handler = handler_name
    self._status = 500
    self._response_headers = []
    self._started_handling = False
    self._body = []
    self._written_body = []
    environ['wsgi.multiprocess'] = True
    environ['wsgi.run_once'] = False
    environ['wsgi.version'] = (1, 0)


    environ.setdefault('wsgi.multithread', False)
    self._error = error
    environ['wsgi.url_scheme'] = url.scheme
    environ['wsgi.input'] = post_data
    environ['wsgi.errors'] = self._error
    self._environ = environ

  def _Write(self, body_data):
    """Writes some body_data to the response.

    Args:
      body_data: data to be written.

    Raises:
      InvalidResponseError: body_data is not a str.
    """
    if not isinstance(body_data, str):
      raise InvalidResponseError('body_data must be a str, got %r' %
                                 _GetTypeName(body_data))
    self._written_body.append(body_data)

  def _StartResponse(self, status, response_headers, exc_info=None):
    """A PEP 333 start_response callable.

    Implements the start_response behaviour of PEP 333. Sets the status code and
    response headers as provided. If exc_info is not None, then the previously
    provided status and response headers are replaced; this implementation
    buffers the complete response so valid use of exc_info never raises an
    exception.  Otherwise, _StartResponse may only be called once.

    Args:
      status: A string containing the status code and status string.
      response_headers: a list of pairs representing header keys and values.
      exc_info: exception info as obtained from sys.exc_info().

    Returns:
      A Write method as per PEP 333.

    Raises:
      InvalidResponseError: The arguments passed are invalid.
    """
    if not isinstance(status, str):
      raise InvalidResponseError('status must be a str, got %r (%r)' %
                                 (_GetTypeName(status), status))
    if not status:
      raise InvalidResponseError('status must not be empty')
    if not isinstance(response_headers, list):
      raise InvalidResponseError('response_headers must be a list, got %r' %
                                 _GetTypeName(response_headers))
    for header in response_headers:
      if not isinstance(header, tuple):
        raise InvalidResponseError('response_headers items must be tuple, '
                                   'got %r' % _GetTypeName(header))
      if len(header) != 2:
        raise InvalidResponseError('header tuples must have length 2, '
                                   'actual length %d' % len(header))
      name, value = header
      if not isinstance(name, str):
        raise InvalidResponseError('header names must be str, got %r (%r)' %
                                   (_GetTypeName(name), name))
      if not isinstance(value, str):
        raise InvalidResponseError('header values must be str, '
                                   'got %r (%r) for %r' %
                                   (_GetTypeName(value), value, name))
    try:
      status_number = int(status.split(' ')[0])
    except ValueError:
      raise InvalidResponseError('status code %r is not a number' % status)
    if status_number < 200 or status_number >= 600:
      raise InvalidResponseError('status code must be in the range [200,600), '
                                 'got %d' % status_number)

    if exc_info is not None:

      self._status = status_number
      self._response_headers = response_headers
      exc_info = None
    elif self._started_handling:
      raise InvalidResponseError('_StartResponse may only be called once'
                                 ' without exc_info')
    else:
      self._status = status_number
      self._response_headers = response_headers
    self._started_handling = True
    self._body = []
    self._written_body = []
    return self._Write

  def Handle(self):
    """Handles the request represented by the WsgiRequest object.

    Loads the handler from the handler name provided. Calls the handler with the
    environ. Any exceptions in loading the user handler and executing it are
    caught and logged.

    Returns:
      A dict containing:
        error: App Engine error code. 0 for OK, 1 for error.
        response_code: HTTP response code.
        headers: A list of tuples (key, value) of HTTP headers.
        body: A str of the body of the response
    """
    try:
      handler = _config_handle.add_wsgi_middleware(self._LoadHandler())
    except runtime.DeadlineExceededError:








      exc_info = sys.exc_info()
      try:
        logging.error('', exc_info=exc_info)
      except runtime.DeadlineExceededError:

        logging.exception('Deadline exception occurred while logging a '
                          'deadline exception.')



        logging.error('Original exception:', exc_info=exc_info)
      return {'error': _DEADLINE_DURING_LOADING}
    except:
      logging.exception('')
      return {'error': 1}
    result = None
    try:
      result = handler(dict(self._environ), self._StartResponse)
      for chunk in result:
        if not isinstance(chunk, str):
          raise InvalidResponseError('handler must return an iterable of str')
        self._body.append(chunk)



      body = ''.join(self._written_body + self._body)
      return {'response_code': self._status, 'headers':
              self._response_headers, 'body': body}
    except:
      logging.exception('')
      return {'error': 1}
    finally:
      if hasattr(result, 'close'):
        result.close()

  def _LoadHandler(self):
    """Find and return a Python object with name self._handler.

    Sets _environ so that PATH_TRANSLATED is equal to the file containing the
    handler.

    Packages and modules are imported as necessary.

    Returns:
      The python object specified by self._handler.

    Raises:
      ImportError: An element of the path cannot be resolved.
    """
    handler, path, err = LoadObject(self._handler)
    self._environ['PATH_TRANSLATED'] = path
    if err:
      raise err
    return handler


def HandleRequest(environ, handler_name, url, post_data, error):
  """Handle a single WSGI request.

  Creates a request for handler_name in the form 'path.to.handler' for url with
  the environment contained in environ.

  Args:
    environ: A dict containing the environ for this request (e.g. like from
        os.environ).
    handler_name: A str containing the user-specified handler to use for this
        request as specified in the script field of a handler in app.yaml using
        the Python dot notation; e.g. 'package.module.application'.
    url: An urlparse.SplitResult instance containing the request url.
    post_data: A stream containing the post data for this request.
    error: A stream into which errors are to be written.

  Returns:
    A dict containing:
      error: App Engine error code. 0 for OK, 1 for error.
      response_code: HTTP response code.
      headers: A list of tuples (key, value) of HTTP headers.
      body: A str of the body of the response
  """
  return WsgiRequest(environ, handler_name, url, post_data, error).Handle()

_config_handle = lib_config.register(
    'webapp',
    {'add_wsgi_middleware': lambda app: app})
