#!/usr/bin/env python
# coding:utf-8


"""
GAEProxyHandler is the handler of http proxy port. default to 8087

    if HTTP request:
        do_METHOD()

    elif HTTPS request:
        do_CONNECT()


What is Direct mode:
    if user access google site like www.google.com, client.google.com,
    we don't need forward request to GAE server.
    we can send the original request to google ip directly.
    because most google ip act as general front server.

    Youtube content server do not support direct mode.

    look direct_handler.py for more detail.

What GAE mode:
    Google App Engine support urlfetch for proxy.
    every google account can apply 12 appid.
    after deploy server code under gae_proxy/server/gae to GAE server, user can
    use GAE server as http proxy.

    Here is the global link view:

     Browser => GAE_proxy => GAE server => target http/https server.

    look gae_hander.py for more detail.
"""

import errno
import socket
import ssl
import urlparse

import OpenSSL
NetWorkIOError = (socket.error, ssl.SSLError, OpenSSL.SSL.Error, OSError)


from xlog import getLogger
xlog = getLogger("gae_proxy")
import simple_http_client
import simple_http_server
from cert_util import CertUtil
from config import config
import gae_handler
import direct_handler
from connect_control import touch_active
import web_control


def get_crlf(rfile):
    crlf = rfile.readline(2)
    if crlf != "\r\n":
        xlog.warn("chunk header read fail crlf")


self_host = []
try:
    get_self_host = socket.gethostbyname_ex(socket.gethostname())
    for host in get_self_host:
        if not host or host == "localhost" or host == "127.0.0.1":
            continue
        if isinstance(host, list):
            self_host.append(host[0])
        else:
            self_host.append(host)
except:
    pass

for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]:
    s.connect(('8.8.8.8', 53))
    host = s.getsockname()[0]
    s.close()
    if host not in self_host:
        self_host.append(host)
self_host.append("127.0.0.1")
self_host.append("localhost")


