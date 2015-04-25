#!/usr/bin/env python
# coding:utf-8

import os
import binascii
import time
import socket
import struct
import logging
import threading
import operator
import random

current_path = os.path.dirname(os.path.abspath(__file__))
import OpenSSL
SSLError = OpenSSL.SSL.WantReadError

from config import config
if config.PROXY_ENABLE:
    import socks
    if config.PROXY_TYPE == "HTTP":
        proxy_type = socks.HTTP
    elif config.PROXY_TYPE == "SOCKS4":
        proxy_type = socks.SOCKS4
    elif config.PROXY_TYPE == "SOCKS5":
        proxy_type = socks.SOCKS5
    else:
        logging.error("proxy type %s unknown, disable proxy", config.PROXY_TYPE)
        config.PROXY_ENABLE = 0

if config.PROXY_ENABLE:
    socks.set_default_proxy(proxy_type, config.PROXY_HOST, config.PROXY_PORT, config.PROXY_USER, config.PROXY_PASSWD)



from google_ip import google_ip
from openssl_wrap import SSLConnection

NetWorkIOError = (socket.error, SSLError, OpenSSL.SSL.Error, OSError)

g_cacertfile = os.path.join(current_path, "cacert.pem")

from connect_manager import Connect_pool, random_hostname
from connect_manager import connect_allow_time, connect_fail_time

