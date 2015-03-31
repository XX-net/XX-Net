#!/usr/bin/env python
# coding:utf-8

__version__ = '1.1'

import sys
import os
import glob
import errno
import time
import struct
import collections
import binascii
import zlib
import itertools
import re
import fnmatch
import io
import random
import base64
import string
import hashlib
import threading
import thread
import socket
import ssl
import select
import Queue
import SocketServer
import BaseHTTPServer
import httplib
import urllib
import urllib2
import urlparse
import OpenSSL
import dnslib
import logging

from cert_util import CertUtil

gevent = sys.modules.get('gevent') or logging.warn('please enable gevent.')


try:
    from Crypto.Cipher.ARC4 import new as RC4Cipher
except ImportError:
    #logging.warn('Load Crypto.Cipher.ARC4 Failed, Use Pure Python Instead.')
    class RC4Cipher(object):
        def __init__(self, key):
            x = 0
            box = range(256)
            for i, y in enumerate(box):
                x = (x + y + ord(key[i % len(key)])) & 0xff
                box[i], box[x] = box[x], y
            self.__box = box
            self.__x = 0
            self.__y = 0
        def encrypt(self, data):
            out = []
            out_append = out.append
            x = self.__x
            y = self.__y
            box = self.__box
            for char in data:
                x = (x + 1) & 0xff
                y = (y + box[x]) & 0xff
                box[x], box[y] = box[y], box[x]
                out_append(chr(ord(char) ^ box[(box[x] + box[y]) & 0xff]))
            self.__x = x
            self.__y = y
            return ''.join(out)


class XORCipher(object):
    """XOR Cipher Class"""
    def __init__(self, key):
        self.__key_gen = itertools.cycle([ord(x) for x in key]).next
        self.__key_xor = lambda s: ''.join(chr(ord(x) ^ self.__key_gen()) for x in s)
        if len(key) == 1:
            try:
                from Crypto.Util.strxor import strxor_c
                c = ord(key)
                self.__key_xor = lambda s: strxor_c(s, c)
            except ImportError:
                #logging.debug('Load Crypto.Util.strxor Failed, Use Pure Python Instead.\n')
                pass

    def encrypt(self, data):
        return self.__key_xor(data)


class CipherFileObject(object):
    """fileobj wrapper for cipher"""
    def __init__(self, fileobj, cipher):
        self.__fileobj = fileobj
        self.__cipher = cipher

    def __getattr__(self, attr):
        if attr not in ('__fileobj', '__cipher'):
            return getattr(self.__fileobj, attr)

    def read(self, size=-1):
        return self.__cipher.encrypt(self.__fileobj.read(size))


class LRUCache(object):
    """http://pypi.python.org/pypi/lru/"""

    def __init__(self, max_items=100):
        self.cache = {}
        self.key_order = []
        self.max_items = max_items

    def __setitem__(self, key, value):
        self.cache[key] = value
        self._mark(key)

    def __getitem__(self, key):
        value = self.cache[key]
        self._mark(key)
        return value

    def __contains__(self, key):
        return key in self.cache

    def __len__(self):
        return len(self.cache)

    def _mark(self, key):
        if key in self.key_order:
            self.key_order.remove(key)
        self.key_order.insert(0, key)
        if len(self.key_order) > self.max_items:
            index = self.max_items // 2
            delitem = self.cache.__delitem__
            key_order = self.key_order
            any(delitem(key_order[x]) for x in xrange(index, len(key_order)))
            self.key_order = self.key_order[:index]

    def clear(self):
        self.cache = {}
        self.key_order = []



class SSLConnection(object):
    """OpenSSL Connection Wapper"""

    def __init__(self, context, sock):
        self._context = context
        self._sock = sock
        self._connection = OpenSSL.SSL.Connection(context, sock)
        self._makefile_refs = 0

    def __getattr__(self, attr):
        if attr not in ('_context', '_sock', '_connection', '_makefile_refs'):
            return getattr(self._connection, attr)

    def __iowait(self, io_func, *args, **kwargs):
        timeout = self._sock.gettimeout() or 0.1
        fd = self._sock.fileno()
        while True:
            try:
                return io_func(*args, **kwargs)
            except (OpenSSL.SSL.WantReadError, OpenSSL.SSL.WantX509LookupError):
                sys.exc_clear()
                _, _, errors = select.select([fd], [], [fd], timeout)
                if errors:
                    break
            except OpenSSL.SSL.WantWriteError:
                sys.exc_clear()
                _, _, errors = select.select([], [fd], [fd], timeout)
                if errors:
                    break

    def accept(self):
        sock, addr = self._sock.accept()
        client = OpenSSL.SSL.Connection(sock._context, sock)
        return client, addr

    def do_handshake(self):
        self.__iowait(self._connection.do_handshake)

    def connect(self, *args, **kwargs):
        return self.__iowait(self._connection.connect, *args, **kwargs)

    def __send(self, data, flags=0):
        try:
            return self.__iowait(self._connection.send, data, flags)
        except OpenSSL.SSL.SysCallError as e:
            if e[0] == -1 and not data:
                # errors when writing empty strings are expected and can be ignored
                return 0
            raise

    def __send_memoryview(self, data, flags=0):
        if hasattr(data, 'tobytes'):
            data = data.tobytes()
        return self.__send(data, flags)

    send = __send if sys.version_info >= (2, 7, 5) else __send_memoryview

    def recv(self, bufsiz, flags=0):
        pending = self._connection.pending()
        if pending:
            return self._connection.recv(min(pending, bufsiz))
        try:
            return self.__iowait(self._connection.recv, bufsiz, flags)
        except OpenSSL.SSL.ZeroReturnError:
            return ''
        except OpenSSL.SSL.SysCallError as e:
            if e[0] == -1 and 'Unexpected EOF' in e[1]:
                # errors when reading empty strings are expected and can be ignored
                return ''
            raise

    def read(self, bufsiz, flags=0):
        return self.recv(bufsiz, flags)

    def write(self, buf, flags=0):
        return self.sendall(buf, flags)

    def close(self):
        if self._makefile_refs < 1:
            self._connection = None
            if self._sock:
                socket.socket.close(self._sock)
        else:
            self._makefile_refs -= 1

    def makefile(self, mode='r', bufsize=-1):
        self._makefile_refs += 1
        return socket._fileobject(self, mode, bufsize, close=True)

    @staticmethod
    def context_builder(ssl_version='SSLv23', ca_certs=None, cipher_suites=('ALL', '!aNULL', '!eNULL')):
        protocol_version = getattr(OpenSSL.SSL, '%s_METHOD' % ssl_version)
        ssl_context = OpenSSL.SSL.Context(protocol_version)
        if ca_certs:
            ssl_context.load_verify_locations(os.path.abspath(ca_certs))
            ssl_context.set_verify(OpenSSL.SSL.VERIFY_PEER, lambda c, x, e, d, ok: ok)
        else:
            ssl_context.set_verify(OpenSSL.SSL.VERIFY_NONE, lambda c, x, e, d, ok: ok)
        ssl_context.set_cipher_list(':'.join(cipher_suites))
        return ssl_context


def openssl_set_session_cache_mode(context, mode):
    assert isinstance(context, OpenSSL.SSL.Context)
    try:
        import ctypes
        SSL_CTRL_SET_SESS_CACHE_MODE = 44
        SESS_CACHE_OFF = 0x0
        SESS_CACHE_CLIENT = 0x1
        SESS_CACHE_SERVER = 0x2
        SESS_CACHE_BOTH = 0x3
        c_mode = {'off':SESS_CACHE_OFF, 'client':SESS_CACHE_CLIENT, 'server':SESS_CACHE_SERVER, 'both':SESS_CACHE_BOTH}[mode.lower()]
        if hasattr(context, 'set_session_cache_mode'):
            context.set_session_cache_mode(c_mode)
        elif OpenSSL.__version__ == '0.13':
            # http://bazaar.launchpad.net/~exarkun/pyopenssl/release-0.13/view/head:/OpenSSL/ssl/context.h#L27
            c_context = ctypes.c_void_p.from_address(id(context)+ctypes.sizeof(ctypes.c_int)+ctypes.sizeof(ctypes.c_voidp))
            if os.name == 'nt':
                # https://github.com/openssl/openssl/blob/92c78463720f71e47c251ffa58493e32cd793e13/ssl/ssl.h#L884
                ctypes.c_int.from_address(c_context.value+ctypes.sizeof(ctypes.c_voidp)*7+ctypes.sizeof(ctypes.c_ulong)).value = c_mode
            else:
                import ctypes.util
                # FIXME
                # ctypes.cdll.LoadLibrary(ctypes.util.find_library('ssl')).SSL_CTX_ctrl(c_context, SSL_CTRL_SET_SESS_CACHE_MODE, c_mode, None)
    except Exception as e:
        logging.warning('openssl_set_session_cache_mode failed: %r', e)


class ProxyUtil(object):
    """ProxyUtil module, based on urllib2"""

    @staticmethod
    def parse_proxy(proxy):
        return urllib2._parse_proxy(proxy)

    @staticmethod
    def get_system_proxy():
        proxies = urllib2.getproxies()
        return proxies.get('https') or proxies.get('http') or {}

    @staticmethod
    def get_listen_ip():
        listen_ip = '127.0.0.1'
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(('8.8.8.8', 53))
            listen_ip = sock.getsockname()[0]
        except StandardError:
            pass
        finally:
            if sock:
                sock.close()
        return listen_ip


def inflate(data):
    return zlib.decompress(data, -zlib.MAX_WBITS)


def deflate(data):
    return zlib.compress(data)[2:-4]


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
    <tr><td bgcolor=#3366cc><font face=arial,sans-serif color=#ffffff><b>Message From LocalProxy</b></td></tr>
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


