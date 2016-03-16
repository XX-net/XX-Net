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
"""Handles login/logout pages and dealing with user cookies.

Includes a WSGI application that serves the login page and handles login and
logout HTTP requests. It accepts these GET query parameters:

  continue: URL to redirect to after a login or logout has completed.
  email: Email address to set for the client.
  admin: If 'True', the client should be logged in as an admin.
  action: What action to take ('Login' or 'Logout').

To view the current user information and a form for logging in and out,
supply no parameters.
"""



import cgi
import Cookie
import hashlib
import logging
import urllib

import google
import webapp2

# URL of the login page within the dev appserver.
LOGIN_URL_RELATIVE = '_ah/login'

# CGI parameter constants.
CONTINUE_PARAM = 'continue'
_EMAIL_PARAM = 'email'
_ADMIN_PARAM = 'admin'
ACTION_PARAM = 'action'

# Values for the action parameter.
LOGOUT_ACTION = 'logout'
LOGIN_ACTION = 'login'

# Name of the cookie that stores the user info.
_COOKIE_NAME = 'dev_appserver_login'


def get_user_info(http_cookie, cookie_name=_COOKIE_NAME):
  """Gets the requestor's user info from an HTTP Cookie header.

  Args:
    http_cookie: The value of the 'Cookie' HTTP request header.
    cookie_name: The name of the cookie that stores the user info.

  Returns:
    A tuple (email, admin, user_id) where:
      email: The user's email address, if any.
      admin: True if the user is an admin; False otherwise.
      user_id: The user ID, if any.
  """
  try:
    cookie = Cookie.SimpleCookie(http_cookie)
  except Cookie.CookieError:
    return '', False, ''

  cookie_dict = dict((k, v.value) for k, v in cookie.iteritems())
  return _get_user_info_from_dict(cookie_dict, cookie_name)


def _get_user_info_from_dict(cookie_dict, cookie_name=_COOKIE_NAME):
  """Gets the requestor's user info from a cookie dictionary.

  Args:
    cookie_dict: A dictionary mapping cookie names onto values.
    cookie_name: The name of the cookie that stores the user info.

  Returns:
    A tuple (email, admin, user_id) where:
      email: The user's email address, if any.
      admin: True if the user is an admin; False otherwise.
      user_id: The user ID, if any.
  """
  cookie_value = cookie_dict.get(cookie_name, '')

  email, admin, user_id = (cookie_value.split(':') + ['', '', ''])[:3]
  if '@' not in email:
    if email:
      logging.warning('Ignoring invalid login cookie: %s', cookie_value)
    return '', False, ''
  return email, (admin == 'True'), user_id


def _create_cookie_data(email, admin):
  """Creates cookie payload data.

  Args:
    email: The user's email address.
    admin: True if the user is an admin; False otherwise.

  Returns:
    A string containing the cookie payload.
  """
  if email:
    user_id_digest = hashlib.md5(email.lower()).digest()
    user_id = '1' + ''.join(['%02d' % ord(x) for x in user_id_digest])[:20]
  else:
    user_id = ''
  return '%s:%s:%s' % (email, admin, user_id)


def _set_user_info_cookie(email, admin, cookie_name=_COOKIE_NAME):
  """Creates a cookie to set the user information for the requestor.

  Args:
    email: The email to set for the user.
    admin: True if the user should be admin; False otherwise.
    cookie_name: The name of the cookie that stores the user info.

  Returns:
    Set-Cookie value for setting the user info of the requestor.
  """
  cookie_value = _create_cookie_data(email, admin)
  cookie = Cookie.SimpleCookie()
  cookie[cookie_name] = cookie_value
  cookie[cookie_name]['path'] = '/'
  return cookie[cookie_name].OutputString()


def _clear_user_info_cookie(cookie_name=_COOKIE_NAME):
  """Clears the user info cookie from the requestor, logging them out.

  Args:
    cookie_name: The name of the cookie that stores the user info.

  Returns:
    A Set-Cookie value for clearing the user info of the requestor.
  """
  cookie = Cookie.SimpleCookie()
  cookie[cookie_name] = ''
  cookie[cookie_name]['path'] = '/'
  cookie[cookie_name]['max-age'] = '0'
  return cookie[cookie_name].OutputString()


