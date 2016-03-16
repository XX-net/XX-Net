#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#




"""Socket Module.

This file is intended to provide the equivalent of
python/Modules/socketmodule.c rather than python/Lib/socket.py which amongst
other things adds a buffered file-like interface.
"""














import errno
import os
import re
import struct
import time
import weakref

from google.appengine.api import apiproxy_stub_map
from google.appengine.api.remote_socket import remote_socket_service_pb

from google.appengine.api.remote_socket._remote_socket_addr import *

from google.appengine.api.remote_socket._remote_socket_error import *
from google.appengine.runtime import apiproxy_errors

has_ipv6 = True

SOCK_STREAM = 1
SOCK_DGRAM = 2

SOMAXCONN = 128

MSG_PEEK = 2
MSG_WAITALL = 256

IPPROTO_IP = 0
IPPROTO_ICMP = 1
IPPROTO_TCP = 6
IPPROTO_UDP = 17

IPPORT_RESERVED = 1024
IPPORT_USERRESERVED = 5000

INADDR_ANY = 0x00000000
INADDR_BROADCAST = 0xffffffff
INADDR_LOOPBACK = 0x7f000001
INADDR_NONE = 0xffffffff

(AI_PASSIVE, AI_CANONNAME, AI_NUMERICHOST, AI_NUMERICSERV, AI_V4MAPPED, AI_ALL,
 AI_ADDRCONFIG) = map(lambda x: 1 << x, range(7))

RemoteSocketServiceError = remote_socket_service_pb.RemoteSocketServiceError


def _ImportSymbols(protobuf, symbols, prefix='SOCKET_'):
  """Import symbols defined in a protobuf into the global namespace."""
  for sym in symbols:
    globals()[sym] = getattr(protobuf, prefix + sym)


_ImportSymbols(remote_socket_service_pb.ResolveReply, (
    'EAI_ADDRFAMILY', 'EAI_AGAIN', 'EAI_BADFLAGS', 'EAI_FAIL', 'EAI_FAMILY',
    'EAI_MEMORY', 'EAI_NODATA', 'EAI_NONAME', 'EAI_SERVICE', 'EAI_SOCKTYPE',
    'EAI_SYSTEM', 'EAI_BADHINTS', 'EAI_PROTOCOL', 'EAI_OVERFLOW', 'EAI_MAX'))

_ImportSymbols(remote_socket_service_pb.ShutDownRequest, (
    'SHUT_RD', 'SHUT_WR', 'SHUT_RDWR'))

_ImportSymbols(remote_socket_service_pb.SocketOption, (

    'SOL_SOCKET', 'SOL_IP', 'SOL_TCP', 'SOL_UDP',

    'SO_DEBUG', 'SO_REUSEADDR', 'SO_TYPE', 'SO_ERROR', 'SO_DONTROUTE',
    'SO_BROADCAST', 'SO_SNDBUF', 'SO_RCVBUF', 'SO_KEEPALIVE',

    'IP_TOS', 'IP_TTL', 'IP_HDRINCL', 'IP_OPTIONS',

    'TCP_NODELAY', 'TCP_MAXSEG', 'TCP_CORK', 'TCP_KEEPIDLE', 'TCP_KEEPINTVL',
    'TCP_KEEPCNT', 'TCP_SYNCNT', 'TCP_LINGER2', 'TCP_DEFER_ACCEPT',
    'TCP_WINDOW_CLAMP', 'TCP_INFO', 'TCP_QUICKACK'))

_ImportSymbols(remote_socket_service_pb.PollEvent, (
    'POLLNONE', 'POLLIN', 'POLLPRI', 'POLLOUT', 'POLLERR', 'POLLHUP',
    'POLLNVAL', 'POLLRDNORM', 'POLLRDBAND', 'POLLWRNORM', 'POLLWRBAND',
    'POLLMSG', 'POLLREMOVE', 'POLLRDHUP'))


_GLOBAL_DEFAULT_TIMEOUT = object()
_GLOBAL_TIMEOUT_VALUE = -1.0

_GLOBAL_SOCKET_NEXT_FILENO = 2**32
_GLOBAL_SOCKET_MAP = weakref.WeakValueDictionary()

_SERVICES = {
    'ftp': [('tcp', 21), ('udp', 21)],
    'ftp-data': [('tcp', 20), ('udp', 20)],
    'http': [('tcp', 80), ('udp', 80)],
    'pop3': [('tcp', 110), ('udp', 110)],
    'pop3s': [('tcp', 995), ('udp', 995)],
    'smtp': [('tcp', 25), ('udp', 25)],
    'telnet': [('tcp', 23), ('udp', 23)],
    'www': [('tcp', 80), ('udp', 80)],
    'www-http': [('tcp', 80), ('udp', 80)],
}

