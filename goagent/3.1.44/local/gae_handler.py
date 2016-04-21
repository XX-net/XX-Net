#!/usr/bin/env python
# coding:utf-8


import errno
import time
import struct
import zlib
import functools
import re
import io
import logging
import string
import socket
import ssl
import httplib
import Queue
import urlparse
import threading

from connect_manager import https_manager
from appids_manager import appid_manager


import OpenSSL
NetWorkIOError = (socket.error, ssl.SSLError, OpenSSL.SSL.Error, OSError)

from config import config

def generate_message_html(title, banner, detail=''):
    MESSAGE_TEMPLATE = '''
    <html><head>
    <meta http-equiv="content-type" content="text/html;charset=utf-8">
    <title>$title</title>
    <style><!--
    body {font-family: arial,sans-serif}
    div.nav {margin-top: 1ex}
    div.nav A {font-size: 10pt; font-family: arial,sans-serif}
    span.nav {font-size: 10pt; font-family: arial,sans-serif; font-weight: bold}
    div.nav A,span.big {font-size: 12pt; color: #0000cc}
    div.nav A {font-size: 10pt; color: black}
    A.l:link {color: #6f6f6f}
    A.u:link {color: green}
    //--></style>
    </head>
    <body text=#000000 bgcolor=#ffffff>
    <table border=0 cellpadding=2 cellspacing=0 width=100%>
    <tr><td bgcolor=#3366cc><font face=arial,sans-serif color=#ffffff><b>Message</b></td></tr>
    <tr><td> </td></tr></table>
    <blockquote>
    <H1>$banner</H1>
    $detail
    <p>
    </blockquote>
    <table width=100% cellpadding=0 cellspacing=0><tr><td bgcolor=#3366cc><img alt="" width=1 height=4></td></tr></table>
    </body></html>
    '''
    return string.Template(MESSAGE_TEMPLATE).substitute(title=title, banner=banner, detail=detail)


def spawn_later(seconds, target, *args, **kwargs):
    def wrap(*args, **kwargs):
        __import__('time').sleep(seconds)
        try:
            result = target(*args, **kwargs)
        except:
            result = None
        return result
    return __import__('thread').start_new_thread(wrap, args, kwargs)


skip_headers = frozenset(['Vary',
                          'Via',
                          'X-Forwarded-For',
                          'Proxy-Authorization',
                          'Proxy-Connection',
                          'Upgrade',
                          'X-Chrome-Variations',
                          'Connection',
                          'Cache-Control'])

def _request(sock, headers, payload, bufsize=8192):
    request_data = 'POST /_gh/ HTTP/1.1\r\n'
    request_data += ''.join('%s: %s\r\n' % (k, v) for k, v in headers.items() if k not in skip_headers)
    request_data += '\r\n'

    if isinstance(payload, bytes):
        sock.send(request_data.encode() + payload)
    elif hasattr(payload, 'read'):
        sock.send(request_data)
        while True:
            data = payload.read(bufsize)
            if not data:
                break
            sock.send(data)
    else:
        raise TypeError('_request(payload) must be a string or buffer, not %r' % type(payload))

    response = httplib.HTTPResponse(sock, buffering=True)
    try:
        orig_timeout = sock.gettimeout()
        sock.settimeout(30)
        response.begin()
        sock.settimeout(orig_timeout)
    except httplib.BadStatusLine:
        logging.warn("_request bad status line")
        response = None
    return response

class GAE_Exception(BaseException):
    def __init__(self, type, message):
        self.type = type
        self.message = message


def request(headers={}, payload=None):
    max_retry = 3
    for i in range(max_retry):
        ssl_sock = None
        try:
            ssl_sock = https_manager.create_ssl_connection()
            if not ssl_sock:
                logging.debug('create_ssl_connection fail')
                continue

            if ssl_sock.host == '':
                ssl_sock.appid = appid_manager.get_appid()
                if not ssl_sock.appid:
                    raise GAE_Exception(1, "no appid can use")
                headers['Host'] = ssl_sock.appid + ".appspot.com"
                ssl_sock.host = headers['Host']
            else:
                headers['Host'] = ssl_sock.host


            response = _request(ssl_sock, headers, payload)
            if not response:
                continue

            response.ssl_sock = ssl_sock
            return response

        except Exception as e:
            logging.warn('request failed:%s', e)
            if ssl_sock:
                ssl_sock.close()
    raise GAE_Exception(2, "try max times")


def inflate(data):
    return zlib.decompress(data, -zlib.MAX_WBITS)

