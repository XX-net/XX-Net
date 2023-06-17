import unittest

import utils
import re

def split_the_ip(ip_str):
    # ips = utils.to_str(ip_str).split(":")[0:-1]
    # ip = ":".join(ips)

    ip_pattern = r'(?P<ip>(\d{1,3}\.){3}\d{1,3}|(\[[0-9a-fA-F:]+\])):(?P<port>\d+)'

    match = re.match(ip_pattern, ip_str)
    ip_address = match.group('ip')
    if '[' in ip_address:
        ip_address = ip_address[1:-1]
    port = match.group('port')
    return ip_address


class TestIP(unittest.TestCase):
    def test_check_ipv4(self):
        host = 'bat-bing-com.a-0001.a-msedge.net.'
        res = utils.check_ip_valid4(host)
        self.assertFalse(res)

    def test_private_ip(self):
        ip = 'bat-bing-com.a-0001.a-msedge.net.'
        res = utils.is_private_ip(ip)
        self.assertFalse(res)

    def test_merge_dict(self):
        x = {'a': 1, 'b': 2}
        y = {'b': 3, 'c': 4}
        z = utils.merge_two_dict(x, y)
        self.assertEqual(z, {
            'a': 1,
            'b': 3,
            'c': 4
        })

    def test_memory(self):
        buf = bytearray(8)
        mv = memoryview(buf)
        mv3 = mv[3:]
        print(len(mv3))

    def test_split_ip(self):
        ip_pattern = r'(?P<ip>(\d{1,3}\.){3}\d{1,3}|(\[[0-9a-fA-F:]+\])):(?P<port>\d+)'

        ip_port_str_1 = "127.0.0.1:8080"
        # Extract the IP address and port from the IPv4 string
        match = re.match(ip_pattern, ip_port_str_1)
        ip_address = match.group('ip')
        port = match.group('port')
        self.assertEqual(ip_address, "127.0.0.1")

        ip_port_str_1 = "[fffe:3465:efab::23fe]:8080"
        # Extract the IP address and port from the IPv4 string
        match = re.match(ip_pattern, ip_port_str_1)
        ip_address = match.group('ip')
        if '[' in ip_address:
            ip_address = ip_address[1:-1]
        port = match.group('port')
        self.assertEqual(ip_address, "fffe:3465:efab::23fe")

    def test_split_ip_fun(self):
        self.assertEqual(split_the_ip("127.0.0.1:8080"), "127.0.0.1")
        self.assertEqual(split_the_ip("[fffe:3465:efab::23fe]:8080"), "fffe:3465:efab::23fe")

    def test_utils_get_ip(self):
        ip, port = utils.get_ip_port("2400:8901::f03c:93ff:fe49:5c21")
        ip = utils.to_str(ip)
        self.assertEqual(ip, "2400:8901::f03c:93ff:fe49:5c21")
