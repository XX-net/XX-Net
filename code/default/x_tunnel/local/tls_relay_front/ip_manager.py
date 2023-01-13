import random

from front_base.ip_manager import IpManagerBase


class IpManager(IpManagerBase):
    def __init__(self, config, host_manager, logger):
        super(IpManager, self).__init__(config, None, logger)
        self.host_manager = host_manager
        self.ip_dict = {}

    def get_ip(self):
        ips = self.host_manager.ips

        for _ in range(len(ips)):
            ip = random.choice(ips)
            self.ip_dict.setdefault(ip, {
                "fail_times": 0,
                "success_times": 0,
                "links": 0,
            })
            if self.ip_dict[ip]["links"] >= self.config.max_links_per_ip:
                continue

            self.ip_dict[ip]["links"] += 1
            self.logger.debug("get ip:%s", ip)

            port = self.host_manager.info[ip].get("port", 443)
            return ip + ":" + str(port)

    def report_connect_fail(self, ip_str, reason=""):
        ip = ip_str.split(":")[0]
        self.ip_dict[ip]["fail_times"] += 1
        self.ip_dict[ip]["links"] -= 1
        self.logger.debug("ip %s connect fail", ip)

    def update_ip(self, ip_str, handshake_time):
        ip = ip_str.split(":")[0]
        self.ip_dict.setdefault(ip, {
            "fail_times": 0,
            "success_times": 0
        })
        self.ip_dict[ip]["success_times"] += 1
        self.logger.debug("ip %s connect success", ip)

    def ssl_closed(self, ip_str, reason=""):
        ip = ip_str.split(":")[0]
        self.ip_dict[ip]["links"] -= 1
        self.logger.debug("ip %s connect closed", ip)

    def recheck_ip(self, ip_str):
        pass
