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




"""Validators for v4 datastore protocol buffers.

This module is internal and should not be used by client applications.
"""

















import re

from google.appengine.datastore import datastore_pbs
from google.appengine.datastore import datastore_v4_pb



_DATASET_ID_PARTITION_STRING = (r'[a-z\d\-]{1,%d}'
                                % datastore_pbs.MAX_DATASET_ID_SECTION_LENGTH)

_DATASET_ID_DOMAIN_STRING = (
    r'[a-z\d][a-z\d\-\.]{0,%d}'
    % (datastore_pbs.MAX_DATASET_ID_SECTION_LENGTH - 1))

_DATASET_ID_DISPLAY_STRING = (
    r'[a-z\d][a-z\d\-]{0,%d}'
    % (datastore_pbs.MAX_DATASET_ID_SECTION_LENGTH - 1))

_DATASET_ID_STRING = ('(?:(?:%s)~)?(?:(?:%s):)?(?:%s)'
                      % (_DATASET_ID_PARTITION_STRING,
                         _DATASET_ID_DOMAIN_STRING,
                         _DATASET_ID_DISPLAY_STRING))


_DATASET_ID_RE = re.compile('^%s$' % _DATASET_ID_STRING)


_RESERVED_NAME_RE = re.compile('^__(.*)__$')


_PARTITION_ID_RE = re.compile(r'^[0-9A-Za-z\._\-]{0,%d}$'
                              % datastore_pbs.MAX_PARTITION_ID_LENGTH)


_STRING_VALUE_MEANINGS = frozenset([
    datastore_pbs.MEANING_TEXT,
    datastore_pbs.MEANING_ATOM_CATEGORY,
    datastore_pbs.MEANING_URL,
    datastore_pbs.MEANING_ATOM_TITLE,
    datastore_pbs.MEANING_ATOM_CONTENT,
    datastore_pbs.MEANING_ATOM_SUMMARY,
    datastore_pbs.MEANING_ATOM_AUTHOR,
    datastore_pbs.MEANING_GD_EMAIL,
    datastore_pbs.MEANING_GD_IM,
    datastore_pbs.MEANING_GD_PHONENUMBER,
    datastore_pbs.MEANING_GD_POSTALADDRESS,
    ])


_BLOB_VALUE_MEANINGS = frozenset([
    datastore_pbs.MEANING_BYTESTRING,
    datastore_pbs.MEANING_ZLIB,
    ])


_ENTITY_VALUE_MEANINGS = frozenset([
    datastore_pbs.MEANING_GEORSS_POINT,
    datastore_pbs.MEANING_PREDEFINED_ENTITY_POINT,
    datastore_pbs.MEANING_PREDEFINED_ENTITY_USER,
    ])


_USER_ENTITY_PROPERTY_MAP = {
    datastore_pbs.PROPERTY_NAME_EMAIL: 'string',
    datastore_pbs.PROPERTY_NAME_AUTH_DOMAIN: 'string',
    datastore_pbs.PROPERTY_NAME_USER_ID: 'string',
    datastore_pbs.PROPERTY_NAME_INTERNAL_ID: 'integer',
    datastore_pbs.PROPERTY_NAME_FEDERATED_IDENTITY: 'string',
    datastore_pbs.PROPERTY_NAME_FEDERATED_PROVIDER: 'string',
    }


_USER_ENTITY_REQUIRED_PROPERTIES = frozenset([
    datastore_pbs.PROPERTY_NAME_EMAIL,
    datastore_pbs.PROPERTY_NAME_AUTH_DOMAIN,
    ])


_POINT_ENTITY_PROPERTY_MAP = {
    datastore_pbs.PROPERTY_NAME_X: 'double',
    datastore_pbs.PROPERTY_NAME_Y: 'double',
    }


_POINT_ENTITY_REQUIRED_PROPERTIES = frozenset([
    datastore_pbs.PROPERTY_NAME_X,
    datastore_pbs.PROPERTY_NAME_Y,
    ])



class ValidationError(Exception):
  """Raised when validation fails."""
  pass


def _assert_condition(condition, message):
  """Asserts a validation condition and raises an error if it's not met.

  Args:
    condition: (boolean) condition to enforce
    message: error message

  Raises:
    ValidationError: if condition is not met
  """
  if not condition:
    raise ValidationError(message)


def _assert_initialized(pb):
  """Asserts that a protocol buffer is initialized.

  Args:
    pb: a protocol buffer

  Raises:
    ValidationError: if protocol buffer is not initialized
  """
  errors = []
  if not pb.IsInitialized(errors):
    _assert_condition(False, '\n\t'.join(errors))


