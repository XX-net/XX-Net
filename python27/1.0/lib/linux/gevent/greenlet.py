# Copyright (c) 2009-2010 Denis Bilenko. See LICENSE for details.

import sys
import traceback
from gevent import core
from gevent.hub import greenlet, getcurrent, get_hub, GreenletExit, Waiter
from gevent.timeout import Timeout


__all__ = ['Greenlet',
           'joinall',
           'killall']


class SpawnedLink(object):
    """A wrapper around link that calls it in another greenlet.

    Can be called only from main loop.
    """
    __slots__ = ['callback']

    def __init__(self, callback):
        self.callback = callback

    def __call__(self, source):
        g = greenlet(self.callback, get_hub())
        g.switch(source)

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


class SuccessSpawnedLink(SpawnedLink):
    """A wrapper around link that calls it in another greenlet only if source succeed.

    Can be called only from main loop.
    """
    __slots__ = []

    def __call__(self, source):
        if source.successful():
            return SpawnedLink.__call__(self, source)


class FailureSpawnedLink(SpawnedLink):
    """A wrapper around link that calls it in another greenlet only if source failed.

    Can be called only from main loop.
    """
    __slots__ = []

    def __call__(self, source):
        if not source.successful():
            return SpawnedLink.__call__(self, source)


class GreenletLink(object):
    """A wrapper around greenlet that raises a LinkedExited exception when called.

    Can be called only from main loop.
    """
    __slots__ = ['greenlet']

    def __init__(self, greenlet):
        self.greenlet = greenlet

    def __call__(self, source):
        if source.successful():
            if isinstance(source.value, GreenletExit):
                error = LinkedKilled(source)
            else:
                error = LinkedCompleted(source)
        else:
            error = LinkedFailed(source)
        self.greenlet.throw(error)

    def __hash__(self):
        return hash(self.greenlet)

    def __eq__(self, other):
        return self.greenlet == getattr(other, 'greenlet', other)

    def __str__(self):
        return str(self.greenlet)

    def __repr__(self):
        return repr(self.greenlet)


class SuccessGreenletLink(GreenletLink):
    """A wrapper around greenlet that raises a LinkedExited exception when called
    if source has succeed.

    Can be called only from main loop.
    """
    __slots__ = []

    def __call__(self, source):
        if source.successful():
            return GreenletLink.__call__(self, source)


class FailureGreenletLink(GreenletLink):
    """A wrapper around greenlet that raises a LinkedExited exception when called
    if source has failed.

    Can be called only from main loop.
    """
    __slots__ = []

    def __call__(self, source):
        if not source.successful():
            return GreenletLink.__call__(self, source)


