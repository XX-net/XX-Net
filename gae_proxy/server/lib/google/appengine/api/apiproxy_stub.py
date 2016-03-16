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







from __future__ import with_statement




import random
import threading

from google.appengine.api import apiproxy_rpc
from google.appengine.api import request_info
from google.appengine.runtime import apiproxy_errors


MAX_REQUEST_SIZE = 1 << 20


class APIProxyStub(object):
  """Base class for implementing API proxy stub classes.

  To implement an API proxy stub:
    - Extend this class.
    - Override __init__ to pass in appropriate default service name.
    - Implement service methods as _Dynamic_<method>(request, response).
  """



  _ACCEPTS_REQUEST_ID = False




  THREADSAFE = False

  def __init__(self, service_name, max_request_size=MAX_REQUEST_SIZE,
               request_data=None):
    """Constructor.

    Args:
      service_name: Service name expected for all calls.
      max_request_size: int, maximum allowable size of the incoming request.  A
        apiproxy_errors.RequestTooLargeError will be raised if the inbound
        request exceeds this size.  Default is 1 MB.
      request_data: A request_info.RequestInfo instance used to look up state
        associated with the request that generated an API call.
    """
    self.__service_name = service_name
    self.__max_request_size = max_request_size
    self.request_data = request_data or request_info._local_request_info



    self._mutex = threading.RLock()
    self.__error = None
    self.__error_dict = {}

  def CreateRPC(self):
    """Creates RPC object instance.

    Returns:
      a instance of RPC.
    """
    return apiproxy_rpc.RPC(stub=self)

  def MakeSyncCall(self, service, call, request, response, request_id=None):
    """The main RPC entry point.

    Args:
      service: Must be name as provided to service_name of constructor.
      call: A string representing the rpc to make.  Must be part of
        the underlying services methods and impemented by _Dynamic_<call>.
      request: A protocol buffer of the type corresponding to 'call'.
      response: A protocol buffer of the type corresponding to 'call'.
      request_id: A unique string identifying the request associated with the
          API call.
    """
    assert service == self.__service_name, ('Expected "%s" service name, '
                                            'was "%s"' % (self.__service_name,
                                                          service))
    if request.ByteSize() > self.__max_request_size:
      raise apiproxy_errors.RequestTooLargeError(
          'The request to API call %s.%s() was too large.' % (service, call))
    messages = []
    assert request.IsInitialized(messages), messages




    exception_type, frequency = self.__error_dict.get(call, (None, None))
    if exception_type and frequency:
      if random.random() <= frequency:
        raise exception_type

    if self.__error:
      if random.random() <= self.__error_rate:
        raise self.__error


    method = getattr(self, '_Dynamic_' + call)
    if self._ACCEPTS_REQUEST_ID:
      method(request, response, request_id)
    else:
      method(request, response)

  def SetError(self, error, method=None, error_rate=1):
    """Set an error condition that may be raised when calls made to stub.

    If a method is specified, the error will only apply to that call.
    The error rate is applied to the method specified or all calls if
    method is not set.

    Args:
      error: An instance of apiproxy_errors.Error or None for no error.
      method: A string representing the method that the error will affect.
      error_rate: a number from [0, 1] that sets the chance of the error,
        defaults to 1.
    """
    assert error is None or isinstance(error, apiproxy_errors.Error)
    if method and error:
      self.__error_dict[method] = error, error_rate
    else:
      self.__error_rate = error_rate
      self.__error = error


def Synchronized(method):
  """Decorator to acquire a mutex around an APIProxyStub method.

  Args:
    method: An unbound method of APIProxyStub or a subclass.

  Returns:
    The method, altered such it acquires self._mutex throughout its execution.
  """

  def WrappedMethod(self, *args, **kwargs):
    with self._mutex:
      return method(self, *args, **kwargs)

  return WrappedMethod
