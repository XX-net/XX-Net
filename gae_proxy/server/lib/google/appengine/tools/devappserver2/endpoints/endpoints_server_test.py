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
"""Unit tests for the endpoints_server module."""







import httplib
import json
import logging
import unittest

import google

import mox

from google.appengine.tools.devappserver2 import dispatcher
from google.appengine.tools.devappserver2.endpoints import api_config_manager
from google.appengine.tools.devappserver2.endpoints import api_request
from google.appengine.tools.devappserver2.endpoints import discovery_api_proxy
from google.appengine.tools.devappserver2.endpoints import endpoints_server
from google.appengine.tools.devappserver2.endpoints import errors
from google.appengine.tools.devappserver2.endpoints import test_utils


class JsonMatches(mox.Comparator):
  """A Mox comparator to compare a string of a JSON object to a JSON object."""

  def __init__(self, json_object):
    """Constructor.

    Args:
      json_object: The JSON object to compare against.
    """
    self._json_object = json_object

  def equals(self, json_string):
    """Check if the given object matches our json object.

    This converts json_string from a string to a JSON object, then compares it
    against our json object.

    Args:
      json_string: A string containing a JSON object to be compared against.

    Returns:
      True if the object matches, False if not.
    """
    other_json = json.loads(json_string)
    return self._json_object == other_json

  def __repr__(self):
    return '<JsonMatches %r>' % self._json_object


