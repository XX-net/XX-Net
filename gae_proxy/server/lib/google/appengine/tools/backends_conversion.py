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


"""Tool for converting Backends configuration to Modules configuration.

Uses existing backends.yaml and app.yaml files to create a separate
<module-name>.yaml file for each module defined in backends.yaml.
"""

from __future__ import with_statement

import os
import sys
import warnings

from google.appengine.api import appinfo
from google.appengine.api import backendinfo


warnings.simplefilter('default')


__all__ = [
    'ConvertBackendToModules',
]


START_URI = '/_ah/start'
LOGIN_ADMIN = 'admin'
DEPRECATION_TEXT = ('The failfast option is deprecated for Modules. No '
                    'equivalent option will be set.')
DYNAMIC_PROMPT_TEXT = """\
Backend %s is marked dynamic.
Dynamic backends should be converted to basic_scaling type.
Basic scaling modules require an integer max instances value.
Please provide the max_instances [default: 1]: """
MAIN_ERR_MESSAGE = """\
Backends and App Config filename arguments not passed
in correctly. Can't complete operation.
"""
PRINT_FILE_DELIMITER = ('=' * 80) + '\n' + ('=' * 80)


def _ToYAMLDefault(appinfo_config):
  """Converts an app config to default (alphabetical by key) YAML string.

  Args:
    appinfo_config: appinfo.AppInfoExternal object. Configuration object
      for either a module or app.yaml.

  Returns:
    String containing YAML for the app config object.
  """
  return appinfo_config.ToYAML()



def ConvertBackendToModules(backend_config_filename,
                            app_config_filename,
                            _to_yaml_method=_ToYAMLDefault):
  """Creates Modules configuration using filenames of app and backend config.

  Tries to write config to a file for each module defined.

  Args:
    backend_config_filename: String; Relative path to backends.yaml passed in.
    app_config_filename: String; Relative path to app.yaml passed in.
    _to_yaml_method: A method which takes an appinfo.AppInfoExternal object and
      converts it to a YAML string. Defaults to _ToYAMLDefault which just calls
      ToYAML() on the object.
  """
  with open(backend_config_filename, 'r') as fh:
    backend_config = fh.read()
  with open(app_config_filename, 'r') as fh:
    app_config = fh.read()


  application_root, app_config_filename = os.path.split(
      os.path.abspath(app_config_filename))
  converted_backends = _ConvertBackendToModules(backend_config, app_config)
  for module_config in converted_backends:
    _MaybeWriteConfigToFile(module_config, application_root,
                            _to_yaml_method=_to_yaml_method)


def _MaybeWriteConfigToFile(appinfo_config, application_root,
                            _to_yaml_method=_ToYAMLDefault):
  """Writes an app config to a file.

  If the file already exists, prompts the user before saving. If the user
  does not wish to overwrite the file, prints the would-be file contents.

  Args:
    appinfo_config: appinfo.AppInfoExternal object. Configuration object
      for either a module or app.yaml.
    application_root: String; an absolute path where the application to be
      deployed is located on the local filesystem.
    _to_yaml_method: A method which takes an appinfo.AppInfoExternal object and
      converts it to a YAML string. Defaults to _ToYAMLDefault which just calls
      ToYAML() on the object.
  """
  filename = '%s.yaml' % (appinfo_config.module.encode('ascii'),)
  filepath = os.path.join(application_root, filename)

  contents = _to_yaml_method(appinfo_config)
  if os.path.exists(filepath):
    prompt = 'File %s exists. Overwrite? [y/N] ' % (filename,)
    result = raw_input(prompt).strip()
    if result != 'y':
      print 'File %s not written.' % (filename,)
      print 'Contents:'
      print PRINT_FILE_DELIMITER
      print contents
      print PRINT_FILE_DELIMITER
      return

  with open(filepath, 'w') as fh:
    fh.write(contents)



