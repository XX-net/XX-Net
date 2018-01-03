#!/usr/bin/env python2
# coding:utf-8
import binascii
import os
import socket
import struct
import sys
import time


current_path = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    root = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, os.pardir))
    data_path = os.path.abspath( os.path.join(root, os.pardir, "data", "x_tunnel"))
    python_path = os.path.join(root, 'python27', '1.0')

    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    #sys.path.insert(0, noarch_lib)
    sys.path.append(noarch_lib)

    if sys.platform == "win32":
        win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
        sys.path.append(win32_lib)
    elif sys.platform.startswith("linux"):
        linux_lib = os.path.abspath( os.path.join(python_path, 'lib', 'linux'))
        #sys.path.insert(0, linux_lib)
        sys.path.append(linux_lib)

    from xlog import getLogger
    xlog = getLogger("heroku_front")


else:
    class xlog():
        @staticmethod
        def debug(fmt, *args, **kwargs):
            pass
        @staticmethod
        def info(fmt, *args, **kwargs):
            pass
        @staticmethod
        def warn(fmt, *args, **kwargs):
            pass
        @staticmethod
        def exception(fmt, *args, **kwargs):
            pass


import OpenSSL
SSLError = OpenSSL.SSL.WantReadError

import socks
import check_local_network
from config import config
import cert_util
import openssl_wrap
import simple_http_client
import sni_generater
import hyper

# http://docs.python.org/dev/library/ssl.html
# http://blog.ivanristic.com/2009/07/examples-of-the-information-collected-from-ssl-handshakes.html
# http://src.chromium.org/svn/trunk/src/net/third_party/nss/ssl/sslenum.c
# openssl s_server -accept 443 -key CA.crt -cert CA.crt

# ref: http://vincent.bernat.im/en/blog/2011-ssl-session-reuse-rfc5077.html

g_cacertfile = os.path.join(current_path, "cacert.pem")
openssl_context = openssl_wrap.SSLConnection.context_builder(ca_certs=g_cacertfile)
try:
    openssl_context.set_session_id(binascii.b2a_hex(os.urandom(10)))
except:
    pass

if hasattr(OpenSSL.SSL, 'SESS_CACHE_BOTH'):
    openssl_context.set_session_cache_mode(OpenSSL.SSL.SESS_CACHE_BOTH)

max_timeout = 5


default_socket = socket.socket


def load_proxy_config():
    global default_socket
    if int(config.PROXY_ENABLE):

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


import threading
network_fail_lock = threading.Lock()

def connect_ssl(ip, port=443, timeout=5, top_domain=None, on_close=None):
    sni = sni_generater.get()
    if not top_domain:
        top_domain = sni

    xlog.debug("top_domain:%s sni:%s", top_domain, sni)

    if int(config.PROXY_ENABLE):
        sock = socks.socksocket(socket.AF_INET if ':' not in ip else socket.AF_INET6)
    else:
        sock = socket.socket(socket.AF_INET if ':' not in ip else socket.AF_INET6)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # set struct linger{l_onoff=1,l_linger=0} to avoid 10048 socket error
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
    # resize socket recv buffer 8K->32K to improve browser releated application performance
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32*1024)
    sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
    sock.settimeout(timeout)

    ssl_sock = openssl_wrap.SSLConnection(openssl_context, sock, ip, on_close=on_close)
    ssl_sock.set_connect_state()
    ssl_sock.set_tlsext_host_name(sni)

    time_begin = time.time()
    ip_port = (ip, port)
    ssl_sock.connect(ip_port)
    time_connected = time.time()
    ssl_sock.do_handshake()

    try:
        h2 = ssl_sock.get_alpn_proto_negotiated()
        if h2 == "h2":
            ssl_sock.h2 = True
        else:
            ssl_sock.h2 = False
    except Exception as e:
        #xlog.exception("alpn:%r", e)
        if hasattr(ssl_sock._connection, "protos") and ssl_sock._connection.protos == "h2":
            ssl_sock.h2 = True
        else:
            ssl_sock.h2 = False

    time_handshaked = time.time()

    # report network ok
    check_local_network.network_stat = "OK"
    check_local_network.last_check_time = time_handshaked
    check_local_network.continue_fail_count = 0

    cert = ssl_sock.get_peer_certificate()
    if not cert:
        raise socket.error(' certficate is none')

    issuer_commonname = next((v for k, v in cert.get_issuer().get_components() if k == 'CN'), '')
    if not issuer_commonname.startswith('DigiCert'):
        #  and issuer_commonname not in ['DigiCert ECC Extended Validation Server CA']
        raise socket.error(' certficate is issued by %r, not COMODO' % ( issuer_commonname))

    connect_time = int((time_connected - time_begin) * 1000)
    handshake_time = int((time_handshaked - time_begin) * 1000)
    if __name__ == "__main__":
        xlog.debug("h2:%s", ssl_sock.h2)
        xlog.debug("issued by:%s", issuer_commonname)
        xlog.debug("conn: %d  handshake:%d", connect_time, handshake_time)

    # sometimes, we want to use raw tcp socket directly(select/epoll), so setattr it to ssl socket.
    ssl_sock.ip = ip
    ssl_sock._sock = sock
    ssl_sock.fd = sock.fileno()
    ssl_sock.create_time = time_begin
    ssl_sock.connect_time = connect_time
    ssl_sock.handshake_time = handshake_time
    ssl_sock.sni = sni
    ssl_sock.top_domain = top_domain

    return ssl_sock


