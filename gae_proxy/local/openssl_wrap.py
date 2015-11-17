
# OpenSSL is more stable then ssl
# but OpenSSL is different then ssl, so need a wrapper
import sys
import os


import OpenSSL
SSLError = OpenSSL.SSL.WantReadError

import select
import time
import socket
import xlog

ssl_version = ''

class SSLConnection(object):
    """OpenSSL Connection Wrapper"""

    def __init__(self, context, sock):
        self._context = context
        self._sock = sock
        self._connection = OpenSSL.SSL.Connection(context, sock)
        self._makefile_refs = 0

    def __getattr__(self, attr):
        if attr not in ('_context', '_sock', '_connection', '_makefile_refs'):
            return getattr(self._connection, attr)

    def __iowait(self, io_func, *args, **kwargs):
        timeout = self._sock.gettimeout() or 0.1
        fd = self._sock.fileno()
        time_start = time.time()
        while True:
            try:
                return io_func(*args, **kwargs)
            except (OpenSSL.SSL.WantReadError, OpenSSL.SSL.WantX509LookupError):
                sys.exc_clear()
                _, _, errors = select.select([fd], [], [fd], timeout)
                if errors:
                    break
                time_now = time.time()
                if time_now - time_start > timeout:
                    break
            except OpenSSL.SSL.WantWriteError:
                sys.exc_clear()
                _, _, errors = select.select([], [fd], [fd], timeout)
                if errors:
                    break
                time_now = time.time()
                if time_now - time_start > timeout:
                    break

    def accept(self):
        sock, addr = self._sock.accept()
        client = OpenSSL.SSL.Connection(sock._context, sock)
        return client, addr

    def do_handshake(self):
        self.__iowait(self._connection.do_handshake)

    def connect(self, *args, **kwargs):
        return self.__iowait(self._connection.connect, *args, **kwargs)

    def __send(self, data, flags=0):
        try:
            return self.__iowait(self._connection.send, data, flags)
        except OpenSSL.SSL.SysCallError as e:
            if e[0] == -1 and not data:
                # errors when writing empty strings are expected and can be ignored
                return 0
            raise

    def __send_memoryview(self, data, flags=0):
        if hasattr(data, 'tobytes'):
            data = data.tobytes()
        return self.__send(data, flags)

    send = __send if sys.version_info >= (2, 7, 5) else __send_memoryview

    def recv(self, bufsiz, flags=0):
        pending = self._connection.pending()
        if pending:
            return self._connection.recv(min(pending, bufsiz))
        try:
            return self.__iowait(self._connection.recv, bufsiz, flags)
        except OpenSSL.SSL.ZeroReturnError:
            return ''
        except OpenSSL.SSL.SysCallError as e:
            if e[0] == -1 and 'Unexpected EOF' in e[1]:
                # errors when reading empty strings are expected and can be ignored
                return ''
            raise

    def read(self, bufsiz, flags=0):
        return self.recv(bufsiz, flags)

    def write(self, buf, flags=0):
        return self.sendall(buf, flags)

    def close(self):
        if self._makefile_refs < 1:
            self._connection = None
            if self._sock:
                socket.socket.close(self._sock)
        else:
            self._makefile_refs -= 1

    def makefile(self, mode='r', bufsize=-1):
        self._makefile_refs += 1
        return socket._fileobject(self, mode, bufsize, close=True)

    @staticmethod
    def context_builder(ca_certs=None, cipher_suites=('ALL:!RC4-SHA:!ECDHE-RSA-RC4-SHA:!ECDHE-RSA-AES128-GCM-SHA256:!AES128-GCM-SHA256',)):
        # 'ALL', '!aNULL', '!eNULL'
        global  ssl_version

        if not ssl_version:
            if hasattr(OpenSSL.SSL, "TLSv1_2_METHOD"):
                ssl_version = "TLSv1_2"
            elif hasattr(OpenSSL.SSL, "TLSv1_1_METHOD"):
                ssl_version = "TLSv1_1"
            elif hasattr(OpenSSL.SSL, "TLSv1_METHOD"):
                ssl_version = "TLSv1"
            else:
                ssl_version = "SSLv23"

            if sys.platform == "darwin":
                ssl_version = "TLSv1"
            
            # freenas openssl support fix from twitter user "himanzero"
            # https://twitter.com/himanzero/status/645231724318748672
            if sys.platform == "freebsd9":
                ssl_version = "TLSv1"

            xlog.info("SSL use version:%s", ssl_version)

        protocol_version = getattr(OpenSSL.SSL, '%s_METHOD' % ssl_version)
        ssl_context = OpenSSL.SSL.Context(protocol_version)
        if ca_certs:
            ssl_context.load_verify_locations(os.path.abspath(ca_certs))
            ssl_context.set_verify(OpenSSL.SSL.VERIFY_PEER, lambda c, x, e, d, ok: ok)
        else:
            ssl_context.set_verify(OpenSSL.SSL.VERIFY_NONE, lambda c, x, e, d, ok: ok)
        ssl_context.set_cipher_list(':'.join(cipher_suites))
        return ssl_context

