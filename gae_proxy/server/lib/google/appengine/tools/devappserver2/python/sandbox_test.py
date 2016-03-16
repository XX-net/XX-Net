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
"""Tests for google.appengine.tools.devappserver2.python.sandbox."""



import __builtin__
import imp
import os
import re
import sys
import types
import urllib
import unittest

import google

try:
  import lxml
except ImportError:
  raise unittest.SkipTest('sandbox_test could not import lxml')

try:
  import PIL
except ImportError:
  raise unittest.SkipTest('sandbox_test could not import PIL')

import mox

from google.appengine.tools.devappserver2 import runtime_config_pb2
from google.appengine.tools.devappserver2.python import sandbox
from google.appengine.tools.devappserver2.python import stubs


class SandboxTest(unittest.TestCase):
  def setUp(self):
    super(SandboxTest, self).setUp()
    self.mox = mox.Mox()
    self.old_path = sys.path
    self.old_meta_path = sys.meta_path
    self.old_library_format_string = sandbox._THIRD_PARTY_LIBRARY_FORMAT_STRING
    self.config = runtime_config_pb2.Config()
    self.app_root = 'test/app/root'
    self.config.application_root = self.app_root
    self.config.app_id = 'app'
    self.config.version_id = '1'
    self.builtins = __builtin__.__dict__.copy()
    self.modules = sys.modules.copy()

  def tearDown(self):
    sys.modules.clear()
    sys.modules.update(self.modules)
    __builtin__.__dict__.update(self.builtins)
    sys.meta_path = self.old_meta_path
    sys.path = self.old_path
    sandbox._THIRD_PARTY_LIBRARY_FORMAT_STRING = self.old_library_format_string
    self.mox.UnsetStubs()
    super(SandboxTest, self).tearDown()

  def test_enable_libraries(self):
    sandbox._THIRD_PARTY_LIBRARY_FORMAT_STRING = (
        'name=%(name)s-version=%(version)s')
    libs = self.config.libraries
    libs.add(name='foo', version='12345')
    libs.add(name='webapp2', version='2.5.1')
    self.assertEqual(
        [os.path.join(os.path.dirname(os.path.dirname(
            google.__file__)), 'name=foo-version=12345'),
         os.path.join(os.path.dirname(os.path.dirname(
             google.__file__)), 'name=webapp2-version=2.5.1')],
        sandbox._enable_libraries(libs))

  def test_enable_libraries_no_libraries(self):
    libs = self.config.libraries
    self.assertEqual([], sandbox._enable_libraries(libs))
    self.assertEqual(self.old_path, sys.path)


