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





"""Bulkloader Config Parser and runner.

A library to read bulkloader yaml configs.
The code to interface between the bulkloader tool and the various connectors
and conversions.
"""











import copy
import os
import sys

from google.appengine.api import datastore
from google.appengine.ext.bulkload import bulkloader_errors
from google.appengine.ext.bulkload import bulkloader_parser
from google.appengine.ext.bulkload import csv_connector
from google.appengine.ext.bulkload import simpletext_connector
from google.appengine.ext.bulkload import simplexml_connector


CONNECTOR_FACTORIES = {
    'csv': csv_connector.CsvConnector.create_from_options,
    'simplexml': simplexml_connector.SimpleXmlConnector.create_from_options,
    'simpletext': simpletext_connector.SimpleTextConnector.create_from_options,
}


class BulkloadState(object):
  """Encapsulates state which is passed to other methods used in bulk loading.

  It is optionally passed to import/export transform functions.
  It is passed to connector objects.

  Properties:
    filename: The filename flag passed on the command line.
    loader_opts: The loader_opts flag passed on the command line.
    exporter_opts: The exporter_opts flag passed on the command line.
    current_instance: The current entity or model instance.
    current_entity: On export, the current entity instance.
    current_dictionary: The current input or output dictionary.
  """

  def __init__(self):
    self.filename = ''
    self.loader_opts = None
    self.exporter_opts = None
    self.current_instance = None
    self.current_entity = None
    self.current_dictionary = None


def default_export_transform(value):
  """A default export transform if nothing else is specified.

  We assume most export connectors are string based, so a string cast is used.
  However, casting None to a string leads to 'None', so that's special cased.

  Args:
    value: A value of some type.

  Returns:
    unicode(value), or u'' if value is None
  """


  if value is None:
    return u''
  else:
    return unicode(value)