def _assert_valid_utf8(string, desc):
  """Asserts that a string is valid UTF8.

  Args:
    string: string to check
    desc: description of the string (used in error message)

  Raises:
    ValidationError: if the string is not valid UTF8
  """
  _assert_condition(datastore_pbs.is_valid_utf8(string),
                    'The %s is not valid UTF-8.' % desc)


def _assert_string_not_empty(string, desc):
  """Asserts that a string is not empty.

  Args:
    string: string to check
    desc: description of the string (used in error message)

  Raises:
    ValidationError: if the string is empty
  """
  _assert_condition(string, 'The %s is the empty string.' % desc)


def _assert_string_not_reserved(string, desc):
  """Asserts that a string is not a reserved name.

  Args:
    string: string to check
    desc: description of the string (used in error message)

  Raises:
    ValidationError: if the string is a reserved name
  """
  _assert_condition(not _RESERVED_NAME_RE.match(string),
                    'The %s "%s" is reserved.'  % (desc, string))


def _assert_string_not_too_long(string, max_length, desc):
  """Asserts that a string is within the maximum string size bounds.

  Args:
    string: string to check
    max_length: max length of the string (inclusive)
    desc: description of the string (used in error message)

  Raises:
    ValidationError: if the string is a reserved name
  """
  _assert_condition(len(string) <= max_length,
                    'The %s is longer than %d characters.' % (desc, max_length))


class _ValidationConstraint(object):
  """Container for a set of validation constraints."""

  def __init__(self, absent_key_allowed=False, incomplete_key_path_allowed=True,
               complete_key_path_allowed=False, reserved_key_allowed=False,
               reserved_property_name_allowed=False,
               meaning_index_only_allowed=False):
    self.__absent_key_allowed = absent_key_allowed
    self.__incomplete_key_path_allowed = incomplete_key_path_allowed
    self.__complete_key_path_allowed = complete_key_path_allowed
    self.__reserved_key_allowed = reserved_key_allowed
    self.__reserved_property_name_allowed = reserved_property_name_allowed
    self.__meaning_index_only_allowed = meaning_index_only_allowed

  @property
  def absent_key_allowed(self):
    """Allow keys to be absent from entities."""
    return self.__absent_key_allowed

  @property
  def incomplete_key_path_allowed(self):
    """Allow key paths to be incomplete."""
    return self.__incomplete_key_path_allowed

  @property
  def complete_key_path_allowed(self):
    """Allow key paths to be complete."""
    return self.__complete_key_path_allowed

  @property
  def reserved_key_allowed(self):
    """Allow reserved keys and reserved partition ids."""
    return self.__reserved_key_allowed

  @property
  def reserved_property_name_allowed(self):
    """Allow reserved property names."""
    return self.__reserved_property_name_allowed

  @property
  def meaning_index_only_allowed(self):
    """Allow the index only meaning."""
    return self.__meaning_index_only_allowed

  def __hash__(self):
    return hash(id(self))

  def __eq__(self, other):
    return self is other



READ = _ValidationConstraint(
    absent_key_allowed=False,
    incomplete_key_path_allowed=False,
    complete_key_path_allowed=True,
    reserved_key_allowed=True,
    reserved_property_name_allowed=True,
    meaning_index_only_allowed=True)



READ_ENTITY_IN_VALUE = _ValidationConstraint(
    absent_key_allowed=True,
    incomplete_key_path_allowed=True,
    complete_key_path_allowed=True,
    reserved_key_allowed=True,
    reserved_property_name_allowed=True,
    meaning_index_only_allowed=True)


WRITE = _ValidationConstraint(
    absent_key_allowed=False,
    incomplete_key_path_allowed=False,
    complete_key_path_allowed=True,
    reserved_key_allowed=False,
    reserved_property_name_allowed=False,
    meaning_index_only_allowed=False)


WRITE_ENTITY_IN_VALUE = _ValidationConstraint(
    absent_key_allowed=True,
    incomplete_key_path_allowed=True,
    complete_key_path_allowed=True,
    reserved_key_allowed=True,
    reserved_property_name_allowed=False,
    meaning_index_only_allowed=False)


ALLOCATE_KEY_ID = _ValidationConstraint(
    absent_key_allowed=False,
    incomplete_key_path_allowed=True,
    complete_key_path_allowed=False,
    reserved_key_allowed=False,
    reserved_property_name_allowed=False,
    meaning_index_only_allowed=False)


WRITE_AUTO_ID = _ValidationConstraint(
    absent_key_allowed=False,
    incomplete_key_path_allowed=True,
    complete_key_path_allowed=False,
    reserved_key_allowed=False,
    reserved_property_name_allowed=False,
    meaning_index_only_allowed=False)


