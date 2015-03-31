# Copyright (c) 2009-2012 Denis Bilenko. See LICENSE for details.
"""
gevent is a coroutine-based Python networking library that uses greenlet
to provide a high-level synchronous API on top of libev event loop.

See http://www.gevent.org/ for the documentation.
"""

from __future__ import absolute_import

version_info = (1, 0, 1, 'final', 0)
__version__ = '1.0.1'
__changeset__ = '1.0.1-0-g747630a'


__all__ = ['get_hub',
           'Greenlet',
           'GreenletExit',
           'spawn',
           'spawn_later',
           'spawn_raw',
           'iwait',
           'wait',
           'killall',
           'Timeout',
           'with_timeout',
           'getcurrent',
           'sleep',
           'idle',
           'kill',
           'signal',
           'fork',
           'reinit']


from gevent.hub import get_hub, iwait, wait
from gevent.greenlet import Greenlet, joinall, killall
spawn = Greenlet.spawn
spawn_later = Greenlet.spawn_later
from gevent.timeout import Timeout, with_timeout
from gevent.hub import getcurrent, GreenletExit, spawn_raw, sleep, idle, kill, signal, reinit
try:
    from gevent.os import fork
except ImportError:
    __all__.remove('fork')


# the following makes hidden imports visible to freezing tools like
# py2exe. see https://github.com/surfly/gevent/issues/181
def __dependencies_for_freezing():
    from gevent import core, resolver_thread, resolver_ares, socket,\
        threadpool, thread, threading, select, subprocess
    import pprint
    import traceback
    import signal

del __dependencies_for_freezing
