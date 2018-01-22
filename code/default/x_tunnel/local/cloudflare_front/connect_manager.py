#!/usr/bin/env python
# coding:utf-8


"""
This file manage the ssl connection pool.
For faster access the target host,

ssl link need keep alive every 60 seconds.

We create multi-thread to try-connect cloud ip.

"""


import operator
import threading
import time

from ip_manager import ip_manager
import connect_control
from config import config
import check_ip
import check_local_network
import utils
from xlog import getLogger
xlog = getLogger("cloudflare_front")


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
                inactive_time = time.time() -sock.last_use_time
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
                out_str += "%d \t %s handshake:%d not_active_time:%d h2:%d\r\n" % (i, sock.ip, t, time.time() -sock.last_use_time, sock.h2)
                i += 1
        finally:
            self.pool_lock.release()

        return out_str


class Https_connection_manager(object):
    def __init__(self, host, ssl_timeout_cb):
        self.thread_num_lock = threading.Lock()
        sub, top = utils.split_domain(host)
        self.sub = sub

        self.class_name = "Https_connection_manager"
        self.connect_timeout = 4
        self.thread_num = 0
        self.getter_num = 0

        # after new created ssl_sock timeout(50 seconds)
        # call the callback.
        # This callback will put ssl to worker
        self.ssl_timeout_cb = ssl_timeout_cb

        self.connecting_more_thread = None

        self.load_config()

        p = threading.Thread(target=self.keep_alive_thread)
        p.daemon = True
        p.start()

        self.create_more_connection()

    def load_config(self):
        self.max_connect_thread = config.CONFIG.getint("connect_manager", "max_connect_thread")
        self.ssl_first_use_timeout = config.CONFIG.getint("connect_manager", "ssl_first_use_timeout")
        self.connection_pool_min = config.CONFIG.getint("connect_manager", "connection_pool_min")

        self.new_conn_pool = Connect_pool()

    def keep_alive_thread(self):
        while connect_control.keep_running:
            if not connect_control.is_active():
                time.sleep(1)
                continue

            to_keep_live_list = self.new_conn_pool.get_need_keep_alive(maxtime=self.ssl_first_use_timeout-2)

            for ssl_sock in to_keep_live_list:
                inactive_time = time.time() - ssl_sock.last_use_time
                if inactive_time > self.ssl_first_use_timeout + 5 or not self.ssl_timeout_cb:
                    ip_manager.report_connect_closed(ssl_sock.ip, "alive_timeout")
                    ssl_sock.close()
                else:
                    # put ssl to worker
                    try:
                        self.ssl_timeout_cb(ssl_sock)
                    except:
                        # no appid avaiable
                        pass

            time.sleep(1)

    def create_more_connection(self):
        if not self.connecting_more_thread:
            self.connecting_more_thread = threading.Thread(target=self.create_more_connection_worker)
            self.connecting_more_thread.start()

    def create_more_connection_worker(self):
        while connect_control.allow_connect() and \
                self.thread_num < self.max_connect_thread and \
                (self.new_conn_pool.qsize() < self.connection_pool_min):

            self.thread_num_lock.acquire()
            self.thread_num += 1
            self.thread_num_lock.release()
            p = threading.Thread(target=self.connect_thread)
            p.start()
            time.sleep(0.5)

        self.connecting_more_thread = None

    def connect_thread(self, sleep_time=0):
        time.sleep(sleep_time)
        try:
            while connect_control.allow_connect():
                if self.new_conn_pool.qsize() > self.connection_pool_min:
                #if self.getter_num == 0 or self.new_conn_pool.qsize() > self.connection_pool_min:
                    break

                ip_str = ip_manager.get_gws_ip()
                if not ip_str:
                    xlog.warning("no enough ip")
                    time.sleep(10)
                    break

                ssl_sock = self._create_ssl_connection( (ip_str, 443) )
                if not ssl_sock:
                    continue

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

        ip = ip_port[0]
        port = ip_port[1]
        connect_control.start_connect_register(high_prior=True)

        time_begin = time.time()
        try:
            xlog.debug("try connect %s", ip)
            ssl_sock = check_ip.connect_ssl(ip, port=port, timeout=self.connect_timeout, on_close=ip_manager.ssl_closed)
            ip_manager.update_ip(ip, ssl_sock.handshake_time)
            xlog.debug("create_ssl update ip:%s time:%d h2:%d sni:%s top:%s",
                       ip, ssl_sock.handshake_time, ssl_sock.h2, ssl_sock.sni, ssl_sock.top_domain)
            ssl_sock.last_use_time = ssl_sock.create_time
            ssl_sock.received_size = 0
            ssl_sock.load = 0
            ssl_sock.host = self.sub + "." + ssl_sock.top_domain

            connect_control.report_connect_success()
            return ssl_sock
        except Exception as e:
            time_cost = time.time() - time_begin
            if time_cost < self.connect_timeout - 1:
                xlog.debug("connect %s fail:%s cost:%d ", ip, e, time_cost * 1000)
            else:
                xlog.debug("%s fail:%r", ip, e)

            ip_manager.report_connect_fail(ip)
            connect_control.report_connect_fail()
            if not check_local_network.is_ok():
                time.sleep(10)
            else:
                time.sleep(1)

            return False
        finally:
            connect_control.end_connect_register(high_prior=True)

    def get_ssl_connection(self, max_timeout=120):
        try:
            self.getter_num += 1

            start_time = time.time()
            while True:
                if self.new_conn_pool.qsize() < self.connection_pool_min:
                    self.create_more_connection()

                ret = self.new_conn_pool.get(True, 1)
                if ret:
                    handshake_time, ssl_sock = ret
                    if time.time() - ssl_sock.last_use_time > self.ssl_first_use_timeout:
                        # xlog.debug("new_conn_pool.get:%s handshake:%d timeout.", ssl_sock.ip, handshake_time)
                        ip_manager.report_connect_closed(ssl_sock.ip, "get_timeout")
                        ssl_sock.close()
                        continue
                    else:
                        # xlog.debug("new_conn_pool.get:%s handshake:%d", ssl_sock.ip, handshake_time)
                        return ssl_sock
                else:
                    if time.time() - start_time > max_timeout:
                        xlog.debug("create ssl timeout fail.")
                        return None
        finally:
            self.getter_num -= 1