
# OpenSSL is more stable then ssl
# but OpenSSL is different then ssl, so need a wrapper

# this wrap has a close callback.
# Which is used by google ip manager(google_ip.py)
# google ip manager keep a connection number counter for every ip.

# the wrap is used to keep some attribute like ip/appid for ssl

# __iowait and makefile is used for gevent but not use now.


import sys
import os
import select
import time
import socket
import errno

import OpenSSL
SSLError = OpenSSL.SSL.WantReadError

current_path = os.path.dirname(os.path.abspath(__file__))

from pyasn1.codec.der import decoder as der_decoder
from subj_alt_name import SubjectAltName
from xlog import getLogger
xlog = getLogger("heroku_front")

ssl_version = ''
openssl_version = OpenSSL.version.__version__
support_alpn_npn = "no"


class SSLConnection(object):
    """OpenSSL Connection Wrapper"""

    def __init__(self, context, sock, ip=None, on_close=None):
        self._context = context
        self._sock = sock
        self.ip = ip
        self._connection = OpenSSL.SSL.Connection(context, sock)
        self._makefile_refs = 0
        self.on_close = on_close
        self.timeout = self._sock.gettimeout() or 0.1
        self.running = True
        self.socket_closed = False

    def __del__(self):
        if not self.socket_closed:
            socket.socket.close(self._sock)
            self.socket_closed = True
            if self.on_close:
                self.on_close(self.ip)

    def __getattr__(self, attr):
        if attr not in ('_context', '_sock', '_connection', '_makefile_refs'):
            return getattr(self._connection, attr)

    def __iowait(self, io_func, *args, **kwargs):
        fd = self._sock.fileno()
        time_start = time.time()
        while self.running:
            time_now = time.time()
            wait_timeout = max(0.1, self.timeout - (time_now - time_start))
            wait_timeout = min(wait_timeout, 10)
            # in case socket was blocked by FW
            # recv is called before send request, which timeout is 240
            # then send request is called and timeout change to 100

            try:
                return io_func(*args, **kwargs)
            except (OpenSSL.SSL.WantReadError, OpenSSL.SSL.WantX509LookupError):
                sys.exc_clear()
                _, _, errors = select.select([fd], [], [fd], wait_timeout)
                if errors:
                    raise
                if time_now - time_start > self.timeout:
                    break
            except OpenSSL.SSL.WantWriteError:
                sys.exc_clear()
                _, _, errors = select.select([], [fd], [fd], wait_timeout)
                if errors:
                    raise
                time_now = time.time()
                if time_now - time_start > self.timeout:
                    break
            except OpenSSL.SSL.SysCallError as e:
                if e[0] == 10035 and 'WSAEWOULDBLOCK' in e[1]:
                    sys.exc_clear()
                    if io_func == self._connection.send:
                        _, _, errors = select.select([], [fd], [fd], wait_timeout)
                    else:
                        _, _, errors = select.select([fd], [], [fd], wait_timeout)

                    if errors:
                        raise
                    time_now = time.time()
                    if time_now - time_start > self.timeout:
                        break
                else:
                    raise e
            except Exception as e:
                #xlog.exception("e:%r", e)
                raise e

        return 0

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
        except Exception as e:
            #xlog.exception("ssl send:%r", e)
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
                # remote closed
                #raise e
                return ""
            elif e[0] == 10053 or e[0] == 10054 or e[0] == 10038:
                return ""
            raise

    def recv_into(self, buf):
        pending = self._connection.pending()
        if pending:
            ret = self._connection.recv_into(buf)
            if not ret:
                # xlog.debug("recv_into 0")
                pass
            return ret

        while self.running:
            try:
                ret = self.__iowait(self._connection.recv_into, buf)
                if not ret:
                    # xlog.debug("recv_into 0")
                    pass
                return ret
            except OpenSSL.SSL.ZeroReturnError:
                continue
            except OpenSSL.SSL.SysCallError as e:
                if e[0] == -1 and 'Unexpected EOF' in e[1]:
                    # errors when reading empty strings are expected and can be ignored
                    return 0
                elif e[0] == 11 and e[1] == 'EAGAIN':
                    continue
                raise
            except errno.EAGAIN:
                continue
            except Exception as e:
                #xlog.exception("recv_into:%r", e)
                raise e

    def read(self, bufsiz, flags=0):
        return self.recv(bufsiz, flags)

    def write(self, buf, flags=0):
        return self.sendall(buf, flags)

    def close(self):
        if self._makefile_refs < 1:
            self.running = False
            if not self.socket_closed:
                socket.socket.close(self._sock)
                self.socket_closed = True
                if self.on_close:
                    self.on_close(self.ip)
        else:
            self._makefile_refs -= 1

    def settimeout(self, t):
        if not self.running:
            return

        if self.timeout != t:
            self._sock.settimeout(t)
            self.timeout = t

    def makefile(self, mode='r', bufsize=-1):
        self._makefile_refs += 1
        return socket._fileobject(self, mode, bufsize, close=True)

    @staticmethod
    def npn_select_callback(conn, protocols):
        # xlog.debug("npn protocl:%s", ";".join(protocols))
        if b"h2" in protocols:
            conn.protos = "h2"
            return b"h2"
        else:
            return b"http/1.1"

    @staticmethod
    def context_builder(ca_certs=None, cipher_suites=None):
        global ssl_version, support_alpn_npn

        if not ca_certs:
            ca_certs = os.path.join(current_path, "cacert.pem")

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
                # MacOS pyOpenSSL has TLSv1_2_METHOD attr but can use.
                # There for we hard code here.
                # may be try/cache is a better solution.
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
            ssl_context.set_verify(OpenSSL.SSL.VERIFY_NONE, lambda c, x,    e, d, ok: ok)

        # change default cipher suites.
        # Google video ip can act as Google FrontEnd if cipher suits not include
        # RC4-SHA:ECDHE-RSA-RC4-SHA:ECDHE-RSA-AES128-GCM-SHA256:AES128-GCM-SHA256
        #
        # 'ALL', '!aNULL', '!eNULL'
        #if not cipher_suites:
        #    cipher_suites = ('ALL:!RC4-SHA:!ECDHE-RSA-RC4-SHA:!ECDHE-RSA-AES128-GCM-SHA256:!AES128-GCM-SHA256:!ECDHE-RSA-AES128-SHA:!AES128-SHA',)
        #ssl_context.set_cipher_list(':'.join(cipher_suites))

        if True:
            try:
                ssl_context.set_alpn_protos([b'h2', b'http/1.1'])
                xlog.info("OpenSSL support alpn")
                support_alpn_npn = "alpn"
                return ssl_context
            except Exception as e:
                #xlog.exception("set_alpn_protos:%r", e)
                pass

            try:
                ssl_context.set_npn_select_callback(SSLConnection.npn_select_callback)
                xlog.info("OpenSSL support npn")
                support_alpn_npn = "npn"
            except Exception as e:
                #xlog.exception("set_npn_select_callback:%r", e)
                xlog.info("OpenSSL dont't support npn/alpn, no HTTP/2 supported.")

        return ssl_context


def get_subj_alt_name(peer_cert):
    '''
    Copied from ndg.httpsclient.ssl_peer_verification.ServerSSLCertVerification
    Extract subjectAltName DNS name settings from certificate extensions
    @param peer_cert: peer certificate in SSL connection.  subjectAltName
    settings if any will be extracted from this
    @type peer_cert: OpenSSL.crypto.X509
    '''
    # Search through extensions
    dns_name = []
    general_names = SubjectAltName()
    for i in range(peer_cert.get_extension_count()):
        ext = peer_cert.get_extension(i)
        ext_name = ext.get_short_name()
        if ext_name == "subjectAltName":
            # PyOpenSSL returns extension data in ASN.1 encoded form
            ext_dat = ext.get_data()
            decoded_dat = der_decoder.decode(ext_dat, asn1Spec=general_names)

            for name in decoded_dat:
                if isinstance(name, SubjectAltName):
                    for entry in range(len(name)):
                        component = name.getComponentByPosition(entry)
                        n = str(component.getComponent())
                        if n.startswith("*"):
                            continue
                        dns_name.append(n)
    return dns_name