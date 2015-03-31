"""
This module provides cooperative versions of os.read() and os.write().
On Posix platforms this uses non-blocking IO, on Windows a threadpool
is used.
"""

from __future__ import absolute_import

import os
import sys
from gevent.hub import get_hub, reinit
from gevent.socket import EAGAIN
import errno

try:
    import fcntl
except ImportError:
    fcntl = None

__implements__ = ['fork']
__extensions__ = ['tp_read', 'tp_write']

_read = os.read
_write = os.write


ignored_errors = [EAGAIN, errno.EINTR]


if fcntl:

    __extensions__ += ['make_nonblocking', 'nb_read', 'nb_write']

    def make_nonblocking(fd):
        flags = fcntl.fcntl(fd, fcntl.F_GETFL, 0)
        if not bool(flags & os.O_NONBLOCK):
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            return True

    def nb_read(fd, n):
        """Read up to `n` bytes from file descriptor `fd`. Return a string
        containing the bytes read. If end-of-file is reached, an empty string
        is returned.

        The descriptor must be in non-blocking mode.
        """
        hub, event = None, None
        while True:
            try:
                return _read(fd, n)
            except OSError, e:
                if e.errno not in ignored_errors:
                    raise
                sys.exc_clear()
            if hub is None:
                hub = get_hub()
                event = hub.loop.io(fd, 1)
            hub.wait(event)

    def nb_write(fd, buf):
        """Write bytes from buffer `buf` to file descriptor `fd`. Return the
        number of bytes written.

        The file descriptor must be in non-blocking mode.
        """
        hub, event = None, None
        while True:
            try:
                return _write(fd, buf)
            except OSError, e:
                if e.errno not in ignored_errors:
                    raise
                sys.exc_clear()
            if hub is None:
                hub = get_hub()
                event = hub.loop.io(fd, 2)
            hub.wait(event)


def tp_read(fd, n):
    """Read up to `n` bytes from file descriptor `fd`. Return a string
    containing the bytes read. If end-of-file is reached, an empty string
    is returned."""
    return get_hub().threadpool.apply_e(BaseException, _read, (fd, n))


def tp_write(fd, buf):
    """Write bytes from buffer `buf` to file descriptor `fd`. Return the
    number of bytes written."""
    return get_hub().threadpool.apply_e(BaseException, _write, (fd, buf))


if hasattr(os, 'fork'):
    _fork = os.fork

    def fork():
        result = _fork()
        if not result:
            reinit()
        return result

else:
    __implements__.remove('fork')


__all__ = __implements__ + __extensions__
