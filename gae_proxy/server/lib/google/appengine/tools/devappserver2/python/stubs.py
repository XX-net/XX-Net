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
"""Stub implementations of restricted functions."""



import errno
import functools
import inspect
import locale
import mimetypes
import os
import random
import re
import sys
import threading

# sysconfig is new in Python 2.7.
try:
  import sysconfig
except ImportError:
  sysconfig = None


def os_error_not_implemented(*unused_args, **unused_kwargs):
  raise OSError(errno.ENOSYS, 'Function not implemented')


def return_minus_one(*unused_args, **unused_kwargs):
  return -1


def fake_uname():
  """Fake version of os.uname."""
  return ('Linux', '', '', '', '')


def fake_urandom(n):
  """Fake version of os.urandom."""
  # On Mac OS X, os.urandom reads /dev/urandom from Python code, which is
  # disallowed by the sandbox.
  return ''.join(chr(random.randint(0, 255)) for _ in xrange(n))


def fake_access(path, mode, _os_access=os.access):
  """Fake version of os.access where only reads are supported."""
  if mode & (os.W_OK | os.X_OK):
    return False
  elif not FakeFile.is_file_accessible(path):
    return False
  return _os_access(path, mode)


def fake_open(filename, flags, mode=0777, _os_open=os.open):
  """Fake version of os.open."""
  # A copy of os.open is saved in _os_open so it can still be used after os.open
  # is replaced with this stub.
  if flags & (os.O_RDWR | os.O_CREAT | os.O_WRONLY):
    raise OSError(errno.EROFS, 'Read-only file system', filename)
  elif not FakeFile.is_file_accessible(filename):
    raise OSError(errno.ENOENT, 'No such file or directory', filename)
  return _os_open(filename, flags, mode)


def fake_set_locale(category, value=None, original_setlocale=locale.setlocale):
  """Fake version of locale.setlocale that only supports the default."""
  if value not in (None, '', 'C', 'POSIX'):
    raise locale.Error('locale emulation only supports "C" locale')
  return original_setlocale(category, 'C')


def fake_get_platform():
  """Fake distutils.util.get_platform()."""
  if sys.platform == 'darwin':
    return 'macosx-'
  else:
    return 'linux-'


