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
"""Common functionality for file watchers."""



import os

# A prefix for files and directories that we should not watch at all.
_IGNORED_PREFIX = '.'
# File suffixes that should be ignored.
_IGNORED_FILE_SUFFIXES = (
    # Python temporaries
    '.pyc',
    '.pyo',
    # Backups
    '~',
    # Emacs
    '#',
    # Vim
    '.swp',
    '.swo',
)


def ignore_file(filename):
  """Report whether a file should not be watched."""
  filename = os.path.basename(filename)
  return (
      filename.startswith(_IGNORED_PREFIX) or
      any(filename.endswith(suffix) for suffix in _IGNORED_FILE_SUFFIXES))


def _remove_pred(lst, pred):
  """Remove items from a list that match a predicate."""

  # Walk the list in reverse because once an item is deleted,
  # the indexes of any subsequent items change.
  for idx in reversed(xrange(len(lst))):
    if pred(lst[idx]):
      del lst[idx]


def skip_ignored_dirs(dirs):
  """Skip directories that should not be watched."""

  _remove_pred(dirs, lambda d: d.startswith(_IGNORED_PREFIX))


def skip_local_symlinks(roots, dirpath, directories):
  """Skip symlinks that link to another watched directory.

  Our algorithm gets confused when the same directory is watched multiple times
  due to symlinks.

  Args:
    roots: The realpath of the root of all directory trees being watched.
    dirpath: The base directory that each of the directories are in (i.e.
      the first element of a triplet obtained from os.walkpath).
    directories: A list of directories in dirpath. This list is modified so
      that any element which is a symlink to another directory is removed.
  """

  def is_local_symlink(d):
    d = os.path.join(dirpath, d)
    if not os.path.islink(d):
      return False
    d = os.path.realpath(d)
    return any(d.startswith(root) for root in roots)

  _remove_pred(directories, is_local_symlink)
