# Copyright (c) 2009-2011 Denis Bilenko. See LICENSE for details.
"""Managing greenlets in a group.

The :class:`Group` class in this module abstracts a group of running greenlets.
When a greenlet dies, it's automatically removed from the group.

The :class:`Pool` which a subclass of :class:`Group` provides a way to limit
concurrency: its :meth:`spawn <Pool.spawn>` method blocks if the number of
greenlets in the pool has already reached the limit, until there is a free slot.
"""

import sys
from bisect import insort_right

from gevent.hub import GreenletExit, getcurrent, kill as _kill, PY3
from gevent.greenlet import joinall, Greenlet
from gevent.timeout import Timeout
from gevent.event import Event
from gevent.lock import Semaphore, DummySemaphore

__all__ = ['Group', 'Pool']


class Group(object):
    """Maintain a group of greenlets that are still running.

    Links to each item and removes it upon notification.
    """
    greenlet_class = Greenlet

    def __init__(self, *args):
        assert len(args) <= 1, args
        self.greenlets = set(*args)
        if args:
            for greenlet in args[0]:
                greenlet.rawlink(self._discard)
        # each item we kill we place in dying, to avoid killing the same greenlet twice
        self.dying = set()
        self._empty_event = Event()
        self._empty_event.set()

    def __repr__(self):
        return '<%s at 0x%x %s>' % (self.__class__.__name__, id(self), self.greenlets)

    def __len__(self):
        return len(self.greenlets)

    def __contains__(self, item):
        return item in self.greenlets

    def __iter__(self):
        return iter(self.greenlets)

    def add(self, greenlet):
        try:
            rawlink = greenlet.rawlink
        except AttributeError:
            pass  # non-Greenlet greenlet, like MAIN
        else:
            rawlink(self._discard)
        self.greenlets.add(greenlet)
        self._empty_event.clear()

    def _discard(self, greenlet):
        self.greenlets.discard(greenlet)
        self.dying.discard(greenlet)
        if not self.greenlets:
            self._empty_event.set()

    def discard(self, greenlet):
        self._discard(greenlet)
        try:
            unlink = greenlet.unlink
        except AttributeError:
            pass  # non-Greenlet greenlet, like MAIN
        else:
            unlink(self._discard)

    def start(self, greenlet):
        self.add(greenlet)
        greenlet.start()

    def spawn(self, *args, **kwargs):
        greenlet = self.greenlet_class(*args, **kwargs)
        self.start(greenlet)
        return greenlet

#     def close(self):
#         """Prevents any more tasks from being submitted to the pool"""
#         self.add = RaiseException("This %s has been closed" % self.__class__.__name__)

    def join(self, timeout=None, raise_error=False):
        if raise_error:
            greenlets = self.greenlets.copy()
            self._empty_event.wait(timeout=timeout)
            for greenlet in greenlets:
                if greenlet.exception is not None:
                    raise greenlet.exception
        else:
            self._empty_event.wait(timeout=timeout)

    def kill(self, exception=GreenletExit, block=True, timeout=None):
        timer = Timeout.start_new(timeout)
        try:
            try:
                while self.greenlets:
                    for greenlet in list(self.greenlets):
                        if greenlet not in self.dying:
                            try:
                                kill = greenlet.kill
                            except AttributeError:
                                _kill(greenlet, exception)
                            else:
                                kill(exception, block=False)
                            self.dying.add(greenlet)
                    if not block:
                        break
                    joinall(self.greenlets)
            except Timeout:
                ex = sys.exc_info()[1]
                if ex is not timer:
                    raise
        finally:
            timer.cancel()

    def killone(self, greenlet, exception=GreenletExit, block=True, timeout=None):
        if greenlet not in self.dying and greenlet in self.greenlets:
            greenlet.kill(exception, block=False)
            self.dying.add(greenlet)
            if block:
                greenlet.join(timeout)

    def apply(self, func, args=None, kwds=None):
        """Equivalent of the apply() builtin function. It blocks till the result is ready."""
        if args is None:
            args = ()
        if kwds is None:
            kwds = {}
        if getcurrent() in self:
            return func(*args, **kwds)
        else:
            return self.spawn(func, *args, **kwds).get()

    def apply_cb(self, func, args=None, kwds=None, callback=None):
        result = self.apply(func, args, kwds)
        if callback is not None:
            Greenlet.spawn(callback, result)
        return result

    def apply_async(self, func, args=None, kwds=None, callback=None):
        """A variant of the apply() method which returns a Greenlet object.

        If callback is specified then it should be a callable which accepts a single argument. When the result becomes ready
        callback is applied to it (unless the call failed)."""
        if args is None:
            args = ()
        if kwds is None:
            kwds = {}
        if self.full():
            # cannot call spawn() directly because it will block
            return Greenlet.spawn(self.apply_cb, func, args, kwds, callback)
        else:
            greenlet = self.spawn(func, *args, **kwds)
            if callback is not None:
                greenlet.link(pass_value(callback))
            return greenlet

    def map(self, func, iterable):
        return list(self.imap(func, iterable))

    def map_cb(self, func, iterable, callback=None):
        result = self.map(func, iterable)
        if callback is not None:
            callback(result)
        return result

    def map_async(self, func, iterable, callback=None):
        """
        A variant of the map() method which returns a Greenlet object.

        If callback is specified then it should be a callable which accepts a
        single argument.
        """
        return Greenlet.spawn(self.map_cb, func, iterable, callback)

    def imap(self, func, iterable):
        """An equivalent of itertools.imap()"""
        return IMap.spawn(func, iterable, spawn=self.spawn)

    def imap_unordered(self, func, iterable):
        """The same as imap() except that the ordering of the results from the
        returned iterator should be considered in arbitrary order."""
        return IMapUnordered.spawn(func, iterable, spawn=self.spawn)

    def full(self):
        return False

    def wait_available(self):
        pass


