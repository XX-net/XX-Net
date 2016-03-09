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




"""Client-side transfer throttling for use with remote_api_stub.

This module is used to configure rate limiting for programs accessing
AppEngine services through remote_api.

See the Throttle class for more information.

An example with throttling:
---
from google.appengine.ext import db
from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.ext.remote_api import throttle
from myapp import models
import getpass
import threading

def auth_func():
  return (raw_input('Username:'), getpass.getpass('Password:'))

remote_api_stub.ConfigureRemoteDatastore('my-app', '/remote_api', auth_func)
full_throttle = throttle.DefaultThrottle(multiplier=1.0)
throttle.ThrottleRemoteDatastore(full_throttle)

# Register any threads that will be using the datastore with the throttler
full_throttle.Register(threading.currentThread())

# Now you can access the remote datastore just as if your code was running on
# App Engine, and you don't need to worry about exceeding quota limits!

houses = models.House.all().fetch(100)
for a_house in houses:
  a_house.doors += 1
db.put(houses)
---

This example limits usage to the default free quota levels.  The multiplier
kwarg to throttle.DefaultThrottle can be used to scale the throttle levels
higher or lower.

Throttles can also be constructed directly for more control over the limits
for different operations.  See the Throttle class and the constants following
it for details.
"""



import functools
import logging
import os
import threading
import time
import urllib2
import urlparse

_HTTPLIB2_AVAILABLE = False

try:
  import httplib2
  from google.appengine.tools import appengine_rpc_httplib2
  _HTTPLIB2_AVAILABLE = True
except ImportError:
  pass


if os.environ.get('APPENGINE_RUNTIME') == 'python27':
  from google.appengine.api import apiproxy_stub_map
else:
  from google.appengine.api import apiproxy_stub_map

from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.tools import appengine_rpc

logger = logging.getLogger('google.appengine.ext.remote_api.throttle')


MINIMUM_THROTTLE_SLEEP_DURATION = 0.001


class Error(Exception):
  """Base class for errors in this module."""


class ThreadNotRegisteredError(Error):
  """An unregistered thread has accessed the throttled datastore stub."""


class UnknownThrottleNameError(Error):
  """A transfer was added for an unknown throttle name."""


def InterruptibleSleep(sleep_time):
  """Puts thread to sleep, checking this threads exit_flag four times a second.

  Args:
    sleep_time: Time to sleep.
  """
  slept = 0.0
  epsilon = .0001
  thread = threading.currentThread()
  while slept < sleep_time - epsilon:
    remaining = sleep_time - slept
    this_sleep_time = min(remaining, 0.25)
    time.sleep(this_sleep_time)
    slept += this_sleep_time
    if hasattr(thread, 'exit_flag') and thread.exit_flag:
      return


