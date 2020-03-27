import time
import socket
import struct
import urllib.parse
import select

import utils
from xlog import getLogger
xlog = getLogger("x_tunnel")

from . import global_var as g
from . import proxy_session


def netloc_to_host_port(netloc, default_port=80):
    if isinstance(netloc, str):
        netloc = netloc.encode("ascii")

    if b":" in netloc:
        host, _, port = netloc.rpartition(b':')
        port = int(port)
    else:
        host = netloc
        port = default_port
    return host, port


class Socks5Server():
    handle_num = 0

    def __init__(self, sock, client, args):
        self.connection = sock
        self.rfile = self.connection.makefile("rb", -1)
        self.wfile = self.connection.makefile("wb", 0)
        self.client_address = client
        self.read_buffer = b""
        self.buffer_start = 0
        self.args = args

    def handle(self):
        self.__class__.handle_num += 1
        try:
            r, w, e = select.select([self.connection], [], [])
            socks_version = self.read_bytes(1)
            if not socks_version:
                return

            if socks_version == b"\x04":
                self.socks4_handler()
            elif socks_version == b"\x05":
                self.socks5_handler()
            elif socks_version == b"C":
                self.https_handler()
            elif socks_version in [b"G", b"P", b"D", b"O", b"H", b"T"]:
                self.http_handler(socks_version)
                return
            else:
                xlog.warn("socks version:%s not supported",  utils.str2hex(socks_version))
                return

        except socket.error as e:
            xlog.debug('socks handler read error %r', e)
            return
        except Exception as e:
            xlog.exception("any err:%r", e)

    def read_null_end_line(self):
        sock = self.connection
        sock.setblocking(0)
        try:
            while True:
                n1 = self.read_buffer.find(b"\x00", self.buffer_start)
                if n1 > -1:
                    line = self.read_buffer[self.buffer_start:n1]
                    self.buffer_start = n1 + 1
                    return line

                try:
                    data = sock.recv(8192)
                except socket.error as e:
                    # logging.exception("e:%r", e)
                    if e.errno in [2, 11, 10035]:
                        time.sleep(0.01)
                        continue
                    else:
                        raise e

                self.read_buffer += data
        finally:
            sock.setblocking(1)

    def read_crlf_line(self):
        sock = self.connection
        sock.setblocking(0)
        try:
            while True:
                n1 = self.read_buffer.find(b"\r\n", self.buffer_start)
                if n1 > -1:
                    line = self.read_buffer[self.buffer_start:n1]
                    self.buffer_start = n1 + 2
                    return line

                try:
                    data = sock.recv(8192)
                except socket.error as e:
                    # logging.exception("e:%r", e)
                    if e.errno in [2, 11, 10035]:
                        time.sleep(0.01)
                        continue
                    else:
                        raise e

                self.read_buffer += data
        finally:
            sock.setblocking(1)

    def read_headers(self):
        sock = self.connection
        sock.setblocking(0)
        try:
            while True:
                if self.read_buffer[self.buffer_start:] == b"\r\n":
                    self.buffer_start += 2
                    return b""

                n1 = self.read_buffer.find(b"\r\n\r\n", self.buffer_start)
                if n1 > -1:
                    block = self.read_buffer[self.buffer_start:n1]
                    self.buffer_start = n1 + 4
                    return block

                try:
                    data = sock.recv(8192)
                except socket.error as e:
                    # logging.exception("e:%r", e)
                    if e.errno in [2, 11, 10035]:
                        time.sleep(0.01)
                        continue
                    else:
                        raise e

                self.read_buffer += data
        finally:
            sock.setblocking(1)

    def read_bytes(self, size):
        sock = self.connection
        sock.setblocking(1)
        try:
            while True:
                left = len(self.read_buffer) - self.buffer_start
                if left >= size:
                    break

                need = size - left

                try:
                    data = sock.recv(need)
                except socket.error as e:
                    # logging.exception("e:%r", e)
                    if e.errno in [2, 11, 10035]:
                        time.sleep(0.01)
                        continue
                    else:
                        raise e

                if len(data):
                    self.read_buffer += data
                else:
                    raise socket.error("recv fail")
        finally:
            sock.setblocking(1)

        data = self.read_buffer[self.buffer_start:self.buffer_start + size]
        self.buffer_start += size
        return data

    def socks4_handler(self):
        # Socks4 or Socks4a
        sock = self.connection
        cmd = ord(self.read_bytes(1))
        if cmd != 1:
            xlog.warn("Socks4 cmd:%d not supported", cmd)
            return

        data = self.read_bytes(6)
        port = struct.unpack(">H", data[0:2])[0]
        addr_pack = data[2:6]
        if addr_pack[0:3] == b'\x00\x00\x00' and addr_pack[3] != b'\x00':
            domain_mode = True
        else:
            ip = socket.inet_ntoa(addr_pack)
            domain_mode = False

        user_id = self.read_null_end_line()
        if len(user_id):
            xlog.debug("Socks4 user_id:%s", user_id)

        if domain_mode:
            addr = self.read_null_end_line()
        else:
            addr = ip

        conn_id = proxy_session.create_conn(sock, addr, port)
        if not conn_id:
            xlog.warn("Socks4 connect fail, no conn_id")
            reply = b"\x00\x5b\x00" + addr_pack + struct.pack(">H", port)
            sock.send(reply)
            return

        xlog.info("Socks4:%r to %s:%d, conn_id:%d", self.client_address, addr, port, conn_id)
        reply = b"\x00\x5a" + addr_pack + struct.pack(">H", port)
        sock.send(reply)

        if len(self.read_buffer) - self.buffer_start:
            g.session.conn_list[conn_id].transfer_received_data(self.read_buffer[self.buffer_start:])

        g.session.conn_list[conn_id].start(block=True)

    def socks5_handler(self):
        sock = self.connection
        auth_mode_num = ord(self.read_bytes(1))
        data = self.read_bytes(auth_mode_num)

        sock.send(b"\x05\x00")  # socks version 5, no auth needed.
        try:
            data = self.read_bytes(4)
        except Exception as e:
            xlog.debug("socks5 auth num:%d, list:%s", auth_mode_num, utils.str2hex(data))
            xlog.warn("socks5 protocol error:%r", e)
            return

        socks_version = data[0]
        if socks_version != 5:
            xlog.warn("request version:%d error", socks_version)
            return

        command = data[1]
        if command != 1:  # 1. Tcp connect
            xlog.warn("request not supported command mode:%d", command)
            sock.send(b"\x05\x07\x00\x01")  # Command not supported
            return

        addrtype_pack = data[3:4]
        addrtype = ord(addrtype_pack)
        if addrtype == 1:  # IPv4
            addr_pack = self.read_bytes(4)
            addr = socket.inet_ntoa(addr_pack)
        elif addrtype == 3:  # Domain name
            domain_len_pack = self.read_bytes(1)[0:1]
            domain_len = ord(domain_len_pack)
            domain = self.read_bytes(domain_len)
            addr_pack = domain_len_pack + domain
            addr = domain
        elif addrtype == 4:  # IPv6
            addr_pack = self.read_bytes(16)
            addr = socket.inet_ntop(socket.AF_INET6, addr_pack)
        else:
            xlog.warn("request address type unknown:%d", addrtype)
            sock.send(b"\x05\x07\x00\x01")  # Command not supported
            return

        port = struct.unpack('>H', self.rfile.read(2))[0]

        conn_id = proxy_session.create_conn(sock, addr, port)
        if not conn_id:
            xlog.warn("create conn fail")
            reply = b"\x05\x01\x00" + addrtype_pack + addr_pack + struct.pack(">H", port)
            sock.send(reply)
            return

        xlog.info("socks5 %r connect to %s:%d conn_id:%d", self.client_address, addr, port, conn_id)
        reply = b"\x05\x00\x00" + addrtype_pack + addr_pack + struct.pack(">H", port)
        sock.send(reply)

        if len(self.read_buffer) - self.buffer_start:
            g.session.conn_list[conn_id].transfer_received_data(self.read_buffer[self.buffer_start:])

        g.session.conn_list[conn_id].start(block=True)

    def https_handler(self):
        line = self.read_crlf_line()
        line = line.decode('iso-8859-1')
        words = line.split()
        if len(words) == 3:
            command, path, version = words
        elif len(words) == 2:
            command, path = words
            version = b"HTTP/1.1"
        else:
            xlog.warn("https req line fail:%s", line)
            return

        if command != "ONNECT":
            xlog.warn("https req line fail:%s", line)
            return

        host, _, port = path.rpartition(':')
        host = host.encode()
        port = int(port)

        header_block = self.read_headers()

        sock = self.connection
        conn_id = proxy_session.create_conn(sock, host, port)
        if not conn_id:
            xlog.warn("create conn fail")
            sock.send(b'HTTP/1.1 500 Fail\r\n\r\n')
            return

        xlog.info("https %r connect to %s:%d conn_id:%d", self.client_address, host, port, conn_id)
        try:
            sock.send(b'HTTP/1.1 200 OK\r\n\r\n')
        except:
            xlog.warn("https %r connect to %s:%d conn_id:%d closed.", self.client_address, host, port, conn_id)

        if (len(self.read_buffer) - self.buffer_start) > 0:
            g.session.conn_list[conn_id].transfer_received_data(self.read_buffer[self.buffer_start:])

        g.session.conn_list[conn_id].start(block=True)

    def http_handler(self, first_char):
        req_line = self.read_crlf_line()
        words = req_line.split()
        if len(words) == 3:
            method, url, http_version = words
        elif len(words) == 2:
            method, url = words
            http_version = b"HTTP/1.1"
        else:
            xlog.warn("http req line fail:%s", req_line)
            return

        method = first_char + method
        # if method not in ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "TRACE", "PATCH"]:
        #    xlog.warn("https req method not known:%s", method)

        if url.startswith(b"http://") or url.startswith(b"HTTP://"):
            o = urllib.parse.urlparse(url)
            host, port = netloc_to_host_port(o.netloc)

            p = url[7:].find(b"/")
            if p >= 0:
                path = url[7+p:]
            else:
                path = b"/"
        else:
            header_block = self.read_headers()
            lines = header_block.split(b"\r\n")
            path = url
            host = None
            for line in lines:
                key, _, value = line.rpartition(b":")
                if key.lower == b"host":
                    host, port = netloc_to_host_port(value)
                    break
            if host is None:
                xlog.warn("http proxy host can't parsed. %s %s", req_line, header_block)
                self.connection.send(b'HTTP/1.1 500 Fail\r\n\r\n')
                return

        sock = self.connection
        conn_id = proxy_session.create_conn(sock, host, port)
        if not conn_id:
            xlog.warn("create conn fail")
            sock.send(b'HTTP/1.1 500 Fail\r\n\r\n')
            return

        xlog.info("http %r connect to %s:%d conn_id:%d", self.client_address, host, port, conn_id)

        new_req_line = b"%s %s %s" % (method, path, http_version)
        left_buf = new_req_line + self.read_buffer[(len(req_line) + 1):]
        g.session.conn_list[conn_id].transfer_received_data(left_buf)

        g.session.conn_list[conn_id].start(block=True)

