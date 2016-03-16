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




"""Utility functions shared between the file and sqlite datastore stubs.

This module is internal and should not be used by client applications.
"""


from __future__ import with_statement








try:
  import hashlib
  _MD5_FUNC = hashlib.md5
except ImportError:
  import md5
  _MD5_FUNC = md5.new

import atexit
import collections
import itertools
import logging
import os
import random
import struct
import threading
import time
import weakref

from google.appengine.api import api_base_pb
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore_admin
from google.appengine.api import datastore_errors
from google.appengine.api import datastore_types
from google.appengine.api import yaml_errors
from google.appengine.api.taskqueue import taskqueue_service_pb
from google.appengine.datastore import datastore_index
from google.appengine.datastore import datastore_pb
from google.appengine.datastore import datastore_pbs
from google.appengine.datastore import datastore_query
from google.appengine.datastore import datastore_stub_index
from google.appengine.datastore import datastore_v4_pb
from google.appengine.runtime import apiproxy_errors
from google.net.proto import ProtocolBuffer
from google.appengine.datastore import entity_pb

if datastore_pbs._CLOUD_DATASTORE_ENABLED:
  from google.appengine.datastore.datastore_pbs import googledatastore





_MAXIMUM_RESULTS = 300





_MAXIMUM_QUERY_RESULT_BYTES = 2000000





_MAX_QUERY_OFFSET = 1000



_PROPERTY_TYPE_NAMES = {
    0: 'NULL',
    entity_pb.PropertyValue.kint64Value: 'INT64',
    entity_pb.PropertyValue.kbooleanValue: 'BOOLEAN',
    entity_pb.PropertyValue.kstringValue: 'STRING',
    entity_pb.PropertyValue.kdoubleValue: 'DOUBLE',
    entity_pb.PropertyValue.kPointValueGroup: 'POINT',
    entity_pb.PropertyValue.kUserValueGroup: 'USER',
    entity_pb.PropertyValue.kReferenceValueGroup: 'REFERENCE'
}



_SCATTER_PROPORTION = 32768




_MAX_EG_PER_TXN = 25




_BLOB_MEANINGS = frozenset((entity_pb.Property.BLOB,
                            entity_pb.Property.ENTITY_PROTO,
                            entity_pb.Property.TEXT))







_RETRIES = 3



_INITIAL_RETRY_DELAY_MS = 100



_RETRY_DELAY_MULTIPLIER = 2



_MAX_RETRY_DELAY_MS = 120000



MINIMUM_VERSION = 1




SEQUENTIAL = 'sequential'
SCATTERED = 'scattered'





_MAX_SEQUENTIAL_BIT = 52




_MAX_SEQUENTIAL_COUNTER = (1 << _MAX_SEQUENTIAL_BIT) - 1



_MAX_SEQUENTIAL_ID = _MAX_SEQUENTIAL_COUNTER




_MAX_SCATTERED_COUNTER = (1 << (_MAX_SEQUENTIAL_BIT - 1)) - 1





_MAX_SCATTERED_ID = _MAX_SEQUENTIAL_ID + 1 + _MAX_SCATTERED_COUNTER



_SCATTER_SHIFT = 64 - _MAX_SEQUENTIAL_BIT + 1


def _GetScatterProperty(entity_proto):
  """Gets the scatter property for an object.

  For ease of implementation, this is not synchronized with the actual
  value on the App Engine server, but should work equally well.

  Note: This property may change, either here or in production. No client
  other than the mapper framework should rely on it directly.

  Returns:
    The PropertyValue of the scatter property or None if this entity should not
    have a scatter property.
  """
  hash_obj = _MD5_FUNC()
  for element in entity_proto.key().path().element_list():
    if element.has_name():
      hash_obj.update(element.name())
    elif element.has_id():
      hash_obj.update(str(element.id()))
  hash_bytes = hash_obj.digest()[0:2]
  (hash_int,) = struct.unpack('H', hash_bytes)

  if hash_int >= _SCATTER_PROPORTION:
    return None

  scatter_property = entity_pb.Property()
  scatter_property.set_name(datastore_types.SCATTER_SPECIAL_PROPERTY)
  scatter_property.set_meaning(entity_pb.Property.BYTESTRING)
  scatter_property.set_multiple(False)
  property_value = scatter_property.mutable_value()
  property_value.set_stringvalue(hash_bytes)
  return scatter_property





_SPECIAL_PROPERTY_MAP = {
    datastore_types.SCATTER_SPECIAL_PROPERTY: (False, True, _GetScatterProperty)
}


def GetInvisibleSpecialPropertyNames():
  """Gets the names of all non user-visible special properties."""
  invisible_names = []
  for name, value in _SPECIAL_PROPERTY_MAP.items():
    is_visible, _, _ = value
    if not is_visible:
      invisible_names.append(name)
  return invisible_names


def _PrepareSpecialProperties(entity_proto, is_load):
  """Computes special properties for loading or storing.
  Strips other special properties."""
  for i in xrange(entity_proto.property_size() - 1, -1, -1):
    if _SPECIAL_PROPERTY_MAP.has_key(entity_proto.property(i).name()):
      del entity_proto.property_list()[i]

  for is_visible, is_stored, property_func in _SPECIAL_PROPERTY_MAP.values():
    if is_load:
      should_process = is_visible
    else:
      should_process = is_stored

    if should_process:
      special_property = property_func(entity_proto)
      if special_property:
        entity_proto.property_list().append(special_property)




_METADATA_PROPERTY_NAME = '__metadata__'


def _FromStorageEntity(entity):
  """Converts a stored entity protobuf to an EntityRecord (with metadata).

  This function is only provided as convenience for storage implementations that
  wish to store metadata directly on EntityProto.

  Args:
    entity: An Entity protobuf.

  Returns:
    The EntityRecord including the EntityMetadata protobuf that was stored as a
    property on the Entity protobuf or an empty EntityMetadata if that Entity
    has no metadata property.
  """
  clone = entity_pb.EntityProto()
  clone.CopyFrom(entity)
  metadata = entity_pb.EntityMetadata()
  for i in xrange(clone.property_size() - 1, -1, -1):
    property = clone.property(i)
    if _METADATA_PROPERTY_NAME == property.name():
      del clone.property_list()[i]
      metadata = entity_pb.EntityMetadata(property.value().stringvalue())
  return EntityRecord(clone, metadata)


def _ToStorageEntity(record):
  """Store a metadata object as a pickled string property on an entity protobuf.

  This function is only provided as convenience for storage implementations that
  wish to store metadata directly on EntityProto.

  Args:
    record: An EntityRecord.

  Returns:
    A copy of the entity with an additional string property that contains the
    pickled metadata object. Returns None If the record is None.
  """
  if record:
    clone = entity_pb.EntityProto()
    clone.CopyFrom(record.entity)

    serialized_metadata = record.metadata.SerializeToString()
    metadata_property = clone.add_property()
    metadata_property.set_name(_METADATA_PROPERTY_NAME)
    metadata_property.set_meaning(entity_pb.Property.BLOB)
    metadata_property.set_multiple(False)
    metadata_property.mutable_value().set_stringvalue(serialized_metadata)

    return clone


def _GetGroupByKey(entity, property_names):
  """Computes a key value that uniquely identifies the 'group' of an entity.

  Args:
    entity: The entity_pb.EntityProto for which to create the group key.
    property_names: The names of the properties in the group by clause.

  Returns:
    A hashable value that uniquely identifies the entity's 'group'.
  """
  return frozenset((prop.name(), prop.value().SerializeToString())
                   for prop in entity.property_list()
                   if prop.name() in property_names)


def PrepareSpecialPropertiesForStore(entity_proto):
  """Computes special properties for storing.
  Strips other special properties."""
  _PrepareSpecialProperties(entity_proto, False)


def LoadEntity(entity, keys_only=False, property_names=None):
  """Prepares an entity to be returned to the user.

  Args:
    entity: a entity_pb.EntityProto or None
    keys_only: if a keys only result should be produced
    property_names: if not None or empty, cause a projected entity
        to be produced with the given properties.

  Returns:
    A user friendly copy of entity or None.
  """
  if entity:
    clone = entity_pb.EntityProto()
    if property_names:

      clone.mutable_key().CopyFrom(entity.key())
      clone.mutable_entity_group()
      seen = set()
      for prop in entity.property_list():
        if prop.name() in property_names:

          Check(prop.name() not in seen,
                'datastore dev stub produced bad result',
                datastore_pb.Error.INTERNAL_ERROR)
          seen.add(prop.name())
          new_prop = clone.add_property()
          new_prop.set_name(prop.name())
          new_prop.set_meaning(entity_pb.Property.INDEX_VALUE)
          new_prop.mutable_value().CopyFrom(prop.value())
          new_prop.set_multiple(False)
    elif keys_only:

      clone.mutable_key().CopyFrom(entity.key())
      clone.mutable_entity_group()
    else:

      clone.CopyFrom(entity)
    PrepareSpecialPropertiesForLoad(clone)
    return clone


def LoadRecord(record, keys_only=False, property_names=None):
  """Prepares a record to be returned to the user.

  Args:
    record: an EntityRecord or None
    keys_only: if a keys only result should be produced
    property_names: if not None or empty, cause a projected entity
        to be produced with the given properties.

  Returns:
    A user friendly copy of record or None.
  """
  if record:
    metadata = record.metadata
    if keys_only or property_names:
      metadata = entity_pb.EntityMetadata()
    return EntityRecord(LoadEntity(record.entity, keys_only, property_names),
                        metadata)


def StoreRecord(record):
  """Prepares a record for storing.

  Args:
    record: an EntityRecord to prepare

  Returns:
    A copy of the record that can be stored.
  """
  clone = entity_pb.EntityProto()
  clone.CopyFrom(record.entity)



  PrepareSpecialPropertiesForStore(clone)

  return EntityRecord(clone, record.metadata)


def PrepareSpecialPropertiesForLoad(entity_proto):
  """Computes special properties that are user-visible.
  Strips other special properties."""
  _PrepareSpecialProperties(entity_proto, True)


def Check(test, msg='', error_code=datastore_pb.Error.BAD_REQUEST):
  """Raises an apiproxy_errors.ApplicationError if the condition is false.

  Args:
    test: A condition to test.
    msg: A string to return with the error.
    error_code: One of datastore_pb.Error to use as an error code.

  Raises:
    apiproxy_errors.ApplicationError: If test is false.
  """
  if not test:
    raise apiproxy_errors.ApplicationError(error_code, msg)


def CheckValidUTF8(string, desc):
  """Check that the given string is valid UTF-8.

  Args:
    string: the string to validate.
    desc: a description of the string being validated.

  Raises:
    apiproxy_errors.ApplicationError: if the string is not valid UTF-8.
  """

  if isinstance(string, unicode):
    return True
  try:
    string.decode('utf-8')
  except UnicodeDecodeError:
    Check(False, '%s is not valid UTF-8.' % desc)


def CheckAppId(request_trusted, request_app_id, app_id):
  """Check that this is the stub for app_id.

  Args:
    request_trusted: If the request is trusted.
    request_app_id: The application ID of the app making the request.
    app_id: An application ID.

  Raises:
    apiproxy_errors.ApplicationError: if this is not the stub for app_id.
  """

  assert app_id
  CheckValidUTF8(app_id, 'app id')
  Check(request_trusted or app_id == request_app_id,
        'app "%s" cannot access app "%s"\'s data' % (request_app_id, app_id))


def CheckReference(request_trusted,
                   request_app_id,
                   key,
                   require_id_or_name=True):
  """Check this key.

  Args:
    request_trusted: If the request is trusted.
    request_app_id: The application ID of the app making the request.
    key: entity_pb.Reference
    require_id_or_name: Boolean indicating if we should enforce the presence of
      an id or name in the last element of the key's path.

  Raises:
    apiproxy_errors.ApplicationError: if the key is invalid
  """

  assert isinstance(key, entity_pb.Reference)

  CheckAppId(request_trusted, request_app_id, key.app())

  Check(key.path().element_size() > 0, 'key\'s path cannot be empty')

  if require_id_or_name and not datastore_pbs.is_complete_v3_key(key):
    raise datastore_errors.BadRequestError('missing key id/name')

  for elem in key.path().element_list():
    Check(not elem.has_id() or not elem.has_name(),
          'each key path element should have id or name but not both: %r' % key)
    CheckValidUTF8(elem.type(), 'key path element type')
    if elem.has_name():
      CheckValidUTF8(elem.name(), 'key path element name')


def CheckEntity(request_trusted, request_app_id, entity):
  """Check if this entity can be stored.

  Args:
    request_trusted: If the request is trusted.
    request_app_id: The application ID of the app making the request.
    entity: entity_pb.EntityProto

  Raises:
    apiproxy_errors.ApplicationError: if the entity is invalid
  """


  CheckReference(request_trusted, request_app_id, entity.key(), False)
  for prop in entity.property_list():
    CheckProperty(request_trusted, request_app_id, prop)
  for prop in entity.raw_property_list():
    CheckProperty(request_trusted, request_app_id, prop, indexed=False)


def CheckProperty(request_trusted, request_app_id, prop, indexed=True):
  """Check if this property can be stored.

  Args:
    request_trusted: If the request is trusted.
    request_app_id: The application ID of the app making the request.
    prop: entity_pb.Property
    indexed: Whether the property is indexed.

  Raises:
    apiproxy_errors.ApplicationError: if the property is invalid
  """
  name = prop.name()
  value = prop.value()
  meaning = prop.meaning()
  CheckValidUTF8(name, 'property name')
  Check(request_trusted or
        not datastore_types.RESERVED_PROPERTY_NAME.match(name),
        'cannot store entity with reserved property name \'%s\'' % name)
  Check(prop.meaning() != entity_pb.Property.INDEX_VALUE,
        'Entities with incomplete properties cannot be written.')
  is_blob = meaning in _BLOB_MEANINGS
  if indexed:
    Check(not is_blob,
          'BLOB, ENITY_PROTO or TEXT property ' + name +
          ' must be in a raw_property field')
    max_length = datastore_types._MAX_STRING_LENGTH
  else:
    if is_blob:
      Check(value.has_stringvalue(),
            'BLOB / ENTITY_PROTO / TEXT raw property ' + name +
            'must have a string value')
    max_length = datastore_types._MAX_RAW_PROPERTY_BYTES
  if meaning == entity_pb.Property.ATOM_LINK:
    max_length = datastore_types._MAX_LINK_PROPERTY_LENGTH

  CheckPropertyValue(name, value, max_length, meaning)


def CheckPropertyValue(name, value, max_length, meaning):
  """Check if this property value can be stored.

  Args:
    name: name of the property
    value: entity_pb.PropertyValue
    max_length: maximum length for string values
    meaning: meaning of the property

  Raises:
    apiproxy_errors.ApplicationError: if the property is invalid
  """
  num_values = (value.has_int64value() +
                value.has_stringvalue() +
                value.has_booleanvalue() +
                value.has_doublevalue() +
                value.has_pointvalue() +
                value.has_uservalue() +
                value.has_referencevalue())
  Check(num_values <= 1, 'PropertyValue for ' + name +
        ' has multiple value fields set')

  if value.has_stringvalue():
    s = value.stringvalue()
    if isinstance(s, unicode):
      s = s.encode('utf-8')
    Check(len(s) <= max_length,
          'Property %s is too long. Maximum length is %d.' % (name, max_length))
    if (meaning not in _BLOB_MEANINGS and
        meaning != entity_pb.Property.BYTESTRING):
      CheckValidUTF8(value.stringvalue(), 'String property value')


def CheckTransaction(request_trusted, request_app_id, transaction):
  """Check that this transaction is valid.

  Args:
    request_trusted: If the request is trusted.
    request_app_id: The application ID of the app making the request.
    transaction: datastore_pb.Transaction

  Raises:
    apiproxy_errors.ApplicationError: if the transaction is not valid.
  """
  assert isinstance(transaction, datastore_pb.Transaction)
  CheckAppId(request_trusted, request_app_id, transaction.app())


def CheckQuery(query, filters, orders, max_query_components):
  """Check a datastore query with normalized filters, orders.

  Raises an ApplicationError when any of the following conditions are violated:
  - transactional queries have an ancestor
  - queries that are not too large
    (sum of filters, orders, ancestor <= max_query_components)
  - ancestor (if any) app and namespace match query app and namespace
  - kindless queries only filter on __key__ and only sort on __key__ ascending
  - multiple inequality (<, <=, >, >=) filters all applied to the same property
  - filters on __key__ compare to a reference in the same app and namespace as
    the query
  - if an inequality filter on prop X is used, the first order (if any) must
    be on X

  Args:
    query: query to validate
    filters: normalized (by datastore_index.Normalize) filters from query
    orders: normalized (by datastore_index.Normalize) orders from query
    max_query_components: limit on query complexity
  """
  Check(query.property_name_size() == 0 or not query.keys_only(),
        'projection and keys_only cannot both be set')

  projected_properties = set(query.property_name_list())
  for prop_name in query.property_name_list():
    Check(not datastore_types.RESERVED_PROPERTY_NAME.match(prop_name),
          'projections are not supported for the property: ' + prop_name)
  Check(len(projected_properties) == len(query.property_name_list()),
        'cannot project a property multiple times')

  key_prop_name = datastore_types.KEY_SPECIAL_PROPERTY
  unapplied_log_timestamp_us_name = (
      datastore_types._UNAPPLIED_LOG_TIMESTAMP_SPECIAL_PROPERTY)

  if query.has_transaction():

    Check(query.has_ancestor(),
          'Only ancestor queries are allowed inside transactions.')


  num_components = len(filters) + len(orders)
  if query.has_ancestor():
    num_components += 1
  Check(num_components <= max_query_components,
        'query is too large. may not have more than %s filters'
        ' + sort orders ancestor total' % max_query_components)


  if query.has_ancestor():
    ancestor = query.ancestor()
    Check(query.app() == ancestor.app(),
          'query app is %s but ancestor app is %s' %
          (query.app(), ancestor.app()))
    Check(query.name_space() == ancestor.name_space(),
          'query namespace is %s but ancestor namespace is %s' %
          (query.name_space(), ancestor.name_space()))


  if query.group_by_property_name_size():
    group_by_set = set(query.group_by_property_name_list())
    for order in orders:
      if not group_by_set:
        break
      Check(order.property() in group_by_set,
            'items in the group by clause must be specified first '
            'in the ordering')
      group_by_set.remove(order.property())



  ineq_prop_name = None
  for filter in filters:
    Check(filter.property_size() == 1,
          'Filter has %d properties, expected 1' % filter.property_size())

    prop = filter.property(0)
    prop_name = prop.name().decode('utf-8')

    if prop_name == key_prop_name:



      Check(prop.value().has_referencevalue(),
            '%s filter value must be a Key' % key_prop_name)
      ref_val = prop.value().referencevalue()
      Check(ref_val.app() == query.app(),
            '%s filter app is %s but query app is %s' %
            (key_prop_name, ref_val.app(), query.app()))
      Check(ref_val.name_space() == query.name_space(),
            '%s filter namespace is %s but query namespace is %s' %
            (key_prop_name, ref_val.name_space(), query.name_space()))

    if filter.op() in datastore_index.EQUALITY_OPERATORS:
      Check(prop_name not in projected_properties,
            'cannot use projection on a property with an equality filter')
    if (filter.op() in datastore_index.INEQUALITY_OPERATORS and
        prop_name != unapplied_log_timestamp_us_name):
      if ineq_prop_name is None:
        ineq_prop_name = prop_name
      else:
        Check(ineq_prop_name == prop_name,
              'Only one inequality filter per query is supported. '
              'Encountered both %s and %s' % (ineq_prop_name, prop_name))

  if (ineq_prop_name is not None
      and query.group_by_property_name_size() > 0
      and not orders):

    Check(ineq_prop_name in group_by_set,
          'Inequality filter on %s must also be a group by '
          'property when group by properties are set.'
          % (ineq_prop_name))

  if ineq_prop_name is not None and orders:

    first_order_prop = orders[0].property().decode('utf-8')
    Check(first_order_prop == ineq_prop_name,
          'The first sort property must be the same as the property '
          'to which the inequality filter is applied.  In your query '
          'the first sort property is %s but the inequality filter '
          'is on %s' % (first_order_prop, ineq_prop_name))

  if not query.has_kind():

    for filter in filters:
      prop_name = filter.property(0).name().decode('utf-8')
      Check(prop_name == key_prop_name or
            prop_name == unapplied_log_timestamp_us_name,
            'kind is required for non-__key__ filters')
    for order in orders:
      prop_name = order.property().decode('utf-8')
      Check(prop_name == key_prop_name and
            order.direction() is datastore_pb.Query_Order.ASCENDING,
            'kind is required for all orders except __key__ ascending')