class Throttle(object):
  """A base class for upload rate throttling.

  Transferring large number of entities, too quickly, could trigger
  quota limits and cause the transfer process to halt.  In order to
  stay within the application's quota, we throttle the data transfer
  to a specified limit (across all transfer threads).

  This class tracks a moving average of some aspect of the transfer
  rate (bandwidth, records per second, http connections per
  second). It keeps two windows of counts of bytes transferred, on a
  per-thread basis. One block is the "current" block, and the other is
  the "prior" block. It will rotate the counts from current to prior
  when ROTATE_PERIOD has passed.  Thus, the current block will
  represent from 0 seconds to ROTATE_PERIOD seconds of activity
  (determined by: time.time() - self.last_rotate).  The prior block
  will always represent a full ROTATE_PERIOD.

  Sleeping is performed just before a transfer of another block, and is
  based on the counts transferred *before* the next transfer. It really
  does not matter how much will be transferred, but only that for all the
  data transferred SO FAR that we have interspersed enough pauses to
  ensure the aggregate transfer rate is within the specified limit.

  These counts are maintained on a per-thread basis, so we do not require
  any interlocks around incrementing the counts. There IS an interlock on
  the rotation of the counts because we do not want multiple threads to
  multiply-rotate the counts.

  There are various race conditions in the computation and collection
  of these counts. We do not require precise values, but simply to
  keep the overall transfer within the bandwidth limits. If a given
  pause is a little short, or a little long, then the aggregate delays
  will be correct.
  """

  ROTATE_PERIOD = 600

  def __init__(self,
               get_time=time.time,
               thread_sleep=InterruptibleSleep,
               layout=None):
    self.get_time = get_time
    self.thread_sleep = thread_sleep

    self.start_time = get_time()
    self.transferred = {}
    self.prior_block = {}
    self.totals = {}
    self.throttles = {}

    self.last_rotate = {}
    self.rotate_mutex = {}
    if layout:
      self.AddThrottles(layout)

  def AddThrottle(self, name, limit):
    self.throttles[name] = limit
    self.transferred[name] = {}
    self.prior_block[name] = {}
    self.totals[name] = {}
    self.last_rotate[name] = self.get_time()
    self.rotate_mutex[name] = threading.Lock()

  def AddThrottles(self, layout):
    for key, value in layout.iteritems():
      self.AddThrottle(key, value)

  def Register(self, thread):
    """Register this thread with the throttler."""
    thread_id = id(thread)
    for throttle_name in self.throttles.iterkeys():
      self.transferred[throttle_name][thread_id] = 0
      self.prior_block[throttle_name][thread_id] = 0
      self.totals[throttle_name][thread_id] = 0

  def VerifyThrottleName(self, throttle_name):
    if throttle_name not in self.throttles:
      raise UnknownThrottleNameError('%s is not a registered throttle' %
                                     throttle_name)

  def AddTransfer(self, throttle_name, token_count):
    """Add a count to the amount this thread has transferred.

    Each time a thread transfers some data, it should call this method to
    note the amount sent. The counts may be rotated if sufficient time
    has passed since the last rotation.

    Args:
      throttle_name: The name of the throttle to add to.
      token_count: The number to add to the throttle counter.
    """
    self.VerifyThrottleName(throttle_name)
    transferred = self.transferred[throttle_name]
    try:
      transferred[id(threading.currentThread())] += token_count
    except KeyError:
      thread = threading.currentThread()
      raise ThreadNotRegisteredError(
          'Unregistered thread accessing throttled datastore stub: id = %s\n'
          'name = %s' % (id(thread), thread.getName()))


    if self.last_rotate[throttle_name] + self.ROTATE_PERIOD < self.get_time():
      self._RotateCounts(throttle_name)

  def Sleep(self, throttle_name=None):
    """Possibly sleep in order to limit the transfer rate.

    Note that we sleep based on *prior* transfers rather than what we
    may be about to transfer. The next transfer could put us under/over
    and that will be rectified *after* that transfer. Net result is that
    the average transfer rate will remain within bounds. Spiky behavior
    or uneven rates among the threads could possibly bring the transfer
    rate above the requested limit for short durations.

    Args:
      throttle_name: The name of the throttle to sleep on.  If None or
        omitted, then sleep on all throttles.
    """
    if throttle_name is None:
      for throttle_name in self.throttles:
        self.Sleep(throttle_name=throttle_name)
      return

    self.VerifyThrottleName(throttle_name)

    thread = threading.currentThread()


    while True:


      duration = self.get_time() - self.last_rotate[throttle_name]




      total = 0
      for count in self.prior_block[throttle_name].values():
        total += count



      if total:
        duration += self.ROTATE_PERIOD



      for count in self.transferred[throttle_name].values():
        total += count











      sleep_time = self._SleepTime(total, self.throttles[throttle_name],
                                   duration)

      if sleep_time < MINIMUM_THROTTLE_SLEEP_DURATION:
        break

      logger.debug('[%s] Throttling on %s. Sleeping for %.1f ms '
                   '(duration=%.1f ms, total=%d)',
                   thread.getName(), throttle_name,
                   sleep_time * 1000, duration * 1000, total)
      self.thread_sleep(sleep_time)


      if thread.exit_flag:
        break
      self._RotateCounts(throttle_name)

  def _SleepTime(self, total, limit, duration):
    """Calculate the time to sleep on a throttle.

    Args:
      total: The total amount transferred.
      limit: The amount per second that is allowed to be sent.
      duration: The amount of time taken to send the total.

    Returns:
      A float for the amount of time to sleep.
    """
    if not limit:
      return 0.0
    return max(0.0, (total / limit) - duration)

  def _RotateCounts(self, throttle_name):
    """Rotate the transfer counters.

    If sufficient time has passed, then rotate the counters from active to
    the prior-block of counts.

    This rotation is interlocked to ensure that multiple threads do not
    over-rotate the counts.

    Args:
      throttle_name: The name of the throttle to rotate.
    """
    self.VerifyThrottleName(throttle_name)
    self.rotate_mutex[throttle_name].acquire()
    try:


      next_rotate_time = self.last_rotate[throttle_name] + self.ROTATE_PERIOD
      if next_rotate_time >= self.get_time():
        return

      for name, count in self.transferred[throttle_name].items():

















        self.prior_block[throttle_name][name] = count
        self.transferred[throttle_name][name] = 0

        self.totals[throttle_name][name] += count

      self.last_rotate[throttle_name] = self.get_time()

    finally:
      self.rotate_mutex[throttle_name].release()

  def TotalTransferred(self, throttle_name):
    """Return the total transferred, and over what period.

    Args:
      throttle_name: The name of the throttle to total.

    Returns:
      A tuple of the total count and running time for the given throttle name.
    """
    total = 0

    for count in self.totals[throttle_name].values():
      total += count
    for count in self.transferred[throttle_name].values():
      total += count
    return total, self.get_time() - self.start_time



