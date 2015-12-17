
import sys
import os

import httplib
import time
import socket
import threading
import struct
import socks

current_path = os.path.dirname(os.path.abspath(__file__))

import OpenSSL
SSLError = OpenSSL.SSL.WantReadError


from config import config
import cert_util
from openssl_wrap import SSLConnection

from appids_manager import appid_manager
from proxy import xlog


g_cacertfile = os.path.join(current_path, "cacert.pem")
openssl_context = SSLConnection.context_builder(ca_certs=g_cacertfile) # check cacert cost too many cpu, 100 check thread cost 60%.

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

checking_lock = threading.Lock()
checking_num = 0
network_ok = True
last_check_time = 0
check_network_interval = 100
last_ok_time = 0


def network_is_ok(force=False):
    global checking_lock, checking_num, network_ok, last_check_time, check_network_interval
    time_now = time.time()
    if not force:
        if time_now - last_check_time < check_network_interval:
            return network_ok

        if time_now - last_ok_time < check_network_interval:
            return True

        if checking_num > 0:
            return network_ok

    if config.PROXY_ENABLE:
        socket.socket = socks.socksocket
        xlog.debug("patch socks")

    checking_lock.acquire()
    checking_num += 1
    checking_lock.release()
    try:
        conn = httplib.HTTPSConnection("github.com", 443, timeout=10)
        header = {"user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36",
                  "accept":"application/json, text/javascript, */*; q=0.01",
                  "accept-encoding":"gzip, deflate, sdch",
                  "accept-language":'en-US,en;q=0.8,ja;q=0.6,zh-CN;q=0.4,zh;q=0.2',
                  "connection":"keep-alive"
                  }
        conn.request("HEAD", "/", headers=header)
        response = conn.getresponse()
        if response.status:
            xlog.debug("network is ok, cost:%d ms", 1000*(time.time() - time_now))
            network_ok = True
            last_check_time = time.time()
            return True
    except Exception as e:
        xlog.warn("network fail:%r", e)
        network_ok = False
        last_check_time = time.time()
        return False
    finally:
        checking_lock.acquire()
        checking_num -= 1
        checking_lock.release()

        if config.PROXY_ENABLE:
            socket.socket = default_socket
            xlog.debug("restore socket")



######################################
# about ip connect time and handshake time
# handshake time is double of connect time in common case.
# after connect and handshaked, http get time is like connect time
#
# connect time is zero if you use socks proxy.
#
#
# most case, connect time is 300ms - 600ms.
# good case is 60ms
# bad case is 1300ms and more.


def connect_ssl(ip, port=443, timeout=5, openssl_context=None):
    global last_ok_time
    ip_port = (ip, port)

    if not openssl_context:
        openssl_context = SSLConnection.context_builder()

    if config.PROXY_ENABLE:
        sock = socks.socksocket(socket.AF_INET)
    else:
        sock = socket.socket(socket.AF_INET)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # set struct linger{l_onoff=1,l_linger=0} to avoid 10048 socket error
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
    sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
    sock.settimeout(timeout)

    ssl_sock = SSLConnection(openssl_context, sock)
    ssl_sock.set_connect_state()

    time_begin = time.time()
    ssl_sock.connect(ip_port)
    time_connected = time.time()
    ssl_sock.do_handshake()
    time_handshaked = time.time()

    connct_time = int((time_connected - time_begin) * 1000)
    handshake_time = int((time_handshaked - time_connected) * 1000)
    #xlog.debug("conn: %d  handshake:%d", connct_time, handshake_time)

    # sometimes, we want to use raw tcp socket directly(select/epoll), so setattr it to ssl socket.
    ssl_sock.sock = sock
    ssl_sock.connct_time = connct_time
    ssl_sock.handshake_time = handshake_time
    last_ok_time = time_handshaked
    return ssl_sock


def get_ssl_cert_domain(ssl_sock):
    cert = ssl_sock.get_peer_certificate()
    if not cert:
        raise SSLError("no cert")

    #issuer_commonname = next((v for k, v in cert.get_issuer().get_components() if k == 'CN'), '')
    ssl_cert = cert_util.SSLCert(cert)
    #xlog.info("%s CN:%s", ip, ssl_cert.cn)
    ssl_sock.domain = ssl_cert.cn


def check_appid(ssl_sock, appid):
    request_data = 'GET / HTTP/1.1\r\nHost: %s.appspot.com\r\n\r\n' % appid
    ssl_sock.send(request_data.encode())
    response = httplib.HTTPResponse(ssl_sock, buffering=True)

    response.begin()
    if response.status != 200:
        #xlog.debug("app check %s status:%d", ssl_sock.ip, response.status)
        raise Exception("app check fail")

    content = response.read()
    if "GoAgent" not in content:
        #xlog.debug("app check %s content:%s", ssl_sock.ip, content)
        raise Exception("content fail")

    ssl_sock.server_type = response.getheader('Server', "")


# export api for google_ip
def test_gae_ip(ip, appid=None):
    try:
        ssl_sock = connect_ssl(ip, timeout=max_timeout, openssl_context=openssl_context)
        get_ssl_cert_domain(ssl_sock)

        if not appid:
            appid = appid_manager.get_appid()
        check_appid(ssl_sock, appid)

        return ssl_sock
    except Exception as e:
        #xlog.exception("test_gae_ip %s e:%r",ip, e)
        return False

