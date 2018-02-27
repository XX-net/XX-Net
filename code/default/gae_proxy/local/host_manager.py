import time

from front_base.host_manager import HostManagerBase
from sni_manager import SniManager


class HostManager(HostManagerBase):
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.appid_manager = None

        self.sni_manager = SniManager(logger)

    def get_sni_host(self, ip):
        if not self.appid_manager:
            raise Exception()

        sni = self.sni_manager.get()
        appid = self.appid_manager.get()
        if not appid:
            self.logger.warn("no appid")
            time.sleep(10)
            raise Exception()

        top_domain = appid + ".appspot.com"
        return sni, top_domain