class DevAppserverEndpointsServerTest(test_utils.TestsWithStartResponse):

  def setUp(self):
    """Set up a dev Endpoints server."""
    super(DevAppserverEndpointsServerTest, self).setUp()
    self.mox = mox.Mox()
    self.config_manager = api_config_manager.ApiConfigManager()
    self.mock_dispatcher = self.mox.CreateMock(dispatcher.Dispatcher)
    self.server = endpoints_server.EndpointsDispatcher(self.mock_dispatcher,
                                                       self.config_manager)

  def tearDown(self):
    self.mox.UnsetStubs()

  def prepare_dispatch(self, config):
    # The dispatch call will make a call to get_api_configs, making a
    # dispatcher request.  Set up that request.
    request_method = 'POST'
    request_path = '/_ah/spi/BackendService.getApiConfigs'
    request_headers = [('Content-Type', 'application/json')]
    request_body = '{}'
    response_body = json.dumps({'items': [config]})
    self.mock_dispatcher.add_request(
        request_method, request_path, request_headers, request_body,
        endpoints_server._SERVER_SOURCE_IP).AndReturn(
            dispatcher.ResponseTuple('200 OK',
                                     [('Content-Type', 'application/json'),
                                      ('Content-Length',
                                       str(len(response_body)))],
                                     response_body))

  def assert_dispatch_to_spi(self, request, config, spi_path,
                             expected_spi_body_json=None):
    """Assert that dispatching a request to the SPI works.

    Mock out the dispatcher.add_request and handle_spi_response, and use these
    to ensure that the correct request is being sent to the back end when
    Dispatch is called.

    Args:
      request: An ApiRequest, the request to dispatch.
      config: A dict containing the API configuration.
      spi_path: A string containing the relative path to the SPI.
      expected_spi_body_json: If not None, this is a JSON object containing
        the mock response sent by the back end.  If None, this will create an
        empty response.
    """
    self.prepare_dispatch(config)

    spi_headers = [('Content-Type', 'application/json')]
    spi_body_json = expected_spi_body_json or {}
    spi_response = dispatcher.ResponseTuple('200 OK', [], 'Test')
    self.mock_dispatcher.add_request(
        'POST', spi_path, spi_headers, JsonMatches(spi_body_json),
        request.source_ip).AndReturn(spi_response)

    self.mox.StubOutWithMock(self.server, 'handle_spi_response')
    self.server.handle_spi_response(
        mox.IsA(api_request.ApiRequest), mox.IsA(api_request.ApiRequest),
        spi_response, mox.IsA(dict), self.start_response).AndReturn('Test')

    # Run the test.
    self.mox.ReplayAll()
    response = self.server.dispatch(request, self.start_response)
    self.mox.VerifyAll()

    self.assertEqual('Test', response)

  def test_dispatch_invalid_path(self):
    config = json.dumps({
        'name': 'guestbook_api',
        'version': 'v1',
        'methods': {
            'guestbook.get': {
                'httpMethod': 'GET',
                'path': 'greetings/{gid}',
                'rosyMethod': 'MyApi.greetings_get'
            }
        }
    })
    request = test_utils.build_request('/_ah/api/foo')
    self.prepare_dispatch(config)
    self.mox.ReplayAll()
    response = self.server.dispatch(request, self.start_response)
    self.mox.VerifyAll()

    self.assert_http_match(response, 404,
                           [('Content-Type', 'text/plain'),
                            ('Content-Length', '9')],
                           'Not Found')

  def test_dispatch_invalid_enum(self):
    config = json.dumps({
        'name': 'guestbook_api',
        'version': 'v1',
        'methods': {
            'guestbook.get': {
                'httpMethod': 'GET',
                'path': 'greetings/{gid}',
                'rosyMethod': 'MyApi.greetings_get',
                'request': {
                    'body': 'empty',
                    'parameters': {'gid': {'enum': {'X': {'backendValue': 'X'}},
                                           'type': 'string'
                                          }
                                  }
                    }
                }
            }
        })

    request = test_utils.build_request(
        '/_ah/api/guestbook_api/v1/greetings/invalid_enum')
    self.prepare_dispatch(config)
    self.mox.ReplayAll()
    response = self.server.dispatch(request, self.start_response)
    self.mox.VerifyAll()

    logging.warning('Config %s', self.server.config_manager.configs)

    self.assertEqual(self.response_status, '400 Bad Request')
    body = ''.join(response)
    body_json = json.loads(body)
    self.assertEqual(1, len(body_json['error']['errors']))
    self.assertEqual('gid', body_json['error']['errors'][0]['location'])
    self.assertEqual('invalidParameter',
                     body_json['error']['errors'][0]['reason'])

  def test_dispatch_spi_error(self):
    """Check the error response if the SPI returns an error."""
    config = json.dumps({
        'name': 'guestbook_api',
        'version': 'v1',
        'methods': {
            'guestbook.get': {
                'httpMethod': 'GET',
                'path': 'greetings/{gid}',
                'rosyMethod': 'MyApi.greetings_get'
            }
        }
    })
    request = test_utils.build_request('/_ah/api/foo')
    self.prepare_dispatch(config)
    self.mox.StubOutWithMock(self.server, 'call_spi')
    # The application chose to throw a 404 error.
    response = dispatcher.ResponseTuple('404 Not Found', [],
                                        ('{"state": "APPLICATION_ERROR",'
                                         ' "error_message": "Test error"}'))
    self.server.call_spi(request, mox.IgnoreArg()).AndRaise(
        errors.BackendError(response))

    self.mox.ReplayAll()
    response = self.server.dispatch(request, self.start_response)
    self.mox.VerifyAll()

    expected_response = (
        '{\n'
        ' "error": {\n'
        '  "code": 404, \n'
        '  "errors": [\n'
        '   {\n'
        '    "domain": "global", \n'
        '    "message": "Test error", \n'
        '    "reason": "notFound"\n'
        '   }\n'
        '  ], \n'
        '  "message": "Test error"\n'
        ' }\n'
        '}')
    response = ''.join(response)
    self.assert_http_match(response, '404 Not Found',
                           [('Content-Length', '%d' % len(expected_response)),
                            ('Content-Type', 'application/json')],
                           expected_response)

  def test_dispatch_rpc_error(self):
    """Test than an RPC call that returns an error is handled properly."""
    config = json.dumps({
        'name': 'guestbook_api',
        'version': 'v1',
        'methods': {
            'guestbook.get': {
                'httpMethod': 'GET',
                'path': 'greetings/{gid}',
                'rosyMethod': 'MyApi.greetings_get'
            }
        }
    })
    request = test_utils.build_request(
        '/_ah/api/rpc',
        '{"method": "foo.bar", "apiVersion": "X", "id": "gapiRpc"}')
    self.prepare_dispatch(config)
    self.mox.StubOutWithMock(self.server, 'call_spi')
    # The application chose to throw a 404 error.
    response = dispatcher.ResponseTuple('404 Not Found', [],
                                        ('{"state": "APPLICATION_ERROR",'
                                         ' "error_message": "Test error"}'))
    self.server.call_spi(request, mox.IgnoreArg()).AndRaise(
        errors.BackendError(response))

    self.mox.ReplayAll()
    response = self.server.dispatch(request, self.start_response)
    self.mox.VerifyAll()

    expected_response = {'error': {'code': 404,
                                   'message': 'Test error',
                                   'data': [{
                                       'domain': 'global',
                                       'reason': 'notFound',
                                       'message': 'Test error',
                                       }]
                                  },
                         'id': 'gapiRpc'
                        }
    response = ''.join(response)
    self.assertEqual('200 OK', self.response_status)
    self.assertEqual(expected_response, json.loads(response))

  def test_dispatch_json_rpc(self):
    config = json.dumps({
        'name': 'guestbook_api',
        'version': 'X',
        'methods': {
            'foo.bar': {
                'httpMethod': 'GET',
                'path': 'greetings/{gid}',
                'rosyMethod': 'baz.bim'
            }
        }
    })
    request = test_utils.build_request(
        '/_ah/api/rpc',
        '{"method": "foo.bar", "apiVersion": "X"}')
    self.assert_dispatch_to_spi(request, config,
                                '/_ah/spi/baz.bim')

  def test_dispatch_rest(self):
    config = json.dumps({
        'name': 'myapi',
        'version': 'v1',
        'methods': {
            'bar': {
                'httpMethod': 'GET',
                'path': 'foo/{id}',
                'rosyMethod': 'baz.bim'
            }
        }
    })
    request = test_utils.build_request('/_ah/api/myapi/v1/foo/testId')
    self.assert_dispatch_to_spi(request, config,
                                '/_ah/spi/baz.bim',
                                {'id': 'testId'})

  def test_explorer_redirect(self):
    request = test_utils.build_request('/_ah/api/explorer')
    response = self.server.dispatch(request, self.start_response)
    self.assert_http_match(response, 302,
                           [('Content-Length', '0'),
                            ('Location', ('http://apis-explorer.appspot.com/'
                                          'apis-explorer/?base='
                                          'http://localhost:42/_ah/api'))],
                           '')

  def test_static_existing_file(self):
    relative_url = '/_ah/api/static/proxy.html'

    # Set up mocks for the call to DiscoveryApiProxy.get_static_file.
    discovery_api = self.mox.CreateMock(
        discovery_api_proxy.DiscoveryApiProxy)
    self.mox.StubOutWithMock(discovery_api_proxy, 'DiscoveryApiProxy')
    discovery_api_proxy.DiscoveryApiProxy().AndReturn(discovery_api)
    static_response = self.mox.CreateMock(httplib.HTTPResponse)
    static_response.status = 200
    static_response.reason = 'OK'
    static_response.getheader('Content-Type').AndReturn('test/type')
    test_body = 'test body'
    discovery_api.get_static_file(relative_url).AndReturn(
        (static_response, test_body))

    # Make sure the dispatch works as expected.
    request = test_utils.build_request(relative_url)
    self.mox.ReplayAll()
    response = self.server.dispatch(request, self.start_response)
    self.mox.VerifyAll()

    response = ''.join(response)
    self.assert_http_match(response, '200 OK',
                           [('Content-Length', '%d' % len(test_body)),
                            ('Content-Type', 'test/type')],
                           test_body)

  def test_static_non_existing_file(self):
    relative_url = '/_ah/api/static/blah.html'

    # Set up mocks for the call to DiscoveryApiProxy.get_static_file.
    discovery_api = self.mox.CreateMock(
        discovery_api_proxy.DiscoveryApiProxy)
    self.mox.StubOutWithMock(discovery_api_proxy, 'DiscoveryApiProxy')
    discovery_api_proxy.DiscoveryApiProxy().AndReturn(discovery_api)
    static_response = self.mox.CreateMock(httplib.HTTPResponse)
    static_response.status = 404
    static_response.reason = 'Not Found'
    static_response.getheaders().AndReturn([('Content-Type', 'test/type')])
    test_body = 'No Body'
    discovery_api.get_static_file(relative_url).AndReturn(
        (static_response, test_body))

    # Make sure the dispatch works as expected.
    request = test_utils.build_request(relative_url)
    self.mox.ReplayAll()
    response = self.server.dispatch(request, self.start_response)
    self.mox.VerifyAll()

    response = ''.join(response)
    self.assert_http_match(response, '404 Not Found',
                           [('Content-Length', '%d' % len(test_body)),
                            ('Content-Type', 'test/type')],
                           test_body)

  def test_handle_non_json_spi_response(self):
    orig_request = test_utils.build_request('/_ah/api/fake/path')
    spi_request = orig_request.copy()
    spi_response = dispatcher.ResponseTuple(
        200, [('Content-type', 'text/plain')],
        'This is an invalid response.')
    response = self.server.handle_spi_response(orig_request, spi_request,
                                               spi_response, {},
                                               self.start_response)
    error_json = {'error': {'message':
                            'Non-JSON reply: This is an invalid response.'}}
    body = json.dumps(error_json)
    self.assert_http_match(response, '500',
                           [('Content-Type', 'application/json'),
                            ('Content-Length', '%d' % len(body))],
                           body)

  def test_handle_non_json_spi_response_cors(self):
    """Test that an error response still handles CORS headers."""
    server_response = dispatcher.ResponseTuple(
        '200 OK', [('Content-type', 'text/plain')],
        'This is an invalid response.')
    response = self.check_cors([('origin', 'test.com')], True, 'test.com',
                               server_response=server_response)
    self.assertEqual(
        {'error': {'message': 'Non-JSON reply: This is an invalid response.'}},
        json.loads(response))

  def check_cors(self, request_headers, expect_response, expected_origin=None,
                 expected_allow_headers=None, server_response=None):
    """Check that CORS headers are handled correctly.

    Args:
      request_headers: A list of (header, value), to be used as headers in the
        request.
      expect_response: A boolean, whether or not CORS headers are expected in
        the response.
      expected_origin: A string or None.  If this is a string, this is the value
        that's expected in the response's allow origin header.  This can be
        None if expect_response is False.
      expected_allow_headers: A string or None.  If this is a string, this is
        the value that's expected in the response's allow headers header.  If
        this is None, then the response shouldn't have any allow headers
        headers.
      server_response: A dispatcher.ResponseTuple or None.  The backend's
        response, to be wrapped and returned as the server's response.  If
        this is None, a generic response will be generated.

    Returns:
      A string containing the body of the response that would be sent.
    """
    orig_request = test_utils.build_request('/_ah/api/fake/path',
                                            http_headers=request_headers)
    spi_request = orig_request.copy()

    if server_response is None:
      server_response = dispatcher.ResponseTuple(
          '200 OK', [('Content-type', 'application/json')], '{}')

    response = self.server.handle_spi_response(orig_request, spi_request,
                                               server_response, {},
                                               self.start_response)

    headers = dict(self.response_headers)
    if expect_response:
      self.assertIn(endpoints_server._CORS_HEADER_ALLOW_ORIGIN, headers)
      self.assertEqual(
          headers[endpoints_server._CORS_HEADER_ALLOW_ORIGIN],
          expected_origin)

      self.assertIn(endpoints_server._CORS_HEADER_ALLOW_METHODS, headers)
      self.assertEqual(set(headers[
          endpoints_server._CORS_HEADER_ALLOW_METHODS].split(',')),
                       endpoints_server._CORS_ALLOWED_METHODS)

      if expected_allow_headers is not None:
        self.assertIn(endpoints_server._CORS_HEADER_ALLOW_HEADERS,
                      headers)
        self.assertEqual(
            headers[endpoints_server._CORS_HEADER_ALLOW_HEADERS],
            expected_allow_headers)
      else:
        self.assertNotIn(endpoints_server._CORS_HEADER_ALLOW_HEADERS,
                         headers)
    else:
      self.assertNotIn(endpoints_server._CORS_HEADER_ALLOW_ORIGIN,
                       headers)
      self.assertNotIn(endpoints_server._CORS_HEADER_ALLOW_METHODS,
                       headers)
      self.assertNotIn(endpoints_server._CORS_HEADER_ALLOW_HEADERS,
                       headers)
    return ''.join(response)

  def test_handle_cors(self):
    """Test CORS support on a regular request."""
    self.check_cors([('origin', 'test.com')], True, 'test.com')

  def test_handle_cors_preflight(self):
    """Test a CORS preflight request."""
    self.check_cors([('origin', 'http://example.com'),
                     ('Access-control-request-method', 'GET')], True,
                    'http://example.com')

  def test_handle_cors_preflight_invalid(self):
    """Test a CORS preflight request for an unaccepted OPTIONS request."""
    self.check_cors([('origin', 'http://example.com'),
                     ('Access-control-request-method', 'OPTIONS')], False)

  def test_handle_cors_preflight_request_headers(self):
    """Test a CORS preflight request."""
    self.check_cors([('origin', 'http://example.com'),
                     ('Access-control-request-method', 'GET'),
                     ('Access-Control-Request-Headers', 'Date,Expires')], True,
                    'http://example.com', 'Date,Expires')

  def test_lily_uses_python_method_name(self):
    """Verify Lily protocol correctly uses python method name.

    This test verifies the fix to http://b/7189819
    """
    config = json.dumps({
        'name': 'guestbook_api',
        'version': 'X',
        'methods': {
            'author.greeting.info.get': {
                'httpMethod': 'GET',
                'path': 'authors/{aid}/greetings/{gid}/infos/{iid}',
                'rosyMethod': 'InfoService.get'
            }
        }
    })
    request = test_utils.build_request(
        '/_ah/api/rpc',
        '{"method": "author.greeting.info.get", "apiVersion": "X"}')
    self.assert_dispatch_to_spi(request, config,
                                '/_ah/spi/InfoService.get',
                                {})

  def test_handle_spi_response_json_rpc(self):
    """Verify headers transformed, JsonRpc response transformed, written."""
    orig_request = test_utils.build_request(
        '/_ah/api/rpc', '{"method": "foo.bar", "apiVersion": "X"}')
    self.assertTrue(orig_request.is_rpc())
    orig_request.request_id = 'Z'
    spi_request = orig_request.copy()
    spi_response = dispatcher.ResponseTuple('200 OK', [('a', 'b')],
                                            '{"some": "response"}')

    response = self.server.handle_spi_response(orig_request, spi_request,
                                               spi_response, {},
                                               self.start_response)
    response = ''.join(response)  # Merge response iterator into single body.

    self.assertEqual(self.response_status, '200 OK')
    self.assertIn(('a', 'b'), self.response_headers)
    self.assertEqual({'id': 'Z', 'result': {'some': 'response'}},
                     json.loads(response))

  def test_handle_spi_response_batch_json_rpc(self):
    """Verify that batch requests have an appropriate batch response."""
    orig_request = test_utils.build_request(
        '/_ah/api/rpc', '[{"method": "foo.bar", "apiVersion": "X"}]')
    self.assertTrue(orig_request.is_batch())
    self.assertTrue(orig_request.is_rpc())
    orig_request.request_id = 'Z'
    spi_request = orig_request.copy()
    spi_response = dispatcher.ResponseTuple('200 OK', [('a', 'b')],
                                            '{"some": "response"}')

    response = self.server.handle_spi_response(orig_request, spi_request,
                                               spi_response, {},
                                               self.start_response)
    response = ''.join(response)  # Merge response iterator into single body.

    self.assertEqual(self.response_status, '200 OK')
    self.assertIn(('a', 'b'), self.response_headers)
    self.assertEqual([{'id': 'Z', 'result': {'some': 'response'}}],
                     json.loads(response))

  def test_handle_spi_response_rest(self):
    orig_request = test_utils.build_request('/_ah/api/test', '{}')
    spi_request = orig_request.copy()
    body = json.dumps({'some': 'response'}, indent=1)
    spi_response = dispatcher.ResponseTuple('200 OK', [('a', 'b')], body)
    response = self.server.handle_spi_response(orig_request, spi_request,
                                               spi_response, {},
                                               self.start_response)
    self.assert_http_match(response, '200 OK',
                           [('a', 'b'),
                            ('Content-Length', '%d' % len(body))],
                           body)

  def test_transform_rest_response(self):
    """Verify the response is reformatted correctly."""
    orig_response = '{"sample": "test", "value1": {"value2": 2}}'
    expected_response = ('{\n'
                         ' "sample": "test", \n'
                         ' "value1": {\n'
                         '  "value2": 2\n'
                         ' }\n'
                         '}')
    self.assertEqual(expected_response,
                     self.server.transform_rest_response(orig_response))

  def test_transform_json_rpc_response_batch(self):
    """Verify request_id inserted into the body, and body into body.result."""
    orig_request = test_utils.build_request(
        '/_ah/api/rpc', '[{"params": {"sample": "body"}, "id": "42"}]')
    request = orig_request.copy()
    request.request_id = '42'
    orig_response = '{"sample": "body"}'
    response = self.server.transform_jsonrpc_response(request, orig_response)
    self.assertEqual([{'result': {'sample': 'body'}, 'id': '42'}],
                     json.loads(response))

  def test_lookup_rpc_method_no_body(self):
    orig_request = test_utils.build_request('/_ah/api/rpc', '')
    self.assertEqual(None, self.server.lookup_rpc_method(orig_request))

  def test_lookup_rpc_method(self):
    self.mox.StubOutWithMock(self.server.config_manager, 'lookup_rpc_method')
    self.server.config_manager.lookup_rpc_method('foo', 'v1').AndReturn('bar')

    self.mox.ReplayAll()
    orig_request = test_utils.build_request(
        '/_ah/api/rpc', '{"method": "foo", "apiVersion": "v1"}')
    self.assertEqual('bar', self.server.lookup_rpc_method(orig_request))
    self.mox.VerifyAll()

  def test_verify_response(self):
    response = dispatcher.ResponseTuple('200', [('Content-Type', 'a')], '')
    # Expected response
    self.assertEqual(True, self.server.verify_response(response, 200, 'a'))
    # Any content type accepted
    self.assertEqual(True, self.server.verify_response(response, 200, None))
    # Status code mismatch
    self.assertEqual(False, self.server.verify_response(response, 400, 'a'))
    # Content type mismatch
    self.assertEqual(False, self.server.verify_response(response, 200, 'b'))

    response = dispatcher.ResponseTuple('200', [('Content-Length', '10')], '')
    # Any content type accepted
    self.assertEqual(True, self.server.verify_response(response, 200, None))
    # Specified content type not matched
    self.assertEqual(False, self.server.verify_response(response, 200, 'a'))

  def test_check_empty_response(self):
    """Test that check_empty_response returns 204 for an empty response."""
    orig_request = test_utils.build_request('/_ah/api/test', '{}')
    method_config = {'response': {'body': 'empty'}}
    empty_response = self.server.check_empty_response(orig_request,
                                                      method_config,
                                                      self.start_response)
    self.assert_http_match(empty_response, 204, [('Content-Length', '0')], '')

  def test_check_non_empty_response(self):
    """Test that check_empty_response returns None for a non-empty response."""
    orig_request = test_utils.build_request('/_ah/api/test', '{}')
    method_config = {'response': {'body': 'autoTemplate(backendResponse)'}}
    empty_response = self.server.check_empty_response(orig_request,
                                                      method_config,
                                                      self.start_response)
    self.assertIsNone(empty_response)
    self.assertIsNone(self.response_status)
    self.assertIsNone(self.response_headers)
    self.assertIsNone(self.response_exc_info)


