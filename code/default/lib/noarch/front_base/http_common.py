import threading
import time
import random

from queue import Queue
import simple_http_client


class Task(object):
    def __init__(self, logger, config, method, host, path, headers, body, queue, url, timeout):
        self.logger = logger
        self.config = config
        self.method = method
        self.host = host
        self.path = path
        self.headers = headers
        self.body = body
        self.queue = queue
        self.url = url
        self.timeout = timeout
        self.start_time = time.time()
        self.unique_id = "%s:%f" % (url, self.start_time)
        self.trace_time = []
        self.body_queue = Queue()
        self.predict_rtt = 0.5
        self.body_len = 0
        self.body_readed = 0
        self.content_length = None
        self.worker = None
        self.read_buffers = []
        self.read_buffer_len = 0

        self.responsed = False
        self.finished = False
        self.retry_count = 0

    def to_string(self):
        out_str = " Task:%s\r\n" % self.url
        out_str += "   responsed:%d" % self.responsed
        out_str += "   retry_count:%d" % self.retry_count
        out_str += "   start_time:%d" % (time.time() - self.start_time)
        out_str += "   body_readed:%d\r\n" % self.body_readed
        out_str += "   Trace:%s" % self.get_trace()
        out_str += "\r\n"
        return out_str

    def put_data(self, data):
        # hyper H2
        if isinstance(data, memoryview):
            data = data.tobytes()
        self.body_queue.put(data)
        self.body_len += len(data)

    def read(self, size=None):
        # fail or cloe if return ""
        if self.body_readed == self.content_length:
            return b''

        if size:
            while self.read_buffer_len < size:
                try:
                    data = self.body_queue.get(timeout=self.timeout)
                except:
                    data = None

                if not data:
                    return b''

                self.read_buffers.append(data)
                self.read_buffer_len += len(data)

            if len(self.read_buffers[0]) == size:
                data = self.read_buffers[0]
                self.read_buffers.pop(0)
                self.read_buffer_len -= size
            elif len(self.read_buffers[0]) > size:
                data = self.read_buffers[0][:size]
                self.read_buffers[0] = self.read_buffers[0][size:]
                self.read_buffer_len -= size
            else:
                buff = bytearray(self.read_buffer_len)
                buff_view = memoryview(buff)
                p = 0
                for data in self.read_buffers:
                    buff_view[p:p + len(data)] = data
                    p += len(data)

                if self.read_buffer_len == size:
                    self.read_buffers = []
                    self.read_buffer_len = 0
                    data = buff_view.tobytes()
                else:
                    data = buff_view[:size].tobytes()

                    self.read_buffers = [buff_view[size:].tobytes()]
                    self.read_buffer_len -= size

        else:
            if self.read_buffers:
                data = self.read_buffers.pop(0)
                self.read_buffer_len -= len(data)
            else:
                try:
                    data = self.body_queue.get(timeout=self.timeout)
                except:
                    data = None

                if not data:
                    return b''

        self.body_readed += len(data)
        return data

    def read_all(self):
        if self.content_length:
            left_body = int(self.content_length) - self.body_readed

            buff = bytearray(left_body)
            buff_view = memoryview(buff)
            p = 0
            for data in self.read_buffers:
                buff_view[p:p + len(data)] = data
                p += len(data)

            self.read_buffers = []
            self.read_buffer_len = 0

            while p < left_body:
                data = self.read()
                if not data:
                    break

                buff_view[p:p + len(data)] = data[0:len(data)]
                p += len(data)

            self.body_readed += p
            return buff_view[:p].tobytes()
        else:
            out = list()
            while True:
                data = self.read()
                if not data:
                    break
                out.append(data)
            return b"".join(out)

    def set_state(self, stat):
        # for debug trace
        time_now = time.time()
        self.trace_time.append((time_now, stat))
        if self.config.show_state_debug:
            self.logger.debug("%s stat:%s", self.unique_id, stat)
        return time_now

    def get_trace(self):
        out_list = []
        last_time = self.start_time
        for t, stat in self.trace_time:
            time_diff = int((t - last_time) * 1000)
            if time_diff == 0 and "get_worker" not in stat:
                continue

            last_time = t
            out_list.append("%d:%s" % (time_diff, stat))
        out_list.append(":%d" % ((time.time() - last_time) * 1000))
        return ",".join(out_list)

    def response_fail(self, reason=""):
        if self.responsed:
            self.logger.error("http_common responsed_fail but responed.%s", self.url)
            self.put_data("")
            return

        self.responsed = True
        err_text = "response_fail:%s" % reason
        self.logger.warn("%s %s", self.url, err_text)
        res = simple_http_client.BaseResponse(body=err_text)
        res.task = self
        res.worker = self.worker
        if self.queue:
            self.queue.put(res)
        self.finish()

    def finish(self):
        if self.finished:
            return

        self.put_data("")
        self.finished = True


