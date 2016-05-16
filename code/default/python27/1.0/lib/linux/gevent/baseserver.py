"""Base class for implementing servers"""
# Copyright (c) 2009-2010 Denis Bilenko. See LICENSE for details.
from gevent.greenlet import Greenlet, getfuncname
from gevent.event import Event
import _socket


__all__ = ['BaseServer']


class BaseServer(object):
    """An abstract base class that implements some common functionality for the servers in gevent.

    *listener* can either be an address that the server should bind on or a :class:`gevent.socket.socket`
    instance that is already bound and put into listening mode. In the former case, *backlog* argument specifies the
    length of the backlog queue. If not provided, the default (256) is used.

    *spawn*, if provided, is called to create a new greenlet to run the handler. By default, :func:`gevent.spawn` is used.

    Possible values for *spawn*:

    * a :class:`gevent.pool.Pool` instance -- *handle* will be executed using :meth:`Pool.spawn` method only if the
      pool is not full. While it is full, all the connection are dropped;
    * :func:`gevent.spawn_raw` -- *handle* will be executed in a raw greenlet which have a little less overhead then
      :class:`gevent.Greenlet` instances spawned by default;
    * ``None`` -- *handle* will be executed right away, in the :class:`Hub` greenlet. *handle* cannot use any blocking
      functions as it means switching to the :class:`Hub`.
    * an integer -- a shortcut for ``gevent.pool.Pool(integer)``
    """

    _spawn = Greenlet.spawn

    # the default backlog to use if none was provided in __init__
    backlog = 256

    reuse_addr = 1

    # the default timeout that we wait for the client connections to close in stop()
    stop_timeout = 1

    def __init__(self, listener, handle=None, backlog=None, spawn='default'):
        self._stopped_event = Event()
        self.set_listener(listener, backlog=backlog)
        self.set_spawn(spawn)
        self.set_handle(handle)
        self.started = None

    def set_listener(self, listener, backlog=None):
        if hasattr(listener, 'accept'):
            if hasattr(listener, 'do_handshake'):
                raise TypeError('Expected a regular socket, not SSLSocket: %r' % (listener, ))
            if backlog is not None:
                raise TypeError('backlog must be None when a socket instance is passed')
            self.address = listener.getsockname()
            self.socket = listener
        else:
            if not isinstance(listener, tuple):
                raise TypeError('Expected a socket instance or an address (tuple of 2 elements): %r' % (listener, ))
            if backlog is not None:
                self.backlog = backlog
            self.address = listener

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

    def set_handle(self, handle):
        if handle is not None:
            self.handle = handle

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
            except Exception, ex:
                fileno = str(ex)
            result = 'fileno=%s ' % fileno
        else:
            result = ''
        try:
            if isinstance(self.address, tuple) and len(self.address) == 2:
                result += 'address=%s:%s' % self.address
            else:
                result += 'address=%s' % (self.address, )
        except Exception, ex:
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

    def pre_start(self):
        """If the user initialized the server with an address rather than socket,
        then this function will create a socket, bind it and put it into listening mode.

        It is not supposed to be called by the user, it is called by :meth:`start` before starting
        the accept loop."""
        if not hasattr(self, 'socket'):
            self.socket = _tcp_listener(self.address, backlog=self.backlog, reuse_addr=self.reuse_addr)
            self.address = self.socket.getsockname()
        self._stopped_event.clear()

    def start(self):
        """Start accepting the connections.

        If an address was provided in the constructor, then also create a socket, bind it and put it into the listening mode.
        """
        assert not self.started, '%s already started' % self.__class__.__name__
        self.pre_start()
        self.started = True
        try:
            self.start_accepting()
        except:
            self.kill()
            raise

    def kill(self):
        """Close the listener socket and stop accepting."""
        self.started = False
        try:
            self.stop_accepting()
        finally:
            try:
                self.socket.close()
            except Exception:
                pass
            self.__dict__.pop('socket', None)
            self.__dict__.pop('handle', None)

    def stop(self, timeout=None):
        """Stop accepting the connections and close the listening socket.

        If the server uses a pool to spawn the requests, then :meth:`stop` also waits
        for all the handlers to exit. If there are still handlers executing after *timeout*
        has expired (default 1 second), then the currently running handlers in the pool are killed."""
        self.kill()
        if timeout is None:
            timeout = self.stop_timeout
        if self.pool:
            self.pool.join(timeout=timeout)
            self.pool.kill(block=True, timeout=1)
        self.post_stop()

    def post_stop(self):
        self._stopped_event.set()

    def serve_forever(self, stop_timeout=None):
        """Start the server if it hasn't been already started and wait until it's stopped."""
        # add test that serve_forever exists on stop()
        if not self.started:
            self.start()
        try:
            self._stopped_event.wait()
        except:
            self.stop(timeout=stop_timeout)
            raise


def _tcp_listener(address, backlog=50, reuse_addr=None):
    """A shortcut to create a TCP socket, bind it and put it into listening state.

    The difference from :meth:`gevent.socket.tcp_listener` is that this function returns
    an unwrapped :class:`_socket.socket` instance.
    """
    sock = _socket.socket()
    if reuse_addr is not None:
        sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, reuse_addr)
    try:
        sock.bind(address)
    except _socket.error, ex:
        strerror = getattr(ex, 'strerror', None)
        if strerror is not None:
            ex.strerror = strerror + ': ' + repr(address)
        raise
    sock.listen(backlog)
    sock.setblocking(0)
    return sock