class Direct_connect_manager(object):

    thread_num_lock = threading.Lock()
    keep_alive = config.CONFIG.getint("connect_manager", "https_keep_alive") #0

    def __init__(self):
        # http://docs.python.org/dev/library/ssl.html
        # http://blog.ivanristic.com/2009/07/examples-of-the-information-collected-from-ssl-handshakes.html
        # http://src.chromium.org/svn/trunk/src/net/third_party/nss/ssl/sslenum.c
        # openssl s_server -accept 443 -key CA.crt -cert CA.crt

        self.timeout = 2
        self.max_timeout = 60
        self.thread_num = 0
        self.max_thread_num = config.CONFIG.getint("connect_manager", "https_max_connect_thread") #10
        self.connection_pool_max_num = config.CONFIG.getint("connect_manager", "https_connection_pool_max") #20/30
        self.connection_pool_min_num = config.CONFIG.getint("connect_manager", "https_connection_pool_min") #20/30

        self.new_conn_pool = Connect_pool()
        self.host_conn_pool = {}

        self.openssl_context = SSLConnection.context_builder(ssl_version="TLSv1", ca_certs=g_cacertfile)

        # ref: http://vincent.bernat.im/en/blog/2011-ssl-session-reuse-rfc5077.html
        self.openssl_context.set_session_id(binascii.b2a_hex(os.urandom(10)))
        if hasattr(OpenSSL.SSL, 'SESS_CACHE_BOTH'):
            self.openssl_context.set_session_cache_mode(OpenSSL.SSL.SESS_CACHE_BOTH)




    def save_ssl_connection_for_reuse(self, ssl_sock, host):
        ssl_sock.last_use_time = time.time()
        if host not in self.host_conn_pool:
            self.host_conn_pool[host] = Connect_pool()
        self.host_conn_pool[host].put( (ssl_sock.handshake_time, ssl_sock) )

        while self.host_conn_pool[host].qsize() > self.connection_pool_max_num:
            t, ssl_sock = self.host_conn_pool[host].get_slowest()

            if t < 200:
                self.host_conn_pool[host].put( (ssl_sock.handshake_time, ssl_sock) )
                #ssl_sock.close()
                return
            else:
                ssl_sock.close()


    def create_more_connection(self):
        target_thread_num = min(self.max_thread_num, (self.connection_pool_min_num - self.new_conn_pool.qsize()))
        while self.thread_num < target_thread_num and self.new_conn_pool.qsize() < self.connection_pool_min_num:
            self.thread_num_lock.acquire()
            self.thread_num += 1
            self.thread_num_lock.release()
            p = threading.Thread(target = self.connect_thread)
            p.daemon = True
            p.start()
            time.sleep(0.3)



    def _create_ssl_connection(self, ip_port):
        global connect_allow_time, connect_fail_time
        if time.time() < connect_allow_time:
            return False

        sock = None
        ssl_sock = None
        ip = ip_port[0]

        connect_time = 0
        handshake_time = 0
        time_begin = time.time()
        try:
            if config.PROXY_ENABLE:
                sock = socks.socksocket(socket.AF_INET if ':' not in ip_port[0] else socket.AF_INET6)
            else:
                sock = socket.socket(socket.AF_INET if ':' not in ip_port[0] else socket.AF_INET6)
            # set reuseaddr option to avoid 10048 socket error
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # set struct linger{l_onoff=1,l_linger=0} to avoid 10048 socket error
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
            # resize socket recv buffer 8K->32K to improve browser releated application performance
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32*1024)
            # disable negal algorithm to send http request quickly.
            sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
            # set a short timeout to trigger timeout retry more quickly.

            sock.settimeout(self.timeout)


            ssl_sock = SSLConnection(self.openssl_context, sock)
            ssl_sock.set_connect_state()

            # pick up the certificate
            server_hostname = random_hostname()
            if server_hostname and hasattr(ssl_sock, 'set_tlsext_host_name'):
                #ssl_sock.set_tlsext_host_name(server_hostname)
                pass


            ssl_sock.connect(ip_port)
            time_connected = time.time()
            ssl_sock.do_handshake()
            time_handshaked = time.time()

            connect_time = int((time_connected - time_begin) * 1000)
            handshake_time = int((time_handshaked - time_connected) * 1000)

            google_ip.update_ip(ip, handshake_time)
            logging.debug("direct create_ssl update ip:%s time:%d", ip, handshake_time)
            # sometimes, we want to use raw tcp socket directly(select/epoll), so setattr it to ssl socket.
            ssl_sock.ip = ip
            ssl_sock.sock = sock
            ssl_sock.create_time = time_begin
            ssl_sock.handshake_time = handshake_time
            ssl_sock.host = ''

            def verify_SSL_certificate_issuer(ssl_sock):
                global connect_allow_time
                cert = ssl_sock.get_peer_certificate()
                if not cert:
                    google_ip.report_bad_ip(ip)
                    connect_allow_time = time.time() + (60 * 5)
                    raise socket.error(' certficate is none')

                issuer_commonname = next((v for k, v in cert.get_issuer().get_components() if k == 'CN'), '')
                if not issuer_commonname.startswith('Google'):
                    google_ip.report_bad_ip(ip)
                    connect_allow_time = time.time() + (60 * 5)
                    raise socket.error(' certficate is issued by %r, not Google' % ( issuer_commonname))

            verify_SSL_certificate_issuer(ssl_sock)
            connect_fail_time = 0

            return ssl_sock
        except Exception as e:
            time_cost = time.time() - time_begin
            logging.debug("direct_create_ssl %s fail:%s cost:%d h:%d", ip, e, time_cost * 1000, handshake_time)
            if time_cost < self.timeout:
                google_ip.report_bad_ip(ip)

            if connect_fail_time == 0:
                connect_fail_time = time.time()
            else:
                if time.time() - connect_fail_time > 30:
                    connect_allow_time = time.time() + (60 * 5)

            google_ip.report_connect_fail(ip)


            if ssl_sock:
                ssl_sock.close()
            if sock:
                sock.close()
            return False


    def connect_thread(self):
        global connect_allow_time
        try:
            while self.new_conn_pool.qsize() < self.connection_pool_min_num:
                ip_str = google_ip.get_gws_ip()
                if not ip_str:
                    logging.warning("no gws ip")
                    break

                port = 443
                #logging.debug("create ssl conn %s", ip_str)
                ssl_sock = self._create_ssl_connection( (ip_str, port) )
                if ssl_sock:
                    ssl_sock.last_use_time = time.time()
                    self.new_conn_pool.put((ssl_sock.handshake_time, ssl_sock))
                elif time.time() < connect_allow_time:
                    break
                time.sleep(1)
        finally:
            self.thread_num_lock.acquire()
            self.thread_num -= 1
            self.thread_num_lock.release()

    def create_ssl_connection(self, host=''):

        if host in self.host_conn_pool:
            while True:
                ret = self.host_conn_pool[host].get_nowait()
                if ret:
                    handshake_time, ssl_sock = ret
                else:
                    ssl_sock = None
                    break

                if time.time() - ssl_sock.last_use_time < 225: # gws ssl connection can keep for 230s after created
                    logging.debug("host_conn_pool %s get:%s handshake:%d", host, ssl_sock.ip, handshake_time)
                    return ssl_sock
                    break
                else:
                    ssl_sock.close()
                    continue

        while True:
            ret = self.new_conn_pool.get_nowait()
            if ret:
                handshake_time, ssl_sock = ret
            else:
                ssl_sock = None
                break

            if time.time() - ssl_sock.last_use_time < 225: # gws ssl connection can keep for 230s after created
                logging.debug("new_conn_pool.get:%s handshake:%d", ssl_sock.ip, handshake_time)
                break
            else:
                ssl_sock.close()
                continue

        conn_num = self.new_conn_pool.qsize()
        logging.debug("new_conn_pool conn_num:%d", conn_num)
        if conn_num < self.connection_pool_min_num:
            self.create_more_connection()

        if ssl_sock:
            return ssl_sock
        else:
            ret = self.new_conn_pool.get(True, self.max_timeout)
            if ret:
                handshake_time, ssl_sock = ret
                return ssl_sock
            else:
                logging.debug("create ssl for direct timeout.")
                return None



direct_connect_manager = Direct_connect_manager()



if __name__ == "__main__":
    pass