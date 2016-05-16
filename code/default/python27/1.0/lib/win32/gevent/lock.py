# Copyright (c) 2009-2012 Denis Bilenko. See LICENSE for details.
"""Locking primitives"""

from gevent.hub import getcurrent
from gevent._semaphore import Semaphore


__all__ = ['Semaphore', 'DummySemaphore', 'BoundedSemaphore', 'RLock']


class DummySemaphore(object):
    # XXX what is this used for?
    """A Semaphore initialized with "infinite" initial value. None of its methods ever block."""

    def __str__(self):
        return '<%s>' % self.__class__.__name__

    def locked(self):
        return False

    def release(self):
        pass

    def rawlink(self, callback):
        # XXX should still work and notify?
        pass

    def unlink(self, callback):
        pass

    def wait(self, timeout=None):
        pass

    def acquire(self, blocking=True, timeout=None):
        pass

    def __enter__(self):
        pass

    def __exit__(self, typ, val, tb):
        pass


class BoundedSemaphore(Semaphore):
    """A bounded semaphore checks to make sure its current value doesn't exceed its initial value.
    If it does, ``ValueError`` is raised. In most situations semaphores are used to guard resources
    with limited capacity. If the semaphore is released too many times it's a sign of a bug.

    If not given, *value* defaults to 1."""

    def __init__(self, value=1):
        Semaphore.__init__(self, value)
        self._initial_value = value

    def release(self):
        if self.counter >= self._initial_value:
            raise ValueError("Semaphore released too many times")
        return Semaphore.release(self)


class RLock(object):

    def __init__(self):
        self._block = Semaphore(1)
        self._owner = None
        self._count = 0

    def __repr__(self):
        return "<%s at 0x%x _block=%s _count=%r _owner=%r)>" % (
            self.__class__.__name__,
            id(self),
            self._block,
            self._count,
            self._owner)

    def acquire(self, blocking=1):
        me = getcurrent()
        if self._owner is me:
            self._count = self._count + 1
            return 1
        rc = self._block.acquire(blocking)
        if rc:
            self._owner = me
            self._count = 1
        return rc

    def __enter__(self):
        return self.acquire()

    def release(self):
        if self._owner is not getcurrent():
            raise RuntimeError("cannot release un-aquired lock")
        self._count = count = self._count - 1
        if not count:
            self._owner = None
            self._block.release()

    def __exit__(self, typ, value, tb):
        self.release()

    # Internal methods used by condition variables

    def _acquire_restore(self, count_owner):
        count, owner = count_owner
        self._block.acquire()
        self._count = count
        self._owner = owner

    def _release_save(self):
        count = self._count
        self._count = 0
        owner = self._owner
        self._owner = None
        self._block.release()
        return (count, owner)

    def _is_owned(self):
        return self._owner is getcurrent()
