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




"""Asynchronous datastore API.

This is designed to be the lowest-level API to be used by all Python
datastore client libraries.
"""









__all__ = ['AbstractAdapter',
           'BaseConfiguration',
           'BaseConnection',
           'ConfigOption',
           'Configuration',
           'Connection',
           'IdentityAdapter',
           'MultiRpc',
           'TransactionalConnection',
           'TransactionOptions',
          ]




import collections
import copy
import functools
import logging
import os


from google.appengine.datastore import entity_pb


from google.appengine.api import api_base_pb
from google.appengine.api import apiproxy_rpc
from google.appengine.api import apiproxy_stub_map

from google.appengine.api import datastore_errors
from google.appengine.api import datastore_types

from google.appengine.api.app_identity import app_identity
from google.appengine.datastore import datastore_pb
from google.appengine.datastore import datastore_pbs
from google.appengine.datastore import datastore_v4_pb
from google.appengine.runtime import apiproxy_errors

_CLOUD_DATASTORE_ENABLED = datastore_pbs._CLOUD_DATASTORE_ENABLED
if _CLOUD_DATASTORE_ENABLED:
  from google.appengine.datastore.datastore_pbs import googledatastore





_MAX_ID_BATCH_SIZE = 1000 * 1000 * 1000


_DATASTORE_V3 = 'datastore_v3'
_DATASTORE_V4 = 'datastore_v4'
_CLOUD_DATASTORE_V1 = 'cloud_datastore_v1beta3'



def _positional(max_pos_args):
  """A decorator to declare that only the first N arguments may be positional.

  Note that for methods, n includes 'self'.
  """
  def positional_decorator(wrapped):
    @functools.wraps(wrapped)
    def positional_wrapper(*args, **kwds):
      if len(args) > max_pos_args:
        plural_s = ''
        if max_pos_args != 1:
          plural_s = 's'
        raise TypeError(
          '%s() takes at most %d positional argument%s (%d given)' %
          (wrapped.__name__, max_pos_args, plural_s, len(args)))
      return wrapped(*args, **kwds)
    return positional_wrapper
  return positional_decorator


def _GetDatastoreType(app=None):
  """Tries to get the datastore type for the given app.

  This function is only guaranteed to return something other than
  UNKNOWN_DATASTORE when running in production and querying the current app.
  """
  current_app = datastore_types.ResolveAppId(None)
  if app not in (current_app, None):
    return BaseConnection.UNKNOWN_DATASTORE




  partition, _, _ = app_identity._ParseFullAppId(current_app)
  if partition:
    return BaseConnection.HIGH_REPLICATION_DATASTORE
  return BaseConnection.MASTER_SLAVE_DATASTORE


class AbstractAdapter(object):
  """Abstract interface between protobufs and user-level classes.

  This class defines conversions between the protobuf classes defined
  in entity_pb.py on the one hand, and the corresponding user-level
  classes (which are defined by higher-level API libraries such as
  datastore.py or db.py) on the other hand.

  The premise is that the code in this module is agnostic about the
  user-level classes used to represent keys and entities, while at the
  same time provinging APIs that accept or return such user-level
  classes.

  Higher-level libraries must subclass this abstract class and pass an
  instance of the subclass to the Connection they want to use.

  These methods may raise datastore_errors.Error for bad inputs.
  """

  _entity_converter = datastore_pbs.get_entity_converter()
  _query_converter = datastore_pbs._QueryConverter(_entity_converter)

  def __init__(self, id_resolver=None):
    if id_resolver:
      self._entity_converter = datastore_pbs.get_entity_converter(
          id_resolver)
      self._query_converter = datastore_pbs._QueryConverter(
          self._entity_converter)

  def get_entity_converter(self):
    return self._entity_converter

  def get_query_converter(self):
    return self._query_converter

  def pb_to_key(self, pb):
    """Turn an entity_pb.Reference into a user-level key."""
    raise NotImplementedError

  def pb_v1_to_key(self, pb):
    """Turn an googledatastore.Key into a user-level key."""
    v3_ref = entity_pb.Reference()
    self._entity_converter.v1_to_v3_reference(pb, v3_ref)
    return self.pb_to_key(v3_ref)

  def pb_to_entity(self, pb):
    """Turn an entity_pb.EntityProto into a user-level entity."""
    raise NotImplementedError

  def pb_v1_to_entity(self, pb, is_projection):
    """Turn an googledatastore.Entity into a user-level entity."""
    v3_entity = entity_pb.EntityProto()
    self._entity_converter.v1_to_v3_entity(pb, v3_entity, is_projection)
    return self.pb_to_entity(v3_entity)

  def pb_v1_to_query_result(self, pb, query_options):
    """Turn an googledatastore.Entity into a user-level query result."""
    if query_options.keys_only:
      return self.pb_v1_to_key(pb.key)
    else:
      return self.pb_v1_to_entity(pb, bool(query_options.projection))

  def pb_to_index(self, pb):
    """Turn an entity_pb.CompositeIndex into a user-level Index
    representation."""
    raise NotImplementedError

  def pb_to_query_result(self, pb, query_options):
    """Turn an entity_pb.EntityProto into a user-level query result."""
    if query_options.keys_only:
      return self.pb_to_key(pb.key())
    else:
      return self.pb_to_entity(pb)

  def key_to_pb(self, key):
    """Turn a user-level key into an entity_pb.Reference."""
    raise NotImplementedError

  def key_to_pb_v1(self, key):
    """Turn a user-level key into an googledatastore.Key."""
    v3_ref = self.key_to_pb(key)
    v1_key = googledatastore.Key()
    self._entity_converter.v3_to_v1_key(v3_ref, v1_key)
    return v1_key

  def entity_to_pb(self, entity):
    """Turn a user-level entity into an entity_pb.EntityProto."""
    raise NotImplementedError

  def entity_to_pb_v1(self, entity):
    """Turn a user-level entity into an googledatastore.Key."""
    v3_entity = self.entity_to_pb(entity)
    v1_entity = googledatastore.Entity()
    self._entity_converter.v3_to_v1_entity(v3_entity, v1_entity)
    return v1_entity

  def new_key_pb(self):
    """Create a new, empty entity_pb.Reference."""
    return entity_pb.Reference()

  def new_entity_pb(self):
    """Create a new, empty entity_pb.EntityProto."""
    return entity_pb.EntityProto()


class IdentityAdapter(AbstractAdapter):
  """A concrete adapter that implements the identity mapping.

  This is used as the default when a Connection is created without
  specifying an adapter; that's primarily for testing.
  """

  def __init__(self, id_resolver=None):
    super(IdentityAdapter, self).__init__(id_resolver)

  def pb_to_key(self, pb):
    return pb

  def pb_to_entity(self, pb):
    return pb

  def key_to_pb(self, key):
    return key

  def entity_to_pb(self, entity):
    return entity

  def pb_to_index(self, pb):
    return pb


class ConfigOption(object):
  """A descriptor for a Configuration option.

  This class is used to create a configuration option on a class that inherits
  from BaseConfiguration. A validator function decorated with this class will
  be converted to a read-only descriptor and BaseConfiguration will implement
  constructor and merging logic for that configuration option. A validator
  function takes a single non-None value to validate and either throws
  an exception or returns that value (or an equivalent value). A validator is
  called once at construction time, but only if a non-None value for the
  configuration option is specified the constructor's keyword arguments.
  """

  def __init__(self, validator):
    self.validator = validator

  def __get__(self, obj, objtype):
    if obj is None:
      return self
    return obj._values.get(self.validator.__name__, None)

  def __set__(self, obj, value):
    raise AttributeError('Configuration options are immutable (%s)' %
                         (self.validator.__name__,))

  def __call__(self, *args):
    """Gets the first non-None value for this option from the given args.

    Args:
      *arg: Any number of configuration objects or None values.

    Returns:
      The first value for this ConfigOption found in the given configuration
    objects or None.

    Raises:
      datastore_errors.BadArgumentError if a given in object is not a
    configuration object.
    """
    name = self.validator.__name__
    for config in args:

      if isinstance(config, (type(None), apiproxy_stub_map.UserRPC)):
        pass
      elif not isinstance(config, BaseConfiguration):
        raise datastore_errors.BadArgumentError(
            'invalid config argument (%r)' % (config,))
      elif name in config._values and self is config._options[name]:
        return config._values[name]
    return None


class _ConfigurationMetaClass(type):
  """The metaclass for all Configuration types.

  This class is needed to store a class specific list of all ConfigOptions in
  cls._options, and insert a __slots__ variable into the class dict before the
  class is created to impose immutability.
  """

  def __new__(metaclass, classname, bases, classDict):
    if classname == '_MergedConfiguration':

      return type.__new__(metaclass, classname, bases, classDict)



    if object in bases:
      classDict['__slots__'] = ['_values']
    else:
      classDict['__slots__'] = []
    cls = type.__new__(metaclass, classname, bases, classDict)
    if object not in bases:
      options = {}
      for c in reversed(cls.__mro__):
        if '_options' in c.__dict__:
          options.update(c.__dict__['_options'])
      cls._options = options
      for option, value in cls.__dict__.iteritems():
        if isinstance(value, ConfigOption):
          if cls._options.has_key(option):
            raise TypeError('%s cannot be overridden (%s)' %
                            (option, cls.__name__))
          cls._options[option] = value
          value._cls = cls
    return cls




