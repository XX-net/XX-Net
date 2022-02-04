
from unittest import TestCase

from smart_router.local.dns_query import LocalDnsQuery


class TestDnsQuery(TestCase):
    def test_local_udp_query(self):
        qr = LocalDnsQuery()
        ips = qr.query('www.microsoft.com', timeout=1000)
        self.assertTrue(len(ips) > 0)
        qr.stop()