BANDWIDTH_UP = 'http-bandwidth-up'
BANDWIDTH_DOWN = 'http-bandwidth-down'
REQUESTS = 'http-requests'
HTTPS_BANDWIDTH_UP = 'https-bandwidth-up'
HTTPS_BANDWIDTH_DOWN = 'https-bandwidth-down'
HTTPS_REQUESTS = 'https-requests'
DATASTORE_CALL_COUNT = 'datastore-call-count'
ENTITIES_FETCHED = 'entities-fetched'
ENTITIES_MODIFIED = 'entities-modified'
INDEX_MODIFICATIONS = 'index-modifications'



DEFAULT_LIMITS = {
    BANDWIDTH_UP: 100000,
    BANDWIDTH_DOWN: 100000,
    REQUESTS: 15,
    HTTPS_BANDWIDTH_UP: 100000,
    HTTPS_BANDWIDTH_DOWN: 100000,
    HTTPS_REQUESTS: 15,
    DATASTORE_CALL_COUNT: 120,
    ENTITIES_FETCHED: 400,
    ENTITIES_MODIFIED: 400,
    INDEX_MODIFICATIONS: 1600,
}


NO_LIMITS = {
    BANDWIDTH_UP: None,
    BANDWIDTH_DOWN: None,
    REQUESTS: None,
    HTTPS_BANDWIDTH_UP: None,
    HTTPS_BANDWIDTH_DOWN: None,
    HTTPS_REQUESTS: None,
    DATASTORE_CALL_COUNT: None,
    ENTITIES_FETCHED: None,
    ENTITIES_MODIFIED: None,
    INDEX_MODIFICATIONS: None,
}


def DefaultThrottle(multiplier=1.0):
  """Return a Throttle instance with multiplier * the quota limits."""
  layout = dict([(name, multiplier * limit)
                 for (name, limit) in DEFAULT_LIMITS.iteritems()])
  return Throttle(layout=layout)


