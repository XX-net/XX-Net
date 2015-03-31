# Copyright (c) 2009-2010 Denis Bilenko. See LICENSE for details.
"""Synchronized queues.

The :mod:`gevent.queue` module implements multi-producer, multi-consumer queues
that work across greenlets, with the API similar to the classes found in the
standard :mod:`Queue` and :class:`multiprocessing <multiprocessing.Queue>` modules.

A major difference is that queues in this module operate as channels when
initialized with *maxsize* of zero. In such case, both :meth:`Queue.empty`
and :meth:`Queue.full` return ``True`` and :meth:`Queue.put` always blocks until a call
to :meth:`Queue.get` retrieves the item.

Another interesting difference is that :meth:`Queue.qsize`, :meth:`Queue.empty`, and
:meth:`Queue.full` *can* be used as indicators of whether the subsequent :meth:`Queue.get`
or :meth:`Queue.put` will not block.

Additionally, queues in this module implement iterator protocol. Iterating over queue
means repeatedly calling :meth:`get <Queue.get>` until :meth:`get <Queue.get>` returns ``StopIteration``.

    >>> queue = gevent.queue.Queue()
    >>> queue.put(1)
    >>> queue.put(2)
    >>> queue.put(StopIteration)
    >>> for item in queue:
    ...    print item
    1
    2
"""

import sys
import heapq
import collections
from Queue import Full, Empty

from gevent.timeout import Timeout
from gevent.hub import get_hub, Waiter, getcurrent, _NONE
from gevent import core


__all__ = ['Queue', 'PriorityQueue', 'LifoQueue', 'JoinableQueue']