def parse_hostport(host, default_port=80):
    m = re.match(r'(.+)[#](\d+)$', host)
    if m:
        return m.group(1).strip('[]'), int(m.group(2))
    else:
        return host.strip('[]'), default_port


def dnslib_resolve_over_udp(query, dnsservers, timeout, **kwargs):
    """
    http://gfwrev.blogspot.com/2009/11/gfwdns.html
    http://zh.wikipedia.org/wiki/%E5%9F%9F%E5%90%8D%E6%9C%8D%E5%8A%A1%E5%99%A8%E7%BC%93%E5%AD%98%E6%B1%A1%E6%9F%93
    http://support.microsoft.com/kb/241352
    https://gist.github.com/klzgrad/f124065c0616022b65e5
    """
    if not isinstance(query, (basestring, dnslib.DNSRecord)):
        raise TypeError('query argument requires string/DNSRecord')
    blacklist = kwargs.get('blacklist', ())
    blacklist_prefix = tuple(x for x in blacklist if x.endswith('.'))
    turstservers = kwargs.get('turstservers', ())
    dns_v4_servers = [x for x in dnsservers if ':' not in x]
    dns_v6_servers = [x for x in dnsservers if ':' in x]
    sock_v4 = sock_v6 = None
    socks = []
    if dns_v4_servers:
        sock_v4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socks.append(sock_v4)
    if dns_v6_servers:
        sock_v6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        socks.append(sock_v6)
    timeout_at = time.time() + timeout
    try:
        for _ in xrange(4):
            try:
                for dnsserver in dns_v4_servers:
                    if isinstance(query, basestring):
                        if dnsserver in ('8.8.8.8', '8.8.4.4'):
                            query = '.'.join(x[:-1] + x[-1].upper() for x in query.split('.')).title()
                        query = dnslib.DNSRecord(q=dnslib.DNSQuestion(query))
                    query_data = query.pack()
                    if query.q.qtype == 1 and dnsserver in ('8.8.8.8', '8.8.4.4'):
                        query_data = query_data[:-5] + '\xc0\x04' + query_data[-4:]
                    sock_v4.sendto(query_data, parse_hostport(dnsserver, 53))
                for dnsserver in dns_v6_servers:
                    if isinstance(query, basestring):
                        query = dnslib.DNSRecord(q=dnslib.DNSQuestion(query, qtype=dnslib.QTYPE.AAAA))
                    query_data = query.pack()
                    sock_v6.sendto(query_data, parse_hostport(dnsserver, 53))
                while time.time() < timeout_at:
                    ins, _, _ = select.select(socks, [], [], 0.1)
                    for sock in ins:
                        reply_data, reply_address = sock.recvfrom(512)
                        reply_server = reply_address[0]
                        record = dnslib.DNSRecord.parse(reply_data)
                        iplist = [str(x.rdata) for x in record.rr if x.rtype in (1, 28, 255)]
                        if any(x in blacklist or x.startswith(blacklist_prefix) for x in iplist):
                            logging.warning('qname=%r dnsservers=%r record bad iplist=%r', query.q.qname, dnsservers, iplist)
                        elif record.header.rcode and not iplist and reply_server in turstservers:
                            logging.info('qname=%r trust reply_server=%r record rcode=%s', query.q.qname, reply_server, record.header.rcode)
                            return record
                        elif iplist:
                            logging.debug('qname=%r reply_server=%r record iplist=%s', query.q.qname, reply_server, iplist)
                            return record
                        else:
                            logging.debug('qname=%r reply_server=%r record null iplist=%s', query.q.qname, reply_server, iplist)
                            continue
            except socket.error as e:
                logging.warning('handle dns query=%s socket: %r', query, e)
        raise socket.gaierror(11004, 'getaddrinfo %r from %r failed' % (query, dnsservers))
    finally:
        for sock in socks:
            sock.close()


def dnslib_resolve_over_tcp(query, dnsservers, timeout, **kwargs):
    """dns query over tcp"""
    if not isinstance(query, (basestring, dnslib.DNSRecord)):
        raise TypeError('query argument requires string/DNSRecord')
    blacklist = kwargs.get('blacklist', ())
    blacklist_prefix = tuple(x for x in blacklist if x.endswith('.'))
    def do_resolve(query, dnsserver, timeout, queobj):
        if isinstance(query, basestring):
            qtype = dnslib.QTYPE.AAAA if ':' in dnsserver else dnslib.QTYPE.A
            query = dnslib.DNSRecord(q=dnslib.DNSQuestion(query, qtype=qtype))
        query_data = query.pack()
        sock_family = socket.AF_INET6 if ':' in dnsserver else socket.AF_INET
        sock = socket.socket(sock_family)
        rfile = None
        try:
            sock.settimeout(timeout or None)
            sock.connect(parse_hostport(dnsserver, 53))
            sock.send(struct.pack('>h', len(query_data)) + query_data)
            rfile = sock.makefile('r', 1024)
            reply_data_length = rfile.read(2)
            if len(reply_data_length) < 2:
                raise socket.gaierror(11004, 'getaddrinfo %r from %r failed' % (query.q.qname, dnsserver))
            reply_data = rfile.read(struct.unpack('>h', reply_data_length)[0])
            record = dnslib.DNSRecord.parse(reply_data)
            iplist = [str(x.rdata) for x in record.rr if x.rtype in (1, 28, 255)]
            if any(x in blacklist or x.startswith(blacklist_prefix) for x in iplist):
                logging.debug('qname=%r dnsserver=%r record bad iplist=%r', query.q.qname, dnsserver, iplist)
                raise socket.gaierror(11004, 'getaddrinfo %r from %r failed' % (query, dnsserver))
            else:
                logging.debug('qname=%r dnsserver=%r record iplist=%s', query.q.qname, dnsserver, iplist)
                queobj.put(record)
        except socket.error as e:
            logging.debug('qname=%r dnsserver=%r failed %r', query.q.qname, dnsserver, e)
            queobj.put(e)
        finally:
            if rfile:
                rfile.close()
            sock.close()
    queobj = Queue.Queue()
    for dnsserver in dnsservers:
        thread.start_new_thread(do_resolve, (query, dnsserver, timeout, queobj))
    for i in range(len(dnsservers)):
        try:
            result = queobj.get(timeout)
        except Queue.Empty:
            raise socket.gaierror(11004, 'getaddrinfo %r from %r failed' % (query, dnsservers))
        if result and not isinstance(result, Exception):
            return result
        elif i == len(dnsservers) - 1:
            logging.warning('dnslib_resolve_over_tcp %r with %s return %r', query, dnsservers, result)
    raise socket.gaierror(11004, 'getaddrinfo %r from %r failed' % (query, dnsservers))


def dnslib_record2iplist(record):
    """convert dnslib.DNSRecord to iplist"""
    assert isinstance(record, dnslib.DNSRecord)
    iplist = [x for x in (str(r.rdata) for r in record.rr) if re.match(r'^\d+\.\d+\.\d+\.\d+$', x) or ':' in x]
    return iplist


def get_dnsserver_list():
    if os.name == 'nt':
        import ctypes
        import ctypes.wintypes
        DNS_CONFIG_DNS_SERVER_LIST = 6
        buf = ctypes.create_string_buffer(2048)
        ctypes.windll.dnsapi.DnsQueryConfig(DNS_CONFIG_DNS_SERVER_LIST, 0, None, None, ctypes.byref(buf), ctypes.byref(ctypes.wintypes.DWORD(len(buf))))
        ipcount = struct.unpack('I', buf[0:4])[0]
        iplist = [socket.inet_ntoa(buf[i:i+4]) for i in xrange(4, ipcount*4+4, 4)]
        return iplist
    elif os.path.isfile('/etc/resolv.conf'):
        with open('/etc/resolv.conf', 'rb') as fp:
            return re.findall(r'(?m)^nameserver\s+(\S+)', fp.read())
    else:
        logging.warning("get_dnsserver_list failed: unsupport platform '%s-%s'", sys.platform, os.name)
        return []


def spawn_later(seconds, target, *args, **kwargs):
    def wrap(*args, **kwargs):
        time.sleep(seconds)
        return target(*args, **kwargs)
    return thread.start_new_thread(wrap, args, kwargs)


def is_clienthello(data):
    if len(data) < 20:
        return False
    if data.startswith('\x16\x03'):
        # TLSv12/TLSv11/TLSv1/SSLv3
        length, = struct.unpack('>h', data[3:5])
        return len(data) == 5 + length
    elif data[0] == '\x80' and data[2:4] == '\x01\x03':
        # SSLv23
        return len(data) == 2 + ord(data[1])
    else:
        return False


def extract_sni_name(packet):
    if packet.startswith('\x16\x03'):
        stream = io.BytesIO(packet)
        stream.read(0x2b)
        session_id_length = ord(stream.read(1))
        stream.read(session_id_length)
        cipher_suites_length, = struct.unpack('>h', stream.read(2))
        stream.read(cipher_suites_length+2)
        extensions_length, = struct.unpack('>h', stream.read(2))
        # extensions = {}
        while True:
            data = stream.read(2)
            if not data:
                break
            etype, = struct.unpack('>h', data)
            elen, = struct.unpack('>h', stream.read(2))
            edata = stream.read(elen)
            if etype == 0:
                server_name = edata[5:]
                return server_name

def random_hostname():
    word = ''.join(random.choice(('bcdfghjklmnpqrstvwxyz', 'aeiou')[x&1]) for x in xrange(random.randint(5, 10)))
    gltd = random.choice(['org', 'com', 'net', 'gov', 'cn'])
    return 'www.%s.%s' % (word, gltd)


