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
"""Tests for google.apphosting.tools.devappserver2.inotify_file_watcher."""



import logging
import os
import os.path
import shutil
import sys
import tempfile
import unittest

from google.appengine.tools.devappserver2 import inotify_file_watcher


@unittest.skipUnless(sys.platform.startswith('linux'), 'requires linux')
class TestInotifyFileWatcher(unittest.TestCase):
  """Tests for inotify_file_watcher.InotifyFileWatcher."""

  def setUp(self):
    self._directory = tempfile.mkdtemp()  # The watched directory
    self._junk_directory = tempfile.mkdtemp()  # A scrap directory.
    self._watcher = inotify_file_watcher.InotifyFileWatcher([self._directory])
    logging.debug('watched directory=%r, junk directory=%r',
                  self._directory, self._junk_directory)

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
    os.makedirs(realpath)
    return realpath

  def _create_directory_tree(self, path, num_directories):
    """Create exactly num_directories subdirectories in path."""
    assert num_directories >= 0
    if not num_directories:
      return

    self._create_directory(path)
    num_directories -= 1
    # Divide the remaining number of directories to create among 4
    # subdirectories in an approximate even fashion.
    for i in range(4, 0, -1):
      sub_dir_size = num_directories / i
      self._create_directory_tree(os.path.join(path, 'dir%d' % i), sub_dir_size)
      num_directories -= sub_dir_size

  def test_file_created(self):
    self._watcher.start()
    path = self._create_file('test')
    self.assertEqual(
        set([path]),
        self._watcher.changes())

  def test_file_modified(self):
    path = self._create_file('test')
    self._watcher.start()
    with open(path, 'w') as f:
      f.write('testing')
    self.assertEqual(
        set([path]),
        self._watcher.changes())

  def test_file_read(self):
    path = self._create_file('test')
    with open(path, 'w') as f:
      f.write('testing')
    self._watcher.start()
    with open(path, 'r') as f:
      f.read()
    # Reads should not trigger updates.
    self.assertEqual(
        set(),
        self._watcher.changes())

  def test_file_deleted(self):
    path = self._create_file('test')
    self._watcher.start()
    os.remove(path)
    self.assertEqual(
        set([path]),
        self._watcher.changes())

  def test_file_renamed(self):
    source = self._create_file('test')
    target = os.path.join(os.path.dirname(source), 'test2')
    self._watcher.start()
    os.rename(source, target)
    self.assertEqual(
        set([source, target]),
        self._watcher.changes())

  def test_create_directory(self):
    self._watcher.start()
    directory = self._create_directory('test')
    self.assertEqual(
        set([directory]),
        self._watcher.changes())

  def test_file_created_in_directory(self):
    directory = self._create_directory('test')
    self._watcher.start()
    path = self._create_file('test/file')
    self.assertEqual(
        set([path]),
        self._watcher.changes())

  def test_move_directory(self):
    source = self._create_directory('test')
    target = os.path.join(os.path.dirname(source), 'test2')
    self._watcher.start()
    os.rename(source, target)
    self.assertEqual(
        set([source, target]),
        self._watcher.changes())

  def test_move_directory_out_of_watched(self):
    source = self._create_directory('test')
    target = os.path.join(self._junk_directory, 'test')
    self._watcher.start()
    os.rename(source, target)
    self.assertEqual(
        set([source]),
        self._watcher.changes())
    with open(os.path.join(target, 'file'), 'w'):
      pass
    # Changes to files in subdirectories that have been moved should be ignored.
    self.assertEqual(
        set([]),
        self._watcher.changes())

  def test_move_directory_into_watched(self):
    source = os.path.join(self._junk_directory, 'source')
    target = os.path.join(self._directory, 'target')
    os.mkdir(source)
    self._watcher.start()
    os.rename(source, target)
    self.assertEqual(
        set([target]),
        self._watcher.changes())
    file_path = os.path.join(target, 'file')
    with open(file_path, 'w+'):
      pass
    self.assertEqual(
        set([file_path]),
        self._watcher.changes())

  def test_directory_deleted(self):
    path = self._create_directory('test')
    self._watcher.start()
    os.rmdir(path)
    self.assertEqual(
        set([path]),
        self._watcher.changes())

  def test_subdirectory_deleted(self):
    """Tests that internal _directory_to_subdirs is updated on delete."""
    path = self._create_directory('test')
    sub_path = self._create_directory('test/test2')
    self._watcher.start()

    self.assertEqual(
        set([sub_path]),
        self._watcher._directory_to_subdirs[path])
    os.rmdir(sub_path)
    self.assertEqual(
        set([sub_path]),
        self._watcher.changes())
    self.assertEqual(
        set(),
        self._watcher._directory_to_subdirs[path])

    os.rmdir(path)
    self.assertEqual(
        set([path]),
        self._watcher.changes())

  def test_symlink_directory(self):
    sym_target = os.path.join(self._directory, 'test')
    os.mkdir(os.path.join(self._junk_directory, 'subdir'))
    self._watcher.start()

    # Check that an added symlinked directory is reported.
    os.symlink(self._junk_directory, sym_target)
    self.assertEqual(
        set([sym_target]),
        self._watcher.changes())

    # Check that a file added to the symlinked directory is reported.
    with open(os.path.join(self._junk_directory, 'file1'), 'w'):
      pass
    self.assertEqual(
        set([os.path.join(self._directory, 'test', 'file1')]),
        self._watcher.changes())

    # Check that modifying the file in the symlinked directory is reported.
    with open(os.path.join(self._junk_directory, 'file1'), 'w') as fp:
      fp.write('some data')
    self.assertEqual(
        set([os.path.join(self._directory, 'test', 'file1')]),
        self._watcher.changes())

    # Check that a removed symlinked directory is reported.
    os.remove(sym_target)
    self.assertEqual(
        set([sym_target]),
        self._watcher.changes())

    # Check that a file added to the removed symlinked directory is *not*
    # reported.
    with open(os.path.join(self._junk_directory, 'subdir', 'file2'), 'w'):
      pass
    self.assertEqual(
        set(),
        self._watcher.changes())

  @unittest.skip('b/11896748')
  def test_symlink_file(self):
    actual_file = os.path.join(self._junk_directory, 'moo')
    with open(actual_file, 'w'):
      pass
    symbolic_link = os.path.join(self._directory, 'moo')
    self._watcher.start()

    # Check that symlinking a file into watched directory is reported.
    os.symlink(actual_file, symbolic_link)
    self.assertEqual(
        set([symbolic_link]),
        self._watcher.changes())

    # Check that modifying the source file is reported.
    with open(actual_file, 'w') as fp:
      fp.write('some data')
    self.assertEqual(
        set([symbolic_link]),
        self._watcher.changes())

    # Check that deleting the source file is reported.
    os.unlink(actual_file)
    self.assertEqual(
        set([symbolic_link]),
        self._watcher.changes())

  def test_many_directories(self):
    # Linux supports a limited number of watches per file descriptor. The
    # default is 8192 (i.e. 2^13).
    self._create_directory_tree('bigdir', num_directories=10000)
    self._watcher.start()
    path = self._create_file('bigdir/dir4/dir4/file')
    self.assertEqual(
        set([path]),
        self._watcher.changes())

  def test_internal_symlinks_relative(self):
    dir_a_b = self._create_directory('a/b')
    dir_p = self._create_directory('p')
    os.symlink('../../p', os.path.join(dir_a_b, 'p'))
    self._create_directory('p/q/r')
    self._watcher.start()
    shutil.rmtree(dir_p)
    self._watcher.changes()
    # TODO: validate the value returned from self._watcher.changes() once
    # a solution is designed.

  def test_internal_symlinks_absolute(self):
    dir_a_b = self._create_directory('a/b')
    dir_p = self._create_directory('p')
    os.symlink(dir_p, os.path.join(dir_a_b, 'p'))
    self._create_directory('p/q/r')
    self._watcher.start()
    shutil.rmtree(dir_p)
    self._watcher.changes()
    # TODO: validate the value returned from self._watcher.changes() once
    # a solution is designed.

  @unittest.skip('b/14583335')
  def test_multiple_symlinks_same_directory(self):
    # Create a file inside the junk directory (the important point is it's
    # outside the watched directory).
    junk_file = os.path.join(self._junk_directory, 'file')
    with open(junk_file, 'w'):
      pass

    # Add a symlink from the watched directory to the junk directory. This
    # causes the file inside the junk directory to be watched.
    symlink_junkdir_1 = os.path.join(self._directory, 'junk1')
    os.symlink(self._junk_directory, symlink_junkdir_1)
    watched_junk_file = os.path.join(symlink_junkdir_1, 'file')

    self._watcher.start()

    # Make sure changes to the file are reported via the symlinked directory.
    with open(junk_file, 'w') as f:
      f.write('change1')
    self.assertEqual(
        set([watched_junk_file]),
        self._watcher.changes())

    # Temporarily create a second symlink to the junk directory. We don't
    # care about changed paths are reported, we just need to make sure the
    # inotify internals are updated both when the second symlink is added and
    # when it is removed.
    symlink_junkdir_2 = os.path.join(self._directory, 'junk2')
    os.symlink(self._junk_directory, symlink_junkdir_2)
    self._watcher.changes()
    os.unlink(symlink_junkdir_2)
    self._watcher.changes()

    # And make sure changes to the file are still reported.
    with open(junk_file, 'w') as f:
      f.write('change2')
    self.assertEqual(
        set([watched_junk_file]),
        self._watcher.changes())


