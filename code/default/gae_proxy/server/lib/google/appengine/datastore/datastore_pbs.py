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




"""Utilities for converting between v3 and v1 datastore protocol buffers.

This module is internal and should not be used by client applications.
"""

















from google.appengine.datastore import entity_pb
from google.appengine.datastore import datastore_v4_pb
from google.appengine.datastore import entity_v4_pb

_MIN_CLOUD_DATASTORE_VERSION = (4, 0, 0, 'b1')
_CLOUD_DATASTORE_ENABLED = False

try:
  
  
  import googledatastore

  if googledatastore.VERSION >= _MIN_CLOUD_DATASTORE_VERSION:
    _CLOUD_DATASTORE_ENABLED = True
except ImportError:
  pass
except AttributeError:

  pass

MISSING_CLOUD_DATASTORE_MESSAGE = (
    'Could not import googledatastore. This library must be installed with '
    'version >= %s to use the Cloud Datastore API.' %
    '.'.join([str(v) for v in _MIN_CLOUD_DATASTORE_VERSION]))


MEANING_ATOM_CATEGORY = 1
MEANING_URL = 2
MEANING_ATOM_TITLE = 3
MEANING_ATOM_CONTENT = 4
MEANING_ATOM_SUMMARY = 5
MEANING_ATOM_AUTHOR = 6
MEANING_GD_EMAIL = 8
MEANING_GEORSS_POINT = 9
MEANING_GD_IM = 10
MEANING_GD_PHONENUMBER = 11
MEANING_GD_POSTALADDRESS = 12
MEANING_PERCENT = 13
MEANING_TEXT = 15
MEANING_BYTESTRING = 16
MEANING_BLOBKEY = 17
MEANING_INDEX_ONLY = 18
MEANING_PREDEFINED_ENTITY_USER = 20
MEANING_PREDEFINED_ENTITY_POINT = 21
MEANING_ZLIB = 22
MEANING_POINT_WITHOUT_V3_MEANING = 23
MEANING_EMPTY_LIST = 24


URI_MEANING_ZLIB = 'ZLIB'



MAX_URL_CHARS = 2083
MAX_INDEXED_STRING_CHARS = 500
MAX_INDEXED_BLOB_BYTES = 500
MAX_PARTITION_ID_LENGTH = 100
MAX_DATASET_ID_SECTION_LENGTH = 100



MAX_DATASET_ID_LENGTH = MAX_DATASET_ID_SECTION_LENGTH * 3 + 2
MAX_KEY_PATH_LENGTH = 100


PROPERTY_NAME_X = 'x'
PROPERTY_NAME_Y = 'y'


PROPERTY_NAME_EMAIL = 'email'
PROPERTY_NAME_AUTH_DOMAIN = 'auth_domain'
PROPERTY_NAME_USER_ID = 'user_id'
PROPERTY_NAME_INTERNAL_ID = 'internal_id'
PROPERTY_NAME_FEDERATED_IDENTITY = 'federated_identity'
PROPERTY_NAME_FEDERATED_PROVIDER = 'federated_provider'


PROPERTY_NAME_KEY = '__key__'

DEFAULT_GAIA_ID = 0


def v4_key_to_string(v4_key):
  """Generates a string representing a key's path.

  The output makes no effort to qualify special characters in strings.

  The key need not be valid, but if any of the key path elements have
  both a name and an ID the name is ignored.

  Args:
    v4_key: an entity_v4_pb.Key

  Returns:
    a string representing the key's path
  """
  path_element_strings = []
  for path_element in v4_key.path_element_list():
    if path_element.has_id():
      id_or_name = str(path_element.id())
    elif path_element.has_name():
      id_or_name = path_element.name()
    else:
      id_or_name = ''
    path_element_strings.append('%s: %s' % (path_element.kind(), id_or_name))
  return '[%s]' % ', '.join(path_element_strings)


def is_complete_v4_key(v4_key):
  """Returns True if a key specifies an ID or name, False otherwise.

  Args:
    v4_key: an entity_v4_pb.Key

  Returns:
    True if the key specifies an ID or name, False otherwise.
  """
  assert len(v4_key.path_element_list()) >= 1
  last_element = v4_key.path_element(len(v4_key.path_element_list()) - 1)
  return last_element.has_id() or last_element.has_name()


def v1_key_to_string(v1_key):
  """Generates a string representing a key's path.

  The output makes no effort to qualify special characters in strings.

  The key need not be valid, but if any of the key path elements have
  both a name and an ID the name is ignored.

  Args:
    v1_key: an googledatastore.Key

  Returns:
    a string representing the key's path
  """
  path_element_strings = []
  for path_element in v1_key.path:
    field = path_element.WhichOneof('id_type')
    if field == 'id':
      id_or_name = str(path_element.id)
    elif field == 'name':
      id_or_name = path_element.name
    else:
      id_or_name = ''
    path_element_strings.append('%s: %s' % (path_element.kind, id_or_name))
  return '[%s]' % ', '.join(path_element_strings)


def is_complete_v1_key(v1_key):
  """Returns True if a key specifies an ID or name, False otherwise.

  Args:
    v1_key: an googledatastore.Key

  Returns:
    True if the key specifies an ID or name, False otherwise.
  """
  assert len(v1_key.path) >= 1
  last_element = v1_key.path[len(v1_key.path) - 1]
  return last_element.WhichOneof('id_type') is not None


def is_complete_v3_key(v3_key):
  """Returns True if a key specifies an ID or name, False otherwise.

  Args:
    v3_key: a datastore_pb.Reference

  Returns:
    True if the key specifies an ID or name, False otherwise.
  """
  assert v3_key.path().element_size() >= 1
  last_element = v3_key.path().element_list()[-1]
  return ((last_element.has_id() and last_element.id() != 0) or
          (last_element.has_name() and last_element.name() != ''))


def get_v1_mutation_key_and_entity(v1_mutation):
  """Returns the v1 key and entity for a v1 mutation proto, if applicable.

  Args:
    v1_mutation: a googledatastore.Mutation

  Returns:
    a tuple (googledatastore.Key for this mutation,
             googledatastore.Entity or None if the mutation is a deletion)
  """
  if v1_mutation.HasField('delete'):
    return v1_mutation.delete, None
  else:
    v1_entity = getattr(v1_mutation, v1_mutation.WhichOneof('operation'))
    return v1_entity.key, v1_entity


def is_valid_utf8(s):
  if isinstance(s, unicode):
    return True
  try:
    s.decode('utf-8')
    return True
  except UnicodeDecodeError:
    return False


def check_conversion(condition, message):
  """Asserts a conversion condition and raises an error if it's not met.

  Args:
    condition: (boolean) condition to enforce
    message: error message

  Raises:
    InvalidConversionError: if condition is not met
  """
  if not condition:
    raise InvalidConversionError(message)



class InvalidConversionError(Exception):
  """Raised when conversion fails."""
  pass


class IdResolver(object):
  """A class that can handle project id <--> application id transformations."""

  def __init__(self, app_ids=()):
    """Create a new IdResolver.

    Args:
     app_ids: A list of application ids with application id shard set. i.e.
         s~my_app or e~my_app.
    """
    resolver_map = {}
    for app_id in app_ids:
      resolver_map[self.resolve_project_id(app_id)] = app_id
    self._resolver_map = resolver_map

  def resolve_project_id(self, app_id):
    """Converts an application id to a project id.

    Args:
      app_id: The application id.
    Returns:
      The project id.
    """
    return app_id.rsplit('~')[-1]

  def resolve_app_id(self, project_id):
    """Converts a project id to an application id.

    Args:
      project_id: The project id.
    Returns:
      The application id.
    Raises:
      InvalidConversionError: if the application is unknown for the project id.
    """
    check_conversion(project_id in self._resolver_map,
                     'Cannot determine application id for provided project id: '
                     '"%s".'
                     % project_id)
    return self._resolver_map[project_id]


