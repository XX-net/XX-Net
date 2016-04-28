# Copyright (c) 2009-2010 Denis Bilenko. See LICENSE for details.
"""Make the standard library cooperative.

The functions in this module patch parts of the standard library with compatible cooperative counterparts
from :mod:`gevent` package.

To patch an individual module call the corresponding ``patch_*`` function. For example, to patch
socket module only, call :func:`patch_socket`. To patch all default modules, call ``gevent.monkey.patch_all()``.

Monkey can also patch thread and threading to become greenlet-based. So :func:`thread.start_new_thread`
starts a new greenlet instead and :class:`threading.local` becomes a greenlet-local storage.

Monkey patches:

* :mod:`socket` module -- :func:`patch_socket`

  - :class:`socket`
  - :class:`SocketType`
  - :func:`socketpair`
  - :func:`fromfd`
  - :func:`ssl` and :class:`sslerror`
  - :func:`socket.getaddrinfo`
  - :func:`socket.gethostbyname`
  - It is possible to disable dns patching by passing ``dns=False`` to :func:`patch_socket` of :func:`patch_all`
  - If ssl is not available (Python < 2.6 without ``ssl`` and ``PyOpenSSL`` packages installed) then :func:`ssl` is removed from the target :mod:`socket` module.

* :mod:`ssl` module -- :func:`patch_ssl`

  - :class:`SSLSocket`
  - :func:`wrap_socket`
  - :func:`get_server_certificate`
  - :func:`sslwrap_simple`

* :mod:`os` module -- :func:`patch_os`

  - :func:`fork`

* :mod:`time` module -- :func:`patch_time`

  - :func:`time`

* :mod:`select` module -- :func:`patch_select`

  - :func:`select`
  - Removes polling mechanisms that :mod:`gevent.select` does not simulate: poll, epoll, kqueue, kevent

* :mod:`thread` and :mod:`threading` modules -- :func:`patch_thread`

  - Become greenlet-based.
  - :func:`get_ident`
  - :func:`start_new_thread`
  - :class:`LockType`
  - :func:`allocate_lock`
  - :func:`exit`
  - :func:`stack_size`
  - thread-local storage becomes greenlet-local storage
"""

__all__ = ['patch_all',
           'patch_socket',
           'patch_ssl',
           'patch_os',
           'patch_time',
           'patch_select',
           'patch_thread']


def patch_os():
    """Replace :func:`os.fork` with :func:`gevent.fork`."""
    try:
        from gevent.hub import fork
    except ImportError:
        return
    import os
    os.fork = fork


def patch_time():
    """Replace :func:`time.sleep` with :func:`gevent.sleep`."""
    from gevent.hub import sleep
    _time = __import__('time')
    _time.sleep = sleep


def patch_thread(threading=True, _threading_local=True):
    """Replace the standard :mod:`thread` module to make it greenlet-based.
    If *threading* is true (the default), also patch ``threading.local``.
    If *_threading_local* is true (the default), also patch ``_threading_local.local``.
    """
    from gevent import thread as green_thread
    thread = __import__('thread')
    if thread.exit is not green_thread.exit:
        thread.get_ident = green_thread.get_ident
        thread.start_new_thread = green_thread.start_new_thread
        thread.LockType = green_thread.LockType
        thread.allocate_lock = green_thread.allocate_lock
        thread.exit = green_thread.exit
        if hasattr(green_thread, 'stack_size'):
            thread.stack_size = green_thread.stack_size
        from gevent.local import local
        thread._local = local
        if threading:
            threading = __import__('threading')
            threading.local = local
            threading._start_new_thread = green_thread.start_new_thread
            threading._allocate_lock = green_thread.allocate_lock
            threading.Lock = green_thread.allocate_lock
            threading._get_ident = green_thread.get_ident
        if _threading_local:
            _threading_local = __import__('_threading_local')
            _threading_local.local = local


