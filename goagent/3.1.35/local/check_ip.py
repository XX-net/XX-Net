
import sys
import os
import httplib
import time
import socket

current_path = os.path.dirname(os.path.abspath(__file__))

import OpenSSL
SSLError = OpenSSL.SSL.WantReadError


from config import config
import cert_util
from openssl_wrap import SSLConnection

if __name__ == "__main__":
    import logging
else:
    # hide log in working mode.
    class logging():
        @staticmethod
        def debug(fmt, *args, **kwargs):
            pass
        @staticmethod
        def info(fmt, *args, **kwargs):
            pass
        @staticmethod
        def warn(fmt, *args, **kwargs):
            pass

g_cacertfile = os.path.join(current_path, "cacert.pem")
max_timeout = 5000
g_conn_timeout = 1
g_handshake_timeout = 2

if config.PROXY_ENABLE:
    import socks

    if config.PROXY_TYPE == "HTTP":
        proxy_type = socks.HTTP
    elif config.PROXY_TYPE == "SOCKS4":
        proxy_type = socks.SOCKS4
    elif config.PROXY_TYPE == "SOCKS5":
        proxy_type = socks.SOCKS5
    else:
        config.PROXY_ENABLE = 0
        logging.warn("proxy type %s unknown, disable proxy", config.PROXY_TYPE)

    if config.PROXY_ENABLE:
        socks.set_default_proxy(proxy_type, config.PROXY_HOST, config.PROXY_PORT, config.PROXY_USER, config.PROXY_PASSWD)




class Check_result():
    def __init__(self):
        self.domain = ""
        self.server_type = ""
        self.appspot_ok = False
        self.connect_time = max_timeout
        self.handshake_time = max_timeout

class Check_frame(object):
    def __init__(self, ip):
        self.result = Check_result()
        self.ip = ip

    def check(self, callback=None, check_ca=False):

        timeout = 5
        openssl_context = SSLConnection.context_builder(ssl_version="TLSv1") #, ca_certs=g_cacertfile) # check cacert cost too many cpu, 100 check thread cost 60%.

        ssl_sock = None
        try:
            def connect_ssl(ip):
                import struct
                ip_port = (ip, 443)

                if config.PROXY_ENABLE:
                    sock = socks.socksocket(socket.AF_INET)
                else:
                    sock = socket.socket(socket.AF_INET)
                # set reuseaddr option to avoid 10048 socket error
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # set struct linger{l_onoff=1,l_linger=0} to avoid 10048 socket error
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
                # resize socket recv buffer 8K->32K to improve browser releated application performance
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32*1024)
                # disable negal algorithm to send http request quickly.
                sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
                # set a short timeout to trigger timeout retry more quickly.
                sock.settimeout(timeout)

                ssl_sock = SSLConnection(openssl_context, sock)
                ssl_sock.set_connect_state()

                # pick up the certificate
                #server_hostname = random_hostname() if (cache_key or '').startswith('google_') or hostname.endswith('.appspot.com') else None
                #if server_hostname and hasattr(ssl_sock, 'set_tlsext_host_name'):
                #    ssl_sock.set_tlsext_host_name(server_hostname)

                time_begin = time.time()
                ssl_sock.connect(ip_port)
                time_connected = time.time()
                ssl_sock.do_handshake()
                time_handshaked = time.time()

                self.result.connct_time = int((time_connected - time_begin) * 1000)
                self.result.handshake_time = int((time_handshaked - time_connected) * 1000)
                logging.debug("conn: %d  handshake:%d", self.result.connct_time, self.result.handshake_time)

                # sometimes, we want to use raw tcp socket directly(select/epoll), so setattr it to ssl socket.
                ssl_sock.sock = sock
                return ssl_sock
            ssl_sock = connect_ssl(self.ip)

            # verify SSL certificate issuer.
            def check_ssl_cert(ssl_sock):
                cert = ssl_sock.get_peer_certificate()
                if not cert:
                    raise socket.error(' certficate is none')

                issuer_commonname = next((v for k, v in cert.get_issuer().get_components() if k == 'CN'), '')
                if not issuer_commonname.startswith('Google'):
                    raise socket.error(' certficate is issued by %r, not Google' % ( issuer_commonname))


                ssl_cert = cert_util.SSLCert(cert)
                logging.info("CN:%s", ssl_cert.cn)
                self.result.domain = ssl_cert.cn
            if check_ca:
                check_ssl_cert(ssl_sock)

            if callback:
                return callback(ssl_sock, self.ip)

            return True

        except SSLError as e:
            logging.debug("Check_appengine %s SSLError:%s", self.ip, e)
        except IOError as e:
            logging.debug("Check %s IOError:%s", self.ip, e)
            pass
        except httplib.BadStatusLine:
            #logging.debug('Check_appengine http.bad status line ip:%s', ip)
            #import traceback
            #traceback.print_exc()
            pass
        except Exception as e:
            if len(e.args)>0:
                errno_str = e.args[0]
            else:
                errno_str = e.message
            logging.debug('check_appengine %s %s err:%s', self.ip, errno_str, e)
        finally:
            if ssl_sock:
                ssl_sock.close()

        return False