class HttpWorker(object):
    max_payload = 32 * 1024

    def __init__(self, logger, ip_manager, config, ssl_sock, close_cb, retry_task_cb, idle_cb, log_debug_data):
        self.logger = logger
        self.ip_manager = ip_manager
        self.config = config
        self.ssl_sock = ssl_sock
        self.handshake = ssl_sock.handshake_time * 0.001
        self.rtt = ssl_sock.handshake_time * 0.001
        self.adjust = float(ssl_sock.host_info.get("adjust", 0))
        self.streams = {}
        self.ip_str = ssl_sock.ip_str
        self.close_cb = close_cb
        self.retry_task_cb = retry_task_cb
        self.idle_cb = idle_cb
        self.log_debug_data = log_debug_data

        self._lock = threading.Lock()
        self.accept_task = True
        self.keep_running = True
        self.processed_tasks = 0
        self.continue_fail_tasks = 0
        self.rtt_history = [self.rtt,]
        self.adjust_history = []
        self.last_recv_time = self.ssl_sock.create_time
        self.last_send_time = self.ssl_sock.create_time
        self.life_end_time = self.ssl_sock.create_time + \
                             random.randint(self.config.connection_max_life, int(self.config.connection_max_life * 1.5))
        # self.logger.debug("worker.init %s %s", self.ip_str, self.ssl_sock.getsockname())

    def __str__(self):
        o = ""
        o += " ip_str: %s\r\n" % (self.ip_str)
        o += " running: %s\r\n" % (self.keep_running)
        o += " processed_tasks: %d\r\n" % (self.processed_tasks)
        o += " continue_fail_tasks: %s\r\n" % (self.continue_fail_tasks)
        o += " handshake: %f \r\n" % self.handshake
        o += " adjust: %f \r\n" % self.adjust
        o += " rtt_history: %s\r\n" % (self.rtt_history)
        o += " adjust_history: %s\r\n" % (self.adjust_history)
        if self.version != "1.1":
            o += "streams: %d\r\n" % len(self.streams)
        o += " rtt: %f\r\n" % (self.rtt)
        o += " speed: %f\r\n" % (self.ip_manager.get_speed(self.ip_str))
        o += " score: %f\r\n" % (self.get_score())
        return o

    def update_rtt(self, rtt, predict_rtt=None):
        self.rtt_history.append(rtt)
        if len(self.rtt_history) > 10:
            self.rtt_history.pop(0)
        # self.rtt = sum(self.rtt_history) / len(self.rtt_history)

        if predict_rtt:
            adjust = rtt - predict_rtt
            self.adjust_history.append(adjust)
            if len(self.adjust_history) > 10:
                self.adjust_history.pop(0)

    def update_speed(self, speed):
        self.ip_manager.update_speed(self.ip_str, speed)

    def update_debug_data(self, rtt, sent, received, speed):
        self.log_debug_data(rtt, sent, received)
        return

    def close(self, reason):
        with self._lock:
            if not self.keep_running:
                # self.logger.warn("worker %s already closed %s", self.ip_str, reason)
                return

            # self.logger.debug("worker.close %s reason:%s", self.ip_str, reason)
            self.accept_task = False
            self.keep_running = False
            self.ssl_sock.close(reason)
            if reason not in ["idle timeout", "life end"]:
                now = time.time()
                inactive_time = now - self.last_recv_time
                if inactive_time < self.config.http2_ping_min_interval:
                    self.logger.debug("%s worker close:%s inactive:%d", self.ip_str, reason, inactive_time)
            self.ip_manager.report_connect_closed(self.ssl_sock.ip_str, self.ssl_sock.sni, reason)
            self.close_cb(self)

    def __del__(self):
        # self.logger.debug("__del__ %s", self.ip_str)
        self.close("__del__")

    def get_score(self):
        # The smaller, the better

        score = self.handshake
        if self.processed_tasks == 0 and len(self.streams) == 0:
            score /= 3

        speed = self.ip_manager.get_speed(self.ip_str)
        if self.version == "1.1":
            score += self.max_payload / speed
        else:
            response_body_len = self.max_payload
            for _, stream in self.streams.items():
                if stream.response_body_len == 0:
                    response_body_len += self.max_payload
                else:
                    response_body_len += stream.response_body_len - stream.task.body_len
            score += response_body_len / speed

            score += len(self.streams) * 0.06

        if self.config.show_state_debug:
            self.logger.debug("get_score %s, speed:%f rtt:%d stream_num:%d score:%f", self.ip_str,
                          speed * 0.000001, self.rtt * 1000, len(self.streams), score)

        return score + self.adjust

    def get_host(self, task_host):
        if task_host:
            return task_host
        else:
            return self.ssl_sock.host

    def is_life_end(self):
        now = time.time()
        if now > self.life_end_time:
            return "life_end_time"
        elif now - self.last_recv_time > 230:
            return "last_recv_time"
        elif self.continue_fail_tasks > self.config.dispather_worker_max_continue_fail:
            return "continue_fail"
        elif self.processed_tasks > self.config.http2_max_process_tasks:
            return "processed_tasks"
        elif self.version == "1.1":
            if self.processed_tasks > self.config.http1_max_process_tasks:
                return "http1 max_process_tasks"
            elif now - self.last_recv_time > self.config.http1_idle_time:
                return "http1 last_recv_time"
            else:
                return False
        else:
            return False
