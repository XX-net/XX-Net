# Copyright (c) 2009-2012 Denis Bilenko. See LICENSE for details.

from __future__ import absolute_import
import sys
import os
import traceback

import greenlet  # http://pypi.python.org/pypi/greenlet/
greenlet_version = getattr(greenlet, '__version__', None)
if greenlet_version:
    greenlet_version_info = [int(x) for x in greenlet_version.split('.')]
if not greenlet_version or greenlet_version_info[:3] < [0, 3, 2]:
    raise ImportError('''Your version of greenlet (%s) is too old (required >= 0.3.2)
             You can get a newer version of greenlet from http://pypi.python.org/pypi/greenlet/''' % (greenlet_version, ))
from greenlet import greenlet, getcurrent, GreenletExit


__all__ = ['getcurrent',
           'GreenletExit',
           'spawn_raw',
           'sleep',
           'kill',
           'signal',
           'reinit',
           'get_hub',
           'Hub',
           'Waiter']


PY3 = sys.version_info[0] >= 3


if PY3:
    string_types = str,
    integer_types = int,
else:
    string_types = basestring,
    integer_types = (int, long)


if sys.version_info[0] <= 2:
    import thread
else:
    import _thread as thread
threadlocal = thread._local
_threadlocal = threadlocal()
_threadlocal.Hub = None
get_ident = thread.get_ident
MAIN_THREAD = get_ident()


def spawn_raw(function, *args, **kwargs):
    hub = get_hub()
    g = greenlet(function, hub)
    hub.loop.run_callback(g.switch, *args, **kwargs)
    return g


def sleep(seconds=0, ref=True):
    """Put the current greenlet to sleep for at least *seconds*.

    *seconds* may be specified as an integer, or a float if fractional seconds
    are desired.

    If *ref* is false, the greenlet running sleep() will not prevent gevent.wait()
    from exiting.
    """
    hub = get_hub()
    loop = hub.loop
    if seconds <= 0:
        waiter = Waiter()
        loop.run_callback(waiter.switch)
        waiter.get()
    else:
        hub.wait(loop.timer(seconds, ref=ref))


def idle(priority=0):
    hub = get_hub()
    watcher = hub.loop.idle()
    if priority:
        watcher.priority = priority
    hub.wait(watcher)


def kill(greenlet, exception=GreenletExit):
    """Kill greenlet asynchronously. The current greenlet is not unscheduled.

    Note, that :meth:`gevent.Greenlet.kill` method does the same and more. However,
    MAIN greenlet - the one that exists initially - does not have ``kill()`` method
    so you have to use this function.
    """
    if not greenlet.dead:
        get_hub().loop.run_callback(greenlet.throw, exception)


class signal(object):

    greenlet_class = None

    def __init__(self, signalnum, handler, *args, **kwargs):
        self.hub = get_hub()
        self.watcher = self.hub.loop.signal(signalnum, ref=False)
        self.watcher.start(self._start)
        self.handler = handler
        self.args = args
        self.kwargs = kwargs
        if self.greenlet_class is None:
            from gevent import Greenlet
            self.greenlet_class = Greenlet

    def _get_ref(self):
        return self.watcher.ref

    def _set_ref(self, value):
        self.watcher.ref = value

    ref = property(_get_ref, _set_ref)
    del _get_ref, _set_ref

    def cancel(self):
        self.watcher.stop()

    def _start(self):
        try:
            greenlet = self.greenlet_class(self.handle)
            greenlet.switch()
        except:
            self.hub.handle_error(None, *sys._exc_info())

    def handle(self):
        try:
            self.handler(*self.args, **self.kwargs)
        except:
            self.hub.handle_error(None, *sys.exc_info())


def reinit():
    hub = _get_hub()
    if hub is not None:
        hub.loop.reinit()


