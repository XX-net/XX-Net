#!/usr/bin/env python
# coding:utf-8

import random
import threading
import time

from config import config
from xlog import getLogger
xlog = getLogger("gae_proxy")
import check_ip


class APPID_manager(object):
    lock = threading.Lock()

    def __init__(self):
        self.reset_appid()

    def reset_appid(self):
        # called by web_control
        with self.lock:
            if len(config.GAE_APPIDS) == 0:
                self.working_appid_list = list(config.PUBLIC_APPIDS)
            else:
                self.working_appid_list = list(config.GAE_APPIDS)
            self.not_exist_appids = []
            self.out_of_quota_appids = []
        self.last_reset_time = time.time()

    def get_appid(self):
        if len(self.working_appid_list) == 0:
            if time.time() - self.last_reset_time < 600:
                xlog.warn("all appid out of quota, need 10 min to reset")
                return None
            else:
                xlog.warn("reset appid")
                self.reset_appid()

        return random.choice(self.working_appid_list)

    def report_out_of_quota(self, appid):
        xlog.warn("report_out_of_quota:%s", appid)
        with self.lock:
            if appid not in self.out_of_quota_appids:
                self.out_of_quota_appids.append(appid)
            self.working_appid_list.remove(appid)

    def report_not_exist(self, appid, ip):
        xlog.debug("report_not_exist:%s %s", appid, ip)
        th = threading.Thread(target=self.process_appid_not_exist, args=(appid, ip))
        th.start()

    def process_appid_not_exist(self, appid, ip):
        if check_ip.test_gae_ip(ip, "xxnet-1"):
            self.set_appid_not_exist(appid)
        else:
            xlog.warn("process_appid_not_exist, remove ip:%s", ip)
            from google_ip import google_ip
            google_ip.report_connect_fail(ip, force_remove=True)

    def set_appid_not_exist(self, appid):
        xlog.warn("APPID_manager, set_appid_not_exist %s", appid)
        with self.lock:
            if appid not in self.not_exist_appids:
                self.not_exist_appids.append(appid)
                config.GAE_APPIDS.remove(appid)
                self.working_appid_list.remove(appid)

    def appid_exist(self, appids):
        for appid in appids.split('|'):
            if appid == "":
                continue
            if appid in config.GAE_APPIDS:
                return True
        return False


appid_manager = APPID_manager()

