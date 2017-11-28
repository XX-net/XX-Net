
import threading
import struct
from socket import *

from xlog import getLogger
xlog = getLogger("smart_router")


SO_ORIGINAL_DST = 80


class RedirectHandler(object):
    def __init__(self, bind_ip="127.0.0.1", port=8083, handler=None):
        self.bind_ip = bind_ip
        self.port = port
        self.handler = handler
        self.running =None

        s = socket(AF_INET, SOCK_STREAM)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        s.bind((bind_ip, port))
        s.listen(1)
        self.sock = s

    def serve_forever(self):
        while self.running and self.handler:
            conn, addr = self.sock.accept()

            dst = conn.getsockopt(SOL_IP, SO_ORIGINAL_DST, 16)
            dst_port, srv_ip = struct.unpack("!2xH4s8x", dst)
            ip_str = inet_ntoa(srv_ip)
            xlog.debug("original to:%s:%d from:%s", ip_str, dst_port, addr)

            self.handler(conn, ip_str, dst_port, addr)

    def start(self):
        if not self.handler:
            return False

        self.running = True
        self.th = threading.Thread(target=self.serve_forever)
        self.th.start()
        return True

    def stop(self):
        self.running = False