class ModuleOverrideImportHookTest(unittest.TestCase):
  def setUp(self):
    super(ModuleOverrideImportHookTest, self).setUp()
    self.test_policies = {}
    self.path = sys.path[:]
    self.hook = sandbox.ModuleOverrideImportHook(self.test_policies)
    sys.path_importer_cache = {}
    sys.modules.pop('distutils', None)
    __import__('distutils').__path__.insert(0, 'dummy/path')
    sys.modules.pop('distutils.util', None)
    sys.modules.pop('thread', None)
    self.imported_modules = set(sys.modules)
    self.path_hooks = sys.path_hooks

  def tearDown(self):
    sys.path_hooks = self.path_hooks
    sys.path_importer_cache = {}
    sys.path = self.path
    added_modules = set(sys.modules) - self.imported_modules
    for name in added_modules:
      del sys.modules[name]
    distutils_modules = [module for module in sys.modules if
                         module.startswith('distutils')]
    for name in distutils_modules:
      del sys.modules[name]
    sys.modules.pop('thread', None)
    super(ModuleOverrideImportHookTest, self).tearDown()

  def test_load_builtin_pass_through(self):
    symbols = dir(__import__('thread'))
    del sys.modules['thread']
    self.test_policies['thread'] = sandbox.ModuleOverridePolicy(
        None, [], {}, default_pass_through=True)
    thread = self.hook.load_module('thread')
    self.assertTrue(isinstance(thread, types.ModuleType))
    self.assertTrue(isinstance(thread.__doc__, str))
    self.assertItemsEqual(symbols + ['__loader__'], dir(thread))
    self.assertEqual(self.hook, thread.__loader__)

  def test_load_builtin_no_pass_through(self):
    self.test_policies['thread'] = sandbox.ModuleOverridePolicy(
        None, [], {}, default_pass_through=False)
    thread = self.hook.load_module('thread')
    self.assertTrue(isinstance(thread, types.ModuleType))
    self.assertItemsEqual(
        ['__doc__', '__name__', '__package__', '__loader__'], dir(thread))
    self.assertEqual(self.hook, thread.__loader__)

  def test_load_with_path_hook(self):

    class DummyPathHook(object):

      def __init__(self, path):
        if path != 'dummy/path':
          raise ImportError

      def find_module(self, unused_fullname):
        return self

      def load_module(self, fullname):
        return imp.new_module('fake name: %s' % fullname)

    self.test_policies['distutils.util'] = sandbox.ModuleOverridePolicy(
        None, [], {}, default_pass_through=True)
    sys.path_hooks = [DummyPathHook]
    util = self.hook.load_module('distutils.util')
    self.assertEqual('fake name: distutils.util', util.__name__)

  def test_load_with_path_hook_cant_find(self):

    class DummyPathHook(object):

      def __init__(self, path):
        if path != 'dummy/path':
          raise ImportError

      def find_module(self, unused_fullname):
        return None

      def load_module(self, fullname):
        raise ImportError

    self.test_policies['distutils.util'] = sandbox.ModuleOverridePolicy(
        None, [], {}, default_pass_through=True)
    sys.path_hooks = [DummyPathHook]
    util = self.hook.load_module('distutils.util')
    self.assertEqual('distutils.util', util.__name__)

  def test_load_without_path_hook(self):
    self.test_policies['urllib'] = sandbox.ModuleOverridePolicy(
        None, [], {}, default_pass_through=True)
    urllib = self.hook.load_module('urllib')
    self.assertIn('urlopen', urllib.__dict__)
    self.assertEqual('urllib', urllib.__name__)

  def test_load_without_path_hook_not_found(self):
    self.test_policies['urllib'] = sandbox.ModuleOverridePolicy(
        None, [], {}, default_pass_through=True)
    self.assertRaises(ImportError, self.hook.load_module, 'fake_module')

  def test_load_already_in_sys_modules(self):
    module = imp.new_module('foo')
    sys.modules['foo'] = module
    self.assertEqual(module, self.hook.load_module('foo'))

  def test_is_package(self):
    self.assertTrue(self.hook.is_package('distutils'))

  def test_is_package_standard_lib(self):
    self.assertTrue(self.hook.is_package('email'))

  def test_is_package_not_package_standard_lib(self):
    self.assertFalse(self.hook.is_package('urllib'))

  def test_is_package_not_package(self):
    self.assertFalse(self.hook.is_package('distutils.util'))

  def test_is_package_does_not_exist(self):
    self.assertRaises(ImportError, self.hook.is_package, 'foo.bar')

  def test_get_source(self):
    with open(__import__('distutils').__file__.replace('.pyc', '.py')) as f:
      source = f.read()
    self.assertEqual(source, self.hook.get_source('distutils'))

  def test_get_source_does_not_exist(self):
    self.assertRaises(ImportError, self.hook.get_source, 'foo.bar')

  def test_get_source_standard_library(self):
    # The expected value is hard to find if the standard library might or might
    # not be zipped so just check that a value is found.
    self.assertTrue(self.hook.get_source('urllib'))

  def test_get_code(self):
    filename = __import__('distutils').__file__.replace('.pyc', '.py')
    with open(filename) as f:
      expected_code = compile(f.read(), filename, 'exec')
    self.assertEqual(expected_code, self.hook.get_code('distutils'))

  def test_get_code_does_not_exist(self):
    self.assertRaises(ImportError, self.hook.get_code, 'foo.bar')

  def test_get_code_standard_library(self):
    # The expected value is hard to find if the standard library might or might
    # not be zipped so just check that a value is found.
    self.assertTrue(self.hook.get_code('urllib'))

  def test_os_module_policy(self):
    hooked_os = imp.new_module('os')
    hooked_os.__dict__.update(os.__dict__)
    sandbox._MODULE_OVERRIDE_POLICIES['os'].apply_policy(hooked_os.__dict__)
    self.assertEqual(stubs.return_minus_one, hooked_os.getpid)
    self.assertNotIn('execv', hooked_os.__dict__)
    self.assertEqual(stubs.os_error_not_implemented, hooked_os.unlink)
    self.assertEqual(os.walk, hooked_os.walk)


