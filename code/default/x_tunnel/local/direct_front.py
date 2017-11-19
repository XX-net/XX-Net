
# This front is for debug

import time
import threading
import collections
import simple_http_client
import random

from xlog import getLogger
xlog = getLogger("x_tunnel")

name = "direct_front"
last_success_time = time.time()
last_fail_time = 0
continue_fail_num = 0
success_num = 0
fail_num = 0
rtts = collections.deque([(0, time.time())])
rtts_lock = threading.Lock()
traffics = collections.deque()
traffics_lock = threading.Lock()
recent_sent = 0
recent_received = 0
total_sent = 0
total_received = 0


def init():
    global last_success_time, last_fail_time, continue_fail_num


def log_debug_data(rtt, sent, received):
    global recent_sent, recent_received, total_sent, total_received
    now = time.time()

    rtts.append((rtt, now))

    with traffics_lock:
        traffics.append((sent, received, now))
        recent_sent += sent
        recent_received += received
        total_sent += sent
        total_received += received


def get_rtt():
    now = time.time()

    while len(rtts) > 1:
        with rtts_lock:
            rtt, log_time = rtt_log = max(rtts)

            if now - log_time > 5:
                rtts.remove(rtt_log)
                continue

        return rtt

    return rtts[0][0]


def debug_data_clearup_thread():
    global recent_sent, recent_received
    while True:
        now = time.time()

        with rtts_lock:
            if len(rtts) > 1 and now - rtts[0][-1] > 5:
                rtts.popleft()

        with traffics_lock:
            if traffics and now - traffics[0][-1] > 60:
                sent, received, _ = traffics.popleft()
                recent_sent -= sent
                recent_received -= received

        time.sleep(0.01)


class FakeWorker():
    def update_debug_data(self, rtt, send_data_len, dlen, speed):
        pass

    def get_trace(self):
        return ""


def get_score(host=""):
    return 1


def worker_num():
    return 1


def request(method, host, schema="http", path="/", headers={}, data="", timeout=60):
    global last_success_time, last_fail_time, continue_fail_num, success_num, fail_num

    r = random.randint(0, 100)
    if r < 70:
        return "", 602, {}

    timeout = 30
    # use http to avoid cert fail
    url = "http://" + host + path
    if data:
        headers["Content-Length"] = str(len(data))

    # xlog.debug("gae_proxy %s %s", method, url)
    try:
        response = simple_http_client.request(method, url, headers, data, timeout=timeout)
        if response.status != 200:
            raise Exception("Direct request fail")
    except Exception as e:
        fail_num += 1
        continue_fail_num += 1
        last_fail_time = time.time()
        return "", 602, {}

    last_success_time = time.time()
    continue_fail_num = 0
    success_num += 1
    response.worker = FakeWorker()
    response.task = response.worker
    return response.text, response.status, response


def stop():
    pass


init()