import os
import json
import socket
import time

import utils

from front_base.ip_manager import IpManagerBase


class IpManager(IpManagerBase):
    def __init__(self, config, default_domain_fn, domain_fn, speed_fn, logger):
        super(IpManager, self).__init__(config, None, logger, speed_fn)
        self.default_domain_fn = default_domain_fn
        self.domain_fn = domain_fn

        self.domain_map = self.load_domains()
        # top_domain -> {}

    def __str__(self):
        o = ""
        o += " domain_map: \r\n%s\r\n" % json.dumps(self.domain_map, indent=2)
        return o

    def load_domains(self):
        domain_map = {}  # top_domain -> {}
        for fn in [self.domain_fn, self.default_domain_fn]:
            if not os.path.isfile(fn):
                continue

            try:
                with open(fn, "r") as fd:
                    ds = json.load(fd)
                    for top in ds:
                        domain_map[str(top)] = {
                            "links": 0,
                            "fail_times": 0,
                            "last_try": 0.0
                        }
                self.logger.info("load %s success", fn)
                break
            except Exception as e:
                self.logger.warn("load %s for host failed:%r", fn, e)
        return domain_map

    def save_domains(self, domains):
        ns = []
        for top_domain, _ in self.domain_map.items():
            ns.append(top_domain)

        if ns == domains:
            self.logger.debug("save domains not changed, ignore")
            return
        else:
            self.logger.info("save domains:%s", domains)

        dat = {}
        for domain in domains:
            dat[domain] = ["www." + domain]

        with open(self.domain_fn, "w") as fd:
            json.dump(dat, fd)

        self.domain_map = self.load_domains()

    def get_ip_sni_host(self):
        now = time.time()
        for top_domain, info in self.domain_map.items():
            if info["links"] < 0:
                info["links"] = 0

            if info["links"] >= self.config.max_connection_per_domain:
                continue

            if info["fail_times"] and now - info["last_try"] < 60:
                continue

            sni = "www." + top_domain
            try:
                ip = socket.gethostbyname(sni)
            except Exception as e:
                self.logger.warn("get ip for %s fail:%r", sni, e)
                continue

            self.logger.debug("get ip:%s sni:%s", ip, sni)
            info["links"] += 1
            info["last_try"] = now
            return {
                "ip_str": ip,
                "sni": sni,
                "host": top_domain,
            }

        return None

    def _get_domain(self, top_domain):
        self.domain_map.setdefault(top_domain, {
                            "links": 0,
                            "fail_times": 0,
                            "last_try": 0.0
                        })
        return self.domain_map[top_domain]

    def report_connect_fail(self, ip_str, sni=None, reason="", force_remove=True):
        ip, _ = utils.get_ip_port(ip_str)
        ip = utils.to_str(ip)
        top_domain = ".".join(sni.split(".")[1:])

        info = self._get_domain(top_domain)
        info["fail_times"] += 1
        info["links"] -= 1
        self.logger.debug("ip %s sni:%s connect fail, reason:%s", ip, sni, reason)

    def update_ip(self, ip_str, sni, handshake_time):
        top_domain = ".".join(sni.split(".")[1:])

        info = self._get_domain(top_domain)
        info["fail_times"] = 0
        info["last_try"] = 0.0
        # self.logger.debug("ip %s sni:%s connect success, rtt:%f", ip, sni, handshake_time)

    def ssl_closed(self, ip_str, sni=None, reason=""):
        ip, _ = utils.get_ip_port(ip_str)
        ip = utils.to_str(ip)
        top_domain = ".".join(sni.split(".")[1:])

        try:
            info = self._get_domain(top_domain)
            info["links"] -= 1
            self.logger.debug("ip %s sni:%s connect closed reason %s", ip, sni, reason)
        except Exception as e:
            self.logger.warn("ssl_closed %s sni:%s reason:%s except:%r", ip_str, sni, reason, e)