class ValueRange(object):
  """A range of values defined by its two extremes (inclusive or exclusive)."""

  def __init__(self):
    """Constructor.

    Creates an unlimited range.
    """
    self.__start = self.__end = None
    self.__start_inclusive = self.__end_inclusive = False

  def Update(self, rel_op, limit):
    """Filter the range by 'rel_op limit'.

    Args:
      rel_op: relational operator from datastore_pb.Query_Filter.
      limit: the value to limit the range by.
    """

    if rel_op == datastore_pb.Query_Filter.LESS_THAN:
      if self.__end is None or limit <= self.__end:
        self.__end = limit
        self.__end_inclusive = False
    elif (rel_op == datastore_pb.Query_Filter.LESS_THAN_OR_EQUAL or
          rel_op == datastore_pb.Query_Filter.EQUAL):
      if self.__end is None or limit < self.__end:
        self.__end = limit
        self.__end_inclusive = True

    if rel_op == datastore_pb.Query_Filter.GREATER_THAN:
      if self.__start is None or limit >= self.__start:
        self.__start = limit
        self.__start_inclusive = False
    elif (rel_op == datastore_pb.Query_Filter.GREATER_THAN_OR_EQUAL or
          rel_op == datastore_pb.Query_Filter.EQUAL):
      if self.__start is None or limit > self.__start:
        self.__start = limit
        self.__start_inclusive = True

  def Contains(self, value):
    """Check if the range contains a specific value.

    Args:
      value: the value to check.
    Returns:
      True iff value is contained in this range.
    """
    if self.__start is not None:
      if self.__start_inclusive and value < self.__start: return False
      if not self.__start_inclusive and value <= self.__start: return False
    if self.__end is not None:
      if self.__end_inclusive and value > self.__end: return False
      if not self.__end_inclusive and value >= self.__end: return False
    return True

  def Remap(self, mapper):
    """Transforms the range extremes with a function.

    The function mapper must preserve order, i.e.
      x rel_op y iff mapper(x) rel_op y

    Args:
      mapper: function to apply to the range extremes.
    """
    self.__start = self.__start and mapper(self.__start)
    self.__end = self.__end and mapper(self.__end)

  def MapExtremes(self, mapper):
    """Evaluate a function on the range extremes.

    Args:
      mapper: function to apply to the range extremes.
    Returns:
      (x, y) where x = None if the range has no start,
                       mapper(start, start_inclusive, False) otherwise
                   y = None if the range has no end,
                       mapper(end, end_inclusive, True) otherwise
    """
    return (
        self.__start and mapper(self.__start, self.__start_inclusive, False),
        self.__end and mapper(self.__end, self.__end_inclusive, True))


def ParseKeyFilteredQuery(filters, orders):
  """Parse queries which only allow filters and ascending-orders on __key__.

  Raises exceptions for illegal queries.
  Args:
    filters: the normalized filters of a query.
    orders: the normalized orders of a query.
  Returns:
     The key range (a ValueRange over datastore_types.Key) requested in the
     query.
  """

  remaining_filters = []
  key_range = ValueRange()
  key_prop = datastore_types.KEY_SPECIAL_PROPERTY
  for f in filters:
    op = f.op()
    if not (f.property_size() == 1 and
            f.property(0).name() == key_prop and
            not (op == datastore_pb.Query_Filter.IN or
                 op == datastore_pb.Query_Filter.EXISTS)):
      remaining_filters.append(f)
      continue

    val = f.property(0).value()
    Check(val.has_referencevalue(), '__key__ kind must be compared to a key')
    limit = datastore_types.FromReferenceProperty(val)
    key_range.Update(op, limit)


  remaining_orders = []
  for o in orders:
    if not (o.direction() == datastore_pb.Query_Order.ASCENDING and
            o.property() == datastore_types.KEY_SPECIAL_PROPERTY):
      remaining_orders.append(o)
    else:
      break



  Check(not remaining_filters,
        'Only comparison filters on ' + key_prop + ' supported')
  Check(not remaining_orders,
        'Only ascending order on ' + key_prop + ' supported')

  return key_range


def ParseKindQuery(query, filters, orders):
  """Parse __kind__ (schema) queries.

  Raises exceptions for illegal queries.
  Args:
    query: A Query PB.
    filters: the normalized filters from query.
    orders: the normalized orders from query.
  Returns:
     The kind range (a ValueRange over string) requested in the query.
  """

  Check(not query.has_ancestor(), 'ancestor queries on __kind__ not allowed')

  key_range = ParseKeyFilteredQuery(filters, orders)
  key_range.Remap(_KindKeyToString)

  return key_range


def _KindKeyToString(key):
  """Extract kind name from __kind__ key.

  Raises an ApplicationError if the key is not of the form '__kind__'/name.

  Args:
    key: a key for a __kind__ instance.
  Returns:
    kind specified by key.
  """
  key_path = key.to_path()
  if (len(key_path) == 2 and key_path[0] == '__kind__' and
      isinstance(key_path[1], basestring)):
    return key_path[1]
  Check(False, 'invalid Key for __kind__ table')


def ParseNamespaceQuery(query, filters, orders):
  """Parse __namespace__  queries.

  Raises exceptions for illegal queries.
  Args:
    query: A Query PB.
    filters: the normalized filters from query.
    orders: the normalized orders from query.
  Returns:
     The kind range (a ValueRange over string) requested in the query.
  """

  Check(not query.has_ancestor(),
        'ancestor queries on __namespace__ not allowed')

  key_range = ParseKeyFilteredQuery(filters, orders)
  key_range.Remap(_NamespaceKeyToString)

  return key_range


def _NamespaceKeyToString(key):
  """Extract namespace name from __namespace__ key.

  Raises an ApplicationError if the key is not of the form '__namespace__'/name
  or '__namespace__'/_EMPTY_NAMESPACE_ID.

  Args:
    key: a key for a __namespace__ instance.
  Returns:
    namespace specified by key.
  """
  key_path = key.to_path()
  if len(key_path) == 2 and key_path[0] == '__namespace__':
    if key_path[1] == datastore_types._EMPTY_NAMESPACE_ID:
      return ''
    if isinstance(key_path[1], basestring):
      return key_path[1]
  Check(False, 'invalid Key for __namespace__ table')


def ParsePropertyQuery(query, filters, orders):
  """Parse __property__  queries.

  Raises exceptions for illegal queries.
  Args:
    query: A Query PB.
    filters: the normalized filters from query.
    orders: the normalized orders from query.
  Returns:
     The kind range (a ValueRange over (kind, property) pairs) requested
     in the query.
  """

  Check(not query.has_transaction(),
        'transactional queries on __property__ not allowed')

  key_range = ParseKeyFilteredQuery(filters, orders)
  key_range.Remap(lambda x: _PropertyKeyToString(x, ''))

  if query.has_ancestor():
    ancestor = datastore_types.Key._FromPb(query.ancestor())
    ancestor_kind, ancestor_property = _PropertyKeyToString(ancestor, None)


    if ancestor_property is not None:
      key_range.Update(datastore_pb.Query_Filter.EQUAL,
                       (ancestor_kind, ancestor_property))
    else:

      key_range.Update(datastore_pb.Query_Filter.GREATER_THAN_OR_EQUAL,
                       (ancestor_kind, ''))
      key_range.Update(datastore_pb.Query_Filter.LESS_THAN_OR_EQUAL,
                       (ancestor_kind + '\0', ''))
    query.clear_ancestor()

  return key_range


def _PropertyKeyToString(key, default_property):
  """Extract property name from __property__ key.

  Raises an ApplicationError if the key is not of the form
  '__kind__'/kind, '__property__'/property or '__kind__'/kind

  Args:
    key: a key for a __property__ instance.
    default_property: property value to return when key only has a kind.
  Returns:
    kind, property if key = '__kind__'/kind, '__property__'/property
    kind, default_property if key = '__kind__'/kind
  """
  key_path = key.to_path()
  if (len(key_path) == 2 and
      key_path[0] == '__kind__' and isinstance(key_path[1], basestring)):
    return (key_path[1], default_property)
  if (len(key_path) == 4 and
      key_path[0] == '__kind__' and isinstance(key_path[1], basestring) and
      key_path[2] == '__property__' and isinstance(key_path[3], basestring)):
    return (key_path[1], key_path[3])

  Check(False, 'invalid Key for __property__ table')


def SynthesizeUserId(email):
  """Return a synthetic user ID from an email address.

  Note that this is not the same user ID found in the production system.

  Args:
    email: An email address.

  Returns:
    A string userid derived from the email address.
  """

  user_id_digest = _MD5_FUNC(email.lower()).digest()
  user_id = '1' + ''.join(['%02d' % ord(x) for x in user_id_digest])[:20]
  return user_id


def FillUsersInQuery(filters):
  """Fill in a synthetic user ID for all user properties in a set of filters.

  Args:
    filters: The normalized filters from query.
  """
  for filter in filters:
    for property in filter.property_list():
      FillUser(property)


def FillUser(property):
  """Fill in a synthetic user ID for a user properties.

  Args:
    property: A Property which may have a user value.
  """
  if property.value().has_uservalue():
    uid = SynthesizeUserId(property.value().uservalue().email())
    if uid:
      property.mutable_value().mutable_uservalue().set_obfuscated_gaiaid(uid)


class BaseCursor(object):
  """A base query cursor over a list of entities.

  Public properties:
    cursor: the integer cursor.
    app: the app for which this cursor was created.
    keys_only: whether the query is keys_only.

  Class attributes:
    _next_cursor: the next cursor to allocate.
    _next_cursor_lock: protects _next_cursor.
  """
  _next_cursor = 1
  _next_cursor_lock = threading.Lock()

  def __init__(self, query, dsquery, orders, index_list):
    """Constructor.

    Args:
      query: the query request proto.
      dsquery: a datastore_query.Query over query.
      orders: the orders of query as returned by _GuessOrders.
      index_list: the list of indexes used by the query.
    """

    self.keys_only = query.keys_only()
    self.property_names = set(query.property_name_list())
    self.group_by = set(query.group_by_property_name_list())
    self.app = query.app()
    self.cursor = self._AcquireCursorID()

    if query.has_count():
      count = query.count()
    elif query.has_limit():
      count = query.limit()
    else:
      count = BaseDatastore._BATCH_SIZE

    self.__use_persisted_offset = query.persist_offset()
    self.__persisted_offset = query.offset()
    self.__persisted_count = count

    self.__order_compare_entities = dsquery._order.cmp_for_filter(
        dsquery._filter_predicate)
    if self.group_by:
      self.__cursor_properties = self.group_by
    else:
      self.__cursor_properties = set(order.property() for order in orders)
      self.__cursor_properties.add('__key__')
      self.__cursor_properties = frozenset(self.__cursor_properties)

    self.__first_sort_order = orders[0].direction()
    self.__index_list = index_list

  def _PopulateResultMetadata(self, query_result, compile,
                              first_result, last_result):
    query_result.set_keys_only(self.keys_only)
    if query_result.more_results():
      cursor = query_result.mutable_cursor()
      cursor.set_app(self.app)
      cursor.set_cursor(self.cursor)
    if compile:
      self._EncodeCompiledCursor(last_result,
                                 query_result.mutable_compiled_cursor())
    if first_result:
      query_result.index_list().extend(self.__index_list)

  @classmethod
  def _AcquireCursorID(cls):
    """Acquires the next cursor id in a thread safe manner."""
    cls._next_cursor_lock.acquire()
    try:
      cursor_id = cls._next_cursor
      cls._next_cursor += 1
    finally:
      cls._next_cursor_lock.release()
    return cursor_id

  def _IsBeforeCursor(self, record, cursor):
    """True if entity is before cursor according to the current order.

    Args:
      record: an EntityRecord.
      cursor: a compiled cursor as returned by _DecodeCompiledCursor.
    """
    comparison_entity = entity_pb.EntityProto()
    for prop in record.entity.property_list():
      if prop.name() in self.__cursor_properties:
        comparison_entity.add_property().MergeFrom(prop)
    if cursor[0].has_key():
      comparison_entity.mutable_key().MergeFrom(record.entity.key())
    x = self.__order_compare_entities(comparison_entity, cursor[0])
    if cursor[1]:
      return x < 0
    else:
      return x <= 0

  def _DecodeCompiledCursor(self, compiled_cursor):
    """Converts a compiled_cursor into a cursor_entity.

    Args:
      compiled_cursor: The datastore_pb.CompiledCursor to decode.

    Returns:
      (cursor_entity, inclusive): an entity_pb.EntityProto and if it should
      be included in the result set.
    """
    assert compiled_cursor.has_postfix_position()

    position = compiled_cursor.postfix_position()




    remaining_properties = set(self.__cursor_properties)

    cursor_entity = entity_pb.EntityProto()
    if position.has_key():
      cursor_entity.mutable_key().CopyFrom(position.key())
      try:
        remaining_properties.remove('__key__')
      except KeyError:
        Check(False, 'Cursor does not match query: extra value __key__')
    for index_value in position.index_value_list():
      prop = cursor_entity.add_property()
      prop.set_name(index_value.property_name())
      prop.mutable_value().CopyFrom(index_value.value())
      try:
        remaining_properties.remove(index_value.property_name())
      except KeyError:
        Check(False, 'Cursor does not match query: extra value %s' %
              index_value.property_name())
    Check(not remaining_properties,
          'Cursor does not match query: missing values for %r' %
          remaining_properties)



    return (cursor_entity, position.before())

  def _EncodeCompiledCursor(self, last_result, compiled_cursor):
    """Converts the current state of the cursor into a compiled_cursor.

    Args:
      last_result: the last result returned by this query.
      compiled_cursor: an empty datstore_pb.CompiledCursor.
    """
    if last_result is not None:


      position = compiled_cursor.mutable_postfix_position()


      if '__key__' in self.__cursor_properties:
        position.mutable_key().MergeFrom(last_result.key())
      for prop in last_result.property_list():
        if prop.name() in self.__cursor_properties:
          index_value = position.add_index_value()
          index_value.set_property_name(prop.name())
          index_value.mutable_value().CopyFrom(prop.value())
      position.set_before(False)
      _SetBeforeAscending(position, self.__first_sort_order)

  def PopulateQueryResult(self, result, count, deprecated_offset,
                          compile=False, first_result=False):
    """Populates a QueryResult with this cursor and the given number of results.

    Args:
      result: datastore_pb.QueryResult
      count: integer of how many results to return, or None if not specified
      deprecated_offset: integer of how many results to skip, deprecated.
      compile: boolean, whether we are compiling this query
      first_result: whether the query result is the first for this query

    Raises:
      datastore_errors.BadArgumentError: if the offset doesn't match the
      original offset from the RunQuery call.
    """
    if count is None:
      count = self.__persisted_count
    if (deprecated_offset is not None
        and self.__persisted_offset != deprecated_offset):
      raise datastore_errors.BadArgumentError(
          'Invalid offset provided. Got %d expected %d.'
          % (deprecated_offset, self.__persisted_offset))
    self._PopulateQueryResult(result, count, self.__persisted_offset,
                              compile, first_result)
    self.__persisted_offset -= result.skipped_results()

  def _PopulateQueryResult(self, result, count, offset,
                           compile, first_result):
    raise NotImplementedError


class ListCursor(BaseCursor):
  """A query cursor over a list of entities.

  Public properties:
    keys_only: whether the query is keys_only
  """

  def __init__(self, query, dsquery, orders, index_list, results):
    """Constructor.

    Args:
      query: the query request proto
      dsquery: a datastore_query.Query over query.
      orders: the orders of query as returned by _GuessOrders.
      index_list: the list of indexes used by the query.
      results: list of EntityRecord.
    """
    super(ListCursor, self).__init__(query, dsquery, orders, index_list)


    if self.group_by:
      distincts = set()
      new_results = []
      for result in results:
        key_value = _GetGroupByKey(result.entity, self.group_by)
        if key_value not in distincts:
          distincts.add(key_value)
          new_results.append(result)
      results = new_results

    if (query.has_compiled_cursor()
        and query.compiled_cursor().has_postfix_position()):
      start_cursor = self._DecodeCompiledCursor(query.compiled_cursor())
      self.__last_result = start_cursor[0]
      start_cursor_position = self._GetCursorOffset(results, start_cursor)
    else:
      self.__last_result = None
      start_cursor_position = 0

    if query.has_end_compiled_cursor():
      if query.end_compiled_cursor().has_postfix_position():
        end_cursor = self._DecodeCompiledCursor(query.end_compiled_cursor())
        end_cursor_position = self._GetCursorOffset(results, end_cursor)
      else:
        end_cursor_position = 0
    else:
      end_cursor_position = len(results)


    results = results[start_cursor_position:end_cursor_position]


    if query.has_limit():
      limit = query.limit()
      if query.offset():
        limit += query.offset()
      if limit >= 0 and limit < len(results):
        results = results[:limit]

    self.__results = results
    self.__offset = 0
    self.__count = len(self.__results)

  def _GetCursorOffset(self, results, cursor):
    """Converts a cursor into a offset into the result set even if the
    cursor's entity no longer exists.

    Args:
      results: the query's results (sequence of entity_pb.EntityProto)
      cursor: a compiled cursor as returned by _DecodeCompiledCursor
    Returns:
      the integer offset
    """
    lo = 0
    hi = len(results)
    while lo < hi:
      mid = (lo + hi) // 2
      if self._IsBeforeCursor(results[mid], cursor):
        lo = mid + 1
      else:
        hi = mid
    return lo

  def _PopulateQueryResult(self, result, count, offset, compile, first_result):
    Check(offset >= 0, 'Offset must be >= 0')

    offset = min(offset, self.__count - self.__offset)
    limited_offset = min(offset, _MAX_QUERY_OFFSET)
    if limited_offset:
      self.__offset += limited_offset
      result.set_skipped_results(limited_offset)

    if compile and result.skipped_results() > 0:
      self._EncodeCompiledCursor(
          self.__results[self.__offset - 1].entity,
          result.mutable_skipped_results_compiled_cursor())
    if offset == limited_offset and count:

      if count > _MAXIMUM_RESULTS:
        count = _MAXIMUM_RESULTS
      results = self.__results[self.__offset:self.__offset + count]
      count = len(results)
      self.__offset += count





      records = [LoadRecord(record, self.keys_only, self.property_names)
                 for record in results]
      entities = [record.entity for record in records]
      versions = [record.metadata.updated_version() for record in records
                  if record.metadata.has_updated_version()]

      result.result_list().extend(entities)
      if len(versions) == len(entities):
        result.version_list().extend(versions)

      if compile:
        for record in results:
          self._EncodeCompiledCursor(record.entity,
                                     result.add_result_compiled_cursor())

    if self.__offset:

      self.__last_result = self.__results[self.__offset - 1].entity

    result.set_more_results(self.__offset < self.__count)
    self._PopulateResultMetadata(result, compile,
                                 first_result, self.__last_result)


def _SynchronizeTxn(function):
  """A decorator that locks a transaction during the function call."""

  def sync(txn, *args, **kwargs):

    txn._lock.acquire()
    try:

      Check(txn._state is LiveTxn.ACTIVE, 'transaction closed')

      return function(txn, *args, **kwargs)
    finally:

      txn._lock.release()
  return sync


def _GetEntityGroup(ref):
  """Returns the entity group key for the given reference."""
  entity_group = entity_pb.Reference()
  entity_group.CopyFrom(ref)
  assert (entity_group.path().element_list()[0].has_id() or
          entity_group.path().element_list()[0].has_name())
  del entity_group.path().element_list()[1:]
  return entity_group


