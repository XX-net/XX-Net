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
"""A sandbox implementation that emulates production App Engine."""



import __builtin__
import imp
import os
import re
import sys
import traceback
import types

import google

from google.appengine import dist
from google.appengine.api import app_logging
from google.appengine.api.logservice import logservice
from google.appengine import dist27 as dist27
from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.runtime import request_environment
from google.appengine.tools.devappserver2.python import pdb_sandbox
from google.appengine.tools.devappserver2.python import request_state
from google.appengine.tools.devappserver2.python import stubs

# Needed to handle source file encoding
CODING_MAGIC_COMMENT_RE = re.compile('coding[:=]\s*([-\w.]+)')
DEFAULT_ENCODING = 'ascii'

_C_MODULES = frozenset(['cv', 'Crypto', 'lxml', 'numpy', 'PIL'])

NAME_TO_CMODULE_WHITELIST_REGEX = {
    'cv': re.compile(r'cv(\..*)?$'),
    'lxml': re.compile(r'lxml(\..*)?$'),
    'numpy': re.compile(r'numpy(\..*)?$'),
    'pycrypto': re.compile(r'Crypto(\..*)?$'),
    'PIL': re.compile(r'(PIL(\..*)?|_imaging|_imagingft|_imagingmath)$'),
    'ssl': re.compile(r'_ssl$'),
}

# Maps App Engine third-party library names to the Python package name for
# libraries whose names differ from the package names.
_THIRD_PARTY_LIBRARY_NAME_OVERRIDES = {
    'pycrypto': 'Crypto',
}

# The location of third-party libraries will be different for the packaged SDK.
_THIRD_PARTY_LIBRARY_FORMAT_STRING = (
    'lib/%(name)s-%(version)s')

# Store all the modules removed from sys.modules so they don't get cleaned up.
_removed_modules = []

_open_hooks = []


def add_open_hook(install_open_hook):
  """Hook the open chain to allow files to be opened from FS-like containers.

  In order to allow files to be opened from FS-like containers such as zip
  files, provide a sandbox compatible way to hook into the open chain. To
  correctly work with our sandbox, these hooks must be called before FakeFile.
  Due to code flow, the easiest way to allow that is for code to provide an
  install function that the sandbox calls at the appropriate time.

  Hook functions are expected to only handle paths that cannot be handled by
  the standard filesystem open and are expected to forward all other paths
  to the next hook. Hook functions are responsible for saving the next hook
  function by getting the value of __builtin__.open when the install function
  is called (very key point here, make sure to evaluate __builtin__.open when
  your install function is called and not at import time).

  Args:
    install_open_hook: a method of no parameters that will install an open
      hook.
  """
  _open_hooks.append(install_open_hook)


def _make_request_id_aware_start_new_thread(base_start_new_thread):
  """Returns a replacement for start_new_thread that inherits request id.

  Returns a function with an interface that matches thread.start_new_thread
  where the new thread inherits the request id of the current thread. The
  request id is used by the Remote API to associate API calls with the HTTP
  request that provoked them.

  Args:
    base_start_new_thread: The thread.start_new_thread function to call to
        create a new thread.

  Returns:
    A replacement for start_new_thread.
  """

  def _start_new_thread(target, args, kw=None):
    if kw is None:
      kw = {}

    request_id = remote_api_stub.RemoteStub._GetRequestId()
    request = request_state.get_request_state(request_id)

    def _run():
      try:
        remote_api_stub.RemoteStub._SetRequestId(request_id)
        request.start_thread()
        target(*args, **kw)
      finally:
        request_environment.current_request.Clear()
        request.end_thread()
    return base_start_new_thread(_run, ())
  return _start_new_thread


