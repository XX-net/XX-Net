""" Back-ported, durable, and portable selectors """

# MIT License
#
# Copyright (c) 2017 Seth Michael Larson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from collections import namedtuple
from collections.abc import Mapping
import errno
import math
import platform
import select
import socket
import sys
import time

try:
    monotonic = time.monotonic
except AttributeError:
    monotonic = time.time

__author__ = 'Seth Michael Larson'
__email__ = 'sethmichaellarson@protonmail.com'
__version__ = '2.0.2'
__license__ = 'MIT'
__url__ = 'https://www.github.com/SethMichaelLarson/selectors2'

__all__ = ['EVENT_READ',
           'EVENT_WRITE',
           'SelectorKey',
           'DefaultSelector',
           'BaseSelector']

EVENT_READ = (1 << 0)
EVENT_WRITE = (1 << 1)
_DEFAULT_SELECTOR = None
_SYSCALL_SENTINEL = object()  # Sentinel in case a system call returns None.
_ERROR_TYPES = (OSError, IOError, socket.error)

try:
    _INTEGER_TYPES = (int, long)
except NameError:
    _INTEGER_TYPES = (int,)


SelectorKey = namedtuple('SelectorKey', ['fileobj', 'fd', 'events', 'data'])


class _SelectorMapping(Mapping):
    """ Mapping of file objects to selector keys """

    def __init__(self, selector):
        self._selector = selector

    def __len__(self):
        return len(self._selector._fd_to_key)

    def __getitem__(self, fileobj):
        try:
            fd = self._selector._fileobj_lookup(fileobj)
            return self._selector._fd_to_key[fd]
        except KeyError:
            raise KeyError("{0!r} is not registered.".format(fileobj))

    def __iter__(self):
        return iter(self._selector._fd_to_key)


def _fileobj_to_fd(fileobj):
    """ Return a file descriptor from a file object. If
    given an integer will simply return that integer back. """
    if isinstance(fileobj, _INTEGER_TYPES):
        fd = fileobj
    else:
        for _integer_type in _INTEGER_TYPES:
            try:
                fd = _integer_type(fileobj.fileno())
                break
            except (AttributeError, TypeError, ValueError):
                continue
        else:
            raise ValueError("Invalid file object: {0!r}".format(fileobj))
    if fd < 0:
        raise ValueError("Invalid file descriptor: {0}".format(fd))
    return fd


