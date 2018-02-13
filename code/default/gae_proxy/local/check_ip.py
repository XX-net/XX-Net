#!/usr/bin/env python2
# coding:utf-8
import sys
import os

import httplib
import time
import socket
import struct
import binascii

current_path = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))

    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)

    if sys.platform == "win32":
        win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
        sys.path.append(win32_lib)
    elif sys.platform.startswith("linux"):
        linux_lib = os.path.abspath( os.path.join(python_path, 'lib', 'linux'))
        sys.path.append(linux_lib)

    from xlog import getLogger
    xlog = getLogger("gae_proxy")


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
import sni_generater

import hyper

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

GoogleG23PKP = set((
# https://pki.google.com/GIAG2.crt
b'''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnCoEd1zYUJE6BqOC4NhQ
SLyJP/EZcBqIRn7gj8Xxic4h7lr+YQ23MkSJoHQLU09VpM6CYpXu61lfxuEFgBLE
XpQ/vFtIOPRT9yTm+5HpFcTP9FMN9Er8n1Tefb6ga2+HwNBQHygwA0DaCHNRbH//
OjynNwaOvUsRBOt9JN7m+fwxcfuU1WDzLkqvQtLL6sRqGrLMU90VS4sfyBlhH82d
qD5jK4Q1aWWEyBnFRiL4U5W+44BKEMYq7LqXIBHHOZkQBKDwYXqVJYxOUnXitu0I
yhT8ziJqs07PRgOXlwN+wLHee69FM8+6PnG33vQlJcINNYmdnfsOEXmJHjfFr45y
aQIDAQAB
-----END PUBLIC KEY-----
''',
# https://pki.goog/gsr2/GIAG3.crt
# https://pki.goog/gsr2/GTSGIAG3.crt
b'''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAylJL6h7/ziRrqNpyGGjV
Vl0OSFotNQl2Ws+kyByxqf5TifutNP+IW5+75+gAAdw1c3UDrbOxuaR9KyZ5zhVA
Cu9RuJ8yjHxwhlJLFv5qJ2vmNnpiUNjfmonMCSnrTykUiIALjzgegGoYfB29lzt4
fUVJNk9BzaLgdlc8aDF5ZMlu11EeZsOiZCx5wOdlw1aEU1pDbcuaAiDS7xpp0bCd
c6LgKmBlUDHP+7MvvxGIQC61SRAPCm7cl/q/LJ8FOQtYVK8GlujFjgEWvKgaTUHF
k5GiHqGL8v7BiCRJo0dLxRMB3adXEmliK+v+IO9p+zql8H4p7u2WFvexH6DkkCXg
MwIDAQAB
-----END PUBLIC KEY-----
''',
# https://pki.goog/gsr4/GIAG3ECC.crt
b'''\
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEG4ANKJrwlpAPXThRcA3Z4XbkwQvW
hj5J/kicXpbBQclS4uyuQ5iSOGKcuCRt8ralqREJXuRsnLZo0sIT680+VQ==
-----END PUBLIC KEY-----
'''))


class Cert_Exception(Exception):
    def __init__(self, message):
        xlog.debug("Cert_Exception %r", message)
        self.message = "%s" % (message)

    def __str__(self):
        # for %s
        return repr(self.message)

    def __repr__(self):
        # for %r
        return repr(self.message)


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
            raise Exception()

        socks.set_default_proxy(proxy_type, config.PROXY_HOST, config.PROXY_PORT, config.PROXY_USER, config.PROXY_PASSWD)
load_proxy_config()

import threading
network_fail_lock = threading.Lock()


