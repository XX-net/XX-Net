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
"""Monitors a directory tree for changes using the inotify API.

See http://linux.die.net/man/7/inotify.
"""



import ctypes
import ctypes.util
import errno
import itertools
import logging
import os
import select
import struct
import sys
import threading

from google.appengine.tools.devappserver2 import watcher_common

IN_MODIFY = 0x00000002
IN_ATTRIB = 0x00000004
IN_MOVED_FROM = 0x00000040
IN_MOVED_TO = 0x00000080
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200

IN_IGNORED = 0x00008000
IN_ISDIR = 0x40000000

_INOTIFY_EVENT = struct.Struct('iIII')
_INOTIFY_EVENT_SIZE = _INOTIFY_EVENT.size
_INTERESTING_INOTIFY_EVENTS = (
    IN_ATTRIB | IN_MODIFY | IN_MOVED_FROM | IN_MOVED_TO | IN_CREATE | IN_DELETE)

# inotify only available on Linux and a ctypes.CDLL will raise if code tries to
# specify the arg types or return type for a non-existent function.
if sys.platform.startswith('linux'):
  _libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
  _libc.inotify_init.argtypes = []
  _libc.inotify_init.restype = ctypes.c_int
  _libc.inotify_add_watch.argtypes = [ctypes.c_int,
                                      ctypes.c_char_p,
                                      ctypes.c_uint32]
  _libc.inotify_add_watch.restype = ctypes.c_int
  _libc.inotify_rm_watch.argtypes = [ctypes.c_int,
                                     ctypes.c_int]
  _libc.inotify_rm_watch.restype = ctypes.c_int
else:
  _libc = None


# All the possible attributes.
_ATTRIBUTE_NAMES = [
    'IN_MODIFY',
    'IN_ATTRIB',
    'IN_MOVED_FROM',
    'IN_MOVED_TO',
    'IN_CREATE',
    'IN_DELETE',
    'IN_IGNORED',
    'IN_ISDIR',
]

# A mapping from the attribute mask/bit value to the name.
_ATTRIBUTE_MASK_NAMES = {globals()[name]: name for name in _ATTRIBUTE_NAMES}

# If 2 file changes are less than 100 ms apart,
# aggregate them within one changes call.
_AGGREGATE_CHANGES_MS_APART = 100


def _bit_str(bits, mask_names):
  """Convert a bit field to list of names.

  Args:
    bits: an int that holds a combined bit field.
    mask_names: a mapping from individual bit masks to names.

  Returns:
    A human readable presentation of the combined bit field.
  """
  hex_str = hex(bits)
  names = []
  mask = 0x1
  while bits:
    if bits & mask:
      bits &= ~mask
      names.append(mask_names.get(mask, '(0x%x)' % mask))
    mask <<= 1
  return '%s (%s)' % ('|'.join(names), hex_str)


