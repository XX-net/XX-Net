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
"""Monitors a directory tree for changes using win32 APIs."""

import ctypes
import logging
import os
import threading

# FindNextChangeNotification constants (defined in FileAPI.h):
_FILE_NOTIFY_CHANGE_FILE_NAME = 0x00000001
_FILE_NOTIFY_CHANGE_DIR_NAME = 0x00000002
_FILE_NOTIFY_CHANGE_ATTRIBUTES = 0x00000004
_FILE_NOTIFY_CHANGE_SIZE = 0x00000008
_FILE_NOTIFY_CHANGE_LAST_WRITE = 0x00000010
_FILE_NOTIFY_CHANGE_CREATION = 0x00000040
_FILE_NOTIFY_CHANGE_SECURITY = 0x00000100

_FILE_NOTIFY_CHANGE_ANY = (_FILE_NOTIFY_CHANGE_FILE_NAME |
                           _FILE_NOTIFY_CHANGE_DIR_NAME |
                           _FILE_NOTIFY_CHANGE_ATTRIBUTES |
                           _FILE_NOTIFY_CHANGE_SIZE |
                           _FILE_NOTIFY_CHANGE_LAST_WRITE |
                           _FILE_NOTIFY_CHANGE_CREATION |
                           _FILE_NOTIFY_CHANGE_SECURITY)

# pylint: disable=invalid-name
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
_FILE_LIST_DIRECTORY = 1
_FILE_SHARE_READ = 0x1
_FILE_SHARE_WRITE = 0x2
_FILE_SHARE_DELETE = 0x4
_OPEN_EXISTING = 0x3
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000

_ERROR_NOTIFY_ENUM_DIR = 1022

_COMMON_FILE_NOTIFY_FIELDS = [
    ('NextEntryOffset', ctypes.c_ulong),
    ('Action', ctypes.c_ulong),
    ('FileNameLength', ctypes.c_ulong)
]


class FileNotifyInformationShort(ctypes.Structure):
  """This is the partial translation of the FILE_NOTIFY_INFORMATION struct.

   typedef struct _FILE_NOTIFY_INFORMATION {
     DWORD NextEntryOffset;
     DWORD Action;
     DWORD FileNameLength;
     WCHAR FileName[1];
   } FILE_NOTIFY_INFORMATION

  It is partial because it doesn't include the variable-length FileName field.
  Another ctypes.Structure subclass is needed once we know the FileNameLength.
  """
  _fields_ = _COMMON_FILE_NOTIFY_FIELDS


_WCHAR_BYTESIZE = ctypes.sizeof(ctypes.c_wchar)


def _parse_file_notification_information(buff, offset):
  """Parse FileNotificationInformation from a c_char buffer.

  Args:
    buff: a ctypes string buffer that contains
         a FileNotificationInformation structure.
    offset: the offset you want to parse the struct from.

  Returns:
    a class matching the structure.
  """
  notify_information_short = ctypes.cast(
      ctypes.addressof(buff) + offset,
      ctypes.POINTER(FileNotifyInformationShort)).contents
  # This is a variable length structure so we need to do a 2 steps parse to
  # create a perfectly matching result.
  chr_len = notify_information_short.FileNameLength / _WCHAR_BYTESIZE

  class FileNotifyInformation(ctypes.Structure):
    _fields_ = (
        _COMMON_FILE_NOTIFY_FIELDS +
        [('FileName', ctypes.c_wchar * chr_len)])
  return ctypes.cast(ctypes.addressof(buff) + offset,
                     ctypes.POINTER(FileNotifyInformation)).contents


# we want to be sure that at least one notification fits even if it is a big
# one.
_BUFF_SIZE = 64 * 1024


def _parse_buffer(buff):
  """Parses a FileNotifyInformation out of a ctypes array of c_char."""
  response = set()
  offset = 0
  while True:
    notify_information = _parse_file_notification_information(buff, offset)
    response.add(notify_information.FileName)
    if notify_information.NextEntryOffset == 0:
      return response
    offset += notify_information.NextEntryOffset


class Win32FileWatcher(object):
  """Monitors a directory tree for changes using win32 API."""
  SUPPORTS_MULTIPLE_DIRECTORIES = False

  def __init__(self, directory):
    """Initializer for Win32FileWatcher.

    Args:
      directory: A string representing the path to a directory that should
          be monitored for changes i.e. files and directories added, renamed,
          deleted or changed.
    """
    self._directory = os.path.abspath(directory)
    self._directory_handle = None
    self._change_set = set()
    self._lock = threading.Lock()  # protects self._change_set
    self._stop = threading.Event()
    self._change_event = threading.Event()
    self._thread = None

  def start(self):
    """Start watching the directory for changes."""
    self._directory_handle = ctypes.windll.kernel32.CreateFileW(
        ctypes.c_wchar_p(self._directory),
        ctypes.c_ulong(_FILE_LIST_DIRECTORY),
        ctypes.c_ulong(_FILE_SHARE_READ |
                       _FILE_SHARE_WRITE),
        None,
        ctypes.c_ulong(_OPEN_EXISTING),
        # required to monitor changes.
        ctypes.c_ulong(_FILE_FLAG_BACKUP_SEMANTICS),
        None)
    if self._directory_handle == _INVALID_HANDLE_VALUE:
      raise ctypes.WinError()
    self._thread = threading.Thread(
        target=self._monitor, name='Win32 File Watcher')
    self._thread.start()

  def quit(self):
    """Stop watching the directory for changes."""
    self._stop.set()
    # Note: this will unlock the blocking ReadDirectoryChangesW call.
    ctypes.windll.kernel32.CancelIoEx(self._directory_handle, None)
    self._thread.join()
    ctypes.windll.kernel32.CloseHandle(self._directory_handle)

  def changes(self, timeout_ms=0):
    """Returns the paths changed in the watched directory since the last call.

    start() must be called before this method.

    Args:
      timeout_ms: the maximum number of milliseconds you allow this function to
                  wait for a filesystem change.

    Returns:
      Returns an iterable of changed directories/files.
    """
    if timeout_ms != 0:
      self._change_event.wait(timeout_ms / 1000.0)

    with self._lock:
      result = self._change_set
      self._change_set = set()
      self._change_event.clear()

    return result

  def _monitor(self):
    buff = ctypes.create_string_buffer(_BUFF_SIZE)
    while not self._stop.isSet():
      size_returned = ctypes.c_ulong(0)
      result = ctypes.windll.kernel32.ReadDirectoryChangesW(
          self._directory_handle,
          buff,
          ctypes.c_ulong(_BUFF_SIZE),
          True,  # recursive.
          ctypes.c_ulong(_FILE_NOTIFY_CHANGE_ANY),
          ctypes.byref(size_returned),
          None,
          None)  # this is a blocking call.
      if result == 0 and ctypes.GetLastError() == _ERROR_NOTIFY_ENUM_DIR:
        logging.warning('Buffer overflow while monitoring for file changes.')
        # we need to notify that something changed anyway
        with self._lock:
          self._change_set |= {'Unknown file'}
      if result != 0 and size_returned.value != 0:
        additional_changes = _parse_buffer(buff)
        with self._lock:
          self._change_set |= additional_changes
          self._change_event.set()
