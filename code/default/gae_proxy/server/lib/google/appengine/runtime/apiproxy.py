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




"""Makes API calls to various Google-provided services.

Provides methods for making calls into Google Apphosting services and APIs
from your application code. This code will only work properly from within
the Google Apphosting environment.
"""



import sys

apiproxy_stub_map_loaded = (
    'google.appengine.api.apiproxy_stub_map' in sys.modules)

from google.net.proto import ProtocolBuffer
from google.appengine import runtime
from google.appengine.api import apiproxy_rpc
from google3.apphosting.runtime import _apphosting_runtime___python__apiproxy
from google.appengine.runtime import apiproxy_errors
from google.net.proto2.python.public import message










assert (('google.appengine.api.apiproxy_stub_map' in sys.modules) ==
        apiproxy_stub_map_loaded), ('apiproxy_stub_map imported which breaks '
                                    'apiproxy_stub_map.GetDefaultAPIProxy due '
                                    'to circular import.')



MEMCACHE_UNAVAILABLE = 9










OK                =  0
RPC_FAILED        =  1
CALL_NOT_FOUND    =  2
ARGUMENT_ERROR    =  3
DEADLINE_EXCEEDED =  4
CANCELLED         =  5
APPLICATION_ERROR =  6
OTHER_ERROR       =  7
OVER_QUOTA        =  8
REQUEST_TOO_LARGE =  9
CAPABILITY_DISABLED = 10
FEATURE_DISABLED = 11
RESPONSE_TOO_LARGE = 12


_ExceptionsMap = {
  RPC_FAILED:
  (apiproxy_errors.RPCFailedError,
   "The remote RPC to the application server failed for the call %s.%s()."),
  CALL_NOT_FOUND:
  (apiproxy_errors.CallNotFoundError,
   "The API package '%s' or call '%s()' was not found."),
  ARGUMENT_ERROR:
  (apiproxy_errors.ArgumentError,
   "An error occurred parsing (locally or remotely) the arguments to %s.%s()."),
  DEADLINE_EXCEEDED:
  (apiproxy_errors.DeadlineExceededError,
   "The API call %s.%s() took too long to respond and was cancelled."),
  CANCELLED:
  (apiproxy_errors.CancelledError,
   "The API call %s.%s() was explicitly cancelled."),
  OTHER_ERROR:
  (apiproxy_errors.Error,
   "An error occurred for the API request %s.%s()."),
  OVER_QUOTA:
  (apiproxy_errors.OverQuotaError,
  "The API call %s.%s() required more quota than is available."),
  REQUEST_TOO_LARGE:
  (apiproxy_errors.RequestTooLargeError,
  "The request to API call %s.%s() was too large."),
  RESPONSE_TOO_LARGE:
  (apiproxy_errors.ResponseTooLargeError,
  "The response from API call %s.%s() was too large."),









}



PROTO_BASE_CLASSES = (ProtocolBuffer.ProtocolMessage, message.Message)