class BaseConfiguration(object):
  """A base class for a configuration object.

  Subclasses should provide validation functions for every configuration option
  they accept. Any public function decorated with ConfigOption is assumed to be
  a validation function for an option of the same name. All validation functions
  take a single non-None value to validate and must throw an exception or return
  the value to store.

  This class forces subclasses to be immutable and exposes a read-only
  property for every accepted configuration option. Configuration options set by
  passing keyword arguments to the constructor. The constructor and merge
  function are designed to avoid creating redundant copies and may return
  the configuration objects passed to them if appropriate.

  Setting an option to None is the same as not specifying the option except in
  the case where the 'config' argument is given. In this case the value on
  'config' of the same name is ignored. Options that are not specified will
  return 'None' when accessed.
  """

  __metaclass__ = _ConfigurationMetaClass
  _options = {}

  def __new__(cls, config=None, **kwargs):
    """Immutable constructor.

    If 'config' is non-None all configuration options will default to the value
    it contains unless the configuration option is explicitly set to 'None' in
    the keyword arguments. If 'config' is None then all configuration options
    default to None.

    Args:
      config: Optional base configuration providing default values for
        parameters not specified in the keyword arguments.
      **kwargs: Configuration options to store on this object.

    Returns:
      Either a new Configuration object or (if it would be equivalent)
      the config argument unchanged, but never None.
    """
    if config is None:
      pass
    elif isinstance(config, BaseConfiguration):
      if cls is config.__class__ and config.__is_stronger(**kwargs):

        return config

      for key, value in config._values.iteritems():

        if issubclass(cls, config._options[key]._cls):
          kwargs.setdefault(key, value)
    else:
      raise datastore_errors.BadArgumentError(
          'config argument should be Configuration (%r)' % (config,))

    obj = super(BaseConfiguration, cls).__new__(cls)
    obj._values = {}
    for key, value in kwargs.iteritems():
      if value is not None:
        try:
          config_option = obj._options[key]
        except KeyError, err:
          raise TypeError('Unknown configuration option (%s)' % err)
        value = config_option.validator(value)
        if value is not None:
          obj._values[key] = value
    return obj

  def __eq__(self, other):
    if self is other:
      return True
    if not isinstance(other, BaseConfiguration):
      return NotImplemented
    return self._options == other._options and self._values == other._values

  def __ne__(self, other):
    equal = self.__eq__(other)
    if equal is NotImplemented:
      return equal
    return not equal

  def __hash__(self):
    return (hash(frozenset(self._values.iteritems())) ^
            hash(frozenset(self._options.iteritems())))

  def __repr__(self):
    args = []
    for key_value in sorted(self._values.iteritems()):
      args.append('%s=%r' % key_value)
    return '%s(%s)' % (self.__class__.__name__, ', '.join(args))

  def __is_stronger(self, **kwargs):
    """Internal helper to ask whether a configuration is stronger than another.

    A configuration is stronger when it contains every name/value pair in
    kwargs.

    Example: a configuration with:
      (deadline=5, on_configuration=None, read_policy=EVENTUAL_CONSISTENCY)
    is stronger than:
      (deadline=5, on_configuration=None)
    but not stronger than:
      (deadline=5, on_configuration=None, read_policy=None)
    or
      (deadline=10, on_configuration=None, read_policy=None).

    More formally:
      - Any value is stronger than an unset value;
      - Any value is stronger than itself.

    Returns:
      True if each of the self attributes is stronger than the
    corresponding argument.
    """
    for key, value in kwargs.iteritems():
      if key not in self._values or value != self._values[key]:
        return False
    return True

  @classmethod
  def is_configuration(cls, obj):
    """True if configuration obj handles all options of this class.

    Use this method rather than isinstance(obj, cls) to test if a
    configuration object handles the options of cls (is_configuration
    is handled specially for results of merge which may handle the options
    of unrelated configuration classes).

    Args:
      obj: the object to test.
    """
    return isinstance(obj, BaseConfiguration) and obj._is_configuration(cls)

  def _is_configuration(self, cls):
    return isinstance(self, cls)

  def merge(self, config):
    """Merge two configurations.

    The configuration given as an argument (if any) takes priority;
    defaults are filled in from the current configuration.

    Args:
      config: Configuration providing overrides, or None (but cannot
        be omitted).

    Returns:
      Either a new configuration object or (if it would be equivalent)
      self or the config argument unchanged, but never None.

    Raises:
      BadArgumentError if self or config are of configurations classes
      with conflicting options (i.e. the same option name defined in
      two different configuration classes).
    """
    if config is None or config is self:

      return self



    if not (isinstance(config, _MergedConfiguration) or
            isinstance(self, _MergedConfiguration)):



      if isinstance(config, self.__class__):
        for key in self._values:
          if key not in config._values:
            break
        else:
          return config
      if isinstance(self, config.__class__):
        if  self.__is_stronger(**config._values):
          return self


      def _quick_merge(obj):
        obj._values = self._values.copy()
        obj._values.update(config._values)
        return obj

      if isinstance(config, self.__class__):
        return _quick_merge(type(config)())
      if isinstance(self, config.__class__):
        return _quick_merge(type(self)())


    return _MergedConfiguration(config, self)

  def __getstate__(self):
    return {'_values': self._values}

  def __setstate__(self, state):


    obj = self.__class__(**state['_values'])
    self._values = obj._values


class _MergedConfiguration(BaseConfiguration):
  """Helper class to handle merges of configurations.

  Instances of _MergedConfiguration are in some sense "subclasses" of the
  argument configurations, i.e.:
  - they handle exactly the configuration options of the argument configurations
  - the value of these options is taken in priority order from the arguments
  - isinstance is true on this configuration if it is true on any of the
    argument configurations
  This class raises an exception if two argument configurations have an option
  with the same name but coming from a different configuration class.
  """
  __slots__ = ['_values', '_configs', '_options', '_classes']

  def __new__(cls, *configs):
    obj = super(BaseConfiguration, cls).__new__(cls)
    obj._configs = configs


    obj._options = {}
    for config in configs:
      for name, option in config._options.iteritems():
        if name in obj._options:
          if option is not obj._options[name]:
            error = ("merge conflict on '%s' from '%s' and '%s'" %
                     (name, option._cls.__name__,
                      obj._options[name]._cls.__name__))
            raise datastore_errors.BadArgumentError(error)
        obj._options[name] = option

    obj._values = {}
    for config in reversed(configs):
      for name, value in config._values.iteritems():
        obj._values[name] = value

    return obj

  def __repr__(self):
    return '%s%r' % (self.__class__.__name__, tuple(self._configs))

  def _is_configuration(self, cls):
    for config in self._configs:
      if config._is_configuration(cls):
        return True
    return False

  def __getattr__(self, name):
    if name in self._options:
      if name in self._values:
        return self._values[name]
      else:
        return None
    raise AttributeError("Configuration has no attribute '%s'" % (name,))

  def __getstate__(self):
    return {'_configs': self._configs}

  def __setstate__(self, state):

    obj = _MergedConfiguration(*state['_configs'])
    self._values = obj._values
    self._configs = obj._configs
    self._options = obj._options


class Configuration(BaseConfiguration):
  """Configuration parameters for datastore RPCs.

  This class reserves the right to define configuration options of any name
  except those that start with 'user_'. External subclasses should only define
  function or variables with names that start with in 'user_'.

  The options defined on this class include generic RPC parameters (deadline)
  but also datastore-specific parameters (on_completion and read_policy).

  Options are set by passing keyword arguments to the constructor corresponding
  to the configuration options defined below.
  """


  STRONG_CONSISTENCY = 0
  """A read consistency that will return up to date results."""

  EVENTUAL_CONSISTENCY = 1
  """A read consistency that allows requests to return possibly stale results.

  This read_policy tends to be faster and less prone to unavailability/timeouts.
  May return transactionally inconsistent results in rare cases.
  """

  APPLY_ALL_JOBS_CONSISTENCY = 2
  """A read consistency that aggressively tries to find write jobs to apply.

  Use of this read policy is strongly discouraged.

  This read_policy tends to be more costly and is only useful in a few specific
  cases. It is equivalent to splitting a request by entity group and wrapping
  each batch in a separate transaction. Cannot be used with non-ancestor
  queries.
  """


  ALL_READ_POLICIES = frozenset((STRONG_CONSISTENCY,
                                 EVENTUAL_CONSISTENCY,
                                 APPLY_ALL_JOBS_CONSISTENCY,
                                 ))



  @ConfigOption
  def deadline(value):
    """The deadline for any RPC issued.

    If unset the system default will be used which is typically 5 seconds.

    Raises:
      BadArgumentError if value is not a number or is less than zero.
    """
    if not isinstance(value, (int, long, float)):
      raise datastore_errors.BadArgumentError(
        'deadline argument should be int/long/float (%r)' % (value,))
    if value <= 0:
      raise datastore_errors.BadArgumentError(
        'deadline argument should be > 0 (%r)' % (value,))
    return value

  @ConfigOption
  def on_completion(value):
    """A callback that is invoked when any RPC completes.

    If specified, it will be called with a UserRPC object as argument when an
    RPC completes.

    NOTE: There is a subtle but important difference between
    UserRPC.callback and Configuration.on_completion: on_completion is
    called with the RPC object as its first argument, where callback is
    called without arguments.  (Because a Configuration's on_completion
    function can be used with many UserRPC objects, it would be awkward
    if it was called without passing the specific RPC.)
    """


    return value

  @ConfigOption
  def read_policy(value):
    """The read policy to use for any relevent RPC.

    if unset STRONG_CONSISTENCY will be used.

    Raises:
      BadArgumentError if value is not a known read policy.
    """
    if value not in Configuration.ALL_READ_POLICIES:
      raise datastore_errors.BadArgumentError(
        'read_policy argument invalid (%r)' % (value,))
    return value

  @ConfigOption
  def force_writes(value):
    """If a write request should succeed even if the app is read-only.

    This only applies to user controlled read-only periods.
    """
    if not isinstance(value, bool):
      raise datastore_errors.BadArgumentError(
        'force_writes argument invalid (%r)' % (value,))
    return value

  @ConfigOption
  def max_entity_groups_per_rpc(value):
    """The maximum number of entity groups that can be represented in one rpc.

    For a non-transactional operation that involves more entity groups than the
    maximum, the operation will be performed by executing multiple, asynchronous
    rpcs to the datastore, each of which has no more entity groups represented
    than the maximum.  So, if a put() operation has 8 entity groups and the
    maximum is 3, we will send 3 rpcs, 2 with 3 entity groups and 1 with 2
    entity groups.  This is a performance optimization - in many cases
    multiple, small, concurrent rpcs will finish faster than a single large
    rpc.  The optimal value for this property will be application-specific, so
    experimentation is encouraged.
    """
    if not (isinstance(value, (int, long)) and value > 0):
      raise datastore_errors.BadArgumentError(
          'max_entity_groups_per_rpc should be a positive integer')
    return value

  @ConfigOption
  def max_allocate_ids_keys(value):
    """The maximum number of keys in a v1 AllocateIds rpc."""
    if not (isinstance(value, (int, long)) and value > 0):
      raise datastore_errors.BadArgumentError(
          'max_allocate_ids_keys should be a positive integer')
    return value

  @ConfigOption
  def max_rpc_bytes(value):
    """The maximum serialized size of a Get/Put/Delete without batching."""
    if not (isinstance(value, (int, long)) and value > 0):
      raise datastore_errors.BadArgumentError(
        'max_rpc_bytes should be a positive integer')
    return value

  @ConfigOption
  def max_get_keys(value):
    """The maximum number of keys in a Get without batching."""
    if not (isinstance(value, (int, long)) and value > 0):
      raise datastore_errors.BadArgumentError(
        'max_get_keys should be a positive integer')
    return value

  @ConfigOption
  def max_put_entities(value):
    """The maximum number of entities in a Put without batching."""
    if not (isinstance(value, (int, long)) and value > 0):
      raise datastore_errors.BadArgumentError(
        'max_put_entities should be a positive integer')
    return value

  @ConfigOption
  def max_delete_keys(value):
    """The maximum number of keys in a Delete without batching."""
    if not (isinstance(value, (int, long)) and value > 0):
      raise datastore_errors.BadArgumentError(
        'max_delete_keys should be a positive integer')
    return value



