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



"""Helper CGI for logins/logout in the development application server.

This CGI has these parameters:

  continue: URL to redirect to after a login or logout has completed.
  email: Email address to set for the client.
  admin: If 'True', the client should be logged in as an admin.
  action: What action to take ('Login' or 'Logout').

To view the current user information and a form for logging in and out,
supply no parameters.
"""


import cgi
import Cookie
import os
import sys
import urllib
import hashlib




CONTINUE_PARAM = 'continue'
EMAIL_PARAM = 'email'
ADMIN_PARAM = 'admin'
ACTION_PARAM = 'action'


LOGOUT_ACTION = 'Logout'
LOGIN_ACTION = 'Login'


LOGOUT_PARAM = 'action=%s' % LOGOUT_ACTION


COOKIE_NAME = 'dev_appserver_login'



def GetUserInfo(http_cookie, cookie_name=COOKIE_NAME):
  """Get the requestor's user info from the HTTP cookie in the CGI environment.

  Args:
    http_cookie: Value of the HTTP_COOKIE environment variable.
    cookie_name: Name of the cookie that stores the user info.

  Returns:
    Tuple (email, admin, user_id) where:
      email: The user's email address, if any.
      admin: True if the user is an admin; False otherwise.
      user_id: The user ID, if any.
  """
  try:
    cookie = Cookie.SimpleCookie(http_cookie)
  except Cookie.CookieError:
    return '', False, ''

  cookie_value = ''
  if cookie_name in cookie:
    cookie_value = cookie[cookie_name].value

  email, admin, user_id = (cookie_value.split(':') + ['', '', ''])[:3]
  return email, (admin == 'True'), user_id


def CreateCookieData(email, admin):
  """Creates cookie payload data.

  Args:
    email, admin: Parameters to incorporate into the cookie.

  Returns:
    String containing the cookie payload.
  """
  admin_string = 'False'
  if admin:
    admin_string = 'True'
  if email:
    user_id_digest = hashlib.md5(email.lower()).digest()
    user_id = '1' + ''.join(['%02d' % ord(x) for x in user_id_digest])[:20]
  else:
    user_id = ''
  return '%s:%s:%s' % (email, admin_string, user_id)


def SetUserInfoCookie(email, admin, cookie_name=COOKIE_NAME):
  """Creates a cookie to set the user information for the requestor.

  Args:
    email: Email to set for the user.
    admin: True if the user should be admin; False otherwise.
    cookie_name: Name of the cookie that stores the user info.

  Returns:
    'Set-Cookie' header for setting the user info of the requestor.
  """
  cookie_value = CreateCookieData(email, admin)
  set_cookie = Cookie.SimpleCookie()
  set_cookie[cookie_name] = cookie_value
  set_cookie[cookie_name]['path'] = '/'
  return '%s\r\n' % set_cookie


def ClearUserInfoCookie(cookie_name=COOKIE_NAME):
  """Clears the user info cookie from the requestor, logging them out.

  Args:
    cookie_name: Name of the cookie that stores the user info.

  Returns:
    'Set-Cookie' header for clearing the user info of the requestor.
  """
  set_cookie = Cookie.SimpleCookie()
  set_cookie[cookie_name] = ''
  set_cookie[cookie_name]['path'] = '/'
  set_cookie[cookie_name]['max-age'] = '0'
  return '%s\r\n' % set_cookie



LOGIN_TEMPLATE = """<html>
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
      <input name="email" type="text" value="%(email)s" id="email"/>
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


def RenderLoginTemplate(login_url, continue_url, email, admin):
  """Renders the login page.

  Args:
    login_url, continue_url, email, admin: Parameters passed to
      LoginCGI.

  Returns:
    String containing the contents of the login page.
  """
  login_message = 'Not logged in'
  if email:
    login_message = 'Logged in'
  admin_checked = ''
  if admin:
    admin_checked = 'checked'

  template_dict = {


    'email': (cgi.escape(email, quote=1) or 'test\x40example.com'),
    'admin_checked': admin_checked,
    'login_message': login_message,
    'login_url': cgi.escape(login_url, quote=1),
    'continue_url': cgi.escape(continue_url, quote=1)
  }

  return LOGIN_TEMPLATE % template_dict



def LoginRedirect(login_url,
                  hostname,
                  port,
                  relative_url,
                  outfile):
  """Writes a login redirection URL to a user.

  Args:
    login_url: Relative URL which should be used for handling user logins.
    hostname: Name of the host on which the webserver is running.
    port: Port on which the webserver is running.
    relative_url: String containing the URL accessed.
    outfile: File-like object to which the response should be written.
  """
  dest_url = "http://%s:%s%s" % (hostname, port, relative_url)
  redirect_url = 'http://%s:%s%s?%s=%s' % (hostname,
                                           port,
                                           login_url,
                                           CONTINUE_PARAM,
                                           urllib.quote(dest_url))
  outfile.write('Status: 302 Requires login\r\n')
  outfile.write('Location: %s\r\n\r\n' % redirect_url)


def LoginCGI(login_url,
             email,
             admin,
             action,
             set_email,
             set_admin,
             continue_url,
             outfile):
  """Runs the login CGI.

  This CGI does not care about the method at all. For both POST and GET the
  client will be redirected to the continue URL.

  Args:
    login_url: URL used to run the CGI.
    email: Current email address of the requesting user.
    admin: True if the requesting user is an admin; False otherwise.
    action: The action used to run the CGI; 'Login' for a login action, 'Logout'
      for when a logout should occur.
    set_email: Email to set for the user; Empty if no email should be set.
    set_admin: True if the user should be an admin; False otherwise.
    continue_url: URL to which the user should be redirected when the CGI
      finishes loading; defaults to the login_url with no parameters (showing
      current status) if not supplied.
    outfile: File-like object to which all output data should be written.
  """
  redirect_url = ''
  output_headers = []

  if action:
    if action.lower() == LOGOUT_ACTION.lower():
      output_headers.append(ClearUserInfoCookie())
    elif set_email:
      output_headers.append(SetUserInfoCookie(set_email, set_admin))

    redirect_url = continue_url or login_url

  if redirect_url:
    outfile.write('Status: 302 Redirecting to continue URL\r\n')
    for header in output_headers:
      outfile.write(header)
    outfile.write('Location: %s\r\n' % redirect_url)
    outfile.write('\r\n')
  else:
    outfile.write('Status: 200\r\n')
    outfile.write('Content-Type: text/html\r\n')
    outfile.write('\r\n')
    outfile.write(RenderLoginTemplate(login_url,
                                      continue_url,
                                      email,
                                      admin))



def main():
  """Runs the login and logout CGI script."""
  form = cgi.FieldStorage(environ=os.environ)
  login_url = os.environ['PATH_INFO']
  email = os.environ.get('USER_EMAIL', '')
  admin = os.environ.get('USER_IS_ADMIN', '0') == '1'

  action = form.getfirst(ACTION_PARAM)
  set_email = form.getfirst(EMAIL_PARAM, '')
  set_admin = form.getfirst(ADMIN_PARAM, '') == 'True'
  continue_url = form.getfirst(CONTINUE_PARAM, '')

  LoginCGI(login_url,
           email,
           admin,
           action,
           set_email,
           set_admin,
           continue_url,
           sys.stdout)
  return 0



if __name__ == '__main__':
  main()
