import errno
import sys
import re
try:
    import httplib
except ImportError: # pragma: no cover
    import http.client as httplib
from webob.compat import url_quote
import socket
from webob import exc
from webob.compat import PY3


__all__ = ['send_request_app', 'SendRequest']

class SendRequest:
    """
    Sends the request, as described by the environ, over actual HTTP.
    All controls about how it is sent are contained in the request
    environ itself.

    This connects to the server given in SERVER_NAME:SERVER_PORT, and
    sends the Host header in HTTP_HOST -- they do not have to match.
    You can send requests to servers despite what DNS says.

    Set ``environ['webob.client.timeout'] = 10`` to set the timeout on
    the request (to, for example, 10 seconds).

    Does not add X-Forwarded-For or other standard headers

    If you use ``send_request_app`` then simple ``httplib``
    connections will be used.
    """

    def __init__(self, HTTPConnection=httplib.HTTPConnection,
                 HTTPSConnection=httplib.HTTPSConnection):
        self.HTTPConnection = HTTPConnection
        self.HTTPSConnection = HTTPSConnection

    def __call__(self, environ, start_response):
        scheme = environ['wsgi.url_scheme']
        if scheme == 'http':
            ConnClass = self.HTTPConnection
        elif scheme == 'https':
            ConnClass = self.HTTPSConnection
        else:
            raise ValueError(
                "Unknown scheme: %r" % scheme)
        if 'SERVER_NAME' not in environ:
            host = environ.get('HTTP_HOST')
            if not host:
                raise ValueError(
                    "environ contains neither SERVER_NAME nor HTTP_HOST")
            if ':' in host:
                host, port = host.split(':', 1)
            else:
                if scheme == 'http':
                    port = '80'
                else:
                    port = '443'
            environ['SERVER_NAME'] = host
            environ['SERVER_PORT'] = port
        kw = {}
        if ('webob.client.timeout' in environ and
            self._timeout_supported(ConnClass) ):
            kw['timeout'] = environ['webob.client.timeout']
        conn = ConnClass('%(SERVER_NAME)s:%(SERVER_PORT)s' % environ, **kw)
        headers = {}
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                key = key[5:].replace('_', '-').title()
                headers[key] = value
        path = (url_quote(environ.get('SCRIPT_NAME', ''))
                + url_quote(environ.get('PATH_INFO', '')))
        if environ.get('QUERY_STRING'):
            path += '?' + environ['QUERY_STRING']
        try:
            content_length = int(environ.get('CONTENT_LENGTH', '0'))
        except ValueError:
            content_length = 0
        ## FIXME: there is no streaming of the body, and that might be useful
        ## in some cases
        if content_length:
            body = environ['wsgi.input'].read(content_length)
        else:
            body = ''
        headers['Content-Length'] = content_length
        if environ.get('CONTENT_TYPE'):
            headers['Content-Type'] = environ['CONTENT_TYPE']
        if not path.startswith("/"):
            path = "/" + path
        try:
            conn.request(environ['REQUEST_METHOD'],
                         path, body, headers)
            res = conn.getresponse()
        except socket.timeout:
            resp = exc.HTTPGatewayTimeout()
            return resp(environ, start_response)
        except (socket.error, socket.gaierror) as e:
            if ((isinstance(e, socket.error) and e.args[0] == -2) or
                (isinstance(e, socket.gaierror) and e.args[0] == 8)):
                # Name or service not known
                resp = exc.HTTPBadGateway(
                    "Name or service not known (bad domain name: %s)"
                    % environ['SERVER_NAME'])
                return resp(environ, start_response)
            elif e.args[0] in _e_refused: # pragma: no cover
                # Connection refused
                resp = exc.HTTPBadGateway("Connection refused")
                return resp(environ, start_response)
            raise
        headers_out = self.parse_headers(res.msg)
        status = '%s %s' % (res.status, res.reason)
        start_response(status, headers_out)
        length = res.getheader('content-length')
        # FIXME: This shouldn't really read in all the content at once
        if length is not None:
            body = res.read(int(length))
        else:
            body = res.read()
        conn.close()
        return [body]

    # Remove these headers from response (specify lower case header
    # names):
    filtered_headers = (
        'transfer-encoding',
    )

    MULTILINE_RE = re.compile(r'\r?\n\s*')

    def parse_headers(self, message):
        """
        Turn a Message object into a list of WSGI-style headers.
        """
        headers_out = []
        if PY3:  # pragma: no cover
            headers = message._headers
        else:  # pragma: no cover
            headers = message.headers
        for full_header in headers:
            if not full_header: # pragma: no cover
                # Shouldn't happen, but we'll just ignore
                continue
            if full_header[0].isspace():  # pragma: no cover
                # Continuation line, add to the last header
                if not headers_out:
                    raise ValueError(
                        "First header starts with a space (%r)" % full_header)
                last_header, last_value = headers_out.pop()
                value = last_value + ', ' + full_header.strip()
                headers_out.append((last_header, value))
                continue
            if isinstance(full_header, tuple):  # pragma: no cover
                header, value = full_header
            else:  # pragma: no cover
                try:
                    header, value = full_header.split(':', 1)
                except:
                    raise ValueError("Invalid header: %r" % (full_header,))
            value = value.strip()
            if '\n' in value or '\r\n' in value:  # pragma: no cover
                # Python 3 has multiline values for continuations, Python 2
                # has two items in headers
                value = self.MULTILINE_RE.sub(', ', value)
            if header.lower() not in self.filtered_headers:
                headers_out.append((header, value))
        return headers_out

    def _timeout_supported(self, ConnClass):
        if sys.version_info < (2, 7) and ConnClass in (
            httplib.HTTPConnection, httplib.HTTPSConnection): # pragma: no cover
            return False
        return True


send_request_app = SendRequest()

_e_refused = (errno.ECONNREFUSED,)
if hasattr(errno, 'ENODATA'): # pragma: no cover
    _e_refused += (errno.ENODATA,)
