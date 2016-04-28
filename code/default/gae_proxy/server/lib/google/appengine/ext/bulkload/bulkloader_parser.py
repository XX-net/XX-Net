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

A library to read bulkloader yaml configs. Returns a BulkloaderEntry object
which describes the bulkloader.yaml in object form, including some additional
parsing of things like Python lambdas.
"""













import inspect
import sys

from google.appengine.api import validation
from google.appengine.api import yaml_builder
from google.appengine.api import yaml_listener
from google.appengine.api import yaml_object

from google.appengine.ext.bulkload import bulkloader_errors




_global_temp_globals = None


class EvaluatedCallable(validation.Validator):
  """Validates that a string evaluates to a Python callable.

  Calls eval at validation time and stores the results as a ParsedMethod object.
  The ParsedMethod object can be used as a string (original value) or callable
  (parsed method). It also exposes supports_bulkload_state if the callable has
  a kwarg called 'bulkload_state', which is used to determine how to call
  the *_transform methods.
  """

  class ParsedMethod(object):
    """Wrap the string, the eval'd method, and supports_bulkload_state."""

    def __init__(self, value, key):
      """Initialze internal state.

      Eval the string value and save the result.

      Args:
        value: String to compile as a regular expression.
        key: The YAML field name.

      Raises:
        InvalidCodeInConfiguration: if the code could not be evaluated, or
        the evalauted method is not callable.
      """
      self.value = value
      try:
        self.method = eval(value, _global_temp_globals)
      except Exception, err:
        raise bulkloader_errors.InvalidCodeInConfiguration(
            'Invalid code for %s. Code: "%s". Details: %s' % (key, value, err))
      if not callable(self.method):
        raise bulkloader_errors.InvalidCodeInConfiguration(
            'Code for %s did not return a callable.  Code: "%s".' %
            (key, value))





      self.supports_bulkload_state = False
      try:
        argspec = inspect.getargspec(self.method)
        if 'bulkload_state' in argspec[0]:
          self.supports_bulkload_state = True
      except TypeError:
        pass

    def __str__(self):
      """Return a string representation of the method: the original string."""
      return self.value

    def __call__(self, *args, **kwargs):
      """Call the method."""
      return self.method(*args, **kwargs)

  def __init__(self):
    """Initialize EvaluatedCallable validator."""
    super(EvaluatedCallable, self).__init__()

  def Validate(self, value, key):
    """Validates that the string compiles as a Python callable.

    Args:
      value: String to compile as a regular expression.
      key: The YAML field name.

    Returns:
      Value wrapped in an object with properties 'value' and 'fn'.

    Raises:
      InvalidCodeInConfiguration when value does not compile.
    """
    if isinstance(value, self.ParsedMethod):
      return value
    else:
      return self.ParsedMethod(value, key)

  def ToValue(self, value):
    """Returns the code string for this value."""
    return value.value


OPTIONAL_EVALUATED_CALLABLE = validation.Optional(EvaluatedCallable())





class ConnectorSubOptions(validation.Validated):
  """Connector options."""

  ATTRIBUTES = {
      'delimiter': validation.Optional(validation.TYPE_STR),
      'dialect': validation.Optional(validation.TYPE_STR),
  }



class ConnectorOptions(validation.Validated):
  """Connector options."""

  ATTRIBUTES = {
      'column_list':
          validation.Optional(validation.Repeated(validation.TYPE_STR)),
      'columns': validation.Optional(validation.TYPE_STR),
      'encoding': validation.Optional(validation.TYPE_STR),
      'epilog': validation.Optional(validation.TYPE_STR),
      'export_options': validation.Optional(ConnectorSubOptions),
      'import_options': validation.Optional(ConnectorSubOptions),
      'mode': validation.Optional(validation.TYPE_STR),
      'prolog': validation.Optional(validation.TYPE_STR),
      'style': validation.Optional(validation.TYPE_STR),
      'template': validation.Optional(validation.TYPE_STR),
      'xpath_to_nodes': validation.Optional(validation.TYPE_STR),
      'print_export_header_row': validation.Optional(validation.TYPE_BOOL),
      'skip_import_header_row': validation.Optional(validation.TYPE_BOOL),
  }

  def CheckInitialized(self):
    """Post-loading 'validation'. Really used to fix up yaml hackyness."""
    super(ConnectorOptions, self).CheckInitialized()

    if self.column_list:

      self.column_list = [str(column) for column in self.column_list]


class ExportEntry(validation.Validated):
  """Describes the optional export transform for a single property."""

  ATTRIBUTES = {
      'external_name': validation.Optional(validation.TYPE_STR),
      'export_transform': OPTIONAL_EVALUATED_CALLABLE,
      }


