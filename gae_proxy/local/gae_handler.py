#!/usr/bin/env python
# coding:utf-8


import errno
import time
import struct
import zlib
import functools
import re
import io
import xlog
import string
import socket
import ssl
import httplib
import Queue
import urlparse
import threading
import BaseHTTPServer

from connect_manager import https_manager
from appids_manager import appid_manager


import OpenSSL
NetWorkIOError = (socket.error, ssl.SSLError, OpenSSL.SSL.Error, OSError)

from config import config
from google_ip import google_ip

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
                          'X-Google-Cache-Control',
                          'X-Forwarded-For',
                          'Proxy-Authorization',
                          'Proxy-Connection',
                          'Upgrade',
                          'X-Chrome-Variations',
                          'Connection',
                          'Cache-Control'
                          ])

def send_header(wfile, keyword, value):
    keyword = keyword.title()
    if keyword == 'Set-Cookie':
        # https://cloud.google.com/appengine/docs/python/urlfetch/responseobjects
        for cookie in re.split(r', (?=[^ =]+(?:=|$))', value):
            wfile.write("%s: %s\r\n" % (keyword, cookie))
            #logging.debug("Head1 %s: %s", keyword, cookie)
    elif keyword == 'Content-Disposition' and '"' not in value:
        value = re.sub(r'filename=([^"\']+)', 'filename="\\1"', value)
        wfile.write("%s: %s\r\n" % (keyword, value))
        #logging.debug("Head1 %s: %s", keyword, value)
    else:
        wfile.write("%s: %s\r\n" % (keyword, value))
        #logging.debug("Head1 %s: %s", keyword, value)

def _request(sock, headers, payload, bufsize=8192):
    request_data = 'POST /_gh/ HTTP/1.1\r\n'
    request_data += ''.join('%s: %s\r\n' % (k, v) for k, v in headers.items() if k not in skip_headers)
    request_data += '\r\n'

    if isinstance(payload, bytes):
        sock.send(request_data.encode())
        payload_len = len(payload)
        start = 0
        while start < payload_len:
            send_size = min(payload_len - start, 65535)
            sended = sock.send(payload[start:start+send_size])
            start += sended
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
        sock.settimeout(100)
        response.begin()
        sock.settimeout(orig_timeout)
    except httplib.BadStatusLine as e:
        #logging.warn("_request bad status line:%r", e)
        response.close()
        response = None
    except Exception as e:
        xlog.warn("_request:%r", e)
    return response

class GAE_Exception(BaseException):
    def __init__(self, type, message):
        xlog.debug("GAE_Exception %r %r", type, message)
        self.type = type
        self.message = message


def request(headers={}, payload=None):
    max_retry = 3
    for i in range(max_retry):
        ssl_sock = None
        try:
            ssl_sock = https_manager.get_ssl_connection()
            if not ssl_sock:
                xlog.debug('create_ssl_connection fail')
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
                ssl_sock.close()
                continue

            response.ssl_sock = ssl_sock
            return response

        except Exception as e:
            xlog.warn('request failed:%s', e)
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
        if len(body) > 10 * 1024 * 1024:
            xlog.warn("body len:%d %s %s", len(body), method, url)
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
    kwargs['timeout'] = '19'

    payload = '%s %s HTTP/1.1\r\n' % (method, url)
    payload += ''.join('%s: %s\r\n' % (k, v) for k, v in headers.items() if k not in skip_headers)
    #for k, v in headers.items():
    #    logging.debug("Send %s: %s", k, v)
    payload += ''.join('X-URLFETCH-%s: %s\r\n' % (k, v) for k, v in kwargs.items() if v)

    request_headers = {}
    payload = deflate(payload)

    body = '%s%s%s' % (struct.pack('!h', len(payload)), payload, body)
    request_headers['Content-Length'] = str(len(body))

    response = request(request_headers, body)

    response.app_msg = ''
    response.app_status = response.status
    if response.app_status != 200:
        return response

    data = response.read(2)
    if len(data) < 2:
        xlog.warn("fetch too short lead byte len:%d %s", len(data), url)
        response.status = 502
        response.fp = io.BytesIO(b'connection aborted. too short lead byte data=' + data)
        response.read = response.fp.read
        return response
    headers_length, = struct.unpack('!h', data)
    data = response.read(headers_length)
    if len(data) < headers_length:
        xlog.warn("fetch too short header need:%d get:%d %s", headers_length, len(data), url)
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

    wfile.write("HTTP/1.1 %d\r\n" % status)
    for key, value in headers.items():
        #wfile.write("%s: %s\r\n" % (key, value))
        send_header(wfile, key, value)
    wfile.write("\r\n")
    wfile.write(body)

