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




"""An extremely simple WSGI web application framework.

This module exports three primary classes: Request, Response, and
RequestHandler. You implement a web application by subclassing RequestHandler.
As WSGI requests come in, they are passed to instances of your RequestHandlers.
The RequestHandler class provides access to the easy-to-use Request and
Response objects so you can interpret the request and write the response with
no knowledge of the esoteric WSGI semantics.  Here is a simple example:

  from google.appengine.ext import webapp
  from google.appengine.ext.webapp.util import run_wsgi_app

  class MainPage(webapp.RequestHandler):
    def get(self):
      self.response.out.write(
        '<html><body><form action="/hello" method="post">'
        'Name: <input name="name" type="text" size="20"> '
        '<input type="submit" value="Say Hello"></form></body></html>')

  class HelloPage(webapp.RequestHandler):
    def post(self):
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write('Hello, %s' % self.request.get('name'))

  application = webapp.WSGIApplication([
    ('/', MainPage),
    ('/hello', HelloPage)
  ], debug=True)

  def main():
    run_wsgi_app(application)

  if __name__ == "__main__":
    main()

The WSGIApplication class maps URI regular expressions to your RequestHandler
classes.  It is a WSGI-compatible application object, so you can use it in
conjunction with wsgiref to make your web application into, e.g., a CGI
script or a simple HTTP server, as in the example above.

The framework does not support streaming output. All output from a response
is stored in memory before it is written.
"""





import cgi
import logging
import re
import StringIO
import sys
import traceback
import urlparse
import webob
import wsgiref.handlers
import wsgiref.headers
import wsgiref.util



wsgiref.handlers.BaseHandler.os_environ = {}


RE_FIND_GROUPS = re.compile('\(.*?\)')
_CHARSET_RE = re.compile(r';\s*charset=([^;\s]*)', re.I)

class Error(Exception):
  """Base of all exceptions in the webapp module."""
  pass


class CannotReversePattern(Error):
  """Thrown when a url_pattern cannot be reversed."""
  pass


class NoUrlFoundError(Error):
  """Thrown when RequestHandler.get_url() fails."""
  pass


class Request(webob.Request):
  """Abstraction for an HTTP request.

  Properties:
    uri: the complete URI requested by the user
    scheme: 'http' or 'https'
    host: the host, including the port
    path: the path up to the ';' or '?' in the URL
    parameters: the part of the URL between the ';' and the '?', if any
    query: the part of the URL after the '?'

  You can access parsed query and POST values with the get() method; do not
  parse the query string yourself.
  """





  request_body_tempfile_limit = 0

  uri = property(lambda self: self.url)
  query = property(lambda self: self.query_string)

  def __init__(self, environ):
    """Constructs a Request object from a WSGI environment.

    If the charset isn't specified in the Content-Type header, defaults
    to UTF-8.

    Args:
      environ: A WSGI-compliant environment dictionary.
    """
    match = _CHARSET_RE.search(environ.get('CONTENT_TYPE', ''))
    if match:
      charset = match.group(1).lower()
    else:
      charset = 'utf-8'

    webob.Request.__init__(self, environ, charset=charset,
                           unicode_errors= 'ignore', decode_param_names=True)

  def get(self, argument_name, default_value='', allow_multiple=False):
    """Returns the query or POST argument with the given name.

    We parse the query string and POST payload lazily, so this will be a
    slower operation on the first call.

    Args:
      argument_name: the name of the query or POST argument
      default_value: the value to return if the given argument is not present
      allow_multiple: return a list of values with the given name (deprecated)

    Returns:
      If allow_multiple is False (which it is by default), we return the first
      value with the given name given in the request. If it is True, we always
      return a list.
    """
    param_value = self.get_all(argument_name)
    if allow_multiple:
      logging.warning('allow_multiple is a deprecated param, please use the '
                      'Request.get_all() method instead.')
    if len(param_value) > 0:
      if allow_multiple:
        return param_value
      return param_value[0]
    else:
      if allow_multiple and not default_value:
        return []
      return default_value

  def get_all(self, argument_name, default_value=None):
    """Returns a list of query or POST arguments with the given name.

    We parse the query string and POST payload lazily, so this will be a
    slower operation on the first call.

    Args:
      argument_name: the name of the query or POST argument
      default_value: the value to return if the given argument is not present,
        None may not be used as a default, if it is then an empty list will be
        returned instead.

    Returns:
      A (possibly empty) list of values.
    """
    if self.charset:
      argument_name = argument_name.encode(self.charset)

    if default_value is None:
      default_value = []

    param_value = self.params.getall(argument_name)

    if param_value is None or len(param_value) == 0:
      return default_value

    for i in xrange(len(param_value)):
      if isinstance(param_value[i], cgi.FieldStorage):
        param_value[i] = param_value[i].value

    return param_value

  def arguments(self):
    """Returns a list of the arguments provided in the query and/or POST.

    The return value is a list of strings.
    """
    return list(set(self.params.keys()))

  def get_range(self, name, min_value=None, max_value=None, default=0):
    """Parses the given int argument, limiting it to the given range.

    Args:
      name: the name of the argument
      min_value: the minimum int value of the argument (if any)
      max_value: the maximum int value of the argument (if any)
      default: the default value of the argument if it is not given

    Returns:
      An int within the given range for the argument
    """
    value = self.get(name, default)
    if value is None:
      return value
    try:
      value = int(value)
    except ValueError:
      value = default
    if value is not None:
      if max_value is not None:
        value = min(value, max_value)
      if min_value is not None:
        value = max(value, min_value)
    return value


