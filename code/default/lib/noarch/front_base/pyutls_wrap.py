# this wrap has a close callback.
# Which is used by  ip manager
#  ip manager keep a connection number counter for every ip.

import socket
import threading
import codecs
from asn1crypto.x509 import Certificate

# import selectors2 as selectors
import utils

# from boringssl import lib as bssl, ffi

from pyutls import ( 

    #  ssl connection functions
    new_ssl_connection,
    ssl_connection_write,
    ssl_connection_read,
    ssl_connection_close,
    ssl_connection_h2_support,
    ssl_connection_closed,
    ssl_connection_do_handshake,
    ssl_connection_leaf_cert,
    
    #  context functions
    new_ssl_context,
    new_ssl_context_from_bytes,

    # others functions
    close_go_handle
    )

class HandleObject:
    _handle = 0
    def __init__(self, handle):
        self._handle = handle
    
    @property
    def  handle(self):
        return self._handle

    def __del__(self):
        if self.handle != 0:
            close_go_handle(self.handle)

    def run(self, fn, *args, **kwargs):
        return fn(self.handle, *args, **kwargs)

class SSLContext(HandleObject):
    ALLOW_BLUNT_MIMICRY = True
    ALWAYS_PAD = False
    def __init__(self, logger, ca_certs=None, cipher_suites=None, support_http2=True, protocol=None, handle=None):
        if handle:
            self.logger = logger
            # self.handle = handle
            # super(SSLContext, self).__init__(handle)
            HandleObject.__init__(self, handle)
            return

        self.logger = logger
        self.context = self
        self.support_http2 = support_http2
        tls_ver = 772
        handle = new_ssl_context(tls_ver, support_http2)
        HandleObject.__init__(self, handle)
    
    @classmethod
    def from_bytes(cls, logger, raw_bytes : bytes=None, hex:str=None):
        if hex:
            raw_bytes = codecs.decode(hex, "hex")
        handle = new_ssl_context_from_bytes(cls.ALLOW_BLUNT_MIMICRY, cls.ALWAYS_PAD, raw_bytes)
        obj  = cls(logger, handle=handle)
        return obj


    def supported_protocol(self):
        return "TLS 1.3"

    def support_alpn_npn(self):
        return "alpn"



class SSLConnection(HandleObject):
    CERT_DELIM = b"|!|!|"
    @staticmethod
    def parse_ip(ip_str):
        ip, port = utils.get_ip_port(ip_str)
        ip = ip.decode('utf-8')
        ip_split = ip.split(':')
        if len(ip_split) > 1:
            ip = '['+ ':'.join(ip_split[:5]) + ']'
        return f'{ip}:{port}'


    socket_closed = False
    def __init__(self, context : SSLContext, sock, ip_str=None, sni=None, on_close=None):
        self._lock = threading.Lock()
        self._context = context
        self._sock = sock
        self.ip_str = self.parse_ip(ip_str)
        self.sni = sni.decode('utf-8')
        self._makefile_refs = 0
        self._on_close = on_close
        self.peer_cert = None
        self.socket_closed = False
        # self._fileno = self._sock.fileno()
        # self.timeout = self._sock.gettimeout() or 0.1
        self.running = True
        self._connection = None
        self.wrap()

        # self.select2 = selectors.DefaultSelector()
        # self.select2.register(sock, selectors.EVENT_WRITE)

    def wrap(self):
        # try:
        #     self._sock.connect((ip, port))
        # except Exception as e:
        #     raise socket.error('conn %s fail, sni:%s, e:%r' % (self.ip_str, self.sni, e))

        # self._sock.setblocking(True)

        # fn = self._fileno
        # bio = bssl.BSSL_BIO_new_socket(fn, self.BIO_CLOSE)

        # self._connection = bssl.BSSL_SSL_new(self._context.ctx)

        # if self.sni:
        #     bssl.BSSL_SSL_set_tlsext_host_name(self._connection, utils.to_bytes(self.sni))

        # bssl.BSSL_SSL_set_bio(self._connection, bio, bio)
        print(self.ip_str)
        handle, fd = new_ssl_connection(self._context.handle, self.ip_str, self.sni)
        self._fileno = fd
        # print("handle =>", handle)
        HandleObject.__init__(self, handle)

    @property
    def is_closed(self):
        if not self.socket_closed:
            self.socket_closed = ssl_connection_closed(self.handle)
        return self.socket_closed


    def do_handshake(self):
        return self.run(ssl_connection_do_handshake)

    def is_support_h2(self):
        return ssl_connection_h2_support(self.handle)

    def setblocking(self, block):
        self._context.logger.debug("%s setblocking: %d", self.ip_str, block)
        # self._sock.setblocking(block)
        # raise NotImplementedError()
        # already non blocking
        return

    # def __getattr__(self, attr):
    #     if attr in ('is_support_h2', "_on_close", '_context', '_sock', '_connection', '_makefile_refs',
    #                   'sni', 'wrap', 'socket_closed'):
    #         return getattr(self, attr)

    #     elif hasattr(self._connection, attr):
    #         return getattr(self._connection, attr)


    def get_cert(self):
        if self.peer_cert:
            return self.peer_cert
        certs = self.get_peercertificates()
        self._context.logger.debug("Got %d certificates, using leaf cert with index 0", len(certs))

        cert = certs[0]
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

    def get_peercertificates(self):
        cert_bytes = self.run(ssl_connection_leaf_cert)
        cert_arr = cert_bytes.split(self.CERT_DELIM)
        return tuple(map(Certificate.load, cert_arr))



    def send(self, data, flags=0):
        return ssl_connection_write(self.handle, data)

    def recv(self, bufsiz, flags=0):
        return ssl_connection_read(self.handle, bufsiz)

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

    def close(self):
        ret = None
        with self._lock:
            self.running = False
            if not self.socket_closed:
                if self.handle:
                    ret = ssl_connection_close(self.handle)

                self.socket_closed = True
                if self._on_close:
                    self._on_close(self.ip_str)
        return ret

    def __del__(self):
        self.close()

    def settimeout(self, t):
        if not self.running:
            return

        # if self.timeout != t:
        #     # self._context.logger.debug("settimeout %d", t)
        #     self._sock.settimeout(t)
        #     self.timeout = t

    def makefile(self, mode='r', bufsize=-1):
        self._makefile_refs += 1
        return socket._fileobject(self, mode, bufsize, close=True)

    def fileno(self):
        return self._fileno


class SSLCert:
    def __init__(self, cert):
        """
            Returns a (common name, [subject alternative names]) tuple.
        """
        self.x509 = cert
