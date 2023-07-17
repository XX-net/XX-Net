import random
import json

import utils
from front_base.ip_manager import IpManagerBase


class IpManager(IpManagerBase):
    def __init__(self, config, host_manager, logger):
        super(IpManager, self).__init__(config, None, logger)
        self.host_manager = host_manager
        self.ip_dict = {}

    def __str__(self):
        o = ""
        o += " ip_dict: \r\n%s\r\n" % json.dumps(self.ip_dict, indent=2)
        return o

    def _get_ip_info(self, ip):
        self.ip_dict.setdefault(ip, {
            "ip": ip,
            "fail_times": 0,
            "links": 0,
            "rtt": 1000,
        })
        return self.ip_dict[ip]

    def get_ip_sni_host(self):
        ips = self.host_manager.ips

        best_info = None
        best_rtt = 99999

        for ip in ips:
            info = self._get_ip_info(ip)
            if info["links"] < 0:
                info["links"] = 0

            if info["links"] >= self.config.max_links_per_ip:
                continue

            if info["fail_times"] > 5 and random.randint(0, 10) < 9:
                continue

            if info["rtt"] < best_rtt:
                best_rtt = info["rtt"]
                best_info = info

        if not best_info:
            return None, None, None

        best_info["links"] += 1
        # self.logger.debug("get ip:%s", ip)

        ip = best_info["ip"]
        port = best_info.get("port", 443)
        if ":" in ip:
            ip = "[" + ip + "]"
        return ip + ":" + str(port), None, None


    def update_ip(self, ip_str, sni, handshake_time):
        ip, _ = utils.get_ip_port(ip_str)
        ip = utils.to_str(ip)
        info = self._get_ip_info(ip)
        info["fail_times"] = 0
        info["rtt"] = handshake_time
        # self.logger.debug("ip %s connect success", ip)

    def report_connect_fail(self, ip_str, sni=None, reason="", force_remove=False):
        ip, _ = utils.get_ip_port(ip_str)
        ip = utils.to_str(ip)
        info = self._get_ip_info(ip)
        info["fail_times"] += 1
        info["rtt"] = 2000
        self.logger.debug("ip %s connect fail:%s", ip, reason)

    def ssl_closed(self, ip_str, sni=None, reason=""):
        ip, _ = utils.get_ip_port(ip_str)
        ip = utils.to_str(ip)
        info = self._get_ip_info(ip)
        info["links"] -= 1
        self.logger.debug("ip %s ssl_closed:%s", ip, reason)
