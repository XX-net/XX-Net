import unittest
import utils
import simple_http_client
import simple_http_server


class HttpClientTest(unittest.TestCase):
    def test_get(self):
        server = simple_http_server.HTTPServer(('', 8880), simple_http_server.TestHttpServer, ".")
        server.start()

        client = simple_http_client.Client(timeout=5)
        url = "http://localhost:8880/test"
        res = client.request("GET", url)
        self.assertEqual(res.status, 200)
        content = utils.to_str(res.text)
        print(content)

        server.shutdown()
