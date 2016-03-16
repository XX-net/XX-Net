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
"""Tests for google.appengine.tools.devappserver2.python.stubs."""



import errno
import locale
import mimetypes
import os
import random
import shutil
import sys
import tempfile
import unittest

import google

from distutils import util
import mox

from google.appengine.tools.devappserver2.python import stubs


class StubsTest(unittest.TestCase):

  def setUp(self):
    super(StubsTest, self).setUp()
    self.platform = sys.platform
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(locale, 'setlocale')
    self.mox.StubOutWithMock(util, 'get_platform')
    self.mox.StubOutWithMock(stubs.FakeFile, 'is_file_accessible')

  def tearDown(self):
    self.mox.UnsetStubs()
    sys.platform = self.platform
    super(StubsTest, self).tearDown()

  def test_os_error_not_implemented(self):
    with self.assertRaises(OSError) as cm:
      stubs.os_error_not_implemented()
    self.mox.VerifyAll()
    e = cm.exception
    self.assertEqual(errno.ENOSYS, e.errno)
    self.assertEqual('Function not implemented', e.strerror)
    self.assertIsNone(e.filename)

  def test_return_minus_one(self):
    self.assertEqual(-1, stubs.return_minus_one())

  def test_fake_uname(self):
    self.assertEqual(('Linux', '', '', '', ''), stubs.fake_uname())

  def test_fake_access_accessible(self):
    stubs.FakeFile.is_file_accessible(__file__).AndReturn(True)
    self.mox.ReplayAll()
    self.assertTrue(stubs.fake_access(__file__, os.R_OK))
    self.mox.VerifyAll()

  def test_fake_access_inaccessible(self):
    stubs.FakeFile.is_file_accessible(__file__).AndReturn(False)
    self.mox.ReplayAll()
    self.assertFalse(stubs.fake_access(__file__, os.R_OK))
    self.mox.VerifyAll()

  def test_fake_access_write(self):
    self.mox.ReplayAll()
    self.assertFalse(stubs.fake_access(__file__, os.W_OK))
    self.mox.VerifyAll()

  def test_fake_open_accessible(self):
    stubs.FakeFile.is_file_accessible(__file__).AndReturn(True)
    self.mox.ReplayAll()
    os.close(stubs.fake_open(__file__, os.O_RDONLY))
    self.mox.VerifyAll()

  def test_fake_open_inaccessible(self):
    stubs.FakeFile.is_file_accessible(__file__).AndReturn(False)
    self.mox.ReplayAll()
    with self.assertRaises(OSError) as cm:
      stubs.fake_open(__file__, os.O_RDONLY)
    self.mox.VerifyAll()
    e = cm.exception
    self.assertEqual(errno.ENOENT, e.errno)
    self.assertEqual('No such file or directory', e.strerror)
    self.assertEqual(__file__, e.filename)
    self.mox.VerifyAll()

  def test_fake_open_write(self):
    self.mox.ReplayAll()
    with self.assertRaises(OSError) as cm:
      stubs.fake_open(__file__, os.O_RDWR)
    self.mox.VerifyAll()
    e = cm.exception
    self.assertEqual(errno.EROFS, e.errno)
    self.assertEqual('Read-only file system', e.strerror)
    self.assertEqual(__file__, e.filename)
    self.mox.VerifyAll()

  def test_fake_set_locale_allowed(self):
    locale.setlocale(0, 'C')
    locale.setlocale(0, 'C')
    locale.setlocale(0, 'C')
    locale.setlocale(0, 'C')
    self.mox.ReplayAll()
    stubs.fake_set_locale(0, 'C', original_setlocale=locale.setlocale)
    stubs.fake_set_locale(0, None, original_setlocale=locale.setlocale)
    stubs.fake_set_locale(0, '', original_setlocale=locale.setlocale)
    stubs.fake_set_locale(0, 'POSIX', original_setlocale=locale.setlocale)
    self.mox.VerifyAll()

  def test_fake_set_locale_not_allowed(self):
    self.mox.ReplayAll()
    self.assertRaises(locale.Error, stubs.fake_set_locale, 0, 'AAAA')
    self.mox.VerifyAll()

  def test_fake_get_platform(self):
    sys.platform = 'linux2'
    self.mox.ReplayAll()
    self.assertEqual('linux-', stubs.fake_get_platform())
    self.mox.VerifyAll()

  def test_fake_get_platform_darwin(self):
    sys.platform = 'darwin'
    self.mox.ReplayAll()
    self.assertEqual('macosx-', stubs.fake_get_platform())
    self.mox.VerifyAll()

  def test_restricted_path_function_allowed(self):
    fake_function = self.mox.CreateMockAnything()
    fake_function('foo', bar='baz').AndReturn(1)
    stubs.FakeFile.is_file_accessible('foo').AndReturn(True)
    self.mox.ReplayAll()
    restricted_path_fake_function = stubs.RestrictedPathFunction(fake_function)
    self.assertEqual(1, restricted_path_fake_function('foo', bar='baz'))
    self.mox.VerifyAll()

  def test_restricted_path_function_not_allowed(self):
    fake_function = self.mox.CreateMockAnything()
    stubs.FakeFile.is_file_accessible('foo').AndReturn(False)
    self.mox.ReplayAll()
    restricted_path_fake_function = stubs.RestrictedPathFunction(fake_function)
    with self.assertRaises(OSError) as cm:
      restricted_path_fake_function('foo', bar='baz')
    self.mox.VerifyAll()
    e = cm.exception
    self.assertEqual(errno.EACCES, e.errno)
    self.assertEqual('path not accessible', e.strerror)
    self.assertEqual('foo', e.filename)


