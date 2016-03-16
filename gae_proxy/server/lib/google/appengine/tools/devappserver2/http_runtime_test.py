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
"""Tests for google.appengine.tools.devappserver2.http_runtime."""



import base64
import os
import re
import shutil
import subprocess
import tempfile
import time
import unittest

import google

import mox
import portpicker

from google.appengine.api import appinfo
from google.appengine.tools.devappserver2 import http_proxy
from google.appengine.tools.devappserver2 import http_runtime
from google.appengine.tools.devappserver2 import instance
from google.appengine.tools.devappserver2 import login
from google.appengine.tools.devappserver2 import runtime_config_pb2
from google.appengine.tools.devappserver2 import safe_subprocess
from google.appengine.tools.devappserver2 import wsgi_test_utils


class MockMessage(object):
  def __init__(self, headers):
    self.headers = headers

  def __iter__(self):
    return iter(set(name for name, _ in self.headers))

  def getheaders(self, name):
    return [value for header_name, value in self.headers if header_name == name]


class FakeHttpResponse(object):
  def __init__(self, status, reason, headers, body):
    self.body = body
    self.has_read = False
    self.partial_read_error = None
    self.status = status
    self.reason = reason
    self.headers = headers
    self.msg = MockMessage(headers)

  def read(self, amt=None):
    if not self.has_read:
      self.has_read = True
      return self.body
    elif self.partial_read_error:
      raise self.partial_read_error
    else:
      return ''

  def getheaders(self):
    return self.headers


# We use a fake Tee to avoid the complexity of a real Tee's thread racing with
# the mocking framework and possibly surviving (and calling stderr.readline())
# after a test case completes.
class FakeTee(object):
  def __init__(self, buf):
    self.buf = buf

  def get_buf(self):
    return self.buf

  def join(self, unused_timeout):
    pass


class ModuleConfigurationStub(object):
  def __init__(self, application_root='/tmp', error_handlers=None):
    self.application_root = application_root
    self.error_handlers = error_handlers


