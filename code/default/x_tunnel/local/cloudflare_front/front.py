import time
from xlog import getLogger
xlog = getLogger("cloudflare_front")
xlog.set_buffer(500)

import http_dispatcher
import connect_control


class Front(object):
    def __init__(self):
        self.dispatchs = {}

    def __del__(self):
        connect_control.keep_running = False

    def request(self, method, host, path="/", header={}, data="", timeout=120):
        if host not in self.dispatchs:
            self.dispatchs[host] = http_dispatcher.HttpsDispatcher(host)

        dispatcher = self.dispatchs[host]
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = dispatcher.request(method, host, path, header, data)
                status = response.status
                if status not in [200, 405]:
                    xlog.warn("front request %s %s%s fail, status:%d", method, host, path, status)
                    continue
                heads = response.headers
                length = response.task.content_length

                content = response.task.read(size=length)
                xlog.debug("%s %s%s trace:%s", method, host, path, response.task.get_trace())
                return content, status, heads
            except Exception as e:
                xlog.warn("front request %s %s%s fail:%r", method, host, path, e)
                continue

        return "", 500, {}

    def stop(self):
        connect_control.keep_running = False