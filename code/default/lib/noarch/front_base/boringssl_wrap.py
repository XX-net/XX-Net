# this wrap has a close callback.
# Which is used by  ip manager
#  ip manager keep a connection number counter for every ip.

import socket
import threading

import selectors2 as selectors
import utils

from boringssl import lib as bssl, ffi


class SSLConnection(object):
    BIO_CLOSE = 1

    def __init__(self, context, sock, ip_str=None, sni=None, on_close=None):
        self._lock = threading.Lock()
        self._context = context
        self._sock = sock
        self._fileno = self._sock.fileno()
        # self._context.logger.debug("sock %s init fd:%d", ip_str, self._fileno)
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

        self.select2 = selectors.DefaultSelector()
        self.select2.register(sock, selectors.EVENT_WRITE)

    def wrap(self):
        ip, port = utils.get_ip_port(self.ip_str)
        self.ip = ip
        if isinstance(ip, str):
            ip = utils.to_bytes(ip)

        try:
            self._sock.connect((ip, port))
        except Exception as e:
            raise socket.error('conn %s fail, sni:%s, e:%r' % (self.ip_str, self.sni, e))

        self._sock.setblocking(True)

        fn = self._fileno
        bio = bssl.BSSL_BIO_new_socket(fn, self.BIO_CLOSE)

        self._connection = bssl.BSSL_SSL_new(self._context.ctx)

        if self.sni:
            bssl.BSSL_SSL_set_tlsext_host_name(self._connection, utils.to_bytes(self.sni))

        bssl.BSSL_SSL_set_bio(self._connection, bio, bio)

        if self._context.support_http2:
            proto = b"h2"
            setting = b"h2"
            ret = bssl.BSSL_SSL_add_application_settings(self._connection,
                                                    proto, len(proto),
                                                    setting, len(setting))
            if ret != 1:
                error = bssl.BSSL_SSL_get_error(self._connection, ret)
                raise socket.error("set alpn fail, error:%s" % error)

        ret = bssl.BSSL_SSL_connect(self._connection)
        if ret == 1:
            return

        error = bssl.BSSL_SSL_get_error(self._connection, ret)
        if error == 1:
            p = ffi.new("char[]", b"hello, worldhello, worldhello, worldhello, worldhello, world")  # p is a 'char *'
            q = ffi.new("char **", p)  # q is a 'char **'
            line_no = 0
            line_no_p = ffi.new("int *", line_no)
            error = bssl.BSSL_ERR_get_error_line(q, line_no_p)
            filename = ffi.string(q[0])
            # self._context.logger.error("error:%d file:%s, line:%s", error, filename, line_no_p[0])
            raise socket.error("SSL_connect fail: %s, file:%s, line:%d, sni:%s" %
                               (error, filename, line_no_p[0], self.sni))
        else:
            raise socket.error("SSL_connect fail: %s, sni:%s" % (error, self.sni))

    def do_handshake(self):
        if not self._connection:
            raise socket.error("do_handshake fail: not connected")

        ret = bssl.BSSL_SSL_do_handshake(self._connection)
        if ret == 1:
            return

        error = bssl.BSSL_SSL_get_error(self._connection, ret)
        raise socket.error("do_handshake fail: %s" % error)

    def is_support_h2(self):
        if not self._connection:
            return False

        out_data_pp = ffi.new("uint8_t**", ffi.NULL)
        out_len_p = ffi.new("unsigned*")
        bssl.BSSL_SSL_get0_alpn_selected(self._connection, out_data_pp, out_len_p)

        proto_len = out_len_p[0]
        if proto_len == 0:
            return False

        if ffi.string(out_data_pp[0])[:proto_len] == b"h2":
            return True

        return False

    def setblocking(self, block):
        self._context.logger.debug("%s setblocking: %d", self.ip_str, block)
        self._sock.setblocking(block)

    def __getattr__(self, attr):
        if attr in ('is_support_h2', "_on_close", '_context', '_sock', '_connection', '_makefile_refs',
                      'sni', 'wrap', 'socket_closed'):
            return getattr(self, attr)

        elif hasattr(self._connection, attr):
            return getattr(self._connection, attr)

    def get_cert(self):
        if self.peer_cert:
            return self.peer_cert

        def x509_name_to_string(xname):
            line = bssl.BSSL_X509_NAME_oneline(xname, ffi.NULL, 0)
            return ffi.string(line)

        with self._lock:
            if self._connection:
                try:
                    cert = bssl.BSSL_SSL_get_peer_certificate(self._connection)
                    if cert == ffi.NULL:
                        raise Exception("get cert failed")

                    alt_names_p = bssl.get_alt_names(cert)
                    if alt_names_p == ffi.NULL:
                        raise Exception("get alt_names failed")

                    alt_names = utils.to_str(ffi.string(alt_names_p))
                    bssl.free(alt_names_p)

                    subject = x509_name_to_string(bssl.BSSL_X509_get_subject_name(cert))
                    issuer = x509_name_to_string(bssl.BSSL_X509_get_issuer_name(cert))
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
        with self._lock:
            if not self._connection:
                e = socket.error(5)
                e.errno = 5
                raise e

            try:
                while True:
                    # self._context.logger.debug("%s send %d ", self.ip_str, len(data))
                    ret = bssl.BSSL_SSL_write(self._connection, data, len(data))
                    if ret <= 0:
                        errno = bssl.BSSL_SSL_get_error(self._connection, ret)
                        if errno not in [2, 3, ]:
                            # self._context.logger.warn("send n:%d errno: %d ip:%s", ret, errno, self.ip_str)
                            e = socket.error(errno)
                            e.errno = errno
                            raise e
                        else:
                            # self._context.logger.debug("send n:%d errno: %d ip:%s", ret, errno, self.ip_str)
                            self.select2.select(timeout=self.timeout)
                            continue
                    else:
                        # self._context.logger.debug("send:%d ip:%s", ret, self.ip_str)
                        break

                return ret
            except OSError:
                self._context.logger.warn("ssl send:%r", e)
                raise e
            except Exception as e:
                self._context.logger.exception("ssl send:%r", e)
                raise e

    def recv(self, bufsiz, flags=0):
        with self._lock:
            if not self._connection:
                e = socket.error(2)
                e.errno = 5
                raise e

            bufsiz = min(16*1024, bufsiz)
            buf = bytes(bufsiz)
            # t0 = time.time()
            n = bssl.BSSL_SSL_read(self._connection, buf, bufsiz)
            # t2 = time.time()
            # self._context.logger.debug("%s read: %d t:%f", self.ip_str, n, t2 - t0)
            if n <= 0:
                errno = bssl.BSSL_SSL_get_error(self._connection, n)
                # self._context.logger.warn("recv n:%d errno: %d ip:%s", n, errno, self.ip_str)
                e = socket.error(errno)
                e.errno = errno
                raise e

            dat = bytes(buf[:n])
            return dat

    def recv_into(self, buf, nbytes=None):
        if not nbytes:
            nbytes = len(buf)

        dat = self.recv(nbytes)
        n = len(dat)
        buf[:n] = dat
        return n

    def read(self, bufsiz, flags=0):
        return self.recv(bufsiz, flags)

    def write(self, buf, flags=0):
        return self.send(buf, flags)

    def close(self, reason=""):
        with self._lock:
            self.running = False
            if not self.socket_closed:
                if self._connection:
                    res = bssl.BSSL_SSL_shutdown(self._connection)
                    # res == 0: close_notify sent but not recv, means you need to call SSL_shutdown again if you want a full bidirectional shutdown.
                    # res == 1: success, mean you previously received a close_notify alert from the other peer, and you're totally done
                    # res == -1: failed
                    # self._context.logger.debug("sock %s SSL_shutdown fd:%d res:%d", self.ip_str, self._fileno, res)

                    if res < 0:
                        error = bssl.BSSL_SSL_get_error(self._connection, res)
                        # self._context.logger.debug("sock %s shutdown fd:%d error:%d", self.ip_str, self._fileno, error)
                        if error == 1:
                            p = ffi.new("char[]",
                                        b"hello, worldhello, worldhello, worldhello, worldhello, world")  # p is a 'char *'
                            q = ffi.new("char **", p)  # q is a 'char **'
                            line_no = 0
                            line_no_p = ffi.new("int *", line_no)
                            error = bssl.BSSL_ERR_get_error_line(q, line_no_p)
                            filename = ffi.string(q[0])
                            # self._context.logger.error("error:%d file:%s, line:%s", error, filename, line_no_p[0])
                            self._context.logger.debug("sock %s shutdown error: %s, file:%s, line:%d, sni:%s" %
                                               (self.ip_str, error, filename, line_no_p[0], self.sni))
                        else:
                            self._context.logger.debug("sock %s shutdown error:%s" % (self.ip_str, error))

                    bssl.BSSL_SSL_free(self._connection)
                    self._connection = None

                if self._sock:
                    try:
                        self._sock.close()
                        # self._context.logger.debug("sock %s sock_close fd:%d", self.ip_str, self._fileno)
                    except Exception as e:
                        # self._context.logger.debug("sock %s sock_close fd:%d e:%r", self.ip_str, self._fileno, e)
                        pass
                    self._sock = None

                self.socket_closed = True

                if self._on_close:
                    self._on_close(self.ip_str, self.sni, reason=reason)
                    self._on_close = None

    def __del__(self):
        self.close()

    def settimeout(self, t):
        if not self.running:
            return

        if self.timeout != t:
            # self._context.logger.debug("settimeout %d", t)
            self._sock.settimeout(t)
            self.timeout = t

    def makefile(self, mode='r', bufsize=-1):
        self._makefile_refs += 1
        return socket._fileobject(self, mode, bufsize, close=True)

    def fileno(self):
        return self._fileno


