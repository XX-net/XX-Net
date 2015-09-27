#!/usr/bin/env python
# coding:utf-8


import errno
import time
import re
import xlog
import socket
import ssl
import httplib

import OpenSSL
NetWorkIOError = (socket.error, ssl.SSLError, OpenSSL.SSL.Error, OSError)


from connect_manager import https_manager

from gae_handler import generate_message_html, send_response
from connect_control import connect_allow_time, connect_fail_time
from gae_handler import return_fail_message
from google_ip import google_ip
from config import config



def send_header(wfile, keyword, value):
    keyword = keyword.title()
    if keyword == 'Set-Cookie':
        for cookie in re.split(r', (?=[^ =]+(?:=|$))', value):
            wfile.write("%s: %s\r\n" % (keyword, cookie))
            #logging.debug("Head1 %s: %s", keyword, cookie)
    elif keyword == 'Content-Disposition' and '"' not in value:
        value = re.sub(r'filename=([^"\']+)', 'filename="\\1"', value)
        wfile.write("%s: %s\r\n" % (keyword, value))
        #logging.debug("Head1 %s: %s", keyword, value)
    elif keyword == "Alternate-Protocol":
        return
    else:
        #logging.debug("Head1 %s: %s", keyword, value)
        wfile.write("%s: %s\r\n" % (keyword, value))



def fetch(method, host, path, headers, payload, bufsize=8192):
    request_data = '%s %s HTTP/1.1\r\n' % (method, path)
    request_data += ''.join('%s: %s\r\n' % (k, v) for k, v in headers.items())
    request_data += '\r\n'

    ssl_sock = https_manager.get_ssl_connection(host)
    if not ssl_sock:
        return

    ssl_sock.send(request_data.encode())
    payload_len = len(payload)
    start = 0
    while start < payload_len:
        send_size = min(payload_len - start, 65535)
        sended = ssl_sock.send(payload[start:start+send_size])
        start += sended

    response = httplib.HTTPResponse(ssl_sock, buffering=True)

    response.ssl_sock = ssl_sock
    try:
        orig_timeout = ssl_sock.gettimeout()
        ssl_sock.settimeout(90)
        response.begin()
        ssl_sock.settimeout(orig_timeout)
    except httplib.BadStatusLine as e:
        xlog.warn("direct_handler.fetch bad status line:%r", e)
        response = None
    except Exception as e:
        xlog.warn("direct_handler.fetch:%r", e)
        response = None
    return response


def handler(method, host, url, headers, body, wfile):
    time_request = time.time()

    errors = []
    response = None
    while True:
        if time.time() - time_request > 30:
            return return_fail_message(wfile)

        try:
            response = fetch(method, host, url, headers, body)
            if response:
                if response.status > 400:
                    server_type = response.getheader('Server', "")
                    if "gws" not in server_type:
                        xlog.warn("IP:%s not support GAE, server type:%s status:%d", response.ssl_sock.ip, server_type, response.status)
                        google_ip.report_connect_fail(response.ssl_sock.ip, force_remove=True)
                        response.close()
                        continue
                break
        except OpenSSL.SSL.SysCallError as e:
            errors.append(e)
            xlog.warn("direct_handler.handler err:%r %s/%s", e, host, url)
        except Exception as e:
            errors.append(e)
            xlog.exception('direct_handler.handler %r %s %s , retry...', e, host, url)

    try:
        send_to_browser = True
        try:
            response_headers = dict((k.title(), v) for k, v in response.getheaders())
            wfile.write("HTTP/1.1 %d %s\r\n" % (response.status, response.reason))
            for key, value in response.getheaders():
                send_header(wfile, key, value)
            wfile.write("\r\n")
        except Exception as e:
            send_to_browser = False
            wait_time = time.time()-time_request
            xlog.warn("direct_handler.handler send response fail. t:%d e:%r %s%s", wait_time, e, host, url)


        if method == 'HEAD' or response.status in (204, 304):
            xlog.info("DIRECT t:%d %d %s %s", (time.time()-time_request)*1000, response.status, host, url)
            https_manager.save_ssl_connection_for_reuse(response.ssl_sock, host)
            response.close()
            return

        if 'Transfer-Encoding' in response_headers:
            length = 0
            while True:
                try:
                    data = response.read(8192)
                except httplib.IncompleteRead, e:
                    data = e.partial

                if send_to_browser:
                    try:
                        if not data:
                            wfile.write('0\r\n\r\n')
                            break
                        length += len(data)
                        wfile.write('%x\r\n' % len(data))
                        wfile.write(data)
                        wfile.write('\r\n')
                    except Exception as e:
                        send_to_browser = False
                        xlog.warn("direct_handler.handler send Transfer-Encoding t:%d e:%r %s/%s", time.time()-time_request, e, host, url)
                else:
                    if not data:
                        break

            response.close()
            xlog.info("DIRECT chucked t:%d s:%d %d %s %s", (time.time()-time_request)*1000, length, response.status, host, url)
            return

        content_length = int(response.getheader('Content-Length', 0))
        content_range = response.getheader('Content-Range', '')
        if content_range:
            start, end, length = tuple(int(x) for x in re.search(r'bytes (\d+)-(\d+)/(\d+)', content_range).group(1, 2, 3))
        else:
            start, end, length = 0, content_length-1, content_length

        time_last_read = time.time()
        while True:
            if start > end:
                https_manager.save_ssl_connection_for_reuse(response.ssl_sock, host)
                xlog.info("DIRECT t:%d s:%d %d %s %s", (time.time()-time_request)*1000, length, response.status, host, url)
                return

            data = response.read(config.AUTORANGE_BUFSIZE)
            if not data:
                if time.time() - time_last_read > 20:
                    response.close()
                    xlog.warn("read timeout t:%d len:%d left:%d %s %s", (time.time()-time_request)*1000, length, (end-start), host, url)
                    return
                else:
                    time.sleep(0.1)
                    continue

            time_last_read = time.time()
            data_len = len(data)
            start += data_len
            if send_to_browser:
                try:
                    ret = wfile.write(data)
                    if ret == ssl.SSL_ERROR_WANT_WRITE or ret == ssl.SSL_ERROR_WANT_READ:
                        xlog.debug("send to browser wfile.write ret:%d", ret)
                        ret = wfile.write(data)
                except Exception as e_b:
                    if e_b[0] in (errno.ECONNABORTED, errno.EPIPE, errno.ECONNRESET) or 'bad write retry' in repr(e_b):
                        xlog.warn('direct_handler send to browser return %r %s %r', e_b, host, url)
                    else:
                        xlog.warn('direct_handler send to browser return %r %s %r', e_b, host, url)
                    send_to_browser = False


    except NetWorkIOError as e:
        time_except = time.time()
        time_cost = time_except - time_request
        if e[0] in (errno.ECONNABORTED, errno.EPIPE) or 'bad write retry' in repr(e):
            xlog.exception("direct_handler err:%r %s %s time:%d", e, host, url, time_cost)
        else:
            xlog.exception("direct_handler except:%r %s %s", e, host, url)
    except Exception as e:
        xlog.exception("direct_handler except:%r %s %s", e, host, url)
