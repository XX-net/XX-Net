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
"""Tests for google.appengine.tools.devappserver2.dispatcher."""

import logging
import socket
import unittest

import google

import mox

from google.appengine.api import appinfo
from google.appengine.api import dispatchinfo
from google.appengine.api import request_info
from google.appengine.tools.devappserver2 import api_server
from google.appengine.tools.devappserver2 import dispatcher
from google.appengine.tools.devappserver2 import module
from google.appengine.tools.devappserver2 import scheduled_executor

# This file uses pep8 naming.
# pylint: disable=invalid-name


class ApplicationConfigurationStub(object):

  def __init__(self, modules):
    self.modules = modules
    self.dispatch = None


class ModuleConfigurationStub(object):

  def __init__(self, application, module_name, version, manual_scaling):
    self.application_root = '/'
    self.application = application
    self.application_external_name = 'app'
    self.module_name = module_name
    self.major_version = version
    self.version_id = '%s:%s.%s' % (module_name, version, '12345')
    self.runtime = 'python27'
    self.effective_runtime = self.runtime
    self.threadsafe = False
    self.handlers = []
    self.skip_files = []
    self.normalized_libraries = []
    self.env_variables = []
    if manual_scaling:
      self.automatic_scaling = appinfo.AutomaticScaling()
      self.manual_scaling = None
    else:
      self.automatic_scaling = None
      self.manual_scaling = appinfo.ManualScaling(instances=1)
    self.inbound_services = None

  def add_change_callback(self, fn):
    pass


class DispatchConfigurationStub(object):

  def __init__(self):
    self.dispatch = []


MODULE_CONFIGURATIONS = [
    ModuleConfigurationStub(application='app',
                            module_name='default',
                            version='version',
                            manual_scaling=False),
    ModuleConfigurationStub(application='app',
                            module_name='other',
                            version='version2',
                            manual_scaling=True),
    ModuleConfigurationStub(application='app',
                            module_name='another',
                            version='version3',
                            manual_scaling=True),
    ]


class AutoScalingModuleFacade(module.AutoScalingModule):

  def __init__(self,
               module_configuration,
               host='fakehost',
               balanced_port=0):
    super(AutoScalingModuleFacade, self).__init__(
        module_configuration=module_configuration,
        host=host,
        balanced_port=balanced_port,
        api_host='localhost',
        api_port=8080,
        auth_domain='gmail.com',
        runtime_stderr_loglevel=1,
        php_config=None,
        python_config=None,
        java_config=None,
        custom_config=None,
        cloud_sql_config=None,
        vm_config=None,
        default_version_port=8080,
        port_registry=None,
        request_data=None,
        dispatcher=None,
        max_instances=None,
        use_mtime_file_watcher=False,
        automatic_restarts=True,
        allow_skipped_files=False,
        threadsafe_override=None)

  def start(self):
    pass

  def quit(self):
    pass

  @property
  def balanced_address(self):
    return '%s:%s' % (self._host, self._balanced_port)

  @property
  def balanced_port(self):
    return self._balanced_port


class ManualScalingModuleFacade(module.ManualScalingModule):

  def __init__(self,
               module_configuration,
               host='fakehost',
               balanced_port=0):
    super(ManualScalingModuleFacade, self).__init__(
        module_configuration=module_configuration,
        host=host,
        balanced_port=balanced_port,
        api_host='localhost',
        api_port=8080,
        auth_domain='gmail.com',
        runtime_stderr_loglevel=1,
        php_config=None,
        python_config=None,
        java_config=None,
        custom_config=None,
        cloud_sql_config=None,
        vm_config=None,
        default_version_port=8080,
        port_registry=None,
        request_data=None,
        dispatcher=None,
        max_instances=None,
        use_mtime_file_watcher=False,
        automatic_restarts=True,
        allow_skipped_files=False,
        threadsafe_override=None)

  def start(self):
    pass

  def quit(self):
    pass

  @property
  def balanced_address(self):
    return '%s:%s' % (self._host, self._balanced_port)

  @property
  def balanced_port(self):
    return self._balanced_port

  def get_instance_address(self, instance):
    if instance == 'invalid':
      raise request_info.InvalidInstanceIdError()
    return '%s:%s' % (self._host, int(instance) + 1000)