class RPC(apiproxy_rpc.RPC):
  """A RPC object, suitable for talking to remote services.

  Each instance of this object can be used only once, and should not be reused.

  Stores the data members and methods for making RPC calls via the APIProxy.
  """

  def __init__(self, *args, **kargs):
    """Constructor for the RPC object. All arguments are optional, and
    simply set members on the class. These data members will be
    overriden by values passed to MakeCall.
    """
    super(RPC, self).__init__(*args, **kargs)
    self._result_dict = {}

  def _WaitImpl(self):
    """Waits on the API call associated with this RPC. The callback,
    if provided, will be executed before Wait() returns. If this RPC
    is already complete, or if the RPC was never started, this
    function will return immediately.

    Raises:
      InterruptedError if a callback throws an uncaught exception.
    """
    try:
      rpc_completed = _apphosting_runtime___python__apiproxy.Wait(self)
    except (runtime.DeadlineExceededError, apiproxy_errors.InterruptedError):
      raise
    except:
      exc_class, exc, tb = sys.exc_info()
      if (isinstance(exc, SystemError) and
          exc.args[0] == 'uncaught RPC exception'):
        raise
      rpc = None
      if hasattr(exc, "_appengine_apiproxy_rpc"):
        rpc = exc._appengine_apiproxy_rpc

      new_exc = apiproxy_errors.InterruptedError(exc, rpc)
      raise new_exc.__class__, new_exc, tb
    return True

  def _MakeCallImpl(self):
    assert isinstance(self.request, PROTO_BASE_CLASSES), 'not isinstance(%r, %r): sys.modules=%r, sys.path=%r' % (
            self.request.__class__,
            PROTO_BASE_CLASSES,
            sys.modules,
            sys.path)
    assert isinstance(self.response, PROTO_BASE_CLASSES), 'not isinstance(%r, %r): sys.modules=%r, sys.path=%r' % (
            self.response.__class__,
            PROTO_BASE_CLASSES,
            sys.modules,
            sys.path)



    request_data = self.request.SerializeToString()

    self._state = RPC.RUNNING

    _apphosting_runtime___python__apiproxy.MakeCall(
        self.package, self.call, request_data, self._result_dict,
        self._MakeCallDone, self, deadline=(self.deadline or -1))

  def _MakeCallDone(self):
    self._state = RPC.FINISHING
    self.cpu_usage_mcycles = self._result_dict['cpu_usage_mcycles']
    if self._result_dict['error'] == APPLICATION_ERROR:
      appl_err = self._result_dict['application_error']
      if appl_err == MEMCACHE_UNAVAILABLE and self.package == 'memcache':


        self._exception = apiproxy_errors.CapabilityDisabledError(
            'The memcache service is temporarily unavailable. %s'
            % self._result_dict['error_detail'])
      else:

        self._exception = apiproxy_errors.ApplicationError(
            appl_err,
            self._result_dict['error_detail'])
    elif self._result_dict['error'] == CAPABILITY_DISABLED:

      if self._result_dict['error_detail']:
        self._exception = apiproxy_errors.CapabilityDisabledError(
            self._result_dict['error_detail'])
      else:
        self._exception = apiproxy_errors.CapabilityDisabledError(
            "The API call %s.%s() is temporarily unavailable." % (
            self.package, self.call))
    elif self._result_dict['error'] == FEATURE_DISABLED:
      self._exception = apiproxy_errors.FeatureNotEnabledError(
            self._result_dict['error_detail'])
    elif self._result_dict['error'] in _ExceptionsMap:
      exception_entry = _ExceptionsMap[self._result_dict['error']]
      self._exception = exception_entry[0](
          exception_entry[1] % (self.package, self.call))
    else:
      try:
        self.response.ParseFromString(self._result_dict['result_string'])
      except Exception, e:
        self._exception = e
    self._Callback()

def CreateRPC():
  """Create a RPC instance. suitable for talking to remote services.

  Each RPC instance can be used only once, and should not be reused.

  Returns:
    an instance of RPC object
  """
  return RPC()


def MakeSyncCall(package, call, request, response):
  """Makes a synchronous (i.e. blocking) API call within the specified
  package for the specified call method. request and response must be the
  appropriately typed ProtocolBuffers for the API call. An exception is
  thrown if an error occurs when communicating with the system.

  Args:
    See MakeCall above.

  Raises:
    See CheckSuccess() above.
  """
  rpc = CreateRPC()
  rpc.MakeCall(package, call, request, response)
  rpc.Wait()
  rpc.CheckSuccess()


def CancelApiCalls():
  """Cancels all outstanding API calls."""
  _apphosting_runtime___python__apiproxy.CancelApiCalls()


def GetRequestCpuUsage():
  """Returns the number of megacycles used so far by this request.

  Returns:
    The number of megacycles used so far by this request. Does not include CPU
    used by API calls.
  """
  return _apphosting_runtime___python__apiproxy.get_request_cpu_usage()


def GetRequestApiCpuUsage():
  """Returns the number of megacycles used by API calls.

  Returns:
    The number of megacycles used by API calls so far during this request. Does
    not include CPU used by the request code itself.
  """
  return _apphosting_runtime___python__apiproxy.get_request_api_cpu_usage()
