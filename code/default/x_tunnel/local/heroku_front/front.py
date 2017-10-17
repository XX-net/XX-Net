import time
import struct
import zlib

from xlog import getLogger
xlog = getLogger("heroku_front")
xlog.set_buffer(500)

import simple_http_client
import http_dispatcher
import connect_control


def inflate(data):
    return zlib.decompress(data, -zlib.MAX_WBITS)


def deflate(data):
    return zlib.compress(data)[2:-4]


class Front(object):
    def __init__(self):
        self.validate = 1
        self.connect_timeout = 10
        self.dispatchs = {}
        self.last_success_time = time.time()
        self.last_fail_time = 0
        self.continue_fail_num = 0

    def get_score(self, host):
        if host not in self.dispatchs:
            self.dispatchs[host] = http_dispatcher.HttpsDispatcher(host)

        dispatcher = self.dispatchs[host]
        worker = dispatcher.get_worker(nowait=True)
        if not worker:
            return None

        return worker.get_score()

    def ok(self):
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

    def __del__(self):
        connect_control.keep_running = False

    def _request(self, method, host, path="/", header={}, data="", timeout=120):
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

    def request(self, method, host, schema="https", path="/", headers={}, data="", timeout=10):
        url = schema + "://" + host + path
        payloads = ['%s %s HTTP/1.1\r\n' % (method, url)]
        for k in headers:
            v = headers[k]
            payloads.append('%s: %s\r\n' % (k, v))
        head_payload = "".join(payloads)

        request_body = '%s%s%s%s' % \
                       ((struct.pack('!H', len(head_payload)),  head_payload,
                         struct.pack('!I', len(data)), data))
        request_headers = {'Content-Length': len(data), 'Content-Type': 'application/octet-stream'}

        content, status, response = self._request(
            "POST", "xxnet10.herokuapp.com", "/2/index.php",
            request_headers, request_body, timeout)

        #xlog.info('%s "PHP %s %s %s" %s %s', handler.address_string(), handler.command, url, handler.protocol_version, response.status, response.getheader('Content-Length', '-'))
        # xlog.debug("status:%d", status)
        if status == 200:
            self.last_success_time = time.time()
            self.continue_fail_num = 0
        else:
            self.last_fail_time = time.time()
            self.continue_fail_num += 1

        try:
            res = simple_http_client.TxtResponse(content)
        except:
            return "", 501, {}

        res.worker = response.worker
        res.task = response.task
        return res.body, res.status, res


front = Front()
