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




"""Stub version of the memcache API, keeping all data in process memory."""









import logging
import time

from google.appengine.api import apiproxy_stub
from google.appengine.api import memcache
from google.appengine.api.memcache import memcache_service_pb
from google.appengine.runtime import apiproxy_errors


MemcacheSetResponse = memcache_service_pb.MemcacheSetResponse
MemcacheSetRequest = memcache_service_pb.MemcacheSetRequest
MemcacheIncrementRequest = memcache_service_pb.MemcacheIncrementRequest
MemcacheIncrementResponse = memcache_service_pb.MemcacheIncrementResponse
MemcacheDeleteResponse = memcache_service_pb.MemcacheDeleteResponse


MAX_REQUEST_SIZE = 32 << 20


class CacheEntry(object):
  """An entry in the cache."""

  def __init__(self, value, expiration, flags, cas_id, gettime):
    """Initializer.

    Args:
      value: String containing the data for this entry.
      expiration: Number containing the expiration time or offset in seconds
        for this entry.
      flags: Opaque flags used by the memcache implementation.
      cas_id: Unique Compare-And-Set ID.
      gettime: Used for testing. Function that works like time.time().
    """
    assert isinstance(value, basestring)
    assert len(value) <= memcache.MAX_VALUE_SIZE
    assert isinstance(expiration, (int, long))

    self._gettime = gettime
    self.value = value
    self.flags = flags
    self.cas_id = cas_id
    self.created_time = self._gettime()
    self.will_expire = expiration != 0
    self.locked = False
    self._SetExpiration(expiration)

  def _SetExpiration(self, expiration):
    """Sets the expiration for this entry.

    Args:
      expiration: Number containing the expiration time or offset in seconds
        for this entry. If expiration is above one month, then it's considered
        an absolute time since the UNIX epoch.
    """
    if expiration > (86400 * 30):
      self.expiration_time = expiration
    else:
      self.expiration_time = self._gettime() + expiration

  def CheckExpired(self):
    """Returns True if this entry has expired; False otherwise."""
    return self.will_expire and self._gettime() >= self.expiration_time

  def ExpireAndLock(self, timeout):
    """Marks this entry as deleted and locks it for the expiration time.

    Used to implement memcache's delete timeout behavior.

    Args:
      timeout: Parameter originally passed to memcache.delete or
        memcache.delete_multi to control deletion timeout.
    """
    self.will_expire = True
    self.locked = True
    self._SetExpiration(timeout)

  def CheckLocked(self):
    """Returns True if this entry was deleted but has not yet timed out."""
    return self.locked and not self.CheckExpired()


