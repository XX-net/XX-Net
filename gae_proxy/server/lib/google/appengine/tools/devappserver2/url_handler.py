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
"""Base functionality for handling HTTP requests."""



import logging
import wsgiref.util

from google.appengine.api import appinfo
from google.appengine.tools.devappserver2 import constants
from google.appengine.tools.devappserver2 import login


class URLHandler(object):
  """Abstract base class for subclasses that handle HTTP requests for a URL."""

  def __init__(self, url_pattern):
    """Initializer for URLHandler.

    Args:
      url_pattern: A re.RegexObject that matches URLs that should be handled by
          this handler. It may also optionally bind groups.
    """
    self._url_pattern = url_pattern

  def match(self, url):
    """Tests whether a given URL string matches this handler.

    Args:
      url: A URL string to match.
    Returns:
      A re.MatchObject containing the result of the match, if the URL string
      matches this handler. None, otherwise.
    """
    return self._url_pattern.match(url)

  def handle_authorization(self, environ, start_response):
    """Handles the response if the user is not authorized to access this URL.

    If the user is authorized, this method returns None without side effects.
    The default behaviour is to always authorize the user.

    If the user is not authorized, this method acts as a WSGI handler, calling
    the start_response function and returning the message body. The response
    will either redirect to the login page, or contain an error message, as
    specified by the 'auth_fail_action' setting.

    Args:
      environ: An environ dict for the current request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.

    Returns:
      An iterable over strings containing the body of an HTTP response, if the
      authorization check fails or the login UI must be displayed. None if the
      user is authorized to access the resource.
    """
    return None

  def handle(self, match, environ, start_response):
    """Serves the content associated with this handler.

    Args:
      match: The re.MatchObject containing the result of matching the URL
        against this handler's URL pattern.
      environ: An environ dict for the current request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.

    Returns:
      An iterable over strings containing the body of the HTTP response, or
      None if this handler is not applicable to this URL.
    """
    raise NotImplementedError()


class UserConfiguredURLHandler(URLHandler):
  """Abstract base class for handlers configured by the user.

  This provides common functionality for handlers that need to obey
  authorization restrictions.
  """

  def __init__(self, url_map, url_pattern):
    """Initializer for UserConfiguredURLHandler.

    Args:
      url_map: An appinfo.URLMap instance containing the configuration for this
          handler.
      url_pattern: A re.RegexObject that matches URLs that should be handled by
          this handler. It may also optionally bind groups.
    """
    super(UserConfiguredURLHandler, self).__init__(url_pattern)
    self._url_map = url_map

  def handle_authorization(self, environ, start_response):
    """Handles the response if the user is not authorized to access this URL.

    The authorization check is based on the 'login' setting for this handler,
    configured by the supplied url_map.

    Args:
      environ: An environ dict for the current request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.

    Returns:
      An iterable over strings containing the body of an HTTP response, if the
      authorization check fails or the login UI must be displayed. None if the
      user is authorized to access the resource.
    """
    admin_only = self._url_map.login == appinfo.LOGIN_ADMIN
    requires_login = self._url_map.login == appinfo.LOGIN_REQUIRED or admin_only
    auth_fail_action = self._url_map.auth_fail_action

    cookies = environ.get('HTTP_COOKIE')
    email_addr, admin, _ = login.get_user_info(cookies)

    if constants.FAKE_IS_ADMIN_HEADER in environ:
      admin = True

    if constants.FAKE_LOGGED_IN_HEADER in environ:
      email_addr = 'Fake User'

    # admin has an effect only with login: admin (not login: required).
    if requires_login and not email_addr and not (admin and admin_only):
      if auth_fail_action == appinfo.AUTH_FAIL_ACTION_REDIRECT:
        logging.debug('login required, redirecting user')
        return login.login_redirect(wsgiref.util.application_uri(environ),
                                    wsgiref.util.request_uri(environ),
                                    start_response)
      elif auth_fail_action == appinfo.AUTH_FAIL_ACTION_UNAUTHORIZED:
        logging.debug('login required, user unauthorized')
        start_response('401 Not authorized', [('Content-Type', 'text/html'),
                                              ('Cache-Control', 'no-cache')])
        return ['Login required to view page.']
    elif admin_only and not admin:
      logging.debug('admin required, user unauthorized')
      start_response('401 Not authorized', [('Content-Type', 'text/html'),
                                            ('Cache-Control', 'no-cache')])
      return ['Current logged in user %s is not '
              'authorized to view this page.'
              % email_addr]

    # Authorization check succeeded
    return None
