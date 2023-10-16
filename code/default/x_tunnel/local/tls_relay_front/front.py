import os
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir, os.pardir))

import xlog
import env_info

from .config import Config
from . import host_manager
from . import connect_creator
from . import ip_manager
from front_base.openssl_wrap import SSLContext
from front_base.http_dispatcher import HttpsDispatcher
from front_base.connect_manager import ConnectManager
from gae_proxy.local import check_local_network
from . import http2_stream

current_path = os.path.dirname(os.path.abspath(__file__))
data_path = env_info.data_path
module_data_path = os.path.join(data_path, 'x_tunnel')

logger = xlog.getLogger("tls_relay", log_path=module_data_path, save_start_log=1500, save_warning_log=True)
logger.set_buffer(100)


class Front(object):
    name = "tls_relay_front"

    def __init__(self):
        self.running = False
        self.logger = logger
        config_path = os.path.join(module_data_path, "tls_relay.json")
        self.config = Config(config_path)

    def start(self):
        self.running = True

        self.openssl_context = SSLContext(logger)

        if not os.path.isdir(module_data_path):
            os.mkdir(module_data_path)

        host_fn = os.path.join(module_data_path, "relay_host.json")
        self.host_manager = host_manager.HostManager(host_fn)

        self.connect_creator = connect_creator.ConnectCreator(logger, self.config, self.openssl_context, self.host_manager)

        ip_speed_fn = os.path.join(module_data_path, "relay_speed.json")
        self.ip_manager = ip_manager.IpManager(self.config, self.host_manager, logger, ip_speed_fn)
        self.connect_manager = ConnectManager(logger, self.config, self.connect_creator, self.ip_manager, check_local_network)
        self.http_dispatcher = HttpsDispatcher(logger, self.config, self.ip_manager, self.connect_manager,
                                               http2stream_class=http2_stream.Stream)

        self.account = ""
        self.password = ""

    def get_dispatcher(self, host=None):
        return self.http_dispatcher

    def set_x_tunnel_account(self, account, password):
        self.account = account
        self.password = password
        self.http_dispatcher.account = account

    def set_ips(self, ips):
        if not self.config.allow_set_ips:
            return

        host_info = {}
        for ip_str in ips:
            dat = ips[ip_str]
            sni = dat["sni"]
            url_path = dat["url_path"]
            port = dat.get("port", 443)

            host_info[ip_str] = {
                "sni":sni,
                "url_path": url_path,
                "port": port,
            }

            ipv6 = dat["ipv6"]
            if ipv6:
                host_info[ipv6] = {
                    "sni": sni,
                    "url_path": url_path,
                    "port": port,
                }

        self.host_manager.set_host(host_info)
        self.logger.debug("set_ips:%s", ips)

        self.http_dispatcher.start_connect_all_ips()

    def request(self, method, host, path="/", headers={}, data="", timeout=120):
        headers = dict(headers)
        headers["XX-Account"] = self.account
        headers["X-Path"] = path

        response = self.http_dispatcher.request(method, host, path, dict(headers), data, timeout=timeout)
        if not response:
            logger.warn("req %s get response timeout", path)
            return "", 602, {}

        status = response.status

        content = response.task.read_all()
        if status == 200:
            logger.debug("%s %s%s send:%d recv:%d trace:%s", method, host, path, len(data), len(content),
                       response.task.get_trace())
        else:
            logger.warn("%s %s%s status:%d trace:%s", method, host, path, status,
                       response.task.get_trace())
        return content, status, response

    def stop(self):
        logger.info("terminate")
        self.connect_manager.set_ssl_created_cb(None)
        self.http_dispatcher.stop()
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
