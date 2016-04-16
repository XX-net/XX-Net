# Copyright (c) 2005-2006, Bob Ippolito
# Copyright (c) 2007, Linden Research, Inc.
# Copyright (c) 2009-2010 Denis Bilenko
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Cooperative socket module.

This module provides socket operations and some related functions.
The API of the functions and classes matches the API of the corresponding
items in standard :mod:`socket` module exactly, but the synchronous functions
in this module only block the current greenlet and let the others run.

For convenience, exceptions (like :class:`error <socket.error>` and :class:`timeout <socket.timeout>`)
as well as the constants from :mod:`socket` module are imported into this module.
"""

# standard functions and classes that this module re-implements in a gevent-aware way:
__implements__ = ['create_connection',
                  'getaddrinfo',
                  'gethostbyname',
                  'socket',
                  'SocketType',
                  'fromfd',
                  'socketpair']

# non-standard functions that this module provides:
__extensions__ = ['wait_read',
                  'wait_write',
                  'wait_readwrite']

# standard functions and classes that this module re-imports
__imports__ = ['error',
               'gaierror',
               'getfqdn',
               'herror',
               'htonl',
               'htons',
               'ntohl',
               'ntohs',
               'inet_aton',
               'inet_ntoa',
               'inet_pton',
               'inet_ntop',
               'timeout',
               'gethostname',
               'getprotobyname',
               'getservbyname',
               'getservbyport',
               'getdefaulttimeout',
               'setdefaulttimeout',
               # Python 2.5 and older:
               'RAND_add',
               'RAND_egd',
               'RAND_status',
               # Windows:
               'errorTab']


import sys
import time
import random
import re

is_windows = sys.platform == 'win32'

if is_windows:
    # no such thing as WSAEPERM or error code 10001 according to winsock.h or MSDN
    from errno import WSAEINVAL as EINVAL
    from errno import WSAEWOULDBLOCK as EWOULDBLOCK
    from errno import WSAEINPROGRESS as EINPROGRESS
    from errno import WSAEALREADY as EALREADY
    from errno import WSAEISCONN as EISCONN
    from gevent.win32util import formatError as strerror
    EAGAIN = EWOULDBLOCK
else:
    from errno import EINVAL
    from errno import EWOULDBLOCK
    from errno import EINPROGRESS
    from errno import EALREADY
    from errno import EAGAIN
    from errno import EISCONN
    from os import strerror

try:
    from errno import EBADF
except ImportError:
    EBADF = 9

import _socket
_realsocket = _socket.socket
__socket__ = __import__('socket')
_fileobject = __socket__._fileobject

for name in __imports__[:]:
    try:
        value = getattr(__socket__, name)
        globals()[name] = value
    except AttributeError:
        __imports__.remove(name)

for name in __socket__.__all__:
    value = getattr(__socket__, name)
    if isinstance(value, (int, long, basestring)):
        globals()[name] = value
        __imports__.append(name)

del name, value

if 'inet_ntop' not in globals():
    # inet_ntop is required by our implementation of getaddrinfo

    def inet_ntop(address_family, packed_ip):
        if address_family == AF_INET:
            return inet_ntoa(packed_ip)
        # XXX: ipv6 won't work on windows
        raise NotImplementedError('inet_ntop() is not available on this platform')

# XXX: implement blocking functions that are not yet implemented

from gevent.hub import getcurrent, get_hub
from gevent import core
from gevent import spawn
from gevent.util import wrap_errors

_ip4_re = re.compile('^[\d\.]+$')


def _wait_helper(ev, evtype):
    current, timeout_exc = ev.arg
    if evtype & core.EV_TIMEOUT:
        current.throw(timeout_exc)
    else:
        current.switch(ev)


def wait_read(fileno, timeout=None, timeout_exc=timeout('timed out'), event=None):
    """Block the current greenlet until *fileno* is ready to read.

    If *timeout* is non-negative, then *timeout_exc* is raised after *timeout* second has passed.
    By default *timeout_exc* is ``socket.timeout('timed out')``.

    If :func:`cancel_wait` is called, raise ``socket.error(EBADF, 'File descriptor was closed in another greenlet')``.
    """
    if event is None:
        event = core.read_event(fileno, _wait_helper, timeout, (getcurrent(), timeout_exc))
    else:
        assert event.callback == _wait_helper, event.callback
        assert event.arg is None, 'This event is already used by another greenlet: %r' % (event.arg, )
        event.arg = (getcurrent(), timeout_exc)
        event.add(timeout)
    try:
        switch_result = get_hub().switch()
        assert event is switch_result, 'Invalid switch into wait_read(): %r' % (switch_result, )
    finally:
        event.cancel()
        event.arg = None


def wait_write(fileno, timeout=None, timeout_exc=timeout('timed out'), event=None):
    """Block the current greenlet until *fileno* is ready to write.

    If *timeout* is non-negative, then *timeout_exc* is raised after *timeout* second has passed.
    By default *timeout_exc* is ``socket.timeout('timed out')``.

    If :func:`cancel_wait` is called, raise ``socket.error(EBADF, 'File descriptor was closed in another greenlet')``.
    """
    if event is None:
        event = core.write_event(fileno, _wait_helper, timeout, (getcurrent(), timeout_exc))
    else:
        assert event.callback == _wait_helper, event.callback
        assert event.arg is None, 'This event is already used by another greenlet: %r' % (event.arg, )
        event.arg = (getcurrent(), timeout_exc)
        event.add(timeout)
    try:
        switch_result = get_hub().switch()
        assert event is switch_result, 'Invalid switch into wait_write(): %r' % (switch_result, )
    finally:
        event.arg = None
        event.cancel()


def wait_readwrite(fileno, timeout=None, timeout_exc=timeout('timed out'), event=None):
    """Block the current greenlet until *fileno* is ready to read or write.

    If *timeout* is non-negative, then *timeout_exc* is raised after *timeout* second has passed.
    By default *timeout_exc* is ``socket.timeout('timed out')``.

    If :func:`cancel_wait` is called, raise ``socket.error(EBADF, 'File descriptor was closed in another greenlet')``.
    """
    if event is None:
        event = core.readwrite_event(fileno, _wait_helper, timeout, (getcurrent(), timeout_exc))
    else:
        assert event.callback == _wait_helper, event.callback
        assert event.arg is None, 'This event is already used by another greenlet: %r' % (event.arg, )
        event.arg = (getcurrent(), timeout_exc)
        event.add(timeout)
    try:
        switch_result = get_hub().switch()
        assert event is switch_result, 'Invalid switch into wait_readwrite(): %r' % (switch_result, )
    finally:
        event.arg = None
        event.cancel()


def __cancel_wait(event):
    if event.pending:
        arg = event.arg
        if arg is not None:
            arg[0].throw(error(EBADF, 'File descriptor was closed in another greenlet'))


def cancel_wait(event):
    core.active_event(__cancel_wait, event)


if sys.version_info[:2] <= (2, 4):
    # implement close argument to _fileobject that we require

    realfileobject = _fileobject

    class _fileobject(realfileobject):

        __slots__ = realfileobject.__slots__ + ['_close']

        def __init__(self, *args, **kwargs):
            self._close = kwargs.pop('close', False)
            realfileobject.__init__(self, *args, **kwargs)

        def close(self):
            try:
                if self._sock:
                    self.flush()
            finally:
                if self._close:
                    self._sock.close()
                self._sock = None


if sys.version_info[:2] < (2, 7):
    _get_memory = buffer
else:

    def _get_memory(string, offset):
        return memoryview(string)[offset:]


class _closedsocket(object):
    __slots__ = []

    def _dummy(*args):
        raise error(EBADF, 'Bad file descriptor')
    # All _delegate_methods must also be initialized here.
    send = recv = recv_into = sendto = recvfrom = recvfrom_into = _dummy
    __getattr__ = _dummy


_delegate_methods = ("recv", "recvfrom", "recv_into", "recvfrom_into", "send", "sendto", 'sendall')

timeout_default = object()


class socket(object):

    def __init__(self, family=AF_INET, type=SOCK_STREAM, proto=0, _sock=None):
        if _sock is None:
            self._sock = _realsocket(family, type, proto)
            self.timeout = _socket.getdefaulttimeout()
        else:
            if hasattr(_sock, '_sock'):
                self._sock = _sock._sock
                self.timeout = getattr(_sock, 'timeout', False)
                if self.timeout is False:
                    self.timeout = _socket.getdefaulttimeout()
            else:
                self._sock = _sock
                self.timeout = _socket.getdefaulttimeout()
        self._sock.setblocking(0)
        self._read_event = core.event(core.EV_READ, self.fileno(), _wait_helper)
        self._write_event = core.event(core.EV_WRITE, self.fileno(), _wait_helper)
        # regarding the following, see issue #31
        # (http://code.google.com/p/gevent/issues/detail?id=31#c19)
        if is_windows:
            self._rw_event = core.event(core.EV_READ | core.EV_WRITE, self.fileno(), _wait_helper)
        else:
            self._rw_event = core.event(core.EV_WRITE, self.fileno(), _wait_helper)

    def __repr__(self):
        return '<%s at %s %s>' % (type(self).__name__, hex(id(self)), self._formatinfo())

    def __str__(self):
        return '<%s %s>' % (type(self).__name__, self._formatinfo())

    def _formatinfo(self):
        try:
            fileno = self.fileno()
        except Exception, ex:
            fileno = str(ex)
        try:
            sockname = self.getsockname()
            sockname = '%s:%s' % sockname
        except Exception:
            sockname = None
        try:
            peername = self.getpeername()
            peername = '%s:%s' % peername
        except Exception:
            peername = None
        result = 'fileno=%s' % fileno
        if sockname is not None:
            result += ' sock=' + str(sockname)
        if peername is not None:
            result += ' peer=' + str(peername)
        if getattr(self, 'timeout', None) is not None:
            result += ' timeout=' + str(self.timeout)
        return result

    def accept(self):
        sock = self._sock
        while True:
            try:
                client_socket, address = sock.accept()
                break
            except error, ex:
                if ex[0] != EWOULDBLOCK or self.timeout == 0.0:
                    raise
                sys.exc_clear()
            wait_read(sock.fileno(), timeout=self.timeout, event=self._read_event)
        return socket(_sock=client_socket), address

    def close(self):
        cancel_wait(self._rw_event)
        cancel_wait(self._read_event)
        cancel_wait(self._write_event)
        self._sock = _closedsocket()
        dummy = self._sock._dummy
        for method in _delegate_methods:
            setattr(self, method, dummy)

    def connect(self, address):
        if isinstance(address, tuple) and len(address) == 2:
            address = gethostbyname(address[0]), address[1]
        if self.timeout == 0.0:
            return self._sock.connect(address)
        sock = self._sock
        if self.timeout is None:
            while True:
                err = sock.getsockopt(SOL_SOCKET, SO_ERROR)
                if err:
                    raise error(err, strerror(err))
                result = sock.connect_ex(address)
                if not result or result == EISCONN:
                    break
                elif (result in (EWOULDBLOCK, EINPROGRESS, EALREADY)) or (result == EINVAL and is_windows):
                    wait_readwrite(sock.fileno(), event=self._rw_event)
                else:
                    raise error(result, strerror(result))
        else:
            end = time.time() + self.timeout
            while True:
                err = sock.getsockopt(SOL_SOCKET, SO_ERROR)
                if err:
                    raise error(err, strerror(err))
                result = sock.connect_ex(address)
                if not result or result == EISCONN:
                    break
                elif (result in (EWOULDBLOCK, EINPROGRESS, EALREADY)) or (result == EINVAL and is_windows):
                    timeleft = end - time.time()
                    if timeleft <= 0:
                        raise timeout('timed out')
                    wait_readwrite(sock.fileno(), timeout=timeleft, event=self._rw_event)
                else:
                    raise error(result, strerror(result))

    def connect_ex(self, address):
        try:
            return self.connect(address) or 0
        except timeout:
            return EAGAIN
        except error, ex:
            if type(ex) is error:
                return ex[0]
            else:
                raise  # gaierror is not silented by connect_ex

    def dup(self):
        """dup() -> socket object

        Return a new socket object connected to the same system resource.
        Note, that the new socket does not inherit the timeout."""
        return socket(_sock=self._sock)

    def makefile(self, mode='r', bufsize=-1):
        # note that this does not inherit timeout either (intentionally, because that's
        # how the standard socket behaves)
        return _fileobject(self.dup(), mode, bufsize)

    def recv(self, *args):
        sock = self._sock  # keeping the reference so that fd is not closed during waiting
        while True:
            try:
                return sock.recv(*args)
            except error, ex:
                if ex[0] == EBADF:
                    return ''
                if ex[0] != EWOULDBLOCK or self.timeout == 0.0:
                    raise
                # QQQ without clearing exc_info test__refcount.test_clean_exit fails
                sys.exc_clear()
            try:
                wait_read(sock.fileno(), timeout=self.timeout, event=self._read_event)
            except error, ex:
                if ex[0] == EBADF:
                    return ''
                raise

    def recvfrom(self, *args):
        sock = self._sock
        while True:
            try:
                return sock.recvfrom(*args)
            except error, ex:
                if ex[0] != EWOULDBLOCK or self.timeout == 0.0:
                    raise
                sys.exc_clear()
            wait_read(sock.fileno(), timeout=self.timeout, event=self._read_event)

    def recvfrom_into(self, *args):
        sock = self._sock
        while True:
            try:
                return sock.recvfrom_into(*args)
            except error, ex:
                if ex[0] != EWOULDBLOCK or self.timeout == 0.0:
                    raise
                sys.exc_clear()
            wait_read(sock.fileno(), timeout=self.timeout, event=self._read_event)

    def recv_into(self, *args):
        sock = self._sock
        while True:
            try:
                return sock.recv_into(*args)
            except error, ex:
                if ex[0] == EBADF:
                    return 0
                if ex[0] != EWOULDBLOCK or self.timeout == 0.0:
                    raise
                sys.exc_clear()
            try:
                wait_read(sock.fileno(), timeout=self.timeout, event=self._read_event)
            except error, ex:
                if ex[0] == EBADF:
                    return 0
                raise

    def send(self, data, flags=0, timeout=timeout_default):
        sock = self._sock
        if timeout is timeout_default:
            timeout = self.timeout
        try:
            return sock.send(data, flags)
        except error, ex:
            if ex[0] != EWOULDBLOCK or timeout == 0.0:
                raise
            sys.exc_clear()
            try:
                wait_write(sock.fileno(), timeout=timeout, event=self._write_event)
            except error, ex:
                if ex[0] == EBADF:
                    return 0
                raise
            try:
                return sock.send(data, flags)
            except error, ex2:
                if ex2[0] == EWOULDBLOCK:
                    return 0
                raise

    def sendall(self, data, flags=0):
        if isinstance(data, unicode):
            data = data.encode()
        # this sendall is also reused by SSL subclasses (both from ssl and sslold modules),
        # so it should not call self._sock methods directly
        if self.timeout is None:
            data_sent = 0
            while data_sent < len(data):
                data_sent += self.send(_get_memory(data, data_sent), flags)
        else:
            timeleft = self.timeout
            end = time.time() + timeleft
            data_sent = 0
            while True:
                data_sent += self.send(_get_memory(data, data_sent), flags, timeout=timeleft)
                if data_sent >= len(data):
                    break
                timeleft = end - time.time()
                if timeleft <= 0:
                    raise timeout('timed out')

    def sendto(self, *args):
        sock = self._sock
        try:
            return sock.sendto(*args)
        except error, ex:
            if ex[0] != EWOULDBLOCK or timeout == 0.0:
                raise
            sys.exc_clear()
            wait_write(sock.fileno(), timeout=self.timeout, event=self._write_event)
            try:
                return sock.sendto(*args)
            except error, ex2:
                if ex2[0] == EWOULDBLOCK:
                    return 0
                raise

    def setblocking(self, flag):
        if flag:
            self.timeout = None
        else:
            self.timeout = 0.0

    def settimeout(self, howlong):
        if howlong is not None:
            try:
                f = howlong.__float__
            except AttributeError:
                raise TypeError('a float is required')
            howlong = f()
            if howlong < 0.0:
                raise ValueError('Timeout value out of range')
        self.timeout = howlong

    def gettimeout(self):
        return self.timeout

    def shutdown(self, how):
        cancel_wait(self._rw_event)
        if how == 0:  # SHUT_RD
            cancel_wait(self._read_event)
        elif how == 1:  # SHUT_RW
            cancel_wait(self._write_event)
        else:
            cancel_wait(self._read_event)
            cancel_wait(self._write_event)
        self._sock.shutdown(how)

    family = property(lambda self: self._sock.family, doc="the socket family")
    type = property(lambda self: self._sock.type, doc="the socket type")
    proto = property(lambda self: self._sock.proto, doc="the socket protocol")

    # delegate the functions that we haven't implemented to the real socket object

    _s = ("def %s(self, *args): return self._sock.%s(*args)\n\n"
          "%s.__doc__ = _realsocket.%s.__doc__\n")
    for _m in set(__socket__._socketmethods) - set(locals()):
        exec _s % (_m, _m, _m, _m)
    del _m, _s

SocketType = socket

if hasattr(_socket, 'socketpair'):

    def socketpair(*args):
        one, two = _socket.socketpair(*args)
        return socket(_sock=one), socket(_sock=two)
else:
    __implements__.remove('socketpair')

if hasattr(_socket, 'fromfd'):

    def fromfd(*args):
        return socket(_sock=_socket.fromfd(*args))
else:
    __implements__.remove('fromfd')


def bind_and_listen(descriptor, address=('', 0), backlog=50, reuse_addr=True):
    if reuse_addr:
        try:
            descriptor.setsockopt(SOL_SOCKET, SO_REUSEADDR, descriptor.getsockopt(SOL_SOCKET, SO_REUSEADDR) | 1)
        except error:
            pass
    descriptor.bind(address)
    descriptor.listen(backlog)


def tcp_listener(address, backlog=50, reuse_addr=True):
    """A shortcut to create a TCP socket, bind it and put it into listening state."""
    sock = socket()
    bind_and_listen(sock, address, backlog=backlog, reuse_addr=reuse_addr)
    return sock


try:
    _GLOBAL_DEFAULT_TIMEOUT = __socket__._GLOBAL_DEFAULT_TIMEOUT
except AttributeError:
    _GLOBAL_DEFAULT_TIMEOUT = object()


def create_connection(address, timeout=_GLOBAL_DEFAULT_TIMEOUT, source_address=None):
    """Connect to *address* and return the socket object.

    Convenience function.  Connect to *address* (a 2-tuple ``(host,
    port)``) and return the socket object.  Passing the optional
    *timeout* parameter will set the timeout on the socket instance
    before attempting to connect.  If no *timeout* is supplied, the
    global default timeout setting returned by :func:`getdefaulttimeout`
    is used. If *source_address* is set it must be a tuple of (host, port)
    for the socket to bind as a source address before making the connection.
    An host of '' or port 0 tells the OS to use the default.
    """

    host, port = address
    err = None
    for res in getaddrinfo(host, port, 0, SOCK_STREAM):
        af, socktype, proto, _canonname, sa = res
        sock = None
        try:
            sock = socket(af, socktype, proto)
            if timeout is not _GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect(sa)
            return sock
        except error, ex:
            err = ex
            sys.exc_clear()
            if sock is not None:
                sock.close()
    if err is not None:
        raise err
    else:
        raise error("getaddrinfo returns an empty list")


try:
    from gevent.dns import resolve_ipv4, resolve_ipv6
except Exception:
    import traceback
    traceback.print_exc()
    __implements__.remove('gethostbyname')
    __implements__.remove('getaddrinfo')
else:

    def gethostbyname(hostname):
        """:func:`socket.gethostbyname` implemented using :mod:`gevent.dns`.

        Differs in the following ways:

        * raises :class:`DNSError` (a subclass of :class:`socket.gaierror`) with dns error
          codes instead of standard socket error codes
        * does not support ``/etc/hosts`` but calls the original :func:`socket.gethostbyname`
          if *hostname* has no dots
        * does not iterate through all addresses, instead picks a random one each time
        """
        # TODO: this is supposed to iterate through all the addresses
        # could use a global dict(hostname, iter)
        # - fix these nasty hacks for localhost, ips, etc.
        if not isinstance(hostname, str) or '.' not in hostname:
            return _socket.gethostbyname(hostname)
        if _ip4_re.match(hostname):
            return hostname
        if hostname == _socket.gethostname():
            return _socket.gethostbyname(hostname)
        addrs = None
        try:
            _ttl, addrs = resolve_ipv4(hostname)
        except:
            _ttl, addrs = resolve_ipv6(hostname)
            return inet_ntop(AF_INET6, random.choice(addrs))
        else:
            return inet_ntop(AF_INET, random.choice(addrs))

    def getaddrinfo(host, port, family=0, socktype=0, proto=0, flags=0, evdns_flags=0):
        """*Some* approximation of :func:`socket.getaddrinfo` implemented using :mod:`gevent.dns`.

        If *host* is not a string, does not has any dots or is a numeric IP address, then
        the standard :func:`socket.getaddrinfo` is called.

        Otherwise, calls :func:`resolve_ipv4` (for ``AF_INET``) or :func:`resolve_ipv6` (for ``AF_INET6``) or
        both (for ``AF_UNSPEC``) and formats the result the way :func:`socket.getaddrinfo` does it.

        Differs in the following ways:

        * raises :class:`DNSError` (a subclass of :class:`gaierror`) with libevent-dns error
          codes instead of standard socket error codes
        * *flags* argument is ignored
        * for IPv6, flow info and scope id are always 0

        Additionally, supports *evdns_flags* keyword arguments (default ``0``) that is passed
        to :mod:`dns` functions.
        """
        if isinstance(host, unicode):
            host = host.encode('idna')
        if not isinstance(host, str) or \
           '.' not in host or \
           _ip4_re.match(host) is not None or \
           family not in (AF_UNSPEC, AF_INET, AF_INET6):
            return _socket.getaddrinfo(host, port, family, socktype, proto, flags)

        if isinstance(port, basestring):
            try:
                if socktype == 0:
                    try:
                        port = getservbyname(port, 'tcp')
                        socktype = SOCK_STREAM
                    except socket.error:
                        port = getservbyname(port, 'udp')
                        socktype = SOCK_DGRAM
                elif socktype == SOCK_STREAM:
                    port = getservbyname(port, 'tcp')
                elif socktype == SOCK_DGRAM:
                    port = getservbyname(port, 'udp')
                else:
                    raise gaierror(EAI_SERVICE, 'Servname not supported for ai_socktype')
            except error, ex:
                if 'not found' in str(ex):
                    raise gaierror(EAI_SERVICE, 'Servname not supported for ai_socktype')
                else:
                    raise gaierror(str(ex))

        socktype_proto = [(SOCK_STREAM, 6), (SOCK_DGRAM, 17), (SOCK_RAW, 0)]
        if socktype:
            socktype_proto = [(x, y) for (x, y) in socktype_proto if socktype == x]
        if proto:
            socktype_proto = [(x, y) for (x, y) in socktype_proto if proto == y]

        result = []

        if family == AF_INET:
            for res in resolve_ipv4(host, evdns_flags)[1]:
                sockaddr = (inet_ntop(family, res), port)
                for socktype, proto in socktype_proto:
                    result.append((family, socktype, proto, '', sockaddr))
        elif family == AF_INET6:
            for res in resolve_ipv6(host, evdns_flags)[1]:
                sockaddr = (inet_ntop(family, res), port, 0, 0)
                for socktype, proto in socktype_proto:
                    result.append((family, socktype, proto, '', sockaddr))
        else:

            ipv4_res = None
            ipv6_res = None
            try:
                ipv4_res = resolve_ipv4(host, evdns_flags)[1]
            except:
                pass
            if not ipv4_res:
                ipv4_res = None
                ipv6_res= resolve_ipv6(host, evdns_flags)[1]

            if ipv4_res is not None:
                for res in ipv4_res:
                    sockaddr = (inet_ntop(AF_INET, res), port)
                    for socktype, proto in socktype_proto:
                        result.append((AF_INET, socktype, proto, '', sockaddr))
            if ipv6_res is not None:
                for res in ipv6_res:
                    sockaddr = (inet_ntop(AF_INET6, res), port, 0, 0)
                    for socktype, proto in socktype_proto:
                        result.append((AF_INET6, socktype, proto, '', sockaddr))

        return result
        # TODO libevent2 has getaddrinfo that is probably better than the hack above; should wrap that.


_have_ssl = False

try:
    from gevent.ssl import sslwrap_simple as ssl, SSLError as sslerror, SSLSocket as SSLType
    _have_ssl = True
except ImportError:
    try:
        from gevent.sslold import ssl, sslerror, SSLObject as SSLType
        _have_ssl = True
    except ImportError:
        pass

if sys.version_info[:2] <= (2, 5) and _have_ssl:
    __implements__.extend(['ssl', 'sslerror', 'SSLType'])


__all__ = __implements__ + __extensions__ + __imports__