def enable_sandbox(config):
  """Enable the sandbox based on the configuration.

  This includes installing import hooks to restrict access to C modules and
  stub out functions that are not implemented in production, replacing the file
  builtins with read-only versions and add enabled libraries to the path.

  Args:
    config: The runtime_config_pb2.Config to use to configure the sandbox.
  """









  devnull = open(os.path.devnull)
  modules = [os, traceback, google]
  c_module = _find_shared_object_c_module()
  if c_module:
    modules.append(c_module)
  module_paths = [module.__file__ for module in modules]
  module_paths.extend([os.path.realpath(module.__file__) for module in modules])
  python_lib_paths = [config.application_root]
  for path in sys.path:
    if any(module_path.startswith(path) for module_path in module_paths):
      python_lib_paths.append(path)
  python_lib_paths.extend(_enable_libraries(config.libraries))
  # Note that the above code (see _find_shared_object_c_module) imports modules
  # that must be pruned so please use care if you move the call to
  # _prune_sys_modules.
  _prune_sys_modules()
  path_override_hook = PathOverrideImportHook(
      set(_THIRD_PARTY_LIBRARY_NAME_OVERRIDES.get(lib.name, lib.name)
          for lib in config.libraries).intersection(_C_MODULES))
  python_lib_paths.extend(path_override_hook.extra_sys_paths)
  if not config.vm:
    _install_fake_file(config, python_lib_paths, path_override_hook)
    _install_open_hooks()

  # NOTE(bryanmau): The sys.platform was a hack needed to solve
  # b/7482060.  After python version 2.7.4 this is no longer needed.
  def was_created_before(ver1, ver2):
    """Returns true if the integer tuple ver1 is less than the tuple ver2."""
    if ver1[0] != ver2[0]:
      return ver1[0] < ver2[0]
    elif ver1[1] != ver2[1]:
      return ver1[1] < ver2[1]
    else:
      return ver1[2] < ver2[2]

  if was_created_before(sys.version_info, (2, 7, 4)):
    sys.platform = 'linux3'

  _install_import_hooks(config, path_override_hook)
  sys.path_importer_cache = {}
  if not config.vm:
    sys.path = python_lib_paths[:]
  else:
    # Use anything present on the sys.path if the runtime is on a vm.
    # This lets users use deps installed with pip.
    sys.path.extend(python_lib_paths)

  thread = __import__('thread')
  __import__('%s.threading' % dist27.__name__)
  threading = sys.modules['%s.threading' % dist27.__name__]
  thread.start_new_thread = _make_request_id_aware_start_new_thread(
      thread.start_new_thread)
  # This import needs to be after enabling the sandbox so it imports the
  # sandboxed version of the logging module.
  from google.appengine.runtime import runtime
  runtime.PatchStartNewThread(thread)
  threading._start_new_thread = thread.start_new_thread

  os.chdir(config.application_root)
  sandboxed_os = __import__('os')
  request_environment.PatchOsEnviron(sandboxed_os)
  os.__dict__.update(sandboxed_os.__dict__)
  _init_logging(config.stderr_log_level)
  pdb_sandbox.install(config)
  sys.stdin = devnull
  sys.stdout = sys.stderr


def _prune_sys_modules():
  """Prune sandboxed modules from sys.modules."""
  for name in list(sys.modules):
    if not _should_keep_module(name):
      _removed_modules.append(sys.modules[name])
      del sys.modules[name]


def _install_import_hooks(config, path_override_hook):
  """Install runtime's import hooks.

  These hooks customize the import process as per
  https://docs.python.org/2/library/sys.html#sys.meta_path .

  Args:
    config: An apphosting/tools/devappserver2/runtime_config.proto
        for this instance.
    path_override_hook: A hook for importing special appengine
        versions of select libraries from the libraries
        section of the current module's app.yaml file.
  """
  if not config.vm:
    enabled_library_regexes = [
        NAME_TO_CMODULE_WHITELIST_REGEX[lib.name] for lib in config.libraries
        if lib.name in NAME_TO_CMODULE_WHITELIST_REGEX]
    sys.meta_path = [
        StubModuleImportHook(),
        ModuleOverrideImportHook(_MODULE_OVERRIDE_POLICIES),
        CModuleImportHook(enabled_library_regexes),
        path_override_hook,
        PyCryptoRandomImportHook,
        PathRestrictingImportHook(enabled_library_regexes)]
  else:
    sys.meta_path = [
        # Picks up custom versions of certain libraries in the libraries section
        #     of app.yaml
        path_override_hook,
        # Picks up a custom version of Crypto.Random.OSRNG.posix.
        # TODO: Investigate removing this as it may not be needed
        #     for vms since they are able to read /dev/urandom, I left it for
        #     consistency.
        PyCryptoRandomImportHook]


