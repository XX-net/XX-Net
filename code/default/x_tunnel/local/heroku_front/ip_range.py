#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import time
import json

import ip_utils
from xlog import getLogger
xlog = getLogger("heroku_front")

random.seed(time.time()* 1000000)

current_path = os.path.dirname(os.path.abspath(__file__))


class IpRange(object):
    def __init__(self):
        self.ip_range_list = []
        self.load_ec2_range()

    def load_ec2_range(self):
        fn = os.path.join(current_path, "ec2_iprange.txt")
        with open(fn, "r") as fd:
            ipr = json.load(fd)

        for ipd in ipr["prefixes"]:
            try:
                if ipd["region"] != "us-east-1":
                    continue

                if "ip_prefix" not in ipd:
                    continue

                if ipd["service"] != "EC2":
                    continue

                ipp = ipd["ip_prefix"]
                # xlog.debug("range:%s", ipp)
                begin, end = ip_utils.split_ip(ipp)

                nbegin = ip_utils.ip_string_to_num(begin)
                nend = ip_utils.ip_string_to_num(end)
                self.ip_range_list.append([nbegin, nend])
            except:
                continue

    def get_ip(self):
        while True:
            ip_range = random.choice(self.ip_range_list)
            if ip_range[1] == ip_range[0]:
                return ip_utils.ip_num_to_string(ip_range[1])

            try:
                id_2 = random.randint(0, ip_range[1] - ip_range[0])
            except Exception as e:
                xlog.exception("random.randint:%r %d - %d, %d", e, ip_range[0], ip_range[1], ip_range[1] - ip_range[0])
                return

            ip = ip_range[0] + id_2

            return ip_utils.ip_num_to_string(ip)


ip_range = IpRange()