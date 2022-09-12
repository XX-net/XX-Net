#!/usr/bin/env python
# coding:utf-8


import time
import re
import socket
import ssl
import errno

try:
    import OpenSSL
    NetWorkIOError = (socket.error, ssl.SSLError, OpenSSL.SSL.Error, OSError)
except:
    NetWorkIOError = (socket.error, ssl.SSLError, OSError)


from .gae_handler import send_header, return_fail_message

from .front import direct_front
from xlog import getLogger
xlog = getLogger("gae_proxy")

google_server_types = [b"ClientMapServer"]


def handler(method, host, path, headers, body, wfile, timeout=60):
    time_request = time.time()

    if b"Connection" in headers and headers[b"Connection"] == b"close":
        del headers[b"Connection"]

    errors = []
    while True:
        time_left = time_request + timeout - time.time()
        if time_left <= 0:
            return_fail_message(wfile)
            return "ok"

        try:
            response = direct_front.request(method, host, path, headers, body, timeout=time_left)
            if response:
                if response.status > 600:
                    xlog.warn("direct %s %s % status:%d", method, host, path, response.status)
                    continue
                elif response.status > 400:
                    server_type = response.headers.get(b'Server', b"")

                    if b"G" not in server_type and b"g" not in server_type and server_type not in google_server_types:

                        xlog.debug("IP:%s host:%s not support GAE, server type:%s status:%d",
                                  response.ssl_sock.ip_str, host, server_type, response.status)
                        #direct_front.ip_manager.report_connect_fail(response.ssl_sock.ip_str, force_remove=True)
                        response.worker.close()
                        continue
                break
        except OpenSSL.SSL.SysCallError as e:
            errors.append(e)
            xlog.warn("direct_handler.handler err:%r %s/%s", e, host, path)
        except Exception as e:
            errors.append(e)
            xlog.exception('direct_handler.handler %r %s %s , retry...', e, host, path)

    response_headers = {}
    for key, value in list(response.headers.items()):
        key = key.title()
        response_headers[key] = value

    response_headers[b"Persist"] = b""
    response_headers[b"Connection"] = b"Persist"

    try:
        wfile.write(b"HTTP/1.1 %d %s\r\n" % (response.status, response.reason))
        for key, value in list(response_headers.items()):
            send_header(wfile, key, value)
        wfile.write(b"\r\n")

        length = 0
        while True:
            data = response.task.read()
            data_len = len(data)
            length += data_len
            if b'Transfer-Encoding' in response_headers:
                if not data_len:
                    wfile.write(b'0\r\n\r\n')
                    break
                wfile.write(b'%x\r\n' % data_len)
                wfile.write(data)
                wfile.write(b'\r\n')
            else:
                if not data_len:
                    break
                wfile.write(data)

        xlog.info("DIRECT t:%d s:%d %d %s %s",
                  (time.time()-time_request)*1000, length, response.status, host, path)
        if b'Content-Length' in response_headers or b'Transfer-Encoding' in response_headers:
            return "ok"
    except NetWorkIOError as e:
        xlog.warn('DIRECT %s %s%s except:%r', method, host, path, e)
        if e.args[0] not in (errno.ECONNABORTED, errno.ETIMEDOUT, errno.EPIPE):
            raise
    except Exception as e:
        xlog.exception("DIRECT %s %d %s%s, t:%d send to client except:%r",
                 method, response.status, host, path, (time.time()-time_request)*1000, e)