def _ConvertBackendToModules(backend_config, app_config):
  """Creates Modules configuration using app and backend config.

  Parses the app.yaml and backend.yaml contents into native AppInfoExternal
  and BackendInfoExternal objects and then creates an AppInfoExternal
  for each backend defined in backend_config.

  Args:
    backend_config: String, the contents of backend.yaml.
    app_config: String, the contents of app.yaml.

  Returns:
    A list of AppInfoExternal objects for each module.
  """
  backend_info = backendinfo.LoadBackendInfo(backend_config)
  app_yaml_config = appinfo.LoadSingleAppInfo(app_config)
  return [_ConvertBackendToModule(backend, app_yaml_config)
          for backend in backend_info.backends]


def _ConvertBackendToModule(backend_entry, app_yaml_config):
  """Converts an individual backend to a module config.

  Args:
    backend_entry: A backendinfo.BackendEntry object. Contains a parsed backend
      definition from backends.yaml.
    app_yaml_config: A appinfo.AppInfoExternal object. Contains parsed app.yaml.

  Returns:
    An appinfo.AppInfoExternal object which is a copy of app.yaml patched with
      the backend definition.
  """
  result = _CopyAppInfo(app_yaml_config)


  _MaybeSetNotPublic(result, backend_entry)

  _WarnFailFast(backend_entry)

  _SetStart(result, backend_entry)
  _SetModule(result, backend_entry)
  _SetClass(result, backend_entry)
  _SetScalingType(result, backend_entry)
  return result


def _CopyAppInfo(app_yaml_config):
  """Deep copy of parsed YAML config.

  Casts native YAML object to string and then back again.

  Args:
    app_yaml_config: A appinfo.AppInfoExternal object. Contains parsed app.yaml.

  Returns:
    Deep copy of app_yaml_config.
  """
  as_yaml = app_yaml_config.ToYAML()
  return appinfo.LoadSingleAppInfo(as_yaml)


def _MaybeSetNotPublic(target, backend_entry):
  """Attempts to set all handlers as login: admin if the backend is private.

  Prompts user if this operation is desired before doing so. If the user
  declines, does nothing.

  Args:
    target: A appinfo.AppInfoExternal object. Contains parsed app.yaml augmented
      by current backend info.
    backend_entry: A backendinfo.BackendEntry object. Contains a parsed backend
      definition from backends.yaml.
  """
  if backend_entry.public:
    return

  prompt = ('Backend %s is marked private.\nWould you like to make all '
            'handlers \'login: admin\'? [y/N] ' % (backend_entry.name,))
  result = raw_input(prompt).strip()
  if result == 'y':
    for handler in target.handlers:
      handler.login = LOGIN_ADMIN


def _WarnFailFast(backend_entry):
  """Warns if the deprecated failfast option is used in the backend.

  Args:
    backend_entry: A backendinfo.BackendEntry object. Contains a parsed backend
      definition from backends.yaml.
  """
  if backend_entry.failfast:
    warnings.warn(DEPRECATION_TEXT, DeprecationWarning)


def _RemoveStartHandler(app_yaml_config):
  """Removes a start handler from an application config if one is defined.

  If multiple start handlers are defined, only the first would be used (since
  routing goes in order of first to last).

  Args:
    app_yaml_config: A appinfo.AppInfoExternal object. Contains parsed app.yaml.

  Returns:
    Either None, if there is no start handler or the removed appinfo.URLMap
      object containing the start handler info.
  """
  handlers = app_yaml_config.handlers
  start_handlers = []
  for handler in handlers:
    if handler.url == START_URI:

      start_handlers.append(handler)

  if start_handlers:
    for start_handler in start_handlers:
      handlers.remove(start_handler)

    return start_handlers[0]


def _SetStart(target, backend_entry):
  """Attempts to set a start handler for the target module.

  This only gets set if there is a start script defined for the backend. If
  there was also a start handler in app.yaml, will copy this and use the
  existing handler, replacing the script with the one from the backend.

  Args:
    target: A appinfo.AppInfoExternal object. Contains parsed app.yaml augmented
      by current backend info.
    backend_entry: A backendinfo.BackendEntry object. Contains a parsed backend
      definition from backends.yaml.
  """
  if backend_entry.start is None:
    return

  start_handler = _RemoveStartHandler(target)
  if start_handler is None:
    start_handler = appinfo.URLMap(url=START_URI, login=LOGIN_ADMIN)

  start_handler.script = backend_entry.start
  target.handlers.insert(0, start_handler)


