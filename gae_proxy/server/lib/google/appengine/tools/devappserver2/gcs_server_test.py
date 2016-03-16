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
"""Tests for google.appengine.tools.devappserver2.gcs_server."""

import cStringIO
import httplib
import unittest

import google
import mox

from google.appengine.ext.cloudstorage import stub_dispatcher
from google.appengine.tools.devappserver2 import gcs_server
from google.appengine.tools.devappserver2 import wsgi_test_utils


class FakeResult(object):
  def __init__(self, status, headers, content):
    self.status_code = status
    self.headers = headers
    self.content = content


class GCSTest(wsgi_test_utils.WSGITestCase):
  """Tests GCS url handler."""

  def setUp(self):
    self.mox = mox.Mox()
    self.app = gcs_server.Application()
    self.mox.StubOutWithMock(stub_dispatcher, 'dispatch')
    self._host = 'localhost'

  def tearDown(self):
    self.mox.UnsetStubs()

  def run_request(self, method, headers, path, query, body,
                  expected_status, expected_headers, expected_content):
    environ = {
        'HTTP_HOST': self._host,
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': query,
        'wsgi.url_scheme': 'http',
        'wsgi.input': cStringIO.StringIO(body),
    }

    for k, v in headers.iteritems():
      environ['HTTP_%s' % k.upper()] = v

    self.mox.ReplayAll()
    self.assertResponse(
        expected_status,
        expected_headers,
        expected_content,
        self.app,
        environ)
    self.mox.VerifyAll()

  def expect_dispatch(self, method, headers, path, body, result):
    """Setup a mox expectation to gcs_dispatch.dispatch."""

    # webob always adds Host header and optionally adds Content-Length header
    # for requests with non-empty body.
    new_headers = dict(headers)
    new_headers['Host'] = self._host
    if body:
      new_headers['Content-Length'] = str(len(body))

    url = 'http://%s%s' % (self._host, path)
    stub_dispatcher.dispatch(method, new_headers, url, body).AndReturn(result)

  def test_dispatch(self):
    """Tests that dispatch stub is called with the correct parameters."""
    result = FakeResult(404, {'a': 'b'}, 'blah')
    self.expect_dispatch('POST',
                         {'Foo': 'bar'},
                         '/_ah/gcs/some_bucket?param=1',
                         'body', result)

    self.run_request('POST',
                     {'Foo': 'bar'},
                     '/_ah/gcs/some_bucket',
                     'param=1',
                     'body',
                     '404 Not Found',
                     [('a', 'b')],
                     'blah')

  def test_http_308(self):
    """Tests that the non-standard HTTP 308 status code is handled properly."""
    result = FakeResult(308, {}, '')
    self.expect_dispatch('GET', {}, '/_ah/gcs/some_bucket', '', result)

    self.run_request('GET', {}, '/_ah/gcs/some_bucket', '', '',
                     '308 Resume Incomplete', [], '')

  def test_dispatch_value_error(self):
    """Tests that ValueError raised by dispatch stub is handled properly."""
    error = ValueError('Invalid Token', httplib.BAD_REQUEST)
    stub_dispatcher.dispatch(mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg(),
                             mox.IgnoreArg()).AndRaise(error)

    self.run_request('GET', {}, '/_ah/some_bucket', '', '',
                     '400 Bad Request', [], 'Invalid Token')


if __name__ == '__main__':
  unittest.main()
