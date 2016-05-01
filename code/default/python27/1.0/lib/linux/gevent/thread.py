"""Implementation of the standard :mod:`thread` module that spawns greenlets.

.. note::

    This module is a helper for :mod:`gevent.monkey` and is not intended to be
    used directly. For spawning greenlets in your applications, prefer
    :class:`Greenlet` class.
"""

__implements__ = ['allocate_lock',
                  'get_ident',
                  'exit',
                  'LockType',
                  'stack_size',
                  'start_new_thread']

__imports__ = ['error']

__thread__ = __import__('thread')
error = __thread__.error
from gevent.hub import getcurrent, GreenletExit
from gevent.greenlet import Greenlet
from gevent.coros import Semaphore as LockType


def get_ident(gr=None):
    if gr is None:
        return id(getcurrent())
    else:
        return id(gr)


def start_new_thread(function, args=(), kwargs={}):
    greenlet = Greenlet.spawn(function, *args, **kwargs)
    return get_ident(greenlet)


def allocate_lock():
    return LockType(1)


def exit():
    raise GreenletExit


if hasattr(__thread__, 'stack_size'):
    _original_stack_size = __thread__.stack_size

    def stack_size(size=None):
        if size is None:
            return _original_stack_size()
        if size > _original_stack_size():
            return _original_stack_size(size)
        else:
            pass
            # not going to decrease stack_size, because otherwise other greenlets in this thread will suffer
else:
    __implements__.remove('stack_size')


__all__ = __implements__ + __imports__

# XXX interrupt_main, _local