KEY_IN_VALUE = _ValidationConstraint(
    absent_key_allowed=False,
    incomplete_key_path_allowed=False,
    complete_key_path_allowed=True,
    reserved_key_allowed=True,
    reserved_property_name_allowed=True,
    meaning_index_only_allowed=False)


_ENTITY_IN_VALUE_CONSTRAINTS = {
    READ: READ_ENTITY_IN_VALUE,
    READ_ENTITY_IN_VALUE: READ_ENTITY_IN_VALUE,
    WRITE: WRITE_ENTITY_IN_VALUE,
    WRITE_AUTO_ID: WRITE_ENTITY_IN_VALUE,
    WRITE_ENTITY_IN_VALUE: WRITE_ENTITY_IN_VALUE,
}


def _get_entity_in_value_constraint(constraint):
  """Returns the corresponding constraint for entities in values.

  Args:
    constraint: a _ValidationConstraint

  Returns:
    a _ValidationConstraint for entities in values

  Raises:
    ValueError: if no corresponding constraint exists
  """
  if constraint not in _ENTITY_IN_VALUE_CONSTRAINTS:
    raise ValueError('No corresponding constraint for entities in values.')
  return _ENTITY_IN_VALUE_CONSTRAINTS[constraint]











class _EntityValidator(object):
  """Validator for v4 entities and keys."""

  def validate_keys(self, constraint, keys):
    """Validates a list of keys.

    Args:
      constraint: a _ValidationConstraint to apply
      keys: a list of entity_v4_pb.Key objects

    Raises:
      ValidationError: if any of the keys is invalid
    """
    for key in keys:
      self.validate_key(constraint, key)

  def validate_key(self, constraint, key):
    """Validates a key.

    Args:
      constraint: a _ValidationConstraint to apply
      key: an entity_v4_pb.Key

    Raises:
      ValidationError: if the key is invalid
    """
    _assert_condition(key.has_partition_id(), 'Key is missing partition id.')
    self.validate_partition_id(constraint, key.partition_id())
    num_key_path_elements = len(key.path_element_list())
    _assert_condition(num_key_path_elements, 'Key path is empty.')
    _assert_condition((num_key_path_elements
                       <= datastore_pbs.MAX_KEY_PATH_LENGTH),
                      ('Key path has more than %d elements.'
                       % datastore_pbs.MAX_KEY_PATH_LENGTH))
    num_incomplete_elements = 0
    for path_element in key.path_element_list():
      _assert_valid_utf8(path_element.kind(), 'key path kind')
      kind = path_element.kind()
      self.validate_kind(constraint, kind)
      has_name = path_element.has_name()
      if path_element.has_id():
        _assert_condition(not has_name,
                          'Key path element has both id (%d) and name ("%s").'
                          % (path_element.id(), path_element.name()))
        _assert_condition(path_element.id(),
                          'Key path element has an id of 0.')
      else:
        if has_name:
          _assert_valid_utf8(path_element.name(), 'key path name')
          name = path_element.name()
          _assert_string_not_empty(name, 'key path name')
          _assert_string_not_too_long(name,
                                      datastore_pbs.MAX_INDEXED_STRING_CHARS,
                                      'key path name')
          if not constraint.reserved_key_allowed:
            _assert_string_not_reserved(name, 'key path name')
        else:
          num_incomplete_elements += 1
    final_element = key.path_element(num_key_path_elements - 1)
    final_element_complete = final_element.has_id() or final_element.has_name()
    if not constraint.complete_key_path_allowed:
      _assert_condition(not final_element_complete,
                        'Key path is complete: %s.'
                        % datastore_pbs.v4_key_to_string(key))
    if not constraint.incomplete_key_path_allowed:
      _assert_condition(final_element_complete,
                        'Key path is incomplete: %s.'
                        % datastore_pbs.v4_key_to_string(key))
    if final_element_complete:
      num_expected_incomplete = 0
    else:
      num_expected_incomplete = 1
    if num_incomplete_elements != num_expected_incomplete:

      _assert_condition(False, 'Key path element is incomplete: %s.'
                        % datastore_pbs.v4_key_to_string(key))

  def validate_partition_id(self, constraint, partition_id):
    """Validates a partition ID.

    Args:
      constraint: a _ValidationConstraint to apply
      partition_id: a datastore_v4_pb.PartitionId

    Raises:
      ValidationError: if the partition ID is invalid
    """
    _assert_condition(partition_id.has_dataset_id(),
                      'Partition id is missing dataset id.')
    if partition_id.has_dataset_id():
      self.validate_dataset_id(constraint, partition_id.dataset_id())
    if partition_id.has_namespace():
      self.validate_partition_id_dimension(constraint, partition_id.namespace(),
                                           'namespace')

  def validate_dataset_id(self, constraint, dataset_id):
    """Validates a dataset ID.

    Args:
      constraint: a _ValidationConstraint to apply
      dataset_id: dataset ID

    Raises:
      ValidationError: if the partition ID dimension is invalid
    """
    _assert_valid_utf8(dataset_id, 'dataset id')
    _assert_string_not_empty(dataset_id, 'dataset id')
    _assert_string_not_too_long(dataset_id, datastore_pbs.MAX_DATASET_ID_LENGTH,
                                'dataset id')
    _assert_condition(_DATASET_ID_RE.match(dataset_id),
                      'Illegal string "%s" in dataset id.' % dataset_id)



    if not constraint.reserved_key_allowed:
      _assert_string_not_reserved(dataset_id, 'dataset id')

  def validate_partition_id_dimension(self, constraint, partition_dimension,
                                      desc):
    """Validates a dimension (e.g. namespace) of a partition ID.

    Should not be used for datasets (see validate_dataset).

    Args:
      constraint: a _ValidationConstraint to apply
      partition_dimension: string representing one dimension of a partition ID
      desc: description of the dimension (used in error messages)

    Raises:
      ValidationError: if the partition ID dimension is invalid
    """
    _assert_valid_utf8(partition_dimension, desc)
    _assert_string_not_empty(partition_dimension, desc)
    _assert_string_not_too_long(partition_dimension,
                                datastore_pbs.MAX_PARTITION_ID_LENGTH, desc)
    if not constraint.reserved_key_allowed:
      _assert_string_not_reserved(partition_dimension, desc)
    _assert_condition(_PARTITION_ID_RE.match(partition_dimension),
                      'Illegal string "%s" in %s.' % (partition_dimension,
                                                      desc))

  def validate_kind(self, constraint, kind):
    """Validates a kind.

    Args:
      constraint: a _ValidationConstraint to apply
      kind: kind string

    Raises:
      ValidationError: if the kind is invalid
    """
    _assert_string_not_empty(kind, 'kind')
    _assert_string_not_too_long(kind, datastore_pbs.MAX_INDEXED_STRING_CHARS,
                                'kind')
    if not constraint.reserved_key_allowed:
      _assert_string_not_reserved(kind, 'kind')

  def validate_entities(self, constraint, entities):
    """Validates a list of entities.

    Args:
      constraint: a _ValidationConstraint to apply
      entities: a list of entity_v4_pb.Entity objects

    Raises:
      ValidationError: if any of the entities is invalid
    """
    for entity in entities:
      self.validate_entity(constraint, entity)

  def validate_entity(self, constraint, entity):
    """Validates an entity.

    Args:
      constraint: a _ValidationConstraint to apply
      entity: an entity_v4_pb.Entity

    Raises:
      ValidationError: if the entity is invalid
    """
    if entity.has_key():
      self.validate_key(constraint, entity.key())
    else:
      _assert_condition(constraint.absent_key_allowed,
                        'Entity is missing key.')
    property_names = set()
    for prop in entity.property_list():
      property_name = prop.name()
      _assert_condition(property_name not in property_names,
                        ('Entity has duplicate property name "%s".'
                         % property_name))
      property_names.add(property_name)
      self.validate_property(constraint, prop)

  def validate_property(self, constraint, prop):
    """Validates a property.

    Args:
      constraint: a _ValidationConstraint to apply
      prop: an entity_v4_pb.Property

    Raises:
      ValidationError: if the property is invalid
    """
    _assert_valid_utf8(prop.name(), 'property name')
    property_name = prop.name()
    self.validate_property_name(constraint, property_name)

    _assert_condition(not prop.has_deprecated_multi(),
                      'deprecated_multi field not supported.')
    _assert_condition(not prop.deprecated_value_list(),
                      'deprecated_value field not supported.')
    _assert_condition(prop.has_value(),
                      'Property "%s" has no value.' % property_name)
    self.validate_value(constraint, prop.value())

  def validate_value(self, constraint, value):
    """Validates a value.

    Args:
      constraint: a _ValidationConstraint to apply
      value: an entity_v4_pb.Value

    Raises:
      ValidationError: if the value is invalid
    """
    self.__validate_value_union(value)
    if value.has_string_value():
      _assert_valid_utf8(value.string_value(), 'string value')
    elif value.has_blob_key_value():
      _assert_valid_utf8(value.blob_key_value(), 'blob key value')
    elif value.has_key_value():
      self.validate_key(KEY_IN_VALUE, value.key_value())
    elif value.has_entity_value():
      entity_in_value_constraint = _get_entity_in_value_constraint(constraint)
      self.validate_entity(entity_in_value_constraint, value.entity_value())
    elif value.list_value_list():
      _assert_condition(not value.has_indexed(),
                        ('A Value containing a list_value cannot specify '
                         'indexed.'))
      _assert_condition(not value.has_meaning(),
                        ('A Value containing a list_value cannot specify '
                         'a meaning.'))
      for sub_value in value.list_value_list():
        _assert_condition(not sub_value.list_value_list(),
                          ('list_value cannot contain a Value containing '
                           'another list_value.'))
        self.validate_value(constraint, sub_value)
    self.__validate_value_meaning_matches_union(value)
    self.__validate_value_meaning_constraints(constraint, value)
    self.__validate_value_index_constraints(value)

  def __validate_value_union(self, value):
    """Validates that a value is a valid union.

    Args:
      value: an entity_v4_pb.Value

    Raises:
      ValidationError: if the value contains more than one type
    """
    num_sub_values = (value.has_boolean_value()
                      + value.has_integer_value()
                      + value.has_double_value()
                      + value.has_timestamp_microseconds_value()
                      + value.has_key_value()
                      + value.has_blob_key_value()
                      + value.has_string_value()
                      + value.has_blob_value()
                      + value.has_entity_value()
                      + bool(value.list_value_list()))
    _assert_condition(num_sub_values <= 1,
                      'Value has multiple <type>_value fields set.')
    return num_sub_values

  def __validate_value_meaning_matches_union(self, value):
    """Validates that a value's meaning matches its value type.

    Args:
      value: an entity_v4_pb.Value

    Raises:
      ValidationError: if the Value's value type does not match its meaning
    """
    if not value.has_meaning():
      return
    message = 'Value meaning %d does not match %s field.'
    meaning = value.meaning()
    if meaning in _STRING_VALUE_MEANINGS:
      _assert_condition(value.has_string_value(),
                        message % (meaning, 'string_value'))
    elif meaning in _BLOB_VALUE_MEANINGS:
      _assert_condition(value.has_blob_value(),
                        message % (meaning, 'blob_value'))
    elif meaning in _ENTITY_VALUE_MEANINGS:
      _assert_condition(value.has_entity_value(),
                        message % (meaning, 'entity_value'))
    elif meaning == datastore_pbs.MEANING_PERCENT:
      _assert_condition(value.has_integer_value(),
                        message % (meaning, 'integer_value'))
    elif meaning == datastore_pbs.MEANING_INDEX_ONLY:
      _assert_condition(not value.has_timestamp_microseconds_value(),
                        message % (meaning, 'timestamp_microseconds_value'))
      _assert_condition(not value.has_blob_key_value(),
                        message % (meaning, 'blob_key_value'))
      _assert_condition(not value.has_entity_value(),
                        message % (meaning, 'entity_value'))
    elif meaning == datastore_pbs.MEANING_EMPTY_LIST:
      _assert_condition(self.__validate_value_union(value) == 0,
                        'Empty list cannot have any value fields set.')
    else:
      _assert_condition(False,
                        'Unknown value meaning %d' % meaning)

  def __validate_value_meaning_constraints(self, constraint, value):
    """Checks constraints on values that result from their meaning.

    For example, some meanings cause the length of a value to be constrained.

    Args:
      constraint: a _ValidationConstraint to apply
      value: an entity_v4_pb.Value

    Raises:
      ValidationError: if the value is invalid
    """
    if not value.has_meaning():
      return
    meaning = value.meaning()
    if meaning == datastore_pbs.MEANING_BYTESTRING:
      _assert_condition((len(value.blob_value())
                         <= datastore_pbs.MAX_INDEXED_BLOB_BYTES),
                        ('Blob value with meaning %d has more than '
                         'permitted %d bytes.'
                         % (meaning, datastore_pbs.MAX_INDEXED_BLOB_BYTES)))
    elif meaning in (datastore_pbs.MEANING_TEXT, datastore_pbs.MEANING_ZLIB):
      _assert_condition(not value.indexed(),
                        'Indexed value has meaning %d.' % meaning)
    elif meaning == datastore_pbs.MEANING_URL:
      _assert_condition((len(value.string_value())
                         <= datastore_pbs.MAX_URL_CHARS),
                        'URL value has more than permitted %d characters.'
                        % datastore_pbs.MAX_URL_CHARS)
    elif meaning == datastore_pbs.MEANING_PERCENT:
      _assert_condition((value.integer_value() >= 0
                         and value.integer_value() <= 100),
                        'Percent value outside permitted range [0, 100].')
    elif meaning == datastore_pbs.MEANING_GEORSS_POINT:
      property_map = self._validate_predefined_entity_value(
          value.entity_value(), 'geo point', _POINT_ENTITY_PROPERTY_MAP,
          _POINT_ENTITY_REQUIRED_PROPERTIES)
      latitude = property_map[datastore_pbs.PROPERTY_NAME_X].double_value()
      longitude = property_map[datastore_pbs.PROPERTY_NAME_Y].double_value()
      _assert_condition(abs(latitude) <= 90.0,
                        'Latitude outside permitted range [-90.0, 90.0].')
      _assert_condition(abs(longitude) <= 180.0,
                        'Longitude outside permitted range [-180.0, 180.0].')
    elif meaning == datastore_pbs.MEANING_PREDEFINED_ENTITY_POINT:
      self._validate_predefined_entity_value(value.entity_value(), 'point',
                                             _POINT_ENTITY_PROPERTY_MAP,
                                             _POINT_ENTITY_REQUIRED_PROPERTIES)
    elif meaning == datastore_pbs.MEANING_PREDEFINED_ENTITY_USER:
      self._validate_predefined_entity_value(value.entity_value(), 'user',
                                             _USER_ENTITY_PROPERTY_MAP,
                                             _USER_ENTITY_REQUIRED_PROPERTIES)
    elif meaning == datastore_pbs.MEANING_INDEX_ONLY:
      _assert_condition(constraint.meaning_index_only_allowed,
                        'Value has meaning %d.'
                        % datastore_pbs.MEANING_INDEX_ONLY)

  def _validate_predefined_entity_value(self, entity, entity_name,
                                        allowed_property_map,
                                        required_properties):
    """Validates a predefined entity (e.g. a user or a point).

    Args:
      entity: the predefined entity (an entity_v4_pb.Entity)
      entity_name: the name of the entity (used in error messages)
      allowed_property_map: a dict whose keys are property names allowed in
          the entity and values are the expected types of these properties
      required_properties: a list of required property names

    Returns:
      a dict of entity_v4_pb.Value objects keyed by property name

    Raises:
      ValidationError: if the entity is invalid
    """
    _assert_condition(not entity.has_key(),
                      'The %s entity has a key.' % entity_name)
    property_map = {}
    for prop in entity.property_list():
      property_name = prop.name()
      _assert_condition(property_name in allowed_property_map,
                        'The %s entity property "%s" is not allowed.'
                        % (entity_name, property_name))
      value = prop.value()
      hasser = 'has_%s_value' % allowed_property_map[property_name]
      _assert_condition(
          getattr(value, hasser)(),
          ('The %s entity property "%s" is the wrong type.'
           % (entity_name, property_name)))
      _assert_condition(not value.has_meaning(),
                        'The %s entity property "%s" has a meaning.'
                        % (entity_name, property_name))
      _assert_condition(not value.indexed(),
                        'The %s entity property "%s" is indexed.'
                        % (entity_name, property_name))
      property_map[property_name] = value
    for required_property_name in required_properties:
      _assert_condition(required_property_name in property_map,
                        'The %s entity is missing required property "%s".'
                        % (entity_name, required_property_name))
    return property_map

  def __validate_value_index_constraints(self, value):
    """Checks constraints on values that result from their being indexed.

    Args:
      value: an entity_v4_pb.Value

    Raises:
      ValidationError: if the value is invalid
    """
    if not value.indexed():
      return
    if (value.has_string_value()
        and value.meaning() != datastore_pbs.MEANING_URL):

      _assert_condition((len(value.string_value())
                         <= datastore_pbs.MAX_INDEXED_STRING_CHARS),
                        ('Indexed string value has more than %d permitted '
                         'characters.'
                         % datastore_pbs.MAX_INDEXED_STRING_CHARS))
    elif value.has_blob_value():
      _assert_condition((len(value.blob_value())
                         <= datastore_pbs.MAX_INDEXED_BLOB_BYTES),
                        ('Indexed blob value has more than %d permitted '
                         'bytes.' % datastore_pbs.MAX_INDEXED_BLOB_BYTES))
    elif value.has_entity_value():
      _assert_condition(value.has_meaning(),
                        'Entity value is indexed.')

  def validate_property_name(self, constraint, property_name):
    """Validates a property name.

    Args:
      constraint: a _ValidationConstraint to apply
      property_name: name of a property

    Raises:
      ValidationError: if the property name is invalid
    """
    desc = 'property.name'
    _assert_string_not_empty(property_name, desc)
    _assert_string_not_too_long(property_name,
                                datastore_pbs.MAX_INDEXED_STRING_CHARS, desc)


    if not constraint.reserved_property_name_allowed:
      _assert_string_not_reserved(property_name, desc)



