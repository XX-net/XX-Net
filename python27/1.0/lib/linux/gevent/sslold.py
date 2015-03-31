"""OpenSSL-based implementation of SSLObject.

.. warning::

    This module is deprecated. Use :mod:`ssl <gevent.ssl>` instead.
"""
from OpenSSL import SSL
from gevent.socket import socket, _fileobject, __socket__, error, timeout, EWOULDBLOCK
from gevent.socket import wait_read, wait_write, timeout_default
import sys

__all__ = ['ssl', 'sslerror']

import warnings
warnings.warn("gevent.sslold is deprecated; use gevent.ssl instead (install ssl package from PyPI)", DeprecationWarning, stacklevel=2)

try:
    sslerror = __socket__.sslerror
except AttributeError:

    class sslerror(error):
        pass


class SSLObject(socket):

    def __init__(self, sock, server_side=False):
        socket.__init__(self, _sock=sock)
        self._makefile_refs = 0
        if server_side:
            self._sock.set_accept_state()
        else:
            self._sock.set_connect_state()

    def __getattr__(self, item):
        assert item != '_sock', item
        # since socket no longer implements __getattr__ let's do it here
        # even though it's not good for the same reasons it was not good on socket instances
        # (it confuses sublcasses)
        return getattr(self._sock, item)

    def _formatinfo(self):
        return socket._formatinfo(self) + ' state_string=%r' % self._sock.state_string()

    def accept(self):
        sock, addr = socket.accept(self)
        client = SSLObject(sock._sock, server_side=True)
        client.do_handshake()
        return client, addr

    def do_handshake(self):
        while True:
            try:
                self._sock.do_handshake()
                break
            except SSL.WantReadError:
                sys.exc_clear()
                wait_read(self.fileno())
            except SSL.WantWriteError:
                sys.exc_clear()
                wait_write(self.fileno())
            except SSL.SysCallError, ex:
                raise sslerror(SysCallError_code_mapping.get(ex.args[0], ex.args[0]), ex.args[1])
            except SSL.Error, ex:
                raise sslerror(str(ex))

    def connect(self, *args):
        socket.connect(self, *args)
        self.do_handshake()

    def send(self, data, flags=0, timeout=timeout_default):
        if timeout is timeout_default:
            timeout = self.timeout
        while True:
            try:
                return self._sock.send(data, flags)
            except SSL.WantWriteError, ex:
                if self.timeout == 0.0:
                    raise timeout(str(ex))
                else:
                    sys.exc_clear()
                    wait_write(self.fileno(), timeout=timeout)
            except SSL.WantReadError, ex:
                if self.timeout == 0.0:
                    raise timeout(str(ex))
                else:
                    sys.exc_clear()
                    wait_read(self.fileno(), timeout=timeout)
            except SSL.SysCallError, ex:
                if ex[0] == -1 and data == "":
                    # errors when writing empty strings are expected and can be ignored
                    return 0
                raise sslerror(SysCallError_code_mapping.get(ex.args[0], ex.args[0]), ex.args[1])
            except SSL.Error, ex:
                raise sslerror(str(ex))

    def recv(self, buflen):
        pending = self._sock.pending()
        if pending:
            return self._sock.recv(min(pending, buflen))
        while True:
            try:
                return self._sock.recv(buflen)
            except SSL.WantReadError, ex:
                if self.timeout == 0.0:
                    raise timeout(str(ex))
                else:
                    sys.exc_clear()
                    wait_read(self.fileno(), timeout=self.timeout)
            except SSL.WantWriteError, ex:
                if self.timeout == 0.0:
                    raise timeout(str(ex))
                else:
                    sys.exc_clear()
                    wait_read(self.fileno(), timeout=self.timeout)
            except SSL.ZeroReturnError:
                return ''
            except SSL.SysCallError, ex:
                raise sslerror(SysCallError_code_mapping.get(ex.args[0], ex.args[0]), ex.args[1])
            except SSL.Error, ex:
                raise sslerror(str(ex))

    def read(self, buflen=1024):
        """
        NOTE: read() in SSLObject does not have the semantics of file.read
        reading here until we have buflen bytes or hit EOF is an error
        """
        return self.recv(buflen)

    def write(self, data):
        try:
            return self.sendall(data)
        except SSL.Error, ex:
            raise sslerror(str(ex))

    def makefile(self, mode='r', bufsize=-1):
        self._makefile_refs += 1
        return _fileobject(self, mode, bufsize, close=True)

    def close(self):
        if self._makefile_refs < 1:
            self._sock.shutdown()
            # QQQ wait until shutdown completes?
            socket.close(self)
        else:
            self._makefile_refs -= 1


SysCallError_code_mapping = {-1: 8}


def ssl(sock, keyfile=None, certfile=None):
    context = SSL.Context(SSL.SSLv23_METHOD)
    if certfile is not None:
        context.use_certificate_file(certfile)
    if keyfile is not None:
        context.use_privatekey_file(keyfile)
    context.set_verify(SSL.VERIFY_NONE, lambda *x: True)
    timeout = sock.gettimeout()
    try:
        sock = sock._sock
    except AttributeError:
        pass
    connection = SSL.Connection(context, sock)
    ssl_sock = SSLObject(connection)
    ssl_sock.settimeout(timeout)

    try:
        sock.getpeername()
    except Exception:
        # no, no connection yet
        pass
    else:
        # yes, do the handshake
        ssl_sock.do_handshake()
    return ssl_sock


def wrap_socket(sock, keyfile=None, certfile=None,
                server_side=None, cert_reqs=None,
                ssl_version=None, ca_certs=None,
                do_handshake_on_connect=None,
                suppress_ragged_eofs=None):
    """Create a new :class:`SSLObject` instance.

    For compatibility with :mod:`gevent.ssl` the function accepts all the arguments that :func:`gevent.ssl.wrap_socket`
    accepts. However, it only understands what *sock*, *keyfile* and *certfile* mean, so it will raise
    :exc:`ImportError` if you pass anything else.
    """
    for arg in ['cert_reqs', 'ssl_version', 'ca_certs', 'do_handshake_on_connect', 'suppress_ragged_eofs']:
        if locals()[arg] is not None:
            raise TypeError('To use argument %r install ssl package: http://pypi.python.org/pypi/ssl' % arg)
    return ssl(sock, keyfile=keyfile, certfile=certfile)
