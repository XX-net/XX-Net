#from gevent import monkey
#monkey.patch_all()

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


class HTTP_client():
    def __init__(self, address, http_proxy=None, use_https=False, conn_life=30, cert="CA.crt"):
        # address can be set or tuple [host, port]
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

    def create_sock(self):
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

    def get_conn(self):
        try:
            conn = self.sock_pool.get_nowait()
            if self.conn_life and time.time() - conn.create_time > self.conn_life:
                #logging.debug("drop old sock")
                conn.close()
                raise
            return conn
        except:
            sock = self.create_sock()
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
                        xlog.warn("Transfer-Encoding e:%r ", e)
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

        conn = self.get_conn()
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
