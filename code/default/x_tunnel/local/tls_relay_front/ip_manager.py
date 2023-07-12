import random

import utils
from front_base.ip_manager import IpManagerBase


class IpManager(IpManagerBase):
    def __init__(self, config, host_manager, logger):
        super(IpManager, self).__init__(config, None, logger)
        self.host_manager = host_manager
        self.ip_dict = {}

    def _get_ip_info(self, ip):
        self.ip_dict.setdefault(ip, {
            "fail_times": 0,
            "links": 0,
        })
        return self.ip_dict[ip]

    def get_ip_sni_host(self):
        ips = self.host_manager.ips

        for _ in range(len(ips)):
            ip = random.choice(ips)
            info = self._get_ip_info(ip)
            if info["links"] < 0:
                info["links"] = 0

            if info["links"] >= self.config.max_links_per_ip:
                continue

            port = self.host_manager.info[ip].get("port", 443)
            if ":" in ip:
                ip = "[" + ip + "]"

            info["links"] += 1
            self.logger.debug("get ip:%s", ip)

            return ip + ":" + str(port), None, None

        return None, None, None

    def update_ip(self, ip_str, sni, handshake_time):
        ip, _ = utils.get_ip_port(ip_str)
        ip = utils.to_str(ip)
        info = self._get_ip_info(ip)
        info["fail_times"] = 0
        self.logger.debug("ip %s connect success", ip)

    def report_connect_fail(self, ip_str, sni=None, reason="", force_remove=False):
        ip, _ = utils.get_ip_port(ip_str)
        ip = utils.to_str(ip)
        info = self._get_ip_info(ip)
        info["fail_times"] += 1
        info["links"] -= 1
        self.logger.debug("ip %s connect fail:%s", ip, reason)

    def ssl_closed(self, ip_str, sni=None, reason=""):
        ip, _ = utils.get_ip_port(ip_str)
        ip = utils.to_str(ip)
        info = self._get_ip_info(ip)
        info["links"] -= 1
        self.logger.debug("ip %s ssl_closed:%s", ip, reason)

    def report_connect_closed(self, ip_str, sni=None, reason=""):
        ip, _ = utils.get_ip_port(ip_str)
        ip = utils.to_str(ip)
        info = self._get_ip_info(ip)
        info["links"] -= 1
        self.logger.debug("ip %s report_connect_closed:%s", ip, reason)
