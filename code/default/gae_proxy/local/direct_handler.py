#!/usr/bin/env python
# coding:utf-8


import time
import re
import socket
import ssl

import OpenSSL
NetWorkIOError = (socket.error, ssl.SSLError, OpenSSL.SSL.Error, OSError)


from gae_handler import return_fail_message

from front import direct_front
from xlog import getLogger
xlog = getLogger("gae_proxy")

google_server_types = ["ClientMapServer"]


def send_header(wfile, keyword, value):
    keyword = keyword.title()
    if keyword == 'Set-Cookie':
        for cookie in re.split(r', (?=[^ =]+(?:=|$))', value):
            wfile.write("%s: %s\r\n" % (keyword, cookie))
    elif keyword == 'Content-Disposition' and '"' not in value:
        value = re.sub(r'filename=([^"\']+)', 'filename="\\1"', value)
        wfile.write("%s: %s\r\n" % (keyword, value))
    elif keyword == "Alternate-Protocol":
        return
    else:
        wfile.write("%s: %s\r\n" % (keyword, value))


def handler(method, host, path, headers, body, wfile, timeout=60):
    time_request = time.time()

    if "Connection" in headers and headers["Connection"] == "close":
        del headers["Connection"]

    errors = []
    while True:
        time_left = time_request + timeout - time.time()
        if time_left <= 0:
            return return_fail_message(wfile)

        try:
            response = direct_front.request(method, host, path, headers, body, timeout=time_left)
            if response:
                if response.status > 600:
                    xlog.warn("direct %s %s % status:%d", method, host, path, response.status)
                    continue
                elif response.status > 400:
                    server_type = response.headers.get('Server', "")

                    if "G" not in server_type and "g" not in server_type and server_type not in google_server_types:

                        xlog.warn("IP:%s host:%s not support GAE, server type:%s status:%d",
                                  response.ssl_sock.ip, host, server_type, response.status)
                        direct_front.ip_manager.report_connect_fail(response.ssl_sock.ip, force_remove=True)
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
    for key, value in response.headers.items():
        key = key.title()
        response_headers[key] = value

    response_headers["Persist"] = ""
    response_headers["Connection"] = "Persist"

    try:
        wfile.write("HTTP/1.1 %d %s\r\n" % (response.status, response.reason))
        for key in response_headers:
            value = response_headers[key]
            send_header(wfile, key, value)
        wfile.write("\r\n")
        wfile.flush()

        length = 0
        while True:
            data = response.task.read()
            if isinstance(data, memoryview):
                data = data.tobytes()

            data_len = len(data)
            length += data_len
            if 'Transfer-Encoding' in response.headers:
                if not data_len:
                    wfile._sock.sendall('0\r\n\r\n')
                    break
                wfile._sock.sendall('%x\r\n' % data_len)
                wfile._sock.sendall(data)
                wfile._sock.sendall('\r\n')
            else:
                if not data_len:
                    break
                wfile._sock.sendall(data)

        xlog.info("DIRECT t:%d s:%d %d %s %s",
                  (time.time()-time_request)*1000, length, response.status, host, path)
    except Exception as e:
        xlog.exception("DIRECT %s %d %s %s, t:%d send to client except:%r",
                 method, response.status, host, path, (time.time()-time_request)*1000, e)