class ThrottleHandler(urllib2.BaseHandler):
  """A urllib2 handler for http and https requests that adds to a throttle."""

  def __init__(self, throttle):
    """Initialize a ThrottleHandler.

    Args:
      throttle: A Throttle instance to call for bandwidth and http/https request
        throttling.
    """
    self.throttle = throttle

  def _CalculateRequestSize(self, req):
    """Calculates the request size.

    May be overriden to support different types of requests.

    Args:
      req: A urllib2.Request.

    Returns:
      the size of the request, in bytes.
    """
    (unused_scheme,
     unused_host_port, url_path,
     unused_query, unused_fragment) = urlparse.urlsplit(req.get_full_url())
    size = len('%s %s HTTP/1.1\n' % (req.get_method(), url_path))
    size += self._CalculateHeaderSize(req.headers)
    size += self._CalculateHeaderSize(req.unredirected_hdrs)


    data = req.get_data()
    if data:
      size += len(data)
    return size

  def _CalculateResponseSize(self, res):
    """Calculates the response size.

    May be overriden to support different types of response.

    Args:
      res: A urllib2.Response.

    Returns:
      the size of the response, in bytes.
    """
    content = res.read()

    def ReturnContent():
      return content

    res.read = ReturnContent


    return len(content) + self._CalculateHeaderSize(dict(res.info().items()))

  def _CalculateHeaderSize(self, headers):
    """Calculates the size of the headers.

    Args:
      headers: A dict of header values.

    Returns:
      the size of the headers.
    """
    return sum([len('%s: %s\n' % (key, value))
                for key, value in headers.iteritems()])

  def AddRequest(self, throttle_name, req):
    """Add to bandwidth throttle for given request.

    Args:
      throttle_name: The name of the bandwidth throttle to add to.
      req: The request whose size will be added to the throttle.
    """
    self.throttle.AddTransfer(throttle_name, self._CalculateRequestSize(req))

  def AddResponse(self, throttle_name, res):
    """Add to bandwidth throttle for given response.

    Args:
      throttle_name: The name of the bandwidth throttle to add to.
      res: The response whose size will be added to the throttle.
    """
    self.throttle.AddTransfer(throttle_name, self._CalculateResponseSize(res))

  def http_request(self, req):
    """Process an HTTP request.

    If the throttle is over quota, sleep first.  Then add request size to
    throttle before returning it to be sent.

    Args:
      req: A urllib2.Request object.

    Returns:
      The request passed in.
    """

    self.throttle.Sleep(BANDWIDTH_UP)
    self.throttle.Sleep(BANDWIDTH_DOWN)

    self.AddRequest(BANDWIDTH_UP, req)
    return req

  def https_request(self, req):
    """Process an HTTPS request.

    If the throttle is over quota, sleep first.  Then add request size to
    throttle before returning it to be sent.

    Args:
      req: A urllib2.Request object.

    Returns:
      The request passed in.
    """

    self.throttle.Sleep(HTTPS_BANDWIDTH_UP)
    self.throttle.Sleep(HTTPS_BANDWIDTH_DOWN)

    self.AddRequest(HTTPS_BANDWIDTH_UP, req)
    return req

  def http_response(self, unused_req, res):
    """Process an HTTP response.

    The size of the response is added to the bandwidth throttle and the request
    throttle is incremented by one.

    Args:
      unused_req: The urllib2 request for this response.
      res: A urllib2 response object.

    Returns:
      The response passed in.
    """

    self.AddResponse(BANDWIDTH_DOWN, res)

    self.throttle.AddTransfer(REQUESTS, 1)
    return res

  def https_response(self, unused_req, res):
    """Process an HTTPS response.

    The size of the response is added to the bandwidth throttle and the request
    throttle is incremented by one.

    Args:
      unused_req: The urllib2 request for this response.
      res: A urllib2 response object.

    Returns:
      The response passed in.
    """

    self.AddResponse(HTTPS_BANDWIDTH_DOWN, res)

    self.throttle.AddTransfer(HTTPS_REQUESTS, 1)
    return res


