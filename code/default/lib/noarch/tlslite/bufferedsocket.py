# Copyright (c) 2016, Hubert Kario
#
# See the LICENSE file for legal information regarding use of this file.

"""Wrapper around the socket.socket interface that provides buffering"""

from collections import deque


class BufferedSocket(object):
    """
    Socket that will buffer reads and writes to a real socket object

    When buffer_writes is enabled, writes won't be passed to the real socket
    until flush() is called.

    Not multithread safe.

    :vartype buffer_writes: boolean
    :ivar buffer_writes: whether to buffer data writes, False by default
    """

    def __init__(self, socket):
        """Associate socket with the object"""
        self.socket = socket
        self._write_queue = deque()
        self.buffer_writes = False
        self._read_buffer = bytearray()

    def send(self, data):
        """Send data to the socket"""
        if self.buffer_writes:
            self._write_queue.append(data)
            return len(data)
        return self.socket.send(data)

    def sendall(self, data):
        """Send data to the socket"""
        if self.buffer_writes:
            self._write_queue.append(data)
            return None
        return self.socket.sendall(data)

    def flush(self):
        """Send all buffered data"""
        buf = bytearray()
        for i in self._write_queue:
            buf += i
        self._write_queue.clear()
        if buf:
            self.socket.sendall(buf)

    def recv(self, bufsize):
        """Receive data from socket (socket emulation)"""
        if not self._read_buffer:
            self._read_buffer += self.socket.recv(max(4096, bufsize))
        ret = self._read_buffer[:bufsize]
        del self._read_buffer[:bufsize]
        return ret

    def getsockname(self):
        """Return the socket's own address (socket emulation)."""
        return self.socket.getsockname()

    def getpeername(self):
        """
        Return the remote address to which the socket is connected

        (socket emulation)
        """
        return self.socket.getpeername()

    def settimeout(self, value):
        """Set a timeout on blocking socket operations (socket emulation)."""
        return self.socket.settimeout(value)

    def gettimeout(self):
        """
        Return the timeout associated with socket operations

        (socket emulation)
        """
        return self.socket.gettimeout()

    def setsockopt(self, level, optname, value):
        """Set the value of the given socket option (socket emulation)."""
        return self.socket.setsockopt(level, optname, value)

    def shutdown(self, how):
        """Shutdown the underlying socket."""
        self.flush()
        return self.socket.shutdown(how)

    def close(self):
        """Close the underlying socket."""
        self.flush()
        return self.socket.close()
