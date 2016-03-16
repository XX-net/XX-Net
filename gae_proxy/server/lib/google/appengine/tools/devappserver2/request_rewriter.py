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
"""Provides WSGI middleware for rewriting HTTP responses from the runtime.

The rewriting is used for various sanitisation and processing of the response
from the user's application, including:
  - Removing disallowed HTTP response headers.
  - Setting several response headers to their correct values (e.g.,
    Content-Length).
  - Rewriting responses with X-AppEngine-BlobKey with the full blob download.
  - Rewriting fatal response errors (such as a response that is too large) with
    a 500 error page.

The rewriter is runtime-agnostic. It can be applied to any WSGI application
representing an App Engine runtime.
"""



import calendar
import cStringIO
import email
import functools
import logging
import time
import wsgiref.headers

from google.appengine.tools.devappserver2 import blob_download
from google.appengine.tools.devappserver2 import constants


def _ignore_request_headers_rewriter(environ):
  """Ignore specific request headers.

  Certain request headers should not be sent to the application. This function
  removes those headers from the environment. For a complete list of these
  headers please see:

    https://developers.google.com/appengine/docs/python/runtime#Request_Headers

  Args:
    environ: An environ dict for the current request as defined in PEP-333.
  """
  for h in constants.IGNORED_REQUEST_HEADERS:
    h = 'HTTP_' + h.replace('-', '_').upper()
    try:
      del environ[h]
    except KeyError:
      pass


# A list of functions that take an environ and possibly modify it. The functions
# are applied to the request in order.
_REQUEST_REWRITER_CHAIN = [
    _ignore_request_headers_rewriter,
    ]


class RewriterState(object):
  """The state of a WSGI response while it is being processed.

  Instances of this class hold various attributes that make it easier to pass
  data from one rewriter to another.

  A rewriter is a function that takes a RewriterState as an argument, and
  possibly modifies it.

  Attributes:
    environ: An environ dict for the current request as defined in PEP-333.
    status: A status code and message as a string. (e.g., '200 OK'.)
    headers: A wsgiref.headers.Headers containing the response headers.
    body: An iterable of strings containing the response body.
    allow_large_response: A Boolean value. If True, there is no limit to the
      size of the response body. Defaults to False.
  """

  def __init__(self, environ, status, headers, body):
    """Create a new RewriterState.

    Args:
      environ: An environ dict for the current request as defined in PEP-333.
      status: A status code and message as a string. (e.g., '200 OK'.)
      headers: A list of tuples containing the response headers.
      body: An iterable of strings containing the response body.
    """
    self.environ = environ
    self.status = status
    self.headers = wsgiref.headers.Headers(headers)
    self.body = body
    self.allow_large_response = False

  @property
  def status_code(self):
    """The integer value of the response status."""
    return int(self.status.split(' ', 1)[0])


# Header names may be any printable ASCII character other than ':' and space.
# RFC 2616 prohibits other separator characters, but this is consistent with
# HTTPProto::IsValidHeader.
ALLOWED_HEADER_NAME_CHARACTERS = (frozenset([chr(c) for c in range(33, 128)]) -
                                  frozenset([':']))
# Header values may be any printable ASCII character.
ALLOWED_HEADER_VALUE_CHARACTERS = frozenset([chr(c) for c in range(32, 128)])


def _ignore_response_headers_rewriter(ignored_response_headers, state):
  """Ignore specific response headers.

  Certain response headers cannot be modified by an application. For a complete
  list of these headers please see:

    https://developers.google.com/appengine/docs/python/runtime#Responses

  This rewriter simply removes those headers. It also removes non-printable
  ASCII characters and non-ASCII characters, which are disallowed according to
  RFC 2616.

  Args:
    ignored_response_headers: A list of header names to remove.
    state: A RewriterState to modify.
  """
  for name, value in state.headers.items():
    if name.lower() in ignored_response_headers:
      del state.headers[name]
    # Delete a header if its name or value contains non-allowed characters.
    try:
      if isinstance(name, unicode):
        name = name.encode('ascii')
      if isinstance(value, unicode):
        value = value.encode('ascii')
    except UnicodeEncodeError:
      # Contains non-ASCII Unicode characters.
      del state.headers[name]
    if (set(name) - ALLOWED_HEADER_NAME_CHARACTERS or
        set(value) - ALLOWED_HEADER_VALUE_CHARACTERS):
      del state.headers[name]


