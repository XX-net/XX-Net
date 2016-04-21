# Copyright (C) 2010-2011 gevent contributors. See LICENSE for details.

# Get the standard Python httplib as __httplib__, ensuring we get a version
# that hasn't already been modified by monkey patching of any of its members.
# HTTPSConnection must use the standard HTTPConnection because libevent-http
# does not currently support https.
import imp
__httplib__ = imp.load_module('__httplib__', *imp.find_module('httplib'))

from gevent import core
from gevent.hub import Waiter

__implements__ = [
    'HTTPConnection',
    'HTTPResponse',
]

__imports__ = [
    'HTTPSConnection',
    'HTTPException',
    'InvalidURL',
]

__all__ = __implements__ + __imports__

InvalidURL = __httplib__.InvalidURL
HTTP_PORT = __httplib__.HTTP_PORT
HTTPException = __httplib__.HTTPException
HTTPSConnection = __httplib__.HTTPSConnection

EV_METHOD_TYPES = dict((name, id) for (id, name) in core.HTTP_method2name.items())


class RequestFailed(HTTPException):
    pass


class HTTPMessage(object):

    def __init__(self, headers):
        self._headers = headers
        self.dict = dict(headers)

    def getheaders(self, name):
        name = name.lower()
        result = []
        for key, value in self._headers:
            if key == name:
                result.append(value)
        return result

    # emulation of rfc822.Message (base class of httplib.HTTPMessage)
    @property
    def headers(self):
        return [': '.join(item) for item in self._headers]

    # Access as a dictionary (only finds *last* header of each type):

    def __len__(self):
        """Get the number of headers in a message."""
        return len(self.dict)

    def __getitem__(self, name):
        """Get a specific header, as from a dictionary."""
        return self.dict[name.lower()]

    def get(self, name, default=None):
        name = name.lower()
        try:
            return self.dict[name]
        except KeyError:
            return default

    def has_key(self, name):
        """Determine whether a message contains the named header."""
        return name.lower() in self.dict

    def __contains__(self, name):
        """Determine whether a message contains the named header."""
        return name.lower() in self.dict

    def __iter__(self):
        return iter(self.dict)

    def keys(self):
        """Get all of a message's header field names."""
        return self.dict.keys()

    def values(self):
        """Get all of a message's header field values."""
        return self.dict.values()

    def items(self):
        return self.dict.items()

    def __str__(self):
        return ''.join(self.headers)


class HTTPResponse(object):

    def __init__(self, request, debuglevel=0):
        self._request = request
        self.debuglevel = debuglevel
        self.version = request.major * 10 + request.minor
        assert self.version, request
        self.status = request.response_code
        assert self.status, request
        self.reason = request.response_code_line
        self.headers = request.get_input_headers()
        self.msg = HTTPMessage(self.headers)

        if self.debuglevel > 0:
            for (k, v) in self.getheaders():
                print 'header:', k, v

    def read(self, amt=-1):
        return self._request.input_buffer.read(amt)

    def getheader(self, name, default=None):
        return self.msg.get(name, default)

    def getheaders(self):
        return self.msg.items()

    def close(self):
        self._request = None


class HTTPConnection(object):
    response_class = HTTPResponse
    default_port = HTTP_PORT
    debuglevel = 0

    def __init__(self, host, port=None, timeout=None):
        self.timeout = timeout
        self._set_hostport(host, port)
        self.conn = None
        self.resp = None
        self._waiter = None

    def _set_hostport(self, host, port):
        if port is None:
            i = host.rfind(':')
            j = host.rfind(']')         # ipv6 addresses have [...]
            if i > j:
                try:
                    port = int(host[i+1:])
                except ValueError:
                    raise InvalidURL("nonnumeric port: '%s'" % host[i+1:])
                host = host[:i]
            else:
                port = self.default_port
            if host and host[0] == '[' and host[-1] == ']':
                host = host[1:-1]
        self.host = host
        self.port = port

    def set_debuglevel(self, level):
        self.debuglevel = level

    def request(self, method, uri, body=None, headers=None):
        headers = headers or {}

        self.resp = None
        self.putrequest(method, uri)

        for (k, v) in headers.iteritems():
            self.putheader(k, v)

        self.endheaders()

        if hasattr(body, 'read'):
            while True:
                d = body.read(4096)
                if not d: break
                self.send(d)
        elif body:
            self.send(body)

        self.getresponse()

    def getresponse(self):
        if self.resp is None:
            self.conn.make_request(self.req, self.method, self.uri)
            assert self._waiter is None, self._waiter
            self._waiter = Waiter()
            try:
                self.resp = self._waiter.get()
            finally:
                self._waiter = None

        return self.resp

    def _callback(self, request):
        waiter = self._waiter
        self._waiter = None
        if waiter is not None:
            if request.response_code:
                waiter.switch(self.response_class(request, debuglevel=self.debuglevel))
            else:
                # this seems to be evhttp bug
                waiter.throw(RequestFailed)

    def connect(self):
        if self.conn: return

        if self.debuglevel > 0:
            print 'connect: (%s, %u)' % (self.host, self.port)

        self.conn = core.http_connection.new(self.host, self.port)

        if self.timeout is not None:
            self.conn.set_timeout(int(min(1, self.timeout)))

    def close(self):
        self.resp = None
        self.conn = None

    def putrequest(self, request, selector, skip_host=None, skip_accept_encoding=None):
        self.connect()
        self.req = core.http_request_client(self._callback)

        if not skip_host:
            if self.port == HTTP_PORT:
                self.putheader('Host', self.host)
            else:
                self.putheader('Host', '%s:%u' % (self.host, self.port))

        if not skip_accept_encoding:
            self.putheader('Accept-Encoding', 'identity')

        self.method = EV_METHOD_TYPES[request]
        self.uri = selector or '/'

    def putheader(self, header, *args):
        self.req.add_output_header(header, '\r\n\t'.join(args))

    def endheaders(self):
        pass

    def send(self, data):
        if self.debuglevel > 0:
            print 'send:', repr(data)

        self.req.output_buffer.write(data)