class Greenlet(greenlet):
    """A light-weight cooperatively-scheduled execution unit."""

    def __init__(self, run=None, *args, **kwargs):
        greenlet.__init__(self, parent=get_hub())
        if run is not None:
            self._run = run
        self.args = args
        self.kwargs = kwargs
        self._links = []
        self.value = None
        self._exception = _NONE
        self._notifier = None
        self._start_event = None

    @property
    def started(self):
        return self._start_event is not None or bool(self)

    def ready(self):
        """Return true if and only if the greenlet has finished execution."""
        return self.dead or self._exception is not _NONE

    def successful(self):
        """Return true if and only if the greenlet has finished execution successfully,
        that is, without raising an error."""
        return self._exception is None

    def __repr__(self):
        classname = self.__class__.__name__
        result = '<%s at %s' % (classname, hex(id(self)))
        formatted = self._formatinfo()
        if formatted:
            result += ': ' + formatted
        return result + '>'

    def _formatinfo(self):
        try:
            return self._formatted_info
        except AttributeError:
            pass
        try:
            result = getfuncname(self.__dict__['_run'])
        except Exception:
            pass
        else:
            args = []
            if self.args:
                args = [repr(x)[:50] for x in self.args]
            if self.kwargs:
                args.extend(['%s=%s' % (key, repr(value)[:50]) for (key, value) in self.kwargs.items()])
            if args:
                result += '(' + ', '.join(args) + ')'
            # it is important to save the result here, because once the greenlet exits '_run' attribute will be removed
            self._formatted_info = result
            return result
        return ''

    @property
    def exception(self):
        """Holds the exception instance raised by the function if the greenlet has finished with an error.
        Otherwise ``None``.
        """
        if self._exception is not _NONE:
            return self._exception

    def throw(self, *args):
        """Immediatelly switch into the greenlet and raise an exception in it.

        Should only be called from the HUB, otherwise the current greenlet is left unscheduled forever.
        To raise an exception in a safely manner from any greenlet, use :meth:`kill`.

        If a greenlet was started but never switched to yet, then also
        a) cancel the event that will start it
        b) fire the notifications as if an exception was raised in a greenlet
        """
        if self._start_event is not None:
            self._start_event.cancel()
            self._start_event = None
        try:
            greenlet.throw(self, *args)
        finally:
            if self._exception is _NONE and self.dead:
                # the greenlet was not started yet, so _report_error was not called, so
                # the result was not set and the links weren't notified. let's do it here.
                # checking that self.dead is true is essential, because the exception raised by
                # throw() could have been cancelled by the greenlet's function.
                if len(args) == 1:
                    arg = args[0]
                    #if isinstance(arg, type):
                    if type(arg) is type(Exception):
                        args = (arg, arg(), None)
                    else:
                        args = (type(arg), arg, None)
                elif not args:
                    args = (GreenletExit, GreenletExit(), None)
                self._report_error(args)

    def start(self):
        """Schedule the greenlet to run in this loop iteration"""
        assert not self.started, 'Greenlet already started'
        self._start_event = core.active_event(self.switch)

    def start_later(self, seconds):
        """Schedule the greenlet to run in the future loop iteration *seconds* later"""
        assert not self.started, 'Greenlet already started'
        self._start_event = core.timer(seconds, self.switch)

    @classmethod
    def spawn(cls, *args, **kwargs):
        """Return a new :class:`Greenlet` object, scheduled to start.

        The arguments are passed to :meth:`Greenlet.__init__`.
        """
        g = cls(*args, **kwargs)
        g.start()
        return g

    @classmethod
    def spawn_later(cls, seconds, *args, **kwargs):
        """Return a Greenlet object, scheduled to start *seconds* later.

        The arguments are passed to :meth:`Greenlet.__init__`.
        """
        g = cls(*args, **kwargs)
        g.start_later(seconds)
        return g

    @classmethod
    def spawn_link(cls, *args, **kwargs):
        g = cls.spawn(*args, **kwargs)
        g.link()
        return g

    @classmethod
    def spawn_link_value(cls, *args, **kwargs):
        g = cls.spawn(*args, **kwargs)
        g.link_value()
        return g

    @classmethod
    def spawn_link_exception(cls, *args, **kwargs):
        g = cls.spawn(*args, **kwargs)
        g.link_exception()
        return g

    def kill(self, exception=GreenletExit, block=True, timeout=None):
        """Raise the exception in the greenlet.

        If block is ``True`` (the default), wait until the greenlet dies or the optional timeout expires.
        If block is ``False``, the current greenlet is not unscheduled.

        The function always returns ``None`` and never raises an error.

        `Changed in version 0.13.0:` *block* is now ``True`` by default.
        """
        if self._start_event is not None:
            self._start_event.cancel()
            self._start_event = None
        if not self.dead:
            waiter = Waiter()
            core.active_event(_kill, self, exception, waiter)
            if block:
                waiter.get()
                self.join(timeout)
        # it should be OK to use kill() in finally or kill a greenlet from more than one place;
        # thus it should not raise when the greenlet is already killed (= not started)

    def get(self, block=True, timeout=None):
        """Return the result the greenlet has returned or re-raise the exception it has raised.

        If block is ``False``, raise :class:`gevent.Timeout` if the greenlet is still alive.
        If block is ``True``, unschedule the current greenlet until the result is available
        or the timeout expires. In the latter case, :class:`gevent.Timeout` is raised.
        """
        if self.ready():
            if self.successful():
                return self.value
            else:
                raise self._exception
        if block:
            switch = getcurrent().switch
            self.rawlink(switch)
            try:
                t = Timeout.start_new(timeout)
                try:
                    result = self.parent.switch()
                    assert result is self, 'Invalid switch into Greenlet.get(): %r' % (result, )
                finally:
                    t.cancel()
            except:
                # unlinking in 'except' instead of finally is an optimization:
                # if switch occurred normally then link was already removed in _notify_links
                # and there's no need to touch the links set.
                # Note, however, that if "Invalid switch" assert was removed and invalid switch
                # did happen, the link would remain, causing another invalid switch later in this greenlet.
                self.unlink(switch)
                raise
            if self.ready():
                if self.successful():
                    return self.value
                else:
                    raise self._exception
        else:
            raise Timeout

    def join(self, timeout=None):
        """Wait until the greenlet finishes or *timeout* expires.
        Return ``None`` regardless.
        """
        if self.ready():
            return
        else:
            switch = getcurrent().switch
            self.rawlink(switch)
            try:
                t = Timeout.start_new(timeout)
                try:
                    result = self.parent.switch()
                    assert result is self, 'Invalid switch into Greenlet.join(): %r' % (result, )
                finally:
                    t.cancel()
            except Timeout, ex:
                self.unlink(switch)
                if ex is not t:
                    raise
            except:
                self.unlink(switch)
                raise

    def _report_result(self, result):
        self._exception = None
        self.value = result
        if self._links and self._notifier is None:
            self._notifier = core.active_event(self._notify_links)

    def _report_error(self, exc_info):
        exception = exc_info[1]
        if isinstance(exception, GreenletExit):
            self._report_result(exception)
            return
        try:
            traceback.print_exception(*exc_info)
        except:
            pass
        self._exception = exception

        if self._links and self._notifier is None:
            self._notifier = core.active_event(self._notify_links)

        info = str(self) + ' failed with '
        try:
            info += self._exception.__class__.__name__
        except Exception:
            info += str(self._exception) or repr(self._exception)
        sys.stderr.write(info + '\n\n')

    def run(self):
        try:
            self._start_event = None
            try:
                result = self._run(*self.args, **self.kwargs)
            except:
                self._report_error(sys.exc_info())
                return
            self._report_result(result)
        finally:
            self.__dict__.pop('_run', None)
            self.__dict__.pop('args', None)
            self.__dict__.pop('kwargs', None)

    def rawlink(self, callback):
        """Register a callable to be executed when the greenlet finishes the execution.

        WARNING: the callable will be called in the HUB greenlet.
        """
        if not callable(callback):
            raise TypeError('Expected callable: %r' % (callback, ))
        self._links.append(callback)
        if self.ready() and self._notifier is None:
            self._notifier = core.active_event(self._notify_links)

    def link(self, receiver=None, GreenletLink=GreenletLink, SpawnedLink=SpawnedLink):
        """Link greenlet's completion to callable or another greenlet.

        If *receiver* is a callable then it will be called with this instance as an argument
        once this greenlet's dead. A callable is called in its own greenlet.

        If *receiver* is a greenlet then an :class:`LinkedExited` exception will be
        raised in it once this greenlet's dead.

        If *receiver* is ``None``, link to the current greenlet.

        Always asynchronous, unless receiver is a current greenlet and the result is ready.
        If this greenlet is already dead, then notification will performed in this loop
        iteration as soon as this greenlet switches to the hub.
        """
        current = getcurrent()
        if receiver is None or receiver is current:
            receiver = GreenletLink(current)
            if self.ready():
                # special case : linking to current greenlet when the result is ready
                # raise LinkedExited immediatelly
                receiver(self)
                return
        elif not callable(receiver):
            if isinstance(receiver, greenlet):
                receiver = GreenletLink(receiver)
            else:
                raise TypeError('Expected callable or greenlet: %r' % (receiver, ))
        else:
            receiver = SpawnedLink(receiver)
        self.rawlink(receiver)

    def unlink(self, receiver=None):
        """Remove the receiver set by :meth:`link` or :meth:`rawlink`"""
        if receiver is None:
            receiver = getcurrent()
        # discarding greenlets when we have GreenletLink instances in _links works, because
        # a GreenletLink instance pretends to be a greenlet, hash-wise and eq-wise
        try:
            self._links.remove(receiver)
        except ValueError:
            pass

    def link_value(self, receiver=None, GreenletLink=SuccessGreenletLink, SpawnedLink=SuccessSpawnedLink):
        """Like :meth:`link` but *receiver* is only notified when the greenlet has completed successfully"""
        self.link(receiver=receiver, GreenletLink=GreenletLink, SpawnedLink=SpawnedLink)

    def link_exception(self, receiver=None, GreenletLink=FailureGreenletLink, SpawnedLink=FailureSpawnedLink):
        """Like :meth:`link` but *receiver* is only notified when the greenlet dies because of unhandled exception"""
        self.link(receiver=receiver, GreenletLink=GreenletLink, SpawnedLink=SpawnedLink)

    def _notify_links(self):
        try:
            while self._links:
                link = self._links.pop()
                try:
                    link(self)
                except:
                    traceback.print_exc()
                    try:
                        sys.stderr.write('Failed to notify link %s of %r\n\n' % (getfuncname(link), self))
                    except:
                        traceback.print_exc()
        finally:
            self._notifier = None