# each ssl connection must reuse by same host
# therefor, different host need new ssl connection.

def test_server_type(ssl_sock, ip):
    request_data = "GET / HTTP/1.1\r\nAccept: */*\r\nHost: %s\r\nConnection: Keep-Alive\r\n\r\n" % ip
    time_start = time.time()
    ssl_sock.send(request_data.encode())
    response = httplib.HTTPResponse(ssl_sock, buffering=True)
    try:
        response.begin()
        server_type = response.msg.dict["server"]
        time_stop = time.time()
        time_cost = (time_stop - time_start)*1000

        server_type = server_type.replace(" ", "_")
        if server_type == '':
            server_type = '_'
        logging.info("server_type:%s time:%d", server_type, time_cost)
        return server_type
    finally:
        response.close()


def test_app_check(ssl_sock, ip):
    request_data = 'GET /check HTTP/1.1\r\nHost: xxnet-check.appspot.com\r\n\r\n'
    time_start = time.time()
    ssl_sock.send(request_data.encode())
    response = httplib.HTTPResponse(ssl_sock, buffering=True)
    try:
        response.begin()
        status = response.status
        if status != 200:
            raise Exception("app check fail")
        content = response.read()
        if not content == "CHECK_OK":
            raise Exception("content fail")
    finally:
        response.close()
    time_stop = time.time()
    time_cost = (time_stop - time_start)*1000
    logging.debug("app check time:%d", time_cost)
    return True

def network_is_ok():

    if config.PROXY_ENABLE:
        default_socket = socket.socket
        socket.socket = socks.socksocket
    try:
        conn = httplib.HTTPSConnection("github.com", 443)
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
    except:
        pass
    finally:
        if config.PROXY_ENABLE:
            socket.socket = default_socket

    return False

def test_gws(ip_str):
    logging.info("==>%s", ip_str)
    check = Check_frame(ip_str)

    result = check.check(callback=test_server_type, check_ca=True)
    if not result or not "gws" in result:
        return False

    check.result.server_type = result

    return check.result

def test(ip_str, loop=1):
    logging.info("==>%s", ip_str)
    check = Check_frame(ip_str)

    for i in range(loop):
        result = check.check(callback=test_server_type, check_ca=True)
        if not result:
            logging.debug("test server type fail")
            continue
        check.result.server_type = result

        result = check.check(callback=test_app_check)
        if not result:
            if "gws" in check.result.server_type:
                logging.warn("ip:%s server_type:%s but appengine check fail.", ip_str, check.result.server_type)
            continue
        check.result.appspot_ok = result

    return check.result

import google_ip_range
import ip_utils
def test_main():
    ip_range_manager = google_ip_range.ip_range()
    while True:
        time.sleep(1)
        ip_int = ip_range_manager.get_ip()
        ip_str = ip_utils.ip_num_to_string(ip_int)
        test(ip_str, 1)

from google_ip_range import ip_range
import threading
class fast_search_ip():
    check_num = 0
    gws_num = 0
    lock = threading.Lock()

    def check_ip(self, ip_str):
        result = test_gws(ip_str)

        self.lock.acquire()
        self.check_num += 1
        self.lock.release()

        if not result:
            return False

        self.lock.acquire()
        self.gws_num += 1
        self.lock.release()
        return True

    def runJob(self):
        while self.check_num < 1000000:
            try:
                time.sleep(1)
                #ip_int = ip_range.get_ip()
                ip_int = ip_range.random_get_ip()
                ip_str = ip_utils.ip_num_to_string(ip_int)
                self.check_ip(ip_str)
            except Exception as e:
                logging.warn("google_ip.runJob fail:%s", e)



    def search_more_google_ip(self):
        for i in range(50):
            p = threading.Thread(target = self.runJob)
            p.daemon = True
            p.start()

def test_multi_thread_search_ip():
    test_speed = fast_search_ip()
    test_speed.search_more_google_ip()
    for i in range(2000000):

        test_speed.lock.acquire()
        #test_speed.check_num = 0
        #test_speed.gws_num = 0
        test_speed.lock.release()

        time.sleep(1)
        if test_speed.check_num != 0:
            print test_speed.check_num, test_speed.gws_num, (test_speed.gws_num * 1000 / test_speed.check_num)


if __name__ == "__main__":
    print network_is_ok()
    print network_is_ok()
    test("208.117.224.103", 10) #gws
    #test('208.117.224.213', 10)
    #test("218.176.242.24")
    #test_main()

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