class CModuleImportHookTest(unittest.TestCase):
  def test_find_module_enabled_module(self):
    hook = sandbox.CModuleImportHook([re.compile(r'lxml\.')])
    self.assertIsNone(hook.find_module('lxml'))
    lxml = __import__('lxml')
    self.assertIsNone(hook.find_module('lxml.etree', lxml.__path__))

  def test_find_module_disabled_module(self):
    hook = sandbox.CModuleImportHook([re.compile(r'numpy\.')])
    self.assertIsNone(hook.find_module('lxml'))
    lxml = __import__('lxml')
    self.assertEqual(hook, hook.find_module('lxml.etree', lxml.__path__))

  def test_find_module_not_c_module(self):
    hook = sandbox.CModuleImportHook([])
    self.assertIsNone(hook.find_module('httplib'))

  def test_find_module_whitelisted(self):
    hook = sandbox.CModuleImportHook([])
    for name in sandbox._WHITE_LIST_C_MODULES:
      self.assertIsNone(hook.find_module(name))

  def test_find_module_not_whitelisted(self):
    hook = sandbox.CModuleImportHook([])
    self.assertEqual(hook, hook.find_module('__builtin__'))

  def test_find_module_not_whitelisted_enabled_via_libaries(self):
    hook = sandbox.CModuleImportHook([re.compile(r'__builtin__')])
    self.assertIsNone(hook.find_module('__builtin__'))

  def test_load_module(self):
    hook = sandbox.CModuleImportHook([])
    self.assertRaises(ImportError, hook.load_module, 'lxml')


class PathOverrideImportHookTest(unittest.TestCase):

  def setUp(self):
    self.saved_lxml = lxml
    self.saved_pil = PIL
    self.saved_urllib = urllib

  def tearDown(self):
    sys.modules['urllib'] = self.saved_urllib
    sys.modules['PIL'] = self.saved_pil
    sys.modules['lxml'] = self.saved_lxml

  def test_package_success(self):
    hook = sandbox.PathOverrideImportHook(['lxml'])
    self.assertEqual(hook, hook.find_module('lxml'))
    del sys.modules['lxml']
    hooked_lxml = hook.load_module('lxml')
    self.assertEqual(hooked_lxml.__file__, lxml.__file__)
    self.assertEqual(hooked_lxml.__path__, lxml.__path__)
    self.assertEqual(hooked_lxml.__loader__, hook)
    self.assertEqual([os.path.dirname(self.saved_lxml.__file__)],
                     hook.extra_accessible_paths)
    self.assertFalse(hook.extra_sys_paths)

  def test_package_success_pil_in_sys_path(self):
    hook = sandbox.PathOverrideImportHook(['PIL'])
    self.assertEqual(hook, hook.find_module('PIL'))
    del sys.modules['PIL']
    hooked_pil = hook.load_module('PIL')
    self.assertEqual(hooked_pil.__file__, PIL.__file__)
    self.assertEqual(hooked_pil.__path__, PIL.__path__)
    self.assertEqual(hooked_pil.__loader__, hook)
    self.assertFalse(hook.extra_accessible_paths)
    self.assertEqual([os.path.dirname(self.saved_pil.__file__)],
                     hook.extra_sys_paths)

  def test_module_success(self):
    hook = sandbox.PathOverrideImportHook(['urllib'])
    self.assertEqual(hook, hook.find_module('urllib'))
    del sys.modules['urllib']
    hooked_urllib = hook.load_module('urllib')
    self.assertEqual(hooked_urllib.__file__.replace('.pyc', '.py'),
                     urllib.__file__.replace('.pyc', '.py'))
    self.assertEqual(hooked_urllib.__loader__, hook)
    self.assertNotIn('__path__', hooked_urllib.__dict__)
    self.assertFalse(hook.extra_accessible_paths)
    self.assertFalse(hook.extra_sys_paths)

  def test_disabled_modules(self):
    hook = sandbox.PathOverrideImportHook(['lxml'])
    self.assertFalse(hook.find_module('lxml.foo'))
    self.assertFalse(hook.find_module('numpy'))
    self.assertFalse(hook.find_module('os'))

  def test_module_not_installed(self):
    hook = sandbox.PathOverrideImportHook(['foo'])
    self.assertFalse(hook.find_module('foo'))
    self.assertFalse(hook.extra_accessible_paths)
    self.assertFalse(hook.extra_sys_paths)

  def test_import_alread_in_sys_modules(self):
    hook = sandbox.PathOverrideImportHook(['lxml'])
    self.assertEqual(os, hook.load_module('os'))


