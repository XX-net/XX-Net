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


import Queue
import operator
import os
import threading
import time
import traceback

from utils import SimpleCondition
from xlog import getLogger
import simple_queue

import connect_control
import http_common
import connect_manager
from http1 import HTTP1_worker
from http2_connection import HTTP2_worker

xlog = getLogger("cloudflare_front")


class HttpsDispatcher(object):
    idle_time = 20 * 60

    def __init__(self, host, log_debug_data):
        self.host = host
        self.log_debug_data = log_debug_data
        self.request_queue = Queue.Queue()
        self.workers = []
        self.working_tasks = {}
        self.h1_num = 0
        self.h2_num = 0
        self.create_worker_th = None
        self.last_request_time = time.time()

        self.triger_create_worker_cv = SimpleCondition()
        self.wait_a_worker_cv = simple_queue.Queue()

        threading.Thread(target=self.dispatcher).start()
        threading.Thread(target=self.create_worker_thread).start()

        # move created ssl to worker after ssl timeout
        self.https_manager = connect_manager.Https_connection_manager(host, self.on_ssl_created_cb)

    def on_ssl_created_cb(self, ssl_sock, check_free_work=True):
        if not ssl_sock:
            raise Exception("on_ssl_created_cb ssl_sock None")

        if ssl_sock.h2:
            worker = HTTP2_worker(ssl_sock, self.close_cb, self.retry_task_cb, self._on_worker_idle_cb, self.log_debug_data)
            self.h2_num += 1
        else:
            worker = HTTP1_worker(ssl_sock, self.close_cb, self.retry_task_cb, self._on_worker_idle_cb, self.log_debug_data)
            self.h1_num += 1

        self.workers.append(worker)

        self.wait_a_worker_cv.notify()

        if check_free_work:
            self.check_free_worker()

    def _on_worker_idle_cb(self):
        self.wait_a_worker_cv.notify()

    def create_worker_thread(self):
        while connect_control.keep_running:
            try:
                ssl_sock = self.https_manager.get_ssl_connection()
            except Exception as e:
                continue

            if not ssl_sock:
                # xlog.warn("create_worker_thread get ssl_sock fail")
                continue

            try:
                self.on_ssl_created_cb(ssl_sock, check_free_work=False)
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

            if idle_num > 1 and acceptable_num > 1:
                self.triger_create_worker_cv.wait()

    def get_worker(self, nowait=False):
        while connect_control.keep_running:
            best_score = 99999999
            best_worker = None
            idle_num = 0
            min_idle_time = 5
            now = time.time()
            for worker in self.workers:
                if not worker.accept_task:
                    continue

                if worker.version == "1.1":
                    idle_num += 1
                else:
                    if len(worker.streams) == 0:
                        idle_num += 1

                score = worker.get_score()

                if best_score > score:
                    best_score = score
                    best_worker = worker

            if best_worker is None or idle_num < 1 or (now - best_worker.last_active_time) < min_idle_time or best_score>20000:
                xlog.debug("trigger get more worker")
                self.triger_create_worker_cv.notify()

            if nowait:
                return best_worker

            if best_worker and (now - best_worker.last_active_time) > min_idle_time:
                return best_worker

            self.triger_create_worker_cv.notify()
            self.wait_a_worker_cv.wait(time.time() + 1)
            time.sleep(0.1)

    def check_free_worker(self):
        # close slowest worker,
        # give change for better worker
        while True:
            slowest_score = 9999
            slowest_worker = None
            idle_num = 0
            for worker in self.workers:
                if not worker.accept_task:
                    continue

                if worker.version == "2" and len(worker.streams) > 0:
                    continue

                score = worker.get_score()
                if score < 1000:
                    idle_num += 1

                if score > slowest_score:
                    slowest_score = score
                    slowest_worker = worker

            if idle_num < 10 or idle_num < int(len(self.workers) * 0.3) or len(self.workers) < 50:
                return

            if slowest_worker is None:
                return
            self.close_cb(slowest_worker)

    def request(self, method, host, path, headers, body, url="", timeout=60):
        # xlog.debug("task start request")
        if not url:
            url = "%s %s%s" % (method, host, path)
        self.last_request_time = time.time()
        q = simple_queue.Queue()
        task = http_common.Task(method, host, path, headers, body, q, url, timeout)
        task.set_state("start_request")
        self.request_queue.put(task)
        # self.working_tasks[task.unique_id] = task
        response = q.get(timeout=timeout)
        task.set_state("get_response")
        # del self.working_tasks[task.unique_id]
        return response

    def retry_task_cb(self, task, reason=""):
        if task.responsed:
            xlog.warn("retry but responsed. %s", task.url)
            st = traceback.extract_stack()
            stl = traceback.format_list(st)
            xlog.warn("stack:%r", repr(stl))
            task.finish()
            return

        if task.retry_count > 10:
            task.response_fail("retry time exceed 10")
            return

        if time.time() - task.start_time > task.timeout:
            task.response_fail("retry timeout:%d" % (time.time() - task.start_time))
            return

        task.set_state("retry(%s)" % reason)
        task.retry_count += 1
        self.request_queue.put(task)

    def dispatcher(self):
        while connect_control.keep_running:
            start_time = time.time()
            try:
                task = self.request_queue.get(True)
                if task is None:
                    # exit
                    break
            except Exception as e:
                xlog.exception("http_dispatcher dispatcher request_queue.get fail:%r", e)
                continue
            get_time = time.time()
            get_cost = get_time - start_time

            task.set_state("get_task(%d)" % get_cost)
            try:
                worker = self.get_worker()
            except Exception as e:
                xlog.warn("get worker fail:%r", e)
                task.response_fail(reason="get worker fail:%r" % e)
                continue

            if worker is None:
                # can send because exit.
                xlog.warn("http_dispatcher get None worker")
                task.response_fail("get worker fail.")
                continue

            get_worker_time = time.time()
            get_cost = get_worker_time - get_time
            task.set_state("get_worker(%d):%s" % (get_cost, worker.ip))
            task.worker = worker
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
        now = time.time()
        worker_rate = {}
        for w in self.workers:
            worker_rate[w] = w.get_rtt_rate()

        w_r = sorted(worker_rate.items(), key=operator.itemgetter(1))

        out_str = 'thread num:%d\r\n' % threading.activeCount()
        for w, r in w_r:
            out_str += "%s rtt:%d a:%d live:%d inactive:%d processed:%d" % \
                       (w.ip, w.rtt, w.accept_task, (now-w.ssl_sock.create_time), (now-w.last_active_time), w.processed_tasks)
            if w.version == "2":
                out_str += " streams:%d ping_on_way:%d\r\n" % (len(w.streams), w.ping_on_way)

            elif w.version == "1.1":
                out_str += " Trace:%s" % w.get_trace()

            out_str += "\r\n Speed:"
            for speed in w.speed_history:
               out_str += "%d," % speed

            out_str += "\r\n"

        out_str += "\r\n working_tasks:\r\n"
        for unique_id in self.working_tasks:
            task = self.working_tasks[unique_id]
            out_str += task.to_string()

        return out_str