class HttpRuntimeProxyTest(wsgi_test_utils.WSGITestCase):
  def setUp(self):
    self.mox = mox.Mox()
    self.tmpdir = tempfile.mkdtemp()
    module_configuration = ModuleConfigurationStub(
        application_root=self.tmpdir,
        error_handlers=[
            appinfo.ErrorHandlers(error_code='over_quota', file='foo.html'),
            appinfo.ErrorHandlers(error_code='default', file='error.html'),
            ])
    self.runtime_config = runtime_config_pb2.Config()
    self.runtime_config.app_id = 'app'
    self.runtime_config.version_id = 'version'
    self.runtime_config.api_port = 12345
    self.runtime_config.application_root = self.tmpdir
    self.runtime_config.datacenter = 'us1'
    self.runtime_config.instance_id = 'abc3dzac4'
    self.runtime_config.auth_domain = 'gmail.com'
    self.runtime_config_getter = lambda: self.runtime_config
    self.proxy = http_runtime.HttpRuntimeProxy(
        ['/runtime'], self.runtime_config_getter, module_configuration,
        env={'foo': 'bar'})
    self.proxy._port = 23456
    self.process = self.mox.CreateMock(subprocess.Popen)
    self.process.stdin = self.mox.CreateMockAnything()
    self.process.stdout = self.mox.CreateMockAnything()
    self.process.stderr = self.mox.CreateMockAnything()

    self.mox.StubOutWithMock(safe_subprocess, 'start_process')
    self.mox.StubOutWithMock(login, 'get_user_info')
    self.url_map = appinfo.URLMap(url=r'/(get|post).*',
                                  script=r'\1.py')

    self.mox.StubOutWithMock(http_proxy.HttpProxy, 'wait_for_connection')
    http_proxy.HttpProxy.wait_for_connection()
    self._saved_quit_with_sigterm = None


  def tearDown(self):
    shutil.rmtree(self.tmpdir)
    self.mox.UnsetStubs()
    if self._saved_quit_with_sigterm is not None:
      http_runtime.HttpRuntimeProxy.stop_runtimes_with_sigterm(
          self._saved_quit_with_sigterm)

  def _test_start_and_quit(self, quit_with_sigterm):
    ## Test start()
    # start()
    self._saved_quit_with_sigterm = (
        http_runtime.HttpRuntimeProxy.stop_runtimes_with_sigterm(
            quit_with_sigterm))
    safe_subprocess.start_process(
        ['/runtime'],
        base64.b64encode(self.runtime_config.SerializeToString()),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={'foo': 'bar'},
        cwd=self.tmpdir).AndReturn(self.process)
    self.process.stdout.readline().AndReturn('30000')
    self.proxy._stderr_tee = FakeTee('')

    self.mox.ReplayAll()
    self.proxy.start()
    self.mox.VerifyAll()
    self.mox.ResetAll()

    ## Test quit()
    if quit_with_sigterm:
      self.process.terminate()
    else:
      self.process.kill()
    self.mox.ReplayAll()
    self.proxy.quit()
    self.mox.VerifyAll()

  def test_start_and_quit(self):
    self._test_start_and_quit(quit_with_sigterm=False)

  def test_start_and_quit_with_sigterm(self):
    self._test_start_and_quit(quit_with_sigterm=True)

  def test_start_bad_port(self):
    safe_subprocess.start_process(
        ['/runtime'],
        base64.b64encode(self.runtime_config.SerializeToString()),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={'foo': 'bar'},
        cwd=self.tmpdir).AndReturn(self.process)
    self.process.stdout.readline().AndReturn('hello 30001')
    header = "bad runtime process port ['hello 30001']\n\n"
    stderr0 = "I've just picked up a fault in the AE35 unit.\n"
    stderr1 = "It's going to go 100% failure in 72 hours.\n"
    self.proxy._stderr_tee = FakeTee(stderr0 + stderr1)

    self.mox.ReplayAll()
    self.proxy.start()
    expected_headers = {
        'Content-Type': 'text/plain',
        'Content-Length': str(len(header) + len(stderr0) + len(stderr1)),
    }
    self.assertResponse('500 Internal Server Error', expected_headers,
                        header + stderr0 + stderr1,
                        self.proxy.handle, {},
                        url_map=self.url_map,
                        match=re.match(self.url_map.url, '/get%20request'),
                        request_id='request id',
                        request_type=instance.NORMAL_REQUEST)
    self.mox.VerifyAll()


