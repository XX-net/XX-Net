# Copyright (c) 2009-2010 Denis Bilenko. See LICENSE for details.
"""Timeouts.

Many functions in :mod:`gevent` have a *timeout* argument that allows
to limit function's execution time. When that is not enough, the :class:`Timeout`
class and :func:`with_timeout` function in this module add timeouts
to arbitrary code.

.. warning::

    Timeouts can only work when the greenlet switches to the hub.
    If a blocking function is called or an intense calculation is ongoing during
    which no switches occur, :class:`Timeout` is powerless.
"""

import sys
from gevent.hub import getcurrent, _NONE, get_hub, string_types

__all__ = ['Timeout',
           'with_timeout']


try:
    BaseException
except NameError:  # Python < 2.5

    class BaseException:
        # not subclassing from object() intentionally, because in
        # that case "raise Timeout" fails with TypeError.
        pass


class Timeout(BaseException):
    """Raise *exception* in the current greenlet after given time period::

        timeout = Timeout(seconds, exception)
        timeout.start()
        try:
            ...  # exception will be raised here, after *seconds* passed since start() call
        finally:
            timeout.cancel()

    When *exception* is omitted or ``None``, the :class:`Timeout` instance itself is raised:

        >>> Timeout(0.1).start()
        >>> gevent.sleep(0.2)
        Traceback (most recent call last):
         ...
        Timeout: 0.1 seconds

    For Python 2.5 and newer ``with`` statement can be used::

        with Timeout(seconds, exception) as timeout:
            pass  # ... code block ...

    This is equivalent to try/finally block above with one additional feature:
    if *exception* is ``False``, the timeout is still raised, but context manager
    suppresses it, so the code outside the with-block won't see it.

    This is handy for adding a timeout to the functions that don't support *timeout* parameter themselves::

        data = None
        with Timeout(5, False):
            data = mysock.makefile().readline()
        if data is None:
            ...  # 5 seconds passed without reading a line
        else:
            ...  # a line was read within 5 seconds

    Note that, if ``readline()`` above catches and doesn't re-raise :class:`BaseException`
    (for example, with ``except:``), then your timeout is screwed.

    When catching timeouts, keep in mind that the one you catch maybe not the
    one you have set; if you going to silent a timeout, always check that it's
    the one you need::

        timeout = Timeout(1)
        timeout.start()
        try:
            ...
        except Timeout, t:
            if t is not timeout:
                raise # not my timeout
    """

    def __init__(self, seconds=None, exception=None, ref=True, priority=-1):
        self.seconds = seconds
        self.exception = exception
        self.timer = get_hub().loop.timer(seconds or 0.0, ref=ref, priority=priority)

    def start(self):
        """Schedule the timeout."""
        assert not self.pending, '%r is already started; to restart it, cancel it first' % self
        if self.seconds is None:  # "fake" timeout (never expires)
            pass
        elif self.exception is None or self.exception is False or isinstance(self.exception, string_types):
            # timeout that raises self
            self.timer.start(getcurrent().throw, self)
        else:  # regular timeout with user-provided exception
            self.timer.start(getcurrent().throw, self.exception)

    @classmethod
    def start_new(cls, timeout=None, exception=None, ref=True):
        """Create a started :class:`Timeout`.

        This is a shortcut, the exact action depends on *timeout*'s type:

        * If *timeout* is a :class:`Timeout`, then call its :meth:`start` method.
        * Otherwise, create a new :class:`Timeout` instance, passing (*timeout*, *exception*) as
          arguments, then call its :meth:`start` method.

        Returns the :class:`Timeout` instance.
        """
        if isinstance(timeout, Timeout):
            if not timeout.pending:
                timeout.start()
            return timeout
        timeout = cls(timeout, exception, ref=ref)
        timeout.start()
        return timeout

    @property
    def pending(self):
        """Return True if the timeout is scheduled to be raised."""
        return self.timer.pending or self.timer.active

    def cancel(self):
        """If the timeout is pending, cancel it. Otherwise, do nothing."""
        self.timer.stop()

    def __repr__(self):
        try:
            classname = self.__class__.__name__
        except AttributeError:  # Python < 2.5
            classname = 'Timeout'
        if self.pending:
            pending = ' pending'
        else:
            pending = ''
        if self.exception is None:
            exception = ''
        else:
            exception = ' exception=%r' % self.exception
        return '<%s at %s seconds=%s%s%s>' % (classname, hex(id(self)), self.seconds, exception, pending)

    def __str__(self):
        """
        >>> raise Timeout
        Traceback (most recent call last):
            ...
        Timeout
        """
        if self.seconds is None:
            return ''
        if self.seconds == 1:
            suffix = ''
        else:
            suffix = 's'
        if self.exception is None:
            return '%s second%s' % (self.seconds, suffix)
        elif self.exception is False:
            return '%s second%s (silent)' % (self.seconds, suffix)
        else:
            return '%s second%s: %s' % (self.seconds, suffix, self.exception)

    def __enter__(self):
        if not self.pending:
            self.start()
        return self

    def __exit__(self, typ, value, tb):
        self.cancel()
        if value is self and self.exception is False:
            return True


def with_timeout(seconds, function, *args, **kwds):
    """Wrap a call to *function* with a timeout; if the called
    function fails to return before the timeout, cancel it and return a
    flag value, provided by *timeout_value* keyword argument.

    If timeout expires but *timeout_value* is not provided, raise :class:`Timeout`.

    Keyword argument *timeout_value* is not passed to *function*.
    """
    timeout_value = kwds.pop("timeout_value", _NONE)
    timeout = Timeout.start_new(seconds)
    try:
        try:
            return function(*args, **kwds)
        except Timeout:
            if sys.exc_info()[1] is timeout and timeout_value is not _NONE:
                return timeout_value
            raise
    finally:
        timeout.cancel()
