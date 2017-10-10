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

    def update_front_domains(self):
        client = simple_http_client.HTTP_client("raw.githubusercontent.com", use_https=True)
        path = "/XX-net/XX-Net/master/code/default/x_tunnel/local/cloudflare_front/front_domains.json"
        content, status, response = client.request("GET", path)
        if status != 200:
            xlog.warn("update front domains fail:%d", status)
            return

        front_domains_fn = os.path.join(config.DATA_PATH, "front_domains.json")
        with open(front_domains_fn, "w") as fd:
            fd.write(content)

        check_ip.update_front_domains()

    def __del__(self):
        connect_control.keep_running = False

    def request(self, method, host, path="/", header={}, data="", timeout=120):
        if host not in self.dispatchs:
            self.dispatchs[host] = http_dispatcher.HttpsDispatcher(host)

        dispatcher = self.dispatchs[host]
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = dispatcher.request(method, host, path, header, data, timeout=timeout)
                status = response.status
                if status not in [200, 405]:
                    xlog.warn("front request %s %s%s fail, status:%d", method, host, path, status)
                    continue

                content = response.task.read_all()
                xlog.debug("%s %s%s trace:%s", method, response.ssl_sock.host, path, response.task.get_trace())
                return content, status, response
            except Exception as e:
                xlog.warn("front request %s %s%s fail:%r", method, host, path, e)
                continue

        return "", 500, {}

    def stop(self):
        connect_control.keep_running = False


front = Front()
