#!/usr/bin/env python
# coding:utf-8

import os
import errno
import binascii
import time
import socket
import select
import Queue
import struct
import xlog
import threading
import operator
import httplib
import random
import socks

current_path = os.path.dirname(os.path.abspath(__file__))
import OpenSSL
SSLError = OpenSSL.SSL.WantReadError

from config import config

def load_sock():
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

    if config.PROXY_ENABLE:
        socks.set_default_proxy(proxy_type, config.PROXY_HOST, config.PROXY_PORT, config.PROXY_USER, config.PROXY_PASSWD)
load_sock()


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
                #logging.debug("inactive_time:%d", inactive_time * 1000)
                if inactive_time >= maxtime:
                    return_list.append(sock)
                    del self.pool[sock]

            return return_list
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
        self.max_thread_num = config.CONFIG.getint("connect_manager", "https_max_connect_thread") #10
        self.connection_pool_max_num = config.CONFIG.getint("connect_manager", "https_connection_pool_max") #20/30
        self.connection_pool_min_num = config.CONFIG.getint("connect_manager", "https_connection_pool_min") #20/30
        self.keep_alive = config.CONFIG.getint("connect_manager", "https_keep_alive") #1

        self.new_conn_pool = Connect_pool()
        self.gae_conn_pool = Connect_pool()
        self.host_conn_pool = {}

        self.openssl_context = SSLConnection.context_builder(ca_certs=g_cacertfile)

        # ref: http://vincent.bernat.im/en/blog/2011-ssl-session-reuse-rfc5077.html
        self.openssl_context.set_session_id(binascii.b2a_hex(os.urandom(10)))
        if hasattr(OpenSSL.SSL, 'SESS_CACHE_BOTH'):
            self.openssl_context.set_session_cache_mode(OpenSSL.SSL.SESS_CACHE_BOTH)

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
        if ssl_sock.appid.startswith("xxnet-") and ssl_sock.appid[7:].isdigit():
            #logging.info("public appid don't keep alive")
            #self.keep_alive = 0
            return False

        #logging.debug("head request %s", host)

        request_data = 'HEAD /_gh/ HTTP/1.1\r\nHost: %s\r\n\r\n' % host

        response = None
        try:
            ssl_sock.settimeout(3)
            ssl_sock.sock.settimeout(3)

            data = request_data.encode()
            ret = ssl_sock.send(data)
            if ret != len(data):
                xlog.warn("head send len:%d %d", ret, len(data))
            response = httplib.HTTPResponse(ssl_sock, buffering=True)

            response.begin()

            status = response.status
            if status != 200:
                xlog.debug("app head fail status:%d", status)
                raise Exception("app check fail")
            return True
        except httplib.BadStatusLine as e:
            xlog.debug("head request BadStatusLine fail:%r", e)
            return False
        except Exception as e:
            xlog.debug("head request fail:%r", e)
            return False
        finally:
            if response:
                response.close()

    def keep_alive_worker(self, sock):
        if self.head_request(sock):
            self.save_ssl_connection_for_reuse(sock)
        else:
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
                    ssl_sock.close()
                else:
                    self.start_keep_alive(ssl_sock)

            #self.create_more_connection()

            time.sleep(1)

    def save_ssl_connection_for_reuse(self, ssl_sock, host=None):
        ssl_sock.last_use_time = time.time()
        if host:
            if host not in self.host_conn_pool:
                self.host_conn_pool[host] = Connect_pool()

            self.host_conn_pool[host].put( (ssl_sock.handshake_time, ssl_sock) )

        else:
            self.gae_conn_pool.put( (ssl_sock.handshake_time, ssl_sock) )

            while self.gae_conn_pool.qsize() > self.connection_pool_max_num:
                handshake_time, ssl_sock = self.gae_conn_pool.get_slowest()
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
                xlog.warning("no gws ip")
                return

            port = 443
            #logging.debug("create ssl conn %s", ip_str)
            ssl_sock = self._create_ssl_connection( (ip_str, port) )
            if ssl_sock:
                ssl_sock.last_use_time = time.time()
                self.new_conn_pool.put((ssl_sock.handshake_time, ssl_sock))
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

            ssl_sock.connect(ip_port)
            time_connected = time.time()
            ssl_sock.do_handshake()
            time_handshaked = time.time()

            connect_time = int((time_connected - time_begin) * 1000)
            handshake_time = int((time_handshaked - time_connected) * 1000)

            google_ip.update_ip(ip, handshake_time)
            xlog.debug("create_ssl update ip:%s time:%d", ip, handshake_time)
            # sometimes, we want to use raw tcp socket directly(select/epoll), so setattr it to ssl socket.
            ssl_sock.ip = ip
            ssl_sock.sock = sock
            ssl_sock.create_time = time_begin
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
                    google_ip.report_bad_ip(ssl_sock.ip)
                    connect_control.fall_into_honeypot()
                    raise socket.error(' certficate is issued by %r, not Google' % ( issuer_commonname))

            verify_SSL_certificate_issuer(ssl_sock)

            connect_control.report_connect_success()
            return ssl_sock
        except Exception as e:
            time_cost = time.time() - time_begin
            if time_cost < self.timeout - 1:
                xlog.debug("connect %s fail:%s cost:%d h:%d", ip, e, time_cost * 1000, handshake_time)
            else:
                xlog.debug("%s fail", ip)

            google_ip.report_connect_fail(ip)
            connect_control.report_connect_fail()

            if ssl_sock:
                ssl_sock.close()
            if sock:
                sock.close()
            return False
        finally:
            connect_control.end_connect_register(high_prior=True)


    def connect_thread(self, sleep_time=0):
        time.sleep(sleep_time)
        try:
            while self.new_conn_pool.qsize() < self.connection_pool_min_num:
                if self.new_conn_pool.qsize() >= self.connection_pool_min_num:
                    #xlog.debug("get enough conn")
                    break

                ip_str = google_ip.get_gws_ip()
                if not ip_str:
                    xlog.warning("no gws ip")
                    break

                port = 443
                #logging.debug("create ssl conn %s", ip_str)
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

                    if time.time() - ssl_sock.last_use_time < self.keep_alive+1: # gws ssl connection can keep for 230s after created
                        xlog.debug("host_conn_pool %s get:%s handshake:%d", host, ssl_sock.ip, handshake_time)
                        break
                    else:
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

                if time.time() - ssl_sock.last_use_time < self.keep_alive+1: # gws ssl connection can keep for 230s after created
                    xlog.debug("ssl_pool.get:%s handshake:%d", ssl_sock.ip, handshake_time)
                    break
                else:
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