class GAEProxyHandler(simple_http_server.HttpServerHandler):
    gae_support_methods = tuple(["GET", "POST", "HEAD", "PUT", "DELETE", "PATCH"])
    # GAE don't support command like OPTIONS, PROFILE

    bufsize = 64*1024
    max_retry = 3

    def setup(self):
        self.__class__.do_GET = self.__class__.do_METHOD
        self.__class__.do_PUT = self.__class__.do_METHOD
        self.__class__.do_POST = self.__class__.do_METHOD
        self.__class__.do_HEAD = self.__class__.do_METHOD
        self.__class__.do_DELETE = self.__class__.do_METHOD
        self.__class__.do_OPTIONS = self.__class__.do_METHOD

        self.self_check_response_data = "HTTP/1.1 200 OK\r\n"\
               "Access-Control-Allow-Origin: *\r\n"\
               "Cache-Control: no-cache, no-store, must-revalidate\r\n"\
               "Pragma: no-cache\r\n"\
               "Expires: 0\r\n"\
               "Content-Type: text/plain\r\n"\
               "Content-Length: 2\r\n\r\nOK"

    def read_payload(self):
        self.payload = b''
        if 'Content-Length' in self.headers:
            payload_len = int(self.headers.get('Content-Length', 0))
            # xlog.debug("payload_len:%d %s %s", payload_len, self.command, self.path)
            self.payload = self.rfile.read(payload_len)
        elif 'Transfer-Encoding' in self.headers:
            # chunked, used by facebook android client
            while True:
                chunk_size_str = self.rfile.readline(65537)
                chunk_size_list = chunk_size_str.split(";")
                chunk_size = int("0x" + chunk_size_list[0], 0)
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
                self.payload += self.rfile.read(chunk_size)
                get_crlf(self.rfile)

    def do_METHOD(self):
        # http request like GET/PUT/HEAD, no SSL encrypted
        self.method = "http"
        self.headers = dict((k.title(), v) for k, v in self.headers.items())
        if self.path.startswith("http://"):
            self.url = self.path
            self.parsed_url = urlparse.urlparse(self.url)
            if len(self.parsed_url[4]):
                self.path = '?'.join([self.parsed_url[2], self.parsed_url[4]])
            else:
                self.path = self.parsed_url[2]
        else:
            self.host_port = self.headers.get("Host")
            self.url = "http://%s/%s" % (self.host_port, self.path)
            self.parsed_url = urlparse.urlparse(self.url)

        self.host_port = self.parsed_url[1]
        if ":" in self.host_port:
            self.host, _, self.port = self.host_port.rpartition(':')
            self.port = int(self.port)
        else:
            self.host = self.host_port
            self.port = 80

        self.read_payload()

        self.dispatch_request()

    def do_CONNECT(self):
        self.method = "https"
        self.host_port = self.path
        self.host, _, self.port = self.host_port.rpartition(':')
        self.port = int(self.port)
        if self.port == 443:
            self.host_port = self.host
        # xlog.debug('CONNECT %s:%s ', host, port)

        self.__realconnection = None
        self.wfile.write(b'HTTP/1.1 200 OK\r\n\r\n')

        certfile = CertUtil.get_cert(self.host)
        try:
            ssl_sock = ssl.wrap_socket(self.connection, keyfile=certfile, certfile=certfile, server_side=True)
        except ssl.SSLError as e:
            xlog.info('ssl error: %s, create full domain cert for host:%s', e, self.host)
            certfile = CertUtil.get_cert(self.host, full_name=True)
            return
        except Exception as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET):
                xlog.exception('ssl.wrap_socket(self.connection=%r) failed: %s path:%s, errno:%s',
                               self.connection, e, self.path, e.args[0])
            return

        self.__realconnection = self.connection
        self.__realwfile = self.wfile
        self.__realrfile = self.rfile
        self.connection = ssl_sock
        self.rfile = self.connection.makefile('rb', self.bufsize)
        self.wfile = self.connection.makefile('wb', 0)

        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65535 or not self.raw_requestline:
                #xlog.warn("read request line len:%d", len(self.raw_requestline))
                return
            if not self.parse_request():
                xlog.warn("parse request fail:%s", self.raw_requestline)
                return
        except NetWorkIOError as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.EPIPE):
                xlog.exception('ssl.wrap_socket(self.connection=%r) failed: %s path:%s, errno:%s', self.connection,
                               e, self.path, e.args[0])
                raise
            return
        except Exception as e:
            xlog.exception("read request line error:%r", e)
            return

        if self.path[0] != '/':
            xlog.warn("CONNECT host:%s path:%s", self.host_port, self.path)
            return

        self.url = 'https://%s%s' % (self.host_port, self.path)

        self.headers = dict((k.title(), v) for k, v in self.headers.items())
        self.read_payload()
        self.dispatch_request()

        if self.__realconnection:
            try:
                self.__realconnection.shutdown(socket.SHUT_WR)
                self.__realconnection.close()
            except NetWorkIOError:
                pass
            finally:
                self.__realconnection = None

    # Called by do_METHOD and do_CONNECT
    def dispatch_request(self):
        if self.host == "www.twitter.com" and self.path == "/xxnet":
            xlog.debug("%s %s", self.command, self.url)
            # for web_ui status page
            # auto detect browser proxy setting is work
            return self.wfile.write(self.self_check_response_data)

        if self.host in self_host:
            if self.port == config.LISTEN_PORT:
                controller = web_control.ControlHandler(self.client_address, self.headers, self.command, self.path,
                                                        self.rfile, self.wfile)
                if self.command == "GET":
                    return controller.do_GET()
                elif self.command == "POST":
                    return controller.do_POST()
                else:
                    xlog.warn("method not defined: %s", self.command)
                    return
            else:
                # xlog.warn("Your browser forward localhost to proxy.")
                return self.forward_local()

        touch_active()
        # record active time.
        # backgroud thread will stop keep connection pool if no request for long time.

        if self.host == "www.google.com" and \
                (self.path.startswith("/search?") or self.path.startswith("/complete/search?") ):
            pass
            #return self.use_DIRECT()

        if self.host in config.HOSTS_GAE or self.host.endswith(config.HOSTS_GAE_ENDSWITH):
            return self.use_GAE()

        # redirect http request to https request
        # avoid key word filter when pass through GFW
        if self.host in config.HOSTS_DIRECT or self.host.endswith(config.HOSTS_DIRECT_ENDSWITH):
            if self.method == "http":
                return self.wfile.write((
                                    'HTTP/1.1 301\r\nLocation: %s\r\nContent-Length: 0\r\n\r\n' % self.path.replace(
                                        'http://', 'https://', 1)).encode())
            else:
                return self.use_DIRECT()

        return self.use_GAE()

    def use_GAE(self):
        if self.command == "OPTIONS":
            return self.send_method_allows(self.headers, self.payload)

        if self.command not in self.gae_support_methods:
            xlog.warn("Method %s not support in GAEProxy for %s", self.command, self.path)
            return self.wfile.write(('HTTP/1.1 404 Not Found\r\n\r\n').encode())

        gae_handler.handler(self.command, self.url, self.headers, self.payload, self.wfile)

    def use_DIRECT(self):
        direct_handler.handler(self.command, self.url, self.headers, self.payload, self.wfile)

    def forward_local(self):
        """
        If browser send localhost:xxx request to GAE_proxy,
        we forward it to localhost.
        """
        http_client = simple_http_client.HTTP_client((self.host, int(self.port)))

        content, status, response = http_client.request(self.command, self.path, self.headers, self.payload)
        if not status:
            xlog.warn("forward_local fail")
            return

        out_list = []
        out_list.append("HTTP/1.1 %d\r\n" % status)
        for key, value in response.getheaders():
            key = key.title()
            out_list.append("%s: %s\r\n" % (key, value))
        out_list.append("\r\n")
        out_list.append(content)

        self.wfile.write("".join(out_list))

    def send_method_allows(self, headers, payload):
        xlog.debug("send method allow list for:%s %s", self.command, self.path)
        # Refer: https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS#Preflighted_requests

        response = \
                "HTTP/1.1 200 OK\r\n"\
                "Access-Control-Allow-Credentials: true\r\n"\
                "Access-Control-Allow-Methods: GET, POST, HEAD, PUT, DELETE, PATCH\r\n"\
                "Access-Control-Max-Age: 1728000\r\n"\
                "Content-Length: 0\r\n"

        req_header = headers.get("Access-Control-Request-Headers", "")
        if req_header:
            response += "Access-Control-Allow-Headers: %s\r\n" % req_header

        origin = headers.get("Origin", "")
        if origin:
            response += "Access-Control-Allow-Origin: %s\r\n" % origin
        else:
            response += "Access-Control-Allow-Origin: *\r\n"

        response += "\r\n"

        self.wfile.write(response)
