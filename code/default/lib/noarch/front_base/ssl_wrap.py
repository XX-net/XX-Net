
# this wrap has a close callback.
# Which is used by  ip manager
#  ip manager keep a connection number counter for every ip.

# the wrap SSL implementation, python 2.7 will use pyOpenSSL, python 3.x will use build in ssl.
# This can also be used to store some attribute like ip_str/appid

import os
import sys
import datetime
import socket
import ssl
import time
import select
import errno

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

        self._connection = self._context.wrap_socket(self._sock, server_hostname=self.sni,
                                                     do_handshake_on_connect=False)

    def is_support_h2(self):
        if sys.version_info[0] == 3:
            return self._connection.selected_alpn_protocol() == "h2" or self._connection.selected_npn_protocol() == "h2"
        else:
            return self._connection.get_alpn_proto_negotiated()

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

    def set_tlsext_host_name(self, hostname):
        self._connection.server_hostname = utils.to_str(hostname)

    def get_cert(self):
        # py3 only
        if self.peer_cert:
            return self.peer_cert

        cert = self._connection.getpeercert()
        # For debug:
        #cert = self._connection.getpeercert(True)
        #from asn1crypto.x509 import Certificate
        #cert = Certificate.load(cert)

        self.peer_cert = {
            "cert": cert,
            "issuer_commonname": "",
            "commonName": "",
            "altName": []
        }
        for kv in cert.get("issuer", {}):
            k, v = kv[0]
            if k == 'commonName':
                self.peer_cert["issuer_commonname"] = v

        for kv in cert.get("subject", {}):
            k, v = kv[0]
            if k == 'commonName':
                self.peer_cert["commonName"] = v

        for k, v in cert.get("subjectAltName", {}):
            self.peer_cert["altName"].append(v)
        self.peer_cert["altName"] = tuple(self.peer_cert["altName"])

        return self.peer_cert

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
            except Exception as e:
                #self.logger.exception("e:%r", e)
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
        except Exception as e:
            #self.logger.exception("ssl send:%r", e)
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
        except Exception:
            return ''

    def recv_into(self, buf, nbytes=None):
        pending = self._connection.pending()
        if pending:
            ret = self._connection.recv_into(buf, nbytes)
            if not ret:
                # self.logger.debug("recv_into 0")
                pass
            return ret

        while self.running:
            try:
                ret = self.__iowait(self._connection.recv_into, buf, nbytes)
                if not ret:
                    # self.logger.debug("recv_into 0")
                    pass
                return ret
            except Exception as e:
                if sys.version_info[0] == 2 and e == errno.EAGAIN:
                    continue
                # logging.exception("recv %r", e)
                raise e

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
            if sys.version_info[0] == 3:
                self._connection.settimeout(t)
            else:
                self._sock.settimeout(t)
            self.timeout = t

    def makefile(self, mode='r', bufsize=-1):
        self._makefile_refs += 1
        return socket._fileobject(self, mode, bufsize, close=True)