class HttpRuntimeProxyFileFlavorTest(wsgi_test_utils.WSGITestCase):

  def setUp(self):
    self.mox = mox.Mox()
    self.tmpdir = tempfile.mkdtemp()
    module_configuration = ModuleConfigurationStub(application_root=self.tmpdir)
    self.runtime_config = runtime_config_pb2.Config()
    self.runtime_config.app_id = 'app'
    self.runtime_config.version_id = 'version'
    self.runtime_config.api_port = 12345
    self.runtime_config.application_root = self.tmpdir
    self.runtime_config.datacenter = 'us1'
    self.runtime_config.instance_id = 'abc3dzac4'
    self.runtime_config.auth_domain = 'gmail.com'
    self.runtime_config_getter = lambda: self.runtime_config
    self.proxy = http_runtime.HttpRuntimeProxy(
        ['/runtime'], self.runtime_config_getter, module_configuration,
        env={'foo': 'bar'},
        start_process_flavor=http_runtime.START_PROCESS_FILE)
    self.mox.StubOutWithMock(self.proxy, '_process_lock')
    self.process = self.mox.CreateMock(subprocess.Popen)
    self.process.stdin = self.mox.CreateMockAnything()
    self.process.stdout = self.mox.CreateMockAnything()
    self.process.stderr = self.mox.CreateMockAnything()
    self.process.child_out = self.mox.CreateMockAnything()
    self.mox.StubOutWithMock(safe_subprocess, 'start_process_file')
    self.mox.StubOutWithMock(os, 'remove')
    self.mox.StubOutWithMock(time, 'sleep')
    self.url_map = appinfo.URLMap(url=r'/(get|post).*',
                                  script=r'\1.py')

    self.mox.StubOutWithMock(http_proxy.HttpProxy, 'wait_for_connection')
    http_proxy.HttpProxy.wait_for_connection()

  def tearDown(self):
    shutil.rmtree(self.tmpdir)
    self.mox.UnsetStubs()

  def test_basic(self):
    """Basic functionality test of START_PROCESS_FILE flavor."""
    # start()
    # As the lock is mocked out, this provides a mox expectation.
    with self.proxy._process_lock:
      safe_subprocess.start_process_file(
          args=['/runtime'],
          input_string=self.runtime_config.SerializeToString(),
          env={'foo': 'bar'},
          cwd=self.tmpdir,
          stderr=subprocess.PIPE).AndReturn(self.process)
    self.process.poll().AndReturn(None)
    self.process.child_out.seek(0).AndReturn(None)
    self.process.child_out.read().AndReturn('1234\n')
    self.process.child_out.close().AndReturn(None)
    self.process.child_out.name = '/tmp/c-out.ABC'
    os.remove('/tmp/c-out.ABC').AndReturn(None)
    self.proxy._stderr_tee = FakeTee('')

    self.mox.ReplayAll()
    self.proxy.start()
    self.assertEquals(1234, self.proxy._proxy._port)
    self.mox.VerifyAll()

  def test_slow_shattered(self):
    """The port number is received slowly in chunks."""
    # start()
    # As the lock is mocked out, this provides a mox expectation.
    with self.proxy._process_lock:
      safe_subprocess.start_process_file(
          args=['/runtime'],
          input_string=self.runtime_config.SerializeToString(),
          env={'foo': 'bar'},
          cwd=self.tmpdir,
          stderr=subprocess.PIPE).AndReturn(self.process)
    for response, sleeptime in [
        ('', .125), ('43', .25), ('4321', .5), ('4321\n', None)]:
      self.process.poll().AndReturn(None)
      self.process.child_out.seek(0).AndReturn(None)
      self.process.child_out.read().AndReturn(response)
      if sleeptime is not None:
        time.sleep(sleeptime).AndReturn(None)
    self.process.child_out.close().AndReturn(None)
    self.process.child_out.name = '/tmp/c-out.ABC'
    os.remove('/tmp/c-out.ABC').AndReturn(None)
    self.proxy._stderr_tee = FakeTee('')

    self.mox.ReplayAll()
    self.proxy.start()
    self.assertEquals(4321, self.proxy._proxy._port)
    self.mox.VerifyAll()

  def test_runtime_instance_dies_immediately(self):
    """Runtime instance dies without sending a port."""
    # start()
    # As the lock is mocked out, this provides a mox expectation.
    with self.proxy._process_lock:
      safe_subprocess.start_process_file(
          args=['/runtime'],
          input_string=self.runtime_config.SerializeToString(),
          env={'foo': 'bar'},
          cwd=self.tmpdir,
          stderr=subprocess.PIPE).AndReturn(self.process)
    self.process.poll().AndReturn(1)
    self.process.child_out.close().AndReturn(None)
    self.process.child_out.name = '/tmp/c-out.ABC'
    os.remove('/tmp/c-out.ABC').AndReturn(None)
    header = "bad runtime process port ['']\n\n"
    stderr0 = 'Go away..\n'
    self.proxy._stderr_tee = FakeTee(stderr0)
    time.sleep(.1).AndReturn(None)

    self.mox.ReplayAll()
    self.proxy.start()
    expected_headers = {
        'Content-Type': 'text/plain',
        'Content-Length': str(len(header) + len(stderr0)),
    }
    self.assertResponse('500 Internal Server Error', expected_headers,
                        header + stderr0,
                        self.proxy.handle, {},
                        url_map=self.url_map,
                        match=re.match(self.url_map.url, '/get%20request'),
                        request_id='request id',
                        request_type=instance.NORMAL_REQUEST)
    self.mox.VerifyAll()

  def test_runtime_instance_invalid_response(self):
    """Runtime instance does not terminate port with a newline."""
    # start()
    # As the lock is mocked out, this provides a mox expectation.
    with self.proxy._process_lock:
      safe_subprocess.start_process_file(
          args=['/runtime'],
          input_string=self.runtime_config.SerializeToString(),
          env={'foo': 'bar'},
          cwd=self.tmpdir,
          stderr=subprocess.PIPE).AndReturn(self.process)
    for response, sleeptime in [
        ('30000', .125), ('30000', .25), ('30000', .5), ('30000', 1.0),
        ('30000', 2.0), ('30000', 4.0), ('30000', 8.0), ('30000', 16.0),
        ('30000', 32.0), ('30000', None)]:
      self.process.poll().AndReturn(None)
      self.process.child_out.seek(0).AndReturn(None)
      self.process.child_out.read().AndReturn(response)
      if sleeptime is not None:
        time.sleep(sleeptime).AndReturn(None)
    self.process.child_out.close().AndReturn(None)
    self.process.child_out.name = '/tmp/c-out.ABC'
    os.remove('/tmp/c-out.ABC').AndReturn(None)
    header = "bad runtime process port ['']\n\n"
    stderr0 = 'Go away..\n'
    self.proxy._stderr_tee = FakeTee(stderr0)
    time.sleep(.1)

    self.mox.ReplayAll()
    self.proxy.start()
    expected_headers = {
        'Content-Type': 'text/plain',
        'Content-Length': str(len(header) + len(stderr0)),
    }
    self.assertResponse('500 Internal Server Error', expected_headers,
                        header + stderr0,
                        self.proxy.handle, {},
                        url_map=self.url_map,
                        match=re.match(self.url_map.url, '/get%20request'),
                        request_id='request id',
                        request_type=instance.NORMAL_REQUEST)
    self.mox.VerifyAll()


