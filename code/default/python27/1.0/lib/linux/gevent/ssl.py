# Wrapper module for _ssl. Written by Bill Janssen.
# Ported to gevent by Denis Bilenko.
"""SSL wrapper for socket objects.

For the documentation, refer to :mod:`ssl` module manual.

This module implements cooperative SSL socket wrappers.
On Python 2.6 and newer it uses Python's native :mod:`ssl` module. On Python 2.5 and 2.4
it requires `ssl package`_ to be installed.

.. _`ssl package`: http://pypi.python.org/pypi/ssl
"""

__ssl__ = __import__('ssl')

try:
    _ssl = __ssl__._ssl
except AttributeError:
    _ssl = __ssl__._ssl2

import sys
import errno
from gevent.socket import socket, _fileobject, wait_read, wait_write, timeout_default
from gevent.socket import error as socket_error, EBADF

__implements__ = ['SSLSocket',
                  'wrap_socket',
                  'get_server_certificate',
                  'sslwrap_simple']

__imports__ = ['SSLError',
               'RAND_status',
               'RAND_egd',
               'RAND_add',
               'cert_time_to_seconds',
               'get_protocol_name',
               'DER_cert_to_PEM_cert',
               'PEM_cert_to_DER_cert']

for name in __imports__[:]:
    try:
        value = getattr(__ssl__, name)
        globals()[name] = value
    except AttributeError:
        __imports__.remove(name)

for name in dir(__ssl__):
    if not name.startswith('_'):
        value = getattr(__ssl__, name)
        if isinstance(value, (int, long, basestring, tuple)):
            globals()[name] = value
            __imports__.append(name)

del name, value

__all__ = __implements__ + __imports__


