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




"""A library for managing flags-like configuration that update dynamically.
"""



import logging
import os
import re
import time

try:
  from google.appengine.api import memcache
  from google.appengine.ext import db
  from google.appengine.api import validation
  from google.appengine.api import yaml_object
except:
  from google.appengine.api import memcache
  from google.appengine.ext import db
  from google.appengine.ext import validation
  from google.appengine.ext import yaml_object





DATASTORE_DEADLINE = 1.5


RESERVED_MARKER = 'ah__conf__'



NAMESPACE = '_' + RESERVED_MARKER

CONFIG_KIND = '_AppEngine_Config'

ACTIVE_KEY_NAME = 'active'

FILENAMES = ['conf.yaml', 'conf.yml']

PARAMETERS = 'parameters'


PARAMETER_NAME_REGEX = '[a-zA-Z][a-zA-Z0-9_]*'


_cached_config = None


class Config(db.Expando):
  """The representation of a config in the datastore and memcache."""










  ah__conf__version = db.IntegerProperty(default=0, required=True)

  @classmethod
  def kind(cls):
    """Override the kind name to prevent collisions with users."""
    return CONFIG_KIND

  def ah__conf__load_from_yaml(self, parsed_config):
    """Loads all the params from a YAMLConfiguration into expando fields.

    We set these expando properties with a special name prefix 'p_' to
    keep them separate from the static attributes of Config.  That way we
    don't have to check elsewhere to make sure the user doesn't stomp on
    our built in properties.

    Args:
      parse_config: A YAMLConfiguration.
    """
    for key, value in parsed_config.parameters.iteritems():
      setattr(self, key, value)


class _ValidParameterName(validation.Validator):
  """Validator to check if a value is a valid config parameter name.

  We only allow valid python attribute names without leading underscores
  that also do not collide with reserved words in the datastore models.
  """
  def __init__(self):
    self.regex = validation.Regex(PARAMETER_NAME_REGEX)

  def Validate(self, value, key):
    """Check that all parameter names are valid.

    This is used as a validator when parsing conf.yaml.

    Args:
      value: the value to check.
      key: A description of the context for which this value is being
      validated.

    Returns:
      The validated value.
    """
    value = self.regex.Validate(value, key)

    try:
      db.check_reserved_word(value)
    except db.ReservedWordError:
      raise validation.ValidationError(
          'The config parameter name %.100r is reserved by db.Model see: '
          'https://developers.google.com/appengine/docs/python/datastore/'
          'modelclass#Disallowed_Property_Names for details.' % value)

    if value.startswith(RESERVED_MARKER):
      raise validation.ValidationError(
          'The config parameter name %.100r is reserved, as are all names '
          'beginning with \'%s\', please choose a different name.' % (
              value, RESERVED_MARKER))

    return value


class _Scalar(validation.Validator):
  """Validator to check if a value is a simple scalar type.

  We only allow scalars that are well supported by both the datastore and YAML.
  """
  ALLOWED_PARAMETER_VALUE_TYPES = frozenset(
      [bool, int, long, float, str, unicode])

  def Validate(self, value, key):
    """Check that all parameters are scalar values.

    This is used as a validator when parsing conf.yaml

    Args:
      value: the value to check.
      key: the name of parameter corresponding to this value.

    Returns:
      We just return value unchanged.
    """
    if type(value) not in self.ALLOWED_PARAMETER_VALUE_TYPES:
      raise validation.ValidationError(
          'Expected scalar value for parameter: %s, but found %.100r which '
          'is type %s' % (key, value, type(value).__name__))

    return value


class _ParameterDict(validation.ValidatedDict):
  """This class validates the parameters dictionary in YAMLConfiguration.

  Keys must look like non-private python identifiers and values
  must be a supported scalar.  See the class comment for YAMLConfiguration.
  """
  KEY_VALIDATOR = _ValidParameterName()
  VALUE_VALIDATOR = _Scalar()


class YAMLConfiguration(validation.Validated):
  """This class describes the structure of a conf.yaml file.

  At the top level the file should have a params attribue which is a mapping
  from strings to scalars.  For example:

  parameters:
    background_color: 'red'
    message_size: 1024
    boolean_valued_param: true
  """
  ATTRIBUTES = {PARAMETERS: _ParameterDict}


def LoadSingleConf(stream):
  """Load a conf.yaml file or string and return a YAMLConfiguration object.

  Args:
    stream: a file object corresponding to a conf.yaml file, or its contents
      as a string.

  Returns:
    A YAMLConfiguration instance
  """
  return yaml_object.BuildSingleObject(YAMLConfiguration, stream)




def _find_yaml_path():
  """Traverse directory trees to find conf.yaml file.

  Begins with the current working direcotry and then moves up the
  directory structure until the file is found..

  Returns:
    the path of conf.yaml file or None if not found.
  """
  current, last = os.getcwd(), None
  while current != last:
    for yaml_name in FILENAMES:
      yaml_path = os.path.join(current, yaml_name)
      if os.path.exists(yaml_path):
        return yaml_path
    last = current
    current, last = os.path.dirname(current), current

  return None


