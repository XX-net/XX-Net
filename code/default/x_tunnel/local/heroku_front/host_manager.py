import random

from front_base.host_manager import HostManagerBase


class HostManager(HostManagerBase):
    def __init__(self, appids=[]):
        self.appids = appids

    def set_appids(self, appids):
        self.appids = appids

    def get_sni_host(self, ip):
        return "", random.choice(self.appids)

    def remove(self, appid):
        try:
            self.appids.remove(appid)
        except:
            pass