import os
import datetime
import threading
import socket
import errno
import sys
import select
import time
import json
import base64
import hashlib
import struct

try:
    from urllib.parse import urlparse, urlencode, parse_qs
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urlparse import urlparse, parse_qs
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError
    import mimetools

import xlog
import utils


class GetReqTimeout(Exception):
    pass


class ParseReqFail(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        # for %s
        return repr(self.message)

    def __repr__(self):
        # for %r
        return repr(self.message)


class HttpServerHandler():
    WebSocket_MAGIC_GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    default_request_version = b"HTTP/1.1"

    rbufsize = 32 * 1024
    wbufsize = 32 * 1024

    res_headers = {}

    def __init__(self, sock, client, args, logger=None):
        self.connection = sock
        sock.setblocking(1)
        sock.settimeout(60)
        self.rfile = self.connection.makefile('rb', self.rbufsize)
        self.wfile = self.connection.makefile('wb', self.wbufsize)
        self.client_address = client
        self.args = args
        if logger:
            self.logger = logger
        else:
            self.logger = xlog.getLogger("simple_http_server")
        # self.logger.debug("new connect from:%s", self.address_string())

        self.setup()

    def set_CORS(self, headers):
        self.res_headers = headers

    def setup(self):
        pass

    def __del__(self):
        try:
            socket.socket.close(self.connection)
        except:
            pass

    def handle(self):
        # self.logger.info('Connected from %r', self.client_address)
        while True:
            try:
                self.close_connection = 1
                self.handle_one_request()
            except Exception as e:
                self.logger.warn("handle err:%r close", e)
                self.close_connection = 1

            if self.close_connection:
                break
        self.connection.close()
        # self.logger.debug("closed from %s:%d", self.client_address[0], self.client_address[1])

    def address_string(self):
        return '%s:%s' % self.client_address[:2]

    def parse_headers(self):
        headers = {}
        while True:
            line = self.rfile.readline(65537)
            line = line.strip()
            if len(line) == 0:
                break

            k, v = line.split(b":", 1)
            key = k.title()
            headers[key] = v.lstrip()
        return headers

    def parse_request(self):
        try:
            self.raw_requestline = self.rfile.readline(65537)
        except:
            raise GetReqTimeout()

        if not self.raw_requestline:
            raise GetReqTimeout()

        if len(self.raw_requestline) > 65536:
            raise ParseReqFail("Recv command line too large")

        if self.raw_requestline[0] == '\x16':
            raise socket.error

        self.command = b''  # set in case of error on the first line
        self.path = b''
        self.request_version = version = self.default_request_version

        requestline = self.raw_requestline
        requestline = requestline.rstrip(b'\r\n')
        self.requestline = requestline
        words = requestline.split()
        if len(words) == 3:
            command, path, version = words
            if version[:5] != b'HTTP/':
                raise ParseReqFail("Req command format fail:%s" % requestline)

            try:
                base_version_number = version.split(b'/', 1)[1]
                version_number = base_version_number.split(b".")
                # RFC 2145 section 3.1 says there can be only one "." and
                #   - major and minor numbers MUST be treated as
                #      separate integers;
                #   - HTTP/2.4 is a lower version than HTTP/2.13, which in
                #      turn is lower than HTTP/12.3;
                #   - Leading zeros MUST be ignored by recipients.
                if len(version_number) != 2:
                    raise ParseReqFail("Req command format fail:%s" % requestline)
                version_number = int(version_number[0]), int(version_number[1])
            except (ValueError, IndexError):
                raise ParseReqFail("Req command format fail:%s" % requestline)
            if version_number >= (1, 1):
                self.close_connection = 0
            if version_number >= (2, 0):
                raise ParseReqFail("Req command format fail:%s" % requestline)
        elif len(words) == 2:
            command, path = words
            self.close_connection = 1
            if command != b'GET':
                raise ParseReqFail("Req command format HTTP/0.9 line:%s" % requestline)
        elif not words:
            raise ParseReqFail("Req command format fail:%s" % requestline)
        else:
            raise ParseReqFail("Req command format fail:%s" % requestline)
        self.command, self.path, self.request_version = command, path, version

        # Parse HTTP headers
        self.headers = self.parse_headers()

        self.host = self.headers.get(b'Host', b"")
        conntype = self.headers.get(b'Connection', b"")
        if conntype.lower() == b'close':
            self.close_connection = 1
        elif conntype.lower() == b'keep-alive':
            self.close_connection = 0

        self.upgrade = self.headers.get(b'Upgrade', b"").lower()

        return True

    def unpack_reqs(self, reqs):
        query = {}
        for key, val1 in reqs.items():
            if isinstance(val1, list):
                query[key] = val1[0]
            else:
                query[key] = val1
        return query

    def handle_one_request(self):
        try:
            self.parse_request()

            self.close_connection = 0

            if self.upgrade == b"websocket":
                self.do_WebSocket()
            elif self.command == b"GET":
                self.do_GET()
            elif self.command == b"POST":
                self.do_POST()
            elif self.command == b"CONNECT":
                self.do_CONNECT()
            elif self.command == b"HEAD":
                self.do_HEAD()
            elif self.command == b"DELETE":
                self.do_DELETE()
            elif self.command == b"OPTIONS":
                self.do_OPTIONS()
            elif self.command == b"PUT":
                self.do_PUT()
            else:
                self.logger.warn("unhandler cmd:%s path:%s from:%s", self.command, self.path, self.address_string())
                return

            self.wfile.flush()  # actually send the response if not already done.
        except ParseReqFail as e:
            self.logger.warn("parse req except:%r", e)
            self.close_connection = 1
        except socket.error as e:
            self.logger.warn("socket error:%r", e)
            self.close_connection = 1
        except IOError as e:
            if e.errno == errno.EPIPE:
                self.logger.warn("PIPE error:%r", e)
                pass
            else:
                self.logger.warn("IOError:%r", e)
                pass
            # except OpenSSL.SSL.SysCallError as e:
            #    self.logger.warn("socket error:%r", e)
            self.close_connection = 1
        except GetReqTimeout as e:
            # self.logger.exception("GetReqTimeout %r", e)
            self.close_connection = 1
        except Exception as e:
            self.logger.exception("handler:%r cmd:%s path:%s from:%s", e, self.command, self.path,
                                  self.address_string())
            self.close_connection = 1

    def WebSocket_handshake(self):
        protocol = self.headers.get(b"Sec-WebSocket-Protocol", b"")
        if protocol:
            self.logger.info("Sec-WebSocket-Protocol:%s", protocol)
        version = self.headers.get(b"Sec-WebSocket-Version", b"")
        if version != b"13":
            self.logger.warn("Sec-WebSocket-Version:%s", version)
            self.close_connection = 1
            return False

        key = self.headers[b"Sec-WebSocket-Key"]
        self.WebSocket_key = key
        digest = base64.b64encode(hashlib.sha1(key + self.WebSocket_MAGIC_GUID).hexdigest().decode('hex'))
        response = b'HTTP/1.1 101 Switching Protocols\r\n'
        response += b'Upgrade: websocket\r\n'
        response += b'Connection: Upgrade\r\n'
        response += b'Sec-WebSocket-Accept: %s\r\n\r\n' % digest
        self.wfile.write(response)
        return True

    def WebSocket_send_message(self, message):
        self.wfile.write(chr(129))
        length = len(message)
        if length <= 125:
            self.wfile.write(chr(length))
        elif length >= 126 and length <= 65535:
            self.wfile.write(126)
            self.wfile.write(struct.pack(">H", length))
        else:
            self.wfile.write(127)
            self.wfile.write(struct.pack(">Q", length))
        self.wfile.write(message)

    def WebSocket_receive_worker(self):
        while not self.close_connection:
            try:
                h = self.rfile.read(2)
                if h is None or len(h) == 0:
                    break

                length = ord(h[1]) & 127
                if length == 126:
                    length = struct.unpack(">H", self.rfile.read(2))[0]
                elif length == 127:
                    length = struct.unpack(">Q", self.rfile.read(8))[0]
                masks = [ord(byte) for byte in self.rfile.read(4)]
                decoded = ""
                for char in self.rfile.read(length):
                    decoded += chr(ord(char) ^ masks[len(decoded) % 4])
                try:
                    self.WebSocket_on_message(decoded)
                except Exception as e:
                    self.logger.warn("WebSocket %s except on process message, %r", self.WebSocket_key, e)
            except Exception as e:
                self.logger.exception("WebSocket %s exception:%r", self.WebSocket_key, e)
                break

        self.WebSocket_on_close()
        self.close_connection = 1

    def WebSocket_on_message(self, message):
        self.logger.debug("websocket message:%s", message)

    def WebSocket_on_close(self):
        self.logger.debug("websocket closed")

    def do_WebSocket(self):
        self.logger.info("WebSocket cmd:%s path:%s from:%s", self.command, self.path, self.address_string())
        self.logger.info("Host:%s", self.headers.get("Host", ""))

        if not self.WebSocket_on_connect():
            return

        if not self.WebSocket_handshake():
            self.logger.warn("WebSocket handshake fail.")
            return

        self.WebSocket_receive_worker()

    def WebSocket_on_connect(self):
        # Define the function and return True to accept
        self.logger.warn("unhandled WebSocket from %s", self.address_string())
        self.send_error(501, "Not supported")
        self.close_connection = 1

        return False

    def do_GET(self):
        self.logger.warn("unhandler cmd:%s from:%s", self.command, self.address_string())

    def do_POST(self):
        self.logger.warn("unhandler cmd:%s from:%s", self.command, self.address_string())

    def do_PUT(self):
        self.logger.warn("unhandler cmd:%s from:%s", self.command, self.address_string())

    def do_DELETE(self):
        self.logger.warn("unhandler cmd:%s from:%s", self.command, self.address_string())

    def do_OPTIONS(self):
        self.logger.warn("unhandler cmd:%s from:%s", self.command, self.address_string())

    def do_HEAD(self):
        self.logger.warn("unhandler cmd:%s from:%s", self.command, self.address_string())

    def do_CONNECT(self):
        self.logger.warn("unhandler cmd:%s from:%s", self.command, self.address_string())

    def send_not_found(self):
        self.close_connection = 1
        content = b"File not found."
        self.wfile.write(b'HTTP/1.1 404\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%s' % (len(content), content))

    def send_error(self, code, message=None):
        self.close_connection = 1
        self.wfile.write(b'HTTP/1.1 %d\r\n' % code)
        self.wfile.write(b'Connection: close\r\n\r\n')
        if message:
            self.wfile.write(utils.to_bytes(message))

    def send_response(self, mimetype=b"", content=b"", headers=b"", status=200):
        data = []
        data.append(b'HTTP/1.1 %d\r\n' % status)
        if len(mimetype):
            data.append(b'Content-Type: %s\r\n' % utils.to_bytes(mimetype))

        content = utils.to_bytes(content)

        for key in self.res_headers:
            data.append(b"%s: %s\r\n" % (utils.to_bytes(key), utils.to_bytes(self.res_headers[key])))
        data.append(b'Content-Length: %d\r\n' % len(content))

        if len(headers):
            if isinstance(headers, dict):
                headers = utils.to_bytes(headers)
                if b'Content-Length' in headers:
                    del headers[b'Content-Length']
                for key in headers:
                    data.append(b"%s: %s\r\n" % (utils.to_bytes(key), utils.to_bytes(headers[key])))
            elif isinstance(headers, str):
                data.append(headers.encode("utf-8"))
            elif isinstance(headers, bytes):
                data.append(headers)
        data.append(b"\r\n")

        if len(content) < 1024:
            data.append(content)
            data_str = b"".join(data)
            self.wfile.write(data_str)
        else:
            data_str = b"".join(data)
            self.wfile.write(data_str)
            if len(content):
                self.wfile.write(content)

    def send_redirect(self, url, headers={}, content=b"", status=307, text=b"Temporary Redirect"):
        url = utils.to_bytes(url)
        headers = utils.to_bytes(headers)
        content = utils.to_bytes(content)

        headers[b"Location"] = url
        data = []
        data.append(b'HTTP/1.1 %d\r\n' % status)
        data.append(b'Content-Length: %s\r\n' % len(content))

        if len(headers):
            if isinstance(headers, dict):
                for key in headers:
                    data.append(b"%s: %s\r\n" % (key, headers[key]))
            elif isinstance(headers, str):
                data.append(headers)
        data.append(b"\r\n")

        data.append(content)
        data_str = b"".join(data)
        self.wfile.write(data_str)

    def send_response_nc(self, mimetype=b"", content=b"", headers=b"", status=200):
        no_cache_headers = b"Cache-Control: no-cache, no-store, must-revalidate\r\nPragma: no-cache\r\nExpires: 0\r\n"
        return self.send_response(mimetype, content, no_cache_headers + headers, status)

    def send_file(self, filename, mimetype):
        try:
            if not os.path.isfile(filename):
                self.send_not_found()
                return

            file_size = os.path.getsize(filename)
            tme = (datetime.datetime.today() + datetime.timedelta(minutes=0)).strftime('%a, %d %b %Y %H:%M:%S GMT')
            head = b'HTTP/1.1 200\r\nAccess-Control-Allow-Origin: *\r\nCache-Control:no-cache\r\n'
            head += b'Expires: %s\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % utils.to_bytes(
                (tme, mimetype, file_size))
            self.wfile.write(head)

            with open(filename, 'rb') as fp:
                while True:
                    data = fp.read(65535)
                    if not data:
                        break
                    self.wfile.write(data)
        except:
            pass
            # self.logger.warn("download broken")

    def response_json(self, res_arr, headers=b""):
        data = json.dumps(utils.to_str(res_arr), indent=0, sort_keys=True)
        self.send_response(b'application/json', data, headers=headers)


