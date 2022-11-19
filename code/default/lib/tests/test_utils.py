import unittest

import utils


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
