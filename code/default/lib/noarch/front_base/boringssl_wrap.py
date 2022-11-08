# this wrap has a close callback.
# Which is used by  ip manager
#  ip manager keep a connection number counter for every ip.


import socket

import utils

from boringssl import lib as bssl, ffi


class SSLConnection(object):
    BIO_CLOSE = 1

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

        fn = self._sock.fileno()
        bio = bssl.BIO_new_socket(fn, self.BIO_CLOSE)

        self._connection = bssl.SSL_new(self._context.ctx)

        if self.sni:
            bssl.SSL_set_tlsext_host_name(self._connection, self.sni)

        bssl.SSL_set_bio(self._connection, bio, bio)

        if self._context.support_http2:
            proto = b"h2"
            setting = b"h2"
            ret = bssl.SSL_add_application_settings(self._connection,
                                                    proto, len(proto),
                                                    setting, len(setting))
            if ret != 1:
                error = bssl.SSL_get_error(self._connection, ret)
                raise socket.error("set alpn fail, error:%s" % error)

        self._sock.setblocking(True)
        ret = bssl.SSL_connect(self._connection)
        if ret == 1:
            return

        error = bssl.SSL_get_error(self._connection, ret)
        raise socket.error("SSL_connect fail: %s" % error)

    def do_handshake(self):
        ret = bssl.SSL_do_handshake(self._connection)
        if ret == 1:
            return

        error = bssl.SSL_get_error(self._connection, ret)
        raise socket.error("do_handshake fail: %s" % error)

    def is_support_h2(self):
        out_data_pp = ffi.new("uint8_t**", ffi.NULL)
        out_len_p = ffi.new("unsigned*")
        bssl.SSL_get0_alpn_selected(self._connection, out_data_pp, out_len_p)

        if out_len_p[0] == 0:
            return False

        if ffi.string(out_data_pp[0]) == b"h2":
            return True

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
            self.close()

    def get_cert(self):
        if self.peer_cert:
            return self.peer_cert

        def x509_name_to_string(xname):
            line = bssl.X509_NAME_oneline(xname, ffi.NULL, 0)
            return ffi.string(line)

        try:
            cert = bssl.SSL_get_peer_certificate(self._connection)
            alt_names_p = bssl.get_alt_names(cert)
            alt_names = utils.to_str(ffi.string(alt_names_p))
            subject = x509_name_to_string(bssl.X509_get_subject_name(cert))
            issuer = x509_name_to_string(bssl.X509_get_issuer_name(cert))
            altName = alt_names.split(";")
        except Exception as e:
            subject = ""
            issuer = ""
            altName = []

        self.peer_cert = {
            "cert": subject,
            "issuer_commonname": issuer,
            "commonName": "",
            "altName": altName
        }

        return self.peer_cert

    def send(self, data, flags=0):
        try:
            ret = bssl.SSL_write(self._connection, data, len(data))
            return ret
        except Exception as e:
            self.logger.exception("ssl send:%r", e)
            raise e

    def recv(self, bufsiz, flags=0):
        buf = bytes(bufsiz)
        n = bssl.SSL_read(self._connection, buf, bufsiz)
        if n <= 0:
            e = socket.error(2)
            e.errno = 2
            raise e

        dat = buf[:n]
        return dat

    def recv_into(self, buf, nbytes=None):
        if not nbytes:
            nbytes = len(buf)

        b = ffi.from_buffer(buf)
        n = bssl.SSL_read(self._connection, b, nbytes)
        if n <= 0:
            return None

        return n

    def read(self, bufsiz, flags=0):
        return self.recv(bufsiz, flags)

    def write(self, buf, flags=0):
        return self.send(buf, flags)

    def close(self):
        if self._makefile_refs < 1:
            self.running = False
            if not self.socket_closed:

                bssl.SSL_shutdown(self._connection)
                bssl.SSL_free(self._connection)
                self._connection = None

                self._sock = None
                self.socket_closed = True
                if self._on_close:
                    self._on_close(self.ip_str)
        else:
            self._makefile_refs -= 1

    def settimeout(self, t):
        if not self.running:
            return

        if self.timeout != t:
            # self._sock.settimeout(t)
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

        method = bssl.TLS_method()
        self.ctx = bssl.SSL_CTX_new(method)
        self.support_http2 = support_http2
        bssl.SSL_CTX_set_grease_enabled(self.ctx, 1)

        cmd = b"ALL:!aPSK:!ECDSA+SHA1:!3DES"
        bssl.SSL_CTX_set_cipher_list(self.ctx, cmd)

        if support_http2:
            alpn = b""
            for proto in [b"h2", b"http/1.1"]:
                proto_len = len(proto)
                alpn += proto_len.to_bytes(1, 'big') + proto
            bssl.SSL_CTX_set_alpn_protos(self.ctx, alpn, len(alpn))
        bssl.SSL_CTX_enable_ocsp_stapling(self.ctx)
        bssl.SSL_CTX_enable_signed_cert_timestamps(self.ctx)

        # SSL_SIGN_ECDSA_SECP256R1_SHA256, SSL_SIGN_RSA_PSS_RSAE_SHA256,
        # SSL_SIGN_RSA_PKCS1_SHA256,       SSL_SIGN_ECDSA_SECP384R1_SHA384,
        # SSL_SIGN_RSA_PSS_RSAE_SHA384,    SSL_SIGN_RSA_PKCS1_SHA384,
        # SSL_SIGN_RSA_PSS_RSAE_SHA512,    SSL_SIGN_RSA_PKCS1_SHA512,
        algs = [0x0403, 0x0804, 0x0401, 0x0503, 0x0805, 0x0501, 0x0806, 0x0601]
        algs_buf = ffi.new("uint16_t[%s]" % (len(algs)))
        i = 0
        for alg in algs:
            algs_buf[i] = alg
            i += 1
        cdata_ptr = ffi.cast("uint16_t *", algs_buf)
        bssl.SSL_CTX_set_verify_algorithm_prefs(self.ctx, cdata_ptr, len(algs))

        bssl.SSL_CTX_set_min_proto_version(self.ctx, 0x0303)

        bssl.SetCompression(self.ctx)

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
