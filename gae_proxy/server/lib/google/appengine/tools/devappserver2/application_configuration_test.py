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
"""Tests for google.apphosting.tools.devappserver2.application_configuration."""



import collections
from contextlib import contextmanager
import datetime
import io
import os.path
import shutil
import tempfile
import unittest

import google
import mox

from google.appengine.api import appinfo
from google.appengine.api import appinfo_includes
from google.appengine.api import backendinfo
from google.appengine.api import dispatchinfo
from google.appengine.tools.devappserver2 import application_configuration
from google.appengine.tools.devappserver2 import errors


@contextmanager
def _java_temporarily_supported():
  """Make the java_supported() function return True temporarily.

   Use as:
     with _java_temporarily_supported():
       ...test that relies on Java being supported...
  """
  old_java_supported = application_configuration.java_supported
  application_configuration.java_supported = lambda: True
  yield
  application_configuration.java_supported = old_java_supported


_DEFAULT_HEALTH_CHECK = appinfo.HealthCheck(
    enable_health_check=True,
    check_interval_sec=5,
    timeout_sec=4,
    unhealthy_threshold=2,
    healthy_threshold=2,
    restart_threshold=60,
    host='127.0.0.1')


class TestModuleConfiguration(unittest.TestCase):
  """Tests for application_configuration.ModuleConfiguration."""

  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(appinfo_includes, 'ParseAndReturnIncludePaths')
    self.mox.StubOutWithMock(os.path, 'getmtime')
    application_configuration.open = self._fake_open

  def tearDown(self):
    self.mox.UnsetStubs()
    del application_configuration.open

  @staticmethod
  def _fake_open(unused_filename):
    return io.BytesIO()

  def test_good_app_yaml_configuration(self):
    automatic_scaling = appinfo.AutomaticScaling(min_pending_latency='1.0s',
                                                 max_pending_latency='2.0s',
                                                 min_idle_instances=1,
                                                 max_idle_instances=2)
    error_handlers = [appinfo.ErrorHandlers(file='error.html')]
    handlers = [appinfo.URLMap()]
    env_variables = appinfo.EnvironmentVariables()
    info = appinfo.AppInfoExternal(
        application='app',
        module='module1',
        version='1',
        runtime='python27',
        threadsafe=False,
        automatic_scaling=automatic_scaling,
        skip_files=r'\*.gif',
        error_handlers=error_handlers,
        handlers=handlers,
        inbound_services=['warmup'],
        env_variables=env_variables,
        )
    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)

    self.mox.ReplayAll()
    config = application_configuration.ModuleConfiguration('/appdir/app.yaml')
    self.mox.VerifyAll()

    self.assertEqual(os.path.realpath('/appdir'), config.application_root)
    self.assertEqual(os.path.realpath('/appdir/app.yaml'), config.config_path)
    self.assertEqual('dev~app', config.application)
    self.assertEqual('app', config.application_external_name)
    self.assertEqual('dev', config.partition)
    self.assertEqual('module1', config.module_name)
    self.assertEqual('1', config.major_version)
    self.assertRegexpMatches(config.version_id, r'module1:1\.\d+')
    self.assertEqual('python27', config.runtime)
    self.assertFalse(config.threadsafe)
    self.assertEqual(automatic_scaling, config.automatic_scaling)
    self.assertEqual(info.GetNormalizedLibraries(),
                     config.normalized_libraries)
    self.assertEqual(r'\*.gif', config.skip_files)
    self.assertEqual(error_handlers, config.error_handlers)
    self.assertEqual(handlers, config.handlers)
    self.assertEqual(['warmup'], config.inbound_services)
    self.assertEqual(env_variables, config.env_variables)
    self.assertEqual({'/appdir/app.yaml': 10}, config._mtimes)
    self.assertEqual(_DEFAULT_HEALTH_CHECK, config.health_check)

  def test_app_yaml_with_service(self):
    handlers = [appinfo.URLMap()]
    info = appinfo.AppInfoExternal(
        application='app',
        service='module1',
        version='1',
        runtime='python27',
        threadsafe=False,
        handlers=handlers,
        )
    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)

    self.mox.ReplayAll()
    config = application_configuration.ModuleConfiguration('/appdir/app.yaml')
    self.mox.VerifyAll()

    self.assertEqual('dev~app', config.application)
    self.assertEqual('app', config.application_external_name)
    self.assertEqual('module1', config.module_name)
    self.assertEqual('1', config.major_version)

  def test_vm_app_yaml_configuration_with_env(self):
    manual_scaling = appinfo.ManualScaling()
    vm_settings = appinfo.VmSettings()
    vm_settings['vm_runtime'] = 'myawesomeruntime'
    vm_settings['forwarded_ports'] = '49111:49111,5002:49112,8000'
    health_check = appinfo.HealthCheck()
    health_check.enable_health_check = False
    info = appinfo.AppInfoExternal(
        application='app',
        module='module1',
        version='1',
        runtime='vm',
        env='2',
        vm_settings=vm_settings,
        threadsafe=False,
        manual_scaling=manual_scaling,
        health_check=health_check
    )

    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)

    self.mox.ReplayAll()
    config = application_configuration.ModuleConfiguration('/appdir/app.yaml')

    self.mox.VerifyAll()
    self.assertEqual('2', config.env)

  def test_vm_app_yaml_configuration(self):
    manual_scaling = appinfo.ManualScaling()
    vm_settings = appinfo.VmSettings()
    vm_settings['vm_runtime'] = 'myawesomeruntime'
    vm_settings['forwarded_ports'] = '49111:49111,5002:49112,8000'
    health_check = appinfo.HealthCheck()
    health_check.enable_health_check = False
    info = appinfo.AppInfoExternal(
        application='app',
        module='module1',
        version='1',
        runtime='vm',
        vm_settings=vm_settings,
        threadsafe=False,
        manual_scaling=manual_scaling,
        health_check=health_check
    )

    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)

    self.mox.ReplayAll()
    config = application_configuration.ModuleConfiguration('/appdir/app.yaml')

    self.mox.VerifyAll()
    self.assertEqual(os.path.realpath('/appdir'), config.application_root)
    self.assertEqual(os.path.realpath('/appdir/app.yaml'), config.config_path)
    self.assertEqual('dev~app', config.application)
    self.assertEqual('app', config.application_external_name)
    self.assertEqual('dev', config.partition)
    self.assertEqual('module1', config.module_name)
    self.assertEqual('1', config.major_version)
    self.assertRegexpMatches(config.version_id, r'module1:1\.\d+')
    self.assertEqual('vm', config.runtime)
    self.assertEqual(vm_settings['vm_runtime'], config.effective_runtime)
    self.assertItemsEqual(
        {49111: 49111, 5002: 49112, 8000: 8000},
        config.forwarded_ports)
    self.assertFalse(config.threadsafe)
    self.assertEqual(manual_scaling, config.manual_scaling)
    self.assertEqual({'/appdir/app.yaml': 10}, config._mtimes)
    self.assertEqual(info.health_check, config.health_check)

  def test_vm_app_yaml_configuration_network(self):
    manual_scaling = appinfo.ManualScaling()
    vm_settings = appinfo.VmSettings()
    vm_settings['vm_runtime'] = 'myawesomeruntime'
    network = appinfo.Network()
    network.forwarded_ports = ['49111:49111', '5002:49112', 8000]
    health_check = appinfo.HealthCheck()
    health_check.enable_health_check = False
    info = appinfo.AppInfoExternal(
        application='app',
        module='module1',
        version='1',
        runtime='vm',
        vm_settings=vm_settings,
        threadsafe=False,
        manual_scaling=manual_scaling,
        health_check=health_check,
        network=network
    )

    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)

    self.mox.ReplayAll()
    config = application_configuration.ModuleConfiguration('/appdir/app.yaml')

    self.mox.VerifyAll()
    self.assertEqual(os.path.realpath('/appdir'), config.application_root)
    self.assertEqual(os.path.realpath('/appdir/app.yaml'), config.config_path)
    self.assertEqual('dev~app', config.application)
    self.assertEqual('app', config.application_external_name)
    self.assertEqual('dev', config.partition)
    self.assertEqual('module1', config.module_name)
    self.assertEqual('1', config.major_version)
    self.assertRegexpMatches(config.version_id, r'module1:1\.\d+')
    self.assertEqual('vm', config.runtime)
    self.assertEqual(vm_settings['vm_runtime'], config.effective_runtime)
    self.assertItemsEqual(
        {49111: 49111, 5002: 49112, 8000: 8000},
        config.forwarded_ports)
    self.assertFalse(config.threadsafe)
    self.assertEqual(manual_scaling, config.manual_scaling)
    self.assertEqual({'/appdir/app.yaml': 10}, config._mtimes)
    self.assertEqual(info.health_check, config.health_check)

  def test_vm_no_version(self):
    manual_scaling = appinfo.ManualScaling()
    info = appinfo.AppInfoExternal(
        application='app',
        module='module1',
        runtime='vm',
        threadsafe=False,
        manual_scaling=manual_scaling,
    )

    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)

    self.mox.StubOutWithMock(application_configuration, 'generate_version_id')
    application_configuration.generate_version_id().AndReturn(
        'generated-version')
    self.mox.ReplayAll()
    config = application_configuration.ModuleConfiguration('/appdir/app.yaml')

    self.mox.VerifyAll()
    self.assertEqual(config.major_version, 'generated-version')

  def test_vm_health_check_taken_into_account(self):
    manual_scaling = appinfo.ManualScaling()
    vm_settings = appinfo.VmSettings()
    vm_settings['vm_runtime'] = 'myawesomeruntime'
    vm_settings['forwarded_ports'] = '49111:49111,5002:49112,8000'
    vm_health_check = appinfo.VmHealthCheck(enable_health_check=False)
    info = appinfo.AppInfoExternal(
        application='app',
        module='module1',
        version='1',
        runtime='vm',
        vm_settings=vm_settings,
        threadsafe=False,
        manual_scaling=manual_scaling,
        vm_health_check=vm_health_check
    )

    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)

    self.mox.ReplayAll()
    config = application_configuration.ModuleConfiguration('/appdir/app.yaml')

    self.mox.VerifyAll()
    # tests if it is not overriden from the defaults of health_check
    self.assertIs(config.health_check.enable_health_check, False)

  def test_set_health_check_defaults(self):
    # Pass nothing in.
    self.assertEqual(
        _DEFAULT_HEALTH_CHECK,
        application_configuration._set_health_check_defaults(None))

    # Pass in an empty object.
    self.assertEqual(
        _DEFAULT_HEALTH_CHECK,
        application_configuration._set_health_check_defaults(
            appinfo.HealthCheck()))

    # Override some.
    health_check = appinfo.HealthCheck(restart_threshold=7,
                                       healthy_threshold=4)
    defaults_set = application_configuration._set_health_check_defaults(
        health_check)

    self.assertEqual(defaults_set.enable_health_check,
                     _DEFAULT_HEALTH_CHECK.enable_health_check)
    self.assertEqual(defaults_set.check_interval_sec,
                     _DEFAULT_HEALTH_CHECK.check_interval_sec)
    self.assertEqual(defaults_set.timeout_sec,
                     _DEFAULT_HEALTH_CHECK.timeout_sec)
    self.assertEqual(defaults_set.unhealthy_threshold,
                     _DEFAULT_HEALTH_CHECK.unhealthy_threshold)
    self.assertEqual(defaults_set.healthy_threshold, 4)
    self.assertEqual(defaults_set.restart_threshold, 7)
    self.assertEqual(defaults_set.host,
                     _DEFAULT_HEALTH_CHECK.host)

  def test_override_app_id(self):
    info = appinfo.AppInfoExternal(
        application='ignored-app',
        module='default',
        version='version',
        runtime='python27',
        threadsafe=False)
    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)
    os.path.getmtime('/appdir/app.yaml').AndReturn(20)
    os.path.getmtime('/appdir/app.yaml').AndReturn(20)
    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info, []))

    self.mox.ReplayAll()
    config = application_configuration.ModuleConfiguration(
        '/appdir/app.yaml', 'overriding-app')
    self.assertEqual('overriding-app', config.application_external_name)
    self.assertEqual('dev~overriding-app', config.application)
    config.check_for_updates()
    self.assertEqual('overriding-app', config.application_external_name)
    self.assertEqual('dev~overriding-app', config.application)
    self.mox.VerifyAll()

  def test_check_for_updates_unchanged_mtime(self):
    info = appinfo.AppInfoExternal(
        application='app',
        module='default',
        version='version',
        runtime='python27',
        threadsafe=False)
    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)

    self.mox.ReplayAll()
    config = application_configuration.ModuleConfiguration('/appdir/app.yaml')
    self.assertSequenceEqual(set(), config.check_for_updates())
    self.mox.VerifyAll()

  def test_check_for_updates_with_includes(self):
    info = appinfo.AppInfoExternal(
        application='app',
        module='default',
        version='version',
        runtime='python27',
        includes=['/appdir/include.yaml'],
        threadsafe=False)
    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info, ['/appdir/include.yaml']))
    os.path.getmtime('/appdir/app.yaml').InAnyOrder().AndReturn(10)
    os.path.getmtime('/appdir/include.yaml').InAnyOrder().AndReturn(10)
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)
    os.path.getmtime('/appdir/include.yaml').AndReturn(11)

    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info, ['/appdir/include.yaml']))
    os.path.getmtime('/appdir/app.yaml').InAnyOrder().AndReturn(10)
    os.path.getmtime('/appdir/include.yaml').InAnyOrder().AndReturn(11)

    self.mox.ReplayAll()
    config = application_configuration.ModuleConfiguration('/appdir/app.yaml')
    self.assertEqual({'/appdir/app.yaml': 10, '/appdir/include.yaml': 10},
                     config._mtimes)
    config._mtimes = collections.OrderedDict([('/appdir/app.yaml', 10),
                                              ('/appdir/include.yaml', 10)])
    self.assertSequenceEqual(set(), config.check_for_updates())
    self.mox.VerifyAll()
    self.assertEqual({'/appdir/app.yaml': 10, '/appdir/include.yaml': 11},
                     config._mtimes)

  def test_check_for_updates_no_changes(self):
    info = appinfo.AppInfoExternal(
        application='app',
        module='default',
        version='version',
        runtime='python27',
        threadsafe=False)
    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)
    os.path.getmtime('/appdir/app.yaml').AndReturn(11)
    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(11)

    self.mox.ReplayAll()
    config = application_configuration.ModuleConfiguration('/appdir/app.yaml')
    self.assertSequenceEqual(set(), config.check_for_updates())
    self.mox.VerifyAll()
    self.assertEqual({'/appdir/app.yaml': 11}, config._mtimes)

  def test_check_for_updates_immutable_changes(self):
    automatic_scaling1 = appinfo.AutomaticScaling(
        min_pending_latency='0.1s',
        max_pending_latency='1.0s',
        min_idle_instances=1,
        max_idle_instances=2)
    info1 = appinfo.AppInfoExternal(
        application='app',
        module='default',
        version='version',
        runtime='python27',
        threadsafe=False,
        automatic_scaling=automatic_scaling1)

    info2 = appinfo.AppInfoExternal(
        application='app2',
        module='default2',
        version='version2',
        runtime='python',
        threadsafe=True,
        automatic_scaling=appinfo.AutomaticScaling(
            min_pending_latency='1.0s',
            max_pending_latency='2.0s',
            min_idle_instances=1,
            max_idle_instances=2))

    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info1, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)
    os.path.getmtime('/appdir/app.yaml').AndReturn(11)
    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info2, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(11)

    self.mox.ReplayAll()
    config = application_configuration.ModuleConfiguration('/appdir/app.yaml')
    self.assertSequenceEqual(set(), config.check_for_updates())
    self.mox.VerifyAll()

    self.assertEqual('dev~app', config.application)
    self.assertEqual('default', config.module_name)
    self.assertEqual('version', config.major_version)
    self.assertRegexpMatches(config.version_id, r'^version\.\d+$')
    self.assertEqual('python27', config.runtime)
    self.assertFalse(config.threadsafe)
    self.assertEqual(automatic_scaling1, config.automatic_scaling)

  def test_check_for_updates_mutable_changes(self):
    info1 = appinfo.AppInfoExternal(
        application='app',
        module='default',
        version='version',
        runtime='python27',
        threadsafe=False,
        libraries=[appinfo.Library(name='django', version='latest')],
        skip_files='.*',
        handlers=[],
        inbound_services=['warmup'],
        env_variables=appinfo.EnvironmentVariables(),
        error_handlers=[appinfo.ErrorHandlers(file='error.html')],
        )
    info2 = appinfo.AppInfoExternal(
        application='app',
        module='default',
        version='version',
        runtime='python27',
        threadsafe=False,
        libraries=[appinfo.Library(name='jinja2', version='latest')],
        skip_files=r'.*\.py',
        handlers=[appinfo.URLMap()],
        inbound_services=[],
        )

    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info1, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)
    os.path.getmtime('/appdir/app.yaml').AndReturn(11)
    appinfo_includes.ParseAndReturnIncludePaths(mox.IgnoreArg()).AndReturn(
        (info2, []))
    os.path.getmtime('/appdir/app.yaml').AndReturn(11)

    self.mox.ReplayAll()
    config = application_configuration.ModuleConfiguration('/appdir/app.yaml')
    self.assertSequenceEqual(
        set([application_configuration.NORMALIZED_LIBRARIES_CHANGED,
             application_configuration.SKIP_FILES_CHANGED,
             application_configuration.HANDLERS_CHANGED,
             application_configuration.INBOUND_SERVICES_CHANGED,
             application_configuration.ENV_VARIABLES_CHANGED,
             application_configuration.ERROR_HANDLERS_CHANGED]),
        config.check_for_updates())
    self.mox.VerifyAll()

    self.assertEqual(info2.GetNormalizedLibraries(),
                     config.normalized_libraries)
    self.assertEqual(info2.skip_files, config.skip_files)
    self.assertEqual(info2.error_handlers, config.error_handlers)
    self.assertEqual(info2.handlers, config.handlers)
    self.assertEqual(info2.inbound_services, config.inbound_services)
    self.assertEqual(info2.env_variables, config.env_variables)