def _GetKeyKind(key):
  """Return the kind of the given key."""
  return key.path().element_list()[-1].type()


def _FilterIndexesByKind(key, indexes):
  """Return only the indexes with the specified kind."""
  return filter((lambda index:
                 index.definition().entity_type() == _GetKeyKind(key)), indexes)


class LiveTxn(object):
  """An in flight transaction."""


















  ACTIVE = 1
  COMMITED = 2
  ROLLEDBACK = 3
  FAILED = 4

  _state = ACTIVE
  _commit_time_s = None

  def __init__(self, txn_manager, app, allow_multiple_eg):
    assert isinstance(txn_manager, BaseTransactionManager)
    assert isinstance(app, basestring)

    self._txn_manager = txn_manager
    self._app = app
    self._allow_multiple_eg = allow_multiple_eg


    self._entity_groups = {}

    self._lock = threading.RLock()
    self._apply_lock = threading.Lock()

    self._actions = []
    self._cost = datastore_pb.Cost()

    self._mutation_versions = {}

    self._mutated_references = []





    self._kind_to_indexes = collections.defaultdict(list)

  def _GetTracker(self, reference):
    """Gets the entity group tracker for reference.

    If this is the first time reference's entity group is seen, creates a new
    tracker, checking that the transaction doesn't exceed the entity group
    limit.
    """
    entity_group = _GetEntityGroup(reference)
    key = datastore_types.ReferenceToKeyValue(entity_group)
    tracker = self._entity_groups.get(key, None)
    if tracker is None:
      Check(self._app == reference.app(),
            'Transactions cannot span applications (expected %s, got %s)' %
            (self._app, reference.app()))
      if self._allow_multiple_eg:
        Check(len(self._entity_groups) < _MAX_EG_PER_TXN,
              'operating on too many entity groups in a single transaction.')
      else:
        Check(len(self._entity_groups) < 1,
              'cross-groups transaction need to be explicitly '
              'specified (xg=True)')
      tracker = EntityGroupTracker(entity_group)
      self._entity_groups[key] = tracker

    return tracker

  def _GetAllTrackers(self):
    """Get the trackers for the transaction's entity groups.

    If no entity group has been discovered returns a 'global' entity group
    tracker. This is possible if the txn only contains transactional tasks.

    Returns:
      The tracker list for the entity groups used in this txn.
    """
    if not self._entity_groups:
      self._GetTracker(datastore_types.Key.from_path(
          '__global__', 1, _app=self._app)._ToPb())
    return self._entity_groups.values()

  def _GrabSnapshot(self, reference):
    """Gets snapshot for this reference, creating it if necessary.

    If no snapshot has been set for reference's entity group, a snapshot is
    taken and stored for future reads (this also sets the read position),
    and a CONCURRENT_TRANSACTION exception is thrown if we no longer have
    a consistent snapshot.

    Args:
      reference: A entity_pb.Reference from which to extract the entity group.
    Raises:
      apiproxy_errors.ApplicationError if the snapshot is not consistent.
    """
    tracker = self._GetTracker(reference)
    check_contention = tracker._snapshot is None
    snapshot = tracker._GrabSnapshot(self._txn_manager)
    if check_contention:





      candidates = [other for other in self._entity_groups.values()
                    if other._snapshot is not None and other != tracker]
      meta_data_list = [other._meta_data for other in candidates]
      self._txn_manager._AcquireWriteLocks(meta_data_list)
      try:
        for other in candidates:
          if other._meta_data._log_pos != other._read_pos:
            self._state = self.FAILED
            raise apiproxy_errors.ApplicationError(
                datastore_pb.Error.CONCURRENT_TRANSACTION,
                'Concurrency exception.')
      finally:
        self._txn_manager._ReleaseWriteLocks(meta_data_list)
    return snapshot

  @_SynchronizeTxn
  def Get(self, reference):
    """Returns the entity associated with the given entity_pb.Reference or None.

    Does not see any modifications in the current txn.

    Args:
      reference: The entity_pb.Reference of the entity to look up.

    Returns:
      The associated entity_pb.EntityProto or None if no such entity exists.
    """
    snapshot = self._GrabSnapshot(reference)
    record = snapshot.get(datastore_types.ReferenceToKeyValue(reference))
    return LoadRecord(record)

  @_SynchronizeTxn
  def GetQueryCursor(self, query, filters, orders, index_list):
    """Runs the given datastore_pb.Query and returns a QueryCursor for it.

    Does not see any modifications in the current txn.

    Args:
      query: The datastore_pb.Query to run.
      filters: A list of filters that override the ones found on query.
      orders: A list of orders that override the ones found on query.
      index_list: A list of indexes used by the query.

    Returns:
      A BaseCursor that can be used to fetch query results.
    """
    Check(query.has_ancestor(),
          'Query must have an ancestor when performed in a transaction.')
    snapshot = self._GrabSnapshot(query.ancestor())
    return _ExecuteQuery(snapshot.values(), query, filters, orders, index_list)

  @_SynchronizeTxn
  def Put(self, entity, insert, indexes):
    """Puts the given entity.

    Args:
      entity: The entity_pb.EntityProto to put.
      insert: A boolean that indicates if we should fail if the entity already
        exists.
      indexes: The composite indexes that apply to the entity.
    """
    tracker = self._GetTracker(entity.key())
    key = datastore_types.ReferenceToKeyValue(entity.key())
    tracker._delete.pop(key, None)
    tracker._put[key] = (entity, insert)
    self._kind_to_indexes[_GetKeyKind(entity.key())] = indexes

  @_SynchronizeTxn
  def Delete(self, reference, indexes):
    """Deletes the entity associated with the given reference.

    Args:
      reference: The entity_pb.Reference of the entity to delete.
      indexes: The composite indexes that apply to the entity.
    """
    tracker = self._GetTracker(reference)
    key = datastore_types.ReferenceToKeyValue(reference)
    tracker._put.pop(key, None)
    tracker._delete[key] = reference
    self._kind_to_indexes[_GetKeyKind(reference)] = indexes

  @_SynchronizeTxn
  def AddActions(self, actions, max_actions=None):
    """Adds the given actions to the current txn.

    Args:
      actions: A list of pbs to send to taskqueue.Add when the txn is applied.
      max_actions: A number that indicates the maximum number of actions to
        allow on this txn.
    """
    Check(not max_actions or len(self._actions) + len(actions) <= max_actions,
          'Too many messages, maximum allowed %s' % max_actions)
    self._actions.extend(actions)

  def Rollback(self):
    """Rollback the current txn."""

    self._lock.acquire()
    try:
      Check(self._state is self.ACTIVE or self._state is self.FAILED,
            'transaction closed')
      self._state = self.ROLLEDBACK
    finally:
      self._txn_manager._RemoveTxn(self)

      self._lock.release()

  @_SynchronizeTxn
  def Commit(self):
    """Commits the current txn.

    This function hands off the responsibility of calling _Apply to the owning
    TransactionManager.

    Returns:
      The cost of the transaction.
    """
    try:

      trackers = self._GetAllTrackers()
      empty = True
      for tracker in trackers:
        snapshot = tracker._GrabSnapshot(self._txn_manager)
        empty = empty and not tracker._put and not tracker._delete


        for entity, insert in tracker._put.itervalues():
          Check(not insert or self.Get(entity.key()) is None,
                'the id allocated for a new entity was already '
                'in use, please try again')

          old_entity = None
          old_version = None
          key = datastore_types.ReferenceToKeyValue(entity.key())
          self._mutated_references.append(entity.key())
          if key in snapshot:
            old_entity = snapshot[key].entity
            old_version = snapshot[key].metadata.updated_version()
          self._AddWriteOps(old_entity, entity)

          if _IsNoOpWrite(old_entity, entity):
            self._mutation_versions[key] = old_version

        for reference in tracker._delete.itervalues():


          old_entity = None
          key = datastore_types.ReferenceToKeyValue(reference)
          self._mutated_references.append(reference)
          if key in snapshot:
            old_entity = snapshot[key].entity
            self._AddWriteOps(None, old_entity)

          if _IsNoOpWrite(old_entity, None):
            self._mutation_versions[key] = tracker._read_timestamp


      if empty and not self._actions:
        self.Rollback()
        return datastore_pb.Cost()


      meta_data_list = [tracker._meta_data for tracker in trackers]
      self._txn_manager._AcquireWriteLocks(meta_data_list)
    except:

      self.Rollback()
      raise

    try:

      for tracker in trackers:
        Check(tracker._meta_data._log_pos == tracker._read_pos,
              'Concurrency exception.',
              datastore_pb.Error.CONCURRENT_TRANSACTION)


      for tracker in trackers:
        tracker._meta_data.Log(self)
      self._state = self.COMMITED
      self._commit_time_s = time.time()
      write_timestamp = self._txn_manager._IncrementAndGetCommitTimestamp()

      for reference in self._mutated_references:
        key = datastore_types.ReferenceToKeyValue(reference)
        if key not in self._mutation_versions:
          self._mutation_versions[key] = write_timestamp
    except:

      self.Rollback()
      raise
    else:

      for action in self._actions:
        try:
          apiproxy_stub_map.MakeSyncCall(
              'taskqueue', 'Add', action, api_base_pb.VoidProto())
        except apiproxy_errors.ApplicationError, e:
          logging.warning('Transactional task %s has been dropped, %s',
                          action, e)
      self._actions = []
    finally:
      self._txn_manager._RemoveTxn(self)

      self._txn_manager._ReleaseWriteLocks(meta_data_list)


    self._txn_manager._consistency_policy._OnCommit(self)
    return self._cost

  def GetMutationVersion(self, reference):
    """Returns the version of an entity after this transaction has commited."""
    assert self._state == self.COMMITED
    key = datastore_types.ReferenceToKeyValue(reference)
    return self._mutation_versions[key]

  def _AddWriteOps(self, old_entity, new_entity):
    """Adds the cost of writing the new_entity to the _cost member.

    We assume that old_entity represents the current state of the Datastore.

    Args:
      old_entity: Entity representing the current state in the Datstore.
      new_entity: Entity representing the desired state in the Datstore.
    """
    composite_indexes = self._kind_to_indexes[_GetKeyKind(new_entity.key())]
    entity_writes, index_writes = _CalculateWriteOps(
        composite_indexes, old_entity, new_entity)
    _UpdateCost(self._cost, entity_writes, index_writes)

  def _Apply(self, meta_data):
    """Applies the current txn on the given entity group.

    This function blindly performs the operations contained in the current txn.
    The calling function must acquire the entity group write lock and ensure
    transactions are applied in order.
    """

    self._apply_lock.acquire()
    try:

      assert self._state == self.COMMITED
      for tracker in self._entity_groups.values():
        if tracker._meta_data is meta_data:
          break
      else:
        assert False
      assert tracker._read_pos != tracker.APPLIED


      for entity, insert in tracker._put.itervalues():
        key = datastore_types.ReferenceToKeyValue(entity.key())
        if key in tracker._snapshot:
          metadata = tracker._snapshot[key].metadata
        else:
          metadata = entity_pb.EntityMetadata()
        metadata.set_updated_version(self.GetMutationVersion(entity.key()))
        record = EntityRecord(entity, metadata)
        self._txn_manager._Put(record, insert)


      for key in tracker._delete.itervalues():
        self._txn_manager._Delete(key)


      tracker._read_pos = EntityGroupTracker.APPLIED


      tracker._meta_data.Unlog(self)
    finally:
      self._apply_lock.release()


class EntityRecord(object):
  """An EntityProto and its associated EntityMetadata protobuf."""

  def __init__(self, entity, metadata=None):
    self.entity = entity
    self.metadata = metadata or entity_pb.EntityMetadata()


class EntityGroupTracker(object):
  """An entity group involved a transaction."""

  APPLIED = -2





  _read_pos = None


  _read_timestamp = None


  _snapshot = None


  _meta_data = None

  def __init__(self, entity_group):
    self._entity_group = entity_group
    self._put = {}
    self._delete = {}

  def _GrabSnapshot(self, txn_manager):
    """Snapshot this entity group, remembering the read position."""
    if self._snapshot is None:
      self._meta_data, self._read_pos, self._read_timestamp, self._snapshot = (
          txn_manager._GrabSnapshot(self._entity_group))
    return self._snapshot


class EntityGroupMetaData(object):
  """The meta_data assoicated with an entity group."""


  _log_pos = -1
  _read_timestamp = None

  _snapshot = None

  def __init__(self, entity_group):
    self._entity_group = entity_group
    self._write_lock = threading.Lock()
    self._apply_queue = []

  def CatchUp(self):
    """Applies all outstanding txns."""

    assert self._write_lock.acquire(False) is False

    while self._apply_queue:
      self._apply_queue[0]._Apply(self)

  def Log(self, txn):
    """Add a pending transaction to this entity group.

    Requires that the caller hold the meta data lock.
    This also increments the current log position and clears the snapshot cache.
    """

    assert self._write_lock.acquire(False) is False
    self._apply_queue.append(txn)
    self._log_pos += 1
    self._snapshot = None

  def Unlog(self, txn):
    """Remove the first pending transaction from the apply queue.

    Requires that the caller hold the meta data lock.
    This checks that the first pending transaction is indeed txn.
    """

    assert self._write_lock.acquire(False) is False

    Check(self._apply_queue and self._apply_queue[0] is txn,
          'Transaction is not appliable',
          datastore_pb.Error.INTERNAL_ERROR)
    self._apply_queue.pop(0)


class BaseConsistencyPolicy(object):
  """A base class for a consistency policy to be used with a transaction manger.
  """



  def _OnCommit(self, txn):
    """Called after a LiveTxn has been commited.

    This function can decide whether to apply the txn right away.

    Args:
      txn: A LiveTxn that has been commited
    """
    raise NotImplementedError

  def _OnGroom(self, meta_data_list):
    """Called once for every global query.

    This function must aqcuire the write lock for any meta data before applying
    any outstanding txns.

    Args:
      meta_data_list: A list of EntityGroupMetaData objects.
    """
    raise NotImplementedError


class MasterSlaveConsistencyPolicy(BaseConsistencyPolicy):
  """Enforces the Master / Slave consistency policy.

  Applies all txn on commit.
  """

  def _OnCommit(self, txn):

    for tracker in txn._GetAllTrackers():
      tracker._meta_data._write_lock.acquire()
      try:
        tracker._meta_data.CatchUp()
      finally:
        tracker._meta_data._write_lock.release()




    txn._txn_manager.Write()

  def _OnGroom(self, meta_data_list):


    pass


class BaseHighReplicationConsistencyPolicy(BaseConsistencyPolicy):
  """A base class for High Replication Datastore consistency policies.

  All txn are applied asynchronously.
  """

  def _OnCommit(self, txn):
    pass

  def _OnGroom(self, meta_data_list):


    for meta_data in meta_data_list:
      if not meta_data._apply_queue:
        continue


      meta_data._write_lock.acquire()
      try:
        while meta_data._apply_queue:
          txn = meta_data._apply_queue[0]
          if self._ShouldApply(txn, meta_data):
            txn._Apply(meta_data)
          else:
            break
      finally:
        meta_data._write_lock.release()

  def _ShouldApply(self, txn, meta_data):
    """Determins if the given transaction should be applied."""
    raise NotImplementedError


class TimeBasedHRConsistencyPolicy(BaseHighReplicationConsistencyPolicy):
  """A High Replication Datastore consiseny policy based on elapsed time.

  This class tries to simulate performance seen in the high replication
  datastore using estimated probabilities of a transaction commiting after a
  given amount of time.
  """

  _classification_map = [(.98, 100),
                         (.99, 300),
                         (.995, 2000),
                         (1, 240000)
                        ]

  def SetClassificationMap(self, classification_map):
    """Set the probability a txn will be applied after a given amount of time.

    Args:
      classification_map: A list of tuples containing (float between 0 and 1,
        number of miliseconds) that define the probability of a transaction
        applying after a given amount of time.
    """
    for prob, delay in classification_map:
      if prob < 0 or prob > 1 or delay <= 0:
        raise TypeError(
            'classification_map must be a list of (probability, delay) tuples, '
            'found %r' % (classification_map,))

    self._classification_map = sorted(classification_map)

  def _ShouldApplyImpl(self, elapsed_ms, classification):
    for rate, ms in self._classification_map:
      if classification <= rate:
        break
    return elapsed_ms >= ms

  def _Classify(self, txn, meta_data):
    return random.Random(id(txn) ^ id(meta_data)).random()

  def _ShouldApply(self, txn, meta_data):
    elapsed_ms = (time.time() - txn._commit_time_s) * 1000
    classification = self._Classify(txn, meta_data)
    return self._ShouldApplyImpl(elapsed_ms, classification)


class PseudoRandomHRConsistencyPolicy(BaseHighReplicationConsistencyPolicy):
  """A policy that always gives the same sequence of consistency decisions."""

  def __init__(self, probability=.5, seed=0):
    """Constructor.

    Args:
      probability: A number between 0 and 1 that is the likelihood of a
        transaction applying before a global query is executed.
      seed: A hashable object to use as a seed. Use None to use the current
        timestamp.
    """
    self.SetProbability(probability)
    self.SetSeed(seed)

  def SetProbability(self, probability):
    """Change the probability of a transaction applying.

    Args:
      probability: A number between 0 and 1 that determins the probability of a
        transaction applying before a global query is run.
    """
    if probability < 0 or probability > 1:
      raise TypeError('probability must be a number between 0 and 1, found %r' %
                      probability)
    self._probability = probability

  def SetSeed(self, seed):
    """Reset the seed."""
    self._random = random.Random(seed)

  def _ShouldApply(self, txn, meta_data):
    return self._random.random() < self._probability