class DictConvertor(object):
  """Convert a dict to an App Engine model instance or entity. And back.

  The constructor takes a transformer spec representing a single transformer
  in a bulkloader.yaml.

  The DictConvertor object has two public methods, dict_to_entity and
  entity_to_dict, which do the conversion between a neutral dictionary (the
  input/output of a connector) and an entity based on the spec.

  Note that the model class may be used instead of an entity during the
  transform--this adds extra validation, etc, but also has a performance hit.
  """

  def __init__(self, transformer_spec):
    """Constructor. See class docstring for more info.

    Args:
      transformer_spec: A single transformer from a parsed bulkloader.yaml.
        This assumes that the transformer_spec is valid. It does not
        double check things like use_model_on_export requiring model.
    """
    self._transformer_spec = transformer_spec


    self._create_key = None
    for prop in self._transformer_spec.property_map:
      if prop.property == '__key__':
        self._create_key = prop

  def dict_to_entity(self, input_dict, bulkload_state):
    """Transform the dict to a model or entity instance(s).

    Args:
      input_dict: Neutral input dictionary describing a single input record.
      bulkload_state: bulkload_state object describing the state.

    Returns:
      Entity or model instance, or collection of entity or model instances,
      to be uploaded.
    """

    bulkload_state_copy = copy.copy(bulkload_state)
    bulkload_state_copy.current_dictionary = input_dict
    instance = self.__create_instance(input_dict, bulkload_state_copy)
    bulkload_state_copy.current_instance = instance
    self.__run_import_transforms(input_dict, instance, bulkload_state_copy)
    if self._transformer_spec.post_import_function:
      post_map_instance = self._transformer_spec.post_import_function(
          input_dict, instance, bulkload_state_copy)

      return post_map_instance
    return instance

  def entity_to_dict(self, entity, bulkload_state):
    """Transform the entity to a dict, possibly via a model.

    Args:
      entity: An entity.
      bulkload_state: bulkload_state object describing the global state.

    Returns:
      A neutral output dictionary describing the record to write to the
      output.
      In the future this may return zero or multiple output dictionaries.
    """
    if self._transformer_spec.use_model_on_export:
      instance = self._transformer_spec.model.from_entity(entity)
    else:
      instance = entity

    export_dict = {}
    bulkload_state.current_entity = entity
    bulkload_state.current_instance = instance
    bulkload_state.current_dictionary = export_dict
    self.__run_export_transforms(instance, export_dict, bulkload_state)
    if self._transformer_spec.post_export_function:
      post_export_result = self._transformer_spec.post_export_function(
          instance, export_dict, bulkload_state)



      return post_export_result
    return export_dict

  def __dict_to_prop(self, transform, input_dict, bulkload_state):
    """Handle a single property on import.

    Args:
      transform: The transform spec for this property.
      input_dict: Neutral input dictionary describing a single input record.
      bulkload_state: bulkload_state object describing the global state.

    Returns:
      The value for this particular property.
    """
    if transform.import_template:
      value = transform.import_template % input_dict
    else:

      value = input_dict.get(transform.external_name)

    if transform.import_transform:
      if transform.import_transform.supports_bulkload_state:
        value = transform.import_transform(value, bulkload_state=bulkload_state)
      else:
        value = transform.import_transform(value)
    return value

  def __create_instance(self, input_dict, bulkload_state):
    """Return a model instance or entity from an input_dict.

    Args:
      input_dict: Neutral input dictionary describing a single input record.
      bulkload_state: bulkload_state object describing the global state.

    Returns:
      Entity or model instance, or collection of entity or model instances,
      to be uploaded.
    """
    key = None
    if self._create_key:
      key = self.__dict_to_prop(self._create_key, input_dict, bulkload_state)
      if isinstance(key, (int, long)):
        key = datastore.Key.from_path(self._transformer_spec.kind, key)
      if self._transformer_spec.model:
        if isinstance(key, datastore.Key):
          return self._transformer_spec.model(key=key)
        else:
          return self._transformer_spec.model(key_name=key)
      else:
        if isinstance(key, datastore.Key):
          parent = key.parent()
          if key.name() is None:
            return datastore.Entity(self._transformer_spec.kind,
                                    parent=parent, id=key.id())
          else:
            return datastore.Entity(self._transformer_spec.kind,
                                    parent=parent, name=key.name())
    elif self._transformer_spec.model:
      return self._transformer_spec.model()

    return datastore.Entity(self._transformer_spec.kind, name=key)

  def __run_import_transforms(self, input_dict, instance, bulkload_state):
    """Fill in a single entity or model instance from an input_dict.

    Args:
      input_dict: Input dict from the connector object.
      instance: Entity or model instance to fill in.
      bulkload_state: Passed bulkload state.
    """

    for transform in self._transformer_spec.property_map:
      if transform.property == '__key__':

        continue

      value = self.__dict_to_prop(transform, input_dict, bulkload_state)


      if self._transformer_spec.model:
        setattr(instance, transform.property, value)
      else:
        instance[transform.property] = value

  def __prop_to_dict(self, value, property_name, transform, export_dict,
                     bulkload_state):
    """Transform a single export-side field value to dict property.

    Args:
      value: Value from the entity or model instance.
      property_name: Name of the value in the entity or model instance.
      transform: Transform property, either an ExportEntry or PropertyEntry
      export_dict: output dictionary.
      bulkload_state: Passed bulkload state.

    Raises:
      ErrorOnTransform, encapsulating an error encountered during the transform.
    """
    if transform.export_transform:
      try:
        if transform.export_transform.supports_bulkload_state:
          transformed_value = transform.export_transform(
              value, bulkload_state=bulkload_state)
        else:
          transformed_value = transform.export_transform(value)
      except Exception, err:
        raise bulkloader_errors.ErrorOnTransform(
            'Error on transform. '
            'Property: %s External Name: %s. Code: %s Details: %s' %
            (property_name, transform.external_name, transform.export_transform,
             err))
    else:
      transformed_value = default_export_transform(value)
    export_dict[transform.external_name] = transformed_value

  def __run_export_transforms(self, instance, export_dict, bulkload_state):
    """Fill in export_dict for an entity or model instance.

    Args:
      instance: Entity or model instance
      export_dict: output dictionary.
      bulkload_state: Passed bulkload state.
    """
    for transform in self._transformer_spec.property_map:
      if transform.property == '__key__':
        value = instance.key()
      elif self._transformer_spec.use_model_on_export:
        value = getattr(instance, transform.property, transform.default_value)
      else:

        value = instance.get(transform.property, transform.default_value)


      if transform.export:
        for prop in transform.export:
          self.__prop_to_dict(value, transform.property, prop, export_dict,
                              bulkload_state)
      elif transform.external_name:
        self.__prop_to_dict(value, transform.property, transform, export_dict,
                            bulkload_state)



