#!/usr/bin/env python
# coding:utf-8

import sys
import os
import glob

import errno
import time
import struct
import collections
import zlib
import functools
import re
import io
import logging
import random
import string
import threading
import thread
import socket
import ssl
import Queue
import BaseHTTPServer
import httplib
import urlparse

from cert_util import CertUtil
from http_util import HTTPUtil


current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, os.pardir, 'python27', '1.0'))
if sys.platform == "win32":
    win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
    sys.path.append(win32_lib)
elif sys.platform == "linux" or sys.platform == "linux2":
    win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'linux'))
    sys.path.append(win32_lib)

import OpenSSL
NetWorkIOError = (socket.error, ssl.SSLError, OpenSSL.SSL.Error, OSError)


from common import Common
common = Common()

http_util = HTTPUtil()


def message_html(title, banner, detail=''):
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




def gae_urlfetch(method, url, headers, payload, fetchserver, **kwargs):
    # deflate = lambda x:zlib.compress(x)[2:-4]
    if payload:
        if len(payload) < 10 * 1024 * 1024 and 'Content-Encoding' not in headers:
            zpayload = zlib.compress(payload)[2:-4]
            if len(zpayload) < len(payload):
                payload = zpayload
                headers['Content-Encoding'] = 'deflate'
        headers['Content-Length'] = str(len(payload))
    # GAE donot allow set `Host` header
    if 'Host' in headers:
        del headers['Host']
    metadata = 'G-Method:%s\nG-Url:%s\n%s' % (method, url, ''.join('G-%s:%s\n' % (k, v) for k, v in kwargs.items() if v))
    skip_headers = http_util.skip_headers
    metadata += ''.join('%s:%s\n' % (k.title(), v) for k, v in headers.items() if k not in skip_headers)
    # prepare GAE request
    request_method = 'POST'
    request_headers = {}
    metadata = zlib.compress(metadata)[2:-4]
    payload = '%s%s%s' % (struct.pack('!h', len(metadata)), metadata, payload)
    request_headers['Content-Length'] = str(len(payload))

    # post data
    need_crlf = 0
    connection_cache_key = '%s:%d' % (common.HOSTS_POSTFIX_MAP['.appspot.com'], 443)
    response = http_util.request(request_method, fetchserver, payload, request_headers, crlf=need_crlf, connection_cache_key=connection_cache_key)
    if hasattr(response, "status"):
        response.app_status = response.status
    else:
        return response
    response.app_options = response.getheader('X-GOA-Options', '')
    if response.status != 200:
        if response.status in (400, 405):
            # filter by some firewall
            common.GAE_CRLF = 0
        return response
    data = response.read(4)
    if len(data) < 4:
        response.status = 502
        response.fp = io.BytesIO(b'connection aborted. too short leadtype data=' + data)
        response.read = response.fp.read
        return response
    response.status, headers_length = struct.unpack('!hh', data)
    data = response.read(headers_length)
    if len(data) < headers_length:
        response.status = 502
        response.fp = io.BytesIO(b'connection aborted. too short headers data=' + data)
        response.read = response.fp.read
        return response
    response.msg = httplib.HTTPMessage(io.BytesIO(zlib.decompress(data, -zlib.MAX_WBITS)))
    return response