class TestBackendsConfiguration(unittest.TestCase):
  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(
        application_configuration.BackendsConfiguration,
        '_parse_configuration')
    self.mox.StubOutWithMock(application_configuration, 'BackendConfiguration')

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_good_configuration(self):
    self.mox.StubOutWithMock(application_configuration, 'ModuleConfiguration')
    static_backend_entry = backendinfo.BackendEntry(name='static')
    dynamic_backend_entry = backendinfo.BackendEntry(name='dynamic')
    backend_info = backendinfo.BackendInfoExternal(
        backends=[static_backend_entry, dynamic_backend_entry])
    module_config = object()
    application_configuration.ModuleConfiguration(
        '/appdir/app.yaml', None).AndReturn(module_config)
    application_configuration.BackendsConfiguration._parse_configuration(
        '/appdir/backends.yaml').AndReturn(backend_info)
    static_configuration = object()
    dynamic_configuration = object()
    application_configuration.BackendConfiguration(
        module_config,
        mox.IgnoreArg(),
        static_backend_entry).InAnyOrder().AndReturn(static_configuration)
    application_configuration.BackendConfiguration(
        module_config,
        mox.IgnoreArg(),
        dynamic_backend_entry).InAnyOrder().AndReturn(dynamic_configuration)

    self.mox.ReplayAll()
    config = application_configuration.BackendsConfiguration(
        '/appdir/app.yaml',
        '/appdir/backends.yaml')
    self.assertItemsEqual([static_configuration, dynamic_configuration],
                          config.get_backend_configurations())
    self.mox.VerifyAll()

  def test_no_backends(self):
    self.mox.StubOutWithMock(application_configuration, 'ModuleConfiguration')
    backend_info = backendinfo.BackendInfoExternal()
    module_config = object()
    application_configuration.ModuleConfiguration(
        '/appdir/app.yaml', None).AndReturn(module_config)
    application_configuration.BackendsConfiguration._parse_configuration(
        '/appdir/backends.yaml').AndReturn(backend_info)

    self.mox.ReplayAll()
    config = application_configuration.BackendsConfiguration(
        '/appdir/app.yaml',
        '/appdir/backends.yaml')
    self.assertEqual([], config.get_backend_configurations())
    self.mox.VerifyAll()

  def test_check_for_changes(self):
    static_backend_entry = backendinfo.BackendEntry(name='static')
    dynamic_backend_entry = backendinfo.BackendEntry(name='dynamic')
    backend_info = backendinfo.BackendInfoExternal(
        backends=[static_backend_entry, dynamic_backend_entry])
    module_config = self.mox.CreateMock(
        application_configuration.ModuleConfiguration)
    self.mox.StubOutWithMock(application_configuration, 'ModuleConfiguration')
    application_configuration.ModuleConfiguration(
        '/appdir/app.yaml', None).AndReturn(module_config)
    application_configuration.BackendsConfiguration._parse_configuration(
        '/appdir/backends.yaml').AndReturn(backend_info)
    module_config.check_for_updates().AndReturn(set())
    module_config.check_for_updates().AndReturn(set([1]))
    module_config.check_for_updates().AndReturn(set([2]))
    module_config.check_for_updates().AndReturn(set())

    self.mox.ReplayAll()
    config = application_configuration.BackendsConfiguration(
        '/appdir/app.yaml',
        '/appdir/backends.yaml')
    self.assertEqual(set(), config.check_for_updates('dynamic'))
    self.assertEqual(set([1]), config.check_for_updates('static'))
    self.assertEqual(set([1, 2]), config.check_for_updates('dynamic'))
    self.assertEqual(set([2]), config.check_for_updates('static'))
    self.mox.VerifyAll()


