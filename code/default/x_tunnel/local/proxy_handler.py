import time
import socket, SocketServer, struct

import utils
from xlog import getLogger
xlog = getLogger("x_tunnel")

import global_var as g


class Socks5Server():
    read_buffer = ""
    buffer_start = 0

    def __init__(self, sock, client, args):
        self.connection = sock
        self.rfile = socket._fileobject(self.connection, "rb", -1)
        self.wfile = socket._fileobject(self.connection, "wb", 0)
        self.client_address = client
        self.args = args

    def handle(self):
        try:
            # xlog.debug('Connected from %r', self.client_address)

            socks_version = self.read_bytes(1)
            if socks_version == "\x04":
                self.socks4_handler()
            elif socks_version == "\x05":
                self.socks5_handler()
            elif socks_version == "C":
                self.https_handler()
            else:
                xlog.warn("socks version:%s not supported",  utils.str2hex(socks_version))
                return

        except socket.error as e:
            xlog.exception('socks handler read error %r', e)
        except Exception as e:
            xlog.exception("any err:%r", e)

    def read_line(self):
        sock = self.connection
        sock.setblocking(0)
        try:
            while True:
                n1 = self.read_buffer.find("\x00", self.buffer_start)
                if n1 == -1:
                    n1 = self.read_buffer.find("\r", self.buffer_start)
                if n1 > -1:
                    line = self.read_buffer[self.buffer_start:n1]
                    self.buffer_start = n1 + 1
                    return line
                time.sleep(0.001)
                data = sock.recv(256)
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
                data = sock.recv(need)
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
        if addr_pack[0:3] == '\x00\x00\x00' and addr_pack[3] != '\x00':
            domain_mode = True
        else:
            ip = socket.inet_ntoa(addr_pack)
            domain_mode = False

        user_id = self.read_line()
        if len(user_id):
            xlog.debug("Socks4 user_id:%s", user_id)

        if domain_mode:
            addr = self.read_line()
        else:
            addr = ip

        conn_id = g.session.create_conn(sock, addr, port)
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
            xlog.exception("socks5 protocol error:%r", e)
            return

        socks_version = ord(data[0])
        if socks_version != 5:
            xlog.warn("request version:%d error", socks_version)
            return

        command = ord(data[1])
        if command != 1:  # 1. Tcp connect
            xlog.warn("request not supported command mode:%d", command)
            sock.send(b"\x05\x07\x00\x01")  # Command not supported
            return

        addrtype_pack = data[3]
        addrtype = ord(addrtype_pack)
        if addrtype == 1:  # IPv4
            addr_pack = self.read_bytes(4)
            addr = socket.inet_ntoa(addr_pack)
        elif addrtype == 3:  # Domain name
            domain_len_pack = self.read_bytes(1)[0]
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

        conn_id = g.session.create_conn(sock, addr, port)
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
        line = self.read_line()
        line = line.decode('iso-8859-1')
        words = line.split()
        if len(words) == 3:
            command, path, version = words
        elif len(words) == 2:
            command, path = words
            version = "HTTP/1.1"
        else:
            xlog.warn("https req line fail:%s", line)
            return

        if command != "ONNECT":
            xlog.warn("https req line fail:%s", line)
            return

        host, _, port = path.rpartition(':')
        host = host.encode()
        port = int(port)

        sock = self.connection
        conn_id = g.session.create_conn(sock, host, port)
        if not conn_id:
            xlog.warn("create conn fail")
            sock.send(b'HTTP/1.1 500 Fail\r\n\r\n')
            return

        xlog.info("https %r connect to %s:%d conn_id:%d", self.client_address, host, port, conn_id)
        sock.send(b'HTTP/1.1 200 OK\r\n\r\n')

        g.session.conn_list[conn_id].start(block=True)