class BaseSelector(object):
    """ Abstract Selector class

    A selector supports registering file objects to be monitored
    for specific I/O events.

    A file object is a file descriptor or any object with a
    `fileno()` method. An arbitrary object can be attached to the
    file object which can be used for example to store context info,
    a callback, etc.

    A selector can use various implementations (select(), poll(), epoll(),
    and kqueue()) depending on the platform. The 'DefaultSelector' class uses
    the most efficient implementation for the current platform.
    """
    def __init__(self):
        # Maps file descriptors to keys.
        self._fd_to_key = {}

        # Read-only mapping returned by get_map()
        self._map = _SelectorMapping(self)

    def _fileobj_lookup(self, fileobj):
        """ Return a file descriptor from a file object.
        This wraps _fileobj_to_fd() to do an exhaustive
        search in case the object is invalid but we still
        have it in our map. Used by unregister() so we can
        unregister an object that was previously registered
        even if it is closed. It is also used by _SelectorMapping
        """
        try:
            return _fileobj_to_fd(fileobj)
        except ValueError:

            # Search through all our mapped keys.
            for key in self._fd_to_key.values():
                if key.fileobj is fileobj:
                    return key.fd

            # Raise ValueError after all.
            raise

    def register(self, fileobj, events, data=None):
        """ Register a file object for a set of events to monitor. """
        if (not events) or (events & ~(EVENT_READ | EVENT_WRITE)):
            raise ValueError("Invalid events: {0!r}".format(events))

        key = SelectorKey(fileobj, self._fileobj_lookup(fileobj), events, data)

        if key.fd in self._fd_to_key:
            raise KeyError("{0!r} (FD {1}) is already registered"
                           .format(fileobj, key.fd))

        self._fd_to_key[key.fd] = key
        return key

    def unregister(self, fileobj):
        """ Unregister a file object from being monitored. """
        try:
            key = self._fd_to_key.pop(self._fileobj_lookup(fileobj))
        except KeyError:
            raise KeyError("{0!r} is not registered".format(fileobj))

        # Getting the fileno of a closed socket on Windows errors with EBADF.
        except socket.error as err:
            if err.errno != errno.EBADF:
                raise
            else:
                for key in self._fd_to_key.values():
                    if key.fileobj is fileobj:
                        self._fd_to_key.pop(key.fd)
                        break
                else:
                    raise KeyError("{0!r} is not registered".format(fileobj))
        return key

    def modify(self, fileobj, events, data=None):
        """ Change a registered file object monitored events and data. """
        # NOTE: Some subclasses optimize this operation even further.
        try:
            key = self._fd_to_key[self._fileobj_lookup(fileobj)]
        except KeyError:
            raise KeyError("{0!r} is not registered".format(fileobj))

        if events != key.events:
            self.unregister(fileobj)
            key = self.register(fileobj, events, data)

        elif data != key.data:
            # Use a shortcut to update the data.
            key = key._replace(data=data)
            self._fd_to_key[key.fd] = key

        return key

    def register_event(self, fileobj, event, data):
        try:
            key = self._fd_to_key[self._fileobj_lookup(fileobj)]
        except KeyError:
            # not registered any event before, register
            return self.register(fileobj, event, data)

        if key.events & event:
            # event already registered
            return
        else:
            events = (key.events | event)
            self.unregister(fileobj)
            self.register(fileobj, events, data)

    def unregister_event(self, fileobj, event):
        # Return None if fileobj is removed or not exists

        try:
            key = self._fd_to_key[self._fileobj_lookup(fileobj)]
        except KeyError:
            # not exists
            return

        if not key.events & event:
            # this event is not registered
            return key

        if key.events == event:
            self.unregister(fileobj)
            return
        else:
            events = (key.events & ~(event))
            data = key.data
            self.unregister(fileobj)
            return self.register(fileobj, events, data)

    def select(self, timeout=None):
        """ Perform the actual selection until some monitored file objects
        are ready or the timeout expires. """
        raise NotImplementedError()

    def close(self):
        """ Close the selector. This must be called to ensure that all
        underlying resources are freed. """
        self._fd_to_key.clear()
        self._map = None

    def get_key(self, fileobj):
        """ Return the key associated with a registered file object. """
        mapping = self.get_map()
        if mapping is None:
            raise RuntimeError("Selector is closed")
        try:
            return mapping[fileobj]
        except KeyError:
            raise KeyError("{0!r} is not registered".format(fileobj))

    def get_map(self):
        """ Return a mapping of file objects to selector keys """
        return self._map

    def _key_from_fd(self, fd):
        """ Return the key associated to a given file descriptor
         Return None if it is not found. """
        try:
            return self._fd_to_key[fd]
        except KeyError:
            return None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