def deflate(data):
    return zlib.compress(data)[2:-4]

def fetch(method, url, headers, body):
    if isinstance(body, basestring) and body:
        if len(body) < 10 * 1024 * 1024 and 'Content-Encoding' not in headers:
            zbody = deflate(body)
            if len(zbody) < len(body):
                body = zbody
                headers['Content-Encoding'] = 'deflate'
        headers['Content-Length'] = str(len(body))

    # GAE donot allow set `Host` header
    if 'Host' in headers:
        del headers['Host']

    kwargs = {}
    if config.GAE_PASSWORD:
        kwargs['password'] = config.GAE_PASSWORD

    #kwargs['options'] =
    #kwargs['validate'] =
    kwargs['maxsize'] = config.AUTORANGE_MAXSIZE

    payload = '%s %s HTTP/1.1\r\n' % (method, url)
    payload += ''.join('%s: %s\r\n' % (k, v) for k, v in headers.items() if k not in skip_headers)
    payload += ''.join('X-URLFETCH-%s: %s\r\n' % (k, v) for k, v in kwargs.items() if v)

    request_headers = {}
    payload = deflate(payload)

    body = '%s%s%s' % (struct.pack('!h', len(payload)), payload, body)
    request_headers['Content-Length'] = str(len(body))

    response = request(request_headers, body)

    response.app_status = response.status
    if response.app_status != 200:
        return response

    data = response.read(2)
    if len(data) < 2:
        logging.warn("fetch too short lead byte len:%d %s", len(data), url)
        response.status = 502
        response.fp = io.BytesIO(b'connection aborted. too short lead byte data=' + data)
        response.read = response.fp.read
        return response
    headers_length, = struct.unpack('!h', data)
    data = response.read(headers_length)
    if len(data) < headers_length:
        logging.warn("fetch too short header need:%d get:%d %s", headers_length, len(data), url)
        response.status = 502
        response.fp = io.BytesIO(b'connection aborted. too short headers data=' + data)
        response.read = response.fp.read
        return response
    raw_response_line, headers_data = inflate(data).split('\r\n', 1)
    _, response.status, response.reason = raw_response_line.split(None, 2)
    response.status = int(response.status)
    response.reason = response.reason.strip()
    response.msg = httplib.HTTPMessage(io.BytesIO(headers_data))
    response.app_msg = response.msg.fp.read()
    return response


max_retry = 3
normcookie = functools.partial(re.compile(', ([^ =]+(?:=|$))').sub, '\\r\\nSet-Cookie: \\1')
normattachment = functools.partial(re.compile(r'filename=(.+?)').sub, 'filename="\\1"')


def send_response(wfile, status=404, headers={}, body=''):
    headers = dict((k.title(), v) for k, v in headers.items())
    if 'Transfer-Encoding' in headers:
        del headers['Transfer-Encoding']
    if 'Content-Length' not in headers:
        headers['Content-Length'] = len(body)
    if 'Connection' not in headers:
        headers['Connection'] = 'close'

    wfile.write("HTTP/1.0 %d\r\n" % status)
    for key, value in headers.items():
        wfile.write("%s: %s\r\n" % (key, value))
    wfile.write("\r\n")
    wfile.write(body)

