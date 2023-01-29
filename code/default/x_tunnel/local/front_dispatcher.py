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

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data'))
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

    if g.config.enable_heroku:
        from .heroku_front.front import front as heroku_front
        # all_fronts.append(heroku_front)
        light_fronts.append(heroku_front)

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

    threading.Thread(target=debug_data_clearup_thread).start()


def save_cloudflare_domain(domains):
    if not g.config.enable_cloudflare:
        xlog.warn("save_cloudflare_domain but cloudflare front not enabled")
        return

    if not domains:
        xlog.warn("save_cloudflare_domain fail, domains:%s enable:%d", domains, g.config.enable_cloudflare)
        return

    for front in all_fronts:
        if front.name != "cloudflare_front":
            continue

        front.config.update_domains = False
        front.config.save()

        front.host_manager.save_domains(domains)


def debug_data_clearup_thread():
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
                continue

            score = dispatcher.get_score()
            if not score:
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
        front = get_front(host, timeout)
        if not front:
            xlog.warn("get_front fail")
            return "", 602, {}

        if host == "dns.xx-net.org" and front == cloudflare_front and g.server_host:
            # share the x-tunnel connection with dns.xx-net.org
            # x-tunnel server will forward the request to dns.xx-net.org
            if g.server_host:
                host = g.server_host

        if len(data) < 84:
            padding = utils.to_str(utils.generate_random_lowercase(random.randint(64, 256)))
            headers["Padding"] = padding

        content, status, response = front.request(
            method, host=host, path=path, headers=dict(headers), data=data, timeout=timeout)

        if status not in [200, 521]:
            xlog.warn("front retry %s%s", host, path)
            time.sleep(1)
            continue

        return content, status, response

    return content, status, response


def stop():
    for front in all_fronts:
        front.stop()
