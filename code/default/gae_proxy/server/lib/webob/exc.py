"""
HTTP Exception
--------------
This module processes Python exceptions that relate to HTTP exceptions
by defining a set of exceptions, all subclasses of HTTPException.
Each exception, in addition to being a Python exception that can be
raised and caught, is also a WSGI application and ``webob.Response``
object.

This module defines exceptions according to RFC 2068 [1]_ : codes with
100-300 are not really errors; 400's are client errors, and 500's are
server errors.  According to the WSGI specification [2]_ , the application
can call ``start_response`` more then once only under two conditions:
(a) the response has not yet been sent, or (b) if the second and
subsequent invocations of ``start_response`` have a valid ``exc_info``
argument obtained from ``sys.exc_info()``.  The WSGI specification then
requires the server or gateway to handle the case where content has been
sent and then an exception was encountered.

Exception
  HTTPException
    HTTPOk
      * 200 - HTTPOk
      * 201 - HTTPCreated
      * 202 - HTTPAccepted
      * 203 - HTTPNonAuthoritativeInformation
      * 204 - HTTPNoContent
      * 205 - HTTPResetContent
      * 206 - HTTPPartialContent
    HTTPRedirection
      * 300 - HTTPMultipleChoices
      * 301 - HTTPMovedPermanently
      * 302 - HTTPFound
      * 303 - HTTPSeeOther
      * 304 - HTTPNotModified
      * 305 - HTTPUseProxy
      * 306 - Unused (not implemented, obviously)
      * 307 - HTTPTemporaryRedirect
    HTTPError
      HTTPClientError
        * 400 - HTTPBadRequest
        * 401 - HTTPUnauthorized
        * 402 - HTTPPaymentRequired
        * 403 - HTTPForbidden
        * 404 - HTTPNotFound
        * 405 - HTTPMethodNotAllowed
        * 406 - HTTPNotAcceptable
        * 407 - HTTPProxyAuthenticationRequired
        * 408 - HTTPRequestTimeout
        * 409 - HTTPConflict
        * 410 - HTTPGone
        * 411 - HTTPLengthRequired
        * 412 - HTTPPreconditionFailed
        * 413 - HTTPRequestEntityTooLarge
        * 414 - HTTPRequestURITooLong
        * 415 - HTTPUnsupportedMediaType
        * 416 - HTTPRequestRangeNotSatisfiable
        * 417 - HTTPExpectationFailed
        * 428 - HTTPPreconditionRequired
        * 429 - HTTPTooManyRequests
        * 431 - HTTPRequestHeaderFieldsTooLarge
      HTTPServerError
        * 500 - HTTPInternalServerError
        * 501 - HTTPNotImplemented
        * 502 - HTTPBadGateway
        * 503 - HTTPServiceUnavailable
        * 504 - HTTPGatewayTimeout
        * 505 - HTTPVersionNotSupported
        * 511 - HTTPNetworkAuthenticationRequired

Subclass usage notes:
---------------------

The HTTPException class is complicated by 4 factors:

  1. The content given to the exception may either be plain-text or
     as html-text.

  2. The template may want to have string-substitutions taken from
     the current ``environ`` or values from incoming headers. This
     is especially troublesome due to case sensitivity.

  3. The final output may either be text/plain or text/html
     mime-type as requested by the client application.

  4. Each exception has a default explanation, but those who
     raise exceptions may want to provide additional detail.

Subclass attributes and call parameters are designed to provide an easier path
through the complications.

Attributes:

   ``code``
       the HTTP status code for the exception

   ``title``
       remainder of the status line (stuff after the code)

   ``explanation``
       a plain-text explanation of the error message that is
       not subject to environment or header substitutions;
       it is accessible in the template via %(explanation)s

   ``detail``
       a plain-text message customization that is not subject
       to environment or header substitutions; accessible in
       the template via %(detail)s

   ``body_template``
       a content fragment (in HTML) used for environment and
       header substitution; the default template includes both
       the explanation and further detail provided in the
       message

Parameters:

   ``detail``
     a plain-text override of the default ``detail``

   ``headers``
     a list of (k,v) header pairs

   ``comment``
     a plain-text additional information which is
     usually stripped/hidden for end-users

   ``body_template``
     a string.Template object containing a content fragment in HTML
     that frames the explanation and further detail

To override the template (which is HTML content) or the plain-text
explanation, one must subclass the given exception; or customize it
after it has been created.  This particular breakdown of a message
into explanation, detail and template allows both the creation of
plain-text and html messages for various clients as well as
error-free substitution of environment variables and headers.


The subclasses of :class:`~_HTTPMove`
(:class:`~HTTPMultipleChoices`, :class:`~HTTPMovedPermanently`,
:class:`~HTTPFound`, :class:`~HTTPSeeOther`, :class:`~HTTPUseProxy` and
:class:`~HTTPTemporaryRedirect`) are redirections that require a ``Location``
field. Reflecting this, these subclasses have two additional keyword arguments:
``location`` and ``add_slash``.

Parameters:

    ``location``
      to set the location immediately

    ``add_slash``
      set to True to redirect to the same URL as the request, except with a
      ``/`` appended

Relative URLs in the location will be resolved to absolute.

References:

.. [1] http://www.python.org/peps/pep-0333.html#error-handling
.. [2] http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.5


"""

