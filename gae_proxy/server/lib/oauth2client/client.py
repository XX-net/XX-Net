# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""An OAuth 2.0 client.

Tools for interacting with OAuth 2.0 protected resources.
"""

__author__ = 'jcgregorio@google.com (Joe Gregorio)'

import base64
import collections
import copy
import datetime
import json
import logging
import os
import socket
import sys
import tempfile
import time
import shutil
import six
from six.moves import urllib

import httplib2
from oauth2client import clientsecrets
from oauth2client import GOOGLE_AUTH_URI
from oauth2client import GOOGLE_DEVICE_URI
from oauth2client import GOOGLE_REVOKE_URI
from oauth2client import GOOGLE_TOKEN_URI
from oauth2client import util

HAS_OPENSSL = False
HAS_CRYPTO = False
try:
  from oauth2client import crypt
  HAS_CRYPTO = True
  if crypt.OpenSSLVerifier is not None:
    HAS_OPENSSL = True
except ImportError:
  pass

logger = logging.getLogger(__name__)

# Expiry is stored in RFC3339 UTC format
EXPIRY_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

# Which certs to use to validate id_tokens received.
ID_TOKEN_VERIFICATION_CERTS = 'https://www.googleapis.com/oauth2/v1/certs'
# This symbol previously had a typo in the name; we keep the old name
# around for now, but will remove it in the future.
ID_TOKEN_VERIFICATON_CERTS = ID_TOKEN_VERIFICATION_CERTS

# Constant to use for the out of band OAuth 2.0 flow.
OOB_CALLBACK_URN = 'urn:ietf:wg:oauth:2.0:oob'

# Google Data client libraries may need to set this to [401, 403].
REFRESH_STATUS_CODES = [401]

# The value representing user credentials.
AUTHORIZED_USER = 'authorized_user'

# The value representing service account credentials.
SERVICE_ACCOUNT = 'service_account'

# The environment variable pointing the file with local
# Application Default Credentials.
GOOGLE_APPLICATION_CREDENTIALS = 'GOOGLE_APPLICATION_CREDENTIALS'
# The ~/.config subdirectory containing gcloud credentials. Intended
# to be swapped out in tests.
_CLOUDSDK_CONFIG_DIRECTORY = 'gcloud'
# The environment variable name which can replace ~/.config if set.
_CLOUDSDK_CONFIG_ENV_VAR = 'CLOUDSDK_CONFIG'

# The error message we show users when we can't find the Application
# Default Credentials.
ADC_HELP_MSG = (
    'The Application Default Credentials are not available. They are available '
    'if running in Google Compute Engine. Otherwise, the environment variable '
    + GOOGLE_APPLICATION_CREDENTIALS +
    ' must be defined pointing to a file defining the credentials. See '
    'https://developers.google.com/accounts/docs/application-default-credentials'  # pylint:disable=line-too-long
    ' for more information.')

# The access token along with the seconds in which it expires.
AccessTokenInfo = collections.namedtuple(
    'AccessTokenInfo', ['access_token', 'expires_in'])

DEFAULT_ENV_NAME = 'UNKNOWN'

# If set to True _get_environment avoid GCE check (_detect_gce_environment)
NO_GCE_CHECK = os.environ.setdefault('NO_GCE_CHECK', 'False')

class SETTINGS(object):
  """Settings namespace for globally defined values."""
  env_name = None


class Error(Exception):
  """Base error for this module."""


class FlowExchangeError(Error):
  """Error trying to exchange an authorization grant for an access token."""


class AccessTokenRefreshError(Error):
  """Error trying to refresh an expired access token."""


class TokenRevokeError(Error):
  """Error trying to revoke a token."""


class UnknownClientSecretsFlowError(Error):
  """The client secrets file called for an unknown type of OAuth 2.0 flow. """


class AccessTokenCredentialsError(Error):
  """Having only the access_token means no refresh is possible."""


class VerifyJwtTokenError(Error):
  """Could not retrieve certificates for validation."""


class NonAsciiHeaderError(Error):
  """Header names and values must be ASCII strings."""


class ApplicationDefaultCredentialsError(Error):
  """Error retrieving the Application Default Credentials."""


class OAuth2DeviceCodeError(Error):
  """Error trying to retrieve a device code."""


class CryptoUnavailableError(Error, NotImplementedError):
  """Raised when a crypto library is required, but none is available."""


def _abstract():
  raise NotImplementedError('You need to override this function')


class MemoryCache(object):
  """httplib2 Cache implementation which only caches locally."""

  def __init__(self):
    self.cache = {}

  def get(self, key):
    return self.cache.get(key)

  def set(self, key, value):
    self.cache[key] = value

  def delete(self, key):
    self.cache.pop(key, None)


class Credentials(object):
  """Base class for all Credentials objects.

  Subclasses must define an authorize() method that applies the credentials to
  an HTTP transport.

  Subclasses must also specify a classmethod named 'from_json' that takes a JSON
  string as input and returns an instantiated Credentials object.
  """

  NON_SERIALIZED_MEMBERS = ['store']


  def authorize(self, http):
    """Take an httplib2.Http instance (or equivalent) and authorizes it.

    Authorizes it for the set of credentials, usually by replacing
    http.request() with a method that adds in the appropriate headers and then
    delegates to the original Http.request() method.

    Args:
      http: httplib2.Http, an http object to be used to make the refresh
        request.
    """
    _abstract()


  def refresh(self, http):
    """Forces a refresh of the access_token.

    Args:
      http: httplib2.Http, an http object to be used to make the refresh
        request.
    """
    _abstract()


  def revoke(self, http):
    """Revokes a refresh_token and makes the credentials void.

    Args:
      http: httplib2.Http, an http object to be used to make the revoke
        request.
    """
    _abstract()


  def apply(self, headers):
    """Add the authorization to the headers.

    Args:
      headers: dict, the headers to add the Authorization header to.
    """
    _abstract()

  def _to_json(self, strip):
    """Utility function that creates JSON repr. of a Credentials object.

    Args:
      strip: array, An array of names of members to not include in the JSON.

    Returns:
       string, a JSON representation of this instance, suitable to pass to
       from_json().
    """
    t = type(self)
    d = copy.copy(self.__dict__)
    for member in strip:
      if member in d:
        del d[member]
    if (d.get('token_expiry') and
        isinstance(d['token_expiry'], datetime.datetime)):
      d['token_expiry'] = d['token_expiry'].strftime(EXPIRY_FORMAT)
    # Add in information we will need later to reconsistitue this instance.
    d['_class'] = t.__name__
    d['_module'] = t.__module__
    for key, val in d.items():
      if isinstance(val, bytes):
        d[key] = val.decode('utf-8')
    return json.dumps(d)

  def to_json(self):
    """Creating a JSON representation of an instance of Credentials.

    Returns:
       string, a JSON representation of this instance, suitable to pass to
       from_json().
    """
    return self._to_json(Credentials.NON_SERIALIZED_MEMBERS)

  @classmethod
  def new_from_json(cls, s):
    """Utility class method to instantiate a Credentials subclass from a JSON
    representation produced by to_json().

    Args:
      s: string, JSON from to_json().

    Returns:
      An instance of the subclass of Credentials that was serialized with
      to_json().
    """
    if six.PY3 and isinstance(s, bytes):
      s = s.decode('utf-8')
    data = json.loads(s)
    # Find and call the right classmethod from_json() to restore the object.
    module = data['_module']
    try:
      m = __import__(module)
    except ImportError:
      # In case there's an object from the old package structure, update it
      module = module.replace('.googleapiclient', '')
      m = __import__(module)

    m = __import__(module, fromlist=module.split('.')[:-1])
    kls = getattr(m, data['_class'])
    from_json = getattr(kls, 'from_json')
    return from_json(s)

  @classmethod
  def from_json(cls, unused_data):
    """Instantiate a Credentials object from a JSON description of it.

    The JSON should have been produced by calling .to_json() on the object.

    Args:
      unused_data: dict, A deserialized JSON object.

    Returns:
      An instance of a Credentials subclass.
    """
    return Credentials()


class Flow(object):
  """Base class for all Flow objects."""
  pass


class Storage(object):
  """Base class for all Storage objects.

  Store and retrieve a single credential. This class supports locking
  such that multiple processes and threads can operate on a single
  store.
  """

  def acquire_lock(self):
    """Acquires any lock necessary to access this Storage.

    This lock is not reentrant.
    """
    pass

  def release_lock(self):
    """Release the Storage lock.

    Trying to release a lock that isn't held will result in a
    RuntimeError.
    """
    pass

  def locked_get(self):
    """Retrieve credential.

    The Storage lock must be held when this is called.

    Returns:
      oauth2client.client.Credentials
    """
    _abstract()

  def locked_put(self, credentials):
    """Write a credential.

    The Storage lock must be held when this is called.

    Args:
      credentials: Credentials, the credentials to store.
    """
    _abstract()

  def locked_delete(self):
    """Delete a credential.

    The Storage lock must be held when this is called.
    """
    _abstract()

  def get(self):
    """Retrieve credential.

    The Storage lock must *not* be held when this is called.

    Returns:
      oauth2client.client.Credentials
    """
    self.acquire_lock()
    try:
      return self.locked_get()
    finally:
      self.release_lock()

  def put(self, credentials):
    """Write a credential.

    The Storage lock must be held when this is called.

    Args:
      credentials: Credentials, the credentials to store.
    """
    self.acquire_lock()
    try:
      self.locked_put(credentials)
    finally:
      self.release_lock()

  def delete(self):
    """Delete credential.

    Frees any resources associated with storing the credential.
    The Storage lock must *not* be held when this is called.

    Returns:
      None
    """
    self.acquire_lock()
    try:
      return self.locked_delete()
    finally:
      self.release_lock()


def clean_headers(headers):
  """Forces header keys and values to be strings, i.e not unicode.

  The httplib module just concats the header keys and values in a way that may
  make the message header a unicode string, which, if it then tries to
  contatenate to a binary request body may result in a unicode decode error.

  Args:
    headers: dict, A dictionary of headers.

  Returns:
    The same dictionary but with all the keys converted to strings.
  """
  clean = {}
  try:
    for k, v in six.iteritems(headers):
      clean_k = k if isinstance(k, bytes) else str(k).encode('ascii')
      clean_v = v if isinstance(v, bytes) else str(v).encode('ascii')
      clean[clean_k] = clean_v
  except UnicodeEncodeError:
    raise NonAsciiHeaderError(k + ': ' + v)
  return clean


def _update_query_params(uri, params):
  """Updates a URI with new query parameters.

  Args:
    uri: string, A valid URI, with potential existing query parameters.
    params: dict, A dictionary of query parameters.

  Returns:
    The same URI but with the new query parameters added.
  """
  parts = urllib.parse.urlparse(uri)
  query_params = dict(urllib.parse.parse_qsl(parts.query))
  query_params.update(params)
  new_parts = parts._replace(query=urllib.parse.urlencode(query_params))
  return urllib.parse.urlunparse(new_parts)


class OAuth2Credentials(Credentials):
  """Credentials object for OAuth 2.0.

  Credentials can be applied to an httplib2.Http object using the authorize()
  method, which then adds the OAuth 2.0 access token to each request.

  OAuth2Credentials objects may be safely pickled and unpickled.
  """

  @util.positional(8)
  def __init__(self, access_token, client_id, client_secret, refresh_token,
               token_expiry, token_uri, user_agent, revoke_uri=None,
               id_token=None, token_response=None):
    """Create an instance of OAuth2Credentials.

    This constructor is not usually called by the user, instead
    OAuth2Credentials objects are instantiated by the OAuth2WebServerFlow.

    Args:
      access_token: string, access token.
      client_id: string, client identifier.
      client_secret: string, client secret.
      refresh_token: string, refresh token.
      token_expiry: datetime, when the access_token expires.
      token_uri: string, URI of token endpoint.
      user_agent: string, The HTTP User-Agent to provide for this application.
      revoke_uri: string, URI for revoke endpoint. Defaults to None; a token
        can't be revoked if this is None.
      id_token: object, The identity of the resource owner.
      token_response: dict, the decoded response to the token request. None
        if a token hasn't been requested yet. Stored because some providers
        (e.g. wordpress.com) include extra fields that clients may want.

    Notes:
      store: callable, A callable that when passed a Credential
        will store the credential back to where it came from.
        This is needed to store the latest access_token if it
        has expired and been refreshed.
    """
    self.access_token = access_token
    self.client_id = client_id
    self.client_secret = client_secret
    self.refresh_token = refresh_token
    self.store = None
    self.token_expiry = token_expiry
    self.token_uri = token_uri
    self.user_agent = user_agent
    self.revoke_uri = revoke_uri
    self.id_token = id_token
    self.token_response = token_response

    # True if the credentials have been revoked or expired and can't be
    # refreshed.
    self.invalid = False

  def authorize(self, http):
    """Authorize an httplib2.Http instance with these credentials.

    The modified http.request method will add authentication headers to each
    request and will refresh access_tokens when a 401 is received on a
    request. In addition the http.request method has a credentials property,
    http.request.credentials, which is the Credentials object that authorized
    it.

    Args:
       http: An instance of ``httplib2.Http`` or something that acts
         like it.

    Returns:
       A modified instance of http that was passed in.

    Example::

      h = httplib2.Http()
      h = credentials.authorize(h)

    You can't create a new OAuth subclass of httplib2.Authentication
    because it never gets passed the absolute URI, which is needed for
    signing. So instead we have to overload 'request' with a closure
    that adds in the Authorization header and then calls the original
    version of 'request()'.

    """
    request_orig = http.request

    # The closure that will replace 'httplib2.Http.request'.
    def new_request(uri, method='GET', body=None, headers=None,
                    redirections=httplib2.DEFAULT_MAX_REDIRECTS,
                    connection_type=None):
      if not self.access_token:
        logger.info('Attempting refresh to obtain initial access_token')
        self._refresh(request_orig)

      # Clone and modify the request headers to add the appropriate
      # Authorization header.
      if headers is None:
        headers = {}
      else:
        headers = dict(headers)
      self.apply(headers)

      if self.user_agent is not None:
        if 'user-agent' in headers:
          headers['user-agent'] = self.user_agent + ' ' + headers['user-agent']
        else:
          headers['user-agent'] = self.user_agent

      body_stream_position = None
      if all(getattr(body, stream_prop, None) for stream_prop in
             ('read', 'seek', 'tell')):
        body_stream_position = body.tell()

      resp, content = request_orig(uri, method, body, clean_headers(headers),
                                   redirections, connection_type)

      # A stored token may expire between the time it is retrieved and the time
      # the request is made, so we may need to try twice.
      max_refresh_attempts = 2
      for refresh_attempt in range(max_refresh_attempts):
        if resp.status not in REFRESH_STATUS_CODES:
          break
        logger.info('Refreshing due to a %s (attempt %s/%s)', resp.status,
                    refresh_attempt + 1, max_refresh_attempts)
        self._refresh(request_orig)
        self.apply(headers)
        if body_stream_position is not None:
          body.seek(body_stream_position)

        resp, content = request_orig(uri, method, body, clean_headers(headers),
                                     redirections, connection_type)

      return (resp, content)

    # Replace the request method with our own closure.
    http.request = new_request

    # Set credentials as a property of the request method.
    setattr(http.request, 'credentials', self)

    return http

  def refresh(self, http):
    """Forces a refresh of the access_token.

    Args:
      http: httplib2.Http, an http object to be used to make the refresh
        request.
    """
    self._refresh(http.request)

  def revoke(self, http):
    """Revokes a refresh_token and makes the credentials void.

    Args:
      http: httplib2.Http, an http object to be used to make the revoke
        request.
    """
    self._revoke(http.request)

  def apply(self, headers):
    """Add the authorization to the headers.

    Args:
      headers: dict, the headers to add the Authorization header to.
    """
    headers['Authorization'] = 'Bearer ' + self.access_token

  def to_json(self):
    return self._to_json(Credentials.NON_SERIALIZED_MEMBERS)

  @classmethod
  def from_json(cls, s):
    """Instantiate a Credentials object from a JSON description of it. The JSON
    should have been produced by calling .to_json() on the object.

    Args:
      data: dict, A deserialized JSON object.

    Returns:
      An instance of a Credentials subclass.
    """
    if six.PY3 and isinstance(s, bytes):
      s = s.decode('utf-8')
    data = json.loads(s)
    if (data.get('token_expiry') and
        not isinstance(data['token_expiry'], datetime.datetime)):
      try:
        data['token_expiry'] = datetime.datetime.strptime(
            data['token_expiry'], EXPIRY_FORMAT)
      except ValueError:
        data['token_expiry'] = None
    retval = cls(
        data['access_token'],
        data['client_id'],
        data['client_secret'],
        data['refresh_token'],
        data['token_expiry'],
        data['token_uri'],
        data['user_agent'],
        revoke_uri=data.get('revoke_uri', None),
        id_token=data.get('id_token', None),
        token_response=data.get('token_response', None))
    retval.invalid = data['invalid']
    return retval

  @property
  def access_token_expired(self):
    """True if the credential is expired or invalid.

    If the token_expiry isn't set, we assume the token doesn't expire.
    """
    if self.invalid:
      return True

    if not self.token_expiry:
      return False

    now = datetime.datetime.utcnow()
    if now >= self.token_expiry:
      logger.info('access_token is expired. Now: %s, token_expiry: %s',
                  now, self.token_expiry)
      return True
    return False

  def get_access_token(self, http=None):
    """Return the access token and its expiration information.

    If the token does not exist, get one.
    If the token expired, refresh it.
    """
    if not self.access_token or self.access_token_expired:
      if not http:
        http = httplib2.Http()
      self.refresh(http)
    return AccessTokenInfo(access_token=self.access_token,
                           expires_in=self._expires_in())

  def set_store(self, store):
    """Set the Storage for the credential.

    Args:
      store: Storage, an implementation of Storage object.
        This is needed to store the latest access_token if it
        has expired and been refreshed. This implementation uses
        locking to check for updates before updating the
        access_token.
    """
    self.store = store

  def _expires_in(self):
    """Return the number of seconds until this token expires.

    If token_expiry is in the past, this method will return 0, meaning the
    token has already expired.
    If token_expiry is None, this method will return None. Note that returning
    0 in such a case would not be fair: the token may still be valid;
    we just don't know anything about it.
    """
    if self.token_expiry:
      now = datetime.datetime.utcnow()
      if self.token_expiry > now:
        time_delta = self.token_expiry - now
        # TODO(orestica): return time_delta.total_seconds()
        # once dropping support for Python 2.6
        return time_delta.days * 86400 + time_delta.seconds
      else:
        return 0

  def _updateFromCredential(self, other):
    """Update this Credential from another instance."""
    self.__dict__.update(other.__getstate__())

  def __getstate__(self):
    """Trim the state down to something that can be pickled."""
    d = copy.copy(self.__dict__)
    del d['store']
    return d

  def __setstate__(self, state):
    """Reconstitute the state of the object from being pickled."""
    self.__dict__.update(state)
    self.store = None

  def _generate_refresh_request_body(self):
    """Generate the body that will be used in the refresh request."""
    body = urllib.parse.urlencode({
        'grant_type': 'refresh_token',
        'client_id': self.client_id,
        'client_secret': self.client_secret,
        'refresh_token': self.refresh_token,
        })
    return body

  def _generate_refresh_request_headers(self):
    """Generate the headers that will be used in the refresh request."""
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
    }

    if self.user_agent is not None:
      headers['user-agent'] = self.user_agent

    return headers

  def _refresh(self, http_request):
    """Refreshes the access_token.

    This method first checks by reading the Storage object if available.
    If a refresh is still needed, it holds the Storage lock until the
    refresh is completed.

    Args:
      http_request: callable, a callable that matches the method signature of
        httplib2.Http.request, used to make the refresh request.

    Raises:
      AccessTokenRefreshError: When the refresh fails.
    """
    if not self.store:
      self._do_refresh_request(http_request)
    else:
      self.store.acquire_lock()
      try:
        new_cred = self.store.locked_get()

        if (new_cred and not new_cred.invalid and
            new_cred.access_token != self.access_token and
            not new_cred.access_token_expired):
          logger.info('Updated access_token read from Storage')
          self._updateFromCredential(new_cred)
        else:
          self._do_refresh_request(http_request)
      finally:
        self.store.release_lock()

  def _do_refresh_request(self, http_request):
    """Refresh the access_token using the refresh_token.

    Args:
      http_request: callable, a callable that matches the method signature of
        httplib2.Http.request, used to make the refresh request.

    Raises:
      AccessTokenRefreshError: When the refresh fails.
    """
    body = self._generate_refresh_request_body()
    headers = self._generate_refresh_request_headers()

    logger.info('Refreshing access_token')
    resp, content = http_request(
        self.token_uri, method='POST', body=body, headers=headers)
    if six.PY3 and isinstance(content, bytes):
      content = content.decode('utf-8')
    if resp.status == 200:
      d = json.loads(content)
      self.token_response = d
      self.access_token = d['access_token']
      self.refresh_token = d.get('refresh_token', self.refresh_token)
      if 'expires_in' in d:
        self.token_expiry = datetime.timedelta(
            seconds=int(d['expires_in'])) + datetime.datetime.utcnow()
      else:
        self.token_expiry = None
      # On temporary refresh errors, the user does not actually have to
      # re-authorize, so we unflag here.
      self.invalid = False
      if self.store:
        self.store.locked_put(self)
    else:
      # An {'error':...} response body means the token is expired or revoked,
      # so we flag the credentials as such.
      logger.info('Failed to retrieve access token: %s', content)
      error_msg = 'Invalid response %s.' % resp['status']
      try:
        d = json.loads(content)
        if 'error' in d:
          error_msg = d['error']
          if 'error_description' in d:
            error_msg += ': ' + d['error_description']
          self.invalid = True
          if self.store:
            self.store.locked_put(self)
      except (TypeError, ValueError):
        pass
      raise AccessTokenRefreshError(error_msg)

  def _revoke(self, http_request):
    """Revokes this credential and deletes the stored copy (if it exists).

    Args:
      http_request: callable, a callable that matches the method signature of
        httplib2.Http.request, used to make the revoke request.
    """
    self._do_revoke(http_request, self.refresh_token or self.access_token)

  def _do_revoke(self, http_request, token):
    """Revokes this credential and deletes the stored copy (if it exists).

    Args:
      http_request: callable, a callable that matches the method signature of
        httplib2.Http.request, used to make the refresh request.
      token: A string used as the token to be revoked. Can be either an
        access_token or refresh_token.

    Raises:
      TokenRevokeError: If the revoke request does not return with a 200 OK.
    """
    logger.info('Revoking token')
    query_params = {'token': token}
    token_revoke_uri = _update_query_params(self.revoke_uri, query_params)
    resp, content = http_request(token_revoke_uri)
    if resp.status == 200:
      self.invalid = True
    else:
      error_msg = 'Invalid response %s.' % resp.status
      try:
        d = json.loads(content)
        if 'error' in d:
          error_msg = d['error']
      except (TypeError, ValueError):
        pass
      raise TokenRevokeError(error_msg)

    if self.store:
      self.store.delete()


class AccessTokenCredentials(OAuth2Credentials):
  """Credentials object for OAuth 2.0.

  Credentials can be applied to an httplib2.Http object using the
  authorize() method, which then signs each request from that object
  with the OAuth 2.0 access token. This set of credentials is for the
  use case where you have acquired an OAuth 2.0 access_token from
  another place such as a JavaScript client or another web
  application, and wish to use it from Python. Because only the
  access_token is present it can not be refreshed and will in time
  expire.

  AccessTokenCredentials objects may be safely pickled and unpickled.

  Usage::

    credentials = AccessTokenCredentials('<an access token>',
      'my-user-agent/1.0')
    http = httplib2.Http()
    http = credentials.authorize(http)

  Exceptions:
    AccessTokenCredentialsExpired: raised when the access_token expires or is
      revoked.
  """

  def __init__(self, access_token, user_agent, revoke_uri=None):
    """Create an instance of OAuth2Credentials

    This is one of the few types if Credentials that you should contrust,
    Credentials objects are usually instantiated by a Flow.

    Args:
      access_token: string, access token.
      user_agent: string, The HTTP User-Agent to provide for this application.
      revoke_uri: string, URI for revoke endpoint. Defaults to None; a token
        can't be revoked if this is None.
    """
    super(AccessTokenCredentials, self).__init__(
        access_token,
        None,
        None,
        None,
        None,
        None,
        user_agent,
        revoke_uri=revoke_uri)


  @classmethod
  def from_json(cls, s):
    if six.PY3 and isinstance(s, bytes):
      s = s.decode('utf-8')
    data = json.loads(s)
    retval = AccessTokenCredentials(
      data['access_token'],
      data['user_agent'])
    return retval

  def _refresh(self, http_request):
    raise AccessTokenCredentialsError(
        'The access_token is expired or invalid and can\'t be refreshed.')

  def _revoke(self, http_request):
    """Revokes the access_token and deletes the store if available.

    Args:
      http_request: callable, a callable that matches the method signature of
        httplib2.Http.request, used to make the revoke request.
    """
    self._do_revoke(http_request, self.access_token)


def _detect_gce_environment(urlopen=None):
  """Determine if the current environment is Compute Engine.

  Args:
      urlopen: Optional argument. Function used to open a connection to a URL.

  Returns:
      Boolean indicating whether or not the current environment is Google
          Compute Engine.
  """
  urlopen = urlopen or urllib.request.urlopen
  # Note: the explicit `timeout` below is a workaround. The underlying
  # issue is that resolving an unknown host on some networks will take
  # 20-30 seconds; making this timeout short fixes the issue, but
  # could lead to false negatives in the event that we are on GCE, but
  # the metadata resolution was particularly slow. The latter case is
  # "unlikely".
  try:
    response = urlopen('http://169.254.169.254/', timeout=1)
    return response.info().get('Metadata-Flavor', '') == 'Google'
  except socket.timeout:
    logger.info('Timeout attempting to reach GCE metadata service.')
    return False
  except urllib.error.URLError as e:
    if isinstance(getattr(e, 'reason', None), socket.timeout):
      logger.info('Timeout attempting to reach GCE metadata service.')
    return False


def _in_gae_environment():
  """Detects if the code is running in the App Engine environment.

  Returns:
     True if running in the GAE environment, False otherwise.
  """
  if SETTINGS.env_name is not None:
    return SETTINGS.env_name in ('GAE_PRODUCTION', 'GAE_LOCAL')

  try:
    import google.appengine
    server_software = os.environ.get('SERVER_SOFTWARE', '')
    if server_software.startswith('Google App Engine/'):
      SETTINGS.env_name = 'GAE_PRODUCTION'
      return True
    elif server_software.startswith('Development/'):
      SETTINGS.env_name = 'GAE_LOCAL'
      return True
  except ImportError:
    pass

  return False


def _in_gce_environment(urlopen=None):
  """Detect if the code is running in the Compute Engine environment.

  Args:
      urlopen: Optional argument. Function used to open a connection to a URL.

  Returns:
      True if running in the GCE environment, False otherwise.
  """
  if SETTINGS.env_name is not None:
    return SETTINGS.env_name == 'GCE_PRODUCTION'

  if NO_GCE_CHECK != 'True' and _detect_gce_environment(urlopen=urlopen):
    SETTINGS.env_name = 'GCE_PRODUCTION'
    return True
  return False


class GoogleCredentials(OAuth2Credentials):
  """Application Default Credentials for use in calling Google APIs.

  The Application Default Credentials are being constructed as a function of
  the environment where the code is being run.
  More details can be found on this page:
  https://developers.google.com/accounts/docs/application-default-credentials

  Here is an example of how to use the Application Default Credentials for a
  service that requires authentication:

      from googleapiclient.discovery import build
      from oauth2client.client import GoogleCredentials

      credentials = GoogleCredentials.get_application_default()
      service = build('compute', 'v1', credentials=credentials)

      PROJECT = 'bamboo-machine-422'
      ZONE = 'us-central1-a'
      request = service.instances().list(project=PROJECT, zone=ZONE)
      response = request.execute()

      print(response)
 """

  def __init__(self, access_token, client_id, client_secret, refresh_token,
               token_expiry, token_uri, user_agent,
               revoke_uri=GOOGLE_REVOKE_URI):
    """Create an instance of GoogleCredentials.

    This constructor is not usually called by the user, instead
    GoogleCredentials objects are instantiated by
    GoogleCredentials.from_stream() or
    GoogleCredentials.get_application_default().

    Args:
      access_token: string, access token.
      client_id: string, client identifier.
      client_secret: string, client secret.
      refresh_token: string, refresh token.
      token_expiry: datetime, when the access_token expires.
      token_uri: string, URI of token endpoint.
      user_agent: string, The HTTP User-Agent to provide for this application.
      revoke_uri: string, URI for revoke endpoint.
        Defaults to GOOGLE_REVOKE_URI; a token can't be revoked if this is None.
    """
    super(GoogleCredentials, self).__init__(
        access_token, client_id, client_secret, refresh_token, token_expiry,
        token_uri, user_agent, revoke_uri=revoke_uri)

  def create_scoped_required(self):
    """Whether this Credentials object is scopeless.

    create_scoped(scopes) method needs to be called in order to create
    a Credentials object for API calls.
    """
    return False

  def create_scoped(self, scopes):
    """Create a Credentials object for the given scopes.

    The Credentials type is preserved.
    """
    return self

  @property
  def serialization_data(self):
    """Get the fields and their values identifying the current credentials."""
    return {
        'type': 'authorized_user',
        'client_id': self.client_id,
        'client_secret': self.client_secret,
        'refresh_token': self.refresh_token
    }

  @staticmethod
  def _implicit_credentials_from_gae():
    """Attempts to get implicit credentials in Google App Engine env.

    If the current environment is not detected as App Engine, returns None,
    indicating no Google App Engine credentials can be detected from the
    current environment.

    Returns:
        None, if not in GAE, else an appengine.AppAssertionCredentials object.
    """
    if not _in_gae_environment():
      return None

    return _get_application_default_credential_GAE()

  @staticmethod
  def _implicit_credentials_from_gce():
    """Attempts to get implicit credentials in Google Compute Engine env.

    If the current environment is not detected as Compute Engine, returns None,
    indicating no Google Compute Engine credentials can be detected from the
    current environment.

    Returns:
        None, if not in GCE, else a gce.AppAssertionCredentials object.
    """
    if not _in_gce_environment():
      return None

    return _get_application_default_credential_GCE()

  @staticmethod
  def _implicit_credentials_from_files():
    """Attempts to get implicit credentials from local credential files.

    First checks if the environment variable GOOGLE_APPLICATION_CREDENTIALS
    is set with a filename and then falls back to a configuration file (the
    "well known" file) associated with the 'gcloud' command line tool.

    Returns:
        Credentials object associated with the GOOGLE_APPLICATION_CREDENTIALS
            file or the "well known" file if either exist. If neither file is
            define, returns None, indicating no credentials from a file can
            detected from the current environment.
    """
    credentials_filename = _get_environment_variable_file()
    if not credentials_filename:
      credentials_filename = _get_well_known_file()
      if os.path.isfile(credentials_filename):
        extra_help = (' (produced automatically when running'
                      ' "gcloud auth login" command)')
      else:
        credentials_filename = None
    else:
      extra_help = (' (pointed to by ' + GOOGLE_APPLICATION_CREDENTIALS +
                    ' environment variable)')

    if not credentials_filename:
      return

    # If we can read the credentials from a file, we don't need to know what
    # environment we are in.
    SETTINGS.env_name = DEFAULT_ENV_NAME

    try:
      return _get_application_default_credential_from_file(credentials_filename)
    except (ApplicationDefaultCredentialsError, ValueError) as error:
      _raise_exception_for_reading_json(credentials_filename, extra_help, error)

  @classmethod
  def _get_implicit_credentials(cls):
    """Gets credentials implicitly from the environment.

    Checks environment in order of precedence:
    - Google App Engine (production and testing)
    - Environment variable GOOGLE_APPLICATION_CREDENTIALS pointing to
      a file with stored credentials information.
    - Stored "well known" file associated with `gcloud` command line tool.
    - Google Compute Engine production environment.

    Exceptions:
      ApplicationDefaultCredentialsError: raised when the credentials fail
          to be retrieved.
    """

    # Environ checks (in order).
    environ_checkers = [
      cls._implicit_credentials_from_gae,
      cls._implicit_credentials_from_files,
      cls._implicit_credentials_from_gce,
    ]

    for checker in environ_checkers:
      credentials = checker()
      if credentials is not None:
        return credentials

    # If no credentials, fail.
    raise ApplicationDefaultCredentialsError(ADC_HELP_MSG)

  @staticmethod
  def get_application_default():
    """Get the Application Default Credentials for the current environment.

    Exceptions:
      ApplicationDefaultCredentialsError: raised when the credentials fail
                                          to be retrieved.
    """
    return GoogleCredentials._get_implicit_credentials()

  @staticmethod
  def from_stream(credential_filename):
    """Create a Credentials object by reading the information from a given file.

    It returns an object of type GoogleCredentials.

    Args:
      credential_filename: the path to the file from where the credentials
        are to be read

    Exceptions:
      ApplicationDefaultCredentialsError: raised when the credentials fail
                                          to be retrieved.
    """

    if credential_filename and os.path.isfile(credential_filename):
      try:
        return _get_application_default_credential_from_file(
            credential_filename)
      except (ApplicationDefaultCredentialsError, ValueError) as error:
        extra_help = ' (provided as parameter to the from_stream() method)'
        _raise_exception_for_reading_json(credential_filename,
                                          extra_help,
                                          error)
    else:
      raise ApplicationDefaultCredentialsError(
          'The parameter passed to the from_stream() '
          'method should point to a file.')


def _save_private_file(filename, json_contents):
  """Saves a file with read-write permissions on for the owner.

  Args:
    filename: String. Absolute path to file.
    json_contents: JSON serializable object to be saved.
  """
  temp_filename = tempfile.mktemp()
  file_desc = os.open(temp_filename, os.O_WRONLY | os.O_CREAT, 0o600)
  with os.fdopen(file_desc, 'w') as file_handle:
    json.dump(json_contents, file_handle, sort_keys=True,
              indent=2, separators=(',', ': '))
  shutil.move(temp_filename, filename)


def save_to_well_known_file(credentials, well_known_file=None):
  """Save the provided GoogleCredentials to the well known file.

  Args:
    credentials:
      the credentials to be saved to the well known file;
      it should be an instance of GoogleCredentials
    well_known_file:
      the name of the file where the credentials are to be saved;
      this parameter is supposed to be used for testing only
  """
  # TODO(orestica): move this method to tools.py
  # once the argparse import gets fixed (it is not present in Python 2.6)

  if well_known_file is None:
    well_known_file = _get_well_known_file()

  config_dir = os.path.dirname(well_known_file)
  if not os.path.isdir(config_dir):
    raise OSError('Config directory does not exist: %s' % config_dir)

  credentials_data = credentials.serialization_data
  _save_private_file(well_known_file, credentials_data)


def _get_environment_variable_file():
  application_default_credential_filename = (
      os.environ.get(GOOGLE_APPLICATION_CREDENTIALS,
                     None))

  if application_default_credential_filename:
    if os.path.isfile(application_default_credential_filename):
      return application_default_credential_filename
    else:
      raise ApplicationDefaultCredentialsError(
          'File ' + application_default_credential_filename + ' (pointed by ' +
          GOOGLE_APPLICATION_CREDENTIALS +
          ' environment variable) does not exist!')


def _get_well_known_file():
  """Get the well known file produced by command 'gcloud auth login'."""
  # TODO(orestica): Revisit this method once gcloud provides a better way
  # of pinpointing the exact location of the file.

  WELL_KNOWN_CREDENTIALS_FILE = 'application_default_credentials.json'

  default_config_dir = os.getenv(_CLOUDSDK_CONFIG_ENV_VAR)
  if default_config_dir is None:
    if os.name == 'nt':
      try:
        default_config_dir = os.path.join(os.environ['APPDATA'],
                                          _CLOUDSDK_CONFIG_DIRECTORY)
      except KeyError:
        # This should never happen unless someone is really messing with things.
        drive = os.environ.get('SystemDrive', 'C:')
        default_config_dir = os.path.join(drive, '\\',
                                          _CLOUDSDK_CONFIG_DIRECTORY)
    else:
      default_config_dir = os.path.join(os.path.expanduser('~'),
                                        '.config',
                                        _CLOUDSDK_CONFIG_DIRECTORY)

  return os.path.join(default_config_dir, WELL_KNOWN_CREDENTIALS_FILE)


def _get_application_default_credential_from_file(filename):
  """Build the Application Default Credentials from file."""

  from oauth2client import service_account

  # read the credentials from the file
  with open(filename) as file_obj:
    client_credentials = json.load(file_obj)

  credentials_type = client_credentials.get('type')
  if credentials_type == AUTHORIZED_USER:
    required_fields = set(['client_id', 'client_secret', 'refresh_token'])
  elif credentials_type == SERVICE_ACCOUNT:
    required_fields = set(['client_id', 'client_email', 'private_key_id',
                           'private_key'])
  else:
    raise ApplicationDefaultCredentialsError(
        "'type' field should be defined (and have one of the '" +
        AUTHORIZED_USER + "' or '" + SERVICE_ACCOUNT + "' values)")

  missing_fields = required_fields.difference(client_credentials.keys())

  if missing_fields:
    _raise_exception_for_missing_fields(missing_fields)

  if client_credentials['type'] == AUTHORIZED_USER:
    return GoogleCredentials(
        access_token=None,
        client_id=client_credentials['client_id'],
        client_secret=client_credentials['client_secret'],
        refresh_token=client_credentials['refresh_token'],
        token_expiry=None,
        token_uri=GOOGLE_TOKEN_URI,
        user_agent='Python client library')
  else:  # client_credentials['type'] == SERVICE_ACCOUNT
    return service_account._ServiceAccountCredentials(
        service_account_id=client_credentials['client_id'],
        service_account_email=client_credentials['client_email'],
        private_key_id=client_credentials['private_key_id'],
        private_key_pkcs8_text=client_credentials['private_key'],
        scopes=[])


def _raise_exception_for_missing_fields(missing_fields):
  raise ApplicationDefaultCredentialsError(
      'The following field(s) must be defined: ' + ', '.join(missing_fields))


def _raise_exception_for_reading_json(credential_file,
                                      extra_help,
                                      error):
  raise ApplicationDefaultCredentialsError(
      'An error was encountered while reading json file: '+
      credential_file + extra_help + ': ' + str(error))


def _get_application_default_credential_GAE():
  from oauth2client.appengine import AppAssertionCredentials

  return AppAssertionCredentials([])


def _get_application_default_credential_GCE():
  from oauth2client.gce import AppAssertionCredentials

  return AppAssertionCredentials([])


class AssertionCredentials(GoogleCredentials):
  """Abstract Credentials object used for OAuth 2.0 assertion grants.

  This credential does not require a flow to instantiate because it
  represents a two legged flow, and therefore has all of the required
  information to generate and refresh its own access tokens. It must
  be subclassed to generate the appropriate assertion string.

  AssertionCredentials objects may be safely pickled and unpickled.
  """

  @util.positional(2)
  def __init__(self, assertion_type, user_agent=None,
               token_uri=GOOGLE_TOKEN_URI,
               revoke_uri=GOOGLE_REVOKE_URI,
               **unused_kwargs):
    """Constructor for AssertionFlowCredentials.

    Args:
      assertion_type: string, assertion type that will be declared to the auth
        server
      user_agent: string, The HTTP User-Agent to provide for this application.
      token_uri: string, URI for token endpoint. For convenience
        defaults to Google's endpoints but any OAuth 2.0 provider can be used.
      revoke_uri: string, URI for revoke endpoint.
    """
    super(AssertionCredentials, self).__init__(
        None,
        None,
        None,
        None,
        None,
        token_uri,
        user_agent,
        revoke_uri=revoke_uri)
    self.assertion_type = assertion_type

  def _generate_refresh_request_body(self):
    assertion = self._generate_assertion()

    body = urllib.parse.urlencode({
        'assertion': assertion,
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        })

    return body

  def _generate_assertion(self):
    """Generate the assertion string that will be used in the access token
    request.
    """
    _abstract()

  def _revoke(self, http_request):
    """Revokes the access_token and deletes the store if available.

    Args:
      http_request: callable, a callable that matches the method signature of
        httplib2.Http.request, used to make the revoke request.
    """
    self._do_revoke(http_request, self.access_token)


def _RequireCryptoOrDie():
  """Ensure we have a crypto library, or throw CryptoUnavailableError.

  The oauth2client.crypt module requires either PyCrypto or PyOpenSSL
  to be available in order to function, but these are optional
  dependencies.
  """
  if not HAS_CRYPTO:
    raise CryptoUnavailableError('No crypto library available')


class SignedJwtAssertionCredentials(AssertionCredentials):
  """Credentials object used for OAuth 2.0 Signed JWT assertion grants.

  This credential does not require a flow to instantiate because it
  represents a two legged flow, and therefore has all of the required
  information to generate and refresh its own access tokens.

  SignedJwtAssertionCredentials requires either PyOpenSSL, or PyCrypto
  2.6 or later. For App Engine you may also consider using
  AppAssertionCredentials.
  """

  MAX_TOKEN_LIFETIME_SECS = 3600  # 1 hour in seconds

  @util.positional(4)
  def __init__(self,
               service_account_name,
               private_key,
               scope,
               private_key_password='notasecret',
               user_agent=None,
               token_uri=GOOGLE_TOKEN_URI,
               revoke_uri=GOOGLE_REVOKE_URI,
               **kwargs):
    """Constructor for SignedJwtAssertionCredentials.

    Args:
      service_account_name: string, id for account, usually an email address.
      private_key: string, private key in PKCS12 or PEM format.
      scope: string or iterable of strings, scope(s) of the credentials being
        requested.
      private_key_password: string, password for private_key, unused if
        private_key is in PEM format.
      user_agent: string, HTTP User-Agent to provide for this application.
      token_uri: string, URI for token endpoint. For convenience
        defaults to Google's endpoints but any OAuth 2.0 provider can be used.
      revoke_uri: string, URI for revoke endpoint.
      kwargs: kwargs, Additional parameters to add to the JWT token, for
        example sub=joe@xample.org.

    Raises:
      CryptoUnavailableError if no crypto library is available.
    """
    _RequireCryptoOrDie()
    super(SignedJwtAssertionCredentials, self).__init__(
        None,
        user_agent=user_agent,
        token_uri=token_uri,
        revoke_uri=revoke_uri,
        )

    self.scope = util.scopes_to_string(scope)

    # Keep base64 encoded so it can be stored in JSON.
    self.private_key = base64.b64encode(private_key)
    if isinstance(self.private_key, six.text_type):
      self.private_key = self.private_key.encode('utf-8')

    self.private_key_password = private_key_password
    self.service_account_name = service_account_name
    self.kwargs = kwargs

  @classmethod
  def from_json(cls, s):
    data = json.loads(s)
    retval = SignedJwtAssertionCredentials(
        data['service_account_name'],
        base64.b64decode(data['private_key']),
        data['scope'],
        private_key_password=data['private_key_password'],
        user_agent=data['user_agent'],
        token_uri=data['token_uri'],
        **data['kwargs']
        )
    retval.invalid = data['invalid']
    retval.access_token = data['access_token']
    return retval

  def _generate_assertion(self):
    """Generate the assertion that will be used in the request."""
    now = int(time.time())
    payload = {
        'aud': self.token_uri,
        'scope': self.scope,
        'iat': now,
        'exp': now + SignedJwtAssertionCredentials.MAX_TOKEN_LIFETIME_SECS,
        'iss': self.service_account_name
    }
    payload.update(self.kwargs)
    logger.debug(str(payload))

    private_key = base64.b64decode(self.private_key)
    return crypt.make_signed_jwt(crypt.Signer.from_string(
        private_key, self.private_key_password), payload)

# Only used in verify_id_token(), which is always calling to the same URI
# for the certs.
_cached_http = httplib2.Http(MemoryCache())

@util.positional(2)
def verify_id_token(id_token, audience, http=None,
                    cert_uri=ID_TOKEN_VERIFICATION_CERTS):
  """Verifies a signed JWT id_token.

  This function requires PyOpenSSL and because of that it does not work on
  App Engine.

  Args:
    id_token: string, A Signed JWT.
    audience: string, The audience 'aud' that the token should be for.
    http: httplib2.Http, instance to use to make the HTTP request. Callers
      should supply an instance that has caching enabled.
    cert_uri: string, URI of the certificates in JSON format to
      verify the JWT against.

  Returns:
    The deserialized JSON in the JWT.

  Raises:
    oauth2client.crypt.AppIdentityError: if the JWT fails to verify.
    CryptoUnavailableError: if no crypto library is available.
  """
  _RequireCryptoOrDie()
  if http is None:
    http = _cached_http

  resp, content = http.request(cert_uri)

  if resp.status == 200:
    certs = json.loads(content.decode('utf-8'))
    return crypt.verify_signed_jwt_with_certs(id_token, certs, audience)
  else:
    raise VerifyJwtTokenError('Status code: %d' % resp.status)


def _urlsafe_b64decode(b64string):
  # Guard against unicode strings, which base64 can't handle.
  if isinstance(b64string, six.text_type):
    b64string = b64string.encode('ascii')
  padded = b64string + b'=' * (4 - len(b64string) % 4)
  return base64.urlsafe_b64decode(padded)


def _extract_id_token(id_token):
  """Extract the JSON payload from a JWT.

  Does the extraction w/o checking the signature.

  Args:
    id_token: string or bytestring, OAuth 2.0 id_token.

  Returns:
    object, The deserialized JSON payload.
  """
  if type(id_token) == bytes:
    segments = id_token.split(b'.')
  else:
    segments = id_token.split(u'.')

  if len(segments) != 3:
    raise VerifyJwtTokenError(
        'Wrong number of segments in token: %s' % id_token)

  return json.loads(_urlsafe_b64decode(segments[1]).decode('utf-8'))


def _parse_exchange_token_response(content):
  """Parses response of an exchange token request.

  Most providers return JSON but some (e.g. Facebook) return a
  url-encoded string.

  Args:
    content: The body of a response

  Returns:
    Content as a dictionary object. Note that the dict could be empty,
    i.e. {}. That basically indicates a failure.
  """
  resp = {}
  try:
    resp = json.loads(content.decode('utf-8'))
  except Exception:
    # different JSON libs raise different exceptions,
    # so we just do a catch-all here
    content = content.decode('utf-8')
    resp = dict(urllib.parse.parse_qsl(content))

  # some providers respond with 'expires', others with 'expires_in'
  if resp and 'expires' in resp:
    resp['expires_in'] = resp.pop('expires')

  return resp


@util.positional(4)
def credentials_from_code(client_id, client_secret, scope, code,
                          redirect_uri='postmessage', http=None,
                          user_agent=None, token_uri=GOOGLE_TOKEN_URI,
                          auth_uri=GOOGLE_AUTH_URI,
                          revoke_uri=GOOGLE_REVOKE_URI,
                          device_uri=GOOGLE_DEVICE_URI):
  """Exchanges an authorization code for an OAuth2Credentials object.

  Args:
    client_id: string, client identifier.
    client_secret: string, client secret.
    scope: string or iterable of strings, scope(s) to request.
    code: string, An authorization code, most likely passed down from
      the client
    redirect_uri: string, this is generally set to 'postmessage' to match the
      redirect_uri that the client specified
    http: httplib2.Http, optional http instance to use to do the fetch
    token_uri: string, URI for token endpoint. For convenience
      defaults to Google's endpoints but any OAuth 2.0 provider can be used.
    auth_uri: string, URI for authorization endpoint. For convenience
      defaults to Google's endpoints but any OAuth 2.0 provider can be used.
    revoke_uri: string, URI for revoke endpoint. For convenience
      defaults to Google's endpoints but any OAuth 2.0 provider can be used.
    device_uri: string, URI for device authorization endpoint. For convenience
      defaults to Google's endpoints but any OAuth 2.0 provider can be used.

  Returns:
    An OAuth2Credentials object.

  Raises:
    FlowExchangeError if the authorization code cannot be exchanged for an
     access token
  """
  flow = OAuth2WebServerFlow(client_id, client_secret, scope,
                             redirect_uri=redirect_uri, user_agent=user_agent,
                             auth_uri=auth_uri, token_uri=token_uri,
                             revoke_uri=revoke_uri, device_uri=device_uri)

  credentials = flow.step2_exchange(code, http=http)
  return credentials


@util.positional(3)
def credentials_from_clientsecrets_and_code(filename, scope, code,
                                            message = None,
                                            redirect_uri='postmessage',
                                            http=None,
                                            cache=None,
                                            device_uri=None):
  """Returns OAuth2Credentials from a clientsecrets file and an auth code.

  Will create the right kind of Flow based on the contents of the clientsecrets
  file or will raise InvalidClientSecretsError for unknown types of Flows.

  Args:
    filename: string, File name of clientsecrets.
    scope: string or iterable of strings, scope(s) to request.
    code: string, An authorization code, most likely passed down from
      the client
    message: string, A friendly string to display to the user if the
      clientsecrets file is missing or invalid. If message is provided then
      sys.exit will be called in the case of an error. If message in not
      provided then clientsecrets.InvalidClientSecretsError will be raised.
    redirect_uri: string, this is generally set to 'postmessage' to match the
      redirect_uri that the client specified
    http: httplib2.Http, optional http instance to use to do the fetch
    cache: An optional cache service client that implements get() and set()
      methods. See clientsecrets.loadfile() for details.
    device_uri: string, OAuth 2.0 device authorization endpoint

  Returns:
    An OAuth2Credentials object.

  Raises:
    FlowExchangeError if the authorization code cannot be exchanged for an
     access token
    UnknownClientSecretsFlowError if the file describes an unknown kind of Flow.
    clientsecrets.InvalidClientSecretsError if the clientsecrets file is
      invalid.
  """
  flow = flow_from_clientsecrets(filename, scope, message=message, cache=cache,
                                 redirect_uri=redirect_uri,
                                 device_uri=device_uri)
  credentials = flow.step2_exchange(code, http=http)
  return credentials


class DeviceFlowInfo(collections.namedtuple('DeviceFlowInfo', (
    'device_code', 'user_code', 'interval', 'verification_url',
    'user_code_expiry'))):
  """Intermediate information the OAuth2 for devices flow."""

  @classmethod
  def FromResponse(cls, response):
    """Create a DeviceFlowInfo from a server response.

    The response should be a dict containing entries as described here:

      http://tools.ietf.org/html/draft-ietf-oauth-v2-05#section-3.7.1
    """
    # device_code, user_code, and verification_url are required.
    kwargs = {
        'device_code': response['device_code'],
        'user_code': response['user_code'],
    }
    # The response may list the verification address as either
    # verification_url or verification_uri, so we check for both.
    verification_url = response.get(
        'verification_url', response.get('verification_uri'))
    if verification_url is None:
      raise OAuth2DeviceCodeError(
          'No verification_url provided in server response')
    kwargs['verification_url'] = verification_url
    # expires_in and interval are optional.
    kwargs.update({
        'interval': response.get('interval'),
        'user_code_expiry': None,
    })
    if 'expires_in' in response:
      kwargs['user_code_expiry'] = datetime.datetime.now() + datetime.timedelta(
          seconds=int(response['expires_in']))

    return cls(**kwargs)

class OAuth2WebServerFlow(Flow):
  """Does the Web Server Flow for OAuth 2.0.

  OAuth2WebServerFlow objects may be safely pickled and unpickled.
  """

  @util.positional(4)
  def __init__(self, client_id,
               client_secret=None,
               scope=None,
               redirect_uri=None,
               user_agent=None,
               auth_uri=GOOGLE_AUTH_URI,
               token_uri=GOOGLE_TOKEN_URI,
               revoke_uri=GOOGLE_REVOKE_URI,
               login_hint=None,
               device_uri=GOOGLE_DEVICE_URI,
               authorization_header=None,
               **kwargs):
    """Constructor for OAuth2WebServerFlow.

    The kwargs argument is used to set extra query parameters on the
    auth_uri. For example, the access_type and approval_prompt
    query parameters can be set via kwargs.

    Args:
      client_id: string, client identifier.
      client_secret: string client secret.
      scope: string or iterable of strings, scope(s) of the credentials being
        requested.
      redirect_uri: string, Either the string 'urn:ietf:wg:oauth:2.0:oob' for
        a non-web-based application, or a URI that handles the callback from
        the authorization server.
      user_agent: string, HTTP User-Agent to provide for this application.
      auth_uri: string, URI for authorization endpoint. For convenience
        defaults to Google's endpoints but any OAuth 2.0 provider can be used.
      token_uri: string, URI for token endpoint. For convenience
        defaults to Google's endpoints but any OAuth 2.0 provider can be used.
      revoke_uri: string, URI for revoke endpoint. For convenience
        defaults to Google's endpoints but any OAuth 2.0 provider can be used.
      login_hint: string, Either an email address or domain. Passing this hint
        will either pre-fill the email box on the sign-in form or select the
        proper multi-login session, thereby simplifying the login flow.
      device_uri: string, URI for device authorization endpoint. For convenience
        defaults to Google's endpoints but any OAuth 2.0 provider can be used.
      authorization_header: string, For use with OAuth 2.0 providers that
        require a client to authenticate using a header value instead of passing
        client_secret in the POST body.
      **kwargs: dict, The keyword arguments are all optional and required
                        parameters for the OAuth calls.
    """
    # scope is a required argument, but to preserve backwards-compatibility
    # we don't want to rearrange the positional arguments
    if scope is None:
      raise TypeError("The value of scope must not be None")
    self.client_id = client_id
    self.client_secret = client_secret
    self.scope = util.scopes_to_string(scope)
    self.redirect_uri = redirect_uri
    self.login_hint = login_hint
    self.user_agent = user_agent
    self.auth_uri = auth_uri
    self.token_uri = token_uri
    self.revoke_uri = revoke_uri
    self.device_uri = device_uri
    self.authorization_header = authorization_header
    self.params = {
        'access_type': 'offline',
        'response_type': 'code',
    }
    self.params.update(kwargs)

  @util.positional(1)
  def step1_get_authorize_url(self, redirect_uri=None):
    """Returns a URI to redirect to the provider.

    Args:
      redirect_uri: string, Either the string 'urn:ietf:wg:oauth:2.0:oob' for
        a non-web-based application, or a URI that handles the callback from
        the authorization server. This parameter is deprecated, please move to
        passing the redirect_uri in via the constructor.

    Returns:
      A URI as a string to redirect the user to begin the authorization flow.
    """
    if redirect_uri is not None:
      logger.warning((
          'The redirect_uri parameter for '
          'OAuth2WebServerFlow.step1_get_authorize_url is deprecated. Please '
          'move to passing the redirect_uri in via the constructor.'))
      self.redirect_uri = redirect_uri

    if self.redirect_uri is None:
      raise ValueError('The value of redirect_uri must not be None.')

    query_params = {
        'client_id': self.client_id,
        'redirect_uri': self.redirect_uri,
        'scope': self.scope,
    }
    if self.login_hint is not None:
      query_params['login_hint'] = self.login_hint
    query_params.update(self.params)
    return _update_query_params(self.auth_uri, query_params)

  @util.positional(1)
  def step1_get_device_and_user_codes(self, http=None):
    """Returns a user code and the verification URL where to enter it

    Returns:
      A user code as a string for the user to authorize the application
      An URL as a string where the user has to enter the code
    """
    if self.device_uri is None:
      raise ValueError('The value of device_uri must not be None.')

    body = urllib.parse.urlencode({
        'client_id': self.client_id,
        'scope': self.scope,
    })
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
    }

    if self.user_agent is not None:
      headers['user-agent'] = self.user_agent

    if http is None:
      http = httplib2.Http()

    resp, content = http.request(self.device_uri, method='POST', body=body,
                                 headers=headers)
    if resp.status == 200:
      try:
        flow_info = json.loads(content)
      except ValueError as e:
        raise OAuth2DeviceCodeError(
            'Could not parse server response as JSON: "%s", error: "%s"' % (
                content, e))
      return DeviceFlowInfo.FromResponse(flow_info)
    else:
      error_msg = 'Invalid response %s.' % resp.status
      try:
        d = json.loads(content)
        if 'error' in d:
          error_msg += ' Error: %s' % d['error']
      except ValueError:
        # Couldn't decode a JSON response, stick with the default message.
        pass
      raise OAuth2DeviceCodeError(error_msg)

  @util.positional(2)
  def step2_exchange(self, code=None, http=None, device_flow_info=None):
    """Exchanges a code for OAuth2Credentials.

    Args:

      code: string, a dict-like object, or None. For a non-device
          flow, this is either the response code as a string, or a
          dictionary of query parameters to the redirect_uri. For a
          device flow, this should be None.
      http: httplib2.Http, optional http instance to use when fetching
          credentials.
      device_flow_info: DeviceFlowInfo, return value from step1 in the
          case of a device flow.

    Returns:
      An OAuth2Credentials object that can be used to authorize requests.

    Raises:
      FlowExchangeError: if a problem occurred exchanging the code for a
          refresh_token.
      ValueError: if code and device_flow_info are both provided or both
          missing.

    """
    if code is None and device_flow_info is None:
      raise ValueError('No code or device_flow_info provided.')
    if code is not None and device_flow_info is not None:
      raise ValueError('Cannot provide both code and device_flow_info.')

    if code is None:
      code = device_flow_info.device_code
    elif not isinstance(code, six.string_types):
      if 'code' not in code:
        raise FlowExchangeError(code.get(
            'error', 'No code was supplied in the query parameters.'))
      code = code['code']

    post_data = {
        'client_id': self.client_id,
        'code': code,
        'scope': self.scope,
    }
    if self.client_secret is not None:
      post_data['client_secret'] = self.client_secret
    if device_flow_info is not None:
      post_data['grant_type'] = 'http://oauth.net/grant_type/device/1.0'
    else:
      post_data['grant_type'] = 'authorization_code'
      post_data['redirect_uri'] = self.redirect_uri
    body = urllib.parse.urlencode(post_data)
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
    }
    if self.authorization_header is not None:
      headers['Authorization'] = self.authorization_header
    if self.user_agent is not None:
      headers['user-agent'] = self.user_agent

    if http is None:
      http = httplib2.Http()

    resp, content = http.request(self.token_uri, method='POST', body=body,
                                 headers=headers)
    d = _parse_exchange_token_response(content)
    if resp.status == 200 and 'access_token' in d:
      access_token = d['access_token']
      refresh_token = d.get('refresh_token', None)
      if not refresh_token:
        logger.info(
            'Received token response with no refresh_token. Consider '
            "reauthenticating with approval_prompt='force'.")
      token_expiry = None
      if 'expires_in' in d:
        token_expiry = datetime.datetime.utcnow() + datetime.timedelta(
            seconds=int(d['expires_in']))

      extracted_id_token = None
      if 'id_token' in d:
        extracted_id_token = _extract_id_token(d['id_token'])

      logger.info('Successfully retrieved access token')
      return OAuth2Credentials(access_token, self.client_id,
                               self.client_secret, refresh_token, token_expiry,
                               self.token_uri, self.user_agent,
                               revoke_uri=self.revoke_uri,
                               id_token=extracted_id_token,
                               token_response=d)
    else:
      logger.info('Failed to retrieve access token: %s', content)
      if 'error' in d:
        # you never know what those providers got to say
        error_msg = str(d['error']) + str(d.get('error_description', ''))
      else:
        error_msg = 'Invalid response: %s.' % str(resp.status)
      raise FlowExchangeError(error_msg)


@util.positional(2)
def flow_from_clientsecrets(filename, scope, redirect_uri=None,
                            message=None, cache=None, login_hint=None,
                            device_uri=None):
  """Create a Flow from a clientsecrets file.

  Will create the right kind of Flow based on the contents of the clientsecrets
  file or will raise InvalidClientSecretsError for unknown types of Flows.

  Args:
    filename: string, File name of client secrets.
    scope: string or iterable of strings, scope(s) to request.
    redirect_uri: string, Either the string 'urn:ietf:wg:oauth:2.0:oob' for
      a non-web-based application, or a URI that handles the callback from
      the authorization server.
    message: string, A friendly string to display to the user if the
      clientsecrets file is missing or invalid. If message is provided then
      sys.exit will be called in the case of an error. If message in not
      provided then clientsecrets.InvalidClientSecretsError will be raised.
    cache: An optional cache service client that implements get() and set()
      methods. See clientsecrets.loadfile() for details.
    login_hint: string, Either an email address or domain. Passing this hint
      will either pre-fill the email box on the sign-in form or select the
      proper multi-login session, thereby simplifying the login flow.
    device_uri: string, URI for device authorization endpoint. For convenience
      defaults to Google's endpoints but any OAuth 2.0 provider can be used.

  Returns:
    A Flow object.

  Raises:
    UnknownClientSecretsFlowError if the file describes an unknown kind of Flow.
    clientsecrets.InvalidClientSecretsError if the clientsecrets file is
      invalid.
  """
  try:
    client_type, client_info = clientsecrets.loadfile(filename, cache=cache)
    if client_type in (clientsecrets.TYPE_WEB, clientsecrets.TYPE_INSTALLED):
      constructor_kwargs = {
          'redirect_uri': redirect_uri,
          'auth_uri': client_info['auth_uri'],
          'token_uri': client_info['token_uri'],
          'login_hint': login_hint,
      }
      revoke_uri = client_info.get('revoke_uri')
      if revoke_uri is not None:
        constructor_kwargs['revoke_uri'] = revoke_uri
      if device_uri is not None:
        constructor_kwargs['device_uri'] = device_uri
      return OAuth2WebServerFlow(
          client_info['client_id'], client_info['client_secret'],
          scope, **constructor_kwargs)

  except clientsecrets.InvalidClientSecretsError:
    if message:
      sys.exit(message)
    else:
      raise
  else:
    raise UnknownClientSecretsFlowError(
        'This OAuth 2.0 flow is unsupported: %r' % client_type)
