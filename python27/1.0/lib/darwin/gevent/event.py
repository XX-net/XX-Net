# Copyright (c) 2009-2011 Denis Bilenko. See LICENSE for details.
"""Basic synchronization primitives: Event and AsyncResult"""

import sys
from gevent.hub import get_hub, getcurrent, _NONE, PY3
from gevent.timeout import Timeout
from collections import deque
if PY3:
    xrange = range

__all__ = ['Event', 'AsyncResult']


class Event(object):
    """A synchronization primitive that allows one greenlet to wake up one or more others.
    It has the same interface as :class:`threading.Event` but works across greenlets.

    An event object manages an internal flag that can be set to true with the
    :meth:`set` method and reset to false with the :meth:`clear` method. The :meth:`wait` method
    blocks until the flag is true.
    """

    def __init__(self):
        self._links = set()
        self._todo = set()
        self._flag = False
        self.hub = get_hub()
        self._notifier = None

    def __str__(self):
        return '<%s %s _links[%s]>' % (self.__class__.__name__, (self._flag and 'set') or 'clear', len(self._links))

    def is_set(self):
        """Return true if and only if the internal flag is true."""
        return self._flag

    isSet = is_set  # makes it a better drop-in replacement for threading.Event
    ready = is_set  # makes it compatible with AsyncResult and Greenlet (for example in wait())

    def set(self):
        """Set the internal flag to true. All greenlets waiting for it to become true are awakened.
        Greenlets that call :meth:`wait` once the flag is true will not block at all.
        """
        self._flag = True
        self._todo.update(self._links)
        if self._todo and not self._notifier:
            self._notifier = self.hub.loop.run_callback(self._notify_links)

    def clear(self):
        """Reset the internal flag to false.
        Subsequently, threads calling :meth:`wait`
        will block until :meth:`set` is called to set the internal flag to true again.
        """
        self._flag = False

    def wait(self, timeout=None):
        """Block until the internal flag is true.
        If the internal flag is true on entry, return immediately. Otherwise,
        block until another thread calls :meth:`set` to set the flag to true,
        or until the optional timeout occurs.

        When the *timeout* argument is present and not ``None``, it should be a
        floating point number specifying a timeout for the operation in seconds
        (or fractions thereof).

        Return the value of the internal flag (``True`` or ``False``).
        """
        if self._flag:
            return self._flag
        else:
            switch = getcurrent().switch
            self.rawlink(switch)
            try:
                timer = Timeout.start_new(timeout)
                try:
                    try:
                        result = self.hub.switch()
                        assert result is self, 'Invalid switch into Event.wait(): %r' % (result, )
                    except Timeout:
                        ex = sys.exc_info()[1]
                        if ex is not timer:
                            raise
                finally:
                    timer.cancel()
            finally:
                self.unlink(switch)
        return self._flag

    def rawlink(self, callback):
        """Register a callback to call when the internal flag is set to true.

        *callback* will be called in the :class:`Hub <gevent.hub.Hub>`, so it must not use blocking gevent API.
        *callback* will be passed one argument: this instance.
        """
        if not callable(callback):
            raise TypeError('Expected callable: %r' % (callback, ))
        self._links.add(callback)
        if self._flag and not self._notifier:
            self._todo.add(callback)
            self._notifier = self.hub.loop.run_callback(self._notify_links)

    def unlink(self, callback):
        """Remove the callback set by :meth:`rawlink`"""
        try:
            self._links.remove(callback)
        except ValueError:
            pass

    def _notify_links(self):
        while self._todo:
            link = self._todo.pop()
            if link in self._links:  # check that link was not notified yet and was not removed by the client
                try:
                    link(self)
                except:
                    self.hub.handle_error((link, self), *sys.exc_info())


