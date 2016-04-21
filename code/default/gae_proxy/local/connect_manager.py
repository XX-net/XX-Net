#!/usr/bin/env python
# coding:utf-8


"""
This file manage the ssl connection pool.
For faster access the target host,

ssl link will save to pool after use.
and need keep alive every 60 seconds.

We create multi-thread to try-connect google cloud ip.

we also keep host connect for direct connect.
every ssl connect can't change host after request.
"""


import os
import binascii
import time
import socket
import struct
import threading
import operator
import httplib


import socks

from xlog import getLogger
xlog = getLogger("gae_proxy")

current_path = os.path.dirname(os.path.abspath(__file__))
import OpenSSL
SSLError = OpenSSL.SSL.WantReadError

from config import config


def load_proxy_config():
    if config.PROXY_ENABLE:
        if config.PROXY_TYPE == "HTTP":
            proxy_type = socks.HTTP
        elif config.PROXY_TYPE == "SOCKS4":
            proxy_type = socks.SOCKS4
        elif config.PROXY_TYPE == "SOCKS5":
            proxy_type = socks.SOCKS5
        else:
            xlog.error("proxy type %s unknown, disable proxy", config.PROXY_TYPE)
            config.PROXY_ENABLE = 0
            return

        socks.set_default_proxy(proxy_type, config.PROXY_HOST, config.PROXY_PORT, config.PROXY_USER, config.PROXY_PASSWD)
load_proxy_config()


from google_ip import google_ip
from appids_manager import appid_manager
from openssl_wrap import SSLConnection

NetWorkIOError = (socket.error, SSLError, OpenSSL.SSL.Error, OSError)

g_cacertfile = os.path.join(current_path, "cacert.pem")
import connect_control


class Connect_pool():
    def __init__(self):
        self.pool_lock = threading.Lock()
        self.not_empty = threading.Condition(self.pool_lock)
        self.pool = {}

    def qsize(self):
        return len(self.pool)

    def put(self, item):
        handshake_time, sock = item
        self.not_empty.acquire()
        try:
            self.pool[sock] = handshake_time
            self.not_empty.notify()
        finally:
            self.not_empty.release()

    def get(self, block=True, timeout=None):
        self.not_empty.acquire()
        try:
            if not block:
                if not self.qsize():
                    return None
            elif timeout is None:
                while not self.qsize():
                    self.not_empty.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a positive number")
            else:
                end_time = time.time() + timeout
                while not self.qsize():
                    remaining = end_time - time.time()
                    if remaining <= 0.0:
                        return None
                    self.not_empty.wait(remaining)

            item = self._get()
            return item
        finally:
            self.not_empty.release()

    def get_nowait(self):
        return self.get(block=False)

    def _get(self):
        fastest_time = 9999
        fastest_sock = None
        for sock in self.pool:
            ip = sock.ip
            #if not google_ip.is_traffic_quota_allow(ip):
            #    continue

            time = self.pool[sock]
            if time < fastest_time or not fastest_sock:
                fastest_time = time
                fastest_sock = sock

        self.pool.pop(fastest_sock)
        return (fastest_time, fastest_sock)

    def get_slowest(self):
        self.not_empty.acquire()
        try:
            if not self.qsize():
                raise ValueError("no item")

            slowest_handshake_time = 0
            slowest_sock = None
            for sock in self.pool:
                handshake_time = self.pool[sock]
                if handshake_time > slowest_handshake_time:
                    slowest_handshake_time = handshake_time
                    slowest_sock = sock

            self.pool.pop(slowest_sock)
            return (slowest_handshake_time, slowest_sock)
        finally:
            self.not_empty.release()

    def get_need_keep_alive(self, maxtime=200):
        return_list = []
        self.pool_lock.acquire()
        try:
            pool = tuple(self.pool)
            for sock in pool:
                inactive_time = time.time() -sock.last_use_time
                #xlog.debug("inactive_time:%d", inactive_time * 1000)
                if inactive_time >= maxtime:
                    return_list.append(sock)
                    del self.pool[sock]

            return return_list
        finally:
            self.pool_lock.release()

    def clear(self):
        self.pool_lock.acquire()
        try:
            for sock in self.pool:
                sock.close()

            self.pool = {}
        finally:
            self.pool_lock.release()

    def to_string(self):
        str = ''
        self.pool_lock.acquire()
        try:
            pool = sorted(self.pool.items(), key=operator.itemgetter(1))
            i = 0
            for item in pool:
                sock,t = item
                str += "%d \t %s handshake:%d not_active_time:%d\r\n" % (i, sock.ip, t, time.time() -sock.last_use_time)
                i += 1
        finally:
            self.pool_lock.release()

        return str


