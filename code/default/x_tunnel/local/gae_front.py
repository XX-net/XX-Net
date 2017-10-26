import os
import sys
import time

from xlog import getLogger
xlog = getLogger("x_tunnel")

current_path = os.path.dirname(os.path.abspath(__file__))
launcher_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, "launcher"))
if launcher_path not in sys.path:
    sys.path.append(launcher_path)

try:
    from module_init import proc_handler
except:
    xlog.info("launcher not running")
    proc_handler = None

name = "gae_front"
gae_proxy = None
last_success_time = time.time()
last_fail_time = 0
continue_fail_num = 0
success_num = 0
fail_num = 0


def init():
    global last_success_time, last_fail_time, continue_fail_num, gae_proxy
    if not proc_handler:
        return False

    if "gae_proxy" not in proc_handler:
        xlog.debug("gae_proxy not running")
        return False

    gae_proxy = proc_handler["gae_proxy"]["imp"].local


def get_score(host=""):
    now = time.time()
    if now - last_fail_time < 5*60 and \
            continue_fail_num > 10:
        return None

    if not gae_proxy:
        return None

    worker = gae_proxy.http_dispatcher.http_dispatch.get_worker(nowait=True)
    if not worker:
        return None

    return worker.get_score()


def worker_num():
    if not gae_proxy:
        return 0

    return len(gae_proxy.http_dispatcher.http_dispatch.workers)


def request(method, host, schema="https", path="/", headers={}, data="", timeout=60):
    global last_success_time, last_fail_time, continue_fail_num, gae_proxy, success_num, fail_num
    if not gae_proxy:
        return "", 602, {}

    timeout = 30
    # use http to avoid cert fail
    url = "http://" + host + path
    if data:
        headers["Content-Length"] = str(len(data))

    # xlog.debug("gae_proxy %s %s", method, url)
    try:
        response = gae_proxy.gae_handler.request_gae_proxy(method, url, headers, data, timeout=timeout, retry=False)
        if response.app_status != 200:
            raise Exception("GAE request fail")
    except Exception as e:
        fail_num += 1
        continue_fail_num += 1
        last_fail_time = time.time()
        return "", 602, {}

    last_success_time = time.time()
    continue_fail_num = 0
    success_num += 1
    return response.task.read_all(), response.app_status, response


def stop():
    pass


init()