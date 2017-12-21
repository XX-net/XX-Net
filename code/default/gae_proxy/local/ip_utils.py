#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'moonshawdo@gamil.com'
from utils import *

def get_ip_maskc(ip_str):
    head = ".".join(ip_str.split(".")[:-1])
    return head + ".0"


def split_ip(strline):
    """从每组地址中分离出起始IP以及结束IP"""
    begin = ""
    end = ""
    if "-" in strline:
        num_regions = strline.split(".")
        if len(num_regions) == 4:
            "xxx.xxx.xxx-xxx.xxx-xxx"
            begin = ''
            end = ''
            for region in num_regions:
                if '-' in region:
                    s, e = region.split('-')
                    begin += '.' + s
                    end += '.' + e
                else:
                    begin += '.' + region
                    end += '.' + region
            begin = begin[1:]
            end = end[1:]

        else:
            "xxx.xxx.xxx.xxx-xxx.xxx.xxx.xxx"
            begin, end = strline.split("-")
            if 1 <= len(end) <= 3:
                prefix = begin[0:begin.rfind(".")]
                end = prefix + "." + end

    elif strline.endswith("."):
        "xxx.xxx.xxx."
        begin = strline + "0"
        end = strline + "255"
    elif "/" in strline:
        "xxx.xxx.xxx.xxx/xx"
        (ip, bits) = strline.split("/")
        if check_ip_valid4(ip) and (0 <= int(bits) <= 32):
            orgip = ip_string_to_num(ip)
            end_bits = (1 << (32 - int(bits))) - 1
            begin_bits = 0xFFFFFFFF ^ end_bits
            begin = ip_num_to_string(orgip & begin_bits)
            end = ip_num_to_string(orgip | end_bits)
    else:
        "xxx.xxx.xxx.xxx"
        begin = strline
        end = strline

    return begin, end