class HTTPServer():
    def __init__(self, address, handler, args=(), use_https=False, cert="", logger=xlog, max_thread=3024,
                 check_listen_interval=None):
        self.sockets = []
        if isinstance(address, tuple):
            self.server_address = [address]
        else:
            # server can listen multi-port
            self.server_address = address
        self.handler = handler
        self.logger = logger
        self.args = args
        self.use_https = use_https
        self.cert = cert
        self.max_thread = max_thread
        self.check_listen_interval = check_listen_interval
        # self.logger.info("server %s:%d started.", address[0], address[1])

    def start(self):
        self.init_socket()
        self.http_thread = threading.Thread(target=self.serve_forever, name="serve_%s" % self.server_address)
        self.http_thread.daemon = True
        self.http_thread.start()

    def init_socket(self):
        server_address = self.server_address
        ips = [ip for ip, _ in server_address]
        listen_all_v4 = b"0.0.0.0" in ips
        listen_all_v6 = b"::" in ips
        for ip, port in server_address:
            if ip not in (b"0.0.0.0", b"::") and (
                    listen_all_v4 and b'.' in ip or
                    listen_all_v6 and b':' in ip):
                continue
            self.add_listen((ip, port))

    def add_listen(self, addr):
        ip = addr[0]
        port = addr[1]
        if isinstance(ip, str):
            ip = ip.encode("ascii")

        if b":" in ip:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
        addr = tuple((ip, port))
        try:
            sock.bind(addr)
        except Exception as e:
            err_string = "bind to %s:%d fail:%r" % (addr[0], addr[1], e)
            self.logger.error(err_string)
            raise Exception(err_string)

        if self.use_https:
            import OpenSSL
            if hasattr(OpenSSL.SSL, "TLSv1_2_METHOD"):
                ssl_version = OpenSSL.SSL.TLSv1_2_METHOD
            elif hasattr(OpenSSL.SSL, "TLSv1_1_METHOD"):
                ssl_version = OpenSSL.SSL.TLSv1_1_METHOD
            elif hasattr(OpenSSL.SSL, "TLSv1_METHOD"):
                ssl_version = OpenSSL.SSL.TLSv1_METHOD

            ctx = OpenSSL.SSL.Context(ssl_version)
            # server.pem's location (containing the server private key and the server certificate).
            fpem = self.cert
            ctx.use_privatekey_file(fpem)
            ctx.use_certificate_file(fpem)
            sock = OpenSSL.SSL.Connection(ctx, sock)
        sock.listen(200)
        self.sockets.append(sock)
        self.logger.info("server %s:%d started.", addr[0], addr[1])

    def serve_forever(self):
        self.running = True
        if not self.sockets:
            self.init_socket()

        last_connect_time = time.time()
        if hasattr(select, 'epoll'):
            fn_map = {}
            p = select.epoll()
            for sock in self.sockets:
                fn = sock.fileno()
                sock.setblocking(0)
                p.register(fn, select.EPOLLIN | select.EPOLLHUP | select.EPOLLPRI)
                fn_map[fn] = sock

            while self.running:
                try:
                    try:
                        events = p.poll(timeout=1)
                    except IOError as e:
                        self.logger.exception("poll except:%r", e)
                        if e.errno != 4:  # EINTR:
                            raise
                        else:
                            time.sleep(1)
                            continue

                    if not self.running:
                        break

                    for fn, event in events:
                        if fn not in fn_map:
                            self.logger.error("p.poll get fn:%d", fn)
                            continue

                        sock = fn_map[fn]
                        try:
                            (sock, address) = sock.accept()
                        except IOError as e:
                            self.logger.warn("socket accept fail %r.", e)
                            if e.args[0] == 11:
                                # Resource temporarily unavailable is EAGAIN
                                # and that's not really an error.
                                # It means "I don't have answer for you right now and
                                # you have told me not to wait,
                                # so here I am returning without answer."
                                continue

                            if e.args[0] == 24:
                                self.logger.warn("max file opened when sock.accept")
                                time.sleep(30)
                                continue

                            self.logger.warn("socket accept fail(errno: %s).", e.args[0])
                            continue

                        last_connect_time = time.time()
                        try:
                            self.process_connect(sock, address)
                        except Exception as e:
                            self.logger.exception("process connect error:%r", e)

                    if self.check_listen_interval and last_connect_time + self.check_listen_interval < time.time():
                        self.check_listen_port_or_reset()
                        last_connect_time = time.time()
                except Exception as e:
                    self.logger.exception("serve except:%r", e)
        else:
            while self.running:
                try:
                    try:
                        r, w, e = select.select(self.sockets, [], [], 1)
                    except Exception as e:
                        continue

                    if not self.running:
                        break

                    for rsock in r:
                        try:
                            (sock, address) = rsock.accept()
                        except IOError as e:
                            self.logger.warn("socket accept fail(errno: %s).", e.args[0])
                            if e.args[0] == 10022:
                                self.logger.info("restart socket server.")
                                self.server_close()
                                self.init_socket()
                            break

                        last_connect_time = time.time()
                        self.process_connect(sock, address)

                    if self.check_listen_interval and last_connect_time + self.check_listen_interval < time.time():
                        self.check_listen_port_or_reset()
                        last_connect_time = time.time()
                except Exception as e:
                    self.logger.exception("serve except:%r", e)
        self.server_close()

    def process_connect(self, sock, address):
        # self.logger.debug("connect from %s:%d", address[0], address[1])
        if threading.active_count() > self.max_thread:
            self.logger.warn("thread num exceed the limit. drop request from %s.", address)
            sock.close()
            return

        client_obj = self.handler(sock, address, self.args)
        client_thread = threading.Thread(target=client_obj.handle, name="handle_%s:%d" % address)
        client_thread.start()

    def check_listen_port(self, ip, port):
        if ':' in ip:
            info = [(socket.AF_INET6, socket.SOCK_STREAM, 0, "", (ip, port, 0, 0))]
        else:
            if "0.0.0.0" in ip:
                ip = "127.0.0.1"

            info = [(socket.AF_INET, socket.SOCK_STREAM, 0, "", (ip, port))]

        for res in info:
            af, socktype, proto, canonname, sa = res
            ip_port = (sa[0], sa[1])
            s = None
            try:
                s = socket.socket(af, socktype, proto)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.settimeout(1)
                s.connect(ip_port)
                return s
            except socket.error as e:
                xlog.warn("connect %s except:%r", sa, e)
                if s:
                    s.close()

    def check_listen_port_or_reset(self):
        for ip, port in self.server_address:
            res = self.check_listen_port(ip, port)
            if res:
                return

            self.logger.warn("Listen %s:%d check failed, try restart listening", ip, port)
            self.shutdown()
            time.sleep(3)
            self.start()
            return

    def shutdown(self):
        self.logger.info("shutdown")
        self.running = False
        self.server_close()

    def server_close(self):
        self.logger.info("server_close")
        for sock in self.sockets:
            sock.close()
        self.sockets = []