_NOOP_SERVICE = 'cloud_datastore_noop'


class _NoopRPC(apiproxy_rpc.RPC):
  """An RPC implementation that does not modify the response object."""

  def __init__(self):
    super(_NoopRPC, self).__init__()

  def _WaitImpl(self):
    return True

  def _MakeCallImpl(self):
    self._state = apiproxy_rpc.RPC.FINISHING


class _NoopRPCStub(object):
  """An RPC stub which always creates a NoopRPC."""

  def CreateRPC(self):
    return _NoopRPC()


class MultiRpc(object):
  """A wrapper around multiple UserRPC objects.

  This provides an API similar to that of UserRPC, but wraps multiple
  RPCs such that e.g. .wait() blocks until all wrapped RPCs are
  complete, and .get_result() returns the combined results from all
  wrapped RPCs.

  Class methods:
    flatten(rpcs): Expand a list of UserRPCs and MultiRpcs
      into a list of UserRPCs.
    wait_any(rpcs): Call UserRPC.wait_any(flatten(rpcs)).
    wait_all(rpcs): Call UserRPC.wait_all(flatten(rpcs)).

  Instance methods:
    wait(): Wait for all RPCs.
    check_success(): Wait and then check success for all RPCs.
    get_result(): Wait for all, check successes, then merge
      all results.

  Instance attributes:
    rpcs: The list of wrapped RPCs (returns a copy).
    state: The combined state of all RPCs.
  """

  def __init__(self, rpcs, extra_hook=None):
    """Constructor.

    Args:
      rpcs: A list of UserRPC and MultiRpc objects; it is flattened
        before being stored.
      extra_hook: Optional function to be applied to the final result
        or list of results.
    """
    self.__rpcs = self.flatten(rpcs)
    self.__extra_hook = extra_hook

  @property
  def rpcs(self):
    """Get a flattened list containing the RPCs wrapped.

    This returns a copy to prevent users from modifying the state.
    """
    return list(self.__rpcs)

  @property
  def state(self):
    """Get the combined state of the wrapped RPCs.

    This mimics the UserRPC.state property.  If all wrapped RPCs have
    the same state, that state is returned; otherwise, RUNNING is
    returned (which here really means 'neither fish nor flesh').
    """
    lo = apiproxy_rpc.RPC.FINISHING
    hi = apiproxy_rpc.RPC.IDLE
    for rpc in self.__rpcs:
      lo = min(lo, rpc.state)
      hi = max(hi, rpc.state)
    if lo == hi:
      return lo
    return apiproxy_rpc.RPC.RUNNING

  def wait(self):
    """Wait for all wrapped RPCs to finish.

    This mimics the UserRPC.wait() method.
    """
    apiproxy_stub_map.UserRPC.wait_all(self.__rpcs)

  def check_success(self):
    """Check success of all wrapped RPCs, failing if any of the failed.

    This mimics the UserRPC.check_success() method.

    NOTE: This first waits for all wrapped RPCs to finish before
    checking the success of any of them.  This makes debugging easier.
    """
    self.wait()
    for rpc in self.__rpcs:
      rpc.check_success()

  def get_result(self):
    """Return the combined results of all wrapped RPCs.

    This mimics the UserRPC.get_results() method.  Multiple results
    are combined using the following rules:

    1. If there are no wrapped RPCs, an empty list is returned.

    2. If exactly one RPC is wrapped, its result is returned.

    3. If more than one RPC is wrapped, the result is always a list,
       which is constructed from the wrapped results as follows:

       a. A wrapped result equal to None is ignored;

       b. A wrapped result that is a list (but not any other type of
          sequence!) has its elements added to the result list.

       c. Any other wrapped result is appended to the result list.

    After all results are combined, if __extra_hook is set, it is
    called with the combined results and its return value becomes the
    final result.

    NOTE: This first waits for all wrapped RPCs to finish, and then
    checks all their success.  This makes debugging easier.
    """










    if len(self.__rpcs) == 1:
      results = self.__rpcs[0].get_result()
    else:
      results = []


      for rpc in self.__rpcs:
        result = rpc.get_result()
        if isinstance(result, list):
          results.extend(result)
        elif result is not None:
          results.append(result)
    if self.__extra_hook is not None:
      results = self.__extra_hook(results)
    return results

  @classmethod
  def flatten(cls, rpcs):
    """Return a list of UserRPCs, expanding MultiRpcs in the argument list.

    For example: given 4 UserRPCs rpc1 through rpc4,
    flatten(rpc1, MultiRpc([rpc2, rpc3], rpc4)
    returns [rpc1, rpc2, rpc3, rpc4].

    Args:
      rpcs: A list of UserRPC and MultiRpc objects.

    Returns:
      A list of UserRPC objects.
    """
    flat = []
    for rpc in rpcs:
      if isinstance(rpc, MultiRpc):



        flat.extend(rpc.__rpcs)
      else:
        if not isinstance(rpc, apiproxy_stub_map.UserRPC):
          raise datastore_errors.BadArgumentError(
            'Expected a list of UserRPC object (%r)' % (rpc,))
        flat.append(rpc)
    return flat

  @classmethod
  def wait_any(cls, rpcs):
    """Wait until one of the RPCs passed in is finished.

    This mimics UserRPC.wait_any().

    Args:
      rpcs: A list of UserRPC and MultiRpc objects.

    Returns:
      A UserRPC object or None.
    """
    return apiproxy_stub_map.UserRPC.wait_any(cls.flatten(rpcs))

  @classmethod
  def wait_all(cls, rpcs):
    """Wait until all RPCs passed in are finished.

    This mimics UserRPC.wait_all().

    Args:
      rpcs: A list of UserRPC and MultiRpc objects.
    """
    apiproxy_stub_map.UserRPC.wait_all(cls.flatten(rpcs))


