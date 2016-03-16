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





"""Bulkloader Transform Helper functions.

A collection of helper functions for bulkloading data, typically referenced
from a bulkloader.yaml file.
"""











import base64

import datetime
import os
import re
import tempfile

from google.appengine.api import datastore
from google.appengine.api import datastore_types
from google.appengine.ext.bulkload import bulkloader_errors



CURRENT_PROPERTY = None

KEY_TYPE_NAME = 'name'
KEY_TYPE_ID = 'ID'


# Decorators


def none_if_empty(fn):
  """A decorator which returns None if its input is empty else fn(x).

  Useful on import.  Can be used in config files
  (e.g. "transform.none_if_empty(int)" or as a decorator.

  Args:
    fn: Single argument transform function.

  Returns:
    Wrapped function.
  """

  def wrapper(value):


    if value == '' or value is None or value == []:
      return None
    return fn(value)

  return wrapper


def empty_if_none(fn):
  """A wrapper for a value to return '' if it's None. Useful on export.

  Can be used in config files (e.g. "transform.empty_if_none(unicode)" or
  as a decorator.

  Args:
    fn: Single argument transform function.

  Returns:
    Wrapped function.
  """

  def wrapper(value):

    if value is None:
      return ''
    return fn(value)

  return wrapper


# Key helpers.


def create_foreign_key(kind, key_is_id=False):
  """A method to make one-level Key objects.

  These are typically used in ReferenceProperty in Python, where the reference
  value is a key with kind (or model) name name.

  This helper method does not support keys with parents. Use create_deep_key
  instead to create keys with parents.

  Args:
    kind: The kind name of the reference as a string.
    key_is_id: If true, convert the key into an integer to be used as an id.
      If false, leave the key in the input format (typically a string).

  Returns:
    Single argument method which parses a value into a Key of kind entity_kind.
  """

  def generate_foreign_key_lambda(value):
    if key_is_id:
      value = int(value)
    return datastore.Key.from_path(kind, value)

  return generate_foreign_key_lambda


def create_deep_key(*path_info):
  """A method to make multi-level Key objects.

  Generates multi-level key from multiple fields in the input dictionary.

  This is typically used for Keys for entities which have variable parent keys,
  e.g. ones with owned relationships. It can used for both __key__ and
  references.

  Use create_foreign_key as a simpler way to create single level keys.

  Args:
    path_info: List of tuples, describing (kind, property, is_id=False).
      kind: The kind name.
      property: The external property in the current import dictionary, or
        transform.CURRENT_PROPERTY for the value passed to the transform.
      is_id: Converts value to int and treats as numeric ID if True, otherwise
        the value is a string name. Default is False.
      Example:
        create_deep_key(('rootkind', 'rootcolumn'),
                        ('childkind', 'childcolumn', True),
                        ('leafkind', transform.CURRENT_PROPERTY))

  Returns:
    Transform method which parses the info from the current neutral dictionary
    into a Key with parents as described by path_info.
  """

  validated_path_info = []
  for level_info in path_info:
    if len(level_info) == 3:
      key_is_id = level_info[2]
    elif len(level_info) == 2:
      key_is_id = False
    else:
      raise bulkloader_errors.InvalidConfiguration(
          'Each list in create_deep_key must specify exactly 2 or 3 '
          'parameters, (kind, property, is_id=False). You specified: %s' %
          repr(path_info))
    kind_name = level_info[0]
    property_name = level_info[1]
    validated_path_info.append((kind_name, property_name, key_is_id))

  def create_deep_key_lambda(value, bulkload_state):
    path = []
    for kind_name, property_name, key_is_id in validated_path_info:
      if property_name is CURRENT_PROPERTY:
        name_or_id = value
      else:
        name_or_id = bulkload_state.current_dictionary[property_name]

      if key_is_id:
        name_or_id = int(name_or_id)

      path += [kind_name, name_or_id]

    return datastore.Key.from_path(*path)

  return create_deep_key_lambda


def _key_id_or_name_n(key, index):
  """Internal helper function for key id and name transforms.

  Args:
    key: A datastore key.
    index: The depth in the key to return; 0 is root, -1 is leaf.

  Returns:
    The id or name of the nth deep sub key in key.
  """
  if not key:
    return None
  path = key.to_path()
  if not path:
    return None
  path_index = (index * 2) + 1
  return path[path_index]


