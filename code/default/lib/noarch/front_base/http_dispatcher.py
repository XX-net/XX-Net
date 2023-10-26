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
from six.moves import queue
import random
import operator
import threading
import time
import traceback

from utils import SimpleCondition
from queue import Queue
import utils

from . import http_common
from .http1 import Http1Worker
from .http2_connection import Http2Worker, Stream


class HttpsDispatcher(object):
    idle_time = 2 * 60

    base_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-origin",
    }

    def __init__(self, logger, config, ip_manager, connection_manager,
                 http1worker=Http1Worker,
                 http2worker=Http2Worker,
                 http2stream_class=None):
        self.logger = logger
        self.config = config
        self.ip_manager = ip_manager
        self.connection_manager = connection_manager
        self.connection_manager.set_ssl_created_cb(self.on_ssl_created_cb)

        self.http1worker = http1worker
        self.http2worker = http2worker
        if http2stream_class:
            self.http2stream_class = http2stream_class
        else:
            self.http2stream_class = Stream

        self.request_queue = Queue()
        self.workers = []
        self.working_tasks = {}
        self.account = ""
        self.last_host = None
        self.h1_num = 0
        self.h2_num = 0
        self.last_request_time = time.time()
        self.task_count_lock = threading.Lock()
        self.task_count = 0
        self.running = True

        # used by start_connect_all_ips() to control create_worker_thread()
        self.connect_all_workers = False

        # for statistic
        self.success_num = 0
        self.fail_num = 0
        self.continue_fail_num = 0
        self.last_fail_time = 0
        self.rtts = []
        self.last_sent = self.total_sent = 0
        self.last_received = self.total_received = 0
        self.second_stats = queue.deque()
        self.last_statistic_time = time.time()
        self.second_stat = {
            "rtt": 0,
            "sent": 0,
            "received": 0
        }
        self.minute_stat = {
            "rtt": 0,
            "sent": 0,
            "received": 0
        }
        self.ping_speed_ip_str_last_active = {}  # ip_str => last_active

        self.trigger_create_worker_cv = SimpleCondition()
        self.wait_a_worker_cv = SimpleCondition()

        threading.Thread(target=self.dispatcher, name="%s_dispatch" % self.logger.name).start()
        threading.Thread(target=self.create_worker_thread, name="%s_worker_creator" % self.logger.name).start()
        threading.Thread(target=self.connection_checker, name="%s_conn_checker" % self.logger.name).start()

    def stop(self):
        self.running = False
        self.request_queue.put(None)
        self.close_all_worker("stop")

    def _debug_log(self, fmt, *args, **kwargs):
        if not self.config.show_state_debug:
            return
        self.logger.debug(fmt, *args, **kwargs)

    def on_ssl_created_cb(self, ssl_sock, remove_slowest_worker=True):
        self._debug_log("on_ssl_created_cb %s", ssl_sock.ip_str)

        if not self.running:
            self.logger.info("on_ssl_created_cb %s but stopped", ssl_sock.ip_str)
            ssl_sock.close()
            return

        if not ssl_sock:
            raise Exception("on_ssl_created_cb ssl_sock None")

        if ssl_sock.h2:
            worker = self.http2worker(
                self.logger, self.ip_manager, self.config, ssl_sock,
                self.close_cb, self.retry_task_cb, self._on_worker_idle_cb, self.log_debug_data,
                stream_class=self.http2stream_class)
            self.h2_num += 1
        else:
            worker = self.http1worker(
                self.logger, self.ip_manager, self.config, ssl_sock,
                self.close_cb, self.retry_task_cb, self._on_worker_idle_cb, self.log_debug_data)
            self.h1_num += 1

        self.workers.append(worker)

        if time.time() - self.ping_speed_ip_str_last_active.get(worker.ip_str, 0) > self.config.dispather_ping_check_speed_interval:
            self.ping_speed(worker)
            self.ping_speed_ip_str_last_active[worker.ip_str] = time.time()

        elif remove_slowest_worker:
            self._remove_slowest_worker()

    def ping_speed(self, worker):
        if not self.last_host:
            return

        method = b"POST"
        path = b"/ping?content_length=%d" % self.config.dispather_ping_download_size
        body = utils.to_bytes(utils.generate_random_lowercase(self.config.dispather_ping_upload_size))
        headers = {
            b"Padding": utils.to_str(utils.generate_random_lowercase(random.randint(64, 256))),
            b"Xx-Account": self.account,
            b"X-Host": self.last_host,
            b"X-Path": path
        }

        task = http_common.Task(self.logger, self.config, method, self.last_host, path,
                                headers, body, None, "/ping", 5)
        task.set_state("start_ping_request")
        # self.logger.debug("send ping for %s", worker.ip_str)

        worker.request(task)

    def _on_worker_idle_cb(self):
        self.wait_a_worker_cv.notify()

    def create_worker_thread(self):
        while self.running:
            if not self.connect_all_workers:
                self.trigger_create_worker_cv.wait()

            if len(self.workers) == 0 and self.config.dispather_connect_all_workers_on_startup:
                self._debug_log("create_worker_thread start connect_all_workers")
                self.connect_all_workers = True

            try:
                ssl_sock = self.connection_manager.get_ssl_connection(timeout=60)
            except Exception as e:
                self._debug_log("create_worker_thread get_ssl_connection fail:%r", e)
                ssl_sock = None

            if not ssl_sock:
                self._debug_log("create_worker_thread get ssl_sock fail")
                self.connect_all_workers = False
                continue

            if self.connect_all_workers:
                self._debug_log("connect_all_workers get %s", ssl_sock.ip_str)

            try:
                self.on_ssl_created_cb(ssl_sock, remove_slowest_worker=False)
            except Exception as e:
                self.logger.exception("on_ssl_created_cb %s except:%r", ssl_sock.ip, e)
                time.sleep(10)

    def start_connect_all_ips(self):
        # trigger connect all ips
        # used in tls relay.
        self.connect_all_workers = True
        self.trigger_create_worker_cv.notify()

    def _remove_life_end_workers(self):
        to_close = []
        for worker in self.workers:
            if not worker.is_life_end():
                continue

            if worker.version == "1.1" and not worker.request_onway:
                to_close.append(worker)
                continue

            now = time.time()
            task_finished = True
            for stream_id, stream in worker.streams.items():
                if stream.task.start_time + stream.task.timeout > now:
                    task_finished = False
                    break

            if task_finished:
                to_close.append(worker)

        for worker in to_close:
            reason = worker.is_life_end()
            worker.close("life end:" + reason)
            if worker in self.workers:
                try:
                    self.workers.remove(worker)
                except:
                    pass

    def get_worker(self, nowait=False):
        # self._debug_log("start get_worker")

        while self.running:
            best_score = 99999999
            best_worker = None
            good_worker = 0
            idle_num = 0
            now = time.time()

            self._remove_life_end_workers()

            for worker in self.workers:
                if worker.is_life_end():
                    self._debug_log("life end worker: %s", worker.ip_str)
                    # self.close_cb(worker)
                    continue

                good_worker += 1

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

            if good_worker < self.config.dispather_max_workers and \
                    (best_worker is None or
                    idle_num < self.config.dispather_min_idle_workers or
                    len(self.workers) < self.config.dispather_min_workers or
                    abs(now - best_worker.last_recv_time) < self.config.dispather_work_min_idle_time or
                    best_score > self.config.dispather_work_max_score or
                     (best_worker.version == "2" and len(best_worker.streams) >= self.config.http2_target_concurrent)):

                self._debug_log("trigger get more worker")
                self.trigger_create_worker_cv.notify()

            if nowait or best_worker:
                return best_worker

            self._debug_log("wait a new worker")
            self.wait_a_worker_cv.wait(1)

    def _remove_slowest_worker(self):
        # close slowest worker,
        # give chance for better worker
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

            if idle_num < self.config.dispather_max_idle_workers or \
                    idle_num < int(len(self.workers) * 0.3) or \
                    len(self.workers) < self.config.dispather_max_workers:
                return

            if slowest_worker is None:
                return

            self.logger.debug("remove_slowest_worker remove %s", slowest_worker.ip_str)
            self.close_cb(slowest_worker)

    def request(self, method, host, path, headers, body, url=b"", timeout=60):
        method = utils.to_bytes(method)
        host = utils.to_bytes(host)
        path = utils.to_bytes(path)
        headers = utils.to_bytes(headers)
        body = utils.to_bytes(body)

        if self.task_count > self.config.max_task_num:
            self.logger.warn("task num exceed")
            time.sleep(1)
            return None

        with self.task_count_lock:
            self.task_count += 1

        self.last_host = host

        try:
            if not url:
                url = b"%s %s%s" % (method, host, path)

            self._debug_log("task start request %s" % url)

            self.last_request_time = time.time()
            q = Queue()
            task = http_common.Task(self.logger, self.config, method, host, path, headers, body, q, url, timeout)
            task.set_state("start_request")
            self.request_queue.put(task)

            try:
                response = q.get(timeout=timeout)
            except:
                response = None

            if response and response.status == 200:
                self.success_num += 1
                self.continue_fail_num = 0
                task.worker.continue_fail_tasks = 0
            else:
                self.logger.warn("task %s %s %s timeout", method, host, path)
                self.fail_num += 1
                self.continue_fail_num += 1
                self.last_fail_time = time.time()
                if task.worker:
                    # task.worker.rtt = (time.time() - task.worker.last_recv_time) * 1000

                    task.worker.continue_fail_tasks += 1
                    if task.worker.continue_fail_tasks > self.config.dispather_worker_max_continue_fail:
                        self.trigger_create_worker_cv.notify()
                else:
                    self.trigger_create_worker_cv.notify()

            task.set_state("get_response")
            return response
        except Exception as e:
            self.logger.exception("http_dispatcher:request:%r", e)
        finally:
            with self.task_count_lock:
                self.task_count -= 1

    def retry_task_cb(self, task, reason=""):
        self.fail_num += 1
        self.continue_fail_num += 1
        self.last_fail_time = time.time()
        self.logger.warn("retry_task_cb: %s, trace:%s", task.url, task.get_trace())

        if task.responsed:
            self.logger.warn("retry but responses. %s", task.url)
            st = traceback.extract_stack()
            stl = traceback.format_list(st)
            self.logger.warn("stack:%r", repr(stl))
            task.finish()
            return

        if task.retry_count > 10:
            task.response_fail("retry time exceed 10")
            return

        if time.time() - task.start_time > task.timeout:
            task.response_fail("retry timeout:%d" % (time.time() - task.start_time))
            return

        if not self.running:
            task.response_fail("retry but stopped.")
            return

        task.set_state("retry(%s)" % reason)
        task.retry_count += 1
        self.request_queue.put(task)

    def dispatcher(self):
        while self.running:
            start_time = time.time()
            try:
                task = self.request_queue.get()
            except:
                task = None

            if task is None:
                # exit
                break

            get_time = time.time()
            get_cost = get_time - start_time

            task.set_state("get_task(%d)" % get_cost)
            try:
                worker = self.get_worker()
            except Exception as e:
                self.logger.warn("get worker fail:%r", e)
                task.response_fail(reason="get worker fail:%r" % e)
                continue

            if worker is None:
                # can send because exit.
                self.logger.warn("http_dispatcher get None worker")
                task.response_fail("get worker fail.")
                continue

            get_worker_time = time.time()
            get_cost = get_worker_time - get_time
            self.ping_speed_ip_str_last_active[worker.ip_str] = get_worker_time
            task.set_state("get_worker(%d):%s" % (get_cost, worker.ip_str))
            task.worker = worker
            task.predict_rtt = worker.get_score()
            try:
                worker.request(task)
            except Exception as e:
                self.logger.exception("dispatch request:%r", e)

        # wait up threads to exit.
        self.wait_a_worker_cv.notify()
        self.trigger_create_worker_cv.notify()

    def connection_checker(self):
        while self.running:
            now = time.time()
            try:
                for worker in list(self.workers):
                    if worker.version == "1.1":
                        continue

                    worker.check_active(now)
            except Exception as e:
                self.logger.exception("check worker except:%r", e)

            time.sleep(5)

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

    def close_all_worker(self, reason="close all worker"):
        for w in list(self.workers):
            if w.accept_task:
                w.close(reason)

        self.workers = []
        self.h1_num = 0
        self.h2_num = 0

    def log_debug_data(self, rtt, sent, received):
        self.rtts.append(rtt)
        if len(self.rtts) > 30:
            self.rtts.pop(0)
        self.total_sent += sent
        self.total_received += received

    def statistic(self):
        now = time.time()
        if now > self.last_statistic_time + 60:
            rtt = 0
            sent = 0
            received = 0
            for stat in self.second_stats:
                rtt = max(rtt, stat["rtt"])
                sent += stat["sent"]
                received += stat["received"]
            self.minute_stat = {
                "rtt": rtt,
                "sent": sent,
                "received": received
            }
            self.second_stats = queue.deque()
            self.last_statistic_time = now

        if len(self.rtts):
            rtt = max(self.rtts)
        else:
            rtt = 0

        self.second_stat = {
            "rtt": rtt,
            "sent": self.total_sent - self.last_sent,
            "received": self.total_received - self.last_received
        }
        # self.rtts = []
        self.last_sent = self.total_sent
        self.last_received = self.total_received
        self.second_stats.append(self.second_stat)

    def worker_num(self):
        return len(self.workers)

    def get_score(self):
        if self.task_count >= self.config.max_task_num:
            return None

        now = time.time()
        if now - self.last_fail_time < 10 and self.continue_fail_num > 10:
            return None

        worker = self.get_worker(nowait=True)
        if not worker:
            return None

        return worker.get_score() * self.config.dispather_score_factor

    def to_string(self):
        now = time.time()
        worker_rate = {}
        for w in self.workers:
            worker_rate[w] = w.get_rtt_rate()

        w_r = sorted(list(worker_rate.items()), key=operator.itemgetter(1))

        out_str = 'thread num:%d\r\n' % threading.active_count()
        for w, r in w_r:
            out_str += "%s score:%d rtt:%d running:%d accept:%d live:%d inactive:%d processed:%d" % \
                       (w.ip_str, w.get_score(), w.rtt, w.keep_running,  w.accept_task,
                        (now-w.ssl_sock.create_time), (now-w.last_recv_time), w.processed_tasks)
            if w.version == "2":
                out_str += " continue_timeout:%d streams:%d ping_on_way:%d remote_win:%d send_queue:%d\r\n" % \
                   (w.continue_timeout, len(w.streams), w.ping_on_way, w.remote_window_size, w.send_queue.qsize())

            elif w.version == "1.1":
                out_str += " Trace:%s" % w.get_trace()

            out_str += "\r\n"

        out_str += "\r\n working_tasks:\r\n"
        for unique_id in self.working_tasks:
            task = self.working_tasks[unique_id]
            out_str += task.to_string()

        return out_str
