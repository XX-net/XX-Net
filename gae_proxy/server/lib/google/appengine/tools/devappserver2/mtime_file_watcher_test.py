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
"""Tests for google.appengine.tools.devappserver2.mtime_file_watcher."""

import os
import os.path
import shutil
import tempfile
import time
import unittest

from google.appengine.tools.devappserver2 import mtime_file_watcher


def _sync():
  time.sleep(.1)  # just to stay over the FS timestamp resolution


class TestMtimeFileWatcher(unittest.TestCase):
  """Tests for mtime_file_watcher.MtimeFileWatcher."""

  def setUp(self):
    self._directory = tempfile.mkdtemp()  # The watched directory
    self._junk_directory = tempfile.mkdtemp()  # A scrap directory.
    self._watcher = mtime_file_watcher.MtimeFileWatcher(self._directory)

  def tearDown(self):
    self._watcher.quit()
    shutil.rmtree(self._directory)
    shutil.rmtree(self._junk_directory)

  def _create_file(self, relative_path):
    realpath = os.path.realpath(os.path.join(self._directory, relative_path))
    with open(realpath, 'w'):
      pass
    return realpath

  def _create_directory(self, relative_path):
    realpath = os.path.realpath(os.path.join(self._directory, relative_path))
    os.mkdir(realpath)
    return realpath

  def test_file_created(self):
    self._watcher.start()
    self._watcher._startup_thread.join()
    path = self._create_file('test')
    self.assertEqual(self._watcher.changes(), {path})

  def test_file_modified(self):
    path = self._create_file('test')
    _sync()
    self._watcher.start()
    self._watcher._startup_thread.join()
    with open(path, 'w') as f:
      f.write('testing')
    self.assertEqual(self._watcher.changes(), {path})

  def test_file_read(self):
    path = self._create_file('test')
    with open(path, 'w') as f:
      f.write('testing')
    self._watcher.start()
    self._watcher._startup_thread.join()
    with open(path, 'r') as f:
      f.read()
    # Reads should not trigger updates.
    self.assertEqual(self._watcher.changes(), set())

  def test_file_deleted(self):
    path = self._create_file('test')
    self._watcher.start()
    self._watcher._startup_thread.join()
    os.remove(path)
    self.assertEqual(self._watcher.changes(), {path})

  def test_file_renamed(self):
    source = self._create_file('test')
    target = os.path.join(os.path.dirname(source), 'test2')
    self._watcher.start()
    self._watcher._startup_thread.join()
    os.rename(source, target)
    self.assertEqual(self._watcher.changes(), {source, target})

  def test_create_directory(self):
    self._watcher.start()
    self._watcher._startup_thread.join()
    path = self._create_directory('test')
    self.assertEqual(self._watcher.changes(), {path})

  def test_file_created_in_directory(self):
    dir_path = self._create_directory('test')
    _sync()
    self._watcher.start()
    self._watcher._startup_thread.join()
    path = self._create_file('test/file')
    # Note : creating an entry in an inode changes its timestamp so the is
    # normal
    self.assertEqual(self._watcher.changes(), {dir_path, path})

  def test_move_directory(self):
    source = self._create_directory('test')
    target = os.path.join(os.path.dirname(source), 'test2')
    self._watcher.start()
    self._watcher._startup_thread.join()
    os.rename(source, target)
    self.assertEqual(self._watcher.changes(), {source, target})

  def test_move_directory_out_of_watched(self):
    source = self._create_directory('test')
    target = os.path.join(self._junk_directory, 'test')
    self._watcher.start()
    self._watcher._startup_thread.join()
    os.rename(source, target)
    self.assertEqual(self._watcher.changes(), {source})
    with open(os.path.join(target, 'file'), 'w'):
      pass
    # Changes to files in subdirectories that have been moved should be ignored.
    self.assertEqual(self._watcher.changes(), set())

  def test_move_directory_into_watched(self):
    source = os.path.join(self._junk_directory, 'source')
    target = os.path.join(self._directory, 'target')
    os.mkdir(source)
    _sync()
    self._watcher.start()
    self._watcher._startup_thread.join()
    os.rename(source, target)
    self.assertEqual(self._watcher.changes(), {target})
    file_path = os.path.join(target, 'file')
    with open(file_path, 'w+'):
      pass
    # file has been created so target changed
    self.assertEqual(self._watcher.changes(), {target, file_path})

  def test_directory_deleted(self):
    path = self._create_directory('test')
    _sync()
    self._watcher.start()
    self._watcher._startup_thread.join()
    os.rmdir(path)
    self.assertEqual(self._watcher.changes(), {path})

  @unittest.skipUnless(hasattr(os, 'symlink'), 'requires os.symlink')
  def test_symlink(self):
    sym_target = os.path.join(self._directory, 'test')
    os.mkdir(os.path.join(self._junk_directory, 'subdir'))
    # the translated path in the target dir
    sym_subdir_path = os.path.join(sym_target, 'subdir')
    _sync()
    self._watcher.start()
    self._watcher._startup_thread.join()

    # Check that an added symlinked directory is reported.
    os.symlink(self._junk_directory, sym_target)
    self.assertEqual(
        self._watcher.changes(),
        {sym_target, os.path.join(sym_target, 'subdir')})

    # Check that a file added to the symlinked directory is reported.
    with open(os.path.join(self._junk_directory, 'file1'), 'w'):
      pass
    sym_file_path = os.path.join(sym_target, 'file1')
    # file1 has been created so sym_target changed
    self.assertEqual(
        self._watcher.changes(), {sym_target, sym_file_path})

    # Check that a removed symlinked directory is reported.
    os.remove(sym_target)
    self.assertEqual(
        self._watcher.changes(), {sym_target, sym_file_path, sym_subdir_path})

    # Check that a file added to the removed symlinked directory is *not*
    # reported.
    with open(os.path.join(self._junk_directory, 'subdir', 'file2'), 'w'):
      pass
    self.assertEqual(self._watcher.changes(), set())

  def test_too_many_files(self):
    self._watcher.start()
    self._watcher._startup_thread.join()
    for i in range(10001):
      self._create_file('file%d' % i)
    self.assertEqual(len(self._watcher.changes()), 10000)

  @unittest.skipUnless(hasattr(os, 'symlink'), 'requires os.symlink')
  def test_symlink_loop(self):
    self._watcher.start()
    self._watcher._startup_thread.join()

    for i in range(1000):
      self._create_file('file%d' % i)

    for i in range(11):
      os.symlink(self._directory, os.path.join(self._directory, 'test%d' % i))
    # basically the set is completely crazy
    self.assertEqual(len(self._watcher.changes()), 10000)


if __name__ == '__main__':
  unittest.main()