class FakeFile(file):
  """File sub-class that enforces the restrictions of production."""

  ALLOWED_MODES = frozenset(['r', 'rb', 'U', 'rU'])

  # Individual files that are allowed to be accessed.
  ALLOWED_FILES = set(os.path.normcase(filename)
                      for filename in mimetypes.knownfiles
                      if os.path.isfile(filename))

  # Directories which are allowed to be accessed. All sub-directories are
  # also allowed.
  ALLOWED_DIRS = set([
      os.path.normcase(os.path.realpath(os.path.dirname(os.__file__))),
      os.path.normcase(os.path.abspath(os.path.dirname(os.__file__))),
      os.path.normcase(os.path.dirname(os.path.realpath(os.__file__))),
      os.path.normcase(os.path.dirname(os.path.abspath(os.__file__))),
  ])
  os_source_location = inspect.getsourcefile(os)
  # inspect.getsource may return None if it cannot find the os.py file.
  if os_source_location is not None:
    # Whitelist source file location to allow virtualenv to work.
    # This is necessary because the compiled bytecode may be in a different
    # location to the source code.
    ALLOWED_DIRS.update([
        os.path.normcase(os.path.realpath(os.path.dirname(os_source_location))),
        os.path.normcase(os.path.abspath(os.path.dirname(os_source_location))),
        os.path.normcase(os.path.dirname(os.path.realpath(os_source_location))),
        os.path.normcase(os.path.dirname(os.path.abspath(os_source_location))),
    ])

  # sysconfig requires access to config.h.
  if sysconfig:
    ALLOWED_DIRS.add(os.path.dirname(sysconfig.get_config_h_filename()))

  # Configuration - set_allowed_paths must be called to initialize them.
  _allowed_dirs = None  # List of accessible paths.

  # Configuration - set_skip_files must be called to initialize it.
  _skip_files = None  # Regex of skip files.
  # Configuration - set_static_files must be called to initialize it.
  _static_files = None  # Regex of static files.

  # Cache for results of is_file_accessible, {absolute filename: Boolean}
  _availability_cache = {}
  _availability_cache_lock = threading.Lock()

  @staticmethod
  def set_allowed_paths(root_path, application_paths):
    """Configures which paths are allowed to be accessed.

    Must be called at least once before any file objects are created in the
    hardened environment.

    Args:
      root_path: Absolute path to the root of the application.
      application_paths: List of additional paths that the application may
        access, this must include the App Engine runtime but not the Python
        library directories.
    """
    # Use os.path.realpath to flush out symlink-at-root issues.
    # (Deeper symlinks will not use realpath.)
    _application_paths = (set(os.path.realpath(path)
                              for path in application_paths) |
                          set(os.path.abspath(path)
                              for path in application_paths))
    FakeFile._root_path = os.path.normcase(os.path.abspath(root_path))
    _application_paths.add(FakeFile._root_path)
    FakeFile._allowed_dirs = _application_paths | FakeFile.ALLOWED_DIRS

    with FakeFile._availability_cache_lock:
      FakeFile._availability_cache = {}

  @staticmethod
  def set_skip_files(skip_files):
    """Configure the skip_files regex.

    Files that match this regex are inaccessible in the hardened environment.
    Must be called at least once before any file objects are created in the
    hardened environment.

    Args:
      skip_files: A str containing a regex to match against file paths.
    """
    FakeFile._skip_files = re.compile(skip_files)
    with FakeFile._availability_cache_lock:
      FakeFile._availability_cache = {}

  @staticmethod
  def set_static_files(static_files):
    """Configure the static_files regex.

    Files that match this regex are inaccessible in the hardened environment.
    Must be called at least once before any file objects are created in the
    hardened environment.

    Args:
      static_files: A str containing a regex to match against file paths.
    """
    FakeFile._static_files = re.compile(static_files)
    with FakeFile._availability_cache_lock:
      FakeFile._availability_cache = {}

  @staticmethod
  def is_file_accessible(filename):
    """Determines if a file is accessible.

    set_allowed_paths(), set_skip_files() and SetStaticFileConfigMatcher() must
    be called before this method or else all file accesses will raise an error.

    Args:
      filename: Path of the file to check (relative or absolute). May be a
        directory, in which case access for files inside that directory will
        be checked.

    Returns:
      True if the file is accessible, False otherwise.

    Raises:
      TypeError: filename is not a basestring.
    """
    if not isinstance(filename, basestring):
      raise TypeError()
    # Blindly follow symlinks here. DO NOT use os.path.realpath. This approach
    # enables the application developer to create symlinks in their
    # application directory to any additional libraries they want to use.
    fixed_filename = os.path.normcase(os.path.abspath(filename))

    # Some of the access checks are expensive as they look through a list of
    # regular expressions for a match.  As long as app.yaml isn't changed the
    # answer will always be the same as it's only depending on the filename and
    # the configuration, not on which files do exist or not.
    with FakeFile._availability_cache_lock:
      result = FakeFile._availability_cache.get(fixed_filename)
    if result is None:
      if (_is_path_in_directories(fixed_filename, [FakeFile._root_path]) and
          fixed_filename != FakeFile._root_path):
        relative_filename = fixed_filename[len(FakeFile._root_path):].lstrip(
            os.path.sep)
        block_access = (FakeFile._skip_files.match(relative_filename) or
                        FakeFile._static_files.match(relative_filename))
      else:
        block_access = False
      result = not block_access and (
          fixed_filename in FakeFile.ALLOWED_FILES or
          _is_path_in_directories(fixed_filename, FakeFile._allowed_dirs))
      with FakeFile._availability_cache_lock:
        FakeFile._availability_cache[fixed_filename] = result
    return result

  def __init__(self, filename, mode='r', bufsize=-1, **kwargs):
    """Initializer. See file built-in documentation."""
    if mode not in FakeFile.ALLOWED_MODES:
      raise IOError(errno.EROFS, 'Read-only file system', filename)

    if not FakeFile.is_file_accessible(filename):
      raise IOError(errno.EACCES, 'file not accessible', filename)

    super(FakeFile, self).__init__(filename, mode, bufsize, **kwargs)


class RestrictedPathFunction(object):
  """Enforces restrictions for functions with a path as their first argument."""

  def __init__(self, original_func, error_class=OSError):
    """Initializer.

    Args:
      original_func: Callable that takes as its first argument the path to a
        file or directory on disk; all subsequent arguments may be variable.
      error_class: The class of the error to raise when the file is not
        accessible.
    """
    self._original_func = original_func
    functools.update_wrapper(self, original_func)
    self._error_class = error_class

  def __call__(self, path, *args, **kwargs):
    """Enforces access permissions for the wrapped function."""
    if not FakeFile.is_file_accessible(path):
      raise self._error_class(errno.EACCES, 'path not accessible', path)

    return self._original_func(path, *args, **kwargs)


def _is_path_in_directories(filename, directories):
  """Determines if a filename is contained within one of a set of directories.

  Args:
    filename: Path of the file (relative or absolute).
    directories: Iterable collection of paths to directories which the
      given filename may be under.

  Returns:
    True if the supplied filename is in one of the given sub-directories or
    its hierarchy of children. False otherwise.
  """
  fixed_path = os.path.normcase(os.path.abspath(filename))
  for parent in directories:
    fixed_parent = os.path.normcase(os.path.abspath(parent))
    if os.path.commonprefix([fixed_path, fixed_parent]) == fixed_parent:
      return True
  return False
