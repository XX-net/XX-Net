import json
import time
from unittest import TestCase
import os
import sys

import requests

current_path = os.path.dirname(os.path.abspath(__file__))
default_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
noarch_path = os.path.abspath(os.path.join(default_path, 'lib', "noarch"))
sys.path.append(noarch_path)
sys.path.append(default_path)

from dnslib.dns import DNSRecord, DNSQuestion, QTYPE
from smart_router.local.dns_query import LocalDnsQuery, DnsOverHttpsQuery, g


class MockConfig(object):
    def __init__(self):
        self.PROXY_ENABLE = False

class TestDnsQuery(TestCase):
    def test_local_udp_query(self):

        qr = LocalDnsQuery()
        ips = qr.query('www.microsoft.com', timeout=1000)
        self.assertTrue(len(ips) > 0)
        qr.stop()

    # def test_dns_server(self):
    #     query = DNSRecord(q=DNSQuestion("mtalk.google.com", getattr(QTYPE, "AAAA")))
    #     a_pkt = query.send("127.0.0.1", 53, tcp=False, timeout=5)
    #     a = DNSRecord.parse(a_pkt)
    #     print(a)

    def test_DoH_json_query(self):
        servers = [
            # "https://1.1.1.1/dns-query",
            # "https://dns10.quad9.net/dns-query",
            # "https://dns.aa.net.uk/dns-query",
            "https://doh.la.ahadns.net/dns-query"
        ]
        domain = "vs6.85po.com"
        for server in servers:
            url = server + "?name=" + domain + "&type=A"  # type need to map to Text.
            r = requests.request("GET", url, headers={"accept": "application/dns-json"})
            ips = []
            if not r:
                print(f"{server} failed")
                continue

            t = r.text.encode("utf-8")

            data = json.loads(t)
            for answer in data["Answer"]:
                ips.append(answer["data"])

            print(f"server:{server} ips: {ips}")

    def test_DoH_query(self):
        g.config = MockConfig()
        qr = DnsOverHttpsQuery()
        domain = "vs6.85po.com"
        for url in [
            "https://1.1.1.1/dns-query",
            "https://dns10.quad9.net/dns-query",
            "https://dns.aa.net.uk/dns-query",
            "https://freedns.controld.com/p0"
        ]:
            t0 = time.time()
            ips = qr.query(domain, url=url)
            t1 = time.time()
            print(f"use {url} ips:{ips} cost:{t1-t0}")
