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




"""Used to parse app.yaml files while following builtins/includes directives."""













import logging
import os

from google.appengine.api import appinfo
from google.appengine.api import appinfo_errors
from google.appengine.ext import builtins


class IncludeFileNotFound(Exception):
  """Raised if a specified include file cannot be found on disk."""


def Parse(appinfo_file, open_fn=open):
  """Parse an AppYaml file and merge referenced includes and builtins.

  Args:
    appinfo_file: an opened file, for example the result of open('app.yaml').
    open_fn: a function to open included files.

  Returns:
    The parsed appinfo.AppInfoExternal object.
  """
  appyaml, _ = ParseAndReturnIncludePaths(appinfo_file, open_fn)
  return appyaml


def ParseAndReturnIncludePaths(appinfo_file, open_fn=open):
  """Parse an AppYaml file and merge referenced includes and builtins.

  Args:
    appinfo_file: an opened file, for example the result of open('app.yaml').
    open_fn: a function to open included files.

  Returns:
    A tuple where the first element is the parsed appinfo.AppInfoExternal
    object and the second element is a list of the absolute paths of the
    included files, in no particular order.
  """
  try:
    appinfo_path = appinfo_file.name
    if not os.path.isfile(appinfo_path):
      raise Exception('Name defined by appinfo_file does not appear to be a '
                      'valid file: %s' % appinfo_path)
  except AttributeError:
    raise Exception('File object passed to ParseAndMerge does not define '
                    'attribute "name" as as full file path.')

  appyaml = appinfo.LoadSingleAppInfo(appinfo_file)
  appyaml, include_paths = _MergeBuiltinsIncludes(appinfo_path, appyaml,
                                                  open_fn)


  if not appyaml.handlers:

    if appyaml.IsVm():
      appyaml.handlers = [appinfo.URLMap(url='.*', script='PLACEHOLDER')]
    else:
      raise appinfo_errors.MissingURLMapping(
          'No URLMap entries found in application configuration')
  if len(appyaml.handlers) > appinfo.MAX_URL_MAPS:
    raise appinfo_errors.TooManyURLMappings(
        'Found more than %d URLMap entries in application configuration' %
        appinfo.MAX_URL_MAPS)
  if appyaml.runtime == 'python27' and appyaml.threadsafe:
    for handler in appyaml.handlers:
      if (handler.script and (handler.script.endswith('.py') or
                              '/' in handler.script)):
        raise appinfo_errors.ThreadsafeWithCgiHandler(
            'Threadsafe cannot be enabled with CGI handler: %s' %
            handler.script)

  return appyaml, include_paths


def _MergeBuiltinsIncludes(appinfo_path, appyaml, open_fn=open):
  """Merges app.yaml files from builtins and includes directives in appyaml.

  Args:
    appinfo_path: the application directory.
    appyaml: the yaml file to obtain builtins and includes directives from.
    open_fn: file opening function to pass to _ResolveIncludes, used when
             reading yaml files.

  Returns:
    A tuple where the first element is the modified appyaml object
    incorporating the referenced yaml files, and the second element is a list
    of the absolute paths of the included files, in no particular order.
  """



  if not appyaml.builtins:
    appyaml.builtins = [appinfo.BuiltinHandler(default='on')]

  else:
    if not appinfo.BuiltinHandler.IsDefined(appyaml.builtins, 'default'):
      appyaml.builtins.append(appinfo.BuiltinHandler(default='on'))



  runtime_for_including = appyaml.runtime
  if runtime_for_including == 'vm':
    runtime_for_including = appyaml.vm_settings.get('vm_runtime', 'python27')
  aggregate_appinclude, include_paths = (
      _ResolveIncludes(appinfo_path,
                       appinfo.AppInclude(builtins=appyaml.builtins,
                                          includes=appyaml.includes),
                       os.path.dirname(appinfo_path),
                       runtime_for_including,
                       open_fn=open_fn))

  return (
      appinfo.AppInclude.MergeAppYamlAppInclude(appyaml,
                                                aggregate_appinclude),
      include_paths)