def _kill(greenlet, exception, waiter):
    try:
        greenlet.throw(exception)
    except:
        traceback.print_exc()
    waiter.switch()


def joinall(greenlets, timeout=None, raise_error=False):
    from gevent.queue import Queue
    queue = Queue()
    put = queue.put
    timeout = Timeout.start_new(timeout)
    try:
        try:
            for greenlet in greenlets:
                greenlet.rawlink(put)
            if raise_error:
                for _ in xrange(len(greenlets)):
                    greenlet = queue.get()
                    if not greenlet.successful():
                        raise greenlet.exception
            else:
                for _ in xrange(len(greenlets)):
                    queue.get()
        except:
            for greenlet in greenlets:
                greenlet.unlink(put)
            if sys.exc_info()[1] is not timeout:
                raise
    finally:
        timeout.cancel()


def _killall3(greenlets, exception, waiter):
    diehards = []
    for g in greenlets:
        if not g.dead:
            try:
                g.throw(exception)
            except:
                traceback.print_exc()
            if not g.dead:
                diehards.append(g)
    waiter.switch(diehards)


def _killall(greenlets, exception):
    for g in greenlets:
        if not g.dead:
            try:
                g.throw(exception)
            except:
                traceback.print_exc()


def killall(greenlets, exception=GreenletExit, block=True, timeout=None):
    if block:
        waiter = Waiter()
        core.active_event(_killall3, greenlets, exception, waiter)
        if block:
            t = Timeout.start_new(timeout)
            try:
                alive = waiter.get()
                if alive:
                    joinall(alive, raise_error=False)
            finally:
                t.cancel()
    else:
        core.active_event(_killall, greenlets, exception)


class LinkedExited(Exception):
    pass


class LinkedCompleted(LinkedExited):
    """Raised when a linked greenlet finishes the execution cleanly"""

    msg = "%r completed successfully"

    def __init__(self, source):
        assert source.ready(), source
        assert source.successful(), source
        LinkedExited.__init__(self, self.msg % source)


class LinkedKilled(LinkedCompleted):
    """Raised when a linked greenlet returns GreenletExit instance"""

    msg = "%r returned %s"

    def __init__(self, source):
        try:
            result = source.value.__class__.__name__
        except:
            result = str(source) or repr(source)
        LinkedExited.__init__(self, self.msg % (source, result))


class LinkedFailed(LinkedExited):
    """Raised when a linked greenlet dies because of unhandled exception"""

    msg = "%r failed with %s"

    def __init__(self, source):
        exception = source.exception
        try:
            excname = exception.__class__.__name__
        except:
            excname = str(exception) or repr(exception)
        LinkedExited.__init__(self, self.msg % (source, excname))


def getfuncname(func):
    if not hasattr(func, 'im_self'):
        try:
            funcname = func.__name__
        except AttributeError:
            pass
        else:
            if funcname != '<lambda>':
                return funcname
    return repr(func)


_NONE = Exception("Neither exception nor value")
