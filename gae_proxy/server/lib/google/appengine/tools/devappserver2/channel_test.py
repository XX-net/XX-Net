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
"""Tests for google.appengine.tools.devappserver2.channel."""




import StringIO
import unittest
import urllib

from google.appengine.api.channel import channel_service_stub
from google.appengine.tools.devappserver2 import channel
from google.appengine.tools.devappserver2 import wsgi_test_utils


class MockChannelServiceStub(object):
  """Mock channel service to return known messages for testing."""

  def __init__(self):
    self._messages = {}
    self._connected_channel_tokens = []
    self._disconnected_channel_client_ids = []

  def set_messages(self, messages):
    self._messages = messages

  def has_channel_messages(self, token):
    return (self._messages.has_key(token) and
            self._messages[token])

  def get_channel_messages(self, token):
    return self._messages[token]

  def pop_first_message(self, token):
    if self.has_channel_messages(token):
      return self._messages[token].pop(0)
    else:
      return None

  def clear_channel_messages(self, token):
    del self._messages[token]

  def connect_channel(self, token):
    self.validate_token_and_extract_client_id(token)
    self._connected_channel_tokens.append(token)

  def disconnect_channel(self, client_id):
    self._disconnected_channel_client_ids.append(client_id)

  def get_connected_tokens(self):
    return self._connected_channel_tokens

  def set_connected_tokens(self, tokens):
    self._connected_tokens = tokens

  def validate_token_and_extract_client_id(self, token):
    if token == 'bad':
      raise channel_service_stub.InvalidTokenError()
    if token == 'expired':
      raise channel_service_stub.TokenTimedOutError()
    return 'dummy-client-id'

  def connect_and_pop_first_message(self, token):
    self.connect_channel(token)
    return self.pop_first_message(token)


def _build_environ(path, query=None):
  environ = {
      'REQUEST_METHOD': 'GET',
      'PATH_INFO': path,
  }
  if query:
    environ['QUERY_STRING'] = urllib.urlencode(query)
  return environ


def _build_poll_environ(token):
  """Build an environ for a WSGI request that performs a channel poll.

  Args:
    token: The channel to poll.
  """
  return _build_environ('/_ah/channel/dev',
                        {'command': 'poll', 'channel': token})