# Almost all platforms have select.select()
if hasattr(select, "select"):
    class SelectSelector(BaseSelector):
        """ Select-based selector. """
        def __init__(self):
            super(SelectSelector, self).__init__()
            self._readers = set()
            self._writers = set()

        def register(self, fileobj, events, data=None):
            key = super(SelectSelector, self).register(fileobj, events, data)
            if events & EVENT_READ:
                self._readers.add(key.fd)
            if events & EVENT_WRITE:
                self._writers.add(key.fd)
            return key

        def unregister(self, fileobj):
            key = super(SelectSelector, self).unregister(fileobj)
            self._readers.discard(key.fd)
            self._writers.discard(key.fd)
            return key

        def select(self, timeout=None):
            # Selecting on empty lists on Windows errors out.
            if not len(self._readers) and not len(self._writers):
                return []

            timeout = None if timeout is None else max(timeout, 0.0)
            ready = []
            r, w, _ = _syscall_wrapper(self._wrap_select, True, self._readers,
                                       self._writers, timeout=timeout)
            r = set(r)
            w = set(w)
            for fd in r | w:
                events = 0
                if fd in r:
                    events |= EVENT_READ
                if fd in w:
                    events |= EVENT_WRITE

                key = self._key_from_fd(fd)
                if key:
                    ready.append((key, events & key.events))
            return ready

        def _wrap_select(self, r, w, timeout=None):
            """ Wrapper for select.select because timeout is a positional arg """
            return select.select(r, w, [], timeout)

    __all__.append('SelectSelector')

    # Jython has a different implementation of .fileno() for socket objects.
    if platform.python_implementation() == 'Jython':
        class _JythonSelectorMapping(object):
            """ This is an implementation of _SelectorMapping that is built
            for use specifically with Jython, which does not provide a hashable
            value from socket.socket.fileno(). """

            def __init__(self, selector):
                assert isinstance(selector, JythonSelectSelector)
                self._selector = selector

            def __len__(self):
                return len(self._selector._sockets)

            def __getitem__(self, fileobj):
                for sock, key in self._selector._sockets:
                    if sock is fileobj:
                        return key
                else:
                    raise KeyError("{0!r} is not registered.".format(fileobj))

        class JythonSelectSelector(SelectSelector):
            """ This is an implementation of SelectSelector that is for Jython
            which works around that Jython's socket.socket.fileno() does not
            return an integer fd value. All SelectorKey.fd will be equal to -1
            and should not be used. This instead uses object id to compare fileobj
            and will only use select.select as it's the only selector that allows
            directly passing in socket objects rather than registering fds.
            See: http://bugs.jython.org/issue1678
                 https://wiki.python.org/jython/NewSocketModule#socket.fileno.28.29_does_not_return_an_integer
            """

            def __init__(self):
                super(JythonSelectSelector, self).__init__()

                self._sockets = []  # Uses a list of tuples instead of dictionary.
                self._map = _JythonSelectorMapping(self)
                self._readers = []
                self._writers = []

                # Jython has a select.cpython_compatible_select function in older versions.
                self._select_func = getattr(select, 'cpython_compatible_select', select.select)

            def register(self, fileobj, events, data=None):
                for sock, _ in self._sockets:
                    if sock is fileobj:
                        raise KeyError("{0!r} is already registered"
                                       .format(fileobj, sock))

                key = SelectorKey(fileobj, -1, events, data)
                self._sockets.append((fileobj, key))

                if events & EVENT_READ:
                    self._readers.append(fileobj)
                if events & EVENT_WRITE:
                    self._writers.append(fileobj)
                return key

            def unregister(self, fileobj):
                for i, (sock, key) in enumerate(self._sockets):
                    if sock is fileobj:
                        break
                else:
                    raise KeyError("{0!r} is not registered.".format(fileobj))

                if key.events & EVENT_READ:
                    self._readers.remove(fileobj)
                if key.events & EVENT_WRITE:
                    self._writers.remove(fileobj)

                del self._sockets[i]
                return key

            def _wrap_select(self, r, w, timeout=None):
                """ Wrapper for select.select because timeout is a positional arg """
                return self._select_func(r, w, [], timeout)

        __all__.append('JythonSelectSelector')
        SelectSelector = JythonSelectSelector  # Override so the wrong selector isn't used.