class PropertyEntry(validation.Validated):
  """Describes the transform for a single property."""


  ATTRIBUTES = {
      'property': validation.Type(str),
      'import_transform': OPTIONAL_EVALUATED_CALLABLE,
      'import_template': validation.Optional(validation.TYPE_STR),
      'default_value': validation.Optional(validation.TYPE_STR),
      'export': validation.Optional(validation.Repeated(ExportEntry)),
      }
  ATTRIBUTES.update(ExportEntry.ATTRIBUTES)

  def CheckInitialized(self):
    """Check that all required (combinations) of fields are set.

    Also fills in computed properties.

    Raises:
      InvalidConfiguration: If the config is invalid.
    """
    super(PropertyEntry, self).CheckInitialized()

    if not (self.external_name or self.import_template or self.export):
      raise bulkloader_errors.InvalidConfiguration(
          'Neither external_name nor import_template nor export specified for '
          'property %s.' % self.property)


class TransformerEntry(validation.Validated):
  """Describes the transform for an entity (or model) kind."""

  ATTRIBUTES = {
      'name': validation.Optional(validation.TYPE_STR),
      'kind': validation.Optional(validation.TYPE_STR),
      'model': OPTIONAL_EVALUATED_CALLABLE,
      'connector': validation.TYPE_STR,
      'connector_options': validation.Optional(ConnectorOptions, {}),
      'use_model_on_export': validation.Optional(validation.TYPE_BOOL),
      'sort_key_from_entity': OPTIONAL_EVALUATED_CALLABLE,
      'post_import_function': OPTIONAL_EVALUATED_CALLABLE,
      'post_export_function': OPTIONAL_EVALUATED_CALLABLE,
      'property_map': validation.Repeated(PropertyEntry, default=[]),
  }

  def CheckInitialized(self):
    """Check that all required (combinations) of fields are set.

    Also fills in computed properties.

    Raises:
      InvalidConfiguration: if the config is invalid.
    """
    if not self.kind and not self.model:
      raise bulkloader_errors.InvalidConfiguration(
          'Neither kind nor model specified for transformer.')
    if self.kind and self.model:
      raise bulkloader_errors.InvalidConfiguration(
          'Both kind and model specified for transformer.')


    if self.model:



      self.kind = self.model.method.kind()
    else:
      if self.use_model_on_export:
        raise bulkloader_errors.InvalidConfiguration(
            'No model class specified but use_model_on_export is true.')
    if not self.name:

      self.name = self.kind



    if not self.connector:
      raise bulkloader_errors.InvalidConfiguration('No connector specified.')

    property_names = set()
    for prop in self.property_map:
      if prop.property in property_names:
        raise bulkloader_errors.InvalidConfiguration(
            'Duplicate property specified for property %s in transform %s' %
            (prop.property, self.name))
      property_names.add(prop.property)


class PythonPreambleEntry(validation.Validated):
  """Python modules to import at initialization time, typically models."""




  ATTRIBUTES = {'import': validation.TYPE_STR,
                'as': validation.Optional(validation.TYPE_STR),
               }

  def CheckInitialized(self):
    """Check that all required fields are set, and update global state.

    The imports specified in the preamble are imported at this time.
    """
    python_import = getattr(self, 'import')
    topname = python_import.split('.')[0]
    module_name = getattr(self, 'as')
    if not module_name:
      module_name = python_import.split('.')[-1]

    __import__(python_import, _global_temp_globals)


    _global_temp_globals[topname] = sys.modules[topname]
    _global_temp_globals[module_name] = sys.modules[python_import]


class BulkloaderEntry(validation.Validated):
  """Root of the bulkloader configuration."""

  ATTRIBUTES = {
      'python_preamble':
          validation.Optional(validation.Repeated(PythonPreambleEntry)),
      'transformers': validation.Repeated(TransformerEntry),
  }


def load_config(stream, config_globals):
  """Load a configuration file and generate importer and exporter classes.

  Args:
    stream: Stream containing config YAML.
    config_globals: Dict to use to reference globals for code in the config.

  Returns:
    BulkloaderEntry

  Raises:
    InvalidConfiguration: If the config is invalid.
  """
  builder = yaml_object.ObjectBuilder(BulkloaderEntry)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)


  global _global_temp_globals
  _global_temp_globals = config_globals
  try:
    listener.Parse(stream)
  finally:
    _global_temp_globals = None

  bulkloader_infos = handler.GetResults()
  if len(bulkloader_infos) < 1:
    raise bulkloader_errors.InvalidConfiguration('No configuration specified.')
  if len(bulkloader_infos) > 1:
    raise bulkloader_errors.InvalidConfiguration(
        'Multiple sections in configuration.')
  bulkloader_info = bulkloader_infos[0]
  if not bulkloader_info.transformers:
    raise bulkloader_errors.InvalidConfiguration('No transformers specified.')
  return bulkloader_info