_ERROR_MAP = {
    RemoteSocketServiceError.PERMISSION_DENIED: errno.EACCES,
    RemoteSocketServiceError.INVALID_REQUEST: errno.EINVAL,
    RemoteSocketServiceError.SOCKET_CLOSED: errno.EPIPE,
}

_SOCK_PROTO_MAP = {
    (SOCK_STREAM, IPPROTO_TCP): 'tcp',
    (SOCK_DGRAM, IPPROTO_UDP): 'udp',
}

_ADDRESS_FAMILY_MAP = {
    AF_INET: remote_socket_service_pb.CreateSocketRequest.IPv4,
    AF_INET6: remote_socket_service_pb.CreateSocketRequest.IPv6,
}

_ADDRESS_FAMILY_LENGTH_MAP = {
    4: AF_INET,
    16: AF_INET6,
}


class SocketApiNotImplementedError(NotImplementedError, error):
  pass


def _SystemExceptionFromAppError(e):
  app_error = e.application_error
  if app_error in (RemoteSocketServiceError.SYSTEM_ERROR,
                   RemoteSocketServiceError.GAI_ERROR):
    error_detail = RemoteSocketServiceError()
    try:
      error_detail.ParseASCII(e.error_detail)
    except NotImplementedError:


      m = re.match(
          r'system_error:\s*(-?\d+)\s*,?\s*error_detail:\s*"([^"]*)"\s*',
          e.error_detail)
      if m:
        error_detail.set_system_error(int(m.group(1)))
        error_detail.set_error_detail(m.group(2))
      else:
        error_detail.set_system_error(-1)
        error_detail.set_error_detail(e.error_detail)
    if app_error == RemoteSocketServiceError.SYSTEM_ERROR:
      return error(error_detail.system_error(),
                   (error_detail.error_detail() or
                    os.strerror(error_detail.system_error())))
    elif app_error == RemoteSocketServiceError.GAI_ERROR:
      return gaierror(error_detail.system_error(),
                      error_detail.error_detail())
  elif app_error in _ERROR_MAP:
    return error(_ERROR_MAP[app_error], os.strerror(_ERROR_MAP[app_error]))
  else:
    return e


def _IsAddr(family, addr):
  try:
    inet_pton(family, addr)
  except Exception:
    return False
  return True




def _Resolve(name, families, use_dns=True, canonical=False):
  for family in families:
    if _IsAddr(family, name):

      return (name, [], [name])


  if use_dns:
    canon, aliases, addresses = _ResolveName(name, families)
    if addresses:
      return (canon, aliases, addresses)

  raise gaierror(EAI_NONAME, 'nodename nor servname provided, or not known')




def _ResolveName(name, address_families=(AF_INET6, AF_INET)):
  request = remote_socket_service_pb.ResolveRequest()
  request.set_name(name)
  for af in address_families:
    request.add_address_families(_ADDRESS_FAMILY_MAP[af])

  reply = remote_socket_service_pb.ResolveReply()

  try:
    apiproxy_stub_map.MakeSyncCall('remote_socket', 'Resolve', request, reply)
  except apiproxy_errors.ApplicationError, e:
    raise _SystemExceptionFromAppError(e)

  canonical_name = reply.canonical_name()
  aliases = reply.aliases_list()
  addresses = [inet_ntop(_ADDRESS_FAMILY_LENGTH_MAP[len(a)], a)
               for a in reply.packed_address_list()]
  return canonical_name, aliases, addresses


def _ResolveService(servicename, protocolname, numeric_only=False):
  try:
    return (protocolname, int(servicename))
  except ValueError:
    pass

  if not numeric_only:
    for protocol, port in _SERVICES.get(servicename, []):
      if not protocolname or protocol == protocolname:
        return (protocol, port)

  raise gaierror(EAI_SERVICE, '')


def gethostbyname(host):
  """gethostbyname(host) -> address

  Return the IP address (a string of the form '255.255.255.255') for a host.
  """
  return _Resolve(host, [AF_INET])[2][0]


def gethostbyname_ex(host):
  """gethostbyname_ex(host) -> (name, aliaslist, addresslist)

  Return the true host name, a list of aliases, and a list of IP addresses,
  for a host.  The host argument is a string giving a host name or IP number.
  """
  return _Resolve(host, [AF_INET])


def gethostbyaddr(addr):

  raise SocketApiNotImplementedError()


def gethostname():
  """gethostname() -> string

  Return the current host name.
  """
  return os.environ.get('HTTP_HOST', 'www.appspot.com')


def getprotobyname(protocolname):
  raise SocketApiNotImplementedError()


def getservbyname(servicename, protocolname=None):
  """getservbyname(servicename[, protocolname]) -> integer

  Return a port number from a service name and protocol name.
  The optional protocol name, if given, should be 'tcp' or 'udp',
  otherwise any protocol will match.
  """
  return _ResolveService(servicename, protocolname)[1]


def getservbyport(portnumber, protocolname=0):
  raise SocketApiNotImplementedError()