def get_uptime():
    if os.name == 'nt':
        import ctypes
        try:
            tick = ctypes.windll.kernel32.GetTickCount64()
        except AttributeError:
            tick = ctypes.windll.kernel32.GetTickCount()
        return tick / 1000.0
    elif os.path.isfile('/proc/uptime'):
        with open('/proc/uptime', 'rb') as fp:
            uptime = fp.readline().strip().split()[0].strip()
            return float(uptime)
    elif any(os.path.isfile(os.path.join(x, 'uptime')) for x in os.environ['PATH'].split(os.pathsep)):
        # http://www.opensource.apple.com/source/lldb/lldb-69/test/pexpect-2.4/examples/uptime.py
        pattern = r'up\s+(.*?),\s+([0-9]+) users?,\s+load averages?: ([0-9]+\.[0-9][0-9]),?\s+([0-9]+\.[0-9][0-9]),?\s+([0-9]+\.[0-9][0-9])'
        output = os.popen('uptime').read()
        duration, _, _, _, _ = re.search(pattern, output).groups()
        days, hours, mins = 0, 0, 0
        if 'day' in duration:
            m = re.search(r'([0-9]+)\s+day', duration)
            days = int(m.group(1))
        if ':' in duration:
            m = re.search(r'([0-9]+):([0-9]+)', duration)
            hours = int(m.group(1))
            mins = int(m.group(2))
        if 'min' in duration:
            m = re.search(r'([0-9]+)\s+min', duration)
            mins = int(m.group(1))
        return days * 86400 + hours * 3600 + mins * 60
    else:
        #TODO: support other platforms
        return None




def forward_socket(local, remote, timeout, bufsize):
    """forward socket"""
    def __io_copy(dest, source, timeout):
        try:
            dest.settimeout(timeout)
            source.settimeout(timeout)
            while 1:
                data = source.recv(bufsize)
                if not data:
                    break
                dest.sendall(data)
        except socket.timeout:
            pass
        except (socket.error, ssl.SSLError, OpenSSL.SSL.Error) as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.ENOTCONN, errno.EPIPE):
                raise
            if e.args[0] in (errno.EBADF,):
                return
        finally:
            for sock in (dest, source):
                try:
                    sock.close()
                except StandardError:
                    pass
    thread.start_new_thread(__io_copy, (remote.dup(), local.dup(), timeout))
    __io_copy(local, remote, timeout)


class LocalProxyServer(SocketServer.ThreadingTCPServer):
    """Local Proxy Server"""
    request_queue_size = 1024
    allow_reuse_address = True
    daemon_threads = True

    def close_request(self, request):
        try:
            request.close()
        except StandardError:
            pass

    def finish_request(self, request, client_address):
        try:
            self.RequestHandlerClass(request, client_address, self)
        except (socket.error, ssl.SSLError, OpenSSL.SSL.Error) as e:
            if e[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.EPIPE):
                logging.error("error no:%d", e[0])
                raise

    def handle_error(self, *args):
        """make ThreadingTCPServer happy"""
        exc_info = sys.exc_info()
        error = exc_info and len(exc_info) and exc_info[1]
        if isinstance(error, (socket.error, ssl.SSLError, OpenSSL.SSL.Error)) and len(error.args) > 1 and 'bad write retry' in error.args[1]:
            exc_info = error = None
        else:
            del exc_info, error
            SocketServer.ThreadingTCPServer.handle_error(self, *args)


class BaseHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """Base HTTP Request Handler"""
    def gethostbyname2(self, hostname):
        return socket.gethostbyname_ex(hostname)[-1]

    def create_tcp_connection(self, hostname, port, timeout, **kwargs):
        sock = socket.create_connection((hostname, port), timeout)
        data = kwargs.get('client_hello')
        if data:
            sock.send(data)
        return sock

    def create_ssl_connection(self, hostname, port, timeout, **kwargs):
        sock = self.create_tcp_connection(hostname, port, timeout, **kwargs)
        ssl_sock = ssl.wrap_socket(sock)
        return ssl_sock

    def create_http_request(self, method, url, headers, body, timeout, **kwargs):
        scheme, netloc, path, query, _ = urlparse.urlsplit(url)
        if netloc.rfind(':') <= netloc.rfind(']'):
            # no port number
            host = netloc
            port = 443 if scheme == 'https' else 80
        else:
            host, _, port = netloc.rpartition(':')
            port = int(port)
        if query:
            path += '?' + query
        if 'Host' not in headers:
            headers['Host'] = host
        if body and 'Content-Length' not in headers:
            headers['Content-Length'] = str(len(body))
        ConnectionType = httplib.HTTPSConnection if scheme == 'https' else httplib.HTTPConnection
        connection = ConnectionType(netloc, timeout=timeout)
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        return response


class BaseFetchPlugin(object):
    """abstract fetch plugin"""
    def __init__(self, *args, **kwargs):
        pass

    def handle(self, handler, **kwargs):
        raise NotImplementedError


class MockFetchPlugin(BaseFetchPlugin):
    """mock fetch plugin"""
    def handle(self, handler, status=400, headers={}, body=''):
        """mock response"""
        logging.info('%s "MOCK %s %s %s" %d %d', handler.address_string(), handler.command, handler.path, handler.protocol_version, status, len(body))
        headers = dict((k.title(), v) for k, v in headers.items())
        if 'Transfer-Encoding' in headers:
            del headers['Transfer-Encoding']
        if 'Content-Length' not in headers:
            headers['Content-Length'] = len(body)
        if 'Connection' not in headers:
            headers['Connection'] = 'close'
        handler.send_response(status)
        for key, value in headers.items():
            handler.send_header(key, value)
        handler.end_headers()
        handler.wfile.write(body)


class StripPlugin(BaseFetchPlugin):
    """strip fetch plugin"""

    def __init__(self, ssl_version='SSLv23', ciphers='ALL:!aNULL:!eNULL', cache_size=128, session_cache=True):
        self.ssl_method = getattr(ssl, 'PROTOCOL_%s' % ssl_version)
        self.ciphers = ciphers

    def do_ssl_handshake(self, handler):
        "do_ssl_handshake with ssl"
        certfile = CertUtil.get_cert(handler.host)
        ssl_sock = ssl.wrap_socket(handler.connection, keyfile=certfile, certfile=certfile, server_side=True, ssl_version=self.ssl_method, ciphers=self.ciphers)
        handler.connection = ssl_sock
        handler.rfile = handler.connection.makefile('rb', handler.bufsize)
        handler.wfile = handler.connection.makefile('wb', 0)
        handler.scheme = 'https'

    def handle(self, handler, do_ssl_handshake=True):
        """strip connect"""
        logging.info('%s "STRIP %s %s:%d %s" - -', handler.address_string(), handler.command, handler.host, handler.port, handler.protocol_version)
        handler.send_response(200)
        handler.end_headers()
        if do_ssl_handshake:
            try:
                self.do_ssl_handshake(handler)
            except (socket.error, ssl.SSLError, OpenSSL.SSL.Error) as e:
                if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET) or (e[0] == -1 and 'Unexpected EOF' in e[1]):
                    logging.exception('ssl.wrap_socket(connection=%r) failed: %s', handler.connection, e)
                return
        try:
            handler.raw_requestline = handler.rfile.readline(65537)
            if len(handler.raw_requestline) > 65536:
                handler.requestline = ''
                handler.request_version = ''
                handler.command = ''
                handler.send_error(414)
                handler.wfile.close()
                return
            if not handler.raw_requestline:
                handler.close_connection = 1
                return
            if not handler.parse_request():
                handler.send_error(400)
                handler.wfile.close()
                return
        except (socket.error, ssl.SSLError, OpenSSL.SSL.Error) as e:
            if e.args[0] in (errno.ECONNABORTED, errno.ECONNRESET, errno.EPIPE):
                handler.close_connection = 1
                return
            else:
                raise
        try:
            handler.do_METHOD()
        except (socket.error, ssl.SSLError, OpenSSL.SSL.Error) as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ETIMEDOUT, errno.EPIPE):
                raise

class StripPluginEx(StripPlugin):
    """strip fetch plugin"""

    def __init__(self, ssl_version='SSLv23', ciphers='ALL:!aNULL:!eNULL', cache_size=128, session_cache=True):
        self.ssl_method = getattr(OpenSSL.SSL, '%s_METHOD' % ssl_version)
        self.ciphers = ciphers
        self.ssl_context_cache = LRUCache(cache_size*2)
        self.ssl_session_cache = session_cache

    def get_ssl_context_by_hostname(self, hostname):
        try:
            return self.ssl_context_cache[hostname]
        except LookupError:
            context = OpenSSL.SSL.Context(self.ssl_method)
            certfile = CertUtil.get_cert(hostname)
            if certfile in self.ssl_context_cache:
                context = self.ssl_context_cache[hostname] = self.ssl_context_cache[certfile]
                return context
            with open(certfile, 'rb') as fp:
                pem = fp.read()
                context.use_certificate(OpenSSL.crypto.load_certificate(OpenSSL.SSL.FILETYPE_PEM, pem))
                context.use_privatekey(OpenSSL.crypto.load_privatekey(OpenSSL.SSL.FILETYPE_PEM, pem))
            if self.ciphers:
                context.set_cipher_list(self.ciphers)
            self.ssl_context_cache[hostname] = self.ssl_context_cache[certfile] = context
            if self.ssl_session_cache:
                openssl_set_session_cache_mode(context, 'server')
            return context

    def do_ssl_handshake(self, handler):
        "do_ssl_handshake with OpenSSL"
        ssl_sock = SSLConnection(self.get_ssl_context_by_hostname(handler.host), handler.connection)
        ssl_sock.set_accept_state()
        ssl_sock.do_handshake()
        handler.connection = ssl_sock
        handler.rfile = handler.connection.makefile('rb', handler.bufsize)
        handler.wfile = handler.connection.makefile('wb', 0)
        handler.scheme = 'https'


