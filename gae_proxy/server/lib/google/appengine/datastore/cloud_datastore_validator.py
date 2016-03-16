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




"""Validators for v1 datastore protocol buffers.

This module is internal and should not be used by client applications.
"""

















import re

from google.appengine.api import datastore_types
from google.appengine.datastore import datastore_pbs
if datastore_pbs._CLOUD_DATASTORE_ENABLED:
  from google.appengine.datastore.datastore_pbs import googledatastore




_PROJECT_ID_DOMAIN_STRING = (
    r'[a-z\d][a-z\d\-\.]{0,%d}'
    % (datastore_pbs.MAX_DATASET_ID_SECTION_LENGTH - 1))

_PROJECT_ID_DISPLAY_STRING = (
    r'[a-z\d][a-z\d\-]{0,%d}'
    % (datastore_pbs.MAX_DATASET_ID_SECTION_LENGTH - 1))

_PROJECT_ID_STRING = ('(%s\:)?%s'
                      % (_PROJECT_ID_DOMAIN_STRING,
                         _PROJECT_ID_DISPLAY_STRING))


_PROJECT_ID_RE = re.compile('^%s$' % _PROJECT_ID_STRING)


_RESERVED_NAME_RE = re.compile('^__(.*)__$')


_PARTITION_DIMENSION_RE = re.compile(r'^[0-9A-Za-z\._\-]{0,%d}$'
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
  _assert_condition(string, 'The %s is missing.' % desc)


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


UPSERT = _ValidationConstraint(
    absent_key_allowed=False,
    incomplete_key_path_allowed=True,
    complete_key_path_allowed=True,
    reserved_key_allowed=False,
    reserved_property_name_allowed=False,
    meaning_index_only_allowed=False)


UPSERT_ENTITY_IN_VALUE = _ValidationConstraint(
    absent_key_allowed=True,
    incomplete_key_path_allowed=True,
    complete_key_path_allowed=True,
    reserved_key_allowed=True,
    reserved_property_name_allowed=False,
    meaning_index_only_allowed=False)


UPDATE = _ValidationConstraint(
    absent_key_allowed=False,
    incomplete_key_path_allowed=False,
    complete_key_path_allowed=True,
    reserved_key_allowed=False,
    reserved_property_name_allowed=False,
    meaning_index_only_allowed=False)


DELETE = _ValidationConstraint(
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
    UPSERT: UPSERT_ENTITY_IN_VALUE,
    UPDATE: WRITE_ENTITY_IN_VALUE,
    WRITE_ENTITY_IN_VALUE: WRITE_ENTITY_IN_VALUE,
    UPSERT_ENTITY_IN_VALUE: UPSERT_ENTITY_IN_VALUE,
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
  """Validator for datastore entities and keys."""

  def validate_keys(self, constraint, keys):
    """Validates a list of keys.

    Args:
      constraint: a _ValidationConstraint to apply
      keys: a list of googledatastore.Key objects

    Raises:
      ValidationError: if any of the keys is invalid
    """
    for key in keys:
      self.validate_key(constraint, key)

  def validate_key(self, constraint, key):
    """Validates a key.

    Args:
      constraint: a _ValidationConstraint to apply
      key: an googledatastore.Key

    Raises:
      ValidationError: if the key is invalid
    """
    _assert_condition(key.HasField('partition_id'),
                      'Key is missing partition id.')
    self.validate_partition_id(constraint, key.partition_id)
    num_key_path_elements = len(key.path)
    _assert_condition(num_key_path_elements, 'Key path is empty.')
    _assert_condition((num_key_path_elements
                       <= datastore_pbs.MAX_KEY_PATH_LENGTH),
                      ('Key path has more than %d elements.'
                       % datastore_pbs.MAX_KEY_PATH_LENGTH))
    num_incomplete_elements = 0
    for path_element in key.path:
      _assert_valid_utf8(path_element.kind, 'key path kind')
      kind = path_element.kind
      self.validate_kind(constraint, kind)
      type = path_element.WhichOneof('id_type')
      if  type == 'name':
        _assert_valid_utf8(path_element.name, 'key path name')
        name = path_element.name
        _assert_string_not_empty(name, 'key path name')
        _assert_string_not_too_long(name,
                                    datastore_pbs.MAX_INDEXED_STRING_CHARS,
                                    'key path name')
        if not constraint.reserved_key_allowed:
          _assert_string_not_reserved(name, 'key path name')
      elif type == 'id':
        _assert_condition(path_element.id, 'Key path id cannot be zero.')
      else:
        num_incomplete_elements += 1
    final_element = key.path[num_key_path_elements - 1]
    final_element_complete = (final_element.WhichOneof('id_type'))
    if not constraint.complete_key_path_allowed:
      _assert_condition(not final_element_complete,
                        'Key path is complete: %s.'
                        % datastore_pbs.v1_key_to_string(key))
    if not constraint.incomplete_key_path_allowed:
      _assert_condition(final_element_complete,
                        'Key path is incomplete: %s.'
                        % datastore_pbs.v1_key_to_string(key))
    if final_element_complete:
      num_expected_incomplete = 0
    else:
      num_expected_incomplete = 1
    if num_incomplete_elements != num_expected_incomplete:

      _assert_condition(False, 'Key path element is incomplete: %s.'
                        % datastore_pbs.v1_key_to_string(key))

  def validate_partition_id(self, constraint, partition_id):
    """Validates a partition ID.

    Args:
      constraint: a _ValidationConstraint to apply
      partition_id: a googledatastore.PartitionId

    Raises:
      ValidationError: if the partition ID is invalid
    """
    self.validate_project_id(constraint, partition_id.project_id)
    self.validate_partition_id_dimension(constraint,
                                         partition_id.namespace_id,
                                         'namespace')

  def validate_project_id(self, constraint, project_id):
    """Validates a project ID.

    Args:
      constraint: a _ValidationConstraint to apply
      project_id: project ID

    Raises:
      ValidationError: if the partition ID dimension is invalid
    """
    _assert_condition(project_id, 'The project id is missing')
    _assert_valid_utf8(project_id, 'project id')
    _assert_string_not_too_long(project_id, datastore_pbs.MAX_DATASET_ID_LENGTH,
                                'project id')
    _assert_condition(_PROJECT_ID_RE.match(project_id),
                      'Illegal string "%s" in project id.' % project_id)



    if not constraint.reserved_key_allowed:
      _assert_string_not_reserved(project_id, 'project id')

  def validate_partition_id_dimension(self, constraint, partition_dimension,
                                      desc):
    """Validates a dimension (e.g. namespace_id) of a partition ID.

    Should not be used for datasets (see validate_dataset).

    Args:
      constraint: a _ValidationConstraint to apply
      partition_dimension: string representing one dimension of a partition ID
      desc: description of the dimension (used in error messages)

    Raises:
      ValidationError: if the partition ID dimension is invalid
    """
    _assert_valid_utf8(partition_dimension, desc)
    _assert_string_not_too_long(partition_dimension,
                                datastore_pbs.MAX_PARTITION_ID_LENGTH, desc)
    if not constraint.reserved_key_allowed:
      _assert_string_not_reserved(partition_dimension, desc)
    _assert_condition(_PARTITION_DIMENSION_RE.match(partition_dimension),
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
    _assert_string_not_empty(kind, 'kind name')
    _assert_string_not_too_long(kind, datastore_pbs.MAX_INDEXED_STRING_CHARS,
                                'kind name')
    if not constraint.reserved_key_allowed:
      _assert_string_not_reserved(kind, 'kind name')

  def validate_entities(self, constraint, entities):
    """Validates a list of entities.

    Args:
      constraint: a _ValidationConstraint to apply
      entities: a list of googledatastore.Entity objects

    Raises:
      ValidationError: if any of the entities is invalid
    """
    for entity in entities:
      self.validate_entity(constraint, entity)

  def validate_entity(self, constraint, entity):
    """Validates an entity.

    Args:
      constraint: a _ValidationConstraint to apply
      entity: an googledatastore.Entity

    Raises:
      ValidationError: if the entity is invalid
    """
    if entity.HasField('key'):
      self.validate_key(constraint, entity.key)
    else:
      _assert_condition(constraint.absent_key_allowed,
                        'Entity is missing key.')
    for name, value in entity.properties.iteritems():
      self.validate_property_name(constraint, name)
      self.validate_value(constraint, value)

  def validate_property(self, constraint, prop):
    """Validates a property.

    Args:
      constraint: a _ValidationConstraint to apply
      prop: an googledatastore.PropertiesEntry

    Raises:
      ValidationError: if the property is invalid
    """
    self.validate_property_name(constraint, prop.key)
    _assert_condition(prop.HasField('value'),
                      'Property "%s" has no value.' % prop.key)
    self.validate_value(constraint, prop.value)

  def validate_value(self, constraint, value):
    """Validates a value.

    Args:
      constraint: a _ValidationConstraint to apply
      value: an googledatastore.Value

    Raises:
      ValidationError: if the value is invalid
    """
    if value.HasField('string_value'):
      _assert_valid_utf8(value.string_value, 'string value')
    elif value.HasField('key_value'):
      self.validate_key(KEY_IN_VALUE, value.key_value)
    elif value.HasField('geo_point_value'):
      if value.meaning != datastore_pbs.MEANING_POINT_WITHOUT_V3_MEANING:
        _assert_condition(abs(value.geo_point_value.latitude) <= 90.0,
                          'Latitude outside permitted range [-90.0, 90.0].')
        _assert_condition(abs(value.geo_point_value.longitude) <= 180.0,
                          'Longitude outside permitted range [-180.0, 180.0].')
    elif value.HasField('entity_value'):
      entity_in_value_constraint = _get_entity_in_value_constraint(constraint)
      self.validate_entity(entity_in_value_constraint, value.entity_value)
    elif value.HasField('array_value'):
      _assert_condition(not value.exclude_from_indexes,
                        ('A Value containing a array_value cannot specify '
                         'exclude_from_indexes.'))
      _assert_condition(not value.meaning,
                        ('A Value containing a array_value cannot specify '
                         'a meaning.'))
      for sub_value in value.array_value.values:
        _assert_condition(not sub_value.HasField('array_value'),
                          ('array_value cannot contain a Value containing '
                           'another array_value.'))
        self.validate_value(constraint, sub_value)
    self.__validate_value_meaning_matches_union(value)
    self.__validate_value_meaning_constraints(constraint, value)
    self.__validate_value_index_constraints(value)

  def __validate_value_meaning_matches_union(self, value):
    """Validates that a value's meaning matches its value type.

    Args:
      value: an googledatastore.Value

    Raises:
      ValidationError: if the Value's value type does not match its meaning
    """
    if not value.meaning:
      return
    message = 'Value meaning %d does not match %s field.'
    meaning = value.meaning
    field = value.WhichOneof('value_type')
    if meaning in _STRING_VALUE_MEANINGS:
      _assert_condition(field == 'string_value',
                        message % (meaning, 'string_value'))
    elif meaning in _BLOB_VALUE_MEANINGS:
      _assert_condition(field == 'blob_value',
                        message % (meaning, 'blob_value'))
    elif meaning == datastore_pbs.MEANING_PREDEFINED_ENTITY_USER:
      _assert_condition(field == 'entity_value',
                        message % (meaning, 'entity_value'))
    elif meaning == datastore_pbs.MEANING_POINT_WITHOUT_V3_MEANING:
      _assert_condition(field == 'geo_point_value',
                        message % (meaning, 'geo_point_value'))
    elif meaning == datastore_pbs.MEANING_PERCENT:
      _assert_condition(field == 'integer_value',
                        message % (meaning, 'integer_value'))
    elif meaning == datastore_pbs.MEANING_INDEX_ONLY:
      _assert_condition(field != 'timestamp_value',
                        message % (meaning, 'timestamp_value'))
      _assert_condition(field != 'entity_value',
                        message % (meaning, 'entity_value'))
    elif meaning == datastore_pbs.MEANING_BLOBKEY:
      _assert_condition(field == 'string_value',
                         message % (meaning, 'string_value'))
    else:
      _assert_condition(False,
                        'Unknown value meaning %d' % meaning)

  def __validate_value_meaning_constraints(self, constraint, value):
    """Checks constraints on values that result from their meaning.

    For example, some meanings cause the length of a value to be constrained.

    Args:
      constraint: a _ValidationConstraint to apply
      value: an googledatastore.Value

    Raises:
      ValidationError: if the value is invalid
    """
    meaning = value.meaning
    if not meaning:
      return
    if meaning == datastore_pbs.MEANING_BYTESTRING:
      _assert_condition((len(value.blob_value)
                         <= datastore_pbs.MAX_INDEXED_BLOB_BYTES),
                        ('Blob value with meaning %d has more than '
                         'permitted %d bytes.'
                         % (meaning, datastore_pbs.MAX_INDEXED_BLOB_BYTES)))
    elif meaning in (datastore_pbs.MEANING_TEXT, datastore_pbs.MEANING_ZLIB):
      _assert_condition(value.exclude_from_indexes,
                        'Indexed value has meaning %d.' % meaning)
    elif meaning == datastore_pbs.MEANING_URL:
      _assert_condition((len(value.string_value)
                         <= datastore_pbs.MAX_URL_CHARS),
                        'URL value has more than permitted %d characters.'
                        % datastore_pbs.MAX_URL_CHARS)
    elif meaning == datastore_pbs.MEANING_PERCENT:
      _assert_condition((value.integer_value >= 0
                         and value.integer_value <= 100),
                        'Percent value outside permitted range [0, 100].')
    elif meaning == datastore_pbs.MEANING_PREDEFINED_ENTITY_USER:
      self._validate_predefined_entity_value(value.entity_value, 'user',
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
      entity: the predefined entity (an googledatastore.Entity)
      entity_name: the name of the entity (used in error messages)
      allowed_property_map: a dict whose keys are property names allowed in
          the entity and values are the expected types of these properties
      required_properties: a list of required property names

    Returns:
      a dict of googledatastore.Value objects keyed by property name

    Raises:
      ValidationError: if the entity is invalid
    """
    _assert_condition(not entity.HasField('key'),
                      'The %s entity has a key.' % entity_name)
    property_map = {}
    for property_name, value in entity.properties.iteritems():
      _assert_condition(property_name in allowed_property_map,
                        'The %s entity property "%s" is not allowed.'
                        % (entity_name, property_name))
      value = entity.properties[property_name]
      hasser = 'hasField(\'%s_value\')' % allowed_property_map[property_name]
      _assert_condition(
          value.HasField('%s_value' % allowed_property_map[property_name]),
          ('The %s entity property "%s" is the wrong type.'
           % (entity_name, property_name)))
      _assert_condition(not value.meaning,
                        'The %s entity property "%s" has a meaning.'
                        % (entity_name, property_name))
      _assert_condition(value.exclude_from_indexes,
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
      value: an googledatastore.Value

    Raises:
      ValidationError: if the value is invalid
    """
    if value.exclude_from_indexes:
      return
    if (value.HasField('string_value')
        and value.meaning != datastore_pbs.MEANING_URL):

      _assert_condition((len(value.string_value)
                         <= datastore_pbs.MAX_INDEXED_STRING_CHARS),
                        ('Indexed string value has more than %d permitted '
                         'characters.'
                         % datastore_pbs.MAX_INDEXED_STRING_CHARS))
    elif value.HasField('blob_value'):
      _assert_condition((len(value.blob_value)
                         <= datastore_pbs.MAX_INDEXED_BLOB_BYTES),
                        ('Indexed blob value has more than %d permitted '
                         'bytes.' % datastore_pbs.MAX_INDEXED_BLOB_BYTES))
    elif value.HasField('entity_value'):
      _assert_condition(value.meaning,
                        'Entity value is indexed.')

  def validate_property_name(self, constraint, property_name):
    """Validates a property name.

    Args:
      constraint: a _ValidationConstraint to apply
      property_name: name of a property

    Raises:
      ValidationError: if the property name is invalid
    """
    desc = 'property name'
    _assert_condition(property_name, 'The property name is missing')
    _assert_string_not_too_long(property_name,
                                datastore_pbs.MAX_INDEXED_STRING_CHARS, desc)
    _assert_valid_utf8(property_name, desc)


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
      query: a googledatastore.Query
      is_strong_read_consistency: whether the request containing the query
          requested strong read consistency

    Raises:
      ValidationError: if the query is invalid
    """
    _assert_condition((not is_strong_read_consistency
                       or self._has_ancestor(query.filter)),
                      'Global queries do not support strong consistency.')
    if query.HasField('filter'):
      self.validate_filter(query.filter)
    for kind_expression in query.kind:
      self.__validate_kind_expression(kind_expression)
    for property_reference in query.distinct_on:
      self.__validate_property_reference(property_reference)
    for property_expression in query.projection:
      self.__validate_projection(property_expression)
    for property_order in query.order:
      self.__validate_property_order(property_order)

  def validate_filter(self, filt):
    """Validates a Filter.

    Args:
      filt: a googledatastore.Filter

    Raises:
      ValidationError: if the filter is invalid
    """
    filter_type = filt.WhichOneof('filter_type')
    _assert_condition(filter_type,
                      'A filter must have exactly one of its fields set.')
    if filter_type == 'composite_filter':
      comp_filter = filt.composite_filter
      _assert_condition(comp_filter.filters,
                        'A composite filter must have at least one sub-filter.')
      for sub_filter in comp_filter.filters:
        self.validate_filter(sub_filter)
    elif filter_type == 'property_filter':
      prop_filter = filt.property_filter
      self.__validate_property_reference(prop_filter.property)
      _assert_condition(not prop_filter.value.exclude_from_indexes,
                        'A filter value must be indexed.')
      self.__entity_validator.validate_value(READ,
                                             prop_filter.value)

  def __validate_kind_expression(self, kind_expression):
    """Validates a KindExpression.

    Args:
      kind_expression: a googledatastore.KindExpression

    Raises:
      ValidationError: if the kind expression is invalid
    """
    _assert_valid_utf8(kind_expression.name, 'kind')
    self.__entity_validator.validate_kind(READ,
                                          kind_expression.name)

  def __validate_projection(self, projection):
    """Validates a Projection.

    Args:
      projection: a googledatastore.Projection

    Raises:
      ValidationError: if the property expression is invalid
    """
    self.__validate_property_reference(projection.property)

  def __validate_property_reference(self, property_reference):
    """Validates a PropertyReference.

    Args:
      property_reference: a googledatastore.PropertyReference

    Raises:
      ValidationError: if the property reference is invalid
    """
    self.__entity_validator.validate_property_name(READ,
                                                   property_reference.name)

  def __validate_property_order(self, property_order):
    """Validates a PropertyOrder.

    Args:
      property_order: a googledatastore.PropertyOrder

    Raises:
      ValidationError: if the property expression is invalid
    """
    self.__validate_property_reference(property_order.property)

  def _has_ancestor(self, filt):
    """Determines if a filter includes an ancestor filter.

    Args:
      filt: a googledatastore.Filter

    Returns:
      True if the filter includes an ancestor filter, False otherwise
    """
    if filt.HasField('property_filter'):
      op = filt.property_filter.op
      name = filt.property_filter.property.name
      return (op == googledatastore.PropertyFilter.HAS_ANCESTOR
              and name == datastore_pbs.PROPERTY_NAME_KEY)
    if filt.HasField('composite_filter'):
      if (filt.composite_filter.op
          == googledatastore.CompositeFilter.AND):
        for sub_filter in filt.composite_filter.filters:
          if self._has_ancestor(sub_filter):
            return True
    return False



__query_validator = _QueryValidator(__entity_validator)


def get_query_validator():
  """Validator for queries."""
  return __query_validator


class _ServiceValidator(object):
  """Validator for request/response protos."""

  def __init__(self, entity_validator, query_validator, id_resolver):
    self.__entity_validator = entity_validator
    self.__query_validator = query_validator
    self.__id_resolver = id_resolver

  def validate_begin_transaction_req(self, req):
    """Validates a normalized BeginTransactionRequest.

    Args:
      req: a googledatastore.BeginTransactionRequest

    Raises:
      ValidationError: if the request is invalid
    """
    _assert_initialized(req)

  def validate_rollback_req(self, req):
    """Validates a normalized RunQueryRequest.

    Args:
      req: a googledatastore.RunQueryRequest

    Raises:
      ValidationError: if the request is invalid
    """
    _assert_initialized(req)
    _assert_condition(req.transaction, 'Invalid transaction')

  def validate_commit_req(self, req):
    """Validates a normalized CommitRequest.

    Args:
      req: a googledatastore.CommitRequest

    Raises:
      ValidationError: if the request is invalid
    """
    _assert_initialized(req)
    if (req.mode == googledatastore.CommitRequest.MODE_UNSPECIFIED or
        req.mode == googledatastore.CommitRequest.TRANSACTIONAL):
      _assert_condition(req.WhichOneof('transaction_selector'),
                        'Transactional commit requires a transaction.')
      if req.WhichOneof('transaction_selector') == 'transaction':
        _assert_condition(req.transaction, 'a transaction cannot be the empty '
                                           'string.')


      seen_base_versions = {}
      for mutation in req.mutations:
        v1_key, _ = datastore_pbs.get_v1_mutation_key_and_entity(mutation)
        if datastore_pbs.is_complete_v1_key(v1_key):
          mutation_base_version = None
          if mutation.HasField('base_version'):
            mutation_base_version = mutation.base_version

          key = datastore_types.ReferenceToKeyValue(v1_key, self.__id_resolver)
          if key in seen_base_versions:
            _assert_condition(seen_base_versions[key] == mutation_base_version,
                              'Mutations for the same entity must have the '
                              'same base version.')
          seen_base_versions[key] = mutation_base_version

    elif req.mode == googledatastore.CommitRequest.NON_TRANSACTIONAL:
      _assert_condition(not req.WhichOneof('transaction_selector'),
                        'Non-transactional commit cannot specify a '
                        'transaction.')

      seen_complete_keys = set()
      for mutation in req.mutations:
        v1_key, _ = datastore_pbs.get_v1_mutation_key_and_entity(mutation)
        if datastore_pbs.is_complete_v1_key(v1_key):
          key = datastore_types.ReferenceToKeyValue(v1_key, self.__id_resolver)
          _assert_condition(key not in seen_complete_keys,
                            'A non-transactional commit may not contain '
                            'multiple mutations affecting the same entity.')
          seen_complete_keys.add(key)

    for mutation in req.mutations:
      self.__validate_mutation(mutation)

  def validate_run_query_req(self, req):
    """Validates a normalized RunQueryRequest.

    Args:
      req: a normalized googledatastore.RunQueryRequest

    Raises:
      ValidationError: if the request is invalid
    """



    _assert_condition(not req.HasField('gql_query'), 'GQL not supported.')
    _assert_initialized(req)
    self.__validate_read_options(req.read_options)
    self.__entity_validator.validate_partition_id(READ,
                                                  req.partition_id)
    _assert_condition(req.HasField('query'),
                      ('One of fields Query.query and Query.gql_query '
                       'must be set.'))
    self.__query_validator.validate_query(
        req.query,
        (req.read_options.read_consistency
         == googledatastore.ReadOptions.STRONG))

  def validate_lookup_req(self, req):
    """Validates a LookupRequest.

    Args:
      req: a googledatastore.LookupRequest

    Raises:
      ValidationError: if the request is invalid
    """
    _assert_initialized(req)
    self.__validate_read_options(req.read_options)
    self.__entity_validator.validate_keys(READ, req.keys)

  def validate_allocate_ids_req(self, req):
    """Validates an AllocateIdsRequest.

    Args:
      req: a googledatastore.AllocateIdsRequest

    Raises:
      ValidationError: if the request is invalid
    """
    _assert_initialized(req)
    self.__entity_validator.validate_keys(ALLOCATE_KEY_ID,
                                          req.keys)

  def __validate_mutation(self, mutation):
    if mutation.HasField('insert'):

      self.__entity_validator.validate_entity(UPSERT, mutation.insert)
      mutation_key = mutation.insert.key
    elif mutation.HasField('update'):
      self.__entity_validator.validate_entity(UPDATE, mutation.update)
      mutation_key = mutation.update.key
    elif mutation.HasField('upsert'):
      self.__entity_validator.validate_entity(UPSERT, mutation.upsert)
      mutation_key = mutation.upsert.key
    elif mutation.HasField('delete'):
      self.__entity_validator.validate_key(DELETE, mutation.delete)
      mutation_key = mutation.delete
    else:
      _assert_condition(False, 'mutation lacks required op')

    if mutation.WhichOneof('conflict_detection_strategy') != None:
      _assert_condition(datastore_pbs.is_complete_v1_key(mutation_key),
                        'conflict detection is not allowed for incomplete keys')
    if mutation.HasField('base_version'):
      _assert_condition(mutation.base_version >= 0,
                        'Invalid base_version: %d, '
                        'it should be >= 0' % mutation.base_version)

  def __validate_read_options(self, read_options):
    if read_options.WhichOneof('consistency_type') == 'transaction':
      _assert_condition(read_options.transaction, 'a transaction cannot be the '
                                                  'the empty string.')


def get_service_validator(id_resolver):
  """Returns a validator for v1 service request/response protos.

  Args:
    id_resolver: a datastore_pbs.IdResolver.

  Returns:
    a _ServiceValidator
  """
  return _ServiceValidator(__entity_validator, __query_validator, id_resolver)