def get_hub_class():
    """Return the type of hub to use for the current thread.

    If there's no type of hub for the current thread yet, 'gevent.hub.Hub' is used.
    """
    global _threadlocal
    try:
        hubtype = _threadlocal.Hub
    except AttributeError:
        hubtype = None
    if hubtype is None:
        hubtype = _threadlocal.Hub = Hub
    return hubtype


def get_hub(*args, **kwargs):
    """Return the hub for the current thread.

    If hub does not exists in the current thread, the new one is created with call to :meth:`get_hub_class`.
    """
    global _threadlocal
    try:
        return _threadlocal.hub
    except AttributeError:
        hubtype = get_hub_class()
        hub = _threadlocal.hub = hubtype(*args, **kwargs)
        return hub


def _get_hub():
    """Return the hub for the current thread.

    Return ``None`` if no hub has been created yet.
    """
    global _threadlocal
    try:
        return _threadlocal.hub
    except AttributeError:
        pass


def set_hub(hub):
    _threadlocal.hub = hub


def _import(path):
    if isinstance(path, list):
        if not path:
            raise ImportError('Cannot import from empty list: %r' % (path, ))
        for item in path[:-1]:
            try:
                return _import(item)
            except ImportError:
                pass
        return _import(path[-1])
    if not isinstance(path, string_types):
        return path
    if '.' not in path:
        raise ImportError("Cannot import %r (required format: [path/][package.]module.class)" % path)
    if '/' in path:
        package_path, path = path.rsplit('/', 1)
        sys.path = [package_path] + sys.path
    else:
        package_path = None
    try:
        module, item = path.rsplit('.', 1)
        x = __import__(module)
        for attr in path.split('.')[1:]:
            oldx = x
            x = getattr(x, attr, _NONE)
            if x is _NONE:
                raise ImportError('Cannot import %r from %r' % (attr, oldx))
        return x
    finally:
        try:
            sys.path.remove(package_path)
        except ValueError:
            pass


def config(default, envvar):
    result = os.environ.get(envvar) or default
    if isinstance(result, string_types):
        return result.split(',')
    return result


def resolver_config(default, envvar):
    result = config(default, envvar)
    return [_resolvers.get(x, x) for x in result]


_resolvers = {'ares': 'gevent.resolver_ares.Resolver',
              'thread': 'gevent.resolver_thread.Resolver',
              'block': 'gevent.socket.BlockingResolver'}