__entity_validator = _EntityValidator()


def get_entity_validator():
  """Validator for entities and keys."""
  return __entity_validator



class _QueryValidator(object):
  """Validator for queries."""

  def __init__(self, entity_validator):
    self.__entity_validator = entity_validator

  def validate_query(self, query, is_strong_read_consistency):
    """Validates a Query.

    Args:
      query: a datastore_v4_pb.Query
      is_strong_read_consistency: whether the request containing the query
          requested strong read consistency

    Raises:
      ValidationError: if the query is invalid
    """
    _assert_condition((not is_strong_read_consistency
                       or self._has_ancestor(query.filter())),
                      'Global queries do not support strong consistency.')
    if query.has_filter():
      self.validate_filter(query.filter())
    for kind_expression in query.kind_list():
      self.__validate_kind_expression(kind_expression)
    group_by_properties = set()
    for property_reference in query.group_by_list():
      self.__validate_property_reference(property_reference)
      group_by_properties.add(property_reference.name())
    for property_expression in query.projection_list():
      self.__validate_property_expression(property_expression,
                                          group_by_properties)
    for property_order in query.order_list():
      self.__validate_property_order(property_order)

  def validate_filter(self, filt):
    """Validates a Filter.

    Args:
      filt: a datastore_v4_pb.Filter

    Raises:
      ValidationError: if the filter is invalid
    """
    _assert_condition((filt.has_composite_filter()
                       + filt.has_property_filter() == 1),
                      'A filter must have exactly one of its fields set.')
    if filt.has_composite_filter():
      comp_filter = filt.composite_filter()
      _assert_condition(comp_filter.filter_list(),
                        'A composite filter must have at least one sub-filter.')
      for sub_filter in comp_filter.filter_list():
        self.validate_filter(sub_filter)
    elif filt.has_property_filter():
      prop_filter = filt.property_filter()
      self.__validate_property_reference(prop_filter.property())
      _assert_condition(prop_filter.value().indexed(),
                        'A filter value must be indexed.')
      self.__entity_validator.validate_value(READ,
                                             prop_filter.value())

  def __validate_kind_expression(self, kind_expression):
    """Validates a KindExpression.

    Args:
      kind_expression: a datastore_v4_pb.KindExpression

    Raises:
      ValidationError: if the kind expression is invalid
    """
    _assert_valid_utf8(kind_expression.name(), 'kind')
    self.__entity_validator.validate_kind(READ,
                                          kind_expression.name())

  def __validate_property_reference(self, property_reference):
    """Validates a PropertyReference.

    Args:
      property_reference: a datastore_v4_pb.PropertyReference

    Raises:
      ValidationError: if the property reference is invalid
    """
    _assert_valid_utf8(property_reference.name(), 'property name')
    self.__entity_validator.validate_property_name(READ,
                                                   property_reference.name())

  def __validate_property_expression(self, property_expression,
                                     group_by_properties):
    """Validates a PropertyExpression.

    Args:
      property_expression: a datastore_v4_pb.PropertyExpression
      group_by_properties: the set of property names specified as group by
          properties for the query

    Raises:
      ValidationError: if the property expression is invalid
    """
    self.__validate_property_reference(property_expression.property())
    if not group_by_properties:
      _assert_condition(not property_expression.has_aggregation_function(),
                        'Aggregation function is not allowed without group by.')
    elif property_expression.property().name() in group_by_properties:
      _assert_condition(not property_expression.has_aggregation_function(),
                        ('Aggregation function is not allowed for properties '
                         'in group by: %s.'
                         % property_expression.property().name()))
    else:
      _assert_condition(property_expression.has_aggregation_function(),
                        ('Aggregation function is required for properties '
                         'not in group by: %s.'
                         % property_expression.property().name()))

  def __validate_property_order(self, property_order):
    """Validates a PropertyOrder.

    Args:
      property_order: a datastore_v4_pb.PropertyOrder

    Raises:
      ValidationError: if the property expression is invalid
    """
    self.__validate_property_reference(property_order.property())

  def _has_ancestor(self, filt):
    """Determines if a filter includes an ancestor filter.

    Args:
      filt: a datastore_v4_pb.Filter

    Returns:
      True if the filter includes an ancestor filter, False otherwise
    """
    if filt.has_property_filter():
      op = filt.property_filter().operator()
      name = filt.property_filter().property().name()
      return (op == datastore_v4_pb.PropertyFilter.HAS_ANCESTOR
              and name == datastore_pbs.PROPERTY_NAME_KEY)
    if filt.has_composite_filter():
      if (filt.composite_filter().operator()
          == datastore_v4_pb.CompositeFilter.AND):
        for sub_filter in filt.composite_filter().filter_list():
          if self._has_ancestor(sub_filter):
            return True
    return False