def key_id_or_name_as_string_n(index):
  """Pull out the nth (0-based) key id or name from a key which has parents.

  If a key is present, return its id or name as a string.

  Note that this loses the distinction between integer IDs and strings
  which happen to look like integers. Use key_type to distinguish them.

  This is a useful complement to create_deep_key.

  Args:
    index: The depth of the id or name to extract. Zero is the root key.
        Negative one is the leaf key.

  Returns:
    Function extracting the name or ID of the key at depth index, as a unicode
    string. Returns '' if key is empty (unsaved), otherwise raises IndexError
    if the key is not as deep as described.
  """

  def transform_function(key):
    id_or_name = _key_id_or_name_n(key, index)
    if not id_or_name:
      return u''
    return unicode(id_or_name)

  return transform_function

# # Commonly used helper which returns the value of the leaf key.
key_id_or_name_as_string = key_id_or_name_as_string_n(-1)


def key_type_n(index):
  """Pull out the nth (0-based) key type from a key which has parents.

  This is most useful when paired with key_id_or_name_as_string_n.
  This is a useful complement to create_deep_key.

  Args:
    index: The depth of the id or name to extract. Zero is the root key.
        Negative one is the leaf key.

  Returns:
    Method returning the type ('ID' or 'name') of the key at depth index.
    Returns '' if key is empty (unsaved), otherwise raises IndexError
    if the key is not as deep as described.
  """

  def transform_function(key):
    id_or_name = _key_id_or_name_n(key, index)
    if id_or_name is None:
      return ''
    if isinstance(id_or_name, basestring):
      return KEY_TYPE_NAME
    return KEY_TYPE_ID

  return transform_function

# # Commonly used helper which returns the type of the leaf key.
key_type = key_type_n(-1)


def key_kind_n(index):
  """Pull out the nth (0-based) key kind from a key which has parents.

  This is a useful complement to create_deep_key.

  Args:
    index: The depth of the id or name to extract. Zero is the root key.
      Negative one is the leaf key.

  Returns:
    Function returning the kind of the key at depth index, or raising
    IndexError if the key is not as deep as described.
  """

  @empty_if_none
  def transform_function(key):
    path = key.to_path()
    path_index = (index * 2)
    return unicode(path[path_index])

  return transform_function

# Commonly used helper which returns the kind of the leaf key.
key_kind = key_kind_n(-1)


# Blob and ByteString helpers.


@none_if_empty
def blobproperty_from_base64(value):
  """Return a datastore blob property containing the base64 decoded value."""
  decoded_value = base64.b64decode(value)
  return datastore_types.Blob(decoded_value)


@none_if_empty
def bytestring_from_base64(value):
  """Return a datastore bytestring property from a base64 encoded value."""
  decoded_value = base64.b64decode(value)
  return datastore_types.ByteString(decoded_value)


def blob_to_file(filename_hint_propertyname=None,
                 directory_hint=''):
  """Write the blob contents to a file, and replace them with the filename.

  Args:
    filename_hint_propertyname: If present, the filename will begin with
      the contents of this value in the entity being exported.
    directory_hint: If present, the files will be stored in this directory.

  Returns:
    A function which writes the input blob to a file.
  """

  directory = []

  def transform_function(value, bulkload_state):
    if not directory:
      parent_dir = os.path.dirname(bulkload_state.filename)
      directory.append(os.path.join(parent_dir, directory_hint))
      if directory[0] and not os.path.exists(directory[0]):
        os.makedirs(directory[0])

    filename_hint = 'blob_'
    suffix = ''
    filename = ''
    if filename_hint_propertyname:
      filename_hint = bulkload_state.current_entity[filename_hint_propertyname]
      filename = os.path.join(directory[0], filename_hint)
      if os.path.exists(filename):
        filename = ''
        (filename_hint, suffix) = os.path.splitext(filename_hint)
    if not filename:
      filename = tempfile.mktemp(suffix, filename_hint, directory[0])
    f = open(filename, 'wb')
    f.write(value)
    f.close()
    return filename

  return transform_function


# Formatted string helpers: Extract, convert to boolean, date, or list.


def import_date_time(format, _strptime=None):
  """A wrapper around strptime. Also returns None if the input is empty.

  Args:
    format: Format string for strptime.

  Returns:
    Single argument method which parses a string into a datetime using format.
  """



  if not _strptime:
    _strptime = datetime.datetime.strptime

  def import_date_time_lambda(value):
    if not value:
      return None
    return _strptime(value, format)

  return import_date_time_lambda


def export_date_time(format):
  """A wrapper around strftime. Also returns '' if the input is None.

  Args:
    format: Format string for strftime.

  Returns:
    Single argument method which convers a datetime into a string using format.
  """

  def export_date_time_lambda(value):
    if not value:
      return ''
    return datetime.datetime.strftime(value, format)

  return export_date_time_lambda


