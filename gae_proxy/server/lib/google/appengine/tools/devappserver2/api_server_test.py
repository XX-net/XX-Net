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
"""Tests for google.apphosting.tools.devappserver2.api_server."""



import cStringIO
import pickle
import re
import tempfile
import unittest
import urllib
import wsgiref.util

from google.net.rpc.python.testing import rpc_test_harness

from google.appengine.api import apiproxy_stub
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import urlfetch_service_pb
from google.appengine.api import user_service_pb
from google.appengine.datastore import datastore_stub_util
from google.appengine.datastore import datastore_v4_pb
from google.appengine.ext.remote_api import remote_api_pb
from google.appengine.runtime import apiproxy_errors
from google.appengine.tools.devappserver2 import api_server
from google.appengine.tools.devappserver2 import wsgi_request_info
from google.appengine.tools.devappserver2 import wsgi_test_utils

APP_ID = 'test'
APPLICATION_ROOT = '/tmp'
TRUSTED = False
_, BLOBSTORE_PATH = tempfile.mkstemp(prefix='ae-blobstore')
_, DATASTORE_PATH = tempfile.mkstemp(prefix='ae-datastore')
DATASTORE_REQUIRE_INDEXES = False
IMAGES_HOST_PREFIX = 'localhost:8080'
LOGS_PATH = ':memory:'
MAIL_SMTP_HOST = 'localhost'
MAIL_SMTP_PORT = 80
MAIL_SMTP_USER = 'user'
MAIL_SMTP_PASSWORD = 'abc123'
MAIL_ENABLE_SENDMAIL = False
MAIL_SHOW_MAIL_BODY = True
_, MATCHER_PROSPECTIVE_SEARCH_PATH = tempfile.mkstemp(prefix='ae-ps')
TASKQUEUE_AUTO_RUN_TASKS = False
TASKQUEUE_DEFAULT_HTTP_SERVER = 'localhost:8080'
USER_LOGIN_URL = 'https://localhost/Login?continue=%s'
USER_LOGOUT_URL = 'https://localhost/Logout?continue=%s'

request_data = wsgi_request_info.WSGIRequestInfo(None)


class FakeURLFetchServiceStub(apiproxy_stub.APIProxyStub):
  def __init__(self):
    super(FakeURLFetchServiceStub, self).__init__('urlfetch')

  def _Dynamic_Fetch(self, request, unused_response):
    if request.url() == 'exception':
      raise IOError('the remote error')
    elif request.url() == 'application_error':
      raise apiproxy_errors.ApplicationError(23, 'details')


class FakeDatastoreV4ServiceStub(apiproxy_stub.APIProxyStub):
  def __init__(self):
    super(FakeDatastoreV4ServiceStub, self).__init__('datastore_v4')

  def _Dynamic_BeginTransaction(self, request, response):
    response.set_transaction('whatever')


def setup_stubs():
  """Setup the API stubs. This can only be done once."""
  api_server.test_setup_stubs(
      request_data,
      app_id=APP_ID,
      application_root=APPLICATION_ROOT,
      trusted=TRUSTED,
      blobstore_path=BLOBSTORE_PATH,
      datastore_consistency=datastore_stub_util.TimeBasedHRConsistencyPolicy(),
      datastore_path=DATASTORE_PATH,
      datastore_require_indexes=DATASTORE_REQUIRE_INDEXES,
      images_host_prefix=IMAGES_HOST_PREFIX,
      logs_path=':memory:',
      mail_smtp_host=MAIL_SMTP_HOST,
      mail_smtp_port=MAIL_SMTP_PORT,
      mail_smtp_user=MAIL_SMTP_USER,
      mail_smtp_password=MAIL_SMTP_PASSWORD,
      mail_enable_sendmail=MAIL_ENABLE_SENDMAIL,
      mail_show_mail_body=MAIL_SHOW_MAIL_BODY,
      matcher_prospective_search_path=MATCHER_PROSPECTIVE_SEARCH_PATH,
      taskqueue_auto_run_tasks=TASKQUEUE_AUTO_RUN_TASKS,
      taskqueue_default_http_server=TASKQUEUE_DEFAULT_HTTP_SERVER,
      user_login_url=USER_LOGIN_URL,
      user_logout_url=USER_LOGOUT_URL)
  apiproxy_stub_map.apiproxy.ReplaceStub(
      'urlfetch', FakeURLFetchServiceStub())
  apiproxy_stub_map.apiproxy.ReplaceStub(
      'datastore_v4', FakeDatastoreV4ServiceStub())


