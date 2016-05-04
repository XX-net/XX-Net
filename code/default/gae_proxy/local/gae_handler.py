#!/usr/bin/env python
# coding:utf-8


"""
GoAgent local-server protocol 3.2

request:
  POST /_gh/ HTTP/1.1
  HOST: appid.appspot.com
  content-length: xxx

  http content:
  {
    pack_req_head_len: 2 bytes,
    pack_req_head : deflate{
      original request line,
      original request headers,
      X-URLFETCH-kwargs HEADS, {
        password,
        maxsize, defined in config AUTO RANGE MAX SIZE
        timeout, request timeout for GAE urlfetch.
      }
    }
    body
  }

response:
  200 OK
  http-Heads:
    Content-type: image/gif

  http-content:{
      response_head{
        data_len: 2 bytes,
        data: deflate{
         HTTP/1.1 status, status_code
         headers
         content = error_message, if GAE server fail
        }
      }

      body
  }
"""


import errno
import time
import struct
import re
import io
import string
import ssl
import cgi
import Queue
import urlparse
import urllib
import threading
import zlib


from xlog import getLogger
xlog = getLogger("gae_proxy")
from appids_manager import appid_manager


from config import config
from google_ip import google_ip
import check_local_network
from http_dispatcher import http_dispatch
from http_common import *


def inflate(data):
    return zlib.decompress(data, -zlib.MAX_WBITS)


def deflate(data):
    return zlib.compress(data)[2:-4]


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
            #xlog.debug("Head1 %s: %s", keyword, cookie)
    elif keyword == 'Content-Disposition' and '"' not in value:
        value = re.sub(r'filename=([^"\']+)', 'filename="\\1"', value)
        wfile.write("%s: %s\r\n" % (keyword, value))
        #xlog.debug("Head1 %s: %s", keyword, value)
    else:
        wfile.write("%s: %s\r\n" % (keyword, value))
        #xlog.debug("Head1 %s: %s", keyword, value)


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


def clean_empty_header(headers):
    # fix bug for android market app: Mobogenie
    # GAE url_fetch refuse empty value in header.
    remove_list = []
    for key in headers:
        value = headers[key]
        if value == "":
            remove_list.append(key)

    for key in remove_list:
        del headers[key]

    return headers


def request_gae_server(headers, body):
    # process on http protocol
    # process status code return by http server
    # raise error, let up layer retry.

    response = http_dispatch.request(headers, body)
    if not response:
        raise GAE_Exception(600, "fetch gae fail")

    if response.status >= 600:
        raise GAE_Exception(response.status, "fetch gae fail:%d" % response.status)

    server_type = response.headers.get("server", "")
    content_type = response.headers.get("content-type", "")
    if ("gws" not in server_type and "Google Frontend" not in server_type and "GFE" not in server_type) or \
        response.status == 403 or response.status == 405:

        # some ip can connect, and server type can be gws
        # but can't use as GAE server
        # so we need remove it immediately

        xlog.warn("IP:%s not support GAE, server:%s status:%d", response.ssl_sock.ip, server_type,
                   response.status)
        google_ip.recheck_ip(response.ssl_sock.ip)
        response.worker.close("ip not support GAE")
        raise GAE_Exception(602, "ip not support GAE")

    if response.status == 404:
        # xlog.warning('APPID %r not exists, remove it.', response.ssl_sock.appid)
        appid_manager.report_not_exist(response.ssl_sock.appid, response.ssl_sock.ip)
        # google_ip.report_connect_closed(response.ssl_sock.ip, "appid not exist")
        response.worker.close("appid not exist:%s" % response.ssl_sock.appid)
        raise GAE_Exception(603, "appid not support GAE")

    if response.status == 503:
        appid = response.ssl_sock.appid
        xlog.warning('APPID %r out of Quota, remove it. %s', appid, response.ssl_sock.ip)
        appid_manager.report_out_of_quota(appid)
        # google_ip.report_connect_closed(response.ssl_sock.ip, "out of quota")
        response.worker.close("appid out of quota:%s" % appid)
        raise GAE_Exception(604, "appid out of quota:%s" % appid)

    if response.status > 300:
        raise GAE_Exception(605, "status:%d" % response.status)

    if response.status != 200:
        xlog.warn("GAE %s appid:%s status:%d", response.ssl_sock.ip, response.ssl_sock.appid, response.status)

    return response


