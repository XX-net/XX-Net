"""Base class for implementing servers"""
# Copyright (c) 2009-2012 Denis Bilenko. See LICENSE for details.
import sys
import _socket
import errno
from gevent.greenlet import Greenlet, getfuncname
from gevent.event import Event
from gevent.hub import string_types, integer_types, get_hub


__all__ = ['BaseServer']


class BaseServer(object):
    """An abstract base class that implements some common functionality for the servers in gevent.

    *listener* can either be an address that the server should bind on or a :class:`gevent.socket.socket`
    instance that is already bound (and put into listening mode in case of TCP socket).

    *spawn*, if provided, is called to create a new greenlet to run the handler. By default, :func:`gevent.spawn` is used.

    Possible values for *spawn*:

    * a :class:`gevent.pool.Pool` instance -- *handle* will be executed
      using :meth:`Pool.spawn` method only if the pool is not full.
      While it is full, all the connection are dropped;
    * :func:`gevent.spawn_raw` -- *handle* will be executed in a raw
      greenlet which have a little less overhead then :class:`gevent.Greenlet` instances spawned by default;
    * ``None`` -- *handle* will be executed right away, in the :class:`Hub` greenlet.
      *handle* cannot use any blocking functions as it means switching to the :class:`Hub`.
    * an integer -- a shortcut for ``gevent.pool.Pool(integer)``
    """
    # the number of seconds to sleep in case there was an error in accept() call
    # for consecutive errors the delay will double until it reaches max_delay
    # when accept() finally succeeds the delay will be reset to min_delay again
    min_delay = 0.01
    max_delay = 1

    # Sets the maximum number of consecutive accepts that a process may perform on
    # a single wake up. High values give higher priority to high connection rates,
    # while lower values give higher priority to already established connections.
    # Default is 100. Note, that in case of multiple working processes on the same
    # listening value, it should be set to a lower value. (pywsgi.WSGIServer sets it
    # to 1 when environ["wsgi.multiprocess"] is true)
    max_accept = 100

    _spawn = Greenlet.spawn

    # the default timeout that we wait for the client connections to close in stop()
    stop_timeout = 1

    fatal_errors = (errno.EBADF, errno.EINVAL, errno.ENOTSOCK)

    def __init__(self, listener, handle=None, spawn='default'):
        self._stop_event = Event()
        self._stop_event.set()
        self._watcher = None
        self._timer = None
        self.pool = None
        try:
            self.set_listener(listener)
            self.set_spawn(spawn)
            self.set_handle(handle)
            self.delay = self.min_delay
            self.loop = get_hub().loop
            if self.max_accept < 1:
                raise ValueError('max_accept must be positive int: %r' % (self.max_accept, ))
        except:
            self.close()
            raise

    def set_listener(self, listener):
        if hasattr(listener, 'accept'):
            if hasattr(listener, 'do_handshake'):
                raise TypeError('Expected a regular socket, not SSLSocket: %r' % (listener, ))
            self.family = listener.family
            self.address = listener.getsockname()
            self.socket = listener
        else:
            self.family, self.address = parse_address(listener)

    def set_spawn(self, spawn):
        if spawn == 'default':
            self.pool = None
            self._spawn = self._spawn
        elif hasattr(spawn, 'spawn'):
            self.pool = spawn
            self._spawn = spawn.spawn
        elif isinstance(spawn, (int, long)):
            from gevent.pool import Pool
            self.pool = Pool(spawn)
            self._spawn = self.pool.spawn
        else:
            self.pool = None
            self._spawn = spawn
        if hasattr(self.pool, 'full'):
            self.full = self.pool.full
        if self.pool is not None:
            self.pool._semaphore.rawlink(self._start_accepting_if_started)

    def set_handle(self, handle):
        if handle is not None:
            self.handle = handle
        if hasattr(self, 'handle'):
            self._handle = self.handle
        else:
            raise TypeError("'handle' must be provided")

    def _start_accepting_if_started(self, _event=None):
        if self.started:
            self.start_accepting()

    def start_accepting(self):
        if self._watcher is None:
            # just stop watcher without creating a new one?
            self._watcher = self.loop.io(self.socket.fileno(), 1)
            self._watcher.start(self._do_read)

    def stop_accepting(self):
        if self._watcher is not None:
            self._watcher.stop()
            self._watcher = None
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def do_handle(self, *args):
        spawn = self._spawn
        if spawn is None:
            self._handle(*args)
        else:
            spawn(self._handle, *args)

    def _do_read(self):
        for _ in xrange(self.max_accept):
            if self.full():
                self.stop_accepting()
                return
            try:
                args = self.do_read()
                self.delay = self.min_delay
                if not args:
                    return
            except:
                self.loop.handle_error(self, *sys.exc_info())
                ex = sys.exc_info()[1]
                if self.is_fatal_error(ex):
                    self.close()
                    sys.stderr.write('ERROR: %s failed with %s\n' % (self, str(ex) or repr(ex)))
                    return
                if self.delay >= 0:
                    self.stop_accepting()
                    self._timer = self.loop.timer(self.delay)
                    self._timer.start(self._start_accepting_if_started)
                    self.delay = min(self.max_delay, self.delay * 2)
                break
            else:
                try:
                    self.do_handle(*args)
                except:
                    self.loop.handle_error((args[1:], self), *sys.exc_info())
                    if self.delay >= 0:
                        self.stop_accepting()
                        self._timer = self.loop.timer(self.delay)
                        self._timer.start(self._start_accepting_if_started)
                        self.delay = min(self.max_delay, self.delay * 2)
                    break

    def full(self):
        return False

    def __repr__(self):
        return '<%s at %s %s>' % (type(self).__name__, hex(id(self)), self._formatinfo())

    def __str__(self):
        return '<%s %s>' % (type(self).__name__, self._formatinfo())

    def _formatinfo(self):
        if hasattr(self, 'socket'):
            try:
                fileno = self.socket.fileno()
            except Exception:
                ex = sys.exc_info()[1]
                fileno = str(ex)
            result = 'fileno=%s ' % fileno
        else:
            result = ''
        try:
            if isinstance(self.address, tuple) and len(self.address) == 2:
                result += 'address=%s:%s' % self.address
            else:
                result += 'address=%s' % (self.address, )
        except Exception:
            ex = sys.exc_info()[1]
            result += str(ex) or '<error>'
        try:
            handle = getfuncname(self.__dict__['handle'])
        except Exception:
            handle = None
        if handle is not None:
            result += ' handle=' + handle
        return result

    @property
    def server_host(self):
        """IP address that the server is bound to (string)."""
        if isinstance(self.address, tuple):
            return self.address[0]

    @property
    def server_port(self):
        """Port that the server is bound to (an integer)."""
        if isinstance(self.address, tuple):
            return self.address[1]

    def init_socket(self):
        """If the user initialized the server with an address rather than socket,
        then this function will create a socket, bind it and put it into listening mode.

        It is not supposed to be called by the user, it is called by :meth:`start` before starting
        the accept loop."""
        pass

    @property
    def started(self):
        return not self._stop_event.is_set()

    def start(self):
        """Start accepting the connections.

        If an address was provided in the constructor, then also create a socket,
        bind it and put it into the listening mode.
        """
        self.init_socket()
        self._stop_event.clear()
        try:
            self.start_accepting()
        except:
            self.close()
            raise

    def close(self):
        """Close the listener socket and stop accepting."""
        self._stop_event.set()
        try:
            self.stop_accepting()
        finally:
            try:
                self.socket.close()
            except Exception:
                pass
            finally:
                self.__dict__.pop('socket', None)
                self.__dict__.pop('handle', None)
                self.__dict__.pop('_handle', None)
                self.__dict__.pop('_spawn', None)
                self.__dict__.pop('full', None)
                if self.pool is not None:
                    self.pool._semaphore.unlink(self._start_accepting_if_started)

    @property
    def closed(self):
        return not hasattr(self, 'socket')

    def stop(self, timeout=None):
        """Stop accepting the connections and close the listening socket.

        If the server uses a pool to spawn the requests, then :meth:`stop` also waits
        for all the handlers to exit. If there are still handlers executing after *timeout*
        has expired (default 1 second), then the currently running handlers in the pool are killed."""
        self.close()
        if timeout is None:
            timeout = self.stop_timeout
        if self.pool:
            self.pool.join(timeout=timeout)
            self.pool.kill(block=True, timeout=1)

    def serve_forever(self, stop_timeout=None):
        """Start the server if it hasn't been already started and wait until it's stopped."""
        # add test that serve_forever exists on stop()
        if not self.started:
            self.start()
        try:
            self._stop_event.wait()
        finally:
            Greenlet.spawn(self.stop, timeout=stop_timeout).join()

    def is_fatal_error(self, ex):
        return isinstance(ex, _socket.error) and ex[0] in self.fatal_errors


def _extract_family(host):
    if host.startswith('[') and host.endswith(']'):
        host = host[1:-1]
        return _socket.AF_INET6, host
    return _socket.AF_INET, host


def _parse_address(address):
    if isinstance(address, tuple):
        if ':' in address[0]:
            return _socket.AF_INET6, address
        return _socket.AF_INET, address
    elif isinstance(address, string_types):
        if ':' in address:
            host, port = address.rsplit(':', 1)
            family, host = _extract_family(host)
            if host == '*':
                host = ''
            return family, (host, int(port))
        else:
            return _socket.AF_INET, ('', int(address))
    elif isinstance(address, integer_types):
        return _socket.AF_INET, ('', int(address))
    else:
        raise TypeError('Expected tuple or string, got %s' % type(address))


def parse_address(address):
    try:
        return _parse_address(address)
    except ValueError:
        raise ValueError('Failed to parse address %r: %s' % (address, sys.exc_info()[1]))
