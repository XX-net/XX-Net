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
"""Stub version of the Remote Socket API.

A stub version of the Remote Socket API for the dev_appserver.
"""

from __future__ import with_statement



import binascii
import errno
import os
import re
import select
import socket
import threading
import time
import uuid

from google.appengine.api import apiproxy_stub
from google.appengine.api.remote_socket import _remote_socket_addr
from google.appengine.api.remote_socket import remote_socket_service_pb
from google.appengine.api.remote_socket.remote_socket_service_pb import RemoteSocketServiceError
from google.appengine.runtime import apiproxy_errors


def TranslateSystemErrors(method):
  """Decorator to catch and translate socket.error to ApplicationError.

  Args:
    method: An unbound method of APIProxyStub or a subclass.

  Returns:
    The method, altered such it catches socket.error, socket.timeout and
    socket.gaierror and re-raises the required apiproxy_errors.ApplicationError.
  """

  def WrappedMethod(self, *args, **kwargs):
    try:
      return method(self, *args, **kwargs)
    except socket.gaierror, e:
      raise apiproxy_errors.ApplicationError(
          RemoteSocketServiceError.GAI_ERROR,
          'system_error:%u error_detail:"%s"' % (e.errno, e.strerror))
    except socket.timeout, e:
      raise apiproxy_errors.ApplicationError(
          RemoteSocketServiceError.SYSTEM_ERROR,
          'system_error:%u error_detail:"%s"' % (errno.EAGAIN,
                                                 os.strerror(errno.EAGAIN)))
    except socket.error, e:
      raise apiproxy_errors.ApplicationError(
          RemoteSocketServiceError.SYSTEM_ERROR,
          'system_error:%u error_detail:"%s"' % (e.errno, e.strerror))

  return WrappedMethod


class SocketState(object):
  def __init__(self, family, protocol, sock, last_accessed_time):
    self.family = family
    self.protocol = protocol
    self.sock = sock


    self.last_accessed_time = last_accessed_time


    self.mutex = threading.RLock()
    self.timeout = None
    self.stream_offset = 0

  def SetTimeout(self, timeout):
    if timeout < 0:
      timeout = None
    if self.timeout != timeout:
      self.sock.settimeout(timeout)
    self.timeout = timeout



_MOCK_SOCKET_OPTIONS = (
    'SOL_SOCKET:SO_KEEPALIVE=00000000,'
    'SOL_SOCKET:SO_DEBUG=80000000,'
    'SOL_TCP:TCP_NODELAY=00000000,'
    'SOL_SOCKET:SO_LINGER=0000000000000000,'
    'SOL_SOCKET:SO_OOBINLINE=00000000,'
    'SOL_SOCKET:SO_SNDBUF=00002000,'
    'SOL_SOCKET:SO_RCVBUF=00002000,'
    'SOL_SOCKET:SO_REUSEADDR=01000000')


