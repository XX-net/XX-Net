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




"""Base class for implementing API proxy stubs."""









from google.appengine.api import apiproxy_rpc
from google.appengine.runtime import apiproxy_errors


MAX_REQUEST_SIZE = 1 << 20


class APIProxyStub(object):
  """Base class for implementing API proxy stub classes.

  To implement an API proxy stub:
    - Extend this class.
    - Override __init__ to pass in appropriate default service name.
    - Implement service methods as _Dynamic_<method>(request, response).
  """

  def __init__(self, service_name, max_request_size=MAX_REQUEST_SIZE):
    """Constructor.

    Args:
      service_name: Service name expected for all calls.
      max_request_size: int, maximum allowable size of the incoming request.  A
        apiproxy_errors.RequestTooLargeError will be raised if the inbound
        request exceeds this size.  Default is 1 MB.
    """
    self.__service_name = service_name
    self.__max_request_size = max_request_size

  def CreateRPC(self):
    """Creates RPC object instance.

    Returns:
      a instance of RPC.
    """
    return apiproxy_rpc.RPC(stub=self)

  def MakeSyncCall(self, service, call, request, response):
    """The main RPC entry point.

    Args:
      service: Must be name as provided to service_name of constructor.
      call: A string representing the rpc to make.  Must be part of
        the underlying services methods and impemented by _Dynamic_<call>.
      request: A protocol buffer of the type corresponding to 'call'.
      response: A protocol buffer of the type corresponding to 'call'.
    """
    assert service == self.__service_name, ('Expected "%s" service name, '
                                            'was "%s"' % (self.__service_name,
                                                          service))
    if request.ByteSize() > self.__max_request_size:
      raise apiproxy_errors.RequestTooLargeError(
          'The request to API call %s.%s() was too large.' % (service, call))
    messages = []
    assert request.IsInitialized(messages), messages

    method = getattr(self, '_Dynamic_' + call)
    method(request, response)