def _install_fake_file(config, python_lib_paths, path_override_hook):
  """Install a stub file implementation to enforce sandbox rules."""
  stubs.FakeFile.set_allowed_paths(config.application_root,
                                   python_lib_paths[1:] +
                                   path_override_hook.extra_accessible_paths)
  stubs.FakeFile.set_skip_files(config.skip_files)
  stubs.FakeFile.set_static_files(config.static_files)
  __builtin__.file = stubs.FakeFile
  __builtin__.open = stubs.FakeFile
  types.FileType = stubs.FakeFile


def _install_open_hooks():
  """Install open hooks for sandbox."""
  if _open_hooks:
    for install_open_hook in _open_hooks:
      install_open_hook()
    # Assume installed open hooks don't enforce the sandbox path restrictions
    # and install a final hook to do that (the goal of hooks is to allow
    # alternate open techniques, not to circumvent the sandbox). It does mean
    # that open requests that make it to FakeFile have their path checked
    # twice but that doesn't break anything.
    __builtin__.open = stubs.RestrictedPathFunction(__builtin__.open, IOError)


def _find_shared_object_c_module():
  for module_name in ['_sqlite3', '_multiprocessing', '_ctypes', 'bz2']:
    try:
      module = __import__(module_name)
    except ImportError:
      continue
    else:
      if hasattr(module, '__file__'):
        return module
  return None


def _should_keep_module(name):
  """Returns True if the module should be retained after sandboxing."""
  return (name in ('__builtin__', 'sys', 'codecs', 'encodings', 'site',
                   'google') or
          name.startswith('google.') or name.startswith('encodings.') or




          # Making mysql available is a hack to make the CloudSQL functionality
          # work.
          'mysql' in name.lower())


def _init_logging(stderr_log_level):
  logging = __import__('logging')
  logger = logging.getLogger()

  console_handler = logging.StreamHandler(sys.stderr)
  if stderr_log_level == 0:
    console_handler.setLevel(logging.DEBUG)
  elif stderr_log_level == 1:
    console_handler.setLevel(logging.INFO)
  elif stderr_log_level == 2:
    console_handler.setLevel(logging.WARNING)
  elif stderr_log_level == 3:
    console_handler.setLevel(logging.ERROR)
  elif stderr_log_level == 4:
    console_handler.setLevel(logging.CRITICAL)

  console_handler.setFormatter(logging.Formatter(
      '%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s] %(message)s'))
  logger.addHandler(console_handler)

  logging_stream = request_environment.RequestLocalStream(
      request_environment.current_request)
  logger.addHandler(app_logging.AppLogsHandler())
  logger.setLevel(logging.DEBUG)
  logservice.logs_buffer = lambda: request_environment.current_request.errors
  sys.stderr = Tee(sys.stderr, logging_stream)


class Tee(object):
  """A writeable stream that forwards to zero or more streams."""

  def __init__(self, *streams):
    self._streams = streams

  def close(self):
    for stream in self._streams:
      stream.close()

  def flush(self):
    for stream in self._streams:
      stream.flush()

  def write(self, data):
    for stream in self._streams:
      stream.write(data)

  def writelines(self, data):
    for stream in self._streams:
      stream.writelines(data)


