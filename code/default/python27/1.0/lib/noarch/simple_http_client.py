

import socket
import httplib
import time
import Queue
import os
import errno
import logging
import utils
import ssl


class Connection():
    def __init__(self, sock):
        self.sock = sock
        self.create_time = time.time()

    def close(self):
        self.sock.close()


class TxtResponse(object):
    def __init__(self, buffer):
        self.read_buffer = buffer
        self.buffer_start = 0
        self.parse()

    def read_line(self):
        n1 = self.read_buffer.find("\r\n", self.buffer_start)
        if n1 == -1:
            raise Exception("read_line fail")

        line = self.read_buffer[self.buffer_start:n1]
        self.buffer_start = n1 + 2
        return line

    def read_headers(self):
        n1 = self.read_buffer.find("\r\n\r\n", self.buffer_start)
        if n1 == -1:
            raise Exception("read_headers fail")
        block = self.read_buffer[self.buffer_start:n1]
        self.buffer_start = n1 + 4
        return block

    def parse(self):
        requestline = self.read_line()
        words = requestline.split()
        if len(words) < 2:
            raise Exception("status line:%s" % requestline)

        self.version = words[0]
        self.status = int(words[1])
        self.info = " ".join(words[2:])

        self.headers = {}
        header_block = self.read_headers()
        lines = header_block.split("\r\n")
        for line in lines:
            p = line.find(":")
            key = line[0:p]
            value = line[p+2:]
            key = str(key.lower())
            self.headers[key] = value

        self.body = self.read_buffer[self.buffer_start:]
        self.read_buffer = ""
        self.buffer_start = 0


class Response(object):
    def __init__(self, ssl_sock):
        self.connection = ssl_sock
        ssl_sock.settimeout(1)
        self.read_buffer = ""
        self.buffer_start = 0
        self.chunked = False

    def read_line(self, timeout=60):
        start_time = time.time()
        sock = self.connection
        sock.setblocking(0)
        try:
            while True:
                n1 = self.read_buffer.find("\r\n", self.buffer_start)
                if n1 > -1:
                    line = self.read_buffer[self.buffer_start:n1]
                    self.buffer_start = n1 + 2
                    return line

                if time.time() - start_time > timeout:
                    raise Exception("time out")
                time.sleep(0.001)
                data = sock.recv(8192)
                if isinstance(data, int):
                    continue
                self.read_buffer += data
        finally:
            sock.setblocking(1)

    def read_headers(self, timeout=60):
        start_time = time.time()
        sock = self.connection
        sock.setblocking(0)
        try:
            while True:
                n1 = self.read_buffer.find("\r\n\r\n", self.buffer_start)
                if n1 > -1:
                    block = self.read_buffer[self.buffer_start:n1]
                    self.buffer_start = n1 + 4
                    return block

                if time.time() - start_time > timeout:
                    raise Exception("time out")

                time.sleep(0.001)
                data = sock.recv(8192)
                self.read_buffer += data
        finally:
            sock.setblocking(1)

    def begin(self, timeout=60):
        start_time = time.time()
        line = self.read_line(timeout)

        requestline = line.rstrip('\r\n')
        words = requestline.split()
        if len(words) < 2:
            raise Exception("status line:%s" % requestline)

        self.version = words[0]
        self.status = int(words[1])
        self.reason = " ".join(words[2:])

        self.headers = {}
        timeout -= time.time() - start_time
        timeout = max(timeout, 0.1)
        header_block = self.read_headers(timeout)
        lines = header_block.split("\r\n")
        for line in lines:
            p = line.find(":")
            key = line[0:p]
            value = line[p+2:]
            key = str(key.lower())
            self.headers[key] = value

        self.content_length = self.getheader("content-length", None)
        if "chunked" in self.getheader("Transfer-Encoding", ""):
            self.chunked = True
            self.chunk_list = []

        if "gzip" in self.getheader("Transfer-Encoding", ""):
            print("not work")

    def getheader(self, key, default_value=""):
        key = key.lower()
        if key in self.headers:
            return self.headers[key]
        else:
            return default_value

    def _read_plain(self, read_len, timeout):
        if read_len is not None and len(self.read_buffer) - self.buffer_start > read_len:
            out_str = self.read_buffer[self.buffer_start:self.buffer_start + read_len]
            self.buffer_start += read_len
            if len(self.read_buffer) == self.buffer_start:
                self.read_buffer = ""
                self.buffer_start = 0
            return out_str

        self.connection.setblocking(0)
        start_time = time.time()
        out_list = [ self.read_buffer[self.buffer_start:] ]
        out_len = len(self.read_buffer) - self.buffer_start

        self.read_buffer = ""
        self.buffer_start = 0

        while time.time() - start_time < timeout:
            if not read_len and out_len > 0:
                break

            if read_len and out_len >= read_len:
                break

            if read_len:
                to_read = read_len - out_len
                to_read = min(to_read, 65535)
            else:
                to_read = 65535

            data = self.connection.recv(to_read)
            if data:
                out_list.append(data)
                out_len += len(data)
        if read_len is not None and out_len < read_len:
            raise Exception("time out")

        return "".join(out_list)

    def _read_chunked(self, timeout):
        line = self.read_line(timeout)
        chunk_size = int(line, 16)
        dat = self._read_plain(chunk_size + 2, timeout)
        return dat[:-2]

    def read(self, read_len=None, timeout=60):
        #if not read_len and self.content_length is not None:
        #    read_len = int(self.content_length)

        if not self.chunked:
            return self._read_plain(read_len, timeout)
        else:
            return self._read_chunked(timeout)

    def readall(self, timeout=60):
        start_time = time.time()
        if self.chunked:
            out_list = []
            while True:
                time_left = timeout - (time.time() - start_time)
                if time_left < 0:
                    raise Exception("time out")

                dat = self._read_chunked(time_left)
                if not dat:
                    break

                out_list.append(dat)

            return "".join(out_list)
        else:
            return self._read_plain(int(self.content_length), timeout=timeout)