from string import Template
import re
import sys

from webob.compat import (
    class_types,
    text_,
    text_type,
    urlparse,
    )
from webob.request import Request
from webob.response import Response
from webob.util import (
    html_escape,
    warn_deprecation,
    )

tag_re = re.compile(r'<.*?>', re.S)
br_re = re.compile(r'<br.*?>', re.I|re.S)
comment_re = re.compile(r'<!--|-->')

def no_escape(value):
    if value is None:
        return ''
    if not isinstance(value, text_type):
        if hasattr(value, '__unicode__'):
            value = value.__unicode__()
        if isinstance(value, bytes):
            value = text_(value, 'utf-8')
        else:
            value = text_type(value)
    return value

def strip_tags(value):
    value = value.replace('\n', ' ')
    value = value.replace('\r', '')
    value = br_re.sub('\n', value)
    value = comment_re.sub('', value)
    value = tag_re.sub('', value)
    return value

class HTTPException(Exception):
    def __init__(self, message, wsgi_response):
        Exception.__init__(self, message)
        self.wsgi_response = wsgi_response

    def __call__(self, environ, start_response):
        return self.wsgi_response(environ, start_response)

    # TODO: remove in version 1.3
    @property
    def exception(self):
        warn_deprecation(
            "As of WebOb 1.2, raise the HTTPException instance directly "
            "instead of raising the result of 'HTTPException.exception'",
            '1.3', 2)
        return self

class WSGIHTTPException(Response, HTTPException):

    ## You should set in subclasses:
    # code = 200
    # title = 'OK'
    # explanation = 'why this happens'
    # body_template_obj = Template('response template')
    code = None
    title = None
    explanation = ''
    body_template_obj = Template('''\
${explanation}<br /><br />
${detail}
${html_comment}
''')

    plain_template_obj = Template('''\
${status}

${body}''')

    html_template_obj = Template('''\
<html>
 <head>
  <title>${status}</title>
 </head>
 <body>
  <h1>${status}</h1>
  ${body}
 </body>
</html>''')

    ## Set this to True for responses that should have no request body
    empty_body = False

    def __init__(self, detail=None, headers=None, comment=None,
                 body_template=None, **kw):
        Response.__init__(self,
                          status='%s %s' % (self.code, self.title),
                          **kw)
        Exception.__init__(self, detail)
        if headers:
            self.headers.extend(headers)
        self.detail = detail
        self.comment = comment
        if body_template is not None:
            self.body_template = body_template
            self.body_template_obj = Template(body_template)
        if self.empty_body:
            del self.content_type
            del self.content_length

    def __str__(self):
        return self.detail or self.explanation

    def _make_body(self, environ, escape):
        args = {
            'explanation': escape(self.explanation),
            'detail': escape(self.detail or ''),
            'comment': escape(self.comment or ''),
            }
        if self.comment:
            args['html_comment'] = '<!-- %s -->' % escape(self.comment)
        else:
            args['html_comment'] = ''
        if WSGIHTTPException.body_template_obj is not self.body_template_obj:
            # Custom template; add headers to args
            for k, v in environ.items():
                args[k] = escape(v)
            for k, v in self.headers.items():
                args[k.lower()] = escape(v)
        t_obj = self.body_template_obj
        return t_obj.substitute(args)

    def plain_body(self, environ):
        body = self._make_body(environ, no_escape)
        body = strip_tags(body)
        return self.plain_template_obj.substitute(status=self.status,
                                                  title=self.title,
                                                  body=body)

    def html_body(self, environ):
        body = self._make_body(environ, html_escape)
        return self.html_template_obj.substitute(status=self.status,
                                                 body=body)

    def generate_response(self, environ, start_response):
        if self.content_length is not None:
            del self.content_length
        headerlist = list(self.headerlist)
        accept = environ.get('HTTP_ACCEPT', '')
        if accept and 'html' in accept or '*/*' in accept:
            content_type = 'text/html'
            body = self.html_body(environ)
        else:
            content_type = 'text/plain'
            body = self.plain_body(environ)
        extra_kw = {}
        if isinstance(body, text_type):
            extra_kw.update(charset='utf-8')
        resp = Response(body,
            status=self.status,
            headerlist=headerlist,
            content_type=content_type,
            **extra_kw
        )
        resp.content_type = content_type
        return resp(environ, start_response)

    def __call__(self, environ, start_response):
        is_head = environ['REQUEST_METHOD'] == 'HEAD'
        if self.body or self.empty_body or is_head:
            app_iter = Response.__call__(self, environ, start_response)
        else:
            app_iter = self.generate_response(environ, start_response)
        if is_head:
            app_iter = []
        return app_iter

    @property
    def wsgi_response(self):
        return self