def handler(method, url, headers, body, wfile):
    time_request = time.time()

    errors = []
    response = None
    for i in xrange(max_retry):
        try:
            response = fetch(method, url, headers, body)
            if response.app_status != 200:
                logging.debug("fetch gae status:%d url:%s", response.app_status, url)

            if response.app_status == 404:
                logging.warning('APPID %r not exists, remove it.', response.ssl_sock.appid)
                appid_manager.report_not_exist(response.ssl_sock.appid)
                appid = appid_manager.get_appid()

                if not appid:
                    html = generate_message_html('404 No usable Appid Exists', u'没有可用appid了，请配置可用的appid')
                    send_response(wfile, 404, body=html.encode('utf-8'))
                    response.close()
                    return
                else:
                    response.close()
                    continue

            if response.app_status == 503:
                logging.warning('APPID %r out of Quota, remove it.', response.ssl_sock.appid)
                appid_manager.report_out_of_quota(response.ssl_sock.appid)
                appid = appid_manager.get_appid()

                if not appid:
                    html = generate_message_html('503 No usable Appid Exists', u'appid流量不足，请增加appid')
                    send_response(wfile, 503, body=html.encode('utf-8'))
                    response.close()
                    return
                else:
                    response.close()
                    continue

            if response.app_status < 500:
                break

        except Exception as e:
            errors.append(e)
            logging.exception('gae_handler.handler %s %r, retry...', url, e)

    if len(errors) == max_retry:
        if response and response.app_status >= 500:
            status = response.app_status
            headers = dict(response.getheaders())
            content = response.read()
        else:
            status = 502
            headers = {'Content-Type': 'text/html'}
            content = generate_message_html('502 URLFetch failed', 'Local URLFetch %r failed' % url, '<br>'.join(repr(x) for x in errors))

        if response:
            response.close()

        send_response(wfile, status, headers, content.encode('utf-8'))

        logging.warn("GAE %d %s %s", status, method, url)
        return

    if response.status == 206:
        return RangeFetch(method, url, headers, body, response, wfile).fetch()

    try:

        wfile.write("HTTP/1.1 %d\r\n" % response.status)
        for key, value in response.getheaders():
            if key.title() == 'Transfer-Encoding':
                continue
            wfile.write("%s: %s\r\n" % (key, value))
        wfile.write("\r\n")

        if len(response.app_msg):
            logging.warn("APPID error:%d url:%s", response.status, url)
            wfile.write(response.app_msg)
            response.close()
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
            if not data and time.time() - time_start > 20:
                response.close()
                logging.warn("read timeout t:%d len:%d left:%d %s", (time.time()-time_request)*1000, length, (end-start), url)
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
                        logging.warn('gae_handler send to browser return %r %r', e_b, url)
                    else:
                        logging.warn('gae_handler send to browser return %r %r', e_b, url)
                    send_to_broswer = False

            if start >= end:
                https_manager.save_ssl_connection_for_reuse(response.ssl_sock)
                logging.info("GAE t:%d s:%d %d %s", (time.time()-time_request)*1000, length, response.status, url)
                return

    except NetWorkIOError as e:
        if e[0] in (errno.ECONNABORTED, errno.EPIPE) or 'bad write retry' in repr(e):
            logging.warn("gae_handler %s %r", url, e)
        else:
            logging.exception("gae_handler %s except:%r", url, e)
    except Exception as e:
        logging.exception("gae_handler %s except:%r", url, e)


