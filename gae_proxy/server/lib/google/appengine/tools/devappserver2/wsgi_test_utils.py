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
"""Utilities for testing WSGI apps."""



import cStringIO
import unittest
import wsgiref.headers

from google.appengine.tools.devappserver2 import request_rewriter


class WSGITestCase(unittest.TestCase):
  """Base class for tests involving requests to a WSGI application."""

  @staticmethod
  def _normalize_headers(headers):
    """Normalize a headers set to a list with lowercased names.

    Args:
      headers: A sequence of pairs, a dict or a wsgiref.headers.Headers object.

    Returns:
      headers, converted to a sequence of pairs (if it was not already), with
      all of the header names lowercased.
    """
    if (isinstance(headers, dict) or
        isinstance(headers, wsgiref.headers.Headers)):
      headers = headers.items()

    return [(name.lower(), value) for name, value in headers]

  def assertHeadersEqual(self, expected, actual, msg=None):
    """Tests whether two sets of HTTP headers are equivalent.

    The header sets expected and actual are equal if they both have exactly the
    same set of header name/value pairs. Header names are considered
    case-insensitive, but header values are case sensitive. The order does not
    matter, but duplicate headers (headers of the same name) must be the same in
    both.

    Note: This should be used instead of assertEqual, assertItemsEqual or
    assertDictEqual. Using standard asserts for lists and dicts will be case
    sensitive. Using assert for wsgiref.headers.Headers does reference equality.

    Args:
      expected: A sequence of pairs, a dict or a wsgiref.headers.Headers object.
      actual: A sequence of pairs, a dict or a wsgiref.headers.Headers object.
      msg: A custom error message to display, if the test fails.

    Raises:
      AssertionError if expected and actual are not equal.
    """
    expected = self._normalize_headers(expected)
    actual = self._normalize_headers(actual)

    for name, value in actual:
      self.assertIsInstance(name, str, 'header name %r must be a str' % name)
      self.assertIsInstance(name, str, 'header value %r must be a str' % value)
    self.assertItemsEqual(expected, actual, msg)

  def assertResponse(self,
                     expected_status,
                     expected_headers,
                     expected_content,
                     fn,
                     *args,
                     **kwargs):
    """Calls fn(*args, <start_response>, **kwargs) and checks the result.

    Args:
      expected_status: The expected HTTP status returned e.g. '200 OK'.
      expected_headers: A dict, list or wsgiref.headers.Headers representing the
          expected generated HTTP headers e.g. {'Content-type': 'text/plain'}.
      expected_content: The expected content generated e.g. 'Hello World'.
      fn: The function to test. This function will be called with
          fn(*args, start_response=<func>, **kwargs) where the start_response
          function verifies that it is called with the correct status and
          headers.
      *args: The positional arguments passed to fn.
      **kwargs: The keyword arguments passed to fn.
    """

    # Buffer for 'write' callable
    write_buffer = cStringIO.StringIO()

    def start_response(status, headers, exc_info=None):
      self.assertEqual(expected_status, status)
      self.assertHeadersEqual(expected_headers, headers)
      self.assertEqual(None, exc_info)
      return write_buffer.write

    args += (start_response,)
    response = fn(*args, **kwargs)
    # We sometimes use a function that might, but should not, return None
    # (URLHandler.handle_authorization). Explicitly test for this to avoid a
    # confusing TypeError on the following line.
    self.assertNotEqual(None, response, '%r(*args, **kwargs) != None' % fn)
    response = ''.join(response)
    self.assertIsInstance(
        response, str, 'response %r must be a str' % response[:10])
    self.assertMultiLineEqual(expected_content,
                              write_buffer.getvalue() + response)


class RewriterTestCase(WSGITestCase):
  """Base class for test cases that test rewriter functionality."""

  rewriter_middleware = staticmethod(
      request_rewriter.frontend_rewriter_middleware)

  def assert_rewritten_response(self, expected_status, expected_headers,
                                expected_body, application, environ=None):
    """Tests that a rewritten application produces the expected response.

    This applies the response rewriter chain to application and then tests the
    result.

    Args:
      expected_status: The expected HTTP status returned e.g. '200 OK'.
      expected_headers: A dict, list or wsgiref.headers.Headers representing the
          expected generated HTTP headers e.g. {'Content-type': 'text/plain'}.
      expected_body: The expected content generated e.g. 'Hello World'.
      application: A WSGI application that will be called and have its response
        rewritten.
      environ: Optional environment to pass to the application.
    """
    if environ is None:
      environ = {}
    wrapped_application = self.rewriter_middleware(application)
    self.assertResponse(expected_status, expected_headers, expected_body,
                        wrapped_application, environ)


def constant_app(status, headers, body):
  """Creates a WSGI application that produces a constant response.

  Args:
    status: A status code and message as a string. (e.g., '200 OK'.)
    headers: A list of tuples containing the response headers.
    body: A string containing the response body.

  Returns:
    A WSGI application, as defined in PEP-333.
  """

  def application(unused_environ, start_response):
    start_response(status, headers)
    return [body]

  return application
