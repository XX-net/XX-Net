#!/usr/bin/env python
# coding:utf-8

import random
import threading
import time

from config import config
from proxy import xlog


class APPID_manager(object):
    lock = threading.Lock()

    def __init__(self):
        if len(config.GAE_APPIDS) == 0:
            xlog.error("No usable appid left, add new appid to continue use GAEProxy")
            return

        self.lock.acquire()
        try:
            self.working_appid_list = list(config.GAE_APPIDS)
            self.not_exist_appids = []
            self.out_of_quota_appids = []
        finally:
            self.lock.release()

        self.last_reset_time = 0

    def reset_appid(self):
        # called by web_control
        self.lock.acquire()
        try:
            self.working_appid_list = list(config.GAE_APPIDS)
            self.not_exist_appids = []
            self.out_of_quota_appids = []
        finally:
            self.lock.release()


    def get_appid(self):
        if len(self.working_appid_list) == 0:
            if time.time() - self.last_reset_time < 60:
                xlog.warn("all appid out of quota, need 1 min to reset")
                return None
            else:
                xlog.warn("reset appid")
                self.lock.acquire()
                self.working_appid_list = list(config.GAE_APPIDS)
                self.out_of_quota_appids = []
                self.lock.release()
                self.last_reset_time = time.time()

        return random.choice(self.working_appid_list)

    def report_out_of_quota(self, appid):
        xlog.warn("report_out_of_quota:%s", appid)
        self.lock.acquire()
        try:
            if appid not in self.out_of_quota_appids:
                self.out_of_quota_appids.append(appid)
                self.working_appid_list.remove(appid)
        except:
            pass
        finally:
            self.lock.release()

    def report_not_exist(self, appid):
        xlog.warn("APPID_manager, report_not_exist %s", appid)
        self.lock.acquire()
        try:
            if appid not in self.not_exist_appids:
                self.not_exist_appids.append(appid)
                config.GAE_APPIDS.remove(appid)
                self.working_appid_list.remove(appid)
        except:
            pass
        finally:
            self.lock.release()

    def appid_exist(self, appids):
        for appid in appids.split('|'):
            if appid == "":
                continue
            if appid in config.GAE_APPIDS:
                return True
        return False


appid_manager = APPID_manager()