def _SetModule(target, backend_entry):
  """Sets module name to backend name.

  Args:
    target: A appinfo.AppInfoExternal object. Contains parsed app.yaml augmented
      by current backend info.
    backend_entry: A backendinfo.BackendEntry object. Contains a parsed backend
      definition from backends.yaml.
  """
  target.module = backend_entry.name


def _SetClass(target, backend_entry):
  """Sets module instance class to backend instance class.

  If there was no instance class defined on the backend, does nothing.

  Args:
    target: A appinfo.AppInfoExternal object. Contains parsed app.yaml augmented
      by current backend info.
    backend_entry: A backendinfo.BackendEntry object. Contains a parsed backend
      definition from backends.yaml.
  """
  curr_class = backend_entry.get_class()
  if curr_class is not None:
    target.instance_class = curr_class


def _SetManualScaling(target, backend_entry):
  """Sets scaling type to manual with specified number of instances.

  If instances not defined in backend does nothing. Otherwise, sets the manual
  scaling field to use the number of instances specified.

  Args:
    target: A appinfo.AppInfoExternal object. Contains parsed app.yaml augmented
      by current backend info.
    backend_entry: A backendinfo.BackendEntry object. Contains a parsed backend
      definition from backends.yaml.
  """
  instances = backend_entry.instances
  if instances is not None:
    target.manual_scaling = appinfo.ManualScaling(instances=instances)


def _GetInstances(name):
  """Gets a positive number of instances from the user.

  Uses the DYNAMIC_PROMPT_TEXT to prompt the user. Accepts no
  input to mean the default value of 1.

  Args:
    name: String, name of module.

  Returns:
    Integer parsed from user input, 1 if empty input or None if the input was
      not a positive integer.
  """
  prompt = DYNAMIC_PROMPT_TEXT % (name,)
  result = raw_input(prompt).strip()
  if result == '':
    return 1

  max_instances = -1
  try:
    max_instances = int(result)
  except (TypeError, ValueError):
    pass

  if max_instances <= 0:
    print 'Invalid max_instances value: %r' % (result,)
    return

  return max_instances


def _SetScalingType(target, backend_entry):
  """Sets the scaling type of the modules based on the backend.

  If dynamic, sets scaling type to Basic and passes the number of instances if
  set in the backends config. If not dynamic but instances set, calls to
  _SetManualScaling. If neither dynamic or instances set, does nothing.

  Args:
    target: A appinfo.AppInfoExternal object. Contains parsed app.yaml augmented
      by current backend info.
    backend_entry: A backendinfo.BackendEntry object. Contains a parsed backend
      definition from backends.yaml.
  """
  if not (backend_entry.dynamic or backend_entry.instances):
    return


  if not backend_entry.dynamic:
    _SetManualScaling(target, backend_entry)
    return

  if backend_entry.instances:
    max_instances = backend_entry.instances
  else:
    max_instances = _GetInstances(backend_entry.name)

  if max_instances:
    target.basic_scaling = appinfo.BasicScaling(max_instances=max_instances)


def MakeParser(prog):
  """Create an argument parser.

  Args:
    prog: The name of the program to use when outputting help text.

  Returns:
    An argparse.ArgumentParser built to specification.
  """



  import argparse
  parser = argparse.ArgumentParser(prog=prog)
  parser.add_argument('backend_config_filename', nargs=1,
                      help='Path to backends.yaml for application.')
  parser.add_argument('app_config_filename', nargs=1,
                      help='Path to app.yaml for application.')
  return parser


def main(argv):
  parser = MakeParser(argv[0])
  args = parser.parse_args(argv[1:])

  backend_config_filename_args = getattr(args, 'backend_config_filename', [])
  app_config_filename_args = getattr(args, 'app_config_filename', [])
  if (len(backend_config_filename_args) != 1 or
      len(app_config_filename_args) != 1):
    print >>sys.stderr, MAIN_ERR_MESSAGE
    return 1

  ConvertBackendToModules(backend_config_filename_args[0],
                          app_config_filename_args[0])
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))