class BaseConnection(object):
  """Datastore connection base class.

  NOTE: Do not instantiate this class; use Connection or
  TransactionalConnection instead.

  This is not a traditional database connection -- with App Engine, in
  the end the connection is always implicit in the process state.
  There is also no intent to be compatible with PEP 249 (Python's
  Database-API).  But it is a useful abstraction to have an explicit
  object that manages the database interaction, and especially
  transactions.  Other settings related to the App Engine datastore
  are also stored here (e.g. the RPC timeout).

  A similar class in the Java API to the App Engine datastore is
  DatastoreServiceConfig (but in Java, transaction state is always
  held by the current thread).

  To use transactions, call connection.new_transaction().  This
  returns a new connection (an instance of the TransactionalConnection
  subclass) which you should use for all operations in the
  transaction.

  This model supports multiple unrelated concurrent transactions (but
  not nested transactions as this concept is commonly understood in
  the relational database world).

  When the transaction is done, call .commit() or .rollback() on the
  transactional connection.  If .commit() returns False, the
  transaction failed and none of your operations made it to the
  datastore; if it returns True, all your operations were committed.
  The transactional connection cannot be used once .commit() or
  .rollback() is called.

  Transactions are created lazily.  The first operation that requires
  a transaction handle will issue the low-level BeginTransaction
  request and wait for it to return.

  Transactions keep track of the entity group.  All operations within
  a transaction must use the same entity group.  An entity group
  (currently) comprises an app id, a namespace, and a top-level key (a
  kind and an id or name).  The first operation performed determines
  the entity group.  There is some special-casing when the first
  operation is a put() of an entity with an incomplete key; in this case
  the entity group is determined after the operation returns.

  NOTE: the datastore stubs in the dev_appserver currently support
  only a single concurrent transaction.  Specifically, the (old) file
  stub locks up if an attempt is made to start a new transaction while
  a transaction is already in use, whereas the sqlite stub fails an
  assertion.
  """

  UNKNOWN_DATASTORE = 0
  MASTER_SLAVE_DATASTORE = 1
  HIGH_REPLICATION_DATASTORE = 2

  __SUPPORTED_VERSIONS = frozenset((_DATASTORE_V3,
                                    _CLOUD_DATASTORE_V1))

  @_positional(1)
  def __init__(self, adapter=None, config=None, _api_version=_DATASTORE_V3):
    """Constructor.

    All arguments should be specified as keyword arguments.

    Args:
      adapter: Optional AbstractAdapter subclass instance;
        default IdentityAdapter.
      config: Optional Configuration object.
    """
    if adapter is None:
      adapter = IdentityAdapter()
    if not isinstance(adapter, AbstractAdapter):
      raise datastore_errors.BadArgumentError(
          'invalid adapter argument (%r)' % (adapter,))
    self.__adapter = adapter

    if config is None:
      config = Configuration()
    elif not Configuration.is_configuration(config):
      raise datastore_errors.BadArgumentError(
          'invalid config argument (%r)' % (config,))
    self.__config = config

    if _api_version not in self.__SUPPORTED_VERSIONS:
      raise datastore_errors.BadArgumentError(
          'unsupported API version (%s)' % (_api_version,))
    if _api_version == _CLOUD_DATASTORE_V1:
      if not _CLOUD_DATASTORE_ENABLED:
        raise datastore_errors.BadArgumentError(
            datastore_pbs.MISSING_CLOUD_DATASTORE_MESSAGE)

      apiproxy_stub_map.apiproxy.ReplaceStub(_NOOP_SERVICE, _NoopRPCStub())

    self._api_version = _api_version

    self.__pending_rpcs = set()



  @property
  def adapter(self):
    """The adapter used by this connection."""
    return self.__adapter

  @property
  def config(self):
    """The default configuration used by this connection."""
    return self.__config



  def _add_pending(self, rpc):
    """Add an RPC object to the list of pending RPCs.

    The argument must be a UserRPC object, not a MultiRpc object.
    """
    assert not isinstance(rpc, MultiRpc)
    self.__pending_rpcs.add(rpc)

  def _remove_pending(self, rpc):
    """Remove an RPC object from the list of pending RPCs.

    If the argument is a MultiRpc object, the wrapped RPCs are removed
    from the list of pending RPCs.
    """
    if isinstance(rpc, MultiRpc):


      for wrapped_rpc in rpc._MultiRpc__rpcs:
        self._remove_pending(wrapped_rpc)
    else:
      try:
        self.__pending_rpcs.remove(rpc)
      except KeyError:


        pass

  def is_pending(self, rpc):
    """Check whether an RPC object is currently pending.

    Note that 'pending' in this context refers to an RPC associated
    with this connection for which _remove_pending() hasn't been
    called yet; normally this is called by check_rpc_success() which
    itself is called by the various result hooks.  A pending RPC may
    be in the RUNNING or FINISHING state.

    If the argument is a MultiRpc object, this returns true if at least
    one of its wrapped RPCs is pending.
    """
    if isinstance(rpc, MultiRpc):
      for wrapped_rpc in rpc._MultiRpc__rpcs:
        if self.is_pending(wrapped_rpc):
          return True
      return False
    else:
      return rpc in self.__pending_rpcs

  def get_pending_rpcs(self):
    """Return (a copy of) the list of currently pending RPCs."""
    return set(self.__pending_rpcs)

  def get_datastore_type(self, app=None):
    """Tries to get the datastore type for the given app.

    This function is only guaranteed to return something other than
    UNKNOWN_DATASTORE when running in production and querying the current app.
    """
    return _GetDatastoreType(app)

  def wait_for_all_pending_rpcs(self):
    """Wait for all currently pending RPCs to complete."""
    while self.__pending_rpcs:
      try:
        rpc = apiproxy_stub_map.UserRPC.wait_any(self.__pending_rpcs)
      except Exception:




        logging.info('wait_for_all_pending_rpcs(): exception in wait_any()',
                     exc_info=True)
        continue
      if rpc is None:
        logging.debug('wait_any() returned None')
        continue
      assert rpc.state == apiproxy_rpc.RPC.FINISHING
      if rpc in self.__pending_rpcs:






        try:
          self.check_rpc_success(rpc)
        except Exception:

          logging.info('wait_for_all_pending_rpcs(): '
                       'exception in check_rpc_success()',
                       exc_info=True)




  def _create_rpc(self, config=None, service_name=None):
    """Create an RPC object using the configuration parameters.

    Internal only.

    Args:
      config: Optional Configuration object.
      service_name: Optional datastore service name.

    Returns:
      A new UserRPC object with the designated settings.

    NOTES:

    (1) The RPC object returned can only be used to make a single call
        (for details see apiproxy_stub_map.UserRPC).

    (2) To make a call, use one of the specific methods on the
        Connection object, such as conn.put(entities).  This sends the
        call to the server but does not wait.  To wait for the call to
        finish and get the result, call rpc.get_result().
    """
    deadline = Configuration.deadline(config, self.__config)
    on_completion = Configuration.on_completion(config, self.__config)
    callback = None
    if service_name is None:





      service_name = self._api_version
    if on_completion is not None:


      def callback():
        return on_completion(rpc)
    rpc = apiproxy_stub_map.UserRPC(service_name, deadline, callback)
    return rpc


  create_rpc = _create_rpc

  def _set_request_read_policy(self, request, config=None):
    """Set the read policy on a request.

    This takes the read policy from the config argument or the
    configuration's default configuration, and sets the request's read
    options.

    Args:
      request: A read request protobuf.
      config: Optional Configuration object.

    Returns:
      True if the read policy specifies a read current request, False if it
        specifies an eventually consistent request, None if it does
        not specify a read consistency.
    """

    if isinstance(config, apiproxy_stub_map.UserRPC):
      read_policy = getattr(config, 'read_policy', None)
    else:
      read_policy = Configuration.read_policy(config)


    if read_policy is None:
      read_policy = self.__config.read_policy

    if hasattr(request, 'set_failover_ms') and hasattr(request, 'strong'):

      if read_policy == Configuration.APPLY_ALL_JOBS_CONSISTENCY:
        request.set_strong(True)
        return True
      elif read_policy == Configuration.EVENTUAL_CONSISTENCY:
        request.set_strong(False)



        request.set_failover_ms(-1)
        return False
      else:
        return None
    elif hasattr(request, 'read_options'):



      if read_policy == Configuration.EVENTUAL_CONSISTENCY:
        request.read_options.read_consistency = (
            googledatastore.ReadOptions.EVENTUAL)
        return False
      else:
        return None
    else:
      raise datastore_errors.BadRequestError(
          'read_policy is only supported on read operations.')

  def _set_request_transaction(self, request):
    """Set the current transaction on a request.

    NOTE: This version of the method does nothing.  The version
    overridden by TransactionalConnection is the real thing.

    Args:
      request: A protobuf with a transaction field.

    Returns:
      An object representing a transaction or None.
    """
    return None

  def _make_rpc_call(self, config, method, request, response,
                     get_result_hook=None, user_data=None,
                     service_name=None):
    """Make an RPC call.

    Internal only.

    Except for the added config argument, this is a thin wrapper
    around UserRPC.make_call().

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      method: The method name.
      request: The request protocol buffer.
      response: The response protocol buffer.
      get_result_hook: Optional get-result hook function.  If not None,
        this must be a function with exactly one argument, the RPC
        object (self).  Its return value is returned from get_result().
      user_data: Optional additional arbitrary data for the get-result
        hook function.  This can be accessed as rpc.user_data.  The
        type of this value is up to the service module.

    Returns:
      The UserRPC object used for the call.
    """


    if isinstance(config, apiproxy_stub_map.UserRPC):
      rpc = config
    else:
      rpc = self._create_rpc(config, service_name)
    rpc.make_call(method, request, response, get_result_hook, user_data)
    self._add_pending(rpc)
    return rpc


  make_rpc_call = _make_rpc_call

  def check_rpc_success(self, rpc):
    """Check for RPC success and translate exceptions.

    This wraps rpc.check_success() and should be called instead of that.

    This also removes the RPC from the list of pending RPCs, once it
    has completed.

    Args:
      rpc: A UserRPC or MultiRpc object.

    Raises:
      Nothing if the call succeeded; various datastore_errors.Error
      subclasses if ApplicationError was raised by rpc.check_success().
    """
    try:
      rpc.wait()
    finally:


      self._remove_pending(rpc)
    try:
      rpc.check_success()
    except apiproxy_errors.ApplicationError, err:
      raise _ToDatastoreError(err)





  MAX_RPC_BYTES = 1024 * 1024
  MAX_GET_KEYS = 1000
  MAX_PUT_ENTITIES = 500
  MAX_DELETE_KEYS = 500
  MAX_ALLOCATE_IDS_KEYS = 500


  DEFAULT_MAX_ENTITY_GROUPS_PER_RPC = 10




  def __get_max_entity_groups_per_rpc(self, config):
    """Internal helper: figures out max_entity_groups_per_rpc for the config."""
    return Configuration.max_entity_groups_per_rpc(
        config, self.__config) or self.DEFAULT_MAX_ENTITY_GROUPS_PER_RPC

  def _extract_entity_group(self, value):
    """Internal helper: extracts the entity group from a key or entity.

    Supports both v3 and v1 protobufs.

    Args:
      value: an entity_pb.{Reference, EntityProto} or
          googledatastore.{Key, Entity}.

    Returns:
      A tuple consisting of:
        - kind
        - name, id, or ('new', unique id)
    """
    if _CLOUD_DATASTORE_ENABLED and isinstance(value, googledatastore.Entity):
      value = value.key
    if isinstance(value, entity_pb.EntityProto):
      value = value.key()
    if _CLOUD_DATASTORE_ENABLED and isinstance(value, googledatastore.Key):
      elem = value.path[0]
      elem_id = elem.id
      elem_name = elem.name
      kind = elem.kind
    else:
      elem = value.path().element(0)
      kind = elem.type()
      elem_id = elem.id()
      elem_name = elem.name()


    return (kind, elem_id or elem_name or ('new', id(elem)))

  def _map_and_group(self, values, map_fn, group_fn):
    """Internal helper: map values to keys and group by key. Here key is any
    object derived from an input value by map_fn, and which can be grouped
    by group_fn.

    Args:
      values: The values to be grouped by applying get_group(to_ref(value)).
      map_fn: a function that maps a value to a key to be grouped.
      group_fn: a function that groups the keys output by map_fn.

    Returns:
      A list where each element is a list of (key, index) pairs.  Here
      index is the location of the value from which the key was derived in
      the original list.
    """
    indexed_key_groups = collections.defaultdict(list)
    for index, value in enumerate(values):
      key = map_fn(value)
      indexed_key_groups[group_fn(key)].append((key, index))
    return indexed_key_groups.values()

  def __create_result_index_pairs(self, indexes):
    """Internal helper: build a function that ties an index with each result.

    Args:
      indexes: A list of integers.  A value x at location y in the list means
        that the result at location y in the result list needs to be at location
        x in the list of results returned to the user.
    """
    def create_result_index_pairs(results):
      return zip(results, indexes)
    return create_result_index_pairs

  def __sort_result_index_pairs(self, extra_hook):
    """Builds a function that sorts the indexed results.

    Args:
      extra_hook: A function that the returned function will apply to its result
        before returning.

    Returns:
      A function that takes a list of results and reorders them to match the
      order in which the input values associated with each results were
      originally provided.
    """

    def sort_result_index_pairs(result_index_pairs):
      results = [None] * len(result_index_pairs)
      for result, index in result_index_pairs:
        results[index] = result
      if extra_hook is not None:
        results = extra_hook(results)
      return results
    return sort_result_index_pairs

  def _generate_pb_lists(self, grouped_values, base_size, max_count,
                         max_groups, config):
    """Internal helper: repeatedly yield a list of 2 elements.

    Args:
      grouped_values: A list of lists.  The inner lists consist of objects
        grouped by e.g. entity group or id sequence.

      base_size: An integer representing the base size of an rpc.  Used for
        splitting operations across multiple RPCs due to size limitations.

      max_count: An integer representing the maximum number of objects we can
        send in an rpc.  Used for splitting operations across multiple RPCs.

      max_groups: An integer representing the maximum number of groups we can
        have represented in an rpc.  Can be None, in which case no constraint.

      config: The config object, defining max rpc size in bytes.

    Yields:
      Repeatedly yields 2 element tuples.  The first element is a list of
      protobufs to send in one batch.  The second element is a list containing
      the original location of those protobufs (expressed as an index) in the
      input.
    """
    max_size = (Configuration.max_rpc_bytes(config, self.__config) or
                self.MAX_RPC_BYTES)
    pbs = []
    pb_indexes = []
    size = base_size
    num_groups = 0
    for indexed_pbs in grouped_values:
      num_groups += 1
      if max_groups is not None and num_groups > max_groups:
        yield (pbs, pb_indexes)
        pbs = []
        pb_indexes = []
        size = base_size
        num_groups = 1
      for indexed_pb in indexed_pbs:
        (pb, index) = indexed_pb





        incr_size = pb.ByteSize() + 5




        if (not isinstance(config, apiproxy_stub_map.UserRPC) and
            (len(pbs) >= max_count or (pbs and size + incr_size > max_size))):
          yield (pbs, pb_indexes)
          pbs = []
          pb_indexes = []
          size = base_size
          num_groups = 1
        pbs.append(pb)
        pb_indexes.append(index)
        size += incr_size
    yield (pbs, pb_indexes)

  def __force(self, req):
    """Configure a request to force mutations."""
    if isinstance(req, (datastore_pb.PutRequest,
                        datastore_pb.TouchRequest,
                        datastore_pb.DeleteRequest)):
      req.set_force(True)

  def get(self, keys):
    """Synchronous Get operation.

    Args:
      keys: An iterable of user-level key objects.

    Returns:
      A list of user-level entity objects and None values, corresponding
      1:1 to the argument keys.  A None means there is no entity for the
      corresponding key.
    """
    return self.async_get(None, keys).get_result()

  def async_get(self, config, keys, extra_hook=None):
    """Asynchronous Get operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      keys: An iterable of user-level key objects.
      extra_hook: Optional function to be called on the result once the
        RPC has completed.

    Returns:
      A MultiRpc object.
    """

    def make_get_call(base_req, pbs, extra_hook=None):
      req = copy.deepcopy(base_req)
      if self._api_version == _CLOUD_DATASTORE_V1:
        method = 'Lookup'
        req.keys.extend(pbs)
        resp = googledatastore.LookupResponse()
      else:
        method = 'Get'
        req.key_list().extend(pbs)
        resp = datastore_pb.GetResponse()







      user_data = config, pbs, extra_hook
      return self._make_rpc_call(config, method, req, resp,
                                 get_result_hook=self.__get_hook,
                                 user_data=user_data,
                                 service_name=self._api_version)

    if self._api_version == _CLOUD_DATASTORE_V1:
      base_req = googledatastore.LookupRequest()
      key_to_pb = self.__adapter.key_to_pb_v1
    else:
      base_req = datastore_pb.GetRequest()
      base_req.set_allow_deferred(True)
      key_to_pb = self.__adapter.key_to_pb
    is_read_current = self._set_request_read_policy(base_req, config)
    txn = self._set_request_transaction(base_req)


    if isinstance(config, apiproxy_stub_map.UserRPC) or len(keys) <= 1:
      pbs = [key_to_pb(key) for key in keys]
      return make_get_call(base_req, pbs, extra_hook)

    max_count = (Configuration.max_get_keys(config, self.__config) or
                 self.MAX_GET_KEYS)

    indexed_keys_by_entity_group = self._map_and_group(
        keys, key_to_pb, self._extract_entity_group)

    if is_read_current is None:
      is_read_current = (self.get_datastore_type() ==
                         BaseConnection.HIGH_REPLICATION_DATASTORE)




    if is_read_current and txn is None:
      max_egs_per_rpc = self.__get_max_entity_groups_per_rpc(config)
    else:
      max_egs_per_rpc = None



    pbsgen = self._generate_pb_lists(indexed_keys_by_entity_group,
                                     base_req.ByteSize(), max_count,
                                     max_egs_per_rpc, config)

    rpcs = []
    for pbs, indexes in pbsgen:
      rpcs.append(make_get_call(base_req, pbs,
                                self.__create_result_index_pairs(indexes)))
    return MultiRpc(rpcs, self.__sort_result_index_pairs(extra_hook))

  def __get_hook(self, rpc):
    """Internal method used as get_result_hook for Get operation."""
    self.check_rpc_success(rpc)



    config, keys_from_request, extra_hook = rpc.user_data

    if self._api_version == _DATASTORE_V3 and rpc.response.in_order():


      entities = []
      for entity_result in rpc.response.entity_list():
        if entity_result.has_entity():
          entity = self.__adapter.pb_to_entity(entity_result.entity())
        else:
          entity = None
        entities.append(entity)
    else:

      current_get_response = rpc.response
      result_dict = {}
      self.__add_get_response_entities_to_dict(current_get_response,
                                               result_dict)



      deferred_req = copy.deepcopy(rpc.request)
      if self._api_version == _CLOUD_DATASTORE_V1:
        method = 'Lookup'
        deferred_resp = googledatastore.LookupResponse()
        while current_get_response.deferred:
          deferred_req.ClearField('keys')
          deferred_req.keys.extend(current_get_response.deferred)
          deferred_resp.Clear()
          deferred_rpc = self._make_rpc_call(config, method,
                                             deferred_req, deferred_resp,
                                             service_name=self._api_version)
          deferred_rpc.get_result()
          current_get_response = deferred_rpc.response


          self.__add_get_response_entities_to_dict(current_get_response,
                                                   result_dict)
      else:
        method = 'Get'
        deferred_resp = datastore_pb.GetResponse()
        while current_get_response.deferred_list():
          deferred_req.clear_key()
          deferred_req.key_list().extend(current_get_response.deferred_list())
          deferred_resp.Clear()
          deferred_rpc = self._make_rpc_call(config, method,
                                             deferred_req, deferred_resp,
                                             service_name=self._api_version)
          deferred_rpc.get_result()
          current_get_response = deferred_rpc.response


          self.__add_get_response_entities_to_dict(current_get_response,
                                                   result_dict)



      entities = [result_dict.get(datastore_types.ReferenceToKeyValue(pb))
                  for pb in keys_from_request]



    if extra_hook is not None:
      entities = extra_hook(entities)

    return entities

  def __add_get_response_entities_to_dict(self, get_response, result_dict):
    """Converts entities from the get response and adds them to the dict.

    The Key for the dict will be calculated via
    datastore_types.ReferenceToKeyValue.  There will be no entry for entities
    that were not found.

    Args:
      get_response: A datastore_pb.GetResponse or
          googledatastore.LookupResponse.
      result_dict: The dict to add results to.
    """
    if (_CLOUD_DATASTORE_ENABLED
        and isinstance(get_response, googledatastore.LookupResponse)):
      for result in get_response.found:
        v1_key = result.entity.key
        entity = self.__adapter.pb_v1_to_entity(result.entity, False)
        result_dict[datastore_types.ReferenceToKeyValue(v1_key)] = entity
    else:
      for entity_result in get_response.entity_list():

        if entity_result.has_entity():




          reference_pb = entity_result.entity().key()
          hashable_key = datastore_types.ReferenceToKeyValue(reference_pb)
          entity = self.__adapter.pb_to_entity(entity_result.entity())
          result_dict[hashable_key] = entity

  def get_indexes(self):
    """Synchronous get indexes operation.

    Returns:
      user-level indexes representation
    """
    return self.async_get_indexes(None).get_result()

  def async_get_indexes(self, config, extra_hook=None, _app=None):
    """Asynchronous get indexes operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      extra_hook: Optional function to be called once the RPC has completed.

    Returns:
      A MultiRpc object.
    """
    req = datastore_pb.GetIndicesRequest()
    req.set_app_id(datastore_types.ResolveAppId(_app))
    resp = datastore_pb.CompositeIndices()
    return self._make_rpc_call(config, 'GetIndices', req, resp,
                               get_result_hook=self.__get_indexes_hook,
                               user_data=extra_hook,
                               service_name=_DATASTORE_V3)

  def __get_indexes_hook(self, rpc):
    """Internal method used as get_result_hook for Get operation."""
    self.check_rpc_success(rpc)
    indexes = [self.__adapter.pb_to_index(index)
               for index in rpc.response.index_list()]
    if rpc.user_data:
      indexes = rpc.user_data(indexes)
    return indexes

  def put(self, entities):
    """Synchronous Put operation.

    Args:
      entities: An iterable of user-level entity objects.

    Returns:
      A list of user-level key objects, corresponding 1:1 to the
      argument entities.

    NOTE: If any of the entities has an incomplete key, this will
    *not* patch up those entities with the complete key.
    """
    return self.async_put(None, entities).get_result()

  def async_put(self, config, entities, extra_hook=None):
    """Asynchronous Put operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      entities: An iterable of user-level entity objects.
      extra_hook: Optional function to be called on the result once the
        RPC has completed.

     Returns:
      A MultiRpc object.

    NOTE: If any of the entities has an incomplete key, this will
    *not* patch up those entities with the complete key.
    """

    def make_put_call(base_req, pbs, user_data=None):
      req = copy.deepcopy(base_req)
      if self._api_version == _CLOUD_DATASTORE_V1:
        for entity in pbs:
          mutation = req.mutations.add()
          mutation.upsert.CopyFrom(entity)
        method = 'Commit'
        resp = googledatastore.CommitResponse()
      else:
        req.entity_list().extend(pbs)
        method = 'Put'
        resp = datastore_pb.PutResponse()
      user_data = pbs, user_data
      return self._make_rpc_call(config, method, req, resp,
                                 get_result_hook=self.__put_hook,
                                 user_data=user_data,
                                 service_name=self._api_version)


    if self._api_version == _CLOUD_DATASTORE_V1:
      base_req = googledatastore.CommitRequest()
      base_req.mode = googledatastore.CommitRequest.NON_TRANSACTIONAL
      entity_to_pb = self.__adapter.entity_to_pb_v1
    else:
      base_req = datastore_pb.PutRequest()
      entity_to_pb = self.__adapter.entity_to_pb
    self._set_request_transaction(base_req)
    if Configuration.force_writes(config, self.__config):
      self.__force(base_req)


    if isinstance(config, apiproxy_stub_map.UserRPC) or len(entities) <= 1:
      pbs = [entity_to_pb(entity) for entity in entities]
      return make_put_call(base_req, pbs, extra_hook)

    max_count = (Configuration.max_put_entities(config, self.__config) or
                 self.MAX_PUT_ENTITIES)
    if ((self._api_version == _CLOUD_DATASTORE_V1 and
         not base_req.transaction) or
        not base_req.has_transaction()):
      max_egs_per_rpc = self.__get_max_entity_groups_per_rpc(config)
    else:
      max_egs_per_rpc = None

    indexed_entities_by_entity_group = self._map_and_group(
        entities, entity_to_pb, self._extract_entity_group)



    pbsgen = self._generate_pb_lists(indexed_entities_by_entity_group,
                                     base_req.ByteSize(), max_count,
                                     max_egs_per_rpc, config)

    rpcs = []
    for pbs, indexes in pbsgen:
      rpcs.append(make_put_call(base_req, pbs,
                                self.__create_result_index_pairs(indexes)))
    return MultiRpc(rpcs, self.__sort_result_index_pairs(extra_hook))

  def __put_hook(self, rpc):
    """Internal method used as get_result_hook for Put operation."""
    self.check_rpc_success(rpc)
    entities_from_request, extra_hook = rpc.user_data

    if (_CLOUD_DATASTORE_ENABLED
        and isinstance(rpc.response, googledatastore.CommitResponse)):
      keys = []
      i = 0
      for entity in entities_from_request:
        if datastore_pbs.is_complete_v1_key(entity.key):
          keys.append(entity.key)
        else:
          keys.append(rpc.response.mutation_results[i].key)
          i += 1
      keys = [self.__adapter.pb_v1_to_key(key) for key in keys]
    else:
      keys = [self.__adapter.pb_to_key(key) for key in rpc.response.key_list()]



    if extra_hook is not None:
      keys = extra_hook(keys)
    return keys

  def delete(self, keys):
    """Synchronous Delete operation.

    Args:
      keys: An iterable of user-level key objects.

    Returns:
      None.
    """
    return self.async_delete(None, keys).get_result()

  def async_delete(self, config, keys, extra_hook=None):
    """Asynchronous Delete operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      keys: An iterable of user-level key objects.
      extra_hook: Optional function to be called once the RPC has completed.

    Returns:
      A MultiRpc object.
    """

    def make_delete_call(base_req, pbs, user_data=None):
      req = copy.deepcopy(base_req)
      if self._api_version == _CLOUD_DATASTORE_V1:
        for pb in pbs:
          mutation = req.mutations.add()
          mutation.delete.CopyFrom(pb)
        method = 'Commit'
        resp = googledatastore.CommitResponse()
      else:
        req.key_list().extend(pbs)
        method = 'Delete'
        resp = datastore_pb.DeleteResponse()
      return self._make_rpc_call(config, method, req, resp,
                                 get_result_hook=self.__delete_hook,
                                 user_data=user_data,
                                 service_name=self._api_version)


    if self._api_version == _CLOUD_DATASTORE_V1:
      base_req = googledatastore.CommitRequest()
      base_req.mode = googledatastore.CommitRequest.NON_TRANSACTIONAL
      key_to_pb = self.__adapter.key_to_pb_v1
    else:
      base_req = datastore_pb.DeleteRequest()
      key_to_pb = self.__adapter.key_to_pb
    self._set_request_transaction(base_req)
    if Configuration.force_writes(config, self.__config):
      self.__force(base_req)


    if isinstance(config, apiproxy_stub_map.UserRPC) or len(keys) <= 1:
      pbs = [key_to_pb(key) for key in keys]
      return make_delete_call(base_req, pbs, extra_hook)

    max_count = (Configuration.max_delete_keys(config, self.__config) or
                 self.MAX_DELETE_KEYS)
    if ((self._api_version == _CLOUD_DATASTORE_V1 and
         not base_req.transaction) or
        not base_req.has_transaction()):
      max_egs_per_rpc = self.__get_max_entity_groups_per_rpc(config)
    else:
      max_egs_per_rpc = None

    indexed_keys_by_entity_group = self._map_and_group(
        keys, key_to_pb, self._extract_entity_group)



    pbsgen = self._generate_pb_lists(indexed_keys_by_entity_group,
                                     base_req.ByteSize(), max_count,
                                     max_egs_per_rpc, config)

    rpcs = []
    for pbs, _ in pbsgen:
      rpcs.append(make_delete_call(base_req, pbs))
    return MultiRpc(rpcs, extra_hook)

  def __delete_hook(self, rpc):
    """Internal method used as get_result_hook for Delete operation."""
    self.check_rpc_success(rpc)
    if rpc.user_data is not None:

      rpc.user_data(None)



  def begin_transaction(self, app):
    """Syncnronous BeginTransaction operation.

    NOTE: In most cases the new_transaction() method is preferred,
    since that returns a TransactionalConnection object which will
    begin the transaction lazily.

    Args:
      app: Application ID.

    Returns:
      An object representing a transaction or None.
    """
    return self.async_begin_transaction(None, app).get_result()

  def async_begin_transaction(self, config, app):
    """Asynchronous BeginTransaction operation.

    Args:
      config: A configuration object or None.  Defaults are taken from
        the connection's default configuration.
      app: Application ID.

    Returns:
      A MultiRpc object.
    """
    if not isinstance(app, basestring) or not app:
      raise datastore_errors.BadArgumentError(
          'begin_transaction requires an application id argument (%r)' % (app,))

    if self._api_version == _CLOUD_DATASTORE_V1:
      req = googledatastore.BeginTransactionRequest()
      resp = googledatastore.BeginTransactionResponse()
    else:
      req = datastore_pb.BeginTransactionRequest()
      req.set_app(app)
      if (TransactionOptions.xg(config, self.__config)):
        req.set_allow_multiple_eg(True)
      resp = datastore_pb.Transaction()

    return self._make_rpc_call(config, 'BeginTransaction', req, resp,
                               get_result_hook=self.__begin_transaction_hook,
                               service_name=self._api_version)

  def __begin_transaction_hook(self, rpc):
    """Internal method used as get_result_hook for BeginTransaction."""
    self.check_rpc_success(rpc)
    if self._api_version == _CLOUD_DATASTORE_V1:
      return rpc.response.transaction
    else:
      return rpc.response