if hasattr(select, "poll"):
    class PollSelector(BaseSelector):
        """ Poll-based selector """
        def __init__(self):
            super(PollSelector, self).__init__()
            self._poll = select.poll()

        def register(self, fileobj, events, data=None):
            key = super(PollSelector, self).register(fileobj, events, data)
            event_mask = 0
            if events & EVENT_READ:
                event_mask |= select.POLLIN
            if events & EVENT_WRITE:
                event_mask |= select.POLLOUT
            self._poll.register(key.fd, event_mask)
            return key

        def unregister(self, fileobj):
            key = super(PollSelector, self).unregister(fileobj)
            self._poll.unregister(key.fd)
            return key

        def _wrap_poll(self, timeout=None):
            """ Wrapper function for select.poll.poll() so that
            _syscall_wrapper can work with only seconds. """
            if timeout is not None:
                if timeout <= 0:
                    timeout = 0
                else:
                    # select.poll.poll() has a resolution of 1 millisecond,
                    # round away from zero to wait *at least* timeout seconds.
                    timeout = math.ceil(timeout * 1000)

            result = self._poll.poll(timeout)
            return result

        def select(self, timeout=None):
            ready = []
            fd_events = _syscall_wrapper(self._wrap_poll, True, timeout=timeout)
            for fd, event_mask in fd_events:
                events = 0
                if event_mask & ~select.POLLIN:
                    events |= EVENT_WRITE
                if event_mask & ~select.POLLOUT:
                    events |= EVENT_READ

                key = self._key_from_fd(fd)
                if key:
                    ready.append((key, events & key.events))

            return ready

    __all__.append('PollSelector')

if hasattr(select, "epoll"):
    class EpollSelector(BaseSelector):
        """ Epoll-based selector """
        def __init__(self):
            super(EpollSelector, self).__init__()
            self._epoll = select.epoll()

        def fileno(self):
            return self._epoll.fileno()

        def register(self, fileobj, events, data=None):
            key = super(EpollSelector, self).register(fileobj, events, data)
            events_mask = 0
            if events & EVENT_READ:
                events_mask |= select.EPOLLIN
            if events & EVENT_WRITE:
                events_mask |= select.EPOLLOUT
            _syscall_wrapper(self._epoll.register, False, key.fd, events_mask)
            return key

        def unregister(self, fileobj):
            key = super(EpollSelector, self).unregister(fileobj)
            try:
                _syscall_wrapper(self._epoll.unregister, False, key.fd)
            except _ERROR_TYPES:
                # This can occur when the fd was closed since registry.
                pass
            return key

        def select(self, timeout=None):
            if timeout is not None:
                if timeout <= 0:
                    timeout = 0.0
                else:
                    # select.epoll.poll() has a resolution of 1 millisecond
                    # but luckily takes seconds so we don't need a wrapper
                    # like PollSelector. Just for better rounding.
                    timeout = math.ceil(timeout * 1000) * 0.001
                timeout = float(timeout)
            else:
                timeout = -1.0  # epoll.poll() must have a float.

            # We always want at least 1 to ensure that select can be called
            # with no file descriptors registered. Otherwise will fail.
            max_events = max(len(self._fd_to_key), 1)

            ready = []
            fd_events = _syscall_wrapper(self._epoll.poll, True,
                                         timeout=timeout,
                                         maxevents=max_events)
            for fd, event_mask in fd_events:
                events = 0
                if event_mask & ~select.EPOLLIN:
                    events |= EVENT_WRITE
                if event_mask & ~select.EPOLLOUT:
                    events |= EVENT_READ

                key = self._key_from_fd(fd)
                if key:
                    ready.append((key, events & key.events))
            return ready

        def close(self):
            self._epoll.close()
            super(EpollSelector, self).close()

    __all__.append('EpollSelector')


