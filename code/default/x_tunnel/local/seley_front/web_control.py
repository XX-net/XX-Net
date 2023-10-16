#!/usr/bin/env python
# coding:utf-8


import os
import time

try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs


import simple_http_server
from .front import front


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
top_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, os.pardir))
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
        elif path == "/debug":
            return self.req_debug_handler()
        else:
            front.logger.warn('Control Req %s %s %s ', self.address_string(), self.command, self.path)

        self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Not Found')
        front.logger.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def req_log_handler(self):
        req = urlparse(self.path).query
        reqs = parse_qs(req, keep_blank_values=True)
        data = ''

        cmd = "get_last"
        if reqs["cmd"]:
            cmd = reqs["cmd"][0]

        if cmd == "get_last":
            max_line = int(reqs["max_line"][0])
            data = front.logger.get_last_lines(max_line)
        elif cmd == "get_new":
            last_no = int(reqs["last_no"][0])
            data = front.logger.get_new_lines(last_no)
        else:
            front.logger.error('PAC %s %s %s ', self.address_string(), self.command, self.path)

        mimetype = 'text/plain'
        self.send_response_nc(mimetype, data)

    def req_debug_handler(self):
        if not front.running:
            return self.send_response_nc('text/plain', "Not running")

        data = ""
        for obj in [front.connect_manager, front.http_dispatcher]:
            data += "%s\r\n" % obj.__class__
            for attr in dir(obj):
                if attr.startswith("__"):
                    continue
                sub_obj = getattr(obj, attr)
                if callable(sub_obj):
                    continue

                if isinstance(sub_obj, list):
                    data += "    %s:\r\n" % (attr)
                    for item in sub_obj:
                        data += "      %s\r\n" % item
                    data += "\r\n"
                elif hasattr(sub_obj, "to_string"):
                    data += "    %s:\r\n" % (attr)
                    data += sub_obj.to_string()
                else:
                    data += "    %s = %s\r\n" % (attr, sub_obj)
            if hasattr(obj, "to_string"):
                data += obj.to_string()

        mimetype = 'text/plain'
        self.send_response_nc(mimetype, data)