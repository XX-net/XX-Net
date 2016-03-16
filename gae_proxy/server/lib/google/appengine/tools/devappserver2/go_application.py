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
"""An abstraction around the source and executable for a Go application."""



import atexit
import errno
import logging
import os
import os.path
import shutil
import subprocess
import sys
import tempfile

import google
from google.appengine.tools.devappserver2 import go_errors
from google.appengine.tools.devappserver2 import safe_subprocess


_SDKROOT = os.path.dirname(os.path.dirname(google.__file__))
GOROOT = os.path.join(_SDKROOT, 'goroot')

_GAB_PATH = os.path.join(GOROOT, 'bin', 'go-app-builder')
if sys.platform.startswith('win'):
  _GAB_PATH += '.exe'


def _rmtree(directory):
  try:
    shutil.rmtree(directory)
  except:
    pass


def _escape_tool_flags(*flags):
  """Escapes a list of flags for consumption by gab.

  This is reverse to the encoding in //apphosting/runtime/go/builder/flags.go.
  Args:
    *flags:  A list of flag arguments to be escaped.
  Returns:
    A single escaped string.
  """
  return ','.join([f.replace('\\', r'\\').replace(',', r'\,') for f in flags])


def _get_base_gab_args(application_root, nobuild_files, arch):
  """Returns the base arguments for invoking go-app-builder.

  Args:
    application_root: string path to the root dir of the application.
    nobuild_files: regexp identifying which files to not build.
    arch: The one-character architecture designator (5, 6, or 8).

  Returns:
    List of strings of arguments for invoking go-app-builder.
  """
  # Go's regexp package does not implicitly anchor to the start.
  gab_args = [
      _GAB_PATH,
      '-app_base', application_root,
      '-arch', arch,
      '-dynamic',
      '-goroot', GOROOT,
      '-nobuild_files', '^' + str(nobuild_files),
      '-unsafe',
  ]
  if 'GOPATH' in os.environ:
    gab_args.extend(['-gopath', os.environ['GOPATH']])
  return gab_args


def _run_gab(application_root, nobuild_files, arch, gab_extra_args, env):
  """Run go-app-builder.

  Args:
    application_root: string path to the root dir of the application.
    nobuild_files: regexp identifying which files to not build.
    arch: The one-character architecture designator (5, 6, or 8).
    gab_extra_args: additional arguments (i.e. other than the standard base
      arguments) for go-app-builder.
    env: A dict containing environment variables for the subprocess.

  Returns:
    A tuple of the (stdout, stderr) from the go-app-builder process.

  Raises:
    BuildError: if the go application builder fails.
  """
  gab_args = _get_base_gab_args(application_root, nobuild_files, arch)
  gab_args.extend(gab_extra_args)
  gab_process = safe_subprocess.start_process(gab_args,
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE,
                                              env=env)
  gab_stdout, gab_stderr = gab_process.communicate()
  if gab_process.returncode:
    raise go_errors.BuildError(
        '(Executed command: %s)\n%s\n%s' % (' '.join(gab_args),
                                            gab_stdout, gab_stderr))
  return gab_stdout, gab_stderr


def list_go_files(application_root, nobuild_files, skip_files):
  """Returns a list of all Go files under the application root.

  Args:
    application_root: string path to the root dir of the application.
    nobuild_files: regexp identifying which files to not build.
    skip_files: regexp identifying which files to omit from app.

  Returns:
    A list of every .go file under the application root, relative to
    that root.
  """
  go_files = []
  for root, _, file_names in os.walk(application_root):
    for file_name in file_names:
      if not file_name.endswith('.go'):
        continue
      full_path = os.path.join(root, file_name)
      rel_path = os.path.relpath(full_path, application_root)
      if skip_files.match(rel_path):
        continue
      if nobuild_files.match(rel_path):
        continue

      go_files.append(rel_path)
  return go_files


