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
"""Tests for devappserver2.request_rewriter."""



import functools
import sys
import time
import unittest

import google
import mox

from google.appengine.tools.devappserver2 import request_rewriter
from google.appengine.tools.devappserver2 import wsgi_test_utils


class RewriterMiddlewareTest(wsgi_test_utils.RewriterTestCase):
  """Tests the response rewriter middleware."""

  def setUp(self):
    """Replace the rewriter chain with a series of dummy rewriters."""
    # Used for remembering calls to rewriters.
    self.initial_calls = 0
    self.chain_calls = 0
    self.modify_calls = 0
    # Individual cases can set these to False to prevent the rewriters from
    # checking the expected status and/or body.
    self.test_status = True
    self.test_body = True

    def check_initial_response(state):
      self.assertEquals('Environ value', state.environ['ENVIRON_KEY'])
      if self.test_status:
        self.assertEquals('200 Good to go', state.status)
      self.assertEquals('Some value', state.headers['SomeHeader'])

      # Convert state.body into a list to allow multiple traversals.
      state.body = list(state.body)
      if self.test_body:
        self.assertEquals('Original content', ''.join(state.body))

      self.initial_calls += 1

    def check_chain(unused_state):
      self.chain_calls += 1

    def modify_status(state):
      if self.test_status:
        self.assertEquals('200 Good to go', state.status)
      if not state.status.startswith('500 '):
        state.status = '400 Not so good'
      self.modify_calls += 1

    def modify_headers(state):
      if self.test_status:
        self.assertEquals('400 Not so good', state.status)
      self.assertEquals('Some value', state.headers['SomeHeader'])
      state.headers.add_header('AnotherHeader', 'Another value')
      self.modify_calls += 1

    def modify_body(state):
      body = ''.join(state.body)
      self.assertEquals('Another value', state.headers['AnotherHeader'])
      self.assertEquals('Some value', state.headers['SomeHeader'])
      if self.test_body:
        self.assertEquals('Original content', body)

      state.body = ('%s%say ' % (w[1:], w[:1].lower()) for w in body.split())
      self.modify_calls += 1

    response_rewriter_chain = [check_initial_response,
                               check_chain,
                               check_chain,
                               modify_status,
                               modify_headers,
                               modify_body,
                              ]

    def test_middleware(application):
      return functools.partial(request_rewriter._rewriter_middleware, [],
                               response_rewriter_chain, application)
    self.rewriter_middleware = test_middleware

  def test_rewrite_response_chain(self):
    """Tests that rewriter_middleware correctly chains rewriters."""
    environ = {'ENVIRON_KEY': 'Environ value'}
    application = wsgi_test_utils.constant_app(
        '200 Good to go',
        [('SomeHeader', 'Some value')],
        'Original content')

    expected_status = '400 Not so good'

    expected_headers = {
        'AnotherHeader': 'Another value',
        'SomeHeader': 'Some value',
    }

    expected_body = 'riginaloay ontentcay '

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application, environ)

    self.assertEquals(1, self.initial_calls)
    self.assertEquals(2, self.chain_calls)
    self.assertEquals(3, self.modify_calls)

  def test_body_no_yields(self):
    """Tests an application that yields 0 body blocks."""

    def application(unused_environ, start_response):
      start_response('200 Good to go', [('SomeHeader', 'Some value')])
      return []

    environ = {'ENVIRON_KEY': 'Environ value'}

    expected_status = '400 Not so good'

    expected_headers = {
        'AnotherHeader': 'Another value',
        'SomeHeader': 'Some value',
    }

    expected_body = ''

    self.test_body = False
    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application, environ)

  def test_body_multiple_yields(self):
    """Tests an application that yields several body blocks."""

    def application(unused_environ, start_response):
      start_response('200 Good to go', [('SomeHeader', 'Some value')])
      yield 'Origin'
      yield 'al content'

    environ = {'ENVIRON_KEY': 'Environ value'}

    expected_status = '400 Not so good'

    expected_headers = {
        'AnotherHeader': 'Another value',
        'SomeHeader': 'Some value',
    }

    expected_body = 'riginaloay ontentcay '

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application, environ)

  def test_body_write_and_iterable(self):
    """Tests an application that calls write() and returns an iterable."""

    def application(unused_environ, start_response):
      write = start_response('200 Good to go', [('SomeHeader', 'Some value')])
      write('Origin')
      return ['al content']

    environ = {'ENVIRON_KEY': 'Environ value'}

    expected_status = '400 Not so good'

    expected_headers = {
        'AnotherHeader': 'Another value',
        'SomeHeader': 'Some value',
    }

    expected_body = 'riginaloay ontentcay '

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application, environ)

  def test_body_exception_before_yield(self):
    """Tests an application that raises an exception before yielding."""

    def application(unused_environ, start_response):
      start_response('200 Good to go', [('SomeHeader', 'Some value')])
      # Yield some empty blocks -- these should not prevent us from changing the
      # status and headers.
      yield ''
      yield ''
      try:
        raise ValueError('A problem happened')
      except ValueError, e:
        exc_info = sys.exc_info()
        start_response('500 Internal Server Error',
                       [('SomeHeader', 'Some value')], exc_info)
        yield str(e)
      else:
        yield 'Origin'
        yield 'al content'

    environ = {'ENVIRON_KEY': 'Environ value'}

    expected_status = '500 Internal Server Error'

    expected_headers = {
        'AnotherHeader': 'Another value',
        'SomeHeader': 'Some value',
    }

    expected_body = 'aay roblempay appenedhay '

    self.test_status = False
    self.test_body = False
    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application, environ)

  def test_body_exception_after_yield(self):
    """Tests an application that raises an exception before yielding."""

    def application(unused_environ, start_response):
      start_response('200 Good to go', [('SomeHeader', 'Some value')])
      yield 'Origin'
      try:
        raise ValueError('A problem happened')
      except ValueError, e:
        exc_info = sys.exc_info()
        start_response('500 Internal Server Error',
                       [('SomeHeader', 'Some value')], exc_info)
        yield str(e)
      else:
        yield 'al content'

    environ = {'ENVIRON_KEY': 'Environ value'}

    self.assertRaisesRegexp(ValueError, 'A problem happened$',
                            self.assert_rewritten_response, None, None, None,
                            application, environ)


