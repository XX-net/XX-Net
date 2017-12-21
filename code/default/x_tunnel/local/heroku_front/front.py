import time
import struct
import zlib
import random
import threading
import collections

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
    name = "heroku_front"

    def __init__(self):
        self.hosts = ["xxnet4.herokuapp.com"]
        self.host = str(random.choice(self.hosts))

        self.dispatcher = http_dispatcher.HttpsDispatcher(self.host, self.log_debug_data)
        self.last_success_time = time.time()
        self.last_fail_time = 0
        self.continue_fail_num = 0
        self.success_num = 0
        self.fail_num = 0

        self.rtts = collections.deque([(0, time.time())])
        self.rtts_lock = threading.Lock()
        self.traffics = collections.deque()
        self.traffics_lock = threading.Lock()
        self.recent_sent = 0
        self.recent_received = 0
        self.total_sent = 0
        self.total_received = 0

        threading.Thread(target=self.debug_data_clearup_thread).start()

    def log_debug_data(self, rtt, sent, received):
        now = time.time()

        self.rtts.append((rtt, now))

        with self.traffics_lock:
            self.traffics.append((sent, received, now))
            self.recent_sent += sent
            self.recent_received += received
            self.total_sent += sent
            self.total_received += received

    def get_rtt(self):
        now = time.time()

        while len(self.rtts) > 1:
            with self.rtts_lock:
                rtt, log_time = rtt_log = max(self.rtts)

                if now - log_time > 5:
                    self.rtts.remove(rtt_log)
                    continue

            return rtt

        return self.rtts[0][0]

    def debug_data_clearup_thread(self):
        while True:
            now = time.time()

            with self.rtts_lock:
                if len(self.rtts) > 1 and now - self.rtts[0][-1] > 5:
                    self.rtts.popleft()

            with self.traffics_lock:
                if self.traffics and now - self.traffics[0][-1] > 60:
                    sent, received, _ = self.traffics.popleft()
                    self.recent_sent -= sent
                    self.recent_received -= received

            time.sleep(0.01)

    def get_score(self, host=None):
        now = time.time()
        if now - self.last_fail_time < 5*60 and \
                self.continue_fail_num > 10:
            return None

        if len(self.hosts) == 0:
            return None

        dispatcher = self.dispatcher
        worker = dispatcher.get_worker(nowait=True)
        if not worker:
            return None

        return worker.get_score() * 5

    def worker_num(self):
        return len(self.dispatcher.workers)

    def _request(self, method, host, path="/", header={}, data="", timeout=30):
        timeout = 40

        try:
            response = self.dispatcher.request(method, host, path, header, data, timeout=timeout)
            status = response.status
            if status != 200:
                xlog.warn("front request %s %s%s fail, status:%d", method, host, path, status)

            content = response.task.read_all()
            # xlog.debug("%s %s%s trace:%s", method, response.ssl_sock.host, path, response.task.get_trace())
            return content, status, response
        except Exception as e:
            xlog.exception("front request %s %s%s fail:%r", method, host, path, e)

            return "", 500, {}

    def request(self, method, host, schema="http", path="/", headers={}, data="", timeout=40):
        # change top domain to xx-net.net
        # this domain bypass the cloudflare front for ipv4
        p = host.find(".")
        host_sub = host[:p]
        host = host_sub + ".xx-net.net"

        schema = "http"
        # force schema to http, avoid cert fail on heroku curl.
        # and all x-server provide ipv4 access

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

        heroku_host = str(random.choice(self.hosts))
        content, status, response = self._request(
                                            "POST", heroku_host, "/2/",
                                            request_headers, request_body, timeout)

        #xlog.info('%s "PHP %s %s %s" %s %s', handler.address_string(), handler.command, url, handler.protocol_version, response.status, response.getheader('Content-Length', '-'))
        # xlog.debug("status:%d", status)
        if status == 200:
            xlog.debug("%s %s%s trace:%s", method, host, path, response.task.get_trace())
            self.last_success_time = time.time()
            self.continue_fail_num = 0
            self.success_num += 1
        else:
            if status == 404:
                xlog.warn("heroku:%s fail", heroku_host)
                try:
                    self.hosts.remove(heroku_host)
                except:
                    pass

            self.last_fail_time = time.time()
            self.continue_fail_num += 1
            self.fail_num += 1

        try:
            res = simple_http_client.TxtResponse(content)
        except:
            return "", 501, {}

        res.worker = response.worker
        res.task = response.task
        return res.body, res.status, res

    def stop(self):
        connect_control.keep_running = False


front = Front()