def _enable_libraries(libraries):
  """Add enabled libraries to the path.

  Args:
    libraries: A repeated Config.Library containing the libraries to enable.

  Returns:
    A list of paths containing the enabled libraries.
  """
  library_dirs = []
  library_pattern = os.path.join(os.path.dirname(
      os.path.dirname(google.__file__)), _THIRD_PARTY_LIBRARY_FORMAT_STRING)
  for library in libraries:
    # Encode the library name/version to convert the Python type
    # from unicode to str so that Python doesn't try to decode
    # library pattern from str to unicode (which can cause problems
    # when the SDK has non-ASCII data in the directory). Encode as
    # ASCII should be safe as we control library info and are not
    # likely to have non-ASCII names/versions.
    library_dir = os.path.abspath(
        library_pattern % {'name': library.name.encode('ascii'),
                           'version': library.version.encode('ascii')})
    library_dirs.append(library_dir)
  return library_dirs


class BaseImportHook(object):
  """A base class implementing common import hook functionality.

  This provides utilities for implementing both the finder and loader parts of
  the PEP 302 importer protocol and implements the optional extensions to the
  importer protocol.
  """

  def _find_module_or_loader(self, submodule_name, fullname, path):
    """Acts like imp.find_module with support for path hooks.

    Args:
      submodule_name: The name of the submodule within its parent package.
      fullname: The full name of the module to load.
      path: A list containing the paths to search for the module.

    Returns:
      A tuple (source_file, path_name, description, loader) where:
        source_file: An open file or None.
        path_name: A str containing the path to the module.
        description: A description tuple like the one imp.find_module returns.
        loader: A PEP 302 compatible path hook. If this is not None, then the
            other elements will be None.

    Raises:
      ImportError: The module could not be imported.
    """
    for path_entry in path + [None]:
      result = self._find_path_hook(submodule_name, fullname, path_entry)
      if result is not None:
        break
    else:
      raise ImportError('No module named %s' % fullname)
    if isinstance(result, tuple):
      return result + (None,)
    else:
      return None, None, None, result.find_module(fullname)

  def _find_and_load_module(self, submodule_name, fullname, path):
    """Finds and loads a module, using a provided search path.

    Args:
      submodule_name: The name of the submodule within its parent package.
      fullname: The full name of the module to load.
      path: A list containing the paths to search for the module.

    Returns:
      The requested module.

    Raises:
      ImportError: The module could not be imported.
    """
    source_file, path_name, description, loader = self._find_module_or_loader(
        submodule_name, fullname, path)
    if loader:
      return loader.load_module(fullname)
    try:
      return imp.load_module(fullname, source_file, path_name, description)
    finally:
      if source_file:
        source_file.close()

  def _find_path_hook(self, submodule, submodule_fullname, path_entry):
    """Helper for _find_and_load_module to find a module in a path entry.

    Args:
      submodule: The last portion of the module name from submodule_fullname.
      submodule_fullname: The full name of the module to be imported.
      path_entry: A single sys.path entry, or None representing the builtins.

    Returns:
      None if nothing was found, a PEP 302 loader if one was found or a
      tuple (source_file, path_name, description) where:
          source_file: An open file of the source file.
          path_name: A str containing the path to the source file.
          description: A description tuple to be passed to imp.load_module.
    """
    if path_entry is None:
      # This is the magic entry that tells us to look for a built-in module.
      if submodule_fullname in sys.builtin_module_names:
        try:
          result = imp.find_module(submodule)
        except ImportError:
          pass
        else:
          # Did find_module() find a built-in module?  Unpack the result.
          _, _, description = result
          _, _, file_type = description
          if file_type == imp.C_BUILTIN:
            return result
      # Skip over this entry if we get this far.
      return None

    # It's a regular sys.path entry.
    try:
      importer = sys.path_importer_cache[path_entry]
    except KeyError:
      # Cache miss; try each path hook in turn.
      importer = None
      for hook in sys.path_hooks:
        try:
          importer = hook(path_entry)
          # Success.
          break
        except ImportError:
          # This importer doesn't handle this path entry.
          pass
      # Cache the result, whether an importer matched or not.
      sys.path_importer_cache[path_entry] = importer

    if importer is None:
      # No importer.  Use the default approach.
      try:
        return imp.find_module(submodule, [path_entry])
      except ImportError:
        pass
    else:
      # Have an importer.  Try it.
      loader = importer.find_module(submodule_fullname)
      if loader is not None:
        # This importer knows about this module.
        return loader

    # None of the above.
    return None

  def _get_parent_package(self, fullname):
    """Retrieves the parent package of a fully qualified module name.

    Args:
      fullname: Full name of the module whose parent should be retrieved (e.g.,
        foo.bar).

    Returns:
      Module instance for the parent or None if there is no parent module.

    Raises:
      ImportError: The module's parent could not be found.
    """
    all_modules = fullname.split('.')
    parent_module_fullname = '.'.join(all_modules[:-1])
    if parent_module_fullname:
      __import__(parent_module_fullname)
      return sys.modules[parent_module_fullname]
    return None

  def _get_parent_search_path(self, fullname):
    """Determines the search path of a module's parent package.

    Args:
      fullname: Full name of the module to look up (e.g., foo.bar).

    Returns:
      Tuple (submodule, search_path) where:
        submodule: The last portion of the module name from fullname (e.g.,
          if fullname is foo.bar, then this is bar).
        search_path: List of paths that belong to the parent package's search
          path or None if there is no parent package.

    Raises:
      ImportError exception if the module or its parent could not be found.
    """
    _, _, submodule = fullname.rpartition('.')
    parent_package = self._get_parent_package(fullname)
    search_path = sys.path
    if parent_package is not None and hasattr(parent_package, '__path__'):
      search_path = parent_package.__path__
    return submodule, search_path

  def _get_module_info(self, fullname):
    """Determines the path on disk and the search path of a module or package.

    Args:
      fullname: Full name of the module to look up (e.g., foo.bar).

    Returns:
      Tuple (pathname, search_path, submodule, loader) where:
        pathname: String containing the full path of the module on disk,
            or None if the module wasn't loaded from disk (e.g. from a zipfile).
        search_path: List of paths that belong to the found package's search
            path or None if found module is not a package.
        submodule: The relative name of the submodule that's being imported.
        loader: A PEP 302 compatible path hook. If this is not None, then the
            other elements will be None.
    """
    submodule, search_path = self._get_parent_search_path(fullname)
    _, pathname, description, loader = self._find_module_or_loader(
        submodule, fullname, search_path)
    if loader:
      return None, None, None, loader
    else:
      _, _, file_type = description
      module_search_path = None
      if file_type == imp.PKG_DIRECTORY:
        module_search_path = [pathname]
        pathname = os.path.join(pathname, '__init__%spy' % os.extsep)
      return pathname, module_search_path, submodule, None

  def is_package(self, fullname):
    """Returns whether the module specified by fullname refers to a package.

    This implements part of the extensions to the PEP 302 importer protocol.

    Args:
      fullname: The fullname of the module.

    Returns:
      True if fullname refers to a package.
    """
    submodule, search_path = self._get_parent_search_path(fullname)
    _, _, description, loader = self._find_module_or_loader(
        submodule, fullname, search_path)
    if loader:
      return loader.is_package(fullname)
    _, _, file_type = description
    if file_type == imp.PKG_DIRECTORY:
      return True
    return False

  def get_source(self, fullname):
    """Returns the source for the module specified by fullname.

    This implements part of the extensions to the PEP 302 importer protocol.

    Args:
      fullname: The fullname of the module.

    Returns:
      The source for the module.
    """
    full_path, _, _, loader = self._get_module_info(fullname)
    if loader:
      return loader.get_source(fullname)
    if full_path is None:
      return None
    source_file = open(full_path)
    try:
      return source_file.read()
    finally:
      source_file.close()

  def get_code(self, fullname):
    """Returns the code object for the module specified by fullname.

    This implements part of the extensions to the PEP 302 importer protocol.

    Args:
      fullname: The fullname of the module.

    Returns:
      The code object associated the module.
    """
    full_path, _, _, loader = self._get_module_info(fullname)
    if loader:
      return loader.get_code(fullname)
    if full_path is None:
      return None
    source_file = open(full_path)
    try:
      source_code = source_file.read()
    finally:
      source_file.close()

    # Check that coding cookie is correct if present, error if not present and
    # we can't decode with the default of 'ascii'.  According to PEP 263 this
    # coding cookie line must be in the first or second line of the file.
    encoding = DEFAULT_ENCODING
    for line in source_code.split('\n', 2)[:2]:
      matches = CODING_MAGIC_COMMENT_RE.findall(line)
      if matches:
        encoding = matches[0].lower()
    # This may raise up to the user, which is what we want, however we ignore
    # the output because we don't want to return a unicode version of the code.
    source_code.decode(encoding)

    return compile(source_code, full_path, 'exec')