class BaseTransactionManager(object):
  """A class that manages the state of transactions.

  This includes creating consistent snap shots for transactions.
  """
  _commit_timestamp = MINIMUM_VERSION

  def __init__(self, consistency_policy=None):
    super(BaseTransactionManager, self).__init__()

    self._consistency_policy = (consistency_policy or
                                MasterSlaveConsistencyPolicy())


    self._meta_data_lock = threading.Lock()
    self._commit_timestamp_lock = threading.Lock()
    BaseTransactionManager.Clear(self)

  def SetConsistencyPolicy(self, policy):
    """Set the consistency to use.

    Causes all data to be flushed.

    Args:
      policy: A obj inheriting from BaseConsistencyPolicy.
    """
    if not isinstance(policy, BaseConsistencyPolicy):
      raise TypeError('policy should be of type '
                      'datastore_stub_util.BaseConsistencyPolicy found %r.' %
                      (policy,))
    self.Flush()
    self._consistency_policy = policy

  def Clear(self):
    """Discards any pending transactions and resets the meta data."""

    self._meta_data = {}

    self._txn_map = {}

  def BeginTransaction(self, app, allow_multiple_eg):
    """Start a transaction on the given app.

    Args:
      app: A string representing the app for which to start the transaction.
      allow_multiple_eg: True if transactions can span multiple entity groups.

    Returns:
      A datastore_pb.Transaction for the created transaction
    """
    Check(not (allow_multiple_eg and isinstance(
        self._consistency_policy, MasterSlaveConsistencyPolicy)),
          'transactions on multiple entity groups only allowed with the '
          'High Replication datastore')
    txn = self._BeginTransaction(app, allow_multiple_eg)
    self._txn_map[id(txn)] = txn
    transaction = datastore_pb.Transaction()
    transaction.set_app(app)
    transaction.set_handle(id(txn))
    return transaction

  def GetTxn(self, transaction, request_trusted, request_app):
    """Gets the LiveTxn object associated with the given transaction.

    Args:
      transaction: The datastore_pb.Transaction to look up.
      request_trusted: A boolean indicating If the requesting app is trusted.
      request_app: A string representing the app making the request.

    Returns:
      The associated LiveTxn object.
    """
    request_app = datastore_types.ResolveAppId(request_app)
    CheckTransaction(request_trusted, request_app, transaction)
    txn = self._txn_map.get(transaction.handle())
    Check(txn and txn._app == transaction.app(),
          'Transaction(<%s>) not found' % str(transaction).replace('\n', ', '))
    return txn

  def Groom(self):
    """Attempts to apply any outstanding transactions.

    The consistency policy determins if a transaction should be applied.
    """
    self._meta_data_lock.acquire()
    try:
      self._consistency_policy._OnGroom(self._meta_data.itervalues())
    finally:
      self._meta_data_lock.release()

  def Flush(self):
    """Applies all outstanding transactions."""
    self._meta_data_lock.acquire()
    try:
      for meta_data in self._meta_data.itervalues():
        if not meta_data._apply_queue:
          continue


        meta_data._write_lock.acquire()
        try:
          meta_data.CatchUp()
        finally:
          meta_data._write_lock.release()
    finally:
      self._meta_data_lock.release()

  def _IncrementAndGetCommitTimestamp(self):
    with self._commit_timestamp_lock:
      now_ms = int(time.time() * 1000)
      self._commit_timestamp = max(self._commit_timestamp + 1, now_ms)
      return self._commit_timestamp

  def _GetReadTimestamp(self):
    return self._commit_timestamp

  def _GetMetaData(self, entity_group):
    """Safely gets the EntityGroupMetaData object for the given entity_group.
    """
    self._meta_data_lock.acquire()
    try:
      key = datastore_types.ReferenceToKeyValue(entity_group)

      meta_data = self._meta_data.get(key, None)
      if not meta_data:
        meta_data = EntityGroupMetaData(entity_group)
        self._meta_data[key] = meta_data
      return meta_data
    finally:
      self._meta_data_lock.release()

  def _BeginTransaction(self, app, allow_multiple_eg):
    """Starts a transaction without storing it in the txn_map."""
    return LiveTxn(self, app, allow_multiple_eg)

  def _GrabSnapshot(self, entity_group):
    """Grabs a consistent snapshot of the given entity group.

    Args:
      entity_group: A entity_pb.Reference of the entity group of which the
        snapshot should be taken.

    Returns:
      A tuple of (meta_data, log_pos, snapshot) where log_pos is the current log
      position and snapshot is a map of reference key value to
      entity_pb.EntityProto.
    """

    meta_data = self._GetMetaData(entity_group)
    meta_data._write_lock.acquire()
    try:
      if not meta_data._snapshot:

        meta_data.CatchUp()
        meta_data._snapshot = self._GetEntitiesInEntityGroup(entity_group)
        meta_data._read_timestamp = self._GetReadTimestamp()
      return (meta_data, meta_data._log_pos, meta_data._read_timestamp,
              meta_data._snapshot)
    finally:

      meta_data._write_lock.release()

  def _AcquireWriteLocks(self, meta_data_list):
    """Acquire the write locks for the given entity group meta data.

    These locks must be released with _ReleaseWriteLock before returning to the
    user.

    Args:
      meta_data_list: list of EntityGroupMetaData objects.
    """
    for meta_data in sorted(meta_data_list):
      meta_data._write_lock.acquire()

  def _ReleaseWriteLocks(self, meta_data_list):
    """Release the write locks of the given entity group meta data.

    Args:
      meta_data_list: list of EntityGroupMetaData objects.
    """
    for meta_data in sorted(meta_data_list):
      meta_data._write_lock.release()

  def _RemoveTxn(self, txn):
    """Removes a LiveTxn from the txn_map (if present)."""
    self._txn_map.pop(id(txn), None)

  def _Put(self, record, insert):
    """Put the given entity record.

    This must be implemented by a sub-class. The sub-class can assume that any
    need consistency is enforced at a higher level (and can just put blindly).

    Args:
      record: The EntityRecord to put.
      insert: A boolean that indicates if we should fail if the entity already
        exists.
    """
    raise NotImplementedError

  def _Delete(self, reference):
    """Delete the entity associated with the specified reference.

    This must be implemented by a sub-class. The sub-class can assume that any
    need consistency is enforced at a higher level (and can just delete
    blindly).

    Args:
      reference: The entity_pb.Reference of the entity to delete.
    """
    raise NotImplementedError

  def _GetEntitiesInEntityGroup(self, entity_group):
    """Gets the contents of a specific entity group.

    This must be implemented by a sub-class. The sub-class can assume that any
    need consistency is enforced at a higher level (and can just blindly read).

    Other entity groups may be modified concurrently.

    Args:
      entity_group: A entity_pb.Reference of the entity group to get.

    Returns:
      A dict mapping datastore_types.ReferenceToKeyValue(key) to EntityRecord.
    """
    raise NotImplementedError


class BaseIndexManager(object):
  """A generic index manager that stores all data in memory."""








  WRITE_ONLY = entity_pb.CompositeIndex.WRITE_ONLY
  READ_WRITE = entity_pb.CompositeIndex.READ_WRITE
  DELETED = entity_pb.CompositeIndex.DELETED
  ERROR = entity_pb.CompositeIndex.ERROR

  _INDEX_STATE_TRANSITIONS = {
      WRITE_ONLY: frozenset((READ_WRITE, DELETED, ERROR)),
      READ_WRITE: frozenset((DELETED,)),
      ERROR: frozenset((DELETED,)),
      DELETED: frozenset((ERROR,)),
  }

  def __init__(self):



    self.__indexes = collections.defaultdict(list)
    self.__indexes_lock = threading.Lock()
    self.__next_index_id = 1
    self.__index_id_lock = threading.Lock()

  def __FindIndex(self, index):
    """Finds an existing index by definition.

    Args:
      index: entity_pb.CompositeIndex

    Returns:
      entity_pb.CompositeIndex, if it exists; otherwise None
    """
    app = index.app_id()
    if app in self.__indexes:
      for stored_index in self.__indexes[app]:
        if index.definition() == stored_index.definition():
          return stored_index

    return None

  def CreateIndex(self, index, trusted=False, calling_app=None):


    calling_app = datastore_types.ResolveAppId(calling_app)
    CheckAppId(trusted, calling_app, index.app_id())
    Check(index.id() == 0, 'New index id must be 0.')
    Check(not self.__FindIndex(index), 'Index already exists.')


    self.__index_id_lock.acquire()
    index.set_id(self.__next_index_id)
    self.__next_index_id += 1
    self.__index_id_lock.release()


    clone = entity_pb.CompositeIndex()
    clone.CopyFrom(index)
    app = index.app_id()
    clone.set_app_id(app)


    self.__indexes_lock.acquire()
    try:
      self.__indexes[app].append(clone)
    finally:
      self.__indexes_lock.release()

    self._OnIndexChange(index.app_id())

    return index.id()

  def GetIndexes(self, app, trusted=False, calling_app=None):
    """Get the CompositeIndex objects for the given app."""
    calling_app = datastore_types.ResolveAppId(calling_app)
    CheckAppId(trusted, calling_app, app)

    return self.__indexes[app]

  def UpdateIndex(self, index, trusted=False, calling_app=None):
    CheckAppId(trusted, calling_app, index.app_id())

    stored_index = self.__FindIndex(index)
    Check(stored_index, 'Index does not exist.')
    Check(index.state() == stored_index.state() or
          index.state() in self._INDEX_STATE_TRANSITIONS[stored_index.state()],
          'cannot move index state from %s to %s' %
          (entity_pb.CompositeIndex.State_Name(stored_index.state()),
           (entity_pb.CompositeIndex.State_Name(index.state()))))


    self.__indexes_lock.acquire()
    try:
      stored_index.set_state(index.state())
    finally:
      self.__indexes_lock.release()

    self._OnIndexChange(index.app_id())

  def DeleteIndex(self, index, trusted=False, calling_app=None):
    CheckAppId(trusted, calling_app, index.app_id())

    stored_index = self.__FindIndex(index)
    Check(stored_index, 'Index does not exist.')


    app = index.app_id()
    self.__indexes_lock.acquire()
    try:
      self.__indexes[app].remove(stored_index)
    finally:
      self.__indexes_lock.release()

    self._OnIndexChange(index.app_id())

  def _SideLoadIndex(self, index):
    self.__indexes[index.app()].append(index)

  def _OnIndexChange(self, app_id):
    pass


class BaseDatastore(BaseTransactionManager, BaseIndexManager):
  """A base implemenation of a Datastore.

  This class implements common functions associated with a datastore and
  enforces security restrictions passed on by a stub or client. It is designed
  to be shared by any number of threads or clients serving any number of apps.

  If an app is not specified explicitly it is pulled from the env and assumed to
  be untrusted.
  """



  _MAX_QUERY_COMPONENTS = 100



  _BATCH_SIZE = 20



  _MAX_ACTIONS_PER_TXN = 5

  def __init__(self, require_indexes=False, consistency_policy=None,
               use_atexit=True, auto_id_policy=SEQUENTIAL):
    BaseTransactionManager.__init__(self, consistency_policy=consistency_policy)
    BaseIndexManager.__init__(self)

    self._require_indexes = require_indexes
    self._pseudo_kinds = {}
    self.SetAutoIdPolicy(auto_id_policy)

    if use_atexit:




      atexit.register(self.Write)

  def Clear(self):
    """Clears out all stored values."""

    BaseTransactionManager.Clear(self)


  def _RegisterPseudoKind(self, kind):
    """Registers a pseudo kind to be used to satisfy a meta data query."""
    self._pseudo_kinds[kind.name] = kind
    kind._stub = weakref.proxy(self)




  def GetQueryCursor(self, raw_query, trusted=False, calling_app=None):
    """Execute a query.

    Args:
      raw_query: The non-validated datastore_pb.Query to run.
      trusted: If the calling app is trusted.
      calling_app: The app requesting the results or None to pull the app from
        the environment.

    Returns:
      A BaseCursor that can be used to retrieve results.
    """

    calling_app = datastore_types.ResolveAppId(calling_app)
    CheckAppId(trusted, calling_app, raw_query.app())


    filters, orders = datastore_index.Normalize(raw_query.filter_list(),
                                                raw_query.order_list(),
                                                raw_query.property_name_list())


    CheckQuery(raw_query, filters, orders, self._MAX_QUERY_COMPONENTS)
    FillUsersInQuery(filters)

    self._CheckHasIndex(raw_query, trusted, calling_app)


    index_list = self.__IndexListForQuery(raw_query)


    if raw_query.has_transaction():

      Check(raw_query.kind() not in self._pseudo_kinds,
            'transactional queries on "%s" not allowed' % raw_query.kind())
      txn = self.GetTxn(raw_query.transaction(), trusted, calling_app)
      return txn.GetQueryCursor(raw_query, filters, orders, index_list)

    if raw_query.has_ancestor() and raw_query.kind() not in self._pseudo_kinds:

      txn = self._BeginTransaction(raw_query.app(), False)
      return txn.GetQueryCursor(raw_query, filters, orders, index_list)


    self.Groom()
    return self._GetQueryCursor(raw_query, filters, orders, index_list)

  def __IndexListForQuery(self, query):
    """Get the single composite index pb used by the query, if any, as a list.

    Args:
      query: the datastore_pb.Query to compute the index list for

    Returns:
      A singleton list of the composite index pb used by the query,
    """

    required, kind, ancestor, props = (
        datastore_index.CompositeIndexForQuery(query))
    if not required:
      return []
    composite_index_pb = entity_pb.CompositeIndex()
    composite_index_pb.set_app_id(query.app())
    composite_index_pb.set_id(0)
    composite_index_pb.set_state(entity_pb.CompositeIndex.READ_WRITE)
    index_pb = composite_index_pb.mutable_definition()
    index_pb.set_entity_type(kind)
    index_pb.set_ancestor(bool(ancestor))
    for name, direction in datastore_index.GetRecommendedIndexProperties(props):
      prop_pb = entity_pb.Index_Property()
      prop_pb.set_name(name)
      prop_pb.set_direction(direction)
      index_pb.property_list().append(prop_pb)
    return [composite_index_pb]

  def Get(self, raw_keys, transaction=None, eventual_consistency=False,
          trusted=False, calling_app=None):
    """Get the entity records for the given keys.

    Args:
      raw_keys: A list of unverified entity_pb.Reference objects.
      transaction: The datastore_pb.Transaction to use or None.
      eventual_consistency: If we should allow stale, potentially inconsistent
        results.
      trusted: If the calling app is trusted.
      calling_app: The app requesting the results or None to pull the app from
        the environment.

    Returns:
      A list containing the records in the same order as the list of keys.
    """
    if not raw_keys:
      return []

    calling_app = datastore_types.ResolveAppId(calling_app)
    records = []

    if not transaction and eventual_consistency:
      self.Groom()

      for key in raw_keys:
        CheckReference(calling_app, trusted, key)
        records.append(self._GetWithPseudoKinds(None, key,
                                                eventual_consistency))
    else:

      grouped_keys = collections.defaultdict(list)
      for i, key in enumerate(raw_keys):
        CheckReference(trusted, calling_app, key)
        entity_group = _GetEntityGroup(key)
        entity_group_key = datastore_types.ReferenceToKeyValue(entity_group)
        grouped_keys[entity_group_key].append((key, i))

      if transaction:

        txn = self.GetTxn(transaction, trusted, calling_app)
        records = [self._GetWithPseudoKinds(txn, key, eventual_consistency)
                   for key in raw_keys]
      else:



        records = [None] * len(raw_keys)

        def op(txn, v):
          key, i = v
          records[i] = self._GetWithPseudoKinds(txn, key, eventual_consistency)
        for keys in grouped_keys.itervalues():
          self._RunInTxn(keys, keys[0][0].app(), op)

    return records

  def _GetWithPseudoKinds(self, txn, key, eventual_consistency=False):
    """Fetch entity key in txn, taking account of pseudo-kinds."""
    pseudo_kind = self._pseudo_kinds.get(_GetKeyKind(key), None)
    if pseudo_kind:
      return EntityRecord(pseudo_kind.Get(txn, key))
    else:
      if txn:
        record = txn.Get(key)
      else:
        record = self._Get(key)

      if not record:
        metadata = entity_pb.EntityMetadata()
        if not eventual_consistency:
          metadata.set_updated_version(self._GetReadTimestamp())
        record = EntityRecord(None, metadata)

      return record

  def Put(self, raw_entities, cost, transaction=None,
          trusted=False, calling_app=None):
    """Writes the given given entities.

    Updates an entity's key and entity_group in place if needed

    Args:
      raw_entities: A list of unverified entity_pb.EntityProto objects.
      cost: Out param. The cost of putting the provided entities.
      transaction: The datastore_pb.Transaction to use or None.
      trusted: If the calling app is trusted.
      calling_app: The app requesting the results or None to pull the app from
        the environment.
    Returns:
      A list of tuple (entity_pb.Reference, version number) that indicates where
      each entity was stored and at which version. When a transaction is
      provided, all version numbers are None.
    """
    if not raw_entities:
      return []

    calling_app = datastore_types.ResolveAppId(calling_app)


    result = [None] * len(raw_entities)
    grouped_entities = collections.defaultdict(list)
    for i, raw_entity in enumerate(raw_entities):
      CheckEntity(trusted, calling_app, raw_entity)



      entity = entity_pb.EntityProto()
      entity.CopyFrom(raw_entity)


      for prop in itertools.chain(entity.property_list(),
                                  entity.raw_property_list()):
        FillUser(prop)

      last_element = entity.key().path().element_list()[-1]
      if not (last_element.id() or last_element.has_name()):
        insert = True


        if self._auto_id_policy == SEQUENTIAL:
          last_element.set_id(self._AllocateSequentialIds(entity.key())[0])
        else:
          full_key = self._AllocateIds([entity.key()])[0]
          last_element.set_id(full_key.path().element_list()[-1].id())
      else:
        insert = False

      entity_group = _GetEntityGroup(entity.key())
      entity.mutable_entity_group().CopyFrom(entity_group.path())
      entity_group_key = datastore_types.ReferenceToKeyValue(entity_group)
      grouped_entities[entity_group_key].append((entity, insert, i))



      key = entity_pb.Reference()
      key.CopyFrom(entity.key())
      result[i] = key

    mutation_versions = [None] * len(raw_entities)
    if transaction:

      txn = self.GetTxn(transaction, trusted, calling_app)
      for group in grouped_entities.values():
        for entity, insert, _ in group:

          indexes = _FilterIndexesByKind(entity.key(), self.GetIndexes(
              entity.key().app(), trusted, calling_app))
          txn.Put(entity, insert, indexes)
    else:

      for entities in grouped_entities.itervalues():
        txn = self._RunInTxn(
            entities, entities[0][0].key().app(),

            lambda txn, v: txn.Put(v[0], v[1], _FilterIndexesByKind(
                v[0].key(),
                self.GetIndexes(v[0].key().app(), trusted, calling_app))))

        for entity, _, index in entities:
          mutation_versions[index] = txn.GetMutationVersion(entity.key())
        _UpdateCost(cost, txn._cost.entity_writes(), txn._cost.index_writes())

    return zip(result, mutation_versions)

  def Delete(self, raw_keys, cost, transaction=None,
             trusted=False, calling_app=None):
    """Deletes the entities associated with the given keys.

    Args:
      raw_keys: A list of unverified entity_pb.Reference objects.
      cost: Out param. The cost of putting the provided entities.
      transaction: The datastore_pb.Transaction to use or None.
      trusted: If the calling app is trusted.
      calling_app: The app requesting the results or None to pull the app from
        the environment.

    Returns:
      A list of versions numbers at which the entities were deleted, one for
      each given keys. Every version numbers are None if a transaction is given.
    """
    if not raw_keys:
      return []

    calling_app = datastore_types.ResolveAppId(calling_app)


    grouped_keys = collections.defaultdict(list)
    for i, key in enumerate(raw_keys):
      CheckReference(trusted, calling_app, key)
      entity_group = _GetEntityGroup(key)
      entity_group_key = datastore_types.ReferenceToKeyValue(entity_group)
      grouped_keys[entity_group_key].append((key, i))

    mutation_versions = [None] * len(raw_keys)
    if transaction:

      txn = self.GetTxn(transaction, trusted, calling_app)
      for key in raw_keys:

        indexes = _FilterIndexesByKind(key, self.GetIndexes(
            key.app(), trusted, calling_app))
        txn.Delete(key, indexes)
    else:

      for keys in grouped_keys.itervalues():

        txn = self._RunInTxn(
            keys, keys[0][0].app(),
            lambda txn, key: txn.Delete(key[0], _FilterIndexesByKind(
                key[0], self.GetIndexes(key[0].app(), trusted, calling_app))))

        for key, index in keys:
          mutation_versions[index] = txn.GetMutationVersion(key)
        _UpdateCost(cost, txn._cost.entity_writes(), txn._cost.index_writes())

    return mutation_versions

  def Touch(self, raw_keys, trusted=False, calling_app=None):
    """Applies all outstanding writes."""
    calling_app = datastore_types.ResolveAppId(calling_app)

    grouped_keys = collections.defaultdict(list)
    for key in raw_keys:
      CheckReference(trusted, calling_app, key)
      entity_group = _GetEntityGroup(key)
      entity_group_key = datastore_types.ReferenceToKeyValue(entity_group)
      grouped_keys[entity_group_key].append(key)

    for keys in grouped_keys.itervalues():
      self._RunInTxn(keys, keys[0].app(), lambda txn, key: None)

  def _RunInTxn(self, values, app, op):
    """Runs the given values in a separate Txn.

    Retries up to _RETRIES times on CONCURRENT_TRANSACTION errors.

    Args:
      values: A list of arguments to op.
      app: The app to create the Txn on.
      op: A function to run on each value in the Txn.

    Returns:
      The transaction that was commited.
    """
    retries = 0
    backoff = _INITIAL_RETRY_DELAY_MS / 1000.0
    while True:
      try:
        txn = self._BeginTransaction(app, False)
        for value in values:
          op(txn, value)
        txn.Commit()
        return txn
      except apiproxy_errors.ApplicationError, e:
        if e.application_error == datastore_pb.Error.CONCURRENT_TRANSACTION:

          retries += 1
          if retries <= _RETRIES:
            time.sleep(backoff)
            backoff *= _RETRY_DELAY_MULTIPLIER
            if backoff * 1000.0 > _MAX_RETRY_DELAY_MS:
              backoff = _MAX_RETRY_DELAY_MS / 1000.0
            continue
        raise

  def _CheckHasIndex(self, query, trusted=False, calling_app=None):
    """Checks if the query can be satisfied given the existing indexes.

    Args:
      query: the datastore_pb.Query to check
      trusted: True if the calling app is trusted (like dev_admin_console)
      calling_app: app_id of the current running application
    """
    if query.kind() in self._pseudo_kinds or not self._require_indexes:
      return

    minimal_index = datastore_index.MinimalCompositeIndexForQuery(query,
        (datastore_index.ProtoToIndexDefinition(index)
         for index in self.GetIndexes(query.app(), trusted, calling_app)
         if index.state() == entity_pb.CompositeIndex.READ_WRITE))
    if minimal_index is not None:
      msg = ('This query requires a composite index that is not defined. '
             'You must update the index.yaml file in your application root.')
      is_most_efficient, kind, ancestor, properties = minimal_index
      if not is_most_efficient:

        yaml = datastore_index.IndexYamlForQuery(
            kind, ancestor,
            datastore_index.GetRecommendedIndexProperties(properties))
        msg += '\nThe following index is the minimum index required:\n' + yaml
      raise apiproxy_errors.ApplicationError(datastore_pb.Error.NEED_INDEX, msg)

  def SetAutoIdPolicy(self, auto_id_policy):
    """Set value of _auto_id_policy flag (default SEQUENTIAL).

    SEQUENTIAL auto ID assignment behavior will eventually be deprecated
    and the default will be SCATTERED.

    Args:
      auto_id_policy: string constant.
    Raises:
      TypeError: if auto_id_policy is not one of SEQUENTIAL or SCATTERED.
    """
    valid_policies = (SEQUENTIAL, SCATTERED)
    if auto_id_policy not in valid_policies:
      raise TypeError('auto_id_policy must be in %s, found %s instead',
                      valid_policies, auto_id_policy)
    self._auto_id_policy = auto_id_policy



  def Write(self):
    """Writes the datastore to disk."""
    self.Flush()

  def Close(self):
    """Closes the Datstore, writing any buffered data."""
    self.Write()

  def _GetQueryCursor(self, query, filters, orders, index_list):
    """Runs the given datastore_pb.Query and returns a QueryCursor for it.

    This must be implemented by a sub-class. The sub-class does not need to
    enforced any consistency guarantees (and can just blindly read).

    Args:
      query: The datastore_pb.Query to run.
      filters: A list of filters that override the ones found on query.
      orders: A list of orders that override the ones found on query.
      index_list: A list of indexes used by the query.

    Returns:
      A BaseCursor that can be used to fetch query results.
    """
    raise NotImplementedError

  def _Get(self, reference):
    """Get the entity record for the given reference or None.

    This must be implemented by a sub-class. The sub-class does not need to
    enforced any consistency guarantees (and can just blindly read).

    Args:
      reference: A entity_pb.Reference to loop up.

    Returns:
      The EntityRecord associated with the given reference or None.
    """
    raise NotImplementedError

  def _AllocateSequentialIds(self, reference, size=1, max_id=None):
    """Allocate sequential ids for given reference.

    Args:
      reference: An entity_pb.Reference to allocate an id for.
      size: The size of the range to allocate
      max_id: The upper bound of the range to allocate

    Returns:
      A tuple containing (min, max) of the allocated range.
    """
    raise NotImplementedError

  def _AllocateIds(self, references):
    """Allocate or reserves IDs for the v1 datastore API.

    Incomplete keys are allocated scattered IDs. Complete keys have every id in
    their paths reserved in the appropriate ID space.

    Args:
      references: a list of entity_pb.Reference objects to allocate or reserve

    Returns:
      a list of complete entity_pb.Reference objects corresponding to the
      incomplete keys in the input, with newly allocated ids.
    """
    raise NotImplementedError