def connect_ssl(ip, port=443, timeout=5, check_cert=True, close_cb=None):
    if not check_local_network.is_ok(ip):
        with network_fail_lock:
           time.sleep(0.1)

    ip_port = (ip, port)

    sni = sni_generater.get()

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

    ssl_sock = openssl_wrap.SSLConnection(openssl_context, sock, ip, close_cb)
    ssl_sock.set_connect_state()
    if hasattr(ssl_sock, 'set_tlsext_host_name'):
        try:
            ssl_sock.set_tlsext_host_name(sni)
        except:
            pass

    time_begin = time.time()
    ssl_sock.connect(ip_port)
    time_connected = time.time()
    ssl_sock.do_handshake()

    try:
        h2 = ssl_sock.get_alpn_proto_negotiated()
        if h2 == "h2":
            ssl_sock.h2 = True
        else:
            ssl_sock.h2 = False

        xlog.debug("%s alpn h2:%s", ip, h2)
    except Exception as e:
        #xlog.exception("alpn:%r", e)
        if hasattr(ssl_sock._connection, "protos") and ssl_sock._connection.protos == "h2":
            ssl_sock.h2 = True
            # xlog.debug("ip:%s http/2", ip)
        else:
            ssl_sock.h2 = False
            # xlog.debug("ip:%s http/1.1", ip)
    time_handshaked = time.time()

    check_local_network.report_ok(ip)

    def verify_SSL_certificate_issuer(ssl_sock):
        # cert = ssl_sock.get_peer_certificate()
        # if not cert:
        #    #google_ip.report_bad_ip(ssl_sock.ip)
        #    #connect_control.fall_into_honeypot()
        #    raise socket.error(' certficate is none')

        # issuer_commonname = next((v for k, v in cert.get_issuer().get_components() if k == 'CN'), '')
        # if not issuer_commonname.startswith('Google'):
        #    google_ip.report_connect_fail(ip, force_remove=True)
        #    raise socket.error(' certficate is issued by %r, not Google' % ( issuer_commonname))
        certs = ssl_sock.get_peer_cert_chain()
        if not certs:
            # google_ip.report_bad_ip(ssl_sock.ip)
            # connect_control.fall_into_honeypot()
            raise socket.error(' certficate is none')
        if len(certs) < 3:
            # google_ip.report_connect_fail(ip, force_remove=True)
            raise Cert_Exception('No intermediate CA was found.')

        if hasattr(OpenSSL.crypto, "dump_publickey"):
            # old OpenSSL not support this function.
            if OpenSSL.crypto.dump_publickey(OpenSSL.crypto.FILETYPE_PEM, certs[1].get_pubkey()) not in GoogleG23PKP:
                # google_ip.report_connect_fail(ip, force_remove=True)
                raise Cert_Exception('The intermediate CA is mismatching.')

        issuer_commonname = next((v for k, v in certs[0].get_issuer().get_components() if k == 'CN'), '')
        if not issuer_commonname.startswith('Google'):
            # google_ip.report_connect_fail(ip, force_remove=True)
            raise Cert_Exception(' certficate is issued by %r, not Google' % (issuer_commonname))

    if check_cert:
        verify_SSL_certificate_issuer(ssl_sock)

    connct_time = int((time_connected - time_begin) * 1000)
    handshake_time = int((time_handshaked - time_connected) * 1000)
    #xlog.debug("conn: %d  handshake:%d", connct_time, handshake_time)

    # sometimes, we want to use raw tcp socket directly(select/epoll), so setattr it to ssl socket.
    ssl_sock._sock = sock
    ssl_sock.connct_time = connct_time
    ssl_sock.handshake_time = handshake_time

    ssl_sock.fd = sock.fileno()
    ssl_sock.create_time = time_begin
    ssl_sock.last_use_time = time_begin
    ssl_sock.received_size = 0
    ssl_sock.load = 0
    ssl_sock.sni = sni
    ssl_sock.host = ""

    return ssl_sock


