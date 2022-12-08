import random
import time
import json
import threading
import os

current_path = os.path.dirname(os.path.abspath(__file__))

import utils
import simple_http_client
from front_base.host_manager import HostManagerBase


class HostManager(HostManagerBase):
    def __init__(self, config, logger, default_fn, fn, front):
        self.config = config
        self.logger = logger
        self.default_fn = default_fn
        self.fn = fn
        self.front = front
        self.domains = {}
        self.ip_map = {}
        self.ips = []
        self.load()

        if self.config.update_domains:
            threading.Thread(target=self.update_front_domains).start()

    def load(self):
        for fn in [self.fn, self.default_fn]:
            if not os.path.isfile(fn):
                continue

            try:
                with open(fn, "r") as fd:
                    domains = json.load(fd)
                    self.domains = domains

                    for host, info in domains.items():
                        ips = info["ips"]
                        for ip in ips:
                            self.ip_map[ip] = {
                                "host": host,
                                "sni_policy": info["sni_policy"],
                                "sni_check": info["sni_check"],
                            }
                            self.ips.append(ip)

                self.logger.info("load %s success", fn)
                break
            except Exception as e:
                self.logger.warn("load %s for host fail. %r", fn, e)

    def get_sni_host(self, ip_str):
        ip = ip_str.split(":")[0]
        info = self.ip_map.get(ip)
        if not info:
            self.logger.warn("ip %s not found in host_manager", ip)
            return None, None

        sni_policy = info["sni_policy"]
        host = info["host"]
        if sni_policy == "empty":
            sni = None
        elif sni_policy == "same":
            sni = host
        elif sni_policy == "random_prefix":
            prefix_len = random.randint(3, 8)
            prefix = utils.generate_random_lowercase(prefix_len)

            slc = host.split(".")
            post_fix = ".".join(slc[1:])

            sni = utils.to_str(prefix) + "." + post_fix
        else:
            self.logger.warn("unknown sni_policy: %s", sni_policy)
            sni = host

        return sni, host

    def update_front_domains(self):
        next_update_time = time.time()
        while self.front.running:
            if time.time() < next_update_time:
                time.sleep(4)
                continue

            try:
                timeout = 30
                if self.config.PROXY_ENABLE:
                    client = simple_http_client.Client(proxy={
                        "type": self.config.PROXY_TYPE,
                        "host": self.config.PROXY_HOST,
                        "port": self.config.PROXY_PORT,
                        "user": self.config.PROXY_USER,
                        "pass": self.config.PROXY_PASSWD,
                    }, timeout=timeout)
                else:
                    client = simple_http_client.Client(timeout=timeout)

                url = "https://raw.githubusercontent.com/XX-net/XX-Net/master/code/default/x_tunnel/local/heroku_front/front_domains.json"
                response = client.request("GET", url)
                if not response or response.status != 200:
                    if response:
                        self.logger.warn("update front domains fail:%d", response.status)
                    next_update_time = time.time() + 1800
                    continue

                content = response.text
                if isinstance(content, memoryview):
                    content = content.tobytes()

                if not self.config.update_domains:
                    # check again to avoid network delay issue.
                    return

                need_update = True
                front_domains_fn = self.fn
                if os.path.exists(front_domains_fn):
                    with open(front_domains_fn, "r") as fd:
                        old_content = fd.read()
                        if content == old_content:
                            need_update = False
                else:
                    with open(self.default_fn, "r") as fd:
                        old_content = fd.read()
                        if content == old_content:
                            need_update = False

                if need_update:
                    with open(front_domains_fn, "w") as fd:
                        fd.write(content.decode("utf-8"))
                    self.load()

                    self.logger.info("updated heroku front domains from github.")

                next_update_time = time.time() + (4 * 3600)
            except Exception as e:
                next_update_time = time.time() + 1800
                self.logger.exception("updated heroku front domains from github fail:%r", e)

    def remove(self, host):
        pass