class Response(object):
  """Abstraction for an HTTP response.

  Properties:
    out: file pointer for the output stream
    headers: wsgiref.headers.Headers instance representing the output headers
  """
  def __init__(self):
    """Constructs a response with the default settings."""


    self.out = StringIO.StringIO()
    self.__wsgi_headers = []
    self.headers = wsgiref.headers.Headers(self.__wsgi_headers)
    self.headers['Content-Type'] = 'text/html; charset=utf-8'
    self.headers['Cache-Control'] = 'no-cache'

    self.set_status(200)

  @property
  def status(self):
    """Returns current request status code."""
    return self.__status[0]

  @property
  def status_message(self):
    """Returns current request status message."""
    return self.__status[1]

  def set_status(self, code, message=None):
    """Sets the HTTP status code of this response.

    Args:
      message: the HTTP status string to use

    If no status string is given, we use the default from the HTTP/1.1
    specification.
    """
    if not message:
      message = Response.http_status_message(code)
    self.__status = (code, message)

  def has_error(self):
    """Indicates whether the response was an error response."""
    return self.__status[0] >= 400

  def clear(self):
    """Clears all data written to the output stream so that it is empty."""
    self.out.seek(0)
    self.out.truncate(0)

  def wsgi_write(self, start_response):
    """Writes this response using WSGI semantics with the given WSGI function.

    Args:
      start_response: the WSGI-compatible start_response function
    """
    body = self.out.getvalue()
    if isinstance(body, unicode):


      body = body.encode('utf-8')
    elif self.headers.get('Content-Type', '').endswith('; charset=utf-8'):


      try:


        body.decode('utf-8')
      except UnicodeError, e:
        logging.warning('Response written is not UTF-8: %s', e)

    if (self.headers.get('Cache-Control') == 'no-cache' and
        not self.headers.get('Expires')):
      self.headers['Expires'] = 'Mon, 01 Jan 1990 00:00:00 GMT'
    self.headers['Content-Length'] = str(len(body))


    new_headers = []
    for header, value in self.__wsgi_headers:
      if not isinstance(value, basestring):
        value = unicode(value)
      if ('\n' in header or '\r' in header or
          '\n' in value or '\r' in value):
        logging.warning('Replacing newline in header: %s', repr((header,value)))
        value = value.replace('\n','').replace('\r','')
        header = header.replace('\n','').replace('\r','')
      new_headers.append((header, value))
    self.__wsgi_headers = new_headers

    write = start_response('%d %s' % self.__status, self.__wsgi_headers)
    write(body)
    self.out.close()

  def http_status_message(code):
    """Returns the default HTTP status message for the given code.

    Args:
      code: the HTTP code for which we want a message
    """
    if not Response.__HTTP_STATUS_MESSAGES.has_key(code):
      raise Error('Invalid HTTP status code: %d' % code)
    return Response.__HTTP_STATUS_MESSAGES[code]
  http_status_message = staticmethod(http_status_message)

  __HTTP_STATUS_MESSAGES = {
    100: 'Continue',
    101: 'Switching Protocols',
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Moved Temporarily',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    306: 'Unused',
    307: 'Temporary Redirect',
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Time-out',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Large',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',
    428: 'Precondition Required',
    429: 'Too Many Requests',
    431: 'Request Header Fields Too Large',
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Time-out',
    505: 'HTTP Version not supported',
    511: 'Network Authentication Required'
  }


