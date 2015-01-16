#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'moonshawdo@gmail.com'

import sys
import os

current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, os.pardir, 'python27', '1.0'))
if sys.platform == "win32":
    win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
    sys.path.append(win32_lib)
elif sys.platform == "linux" or sys.platform == "linux2":
    win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'linux'))
    sys.path.append(win32_lib)

import OpenSSL

import logging
import ssl
import select
import time
import socket
from time import sleep

g_conn_timeout = 2
g_handshake_timeout = 3

g_filedir = os.path.dirname(__file__)
g_cacertfile = os.path.join(g_filedir, "cacert.pem")

g_useOpenSSL = 1
g_usegevent = 1
if g_usegevent == 1:
    try:
        from gevent import monkey
        monkey.patch_all(Event=True)
        g_useOpenSSL = 0
        from gevent import sleep
    except ImportError:
        g_usegevent = 0

if g_useOpenSSL == 1:
    try:
        import OpenSSL.SSL

        SSLError = OpenSSL.SSL.WantReadError
        g_usegevent = 0
    except ImportError:
        g_useOpenSSL = 0
        SSLError = ssl.SSLError
else:
    SSLError = ssl.SSLError


def PRINT(strlog):
    #print (strlog)
    logging.info(strlog)


prekey="\nServer:"
def parse_google_server_name_from_header(header):
    begin = header.find(prekey)
    if begin != -1:
        begin += len(prekey)
        end = header.find("\n",begin)
        if end == -1:
            end = len(header)
        gws = header[begin:end].strip(" \t")
        return gws
    return ""