class InotifyFileWatcher(object):
  """Monitors a directory tree for changes using inotify."""

  SUPPORTS_MULTIPLE_DIRECTORIES = True

  def __init__(self, directories):
    """Initializer for InotifyFileWatcher.

    Args:
      directories: An iterable of strings representing the path to a directory
          that should be monitored for changes i.e. files and directories added,
          renamed, deleted or changed.

    Raises:
      OSError: if there are no inotify instances available.
    """
    assert _libc is not None, 'InotifyFileWatcher only available on Linux.'
    self._directories = [os.path.abspath(d) for d in directories]
    self._real_directories = [os.path.realpath(d) for d in self._directories]
    self._watch_to_directory = {}
    self._directory_to_watch_descriptor = {}
    self._directory_to_subdirs = {}
    self._inotify_events = ''
    self._inotify_fd = _libc.inotify_init()
    if self._inotify_fd < 0:
      error = OSError('failed call to inotify_init')
      error.errno = ctypes.get_errno()
      error.strerror = errno.errorcode[ctypes.get_errno()]
      raise error
    self._inotify_poll = select.poll()
    # Protects operations that cannot be done while the watcher is quitting.
    self._inotify_fd_lock = threading.Lock()

  def _remove_watch_for_path(self, path):
    # Must be called with _inotify_fd_lock held.
    logging.debug('_remove_watch_for_path(%r)', path)
    wd = self._directory_to_watch_descriptor[path]

    if _libc.inotify_rm_watch(self._inotify_fd, wd) < 0:
      # If the directory is deleted then the watch will removed automatically
      # and inotify_rm_watch will fail. Just log the error.
      logging.debug('inotify_rm_watch failed for %r: %d [%r]',
                    path,
                    ctypes.get_errno(),
                    errno.errorcode[ctypes.get_errno()])

    parent_path = os.path.dirname(path)
    if parent_path in self._directory_to_subdirs:
      self._directory_to_subdirs[parent_path].remove(path)

    # _directory_to_subdirs must be copied because it is mutated in the
    # recursive call.
    for subdir in frozenset(self._directory_to_subdirs[path]):
      self._remove_watch_for_path(subdir)

    del self._watch_to_directory[wd]
    del self._directory_to_watch_descriptor[path]
    del self._directory_to_subdirs[path]

  def _add_watch_for_path(self, path):
    # Must be called with _inotify_fd_lock held.
    logging.debug('_add_watch_for_path(%r)', path)

    for dirpath, directories, _ in itertools.chain(
        [(os.path.dirname(path), [os.path.basename(path)], None)],
        os.walk(path, topdown=True, followlinks=True)):
      watcher_common.skip_ignored_dirs(directories)
      # TODO: this is not an ideal solution as there are other ways for
      # symlinks to confuse our algorithm but a general solution is going to
      # be very complex and this is good enough to solve the immediate problem
      # with Dart's directory structure.
      watcher_common.skip_local_symlinks(
          self._real_directories, dirpath, directories)
      for directory in directories:
        directory_path = os.path.join(dirpath, directory)
        # dirpath cannot be used as the parent directory path because it is the
        # empty string for symlinks :-(
        parent_path = os.path.dirname(directory_path)

        watch_descriptor = _libc.inotify_add_watch(
            self._inotify_fd,
            ctypes.create_string_buffer(directory_path),
            _INTERESTING_INOTIFY_EVENTS)
        if watch_descriptor < 0:
          if ctypes.get_errno() == errno.ENOSPC:
            logging.warning(
                'There are too many directories in your application for '
                'changes in all of them to be monitored. You may have to '
                'restart the development server to see some changes to your '
                'files.')
            return
          error = OSError('could not add watch for %r' % directory_path)
          error.errno = ctypes.get_errno()
          error.strerror = errno.errorcode[ctypes.get_errno()]
          error.filename = directory_path
          raise error

        if parent_path in self._directory_to_subdirs:
          self._directory_to_subdirs[parent_path].add(directory_path)
        self._watch_to_directory[watch_descriptor] = directory_path
        self._directory_to_watch_descriptor[directory_path] = watch_descriptor
        self._directory_to_subdirs[directory_path] = set()

  def start(self):
    """Start watching the directory for changes."""
    with self._inotify_fd_lock:
      if self._inotify_fd < 0:
        return
      self._inotify_poll.register(self._inotify_fd, select.POLLIN)
      for directory in self._directories:
        self._add_watch_for_path(directory)

  def quit(self):
    """Stop watching the directory for changes."""
    with self._inotify_fd_lock:
      os.close(self._inotify_fd)
      self._inotify_fd = -1

  def changes(self, timeout_ms=0):
    """Return paths for changed files and directories.

    start() must be called before this method.

    Args:
      timeout_ms: a timeout in milliseconds on which this watcher will block
                  waiting for a change. It allows for external polling threads
                  to react immediately on a change instead of waiting for
                  a random polling delay.

    Returns:
      A set of strings representing file and directory paths that have changed
      since the last call to get_changed_paths.
    """
    paths = set()
    while True:
      with self._inotify_fd_lock:
        if self._inotify_fd < 0:
          return set()
        # Don't wait to detect subsequent changes after the initial one.
        if not self._inotify_poll.poll(
            _AGGREGATE_CHANGES_MS_APART if paths else timeout_ms):
          break

        self._inotify_events += os.read(self._inotify_fd, 1024)
        while len(self._inotify_events) > _INOTIFY_EVENT_SIZE:
          wd, mask, cookie, length = _INOTIFY_EVENT.unpack(
              self._inotify_events[:_INOTIFY_EVENT_SIZE])
          if len(self._inotify_events) < _INOTIFY_EVENT_SIZE + length:
            break

          name = self._inotify_events[
              _INOTIFY_EVENT_SIZE:_INOTIFY_EVENT_SIZE + length]
          name = name.rstrip('\0')

          logging.debug(
              'wd=%s, mask=%s, cookie=%s, length=%s, name=%r', wd,
              _bit_str(mask, _ATTRIBUTE_MASK_NAMES), cookie, length, name)

          self._inotify_events = self._inotify_events[
              _INOTIFY_EVENT_SIZE + length:]

          if mask & IN_IGNORED:
            continue
          try:
            directory = self._watch_to_directory[wd]
          except KeyError:
            logging.debug('Watch deleted for watch descriptor=%d', wd)
            continue

          path = os.path.join(directory, name)
          if os.path.isdir(path) or path in self._directory_to_watch_descriptor:
            if mask & IN_DELETE:
              self._remove_watch_for_path(path)
            elif mask & IN_MOVED_FROM:
              self._remove_watch_for_path(path)
            elif mask & IN_CREATE:
              self._add_watch_for_path(path)
            elif mask & IN_MOVED_TO:
              self._add_watch_for_path(path)
          if path not in paths and not watcher_common.ignore_file(path):
            paths.add(path)
    return paths