class Connection(BaseConnection):
  """Transaction-less connection class.

  This contains those operations that are not allowed on transactional
  connections.  (Currently only allocate_ids and reserve_key_ids.)
  """

  @_positional(1)
  def __init__(self, adapter=None, config=None, _api_version=_DATASTORE_V3):
    """Constructor.

    All arguments should be specified as keyword arguments.

    Args:
      adapter: Optional AbstractAdapter subclass instance;
        default IdentityAdapter.
      config: Optional Configuration object.
    """
    super(Connection, self).__init__(adapter=adapter, config=config,
                                     _api_version=_api_version)
    self.__adapter = self.adapter
    self.__config = self.config



  def new_transaction(self, config=None):
    """Create a new transactional connection based on this one.

    This is different from, and usually preferred over, the
    begin_transaction() method; new_transaction() returns a new
    TransactionalConnection object.

    Args:
      config: A configuration object for the new connection, merged
        with this connection's config.
    """
    config = self.__config.merge(config)
    return TransactionalConnection(adapter=self.__adapter, config=config,
                                   _api_version=self._api_version)



  def allocate_ids(self, key, size=None, max=None):
    """Synchronous AllocateIds operation.

    Exactly one of size and max must be specified.

    Args:
      key: A user-level key object.
      size: Optional number of IDs to allocate.
      max: Optional maximum ID to allocate.

    Returns:
      A pair (start, end) giving the (inclusive) range of IDs allocation.
    """
    return self.async_allocate_ids(None, key, size, max).get_result()

  def async_allocate_ids(self, config, key, size=None, max=None,
                         extra_hook=None):
    """Asynchronous AllocateIds operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      key: A user-level key object.
      size: Optional number of IDs to allocate.
      max: Optional maximum ID to allocate.
      extra_hook: Optional function to be called on the result once the
        RPC has completed.

    Returns:
      A MultiRpc object.
    """
    if size is not None:
      if max is not None:
        raise datastore_errors.BadArgumentError(
          'Cannot allocate ids using both size and max')
      if not isinstance(size, (int, long)):
        raise datastore_errors.BadArgumentError('Invalid size (%r)' % (size,))
      if size > _MAX_ID_BATCH_SIZE:
        raise datastore_errors.BadArgumentError(
          'Cannot allocate more than %s ids at a time; received %s'
          % (_MAX_ID_BATCH_SIZE, size))
      if size <= 0:
        raise datastore_errors.BadArgumentError(
          'Cannot allocate less than 1 id; received %s' % size)
    if max is not None:
      if not isinstance(max, (int, long)):
        raise datastore_errors.BadArgumentError('Invalid max (%r)' % (max,))
      if max < 0:
        raise datastore_errors.BadArgumentError(
          'Cannot allocate a range with a max less than 0 id; received %s' %
          size)
    req = datastore_pb.AllocateIdsRequest()
    req.mutable_model_key().CopyFrom(self.__adapter.key_to_pb(key))
    if size is not None:
      req.set_size(size)
    if max is not None:
      req.set_max(max)
    resp = datastore_pb.AllocateIdsResponse()
    rpc = self._make_rpc_call(config, 'AllocateIds', req, resp,
                              get_result_hook=self.__allocate_ids_hook,
                              user_data=extra_hook,
                              service_name=_DATASTORE_V3)
    return rpc

  def __allocate_ids_hook(self, rpc):
    """Internal method used as get_result_hook for AllocateIds."""
    self.check_rpc_success(rpc)
    pair = rpc.response.start(), rpc.response.end()
    if rpc.user_data is not None:
      pair = rpc.user_data(pair)
    return pair



  def _reserve_keys(self, keys):
    """Synchronous AllocateIds operation to reserve the given keys.

    Sends one or more v4 AllocateIds rpcs with keys to reserve.
    Reserved keys must be complete and must have valid ids.

    Args:
      keys: Iterable of user-level keys.
    """
    self._async_reserve_keys(None, keys).get_result()

  def _async_reserve_keys(self, config, keys, extra_hook=None):
    """Asynchronous AllocateIds operation to reserve the given keys.

    Sends one or more v4 AllocateIds rpcs with keys to reserve.
    Reserved keys must be complete and must have valid ids.

    Args:
      config: A Configuration object or None to use Connection default.
      keys: Iterable of user-level keys.
      extra_hook: Optional function to be called on rpc result.

    Returns:
      None, or the result of user-supplied extra_hook.
    """
    def to_id_key(key):
      if key.path().element_size() == 1:
        return 'root_idkey'
      else:
        return self._extract_entity_group(key)

    keys_by_idkey = self._map_and_group(keys, self.__adapter.key_to_pb,
                                        to_id_key)
    max_count = (Configuration.max_allocate_ids_keys(config, self.__config) or
                 self.MAX_ALLOCATE_IDS_KEYS)

    rpcs = []
    pbsgen = self._generate_pb_lists(keys_by_idkey, 0, max_count, None, config)
    for pbs, _ in pbsgen:
      req = datastore_v4_pb.AllocateIdsRequest()
      for key in pbs:
        datastore_pbs.get_entity_converter().v3_to_v4_key(key,
                                                          req.add_reserve())
      resp = datastore_v4_pb.AllocateIdsResponse()
      rpcs.append(self._make_rpc_call(config, 'AllocateIds', req, resp,
                                      get_result_hook=self.__reserve_keys_hook,
                                      user_data=extra_hook,
                                      service_name=_DATASTORE_V4))
    return MultiRpc(rpcs)

  def __reserve_keys_hook(self, rpc):
    """Internal get_result_hook for _reserve_keys."""
    self.check_rpc_success(rpc)
    if rpc.user_data is not None:
      return rpc.user_data(rpc.response)