class GoApplication(object):
  """An abstraction around the source and executable for a Go application."""

  def __init__(self, module_configuration):
    """Initializer for Module.

    Args:
      module_configuration: An application_configuration.ModuleConfiguration
          instance storing the configuration data for a module.
    """
    self._module_configuration = module_configuration
    self._go_file_to_mtime = {}
    self._extras_hash = None
    self._go_executable = None
    self._work_dir = None
    self._arch = self._get_architecture()
    self._pkg_path = self._get_pkg_path()

  @property
  def go_executable(self):
    """The path to the Go executable. None if it has not been built."""
    return self._go_executable

  def _run_gab(self, gab_extra_args, env):
    return _run_gab(
        self._module_configuration.application_root,
        self._module_configuration.nobuild_files, self._arch,
        gab_extra_args, env)

  def get_environment(self):
    """Return the environment that used be used to run the Go executable."""
    environ = {'GOROOT': GOROOT,
               'PWD': self._module_configuration.application_root,
               'TZ': 'UTC',
               'RUN_WITH_DEVAPPSERVER': '1'}
    if 'SYSTEMROOT' in os.environ:
      environ['SYSTEMROOT'] = os.environ['SYSTEMROOT']
    if 'USER' in os.environ:
      environ['USER'] = os.environ['USER']
    return environ

  @staticmethod
  def _get_architecture():
    architecture_map = {
        'arm': '5',
        'amd64': '6',
        '386': '8',
    }
    for platform in os.listdir(os.path.join(GOROOT, 'pkg', 'tool')):
      # Look for 'linux_amd64', 'windows_386', etc.
      if '_' not in platform:
        continue
      architecture = platform.split('_', 1)[1]
      if architecture in architecture_map:
        return architecture_map[architecture]
    raise go_errors.BuildError(
        'No known compiler found in goroot (%s)' % GOROOT)

  @staticmethod
  def _get_pkg_path():
    for n in os.listdir(os.path.join(GOROOT, 'pkg')):
      # Look for 'linux_amd64_appengine', 'windows_386_appengine', etc.
      if n.endswith('_appengine'):
        return os.path.join(GOROOT, 'pkg', n)
    raise go_errors.BuildError('No package path found in goroot (%s)' % GOROOT)

  def _get_go_files_to_mtime(self):
    """Returns a dict mapping all Go files to their mtimes.

    Returns:
      A dict mapping the path relative to the application root of every .go
      file in the application root, or any of its subdirectories, to the file's
      modification time.
    """
    app_root = self._module_configuration.application_root
    go_file_to_mtime = {}
    for rel_path in list_go_files(
        app_root, self._module_configuration.nobuild_files,
        self._module_configuration.skip_files):
      full_path = os.path.join(app_root, rel_path)
      try:
        go_file_to_mtime[rel_path] = os.path.getmtime(full_path)
      except OSError as e:
        # Ignore deleted files.
        if e.errno != errno.ENOENT:
          raise
    return go_file_to_mtime

  def _get_extras_hash(self):
    """Returns a hash of the names and mtimes of package dependencies.

    Returns:
      Returns a string representing a hash.

    Raises:
      BuildError: if the go application builder fails.
    """
    gab_args = ['-print_extras_hash']
    gab_args.extend(self._go_file_to_mtime)
    gab_stdout, _ = self._run_gab(gab_args, env={})
    return gab_stdout

  def _build(self):
    assert self._go_file_to_mtime, 'no .go files'
    logging.debug('Building Go application')

    gab_args = [
        '-binary_name', '_go_app',
        '-extra_imports', 'appengine_internal/init',
        '-work_dir', self._work_dir,
        '-gcflags', _escape_tool_flags('-I', self._pkg_path),
        '-ldflags', _escape_tool_flags('-L', self._pkg_path),
    ]
    gab_args.extend(self._go_file_to_mtime)
    gab_stdout, gab_stderr = self._run_gab(gab_args, env={})
    logging.debug('Build succeeded:\n%s\n%s', gab_stdout, gab_stderr)
    self._go_executable = os.path.join(self._work_dir, '_go_app')

  def maybe_build(self, maybe_modified_since_last_build):
    """Builds an executable for the application if necessary.

    Args:
      maybe_modified_since_last_build: True if any files in the application root
          or the GOPATH have changed since the last call to maybe_build, False
          otherwise. This argument is used to decide whether a build is Required
          or not.

    Returns:
      True if compilation was successfully performed (will raise
        an exception if compilation was attempted but failed).
      False if compilation was not attempted.

    Raises:
      BuildError: if building the executable fails for any reason.
    """
    if not self._work_dir:
      self._work_dir = tempfile.mkdtemp('appengine-go-bin')
      atexit.register(_rmtree, self._work_dir)

    if not os.path.exists(_GAB_PATH):
      # TODO: This message should be more useful i.e. point the
      # user to an SDK that does have the right components.
      raise go_errors.BuildError(
          'Required Go components are missing from the SDK.')

    if self._go_executable and not maybe_modified_since_last_build:
      return False

    (self._go_file_to_mtime,
     old_go_file_to_mtime) = (self._get_go_files_to_mtime(),
                              self._go_file_to_mtime)

    if not self._go_file_to_mtime:
      raise go_errors.BuildError('no .go files found in %s' %
                                 self._module_configuration.application_root)

    self._extras_hash, old_extras_hash = (self._get_extras_hash(),
                                          self._extras_hash)

    if (self._go_executable and
        self._go_file_to_mtime == old_go_file_to_mtime and
        self._extras_hash == old_extras_hash):
      return False

    if self._go_file_to_mtime != old_go_file_to_mtime:
      logging.debug('Rebuilding Go application due to source modification')
    elif self._extras_hash != old_extras_hash:
      logging.debug('Rebuilding Go application due to GOPATH modification')
    else:
      logging.debug('Building Go application')
    self._build()
    return True