def get_ssl_cert_domain(ssl_sock):
    cert = ssl_sock.get_peer_certificate()
    if not cert:
        raise SSLError("no cert")

    #issuer_commonname = next((v for k, v in cert.get_issuer().get_components() if k == 'CN'), '')
    ssl_cert = cert_util.SSLCert(cert)
    xlog.info("%s CN:%s", ssl_sock.ip, ssl_cert.cn)
    ssl_sock.domain = ssl_cert.cn


def check_xtunnel_http1(ssl_sock, host):
    xlog.warn("ip:%s use http/1.1", ssl_sock.ip)
    start_time = time.time()

    try:
        request_data = 'GET / HTTP/1.1\r\nHost: %s\r\n\r\n' % host
        ssl_sock.send(request_data.encode())

        response = simple_http_client.Response(ssl_sock)
        response.begin(timeout=5)

        server_type = response.getheader('Server', "")
        xlog.debug("status:%d", response.status)
        xlog.debug("Server type:%s", server_type)
        if response.status == 403:
            xlog.warn("check status:%d", response.status)
            return ssl_sock

        if response.status != 200:
            xlog.warn("ip:%s status:%d", ssl_sock.ip, response.status)
            return False

        content = response.read(timeout=1)
        if content != "OK":
            xlog.warn("app check content:%s", content)
            return ssl_sock
    except Exception as e:
        xlog.debug("check ip %s http1 e:%r", ssl_sock.ip, e)
        return ssl_sock

    time_cost = (time.time() - start_time) * 1000
    ssl_sock.request_time = time_cost
    xlog.info("check_xtunnel ok, time:%d", time_cost)
    ssl_sock.support_xtunnel = True
    return ssl_sock


def check_xtunnel_http2(ssl_sock, host):
    xlog.warn("ip:%s use http/2", ssl_sock.ip)
    start_time = time.time()
    try:
        conn = hyper.HTTP20Connection(ssl_sock, host=host, ip=ssl_sock.ip, port=443)
        conn.request('GET', '/')
    except Exception as e:
        #xlog.exception("xtunnel %r", e)
        xlog.debug("ip:%s http/1.1:%r", ssl_sock.ip, e )
        return ssl_sock

    try:
        response = conn.get_response()
    except Exception as e:
        xlog.exception("http2 get response fail:%r", e)
        return ssl_sock

    xlog.debug("ip:%s http/2", ssl_sock.ip)

    if response.status != 200:
        xlog.warn("app check ip:%s status:%d", ssl_sock.ip, response.status)
        return ssl_sock

    content = response.read()
    if content != "OK":
        xlog.warn("app check content:%s", content)
        return ssl_sock

    ssl_sock.support_xtunnel = True
    time_cost = (time.time() - start_time) * 1000
    ssl_sock.request_time = time_cost
    xlog.info("check_xtunnel ok, time:%d", time_cost)
    return ssl_sock


def test_xtunnel_ip2(ip, top_domain=None, wait_time=0):
    try:
        ssl_sock = connect_ssl(ip, timeout=max_timeout, top_domain=top_domain)
        get_ssl_cert_domain(ssl_sock)
    except socket.timeout:
        xlog.warn("connect timeout")
        return False
    except Exception as e:
        xlog.exception("test_xtunnel_ip %s e:%r",ip, e)
        return False

    ssl_sock.support_xtunnel = False

    host = "xxnet4.herokuapp.com"
    xlog.info("host:%s", host)

    time.sleep(wait_time)

    if not ssl_sock.h2:
        return check_xtunnel_http1(ssl_sock, host)
    else:
        return check_xtunnel_http2(ssl_sock, host)


if __name__ == "__main__":
    # case 1: only ip
    # case 2: ip + domain
    #    connect use domain

    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = "107.21.125.200"
        print("Usage: check_ip.py [ip] [top_domain] [wait_time=0]")
    xlog.info("test ip:%s", ip)

    if len(sys.argv) > 2:
        top_domain = sys.argv[2]
    else:
        top_domain = None

    if len(sys.argv) > 3:
        wait_time = int(sys.argv[3])
    else:
        wait_time = 0

    res = test_xtunnel_ip2(ip, top_domain=top_domain, wait_time=wait_time)
    if not res:
        print("connect fail")
    elif res.support_xtunnel:
        print("success, domain:%s handshake:%d" % (res.domain, res.handshake_time))
    else:
        print("not support")