class DirectFetchPlugin(BaseFetchPlugin):
    """direct fetch plugin"""
    connect_timeout = 4
    read_timeout = 16
    max_retry = 3

    def handle(self, handler, **kwargs):
        if handler.command != 'CONNECT':
            return self.handle_method(handler, kwargs)
        else:
            return self.handle_connect(handler, kwargs)

    def handle_method(self, handler, kwargs):
        method = handler.command
        if handler.path.lower().startswith(('http://', 'https://', 'ftp://')):
            url = handler.path
        else:
            url = 'http://%s%s' % (handler.headers['Host'], handler.path)
        headers = dict((k.title(), v) for k, v in handler.headers.items())
        body = handler.body
        response = None
        try:
            response = handler.create_http_request(method, url, headers, body, timeout=self.connect_timeout, read_timeout=self.read_timeout, **kwargs)
            logging.info('%s "DIRECT %s %s %s" %s %s', handler.address_string(), handler.command, url, handler.protocol_version, response.status, response.getheader('Content-Length', '-'))
            response_headers = dict((k.title(), v) for k, v in response.getheaders())
            handler.send_response(response.status)
            for key, value in response.getheaders():
                handler.send_header(key, value)
            handler.end_headers()
            if handler.command == 'HEAD' or response.status in (204, 304):
                response.close()
                return
            need_chunked = 'Transfer-Encoding' in response_headers
            while True:
                data = response.read(8192)
                if not data:
                    if need_chunked:
                        handler.wfile.write('0\r\n\r\n')
                    break
                if need_chunked:
                    handler.wfile.write('%x\r\n' % len(data))
                handler.wfile.write(data)
                if need_chunked:
                    handler.wfile.write('\r\n')
                del data
        except (ssl.SSLError, socket.timeout, socket.error):
            if response:
                if response.fp and response.fp._sock:
                    response.fp._sock.close()
                response.close()
        finally:
            if response:
                response.close()

    def handle_connect(self, handler, kwargs):
        """forward socket"""
        host = handler.host
        port = handler.port
        local = handler.connection
        remote = None
        handler.send_response(200)
        handler.end_headers()
        handler.close_connection = 1
        data = local.recv(1024)
        if not data:
            local.close()
            return
        data_is_clienthello = is_clienthello(data)
        if data_is_clienthello:
            kwargs['client_hello'] = data
        for i in xrange(self.max_retry):
            try:
                remote = handler.create_tcp_connection(host, port, self.connect_timeout, **kwargs)
                if not data_is_clienthello and remote and not isinstance(remote, Exception):
                    remote.sendall(data)
                break
            except StandardError as e:
                logging.exception('%s "FORWARD %s %s:%d %s" %r', handler.address_string(), handler.command, host, port, handler.protocol_version, e)
                if hasattr(remote, 'close'):
                    remote.close()
                if i == self.max_retry - 1:
                    raise
        logging.info('%s "FORWARD %s %s:%d %s" - -', handler.address_string(), handler.command, host, port, handler.protocol_version)
        if hasattr(remote, 'fileno'):
            # reset timeout default to avoid long http upload failure, but it will delay timeout retry :(
            remote.settimeout(None)
        data = data_is_clienthello and getattr(remote, 'data', None)
        if data:
            del remote.data
            local.sendall(data)
        forward_socket(local, remote, 60, bufsize=256*1024)


class BaseProxyHandlerFilter(object):
    """base proxy handler filter"""
    def filter(self, handler):
        raise NotImplementedError


class SimpleProxyHandlerFilter(BaseProxyHandlerFilter):
    """simple proxy handler filter"""
    def filter(self, handler):
        return 'direct', {}


class MIMTProxyHandlerFilter(BaseProxyHandlerFilter):
    """mimt proxy handler filter"""
    def filter(self, handler):
        if handler.command == 'CONNECT':
            return 'strip', {}
        else:
            return 'direct', {}


