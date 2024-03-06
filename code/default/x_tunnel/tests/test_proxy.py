from unittest import TestCase
import json
import os
import time
import sys

current_path = os.path.dirname(os.path.abspath(__file__))
default_path = os.path.abspath(os.path.join(current_path, os.path.pardir, os.path.pardir))
root_path = os.path.abspath(os.path.join(default_path, os.path.pardir, os.path.pardir))

noarch_lib = os.path.abspath(os.path.join(default_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

import utils
import simple_http_server
from dnslib.dns import DNSRecord, DNSHeader, DNSQuestion
import socket

import simple_http_client
from xlog import getLogger
xlog = getLogger("test")


class ProxyTest(TestCase):
    def __init__(self):
        super().__init__()

    def test_xtunnel_logout(self):
        xlog.info("Start testing XTunnel logout")
        res = simple_http_client.request("POST", "http://127.0.0.1:8085/module/x_tunnel/control/logout", timeout=10)
        self.assertEqual(res.status, 200)
        self.xtunnel_login_status = False
        xlog.info("Finished testing XTunnel logout")

    def smart_route_proxy_http(self):
        xlog.info("Start testing SmartRouter HTTP proxy protocol")
        proxy = "http://localhost:8086"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=20)
        self.assertEqual(res.status, 200)
        xlog.info("Finished testing SmartRouter HTTP proxy protocol")

    def smart_route_proxy_socks4(self):
        xlog.info("Start testing SmartRouter SOCKS4 proxy protocol")
        proxy = "socks4://localhost:8086"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=15)
        self.assertEqual(res.status, 200)
        xlog.info("Finished testing SmartRouter SOCKS4 proxy protocol")

    def smart_route_proxy_socks5(self):
        xlog.info("Start testing SmartRouter SOCKS5 proxy protocol")
        proxy = "socks5://localhost:8086"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=15)
        self.assertEqual(res.status, 200)
        xlog.info("Finished testing SmartRouter SOCKS5 proxy protocol")

    def smart_route_dns_query(self):
        xlog.info("Start testing SmartRouter DNS Query")
        domain = "appsec.hicloud.com"
        d = DNSRecord(DNSHeader(123))
        d.add_question(DNSQuestion(domain, 1))
        req4_pack = d.pack()

        for port in [8053, 53]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(req4_pack, ("127.0.0.1", port))
            sock.settimeout(5)

            try:
                response, server = sock.recvfrom(8192)
            except Exception as e:
                xlog.warn("recv fail for port:%s e:%r", port, e)
                continue

            p = DNSRecord.parse(response)
            for r in p.rr:
                ip = utils.to_bytes(str(r.rdata))
                xlog.info("IP:%s" % ip)
                self.assertEqual(utils.check_ip_valid(ip), True)

            xlog.info("Finished testing SmartRouter DNS Query")
            return

    def xtunnel_token_login(self):
        xlog.info("Start testing XTunnel login")
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "login_token": os.getenv("XTUNNEL_TOKEN"),
        }
        data = json.dumps(data)
        res = simple_http_client.request("POST", "http://127.0.0.1:8085/module/x_tunnel/control/token_login",
                                         headers=headers, body=data, timeout=60)
        self.assertEqual(res.status, 200)
        self.xtunnel_login_status = True
        xlog.info("Finished testing XTunnel login")

    def test_xtunnel_proxy_http(self):
        xlog.info("Start testing XTunnel HTTP proxy protocol")
        # if not self.xtunnel_login_status:
        #     self.xtunnel_token_login()
        proxy = "http://localhost:1080"
        for _ in range(3):
            res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=30)
            if not res:
                time.sleep(5)
                continue
            self.assertEqual(res.status, 200)
            xlog.info("Finished testing XTunnel HTTP proxy protocol")

        self.assertEqual(res.status, 200)

    def xtunnel_proxy_socks4(self):
        xlog.info("Start testing XTunnel Socks4 proxy protocol")
        if not self.xtunnel_login_status:
            self.xtunnel_token_login()
        proxy = "socks4://localhost:1080"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=15)
        self.assertEqual(res.status, 200)
        xlog.info("Finished testing XTunnel Socks4 proxy protocol")

    def xtunnel_proxy_socks5(self):
        xlog.info("Start testing XTunnel Socks5 proxy protocol")
        if not self.xtunnel_login_status:
            self.xtunnel_token_login()
        proxy = "socks5://localhost:1080"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=15)
        self.assertEqual(res.status, 200)
        xlog.info("Finished testing XTunnel Socks5 proxy protocol")
