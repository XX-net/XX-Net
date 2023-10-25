
# this wrap has a close callback.
# Which is used by  ip manager
#  ip manager keep a connection number counter for every ip.

# the wrap SSL implementation, python 2.7 will use pyOpenSSL, python 3.x will use build in ssl.
# This can also be used to store some attribute like ip_str/appid

import socket

from tlslite.tlsconnection import TLSConnection
from tlslite.handshakesettings import HandshakeSettings
import utils


class SSLConnection(object):
    def __init__(self, context, sock, ip_str=None, sni=None, on_close=None):
        self._context = context
        self._sock = sock
        self.ip_str = utils.to_bytes(ip_str)
        self.sni = sni
        self._makefile_refs = 0
        self._on_close = on_close
        self.peer_cert = None
        self.socket_closed = False
        self.timeout = self._sock.gettimeout() or 0.1
        self.running = True
        self._connection = None
        self.wrap()

    def wrap(self):
        ip, port = utils.get_ip_port(self.ip_str)
        if isinstance(ip, str):
            ip = utils.to_bytes(ip)

        try:
            self._sock.connect((ip, port))
        except Exception as e:
            raise socket.error('conn %s fail, sni:%s, e:%r' % (self.ip_str, self.sni, e))

        self._connection = TLSConnection(self._sock)

    def is_support_h2(self):
        if self._connection.session.appProto == bytearray(b"h2"):
            return True
        else:
            return False

    def setblocking(self, block):
        self._sock.setblocking(block)

    def __getattr__(self, attr):
        if attr == "socket_closed":
            # work around in case close before finished init.
            return True

        elif attr in ('is_support_h2', "_on_close", '_context', '_sock', '_connection', '_makefile_refs',
                      'sni', 'wrap', 'socket_closed'):
            return getattr(self, attr)

        elif hasattr(self._connection, attr):
            return getattr(self._connection, attr)

    def __del__(self):
        if not self.socket_closed and self._connection:
            self._connection.close()
            self.socket_closed = True
            if self._on_close:
                self._on_close(self.ip_str, self.sni)

    def get_cert(self):
        if self.peer_cert:
            return self.peer_cert

        cert = self._connection.session.serverCertChain.x509List[0].bytes
        cert = bytes(cert)

        from asn1crypto.x509 import Certificate
        cert = Certificate.load(cert)

        try:
            altName = cert.subject_alt_name_value.native
        except:
            altName = []

        self.peer_cert = {
            "cert": cert,
            "issuer_commonname": cert.issuer.human_friendly,
            "commonName": "",
            "altName": altName
        }

        return self.peer_cert

    def do_handshake(self):
        cert_chain = None
        privateKey = None
        self._connection.handshakeClientCert(cert_chain, privateKey, None,
            self._context.settings, None, None, None, self.sni, False, self._context.alpn)

    def connect(self, *args, **kwargs):
        return self._connection.connect(*args, **kwargs)

    def send(self, data, flags=0):
        try:
            return self._connection.send(data)
        except Exception as e:
            #self.logger.exception("ssl send:%r", e)
            raise e

    def recv(self, bufsiz, flags=0):
        return self._connection.recv(bufsiz)

    def recv_into(self, buf, nbytes=None):
        if not nbytes:
            nbytes = len(buf)

        data = self._connection.read(nbytes)
        if not data:
            return None
        buf[:len(data)] = data
        return len(data)

    def read(self, bufsiz, flags=0):
        return self.recv(bufsiz, flags)

    def write(self, buf, flags=0):
        return self.sendall(buf, flags)

    def close(self, reason=""):
        if self._makefile_refs < 1:
            self.running = False
            if not self.socket_closed:
                socket.socket.close(self._sock)
                self.socket_closed = True
                if self._on_close:
                    self._on_close(self.ip_str, self.sni, reason=reason)
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

    def fileno(self):
        return self._sock.fileno()


class SSLContext(object):
    def __init__(self, logger, ca_certs=None, cipher_suites=None, support_http2=True, protocol=None):
        self.logger = logger
        self.context = self

        self.settings = HandshakeSettings()

        self.support_alpn_npn = None
        self.alpn = []
        if support_http2:
            self.alpn = [
                bytearray(b"h2"),
            ]
        self.alpn.append(bytearray(b"http/1.1"))

    def supported_protocol(self):
        return "TLS 1.3"

    def support_alpn_npn(self):
        return "alpn"


class SSLCert:
    def __init__(self, cert):
        """
            Returns a (common name, [subject alternative names]) tuple.
        """
        self.x509 = cert
