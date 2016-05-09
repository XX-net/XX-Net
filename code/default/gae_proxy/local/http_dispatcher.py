#!/usr/bin/env python
# coding:utf-8


"""
This file manage the ssl connection dispatcher
Include http/1.1 and http/2 workers.

create ssl socket, then run worker on ssl.
if ssl suppport http/2, run http/2 worker.

provide simple https request block api.
 caller don't need to known ip/ssl/http2/appid.

performance:
 get the fastest worker to process the request.
 sorted by rtt and pipeline task on load.
"""


import os
import time
import threading
import operator
import Queue

import socks

from config import config
from appids_manager import appid_manager
import connect_control
from connect_manager import https_manager
from http1 import HTTP1_worker
from http2_connection import HTTP2_worker
from http_common import *
from xlog import getLogger
xlog = getLogger("gae_proxy")


current_path = os.path.dirname(os.path.abspath(__file__))
g_cacertfile = os.path.join(current_path, "cacert.pem")


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


class HttpsDispatcher(object):
    min_worker_num = 20
    idle_time = 20 * 60

    def __init__(self):
        self.request_queue = Queue.Queue()
        self.workers = []
        self.h1_num = 0
        self.h2_num = 0
        self.create_worker_th = None
        self.last_request_time = time.time()
        th = threading.Thread(target=self.dispatcher)
        th.start()

        # move created ssl to worker after ssl timeout
        https_manager.set_ssl_time_handler(self.on_ssl_created_cb)

    def on_ssl_created_cb(self, ssl_sock):
        if not ssl_sock:
            raise Exception("on_ssl_created_cb ssl_sock None")

        appid = appid_manager.get_appid()
        if not appid:
            time.sleep(60)
            ssl_sock.close()
            raise GAE_Exception(1, "no appid can use")

        ssl_sock.appid = appid
        ssl_sock.host = ssl_sock.appid + ".appspot.com"

        if ssl_sock.h2:
            worker = HTTP2_worker(ssl_sock, self.close_cb, self.retry_task_cb)
            self.h2_num += 1
        else:
            worker = HTTP1_worker(ssl_sock, self.close_cb, self.retry_task_cb)
            self.h1_num += 1

        self.workers.append(worker)
        return worker

    def create_worker_thread(self):
        try:
            while True:
                ssl_sock = https_manager.get_ssl_connection()
                if not ssl_sock:
                    #xlog.warn("create_worker_thread get ssl_sock fail")
                    continue

                try:
                    self.on_ssl_created_cb(ssl_sock)
                except:
                    time.sleep(10)

                if len(self.workers) > self.min_worker_num:
                    break

        finally:
            self.create_worker_th = None

    def create_more_worker(self):
        if self.create_worker_th:
            return

        self.create_worker_th = threading.Thread(target=self.create_worker_thread)
        self.create_worker_th.start()

    def get_worker(self):
        best_rtt = 9999
        best_worker = None
        idle_num = 0
        for worker in self.workers:
            if not worker.accept_task:
                continue

            if worker.version == "1.1":
                idle_num += 1
            else:
                if len(worker.streams) == 0:
                    idle_num += 1

            rtt = worker.get_rtt_rate()

            if rtt < best_rtt:
                best_rtt = rtt
                best_worker = worker

        if idle_num == 0 or len(self.workers) < self.min_worker_num:
            self.create_more_worker()

        if best_worker:
            return best_worker

        ssl_sock = https_manager.get_ssl_connection()
        if not ssl_sock:
            raise GAE_Exception(1, "no ssl_sock")

        worker = self.on_ssl_created_cb(ssl_sock)

        return worker

    def request(self, headers, body):
        # xlog.debug("task start request")
        self.last_request_time = time.time()
        q = Queue.Queue()
        task = Task(headers, body, q)
        task.set_state("start_request")
        self.request_queue.put(task)
        response = q.get(True)
        task.set_state("get_response")
        # xlog.debug("task get response")
        return response

    def retry_task_cb(self, task):
        task.set_state("retry")
        self.request_queue.put(task)

    def retry_task(self, task):
        if time.time() - task.start_time > 180:
            task.response_fail("timeout")
        else:
            self.request_queue.put(task)

    def dispatcher(self):
        while connect_control.keep_running:
            try:
                task = self.request_queue.get(True)
            except:
                continue

            task.set_state("get_task")
            # xlog.debug("get task")
            try:
                worker = self.get_worker()
            except Exception as e:
                xlog.warn("get worker fail:%r", e)
                task.response_fail(reason="get worker fail:%r" % e)
                continue

            task.set_state("get_worker")
            # xlog.debug("get worker")
            worker.request(task)

    def is_idle(self):
        return time.time() - self.last_request_time > 20 * 60

    def close_cb(self, worker):
        try:
            self.workers.remove(worker)
            if worker.version == "2":
                self.h2_num -= 1
            else:
                self.h1_num -= 1
        except:
            pass

        if len(self.workers) == 0 and not self.is_idle():
            https_manager.create_more_connection()

    def close_all_worker(self):
        for w in self.workers:
            w.close("close all worker")

        self.workers = []
        self.h1_num = 0
        self.h2_num = 0

    def to_string(self):
        worker_rate = {}
        for w in self.workers:
            worker_rate[w] = w.get_rtt_rate()

        w_r = sorted(worker_rate.items(), key=operator.itemgetter(1))

        out_str = 'thread num:%d\r\n' % threading.activeCount()
        for w,r in w_r:
            out_str += "%s rtt:%d a:%d live:%d processed:%d" % \
                       (w.ip, w.rtt, w.accept_task, (time.time()-w.ssl_sock.create_time), w.processed_tasks)
            if w.version == "2":
                out_str += " streams:%d ping_on_way:%d\r\n" % (len(w.streams), w.ping_on_way)

            out_str += " Speed:"
            for speed in w.speed_history:
                out_str += "%d," % speed

            out_str += "\r\n"

        return out_str

http_dispatch = HttpsDispatcher()