class RangeFetch(object):
    threads = config.AUTORANGE_THREADS
    maxsize = config.AUTORANGE_MAXSIZE
    bufsize = config.AUTORANGE_BUFSIZE
    waitsize = config.AUTORANGE_WAITSIZE

    def __init__(self, method, url, headers, body, response, wfile):
        self.method = method
        self.wfile = wfile
        self.url = url
        self.headers = headers
        self.body = body
        self.response = response

        self._stopped = False
        self._last_app_status = {}
        self.expect_begin = 0

    def fetch(self):
        response_headers = dict((k.title(), v) for k, v in self.response.getheaders())
        content_range = response_headers['Content-Range']
        start, end, length = tuple(int(x) for x in re.search(r'bytes (\d+)-(\d+)/(\d+)', content_range).group(1, 2, 3))
        if start == 0:
            response_headers['Content-Length'] = str(length)
            del response_headers['Content-Range']
        else:
            response_headers['Content-Range'] = 'bytes %s-%s/%s' % (start, end, length)
            response_headers['Content-Length'] = str(length-start)

        logging.info('>>>>>>>>>>>>>>> RangeFetch started(%r) %d-%d', self.url, start, end)

        self.wfile.write("HTTP/1.1 %d\r\n" % self.response.status)
        for key, value in self.response.getheaders():
            self.wfile.write("%s: %s\r\n" % (key, value))
        self.wfile.write("\r\n")


        data_queue = Queue.PriorityQueue()
        range_queue = Queue.PriorityQueue()
        range_queue.put((start, end, self.response))
        self.expect_begin = start
        for begin in range(end+1, length, self.maxsize):
            range_queue.put((begin, min(begin+self.maxsize-1, length-1), None))
        for i in xrange(0, self.threads):
            range_delay_size = i * self.maxsize
            spawn_later(float(range_delay_size)/self.waitsize, self.__fetchlet, range_queue, data_queue, range_delay_size)

        has_peek = hasattr(data_queue, 'peek')
        peek_timeout = 120
        while self.expect_begin < length - 1:
            try:
                if has_peek:
                    begin, data = data_queue.peek(timeout=peek_timeout)
                    if self.expect_begin == begin:
                        data_queue.get()
                    elif self.expect_begin < begin:
                        time.sleep(0.1)
                        continue
                    else:
                        logging.error('RangeFetch Error: begin(%r) < expect_begin(%r), quit.', begin, self.expect_begin)
                        break
                else:
                    begin, data = data_queue.get(timeout=peek_timeout)
                    if self.expect_begin == begin:
                        pass
                    elif self.expect_begin < begin:
                        data_queue.put((begin, data))
                        time.sleep(0.1)
                        continue
                    else:
                        logging.error('RangeFetch Error: begin(%r) < expect_begin(%r), quit.', begin, self.expect_begin)
                        break
            except Queue.Empty:
                logging.error('data_queue peek timeout, break')
                break

            try:
                self.wfile.write(data)
                self.expect_begin += len(data)
                del data
            except Exception as e:
                logging.info('RangeFetch client closed(%s). %s', e, self.url)
                break
        self._stopped = True

    def __fetchlet(self, range_queue, data_queue, range_delay_size):
        headers = dict((k.title(), v) for k, v in self.headers.items())
        headers['Connection'] = 'close'
        while not self._stopped:
            try:
                try:
                    start, end, response = range_queue.get(timeout=1)
                    if self.expect_begin < start and data_queue.qsize() * self.bufsize + range_delay_size > 30*1024*1024:
                        range_queue.put((start, end, response))
                        time.sleep(10)
                        continue
                    headers['Range'] = 'bytes=%d-%d' % (start, end)
                    if not response:
                        response = fetch(self.method, self.url, headers, self.body)
                except Queue.Empty:
                    continue
                except Exception as e:
                    logging.warning("RangeFetch fetch response %r in __fetchlet", e)
                    range_queue.put((start, end, None))
                    continue

                if not response:
                    logging.warning('RangeFetch %s return %r', headers['Range'], response)
                    range_queue.put((start, end, None))
                    continue
                if response.app_status != 200:
                    logging.warning('Range Fetch return %s "%s %s" %s ', response.app_status, self.method, self.url, headers['Range'])

                    if response.app_status == 404:
                        logging.warning('APPID %r not exists, remove it.', response.ssl_sock.appid)
                        appid_manager.report_not_exist(response.ssl_sock.appid)
                        appid = appid_manager.get_appid()
                        if not appid:
                            logging.error("no appid left")
                            self._stopped = True
                            response.close()
                            return

                    if response.app_status == 503:
                        logging.warning('APPID %r out of Quota, remove it temporary.', response.ssl_sock.appid)
                        appid_manager.report_out_of_quota(response.ssl_sock.appid)
                        appid = appid_manager.get_appid()
                        if not appid:
                            logging.error("no appid left")
                            self._stopped = True
                            response.close()
                            return

                    response.close()
                    range_queue.put((start, end, None))
                    continue

                if response.getheader('Location'):
                    self.url = urlparse.urljoin(self.url, response.getheader('Location'))
                    logging.info('RangeFetch Redirect(%r)', self.url)
                    response.close()
                    range_queue.put((start, end, None))
                    continue

                if 200 <= response.status < 300:
                    content_range = response.getheader('Content-Range')
                    if not content_range:
                        logging.warning('RangeFetch "%s %s" return Content-Range=%r: response headers=%r, retry %s-%s', self.method, self.url, content_range, response.getheaders(), start, end)
                        response.close()
                        range_queue.put((start, end, None))
                        continue
                    content_length = int(response.getheader('Content-Length', 0))
                    logging.info('>>>>>>>>>>>>>>> [thread %s] %s %s', threading.currentThread().ident, content_length, content_range)

                    time_start = time.time()
                    while start < end + 1:
                        try:
                            data = response.read(self.bufsize)
                            if not data:
                                if time.time() - time_start > 20:
                                    break
                                else:
                                    time.sleep(0.1)
                                    continue

                            data_len = len(data)
                            data_queue.put((start, data))
                            start += data_len


                        except Exception as e:
                            logging.warning('RangeFetch "%s %s" %s failed: %s', self.method, self.url, headers['Range'], e)
                            break

                    if start < end + 1:
                        logging.warning('RangeFetch "%s %s" retry %s-%s', self.method, self.url, start, end)
                        response.close()
                        range_queue.put((start, end, None))
                        continue

                    https_manager.save_ssl_connection_for_reuse(response.ssl_sock)
                    logging.info('>>>>>>>>>>>>>>> Successfully reached %d bytes.', start - 1)
                else:
                    logging.error('RangeFetch %r return %s', self.url, response.status)
                    response.close()
                    range_queue.put((start, end, None))
                    continue
            except StandardError as e:
                logging.exception('RangeFetch._fetchlet error:%s', e)
                raise