class HTTP_client():
    def __init__(self, address, http_proxy=None, use_https=False, conn_life=30, cert="CA.crt"):
        # address can be set or tuple [host, port]
        if isinstance(address, str):
            if use_https:
                self.address = (address, 443)
            else:
                self.address = (address, 80)
        else:
            self.address = address

        self.http_proxy = http_proxy
        self.use_https = use_https
        self.conn_life = conn_life
        self.cert = cert


        if not self.http_proxy:
            self.path_base = ""
        else:
            if use_https:
                self.path_base = "https://%s:%d" % self.address
            else:
                self.path_base = "http://%s:%d" % self.address

        self.sock_pool = Queue.Queue()

    def create_sock(self, host):
        if ":" in self.address[0]:
            sock = socket.socket(socket.AF_INET6)
        else:
            sock = socket.socket(socket.AF_INET)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32*1024)
        sock.settimeout(5)
        try:
            if not self.http_proxy:
                if self.use_https:
                    if os.path.isfile(self.cert):
                        sock = ssl.wrap_socket(sock, ca_certs=self.cert, do_handshake_on_connect=True)
                    else:
                        sock = ssl.wrap_socket(sock, do_handshake_on_connect=True)

                sock.connect(self.address)
            else:
                sock.connect(self.http_proxy)
        except Exception as e:
            #logging.warn("create connect to %s:%d fail:%r", self.address[0], self.address[1], e)
            sock.close()
            return None

        return sock

    def get_conn(self, host):
        try:
            conn = self.sock_pool.get_nowait()
            if self.conn_life and time.time() - conn.create_time > self.conn_life:
                #logging.debug("drop old sock")
                conn.close()
                raise
            return conn
        except:
            sock = self.create_sock(host)
            if not sock:
                return None

            conn = Connection(sock)
            return conn

    def request(self, method="GET", path="", header={}, data="", timeout=60):
        response = None
        start_time = time.time()
        end_time = start_time + timeout
        try:
            time_request = time.time()
            header["Content-Length"] = str(len(data))
            host = self.address[0] + ":" + str(self.address[1])
            header["Host"] = host
            if path.startswith("/"):
                req_path = self.path_base + path
            else:
                req_path = self.path_base + "/" + path
            response = self.fetch(method, host, req_path, header, data, timeout=timeout)
            if not response:
                #logging.warn("post return fail")
                return "", False, response

            if response.status != 200:
                #logging.warn("post status:%r", response.status)
                return "", response.status, response

            response_headers = dict((k.title(), v) for k, v in response.getheaders())

            if 'Transfer-Encoding' in response_headers:
                length = 0
                data_buffer = []
                while True:
                    try:
                        data = response.read(8192)
                    except httplib.IncompleteRead, e:
                        data = e.partial
                    except Exception as e:
                        # xlog.warn("Transfer-Encoding e:%r ", e)
                        return "", False, response
                    

                    if not data:
                        break
                    else:
                        data_buffer.append(data)

                #self.sock_pool.put(response.conn)
                response_data = "".join(data_buffer)
                return response_data, 200, response
            else:
                content_length = int(response.getheader('Content-Length', 0))
                start, end, length = 0, content_length-1, content_length

                last_read_time = time.time()
                data_buffer = []
                while True:
                    if start > end:
                        self.sock_pool.put(response.conn)
                        #logging.info("POST t:%d s:%d %d %s", (time.time()-time_request)*1000, length, response.status, req_path)
                        response_data = "".join(data_buffer)
                        return response_data, 200, response

                    data = response.read(65535)
                    if not data:
                        if time.time() - last_read_time > 20 or time.time() > end_time:
                            response.close()
                            #logging.warn("read timeout t:%d len:%d left:%d %s", (time.time()-time_request)*1000, length, (end-start), req_path)
                            return "", False, response
                        else:
                            time.sleep(0.1)
                            continue

                    last_read_time = time.time()
                    data_len = len(data)
                    start += data_len
                    data_buffer.append(data)
        except IOError, e:
            if e.errno == errno.EPIPE:
                pass
        except Exception as e:
            logging.exception("Post e:%r", e)
            self.sock = None
        return "", 400, response


    def fetch(self, method, host, path, headers, payload, bufsize=8192, timeout=20):
        request_data = '%s %s HTTP/1.1\r\n' % (method, path)
        request_data += ''.join('%s: %s\r\n' % (k, v) for k, v in headers.items())
        request_data += '\r\n'

        #print("request:%s" % request_data)
        #print("payload:%s" % payload)

        conn = self.get_conn(host)
        if not conn:
            logging.warn("get sock fail")
            return

        if len(request_data) + len(payload) < 1300:
            payload = request_data.encode() + payload
        else:
            conn.sock.send(request_data.encode())
            
        payload_len = len(payload)
        start = 0
        while start < payload_len:
            send_size = min(payload_len - start, 65535)
            sended = conn.sock.send(payload[start:start+send_size])
            start += sended

        conn.sock.settimeout(timeout)
        response = httplib.HTTPResponse(conn.sock, buffering=True)

        response.conn = conn
        try:
            #orig_timeout = conn.sock.gettimeout()
            #conn.sock.settimeout(timeout)
            response.begin()
            #conn.sock.settimeout(orig_timeout)
        except httplib.BadStatusLine as e:
            logging.warn("fetch bad status line:%r", e)
            response = None
        except Exception as e:
            logging.warn("fetch:%r", e)
        return response
