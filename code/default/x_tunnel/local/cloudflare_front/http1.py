
import threading
import Queue
import httplib

from xlog import getLogger
xlog = getLogger("cloudflare_front")
import connect_control
from ip_manager import ip_manager
from http_common import *


class HTTP1_worker(HTTP_worker):
    version = "1.1"
    idle_time = 360

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
        ping_interval = 10

        time_to_ping = max(ping_interval - (time.time() - self.ssl_sock.create_time), 0.2)
        time.sleep(time_to_ping)

        time_now = time.time()
        if time_now - self.last_active_time > ping_interval:
            self.task_queue.put("ping")

        while connect_control.keep_running and self.keep_running:
            time_to_ping = max(ping_interval - (time.time() - self.last_active_time), 0.2)
            time.sleep(time_to_ping)

            time_now = time.time()
            if time_now - self.last_active_time > self.idle_time:
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
                # not work now.
                if not self.head_request():
                    self.accept_task = False
                    self.keep_running = False
                    if self.task is not None:
                        self.retry_task_cb(self.task)
                        self.task = None

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

            self.last_request_time = time_now
            self.last_active_time = time_now
            self.request_task(task)

    def request_task(self, task):
        start_time = time.time()
        task.set_state("h1_req")

        task.headers['Host'] = self.task.host
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

            response = httplib.HTTPResponse(self.ssl_sock, buffering=True)
            self.ssl_sock.settimeout(100)
            response.begin()

        except Exception as e:
            xlog.warn("%s h1_request:%r inactive_time:%d", self.ip, e, time.time()-self.last_active_time)
            ip_manager.report_connect_closed(self.ssl_sock.ip, "request_fail")
            self.retry_task_cb(task)
            self.task = None
            self.close("request fail")
            return

        task.set_state("h1_get_head")

        if "transfer-encoding" in response.msg:
            length = 0
            while True:
                try:
                    data = response.read(8192)
                except httplib.IncompleteRead, e:
                    data = e.partial
                except Exception as e:
                    xlog.warn("Transfer-Encoding fail, ip:%s url:%s e:%r", self.ip, task.url, e)
                    break

                if not data:
                    break
                length += len(data)
                task.put_data(data)

            task.content_length = length

            task.responsed = True
            response.headers = response.msg.dict
            response.worker = self
            response.task = task
            response.ssl_sock = self.ssl_sock
            task.queue.put(response)

            self.ssl_sock.received_size += length
            time_cost = (time.time() - start_time)
            if time_cost != 0:
                speed = length / time_cost
                task.set_state("h1_finish[SP:%d]" % speed)
            self.task = None
            self.accept_task = True
            self.idle_cb()
            self.processed_tasks += 1
            self.last_active_time = time.time()

            return

        else:

            body_length = int(response.getheader("Content-Length", 0))
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
            ip_manager.report_connect_closed(self.ssl_sock.ip, "down fail")
            self.close("request body fail")

    def head_request(self):
        # for keep alive, not work now.

        start_time = time.time()
        # xlog.debug("head request %s", self.ssl_sock.ip)
        request_data = 'GET / HTTP/1.1\r\nHost: %s\r\n\r\n' % self.ssl_sock.host

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

            content = response.read()

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