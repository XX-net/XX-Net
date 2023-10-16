import os

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir, os.pardir))

import env_info
import xlog

from .config import Config
from . import ip_manager
from front_base.openssl_wrap import SSLContext
from front_base.connect_creator import ConnectCreator
from front_base.ip_source import Ipv4RangeSource, Ipv6PoolSource, IpCombineSource
from front_base.http_dispatcher import HttpsDispatcher
from front_base.connect_manager import ConnectManager
from front_base.check_ip import CheckIp
from .http2_connection import CloudflareHttp2Worker
from gae_proxy.local import check_local_network

data_path = env_info.data_path
module_data_path = os.path.join(data_path, 'x_tunnel')

logger = xlog.getLogger("cloudflare_front", log_path=module_data_path, save_start_log=1500, save_warning_log=True)
logger.set_buffer(300)


class Front(object):
    name = "cloudflare_front"

    def __init__(self):
        self.running = False
        self.logger = logger
        config_path = os.path.join(module_data_path, "cloudflare_front.json")
        self.config = Config(config_path)
        self.light_config = Config(config_path)
        self.light_config.dispather_min_idle_workers = 0
        self.light_config.dispather_min_workers = 1
        self.light_config.dispather_max_workers = 1
        self.light_config.max_good_ip_num = 10

    def start(self):
        self.running = True
        self.last_host = "center.xx-net.org"

        ca_certs = os.path.join(current_path, "cacert.pem")
        default_domain_fn = os.path.join(current_path, "front_domains.json")
        domain_fn = os.path.join(module_data_path, "cloudflare_domains.json")
        ip_speed_fn = os.path.join(module_data_path, "cloudflare_speed.json")
        self.ip_manager = ip_manager.IpManager(self.config, default_domain_fn, domain_fn, ip_speed_fn, self.logger)

        openssl_context = SSLContext(logger, ca_certs=ca_certs)
        self.connect_creator = ConnectCreator(logger, self.config, openssl_context, None)
        self.check_ip = CheckIp(xlog.null, self.config, self.connect_creator)

        self.ipv4_source = Ipv4RangeSource(
            logger, self.config,
            os.path.join(current_path, "ip_range.txt"),
            os.path.join(module_data_path, "cloudflare_ip_range.txt")
        )
        self.ipv6_source = Ipv6PoolSource(
            logger, self.config,
            os.path.join(current_path, "ipv6_list.txt")
        )
        self.ip_source = IpCombineSource(
            logger, self.config,
            self.ipv4_source, self.ipv6_source
        )

        self.connect_manager = ConnectManager(
            logger, self.config, self.connect_creator, self.ip_manager, check_local_network)

        self.dispatchs = {}

    def get_dispatcher(self, host=None):
        if not host:
            host = self.last_host
        else:
            self.last_host = host

        if host not in self.dispatchs:
            if host in ["center.xx-net.org", "dns.xx-net.org"]:
                config = self.light_config
            else:
                config = self.config

            http_dispatcher = HttpsDispatcher(
                logger, config, self.ip_manager, self.connect_manager,
                http2worker=CloudflareHttp2Worker)
            self.dispatchs[host] = http_dispatcher

        dispatcher = self.dispatchs[host]
        return dispatcher

    def request(self, method, host, path="/", headers={}, data="", timeout=120):
        dispatcher = self.get_dispatcher(host)
        response = dispatcher.request(method, host, path, dict(headers), data, timeout=timeout)
        if not response:
            self.logger.warn("req %s get response timeout", path)
            return "", 602, {}

        status = response.status
        content = response.task.read_all()
        if status == 200:
            logger.debug("%s %s%s send:%d recv:%d trace:%s", method, host, path, len(data), len(content),
                       response.task.get_trace())
        else:
            self.logger.warn("%s %s%s status:%d trace:%s", method, response.worker.ssl_sock.host, path, status,
                       response.task.get_trace())
        return content, status, response

    def stop(self):
        logger.info("terminate")
        self.connect_manager.set_ssl_created_cb(None)
        for host in self.dispatchs:
            dispatcher = self.dispatchs[host]
            dispatcher.stop()
        self.connect_manager.stop()

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