def getaddrinfo(host, service, family=AF_UNSPEC, socktype=0, proto=0, flags=0):
  """getaddrinfo(host, port [, family, socktype, proto, flags])
      -> list of (family, socktype, proto, canonname, sockaddr)

  Resolve host and port into addrinfo struct.
  """
  if isinstance(host, unicode):
    host = host.encode('idna')
  if host == '*':
    host = ''
  if service == '*':
    service = ''
  if not host and not service:
    raise gaierror(EAI_NONAME, 'nodename nor servname provided, or not known')

  families = [f for f in _ADDRESS_FAMILY_MAP.keys()
              if family in (AF_UNSPEC, f)]
  if not families:
    raise gaierror(EAI_FAMILY, 'ai_family not supported')

  sock_proto = [sp for sp in _SOCK_PROTO_MAP.keys()
                if socktype in (0, sp[0]) and proto in (0, sp[1])]
  if not sock_proto:
    raise gaierror(EAI_BADHINTS, 'Bad hints')

  canon = ''
  sock_proto_port = []
  family_addresses = []


  if host:
    canon, _, addresses = _Resolve(
        host, families,
        use_dns=~(flags & AI_NUMERICHOST),
        canonical=(flags & AI_CANONNAME))
    family_addresses = [(f, a)
                        for f in families
                        for a in addresses if _IsAddr(f, a)]
  else:
    if flags & AI_PASSIVE:
      canon = 'anyaddr'
      if AF_INET6 in families:
        family_addresses.append((AF_INET6, '::'))
      if AF_INET in families:
        family_addresses.append((AF_INET, '0.0.0.0'))
    else:
      canon = 'localhost'
      if AF_INET6 in families:
        family_addresses.append((AF_INET6, '::1'))
      if AF_INET in families:
        family_addresses.append((AF_INET, '127.0.0.1'))


  if service:
    sock_proto_port = [
        sp + (_ResolveService(service, _SOCK_PROTO_MAP[sp],
                              flags & AI_NUMERICSERV)[1],)
        for sp in sock_proto]
  else:
    sock_proto_port = [sp + (0,) for sp in sock_proto]

  return [(fa[0], spp[0], spp[1], canon, (fa[1], spp[2]))
          for fa in family_addresses
          for spp in sock_proto_port]


def getnameinfo():

  raise SocketApiNotImplementedError()


def getdefaulttimeout():
  """getdefaulttimeout() -> timeout

  Returns the default timeout in floating seconds for new socket objects.
  A value of None indicates that new socket objects have no timeout.
  When the socket module is first imported, the default is None.
  """

  if _GLOBAL_TIMEOUT_VALUE < 0.0:
    return None
  return _GLOBAL_TIMEOUT_VALUE




def setdefaulttimeout(timeout):
  """setdefaulttimeout(timeout)

  Set the default timeout in floating seconds for new socket objects.
  A value of None indicates that new socket objects have no timeout.
  When the socket module is first imported, the default is None.
  """

  if timeout is None:
    timeout = -1.0
  else:
    try:
      timeout = 0.0 + timeout
    except TypeError:
      raise TypeError('a float is required')
    if timeout < 0.0:
      raise ValueError('Timeout value out of range')


  global _GLOBAL_TIMEOUT_VALUE
  _GLOBAL_TIMEOUT_VALUE = timeout


def _GetSocket(value):
  if isinstance(value, (int, long)):
    fileno = value
  else:
    try:
      fileno = value.fileno()
    except AttributeError:
      raise TypeError('argument must be an int, or have a fileno() method.')
  try:
    return _GLOBAL_SOCKET_MAP[fileno]
  except KeyError:
    raise ValueError('select only supported on socket objects.')