class RequestHandler(object):
  """Our base HTTP request handler. Clients should subclass this class.

  Subclasses should override get(), post(), head(), options(), etc to handle
  different HTTP methods.
  """
  def initialize(self, request, response):
    """Initializes this request handler with the given Request and Response."""
    self.request = request
    self.response = response

  def get(self, *args):
    """Handler method for GET requests."""
    self.error(405)

  def post(self, *args):
    """Handler method for POST requests."""
    self.error(405)

  def head(self, *args):
    """Handler method for HEAD requests."""
    self.error(405)

  def options(self, *args):
    """Handler method for OPTIONS requests."""
    self.error(405)

  def put(self, *args):
    """Handler method for PUT requests."""
    self.error(405)

  def delete(self, *args):
    """Handler method for DELETE requests."""
    self.error(405)

  def trace(self, *args):
    """Handler method for TRACE requests."""
    self.error(405)

  def error(self, code):
    """Clears the response output stream and sets the given HTTP error code.

    Args:
      code: the HTTP status error code (e.g., 501)
    """
    self.response.set_status(code)
    self.response.clear()

  def redirect(self, uri, permanent=False):
    """Issues an HTTP redirect to the given relative URL.

    Args:
      uri: a relative or absolute URI (e.g., '../flowers.html')
      permanent: if true, we use a 301 redirect instead of a 302 redirect
    """
    if permanent:
      self.response.set_status(301)
    else:
      self.response.set_status(302)
    absolute_url = urlparse.urljoin(self.request.uri, uri)
    self.response.headers['Location'] = str(absolute_url)
    self.response.clear()

  def handle_exception(self, exception, debug_mode):
    """Called if this handler throws an exception during execution.

    The default behavior is to call self.error(500) and print a stack trace
    if debug_mode is True.

    Args:
      exception: the exception that was thrown
      debug_mode: True if the web application is running in debug mode
    """
    self.error(500)
    logging.exception(exception)
    if debug_mode:
      lines = ''.join(traceback.format_exception(*sys.exc_info()))
      self.response.clear()
      self.response.out.write('<pre>%s</pre>' % (cgi.escape(lines, quote=True)))

  @classmethod
  def new_factory(cls, *args, **kwargs):
    """Create new request handler factory.

    Use factory method to create reusable request handlers that just
    require a few configuration parameters to construct.  Also useful
    for injecting shared state between multiple request handler
    instances without relying on global variables.  For example, to
    create a set of post handlers that will do simple text transformations
    you can write:

      class ChangeTextHandler(webapp.RequestHandler):

        def __init__(self, transform):
          self.transform = transform

        def post(self):
          response_text = self.transform(
              self.request.request.body_file.getvalue())
          self.response.out.write(response_text)

      application = webapp.WSGIApplication(
          [('/to_lower', ChangeTextHandler.new_factory(str.lower)),
           ('/to_upper', ChangeTextHandler.new_factory(str.upper)),
          ],
          debug=True)

    Text POSTed to /to_lower will be lower cased.
    Text POSTed to /to_upper will be upper cased.
    """
    def new_instance():
      return cls(*args, **kwargs)
    new_instance.__name__ = cls.__name__ + 'Factory'
    return new_instance

  @classmethod
  def get_url(cls, *args, **kargs):
    """Returns the url for the given handler.

    The default implementation uses the patterns passed to the active
    WSGIApplication to create a url. However, it is different from Django's
    urlresolvers.reverse() in the following ways:
      - It does not try to resolve handlers via module loading
      - It does not support named arguments
      - It performs some post-prosessing on the url to remove some regex
        operators.
      - It will try to fill in the left-most missing arguments with the args
        used in the active request.

    Args:
      args: Parameters for the url pattern's groups.
      kwargs: Optionally contains 'implicit_args' that can either be a boolean
              or a tuple. When it is True, it will use the arguments to the
              active request as implicit arguments. When it is False (default),
              it will not use any implicit arguments. When it is a tuple, it
              will use the tuple as the implicit arguments.
              the left-most args if some are missing from args.

    Returns:
      The url for this handler/args combination.

    Raises:
      NoUrlFoundError: No url pattern for this handler has the same
        number of args that were passed in.
    """


    app = WSGIApplication.active_instance
    pattern_map = app._pattern_map

    implicit_args = kargs.get('implicit_args', ())
    if implicit_args == True:
      implicit_args = app.current_request_args



    min_params = len(args)

    for pattern_tuple in pattern_map.get(cls, ()):
      num_params_in_pattern = pattern_tuple[1]
      if num_params_in_pattern < min_params:
        continue

      try:

        num_implicit_args = max(0, num_params_in_pattern - len(args))
        merged_args = implicit_args[:num_implicit_args] + args

        url = _reverse_url_pattern(pattern_tuple[0], *merged_args)



        url = url.replace('\\', '')
        url = url.replace('?', '')
        return url
      except CannotReversePattern:
        continue

    logging.warning('get_url failed for Handler name: %r, Args: %r',
                    cls.__name__, args)
    raise NoUrlFoundError


