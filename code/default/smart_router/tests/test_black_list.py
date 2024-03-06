import os
from os.path import join
import sys
import unittest


current_path = os.path.dirname(os.path.abspath(__file__))
smart_route_path = os.path.abspath(os.path.join(current_path, os.path.pardir))
local_path = os.path.join(smart_route_path, "local")
sys.path.append(local_path)

default_path = os.path.abspath(join(smart_route_path, os.path.pardir))
noarch_path = join(default_path, "lib", "noarch")
sys.path.append(noarch_path)

import gfwlist


class TestGFW(unittest.TestCase):
    def test_Ip_Mask(self):
        ip = "1.2.3.4"
        ip_mask = "1.2.3.0/24"
        ip_masks = [ip_mask]
        subnets = gfwlist.IpMask(ip_masks)
        c = subnets.check_ip(ip)
        print(c)

        print(subnets.check_ip("1.2.3.5"))
        print(subnets.check_ip("1.2.4.5"))
        print(subnets.check_ip("1.3.4.5"))

    def test_domain(self):
        gfw = gfwlist.GfwList()
        print(gfw.ip_in_black_list("91.108.56.1"))
        print(gfw.ip_in_black_list("1.1.1.1"))

    def test_keyword(self):
        gfw = gfwlist.GfwList()
        print(gfw.in_block_list(b"www.amazon.com"))
        print(gfw.in_block_list(b"www.apple.com"))
