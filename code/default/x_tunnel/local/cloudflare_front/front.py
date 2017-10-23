import time
import os
import threading
from xlog import getLogger
xlog = getLogger("cloudflare_front")
xlog.set_buffer(500)
import simple_http_client
from config import config

import http_dispatcher
import connect_control
import check_ip


class Front(object):
    name = "cloudflare_front"

    def __init__(self):
        self.dispatchs = {}
        threading.Thread(target=self.update_front_domains).start()
        self.last_success_time = time.time()
        self.last_fail_time = 0
        self.continue_fail_num = 0
        self.success_num = 0
        self.fail_num = 0
        self.last_host = "center.xx-net.net"

    @staticmethod
    def update_front_domains():
        next_update_time = time.time()
        while connect_control.keep_running:
            if time.time() < next_update_time:
                time.sleep(4)
                continue

            try:
                client = simple_http_client.HTTP_client("raw.githubusercontent.com", use_https=True)
                path = "/XX-net/XX-Net/master/code/default/x_tunnel/local/cloudflare_front/front_domains.json"
                content, status, response = client.request("GET", path)
                if status != 200:
                    xlog.warn("update front domains fail:%d", status)
                    raise Exception("status:%r", status)

                front_domains_fn = os.path.join(config.DATA_PATH, "front_domains.json")
                if os.path.exists(front_domains_fn):
                    with open(front_domains_fn, "r") as fd:
                        old_content = fd.read()
                        if content != old_content:
                            with open(front_domains_fn, "w") as fd:
                                fd.write(content)
                            check_ip.update_front_domains()

                next_update_time = time.time() + (4 * 3600)
                xlog.info("updated cloudflare front domains from github.")
            except Exception as e:
                next_update_time = time.time() + (1800)
                xlog.debug("updated cloudflare front domains from github fail:%r", e)

    def worker_num(self):
        host = self.last_host
        if host not in self.dispatchs:
            self.dispatchs[host] = http_dispatcher.HttpsDispatcher(host)

        dispatcher = self.dispatchs[host]
        return len(dispatcher.workers)

    def get_score(self, host=None):
        now = time.time()
        if now - self.last_fail_time < 5*60 and \
                self.continue_fail_num > 10:
            return None

        if host is None:
            host = self.last_host

        if host not in self.dispatchs:
            self.dispatchs[host] = http_dispatcher.HttpsDispatcher(host)

        dispatcher = self.dispatchs[host]
        worker = dispatcher.get_worker(nowait=True)
        if not worker:
            return None

        return worker.get_score()

    def request(self, method, host, path="/", headers={}, data="", timeout=120):
        if host not in self.dispatchs:
            self.dispatchs[host] = http_dispatcher.HttpsDispatcher(host)

        self.last_host = host

        dispatcher = self.dispatchs[host]
        response = dispatcher.request(method, host, path, headers, data, timeout=timeout)
        status = response.status
        if status not in [200, 405]:
            # xlog.warn("front request %s %s%s fail, status:%d", method, host, path, status)
            self.fail_num += 1
            self.continue_fail_num += 1
            self.last_fail_time = time.time()
        else:
            self.success_num += 1
            self.continue_fail_num = 0

        content = response.task.read_all()
        if status == 200:
            xlog.debug("%s %s%s status:%d trace:%s", method, response.worker.ssl_sock.host, path, status,
                       response.task.get_trace())
        else:
            xlog.warn("%s %s%s status:%d trace:%s", method, response.worker.ssl_sock.host, path, status,
                       response.task.get_trace())
        return content, status, response

    def stop(self):
        connect_control.keep_running = False


front = Front()