def _reverse_url_pattern(url_pattern, *args):
  """Turns a regex that matches a url back into a url by replacing
  the url pattern's groups with the given args. Removes '^' and '$'
  from the result.

  Args:
    url_pattern: A pattern used to match a URL.
    args: list of values corresponding to groups in url_pattern.

  Returns:
    A string with url_pattern's groups filled in values from args.

  Raises:
     CannotReversePattern if either there aren't enough args to fill
     url_pattern's groups, or if any arg isn't matched by the regular
     expression fragment in the corresponding group.
  """

  group_index = [0]

  def expand_group(match):
    group = match.group(1)
    try:

      value = str(args[group_index[0]])
      group_index[0] += 1
    except IndexError:
      raise CannotReversePattern('Not enough arguments in url tag')

    if not re.match(group + '$', value):
      raise CannotReversePattern("Value %r doesn't match (%r)" % (value, group))
    return value

  result = re.sub(r'\(([^)]+)\)', expand_group, url_pattern.pattern)
  result = result.replace('^', '')
  result = result.replace('$', '')
  return result


class RedirectHandler(RequestHandler):
  """Simple redirection handler.

  Easily configure URLs to redirect to alternate targets.  For example,
  to configure a web application so that the root URL is always redirected
  to the /home path, do:

    application = webapp.WSGIApplication(
        [('/', webapp.RedirectHandler.new_factory('/home', permanent=True)),
         ('/home', HomeHandler),
        ],
        debug=True)

  Handler also useful for setting up obsolete URLs to redirect to new paths.
  """

  def __init__(self, path, permanent=False):
    """Constructor.

    Do not use directly.  Configure using new_factory method.

    Args:
      path: Path to redirect to.
      permanent: if true, we use a 301 redirect instead of a 302 redirect.
    """
    self.path = path
    self.permanent = permanent

  def get(self):
    self.redirect(self.path, permanent=self.permanent)


