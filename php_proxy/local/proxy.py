#!/usr/bin/env python
# coding:utf-8
# Based on GAppProxy 2.0.0 by Du XiaoGang <dugang.2008@gmail.com>
# Based on WallProxy 0.4.0 by Hust Moon <www.ehust@gmail.com>
# Contributor:
#      Phus Lu           <phus.lu@gmail.com>
#      Hewig Xu          <hewigovens@gmail.com>
#      Ayanamist Yang    <ayanamist@gmail.com>
#      V.E.O             <V.E.O@tom.com>
#      Max Lv            <max.c.lv@gmail.com>
#      AlsoTang          <alsotang@gmail.com>
#      Christopher Meng  <i@cicku.me>
#      Yonsm Guo         <YonsmGuo@gmail.com>
#      Parkman           <cseparkman@gmail.com>
#      Ming Bai          <mbbill@gmail.com>
#      Bin Yu            <yubinlove1991@gmail.com>
#      lileixuan         <lileixuan@gmail.com>
#      Cong Ding         <cong@cding.org>
#      Zhang Youfu       <zhangyoufu@gmail.com>
#      Lu Wei            <luwei@barfoo>
#      Harmony Meow      <harmony.meow@gmail.com>
#      logostream        <logostream@gmail.com>
#      Rui Wang          <isnowfy@gmail.com>
#      Wang Wei Qiang    <wwqgtxx@gmail.com>
#      Felix Yan         <felixonmars@gmail.com>
#      Sui Feng          <suifeng.me@qq.com>
#      QXO               <qxodream@gmail.com>
#      Geek An           <geekan@foxmail.com>
#      Poly Rabbit       <mcx_221@foxmail.com>
#      oxnz              <yunxinyi@gmail.com>
#      Shusen Liu        <liushusen.smart@gmail.com>
#      Yad Smood         <y.s.inside@gmail.com>
#      Chen Shuang       <cs0x7f@gmail.com>
#      cnfuyu            <cnfuyu@gmail.com>
#      cuixin            <steven.cuixin@gmail.com>
#      s2marine0         <s2marine0@gmail.com>
#      Toshio Xiang      <snachx@gmail.com>
#      Bo Tian           <dxmtb@163.com>
#      Virgil            <variousvirgil@gmail.com>
#      hub01             <miaojiabumiao@yeah.net>
#      v3aqb             <sgzz.cj@gmail.com>
#      Oling Cat         <olingcat@gmail.com>
#      Meng Zhuo         <mengzhuo1203@gmail.com>
#      zwhfly            <zwhfly@163.com>
#      Hubertzhang       <hubert.zyk@gmail.com>
#      arrix             <arrixzhou@gmail.com>
#      gwjwin            <gwjwin@sina.com>
#      Jobin             <1149225004@qq.com>
#      Zhuhao Wang       <zhuhaow@gmail.com>
#      YFdyh000          <yfdyh000@gmail.com>
#      zzq1015           <zzq1015@users.noreply.github.com>
#      Zhengfa Dang      <zfdang@users.noreply.github.com>
#      haosdent          <haosdent@gmail.com>
#      xk liu            <lxk1012@gmail.com>

__version__ = '3.2.3'

import os
import sys
import sysconfig
import platform

#reload(sys).setdefaultencoding('UTF-8')
sys.dont_write_bytecode = True


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir))
python_path = os.path.join(root_path, 'python27', '1.0')

noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

if sys.platform == "win32":
    win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
    sys.path.append(win32_lib)
elif sys.platform == "linux" or sys.platform == "linux2":
    linux_lib = os.path.abspath( os.path.join(python_path, 'lib', 'linux'))
    sys.path.append(linux_lib)
elif sys.platform == "darwin":
    darwin_lib = os.path.abspath( os.path.join(python_path, 'lib', 'darwin'))
    sys.path.append(darwin_lib)
    extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python"
    sys.path.append(extra_lib)


from cert_util import CertUtil


try:
    __import__('gevent.monkey', fromlist=['.']).patch_all()
except (ImportError, SystemError) as e:
    print "import gevent fail:", e
    sys.exit(sys.stderr.write('please install python-gevent\n'))


import base64
import collections
import ConfigParser
import errno
import httplib
import io
import Queue
import random
import re
import socket
import ssl
import struct
import thread
import threading
import time
import urllib2
import urlparse


import gevent
import OpenSSL

NetWorkIOError = (socket.error, ssl.SSLError, OpenSSL.SSL.Error, OSError)
import logging


from proxylib import AuthFilter
from proxylib import AutoRangeFilter
from proxylib import BaseFetchPlugin
from proxylib import BaseProxyHandlerFilter
from proxylib import BlackholeFilter
from proxylib import CipherFileObject
from proxylib import deflate
from proxylib import DirectFetchPlugin
from proxylib import DirectRegionFilter
from proxylib import dnslib_record2iplist
from proxylib import dnslib_resolve_over_tcp
from proxylib import dnslib_resolve_over_udp
from proxylib import FakeHttpsFilter
from proxylib import ForceHttpsFilter
from proxylib import CRLFSitesFilter
from proxylib import get_dnsserver_list
from proxylib import get_uptime
from proxylib import inflate
from proxylib import LocalProxyServer
from proxylib import message_html
from proxylib import MockFetchPlugin
from proxylib import MultipleConnectionMixin
from proxylib import openssl_set_session_cache_mode
from proxylib import ProxyConnectionMixin
from proxylib import ProxyUtil
from proxylib import RC4Cipher
from proxylib import SimpleProxyHandler
from proxylib import spawn_later
from proxylib import SSLConnection
from proxylib import StaticFileFilter
from proxylib import StripPlugin
from proxylib import StripPluginEx
from proxylib import URLRewriteFilter
from proxylib import UserAgentFilter
from proxylib import XORCipher

import web_control

def is_google_ip(ipaddr):
    if ipaddr in ('74.125.127.102', '74.125.155.102', '74.125.39.102', '74.125.39.113', '209.85.229.138'):
        return False
    if ipaddr.startswith(('173.194.', '207.126.', '209.85.', '216.239.', '64.18.', '64.233.', '66.102.', '66.249.', '72.14.', '74.125.')):
        return True
    return False