class RequestRewritersTest(wsgi_test_utils.RewriterTestCase):
  """Tests the request rewriter."""

  def test_request_header_sanitation(self):
    """Tests that the invalid request headers are stripped out."""

    input_environ = {
        'HTTP_ACCEPT_ENCODING': 'gzip',
        'HTTP_CONNECTION': 'close',
        'HTTP_CONTENT_TYPE': 'text/html',
        'HTTP_KEEP_ALIVE': 'foo',
        'HTTP_PROXY_AUTHORIZATION': 'me',
        'HTTP_TE': 'deflate',
        'HTTP_TRAILER': 'X-Bar',
        'HTTP_TRANSFER_ENCODING': 'chunked',
        'HTTP_X_FOO': 'bar',
    }

    expected_environ = {
        'HTTP_CONTENT_TYPE': 'text/html',
        'HTTP_X_FOO': 'bar',
    }

    def application(environ, start_response):
      self.assertDictEqual(expected_environ, environ)

      start_response('200 OK', [])
      return ['ok']

    def start_response(unused_status, unused_headers, unused_exc_info=None):
      pass

    wrapped_application = request_rewriter.frontend_rewriter_middleware(
        application)

    wrapped_application(input_environ, start_response)


class ResponseRewritersTest(wsgi_test_utils.RewriterTestCase):
  """Tests the actual response rewriter chain."""

  def test_content_length_rewrite(self):
    """Tests when the 'Content-Length' header needs to be updated."""
    application = wsgi_test_utils.constant_app(
        '200 OK',
        [('Content-Type', 'text/html'),
         ('Cache-Control', 'no-cache'),
         ('Expires', 'Fri, 01 Jan 1990 00:00:00 GMT'),
         ('Content-Length', '1234'),
        ],
        'this is my data')

    expected_status = '200 OK'

    expected_headers = {
        'Content-Type': 'text/html',
        'Cache-Control': 'no-cache',
        'Expires': 'Fri, 01 Jan 1990 00:00:00 GMT',
        'Content-Length': '15',
    }

    expected_body = 'this is my data'

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

  def test_too_big_rewrite(self):
    """Tests that a response that is too big is rejected."""
    application = wsgi_test_utils.constant_app(
        '200 OK',
        [('Content-Type', 'text/plain'),
         ('Cache-Control', 'no-cache'),
         ('Expires', 'Fri, 01 Jan 1990 00:00:00 GMT'),
         ('Content-Length', '1234'),
        ],
        'x' * 33554433)     # 32 MB + 1 byte

    expected_status = '500 Internal Server Error'

    expected_headers = {
        'Content-Type': 'text/html',
        'Cache-Control': 'no-cache',
        'Expires': 'Fri, 01 Jan 1990 00:00:00 GMT',
        'Content-Length': '63',
    }

    expected_body = ('HTTP response was too large: 33554433. The limit is: '
                     '33554432.\n')

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

  def test_head_method_preserves_content_length(self):
    """Tests that a HEAD request does not delete or alter the Content-Length."""
    environ = {'REQUEST_METHOD': 'HEAD'}

    application = wsgi_test_utils.constant_app(
        '200 OK',
        [('Content-Type', 'text/html'),
         ('Cache-Control', 'no-cache'),
         ('Expires', 'Fri, 01 Jan 1990 00:00:00 GMT'),
         ('Content-Length', '1234'),
        ],
        'this is my data')

    expected_status = '200 OK'

    expected_headers = {
        'Content-Type': 'text/html',
        'Cache-Control': 'no-cache',
        'Expires': 'Fri, 01 Jan 1990 00:00:00 GMT',
        'Content-Length': '1234',
    }

    # Also expect that the body is deleted.
    expected_body = ''

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application, environ)

  def test_default_content_type(self):
    """Tests that the default Content-Type header is applied."""
    application = wsgi_test_utils.constant_app(
        '200 OK',
        [('Cache-Control', 'no-cache'),
         ('Expires', 'Fri, 01 Jan 1990 00:00:00 GMT'),
        ],
        'this is my data')

    expected_status = '200 OK'

    expected_headers = {
        'Content-Type': 'text/html',
        'Cache-Control': 'no-cache',
        'Expires': 'Fri, 01 Jan 1990 00:00:00 GMT',
        'Content-Length': '15',
    }

    expected_body = 'this is my data'

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

  def test_cache_control_rewrite(self):
    """Tests when the 'cache-control' header needs to be updated."""
    application = wsgi_test_utils.constant_app(
        '200 OK',
        [('Content-Type', 'text/html')],
        'this is my data')

    expected_status = '200 OK'

    expected_headers = {
        'Content-Type': 'text/html',
        'Cache-Control': 'no-cache',
        'Expires': 'Fri, 01 Jan 1990 00:00:00 GMT',
        'Content-Length': '15',
    }

    expected_body = 'this is my data'

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

  def test_manual_cache_control(self):
    """Tests that the user is able to manually set Cache-Control and Expires."""
    application = wsgi_test_utils.constant_app(
        '200 OK',
        [('Content-Type', 'text/html'),
         ('Cache-Control', 'max-age'),
         ('Expires', 'Mon, 25 Jul 9999 14:47:05 GMT'),
        ],
        'this is my data')

    expected_status = '200 OK'

    expected_headers = {
        'Content-Type': 'text/html',
        'Cache-Control': 'max-age',
        'Expires': 'Mon, 25 Jul 9999 14:47:05 GMT',
        'Content-Length': '15',
    }

    expected_body = 'this is my data'

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

  def test_manual_cache_control_not_expires(self):
    """Tests that the user is able to set Cache-Control without Expires."""
    application = wsgi_test_utils.constant_app(
        '200 OK',
        [('Content-Type', 'text/html'),
         ('Cache-Control', 'max-age'),
        ],
        'this is my data')

    expected_status = '200 OK'

    # Expect the custom Cache-Control, but no automatic Expires.
    expected_headers = {
        'Content-Type': 'text/html',
        'Cache-Control': 'max-age',
        'Content-Length': '15',
    }

    expected_body = 'this is my data'

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

  def test_manual_expires(self):
    """Tests that the user is able to set Expires without Cache-Control."""
    application = wsgi_test_utils.constant_app(
        '200 OK',
        [('Content-Type', 'text/html'),
         ('Expires', 'Wed, 25 Jul 2012 14:47:05 GMT'),
        ],
        'this is my data')

    expected_status = '200 OK'

    # Expect the default Cache-Control, and the custom Expires.
    expected_headers = {
        'Content-Type': 'text/html',
        'Cache-Control': 'no-cache',
        'Expires': 'Wed, 25 Jul 2012 14:47:05 GMT',
        'Content-Length': '15',
    }

    expected_body = 'this is my data'

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

  def test_set_cookie_prevents_caching(self):
    """Tests that the Set-Cookie header prevents caching from taking place."""
    # Test with no explicit Cache-Control and Expires headers.
    m = mox.Mox()
    m.StubOutWithMock(time, 'time')
    time.time().AndReturn(788918400)  # 1 Jan 1995 00:00:00
    m.ReplayAll()

    application = wsgi_test_utils.constant_app(
        '200 OK',
        [('Content-Type', 'text/html'),
         ('Set-Cookie', 'UserID=john; Max-Age=3600; Version=1'),
        ],
        'this is my data')

    expected_status = '200 OK'

    expected_headers = {
      'Content-Type': 'text/html',
      'Cache-Control': 'no-cache',
      'Expires': 'Fri, 01 Jan 1990 00:00:00 GMT',
      'Content-length': '15',
      'Set-Cookie': 'UserID=john; Max-Age=3600; Version=1',
    }

    expected_body = 'this is my data'

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

    m.VerifyAll()
    m.UnsetStubs()

    # Test with explicit Cache-Control: public and future Expires headers.
    m = mox.Mox()
    m.StubOutWithMock(time, 'time')
    time.time().AndReturn(788918400)  # 1 Jan 1995 00:00:00
    m.ReplayAll()

    application = wsgi_test_utils.constant_app(
        '200 OK',
        [('Content-Type', 'text/html'),
         ('Cache-Control', 'public'),
         ('Cache-Control', 'max-age=20'),
         ('Expires', 'Mon, 25 Jul 9999 14:47:05 GMT'),
         ('Set-Cookie', 'UserID=john; Max-Age=3600; Version=1'),
        ],
        'this is my data')

    expected_status = '200 OK'

    expected_headers = {
      'Content-Type': 'text/html',
      'Cache-Control': 'max-age=20, private',
      'Expires': 'Sun, 01 Jan 1995 00:00:00 GMT',
      'Content-Length': '15',
      'Set-Cookie': 'UserID=john; Max-Age=3600; Version=1',
    }

    expected_body = 'this is my data'

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

    m.VerifyAll()
    m.UnsetStubs()

    # Test with explicit Cache-Control: private and past Expires headers.
    m = mox.Mox()
    m.StubOutWithMock(time, 'time')
    time.time().AndReturn(788918400)  # 1 Jan 1995 00:00:00
    m.ReplayAll()

    application = wsgi_test_utils.constant_app(
        '200 OK',
        [('Content-Type', 'text/html'),
         ('Cache-Control', 'private, max-age=20'),
         ('Expires', 'Mon, 13 Mar 1992 18:12:51 GMT'),
         ('Set-Cookie', 'UserID=john; Max-Age=3600; Version=1'),
        ],
        'this is my data')

    expected_status = '200 OK'

    expected_headers = {
      'Content-Type': 'text/html',
      'Cache-Control': 'private, max-age=20',
      'Expires': 'Mon, 13 Mar 1992 18:12:51 GMT',
      'Content-Length': '15',
      'Set-Cookie': 'UserID=john; Max-Age=3600; Version=1',
    }

    expected_body = 'this is my data'

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

    m.VerifyAll()
    m.UnsetStubs()

    # Test with a non-cacheable status code.
    # Note: For simplicity, we simply treat this as normal (unlike production,
    # which does not sanitize such cases).
    m = mox.Mox()
    m.StubOutWithMock(time, 'time')
    time.time().AndReturn(788918400)  # 1 Jan 1995 00:00:00
    m.ReplayAll()

    application = wsgi_test_utils.constant_app(
        '404 Not Found',
        [('Content-Type', 'text/html'),
         ('Cache-Control', 'public, max-age=20'),
         ('Expires', 'Mon, 25 Jul 9999 14:47:05 GMT'),
         ('Set-Cookie', 'UserID=john; Max-Age=3600; Version=1'),
        ],
        'this is my data')

    expected_status = '404 Not Found'

    expected_headers = {
      'Content-Type': 'text/html',
      'Cache-Control': 'max-age=20, private',
      'Expires': 'Sun, 01 Jan 1995 00:00:00 GMT',
      'Content-Length': '15',
      'Set-Cookie': 'UserID=john; Max-Age=3600; Version=1',
    }

    expected_body = 'this is my data'

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

    m.VerifyAll()
    m.UnsetStubs()

  def _run_no_body_status_test(self, status):
    """Tests rewriting when the status is not allowed to have a body."""
    application = wsgi_test_utils.constant_app(
        status,
        [('Content-Type', 'text/html'),
         ('Content-Length', '1234'),
        ],
        'this is my data')

    expected_status = status

    expected_headers = {
        'Content-Type': 'text/html',
    }

    expected_body = ''

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

  def test_no_body_100(self):
    """Tests rewriting when the status is 100."""
    self._run_no_body_status_test('100 Continue')

  def test_no_body_101(self):
    """Tests rewriting when the status is 101."""
    self._run_no_body_status_test('101 Switching Protocols')

  def test_no_body_204(self):
    """Tests rewriting when the status is 204."""
    self._run_no_body_status_test('204 No Content')

  def test_no_body_304(self):
    """Tests rewriting when the status is 304."""
    self._run_no_body_status_test('304 Not Modified')

  def test_no_rewrite(self):
    """Tests when nothing gets rewritten."""
    application = wsgi_test_utils.constant_app(
        '200 OK',
        [('Content-Type', 'text/html'),
         ('Cache-Control', 'no-cache'),
         ('Expires', 'Fri, 01 Jan 1990 00:00:00 GMT'),
         ('Content-Length', '15'),
        ],
        'this is my data')

    expected_status = '200 OK'

    expected_headers = {
        'Content-Type': 'text/html',
        'Cache-Control': 'no-cache',
        'Expires': 'Fri, 01 Jan 1990 00:00:00 GMT',
        'Content-Length': '15',
    }

    expected_body = 'this is my data'

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

  def test_header_sanitation(self):
    """Tests that unsafe headers are deleted."""
    application = wsgi_test_utils.constant_app(
        '200 OK',
        [('Server', 'iis'),
         ('Date', 'sometime in the summer'),
         ('Content-Type', 'text/html'),
         ('Cache-Control', 'no-cache'),
         ('Expires', 'Fri, 01 Jan 1990 00:00:00 GMT'),
         ('Content-Length', '1500'),
         ('Content-Encoding', 'gzip'),
         ('Accept-Encoding', 'gzip'),
         ('Transfer-Encoding', 'chunked'),
         ('Content-Disposition', 'attachment; filename="h\xc3\xa9llo.png"'),
         ('Connection', 'close'),
         ('Keep-Alive', 'foo'),
         ('Proxy-Authenticate', 'Basic'),
         ('Trailer', 'X-Bar'),
         ('Upgrade', 'SPDY/2'),
         # Detailed illegal character tests
         ('has space', 'foo'),
         ('has:colon', 'foo'),
         ('has-non-printable\x03', 'foo'),
         ('has-non-ascii\xdc', 'foo'),
         ('value-has-space', 'has space'),                      # Legal
         ('value-has-colon', 'has:colon'),                      # Legal
         ('value-has-non-printable', 'ab\x03cd'),
         ('value-has-non-ascii', 'ab\xdccd'),
        ],
        'this is my data')

    expected_status = '200 OK'

    expected_headers = {
        'Content-Type': 'text/html',
        'Cache-Control': 'no-cache',
        'Expires': 'Fri, 01 Jan 1990 00:00:00 GMT',
        'Content-Length': '15',
        # NOTE: Accept-Encoding is not a response header, so we do not care if
        # the user is able to set it.
        'Accept-Encoding': 'gzip',
        'value-has-space': 'has space',
        'value-has-colon': 'has:colon',
    }

    expected_body = 'this is my data'

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)


if __name__ == '__main__':
  unittest.main()
