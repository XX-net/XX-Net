#!/usr/bin/env python
# coding:utf-8


import errno
import xlog
import socket
import ssl
import urlparse

import simple_http_server
from cert_util import CertUtil
from connect_manager import https_manager,forwork_manager

import OpenSSL
NetWorkIOError = (socket.error, ssl.SSLError, OpenSSL.SSL.Error, OSError)


from config import config
import gae_handler
import direct_handler
from connect_control import connect_allow_time, connect_fail_time, touch_active
import web_control


class GAEProxyHandler(simple_http_server.HttpServerHandler):
    gae_support_methods = tuple(["GET", "POST", "HEAD", "PUT", "DELETE", "PATCH"])
    bufsize = 256*1024
    max_retry = 3

    def setup(self):
        self.__class__.do_GET = self.__class__.do_METHOD
        self.__class__.do_PUT = self.__class__.do_METHOD
        self.__class__.do_POST = self.__class__.do_METHOD
        self.__class__.do_HEAD = self.__class__.do_METHOD
        self.__class__.do_DELETE = self.__class__.do_METHOD
        self.__class__.do_OPTIONS = self.__class__.do_METHOD

    def address_string(self):
        return '%s:%s' % self.client_address[:2]

    def forward_local(self):
        html = gae_handler.generate_message_html('Browser pass local request to proxy', u'您的浏览器把本地请求转发到代理上。<br>请在浏览器中设置：访问本地，不经过代理。<br><a href="https://github.com/XX-net/XX-Net/wiki/Browser-pass-localhost-request-to-proxy">帮助</a>')
        gae_handler.send_response(self.wfile, 200, body=html.encode('utf-8'))

    def do_METHOD(self):
        touch_active()

        host = self.headers.get('Host', '')
        host_ip, _, port = host.rpartition(':')
        if host_ip == "127.0.0.1" and port == str(config.LISTEN_PORT):
            controler = web_control.ControlHandler(self.client_address, self.headers, self.command, self.path, self.rfile, self.wfile)
            if self.command == "GET":
                return controler.do_GET()
            elif self.command == "POST":
                return controler.do_POST()
            else:
                xlog.warn("method not defined: %s", self.command)
                return

        if self.path[0] == '/' and host:
            self.path = 'http://%s%s' % (host, self.path)
        elif not host and '://' in self.path:
            host = urlparse.urlparse(self.path).netloc

        if host.startswith("127.0.0.1") or host.startswith("localhost"):
            xlog.warn("Your browser forward localhost to proxy.")
            return self.forward_local()

        self.parsed_url = urlparse.urlparse(self.path)

        if host in config.HOSTS_GAE:
            return self.do_AGENT()

        if host in config.HOSTS_FWD or host in config.HOSTS_DIRECT:
            return self.wfile.write(('HTTP/1.1 301\r\nLocation: %s\r\n\r\n' % self.path.replace('http://', 'https://', 1)).encode())

        if host.endswith(config.HOSTS_GAE_ENDSWITH):
            return self.do_AGENT()

        if host.endswith(config.HOSTS_FWD_ENDSWITH) or host.endswith(config.HOSTS_DIRECT_ENDSWITH):
            return self.wfile.write(('HTTP/1.1 301\r\nLocation: %s\r\n\r\n' % self.path.replace('http://', 'https://', 1)).encode())

        return self.do_AGENT()

    # Called by do_METHOD and do_CONNECT_AGENT
    def do_AGENT(self):
        def get_crlf(rfile):
            crlf = rfile.readline(2)
            if crlf != "\r\n":
                xlog.warn("chunk header read fail crlf")

        request_headers = dict((k.title(), v) for k, v in self.headers.items())

        payload = b''
        if 'Content-Length' in request_headers:
            try:
                payload_len = int(request_headers.get('Content-Length', 0))
                #logging.debug("payload_len:%d %s %s", payload_len, self.command, self.path)
                payload = self.rfile.read(payload_len)
            except NetWorkIOError as e:
                xlog.error('handle_method_urlfetch read payload failed:%s', e)
                return
        elif 'Transfer-Encoding' in request_headers:
            # chunked, used by facebook android client
            payload = ""
            while True:
                chunk_size_str = self.rfile.readline(65537)
                chunk_size_list = chunk_size_str.split(";")
                chunk_size = int("0x"+chunk_size_list[0], 0)
                if len(chunk_size_list) > 1 and chunk_size_list[1] != "\r\n":
                    xlog.warn("chunk ext: %s", chunk_size_str)
                if chunk_size == 0:
                    while True:
                        line = self.rfile.readline(65537)
                        if line == "\r\n":
                            break
                        else:
                            xlog.warn("entity header:%s", line)
                    break
                payload += self.rfile.read(chunk_size)
                get_crlf(self.rfile)

        gae_handler.handler(self.command, self.path, request_headers, payload, self.wfile)

    def do_CONNECT(self):
        touch_active()
        host, _, port = self.path.rpartition(':')

        if host in config.HOSTS_GAE:
            return self.do_CONNECT_AGENT()
        if host in config.HOSTS_DIRECT:
            return self.do_CONNECT_DIRECT()
        if host in config.HOSTS_FWD:
            return self.do_CONNECT_FWD()

        if host.endswith(config.HOSTS_GAE_ENDSWITH):
            return self.do_CONNECT_AGENT()
        if host.endswith(config.HOSTS_DIRECT_ENDSWITH):
            return self.do_CONNECT_DIRECT()
        if host.endswith(config.HOSTS_FWD_ENDSWITH):
            return self.do_CONNECT_FWD()

        return self.do_CONNECT_AGENT()

    def do_CONNECT_FWD(self):
        """socket forward for http CONNECT command"""
        host, _, port = self.path.rpartition(':')
        port = int(port)
        xlog.info('FWD %s %s:%d ', self.command, host, port)
        if host == "appengine.google.com" or host == "www.google.com":
            connected_in_s = 5 # gae_proxy upload to appengine is slow, it need more 'fresh' connection.
        else:
            connected_in_s = 10  # gws connect can be used after tcp connection created 15 s

        try:
            self.wfile.write(b'HTTP/1.1 200 OK\r\n\r\n')
            data = self.connection.recv(1024)
        except Exception as e:
            xlog.exception('do_CONNECT_FWD (%r, %r) Exception:%s', host, port, e)
            self.connection.close()
            return

        remote = forwork_manager.create_connection(host=host, port=port, sock_life=connected_in_s)
        if remote is None:
            self.connection.close()
            xlog.warn('FWD %s %s:%d create_connection fail', self.command, host, port)
            return

        try:
            if data:
                remote.send(data)
        except Exception as e:
            xlog.exception('do_CONNECT_FWD (%r, %r) Exception:%s', host, port, e)
            self.connection.close()
            remote.close()
            return

        # reset timeout default to avoid long http upload failure, but it will delay timeout retry :(
        remote.settimeout(None)

        forwork_manager.forward_socket(self.connection, remote, bufsize=self.bufsize)
        xlog.debug('FWD %s %s:%d with closed', self.command, host, port)

    def do_CONNECT_AGENT(self):
        """deploy fake cert to client"""
        # GAE supports the following HTTP methods: GET, POST, HEAD, PUT, DELETE, and PATCH
        host, _, port = self.path.rpartition(':')
        port = int(port)
        certfile = CertUtil.get_cert(host)
        xlog.info('GAE %s %s:%d ', self.command, host, port)
        self.__realconnection = None
        self.wfile.write(b'HTTP/1.1 200 OK\r\n\r\n')

        try:
            ssl_sock = ssl.wrap_socket(self.connection, keyfile=certfile, certfile=certfile, server_side=True)
        except ssl.SSLError as e:
            xlog.info('ssl error: %s, create full domain cert for host:%s', e, host)
            certfile = CertUtil.get_cert(host, full_name=True)
            return
        except Exception as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET):
                xlog.exception('ssl.wrap_socket(self.connection=%r) failed: %s path:%s, errno:%s', self.connection, e, self.path, e.args[0])
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
                xlog.warn("read request line len:%d", len(self.raw_requestline))
                return
            if not self.raw_requestline:
                xlog.warn("read request line empty")
                return
            if not self.parse_request():
                xlog.warn("parse request fail:%s", self.raw_requestline)
                return
        except NetWorkIOError as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.EPIPE):
                xlog.exception('ssl.wrap_socket(self.connection=%r) failed: %s path:%s, errno:%s', self.connection, e, self.path, e.args[0])
                raise
        if self.path[0] == '/' and host:
            self.path = 'https://%s%s' % (self.headers['Host'], self.path)
        xlog.debug('GAE CONNECT %s %s', self.command, self.path)
        if self.command not in self.gae_support_methods:
            if host.endswith(".google.com") or host.endswith(config.HOSTS_DIRECT_ENDSWITH) or host.endswith(config.HOSTS_GAE_ENDSWITH):
                if host in config.HOSTS_GAE:
                    gae_set = [s for s in config.HOSTS_GAE]
                    gae_set.remove(host)
                    config.HOSTS_GAE = tuple(gae_set)
                if host not in config.HOSTS_DIRECT:
                    fwd_set = [s for s in config.HOSTS_DIRECT]
                    fwd_set.append(host)
                    config.HOSTS_DIRECT = tuple(fwd_set)
                xlog.warn("Method %s not support in GAE, Redirect to DIRECT for %s", self.command, self.path)
                return self.wfile.write(('HTTP/1.1 301\r\nLocation: %s\r\n\r\n' % self.path).encode())
            else:
                xlog.warn("Method %s not support in GAEProxy for %s", self.command, self.path)
                return self.wfile.write(('HTTP/1.1 404 Not Found\r\n\r\n').encode())

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

    def do_CONNECT_DIRECT(self):
        """deploy fake cert to client"""
        host, _, port = self.path.rpartition(':')
        port = int(port)
        if port != 443:
            xlog.warn("CONNECT %s port:%d not support", host, port)
            return

        certfile = CertUtil.get_cert(host)
        xlog.info('GAE %s %s:%d ', self.command, host, port)
        self.__realconnection = None
        self.wfile.write(b'HTTP/1.1 200 OK\r\n\r\n')

        try:
            ssl_sock = ssl.wrap_socket(self.connection, keyfile=certfile, certfile=certfile, server_side=True)
        except ssl.SSLError as e:
            xlog.info('ssl error: %s, create full domain cert for host:%s', e, host)
            certfile = CertUtil.get_cert(host, full_name=True)
            return
        except Exception as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET):
                xlog.exception('ssl.wrap_socket(self.connection=%r) failed: %s path:%s, errno:%s', self.connection, e, self.path, e.args[0])
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
        xlog.debug('GAE CONNECT %s %s', self.command, self.path)

        try:
            if self.path[0] == '/' and host:
                self.path = 'http://%s%s' % (host, self.path)
            elif not host and '://' in self.path:
                host = urlparse.urlparse(self.path).netloc

            self.parsed_url = urlparse.urlparse(self.path)
            if len(self.parsed_url[4]):
                path = '?'.join([self.parsed_url[2], self.parsed_url[4]])
            else:
                path = self.parsed_url[2]

            request_headers = dict((k.title(), v) for k, v in self.headers.items())

            payload = b''
            if 'Content-Length' in request_headers:
                try:
                    payload_len = int(request_headers.get('Content-Length', 0))
                    #logging.debug("payload_len:%d %s %s", payload_len, self.command, self.path)
                    payload = self.rfile.read(payload_len)
                except NetWorkIOError as e:
                    xlog.error('handle_method_urlfetch read payload failed:%s', e)
                    return

            direct_handler.handler(self.command, host, path, request_headers, payload, self.wfile)

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

if __name__ == "__main__":
    pass