class HTTPError(WSGIHTTPException):
    """
    base class for status codes in the 400's and 500's

    This is an exception which indicates that an error has occurred,
    and that any work in progress should not be committed.  These are
    typically results in the 400's and 500's.
    """

class HTTPRedirection(WSGIHTTPException):
    """
    base class for 300's status code (redirections)

    This is an abstract base class for 3xx redirection.  It indicates
    that further action needs to be taken by the user agent in order
    to fulfill the request.  It does not necessarly signal an error
    condition.
    """

class HTTPOk(WSGIHTTPException):
    """
    Base class for the 200's status code (successful responses)

    code: 200, title: OK
    """
    code = 200
    title = 'OK'

############################################################
## 2xx success
############################################################

class HTTPCreated(HTTPOk):
    """
    subclass of :class:`~HTTPOk`

    This indicates that request has been fulfilled and resulted in a new
    resource being created.

    code: 201, title: Created
    """
    code = 201
    title = 'Created'

class HTTPAccepted(HTTPOk):
    """
    subclass of :class:`~HTTPOk`

    This indicates that the request has been accepted for processing, but the
    processing has not been completed.

    code: 202, title: Accepted
    """
    code = 202
    title = 'Accepted'
    explanation = 'The request is accepted for processing.'

class HTTPNonAuthoritativeInformation(HTTPOk):
    """
    subclass of :class:`~HTTPOk`

    This indicates that the returned metainformation in the entity-header is
    not the definitive set as available from the origin server, but is
    gathered from a local or a third-party copy.

    code: 203, title: Non-Authoritative Information
    """
    code = 203
    title = 'Non-Authoritative Information'

class HTTPNoContent(HTTPOk):
    """
    subclass of :class:`~HTTPOk`

    This indicates that the server has fulfilled the request but does
    not need to return an entity-body, and might want to return updated
    metainformation.

    code: 204, title: No Content
    """
    code = 204
    title = 'No Content'
    empty_body = True

class HTTPResetContent(HTTPOk):
    """
    subclass of :class:`~HTTPOk`

    This indicates that the the server has fulfilled the request and
    the user agent SHOULD reset the document view which caused the
    request to be sent.

    code: 205, title: Reset Content
    """
    code = 205
    title = 'Reset Content'
    empty_body = True

class HTTPPartialContent(HTTPOk):
    """
    subclass of :class:`~HTTPOk`

    This indicates that the server has fulfilled the partial GET
    request for the resource.

    code: 206, title: Partial Content
    """
    code = 206
    title = 'Partial Content'

############################################################
## 3xx redirection
############################################################

