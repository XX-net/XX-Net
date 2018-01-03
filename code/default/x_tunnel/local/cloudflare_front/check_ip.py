#!/usr/bin/env python2
# coding:utf-8
import binascii
import random
import os
import socket
import struct
import sys
import time
import json


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
    xlog = getLogger("cloudflare_front")


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

from pyasn1.codec.der import decoder as der_decoder
import socks
import check_local_network
from config import config
import cert_util
import ip_utils
import openssl_wrap
import simple_http_client
from subj_alt_name import SubjectAltName

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


def load_front_domains(file_path):
    if not os.path.isfile(file_path):
        raise Exception("load front domain fn:%s not exist" % file_path)

    lns = []
    with open(file_path, "r") as fd:
        ds = json.load(fd)
        for top in ds:
            subs = ds[top]
            subs = [str(s) for s in subs]
            lns.append([str(top) , subs])
    return lns


ns = None


def update_front_domains():
    global ns
    front_domains_fn = os.path.join(config.DATA_PATH, "front_domains.json")
    default_front_domains_fn = os.path.join(current_path, "front_domains.json")

    try:
        ns = load_front_domains(front_domains_fn)
        xlog.info("load front:%s", front_domains_fn)
    except Exception as e:
        ns = load_front_domains(default_front_domains_fn)
        xlog.info("load front:%s", default_front_domains_fn)


update_front_domains()
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


def get_subj_alt_name(peer_cert):
    '''
    Copied from ndg.httpsclient.ssl_peer_verification.ServerSSLCertVerification
    Extract subjectAltName DNS name settings from certificate extensions
    @param peer_cert: peer certificate in SSL connection.  subjectAltName
    settings if any will be extracted from this
    @type peer_cert: OpenSSL.crypto.X509
    '''
    # Search through extensions
    dns_name = []
    general_names = SubjectAltName()
    for i in range(peer_cert.get_extension_count()):
        ext = peer_cert.get_extension(i)
        ext_name = ext.get_short_name()
        if ext_name == "subjectAltName":
            # PyOpenSSL returns extension data in ASN.1 encoded form
            ext_dat = ext.get_data()
            decoded_dat = der_decoder.decode(ext_dat, asn1Spec=general_names)

            for name in decoded_dat:
                if isinstance(name, SubjectAltName):
                    for entry in range(len(name)):
                        component = name.getComponentByPosition(entry)
                        n = str(component.getComponent())
                        if n.startswith("*"):
                            continue
                        dns_name.append(n)
    return dns_name


import threading
network_fail_lock = threading.Lock()


def connect_ssl(ip, port=443, timeout=5, top_domain=None, on_close=None):
    if top_domain is None:
        top_domain, subs = random.choice(ns)
        sni = random.choice(subs)
    else:
        sni = top_domain

    top_domain = str(top_domain)
    sni = str(sni)
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

    try:
        ssl_sock = openssl_wrap.SSLConnection(openssl_context, sock, ip, on_close=on_close)
        ssl_sock.set_connect_state()
        ssl_sock.set_tlsext_host_name(sni)

        time_begin = time.time()
        ip_port = (ip, port)
        ssl_sock.connect(ip_port)
        time_connected = time.time()
        ssl_sock.do_handshake()
    except Exception as e:
        xlog.warn("connect:%s sni:%s fail:%r", ip, sni, e)
        raise socket.error('conn fail, sni:%s, top:%s e:%r' % (sni, top_domain, e))

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
        raise socket.error('certficate is none, sni:%s, top:%s' % (sni, top_domain))

    issuer_commonname = next((v for k, v in cert.get_issuer().get_components() if k == 'CN'), '')
    if not issuer_commonname.startswith('COMODO'):
        #  and issuer_commonname not in ['DigiCert ECC Extended Validation Server CA']
        raise socket.error(' certficate is issued by %r, not COMODO' % ( issuer_commonname))

    connect_time = int((time_connected - time_begin) * 1000)
    handshake_time = int((time_handshaked - time_begin) * 1000)
    if __name__ == "__main__":
        xlog.debug("h2:%s", ssl_sock.h2)
        xlog.debug("issued by:%s", issuer_commonname)
        xlog.debug("conn: %d  handshake:%d", connect_time, handshake_time)
        alt_names = get_subj_alt_name(cert)
        xlog.debug("alt names:%s", alt_names)

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
    start_time = time.time()
    request_data = 'GET / HTTP/1.1\r\nHost: %s\r\n\r\n' % host
    ssl_sock.send(request_data.encode())

    response = simple_http_client.Response(ssl_sock)
    response.begin(timeout=5)

    server_type = response.getheader('Server', "")
    xlog.debug("status:%d", response.status)
    xlog.debug("Server type:%s", server_type)
    if response.status == 403:
        xlog.warn("check status:%d", response.status)
        return False

    if response.status != 200:
        xlog.warn("ip:%s status:%d", ssl_sock.ip, response.status)
        return False

    content = response.read(timeout=1)
    if "X_Tunnel OK" not in content:
        xlog.warn("app check content:%s", content)
        return False

    time_cost = (time.time() - start_time) * 1000
    ssl_sock.request_time = time_cost
    xlog.info("check_xtunnel ok, time:%d", time_cost)

    return True


def check_xtunnel_http2(ssl_sock, host):
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
    if "X_Tunnel OK" not in content:
        xlog.warn("app check content:%s", content)
        return ssl_sock

    ssl_sock.support_xtunnel = True
    time_cost = (time.time() - start_time) * 1000
    ssl_sock.request_time = time_cost
    xlog.info("check_xtunnel ok, time:%d", time_cost)
    return ssl_sock


def test_xtunnel_ip2(ip, sub="scan1", top_domain=None):
    try:
        ssl_sock = connect_ssl(ip, timeout=max_timeout, top_domain=top_domain)
        get_ssl_cert_domain(ssl_sock)
    except socket.timeout:
        xlog.warn("connect timeout")
        return False
    except Exception as e:
        xlog.exception("test_xtunnel_ip %s e:%r",ip, e)
        return False

    host = sub + "." + ssl_sock.top_domain
    xlog.info("host:%s", host)

    ssl_sock.support_xtunnel = False
    if not ssl_sock.h2:
        xlog.warn("ip:%s not support http/2", ip)

        try:
            if not check_xtunnel_http1(ssl_sock, host):
                return ssl_sock
            else:
                ssl_sock.support_xtunnel = True
                return ssl_sock
        except Exception as e:
            xlog.exception("check fail:%r", e)
            return False
    else:
        return check_xtunnel_http2(ssl_sock, host)


if __name__ == "__main__":
    # case 1: only ip
    # case 2: ip + domain
    #    connect use domain, print altNames

    top_domain = None
    if len(sys.argv) > 1:
        ip = sys.argv[1]
        if not ip_utils.check_ip_valid(ip):
            ip = "104.28.100.89"
            top_domain = sys.argv[1]
            xlog.info("test domain:%s", top_domain)
    else:
        ip = "104.28.100.89"
        print("Usage: check_ip.py [ip] [top_domain] [wait_time=0]")

    xlog.info("test ip:%s", ip)

    if len(sys.argv) > 2:
        top_domain = sys.argv[2]
        xlog.info("test top domain:%s", top_domain)

    res = test_xtunnel_ip2(ip, top_domain=top_domain)
    if not res:
        print("connect fail")
    elif res.support_xtunnel:
        print("success, domain:%s handshake:%d" % (res.domain, res.handshake_time))
    else:
        print("not support")

