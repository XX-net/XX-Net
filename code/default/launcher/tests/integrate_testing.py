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
import simple_http_server
from dnslib.dns import DNSRecord, DNSHeader, DNSQuestion
import socket

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

        # Lock for one integrate testing at the same time.
        # github act running in local will run multi python version in same VM, so we need to lock to avoid conflict.
        while True:
            try:
                res = simple_http_client.request("GET", "http://127.0.0.1:8888/test")
                if res and res.status == 200:
                    time.sleep(1)
                    continue
                else:
                    break
            except:
                break

        self.lock_server = simple_http_server.HTTPServer(('', 8888), simple_http_server.TestHttpServer, ".")
        self.lock_server.start()

        if self.check_web_console():
            xlog.info("APP was running externally.")
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
        self.smart_route_dns_query()
        self.smart_route_proxy_http()
        self.smart_route_proxy_socks4()
        self.smart_route_proxy_socks5()

        self.xtunnel_login()
        self.xtunnel_proxy_http()
        self.xtunnel_proxy_socks4()
        self.xtunnel_proxy_socks5()

        if not self.th:
            return

        self.stop_xxnet()

        self.check_log()

        self.lock_server.shutdown()

        for _ in range(30):
            if not self.th:
                return

            time.sleep(1)

        # If APP not exit, kill all python to exit, this script will also be killed.
        self.kill_python()

    def check_web_console(self):
        try:
            res = simple_http_client.request("GET", "http://127.0.0.1:8085/", timeout=1)
            return res is not None and res.status in [200, 404]
            # 404 is because act running locally may lost some folder. just bypass this error.
        except Exception as e:
            # xlog.debug("get web_console fail:%r", e)
            return False

    def get_xxnet_web_console(self, timeout=50):
        xlog.info("Start get xxnet web console.")
        t0 = time.time()
        t_end = t0 + timeout
        while time.time() < t_end and self.running:
            if not self.check_web_console():
                time.sleep(1)
                continue

            xlog.info("Got web console success.")
            return

        xlog.warn("Get Web Console timeout.")

    def xtunnel_logout(self):
        xlog.info("Start testing XTunnel logout")
        res = simple_http_client.request("POST", "http://127.0.0.1:8085/module/x_tunnel/control/logout", timeout=10)
        self.assertEqual(res.status, 200)
        self.xtunnel_login_status = False
        xlog.info("Finished testing XTunnel logout")

    def smart_route_proxy_http(self):
        xlog.info("Start testing SmartRouter HTTP proxy protocol")
        proxy = "http://localhost:8086"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=20)
        self.assertEqual(res.status, 200)
        xlog.info("Finished testing SmartRouter HTTP proxy protocol")

    def smart_route_proxy_socks4(self):
        xlog.info("Start testing SmartRouter SOCKS4 proxy protocol")
        proxy = "socks4://localhost:8086"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=15)
        self.assertEqual(res.status, 200)
        xlog.info("Finished testing SmartRouter SOCKS4 proxy protocol")

    def smart_route_proxy_socks5(self):
        xlog.info("Start testing SmartRouter SOCKS5 proxy protocol")
        proxy = "socks5://localhost:8086"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=15)
        self.assertEqual(res.status, 200)
        xlog.info("Finished testing SmartRouter SOCKS5 proxy protocol")

    def smart_route_dns_query(self):
        xlog.info("Start testing SmartRouter DNS Query")
        domain = "appsec.hicloud.com"
        d = DNSRecord(DNSHeader(123))
        d.add_question(DNSQuestion(domain, 1))
        req4_pack = d.pack()

        for port in [8053, 53]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(req4_pack, ("127.0.0.1", port))
            sock.settimeout(5)

            try:
                response, server = sock.recvfrom(8192)
            except Exception as e:
                xlog.warn("recv fail for port:%s e:%r", port, e)
                continue

            p = DNSRecord.parse(response)
            for r in p.rr:
                ip = utils.to_bytes(str(r.rdata))
                xlog.info("IP:%s" % ip)
                self.assertEqual(utils.check_ip_valid(ip), True)

            xlog.info("Finished testing SmartRouter DNS Query")
            return

    def xtunnel_login(self):
        xlog.info("Start testing XTunnel login")
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "username": [os.getenv("XTUNNEL_USER"),],
            "password": [os.getenv("XTUNNEL_PASS"),],
            "is_register": [0,]
        }
        data = json.dumps(data)
        res = simple_http_client.request("POST", "http://127.0.0.1:8085/module/x_tunnel/control/login",
                                         headers=headers, body=data, timeout=60)
        self.assertEqual(res.status, 200)
        self.xtunnel_login_status = True
        xlog.info("Finished testing XTunnel login")

    def xtunnel_proxy_http(self):
        xlog.info("Start testing XTunnel HTTP proxy protocol")
        if not self.xtunnel_login_status:
            self.xtunnel_login()
        proxy = "http://localhost:1080"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=30)
        self.assertEqual(res.status, 200)
        xlog.info("Finished testing XTunnel HTTP proxy protocol")

    def xtunnel_proxy_socks4(self):
        xlog.info("Start testing XTunnel Socks4 proxy protocol")
        if not self.xtunnel_login_status:
            self.xtunnel_login()
        proxy = "socks4://localhost:1080"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=15)
        self.assertEqual(res.status, 200)
        xlog.info("Finished testing XTunnel Socks4 proxy protocol")

    def xtunnel_proxy_socks5(self):
        xlog.info("Start testing XTunnel Socks5 proxy protocol")
        if not self.xtunnel_login_status:
            self.xtunnel_login()
        proxy = "socks5://localhost:1080"
        res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=15)
        self.assertEqual(res.status, 200)
        xlog.info("Finished testing XTunnel Socks5 proxy protocol")

    def start_xxnet(self):
        py_bin = sys.executable
        start_script = os.path.join(default_path, "launcher", "start.py")
        cmd = [py_bin, start_script]
        xlog.info("start APP cmd: %s" % cmd)
        try:
            self.pth = Popen(cmd, stdout=PIPE, stderr=STDOUT)  # , preexec_fn=os.setsid, shell=True, , bufsize=1
            for line in iter(self.pth.stdout.readline, b''):
                self.log_fp.write(line)
                self.log_fp.flush()
                line = line.strip()
                xlog.info("LOG|%s", line)
                if not self.running:
                    break
        except Exception as e:
            xlog.exception("run %s error:%r", cmd, e)

        xlog.info("xxnet quit.")
        self.running = False
        self.th = None

    def stop_xxnet(self):
        xlog.info("call api to Quit xxnet")
        try:
            res = simple_http_client.request("GET", "http://127.0.0.1:8085/quit", timeout=0.5)
            if res:
                xlog.info("Quit API res:%s", res.text)
            else:
                xlog.info("Quit API request failed.")
        except Exception as e:
            xlog.info("Quit API except:%r", e)

    def kill_python(self):
        self.running = False
        xlog.info("start kill python")
        if sys.platform == "win32":
            # This will kill this script as well.
            os.system("taskkill /F /im python.exe")
        else:
            os.system("pkill -9 -f 'start.py'")
        xlog.info("Finished kill python")

    def check_log(self):
        if not self.log_fn:
            # Debugging mode, running xxnet manually, check by human.
            return

        with open(self.log_fn, "r") as fp:
            for line in fp.readlines():
                line = line.strip()
                line = utils.to_str(line)

                self.assertNotIn("[ERROR]", line)

        xlog.info("Log Check passed!")

    def assertEqual(self, a, b):
        if not a == b:
            raise Exception("%s not equal %s" % (a, b))

    def assertNotIn(self, a, b):
        if a in b:
            raise Exception("%s in %s" % (a, b))


def run_testing():
    testing = ServiceTesting()
    try:
        testing.run()
    except Exception as e:
        xlog.exception("test failed:%r", e)
        testing.stop_xxnet()
        testing.kill_python()
        exit(1)


if __name__ == "__main__":
    run_testing()
