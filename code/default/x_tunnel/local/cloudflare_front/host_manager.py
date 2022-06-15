import random
import os
import json
import time
import threading

import simple_http_client

from front_base.host_manager import HostManagerBase


class HostManager(HostManagerBase):
    def __init__(self, config, logger, default_fn, fn, front):
        self.config = config
        self.logger = logger
        self.default_fn = default_fn
        self.fn = fn
        self.front = front
        self.ns = self.load()
        self.ns_idx = 0
        if self.config.update_domains:
            threading.Thread(target=self.update_front_domains).start()
        
    def load(self):
        lns = []
        for fn in [self.fn, self.default_fn]:
            if not os.path.isfile(fn):
                continue

            try:
                with open(fn, "r") as fd:
                    ds = json.load(fd)
                    for top in ds:
                        subs = ds[top]
                        subs = [str(s) for s in subs]
                        lns.append([str(top), subs])
                self.logger.info("load %s success", fn)
                break
            except Exception as e:
                self.logger.warn("load %s for host fail.", fn)
        return lns

    def get_sni_host(self, ip):
        ns_num = len(self.ns)
        if ns_num == 0:
            return None, None

        i = self.ns_idx % ns_num
        top_domain, subs = self.ns[i]
        sni = random.choice(subs)
        self.ns_idx += 1
        
        return sni, top_domain

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

                url = "https://raw.githubusercontent.com/XX-net/XX-Net/master/code/default/x_tunnel/local/cloudflare_front/front_domains.json"
                response = client.request("GET", url)
                if not response or response.status != 200:
                    if response:
                        self.logger.warn("update front domains fail:%d", response.status)
                    next_update_time = time.time() + (1800)
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

                if need_update:
                    with open(front_domains_fn, "w") as fd:
                        fd.write(content.decode("utf-8"))
                    self.load()

                    self.logger.info("updated cloudflare front domains from github.")

                next_update_time = time.time() + (4 * 3600)
            except Exception as e:
                next_update_time = time.time() + (1800)
                self.logger.exception("updated cloudflare front domains from github fail:%r", e)

    def save_domains(self, domains):
        ns = []
        for top, subs in self.ns:
            ns.append(top)

        if ns == self.ns:
            return

        dat = {}
        for domain in domains:
            dat[domain] = ["www." + domain]

        with open(self.fn, "w") as fd:
            json.dump(dat, fd)

        self.ns = self.load()