def patch_socket(dns=True, aggressive=True):
    """Replace the standard socket object with gevent's cooperative sockets.

    If *dns* is true, also patch dns functions in :mod:`socket`.
    """
    from gevent import socket
    _socket = __import__('socket')
    _socket.socket = socket.socket
    _socket.SocketType = socket.SocketType
    _socket.create_connection = socket.create_connection
    if hasattr(socket, 'socketpair'):
        _socket.socketpair = socket.socketpair
    if hasattr(socket, 'fromfd'):
        _socket.fromfd = socket.fromfd
    try:
        from gevent.socket import ssl, sslerror
        _socket.ssl = ssl
        _socket.sslerror = sslerror
    except ImportError:
        if aggressive:
            try:
                del _socket.ssl
            except AttributeError:
                pass
    if dns:
        patch_dns()


def patch_dns():
    from gevent.socket import gethostbyname, getaddrinfo
    _socket = __import__('socket')
    _socket.getaddrinfo = getaddrinfo
    _socket.gethostbyname = gethostbyname


def patch_ssl():
    try:
        _ssl = __import__('ssl')
    except ImportError:
        return
    from gevent.ssl import SSLSocket, wrap_socket, get_server_certificate, sslwrap_simple
    _ssl.SSLSocket = SSLSocket
    _ssl.wrap_socket = wrap_socket
    _ssl.get_server_certificate = get_server_certificate
    _ssl.sslwrap_simple = sslwrap_simple


def patch_select(aggressive=False):
    """Replace :func:`select.select` with :func:`gevent.select.select`.

    If aggressive is true (the default), also remove other blocking functions the :mod:`select`.
    """
    from gevent.select import select
    _select = __import__('select')
    globals()['_select_select'] = _select.select
    _select.select = select
    if aggressive:
        # since these are blocking and don't work with the libevent's event loop
        # we're removing them here. This makes some other modules (e.g. asyncore)
        # non-blocking, as they use select that we provide when none of these are available.
        _select.__dict__.pop('poll', None)
        _select.__dict__.pop('epoll', None)
        _select.__dict__.pop('kqueue', None)
        _select.__dict__.pop('kevent', None)


def patch_httplib():
    httplib = __import__('httplib')
    from gevent.httplib import HTTPConnection, HTTPSConnection
    httplib.HTTPConnection = HTTPConnection
    httplib.HTTPSConnection = HTTPSConnection


def patch_all(socket=True, dns=True, time=True, select=True, thread=True, os=True, ssl=True, httplib=False, aggressive=True):
    """Do all of the default monkey patching (calls every other function in this module."""
    # order is important
    if os:
        patch_os()
    if time:
        patch_time()
    if thread:
        patch_thread()
    if socket:
        patch_socket(dns=dns, aggressive=aggressive)
    if select:
        patch_select(aggressive=aggressive)
    if ssl:
        patch_ssl()
    if httplib:
        patch_httplib()


if __name__ == '__main__':
    import sys
    modules = [x.replace('patch_', '') for x in globals().keys() if x.startswith('patch_') and x != 'patch_all']
    script_help = """gevent.monkey - monkey patch the standard modules to use gevent.

USAGE: python -m gevent.monkey [MONKEY OPTIONS] script [SCRIPT OPTIONS]

If no OPTIONS present, monkey patches all the modules it can patch.
You can exclude a module with --no-module, e.g. --no-thread. You can
specify a module to patch with --module, e.g. --socket. In the latter
case only the modules specified on the command line will be patched.

MONKEY OPTIONS: --verbose %s""" % ', '.join('--[no-]%s' % m for m in modules)
    args = {}
    argv = sys.argv[1:]
    verbose = False
    while argv and argv[0].startswith('--'):
        option = argv[0][2:]
        if option == 'verbose':
            verbose = True
        elif option.startswith('no-') and option.replace('no-', '') in modules:
            args[option[3:]] = False
        elif option not in modules:
            args[option] = True
        else:
            sys.exit(script_help + '\n\n' + 'Cannot patch %r' % option)
        del argv[0]
        # TODO: break on --
    if verbose:
        import pprint
        import os
        print 'gevent.monkey.patch_all(%s)' % ', '.join('%s=%s' % item for item in args.items())
        print 'sys.version=%s' % (sys.version.strip().replace('\n', ' '), )
        print 'sys.path=%s' % pprint.pformat(sys.path)
        print 'sys.modules=%s' % pprint.pformat(sorted(sys.modules.keys()))
        print 'cwd=%s' % os.getcwd()

    patch_all(**args)
    if argv:
        sys.argv = argv
        __package__ = None
        execfile(sys.argv[0])
    else:
        print script_help