class Hub(greenlet):
    """A greenlet that runs the event loop.

    It is created automatically by :func:`get_hub`.
    """

    SYSTEM_ERROR = (KeyboardInterrupt, SystemExit, SystemError)
    NOT_ERROR = (GreenletExit, SystemExit)
    loop_class = config('gevent.core.loop', 'GEVENT_LOOP')
    resolver_class = ['gevent.resolver_thread.Resolver',
                      'gevent.resolver_ares.Resolver',
                      'gevent.socket.BlockingResolver']
    resolver_class = resolver_config(resolver_class, 'GEVENT_RESOLVER')
    threadpool_class = config('gevent.threadpool.ThreadPool', 'GEVENT_THREADPOOL')
    backend = config(None, 'GEVENT_BACKEND')
    format_context = 'pprint.pformat'
    threadpool_size = 10

    def __init__(self, loop=None, default=None):
        greenlet.__init__(self)
        if hasattr(loop, 'run'):
            if default is not None:
                raise TypeError("Unexpected argument: default")
            self.loop = loop
        else:
            if default is None and get_ident() != MAIN_THREAD:
                default = False
            loop_class = _import(self.loop_class)
            if loop is None:
                loop = self.backend
            self.loop = loop_class(flags=loop, default=default)
        self._resolver = None
        self._threadpool = None
        self.format_context = _import(self.format_context)

    def __repr__(self):
        if self.loop is None:
            info = 'destroyed'
        else:
            try:
                info = self.loop._format()
            except Exception, ex:
                info = str(ex) or repr(ex) or 'error'
        result = '<%s at 0x%x %s' % (self.__class__.__name__, id(self), info)
        if self._resolver is not None:
            result += ' resolver=%r' % self._resolver
        if self._threadpool is not None:
            result += ' threadpool=%r' % self._threadpool
        return result + '>'

    def handle_error(self, context, type, value, tb):
        if not issubclass(type, self.NOT_ERROR):
            self.print_exception(context, type, value, tb)
        if context is None or issubclass(type, self.SYSTEM_ERROR):
            self.handle_system_error(type, value)

    def handle_system_error(self, type, value):
        current = getcurrent()
        if current is self or current is self.parent or self.loop is None:
            self.parent.throw(type, value)
        else:
            # in case system error was handled and life goes on
            # switch back to this greenlet as well
            cb = None
            try:
                cb = self.loop.run_callback(current.switch)
            except:
                traceback.print_exc()
            try:
                self.parent.throw(type, value)
            finally:
                if cb is not None:
                    cb.stop()

    def print_exception(self, context, type, value, tb):
        traceback.print_exception(type, value, tb)
        del tb
        if context is not None:
            if not isinstance(context, str):
                try:
                    context = self.format_context(context)
                except:
                    traceback.print_exc()
                    context = repr(context)
            sys.stderr.write('%s failed with %s\n\n' % (context, getattr(type, '__name__', 'exception'), ))

    def switch(self):
        switch_out = getattr(getcurrent(), 'switch_out', None)
        if switch_out is not None:
            switch_out()
        return greenlet.switch(self)

    def switch_out(self):
        raise AssertionError('Impossible to call blocking function in the event loop callback')

    def wait(self, watcher):
        waiter = Waiter()
        unique = object()
        watcher.start(waiter.switch, unique)
        try:
            result = waiter.get()
            assert result is unique, 'Invalid switch into %s: %r (expected %r)' % (getcurrent(), result, unique)
        finally:
            watcher.stop()

    def cancel_wait(self, watcher, error):
        if watcher.callback is not None:
            self.loop.run_callback(self._cancel_wait, watcher, error)

    def _cancel_wait(self, watcher, error):
        if watcher.active:
            switch = watcher.callback
            if switch is not None:
                greenlet = getattr(switch, '__self__', None)
                if greenlet is not None:
                    greenlet.throw(error)

    def run(self):
        assert self is getcurrent(), 'Do not call Hub.run() directly'
        while True:
            loop = self.loop
            loop.error_handler = self
            try:
                loop.run()
            finally:
                loop.error_handler = None  # break the refcount cycle
            self.parent.throw(LoopExit('This operation would block forever'))
        # this function must never return, as it will cause switch() in the parent greenlet
        # to return an unexpected value
        # It is still possible to kill this greenlet with throw. However, in that case
        # switching to it is no longer safe, as switch will return immediatelly

    def join(self, timeout=None):
        """Wait for the event loop to finish. Exits only when there are
        no more spawned greenlets, started servers, active timeouts or watchers.

        If *timeout* is provided, wait no longer for the specified number of seconds.

        Returns True if exited because the loop finished execution.
        Returns False if exited because of timeout expired.
        """
        assert getcurrent() is self.parent, "only possible from the MAIN greenlet"
        if self.dead:
            return True

        waiter = Waiter()

        if timeout is not None:
            timeout = self.loop.timer(timeout, ref=False)
            timeout.start(waiter.switch)

        try:
            try:
                waiter.get()
            except LoopExit:
                return True
        finally:
            if timeout is not None:
                timeout.stop()
        return False

    def destroy(self, destroy_loop=None):
        global _threadlocal
        if self._resolver is not None:
            self._resolver.close()
            del self._resolver
        if self._threadpool is not None:
            self._threadpool.kill()
            del self._threadpool
        if destroy_loop is None:
            destroy_loop = not self.loop.default
        if destroy_loop:
            self.loop.destroy()
        self.loop = None
        if getattr(_threadlocal, 'hub', None) is self:
            del _threadlocal.hub

    def _get_resolver(self):
        if self._resolver is None:
            if self.resolver_class is not None:
                self.resolver_class = _import(self.resolver_class)
                self._resolver = self.resolver_class(hub=self)
        return self._resolver

    def _set_resolver(self, value):
        self._resolver = value

    def _del_resolver(self):
        del self._resolver

    resolver = property(_get_resolver, _set_resolver, _del_resolver)

    def _get_threadpool(self):
        if self._threadpool is None:
            if self.threadpool_class is not None:
                self.threadpool_class = _import(self.threadpool_class)
                self._threadpool = self.threadpool_class(self.threadpool_size, hub=self)
        return self._threadpool

    def _set_threadpool(self, value):
        self._threadpool = value

    def _del_threadpool(self):
        del self._threadpool

    threadpool = property(_get_threadpool, _set_threadpool, _del_threadpool)