def select(rlist, wlist, xlist, timeout=None):
  """select(rlist, wlist, xlist[, timeout]) -> (rlist, wlist, xlist)

  Wait until one or more file descriptors are ready for some kind of I/O.
  The first three arguments are sequences of file descriptors to be waited for:
  rlist -- wait until ready for reading
  wlist -- wait until ready for writing
  xlist -- wait for an ``exceptional condition''
  If only one kind of condition is required, pass [] for the other lists.
  A file descriptor is either a socket or file object, or a small integer
  gotten from a fileno() method call on one of those.

  The optional 4th argument specifies a timeout in seconds; it may be
  a floating point number to specify fractions of seconds.  If it is absent
  or None, the call will never time out.

  The return value is a tuple of three lists corresponding to the first three
  arguments; each contains the subset of the corresponding file descriptors
  that are ready.
  """
  if not rlist and not wlist and not xlist:
    if timeout:
      time.sleep(timeout)
    return ([], [], [])

  state_map = {}
  rlist_out, wlist_out, xlist_out = [], [], []

  def _SetState(request, sock, event):
    socket_descriptor = sock._SocketDescriptor()
    state = state_map.setdefault(socket_descriptor, { 'observed_events': 0, })

    if ((event == POLLIN and sock._shutdown_read) or
        (event == POLLOUT and sock._shutdown_write)):
      state['observed_events'] |= event
      request.set_timeout_seconds(0.0)
      return

    poll_event = state.get('poll_event')
    if not poll_event:
      poll_event = request.add_events()
      poll_event.set_socket_descriptor(socket_descriptor)
      poll_event.set_observed_events(0)
      state['poll_event'] = poll_event
    poll_event.set_requested_events(poll_event.requested_events()|event)

  request = remote_socket_service_pb.PollRequest()
  if timeout is not None:
    request.set_timeout_seconds(timeout)

  for value in rlist:
    _SetState(request, _GetSocket(value), POLLIN)
  for value in wlist:
    _SetState(request, _GetSocket(value), POLLOUT)

  if request.events_size():
    reply = remote_socket_service_pb.PollReply()

    try:
      apiproxy_stub_map.MakeSyncCall('remote_socket', 'Poll', request, reply)
    except apiproxy_errors.ApplicationError, e:
      raise _SystemExceptionFromAppError(e)

    for event in reply.events_list():
      state_map[event.socket_descriptor()][
          'observed_events'] |= event.observed_events()

  for value in rlist:
    state = state_map[_GetSocket(value)._SocketDescriptor()]
    if state['observed_events'] & POLLIN:
      rlist_out.append(value)
  for value in wlist:
    state = state_map[_GetSocket(value)._SocketDescriptor()]
    if state['observed_events'] & POLLOUT:
      wlist_out.append(value)

  return (rlist_out, wlist_out, xlist_out)


