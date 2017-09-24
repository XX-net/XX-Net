
import threading
import Queue
import httplib

from xlog import getLogger
xlog = getLogger("gae_proxy")
import connect_control
from google_ip import google_ip
from http_common import *


class HTTP1_worker(HTTP_worker):
    version = "1.1"
    idle_time = 10 * 60

    def __init__(self, ssl_sock, close_cb, retry_task_cb, idle_cb):
        super(HTTP1_worker, self).__init__(ssl_sock, close_cb, retry_task_cb, idle_cb)

        self.last_active_time = self.ssl_sock.create_time
        self.last_request_time = self.ssl_sock.create_time
        self.task = None

        self.task_queue = Queue.Queue()
        threading.Thread(target=self.work_loop).start()
        threading.Thread(target=self.keep_alive_thread).start()

    def get_rtt_rate(self):
        return self.rtt + 100

    def request(self, task):
        self.accept_task = False
        self.task = task
        self.task_queue.put(task)

    def keep_alive_thread(self):
        ping_interval = 55.0

        while connect_control.keep_running and self.keep_running:
            time_to_ping = max(ping_interval - (time.time() - self.last_active_time), 0.2)
            time.sleep(time_to_ping)

            time_now = time.time()
            if time_now - self.last_active_time < ping_interval:
                continue

            if time_now - self.last_request_time > self.idle_time:
                self.close("idle timeout")
                return

            self.task_queue.put("ping")

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
                    # now many gvs don't support gae
                    self.accept_task = False
                    self.keep_running = False
                    if self.task is not None:
                        self.retry_task_cb(self.task)
                        self.task = None

                    google_ip.recheck_ip(self.ssl_sock.ip)
                    self.close("keep alive")
                    return
                else:
                    self.last_active_time = time.time()
                    continue

            xlog.debug("http1 get task")
            time_now = time.time()
            self.last_request_time = time_now
            self.request_task(task)

    def request_task(self, task):
        task.set_state("h1_req")

        task.headers['Host'] = self.ssl_sock.host
        request_data = 'POST /_gh/ HTTP/1.1\r\n'
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

            response = httplib.HTTPResponse(self.ssl_sock, buffering=True)
            self.ssl_sock.settimeout(100)
            response.begin()

        #except httplib.BadStatusLine as e:
        #    xlog.warn("%s _request bad status line:%r", self.ip, e)
        except Exception as e:
            xlog.warn("%s h1_request:%r", self.ip, e)
            google_ip.report_connect_closed(self.ssl_sock.ip, "request_fail")
            self.retry_task_cb(task)
            self.task = None
            self.close("request fail")
            return

        task.set_state("h1_get_head")
        body_length = int(response.getheader("Content-Length", "0"))
        task.content_length = body_length

        task.responsed = True
        response.headers = response.msg.dict
        response.worker = self
        response.task = task
        response.ssl_sock = self.ssl_sock
        task.queue.put(response)

        if body_length == 0:
            self.accept_task = True
            self.processed_tasks += 1
            return

        # read response body,
        try:
            start = 0
            end = body_length
            time_response = last_read_time = time.time()
            while True:
                if start >= end:
                    self.ssl_sock.received_size += body_length
                    time_cost = (time.time() - time_response)
                    if time_cost != 0:
                        speed = body_length / time_cost
                        task.set_state("h1_finish[SP:%d]" % speed)
                        self.report_speed(speed, body_length)
                    self.task = None
                    self.accept_task = True
                    self.idle_cb()
                    self.processed_tasks += 1
                    self.last_active_time = time.time()
                    return

                to_read = max(end - start, 65535)
                data = response.read(to_read)
                if not data:
                    if time.time() - last_read_time > 20:
                        xlog.warn("%s read timeout t:%d expect:%d left:%d ",
                                  self.ip, (time.time()-time_response)*1000, body_length, (end-start))
                        break
                    else:
                        time.sleep(0.1)
                        continue

                last_read_time = time.time()
                data_len = len(data)
                start += data_len
                task.put_data(data)

        except Exception as e:
            xlog.warn("%s h1_request:%r", self.ip, e)

        task.put_data("")
        google_ip.report_connect_closed(self.ssl_sock.ip, "down fail")
        self.close("request body fail")

    def head_request(self):
        # for keep alive

        start_time = time.time()
        # xlog.debug("head request %s", host)
        request_data = 'HEAD /_gh/ HTTP/1.1\r\nHost: %s\r\n\r\n' % self.ssl_sock.host

        try:
            data = request_data.encode()
            ret = self.ssl_sock.send(data)
            if ret != len(data):
                xlog.warn("h1 head send len:%r %d %s", ret, len(data), self.ip)
                return False
            response = httplib.HTTPResponse(self.ssl_sock, buffering=True)
            self.ssl_sock.settimeout(100)
            response.begin()

            status = response.status
            if status != 200:
                xlog.debug("%s appid:%s head fail status:%d", self.ip, self.ssl_sock.appid, status)
                return False

            self.rtt = (time.time() - start_time) * 1000
            return True
        except httplib.BadStatusLine as e:
            time_now = time.time()
            inactive_time = time_now - self.last_active_time
            head_timeout = time_now - start_time
            xlog.debug("%s keep alive fail, inactive_time:%d head_timeout:%d",
                       self.ssl_sock.ip, inactive_time, head_timeout)
        except Exception as e:
            xlog.debug("h1 %s appid:%s HEAD keep alive request fail:%r", self.ssl_sock.ip, self.ssl_sock.appid, e)

    def close(self, reason=""):
        # Notify loop to exit
        # This function may be call by out side http2
        # When gae_proxy found the appid or ip is wrong
        self.accept_task = False
        self.keep_running = False

        if self.task is not None:
            if self.task.responsed:
                self.task.put_data("")
            else:
                self.retry_task_cb(self.task)
            self.task = None

        super(HTTP1_worker, self).close(reason)
        self.task_queue.put(None)