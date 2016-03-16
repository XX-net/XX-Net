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




"""Generate Datastore Stats over Dev mode appserver's datastore."""










import datetime
import logging

from google.appengine.api import datastore
from google.appengine.api import datastore_admin
from google.appengine.api import datastore_types
from google.appengine.api import users
from google.appengine.ext.db import stats

DELETE_BATCH_SIZE = 100


_GLOBAL_KEY = (stats.GlobalStat, 'total_entity_usage', '')






_PROPERTY_TYPE_TO_DSS_NAME = {
    unicode: ('String', 'STRING'),
    bool: ('Boolean', 'BOOLEAN'),
    long: ('Integer', 'INT64'),
    type(None): ('NULL', 'NULL'),
    float: ('Float', 'DOUBLE'),
    datastore_types.Key: ('Key', 'REFERENCE'),
    datastore_types.Blob: ('Blob', 'STRING'),
    datastore_types.EmbeddedEntity: ('EmbeddedEntity', 'STRING'),
    datastore_types.ByteString: ('ShortBlob', 'STRING'),
    datastore_types.Text: ('Text', 'STRING'),
    users.User: ('User', 'USER'),
    datastore_types.Category: ('Category', 'STRING'),
    datastore_types.Link: ('Link', 'STRING'),
    datastore_types.Email: ('Email', 'STRING'),
    datetime.datetime: ('Date/Time', 'INT64'),
    datastore_types.GeoPt: ('GeoPt', 'POINT'),
    datastore_types.IM: ('IM', 'STRING'),
    datastore_types.PhoneNumber: ('PhoneNumber', 'STRING'),
    datastore_types.PostalAddress: ('PostalAddress', 'STRING'),
    datastore_types.Rating: ('Rating', 'INT64'),
    datastore_types.BlobKey: ('BlobKey', 'STRING'),
    }