class TransformRequestTests(unittest.TestCase):
  """Tests that only hit the request transformation functions."""

  def setUp(self):
    """Set up a dev Endpoints server."""
    super(TransformRequestTests, self).setUp()
    self.mox = mox.Mox()
    self.config_manager = api_config_manager.ApiConfigManager()
    self.mock_dispatcher = self.mox.CreateMock(dispatcher.Dispatcher)
    self.server = endpoints_server.EndpointsDispatcher(self.mock_dispatcher,
                                                       self.config_manager)

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_transform_request(self):
    """Verify path is method name after a request is transformed."""
    request = test_utils.build_request('/_ah/api/test/{gid}',
                                       '{"sample": "body"}')
    method_config = {'rosyMethod': 'GuestbookApi.greetings_get'}

    new_request = self.server.transform_request(request, {'gid': 'X'},
                                                method_config)
    self.assertEqual({'sample': 'body', 'gid': 'X'},
                     json.loads(new_request.body))
    self.assertEqual('GuestbookApi.greetings_get', new_request.path)

  def test_transform_json_rpc_request(self):
    """Verify request_id is extracted and body is scoped to body.params."""
    orig_request = test_utils.build_request(
        '/_ah/api/rpc', '{"params": {"sample": "body"}, "id": "42"}')

    new_request = self.server.transform_jsonrpc_request(orig_request)
    self.assertEqual({'sample': 'body'},
                     json.loads(new_request.body))
    self.assertEqual('42', new_request.request_id)

  def _try_transform_rest_request(self, path_parameters, query_parameters,
                                  body_json, expected, method_params=None):
    """Takes body, query and path values from a rest request for testing.

    Args:
      path_parameters: A dict containing the parameters parsed from the path.
        For example if the request came through /a/b for the template /a/{x}
        then we'd have {'x': 'b'}.
      query_parameters: A dict containing the parameters parsed from the query
        string.
      body_json: A dict with the JSON object from the request body.
      expected: A dict with the expected JSON body after being transformed.
      method_params: Optional dictionary specifying the parameter configuration
        associated with the method.
    """
    method_params = method_params or {}

    test_request = test_utils.build_request('/_ah/api/test')
    test_request.body_json = body_json
    test_request.body = json.dumps(body_json)
    test_request.parameters = query_parameters

    transformed_request = self.server.transform_rest_request(test_request,
                                                             path_parameters,
                                                             method_params)

    self.assertEqual(expected, transformed_request.body_json)
    self.assertEqual(transformed_request.body_json,
                     json.loads(transformed_request.body))

  # Path only

  def test_transform_rest_request_path_only(self):
    path_parameters = {'gid': 'X'}
    query_parameters = {}
    body_object = {}
    expected = {'gid': 'X'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_path_only_message_field(self):
    path_parameters = {'gid.val': 'X'}
    query_parameters = {}
    body_object = {}
    expected = {'gid': {'val': 'X'}}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_path_only_enum(self):
    query_parameters = {}
    body_object = {}
    enum_descriptor = {'X': {'backendValue': 'X'}}
    method_params = {'gid': {'enum': enum_descriptor}}

    # Good enum
    path_parameters = {'gid': 'X'}
    expected = {'gid': 'X'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected,
                                     method_params=method_params)

    # Bad enum
    path_parameters = {'gid': 'Y'}
    expected = {'gid': 'Y'}
    try:
      self._try_transform_rest_request(path_parameters, query_parameters,
                                       body_object, expected,
                                       method_params=method_params)
      self.fail('Bad enum should have caused failure.')
    except errors.EnumRejectionError as error:
      self.assertEqual(error.parameter_name, 'gid')

  # Query only

  def test_transform_rest_request_query_only(self):
    path_parameters = {}
    query_parameters = {'foo': ['bar']}
    body_object = {}
    expected = {'foo': 'bar'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_query_only_message_field(self):
    path_parameters = {}
    query_parameters = {'gid.val': ['X']}
    body_object = {}
    expected = {'gid': {'val': 'X'}}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_query_only_multiple_values_not_repeated(self):
    path_parameters = {}
    query_parameters = {'foo': ['bar', 'baz']}
    body_object = {}
    expected = {'foo': 'bar'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_query_only_multiple_values_repeated(self):
    path_parameters = {}
    query_parameters = {'foo': ['bar', 'baz']}
    body_object = {}
    method_params = {'foo': {'repeated': True}}
    expected = {'foo': ['bar', 'baz']}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected,
                                     method_params=method_params)

  def test_transform_rest_request_query_only_enum(self):
    path_parameters = {}
    body_object = {}
    enum_descriptor = {'X': {'backendValue': 'X'}}
    method_params = {'gid': {'enum': enum_descriptor}}

    # Good enum
    query_parameters = {'gid': ['X']}
    expected = {'gid': 'X'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected,
                                     method_params=method_params)

    # Bad enum
    query_parameters = {'gid': ['Y']}
    expected = {'gid': 'Y'}
    try:
      self._try_transform_rest_request(path_parameters, query_parameters,
                                       body_object, expected,
                                       method_params=method_params)
      self.fail('Bad enum should have caused failure.')
    except errors.EnumRejectionError as error:
      self.assertEqual(error.parameter_name, 'gid')

  def test_transform_rest_request_query_only_repeated_enum(self):
    path_parameters = {}
    body_object = {}
    enum_descriptor = {'X': {'backendValue': 'X'}, 'Y': {'backendValue': 'Y'}}
    method_params = {'gid': {'enum': enum_descriptor, 'repeated': True}}

    # Good enum
    query_parameters = {'gid': ['X', 'Y']}
    expected = {'gid': ['X', 'Y']}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected,
                                     method_params=method_params)

    # Bad enum
    query_parameters = {'gid': ['X', 'Y', 'Z']}
    expected = {'gid': ['X', 'Y', 'Z']}
    try:
      self._try_transform_rest_request(path_parameters, query_parameters,
                                       body_object, expected,
                                       method_params=method_params)
      self.fail('Bad enum should have caused failure.')
    except errors.EnumRejectionError as error:
      self.assertEqual(error.parameter_name, 'gid[2]')

  # Body only

  def test_transform_rest_request_body_only(self):
    path_parameters = {}
    query_parameters = {}
    body_object = {'sample': 'body'}
    expected = {'sample': 'body'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_body_only_any_old_value(self):
    path_parameters = {}
    query_parameters = {}
    body_object = {'sample': {'body': ['can', 'be', 'anything']}}
    expected = {'sample': {'body': ['can', 'be', 'anything']}}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_body_only_message_field(self):
    path_parameters = {}
    query_parameters = {}
    body_object = {'gid': {'val': 'X'}}
    expected = {'gid': {'val': 'X'}}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_body_only_enum(self):
    path_parameters = {}
    query_parameters = {}
    enum_descriptor = {'X': {'backendValue': 'X'}}
    method_params = {'gid': {'enum': enum_descriptor}}

    # Good enum
    body_object = {'gid': 'X'}
    expected = {'gid': 'X'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected,
                                     method_params=method_params)

    # Bad enum
    body_object = {'gid': 'Y'}
    expected = {'gid': 'Y'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected,
                                     method_params=method_params)

  # Path and query only

  def test_transform_rest_request_path_query_no_collision(self):
    path_parameters = {'a': 'b'}
    query_parameters = {'c': ['d']}
    body_object = {}
    expected = {'a': 'b', 'c': 'd'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_path_query_collision(self):
    path_parameters = {'a': 'b'}
    query_parameters = {'a': ['d']}
    body_object = {}
    expected = {'a': 'd'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_path_query_collision_in_repeated_param(self):
    path_parameters = {'a': 'b'}
    query_parameters = {'a': ['d', 'c']}
    body_object = {}
    expected = {'a': ['d', 'c', 'b']}
    method_params = {'a': {'repeated': True}}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected,
                                     method_params=method_params)

  # Path and body only

  def test_transform_rest_request_path_body_no_collision(self):
    path_parameters = {'a': 'b'}
    query_parameters = {}
    body_object = {'c': 'd'}
    expected = {'a': 'b', 'c': 'd'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_path_body_collision(self):
    path_parameters = {'a': 'b'}
    query_parameters = {}
    body_object = {'a': 'd'}
    expected = {'a': 'd'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_path_body_collision_in_repeated_param(self):
    path_parameters = {'a': 'b'}
    query_parameters = {}
    body_object = {'a': ['d']}
    expected = {'a': ['d']}
    method_params = {'a': {'repeated': True}}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected,
                                     method_params=method_params)

  def test_transform_rest_request_path_body_message_field_cooperative(self):
    path_parameters = {'gid.val1': 'X'}
    query_parameters = {}
    body_object = {'gid': {'val2': 'Y'}}
    expected = {'gid': {'val1': 'X', 'val2': 'Y'}}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_path_body_message_field_collision(self):
    path_parameters = {'gid.val': 'X'}
    query_parameters = {}
    body_object = {'gid': {'val': 'Y'}}
    expected = {'gid': {'val': 'Y'}}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  # Query and body only

  def test_transform_rest_request_query_body_no_collision(self):
    path_parameters = {}
    query_parameters = {'a': ['b']}
    body_object = {'c': 'd'}
    expected = {'a': 'b', 'c': 'd'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_query_body_collision(self):
    path_parameters = {}
    query_parameters = {'a': ['b']}
    body_object = {'a': 'd'}
    expected = {'a': 'd'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_query_body_collision_in_repeated_param(self):
    path_parameters = {}
    query_parameters = {'a': ['b']}
    body_object = {'a': ['d']}
    expected = {'a': ['d']}
    method_params = {'a': {'repeated': True}}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected,
                                     method_params=method_params)

  def test_transform_rest_request_query_body_message_field_cooperative(self):
    path_parameters = {}
    query_parameters = {'gid.val1': ['X']}
    body_object = {'gid': {'val2': 'Y'}}
    expected = {'gid': {'val1': 'X', 'val2': 'Y'}}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_query_body_message_field_collision(self):
    path_parameters = {}
    query_parameters = {'gid.val': ['X']}
    body_object = {'gid': {'val': 'Y'}}
    expected = {'gid': {'val': 'Y'}}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  # Path, body and query

  def test_transform_rest_request_path_query_body_no_collision(self):
    path_parameters = {'a': 'b'}
    query_parameters = {'c': ['d']}
    body_object = {'e': 'f'}
    expected = {'a': 'b', 'c': 'd', 'e': 'f'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_path_query_body_collision(self):
    path_parameters = {'a': 'b'}
    query_parameters = {'a': ['d']}
    body_object = {'a': 'f'}
    expected = {'a': 'f'}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected)

  def test_transform_rest_request_unknown_parameters(self):
    path_parameters = {'a': 'b'}
    query_parameters = {'c': ['d']}
    body_object = {'e': 'f'}
    expected = {'a': 'b', 'c': 'd', 'e': 'f'}
    method_params = {'X': {}, 'Y': {}}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected,
                                     method_params=method_params)

  # Other tests.

  def test_type_conversions(self):
    """Verify that type conversion matches prod."""
    path_parameters = {'int32_val': '1', 'uint32_val': '2',
                       'int64_val': '3', 'uint64_val': '4',
                       'true_bool_val': 'true', 'false_bool_val': 'FALSE'}
    query_parameters = {'float_val': ['5.25'], 'double_val': ['6.5']}
    body_object = {'int_body_val': '7'}
    expected = {'int32_val': 1,
                'uint32_val': 2,
                'int64_val': '3',
                'uint64_val': '4',
                'true_bool_val': True,
                'false_bool_val': False,
                'float_val': 5.25,
                'double_val': 6.5,
                'int_body_val': '7'}
    method_params = {'int32_val': {'type': 'int32'},
                     'uint32_val': {'type': 'uint32'},
                     'int64_val': {'type': 'int64'},
                     'uint64_val': {'type': 'uint64'},
                     'true_bool_val': {'type': 'boolean'},
                     'false_bool_val': {'type': 'boolean'},
                     'float_val': {'type': 'float'},
                     'double_val': {'type': 'double'},
                     'int_body_val': {'type': 'int32'}}
    self._try_transform_rest_request(path_parameters, query_parameters,
                                     body_object, expected, method_params)

  def test_invalid_conversions(self):
    """Verify that invalid parameter values for basic types raise errors."""
    for type_name in ('int32', 'uint32', 'boolean', 'float', 'double'):
      param_name = '%s_val' % type_name
      path_parameters = {param_name: 'invalid'}
      query_parameters = {}
      body_object = {}
      expected = {}
      method_params = {param_name: {'type': type_name}}

      try:
        self._try_transform_rest_request(path_parameters, query_parameters,
                                         body_object, expected,
                                         method_params=method_params)
        self.fail('Bad %s value should have caused failure.' % type_name)
      except errors.BasicTypeParameterError as error:
        self.assertEqual(error.parameter_name, param_name)

if __name__ == '__main__':
  unittest.main()