def _NeedsIndexes(func):
  """A decorator for DatastoreStub methods that require or affect indexes.

  Updates indexes to match index.yaml before the call and updates index.yaml
  after the call if require_indexes is False. If root_path is not set, this is a
  no op.
  """

  def UpdateIndexesWrapper(self, *args, **kwargs):
    self._SetupIndexes()
    try:
      return func(self, *args, **kwargs)
    finally:
      self._UpdateIndexes()

  return UpdateIndexesWrapper


class EntityGroupPseudoKind(object):
  """A common implementation of get() for the __entity_group__ pseudo-kind.

  Public properties:
    name: the pseudo-kind name
  """
  name = '__entity_group__'









  base_version = int(time.time() * 1e6)

  def Get(self, txn, key):
    """Fetch key of this pseudo-kind within txn.

    Args:
      txn: transaction within which Get occurs, may be None if this is an
           eventually consistent Get.
      key: key of pseudo-entity to Get.

    Returns:
      An entity for key, or None if it doesn't exist.
    """

    if not txn:
      txn = self._stub._BeginTransaction(key.app(), False)
      try:
        return self.Get(txn, key)
      finally:
        txn.Rollback()


    if isinstance(txn._txn_manager._consistency_policy,
                  MasterSlaveConsistencyPolicy):
      return None






    path = key.path()
    if path.element_size() != 2 or path.element_list()[-1].id() != 1:
      return None

    tracker = txn._GetTracker(key)
    tracker._GrabSnapshot(txn._txn_manager)

    eg = entity_pb.EntityProto()
    eg.mutable_key().CopyFrom(key)
    eg.mutable_entity_group().CopyFrom(_GetEntityGroup(key).path())
    version = entity_pb.Property()
    version.set_name('__version__')
    version.set_multiple(False)
    version.mutable_value().set_int64value(
        tracker._read_pos + self.base_version)
    eg.property_list().append(version)
    return eg

  def Query(self, query, filters, orders):
    """Perform a query on this pseudo-kind.

    Args:
      query: the original datastore_pb.Query.
      filters: the filters from query.
      orders: the orders from query.

    Returns:
      always raises an error
    """


    raise apiproxy_errors.ApplicationError(
        datastore_pb.Error.BAD_REQUEST, 'queries not supported on ' + self.name)


class _CachedIndexDefinitions(object):
  """Records definitions read from index configuration files for later reuse.

  If the names and modification times of the configuration files are unchanged,
  then the index configurations previously parsed out of those files can be
  reused.

  Attributes:
    file_names: a list of the names of the configuration files. This will have
      one element when the configuration is based on an index.yaml but may have
      more than one if it is based on datastore-indexes.xml and
      datastore-indexes-auto.xml.
    last_modifieds: a list of floats that are the modification times of the
      files in file_names.
    index_protos: a list of entity_pb.CompositeIndex objects corresponding to
      the index definitions read from file_names.
  """

  def __init__(self, file_names, last_modifieds, index_protos):

    assert len(file_names) <= 1
    self.file_names = file_names
    self.last_modifieds = last_modifieds
    self.index_protos = index_protos


class DatastoreStub(object):
  """A stub that maps datastore service calls on to a BaseDatastore.

  This class also keeps track of query cursors.
  """

  def __init__(self,
               datastore,
               app_id=None,
               trusted=None,
               root_path=None):
    super(DatastoreStub, self).__init__()
    self._datastore = datastore
    self._app_id = datastore_types.ResolveAppId(app_id)
    self._trusted = trusted
    self._root_path = root_path
    self._xml_configuration = self._XmlConfiguration()


    self.__query_history = {}


    self.__query_ci_history = set()



    self._cached_index_definitions = _CachedIndexDefinitions([], [], None)

    if self._require_indexes or root_path is None:

      self._index_config_updater = None
    else:


      updater_class = (
          datastore_stub_index.DatastoreIndexesAutoXmlUpdater
          if self._xml_configuration else datastore_stub_index.IndexYamlUpdater)
      self._index_config_updater = updater_class(root_path)

    DatastoreStub.Clear(self)

  def _XmlConfiguration(self):
    """Return True if the app at self._root_path uses XML configuration files.

    An app uses XML configuration files if it has a WEB-INF subdirectory and it
    does not have an index.yaml at its root. We assume this even if it doesn't
    currently have any configuration files at all, because then we will want to
    create a new datastore-indexes-auto.xml rather than create a new index.yaml.

    Returns:
      True if the app uses XML configuration files, False otherwise.

    Raises:
      yaml_errors.AmbiguousConfigurationFiles: if there is both an index.yaml
        and either or both of the two possible XML configuration files.
    """
    if not self._root_path:
      return False
    index_yaml = os.path.join(self._root_path, 'index.yaml')
    web_inf = os.path.join(self._root_path, 'WEB-INF')
    datastore_indexes_xml = os.path.join(web_inf, 'datastore-indexes.xml')
    datastore_indexes_auto_xml = os.path.join(
        web_inf, 'appengine-generated', 'datastore-indexes-auto.xml')
    existing = [
        f for f in [
            index_yaml, datastore_indexes_xml, datastore_indexes_auto_xml]
        if os.path.isfile(f)]
    if existing == [index_yaml]:
      return False
    elif index_yaml in existing:
      raise yaml_errors.AmbiguousConfigurationFiles(
          'App has both XML and YAML configuration files: %s' % existing)
    else:
      return os.path.isdir(web_inf)

  def Clear(self):
    """Clears out all stored values."""
    self._query_cursors = {}
    self.__query_history = {}
    self.__query_ci_history = set()

  def QueryHistory(self):
    """Returns a dict that maps Query PBs to times they've been run."""

    return dict((pb, times) for pb, times in self.__query_history.items()
                if pb.app() == self._app_id)

  def _QueryCompositeIndexHistoryLength(self):
    """Returns the length of the CompositeIndex set for query history."""
    return len(self.__query_ci_history)

  def SetTrusted(self, trusted):
    """Set/clear the trusted bit in the stub.

    This bit indicates that the app calling the stub is trusted. A
    trusted app can write to datastores of other apps.

    Args:
      trusted: boolean.
    """
    self._trusted = trusted



  def _Dynamic_Get(self, req, res):


    transaction = req.has_transaction() and req.transaction() or None


    if req.allow_deferred() and req.key_size() > _MAXIMUM_RESULTS:



      keys_to_get = req.key_list()[-_MAXIMUM_RESULTS:]
      deferred_keys = req.key_list()[:-_MAXIMUM_RESULTS]
      res.deferred_list().extend(deferred_keys)
    else:

      keys_to_get = req.key_list()

    res.set_in_order(not req.allow_deferred())

    total_response_bytes = 0
    for index, record in enumerate(self._datastore.Get(keys_to_get,
                                                       transaction,
                                                       req.has_failover_ms(),
                                                       self._trusted,
                                                       self._app_id)):
      entity = record.entity
      entity_size = entity and entity.ByteSize() or 0


      if (req.allow_deferred()
          and index > 0
          and total_response_bytes + entity_size > _MAXIMUM_QUERY_RESULT_BYTES):

        res.deferred_list().extend(keys_to_get[index:])
        break
      else:
        entity_result = res.add_entity()
        if record.metadata.has_updated_version():
          entity_result.set_version(record.metadata.updated_version())

        if entity:
          entity_result.mutable_entity().CopyFrom(entity)
          total_response_bytes += entity_size
        else:

          entity_result.mutable_key().CopyFrom(keys_to_get[index])

  def _Dynamic_Put(self, req, res):
    transaction = req.has_transaction() and req.transaction() or None
    results = self._datastore.Put(req.entity_list(), res.mutable_cost(),
                                  transaction, self._trusted, self._app_id)
    res.key_list().extend(result[0] for result in results)
    if not transaction:
      res.version_list().extend(result[1] for result in results)

  def _Dynamic_Delete(self, req, res):
    transaction = req.has_transaction() and req.transaction() or None
    versions = self._datastore.Delete(req.key_list(), res.mutable_cost(),
                                      transaction, self._trusted, self._app_id)
    if not transaction:
      res.version_list().extend(versions)

  def _Dynamic_Touch(self, req, _):
    self._datastore.Touch(req.key_list(), self._trusted, self._app_id)

  @_NeedsIndexes
  def _Dynamic_RunQuery(self, query, query_result):
    cursor = self._datastore.GetQueryCursor(query, self._trusted, self._app_id)

    count = query.count() if query.has_count() else None
    cursor.PopulateQueryResult(query_result, count, query.offset(),
                               query.compile(), first_result=True)
    if query_result.has_cursor():
      self._query_cursors[query_result.cursor().cursor()] = cursor


    if query.compile():


      compiled_query = query_result.mutable_compiled_query()
      compiled_query.set_keys_only(query.keys_only())
      compiled_query.mutable_primaryscan().set_index_name(query.Encode())
    self.__UpdateQueryHistory(query)

  def __UpdateQueryHistory(self, query):

    clone = datastore_pb.Query()
    clone.CopyFrom(query)
    clone.clear_hint()
    clone.clear_limit()
    clone.clear_offset()
    clone.clear_count()
    if clone in self.__query_history:
      self.__query_history[clone] += 1
    else:
      self.__query_history[clone] = 1
      if clone.app() == self._app_id:
        self.__query_ci_history.add(
            datastore_index.CompositeIndexForQuery(clone))

  def _Dynamic_Next(self, next_request, query_result):
    app = next_request.cursor().app()
    CheckAppId(self._trusted, self._app_id, app)

    cursor = self._query_cursors.get(next_request.cursor().cursor())
    Check(cursor and cursor.app == app,
          'Cursor %d not found' % next_request.cursor().cursor())

    count = next_request.count() if next_request.has_count() else None
    offset = next_request.offset() if next_request.has_offset() else None
    cursor.PopulateQueryResult(query_result,
                               count,
                               offset,
                               next_request.compile(),
                               first_result=False)

    if not query_result.has_cursor():
      del self._query_cursors[next_request.cursor().cursor()]

  def _Dynamic_AddActions(self, request, _):
    """Associates the creation of one or more tasks with a transaction.

    Args:
      request: A taskqueue_service_pb.TaskQueueBulkAddRequest containing the
        tasks that should be created when the transaction is committed.
    """




    if not request.add_request_list():
      return

    first_add_request = request.add_request_list()[0]
    datastore_transaction = None
    if first_add_request.has_datastore_transaction():
      datastore_transaction = first_add_request.datastore_transaction()
      transaction = datastore_pb.Transaction()
      get_service_converter().v1_to_v3_txn(datastore_transaction, transaction)
    else:
      transaction = first_add_request.transaction()
    txn = self._datastore.GetTxn(transaction, self._trusted, self._app_id)
    new_actions = []
    for add_request in request.add_request_list():



      Check(datastore_transaction is not None
            and add_request.datastore_transaction() == datastore_transaction
            or add_request.transaction() == transaction,
            'Cannot add requests to different transactions')
      clone = taskqueue_service_pb.TaskQueueAddRequest()
      clone.CopyFrom(add_request)
      clone.clear_transaction()
      clone.clear_datastore_transaction()
      new_actions.append(clone)

    txn.AddActions(new_actions, self._MAX_ACTIONS_PER_TXN)

  def _Dynamic_BeginTransaction(self, req, transaction):
    CheckAppId(self._trusted, self._app_id, req.app())
    transaction.CopyFrom(self._datastore.BeginTransaction(
        req.app(), req.allow_multiple_eg()))

  def _Dynamic_Commit(self, transaction, res):
    CheckAppId(self._trusted, self._app_id, transaction.app())
    txn = self._datastore.GetTxn(transaction, self._trusted, self._app_id)
    res.mutable_cost().CopyFrom(txn.Commit())
    for reference in txn._mutated_references:
      commit_version = res.add_version()
      commit_version.mutable_root_entity_key().CopyFrom(reference)
      commit_version.set_version(txn.GetMutationVersion(reference))

  def _Dynamic_Rollback(self, transaction, _):
    CheckAppId(self._trusted, self._app_id, transaction.app())
    txn = self._datastore.GetTxn(transaction, self._trusted, self._app_id)
    txn.Rollback()

  def _Dynamic_CreateIndex(self, index, id_response):
    id_response.set_value(self._datastore.CreateIndex(index,
                                                      self._trusted,
                                                      self._app_id))

  @_NeedsIndexes
  def _Dynamic_GetIndices(self, get_indicies_request, composite_indices):
    composite_indices.index_list().extend(self._datastore.GetIndexes(
        get_indicies_request.app_id(), self._trusted, self._app_id))

  def _Dynamic_UpdateIndex(self, index, _):
    self._datastore.UpdateIndex(index, self._trusted, self._app_id)

  def _Dynamic_DeleteIndex(self, index, _):
    self._datastore.DeleteIndex(index, self._trusted, self._app_id)

  def _Dynamic_AllocateIds(self, allocate_ids_request, allocate_ids_response):
    Check(not allocate_ids_request.has_model_key()
          or not allocate_ids_request.reserve_list(),
          'Cannot allocate and reserve IDs in the same request')
    if allocate_ids_request.reserve_list():
      Check(not allocate_ids_request.has_size(),
            'Cannot specify size when reserving IDs')
      Check(not allocate_ids_request.has_max(),
            'Cannot specify max when reserving IDs')

    if allocate_ids_request.has_model_key():
      CheckAppId(allocate_ids_request.model_key().app(),
                 self._trusted, self._app_id)

      reference = allocate_ids_request.model_key()

      (start, end) = self._datastore._AllocateSequentialIds(
          reference, allocate_ids_request.size(), allocate_ids_request.max())

      allocate_ids_response.set_start(start)
      allocate_ids_response.set_end(end)
    else:
      for reference in allocate_ids_request.reserve_list():
        CheckAppId(reference.app(), self._trusted, self._app_id)
      self._datastore._AllocateIds(allocate_ids_request.reserve_list())
      allocate_ids_response.set_start(0)
      allocate_ids_response.set_end(0)

  def _SetupIndexes(self, _open=open):
    """Ensure that the set of existing composite indexes matches index.yaml.

    Note: this is similar to the algorithm used by the admin console for
    the same purpose.
    """



    if not self._root_path:
      return
    file_names = [os.path.join(self._root_path, 'index.yaml')]
    file_mtimes = [os.path.getmtime(f) for f in file_names if os.path.exists(f)]
    if (self._cached_index_definitions.file_names == file_names and
        all(os.path.exists(f) for f in file_names) and
        self._cached_index_definitions.last_modifieds == file_mtimes):
      requested_indexes = self._cached_index_definitions.index_protos
    else:
      file_mtimes = []
      index_texts = []
      for file_name in file_names:
        try:
          file_mtimes.append(os.path.getmtime(file_name))
          with _open(file_name, 'r') as fh:
            index_texts.append(fh.read())
        except (OSError, IOError):
          pass

      requested_indexes = []
      if len(index_texts) == len(file_names):
        all_ok = True
        for index_text in index_texts:

          index_defs = datastore_index.ParseIndexDefinitions(index_text)
          if index_defs is None or index_defs.indexes is None:
            all_ok = False
          else:

            requested_indexes.extend(
                datastore_index.IndexDefinitionsToProtos(
                    self._app_id, index_defs.indexes))
        if all_ok:
          self._cached_index_definitions = _CachedIndexDefinitions(
              file_names, file_mtimes, requested_indexes)


    existing_indexes = self._datastore.GetIndexes(
        self._app_id, self._trusted, self._app_id)


    requested = dict((x.definition().Encode(), x) for x in requested_indexes)
    existing = dict((x.definition().Encode(), x) for x in existing_indexes)


    created = 0
    for key, index in requested.iteritems():
      if key not in existing:
        new_index = entity_pb.CompositeIndex()
        new_index.CopyFrom(index)
        new_index.set_id(datastore_admin.CreateIndex(new_index))
        new_index.set_state(entity_pb.CompositeIndex.READ_WRITE)
        datastore_admin.UpdateIndex(new_index)
        created += 1


    deleted = 0
    for key, index in existing.iteritems():
      if key not in requested:
        datastore_admin.DeleteIndex(index)
        deleted += 1


    if created or deleted:
      logging.debug('Created %d and deleted %d index(es); total %d',
                    created, deleted, len(requested))

  def _UpdateIndexes(self):
    if self._index_config_updater is not None:
      self._index_config_updater.UpdateIndexConfig()