class RangeFetch(object):
    """Range Fetch Class"""

    maxsize = 1024*1024*4
    bufsize = 8192
    threads = 1
    waitsize = 1024*512
    urlfetch = staticmethod(gae_urlfetch)
    expect_begin = 0

    def __init__(self, wfile, response, method, url, headers, payload, fetchservers, password, maxsize=0, bufsize=0, waitsize=0, threads=0):
        self.wfile = wfile
        self.response = response
        self.command = method
        self.url = url
        self.headers = headers
        self.payload = payload
        self.fetchservers = fetchservers
        self.password = password
        self.maxsize = maxsize or self.__class__.maxsize
        self.bufsize = bufsize or self.__class__.bufsize
        self.waitsize = waitsize or self.__class__.bufsize
        self.threads = threads or self.__class__.threads
        self._stopped = None
        self._last_app_status = {}

    def fetch(self):
        response_status = self.response.status
        response_headers = dict((k.title(), v) for k, v in self.response.getheaders())
        content_range = response_headers['Content-Range']
        #content_length = response_headers['Content-Length']
        start, end, length = tuple(int(x) for x in re.search(r'bytes (\d+)-(\d+)/(\d+)', content_range).group(1, 2, 3))
        if start == 0:
            response_status = 200
            response_headers['Content-Length'] = str(length)
            del response_headers['Content-Range']
        else:
            response_headers['Content-Range'] = 'bytes %s-%s/%s' % (start, end, length)
            response_headers['Content-Length'] = str(length-start)

        logging.info('>>>>>>>>>>>>>>> RangeFetch started(%r) %d-%d', self.url, start, end)
        self.wfile.write(('HTTP/1.1 %s\r\n%s\r\n' % (response_status, ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items()))))

        data_queue = Queue.PriorityQueue()
        range_queue = Queue.PriorityQueue()
        range_queue.put((start, end, self.response))
        for begin in range(end+1, length, self.maxsize):
            range_queue.put((begin, min(begin+self.maxsize-1, length-1), None))
        thread.start_new_thread(self.__fetchlet, (range_queue, data_queue, 0))
        t0 = time.time()
        cur_threads = 1
        has_peek = hasattr(data_queue, 'peek')
        peek_timeout = 90
        self.expect_begin = start
        while self.expect_begin < length - 1:
            while cur_threads < self.threads and time.time() - t0 > cur_threads * common.AUTORANGE_MAXSIZE / 1048576:
                thread.start_new_thread(self.__fetchlet, (range_queue, data_queue, cur_threads * common.AUTORANGE_MAXSIZE))
                cur_threads += 1
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
            except Exception as e:
                logging.info('RangeFetch client connection aborted(%s).', e)
                break
        self._stopped = True

    def __fetchlet(self, range_queue, data_queue, range_delay_size):
        headers = dict((k.title(), v) for k, v in self.headers.items())
        headers['Connection'] = 'close'
        while 1:
            try:
                if self._stopped:
                    return
                try:
                    start, end, response = range_queue.get(timeout=1)
                    if self.expect_begin < start and data_queue.qsize() * self.bufsize + range_delay_size > 30*1024*1024:
                        range_queue.put((start, end, response))
                        time.sleep(10)
                        continue
                    headers['Range'] = 'bytes=%d-%d' % (start, end)
                    fetchserver = ''
                    if not response:
                        fetchserver = random.choice(self.fetchservers)
                        if self._last_app_status.get(fetchserver, 200) >= 500:
                            time.sleep(5)
                        response = self.urlfetch(self.command, self.url, headers, self.payload, fetchserver, password=self.password)
                except Queue.Empty:
                    continue
                except Exception as e:
                    logging.warning("Response %r in __fetchlet", e)
                    range_queue.put((start, end, None))
                    continue
                if not response:
                    logging.warning('RangeFetch %s return %r', headers['Range'], response)
                    range_queue.put((start, end, None))
                    continue
                if fetchserver:
                    self._last_app_status[fetchserver] = response.app_status
                if response.app_status != 200:
                    logging.warning('Range Fetch "%s %s" %s return %s', self.command, self.url, headers['Range'], response.app_status)
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
                        logging.warning('RangeFetch "%s %s" return Content-Range=%r: response headers=%r', self.command, self.url, content_range, response.getheaders())
                        response.close()
                        range_queue.put((start, end, None))
                        continue
                    content_length = int(response.getheader('Content-Length', 0))
                    logging.info('>>>>>>>>>>>>>>> [thread %s] %s %s', threading.currentThread().ident, content_length, content_range)
                    while 1:
                        try:
                            if self._stopped:
                                response.close()
                                return
                            data = response.read(self.bufsize)
                            if not data:
                                break
                            data_queue.put((start, data))
                            start += len(data)
                        except Exception as e:
                            logging.warning('RangeFetch "%s %s" %s failed: %s', self.command, self.url, headers['Range'], e)
                            break
                    if start < end + 1:
                        logging.warning('RangeFetch "%s %s" retry %s-%s', self.command, self.url, start, end)
                        response.close()
                        range_queue.put((start, end, None))
                        continue
                    logging.info('>>>>>>>>>>>>>>> Successfully reached %d bytes.', start - 1)
                else:
                    logging.error('RangeFetch %r return %s', self.url, response.status)
                    response.close()
                    range_queue.put((start, end, None))
                    continue
            except Exception as e:
                logging.exception('RangeFetch._fetchlet error:%s', e)
                raise




class GAEProxyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    bufsize = 256*1024
    first_run_lock = threading.Lock()
    urlfetch = staticmethod(gae_urlfetch)
    normcookie = functools.partial(re.compile(', ([^ =]+(?:=|$))').sub, '\\r\\nSet-Cookie: \\1')
    normattachment = functools.partial(re.compile(r'filename=(.+?)').sub, 'filename="\\1"')

    def first_run(self):
        """GAEProxyHandler setup, init domain/iplist map"""
        for appid in common.GAE_APPIDS:
            host = '%s.appspot.com' % appid
            if host not in common.HOSTS_MAP:
                common.HOSTS_MAP[host] = common.HOSTS_POSTFIX_MAP['.appspot.com']

    def setup(self):
        if isinstance(self.__class__.first_run, collections.Callable):
            try:
                with self.__class__.first_run_lock:
                    if isinstance(self.__class__.first_run, collections.Callable):
                        self.first_run()
                        self.__class__.first_run = None
            except Exception as e:
                logging.exception('GAEProxyHandler.first_run() return %r', e)
        self.__class__.setup = BaseHTTPServer.BaseHTTPRequestHandler.setup
        self.__class__.do_GET = self.__class__.do_METHOD
        self.__class__.do_PUT = self.__class__.do_METHOD
        self.__class__.do_POST = self.__class__.do_METHOD
        self.__class__.do_HEAD = self.__class__.do_METHOD
        self.__class__.do_DELETE = self.__class__.do_METHOD
        self.__class__.do_OPTIONS = self.__class__.do_METHOD
        self.setup()

    def finish(self):
        """make python2 BaseHTTPRequestHandler happy"""
        try:
            BaseHTTPServer.BaseHTTPRequestHandler.finish(self)
        except NetWorkIOError as e:
            if e[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.EPIPE):
                raise

    def address_string(self):
        return '%s:%s' % self.client_address[:2]

    def do_METHOD(self):

        host = self.headers.get('Host', '')


        if self.path[0] == '/' and host:
            self.path = 'http://%s%s' % (host, self.path)
        elif not host and '://' in self.path:
            host = urlparse.urlparse(self.path).netloc

        self.parsed_url = urlparse.urlparse(self.path)

        #if not hasattr(self.connection, "_sslobj") and host in common.HTTP_FORCEHTTPS:
        #    return self.wfile.write(('HTTP/1.1 301\r\nLocation: %s\r\n\r\n' % self.path.replace('http://', 'https://', 1)).encode())
        if self.command not in ('GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'PATCH'):
            return self.do_METHOD_FWD()
        if any(x(self.path) for x in common.METHOD_REMATCH_MAP) or host in common.HOSTS_MAP or host.endswith(common.HOSTS_POSTFIX_ENDSWITH):
            if hasattr(self.connection, "_sslobj"):
                return self.do_METHOD_FWD()
            else:
                return self.wfile.write(('HTTP/1.1 301\r\nLocation: %s\r\n\r\n' % self.path.replace('http://', 'https://', 1)).encode())
        else:
            return self.do_METHOD_AGENT()

    def do_METHOD_FWD(self):
        """Direct http forward"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            payload = self.rfile.read(content_length) if content_length else b''
            host = self.parsed_url.netloc
            if any(x(self.path) for x in common.METHOD_REMATCH_MAP):
                hostname = next(common.METHOD_REMATCH_MAP[x] for x in common.METHOD_REMATCH_MAP if x(self.path))
            elif host in common.HOSTS_MAP:
                hostname = common.HOSTS_MAP[host]
            elif host.endswith(common.HOSTS_POSTFIX_ENDSWITH):
                hostname = next(common.HOSTS_POSTFIX_MAP[x] for x in common.HOSTS_POSTFIX_MAP if host.endswith(x))
                common.HOSTS_MAP[host] = hostname
            else:
                hostname = host
            hostname = hostname or host

            connection_cache_key = hostname
            response = http_util.request(self.command, self.path, payload, self.headers, connection_cache_key=connection_cache_key)
            if not response:
                return
            logging.info('FWD %s %s HTTP/1.1 %s %s', self.command, self.path, response.status, response.getheader('Content-Length', '-'))
            if response.status in (400, 405):
                common.GAE_CRLF = 0
            self.wfile.write(('HTTP/1.1 %s\r\n%s\r\n' % (response.status, ''.join('%s: %s\r\n' % (k.title(), v) for k, v in response.getheaders() if k.title() != 'Transfer-Encoding'))))
            while 1:
                data = response.read(8192)
                if not data:
                    break
                self.wfile.write(data)
            response.close()
        except NetWorkIOError as e:
            if e.args[0] in (errno.ECONNRESET, 10063, errno.ENAMETOOLONG):
                #logging.warn('http_util.request "%s %s" failed:%s, try addto `withgae`', self.command, self.path, e)
                #common.HTTP_WITHGAE = tuple(list(common.HTTP_WITHGAE)+[re.sub(r':\d+$', '', self.parsed_url.netloc)])
                pass
            elif e.args[0] not in (errno.ECONNABORTED, errno.EPIPE):
                raise
        except Exception as e:
            host = self.headers.get('Host', '')
            logging.warn('GAEProxyHandler direct(%s) Error', host)
            raise

    def do_METHOD_AGENT(self):
        """GAE http urlfetch"""
        request_headers = dict((k.title(), v) for k, v in self.headers.items())
        host = request_headers.get('Host', '')
        path = self.parsed_url.path
        range_in_query = 'range=' in self.parsed_url.query
        special_range = (any(x(host) for x in common.AUTORANGE_HOSTS_MATCH) or path.endswith(common.AUTORANGE_ENDSWITH)) and not path.endswith(common.AUTORANGE_NOENDSWITH)
        if 'Range' in request_headers:
            m = re.search(r'bytes=(\d+)-', request_headers['Range'])
            start = int(m.group(1) if m else 0)
            request_headers['Range'] = 'bytes=%d-%d' % (start, start+common.AUTORANGE_MAXSIZE-1)
            logging.info('autorange range=%r match url=%r', request_headers['Range'], self.path)
        elif not range_in_query and special_range:
            logging.info('Found [autorange]endswith match url=%r', self.path)
            m = re.search(r'bytes=(\d+)-', request_headers.get('Range', ''))
            start = int(m.group(1) if m else 0)
            request_headers['Range'] = 'bytes=%d-%d' % (start, start+common.AUTORANGE_MAXSIZE-1)

        payload = b''
        if 'Content-Length' in request_headers:
            try:
                payload = self.rfile.read(int(request_headers.get('Content-Length', 0)))
            except NetWorkIOError as e:
                logging.error('handle_method_urlfetch read payload failed:%s', e)
                return
        response = None
        errors = []
        headers_sent = False
        fetchserver = common.GAE_FETCHSERVER
        if range_in_query and special_range:
            fetchserver = re.sub(r'//[\w-]+\.appspot\.com', '//%s.appspot.com' % random.choice(common.GAE_APPIDS), fetchserver)
        for retry in range(common.FETCHMAX_LOCAL):
            try:
                content_length = 0
                kwargs = {}
                if common.GAE_PASSWORD:
                    kwargs['password'] = common.GAE_PASSWORD
                #if common.GAE_VALIDATE:
                kwargs['validate'] = 0
                response = self.urlfetch(self.command, self.path, request_headers, payload, fetchserver, **kwargs)
                if not response:
                    if retry >= common.FETCHMAX_LOCAL-1:
                        html = message_html('502 URLFetch failed', 'Local URLFetch %r failed' % self.path, str(errors))
                        self.wfile.write(b'HTTP/1.0 502\r\nContent-Type: text/html\r\n\r\n' + html.encode('utf-8'))
                        logging.warning('GET %s no response', self.path)
                        return
                    else:
                        continue
                # appid not exists, try remove it from appid
                if response.app_status == 404:
                    if len(common.GAE_APPIDS) > 1:
                        appid = common.GAE_APPIDS.pop(0)
                        common.GAE_FETCHSERVER = '%s://%s.appspot.com%s?' % (common.GAE_MODE, common.GAE_APPIDS[0], common.GAE_PATH)
                        logging.warning('APPID %r not exists, remove it.', appid)
                        continue
                    else:
                        appid = common.GAE_APPIDS[0]
                        logging.error('APPID %r not exists, please ensure your appid in proxy.ini.', appid)
                        html = message_html('404 Appid Not Exists', 'Appid %r Not Exists' % appid, 'appid %r not exist, please edit your proxy.ini' % appid)
                        self.wfile.write(b'HTTP/1.0 502\r\nContent-Type: text/html\r\n\r\n' + html.encode('utf-8'))
                        return
                # appid over qouta, switch to next appid
                if response.app_status == 503:
                    if len(common.GAE_APPIDS) > 1:
                        common.GAE_APPIDS.pop(0)
                        common.GAE_FETCHSERVER = '%s://%s.appspot.com%s?' % (common.GAE_MODE, common.GAE_APPIDS[0], common.GAE_PATH)
                        logging.info('Current APPID Over Quota,Auto Switch to [%s], Retrying…' % (common.GAE_APPIDS[0]))
                        continue
                    else:
                        logging.error('All APPID Over Quota')
                        break
                # bad request, disable CRLF injection
                if response.app_status in (400, 405):
                    http_util.crlf = 0
                    continue
                if response.app_status == 500 and range_in_query and special_range:
                    fetchserver = re.sub(r'//[\w-]+\.appspot\.com', '//%s.appspot.com' % random.choice(common.GAE_APPIDS), fetchserver)
                    logging.warning('500 with range in query, trying another APPID')
                    # logging.warning('Temporary fetchserver: %s -> %s' % (common.GAE_FETCHSERVER, fetchserver))
                    # retry -= 1
                    # logging.warning('retry: %s' % retry)
                    continue
                if response.app_status != 200 and retry == common.FETCHMAX_LOCAL-1:
                    logging.info('GAE %s %s status:%s', self.command, self.path, response.status)
                    self.wfile.write(('HTTP/1.1 %s\r\n%s\r\n' % (response.status, ''.join('%s: %s\r\n' % (k.title(), v) for k, v in response.getheaders() if k.title() != 'Transfer-Encoding'))))
                    self.wfile.write(response.read())
                    response.close()
                    return
                # first response, has no retry.
                if not headers_sent:
                    logging.info('"GAE %s %s HTTP/1.1" status:%s len:%s', self.command, self.path, response.status, response.getheader('Content-Length', '-'))
                    if response.status == 206:
                        fetchservers = [re.sub(r'//[\w-]+\.appspot\.com', '//%s.appspot.com' % appid, common.GAE_FETCHSERVER) for appid in common.GAE_APPIDS]
                        rangefetch = RangeFetch(self.wfile, response, self.command, self.path, self.headers, payload, fetchservers, common.GAE_PASSWORD, maxsize=common.AUTORANGE_MAXSIZE, bufsize=common.AUTORANGE_BUFSIZE, waitsize=common.AUTORANGE_WAITSIZE, threads=common.AUTORANGE_THREADS)
                        return rangefetch.fetch()
                    if response.getheader('Set-Cookie'):
                        response.msg['Set-Cookie'] = self.normcookie(response.getheader('Set-Cookie'))
                    if response.getheader('Content-Disposition') and '"' not in response.getheader('Content-Disposition'):
                        response.msg['Content-Disposition'] = self.normattachment(response.getheader('Content-Disposition'))
                    headers_data = 'HTTP/1.1 %s\r\n%s\r\n' % (response.status, ''.join('%s: %s\r\n' % (k.title(), v) for k, v in response.getheaders() if k.title() != 'Transfer-Encoding'))
                    #logging.debug('headers_data=%s', headers_data)
                    #self.wfile.write(headers_data.encode() if bytes is not str else headers_data)
                    self.wfile.write(headers_data)
                    headers_sent = True
                content_length = int(response.getheader('Content-Length', 0))
                content_range = response.getheader('Content-Range', '')
                accept_ranges = response.getheader('Accept-Ranges', 'none')
                if content_range:
                    start, end, length = tuple(int(x) for x in re.search(r'bytes (\d+)-(\d+)/(\d+)', content_range).group(1, 2, 3))
                else:
                    start, end, length = 0, content_length-1, content_length
                while 1:
                    data = response.read(8192)
                    if not data:
                        response.close()
                        return
                    start += len(data)
                    self.wfile.write(data)
                    if start >= end:
                        response.close()
                        return
            except Exception as e:
                errors.append(e)
                if response:
                    response.close()
                if e.args[0] in (errno.ECONNABORTED, errno.EPIPE):
                    #logging.debug('GAEProxyHandler.do_METHOD_AGENT return %r', e)
                    pass
                elif e.args[0] in (errno.ECONNRESET, errno.ETIMEDOUT, errno.ENETUNREACH, 11004):
                    # connection reset or timeout, switch to https
                    common.GAE_MODE = 'https'
                    common.GAE_FETCHSERVER = '%s://%s.appspot.com%s?' % (common.GAE_MODE, common.GAE_APPIDS[0], common.GAE_PATH)
                elif e.args[0] == errno.ETIMEDOUT or isinstance(e.args[0], str) and 'timed out' in e.args[0]:
                    if content_length and accept_ranges == 'bytes':
                        # we can retry range fetch here
                        logging.warn('GAEProxyHandler.do_METHOD_AGENT timed out, url=%r, content_length=%r, try again', self.path, content_length)
                        self.headers['Range'] = 'bytes=%d-%d' % (start, end)
                elif isinstance(e, NetWorkIOError) and 'bad write retry' in e.args[-1]:
                    logging.info('GAEProxyHandler.do_METHOD_AGENT url=%r return %r, abort.', self.path, e)
                    return
                else:
                    logging.exception('GAEProxyHandler.do_METHOD_AGENT %r return %r, try again', self.path, e)

    def do_CONNECT(self):
        """handle CONNECT cmmand, socket forward or deploy a fake cert"""
        host, _, port = self.path.rpartition(':')

        if False and host.endswith('.googlevideo.com'): #test only.
            return self.do_CONNECT_FWD()

        if self.path in common.CONNECT_HOSTS_MAP or self.path.endswith(common.CONNECT_POSTFIX_ENDSWITH):
            return self.do_CONNECT_FWD()
        elif host in common.HOSTS_MAP or host.endswith(common.HOSTS_POSTFIX_ENDSWITH):
            return self.do_CONNECT_FWD()
        else:
            return self.do_CONNECT_AGENT()

    def do_CONNECT_FWD(self):
        """socket forward for http CONNECT command"""
        host, _, port = self.path.rpartition(':')
        port = int(port)
        logging.info('FWD %s %s:%d ', self.command, host, port)
        #http_headers = ''.join('%s: %s\r\n' % (k, v) for k, v in self.headers.items())

        self.wfile.write(b'HTTP/1.1 200 OK\r\n\r\n')
        data = self.connection.recv(1024)
        for i in range(5):
            try:
                if self.path in common.CONNECT_HOSTS_MAP:
                    hostname = common.CONNECT_HOSTS_MAP[self.path]
                elif self.path.endswith(common.CONNECT_POSTFIX_ENDSWITH):
                    hostname = next(common.CONNECT_POSTFIX_MAP[x] for x in common.CONNECT_POSTFIX_MAP if self.path.endswith(x))
                    common.CONNECT_HOSTS_MAP[self.path] = hostname
                elif host in common.HOSTS_MAP:
                    hostname = common.HOSTS_MAP[host]
                elif host.endswith(common.HOSTS_POSTFIX_ENDSWITH):
                    hostname = next(common.HOSTS_POSTFIX_MAP[x] for x in common.HOSTS_POSTFIX_MAP if host.endswith(x))
                    common.HOSTS_MAP[host] = hostname
                else:
                    hostname = host
                hostname = hostname or host

                if host == 'appengine.google.com' or host == 'www.google.com':
                    connection_cache_key = None
                    # for some reason, appengine can't reuse https connection for upload app to gae
                else:
                    connection_cache_key = '%s:%d' % (hostname or host, port)
                timeout = 4
                remote = http_util.create_connection((host, port), timeout, cache_key=connection_cache_key)
                if remote is not None and data:
                    remote.sendall(data)
                    break
                elif i == 0:
                    # only logging first create_connection error
                    logging.error('http_util.create_connection((host=%r, port=%r), %r) timeout', host, port, timeout)
            except NetWorkIOError as e:
                if e.args[0] == 9:
                    logging.error('GAEProxyHandler direct forward remote (%r, %r) failed', host, port)
                    continue
                else:
                    raise
        if hasattr(remote, 'fileno'):
            # reset timeout default to avoid long http upload failure, but it will delay timeout retry :(
            remote.settimeout(None)
            http_util.forward_socket(self.connection, remote, bufsize=self.bufsize)


    def do_CONNECT_AGENT(self):
        """deploy fake cert to client"""
        host, _, port = self.path.rpartition(':')
        port = int(port)
        certfile = CertUtil.get_cert(host)
        logging.info('CONNECT_AGENT %s %s:%d ', self.command, host, port)
        self.__realconnection = None
        self.wfile.write(b'HTTP/1.1 200 OK\r\n\r\n')
        try:
            ssl_sock = ssl.wrap_socket(self.connection, keyfile=certfile, certfile=certfile, server_side=True, ssl_version=ssl.PROTOCOL_TLSv1)
        except Exception as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET):
                logging.exception('ssl.wrap_socket(self.connection=%r) failed: %s path:%s', self.connection, e, self.path)
            return
        except ssl.SSLError as e:
            logging.info('ssl error: %s', e)

        self.__realconnection = self.connection
        self.__realwfile = self.wfile
        self.__realrfile = self.rfile
        self.connection = ssl_sock
        self.rfile = self.connection.makefile('rb', self.bufsize)
        self.wfile = self.connection.makefile('wb', 0)
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(414)
                return
            if not self.raw_requestline:
                self.close_connection = 1
                return
            if not self.parse_request():
                return
        except NetWorkIOError as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.EPIPE):
                raise
        if self.path[0] == '/' and host:
            self.path = 'https://%s%s' % (self.headers['Host'], self.path)
        logging.debug('GAE CONNECT %s %s', self.command, self.path)

        try:
            self.do_METHOD()
        except NetWorkIOError as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ETIMEDOUT, errno.EPIPE):
                raise
        finally:
            if self.__realconnection:
                try:
                    self.__realconnection.shutdown(socket.SHUT_WR)
                    self.__realconnection.close()
                except NetWorkIOError:
                    pass
                finally:
                    self.__realconnection = None


