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




"""Memcache API.

Provides memcached-alike API to application developers to store
data in memory when reliable storage via the DataStore API isn't
required and higher performance is desired.
"""








import cPickle
import cStringIO
import hashlib
import math
import types

from google.appengine.api import api_base_pb
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import capabilities
from google.appengine.api import namespace_manager
from google.appengine.api.memcache import memcache_service_pb
from google.appengine.runtime import apiproxy_errors


MemcacheSetResponse = memcache_service_pb.MemcacheSetResponse
MemcacheSetRequest = memcache_service_pb.MemcacheSetRequest

MemcacheGetResponse = memcache_service_pb.MemcacheGetResponse
MemcacheGetRequest = memcache_service_pb.MemcacheGetRequest

MemcacheDeleteResponse = memcache_service_pb.MemcacheDeleteResponse
MemcacheDeleteRequest = memcache_service_pb.MemcacheDeleteRequest

MemcacheIncrementResponse = memcache_service_pb.MemcacheIncrementResponse
MemcacheIncrementRequest = memcache_service_pb.MemcacheIncrementRequest

MemcacheBatchIncrementResponse = memcache_service_pb.MemcacheBatchIncrementResponse
MemcacheBatchIncrementRequest = memcache_service_pb.MemcacheBatchIncrementRequest

MemcacheFlushResponse = memcache_service_pb.MemcacheFlushResponse
MemcacheFlushRequest = memcache_service_pb.MemcacheFlushRequest

MemcacheStatsRequest = memcache_service_pb.MemcacheStatsRequest
MemcacheStatsResponse = memcache_service_pb.MemcacheStatsResponse


DELETE_NETWORK_FAILURE = 0
DELETE_ITEM_MISSING = 1
DELETE_SUCCESSFUL = 2


STORED = MemcacheSetResponse.STORED
NOT_STORED = MemcacheSetResponse.NOT_STORED
ERROR = MemcacheSetResponse.ERROR
EXISTS = MemcacheSetResponse.EXISTS


MAX_KEY_SIZE = 250
MAX_VALUE_SIZE = 10 ** 6


STAT_HITS = 'hits'
STAT_MISSES = 'misses'
STAT_BYTE_HITS = 'byte_hits'
STAT_ITEMS = 'items'
STAT_BYTES = 'bytes'
STAT_OLDEST_ITEM_AGES = 'oldest_item_age'



FLAG_TYPE_MASK = 7
FLAG_COMPRESSED = 1 << 3





TYPE_STR = 0
TYPE_UNICODE = 1
TYPE_PICKLED = 2
TYPE_INT = 3
TYPE_LONG = 4
TYPE_BOOL = 5


CAPABILITY = capabilities.CapabilitySet('memcache')


def _is_pair(obj):
  """Helper to test if something is a pair (2-tuple)."""
  return isinstance(obj, tuple) and len(obj) == 2


def _add_name_space(message, namespace=None):
  """Populate the name_space field in a messagecol buffer.

  Args:
    message: A messagecol buffer supporting the set_name_space() operation.
    namespace: The name of the namespace part. If None, use the
      default namespace. The empty namespace (i.e. '') will clear
      the name_space field.
  """
  if namespace is None:
    namespace = namespace_manager.get_namespace()
  if not namespace:
    message.clear_name_space()
  else:
    message.set_name_space(namespace)


def _key_string(key, key_prefix='', server_to_user_dict=None):
  """Utility function to handle different ways of requesting keys.

  Args:
    key: Either a string or tuple of (shard_number, string).  In Google App
      Engine the sharding is automatic so the shard number is ignored.
      To memcache, the key is just bytes (no defined encoding).
    key_prefix: Optional string prefix to prepend to key.
    server_to_user_dict: Optional dictionary to populate with a mapping of
      server-side key (which includes the key_prefix) to user-supplied key
      (which does not have the prefix).

  Returns:
    The key as a non-unicode string prepended with key_prefix. This is
    the key sent to and stored by the server. If the resulting key is
    longer then MAX_KEY_SIZE, it will be hashed with sha1 and will be
    replaced with the hex representation of the said hash.

  Raises:
    TypeError: If provided key isn't a string or tuple of (int, string)
      or key_prefix.
  """
  if _is_pair(key):
    key = key[1]
  if not isinstance(key, basestring):
    raise TypeError('Key must be a string instance, received %r' % key)
  if not isinstance(key_prefix, basestring):
    raise TypeError('key_prefix must be a string instance, received %r' %
                    key_prefix)





  server_key = key_prefix + key
  if isinstance(server_key, unicode):
    server_key = server_key.encode('utf-8')

  if len(server_key) > MAX_KEY_SIZE:
    server_key = hashlib.sha1(server_key).hexdigest()

  if server_to_user_dict is not None:
    assert isinstance(server_to_user_dict, dict)
    server_to_user_dict[server_key] = key

  return server_key


def _validate_encode_value(value, do_pickle):
  """Utility function to validate and encode server keys and values.

  Args:
    value: Value to store in memcache. If it's a string, it will get passed
      along as-is. If it's a unicode string, it will be marked appropriately,
      such that retrievals will yield a unicode value. If it's any other data
      type, this function will attempt to pickle the data and then store the
      serialized result, unpickling it upon retrieval.
    do_pickle: Callable that takes an object and returns a non-unicode
      string containing the pickled object.

  Returns:
    Tuple (stored_value, flags) where:
      stored_value: The value as a non-unicode string that should be stored
        in memcache.
      flags: An integer with bits set from the FLAG_* constants in this file
        to indicate the encoding of the key and value.

  Raises:
    ValueError: If the encoded value is too large.
    pickle.PicklingError: If the value is not a string and could not be pickled.
    RuntimeError: If a complicated data structure could not be pickled due to
      too many levels of recursion in its composition.
  """
  flags = 0
  stored_value = value

  if isinstance(value, str):
    pass
  elif isinstance(value, unicode):
    stored_value = value.encode('utf-8')
    flags |= TYPE_UNICODE
  elif isinstance(value, bool):


    stored_value = str(int(value))
    flags |= TYPE_BOOL
  elif isinstance(value, int):
    stored_value = str(value)
    flags |= TYPE_INT
  elif isinstance(value, long):
    stored_value = str(value)
    flags |= TYPE_LONG
  else:
    stored_value = do_pickle(value)
    flags |= TYPE_PICKLED





  if len(stored_value) > MAX_VALUE_SIZE:
    raise ValueError('Values may not be more than %d bytes in length; '
                     'received %d bytes' % (MAX_VALUE_SIZE, len(stored_value)))

  return (stored_value, flags)


