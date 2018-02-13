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
import traceback

from utils import SimpleCondition
from appids_manager import appid_manager
import connect_control
from connect_manager import https_manager
from http1 import HTTP1_worker
from http2_connection import HTTP2_worker
import http_common
import simple_queue
from xlog import getLogger
xlog = getLogger("gae_proxy")


current_path = os.path.dirname(os.path.abspath(__file__))
g_cacertfile = os.path.join(current_path, "cacert.pem")


class HttpsDispatcher(object):
    idle_time = 20 * 60

    def __init__(self):
        self.request_queue = Queue.Queue()
        self.workers = []
        self.working_tasks = {}
        self.h1_num = 0
        self.h2_num = 0
        self.create_worker_th = None
        self.last_request_time = time.time()

        self.triger_create_worker_cv = SimpleCondition()
        self.wait_a_worker_cv = SimpleCondition()

        threading.Thread(target=self.dispatcher).start()
        threading.Thread(target=self.create_worker_thread).start()

        # move created ssl to worker after ssl timeout
        https_manager.set_ssl_time_handler(self.on_ssl_created_cb)

    def on_ssl_created_cb(self, ssl_sock, check_free_worke=True):
        if not ssl_sock:
            raise Exception("on_ssl_created_cb ssl_sock None")

        appid = appid_manager.get_appid()
        if not appid:
            time.sleep(60)
            ssl_sock.close()
            raise http_common.GAE_Exception(1, "no appid can use")

        ssl_sock.appid = appid
        ssl_sock.host = ssl_sock.appid + ".appspot.com"

        if ssl_sock.h2:
            worker = HTTP2_worker(ssl_sock, self.close_cb, self.retry_task_cb, self._on_worker_idle_cb, self.log_debug_data)
            self.h2_num += 1
        else:
            worker = HTTP1_worker(ssl_sock, self.close_cb, self.retry_task_cb, self._on_worker_idle_cb, self.log_debug_data)
            self.h1_num += 1

        self.workers.append(worker)

        self.wait_a_worker_cv.notify()

        if check_free_worke:
            self.check_free_worker()

    def log_debug_data(self, rtt, sent, received):
        pass

    def _on_worker_idle_cb(self):
        self.wait_a_worker_cv.notify()

    def create_worker_thread(self):
        while connect_control.keep_running:
            try:
                ssl_sock = https_manager.get_ssl_connection()
            except Exception as e:
                continue

            if not ssl_sock:
                # xlog.warn("create_worker_thread get ssl_sock fail")
                continue

            try:
                self.on_ssl_created_cb(ssl_sock, check_free_worke=False)
            except:
                time.sleep(10)

            idle_num = 0
            acceptable_num = 0
            for worker in self.workers:
                if worker.accept_task:
                    acceptable_num += 1

                if worker.version == "1.1":
                    if worker.accept_task:
                        idle_num += 1
                else:
                    if len(worker.streams) == 0:
                        idle_num += 1

            if idle_num > 5 and acceptable_num > 20:
                self.triger_create_worker_cv.wait()

    def get_worker(self, nowait=False):
        while connect_control.keep_running:
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

                rtt = worker.get_score()

                if rtt < best_rtt:
                    best_rtt = rtt
                    best_worker = worker

            if idle_num < 5 or best_rtt > 1000:
                self.triger_create_worker_cv.notify()

            if best_worker or nowait:
                return best_worker

            self.wait_a_worker_cv.wait()

    def check_free_worker(self):
        # close slowest worker,
        # give change for better worker
        while True:
            slowest_rtt = 9999
            slowest_worker = None
            idle_num = 0
            for worker in self.workers:
                if not worker.accept_task:
                    continue

                if worker.version == "2" and len(worker.streams) > 0:
                    continue

                idle_num += 1

                rtt = worker.get_score()

                if rtt > slowest_rtt:
                    slowest_rtt = rtt
                    slowest_worker = worker

            if idle_num < 30 or idle_num < int(len(self.workers) * 0.3):
                return

            if slowest_worker is None:
                return
            self.close_cb(slowest_worker)

    def request(self, headers, body, url, timeout):
        # xlog.debug("task start request:%s timeout:%d", url, timeout)
        self.last_request_time = time.time()
        q = simple_queue.Queue()
        task = http_common.Task(headers, body, q, url, timeout)
        task.set_state("start_request")
        self.request_queue.put(task)
        response = q.get(timeout=timeout)
        task.set_state("get_response")
        return response

    def retry_task_cb(self, task):
        if task.responsed:
            xlog.warn("retry but responsed. %s", task.url)
            st = traceback.extract_stack()
            stl = traceback.format_list(st)
            xlog.warn("stack:%r", repr(stl))
            task.put_data("")
            return

        if task.retry_count > 10:
            task.response_fail("retry time exceed 10")
            return

        if time.time() - task.start_time > 240:
            task.response_fail("retry timeout:%d" % (time.time() - task.start_time))
            return

        task.set_state("retry")
        task.retry_count += 1
        self.request_queue.put(task)

    def dispatcher(self):
        while connect_control.keep_running:
            try:
                task = self.request_queue.get(True)
                if task is None:
                    # exit
                    break
            except Exception as e:
                xlog.exception("http_dispatcher dispatcher request_queue.get fail:%r", e)
                continue

            task.set_state("get_task")
            try:
                worker = self.get_worker()
            except Exception as e:
                xlog.warn("get worker fail:%r", e)
                task.response_fail(reason="get worker fail:%r" % e)
                continue

            if worker is None:
                # can send because exit.
                xlog.warn("http_dispatcher get None worker")
                continue

            task.set_state("get_worker:%s" % worker.ip)
            try:
                worker.request(task)
            except Exception as e:
                xlog.exception("dispatch request:%r", e)

        # wait up threads to exit.
        self.wait_a_worker_cv.notify()
        self.triger_create_worker_cv.notify()

    def is_idle(self):
        return time.time() - self.last_request_time > self.idle_time

    def close_cb(self, worker):
        try:
            self.workers.remove(worker)
            if worker.version == "2":
                self.h2_num -= 1
            else:
                self.h1_num -= 1
        except:
            pass

    def close_all_worker(self):
        for w in self.workers:
            w.close("close all worker")

        self.workers = []
        self.h1_num = 0
        self.h2_num = 0

    def to_string(self):
        worker_rate = {}
        for w in self.workers:
            worker_rate[w] = w.get_score()

        w_r = sorted(worker_rate.items(), key=operator.itemgetter(1))

        out_str = 'thread num:%d\r\n' % threading.activeCount()
        for w, r in w_r:
            out_str += "%s rtt:%d a:%d live:%d processed:%d" % \
                       (w.ip, w.rtt, w.accept_task, (time.time()-w.ssl_sock.create_time), w.processed_tasks)
            if w.version == "2":
                out_str += " streams:%d ping_on_way:%d\r\n" % (len(w.streams), w.ping_on_way)

            out_str += " Speed:"
            for speed in w.speed_history:
                out_str += "%d," % speed

            out_str += "\r\n"

        out_str += "\r\n<br> working_tasks:\r\n"
        for unique_id in self.working_tasks:
            task = self.working_tasks[unique_id]
            out_str += task.to_string()

        return out_str

http_dispatch = HttpsDispatcher()