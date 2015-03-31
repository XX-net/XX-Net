# Copyright (c) 2009-2010 Denis Bilenko. See LICENSE for details.
"""
gevent is a coroutine-based Python networking library that uses greenlet
to provide a high-level synchronous API on top of libevent event loop.

See http://www.gevent.org/ for the documentation.
"""

version_info = (0, 13, 6)
__version__ = '0.13.6'
__changeset__ = '1734:6c834b912c36'

__all__ = ['Greenlet',
           'GreenletExit',
           'spawn',
           'spawn_later',
           'spawn_link',
           'spawn_link_value',
           'spawn_link_exception',
           'spawn_raw',
           'joinall',
           'killall',
           'Timeout',
           'with_timeout',
           'getcurrent',
           'sleep',
           'kill',
           'signal',
           'fork',
           'shutdown',
           'core',
           'reinit']


import sys
if sys.platform == 'win32':
    __import__('socket')  # trigger WSAStartup call
del sys


from gevent import core
core.EV_TIMEOUT = 0x01
core.EV_READ    = 0x02
core.EV_WRITE   = 0x04
core.EV_SIGNAL  = 0x08
core.EV_PERSIST = 0x10

from gevent.core import reinit
from gevent.greenlet import Greenlet, joinall, killall
spawn = Greenlet.spawn
spawn_later = Greenlet.spawn_later
spawn_link = Greenlet.spawn_link
spawn_link_value = Greenlet.spawn_link_value
spawn_link_exception = Greenlet.spawn_link_exception
from gevent.timeout import Timeout, with_timeout
from gevent.hub import getcurrent, GreenletExit, spawn_raw, sleep, kill, signal, shutdown
try:
    from gevent.hub import fork
except ImportError:
    __all__.remove('fork')
