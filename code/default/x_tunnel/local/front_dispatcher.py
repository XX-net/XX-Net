import time
import threading
import os
import random

all_fronts = []
light_fronts = []
session_fronts = []
cloudflare_front = None

from . import global_var as g
import utils
from xlog import getLogger
import env_info

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
data_path = env_info.data_path
data_xtunnel_path = os.path.join(data_path, 'x_tunnel')

xlog = getLogger("x_tunnel", log_path=data_xtunnel_path, save_start_log=500, save_warning_log=True)


def init():
    global cloudflare_front

    if g.config.enable_gae_proxy:
        from . import gae_front
        if gae_front.get_dispatcher():
            all_fronts.append(gae_front)
            session_fronts.append(gae_front)
            light_fronts.append(gae_front)

    if g.config.enable_cloudflare:
        from .cloudflare_front.front import front as _cloudflare_front
        cloudflare_front = _cloudflare_front
        all_fronts.append(cloudflare_front)
        session_fronts.append(cloudflare_front)
        light_fronts.append(cloudflare_front)
        g.cloudflare_front = cloudflare_front

    if g.config.enable_cloudfront:
        from .cloudfront_front.front import front as cloudfront_front
        all_fronts.append(cloudfront_front)
        session_fronts.append(cloudfront_front)
        light_fronts.append(cloudfront_front)
        g.cloudfront_front = cloudfront_front

    if g.config.enable_seley:
        from .seley_front.front import front as seley_front
        all_fronts.append(seley_front)
        session_fronts.append(seley_front)
        light_fronts.append(seley_front)
        g.seley_front = seley_front

    if g.config.enable_tls_relay:
        from .tls_relay_front.front import front as tls_relay_front
        all_fronts.append(tls_relay_front)
        session_fronts.append(tls_relay_front)
        light_fronts.append(tls_relay_front)
        g.tls_relay_front = tls_relay_front

    if g.config.enable_direct:
        from . import direct_front
        all_fronts.append(direct_front)
        session_fronts.append(direct_front)
        light_fronts.append(direct_front)

    for front in all_fronts:
        front.start()

    threading.Thread(target=front_staticstic_thread, name="front_statistic_thread").start()


def save_cloudflare_domain(domains):
    if not g.config.enable_cloudflare:
        xlog.warn("save_cloudflare_domain but cloudflare front not enabled")
        return

    for front in all_fronts:
        if front.name != "cloudflare_front":
            continue

        front.ip_manager.save_domains(domains)


def front_staticstic_thread():
    while g.running:
        for front in all_fronts:
            dispatcher = front.get_dispatcher()
            if not dispatcher:
                continue

            dispatcher.statistic()

        time.sleep(3)


def get_front(host, timeout):
    start_time = time.time()
    if host in ["dns.xx-net.org", g.config.api_server]:
        fronts = light_fronts
    else:
        fronts = session_fronts

    while time.time() - start_time < timeout:
        best_front = None
        best_score = 999999999
        for front in fronts:
            if host == "dns.xx-net.org" and front == cloudflare_front and g.server_host:
                # share the x-tunnel connection with dns.xx-net.org
                # x-tunnel server will forward the request to dns.xx-net.org
                host = g.server_host

            dispatcher = front.get_dispatcher(host)
            if not dispatcher:
                # xlog.warn("get dispatcher from %s fail for %s", front.name, host)
                continue

            score = dispatcher.get_score()
            if not score:
                if front.config.show_state_debug:
                    xlog.warn("get_front get_score failed for %s ", front.name)
                continue

            if score < best_score:
                best_score = score
                best_front = front

        if best_front is not None:
            return best_front

        time.sleep(1)
    g.stat["timeout_roundtrip"] += 5
    return None


def count_connection(host):
    fronts = session_fronts

    num = 0
    for front in fronts:
        dispatcher = front.get_dispatcher(host)
        if not dispatcher:
            continue

        num += len(dispatcher.workers)

        num += dispatcher.connection_manager.new_conn_pool.qsize()

    return num


def request(method, host, path="/", headers={}, data="", timeout=100):
    # xlog.debug("front request %s timeout:%d", path, timeout)
    start_time = time.time()

    content, status, response = "", 603, {}
    while time.time() - start_time < timeout:
        start_get_front = time.time()
        front = get_front(host, timeout)
        if not front:
            xlog.warn("get_front fail")
            return "", 602, {}

        finished_get_front = time.time()
        get_front_time = finished_get_front - start_get_front
        if get_front_time > 0.1:
            xlog.warn("get_front_time: %f for %s %s %s", get_front_time, method, host, path)

        if host == "dns.xx-net.org" and front == cloudflare_front and g.server_host:
            # share the x-tunnel connection with dns.xx-net.org
            # x-tunnel server will forward the request to dns.xx-net.org
            if g.server_host:
                host = g.server_host

        headers["X-Async"] = "1"
        if len(data) < 84:
            padding = utils.to_str(utils.generate_random_lowercase(random.randint(64, 256)))
            headers["Padding"] = padding

        content, status, response = front.request(
            method, host=host, path=path, headers=dict(headers), data=data, timeout=timeout)

        if status not in [200, 521, 400, 404]:
            xlog.warn("front retry %s%s", host, path)
            time.sleep(1)
            continue

        header_len = int(response.headers.get(b"Content-Length", 0))
        if header_len and len(content) != header_len:
            xlog.warn("response length incorrect, head len:%s, content len:%d retry it", header_len, len(content))
            time.sleep(1)
            continue

        return content, status, response

    return content, status, response


def stop():
    global all_fronts, light_fronts, session_fronts, cloudflare_front

    for front in all_fronts:
        front.stop()

    all_fronts = []
    light_fronts = []
    session_fronts = []
    cloudflare_front = None