def get_ssl_cert_domain(ssl_sock):
    cert = ssl_sock.get_peer_certificate()
    if not cert:
        raise SSLError("no cert")

    #issuer_commonname = next((v for k, v in cert.get_issuer().get_components() if k == 'CN'), '')
    ssl_cert = cert_util.SSLCert(cert)
    xlog.info("%s CN:%s", ssl_sock.ip, ssl_cert.cn)
    ssl_sock.domain = ssl_cert.cn


def check_goagent(ssl_sock, appid):
    request_data = 'GET /_gh/ HTTP/1.1\r\nHost: %s.appspot.com\r\n\r\n' % appid
    ssl_sock.send(request_data.encode())
    response = httplib.HTTPResponse(ssl_sock, buffering=True)

    response.begin()

    server_type = response.getheader('Server', "")
    xlog.debug("status:%d", response.status)
    xlog.debug("Server type:%s", server_type)
    if response.status == 404:
        xlog.warn("app check %s status:%d", appid, response.status)
        return False

    if response.status == 503:
        # out of quota
        if "gws" not in server_type and "Google Frontend" not in server_type and "GFE" not in server_type:
            xlog.warn("503 but server type:%s", server_type)
            return False
        else:
            xlog.info("503 server type:%s", server_type)
            return True

    if response.status != 200:
        xlog.warn("app check %s ip:%s status:%d", appid, ip, response.status)
        return False

    content = response.read()
    if "GoAgent" not in content:
        xlog.warn("app check %s content:%s", appid, content)
        return False

    xlog.info("check_goagent ok")
    return True


def test_gae_ip2(ip, appid="xxnet-1"):
    try:
        ssl_sock = connect_ssl(ip, timeout=max_timeout)
        get_ssl_cert_domain(ssl_sock)
    except socket.timeout:
        xlog.warn("connect timeout")
        return False
    except Exception as e:
        xlog.exception("test_gae_ip %s e:%r",ip, e)
        return False

    ssl_sock.support_gae = False
    if not ssl_sock.h2:
        xlog.warn("ip:%s not support http/2", ip)

        try:
            if not check_goagent(ssl_sock, appid):
                return ssl_sock
            else:
                ssl_sock.support_gae = True
                return ssl_sock
        except Exception as e:
            xlog.warn("check fail:%r", e)
            return False

    try:
        conn = hyper.HTTP20Connection(ssl_sock, host='%s.appspot.com'%appid, ip=ip, port=443)
        conn.request('GET', '/_gh/')
    except Exception as e:
        #xlog.exception("gae %r", e)
        xlog.debug("ip:%s http/1.1:%r", ip, e )
        return ssl_sock

    try:
        response = conn.get_response()
    except Exception as e:
        xlog.exception("http2 get response fail:%r", e)
        return ssl_sock

    xlog.debug("ip:%s http/2", ip)

    if response.status == 404:
        xlog.warn("app check %s status:%d", appid, response.status)
        return ssl_sock

    if response.status == 503:
        # out of quota
        server_type = response.headers.get('Server', "")
        xlog.debug("Server type:%s", server_type)
        if "gws" not in server_type and "Google Frontend" not in server_type and "GFE" not in server_type:
            xlog.warn("503 but server type:%s", server_type)
            return ssl_sock
        else:
            xlog.info("503 server type:%s", server_type)
            ssl_sock.support_gae = True
            return ssl_sock

    if response.status != 200:
        xlog.warn("app check %s ip:%s status:%d", appid, ip, response.status)
        return ssl_sock

    content = response.read()
    if "GoAgent" not in content:
        xlog.warn("app check %s content:%s", appid, content)
        return ssl_sock

    xlog.info("check_goagent ok")
    ssl_sock.support_gae = True
    return ssl_sock


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ip = sys.argv[1]
        xlog.info("test ip:%s", ip)
        res = test_gae_ip2(ip)
        if not res:
            print("connect fail")
        elif res.support_gae:
            print("success, domain:%s handshake:%d" % (res.domain, res.handshake_time))
        else:
            print("not support")
    else:
        xlog.info("check_ip <ip>")

