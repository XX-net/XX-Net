#!/usr/bin/env python
# coding:utf-8

import os

try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs

from xlog import getLogger
xlog = getLogger("smart_router")

import simple_http_server
from . import pac_server
from . import global_var as g

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
web_ui_path = os.path.join(current_path, os.path.pardir, "web_ui")


class ControlHandler(simple_http_server.HttpServerHandler):
    def __init__(self, client_address, headers, command, path, rfile, wfile):
        self.client_address = client_address
        self.headers = headers
        self.command = command
        self.path = path
        self.rfile = rfile
        self.wfile = wfile

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/log":
            return self.req_log_handler()
        elif path == "/status":
            return self.req_status()
        else:
            xlog.warn('Control Req %s %s %s ', self.address_string(), self.command, self.path)

    def do_POST(self):
        xlog.debug('Web_control %s %s %s ', self.address_string(), self.command, self.path)

        path = urlparse(self.path).path
        if path == '/rules':
            return self.req_rules_handler()
        elif path == "/cache":
            return self.req_cache_handler()
        elif path == "/config":
            return self.req_config_handler()
        else:
            xlog.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)
            return self.send_not_found()

    def req_log_handler(self):
        req = urlparse(self.path).query
        reqs = self.unpack_reqs(parse_qs(req, keep_blank_values=True))
        data = ''

        if reqs["cmd"]:
            cmd = reqs["cmd"]
        else:
            cmd = "get_last"

        if cmd == "get_last":
            max_line = int(reqs["max_line"])
            data = xlog.get_last_lines(max_line)
        elif cmd == "get_new":
            last_no = int(reqs["last_no"])
            data = xlog.get_new_lines(last_no)
        else:
            xlog.error('xtunnel log cmd:%s', cmd)

        mimetype = 'text/plain'
        self.send_response(mimetype, data)

    def req_rules_handler(self):
        reqs = self.postvars

        if "cmd" in reqs and reqs["cmd"]:
            cmd = reqs["cmd"]
        else:
            cmd = "get"

        if cmd == "get":
            rules = g.user_rules.get_rules()
            rules["res"] = "success"
            return self.response_json(rules)
        elif cmd == "set":
            g.user_rules.save(reqs)
            g.user_rules.load()
            return self.response_json({"res": "OK"})

    def req_config_handler(self):
        reqs = self.postvars
        if "cmd" in reqs and reqs["cmd"]:
            cmd = reqs["cmd"]
        else:
            cmd = "get"

        if cmd == "get":
            data = {
                "gae_enabled": g.gae_proxy is not None,
                "pac_policy": g.config.pac_policy,
                "country": g.config.country_code,
                "auto_direct":g.config.auto_direct,
                "auto_direct6":g.config.auto_direct6,
                "auto_gae": g.config.auto_gae,
                "enable_fake_ca": g.config.enable_fake_ca,
                "bypass_speedtest": g.config.bypass_speedtest,
                "block_advertisement": g.config.block_advertisement
            }
            return self.response_json(data)
        elif cmd == "set":
            if "pac_policy" in reqs:
                pac_policy = reqs["pac_policy"]
                if pac_policy not in pac_server.allow_policy:
                    return self.response_json({"res": "fail", "reason": "policy not allow"})

                g.config.pac_policy = pac_policy
            if "country" in reqs:
                g.config.country_code = reqs["country"]
            if "auto_direct" in reqs:
                g.config.auto_direct = int(reqs["auto_direct"])
            if "auto_direct6" in reqs:
                g.config.auto_direct6 = int(reqs["auto_direct6"])
            if "auto_gae" in reqs:
                g.config.auto_gae = int(reqs["auto_gae"])
            if "enable_fake_ca" in reqs:
                g.config.enable_fake_ca = int(reqs["enable_fake_ca"])
            if "bypass_speedtest" in reqs:
                g.config.bypass_speedtest = int(reqs["bypass_speedtest"])
            if "block_advertisement" in reqs:
                g.config.block_advertisement = int(reqs["block_advertisement"])
            g.config.save()
            return self.response_json({"res": "success"}, headers={"Access-Control-Allow-Origin": "*"})

    def req_cache_handler(self):
        reqs = self.postvars
        if "cmd" in reqs and reqs["cmd"]:
            cmd = reqs["cmd"]
        else:
            cmd = "get"

        if cmd == "get":
            g.domain_cache.save(True)
            g.ip_cache.save(True)
            data = {
                "domain_cache_list": g.domain_cache.get_content(),
                "ip_cache_list": g.ip_cache.get_content(),
                "res": "success"
            }
            return self.response_json(data)
        elif cmd == "clean":
            g.domain_cache.clean()
            g.ip_cache.clean()
            return self.response_json({"res": "success"})

    def req_status(self):
        out_str = "pipe status:\n" + str(g.pipe_socks)
        self.send_response("text/plain", out_str)