class ThrottledHttpRpcServer(appengine_rpc.HttpRpcServer):
  """Provides a simplified RPC-style interface for HTTP requests.

  This RPC server uses a Throttle to prevent exceeding quotas.
  """

  def __init__(self, throttle, *args, **kwargs):
    """Initialize a ThrottledHttpRpcServer.

    Also sets request_manager.rpc_server to the ThrottledHttpRpcServer instance.

    Args:
      throttle: A Throttles instance.
      args: Positional arguments to pass through to
        appengine_rpc.HttpRpcServer.__init__
      kwargs: Keyword arguments to pass through to
        appengine_rpc.HttpRpcServer.__init__
    """
    self.throttle = throttle
    appengine_rpc.HttpRpcServer.__init__(self, *args, **kwargs)

  def _GetOpener(self):
    """Returns an OpenerDirector that supports cookies and ignores redirects.

    Returns:
      A urllib2.OpenerDirector object.
    """
    opener = appengine_rpc.HttpRpcServer._GetOpener(self)
    opener.add_handler(ThrottleHandler(self.throttle))

    return opener




if _HTTPLIB2_AVAILABLE:

  class ThrottledHttpRpcServerOAuth2(
      appengine_rpc_httplib2.HttpRpcServerOAuth2):

    def __init__(self, throttle, *args, **kwargs):
      kwargs['http_class'] = functools.partial(_ThrottledHttp, throttle)
      super(ThrottledHttpRpcServerOAuth2, self).__init__(*args, **kwargs)

  class _ThrottledHttp(httplib2.Http):
    """An implementation of Http which throttles requests."""

    def __init__(self, throttle, *args, **kwargs):
      self.throttle_handler = _HttpThrottleHandler(throttle)
      super(_ThrottledHttp, self).__init__(*args, **kwargs)

    def request(self, uri, method='GET', body=None, headers=None,
                redirections=httplib2.DEFAULT_MAX_REDIRECTS,
                connection_type=None):
      scheme = urlparse.urlparse(uri).scheme
      request = (uri, method, body, headers)
      if scheme == 'http':
        self.throttle_handler.http_request(request)
      elif scheme == 'https':
        self.throttle_handler.https_request(request)

      response = super(_ThrottledHttp, self).request(
          uri, method, body, headers, redirections, connection_type)

      if scheme == 'http':
        self.throttle_handler.http_response(request, response)
      elif scheme == 'https':
        self.throttle_handler.https_response(request, response)

      return response


class _HttpThrottleHandler(ThrottleHandler):
  """A ThrottleHandler designed to be used by ThrottledHttp."""

  def _CalculateRequestSize(self, req):
    """Calculates the request size.

    Args:
      req: A tuple of (uri, method name, request body, header map)
    Returns:
      the size of the request, in bytes.
    """
    uri, method, body, headers = req
    (unused_scheme,
     unused_host_port, url_path,
     unused_query, unused_fragment) = urlparse.urlsplit(uri)
    size = len('%s %s HTTP/1.1\n' % (method, url_path))
    size += self._CalculateHeaderSize(headers)


    if body:
      size += len(body)
    return size

  def _CalculateResponseSize(self, res):
    """Calculates the response size.

    May be overriden to support different types of response.

    Args:
      res: A tuple of (header map, response body).

    Returns:
      the size of the response, in bytes.
    """
    headers, content = res
    return len(content) + self._CalculateHeaderSize(headers)