class AsyncResult(object):
    """A one-time event that stores a value or an exception.

    Like :class:`Event` it wakes up all the waiters when :meth:`set` or :meth:`set_exception` method
    is called. Waiters may receive the passed value or exception by calling :meth:`get`
    method instead of :meth:`wait`. An :class:`AsyncResult` instance cannot be reset.

    To pass a value call :meth:`set`. Calls to :meth:`get` (those that currently blocking as well as
    those made in the future) will return the value:

        >>> result = AsyncResult()
        >>> result.set(100)
        >>> result.get()
        100

    To pass an exception call :meth:`set_exception`. This will cause :meth:`get` to raise that exception:

        >>> result = AsyncResult()
        >>> result.set_exception(RuntimeError('failure'))
        >>> result.get()
        Traceback (most recent call last):
         ...
        RuntimeError: failure

    :class:`AsyncResult` implements :meth:`__call__` and thus can be used as :meth:`link` target:

        >>> result = AsyncResult()
        >>> gevent.spawn(lambda : 1/0).link(result)
        >>> result.get()
        Traceback (most recent call last):
         ...
        ZeroDivisionError: integer division or modulo by zero
    """
    def __init__(self):
        self._links = deque()
        self.value = None
        self._exception = _NONE
        self.hub = get_hub()
        self._notifier = None

    def __str__(self):
        result = '<%s ' % (self.__class__.__name__, )
        if self.value is not None or self._exception is not _NONE:
            result += 'value=%r ' % self.value
        if self._exception is not None and self._exception is not _NONE:
            result += 'exception=%r ' % self._exception
        if self._exception is _NONE:
            result += 'unset '
        return result + ' _links[%s]>' % len(self._links)

    def ready(self):
        """Return true if and only if it holds a value or an exception"""
        return self._exception is not _NONE

    def successful(self):
        """Return true if and only if it is ready and holds a value"""
        return self._exception is None

    @property
    def exception(self):
        """Holds the exception instance passed to :meth:`set_exception` if :meth:`set_exception` was called.
        Otherwise ``None``."""
        if self._exception is not _NONE:
            return self._exception

    def set(self, value=None):
        """Store the value. Wake up the waiters.

        All greenlets blocking on :meth:`get` or :meth:`wait` are woken up.
        Sequential calls to :meth:`wait` and :meth:`get` will not block at all.
        """
        self.value = value
        self._exception = None
        if self._links and not self._notifier:
            self._notifier = self.hub.loop.run_callback(self._notify_links)

    def set_exception(self, exception):
        """Store the exception. Wake up the waiters.

        All greenlets blocking on :meth:`get` or :meth:`wait` are woken up.
        Sequential calls to :meth:`wait` and :meth:`get` will not block at all.
        """
        self._exception = exception
        if self._links and not self._notifier:
            self._notifier = self.hub.loop.run_callback(self._notify_links)

    def get(self, block=True, timeout=None):
        """Return the stored value or raise the exception.

        If this instance already holds a value / an exception, return / raise it immediatelly.
        Otherwise, block until another greenlet calls :meth:`set` or :meth:`set_exception` or
        until the optional timeout occurs.

        When the *timeout* argument is present and not ``None``, it should be a
        floating point number specifying a timeout for the operation in seconds
        (or fractions thereof).
        """
        if self._exception is not _NONE:
            if self._exception is None:
                return self.value
            raise self._exception
        elif block:
            switch = getcurrent().switch
            self.rawlink(switch)
            try:
                timer = Timeout.start_new(timeout)
                try:
                    result = self.hub.switch()
                    assert result is self, 'Invalid switch into AsyncResult.get(): %r' % (result, )
                finally:
                    timer.cancel()
            except:
                self.unlink(switch)
                raise
            if self._exception is None:
                return self.value
            raise self._exception
        else:
            raise Timeout

    def get_nowait(self):
        """Return the value or raise the exception without blocking.

        If nothing is available, raise :class:`gevent.Timeout` immediatelly.
        """
        return self.get(block=False)

    def wait(self, timeout=None):
        """Block until the instance is ready.

        If this instance already holds a value / an exception, return immediatelly.
        Otherwise, block until another thread calls :meth:`set` or :meth:`set_exception` or
        until the optional timeout occurs.

        When the *timeout* argument is present and not ``None``, it should be a
        floating point number specifying a timeout for the operation in seconds
        (or fractions thereof).

        Return :attr:`value`.
        """
        if self._exception is not _NONE:
            return self.value
        else:
            switch = getcurrent().switch
            self.rawlink(switch)
            try:
                timer = Timeout.start_new(timeout)
                try:
                    result = self.hub.switch()
                    assert result is self, 'Invalid switch into AsyncResult.wait(): %r' % (result, )
                finally:
                    timer.cancel()
            except Timeout:
                exc = sys.exc_info()[1]
                self.unlink(switch)
                if exc is not timer:
                    raise
            except:
                self.unlink(switch)
                raise
            # not calling unlink() in non-exception case, because if switch()
            # finished normally, link was already removed in _notify_links
        return self.value

    def _notify_links(self):
        while self._links:
            link = self._links.popleft()
            try:
                link(self)
            except:
                self.hub.handle_error((link, self), *sys.exc_info())

    def rawlink(self, callback):
        """Register a callback to call when a value or an exception is set.

        *callback* will be called in the :class:`Hub <gevent.hub.Hub>`, so it must not use blocking gevent API.
        *callback* will be passed one argument: this instance.
        """
        if not callable(callback):
            raise TypeError('Expected callable: %r' % (callback, ))
        self._links.append(callback)
        if self.ready() and not self._notifier:
            self._notifier = self.hub.loop.run_callback(self._notify_links)

    def unlink(self, callback):
        """Remove the callback set by :meth:`rawlink`"""
        try:
            self._links.remove(callback)
        except ValueError:
            pass

    # link protocol
    def __call__(self, source):
        if source.successful():
            self.set(source.value)
        else:
            self.set_exception(source.exception)
