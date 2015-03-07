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
import random
import string
import threading
import socket
import ssl
import Queue
import BaseHTTPServer
import httplib
import urlparse


from cert_util import CertUtil
from connect_manager import https_manager,forwork_manager

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

class APPID_manager(object):
    def __init__(self):
        self.working_appid_list = config.GAE_APPIDS

    def get_appid(self):
        if len(self.working_appid_list) == 0:
            logging.error("No usable appid left, add new appid to continue use GoAgent")
            return None
        else:
            return random.choice(self.working_appid_list)

    def report_out_of_quota(self, appid):
        try:
            self.working_appid_list.remove(appid)
        except:
            pass
        if len(self.working_appid_list) == 0:
            self.working_appid_list = config.GAE_APPIDS

    def report_not_exist(self, appid):
        try:
            #logging.error("APPID_manager, report_not_exist %s", appid)
            config.GAE_APPIDS.remove(appid)
        except:
            pass

        self.report_out_of_quota(appid)

appid_manager = APPID_manager()


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
    request_data = 'POST /2? HTTP/1.1\r\n'
    request_data += ''.join('%s: %s\r\n' % (k, v) for k, v in headers.items() if k not in skip_headers)
    request_data += '\r\n'

    if isinstance(payload, bytes):
        sock.sendall(request_data.encode() + payload)
    elif hasattr(payload, 'read'):
        sock.sendall(request_data)
        while True:
            data = payload.read(bufsize)
            if not data:
                break
            sock.sendall(data)
    else:
        raise TypeError('_request(payload) must be a string or buffer, not %r' % type(payload))

    response = httplib.HTTPResponse(sock, buffering=True)
    try:
        response.begin()
    except httplib.BadStatusLine:
        response = None
    return response

# Caller:  gae_urlfetch
def request(payload=None, headers={}):
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
                    raise "no appid can use."
                headers['Host'] = ssl_sock.appid + ".appspot.com"
                ssl_sock.host = headers['Host']
            else:
                headers['Host'] = ssl_sock.host


            response = _request(ssl_sock, headers, payload)
            if response:
                response.ssl_sock = ssl_sock
            return response

        except Exception as e:
            logging.warn('request failed:%s', e)
            if ssl_sock:
                ssl_sock.close()
            if i == max_retry - 1:
                raise
            else:
                continue

def gae_urlfetch(method, url, headers, payload, **kwargs):

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

    if config.GAE_PASSWORD:
        kwargs['password'] = config.GAE_PASSWORD

    metadata = 'G-Method:%s\nG-Url:%s\n%s' % (method, url, ''.join('G-%s:%s\n' % (k, v) for k, v in kwargs.items() if v))
    metadata += ''.join('%s:%s\n' % (k.title(), v) for k, v in headers.items() if k not in skip_headers)

    # prepare GAE request
    request_headers = {}
    metadata = zlib.compress(metadata)[2:-4]
    payload = '%s%s%s' % (struct.pack('!h', len(metadata)), metadata, payload)
    request_headers['Content-Length'] = str(len(payload))

    response = request(payload, request_headers)

    if hasattr(response, "status"):
        response.app_status = response.status
    else:
        return response
    #logging.debug("request time:%d status:%d url:%s ", int(cost_time * 1000), response.status, url)

    response.app_options = response.getheader('X-GOA-Options', '')
    if response.status != 200:
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
        if data.startswith('ent 服务端已经在'):
            response.status = 501
            response.app_status = 501
        else:
            response.status = 502
        message = b'connection aborted. too short headers data=' + data
        response.fp = io.BytesIO(message)
        response.read = response.fp.read
        return response
    response.msg = httplib.HTTPMessage(io.BytesIO(zlib.decompress(data, -zlib.MAX_WBITS)))
    return response