class StubQueryConverter(datastore_pbs._QueryConverter):
  """Converter for v3, v4 and v1 queries suitable for use in stubs."""

  def __init__(self, entity_converter):
    super(StubQueryConverter, self).__init__(entity_converter)

  def v4_to_v3_compiled_cursor(self, v4_cursor, v3_compiled_cursor):
    """Converts a v4 cursor string to a v3 CompiledCursor.

    Args:
      v4_cursor: a string representing a v4 query cursor
      v3_compiled_cursor: a datastore_pb.CompiledCursor to populate
    """
    v3_compiled_cursor.Clear()
    try:
      v3_compiled_cursor.ParseFromString(v4_cursor)
    except ProtocolBuffer.ProtocolBufferDecodeError:
      raise datastore_pbs.InvalidConversionError('Invalid query cursor.')

  def v3_to_v4_compiled_cursor(self, v3_compiled_cursor):
    """Converts a v3 CompiledCursor to a v4 cursor string.

    Args:
      v3_compiled_cursor: a datastore_pb.CompiledCursor

    Returns:
      a string representing a v4 query cursor
    """
    return v3_compiled_cursor.SerializeToString()

  def v4_to_v3_query(self, v4_partition_id, v4_query, v3_query):
    """Converts a v4 Query to a v3 Query.

    Args:
      v4_partition_id: a datastore_v4_pb.PartitionId
      v4_query: a datastore_v4_pb.Query
      v3_query: a datastore_pb.Query to populate

    Raises:
      InvalidConversionError if the query cannot be converted
    """
    v3_query.Clear()

    if v4_partition_id.dataset_id():
      v3_query.set_app(v4_partition_id.dataset_id())
    if v4_partition_id.has_namespace():
      v3_query.set_name_space(v4_partition_id.namespace())

    v3_query.set_persist_offset(True)
    v3_query.set_require_perfect_plan(True)
    v3_query.set_compile(True)


    if v4_query.has_limit():
      v3_query.set_limit(v4_query.limit())
    if v4_query.offset():
      v3_query.set_offset(v4_query.offset())
    if v4_query.has_start_cursor():
      self.v4_to_v3_compiled_cursor(v4_query.start_cursor(),
                                    v3_query.mutable_compiled_cursor())
    if v4_query.has_end_cursor():
      self.v4_to_v3_compiled_cursor(v4_query.end_cursor(),
                                    v3_query.mutable_end_compiled_cursor())


    if v4_query.kind_list():
      datastore_pbs.check_conversion(len(v4_query.kind_list()) == 1,
                                     'multiple kinds not supported')
      v3_query.set_kind(v4_query.kind(0).name())


    has_key_projection = False
    for prop in v4_query.projection_list():
      if prop.property().name() == datastore_pbs.PROPERTY_NAME_KEY:
        has_key_projection = True
      else:
        v3_query.add_property_name(prop.property().name())
    if has_key_projection and not v3_query.property_name_list():
      v3_query.set_keys_only(True)


    for prop in v4_query.group_by_list():
      v3_query.add_group_by_property_name(prop.name())


    self.__populate_v3_filters_from_v4(v4_query.filter(), v3_query)


    for v4_order in v4_query.order_list():
      v3_order = v3_query.add_order()
      v3_order.set_property(v4_order.property().name())
      if v4_order.has_direction():
        v3_order.set_direction(v4_order.direction())

  def v3_to_v4_query(self, v3_query, v4_query):
    """Converts a v3 Query to a v4 Query.

    Args:
      v3_query: a datastore_pb.Query
      v4_query: a datastore_v4_pb.Query to populate

    Raises:
      InvalidConversionError if the query cannot be converted
    """
    v4_query.Clear()

    datastore_pbs.check_conversion(not v3_query.has_distinct(),
                                   'distinct option not supported')
    datastore_pbs.check_conversion(v3_query.require_perfect_plan(),
                                   'non-perfect plans not supported')



    if v3_query.has_limit():
      v4_query.set_limit(v3_query.limit())
    if v3_query.offset():
      v4_query.set_offset(v3_query.offset())
    if v3_query.has_compiled_cursor():
      v4_query.set_start_cursor(
          self.v3_to_v4_compiled_cursor(v3_query.compiled_cursor()))
    if v3_query.has_end_compiled_cursor():
      v4_query.set_end_cursor(
          self.v3_to_v4_compiled_cursor(v3_query.end_compiled_cursor()))


    if v3_query.has_kind():
      v4_query.add_kind().set_name(v3_query.kind())


    for name in v3_query.property_name_list():
      v4_query.add_projection().mutable_property().set_name(name)
    if v3_query.keys_only():
      v4_query.add_projection().mutable_property().set_name(
          datastore_pbs.PROPERTY_NAME_KEY)


    for name in v3_query.group_by_property_name_list():
      v4_query.add_group_by().set_name(name)


    num_v4_filters = len(v3_query.filter_list())
    if v3_query.has_ancestor():
      num_v4_filters += 1

    if num_v4_filters == 1:
      get_property_filter = self.__get_property_filter_from_v4
    elif num_v4_filters >= 1:
      v4_query.mutable_filter().mutable_composite_filter().set_operator(
          datastore_v4_pb.CompositeFilter.AND)
      get_property_filter = self.__add_property_filter_from_v4

    if v3_query.has_ancestor():
      self._v3_query_to_v4_ancestor_filter(v3_query,
                                           get_property_filter(v4_query))
    for v3_filter in v3_query.filter_list():
      self._v3_filter_to_v4_property_filter(v3_filter,
                                            get_property_filter(v4_query))


    for v3_order in v3_query.order_list():
      self.v3_order_to_v4_order(v3_order, v4_query.add_order())

  def __get_property_filter_from_v4(self, v4_query):
    """Returns the PropertyFilter from the query's top-level filter."""
    return v4_query.mutable_filter().mutable_property_filter()

  def __add_property_filter_from_v4(self, v4_query):
    """Adds and returns a PropertyFilter from the query's composite filter."""
    v4_comp_filter = v4_query.mutable_filter().mutable_composite_filter()
    return v4_comp_filter.add_filter().mutable_property_filter()

  def __populate_v3_filters_from_v4(self, v4_filter, v3_query):
    """Populates a filters for a v3 Query.

    Args:
      v4_filter: a datastore_v4_pb.Filter
      v3_query: a datastore_pb.Query to populate with filters
    """
    if v4_filter.has_property_filter():
      v4_property_filter = v4_filter.property_filter()
      if (v4_property_filter.operator()
          == datastore_v4_pb.PropertyFilter.HAS_ANCESTOR):
        datastore_pbs.check_conversion(
            v4_property_filter.value().has_key_value(),
            'HAS_ANCESTOR requires a reference value')
        datastore_pbs.check_conversion((v4_property_filter.property().name()
                                        == datastore_pbs.PROPERTY_NAME_KEY),
                                       'unsupported property')
        datastore_pbs.check_conversion(not v3_query.has_ancestor(),
                                       'duplicate ancestor constraint')
        self._entity_converter.v4_to_v3_reference(
            v4_property_filter.value().key_value(),
            v3_query.mutable_ancestor())
      else:
        v3_filter = v3_query.add_filter()
        property_name = v4_property_filter.property().name()
        v3_filter.set_op(v4_property_filter.operator())
        datastore_pbs.check_conversion(
            not v4_property_filter.value().list_value_list(),
            ('unsupported value type, %s, in property filter'
             ' on "%s"' % ('list_value', property_name)))
        self._entity_converter.v4_to_v3_property(property_name,
                                                 False,
                                                 False,
                                                 v4_property_filter.value(),
                                                 v3_filter.add_property())
    elif v4_filter.has_composite_filter():
      datastore_pbs.check_conversion((v4_filter.composite_filter().operator()
                                      == datastore_v4_pb.CompositeFilter.AND),
                                     'unsupported composite property operator')
      for v4_sub_filter in v4_filter.composite_filter().filter_list():
        self.__populate_v3_filters_from_v4(v4_sub_filter, v3_query)

  def v1_to_v3_compiled_cursor(self, v1_cursor, v3_compiled_cursor):
    """Converts a v1 cursor string to a v3 CompiledCursor.

    Args:
      v1_cursor: a string representing a v1 query cursor
      v3_compiled_cursor: a datastore_pb.CompiledCursor to populate
    """
    v3_compiled_cursor.Clear()
    try:
      v3_compiled_cursor.ParseFromString(v1_cursor)
    except ProtocolBuffer.ProtocolBufferDecodeError:
      raise datastore_pbs.InvalidConversionError('Invalid query cursor.')

  def v3_to_v1_compiled_cursor(self, v3_compiled_cursor):
    """Converts a v3 CompiledCursor to a v1 cursor string.

    Args:
      v3_compiled_cursor: a datastore_pb.CompiledCursor

    Returns:
      a string representing a v1 query cursor
    """
    return v3_compiled_cursor.SerializeToString()

  def v1_to_v3_query(self, v1_partition_id, v1_query, v3_query):
    """Converts a v1 Query to a v3 Query.

    Args:
      v1_partition_id: a googledatastore.PartitionId
      v1_query: a googledatastore.Query
      v3_query: a datastore_pb.Query to populate

    Raises:
      InvalidConversionError if the query cannot be converted
    """
    v3_query.Clear()

    if v1_partition_id.project_id:
      v3_query.set_app(v1_partition_id.project_id)
    if v1_partition_id.namespace_id:
      v3_query.set_name_space(v1_partition_id.namespace_id)

    v3_query.set_persist_offset(True)
    v3_query.set_require_perfect_plan(True)
    v3_query.set_compile(True)


    if v1_query.HasField('limit'):
      v3_query.set_limit(v1_query.limit.value)
    if v1_query.offset:
      v3_query.set_offset(v1_query.offset)
    if v1_query.start_cursor:
      self.v1_to_v3_compiled_cursor(v1_query.start_cursor,
                                    v3_query.mutable_compiled_cursor())
    if v1_query.end_cursor:
      self.v1_to_v3_compiled_cursor(v1_query.end_cursor,
                                    v3_query.mutable_end_compiled_cursor())


    if v1_query.kind:
      datastore_pbs.check_conversion(len(v1_query.kind) == 1,
                                     'multiple kinds not supported')
      v3_query.set_kind(v1_query.kind[0].name.encode('utf-8['))


    has_key_projection = False
    for prop in v1_query.projection:
      if prop.property.name == datastore_pbs.PROPERTY_NAME_KEY:
        has_key_projection = True
      else:
        v3_query.add_property_name(prop.property.name)
    if has_key_projection and not v3_query.property_name_size():
      v3_query.set_keys_only(True)


    for prop in v1_query.distinct_on:
      v3_query.add_group_by_property_name(prop.name)


    self.__populate_v3_filters_from_v1(v1_query.filter, v3_query)


    for v1_order in v1_query.order:
      v3_order = v3_query.add_order()
      v3_order.set_property(v1_order.property.name)
      if v1_order.direction:
        v3_order.set_direction(v1_order.direction)

  def v3_to_v1_query(self, v3_query, v1_query):
    """Converts a v3 Query to a v1 Query.

    Args:
      v3_query: a datastore_pb.Query
      v1_query: a googledatastore.Query to populate

    Raises:
      InvalidConversionError if the query cannot be converted
    """
    v1_query.Clear()

    datastore_pbs.check_conversion(not v3_query.has_distinct(),
                                   'distinct option not supported')
    datastore_pbs.check_conversion(v3_query.require_perfect_plan(),
                                   'non-perfect plans not supported')



    if v3_query.has_limit():
      v1_query.limit.value = v3_query.limit()
    if v3_query.offset():
      v1_query.offset = v3_query.offset()
    if v3_query.has_compiled_cursor():
      v1_query.start_cursor = (
          self.v3_to_v1_compiled_cursor(v3_query.compiled_cursor()))
    if v3_query.has_end_compiled_cursor():
      v1_query.end_cursor = (
          self.v3_to_v1_compiled_cursor(v3_query.end_compiled_cursor()))


    if v3_query.has_kind():
      v1_query.kind.add().name = v3_query.kind()


    for name in v3_query.property_name_list():
      v1_query.projection.add().property.name = name
    if v3_query.keys_only():
      v1_query.projection.add().property.name = (
          datastore_pbs.PROPERTY_NAME_KEY)


    for name in v3_query.group_by_property_name_list():
      v1_query.distinct_on.add().name = name


    num_v1_filters = len(v3_query.filter_list())
    if v3_query.has_ancestor():
      num_v1_filters += 1

    if num_v1_filters == 1:
      get_property_filter = self.__get_property_filter_from_v1
    elif num_v1_filters >= 1:
      v1_query.filter.composite_filter.operator = (
          googledatastore.CompositeFilter.AND)
      get_property_filter = self.__add_property_filter_from_V1

    if v3_query.has_ancestor():
      self._v3_query_to_v1_ancestor_filter(v3_query,
                                           get_property_filter(v1_query))
    for v3_filter in v3_query.filter_list():
      self._v3_filter_to_v1_property_filter(v3_filter,
                                            get_property_filter(v1_query))


    for v3_order in v3_query.order_list():
      self.v3_order_to_v1_order(v3_order, v1_query.order.add())

  def __get_property_filter_from_v1(self, v1_query):
    """Returns the PropertyFilter from the query's top-level filter."""
    return v1_query.filter.add().property_filter

  def __add_property_filter_from_v1(self, v1_query):
    """Adds and returns a PropertyFilter from the query's composite filter."""
    v1_comp_filter = v1_query.filter.composite_filter
    return v1_comp_filter.filter.add().property_filter

  def __populate_v3_filters_from_v1(self, v1_filter, v3_query):
    """Populates a filters for a v3 Query.

    Args:
      v1_filter: a googledatastore.Filter
      v3_query: a datastore_pb.Query to populate with filters
    """
    filter_type = v1_filter.WhichOneof('filter_type')
    if filter_type == 'property_filter':
      v1_property_filter = v1_filter.property_filter
      v1_property_name = v1_property_filter.property.name
      if (v1_property_filter.op
          == googledatastore.PropertyFilter.HAS_ANCESTOR):
        datastore_pbs.check_conversion(
            v1_property_filter.value.HasField('key_value'),
            'HAS_ANCESTOR requires a reference value')
        datastore_pbs.check_conversion((v1_property_name
                                        == datastore_pbs.PROPERTY_NAME_KEY),
                                       'unsupported property')
        datastore_pbs.check_conversion(not v3_query.has_ancestor(),
                                       'duplicate ancestor constraint')
        self._entity_converter.v1_to_v3_reference(
            v1_property_filter.value.key_value,
            v3_query.mutable_ancestor())
      else:
        v3_filter = v3_query.add_filter()
        property_name = v1_property_name
        v3_filter.set_op(v1_property_filter.op)
        datastore_pbs.check_conversion(
            not v1_property_filter.value.HasField('array_value'),
            ('unsupported value type, %s, in property filter'
             ' on "%s"' % ('array_value', property_name)))
        self._entity_converter.v1_to_v3_property(property_name,
                                                 False,
                                                 False,
                                                 v1_property_filter.value,
                                                 v3_filter.add_property())
    elif filter_type == 'composite_filter':
      datastore_pbs.check_conversion((v1_filter.composite_filter.op
                                      == googledatastore.CompositeFilter.AND),
                                     'unsupported composite property operator')
      for v1_sub_filter in v1_filter.composite_filter.filters:
        self.__populate_v3_filters_from_v1(v1_sub_filter, v3_query)


def get_query_converter(id_resolver=None):
  """Returns a converter for v3 and v1 queries (not suitable for production).

  This converter is suitable for use in stubs but not for production.

  Returns:
    a StubQueryConverter
  """
  return StubQueryConverter(datastore_pbs.get_entity_converter(id_resolver))


