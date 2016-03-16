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
"""Tests for google.appengine.tools.devappserver2.url_handler."""



import re
import unittest
import wsgiref.util

from google.appengine.api import appinfo
from google.appengine.tools.devappserver2 import constants
from google.appengine.tools.devappserver2 import url_handler
from google.appengine.tools.devappserver2 import wsgi_test_utils

COOKIE = 'dev_appserver_login=johnny@example.com:False:115914779145204185301'
COOKIE_ADMIN = ('dev_appserver_login=johnny@example.com:True:'
                '115914779145204185301')


class TestURLHandler(unittest.TestCase):
  """Tests URLHandler base class functionality."""

  def test_match(self):
    handler = url_handler.URLHandler(re.compile('/(foo|bar).*'))
    self.assertTrue(handler.match('/foo'))
    self.assertTrue(handler.match('/bar'))
    self.assertTrue(handler.match('/foo/baz'))
    self.assertTrue(handler.match('/bar/baz'))
    self.assertFalse(handler.match('/baz'))
    self.assertFalse(handler.match('/baz/baz'))


class TestAuthorization(wsgi_test_utils.WSGITestCase):
  """Tests authorization functionality in UserConfiguredURLHandler."""

  def setUp(self):
    self.environ = {}
    wsgiref.util.setup_testing_defaults(self.environ)
    # Have a different SERVER_NAME to HTTP_HOST to we can test that the server
    # is using the right one.
    self.environ['SERVER_NAME'] = '127.0.0.1'
    self.environ['HTTP_HOST'] = 'localhost:8080'
    self.environ['PATH_INFO'] = '/my/album/of/pictures'
    self.environ['QUERY_STRING'] = 'with=some&query=parameters'

  def test_optional(self):
    """Test page with no login requirement, and no cookie."""
    url_map = appinfo.URLMap(url='/')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    def start_response(unused_status, unused_response_headers,
                       unused_exc_info=None):
      # Successful authorization should not call start_response
      self.fail('start_response was called')

    r = h.handle_authorization(self.environ, start_response)
    self.assertEqual(None, r)

  def test_required_redirect_no_login(self):
    """Test page with login: required; redirect, and no cookie."""
    url_map = appinfo.URLMap(url='/',
                             login='required')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    expected_status = '302 Requires login'
    expected_location = (
        'http://localhost:8080/_ah/login?continue=http%3A//localhost%3A8080'
        '/my/album/of/pictures%3Fwith%3Dsome%26query%3Dparameters')
    expected_headers = {'Location': expected_location}

    self.assertResponse(expected_status, expected_headers, '',
                        h.handle_authorization, self.environ)

  def test_required_unauthorized_no_login(self):
    """Test page with login: required; unauthorized, and no cookie."""
    url_map = appinfo.URLMap(url='/',
                             login='required',
                             auth_fail_action='unauthorized')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    expected_status = '401 Not authorized'
    expected_headers = {'Content-Type': 'text/html',
                        'Cache-Control': 'no-cache'}
    expected_content = 'Login required to view page.'

    self.assertResponse(expected_status, expected_headers, expected_content,
                        h.handle_authorization, self.environ)

  def test_required_succeed(self):
    """Test page with login: required, and a valid cookie."""
    url_map = appinfo.URLMap(url='/',
                             login='required')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    self.environ['HTTP_COOKIE'] = COOKIE

    def start_response(unused_status, unused_response_headers,
                       unused_exc_info=None):
      # Successful authorization should not call start_response
      self.fail('start_response was called')

    r = h.handle_authorization(self.environ, start_response)
    self.assertEqual(None, r)

  def test_required_no_login_fake_is_admin(self):
    """Test page with login: required, no cookie, with fake-is-admin header."""
    # This should FAIL, because fake-is-admin only applies to login: admin, not
    # login: required.
    url_map = appinfo.URLMap(url='/',
                             login='required')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    self.environ[constants.FAKE_IS_ADMIN_HEADER] = '1'

    expected_status = '302 Requires login'
    expected_location = (
        'http://localhost:8080/_ah/login?continue=http%3A//localhost%3A8080'
        '/my/album/of/pictures%3Fwith%3Dsome%26query%3Dparameters')
    expected_headers = {'Location': expected_location}

    self.assertResponse(expected_status, expected_headers, '',
                        h.handle_authorization, self.environ)

  def test_admin_no_login_fake_logged_in(self):
    """Tests page with login: admin, no cookie with fake login header."""
    # This should FAIL, because a fake login does not imply admin privileges.
    url_map = appinfo.URLMap(url='/',
                             login='admin')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    self.environ[constants.FAKE_LOGGED_IN_HEADER] = '1'

    expected_status = '401 Not authorized'
    expected_headers = {'Content-Type': 'text/html',
                        'Cache-Control': 'no-cache'}
    expected_content = ('Current logged in user Fake User is not authorized '
                        'to view this page.')

    self.assertResponse(expected_status, expected_headers, expected_content,
                        h.handle_authorization, self.environ)

  def test_required_succeed_fake_is_admin(self):
    """Test with login: required, and a valid cookie, with fake-is-admin."""
    url_map = appinfo.URLMap(url='/',
                             login='required')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    self.environ['HTTP_COOKIE'] = COOKIE
    self.environ[constants.FAKE_IS_ADMIN_HEADER] = '1'

    def start_response(unused_status, unused_response_headers,
                       unused_exc_info=None):
      # Successful authorization should not call start_response
      self.fail('start_response was called')

    r = h.handle_authorization(self.environ, start_response)
    self.assertEqual(None, r)

  def test_admin_redirect_no_login(self):
    """Test page with login: admin; redirect, and no cookie."""
    url_map = appinfo.URLMap(url='/',
                             login='admin')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    expected_status = '302 Requires login'
    expected_location = (
        'http://localhost:8080/_ah/login?continue=http%3A//localhost%3A8080'
        '/my/album/of/pictures%3Fwith%3Dsome%26query%3Dparameters')
    expected_headers = {'Location': expected_location}

    self.assertResponse(expected_status, expected_headers, '',
                        h.handle_authorization, self.environ)

  def test_admin_unauthorized_no_login(self):
    """Test page with login: admin; unauthorized, and no cookie."""
    url_map = appinfo.URLMap(url='/',
                             login='admin',
                             auth_fail_action='unauthorized')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    expected_status = '401 Not authorized'
    expected_headers = {'Content-Type': 'text/html',
                        'Cache-Control': 'no-cache'}
    expected_content = 'Login required to view page.'

    self.assertResponse(expected_status, expected_headers, expected_content,
                        h.handle_authorization, self.environ)

  def test_admin_no_admin(self):
    """Test page with login: admin, and a non-admin cookie."""
    url_map = appinfo.URLMap(url='/',
                             login='admin')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    self.environ['HTTP_COOKIE'] = COOKIE

    expected_status = '401 Not authorized'
    expected_headers = {'Content-Type': 'text/html',
                        'Cache-Control': 'no-cache'}
    expected_content = ('Current logged in user johnny@example.com is not '
                        'authorized to view this page.')

    self.assertResponse(expected_status, expected_headers, expected_content,
                        h.handle_authorization, self.environ)

  def test_admin_succeed(self):
    """Test page with login: admin, and a valid admin cookie."""
    url_map = appinfo.URLMap(url='/',
                             login='admin')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    self.environ['HTTP_COOKIE'] = COOKIE_ADMIN

    def start_response(unused_status, unused_response_headers,
                       unused_exc_info=None):
      # Successful authorization should not call start_response
      self.fail('start_response was called')

    r = h.handle_authorization(self.environ, start_response)
    self.assertEqual(None, r)

  def test_admin_no_login_fake_is_admin(self):
    """Test page with login: admin, and no cookie, with fake-is-admin."""
    url_map = appinfo.URLMap(url='/',
                             login='admin')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    self.environ[constants.FAKE_IS_ADMIN_HEADER] = '1'

    def start_response(unused_status, unused_response_headers,
                       unused_exc_info=None):
      # Successful authorization should not call start_response
      self.fail('start_response was called')

    r = h.handle_authorization(self.environ, start_response)
    self.assertEqual(None, r)

  def test_admin_no_admin_fake_is_admin(self):
    """Test with login: admin, and a non-admin cookie, with fake-is-admin."""
    url_map = appinfo.URLMap(url='/',
                             login='admin')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    self.environ['HTTP_COOKIE'] = COOKIE
    self.environ[constants.FAKE_IS_ADMIN_HEADER] = '1'

    def start_response(unused_status, unused_response_headers,
                       unused_exc_info=None):
      # Successful authorization should not call start_response
      self.fail('start_response was called')

    r = h.handle_authorization(self.environ, start_response)
    self.assertEqual(None, r)

  def test_admin_succeed_fake_is_admin(self):
    """Test with login: admin, and valid admin cookie, with fake-is-admin."""
    url_map = appinfo.URLMap(url='/',
                             login='admin')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    self.environ['HTTP_COOKIE'] = COOKIE_ADMIN
    self.environ[constants.FAKE_IS_ADMIN_HEADER] = '1'

    def start_response(unused_status, unused_response_headers,
                       unused_exc_info=None):
      # Successful authorization should not call start_response
      self.fail('start_response was called')

    r = h.handle_authorization(self.environ, start_response)
    self.assertEqual(None, r)

  def test_admin_no_login_fake_is_admin_header(self):
    """Test page with login: admin, and no cookie, with fake-is-admin header."""
    url_map = appinfo.URLMap(url='/',
                             login='admin')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    self.environ[constants.FAKE_IS_ADMIN_HEADER] = '1'

    def start_response(unused_status, unused_response_headers,
                       unused_exc_info=None):
      # Successful authorization should not call start_response
      self.fail('start_response was called')

    r = h.handle_authorization(self.environ, start_response)
    self.assertEqual(None, r)

  def test_login_required_no_login_fake_logged_in_header(self):
    """Test page with login: required with fake-login-required."""
    url_map = appinfo.URLMap(url='/',
                             login='required')

    h = url_handler.UserConfiguredURLHandler(url_map, '/$')

    self.environ[constants.FAKE_LOGGED_IN_HEADER] = '1'

    def start_response(unused_status, unused_response_headers,
                       unused_exc_info=None):
      # Successful authorization should not call start_response
      self.fail('start_response was called')

    r = h.handle_authorization(self.environ, start_response)
    self.assertEqual(None, r)

if __name__ == '__main__':
  unittest.main()
