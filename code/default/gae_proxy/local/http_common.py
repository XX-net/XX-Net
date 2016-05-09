import time
import collections
import Queue

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
        self.body_queue = Queue.Queue()
        self.body_len = 0
        self.body_readed = 0
        self.content_length = None
        self.read_buffer = ""

    def put_data(self, data):
        self.body_queue.put(data)
        self.body_len += len(data)

    def read(self, size=None):
        # fail or cloe if return ""
        if self.body_readed == self.content_length:
            return ""

        if size:
            while len(self.read_buffer) < size:
                data = self.body_queue.get(block=True)
                if not data:
                    return ""

                self.read_buffer += data

            data = self.read_buffer[:size]
            self.read_buffer = self.read_buffer[size:]
        else:
            if len(self.read_buffer):
                data = self.read_buffer
                self.read_buffer = ""
            else:
                data = self.body_queue.get(block=True)

        self.body_readed += len(data)
        return data

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

    def report_speed(self, speed, body_length):
        if body_length < 10 * 1024:
            return

        self.speed_history.append(speed)
        if len(self.speed_history) > 10:
            self.speed_history.pop(0)

    def close(self, reason):
        self.accept_task = False
        self.keep_running = False
        self.ssl_sock.close()
        xlog.debug("%s worker close:%s", self.ip, reason)
        self.close_cb(self)