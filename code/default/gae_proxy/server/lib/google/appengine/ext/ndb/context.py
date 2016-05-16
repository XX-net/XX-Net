#
# Copyright 2008 The ndb Authors. All Rights Reserved.
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

"""Context class."""

import logging
import sys

from .google_imports import datastore  # For taskqueue coordination
from .google_imports import datastore_errors
from .google_imports import memcache
from .google_imports import namespace_manager
from .google_imports import urlfetch
from .google_imports import datastore_rpc
from .google_imports import entity_pb

from .google_imports import ProtocolBuffer

from . import key as key_module
from . import model
from . import tasklets
from . import eventloop
from . import utils

__all__ = ['Context', 'ContextOptions', 'TransactionOptions', 'AutoBatcher',
           'EVENTUAL_CONSISTENCY',
          ]

_LOCK_TIME = 32  # Time to lock out memcache.add() after datastore updates.
_LOCKED = 0  # Special value to store in memcache indicating locked value.


# Constant for read_policy.
EVENTUAL_CONSISTENCY = datastore_rpc.Configuration.EVENTUAL_CONSISTENCY


class ContextOptions(datastore_rpc.Configuration):
  """Configuration options that may be passed along with get/put/delete."""

  @datastore_rpc.ConfigOption
  def use_cache(value):
    if not isinstance(value, bool):
      raise datastore_errors.BadArgumentError(
          'use_cache should be a bool (%r)' % (value,))
    return value

  @datastore_rpc.ConfigOption
  def use_memcache(value):
    if not isinstance(value, bool):
      raise datastore_errors.BadArgumentError(
          'use_memcache should be a bool (%r)' % (value,))
    return value

  @datastore_rpc.ConfigOption
  def use_datastore(value):
    if not isinstance(value, bool):
      raise datastore_errors.BadArgumentError(
          'use_datastore should be a bool (%r)' % (value,))
    return value

  @datastore_rpc.ConfigOption
  def memcache_timeout(value):
    if not isinstance(value, (int, long)):
      raise datastore_errors.BadArgumentError(
          'memcache_timeout should be an integer (%r)' % (value,))
    return value

  @datastore_rpc.ConfigOption
  def max_memcache_items(value):
    if not isinstance(value, (int, long)):
      raise datastore_errors.BadArgumentError(
          'max_memcache_items should be an integer (%r)' % (value,))
    return value

  @datastore_rpc.ConfigOption
  def memcache_deadline(value):
    if not isinstance(value, (int, long)):
      raise datastore_errors.BadArgumentError(
          'memcache_deadline should be an integer (%r)' % (value,))
    return value


class TransactionOptions(ContextOptions, datastore_rpc.TransactionOptions):
  """Support both context options and transaction options."""


# options and config can be used interchangeably.
_OPTION_TRANSLATIONS = {
    'options': 'config',
}


def _make_ctx_options(ctx_options, config_cls=ContextOptions):
  """Helper to construct a ContextOptions object from keyword arguments.

  Args:
    ctx_options: A dict of keyword arguments.
    config_cls: Optional Configuration class to use, default ContextOptions.

  Note that either 'options' or 'config' can be used to pass another
  Configuration object, but not both.  If another Configuration
  object is given it provides default values.

  Returns:
    A Configuration object, or None if ctx_options is empty.
  """
  if not ctx_options:
    return None
  for key in list(ctx_options):
    translation = _OPTION_TRANSLATIONS.get(key)
    if translation:
      if translation in ctx_options:
        raise ValueError('Cannot specify %s and %s at the same time' %
                         (key, translation))
      ctx_options[translation] = ctx_options.pop(key)
  return config_cls(**ctx_options)


