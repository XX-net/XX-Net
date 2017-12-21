#!/usr/bin/env python
# coding:utf-8


import os

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data', "smart_router"))

from xlog import getLogger
xlog = getLogger("smart_router")


class GfwList(object):
    def __init__(self):
        self.gfwlist = self.load()

    def load(self):
        user_file = os.path.join(data_path, "gfw_black_list.txt")
        if os.path.isfile(user_file):
            list_file = user_file
        else:
            list_file = os.path.join(current_path, "gfw_black_list.txt")

        xlog.info("Load GFW black list file:%s", list_file)

        fd = open(list_file, "r")
        gfwdict = {}
        for line in fd.readlines():
            line = line.strip()
            if not line:
                continue

            gfwdict[line] = 1

        gfwlist = [h for h in gfwdict]
        return tuple(gfwlist)

    def check(self, host):
        if not host.endswith(self.gfwlist):
            return False

        # check avoid wrong match like xgoogle.com
        dpl = host.split(".")
        for i in range(0, len(dpl)):
            h = ".".join(dpl[i:])
            if h in self.gfwlist:
                return True

        return False

    def get_pac_string(self):
        s = '",\n"'.join(self.gfwlist)
        return s
