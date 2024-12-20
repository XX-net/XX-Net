import time
import json

import utils
from front_base.ip_manager import IpManagerBase


class IpManager(IpManagerBase):
    def __init__(self, config, host_manager, logger, speed_fn):
        super(IpManager, self).__init__(config, None, logger, speed_fn)
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
            "last_try": 0.0
        })
        return self.ip_dict[ip]

    def get_ip_sni_host(self):
        now = time.time()

        best_info = None
        best_speed = 0

        for ip, ip_info in self.host_manager.info.items():
            if "sni" not in ip_info:
                continue

            port = int(ip_info.get("port", 443))
            ip_str = utils.get_ip_str(ip, port)

            info = self._get_ip_info(ip)
            if info["links"] < 0:
                # self.logger.error("ip %s link:%d", ip, info["links"])
                info["links"] = 0

            if info["links"] >= self.config.max_links_per_ip:
                continue

            if info["fail_times"] and now - info["last_try"] < 60:
                continue

            speed = self.get_speed(ip_str)
            if speed > best_speed:
                best_speed = speed
                best_info = info

        if not best_info:
            return None

        best_info["links"] += 1
        best_info["last_try"] = now
        # self.logger.debug("get ip:%s", ip)

        ip = best_info["ip"]
        port = int(self.host_manager.info[ip].get("port", 443))
        ip_str = utils.get_ip_str(ip, port)
        return {
            "ip_str": ip_str,
            "sni": None,
            "host": None,
        }

    def update_ip(self, ip_str, sni, handshake_time):
        ip, _ = utils.get_ip_port(ip_str)
        ip = utils.to_str(ip)
        info = self._get_ip_info(ip)
        info["fail_times"] = 0
        info["rtt"] = handshake_time
        info["last_try"] = 0.0
        # self.logger.debug("ip %s connect success", ip)

    def report_connect_fail(self, ip_str, sni=None, reason="", force_remove=False):
        ip, _ = utils.get_ip_port(ip_str)
        ip = utils.to_str(ip)
        info = self._get_ip_info(ip)
        info["fail_times"] += 1
        info["rtt"] = 2000
        info["links"] -= 1
        self.logger.debug("ip %s connect fail:%s", ip, reason)

    def ssl_closed(self, ip_str, sni=None, reason=""):
        ip, _ = utils.get_ip_port(ip_str)
        ip = utils.to_str(ip)
        info = self._get_ip_info(ip)
        info["links"] -= 1
        self.logger.debug("ip %s ssl_closed:%s", ip, reason)