class SSLContext(object):
    def __init__(self, logger, ca_certs=None, cipher_suites=None, support_http2=True, protocol=None):
        self.logger = logger
        self.context = self

        method = bssl.BSSL_TLS_method()
        self.ctx = bssl.BSSL_SSL_CTX_new(method)
        self.support_http2 = support_http2
        bssl.BSSL_SSL_CTX_set_grease_enabled(self.ctx, 1)

        cmd = b"ALL:!aPSK:!ECDSA+SHA1:!3DES"
        bssl.BSSL_SSL_CTX_set_cipher_list(self.ctx, cmd)

        if support_http2:
            alpn = b""
            for proto in [b"h2", b"http/1.1"]:
                proto_len = len(proto)
                alpn += proto_len.to_bytes(1, 'big') + proto
            bssl.BSSL_SSL_CTX_set_alpn_protos(self.ctx, alpn, len(alpn))
        bssl.BSSL_SSL_CTX_enable_ocsp_stapling(self.ctx)
        bssl.BSSL_SSL_CTX_enable_signed_cert_timestamps(self.ctx)

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
        bssl.BSSL_SSL_CTX_set_verify_algorithm_prefs(self.ctx, cdata_ptr, len(algs))

        bssl.BSSL_SSL_CTX_set_min_proto_version(self.ctx, 0x0303)

        try:
            bssl.BSSL_SSL_CTX_set_num_tickets(self.ctx, 0)
            bssl.BSSL_SSL_CTX_set_permute_extensions(self.ctx, 1)
        except:
            self.logger.info("boringsssl not support permute extension")

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