def _decode_value(stored_value, flags, do_unpickle):
  """Utility function for decoding values retrieved from memcache.

  Args:
    stored_value: The value as a non-unicode string that was stored.
    flags: An integer with bits set from the FLAG_* constants in this file
      that indicate the encoding of the key and value.
    do_unpickle: Callable that takes a non-unicode string object that contains
      a pickled object and returns the pickled object.

  Returns:
    The original object that was stored, be it a normal string, a unicode
    string, int, long, or a Python object that was pickled.

  Raises:
    pickle.UnpicklingError: If the value could not be unpickled.
  """
  assert isinstance(stored_value, str)
  assert isinstance(flags, (int, long))

  type_number = flags & FLAG_TYPE_MASK
  value = stored_value



  if type_number == TYPE_STR:
    return value
  elif type_number == TYPE_UNICODE:
    return unicode(value, 'utf-8')
  elif type_number == TYPE_PICKLED:
    return do_unpickle(value)
  elif type_number == TYPE_BOOL:
    return bool(int(value))
  elif type_number == TYPE_INT:
    return int(value)
  elif type_number == TYPE_LONG:
    return long(value)
  else:
    assert False, "Unknown stored type"
  assert False, "Shouldn't get here."


def create_rpc(deadline=None, callback=None):
  """Creates an RPC object for use with the memcache API.

  Args:
    deadline: Optional deadline in seconds for the operation; the default
      is a system-specific deadline (typically 5 seconds).
    callback: Optional callable to invoke on completion.

  Returns:
    An apiproxy_stub_map.UserRPC object specialized for this service.
  """
  return apiproxy_stub_map.UserRPC('memcache', deadline, callback)


