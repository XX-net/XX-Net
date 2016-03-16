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





"""Trivial implementation of the UserService."""




import logging
import os
import urllib
import urlparse
from google.appengine.api import apiproxy_stub
from google.appengine.api import user_service_pb

if os.environ.get('APPENGINE_RUNTIME') == 'python27':
  from google.appengine.runtime import apiproxy_errors
else:
  from google.appengine.runtime import apiproxy_errors

_DEFAULT_LOGIN_URL = 'https://www.google.com/accounts/Login?continue=%s'
_DEFAULT_LOGOUT_URL = 'https://www.google.com/accounts/Logout?continue=%s'
_DEFAULT_AUTH_DOMAIN = 'gmail.com'




_OAUTH_CONSUMER_KEY = 'example.com'
_OAUTH_EMAIL = 'example@example.com'
_OAUTH_USER_ID = '0'
_OAUTH_AUTH_DOMAIN = _DEFAULT_AUTH_DOMAIN
_OAUTH_CLIENT_ID = '123456789.apps.googleusercontent.com'

_OPENID_DEPRECATION_WARNING = (
    'Open ID 2.0 support in the App Engine Users service is deprecated and '
    'will soon be removed. Please see '
    'https://cloud.google.com/appengine/docs/deprecations/open_id '
    'for details.')


class UserServiceStub(apiproxy_stub.APIProxyStub):
  """Trivial implementation of the UserService."""

  _ACCEPTS_REQUEST_ID = True

  THREADSAFE = True

  def __init__(self,
               login_url=_DEFAULT_LOGIN_URL,
               logout_url=_DEFAULT_LOGOUT_URL,
               service_name='user',
               auth_domain=_DEFAULT_AUTH_DOMAIN,
               request_data=None):
    """Initializer.

    Args:
      login_url: String containing the URL to use for logging in.
      logout_url: String containing the URL to use for logging out.
      service_name: Service name expected for all calls.
      auth_domain: The authentication domain for the service e.g. "gmail.com".
      request_data: A apiproxy_stub.RequestData instance used to look up state
          associated with the request that generated an API call.

    Note: Both the login_url and logout_url arguments must contain one format
    parameter, which will be replaced with the continuation URL where the user
    should be redirected after log-in or log-out has been completed.
    """
    super(UserServiceStub, self).__init__(service_name,
                                          request_data=request_data)
    self._login_url = login_url
    self._logout_url = logout_url
    self.__scopes = None

    self.SetOAuthUser(is_admin=(os.environ.get('OAUTH_IS_ADMIN', '0') == '1'))




    os.environ['AUTH_DOMAIN'] = auth_domain

  def SetOAuthUser(self,
                   email=_OAUTH_EMAIL,
                   domain=_OAUTH_AUTH_DOMAIN,
                   user_id=_OAUTH_USER_ID,
                   is_admin=False,
                   scopes=None,
                   client_id=_OAUTH_CLIENT_ID):
    """Set test OAuth user.

    Determines what user is returned by requests to GetOAuthUser.

    Args:
      email: Email address of oauth user.  None indicates that no oauth user
        is authenticated.
      domain: Domain of oauth user.
      user_id: User ID of oauth user.
      is_admin:  Whether the user is an admin.
      scopes: List of scopes that user is authenticated against.
      client_id: Client ID of the OAuth2 request
    """
    self.__email = email
    self.__domain = domain
    self.__user_id = user_id
    self.__is_admin = is_admin
    self.__scopes = scopes
    self.__client_id = client_id

  def _Dynamic_CreateLoginURL(self, request, response, request_id):
    """Trivial implementation of UserService.CreateLoginURL().

    Args:
      request: a CreateLoginURLRequest
      response: a CreateLoginURLResponse
      request_id: A unique string identifying the request associated with the
          API call.
    """
    if request.has_federated_identity():
      logging.warning(_OPENID_DEPRECATION_WARNING)

    response.set_login_url(
        self._login_url %
        urllib.quote(self._AddHostToContinueURL(request.destination_url(),
                                                request_id)))

  def _Dynamic_CreateLogoutURL(self, request, response, request_id):
    """Trivial implementation of UserService.CreateLogoutURL().

    Args:
      request: a CreateLogoutURLRequest
      response: a CreateLogoutURLResponse
      request_id: A unique string identifying the request associated with the
          API call.
    """
    response.set_logout_url(
        self._logout_url %
        urllib.quote(self._AddHostToContinueURL(request.destination_url(),
                                                request_id)))

  def _Dynamic_GetOAuthUser(self, request, response, request_id):
    """Trivial implementation of UserService.GetOAuthUser().

    Args:
      request: a GetOAuthUserRequest
      response: a GetOAuthUserResponse
      request_id: A unique string identifying the request associated with the
          API call.
    """
    if self.__email is None:
      raise apiproxy_errors.ApplicationError(
          user_service_pb.UserServiceError.OAUTH_INVALID_REQUEST)
    else:
      if self.__scopes is None:
        authorized_scopes = set()
      else:

        authorized_scopes = set(request.scopes_list()).intersection(
            self.__scopes)
        if not authorized_scopes:
          raise apiproxy_errors.ApplicationError(
              user_service_pb.UserServiceError.OAUTH_INVALID_TOKEN)
      response.set_email(self.__email)
      response.set_user_id(self.__user_id)
      response.set_auth_domain(self.__domain)
      response.set_is_admin(self.__is_admin)
      response.set_client_id(self.__client_id)
      if request.request_writer_permission():
        response.set_is_project_writer(self.__is_admin)
      for scope in authorized_scopes:
        response.add_scopes(scope)

  def _Dynamic_CheckOAuthSignature(self, unused_request, response, request_id):
    """Trivial implementation of UserService.CheckOAuthSignature().

    Args:
      unused_request: a CheckOAuthSignatureRequest
      response: a CheckOAuthSignatureResponse
      request_id: A unique string identifying the request associated with the
          API call.
    """
    response.set_oauth_consumer_key(_OAUTH_CONSUMER_KEY)

  def _AddHostToContinueURL(self, continue_url, request_id):
    """Adds the request host to the continue url if no host is specified.

    Args:
      continue_url: the URL which may or may not have a host specified
      request_id: A unique string identifying the request associated with the
          API call.

    Returns:
      string
    """
    (protocol, host, path, parameters, query, fragment) = urlparse.urlparse(continue_url)

    if host and protocol:
      return continue_url

    try:
      protocol, host, _, _, _, _ = urlparse.urlparse(
          self.request_data.get_request_url(request_id))
    except KeyError:



      pass


    if path == '':
      path = '/'

    return urlparse.urlunparse(
      (protocol, host, path, parameters, query, fragment))
