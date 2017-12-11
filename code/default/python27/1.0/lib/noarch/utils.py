#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import threading

g_ip_check = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')


def check_ip_valid4(ip):
    """检查ipv4地址的合法性"""
    ret = g_ip_check.match(ip)
    if ret is not None:
        "each item range: [0,255]"
        for item in ret.groups():
            if int(item) > 255:
                return 0
        return 1
    else:
        return 0


def check_ip_valid6(ip):
    """Copied from http://stackoverflow.com/a/319293/2755602"""
    """Validates IPv6 addresses.
    """
    pattern = re.compile(r"""
        ^
        \s*                         # Leading whitespace
        (?!.*::.*::)                # Only a single whildcard allowed
        (?:(?!:)|:(?=:))            # Colon iff it would be part of a wildcard
        (?:                         # Repeat 6 times:
            [0-9a-f]{0,4}           #   A group of at most four hexadecimal digits
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
        ){6}                        #
        (?:                         # Either
            [0-9a-f]{0,4}           #   Another group
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
            [0-9a-f]{0,4}           #   Last group
            (?: (?<=::)             #   Colon iff preceeded by exacly one colon
             |  (?<!:)              #
             |  (?<=:) (?<!::) :    #
             )                      # OR
         |                          #   A v4 address with NO leading zeros
            (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            (?: \.
                (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            ){3}
        )
        \s*                         # Trailing whitespace
        $
    """, re.VERBOSE | re.IGNORECASE | re.DOTALL)
    return pattern.match(ip) is not None


def check_ip_valid(ip):
    if ':' in ip:
        return check_ip_valid6(ip)
    else:
        return check_ip_valid4(ip)


domain_allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$")


def check_domain_valid(hostname):
    if len(hostname) > 255:
        return False
    if hostname.endswith("."):
        hostname = hostname[:-1]

    return all(domain_allowed.match(x) for x in hostname.split("."))


def str2hex(data):
    return ":".join("{:02x}".format(ord(c)) for c in data)


def generate_random_lowercase(n):
    min_lc = ord(b'a')
    len_lc = 26
    ba = bytearray(os.urandom(n))
    for i, b in enumerate(ba):
        ba[i] = min_lc + b % len_lc # convert 0..255 to 97..122
    #sys.stdout.buffer.write(ba)
    return ba


class SimpleCondition(object):
    def __init__(self):
        self.lock = threading.Condition()

    def notify(self):
        self.lock.acquire()
        self.lock.notify()
        self.lock.release()

    def wait(self):
        self.lock.acquire()
        self.lock.wait()
        self.lock.release()


def split_domain(host):
    hl = host.split(".")
    return hl[0], ".".join(hl[1:])