class IMapUnordered(Greenlet):

    def __init__(self, func, iterable, spawn=None):
        from gevent.queue import Queue
        Greenlet.__init__(self)
        if spawn is not None:
            self.spawn = spawn
        self.func = func
        self.iterable = iterable
        self.queue = Queue()
        self.count = 0
        self.finished = False
        self.rawlink(self._on_finish)

    def __iter__(self):
        return self

    def next(self):
        value = self.queue.get()
        if isinstance(value, Failure):
            raise value.exc
        return value

    if PY3:
        __next__ = next
        del next

    def _run(self):
        try:
            func = self.func
            for item in self.iterable:
                self.count += 1
                self.spawn(func, item).rawlink(self._on_result)
        finally:
            self.__dict__.pop('spawn', None)
            self.__dict__.pop('func', None)
            self.__dict__.pop('iterable', None)

    def _on_result(self, greenlet):
        self.count -= 1
        if greenlet.successful():
            self.queue.put(greenlet.value)
        else:
            self.queue.put(Failure(greenlet.exception))
        if self.ready() and self.count <= 0 and not self.finished:
            self.queue.put(Failure(StopIteration))
            self.finished = True

    def _on_finish(self, _self):
        if self.finished:
            return
        if not self.successful():
            self.queue.put(Failure(self.exception))
            self.finished = True
            return
        if self.count <= 0:
            self.queue.put(Failure(StopIteration))
            self.finished = True


class IMap(Greenlet):

    def __init__(self, func, iterable, spawn=None):
        from gevent.queue import Queue
        Greenlet.__init__(self)
        if spawn is not None:
            self.spawn = spawn
        self.func = func
        self.iterable = iterable
        self.queue = Queue()
        self.count = 0
        self.waiting = []  # QQQ maybe deque will work faster there?
        self.index = 0
        self.maxindex = -1
        self.finished = False
        self.rawlink(self._on_finish)

    def __iter__(self):
        return self

    def next(self):
        while True:
            if self.waiting and self.waiting[0][0] <= self.index:
                index, value = self.waiting.pop(0)
            else:
                index, value = self.queue.get()
                if index > self.index:
                    insort_right(self.waiting, (index, value))
                    continue
            self.index += 1
            if isinstance(value, Failure):
                raise value.exc
            return value

    if PY3:
        __next__ = next
        del next

    def _run(self):
        try:
            func = self.func
            for item in self.iterable:
                self.count += 1
                g = self.spawn(func, item)
                g.rawlink(self._on_result)
                self.maxindex += 1
                g.index = self.maxindex
        finally:
            self.__dict__.pop('spawn', None)
            self.__dict__.pop('func', None)
            self.__dict__.pop('iterable', None)

    def _on_result(self, greenlet):
        self.count -= 1
        if greenlet.successful():
            self.queue.put((greenlet.index, greenlet.value))
        else:
            self.queue.put((greenlet.index, Failure(greenlet.exception)))
        if self.ready() and self.count <= 0 and not self.finished:
            self.maxindex += 1
            self.queue.put((self.maxindex, Failure(StopIteration)))
            self.finished = True

    def _on_finish(self, _self):
        if self.finished:
            return
        if not self.successful():
            self.maxindex += 1
            self.queue.put((self.maxindex, Failure(self.exception)))
            self.finished = True
            return
        if self.count <= 0:
            self.maxindex += 1
            self.queue.put((self.maxindex, Failure(StopIteration)))
            self.finished = True


class Failure(object):
    __slots__ = ['exc']

    def __init__(self, exc):
        self.exc = exc


class Pool(Group):

    def __init__(self, size=None, greenlet_class=None):
        if size is not None and size < 0:
            raise ValueError('size must not be negative: %r' % (size, ))
        Group.__init__(self)
        self.size = size
        if greenlet_class is not None:
            self.greenlet_class = greenlet_class
        if size is None:
            self._semaphore = DummySemaphore()
        else:
            self._semaphore = Semaphore(size)

    def wait_available(self):
        self._semaphore.wait()

    def full(self):
        return self.free_count() <= 0

    def free_count(self):
        if self.size is None:
            return 1
        return max(0, self.size - len(self))

    def add(self, greenlet):
        self._semaphore.acquire()
        try:
            Group.add(self, greenlet)
        except:
            self._semaphore.release()
            raise

    def _discard(self, greenlet):
        Group._discard(self, greenlet)
        self._semaphore.release()


class pass_value(object):
    __slots__ = ['callback']

    def __init__(self, callback):
        self.callback = callback

    def __call__(self, source):
        if source.successful():
            self.callback(source.value)

    def __hash__(self):
        return hash(self.callback)

    def __eq__(self, other):
        return self.callback == getattr(other, 'callback', other)

    def __str__(self):
        return str(self.callback)

    def __repr__(self):
        return repr(self.callback)

    def __getattr__(self, item):
        assert item != 'callback'
        return getattr(self.callback, item)