class PathOverrideImportHook(BaseImportHook):
  """An import hook that imports enabled modules from predetermined paths.

  Imports handled by this hook ignore the paths in sys.path, instead using paths
  discovered at initialization time.

  Attributes:
    extra_sys_paths: A list of paths that should be added to sys.path.
    extra_accessible_paths: A list of paths that should be accessible by
        sandboxed code.
  """

  def __init__(self, modules):
    self._modules = {}
    self.extra_accessible_paths = []
    self.extra_sys_paths = []
    for module in modules:
      module_path = self._get_module_path(module)
      if module_path:
        self._modules[module] = module_path
        if isinstance(module_path, str):
          package_dir = os.path.join(module_path, module)
          if os.path.isdir(package_dir):
            if module == 'PIL':
              self.extra_sys_paths.append(package_dir)
            else:
              self.extra_accessible_paths.append(package_dir)

  def find_module(self, fullname, unused_path=None):
    return fullname in self._modules and self or None

  def load_module(self, fullname):
    if fullname in sys.modules:
      return sys.modules[fullname]
    module_path = self._modules[fullname]
    if hasattr(module_path, 'load_module'):
      module = module_path.load_module(fullname)
    else:
      module = self._find_and_load_module(fullname, fullname, [module_path])
    module.__loader__ = self
    return module

  def _get_module_path(self, fullname):
    """Returns the directory containing the module or None if not found."""
    try:
      _, _, submodule = fullname.rpartition('.')
      f, filepath, _, loader = self._find_module_or_loader(
          submodule, fullname, sys.path)
    except ImportError:
      return None
    if f:
      f.close()
    if loader:
      return loader.find_module(fullname)
    return os.path.dirname(filepath)


