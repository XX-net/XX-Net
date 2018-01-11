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

import time
import threading
import operator


from xlog import getLogger
xlog = getLogger("gae_proxy")
import check_local_network
from config import config
from google_ip import google_ip
import connect_control
import check_ip


class Connect_pool():
    def __init__(self):
        self.pool_lock = threading.Lock()
        self.not_empty = threading.Condition(self.pool_lock)
        self.pool = {}
        self.h1_num = 0

    def qsize(self, only_h1=False):
        if only_h1:
            return self.h1_num
        else:
            return len(self.pool)

    def put(self, item):
        handshake_time, sock = item
        self.not_empty.acquire()
        try:
            self.pool[sock] = handshake_time
            if not sock.h2:
                self.h1_num += 1
            self.not_empty.notify()
        finally:
            self.not_empty.release()

    def get(self, block=True, timeout=None, only_h1=False):
        self.not_empty.acquire()
        try:
            if not block:
                if self.qsize(only_h1=only_h1) == 0:
                    return None
            elif timeout is None:
                while self.qsize(only_h1=only_h1) == 0:
                    self.not_empty.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a positive number")
            else:
                end_time = time.time() + timeout
                while not self.qsize(only_h1=only_h1):
                    remaining = end_time - time.time()
                    if remaining <= 0.0:
                        return None
                    self.not_empty.wait(remaining)

            item = self._get(only_h1=only_h1)
            return item
        finally:
            self.not_empty.release()

    def get_nowait(self, only_h1=False):
        return self.get(block=False, only_h1=only_h1)

    def _get(self, only_h1=False):
        fastest_time = 9999
        fastest_sock = None
        for sock in self.pool:
            if only_h1 and sock.h2:
                continue

            hs_time = self.pool[sock]
            if hs_time < fastest_time or not fastest_sock:
                fastest_time = hs_time
                fastest_sock = sock

        if not fastest_sock.h2:
            self.h1_num -= 1

        self.pool.pop(fastest_sock)
        return fastest_time, fastest_sock

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

            if not slowest_sock.h2:
                self.h1_num -= 1

            self.pool.pop(slowest_sock)
            return slowest_handshake_time, slowest_sock
        finally:
            self.not_empty.release()

    def get_need_keep_alive(self, maxtime=200):
        return_list = []
        self.pool_lock.acquire()
        try:
            pool = tuple(self.pool)
            for sock in pool:
                inactive_time = time.time() - sock.last_use_time
                # xlog.debug("inactive_time:%d", inactive_time * 1000)
                if inactive_time >= maxtime:
                    return_list.append(sock)

                    if not sock.h2:
                        self.h1_num -= 1

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
            self.h1_num = 0
        finally:
            self.pool_lock.release()

    def to_string(self):
        out_str = ''
        self.pool_lock.acquire()
        try:
            pool = sorted(self.pool.items(), key=operator.itemgetter(1))
            i = 0
            for item in pool:
                sock,t = item
                out_str += "%d \t %s handshake:%d not_active_time:%d h2:%d\r\n" % (i, sock.ip, t, time.time() - sock.last_use_time, sock.h2)
                i += 1
        finally:
            self.pool_lock.release()

        return out_str