class RangeFetch(object):

    maxsize = 1024*1024*4
    bufsize = 8192
    threads = 1
    waitsize = 1024*512
    expect_begin = 0

    def __init__(self, wfile, response, method, url, headers, payload, maxsize=0, bufsize=0, waitsize=0, threads=0):
        self.wfile = wfile
        self.response = response
        self.command = method
        self.url = url
        self.headers = headers
        self.payload = payload
        self.maxsize = maxsize or self.__class__.maxsize
        self.bufsize = bufsize or self.__class__.bufsize
        self.waitsize = waitsize or self.__class__.bufsize
        self.threads = threads or self.__class__.threads
        self._stopped = None

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
        #thread.start_new_thread(self.__fetchlet, (range_queue, data_queue, 0))
        p = threading.Thread(target=self.__fetchlet, args=(range_queue, data_queue, 0))
        p.daemon = True
        p.start()
        t0 = time.time()
        cur_threads = 1
        has_peek = hasattr(data_queue, 'peek')
        peek_timeout = 90
        self.expect_begin = start
        while self.expect_begin < length - 1:
            while cur_threads < self.threads and time.time() - t0 > cur_threads * config.AUTORANGE_MAXSIZE / 1048576:
                #thread.start_new_thread(self.__fetchlet, (range_queue, data_queue, cur_threads * config.AUTORANGE_MAXSIZE))
                p = threading.Thread(target=self.__fetchlet, args=(range_queue, data_queue, cur_threads * config.AUTORANGE_MAXSIZE))
                p.daemon = True
                p.start()
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
                    if not response:
                        response = gae_urlfetch(self.command, self.url, headers, self.payload)
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

    normcookie = functools.partial(re.compile(', ([^ =]+(?:=|$))').sub, '\\r\\nSet-Cookie: \\1')
    normattachment = functools.partial(re.compile(r'filename=(.+?)').sub, 'filename="\\1"')


    def setup(self):
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

        if host in config.HOSTS_MAP or host.endswith(config.HOSTS_POSTFIX_ENDSWITH):
            return self.wfile.write(('HTTP/1.1 301\r\nLocation: %s\r\n\r\n' % self.path.replace('http://', 'https://', 1)).encode())
        else:
            return self.do_AGENT()


    # Called by do_METHOD and do_CONNECT_AGENT
    def do_AGENT(self):
        """GAE http urlfetch"""
        request_headers = dict((k.title(), v) for k, v in self.headers.items())
        host = request_headers.get('Host', '')
        path = self.parsed_url.path
        range_in_query = 'range=' in self.parsed_url.query
        special_range = (any(x(host) for x in config.AUTORANGE_HOSTS_MATCH) or path.endswith(config.AUTORANGE_ENDSWITH)) and not path.endswith(config.AUTORANGE_NOENDSWITH)
        if 'Range' in request_headers:
            m = re.search(r'bytes=(\d+)-', request_headers['Range'])
            start = int(m.group(1) if m else 0)
            request_headers['Range'] = 'bytes=%d-%d' % (start, start+config.AUTORANGE_MAXSIZE-1)
            logging.info('autorange range=%r match url=%r', request_headers['Range'], self.path)
        elif not range_in_query and special_range:
            logging.info('Found [autorange]endswith match url=%r', self.path)
            m = re.search(r'bytes=(\d+)-', request_headers.get('Range', ''))
            start = int(m.group(1) if m else 0)
            request_headers['Range'] = 'bytes=%d-%d' % (start, start+config.AUTORANGE_MAXSIZE-1)

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


        for retry in range(config.FETCHMAX_LOCAL):
            try:
                content_length = 0
                kwargs = {}

                # TODO: test validate = 1
                kwargs['validate'] = 0

                time_start = time.time()
                response = gae_urlfetch(self.command, self.path, request_headers, payload, **kwargs)
                time_stop = time.time()
                time_cost = int((time_stop - time_start) * 1000)
                if not response:
                    if retry >= config.FETCHMAX_LOCAL-1:
                        html = generate_message_html('502 URLFetch failed', 'Local URLFetch %r failed' % self.path, str(errors))
                        self.wfile.write(b'HTTP/1.0 502\r\nContent-Type: text/html\r\n\r\n' + html.encode('utf-8'))
                        logging.warning('GET no response %s ', self.path)
                        return
                    else:
                        continue

                # appid not exists, try remove it from appid
                if response.app_status == 404:
                    logging.warning('APPID %r not exists, remove it.', response.ssl_sock.appid)
                    appid_manager.report_not_exist(response.ssl_sock.appid)
                    appid = appid_manager.get_appid()

                    if not appid:
                        html = generate_message_html('404 No usable Appid Exists', 'No usable Appid Exists, please add appid')
                        self.wfile.write(b'HTTP/1.0 502\r\nContent-Type: text/html\r\n\r\n' + html.encode('utf-8'))
                        response.close()
                        return
                    else:
                        continue

                # appid over qouta, switch to next appid
                if response.app_status == 503:
                    logging.warning('APPID %r out of Quota, remove it.', response.ssl_sock.appid)
                    appid_manager.report_out_of_quota(response.ssl_sock.appid)
                    appid = appid_manager.get_appid()

                    if not appid:
                        html = generate_message_html('404 No usable Appid Exists', 'No usable Appid Exists, please add appid')
                        self.wfile.write(b'HTTP/1.0 502\r\nContent-Type: text/html\r\n\r\n' + html.encode('utf-8'))
                        response.close()
                        return
                    else:
                        continue

                # 500 is Web server internal err
                if response.app_status == 500 and range_in_query and special_range:

                    logging.warning('500 with range in query') #, need trying another APPID?
                    response.close()
                    continue

                if response.app_status == 501:
                    deploy_url = "http://127.0.0.1:8085/?module=goagent&menu=deploy"
                    message = u'请重新部署服务端: <a href="%s">%s</a>' % (deploy_url, deploy_url)
                    html = generate_message_html('Please deploy new server', message)
                    self.wfile.write(b'HTTP/1.0 501\r\nContent-Type: text/html\r\n\r\n' + html.encode('utf-8'))
                    response.close()
                    return

                if response.app_status != 200 and retry == config.FETCHMAX_LOCAL-1:
                    logging.info('GAE %s %s status:%s', self.command, self.path, response.status)
                    self.wfile.write(('HTTP/1.1 %s\r\n%s\r\n' % (response.status, ''.join('%s: %s\r\n' % (k.title(), v) for k, v in response.getheaders() if k.title() != 'Transfer-Encoding'))))
                    self.wfile.write(response.read())
                    response.close()
                    return

                # first response, has no retry.
                if not headers_sent:
                    data_size = response.getheader('Content-Length', '0')
                    download_speed = int(data_size) * 1000 / time_cost
                    logging.info('"GAE t:%d speed:%d len:%s status:%s %s %s HTTP/1.1"', time_cost, download_speed, response.getheader('Content-Length', '-'), response.status, self.command, self.path)
                    if response.status == 206:
                        # 206 means "Partial Content"
                        rangefetch = RangeFetch(self.wfile, response, self.command, self.path, self.headers, payload, maxsize=config.AUTORANGE_MAXSIZE, bufsize=config.AUTORANGE_BUFSIZE, waitsize=config.AUTORANGE_WAITSIZE, threads=config.AUTORANGE_THREADS)
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

                while True:
                    data = response.read(8192)
                    if not data:
                        response.close()
                        return
                    start += len(data)
                    self.wfile.write(data)
                    if start >= end:
                        https_manager.save_ssl_connection_for_reuse(response.ssl_sock) #, response.connection_cache_key)
                        #response.close()
                        return
            except Exception as e:
                errors.append(e)
                if response:
                    response.close()
                if e.args[0] in (errno.ECONNABORTED, errno.EPIPE, errno.ECONNRESET):
                    #logging.debug('GAEProxyHandler.do_METHOD_AGENT return %r', e)
                    pass
                elif e.args[0] == errno.ETIMEDOUT or isinstance(e.args[0], str) and 'timed out' in e.args[0]:
                    if content_length and accept_ranges == 'bytes':
                        # we can retry range fetch here
                        logging.warn('GAEProxyHandler.do_METHOD_AGENT timed out, content_length=%r, url=%r, try again', content_length, self.path)
                        self.headers['Range'] = 'bytes=%d-%d' % (start, end)
                elif isinstance(e, NetWorkIOError) and 'bad write retry' in e.args[-1]:
                    logging.warn('GAEProxyHandler.do_METHOD_AGENT return %r, abort. url=%r ', e, self.path)
                    return
                else:
                    logging.exception('GAEProxyHandler.do_METHOD_AGENT %r return %r', self.path, e) #IOError(9, 'Bad file descriptor'), int(e.args[0])
                    #traceback.print_exc()

    def do_CONNECT(self):
        """handle CONNECT cmmand, socket forward or deploy a fake cert"""
        host, _, port = self.path.rpartition(':')


        if host in config.HOSTS_MAP or host.endswith(config.HOSTS_POSTFIX_ENDSWITH):
            return self.do_CONNECT_FWD()
        else:
            return self.do_CONNECT_AGENT()

    def do_CONNECT_FWD(self):
        """socket forward for http CONNECT command"""
        host, _, port = self.path.rpartition(':')
        port = int(port)
        logging.info('FWD %s %s:%d ', self.command, host, port)
        if host == "appengine.google.com" or host == "www.google.com":
            connected_in_s = 5 # goagent upload to appengine is slow, it need more 'fresh' connection.
        else:
            connected_in_s = 10  # gws connect can be used after tcp connection created 15 s


        try:
            self.wfile.write(b'HTTP/1.1 200 OK\r\n\r\n')
            data = self.connection.recv(1024)
        except Exception as e:
            logging.exception('do_CONNECT_FWD (%r, %r) Exception:%s', host, port, e)
            self.connection.close()
            return

        remote = forwork_manager.create_connection(port=port, sock_life=connected_in_s)
        if remote is None:
            self.connection.close()
            logging.warn('FWD %s %s:%d create_connection fail', self.command, host, port)
            return

        try:
            if data:
                remote.send(data)
        except Exception as e:
            logging.exception('do_CONNECT_FWD (%r, %r) Exception:%s', host, port, e)
            self.connection.close()
            remote.close()
            return

        # reset timeout default to avoid long http upload failure, but it will delay timeout retry :(
        remote.settimeout(None)

        forwork_manager.forward_socket(self.connection, remote, bufsize=self.bufsize)
        logging.debug('FWD %s %s:%d closed', self.command, host, port)

    def do_CONNECT_AGENT(self):
        """deploy fake cert to client"""
        host, _, port = self.path.rpartition(':')
        port = int(port)
        certfile = CertUtil.get_cert(host)
        logging.info('GAE %s %s:%d ', self.command, host, port)
        self.__realconnection = None
        self.wfile.write(b'HTTP/1.1 200 OK\r\n\r\n')

        try:
            ssl_sock = ssl.wrap_socket(self.connection, keyfile=certfile, certfile=certfile, server_side=True)
        except ssl.SSLError as e:
            logging.info('ssl error: %s, create full domain cert for host:%s', e, host)
            certfile = CertUtil.get_cert(host, full_name=True)
            return
        except Exception as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET):
                logging.exception('ssl.wrap_socket(self.connection=%r) failed: %s path:%s, errno:%s', self.connection, e, self.path, e.args[0])
            return

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
            if self.path[0] == '/' and host:
                self.path = 'http://%s%s' % (host, self.path)
            elif not host and '://' in self.path:
                host = urlparse.urlparse(self.path).netloc

            self.parsed_url = urlparse.urlparse(self.path)

            return self.do_AGENT()


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