class StubServiceConverter(object):
  """Converter for v3/v4/v1 request/response protos suitable for use in stubs.
  """

  def __init__(self, entity_converter, query_converter):
    self._entity_converter = entity_converter
    self._query_converter = query_converter

  def v1_to_v3_cursor(self, v1_query_handle, v3_cursor):
    """Converts a v1 cursor string to a v3 Cursor.

    Args:
      v1_query_handle: a string representing a v1 query handle
      v3_cursor: a datastore_pb.Cursor to populate
    """
    try:
      v3_cursor.ParseFromString(v1_query_handle)
    except ProtocolBuffer.ProtocolBufferDecodeError:
      raise datastore_pbs.InvalidConversionError('Invalid query handle.')
    return v3_cursor

  def _v3_to_v1_query_handle(self, v3_cursor):
    """Converts a v3 Cursor to a v1 query handle string.

    Args:
      v3_cursor: a datastore_pb.Cursor

    Returns:
      a string representing a v1 cursor
    """
    return v3_cursor.SerializeToString()

  def v1_to_v3_txn(self, v1_txn, v3_txn):
    """Converts a v1 transaction string to a v3 Transaction.

    Args:
      v1_txn: a string representing a v1 transaction
      v3_txn: a datastore_pb.Transaction to populate
    """
    try:
      v3_txn.ParseFromString(v1_txn)
    except ProtocolBuffer.ProtocolBufferDecodeError:
      raise datastore_pbs.InvalidConversionError('Invalid transaction.')
    return v3_txn

  def _v3_to_v1_txn(self, v3_txn):
    """Converts a v3 Transaction to a v1 transaction string.

    Args:
      v3_txn: a datastore_pb.Transaction

    Returns:
      a string representing a v1 transaction
    """
    return v3_txn.SerializeToString()




  def v1_to_v3_begin_transaction_req(self, app_id, v1_req):
    """Converts a v1 BeginTransactionRequest to a v3 BeginTransactionRequest.

    Args:
      app_id: app id
      v1_req: a googledatastore.BeginTransactionRequest

    Returns:
      a datastore_pb.BeginTransactionRequest
    """
    v3_req = datastore_pb.BeginTransactionRequest()
    v3_req.set_app(app_id)
    v3_req.set_allow_multiple_eg(True)
    return v3_req

  def v3_to_v1_begin_transaction_resp(self, v3_resp):
    """Converts a v3 Transaction to a v1 BeginTransactionResponse.

    Args:
      v3_resp: a datastore_pb.Transaction

    Returns:
      a googledatastore.BeginTransactionResponse
    """
    v1_resp = googledatastore.BeginTransactionResponse()
    v1_resp.transaction = self._v3_to_v1_txn(v3_resp)
    return v1_resp




  def v1_rollback_req_to_v3_txn(self, v1_req):
    """Converts a v1 RollbackRequest to a v3 Transaction.

    Args:
      v1_req: a googledatastore.RollbackRequest

    Returns:
      a datastore_pb.Transaction
    """
    v3_txn = datastore_pb.Transaction()
    self.v1_to_v3_txn(v1_req.transaction, v3_txn)
    return v3_txn




  def v1_commit_req_to_v3_txn(self, v1_req):
    """Converts a v1 CommitRequest to a v3 Transaction.

    Args:
      v1_req: a googledatastore.CommitRequest

    Returns:
      a datastore_pb.Transaction
    """
    v3_txn = datastore_pb.Transaction()
    self.v1_to_v3_txn(v1_req.transaction, v3_txn)
    return v3_txn




  def v1_run_query_req_to_v3_query(self, v1_req, new_txn=None):
    """Converts a v1 RunQueryRequest to a v3 Query.

    GQL is not supported.

    Args:
      v1_req: a googledatastore.RunQueryRequest
      new_txn: a v1 transaction created ad-hoc for this query, or None.

    Returns:
      a datastore_pb.Query
    """
    consistency_type = v1_req.read_options.WhichOneof('consistency_type')

    datastore_pbs.check_conversion(not v1_req.HasField('gql_query'),
                                   'GQL not supported')
    if (new_txn is None) == (consistency_type == 'new_transaction'):
      raise datastore_errors.InternalError('new_txn should be set only if the '
                                           'consistency type is '
                                           'new_transaction')

    v3_query = datastore_pb.Query()
    self._query_converter.v1_to_v3_query(v1_req.partition_id, v1_req.query,
                                         v3_query)


    if consistency_type == 'transaction':
      self.v1_to_v3_txn(v1_req.read_options.transaction,
                        v3_query.mutable_transaction())
    elif consistency_type == 'new_transaction':
      self.v1_to_v3_txn(new_txn, v3_query.mutable_transaction())
    elif consistency_type == 'read_consistency':
      read_consistency = v1_req.read_options.read_consistency
      if read_consistency == googledatastore.ReadOptions.EVENTUAL:
        v3_query.set_strong(False)
        v3_query.set_failover_ms(-1)
      elif read_consistency == googledatastore.ReadOptions.STRONG:
        v3_query.set_strong(True)
      elif (read_consistency !=
            googledatastore.ReadOptions.READ_CONSISTENCY_UNSPECIFIED):
        raise datastore_errors.InternalError('Unknown read_consistency %d'
                                             % read_consistency)
    elif consistency_type is not None:
      raise datastore_errors.InternalError('Unknown consistency_type: %s'
                                           % consistency_type)

    return v3_query

  def v3_to_v1_run_query_req(self, v3_req):
    """Converts a v3 Query to a v1 RunQueryRequest.

    Args:
      v3_req: a datastore_pb.Query

    Returns:
      a googledatastore.RunQueryRequest
    """
    v1_req = googledatastore.RunQueryRequest()


    v1_partition_id = v1_req.partition_id
    v1_partition_id.project_id = v3_req.app()
    if v3_req.name_space():
      v1_partition_id.namespace = v3_req.name_space()


    if v3_req.has_transaction():
      v1_req.read_options.transaction = self._v3_to_v1_txn(v3_req.transaction())
    elif v3_req.strong():
      v1_req.read_options.read_consistency = (
          googledatastore.ReadOptions.STRONG)
    elif v3_req.has_strong():
      v1_req.read_options.read_consistency = (
          googledatastore.ReadOptions.EVENTUAL)

    self._query_converter.v3_to_v1_query(v3_req, v1_req.mutable_query())

    return v1_req

  def v1_run_query_resp_to_v3_query_result(self, v1_resp):
    """Converts a V4 RunQueryResponse to a v3 QueryResult.

    Args:
      v1_resp: a googledatastore.QueryResult

    Returns:
      a datastore_pb.QueryResult
    """
    v3_resp = self.v1_to_v3_query_result(v1_resp.batch)

    return v3_resp

  def v3_to_v1_run_query_resp(self, v3_resp, new_txn=None):
    """Converts a v3 QueryResult to a V4 RunQueryResponse.

    Args:
      v3_resp: a datastore_pb.QueryResult
      new_txn: optional, a transaction that was created when processing the
        RunQueryRequest.

    Returns:
      a googledatastore.RunQueryResponse
    """
    v1_resp = googledatastore.RunQueryResponse()
    self.v3_to_v1_query_result_batch(v3_resp, v1_resp.batch)
    if new_txn:
      v1_resp.transaction = new_txn

    return v1_resp




  def v1_to_v3_get_req(self, v1_req, new_txn=None):
    """Converts a v1 LookupRequest to a v3 GetRequest.

    Args:
      v1_req: a googledatastore.LookupRequest
      new_txn: a v1 transaction created ad-hoc for this lookup, or None.

    Returns:
      a datastore_pb.GetRequest
    """
    consistency_type = v1_req.read_options.WhichOneof('consistency_type')
    if (new_txn is None) == (consistency_type == 'new_transaction'):
      raise datastore_errors.InternalError('new_txn should be set only if the '
                                           'consistency type is '
                                           'new_transaction')

    v3_req = datastore_pb.GetRequest()
    v3_req.set_allow_deferred(True)


    if consistency_type == 'transaction':
      self.v1_to_v3_txn(v1_req.read_options.transaction,
                        v3_req.mutable_transaction())
    elif consistency_type == 'new_transaction':
      self.v1_to_v3_txn(new_txn, v3_req.mutable_transaction())
    elif consistency_type == 'read_consistency':
      read_consistency = v1_req.read_options.read_consistency
      if read_consistency == googledatastore.ReadOptions.EVENTUAL:
        v3_req.set_strong(False)
        v3_req.set_failover_ms(-1)
      elif read_consistency == googledatastore.ReadOptions.STRONG:
        v3_req.set_strong(True)
      elif (read_consistency !=
            googledatastore.ReadOptions.READ_CONSISTENCY_UNSPECIFIED):
        raise datastore_errors.InternalError('Unknown read_consistency %d'
                                             % read_consistency)
    elif consistency_type is not None:
      raise datastore_errors.InternalError('Unknown consistency_type: %s'
                                           % consistency_type)

    for v1_key in v1_req.keys:
      self._entity_converter.v1_to_v3_reference(v1_key, v3_req.add_key())

    return v3_req

  def v3_to_v1_lookup_resp(self, v3_resp, new_txn=None):
    """Converts a v3 GetResponse to a v1 LookupResponse.

    Args:
      v3_resp: a datastore_pb.GetResponse
      new_txn: a v1 transaction created ad-hoc for this lookup, or None.

    Returns:
      a googledatastore.LookupResponse
    """
    v1_resp = googledatastore.LookupResponse()
    if new_txn:
      v1_resp.transaction = new_txn

    for v3_ref in v3_resp.deferred_list():
      self._entity_converter.v3_to_v1_key(v3_ref, v1_resp.deferred.add())
    for v3_entity in v3_resp.entity_list():
      if v3_entity.has_entity():
        v1_entity_result = v1_resp.found.add()
        self._entity_converter.v3_to_v1_entity(
            v3_entity.entity(), v1_entity_result.entity)
      if v3_entity.has_key():
        v1_entity_result = v1_resp.missing.add()
        self._entity_converter.v3_to_v1_key(
            v3_entity.key(), v1_entity_result.entity.key)
      if v3_entity.has_version():
        v1_entity_result.version = v3_entity.version()

    return v1_resp

  def v1_to_v3_query_result(self, v1_batch):
    """Converts a v1 QueryResultBatch to a v3 QueryResult.

    Args:
      v1_batch: a googledatastore.QueryResultBatch

    Returns:
      a datastore_pb.QueryResult
    """
    v3_result = datastore_pb.QueryResult()


    v3_result.set_more_results(
        (v1_batch.more_results
         == googledatastore.QueryResultBatch.NOT_FINISHED))
    if v1_batch.end_cursor:
      self._query_converter.v1_to_v3_compiled_cursor(
          v1_batch.end_cursor, v3_result.mutable_compiled_cursor())
    if v1_batch.skipped_cursor:
      self._query_converter.v1_to_v3_compiled_cursor(
          v1_batch.skipped_cursor,
          v3_result.mutable_skipped_results_compiled_cursor())


    if v1_batch.entity_result_type() == googledatastore.EntityResult.PROJECTION:
      v3_result.set_index_only(True)
    elif v1_batch.entity_result_type() == googledatastore.EntityResult.KEY_ONLY:
      v3_result.set_keys_only(True)


    if v1_batch.skipped_results:
      v3_result.set_skipped_results(v1_batch.skipped_results)
    for v1_entity_result in v1_batch.entity_result:
      v3_entity = v3_result.add_result()
      self._entity_converter.v1_to_v3_entity(v1_entity_result.entity, v3_entity)
      if v1_entity_result.cursor:
        cursor = v3_result.add_result_compiled_cursor()
        self._query_converter.v1_to_v3_compiled_cursor(v1_entity_result.cursor,
                                                       cursor)
      if v1_batch.entity_result_type != googledatastore.EntityResult.FULL:


        v3_entity.clear_entity_group()

    return v3_result

  def v3_to_v1_query_result_batch(self, v3_result, v1_batch):
    """Converts a v3 QueryResult to a v1 QueryResultBatch.

    Args:
      v3_result: a datastore_pb.QueryResult
      v1_batch: a googledatastore.QueryResultBatch to populate
    """
    v1_batch.Clear()


    if v3_result.more_results():
      v1_batch.more_results = googledatastore.QueryResultBatch.NOT_FINISHED
    else:
      v1_batch.more_results = (
          googledatastore.QueryResultBatch.MORE_RESULTS_AFTER_LIMIT)
    if v3_result.has_compiled_cursor():
      v1_batch.end_cursor = (
          self._query_converter.v3_to_v1_compiled_cursor(
              v3_result.compiled_cursor()))
    if v3_result.has_skipped_results_compiled_cursor():
      v1_batch.skipped_cursor = (
          self._query_converter.v3_to_v1_compiled_cursor(
              v3_result.skipped_results_compiled_cursor()))


    if v3_result.keys_only():
      v1_batch.entity_result_type = googledatastore.EntityResult.KEY_ONLY
    elif v3_result.index_only():
      v1_batch.entity_result_type = googledatastore.EntityResult.PROJECTION
    else:
      v1_batch.entity_result_type = googledatastore.EntityResult.FULL


    if v3_result.has_skipped_results():
      v1_batch.skipped_results = v3_result.skipped_results()
    for v3_entity, v3_version, v3_cursor in itertools.izip_longest(
        v3_result.result_list(),
        v3_result.version_list(),
        v3_result.result_compiled_cursor_list()):
      v1_entity_result = v1_batch.entity_results.add()
      self._entity_converter.v3_to_v1_entity(v3_entity,
                                             v1_entity_result.entity)
      if v3_version is not None:
        v1_entity_result.version = v3_version
      if v3_cursor is not None:
        v1_entity_result.cursor = (
            self._query_converter.v3_to_v1_compiled_cursor(v3_cursor))

  def v4_to_v3_cursor(self, v4_query_handle, v3_cursor):
    """Converts a v4 cursor string to a v3 Cursor.

    Args:
      v4_query_handle: a string representing a v4 query handle
      v3_cursor: a datastore_pb.Cursor to populate
    """
    try:
      v3_cursor.ParseFromString(v4_query_handle)
    except ProtocolBuffer.ProtocolBufferDecodeError:
      raise datastore_pbs.InvalidConversionError('Invalid query handle.')
    return v3_cursor

  def _v3_to_v4_query_handle(self, v3_cursor):
    """Converts a v3 Cursor to a v4 query handle string.

    Args:
      v3_cursor: a datastore_pb.Cursor

    Returns:
      a string representing a v4 cursor
    """
    return v3_cursor.SerializeToString()

  def v4_to_v3_txn(self, v4_txn, v3_txn):
    """Converts a v4 transaction string to a v3 Transaction.

    Args:
      v4_txn: a string representing a v4 transaction
      v3_txn: a datastore_pb.Transaction to populate
    """
    try:
      v3_txn.ParseFromString(v4_txn)
    except ProtocolBuffer.ProtocolBufferDecodeError:
      raise datastore_pbs.InvalidConversionError('Invalid transaction.')
    return v3_txn

  def _v3_to_v4_txn(self, v3_txn):
    """Converts a v3 Transaction to a v4 transaction string.

    Args:
      v3_txn: a datastore_pb.Transaction

    Returns:
      a string representing a v4 transaction
    """
    return v3_txn.SerializeToString()




  def v4_to_v3_begin_transaction_req(self, app_id, v4_req):
    """Converts a v4 BeginTransactionRequest to a v3 BeginTransactionRequest.

    Args:
      app_id: app id
      v4_req: a datastore_v4_pb.BeginTransactionRequest

    Returns:
      a datastore_pb.BeginTransactionRequest
    """
    v3_req = datastore_pb.BeginTransactionRequest()
    v3_req.set_app(app_id)
    v3_req.set_allow_multiple_eg(v4_req.cross_group())
    return v3_req

  def v3_to_v4_begin_transaction_resp(self, v3_resp):
    """Converts a v3 Transaction to a v4 BeginTransactionResponse.

    Args:
      v3_resp: a datastore_pb.Transaction

    Returns:
      a datastore_v4_pb.BeginTransactionResponse
    """
    v4_resp = datastore_v4_pb.BeginTransactionResponse()
    v4_resp.set_transaction(self._v3_to_v4_txn(v3_resp))
    return v4_resp




  def v4_rollback_req_to_v3_txn(self, v4_req):
    """Converts a v4 RollbackRequest to a v3 Transaction.

    Args:
      v4_req: a datastore_v4_pb.RollbackRequest

    Returns:
      a datastore_pb.Transaction
    """
    v3_txn = datastore_pb.Transaction()
    self.v4_to_v3_txn(v4_req.transaction(), v3_txn)
    return v3_txn




  def v4_commit_req_to_v3_txn(self, v4_req):
    """Converts a v4 CommitRequest to a v3 Transaction.

    Args:
      v4_req: a datastore_v4_pb.CommitRequest

    Returns:
      a datastore_pb.Transaction
    """
    v3_txn = datastore_pb.Transaction()
    self.v4_to_v3_txn(v4_req.transaction(), v3_txn)
    return v3_txn




  def v4_run_query_req_to_v3_query(self, v4_req):
    """Converts a v4 RunQueryRequest to a v3 Query.

    GQL is not supported.

    Args:
      v4_req: a datastore_v4_pb.RunQueryRequest

    Returns:
      a datastore_pb.Query
    """

    datastore_pbs.check_conversion(not v4_req.has_gql_query(),
                                   'GQL not supported')
    v3_query = datastore_pb.Query()
    self._query_converter.v4_to_v3_query(v4_req.partition_id(), v4_req.query(),
                                         v3_query)


    if v4_req.has_suggested_batch_size():
      v3_query.set_count(v4_req.suggested_batch_size())


    read_options = v4_req.read_options()
    if read_options.has_transaction():
      self.v4_to_v3_txn(read_options.transaction(),
                        v3_query.mutable_transaction())
    elif (read_options.read_consistency()
          == datastore_v4_pb.ReadOptions.EVENTUAL):
      v3_query.set_strong(False)
      v3_query.set_failover_ms(-1)
    elif read_options.read_consistency() == datastore_v4_pb.ReadOptions.STRONG:
      v3_query.set_strong(True)

    if v4_req.has_min_safe_time_seconds():
      v3_query.set_min_safe_time_seconds(v4_req.min_safe_time_seconds())

    return v3_query

  def v3_to_v4_run_query_req(self, v3_req):
    """Converts a v3 Query to a v4 RunQueryRequest.

    Args:
      v3_req: a datastore_pb.Query

    Returns:
      a datastore_v4_pb.RunQueryRequest
    """
    v4_req = datastore_v4_pb.RunQueryRequest()


    v4_partition_id = v4_req.mutable_partition_id()
    v4_partition_id.set_dataset_id(v3_req.app())
    if v3_req.name_space():
      v4_partition_id.set_namespace(v3_req.name_space())


    if v3_req.has_count():
      v4_req.set_suggested_batch_size(v3_req.count())


    if v3_req.has_transaction():
      v4_req.mutable_read_options().set_transaction(
          self._v3_to_v4_txn(v3_req.transaction()))
    elif v3_req.strong():
      v4_req.mutable_read_options().set_read_consistency(
          datastore_v4_pb.ReadOptions.STRONG)
    elif v3_req.has_strong():
      v4_req.mutable_read_options().set_read_consistency(
          datastore_v4_pb.ReadOptions.EVENTUAL)
    if v3_req.has_min_safe_time_seconds():
      v4_req.set_min_safe_time_seconds(v3_req.min_safe_time_seconds())

    self._query_converter.v3_to_v4_query(v3_req, v4_req.mutable_query())

    return v4_req

  def v4_run_query_resp_to_v3_query_result(self, v4_resp):
    """Converts a V4 RunQueryResponse to a v3 QueryResult.

    Args:
      v4_resp: a datastore_v4_pb.QueryResult

    Returns:
      a datastore_pb.QueryResult
    """
    v3_resp = self.v4_to_v3_query_result(v4_resp.batch())


    if v4_resp.has_query_handle():
      self.v4_to_v3_cursor(v4_resp.query_handle(), v3_resp.mutable_cursor())

    return v3_resp

  def v3_to_v4_run_query_resp(self, v3_resp):
    """Converts a v3 QueryResult to a V4 RunQueryResponse.

    Args:
      v3_resp: a datastore_pb.QueryResult

    Returns:
      a datastore_v4_pb.RunQueryResponse
    """
    v4_resp = datastore_v4_pb.RunQueryResponse()
    self.v3_to_v4_query_result_batch(v3_resp, v4_resp.mutable_batch())

    if v3_resp.has_cursor():
      v4_resp.set_query_handle(
          self._query_converter.v3_to_v4_compiled_cursor(v3_resp.cursor()))

    return v4_resp




  def v4_to_v3_next_req(self, v4_req):
    """Converts a v4 ContinueQueryRequest to a v3 NextRequest.

    Args:
      v4_req: a datastore_v4_pb.ContinueQueryRequest

    Returns:
      a datastore_pb.NextRequest
    """
    v3_req = datastore_pb.NextRequest()
    v3_req.set_compile(True)
    self.v4_to_v3_cursor(v4_req.query_handle(), v3_req.mutable_cursor())
    return v3_req

  def v3_to_v4_continue_query_resp(self, v3_resp):
    """Converts a v3 QueryResult to a v4 ContinueQueryResponse.

    Args:
      v3_resp: a datstore_pb.QueryResult

    Returns:
      a datastore_v4_pb.ContinueQueryResponse
    """
    v4_resp = datastore_v4_pb.ContinueQueryResponse()
    self.v3_to_v4_query_result_batch(v3_resp, v4_resp.mutable_batch())
    return v4_resp




  def v4_to_v3_get_req(self, v4_req):
    """Converts a v4 LookupRequest to a v3 GetRequest.

    Args:
      v4_req: a datastore_v4_pb.LookupRequest

    Returns:
      a datastore_pb.GetRequest
    """
    v3_req = datastore_pb.GetRequest()
    v3_req.set_allow_deferred(True)


    if v4_req.read_options().has_transaction():
      self.v4_to_v3_txn(v4_req.read_options().transaction(),
                        v3_req.mutable_transaction())
    elif (v4_req.read_options().read_consistency()
          == datastore_v4_pb.ReadOptions.EVENTUAL):
      v3_req.set_strong(False)
      v3_req.set_failover_ms(-1)
    elif (v4_req.read_options().read_consistency()
          == datastore_v4_pb.ReadOptions.STRONG):
      v3_req.set_strong(True)

    for v4_key in v4_req.key_list():
      self._entity_converter.v4_to_v3_reference(v4_key, v3_req.add_key())

    return v3_req

  def v3_to_v4_lookup_resp(self, v3_resp):
    """Converts a v3 GetResponse to a v4 LookupResponse.

    Args:
      v3_resp: a datastore_pb.GetResponse

    Returns:
      a datastore_v4_pb.LookupResponse
    """
    v4_resp = datastore_v4_pb.LookupResponse()

    for v3_ref in v3_resp.deferred_list():
      self._entity_converter.v3_to_v4_key(v3_ref, v4_resp.add_deferred())
    for v3_entity in v3_resp.entity_list():
      if v3_entity.has_entity():
        self._entity_converter.v3_to_v4_entity(
            v3_entity.entity(),
            v4_resp.add_found().mutable_entity())
      if v3_entity.has_key():
        self._entity_converter.v3_to_v4_key(
            v3_entity.key(),
            v4_resp.add_missing().mutable_entity().mutable_key())

    return v4_resp

  def v4_to_v3_query_result(self, v4_batch):
    """Converts a v4 QueryResultBatch to a v3 QueryResult.

    Args:
      v4_batch: a datastore_v4_pb.QueryResultBatch

    Returns:
      a datastore_pb.QueryResult
    """
    v3_result = datastore_pb.QueryResult()


    v3_result.set_more_results(
        (v4_batch.more_results()
         == datastore_v4_pb.QueryResultBatch.NOT_FINISHED))
    if v4_batch.has_end_cursor():
      self._query_converter.v4_to_v3_compiled_cursor(
          v4_batch.end_cursor(), v3_result.mutable_compiled_cursor())
    if v4_batch.has_skipped_cursor():
      self._query_converter.v4_to_v3_compiled_cursor(
          v4_batch.skipped_cursor(),
          v3_result.mutable_skipped_results_compiled_cursor())


    if v4_batch.entity_result_type() == datastore_v4_pb.EntityResult.PROJECTION:
      v3_result.set_index_only(True)
    elif v4_batch.entity_result_type() == datastore_v4_pb.EntityResult.KEY_ONLY:
      v3_result.set_keys_only(True)


    if v4_batch.has_skipped_results():
      v3_result.set_skipped_results(v4_batch.skipped_results())
    for v4_entity in v4_batch.entity_result_list():
      v3_entity = v3_result.add_result()
      self._entity_converter.v4_to_v3_entity(v4_entity.entity(), v3_entity)
      if v4_entity.has_cursor():
        cursor = v3_result.add_result_compiled_cursor()
        self._query_converter.v4_to_v3_compiled_cursor(v4_entity.cursor(),
                                                       cursor)
      if v4_batch.entity_result_type() != datastore_v4_pb.EntityResult.FULL:


        v3_entity.clear_entity_group()

    return v3_result

  def v3_to_v4_query_result_batch(self, v3_result, v4_batch):
    """Converts a v3 QueryResult to a v4 QueryResultBatch.

    Args:
      v3_result: a datastore_pb.QueryResult
      v4_batch: a datastore_v4_pb.QueryResultBatch to populate
    """
    v4_batch.Clear()


    if v3_result.more_results():
      v4_batch.set_more_results(datastore_v4_pb.QueryResultBatch.NOT_FINISHED)
    else:
      v4_batch.set_more_results(
          datastore_v4_pb.QueryResultBatch.MORE_RESULTS_AFTER_LIMIT)
    if v3_result.has_compiled_cursor():
      v4_batch.set_end_cursor(
          self._query_converter.v3_to_v4_compiled_cursor(
              v3_result.compiled_cursor()))
    if v3_result.has_skipped_results_compiled_cursor():
      v4_batch.set_skipped_cursor(
          self._query_converter.v3_to_v4_compiled_cursor(
              v3_result.skipped_results_compiled_cursor()))


    if v3_result.keys_only():
      v4_batch.set_entity_result_type(datastore_v4_pb.EntityResult.KEY_ONLY)
    elif v3_result.index_only():
      v4_batch.set_entity_result_type(datastore_v4_pb.EntityResult.PROJECTION)
    else:
      v4_batch.set_entity_result_type(datastore_v4_pb.EntityResult.FULL)


    if v3_result.has_skipped_results():
      v4_batch.set_skipped_results(v3_result.skipped_results())
    for v3_entity, v3_cursor in itertools.izip_longest(
        v3_result.result_list(),
        v3_result.result_compiled_cursor_list()):
      v4_entity_result = datastore_v4_pb.EntityResult()
      self._entity_converter.v3_to_v4_entity(v3_entity,
                                             v4_entity_result.mutable_entity())
      if v3_cursor is not None:
        v4_entity_result.set_cursor(
            self._query_converter.v3_to_v4_compiled_cursor(v3_cursor))
      v4_batch.entity_result_list().append(v4_entity_result)


