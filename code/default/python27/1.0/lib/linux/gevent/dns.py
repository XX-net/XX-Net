# Copyright (c) 2010 Denis Bilenko. See LICENSE for details.
"""Libevent DNS API made synchronous.

The functions in this module match those in libevent as closely as possible
yet they return the result instead of passing it to a callback. The calling
greenlet remains blocked until the result is ready.
"""

from gevent import core
from gevent.hub import Waiter
from _socket import gaierror
from gevent.core import DNS_QUERY_NO_SEARCH as QUERY_NO_SEARCH


__all__ = ['DNSError',
           'resolve_ipv4',
           'resolve_ipv6',
           'resolve_reverse',
           'resolve_reverse_ipv6',
           'QUERY_NO_SEARCH']


# move from here into Hub.__init__ (once event_init() is move here as well)
core.dns_init()


class DNSError(gaierror):
    """A subclass of :class:`socket.gaierror` used by :mod:`evdns` functions to report errors.

    It uses evdns-specific error codes that are different from the standard socket errors.

        >>> resolve_ipv4('aaaaaaaaaaa')
        Traceback (most recent call last):
         ...
        DNSError: [Errno 3] name does not exist
    """

    def __init__(self, *args):
        if len(args) == 1:
            code = args[0]
            gaierror.__init__(self, code, core.dns_err_to_string(code))
        else:
            gaierror.__init__(self, *args)


def resolve_ipv4(name, flags=0):
    """Lookup an A record for a given *name*.
    To disable searching for this query, set *flags* to ``QUERY_NO_SEARCH``.

    Returns (ttl, list of packed IPs).

        >>> resolve_ipv4('www.python.org')
        (10000, ['R^\\xa4\\xa2'])
    """
    waiter = Waiter()
    core.dns_resolve_ipv4(name, flags, waiter.switch_args)
    result, _type, ttl, addrs = waiter.get()
    if result != core.DNS_ERR_NONE:
        raise DNSError(result)
    return ttl, addrs


def resolve_ipv6(name, flags=0):
    """Lookup an AAAA record for a given *name*.
    To disable searching for this query, set *flags* to ``QUERY_NO_SEARCH``.

    Returns (ttl, list of packed IPs).
    """
    waiter = Waiter()
    core.dns_resolve_ipv6(name, flags, waiter.switch_args)
    result, _type, ttl, addrs = waiter.get()
    if result != core.DNS_ERR_NONE:
        raise DNSError(result)
    return ttl, addrs


def resolve_reverse(packed_ip, flags=0):
    """Lookup a PTR record for a given IP address.
    To disable searching for this query, set *flags* to ``QUERY_NO_SEARCH``.

        >>> packed_ip = socket.inet_aton('82.94.164.162')
        >>> resolve_reverse(packed_ip)
        (10000, 'www.python.org')
    """
    waiter = Waiter()
    core.dns_resolve_reverse(packed_ip, flags, waiter.switch_args)
    result, _type, ttl, addr = waiter.get()
    if result != core.DNS_ERR_NONE:
        raise DNSError(result)
    return ttl, addr


def resolve_reverse_ipv6(packed_ip, flags=0):
    """Lookup a PTR record for a given IPv6 address.
    To disable searching for this query, set *flags* to ``QUERY_NO_SEARCH``.
    """
    waiter = Waiter()
    core.dns_resolve_reverse_ipv6(packed_ip, flags, waiter.switch_args)
    result, _type, ttl, addrs = waiter.get()
    if result != core.DNS_ERR_NONE:
        raise DNSError(result)
    return ttl, addrs