class RangeFetch(object):
    """Range Fetch Class"""

    threads = 2
    maxsize = 1024*1024*4
    bufsize = 8192
    waitsize = 1024*512

    def __init__(self, handler, plugin, response, fetchservers, **kwargs):
        assert isinstance(plugin, BaseFetchPlugin) and hasattr(plugin, 'fetch')
        self.handler = handler
        self.url = handler.path
        self.plugin = plugin
        self.response = response
        self.fetchservers = fetchservers
        self.kwargs = kwargs
        self._stopped = None
        self._last_app_status = {}
        self.expect_begin = 0

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
        self.handler.send_response(response_status)
        for key, value in response_headers.items():
            self.handler.send_header(key, value)
        self.handler.end_headers()

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
                self.handler.wfile.write(data)
                self.expect_begin += len(data)
                del data
            except Exception as e:
                logging.info('RangeFetch client connection aborted(%s).', e)
                break
        self._stopped = True

    def __fetchlet(self, range_queue, data_queue, range_delay_size):
        headers = dict((k.title(), v) for k, v in self.handler.headers.items())
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
                        response = self.plugin.fetch(self.handler, self.handler.command, self.url, headers, self.handler.body, timeout=self.handler.connect_timeout, fetchserver=fetchserver, **self.kwargs)
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
                if fetchserver:
                    self._last_app_status[fetchserver] = response.app_status
                if response.app_status != 200:
                    logging.warning('Range Fetch "%s %s" %s return %s', self.handler.command, self.url, headers['Range'], response.app_status)
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
                        logging.warning('RangeFetch "%s %s" return Content-Range=%r: response headers=%r, retry %s-%s', self.handler.command, self.url, content_range, response.getheaders(), start, end)
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
                            data = None
                            with gevent.Timeout(max(1, self.bufsize//8192), False):
                                data = response.read(self.bufsize)
                            if not data:
                                break
                            data_queue.put((start, data))
                            start += len(data)
                        except Exception as e:
                            logging.warning('RangeFetch "%s %s" %s failed: %s', self.handler.command, self.url, headers['Range'], e)
                            break
                    if start < end + 1:
                        logging.warning('RangeFetch "%s %s" retry %s-%s', self.handler.command, self.url, start, end)
                        response.close()
                        range_queue.put((start, end, None))
                        continue
                    logging.info('>>>>>>>>>>>>>>> Successfully reached %d bytes.', start - 1)
                else:
                    logging.error('RangeFetch %r return %s', self.url, response.status)
                    response.close()
                    range_queue.put((start, end, None))
                    continue
            except StandardError as e:
                logging.exception('RangeFetch._fetchlet error:%s', e)
                raise


class GAEFetchPlugin(BaseFetchPlugin):
    """gae fetch plugin"""
    connect_timeout = 4
    max_retry = 2

    def __init__(self, appids, password, path, mode, cachesock, keepalive, obfuscate, pagespeed, validate, options, maxsize):
        BaseFetchPlugin.__init__(self)
        self.appids = appids
        self.password = password
        self.path = path
        self.mode = mode
        self.cachesock = cachesock
        self.keepalive = keepalive
        self.obfuscate = obfuscate
        self.pagespeed = pagespeed
        self.validate = validate
        self.options = options
        self.maxsize = maxsize

    def handle(self, handler, **kwargs):
        assert handler.command != 'CONNECT'
        method = handler.command
        headers = dict((k.title(), v) for k, v in handler.headers.items())
        body = handler.body
        if handler.path[0] == '/':
            url = '%s://%s%s' % (handler.scheme, handler.headers['Host'], handler.path)
        elif handler.path.lower().startswith(('http://', 'https://', 'ftp://')):
            url = handler.path
        else:
            raise ValueError('URLFETCH %r is not a valid url' % handler.path)
        errors = []
        response = None
        for i in xrange(self.max_retry):
            try:
                response = self.fetch(handler, method, url, headers, body, self.connect_timeout)
                if response.app_status < 500:
                    break
                else:
                    if response.app_status == 503:
                        # appid over qouta, switch to next appid
                        if len(self.appids) > 1:
                            self.appids.append(self.appids.pop(0))
                            logging.info('gae over qouta, switch next appid=%r', self.appids[0])
                    if i < self.max_retry - 1 and len(self.appids) > 1:
                        self.appids.append(self.appids.pop(0))
                        logging.info('URLFETCH return %d, trying next appid=%r', response.app_status, self.appids[0])
                    response.close()
            except Exception as e:
                errors.append(e)
                logging.info('GAE "%s %s" appid=%r %r, retry...', handler.command, handler.path, self.appids[0], e)
        if len(errors) == self.max_retry:
            if response and response.app_status >= 500:
                status = response.app_status
                headers = dict(response.getheaders())
                content = response.read()
                response.close()
            else:
                status = 502
                headers = {'Content-Type': 'text/html'}
                content = message_html('502 URLFetch failed', 'Local URLFetch %r failed' % handler.path, '<br>'.join(repr(x) for x in errors))
            return handler.handler_plugins['mock'].handle(handler, status, headers, content)
        logging.info('%s "GAE %s %s %s" %s %s', handler.address_string(), handler.command, handler.path, handler.protocol_version, response.status, response.getheader('Content-Length', '-'))
        try:
            if response.status == 206:
                fetchservers = ['%s://%s.appspot.com%s' % (self.mode, x, self.path) for x in self.appids]
                return RangeFetch(handler, self, response, fetchservers).fetch()
            handler.close_connection = not response.getheader('Content-Length')
            handler.send_response(response.status)
            for key, value in response.getheaders():
                if key.title() == 'Transfer-Encoding':
                    continue
                handler.send_header(key, value)
            handler.end_headers()
            bufsize = 8192
            while True:
                data = None
                with gevent.Timeout(self.connect_timeout, False):
                    data = response.read(bufsize)
                if data is None:
                    logging.warning('response.read(%r) %r timeout', bufsize, url)
                    handler.close_connection = True
                    break
                if data:
                    handler.wfile.write(data)
                if not data:
                    cache_sock = getattr(response, 'cache_sock', None)
                    if cache_sock:
                        cache_sock.close()
                        del response.cache_sock
                    response.close()
                    break
                del data
        except NetWorkIOError as e:
            if e[0] in (errno.ECONNABORTED, errno.EPIPE) or 'bad write retry' in repr(e):
                return

    def fetch(self, handler, method, url, headers, body, timeout, **kwargs):
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
        if self.password:
            kwargs['password'] = self.password
        if self.options:
            kwargs['options'] = self.options
        if self.validate:
            kwargs['validate'] = self.validate
        if self.maxsize:
            kwargs['maxsize'] = self.maxsize
        payload = '%s %s %s\r\n' % (method, url, handler.request_version)
        payload += ''.join('%s: %s\r\n' % (k, v) for k, v in headers.items() if k not in handler.skip_headers)
        payload += ''.join('X-URLFETCH-%s: %s\r\n' % (k, v) for k, v in kwargs.items() if v)
        # prepare GAE request
        request_method = 'POST'
        fetchserver_index = random.randint(0, len(self.appids)-1) if 'Range' in headers else 0
        fetchserver = kwargs.get('fetchserver') or '%s://%s.appspot.com%s' % (self.mode, self.appids[fetchserver_index], self.path)
        request_headers = {}
        if common.GAE_OBFUSCATE:
            request_method = 'GET'
            fetchserver += 'ps/%d%s.gif' % (int(time.time()*1000), random.random())
            request_headers['X-URLFETCH-PS1'] = base64.b64encode(deflate(payload)).strip()
            if body:
                request_headers['X-URLFETCH-PS2'] = base64.b64encode(deflate(body)).strip()
                body = ''
            if common.GAE_PAGESPEED:
                fetchserver = re.sub(r'^(\w+://)', r'\g<1>1-ps.googleusercontent.com/h/', fetchserver)
        else:
            payload = deflate(payload)
            body = '%s%s%s' % (struct.pack('!h', len(payload)), payload, body)
            if 'rc4' in common.GAE_OPTIONS:
                request_headers['X-URLFETCH-Options'] = 'rc4'
                body = RC4Cipher(kwargs.get('password')).encrypt(body)
            request_headers['Content-Length'] = str(len(body))
        # post data
        need_crlf = 0 if common.GAE_MODE == 'https' else 1
        need_validate = common.GAE_VALIDATE
        cache_key = '%s:%d' % (common.HOST_POSTFIX_MAP['.appspot.com'], 443 if common.GAE_MODE == 'https' else 80)
        headfirst = bool(common.GAE_HEADFIRST)
        response = handler.create_http_request(request_method, fetchserver, request_headers, body, timeout, crlf=need_crlf, validate=need_validate, cache_key=cache_key, headfirst=headfirst)
        response.app_status = response.status
        if response.app_status != 200:
            return response
        if 'rc4' in request_headers.get('X-URLFETCH-Options', ''):
            response.fp = CipherFileObject(response.fp, RC4Cipher(kwargs['password']))
        data = response.read(2)
        if len(data) < 2:
            response.status = 502
            response.fp = io.BytesIO(b'connection aborted. too short leadbyte data=' + data)
            response.read = response.fp.read
            return response
        headers_length, = struct.unpack('!h', data)
        data = response.read(headers_length)
        if len(data) < headers_length:
            response.status = 502
            response.fp = io.BytesIO(b'connection aborted. too short headers data=' + data)
            response.read = response.fp.read
            return response
        raw_response_line, headers_data = inflate(data).split('\r\n', 1)
        _, response.status, response.reason = raw_response_line.split(None, 2)
        response.status = int(response.status)
        response.reason = response.reason.strip()
        response.msg = httplib.HTTPMessage(io.BytesIO(headers_data))
        return response


class PHPFetchPlugin(BaseFetchPlugin):
    """php fetch plugin"""
    connect_timeout = 4
    def __init__(self, fetchservers, password, validate):
        BaseFetchPlugin.__init__(self)
        self.fetchservers = fetchservers
        self.password = password
        self.validate = validate

    def handle(self, handler, **kwargs):
        method = handler.command
        url = handler.path
        headers = dict((k.title(), v) for k, v in handler.headers.items())
        body = handler.body
        if body:
            if len(body) < 10 * 1024 * 1024 and 'Content-Encoding' not in headers:
                zbody = deflate(body)
                if len(zbody) < len(body):
                    body = zbody
                    headers['Content-Encoding'] = 'deflate'
            headers['Content-Length'] = str(len(body))
        skip_headers = handler.skip_headers
        if self.password:
            kwargs['password'] = self.password
        if self.validate:
            kwargs['validate'] = self.validate
        payload = '%s %s %s\r\n' % (method, url, handler.request_version)
        payload += ''.join('%s: %s\r\n' % (k, v) for k, v in headers.items() if k not in handler.skip_headers)
        payload += ''.join('X-URLFETCH-%s: %s\r\n' % (k, v) for k, v in kwargs.items() if v)
        payload = deflate(payload)
        body = '%s%s%s' % ((struct.pack('!h', len(payload)), payload, body))
        request_headers = {'Content-Length': len(body), 'Content-Type': 'application/octet-stream'}
        fetchserver_index = 0 if 'Range' not in headers else random.randint(0, len(self.fetchservers)-1)
        fetchserver = '%s?%s' % (self.fetchservers[fetchserver_index], random.random())
        crlf = 0
        cache_key = '%s//:%s' % urlparse.urlsplit(fetchserver)[:2]
        try:
            response = handler.create_http_request('POST', fetchserver, request_headers, body, self.connect_timeout, crlf=crlf, cache_key=cache_key)
        except Exception as e:
            logging.warning('%s "%s" failed %r', method, url, e)
            return
        response.app_status = response.status
        need_decrypt = self.password and response.app_status == 200 and response.getheader('Content-Type', '') == 'image/gif' and response.fp
        if need_decrypt:
            response.fp = CipherFileObject(response.fp, XORCipher(self.password[0]))
        logging.info('%s "PHP %s %s %s" %s %s', handler.address_string(), handler.command, url, handler.protocol_version, response.status, response.getheader('Content-Length', '-'))
        handler.close_connection = bool(response.getheader('Transfer-Encoding'))
        while True:
            data = response.read(8192)
            if not data:
                break
            handler.wfile.write(data)
            del data


class VPSFetchPlugin(BaseFetchPlugin):
    """vps fetch plugin"""
    connect_timeout = 4

    def __init__(self, fetchservers, username, password):
        BaseFetchPlugin.__init__(self)
        self.fetchservers = fetchservers
        self.username = username
        self.password = password
        self.fake_headers = {}

    def handle(self, handler, **kwargs):
        if handler.command == 'CONNECT':
            return self.handle_connect(handler, **kwargs)
        else:
            return self.handle_method(handler, **kwargs)

    def handle_connect(self, handler, **kwargs):
        return

    def handle_method(self, handler, **kwargs):
        method = handler.command
        url = handler.path
        headers = dict((k.title(), v) for k, v in handler.headers.items() if k.title() not in handler.skip_headers)
        x_headers = {}
        if 'Host' in headers:
            x_headers['Host'] = headers.pop('Host')
        if 'Cookie' in headers:
            x_headers['Cookie'] = headers.pop('Cookie')
        headers['Host'] = 'www.%s.com' % self.username
        self.fake_headers = headers.copy()
        fetchserver = random.choice(self.fetchservers)
        response = handler.create_http_request(handler.command, fetchserver, headers, handler.body, self.connect_timeout)
        if not response:
            raise socket.error(errno.ECONNRESET, 'urlfetch %r return None' % url)
        #TODO


class HostsFilter(BaseProxyHandlerFilter):
    """hosts filter"""
    def __init__(self, iplist_map, host_map, host_postfix_map, hostport_map, hostport_postfix_map, urlre_map):
        self.iplist_map = iplist_map
        self.host_map = host_map
        self.host_postfix_map = host_postfix_map
        self.host_postfix_endswith = tuple(host_postfix_map)
        self.hostport_map = hostport_map
        self.hostport_postfix_map = hostport_postfix_map
        self.hostport_postfix_endswith = tuple(hostport_postfix_map)
        self.urlre_map = urlre_map

    def gethostbyname2(self, handler, hostname):
        hostport = '%s:%d' % (hostname, handler.port)
        hosts = ''
        if hostname in self.host_map:
            hosts = self.host_map[hostname]
        elif hostname.endswith(self.host_postfix_endswith):
            hosts = next(self.host_postfix_map[x] for x in self.host_postfix_map if hostname.endswith(x))
        if hostport in self.hostport_map:
            hosts = self.hostport_map[hostport]
        elif hostport.endswith(self.hostport_postfix_endswith):
            hosts = next(self.hostport_postfix_map[x] for x in self.hostport_postfix_map if hostport.endswith(x))
        if handler.command != 'CONNECT' and self.urlre_map:
            try:
                hosts = next(self.urlre_map[x] for x in self.urlre_map if x(handler.path))
            except StopIteration:
                pass
        if hosts not in ('', 'direct'):
            return self.iplist_map.get(hosts) or hosts.split('|')
        return None

    def filter(self, handler):
        host, port = handler.host, handler.port
        hostport = handler.path if handler.command == 'CONNECT' else '%s:%d' % (host, port)
        headfirst = '.google' in host
        if host in self.host_map:
            return 'direct', {'cache_key': '%s:%d' % (self.host_map[host], port), 'headfirst': headfirst}
        elif host.endswith(self.host_postfix_endswith):
            self.host_map[host] = next(self.host_postfix_map[x] for x in self.host_postfix_map if host.endswith(x))
            return 'direct', {'cache_key': '%s:%d' % (self.host_map[host], port), 'headfirst': headfirst}
        elif hostport in self.hostport_map:
            return 'direct', {'cache_key': '%s:%d' % (self.hostport_map[hostport], port), 'headfirst': headfirst}
        elif hostport.endswith(self.hostport_postfix_endswith):
            self.hostport_map[hostport] = next(self.hostport_postfix_map[x] for x in self.hostport_postfix_map if hostport.endswith(x))
            return 'direct', {'cache_key': '%s:%d' % (self.hostport_map[hostport], port), 'headfirst': headfirst}
        if handler.command != 'CONNECT' and self.urlre_map and any(x(handler.path) for x in self.urlre_map):
            return 'direct', {'headfirst': headfirst}


class GAEFetchFilter(BaseProxyHandlerFilter):
    """gae fetch filter"""
    #https://github.com/AppScale/gae_sdk/blob/master/google/appengine/api/taskqueue/taskqueue.py#L241
    MAX_URL_LENGTH = 2083
    def filter(self, handler):
        """https://developers.google.com/appengine/docs/python/urlfetch/"""
        if handler.command == 'CONNECT':
            do_ssl_handshake = 440 <= handler.port <= 450 or 1024 <= handler.port <= 65535
            return 'strip', {'do_ssl_handshake': do_ssl_handshake}
        elif handler.command in ('GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'PATCH'):
            return 'gae', {}
        else:
            if 'php' in handler.handler_plugins:
                return 'php', {}
            else:
                logging.warning('"%s %s" not supported by GAE, please enable PHP mode!', handler.command, handler.path)
                return 'direct', {}


class WithGAEFilter(BaseProxyHandlerFilter):
    """withgae/withphp/withvps filter"""
    def __init__(self, withgae_sites, withphp_sites, withvps_sites):
        self.withgae_sites = set(x for x in withgae_sites if not x.startswith('.'))
        self.withgae_sites_postfix = tuple(x for x in withgae_sites if x.startswith('.'))
        self.withphp_sites = set(x for x in withphp_sites if not x.startswith('.'))
        self.withphp_sites_postfix = tuple(x for x in withphp_sites if x.startswith('.'))
        self.withvps_sites = set(x for x in withvps_sites if not x.startswith('.'))
        self.withvps_sites_postfix = tuple(x for x in withvps_sites if x.startswith('.'))

    def filter(self, handler):
        plugin = ''
        if handler.host in self.withgae_sites or handler.host.endswith(self.withgae_sites_postfix):
            plugin = 'gae'
        elif handler.host in self.withphp_sites or handler.host.endswith(self.withphp_sites_postfix):
            plugin = 'php'
        elif handler.host in self.withvps_sites or handler.host.endswith(self.withvps_sites_postfix):
            plugin = 'vps'
        if plugin:
            if handler.command == 'CONNECT':
                do_ssl_handshake = 440 <= handler.port <= 450 or 1024 <= handler.port <= 65535
                return 'strip', {'do_ssl_handshake': do_ssl_handshake}
            else:
                return plugin, {}


class GAEProxyHandler(MultipleConnectionMixin, SimpleProxyHandler):
    """GAE Proxy Handler"""
    handler_filters = [GAEFetchFilter()]
    handler_plugins = {'direct': DirectFetchPlugin(),
                       'mock': MockFetchPlugin(),
                       'strip': StripPlugin(),}
    hosts_filter = None

    def __init__(self, *args, **kwargs):
        SimpleProxyHandler.__init__(self, *args, **kwargs)

    def first_run(self):
        """GAEProxyHandler setup, init domain/iplist map"""
        openssl_set_session_cache_mode(self.openssl_context, 'client')
        if not common.PROXY_ENABLE:
            logging.info('resolve common.IPLIST_MAP names=%s to iplist', list(common.IPLIST_MAP))
            common.resolve_iplist()
        random.shuffle(common.GAE_APPIDS)
        self.__class__.handler_plugins['gae'] = GAEFetchPlugin(common.GAE_APPIDS, common.GAE_PASSWORD, common.GAE_PATH, common.GAE_MODE, common.GAE_CACHESOCK, common.GAE_KEEPALIVE, common.GAE_OBFUSCATE, common.GAE_PAGESPEED, common.GAE_VALIDATE, common.GAE_OPTIONS, common.GAE_MAXSIZE)
        try:
            self.__class__.hosts_filter = next(x for x in self.__class__.handler_filters if isinstance(x, HostsFilter))
        except StopIteration:
            pass

    def gethostbyname2(self, hostname):
        iplist = self.hosts_filter.gethostbyname2(self, hostname) if self.hosts_filter else None
        return iplist or MultipleConnectionMixin.gethostbyname2(self, hostname)


class ProxyGAEProxyHandler(ProxyConnectionMixin, GAEProxyHandler):

    def __init__(self, *args, **kwargs):
        ProxyConnectionMixin.__init__(self, common.PROXY_HOST, common.PROXY_PORT, common.PROXY_USERNAME, common.PROXY_PASSWROD)
        GAEProxyHandler.__init__(self, *args, **kwargs)

    def gethostbyname2(self, hostname):
        for postfix in ('.appspot.com', '.googleusercontent.com'):
            if hostname.endswith(postfix):
                host = common.HOST_MAP.get(hostname) or common.HOST_POSTFIX_MAP.get(postfix) or 'www.google.com'
                return common.IPLIST_MAP.get(host) or host.split('|')
        return ProxyConnectionMixin.gethostbyname2(self, hostname)


class PHPFetchFilter(BaseProxyHandlerFilter):
    """php fetch filter"""
    def filter(self, handler):
        if handler.command == 'CONNECT':
            return 'strip', {}
        else:
            return 'php', {}


class VPSFetchFilter(BaseProxyHandlerFilter):
    """vps fetch filter"""
    def filter(self, handler):
        return 'vps', {}


class PHPProxyHandler(MultipleConnectionMixin, SimpleProxyHandler):
    """PHP Proxy Handler"""
    handler_filters = [PHPFetchFilter()]
    handler_plugins = {'direct': DirectFetchPlugin(),
                       'mock': MockFetchPlugin(),
                       'strip': StripPlugin(),}

    def __init__(self, *args, **kwargs):
        SimpleProxyHandler.__init__(self, *args, **kwargs)


class ProxyPHPProxyHandler(ProxyConnectionMixin, PHPProxyHandler):

    def __init__(self, *args, **kwargs):
        ProxyConnectionMixin.__init__(self, common.PROXY_HOST, common.PROXY_PORT, common.PROXY_USERNAME, common.PROXY_PASSWROD)
        PHPProxyHandler.__init__(self, *args, **kwargs)

    def gethostbyname2(self, hostname):
        return [hostname]



class Common(object):
    """Global Config Object"""

    ENV_CONFIG_PREFIX = 'GOAGENT_'

    def __init__(self):
        """load config from proxy.ini"""
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>\S+)\s+(?P<vi>[=])\s+(?P<value>.*)$')
        self.CONFIG = ConfigParser.ConfigParser()
        self.CONFIG_FILENAME = os.path.splitext(os.path.abspath(__file__))[0]+'.ini'
        self.DATA_PATH = os.path.join(root_path, "data", "php_proxy")
        if not os.path.isdir(self.DATA_PATH):
            os.mkdir(self.DATA_PATH)

        self.CONFIG_USER_FILENAME = os.path.join(self.DATA_PATH, "config.ini")
        if os.path.isfile(self.CONFIG_USER_FILENAME):
            self.CONFIG.read([self.CONFIG_FILENAME, self.CONFIG_USER_FILENAME])
        else:
            self.CONFIG.read(self.CONFIG_FILENAME)

        for key, value in os.environ.items():
            m = re.match(r'^%s([A-Z]+)_([A-Z\_\-]+)$' % self.ENV_CONFIG_PREFIX, key)
            if m:
                self.CONFIG.set(m.group(1).lower(), m.group(2).lower(), value)

        self.LISTEN_IP = self.CONFIG.get('listen', 'ip')
        self.LISTEN_PORT = self.CONFIG.getint('listen', 'port')
        self.LISTEN_USERNAME = self.CONFIG.get('listen', 'username') if self.CONFIG.has_option('listen', 'username') else ''
        self.LISTEN_PASSWORD = self.CONFIG.get('listen', 'password') if self.CONFIG.has_option('listen', 'password') else ''
        self.LISTEN_VISIBLE = self.CONFIG.getint('listen', 'visible')
        self.LISTEN_DEBUGINFO = self.CONFIG.getint('listen', 'debuginfo')

        self.GAE_ENABLE = self.CONFIG.getint('gae', 'enable')
        self.GAE_APPIDS = re.findall(r'[\w\-\.]+', self.CONFIG.get('gae', 'appid').replace('.appspot.com', ''))
        self.GAE_PASSWORD = self.CONFIG.get('gae', 'password').strip()
        self.GAE_PATH = self.CONFIG.get('gae', 'path')
        self.GAE_MODE = self.CONFIG.get('gae', 'mode')
        self.GAE_IPV6 = self.CONFIG.getint('gae', 'ipv6')
        self.GAE_WINDOW = self.CONFIG.getint('gae', 'window')
        self.GAE_KEEPALIVE = self.CONFIG.getint('gae', 'keepalive')
        self.GAE_CACHESOCK = self.CONFIG.getint('gae', 'cachesock')
        self.GAE_HEADFIRST = self.CONFIG.getint('gae', 'headfirst')
        self.GAE_OBFUSCATE = self.CONFIG.getint('gae', 'obfuscate')
        self.GAE_VALIDATE = self.CONFIG.getint('gae', 'validate')
        self.GAE_TRANSPORT = self.CONFIG.getint('gae', 'transport') if self.CONFIG.has_option('gae', 'transport') else 0
        self.GAE_OPTIONS = self.CONFIG.get('gae', 'options')
        self.GAE_REGIONS = set(x.upper() for x in self.CONFIG.get('gae', 'regions').split('|') if x.strip())
        self.GAE_SSLVERSION = self.CONFIG.get('gae', 'sslversion')
        self.GAE_PAGESPEED = self.CONFIG.getint('gae', 'pagespeed') if self.CONFIG.has_option('gae', 'pagespeed') else 0
        self.GAE_MAXSIZE = self.CONFIG.getint('gae', 'maxsize')

        if self.GAE_IPV6:
            sock = None
            try:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                sock.connect(('2001:4860:4860::8888', 53))
                logging.info('use ipv6 interface %s for gae', sock.getsockname()[0])
            except Exception as e:
                logging.info('Fail try use ipv6 %r, fallback ipv4', e)
                self.GAE_IPV6 = 0
            finally:
                if sock:
                    sock.close()

        if 'USERDNSDOMAIN' in os.environ and re.match(r'^\w+\.\w+$', os.environ['USERDNSDOMAIN']):
            self.CONFIG.set('profile', '.' + os.environ['USERDNSDOMAIN'], '')

        urlrewrite_map = collections.OrderedDict()
        host_map = collections.OrderedDict()
        host_postfix_map = collections.OrderedDict()
        hostport_map = collections.OrderedDict()
        hostport_postfix_map = collections.OrderedDict()
        urlre_map = collections.OrderedDict()
        withgae_sites = []
        withphp_sites = []
        withvps_sites = []
        crlf_sites = []
        nocrlf_sites = []
        forcehttps_sites = []
        noforcehttps_sites = []
        fakehttps_sites = []
        nofakehttps_sites = []
        dns_servers = []

        for site, rule in self.CONFIG.items('profile'):
            rules = [x.strip() for x in re.split(r'[,\|]', rule) if x.strip()]
            if site == 'dns':
                dns_servers = rules
                continue
            if rule.startswith(('file://', 'http://', 'https://')) or '$1' in rule:
                urlrewrite_map[site] = rule
                continue
            for name, sites in [('withgae', withgae_sites),
                                ('withphp', withphp_sites),
                                ('withvps', withvps_sites),
                                ('crlf', crlf_sites),
                                ('nocrlf', nocrlf_sites),
                                ('forcehttps', forcehttps_sites),
                                ('noforcehttps', noforcehttps_sites),
                                ('fakehttps', fakehttps_sites),
                                ('nofakehttps', nofakehttps_sites)]:
                if name in rules:
                    sites.append(site)
                    rules.remove(name)
            hostname = rules and rules[0]
            if not hostname:
                continue
            if ':' in site and '\\' not in site:
                if site.startswith('.'):
                    hostport_postfix_map[site] = hostname
                else:
                    hostport_map[site] = hostname
            elif '\\' in site:
                urlre_map[re.compile(site).match] = hostname
            else:
                if site.startswith('.'):
                    host_postfix_map[site] = hostname
                else:
                    host_map[site] = hostname

        self.HTTP_DNS = dns_servers
        self.WITHGAE_SITES = tuple(withgae_sites)
        self.WITHPHP_SITES = tuple(withphp_sites)
        self.WITHVPS_SITES = tuple(withvps_sites)
        self.CRLF_SITES = tuple(crlf_sites)
        self.NOCRLF_SITES = set(nocrlf_sites)
        self.FORCEHTTPS_SITES = tuple(forcehttps_sites)
        self.NOFORCEHTTPS_SITES = set(noforcehttps_sites)
        self.FAKEHTTPS_SITES = tuple(fakehttps_sites)
        self.NOFAKEHTTPS_SITES = set(nofakehttps_sites)
        self.URLREWRITE_MAP = urlrewrite_map
        self.HOSTPORT_MAP = hostport_map
        self.HOSTPORT_POSTFIX_MAP = hostport_postfix_map
        self.URLRE_MAP = urlre_map
        self.HOST_MAP = host_map
        self.HOST_POSTFIX_MAP = host_postfix_map

        self.IPLIST_MAP = collections.OrderedDict((k, v.split('|') if v else []) for k, v in self.CONFIG.items('iplist'))
        self.IPLIST_MAP.update((k, [k]) for k, v in self.HOST_MAP.items() if k == v)
        self.IPLIST_PREDEFINED = [x for x in sum(self.IPLIST_MAP.values(), []) if re.match(r'^\d+\.\d+\.\d+\.\d+$', x) or ':' in x]

        if self.GAE_IPV6 and 'google_ipv6' in self.IPLIST_MAP:
            for name in self.IPLIST_MAP.keys():
                if name.startswith('google') and name not in ('google_ipv6', 'google_talk'):
                    self.IPLIST_MAP[name] = self.IPLIST_MAP['google_ipv6']

        self.PAC_ENABLE = self.CONFIG.getint('pac', 'enable')
        self.PAC_IP = self.CONFIG.get('pac', 'ip')
        self.PAC_PORT = self.CONFIG.getint('pac', 'port')
        self.PAC_FILE = self.CONFIG.get('pac', 'file').lstrip('/')
        self.PAC_GFWLIST = self.CONFIG.get('pac', 'gfwlist')
        self.PAC_ADBLOCK = self.CONFIG.get('pac', 'adblock')
        self.PAC_ADMODE = self.CONFIG.getint('pac', 'admode')
        self.PAC_EXPIRED = self.CONFIG.getint('pac', 'expired')

        self.PHP_ENABLE = self.CONFIG.getint('php', 'enable')
        self.PHP_LISTEN = self.CONFIG.get('php', 'listen')
        self.PHP_PASSWORD = self.CONFIG.get('php', 'password') if self.CONFIG.has_option('php', 'password') else ''
        self.PHP_CRLF = self.CONFIG.getint('php', 'crlf') if self.CONFIG.has_option('php', 'crlf') else 1
        self.PHP_VALIDATE = self.CONFIG.getint('php', 'validate') if self.CONFIG.has_option('php', 'validate') else 0
        self.PHP_FETCHSERVERS = self.CONFIG.get('php', 'fetchserver').split('|')

        self.PROXY_ENABLE = self.CONFIG.getint('proxy', 'enable')
        self.PROXY_AUTODETECT = self.CONFIG.getint('proxy', 'autodetect') if self.CONFIG.has_option('proxy', 'autodetect') else 0
        self.PROXY_HOST = self.CONFIG.get('proxy', 'host')
        self.PROXY_PORT = self.CONFIG.get('proxy', 'port')
        if self.PROXY_PORT == "":
            self.PROXY_PORT = 0
        else:
            self.PROXY_PORT = int(self.PROXY_PORT)

        self.PROXY_USERNAME = self.CONFIG.get('proxy', 'username')
        self.PROXY_PASSWROD = self.CONFIG.get('proxy', 'password')

        if not self.PROXY_ENABLE and self.PROXY_AUTODETECT:
            system_proxy = ProxyUtil.get_system_proxy()
            if system_proxy and self.LISTEN_IP not in system_proxy:
                _, username, password, address = ProxyUtil.parse_proxy(system_proxy)
                proxyhost, _, proxyport = address.rpartition(':')
                self.PROXY_ENABLE = 1
                self.PROXY_USERNAME = username
                self.PROXY_PASSWROD = password
                self.PROXY_HOST = proxyhost
                self.PROXY_PORT = int(proxyport)
        if self.PROXY_ENABLE:
            self.GAE_MODE = 'https'

        self.CONTROL_ENABLE = self.CONFIG.getint('control', 'enable')
        self.CONTROL_IP = self.CONFIG.get('control', 'ip')
        self.CONTROL_PORT = self.CONFIG.getint('control', 'port')

        self.AUTORANGE_HOSTS = self.CONFIG.get('autorange', 'hosts').split('|')
        self.AUTORANGE_ENDSWITH = tuple(self.CONFIG.get('autorange', 'endswith').split('|'))
        self.AUTORANGE_NOENDSWITH = tuple(self.CONFIG.get('autorange', 'noendswith').split('|'))
        self.AUTORANGE_MAXSIZE = self.CONFIG.getint('autorange', 'maxsize')
        self.AUTORANGE_WAITSIZE = self.CONFIG.getint('autorange', 'waitsize')
        self.AUTORANGE_BUFSIZE = self.CONFIG.getint('autorange', 'bufsize')
        self.AUTORANGE_THREADS = self.CONFIG.getint('autorange', 'threads')

        self.FETCHMAX_LOCAL = self.CONFIG.getint('fetchmax', 'local') if self.CONFIG.get('fetchmax', 'local') else 3
        self.FETCHMAX_SERVER = self.CONFIG.get('fetchmax', 'server')

        self.DNS_ENABLE = self.CONFIG.getint('dns', 'enable')
        self.DNS_LISTEN = self.CONFIG.get('dns', 'listen')
        self.DNS_SERVERS = self.HTTP_DNS or self.CONFIG.get('dns', 'servers').split('|')
        self.DNS_BLACKLIST = set(self.CONFIG.get('dns', 'blacklist').split('|'))
        self.DNS_TCPOVER = tuple(self.CONFIG.get('dns', 'tcpover').split('|')) if self.CONFIG.get('dns', 'tcpover').strip() else tuple()
        if self.GAE_IPV6:
            self.DNS_SERVERS = [x for x in self.DNS_SERVERS if ':' in x]
        else:
            self.DNS_SERVERS = [x for x in self.DNS_SERVERS if ':' not in x]

        self.USERAGENT_ENABLE = self.CONFIG.getint('useragent', 'enable')
        self.USERAGENT_STRING = self.CONFIG.get('useragent', 'string')

        self.LOVE_ENABLE = self.CONFIG.getint('love', 'enable')
        self.LOVE_TIP = self.CONFIG.get('love', 'tip').encode('utf8').decode('unicode-escape').split('|')

        self.keep_run = True

    def extend_iplist(self, iplist_name, hosts):
        logging.info('extend_iplist start for hosts=%s', hosts)
        new_iplist = []
        def do_remote_resolve(host, dnsserver, queue):
            assert isinstance(dnsserver, basestring)
            for dnslib_resolve in (dnslib_resolve_over_udp, dnslib_resolve_over_tcp):
                try:
                    time.sleep(random.random())
                    iplist = dnslib_record2iplist(dnslib_resolve(host, [dnsserver], timeout=4, blacklist=self.DNS_BLACKLIST))
                    queue.put((host, dnsserver, iplist))
                except (socket.error, OSError) as e:
                    logging.info('%s remote host=%r failed: %s', str(dnslib_resolve).split()[1], host, e)
                    time.sleep(1)
        result_queue = Queue.Queue()
        pool = __import__('gevent.pool', fromlist=['.']).Pool(8) if sys.modules.get('gevent') else None
        for host in hosts:
            for dnsserver in self.DNS_SERVERS:
                logging.debug('remote resolve host=%r from dnsserver=%r', host, dnsserver)
                if pool:
                    pool.spawn(do_remote_resolve, host, dnsserver, result_queue)
                else:
                    thread.start_new_thread(do_remote_resolve, (host, dnsserver, result_queue))
        for _ in xrange(len(self.DNS_SERVERS) * len(hosts) * 2):
            try:
                host, dnsserver, iplist = result_queue.get(timeout=16)
                logging.debug('%r remote host=%r return %s', dnsserver, host, iplist)
                if '.google' in host:
                    if self.GAE_IPV6:
                        iplist = [x for x in iplist if ':' in x]
                    else:
                        iplist = [x for x in iplist if is_google_ip(x)]
                new_iplist += iplist
            except Queue.Empty:
                break
        logging.info('extend_iplist finished, added %s', len(set(self.IPLIST_MAP[iplist_name])-set(new_iplist)))
        self.IPLIST_MAP[iplist_name] = list(set(self.IPLIST_MAP[iplist_name] + new_iplist))

    def resolve_iplist(self):
        # https://support.google.com/websearch/answer/186669?hl=zh-Hans
        def do_local_resolve(host, queue):
            assert isinstance(host, basestring)
            for _ in xrange(3):
                try:
                    family = socket.AF_INET6 if self.GAE_IPV6 else socket.AF_INET
                    iplist = [x[-1][0] for x in socket.getaddrinfo(host, 80, family)]
                    queue.put((host, iplist))
                except (socket.error, OSError) as e:
                    logging.warning('socket.getaddrinfo host=%r failed: %s', host, e)
                    time.sleep(0.1)
        google_blacklist = ['216.239.32.20'] + list(self.DNS_BLACKLIST)
        google_blacklist_prefix = tuple(x for x in self.DNS_BLACKLIST if x.endswith('.'))
        for name, need_resolve_hosts in list(self.IPLIST_MAP.items()):
            if all(re.match(r'\d+\.\d+\.\d+\.\d+', x) or ':' in x for x in need_resolve_hosts):
                continue
            need_resolve_remote = [x for x in need_resolve_hosts if ':' not in x and not re.match(r'\d+\.\d+\.\d+\.\d+', x)]
            resolved_iplist = [x for x in need_resolve_hosts if x not in need_resolve_remote]
            result_queue = Queue.Queue()
            for host in need_resolve_remote:
                logging.debug('local resolve host=%r', host)
                thread.start_new_thread(do_local_resolve, (host, result_queue))
            for _ in xrange(len(need_resolve_remote)):
                try:
                    host, iplist = result_queue.get(timeout=8)
                    resolved_iplist += iplist
                except Queue.Empty:
                    break
            if name == 'google_hk' and need_resolve_remote:
                for delay in (30, 60, 150, 240, 300, 450, 600, 900):
                    spawn_later(delay, self.extend_iplist, name, need_resolve_remote)
            if name.startswith('google_') and name not in ('google_cn', 'google_hk') and resolved_iplist:
                iplist_prefix = re.split(r'[\.:]', resolved_iplist[0])[0]
                resolved_iplist = list(set(x for x in resolved_iplist if x.startswith(iplist_prefix)))
            else:
                resolved_iplist = list(set(resolved_iplist))
            if name.startswith('google_'):
                resolved_iplist = list(set(resolved_iplist) - set(google_blacklist))
                resolved_iplist = [x for x in resolved_iplist if not x.startswith(google_blacklist_prefix)]
            if len(resolved_iplist) == 0 and name in ('google_hk', 'google_cn') and not self.GAE_IPV6:
                logging.error('resolve %s host return empty! please retry!', name)
                sys.exit(-1)
            logging.info('resolve name=%s host to iplist=%r', name, resolved_iplist)
            common.IPLIST_MAP[name] = resolved_iplist
        if self.IPLIST_MAP.get('google_cn', []):
            try:
                for _ in xrange(4):
                    socket.create_connection((random.choice(self.IPLIST_MAP['google_cn']), 80), timeout=2).close()
            except socket.error:
                self.IPLIST_MAP['google_cn'] = []
        if len(self.IPLIST_MAP.get('google_cn', [])) < 4 and self.IPLIST_MAP.get('google_hk', []):
            logging.warning('google_cn resolved too short iplist=%s, switch to google_hk', self.IPLIST_MAP.get('google_cn', []))
            self.IPLIST_MAP['google_cn'] = self.IPLIST_MAP['google_hk']

    def info(self):
        info = ''
        info += '------------------------------------------------------\n'
        info += 'PHP Proxy Version    : %s (python/%s gevent/%s pyopenssl/%s)\n' % (__version__, platform.python_version(), gevent.__version__, OpenSSL.__version__)
        info += 'Uvent Version      : %s (pyuv/%s libuv/%s)\n' % (__import__('uvent').__version__, __import__('pyuv').__version__, __import__('pyuv').LIBUV_VERSION) if all(x in sys.modules for x in ('pyuv', 'uvent')) else ''

        info += 'Local Proxy        : %s:%s\n' % (self.PROXY_HOST, self.PROXY_PORT) if self.PROXY_ENABLE else ''
        info += 'Debug INFO         : %s\n' % self.LISTEN_DEBUGINFO if self.LISTEN_DEBUGINFO else ''
        if common.GAE_ENABLE:
            info += 'Listen Address     : %s:%d\n' % (self.LISTEN_IP, self.LISTEN_PORT)
            info += 'GAE Mode           : %s\n' % self.GAE_MODE
            info += 'GAE IPv6           : %s\n' % self.GAE_IPV6 if self.GAE_IPV6 else ''
            info += 'GAE APPID          : %s\n' % '|'.join(self.GAE_APPIDS)
            info += 'GAE Validate       : %s\n' % self.GAE_VALIDATE if self.GAE_VALIDATE else ''
            info += 'GAE Obfuscate      : %s\n' % self.GAE_OBFUSCATE if self.GAE_OBFUSCATE else ''
        if common.PAC_ENABLE:
            info += 'Pac Server         : http://%s:%d/%s\n' % (self.PAC_IP if self.PAC_IP and self.PAC_IP != '0.0.0.0' else ProxyUtil.get_listen_ip(), self.PAC_PORT, self.PAC_FILE)
            info += 'Pac File           : file://%s\n' % os.path.abspath(self.PAC_FILE)
        if common.PHP_ENABLE:
            info += 'PHP Listen         : %s\n' % common.PHP_LISTEN
            info += 'PHP FetchServers   : %s\n' % common.PHP_FETCHSERVERS
        if common.DNS_ENABLE:
            info += 'DNS Listen         : %s\n' % common.DNS_LISTEN
            info += 'DNS Servers        : %s\n' % '|'.join(common.DNS_SERVERS)
        info += '------------------------------------------------------\n'
        return info

common = Common()


def pre_start():
    if gevent.__version__ < '1.0':
        logging.warning("*NOTE*, please upgrade to gevent 1.1 as possible")

    if GAEProxyHandler.max_window != common.GAE_WINDOW:
        GAEProxyHandler.max_window = common.GAE_WINDOW
    if common.GAE_CACHESOCK:
        GAEProxyHandler.tcp_connection_cachesock = True
        GAEProxyHandler.ssl_connection_cachesock = True
    if common.GAE_KEEPALIVE:
        GAEProxyHandler.tcp_connection_cachesock = True
        GAEProxyHandler.tcp_connection_keepalive = True
        GAEProxyHandler.ssl_connection_cachesock = True
        GAEProxyHandler.ssl_connection_keepalive = True
    if common.IPLIST_PREDEFINED:
        GAEProxyHandler.iplist_predefined = set(common.IPLIST_PREDEFINED)
    if common.GAE_PAGESPEED and not common.GAE_OBFUSCATE:
        logging.critical("*NOTE*, [gae]pagespeed=1 requires [gae]obfuscate=1")
        sys.exit(-1)
    if common.GAE_SSLVERSION and not sysconfig.get_platform().startswith('macosx-'):
        GAEProxyHandler.ssl_version = getattr(ssl, 'PROTOCOL_%s' % common.GAE_SSLVERSION)
        GAEProxyHandler.openssl_context = SSLConnection.context_builder(common.GAE_SSLVERSION)
    if common.GAE_ENABLE and common.GAE_APPIDS[0] == 'goagent':
        logging.warning('please edit %s to add your appid to [gae] !', common.CONFIG_FILENAME)
    if common.GAE_ENABLE and common.GAE_MODE == 'http' and common.GAE_PASSWORD == '':
        logging.critical('to enable http mode, you should set %r [gae]password = <your_pass> and [gae]options = rc4', common.CONFIG_FILENAME)
        sys.exit(-1)
    if common.GAE_TRANSPORT:
        GAEProxyHandler.disable_transport_ssl = False
    if common.PAC_ENABLE:
        pac_ip = ProxyUtil.get_listen_ip() if common.PAC_IP in ('', '::', '0.0.0.0') else common.PAC_IP
        url = 'http://%s:%d/%s' % (pac_ip, common.PAC_PORT, common.PAC_FILE)
        spawn_later(600, urllib2.build_opener(urllib2.ProxyHandler({})).open, url)
    if not common.DNS_ENABLE:
        if not common.HTTP_DNS:
            common.HTTP_DNS = common.DNS_SERVERS[:]
        for dnsservers_ref in (common.HTTP_DNS, common.DNS_SERVERS):
            any(dnsservers_ref.insert(0, x) for x in [y for y in get_dnsserver_list() if y not in dnsservers_ref])
        GAEProxyHandler.dns_servers = common.HTTP_DNS
        GAEProxyHandler.dns_blacklist = common.DNS_BLACKLIST
    else:
        GAEProxyHandler.dns_servers = common.HTTP_DNS or common.DNS_SERVERS
        GAEProxyHandler.dns_blacklist = common.DNS_BLACKLIST
    RangeFetch.threads = common.AUTORANGE_THREADS
    RangeFetch.maxsize = common.AUTORANGE_MAXSIZE
    RangeFetch.bufsize = common.AUTORANGE_BUFSIZE
    RangeFetch.waitsize = common.AUTORANGE_WAITSIZE
    if True:
        GAEProxyHandler.handler_filters.insert(0, AutoRangeFilter(common.AUTORANGE_HOSTS, common.AUTORANGE_ENDSWITH, common.AUTORANGE_NOENDSWITH, common.AUTORANGE_MAXSIZE))
    if common.GAE_REGIONS:
        GAEProxyHandler.handler_filters.insert(0, DirectRegionFilter(common.GAE_REGIONS))
    if common.HOST_MAP or common.HOST_POSTFIX_MAP or common.HOSTPORT_MAP or common.HOSTPORT_POSTFIX_MAP or common.URLRE_MAP:
        GAEProxyHandler.handler_filters.insert(0, HostsFilter(common.IPLIST_MAP, common.HOST_MAP, common.HOST_POSTFIX_MAP, common.HOSTPORT_MAP, common.HOSTPORT_POSTFIX_MAP, common.URLRE_MAP))
    if common.CRLF_SITES:
        GAEProxyHandler.handler_filters.insert(0, CRLFSitesFilter(common.CRLF_SITES, common.NOCRLF_SITES))
    if common.URLREWRITE_MAP:
        GAEProxyHandler.handler_filters.insert(0, URLRewriteFilter(common.URLREWRITE_MAP, common.FORCEHTTPS_SITES, common.NOFORCEHTTPS_SITES))
    if common.FAKEHTTPS_SITES:
        GAEProxyHandler.handler_filters.insert(0, FakeHttpsFilter(common.FAKEHTTPS_SITES, common.NOFAKEHTTPS_SITES))
    if common.FORCEHTTPS_SITES:
        GAEProxyHandler.handler_filters.insert(0, ForceHttpsFilter(common.FORCEHTTPS_SITES, common.NOFORCEHTTPS_SITES))
    if common.WITHGAE_SITES or common.WITHPHP_SITES or common.WITHVPS_SITES:
        GAEProxyHandler.handler_filters.insert(0, WithGAEFilter(common.WITHGAE_SITES, common.WITHPHP_SITES, common.WITHVPS_SITES))
    if common.USERAGENT_ENABLE:
        GAEProxyHandler.handler_filters.insert(0, UserAgentFilter(common.USERAGENT_STRING))
    if common.LISTEN_USERNAME:
        GAEProxyHandler.handler_filters.insert(0, AuthFilter(common.LISTEN_USERNAME, common.LISTEN_PASSWORD))



def main():
    global __file__
    __file__ = os.path.abspath(__file__)
    if os.path.islink(__file__):
        __file__ = getattr(os, 'readlink', lambda x: x)(__file__)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    pre_start()


    logging.info(common.info())

    if common.CONTROL_ENABLE:
        control_server = LocalProxyServer((common.CONTROL_IP, common.CONTROL_PORT), web_control.RemoteContralServerHandler)
        p = threading.Thread(target=control_server.serve_forever)
        p.setDaemon(True)
        p.start()

    if common.PHP_ENABLE:

        host, port = common.PHP_LISTEN.split(':')
        HandlerClass = PHPProxyHandler if not common.PROXY_ENABLE else ProxyPHPProxyHandler
        HandlerClass.handler_plugins['php'] = PHPFetchPlugin(common.PHP_FETCHSERVERS, common.PHP_PASSWORD, common.PHP_VALIDATE)
        php_server = LocalProxyServer((host, int(port)), HandlerClass)
        thread.start_new_thread(php_server.serve_forever, tuple())

        CertUtil.init_ca()

    while common.keep_run:
        gevent.sleep(1)

    sys.exit(0)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
