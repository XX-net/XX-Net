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
"""Helper that converts parameter values to the type expected by the SPI.

Parameter values that appear in the URL and the query string are usually
converted to native types before being passed to the SPI.  This code handles
that conversion and some validation.
"""







from google.appengine.tools.devappserver2.endpoints import errors


__all__ = ['transform_parameter_value']


def _check_enum(parameter_name, value, parameter_config):
  """Checks if an enum value is valid.

  This is called by the transform_parameter_value function and shouldn't be
  called directly.

  This verifies that the value of an enum parameter is valid.

  Args:
    parameter_name: A string containing the name of the parameter, which is
      either just a variable name or the name with the index appended. For
      example 'var' or 'var[2]'.
    value: A string containing the value passed in for the parameter.
    parameter_config: The dictionary containing information specific to the
      parameter in question. This is retrieved from request.parameters in
      the method config.

  Raises:
    EnumRejectionError: If the given value is not among the accepted
      enum values in the field parameter.
  """
  enum_values = [enum['backendValue']
                 for enum in parameter_config['enum'].values()
                 if 'backendValue' in enum]
  if value not in enum_values:
    raise errors.EnumRejectionError(parameter_name, value, enum_values)


def _check_boolean(parameter_name, value, parameter_config):
  """Checks if a boolean value is valid.

  This is called by the transform_parameter_value function and shouldn't be
  called directly.

  This checks that the string value passed in can be converted to a valid
  boolean value.

  Args:
    parameter_name: A string containing the name of the parameter, which is
      either just a variable name or the name with the index appended. For
      example 'var' or 'var[2]'.
    value: A string containing the value passed in for the parameter.
    parameter_config: The dictionary containing information specific to the
      parameter in question. This is retrieved from request.parameters in
      the method config.

  Raises:
    BasicTypeParameterError: If the given value is not a valid boolean
      value.
  """
  if parameter_config.get('type') != 'boolean':
    return





  if value.lower() not in ('1', 'true', '0', 'false'):
    raise errors.BasicTypeParameterError(parameter_name, value, 'boolean')


def _convert_boolean(value):
  """Convert a string to a boolean value the same way the server does.

  This is called by the transform_parameter_value function and shouldn't be
  called directly.

  Args:
    value: A string value to be converted to a boolean.

  Returns:
    True or False, based on whether the value in the string would be interpreted
    as true or false by the server.  In the case of an invalid entry, this
    returns False.
  """
  if value.lower() in ('1', 'true'):
    return True
  return False


# Map to convert parameters from strings to their desired back-end format.
# Anything not listed here will remain a string.  Note that the server
# keeps int64 and uint64 as strings when passed to the SPI.
# This maps a type name from the .api method configuration to a (validation
# function, conversion function, descriptive type name) tuple.  The
# descriptive type name is only used in conversion error messages, and the
# names here are chosen to match the error messages from the server.
# Note that the 'enum' entry is special cased.  Enums have 'type': 'string',
# so we have special case code to recognize them and use the 'enum' map
# entry.
_PARAM_CONVERSION_MAP = {'boolean': (_check_boolean,
                                     _convert_boolean,
                                     'boolean'),
                         'int32': (None, int, 'integer'),
                         'uint32': (None, int, 'integer'),
                         'float': (None, float, 'float'),
                         'double': (None, float, 'double'),
                         'enum': (_check_enum, None, None)}


def _get_parameter_conversion_entry(parameter_config):
  """Get information needed to convert the given parameter to its SPI type.

  Args:
    parameter_config: The dictionary containing information specific to the
      parameter in question. This is retrieved from request.parameters in the
      method config.

  Returns:
    The entry from _PARAM_CONVERSION_MAP with functions/information needed to
    validate and convert the given parameter from a string to the type expected
    by the SPI.
  """
  entry = _PARAM_CONVERSION_MAP.get(parameter_config.get('type'))

  # Special handling for enum parameters.  An enum's type is 'string', so we
  # need to detect them by the presence of an 'enum' property in their
  # configuration.
  if entry is None and 'enum' in parameter_config:
    entry = _PARAM_CONVERSION_MAP['enum']

  return entry


def transform_parameter_value(parameter_name, value, parameter_config):
  """Validates and transforms parameters to the type expected by the SPI.

  If the value is a list this will recursively call _transform_parameter_value
  on the values in the list. Otherwise, it checks all parameter rules for the
  the current value and converts its type from a string to whatever format
  the SPI expects.

  In the list case, '[index-of-value]' is appended to the parameter name for
  error reporting purposes.

  Args:
    parameter_name: A string containing the name of the parameter, which is
      either just a variable name or the name with the index appended, in the
      recursive case. For example 'var' or 'var[2]'.
    value: A string or list of strings containing the value(s) passed in for
      the parameter.  These are the values from the request, to be validated,
      transformed, and passed along to the SPI.
    parameter_config: The dictionary containing information specific to the
      parameter in question. This is retrieved from request.parameters in the
      method config.

  Returns:
    The converted parameter value(s).  Not all types are converted, so this
    may be the same string that's passed in.
  """
  if isinstance(value, list):
    # We're only expecting to handle path and query string parameters here.
    # The way path and query string parameters are passed in, they'll likely
    # only be single values or singly-nested lists (no lists nested within
    # lists).  But even if there are nested lists, we'd want to preserve that
    # structure.  These recursive calls should preserve it and convert all
    # parameter values.  See the docstring for information about the parameter
    # renaming done here.
    return [transform_parameter_value('%s[%d]' % (parameter_name, index),
                                      element, parameter_config)
            for index, element in enumerate(value)]

  # Validate and convert the parameter value.
  entry = _get_parameter_conversion_entry(parameter_config)
  if entry:
    validation_func, conversion_func, type_name = entry
    if validation_func:
      validation_func(parameter_name, value, parameter_config)
    if conversion_func:
      try:
        return conversion_func(value)
      except ValueError:
        raise errors.BasicTypeParameterError(parameter_name, value, type_name)

  return value