class ModuleOverridePolicy(object):
  """A policy for implementing a partial whitelist for a module."""

  def __init__(self, default_stub=None,
               whitelist=None,
               overrides=None,
               deletes=None,
               constant_types=(str, int, long, BaseException),
               default_pass_through=False):
    self.default_stub = default_stub
    self.whitelist = whitelist or []
    self.overrides = overrides or {}
    self.deletes = deletes or []
    self.constant_types = constant_types
    self.default_pass_through = default_pass_through

  def apply_policy(self, module_dict):
    """Apply this policy to the provided module dict.

    In order, one of the following will apply:
    - Symbols in overrides are set to the override value.
    - Symbols in deletes are removed.
    - Whitelisted symbols and symbols with a constant type are unchanged.
    - If a default stub is set, all other symbols are replaced by it.
    - If default_pass_through is True, all other symbols are unchanged.
    - If default_pass_through is False, all other symbols are removed.

    Args:
      module_dict: The module dict to be filtered.
    """
    for symbol in module_dict.keys():
      if symbol in self.overrides:
        module_dict[symbol] = self.overrides[symbol]
      elif symbol in self.deletes:
        del module_dict[symbol]
      elif not (symbol in self.whitelist or
                isinstance(module_dict[symbol], self.constant_types) or
                (symbol.startswith('__') and symbol.endswith('__'))):
        if self.default_stub:
          module_dict[symbol] = self.default_stub
        elif not self.default_pass_through:
          del module_dict[symbol]