class TestDispatchConfiguration(unittest.TestCase):
  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(os.path, 'getmtime')
    self.mox.StubOutWithMock(
        application_configuration.DispatchConfiguration,
        '_parse_configuration')

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_good_configuration(self):
    info = dispatchinfo.DispatchInfoExternal(
        application='appid',
        dispatch=[
            dispatchinfo.DispatchEntry(url='*/path', module='foo'),
            dispatchinfo.DispatchEntry(url='domain.com/path', module='bar'),
            dispatchinfo.DispatchEntry(url='*/path/*', module='baz'),
            dispatchinfo.DispatchEntry(url='*.domain.com/path/*', module='foo'),
            ])

    os.path.getmtime('/appdir/dispatch.yaml').AndReturn(123.456)
    application_configuration.DispatchConfiguration._parse_configuration(
        '/appdir/dispatch.yaml').AndReturn(info)

    self.mox.ReplayAll()
    config = application_configuration.DispatchConfiguration(
        '/appdir/dispatch.yaml')
    self.mox.VerifyAll()

    self.assertEqual(123.456, config._mtime)
    self.assertEqual(2, len(config.dispatch))
    self.assertEqual(vars(dispatchinfo.ParsedURL('*/path')),
                     vars(config.dispatch[0][0]))
    self.assertEqual('foo', config.dispatch[0][1])
    self.assertEqual(vars(dispatchinfo.ParsedURL('*/path/*')),
                     vars(config.dispatch[1][0]))
    self.assertEqual('baz', config.dispatch[1][1])

  def test_check_for_updates_no_modification(self):
    info = dispatchinfo.DispatchInfoExternal(
        application='appid',
        dispatch=[])

    os.path.getmtime('/appdir/dispatch.yaml').AndReturn(123.456)
    application_configuration.DispatchConfiguration._parse_configuration(
        '/appdir/dispatch.yaml').AndReturn(info)
    os.path.getmtime('/appdir/dispatch.yaml').AndReturn(123.456)

    self.mox.ReplayAll()
    config = application_configuration.DispatchConfiguration(
        '/appdir/dispatch.yaml')
    config.check_for_updates()
    self.mox.VerifyAll()

  def test_check_for_updates_with_invalid_modification(self):
    info = dispatchinfo.DispatchInfoExternal(
        application='appid',
        dispatch=[
            dispatchinfo.DispatchEntry(url='*/path', module='bar'),
            ])

    os.path.getmtime('/appdir/dispatch.yaml').AndReturn(123.456)
    application_configuration.DispatchConfiguration._parse_configuration(
        '/appdir/dispatch.yaml').AndReturn(info)
    os.path.getmtime('/appdir/dispatch.yaml').AndReturn(124.456)
    application_configuration.DispatchConfiguration._parse_configuration(
        '/appdir/dispatch.yaml').AndRaise(Exception)

    self.mox.ReplayAll()
    config = application_configuration.DispatchConfiguration(
        '/appdir/dispatch.yaml')
    self.assertEqual('bar', config.dispatch[0][1])
    config.check_for_updates()
    self.mox.VerifyAll()
    self.assertEqual('bar', config.dispatch[0][1])

  def test_check_for_updates_with_modification(self):
    info = dispatchinfo.DispatchInfoExternal(
        application='appid',
        dispatch=[
            dispatchinfo.DispatchEntry(url='*/path', module='bar'),
            ])
    new_info = dispatchinfo.DispatchInfoExternal(
        application='appid',
        dispatch=[
            dispatchinfo.DispatchEntry(url='*/path', module='foo'),
            ])

    os.path.getmtime('/appdir/dispatch.yaml').AndReturn(123.456)
    application_configuration.DispatchConfiguration._parse_configuration(
        '/appdir/dispatch.yaml').AndReturn(info)
    os.path.getmtime('/appdir/dispatch.yaml').AndReturn(124.456)
    application_configuration.DispatchConfiguration._parse_configuration(
        '/appdir/dispatch.yaml').AndReturn(new_info)

    self.mox.ReplayAll()
    config = application_configuration.DispatchConfiguration(
        '/appdir/dispatch.yaml')
    self.assertEqual('bar', config.dispatch[0][1])
    config.check_for_updates()
    self.mox.VerifyAll()
    self.assertEqual('foo', config.dispatch[0][1])


