#!/usr/bin/env python
# coding:utf-8

from config import config
import xlog
import random

class APPID_manager(object):
    def __init__(self):
        self.reset_appid()

    def get_appid(self):
        if len(self.working_appid_list) == 0:
            xlog.error("No usable appid left, add new appid to continue use GAEProxy")
            return None
        else:
            return random.choice(self.working_appid_list)

    def report_out_of_quota(self, appid):
        try:
            self.working_appid_list.remove(appid)
            self.out_of_quota_appids.append(appid)
        except:
            pass
        if len(self.working_appid_list) == 0:
            self.reset_appid()

    def report_not_exist(self, appid):
        xlog.warn("APPID_manager, report_not_exist %s", appid)

        try:
            config.GAE_APPIDS.remove(appid)
            self.not_exist_appids.append(appid)
        except:
            pass

        try:
            self.working_appid_list.remove(appid)
        except:
            pass

        if len(self.working_appid_list) == 0:
            self.reset_appid()

    def appid_exist(self, appids):
        for appid in appids.split('|'):
            if appid == "":
                continue
            if appid in config.GAE_APPIDS:
                return True
        return False

    def reset_appid(self):
        self.working_appid_list = config.GAE_APPIDS
        self.out_of_quota_appids = []
        self.not_exist_appids = []

appid_manager = APPID_manager()