def get_service_converter(id_resolver=None):
  """Returns a converter for v3 and v1 service request/response protos.

  This converter is suitable for use in stubs but not for production.

  Returns:
    a StubServiceConverter
  """
  query_converter = get_query_converter(id_resolver)
  return StubServiceConverter(query_converter.get_entity_converter(),
                              query_converter)


def ReverseBitsInt64(v):
  """Reverse the bits of a 64-bit integer.

  Args:
    v: Input integer of type 'int' or 'long'.

  Returns:
    Bit-reversed input as 'int' on 64-bit machines or as 'long' otherwise.
  """

  v = ((v >> 1) & 0x5555555555555555) | ((v & 0x5555555555555555) << 1)
  v = ((v >> 2) & 0x3333333333333333) | ((v & 0x3333333333333333) << 2)
  v = ((v >> 4) & 0x0F0F0F0F0F0F0F0F) | ((v & 0x0F0F0F0F0F0F0F0F) << 4)
  v = ((v >> 8) & 0x00FF00FF00FF00FF) | ((v & 0x00FF00FF00FF00FF) << 8)
  v = ((v >> 16) & 0x0000FFFF0000FFFF) | ((v & 0x0000FFFF0000FFFF) << 16)
  v = int((v >> 32) | (v << 32) & 0xFFFFFFFFFFFFFFFF)
  return v


def ToScatteredId(v):
  """Map counter value v to the scattered ID space.

  Translate to scattered ID space, then reverse bits.

  Args:
    v: Counter value from which to produce ID.

  Returns:
    Integer ID.

  Raises:
    datastore_errors.BadArgumentError if counter value exceeds the range of
  the scattered ID space.
  """
  if v >= _MAX_SCATTERED_COUNTER:
    raise datastore_errors.BadArgumentError('counter value too large (%d)' % v)
  return _MAX_SEQUENTIAL_ID + 1 + long(ReverseBitsInt64(v << _SCATTER_SHIFT))


def IdToCounter(k):
  """Map ID k to the counter value from which it was generated.

  Determine whether k is sequential or scattered ID.

  Args:
    k: ID from which to infer counter value.

  Returns:
    Tuple of integers (counter_value, id_space).
  """
  if k > _MAX_SCATTERED_ID:
    return 0, SCATTERED
  elif k > _MAX_SEQUENTIAL_ID and k <= _MAX_SCATTERED_ID:
    return long(ReverseBitsInt64(k) >> _SCATTER_SHIFT), SCATTERED
  elif k > 0:
    return long(k), SEQUENTIAL
  else:
    raise datastore_errors.BadArgumentError('invalid id (%d)' % k)


def CompareEntityPbByKey(a, b):
  """Compare two entity protobuf's by key.

  Args:
    a: entity_pb.EntityProto to compare
    b: entity_pb.EntityProto to compare
  Returns:
     <0 if a's key is before b's, =0 if they are the same key, and >0 otherwise.
  """
  return cmp(datastore_types.Key._FromPb(a.key()),
             datastore_types.Key._FromPb(b.key()))


def NormalizeCursors(query, first_sort_direction):
  """Normalizes compiled cursors in place.

  Any position specified in the position group is moved to either the
  postfix_position or absolute_position field and the position group is
  cleared.

  If the cursor position does not specify before_ascending, populate it.
  If before_ascending is already populated, use it and the sort direction
  from the query to set an appropriate value for before.

  Args:
    query: datastore_pb.Query
    first_sort_direction: first sort direction as returned by _GuessOrders
  """
  _NormalizeCursor(query.compiled_cursor(), first_sort_direction)
  _NormalizeCursor(query.end_compiled_cursor(), first_sort_direction)


def _GuessOrders(filters, orders):
  """Guess any implicit ordering.

  The datastore gives a logical, but not necessarily predictable, ordering when
  orders are not completely explicit. This function guesses at that ordering
  (which is better then always ordering by __key__ for tests).

  Args:
    filters: The datastore_pb.Query_Filter that have already been normalized and
      checked.
    orders: The datastore_pb.Query_Order that have already been normalized and
      checked. Mutated in place.
  """
  orders = orders[:]


  if not orders:
    for filter_pb in filters:
      if filter_pb.op() in datastore_index.INEQUALITY_OPERATORS:

        order = datastore_pb.Query_Order()
        order.set_property(filter_pb.property(0).name())
        orders.append(order)
        break


  exists_props = (filter_pb.property(0).name() for filter_pb in filters
                  if filter_pb.op() == datastore_pb.Query_Filter.EXISTS)
  for prop in sorted(exists_props):
    order = datastore_pb.Query_Order()
    order.set_property(prop)
    orders.append(order)


  if not orders or orders[-1].property() != '__key__':
    order = datastore_pb.Query_Order()
    order.set_property('__key__')
    orders.append(order)
  return orders


def _MakeQuery(query_pb, filters, orders):
  """Make a datastore_query.Query for the given datastore_pb.Query.

  Overrides filters and orders in query with the specified arguments.

  Args:
    query_pb: a datastore_pb.Query.
    filters: the filters from query.
    orders: the orders from query.

  Returns:
    A datastore_query.Query for the datastore_pb.Query."""

  clone_pb = datastore_pb.Query()
  clone_pb.CopyFrom(query_pb)
  clone_pb.clear_filter()
  clone_pb.clear_order()
  clone_pb.filter_list().extend(filters)
  clone_pb.order_list().extend(orders)

  return datastore_query.Query._from_pb(clone_pb)


def _CreateIndexEntities(entity, postfix_props):
  """Creates entities for index values that would appear in prodcution.

  This function finds all multi-valued properties listed in split_props, and
  creates a new entity for each unique combination of values. The resulting
  entities will only have a single value for each property listed in
  split_props.

  It reserves the right to include index data that would not be
  seen in production, e.g. by returning the original entity when no splitting
  is needed. LoadEntity will remove any excess fields.

  This simulates the results seen by an index scan in the datastore.

  Args:
    entity: The entity_pb.EntityProto to split.
    split_props: A set of property names to split on.

  Returns:
    A list of the split entity_pb.EntityProtos.
  """
  to_split = {}
  split_required = False
  base_props = []
  for prop in entity.property_list():
    if prop.name() in postfix_props:
      values = to_split.get(prop.name())
      if values is None:
        values = []
        to_split[prop.name()] = values
      else:

        split_required = True
      if prop.value() not in values:
        values.append(prop.value())
    else:
      base_props.append(prop)

  if not split_required:

    return [entity]

  clone = entity_pb.EntityProto()
  clone.CopyFrom(entity)
  clone.clear_property()
  clone.property_list().extend(base_props)
  results = [clone]

  for name, splits in to_split.iteritems():
    if len(splits) == 1:

      for result in results:
        prop = result.add_property()
        prop.set_name(name)
        prop.set_multiple(False)
        prop.set_meaning(entity_pb.Property.INDEX_VALUE)
        prop.mutable_value().CopyFrom(splits[0])
      continue

    new_results = []
    for result in results:
      for split in splits:
        clone = entity_pb.EntityProto()
        clone.CopyFrom(result)
        prop = clone.add_property()
        prop.set_name(name)
        prop.set_multiple(False)
        prop.set_meaning(entity_pb.Property.INDEX_VALUE)
        prop.mutable_value().CopyFrom(split)
        new_results.append(clone)
    results = new_results
  return results


def _CreateIndexOnlyQueryResults(records, postfix_props):
  """Creates a result set similar to that returned by an index only query."""
  new_records = []
  for record in records:
    index_entities = _CreateIndexEntities(record.entity, postfix_props)
    new_records.extend([EntityRecord(e, record.metadata)
                        for e in index_entities])
  return new_records


def _ExecuteQuery(results, query, filters, orders, index_list):
  """Executes the query on a superset of its results.

  Args:
    results: superset of results for query, list of EntityRecord.
    query: a datastore_pb.Query.
    filters: the filters from query.
    orders: the orders from query.
    index_list: the list of indexes used by the query.

  Returns:
    A ListCursor over the results of applying query to results.
  """
  orders = _GuessOrders(filters, orders)


  NormalizeCursors(query, orders[0].direction())
  dsquery = _MakeQuery(query, filters, orders)

  if query.property_name_size():
    order_properties = set(order.property() for order in orders)
    results = _CreateIndexOnlyQueryResults(results, order_properties)

  filtered_results = datastore_query.apply_query(dsquery, results,
                                                 lambda r: r.entity)
  return ListCursor(query, dsquery, orders, index_list, filtered_results)


def _UpdateCost(cost, entity_writes, index_writes):
  """Updates the provided cost.

  Args:
    cost: Out param. The cost object to update.
    entity_writes: The number of entity writes to add.
    index_writes: The number of index writes to add.
  """
  cost.set_entity_writes(cost.entity_writes() + entity_writes)
  cost.set_index_writes(cost.index_writes() + index_writes)


def _PropertyListToMultimap(property_list):
  """Transforms a list of property protobufs into a multimap keyed by name.

  The order of repeated properties is respected in the result. The returned
  multimap can be compared directly for entity equality testing.

  Args:
    property_list: a list of datastore_pbs.Property protobufs.

  Returns:
    a map of property names to list of datastore_pbs.Property with that name.
  """
  result = collections.defaultdict(list)
  for prop in property_list:
    result[prop.name()].append(prop)
  return result


def _IsNoOpWrite(old_entity, new_entity):
  """Returns whether putting an entity is a no-op given its current value.

  Args:
    old_entity: the current entity in the datastore, or None if the entity does
        not exist.
    new_entity: the new entity to store, or None if we are deleting the entity.
        Note that the two entities must share the same key.

  Returns:
    True iff both the previous and new entities are None or are equivalent (have
    the same properties and property values).
  """
  if old_entity is not None and new_entity is not None:
    old_raw_properties = _PropertyListToMultimap(old_entity.raw_property_list())
    new_raw_properties = _PropertyListToMultimap(new_entity.raw_property_list())
    old_properties = _PropertyListToMultimap(old_entity.property_list())
    new_properties = _PropertyListToMultimap(new_entity.property_list())

    return (old_properties == new_properties
            and old_raw_properties == new_raw_properties)
  else:
    return old_entity == new_entity


def _CalculateWriteOps(composite_indexes, old_entity, new_entity):
  """Determines number of entity and index writes needed to write new_entity.

  We assume that old_entity represents the current state of the Datastore.

  Args:
    composite_indexes: The composite_indexes for the kind of the entities.
    old_entity: Entity representing the current state in the Datstore.
    new_entity: Entity representing the desired state in the Datstore.

  Returns:
    A tuple of size 2, where the first value is the number of entity writes and
    the second value is the number of index writes.
  """
  if _IsNoOpWrite(old_entity, new_entity):
    return 0, 0

  index_writes = _ChangedIndexRows(composite_indexes, old_entity, new_entity)
  if old_entity is None:



    index_writes += 1

  return 1, index_writes


def _ChangedIndexRows(composite_indexes, old_entity, new_entity):
  """Determine the number of index rows that need to change.

  We assume that old_entity represents the current state of the Datastore.

  Args:
    composite_indexes: The composite_indexes for the kind of the entities.
    old_entity: Entity representing the current state in the Datastore.
    new_entity: Entity representing the desired state in the Datastore

  Returns:
    The number of index rows that need to change.
  """



  unique_old_properties = collections.defaultdict(set)




  unique_new_properties = collections.defaultdict(set)

  if old_entity is not None:
    for old_prop in old_entity.property_list():
      _PopulateUniquePropertiesSet(old_prop, unique_old_properties)


  unchanged = collections.defaultdict(int)

  for new_prop in new_entity.property_list():
    new_prop_as_str = _PopulateUniquePropertiesSet(
        new_prop, unique_new_properties)
    if new_prop_as_str in unique_old_properties[new_prop.name()]:
      unchanged[new_prop.name()] += 1




  all_property_names = set(unique_old_properties.iterkeys())
  all_property_names.update(unique_old_properties.iterkeys())
  all_property_names.update(unchanged.iterkeys())

  all_indexes = _GetEntityByPropertyIndexes(all_property_names)
  all_indexes.extend([comp.definition() for comp in composite_indexes])
  path_size = new_entity.key().path().element_size()
  writes = 0
  for index in all_indexes:



    ancestor_multiplier = 1
    if index.ancestor() and index.property_size() > 1:
      ancestor_multiplier = path_size
    writes += (_CalculateWritesForCompositeIndex(
        index, unique_old_properties, unique_new_properties, unchanged) *
               ancestor_multiplier)
  return writes


def _PopulateUniquePropertiesSet(prop, unique_properties):
  """Populates a set containing unique properties.

  Args:
    prop: An entity property.
    unique_properties: Dictionary mapping property names to a set of unique
      properties.

  Returns:
    The property pb in string (hashable) form.
  """
  if prop.multiple():
    prop = _CopyAndSetMultipleToFalse(prop)


  prop_as_str = prop.SerializePartialToString()
  unique_properties[prop.name()].add(prop_as_str)
  return prop_as_str


def _CalculateWritesForCompositeIndex(index, unique_old_properties,
                                      unique_new_properties,
                                      common_properties):
  """Calculate the number of writes required to maintain a specific Index.

  Args:
    index: The composite index.
    unique_old_properties: Dictionary mapping property names to a set of props
      present on the old entity.
    unique_new_properties: Dictionary mapping property names to a set of props
      present on the new entity.
    common_properties: Dictionary mapping property names to the number of
      properties with that name that are present on both the old and new
      entities.

  Returns:
    The number of writes required to maintained the provided index.
  """
  old_count = 1
  new_count = 1
  common_count = 1
  for prop in index.property_list():
    old_count *= len(unique_old_properties[prop.name()])
    new_count *= len(unique_new_properties[prop.name()])
    common_count *= common_properties[prop.name()]

  return (old_count - common_count) + (new_count - common_count)


def _GetEntityByPropertyIndexes(all_property_names):
  indexes = []
  for prop_name in all_property_names:
    indexes.append(
        _SinglePropertyIndex(prop_name, entity_pb.Index_Property.ASCENDING))
    indexes.append(
        _SinglePropertyIndex(prop_name, entity_pb.Index_Property.DESCENDING))
  return indexes


def _SinglePropertyIndex(prop_name, direction):
  """Creates a single property Index for the given name and direction.

  Args:
    prop_name: The name of the single property on the Index.
    direction: The direction of the Index.

  Returns:
    A single property Index with the given property and direction.
  """
  index = entity_pb.Index()
  prop = index.add_property()
  prop.set_name(prop_name)
  prop.set_direction(direction)
  return index


def _CopyAndSetMultipleToFalse(prop):
  """Copy the provided Property and set its "multiple" attribute to False.

  Args:
    prop: The Property to copy.

  Returns:
    A copy of the given Property with its "multiple" attribute set to False.
  """





  prop_copy = entity_pb.Property()
  prop_copy.MergeFrom(prop)
  prop_copy.set_multiple(False)
  return prop_copy


def _NormalizeCursor(cursor, first_sort_direction):
  """Normalizes a compiled cursor in place.

  Any position specified in the position group is moved to either the
  postfix_position or absolute_position field and the position group is
  cleared.

  If the cursor position does not specify before_ascending, populate it.
  If before_ascending is already populated, use it and the provided direction
  to set an appropriate value for before.

  Args:
    cursor: datastore_pb.CompiledCursor
    first_sort_direction: first sort direction as returned by _GuessOrders
  """
  Check((cursor.has_position()
         + cursor.has_postfix_position()
         + cursor.has_absolute_position()) <= 1,
        ('Cursor may specify at most one of position, postfix_position, '
         'and absolute_position.'))


  if cursor.has_position():
    pos = cursor.position()
    if pos.has_start_key():
      index_pos = cursor.mutable_absolute_position()
      index_pos.set_key(pos.start_key())
      if pos.has_start_inclusive():
        index_pos.set_before(pos.start_inclusive())
      if pos.has_before_ascending():
        index_pos.set_before_ascending(pos.before_ascending())
    elif pos.has_key() or len(pos.indexvalue_list()) > 0:
      postfix_pos = cursor.mutable_postfix_position()
      for value in pos.indexvalue_list():
        index_value = postfix_pos.add_index_value()
        index_value.set_property_name(value.property())
        index_value.mutable_value().MergeFrom(value.value())
      if pos.has_key():
        postfix_pos.mutable_key().MergeFrom(pos.key())
      if pos.has_start_inclusive():
        postfix_pos.set_before(pos.start_inclusive())
      if pos.has_before_ascending():
        postfix_pos.set_before_ascending(pos.before_ascending())
    cursor.clear_position()


  pos = None
  if cursor.has_absolute_position():
    pos = cursor.absolute_position()
  elif cursor.has_postfix_position():
    pos = cursor.postfix_position()
  if pos:
    if pos.has_before_ascending():
      _SetBefore(pos, first_sort_direction)
    else:
      _SetBeforeAscending(pos, first_sort_direction)


def _SetBefore(position, first_direction):
  """Sets the before field in position.

  Args:
    position: an entity_pb.IndexPosition or entity_pb.IndexPostfix
    first_direction: the first sort order from the query
      (a datastore_pb.Query_Order) or None
  """
  position.set_before(
      position.before_ascending()
      != (first_direction == datastore_pb.Query_Order.DESCENDING))


def _SetBeforeAscending(position, first_direction):
  """Sets the before_ascending field in position.

  Args:
    position: an entity_pb.IndexPosition or entity_pb.IndexPostfix
    first_direction: the first sort order from the query
      (a datastore_pb.Query_Order) or None
  """
  position.set_before_ascending(
      position.before()
      != (first_direction == datastore_pb.Query_Order.DESCENDING))