class Client(object):
  """Memcache client object, through which one invokes all memcache operations.

  Several methods are no-ops to retain source-level compatibility
  with the existing popular Python memcache library.

  Any method that takes a 'key' argument will accept that key as a string
  (unicode or not) or a tuple of (hash_value, string) where the hash_value,
  normally used for sharding onto a memcache instance, is instead ignored, as
  Google App Engine deals with the sharding transparently. Keys in memcache are
  just bytes, without a specified encoding. All such methods may raise TypeError
  if provided a bogus key value and a ValueError if the key is too large.

  Any method that takes a 'value' argument will accept as that value any
  string (unicode or not), int, long, or pickle-able Python object, including
  all native types.  You'll get back from the cache the same type that you
  originally put in.

  The Client class is not thread-safe with respect to the gets(), cas() and
  cas_multi() methods (and other compare-and-set-related methods). Therefore,
  Client objects should not be used by more than one thread for CAS purposes.
  Note that the global Client for the module-level functions is okay because it
  does not expose any of the CAS methods.
  """

  def __init__(self, servers=None, debug=0,
               pickleProtocol=cPickle.HIGHEST_PROTOCOL,
               pickler=cPickle.Pickler,
               unpickler=cPickle.Unpickler,
               pload=None,
               pid=None,
               make_sync_call=None,
               _app_id=None):
    """Create a new Client object.

    No parameters are required.

    Arguments:
      servers: Ignored; only for compatibility.
      debug: Ignored; only for compatibility.
      pickleProtocol: Pickle protocol to use for pickling the object.
      pickler: pickle.Pickler sub-class to use for pickling.
      unpickler: pickle.Unpickler sub-class to use for unpickling.
      pload: Callable to use for retrieving objects by persistent id.
      pid: Callable to use for determine the persistent id for objects, if any.
      make_sync_call: Ignored; only for compatibility with an earlier version.
    """





    self._pickler_factory = pickler
    self._unpickler_factory = unpickler
    self._pickle_protocol = pickleProtocol
    self._persistent_id = pid
    self._persistent_load = pload
    self._app_id = _app_id
    self._cas_ids = {}

  def cas_reset(self):
    """Clear the remembered CAS ids."""
    self._cas_ids.clear()

  def _make_async_call(self, rpc, method, request, response,
                       get_result_hook, user_data):
    """Internal helper to schedule an asynchronous RPC.

    Args:
      rpc: None or a UserRPC object.
      method: Method name, e.g. 'Get'.
      request: Request protobuf.
      response: Response protobuf.
      get_result_hook: None or hook function used to process results
        (See UserRPC.make_call() for more info).
      user_data: None or user data for hook function.

    Returns:
      A UserRPC object; either the one passed in as the first argument,
      or a new one (if the first argument was None).
    """

    if rpc is None:
      rpc = create_rpc()
    assert rpc.service == 'memcache', repr(rpc.service)
    rpc.make_call(method, request, response, get_result_hook, user_data)
    return rpc

  def _do_pickle(self, value):
    """Pickles a provided value."""
    pickle_data = cStringIO.StringIO()
    pickler = self._pickler_factory(pickle_data,
                                    protocol=self._pickle_protocol)
    if self._persistent_id is not None:
      pickler.persistent_id = self._persistent_id
    pickler.dump(value)
    return pickle_data.getvalue()

  def _do_unpickle(self, value):
    """Unpickles a provided value."""
    pickle_data = cStringIO.StringIO(value)
    unpickler = self._unpickler_factory(pickle_data)
    if self._persistent_load is not None:
      unpickler.persistent_load = self._persistent_load
    return unpickler.load()

  def _add_app_id(self, message):
    """Populates override field in message if accessing another app's memcache.

    Args:
      message: A protocol buffer supporting the mutable_override() operation.
    """
    if self._app_id:
      app_override = message.mutable_override()
      app_override.set_app_id(self._app_id)

  def set_servers(self, servers):
    """Sets the pool of memcache servers used by the client.

    This is purely a compatibility method.  In Google App Engine, it's a no-op.
    """
    pass

  def disconnect_all(self):
    """Closes all connections to memcache servers.

    This is purely a compatibility method.  In Google App Engine, it's a no-op.
    """
    pass

  def forget_dead_hosts(self):
    """Resets all servers to the alive status.

    This is purely a compatibility method.  In Google App Engine, it's a no-op.
    """
    pass

  def debuglog(self):
    """Logging function for debugging information.

    This is purely a compatibility method.  In Google App Engine, it's a no-op.
    """
    pass

  def get_stats(self):
    """Gets memcache statistics for this application.

    All of these statistics may reset due to various transient conditions. They
    provide the best information available at the time of being called.

    Returns:
      Dictionary mapping statistic names to associated values. Statistics and
      their associated meanings:

        hits: Number of cache get requests resulting in a cache hit.
        misses: Number of cache get requests resulting in a cache miss.
        byte_hits: Sum of bytes transferred on get requests. Rolls over to
          zero on overflow.
        items: Number of key/value pairs in the cache.
        bytes: Total size of all items in the cache.
        oldest_item_age: How long in seconds since the oldest item in the
          cache was accessed. Effectively, this indicates how long a new
          item will survive in the cache without being accessed. This is
          _not_ the amount of time that has elapsed since the item was
          created.

      On error, returns None.
    """
    rpc = self.get_stats_async()
    return rpc.get_result()

  def get_stats_async(self, rpc=None):
    """Async version of get_stats().

    Returns:
      A UserRPC instance whose get_result() method returns None if
      there was a network error, otherwise a dict just like
      get_stats() returns.
    """
    request = MemcacheStatsRequest()
    self._add_app_id(request)
    response = MemcacheStatsResponse()
    return self._make_async_call(rpc, 'Stats', request, response,
                                 self.__get_stats_hook, None)

  def __get_stats_hook(self, rpc):
    try:
      rpc.check_success()
    except apiproxy_errors.Error:
      return None
    response = rpc.response
    if not response.has_stats():
      return {
        STAT_HITS: 0,
        STAT_MISSES: 0,
        STAT_BYTE_HITS: 0,
        STAT_ITEMS: 0,
        STAT_BYTES: 0,
        STAT_OLDEST_ITEM_AGES: 0,
      }

    stats = response.stats()
    return {
      STAT_HITS: stats.hits(),
      STAT_MISSES: stats.misses(),
      STAT_BYTE_HITS: stats.byte_hits(),
      STAT_ITEMS: stats.items(),
      STAT_BYTES: stats.bytes(),
      STAT_OLDEST_ITEM_AGES: stats.oldest_item_age(),
    }

  def flush_all(self):
    """Deletes everything in memcache.

    Returns:
      True on success, False on RPC or server error.
    """
    rpc = self.flush_all_async()
    return rpc.get_result()

  def flush_all_async(self, rpc=None):
    """Async version of flush_all().

    Returns:
      A UserRPC instance whose get_result() method returns True on
      success, False on RPC or server error.
    """
    request = MemcacheFlushRequest()
    self._add_app_id(request)
    response = MemcacheFlushResponse()
    return self._make_async_call(rpc, 'FlushAll', request, response,
                                 self.__flush_all_hook, None)

  def __flush_all_hook(self, rpc):
    try:
      rpc.check_success()
    except apiproxy_errors.Error:
      return False
    return True

  def get(self, key, namespace=None, for_cas=False):
    """Looks up a single key in memcache.

    If you have multiple items to load, though, it's much more efficient
    to use get_multi() instead, which loads them in one bulk operation,
    reducing the networking latency that'd otherwise be required to do
    many serialized get() operations.

    Args:
      key: The key in memcache to look up.  See docs on Client
        for details of format.
      namespace: a string specifying an optional namespace to use in
        the request.
      for_cas: If True, request and store CAS ids on the client (see
        cas() operation below).

    Returns:
      The value of the key, if found in memcache, else None.
    """
    if _is_pair(key):
      key = key[1]
    rpc = self.get_multi_async([key], namespace=namespace, for_cas=for_cas)
    results = rpc.get_result()
    return results.get(key)

  def gets(self, key, namespace=None):
    """An alias for get(..., for_cas=True)."""
    return self.get(key, namespace=namespace, for_cas=True)

  def get_multi(self, keys, key_prefix='', namespace=None, for_cas=False):
    """Looks up multiple keys from memcache in one operation.

    This is the recommended way to do bulk loads.

    Args:
      keys: List of keys to look up.  Keys may be strings or
        tuples of (hash_value, string).  Google App Engine
        does the sharding and hashing automatically, though, so the hash
        value is ignored.  To memcache, keys are just series of bytes,
        and not in any particular encoding.
      key_prefix: Prefix to prepend to all keys when talking to the server;
        not included in the returned dictionary.
      namespace: a string specifying an optional namespace to use in
        the request.
      for_cas: If True, request and store CAS ids on the client.

    Returns:
      A dictionary of the keys and values that were present in memcache.
      Even if the key_prefix was specified, that key_prefix won't be on
      the keys in the returned dictionary.
    """
    rpc = self.get_multi_async(keys, key_prefix, namespace, for_cas)
    return rpc.get_result()

  def get_multi_async(self, keys, key_prefix='', namespace=None,
                      for_cas=False, rpc=None):
    """Async version of get_multi().

    Returns:
      A UserRPC instance whose get_result() method returns {} if
      there was a network error, otherwise a dict just like
      get_multi() returns.
    """
    request = MemcacheGetRequest()
    self._add_app_id(request)
    _add_name_space(request, namespace)
    if for_cas:
      request.set_for_cas(True)
    response = MemcacheGetResponse()
    user_key = {}
    for key in keys:
      request.add_key(_key_string(key, key_prefix, user_key))

    return self._make_async_call(rpc, 'Get', request, response,
                                 self.__get_hook, user_key)

  def __get_hook(self, rpc):
    try:
      rpc.check_success()
    except apiproxy_errors.Error:
      return {}
    for_cas = rpc.request.for_cas()
    response = rpc.response
    user_key = rpc.user_data
    return_value = {}
    for returned_item in response.item_list():
      value = _decode_value(returned_item.value(), returned_item.flags(),
                            self._do_unpickle)
      raw_key = returned_item.key()
      if for_cas:
        self._cas_ids[raw_key] = returned_item.cas_id()
      return_value[user_key[raw_key]] = value
    return return_value






  def delete(self, key, seconds=0, namespace=None):
    """Deletes a key from memcache.

    Args:
      key: Key to delete.  See docs on Client for detils.
      seconds: Optional number of seconds to make deleted items 'locked'
        for 'add' operations. Value can be a delta from current time (up to
        1 month), or an absolute Unix epoch time.  Defaults to 0, which means
        items can be immediately added.  With or without this option,
        a 'set' operation will always work.  Float values will be rounded up to
        the nearest whole second.
      namespace: a string specifying an optional namespace to use in
        the request.

    Returns:
      DELETE_NETWORK_FAILURE (0) on network failure,
      DELETE_ITEM_MISSING (1) if the server tried to delete the item but
      didn't have it, or
      DELETE_SUCCESSFUL (2) if the item was actually deleted.
      This can be used as a boolean value, where a network failure is the
      only bad condition.
    """
    rpc = self.delete_multi_async([key], seconds, namespace=namespace)
    results = rpc.get_result()
    if not results:
      return DELETE_NETWORK_FAILURE
    return results[0]

  def delete_multi(self, keys, seconds=0, key_prefix='', namespace=None):
    """Delete multiple keys at once.

    Args:
      keys: List of keys to delete.
      seconds: Optional number of seconds to make deleted items 'locked'
        for 'add' operations. Value can be a delta from current time (up to
        1 month), or an absolute Unix epoch time.  Defaults to 0, which means
        items can be immediately added.  With or without this option,
        a 'set' operation will always work.  Float values will be rounded up to
        the nearest whole second.
      key_prefix: Prefix to put on all keys when sending specified
        keys to memcache.  See docs for get_multi() and set_multi().
      namespace: a string specifying an optional namespace to use in
        the request.

    Returns:
      True if all operations completed successfully.  False if one
      or more failed to complete.
    """
    rpc = self.delete_multi_async(keys, seconds, key_prefix, namespace)
    results = rpc.get_result()
    return bool(results)

  def delete_multi_async(self, keys, seconds=0, key_prefix='',
                         namespace=None, rpc=None):
    """Async version of delete_multi() -- note different return value.

    Returns:
      A UserRPC instance whose get_result() method returns None if
      there was a network error, or a list of status values otherwise,
      where each status corresponds to a key and is either
      DELETE_SUCCESSFUL, DELETE_ITEM_MISSING, or DELETE_NETWORK_FAILURE
      (see delete() docstring for details).
    """
    if not isinstance(seconds, (int, long, float)):
      raise TypeError('Delete timeout must be a number.')
    if seconds < 0:
      raise ValueError('Delete timeout must not be negative.')

    request = MemcacheDeleteRequest()
    self._add_app_id(request)
    _add_name_space(request, namespace)
    response = MemcacheDeleteResponse()

    for key in keys:
      delete_item = request.add_item()
      delete_item.set_key(_key_string(key, key_prefix=key_prefix))
      delete_item.set_delete_time(int(math.ceil(seconds)))

    return self._make_async_call(rpc, 'Delete', request, response,
                                 self.__delete_hook, None)

  def __delete_hook(self, rpc):
    try:
      rpc.check_success()
    except apiproxy_errors.Error:
      return None
    result = []
    for status in rpc.response.delete_status_list():
      if status == MemcacheDeleteResponse.DELETED:
        result.append(DELETE_SUCCESSFUL)
      elif status == MemcacheDeleteResponse.NOT_FOUND:
        result.append(DELETE_ITEM_MISSING)
      else:
        result.append(DELETE_NETWORK_FAILURE)
    return result









  def set(self, key, value, time=0, min_compress_len=0, namespace=None):
    """Sets a key's value, regardless of previous contents in cache.

    Unlike add() and replace(), this method always sets (or
    overwrites) the value in memcache, regardless of previous
    contents.

    Args:
      key: Key to set.  See docs on Client for details.
      value: Value to set.  Any type.  If complex, will be pickled.
      time: Optional expiration time, either relative number of seconds
        from current time (up to 1 month), or an absolute Unix epoch time.
        By default, items never expire, though items may be evicted due to
        memory pressure.  Float values will be rounded up to the nearest
        whole second.
      min_compress_len: Ignored option for compatibility.
      namespace: a string specifying an optional namespace to use in
        the request.

    Returns:
      True if set.  False on error.
    """
    return self._set_with_policy(MemcacheSetRequest.SET, key, value, time=time,
                                 namespace=namespace)

  def add(self, key, value, time=0, min_compress_len=0, namespace=None):
    """Sets a key's value, iff item is not already in memcache.

    Args:
      key: Key to set.  See docs on Client for details.
      value: Value to set.  Any type.  If complex, will be pickled.
      time: Optional expiration time, either relative number of seconds
        from current time (up to 1 month), or an absolute Unix epoch time.
        By default, items never expire, though items may be evicted due to
        memory pressure.  Float values will be rounded up to the nearest
        whole second.
      min_compress_len: Ignored option for compatibility.
      namespace: a string specifying an optional namespace to use in
        the request.

    Returns:
      True if added.  False on error.
    """
    return self._set_with_policy(MemcacheSetRequest.ADD, key, value, time=time,
                                 namespace=namespace)

  def replace(self, key, value, time=0, min_compress_len=0, namespace=None):
    """Replaces a key's value, failing if item isn't already in memcache.

    Args:
      key: Key to set.  See docs on Client for details.
      value: Value to set.  Any type.  If complex, will be pickled.
      time: Optional expiration time, either relative number of seconds
        from current time (up to 1 month), or an absolute Unix epoch time.
        By default, items never expire, though items may be evicted due to
        memory pressure.  Float values will be rounded up to the nearest
        whole second.
      min_compress_len: Ignored option for compatibility.
      namespace: a string specifying an optional namespace to use in
        the request.

    Returns:
      True if replaced.  False on RPC error or cache miss.
    """
    return self._set_with_policy(MemcacheSetRequest.REPLACE,
                                 key, value, time=time, namespace=namespace)

  def cas(self, key, value, time=0, min_compress_len=0, namespace=None):
    """Compare-And-Set update.

    This requires that the key has previously been successfully
    fetched with gets() or get(..., for_cas=True), and that no changes
    have been made to the key since that fetch.  Typical usage is:

      key = ...
      client = memcache.Client()
      value = client.gets(key)  # OR client.get(key, for_cas=True)
      <updated value>
      ok = client.cas(key, value)

    If two processes run similar code, the first one calling cas()
    will succeed (ok == True), while the second one will fail (ok ==
    False).  This can be used to detect race conditions.

    NOTE: some state (the CAS id) is stored on the Client object for
    each key ever used with gets().  To prevent ever-increasing memory
    usage, you must use a Client object when using cas(), and the
    lifetime of your Client object should be limited to that of one
    incoming HTTP request.  You cannot use the global-function-based
    API.

    Args:
      key: Key to set.  See docs on Client for details.
      value: The new value.
      time: Optional expiration time, either relative number of seconds
        from current time (up to 1 month), or an absolute Unix epoch time.
        By default, items never expire, though items may be evicted due to
        memory pressure.  Float values will be rounded up to the nearest
        whole second.
      min_compress_len: Ignored option for compatibility.
      namespace: a string specifying an optional namespace to use in
        the request.

    Returns:
      True if updated.  False on RPC error or if the CAS id didn't match.
    """
    return self._set_with_policy(MemcacheSetRequest.CAS, key, value,
                                 time, namespace)

  def _set_with_policy(self, policy, key, value, time=0, namespace=None):
    """Sets a single key with a specified policy.

    Helper function for set(), add(), and replace().

    Args:
      policy:  One of MemcacheSetRequest.SET, .ADD, .REPLACE or .CAS.
      key: Key to add, set, or replace.  See docs on Client for details.
      value: Value to set.
      time: Expiration time, defaulting to 0 (never expiring).
      namespace: a string specifying an optional namespace to use in
        the request.

    Returns:
      True if stored, False on RPC error or policy error, e.g. a replace
      that failed due to the item not already existing, or an add
      failing due to the item not already existing.
    """
    rpc = self._set_multi_async_with_policy(policy, {key: value},
                                            time, '', namespace)
    status_dict = rpc.get_result()
    if not status_dict:
      return False
    return status_dict.get(key) == MemcacheSetResponse.STORED






  def _set_multi_with_policy(self, policy, mapping, time=0, key_prefix='',
                             namespace=None):
    """Set multiple keys with a specified policy.

    Helper function for set_multi(), add_multi(), and replace_multi(). This
    reduces the network latency of doing many requests in serial.

    Args:
      policy:  One of MemcacheSetRequest.SET, .ADD, .REPLACE or .CAS.
      mapping: Dictionary of keys to values.  If policy == CAS, the
        values must be (value, cas_id) tuples.
      time: Optional expiration time, either relative number of seconds
        from current time (up to 1 month), or an absolute Unix epoch time.
        By default, items never expire, though items may be evicted due to
        memory pressure.  Float values will be rounded up to the nearest
        whole second.
      key_prefix: Prefix for to prepend to all keys.
      namespace: a string specifying an optional namespace to use in
        the request.

    Returns:
      A list of keys whose values were NOT set.  On total success,
      this list should be empty.  On network/RPC/server errors,
      a list of all input keys is returned; in this case the keys
      may or may not have been updated.
    """
    rpc = self._set_multi_async_with_policy(policy, mapping, time,
                                            key_prefix, namespace)
    status_dict = rpc.get_result()
    server_keys, user_key = rpc.user_data

    if not status_dict:
      return user_key.values()


    unset_list = []
    for server_key in server_keys:
      key = user_key[server_key]
      set_status = status_dict[key]
      if set_status != MemcacheSetResponse.STORED:
        unset_list.append(key)

    return unset_list


  def _set_multi_async_with_policy(self, policy, mapping, time=0,
                                   key_prefix='', namespace=None, rpc=None):
    """Async version of _set_multi_with_policy() -- note different return.

    Returns:
      A UserRPC instance whose get_result() method returns None if
      there was a network error, or a dict mapping (user) keys to
      status values otherwise, where each status is one of STORED,
      NOT_STORED, ERROR, or EXISTS.
    """
    if not isinstance(time, (int, long, float)):
      raise TypeError('Expiration must be a number.')
    if time < 0.0:
      raise ValueError('Expiration must not be negative.')

    request = MemcacheSetRequest()
    self._add_app_id(request)
    _add_name_space(request, namespace)
    user_key = {}
    server_keys = []
    set_cas_id = (policy == MemcacheSetRequest.CAS)
    for key, value in mapping.iteritems():
      server_key = _key_string(key, key_prefix, user_key)
      stored_value, flags = _validate_encode_value(value, self._do_pickle)
      server_keys.append(server_key)

      item = request.add_item()
      item.set_key(server_key)
      item.set_value(stored_value)
      item.set_flags(flags)
      item.set_set_policy(policy)
      item.set_expiration_time(int(math.ceil(time)))
      if set_cas_id:
        cas_id = self._cas_ids.get(server_key)

        if cas_id is not None:
          item.set_cas_id(cas_id)


          item.set_for_cas(True)

    response = MemcacheSetResponse()


    return self._make_async_call(rpc, 'Set', request, response,
                                 self.__set_with_policy_hook,
                                 (server_keys, user_key))

  def __set_with_policy_hook(self, rpc):
    try:
      rpc.check_success()
    except apiproxy_errors.Error:
      return None

    response = rpc.response
    server_keys, user_key = rpc.user_data
    assert response.set_status_size() == len(server_keys)
    status_dict = {}
    for server_key, status in zip(server_keys, response.set_status_list()):
      status_dict[user_key[server_key]] = status
    return status_dict

  def set_multi(self, mapping, time=0, key_prefix='', min_compress_len=0,
                namespace=None):
    """Set multiple keys' values at once, regardless of previous contents.

    Args:
      mapping: Dictionary of keys to values.
      time: Optional expiration time, either relative number of seconds
        from current time (up to 1 month), or an absolute Unix epoch time.
        By default, items never expire, though items may be evicted due to
        memory pressure.  Float values will be rounded up to the nearest
        whole second.
      key_prefix: Prefix for to prepend to all keys.
      min_compress_len: Unimplemented compatibility option.
      namespace: a string specifying an optional namespace to use in
        the request.

    Returns:
      A list of keys whose values were NOT set.  On total success,
      this list should be empty.
    """
    return self._set_multi_with_policy(MemcacheSetRequest.SET, mapping,
                                       time=time, key_prefix=key_prefix,
                                       namespace=namespace)

  def set_multi_async(self, mapping, time=0,  key_prefix='',
                      min_compress_len=0, namespace=None, rpc=None):
    """Async version of set_multi() -- note different return value.

    Returns:
      See _set_multi_async_with_policy().
    """
    return self._set_multi_async_with_policy(MemcacheSetRequest.SET, mapping,
                                             time=time, key_prefix=key_prefix,
                                             namespace=namespace, rpc=rpc)

  def add_multi(self, mapping, time=0, key_prefix='', min_compress_len=0,
                namespace=None):
    """Set multiple keys' values iff items are not already in memcache.

    Args:
      mapping: Dictionary of keys to values.
      time: Optional expiration time, either relative number of seconds
        from current time (up to 1 month), or an absolute Unix epoch time.
        By default, items never expire, though items may be evicted due to
        memory pressure.  Float values will be rounded up to the nearest
        whole second.
      key_prefix: Prefix for to prepend to all keys.
      min_compress_len: Unimplemented compatibility option.
      namespace: a string specifying an optional namespace to use in
        the request.

    Returns:
      A list of keys whose values were NOT set because they did not already
      exist in memcache.  On total success, this list should be empty.
    """
    return self._set_multi_with_policy(MemcacheSetRequest.ADD, mapping,
                                       time=time, key_prefix=key_prefix,
                                       namespace=namespace)

  def add_multi_async(self, mapping, time=0,  key_prefix='',
                      min_compress_len=0, namespace=None, rpc=None):
    """Async version of add_multi() -- note different return value.

    Returns:
      See _set_multi_async_with_policy().
    """
    return self._set_multi_async_with_policy(MemcacheSetRequest.ADD, mapping,
                                             time=time, key_prefix=key_prefix,
                                             namespace=namespace, rpc=rpc)

  def replace_multi(self, mapping, time=0, key_prefix='', min_compress_len=0,
                    namespace=None):
    """Replace multiple keys' values, failing if the items aren't in memcache.

    Args:
      mapping: Dictionary of keys to values.
      time: Optional expiration time, either relative number of seconds
        from current time (up to 1 month), or an absolute Unix epoch time.
        By default, items never expire, though items may be evicted due to
        memory pressure.  Float values will be rounded up to the nearest
        whole second.
      key_prefix: Prefix for to prepend to all keys.
      min_compress_len: Unimplemented compatibility option.
      namespace: a string specifying an optional namespace to use in
        the request.

    Returns:
      A list of keys whose values were NOT set because they already existed
      in memcache.  On total success, this list should be empty.
    """
    return self._set_multi_with_policy(MemcacheSetRequest.REPLACE, mapping,
                                       time=time, key_prefix=key_prefix,
                                       namespace=namespace)

  def replace_multi_async(self, mapping, time=0,  key_prefix='',
                          min_compress_len=0, namespace=None, rpc=None):
    """Async version of replace_multi() -- note different return value.

    Returns:
      See _set_multi_async_with_policy().
    """
    return self._set_multi_async_with_policy(MemcacheSetRequest.REPLACE,
                                             mapping,
                                             time=time, key_prefix=key_prefix,
                                             namespace=namespace, rpc=rpc)

  def cas_multi(self, mapping, time=0, key_prefix='', min_compress_len=0,
                namespace=None):
    """Compare-And-Set update for multiple keys.

    See cas() docstring for an explanation.

    Args:
      mapping: Dictionary of keys to values.
      time: Optional expiration time, either relative number of seconds
        from current time (up to 1 month), or an absolute Unix epoch time.
        By default, items never expire, though items may be evicted due to
        memory pressure.  Float values will be rounded up to the nearest
        whole second.
      key_prefix: Prefix for to prepend to all keys.
      min_compress_len: Unimplemented compatibility option.
      namespace: a string specifying an optional namespace to use in
        the request.

    Returns:
      A list of keys whose values were NOT set because the compare
      failed.  On total success, this list should be empty.
    """
    return self._set_multi_with_policy(MemcacheSetRequest.CAS, mapping,
                                       time=time, key_prefix=key_prefix,
                                       namespace=namespace)

  def cas_multi_async(self, mapping, time=0,  key_prefix='',
                      min_compress_len=0, namespace=None, rpc=None):
    """Async version of cas_multi() -- note different return value.

    Returns:
      See _set_multi_async_with_policy().
    """
    return self._set_multi_async_with_policy(MemcacheSetRequest.CAS, mapping,
                                             time=time, key_prefix=key_prefix,
                                             namespace=namespace, rpc=rpc)

  def incr(self, key, delta=1, namespace=None, initial_value=None):
    """Atomically increments a key's value.

    Internally, the value is a unsigned 64-bit integer.  Memcache
    doesn't check 64-bit overflows.  The value, if too large, will
    wrap around.

    Unless an initial_value is specified, the key must already exist
    in the cache to be incremented.  To initialize a counter, either
    specify initial_value or set() it to the initial value, as an
    ASCII decimal integer.  Future get()s of the key, post-increment,
    will still be an ASCII decimal value.

    Args:
      key: Key to increment. If an iterable collection, each one of the keys
          will be offset. See Client's docstring for details.
      delta: Non-negative integer value (int or long) to increment key by,
        defaulting to 1.
      namespace: a string specifying an optional namespace to use in
        the request.
      initial_value: initial value to put in the cache, if it doesn't
        already exist.  The default value, None, will not create a cache
        entry if it doesn't already exist.

    Returns:
      If key was a single value, the new long integer value, or None if key
      was not in the cache, could not be incremented for any other reason, or
      a network/RPC/server error occurred.

      If key was an iterable collection, a dictionary will be returned
      mapping supplied keys to values, with the values having the same meaning
      as the singular return value of this method.

    Raises:
      ValueError: If number is negative.
      TypeError: If delta isn't an int or long.
    """
    return self._incrdecr(key, False, delta, namespace=namespace,
                          initial_value=initial_value)

  def incr_async(self, key, delta=1, namespace=None, initial_value=None,
                 rpc=None):
    """Async version of incr().

    Returns:
      A UserRPC instance whose get_result() method returns the same
      kind of value as incr() returns.
    """
    return self._incrdecr_async(key, False, delta, namespace=namespace,
                                initial_value=initial_value, rpc=rpc)

  def decr(self, key, delta=1, namespace=None, initial_value=None):
    """Atomically decrements a key's value.

    Internally, the value is a unsigned 64-bit integer.  Memcache
    caps decrementing below zero to zero.

    The key must already exist in the cache to be decremented.  See
    docs on incr() for details.

    Args:
      key: Key to decrement. If an iterable collection, each one of the keys
          will be offset.  See Client's docstring for details.
      delta: Non-negative integer value (int or long) to decrement key by,
        defaulting to 1.
      namespace: a string specifying an optional namespace to use in
        the request.
      initial_value: initial value to put in the cache, if it doesn't
        already exist.  The default value, None, will not create a cache
        entry if it doesn't already exist.

    Returns:
      If key was a single value, the new long integer value, or None if key
      was not in the cache, could not be decremented for any other reason, or
      a network/RPC/server error occurred.

      If key was an iterable collection, a dictionary will be returned
      mapping supplied keys to values, with the values having the same meaning
      as the singular return value of this method.

    Raises:
      ValueError: If number is negative.
      TypeError: If delta isn't an int or long.
    """
    return self._incrdecr(key, True, delta, namespace=namespace,
                          initial_value=initial_value)

  def decr_async(self, key, delta=1, namespace=None, initial_value=None,
                 rpc=None):
    """Async version of decr().

    Returns:
      A UserRPC instance whose get_result() method returns the same
      kind of value as decr() returns.
    """
    return self._incrdecr_async(key, True, delta, namespace=namespace,
                                initial_value=initial_value, rpc=rpc)

  def _incrdecr(self, key, is_negative, delta, namespace=None,
                initial_value=None):
    """Increment or decrement a key by a provided delta.

    Args:
      key: Key to increment or decrement. If an iterable collection, each
        one of the keys will be offset.
      is_negative: Boolean, if this is a decrement.
      delta: Non-negative integer amount (int or long) to increment
        or decrement by.
      namespace: a string specifying an optional namespace to use in
        the request.
      initial_value: initial value to put in the cache, if it doesn't
        already exist.  The default value, None, will not create a cache
        entry if it doesn't already exist.

    Returns:
      New long integer value, or None on cache miss or network/RPC/server
      error.

    Raises:
      ValueError: If delta is negative.
      TypeError: If delta isn't an int or long.
    """
    rpc = self._incrdecr_async(key, is_negative, delta, namespace,
                               initial_value)
    return rpc.get_result()

  def _incrdecr_async(self, key, is_negative, delta, namespace=None,
                initial_value=None, rpc=None):
    """Async version of _incrdecr().

    Returns:
      A UserRPC instance whose get_result() method returns the same
      kind of value as _incrdecr() returns.
    """
    if not isinstance(delta, (int, long)):
      raise TypeError('Delta must be an integer or long, received %r' % delta)
    if delta < 0:
      raise ValueError('Delta must not be negative.')


    if not isinstance(key, basestring):
      try:
        it = iter(key)
      except TypeError:

        pass
      else:
        if is_negative:
          delta = -delta
        return self.offset_multi_async(dict((k, delta) for k in it),
                                       namespace=namespace,
                                       initial_value=initial_value,
                                       rpc=rpc)


    request = MemcacheIncrementRequest()
    self._add_app_id(request)
    _add_name_space(request, namespace)
    response = MemcacheIncrementResponse()
    request.set_key(_key_string(key))
    request.set_delta(delta)
    if is_negative:
      request.set_direction(MemcacheIncrementRequest.DECREMENT)
    else:
      request.set_direction(MemcacheIncrementRequest.INCREMENT)
    if initial_value is not None:

      request.set_initial_value(long(initial_value))
      initial_flags = None
      if isinstance(initial_value, int):
        initial_flags = TYPE_INT
      elif isinstance(initial_value, long):
        initial_flags = TYPE_LONG
      if initial_flags is not None:
        request.set_initial_flags(initial_flags)


    return self._make_async_call(rpc, 'Increment', request, response,
                                 self.__incrdecr_hook, None)

  def __incrdecr_hook(self, rpc):
    try:
      rpc.check_success()
    except apiproxy_errors.Error:
      return None

    response = rpc.response
    if response.has_new_value():
      return response.new_value()
    return None

  def offset_multi(self, mapping, key_prefix='',
                   namespace=None, initial_value=None):
    """Offsets multiple keys by a delta, incrementing and decrementing in batch.

    Args:
      mapping: Dictionary mapping keys to deltas (positive or negative integers)
        to apply to each corresponding key.
      key_prefix: Prefix for to prepend to all keys.
      initial_value: Initial value to put in the cache, if it doesn't
        already exist. The default value, None, will not create a cache
        entry if it doesn't already exist.
      namespace: A string specifying an optional namespace to use in
        the request.

    Returns:
      Dictionary mapping input keys to new integer values. The new value will
      be None if an error occurs, the key does not already exist, or the value
      was not an integer type. The values will wrap-around at unsigned 64-bit
      integer-maximum and underflow will be floored at zero.
    """
    rpc = self.offset_multi_async(mapping, key_prefix,
                                  namespace, initial_value)
    return rpc.get_result()

  def offset_multi_async(self, mapping, key_prefix='',
                         namespace=None, initial_value=None, rpc=None):
    """Async version of offset_multi().

    Returns:
      A UserRPC instance whose get_result() method returns a dict just
      like offset_multi() returns.
    """
    initial_flags = None
    if initial_value is not None:
      if not isinstance(initial_value, (int, long)):
        raise TypeError('initial_value must be an integer')
      if initial_value < 0:
        raise ValueError('initial_value must be >= 0')
      if isinstance(initial_value, int):
        initial_flags = TYPE_INT
      else:
        initial_flags = TYPE_LONG

    request = MemcacheBatchIncrementRequest()
    self._add_app_id(request)
    response = MemcacheBatchIncrementResponse()
    _add_name_space(request, namespace)

    for key, delta in mapping.iteritems():
      if not isinstance(delta, (int, long)):
        raise TypeError('Delta must be an integer or long, received %r' % delta)
      if delta >= 0:
        direction = MemcacheIncrementRequest.INCREMENT
      else:
        delta = -delta
        direction = MemcacheIncrementRequest.DECREMENT

      server_key = _key_string(key, key_prefix)

      item = request.add_item()
      item.set_key(server_key)
      item.set_delta(delta)
      item.set_direction(direction)
      if initial_value is not None:
        item.set_initial_value(initial_value)
        item.set_initial_flags(initial_flags)


    return self._make_async_call(rpc, 'BatchIncrement', request, response,
                                 self.__offset_hook, mapping)

  def __offset_hook(self, rpc):
    mapping = rpc.user_data
    try:
      rpc.check_success()
    except apiproxy_errors.Error:
      return dict((k, None) for k in mapping.iterkeys())

    response = rpc.response
    assert response.item_size() == len(mapping)

    result_dict = {}
    for key, resp_item in zip(mapping.iterkeys(), response.item_list()):
      if (resp_item.increment_status() == MemcacheIncrementResponse.OK and
          resp_item.has_new_value()):
        result_dict[key] = resp_item.new_value()
      else:
        result_dict[key] = None

    return result_dict





