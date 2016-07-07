#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Based on checkgoogleip by  <moonshawdo@gmail.com>
import random
import time
import os
import ip_utils
from config import config

from xlog import getLogger
xlog = getLogger("gae_proxy")

random.seed(time.time()* 1000000)

current_path = os.path.dirname(os.path.abspath(__file__))


class IpRange(object):
    def __init__(self):
        self.default_range_file = os.path.join(current_path, "ip_range.txt")
        self.user_range_file = os.path.join(config.DATA_PATH, "ip_range.txt")
        self.load_ip_range()

    def load_range_content(self, default=False):
        if not default and os.path.isfile(self.user_range_file):
            self.range_file = self.user_range_file
        else:
            self.range_file = self.default_range_file

        xlog.info("load ip range file:%s", self.range_file)
        fd = open(self.range_file, "r")
        if not fd:
            xlog.error("load ip range %s fail", self.range_file)
            return

        content = fd.read()
        fd.close()
        return content

    def update_range_content(self, content):
        with open(self.user_range_file, "w") as fd:
            fd.write(content)

    def remove_user_range(self):
        try:
            os.remove(self.user_range_file)
        except:
            pass

    def load_ip_range(self):
        self.ip_range_map = {}
        self.ip_range_list = []
        self.ip_range_index = []
        self.candidate_amount_ip = 0

        content = self.load_range_content()
        lines = content.splitlines()
        for line in lines:
            if len(line) == 0 or line[0] == '#':
                continue

            try:
                begin, end = ip_utils.split_ip(line)
                nbegin = ip_utils.ip_string_to_num(begin)
                nend = ip_utils.ip_string_to_num(end)
                if not nbegin or not nend or nend < nbegin:
                    xlog.warn("load ip range:%s fail", line)
                    continue
            except Exception as e:
                xlog.exception("load ip range:%s fail:%r", line, e)
                continue

            self.ip_range_map[self.candidate_amount_ip] = [nbegin, nend]
            self.ip_range_list.append( [nbegin, nend] )
            self.ip_range_index.append(self.candidate_amount_ip)
            num = nend - nbegin
            self.candidate_amount_ip += num
            # print ip_utils.ip_num_to_string(nbegin), ip_utils.ip_num_to_string(nend), num

        self.ip_range_index.sort()
        #print "amount ip num:", self.candidate_amount_ip

    def show_ip_range(self):
        for id in self.ip_range_map:
            print "[",id,"]:", self.ip_range_map[id]

    def get_real_random_ip(self):
        while True:
            ip_int = random.randint(0, 4294967294)
            add_last_byte = ip_int % 255
            if add_last_byte == 0 or add_last_byte == 255:
                continue

            return ip_int

    def get_ip(self):
        #return self.get_real_random_ip()
        while True:
            index = random.randint(0, len(self.ip_range_list) - 1)
            ip_range = self.ip_range_list[index]
            #xlog.debug("random.randint %d - %d", ip_range[0], ip_range[1])
            if ip_range[1] == ip_range[0]:
                return ip_utils.ip_num_to_string(ip_range[1])

            try:
                id_2 = random.randint(0, ip_range[1] - ip_range[0])
            except Exception as e:
                xlog.exception("random.randint:%r %d - %d, %d", e, ip_range[0], ip_range[1], ip_range[1] - ip_range[0])
                return

            ip = ip_range[0] + id_2
            add_last_byte = ip % 256
            if add_last_byte == 0 or add_last_byte == 255:
                continue

            return ip_utils.ip_num_to_string(ip)

ip_range = IpRange()