# Copyright (c) 2009-2012 Denis Bilenko. See LICENSE for details.
"""TCP/SSL server"""
import sys
import _socket
from gevent.baseserver import BaseServer
from gevent.socket import EWOULDBLOCK, socket


__all__ = ['StreamServer', 'DatagramServer']


if sys.platform == 'win32':
    # SO_REUSEADDR on Windows does not mean the same thing as on *nix (issue #217)
    DEFAULT_REUSE_ADDR = None
else:
    DEFAULT_REUSE_ADDR = 1


class StreamServer(BaseServer):
    """A generic TCP server. Accepts connections on a listening socket and spawns user-provided *handle*
    for each connection with 2 arguments: the client socket and the client address.

    If any of the following keyword arguments are present, then the server assumes SSL mode and uses these arguments
    to create an SSL wrapper for the client socket before passing it to *handle*:

    - keyfile
    - certfile
    - cert_reqs
    - ssl_version
    - ca_certs
    - suppress_ragged_eofs
    - do_handshake_on_connect
    - ciphers

    Note that although the errors in a successfully spawned handler will not affect the server or other connections,
    the errors raised by :func:`accept` and *spawn* cause the server to stop accepting for a short amount of time. The
    exact period depends on the values of :attr:`min_delay` and :attr:`max_delay` attributes.

    The delay starts with :attr:`min_delay` and doubles with each successive error until it reaches :attr:`max_delay`.
    A successful :func:`accept` resets the delay to :attr:`min_delay` again.
    """
    # the default backlog to use if none was provided in __init__
    backlog = 256

    reuse_addr = DEFAULT_REUSE_ADDR

    def __init__(self, listener, handle=None, backlog=None, spawn='default', **ssl_args):
        BaseServer.__init__(self, listener, handle=handle, spawn=spawn)
        try:
            if ssl_args:
                ssl_args.setdefault('server_side', True)
                from gevent.ssl import wrap_socket
                self.wrap_socket = wrap_socket
                self.ssl_args = ssl_args
            else:
                self.ssl_args = None
            if backlog is not None:
                if hasattr(self, 'socket'):
                    raise TypeError('backlog must be None when a socket instance is passed')
                self.backlog = backlog
        except:
            self.close()
            raise

    @property
    def ssl_enabled(self):
        return self.ssl_args is not None

    def set_listener(self, listener):
        BaseServer.set_listener(self, listener)
        try:
            self.socket = self.socket._sock
        except AttributeError:
            pass

    def init_socket(self):
        if not hasattr(self, 'socket'):
            self.socket = self.get_listener(self.address, self.backlog, self.family)
            self.address = self.socket.getsockname()
        if self.ssl_args:
            self._handle = self.wrap_socket_and_handle
        else:
            self._handle = self.handle

    @classmethod
    def get_listener(self, address, backlog=None, family=None):
        if backlog is None:
            backlog = self.backlog
        return _tcp_listener(address, backlog=backlog, reuse_addr=self.reuse_addr, family=family)

    def do_read(self):
        try:
            client_socket, address = self.socket.accept()
        except _socket.error, err:
            if err[0] == EWOULDBLOCK:
                return
            raise
        return socket(_sock=client_socket), address

    def wrap_socket_and_handle(self, client_socket, address):
        # used in case of ssl sockets
        ssl_socket = self.wrap_socket(client_socket, **self.ssl_args)
        return self.handle(ssl_socket, address)


class DatagramServer(BaseServer):
    """A UDP server"""

    reuse_addr = DEFAULT_REUSE_ADDR

    def __init__(self, *args, **kwargs):
        BaseServer.__init__(self, *args, **kwargs)
        from gevent.lock import Semaphore
        self._writelock = Semaphore()

    def init_socket(self):
        if not hasattr(self, 'socket'):
            self.socket = self.get_listener(self.address, self.family)
            self.address = self.socket.getsockname()
        self._socket = self.socket
        try:
            self._socket = self._socket._sock
        except AttributeError:
            pass

    @classmethod
    def get_listener(self, address, family=None):
        return _udp_socket(address, reuse_addr=self.reuse_addr, family=family)

    def do_read(self):
        try:
            data, address = self._socket.recvfrom(8192)
        except _socket.error, err:
            if err[0] == EWOULDBLOCK:
                return
            raise
        return data, address

    def sendto(self, *args):
        self._writelock.acquire()
        try:
            self.socket.sendto(*args)
        finally:
            self._writelock.release()


def _tcp_listener(address, backlog=50, reuse_addr=None, family=_socket.AF_INET):
    """A shortcut to create a TCP socket, bind it and put it into listening state."""
    sock = socket(family=family)
    if reuse_addr is not None:
        sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, reuse_addr)
    try:
        sock.bind(address)
    except _socket.error:
        ex = sys.exc_info()[1]
        strerror = getattr(ex, 'strerror', None)
        if strerror is not None:
            ex.strerror = strerror + ': ' + repr(address)
        raise
    sock.listen(backlog)
    sock.setblocking(0)
    return sock


def _udp_socket(address, backlog=50, reuse_addr=None, family=_socket.AF_INET):
    # we want gevent.socket.socket here
    sock = socket(family=family, type=_socket.SOCK_DGRAM)
    if reuse_addr is not None:
        sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, reuse_addr)
    try:
        sock.bind(address)
    except _socket.error:
        ex = sys.exc_info()[1]
        strerror = getattr(ex, 'strerror', None)
        if strerror is not None:
            ex.strerror = strerror + ': ' + repr(address)
        raise
    return sock
