import os
import time
import threading
import collections
import struct

import xlog
logger = xlog.getLogger("heroku_front")
logger.set_buffer(500)

import simple_http_client
from config import Config
import host_manager
from front_base.openssl_wrap import SSLContext
from front_base.connect_creator import ConnectCreator
from front_base.ip_manager import IpManager
from front_base.http_dispatcher import HttpsDispatcher
from front_base.connect_manager import ConnectManager
from front_base.check_ip import CheckIp
from gae_proxy.local import check_local_network


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data'))
module_data_path = os.path.join(data_path, 'x_tunnel')


class Front(object):
    name = "heroku_front"

    def __init__(self):
        self.logger = logger
        config_path = os.path.join(module_data_path, "heroku_front.json")
        self.config = Config(config_path)

        ca_certs = os.path.join(current_path, "cacert.pem")
        self.host_manager = host_manager.HostManager(self.config.appids)

        openssl_context = SSLContext(logger, ca_certs=ca_certs)
        self.connect_creator = ConnectCreator(logger, self.config, openssl_context, self.host_manager)
        self.check_ip = CheckIp(xlog.null, self.config, self.connect_creator)

        ip_source = None
        default_ip_list_fn = os.path.join(current_path, "good_ip.txt")
        ip_list_fn = os.path.join(module_data_path, "heroku_ip_list.txt")
        self.ip_manager = IpManager(logger, self.config, ip_source, check_local_network,
                    self.check_ip.check_ip,
                 default_ip_list_fn, ip_list_fn, scan_ip_log=None)

        self.connect_manager = ConnectManager(logger, self.config, self.connect_creator, self.ip_manager, check_local_network)
        self.http_dispatcher = HttpsDispatcher(logger, self.config, self.ip_manager, self.connect_manager)

        self.success_num = 0
        self.fail_num = 0
        self.continue_fail_num = 0
        self.last_fail_time = 0
        self.running = True

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
        while self.running:
            now = time.time()

            with self.rtts_lock:
                if len(self.rtts) > 1 and now - self.rtts[0][-1] > 5:
                    self.rtts.popleft()

            with self.traffics_lock:
                if self.traffics and now - self.traffics[0][-1] > 60:
                    sent, received, _ = self.traffics.popleft()
                    self.recent_sent -= sent
                    self.recent_received -= received

            time.sleep(1)

    def worker_num(self):
        return len(self.http_dispatcher.workers)

    def set_ips(self, ips):
        self.ip_manager.set_ips(ips)

    def get_score(self, host=None):
        if not self.host_manager.appids:
            return None

        now = time.time()
        if now - self.last_fail_time < self.config.front_continue_fail_block and \
                self.continue_fail_num > self.config.front_continue_fail_num:
            return None

        worker = self.http_dispatcher.get_worker(nowait=True)
        if not worker:
            return None

        return worker.get_score()

    def _request(self, method, host, path="/", headers={}, data="", timeout=40):
        try:
            response = self.http_dispatcher.request(method, host, path, dict(headers), data, timeout=timeout)
            if not response:
                return "", 500, {}

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
        #p = host.find(".")
        #host_sub = host[:p]
        #host = host_sub + ".xx-net.net"

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

        heroku_host = ""
        content, status, response = self._request(
                                            "POST", heroku_host, "/2/",
                                            request_headers, request_body, timeout)

        # xlog.info('%s "PHP %s %s %s" %s %s', handler.address_string(), handler.command, url, handler.protocol_version, response.status, response.getheader('Content-Length', '-'))
        # xlog.debug("status:%d", status)
        if status == 200:
            xlog.debug("%s %s%s trace:%s", method, host, path, response.task.get_trace())
            self.last_success_time = time.time()
            self.continue_fail_num = 0
            self.success_num += 1
        else:
            if status == 404:
                heroku_host = response.ssl_sock.host
                xlog.warn("heroku:%s fail", heroku_host)
                try:
                    self.host_manager.remove(heroku_host)
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
        logger.info("terminate")
        self.connect_manager.set_ssl_created_cb(None)
        self.http_dispatcher.stop()
        self.connect_manager.stop()
        self.ip_manager.stop()

        self.running = False

    def set_proxy(self, args):
        logger.info("set_proxy:%s", args)

        self.config.PROXY_ENABLE = args["enable"]
        self.config.PROXY_TYPE = args["type"]
        self.config.PROXY_HOST = args["host"]
        self.config.PROXY_PORT = args["port"]
        self.config.PROXY_USER = args["user"]
        self.config.PROXY_PASSWD = args["passwd"]

        self.config.save()

        self.connect_creator.update_config()


front = Front()