class Https_connection_manager(object):
    thread_num_lock = threading.Lock()

    def __init__(self):
        # http://docs.python.org/dev/library/ssl.html
        # http://blog.ivanristic.com/2009/07/examples-of-the-information-collected-from-ssl-handshakes.html
        # http://src.chromium.org/svn/trunk/src/net/third_party/nss/ssl/sslenum.c
        # openssl s_server -accept 443 -key CA.crt -cert CA.crt

        # ref: http://vincent.bernat.im/en/blog/2011-ssl-session-reuse-rfc5077.html
        self.openssl_context = SSLConnection.context_builder(ca_certs=g_cacertfile)
        self.openssl_context.set_session_id(binascii.b2a_hex(os.urandom(10)))
        if hasattr(OpenSSL.SSL, 'SESS_CACHE_BOTH'):
            self.openssl_context.set_session_cache_mode(OpenSSL.SSL.SESS_CACHE_BOTH)

        self.timeout = 4
        self.max_timeout = 15
        self.thread_num = 0

        self.load_config()

        if self.keep_alive:
            p = threading.Thread(target = self.keep_alive_thread)
            p.daemon = True
            p.start()

        p = threading.Thread(target = self.create_connection_daemon)
        p.daemon = True
        p.start()

    def load_config(self):
        self.max_thread_num = config.CONFIG.getint("connect_manager", "https_max_connect_thread")
        self.connection_pool_max_num = config.CONFIG.getint("connect_manager", "https_connection_pool_max")
        self.connection_pool_min_num = config.CONFIG.getint("connect_manager", "https_connection_pool_min")
        self.keep_alive = config.CONFIG.getint("connect_manager", "https_keep_alive")

        self.new_conn_pool = Connect_pool()
        self.gae_conn_pool = Connect_pool()
        self.host_conn_pool = {}

    def clean_old_connection(self):
        # We should clean old connection if update appid.
        # because ssl connection can't change host name after first request.
        self.gae_conn_pool.clear()

    def head_request(self, ssl_sock):
        if ssl_sock.host == '':
            ssl_sock.appid = appid_manager.get_appid()
            if not ssl_sock.appid:
                xlog.error("no appid can use")
                return False
            host = ssl_sock.appid + ".appspot.com"
            ssl_sock.host = host
        else:
            host = ssl_sock.host

        # public appid don't keep alive, for quota limit.
        if ssl_sock.appid in config.PUBLIC_APPIDS:
            #xlog.info("public appid don't keep alive")
            #self.keep_alive = 0
            return False

        #xlog.debug("head request %s", host)

        request_data = 'HEAD /_gh/ HTTP/1.1\r\nHost: %s\r\n\r\n' % host

        response = None
        try:
            ssl_sock.settimeout(10)
            ssl_sock._sock.settimeout(10)

            data = request_data.encode()
            ret = ssl_sock.send(data)
            if ret != len(data):
                xlog.warn("head send len:%d %d", ret, len(data))
            response = httplib.HTTPResponse(ssl_sock, buffering=True)

            response.begin()

            status = response.status
            if status != 200:
                xlog.debug("app head fail status:%d", status)
                raise Exception("app check fail %r" % status)
            return True
        except httplib.BadStatusLine as e:
            inactive_time = time.time() - ssl_sock.last_use_time
            xlog.debug("%s keep alive fail, time:%d", ssl_sock.ip, inactive_time)
            return False
        except Exception as e:
            xlog.warn("%s head %s request fail:%r", ssl_sock.ip, ssl_sock.appid, e)
            return False
        finally:
            if response:
                response.close()

    def keep_alive_worker(self, sock):
        call_time = time.time()
        if self.head_request(sock):
            self.save_ssl_connection_for_reuse(sock, call_time=call_time)
        else:
            google_ip.report_connect_closed(sock.ip, "HEAD")
            sock.close()
            #self.create_more_connection()

    def start_keep_alive(self, sock):
        work_thread = threading.Thread(target=self.keep_alive_worker, args=(sock,))
        work_thread.start()

    def keep_alive_thread(self):
        while self.keep_alive and connect_control.keep_running:
            if not connect_control.is_active():
                time.sleep(1)
                continue

            new_list = self.new_conn_pool.get_need_keep_alive(maxtime=self.keep_alive-3)
            old_list = self.gae_conn_pool.get_need_keep_alive(maxtime=self.keep_alive-3)
            to_keep_live_list = new_list + old_list

            for ssl_sock in to_keep_live_list:
                inactive_time = time.time() - ssl_sock.last_use_time
                if inactive_time > self.keep_alive:
                    google_ip.report_connect_closed(ssl_sock.ip, "alive_timeout")
                    ssl_sock.close()
                else:
                    self.start_keep_alive(ssl_sock)

            for host in self.host_conn_pool:
                host_list = self.host_conn_pool[host].get_need_keep_alive(maxtime=self.keep_alive-3)

                for ssl_sock in host_list:
                    google_ip.report_connect_closed(ssl_sock.ip, "host pool alive_timeout")
                    ssl_sock.close()
            #self.create_more_connection()

            time.sleep(1)

    def save_ssl_connection_for_reuse(self, ssl_sock, host=None, call_time=0):
        if call_time:
            ssl_sock.last_use_time = call_time
        else:
            ssl_sock.last_use_time = time.time()

        if host:
            if host not in self.host_conn_pool:
                self.host_conn_pool[host] = Connect_pool()

            self.host_conn_pool[host].put( (ssl_sock.handshake_time, ssl_sock) )

        else:
            self.gae_conn_pool.put( (ssl_sock.handshake_time, ssl_sock) )

            while self.gae_conn_pool.qsize() > self.connection_pool_max_num:
                handshake_time, ssl_sock = self.gae_conn_pool.get_slowest()
                google_ip.report_connect_closed(ssl_sock.ip, "slowest %d" % ssl_sock.handshake_time)
                ssl_sock.close()


    def create_more_connection_worker(self):
        need_conn_num = self.connection_pool_min_num - self.new_conn_pool.qsize()

        target_thread_num = min(self.max_thread_num, need_conn_num)
        while self.thread_num < target_thread_num and self.new_conn_pool.qsize() < self.connection_pool_min_num:
            if not connect_control.allow_connect():
                break

            self.thread_num_lock.acquire()
            self.thread_num += 1
            self.thread_num_lock.release()
            p = threading.Thread(target=self.connect_thread)
            p.start()
            time.sleep(0.3)

    def create_more_connection(self):
        p = threading.Thread(target=self.create_more_connection_worker)
        p.start()

    def create_connection_daemon(self):
        connect_start_num = 0

        while connect_control.keep_running:
            time.sleep(0.1)
            if not connect_control.allow_connect():
                time.sleep(5)
                continue

            if self.thread_num > self.max_thread_num:
                continue

            target_conn_num = (1 - (connect_control.inactive_time()/(10*60))) * self.connection_pool_min_num
            if self.new_conn_pool.qsize() > target_conn_num:
                time.sleep(1)
                continue

            self.thread_num_lock.acquire()
            self.thread_num += 1
            self.thread_num_lock.release()
            p = threading.Thread(target=self.connect_process)
            p.start()
            connect_start_num += 1

            if connect_start_num > 10:
                time.sleep(5)
                connect_start_num = 0

    def connect_process(self):
        try:
            ip_str = google_ip.get_gws_ip()
            if not ip_str:
                time.sleep(60)
                xlog.warning("no enough ip")
                return

            port = 443
            #xlog.debug("create ssl conn %s", ip_str)
            ssl_sock = self._create_ssl_connection( (ip_str, port) )
            if ssl_sock:
                ssl_sock.last_use_time = time.time()
                self.new_conn_pool.put((ssl_sock.handshake_time, ssl_sock))
        finally:
            self.thread_num_lock.acquire()
            self.thread_num -= 1
            self.thread_num_lock.release()

    def connect_thread(self, sleep_time=0):
        time.sleep(sleep_time)
        try:
            while self.new_conn_pool.qsize() < self.connection_pool_min_num:
                if self.new_conn_pool.qsize() >= self.connection_pool_min_num:
                    #xlog.debug("get enough conn")
                    break

                ip_str = google_ip.get_gws_ip()
                if not ip_str:
                    time.sleep(60)
                    xlog.warning("no enough ip")
                    break

                port = 443
                #xlog.debug("create ssl conn %s", ip_str)
                ssl_sock = self._create_ssl_connection( (ip_str, port) )
                if ssl_sock:
                    ssl_sock.last_use_time = time.time()
                    self.new_conn_pool.put((ssl_sock.handshake_time, ssl_sock))
                elif not connect_control.allow_connect():
                    break
                time.sleep(1)
        finally:
            self.thread_num_lock.acquire()
            self.thread_num -= 1
            self.thread_num_lock.release()

    def _create_ssl_connection(self, ip_port):
        if not connect_control.allow_connect():
            time.sleep(10)
            return False

        sock = None
        ssl_sock = None
        ip = ip_port[0]

        connect_control.start_connect_register(high_prior=True)

        connect_time = 0
        handshake_time = 0
        time_begin = time.time()
        try:
            if config.PROXY_ENABLE:
                sock = socks.socksocket(socket.AF_INET if ':' not in ip else socket.AF_INET6)
            else:
                sock = socket.socket(socket.AF_INET if ':' not in ip else socket.AF_INET6)
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

            ssl_sock = SSLConnection(self.openssl_context, sock, ip, google_ip.ssl_closed)
            ssl_sock.set_connect_state()

            ssl_sock.connect(ip_port)
            time_connected = time.time()
            ssl_sock.do_handshake()
            time_handshaked = time.time()

            connect_time = int((time_connected - time_begin) * 1000)
            handshake_time = int((time_handshaked - time_connected) * 1000)

            google_ip.update_ip(ip, handshake_time)
            xlog.debug("create_ssl update ip:%s time:%d", ip, handshake_time)
            ssl_sock.fd = sock.fileno()
            ssl_sock.create_time = time_begin
            ssl_sock.received_size = 0
            ssl_sock.load = 0
            ssl_sock.handshake_time = handshake_time
            ssl_sock.host = ''

            def verify_SSL_certificate_issuer(ssl_sock):
                cert = ssl_sock.get_peer_certificate()
                if not cert:
                    #google_ip.report_bad_ip(ssl_sock.ip)
                    #connect_control.fall_into_honeypot()
                    raise socket.error(' certficate is none')

                issuer_commonname = next((v for k, v in cert.get_issuer().get_components() if k == 'CN'), '')
                if not issuer_commonname.startswith('Google'):
                    google_ip.report_connect_fail(ip, force_remove=True)
                    raise socket.error(' certficate is issued by %r, not Google' % ( issuer_commonname))

            verify_SSL_certificate_issuer(ssl_sock)

            connect_control.report_connect_success()
            return ssl_sock
        except Exception as e:
            time_cost = time.time() - time_begin
            if time_cost < self.timeout - 1:
                xlog.debug("connect %s fail:%s cost:%d h:%d", ip, e, time_cost * 1000, handshake_time)
            else:
                xlog.debug("%s fail:%r", ip, e)

            google_ip.report_connect_fail(ip)
            connect_control.report_connect_fail()

            if ssl_sock:
                ssl_sock.close()
            if sock:
                sock.close()
            return False
        finally:
            connect_control.end_connect_register(high_prior=True)

    def get_ssl_connection(self, host=''):
        ssl_sock = None
        if host:
            if host in self.host_conn_pool:
                while True:
                    ret = self.host_conn_pool[host].get_nowait()
                    if ret:
                        handshake_time, ssl_sock = ret
                    else:
                        ssl_sock = None
                        break

                    if time.time() - ssl_sock.last_use_time < self.keep_alive+1:
                        xlog.debug("host_conn_pool %s get:%s handshake:%d", host, ssl_sock.ip, handshake_time)
                        break
                    else:
                        google_ip.report_connect_closed(ssl_sock.ip, "get_timeout")
                        ssl_sock.close()
                        continue
        else:
            while True:
                ret = self.gae_conn_pool.get_nowait()
                if ret:
                    handshake_time, ssl_sock = ret
                else:
                    ssl_sock = None
                    break

                if time.time() - ssl_sock.last_use_time < self.keep_alive+1:
                    xlog.debug("ssl_pool.get:%s handshake:%d", ssl_sock.ip, handshake_time)
                    break
                else:
                    google_ip.report_connect_closed(ssl_sock.ip, "get_timeout")
                    ssl_sock.close()
                    continue

        self.create_more_connection()

        if ssl_sock:
            return ssl_sock
        else:
            ret = self.new_conn_pool.get(True, self.max_timeout)
            if ret:
                handshake_time, ssl_sock = ret
                return ssl_sock
            else:
                xlog.debug("create ssl timeout fail.")
                return None

    def get_new_ssl(self):
        self.create_more_connection()
        ret = self.new_conn_pool.get(True, self.max_timeout)
        if ret:
            handshake_time, ssl_sock = ret
            return ssl_sock
        else:
            xlog.debug("get_new_ssl timeout fail.")
            return None

https_manager = Https_connection_manager()