def _default_content_type_rewriter(state):
  """Set the default Content-Type header.

  Args:
    state: A RewriterState to modify.
  """
  if not 'Content-Type' in state.headers:
    state.headers['Content-Type'] = 'text/html'


def _cache_rewriter(state):
  """Set the default Cache-Control and Expires headers, and sanitize them.

  The default values are only set if the response status allows a body, and only
  if the headers have not been explicitly set by the application.

  If the Set-Cookie response header is set, sanitizes the Cache-Control and
  Expires headers to avoid public caching.

  Args:
    state: A RewriterState to modify.
  """
  # If the response is cacheable, we need to be concerned about the
  # Cache-Control and Expires headers.
  if state.status_code in constants.NO_BODY_RESPONSE_STATUSES:
    return

  if not 'Cache-Control' in state.headers:
    state.headers['Cache-Control'] = 'no-cache'
    if not 'Expires' in state.headers:
      state.headers['Expires'] = 'Fri, 01 Jan 1990 00:00:00 GMT'




  if 'Set-Cookie' in state.headers:
    # It is a security risk to have any caching with Set-Cookie.
    # If Expires is omitted or set to a future date, and response code is
    # cacheable, set Expires to the current date.
    current_date = time.time()
    expires = state.headers.get('Expires')
    reset_expires = True
    if expires:
      expires_time = email.Utils.parsedate(expires)
      if expires_time:
        reset_expires = calendar.timegm(expires_time) >= current_date
    if reset_expires:
      state.headers['Expires'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT',
                                               time.gmtime(current_date))

    # Remove 'public' cache-control directive, and add 'private' if it (or a
    # more restrictive directive) is not already present.
    cache_directives = []
    for header in state.headers.get_all('Cache-Control'):
      cache_directives.extend(v.strip() for v in header.split(','))
    cache_directives = [d for d in cache_directives if d != 'public']
    if not constants.NON_PUBLIC_CACHE_CONTROLS.intersection(cache_directives):
      cache_directives.append('private')
    state.headers['Cache-Control'] = ', '.join(cache_directives)


def _content_length_rewriter(state):
  """Rewrite the Content-Length header.

  Even though Content-Length is not a user modifiable header, App Engine
  sends a correct Content-Length to the user based on the actual response.

  If the response status code indicates that the response is not allowed to
  contain a body, the body will be deleted instead. If the response body is
  longer than the maximum response length, the response will be turned into a
  500 Internal Server Error.

  Args:
    state: A RewriterState to modify.
  """
  # Convert the body into a list of strings, to allow it to be traversed more
  # than once. This is the only way to get the Content-Length before streaming
  # the output.
  state.body = list(state.body)

  length = sum(len(block) for block in state.body)

  if state.status_code in constants.NO_BODY_RESPONSE_STATUSES:
    # Delete the body and Content-Length response header.
    state.body = []
    del state.headers['Content-Length']
  elif state.environ.get('REQUEST_METHOD') == 'HEAD':
    if length:
      # Delete the body, but preserve the Content-Length response header.
      logging.warning('Dropping unexpected body in response to HEAD request')
      state.body = []
  else:
    if (not state.allow_large_response and
        length > constants.MAX_RUNTIME_RESPONSE_SIZE):
      # NOTE: This response is too small to be visible in IE, as it replaces any
      # error page with <512 bytes with its own.
      # http://en.wikipedia.org/wiki/HTTP_404#Custom_error_pages
      logging.error('Response too large: %d, max is %d',
                    length, constants.MAX_RUNTIME_RESPONSE_SIZE)
      new_response = ('HTTP response was too large: %d. The limit is: %d.\n' %
                      (length, constants.MAX_RUNTIME_RESPONSE_SIZE))
      state.status = '500 Internal Server Error'
      state.headers['Content-Type'] = 'text/html'
      state.headers['Content-Length'] = str(len(new_response))
      state.body = [new_response]
    else:
      state.headers['Content-Length'] = str(length)