class ssl_check(object):
    httpreq = "GET / HTTP/1.1\r\nAccept: */*\r\nHost: %s\r\nConnection: Keep-Alive\r\n\r\n"

    def __init__(self):
        pass


    def init_ssl_context(self):
        self.ssl_cxt = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_METHOD)
        self.ssl_cxt.set_timeout(g_handshake_timeout)
        #PRINT("init ssl context ok")

    def get_ssl_domain(self, ip):
        time_begin = time.time()
        s = None
        c = None
        has_error = 1
        timeout = 0
        domain = None
        gws_name = ""
        try:
            s = socket.socket()
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if g_useOpenSSL:
                self.init_ssl_context()
                s.settimeout(g_conn_timeout)
                s.connect((ip, 443))
                c = OpenSSL.SSL.Connection(self.ssl_cxt, s)
                c.set_connect_state()
                s.setblocking(0)
                while True:
                    try:
                        c.do_handshake()
                        break
                    except SSLError:
                        infds, outfds, errfds = select.select([s, ], [], [], g_handshake_timeout)
                        if len(infds) == 0:
                            # print "do_handshake timed out"
                            raise SSLError("do_handshake timed out")
                        else:
                            costtime = int(time.time() - time_begin)
                            if costtime > g_handshake_timeout:
                                # print "do_handshake timed out"
                                raise SSLError("do_handshake timed out")
                            else:
                                pass
                    except OpenSSL.SSL.SysCallError as e:
                        raise SSLError(e.args)
                time_end = time.time()
                costtime = int(time_end * 1000 - time_begin * 1000)
                cert = c.get_peer_certificate()
                for subject in cert.get_subject().get_components():
                    if subject[0] == "CN":
                        domain = subject[1]
                        has_error = 0
                if domain is None:
                    PRINT("%s can not get CN: %s " % (ip, cert.get_subject().get_components()))
                #尝试发送http请求，获取回应头部的Server字段
                #if domain is None or isgoolgledomain(domain) == 2:
                if True:
                    cur_time = time.time()
                    gws_name = self.get_server_name_from_header(c,s,ip)
                    time_end = time.time()
                    costtime += int(time_end * 1000 - cur_time * 1000)
                    if domain is None and len(gws_name) > 0:
                        domain = "null"
                return domain, costtime,timeout,gws_name
            else:
                s.settimeout(g_conn_timeout)
                c = ssl.wrap_socket(s, cert_reqs=ssl.CERT_REQUIRED, ca_certs=g_cacertfile,
                                    do_handshake_on_connect=False)
                c.settimeout(g_conn_timeout)
                c.connect((ip, 443))
                c.settimeout(g_handshake_timeout)
                c.do_handshake()
                time_end = time.time()
                cert = c.getpeercert()
                costtime = int(time_end * 1000 - time_begin * 1000)
                if 'subject' in cert:
                    subjectitems = cert['subject']
                    for mysets in subjectitems:
                        for item in mysets:
                            if item[0] == "commonName":
                                if not isinstance(item[1], str):
                                    domain = item[1].encode("utf-8")
                                else:
                                    domain = item[1]
                                has_error = 0
                    if domain is None:
                        PRINT("%s can not get commonName: %s " % (ip, subjectitems))
                #尝试发送http请求，获取回应头部的Server字段
                #if domain is None or isgoolgledomain(domain) == 2:
                if True:
                    cur_time = time.time()
                    gws_name = self.get_server_name_from_header(c,s,ip)
                    time_end = time.time()
                    costtime += int(time_end * 1000 - cur_time * 1000)
                    if domain is None and len(gws_name) > 0:
                        domain = "null"
                return domain, costtime,timeout,gws_name
        except SSLError as e:
            time_end = time.time()
            costtime = int(time_end * 1000 - time_begin * 1000)
            if str(e).endswith("timed out"):
                timeout = 1
            else:
                #PRINT("SSL Exception(%s): %s, times:%d ms " % (ip, e, costtime))
                pass
            return domain, costtime,timeout,gws_name
        except IOError as e:
            time_end = time.time()
            costtime = int(time_end * 1000 - time_begin * 1000)
            if str(e).endswith("timed out"):
                #print "IO timeout:", str(e)
                timeout = 1
            else:
                #PRINT("Catch IO Exception(%s): %s, times:%d ms " % (ip, e, costtime))
                pass
            return domain, costtime,timeout,gws_name
        except Exception as e:
            time_end = time.time()
            costtime = int(time_end * 1000 - time_begin * 1000)
            #PRINT("Catch Exception(%s): %s, times:%d ms " % (ip, e, costtime))
            return domain, costtime,timeout,gws_name
        finally:
            if g_useOpenSSL:
                if c:
                    if has_error == 0:
                        c.shutdown()
                        c.sock_shutdown(2)
                    c.close()
                if s:
                    s.close()
            else:
                if c:
                    if has_error == 0:
                        c.shutdown(2)
                    c.close()
                elif s:
                    s.close()

    def get_server_name_from_header(self,conn,sock,ip):
        try:
            myreq = ssl_check.httpreq % ip
            conn.write(myreq)
            data=""
            sock.setblocking(0)
            trycnt = 0
            begin = time.time()
            conntimeout = g_conn_timeout if g_usegevent == 0 else 0.001
            while True:
                end = time.time()
                costime = int(end-begin)
                if costime >= g_conn_timeout:
                    #PRINT("get http response timeout(%ss),ip:%s,cnt:%d" % (costime,ip,trycnt) )
                    return ""
                trycnt += 1
                infds, outfds, errfds = select.select([sock, ], [], [], conntimeout)
                if len(infds) == 0:
                    if g_usegevent == 1:
                        sleep(0.5)
                    continue
                timeout = 0
                try:
                    d = conn.read(1024)
                except SSLError as e:
                    sleep(0.5)
                    continue
                readlen = len(d)
                if readlen == 0:
                    sleep(0.5)
                    continue
                data = data + d.replace("\r","")
                index = data.find("\n\n")
                if index != -1:
                    gwsname = parse_google_server_name_from_header(data[0:index])
                    return gwsname
                elif readlen <= 64:
                    sleep(0.01)
            return ""
        except Exception as e:
            info = "%s" % e
            if len(info) == 0:
                info = type(e)
            #PRINT("Catch Exception(%s) in getgooglesvrname: %s" % (ip, info))
            return ""