class TransactionOptions(Configuration):
  """An immutable class that contains options for a transaction."""

  NESTED = 1
  """Create a nested transaction under an existing one."""

  MANDATORY = 2
  """Always propagate an existing transaction, throw an exception if there is
  no existing transaction."""

  ALLOWED = 3
  """If there is an existing transaction propagate it."""

  INDEPENDENT = 4
  """Always use a new transaction, pausing any existing transactions."""

  _PROPAGATION = frozenset((NESTED, MANDATORY, ALLOWED, INDEPENDENT))

  @ConfigOption
  def propagation(value):
    """How existing transactions should be handled.

    One of NESTED, MANDATORY, ALLOWED, INDEPENDENT. The interpertation of
    these types is up to higher level run-in-transaction implementations.

    WARNING: Using anything other than NESTED for the propagation flag
    can have strange consequences.  When using ALLOWED or MANDATORY, if
    an exception is raised, the transaction is likely not safe to
    commit.  When using INDEPENDENT it is not generally safe to return
    values read to the caller (as they were not read in the caller's
    transaction).

    Raises: datastore_errors.BadArgumentError if value is not reconized.
    """
    if value not in TransactionOptions._PROPAGATION:
      raise datastore_errors.BadArgumentError('Unknown propagation value (%r)' %
                                              (value,))
    return value

  @ConfigOption
  def xg(value):
    """Whether to allow cross-group transactions.

    Raises: datastore_errors.BadArgumentError if value is not a bool.
    """
    if not isinstance(value, bool):
      raise datastore_errors.BadArgumentError(
          'xg argument should be bool (%r)' % (value,))
    return value

  @ConfigOption
  def retries(value):
    """How many retries to attempt on the transaction.

    The exact retry logic is implemented in higher level run-in-transaction
    implementations.

    Raises: datastore_errors.BadArgumentError if value is not an integer or
      is not greater than zero.
    """
    datastore_types.ValidateInteger(value,
                                    'retries',
                                    datastore_errors.BadArgumentError,
                                    zero_ok=True)
    return value

  @ConfigOption
  def app(value):
    """The application in which to perform the transaction.

    Raises: datastore_errors.BadArgumentError if value is not a string
      or is the empty string.
    """
    datastore_types.ValidateString(value,
                                   'app',
                                   datastore_errors.BadArgumentError)
    return value