class socket(object):
  """socket([family[, type[, proto]]]) -> socket object

  Open a socket of the given type.  The family argument specifies the
  address family; it defaults to AF_INET.  The type argument specifies
  whether this is a stream (SOCK_STREAM, this is the default)
  or datagram (SOCK_DGRAM) socket.  The protocol argument defaults to 0,
  specifying the default protocol.  Keyword arguments are accepted.

  A socket object represents one endpoint of a network connection.
  """

  def __del__(self):
    if not self._serialized:
      self.close()

  def __getstate__(self):
    self._serialized = True
    return self.__dict__



  def __init__(self, family=AF_INET, type=SOCK_STREAM, proto=0, _create=False):
    if family not in (AF_INET, AF_INET6):
      raise error(errno.EAFNOSUPPORT, os.strerror(errno.EAFNOSUPPORT))

    if type not in (SOCK_STREAM, SOCK_DGRAM):
      raise error(errno.EPROTONOSUPPORT, os.strerror(errno.EPROTONOSUPPORT))

    if proto:
      if ((proto not in (IPPROTO_TCP, IPPROTO_UDP)) or
          (proto == IPPROTO_TCP and type != SOCK_STREAM) or
          (proto == IPPROTO_UDP and type != SOCK_DGRAM)):
        raise error(errno.EPROTONOSUPPORT, os.strerror(errno.EPROTONOSUPPORT))

    self.family = family
    self.type = type
    self.proto = proto
    self._created = False
    self._fileno = None
    self._serialized = False
    self.settimeout(getdefaulttimeout())
    self._Clear()

    if _create:
      self._CreateSocket()

  def _Clear(self):
    self._socket_descriptor = None
    self._bound = False
    self._listen = False
    self._connected = False
    self._connect_in_progress = False
    self._shutdown_read = False
    self._shutdown_write = False
    self._setsockopt = []
    self._stream_offset = 0

  def _CreateSocket(self, address=None, bind_address=None,
                    address_hostname_hint=None):
    assert not self._created
    self._created = True

    request = remote_socket_service_pb.CreateSocketRequest()

    if self.family == AF_INET:
      request.set_family(remote_socket_service_pb.CreateSocketRequest.IPv4)
    elif self.family == AF_INET6:
      request.set_family(remote_socket_service_pb.CreateSocketRequest.IPv6)

    if self.type == SOCK_STREAM:
      request.set_protocol(remote_socket_service_pb.CreateSocketRequest.TCP)
    elif self.type == SOCK_DGRAM:
      request.set_protocol(remote_socket_service_pb.CreateSocketRequest.UDP)

    if address:
      assert self.gettimeout() is None, (
          'Non-blocking connect not supported by CreateSocket')
      self._SetProtoFromAddr(request.mutable_remote_ip(), address,
                             address_hostname_hint)

    if bind_address:
      self._SetProtoFromAddr(request.mutable_proxy_external_ip(), bind_address)

    for level, option, value in self._setsockopt:
      o = request.add_socket_options()
      o.set_level(level)
      o.set_option(option)
      if isinstance(value, (int, long)):
        o.set_value(struct.pack('=L', value))
      else:
        o.set_value(value)
    self._setsockopt = []

    reply = remote_socket_service_pb.CreateSocketReply()

    try:
      apiproxy_stub_map.MakeSyncCall(
          'remote_socket', 'CreateSocket', request, reply)
    except apiproxy_errors.ApplicationError, e:
      raise _SystemExceptionFromAppError(e)

    self._socket_descriptor = reply.socket_descriptor()
    if bind_address:
      self._bound = True
    if address:
      self._bound = True
      self._connected = True

  def _GetPackedAddr(self, addr):
    if addr == '<broadcast>':
      if self.family == AF_INET6:
        return '\xff' * 16
      else:
        return '\xff' * 4
    for res in getaddrinfo(addr, '0',
                           self.family, self.type, self.proto,
                           AI_NUMERICSERV|AI_PASSIVE):
      return inet_pton(self.family, res[4][0])

  def _SetProtoFromAddr(self, proto, address, hostname_hint=None):
    address, port = address
    proto.set_packed_address(self._GetPackedAddr(address))
    proto.set_port(port)
    proto.set_hostname_hint(hostname_hint or address)

  def fileno(self):
    """fileno() -> integer

    Return the integer file descriptor of the socket.
    """
    global _GLOBAL_SOCKET_MAP
    global _GLOBAL_SOCKET_NEXT_FILENO
    if self._fileno is None:
      self._fileno = _GLOBAL_SOCKET_NEXT_FILENO
      _GLOBAL_SOCKET_NEXT_FILENO += 1
      _GLOBAL_SOCKET_MAP[self._fileno] = self
    assert _GLOBAL_SOCKET_MAP.get(self._fileno) == self, (
        "fileno mismatch in _GLOBAL_SOCKET_MAP")
    return self._fileno

  def bind(self, address):
    """bind(address)

    Bind the socket to a local address.  For IP sockets, the address is a
    pair (host, port); the host must refer to the local host. For raw packet
    sockets the address is a tuple (ifname, proto [,pkttype [,hatype]])
    """
    if not self._created:
      self._CreateSocket(bind_address=address)
      return
    if not self._socket_descriptor:
      raise error(errno.EBADF, os.strerror(errno.EBADF))
    if self._bound:
      raise error(errno.EINVAL, os.strerror(errno.EINVAL))

    request = remote_socket_service_pb.BindRequest()
    request.set_socket_descriptor(self._socket_descriptor)
    self._SetProtoFromAddr(request.mutable_proxy_external_ip(), address)

    reply = remote_socket_service_pb.BindReply()

    try:
      apiproxy_stub_map.MakeSyncCall('remote_socket', 'Bind', request, reply)
    except apiproxy_errors.ApplicationError, e:
      raise _SystemExceptionFromAppError(e)

  def listen(self, backlog):
    """listen(backlog)

    Enable a server to accept connections.  The backlog argument must be at
    least 1; it specifies the number of unaccepted connection that the system
    will allow before refusing new connections.
    """
    if not self._created:
      self._CreateSocket(bind_address=('', 0))
    if not self._socket_descriptor:
      raise error(errno.EBADF, os.strerror(errno.EBADF))
    if self._connected:
      raise error(errno.EINVAL, os.strerror(errno.EINVAL))
    if self.type != SOCK_STREAM:
      raise error(errno.EOPNOTSUPP, os.strerror(errno.EOPNOTSUPP))
    self._bound = True
    self._listen = True

    request = remote_socket_service_pb.ListenRequest()
    request.set_socket_descriptor(self._socket_descriptor)
    request.set_backlog(backlog)

    reply = remote_socket_service_pb.ListenReply()

    try:
      apiproxy_stub_map.MakeSyncCall('remote_socket', 'Listen', request, reply)
    except apiproxy_errors.ApplicationError, e:
      raise _SystemExceptionFromAppError(e)

  def accept(self):
    """accept() -> (socket object, address info)

    Wait for an incoming connection.  Return a new socket representing the
    connection, and the address of the client.  For IP sockets, the address
    info is a pair (hostaddr, port).
    """
    if not self._created:
      self._CreateSocket()
    if not self._socket_descriptor:
      raise error(errno.EBADF, os.strerror(errno.EBADF))
    if not self._listen:
      raise error(errno.EINVAL, os.strerror(errno.EINVAL))

    request = remote_socket_service_pb.AcceptRequest()
    request.set_socket_descriptor(self._socket_descriptor)
    if self.gettimeout() is not None:
      request.set_timeout_seconds(self.gettimeout())

    reply = remote_socket_service_pb.AcceptReply()

    try:
      apiproxy_stub_map.MakeSyncCall('remote_socket', 'Accept', request, reply)
    except apiproxy_errors.ApplicationError, e:
      raise _SystemExceptionFromAppError(e)

    ret = socket(self.family, self.type, self.proto)
    ret._socket_descriptor = reply.new_socket_descriptor()
    ret._created = True
    ret._bound = True
    ret._connected = True
    return ret




  def connect(self, address, _hostname_hint=None):
    """connect(address)

    Connect the socket to a remote address.  For IP sockets, the address
    is a pair (host, port).
    """
    if not self._created:
      if self.gettimeout() is None:
        self._CreateSocket(address=address,
                           address_hostname_hint=_hostname_hint)
        return
      else:




        self._CreateSocket()
    if not self._socket_descriptor:
      raise error(errno.EBADF, os.strerror(errno.EBADF))
    if self._connected:
      raise error(errno.EISCONN, os.strerror(errno.EISCONN))

    request = remote_socket_service_pb.ConnectRequest()
    request.set_socket_descriptor(self._socket_descriptor)
    self._SetProtoFromAddr(request.mutable_remote_ip(), address, _hostname_hint)
    if self.gettimeout() is not None:
      request.set_timeout_seconds(self.gettimeout())

    reply = remote_socket_service_pb.ConnectReply()

    try:
      apiproxy_stub_map.MakeSyncCall('remote_socket', 'Connect', request, reply)
    except apiproxy_errors.ApplicationError, e:
      translated_e = _SystemExceptionFromAppError(e)
      if translated_e.errno == errno.EISCONN:
        self._bound = True
        self._connected = True
      elif translated_e.errno == errno.EINPROGRESS:
        self._connect_in_progress = True
      raise translated_e

    self._bound = True
    self._connected = True

  def connect_ex(self, address):
    """connect_ex(address) -> errno

    This is like connect(address), but returns an error code (the errno value)
    instead of raising an exception when an error occurs.
    """
    try:
      self.connect(address)
    except error, e:
      return e.errno
    return 0

  def getpeername(self):
    """getpeername() -> address info

    Return the address of the remote endpoint.  For IP sockets, the address
    info is a pair (hostaddr, port).
    """
    if not self._created:
      self._CreateSocket()
    if not self._socket_descriptor:
      raise error(errno.EBADF, os.strerror(errno.EBADF))
    if not (self._connected or self._connect_in_progress):
      raise error(errno.ENOTCONN, os.strerror(errno.ENOTCONN))

    request = remote_socket_service_pb.GetPeerNameRequest()
    request.set_socket_descriptor(self._socket_descriptor)

    reply = remote_socket_service_pb.GetPeerNameReply()

    try:
      apiproxy_stub_map.MakeSyncCall(
          'remote_socket', 'GetPeerName', request, reply)
    except apiproxy_errors.ApplicationError, e:
      raise _SystemExceptionFromAppError(e)

    if self._connect_in_progress:
      self._connect_in_progress = False
      self._connected = True

    return (
        inet_ntop(self.family, reply.peer_ip().packed_address()),
        reply.peer_ip().port())

  def getsockname(self):
    """getsockname() -> address info

    Return the address of the local endpoint.  For IP sockets, the address
    info is a pair (hostaddr, port).
    """
    if not self._created:
      self._CreateSocket()
    if not self._socket_descriptor:
      raise error(errno.EBADF, os.strerror(errno.EBADF))

    request = remote_socket_service_pb.GetSocketNameRequest()
    request.set_socket_descriptor(self._socket_descriptor)

    reply = remote_socket_service_pb.GetSocketNameReply()

    try:
      apiproxy_stub_map.MakeSyncCall(
          'remote_socket', 'GetSocketName', request, reply)
    except apiproxy_errors.ApplicationError, e:
      raise _SystemExceptionFromAppError(e)

    return (
        inet_ntop(self.family, reply.proxy_external_ip().packed_address()),
        reply.proxy_external_ip().port())

  def recv(self, buffersize, flags=0):
    """recv(buffersize[, flags]) -> data

    Receive up to buffersize bytes from the socket.  For the optional flags
    argument, see the Unix manual.  When no data is available, block until
    at least one byte is available or until the remote end is closed.  When
    the remote end is closed and all data is read, return the empty string.
    """
    return self.recvfrom(buffersize, flags)[0]

  def recv_into(self, buf, nbytes=0, flags=0):
    """recv_into(buffer, [nbytes[, flags]]) -> nbytes_read

    A version of recv() that stores its data into a buffer rather than
    creating a new string.  Receive up to buffersize bytes from the socket.
    If buffersize is not specified (or 0), receive up to the size available
    in the given buffer.

    See recv() for documentation about the flags.
    """
    return self.recvfrom_into(buf, nbytes, flags)[0]

  def recvfrom(self, buffersize, flags=0):
    """recvfrom(buffersize[, flags]) -> (data, address info)

    Like recv(buffersize, flags) but also return the sender's address info.
    """
    if not self._created:
      self._CreateSocket()
    if not self._socket_descriptor:
      raise error(errno.EBADF, os.strerror(errno.EBADF))

    request = remote_socket_service_pb.ReceiveRequest()
    request.set_socket_descriptor(self._socket_descriptor)
    request.set_data_size(buffersize)
    request.set_flags(flags)
    if self.type == SOCK_STREAM:
      if not (self._connected or self._connect_in_progress):
        raise error(errno.ENOTCONN, os.strerror(errno.ENOTCONN))
    if self._shutdown_read:
      request.set_timeout_seconds(0.0)
    elif self.gettimeout() is not None:
      request.set_timeout_seconds(self.gettimeout())

    reply = remote_socket_service_pb.ReceiveReply()

    try:
      apiproxy_stub_map.MakeSyncCall('remote_socket', 'Receive', request, reply)
    except apiproxy_errors.ApplicationError, e:
      e = _SystemExceptionFromAppError(e)
      if not self._shutdown_read or e.errno != errno.EAGAIN:
        raise e

    if self._connect_in_progress:
      self._connect_in_progress = False
      self._connected = True

    address = None
    if reply.has_received_from():
      address = (
          inet_ntop(self.family, reply.received_from().packed_address()),
          reply.received_from().port())

    return reply.data(), address

  def recvfrom_into(self, buffer, nbytes=0, flags=0):
    """recvfrom_into(buffer[, nbytes[, flags]]) -> (nbytes, address info)

    Like recv_into(buffer[, nbytes[, flags]]) but also return the
    sender's address info.
    """
    if nbytes == 0 or nbytes > len(buffer):
      nbytes = len(buffer)
    (data, addr) = self.recvfrom(nbytes, flags)
    data = bytearray(data)
    buffer[:len(data)] = data
    return (len(data), addr)

  def send(self, data, flags=0):
    """send(data[, flags]) -> count

    Send a data string to the socket.  For the optional flags
    argument, see the Unix manual.  Return the number of bytes
    sent; this may be less than len(data) if the network is busy.
    """
    return self.sendto(data, flags, None)

  def sendall(self, data, flags=0):
    """sendall(data[, flags])

    Send a data string to the socket.  For the optional flags
    argument, see the Unix manual.  This calls send() repeatedly
    until all data is sent.  If an error occurs, it's impossible
    to tell how much data has been sent.
    """
    offset = 0
    while offset < len(data):
      offset += self.sendto(data[offset:], flags, None)

  def sendto(self, data, *args):
    """sendto(data[, flags], address) -> count

    Like send(data, flags) but allows specifying the destination address.
    For IP sockets, the address is a pair (hostaddr, port).
    """
    if len(args) == 1:
      flags, address = 0, args[0]
    elif len(args) == 2:
      flags, address = args

    if not self._created:
      self._CreateSocket()
    if not self._socket_descriptor:
      raise error(errno.EBADF, os.strerror(errno.EBADF))
    if self._shutdown_write:
      raise error(errno.EPIPE, os.strerror(errno.EPIPE))

    request = remote_socket_service_pb.SendRequest()
    request.set_socket_descriptor(self._socket_descriptor)

    if len(data) > 512*1024:
      request.set_data(data[:512*1024])
    else:
      request.set_data(data)
    request.set_flags(flags)
    request.set_stream_offset(self._stream_offset)

    if address:
      if self._connected:
        raise error(errno.EISCONN, os.strerror(errno.EISCONN))
      if self.type != SOCK_DGRAM:
        raise error(errno.ENOTCONN, os.strerror(errno.ENOTCONN))
      self._SetProtoFromAddr(request.mutable_send_to(), address)
    else:
      if not (self._connected or self._connect_in_progress):
        raise error(errno.ENOTCONN, os.strerror(errno.ENOTCONN))

    if self.gettimeout() is not None:
      request.set_timeout_seconds(self.gettimeout())

    reply = remote_socket_service_pb.SendReply()

    try:
      apiproxy_stub_map.MakeSyncCall('remote_socket', 'Send', request, reply)
    except apiproxy_errors.ApplicationError, e:
      raise _SystemExceptionFromAppError(e)

    if self._connect_in_progress:
      self._connect_in_progress = False
      self._connected = True

    nbytes = reply.data_sent()
    assert nbytes >= 0
    if self.type == SOCK_STREAM:
      self._stream_offset += nbytes
    return nbytes

  def setblocking(self, block):
    """setblocking(flag)

    Set the socket to blocking (flag is true) or non-blocking (false).
    setblocking(True) is equivalent to settimeout(None);
    setblocking(False) is equivalent to settimeout(0.0).
    """
    if block:
      self._timeout = -1.0
    else:
      self._timeout = 0.0

  def settimeout(self, timeout):
    """settimeout(timeout)

    Set a timeout on socket operations.  'timeout' can be a float,
    giving in seconds, or None.  Setting a timeout of None disables
    the timeout feature and is equivalent to setblocking(1).
    Setting a timeout of zero is the same as setblocking(0).
    """
    if timeout is None:
      self._timeout = -1.0
    else:
      try:
        self._timeout = 0.0 + timeout
      except:
        raise TypeError('a float is required')
      if self._timeout < 0.0:
        raise ValueError('Timeout value out of range')

  def gettimeout(self):
    """gettimeout() -> timeout

    Returns the timeout in floating seconds associated with socket
    operations. A timeout of None indicates that timeouts on socket
    operations are disabled.
    """
    if self._timeout < 0.0:
      return None
    return self._timeout

  def setsockopt(self, level, option, value):
    """setsockopt(level, option, value)

    Set a socket option.  See the Unix manual for level and option.
    The value argument can either be an integer or a string.
    """



    if not self._created:
      self._setsockopt.append((level, option, value))
      self._CreateSocket()
      return
    if not self._socket_descriptor:
      raise error(errno.EBADF, os.strerror(errno.EBADF))

    request = remote_socket_service_pb.SetSocketOptionsRequest()
    request.set_socket_descriptor(self._socket_descriptor)

    o = request.add_options()
    o.set_level(level)
    o.set_option(option)
    if isinstance(value, (int, long)):
      o.set_value(struct.pack('=L', value))
    else:
      o.set_value(value)

    reply = remote_socket_service_pb.SetSocketOptionsReply()

    try:
      apiproxy_stub_map.MakeSyncCall(
          'remote_socket', 'SetSocketOptions', request, reply)
    except apiproxy_errors.ApplicationError, e:
      raise _SystemExceptionFromAppError(e)

  def getsockopt(self, level, option, buffersize=0):
    """getsockopt(level, option[, buffersize]) -> value

    Get a socket option.  See the Unix manual for level and option.
    If a nonzero buffersize argument is given, the return value is a
    string of that length; otherwise it is an integer.
    """
    if not self._created:
      self._CreateSocket()
    if not self._socket_descriptor:
      raise error(errno.EBADF, os.strerror(errno.EBADF))

    request = remote_socket_service_pb.GetSocketOptionsRequest()
    request.set_socket_descriptor(self._socket_descriptor)
    o = request.add_options()
    o.set_level(level)
    o.set_option(option)
    o.set_value('')

    reply = remote_socket_service_pb.GetSocketOptionsReply()

    try:
      apiproxy_stub_map.MakeSyncCall(
          'remote_socket', 'GetSocketOptions', request, reply)
    except apiproxy_errors.ApplicationError, e:
      raise _SystemExceptionFromAppError(e)

    if not buffersize:
      return struct.unpack('=L', reply.options(0).value())[0]
    else:
      return reply.options(0).value()[:buffersize]

  def shutdown(self, flag):
    """shutdown(flag)

    Shut down the reading side of the socket (flag == SHUT_RD), the writing side
    of the socket (flag == SHUT_WR), or both ends (flag == SHUT_RDWR).
    """
    if not flag in (SHUT_RD, SHUT_WR, SHUT_RDWR):
      raise error(errno.EINVAL, os.strerror(errno.EINVAL))
    if not self._created:
      self._CreateSocket()
    if not self._socket_descriptor:
      raise error(errno.EBADF, os.strerror(errno.EBADF))
    if (not self._connected or
        (self._shutdown_read and flag in (SHUT_RD, SHUT_RDWR)) or
        (self._shutdown_write and flag in (SHUT_RD, SHUT_RDWR))):
      raise error(errno.ENOTCONN, os.strerror(errno.ENOTCONN))

    request = remote_socket_service_pb.ShutDownRequest()
    request.set_socket_descriptor(self._socket_descriptor)
    request.set_how(flag)
    request.set_send_offset(self._stream_offset)

    reply = remote_socket_service_pb.ShutDownReply()

    try:
      apiproxy_stub_map.MakeSyncCall(
          'remote_socket', 'ShutDown', request, reply)
    except apiproxy_errors.ApplicationError, e:
      raise _SystemExceptionFromAppError(e)

    if flag == SHUT_RD or flag == SHUT_RDWR:
      self._shutdown_read = True
    if flag == SHUT_WR or flag == SHUT_RDWR:
      self._shutdown_write = True

  def close(self):
    """close()

    Close the socket.  It cannot be used after this call.
    """
    self._created = True
    if not self._socket_descriptor:
      return

    request = remote_socket_service_pb.CloseRequest()
    request.set_socket_descriptor(self._socket_descriptor)

    reply = remote_socket_service_pb.CloseReply()

    try:
      apiproxy_stub_map.MakeSyncCall('remote_socket', 'Close', request, reply)
    except apiproxy_errors.ApplicationError, e:
      raise _SystemExceptionFromAppError(e)

    self._Clear()

  def _SocketDescriptor(self):
    if not self._created:
      self._CreateSocket()
    if not self._socket_descriptor:
      raise error(errno.EBADF, os.strerror(errno.EBADF))
    return self._socket_descriptor