if hasattr(select, "devpoll"):
    class DevpollSelector(BaseSelector):
        """Solaris /dev/poll selector."""

        def __init__(self):
            super(DevpollSelector, self).__init__()
            self._devpoll = select.devpoll()

        def fileno(self):
            return self._devpoll.fileno()

        def register(self, fileobj, events, data=None):
            key = super(DevpollSelector, self).register(fileobj, events, data)
            poll_events = 0
            if events & EVENT_READ:
                poll_events |= select.POLLIN
            if events & EVENT_WRITE:
                poll_events |= select.POLLOUT
            self._devpoll.register(key.fd, poll_events)
            return key

        def unregister(self, fileobj):
            key = super(DevpollSelector, self).unregister(fileobj)
            self._devpoll.unregister(key.fd)
            return key

        def _wrap_poll(self, timeout=None):
            """ Wrapper function for select.poll.poll() so that
            _syscall_wrapper can work with only seconds. """
            if timeout is not None:
                if timeout <= 0:
                    timeout = 0
                else:
                    # select.devpoll.poll() has a resolution of 1 millisecond,
                    # round away from zero to wait *at least* timeout seconds.
                    timeout = math.ceil(timeout * 1000)

            result = self._devpoll.poll(timeout)
            return result

        def select(self, timeout=None):
            ready = []
            fd_events = _syscall_wrapper(self._wrap_poll, True, timeout=timeout)
            for fd, event_mask in fd_events:
                events = 0
                if event_mask & ~select.POLLIN:
                    events |= EVENT_WRITE
                if event_mask & ~select.POLLOUT:
                    events |= EVENT_READ

                key = self._key_from_fd(fd)
                if key:
                    ready.append((key, events & key.events))

            return ready

        def close(self):
            self._devpoll.close()
            super(DevpollSelector, self).close()

    __all__.append('DevpollSelector')


if hasattr(select, "kqueue"):
    class KqueueSelector(BaseSelector):
        """ Kqueue / Kevent-based selector """
        def __init__(self):
            super(KqueueSelector, self).__init__()
            self._kqueue = select.kqueue()

        def fileno(self):
            return self._kqueue.fileno()

        def register(self, fileobj, events, data=None):
            key = super(KqueueSelector, self).register(fileobj, events, data)
            if events & EVENT_READ:
                kevent = select.kevent(key.fd,
                                       select.KQ_FILTER_READ,
                                       select.KQ_EV_ADD)

                _syscall_wrapper(self._wrap_control, False, [kevent], 0, 0)

            if events & EVENT_WRITE:
                kevent = select.kevent(key.fd,
                                       select.KQ_FILTER_WRITE,
                                       select.KQ_EV_ADD)

                _syscall_wrapper(self._wrap_control, False, [kevent], 0, 0)

            return key

        def unregister(self, fileobj):
            key = super(KqueueSelector, self).unregister(fileobj)
            if key.events & EVENT_READ:
                kevent = select.kevent(key.fd,
                                       select.KQ_FILTER_READ,
                                       select.KQ_EV_DELETE)
                try:
                    _syscall_wrapper(self._wrap_control, False, [kevent], 0, 0)
                except _ERROR_TYPES:
                    pass
            if key.events & EVENT_WRITE:
                kevent = select.kevent(key.fd,
                                       select.KQ_FILTER_WRITE,
                                       select.KQ_EV_DELETE)
                try:
                    _syscall_wrapper(self._wrap_control, False, [kevent], 0, 0)
                except _ERROR_TYPES:
                    pass

            return key

        def select(self, timeout=None):
            if timeout is not None:
                timeout = max(timeout, 0)

            max_events = len(self._fd_to_key) * 2
            ready_fds = {}

            kevent_list = _syscall_wrapper(self._wrap_control, True,
                                           None, max_events, timeout=timeout)

            for kevent in kevent_list:
                fd = kevent.ident
                event_mask = kevent.filter
                events = 0
                if event_mask == select.KQ_FILTER_READ:
                    events |= EVENT_READ
                if event_mask == select.KQ_FILTER_WRITE:
                    events |= EVENT_WRITE

                key = self._key_from_fd(fd)
                if key:
                    if key.fd not in ready_fds:
                        ready_fds[key.fd] = (key, events & key.events)
                    else:
                        old_events = ready_fds[key.fd][1]
                        ready_fds[key.fd] = (key, (events | old_events) & key.events)

            return list(ready_fds.values())

        def close(self):
            self._kqueue.close()
            super(KqueueSelector, self).close()

        def _wrap_control(self, changelist, max_events, timeout):
            return self._kqueue.control(changelist, max_events, timeout)

    __all__.append('KqueueSelector')