class LoopExit(Exception):
    pass


class Waiter(object):
    """A low level communication utility for greenlets.

    Wrapper around greenlet's ``switch()`` and ``throw()`` calls that makes them somewhat safer:

    * switching will occur only if the waiting greenlet is executing :meth:`get` method currently;
    * any error raised in the greenlet is handled inside :meth:`switch` and :meth:`throw`
    * if :meth:`switch`/:meth:`throw` is called before the receiver calls :meth:`get`, then :class:`Waiter`
      will store the value/exception. The following :meth:`get` will return the value/raise the exception.

    The :meth:`switch` and :meth:`throw` methods must only be called from the :class:`Hub` greenlet.
    The :meth:`get` method must be called from a greenlet other than :class:`Hub`.

        >>> result = Waiter()
        >>> timer = get_hub().loop.timer(0.1)
        >>> timer.start(result.switch, 'hello from Waiter')
        >>> result.get() # blocks for 0.1 seconds
        'hello from Waiter'

    If switch is called before the greenlet gets a chance to call :meth:`get` then
    :class:`Waiter` stores the value.

        >>> result = Waiter()
        >>> timer = get_hub().loop.timer(0.1)
        >>> timer.start(result.switch, 'hi from Waiter')
        >>> sleep(0.2)
        >>> result.get() # returns immediatelly without blocking
        'hi from Waiter'

    .. warning::

        This a limited and dangerous way to communicate between greenlets. It can easily
        leave a greenlet unscheduled forever if used incorrectly. Consider using safer
        :class:`Event`/:class:`AsyncResult`/:class:`Queue` classes.
    """

    __slots__ = ['hub', 'greenlet', 'value', '_exception']

    def __init__(self, hub=None):
        if hub is None:
            self.hub = get_hub()
        else:
            self.hub = hub
        self.greenlet = None
        self.value = None
        self._exception = _NONE

    def clear(self):
        self.greenlet = None
        self.value = None
        self._exception = _NONE

    def __str__(self):
        if self._exception is _NONE:
            return '<%s greenlet=%s>' % (type(self).__name__, self.greenlet)
        elif self._exception is None:
            return '<%s greenlet=%s value=%r>' % (type(self).__name__, self.greenlet, self.value)
        else:
            return '<%s greenlet=%s exc_info=%r>' % (type(self).__name__, self.greenlet, self.exc_info)

    def ready(self):
        """Return true if and only if it holds a value or an exception"""
        return self._exception is not _NONE

    def successful(self):
        """Return true if and only if it is ready and holds a value"""
        return self._exception is None

    @property
    def exc_info(self):
        "Holds the exception info passed to :meth:`throw` if :meth:`throw` was called. Otherwise ``None``."
        if self._exception is not _NONE:
            return self._exception

    def switch(self, value=None):
        """Switch to the greenlet if one's available. Otherwise store the value."""
        greenlet = self.greenlet
        if greenlet is None:
            self.value = value
            self._exception = None
        else:
            assert getcurrent() is self.hub, "Can only use Waiter.switch method from the Hub greenlet"
            switch = greenlet.switch
            try:
                switch(value)
            except:
                self.hub.handle_error(switch, *sys.exc_info())

    def switch_args(self, *args):
        return self.switch(args)

    def throw(self, *throw_args):
        """Switch to the greenlet with the exception. If there's no greenlet, store the exception."""
        greenlet = self.greenlet
        if greenlet is None:
            self._exception = throw_args
        else:
            assert getcurrent() is self.hub, "Can only use Waiter.switch method from the Hub greenlet"
            throw = greenlet.throw
            try:
                throw(*throw_args)
            except:
                self.hub.handle_error(throw, *sys.exc_info())

    def get(self):
        """If a value/an exception is stored, return/raise it. Otherwise until switch() or throw() is called."""
        if self._exception is not _NONE:
            if self._exception is None:
                return self.value
            else:
                getcurrent().throw(*self._exception)
        else:
            assert self.greenlet is None, 'This Waiter is already used by %r' % (self.greenlet, )
            self.greenlet = getcurrent()
            try:
                return self.hub.switch()
            finally:
                self.greenlet = None

    def __call__(self, source):
        if source.exception is None:
            self.switch(source.value)
        else:
            self.throw(source.exception)

    # can also have a debugging version, that wraps the value in a tuple (self, value) in switch()
    # and unwraps it in wait() thus checking that switch() was indeed called