_LOGIN_TEMPLATE = """<html>
<head>
  <title>Login</title>
</head>
<body>

<form method="get" action="%(login_url)s"
      style="text-align:center; font: 13px sans-serif">
  <div style="width: 20em; margin: 1em auto;
              text-align:left;
              padding: 0 2em 1.25em 2em;
              background-color: #d6e9f8;
              border: 2px solid #67a7e3">
    <h3>%(login_message)s</h3>
    <p style="padding: 0; margin: 0">
      <label for="email" style="width: 3em">Email:</label>
      <input name="email" type="email" value="%(email)s" id="email"/>
    </p>
    <p style="margin: .5em 0 0 3em; font-size:12px">
      <input name="admin" type="checkbox" value="True"
       %(admin_checked)s id="admin"/>
        <label for="admin">Sign in as Administrator</label>
    </p>
    <p style="margin-left: 3em">
      <input name="action" value="Login" type="submit"
             id="submit-login" />
      <input name="action" value="Logout" type="submit"
             id="submit-logout" />
    </p>
  </div>
  <input name="continue" type="hidden" value="%(continue_url)s"/>
</form>

</body>
</html>
"""


def _render_login_template(login_url, continue_url, email, admin):
  """Renders the login page.

  Args:
    login_url: The parameter to _login_response.
    continue_url: The parameter to _login_response.
    email: The email address of the current user, if any.
    admin: True if the user is currently an admin; False otherwise.

  Returns:
    A string containing the contents of the login page.
  """
  if email:
    login_message = 'Logged in'
  else:
    login_message = 'Not logged in'




    email = 'test\x40example.com'
  admin_checked = 'checked' if admin else ''

  template_dict = {
      'email': cgi.escape(email, quote=True),
      'admin_checked': admin_checked,
      'login_message': login_message,
      'login_url': cgi.escape(login_url, quote=True),
      'continue_url': cgi.escape(continue_url, quote=True),
  }

  return _LOGIN_TEMPLATE % template_dict


def login_redirect(application_url, continue_url, start_response):
  """Writes a login redirection URL to a user.

  This redirects to login_url with a continue parameter to return to
  continue_url. The login_url should be on the canonical front-end server,
  regardless of the host:port the user connected to.

  Args:
    application_url: The URL of the dev appserver domain
      (e.g., 'http://localhost:8080').
    continue_url: The URL to continue to after the user logs in.
    start_response: A WSGI start_response function.

  Returns:
    An (empty) iterable over strings containing the body of the HTTP response.
  """
  if not application_url.endswith('/'):
    application_url += '/'
  redirect_url = '%s%s?%s=%s' % (application_url, LOGIN_URL_RELATIVE,
                                 CONTINUE_PARAM, urllib.quote(continue_url))
  start_response('302 Requires login',
                 [('Location', redirect_url)])
  return []


class Handler(webapp2.RequestHandler):
  """The request handler for the login and logout pages."""

  def get(self):
    action = self.request.get(ACTION_PARAM)
    set_email = self.request.get(_EMAIL_PARAM)
    set_admin = self.request.get(_ADMIN_PARAM).lower() == 'true'
    continue_url = self.request.get(CONTINUE_PARAM)

    login_url = self.request.path_url

    if action:
      # Perform the action and then redirect
      if action.lower() == LOGOUT_ACTION.lower():
        self.response.headers['Set-Cookie'] = _clear_user_info_cookie()
      elif action.lower() == LOGIN_ACTION.lower() and set_email:
        self.response.headers['Set-Cookie'] = _set_user_info_cookie(set_email,
                                                                    set_admin)

      redirect_url = continue_url or login_url
      # URLs should be ASCII-only byte strings.
      if isinstance(redirect_url, unicode):
        redirect_url = redirect_url.encode('ascii')

      self.response.status = 302
      self.response.status_message = 'Redirecting to continue URL'
      self.response.headers['Location'] = redirect_url
    else:
      email, admin, _ = _get_user_info_from_dict(self.request.cookies)
      self.response.status = 200
      self.response.headers['Content-Type'] = 'text/html'
      body = _render_login_template(login_url, continue_url, email, admin)
      self.response.write(body)


application = webapp2.WSGIApplication([('/.*', Handler)], debug=True)
