#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Based on checkgoogleip by  <moonshawdo@gmail.com>
import random
import time
import os
import sys
import struct
import threading


random.seed(time.time()* 1000000)

current_path = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))

    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)

    if sys.platform == "win32":
        win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
        sys.path.append(win32_lib)
    elif sys.platform.startswith("linux"):
        linux_lib = os.path.abspath( os.path.join(python_path, 'lib', 'linux'))
        sys.path.append(linux_lib)


import ip_utils
from config import config
from xlog import getLogger
xlog = getLogger("gae_proxy")


class IpPool(object):
    def __init__(self):
        self.txt_ip_fn = os.path.join(current_path, "ip_checked.txt")
        self.bin_ip_fn = os.path.join(config.DATA_PATH, "ip_checked.bin")
        self.bin_fd = None
        threading.Thread(target=self.init).start()

    def init(self):
        if not self.check_bin():
            self.generate_bin()
        self.bin_fd = open(self.bin_ip_fn, "rb")
        self.bin_size = os.path.getsize(self.bin_ip_fn)

    def check_bin(self):
        if not os.path.isfile(self.bin_ip_fn):
            return False

        if os.path.getmtime(self.bin_ip_fn) < os.path.getmtime(self.txt_ip_fn):
            return False

        return True

    def generate_bin(self):
        xlog.info("generating binary ip pool file.")
        rfd = open(self.txt_ip_fn, "rt")
        wfd = open(self.bin_ip_fn, "wb")
        num = 0
        for line in rfd.readlines():
            ip = line
            try:
                ip_num = ip_utils.ip_string_to_num(ip)
            except Exception as e:
                xlog.warn("ip %s not valid in %s", ip, self.txt_ip_fn)
                continue
            ip_bin = struct.pack("<I", ip_num)
            wfd.write(ip_bin)
            num += 1

        rfd.close()
        wfd.close()
        xlog.info("finished generate binary ip pool file, num:%d", num)

    def random_get_ip(self):
        while self.bin_fd is None:
            time.sleep(1)
        for _ in range(5):
            position = random.randint(0, self.bin_size/4) * 4
            self.bin_fd.seek(position)
            ip_bin = self.bin_fd.read(4)
            if ip_bin is None:
                xlog.warn("ip_pool.random_get_ip position:%d get None", position)
            elif len(ip_bin) != 4:
                xlog.warn("ip_pool.random_get_ip position:%d len:%d", position, len(ip_bin))
            else:
                ip_num = struct.unpack("<I", ip_bin)[0]
                ip = ip_utils.ip_num_to_string(ip_num)
                return ip
        time.sleep(3)
        raise Exception("get ip fail.")


class IpRange(object):
    def __init__(self):
        self.default_range_file = os.path.join(current_path, "ip_range.txt")
        self.user_range_file = os.path.join(config.DATA_PATH, "ip_range.txt")

        self.ipv6_scan_ratio = config.CONFIG.getint("google_ip", "ipv6_scan_ratio")
        ip_source = config.CONFIG.get("google_ip", "ip_source")
        if ip_source == "ip_pool":
            self.ip_pool = IpPool()
            self.get_ipv4 = self.ip_pool.random_get_ip
            xlog.info("Use google ip pool.")
        else:
            self.load_ip_range()

        self.ipv6_list = []
        self.load_ipv6()

    def load_ipv6(self):
        with open(os.path.join(current_path, "good_ipv6.txt"), "r") as fd:
            for line in fd.readlines():
                if not line:
                    continue
                try:
                    lp = line.split()
                    ip = lp[0]
                    if not ip:
                        continue

                    self.ipv6_list.append(ip)
                except:
                    continue

    def load_range_content(self, default=False):
        if not default and os.path.isfile(self.user_range_file):
            fd = open(self.user_range_file, "r")
            if fd:
                content = fd.read()
                fd.close()
                if len(content) > 10:
                    xlog.info("load ip range file:%s", self.user_range_file)
                    return content

        xlog.info("load ip range file:%s", self.default_range_file)
        fd = open(self.default_range_file, "r")
        if not fd:
            xlog.error("load ip range %s fail", self.default_range_file)
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

    def get_ip(self, use_ipv6=None):
        if use_ipv6 is None:
            use_ipv6 = config.USE_IPV6

        if use_ipv6 == "force_ipv4":
            return self.get_ipv4()
        elif use_ipv6 == "force_ipv6":
            return self.get_ipv6()
        else:
            if use_ipv6 != "auto":
                xlog.warn("IpRange get_ip but use_ip is %s", use_ipv6)

            ran = random.randint(0, 100)
            if ran < self.ipv6_scan_ratio:
                return self.get_ipv6()
            else:
                return self.get_ipv4()

    def get_ipv4(self):
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

    def get_ipv6(self):
        return random.choice(self.ipv6_list)


ip_range = IpRange()


if __name__ == '__main__':
    ip = ip_range.get_ip()
    print (ip)