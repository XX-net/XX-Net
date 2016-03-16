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
"""Utilities commonly used in endpoints tests."""







import cStringIO
import unittest
import urlparse

from google.appengine.tools.devappserver2.endpoints import api_request


def build_request(path, body='', http_headers=None):
  """Build an ApiRequest for the given path and body.

  Args:
    path: A string containing the URL for the proposed request.
    body: A string containing the body of the proposed request.
    http_headers: A list of (header, value) headers to add to the request.

  Returns:
    An ApiRequest object built based on the incoming parameters.
  """
  (unused_scheme, unused_netloc, path, query,
   unused_fragment) = urlparse.urlsplit(path)
  env = {'SERVER_PORT': 42, 'REQUEST_METHOD': 'GET',
         'SERVER_NAME': 'localhost', 'HTTP_CONTENT_TYPE': 'application/json',
         'PATH_INFO': path, 'wsgi.input': cStringIO.StringIO(body)}
  if query:
    env['QUERY_STRING'] = query

  if http_headers:
    for header, value in http_headers:
      header = 'HTTP_%s' % header.upper().replace('-', '_')
      env[header] = value

  cgi_request = api_request.ApiRequest(env)
  return cgi_request


class TestsWithStartResponse(unittest.TestCase):
  def setUp(self):
    self.response_status = None
    self.response_headers = None
    self.response_exc_info = None

    def start_response(status, headers, exc_info=None):
      self.response_status = status
      self.response_headers = headers
      self.response_exc_info = exc_info
    self.start_response = start_response

  def assert_http_match(self, response, expected_status, expected_headers,
                        expected_body):
    """Test that the headers and body match."""
    self.assertEqual(str(expected_status), self.response_status)

    # Verify that headers match.  Order shouldn't matter.
    self.assertEqual(len(self.response_headers), len(expected_headers))
    self.assertEqual(set(self.response_headers), set(expected_headers))
    # Make sure there are no duplicate headers in the response.
    self.assertEqual(len(self.response_headers),
                     len(set(header for header, _ in self.response_headers)))

    # Convert the body from an iterator to a string.
    body = ''.join(response)
    self.assertEqual(expected_body, body)


class MockConnectionResponse(object):

  def __init__(self, status, body):
    self._body = body
    self.status = status

  def read(self):
    return self._body

  @staticmethod
  def close(*args):
    pass
