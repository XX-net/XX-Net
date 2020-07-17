
import socket
import struct
import time

import socks
import utils
from . import openssl_wrap


class ConnectCreator(object):
    def __init__(self, logger, config, openssl_context, host_manager,
                 timeout=5, debug=False,
                 check_cert=None):
        self.logger = logger
        self.config = config
        self.openssl_context = openssl_context
        self.host_manager = host_manager
        self.timeout = timeout
        self.debug = debug or self.config.show_state_debug
        self.peer_cert = None
        if check_cert:
            self.check_cert = check_cert
        self.update_config()

        self.connect_force_http1 = self.config.connect_force_http1
        self.connect_force_http2 = self.config.connect_force_http2

    def update_config(self):
        if int(self.config.PROXY_ENABLE):

            if self.config.PROXY_TYPE == "HTTP":
                proxy_type = socks.HTTP
            elif self.config.PROXY_TYPE == "SOCKS4":
                proxy_type = socks.SOCKS4
            elif self.config.PROXY_TYPE == "SOCKS5":
                proxy_type = socks.SOCKS5
            else:
                self.logger.error("proxy type %s unknown, disable proxy", self.config.PROXY_TYPE)
                raise Exception()

            socks.set_default_proxy(proxy_type, self.config.PROXY_HOST, self.config.PROXY_PORT,
                                    self.config.PROXY_USER,
                                    self.config.PROXY_PASSWD)

    def connect_ssl(self, ip_str, sni=b"", close_cb=None):
        if sni:
            host = sni
        else:
            sni, host = self.host_manager.get_sni_host(ip_str)

        host = str(host)
        if isinstance(sni, str):
            sni = bytes(sni, encoding='ascii')
        ip, port = utils.get_ip_port(ip_str)
        if isinstance(ip, str):
            ip = bytes(ip, encoding='ascii')

        if int(self.config.PROXY_ENABLE):
            sock = socks.socksocket(socket.AF_INET if b':' not in ip else socket.AF_INET6)
        else:
            sock = socket.socket(socket.AF_INET if b':' not in ip else socket.AF_INET6)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # set struct linger{l_onoff=1,l_linger=0} to avoid 10048 socket error
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        # resize socket recv buffer ->64 above to improve browser releated application performance
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.config.connect_receive_buffer)
        sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
        sock.settimeout(self.timeout)

        ssl_sock = openssl_wrap.SSLConnection(self.openssl_context.context, sock, ip_str, on_close=close_cb)

        if sni:
            if self.debug:
                self.logger.debug("sni:%s", sni)

            try:
                ssl_sock.set_tlsext_host_name(sni)
            except Exception as e:
                self.logger.exception("set_tlsext_host_name %s except:%r", sni, e)
                pass

        ssl_sock.sni = utils.to_str(sni)

        time_begin = time.time()
        ip_port = (utils.to_str(ip), port)

        try:
            ssl_sock.connect(ip_port)
            time_connected = time.time()
            ssl_sock.do_handshake()
        except Exception as e:
            raise socket.error('conn fail, sni:%s, top:%s e:%r' % (sni, host, e))

        if self.connect_force_http1:
            ssl_sock.h2 = False
        elif self.connect_force_http2:
            ssl_sock.h2 = True
        else:
            try:
                if ssl_sock.selected_alpn_protocol() == "h2" or ssl_sock.selected_npn_protocol() == "h2":
                    ssl_sock.h2 = True
                else:
                    ssl_sock.h2 = False
            except Exception as e:
                self.logger.exception("alpn:%r", e)
                ssl_sock.h2 = False

        time_handshaked = time.time()

        self.check_cert(ssl_sock)

        connect_time = int((time_connected - time_begin) * 1000)
        handshake_time = int((time_handshaked - time_begin) * 1000)
        ssl_sock.fd = sock.fileno()
        ssl_sock.create_time = time_begin
        ssl_sock.connect_time = connect_time
        ssl_sock.handshake_time = handshake_time
        ssl_sock.last_use_time = time_handshaked
        ssl_sock.host = host
        ssl_sock.received_size = 0

        return ssl_sock

    def check_cert(self, ssl_sock):
        try:
            peer_cert = ssl_sock.get_cert()
            if self.debug:
                self.logger.debug("cert:%r", peer_cert)

            if self.config.check_commonname:
                if not peer_cert["issuer_commonname"].startswith(self.config.check_commonname):
                    raise socket.error(' certificate is issued by %r' % (peer_cert["issuer_commonname"]))

            if isinstance(self.config.check_sni, str):
                if self.config.check_sni not in peer_cert["altName"]:
                    raise socket.error('check sni fail:%s, alt_names:%s' % (self.config.check_sni, peer_cert["altName"]))
            elif self.config.check_sni:
                if not ssl_sock.sni.endswith(peer_cert["altName"]):
                    raise socket.error('check sni:%s fail, alt_names:%s' % (ssl_sock.sni, peer_cert["altName"]))
        except Exception as e:
            self.logger.exception("check_cert %r", e)