class TransactionalConnection(BaseConnection):
  """A connection specific to one transaction.

  It is possible to pass the transaction and entity group to the
  constructor, but typically the transaction is lazily created by
  _get_transaction() when the first operation is started.
  """

  @_positional(1)
  def __init__(self,
               adapter=None, config=None, transaction=None, entity_group=None,
               _api_version=_DATASTORE_V3):
    """Constructor.

    All arguments should be specified as keyword arguments.

    Args:
      adapter: Optional AbstractAdapter subclass instance;
        default IdentityAdapter.
      config: Optional Configuration object.
      transaction: Optional datastore_db.Transaction object.
      entity_group: Deprecated, do not use.
    """
    super(TransactionalConnection, self).__init__(adapter=adapter,
                                                  config=config,
                                                  _api_version=_api_version)
    self.__adapter = self.adapter
    self.__config = self.config
    if transaction is None:
      app = TransactionOptions.app(self.config)
      app = datastore_types.ResolveAppId(TransactionOptions.app(self.config))
      self.__transaction_rpc = self.async_begin_transaction(None, app)
    else:
      if self._api_version == _CLOUD_DATASTORE_V1:
        txn_class = str
      else:
        txn_class = datastore_pb.Transaction
      if not isinstance(transaction, txn_class):
        raise datastore_errors.BadArgumentError(
            'Invalid transaction (%r)' % transaction)
      self.__transaction = transaction
      self.__transaction_rpc = None
    self.__finished = False


    self.__pending_v1_upserts = {}
    self.__pending_v1_deletes = {}

  @property
  def finished(self):
    return self.__finished

  @property
  def transaction(self):
    if self.__transaction_rpc is not None:
      self.__transaction = self.__transaction_rpc.get_result()
      self.__transaction_rpc = None
    return self.__transaction

  def _set_request_transaction(self, request):
    """Set the current transaction on a request.

    This calls _get_transaction() (see below).  The transaction object
    returned is both set as the transaction field on the request
    object and returned.

    Args:
      request: A protobuf with a transaction field.

    Returns:
      An object representing a transaction or None.

    Raises:
      ValueError: if called with a non-Cloud Datastore request when using
          Cloud Datastore.
    """
    if self.__finished:
      raise datastore_errors.BadRequestError(
          'Cannot start a new operation in a finished transaction.')
    transaction = self.transaction
    if self._api_version == _CLOUD_DATASTORE_V1:
      if isinstance(request, (googledatastore.CommitRequest,
                              googledatastore.RollbackRequest)):
        request.transaction = transaction
      elif isinstance(request, (googledatastore.LookupRequest,
                                googledatastore.RunQueryRequest)):
        request.read_options.transaction = transaction
      else:




        raise ValueError('Cannot use Cloud Datastore V1 transactions with %s.' %
                         type(request))
      request.read_options.transaction = transaction
    else:
      request.mutable_transaction().CopyFrom(transaction)
    return transaction

  def _end_transaction(self):
    """Finish the current transaction.

    This blocks waiting for all pending RPCs to complete, and then
    marks the connection as finished.  After that no more operations
    can be started using this connection.

    Returns:
      An object representing a transaction or None.

    Raises:
      datastore_errors.BadRequestError if the transaction is already
      finished.
    """
    if self.__finished:
      raise datastore_errors.BadRequestError(
          'The transaction is already finished.')


    self.wait_for_all_pending_rpcs()
    assert not self.get_pending_rpcs()
    transaction = self.transaction
    self.__finished = True
    self.__transaction = None
    return transaction



  def async_put(self, config, entities, extra_hook=None):
    """Transactional asynchronous Put operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      entities: An iterable of user-level entity objects.
      extra_hook: Optional function to be called on the result once the
        RPC has completed.

     Returns:
      A MultiRpc object.

    NOTE: If any of the entities has an incomplete key, this will
    *not* patch up those entities with the complete key.
    """
    if self._api_version != _CLOUD_DATASTORE_V1:

      return super(TransactionalConnection, self).async_put(
          config, entities, extra_hook)

    v1_entities = [self.adapter.entity_to_pb_v1(entity)
                   for entity in entities]


    v1_req = googledatastore.AllocateIdsRequest()
    for v1_entity in v1_entities:
      if not datastore_pbs.is_complete_v1_key(v1_entity.key):
        v1_req.keys.add().CopyFrom(v1_entity.key)

    user_data = v1_entities, extra_hook

    service_name = _CLOUD_DATASTORE_V1
    if not v1_req.keys:

      service_name = _NOOP_SERVICE
    return self._make_rpc_call(config, 'AllocateIds', v1_req,
                               googledatastore.AllocateIdsResponse(),
                               get_result_hook=self.__v1_put_allocate_ids_hook,
                               user_data=user_data,
                               service_name=service_name)

  def __v1_put_allocate_ids_hook(self, rpc):
    """Internal method used as get_result_hook for AllocateIds call."""
    self.check_rpc_success(rpc)
    v1_resp = rpc.response
    return self.__v1_build_put_result(list(v1_resp.keys),
                                      rpc.user_data)

  def __v1_build_put_result(self, v1_allocated_keys, user_data):
    """Internal method that builds the result of a put operation.

    Converts the results from a v1 AllocateIds operation to a list of user-level
    key objects.

    Args:
      v1_allocated_keys: a list of googledatastore.Keys that have been allocated
      user_data: a tuple consisting of:
        - a list of googledatastore.Entity objects
        - an optional extra_hook
    """
    v1_entities, extra_hook = user_data
    keys = []
    idx = 0
    for v1_entity in v1_entities:






      v1_entity = copy.deepcopy(v1_entity)
      if not datastore_pbs.is_complete_v1_key(v1_entity.key):
        v1_entity.key.CopyFrom(v1_allocated_keys[idx])
        idx += 1
      hashable_key = datastore_types.ReferenceToKeyValue(v1_entity.key)

      self.__pending_v1_deletes.pop(hashable_key, None)


      self.__pending_v1_upserts[hashable_key] = v1_entity
      keys.append(self.adapter.pb_v1_to_key(copy.deepcopy(v1_entity.key)))


    if extra_hook:
      keys = extra_hook(keys)
    return keys



  def async_delete(self, config, keys, extra_hook=None):
    """Transactional asynchronous Delete operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      keys: An iterable of user-level key objects.
      extra_hook: Optional function to be called once the RPC has completed.

    Returns:
      A MultiRpc object.
    """
    if self._api_version != _CLOUD_DATASTORE_V1:

      return super(TransactionalConnection, self).async_delete(config,
                                                               keys,
                                                               extra_hook)

    v1_keys = [self.__adapter.key_to_pb_v1(key) for key in keys]

    for key in v1_keys:
      hashable_key = datastore_types.ReferenceToKeyValue(key)

      self.__pending_v1_upserts.pop(hashable_key, None)


      self.__pending_v1_deletes[hashable_key] = key



    return self._make_rpc_call(config, 'Commit', None,
                               googledatastore.CommitResponse(),
                               get_result_hook=self.__v1_delete_hook,
                               user_data=extra_hook,
                               service_name=_NOOP_SERVICE)

  def __v1_delete_hook(self, rpc):
    extra_hook = rpc.user_data
    if extra_hook:
      extra_hook(None)



  def commit(self):
    """Synchronous Commit operation.

    Returns:
      True if the transaction was successfully committed.  False if
      the backend reported a concurrent transaction error.
    """


    rpc = self._create_rpc(service_name=self._api_version)
    rpc = self.async_commit(rpc)
    if rpc is None:
      return True
    return rpc.get_result()

  def async_commit(self, config):
    """Asynchronous Commit operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.

     Returns:
      A MultiRpc object.
    """
    transaction = self._end_transaction()
    if transaction is None:
      return None

    if self._api_version == _CLOUD_DATASTORE_V1:
      req = googledatastore.CommitRequest()
      req.transaction = transaction
      if Configuration.force_writes(config, self.__config):
        self.__force(req)


      for entity in self.__pending_v1_upserts.itervalues():
        mutation = req.mutations.add()
        mutation.upsert.CopyFrom(entity)
      for key in self.__pending_v1_deletes.itervalues():
        mutation = req.mutations.add()
        mutation.delete.CopyFrom(key)


      self.__pending_v1_upserts.clear()
      self.__pending_v1_deletes.clear()

      resp = googledatastore.CommitResponse()
    else:
      req = transaction
      resp = datastore_pb.CommitResponse()

    return self._make_rpc_call(config, 'Commit', req, resp,
                               get_result_hook=self.__commit_hook,
                               service_name=self._api_version)

  def __commit_hook(self, rpc):
    """Internal method used as get_result_hook for Commit."""
    try:
      rpc.check_success()
    except apiproxy_errors.ApplicationError, err:
      if err.application_error == datastore_pb.Error.CONCURRENT_TRANSACTION:
        return False
      else:
        raise _ToDatastoreError(err)
    else:
      return True



  def rollback(self):
    """Synchronous Rollback operation."""
    rpc = self.async_rollback(None)
    if rpc is None:
      return None
    return rpc.get_result()

  def async_rollback(self, config):
    """Asynchronous Rollback operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.

     Returns:
      A MultiRpc object.
    """
    transaction = self._end_transaction()
    if transaction is None:
      return None

    if self._api_version == _CLOUD_DATASTORE_V1:
      req = googledatastore.RollbackRequest()
      req.transaction = transaction
      resp = googledatastore.RollbackResponse()
    else:
      req = transaction
      resp = api_base_pb.VoidProto()

    return self._make_rpc_call(config, 'Rollback', req, resp,
                               get_result_hook=self.__rollback_hook,
                               service_name=self._api_version)

  def __rollback_hook(self, rpc):
    """Internal method used as get_result_hook for Rollback."""
    self.check_rpc_success(rpc)