class Queue(object):
    """Create a queue object with a given maximum size.

    If *maxsize* is less than zero or ``None``, the queue size is infinite.

    ``Queue(0)`` is a channel, that is, its :meth:`put` method always blocks until the
    item is delivered. (This is unlike the standard :class:`Queue`, where 0 means
    infinite size).
    """

    def __init__(self, maxsize=None):
        if maxsize < 0:
            self.maxsize = None
        else:
            self.maxsize = maxsize
        self.getters = set()
        self.putters = set()
        self._event_unlock = None
        self._init(maxsize)

    # QQQ make maxsize into a property with setter that schedules unlock if necessary

    def _init(self, maxsize):
        self.queue = collections.deque()

    def _get(self):
        return self.queue.popleft()

    def _put(self, item):
        self.queue.append(item)

    def __repr__(self):
        return '<%s at %s %s>' % (type(self).__name__, hex(id(self)), self._format())

    def __str__(self):
        return '<%s %s>' % (type(self).__name__, self._format())

    def _format(self):
        result = 'maxsize=%r' % (self.maxsize, )
        if getattr(self, 'queue', None):
            result += ' queue=%r' % self.queue
        if self.getters:
            result += ' getters[%s]' % len(self.getters)
        if self.putters:
            result += ' putters[%s]' % len(self.putters)
        if self._event_unlock is not None:
            result += ' unlocking'
        return result

    def qsize(self):
        """Return the size of the queue."""
        return len(self.queue)

    def empty(self):
        """Return ``True`` if the queue is empty, ``False`` otherwise."""
        return not self.qsize()

    def full(self):
        """Return ``True`` if the queue is full, ``False`` otherwise.

        ``Queue(None)`` is never full.
        """
        return self.qsize() >= self.maxsize

    def put(self, item, block=True, timeout=None):
        """Put an item into the queue.

        If optional arg *block* is true and *timeout* is ``None`` (the default),
        block if necessary until a free slot is available. If *timeout* is
        a positive number, it blocks at most *timeout* seconds and raises
        the :class:`Full` exception if no free slot was available within that time.
        Otherwise (*block* is false), put an item on the queue if a free slot
        is immediately available, else raise the :class:`Full` exception (*timeout*
        is ignored in that case).
        """
        if self.maxsize is None or self.qsize() < self.maxsize:
            # there's a free slot, put an item right away
            self._put(item)
            if self.getters:
                self._schedule_unlock()
        elif not block and get_hub() is getcurrent():
            # we're in the mainloop, so we cannot wait; we can switch() to other greenlets though
            # find a getter and deliver an item to it
            while self.getters:
                getter = self.getters.pop()
                if getter:
                    self._put(item)
                    item = self._get()
                    getter.switch(item)
                    return
            raise Full
        elif block:
            waiter = ItemWaiter(item)
            self.putters.add(waiter)
            timeout = Timeout.start_new(timeout, Full)
            try:
                if self.getters:
                    self._schedule_unlock()
                result = waiter.get()
                assert result is waiter, "Invalid switch into Queue.put: %r" % (result, )
                if waiter.item is not _NONE:
                    self._put(item)
            finally:
                timeout.cancel()
                self.putters.discard(waiter)
        else:
            raise Full

    def put_nowait(self, item):
        """Put an item into the queue without blocking.

        Only enqueue the item if a free slot is immediately available.
        Otherwise raise the :class:`Full` exception.
        """
        self.put(item, False)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args *block* is true and *timeout* is ``None`` (the default),
        block if necessary until an item is available. If *timeout* is a positive number,
        it blocks at most *timeout* seconds and raises the :class:`Empty` exception
        if no item was available within that time. Otherwise (*block* is false), return
        an item if one is immediately available, else raise the :class:`Empty` exception
        (*timeout* is ignored in that case).
        """
        if self.qsize():
            if self.putters:
                self._schedule_unlock()
            return self._get()
        elif not block and get_hub() is getcurrent():
            # special case to make get_nowait() runnable in the mainloop greenlet
            # there are no items in the queue; try to fix the situation by unlocking putters
            while self.putters:
                putter = self.putters.pop()
                if putter:
                    putter.switch(putter)
                    if self.qsize():
                        return self._get()
            raise Empty
        elif block:
            waiter = Waiter()
            timeout = Timeout.start_new(timeout, Empty)
            try:
                self.getters.add(waiter)
                if self.putters:
                    self._schedule_unlock()
                return waiter.get()
            finally:
                self.getters.discard(waiter)
                timeout.cancel()
        else:
            raise Empty

    def get_nowait(self):
        """Remove and return an item from the queue without blocking.

        Only get an item if one is immediately available. Otherwise
        raise the :class:`Empty` exception.
        """
        return self.get(False)

    def _unlock(self):
        try:
            while True:
                if self.qsize() and self.getters:
                    getter = self.getters.pop()
                    if getter:
                        try:
                            item = self._get()
                        except:
                            getter.throw(*sys.exc_info())
                        else:
                            getter.switch(item)
                elif self.putters and self.getters:
                    putter = self.putters.pop()
                    if putter:
                        getter = self.getters.pop()
                        if getter:
                            item = putter.item
                            putter.item = _NONE  # this makes greenlet calling put() not to call _put() again
                            self._put(item)
                            item = self._get()
                            getter.switch(item)
                            putter.switch(putter)
                        else:
                            self.putters.add(putter)
                elif self.putters and (self.getters or self.qsize() < self.maxsize):
                    putter = self.putters.pop()
                    putter.switch(putter)
                else:
                    break
        finally:
            self._event_unlock = None  # QQQ maybe it's possible to obtain this info from libevent?
            # i.e. whether this event is pending _OR_ currently executing
        # testcase: 2 greenlets: while True: q.put(q.get()) - nothing else has a change to execute
        # to avoid this, schedule unlock with timer(0, ...) once in a while

    def _schedule_unlock(self):
        if self._event_unlock is None:
            self._event_unlock = core.active_event(self._unlock)
            # QQQ re-activate event (with event_active libevent call) instead of creating a new one each time

    def __iter__(self):
        return self

    def next(self):
        result = self.get()
        if result is StopIteration:
            raise result
        return result


class ItemWaiter(Waiter):
    __slots__ = ['item']

    def __init__(self, item):
        Waiter.__init__(self)
        self.item = item


class PriorityQueue(Queue):
    '''A subclass of :class:`Queue` that retrieves entries in priority order (lowest first).

    Entries are typically tuples of the form: ``(priority number, data)``.
    '''

    def _init(self, maxsize):
        self.queue = []

    def _put(self, item, heappush=heapq.heappush):
        heappush(self.queue, item)

    def _get(self, heappop=heapq.heappop):
        return heappop(self.queue)


class LifoQueue(Queue):
    '''A subclass of :class:`Queue` that retrieves most recently added entries first.'''

    def _init(self, maxsize):
        self.queue = []

    def _put(self, item):
        self.queue.append(item)

    def _get(self):
        return self.queue.pop()


class JoinableQueue(Queue):
    '''A subclass of :class:`Queue` that additionally has :meth:`task_done` and :meth:`join` methods.'''

    def __init__(self, maxsize=None):
        from gevent.event import Event
        Queue.__init__(self, maxsize)
        self.unfinished_tasks = 0
        self._cond = Event()
        self._cond.set()

    def _format(self):
        result = Queue._format(self)
        if self.unfinished_tasks:
            result += ' tasks=%s _cond=%s' % (self.unfinished_tasks, self._cond)
        return result

    def _put(self, item):
        Queue._put(self, item)
        self.unfinished_tasks += 1
        self._cond.clear()

    def task_done(self):
        '''Indicate that a formerly enqueued task is complete. Used by queue consumer threads.
        For each :meth:`get <Queue.get>` used to fetch a task, a subsequent call to :meth:`task_done` tells the queue
        that the processing on the task is complete.

        If a :meth:`join` is currently blocking, it will resume when all items have been processed
        (meaning that a :meth:`task_done` call was received for every item that had been
        :meth:`put <Queue.put>` into the queue).

        Raises a :exc:`ValueError` if called more times than there were items placed in the queue.
        '''
        if self.unfinished_tasks <= 0:
            raise ValueError('task_done() called too many times')
        self.unfinished_tasks -= 1
        if self.unfinished_tasks == 0:
            self._cond.set()

    def join(self):
        '''Block until all items in the queue have been gotten and processed.

        The count of unfinished tasks goes up whenever an item is added to the queue.
        The count goes down whenever a consumer thread calls :meth:`task_done` to indicate
        that the item was retrieved and all work on it is complete. When the count of
        unfinished tasks drops to zero, :meth:`join` unblocks.
        '''
        self._cond.wait()