def regexp_extract(pattern, method=re.match, group=1):
  """Return first group in the value matching the pattern using re.match.

  Args:
    pattern: A regular expression to match on with at least one group.
    method: The method to use for matching; normally re.match or re.search.
    group: The group to use for extracting a value.

  Returns:
    A single argument method which returns the group_arg group matched,
    or None if no match was found or the input was empty.
  """

  def regexp_extract_lambda(value):
    if not value:
      return None
    matches = method(pattern, value)
    if not matches:
      return None
    return matches.group(group)

  return regexp_extract_lambda


def regexp_to_list(pattern):
  """Return function that returns a list of objects that match the regex.

  Useful on import.  Uses the provided regex to split a string value into a list
  of strings.  Wrapped by none_if_input_or_result_empty, so returns none if
  there are no matches for the regex and none if the input is empty.

  Args:
    pattern: A regular expression pattern to match against the input string.

  Returns:
    None if the input was none or no matches were found, otherwise a list of
    strings matching the input expression.
  """
  @none_if_empty
  def regexp_to_list_lambda(value):
    result = re.findall(pattern, value)
    if result == []:
      return None
    return result

  return regexp_to_list_lambda


def regexp_bool(regexp, flags=0):
  """Return a boolean if the expression matches with re.match.

  Note that re.match anchors at the start but not end of the string.

  Args:
    regexp: String, regular expression.
    flags: Optional flags to pass to re.match.

  Returns:
    Method which returns a Boolean if the expression matches.
  """

  def transform_function(value):
    return bool(re.match(regexp, value, flags))

  return transform_function


def split_string(delimeter):
  """Split a string using the delimeter into a list.

  This is just a wrapper for string.split.

  Args:
    delimeter: The delimiter to split the string on.

  Returns:
    Method which splits the string into a list along the delimeter.
  """

  def split_string_lambda(value):
    return value.split(delimeter)

  return split_string_lambda


def join_list(delimeter):
  """Join a list into a string using the delimeter.

  This is just a wrapper for string.join.

  Args:
    delimeter: The delimiter to use when joining the string.

  Returns:
    Method which joins the list into a string with the delimeter.
  """

  def join_string_lambda(value):
    return delimeter.join(value)

  return join_string_lambda


def list_from_multiproperty(*external_names):
  """Create a list from multiple properties.

  Args:
    external_names: List of the properties to use.

  Returns:
    Transform function which returns a list of the properties in external_names.
  """

  def list_from_multiproperty_lambda(unused_value, bulkload_state):
    result = []
    for external_name in external_names:
      value = bulkload_state.current_dictionary.get(external_name)
      if value:
        result.append(value)
    return result

  return list_from_multiproperty_lambda


def property_from_list(index):
  """Return the Nth item from a list, or '' if the list is shorter.

  Args:
    index: Item in the list to return.

  Returns:
    Function returning the item from a list, or '' if the list is too short.
  """

  @empty_if_none
  def property_from_list_lambda(values):
    if len(values) > index:
      return values[index]
    return ''

  return property_from_list_lambda


# SimpleXML list Helpers


def list_from_child_node(xpath, suppress_blank=False):
  """Return a list property from child nodes of the current xml node.

  This applies only the simplexml helper, as it assumes __node__, the current
  ElementTree node corresponding to the import record.

  Sample usage for structure:
   <Visit>
    <VisitActivities>
     <Activity>A1</Activity>
     <Activity>A2</Activity>
    </VisitActivities>
   </Visit>

  property: activities
  external_name: VisitActivities # Ignored on import, used on export.
  import_transform: list_from_xml_node('VisitActivities/Activity')
  export_transform: child_node_from_list('Activity')

  Args:
    xpath: XPath to run on the current node.
    suppress_blank: if True, ndoes with no text will be skipped.

  Returns:
    Transform function which works as described in the args.
  """

  def list_from_child_node_lambda(unused_value, bulkload_state):
    result = []
    for node in bulkload_state.current_dictionary['__node__'].findall(xpath):
      if node.text:
        result.append(node.text)
      elif not suppress_blank:
        result.append('')
    return result

  return list_from_child_node_lambda


def child_node_from_list(child_node_name):
  """Return a value suitable for generating an XML child node on export.

  The return value is a list of tuples which the simplexml connector will
  use to build a child node.

  See also list_from_child_node

  Args:
    child_node_name: The name to use for each child node.

  Returns:
    Transform function which works as described in the args.
  """

  def child_node_from_list_lambda(values):
    return [(child_node_name, value) for value in values]

  return child_node_from_list_lambda
