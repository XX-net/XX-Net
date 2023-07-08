import os
import socket
import struct
import time

import socks
import utils
import front_base.openssl_wrap


from front_base.connect_creator import ConnectCreator as ConnectCreatorBase


class ConnectCreator(ConnectCreatorBase):

    def connect_ssl(self, ip_str, sni, host, close_cb=None):
        info = self.host_manager.get_info(ip_str)
        sni = str(info["sni"])
        url_path = info["url_path"]
        host = sni
        ip, port = utils.get_ip_port(ip_str)

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

        time_begin = time.time()
        if info.get("client_ca"):
            self.openssl_context.context.load_cert_chain(os.path.abspath(info["client_ca_fn"]),
                                                         os.path.abspath(info["client_key_fn"]))

        ssl_sock = front_base.openssl_wrap.SSLConnection(self.openssl_context.context, sock,
                                                         ip_str=ip_str,
                                                         sni=sni,
                                                         on_close=close_cb)
        time_connected = time.time()
        try:
            ssl_sock.do_handshake()
        except Exception as e:
            raise socket.error('tls handshake fail, sni:%s, top:%s e:%r' % (sni, host, e))

        if ssl_sock.is_support_h2():
            ssl_sock.h2 = True
        else:
            ssl_sock.h2 = False

        time_handshaked = time.time()

        ssl_sock.sni = sni
        ssl_sock.url_path = utils.to_bytes(url_path)
        self.check_cert(ssl_sock)

        connect_time = int((time_connected - time_begin) * 1000)
        handshake_time = int((time_handshaked - time_begin) * 1000)
        # sometimes, we want to use raw tcp socket directly(select/epoll), so setattr it to ssl socket.
        ssl_sock.ip_str = ip_str
        ssl_sock._sock = sock
        ssl_sock.fd = sock.fileno()
        ssl_sock.create_time = time_begin
        ssl_sock.connect_time = connect_time
        ssl_sock.handshake_time = handshake_time
        ssl_sock.last_use_time = time_handshaked
        ssl_sock.host = host
        ssl_sock.received_size = 0

        return ssl_sock