class TestHttpServer(HttpServerHandler):
    def __init__(self, sock, client, args):
        self.data_path = utils.to_bytes(args)
        HttpServerHandler.__init__(self, sock, client, args)

    def generate_random_lowercase(self, n):
        min_lc = ord(b'a')
        len_lc = 26
        ba = bytearray(os.urandom(n))
        for i, b in enumerate(ba):
            ba[i] = min_lc + b % len_lc  # convert 0..255 to 97..122
        # sys.stdout.buffer.write(ba)
        return ba

    def WebSocket_on_connect(self):
        return True

    def WebSocket_on_message(self, message):
        self.WebSocket_send_message(message)

    def do_GET(self):
        url_path = urlparse(self.path).path
        req = urlparse(self.path).query
        reqs = parse_qs(req, keep_blank_values=True)

        self.logger.debug("GET %s from %s:%d", self.path, self.client_address[0], self.client_address[1])

        if url_path == b"/test":
            tme = (datetime.datetime.today() + datetime.timedelta(minutes=330)).strftime('%a, %d %b %Y %H:%M:%S GMT')
            tme = utils.to_bytes(tme)
            head = b'HTTP/1.1 200\r\nAccess-Control-Allow-Origin: *\r\nCache-Control:public, max-age=31536000\r\n'
            head += b'Expires: %s\r\nContent-Type: text/plain\r\nContent-Length: 4\r\n\r\nOK\r\n' % (tme)
            self.wfile.write(head)

        elif url_path == b'/':
            data = b"OK\r\n"
            self.wfile.write(
                b'HTTP/1.1 200\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: %d\r\n\r\n%s' % (len(data), data))
        elif url_path == b'/null':
            mimetype = b"application/x-binary"
            if b"size" in reqs:
                file_size = int(reqs[b'size'][0])
            else:
                file_size = 1024 * 1024 * 1024

            self.wfile.write(b'HTTP/1.1 200\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, file_size))
            start = 0
            data = self.generate_random_lowercase(65535)
            while start < file_size:
                left = file_size - start
                send_batch = min(left, 65535)
                self.wfile.write(data[:send_batch])
                start += send_batch
        else:
            if b".." in url_path[1:]:
                return self.send_not_found()

            target = os.path.join(self.data_path, url_path[1:])
            if os.path.isfile(target):
                self.send_file(target, b"application/x-binary")
            else:
                self.wfile.write(b'HTTP/1.1 404\r\nContent-Length: 0\r\n\r\n')


def main(data_path="."):
    xlog.info("listen http on 8880")
    httpd = HTTPServer(('', 8880), TestHttpServer, data_path)
    httpd.start()

    while True:
        time.sleep(10)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        data_path = sys.argv[1]
    else:
        data_path = ""

    try:
        main(data_path=data_path)
    except Exception:
        import traceback

        traceback.print_exc(file=sys.stdout)
    except KeyboardInterrupt:
        sys.exit()
