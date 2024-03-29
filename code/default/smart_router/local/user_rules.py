#!/usr/bin/env python
# coding:utf-8


import os


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))

import env_info
import utils
from xlog import getLogger
xlog = getLogger("smart_router")
data_path = os.path.join(env_info.data_path, "smart_router")


class Config(object):
    rule_list = ["direct", "gae", "socks", "black", "redirect_https"]

    def __init__(self):
        self.rule_lists = {}
        self.host_rules = {}
        self.end_rules = {}

        self.redirect_https_host_rules = ()
        self.redirect_https_end_rules = ()

        self.load()

    def save(self, rules_info):
        for section in self.rule_list:
            if section not in rules_info:
                continue

            value = rules_info[section]
            fn = os.path.join(data_path, "%s_list.txt" % section)
            with open(fn, "w") as fd:
                fd.write(value)

    def get_rules(self):
        rules_info = {
        }

        for section in self.rule_list:
            fn = os.path.join(data_path, "%s_list.txt" % section)
            if not os.path.isfile(fn):
                rules_info[section] = b""
                continue

            with open(fn, "r") as fd:
                content = fd.read()
                rules_info[section] = content

        return rules_info

    def parse_rules(self, content):
        end_fix = []
        hosts = []

        content = utils.to_bytes(content)

        content = content.replace(b",", b"\n").replace(b";", b"\n")
        lines = content.split(b"\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if b"=" in line:
                lp = line.split(b"=")
                left = lp[0].strip()
                right = lp[1].strip()
            else:
                left = line
                right = None

            if left.startswith(b"http://"):
                left = left[7:]
            if left.startswith(b"https://"):
                left = left[8:]
            if left.startswith(b"*"):
                left = left[1:]
            if b"/" in left:
                p = left.find(b"/")
                host = left[:p]
            else:
                host = left

            if host.startswith(b"."):
                end_fix.append(host)
            elif host.startswith(b"*."):
                end_fix.append(host[1:])
            else:
                hosts.append(host)

        return hosts, end_fix

    def load(self):
        self.host_rules = {}
        self.end_rules = {}

        for section in self.rule_list:
            self.rule_lists[section] = tuple()
            fn = os.path.join(data_path, "%s_list.txt" % section)
            if not os.path.isfile(fn):
                continue

            with open(fn, "r") as fd:
                content = fd.read()
                hosts, end_fix = self.parse_rules(content)
                self.rule_lists[section] = tuple(hosts + end_fix)
                if section == "redirect_https":
                    self.redirect_https_host_rules = tuple(utils.to_bytes(hosts))
                    self.redirect_https_end_rules = tuple(utils.to_bytes(end_fix))
                else:
                    for host in hosts:
                        self.host_rules[host] = section

                    if len(end_fix):
                        self.end_rules[section] = tuple(utils.to_bytes(end_fix))

    def check_host(self, domain, port=None):
        domain = utils.to_bytes(domain)
        if port == 80:
            if domain in self.redirect_https_host_rules or domain.endswith(self.redirect_https_end_rules):
                return "redirect_https"

        if domain in self.host_rules:
            return self.host_rules[domain]

        for sec in self.end_rules:
            try:
                if domain.endswith(self.end_rules[sec]):
                    return sec
            except Exception as e:
                xlog.exception("check_host domain:%s sec:%s self.end_rules[sec]", domain, sec, self.end_rules[sec])
