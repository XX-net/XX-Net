import json
import unittest
import os
import sys
from subprocess import Popen, PIPE, STDOUT
import threading
import time
import signal

import simple_http_client
from xlog import getLogger
xlog = getLogger("test")

current_path = os.path.dirname(os.path.abspath(__file__))
default_path = os.path.abspath(os.path.join(current_path, os.path.pardir, os.path.pardir))


class RunningTest(unittest.TestCase):
    def setUp(self):
        self.pth = None
        if not self.check_web_console():
            self.th = threading.Thread(target=self.start_xxnet)
            self.th.start()
        else:
            self.th = None

        self.xtunnel_login_status = False
        self.running = True

    def tearDown(self):
        if self.pth:
            self.stop_xxnet()
            os.killpg(os.getpgid(self.pth.pid), signal.SIGTERM)

            while self.th:
                self.stop_xxnet()
                time.sleep(1)

    def test_basic_running(self):
        self.get_xxnet_web_console()
        self.xtunnel_logout()
        self.smart_route_proxy_http()
        self.smart_route_proxy_socks4()
        self.smart_route_proxy_socks5()

        self.xtunnel_login()
        self.xtunnel_proxy_http()
        self.xtunnel_proxy_socks4()
        self.xtunnel_proxy_socks5()

    def check_web_console(self):
        res = simple_http_client.request("GET", "http://127.0.0.1:8085/", timeout=10)
        return res is not None and res.status == 200

    def get_xxnet_web_console(self, timeout=1000):
        t0 = time.time()
        t_end = t0 + timeout
        while time.time() < t_end and self.running:
            if not self.check_web_console():
                time.sleep(1)
                continue

            xlog.info("got web console")
            return

        self.assertFalse(True)

    def xtunnel_logout(self):
        res = simple_http_client.request("POST", "http://localhost:8085/module/x_tunnel/control/logout", timeout=1)
        self.assertEqual(res.status, 200)
        self.xtunnel_login_status = False

    def smart_route_proxy_http(self):
        proxy = "http://localhost:8086"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=15)
        self.assertEqual(res.status, 200)

    def smart_route_proxy_socks4(self):
        proxy = "socks4://localhost:8086"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=15)
        self.assertEqual(res.status, 200)

    def smart_route_proxy_socks5(self):
        proxy = "socks5://localhost:8086"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=15)
        self.assertEqual(res.status, 200)

    def xtunnel_login(self):
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "username": [os.getenv("XTUNNEL_USER"),],
            "password": [os.getenv("XTUNNEL_PASS"),],
            "is_register": [0,]
        }
        data = json.dumps(data)
        res = simple_http_client.request("POST", "http://localhost:8085/module/x_tunnel/control/login",
                                         headers=headers, body=data, timeout=15)
        self.assertEqual(res.status, 200)
        self.xtunnel_login_status = True

    def xtunnel_proxy_http(self):
        if not self.xtunnel_login_status:
            self.xtunnel_login()
        proxy = "http://localhost:1080"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=15)
        self.assertEqual(res.status, 200)

    def xtunnel_proxy_socks4(self):
        if not self.xtunnel_login_status:
            self.xtunnel_login()
        proxy = "socks4://localhost:1080"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=15)
        self.assertEqual(res.status, 200)

    def xtunnel_proxy_socks5(self):
        if not self.xtunnel_login_status:
            self.xtunnel_login()
        proxy = "socks5://localhost:1080"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=15)
        self.assertEqual(res.status, 200)

    def stop_xxnet(self):
        xlog.info("ask to stop xxnet")

        try:
            simple_http_client.request("GET", "http://127.0.0.1:8085/quit", timeout=0.5)
        except:
            pass

    def start_xxnet(self):
        py_bin = sys.executable
        start_script = os.path.join(default_path, "launcher", "start.py")
        cmd = [py_bin, start_script]
        xlog.info("cmd: %s" % cmd)
        try:
            self.pth = Popen(cmd, stdout=PIPE, stderr=STDOUT, bufsize=1)  # , preexec_fn=os.setsid
            # for line in stream.stdout:
            for line in iter(self.pth.stdout.readline, b''):
                line = line.strip()
                print(b"LOG|%s" % line)
                self.assertNotIn(b"[ERROR]", line)
        except Exception as e:
            xlog.exception("run %s error:%r", cmd, e)

        xlog.info("xxnet exit.")
        self.running = False
        self.th = None
