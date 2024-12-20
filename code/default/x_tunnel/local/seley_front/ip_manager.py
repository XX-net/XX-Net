import time
import os
import json
import socket
import threading

from front_base.ip_manager import IpManagerBase
import utils
from xlog import getLogger
xlog = getLogger("seley_front")


class IpManager(IpManagerBase):
    def __init__(self, config, logger, config_fn, speed_fn):
        super().__init__(config, None, logger, speed_fn)
        self.config_fn = config_fn
        self.hosts = {}
        self.ip_dict = {}
        self.load()
        threading.Thread(target=self.resolve_domains, name="seley_resolve_domain", daemon=False).start()

    def __str__(self):
        o = ""
        o += " seley_host: \r\n%s\r\n" % json.dumps(self.hosts, indent=2)
        o += " seley_dict: \r\n%s\r\n" % json.dumps(self.ip_dict, indent=2)
        o += " speed_info: \r\n%s\r\n" % json.dumps(self.speed_info, indent=2)
        return o

    def set_hosts(self, hosts):
        try:
            with open(self.config_fn, "w") as fd:
                json.dump(hosts, fd, indent=2)

            self.load()
        except Exception as e:
            xlog.error("save hosts %s e:%r", self.config_fn, e)

    def load(self):
        if not os.path.isfile(self.config_fn):
            return

        try:
            with open(self.config_fn, "r") as fd:
                domain_hosts = json.load(fd)
        except Exception as e:
            xlog.warn("load hosts %s e:%r", self.config_fn, e)
            return

        self.hosts = domain_hosts

    def resolve_domains(self):
        ip_hosts = {}
        for domain_port, host_info in self.hosts.items():
            if not host_info.get("key"):
                continue

            ip, port = utils.get_ip_port(domain_port)
            if not utils.check_ip_valid(ip):
                try:
                    info = socket.getaddrinfo(ip, port, socket.AF_UNSPEC,
                                              socket.SOCK_STREAM)

                    for af, socktype, proto, canonname, sa in info:
                        ip = sa[0]

                        ip_str = utils.get_ip_str(ip, port)
                        ip_hosts[ip_str] = host_info
                except socket.gaierror:
                    ip_hosts[domain_port] = host_info
            else:
                ip_hosts[domain_port] = host_info

        self.hosts = ip_hosts

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
        best_params = {}
        best_speed = 0

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

            if now - info["last_try"] > 30 * 60:
                best_info = info
                best_params = params
                # xlog.debug("get_ip_sni_host last_try %s", ip_str)
                break

            speed = self.get_speed(ip_str)
            if speed > best_speed:
                best_speed = speed
                best_info = info
                best_params = params
                # xlog.debug("get_ip_sni_host best speed %s", ip_str)

        if not best_info:
            return None

        ip_str = best_info["ip_str"]
        self.ip_dict[ip_str]["links"] += 1
        self.ip_dict[ip_str]["last_try"] = now
        key = self.hosts[ip_str]["key"]

        return {
            "ip_str": best_info["ip_str"],
            "sni": key,
            "host": ip_str,
            "adjust": best_params.get("adjust", 0),
        }

    def update_ip(self, ip_str, sni, handshake_time):
        info = self._get_ip_info(ip_str)
        info["fail_times"] = 0
        info["rtt"] = handshake_time
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
