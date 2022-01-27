import unittest

import utils
import json
import simple_http_client


class HttpClientTest(unittest.TestCase):
    def test_get(self):
        client = simple_http_client.Client(timeout=10)
        url = "https://raw.githubusercontent.com/XX-net/XX-Net/master/code/default/x_tunnel/local/cloudflare_front/front_domains.json"
        res = client.request("GET", url)
        self.assertEquals(res.status, 200)
        content = utils.to_str(res.text)
        data = json.loads(content)
        print(data)
