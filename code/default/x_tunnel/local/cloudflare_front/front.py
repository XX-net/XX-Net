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
    def __init__(self):
        self.dispatchs = {}
        threading.Thread(target=self.update_front_domains).start()

        self.last_success_time = time.time()
        self.last_fail_time = 0
        self.continue_fail_num = 0
        self.processed_reqs = 0

    def get_score(self, host):
        if host not in self.dispatchs:
            self.dispatchs[host] = http_dispatcher.HttpsDispatcher(host)

        dispatcher = self.dispatchs[host]
        worker = dispatcher.get_worker(nowait=True)
        if not worker:
            return None

        return worker.get_score()

    def ok(self):
        if self.processed_reqs > 10:
            self.processed_reqs = 0
            return False

        now = time.time()
        if self.continue_fail_num == 0 and now - self.last_success_time < 30:
            return True

        if now - self.last_fail_time < 30 and \
            now - self.last_success_time > 30 and \
                self.continue_fail_num > 10:
            return False

        for host in self.dispatchs:
            dispatcher = self.dispatchs[host]
            if len(dispatcher.workers):
                return True
            if len(dispatcher.https_manager.new_conn_pool.pool):
                return True

        return False

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

    def __del__(self):
        connect_control.keep_running = False

    def request(self, method, host, path="/", headers={}, data="", timeout=120):
        self.processed_reqs += 1
        if host not in self.dispatchs:
            self.dispatchs[host] = http_dispatcher.HttpsDispatcher(host)

        dispatcher = self.dispatchs[host]
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = dispatcher.request(method, host, path, headers, data, timeout=timeout)
                status = response.status
                if status not in [200, 405]:
                    xlog.warn("front request %s %s%s fail, status:%d trace:%s",
                              method, host, path, status, response.task.get_trace())
                    continue

                content = response.task.read_all()
                xlog.debug("%s %s%s trace:%s", method, response.ssl_sock.host, path, response.task.get_trace())
                self.last_success_time = time.time()
                self.continue_fail_num = 0
                return content, status, response
            except Exception as e:
                xlog.warn("front request %s %s%s fail:%r", method, host, path, e)
                continue

        self.last_fail_time = time.time()
        self.continue_fail_num += 1
        return "", 500, {}

    def stop(self):
        connect_control.keep_running = False


front = Front()