class _HTTPMove(HTTPRedirection):
    """
    redirections which require a Location field

    Since a 'Location' header is a required attribute of 301, 302, 303,
    305 and 307 (but not 304), this base class provides the mechanics to
    make this easy.

    You can provide a location keyword argument to set the location
    immediately.  You may also give ``add_slash=True`` if you want to
    redirect to the same URL as the request, except with a ``/`` added
    to the end.

    Relative URLs in the location will be resolved to absolute.
    """
    explanation = 'The resource has been moved to'
    body_template_obj = Template('''\
${explanation} <a href="${location}">${location}</a>;
you should be redirected automatically.
${detail}
${html_comment}''')

    def __init__(self, detail=None, headers=None, comment=None,
                 body_template=None, location=None, add_slash=False):
        super(_HTTPMove, self).__init__(
            detail=detail, headers=headers, comment=comment,
            body_template=body_template)
        if location is not None:
            self.location = location
            if add_slash:
                raise TypeError(
                    "You can only provide one of the arguments location "
                    "and add_slash")
        self.add_slash = add_slash

    def __call__(self, environ, start_response):
        req = Request(environ)
        if self.add_slash:
            url = req.path_url
            url += '/'
            if req.environ.get('QUERY_STRING'):
                url += '?' + req.environ['QUERY_STRING']
            self.location = url
        self.location = urlparse.urljoin(req.path_url, self.location)
        return super(_HTTPMove, self).__call__(
            environ, start_response)

class HTTPMultipleChoices(_HTTPMove):
    """
    subclass of :class:`~_HTTPMove`

    This indicates that the requested resource corresponds to any one
    of a set of representations, each with its own specific location,
    and agent-driven negotiation information is being provided so that
    the user can select a preferred representation and redirect its
    request to that location.

    code: 300, title: Multiple Choices
    """
    code = 300
    title = 'Multiple Choices'

class HTTPMovedPermanently(_HTTPMove):
    """
    subclass of :class:`~_HTTPMove`

    This indicates that the requested resource has been assigned a new
    permanent URI and any future references to this resource SHOULD use
    one of the returned URIs.

    code: 301, title: Moved Permanently
    """
    code = 301
    title = 'Moved Permanently'

class HTTPFound(_HTTPMove):
    """
    subclass of :class:`~_HTTPMove`

    This indicates that the requested resource resides temporarily under
    a different URI.

    code: 302, title: Found
    """
    code = 302
    title = 'Found'
    explanation = 'The resource was found at'

# This one is safe after a POST (the redirected location will be
# retrieved with GET):
class HTTPSeeOther(_HTTPMove):
    """
    subclass of :class:`~_HTTPMove`

    This indicates that the response to the request can be found under
    a different URI and SHOULD be retrieved using a GET method on that
    resource.

    code: 303, title: See Other
    """
    code = 303
    title = 'See Other'

class HTTPNotModified(HTTPRedirection):
    """
    subclass of :class:`~HTTPRedirection`

    This indicates that if the client has performed a conditional GET
    request and access is allowed, but the document has not been
    modified, the server SHOULD respond with this status code.

    code: 304, title: Not Modified
    """
    # TODO: this should include a date or etag header
    code = 304
    title = 'Not Modified'
    empty_body = True

class HTTPUseProxy(_HTTPMove):
    """
    subclass of :class:`~_HTTPMove`

    This indicates that the requested resource MUST be accessed through
    the proxy given by the Location field.

    code: 305, title: Use Proxy
    """
    # Not a move, but looks a little like one
    code = 305
    title = 'Use Proxy'
    explanation = (
        'The resource must be accessed through a proxy located at')

class HTTPTemporaryRedirect(_HTTPMove):
    """
    subclass of :class:`~_HTTPMove`

    This indicates that the requested resource resides temporarily
    under a different URI.

    code: 307, title: Temporary Redirect
    """
    code = 307
    title = 'Temporary Redirect'

############################################################
## 4xx client error
############################################################

class HTTPClientError(HTTPError):
    """
    base class for the 400's, where the client is in error

    This is an error condition in which the client is presumed to be
    in-error.  This is an expected problem, and thus is not considered
    a bug.  A server-side traceback is not warranted.  Unless specialized,
    this is a '400 Bad Request'
    """
    code = 400
    title = 'Bad Request'
    explanation = ('The server could not comply with the request since\r\n'
                   'it is either malformed or otherwise incorrect.\r\n')