class GenericImporter(object):
  """Generic Bulkloader import class for input->dict->model transformation.

  The bulkloader will call generate_records and create_entity, and
  we'll delegate those to the passed in methods.
  """

  def __init__(self, import_record_iterator, dict_to_entity, name,
               reserve_keys):
    """Constructor.

    Args:
      import_record_iterator: Method which yields neutral dictionaries.
      dict_to_entity: Method dict_to_entity(input_dict) returns model or entity
        instance(s).
      name: Name to register with the bulkloader importers (as 'kind').
      reserve_keys: Method ReserveKeys(keys) which will advance the id
        sequence in the datastore beyond each key.id(). Can be None.
    """
    self.import_record_iterator = import_record_iterator
    self.dict_to_entity = dict_to_entity
    self.kind = name
    self.bulkload_state = BulkloadState()
    self.reserve_keys = reserve_keys
    self.keys_to_reserve = []

  def get_keys_to_reserve(self):
    """Required as part of the bulkloader Loader interface.

    At the moment, this is not actually used by the bulkloader for import;
    instead we will reserve keys if necessary in finalize.

    Returns:
      List of keys to reserve, currently always [].
    """
    return []

  def initialize(self, filename, loader_opts):
    """Performs initialization. Merely records the values for later use.

    Args:
      filename: The string given as the --filename flag argument.
      loader_opts: The string given as the --loader_opts flag argument.
    """

    self.bulkload_state.loader_opts = loader_opts
    self.bulkload_state.filename = filename

  def finalize(self):
    """Performs finalization actions after the upload completes.

    If keys with numeric ids were used on import, this will call AllocateIds
    to ensure that autogenerated IDs will not raise exceptions on conflict
    with uploaded entities.
    """
    if self.reserve_keys:
      self.reserve_keys(self.keys_to_reserve)

  def generate_records(self, filename):
    """Iterator yielding neutral dictionaries from the connector object.

    Args:
      filename: Filename argument passed in on the command line.

    Returns:
      Iterator yielding neutral dictionaries, later passed to create_entity.
    """
    return self.import_record_iterator(filename, self.bulkload_state)

  def generate_key(self, line_number, unused_values):
    """Bulkloader method to generate keys, mostly unused here.

    This is called by the bulkloader just before it calls create_entity. The
    line_number is returned to be passed to the record dict, but otherwise
    unused.

    Args:
      line_number: Record number from the bulkloader.
      unused_values: Neutral dict from generate_records; unused.

    Returns:
      line_number for use later on.
    """
    return line_number

  def __reserve_entity_key(self, entity):
    """Collect entity key to be reserved if it has a numeric id in its path.

    Keys to reserve are stored in self.keys_to_reserve.
    They are not tracked if self.reserve_keys is None.

    Args:
      entity: An entity with a key.
    """
    if not self.reserve_keys:
      return
    if isinstance(entity, datastore.Entity):
      if not entity.key():
        return
    elif not entity.has_key():
      return
    key = entity.key()




    if not key.has_id_or_name():
      return


    for id_or_name in key.to_path()[1::2]:
      if isinstance(id_or_name, (int, long)):
        self.keys_to_reserve.append(key)
        return

  def create_entity(self, values, key_name=None, parent=None):
    """Creates entity/entities from input values via the dict_to_entity method.

    Args:
      values: Neutral dict from generate_records.
      key_name: record number from generate_key.
      parent: Always None in this implementation of a Loader.

    Returns:
      Entity or model instance, or collection of entity or model instances,
      to be uploaded.
    """

    input_dict = values
    input_dict['__record_number__'] = key_name
    entity = self.dict_to_entity(input_dict, self.bulkload_state)
    self.__reserve_entity_key(entity)
    return entity


class GenericExporter(object):
  """Implements bulkloader.Exporter interface and delegates.

  This will delegate to the passed in entity_to_dict method and the
  methods on the export_recorder which are in the ConnectorInterface.
  """

  def __init__(self, export_recorder, entity_to_dict, kind,
               sort_key_from_entity):
    """Constructor.

    Args:
      export_recorder: Object which writes results, an implementation of
          ConnectorInterface.
      entity_to_dict: Method which converts a single entity to a neutral dict.
      kind: Kind to identify this object to the bulkloader.
      sort_key_from_entity: Optional method to return a sort key for each
          entity. This key will be used to sort the downloaded entities before
          passing them to eneity_to_dict.
    """
    self.export_recorder = export_recorder
    self.entity_to_dict = entity_to_dict
    self.kind = kind
    self.sort_key_from_entity = sort_key_from_entity
    self.calculate_sort_key_from_entity = bool(sort_key_from_entity)
    self.bulkload_state = BulkloadState()

  def initialize(self, filename, exporter_opts):
    """Performs initialization and validation of the output file.

    Args:
      filename: The string given as the --filename flag argument.
      exporter_opts: The string given as the --exporter_opts flag argument.
    """
    self.bulkload_state.filename = filename
    self.bulkload_state.exporter_opts = exporter_opts
    self.export_recorder.initialize_export(filename, self.bulkload_state)

  def output_entities(self, entity_iterator):
    """Outputs the downloaded entities.

    Args:
      entity_iterator: An iterator that yields the downloaded entities
        in sorted order.
    """
    for entity in entity_iterator:
      output_dict = self.entity_to_dict(entity, self.bulkload_state)


      if output_dict:
        self.export_recorder.write_dict(output_dict)

  def finalize(self):
    """Performs finalization actions after the download completes."""
    self.export_recorder.finalize_export()


