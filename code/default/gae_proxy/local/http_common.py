import time
import collections

from xlog import getLogger
xlog = getLogger("gae_proxy")


class ReadBuffer(object):
    def __init__(self, buf, begin=0, size=None):
        buf_len = len(buf)
        if size is None:
            if begin > buf_len:
                raise Exception("ReadBuffer buf_len:%d, start:%d" % (buf_len, begin))
            size = buf_len - begin
        elif begin + size > buf_len:
            raise Exception("ReadBuffer buf_len:%d, start:%d len:%d" % (buf_len, begin, size))

        self.size = size
        self.buf = buf
        self.begin = begin

    def __len__(self):
        return self.size

    def get(self, size=None):
        if size is None:
            size = self.size
        elif size > self.size:
            raise Exception("ReadBuffer get %d but left %d" % (size, self.size))

        data = self.buf[self.begin:self.begin + size]
        self.begin += size
        self.size -= size
        return data

    def get_buf(self, size=None):
        if size is None:
            size = self.size
        elif size > self.size:
            raise Exception("ReadBuffer get %d but left %d" % (size, self.size))

        buf = ReadBuffer(self.buf, self.begin, size)

        self.begin += size
        self.size -= size
        return buf


class GAE_Exception(Exception):
    def __init__(self, type, message):
        xlog.debug("GAE_Exception %r %r", type, message)
        self.type = type
        self.message = message


class BaseResponse(object):
    def __init__(self, status=601, reason="", headers={}, body=""):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = ReadBuffer(body)


class Task(object):
    def __init__(self, headers, body, queue):
        self.headers = headers
        self.body = body
        self.queue = queue
        self.start_time = time.time()
        self.trace_time = {}

    def set_state(self, stat):
        time_now = time.time()
        self.trace_time[time_now] = stat
        return time_now

    def get_trace(self):
        tr_list = collections.OrderedDict(sorted(self.trace_time.items()))
        out_list = []
        last_time = self.start_time
        for t, stat in tr_list.items():
            time_diff = int((t - last_time) * 1000)
            last_time = t
            if time_diff > 1:
                out_list.append("%s:%d" % (stat, time_diff))
        return ",".join(out_list)

    def response_fail(self, reason=""):
        err_text = "response_fail:%s" % reason
        xlog.debug(err_text)
        res = BaseResponse(body=err_text)
        self.queue.put(res)


class HTTP_worker(object):
    def __init__(self, ssl_sock, close_cb, retry_task_cb):
        self.ssl_sock = ssl_sock
        self.init_rtt = ssl_sock.handshake_time / 3
        self.rtt = self.init_rtt
        self.ip = ssl_sock.ip
        self.close_cb = close_cb
        self.retry_task_cb = retry_task_cb
        self.accept_task = True
        self.keep_running = True
        self.processed_tasks = 0
        self.speed_history = []

    def report_speed(self, speed):
        self.speed_history.append(speed)
        if len(self.speed_history) > 10:
            self.speed_history.pop(0)

    def close(self, reason):
        self.accept_task = False
        self.keep_running = False
        self.ssl_sock.close()
        xlog.debug("%s worker close:%s", self.ip, reason)
        self.close_cb(self)