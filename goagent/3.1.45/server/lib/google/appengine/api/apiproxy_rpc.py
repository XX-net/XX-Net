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




"""Base class for implementing RPC of API proxy stubs."""









import sys


class RPC(object):
  """Base class for implementing RPC of API proxy stubs.

  To implement a RPC to make real asynchronous API call:
    - Extend this class.
    - Override _MakeCallImpl and/or _WaitImpl to do a real asynchronous call.
  """

  IDLE = 0
  RUNNING = 1
  FINISHING = 2

  def __init__(self, package=None, call=None, request=None, response=None,
               callback=None, deadline=None, stub=None):
    """Constructor for the RPC object.

    All arguments are optional, and simply set members on the class.
    These data members will be overriden by values passed to MakeCall.

    Args:
      package: string, the package for the call
      call: string, the call within the package
      request: ProtocolMessage instance, appropriate for the arguments
      response: ProtocolMessage instance, appropriate for the response
      callback: callable, called when call is complete
      deadline: A double specifying the deadline for this call as the number of
                seconds from the current time. Ignored if non-positive.
      stub: APIProxyStub instance, used in default _WaitImpl to do real call
    """
    self.__exception = None
    self.__state = RPC.IDLE
    self.__traceback = None

    self.package = package
    self.call = call
    self.request = request
    self.response = response
    self.callback = callback
    self.deadline = deadline
    self.stub = stub
    self.cpu_usage_mcycles = 0

  def Clone(self):
    """Make a shallow copy of this instances attributes, excluding methods.

    This is usually used when an RPC has been specified with some configuration
    options and is being used as a template for multiple RPCs outside of a
    developer's easy control.
    """
    if self.state != RPC.IDLE:
      raise AssertionError('Cannot clone a call already in progress')

    clone = self.__class__()
    for k, v in self.__dict__.iteritems():
      setattr(clone, k, v)
    return clone

  def MakeCall(self, package=None, call=None, request=None, response=None,
               callback=None, deadline=None):
    """Makes an asynchronous (i.e. non-blocking) API call within the
    specified package for the specified call method.

    It will call the _MakeRealCall to do the real job.

    Args:
      Same as constructor; see __init__.

    Raises:
      TypeError or AssertionError if an argument is of an invalid type.
      AssertionError or RuntimeError is an RPC is already in use.
    """
    self.callback = callback or self.callback
    self.package = package or self.package
    self.call = call or self.call
    self.request = request or self.request
    self.response = response or self.response
    self.deadline = deadline or self.deadline

    assert self.__state is RPC.IDLE, ('RPC for %s.%s has already been started' %
                                      (self.package, self.call))
    assert self.callback is None or callable(self.callback)
    self._MakeCallImpl()

  def Wait(self):
    """Waits on the API call associated with this RPC."""
    rpc_completed = self._WaitImpl()

    assert rpc_completed, ('RPC for %s.%s was not completed, and no other '
                           'exception was raised ' % (self.package, self.call))

  def CheckSuccess(self):
    """If there was an exception, raise it now.

    Raises:
      Exception of the API call or the callback, if any.
    """
    if self.exception and self.__traceback:
      raise self.exception.__class__, self.exception, self.__traceback
    elif self.exception:
      raise self.exception

  @property
  def exception(self):
    return self.__exception

  @property
  def state(self):
    return self.__state

  def _MakeCallImpl(self):
    """Override this method to implement a real asynchronous call rpc."""
    self.__state = RPC.RUNNING

  def _WaitImpl(self):
    """Override this method to implement a real asynchronous call rpc.

    Returns:
      True if the async call was completed successfully.
    """
    try:
      try:
        self.stub.MakeSyncCall(self.package, self.call,
                               self.request, self.response)
      except Exception:
        _, self.__exception, self.__traceback = sys.exc_info()
    finally:
      self.__state = RPC.FINISHING
      self.__Callback()

    return True

  def __Callback(self):
    if self.callback:
      try:
        self.callback()
      except:
        _, self.__exception, self.__traceback = sys.exc_info()
        self.__exception._appengine_apiproxy_rpc = self
        raise