_MODULE_OVERRIDE_POLICIES = {
    'os': ModuleOverridePolicy(
        default_stub=stubs.os_error_not_implemented,
        whitelist=['altsep', 'curdir', 'defpath', 'devnull', 'environ', 'error',
                   'fstat', 'getcwd', 'getcwdu', 'getenv', '_get_exports_list',
                   'name', 'open', 'pardir', 'path', 'pathsep', 'sep',
                   'stat_float_times', 'stat_result', 'strerror', 'sys',
                   'walk'],
        overrides={
            'access': stubs.fake_access,
            'listdir': stubs.RestrictedPathFunction(os.listdir),
            # Alias lstat() to stat() to match the behavior in production.
            'lstat': stubs.RestrictedPathFunction(os.stat),
            'open': stubs.fake_open,
            'stat': stubs.RestrictedPathFunction(os.stat),
            'uname': stubs.fake_uname,
            'getpid': stubs.return_minus_one,
            'getppid': stubs.return_minus_one,
            'getpgrp': stubs.return_minus_one,
            'getgid': stubs.return_minus_one,
            'getegid': stubs.return_minus_one,
            'geteuid': stubs.return_minus_one,
            'getuid': stubs.return_minus_one,
            'urandom': stubs.fake_urandom,
            'system': stubs.return_minus_one,
            },
        deletes=['execv', 'execve']),
    'signal': ModuleOverridePolicy(overrides={'__doc__': None}),
    'locale': ModuleOverridePolicy(
        overrides={'setlocale': stubs.fake_set_locale},
        default_pass_through=True),
    'distutils.util': ModuleOverridePolicy(
        overrides={'get_platform': stubs.fake_get_platform},
        default_pass_through=True),
    # TODO: Stub out imp.find_module and friends.
    }


class ModuleOverrideImportHook(BaseImportHook):
  """An import hook that applies a ModuleOverridePolicy to modules."""

  def __init__(self, policies):
    super(ModuleOverrideImportHook, self).__init__()
    self.policies = policies

  def find_module(self, fullname, unused_path=None):
    return fullname in self.policies and self or None

  def load_module(self, fullname):
    if fullname in sys.modules:
      return sys.modules[fullname]
    parent_name, _, submodule_name = fullname.rpartition('.')
    if parent_name:
      parent = sys.modules[parent_name]
      path = getattr(parent, '__path__', sys.path)
    else:
      path = sys.path
      parent = None
    module = self._find_and_load_module(submodule_name, fullname, path)
    self.policies[fullname].apply_policy(module.__dict__)
    module.__loader__ = self
    sys.modules[fullname] = module
    return module


class StubModuleImportHook(BaseImportHook):
  """An import hook that replaces entire modules with stubs."""

  def find_module(self, fullname, unused_path=None):
    return self if fullname in dist27.MODULE_OVERRIDES else None

  def load_module(self, fullname):
    if fullname in sys.modules:
      return sys.modules[fullname]
    return self.import_stub_module(fullname)

  def import_stub_module(self, name):
    """Import the stub module replacement for the specified module."""
    # Do the equivalent of
    # ``from google.appengine.dist import <name>``.
    providing_dist = dist
    # When using the Py27 runtime, modules in dist27 have priority.
    # (They have already been vetted.)
    if name in dist27.__all__:
      providing_dist = dist27
    fullname = '%s.%s' % (providing_dist.__name__, name)
    __import__(fullname, {}, {})
    module = imp.new_module(fullname)
    module.__dict__.update(sys.modules[fullname].__dict__)
    module.__loader__ = self
    module.__name__ = name
    module.__package__ = None
    module.__name__ = name
    sys.modules[name] = module
    return module

