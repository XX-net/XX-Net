import json
import os
import time
import sys
from subprocess import Popen, PIPE, STDOUT
import threading

current_path = os.path.dirname(os.path.abspath(__file__))
default_path = os.path.abspath(os.path.join(current_path, os.path.pardir, os.path.pardir))
root_path = os.path.abspath(os.path.join(default_path, os.path.pardir, os.path.pardir))

noarch_lib = os.path.abspath(os.path.join(default_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

import utils

import simple_http_client
from xlog import getLogger
xlog = getLogger("test")


class ServiceTesting(object):
    def __init__(self):
        self.xtunnel_login_status = False
        self.running = True

        self.pth = None
        self.log_fp = None
        self.log_fn = None

        if self.check_web_console():
            xlog.info("XX-Net was running externally.")
            self.th = None
            return

        self.log_fn = os.path.join(root_path, "running.log")
        if sys.version_info[0] == 3:
            self.log_fp = open(self.log_fn, "wb")
        else:
            self.log_fp = open(self.log_fn, "w")

        self.th = threading.Thread(target=self.start_xxnet)
        self.th.start()

    def __del__(self):
        if self.log_fp:
            self.log_fp.close()
            self.log_fp = None

    def run(self):
        self.get_xxnet_web_console()
        self.xtunnel_logout()
        self.smart_route_proxy_http()
        self.smart_route_proxy_socks4()
        self.smart_route_proxy_socks5()

        self.xtunnel_login()
        time.sleep(10)
        self.xtunnel_proxy_http()
        self.xtunnel_proxy_socks4()
        self.xtunnel_proxy_socks5()

        self.stop_xxnet()

        self.check_log()

        for _ in range(30):
            if not self.th:
                return

            time.sleep(1)

        # If XX-Net not exit, kill all python to exit, this script will also be killed.
        self.kill_python()

    def check_web_console(self):
        try:
            res = simple_http_client.request("GET", "http://127.0.0.1:8085/", timeout=30)
            return res is not None and res.status == 200
        except Exception as e:
            xlog.exception("get web_console fail:%r", e)
            return False

    def get_xxnet_web_console(self, timeout=15):
        t0 = time.time()
        t_end = t0 + timeout
        while time.time() < t_end and self.running:
            if not self.check_web_console():
                time.sleep(1)
                continue

            xlog.info("got web console")
            return

    def xtunnel_logout(self):
        res = simple_http_client.request("POST", "http://localhost:8085/module/x_tunnel/control/logout", timeout=10)
        self.assertEqual(res.status, 200)
        self.xtunnel_login_status = False

    def smart_route_proxy_http(self):
        proxy = "http://localhost:8086"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=20)
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
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=30)
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

    def start_xxnet(self):
        py_bin = sys.executable
        start_script = os.path.join(default_path, "launcher", "start.py")
        cmd = [py_bin, start_script]
        xlog.info("start XX-Net cmd: %s" % cmd)
        try:
            self.pth = Popen(cmd, stdout=PIPE, stderr=STDOUT, bufsize=1)  # , preexec_fn=os.setsid, shell=True,
            for line in iter(self.pth.stdout.readline, b''):
                self.log_fp.write(line)
                self.log_fp.flush()
                line = line.strip()
                xlog.info("LOG|%s", line)
        except Exception as e:
            xlog.exception("run %s error:%r", cmd, e)

        xlog.info("xxnet quit.")
        self.running = False
        self.th = None

    def stop_xxnet(self):
        xlog.info("call api to stop xxnet")

        try:
            simple_http_client.request("GET", "http://127.0.0.1:8085/quit", timeout=0.5)
        except:
            pass

    def kill_python(self):
        xlog.info("start kill python")
        if sys.platform == "win32":
            # This will kill this script as well.
            os.system("taskkill /im /F python.exe")
        else:
            os.system("pkill -9 -f 'start.py'")

    def check_log(self):
        if not self.log_fn:
            # Debugging mode, running xxnet manually, check by human.
            return

        with open(self.log_fn, "r") as fp:
            for line in fp.readlines():
                line = line.strip()
                line = utils.to_str(line)

                self.assertNotIn("[ERROR]", line)

    def assertEqual(self, a, b):
        if not a == b:
            raise Exception("%s not equal %s" % (a, b))

    def assertNotIn(self, a, b):
        if a in b:
            raise Exception("%s in %s" % (a, b))


if __name__ == "__main__":
    testing = ServiceTesting()
    try:
        testing.run()
    except Exception as e:
        xlog.exception("test failed:%r", e)
        testing.stop_xxnet()
        testing.kill_python()
        exit(1)
