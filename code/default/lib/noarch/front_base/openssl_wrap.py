
# OpenSSL is more stable then ssl
# but OpenSSL is different then ssl, so need a wrapper

# this wrap has a close callback.
# Which is used by  ip manager
#  ip manager keep a connection number counter for every ip.

# the wrap is used to keep some attribute like ip_str/appid for ssl

import os

import datetime
import ssl

import utils

# This is a throwaway variable to deal with a python bug
throwaway = datetime.datetime.strptime('20110101','%Y%m%d')


class SSLConnection():
    def __init__(self, context, sock, ip_str=None, server_hostname=None, on_close=None):
        self._connection = context.wrap_socket(sock, server_hostname=server_hostname, do_handshake_on_connect=False)
        self._context = context
        self._sock = sock
        self.ip_str = ip_str
        self._on_close = on_close
        self.peer_cert = None
        self.socket_closed = False

    def __getattr__(self, attr):
        if attr == "socket_closed":
            # work around in case close before finished init.
            return True

        if hasattr(self, "_connection") and hasattr(self._connection, attr):
            return getattr(self._connection, attr)
        else:
            return None

    def __del__(self):
        if not self.socket_closed:
            self._connection.close()
            self.socket_closed = True
            if self._on_close:
                self._on_close(self.ip_str)

    def set_tlsext_host_name(self, hostname):
        self._connection.server_hostname = utils.to_str(hostname)

    def get_cert(self):
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
        for kv in cert["issuer"]:
            k, v = kv[0]
            if k == 'commonName':
                self.peer_cert["issuer_commonname"] = v

        for kv in cert["subject"]:
            k, v = kv[0]
            if k == 'commonName':
                self.peer_cert["commonName"] = v

        for k, v in cert["subjectAltName"]:
            self.peer_cert["altName"].append(v)
        self.peer_cert["altName"] = tuple(self.peer_cert["altName"])

        return self.peer_cert


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
                # self.logger.exception("set_alpn_protos:%r", e)
                pass

            try:
                self.context.set_npn_protocols(['h2', 'http/1.1'])
                self.logger.info("OpenSSL support npn")
                self.support_alpn_npn = "npn"
            except Exception as e:
                #xlog.exception("set_npn_select_callback:%r", e)
                self.logger.info("OpenSSL dont't support npn/alpn, no HTTP/2 supported.")
                pass

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
        try:
            if ca_certs:
                self.context.load_verify_locations(cafile=os.path.abspath(ca_certs))
                self.context.verify_mode = ssl.CERT_REQUIRED
            else:
                self.context.verify_mode = ssl.CERT_NONE
        except Exception as e:
            self.logger.debug("set_ca fail:%r", e)
            return