def _ToDatastoreError(err):
  """Converts an apiproxy.ApplicationError to an error in datastore_errors.

  Args:
    err: An apiproxy.ApplicationError object.

  Returns:
    An instance of a subclass of datastore_errors.Error.
  """
  return _DatastoreExceptionFromErrorCodeAndDetail(err.application_error,
                                                   err.error_detail)


_DATASTORE_EXCEPTION_CLASSES = {
    datastore_pb.Error.BAD_REQUEST: datastore_errors.BadRequestError,
    datastore_pb.Error.CONCURRENT_TRANSACTION: datastore_errors.TransactionFailedError,
    datastore_pb.Error.INTERNAL_ERROR: datastore_errors.InternalError,
    datastore_pb.Error.NEED_INDEX: datastore_errors.NeedIndexError,
    datastore_pb.Error.TIMEOUT: datastore_errors.Timeout,
    datastore_pb.Error.BIGTABLE_ERROR: datastore_errors.Timeout,
    datastore_pb.Error.COMMITTED_BUT_STILL_APPLYING: datastore_errors.CommittedButStillApplying,
    datastore_pb.Error.CAPABILITY_DISABLED: apiproxy_errors.CapabilityDisabledError,
}

_CLOUD_DATASTORE_EXCEPTION_CLASSES = {}

if _CLOUD_DATASTORE_ENABLED:
  _CLOUD_DATASTORE_EXCEPTION_CLASSES = {
      googledatastore.code_pb2.INVALID_ARGUMENT: datastore_errors.BadRequestError,
      googledatastore.code_pb2.ABORTED: datastore_errors.TransactionFailedError,
      googledatastore.code_pb2.FAILED_PRECONDITION:

          datastore_errors.NeedIndexError,
      googledatastore.code_pb2.DEADLINE_EXCEEDED: datastore_errors.Timeout,
      googledatastore.code_pb2.PERMISSION_DENIED: datastore_errors.BadRequestError,
      googledatastore.code_pb2.UNAVAILABLE: apiproxy_errors.RPCFailedError,
      googledatastore.code_pb2.RESOURCE_EXHAUSTED: apiproxy_errors.OverQuotaError,
      googledatastore.code_pb2.INTERNAL:

          datastore_errors.InternalError,
  }


def _DatastoreExceptionFromErrorCodeAndDetail(error, detail):
  """Converts a datastore_pb.Error into a datastore_errors.Error.

  Args:
    error: A member of the datastore_pb.Error enumeration.
    detail: A string providing extra details about the error.

  Returns:
    An instance of a subclass of datastore_errors.Error.
  """
  exception_class = _DATASTORE_EXCEPTION_CLASSES.get(error,
                                                     datastore_errors.Error)

  if detail is None:
    return exception_class()
  else:
    return exception_class(detail)


def _DatastoreExceptionFromCanonicalErrorCodeAndDetail(error, detail):
  """Converts a canonical error code into a datastore_errors.Error.

  Args:
    error: A canonical error code from google.rpc.code.
    detail: A string providing extra details about the error.

  Returns:
    An instance of a subclass of datastore_errors.Error.
  """
  exception_class = _CLOUD_DATASTORE_EXCEPTION_CLASSES.get(
      error, datastore_errors.InternalError)

  if detail is None:
    return exception_class()
  else:
    return exception_class(detail)
