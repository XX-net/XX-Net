#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Based on checkgoogleip by  <moonshawdo@gmail.com>
import random
import bisect
import time
import os
import shutil
import ip_utils
from config import config
import logging

random.seed(time.time()* 1000000)

current_path = os.path.dirname(os.path.abspath(__file__))
default_range_file = os.path.join(current_path, "ip_range.txt")
user_range_file = os.path.join(config.DATA_PATH, "ip_range.txt")

class Ip_range(object):
    def __init__(self):
        self.load_ip_range()

    def load_range_content(self):
        if os.path.isfile(user_range_file):
            self.range_file = user_range_file
        else:
            self.range_file = default_range_file

        logging.info("load ip range file:%s", self.range_file)
        fd = open(self.range_file, "r")
        if not fd:
            logging.error("load ip range %s fail", self.range_file)
            return

        content = fd.read()
        fd.close()
        return content

    def update_range_content(self, content):
        with open(user_range_file, "w") as fd:
            fd.write(content)

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

            begin, end = ip_utils.split_ip(line)
            nbegin = ip_utils.ip_string_to_num(begin)
            nend = ip_utils.ip_string_to_num(end)
            if not nbegin or not nend or nend < nbegin:
                logging.warn("load ip range:%s fail", line)
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

    def random_get_ip(self):
        # this function have bug, not fixed, and proved to be not a good idea.
        while True:
            index = random.randint(0, self.candidate_amount_ip)
            id = bisect.bisect_left(self.ip_range_index, index)
            range_index = self.ip_range_index[id-1]
            ip_range = self.ip_range_map[range_index]
            ip = ip_range[0] + (index - id)
            add_last_byte = ip % 255
            if add_last_byte == 0 or add_last_byte == 255:
                continue
            return ip

    def get_ip(self):
        while True:
            index = random.randint(0, len(self.ip_range_list) - 1)
            ip_range = self.ip_range_list[index]
            #logging.debug("random.randint %d - %d", ip_range[0], ip_range[1])
            if ip_range[1] == ip_range[0]:
                return ip_range[1]

            try:
                id_2 = random.randint(0, ip_range[1] - ip_range[0])
            except Exception as e:
                logging.exception("random.randint:%r %d - %d, %d", e, ip_range[0], ip_range[1], ip_range[1] - ip_range[0])

            ip = ip_range[0] + id_2
            add_last_byte = ip % 255
            if add_last_byte == 0 or add_last_byte == 255:
                continue

            return ip

ip_range = Ip_range()

def test():
    proxy = ip_range()
    # proxy.show_ip_range()
    for i in range(1, 300):
        ip = proxy.get_ip()
        ip_addr = ip_utils.ip_num_to_string(ip)
        print "ip:", ip_addr

def test_random():
    #random.seed(time.time())
    for i in range(1000):
        index = random.randint(0, 1000 - 1)
        print index

if __name__ == '__main__':
    test_random()
