import os

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir, os.pardir))

import env_info
import xlog

from front_base.http_dispatcher import HttpsDispatcher
from front_base.connect_manager import ConnectManager
from gae_proxy.local import check_local_network

from .config import Config
from .connect_creator import ConnectCreator

data_path = env_info.data_path
module_data_path = os.path.join(data_path, 'x_tunnel')

logger = xlog.getLogger("seley_front", log_path=module_data_path, save_start_log=1500, save_warning_log=True)
logger.set_buffer(300)

from .ip_manager import IpManager


class Front(object):
    name = "seley_front"

    def __init__(self):
        self.running = False
        self.account = ""
        self.password = ""
        self.logger = logger
        config_path = os.path.join(module_data_path, "seley_front.json")
        self.config = Config(config_path)

    def start(self):
        self.running = True
        self.connect_creator = ConnectCreator(logger, self.config)

        hosts_fn = os.path.join(module_data_path, "seley_host.json")
        ip_speed_fn = os.path.join(module_data_path, "seley_speed.json")
        self.ip_manager = IpManager(self.config, logger, hosts_fn, ip_speed_fn)

        self.connect_manager = ConnectManager(logger, self.config, self.connect_creator, self.ip_manager,
                                              check_local_network)
        self.http_dispatcher = HttpsDispatcher(logger, self.config, self.ip_manager, self.connect_manager)

    def set_x_tunnel_account(self, account, password):
        self.account = account
        self.password = password
        self.http_dispatcher.account = account

    def set_hosts(self, hosts):
        if not self.config.allow_set_hosts:
            return

        self.ip_manager.set_hosts(hosts)
        self.logger.debug("set_hosts:%s", hosts)

        self.http_dispatcher.start_connect_all_ips()

    def get_dispatcher(self, host=None):
        if len(self.ip_manager.hosts) == 0:
            return None

        return self.http_dispatcher

    def request(self, method, host, path="/", headers={}, data="", timeout=120):
        headers = dict(headers)
        headers["XX-Account"] = self.account
        headers["X-Host"] = host
        headers["X-Path"] = path

        response = self.http_dispatcher.request(method, host, "/", dict(headers), data, timeout=timeout)
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