class WSGIApplication(object):
  """Wraps a set of webapp RequestHandlers in a WSGI-compatible application.

  To use this class, pass a list of (URI regular expression, RequestHandler)
  pairs to the constructor, and pass the class instance to a WSGI handler.
  See the example in the module comments for details.

  The URL mapping is first-match based on the list ordering.
  """

  REQUEST_CLASS = Request
  RESPONSE_CLASS = Response

  def __init__(self, url_mapping, debug=False):
    """Initializes this application with the given URL mapping.

    Args:
      url_mapping: list of (URI regular expression, RequestHandler) pairs
                   (e.g., [('/', ReqHan)])
      debug: if true, we send Python stack traces to the browser on errors
    """
    self._init_url_mappings(url_mapping)
    self.__debug = debug


    WSGIApplication.active_instance = self
    self.current_request_args = ()

  def __call__(self, environ, start_response):
    """Called by WSGI when a request comes in."""
    request = self.REQUEST_CLASS(environ)
    response = self.RESPONSE_CLASS()


    WSGIApplication.active_instance = self


    handler = None
    groups = ()
    for regexp, handler_class in self._url_mapping:
      match = regexp.match(request.path)
      if match:
        try:
          handler = handler_class()



          handler.initialize(request, response)
        except Exception, e:
          if handler is None:
            handler = RequestHandler()
          handler.response = response
          handler.handle_exception(e, self.__debug)
          response.wsgi_write(start_response)
          return ['']
        groups = match.groups()
        break


    self.current_request_args = groups


    if handler:
      try:
        method = environ['REQUEST_METHOD']
        if method == 'GET':
          handler.get(*groups)
        elif method == 'POST':
          handler.post(*groups)
        elif method == 'HEAD':
          handler.head(*groups)
        elif method == 'OPTIONS':
          handler.options(*groups)
        elif method == 'PUT':
          handler.put(*groups)
        elif method == 'DELETE':
          handler.delete(*groups)
        elif method == 'TRACE':
          handler.trace(*groups)
        else:
          handler.error(501)
      except Exception, e:
        handler.handle_exception(e, self.__debug)
    else:
      response.set_status(404)


    response.wsgi_write(start_response)
    return ['']

  def _init_url_mappings(self, handler_tuples):
    """Initializes the maps needed for mapping urls to handlers and handlers
    to urls.

    Args:
      handler_tuples: list of (URI, RequestHandler) pairs.
    """





    handler_map = {}

    pattern_map = {}

    url_mapping = []


    for regexp, handler in handler_tuples:

      try:
        handler_name = handler.__name__
      except AttributeError:
        pass
      else:
        handler_map[handler_name] = handler


      if not regexp.startswith('^'):
        regexp = '^' + regexp
      if not regexp.endswith('$'):
        regexp += '$'

      if regexp == '^/form$':
        logging.warning('The URL "/form" is reserved and will not be matched.')

      compiled = re.compile(regexp)
      url_mapping.append((compiled, handler))


      num_groups = len(RE_FIND_GROUPS.findall(regexp))
      handler_patterns = pattern_map.setdefault(handler, [])
      handler_patterns.append((compiled, num_groups))

    self._handler_map = handler_map
    self._pattern_map = pattern_map
    self._url_mapping = url_mapping

  def get_registered_handler_by_name(self, handler_name):
    """Returns the handler given the handler's name.

    This uses the application's url mapping.

    Args:
      handler_name: The __name__ of a handler to return.

    Returns:
      The handler with the given name.

    Raises:
      KeyError: If the handler name is not found in the parent application.
    """
    try:
      return self._handler_map[handler_name]
    except:
      logging.error('Handler does not map to any urls: %s', handler_name)
      raise
