
from unittest import TestCase

from dnslib.dns import DNSRecord, DNSQuestion, QTYPE
from smart_router.local.dns_query import LocalDnsQuery


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