_CLIENT = None


def setup_client(client_obj):
  """Sets the Client object instance to use for all module-level methods.

  Use this method if you want to have customer persistent_id() or
  persistent_load() functions associated with your client.

  NOTE: We don't expose the _async methods as functions; they're too
  obscure; and we don't expose gets(), cas() and cas_multi() because
  they maintain state on the client object.

  Args:
    client_obj: Instance of the memcache.Client object.
  """
  global _CLIENT
  var_dict = globals()

  _CLIENT = client_obj
  var_dict['set_servers'] = _CLIENT.set_servers
  var_dict['disconnect_all'] = _CLIENT.disconnect_all
  var_dict['forget_dead_hosts'] = _CLIENT.forget_dead_hosts
  var_dict['debuglog'] = _CLIENT.debuglog
  var_dict['get'] = _CLIENT.get
  var_dict['get_multi'] = _CLIENT.get_multi
  var_dict['set'] = _CLIENT.set
  var_dict['set_multi'] = _CLIENT.set_multi
  var_dict['add'] = _CLIENT.add
  var_dict['add_multi'] = _CLIENT.add_multi
  var_dict['replace'] = _CLIENT.replace
  var_dict['replace_multi'] = _CLIENT.replace_multi
  var_dict['delete'] = _CLIENT.delete
  var_dict['delete_multi'] = _CLIENT.delete_multi
  var_dict['incr'] = _CLIENT.incr
  var_dict['decr'] = _CLIENT.decr
  var_dict['flush_all'] = _CLIENT.flush_all
  var_dict['get_stats'] = _CLIENT.get_stats
  var_dict['offset_multi'] = _CLIENT.offset_multi


setup_client(Client())