def _can_allocate(struct):
    """ Checks that select structs can be allocated by the underlying
    operating system, not just advertised by the select module. We don't
    check select() because we'll be hopeful that most platforms that
    don't have it available will not advertise it. (ie: GAE) """
    try:
        # select.poll() objects won't fail until used.
        if struct == 'poll':
            p = select.poll()
            p.poll(0)

        # All others will fail on allocation.
        else:
            getattr(select, struct)().close()
        return True
    except (OSError, AttributeError):
        return False


# Python 3.5 uses a more direct route to wrap system calls to increase speed.
if sys.version_info >= (3, 5):
    def _syscall_wrapper(func, _, *args, **kwargs):
        """ This is the short-circuit version of the below logic
        because in Python 3.5+ all selectors restart system calls. """
        return func(*args, **kwargs)
else:
    def _syscall_wrapper(func, recalc_timeout, *args, **kwargs):
        """ Wrapper function for syscalls that could fail due to EINTR.
        All functions should be retried if there is time left in the timeout
        in accordance with PEP 475. """
        timeout = kwargs.get("timeout", None)
        if timeout is None:
            expires = None
            recalc_timeout = False
        else:
            timeout = float(timeout)
            if timeout < 0.0:  # Timeout less than 0 treated as no timeout.
                expires = None
            else:
                expires = monotonic() + timeout

        if recalc_timeout and 'timeout' not in kwargs:
            raise ValueError(
                'Timeout must be in kwargs to be recalculated')

        result = _SYSCALL_SENTINEL
        while result is _SYSCALL_SENTINEL:
            try:
                result = func(*args, **kwargs)
            # OSError is thrown by select.select
            # IOError is thrown by select.epoll.poll
            # select.error is thrown by select.poll.poll
            # Aren't we thankful for Python 3.x rework for exceptions?
            except (OSError, IOError, select.error) as e:
                # select.error wasn't a subclass of OSError in the past.
                errcode = None
                if hasattr(e, 'errno') and e.errno is not None:
                    errcode = e.errno
                elif hasattr(e, 'args'):
                    errcode = e.args[0]

                # Also test for the Windows equivalent of EINTR.
                is_interrupt = (errcode == errno.EINTR or (hasattr(errno, 'WSAEINTR') and
                                                           errcode == errno.WSAEINTR))

                if is_interrupt:
                    if expires is not None:
                        current_time = monotonic()
                        if current_time > expires:
                            raise OSError(errno.ETIMEDOUT, 'Connection timed out')
                        if recalc_timeout:
                            kwargs["timeout"] = expires - current_time
                    continue
                raise
        return result


# Choose the best implementation, roughly:
# kqueue == devpoll == epoll > poll > select
# select() also can't accept a FD > FD_SETSIZE (usually around 1024)
def DefaultSelector():
    """ This function serves as a first call for DefaultSelector to
    detect if the select module is being monkey-patched incorrectly
    by eventlet, greenlet, and preserve proper behavior. """
    global _DEFAULT_SELECTOR
    if _DEFAULT_SELECTOR is None:
        if platform.python_implementation() == 'Jython':  # Platform-specific: Jython
            _DEFAULT_SELECTOR = JythonSelectSelector
        elif _can_allocate('kqueue'):
            _DEFAULT_SELECTOR = KqueueSelector
        elif _can_allocate('devpoll'):
            _DEFAULT_SELECTOR = DevpollSelector
        elif _can_allocate('epoll'):
            _DEFAULT_SELECTOR = EpollSelector
        elif _can_allocate('poll'):
            _DEFAULT_SELECTOR = PollSelector
        elif hasattr(select, 'select'):
            _DEFAULT_SELECTOR = SelectSelector
        else:  # Platform-specific: AppEngine
            raise RuntimeError('Platform does not have a selector.')
    return _DEFAULT_SELECTOR()