_WHITE_LIST_C_MODULES = [
    'array',
    '_ast',
    'binascii',
    '_bisect',
    '_bytesio',
    'bz2',
    'cmath',
    '_codecs',
    '_codecs_cn',
    '_codecs_hk',
    '_codecs_iso2022',
    '_codecs_jp',
    '_codecs_kr',
    '_codecs_tw',
    '_collections',  # Python 2.6 compatibility
    'crypt',
    'cPickle',
    'cStringIO',
    '_csv',
    'datetime',
    '_elementtree',
    'errno',
    'exceptions',
    '_fileio',
    '_functools',
    'future_builtins',
    'gc',
    '_hashlib',
    '_heapq',
    'imp',
    '_io',
    'itertools',
    '_json',
    '_locale',
    '_lsprof',
    '__main__',
    'marshal',
    'math',
    '_md5',  # Python2.5 compatibility
    '_multibytecodec',
    'nt',  # Only indirectly through the os module.
    'operator',
    'parser',
    'posix',  # Only indirectly through the os module.
    'pyexpat',
    '_random',
    '_scproxy',  # Mac OS X compatibility
    '_sha256',  # Python2.5 compatibility
    '_sha512',  # Python2.5 compatibility
    '_sha',  # Python2.5 compatibility
    '_sre',
    'strop',
    '_struct',
    '_symtable',
    'sys',
    'thread',
    'time',
    'timing',
    'unicodedata',
    '_warnings',
    '_weakref',
    'zipimport',
    'zlib',
]


class CModuleImportHook(object):
  """An import hook implementing a C module (builtin or extensions) whitelist.

  CModuleImportHook implements the PEP 302 finder protocol where it returns
  itself as a loader for any builtin module that isn't whitelisted or part of an
  enabled third-party library. The loader implementation always raises
  ImportError.
  """

  def __init__(self, enabled_regexes):
    self._enabled_regexes = enabled_regexes

  @staticmethod
  def _module_type(fullname, path):
    _, _, submodule_name = fullname.rpartition('.')
    try:
      f, _, description = imp.find_module(submodule_name, path)
      _, _, file_type = description
    except ImportError:
      return None
    if f:
      f.close()
    return file_type

  def find_module(self, fullname, path=None):
    if (fullname in _WHITE_LIST_C_MODULES or
        any(regex.match(fullname) for regex in self._enabled_regexes)):
      return None
    if self._module_type(fullname, path) in [imp.C_EXTENSION, imp.C_BUILTIN]:
      return self
    return None

  def load_module(self, fullname):
    raise ImportError('No module named %s' % fullname)


class PathRestrictingImportHook(object):
  """An import hook that restricts imports to accessible paths.

  This import hook uses FakeFile.is_file_accessible to determine which paths are
  accessible.
  """
  _EXCLUDED_TYPES = frozenset([
      imp.C_BUILTIN,
      imp.PY_FROZEN,
      ])

  def __init__(self, enabled_regexes):
    self._enabled_regexes = enabled_regexes

  def find_module(self, fullname, path=None):
    if any(regex.match(fullname) for regex in self._enabled_regexes):
      return None
    _, _, submodule_name = fullname.rpartition('.')
    try:
      f, filename, description = imp.find_module(submodule_name, path)
    except ImportError:
      return None
    if f:
      f.close()
    _, _, file_type = description
    if (file_type in self._EXCLUDED_TYPES or
        stubs.FakeFile.is_file_accessible(filename) or
        (filename.endswith('.pyc') and
         os.path.exists(filename.replace('.pyc', '.py')))):
      return None
    return self

  def load_module(self, fullname):
    raise ImportError('No module named %s' % fullname)


class PyCryptoRandomImportHook(BaseImportHook):
  """An import hook that allows Crypto.Random.OSRNG.new() to work on posix.

  This changes PyCrypto to always use os.urandom() instead of reading from
  /dev/urandom.
  """

  def __init__(self, path):
    self._path = path

  @classmethod
  def find_module(cls, fullname, path=None):
    if fullname == 'Crypto.Random.OSRNG.posix':
      return cls(path)
    return None

  def load_module(self, fullname):
    if fullname in sys.modules:
      return sys.modules[fullname]
    __import__('Crypto.Random.OSRNG.fallback')
    module = self._find_and_load_module('posix', fullname, self._path)
    fallback = sys.modules['Crypto.Random.OSRNG.fallback']
    module.new = fallback.new
    module.__loader__ = self
    sys.modules[fullname] = module
    return module