class TestBackendConfiguration(unittest.TestCase):
  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(
        application_configuration.ModuleConfiguration,
        '_parse_configuration')
    self.mox.StubOutWithMock(os.path, 'getmtime')

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_good_configuration(self):
    automatic_scaling = appinfo.AutomaticScaling(min_pending_latency='1.0s',
                                                 max_pending_latency='2.0s',
                                                 min_idle_instances=1,
                                                 max_idle_instances=2)
    error_handlers = [appinfo.ErrorHandlers(file='error.html')]
    handlers = [appinfo.URLMap()]
    env_variables = appinfo.EnvironmentVariables()
    info = appinfo.AppInfoExternal(
        application='app',
        module='module1',
        env='1',
        version='1',
        runtime='python27',
        threadsafe=False,
        automatic_scaling=automatic_scaling,
        skip_files=r'\*.gif',
        error_handlers=error_handlers,
        handlers=handlers,
        inbound_services=['warmup'],
        env_variables=env_variables,
        )
    backend_entry = backendinfo.BackendEntry(
        name='static',
        instances='3',
        options='public')

    application_configuration.ModuleConfiguration._parse_configuration(
        '/appdir/app.yaml').AndReturn((info, ['/appdir/app.yaml']))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)

    self.mox.ReplayAll()
    module_config = application_configuration.ModuleConfiguration(
        '/appdir/app.yaml')
    config = application_configuration.BackendConfiguration(
        module_config, None, backend_entry)
    self.mox.VerifyAll()

    self.assertEqual(os.path.realpath('/appdir'), config.application_root)
    self.assertEqual('dev~app', config.application)
    self.assertEqual('app', config.application_external_name)
    self.assertEqual('dev', config.partition)
    self.assertEqual('1', config.env)
    self.assertEqual('static', config.module_name)
    self.assertEqual('1', config.major_version)
    self.assertRegexpMatches(config.version_id, r'static:1\.\d+')
    self.assertEqual('python27', config.runtime)
    self.assertFalse(config.threadsafe)
    self.assertEqual(None, config.automatic_scaling)
    self.assertEqual(None, config.basic_scaling)
    self.assertEqual(appinfo.ManualScaling(instances='3'),
                     config.manual_scaling)
    self.assertEqual(info.GetNormalizedLibraries(),
                     config.normalized_libraries)
    self.assertEqual(r'\*.gif', config.skip_files)
    self.assertEqual(error_handlers, config.error_handlers)
    self.assertEqual(handlers, config.handlers)
    self.assertEqual(['warmup'], config.inbound_services)
    self.assertEqual(env_variables, config.env_variables)

    whitelist_fields = ['module_name', 'version_id', 'automatic_scaling',
                        'manual_scaling', 'basic_scaling', 'is_backend',
                        'minor_version']
    # Check that all public attributes and methods in a ModuleConfiguration
    # exist in a BackendConfiguration.
    for field in dir(module_config):
      if not field.startswith('_'):
        self.assertTrue(hasattr(config, field), 'Missing field: %s' % field)
        value = getattr(module_config, field)
        if field not in whitelist_fields and not callable(value):
          # Check that the attributes other than those in the whitelist have
          # equal values in the BackendConfiguration to the ModuleConfiguration
          # from which it inherits.
          self.assertEqual(value, getattr(config, field))

  def test_vm_app_yaml_configuration(self):
    automatic_scaling = appinfo.AutomaticScaling(min_pending_latency='1.0s',
                                                 max_pending_latency='2.0s',
                                                 min_idle_instances=1,
                                                 max_idle_instances=2)
    beta_settings = appinfo.BetaSettings()
    beta_settings['vm_runtime'] = 'myawesomeruntime'
    info = appinfo.AppInfoExternal(
        application='app',
        module='module1',
        version='1',
        runtime='vm',
        beta_settings=beta_settings,
        threadsafe=False,
        automatic_scaling=automatic_scaling,
    )
    backend_entry = backendinfo.BackendEntry(
        name='static',
        instances='3',
        options='public')
    application_configuration.ModuleConfiguration._parse_configuration(
        '/appdir/app.yaml').AndReturn((info, ['/appdir/app.yaml']))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)

    self.mox.ReplayAll()
    module_config = application_configuration.ModuleConfiguration(
        '/appdir/app.yaml')
    config = application_configuration.BackendConfiguration(
        module_config, None, backend_entry)

    self.mox.VerifyAll()
    self.assertEqual(os.path.realpath('/appdir'), config.application_root)
    self.assertEqual('dev~app', config.application)
    self.assertEqual('app', config.application_external_name)
    self.assertEqual('dev', config.partition)
    self.assertEqual('static', config.module_name)
    self.assertEqual('1', config.major_version)
    self.assertRegexpMatches(config.version_id, r'static:1\.\d+')
    self.assertEqual('vm', config.runtime)
    self.assertEqual(beta_settings['vm_runtime'], config.effective_runtime)
    self.assertFalse(config.threadsafe)
    # Resident backends are assigned manual scaling.
    self.assertEqual(None, config.automatic_scaling)
    self.assertEqual(None, config.basic_scaling)
    self.assertEqual(appinfo.ManualScaling(instances='3'),
                     config.manual_scaling)

  def test_good_configuration_dynamic_scaling(self):
    automatic_scaling = appinfo.AutomaticScaling(min_pending_latency='1.0s',
                                                 max_pending_latency='2.0s',
                                                 min_idle_instances=1,
                                                 max_idle_instances=2)
    error_handlers = [appinfo.ErrorHandlers(file='error.html')]
    handlers = [appinfo.URLMap()]
    env_variables = appinfo.EnvironmentVariables()
    info = appinfo.AppInfoExternal(
        application='app',
        module='module1',
        version='1',
        runtime='python27',
        threadsafe=False,
        automatic_scaling=automatic_scaling,
        skip_files=r'\*.gif',
        error_handlers=error_handlers,
        handlers=handlers,
        inbound_services=['warmup'],
        env_variables=env_variables,
        )
    backend_entry = backendinfo.BackendEntry(
        name='dynamic',
        instances='3',
        options='public, dynamic',
        start='handler')

    application_configuration.ModuleConfiguration._parse_configuration(
        '/appdir/app.yaml').AndReturn((info, ['/appdir/app.yaml']))
    os.path.getmtime('/appdir/app.yaml').AndReturn(10)

    self.mox.ReplayAll()
    module_config = application_configuration.ModuleConfiguration(
        '/appdir/app.yaml')
    config = application_configuration.BackendConfiguration(
        module_config, None, backend_entry)
    self.mox.VerifyAll()

    self.assertEqual(os.path.realpath('/appdir'), config.application_root)
    self.assertEqual('dev~app', config.application)
    self.assertEqual('dynamic', config.module_name)
    self.assertEqual('1', config.major_version)
    self.assertRegexpMatches(config.version_id, r'dynamic:1\.\d+')
    self.assertEqual('python27', config.runtime)
    self.assertFalse(config.threadsafe)
    self.assertEqual(None, config.automatic_scaling)
    self.assertEqual(None, config.manual_scaling)
    self.assertEqual(appinfo.BasicScaling(max_instances='3'),
                     config.basic_scaling)
    self.assertEqual(info.GetNormalizedLibraries(),
                     config.normalized_libraries)
    self.assertEqual(r'\*.gif', config.skip_files)
    self.assertEqual(error_handlers, config.error_handlers)
    start_handler = appinfo.URLMap(url='/_ah/start',
                                   script=backend_entry.start,
                                   login='admin')
    self.assertEqual([start_handler] + handlers, config.handlers)
    self.assertEqual(['warmup'], config.inbound_services)
    self.assertEqual(env_variables, config.env_variables)

  def test_check_for_changes(self):
    backends_config = self.mox.CreateMock(
        application_configuration.BackendsConfiguration)
    config = application_configuration.BackendConfiguration(
        None, backends_config, backendinfo.BackendEntry(name='backend'))
    changes = object()
    backends_config.check_for_updates('backend').AndReturn([])
    backends_config.check_for_updates('backend').AndReturn(changes)
    minor_version = config.minor_version
    self.mox.ReplayAll()
    self.assertEqual([], config.check_for_updates())
    self.assertEqual(minor_version, config.minor_version)
    self.assertEqual(changes, config.check_for_updates())
    self.assertNotEqual(minor_version, config.minor_version)
    self.mox.VerifyAll()


