
import threading
import httplib

from xlog import getLogger
xlog = getLogger("cloudflare_front")
import connect_control
from ip_manager import ip_manager
from http_common import *
import simple_http_client


class HTTP1_worker(HTTP_worker):
    version = "1.1"
    idle_time = 360

    def __init__(self, ssl_sock, close_cb, retry_task_cb, idle_cb, log_debug_data):
        super(HTTP1_worker, self).__init__(ssl_sock, close_cb, retry_task_cb, idle_cb, log_debug_data)

        self.last_active_time = self.ssl_sock.create_time
        self.last_request_time = self.ssl_sock.create_time
        self.task = None
        self.request_onway = False
        self.transfered_size = 0
        self.trace_time = []
        self.trace_time.append([ssl_sock.create_time, "connect"])
        self.record_active("init")

        self.task_queue = Queue.Queue()
        self.task_queue.put("ping")

        threading.Thread(target=self.work_loop).start()

    def record_active(self, active=""):
        self.trace_time.append([time.time(), active])
        # xlog.debug("%s stat:%s", self.ip, active)

    def get_trace(self):
        out_list = []
        last_time = self.trace_time[0][0]
        for t, stat in self.trace_time:
            time_diff = int((t - last_time) * 1000)
            last_time = t
            out_list.append(" %d:%s" % (time_diff, stat))
        out_list.append(":%d" % ((time.time() - last_time) * 1000))
        out_list.append(" processed:%d" % self.processed_tasks)
        out_list.append(" transfered:%d" % self.transfered_size)
        out_list.append(" sni:%s" % self.ssl_sock.sni)
        return ",".join(out_list)

    def get_rtt_rate(self):
        return self.rtt + 100

    def request(self, task):
        self.accept_task = False
        self.task = task
        self.task_queue.put(task)

    def keep_alive_thread(self):
        self.task_queue.put("ping")

        ping_interval = 300
        while connect_control.keep_running and self.keep_running:
            time_to_ping = max(ping_interval - (time.time() - self.last_active_time), 0.2)
            time.sleep(time_to_ping)

            time_now = time.time()
            if not self.request_onway and time_now - self.last_active_time > self.idle_time:
                self.close("idle timeout")
                return

    def work_loop(self):
        while connect_control.keep_running and self.keep_running:
            task = self.task_queue.get(True)
            if not task:
                # None task means exit
                self.accept_task = False
                self.keep_running = False
                return
            elif task == "ping":
                if not self.head_request():
                    ip_manager.recheck_ip(self.ssl_sock.ip)
                    self.close("keep alive")
                    return
                else:
                    self.last_active_time = time.time()
                    continue

            # xlog.debug("http1 get task")
            time_now = time.time()
            if time_now - self.last_active_time > 360:
                xlog.warn("get task but inactive time:%d", time_now - self.last_active_time)
                self.task = task
                self.close("inactive timeout %d" % (time_now - self.last_active_time))
                return

            self.request_task(task)
            self.request_onway = False
            self.last_request_time = time_now
            self.last_active_time = time_now

            if self.processed_tasks > 35:
                self.close("lift end.")
                return

    def request_task(self, task):
        timeout = task.timeout
        self.request_onway = True
        start_time = time.time()

        self.record_active("request")
        task.set_state("h1_req")

        task.headers['Host'] = self.ssl_sock.host
        task.headers["Content-Length"] = len(task.body)
        request_data = '%s %s HTTP/1.1\r\n' % (task.method, task.path)
        request_data += ''.join('%s: %s\r\n' % (k, v) for k, v in task.headers.items())
        request_data += '\r\n'

        try:
            self.ssl_sock.send(request_data.encode())
            payload_len = len(task.body)
            start = 0
            while start < payload_len:
                send_size = min(payload_len - start, 65535)
                sended = self.ssl_sock.send(task.body[start:start+send_size])
                start += sended

            task.set_state("h1_req_sended")

            response = simple_http_client.Response(self.ssl_sock)

            response.begin(timeout=timeout)
            task.set_state("response_begin")

        except Exception as e:
            xlog.exception("%s h1_request:%r inactive_time:%d task.timeout:%d",
                           self.ip, e, time.time()-self.last_active_time, task.timeout)
            xlog.warn('%s trace:%s', self.ip, self.get_trace())

            ip_manager.report_connect_closed(self.ip, "down fail")
            self.retry_task_cb(task)
            self.task = None
            self.close("request fail")
            return

        task.set_state("h1_get_head")

        time_left = timeout - (time.time() - start_time)

        try:
            data = response.readall(timeout=time_left)
        except Exception as e:
            xlog.exception("read fail, ip:%s, chunk:%d url:%s task.timeout:%d e:%r",
                           self.ip, response.chunked, task.url, task.timeout, e)
            xlog.warn('%s trace:%s', self.ip, self.get_trace())
            ip_manager.report_connect_closed(self.ip, "down fail")
            self.close("read fail")
            return

        response.worker = self
        response.task = task
        response.ssl_sock = self.ssl_sock

        length = len(data)
        task.content_length = length
        task.put_data(data)
        task.responsed = True
        task.queue.put(response)
        task.finish()

        self.ssl_sock.received_size += length
        time_cost = (time.time() - start_time)
        if time_cost != 0:
            speed = length / time_cost
            task.set_state("h1_finish[SP:%d]" % speed)

        self.transfered_size += len(request_data) + length
        self.task = None
        self.accept_task = True
        self.idle_cb()
        self.processed_tasks += 1
        self.last_active_time = time.time()
        self.record_active("Res")

    def head_request(self):
        # for keep alive, not work now.
        self.request_onway = True
        self.record_active("head")
        start_time = time.time()
        xlog.debug("head request %s", self.ip)
        request_data = 'GET / HTTP/1.1\r\nHost: %s\r\n\r\n' % self.ssl_sock.host

        try:
            data = request_data.encode()
            ret = self.ssl_sock.send(data)
            if ret != len(data):
                xlog.warn("h1 head send len:%r %d %s", ret, len(data), self.ip)
                xlog.warn('%s trace:%s', self.ip, self.get_trace())
                return False
            response = simple_http_client.Response(self.ssl_sock)
            response.begin(timeout=5)

            status = response.status
            if status != 200:
                xlog.warn("%s host:%s head fail status:%d", self.ip, self.ssl_sock.host, status)
                return False

            content = response.readall(timeout=5)
            self.record_active("head end")
            self.rtt = (time.time() - start_time) * 1000
            ip_manager.update_ip(self.ip, self.rtt)
            return True
        except Exception as e:
            xlog.warn("h1 %s HEAD keep alive request fail:%r", self.ssl_sock.ip, e)
            xlog.warn('%s trace:%s', self.ip, self.get_trace())
            ip_manager.report_connect_closed(self.ip, "down fail")
            self.close("head fail")
        finally:
            self.request_onway = False

    def close(self, reason=""):
        # Notify loop to exit
        # This function may be call by out side http2
        # When gae_proxy found the appid or ip is wrong
        self.accept_task = False
        self.keep_running = False

        if self.task is not None:
            if self.task.responsed:
                self.task.finish()
            else:
                self.retry_task_cb(self.task)
            self.task = None

        super(HTTP1_worker, self).close(reason)
        self.task_queue.put(None)