class PathRestrictingImportHookTest(unittest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(imp, 'find_module')
    self.mox.StubOutWithMock(stubs.FakeFile, 'is_file_accessible')
    self.hook = sandbox.PathRestrictingImportHook([re.compile(r'lxml(\..*)?$')])

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_accessible(self):
    imp.find_module('bar', ['foo']).AndReturn((None, 'foo/bar.py',
                                               (None, None, imp.PY_SOURCE)))
    stubs.FakeFile.is_file_accessible('foo/bar.py').AndReturn(True)
    self.mox.ReplayAll()
    self.assertIsNone(self.hook.find_module('foo.bar', ['foo']))

  def test_not_accessible(self):
    imp.find_module('bar', ['foo']).AndReturn((None, 'foo/bar.py',
                                               (None, None, imp.PY_SOURCE)))
    stubs.FakeFile.is_file_accessible('foo/bar.py').AndReturn(False)
    self.mox.ReplayAll()
    self.assertEqual(self.hook, self.hook.find_module('foo.bar', ['foo']))

  def test_c_module_accessible(self):
    imp.find_module('bar', ['foo']).AndReturn((None, 'foo/bar.so',
                                               (None, None, imp.C_EXTENSION)))
    stubs.FakeFile.is_file_accessible('foo/bar.so').AndReturn(True)
    self.mox.ReplayAll()
    self.assertIsNone(self.hook.find_module('foo.bar', ['foo']))

  def test_c_module_not_accessible(self):
    imp.find_module('bar', ['foo']).AndReturn((None, 'foo/bar.so',
                                               (None, None, imp.C_EXTENSION)))
    stubs.FakeFile.is_file_accessible('foo/bar.so').AndReturn(False)
    self.mox.ReplayAll()
    self.assertEqual(self.hook, self.hook.find_module('foo.bar', ['foo']))

  def test_compiled_python_accessible(self):
    imp.find_module('bar', ['foo']).AndReturn((None, 'foo/bar.pyc',
                                               (None, None, imp.PY_COMPILED)))
    stubs.FakeFile.is_file_accessible('foo/bar.pyc').AndReturn(True)
    self.mox.ReplayAll()
    self.assertIsNone(self.hook.find_module('foo.bar', ['foo']))

  def test_compiled_python_not_accessible(self):
    imp.find_module('bar', ['foo']).AndReturn((None, 'foo/bar.pyc',
                                               (None, None, imp.PY_COMPILED)))
    stubs.FakeFile.is_file_accessible('foo/bar.pyc').AndReturn(False)
    self.mox.ReplayAll()
    self.assertEqual(self.hook, self.hook.find_module('foo.bar', ['foo']))

  def test_c_builtin(self):
    imp.find_module('bar', ['foo']).AndReturn((None, 'bar',
                                               (None, None, imp.C_BUILTIN)))
    self.mox.ReplayAll()
    self.assertIsNone(self.hook.find_module('foo.bar', ['foo']))

  def test_py_frozen(self):
    imp.find_module('bar', ['foo']).AndReturn((None, 'bar',
                                               (None, None, imp.PY_FROZEN)))
    self.mox.ReplayAll()
    self.assertIsNone(self.hook.find_module('foo.bar', ['foo']))

  def test_enabled_c_library(self):
    imp.find_module('lxmla', ['foo']).AndReturn((None, 'lxmla.py',
                                                 (None, None, imp.PY_SOURCE)))
    stubs.FakeFile.is_file_accessible('lxmla.py').AndReturn(False)
    self.mox.ReplayAll()
    self.assertEqual(self.hook, self.hook.find_module('lxmla', ['foo']))
    self.assertIsNone(self.hook.find_module('lxml', None))
    self.assertIsNone(self.hook.find_module('lxml.html', None))

  def test_load_module(self):
    self.assertRaises(ImportError, self.hook.load_module, 'os')


class PyCryptoRandomImportHookTest(unittest.TestCase):

  def test_find_module(self):
    self.assertIsInstance(
        sandbox.PyCryptoRandomImportHook.find_module(
            'Crypto.Random.OSRNG.posix'),
        sandbox.PyCryptoRandomImportHook)
    self.assertIsNone(
        sandbox.PyCryptoRandomImportHook.find_module('Crypto.Random.OSRNG.nt'))


if __name__ == '__main__':
  unittest.main()