def pack_request(method, url, headers, body):
    if isinstance(body, basestring) and body:
        if len(body) < 10 * 1024 * 1024 and 'Content-Encoding' not in headers:
            zbody = deflate(body)
            if len(zbody) < len(body):
                body = zbody
                headers['Content-Encoding'] = 'deflate'
        if len(body) > 10 * 1024 * 1024:
            xlog.warn("body len:%d %s %s", len(body), method, url)
        headers['Content-Length'] = str(len(body))

    # GAE don't allow set `Host` header
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
    #    xlog.debug("Send %s: %s", k, v)
    payload += ''.join('X-URLFETCH-%s: %s\r\n' % (k, v) for k, v in kwargs.items() if v)

    request_headers = {}
    payload = deflate(payload)

    body = '%s%s%s' % (struct.pack('!h', len(payload)), payload, body)
    request_headers['Content-Length'] = str(len(body))

    return request_headers, body


def unpack_response(response):

    try:
        data = response.body.get(2)

        headers_length, = struct.unpack('!h', data)
        data = response.body.get(headers_length)

        raw_response_line, headers_data = inflate(data).split('\r\n', 1)
        _, status, reason = raw_response_line.split(None, 2)
        response.app_status = int(status)
        response.app_reason = reason.strip()

        headers_block, app_msg = headers_data.split('\r\n\r\n')
        headers_pairs = headers_block.split('\r\n')
        response.headers = {}
        for pair in headers_pairs:
            if not pair:
                break
            k, v = pair.split(': ', 1)
            response.headers[k] = v

        response.app_msg = app_msg

        return response
    except Exception as e:
        response.worker.close("unpack protocol error")
        google_ip.recheck_ip(response.ssl_sock.ip)
        raise GAE_Exception("unpack protocol:%r", e)


def request_gae_proxy(method, url, headers, body):
    # make retry and time out
    time_request = time.time()
    request_headers, request_body = pack_request(method, url, headers, body)
    error_msg = []

    while True:
        if time.time() - time_request > 60: #time out
            raise GAE_Exception(600, b"".join(error_msg))

        try:
            response = request_gae_server(request_headers, request_body)

            check_local_network.report_network_ok()

            response = unpack_response(response)

            if response.app_msg:
                xlog.warn("server app return fail, status:%d", response.app_status)
                if len(response.app_msg) < 2048:
                    xlog.warn('app_msg:%s', cgi.escape(response.app_msg))

                if response.app_status == 510:
                    # reach 80% of traffic today
                    # disable for get big file.

                    appid_manager.report_out_of_quota(response.ssl_sock.appid)
                    response.worker.close("appid out of quota:%s" % response.ssl_sock.appid)
                    continue

            return response
        except GAE_Exception as e:
            err_msg = "gae_exception:%r %s" % (e, url)
            error_msg.append(err_msg)
            xlog.warn("gae_exception:%r %s", e, url)
        except Exception as e:
            err_msg = 'gae_handler.handler %r %s , retry...' % ( e, url)
            error_msg.append(err_msg)
            xlog.exception('gae_handler.handler %r %s , retry...', e, url)