class TestAPIServer(wsgi_test_utils.WSGITestCase):
  """Tests for api_server.APIServer."""

  def setUp(self):
    setup_stubs()
    self.server = api_server.APIServer('localhost',
                                       0,
                                       APP_ID)

  def tearDown(self):
    api_server.cleanup_stubs()

  def _assert_remote_call(
      self, expected_remote_response, stub_request, service, method):
    """Test a call across the remote API to the API server.

    Args:
      expected_remote_response: the remote response that is expected.
      stub_request: the request protobuf that the stub expects.
      service: the stub's service name.
      method: which service method to call.
    """
    request_environ = {'HTTP_HOST': 'machine:8080'}
    wsgiref.util.setup_testing_defaults(request_environ)

    with request_data.request(request_environ, None) as request_id:
      remote_request = remote_api_pb.Request()
      remote_request.set_service_name(service)
      remote_request.set_method(method)
      remote_request.set_request(stub_request.Encode())
      remote_request.set_request_id(request_id)
      remote_payload = remote_request.Encode()

      environ = {'CONTENT_LENGTH': len(remote_payload),
                 'REQUEST_METHOD': 'POST',
                 'wsgi.input': cStringIO.StringIO(remote_payload)}

      expected_headers = {'Content-Type': 'application/octet-stream'}
      self.assertResponse('200 OK',
                          expected_headers,
                          expected_remote_response.Encode(),
                          self.server,
                          environ)

  def test_user_api_call(self):
    logout_response = user_service_pb.CreateLogoutURLResponse()
    logout_response.set_logout_url(
        USER_LOGOUT_URL % urllib.quote('http://machine:8080/crazy_logout'))

    expected_remote_response = remote_api_pb.Response()
    expected_remote_response.set_response(logout_response.Encode())

    logout_request = user_service_pb.CreateLogoutURLRequest()
    logout_request.set_destination_url('/crazy_logout')

    self._assert_remote_call(
        expected_remote_response, logout_request, 'user', 'CreateLogoutURL')

  def test_datastore_v4_api_call(self):
    begin_transaction_response = datastore_v4_pb.BeginTransactionResponse()
    begin_transaction_response.set_transaction('whatever')

    expected_remote_response = remote_api_pb.Response()
    expected_remote_response.set_response(
        begin_transaction_response.Encode())

    begin_transaction_request = datastore_v4_pb.BeginTransactionRequest()

    self._assert_remote_call(
        expected_remote_response, begin_transaction_request,
        'datastore_v4', 'BeginTransaction')

  def test_datastore_v4_api_calls_handled(self):
    # We are only using RpcTestHarness as a clean way to get the list of
    # service methods.
    harness = rpc_test_harness.RpcTestHarness(
        datastore_v4_pb.DatastoreV4Service)
    deprecated = ['Get', 'Write']
    methods = set([k for k in harness.__dict__.keys()
                   if k not in deprecated and not k.startswith('_')])
    self.assertEqual(methods, set(api_server._DATASTORE_V4_METHODS.keys()))

  def test_GET(self):
    environ = {'REQUEST_METHOD': 'GET',
               'QUERY_STRING': 'rtok=23'}
    self.assertResponse('200 OK',
                        {'Content-Type': 'text/plain'},
                        "{app_id: test, rtok: '23'}\n",
                        self.server,
                        environ)

  def test_unsupported_method(self):
    environ = {'REQUEST_METHOD': 'HEAD',
               'QUERY_STRING': 'rtok=23'}
    self.assertResponse('405 Method Not Allowed',
                        {},
                        '',
                        self.server,
                        environ)

  def test_exception(self):
    urlfetch_request = urlfetch_service_pb.URLFetchRequest()
    urlfetch_request.set_url('exception')
    urlfetch_request.set_method(urlfetch_service_pb.URLFetchRequest.GET)

    expected_remote_response = remote_api_pb.Response()
    expected_remote_response.set_exception(pickle.dumps(
        RuntimeError(repr(IOError('the remote error')))))

    self._assert_remote_call(
        expected_remote_response, urlfetch_request, 'urlfetch', 'Fetch')

  def test_application_error(self):
    urlfetch_request = urlfetch_service_pb.URLFetchRequest()
    urlfetch_request.set_url('application_error')
    urlfetch_request.set_method(urlfetch_service_pb.URLFetchRequest.GET)

    expected_remote_response = remote_api_pb.Response()
    expected_remote_response.mutable_application_error().set_code(23)
    expected_remote_response.mutable_application_error().set_detail('details')
    expected_remote_response.set_exception(pickle.dumps(
        apiproxy_errors.ApplicationError(23, 'details')))

    self._assert_remote_call(
        expected_remote_response, urlfetch_request, 'urlfetch', 'Fetch')


if __name__ == '__main__':
  unittest.main()
