import os
import unittest
import time
import utils
import json
import simple_http_client
import tempfile


class HttpClientTest(unittest.TestCase):
    def test_get(self):
        client = simple_http_client.Client(timeout=10)
        url = "https://raw.githubusercontent.com/XX-net/XX-Net/master/code/default/x_tunnel/local/cloudflare_front/front_domains.json"
        res = client.request("GET", url)
        self.assertEqual(res.status, 200)
        content = utils.to_str(res.text)
        data = json.loads(content)
        print(data)

    def test_get2(self):
        url = "https://raw.githubusercontent.com/XX-net/XX-Net/master/code/default/update_v5.txt"

        client = simple_http_client.Client(timeout=10)
        res = client.request("GET", url)
        self.assertEqual(res.status, 200)
        content = utils.to_str(res.text)
        print(content)

    def test_get_fail(self):
        headers = {"connection": "close"}
        res = simple_http_client.request("GET", "http://127.0.0.1:2515/ping", headers=headers, timeout=0.5)
        self.assertIsNone(res)

    def test_get_bulk(self):
        timeout = 5
        client = simple_http_client.Client(timeout=timeout)
        url = "https://raw.githubusercontent.com/XX-net/XX-Net/master/code/default/update_v5.txt"

        start_time = time.time()
        req = client.request("GET", url, read_payload=False)
        self.assertIsNotNone(req)

        tp = tempfile.gettempdir()
        filename = os.path.join(tp, "v5.txt")
        if req.chunked:
            downloaded = 0
            with open(filename, 'wb') as fp:
                while True:
                    time_left = timeout - (time.time() - start_time)
                    if time_left < 0:
                        raise Exception("time out")

                    dat = req.read(timeout=time_left)
                    if not dat:
                        break

                    fp.write(dat)
                    downloaded += len(dat)

            return True
        else:
            file_size = int(req.getheader(b'Content-Length', 0))

            left = file_size
            downloaded = 0
            with open(filename, 'wb') as fp:
                while True:
                    chunk_len = min(65536, left)
                    if not chunk_len:
                        break

                    chunk = req.read(chunk_len)
                    if not chunk:
                        break
                    fp.write(chunk)
                    downloaded += len(chunk)
                    left -= len(chunk)
