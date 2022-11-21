
import socket

from boringssl import lib as bssl, ffi


class SSLConnection(object):
    BIO_CLOSE = 1

    def __init__(self, context, sock, ip_str=None, sni=None, on_close=None):
        self._context = context
        self._sock = sock
        # self.ip_str = utils.to_bytes(ip_str)
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
        fn = self._sock.fileno()
        bio = bssl.BIO_new_socket(fn, self.BIO_CLOSE)

        self._connection = bssl.SSL_new(self._context.ctx)

        bssl.SSL_set_tlsext_host_name(self._connection, self.sni)

        bssl.SSL_set_bio(self._connection, bio, bio)

        if self._context.enable_h2:
            proto = b"h2"
            setting = b"h2"
            ret = bssl.SSL_add_application_settings(self._connection,
                                                    proto, len(proto),
                                                    setting, len(setting))
            # print(ret)

        ret = bssl.SSL_connect(self._connection)

    def send(self, data):
        bssl.SSL_write(self._connection, data, len(data))

    def recv(self, size):
        buf = bytes(size)
        n = bssl.SSL_read(self._connection, buf, size)
        if n <= 0:
            return None

        dat = buf[:n]
        return dat

    def close(self):
        print("close")
        bssl.SSL_shutdown(self._connection)
        bssl.SSL_free(self._connection)
        self._connection = None

    def __del__(self):
        self.close()


class SSLContext(object):
    def __init__(self, enable_h2=True):
        method = bssl.TLS_method()
        self.ctx = bssl.SSL_CTX_new(method)
        self.enable_h2 = enable_h2
        bssl.SSL_CTX_set_grease_enabled(self.ctx, 1)

        cmd = b"ALL:!aPSK:!ECDSA+SHA1:!3DES"
        bssl.SSL_CTX_set_cipher_list(self.ctx, cmd)

        if enable_h2:
            alpn = b""
            for proto in [b"h2", b"http/1.1"]:
                proto_len = len(proto)
                alpn += proto_len.to_bytes(1, 'big') + proto
            bssl.SSL_CTX_set_alpn_protos(self.ctx, alpn, len(alpn))
        bssl.SSL_CTX_enable_ocsp_stapling(self.ctx)
        bssl.SSL_CTX_enable_signed_cert_timestamps(self.ctx)

        #SSL_SIGN_ECDSA_SECP256R1_SHA256, SSL_SIGN_RSA_PSS_RSAE_SHA256,
        #SSL_SIGN_RSA_PKCS1_SHA256,       SSL_SIGN_ECDSA_SECP384R1_SHA384,
        #SSL_SIGN_RSA_PSS_RSAE_SHA384,    SSL_SIGN_RSA_PKCS1_SHA384,
        #SSL_SIGN_RSA_PSS_RSAE_SHA512,    SSL_SIGN_RSA_PKCS1_SHA512,
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


def round():
    ip = "127.0.0.1"
    host = "agentnobody.pics"
    sock = socket.socket(socket.AF_INET if ':' not in ip else socket.AF_INET6)
    sock.settimeout(3)
    try:
        sock.connect((ip, 443))
    except Exception as e:
        print("connnect fail")
        return

    context = SSLContext(enable_h2=False)
    connection = SSLConnection(context, sock, sni=host.encode("utf-8"))
    sock.setblocking(True)
    # connection.settimeout(10)
    print("connected")

    connection.send(b"GET / HTTP/1.0\r\n")
    connection.send(b"Host: %s\r\n" % host.encode("utf-8"))
    connection.send(b"User-Agent: curl\r\n")
    connection.send(b"Accept: */*\r\n")
    connection.send(b"\r\n")

    while True:
        try:
            r = connection.recv(10240)
            if not r:
                break
            print(r.decode("utf-8"))
        except socket.timeout:
            break
        except Exception as e:
            break


def loop():
    while True:
        round()


loop()