class HTTPBadRequest(HTTPClientError):
    pass

class HTTPUnauthorized(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the request requires user authentication.

    code: 401, title: Unauthorized
    """
    code = 401
    title = 'Unauthorized'
    explanation = (
        'This server could not verify that you are authorized to\r\n'
        'access the document you requested.  Either you supplied the\r\n'
        'wrong credentials (e.g., bad password), or your browser\r\n'
        'does not understand how to supply the credentials required.\r\n')

class HTTPPaymentRequired(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    code: 402, title: Payment Required
    """
    code = 402
    title = 'Payment Required'
    explanation = ('Access was denied for financial reasons.')

class HTTPForbidden(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the server understood the request, but is
    refusing to fulfill it.

    code: 403, title: Forbidden
    """
    code = 403
    title = 'Forbidden'
    explanation = ('Access was denied to this resource.')

class HTTPNotFound(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the server did not find anything matching the
    Request-URI.

    code: 404, title: Not Found
    """
    code = 404
    title = 'Not Found'
    explanation = ('The resource could not be found.')

class HTTPMethodNotAllowed(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the method specified in the Request-Line is
    not allowed for the resource identified by the Request-URI.

    code: 405, title: Method Not Allowed
    """
    code = 405
    title = 'Method Not Allowed'
    # override template since we need an environment variable
    body_template_obj = Template('''\
The method ${REQUEST_METHOD} is not allowed for this resource. <br /><br />
${detail}''')

class HTTPNotAcceptable(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates the resource identified by the request is only
    capable of generating response entities which have content
    characteristics not acceptable according to the accept headers
    sent in the request.

    code: 406, title: Not Acceptable
    """
    code = 406
    title = 'Not Acceptable'
    # override template since we need an environment variable
    template = Template('''\
The resource could not be generated that was acceptable to your browser
(content of type ${HTTP_ACCEPT}. <br /><br />
${detail}''')

class HTTPProxyAuthenticationRequired(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This is similar to 401, but indicates that the client must first
    authenticate itself with the proxy.

    code: 407, title: Proxy Authentication Required
    """
    code = 407
    title = 'Proxy Authentication Required'
    explanation = ('Authentication with a local proxy is needed.')

class HTTPRequestTimeout(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the client did not produce a request within
    the time that the server was prepared to wait.

    code: 408, title: Request Timeout
    """
    code = 408
    title = 'Request Timeout'
    explanation = ('The server has waited too long for the request to '
                   'be sent by the client.')

class HTTPConflict(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the request could not be completed due to a
    conflict with the current state of the resource.

    code: 409, title: Conflict
    """
    code = 409
    title = 'Conflict'
    explanation = ('There was a conflict when trying to complete '
                   'your request.')

class HTTPGone(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the requested resource is no longer available
    at the server and no forwarding address is known.

    code: 410, title: Gone
    """
    code = 410
    title = 'Gone'
    explanation = ('This resource is no longer available.  No forwarding '
                   'address is given.')

class HTTPLengthRequired(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the the server refuses to accept the request
    without a defined Content-Length.

    code: 411, title: Length Required
    """
    code = 411
    title = 'Length Required'
    explanation = ('Content-Length header required.')

class HTTPPreconditionFailed(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the precondition given in one or more of the
    request-header fields evaluated to false when it was tested on the
    server.

    code: 412, title: Precondition Failed
    """
    code = 412
    title = 'Precondition Failed'
    explanation = ('Request precondition failed.')

class HTTPRequestEntityTooLarge(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the server is refusing to process a request
    because the request entity is larger than the server is willing or
    able to process.

    code: 413, title: Request Entity Too Large
    """
    code = 413
    title = 'Request Entity Too Large'
    explanation = ('The body of your request was too large for this server.')

class HTTPRequestURITooLong(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the server is refusing to service the request
    because the Request-URI is longer than the server is willing to
    interpret.

    code: 414, title: Request-URI Too Long
    """
    code = 414
    title = 'Request-URI Too Long'
    explanation = ('The request URI was too long for this server.')

class HTTPUnsupportedMediaType(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the server is refusing to service the request
    because the entity of the request is in a format not supported by
    the requested resource for the requested method.

    code: 415, title: Unsupported Media Type
    """
    code = 415
    title = 'Unsupported Media Type'
    # override template since we need an environment variable
    template_obj = Template('''\
The request media type ${CONTENT_TYPE} is not supported by this server.
<br /><br />
${detail}''')

class HTTPRequestRangeNotSatisfiable(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    The server SHOULD return a response with this status code if a
    request included a Range request-header field, and none of the
    range-specifier values in this field overlap the current extent
    of the selected resource, and the request did not include an
    If-Range request-header field.

    code: 416, title: Request Range Not Satisfiable
    """
    code = 416
    title = 'Request Range Not Satisfiable'
    explanation = ('The Range requested is not available.')

class HTTPExpectationFailed(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indidcates that the expectation given in an Expect
    request-header field could not be met by this server.

    code: 417, title: Expectation Failed
    """
    code = 417
    title = 'Expectation Failed'
    explanation = ('Expectation failed.')

class HTTPUnprocessableEntity(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the server is unable to process the contained
    instructions. Only for WebDAV.

    code: 422, title: Unprocessable Entity
    """
    ## Note: from WebDAV
    code = 422
    title = 'Unprocessable Entity'
    explanation = 'Unable to process the contained instructions'

class HTTPLocked(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the resource is locked. Only for WebDAV

    code: 423, title: Locked
    """
    ## Note: from WebDAV
    code = 423
    title = 'Locked'
    explanation = ('The resource is locked')

class HTTPFailedDependency(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the method could not be performed because the
    requested action depended on another action and that action failed.
    Only for WebDAV.

    code: 424, title: Failed Dependency
    """
    ## Note: from WebDAV
    code = 424
    title = 'Failed Dependency'
    explanation = (
        'The method could not be performed because the requested '
        'action dependended on another action and that action failed')

class HTTPPreconditionRequired(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the origin server requires the request to be
    conditional.  From RFC 6585, "Additional HTTP Status Codes".

    code: 428, title: Precondition Required
    """
    code = 428
    title = 'Precondition Required'
    explanation = ('This request is required to be conditional')

class HTTPTooManyRequests(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the client has sent too many requests in a
    given amount of time.  Useful for rate limiting.

    From RFC 6585, "Additional HTTP Status Codes".

    code: 429, title: Too Many Requests
    """
    code = 429
    title = 'Too Many Requests'
    explanation = (
        'The client has sent too many requests in a given amount of time')

class HTTPRequestHeaderFieldsTooLarge(HTTPClientError):
    """
    subclass of :class:`~HTTPClientError`

    This indicates that the server is unwilling to process the request
    because its header fields are too large. The request may be resubmitted
    after reducing the size of the request header fields.

    From RFC 6585, "Additional HTTP Status Codes".

    code: 431, title: Request Header Fields Too Large
    """
    code = 431
    title = 'Request Header Fields Too Large'
    explanation = (
        'The request header fields were too large')

############################################################
## 5xx Server Error
############################################################
#  Response status codes beginning with the digit "5" indicate cases in
#  which the server is aware that it has erred or is incapable of
#  performing the request. Except when responding to a HEAD request, the
#  server SHOULD include an entity containing an explanation of the error
#  situation, and whether it is a temporary or permanent condition. User
#  agents SHOULD display any included entity to the user. These response
#  codes are applicable to any request method.

class HTTPServerError(HTTPError):
    """
    base class for the 500's, where the server is in-error

    This is an error condition in which the server is presumed to be
    in-error.  This is usually unexpected, and thus requires a traceback;
    ideally, opening a support ticket for the customer. Unless specialized,
    this is a '500 Internal Server Error'
    """
    code = 500
    title = 'Internal Server Error'
    explanation = (
      'The server has either erred or is incapable of performing\r\n'
      'the requested operation.\r\n')

class HTTPInternalServerError(HTTPServerError):
    pass

class HTTPNotImplemented(HTTPServerError):
    """
    subclass of :class:`~HTTPServerError`

    This indicates that the server does not support the functionality
    required to fulfill the request.

    code: 501, title: Not Implemented
    """
    code = 501
    title = 'Not Implemented'
    template = Template('''
The request method ${REQUEST_METHOD} is not implemented for this server. <br /><br />
${detail}''')

class HTTPBadGateway(HTTPServerError):
    """
    subclass of :class:`~HTTPServerError`

    This indicates that the server, while acting as a gateway or proxy,
    received an invalid response from the upstream server it accessed
    in attempting to fulfill the request.

    code: 502, title: Bad Gateway
    """
    code = 502
    title = 'Bad Gateway'
    explanation = ('Bad gateway.')

class HTTPServiceUnavailable(HTTPServerError):
    """
    subclass of :class:`~HTTPServerError`

    This indicates that the server is currently unable to handle the
    request due to a temporary overloading or maintenance of the server.

    code: 503, title: Service Unavailable
    """
    code = 503
    title = 'Service Unavailable'
    explanation = ('The server is currently unavailable. '
                   'Please try again at a later time.')

class HTTPGatewayTimeout(HTTPServerError):
    """
    subclass of :class:`~HTTPServerError`

    This indicates that the server, while acting as a gateway or proxy,
    did not receive a timely response from the upstream server specified
    by the URI (e.g. HTTP, FTP, LDAP) or some other auxiliary server
    (e.g. DNS) it needed to access in attempting to complete the request.

    code: 504, title: Gateway Timeout
    """
    code = 504
    title = 'Gateway Timeout'
    explanation = ('The gateway has timed out.')

class HTTPVersionNotSupported(HTTPServerError):
    """
    subclass of :class:`~HTTPServerError`

    This indicates that the server does not support, or refuses to
    support, the HTTP protocol version that was used in the request
    message.

    code: 505, title: HTTP Version Not Supported
    """
    code = 505
    title = 'HTTP Version Not Supported'
    explanation = ('The HTTP version is not supported.')

class HTTPInsufficientStorage(HTTPServerError):
    """
    subclass of :class:`~HTTPServerError`

    This indicates that the server does not have enough space to save
    the resource.

    code: 507, title: Insufficient Storage
    """
    code = 507
    title = 'Insufficient Storage'
    explanation = ('There was not enough space to save the resource')

class HTTPNetworkAuthenticationRequired(HTTPServerError):
    """
    subclass of :class:`~HTTPServerError`

    This indicates that the client needs to authenticate to gain
    network access.  From RFC 6585, "Additional HTTP Status Codes".

    code: 511, title: Network Authentication Required
    """
    code = 511
    title = 'Network Authentication Required'
    explanation = ('Network authentication is required')

class HTTPExceptionMiddleware(object):
    """
    Middleware that catches exceptions in the sub-application.  This
    does not catch exceptions in the app_iter; only during the initial
    calling of the application.

    This should be put *very close* to applications that might raise
    these exceptions.  This should not be applied globally; letting
    *expected* exceptions raise through the WSGI stack is dangerous.
    """

    def __init__(self, application):
        self.application = application
    def __call__(self, environ, start_response):
        try:
            return self.application(environ, start_response)
        except HTTPException:
            parent_exc_info = sys.exc_info()
            def repl_start_response(status, headers, exc_info=None):
                if exc_info is None:
                    exc_info = parent_exc_info
                return start_response(status, headers, exc_info)
            return parent_exc_info[1](environ, repl_start_response)

try:
    from paste import httpexceptions
except ImportError:   # pragma: no cover
    # Without Paste we don't need to do this fixup
    pass
else: # pragma: no cover
    for name in dir(httpexceptions):
        obj = globals().get(name)
        if (obj and isinstance(obj, type) and issubclass(obj, HTTPException)
            and obj is not HTTPException
            and obj is not WSGIHTTPException):
            obj.__bases__ = obj.__bases__ + (getattr(httpexceptions, name),)
    del name, obj, httpexceptions

__all__ = ['HTTPExceptionMiddleware', 'status_map']
status_map={}
for name, value in list(globals().items()):
    if (isinstance(value, (type, class_types)) and
        issubclass(value, HTTPException)
        and not name.startswith('_')):
        __all__.append(name)
        if getattr(value, 'code', None):
            status_map[value.code]=value
        if hasattr(value, 'explanation'):
            value.explanation = ' '.join(value.explanation.strip().split())
del name, value
