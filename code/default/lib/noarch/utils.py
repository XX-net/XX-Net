#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import threading
from functools import reduce
from six import string_types

ipv4_pattern = re.compile(br'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')

ipv6_pattern = re.compile(br"""
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


def check_ip_valid4(ip):
    """检查ipv4地址的合法性"""
    ip = to_bytes(ip)
    ret = ipv4_pattern.match(ip)
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
    ip = to_bytes(ip)

    return ipv6_pattern.match(ip) is not None


def check_ip_valid(ip):
    ip = to_bytes(ip)
    if b'.' in ip:
        return check_ip_valid4(ip)
    else:
        return check_ip_valid6(ip)


def get_ip_port(ip_str, port=443):
    ip_str = to_bytes(ip_str)
    if b"." in ip_str:
        # ipv4
        if b":" in ip_str:
            # format is ip:port
            ps = ip_str.split(b":")
            ip = ps[0]
            port = ps[1]
        else:
            # format is ip
            ip = ip_str
    else:
        # ipv6
        if b"[" in ip_str:
            # format: [ab01:12:23:34::1]
            # format: [ab01:12:23:34::1]:23

            p1 = ip_str.find(b"[")
            p2 = ip_str.find(b"]")
            ip = ip_str[p1 + 1:p2]
            port_str = ip_str[p2 + 1:]
            if len(port_str) > 0:
                port = port_str[1:]
        else:
            ip = ip_str

    return ip, int(port)


domain_allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$")


def check_domain_valid(hostname):
    if len(hostname) > 255:
        return False
    if hostname.endswith("."):
        hostname = hostname[:-1]

    return all(domain_allowed.match(x) for x in hostname.split("."))


def str2hex(data):
    data = to_str(data)
    return ":".join("{:02x}".format(ord(c)) for c in data)


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


def generate_random_lowercase(n):
    min_lc = ord(b'a')
    len_lc = 26
    ba = bytearray(os.urandom(n))
    for i, b in enumerate(ba):
        ba[i] = min_lc + b % len_lc  # convert 0..255 to 97..122
    # sys.stdout.buffer.write(ba)
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
    host = to_bytes(host)
    hl = host.split(b".")
    return hl[0], b".".join(hl[1:])


def ip_string_to_num(s):
    """Convert dotted IPv4 address to integer."""
    return reduce(lambda a, b: a << 8 | b, list(map(int, s.split("."))))


def ip_num_to_string(ip):
    """Convert 32-bit integer to dotted IPv4 address."""
    return ".".join([str(ip >> n & 0xFF) for n in [24, 16, 8, 0]])


private_ipv4_range = [
    ("10.0.0.0", "10.255.255.255"),
    ("127.0.0.0", "127.255.255.255"),
    ("169.254.0.0", "169.254.255.255"),
    ("172.16.0.0", "172.31.255.255"),
    ("192.168.0.0", "192.168.255.255")
]

private_ipv6_range = [
    ("::1", "::1"),
    ("fc00::", "fdff:ffff:ffff:ffff:ffff:ffff:ffff:ffff")
]

private_ipv4_range_bin = []
for b, e in private_ipv4_range:
    bb = ip_string_to_num(b)
    ee = ip_string_to_num(e)
    private_ipv4_range_bin.append((bb, ee))


def is_private_ip(ip):
    ip = to_str(ip)
    try:
        if "." in ip:
            ip_bin = ip_string_to_num(ip)
            for b, e in private_ipv4_range_bin:
                if b <= ip_bin <= e:
                    return True
            return False
        else:
            if ip == "::1":
                return True

            fi = ip.find(":")
            if fi != 4:
                return False

            be = ip[0:2]
            if be in ["fc", "fd"]:
                return True
            else:
                return False
    except Exception as e:
        # print(("is_private_ip(%s), except:%r", ip, e))
        return False


import string

printable = set(string.printable)


def get_printable(s):
    return [x for x in s if x in printable]


def compare_version(version, reference_version):
    try:
        p = re.compile(r'([0-9]+)\.([0-9]+)\.([0-9]+)')
        m1 = p.match(version)
        m2 = p.match(reference_version)
        v1 = list(map(int, list(map(m1.group, [1, 2, 3]))))
        v2 = list(map(int, list(map(m2.group, [1, 2, 3]))))

        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
        else:
            return 0
    except Exception as e:
        print("older_or_equal fail: %s, %s" % (version, reference_version))
        raise e


def map_with_parameter(function, datas, args):
    l = []
    for data in datas:
        d_out = function(data, args)
        l.append(d_out)
    return l


def to_bytes(data, coding='utf-8'):
    if isinstance(data, bytes):
        return data
    if isinstance(data, string_types):
        return data.encode(coding)
    if isinstance(data, dict):
        return dict(map_with_parameter(to_bytes, data.items(), coding))
    if isinstance(data, tuple):
        return tuple(map_with_parameter(to_bytes, data, coding))
    if isinstance(data, list):
        return list(map_with_parameter(to_bytes, data, coding))
    if isinstance(data, int):
        return to_bytes(str(data))
    if data is None:
        return data
    return bytes(data)


def to_str(data, coding='utf-8'):
    if isinstance(data, string_types):
        return data
    if isinstance(data, bytes):
        return data.decode(coding)
    if isinstance(data, bytearray):
        return data.decode(coding)
    if isinstance(data, dict):
        return dict(map_with_parameter(to_str, data.items(), coding))
    if isinstance(data, tuple):
        return tuple(map_with_parameter(to_str, data, coding))
    if isinstance(data, list):
        return list(map_with_parameter(to_str, data, coding))
    if isinstance(data, int):
        return str(data)
    if data is None:
        return data
    return str(data)


def bytes2str_only(data, coding='utf-8'):
    if isinstance(data, bytes):
        return data.decode(coding)
    if isinstance(data, dict):
        return dict(map_with_parameter(bytes2str_only, data.items(), coding))
    if isinstance(data, tuple):
        return tuple(map_with_parameter(bytes2str_only, data, coding))
    if isinstance(data, list):
        return list(map_with_parameter(bytes2str_only, data, coding))
    else:
        return data


def merge_two_dict(x, y):
    """Given two dictionaries, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z


if __name__ == '__main__':
    # print(get_ip_port("1.2.3.4", 443))
    # print(get_ip_port("1.2.3.4:8443", 443))
    print((get_ip_port("[face:ab1:11::0]", 443)))
    print((get_ip_port("ab01::1", 443)))
    print((get_ip_port("[ab01:55::1]:8444", 443)))