def _ResolveIncludes(included_from, app_include, basepath, runtime, state=None,
                     open_fn=open):
  """Recursively includes all encountered builtins/includes directives.

  This function takes an initial AppInclude object specified as a parameter
  and recursively evaluates every builtins/includes directive in the passed
  in AppInclude and any files they reference.  The sole output of the function
  is an AppInclude object that is the result of merging all encountered
  AppInclude objects.  This must then be merged with the root AppYaml object.

  Args:
    included_from: file that included file was included from.
    app_include: the AppInclude object to resolve.
    basepath: application basepath.
    runtime: name of the runtime.
    state: contains the list of included and excluded files as well as the
           directives of all encountered AppInclude objects.
    open_fn: file opening function udes, used when reading yaml files.

  Returns:
    A two-element tuple where the first element is the AppInclude object merged
    from following all builtins/includes defined in provided AppInclude object;
    and the second element is a list of the absolute paths of the included
    files, in no particular order.

  Raises:
    IncludeFileNotFound: if file specified in an include statement cannot be
      resolved to an includeable file (result from _ResolvePath is False).
  """

  class RecurseState(object):





    def __init__(self):
      self.includes = {}
      self.excludes = {}
      self.aggregate_appinclude = appinfo.AppInclude()


  if not state:
    state = RecurseState()


  appinfo.AppInclude.MergeAppIncludes(state.aggregate_appinclude, app_include)


  includes_list = _ConvertBuiltinsToIncludes(included_from, app_include,
                                             state, runtime)


  includes_list.extend(app_include.includes or [])


  for i in includes_list:
    inc_path = _ResolvePath(included_from, i, basepath)
    if not inc_path:
      raise IncludeFileNotFound('File %s listed in includes directive of %s '
                                'could not be found.' % (i, included_from))

    if inc_path in state.excludes:
      logging.warning('%s already disabled by %s but later included by %s',
                      inc_path, state.excludes[inc_path], included_from)
    elif not inc_path in state.includes:
      state.includes[inc_path] = included_from
      yaml_file = open_fn(inc_path, 'r')
      try:
        inc_yaml = appinfo.LoadAppInclude(yaml_file)
        _ResolveIncludes(inc_path, inc_yaml, basepath, runtime, state=state,
                         open_fn=open_fn)
      except appinfo_errors.EmptyConfigurationFile:

        if not os.path.basename(os.path.dirname(inc_path)) == 'default':
          logging.warning('Nothing to include in %s', inc_path)


  return state.aggregate_appinclude, state.includes.keys()


def _ConvertBuiltinsToIncludes(included_from, app_include, state, runtime):
  """Converts builtins directives to includes directives.

  Moves all builtins directives in app_include into the includes
  directives list.  Modifies class excludes dict if any builtins are
  switched off.  Class includes dict is used to determine if an excluded
  builtin was previously included.

  Args:
    included_from: file that builtin directive was found in
    app_include: the AppInclude object currently being processed.
    state: contains the list of included and excluded files as well as the
           directives of all encountered AppInclude objects.
    runtime: name of the runtime.

  Returns:
    list of the absolute paths to the include files for builtins where
    "x: on" directive was specified, e.g. "builtins:\n  default: on" ->
    ['/google/appengine/ext/builtins/default/include.yaml']
  """
  includes_list = []
  if app_include.builtins:
    builtins_list = appinfo.BuiltinHandler.ListToTuples(app_include.builtins)
    for builtin_name, on_or_off in builtins_list:

      if not on_or_off:
        continue


      yaml_path = builtins.get_yaml_path(builtin_name, runtime)

      if on_or_off == 'on':
        includes_list.append(yaml_path)
      elif on_or_off == 'off':
        if yaml_path in state.includes:
          logging.warning('%s already included by %s but later disabled by %s',
                          yaml_path, state.includes[yaml_path], included_from)
        state.excludes[yaml_path] = included_from
      else:
        logging.error('Invalid state for AppInclude object loaded from %s; '
                      'builtins directive "%s: %s" ignored.',
                      included_from, builtin_name, on_or_off)

  return includes_list


def _ResolvePath(included_from, included_path, basepath):
  """Gets the absolute path of the file to be included.

  Resolves in the following order:
  - absolute path or relative to working directory
    (path as specified resolves to a file)
  - relative to basepath
    (basepath + path resolves to a file)
  - relative to file it was included from
    (included_from + included_path resolves to a file)

  Args:
    included_from: absolute path of file that included_path was included from.
    included_path: file string from includes directive.
    basepath: the application directory.

  Returns:
    absolute path of the first file found for included_path or ''.
  """







  path = os.path.join(os.path.dirname(included_from), included_path)
  if not _IsFileOrDirWithFile(path):

    path = os.path.join(basepath, included_path)
    if not _IsFileOrDirWithFile(path):

      path = included_path
      if not _IsFileOrDirWithFile(path):
        return ''

  if os.path.isfile(path):
    return os.path.normcase(os.path.abspath(path))

  return os.path.normcase(os.path.abspath(os.path.join(path, 'include.yaml')))


def _IsFileOrDirWithFile(path):
  """Determine if a path is a file or a directory with an appropriate file."""
  return os.path.isfile(path) or (
      os.path.isdir(path) and
      os.path.isfile(os.path.join(path, 'include.yaml')))