__query_validator = _QueryValidator(__entity_validator)


def get_query_validator():
  """Validator for queries."""
  return __query_validator


class _ServiceValidator(object):
  """Validator for request/response protos."""

  def __init__(self, entity_validator, query_validator):
    self.__entity_validator = entity_validator
    self.__query_validator = query_validator

  def validate_begin_transaction_req(self, req):
    """Validates a normalized BeginTransactionRequest.

    Args:
      req: a datastore_v4_pb.BeginTransactionRequest

    Raises:
      ValidationError: if the request is invalid
    """
    _assert_initialized(req)

  def validate_rollback_req(self, req):
    """Validates a normalized RunQueryRequest.

    Args:
      req: a datastore_v4_pb.RunQueryRequest

    Raises:
      ValidationError: if the request is invalid
    """
    _assert_initialized(req)

  def validate_commit_req(self, req):
    """Validates a normalized CommitRequest.

    Args:
      req: a datastore_v4_pb.CommitRequest

    Raises:
      ValidationError: if the request is invalid
    """
    _assert_initialized(req)
    if req.mode() == datastore_v4_pb.CommitRequest.TRANSACTIONAL:
      _assert_condition(req.has_transaction(),
                        'Transactional commit requires a transaction.')
    elif req.mode() == datastore_v4_pb.CommitRequest.NON_TRANSACTIONAL:
      _assert_condition(not req.has_transaction(),
                        ('Non-transactional commit cannot specify a '
                         'transaction.'))
    else:
      _assert_condition(False,
                        'Unknown commit mode: %d.' % req.mode())
    self.__validate_deprecated_mutation(req.deprecated_mutation())

  def validate_run_query_req(self, req):
    """Validates a normalized RunQueryRequest.

    Args:
      req: a normalized datastore_v4_pb.RunQueryRequest

    Raises:
      ValidationError: if the request is invalid
    """



    _assert_condition(not req.has_gql_query(), 'GQL not supported.')
    _assert_initialized(req)
    self.validate_read_options(req.read_options())
    self.__entity_validator.validate_partition_id(READ,
                                                  req.partition_id())
    _assert_condition(req.has_query(),
                      ('One of fields Query.query and Query.gql_query '
                       'must be set.'))
    self.__query_validator.validate_query(
        req.query(),
        (req.read_options().read_consistency()
         == datastore_v4_pb.ReadOptions.STRONG))

  def validate_continue_query_req(self, req):
    _assert_initialized(req)

  def validate_lookup_req(self, req):
    """Validates a LookupRequest.

    Args:
      req: a datastore_v4_pb.LookupRequest

    Raises:
      ValidationError: if the request is invalid
    """
    _assert_initialized(req)
    self.validate_read_options(req.read_options())
    self.__entity_validator.validate_keys(READ, req.key_list())

  def validate_allocate_ids_req(self, req):
    """Validates an AllocateIdsRequest.

    Args:
      req: a datastore_v4_pb.AllocateIdsRequest

    Raises:
      ValidationError: if the request is invalid
    """
    _assert_initialized(req)
    _assert_condition(not req.allocate_list() or not req.reserve_list(),
                      'Cannot reserve and allocate ids in the same request.')
    self.__entity_validator.validate_keys(ALLOCATE_KEY_ID,
                                          req.allocate_list())
    self.__entity_validator.validate_keys(WRITE,
                                          req.reserve_list())

  def validate_read_options(self, read_options):
    _assert_condition((not read_options.has_read_consistency()
                       or not read_options.has_transaction()),
                      ('Cannot specify both a read consistency and'
                       ' a transaction.'))

  def __validate_deprecated_mutation(self, deprecated_mutation):
    self.__entity_validator.validate_entities(WRITE,
                                              deprecated_mutation.upsert_list())
    self.__entity_validator.validate_entities(WRITE,
                                              deprecated_mutation.update_list())
    self.__entity_validator.validate_entities(WRITE,
                                              deprecated_mutation.insert_list())
    self.__entity_validator.validate_entities(
        WRITE_AUTO_ID,
        deprecated_mutation.insert_auto_id_list())
    self.__entity_validator.validate_keys(WRITE,
                                          deprecated_mutation.delete_list())



__service_validator = _ServiceValidator(__entity_validator,
                                        __query_validator)


def get_service_validator():
  """Returns a validator for v4 service request/response protos.

  Returns:
    a _ServiceValidator
  """
  return __service_validator
