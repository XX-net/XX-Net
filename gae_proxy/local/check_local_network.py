
import sys
import os

import http.client
import time
import socket
import threading

if __name__ == "__main__":
    current_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
    gae_path = os.path.join(root_path, "gae_proxy")
    sys.path.append(gae_path)

    noarch_lib = os.path.join(root_path, 'lib', 'noarch')
    sys.path.append(noarch_lib)
    common_lib = os.path.join(root_path, 'lib', 'common')
    sys.path.append(common_lib)

    if sys.platform == "win32":
        win32_lib = os.path.join(root_path, 'lib', 'win32')
        sys.path.append(win32_lib)
    elif sys.platform.startswith("linux"):
        linux_lib = os.path.join(root_path, 'lib', 'linux')
        sys.path.append(linux_lib)

import OpenSSL
SSLError = OpenSSL.SSL.WantReadError

import socks
from .config import config

from xlog import getLogger
xlog = getLogger("gae_proxy")


max_timeout = 5

default_socket = socket.socket


def load_proxy_config():
    global default_socket
    if config.PROXY_ENABLE:

        if config.PROXY_TYPE == "HTTP":
            proxy_type = socks.HTTP
        elif config.PROXY_TYPE == "SOCKS4":
            proxy_type = socks.SOCKS4
        elif config.PROXY_TYPE == "SOCKS5":
            proxy_type = socks.SOCKS5
        else:
            xlog.error("proxy type %s unknown, disable proxy", config.PROXY_TYPE)
            raise

        socks.set_default_proxy(proxy_type, config.PROXY_HOST, config.PROXY_PORT, config.PROXY_USER, config.PROXY_PASSWD)
load_proxy_config()

#####################################
#  Checking network ok

_checking_lock = threading.Lock()
_checking_num = 0
network_stat = "unknown"
last_check_time = 0
continue_fail_count = 0


def report_network_ok():
    global network_stat, last_check_time, continue_fail_count
    network_stat = "OK"
    last_check_time = time.time()
    continue_fail_count = 0

def _check_worker():
    global _checking_lock, _checking_num, network_stat, last_check_time
    time_now = time.time()
    if config.PROXY_ENABLE:
        socket.socket = socks.socksocket
        xlog.debug("patch socks")

    _checking_lock.acquire()
    _checking_num += 1
    _checking_lock.release()
    try:
        conn = http.client.HTTPSConnection("github.com", 443, timeout=30)
        header = {}
        conn.request("HEAD", "/", headers=header)
        response = conn.getresponse()
        if response.status:
            last_check_time = time.time()
            report_network_ok()
            xlog.debug("network is ok, cost:%d ms", 1000*(time.time() - time_now))
            return True
    except Exception as e:
        xlog.warn("check network fail:%r", e)
        network_stat = "Fail"
        last_check_time = time.time()
        return False
    finally:
        _checking_lock.acquire()
        _checking_num -= 1
        _checking_lock.release()

        if config.PROXY_ENABLE:
            socket.socket = default_socket
            xlog.debug("restore socket")


def _simple_check_worker():
    global _checking_lock, _checking_num, network_stat, last_check_time
    time_now = time.time()
    if config.PROXY_ENABLE:
        socket.socket = socks.socksocket
        xlog.debug("patch socks")

    _checking_lock.acquire()
    _checking_num += 1
    _checking_lock.release()
    try:
        conn = http.client.HTTPConnection("www.google.cn", 80, timeout=3)
        header = {}
        conn.request("HEAD", "/", headers=header)
        response = conn.getresponse()
        if response.status:
            last_check_time = time.time()
            report_network_ok()
            xlog.debug("network is ok, cost:%d ms", 1000*(time.time() - time_now))
            return True
    except Exception as e:
        xlog.exception("simple check network fail:%r", e)
        network_stat = "Fail"
        last_check_time = time.time()
        return False
    finally:
        _checking_lock.acquire()
        _checking_num -= 1
        _checking_lock.release()

        if config.PROXY_ENABLE:
            socket.socket = default_socket
            xlog.debug("restore socket")

_simple_check_worker()


def triger_check_network(force=False):
    global _checking_lock, _checking_num, network_stat, last_check_time
    time_now = time.time()
    if not force:
        if _checking_num > 0:
            return

        if network_stat == "OK":
            if time_now - last_check_time < 10:
                return
        else:
            # Fail or unknown
            if time_now - last_check_time < 3:
                return

    last_check_time = time_now
    th = threading.Thread(target=_simple_check_worker)
    th.start()


#===========================================


def _check_ipv6_host(host):
    try:
        conn = http.client.HTTPConnection(host, 80, timeout=5)
        header = {"user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36",
                  "accept":"application/json, text/javascript, */*; q=0.01",
                  "accept-encoding":"gzip, deflate, sdch",
                  "accept-language":'en-US,en;q=0.8,ja;q=0.6,zh-CN;q=0.4,zh;q=0.2',
                  "connection":"keep-alive"
                  }
        conn.request("HEAD", "/", headers=header)
        response = conn.getresponse()
        if response.status:
            return True
        else:
            return False
    except Exception as e:
        return False


def check_ipv6():
    hosts = ["www.6rank.edu.cn", "v6.testmyipv6.com", ]
    for host in hosts:
        if _check_ipv6_host(host):
            return True
    return False
