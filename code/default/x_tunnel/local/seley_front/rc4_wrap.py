import socket
import time
import struct
import json
import os
import errno

import env_info
import xlog
data_path = env_info.data_path
module_data_path = os.path.join(data_path, 'x_tunnel')

logger = xlog.getLogger("seley_front", log_path=module_data_path, save_start_log=1500, save_warning_log=True)
logger.set_buffer(300)

try:
    from py_aes_cfb import lib as aes
    logger.debug("load py_aes_cfb success")
except Exception as e:
    aes = None

    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        logger.debug("load cryptography success")
    except:
        logger.warn("load cryptography failed:%r", e)
        algorithms = None


import utils


class SSLConnection(object):
    def __init__(self, sock, ip_str=None, sni=None, on_close=None):
        self._sock = sock
        self.ip_str = utils.to_bytes(ip_str)
        self.sni = utils.to_bytes(sni)
        self._makefile_refs = 0
        self._on_close = on_close
        self.peer_cert = None
        self.socket_closed = False
        self.timeout = self._sock.gettimeout() or 0.1
        self.running = True
        self.h2 = False

        if not aes and not algorithms:
            raise socket.error('no cryptography')

        key = self.sni
        iv = b'\x00' * 16
        if aes:
            self.encryptor = aes.encryptor_create(key, len(key), iv, len(iv))
            self.decryptor = aes.decryptor_create(key, len(key), iv, len(iv))
        else:
            algorithm = algorithms.AES(key)
            self.cipher = Cipher(algorithm, mode=modes.CFB(iv))
            self.decryptor = self.cipher.decryptor()
            self.encryptor = self.cipher.encryptor()
        self.wrap()

    def encode(self, input):
        if aes:
            out = bytes(input)
            aes.encryptor_update(self.encryptor, input, len(input), out)
            return out
        else:
            return self.encryptor.update(input)

    def decode(self, input):
        if aes:
            out = bytes(input)
            aes.decryptor_update(self.decryptor, input, len(input), out)
            return out
        else:
            return self.decryptor.update(input)

    def wrap(self):
        ip, port = utils.get_ip_port(self.ip_str)
        if isinstance(ip, str):
            ip = utils.to_bytes(ip)

        try:
            self._sock.connect((ip, port))
        except Exception as e:
            raise socket.error('conn %s fail, sni:%s, e:%r' % (self.ip_str, self.sni, e))

    def do_handshake(self):
        magic = b"SE"
        info = {
            "ts": time.time()
        }
        data = json.dumps(info)
        data_len = len(data)
        dat = magic + struct.pack("I", data_len) + utils.to_bytes(data)
        dat = self.encode(dat)
        sended = self._sock.send(dat)

        res = self._sock.recv(6)
        res = self.decode(res)
        if res[0:2] != b"SE":
            raise Exception("handshake failed")

        data_len = struct.unpack("I", res[2:])[0]
        res = self._sock.recv(data_len)
        res = self.decode(res)
        info = json.loads(res)

    def is_support_h2(self):
        return False

    def setblocking(self, block):
        self._sock.setblocking(block)

    def getsockname(self):
        self._sock.getsockname()

    def __getattr__(self, attr):
        if attr == "socket_closed":
            # work around in case close before finished init.
            return True

        # '_connection',
        elif attr in ('is_support_h2', "_on_close", '_context', '_sock', '_makefile_refs',
                      'sni', 'wrap', 'socket_closed', 'cipher', 'decryptor', 'encryptor'):
            return getattr(self, attr)

    def __del__(self):
        if not self.socket_closed:
            self.socket_closed = True
            if self._on_close:
                self._on_close(self.ip_str, self.sni)

        if aes:
            aes.encryptor_destroy(self.encryptor)
            aes.decryptor_destroy(self.decryptor)

    def get_cert(self):
        self.peer_cert = {
            "cert": "",
            "issuer_commonname": "",
            "commonName": "",
            "altName": ""
        }
        return self.peer_cert

    def connect(self, *args, **kwargs):
        return

    def send(self, data, flags=0):
        data = self.encode(data)
        while True:
            try:
                bytes_sent = self._sock.send(data)
                return bytes_sent
            except BlockingIOError as e:
                time.sleep(0.1)
                continue
            except socket.error as e:
                if e.errno == errno.EAGAIN:
                    # if str(e) == "[Errno 35] Resource temporarily unavailable":
                    time.sleep(0.1)
                else:
                    raise e

    def recv(self, bufsiz, flags=0):
        data = self._sock.recv(bufsiz)
        data = self.decode(data)
        return data

    def recv_into(self, buf, nbytes=None):
        if not nbytes:
            nbytes = len(buf)

        data = self._connection.read(nbytes)
        if not data:
            return None

        data = self.decode(data)
        buf[:len(data)] = data
        return len(data)

    def read(self, bufsiz, flags=0):
        return self.recv(bufsiz, flags)

    def write(self, buf, flags=0):
        return self.sendall(buf, flags)

    def close(self, reason=""):
        if self._makefile_refs < 1:
            self.running = False
            if not self.socket_closed:
                socket.socket.close(self._sock)
                self.socket_closed = True
                if self._on_close:
                    self._on_close(self.ip_str, self.sni, reason=reason)
        else:
            self._makefile_refs -= 1

    def settimeout(self, t):
        if not self.running:
            return

        if self.timeout != t:
            self._sock.settimeout(t)
            self.timeout = t

    def makefile(self, mode='r', bufsize=-1):
        self._makefile_refs += 1
        return socket._fileobject(self, mode, bufsize, close=True)

    def fileno(self):
        return self._sock.fileno()