class DirectRegionFilter(BaseProxyHandlerFilter):
    """direct region filter"""
    region_cache = LRUCache(16*1024)

    def __init__(self, regions):
        self.regions = set(regions)
        try:
            import pygeoip
            self.geoip = pygeoip.GeoIP(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GeoIP.dat'))
        except StandardError as e:
            logging.error('DirectRegionFilter init pygeoip failed: %r', e)
            sys.exit(-1)

    def get_country_code(self, hostname, dnsservers):
        """http://dev.maxmind.com/geoip/legacy/codes/iso3166/"""
        try:
            return self.region_cache[hostname]
        except KeyError:
            pass
        try:
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', hostname) or ':' in hostname:
                iplist = [hostname]
            elif dnsservers:
                iplist = dnslib_record2iplist(dnslib_resolve_over_udp(hostname, dnsservers, timeout=2))
            else:
                iplist = socket.gethostbyname_ex(hostname)[-1]
            if iplist[0].startswith(('127.', '192.168.', '10.')):
                country_code = 'LOCAL'
            else:
                country_code = self.geoip.country_code_by_addr(iplist[0])
        except StandardError as e:
            logging.warning('DirectRegionFilter cannot determine region for hostname=%r %r', hostname, e)
            country_code = ''
        self.region_cache[hostname] = country_code
        return country_code

    def filter(self, handler):
        country_code = self.get_country_code(handler.host, handler.dns_servers)
        if country_code in self.regions:
            return 'direct', {}


class AuthFilter(BaseProxyHandlerFilter):
    """authorization filter"""
    auth_info = "Proxy authentication required"""
    white_list = set(['127.0.0.1'])

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def check_auth_header(self, auth_header):
        method, _, auth_data = auth_header.partition(' ')
        if method == 'Basic':
            username, _, password = base64.b64decode(auth_data).partition(':')
            if username == self.username and password == self.password:
                return True
        return False

    def filter(self, handler):
        if self.white_list and handler.client_address[0] in self.white_list:
            return None
        auth_header = handler.headers.get('Proxy-Authorization') or getattr(handler, 'auth_header', None)
        if auth_header and self.check_auth_header(auth_header):
            handler.auth_header = auth_header
        else:
            headers = {'Access-Control-Allow-Origin': '*',
                       'Proxy-Authenticate': 'Basic realm="%s"' % self.auth_info,
                       'Content-Length': '0',
                       'Connection': 'keep-alive'}
            return 'mock', {'status': 407, 'headers': headers, 'body': ''}


class UserAgentFilter(BaseProxyHandlerFilter):
    """user agent filter"""
    def __init__(self, user_agent):
        self.user_agent = user_agent

    def filter(self, handler):
        handler.headers['User-Agent'] = self.user_agent


class ForceHttpsFilter(BaseProxyHandlerFilter):
    """force https filter"""
    def __init__(self, forcehttps_sites, noforcehttps_sites):
        self.forcehttps_sites = tuple(forcehttps_sites)
        self.noforcehttps_sites = set(noforcehttps_sites)

    def filter(self, handler):
        if handler.command != 'CONNECT' and handler.host.endswith(self.forcehttps_sites) and handler.host not in self.noforcehttps_sites:
            if not handler.headers.get('Referer', '').startswith('https://') and not handler.path.startswith('https://'):
                logging.debug('ForceHttpsFilter metched %r %r', handler.path, handler.headers)
                headers = {'Location': handler.path.replace('http://', 'https://', 1), 'Content-Length': '0'}
                return 'mock', {'status': 301, 'headers': headers, 'body': ''}


class FakeHttpsFilter(BaseProxyHandlerFilter):
    """fake https filter"""
    def __init__(self, fakehttps_sites, nofakehttps_sites):
        self.fakehttps_sites = tuple(fakehttps_sites)
        self.nofakehttps_sites = set(nofakehttps_sites)

    def filter(self, handler):
        if handler.command == 'CONNECT' and handler.host.endswith(self.fakehttps_sites) and handler.host not in self.nofakehttps_sites:
            logging.debug('FakeHttpsFilter metched %r %r', handler.path, handler.headers)
            return 'strip', {}


class CRLFSitesFilter(BaseProxyHandlerFilter):
    """crlf sites filter"""
    def __init__(self, crlf_sites, nocrlf_sites):
        self.crlf_sites = tuple(crlf_sites)
        self.nocrlf_sites = set(nocrlf_sites)

    def filter(self, handler):
        if handler.command != 'CONNECT' and handler.scheme != 'https':
            if handler.host.endswith(self.crlf_sites) and handler.host not in self.nocrlf_sites:
                logging.debug('CRLFSitesFilter metched %r %r', handler.path, handler.headers)
                handler.close_connection = True
                return 'direct', {'crlf': True}


class URLRewriteFilter(BaseProxyHandlerFilter):
    """url rewrite filter"""
    def __init__(self, urlrewrite_map, forcehttps_sites, noforcehttps_sites):
        self.urlrewrite_map = {}
        for regex, repl in urlrewrite_map.items():
            mo = re.search(r'://([^/:]+)', regex)
            if not mo:
                logging.warning('URLRewriteFilter does not support regex: %r', regex)
                continue
            addr = mo.group(1).replace(r'\.', '.')
            mo = re.match(r'[\w\-\_\d\[\]\:]+', addr)
            if not mo:
                logging.warning('URLRewriteFilter does not support wildcard host: %r', addr)
            self.urlrewrite_map.setdefault(addr, []).append((re.compile(regex).search, repl))
        self.forcehttps_sites = tuple(forcehttps_sites)
        self.noforcehttps_sites = set(noforcehttps_sites)

    def filter(self, handler):
        if handler.host not in self.urlrewrite_map:
            return
        for match, repl in self.urlrewrite_map[handler.host]:
            mo = match(handler.path)
            if mo:
                logging.debug('URLRewriteFilter metched %r', handler.path)
                if repl.startswith('file://'):
                    return self.filter_localfile(handler, mo, repl)
                else:
                    return self.filter_redirect(handler, mo, repl)

    def filter_redirect(self, handler, mo, repl):
        for i, g in enumerate(mo.groups()):
            repl = repl.replace('$%d' % (i+1), urllib.unquote_plus(g))
        if repl.startswith('http://') and self.forcehttps_sites:
            hostname = urlparse.urlsplit(repl).hostname
            if hostname.endswith(self.forcehttps_sites) and hostname not in self.noforcehttps_sites:
                repl = 'https://%s' % repl[len('http://'):]
        headers = {'Location': repl, 'Content-Length': '0'}
        return 'mock', {'status': 302, 'headers': headers, 'body': ''}

    def filter_localfile(self, handler, mo, repl):
        filename = repl.lstrip('file://')
        if filename.lower() in ('/dev/null', 'nul'):
            filename = os.devnull
        if os.name == 'nt':
            filename = filename.lstrip('/')
        content_type = None
        try:
            import mimetypes
            content_type = mimetypes.types_map.get(os.path.splitext(filename)[1])
        except StandardError as e:
            logging.error('import mimetypes failed: %r', e)
        try:
            with open(filename, 'rb') as fp:
                data = fp.read()
                headers = {'Connection': 'close', 'Content-Length': str(len(data))}
                if content_type:
                    headers['Content-Type'] = content_type
                return 'mock', {'status': 200, 'headers': headers, 'body': data}
        except StandardError as e:
            return 'mock', {'status': 403, 'headers': {'Connection': 'close'}, 'body': 'read %r %r' % (filename, e)}


class AutoRangeFilter(BaseProxyHandlerFilter):
    """auto range filter"""
    def __init__(self, hosts_patterns, endswith_exts, noendswith_exts, maxsize):
        self.hosts_match = [re.compile(fnmatch.translate(h)).match for h in hosts_patterns]
        self.endswith_exts = tuple(endswith_exts)
        self.noendswith_exts = tuple(noendswith_exts)
        self.maxsize = int(maxsize)

    def filter(self, handler):
        path = urlparse.urlsplit(handler.path).path
        need_autorange = any(x(handler.host) for x in self.hosts_match) or path.endswith(self.endswith_exts)
        if path.endswith(self.noendswith_exts) or 'range=' in urlparse.urlsplit(path).query or handler.command == 'HEAD':
            return None
        if handler.command != 'HEAD' and handler.headers.get('Range'):
            m = re.search(r'bytes=(\d+)-', handler.headers['Range'])
            start = int(m.group(1) if m else 0)
            handler.headers['Range'] = 'bytes=%d-%d' % (start, start+self.maxsize-1)
            logging.info('autorange range=%r match url=%r', handler.headers['Range'], handler.path)
        elif need_autorange:
            logging.info('Found [autorange]endswith match url=%r', handler.path)
            m = re.search(r'bytes=(\d+)-', handler.headers.get('Range', ''))
            start = int(m.group(1) if m else 0)
            handler.headers['Range'] = 'bytes=%d-%d' % (start, start+self.maxsize-1)


class StaticFileFilter(BaseProxyHandlerFilter):
    """static file filter"""
    index_file = 'index.html'

    def format_index_html(self, dirname):
        INDEX_TEMPLATE = u'''
        <html>
        <title>Directory listing for $dirname</title>
        <body>
        <h2>Directory listing for $dirname</h2>
        <hr>
        <ul>
        $html
        </ul>
        <hr>
        </body></html>
        '''
        html = ''
        if not isinstance(dirname, unicode):
            dirname = dirname.decode(sys.getfilesystemencoding())
        for name in os.listdir(dirname):
            fullname = os.path.join(dirname, name)
            suffix = u'/' if os.path.isdir(fullname) else u''
            html += u'<li><a href="%s%s">%s%s</a>\r\n' % (name, suffix, name, suffix)
        return string.Template(INDEX_TEMPLATE).substitute(dirname=dirname, html=html)

    def filter(self, handler):
        path = urlparse.urlsplit(handler.path).path
        if path.startswith('/'):
            path = urllib.unquote_plus(path.lstrip('/') or '.').decode('utf8')
            if os.path.isdir(path):
                index_file = os.path.join(path, self.index_file)
                if not os.path.isfile(index_file):
                    content = self.format_index_html(path).encode('UTF-8')
                    headers = {'Content-Type': 'text/html; charset=utf-8', 'Connection': 'close'}
                    return 'mock', {'status': 200, 'headers': headers, 'body': content}
                else:
                    path = index_file
            if os.path.isfile(path):
                content_type = 'application/octet-stream'
                try:
                    import mimetypes
                    content_type = mimetypes.types_map.get(os.path.splitext(path)[1])
                    if os.path.splitext(path)[1].endswith(('crt', 'pem')):
                        content_type = 'application/x-x509-ca-cert'
                except StandardError as e:
                    logging.error('import mimetypes failed: %r', e)
                with open(path, 'rb') as fp:
                    content = fp.read()
                    headers = {'Connection': 'close', 'Content-Type': content_type}
                    return 'mock', {'status': 200, 'headers': headers, 'body': content}


class BlackholeFilter(BaseProxyHandlerFilter):
    """blackhole filter"""
    one_pixel_gif = 'GIF89a\x01\x00\x01\x00\x80\xff\x00\xc0\xc0\xc0\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'

    def filter(self, handler):
        if handler.command == 'CONNECT':
            return 'strip', {}
        elif handler.path.startswith(('http://', 'https://')):
            headers = {'Cache-Control': 'max-age=86400',
                       'Expires': 'Oct, 01 Aug 2100 00:00:00 GMT',
                       'Connection': 'close'}
            content = ''
            if urlparse.urlsplit(handler.path).path.lower().endswith(('.jpg', '.gif', '.png', '.jpeg', '.bmp')):
                headers['Content-Type'] = 'image/gif'
                content = self.one_pixel_gif
            return 'mock', {'status': 200, 'headers': headers, 'body': content}
        else:
            return 'mock', {'status': 404, 'headers': {'Connection': 'close'}, 'body': ''}


class SimpleProxyHandler(BaseHTTPRequestHandler):
    """Simple Proxy Handler"""

    bufsize = 256*1024
    protocol_version = 'HTTP/1.1'
    ssl_version = ssl.PROTOCOL_SSLv23
    skip_headers = frozenset(['Vary',
                              'Via',
                              'X-Forwarded-For',
                              'Proxy-Authorization',
                              'Proxy-Connection',
                              'Upgrade',
                              'X-Chrome-Variations',
                              'Connection',
                              'Cache-Control'])
    disable_transport_ssl = True
    scheme = 'http'
    first_run_lock = threading.Lock()
    handler_filters = [SimpleProxyHandlerFilter()]
    handler_plugins = {'direct': DirectFetchPlugin(),
                       'mock': MockFetchPlugin(),
                       'strip': StripPlugin(),}

    def finish(self):
        """make python2 BaseHTTPRequestHandler happy"""
        try:
            BaseHTTPServer.BaseHTTPRequestHandler.finish(self)
        except (socket.error, ssl.SSLError, OpenSSL.SSL.Error) as e:
            if e[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.EPIPE):
                raise

    def address_string(self):
        return '%s:%s' % self.client_address[:2]

    def send_response(self, code, message=None):
        if message is None:
            if code in self.responses:
                message = self.responses[code][0]
            else:
                message = ''
        if self.request_version != 'HTTP/0.9':
            self.wfile.write('%s %d %s\r\n' % (self.protocol_version, code, message))

    def send_header(self, keyword, value):
        """Send a MIME header."""
        base_send_header = BaseHTTPServer.BaseHTTPRequestHandler.send_header
        keyword = keyword.title()
        if keyword == 'Set-Cookie':
            for cookie in re.split(r', (?=[^ =]+(?:=|$))', value):
                base_send_header(self, keyword, cookie)
        elif keyword == 'Content-Disposition' and '"' not in value:
            value = re.sub(r'filename=([^"\']+)', 'filename="\\1"', value)
            base_send_header(self, keyword, value)
        else:
            base_send_header(self, keyword, value)

    def setup(self):
        if isinstance(self.__class__.first_run, collections.Callable):
            try:
                with self.__class__.first_run_lock:
                    if isinstance(self.__class__.first_run, collections.Callable):
                        self.first_run()
                        self.__class__.first_run = None
            except StandardError as e:
                logging.exception('%s.first_run() return %r', self.__class__, e)
        self.__class__.setup = BaseHTTPServer.BaseHTTPRequestHandler.setup
        self.__class__.do_CONNECT = self.__class__.do_METHOD
        self.__class__.do_GET = self.__class__.do_METHOD
        self.__class__.do_PUT = self.__class__.do_METHOD
        self.__class__.do_POST = self.__class__.do_METHOD
        self.__class__.do_HEAD = self.__class__.do_METHOD
        self.__class__.do_DELETE = self.__class__.do_METHOD
        self.__class__.do_OPTIONS = self.__class__.do_METHOD
        self.__class__.do_PATCH = self.__class__.do_METHOD
        self.setup()

    def handle_one_request(self):
        if not self.disable_transport_ssl and self.scheme == 'http':
            leadbyte = self.connection.recv(1, socket.MSG_PEEK)
            if leadbyte in ('\x80', '\x16'):
                server_name = ''
                if leadbyte == '\x16':
                    for _ in xrange(2):
                        leaddata = self.connection.recv(1024, socket.MSG_PEEK)
                        if is_clienthello(leaddata):
                            try:
                                server_name = extract_sni_name(leaddata)
                            finally:
                                break
                try:
                    certfile = CertUtil.get_cert(server_name or 'www.google.com')
                    ssl_sock = ssl.wrap_socket(self.connection, ssl_version=self.ssl_version, keyfile=certfile, certfile=certfile, server_side=True)
                except StandardError as e:
                    if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET):
                        logging.exception('ssl.wrap_socket(self.connection=%r) failed: %s', self.connection, e)
                    return
                self.connection = ssl_sock
                self.rfile = self.connection.makefile('rb', self.bufsize)
                self.wfile = self.connection.makefile('wb', 0)
                self.scheme = 'https'
        return BaseHTTPServer.BaseHTTPRequestHandler.handle_one_request(self)

    def first_run(self):
        pass

    def parse_header(self):
        if self.command == 'CONNECT':
            netloc = self.path
        elif self.path[0] == '/':
            netloc = self.headers.get('Host', 'localhost')
            self.path = '%s://%s%s' % (self.scheme, netloc, self.path)
        else:
            netloc = urlparse.urlsplit(self.path).netloc
        m = re.match(r'^(.+):(\d+)$', netloc)
        if m:
            self.host = m.group(1).strip('[]')
            self.port = int(m.group(2))
        else:
            self.host = netloc
            self.port = 443 if self.scheme == 'https' else 80

    def do_METHOD(self):
        self.parse_header()
        self.body = self.rfile.read(int(self.headers['Content-Length'])) if 'Content-Length' in self.headers else ''
        for handler_filter in self.handler_filters:
            action = handler_filter.filter(self)
            if not action:
                continue
            if not isinstance(action, tuple):
                raise TypeError('%s must return a tuple, not %r' % (handler_filter, action))
            plugin = self.handler_plugins[action[0]]
            return plugin.handle(self, **action[1])