class SSLSocket(socket):

    def __init__(self, sock, keyfile=None, certfile=None,
                 server_side=False, cert_reqs=CERT_NONE,
                 ssl_version=PROTOCOL_SSLv23, ca_certs=None,
                 do_handshake_on_connect=True,
                 suppress_ragged_eofs=True,
                 ciphers=None):
        socket.__init__(self, _sock=sock)

        if certfile and not keyfile:
            keyfile = certfile
        # see if it's connected
        try:
            socket.getpeername(self)
        except socket_error, e:
            if e[0] != errno.ENOTCONN:
                raise
            # no, no connection yet
            self._sslobj = None
        else:
            # yes, create the SSL object
            if ciphers is None:
                self._sslobj = _ssl.sslwrap(self._sock, server_side,
                                            keyfile, certfile,
                                            cert_reqs, ssl_version, ca_certs)
            else:
                self._sslobj = _ssl.sslwrap(self._sock, server_side,
                                            keyfile, certfile,
                                            cert_reqs, ssl_version, ca_certs,
                                            ciphers)
            if do_handshake_on_connect:
                self.do_handshake()
        self.keyfile = keyfile
        self.certfile = certfile
        self.cert_reqs = cert_reqs
        self.ssl_version = ssl_version
        self.ca_certs = ca_certs
        self.ciphers = ciphers
        self.do_handshake_on_connect = do_handshake_on_connect
        self.suppress_ragged_eofs = suppress_ragged_eofs
        self._makefile_refs = 0

    def read(self, len=1024):
        """Read up to LEN bytes and return them.
        Return zero-length string on EOF."""
        while True:
            try:
                return self._sslobj.read(len)
            except SSLError, ex:
                if ex.args[0] == SSL_ERROR_EOF and self.suppress_ragged_eofs:
                    return ''
                elif ex.args[0] == SSL_ERROR_WANT_READ:
                    if self.timeout == 0.0:
                        raise
                    sys.exc_clear()
                    try:
                        wait_read(self.fileno(), timeout=self.timeout, timeout_exc=_SSLErrorReadTimeout, event=self._read_event)
                    except socket_error, ex:
                        if ex[0] == EBADF:
                            return ''
                        raise
                elif ex.args[0] == SSL_ERROR_WANT_WRITE:
                    if self.timeout == 0.0:
                        raise
                    sys.exc_clear()
                    try:
                        # note: using _SSLErrorReadTimeout rather than _SSLErrorWriteTimeout below is intentional
                        wait_write(self.fileno(), timeout=self.timeout, timeout_exc=_SSLErrorReadTimeout, event=self._write_event)
                    except socket_error, ex:
                        if ex[0] == EBADF:
                            return ''
                        raise
                else:
                    raise

    def write(self, data):
        """Write DATA to the underlying SSL channel.  Returns
        number of bytes of DATA actually transmitted."""
        while True:
            try:
                return self._sslobj.write(data)
            except SSLError, ex:
                if ex.args[0] == SSL_ERROR_WANT_READ:
                    if self.timeout == 0.0:
                        raise
                    sys.exc_clear()
                    try:
                        wait_read(self.fileno(), timeout=self.timeout, timeout_exc=_SSLErrorWriteTimeout, event=self._read_event)
                    except socket_error, ex:
                        if ex[0] == EBADF:
                            return 0
                        raise
                elif ex.args[0] == SSL_ERROR_WANT_WRITE:
                    if self.timeout == 0.0:
                        raise
                    sys.exc_clear()
                    try:
                        wait_write(self.fileno(), timeout=self.timeout, timeout_exc=_SSLErrorWriteTimeout, event=self._write_event)
                    except socket_error, ex:
                        if ex[0] == EBADF:
                            return 0
                        raise
                else:
                    raise

    def getpeercert(self, binary_form=False):
        """Returns a formatted version of the data in the
        certificate provided by the other end of the SSL channel.
        Return None if no certificate was provided, {} if a
        certificate was provided, but not validated."""
        return self._sslobj.peer_certificate(binary_form)

    def cipher(self):
        if not self._sslobj:
            return None
        else:
            return self._sslobj.cipher()

    def send(self, data, flags=0, timeout=timeout_default):
        if timeout is timeout_default:
            timeout = self.timeout
        if self._sslobj:
            if flags != 0:
                raise ValueError(
                    "non-zero flags not allowed in calls to send() on %s" %
                    self.__class__)
            while True:
                try:
                    v = self._sslobj.write(data)
                except SSLError, x:
                    if x.args[0] == SSL_ERROR_WANT_READ:
                        if self.timeout == 0.0:
                            return 0
                        sys.exc_clear()
                        try:
                            wait_read(self.fileno(), timeout=timeout, event=self._read_event)
                        except socket_error, ex:
                            if ex[0] == EBADF:
                                return 0
                            raise
                    elif x.args[0] == SSL_ERROR_WANT_WRITE:
                        if self.timeout == 0.0:
                            return 0
                        sys.exc_clear()
                        try:
                            wait_write(self.fileno(), timeout=timeout, event=self._write_event)
                        except socket_error, ex:
                            if ex[0] == EBADF:
                                return 0
                            raise
                    else:
                        raise
                else:
                    return v
        else:
            return socket.send(self, data, flags, timeout)
    # is it possible for sendall() to send some data without encryption if another end shut down SSL?

    def sendto(self, *args):
        if self._sslobj:
            raise ValueError("sendto not allowed on instances of %s" %
                             self.__class__)
        else:
            return socket.sendto(self, *args)

    def recv(self, buflen=1024, flags=0):
        if self._sslobj:
            if flags != 0:
                raise ValueError(
                    "non-zero flags not allowed in calls to recv() on %s" %
                    self.__class__)
            # QQQ Shouldn't we wrap the SSL_WANT_READ errors as socket.timeout errors to match socket.recv's behavior?
            return self.read(buflen)
        else:
            return socket.recv(self, buflen, flags)

    def recv_into(self, buffer, nbytes=None, flags=0):
        if buffer and (nbytes is None):
            nbytes = len(buffer)
        elif nbytes is None:
            nbytes = 1024
        if self._sslobj:
            if flags != 0:
                raise ValueError(
                  "non-zero flags not allowed in calls to recv_into() on %s" %
                  self.__class__)
            while True:
                try:
                    tmp_buffer = self.read(nbytes)
                    v = len(tmp_buffer)
                    buffer[:v] = tmp_buffer
                    return v
                except SSLError, x:
                    if x.args[0] == SSL_ERROR_WANT_READ:
                        sys.exc_clear()
                        if self.timeout == 0.0:
                            raise
                        try:
                            wait_read(self.fileno(), timeout=self.timeout, event=self._read_event)
                        except socket_error, ex:
                            if ex[0] == EBADF:
                                return 0
                            raise
                        continue
                    else:
                        raise
        else:
            return socket.recv_into(self, buffer, nbytes, flags)

    def recvfrom(self, *args):
        if self._sslobj:
            raise ValueError("recvfrom not allowed on instances of %s" %
                             self.__class__)
        else:
            return socket.recvfrom(self, *args)

    def recvfrom_into(self, *args):
        if self._sslobj:
            raise ValueError("recvfrom_into not allowed on instances of %s" %
                             self.__class__)
        else:
            return socket.recvfrom_into(self, *args)

    def pending(self):
        if self._sslobj:
            return self._sslobj.pending()
        else:
            return 0

    def _sslobj_shutdown(self):
        while True:
            try:
                return self._sslobj.shutdown()
            except SSLError, ex:
                if ex.args[0] == SSL_ERROR_EOF and self.suppress_ragged_eofs:
                    return ''
                elif ex.args[0] == SSL_ERROR_WANT_READ:
                    if self.timeout == 0.0:
                        raise
                    sys.exc_clear()
                    try:
                        wait_read(self.fileno(), timeout=self.timeout, timeout_exc=_SSLErrorReadTimeout, event=self._read_event)
                    except socket_error, ex:
                        if ex[0] == EBADF:
                            return ''
                        raise
                elif ex.args[0] == SSL_ERROR_WANT_WRITE:
                    if self.timeout == 0.0:
                        raise
                    sys.exc_clear()
                    try:
                        wait_write(self.fileno(), timeout=self.timeout, timeout_exc=_SSLErrorWriteTimeout, event=self._write_event)
                    except socket_error, ex:
                        if ex[0] == EBADF:
                            return ''
                        raise
                else:
                    raise

    def unwrap(self):
        if self._sslobj:
            s = self._sslobj_shutdown()
            self._sslobj = None
            return socket(_sock=s)
        else:
            raise ValueError("No SSL wrapper around " + str(self))

    def shutdown(self, how):
        self._sslobj = None
        socket.shutdown(self, how)

    def close(self):
        if self._makefile_refs < 1:
            self._sslobj = None
            socket.close(self)
        else:
            self._makefile_refs -= 1

    def do_handshake(self):
        """Perform a TLS/SSL handshake."""
        while True:
            try:
                return self._sslobj.do_handshake()
            except SSLError, ex:
                if ex.args[0] == SSL_ERROR_WANT_READ:
                    if self.timeout == 0.0:
                        raise
                    sys.exc_clear()
                    wait_read(self.fileno(), timeout=self.timeout, timeout_exc=_SSLErrorHandshakeTimeout, event=self._read_event)
                elif ex.args[0] == SSL_ERROR_WANT_WRITE:
                    if self.timeout == 0.0:
                        raise
                    sys.exc_clear()
                    wait_write(self.fileno(), timeout=self.timeout, timeout_exc=_SSLErrorHandshakeTimeout, event=self._write_event)
                else:
                    raise

    def connect(self, addr):
        """Connects to remote ADDR, and then wraps the connection in
        an SSL channel."""
        # Here we assume that the socket is client-side, and not
        # connected at the time of the call.  We connect it, then wrap it.
        if self._sslobj:
            raise ValueError("attempt to connect already-connected SSLSocket!")
        socket.connect(self, addr)
        if self.ciphers is None:
            self._sslobj = _ssl.sslwrap(self._sock, False, self.keyfile, self.certfile,
                                        self.cert_reqs, self.ssl_version,
                                        self.ca_certs)
        else:
            self._sslobj = _ssl.sslwrap(self._sock, False, self.keyfile, self.certfile,
                                        self.cert_reqs, self.ssl_version,
                                        self.ca_certs, self.ciphers)
        if self.do_handshake_on_connect:
            self.do_handshake()

    def accept(self):
        """Accepts a new connection from a remote client, and returns
        a tuple containing that new connection wrapped with a server-side
        SSL channel, and the address of the remote client."""
        newsock, addr = socket.accept(self)
        return (SSLSocket(newsock._sock,
                          keyfile=self.keyfile,
                          certfile=self.certfile,
                          server_side=True,
                          cert_reqs=self.cert_reqs,
                          ssl_version=self.ssl_version,
                          ca_certs=self.ca_certs,
                          do_handshake_on_connect=self.do_handshake_on_connect,
                          suppress_ragged_eofs=self.suppress_ragged_eofs,
                          ciphers=self.ciphers),
                addr)

    def makefile(self, mode='r', bufsize=-1):
        """Make and return a file-like object that
        works with the SSL connection.  Just use the code
        from the socket module."""
        self._makefile_refs += 1
        # close=True so as to decrement the reference count when done with
        # the file-like object.
        return _fileobject(self, mode, bufsize, close=True)