class AutoBatcher(object):
  """Batches multiple async calls if they share the same rpc options.

  Here is an example to explain what this class does.

  Life of a key.get_async(options) API call:
  *) Key gets the singleton Context instance and invokes Context.get.
  *) Context.get calls Context._get_batcher.add(key, options). This
     returns a future "fut" as the return value of key.get_async.
     At this moment, key.get_async returns.

  *) When more than "limit" number of _get_batcher.add() was called,
     _get_batcher invokes its self._todo_tasklet, Context._get_tasklet,
     with the list of keys seen so far.
  *) Context._get_tasklet fires a MultiRPC and waits on it.
  *) Upon MultiRPC completion, Context._get_tasklet passes on the results
     to the respective "fut" from key.get_async.

  *) If user calls "fut".get_result() before "limit" number of add() was called,
     "fut".get_result() will repeatedly call eventloop.run1().
  *) After processing immediate callbacks, eventloop will run idlers.
     AutoBatcher._on_idle is an idler.
  *) _on_idle will run the "todo_tasklet" before the batch is full.

  So the engine is todo_tasklet, which is a proxy tasklet that can combine
  arguments into batches and passes along results back to respective futures.
  This class is mainly a helper that invokes todo_tasklet with the right
  arguments at the right time.
  """

  def __init__(self, todo_tasklet, limit):
    """Init.

    Args:
      todo_tasklet: the tasklet that actually fires RPC and waits on a MultiRPC.
        It should take a list of (future, arg) pairs and an "options" as
        arguments. "options" are rpc options.
      limit: max number of items to batch for each distinct value of "options".
    """
    self._todo_tasklet = todo_tasklet
    self._limit = limit
    # A map from "options" to a list of (future, arg) tuple.
    # future is the future return from a single async operations.
    self._queues = {}
    self._running = []  # A list of in-flight todo_tasklet futures.
    self._cache = {}  # Cache of in-flight todo_tasklet futures.

  def __repr__(self):
    return '%s(%s)' % (self.__class__.__name__, self._todo_tasklet.__name__)

  def run_queue(self, options, todo):
    """Actually run the _todo_tasklet."""
    utils.logging_debug('AutoBatcher(%s): %d items',
                        self._todo_tasklet.__name__, len(todo))
    batch_fut = self._todo_tasklet(todo, options)
    self._running.append(batch_fut)
    # Add a callback when we're done.
    batch_fut.add_callback(self._finished_callback, batch_fut, todo)

  def _on_idle(self):
    """An idler eventloop can run.

    Eventloop calls this when it has finished processing all immediate
    callbacks. This method runs _todo_tasklet even before the batch is full.
    """
    if not self.action():
      return None
    return True

  def add(self, arg, options=None):
    """Adds an arg and gets back a future.

    Args:
      arg: one argument for _todo_tasklet.
      options: rpc options.

    Return:
      An instance of future, representing the result of running
        _todo_tasklet without batching.
    """
    fut = tasklets.Future('%s.add(%s, %s)' % (self, arg, options))
    todo = self._queues.get(options)
    if todo is None:
      utils.logging_debug('AutoBatcher(%s): creating new queue for %r',
                          self._todo_tasklet.__name__, options)
      if not self._queues:
        eventloop.add_idle(self._on_idle)
      todo = self._queues[options] = []
    todo.append((fut, arg))
    if len(todo) >= self._limit:
      del self._queues[options]
      self.run_queue(options, todo)
    return fut

  def add_once(self, arg, options=None):
    cache_key = (arg, options)
    fut = self._cache.get(cache_key)
    if fut is None:
      fut = self.add(arg, options)
      self._cache[cache_key] = fut
      fut.add_immediate_callback(self._cache.__delitem__, cache_key)
    return fut

  def action(self):
    queues = self._queues
    if not queues:
      return False
    options, todo = queues.popitem()  # TODO: Should this use FIFO ordering?
    self.run_queue(options, todo)
    return True

  def _finished_callback(self, batch_fut, todo):
    """Passes exception along.

    Args:
      batch_fut: the batch future returned by running todo_tasklet.
      todo: (fut, option) pair. fut is the future return by each add() call.

    If the batch fut was successful, it has already called fut.set_result()
    on other individual futs. This method only handles when the batch fut
    encountered an exception.
    """
    self._running.remove(batch_fut)
    err = batch_fut.get_exception()
    if err is not None:
      tb = batch_fut.get_traceback()
      for (fut, _) in todo:
        if not fut.done():
          fut.set_exception(err, tb)

  @tasklets.tasklet
  def flush(self):
    while self._running or self.action():
      if self._running:
        yield self._running  # A list of Futures