def iwait(objects, timeout=None):
    """Yield objects as they are ready, until all are ready or timeout expired.

    *objects* must be iterable yielding instance implementing wait protocol (rawlink() and unlink()).
    """
    # QQQ would be nice to support iterable here that can be generated slowly (why?)
    waiter = Waiter()
    switch = waiter.switch
    if timeout is not None:
        timer = get_hub().loop.timer(timeout, priority=-1)
        timer.start(waiter.switch, _NONE)
    try:
        count = len(objects)
        for obj in objects:
            obj.rawlink(switch)
        for _ in xrange(count):
            item = waiter.get()
            waiter.clear()
            if item is _NONE:
                return
            yield item
    finally:
        if timeout is not None:
            timer.stop()
        for obj in objects:
            unlink = getattr(obj, 'unlink', None)
            if unlink:
                try:
                    unlink(switch)
                except:
                    traceback.print_exc()


def wait(objects=None, timeout=None, count=None):
    """Wait for *objects* to become ready or for event loop to finish.

    If *objects* is provided, it should be an iterable containg objects implementing wait protocol (rawlink() and
    unlink() methods):

    - :class:`gevent.Greenlet` instance
    - :class:`gevent.event.Event` instance
    - :class:`gevent.lock.Semaphore` instance
    - :class:`gevent.subprocess.Popen` instance

    If *objects* is ``None`` (the default), ``wait()`` blocks until all event loops has nothing to do:

    - all greenlets have finished
    - all servers were stopped
    - all event loop watchers were stopped.

    If *count* is ``None`` (the default), wait for all of *object* to become ready.

    If *count* is a number, wait for *count* object to become ready. (For example, if count is ``1`` then the
    function exits when any object in the list is ready).

    If *timeout* is provided, it specifies the maximum number of seconds ``wait()`` will block.

    Returns the list of ready objects, in the order in which they were ready.
    """
    if objects is None:
        return get_hub().join(timeout=timeout)
    result = []
    if count is None:
        return list(iwait(objects, timeout))
    for obj in iwait(objects=objects, timeout=timeout):
        result.append(obj)
        count -= 1
        if count <= 0:
            break
    return result


class linkproxy(object):
    __slots__ = ['callback', 'obj']

    def __init__(self, callback, obj):
        self.callback = callback
        self.obj = obj

    def __call__(self, *args):
        callback = self.callback
        obj = self.obj
        self.callback = None
        self.obj = None
        callback(obj)


class _NONE(object):
    "A special thingy you must never pass to any of gevent API"
    __slots__ = []

    def __repr__(self):
        return '<_NONE>'

_NONE = _NONE()
