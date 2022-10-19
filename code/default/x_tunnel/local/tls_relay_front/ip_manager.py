import random

from front_base.ip_manager import IpManagerBase


class IpManager(IpManagerBase):
    def __init__(self, config, host_manager, logger):
        super(IpManager, self).__init__(config, None, logger)
        self.host_manager = host_manager
        self.ip_dict = {}

    def get_ip(self):
        ips = self.host_manager.ips
        if not ips:
            return None

        ip = random.choice(ips)
        return ip + ":443"

    def report_connect_fail(self, ip_str, reason=""):
        ip = ip_str.split(":")[0]
        self.ip_dict.setdefault(ip, {
            "fail_times": 0,
            "success_times": 0
        })
        self.ip_dict[ip]["fail_times"] += 1

    def update_ip(self, ip_str, handshake_time):
        ip = ip_str.split(":")[0]
        self.ip_dict.setdefault(ip, {
            "fail_times": 0,
            "success_times": 0
        })
        self.ip_dict[ip]["success_times"] += 1

    def recheck_ip(self, ip_str):
        pass