class RemoteSocketServiceStub(apiproxy_stub.APIProxyStub):
  """Stub implementation of the Remote Socket API."""

  THREADSAFE = True

  _AF_MAP = {
      socket.AF_INET: remote_socket_service_pb.CreateSocketRequest.IPv4,
      socket.AF_INET6: remote_socket_service_pb.CreateSocketRequest.IPv6,
      }



  _TRANSLATED_AF_MAP = {
      socket.AF_INET: _remote_socket_addr.AF_INET,
      socket.AF_INET6: _remote_socket_addr.AF_INET6,
      }

  _HOW_MAP = {
      remote_socket_service_pb.ShutDownRequest.SOCKET_SHUT_RD: socket.SHUT_RD,
      remote_socket_service_pb.ShutDownRequest.SOCKET_SHUT_WR: socket.SHUT_WR,
      remote_socket_service_pb.ShutDownRequest.SOCKET_SHUT_RDWR: (
          socket.SHUT_RDWR),
      }

  def __init__(self,
               service_name='remote_socket',
               get_time=time.time,
               mock_options_spec=_MOCK_SOCKET_OPTIONS):
    """Initializer.

    Args:
      log: where to log messages
      service_name: service name expected for all calls
      get_time: Used for testing. Function that works like time.time().
    """
    super(RemoteSocketServiceStub, self).__init__(service_name)
    self._descriptor_to_socket_state = {}
    self._time = get_time
    self._mock_options = _MockSocketOptions(mock_options_spec)

  def ResetMockOptions(self, mock_options_spec):
    self._mock_options = _MockSocketOptions(mock_options_spec)

  def _LookupSocket(self, descriptor):
    with self._mutex:
      val = self._descriptor_to_socket_state.get(descriptor)
      if not val:
        raise apiproxy_errors.ApplicationError(
            RemoteSocketServiceError.SOCKET_CLOSED)

      now = self._time()
      if val.last_accessed_time < now - 120:
        del self._descriptor_to_socket_state[descriptor]
        raise apiproxy_errors.ApplicationError(
            RemoteSocketServiceError.SOCKET_CLOSED)

      val.last_accessed_time = now
      return val

  def _AddressPortTupleFromProto(self, family, ap_proto):
    """Converts an AddressPort proto into a python (addrstr, port) tuple."""
    try:
      addr = _remote_socket_addr.inet_ntop(
          self._TRANSLATED_AF_MAP[family], ap_proto.packed_address())
    except ValueError:
      raise apiproxy_errors.ApplicationError(
          RemoteSocketServiceError.INVALID_REQUEST,
          'Invalid Address.')
    return (addr, ap_proto.port())

  def _AddressPortTupleToProto(self, family, ap_tuple, ap_proto):
    """Converts a python (addrstr, port) tuple into an AddressPort proto."""
    ap_proto.set_packed_address(
        _remote_socket_addr.inet_pton(
          self._TRANSLATED_AF_MAP[family], ap_tuple[0]))
    ap_proto.set_port(ap_tuple[1])

  def _BindAllowed(self, addr, port):
    if addr in ('0.0.0.0', '::') and port == 0:
      return True
    return False

  @TranslateSystemErrors
  def _Dynamic_CreateSocket(self, request, response):
    family = socket.AF_INET
    if request.family() == remote_socket_service_pb.CreateSocketRequest.IPv6:
      family = socket.AF_INET6
    protocol = socket.SOCK_STREAM
    if request.protocol() == remote_socket_service_pb.CreateSocketRequest.UDP:
      protocol = socket.SOCK_DGRAM
    sock = socket.socket(family, protocol)
    if request.has_proxy_external_ip():
      addr, port = self._AddressPortTupleFromProto(
          family, request.proxy_external_ip())
      if not self._BindAllowed(addr, port):
        raise apiproxy_errors.ApplicationError(
            RemoteSocketServiceError.PERMISSION_DENIED,
            'Attempt to bind port without permission.')
      sock.bind((addr, port))
    if request.has_remote_ip():
      sock.connect(self._AddressPortTupleFromProto(family, request.remote_ip()))

    descriptor = str(uuid.uuid4())
    state = SocketState(family, protocol, sock, self._time())
    with self._mutex:
      self._descriptor_to_socket_state[descriptor] = state

    response.set_socket_descriptor(descriptor)
    if request.has_proxy_external_ip() or request.has_remote_ip():
      self._AddressPortTupleToProto(family, sock.getsockname(),
                                    response.mutable_proxy_external_ip())

  @TranslateSystemErrors
  def _Dynamic_Bind(self, request, response):
    state = self._LookupSocket(request.socket_descriptor())
    addr, port = self._AddressPortTupleFromProto(
        state.family, request.proxy_external_ip())
    if not self._BindAllowed(addr, port):
      raise apiproxy_errors.ApplicationError(
          RemoteSocketServiceError.PERMISSION_DENIED,
          'Attempt to bind port without permission.')
    state.sock.bind((addr, port))
    self._AddressPortTupleToProto(state.family, state.sock.getsockname(),
                                  response.mutable_proxy_external_ip())

  def _Dynamic_Listen(self, request, response):
    raise NotImplementedError()

  def _Dynamic_Accept(self, request, response):
    raise NotImplementedError()

  @TranslateSystemErrors
  def _Dynamic_Connect(self, request, response):
    state = self._LookupSocket(request.socket_descriptor())
    with state.mutex:
      state.SetTimeout(request.timeout_seconds())
      state.sock.connect(
          self._AddressPortTupleFromProto(state.family, request.remote_ip()))

  @TranslateSystemErrors
  def _Dynamic_GetSocketOptions(self, request, response):
    state = self._LookupSocket(request.socket_descriptor())
    for opt in request.options_list():
      if (opt.level() ==
          remote_socket_service_pb.SocketOption.SOCKET_SOL_SOCKET and
          opt.option() ==
          remote_socket_service_pb.SocketOption.SOCKET_SO_ERROR):
        ret = response.add_options()
        ret.set_level(opt.level())
        ret.set_option(opt.option())
        ret.set_value(
            state.sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR, 1024))
      else:
        value = self._mock_options.GetMockValue(opt.level(), opt.option())
        if value is None:
          raise apiproxy_errors.ApplicationError(
              RemoteSocketServiceError.PERMISSION_DENIED,
              'Attempt to get blocked socket option.')

        ret = response.add_options()
        ret.set_level(opt.level())
        ret.set_option(opt.option())
        ret.set_value(value)



  def _Dynamic_SetSocketOptions(self, request, response):
    self._LookupSocket(request.socket_descriptor())
    for opt in request.options_list():
      value = self._mock_options.GetMockValue(opt.level(), opt.option())
      if value is None:
        raise apiproxy_errors.ApplicationError(
            RemoteSocketServiceError.PERMISSION_DENIED,
            'Attempt to set blocked socket option.')

  @TranslateSystemErrors
  def _Dynamic_GetSocketName(self, request, response):
    state = self._LookupSocket(request.socket_descriptor())
    self._AddressPortTupleToProto(state.family,
                                  state.sock.getsockname(),
                                  response.mutable_proxy_external_ip())

  @TranslateSystemErrors
  def _Dynamic_GetPeerName(self, request, response):
    state = self._LookupSocket(request.socket_descriptor())
    self._AddressPortTupleToProto(state.family,
                                  state.sock.getpeername(),
                                  response.mutable_peer_ip())

  @TranslateSystemErrors
  def _Dynamic_Send(self, request, response):
    state = self._LookupSocket(request.socket_descriptor())
    with state.mutex:
      state.SetTimeout(request.timeout_seconds())
      if state.protocol == socket.SOCK_STREAM:
        if request.stream_offset() != state.stream_offset:
          raise apiproxy_errors.ApplicationError(
              RemoteSocketServiceError.INVALID_REQUEST,
              'Invalid stream_offset.')
      flags = request.flags()
      if flags != 0:
        raise apiproxy_errors.ApplicationError(
            RemoteSocketServiceError.INVALID_REQUEST,
            'Invalid flags.')
      if request.has_send_to():
        data_sent = state.sock.sendto(
            request.data(),
            flags,
            self._AddressPortTupleFromProto(state.family, request.send_to()))
      else:
        data_sent = state.sock.send(request.data(), flags)
      response.set_data_sent(data_sent)
      state.stream_offset += data_sent

  @TranslateSystemErrors
  def _Dynamic_Receive(self, request, response):
    state = self._LookupSocket(request.socket_descriptor())
    with state.mutex:
      state.SetTimeout(request.timeout_seconds())
      flags = 0
      if request.flags() & remote_socket_service_pb.ReceiveRequest.MSG_PEEK:
        flags |= socket.MSG_PEEK
      received_from = None
      if state.protocol == socket.SOCK_DGRAM:
        data, received_from = state.sock.recvfrom(request.data_size(), flags)
      else:
        data = state.sock.recv(request.data_size(), flags)
      response.set_data(data)
      if received_from:
        self._AddressPortTupleToProto(state.family, received_from,
                                      response.mutable_received_from())

  @TranslateSystemErrors
  def _Dynamic_ShutDown(self, request, response):
    state = self._LookupSocket(request.socket_descriptor())
    state.sock.shutdown(self._HOW_MAP[request.how()])

  @TranslateSystemErrors
  def _Dynamic_Close(self, request, response):
    with self._mutex:
      try:
        state = self._LookupSocket(request.socket_descriptor())
      except apiproxy_errors.ApplicationError:
        return
      state.sock.close()
      del self._descriptor_to_socket_state[request.socket_descriptor()]

  @TranslateSystemErrors
  def _Dynamic_Resolve(self, request, response):
    addrs = {}
    for family, _, _, canonname, sa in socket.getaddrinfo(
        request.name(), 0, 0, socket.SOCK_STREAM, 0, socket.AI_CANONNAME):
      addrs.setdefault(self._AF_MAP.get(family), set()).add(
          _remote_socket_addr.inet_pton(self._TRANSLATED_AF_MAP[family], sa[0]))
      response.set_canonical_name(canonname)





      if canonname and canonname.lower() != request.name().lower():
        if not response.aliases_size():
          response.add_aliases(request.name())
    for af in request.address_families_list():
      for packed_addr in addrs.get(af, set()):
        response.add_packed_address(packed_addr)

  @TranslateSystemErrors
  def _Dynamic_Poll(self, request, response):
    timeout = request.timeout_seconds()
    if timeout < 0:
      timeout = None
    rfds, wfds, efds = [], [], []
    sock_map = {}
    for e in request.events_list():
      state = self._LookupSocket(e.socket_descriptor())
      events = e.requested_events()
      if events & ~(remote_socket_service_pb.PollEvent.SOCKET_POLLIN|
                    remote_socket_service_pb.PollEvent.SOCKET_POLLOUT):
        raise apiproxy_errors.ApplicationError(
            RemoteSocketServiceError.INVALID_REQUEST,
            'Invalid requested_events.')
      if events & remote_socket_service_pb.PollEvent.SOCKET_POLLIN:
        rfds.append(state.sock)
      if events & remote_socket_service_pb.PollEvent.SOCKET_POLLOUT:
        wfds.append(state.sock)
      o = response.add_events()
      o.set_socket_descriptor(e.socket_descriptor())
      o.set_requested_events(e.requested_events())
      o.set_observed_events(0)
      sock_map.setdefault(state.sock, []).append(o)
    rfds, wfds, _ = select.select(rfds, wfds, efds, timeout)
    for sock in rfds:
      for o in sock_map[sock]:
        o.set_observed_events(
            o.observed_events()|
            remote_socket_service_pb.PollEvent.SOCKET_POLLIN)
    for sock in wfds:
      for o in sock_map[sock]:
        o.set_observed_events(
            o.observed_events()|
            remote_socket_service_pb.PollEvent.SOCKET_POLLOUT)








class _MockSocketOptions(object):

  def __init__(self, mock_options_spec):
    self._mock_options = {}

    option_spec_re = re.compile(r'^(\w+):(\w+)=(\w+)$')
    for mock_option_spec in mock_options_spec.split(','):
      if not mock_option_spec:
        continue

      m = option_spec_re.match(mock_option_spec)
      if m is None:
        raise Exception('option specification malformed. '
                        'expected <level>:<name>=<value>. Saw "%s"'
                        % mock_option_spec)

      level, name, value = m.groups()

      numeric_level = getattr(remote_socket_service_pb.SocketOption,
                              'SOCKET_' + level)
      numeric_name = getattr(remote_socket_service_pb.SocketOption,
                             'SOCKET_' + name)
      raw_value = binascii.a2b_hex(value)

      self._mock_options[(numeric_level, numeric_name)] = raw_value

  def GetMockValue(self, level, name):
    return self._mock_options.get((level, name), None)
