import os
import time
import threading
import collections

import xlog
logger = xlog.getLogger("cloudflare_front")
logger.set_buffer(500)

from config import Config
import host_manager
from front_base.openssl_wrap import SSLContext
from front_base.connect_creator import ConnectCreator
from front_base.ip_manager import IpManager
from front_base.ip_source import Ipv4RangeSource
from front_base.http_dispatcher import HttpsDispatcher
from front_base.connect_manager import ConnectManager
from front_base.check_ip import CheckIp
from http2_connection import CloudflareHttp2Worker
from gae_proxy.local import check_local_network


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data'))
module_data_path = os.path.join(data_path, 'x_tunnel')


class Front(object):
    name = "cloudflare_front"

    def __init__(self):
        self.running = True
        self.last_host = "center.xx-net.net"

        self.logger = logger
        config_path = os.path.join(module_data_path, "cloudflare_front.json")
        self.config = Config(config_path)

        ca_certs = os.path.join(current_path, "cacert.pem")
        default_domain_fn = os.path.join(current_path, "front_domains.json")
        domain_fn = os.path.join(module_data_path, "cloudflare_domains.json")
        self.host_manager = host_manager.HostManager(self.config, logger, default_domain_fn, domain_fn, self)

        openssl_context = SSLContext(logger, ca_certs=ca_certs)
        self.connect_creator = ConnectCreator(logger, self.config, openssl_context, self.host_manager)
        self.check_ip = CheckIp(xlog.null, self.config, self.connect_creator)

        ip_source = Ipv4RangeSource(
            logger, self.config,
            os.path.join(current_path, "ip_range.txt"),
            os.path.join(module_data_path, "cloudflare_ip_range.txt")
        )
        self.ip_manager = IpManager(
            logger, self.config, ip_source, check_local_network,
            self.check_ip.check_ip,
            os.path.join(current_path, "good_ip.txt"),
            os.path.join(module_data_path, "cloudflare_ip_list.txt"),
            scan_ip_log=None)

        self.connect_manager = ConnectManager(
            logger, self.config, self.connect_creator, self.ip_manager, check_local_network)

        self.dispatchs = {}

        self.success_num = 0
        self.fail_num = 0
        self.continue_fail_num = 0
        self.last_fail_time = 0

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

    def init_host_dispatcher(self, host):
        if host not in self.dispatchs:
            http_dispatcher = HttpsDispatcher(
                logger, self.config, self.ip_manager, self.connect_manager,
                http2worker=CloudflareHttp2Worker)
            self.dispatchs[host] = http_dispatcher

    def worker_num(self):
        host = self.last_host
        self.init_host_dispatcher(host)

        dispatcher = self.dispatchs[host]
        return len(dispatcher.workers)

    def get_score(self, host=None):
        now = time.time()
        if now - self.last_fail_time < 60 and \
                self.continue_fail_num > 10:
            return None

        if host is None:
            host = self.last_host

        self.init_host_dispatcher(host)

        dispatcher = self.dispatchs[host]
        worker = dispatcher.get_worker(nowait=True)
        if not worker:
            return None

        return worker.get_score() * 10

    def request(self, method, host, path="/", headers={}, data="", timeout=120):
        self.init_host_dispatcher(host)

        self.last_host = host

        dispatcher = self.dispatchs[host]
        response = dispatcher.request(method, host, path, dict(headers), data, timeout=timeout)
        if not response:
            self.logger.warn("req %s get response timeout", path)
            return "", 602, {}

        status = response.status
        if status not in [200, 405]:
            # self.logger.warn("front request %s %s%s fail, status:%d", method, host, path, status)
            self.fail_num += 1
            self.continue_fail_num += 1
            self.last_fail_time = time.time()
        else:
            self.success_num += 1
            self.continue_fail_num = 0

        content = response.task.read_all()
        if status == 200:
            self.logger.debug("%s %s%s status:%d trace:%s", method, response.worker.host, path, status,
                       response.task.get_trace())
        else:
            self.logger.warn("%s %s%s status:%d trace:%s", method, response.worker.host, path, status,
                       response.task.get_trace())
        return content, status, response

    def stop(self):
        logger.info("terminate")
        self.connect_manager.set_ssl_created_cb(None)
        for host in self.dispatchs:
            dispatcher = self.dispatchs[host]
            dispatcher.stop()
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