def handler(method, url, headers, body, wfile):
    request_time = time.time()
    headers = clean_empty_header(headers)

    try:
        response = request_gae_proxy(method, url, headers, body)
    except GAE_Exception as e:
        xlog.warn("GAE %s %s request fail:%r", method, url, e)
        send_response(wfile, e.type, body=e.message)
        return return_fail_message(wfile)

    if response.app_msg:
        return send_response(wfile, response.app_status, body=response.app_msg)
    else:
        response.status = response.app_status

    if response.status == 206:
        return RangeFetch(method, url, headers, body, response, wfile).fetch()

    xlog.info("GAE t:%d s:%d %s %s", (time.time()-request_time)*1000, len(response.body), method, url)

    response_headers = {}
    for key, value in response.headers.items():
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

    try:
        wfile.write("HTTP/1.1 %d %s\r\n" % (response.status, response.reason))
        for key in response_headers:
            value = response_headers[key]
            send_header(wfile, key, value)
            #xlog.debug("Head- %s: %s", key, value)
        wfile.write("\r\n")
    except Exception as e:
        xlog.warn("gae_handler.handler send response fail. e:%r %s", e, url)
        return

    content_length = int(response.headers.get('Content-Length', 0))
    content_range = response.headers.get('Content-Range', '')
    if content_range:
        start, end, length = tuple(int(x) for x in re.search(r'bytes (\d+)-(\d+)/(\d+)', content_range).group(1, 2, 3))
    else:
        start, end, length = 0, content_length-1, content_length
    body_length = end - start + 1

    if body_length != len(response.body):
        xlog.warn("%s %s response.body len:%d, expect:%d", method, url, len(response.body), body_length)
        return

    try:
        data = response.body.get()
        ret = wfile.write(data)
        if ret == ssl.SSL_ERROR_WANT_WRITE or ret == ssl.SSL_ERROR_WANT_READ:
            xlog.debug("send to browser wfile.write ret:%d", ret)
            ret = wfile.write(data)
    except Exception as e_b:
        if e_b[0] in (errno.ECONNABORTED, errno.EPIPE, errno.ECONNRESET) or 'bad write retry' in repr(e_b):
            xlog.warn('gae_handler send to browser return %r %r', e_b, url)
        else:
            xlog.warn('gae_handler send to browser return %r %r', e_b, url)


class RangeFetch(object):
    threads = config.AUTORANGE_THREADS
    maxsize = config.AUTORANGE_MAXSIZE
    bufsize = config.AUTORANGE_BUFSIZE

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
        response_headers = dict((k.title(), v) for k, v in self.response.headers.items())
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
                #xlog.debug("Head %s: %s", key.title(), value)
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

        thread_num = min(self.threads, range_queue.qsize())
        for i in xrange(0, thread_num):
            range_delay_size = i * self.maxsize
            spawn_later(i*0.1, self.__fetchlet, range_queue, data_queue, range_delay_size)

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
                start, end, response = range_queue.get(timeout=1)
            except Queue.Empty:
                continue

            if start > self.expect_begin and data_queue.qsize() * self.bufsize + range_delay_size > 30*1024*1024:
                range_queue.put((start, end, response))
                time.sleep(2)
                continue
            headers['Range'] = 'bytes=%d-%d' % (start, end)

            if not response:
                try:
                    response = request_gae_proxy(self.method, self.url, headers, self.body)
                except GAE_Exception as e:
                    xlog.warning('RangeFetch %s return %r', headers['Range'], e)
                    range_queue.put((start, end, None))
                    continue

            if response.app_msg:
                response.worker.close("no range")
                range_queue.put((start, end, None))
                continue
            else:
                response.status = response.app_status

            if response.headers.get('Location', None):
                self.url = urlparse.urljoin(self.url, response.headers.get('Location'))
                xlog.warn('RangeFetch Redirect(%r)', self.url)
                # google_ip.report_connect_closed(response.ssl_sock.ip, "reLocation")
                range_queue.put((start, end, None))
                continue

            if response.status >= 300:
                xlog.error('RangeFetch %r return %s :%s', self.url, response.status, cgi.escape(response.body))
                response.worker.close("range status:%s", response.status)
                range_queue.put((start, end, None))
                continue

            content_range = response.headers.get('Content-Range', "")
            if not content_range:
                xlog.warning('RangeFetch "%s %s" return headers=%r, retry %s-%s',
                    self.method, self.url, response.headers, start, end)
                if len(response.body) < 2048:
                    xlog.warn('body:%s', cgi.escape(response.body))
                response.worker.close("no range")
                range_queue.put((start, end, None))
                continue

            content_length = int(response.headers.get('Content-Length', 0))
            xlog.info('>>>>>>>>>>>>>>> [thread %s] %s %s', threading.currentThread().ident, content_length, content_range)

            data = response.body.get()
            data_len = len(data)
            data_queue.put((start, data))
            start += data_len

            if start < end + 1:
                xlog.error('RangeFetch "%s %s" retry %s-%s', self.method, self.url, start, end)
                # google_ip.report_connect_closed(response.ssl_sock.ip, "down err")
                range_queue.put((start, end, None))
                continue

            xlog.info('>>>>>>>>>>>>>>> Successfully reached %d bytes.', start - 1)