class ThrottledHttpRpcServerFactory(object):
  """A factory to produce ThrottledHttpRpcServer for a given throttle."""

  def __init__(self, throttle, throttle_class=None):
    """Initialize a ThrottledHttpRpcServerFactory.

    Args:
      throttle: A Throttle instance to use for the ThrottledHttpRpcServer.
      throttle_class: A class to use instead of the default
        ThrottledHttpRpcServer.

    Returns:
      A factory to produce a ThrottledHttpRpcServer.
    """
    self.throttle = throttle
    self.throttle_class = throttle_class

  def __call__(self, *args, **kwargs):
    """Factory to produce a ThrottledHttpRpcServer.

    Args:
      args: Positional args to pass to ThrottledHttpRpcServer.
      kwargs: Keyword args to pass to ThrottledHttpRpcServer.

    Returns:
      A ThrottledHttpRpcServer instance.
    """

    kwargs['account_type'] = 'HOSTED_OR_GOOGLE'

    kwargs['save_cookies'] = True
    if self.throttle_class:
      rpc_server = self.throttle_class(self.throttle, *args, **kwargs)
    else:
      rpc_server = ThrottledHttpRpcServer(self.throttle, *args, **kwargs)
    return rpc_server


class Throttler(object):
  def PrehookHandler(self, service, call, request, response):
    handler = getattr(self, '_Prehook_' + call, None)
    if handler:
      handler(request, response)

  def PosthookHandler(self, service, call, request, response):
    handler = getattr(self, '_Posthook_' + call, None)
    if handler:
      handler(request, response)


def SleepHandler(*throttle_names):
  def SleepOnThrottles(self, request, response):
    if throttle_names:
      for throttle_name in throttle_names:
        self._DatastoreThrottler__throttle.Sleep(throttle_name)
    else:
      self._DatastoreThrottler__throttle.Sleep()
  return SleepOnThrottles


class DatastoreThrottler(Throttler):
  def __init__(self, throttle):
    Throttler.__init__(self)
    self.__throttle = throttle

  def AddCost(self, cost_proto):
    """Add costs from the Cost protobuf."""
    self.__throttle.AddTransfer(INDEX_MODIFICATIONS, cost_proto.index_writes())
    self.__throttle.AddTransfer(ENTITIES_MODIFIED, cost_proto.entity_writes())
    self.__throttle.AddTransfer(BANDWIDTH_UP, cost_proto.entity_write_bytes())



  _Prehook_Put = SleepHandler(ENTITIES_MODIFIED,
                              INDEX_MODIFICATIONS,
                              BANDWIDTH_UP)

  def _Posthook_Put(self, request, response):
    self.AddCost(response.cost())



  _Prehook_Get = SleepHandler(ENTITIES_FETCHED)

  def _Posthook_Get(self, request, response):
    self.__throttle.AddTransfer(ENTITIES_FETCHED, response.entity_size())



  _Prehook_RunQuery = SleepHandler(ENTITIES_FETCHED)

  def _Posthook_RunQuery(self, request, response):

    if not response.keys_only():
      self.__throttle.AddTransfer(ENTITIES_FETCHED, response.result_size())



  _Prehook_Next = SleepHandler(ENTITIES_FETCHED)

  def _Posthook_Next(self, request, response):

    if not response.keys_only():
      self.__throttle.AddTransfer(ENTITIES_FETCHED, response.result_size())



  _Prehook_Delete = SleepHandler(ENTITIES_MODIFIED, INDEX_MODIFICATIONS)

  def _Posthook_Delete(self, request, response):
    self.AddCost(response.cost())



  _Prehook_Commit = SleepHandler()

  def _Posthook_Commit(self, request, response):
    self.AddCost(response.cost())


def ThrottleRemoteDatastore(throttle, remote_datastore_stub=None):
  """Install the given throttle for the remote datastore stub.

  Args:
    throttle: A Throttle instance to limit datastore access rates
    remote_datastore_stub: The datstore stub instance to throttle, for
      testing purposes.
  """
  if not remote_datastore_stub:
    remote_datastore_stub = apiproxy_stub_map.apiproxy.GetStub('datastore_v3')
  if not isinstance(remote_datastore_stub, remote_api_stub.RemoteDatastoreStub):
    raise remote_api_stub.ConfigurationError('remote_api is not configured.')
  throttler = DatastoreThrottler(throttle)
  remote_datastore_stub._PreHookHandler = throttler.PrehookHandler
  remote_datastore_stub._PostHookHandler = throttler.PosthookHandler
