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
"""Tests for google.appengine.tools.devappserver2.http_proxy."""

import cStringIO
import httplib
import os
import re
import shutil
import socket
import tempfile
import unittest

import google

import mox

from google.appengine.api import appinfo
from google.appengine.tools.devappserver2 import http_proxy
from google.appengine.tools.devappserver2 import http_runtime_constants
from google.appengine.tools.devappserver2 import instance
from google.appengine.tools.devappserver2 import login
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


def get_instance_logs():
  return ''


class HttpProxyTest(wsgi_test_utils.WSGITestCase):
  def setUp(self):
    self.mox = mox.Mox()
    self.tmpdir = tempfile.mkdtemp()

    self.proxy = http_proxy.HttpProxy(
        host='localhost', port=23456,
        instance_died_unexpectedly=lambda: False,
        instance_logs_getter=get_instance_logs,
        error_handler_file=None)

    self.mox.StubOutWithMock(httplib.HTTPConnection, 'connect')
    self.mox.StubOutWithMock(httplib.HTTPConnection, 'request')
    self.mox.StubOutWithMock(httplib.HTTPConnection, 'getresponse')
    self.mox.StubOutWithMock(httplib.HTTPConnection, 'close')
    self.mox.StubOutWithMock(login, 'get_user_info')
    self.url_map = appinfo.URLMap(url=r'/(get|post).*',
                                  script=r'\1.py')

  def tearDown(self):
    shutil.rmtree(self.tmpdir)
    self.mox.UnsetStubs()

  def test_handle_get(self):
    response = FakeHttpResponse(200,
                                'OK',
                                [('Foo', 'a'), ('Foo', 'b'), ('Var', 'c')],
                                'response')
    login.get_user_info(None).AndReturn(('', False, ''))
    httplib.HTTPConnection.connect()
    httplib.HTTPConnection.request(
        'GET', '/get%20request?key=value', None,
        {'HEADER': 'value',
         http_runtime_constants.REQUEST_ID_HEADER: 'request id',
         'X-AppEngine-Country': 'ZZ',
         'X-Appengine-User-Email': '',
         'X-Appengine-User-Id': '',
         'X-Appengine-User-Is-Admin': '0',
         'X-Appengine-User-Nickname': '',
         'X-Appengine-User-Organization': '',
         'X-APPENGINE-DEV-SCRIPT': 'get.py',
         'X-APPENGINE-SERVER-NAME': 'localhost',
         'X-APPENGINE-SERVER-PORT': '8080',
         'X-APPENGINE-SERVER-PROTOCOL': 'HTTP/1.1',
        })
    httplib.HTTPConnection.getresponse().AndReturn(response)
    httplib.HTTPConnection.close()
    environ = {'HTTP_HEADER': 'value', 'PATH_INFO': '/get request',
               'QUERY_STRING': 'key=value',
               'HTTP_X_APPENGINE_USER_ID': '123',
               'SERVER_NAME': 'localhost',
               'SERVER_PORT': '8080',
               'SERVER_PROTOCOL': 'HTTP/1.1',
              }
    self.mox.ReplayAll()
    expected_headers = [('Foo', 'a'), ('Foo', 'b'), ('Var', 'c')]
    self.assertResponse('200 OK', expected_headers, 'response',
                        self.proxy.handle, environ,
                        url_map=self.url_map,
                        match=re.match(self.url_map.url, '/get%20request'),
                        request_id='request id',
                        request_type=instance.NORMAL_REQUEST)
    self.mox.VerifyAll()

  def test_handle_post(self):
    response = FakeHttpResponse(200,
                                'OK',
                                [('Foo', 'a'), ('Foo', 'b'), ('Var', 'c')],
                                'response')
    login.get_user_info('cookie').AndReturn(('user@example.com', True, '12345'))
    httplib.HTTPConnection.connect()
    httplib.HTTPConnection.request(
        'POST', '/post', 'post data',
        {'HEADER': 'value',
         'COOKIE': 'cookie',
         'CONTENT-TYPE': 'text/plain',
         'CONTENT-LENGTH': '9',
         http_runtime_constants.REQUEST_ID_HEADER: 'request id',
         'X-AppEngine-Country': 'ZZ',
         'X-Appengine-User-Email': 'user@example.com',
         'X-Appengine-User-Id': '12345',
         'X-Appengine-User-Is-Admin': '1',
         'X-Appengine-User-Nickname': 'user',
         'X-Appengine-User-Organization': 'example.com',
         'X-APPENGINE-DEV-SCRIPT': 'post.py',
         'X-APPENGINE-SERVER-NAME': 'localhost',
         'X-APPENGINE-SERVER-PORT': '8080',
         'X-APPENGINE-SERVER-PROTOCOL': 'HTTP/1.1',
        })
    httplib.HTTPConnection.getresponse().AndReturn(response)
    httplib.HTTPConnection.close()
    environ = {'HTTP_HEADER': 'value', 'PATH_INFO': '/post',
               'wsgi.input': cStringIO.StringIO('post data'),
               'CONTENT_LENGTH': '9',
               'CONTENT_TYPE': 'text/plain',
               'REQUEST_METHOD': 'POST',
               'HTTP_COOKIE': 'cookie',
               'SERVER_NAME': 'localhost',
               'SERVER_PORT': '8080',
               'SERVER_PROTOCOL': 'HTTP/1.1',
              }
    self.mox.ReplayAll()
    expected_headers = [('Foo', 'a'), ('Foo', 'b'), ('Var', 'c')]
    self.assertResponse('200 OK', expected_headers, 'response',
                        self.proxy.handle, environ,
                        url_map=self.url_map,
                        match=re.match(self.url_map.url, '/post'),
                        request_id='request id',
                        request_type=instance.NORMAL_REQUEST)
    self.mox.VerifyAll()

  def test_handle_with_error(self):
    error_handler_file = os.path.join(self.tmpdir, 'error.html')
    with open(error_handler_file, 'w') as f:
      f.write('error')

    self.proxy = http_proxy.HttpProxy(
        host='localhost', port=23456,
        instance_died_unexpectedly=lambda: False,
        instance_logs_getter=get_instance_logs,
        error_handler_file=error_handler_file)

    response = FakeHttpResponse(
        500, 'Internal Server Error',
        [(http_runtime_constants.ERROR_CODE_HEADER, '1')], '')
    login.get_user_info(None).AndReturn(('', False, ''))
    httplib.HTTPConnection.connect()
    httplib.HTTPConnection.request(
        'GET', '/get%20error', None,
        {'HEADER': 'value',
         http_runtime_constants.REQUEST_ID_HEADER: 'request id',
         'X-AppEngine-Country': 'ZZ',
         'X-Appengine-User-Email': '',
         'X-Appengine-User-Id': '',
         'X-Appengine-User-Is-Admin': '0',
         'X-Appengine-User-Nickname': '',
         'X-Appengine-User-Organization': '',
         'X-APPENGINE-DEV-SCRIPT': 'get.py',
         'X-APPENGINE-SERVER-NAME': 'localhost',
         'X-APPENGINE-SERVER-PORT': '8080',
         'X-APPENGINE-SERVER-PROTOCOL': 'HTTP/1.1',
        })
    httplib.HTTPConnection.getresponse().AndReturn(response)
    httplib.HTTPConnection.close()
    environ = {'HTTP_HEADER': 'value', 'PATH_INFO': '/get error',
               'QUERY_STRING': '',
               'HTTP_X_APPENGINE_USER_ID': '123',
               'SERVER_NAME': 'localhost',
               'SERVER_PORT': '8080',
               'SERVER_PROTOCOL': 'HTTP/1.1',
              }
    self.mox.ReplayAll()
    expected_headers = {
        'Content-Type': 'text/html',
        'Content-Length': '5',
    }
    self.assertResponse('500 Internal Server Error', expected_headers, 'error',
                        self.proxy.handle, environ,
                        url_map=self.url_map,
                        match=re.match(self.url_map.url, '/get%20error'),
                        request_id='request id',
                        request_type=instance.NORMAL_REQUEST)
    self.mox.VerifyAll()

  def test_handle_with_error_no_error_handler(self):
    self.proxy = http_proxy.HttpProxy(
        host='localhost', port=23456,
        instance_died_unexpectedly=lambda: False,
        instance_logs_getter=get_instance_logs,
        error_handler_file=None)
    response = FakeHttpResponse(
        500, 'Internal Server Error',
        [(http_runtime_constants.ERROR_CODE_HEADER, '1')], '')
    login.get_user_info(None).AndReturn(('', False, ''))
    httplib.HTTPConnection.connect()
    httplib.HTTPConnection.request(
        'GET', '/get%20error', None,
        {'HEADER': 'value',
         http_runtime_constants.REQUEST_ID_HEADER: 'request id',
         'X-AppEngine-Country': 'ZZ',
         'X-Appengine-User-Email': '',
         'X-Appengine-User-Id': '',
         'X-Appengine-User-Is-Admin': '0',
         'X-Appengine-User-Nickname': '',
         'X-Appengine-User-Organization': '',
         'X-APPENGINE-DEV-SCRIPT': 'get.py',
         'X-APPENGINE-SERVER-NAME': 'localhost',
         'X-APPENGINE-SERVER-PORT': '8080',
         'X-APPENGINE-SERVER-PROTOCOL': 'HTTP/1.1',
        })
    httplib.HTTPConnection.getresponse().AndReturn(response)
    httplib.HTTPConnection.close()
    environ = {'HTTP_HEADER': 'value', 'PATH_INFO': '/get error',
               'QUERY_STRING': '',
               'HTTP_X_APPENGINE_USER_ID': '123',
               'SERVER_NAME': 'localhost',
               'SERVER_PORT': '8080',
               'SERVER_PROTOCOL': 'HTTP/1.1',
              }
    self.mox.ReplayAll()
    self.assertResponse('500 Internal Server Error', {}, '',
                        self.proxy.handle, environ,
                        url_map=self.url_map,
                        match=re.match(self.url_map.url, '/get%20error'),
                        request_id='request id',
                        request_type=instance.NORMAL_REQUEST)
    self.mox.VerifyAll()

  def test_handle_with_error_missing_error_handler(self):
    error_handler_file = os.path.join(self.tmpdir, 'error.html')

    self.proxy = http_proxy.HttpProxy(
        host='localhost', port=23456,
        instance_died_unexpectedly=lambda: False,
        instance_logs_getter=get_instance_logs,
        error_handler_file=error_handler_file)

    response = FakeHttpResponse(
        500, 'Internal Server Error',
        [(http_runtime_constants.ERROR_CODE_HEADER, '1')], '')
    login.get_user_info(None).AndReturn(('', False, ''))
    httplib.HTTPConnection.connect()
    httplib.HTTPConnection.request(
        'GET', '/get%20error', None,
        {'HEADER': 'value',
         http_runtime_constants.REQUEST_ID_HEADER: 'request id',
         'X-AppEngine-Country': 'ZZ',
         'X-Appengine-User-Email': '',
         'X-Appengine-User-Id': '',
         'X-Appengine-User-Is-Admin': '0',
         'X-Appengine-User-Nickname': '',
         'X-Appengine-User-Organization': '',
         'X-APPENGINE-DEV-SCRIPT': 'get.py',
         'X-APPENGINE-SERVER-NAME': 'localhost',
         'X-APPENGINE-SERVER-PORT': '8080',
         'X-APPENGINE-SERVER-PROTOCOL': 'HTTP/1.1',
        })
    httplib.HTTPConnection.getresponse().AndReturn(response)
    httplib.HTTPConnection.close()
    environ = {'HTTP_HEADER': 'value', 'PATH_INFO': '/get error',
               'QUERY_STRING': '',
               'HTTP_X_APPENGINE_USER_ID': '123',
               'SERVER_NAME': 'localhost',
               'SERVER_PORT': '8080',
               'SERVER_PROTOCOL': 'HTTP/1.1',
              }
    self.mox.ReplayAll()
    expected_headers = {
        'Content-Type': 'text/html',
        'Content-Length': '28',
    }
    self.assertResponse('500 Internal Server Error', expected_headers,
                        'Failed to load error handler', self.proxy.handle,
                        environ, url_map=self.url_map,
                        match=re.match(self.url_map.url, '/get%20error'),
                        request_id='request id',
                        request_type=instance.NORMAL_REQUEST)
    self.mox.VerifyAll()

  def test_http_response_early_failure(self):
    header = ('the runtime process gave a bad HTTP response: '
              'IncompleteRead(0 bytes read)\n\n')
    def dave_message():
      return "I'm sorry, Dave. I'm afraid I can't do that.\n"

    self.proxy = http_proxy.HttpProxy(
        host='localhost', port=23456,
        instance_died_unexpectedly=lambda: False,
        instance_logs_getter=dave_message,
        error_handler_file=None)

    login.get_user_info(None).AndReturn(('', False, ''))
    httplib.HTTPConnection.connect()
    httplib.HTTPConnection.request(
        'GET', '/get%20request?key=value', None,
        {'HEADER': 'value',
         http_runtime_constants.REQUEST_ID_HEADER: 'request id',
         'X-AppEngine-Country': 'ZZ',
         'X-Appengine-User-Email': '',
         'X-Appengine-User-Id': '',
         'X-Appengine-User-Is-Admin': '0',
         'X-Appengine-User-Nickname': '',
         'X-Appengine-User-Organization': '',
         'X-APPENGINE-DEV-SCRIPT': 'get.py',
         'X-APPENGINE-SERVER-NAME': 'localhost',
         'X-APPENGINE-SERVER-PORT': '8080',
         'X-APPENGINE-SERVER-PROTOCOL': 'HTTP/1.1',
        })
    httplib.HTTPConnection.getresponse().AndRaise(httplib.IncompleteRead(''))
    httplib.HTTPConnection.close()
    environ = {'HTTP_HEADER': 'value', 'PATH_INFO': '/get request',
               'QUERY_STRING': 'key=value',
               'HTTP_X_APPENGINE_USER_ID': '123',
               'SERVER_NAME': 'localhost',
               'SERVER_PORT': '8080',
               'SERVER_PROTOCOL': 'HTTP/1.1',
              }
    self.mox.ReplayAll()
    expected_headers = {
        'Content-Type': 'text/plain',
        'Content-Length': '%d' % (len(header) + len(dave_message()))
    }

    self.assertResponse('500 Internal Server Error', expected_headers,
                        header + dave_message(),
                        self.proxy.handle, environ,
                        url_map=self.url_map,
                        match=re.match(self.url_map.url, '/get%20request'),
                        request_id='request id',
                        request_type=instance.NORMAL_REQUEST)
    self.mox.VerifyAll()

  def test_http_response_late_failure(self):
    line0 = "I know I've made some very poor decisions recently...\n"
    def dave_message():
      return "I'm afraid. I'm afraid, Dave.\n"

    self.proxy = http_proxy.HttpProxy(
        host='localhost', port=23456,
        instance_died_unexpectedly=lambda: False,
        instance_logs_getter=dave_message,
        error_handler_file=None)

    response = FakeHttpResponse(200, 'OK', [], line0)
    response.partial_read_error = httplib.IncompleteRead('')
    login.get_user_info(None).AndReturn(('', False, ''))
    httplib.HTTPConnection.connect()
    httplib.HTTPConnection.request(
        'GET', '/get%20request?key=value', None,
        {'HEADER': 'value',
         http_runtime_constants.REQUEST_ID_HEADER: 'request id',
         'X-AppEngine-Country': 'ZZ',
         'X-Appengine-User-Email': '',
         'X-Appengine-User-Id': '',
         'X-Appengine-User-Is-Admin': '0',
         'X-Appengine-User-Nickname': '',
         'X-Appengine-User-Organization': '',
         'X-APPENGINE-DEV-SCRIPT': 'get.py',
         'X-APPENGINE-SERVER-NAME': 'localhost',
         'X-APPENGINE-SERVER-PORT': '8080',
         'X-APPENGINE-SERVER-PROTOCOL': 'HTTP/1.1',
        })
    httplib.HTTPConnection.getresponse().AndReturn(response)
    httplib.HTTPConnection.close()
    environ = {'HTTP_HEADER': 'value', 'PATH_INFO': '/get request',
               'QUERY_STRING': 'key=value',
               'HTTP_X_APPENGINE_USER_ID': '123',
               'SERVER_NAME': 'localhost',
               'SERVER_PORT': '8080',
               'SERVER_PROTOCOL': 'HTTP/1.1',
              }
    self.mox.ReplayAll()
    self.assertResponse('200 OK', {},
                        line0,
                        self.proxy.handle, environ,
                        url_map=self.url_map,
                        match=re.match(self.url_map.url, '/get%20request'),
                        request_id='request id',
                        request_type=instance.NORMAL_REQUEST)
    self.mox.VerifyAll()

  def test_connection_error(self):
    login.get_user_info(None).AndReturn(('', False, ''))
    httplib.HTTPConnection.connect().AndRaise(socket.error())
    httplib.HTTPConnection.close()

    self.mox.ReplayAll()
    self.assertRaises(socket.error,
                      self.proxy.handle(
                          {'PATH_INFO': '/'},
                          start_response=None,  # Not used.
                          url_map=self.url_map,
                          match=re.match(self.url_map.url, '/get%20error'),
                          request_id='request id',
                          request_type=instance.NORMAL_REQUEST).next)
    self.mox.VerifyAll()

  def test_connection_error_process_quit(self):
    self.proxy = http_proxy.HttpProxy(
        host='localhost', port=123,
        instance_died_unexpectedly=lambda: True,
        instance_logs_getter=get_instance_logs,
        error_handler_file=None)
    login.get_user_info(None).AndReturn(('', False, ''))
    httplib.HTTPConnection.connect().AndRaise(socket.error())
    httplib.HTTPConnection.close()

    self.mox.ReplayAll()
    expected_headers = {
        'Content-Type': 'text/plain',
        'Content-Length': '78',
    }
    expected_content = ('the runtime process for the instance running on port '
                        '123 has unexpectedly quit')
    self.assertResponse('500 Internal Server Error',
                        expected_headers,
                        expected_content,
                        self.proxy.handle,
                        {'PATH_INFO': '/'},
                        url_map=self.url_map,
                        match=re.match(self.url_map.url, '/get%20error'),
                        request_id='request id',
                        request_type=instance.NORMAL_REQUEST)
    self.mox.VerifyAll()

  def test_handle_background_thread(self):
    response = FakeHttpResponse(200, 'OK', [('Foo', 'Bar')], 'response')
    login.get_user_info(None).AndReturn(('', False, ''))
    httplib.HTTPConnection.connect()
    httplib.HTTPConnection.request(
        'GET', '/get%20request?key=value', None,
        {'HEADER': 'value',
         http_runtime_constants.REQUEST_ID_HEADER: 'request id',
         'X-AppEngine-Country': 'ZZ',
         'X-Appengine-User-Email': '',
         'X-Appengine-User-Id': '',
         'X-Appengine-User-Is-Admin': '0',
         'X-Appengine-User-Nickname': '',
         'X-Appengine-User-Organization': '',
         'X-APPENGINE-DEV-SCRIPT': 'get.py',
         'X-APPENGINE-DEV-REQUEST-TYPE': 'background',
         'X-APPENGINE-SERVER-NAME': 'localhost',
         'X-APPENGINE-SERVER-PORT': '8080',
         'X-APPENGINE-SERVER-PROTOCOL': 'HTTP/1.1',
        })
    httplib.HTTPConnection.getresponse().AndReturn(response)
    httplib.HTTPConnection.close()
    environ = {'HTTP_HEADER': 'value', 'PATH_INFO': '/get request',
               'QUERY_STRING': 'key=value',
               'HTTP_X_APPENGINE_USER_ID': '123',
               'SERVER_NAME': 'localhost',
               'SERVER_PORT': '8080',
               'SERVER_PROTOCOL': 'HTTP/1.1',
              }
    self.mox.ReplayAll()
    expected_headers = {
        'Foo': 'Bar',
    }
    self.assertResponse('200 OK', expected_headers, 'response',
                        self.proxy.handle, environ,
                        url_map=self.url_map,
                        match=re.match(self.url_map.url, '/get%20request'),
                        request_id='request id',
                        request_type=instance.BACKGROUND_REQUEST)
    self.mox.VerifyAll()

  def test_prior_error(self):
    error = 'Oh no! Something is broken again!'
    self.proxy = http_proxy.HttpProxy(
        host=None, port=None,
        instance_died_unexpectedly=None,
        instance_logs_getter=get_instance_logs,
        error_handler_file=None,
        prior_error=error)

    # Expect that wait_for_connection does not hang.
    self.proxy.wait_for_connection()

    expected_headers = {
        'Content-Type': 'text/plain',
        'Content-Length': str(len(error)),
    }
    self.assertResponse('500 Internal Server Error', expected_headers,
                        error,
                        self.proxy.handle, {},
                        url_map=self.url_map,
                        match=re.match(self.url_map.url, '/get%20request'),
                        request_id='request id',
                        request_type=instance.NORMAL_REQUEST)
    self.mox.VerifyAll()


if __name__ == '__main__':
  unittest.main()
