
import threading
import Queue
import httplib

from xlog import getLogger
xlog = getLogger("gae_proxy")
import connect_control
from google_ip import google_ip
from http_common import *
from config import config


class HTTP1_worker(HTTP_worker):
    version = "1.1"
    idle_time = 10 * 60

    def __init__(self, ssl_sock, close_cb, retry_task_cb):
        super(HTTP1_worker, self).__init__(ssl_sock, close_cb, retry_task_cb)

        self.last_active_time = self.ssl_sock.create_time
        self.last_request_time = self.ssl_sock.create_time

        self.task_queue = Queue.Queue()
        threading.Thread(target=self.work_loop).start()
        threading.Thread(target=self.keep_alive_thread).start()

    def get_rtt_rate(self):
        return self.rtt

    def request(self, task):
        self.accept_task = False
        self.task_queue.put(task)

    def keep_alive_thread(self):
        ping_interval = 55

        while connect_control.keep_running and self.keep_running:
            time_to_ping = max(ping_interval - (time.time() - self.last_active_time), 0)
            time.sleep(time_to_ping)

            time_now = time.time()
            if time_now - self.last_active_time < ping_interval:
                continue

            if time_now - self.last_request_time > self.idle_time:
                self.close("idle timeout")
                return

            self.last_active_time = time_now
            self.task_queue.put("ping")

    def work_loop(self):
        while connect_control.keep_running and self.keep_running:
            task = self.task_queue.get(True)
            if not task:
                # None task to exit
                return
            elif task == "ping":
                self.last_active_time = time.time()
                if not self.head_request():
                    # now many gvs don't support gae
                    google_ip.recheck_ip(self.ssl_sock.ip)
                    self.close("keep alive")
                    return
                else:
                    continue

            # xlog.debug("http1 get task")
            time_now = time.time()
            self.last_request_time = time_now
            self.last_active_time = time_now
            self.request_task(task)

    def request_task(self, task):
        headers = task.headers
        payload = task.body

        headers['Host'] = self.ssl_sock.host

        response = self._request(headers, payload)
        if not response:
            google_ip.report_connect_closed(self.ssl_sock.ip, "request_fail")
            self.retry_task_cb(task)
            self.close("request fail")
        else:
            # xlog.debug("http1 finished task")
            task.queue.put(response)
            self.accept_task = True
            self.processed_tasks += 1

    def _request(self, headers, payload):
        request_data = 'POST /_gh/ HTTP/1.1\r\n'
        request_data += ''.join('%s: %s\r\n' % (k, v) for k, v in headers.items())
        request_data += '\r\n'

        try:
            self.ssl_sock.send(request_data.encode())
            payload_len = len(payload)
            start = 0
            while start < payload_len:
                send_size = min(payload_len - start, 65535)
                sended = self.ssl_sock.send(payload[start:start+send_size])
                start += sended

            response = httplib.HTTPResponse(self.ssl_sock, buffering=True)
            self.ssl_sock.settimeout(100)
            response.begin()

            # read response body,
            body_length = int(response.getheader("Content-Length", "0"))
            start = 0
            end = body_length - 1
            last_read_time = time.time()
            time_response = time.time()
            response_body = []
            while True:
                if start > end:
                    self.ssl_sock.received_size += body_length
                    response.headers = response.msg.dict
                    response.body = ReadBuffer(b''.join(response_body))
                    response.ssl_sock = self.ssl_sock
                    response.worker = self
                    return response

                data = response.read(65535)
                if not data:
                    if time.time() - last_read_time > 20:
                        google_ip.report_connect_closed(self.ssl_sock.ip, "down fail")
                        response.close()
                        xlog.warn("%s read timeout t:%d len:%d left:%d ",
                                  self.ip, (time.time()-time_response)*1000, body_length, (end-start))
                        return False
                    else:
                        time.sleep(0.1)
                        continue

                last_read_time = time.time()
                data_len = len(data)
                start += data_len
                response_body.append(data)

        except httplib.BadStatusLine as e:
            xlog.warn("%s _request bad status line:%r", self.ip, e)
            pass
        except Exception as e:
            xlog.warn("%s _request:%r", self.ip, e)
        return False

    def head_request(self):
        # for keep alive

        start_time = time.time()
        # xlog.debug("head request %s", host)
        request_data = 'HEAD /_gh/ HTTP/1.1\r\nHost: %s\r\n\r\n' % self.ssl_sock.host

        try:
            data = request_data.encode()
            ret = self.ssl_sock.send(data)
            if ret != len(data):
                xlog.warn("head send len:%r %d", ret, len(data))
            response = httplib.HTTPResponse(self.ssl_sock, buffering=True)
            self.ssl_sock.settimeout(100)
            response.begin()

            status = response.status
            if status != 200:
                xlog.debug("appid:%s head fail status:%d", self.ssl_sock.appid, status)
                return False

            self.rtt = (time.time() - start_time) * 1000
            return True
        except httplib.BadStatusLine as e:
            time_now = time.time()
            inactive_time = time_now - self.ssl_sock.last_use_time
            head_timeout = time_now - start_time
            xlog.warn("%s keep alive fail, inactive_time:%d head_timeout:%d",
                       self.ssl_sock.ip, inactive_time, head_timeout)
        except Exception as e:
            xlog.exception("%s head appid:%s request fail:%r", self.ssl_sock.ip, self.ssl_sock.appid, e)

    def close(self, reason=""):
        # Notify loop to exit
        # This function may be call by out side http2
        # When gae_proxy found the appid or ip is wrong

        super(HTTP1_worker, self).close(reason)
        self.task_queue.put(None)