import random
import socket

import utils
from front_base.ip_manager import IpManagerBase


class IpManager(IpManagerBase):
    def __init__(self, config, host_manager, logger):
        super(IpManager, self).__init__(config, None, logger)
        self.host_manager = host_manager

    def get_ip(self):
        domains = list(self.host_manager.domains.keys())
        domain = random.choice(domains)

        ips = self.host_manager.domains[domain]["ips"]
        if isinstance(ips, list):
            ip = random.choice(ips)
            return ip + ":443"
        elif ips == "dns_random_prefix":

            prefix_len = random.randint(3, 8)
            prefix = utils.generate_random_lowercase(prefix_len)

            slc = domain.split(".")
            post_fix = ".".join(slc[1:])

            host = utils.to_str(prefix) + "." + post_fix
            ip = socket.gethostbyname(host)

            self.host_manager.ip_map[ip] = self.host_manager.domains[domain]
            self.host_manager.ip_map[ip]["host"] = domain

            return ip + ":443"
        elif ips == "dns":
            ip = socket.gethostbyname(domain)

            self.host_manager.ip_map[ip] = self.host_manager.domains[domain]
            self.host_manager.ip_map[ip]["host"] = domain

            return ip + ":443"

    def recheck_ip(self, ip_str):
        pass