class ModuleConfigurationStub(object):
  def __init__(self, application='myapp', module_name='module'):
    self.application = application
    self.module_name = module_name


class DispatchConfigurationStub(object):
  def __init__(self, dispatch):
    self.dispatch = dispatch


class TestApplicationConfiguration(unittest.TestCase):
  """Tests for application_configuration.ApplicationConfiguration."""

  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(application_configuration, 'ModuleConfiguration')
    self.mox.StubOutWithMock(application_configuration, 'BackendsConfiguration')
    self.mox.StubOutWithMock(application_configuration, 'DispatchConfiguration')
    self.tmpdir = tempfile.mkdtemp(dir=os.getenv('TEST_TMPDIR'))

  def tearDown(self):
    self.mox.UnsetStubs()
    shutil.rmtree(self.tmpdir)

  def _make_file_hierarchy(self, filenames):
    absnames = []
    for filename in filenames:
      absname = os.path.normpath(self.tmpdir + '/' + filename)
      absnames += [absname]
      dirname = os.path.dirname(absname)
      if not os.path.exists(dirname):
        os.makedirs(dirname)
      open(absname, 'w').close()
    return absnames

  def test_yaml_files(self):
    absnames = self._make_file_hierarchy(
        ['appdir/app.yaml', 'appdir/other.yaml'])

    module_config1 = ModuleConfigurationStub()
    application_configuration.ModuleConfiguration(
        absnames[0], None).AndReturn(module_config1)

    module_config2 = ModuleConfigurationStub(module_name='other')
    application_configuration.ModuleConfiguration(
        absnames[1], None).AndReturn(module_config2)

    self.mox.ReplayAll()
    config = application_configuration.ApplicationConfiguration(
        absnames)
    self.mox.VerifyAll()
    self.assertEqual('myapp', config.app_id)
    self.assertSequenceEqual([module_config1, module_config2], config.modules)

  def test_yaml_files_with_different_app_ids(self):
    absnames = self._make_file_hierarchy(
        ['appdir/app.yaml', 'appdir/other.yaml'])

    module_config1 = ModuleConfigurationStub()
    application_configuration.ModuleConfiguration(
        absnames[0], None).AndReturn(module_config1)

    module_config2 = ModuleConfigurationStub(application='other_app',
                                             module_name='other')
    application_configuration.ModuleConfiguration(
        absnames[1], None).AndReturn(module_config2)

    self.mox.ReplayAll()
    self.assertRaises(errors.InvalidAppConfigError,
                      application_configuration.ApplicationConfiguration,
                      absnames)
    self.mox.VerifyAll()

  def test_yaml_files_with_duplicate_module_names(self):
    absnames = self._make_file_hierarchy(
        ['appdir/app.yaml', 'appdir/other.yaml'])

    application_configuration.ModuleConfiguration(
        absnames[0], None).AndReturn(ModuleConfigurationStub())

    application_configuration.ModuleConfiguration(
        absnames[1], None).AndReturn(ModuleConfigurationStub())

    self.mox.ReplayAll()
    self.assertRaises(errors.InvalidAppConfigError,
                      application_configuration.ApplicationConfiguration,
                      absnames)
    self.mox.VerifyAll()

  def test_directory(self):
    absnames = self._make_file_hierarchy(['appdir/app.yaml'])

    module_config = ModuleConfigurationStub()
    application_configuration.ModuleConfiguration(
        absnames[0], None).AndReturn(module_config)

    self.mox.ReplayAll()
    config = application_configuration.ApplicationConfiguration(
        [os.path.dirname(absnames[0])])
    self.mox.VerifyAll()
    self.assertEqual('myapp', config.app_id)
    self.assertSequenceEqual([module_config], config.modules)

  def test_directory_and_module(self):
    absnames = self._make_file_hierarchy(
        ['appdir/app.yaml', 'otherdir/mymodule.yaml'])

    app_yaml_config = ModuleConfigurationStub()
    application_configuration.ModuleConfiguration(
        absnames[0], None).AndReturn(app_yaml_config)
    my_module_config = ModuleConfigurationStub(module_name='my_module')
    application_configuration.ModuleConfiguration(
        absnames[1], None).AndReturn(my_module_config)
    self.mox.ReplayAll()
    config = application_configuration.ApplicationConfiguration(
        [os.path.dirname(absnames[0]), absnames[1]])
    self.mox.VerifyAll()
    self.assertSequenceEqual(
        [app_yaml_config, my_module_config], config.modules)

  def test_directory_app_yml_only(self):
    absnames = self._make_file_hierarchy(['appdir/app.yml'])

    module_config = ModuleConfigurationStub()
    application_configuration.ModuleConfiguration(
        absnames[0], None).AndReturn(module_config)

    self.mox.ReplayAll()
    config = application_configuration.ApplicationConfiguration(
        [os.path.dirname(absnames[0])])
    self.mox.VerifyAll()
    self.assertEqual('myapp', config.app_id)
    self.assertSequenceEqual([module_config], config.modules)

  def test_directory_app_yaml_and_app_yml(self):
    absnames = self._make_file_hierarchy(['appdir/app.yaml', 'appdir/app.yml'])
    self.mox.ReplayAll()
    self.assertRaises(errors.InvalidAppConfigError,
                      application_configuration.ApplicationConfiguration,
                      [os.path.dirname(absnames[0])])
    self.mox.VerifyAll()

  def test_directory_no_app_yamls(self):
    absnames = self._make_file_hierarchy(['appdir/somethingelse.yaml'])

    self.mox.ReplayAll()
    self.assertRaises(errors.AppConfigNotFoundError,
                      application_configuration.ApplicationConfiguration,
                      [os.path.dirname(absnames[0])])
    self.mox.VerifyAll()

  def test_directory_no_app_yamls_or_web_inf(self):
    absnames = self._make_file_hierarchy(['appdir/somethingelse.yaml'])

    self.mox.ReplayAll()
    with _java_temporarily_supported():
      self.assertRaises(errors.AppConfigNotFoundError,
                        application_configuration.ApplicationConfiguration,
                        [os.path.dirname(absnames[0])])
    self.mox.VerifyAll()

  def test_app_yaml(self):
    absnames = self._make_file_hierarchy(['appdir/app.yaml'])

    module_config = ModuleConfigurationStub()
    application_configuration.ModuleConfiguration(
        absnames[0], None).AndReturn(module_config)

    self.mox.ReplayAll()
    config = application_configuration.ApplicationConfiguration(absnames)
    self.mox.VerifyAll()
    self.assertEqual('myapp', config.app_id)
    self.assertSequenceEqual([module_config], config.modules)

  def test_directory_with_backends_yaml(self):
    absnames = self._make_file_hierarchy(
        ['appdir/app.yaml', 'appdir/backends.yaml'])

    module_config = ModuleConfigurationStub()
    application_configuration.ModuleConfiguration(
        absnames[0], None).AndReturn(module_config)
    backend_config = ModuleConfigurationStub(module_name='backend')
    backends_config = self.mox.CreateMock(
        application_configuration.BackendsConfiguration)
    backends_config.get_backend_configurations().AndReturn([backend_config])
    application_configuration.BackendsConfiguration(
        absnames[0], absnames[1], None).AndReturn(backends_config)

    self.mox.ReplayAll()
    config = application_configuration.ApplicationConfiguration(
        [os.path.dirname(absnames[0])])
    self.mox.VerifyAll()
    self.assertEqual('myapp', config.app_id)
    self.assertSequenceEqual([module_config, backend_config], config.modules)

  def test_yaml_files_with_backends_yaml(self):
    absnames = self._make_file_hierarchy(
        ['appdir/app.yaml', 'appdir/backends.yaml'])

    module_config = ModuleConfigurationStub()
    application_configuration.ModuleConfiguration(
        absnames[0], None).AndReturn(module_config)

    backend_config = ModuleConfigurationStub(module_name='backend')
    backends_config = self.mox.CreateMock(
        application_configuration.BackendsConfiguration)
    backends_config.get_backend_configurations().AndReturn([backend_config])
    application_configuration.BackendsConfiguration(
        absnames[0], absnames[1], None).AndReturn(backends_config)

    self.mox.ReplayAll()
    config = application_configuration.ApplicationConfiguration(absnames)
    self.mox.VerifyAll()
    self.assertEqual('myapp', config.app_id)
    self.assertSequenceEqual([module_config, backend_config], config.modules)

  def test_yaml_files_with_backends_and_dispatch_yaml(self):
    absnames = self._make_file_hierarchy(
        ['appdir/app.yaml', 'appdir/backends.yaml', 'appdir/dispatch.yaml'])

    module_config = ModuleConfigurationStub(module_name='default')
    application_configuration.ModuleConfiguration(
        absnames[0], None).AndReturn(module_config)

    backend_config = ModuleConfigurationStub(module_name='backend')
    backends_config = self.mox.CreateMock(
        application_configuration.BackendsConfiguration)
    backends_config.get_backend_configurations().AndReturn([backend_config])
    application_configuration.BackendsConfiguration(
        absnames[0], absnames[1], None).AndReturn(backends_config)
    dispatch_config = DispatchConfigurationStub(
        [(None, 'default'), (None, 'backend')])
    application_configuration.DispatchConfiguration(
        absnames[2]).AndReturn(dispatch_config)

    self.mox.ReplayAll()
    config = application_configuration.ApplicationConfiguration(absnames)
    self.mox.VerifyAll()
    self.assertEqual('myapp', config.app_id)
    self.assertSequenceEqual([module_config, backend_config], config.modules)
    self.assertEqual(dispatch_config, config.dispatch)

  def test_yaml_files_dispatch_yaml_and_no_default_module(self):
    absnames = self._make_file_hierarchy(
        ['appdir/app.yaml', 'appdir/dispatch.yaml'])

    module_config = ModuleConfigurationStub(module_name='not-default')
    application_configuration.ModuleConfiguration(
        absnames[0], None).AndReturn(module_config)

    dispatch_config = DispatchConfigurationStub([(None, 'default')])
    application_configuration.DispatchConfiguration(
        absnames[1]).AndReturn(dispatch_config)

    self.mox.ReplayAll()
    self.assertRaises(errors.InvalidAppConfigError,
                      application_configuration.ApplicationConfiguration,
                      absnames)
    self.mox.VerifyAll()

  def test_yaml_files_dispatch_yaml_and_missing_dispatch_target(self):
    absnames = self._make_file_hierarchy(
        ['appdir/app.yaml', 'appdir/dispatch.yaml'])

    module_config = ModuleConfigurationStub(module_name='default')
    application_configuration.ModuleConfiguration(
        absnames[0], None).AndReturn(module_config)

    dispatch_config = DispatchConfigurationStub(
        [(None, 'default'), (None, 'fake-module')])
    application_configuration.DispatchConfiguration(
        absnames[1]).AndReturn(dispatch_config)

    self.mox.ReplayAll()
    self.assertRaises(errors.InvalidAppConfigError,
                      application_configuration.ApplicationConfiguration,
                      absnames)
    self.mox.VerifyAll()

  def test_directory_web_inf(self):
    absnames = self._make_file_hierarchy(
        ['appdir/WEB-INF/appengine-web.xml', 'appdir/WEB-INF/web.xml'])
    appdir = os.path.dirname(os.path.dirname(absnames[0]))

    module_config = ModuleConfigurationStub(module_name='default')
    application_configuration.ModuleConfiguration(
        absnames[0], None).AndReturn(module_config)

    self.mox.ReplayAll()
    with _java_temporarily_supported():
      config = application_configuration.ApplicationConfiguration([appdir])
    self.mox.VerifyAll()

    self.assertEqual('myapp', config.app_id)
    self.assertSequenceEqual([module_config], config.modules)

  def test_directory_web_inf_missing_appengine_xml(self):
    absnames = self._make_file_hierarchy(['appdir/WEB-INF/web.xml'])
    appdir = os.path.dirname(os.path.dirname(absnames[0]))

    self.mox.ReplayAll()
    with _java_temporarily_supported():
      self.assertRaises(errors.AppConfigNotFoundError,
                        application_configuration.ApplicationConfiguration,
                        [appdir])
    self.mox.VerifyAll()

  def test_directory_web_inf_missing_web_xml(self):
    absnames = self._make_file_hierarchy(['appdir/WEB-INF/appengine-web.xml'])
    appdir = os.path.dirname(os.path.dirname(absnames[0]))

    self.mox.ReplayAll()
    with _java_temporarily_supported():
      self.assertRaises(errors.AppConfigNotFoundError,
                        application_configuration.ApplicationConfiguration,
                        [appdir])
    self.mox.VerifyAll()

  def test_config_with_yaml_and_xml(self):
    absnames = self._make_file_hierarchy(
        ['module1/app.yaml', 'module1/dispatch.yaml',
         'module2/WEB-INF/appengine-web.xml', 'module2/WEB-INF/web.xml'])
    app_yaml = absnames[0]
    dispatch_yaml = absnames[1]
    appengine_web_xml = absnames[2]
    module2 = os.path.dirname(os.path.dirname(appengine_web_xml))

    module1_config = ModuleConfigurationStub(module_name='default')
    application_configuration.ModuleConfiguration(
        app_yaml, None).AndReturn(module1_config)
    dispatch_config = DispatchConfigurationStub(
        [(None, 'default'), (None, 'module2')])
    application_configuration.DispatchConfiguration(
        dispatch_yaml).AndReturn(dispatch_config)
    module2_config = ModuleConfigurationStub(module_name='module2')
    application_configuration.ModuleConfiguration(
        appengine_web_xml, None).AndReturn(module2_config)

    self.mox.ReplayAll()
    with _java_temporarily_supported():
      config = application_configuration.ApplicationConfiguration(
          [app_yaml, dispatch_yaml, module2])
    self.mox.VerifyAll()

    self.assertEqual('myapp', config.app_id)
    self.assertSequenceEqual(
        [module1_config, module2_config], config.modules)
    self.assertEqual(dispatch_config, config.dispatch)


class GenerateVersionIdTest(unittest.TestCase):
  """Tests the GenerateVersionId function."""

  def test_generate_version_id(self):
    datetime_getter = lambda: datetime.datetime(2014, 9, 18, 17, 31, 45, 92949)
    generated_version = application_configuration.generate_version_id(
        datetime_getter)
    self.assertEqual(generated_version, '20140918t173145')


if __name__ == '__main__':
  unittest.main()
