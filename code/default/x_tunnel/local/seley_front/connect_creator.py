import socket
import struct
import time

import socks
import utils


from front_base.connect_creator import ConnectCreator as ConnectCreatorBase
from . import rc4_wrap


class ConnectCreator(ConnectCreatorBase):

    def connect_ssl(self, ip_str, sni, host, close_cb=None):
        ip_str = utils.to_str(ip_str)

        if self.debug:
            self.logger.debug("connect ip:%s sni:%s host:%s", ip_str, sni, host)

        ip, port = utils.get_ip_port(ip_str)
        if isinstance(ip, str):
            ip = utils.to_bytes(ip)

        if not utils.check_ip_valid(ip):
            try:
                info = socket.getaddrinfo(ip, port, socket.AF_UNSPEC,
                                          socket.SOCK_STREAM)

                af, socktype, proto, canonname, sa = info[0]
                ip = utils.to_bytes(sa[0])
                ip_str = b"%s:%d" % (ip, port)
            except socket.gaierror:
                pass

        if int(self.config.PROXY_ENABLE):
            sock = socks.socksocket(socket.AF_INET if b':' not in ip else socket.AF_INET6)
        else:
            sock = socket.socket(socket.AF_INET if b':' not in ip else socket.AF_INET6)

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # set struct linger{l_onoff=1,l_linger=0} to avoid 10048 socket error
        # Close the connection with a TCP RST instead of a TCP FIN.
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))

        # resize socket receive buffer ->64 above to improve browser related application performance
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.config.connect_receive_buffer)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.config.connect_send_buffer)
        sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
        sock.settimeout(self.timeout)

        time_begin = time.time()
        ssl_sock = rc4_wrap.SSLConnection(sock,
                                              ip_str=ip_str,
                                              sni=sni,
                                              on_close=close_cb)
        ssl_sock.ip = ip
        ssl_sock.sni = utils.to_str(sni)

        time_connected = time.time()
        try:
            ssl_sock.do_handshake()
        except Exception as e:
            raise socket.error('tls handshake fail, sni:%s, ip_str:%s e:%r' % (sni, ip_str, e))

        time_handshaked = time.time()

        connect_time = int((time_connected - time_begin) * 1000)
        handshake_time = int((time_handshaked - time_begin) * 1000)
        if sock:
            ssl_sock.fd = sock.fileno()
        ssl_sock.create_time = time_begin
        ssl_sock.connect_time = connect_time
        ssl_sock.handshake_time = handshake_time
        ssl_sock.last_use_time = time_handshaked
        ssl_sock.host = host
        ssl_sock.received_size = 0

        if self.debug:
            self.logger.debug("connect ip:%s sni:%s host:%s success", ip_str, sni, host)

        return ssl_sock

    def check_cert(self, ssl_sock):
        return