# A list of functions that take a RewriterState and possibly modify it. The
# functions are applied to the response in order.
_FRONTEND_RESPONSE_REWRITER_CHAIN = [
    blob_download.blobstore_download_rewriter,
    functools.partial(_ignore_response_headers_rewriter,
                      constants.FRONTEND_IGNORED_RESPONSE_HEADERS),
    _default_content_type_rewriter,
    _cache_rewriter,
    _content_length_rewriter,
    ]

_RUNTIME_RESPONSE_REWRITER_CHAIN = [
    _content_length_rewriter,
    functools.partial(_ignore_response_headers_rewriter,
                      constants.RUNTIME_IGNORED_RESPONSE_HEADERS),
    ]


def _rewriter_middleware(request_rewriter_chain, response_rewriter_chain,
                         application, environ, start_response):
  """Wraps an application and applies a chain of rewriters to its response.

  This first applies each function in request_rewriter_chain to the environ. It
  then executes the application, and applies each function in
  response_rewriter_chain to the response.

  Args:
    request_rewriter_chain: A chain of functions to apply to the environ.
    response_rewriter_chain: A chain of functions to apply to the response.
    application: The WSGI application to wrap as defined in PEP-333.
    environ: An environ dict for the current request as defined in PEP-333.
    start_response: A function with semantics defined in PEP-333.

  Returns:
    An iterable of strings containing the body of an HTTP response.
  """
  response_dict = {'headers_sent': False}
  write_body = cStringIO.StringIO()

  def wrapped_start_response(status, response_headers, exc_info=None):
    if exc_info and response_dict['headers_sent']:
      # Headers have already been sent. PEP 333 mandates that this is an error.
      raise exc_info[0], exc_info[1], exc_info[2]

    response_dict['status'] = status
    response_dict['response_headers'] = response_headers
    return write_body.write

  for rewriter in request_rewriter_chain:
    rewriter(environ)

  response_body = iter(application(environ, wrapped_start_response))

  # Get the first non-empty string from the application's response. This ensures
  # that the application has called wrapped_start_response, and allows us to
  # treat future calls to wrapped_start_response as errors.
  first = write_body.getvalue()
  while not first:
    try:
      first = response_body.next()
    except StopIteration:
      break

  # A conformant application must have called wrapped_start_response by this
  # point, and should not call it again unless there is an unrecoverable error.
  response_dict['headers_sent'] = True

  try:
    status = response_dict['status']
    response_headers = response_dict['response_headers']
  except KeyError:
    raise AssertionError('Application yielded before calling start_response.')

  # Prepend first onto response_body.
  def reconstructed_body():
    yield first
    for string in response_body:
      yield string
  body = reconstructed_body()

  state = RewriterState(environ, status, response_headers, body)
  for rewriter in response_rewriter_chain:
    rewriter(state)
  start_response(state.status, state.headers.items())
  return state.body


def frontend_rewriter_middleware(application):
  """WSGI middleware application that applies a chain of response rewriters.

  Args:
    application: The WSGI application to wrap as defined in PEP-333.

  Returns:
    A WSGI application that applies the rewriter chain to the inner application.
  """
  return functools.partial(_rewriter_middleware,
                           _REQUEST_REWRITER_CHAIN,
                           _FRONTEND_RESPONSE_REWRITER_CHAIN,
                           application)


def runtime_rewriter_middleware(application):
  """WSGI middleware application that applies a chain of response rewriters.

  Args:
    application: The WSGI application to wrap as defined in PEP-333.

  Returns:
    A WSGI application that applies the rewriter chain to the inner application.
  """
  return functools.partial(_rewriter_middleware,
                           _REQUEST_REWRITER_CHAIN,
                           _RUNTIME_RESPONSE_REWRITER_CHAIN,
                           application)
