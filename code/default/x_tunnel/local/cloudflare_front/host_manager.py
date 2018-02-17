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
        self.load()
        if self.config.update_domains:
            threading.Thread(target=self.update_front_domains).start()
        
    def load(self):
        if os.path.isfile(self.fn):
            fn = self.fn
        else:
            fn = self.default_fn

        lns = []
        try:
            with open(fn, "r") as fd:
                ds = json.load(fd)
                for top in ds:
                    subs = ds[top]
                    subs = [str(s) for s in subs]
                    lns.append([str(top), subs])
            self.ns = lns
        except Exception as e:
            self.logger.warn("load %s for host fail.", fn)

    def get_sni_host(self, ip):
        top_domain, subs = random.choice(self.ns)
        sni = random.choice(subs)
        
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
                if response.status != 200:
                    self.logger.warn("update front domains fail:%d", response.status)
                    raise Exception("status:%r", response.status)

                need_update = True
                front_domains_fn = self.fn
                if os.path.exists(front_domains_fn):
                    with open(front_domains_fn, "r") as fd:
                        old_content = fd.read()
                        if response.text == old_content:
                            need_update = False

                if need_update:
                    with open(front_domains_fn, "w") as fd:
                        fd.write(response.text)
                    self.load()

                next_update_time = time.time() + (4 * 3600)
                self.logger.info("updated cloudflare front domains from github.")
            except Exception as e:
                next_update_time = time.time() + (1800)
                self.logger.debug("updated cloudflare front domains from github fail:%r", e)
