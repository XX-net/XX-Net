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

gae_proxy_listen = "PROXY_LISTEN"


def get_serving_pacfile():
    if not os.path.isfile(user_pacfile):
        serving_pacfile = default_pacfile
    else:
        serving_pacfile = user_pacfile
    return serving_pacfile


class PacHandler(simple_http_server.HttpServerHandler):

    def do_GET(self):
        path = urlparse.urlparse(self.path).path # '/proxy.pac'
        filename = os.path.normpath('./' + path)
        if filename != 'proxy.pac':
            xlog.warn("pac_server GET %s fail", self.path)
            return self.send_not_found()

        pac_filename = get_serving_pacfile()
        with open(pac_filename, 'rb') as fp:
            data = fp.read()

        host = self.headers.getheader('Host')
        host, _, port = host.rpartition(":")
        gae_proxy_proxy = host + ":" + str(g.config.proxy_port)
        data = data.replace(gae_proxy_listen, gae_proxy_proxy)
        data = data.replace("BLACK_LIST", g.gfwlist.get_pac_string())
        self.send_response('text/plain', data)
