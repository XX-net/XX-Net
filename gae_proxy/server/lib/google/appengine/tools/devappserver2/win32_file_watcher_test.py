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
# -*- coding: utf-8 -*-

"""Tests for google.apphosting.tools.devappserver2.win32_file_watcher."""



import ctypes
import unittest

import google

import mox

from google.appengine.tools.devappserver2 import win32_file_watcher


def mox_c(value):
  # bridge to correctly match a ctypes objects in mox signature.
  # This is necessary because :
  # >>> ctypes.c_ulong(2) == ctypes.c_ulong(2)
  # False
  return mox.Func(lambda c_value: c_value.value == value)


class WinError(Exception):
  pass


class Win32FileWatcherTest(unittest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()
    ctypes.windll = self.mox.CreateMockAnything()
    ctypes.windll.kernel32 = self.mox.CreateMockAnything()
    ctypes.windll.kernel32.CreateFileW = self.mox.CreateMockAnything()
    ctypes.windll.kernel32.ReadDirectoryChangesW = self.mox.CreateMockAnything()
    ctypes.windll.kernel32.CancelIoEx = self.mox.CreateMockAnything()
    ctypes.windll.kernel32.CloseHandle = self.mox.CreateMockAnything()
    ctypes.WinError = WinError

  def tearDown(self):
    self.mox.UnsetStubs()
    del ctypes.windll

  def test_with_change(self):
    watcher = win32_file_watcher.Win32FileWatcher('/tmp')

    ctypes.windll.kernel32.CreateFileW(
        mox_c('/tmp'),
        mox_c(1L),
        mox_c(3L),
        None,
        mox_c(3L),
        mox_c(win32_file_watcher._FILE_FLAG_BACKUP_SEMANTICS),
        None).AndReturn(31415)
    # pylint: disable=unused-argument

    def found_something(
        handle, buff, size, recursive, change_type, size_returned_by_ref,
        unused1, unused2):

      parray = [
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # next offset = 0
          0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Action
          0x28, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # 4 * 10 chrs
          0x74, 0x00, 0x00, 0x00,  # 't'
          0x65, 0x00, 0x00, 0x00,  # 'e'
          0x73, 0x00, 0x00, 0x00,  # 's'
          0x74, 0x00, 0x00, 0x00,  # 't'
          0x20, 0x00, 0x00, 0x00,  # ' '
          0x73, 0x00, 0x00, 0x00,  # 's'
          0x74, 0x00, 0x00, 0x00,  # 't'
          0x75, 0x00, 0x00, 0x00,  # 'u'
          0x66, 0x00, 0x00, 0x00,  # 'f'
          0x66, 0x00, 0x00, 0x00]  # 'f'
      nbuff = (ctypes.c_ubyte * len(parray))(*parray)
      ctypes.memmove(
          buff,
          ctypes.addressof(nbuff),
          ctypes.sizeof(nbuff))

      psize = ctypes.cast(size_returned_by_ref, ctypes.POINTER(ctypes.c_ulong))
      psize[0] = ctypes.sizeof(nbuff)

    ctypes.windll.kernel32.ReadDirectoryChangesW(
        31415,
        mox.IgnoreArg(),
        mox_c(win32_file_watcher._BUFF_SIZE),
        True,
        mox_c(351),
        mox.IgnoreArg(),
        None,
        None).WithSideEffects(found_something).AndReturn(1)

    ctypes.windll.kernel32.CancelIoEx(31415, None)
    ctypes.windll.kernel32.CloseHandle(31415)

    self.mox.ReplayAll()
    watcher.start()
    watcher.quit()
    self.assertEqual(watcher.changes(), {'test stuff'})
    self.mox.VerifyAll()

  def test_with_no_change(self):
    watcher = win32_file_watcher.Win32FileWatcher('/tmp')

    ctypes.windll.kernel32.CreateFileW(
        mox_c('/tmp'),
        mox_c(1L),
        mox_c(3L),
        None,
        mox_c(3L),
        mox_c(win32_file_watcher._FILE_FLAG_BACKUP_SEMANTICS),
        None).AndReturn(31415)
    # pylint: disable=unused-argument

    def found_nothing(
        handle, buff, size, recursive, change_type, size_returned_by_ref,
        unused1, unused2):
      ctypes.cast(size_returned_by_ref, ctypes.POINTER(ctypes.c_ulong))[0] = 0L

    ctypes.windll.kernel32.ReadDirectoryChangesW(
        31415,
        mox.IgnoreArg(),
        mox_c(4096),
        True,
        mox_c(351),
        mox.IgnoreArg(),
        None,
        None).WithSideEffects(found_nothing).AndReturn(-1)

    ctypes.windll.kernel32.CancelIoEx(31415, None)
    ctypes.windll.kernel32.CloseHandle(31415)

    self.mox.ReplayAll()
    watcher.start()
    watcher.quit()
    self.assertEqual(watcher.changes(), set())
    self.mox.VerifyAll()

  def test_with_error(self):
    watcher = win32_file_watcher.Win32FileWatcher('/tmp')

    ctypes.windll.kernel32.CreateFileW(
        mox_c('/tmp'),
        mox_c(1L),
        mox_c(3L),
        None,
        mox_c(3L),
        mox_c(win32_file_watcher._FILE_FLAG_BACKUP_SEMANTICS),
        None).AndReturn(win32_file_watcher._INVALID_HANDLE_VALUE)

    self.mox.ReplayAll()
    self.assertRaises(WinError, watcher.start)
    self.mox.VerifyAll()

if __name__ == '__main__':
  unittest.main()