class Forward_connection_manager():
    timeout = 1
    max_timeout = 60
    tcp_connection_cache = Queue.PriorityQueue()
    thread_num_lock = threading.Lock()
    thread_num = 0

    def __init__(self):
        self.load_config()

    def load_config(self):
        self.max_thread_num = config.CONFIG.getint("connect_manager", "forward_max_connect_thread") #10

    def create_connection(self, host="", port=443, sock_life=5):
        if port != 443:
            xlog.warn("forward port %d not supported.", port)
            return None

        def _create_connection(ip_port, delay=0):
            time.sleep(delay)
            ip = ip_port[0]
            sock = None
            # start connection time record
            start_time = time.time()
            conn_time = 0
            connect_control.start_connect_register(high_prior=True)
            try:
                # create a ipv4/ipv6 socket object
                if config.PROXY_ENABLE:
                    sock = socks.socksocket(socket.AF_INET if ':' not in ip else socket.AF_INET6)
                else:
                    sock = socket.socket(socket.AF_INET if ':' not in ip else socket.AF_INET6)
                # set reuseaddr option to avoid 10048 socket error
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # resize socket recv buffer 8K->32K to improve browser releated application performance
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32*1024)
                # disable negal algorithm to send http request quickly.
                sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
                # set a short timeout to trigger timeout retry more quickly.
                sock.settimeout(self.timeout)

                # TCP connect
                sock.connect(ip_port)

                # record TCP connection time
                conn_time = time.time() - start_time
                xlog.debug("tcp conn %s time:%d", ip, conn_time * 1000)

                google_ip.update_ip(ip, conn_time * 2000)
                #logging.info("create_tcp update ip:%s time:%d", ip, conn_time * 2000)

                # put ssl socket object to output queobj
                #sock.ip = ip
                self.tcp_connection_cache.put((time.time(), sock))
            except Exception as e:
                conn_time = int((time.time() - start_time) * 1000)
                xlog.debug("tcp conn %s fail t:%d", ip, conn_time)
                google_ip.report_connect_fail(ip)
                #logging.info("create_tcp report fail ip:%s", ip)
                if sock:
                    sock.close()
            finally:
                self.thread_num_lock.acquire()
                self.thread_num -= 1
                self.thread_num_lock.release()
                connect_control.end_connect_register(high_prior=True)


        if host != "appengine.google.com":
            while True:
                try:
                    ctime, sock = self.tcp_connection_cache.get_nowait()
                    if time.time() - ctime < sock_life:
                        return sock
                    else:
                        sock.close()
                        continue
                except Queue.Empty:
                    break

        start_time = time.time()
        while time.time() - start_time < self.max_timeout:

            if self.thread_num < self.max_thread_num:
                if host == "appengine.google.com":
                    ip = google_ip.get_host_ip("*.google.com")
                else:
                    ip = google_ip.get_gws_ip()
                if not ip:
                    xlog.error("no gws ip.")
                    return
                addr = (ip, port)
                self.thread_num_lock.acquire()
                self.thread_num += 1
                self.thread_num_lock.release()
                p = threading.Thread(target=_create_connection, args=(addr,))
                p.start()

            try:
                ctime, sock = self.tcp_connection_cache.get(timeout=0.2)
                return sock
            except:
                continue
        xlog.warning('create tcp connection fail.')


    def forward_socket(self, local, remote, timeout=60, tick=2, bufsize=8192):
        try:
            timecount = timeout
            while 1:
                timecount -= tick
                if timecount <= 0:
                    break
                (ins, _, errors) = select.select([local, remote], [], [local, remote], tick)
                if errors:
                    break
                if not ins:
                    continue

                for sock in ins:
                    data = sock.recv(bufsize)
                    if not data:
                        if sock is remote:
                            xlog.debug("forward remote disconnected.")
                        else:
                            xlog.debug("forward local disconnected.")
                        return

                    if sock is remote:
                        local.sendall(data)
                        timecount = timeout
                    else:
                        remote.sendall(data)
                        timecount = timeout
        except Exception as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.ENOTCONN, errno.EPIPE):
                xlog.exception("forward except:%s.", e)
        finally:
            if local:
                local.close()
            if remote:
                remote.close()




https_manager = Https_connection_manager()
forwork_manager = Forward_connection_manager()


def test_pool():
    pool = Connect_pool()
    pool.put((3, "c"))
    pool.put((1, "a"))
    pool.put((2, "b"))

    t, s = pool.get()
    print s

    t, s = pool.get()
    print s

    t, s = pool.get()
    print s


def test_pool_speed():
    pool = Connect_pool()
    for i in range(100):
        pool.put((i, "%d"%i))

    start = time.time()
    t, s = pool.get()
    print time.time() - start
    print s
    # sort time is 5ms for 10000
    # sort time is 0ms for 100

if __name__ == "__main__":
    #test_pool_speed()
    #sock = forwork_manager.create_connection()
    #print sock
    appid = "xxnet-a23"
    le = appid[7:]
    print le
    if appid.startswith("xxnet-") and le.isdigit():
        print "is dig"
    else:
        print "not dig"