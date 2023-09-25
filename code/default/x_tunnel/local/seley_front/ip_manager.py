import time
import os
import json

from front_base.ip_manager import IpManagerBase
import utils
from xlog import getLogger
xlog = getLogger("seley_front")


class IpManager(IpManagerBase):
    def __init__(self, config, logger, config_fn):
        super().__init__(config, None, logger)
        self.config_fn = config_fn
        self.hosts = {}
        self.ip_dict = {}
        self.load()

    def __str__(self):
        o = ""
        o += " seley_dict: \r\n%s\r\n" % json.dumps(self.ip_dict, indent=2)
        return o

    def set_hosts(self, hosts):
        self.hosts = hosts
        try:
            with open(self.config_fn, "w") as fd:
                json.dump(self.hosts, fd)
        except Exception as e:
            xlog.error("save hosts %s e:%r", self.config_fn, e)

    def load(self):
        if not os.path.isfile(self.config_fn):
            return

        try:
            with open(self.config_fn, "r") as fd:
                self.hosts = json.load(fd)
        except Exception as e:
            xlog.warn("load hosts %s e:%r", self.config_fn, e)

    def _get_ip_info(self, ip_str):
        ip_str = utils.to_str(ip_str)
        self.ip_dict.setdefault(ip_str, {
            "ip_str": ip_str,
            "fail_times": 0,
            "links": 0,
            "rtt": 1000,
            "last_try": 0.0
        })
        return self.ip_dict[ip_str]

    def get_ip_sni_host(self):
        now = time.time()

        best_info = None
        best_rtt = 99999

        for ip_str, params in self.hosts.items():
            if not params.get("key"):
                continue

            info = self._get_ip_info(ip_str)
            if info["links"] < 0:
                # self.logger.error("ip %s link:%d", ip, info["links"])
                info["links"] = 0

            if info["links"] >= self.config.max_links_per_ip:
                continue

            if info["fail_times"] and now - info["last_try"] < 60:
                continue

            if info["rtt"] < best_rtt:
                best_rtt = info["rtt"]
                best_info = info

        if not best_info:
            return None, None, None

        best_info["links"] += 1
        best_info["last_try"] = now
        ip_str = best_info["ip_str"]
        key = self.hosts[ip_str]["key"]

        return best_info["ip_str"], key, ip_str

    def update_ip(self, ip_str, sni, handshake_time):
        info = self._get_ip_info(ip_str)
        info["fail_times"] = 0
        info["rtt"] = handshake_time
        info["last_try"] = 0.0
        # self.logger.debug("ip %s connect success", ip)

    def report_connect_fail(self, ip_str, sni=None, reason="", force_remove=False):
        info = self._get_ip_info(ip_str)
        info["fail_times"] += 1
        info["rtt"] = 2000
        info["links"] -= 1
        self.logger.debug("ip %s connect fail:%s", ip_str, reason)

    def ssl_closed(self, ip_str, sni=None, reason=""):
        info = self._get_ip_info(ip_str)
        info["links"] -= 1
        self.logger.debug("ip %s ssl_closed:%s", ip_str, reason)

    def recheck_ip(self, ip_str):
        pass
