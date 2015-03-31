# Copyright (c) 2011 Denis Bilenko. See LICENSE for details.
from __future__ import absolute_import
import os
import sys
from _socket import getservbyname, getaddrinfo, gaierror, error
from gevent.hub import Waiter, get_hub, string_types
from gevent.socket import AF_UNSPEC, AF_INET, AF_INET6, SOCK_STREAM, SOCK_DGRAM, SOCK_RAW, AI_NUMERICHOST, EAI_SERVICE, AI_PASSIVE
from gevent.ares import channel, InvalidIP


__all__ = ['Resolver']


class Resolver(object):

    ares_class = channel

    def __init__(self, hub=None, use_environ=True, **kwargs):
        if hub is None:
            hub = get_hub()
        self.hub = hub
        if use_environ:
            for key in os.environ.iterkeys():
                if key.startswith('GEVENTARES_'):
                    name = key[11:].lower()
                    if name:
                        value = os.environ[key]
                        kwargs.setdefault(name, value)
        self.ares = self.ares_class(hub.loop, **kwargs)
        self.pid = os.getpid()
        self.params = kwargs
        self.fork_watcher = hub.loop.fork(ref=False)
        self.fork_watcher.start(self._on_fork)

    def __repr__(self):
        return '<gevent.resolver_ares.Resolver at 0x%x ares=%r>' % (id(self), self.ares)

    def _on_fork(self):
        pid = os.getpid()
        if pid != self.pid:
            self.hub.loop.run_callback(self.ares.destroy)
            self.ares = self.ares_class(self.hub.loop, **self.params)
            self.pid = pid

    def close(self):
        if self.ares is not None:
            self.hub.loop.run_callback(self.ares.destroy)
            self.ares = None
        self.fork_watcher.stop()

    def gethostbyname(self, hostname, family=AF_INET):
        hostname = _resolve_special(hostname, family)
        return self.gethostbyname_ex(hostname, family)[-1][0]

    def gethostbyname_ex(self, hostname, family=AF_INET):
        if isinstance(hostname, unicode):
            hostname = hostname.encode('ascii')
        elif not isinstance(hostname, str):
            raise TypeError('Expected string, not %s' % type(hostname).__name__)

        while True:
            ares = self.ares
            try:
                waiter = Waiter(self.hub)
                ares.gethostbyname(waiter, hostname, family)
                result = waiter.get()
                if not result[-1]:
                    raise gaierror(-5, 'No address associated with hostname')
                return result
            except gaierror:
                if ares is self.ares:
                    raise
                # "self.ares is not ares" means channel was destroyed (because we were forked)

    def _lookup_port(self, port, socktype):
        socktypes = []
        if isinstance(port, string_types):
            try:
                port = int(port)
            except ValueError:
                try:
                    if socktype == 0:
                        origport = port
                        try:
                            port = getservbyname(port, 'tcp')
                            socktypes.append(SOCK_STREAM)
                        except error:
                            port = getservbyname(port, 'udp')
                            socktypes.append(SOCK_DGRAM)
                        else:
                            try:
                                if port == getservbyname(origport, 'udp'):
                                    socktypes.append(SOCK_DGRAM)
                            except error:
                                pass
                    elif socktype == SOCK_STREAM:
                        port = getservbyname(port, 'tcp')
                    elif socktype == SOCK_DGRAM:
                        port = getservbyname(port, 'udp')
                    else:
                        raise gaierror(EAI_SERVICE, 'Servname not supported for ai_socktype')
                except error:
                    ex = sys.exc_info()[1]
                    if 'not found' in str(ex):
                        raise gaierror(EAI_SERVICE, 'Servname not supported for ai_socktype')
                    else:
                        raise gaierror(str(ex))
                except UnicodeEncodeError:
                    raise error('Int or String expected')
        elif port is None:
            port = 0
        elif isinstance(port, int):
            pass
        else:
            raise error('Int or String expected')
        port = int(port % 65536)
        if not socktypes and socktype:
            socktypes.append(socktype)
        return port, socktypes

    def _getaddrinfo(self, host, port, family=0, socktype=0, proto=0, flags=0):
        if isinstance(host, unicode):
            host = host.encode('idna')
        elif not isinstance(host, str) or (flags & AI_NUMERICHOST):
            # this handles cases which do not require network access
            # 1) host is None
            # 2) host is of an invalid type
            # 3) AI_NUMERICHOST flag is set
            return getaddrinfo(host, port, family, socktype, proto, flags)
            # we also call _socket.getaddrinfo below if family is not one of AF_*

        port, socktypes = self._lookup_port(port, socktype)

        socktype_proto = [(SOCK_STREAM, 6), (SOCK_DGRAM, 17), (SOCK_RAW, 0)]
        if socktypes:
            socktype_proto = [(x, y) for (x, y) in socktype_proto if x in socktypes]
        if proto:
            socktype_proto = [(x, y) for (x, y) in socktype_proto if proto == y]

        ares = self.ares

        if family == AF_UNSPEC:
            values = Values(self.hub, 2)
            ares.gethostbyname(values, host, AF_INET)
            ares.gethostbyname(values, host, AF_INET6)
        elif family == AF_INET:
            values = Values(self.hub, 1)
            ares.gethostbyname(values, host, AF_INET)
        elif family == AF_INET6:
            values = Values(self.hub, 1)
            ares.gethostbyname(values, host, AF_INET6)
        else:
            raise gaierror(5, 'ai_family not supported: %r' % (family, ))

        values = values.get()
        if len(values) == 2 and values[0] == values[1]:
            values.pop()

        result = []
        result4 = []
        result6 = []

        for addrs in values:
            if addrs.family == AF_INET:
                for addr in addrs[-1]:
                    sockaddr = (addr, port)
                    for socktype, proto in socktype_proto:
                        result4.append((AF_INET, socktype, proto, '', sockaddr))
            elif addrs.family == AF_INET6:
                for addr in addrs[-1]:
                    if addr == '::1':
                        dest = result
                    else:
                        dest = result6
                    sockaddr = (addr, port, 0, 0)
                    for socktype, proto in socktype_proto:
                        dest.append((AF_INET6, socktype, proto, '', sockaddr))

        result += result4 + result6

        if not result:
            raise gaierror(-5, 'No address associated with hostname')

        return result

    def getaddrinfo(self, host, port, family=0, socktype=0, proto=0, flags=0):
        while True:
            ares = self.ares
            try:
                return self._getaddrinfo(host, port, family, socktype, proto, flags)
            except gaierror:
                if ares is self.ares:
                    raise

    def _gethostbyaddr(self, ip_address):
        if isinstance(ip_address, unicode):
            ip_address = ip_address.encode('ascii')
        elif not isinstance(ip_address, str):
            raise TypeError('Expected string, not %s' % type(ip_address).__name__)

        waiter = Waiter(self.hub)
        try:
            self.ares.gethostbyaddr(waiter, ip_address)
            return waiter.get()
        except InvalidIP:
            result = self._getaddrinfo(ip_address, None, family=AF_UNSPEC, socktype=SOCK_DGRAM)
            if not result:
                raise
            _ip_address = result[0][-1][0]
            if _ip_address == ip_address:
                raise
            waiter.clear()
            self.ares.gethostbyaddr(waiter, _ip_address)
            return waiter.get()

    def gethostbyaddr(self, ip_address):
        ip_address = _resolve_special(ip_address, AF_UNSPEC)
        while True:
            ares = self.ares
            try:
                return self._gethostbyaddr(ip_address)
            except gaierror:
                if ares is self.ares:
                    raise

    def _getnameinfo(self, sockaddr, flags):
        if not isinstance(flags, int):
            raise TypeError('an integer is required')
        if not isinstance(sockaddr, tuple):
            raise TypeError('getnameinfo() argument 1 must be a tuple')

        address = sockaddr[0]
        if isinstance(address, unicode):
            address = address.encode('ascii')

        if not isinstance(address, str):
            raise TypeError('sockaddr[0] must be a string, not %s' % type(address).__name__)

        port = sockaddr[1]
        if not isinstance(port, int):
            raise TypeError('port must be an integer, not %s' % type(port))

        waiter = Waiter(self.hub)
        result = self._getaddrinfo(address, str(sockaddr[1]), family=AF_UNSPEC, socktype=SOCK_DGRAM)
        if not result:
            raise
        elif len(result) != 1:
            raise error('sockaddr resolved to multiple addresses')
        family, socktype, proto, name, address = result[0]

        if family == AF_INET:
            if len(sockaddr) != 2:
                raise error("IPv4 sockaddr must be 2 tuple")
        elif family == AF_INET6:
            address = address[:2] + sockaddr[2:]

        self.ares.getnameinfo(waiter, address, flags)
        node, service = waiter.get()
        if service is None:
            service = '0'
        return node, service

    def getnameinfo(self, sockaddr, flags):
        while True:
            ares = self.ares
            try:
                return self._getnameinfo(sockaddr, flags)
            except gaierror:
                if ares is self.ares:
                    raise


class Values(object):
    # helper to collect multiple values; ignore errors unless nothing has succeeded
    # QQQ could probably be moved somewhere - hub.py?

    __slots__ = ['count', 'values', 'error', 'waiter']

    def __init__(self, hub, count):
        self.count = count
        self.values = []
        self.error = None
        self.waiter = Waiter(hub)

    def __call__(self, source):
        self.count -= 1
        if source.exception is None:
            self.values.append(source.value)
        else:
            self.error = source.exception
        if self.count <= 0:
            self.waiter.switch()

    def get(self):
        self.waiter.get()
        if self.values:
            return self.values
        else:
            raise self.error


def _resolve_special(hostname, family):
    if hostname == '':
        result = getaddrinfo(None, 0, family, SOCK_DGRAM, 0, AI_PASSIVE)
        if len(result) != 1:
            raise error('wildcard resolved to multiple address')
        return result[0][4][0]
    return hostname