class DevAppserverChannelTest(wsgi_test_utils.WSGITestCase):
  """Test the dev appserver channel module."""

  def setUp(self):
    """Set up the mocks and output objects for tests."""
    self._mock_channel_service_stub = MockChannelServiceStub()
    self._old_get_channel_stub = channel._get_channel_stub
    channel._get_channel_stub = lambda: self._mock_channel_service_stub
    self._channel_app = channel.application
    self._output = StringIO.StringIO()

  def tearDown(self):
    channel._get_channel_stub = self._old_get_channel_stub

  def test_channel_request_no_messages(self):
    """Test a channel request with no pending messages."""
    environ = _build_poll_environ('id')
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '0',
    }
    self.assertResponse('200 OK', expected_headers, '', channel.application,
                        environ)

  def test_channel_request_missing_parameters(self):
    """Test a channel request with missing query string parameters."""
    environ = _build_environ('/_ah/channel/dev', {'command': 'poll'})
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '0',
    }
    self.assertResponse('400 Bad Request', expected_headers, '',
                        channel.application, environ)

    environ = _build_environ('/_ah/channel/dev', {'channel': 'id'})
    self.assertResponse('400 Bad Request', expected_headers, '',
                        channel.application, environ)

  def test_channel_request_bad_command(self):
    """Test a channel request with an invalid command."""
    environ = _build_environ('/_ah/channel/dev', {'command': 'bad',
                                                  'channel': 'id'})
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '0',
    }
    self.assertResponse('400 Bad Request', expected_headers, '',
                        channel.application, environ)

  def test_channel_request_bad_token(self):
    """Test a channel request with an invalid token."""
    environ = _build_poll_environ('bad')
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '0',
    }
    self.assertResponse('401 Invalid+token.', expected_headers, '',
                        channel.application, environ)

  def test_channel_request_expired_token(self):
    """Test a channel request with an expired token."""
    environ = _build_poll_environ('expired')
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '0',
    }
    self.assertResponse('401 Token+timed+out.', expected_headers, '',
                        channel.application, environ)

  def test_channel_request_other_channel_has_messages(self):
    """Test a channel request with another channel with messages."""
    self._mock_channel_service_stub.set_messages({'a': ['hello']})
    environ = _build_poll_environ('b')
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '0',
    }
    self.assertResponse('200 OK', expected_headers, '', channel.application,
                        environ)

  def test_channel_request_with_messages(self):
    """Test a channel request with a channel that has a message."""
    self._mock_channel_service_stub.set_messages({'a': ['hello']})
    environ = _build_poll_environ('a')
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '5',
        'Content-Type': 'application/json',
    }
    self.assertResponse('200 OK', expected_headers, 'hello',
                        channel.application, environ)

  def test_channel_request_empty_message(self):
    """Test a channel request with a channel that has a 0-length message."""
    self._mock_channel_service_stub.set_messages({'a': ['']})
    environ = _build_poll_environ('a')
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '0',
        'Content-Type': 'application/json',
    }
    self.assertResponse('200 OK', expected_headers, '', channel.application,
                        environ)

  def test_channel_request_with_multiple_messages(self):
    """Test a channel request with a channel that has multiple messages."""
    self._mock_channel_service_stub.set_messages({'a': ['hello', 'goodbye']})
    environ = _build_poll_environ('a')
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '5',
        'Content-Type': 'application/json',
    }
    self.assertResponse('200 OK', expected_headers, 'hello',
                        channel.application, environ)
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '7',
        'Content-Type': 'application/json',
    }
    self.assertResponse('200 OK', expected_headers, 'goodbye',
                        channel.application, environ)

  def test_channel_request_clears_messages(self):
    """Test that request a channel's messages clears those messages."""
    self._mock_channel_service_stub.set_messages({'a': ['hello']})
    environ = _build_poll_environ('a')
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '5',
        'Content-Type': 'application/json',
    }
    self.assertResponse('200 OK', expected_headers, 'hello',
                        channel.application, environ)
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '0',
    }
    self.assertResponse('200 OK', expected_headers, '', channel.application,
                        environ)

  def test_channel_request_clears_correct_messages(self):
    """Test that request a channel's messages clears only those messages."""
    self._mock_channel_service_stub.set_messages({'a': ['hello'],
                                                  'b': ['goodbye']})
    environ = _build_poll_environ('a')
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '5',
        'Content-Type': 'application/json',
    }
    self.assertResponse('200 OK', expected_headers, 'hello',
                        channel.application, environ)
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '0',
    }
    self.assertResponse('200 OK', expected_headers, '', channel.application,
                        environ)
    environ = _build_poll_environ('b')
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '7',
        'Content-Type': 'application/json',
    }
    self.assertResponse('200 OK', expected_headers, 'goodbye',
                        channel.application, environ)

  def test_channel_request_connects_channel(self):
    """Ensure that a channel request causes the channel to be connected."""
    mock_stub = self._mock_channel_service_stub
    mock_stub.set_connected_tokens([])
    environ = _build_poll_environ('id')
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': '0',
    }
    self.assertResponse('200 OK', expected_headers, '', channel.application,
                        environ)
    self.assertListEqual(['id'], mock_stub.get_connected_tokens())

  def test_channel_request_jsapi(self):
    """Test that requesting the jsapi script returns expected result."""
    environ = _build_environ('/_ah/channel/jsapi')
    # Read the JS API file to test that it matches.
    js_text = open(channel._JSAPI_PATH).read()
    expected_headers = {
        'Cache-Control': 'no-cache',
        'Content-Length': str(len(js_text)),
        'Content-Type': 'text/javascript',
    }
    self.assertResponse('200 OK', expected_headers, js_text,
                        channel.application, environ)


if __name__ == '__main__':
  unittest.main()
