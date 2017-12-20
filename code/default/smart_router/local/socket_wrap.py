import time


class SocketWrap(object):

    def __init__(self, sock, ip=None, port=None, host="", target=""):
        self._sock = sock
        self.ip = ip
        self.port = port
        self.host = host
        self.target = target
        self.recved_data = 0
        self.recved_times = 0
        self.create_time = time.time()
        self.closed = False

    def __getattr__(self, attr):
        return getattr(self._sock, attr)

    def close(self):
        self._sock.close()
        self.closed = True

    def is_closed(self):
        return self.closed

    def __str__(self):
        return "%s[%s]:%d" % (self.host, self.ip, self.port)
