import os
import sys

from xlog import getLogger
xlog = getLogger("x_tunnel")

current_path = os.path.dirname(os.path.abspath(__file__))
launcher_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, "launcher"))
if launcher_path not in sys.path:
    sys.path.append(launcher_path)

import utils

try:
    from module_init import proc_handler
except:
    xlog.info("launcher not running")
    proc_handler = None

name = "gae_front"
gae_proxy = None


def init():
    global gae_proxy
    if not proc_handler:
        return False

    if "gae_proxy" not in proc_handler:
        xlog.debug("gae_proxy not running")
        return False

    gae_proxy = proc_handler["gae_proxy"]["imp"].local


def get_dispatcher(host=None):
    if not gae_proxy:
        return None

    return gae_proxy.front.front.http_dispatcher


def request(method, host, schema="https", path="/", headers={}, data="", timeout=60):
    if not gae_proxy:
        return "", 602, {}

    method = utils.to_bytes(method)
    host = utils.to_bytes(host)
    schema = utils.to_bytes(schema)
    path = utils.to_bytes(path)
    headers = utils.to_bytes(headers)
    data = utils.to_bytes(data)

    # use http to avoid cert fail
    url = b"%s://%s%s" % (schema, host, path)
    if data:
        headers[b"Content-Length"] = bytes(str(len(data)), encoding='ascii')

    # xlog.debug("gae_proxy %s %s", method, url)
    try:
        response = gae_proxy.gae_handler.request_gae_proxy(method, url, headers, data, timeout=timeout)
        if response.app_status != 200:
            raise Exception("GAE request fail")
    except Exception as e:
        return "", 602, {}

    return response.task.read_all(), response.app_status, response


def stop():
    pass


def set_proxy(args):
    pass


init()