_SSLErrorReadTimeout = SSLError('The read operation timed out')
_SSLErrorWriteTimeout = SSLError('The write operation timed out')
_SSLErrorHandshakeTimeout = SSLError('The handshake operation timed out')


def wrap_socket(sock, keyfile=None, certfile=None,
                server_side=False, cert_reqs=CERT_NONE,
                ssl_version=PROTOCOL_SSLv23, ca_certs=None,
                do_handshake_on_connect=True,
                suppress_ragged_eofs=True, ciphers=None):
    """Create a new :class:`SSLSocket` instance."""
    return SSLSocket(sock, keyfile=keyfile, certfile=certfile,
                     server_side=server_side, cert_reqs=cert_reqs,
                     ssl_version=ssl_version, ca_certs=ca_certs,
                     do_handshake_on_connect=do_handshake_on_connect,
                     suppress_ragged_eofs=suppress_ragged_eofs,
                     ciphers=ciphers)


def get_server_certificate(addr, ssl_version=PROTOCOL_SSLv23, ca_certs=None):
    """Retrieve the certificate from the server at the specified address,
    and return it as a PEM-encoded string.
    If 'ca_certs' is specified, validate the server cert against it.
    If 'ssl_version' is specified, use it in the connection attempt."""

    host, port = addr
    if (ca_certs is not None):
        cert_reqs = CERT_REQUIRED
    else:
        cert_reqs = CERT_NONE
    s = wrap_socket(socket(), ssl_version=ssl_version,
                    cert_reqs=cert_reqs, ca_certs=ca_certs)
    s.connect(addr)
    dercert = s.getpeercert(True)
    s.close()
    return DER_cert_to_PEM_cert(dercert)


def sslwrap_simple(sock, keyfile=None, certfile=None):
    """A replacement for the old socket.ssl function.  Designed
    for compability with Python 2.5 and earlier.  Will disappear in
    Python 3.0."""
    return SSLSocket(sock, keyfile, certfile)
