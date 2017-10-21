import time
import gae_front
from cloudflare_front.front import front as cloudflare_front
from heroku_front.front import front as heroku_front

from xlog import getLogger
xlog = getLogger("x_tunnel")

all_fronts = [gae_front, cloudflare_front, heroku_front]
# all_fronts = [cloudflare_front]

running_front_list = list(all_fronts)
current_front = running_front_list.pop(0)


def get_front(host, timeout):
    start_time = time.time()
    while time.time() - start_time < timeout:
        best_front = None
        best_score = 9999999
        for front in all_fronts:
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
    front = get_front(host, timeout)
    if not front:
        return "", 602, {}

    #headers["Content-Length"] = str(len(data))
    #if "Content-Type" not in headers:
    #    headers["Content-Type"] = "application/x-binary"
    #headers["User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36"
    #headers["Accept"] = "*/*"
    return front.request(method, host=host, path=path, headers=headers, data=data, timeout=timeout)


def stop():
    for front in all_fronts:
        front.stop()