class HttpRuntimeProxyReverseFlavorTest(wsgi_test_utils.WSGITestCase):

  def setUp(self):
    self.mox = mox.Mox()
    self.tmpdir = tempfile.mkdtemp()
    module_configuration = ModuleConfigurationStub(application_root=self.tmpdir)
    self.runtime_config = runtime_config_pb2.Config()
    self.runtime_config.app_id = 'app'
    self.runtime_config.version_id = 'version'
    self.runtime_config.api_port = 12345
    self.runtime_config.application_root = self.tmpdir
    self.runtime_config.datacenter = 'us1'
    self.runtime_config.instance_id = 'abc3dzac4'
    self.runtime_config.auth_domain = 'gmail.com'
    self.runtime_config_getter = lambda: self.runtime_config
    self.proxy = http_runtime.HttpRuntimeProxy(
        ['/runtime'], self.runtime_config_getter, module_configuration,
        env={'foo': 'bar'},
        start_process_flavor=http_runtime.START_PROCESS_REVERSE)
    self.mox.StubOutWithMock(self.proxy, '_process_lock')
    self.process = self.mox.CreateMock(subprocess.Popen)
    self.process.stdin = self.mox.CreateMockAnything()
    self.mox.StubOutWithMock(safe_subprocess, 'start_process_file')
    self.mox.StubOutWithMock(os, 'remove')
    self.mox.StubOutWithMock(time, 'sleep')
    self.url_map = appinfo.URLMap(url=r'/(get|post).*',
                                  script=r'\1.py')

    self.mox.StubOutWithMock(http_proxy.HttpProxy, 'wait_for_connection')
    self.mox.StubOutWithMock(portpicker, 'PickUnusedPort')
    http_proxy.HttpProxy.wait_for_connection()

  def tearDown(self):
    shutil.rmtree(self.tmpdir)
    self.mox.UnsetStubs()

  def test_basic(self):
    """Basic functionality test of START_PROCESS_REVERSE flavor."""
    portpicker.PickUnusedPort().AndReturn(2345)
    # As the lock is mocked out, this provides a mox expectation.
    with self.proxy._process_lock:
      safe_subprocess.start_process_file(
          args=['/runtime'],
          input_string=self.runtime_config.SerializeToString(),
          env={'foo': 'bar',
               'PORT': '2345'},
          cwd=self.tmpdir,
          stderr=subprocess.PIPE).AndReturn(self.process)
    self.proxy._stderr_tee = FakeTee('')

    self.mox.ReplayAll()
    self.proxy.start()
    self.assertEquals(2345, self.proxy._proxy._port)
    self.mox.VerifyAll()

if __name__ == '__main__':
  unittest.main()
