#!/usr/bin/env python
# coding:utf-8

import os
import urlparse


import simple_http_server

import global_var as g
from xlog import getLogger
xlog = getLogger("smart_router")


current_path = os.path.dirname(os.path.abspath(__file__))

root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
top_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir))
data_path = os.path.join(top_path, 'data', "smart_router")

default_pacfile = os.path.join(current_path, "proxy.pac")
user_pacfile = os.path.join(data_path, "proxy.pac")

gae_ca_file = os.path.join(top_path, 'data', "gae_proxy", "CA.crt")


allow_policy = ["black_GAE", "black_X-Tunnel", "smart-router"]


def get_serving_pacfile():
    if not os.path.isfile(user_pacfile):
        serving_pacfile = default_pacfile
    else:
        serving_pacfile = user_pacfile

    with open(serving_pacfile, 'rb') as fp:
        content = fp.read()

    return content


class PacHandler(simple_http_server.HttpServerHandler):
    PROXY_LISTEN = "PROXY_LISTEN"

    def policy_smart_router(self, host):
        content = """function FindProxyForURL(url, host) { return 'PROXY PROXY_LISTEN';}"""

        proxy = host + ":" + str(g.config.proxy_port)
        content = content.replace(self.PROXY_LISTEN, proxy)
        return content

    def policy_black_port(self, host, port):
        content = get_serving_pacfile()

        proxy = host + ":" + str(port)
        content = content.replace(self.PROXY_LISTEN, proxy)

        black, white = g.gfwlist.get_pac_string()
        content = content.replace("BLACK_LIST", black).replace("WHITE_LIST", white)
        return content

    def do_GET(self):
        path = urlparse.urlparse(self.path).path # '/proxy.pac'
        filename = os.path.normpath('./' + path)
        if filename != 'proxy.pac':
            xlog.warn("pac_server GET %s fail", self.path)
            return self.send_not_found()

        host = self.headers.getheader('Host')
        host, _, port = host.rpartition(":")

        if g.config.pac_policy == "black_GAE":
            content = self.policy_black_port(host, "8087")
        elif g.config.pac_policy == "black_X-Tunnel":
            content = self.policy_black_port(host, "1080")
        else:
            content = self.policy_smart_router(host)

        self.send_response('text/plain', content)