def _fetch_from_local_file(pathfinder=_find_yaml_path, fileopener=open):
  """Get the configuration that was uploaded with this version.

  Args:
    pathfinder: a callable to use for finding the path of the conf.yaml
    file.  This is only for use in testing.
    fileopener: a callable to use for opening a named file.  This is
    only for use in testing.

  Returns:
    A config class instance for the options that were uploaded.  If there
    is no config file, return None
  """


  yaml_path = pathfinder()
  if yaml_path:
    config = Config()
    config.ah__conf__load_from_yaml(LoadSingleConf(fileopener(yaml_path)))
    logging.debug('Loaded conf parameters from conf.yaml.')
    return config

  return None


def _get_active_config_key(app_version):
  """Generate the key for the active config record belonging to app_version.

  Args:
    app_version: the major version you want configuration data for.

  Returns:
    The key for the active Config record for the given app_version.
  """
  return db.Key.from_path(
      CONFIG_KIND,
      '%s/%s' % (app_version, ACTIVE_KEY_NAME),
      namespace=NAMESPACE)


def _fetch_latest_from_datastore(app_version):
  """Get the latest configuration data for this app-version from the datastore.

  Args:
    app_version: the major version you want configuration data for.

  Side Effects:
    We populate memcache with whatever we find in the datastore.

  Returns:
    A config class instance for most recently set options or None if the
    query could not complete due to a datastore exception.
  """





  rpc = db.create_rpc(deadline=DATASTORE_DEADLINE,
                      read_policy=db.EVENTUAL_CONSISTENCY)
  key = _get_active_config_key(app_version)
  config = None
  try:
    config = Config.get(key, rpc=rpc)
    logging.debug('Loaded most recent conf data from datastore.')
  except:
    logging.warning('Tried but failed to fetch latest conf data from the '
                    'datastore.')

  if config:
    memcache.set(app_version, db.model_to_protobuf(config).Encode(),
                 namespace=NAMESPACE)
    logging.debug('Wrote most recent conf data into memcache.')

  return config


def _fetch_latest_from_memcache(app_version):
  """Get the latest configuration data for this app-version from memcache.

  Args:
    app_version: the major version you want configuration data for.

  Returns:
    A Config class instance for most recently set options or None if none
    could be found in memcache.
  """
  proto_string = memcache.get(app_version, namespace=NAMESPACE)
  if proto_string:
    logging.debug('Loaded most recent conf data from memcache.')
    return db.model_from_protobuf(proto_string)

  logging.debug('Tried to load conf data from memcache, but found nothing.')
  return None


def _inspect_environment():
  """Return relevant information from the cgi environment.

  This is mostly split out to simplify testing.

  Returns:
    A tuple: (app_version, conf_version, development)
    app_version: the major version of the current application.
    conf_version: the current configuration version.
    development: a boolean, True if we're running under devappserver.
  """
  app_version = os.environ['CURRENT_VERSION_ID'].rsplit('.', 1)[0]
  conf_version = int(os.environ.get('CURRENT_CONFIGURATION_VERSION', '0'))
  development = os.environ.get('SERVER_SOFTWARE', '').startswith('Development/')
  return (app_version, conf_version, development)


def refresh():
  """Update the local config cache from memcache/datastore.

  Normally configuration parameters are only refreshed at the start of a
  new request.  If you have a very long running request, or you just need
  the freshest data for some reason, you can call this function to force
  a refresh.
  """
  app_version, _, _ = _inspect_environment()




  global _cached_config

  new_config = _fetch_latest_from_memcache(app_version)

  if not new_config:
    new_config = _fetch_latest_from_datastore(app_version)

  if new_config:
    _cached_config = new_config


def _new_request():
  """Test if this is the first call to this function in the current request.

  This function will return True exactly once for each request
  Subsequent calls in the same request will return False.

  Returns:
    True if this is the first call in a given request, False otherwise.
  """
  if RESERVED_MARKER in os.environ:
    return False

  os.environ[RESERVED_MARKER] = RESERVED_MARKER
  return True


def _get_config():
  """Check if the current cached config is stale, and if so update it."""







  app_version, current_config_version, development = _inspect_environment()

  global _cached_config

  if (development and _new_request()) or not _cached_config:
    _cached_config = _fetch_from_local_file() or Config()

  if _cached_config.ah__conf__version < current_config_version:
    newconfig = _fetch_latest_from_memcache(app_version)
    if not newconfig or newconfig.ah__conf__version < current_config_version:
      newconfig = _fetch_latest_from_datastore(app_version)



    _cached_config = newconfig or _cached_config

  return _cached_config


def get(name, default=None):
  """Get the value of a configuration parameter.

  This function is guaranteed to return the same value for every call
  during a single request.

  Args:
    name: The name of the configuration parameter you want a value for.
    default: A default value to return if the named parameter doesn't exist.

  Returns:
    The string value of the configuration parameter.
  """
  return getattr(_get_config(), name, default)


def get_all():
  """Return an object with an attribute for each conf parameter.

  Returns:
    An object with an attribute for each conf parameter.
  """
  return _get_config()