class MultipleConnectionMixin(object):
    """Multiple Connection Mixin"""
    dns_cache = LRUCache(64*1024)
    dns_servers = ['8.8.8.8', '114.114.114.114']
    dns_blacklist = []
    tcp_connection_time = collections.defaultdict(float)
    tcp_connection_time_with_clienthello = collections.defaultdict(float)
    tcp_connection_cache = collections.defaultdict(Queue.PriorityQueue)
    tcp_connection_good_ipaddrs = {}
    tcp_connection_bad_ipaddrs = {}
    tcp_connection_unknown_ipaddrs = {}
    tcp_connection_cachesock = False
    tcp_connection_keepalive = False
    ssl_connection_time = collections.defaultdict(float)
    ssl_connection_cache = collections.defaultdict(Queue.PriorityQueue)
    ssl_connection_good_ipaddrs = {}
    ssl_connection_bad_ipaddrs = {}
    ssl_connection_unknown_ipaddrs = {}
    ssl_connection_cachesock = False
    ssl_connection_keepalive = False
    iplist_predefined = set([])
    max_window = 4
    connect_timeout = 6
    max_timeout = 8
    ssl_version = ssl.PROTOCOL_SSLv23
    openssl_context = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv23_METHOD)

    def gethostbyname2(self, hostname):
        try:
            iplist = self.dns_cache[hostname]
        except KeyError:
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', hostname) or ':' in hostname:
                iplist = [hostname]
            elif self.dns_servers:
                try:
                    record = dnslib_resolve_over_udp(hostname, self.dns_servers, timeout=2, blacklist=self.dns_blacklist)
                except socket.gaierror:
                    record = dnslib_resolve_over_tcp(hostname, self.dns_servers, timeout=2, blacklist=self.dns_blacklist)
                iplist = dnslib_record2iplist(record)
            else:
                iplist = socket.gethostbyname_ex(hostname)[-1]
            self.dns_cache[hostname] = iplist
        return iplist

    def create_tcp_connection(self, hostname, port, timeout, **kwargs):
        client_hello = kwargs.get('client_hello', None)
        cache_key = kwargs.get('cache_key', '') if not client_hello else ''
        def create_connection(ipaddr, timeout, queobj):
            sock = None
            sock = None
            try:
                # create a ipv4/ipv6 socket object
                sock = socket.socket(socket.AF_INET if ':' not in ipaddr[0] else socket.AF_INET6)
                # set reuseaddr option to avoid 10048 socket error
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # set struct linger{l_onoff=1,l_linger=0} to avoid 10048 socket error
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
                # resize socket recv buffer 8K->32K to improve browser releated application performance
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32*1024)
                # disable negal algorithm to send http request quickly.
                sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
                # set a short timeout to trigger timeout retry more quickly.
                sock.settimeout(min(self.connect_timeout, timeout))
                # start connection time record
                start_time = time.time()
                # TCP connect
                sock.connect(ipaddr)
                # end connection time record
                connected_time = time.time()
                # record TCP connection time
                self.tcp_connection_time[ipaddr] = sock.tcp_time = connected_time - start_time
                if gevent and isinstance(sock, gevent.socket.socket):
                    sock.tcp_time = connected_time - start_time
                if client_hello:
                    sock.sendall(client_hello)
                    if gevent and isinstance(sock, gevent.socket.socket):
                        sock.data = data = sock.recv(4096)
                    else:
                        data = sock.recv(4096, socket.MSG_PEEK)
                    if not data:
                        logging.debug('create_tcp_connection %r with client_hello return NULL byte, continue %r', ipaddr, time.time()-start_time)
                        raise socket.timeout('timed out')
                    # record TCP connection time with client hello
                    self.tcp_connection_time_with_clienthello[ipaddr] = time.time() - start_time
                # remove from bad/unknown ipaddrs dict
                self.tcp_connection_bad_ipaddrs.pop(ipaddr, None)
                self.tcp_connection_unknown_ipaddrs.pop(ipaddr, None)
                # add to good ipaddrs dict
                if ipaddr not in self.tcp_connection_good_ipaddrs:
                    self.tcp_connection_good_ipaddrs[ipaddr] = connected_time
                # put ssl socket object to output queobj
                queobj.put(sock)
            except (socket.error, ssl.SSLError, OSError) as e:
                # any socket.error, put Excpetions to output queobj.
                queobj.put(e)
                # reset a large and random timeout to the ipaddr
                self.tcp_connection_time[ipaddr] = self.connect_timeout + random.random()
                # add to bad ipaddrs dict
                if ipaddr not in self.tcp_connection_bad_ipaddrs:
                    self.tcp_connection_bad_ipaddrs[ipaddr] = time.time()
                # remove from good/unknown ipaddrs dict
                self.tcp_connection_good_ipaddrs.pop(ipaddr, None)
                self.tcp_connection_unknown_ipaddrs.pop(ipaddr, None)
                # close ssl socket
                if sock:
                    sock.close()
        def close_connection(count, queobj, first_tcp_time):
            for _ in range(count):
                sock = queobj.get()
                tcp_time_threshold = min(1, 1.3 * first_tcp_time)
                if sock and hasattr(sock, 'getpeername'):
                    if cache_key and (sock.getpeername()[0] in self.iplist_predefined or self.tcp_connection_cachesock) and sock.tcp_time < tcp_time_threshold:
                        cache_queue = self.tcp_connection_cache[cache_key]
                        if cache_queue.qsize() < 8:
                            try:
                                _, old_sock = cache_queue.get_nowait()
                                old_sock.close()
                            except Queue.Empty:
                                pass
                        cache_queue.put((time.time(), sock))
                    else:
                        sock.close()
        def reorg_ipaddrs():
            current_time = time.time()
            for ipaddr, ctime in self.tcp_connection_good_ipaddrs.items():
                if current_time - ctime > 4 * 60 and len(self.tcp_connection_good_ipaddrs) > 2 * self.max_window and ipaddr[0] not in self.iplist_predefined:
                    self.tcp_connection_good_ipaddrs.pop(ipaddr, None)
                    self.tcp_connection_unknown_ipaddrs[ipaddr] = ctime
            for ipaddr, ctime in self.tcp_connection_bad_ipaddrs.items():
                if current_time - ctime > 6 * 60:
                    self.tcp_connection_bad_ipaddrs.pop(ipaddr, None)
                    self.tcp_connection_unknown_ipaddrs[ipaddr] = ctime
            #logging.info("tcp good_ipaddrs=%d, bad_ipaddrs=%d, unknown_ipaddrs=%d", len(self.tcp_connection_good_ipaddrs), len(self.tcp_connection_bad_ipaddrs), len(self.tcp_connection_unknown_ipaddrs))
        try:
            while cache_key:
                ctime, sock = self.tcp_connection_cache[cache_key].get_nowait()
                if time.time() - ctime < self.connect_timeout:
                    return sock
                else:
                    sock.close()
        except Queue.Empty:
            pass
        addresses = [(x, port) for x in self.gethostbyname2(hostname)]
        #logging.info('gethostbyname2(%r) return %d addresses', hostname, len(addresses))
        sock = None
        for i in range(kwargs.get('max_retry', 4)):
            reorg_ipaddrs()
            window = self.max_window + i
            if len(self.ssl_connection_good_ipaddrs) > len(self.ssl_connection_bad_ipaddrs):
                window = max(2, window-2)
            if len(self.tcp_connection_bad_ipaddrs)/2 >= len(self.tcp_connection_good_ipaddrs) <= 1.5 * window:
                window += 2
            good_ipaddrs = [x for x in addresses if x in self.tcp_connection_good_ipaddrs]
            good_ipaddrs = sorted(good_ipaddrs, key=self.tcp_connection_time.get)[:window]
            unknown_ipaddrs = [x for x in addresses if x not in self.tcp_connection_good_ipaddrs and x not in self.tcp_connection_bad_ipaddrs]
            random.shuffle(unknown_ipaddrs)
            unknown_ipaddrs = unknown_ipaddrs[:window]
            bad_ipaddrs = [x for x in addresses if x in self.tcp_connection_bad_ipaddrs]
            bad_ipaddrs = sorted(bad_ipaddrs, key=self.tcp_connection_bad_ipaddrs.get)[:window]
            addrs = good_ipaddrs + unknown_ipaddrs + bad_ipaddrs
            remain_window = 3 * window - len(addrs)
            if 0 < remain_window <= len(addresses):
                addrs += random.sample(addresses, remain_window)
            #logging.debug('%s good_ipaddrs=%d, unknown_ipaddrs=%r, bad_ipaddrs=%r', cache_key, len(good_ipaddrs), len(unknown_ipaddrs), len(bad_ipaddrs))
            queobj = Queue.Queue()
            for addr in addrs:
                thread.start_new_thread(create_connection, (addr, timeout, queobj))
            for i in range(len(addrs)):
                sock = queobj.get()
                if hasattr(sock, 'getpeername'):
                    spawn_later(0.01, close_connection, len(addrs)-i-1, queobj, getattr(sock, 'tcp_time') or self.tcp_connection_time[sock.getpeername()])
                    return sock
                elif i == 0:
                    # only output first error
                    logging.warning('create_tcp_connection to %r with %s return %r, try again.', hostname, addrs, sock)
        if not hasattr(sock, 'getpeername'):
            raise sock

    def create_ssl_connection(self, hostname, port, timeout, **kwargs):
        cache_key = kwargs.get('cache_key', '')
        validate = kwargs.get('validate')
        headfirst = kwargs.get('headfirst')
        def create_connection(ipaddr, timeout, queobj):
            sock = None
            ssl_sock = None
            try:
                # create a ipv4/ipv6 socket object
                sock = socket.socket(socket.AF_INET if ':' not in ipaddr[0] else socket.AF_INET6)
                # set reuseaddr option to avoid 10048 socket error
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # set struct linger{l_onoff=1,l_linger=0} to avoid 10048 socket error
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
                # resize socket recv buffer 8K->32K to improve browser releated application performance
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32*1024)
                # disable negal algorithm to send http request quickly.
                sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
                # set a short timeout to trigger timeout retry more quickly.
                sock.settimeout(min(self.connect_timeout, timeout))
                # pick up the certificate
                if not validate:
                    ssl_sock = ssl.wrap_socket(sock, ssl_version=self.ssl_version, do_handshake_on_connect=False)
                else:
                    ssl_sock = ssl.wrap_socket(sock, ssl_version=self.ssl_version, cert_reqs=ssl.CERT_REQUIRED, ca_certs=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cacert.pem'), do_handshake_on_connect=False)
                ssl_sock.settimeout(min(self.connect_timeout, timeout))
                # start connection time record
                start_time = time.time()
                # TCP connect
                ssl_sock.connect(ipaddr)
                connected_time = time.time()
                # SSL handshake
                ssl_sock.do_handshake()
                handshaked_time = time.time()
                # record TCP connection time
                self.tcp_connection_time[ipaddr] = ssl_sock.tcp_time = connected_time - start_time
                # record SSL connection time
                self.ssl_connection_time[ipaddr] = ssl_sock.ssl_time = handshaked_time - start_time
                ssl_sock.ssl_time = connected_time - start_time
                # sometimes, we want to use raw tcp socket directly(select/epoll), so setattr it to ssl socket.
                ssl_sock.sock = sock
                # remove from bad/unknown ipaddrs dict
                self.ssl_connection_bad_ipaddrs.pop(ipaddr, None)
                self.ssl_connection_unknown_ipaddrs.pop(ipaddr, None)
                # add to good ipaddrs dict
                if ipaddr not in self.ssl_connection_good_ipaddrs:
                    self.ssl_connection_good_ipaddrs[ipaddr] = handshaked_time
                # verify SSL certificate issuer.
                if validate and (hostname.endswith('.appspot.com') or '.google' in hostname):
                    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, ssl_sock.getpeercert(True))
                    issuer_commonname = next((v for k, v in cert.get_issuer().get_components() if k == 'CN'), '')
                    if not issuer_commonname.startswith('Google'):
                        raise socket.error('%r certficate is issued by %r, not Google' % (hostname, issuer_commonname))
                # set timeout
                ssl_sock.settimeout(timeout)
                # do head first check
                if headfirst:
                    ssl_sock.send('HEAD /favicon.ico HTTP/1.1\r\nHost: %s\r\n\r\n' % hostname)
                    response = httplib.HTTPResponse(ssl_sock, buffering=True)
                    try:
                        if gevent:
                            with gevent.Timeout(timeout):
                                response.begin()
                        else:
                            response.begin()
                    except gevent.Timeout:
                        ssl_sock.close()
                        raise socket.timeout('timed out')
                    finally:
                        response.close()
                # put ssl socket object to output queobj
                queobj.put(ssl_sock)
            except (socket.error, ssl.SSLError, OSError) as e:
                # any socket.error, put Excpetions to output queobj.
                queobj.put(e)
                # reset a large and random timeout to the ipaddr
                self.ssl_connection_time[ipaddr] = self.connect_timeout + random.random()
                # add to bad ipaddrs dict
                if ipaddr not in self.ssl_connection_bad_ipaddrs:
                    self.ssl_connection_bad_ipaddrs[ipaddr] = time.time()
                # remove from good/unknown ipaddrs dict
                self.ssl_connection_good_ipaddrs.pop(ipaddr, None)
                self.ssl_connection_unknown_ipaddrs.pop(ipaddr, None)
                # close ssl socket
                if ssl_sock:
                    ssl_sock.close()
                # close tcp socket
                if sock:
                    sock.close()
        def create_connection_withopenssl(ipaddr, timeout, queobj):
            sock = None
            ssl_sock = None
            timer = None
            NetworkError = (socket.error, OpenSSL.SSL.Error, OSError)
            if gevent and (ipaddr[0] not in self.iplist_predefined):
                NetworkError += (gevent.Timeout,)
                #timer = gevent.Timeout(timeout)
                #timer.start()
            try:
                # create a ipv4/ipv6 socket object
                sock = socket.socket(socket.AF_INET if ':' not in ipaddr[0] else socket.AF_INET6)
                # set reuseaddr option to avoid 10048 socket error
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # set struct linger{l_onoff=1,l_linger=0} to avoid 10048 socket error
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
                # resize socket recv buffer 8K->32K to improve browser releated application performance
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32*1024)
                # disable negal algorithm to send http request quickly.
                sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
                # set a short timeout to trigger timeout retry more quickly.
                sock.settimeout(timeout or self.connect_timeout)
                # pick up the certificate
                server_hostname = random_hostname() if (cache_key or '').startswith('google_') or hostname.endswith('.appspot.com') else None
                ssl_sock = SSLConnection(self.openssl_context, sock)
                ssl_sock.set_connect_state()
                if server_hostname and hasattr(ssl_sock, 'set_tlsext_host_name'):
                    ssl_sock.set_tlsext_host_name(server_hostname)
                # start connection time record
                start_time = time.time()
                # TCP connect
                ssl_sock.connect(ipaddr)
                connected_time = time.time()
                # SSL handshake
                ssl_sock.do_handshake()
                handshaked_time = time.time()
                # record TCP connection time
                self.tcp_connection_time[ipaddr] = ssl_sock.tcp_time = connected_time - start_time
                # record SSL connection time
                self.ssl_connection_time[ipaddr] = ssl_sock.ssl_time = handshaked_time - start_time
                # sometimes, we want to use raw tcp socket directly(select/epoll), so setattr it to ssl socket.
                ssl_sock.sock = sock
                # remove from bad/unknown ipaddrs dict
                self.ssl_connection_bad_ipaddrs.pop(ipaddr, None)
                self.ssl_connection_unknown_ipaddrs.pop(ipaddr, None)
                # add to good ipaddrs dict
                if ipaddr not in self.ssl_connection_good_ipaddrs:
                    self.ssl_connection_good_ipaddrs[ipaddr] = handshaked_time
                # verify SSL certificate issuer.
                if validate and (hostname.endswith('.appspot.com') or '.google' in hostname):
                    cert = ssl_sock.get_peer_certificate()
                    issuer_commonname = next((v for k, v in cert.get_issuer().get_components() if k == 'CN'), '')
                    if not issuer_commonname.startswith('Google'):
                        raise socket.error('%r certficate is issued by %r, not Google' % (hostname, issuer_commonname))
                # do head first check
                if headfirst:
                    ssl_sock.send('HEAD /favicon.ico HTTP/1.1\r\nHost: %s\r\n\r\n' % hostname)
                    response = httplib.HTTPResponse(ssl_sock, buffering=True)
                    try:
                        if gevent:
                            with gevent.Timeout(timeout):
                                response.begin()
                        else:
                            response.begin()
                    except gevent.Timeout:
                        ssl_sock.close()
                        raise socket.timeout('timed out')
                    finally:
                        response.close()
                # put ssl socket object to output queobj
                queobj.put(ssl_sock)
            except NetworkError as e:
                # any socket.error, put Excpetions to output queobj.
                queobj.put(e)
                # reset a large and random timeout to the ipaddr
                self.ssl_connection_time[ipaddr] = self.connect_timeout + random.random()
                # add to bad ipaddrs dict
                if ipaddr not in self.ssl_connection_bad_ipaddrs:
                    self.ssl_connection_bad_ipaddrs[ipaddr] = time.time()
                # remove from good/unknown ipaddrs dict
                self.ssl_connection_good_ipaddrs.pop(ipaddr, None)
                self.ssl_connection_unknown_ipaddrs.pop(ipaddr, None)
                # close ssl socket
                if ssl_sock:
                    ssl_sock.close()
                # close tcp socket
                if sock:
                    sock.close()
            finally:
                if timer:
                    timer.cancel()
        def close_connection(count, queobj, first_tcp_time, first_ssl_time):
            for _ in range(count):
                sock = queobj.get()
                ssl_time_threshold = min(1, 1.3 * first_ssl_time)
                if sock and hasattr(sock, 'getpeername'):
                    if cache_key and (sock.getpeername()[0] in self.iplist_predefined or self.ssl_connection_cachesock) and sock.ssl_time < ssl_time_threshold:
                        cache_queue = self.ssl_connection_cache[cache_key]
                        if cache_queue.qsize() < 8:
                            try:
                                _, old_sock = cache_queue.get_nowait()
                                old_sock.close()
                            except Queue.Empty:
                                pass
                        cache_queue.put((time.time(), sock))
                    else:
                        sock.close()
        def reorg_ipaddrs():
            current_time = time.time()
            for ipaddr, ctime in self.ssl_connection_good_ipaddrs.items():
                if current_time - ctime > 4 * 60 and len(self.ssl_connection_good_ipaddrs) > 2 * self.max_window and ipaddr[0] not in self.iplist_predefined:
                    self.ssl_connection_good_ipaddrs.pop(ipaddr, None)
                    self.ssl_connection_unknown_ipaddrs[ipaddr] = ctime
            for ipaddr, ctime in self.ssl_connection_bad_ipaddrs.items():
                if current_time - ctime > 6 * 60:
                    self.ssl_connection_bad_ipaddrs.pop(ipaddr, None)
                    self.ssl_connection_unknown_ipaddrs[ipaddr] = ctime
            #logging.info("ssl good_ipaddrs=%d, bad_ipaddrs=%d, unknown_ipaddrs=%d", len(self.ssl_connection_good_ipaddrs), len(self.ssl_connection_bad_ipaddrs), len(self.ssl_connection_unknown_ipaddrs))
        try:
            while cache_key:
                ctime, sock = self.ssl_connection_cache[cache_key].get_nowait()
                if time.time() - ctime < self.connect_timeout:
                    return sock
                else:
                    sock.close()
        except Queue.Empty:
            pass
        addresses = [(x, port) for x in self.gethostbyname2(hostname)]
        #logging.info('gethostbyname2(%r) return %d addresses', hostname, len(addresses))
        sock = None
        for i in range(kwargs.get('max_retry', 4)):
            reorg_ipaddrs()
            good_ipaddrs = sorted([x for x in addresses if x in self.ssl_connection_good_ipaddrs], key=self.ssl_connection_time.get)
            bad_ipaddrs = sorted([x for x in addresses if x in self.ssl_connection_bad_ipaddrs], key=self.ssl_connection_bad_ipaddrs.get)
            unknown_ipaddrs = [x for x in addresses if x not in self.ssl_connection_good_ipaddrs and x not in self.ssl_connection_bad_ipaddrs]
            random.shuffle(unknown_ipaddrs)
            window = self.max_window + i
            if len(bad_ipaddrs) < 0.2 * len(good_ipaddrs) and len(good_ipaddrs) > 10:
                addrs = good_ipaddrs[:window]
                addrs += [random.choice(unknown_ipaddrs)] if unknown_ipaddrs else []
            elif len(good_ipaddrs) > 2 * window or len(bad_ipaddrs) < 0.5 * len(good_ipaddrs):
                addrs = (good_ipaddrs[:window] + unknown_ipaddrs + bad_ipaddrs)[:2*window]
            else:
                addrs = good_ipaddrs[:window] + unknown_ipaddrs[:window] + bad_ipaddrs[:window]
                addrs += random.sample(addresses, min(len(addresses), 3*window-len(addrs))) if len(addrs) < 3*window else []
            #logging.debug('%s good_ipaddrs=%d, unknown_ipaddrs=%r, bad_ipaddrs=%r', cache_key, len(good_ipaddrs), len(unknown_ipaddrs), len(bad_ipaddrs))
            queobj = Queue.Queue()
            for addr in addrs:
                if sys.platform != 'win32':
                    # Workaround for CPU 100% issue under MacOSX/Linux
                    thread.start_new_thread(create_connection, (addr, timeout, queobj))
                else:
                    thread.start_new_thread(create_connection_withopenssl, (addr, timeout, queobj))
            errors = []
            for i in range(len(addrs)):
                sock = queobj.get()
                if hasattr(sock, 'getpeername'):
                    spawn_later(0.01, close_connection, len(addrs)-i-1, queobj, sock.tcp_time, sock.ssl_time)
                    return sock
                else:
                    errors.append(sock)
                    if i == len(addrs) - 1:
                        logging.warning('create_ssl_connection to %r with %s return %s, try again.', hostname, addrs, collections.OrderedDict.fromkeys(str(x) for x in errors).keys())
        if not hasattr(sock, 'getpeername'):
            raise sock

    def create_http_request(self, method, url, headers, body, timeout, max_retry=2, bufsize=8192, crlf=None, validate=None, cache_key=None, headfirst=False, **kwargs):
        scheme, netloc, path, query, _ = urlparse.urlsplit(url)
        if netloc.rfind(':') <= netloc.rfind(']'):
            # no port number
            host = netloc
            port = 443 if scheme == 'https' else 80
        else:
            host, _, port = netloc.rpartition(':')
            port = int(port)
        if query:
            path += '?' + query
        if 'Host' not in headers:
            headers['Host'] = host
        if body and 'Content-Length' not in headers:
            headers['Content-Length'] = str(len(body))
        sock = None
        for i in range(max_retry):
            try:
                create_connection = self.create_ssl_connection if scheme == 'https' else self.create_tcp_connection
                sock = create_connection(host, port, timeout, validate=validate, cache_key=cache_key, headfirst=headfirst)
                break
            except StandardError as e:
                logging.exception('create_http_request "%s %s" failed:%s', method, url, e)
                if sock:
                    sock.close()
                if i == max_retry - 1:
                    raise
        request_data = ''
        crlf_counter = 0
        if scheme != 'https' and crlf:
            fakeheaders = dict((k.title(), v) for k, v in headers.items())
            fakeheaders.pop('Content-Length', None)
            fakeheaders.pop('Cookie', None)
            fakeheaders.pop('Host', None)
            if 'User-Agent' not in fakeheaders:
                fakeheaders['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1878.0 Safari/537.36'
            if 'Accept-Language' not in fakeheaders:
                fakeheaders['Accept-Language'] = 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4'
            if 'Accept' not in fakeheaders:
                fakeheaders['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            fakeheaders_data = ''.join('%s: %s\r\n' % (k, v) for k, v in fakeheaders.items() if k not in self.skip_headers)
            while crlf_counter < 5 or len(request_data) < 1500 * 2:
                request_data += 'GET / HTTP/1.1\r\n%s\r\n' % fakeheaders_data
                crlf_counter += 1
            request_data += '\r\n\r\n\r\n'
        request_data += '%s %s %s\r\n' % (method, path, 'HTTP/1.1')
        request_data += ''.join('%s: %s\r\n' % (k.title(), v) for k, v in headers.items() if k.title() not in self.skip_headers)
        request_data += '\r\n'
        if isinstance(body, bytes):
            sock.sendall(request_data.encode() + body)
        elif hasattr(body, 'read'):
            sock.sendall(request_data)
            while 1:
                data = body.read(bufsize)
                if not data:
                    break
                sock.sendall(data)
        else:
            raise TypeError('create_http_request(body) must be a string or buffer, not %r' % type(body))
        response = None
        try:
            while crlf_counter:
                if sys.version[:3] == '2.7':
                    response = httplib.HTTPResponse(sock, buffering=False)
                else:
                    response = httplib.HTTPResponse(sock)
                    response.fp.close()
                    response.fp = sock.makefile('rb', 0)
                response.begin()
                response.read()
                response.close()
                crlf_counter -= 1
        except StandardError as e:
            logging.exception('crlf skip read host=%r path=%r error: %r', headers.get('Host'), path, e)
            if response:
                if response.fp and response.fp._sock:
                    response.fp._sock.close()
                response.close()
            if sock:
                sock.close()
            return None
        if sys.version[:3] == '2.7':
            response = httplib.HTTPResponse(sock, buffering=True)
        else:
            response = httplib.HTTPResponse(sock)
            response.fp.close()
            response.fp = sock.makefile('rb')
        if gevent and not headfirst and kwargs.get('read_timeout'):
            try:
                with gevent.Timeout(int(kwargs.get('read_timeout'))):
                    response.begin()
            except gevent.Timeout:
                response.close()
                raise socket.timeout('timed out')
        else:
            orig_timeout = sock.gettimeout()
            sock.settimeout(self.connect_timeout)
            response.begin()
            sock.settimeout(orig_timeout)
        if ((scheme == 'https' and self.ssl_connection_cachesock and self.ssl_connection_keepalive) or (scheme == 'http' and self.tcp_connection_cachesock and self.tcp_connection_keepalive)) and cache_key:
            response.cache_key = cache_key
            response.cache_sock = response.fp._sock
        return response


class ProxyConnectionMixin(object):
    """Proxy Connection Mixin"""
    def __init__(self, proxy_host, proxy_port, proxy_username='', proxy_password=''):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password

    def gethostbyname2(self, hostname):
        try:
            return socket.gethostbyname_ex(hostname)[-1]
        except socket.error:
            return [hostname]

    def create_tcp_connection(self, hostname, port, timeout, **kwargs):
        sock = socket.create_connection((self.proxy_host, int(self.proxy_port)))
        if hostname.endswith('.appspot.com'):
            hostname = 'www.google.com'
        request_data = 'CONNECT %s:%s HTTP/1.1\r\n' % (hostname, port)
        if self.proxy_username and self.proxy_password:
            request_data += 'Proxy-Authorization: Basic %s\r\n' % base64.b64encode(('%s:%s' % (self.proxy_username, self.proxy_password)).encode()).decode().strip()
        request_data += '\r\n'
        sock.sendall(request_data)
        response = httplib.HTTPResponse(sock)
        response.fp.close()
        response.fp = sock.makefile('rb', 0)
        response.begin()
        if response.status >= 400:
            raise httplib.BadStatusLine('%s %s %s' % (response.version, response.status, response.reason))
        return sock

    def create_ssl_connection(self, hostname, port, timeout, **kwargs):
        sock = self.create_tcp_connection(hostname, port, timeout, **kwargs)
        ssl_sock = ssl.wrap_socket(sock)
        return ssl_sock


def test():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(asctime)s %(message)s', datefmt='[%b %d %H:%M:%S]')
    # SimpleProxyHandler.handler_filters.insert(0, MIMTProxyHandlerFilter())
    server = LocalProxyServer(('', 8080), SimpleProxyHandler)
    logging.info('serving at %r', server.server_address)
    server.serve_forever()


if __name__ == '__main__':
    test()