def create_transformer_classes(transformer_spec, config_globals, reserve_keys):
  """Create an importer and exporter class from a transformer spec.

  Args:
    transformer_spec: A bulkloader_parser.TransformerEntry.
    config_globals: Dict to use to reference globals for code in the config.
    reserve_keys: Method ReserveKeys(keys) which will advance the id
        sequence in the datastore beyond each key.id(). Can be None.

  Raises:
    InvalidConfig: when the config is invalid.

  Returns:
    Tuple, (importer class, exporter class), each which is in turn a wrapper
    for the GenericImporter/GenericExporter class using a DictConvertor object
    configured as per the transformer_spec.
  """

  if transformer_spec.connector in CONNECTOR_FACTORIES:
    connector_factory = CONNECTOR_FACTORIES[transformer_spec.connector]
  elif config_globals and '.' in transformer_spec.connector:
    try:
      connector_factory = eval(transformer_spec.connector, config_globals)
    except (NameError, AttributeError):
      raise bulkloader_errors.InvalidConfiguration(
          'Invalid connector specified for name=%s. Could not evaluate %s.' %
          (transformer_spec.name, transformer_spec.connector))
  else:
    raise bulkloader_errors.InvalidConfiguration(
        'Invalid connector specified for name=%s. Must be either a built in '
        'connector ("%s") or a factory method in a module imported via '
        'python_preamble.' %
        (transformer_spec.name, '", "'.join(CONNECTOR_FACTORIES)))
  options = {}
  if transformer_spec.connector_options:
    options = transformer_spec.connector_options.ToDict()

  try:
    connector_object = connector_factory(options, transformer_spec.name)
  except TypeError:


    raise bulkloader_errors.InvalidConfiguration(
        'Invalid connector specified for name=%s. Could not initialize %s.' %
        (transformer_spec.name, transformer_spec.connector))





  dict_to_model_object = DictConvertor(transformer_spec)

  class ImporterClass(GenericImporter):
    """Class to pass to the bulkloader, wraps the specificed configuration."""

    def __init__(self):
      super(self.__class__, self).__init__(
          connector_object.generate_import_record,
          dict_to_model_object.dict_to_entity,
          transformer_spec.name,
          reserve_keys)
  importer_class = ImporterClass

  class ExporterClass(GenericExporter):
    """Class to pass to the bulkloader, wraps the specificed configuration."""

    def __init__(self):

      super(self.__class__, self).__init__(
          connector_object,
          dict_to_model_object.entity_to_dict,
          transformer_spec.kind,
          transformer_spec.sort_key_from_entity)
  exporter_class = ExporterClass

  return importer_class, exporter_class


def load_config_from_stream(stream, reserve_keys=None):
  """Parse a bulkloader.yaml file into bulkloader loader classes.

  Args:
    stream: A stream containing bulkloader.yaml data.
    reserve_keys: Method ReserveKeys(keys) which will advance the id
        sequence in the datastore beyond each key.id(). Can be None.

  Returns:
    importer_classes, exporter_classes: Constructors suitable to pass to the
    bulkloader.
  """
  config_globals = {}
  config = bulkloader_parser.load_config(stream, config_globals)
  importer_classes = []
  exporter_classes = []
  for transformer in config.transformers:
    importer, exporter = create_transformer_classes(transformer, config_globals,
                                                    reserve_keys)
    if importer:
      importer_classes.append(importer)
    if exporter:
      exporter_classes.append(exporter)

  return importer_classes, exporter_classes


def load_config(filename, update_path=True, reserve_keys=None):
  """Load a configuration file and create importer and exporter classes.

  Args:
    filename: Filename of bulkloader.yaml.
    update_path: Should sys.path be extended to include the path of filename?
    reserve_keys: Method ReserveKeys(keys) which will advance the id
        sequence in the datastore beyond each key.id(). Can be None.

  Returns:
    Tuple, (importer classes, exporter classes) based on the transformers
    specified in the file.
  """

  if update_path:

    sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(filename))))
  stream = file(filename, 'r')
  try:
    return load_config_from_stream(stream, reserve_keys)
  finally:
    stream.close()