class MemcacheServiceStub(apiproxy_stub.APIProxyStub):
  """Python only memcache service stub.

  This stub keeps all data in the local process' memory, not in any
  external servers.
  """

  THREADSAFE = True

  def __init__(self, gettime=time.time, service_name='memcache'):
    """Initializer.

    Args:
      gettime: time.time()-like function used for testing.
      service_name: Service name expected for all calls.
    """
    super(MemcacheServiceStub, self).__init__(service_name,
                                              max_request_size=MAX_REQUEST_SIZE)
    self._next_cas_id = 1
    self._gettime = lambda: int(gettime())
    self._ResetStats()


    self._the_cache = {}






  def _ResetStats(self):
    """Resets statistics information.

    Must be called while the current thread holds self._mutex (with an exception
    for __init__).
    """

    self._hits = 0
    self._misses = 0
    self._byte_hits = 0

    self._cache_creation_time = self._gettime()

  @apiproxy_stub.Synchronized
  def _GetKey(self, namespace, key):
    """Retrieves a CacheEntry from the cache if it hasn't expired.

    Does not take deletion timeout into account.

    Args:
      namespace: The namespace that keys are stored under.
      key: The key to retrieve from the cache.

    Returns:
      The corresponding CacheEntry instance, or None if it was not found or
      has already expired.
    """
    namespace_dict = self._the_cache.get(namespace, None)
    if namespace_dict is None:
      return None
    entry = namespace_dict.get(key, None)
    if entry is None:
      return None
    elif entry.CheckExpired():
      del namespace_dict[key]
      return None
    else:
      return entry

  @apiproxy_stub.Synchronized
  def _Dynamic_Get(self, request, response):
    """Implementation of MemcacheService::Get().

    Args:
      request: A MemcacheGetRequest.
      response: A MemcacheGetResponse.
    """
    namespace = request.name_space()
    keys = set(request.key_list())
    for key in keys:
      entry = self._GetKey(namespace, key)
      if entry is None or entry.CheckLocked():
        self._misses += 1
        continue
      self._hits += 1
      self._byte_hits += len(entry.value)
      item = response.add_item()
      item.set_key(key)
      item.set_value(entry.value)
      item.set_flags(entry.flags)
      if request.for_cas():
        item.set_cas_id(entry.cas_id)

  @apiproxy_stub.Synchronized
  def _Dynamic_Set(self, request, response):
    """Implementation of MemcacheService::Set().

    Args:
      request: A MemcacheSetRequest.
      response: A MemcacheSetResponse.
    """
    namespace = request.name_space()
    for item in request.item_list():
      key = item.key()
      set_policy = item.set_policy()
      old_entry = self._GetKey(namespace, key)

      set_status = MemcacheSetResponse.NOT_STORED
      if ((set_policy == MemcacheSetRequest.SET) or
          (set_policy == MemcacheSetRequest.ADD and old_entry is None) or
          (set_policy == MemcacheSetRequest.REPLACE and old_entry is not None)):


        if (old_entry is None or
            set_policy == MemcacheSetRequest.SET
            or not old_entry.CheckLocked()):
          set_status = MemcacheSetResponse.STORED

      elif (set_policy == MemcacheSetRequest.CAS and item.has_cas_id()):
        if old_entry is None or old_entry.CheckLocked():
          set_status = MemcacheSetResponse.NOT_STORED
        elif old_entry.cas_id != item.cas_id():
          set_status = MemcacheSetResponse.EXISTS
        else:
          set_status = MemcacheSetResponse.STORED

      if set_status == MemcacheSetResponse.STORED:
        if namespace not in self._the_cache:
          self._the_cache[namespace] = {}
        self._the_cache[namespace][key] = CacheEntry(item.value(),
                                                     item.expiration_time(),
                                                     item.flags(),
                                                     self._next_cas_id,
                                                     gettime=self._gettime)
        self._next_cas_id += 1

      response.add_set_status(set_status)

  @apiproxy_stub.Synchronized
  def _Dynamic_Delete(self, request, response):
    """Implementation of MemcacheService::Delete().

    Args:
      request: A MemcacheDeleteRequest.
      response: A MemcacheDeleteResponse.
    """
    namespace = request.name_space()
    for item in request.item_list():
      key = item.key()
      entry = self._GetKey(namespace, key)

      delete_status = MemcacheDeleteResponse.DELETED
      if entry is None:
        delete_status = MemcacheDeleteResponse.NOT_FOUND
      elif item.delete_time() == 0:
        del self._the_cache[namespace][key]
      else:

        entry.ExpireAndLock(item.delete_time())

      response.add_delete_status(delete_status)

  @apiproxy_stub.Synchronized
  def _internal_increment(self, namespace, request):
    """Internal function for incrementing from a MemcacheIncrementRequest.

    Args:
      namespace: A string containing the namespace for the request, if any.
        Pass an empty string if there is no namespace.
      request: A MemcacheIncrementRequest instance.

    Returns:
      An integer or long if the offset was successful, None on error.
    """
    key = request.key()
    entry = self._GetKey(namespace, key)
    if entry is None or entry.CheckLocked():
      if not request.has_initial_value():
        return None
      if namespace not in self._the_cache:
        self._the_cache[namespace] = {}
      flags = 0
      if request.has_initial_flags():
        flags = request.initial_flags()
      self._the_cache[namespace][key] = CacheEntry(str(request.initial_value()),
                                                   expiration=0,
                                                   flags=flags,
                                                   cas_id=self._next_cas_id,
                                                   gettime=self._gettime)
      self._next_cas_id += 1
      entry = self._GetKey(namespace, key)
      assert entry is not None

    try:
      old_value = long(entry.value)
      if old_value < 0:




        raise ValueError
    except ValueError:
      logging.error('Increment/decrement failed: Could not interpret '
                    'value for key = "%s" as an unsigned integer.', key)
      return None

    delta = request.delta()
    if request.direction() == MemcacheIncrementRequest.DECREMENT:
      delta = -delta


    new_value = max(old_value + delta, 0) % (2**64)

    entry.value = str(new_value)
    return new_value

  def _Dynamic_Increment(self, request, response):
    """Implementation of MemcacheService::Increment().

    Args:
      request: A MemcacheIncrementRequest.
      response: A MemcacheIncrementResponse.
    """
    namespace = request.name_space()
    new_value = self._internal_increment(namespace, request)
    if new_value is None:
      raise apiproxy_errors.ApplicationError(
          memcache_service_pb.MemcacheServiceError.UNSPECIFIED_ERROR)
    response.set_new_value(new_value)

  @apiproxy_stub.Synchronized
  def _Dynamic_BatchIncrement(self, request, response):
    """Implementation of MemcacheService::BatchIncrement().

    Args:
      request: A MemcacheBatchIncrementRequest.
      response: A MemcacheBatchIncrementResponse.
    """
    namespace = request.name_space()
    for request_item in request.item_list():
      new_value = self._internal_increment(namespace, request_item)
      item = response.add_item()
      if new_value is None:
        item.set_increment_status(MemcacheIncrementResponse.NOT_CHANGED)
      else:
        item.set_increment_status(MemcacheIncrementResponse.OK)
        item.set_new_value(new_value)

  @apiproxy_stub.Synchronized
  def _Dynamic_FlushAll(self, request, response):
    """Implementation of MemcacheService::FlushAll().

    Args:
      request: A MemcacheFlushRequest.
      response: A MemcacheFlushResponse.
    """
    self._the_cache.clear()
    self._ResetStats()

  @apiproxy_stub.Synchronized
  def _Dynamic_Stats(self, request, response):
    """Implementation of MemcacheService::Stats().

    Args:
      request: A MemcacheStatsRequest.
      response: A MemcacheStatsResponse.
    """
    stats = response.mutable_stats()
    stats.set_hits(self._hits)
    stats.set_misses(self._misses)
    stats.set_byte_hits(self._byte_hits)
    items = 0
    total_bytes = 0
    for namespace in self._the_cache.itervalues():
      items += len(namespace)
      for entry in namespace.itervalues():
        total_bytes += len(entry.value)
    stats.set_items(items)
    stats.set_bytes(total_bytes)


    stats.set_oldest_item_age(self._gettime() - self._cache_creation_time)
