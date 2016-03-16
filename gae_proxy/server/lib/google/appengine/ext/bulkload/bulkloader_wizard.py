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





"""Wizard to generate bulkloader configuration.

Helper functions to call from the bulkloader.yaml.
The wizard is run by having bulkloader.py download datastore statistics
(https://developers.google.com/appengine/docs/python/datastore/stats,
specifically __Stat_PropertyType_PropertyName_Kind__) configured with
bulkloader_wizard.yaml.
"""


PROPERTY_DUPE_WARNING = (
    '    # Warning: This property is a duplicate, but with a different type.\n'
    '    # TODO: Edit this transform so only one property with this name '
    'remains.\n')

KIND_PREAMBLE = """
- kind: %(kind_name)s
  connector: # TODO: Choose a connector here: csv, simplexml, etc...
  connector_options:
    # TODO: Add connector options here--these are specific to each connector.
  property_map:
    - property: __key__
      external_name: key
      export_transform: transform.key_id_or_name_as_string

"""


class StatPostTransform(object):
  """Create text to insert between properties and filter out 'bad' properties.

  This class is a callable post_export_function which saves state
  across multiple calls.

  It uses this saved state to determine if each entity is the first entity seen
  of a new kind, a duplicate kind/propertyname entry, or just a new property
  in the current kind being processed.

  It will suppress bad output by returning None for NULL property types and
  __private__ types (notably the stats themselves).
  """

  def __init__(self):
    """Constructor.

    Attributes:
      seen_properties: (kind, propertyname) -> number of times seen before. If
        seen more than once, this is a duplicate property for the kind.
      last_seen: Previous kind seen. If it changes, this is a new kind.
    """
    self.seen_properties = {}
    self.last_seen = None

  def __call__(self, instance, dictionary, bulkload_state):
    """Implementation of StatPropertyTypePropertyNameKindPostExport.

    See class docstring for more info.

    Args:
      instance: Input, current entity being exported.
      dictionary: Output, dictionary created by property_map transforms.
      bulkload_state: Passed bulkload_state.

    Returns:
      Dictionary--same object as passed in dictionary.
    """
    kind_name = dictionary['kind_name']
    property_name = dictionary['property_name']
    property_type = dictionary['property_type']

    if kind_name.startswith('__'):

      return None
    if property_type == 'NULL':

      return None

    property_key = kind_name, property_name
    if kind_name != self.last_seen:

      self.last_seen = kind_name
      separator = KIND_PREAMBLE % dictionary
    elif property_key in self.seen_properties:

      separator = PROPERTY_DUPE_WARNING % dictionary
    else:

      separator = ''
    self.seen_properties[property_key] = (
        self.seen_properties.get(property_key, 0) + 1)

    dictionary['separator'] = separator
    return dictionary



TYPE_TO_TRANSFORM_MAP = {
    'Blob': ('transform.blobproperty_from_base64',
             'base64.b64encode'),
    'Boolean': ('transform.regexp_bool(\'true\', re.IGNORECASE)',
                None),
    'ByteString': ('transform.bytestring_from_base64', 'base64.b64encode'),
    'Category': ('db.Category', None),
    'Date/Time': ('transform.import_date_time(\'%Y-%m-%dT%H:%M:%S\')',
                  'transform.export_date_time(\'%Y-%m-%dT%H:%M:%S\')'),
    'Email': ('db.Email', None),
    'Float': ('transform.none_if_empty(float)', None),

    'Integer': ('transform.none_if_empty(int)', None),
    'Key': ('transform.create_foreign_key(\'TODO: fill in Kind name\')',
            'transform.key_id_or_name_as_string'),
    'Link': ('db.Link', None),

    'PhoneNumber': ('db.PhoneNumber', None),
    'PostalAddress': ('db.PostalAddress', None),
    'Rating': ('transform.none_if_empty(db.Rating)', None),
    'String': (None, None),
    'Text': ('db.Text', None),
    'User': ('transform.none_if_empty(users.User)  # Assumes email address',
             None),
}


def DatastoreTypeToTransforms(property_type):
  """Return the import/export_transform lines for a datastore type.

  Args:
    property_type: Property type from the KindPropertyNamePropertyTypeStat.

  Returns:
    Strings for use in a bulkloader.yaml as transforms. This
    may be '' (no transform needed), or one or two lines with import_transform
    or export_transform.
  """

  import_transform, export_transform = TYPE_TO_TRANSFORM_MAP.get(property_type,
                                                                 (None, None))
  transform = []
  if import_transform:
    transform.append('      import_transform: %s\n' % import_transform)
  if export_transform:
    transform.append('      export_transform: %s\n' % export_transform)

  return ''.join(transform)