class _IdentityIdResolver(IdResolver):
  """An IdResolver that resolve app_id == project_id."""

  def resolve_project_id(self, app_id):
    return app_id

  def resolve_app_id(self, project_id):
    return project_id


class _EntityConverter(object):
  """Converter for entities and keys."""

  def __init__(self, id_resolver):
    """Creates a new EntityConverter.

    Args:
      id_resolver: an IdResolver object for converting
      project_id <--> application_id
    """
    self._id_resolver = id_resolver

  def v4_to_v3_reference(self, v4_key, v3_ref):
    """Converts a v4 Key to a v3 Reference.

    Args:
      v4_key: an entity_v4_pb.Key
      v3_ref: an entity_pb.Reference to populate
    """
    v3_ref.Clear()
    if v4_key.has_partition_id():
      if v4_key.partition_id().has_dataset_id():
        v3_ref.set_app(v4_key.partition_id().dataset_id())
      if v4_key.partition_id().has_namespace():
        v3_ref.set_name_space(v4_key.partition_id().namespace())
    for v4_element in v4_key.path_element_list():
      v3_element = v3_ref.mutable_path().add_element()
      v3_element.set_type(v4_element.kind())
      if v4_element.has_id():
        v3_element.set_id(v4_element.id())
      if v4_element.has_name():
        v3_element.set_name(v4_element.name())

  def v4_to_v3_references(self, v4_keys):
    """Converts a list of v4 Keys to a list of v3 References.

    Args:
      v4_keys: a list of entity_v4_pb.Key objects

    Returns:
      a list of entity_pb.Reference objects
    """
    v3_refs = []
    for v4_key in v4_keys:
      v3_ref = entity_pb.Reference()
      self.v4_to_v3_reference(v4_key, v3_ref)
      v3_refs.append(v3_ref)
    return v3_refs

  def v3_to_v4_key(self, v3_ref, v4_key):
    """Converts a v3 Reference to a v4 Key.

    Args:
      v3_ref: an entity_pb.Reference
      v4_key: an entity_v4_pb.Key to populate
    """
    v4_key.Clear()
    if not v3_ref.app():
      return
    v4_key.mutable_partition_id().set_dataset_id(v3_ref.app())
    if v3_ref.name_space():
      v4_key.mutable_partition_id().set_namespace(v3_ref.name_space())
    for v3_element in v3_ref.path().element_list():
      v4_element = v4_key.add_path_element()
      v4_element.set_kind(v3_element.type())
      if v3_element.has_id():
        v4_element.set_id(v3_element.id())
      if v3_element.has_name():
        v4_element.set_name(v3_element.name())

  def v3_to_v4_keys(self, v3_refs):
    """Converts a list of v3 References to a list of v4 Keys.

    Args:
      v3_refs: a list of entity_pb.Reference objects

    Returns:
      a list of entity_v4_pb.Key objects
    """
    v4_keys = []
    for v3_ref in v3_refs:
      v4_key = entity_v4_pb.Key()
      self.v3_to_v4_key(v3_ref, v4_key)
      v4_keys.append(v4_key)
    return v4_keys

  def v4_to_v3_entity(self, v4_entity, v3_entity, is_projection=False):
    """Converts a v4 Entity to a v3 EntityProto.

    Args:
      v4_entity: an entity_v4_pb.Entity
      v3_entity: an entity_pb.EntityProto to populate
      is_projection: True if the v4_entity is from a projection query.
    """
    v3_entity.Clear()
    for v4_property in v4_entity.property_list():
      property_name = v4_property.name()
      v4_value = v4_property.value()
      if v4_value.list_value_list():
        for v4_sub_value in v4_value.list_value_list():
          self.__add_v3_property_from_v4(
              property_name, True, is_projection, v4_sub_value, v3_entity)
      else:
        self.__add_v3_property_from_v4(
            property_name, False, is_projection, v4_value, v3_entity)
    if v4_entity.has_key():
      v4_key = v4_entity.key()
      self.v4_to_v3_reference(v4_key, v3_entity.mutable_key())
      v3_ref = v3_entity.key()
      self.v3_reference_to_group(v3_ref, v3_entity.mutable_entity_group())
    else:


      pass

  def v3_to_v4_entity(self, v3_entity, v4_entity):
    """Converts a v3 EntityProto to a v4 Entity.

    Args:
      v3_entity: an entity_pb.EntityProto
      v4_entity: an entity_v4_pb.Proto to populate
    """
    v4_entity.Clear()
    self.v3_to_v4_key(v3_entity.key(), v4_entity.mutable_key())
    if not v3_entity.key().has_app():

      v4_entity.clear_key()




    v4_properties = {}
    for v3_property in v3_entity.property_list():
      self.__add_v4_property_to_entity(v4_entity, v4_properties, v3_property,
                                       True)
    for v3_property in v3_entity.raw_property_list():
      self.__add_v4_property_to_entity(v4_entity, v4_properties, v3_property,
                                       False)

  def v4_value_to_v3_property_value(self, v4_value, v3_value):
    """Converts a v4 Value to a v3 PropertyValue.

    Args:
      v4_value: an entity_v4_pb.Value
      v3_value: an entity_pb.PropertyValue to populate
    """
    v3_value.Clear()
    if v4_value.has_boolean_value():
      v3_value.set_booleanvalue(v4_value.boolean_value())
    elif v4_value.has_integer_value():
      v3_value.set_int64value(v4_value.integer_value())
    elif v4_value.has_double_value():
      v3_value.set_doublevalue(v4_value.double_value())
    elif v4_value.has_timestamp_microseconds_value():
      v3_value.set_int64value(v4_value.timestamp_microseconds_value())
    elif v4_value.has_key_value():
      v3_ref = entity_pb.Reference()
      self.v4_to_v3_reference(v4_value.key_value(), v3_ref)
      self.v3_reference_to_v3_property_value(v3_ref, v3_value)
    elif v4_value.has_blob_key_value():
      v3_value.set_stringvalue(v4_value.blob_key_value())
    elif v4_value.has_string_value():
      v3_value.set_stringvalue(v4_value.string_value())
    elif v4_value.has_blob_value():
      v3_value.set_stringvalue(v4_value.blob_value())
    elif v4_value.has_entity_value():
      v4_entity_value = v4_value.entity_value()
      v4_meaning = v4_value.meaning()
      if (v4_meaning == MEANING_GEORSS_POINT
          or v4_meaning == MEANING_PREDEFINED_ENTITY_POINT):
        self.__v4_to_v3_point_value(v4_entity_value,
                                    v3_value.mutable_pointvalue())
      elif v4_meaning == MEANING_PREDEFINED_ENTITY_USER:
        self.v4_entity_to_v3_user_value(v4_entity_value,
                                        v3_value.mutable_uservalue())
      else:
        v3_entity_value = entity_pb.EntityProto()
        self.v4_to_v3_entity(v4_entity_value, v3_entity_value)
        v3_value.set_stringvalue(v3_entity_value.SerializePartialToString())
    elif v4_value.has_geo_point_value():
      point_value = v3_value.mutable_pointvalue()
      point_value.set_x(v4_value.geo_point_value().latitude())
      point_value.set_y(v4_value.geo_point_value().longitude())
    else:

      pass

  def v3_property_to_v4_value(self, v3_property, indexed, v4_value):
    """Converts a v3 Property to a v4 Value.

    Args:
      v3_property: an entity_pb.Property
      indexed: whether the v3 property is indexed
      v4_value: an entity_v4_pb.Value to populate
    """
    v4_value.Clear()
    v3_property_value = v3_property.value()
    v3_meaning = v3_property.meaning()
    v3_uri_meaning = None
    if v3_property.meaning_uri():
      v3_uri_meaning = v3_property.meaning_uri()

    if not self.__is_v3_property_value_union_valid(v3_property_value):


      v3_meaning = None
      v3_uri_meaning = None
    elif v3_meaning == entity_pb.Property.NO_MEANING:
      v3_meaning = None
    elif not self.__is_v3_property_value_meaning_valid(v3_property_value,
                                                       v3_meaning):

      v3_meaning = None

    is_zlib_value = False
    if v3_uri_meaning:
      if v3_uri_meaning == URI_MEANING_ZLIB:
        if v3_property_value.has_stringvalue():
          is_zlib_value = True
          if v3_meaning != entity_pb.Property.BLOB:

            v3_meaning = entity_pb.Property.BLOB
        else:
          pass
      else:
        pass


    if v3_property_value.has_booleanvalue():
      v4_value.set_boolean_value(v3_property_value.booleanvalue())
    elif v3_property_value.has_int64value():
      if v3_meaning == entity_pb.Property.GD_WHEN:
        v4_value.set_timestamp_microseconds_value(
            v3_property_value.int64value())
        v3_meaning = None
      else:
        v4_value.set_integer_value(v3_property_value.int64value())
    elif v3_property_value.has_doublevalue():
      v4_value.set_double_value(v3_property_value.doublevalue())
    elif v3_property_value.has_referencevalue():
      v3_ref = entity_pb.Reference()
      self.__v3_reference_value_to_v3_reference(
          v3_property_value.referencevalue(), v3_ref)
      self.v3_to_v4_key(v3_ref, v4_value.mutable_key_value())
    elif v3_property_value.has_stringvalue():
      if v3_meaning == entity_pb.Property.ENTITY_PROTO:
        serialized_entity_v3 = v3_property_value.stringvalue()
        v3_entity = entity_pb.EntityProto()


        v3_entity.ParsePartialFromString(serialized_entity_v3)
        self.v3_to_v4_entity(v3_entity, v4_value.mutable_entity_value())
        v3_meaning = None
      elif (v3_meaning == entity_pb.Property.BLOB
            or v3_meaning == entity_pb.Property.BYTESTRING):
        v4_value.set_blob_value(v3_property_value.stringvalue())

        if indexed or v3_meaning == entity_pb.Property.BLOB:
          v3_meaning = None
      else:
        string_value = v3_property_value.stringvalue()
        if is_valid_utf8(string_value):
          if v3_meaning == entity_pb.Property.BLOBKEY:
            v4_value.set_blob_key_value(string_value)
            v3_meaning = None
          else:
            v4_value.set_string_value(string_value)
        else:

          v4_value.set_blob_value(string_value)

          if v3_meaning != entity_pb.Property.INDEX_VALUE:
            v3_meaning = None


    elif v3_property_value.has_pointvalue():
      if v3_meaning == MEANING_GEORSS_POINT:
        point_value = v3_property_value.pointvalue()
        v4_value.mutable_geo_point_value().set_latitude(point_value.x())
        v4_value.mutable_geo_point_value().set_longitude(point_value.y())
      else:
        self.__v3_to_v4_point_entity(v3_property_value.pointvalue(),
                                     v4_value.mutable_entity_value())
        v4_value.set_meaning(MEANING_PREDEFINED_ENTITY_POINT)

      v3_meaning = None
    elif v3_property_value.has_uservalue():
      self.v3_user_value_to_v4_entity(v3_property_value.uservalue(),
                                      v4_value.mutable_entity_value())
      v4_value.set_meaning(MEANING_PREDEFINED_ENTITY_USER)
      v3_meaning = None
    else:
      pass

    if is_zlib_value:
      v4_value.set_meaning(MEANING_ZLIB)
    elif v3_meaning:
      v4_value.set_meaning(v3_meaning)


    if indexed != v4_value.indexed():
      v4_value.set_indexed(indexed)

  def v4_to_v3_property(self, property_name, is_multi, is_projection,
                        v4_value, v3_property):
    """Converts info from a v4 Property to a v3 Property.

    v4_value must not have a list_value.

    Args:
      property_name: the name of the property
      is_multi: whether the property contains multiple values
      is_projection: whether the property is projected
      v4_value: an entity_v4_pb.Value
      v3_property: an entity_pb.Property to populate
    """
    assert not v4_value.list_value_list(), 'v4 list_value not convertable to v3'
    v3_property.Clear()
    v3_property.set_name(property_name)

    if v4_value.has_meaning() and v4_value.meaning() == MEANING_EMPTY_LIST:
      v3_property.set_meaning(MEANING_EMPTY_LIST)
      v3_property.set_multiple(False)
      v3_property.mutable_value()
      return

    v3_property.set_multiple(is_multi)
    self.v4_value_to_v3_property_value(v4_value, v3_property.mutable_value())

    v4_meaning = None
    if v4_value.has_meaning():
      v4_meaning = v4_value.meaning()
    if v4_value.has_timestamp_microseconds_value():
      v3_property.set_meaning(entity_pb.Property.GD_WHEN)
    elif v4_value.has_blob_key_value():
      v3_property.set_meaning(entity_pb.Property.BLOBKEY)
    elif v4_value.has_blob_value():
      if v4_meaning == MEANING_ZLIB:
        v3_property.set_meaning_uri(URI_MEANING_ZLIB)
      if v4_meaning == entity_pb.Property.BYTESTRING:
        if v4_value.indexed():
          pass


      else:
        if v4_value.indexed():
          v3_property.set_meaning(entity_pb.Property.BYTESTRING)
        else:
          v3_property.set_meaning(entity_pb.Property.BLOB)
        v4_meaning = None
    elif v4_value.has_entity_value():
      if v4_meaning != MEANING_GEORSS_POINT:
        if (v4_meaning != MEANING_PREDEFINED_ENTITY_POINT
            and v4_meaning != MEANING_PREDEFINED_ENTITY_USER):
          v3_property.set_meaning(entity_pb.Property.ENTITY_PROTO)
        v4_meaning = None
    elif v4_value.has_geo_point_value():
      v3_property.set_meaning(MEANING_GEORSS_POINT)
    else:

      pass
    if v4_meaning is not None:
      v3_property.set_meaning(v4_meaning)

    if is_projection:
      v3_property.set_meaning(entity_pb.Property.INDEX_VALUE)


  def __add_v3_property_from_v4(self, property_name, is_multi, is_projection,
                        v4_value, v3_entity):
    """Adds a v3 Property to an Entity based on information from a v4 Property.

    Args:
      property_name: the name of the property
      is_multi: whether the property contains multiple values
      is_projection: whether the property is a projection
      v4_value: an entity_v4_pb.Value
      v3_entity: an entity_pb.EntityProto
    """
    if v4_value.indexed():
      self.v4_to_v3_property(property_name, is_multi, is_projection,
                             v4_value, v3_entity.add_property())
    else:
      self.v4_to_v3_property(property_name, is_multi, is_projection,
                             v4_value, v3_entity.add_raw_property())

  def __build_name_to_v4_property_map(self, v4_entity):
    property_map = {}
    for prop in v4_entity.property_list():
      property_map[prop.name()] = prop
    return property_map

  def __add_v4_property_to_entity(self, v4_entity, property_map, v3_property,
                                  indexed):
    """Adds a v4 Property to an entity or modifies an existing one.

    property_map is used to track of properties that have already been added.
    The same dict should be used for all of an entity's properties.

    Args:
      v4_entity: an entity_v4_pb.Entity
      property_map: a dict of name -> v4_property
      v3_property: an entity_pb.Property to convert to v4 and add to the dict
      indexed: whether the property is indexed
    """
    property_name = v3_property.name()
    if property_name in property_map:
      v4_property = property_map[property_name]
    else:
      v4_property = v4_entity.add_property()
      v4_property.set_name(property_name)
      property_map[property_name] = v4_property
    if v3_property.multiple():
      self.v3_property_to_v4_value(v3_property, indexed,
                                   v4_property.mutable_value().add_list_value())
    else:
      self.v3_property_to_v4_value(v3_property, indexed,
                                   v4_property.mutable_value())

  def __get_v4_integer_value(self, v4_property):
    """Returns an integer value from a v4 Property.

    Args:
      v4_property: an entity_v4_pb.Property

    Returns:
      an integer

    Raises:
      InvalidConversionError: if the property doesn't contain an integer value
    """
    check_conversion(v4_property.value().has_integer_value(),
                     'Property does not contain an integer value.')
    return v4_property.value().integer_value()

  def __get_v4_double_value(self, v4_property):
    """Returns a double value from a v4 Property.

    Args:
      v4_property: an entity_v4_pb.Property

    Returns:
      a double

    Raises:
      InvalidConversionError: if the property doesn't contain a double value
    """
    check_conversion(v4_property.value().has_double_value(),
                     'Property does not contain a double value.')
    return v4_property.value().double_value()

  def __get_v4_string_value(self, v4_property):
    """Returns an string value from a v4 Property.

    Args:
      v4_property: an entity_v4_pb.Property

    Returns:
      a string

    Throws:
      InvalidConversionError: if the property doesn't contain a string value
    """
    check_conversion(v4_property.value().has_string_value(),
                     'Property does not contain a string value.')
    return v4_property.value().string_value()

  def __v4_integer_property(self, name, value, indexed):
    """Creates a single-integer-valued v4 Property.

    Args:
      name: the property name
      value: the integer value of the property
      indexed: whether the value should be indexed

    Returns:
      an entity_v4_pb.Property
    """
    v4_property = entity_v4_pb.Property()
    v4_property.set_name(name)
    v4_value = v4_property.mutable_value()
    v4_value.set_indexed(indexed)
    v4_value.set_integer_value(value)
    return v4_property

  def __v4_double_property(self, name, value, indexed):
    """Creates a single-double-valued v4 Property.

    Args:
      name: the property name
      value: the double value of the property
      indexed: whether the value should be indexed

    Returns:
      an entity_v4_pb.Property
    """
    v4_property = entity_v4_pb.Property()
    v4_property.set_name(name)
    v4_value = v4_property.mutable_value()
    v4_value.set_indexed(indexed)
    v4_value.set_double_value(value)
    return v4_property

  def __v4_string_property(self, name, value, indexed):
    """Creates a single-string-valued v4 Property.

    Args:
      name: the property name
      value: the string value of the property
      indexed: whether the value should be indexed

    Returns:
      an entity_v4_pb.Property
    """
    v4_property = entity_v4_pb.Property()
    v4_property.set_name(name)
    v4_value = v4_property.mutable_value()
    v4_value.set_indexed(indexed)
    v4_value.set_string_value(value)
    return v4_property

  def __v4_to_v3_point_value(self, v4_point_entity, v3_point_value):
    """Converts a v4 point Entity to a v3 PointValue.

    Args:
      v4_point_entity: an entity_v4_pb.Entity representing a point
      v3_point_value: an entity_pb.Property_PointValue to populate
    """
    v3_point_value.Clear()
    name_to_v4_property = self.__build_name_to_v4_property_map(v4_point_entity)
    v3_point_value.set_x(
        self.__get_v4_double_value(name_to_v4_property['x']))
    v3_point_value.set_y(
        self.__get_v4_double_value(name_to_v4_property['y']))

  def __v3_to_v4_point_entity(self, v3_point_value, v4_entity):
    """Converts a v3 UserValue to a v4 user Entity.

    Args:
      v3_point_value: an entity_pb.Property_PointValue
      v4_entity: an entity_v4_pb.Entity to populate
    """
    v4_entity.Clear()
    v4_entity.property_list().append(
        self.__v4_double_property(PROPERTY_NAME_X, v3_point_value.x(), False))
    v4_entity.property_list().append(
        self.__v4_double_property(PROPERTY_NAME_Y, v3_point_value.y(), False))

  def v4_entity_to_v3_user_value(self, v4_user_entity, v3_user_value):
    """Converts a v4 user Entity to a v3 UserValue.

    Args:
      v4_user_entity: an entity_v4_pb.Entity representing a user
      v3_user_value: an entity_pb.Property_UserValue to populate
    """
    v3_user_value.Clear()
    name_to_v4_property = self.__build_name_to_v4_property_map(v4_user_entity)

    v3_user_value.set_email(self.__get_v4_string_value(
        name_to_v4_property[PROPERTY_NAME_EMAIL]))
    v3_user_value.set_auth_domain(self.__get_v4_string_value(
        name_to_v4_property[PROPERTY_NAME_AUTH_DOMAIN]))
    if PROPERTY_NAME_USER_ID in name_to_v4_property:
      v3_user_value.set_obfuscated_gaiaid(
          self.__get_v4_string_value(
              name_to_v4_property[PROPERTY_NAME_USER_ID]))
    if PROPERTY_NAME_INTERNAL_ID in name_to_v4_property:
      v3_user_value.set_gaiaid(self.__get_v4_integer_value(
          name_to_v4_property[PROPERTY_NAME_INTERNAL_ID]))
    else:

      v3_user_value.set_gaiaid(0)
    if PROPERTY_NAME_FEDERATED_IDENTITY in name_to_v4_property:
      v3_user_value.set_federated_identity(
          self.__get_v4_string_value(name_to_v4_property[
              PROPERTY_NAME_FEDERATED_IDENTITY]))
    if PROPERTY_NAME_FEDERATED_PROVIDER in name_to_v4_property:
      v3_user_value.set_federated_provider(
          self.__get_v4_string_value(name_to_v4_property[
              PROPERTY_NAME_FEDERATED_PROVIDER]))

  def v3_user_value_to_v4_entity(self, v3_user_value, v4_entity):
    """Converts a v3 UserValue to a v4 user Entity.

    Args:
      v3_user_value: an entity_pb.Property_UserValue
      v4_entity: an entity_v4_pb.Entity to populate
    """
    v4_entity.Clear()
    v4_entity.property_list().append(
        self.__v4_string_property(PROPERTY_NAME_EMAIL, v3_user_value.email(),
                                  False))
    v4_entity.property_list().append(self.__v4_string_property(
        PROPERTY_NAME_AUTH_DOMAIN,
        v3_user_value.auth_domain(), False))

    if v3_user_value.gaiaid() != 0:
      v4_entity.property_list().append(self.__v4_integer_property(
          PROPERTY_NAME_INTERNAL_ID,
          v3_user_value.gaiaid(),
          False))
    if v3_user_value.has_obfuscated_gaiaid():
      v4_entity.property_list().append(self.__v4_string_property(
          PROPERTY_NAME_USER_ID,
          v3_user_value.obfuscated_gaiaid(),
          False))
    if v3_user_value.has_federated_identity():
      v4_entity.property_list().append(self.__v4_string_property(
          PROPERTY_NAME_FEDERATED_IDENTITY,
          v3_user_value.federated_identity(),
          False))
    if v3_user_value.has_federated_provider():
      v4_entity.property_list().append(self.__v4_string_property(
          PROPERTY_NAME_FEDERATED_PROVIDER,
          v3_user_value.federated_provider(),
          False))

  def v1_to_v3_reference(self, v1_key, v3_ref):
    """Converts a v1 Key to a v3 Reference.

    Args:
      v1_key: an googledatastore.Key
      v3_ref: an entity_pb.Reference to populate
    """
    v3_ref.Clear()
    if v1_key.HasField('partition_id'):
      project_id = v1_key.partition_id.project_id
      if project_id:
        app_id = self._id_resolver.resolve_app_id(project_id)
        v3_ref.set_app(app_id)
      if v1_key.partition_id.namespace_id:
        v3_ref.set_name_space(v1_key.partition_id.namespace_id)
    for v1_element in v1_key.path:
      v3_element = v3_ref.mutable_path().add_element()
      v3_element.set_type(v1_element.kind.encode('utf-8'))
      id_type = v1_element.WhichOneof('id_type')
      if id_type == 'id':
        v3_element.set_id(v1_element.id)
      elif id_type == 'name':
        v3_element.set_name(v1_element.name.encode('utf-8'))

  def v1_to_v3_references(self, v1_keys):
    """Converts a list of v1 Keys to a list of v3 References.

    Args:
      v1_keys: a list of googledatastore.Key objects

    Returns:
      a list of entity_pb.Reference objects
    """
    v3_refs = []
    for v1_key in v1_keys:
      v3_ref = entity_pb.Reference()
      self.v1_to_v3_reference(v1_key, v3_ref)
      v3_refs.append(v3_ref)
    return v3_refs

  def v3_to_v1_key(self, v3_ref, v1_key):
    """Converts a v3 Reference to a v1 Key.

    Args:
      v3_ref: an entity_pb.Reference
      v1_key: an googledatastore.Key to populate
    """
    v1_key.Clear()
    if not v3_ref.app():
      return
    project_id = self._id_resolver.resolve_project_id(v3_ref.app())
    v1_key.partition_id.project_id = project_id
    if v3_ref.name_space():
      v1_key.partition_id.namespace_id = v3_ref.name_space()
    for v3_element in v3_ref.path().element_list():
      v1_element = v1_key.path.add()
      v1_element.kind = v3_element.type()
      if v3_element.has_id():
        v1_element.id = v3_element.id()
      if v3_element.has_name():
        v1_element.name = v3_element.name()

  def v3_to_v1_keys(self, v3_refs):
    """Converts a list of v3 References to a list of v1 Keys.

    Args:
      v3_refs: a list of entity_pb.Reference objects

    Returns:
      a list of googledatastore.Key objects
    """
    v1_keys = []
    for v3_ref in v3_refs:
      v1_key = googledatastore.Key()
      self.v3_to_v1_key(v3_ref, v1_key)
      v1_keys.append(v1_key)
    return v1_keys

  def project_to_app_id(self, project_id):
    """Converts a string project id to a string app id."""
    return self._id_resolver.resolve_app_id(project_id)

  def app_to_project_id(self, app_id):
    """Converts a string app id to a string project id."""
    return self._id_resolver.resolve_project_id(app_id)

  def __new_v3_property(self, v3_entity, is_indexed):
    if is_indexed:
      return v3_entity.add_property()
    else:
      return v3_entity.add_raw_property()

  def v1_to_v3_entity(self, v1_entity, v3_entity, is_projection=False):
    """Converts a v1 Entity to a v3 EntityProto.

    Args:
      v1_entity: an googledatastore.Entity
      v3_entity: an entity_pb.EntityProto to populate
      is_projection: True if the v1_entity is from a projection query.
    """
    v3_entity.Clear()
    for property_name, v1_value in v1_entity.properties.iteritems():

      if v1_value.HasField('array_value'):
        if len(v1_value.array_value.values) == 0:
          empty_list = self.__new_v3_property(v3_entity,
                                              not v1_value.exclude_from_indexes)
          empty_list.set_name(property_name.encode('utf-8'))
          empty_list.set_multiple(False)
          empty_list.set_meaning(MEANING_EMPTY_LIST)
          empty_list.mutable_value()
        else:
          for v1_sub_value in v1_value.array_value.values:
            list_element = self.__new_v3_property(
                v3_entity, not v1_sub_value.exclude_from_indexes)
            self.v1_to_v3_property(
                property_name, True, is_projection, v1_sub_value, list_element)
      else:
        value_property = self.__new_v3_property(
            v3_entity, not v1_value.exclude_from_indexes)
        self.v1_to_v3_property(
            property_name, False, is_projection, v1_value, value_property)

    if v1_entity.HasField('key'):
      v1_key = v1_entity.key
      self.v1_to_v3_reference(v1_key, v3_entity.mutable_key())
      v3_ref = v3_entity.key()
      self.v3_reference_to_group(v3_ref, v3_entity.mutable_entity_group())
    else:


      pass

  def v3_to_v1_entity(self, v3_entity, v1_entity):
    """Converts a v3 EntityProto to a v1 Entity.

    Args:
      v3_entity: an entity_pb.EntityProto
      v1_entity: an googledatastore.Proto to populate
    """
    v1_entity.Clear()
    self.v3_to_v1_key(v3_entity.key(), v1_entity.key)
    if not v3_entity.key().has_app():

      v1_entity.ClearField('key')




    for v3_property in v3_entity.property_list():
      self.__add_v1_property_to_entity(v1_entity, v3_property, True)
    for v3_property in v3_entity.raw_property_list():
      self.__add_v1_property_to_entity(v1_entity, v3_property, False)

  def v1_value_to_v3_property_value(self, v1_value, v3_value):
    """Converts a v1 Value to a v3 PropertyValue.

    Args:
      v1_value: an googledatastore.Value
      v3_value: an entity_pb.PropertyValue to populate
    """
    v3_value.Clear()
    field = v1_value.WhichOneof('value_type')
    if field == 'boolean_value':
      v3_value.set_booleanvalue(v1_value.boolean_value)
    elif field == 'integer_value':
      v3_value.set_int64value(v1_value.integer_value)
    elif field == 'double_value':
      v3_value.set_doublevalue(v1_value.double_value)
    elif field == 'timestamp_value':
      v3_value.set_int64value(
          googledatastore.helper.micros_from_timestamp(
              v1_value.timestamp_value))
    elif field == 'key_value':
      v3_ref = entity_pb.Reference()
      self.v1_to_v3_reference(v1_value.key_value, v3_ref)
      self.v3_reference_to_v3_property_value(v3_ref, v3_value)
    elif field == 'string_value':
      v3_value.set_stringvalue(v1_value.string_value.encode('utf-8'))
    elif field == 'blob_value':
      v3_value.set_stringvalue(v1_value.blob_value)
    elif field == 'entity_value':
      v1_entity_value = v1_value.entity_value
      v1_meaning = v1_value.meaning
      if v1_meaning == MEANING_PREDEFINED_ENTITY_USER:
        self.v1_entity_to_v3_user_value(v1_entity_value,
                                        v3_value.mutable_uservalue())
      else:
        v3_entity_value = entity_pb.EntityProto()
        self.v1_to_v3_entity(v1_entity_value, v3_entity_value)
        v3_value.set_stringvalue(v3_entity_value.SerializePartialToString())
    elif field == 'geo_point_value':
      point_value = v3_value.mutable_pointvalue()
      point_value.set_x(v1_value.geo_point_value.latitude)
      point_value.set_y(v1_value.geo_point_value.longitude)
    elif field == 'null_value':
      pass
    else:

      pass

  def v3_property_to_v1_value(self, v3_property, indexed, v1_value):
    """Converts a v3 Property to a v1 Value.

    Args:
      v3_property: an entity_pb.Property
      indexed: whether the v3 property is indexed
      v1_value: an googledatastore.Value to populate
    """
    v1_value.Clear()
    v3_property_value = v3_property.value()
    v3_meaning = v3_property.meaning()
    v3_uri_meaning = None
    if v3_property.meaning_uri():
      v3_uri_meaning = v3_property.meaning_uri()

    if not self.__is_v3_property_value_union_valid(v3_property_value):


      v3_meaning = None
      v3_uri_meaning = None
    elif v3_meaning == entity_pb.Property.NO_MEANING:
      v3_meaning = None
    elif not self.__is_v3_property_value_meaning_valid(v3_property_value,
                                                       v3_meaning):

      v3_meaning = None

    is_zlib_value = False
    if v3_uri_meaning:
      if v3_uri_meaning == URI_MEANING_ZLIB:
        if v3_property_value.has_stringvalue():
          is_zlib_value = True
          if v3_meaning != entity_pb.Property.BLOB:

            v3_meaning = entity_pb.Property.BLOB
        else:
          pass
      else:
        pass


    if v3_property.meaning() == entity_pb.Property.EMPTY_LIST:
      v1_value.array_value.values.extend([])
      v3_meaning = None
    elif v3_property_value.has_booleanvalue():
      v1_value.boolean_value = v3_property_value.booleanvalue()
    elif v3_property_value.has_int64value():
      if v3_meaning == entity_pb.Property.GD_WHEN:
        googledatastore.helper.micros_to_timestamp(
            v3_property_value.int64value(), v1_value.timestamp_value)
        v3_meaning = None
      else:
        v1_value.integer_value = v3_property_value.int64value()
    elif v3_property_value.has_doublevalue():
      v1_value.double_value = v3_property_value.doublevalue()
    elif v3_property_value.has_referencevalue():
      v3_ref = entity_pb.Reference()
      self.__v3_reference_value_to_v3_reference(
          v3_property_value.referencevalue(), v3_ref)
      self.v3_to_v1_key(v3_ref, v1_value.key_value)
    elif v3_property_value.has_stringvalue():
      if v3_meaning == entity_pb.Property.ENTITY_PROTO:
        serialized_entity_v3 = v3_property_value.stringvalue()
        v3_entity = entity_pb.EntityProto()


        v3_entity.ParsePartialFromString(serialized_entity_v3)
        self.v3_to_v1_entity(v3_entity, v1_value.entity_value)
        v3_meaning = None
      elif (v3_meaning == entity_pb.Property.BLOB
            or v3_meaning == entity_pb.Property.BYTESTRING):
        v1_value.blob_value = v3_property_value.stringvalue()

        if indexed or v3_meaning == entity_pb.Property.BLOB:
          v3_meaning = None
      else:
        string_value = v3_property_value.stringvalue()
        if is_valid_utf8(string_value):
          v1_value.string_value = string_value
        else:

          v1_value.blob_value = string_value

          if v3_meaning != entity_pb.Property.INDEX_VALUE:
            v3_meaning = None


    elif v3_property_value.has_pointvalue():
      if v3_meaning != MEANING_GEORSS_POINT:
        v1_value.meaning = MEANING_POINT_WITHOUT_V3_MEANING

      point_value = v3_property_value.pointvalue()
      v1_value.geo_point_value.latitude = point_value.x()
      v1_value.geo_point_value.longitude = point_value.y()
      v3_meaning = None
    elif v3_property_value.has_uservalue():
      self.v3_user_value_to_v1_entity(v3_property_value.uservalue(),
                                      v1_value.entity_value)
      v1_value.meaning = MEANING_PREDEFINED_ENTITY_USER
      v3_meaning = None
    else:

      v1_value.null_value = googledatastore.NULL_VALUE

    if is_zlib_value:
      v1_value.meaning = MEANING_ZLIB
    elif v3_meaning:
      v1_value.meaning = v3_meaning


    if indexed == v1_value.exclude_from_indexes:
      v1_value.exclude_from_indexes = not indexed

  def v1_to_v3_property(self, property_name, is_multi, is_projection,
                        v1_value, v3_property):
    """Converts info from a v1 Property to a v3 Property.

    v1_value must not have an array_value.

    Args:
      property_name: the name of the property, unicode
      is_multi: whether the property contains multiple values
      is_projection: whether the property is projected
      v1_value: an googledatastore.Value
      v3_property: an entity_pb.Property to populate
    """
    v1_value_type = v1_value.WhichOneof('value_type')
    if v1_value_type == 'array_value':
      assert False, 'v1 array_value not convertable to v3'
    v3_property.Clear()
    v3_property.set_name(property_name.encode('utf-8'))
    v3_property.set_multiple(is_multi)
    self.v1_value_to_v3_property_value(v1_value, v3_property.mutable_value())

    v1_meaning = None
    if v1_value.meaning:
      v1_meaning = v1_value.meaning
    if v1_value_type == 'timestamp_value':
      v3_property.set_meaning(entity_pb.Property.GD_WHEN)
    elif v1_value_type == 'blob_value':
      if v1_meaning == MEANING_ZLIB:
        v3_property.set_meaning_uri(URI_MEANING_ZLIB)
      if v1_meaning == entity_pb.Property.BYTESTRING:
        if not v1_value.exclude_from_indexes:
          pass


      else:
        if not v1_value.exclude_from_indexes:
          v3_property.set_meaning(entity_pb.Property.BYTESTRING)
        else:
          v3_property.set_meaning(entity_pb.Property.BLOB)
        v1_meaning = None
    elif v1_value_type == 'entity_value':
      if v1_meaning != MEANING_PREDEFINED_ENTITY_USER:
        v3_property.set_meaning(entity_pb.Property.ENTITY_PROTO)
      v1_meaning = None
    elif v1_value_type == 'geo_point_value':
      if v1_meaning != MEANING_POINT_WITHOUT_V3_MEANING:
        v3_property.set_meaning(MEANING_GEORSS_POINT)
      v1_meaning = None
    else:

      pass
    if v1_meaning is not None:
      v3_property.set_meaning(v1_meaning)

    if is_projection:
      v3_property.set_meaning(entity_pb.Property.INDEX_VALUE)

  def __add_v1_property_to_entity(self, v1_entity, v3_property, indexed):
    """Adds a v1 Property to an entity or modifies an existing one.

    Args:
      v1_entity: an googledatastore.Entity
      v3_property: an entity_pb.Property to convert to v1 and add to the dict
      indexed: whether the property is indexed
    """
    property_name = v3_property.name()
    v1_value = v1_entity.properties[property_name]
    if v3_property.multiple():
      self.v3_property_to_v1_value(v3_property, indexed,
                                   v1_value.array_value.values.add())
    else:
      self.v3_property_to_v1_value(v3_property, indexed, v1_value)

  def __get_v1_integer_value(self, v1_value):
    """Returns an integer value from a v1 Value.

    Args:
      v1_value: a googledatastore.Value

    Returns:
      an integer

    Raises:
      InvalidConversionError: if the value doesn't contain an integer value
    """
    check_conversion(v1_value.HasField('integer_value'),
                     'Value does not contain an integer value.')
    return v1_value.integer_value

  def __get_v1_double_value(self, v1_value):
    """Returns a double value from a v1 Value.

    Args:
      v1_value: an googledatastore.Value

    Returns:
      a double

    Raises:
      InvalidConversionError: if the value doesn't contain a double value
    """
    check_conversion(v1_value.HasField('double_value'),
                     'Value does not contain a double value.')
    return v1_value.double_value

  def __get_v1_string_value(self, v1_value):
    """Returns an string value from a v1 Value.

    Args:
      v1_value: an googledatastore.Value

    Returns:
      a string

    Throws:
      InvalidConversionError: if the value doesn't contain a string value
    """
    check_conversion(v1_value.HasField('string_value'),
                     'Value does not contain a string value.')
    return v1_value.string_value

  def __v1_integer_property(self, entity, name, value, indexed):
    """Populates a single-integer-valued v1 Property.

    Args:
      entity: the entity to populate
      name: the name of the property to populate
      value: the integer value of the property
      indexed: whether the value should be indexed
    """
    v1_value = entity.properties[name]
    v1_value.exclude_from_indexes = not indexed
    v1_value.integer_value = value

  def __v1_double_property(self, entity, name, value, indexed):
    """Populates a single-double-valued v1 Property.

    Args:
      entity: the entity to populate
      name: the name of the property to populate
      value: the double value of the property
      indexed: whether the value should be indexed
    """
    v1_value = entity.properties[name]
    v1_value.exclude_from_indexes = not indexed
    v1_value.double_value = value

  def __v1_string_property(self, entity, name, value, indexed):
    """Populates a single-string-valued v1 Property.

    Args:
      entity: the entity to populate
      name: the name of the property to populate
      value: the string value of the property
      indexed: whether the value should be indexed
    """
    v1_value = entity.properties[name]
    v1_value.exclude_from_indexes = not indexed
    v1_value.string_value = value

  def v1_entity_to_v3_user_value(self, v1_user_entity, v3_user_value):
    """Converts a v1 user Entity to a v3 UserValue.

    Args:
      v1_user_entity: an googledatastore.Entity representing a user
      v3_user_value: an entity_pb.Property_UserValue to populate
    """
    v3_user_value.Clear()
    properties = v1_user_entity.properties

    v3_user_value.set_email(self.__get_v1_string_value(
        properties[PROPERTY_NAME_EMAIL]))
    v3_user_value.set_auth_domain(self.__get_v1_string_value(
        properties[PROPERTY_NAME_AUTH_DOMAIN]))
    if PROPERTY_NAME_USER_ID in properties:
      v3_user_value.set_obfuscated_gaiaid(
          self.__get_v1_string_value(properties[PROPERTY_NAME_USER_ID]))
    if PROPERTY_NAME_INTERNAL_ID in properties:
      v3_user_value.set_gaiaid(self.__get_v1_integer_value(
          properties[PROPERTY_NAME_INTERNAL_ID]))
    else:

      v3_user_value.set_gaiaid(0)
    if PROPERTY_NAME_FEDERATED_IDENTITY in properties:
      v3_user_value.set_federated_identity(
          self.__get_v1_string_value(properties[
              PROPERTY_NAME_FEDERATED_IDENTITY]))
    if PROPERTY_NAME_FEDERATED_PROVIDER in properties:
      v3_user_value.set_federated_provider(
          self.__get_v1_string_value(properties[
              PROPERTY_NAME_FEDERATED_PROVIDER]))

  def v3_user_value_to_v1_entity(self, v3_user_value, v1_entity):
    """Converts a v3 UserValue to a v1 user Entity.

    Args:
      v3_user_value: an entity_pb.Property_UserValue
      v1_entity: an googledatastore.Entity to populate
    """
    v1_entity.Clear()
    self.__v1_string_property(v1_entity, PROPERTY_NAME_EMAIL,
                              v3_user_value.email(), False)
    self.__v1_string_property(v1_entity, PROPERTY_NAME_AUTH_DOMAIN,
                              v3_user_value.auth_domain(), False)

    if v3_user_value.gaiaid() != 0:
      self.__v1_integer_property(
          v1_entity,
          PROPERTY_NAME_INTERNAL_ID,
          v3_user_value.gaiaid(),
          False)
    if v3_user_value.has_obfuscated_gaiaid():
      self.__v1_string_property(
          v1_entity,
          PROPERTY_NAME_USER_ID,
          v3_user_value.obfuscated_gaiaid(),
          False)
    if v3_user_value.has_federated_identity():
      self.__v1_string_property(
          v1_entity,
          PROPERTY_NAME_FEDERATED_IDENTITY,
          v3_user_value.federated_identity(),
          False)
    if v3_user_value.has_federated_provider():
      self.__v1_string_property(
          v1_entity,
          PROPERTY_NAME_FEDERATED_PROVIDER,
          v3_user_value.federated_provider(),
          False)

  def __is_v3_property_value_union_valid(self, v3_property_value):
    """Returns True if the v3 PropertyValue's union is valid."""
    num_sub_values = (v3_property_value.has_booleanvalue()
                      + v3_property_value.has_int64value()
                      + v3_property_value.has_doublevalue()
                      + v3_property_value.has_referencevalue()
                      + v3_property_value.has_stringvalue()
                      + v3_property_value.has_pointvalue()
                      + v3_property_value.has_uservalue())
    return num_sub_values <= 1

  def __is_v3_property_value_meaning_valid(self, v3_property_value, v3_meaning):
    """Returns True if the v3 PropertyValue's type value matches its meaning."""
    def ReturnTrue():
      return True
    def HasStringValue():
      return v3_property_value.has_stringvalue()
    def HasInt64Value():
      return v3_property_value.has_int64value()
    def HasPointValue():
      return v3_property_value.has_pointvalue()
    def ReturnFalse():
      return False
    value_checkers = {
        entity_pb.Property.NO_MEANING: ReturnTrue,
        entity_pb.Property.INDEX_VALUE: ReturnTrue,
        entity_pb.Property.BLOB: HasStringValue,
        entity_pb.Property.TEXT: HasStringValue,
        entity_pb.Property.BYTESTRING: HasStringValue,
        entity_pb.Property.ATOM_CATEGORY: HasStringValue,
        entity_pb.Property.ATOM_LINK: HasStringValue,
        entity_pb.Property.ATOM_TITLE: HasStringValue,
        entity_pb.Property.ATOM_CONTENT: HasStringValue,
        entity_pb.Property.ATOM_SUMMARY: HasStringValue,
        entity_pb.Property.ATOM_AUTHOR: HasStringValue,
        entity_pb.Property.GD_EMAIL: HasStringValue,
        entity_pb.Property.GD_IM: HasStringValue,
        entity_pb.Property.GD_PHONENUMBER: HasStringValue,
        entity_pb.Property.GD_POSTALADDRESS: HasStringValue,
        entity_pb.Property.BLOBKEY: HasStringValue,
        entity_pb.Property.ENTITY_PROTO: HasStringValue,
        entity_pb.Property.GD_WHEN: HasInt64Value,
        entity_pb.Property.GD_RATING: HasInt64Value,
        entity_pb.Property.GEORSS_POINT: HasPointValue,
        entity_pb.Property.EMPTY_LIST: ReturnTrue,
    }
    default = ReturnFalse
    return value_checkers.get(v3_meaning, default)()

  def __v3_reference_has_id_or_name(self, v3_ref):
    """Determines if a v3 Reference specifies an ID or name.

    Args:
      v3_ref: an entity_pb.Reference

    Returns:
      boolean: True if the last path element specifies an ID or name.
    """
    path = v3_ref.path()
    assert path.element_size() >= 1
    last_element = path.element(path.element_size() - 1)
    return last_element.has_id() or last_element.has_name()

  def v3_reference_to_group(self, v3_ref, group):
    """Converts a v3 Reference to a v3 Path representing the entity group.

    The entity group is represented as an entity_pb.Path containing only the
    first element in the provided Reference.

    Args:
      v3_ref: an entity_pb.Reference
      group: an entity_pb.Path to populate
    """
    group.Clear()
    path = v3_ref.path()
    assert path.element_size() >= 1
    group.add_element().CopyFrom(path.element(0))

  def v3_reference_to_v3_property_value(self, v3_ref, v3_property_value):
    """Converts a v3 Reference to a v3 PropertyValue.

    Args:
      v3_ref: an entity_pb.Reference
      v3_property_value: an entity_pb.PropertyValue to populate
    """
    v3_property_value.Clear()
    reference_value = v3_property_value.mutable_referencevalue()
    if v3_ref.has_app():
      reference_value.set_app(v3_ref.app())
    if v3_ref.has_name_space():
      reference_value.set_name_space(v3_ref.name_space())
    for v3_path_element in v3_ref.path().element_list():
      v3_ref_value_path_element = reference_value.add_pathelement()
      if v3_path_element.has_type():
        v3_ref_value_path_element.set_type(v3_path_element.type())
      if v3_path_element.has_id():
        v3_ref_value_path_element.set_id(v3_path_element.id())
      if v3_path_element.has_name():
        v3_ref_value_path_element.set_name(v3_path_element.name())

  def __v3_reference_value_to_v3_reference(self, v3_ref_value, v3_ref):
    """Converts a v3 ReferenceValue to a v3 Reference.

    Args:
      v3_ref_value: an entity_pb.PropertyValue_ReferenceValue
      v3_ref: an entity_pb.Reference to populate
    """
    v3_ref.Clear()
    if v3_ref_value.has_app():
      v3_ref.set_app(v3_ref_value.app())
    if v3_ref_value.has_name_space():
      v3_ref.set_name_space(v3_ref_value.name_space())
    for v3_ref_value_path_element in v3_ref_value.pathelement_list():
      v3_path_element = v3_ref.mutable_path().add_element()
      if v3_ref_value_path_element.has_type():
        v3_path_element.set_type(v3_ref_value_path_element.type())
      if v3_ref_value_path_element.has_id():
        v3_path_element.set_id(v3_ref_value_path_element.id())
      if v3_ref_value_path_element.has_name():
        v3_path_element.set_name(v3_ref_value_path_element.name())


