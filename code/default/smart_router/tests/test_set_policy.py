import requests
import re
from unittest import TestCase


class TestSetPolicy(TestCase):
    def test_set_global(self):
        url = "http://localhost:8085/module/smart_router/control/config"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "cmd": "set",
            "pac_policy": "all_X-Tunnel"
        }
        r = requests.post(url, json=data, headers=headers)
        print(r.text)

    def test_set_smart(self):
        url = "http://localhost:8085/module/smart_router/control/config"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "cmd": "set",
            "pac_policy": "smart-router"
        }
        r = requests.post(url, json=data, headers=headers)
        print(r.text)

    def test_match(self):
        r = re.compile("google|apple")
        s1 = "www.google.com"
        s2 = "www.apple.com"
        s3 = "www.ms.com"
        g1 = r.search(s1)
        print(g1)
        g2 = r.search(s2)
        print(g2)
        g3 = r.search(s3)
        print(g3)

    def test_re(self):
        strs = 'Test result 1: Not Ok -31.08'
        g = re.search(r'\bNot Ok\b', strs).group(0)
        print(g)