class DatastoreStatsProcessor(object):
  """Generates datastore stats for an app's an datastore entities."""

  def __init__(self, _app=None):
    self.app_id = datastore_types.ResolveAppId(_app)


    self.whole_app_stats = {}



    self.namespace_stats = {}
    self.found_non_empty_namespace = False


    self.old_stat_keys = []


    self.timestamp = datetime.datetime.utcnow()

  def __ScanAllNamespaces(self):
    """Scans all the namespaces and processes each namespace."""
    namespace_query = datastore.Query('__namespace__', _app=self.app_id)

    for namespace_entity in namespace_query.Run():
      name = namespace_entity.key().name()
      if name is None:
        name = ''
      self.__ProcessNamespace(name)

  def __ProcessNamespace(self, namespace):
    """Process all the entities in a given namespace."""

    all_query = datastore.Query(namespace=namespace, _app=self.app_id)


    for entity in all_query.Run():
      self.found_non_empty_namespace |= (namespace != '')
      proto = entity.ToPb()
      proto_size = len(proto.SerializeToString())

      if entity.key().kind() in stats._DATASTORE_STATS_CLASSES_BY_KIND:



        stat_kind = stats._DATASTORE_STATS_CLASSES_BY_KIND[entity.key().kind()]

        self.old_stat_keys.append(entity.key())
        self.__AggregateTotal(proto_size, entity.key(), proto, namespace,
                              stat_kind)
      else:
        self.__ProcessUserEntity(proto_size, entity.key(), proto, namespace)

  def __GetPropertyIndexStat(self, namespace, kind_name,
                             entity_key_size, prop):
    """Return the size and count of indexes for a property of an EntityProto."""

    property_index_size = (len(self.app_id) + len(kind_name) +
                           len(prop.value().SerializeToString()) +
                           len(namespace) + entity_key_size)

    return (property_index_size, 2)

  def __GetTypeIndexStat(self, namespace, kind_name, entity_key_size):
    """Return the size and count of indexes by type of an EntityProto."""
    type_index_size = (len(self.app_id) + len(kind_name) + entity_key_size
                       + len(namespace))
    return (type_index_size, 1)

  def __ProcessUserEntity(self, proto_size, key, proto, namespace):
    """Increment datastore stats for a non stats record."""
    self.__AggregateTotal(proto_size, key, proto, namespace, None)

    kind_name = key.kind()

    entity_key_size = (len(proto.key().app()) + len(namespace) +
                       len(proto.key().path().SerializeToString()) +
                       len(proto.entity_group().SerializeToString()))

    self.__AggregateCompositeIndices(proto, namespace, kind_name,
                                     entity_key_size)

    type_index_size, type_index_count = self.__GetTypeIndexStat(namespace,
                                                                kind_name,
                                                                entity_key_size)
    property_index_count = 0
    property_index_size = 0


    for prop_list in (proto.property_list(), proto.raw_property_list()):
      for prop in prop_list:
        index_size, index_count = self.__GetPropertyIndexStat(namespace,
                                                              kind_name,
                                                              entity_key_size,
                                                              prop)
        property_index_size += index_size
        property_index_count += index_count

    builtin_index_size = type_index_size + property_index_size
    builtin_index_count = type_index_count + property_index_count

    self.__Increment(self.whole_app_stats, 1,
                     (stats.KindStat, kind_name, ''),
                     proto_size,
                     builtin_index_count=builtin_index_count,
                     builtin_index_size=builtin_index_size,
                     kind_name=kind_name)

    self.__Increment(self.namespace_stats, 1,
                     (stats.NamespaceKindStat, kind_name, namespace),
                     proto_size,
                     builtin_index_count=builtin_index_count,
                     builtin_index_size=builtin_index_size,
                     kind_name=kind_name)



    if key.parent() is None:
      whole_app_model = stats.KindRootEntityStat
      namespace_model = stats.NamespaceKindRootEntityStat
    else:
      whole_app_model = stats.KindNonRootEntityStat
      namespace_model = stats.NamespaceKindNonRootEntityStat

    self.__Increment(self.whole_app_stats, 1,
                     (whole_app_model, kind_name, ''),
                     proto_size,
                     kind_name=kind_name)

    self.__Increment(self.namespace_stats, 1,
                     (namespace_model, kind_name, namespace),
                     proto_size,
                     kind_name=kind_name)

    self.__ProcessProperties(
        kind_name,
        namespace,
        entity_key_size,
        (proto.property_list(), proto.raw_property_list()))

  def __ProcessProperties(self, kind_name, namespace, entity_key_size,
                          prop_lists):
    for prop_list in prop_lists:
      for prop in prop_list:
        try:
          value = datastore_types.FromPropertyPb(prop)
          self.__AggregateProperty(kind_name, namespace, entity_key_size,
                                   prop, value)
        except (AssertionError, AttributeError, TypeError, ValueError), e:
          logging.error('Cannot process property %r, exception %s' %
                        (prop, e))

  def __AggregateProperty(self, kind_name, namespace, entity_key_size,
                          prop, value):
    property_name = prop.name()
    property_type = _PROPERTY_TYPE_TO_DSS_NAME[type(value)][0]
    index_property_type = _PROPERTY_TYPE_TO_DSS_NAME[type(value)][1]
    size = len(prop.SerializeToString())


    index_size, index_count = self.__GetPropertyIndexStat(namespace, kind_name,
                                                          entity_key_size, prop)





    self.__Increment(self.whole_app_stats, 1,
                     (stats.PropertyTypeStat, property_type, ''),
                     size,
                     builtin_index_count=0,
                     builtin_index_size=0,
                     property_type=property_type)

    self.__Increment(self.whole_app_stats, 0,
                     (stats.PropertyTypeStat, index_property_type, ''),
                     0,
                     builtin_index_count=index_count,
                     builtin_index_size=index_size,
                     property_type=index_property_type)

    self.__Increment(self.namespace_stats, 1,
                     (stats.NamespacePropertyTypeStat,
                      property_type, namespace),
                     size,
                     builtin_index_count=0,
                     builtin_index_size=0,
                     property_type=property_type)

    self.__Increment(self.namespace_stats, 0,
                     (stats.NamespacePropertyTypeStat,
                      index_property_type, namespace),
                     0,
                     builtin_index_count=index_count,
                     builtin_index_size=index_size,
                     property_type=index_property_type)


    self.__Increment(self.whole_app_stats, 1,
                     (stats.KindPropertyTypeStat,
                      property_type + '_' + kind_name, ''),
                     size,
                     builtin_index_count=0,
                     builtin_index_size=0,
                     property_type=property_type, kind_name=kind_name)

    self.__Increment(self.whole_app_stats, 0,
                     (stats.KindPropertyTypeStat,
                      index_property_type + '_' + kind_name, ''),
                     0,
                     builtin_index_count=index_count,
                     builtin_index_size=index_size,
                     property_type=index_property_type, kind_name=kind_name)

    self.__Increment(self.namespace_stats, 1,
                     (stats.NamespaceKindPropertyTypeStat,
                      property_type + '_' + kind_name, namespace),
                     size,
                     builtin_index_count=0,
                     builtin_index_size=0,
                     property_type=property_type, kind_name=kind_name)

    self.__Increment(self.namespace_stats, 0,
                     (stats.NamespaceKindPropertyTypeStat,
                      index_property_type + '_' + kind_name, namespace),
                     0,
                     builtin_index_count=index_count,
                     builtin_index_size=index_size,
                     property_type=index_property_type, kind_name=kind_name)


    self.__Increment(self.whole_app_stats, 1,
                     (stats.KindPropertyNameStat,
                      property_name + '_' + kind_name, ''),
                     size,
                     builtin_index_count=index_count,
                     builtin_index_size=index_size,
                     property_name=property_name, kind_name=kind_name)

    self.__Increment(self.namespace_stats, 1,
                     (stats.NamespaceKindPropertyNameStat,
                      property_name + '_' + kind_name, namespace),
                     size,
                     builtin_index_count=index_count,
                     builtin_index_size=index_size,
                     property_name=property_name, kind_name=kind_name)


    self.__Increment(self.whole_app_stats, 1,
                     (stats.KindPropertyNamePropertyTypeStat,
                      property_type + '_' + property_name + '_' + kind_name,
                      ''), size,
                     builtin_index_count=0,
                     builtin_index_size=0,
                     property_type=property_type,
                     property_name=property_name, kind_name=kind_name)

    self.__Increment(self.whole_app_stats, 0,
                     (stats.KindPropertyNamePropertyTypeStat,
                      index_property_type + '_' + property_name + '_' +
                      kind_name,
                      ''), 0,
                     builtin_index_count=index_count,
                     builtin_index_size=index_size,
                     property_type=index_property_type,
                     property_name=property_name, kind_name=kind_name)

    self.__Increment(self.namespace_stats, 1,
                     (stats.NamespaceKindPropertyNamePropertyTypeStat,
                      property_type + '_' + property_name + '_' + kind_name,
                      namespace),
                     size,
                     builtin_index_count=0,
                     builtin_index_size=0,
                     property_type=property_type,
                     property_name=property_name, kind_name=kind_name)

    self.__Increment(self.namespace_stats, 0,
                     (stats.NamespaceKindPropertyNamePropertyTypeStat,
                      index_property_type + '_' + property_name + '_' +
                      kind_name,
                      namespace),
                     0,
                     builtin_index_count=index_count,
                     builtin_index_size=index_size,
                     property_type=index_property_type,
                     property_name=property_name, kind_name=kind_name)

  def __GetCompositeIndexStat(self, definition, proto, namespace, kind_name,
                              entity_key_size):
    """Get statistics of composite index for a index definition of an entity."""






    property_list = proto.property_list()
    property_count = []
    property_size = []
    index_count = 1
    for indexed_prop in definition.property_list():
      name = indexed_prop.name()
      count = 0
      prop_size = 0
      for prop in property_list:
        if prop.name() == name:
          count += 1
          prop_size += len(prop.SerializeToString())

      property_count.append(count)
      property_size.append(prop_size)
      index_count *= count

    if index_count == 0:
      return (0, 0)

    index_only_size = 0
    for i in range(len(property_size)):
      index_only_size += property_size[i] * (index_count / property_count[i])





    index_size = (index_count * (entity_key_size + len(kind_name) +
                                 len(self.app_id) + len(namespace)) +
                  index_only_size * 2)

    return (index_size, index_count)

  def __AggregateCompositeIndices(self, proto, namespace, kind_name,
                                  entity_key_size):
    """Aggregate statistics of composite indexes for an entity."""
    composite_indices = datastore_admin.GetIndices(self.app_id)
    for index in composite_indices:
      definition = index.definition()
      if kind_name != definition.entity_type():
        continue

      index_size, index_count = self.__GetCompositeIndexStat(definition, proto,
                                                             namespace,
                                                             kind_name,
                                                             entity_key_size)

      if index_count == 0:
        continue


      name_id = namespace
      if not name_id:
        name_id = 1


      self.__Increment(self.whole_app_stats, 0, _GLOBAL_KEY, 0,
                       composite_index_count=index_count,
                       composite_index_size=index_size)

      self.__Increment(self.whole_app_stats, 0,
                       (stats.NamespaceStat, name_id, ''), 0,
                       composite_index_count=index_count,
                       composite_index_size=index_size,
                       subject_namespace=namespace)

      self.__Increment(self.namespace_stats, 0,
                       (stats.NamespaceGlobalStat, 'total_entity_usage',
                        namespace), 0,
                       composite_index_count=index_count,
                       composite_index_size=index_size)


      self.__Increment(self.whole_app_stats, 0,
                       (stats.KindStat, kind_name, ''), 0,
                       composite_index_count=index_count,
                       composite_index_size=index_size,
                       kind_name=kind_name)

      self.__Increment(self.namespace_stats, 0,
                       (stats.NamespaceKindStat, kind_name, namespace), 0,
                       composite_index_count=index_count,
                       composite_index_size=index_size,
                       kind_name=kind_name)


      index_id = index.id()
      self.__Increment(self.whole_app_stats, index_count,
                       (stats.KindCompositeIndexStat,
                        kind_name + '_%s' % index_id, ''), index_size,
                       kind_name=kind_name, index_id=index_id)

      self.__Increment(self.namespace_stats, index_count,
                       (stats.NamespaceKindCompositeIndexStat,
                        kind_name + '_%s' % index_id, namespace), index_size,
                       kind_name=kind_name, index_id=index_id)

  def __AggregateTotal(self, size, key, proto, namespace, stat_kind):
    """Aggregate total datastore stats."""
    kind_name = key.kind()

    entity_key_size = (len(proto.key().app()) +
                       len(proto.key().path().SerializeToString()) +
                       len(proto.entity_group().SerializeToString()))

    type_index_size, type_index_count = self.__GetTypeIndexStat(namespace,
                                                                kind_name,
                                                                entity_key_size)
    property_index_count = 0
    property_index_size = 0
    for prop_list in (proto.property_list(), proto.raw_property_list()):
      for prop in prop_list:
        index_size, index_count = self.__GetPropertyIndexStat(namespace,
                                                              kind_name,
                                                              entity_key_size,
                                                              prop)
        property_index_size += index_size
        property_index_count += index_count

    builtin_index_size = type_index_size + property_index_size
    builtin_index_count = type_index_count + property_index_count


    if stat_kind == stats.GlobalStat:
      count = 0
    else:
      count = 1


    self.__Increment(self.whole_app_stats, count, _GLOBAL_KEY, size,
                     builtin_index_count=builtin_index_count,
                     builtin_index_size=builtin_index_size)


    name_id = namespace
    if not name_id:
      name_id = 1

    if (stat_kind == stats.NamespaceStat) and (namespace == ''):
      count = 0


    self.__Increment(self.whole_app_stats, count,
                     (stats.NamespaceStat, name_id, ''),
                     size,
                     builtin_index_count=builtin_index_count,
                     builtin_index_size=builtin_index_size,
                     subject_namespace=namespace)

    if stat_kind == stats.NamespaceGlobalStat:
      count = 0


    self.__Increment(
        self.namespace_stats, count,
        (stats.NamespaceGlobalStat, 'total_entity_usage', namespace), size,
        builtin_index_count=builtin_index_count,
        builtin_index_size=builtin_index_size)

  def __Increment(self, stats_dict, count, stat_key, size,
                  builtin_index_count=0, builtin_index_size=0,
                  composite_index_count=0, composite_index_size=0, **kwds):
    """Increment stats for a particular kind.

    Args:
        stats_dict: The dictionary where the entities are held.
          The entities are keyed by stat_key. e.g. The
          __Stat_Total__ entity will be found in stats_dict[_GLOBAL_KEY].
        count: The amount to increment the datastore stat by.
        stat_key: A tuple of (db.Model of the stat, key value, namespace).
        size: The "bytes" to increment the size by.
        builtin_index_count: The bytes of builtin index to add in to a stat.
        builtin_index_size: The count of builtin index to add in to a stat.
        composite_index_count: The bytes of composite index to add in to a stat.
        composite_index_size: The count of composite index to add in to a stat.
        kwds: Name value pairs that are set on the created entities.
    """

    if stat_key not in stats_dict:
      stat_model = stat_key[0](
          key=datastore_types.Key.from_path(stat_key[0].STORED_KIND_NAME,
                                            stat_key[1],
                                            namespace=stat_key[2],
                                            _app=self.app_id),
          _app=self.app_id)
      stats_dict[stat_key] = stat_model
      for field, value in kwds.iteritems():
        setattr(stat_model, field, value)
      stat_model.count = count
      if size:
        stat_model.entity_bytes = size
      if builtin_index_size:
        stat_model.builtin_index_bytes = builtin_index_size
        stat_model.builtin_index_count = builtin_index_count
      if composite_index_size:
        stat_model.composite_index_bytes = composite_index_size
        stat_model.composite_index_count = composite_index_count
      stat_model.bytes = size + builtin_index_size + composite_index_size
      stat_model.timestamp = self.timestamp
    else:
      stat_model = stats_dict[stat_key]
      stat_model.count += count
      if size:
        stat_model.entity_bytes += size
      if builtin_index_size:
        stat_model.builtin_index_bytes += builtin_index_size
        stat_model.builtin_index_count += builtin_index_count
      if composite_index_size:
        stat_model.composite_index_bytes += composite_index_size
        stat_model.composite_index_count += composite_index_count
      stat_model.bytes += size + builtin_index_size + composite_index_size

  def __Finalize(self):
    """Finishes processing, deletes all old stats and writes new ones."""

    for i in range(0, len(self.old_stat_keys), DELETE_BATCH_SIZE):
      datastore.Delete(self.old_stat_keys[i:i+DELETE_BATCH_SIZE])

    self.written = 0

    for stat in self.whole_app_stats.itervalues():
      if stat.count or not (isinstance(stat, stats.GlobalStat) or
                            isinstance(stat, stats.NamespaceStat)):
        stat.put()
        self.written += 1



    if self.found_non_empty_namespace:
      for stat in self.namespace_stats.itervalues():
        if stat.count or not isinstance(stat, stats.NamespaceGlobalStat):
          stat.put()
          self.written += 1

  def Run(self):
    """Scans the datastore, computes new stats and writes them."""
    self.__ScanAllNamespaces()
    self.__Finalize()
    return self

  def Report(self):
    """Produce a small report about the result."""
    stat = self.whole_app_stats.get(_GLOBAL_KEY, None)
    entity_size = 0
    entity_count = 0
    builtin_index_size = 0
    builtin_index_count = 0
    composite_index_size = 0
    composite_index_count = 0
    if stat:
      entity_size = stat.entity_bytes
      entity_count = stat.count
      builtin_index_size = stat.builtin_index_bytes
      builtin_index_count = stat.builtin_index_count
      composite_index_size = stat.composite_index_bytes
      composite_index_count = stat.composite_index_count

      if not entity_count:
        entity_count = 1

    return ('Scanned %d entities of total %d bytes, %d index entries of total '
            '%d bytes and %d composite index entries of total %d bytes. '
            'Inserted %d new records.'
            % (entity_count, entity_size, builtin_index_count,
               builtin_index_size, composite_index_count, composite_index_size,
               self.written))
