#!/usr/bin/env python
# coding:utf-8


import errno
import time
import re
import logging
import socket
import ssl
import httplib
from direct_connect_manager import direct_connect_manager

from gae_handler import generate_message_html, send_response
from connect_manager import connect_allow_time
import OpenSSL
NetWorkIOError = (socket.error, ssl.SSLError, OpenSSL.SSL.Error, OSError)

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
        try:
            wfile.write("%s: %s\r\n" % (keyword, value))
        except Exception as e:
            logging.exception("e:%r header: %s: %s ", e, keyword, value)
            raise e



def fetch(method, host, path, headers, payload, bufsize=8192):
    request_data = '%s %s HTTP/1.1\r\n' % (method, path)
    request_data += ''.join('%s: %s\r\n' % (k, v) for k, v in headers.items())
    request_data += '\r\n'

    ssl_sock = direct_connect_manager.create_ssl_connection(host)
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
        logging.warn("_request bad status line:%r", e)
        response = None
    except Exception as e:
        logging.warn("_request:%r", e)
    return response


def handler(method, host, url, headers, body, wfile):
    global connect_allow_time
    time_request = time.time()

    errors = []
    response = None
    while True:
        if time.time() - time_request > 30 or time.time() < connect_allow_time:
            html = generate_message_html('504 GoAgent Proxy Time out', u'翻不上去，先休息2分钟再来！')
            send_response(wfile, 504, body=html.encode('utf-8'))
            return

        try:
            response = fetch(method, host, url, headers, body)
            if response:
                break

        except Exception as e:
            errors.append(e)
            logging.exception('direct_handler.handler %r %s %s , retry...', e, host, url)

    try:
        wfile.write("HTTP/1.1 %d %s\r\n" % (response.status, response.reason))
        response_headers = dict((k.title(), v) for k, v in response.getheaders())
        for key, value in response.getheaders():
            send_header(wfile, key, value)
            #logging.debug("Head- %s: %s", key, value)
        wfile.write("\r\n")

        if method == 'HEAD' or response.status in (204, 304):
            logging.info("DIRECT t:%d %d %s %s", (time.time()-time_request)*1000, response.status, host, url)
            direct_connect_manager.save_ssl_connection_for_reuse(response.ssl_sock, host)
            response.close()
            return

        if 'Transfer-Encoding' in response_headers:
            length = 0
            while True:
                data = response.read(8192)
                if not data:
                    wfile.write('0\r\n\r\n')
                    break
                length += len(data)
                wfile.write('%x\r\n' % len(data))
                wfile.write(data)
                wfile.write('\r\n')
            response.close()
            logging.info("DIRECT chucked t:%d s:%d %d %s %s", (time.time()-time_request)*1000, length, response.status, host, url)
            return

        content_length = int(response.getheader('Content-Length', 0))
        content_range = response.getheader('Content-Range', '')
        if content_range:
            start, end, length = tuple(int(x) for x in re.search(r'bytes (\d+)-(\d+)/(\d+)', content_range).group(1, 2, 3))
        else:
            start, end, length = 0, content_length-1, content_length

        time_start = time.time()
        send_to_broswer = True
        while True:
            data = response.read(config.AUTORANGE_BUFSIZE)
            if not data and time.time() - time_start > 120:
                response.close()
                logging.warn("read timeout t:%d len:%d left:%d %s %s", (time.time()-time_request)*1000, length, (end-start), host, url)
                return

            data_len = len(data)
            start += data_len
            if send_to_broswer:
                try:
                    ret = wfile.write(data)
                    if ret == ssl.SSL_ERROR_WANT_WRITE or ret == ssl.SSL_ERROR_WANT_READ:
                        logging.debug("send to browser wfile.write ret:%d", ret)
                        ret = wfile.write(data)
                except Exception as e_b:
                    if e_b[0] in (errno.ECONNABORTED, errno.EPIPE, errno.ECONNRESET) or 'bad write retry' in repr(e_b):
                        logging.warn('direct_handler send to browser return %r %s %r', e_b, host, url)
                    else:
                        logging.warn('direct_handler send to browser return %r %s %r', e_b, host, url)
                    send_to_broswer = False

            if start >= end:
                direct_connect_manager.save_ssl_connection_for_reuse(response.ssl_sock, host)
                logging.info("DIRECT t:%d s:%d %d %s %s", (time.time()-time_request)*1000, length, response.status, host, url)
                return

    except NetWorkIOError as e:
        if e[0] in (errno.ECONNABORTED, errno.EPIPE) or 'bad write retry' in repr(e):
            logging.warn("direct_handler err:%r %s %s", e, host, url)
        else:
            logging.exception("direct_handler except:%r %s %s", e, host, url)
    except Exception as e:
        logging.exception("direct_handler except:%r %s %s", e, host, url)