class Context(object):

  def __init__(self, conn=None, auto_batcher_class=AutoBatcher, config=None,
               parent_context=None):
    # NOTE: If conn is not None, config is only used to get the
    # auto-batcher limits.
    if conn is None:
      conn = model.make_connection(config)
    self._conn = conn
    self._auto_batcher_class = auto_batcher_class
    self._parent_context = parent_context  # For transaction nesting.
    # Get the get/put/delete limits (defaults 1000, 500, 500).
    # Note that the explicit config passed in overrides the config
    # attached to the connection, if it was passed in.
    max_get = (datastore_rpc.Configuration.max_get_keys(config, conn.config) or
               datastore_rpc.Connection.MAX_GET_KEYS)
    max_put = (datastore_rpc.Configuration.max_put_entities(config,
                                                            conn.config) or
               datastore_rpc.Connection.MAX_PUT_ENTITIES)
    max_delete = (datastore_rpc.Configuration.max_delete_keys(config,
                                                              conn.config) or
                  datastore_rpc.Connection.MAX_DELETE_KEYS)
    # Create the get/put/delete auto-batchers.
    self._get_batcher = auto_batcher_class(self._get_tasklet, max_get)
    self._put_batcher = auto_batcher_class(self._put_tasklet, max_put)
    self._delete_batcher = auto_batcher_class(self._delete_tasklet, max_delete)
    # We only have a single limit for memcache (default 1000).
    max_memcache = (ContextOptions.max_memcache_items(config, conn.config) or
                    datastore_rpc.Connection.MAX_GET_KEYS)
    # Create the memcache auto-batchers.
    self._memcache_get_batcher = auto_batcher_class(self._memcache_get_tasklet,
                                                    max_memcache)
    self._memcache_set_batcher = auto_batcher_class(self._memcache_set_tasklet,
                                                    max_memcache)
    self._memcache_del_batcher = auto_batcher_class(self._memcache_del_tasklet,
                                                    max_memcache)
    self._memcache_off_batcher = auto_batcher_class(self._memcache_off_tasklet,
                                                    max_memcache)
    # Create a list of batchers for flush().
    self._batchers = [self._get_batcher,
                      self._put_batcher,
                      self._delete_batcher,
                      self._memcache_get_batcher,
                      self._memcache_set_batcher,
                      self._memcache_del_batcher,
                      self._memcache_off_batcher,
                     ]
    self._cache = {}
    self._memcache = memcache.Client()
    self._on_commit_queue = []

  # NOTE: The default memcache prefix is altered if an incompatible change is
  # required. Remember to check release notes when using a custom prefix.
  _memcache_prefix = 'NDB9:'  # TODO: Might make this configurable.

  @tasklets.tasklet
  def flush(self):
    # Rinse and repeat until all batchers are completely out of work.
    more = True
    while more:
      yield [batcher.flush() for batcher in self._batchers]
      more = False
      for batcher in self._batchers:
        if batcher._running or batcher._queues:
          more = True
          break

  @tasklets.tasklet
  def _get_tasklet(self, todo, options):
    if not todo:
      raise RuntimeError('Nothing to do.')
    # Make the datastore RPC call.
    datastore_keys = []
    for unused_fut, key in todo:
      datastore_keys.append(key)
    # Now wait for the datastore RPC(s) and pass the results to the futures.
    entities = yield self._conn.async_get(options, datastore_keys)
    for ent, (fut, unused_key) in zip(entities, todo):
      fut.set_result(ent)

  @tasklets.tasklet
  def _put_tasklet(self, todo, options):
    if not todo:
      raise RuntimeError('Nothing to do.')
    # TODO: What if the same entity is being put twice?
    # TODO: What if two entities with the same key are being put?
    datastore_entities = []
    for unused_fut, ent in todo:
      datastore_entities.append(ent)
    # Wait for datastore RPC(s).
    keys = yield self._conn.async_put(options, datastore_entities)
    for key, (fut, ent) in zip(keys, todo):
      if key != ent._key:
        if ent._has_complete_key():
          raise datastore_errors.BadKeyError(
              'Entity key differs from the one returned by the datastore. '
              'Expected %r, got %r' % (key, ent._key))
        ent._key = key
      fut.set_result(key)

  @tasklets.tasklet
  def _delete_tasklet(self, todo, options):
    if not todo:
      raise RuntimeError('Nothing to do.')
    futures = []
    datastore_keys = []
    for fut, key in todo:
      futures.append(fut)
      datastore_keys.append(key)
    # Wait for datastore RPC(s).
    yield self._conn.async_delete(options, datastore_keys)
    # Send a dummy result to all original Futures.
    for fut in futures:
      fut.set_result(None)

  # TODO: Unify the policy docstrings (they're getting too verbose).

  # All the policy functions may also:
  # - be a constant of the right type (instead of a function);
  # - return None (instead of a value of the right type);
  # - be None (instead of a function or constant).

  # Model classes may define class variables or class methods
  # _use_{cache,memcache,datastore} or _memcache_timeout to set the
  # default policy of that type for that class.

  @staticmethod
  def default_cache_policy(key):
    """Default cache policy.

    This defers to _use_cache on the Model class.

    Args:
      key: Key instance.

    Returns:
      A bool or None.
    """
    flag = None
    if key is not None:
      modelclass = model.Model._kind_map.get(key.kind())
      if modelclass is not None:
        policy = getattr(modelclass, '_use_cache', None)
        if policy is not None:
          if isinstance(policy, bool):
            flag = policy
          else:
            flag = policy(key)
    return flag

  _cache_policy = default_cache_policy

  def get_cache_policy(self):
    """Return the current context cache policy function.

    Returns:
      A function that accepts a Key instance as argument and returns
      a bool indicating if it should be cached.  May be None.
    """
    return self._cache_policy

  def set_cache_policy(self, func):
    """Set the context cache policy function.

    Args:
      func: A function that accepts a Key instance as argument and returns
        a bool indicating if it should be cached.  May be None.
    """
    if func is None:
      func = self.default_cache_policy
    elif isinstance(func, bool):
      func = lambda unused_key, flag=func: flag
    self._cache_policy = func

  def _use_cache(self, key, options=None):
    """Return whether to use the context cache for this key.

    Args:
      key: Key instance.
      options: ContextOptions instance, or None.

    Returns:
      True if the key should be cached, False otherwise.
    """
    flag = ContextOptions.use_cache(options)
    if flag is None:
      flag = self._cache_policy(key)
    if flag is None:
      flag = ContextOptions.use_cache(self._conn.config)
    if flag is None:
      flag = True
    return flag

  @staticmethod
  def default_memcache_policy(key):
    """Default memcache policy.

    This defers to _use_memcache on the Model class.

    Args:
      key: Key instance.

    Returns:
      A bool or None.
    """
    flag = None
    if key is not None:
      modelclass = model.Model._kind_map.get(key.kind())
      if modelclass is not None:
        policy = getattr(modelclass, '_use_memcache', None)
        if policy is not None:
          if isinstance(policy, bool):
            flag = policy
          else:
            flag = policy(key)
    return flag

  _memcache_policy = default_memcache_policy

  def get_memcache_policy(self):
    """Return the current memcache policy function.

    Returns:
      A function that accepts a Key instance as argument and returns
      a bool indicating if it should be cached.  May be None.
    """
    return self._memcache_policy

  def set_memcache_policy(self, func):
    """Set the memcache policy function.

    Args:
      func: A function that accepts a Key instance as argument and returns
        a bool indicating if it should be cached.  May be None.
    """
    if func is None:
      func = self.default_memcache_policy
    elif isinstance(func, bool):
      func = lambda unused_key, flag=func: flag
    self._memcache_policy = func

  def _use_memcache(self, key, options=None):
    """Return whether to use memcache for this key.

    Args:
      key: Key instance.
      options: ContextOptions instance, or None.

    Returns:
      True if the key should be cached in memcache, False otherwise.
    """
    flag = ContextOptions.use_memcache(options)
    if flag is None:
      flag = self._memcache_policy(key)
    if flag is None:
      flag = ContextOptions.use_memcache(self._conn.config)
    if flag is None:
      flag = True
    return flag

  @staticmethod
  def default_datastore_policy(key):
    """Default datastore policy.

    This defers to _use_datastore on the Model class.

    Args:
      key: Key instance.

    Returns:
      A bool or None.
    """
    flag = None
    if key is not None:
      modelclass = model.Model._kind_map.get(key.kind())
      if modelclass is not None:
        policy = getattr(modelclass, '_use_datastore', None)
        if policy is not None:
          if isinstance(policy, bool):
            flag = policy
          else:
            flag = policy(key)
    return flag

  _datastore_policy = default_datastore_policy

  def get_datastore_policy(self):
    """Return the current context datastore policy function.

    Returns:
      A function that accepts a Key instance as argument and returns
      a bool indicating if it should use the datastore.  May be None.
    """
    return self._datastore_policy

  def set_datastore_policy(self, func):
    """Set the context datastore policy function.

    Args:
      func: A function that accepts a Key instance as argument and returns
        a bool indicating if it should use the datastore.  May be None.
    """
    if func is None:
      func = self.default_datastore_policy
    elif isinstance(func, bool):
      func = lambda unused_key, flag=func: flag
    self._datastore_policy = func

  def _use_datastore(self, key, options=None):
    """Return whether to use the datastore for this key.

    Args:
      key: Key instance.
      options: ContextOptions instance, or None.

    Returns:
      True if the datastore should be used, False otherwise.
    """
    flag = ContextOptions.use_datastore(options)
    if flag is None:
      flag = self._datastore_policy(key)
    if flag is None:
      flag = ContextOptions.use_datastore(self._conn.config)
    if flag is None:
      flag = True
    return flag

  @staticmethod
  def default_memcache_timeout_policy(key):
    """Default memcache timeout policy.

    This defers to _memcache_timeout on the Model class.

    Args:
      key: Key instance.

    Returns:
      Memcache timeout to use (integer), or None.
    """
    timeout = None
    if key is not None and isinstance(key, model.Key):
      modelclass = model.Model._kind_map.get(key.kind())
      if modelclass is not None:
        policy = getattr(modelclass, '_memcache_timeout', None)
        if policy is not None:
          if isinstance(policy, (int, long)):
            timeout = policy
          else:
            timeout = policy(key)
    return timeout

  _memcache_timeout_policy = default_memcache_timeout_policy

  def set_memcache_timeout_policy(self, func):
    """Set the policy function for memcache timeout (expiration).

    Args:
      func: A function that accepts a key instance as argument and returns
        an integer indicating the desired memcache timeout.  May be None.

    If the function returns 0 it implies the default timeout.
    """
    if func is None:
      func = self.default_memcache_timeout_policy
    elif isinstance(func, (int, long)):
      func = lambda unused_key, flag=func: flag
    self._memcache_timeout_policy = func

  def get_memcache_timeout_policy(self):
    """Return the current policy function for memcache timeout (expiration)."""
    return self._memcache_timeout_policy

  def _get_memcache_timeout(self, key, options=None):
    """Return the memcache timeout (expiration) for this key."""
    timeout = ContextOptions.memcache_timeout(options)
    if timeout is None:
      timeout = self._memcache_timeout_policy(key)
    if timeout is None:
      timeout = ContextOptions.memcache_timeout(self._conn.config)
    if timeout is None:
      timeout = 0
    return timeout

  def _get_memcache_deadline(self, options=None):
    """Return the memcache RPC deadline.

    Not to be confused with the memcache timeout, or expiration.

    This is only used by datastore operations when using memcache
    as a cache; it is ignored by the direct memcache calls.

    There is no way to vary this per key or per entity; you must either
    set it on a specific call (e.g. key.get(memcache_deadline=1) or
    in the configuration options of the context's connection.
    """
    # If this returns None, the system default (typically, 5) will apply.
    return ContextOptions.memcache_deadline(options, self._conn.config)

  def _load_from_cache_if_available(self, key):
    """Returns a cached Model instance given the entity key if available.

    Args:
      key: Key instance.

    Returns:
      A Model instance if the key exists in the cache.
    """
    if key in self._cache:
      entity = self._cache[key]  # May be None, meaning "doesn't exist".
      if entity is None or entity._key == key:
        # If entity's key didn't change later, it is ok.
        # See issue 13.  http://goo.gl/jxjOP
        raise tasklets.Return(entity)

  # TODO: What about conflicting requests to different autobatchers,
  # e.g. tasklet A calls get() on a given key while tasklet B calls
  # delete()?  The outcome is nondeterministic, depending on which
  # autobatcher gets run first.  Maybe we should just flag such
  # conflicts as errors, with an overridable policy to resolve them
  # differently?

  @tasklets.tasklet
  def get(self, key, **ctx_options):
    """Return a Model instance given the entity key.

    It will use the context cache if the cache policy for the given
    key is enabled.

    Args:
      key: Key instance.
      **ctx_options: Context options.

    Returns:
      A Model instance if the key exists in the datastore; None otherwise.
    """
    options = _make_ctx_options(ctx_options)
    use_cache = self._use_cache(key, options)
    if use_cache:
      self._load_from_cache_if_available(key)

    use_datastore = self._use_datastore(key, options)
    if (use_datastore and
        isinstance(self._conn, datastore_rpc.TransactionalConnection)):
      use_memcache = False
    else:
      use_memcache = self._use_memcache(key, options)
    ns = key.namespace()
    memcache_deadline = None  # Avoid worries about uninitialized variable.

    if use_memcache:
      mkey = self._memcache_prefix + key.urlsafe()
      memcache_deadline = self._get_memcache_deadline(options)
      mvalue = yield self.memcache_get(mkey, for_cas=use_datastore,
                                       namespace=ns, use_cache=True,
                                       deadline=memcache_deadline)
      # A value may have appeared while yielding.
      if use_cache:
        self._load_from_cache_if_available(key)
      if mvalue not in (_LOCKED, None):
        cls = model.Model._lookup_model(key.kind(),
                                        self._conn.adapter.default_model)
        pb = entity_pb.EntityProto()

        try:
          pb.MergePartialFromString(mvalue)
        except ProtocolBuffer.ProtocolBufferDecodeError:
          logging.warning('Corrupt memcache entry found '
                          'with key %s and namespace %s' % (mkey, ns))
          mvalue = None
        else:
          entity = cls._from_pb(pb)
          # Store the key on the entity since it wasn't written to memcache.
          entity._key = key
          if use_cache:
            # Update in-memory cache.
            self._cache[key] = entity
          raise tasklets.Return(entity)

      if mvalue is None and use_datastore:
        yield self.memcache_set(mkey, _LOCKED, time=_LOCK_TIME, namespace=ns,
                                use_cache=True, deadline=memcache_deadline)
        yield self.memcache_gets(mkey, namespace=ns, use_cache=True,
                                 deadline=memcache_deadline)

    if not use_datastore:
      # NOTE: Do not cache this miss.  In some scenarios this would
      # prevent an app from working properly.
      raise tasklets.Return(None)

    if use_cache:
      entity = yield self._get_batcher.add_once(key, options)
    else:
      entity = yield self._get_batcher.add(key, options)

    if entity is not None:
      if use_memcache and mvalue != _LOCKED:
        # Don't serialize the key since it's already the memcache key.
        pbs = entity._to_pb(set_key=False).SerializePartialToString()
        # Don't attempt to write to memcache if too big.  Note that we
        # use LBYL ("look before you leap") because a multi-value
        # memcache operation would fail for all entities rather than
        # for just the one that's too big.  (Also, the AutoBatcher
        # class doesn't pass back exceptions very well.)
        if len(pbs) <= memcache.MAX_VALUE_SIZE:
          timeout = self._get_memcache_timeout(key, options)
          # Don't use fire-and-forget -- for users who forget
          # @ndb.toplevel, it's too painful to diagnose why their simple
          # code using a single synchronous call doesn't seem to use
          # memcache.  See issue 105.  http://goo.gl/JQZxp
          yield self.memcache_cas(mkey, pbs, time=timeout, namespace=ns,
                                  deadline=memcache_deadline)

    if use_cache:
      # Cache hit or miss.  NOTE: In this case it is okay to cache a
      # miss; the datastore is the ultimate authority.
      self._cache[key] = entity

    raise tasklets.Return(entity)

  @tasklets.tasklet
  def put(self, entity, **ctx_options):
    options = _make_ctx_options(ctx_options)
    # TODO: What if the same entity is being put twice?
    # TODO: What if two entities with the same key are being put?
    key = entity._key
    if key is None:
      # Pass a dummy Key to _use_datastore().
      key = model.Key(entity.__class__, None)
    use_datastore = self._use_datastore(key, options)
    use_memcache = None
    memcache_deadline = None  # Avoid worries about uninitialized variable.

    if entity._has_complete_key():
      use_memcache = self._use_memcache(key, options)
      if use_memcache:
        # Wait for memcache operations before starting datastore RPCs.
        memcache_deadline = self._get_memcache_deadline(options)
        mkey = self._memcache_prefix + key.urlsafe()
        ns = key.namespace()
        if use_datastore:
          yield self.memcache_set(mkey, _LOCKED, time=_LOCK_TIME,
                                  namespace=ns, use_cache=True,
                                  deadline=memcache_deadline)
        else:
          pbs = entity._to_pb(set_key=False).SerializePartialToString()
          # If the byte string to be written is too long for memcache,
          # raise ValueError.  (See LBYL explanation in get().)
          if len(pbs) > memcache.MAX_VALUE_SIZE:
            raise ValueError('Values may not be more than %d bytes in length; '
                             'received %d bytes' % (memcache.MAX_VALUE_SIZE,
                                                    len(pbs)))
          timeout = self._get_memcache_timeout(key, options)
          yield self.memcache_set(mkey, pbs, time=timeout, namespace=ns,
                                  deadline=memcache_deadline)

    if use_datastore:
      key = yield self._put_batcher.add(entity, options)
      if not isinstance(self._conn, datastore_rpc.TransactionalConnection):
        if use_memcache is None:
          use_memcache = self._use_memcache(key, options)
        if use_memcache:
          mkey = self._memcache_prefix + key.urlsafe()
          ns = key.namespace()
          # Don't use fire-and-forget -- see memcache_cas() in get().
          yield self.memcache_delete(mkey, namespace=ns,
                                     deadline=memcache_deadline)

    if key is not None:
      if entity._key != key:
        logging.info('replacing key %s with %s', entity._key, key)
        entity._key = key
      # TODO: For updated entities, could we update the cache first?
      if self._use_cache(key, options):
        # TODO: What if by now the entity is already in the cache?
        self._cache[key] = entity

    raise tasklets.Return(key)

  @tasklets.tasklet
  def delete(self, key, **ctx_options):
    options = _make_ctx_options(ctx_options)
    if self._use_memcache(key, options):
      memcache_deadline = self._get_memcache_deadline(options)
      mkey = self._memcache_prefix + key.urlsafe()
      ns = key.namespace()
      # TODO: If not use_datastore, delete instead of lock?
      yield self.memcache_set(mkey, _LOCKED, time=_LOCK_TIME, namespace=ns,
                              use_cache=True, deadline=memcache_deadline)

    if self._use_datastore(key, options):
      yield self._delete_batcher.add(key, options)
      # TODO: Delete from memcache here?

    if self._use_cache(key, options):
      self._cache[key] = None

  @tasklets.tasklet
  def allocate_ids(self, key, size=None, max=None, **ctx_options):
    options = _make_ctx_options(ctx_options)
    lo_hi = yield self._conn.async_allocate_ids(options, key, size, max)
    raise tasklets.Return(lo_hi)

  @tasklets.tasklet
  def get_indexes(self, **ctx_options):
    options = _make_ctx_options(ctx_options)
    index_list = yield self._conn.async_get_indexes(options)
    raise tasklets.Return(index_list)

  @utils.positional(3)
  def map_query(self, query, callback, pass_batch_into_callback=None,
                options=None, merge_future=None):
    mfut = merge_future
    if mfut is None:
      mfut = tasklets.MultiFuture('map_query')

    @tasklets.tasklet
    def helper():
      try:
        inq = tasklets.SerialQueueFuture()
        query.run_to_queue(inq, self._conn, options)
        while True:
          try:
            batch, i, ent = yield inq.getq()
          except EOFError:
            break
          ent = self._update_cache_from_query_result(ent, options)
          if ent is None:
            continue
          if callback is None:
            val = ent
          else:
            # TODO: If the callback raises, log and ignore.
            if pass_batch_into_callback:
              val = callback(batch, i, ent)
            else:
              val = callback(ent)
          mfut.putq(val)
      except GeneratorExit:
        raise
      except Exception, err:
        _, _, tb = sys.exc_info()
        mfut.set_exception(err, tb)
        raise
      else:
        mfut.complete()

    helper()
    return mfut

  def _update_cache_from_query_result(self, ent, options):
    if isinstance(ent, model.Key):
      return ent  # It was a keys-only query and ent is really a Key.
    if ent._projection:
      return ent  # Never cache partial entities (projection query results).
    key = ent._key
    if not self._use_cache(key, options):
      return ent  # This key should not be cached.

    # Check the cache.  If there is a valid cached entry, substitute
    # that for the result, even if the cache has an explicit None.
    if key in self._cache:
      cached_ent = self._cache[key]
      if (cached_ent is None or
          cached_ent.key == key and cached_ent.__class__ is ent.__class__):
        return cached_ent

    # Update the cache.
    self._cache[key] = ent
    return ent

  @utils.positional(2)
  def iter_query(self, query, callback=None, pass_batch_into_callback=None,
                 options=None):
    return self.map_query(query, callback=callback, options=options,
                          pass_batch_into_callback=pass_batch_into_callback,
                          merge_future=tasklets.SerialQueueFuture())

  @tasklets.tasklet
  def transaction(self, callback, **ctx_options):
    # Will invoke callback() one or more times with the default
    # context set to a new, transactional Context.  Returns a Future.
    # Callback may be a tasklet; in that case it will be waited on.
    options = _make_ctx_options(ctx_options, TransactionOptions)
    propagation = TransactionOptions.propagation(options)
    if propagation is None:
      propagation = TransactionOptions.NESTED

    parent = self
    if propagation == TransactionOptions.NESTED:
      if self.in_transaction():
        raise datastore_errors.BadRequestError(
            'Nested transactions are not supported.')
    elif propagation == TransactionOptions.MANDATORY:
      if not self.in_transaction():
        raise datastore_errors.BadRequestError(
            'Requires an existing transaction.')
      result = callback()
      if isinstance(result, tasklets.Future):
        result = yield result
      raise tasklets.Return(result)
    elif propagation == TransactionOptions.ALLOWED:
      if self.in_transaction():
        result = callback()
        if isinstance(result, tasklets.Future):
          result = yield result
        raise tasklets.Return(result)
    elif propagation == TransactionOptions.INDEPENDENT:
      while parent.in_transaction():
        parent = parent._parent_context
        if parent is None:
          raise datastore_errors.BadRequestError(
              'Context without non-transactional ancestor')
    else:
      raise datastore_errors.BadArgumentError(
          'Invalid propagation value (%s).' % (propagation,))

    app = TransactionOptions.app(options) or key_module._DefaultAppId()
    # Note: zero retries means try it once.
    retries = TransactionOptions.retries(options)
    if retries is None:
      retries = 3
    yield parent.flush()
    for _ in xrange(1 + max(0, retries)):
      transaction = yield parent._conn.async_begin_transaction(options, app)
      tconn = datastore_rpc.TransactionalConnection(
          adapter=parent._conn.adapter,
          config=parent._conn.config,
          transaction=transaction,
          _api_version=parent._conn._api_version)
      tctx = parent.__class__(conn=tconn,
                              auto_batcher_class=parent._auto_batcher_class,
                              parent_context=parent)
      tctx._old_ds_conn = datastore._GetConnection()
      ok = False
      try:
        # Copy memcache policies.  Note that get() will never use
        # memcache in a transaction, but put and delete should do their
        # memcache thing (which is to mark the key as deleted for
        # _LOCK_TIME seconds).  Also note that the in-process cache and
        # datastore policies keep their default (on) state.
        tctx.set_memcache_policy(parent.get_memcache_policy())
        tctx.set_memcache_timeout_policy(parent.get_memcache_timeout_policy())
        tasklets.set_context(tctx)
        datastore._SetConnection(tconn)  # For taskqueue coordination
        try:
          try:
            result = callback()
            if isinstance(result, tasklets.Future):
              result = yield result
          finally:
            yield tctx.flush()
        except GeneratorExit:
          raise
        except Exception:
          t, e, tb = sys.exc_info()
          tconn.async_rollback(options)  # Fire and forget.
          if issubclass(t, datastore_errors.Rollback):
            # TODO: Raise value using tasklets.get_return_value(t)?
            return
          else:
            raise t, e, tb
        else:
          ok = yield tconn.async_commit(options)
          if ok:
            parent._cache.update(tctx._cache)
            yield parent._clear_memcache(tctx._cache)
            raise tasklets.Return(result)
            # The finally clause will run the on-commit queue.
      finally:
        datastore._SetConnection(tctx._old_ds_conn)
        del tctx._old_ds_conn
        if ok:
          # Call the callbacks collected in the transaction context's
          # on-commit queue.  If the transaction failed the queue is
          # abandoned.  We must do this after the connection has been
          # restored, but we can't do it after the for-loop because we
          # leave it by raising tasklets.Return().
          for on_commit_callback in tctx._on_commit_queue:
            on_commit_callback()  # This better not raise.

    # Out of retries
    raise datastore_errors.TransactionFailedError(
        'The transaction could not be committed. Please try again.')

  def in_transaction(self):
    """Return whether a transaction is currently active."""
    return isinstance(self._conn, datastore_rpc.TransactionalConnection)

  def call_on_commit(self, callback):
    """Call a callback upon successful commit of a transaction.

    If not in a transaction, the callback is called immediately.

    In a transaction, multiple callbacks may be registered and will be
    called once the transaction commits, in the order in which they
    were registered.  If the transaction fails, the callbacks will not
    be called.

    If the callback raises an exception, it bubbles up normally.  This
    means: If the callback is called immediately, any exception it
    raises will bubble up immediately.  If the call is postponed until
    commit, remaining callbacks will be skipped and the exception will
    bubble up through the transaction() call.  (However, the
    transaction is already committed at that point.)
    """
    if not self.in_transaction():
      callback()
    else:
      self._on_commit_queue.append(callback)

  def clear_cache(self):
    """Clears the in-memory cache.

    NOTE: This does not affect memcache.
    """
    self._cache.clear()

  @tasklets.tasklet
  def _clear_memcache(self, keys):
    keys = set(key for key in keys if self._use_memcache(key))
    futures = []
    for key in keys:
      mkey = self._memcache_prefix + key.urlsafe()
      ns = key.namespace()
      fut = self.memcache_delete(mkey, namespace=ns)
      futures.append(fut)
    yield futures

  @tasklets.tasklet
  def _memcache_get_tasklet(self, todo, options):
    if not todo:
      raise RuntimeError('Nothing to do.')
    for_cas, namespace, deadline = options
    keys = set()
    for unused_fut, key in todo:
      keys.add(key)
    rpc = memcache.create_rpc(deadline=deadline)
    results = yield self._memcache.get_multi_async(keys, for_cas=for_cas,
                                                   namespace=namespace,
                                                   rpc=rpc)
    for fut, key in todo:
      fut.set_result(results.get(key))

  @tasklets.tasklet
  def _memcache_set_tasklet(self, todo, options):
    if not todo:
      raise RuntimeError('Nothing to do.')
    opname, time, namespace, deadline = options
    methodname = opname + '_multi_async'
    method = getattr(self._memcache, methodname)
    mapping = {}
    for unused_fut, (key, value) in todo:
      mapping[key] = value
    rpc = memcache.create_rpc(deadline=deadline)
    results = yield method(mapping, time=time, namespace=namespace, rpc=rpc)
    for fut, (key, unused_value) in todo:
      if results is None:
        status = memcache.MemcacheSetResponse.ERROR
      else:
        status = results.get(key)
      fut.set_result(status == memcache.MemcacheSetResponse.STORED)

  @tasklets.tasklet
  def _memcache_del_tasklet(self, todo, options):
    if not todo:
      raise RuntimeError('Nothing to do.')
    seconds, namespace, deadline = options
    keys = set()
    for unused_fut, key in todo:
      keys.add(key)
    rpc = memcache.create_rpc(deadline=deadline)
    statuses = yield self._memcache.delete_multi_async(keys, seconds=seconds,
                                                       namespace=namespace,
                                                       rpc=rpc)
    status_key_mapping = {}
    if statuses:  # On network error, statuses is None.
      for key, status in zip(keys, statuses):
        status_key_mapping[key] = status
    for fut, key in todo:
      status = status_key_mapping.get(key, memcache.DELETE_NETWORK_FAILURE)
      fut.set_result(status)

  @tasklets.tasklet
  def _memcache_off_tasklet(self, todo, options):
    if not todo:
      raise RuntimeError('Nothing to do.')
    initial_value, namespace, deadline = options
    mapping = {}  # {key: delta}
    for unused_fut, (key, delta) in todo:
      mapping[key] = delta
    rpc = memcache.create_rpc(deadline=deadline)
    results = yield self._memcache.offset_multi_async(
        mapping, initial_value=initial_value, namespace=namespace, rpc=rpc)
    for fut, (key, unused_delta) in todo:
      fut.set_result(results.get(key))

  def memcache_get(self, key, for_cas=False, namespace=None, use_cache=False,
                   deadline=None):
    """An auto-batching wrapper for memcache.get() or .get_multi().

    Args:
      key: Key to set.  This must be a string; no prefix is applied.
      for_cas: If True, request and store CAS ids on the Context.
      namespace: Optional namespace.
      deadline: Optional deadline for the RPC.

    Returns:
      A Future (!) whose return value is the value retrieved from
      memcache, or None.
    """
    if not isinstance(key, basestring):
      raise TypeError('key must be a string; received %r' % key)
    if not isinstance(for_cas, bool):
      raise TypeError('for_cas must be a bool; received %r' % for_cas)
    if namespace is None:
      namespace = namespace_manager.get_namespace()
    options = (for_cas, namespace, deadline)
    batcher = self._memcache_get_batcher
    if use_cache:
      return batcher.add_once(key, options)
    else:
      return batcher.add(key, options)

  # XXX: Docstrings below.

  def memcache_gets(self, key, namespace=None, use_cache=False, deadline=None):
    return self.memcache_get(key, for_cas=True, namespace=namespace,
                             use_cache=use_cache, deadline=deadline)

  def memcache_set(self, key, value, time=0, namespace=None, use_cache=False,
                   deadline=None):
    if not isinstance(key, basestring):
      raise TypeError('key must be a string; received %r' % key)
    if not isinstance(time, (int, long)):
      raise TypeError('time must be a number; received %r' % time)
    if namespace is None:
      namespace = namespace_manager.get_namespace()
    options = ('set', time, namespace, deadline)
    batcher = self._memcache_set_batcher
    if use_cache:
      return batcher.add_once((key, value), options)
    else:
      return batcher.add((key, value), options)

  def memcache_add(self, key, value, time=0, namespace=None, deadline=None):
    if not isinstance(key, basestring):
      raise TypeError('key must be a string; received %r' % key)
    if not isinstance(time, (int, long)):
      raise TypeError('time must be a number; received %r' % time)
    if namespace is None:
      namespace = namespace_manager.get_namespace()
    return self._memcache_set_batcher.add((key, value),
                                          ('add', time, namespace, deadline))

  def memcache_replace(self, key, value, time=0, namespace=None, deadline=None):
    if not isinstance(key, basestring):
      raise TypeError('key must be a string; received %r' % key)
    if not isinstance(time, (int, long)):
      raise TypeError('time must be a number; received %r' % time)
    if namespace is None:
      namespace = namespace_manager.get_namespace()
    options = ('replace', time, namespace, deadline)
    return self._memcache_set_batcher.add((key, value), options)

  def memcache_cas(self, key, value, time=0, namespace=None, deadline=None):
    if not isinstance(key, basestring):
      raise TypeError('key must be a string; received %r' % key)
    if not isinstance(time, (int, long)):
      raise TypeError('time must be a number; received %r' % time)
    if namespace is None:
      namespace = namespace_manager.get_namespace()
    return self._memcache_set_batcher.add((key, value),
                                          ('cas', time, namespace, deadline))

  def memcache_delete(self, key, seconds=0, namespace=None, deadline=None):
    if not isinstance(key, basestring):
      raise TypeError('key must be a string; received %r' % key)
    if not isinstance(seconds, (int, long)):
      raise TypeError('seconds must be a number; received %r' % seconds)
    if namespace is None:
      namespace = namespace_manager.get_namespace()
    return self._memcache_del_batcher.add(key, (seconds, namespace, deadline))

  def memcache_incr(self, key, delta=1, initial_value=None, namespace=None,
                    deadline=None):
    if not isinstance(key, basestring):
      raise TypeError('key must be a string; received %r' % key)
    if not isinstance(delta, (int, long)):
      raise TypeError('delta must be a number; received %r' % delta)
    if initial_value is not None and not isinstance(initial_value, (int, long)):
      raise TypeError('initial_value must be a number or None; received %r' %
                      initial_value)
    if namespace is None:
      namespace = namespace_manager.get_namespace()
    return self._memcache_off_batcher.add((key, delta),
                                          (initial_value, namespace, deadline))

  def memcache_decr(self, key, delta=1, initial_value=None, namespace=None,
                    deadline=None):
    if not isinstance(key, basestring):
      raise TypeError('key must be a string; received %r' % key)
    if not isinstance(delta, (int, long)):
      raise TypeError('delta must be a number; received %r' % delta)
    if initial_value is not None and not isinstance(initial_value, (int, long)):
      raise TypeError('initial_value must be a number or None; received %r' %
                      initial_value)
    if namespace is None:
      namespace = namespace_manager.get_namespace()
    return self._memcache_off_batcher.add((key, -delta),
                                          (initial_value, namespace, deadline))

  @tasklets.tasklet
  def urlfetch(self, url, payload=None, method='GET', headers={},
               allow_truncated=False, follow_redirects=True,
               validate_certificate=None, deadline=None, callback=None):
    rpc = urlfetch.create_rpc(deadline=deadline, callback=callback)
    urlfetch.make_fetch_call(rpc, url,
                             payload=payload,
                             method=method,
                             headers=headers,
                             allow_truncated=allow_truncated,
                             follow_redirects=follow_redirects,
                             validate_certificate=validate_certificate)
    result = yield rpc
    raise tasklets.Return(result)
