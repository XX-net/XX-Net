import time
import gae_front
import cloudflare_front.front as cloudflare_front
import heroku_front.front as heroku_front
from xlog import getLogger
xlog = getLogger("x_tunnel")

all_fronts = [gae_front, cloudflare_front.front, heroku_front.front]

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


def request(method, host, path, headers={}, data="", timeout=10):
    front = get_front(host, timeout)
    if not front:
        return "", 602, {}

    return front.request(method, host=host, path=path, headers=headers, data=data, timeout=timeout)


def stop():
    for front in all_fronts:
        front.stop()