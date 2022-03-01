#!/usr/bin/env python
# coding:utf-8

import os

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

import simple_http_server

from . import global_var as g
from xlog import getLogger
xlog = getLogger("smart_router")
import utils

current_path = os.path.dirname(os.path.abspath(__file__))

root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
top_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir))
data_path = os.path.join(top_path, 'data', "smart_router")

default_pacfile = os.path.join(current_path, "proxy.pac")
user_pacfile = os.path.join(data_path, "proxy.pac")

gae_ca_file = os.path.join(top_path, 'data', "gae_proxy", "CA.crt")


allow_policy = ["black_GAE", "black_X-Tunnel", "smart-router", "all_X-Tunnel"]


def get_serving_pacfile():
    if not os.path.isfile(user_pacfile):
        serving_pacfile = default_pacfile
    else:
        serving_pacfile = user_pacfile

    with open(serving_pacfile, 'r') as fp:
        content = fp.read()

    return content


class PacHandler(simple_http_server.HttpServerHandler):
    PROXY_LISTEN = "PROXY_LISTEN"

    def policy_all_to_proxy(self, host, port):
        content = """function FindProxyForURL(url, host) { return 'PROXY PROXY_LISTEN';}"""

        proxy = host + ":" + str(port)
        content = content.replace(self.PROXY_LISTEN, proxy)
        return content

    def policy_blacklist_to_proxy(self, host, port):
        content = get_serving_pacfile()

        proxy = host + ":" + str(port)
        content = content.replace(self.PROXY_LISTEN, proxy)

        black_list = tuple([domain[1:] for domain in g.gfwlist.gfw_black_list])
        white_list = tuple([domain[1:] for domain in g.gfwlist.gfw_white_list])

        black = b'",\n"'.join(black_list
                             + g.user_rules.rule_lists["gae"]
                             + g.user_rules.rule_lists["socks"]
                             )
        white = b'",\n"'.join(white_list + g.user_rules.rule_lists["direct"])

        content = content.replace("BLACK_LIST", utils.to_str(black)).replace("WHITE_LIST", utils.to_str(white))
        return content

    def do_GET(self):
        path = urlparse(self.path).path # '/proxy.pac'
        path = utils.to_str(path)
        self.headers = utils.to_str(self.headers)

        filename = os.path.normpath('./' + path)
        if filename != 'proxy.pac':
            xlog.warn("pac_server GET %s fail", self.path)
            return self.send_not_found()

        host = self.headers.get('Host')
        host, _, port = host.rpartition(":")

        if g.config.pac_policy == "black_GAE":
            content = self.policy_blacklist_to_proxy(host, "%s" % g.gae_proxy_listen_port)
        elif g.config.pac_policy == "black_X-Tunnel":
            content = self.policy_blacklist_to_proxy(host, "%s" % g.x_tunnel_socks_port)
        elif g.config.pac_policy == "all_X-Tunnel":
            content = self.policy_all_to_proxy(host, "%s" % g.x_tunnel_socks_port)
        else:
            content = self.policy_all_to_proxy(host, g.config.proxy_port)

        self.send_response('application/x-ns-proxy-autoconfig', content)