def _make_dispatcher(app_config):
  """Make a new dispatcher with the given ApplicationConfigurationStub."""
  return dispatcher.Dispatcher(
      app_config,
      'localhost',
      1,
      'gmail.com',
      1,
      php_config=None,
      python_config=None,
      java_config=None,
      custom_config=None,
      cloud_sql_config=None,
      vm_config=None,
      module_to_max_instances={},
      use_mtime_file_watcher=False,
      automatic_restart=True,
      allow_skipped_files=False,
      module_to_threadsafe_override={},
      external_port=None)


class DispatcherQuitWithoutStartTest(unittest.TestCase):

  def test_quit_without_start(self):
    """Test that calling quit on a dispatcher without calling start is safe."""
    app_config = ApplicationConfigurationStub(MODULE_CONFIGURATIONS)
    unstarted_dispatcher = _make_dispatcher(app_config)
    unstarted_dispatcher.quit()


class DispatcherTest(unittest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()
    api_server.test_setup_stubs()
    self.dispatch_config = DispatchConfigurationStub()
    app_config = ApplicationConfigurationStub(MODULE_CONFIGURATIONS)
    self.dispatcher = _make_dispatcher(app_config)
    self.module1 = AutoScalingModuleFacade(app_config.modules[0],
                                           balanced_port=1,
                                           host='localhost')
    self.module2 = ManualScalingModuleFacade(app_config.modules[0],
                                             balanced_port=2,
                                             host='localhost')
    self.module3 = ManualScalingModuleFacade(app_config.modules[0],
                                             balanced_port=3,
                                             host='0.0.0.0')

    self.mox.StubOutWithMock(self.dispatcher, '_create_module')
    self.dispatcher._create_module(app_config.modules[0], 1).AndReturn(
        (self.module1, 2))
    self.dispatcher._create_module(app_config.modules[1], 2).AndReturn(
        (self.module2, 3))
    self.dispatcher._create_module(app_config.modules[2], 3).AndReturn(
        (self.module3, 4))
    self.mox.ReplayAll()
    self.dispatcher.start('localhost', 12345, object())
    app_config.dispatch = self.dispatch_config
    self.mox.VerifyAll()
    self.mox.StubOutWithMock(module.Module, 'build_request_environ')

  def tearDown(self):
    self.dispatcher.quit()
    self.mox.UnsetStubs()

  def test_get_module_names(self):
    self.assertItemsEqual(['default', 'other', 'another'],
                          self.dispatcher.get_module_names())

  def test_get_hostname(self):
    self.assertEqual('localhost:1',
                     self.dispatcher.get_hostname('default', 'version'))
    self.assertEqual('localhost:2',
                     self.dispatcher.get_hostname('other', 'version2'))
    self.assertRaises(request_info.VersionDoesNotExistError,
                      self.dispatcher.get_hostname, 'default', 'fake')
    self.assertRaises(request_info.NotSupportedWithAutoScalingError,
                      self.dispatcher.get_hostname, 'default', 'version', '0')
    self.assertEqual('localhost:1000',
                     self.dispatcher.get_hostname('other', 'version2', '0'))
    self.assertRaises(request_info.InvalidInstanceIdError,
                      self.dispatcher.get_hostname, 'other', 'version2',
                      'invalid')
    self.assertRaises(request_info.ModuleDoesNotExistError,
                      self.dispatcher.get_hostname,
                      'nomodule',
                      'version2',
                      None)
    self.assertEqual('%s:3' % socket.gethostname(),
                     self.dispatcher.get_hostname('another', 'version3'))
    self.assertEqual(
        '%s:1000' % socket.gethostname(),
        self.dispatcher.get_hostname('another', 'version3', '0'))

  def test_get_module_by_name(self):
    self.assertEqual(self.module1,
                     self.dispatcher.get_module_by_name('default'))
    self.assertEqual(self.module2,
                     self.dispatcher.get_module_by_name('other'))
    self.assertRaises(request_info.ModuleDoesNotExistError,
                      self.dispatcher.get_module_by_name, 'fake')

  def test_get_versions(self):
    self.assertEqual(['version'], self.dispatcher.get_versions('default'))
    self.assertEqual(['version2'], self.dispatcher.get_versions('other'))
    self.assertRaises(request_info.ModuleDoesNotExistError,
                      self.dispatcher.get_versions, 'fake')

  def test_get_default_version(self):
    self.assertEqual('version', self.dispatcher.get_default_version('default'))
    self.assertEqual('version2', self.dispatcher.get_default_version('other'))
    self.assertRaises(request_info.ModuleDoesNotExistError,
                      self.dispatcher.get_default_version, 'fake')

  def test_add_event(self):
    self.mox.StubOutWithMock(scheduled_executor.ScheduledExecutor, 'add_event')
    runnable = object()
    scheduled_executor.ScheduledExecutor.add_event(runnable, 123, ('foo',
                                                                   'bar'))
    scheduled_executor.ScheduledExecutor.add_event(runnable, 124, None)
    self.mox.ReplayAll()
    self.dispatcher.add_event(runnable, 123, 'foo', 'bar')
    self.dispatcher.add_event(runnable, 124)
    self.mox.VerifyAll()

  def test_update_event(self):
    self.mox.StubOutWithMock(scheduled_executor.ScheduledExecutor,
                             'update_event')
    scheduled_executor.ScheduledExecutor.update_event(123, ('foo', 'bar'))
    self.mox.ReplayAll()
    self.dispatcher.update_event(123, 'foo', 'bar')
    self.mox.VerifyAll()

  def test_add_async_request(self):
    dummy_environ = object()
    self.mox.StubOutWithMock(dispatcher._THREAD_POOL, 'submit')
    self.dispatcher._module_name_to_module['default'].build_request_environ(
        'PUT', '/foo?bar=baz', [('Header', 'Value'), ('Other', 'Values')],
        'body', '1.2.3.4', 1).AndReturn(
            dummy_environ)
    dispatcher._THREAD_POOL.submit(
        self.dispatcher._handle_request, dummy_environ, mox.IgnoreArg(),
        self.dispatcher._module_name_to_module['default'],
        None, catch_and_log_exceptions=True)
    self.mox.ReplayAll()
    self.dispatcher.add_async_request(
        'PUT', '/foo?bar=baz', [('Header', 'Value'), ('Other', 'Values')],
        'body', '1.2.3.4')
    self.mox.VerifyAll()

  def test_add_async_request_specific_module(self):
    dummy_environ = object()
    self.mox.StubOutWithMock(dispatcher._THREAD_POOL, 'submit')
    self.dispatcher._module_name_to_module['other'].build_request_environ(
        'PUT', '/foo?bar=baz', [('Header', 'Value'), ('Other', 'Values')],
        'body', '1.2.3.4', 2).AndReturn(
            dummy_environ)
    dispatcher._THREAD_POOL.submit(
        self.dispatcher._handle_request, dummy_environ, mox.IgnoreArg(),
        self.dispatcher._module_name_to_module['other'],
        None, catch_and_log_exceptions=True)
    self.mox.ReplayAll()
    self.dispatcher.add_async_request(
        'PUT', '/foo?bar=baz', [('Header', 'Value'), ('Other', 'Values')],
        'body', '1.2.3.4', module_name='other')
    self.mox.VerifyAll()

  def test_add_async_request_soft_routing(self):
    """Tests add_async_request with soft routing."""
    dummy_environ = object()
    self.mox.StubOutWithMock(dispatcher._THREAD_POOL, 'submit')
    self.dispatcher._module_name_to_module['default'].build_request_environ(
        'PUT', '/foo?bar=baz', [('Header', 'Value'), ('Other', 'Values')],
        'body', '1.2.3.4', 1).AndReturn(
            dummy_environ)
    dispatcher._THREAD_POOL.submit(
        self.dispatcher._handle_request, dummy_environ, mox.IgnoreArg(),
        self.dispatcher._module_name_to_module['default'],
        None, catch_and_log_exceptions=True)
    self.mox.ReplayAll()
    self.dispatcher.add_async_request(
        'PUT', '/foo?bar=baz', [('Header', 'Value'), ('Other', 'Values')],
        'body', '1.2.3.4', module_name='nomodule')
    self.mox.VerifyAll()

  def test_add_request(self):
    dummy_environ = object()
    self.mox.StubOutWithMock(self.dispatcher, '_resolve_target')
    self.mox.StubOutWithMock(self.dispatcher, '_handle_request')
    self.dispatcher._resolve_target(None, '/foo').AndReturn(
        (self.dispatcher._module_name_to_module['default'], None))
    self.dispatcher._module_name_to_module['default'].build_request_environ(
        'PUT', '/foo?bar=baz', [('Header', 'Value'), ('Other', 'Values')],
        'body', '1.2.3.4', 1, fake_login=True).AndReturn(
            dummy_environ)
    self.dispatcher._handle_request(
        dummy_environ, mox.IgnoreArg(),
        self.dispatcher._module_name_to_module['default'],
        None).AndReturn(['Hello World'])
    self.mox.ReplayAll()
    response = self.dispatcher.add_request(
        'PUT', '/foo?bar=baz', [('Header', 'Value'), ('Other', 'Values')],
        'body', '1.2.3.4', fake_login=True)
    self.mox.VerifyAll()
    self.assertEqual('Hello World', response.content)

  def test_add_request_soft_routing(self):
    """Tests soft routing to the default module."""
    dummy_environ = object()
    self.mox.StubOutWithMock(self.dispatcher, '_handle_request')
    self.dispatcher._module_name_to_module['default'].build_request_environ(
        'PUT', '/foo?bar=baz', [('Header', 'Value'), ('Other', 'Values')],
        'body', '1.2.3.4', 1, fake_login=True).AndReturn(
            dummy_environ)
    self.dispatcher._handle_request(
        dummy_environ, mox.IgnoreArg(),
        self.dispatcher._module_name_to_module['default'],
        None).AndReturn(['Hello World'])
    self.mox.ReplayAll()
    response = self.dispatcher.add_request(
        'PUT', '/foo?bar=baz', [('Header', 'Value'), ('Other', 'Values')],
        'body', '1.2.3.4', fake_login=True, module_name='nomodule')
    self.mox.VerifyAll()
    self.assertEqual('Hello World', response.content)

  def test_add_request_merged_response(self):
    """Tests handlers which return side-effcting generators."""
    dummy_environ = object()
    self.mox.StubOutWithMock(self.dispatcher, '_handle_request')
    self.dispatcher._module_name_to_module['default'].build_request_environ(
        'PUT', '/foo?bar=baz', [('Header', 'Value'), ('Other', 'Values')],
        'body', '1.2.3.4', 1, fake_login=True).AndReturn(
            dummy_environ)

    start_response_ref = []
    def capture_start_response(unused_env, start_response, unused_module,
                               unused_inst):
      start_response_ref.append(start_response)

    def side_effecting_handler():
      start_response_ref[0]('200 OK', [('Content-Type', 'text/plain')])
      yield 'Hello World'

    mock = self.dispatcher._handle_request(
        dummy_environ, mox.IgnoreArg(),
        self.dispatcher._module_name_to_module['default'],
        None)
    mock = mock.WithSideEffects(capture_start_response)
    mock = mock.AndReturn(side_effecting_handler())

    self.mox.ReplayAll()
    response = self.dispatcher.add_request(
        'PUT', '/foo?bar=baz', [('Header', 'Value'), ('Other', 'Values')],
        'body', '1.2.3.4', fake_login=True, module_name='nomodule')
    self.mox.VerifyAll()
    self.assertEqual('200 OK', response.status)
    self.assertEqual([('Content-Type', 'text/plain')], response.headers)
    self.assertEqual('Hello World', response.content)

  def test_handle_request(self):
    start_response = object()
    servr = self.dispatcher._module_name_to_module['other']
    self.mox.StubOutWithMock(servr, '_handle_request')
    servr._handle_request({'foo': 'bar'}, start_response, inst=None,
                          request_type=3).AndReturn(['body'])
    self.mox.ReplayAll()
    self.dispatcher._handle_request({'foo': 'bar'}, start_response, servr, None,
                                    request_type=3)
    self.mox.VerifyAll()

  def test_handle_request_reraise_exception(self):
    start_response = object()
    servr = self.dispatcher._module_name_to_module['other']
    self.mox.StubOutWithMock(servr, '_handle_request')
    servr._handle_request({'foo': 'bar'}, start_response).AndRaise(Exception)
    self.mox.ReplayAll()
    self.assertRaises(Exception, self.dispatcher._handle_request,
                      {'foo': 'bar'}, start_response, servr, None)
    self.mox.VerifyAll()

  def test_handle_request_log_exception(self):
    start_response = object()
    servr = self.dispatcher._module_name_to_module['other']
    self.mox.StubOutWithMock(servr, '_handle_request')
    self.mox.StubOutWithMock(logging, 'exception')
    servr._handle_request({'foo': 'bar'}, start_response).AndRaise(Exception)
    logging.exception('Internal error while handling request.')
    self.mox.ReplayAll()
    self.dispatcher._handle_request({'foo': 'bar'}, start_response, servr, None,
                                    catch_and_log_exceptions=True)
    self.mox.VerifyAll()

  def test_call(self):
    self.mox.StubOutWithMock(self.dispatcher, '_module_for_request')
    self.mox.StubOutWithMock(self.dispatcher, '_handle_request')
    servr = object()
    environ = {'PATH_INFO': '/foo', 'QUERY_STRING': 'bar=baz'}
    start_response = object()
    self.dispatcher._module_for_request('/foo').AndReturn(servr)
    self.dispatcher._handle_request(environ, start_response, servr)
    self.mox.ReplayAll()
    self.dispatcher(environ, start_response)
    self.mox.VerifyAll()

  def test_module_for_request(self):

    class FakeDict(dict):
      def __contains__(self, key):
        return True

      def __getitem__(self, key):
        return key

    self.dispatcher._module_name_to_module = FakeDict()
    self.dispatch_config.dispatch = [
        (dispatchinfo.ParsedURL('*/path'), '1'),
        (dispatchinfo.ParsedURL('*/other_path/*'), '2'),
        (dispatchinfo.ParsedURL('*/other_path/'), '3'),
        (dispatchinfo.ParsedURL('*/other_path'), '3'),
        ]
    self.assertEqual('1', self.dispatcher._module_for_request('/path'))
    self.assertEqual('2', self.dispatcher._module_for_request('/other_path/'))
    self.assertEqual('2', self.dispatcher._module_for_request('/other_path/a'))
    self.assertEqual('3',
                     self.dispatcher._module_for_request('/other_path'))
    self.assertEqual('default',
                     self.dispatcher._module_for_request('/undispatched'))

  def test_should_use_dispatch_config(self):
    """Tests the _should_use_dispatch_config method."""
    self.assertTrue(self.dispatcher._should_use_dispatch_config('/'))
    self.assertTrue(self.dispatcher._should_use_dispatch_config('/foo/'))
    self.assertTrue(self.dispatcher._should_use_dispatch_config(
        '/_ah/queue/deferred'))
    self.assertTrue(self.dispatcher._should_use_dispatch_config(
        '/_ah/queue/deferred/blah'))

    self.assertFalse(self.dispatcher._should_use_dispatch_config('/_ah/'))
    self.assertFalse(self.dispatcher._should_use_dispatch_config('/_ah/foo/'))
    self.assertFalse(self.dispatcher._should_use_dispatch_config(
        '/_ah/foo/bar/'))
    self.assertFalse(self.dispatcher._should_use_dispatch_config(
        '/_ah/queue/'))

  def test_resolve_target(self):
    servr = object()
    inst = object()
    self.dispatcher._port_registry.add(8080, servr, inst)
    self.mox.StubOutWithMock(self.dispatcher, '_module_for_request')
    self.mox.ReplayAll()
    self.assertEqual((servr, inst),
                     self.dispatcher._resolve_target('localhost:8080', '/foo'))
    self.mox.VerifyAll()

  def test_resolve_target_no_hostname(self):
    self.mox.StubOutWithMock(self.dispatcher, '_module_for_request')
    servr = object()
    self.dispatcher._module_for_request('/foo').AndReturn(servr)
    self.mox.ReplayAll()
    self.assertEqual((servr, None),
                     self.dispatcher._resolve_target(None, '/foo'))
    self.mox.VerifyAll()

  def test_resolve_target_dispatcher_port(self):
    self.dispatcher._port_registry.add(80, None, None)
    self.mox.StubOutWithMock(self.dispatcher, '_module_for_request')
    servr = object()
    self.dispatcher._module_for_request('/foo').AndReturn(servr)
    self.mox.ReplayAll()
    self.assertEqual((servr, None),
                     self.dispatcher._resolve_target('localhost', '/foo'))
    self.mox.VerifyAll()

  def test_resolve_target_unknown_port(self):
    self.mox.StubOutWithMock(self.dispatcher, '_module_for_request')
    self.mox.ReplayAll()
    self.assertRaises(request_info.ModuleDoesNotExistError,
                      self.dispatcher._resolve_target, 'localhost:100', '/foo')
    self.mox.VerifyAll()

  def test_resolve_target_module_prefix(self):
    self.mox.StubOutWithMock(self.dispatcher, '_module_for_request')
    self.mox.StubOutWithMock(self.dispatcher, '_get_module_with_soft_routing')
    servr = object()
    self.dispatcher._get_module_with_soft_routing('backend', None).AndReturn(
        servr)
    self.mox.ReplayAll()
    self.assertEqual((servr, None),
                     self.dispatcher._resolve_target('backend.localhost:1',
                                                     '/foo'))
    self.mox.VerifyAll()

  def test_resolve_target_instance_module_prefix(self):
    self.mox.StubOutWithMock(self.dispatcher, '_module_for_request')
    self.mox.StubOutWithMock(self.dispatcher, '_get_module_with_soft_routing')
    servr = object()
    self.dispatcher._get_module_with_soft_routing('backend', None).AndReturn(
        servr)
    self.mox.ReplayAll()
    self.assertEqual((servr, None),
                     self.dispatcher._resolve_target('1.backend.localhost:1',
                                                     '/foo'))
    self.mox.VerifyAll()

  def test_resolve_target_instance_version_module_prefix(self):
    self.mox.StubOutWithMock(self.dispatcher, '_module_for_request')
    self.mox.StubOutWithMock(self.dispatcher, '_get_module_with_soft_routing')
    servr = object()
    self.dispatcher._get_module_with_soft_routing('backend', None).AndReturn(
        servr)
    self.mox.ReplayAll()
    self.assertEqual((servr, None),
                     self.dispatcher._resolve_target('1.v1.backend.localhost:1',
                                                     '/foo'))
    self.mox.VerifyAll()

  def test_get_module_no_modules(self):
    """Tests the _get_module method with no modules."""
    self.dispatcher._module_name_to_module = {}
    self.assertRaises(request_info.ModuleDoesNotExistError,
                      self.dispatcher._get_module,
                      None,
                      None)

  def test_get_module_default_module(self):
    """Tests the _get_module method with a default module."""
    # Test default mopdule is returned for an empty query.
    self.dispatcher._module_name_to_module = {'default': self.module1}
    self.assertEqual(self.dispatcher._get_module(None, None), self.module1)

    self.dispatcher._module_name_to_module['nondefault'] = self.module2
    self.assertEqual(self.dispatcher._get_module(None, None), self.module1)

    self.dispatcher._module_name_to_module = {'default': self.module1}
    self.assertRaises(request_info.ModuleDoesNotExistError,
                      self.dispatcher._get_module,
                      'nondefault',
                      None)
    # Test version handling.
    self.dispatcher._module_configurations['default'] = MODULE_CONFIGURATIONS[0]
    self.assertEqual(self.dispatcher._get_module('default', 'version'),
                     self.module1)
    self.assertRaises(request_info.VersionDoesNotExistError,
                      self.dispatcher._get_module,
                      'default',
                      'version2')

  def test_get_module_non_default(self):
    """Tests the _get_module method with a non-default module."""
    self.dispatcher._module_name_to_module = {'default': self.module1,
                                              'other': self.module2}
    self.assertEqual(self.dispatcher._get_module('other', None),
                     self.module2)
    # Test version handling.
    self.dispatcher._module_configurations['default'] = MODULE_CONFIGURATIONS[0]
    self.dispatcher._module_configurations['other'] = MODULE_CONFIGURATIONS[1]
    self.assertEqual(self.dispatcher._get_module('other', 'version2'),
                     self.module2)
    self.assertRaises(request_info.VersionDoesNotExistError,
                      self.dispatcher._get_module,
                      'other',
                      'version3')

  def test_get_module_no_default(self):
    """Tests the _get_module method with no default module."""
    self.dispatcher._module_name_to_module = {'other': self.module1}
    self.assertEqual(self.dispatcher._get_module('other', None),
                     self.module1)
    self.assertRaises(request_info.ModuleDoesNotExistError,
                      self.dispatcher._get_module,
                      None,
                      None)
    # Test version handling.
    self.dispatcher._module_configurations['other'] = MODULE_CONFIGURATIONS[0]
    self.assertEqual(self.dispatcher._get_module('other', 'version'),
                     self.module1)
    self.assertRaises(request_info.VersionDoesNotExistError,
                      self.dispatcher._get_module,
                      'other',
                      'version2')

  def test_get_module_soft_routing_no_modules(self):
    """Tests the _get_module_soft_routing method with no modules."""
    self.dispatcher._module_name_to_module = {}
    self.assertRaises(request_info.ModuleDoesNotExistError,
                      self.dispatcher._get_module_with_soft_routing,
                      None,
                      None)

  def test_get_module_soft_routing_default_module(self):
    """Tests the _get_module_soft_routing method with a default module."""
    # Test default mopdule is returned for an empty query.
    self.dispatcher._module_name_to_module = {'default': self.module1}
    self.assertEqual(self.dispatcher._get_module_with_soft_routing(None, None),
                     self.module1)

    self.dispatcher._module_name_to_module['other'] = self.module2
    self.assertEqual(self.dispatcher._get_module_with_soft_routing(None, None),
                     self.module1)

    # Test soft-routing. Querying for a non-existing module should return
    # default.
    self.dispatcher._module_name_to_module = {'default': self.module1}
    self.assertEqual(self.dispatcher._get_module_with_soft_routing('other',
                                                                   None),
                     self.module1)

    # Test version handling.
    self.dispatcher._module_configurations['default'] = MODULE_CONFIGURATIONS[0]
    self.assertEqual(self.dispatcher._get_module_with_soft_routing('other',
                                                                   'version'),
                     self.module1)
    self.assertEqual(self.dispatcher._get_module_with_soft_routing('default',
                                                                   'version'),
                     self.module1)
    self.assertRaises(request_info.VersionDoesNotExistError,
                      self.dispatcher._get_module_with_soft_routing,
                      'default',
                      'version2')
    self.assertRaises(request_info.VersionDoesNotExistError,
                      self.dispatcher._get_module_with_soft_routing,
                      'other',
                      'version2')

  def test_get_module_soft_routing_non_default(self):
    """Tests the _get_module_soft_routing method with a non-default module."""
    self.dispatcher._module_name_to_module = {'default': self.module1,
                                              'other': self.module2}
    self.assertEqual(self.dispatcher._get_module_with_soft_routing('other',
                                                                   None),
                     self.module2)
    # Test version handling.
    self.dispatcher._module_configurations['default'] = MODULE_CONFIGURATIONS[0]
    self.dispatcher._module_configurations['other'] = MODULE_CONFIGURATIONS[1]
    self.assertEqual(self.dispatcher._get_module_with_soft_routing('other',
                                                                   'version2'),
                     self.module2)
    self.assertRaises(request_info.VersionDoesNotExistError,
                      self.dispatcher._get_module_with_soft_routing,
                      'other',
                      'version3')

  def test_get_module_soft_routing_no_default(self):
    """Tests the _get_module_soft_routing method with no default module."""
    self.dispatcher._module_name_to_module = {'other': self.module1}
    self.assertEqual(self.dispatcher._get_module_with_soft_routing('other',
                                                                   None),
                     self.module1)
    self.assertEqual(self.dispatcher._get_module_with_soft_routing('other',
                                                                   None),
                     self.module1)
    # Test version handling.
    self.dispatcher._module_configurations['other'] = MODULE_CONFIGURATIONS[0]
    self.assertEqual(self.dispatcher._get_module_with_soft_routing('other',
                                                                   'version'),
                     self.module1)
    self.assertRaises(request_info.VersionDoesNotExistError,
                      self.dispatcher._get_module_with_soft_routing,
                      'other',
                      'version2')

if __name__ == '__main__':
  unittest.main()
