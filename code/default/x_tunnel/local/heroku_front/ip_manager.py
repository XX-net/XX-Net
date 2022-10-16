import random

from front_base.ip_manager import IpManagerBase


class IpManager(IpManagerBase):
    def __init__(self, config, host_manager, logger):
        super(IpManager, self).__init__(config, None, logger)
        self.host_manager = host_manager

    def get_ip(self):
        ip = random.choice(self.host_manager.ips)
        return ip + ":443"

    def recheck_ip(self, ip_str):
        pass
