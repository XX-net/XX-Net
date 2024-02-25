#!/usr/bin/env python
# coding:utf-8


import os
import sys
import base64
import re
import socket
import struct
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))

if __name__ == '__main__':
    python_path = root_path
    noarch_lib = os.path.abspath(os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)


import env_info
import utils
from xlog import getLogger
xlog = getLogger("smart_router")

data_path = os.path.join(env_info.data_path, "smart_router")


class IpMask(object):
    def __init__(self, ip_masks):
        self.masks = self.generate_masks(ip_masks)

    def makeMask(self, n):
        # return a mask of n bits as a long integer
        return (2 << int(n) - 1) - 1

    def dottedQuadToNum(self, ip):
        # convert decimal dotted quad string to long integer
        try:
            i = socket.inet_aton(ip)
        except Exception as e:
            xlog.exception("inet_aton e:%r", e)

        return struct.unpack('I', i)[0]

    def networkMask(self, ip, bits):
        # Convert a network address to a long integer
        return self.dottedQuadToNum(ip) & self.makeMask(bits)

    def generate_masks(self, ip_masks):
        masks = []
        for ip_mask in ip_masks:
            ip, m = ip_mask.split("/")
            mask = self.networkMask(ip, m)
            masks.append(mask)

        return tuple(masks)

    def check_ip(self, ip):
        address = self.dottedQuadToNum(ip)
        for mask in self.masks:
            if address & mask == mask:
                return True

        return False


class GfwList(object):
    def __init__(self):
        # self.gfw_black_list = utils.to_bytes(self.load("gfw_black_list.txt"))
        # https://johnshall.github.io/Shadowrocket-ADBlock-Rules-Forever/sr_top500_banlist.conf
        self.gfw_black_list, ip_masks, keywords = self.load_banlist("sr_top500_banlist.conf")
        self.keyword_re = re.compile("|".join(keywords))
        self.black_subnets = IpMask(ip_masks)
        self.gfw_white_list = utils.to_bytes(self.load("gfw_white_list.txt"))
        self.speedtest_whitelist = utils.to_bytes(self.load("speedtest_whitelist.txt"))
        self.advertisement_list = utils.to_bytes(self.load("advertisement_list.txt"))
        # xlog.debug("white_list size:%d mem:%d", len(self.gfw_white_list), sys.getsizeof(self.gfw_white_list))
        # xlog.debug("black_list size:%d mem:%d", len(self.gfw_black_list), sys.getsizeof(self.gfw_black_list))

    @staticmethod
    def load(name):
        user_file = os.path.join(data_path, name)
        if os.path.isfile(user_file):
            list_file = user_file
        else:
            list_file = os.path.join(current_path, name)

        xlog.info("Load file:%s", list_file)

        with open(list_file, "r") as fd:
            gfwdict = {}
            for line in fd.readlines():
                line = line.strip()
                if not line:
                    continue

                gfwdict["." + line] = 1

        gfwlist = [h for h in gfwdict]
        return tuple(gfwlist)

    def load_banlist(self, fn):
        gfwdict = {}
        ip_masks = []
        keywords = []
        list_file = os.path.join(current_path, fn)
        with open(list_file, "rb") as fd:
            for line in fd.readlines():
                line = utils.to_str(line.strip())
                if not line or line.startswith("#") or line.startswith("["):
                    continue

                if line.startswith("DOMAIN-SUFFIX,"):
                    suffix = line.split(",")[1]
                    gfwdict["." + suffix] = 1

                if line.startswith("IP-CIDR,"):
                    ip_mask = line.split(",")[1]
                    if ":" not in ip_mask:
                        ip_masks.append(ip_mask)

                if line.startswith("DOMAIN-KEYWORD,"):
                    keyword = line.split(",")[1]
                    keywords.append(keyword)

        gfwlist = [h for h in gfwdict]
        return tuple(utils.to_bytes(gfwlist)), ip_masks, keywords

    def ip_in_black_list(self, ip):
        return self.black_subnets.check_ip(ip)

    def in_block_list(self, host):
        dot_host = b"." + utils.to_bytes(host)
        if dot_host.endswith(self.gfw_black_list):
            return True
        elif self.keyword_re.search(utils.to_str(host)):
            return True
        else:
            return False

    def in_white_list(self, host):
        dot_host = b"." + host
        if dot_host.endswith(self.gfw_white_list):
            return True
        else:
            return False

    def in_speedtest_whitelist(self, host):
        dot_host = b"." + host
        if dot_host.endswith(self.speedtest_whitelist):
            return True
        else:
            return False

    def is_advertisement(self, host):
        dot_host = b"." + host
        if dot_host.endswith(self.advertisement_list):
            return True
        else:
            return False


class UpdateGFWList(object):
    white_list_fn = os.path.join(current_path, "gfw_white_list.txt")
    black_list_fn = os.path.join(current_path, "gfw_black_list.txt")

    def __init__(self):
        self.white_list = self.load_white_list()

    def load_white_list(self):
        white_list = []
        with open(self.white_list_fn, "r") as fd:
            for line in fd.readlines():
                domain = line.strip()
                if domain not in white_list:
                    white_list.append(domain)

        return white_list

    def download_update_white_list(self):
        import subprocess
        url = 'https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/accelerated-domains.china.conf'
        try:
            data = subprocess.check_output(['wget', url, '-O-'])
        except (OSError, AttributeError):
            xlog.info("Fetching data from apnic.net, it might take a few minutes, please wait...")
            data = urlopen(url).read()

        for line in data.split(b"\n"):
            line = line.strip()
            line = utils.to_str(line)
            pl = line.split("/")
            if len(pl) != 3:
                xlog.warn("line:%s", line)
                continue
            domain = pl[1]
            if domain in self.white_list:
                continue

            self.white_list.append(domain)
            xlog.debug("white list add:%s", domain)

    def download_update_gfwlist(self):
        import subprocess
        url = 'https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt'
        try:
            data = subprocess.check_output(['wget', url, '-O-'])
        except (OSError, AttributeError):
            xlog.info("Fetching data from apnic.net, it might take a few minutes, please wait...")
            data = urlopen(url).read()

        data = base64.b64decode(data)

        with open("gfwlist.txt", "w") as fd:
            for line in data.split(b"\n"):
                line = line.strip()
                line = utils.to_str(line)
                if line.startswith("!"):
                    continue

                xlog.debug("%s", line)
                fd.write("%s\n" % line)

                if not line.startswith("@@"):
                    continue

                domain = line[2:]
                if domain.startswith("http://"):
                    domain = domain[7:]
                elif domain.startswith("https://"):
                    domain = domain[8:]

                if domain in self.white_list:
                    continue

                self.white_list.append(domain)
                xlog.debug("white list add:%s", domain)

    def save_white_list(self):
        self.white_list.sort()

        with open(self.white_list_fn, "w") as fd:
            for domain in self.white_list:
                fd.write("%s\n" % domain)

        xlog.info("white list updated to %s", self.white_list_fn)


if __name__ == "__main__":
    updater = UpdateGFWList()
    updater.download_update_white_list()
    updater.save_white_list()
