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





"""Python datastore class User to be used as a datastore data type.

Classes defined here:
  User: object representing a user. A user could be a Google Accounts user
        or a federated user.
  Error: base exception type
  UserNotFoundError: UserService exception
  RedirectTooLongError: UserService exception
  NotAllowedError: UserService exception
"""












import os
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import user_service_pb
from google.appengine.runtime import apiproxy_errors


class Error(Exception):
  """Base User error type."""


class UserNotFoundError(Error):
  """Raised by User.__init__() when there's no email argument and no user is
  logged in."""


class RedirectTooLongError(Error):
  """Raised by UserService calls if the generated redirect URL was too long.
  """


class NotAllowedError(Error):
  """Raised by UserService calls if the requested redirect URL is not allowed.
  """


class User(object):
  """A user.

  We provide the email address, nickname, and id for a user.

  A nickname is a human-readable string which uniquely identifies a Google
  user, akin to a username. It will be an email address for some users, but
  not all.

  A user could be a Google Accounts user or a federated login user.

  federated_identity and federated_provider are only avaliable for
  federated users.
  """





  __user_id = None
  __federated_identity = None
  __federated_provider = None

  def __init__(self, email=None, _auth_domain=None,
               _user_id=None, federated_identity=None, federated_provider=None,
               _strict_mode=True):
    """Constructor.

    Args:
      email: An optional string of the user's email address. It defaults to
          the current user's email address.
      federated_identity: federated identity of user. It defaults to the current
          user's federated identity.
      federated_provider: federated provider url of user.

    Raises:
      UserNotFoundError: Raised if the user is not logged in and both email
          and federated identity are empty.
    """







    if _auth_domain is None:
      _auth_domain = os.environ.get('AUTH_DOMAIN')
    assert _auth_domain

    if email is None and federated_identity is None:
      email = os.environ.get('USER_EMAIL', email)
      _user_id = os.environ.get('USER_ID', _user_id)
      federated_identity = os.environ.get('FEDERATED_IDENTITY',
                                          federated_identity)
      federated_provider = os.environ.get('FEDERATED_PROVIDER',
                                          federated_provider)





    if email is None:
      email = ''

    if not email and not federated_identity and _strict_mode:


      raise UserNotFoundError

    self.__email = email
    self.__federated_identity = federated_identity
    self.__federated_provider = federated_provider
    self.__auth_domain = _auth_domain
    self.__user_id = _user_id or None


  def nickname(self):
    """Return this user's nickname.

    The nickname will be a unique, human readable identifier for this user
    with respect to this application. It will be an email address for some
    users, part of the email address for some users, and the federated identity
    for federated users who have not asserted an email address.
    """
    if (self.__email and self.__auth_domain and
        self.__email.endswith('@' + self.__auth_domain)):
      suffix_len = len(self.__auth_domain) + 1
      return self.__email[:-suffix_len]
    elif self.__federated_identity:
      return self.__federated_identity
    else:
      return self.__email

  def email(self):
    """Return this user's email address."""
    return self.__email

  def user_id(self):
    """Return either a permanent unique identifying string or None.

    If the email address was set explicity, this will return None.
    """
    return self.__user_id

  def auth_domain(self):
    """Return this user's auth domain.

    This method is internal and should not be used by client applications.
    """
    return self.__auth_domain

  def federated_identity(self):
    """Return this user's federated identity, None if not a federated user."""
    return self.__federated_identity

  def federated_provider(self):
    """Return this user's federated provider, None if not a federated user."""
    return self.__federated_provider

  def __unicode__(self):
    return unicode(self.nickname())

  def __str__(self):
    return str(self.nickname())

  def __repr__(self):
    values = []
    if self.__email:
      values.append("email='%s'" % self.__email)
    if self.__federated_identity:
      values.append("federated_identity='%s'" % self.__federated_identity)
    if self.__user_id:
      values.append("_user_id='%s'" % self.__user_id)
    return 'users.User(%s)' % ','.join(values)

  def __hash__(self):
    if self.__federated_identity:
      return hash((self.__federated_identity, self.__auth_domain))
    else:
      return hash((self.__email, self.__auth_domain))

  def __cmp__(self, other):
    if not isinstance(other, User):
      return NotImplemented
    if self.__federated_identity:
      return cmp((self.__federated_identity, self.__auth_domain),
                 (other.__federated_identity, other.__auth_domain))
    else:
      return cmp((self.__email, self.__auth_domain),
                 (other.__email, other.__auth_domain))


def create_login_url(dest_url=None, _auth_domain=None,
                     federated_identity=None):
  """Computes the login URL for redirection.

  Args:
    dest_url: String that is the desired final destination URL for the user
              once login is complete. If 'dest_url' does not have a host
              specified, we will use the host from the current request.
    federated_identity: federated_identity is used to trigger OpenId Login
                        flow, an empty value will trigger Google OpenID Login
                        by default.

  Returns:
       Login URL as a string. If federated_identity is set, this will be
       a federated login using the specified identity. If not, this
       will use Google Accounts.
  """
  req = user_service_pb.CreateLoginURLRequest()
  resp = user_service_pb.CreateLoginURLResponse()
  if dest_url:
    req.set_destination_url(dest_url)
  else:
    req.set_destination_url('')
  if _auth_domain:
    req.set_auth_domain(_auth_domain)
  if federated_identity:
    req.set_federated_identity(federated_identity)

  try:
    apiproxy_stub_map.MakeSyncCall('user', 'CreateLoginURL', req, resp)
  except apiproxy_errors.ApplicationError, e:
    if (e.application_error ==
        user_service_pb.UserServiceError.REDIRECT_URL_TOO_LONG):
      raise RedirectTooLongError
    elif (e.application_error ==
          user_service_pb.UserServiceError.NOT_ALLOWED):
      raise NotAllowedError
    else:
      raise e
  return resp.login_url()


CreateLoginURL = create_login_url


def create_logout_url(dest_url, _auth_domain=None):
  """Computes the logout URL for this request and specified destination URL,
     for both federated login App and Google Accounts App.

  Args:
    dest_url: String that is the desired final destination URL for the user
              once logout is complete. If 'dest_url' does not have a host
              specified, we will use the host from the current request.

  Returns:
    Logout URL as a string
  """
  req = user_service_pb.CreateLogoutURLRequest()
  resp = user_service_pb.CreateLogoutURLResponse()
  req.set_destination_url(dest_url)
  if _auth_domain:
    req.set_auth_domain(_auth_domain)

  try:
    apiproxy_stub_map.MakeSyncCall('user', 'CreateLogoutURL', req, resp)
  except apiproxy_errors.ApplicationError, e:
    if (e.application_error ==
        user_service_pb.UserServiceError.REDIRECT_URL_TOO_LONG):
      raise RedirectTooLongError
    else:
      raise e
  return resp.logout_url()


CreateLogoutURL = create_logout_url


def get_current_user():
  try:
    return User()
  except UserNotFoundError:
    return None


GetCurrentUser = get_current_user


def is_current_user_admin():
  """Return true if the user making this request is an admin for this
  application, false otherwise.

  We specifically make this a separate function, and not a member function of
  the User class, because admin status is not persisted in the datastore. It
  only exists for the user making this request right now.
  """
  return (os.environ.get('USER_IS_ADMIN', '0')) == '1'


IsCurrentUserAdmin = is_current_user_admin