def return_fail_message(wfile):
    html = generate_message_html('504 GAEProxy Proxy Time out', u'连接超时，先休息一会再来！')
    send_response(wfile, 504, body=html.encode('utf-8'))
    return

# fix bug for android market app: Mobogenie
# GAE url_fetch refuse empty value in header.
def clean_empty_header(headers):
    remove_list = []
    for key in headers:
        value = headers[key]
        if value == "":
            remove_list.append(key)

    for key in remove_list:
        del headers[key]

    return headers


def handler(method, url, headers, body, wfile):
    time_request = time.time()

    headers = clean_empty_header(headers)
    errors = []
    response = None
    while True:
        if time.time() - time_request > 30: #time out
            return return_fail_message(wfile)

        try:
            response = fetch(method, url, headers, body)
            if response.app_status != 200:
                xlog.warn("fetch gae status:%s url:%s", response.app_status, url)

                server_type = response.getheader('Server', "")
                if "gws" not in server_type:
                    xlog.warn("IP:%s not support GAE, server type:%s", response.ssl_sock.ip, server_type)
                    google_ip.report_connect_fail(response.ssl_sock.ip, force_remove=True)
                    response.close()
                    continue

            if response.app_status == 404:
                xlog.warning('APPID %r not exists, remove it.', response.ssl_sock.appid)
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

            if response.app_status == 403 or response.app_status == 405: #Method not allowed
                # google have changed from gws to gvs, need to remove.
                xlog.warning('405 Method not allowed. remove %s ', response.ssl_sock.ip)
                # some ip can connect, and server type is gws
                # but can't use as GAE server
                # so we need remove it immediately
                google_ip.report_connect_fail(response.ssl_sock.ip, force_remove=True)
                response.close()
                continue

            if response.app_status == 503:
                xlog.warning('APPID %r out of Quota, remove it.', response.ssl_sock.appid)
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

        except GAE_Exception as e:
            errors.append(e)
            xlog.warn("gae_exception:%r %s", e, url)
        except Exception as e:
            errors.append(e)
            xlog.exception('gae_handler.handler %r %s , retry...', e, url)


    if response.status == 206:
        return RangeFetch(method, url, headers, body, response, wfile).fetch()
    try:
        wfile.write("HTTP/1.1 %d %s\r\n" % (response.status, response.reason))
        response_headers = {}
        for key, value in response.getheaders():
            key = key.title()
            if key == 'Transfer-Encoding':
                #http://en.wikipedia.org/wiki/Chunked_transfer_encoding
                continue
            if key in skip_headers:
                continue
            response_headers[key] = value

        if 'X-Head-Content-Length' in response_headers:
            if method == "HEAD":
                response_headers['Content-Length'] = response_headers['X-Head-Content-Length']
            del response_headers['X-Head-Content-Length']

        send_to_browser = True
        try:
            for key in response_headers:
                value = response_headers[key]
                send_header(wfile, key, value)
                #logging.debug("Head- %s: %s", key, value)
            wfile.write("\r\n")
        except Exception as e:
            send_to_browser = False
            xlog.warn("gae_handler.handler send response fail. t:%d e:%r %s", time.time()-time_request, e, url)


        if len(response.app_msg):
            xlog.warn("APPID error:%d url:%s", response.status, url)
            wfile.write(response.app_msg)
            response.close()
            return

        content_length = int(response.getheader('Content-Length', 0))
        content_range = response.getheader('Content-Range', '')
        if content_range:
            start, end, length = tuple(int(x) for x in re.search(r'bytes (\d+)-(\d+)/(\d+)', content_range).group(1, 2, 3))
        else:
            start, end, length = 0, content_length-1, content_length

        last_read_time = time.time()
        while True:
            if start > end:
                https_manager.save_ssl_connection_for_reuse(response.ssl_sock)
                xlog.info("GAE t:%d s:%d %d %s", (time.time()-time_request)*1000, length, response.status, url)
                return

            data = response.read(config.AUTORANGE_BUFSIZE)
            if not data:
                if time.time() - last_read_time > 20:
                    response.close()
                    xlog.warn("read timeout t:%d len:%d left:%d %s", (time.time()-time_request)*1000, length, (end-start), url)
                    return
                else:
                    time.sleep(0.1)
                    continue

            last_read_time = time.time()
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
                        xlog.warn('gae_handler send to browser return %r %r', e_b, url)
                    else:
                        xlog.warn('gae_handler send to browser return %r %r', e_b, url)
                    send_to_browser = False

    except NetWorkIOError as e:
        time_except = time.time()
        time_cost = time_except - time_request
        if e[0] in (errno.ECONNABORTED, errno.EPIPE) or 'bad write retry' in repr(e):
            xlog.warn("gae_handler err:%r time:%d %s ", e, time_cost, url)
        else:
            xlog.exception("gae_handler except:%r %s", e, url)
    except Exception as e:
        xlog.exception("gae_handler except:%r %s", e, url)


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

        xlog.info('>>>>>>>>>>>>>>> RangeFetch started(%r) %d-%d', self.url, start, end)

        try:
            self.wfile.write("HTTP/1.1 200 OK\r\n")
            for key in response_headers:
                if key == 'Transfer-Encoding':
                    continue
                if key == 'X-Head-Content-Length':
                    continue
                if key in skip_headers:
                    continue
                value = response_headers[key]
                #logging.debug("Head %s: %s", key.title(), value)
                send_header(self.wfile, key, value)
            self.wfile.write("\r\n")
        except Exception as e:
            self._stopped = True
            xlog.warn("RangeFetch send response fail:%r %s", e, self.url)
            return

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
                        xlog.error('RangeFetch Error: begin(%r) < expect_begin(%r), quit.', begin, self.expect_begin)
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
                        xlog.error('RangeFetch Error: begin(%r) < expect_begin(%r), quit.', begin, self.expect_begin)
                        break
            except Queue.Empty:
                xlog.error('data_queue peek timeout, break')
                break

            try:
                ret = self.wfile.write(data)
                if ret == ssl.SSL_ERROR_WANT_WRITE or ret == ssl.SSL_ERROR_WANT_READ:
                    xlog.debug("send to browser wfile.write ret:%d, retry", ret)
                    ret = self.wfile.write(data)
                    xlog.debug("send to browser wfile.write ret:%d", ret)
                self.expect_begin += len(data)
                del data
            except Exception as e:
                xlog.warn('RangeFetch client closed(%s). %s', e, self.url)
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
                    xlog.warning("RangeFetch fetch response %r in __fetchlet", e)
                    range_queue.put((start, end, None))
                    continue

                if not response:
                    xlog.warning('RangeFetch %s return %r', headers['Range'], response)
                    range_queue.put((start, end, None))
                    continue
                if response.app_status != 200:
                    xlog.warning('Range Fetch return %s "%s %s" %s ', response.app_status, self.method, self.url, headers['Range'])

                    if response.app_status == 404:
                        xlog.warning('APPID %r not exists, remove it.', response.ssl_sock.appid)
                        appid_manager.report_not_exist(response.ssl_sock.appid)
                        appid = appid_manager.get_appid()
                        if not appid:
                            xlog.error("no appid left")
                            self._stopped = True
                            response.close()
                            return

                    if response.app_status == 503:
                        xlog.warning('APPID %r out of Quota, remove it temporary.', response.ssl_sock.appid)
                        appid_manager.report_out_of_quota(response.ssl_sock.appid)
                        appid = appid_manager.get_appid()
                        if not appid:
                            xlog.error("no appid left")
                            self._stopped = True
                            response.close()
                            return

                    response.close()
                    range_queue.put((start, end, None))
                    continue

                if response.getheader('Location'):
                    self.url = urlparse.urljoin(self.url, response.getheader('Location'))
                    xlog.info('RangeFetch Redirect(%r)', self.url)
                    response.close()
                    range_queue.put((start, end, None))
                    continue

                if 200 <= response.status < 300:
                    content_range = response.getheader('Content-Range')
                    if not content_range:
                        xlog.warning('RangeFetch "%s %s" return Content-Range=%r: response headers=%r, retry %s-%s', self.method, self.url, content_range, response.getheaders(), start, end)
                        response.close()
                        range_queue.put((start, end, None))
                        continue
                    content_length = int(response.getheader('Content-Length', 0))
                    xlog.info('>>>>>>>>>>>>>>> [thread %s] %s %s', threading.currentThread().ident, content_length, content_range)

                    time_last_read = time.time()
                    while start < end + 1:
                        try:
                            data = response.read(self.bufsize)
                            if not data:
                                if time.time() - time_last_read > 20:
                                    break
                                else:
                                    time.sleep(0.1)
                                    continue

                            time_last_read = time.time()
                            data_len = len(data)
                            data_queue.put((start, data))
                            start += data_len

                        except Exception as e:
                            xlog.warning('RangeFetch "%s %s" %s failed: %s', self.method, self.url, headers['Range'], e)
                            break

                    if start < end + 1:
                        xlog.warning('RangeFetch "%s %s" retry %s-%s', self.method, self.url, start, end)
                        response.close()
                        range_queue.put((start, end, None))
                        continue

                    https_manager.save_ssl_connection_for_reuse(response.ssl_sock)
                    xlog.info('>>>>>>>>>>>>>>> Successfully reached %d bytes.', start - 1)
                else:
                    xlog.error('RangeFetch %r return %s', self.url, response.status)
                    response.close()
                    range_queue.put((start, end, None))
                    continue
            except StandardError as e:
                xlog.exception('RangeFetch._fetchlet error:%s', e)
                raise

