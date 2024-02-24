from unittest import TestCase
import json

import simple_http_client


class TestAPi(TestCase):
    def setUp(self):
        self.base_url = "http://localhost:8085"

    def test_set_proxy_applist(self):
        url = self.base_url + "/set_proxy_applist"
        headers = {
            "Content-Type": "application/json"
        }
        info = {
            'proxy_by_app': "true",
            'enabled_app_list[]': [
                "com.google.android.youtube"
            ]
        }
        dat = json.dumps(info)

        res = simple_http_client.request("POST", url, headers=headers, body=dat)
        print(res.text)
