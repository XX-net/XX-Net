import time
import gae_front
from cloudflare_front.front import front as cloudflare_front
from heroku_front.front import front as heroku_front
all_fronts = [gae_front, cloudflare_front, heroku_front]
dns_fronts = [gae_front, cloudflare_front, heroku_front]
session_fronts = [gae_front, cloudflare_front]

# import direct_front
# all_fronts = [direct_front]

from xlog import getLogger
xlog = getLogger("x_tunnel")

running_front_list = list(all_fronts)
current_front = running_front_list.pop(0)


def get_front(host, timeout):
    start_time = time.time()
    if host in ["dns.xx-net.net"]:
        fronts = dns_fronts
    else:
        fronts = session_fronts

    while time.time() - start_time < timeout:
        best_front = None
        best_score = 9999999
        for front in fronts:
            score = front.get_score(host)
            if not score:
                continue
            if score < best_score:
                best_score = score
                best_front = front

        if best_front is not None:
            return best_front

        time.sleep(1)

    return None


def request(method, host, path="/", headers={}, data="", timeout=100):
    # xlog.debug("front request %s timeout:%d", path, timeout)
    start_time = time.time()

    content, status, response = "", 603, {}
    while time.time() - start_time < timeout:
        front = get_front(host, timeout)
        if not front:
            return "", 602, {}

        content, status, response = front.request(
            method, host=host, path=path, headers=dict(headers), data=data, timeout=timeout)

        if status not in [200, 521]:
            xlog.warn("front retry %s", path)
            continue

        return content, status, response

    return content, status, response


def stop():
    for front in all_fronts:
        front.stop()
