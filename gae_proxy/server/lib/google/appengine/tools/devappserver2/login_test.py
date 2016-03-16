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
"""Tests for devappserver2.login."""



import Cookie
import unittest
import urllib
import wsgiref.util

from google.appengine.tools.devappserver2 import login

# Values used by many tests
COOKIE_NAME = 'my_fancy_cookie'
EMAIL = 'johnny@example.com'
USER_ID = '115914779145204185301'


class CookieTest(unittest.TestCase):
  """Tests for the cookie handling functions."""

  def test_get_user_info_admin(self):
    """Tests the get_user_info function when the admin field is True."""
    cookie_value = '%s:True:%s' % (EMAIL, USER_ID)

    http_cookie = 'one=two; %s=%s; three=four' % (COOKIE_NAME, cookie_value)
    email, admin, user_id = login.get_user_info(http_cookie,
                                                cookie_name=COOKIE_NAME)

    self.assertEqual(EMAIL, email)
    self.assertTrue(admin)
    self.assertEqual(USER_ID, user_id)

  def test_get_user_info_not_admin(self):
    """Tests the get_user_info function when the admin field is False."""
    cookie_value = '%s:False:%s' % (EMAIL, USER_ID)

    http_cookie = 'one=two; %s=%s; three=four' % (COOKIE_NAME, cookie_value)
    email, admin, user_id = login.get_user_info(http_cookie,
                                                cookie_name=COOKIE_NAME)

    self.assertEqual(EMAIL, email)
    self.assertFalse(admin)
    self.assertEqual(USER_ID, user_id)

  def test_get_user_info_invalid_email(self):
    """Tests the get_user_info function when the admin field is False."""
    cookie_value = 'foo:True:%s' % USER_ID

    http_cookie = 'one=two; %s=%s; three=four' % (COOKIE_NAME, cookie_value)
    email, admin, user_id = login.get_user_info(http_cookie,
                                                cookie_name=COOKIE_NAME)

    self.assertEqual('', email)
    self.assertFalse(admin)
    self.assertEqual('', user_id)

  def test_get_user_info_does_not_exist(self):
    """Tests the get_user_info function when the cookie is not present."""
    http_cookie = 'one=two; three=four'
    email, admin, user_id = login.get_user_info(http_cookie,
                                                cookie_name=COOKIE_NAME)

    self.assertEqual('', email)
    self.assertFalse(admin)
    self.assertEqual('', user_id)

  def test_get_user_info_bad_cookie(self):
    """Tests the get_user_info function when the cookie is malformed."""
    cookie_name = 'SinaRot/g/get'  # seen in the wild
    cookie_value = 'blah'

    http_cookie = '%s=%s' % (cookie_name, cookie_value)
    email, admin, user_id = login.get_user_info(http_cookie,
                                                cookie_name=cookie_name)

    self.assertEqual('', email)
    self.assertFalse(admin)
    self.assertEqual('', user_id)

  def test_get_user_info_from_dict_admin(self):
    """Tests the get_user_info function when the admin field is True."""
    cookie_value = '%s:True:%s' % (EMAIL, USER_ID)

    cookie_dict = {'one': 'two', COOKIE_NAME: cookie_value, 'three': 'four'}
    email, admin, user_id = login._get_user_info_from_dict(
        cookie_dict, cookie_name=COOKIE_NAME)

    self.assertEqual(EMAIL, email)
    self.assertTrue(admin)
    self.assertEqual(USER_ID, user_id)

  def test_get_user_info_from_dict_not_admin(self):
    """Tests the get_user_info function when the admin field is False."""
    cookie_value = '%s:False:%s' % (EMAIL, USER_ID)

    cookie_dict = {'one': 'two', COOKIE_NAME: cookie_value, 'three': 'four'}
    email, admin, user_id = login._get_user_info_from_dict(
        cookie_dict, cookie_name=COOKIE_NAME)

    self.assertEqual(EMAIL, email)
    self.assertFalse(admin)
    self.assertEqual(USER_ID, user_id)

  def test_get_user_info_from_dict_does_not_exist(self):
    """Tests the get_user_info function when the cookie is not present."""
    cookie_dict = {'one': 'two', 'three': 'four'}
    email, admin, user_id = login._get_user_info_from_dict(
        cookie_dict, cookie_name=COOKIE_NAME)

    self.assertEqual('', email)
    self.assertFalse(admin)
    self.assertEqual('', user_id)

  def test_set_user_info_cookie(self):
    """Tests the set_user_info_cookie function."""
    cookie_value = '%s:True:%s' % (EMAIL, USER_ID)
    expected_result = '%s="%s"; Path=/' % (COOKIE_NAME, cookie_value)

    result = login._set_user_info_cookie(EMAIL, True, cookie_name=COOKIE_NAME)

    self.assertEqual(expected_result, result)

  def test_clear_user_info_cookie(self):
    """Tests the clear_user_info_cookie function."""
    expected_result = '%s=; Max-Age=0; Path=/' % COOKIE_NAME

    result = login._clear_user_info_cookie(cookie_name=COOKIE_NAME)

    self.assertEqual(expected_result, result)