class _QueryConverter(object):
  """Base converter for v3 and v1 queries."""

  def __init__(self, entity_converter):
    self._entity_converter = entity_converter

  def get_entity_converter(self):
    return self._entity_converter

  def _v3_filter_to_v1_property_filter(self, v3_filter, v1_property_filter):
    """Converts a v3 Filter to a v1 PropertyFilter.

    Args:
      v3_filter: a datastore_pb.Filter
      v1_property_filter: a googledatastore.PropertyFilter to populate

    Raises:
      InvalidConversionError if the filter cannot be converted
    """
    check_conversion(v3_filter.property_size() == 1,
                     'invalid filter')
    check_conversion(v3_filter.op() <= 5,
                     'unsupported filter op: %d' % v3_filter.op())
    v1_property_filter.Clear()
    v1_property_filter.op = v3_filter.op()
    v1_property_filter.property.name = v3_filter.property(0).name()
    self._entity_converter.v3_property_to_v1_value(
        v3_filter.property(0), True, v1_property_filter.value)

  def _v3_query_to_v1_ancestor_filter(self, v3_query, v1_property_filter):
    """Converts a v3 Query to a v1 ancestor PropertyFilter.

    Args:
      v3_query: a datastore_pb.Query
      v1_property_filter: a googledatastore.PropertyFilter to populate
    """
    v1_property_filter.Clear()
    v1_property_filter.set_operator(
        googledatastore.PropertyFilter.HAS_ANCESTOR)
    prop = v1_property_filter.property
    prop.set_name(PROPERTY_NAME_KEY)
    self._entity_converter.v3_to_v1_key(
        v3_query.ancestor(),
        v1_property_filter.value.mutable_key_value)

  def v3_order_to_v1_order(self, v3_order, v1_order):
    """Converts a v3 Query order to a v1 PropertyOrder.

    Args:
      v3_order: a datastore_pb.Query.Order
      v1_order: a googledatastore.PropertyOrder to populate
    """
    v1_order.property.name = v3_order.property()
    if v3_order.has_direction():
      v1_order.direction = v3_order.direction()

  def _v3_filter_to_v4_property_filter(self, v3_filter, v4_property_filter):
    """Converts a v3 Filter to a v4 PropertyFilter.

    Args:
      v3_filter: a datastore_pb.Filter
      v4_property_filter: a datastore_v4_pb.PropertyFilter to populate

    Raises:
      InvalidConversionError if the filter cannot be converted
    """
    check_conversion(v3_filter.property_size() == 1,
                     'invalid filter')
    check_conversion(v3_filter.op() <= 5,
                     'unsupported filter op: %d' % v3_filter.op())
    v4_property_filter.Clear()
    v4_property_filter.set_operator(v3_filter.op())
    v4_property_filter.mutable_property().set_name(v3_filter.property(0).name())
    self._entity_converter.v3_property_to_v4_value(
        v3_filter.property(0), True, v4_property_filter.mutable_value())

  def _v3_query_to_v4_ancestor_filter(self, v3_query, v4_property_filter):
    """Converts a v3 Query to a v4 ancestor PropertyFilter.

    Args:
      v3_query: a datastore_pb.Query
      v4_property_filter: a datastore_v4_pb.PropertyFilter to populate
    """
    v4_property_filter.Clear()
    v4_property_filter.set_operator(
        datastore_v4_pb.PropertyFilter.HAS_ANCESTOR)
    prop = v4_property_filter.mutable_property()
    prop.set_name(PROPERTY_NAME_KEY)
    self._entity_converter.v3_to_v4_key(
        v3_query.ancestor(),
        v4_property_filter.mutable_value().mutable_key_value())

  def v3_order_to_v4_order(self, v3_order, v4_order):
    """Converts a v3 Query order to a v4 PropertyOrder.

    Args:
      v3_order: a datastore_pb.Query.Order
      v4_order: a datastore_v4_pb.PropertyOrder to populate
    """
    v4_order.mutable_property().set_name(v3_order.property())
    if v3_order.has_direction():
      v4_order.set_direction(v3_order.direction())


def get_entity_converter(id_resolver=None):
  """Returns a converter for v3 and v1 entities and keys.

  Args:
    id_resolver: An IdResolver for project id resolution.
  """
  id_resolver = id_resolver or _IdentityIdResolver()
  return _EntityConverter(id_resolver)