class Https_connection_manager(object):
    thread_num_lock = threading.Lock()

    def __init__(self):
        self.class_name = "Https_connection_manager"
        self.timeout = 4
        self.max_timeout = 60
        self.thread_num = 0

        # after new created ssl_sock timeout(50 seconds)
        # call the callback.
        # This callback will put ssl to worker
        self.ssl_timeout_cb = None

        self.connecting_more_thread = None

        self.load_config()

        p = threading.Thread(target=self.keep_alive_thread)
        p.daemon = True
        p.start()

        if self.connection_pool_min_num:
            p = threading.Thread(target=self.keep_connection_daemon)
            p.daemon = True
            p.start()

        self.create_more_connection()

    def load_config(self):
        self.max_thread_num = config.CONFIG.getint("connect_manager", "https_max_connect_thread")
        self.connection_pool_max_num = config.CONFIG.getint("connect_manager", "https_connection_pool_max")
        self.connection_pool_min_num = config.CONFIG.getint("connect_manager", "https_connection_pool_min")
        self.keep_alive = config.CONFIG.getint("connect_manager", "https_keep_alive")
        self.keep_active_timeout = config.CONFIG.getint("connect_manager", "keep_active_timeout")
        self.https_new_connect_num = config.CONFIG.getint("connect_manager", "https_new_connect_num")

        self.new_conn_pool = Connect_pool()
        self.gae_conn_pool = Connect_pool()
        self.host_conn_pool = {}

    def set_ssl_time_handler(self, cb):
        self.ssl_timeout_cb = cb

    def keep_alive_thread(self):
        while connect_control.keep_running:
            if not connect_control.is_active():
                time.sleep(1)
                continue

            to_keep_live_list = self.new_conn_pool.get_need_keep_alive(maxtime=self.keep_alive-3)

            for ssl_sock in to_keep_live_list:
                inactive_time = time.time() - ssl_sock.last_use_time
                if inactive_time > self.keep_alive or not self.ssl_timeout_cb:
                    google_ip.report_connect_closed(ssl_sock.ip, "alive_timeout")
                    ssl_sock.close()
                else:
                    # put ssl to worker
                    try:
                        self.ssl_timeout_cb(ssl_sock)
                    except Exception as e:
                        xlog.exception("ssl_timeout_cb except:%r", e)
                        # no appid avaiable
                        pass

            for host in self.host_conn_pool:
                host_list = self.host_conn_pool[host].get_need_keep_alive(maxtime=self.keep_alive-3)

                for ssl_sock in host_list:
                    google_ip.report_connect_closed(ssl_sock.ip, "host pool alive_timeout")
                    ssl_sock.close()

            time.sleep(1)

    def save_ssl_connection_for_reuse(self, ssl_sock, host=None, call_time=0):
        # only used by direct mode now, host ssl.
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

    def keep_connection_daemon(self):
        while connect_control.keep_running:
            if not connect_control.allow_connect():
                time.sleep(5)
                continue

            if self.new_conn_pool.qsize() > self.connection_pool_min_num:
                time.sleep(5)
                continue

            self.connect_process()

    def connect_process(self):
        try:
            ip_str = google_ip.get_gws_ip()
            if not ip_str:
                time.sleep(60)
                xlog.warning("no enough ip")
                return

            #xlog.debug("create ssl conn %s", ip_str)
            ssl_sock = self._create_ssl_connection( (ip_str, 443) )
            if not ssl_sock:
                return

            self.new_conn_pool.put((ssl_sock.handshake_time, ssl_sock))
        except:
            pass

    def create_more_connection_worker(self):
        while connect_control.allow_connect() and \
                self.thread_num < self.max_thread_num and \
                (self.new_conn_pool.qsize() < self.https_new_connect_num or
                    self.new_conn_pool.qsize(only_h1=True) < 1):

            self.thread_num_lock.acquire()
            self.thread_num += 1
            self.thread_num_lock.release()
            p = threading.Thread(target=self.connect_thread)
            p.start()
            time.sleep(0.5)

        self.connecting_more_thread = None

    def create_more_connection(self):
        if not self.connecting_more_thread:
            self.connecting_more_thread = threading.Thread(target=self.create_more_connection_worker)
            self.connecting_more_thread.start()

    def connect_thread(self, sleep_time=0):
        time.sleep(sleep_time)
        try:
            while self.new_conn_pool.qsize() < self.https_new_connect_num or \
                    self.new_conn_pool.qsize(only_h1=True) < 1:

                if self.new_conn_pool.qsize() > self.connection_pool_max_num:
                    break

                if not connect_control.allow_connect():
                    break

                ip_str = google_ip.get_gws_ip()
                if not ip_str:
                    xlog.warning("no enough ip")
                    time.sleep(60)
                    break

                ssl_sock = self._create_ssl_connection( (ip_str, 443) )
                if not ssl_sock:
                    continue

                if self.ssl_timeout_cb and \
                        self.new_conn_pool.qsize() > self.connection_pool_max_num + 1 and \
                        self.new_conn_pool.qsize() > self.https_new_connect_num + 1 and \
                        self.new_conn_pool.qsize(only_h1=True) > 2:

                    self.ssl_timeout_cb(ssl_sock)
                else:
                    self.new_conn_pool.put((ssl_sock.handshake_time, ssl_sock))
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

        try:
            ssl_sock = check_ip.connect_ssl(ip, port=443, timeout=self.timeout, check_cert=True,
                                            close_cb=google_ip.ssl_closed)

            google_ip.update_ip(ip, ssl_sock.handshake_time)
            xlog.debug("create_ssl update ip:%s time:%d h2:%d", ip, ssl_sock.handshake_time, ssl_sock.h2)

            connect_control.report_connect_success()
            return ssl_sock
        except check_ip.Cert_Exception as e:
            xlog.debug("connect %s fail:%s ", ip, e)
            google_ip.report_connect_fail(ip, force_remove=True)

            if ssl_sock:
                ssl_sock.close()
            if sock:
                sock.close()
        except Exception as e:
            xlog.debug("connect %s fail:%r", ip, e)

            google_ip.report_connect_fail(ip)
            connect_control.report_connect_fail()

            if not check_local_network.IPv4.is_ok():
                time.sleep(10)
            else:
                time.sleep(1)

            if ssl_sock:
                ssl_sock.close()
            if sock:
                sock.close()
        finally:
            connect_control.end_connect_register(high_prior=True)

    def get_ssl_connection(self, host=''):
        ssl_sock = None
        if host:
            only_h1=True
            if host in self.host_conn_pool:
                while True:
                    ret = self.host_conn_pool[host].get_nowait(only_h1=True)
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
            only_h1=False
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
            start_time = time.time()
            while True:
                ret = self.new_conn_pool.get(True, 1, only_h1=only_h1)
                if ret:
                    handshake_time, ssl_sock = ret
                    if time.time() - ssl_sock.last_use_time < self.keep_active_timeout - 1:
                        # xlog.debug("new_conn_pool.get:%s handshake:%d", ssl_sock.ip, handshake_time)
                        return ssl_sock
                    else:
                        # xlog.debug("new_conn_pool.get:%s handshake:%d timeout.", ssl_sock.ip, handshake_time)
                        google_ip.report_connect_closed(ssl_sock.ip, "get_timeout")
                        ssl_sock.close()
                        continue
                else:
                    if time.time() - start_time > self.max_timeout:
                        xlog.debug("create ssl timeout fail.")
                        return None

    def get_new_ssl(self, only_h1=True):
        self.create_more_connection()
        ret = self.new_conn_pool.get(True, self.max_timeout, only_h1=only_h1)
        if ret:
            handshake_time, ssl_sock = ret
            return ssl_sock
        else:
            xlog.debug("get_new_ssl timeout fail.")
            return None


https_manager = Https_connection_manager()