class SSLContext(object):
    def __init__(self, logger, ca_certs=None, cipher_suites=None, support_http2=True, protocol=None):
        self.logger = logger

        if protocol == "TLSv1_2":
            ssl_version = ssl.PROTOCOL_TLSv1_2

        elif hasattr(ssl, "PROTOCOL_TLS"):
            ssl_version = ssl.PROTOCOL_TLS
        elif hasattr(ssl, "PROTOCOL_TLSv1_2"):
            ssl_version = ssl.PROTOCOL_TLSv1_2
        elif hasattr(ssl, "PROTOCOL_TLSv1_1"):
            ssl_version = ssl.PROTOCOL_TLSv1_1
        elif hasattr(ssl, "PROTOCOL_TLSv1"):
            ssl_version = ssl.PROTOCOL_TLSv1
        elif hasattr(ssl, "PROTOCOL_SSLv3"):
            ssl_version = ssl.PROTOCOL_SSLv3
        elif hasattr(ssl, "PROTOCOL_SSLv2"):
            ssl_version = ssl.PROTOCOL_SSLv2
        else:
            ssl_version = ssl.PROTOCOL_SSLv23

        self.logger.info("SSL use version:%s", self.supported_protocol())
        self.context = ssl.SSLContext(protocol=ssl_version)

        self.set_ca(ca_certs)

        if cipher_suites:
            self.context.set_ciphers(':'.join(cipher_suites))

        self.support_alpn_npn = None
        if support_http2:
            try:
                self.context.set_alpn_protocols(['h2', 'http/1.1'])
                self.logger.info("OpenSSL support alpn")
                self.support_alpn_npn = "alpn"
                return
            except Exception as e:
                self.logger.exception("set_alpn_protos:%r", e)
                pass

            try:
                self.context.set_npn_protocols(['h2', 'http/1.1'])
                self.logger.info("OpenSSL support npn")
                self.support_alpn_npn = "npn"
            except Exception as e:
                # xlog.exception("set_npn_select_callback:%r", e)
                self.logger.info("OpenSSL dont't support npn/alpn, no HTTP/2 supported.")
                pass

    @staticmethod
    def npn_select_callback(conn, protocols):
        # self.logger.debug("npn protocl:%s", ";".join(protocols))
        if b"h2" in protocols:
            conn.protos = "h2"
            return b"h2"
        else:
            return b"http/1.1"

    @staticmethod
    def supported_protocol():
        if hasattr(ssl, "HAS_TLSv1_3") and ssl.HAS_TLSv1_3:
            ssl_version = "TLSv1_3"
        elif hasattr(ssl, "HAS_TLSv1_2") and ssl.HAS_TLSv1_2:
            ssl_version = "TLSv1_2"
        elif hasattr(ssl, "HAS_TLSv1_1") and ssl.HAS_TLSv1_1:
            ssl_version = "TLSv1_1"
        elif hasattr(ssl, "HAS_SSLv3") and ssl.HAS_SSLv3:
            ssl_version = "SSLv3"
        elif hasattr(ssl, "HAS_SSLv2") and ssl.HAS_SSLv2:
            ssl_version = "SSLv2"
        else:
            ssl_version = "SSLv1"

        return ssl_version

    def set_ca(self, ca_certs):
        if sys.version_info[0] == 3:
            try:
                if ca_certs:
                    self.context.load_verify_locations(cafile=os.path.abspath(ca_certs))
                    self.context.verify_mode = ssl.CERT_REQUIRED
                else:
                    self.context.verify_mode = ssl.CERT_NONE
            except Exception as e:
                self.logger.debug("set_ca fail:%r", e)
        else:
            if ca_certs:
                self.context.load_verify_locations(os.path.abspath(ca_certs))
                self.context.set_verify(OpenSSL.SSL.VERIFY_PEER, lambda c, x, e, d, ok: ok)
            else:
                self.context.set_verify(OpenSSL.SSL.VERIFY_NONE, lambda c, x, e, d, ok: ok)


from pyasn1.codec.der.decoder import decode
from pyasn1.error import PyAsn1Error
from pyasn1.type import univ, constraint, char, namedtype, tag


class _GeneralName(univ.Choice):
    # We are only interested in dNSNames. We use a default handler to ignore
    # other types.
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('dNSName', char.IA5String().subtype(
                implicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 2)
            )
        ),
    )


class _GeneralNames(univ.SequenceOf):
    componentType = _GeneralName()
    sizeSpec = univ.SequenceOf.sizeSpec + constraint.ValueSizeConstraint(1, 1024)


class SSLCert:
    def __init__(self, cert):
        """
            Returns a (common name, [subject alternative names]) tuple.
        """
        self.x509 = cert

    # @classmethod
    # def from_pem(klass, txt):
    #     x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, txt)
    #     return klass(x509)

    # @classmethod
    # def from_der(klass, der):
    #     pem = ssl.DER_cert_to_PEM_cert(der)
    #     return klass.from_pem(pem)

    # def to_pem(self):
    #     return OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, self.x509)

    def digest(self, name):
        return self.x509.digest(name)

    @property
    def issuer(self):
        return self.x509.get_issuer().get_components()

    @property
    def notbefore(self):
        t = self.x509.get_notBefore()
        return datetime.datetime.strptime(t, "%Y%m%d%H%M%SZ")

    @property
    def notafter(self):
        t = self.x509.get_notAfter()
        return datetime.datetime.strptime(t, "%Y%m%d%H%M%SZ")

    @property
    def has_expired(self):
        return self.x509.has_expired()

    @property
    def subject(self):
        return self.x509.get_subject().get_components()

    @property
    def serial(self):
        return self.x509.get_serial_number()

    # @property
    # def keyinfo(self):
    #     pk = self.x509.get_pubkey()
    #     types = {
    #         OpenSSL.crypto.TYPE_RSA: "RSA",
    #         OpenSSL.crypto.TYPE_DSA: "DSA",
    #     }
    #     return (
    #         types.get(pk.type(), "UNKNOWN"),
    #         pk.bits()
    #     )

    @property
    def cn(self):
        c = None
        for i in self.subject:
            if i[0] == "CN":
                c = i[1]
        return c

    @property
    def altnames(self):
        altnames = []
        for i in range(self.x509.get_extension_count()):
            ext = self.x509.get_extension(i)
            if ext.get_short_name() == "subjectAltName":
                try:
                    dec = decode(ext.get_data(), asn1Spec=_GeneralNames())
                except PyAsn1Error:
                    continue
                for i in dec[0]:
                    altnames.append(i[0].asOctets())
        return altnames