@unittest.skipUnless(sys.platform.startswith('linux'), 'requires linux')
class TestInotifyFileWatcherMultipleDirectories(unittest.TestCase):
  """Tests for inotify_file_watcher.InotifyFileWatcher."""

  def setUp(self):
    self._directories = [tempfile.mkdtemp() for _ in range(4)]
    self._watcher = inotify_file_watcher.InotifyFileWatcher(self._directories)
    self._watcher.start()

  def tearDown(self):
    self._watcher.quit()
    for directory in self._directories:
      shutil.rmtree(directory)

  @staticmethod
  def _create_file(*paths):
    realpath = os.path.realpath(os.path.join(*paths))
    with open(realpath, 'w'):
      pass
    return realpath

  def testInDir0(self):
    path = self._create_file(self._directories[0], 'moo')
    self.assertEqual(
        set([path]),
        self._watcher.changes())

  def testInDir2(self):
    path = self._create_file(self._directories[2], 'moo')
    self.assertEqual(
        set([path]),
        self._watcher.changes())

  def testInDir1And3(self):
    path1 = self._create_file(self._directories[1], 'moo')
    path3 = self._create_file(self._directories[3], 'moo')
    self.assertEqual(
        set([path1, path3]),
        self._watcher.changes())


class TestBitStr(unittest.TestCase):
  _MASK_NAMES = {
      0x1: 'one',
      0x2: 'two',
      0x8: 'eight',
  }

  def testSingleBit(self):
    self.assertEquals(
        'one (0x1)',
        inotify_file_watcher._bit_str(0x1, self._MASK_NAMES))

  def testMultipleBits(self):
    self.assertEquals(
        'one|two|eight (0xb)',
        inotify_file_watcher._bit_str(0x1 | 0x2 | 0x8, self._MASK_NAMES))

  def testExtraBits(self):
    self.assertEquals(
        'one|two|(0x4)|eight|(0x10) (0x1f)',
        inotify_file_watcher._bit_str(0x1 | 0x2 | 0x4 | 0x8 | 0x10,
                                      self._MASK_NAMES))

if __name__ == '__main__':
  unittest.main()
