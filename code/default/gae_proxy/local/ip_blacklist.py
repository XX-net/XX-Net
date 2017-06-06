import ip_utils
import os
from config import config
from xlog import getLogger
xlog = getLogger("gae_proxy")

class Ip_BlackList(object):
    def __init__(self):
        self.user_ip_blacklist_file = os.path.join(config.DATA_PATH, "ip_blacklist.txt")
        self.load_ip_blacklist()

    def load_ip_blacklist(self):
        xlog.info("load user ip blacklist file:%s",self.user_ip_blacklist_file)
        with open(self.user_ip_blacklist_file,"r") as fd:
            self.ip_blacklist=[ip for ip in fd.readlines() if ip_utils.check_ip_valid(ip)]
        

if __name__ == "__main__":
    ip_blacklist=Ip_BlackList()
    print type(ip_blacklist.ip_blacklist)
    for ip in ip_blacklist.ip_blacklist:
        print ip