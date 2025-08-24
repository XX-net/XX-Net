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

    def __str__(self):
        o = super().__str__()
        o += " seley_host: \r\n%s\r\n" % json.dumps(self.hosts, indent=2)
        o += " seley_dict: \r\n%s\r\n" % json.dumps(self.ip_dict, indent=2)
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

    def _get_ip_dict(self, host_port):
        host_port = utils.to_str(host_port)

        host, port = utils.get_ip_port(host_port)
        ip = None
        if not utils.check_ip_valid(host):
            try:
                info = socket.getaddrinfo(host, port, socket.AF_UNSPEC,
                                          socket.SOCK_STREAM)

                for af, socktype, proto, canonname, sa in info:
                    ip = sa[0]
            except socket.gaierror:
                return None
        else:
            ip = host

        if not ip:
            return None

        ip_str = utils.get_ip_str(ip, port)

        self.ip_dict.setdefault(ip_str, {
            "ip_str": ip_str,
            "host_port": host_port,
            "fail_times": 0,
            "links": 0,
            "rtt": 1000,
            "last_try": 0.0
        })
        return self.ip_dict[ip_str]

    def _get_ip_sni_host(self, force=False):
        now = time.time()

        best_dict = None
        best_score = 99

        for host_port, params in self.hosts.items():
            if not params.get("key") or host_port.startswith("_"):
                continue

            ip_dict = self._get_ip_dict(host_port)
            if not ip_dict:
                continue

            ip_str = ip_dict["ip_str"]
            if ip_dict["links"] < 0:
                # self.logger.error("ip %s link:%d", ip, info["links"])
                ip_dict["links"] = 0

            if ip_dict["links"] >= self.config.max_links_per_ip:
                continue

            if ip_dict["fail_times"]:
                last_try = now - ip_dict["last_try"]
                if last_try < 5 or (not force and last_try < 60):
                    continue
                else:
                    best_dict = ip_dict
                    # xlog.debug("get_ip_sni_host last_try %s", ip_str)
                    break

            score = self.get_score(ip_str)
            if score < best_score:
                best_score = score
                best_dict = ip_dict
                # xlog.debug("get_ip_sni_host best speed %s", ip_str)

        return best_dict

    def get_ip_sni_host(self):
        if not self.hosts:
            return None

        best_dict = self._get_ip_sni_host()
        if not best_dict:
            # try again, incase the network is disconnected
            best_dict = self._get_ip_sni_host(force=True)

        if not best_dict:
            time.sleep(1)
            return None

        ip_str = best_dict["ip_str"]
        host_port = best_dict["host_port"]
        best_params = self.hosts[host_port]

        best_dict["links"] += 1
        best_dict["last_try"] = time.time()

        return {
            "ip_str": ip_str,
            "sni": best_params["key"],
            "host": ip_str,
            "adjust": best_params.get("adjust", 0),
        }

    def update_ip(self, ip_str, sni, handshake_time):
        info = self._get_ip_dict(ip_str)
        info["fail_times"] = 0
        info["rtt"] = handshake_time
        # self.logger.debug("ip %s connect success", ip)

    def report_connect_fail(self, ip_str, sni=None, reason="", force_remove=False):
        info = self._get_ip_dict(ip_str)
        info["fail_times"] += 1
        info["links"] -= 1
        self.logger.debug("ip %s connect fail:%s", ip_str, reason)

    def report_connect_closed(self, ip_str, sni=None, reason=""):
        info = self._get_ip_dict(ip_str)
        info["links"] -= 1
        self.logger.debug("%s report_connect_closed:%s", ip_str, reason)

    def recheck_ip(self, ip_str):
        pass