class LoginRedirectTest(unittest.TestCase):
  """Tests the login_redirect function."""

  def test_basic(self):
    """Tests that redirects are written back to the user."""
    application_url = 'http://foo.com:1234'
    continue_url = ('http://foo.com:1234/my/album/of/pictures?'
                    'with=some&query=parameters')

    expected_location = (
        'http://foo.com:1234/_ah/login?continue='
        'http%3A//foo.com%3A1234'
        '/my/album/of/pictures%3Fwith%3Dsome%26query%3Dparameters')

    def start_response(status, headers, exc_info=None):
      self.assertTrue(status.startswith('302'))
      headers = dict(headers)
      self.assertEqual({'Location': expected_location}, headers)
      self.assertEqual(None, exc_info)
    body = login.login_redirect(application_url, continue_url, start_response)

    self.assertEqual('', ''.join(body))


class LoginPageTest(unittest.TestCase):
  """Tests the various ways of invoking the login page."""

  def test_no_params(self):
    """Tests just accessing the login URL with no params."""
    host = 'foo.com:1234'
    path_info = '/_ah/login'
    cookie_dict = {}
    action = ''
    set_email = ''
    set_admin = False
    continue_url = ''
    status, location, set_cookie, content_type = self._run_test(
        host, path_info, cookie_dict, action, set_email, set_admin,
        continue_url)
    self.assertEqual(200, status)
    self.assertFalse(location)
    self.assertFalse(set_cookie)
    self.assertEqual('text/html', content_type)

  def test_login(self):
    """Tests when setting the user info with and without continue URL."""
    host = 'foo.com:1234'
    path_info = '/_ah/login'
    cookie_dict = {}
    action = 'Login'
    set_email = EMAIL
    set_admin = False
    continue_url = ''

    expected_set = login._set_user_info_cookie(set_email, set_admin).strip()

    # No continue URL.
    status, location, set_cookie, _ = self._run_test(
        host, path_info, cookie_dict, action, set_email, set_admin,
        continue_url)
    self.assertEqual(302, status)
    self.assertEqual('http://%s%s' % (host, path_info), location)
    self.assertEqual(expected_set, set_cookie)
    self.assertIsInstance(location, str)
    self.assertIsInstance(set_cookie, str)

    # Continue URL.
    continue_url = 'http://foo.com/blah'
    status, location, set_cookie, _ = self._run_test(
        host, path_info, cookie_dict, action, set_email, set_admin,
        continue_url)
    self.assertEqual(302, status)
    self.assertEqual(continue_url, location)
    self.assertEqual(expected_set, set_cookie)
    self.assertIsInstance(location, str)
    self.assertIsInstance(set_cookie, str)

  def test_logout(self):
    """Tests when logging out with and without continue URL."""
    host = 'foo.com:1234'
    path_info = '/_ah/login'
    cookie_dict = {'dev_appserver_login': '%s:False:%s' % (EMAIL, USER_ID)}
    action = 'Logout'
    set_email = ''
    set_admin = False
    continue_url = ''

    expected_set = login._clear_user_info_cookie().strip()

    # No continue URL.
    status, location, set_cookie, _ = self._run_test(
        host, path_info, cookie_dict, action, set_email, set_admin,
        continue_url)
    self.assertEqual(302, status)
    self.assertEqual('http://%s%s' % (host, path_info), location)
    self.assertEqual(expected_set, set_cookie)
    self.assertIsInstance(location, str)
    self.assertIsInstance(set_cookie, str)

    # Continue URL.
    continue_url = 'http://foo.com/blah'
    status, location, set_cookie, _ = self._run_test(
        host, path_info, cookie_dict, action, set_email, set_admin,
        continue_url)
    self.assertEqual(302, status)
    self.assertEqual(continue_url, location)
    self.assertEqual(expected_set, set_cookie)
    self.assertIsInstance(location, str)
    self.assertIsInstance(set_cookie, str)

  def test_passive(self):
    """Tests when the user is already logged in."""
    host = 'foo.com:1234'
    path_info = '/_ah/login'
    cookie_dict = {'dev_appserver_login': '%s:False:%s' % (EMAIL, USER_ID)}
    action = ''
    set_email = ''
    set_admin = False
    continue_url = '/my/fancy/url'

    # Continue URL.
    continue_url = 'http://foo.com/blah'
    status, location, set_cookie, content_type = self._run_test(
        host, path_info, cookie_dict, action, set_email, set_admin,
        continue_url)
    self.assertEqual(200, status)
    self.assertFalse(location)
    self.assertFalse(set_cookie)
    self.assertEqual('text/html; charset=utf-8', content_type)
    self.assertIsInstance(content_type, str)

  def _run_test(self, host, path_info='/', cookie_dict=None, action=None,
                set_email=None, set_admin=None, continue_url=None,
                method='GET'):
    """Runs the login HTTP handler, returning information about the response.

    Args:
      host: The value of the HTTP Host header.
      path_info: The absolute path of the request.
      cookie_dict: A cookie dictionary with the existing cookies.
      action: Value of the 'action' query argument.
      set_email: Value of the 'email' query argument.
      set_admin: Value of the 'admin' query argument.
      continue_url: Value of the 'continue' query argument.
      method: The HTTP method (e.g., 'GET').

    Returns:
      Tuple (status, location, set_cookie, content_type) where each
        value is the value of the corresponding header from the
        response; if no header exists, the value will be None. In the
        case of status, it will just return the integer status code
        and not the rest of the status message.
    """
    environ = {}
    wsgiref.util.setup_testing_defaults(environ)
    # The SERVER_NAME should never be used by the login module -- always defer
    # to the HTTP Host (so the user is not redirected to a different domain).
    environ['SERVER_NAME'] = 'do_not_use'
    environ['SERVER_PORT'] = '666'
    environ['SERVER_PROTOCOL'] = 'HTTP/1.1'
    environ['HTTP_HOST'] = host
    environ['PATH_INFO'] = path_info
    environ['REQUEST_METHOD'] = method
    if cookie_dict:
      cookie = Cookie.SimpleCookie(cookie_dict)
      cookie_value = ';'.join(m.OutputString() for m in cookie.values())
      environ['HTTP_COOKIE'] = cookie_value
    query_dict = {}
    if action:
      query_dict['action'] = action
    if set_email:
      query_dict['email'] = set_email
    if set_admin:
      query_dict['admin'] = set_admin
    if continue_url:
      query_dict['continue'] = continue_url
    if query_dict:
      environ['QUERY_STRING'] = urllib.urlencode(query_dict)

    response_dict = {}

    def start_response(status, headers):
      response_dict['status'] = int(status.split(' ', 1)[0])
      response_dict['headers'] = dict((k.lower(), v)
                                      for (k, v) in headers)

    login.application(environ, start_response)

    return (response_dict['status'],
            response_dict['headers'].get('location'),
            response_dict['headers'].get('set-cookie'),
            response_dict['headers'].get('content-type'))


if __name__ == '__main__':
  unittest.main()
