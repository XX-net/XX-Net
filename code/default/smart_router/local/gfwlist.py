#!/usr/bin/env python
# coding:utf-8


import os

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data', "smart_router"))

import utils
from xlog import getLogger
xlog = getLogger("smart_router")


class GfwList(object):
    def __init__(self):
        self.gfw_black_list = utils.to_bytes(self.load("gfw_black_list.txt"))
        self.gfw_white_list = utils.to_bytes(self.load("gfw_white_list.txt"))
        self.advertisement_list = utils.to_bytes(self.load("advertisement_list.txt"))

    def load(self, name):
        user_file = os.path.join(data_path, name)
        if os.path.isfile(user_file):
            list_file = user_file
        else:
            list_file = os.path.join(current_path, name)

        xlog.info("Load file:%s", list_file)

        fd = open(list_file, "r")
        gfwdict = {}
        for line in fd.readlines():
            line = line.strip()
            if not line:
                continue

            gfwdict["." + line] = 1

        gfwlist = [h for h in gfwdict]
        return tuple(gfwlist)

    def in_block_list(self, host):
        dot_host = b"." + host
        if dot_host.endswith(self.gfw_black_list):
            return True

        return False

    def in_white_list(self, host):
        dot_host = b"." + host
        if dot_host.endswith(self.gfw_white_list):
            return True
        else:
            return False

    def is_advertisement(self, host):
        dot_host = b"." + host
        if dot_host.endswith(self.advertisement_list):
            return True
        else:
            return False