class FakeFileTest(unittest.TestCase):

  def setUp(self):
    super(FakeFileTest, self).setUp()
    self.mox = mox.Mox()
    self.tempdir = tempfile.mkdtemp()
    stubs.FakeFile._application_paths = []
    stubs.FakeFile.set_skip_files('^$')
    stubs.FakeFile.set_static_files('^$')

  def tearDown(self):
    stubs.FakeFile._application_paths = []
    self.mox.UnsetStubs()
    shutil.rmtree(self.tempdir)
    super(FakeFileTest, self).tearDown()

  def test_init_accessible(self):
    self.mox.StubOutWithMock(stubs.FakeFile, 'is_file_accessible')
    stubs.FakeFile.is_file_accessible(__file__).AndReturn(True)
    self.mox.ReplayAll()
    with stubs.FakeFile(__file__) as f:
      fake_file_content = f.read()
    self.mox.VerifyAll()
    with open(__file__) as f:
      real_file_content = f.read()
    self.assertEqual(real_file_content, fake_file_content)

  def test_init_inaccessible(self):
    self.mox.StubOutWithMock(stubs.FakeFile, 'is_file_accessible')
    stubs.FakeFile.is_file_accessible(__file__).AndReturn(False)
    self.mox.ReplayAll()
    self.assertRaises(IOError, stubs.FakeFile, __file__)
    self.mox.VerifyAll()

  def test_init_to_write(self):
    self.mox.StubOutWithMock(stubs.FakeFile, 'is_file_accessible')
    self.mox.ReplayAll()
    self.assertRaises(IOError, stubs.FakeFile, __file__, 'w')
    self.mox.VerifyAll()

  def test_init_to_append(self):
    self.mox.StubOutWithMock(stubs.FakeFile, 'is_file_accessible')
    self.mox.ReplayAll()
    self.assertRaises(IOError, stubs.FakeFile, __file__, 'a')
    self.mox.VerifyAll()

  def test_init_to_read_plus(self):
    self.mox.StubOutWithMock(stubs.FakeFile, 'is_file_accessible')
    self.mox.ReplayAll()
    self.assertRaises(IOError, stubs.FakeFile, __file__, 'r+')
    self.mox.VerifyAll()

  def test_is_accessible_accessible(self):
    open(os.path.join(self.tempdir, 'allowed'), 'w').close()
    stubs.FakeFile.set_allowed_paths(self.tempdir, [])
    self.assertTrue(stubs.FakeFile.is_file_accessible(
        os.path.join(self.tempdir, 'allowed')))

  def test_is_accessible_not_accessible(self):
    open(os.path.join(self.tempdir, 'not_allowed'), 'w').close()
    stubs.FakeFile.set_allowed_paths(os.path.join(self.tempdir, 'allowed'), [])
    self.assertFalse(stubs.FakeFile.is_file_accessible(
        os.path.join(self.tempdir, 'not_allowed')))

  def test_is_accessible_accessible_directory(self):
    os.mkdir(os.path.join(self.tempdir, 'allowed'))
    stubs.FakeFile.set_allowed_paths(self.tempdir, [])
    self.assertTrue(stubs.FakeFile.is_file_accessible(
        os.path.join(self.tempdir, 'allowed')))

  def test_is_accessible_not_accessible_directory(self):
    os.mkdir(os.path.join(self.tempdir, 'not_allowed'))
    stubs.FakeFile.set_allowed_paths(os.path.join(self.tempdir, 'allowed'), [])
    self.assertFalse(stubs.FakeFile.is_file_accessible(
        os.path.join(self.tempdir, 'not_allowed')))

  def test_is_accessible_accessible_in_application_dir(self):
    open(os.path.join(self.tempdir, 'allowed'), 'w').close()
    stubs.FakeFile.set_allowed_paths('.', [self.tempdir])
    self.assertTrue(stubs.FakeFile.is_file_accessible(
        os.path.join(self.tempdir, 'allowed')))

  def test_is_accessible_accessible_directory_in_application_dir(self):
    os.mkdir(os.path.join(self.tempdir, 'allowed'))
    stubs.FakeFile.set_allowed_paths('.', [self.tempdir])
    self.assertTrue(stubs.FakeFile.is_file_accessible(
        os.path.join(self.tempdir, 'allowed')))

  def test_is_accessible_mimetypes_files(self):
    stubs.FakeFile.set_allowed_paths(self.tempdir, [])
    for filename in mimetypes.knownfiles:
      if os.path.isfile(filename):
        self.assertTrue(stubs.FakeFile.is_file_accessible(filename))

  def test_is_accessible_skipped(self):
    open(os.path.join(self.tempdir, 'allowed'), 'w').close()
    stubs.FakeFile.set_allowed_paths(self.tempdir, [])
    stubs.FakeFile.set_skip_files('^%s$' % 'allowed')
    self.assertFalse(stubs.FakeFile.is_file_accessible(
        os.path.join(self.tempdir, 'allowed')))

  def test_is_accessible_skipped_root_appdir(self):
    stubs.FakeFile.set_allowed_paths(self.tempdir, [])
    stubs.FakeFile.set_skip_files(r'^(\..*)|$')
    self.assertTrue(stubs.FakeFile.is_file_accessible(self.tempdir))

  def test_is_accessible_skipped_root_appdir_with_trailing_slash(self):
    stubs.FakeFile.set_allowed_paths(self.tempdir, [])
    stubs.FakeFile.set_skip_files(r'^(\..*)|$')
    self.assertTrue(stubs.FakeFile.is_file_accessible(
        '%s%s' % (self.tempdir, os.path.sep)))

  def test_is_accessible_skipped_and_not_accessible(self):
    stubs.FakeFile.set_allowed_paths(os.path.join(self.tempdir, 'allowed'), [])
    stubs.FakeFile.set_skip_files('^.*%s.*$' % 'not_allowed')
    self.assertFalse(stubs.FakeFile.is_file_accessible(
        os.path.join(self.tempdir, 'not_allowed')))

  def test_is_accessible_skipped_outside_appdir(self):
    stubs.FakeFile.set_allowed_paths(os.path.join(self.tempdir, 'foo'),
                                     [os.path.join(self.tempdir, 'allowed')])
    stubs.FakeFile.set_skip_files('^.*%s.*$' % 'filename')
    self.assertTrue(stubs.FakeFile.is_file_accessible(
        os.path.join(self.tempdir, 'allowed', 'filename')))

  def test_is_accessible_static(self):
    open(os.path.join(self.tempdir, 'allowed'), 'w').close()
    stubs.FakeFile.set_allowed_paths(self.tempdir, [])
    stubs.FakeFile.set_static_files('^%s$' % 'allowed')
    self.assertFalse(stubs.FakeFile.is_file_accessible(
        os.path.join(self.tempdir, 'allowed')))

  def test_is_accessible_static_and_not_accessible(self):
    stubs.FakeFile.set_allowed_paths(os.path.join(self.tempdir, 'allowed'), [])
    stubs.FakeFile.set_static_files('^.*%s.*$' % 'not_allowed')
    self.assertFalse(stubs.FakeFile.is_file_accessible(
        os.path.join(self.tempdir, 'not_allowed')))

  def test_is_accessible_skipped_and_static_root_appdir(self):
    stubs.FakeFile.set_allowed_paths(self.tempdir, [])
    self.assertTrue(stubs.FakeFile.is_file_accessible(self.tempdir))

  def test_is_accessible_none_filename(self):
    self.assertRaises(TypeError, stubs.FakeFile.is_file_accessible, None)


if __name__ == '__main__':
  unittest.main()
