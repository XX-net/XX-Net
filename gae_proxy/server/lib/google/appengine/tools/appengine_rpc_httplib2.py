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
"""Library with a variant of appengine_rpc using httplib2.

The httplib2 module offers some of the features in appengine_rpc, with
one important one being a simple integration point for OAuth2 integration.
"""




import cStringIO
import logging
import os
import random
import re
import time
import types
import urllib
import urllib2

import httplib2

from oauth2client import client
from oauth2client import file as oauth2client_file
from oauth2client import tools
from google.appengine.tools.value_mixin import ValueMixin

logger = logging.getLogger('google.appengine.tools.appengine_rpc')


_TIMEOUT_WAIT_TIME = 5


class Error(Exception):
  pass


class AuthPermanentFail(Error):
  """Authentication will not succeed in the current context."""


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


def RaiseHttpError(url, response_info, response_body, extra_msg=''):
  """Raise a urllib2.HTTPError based on an httplib2 response tuple."""
  if response_body is not None:
    stream = cStringIO.StringIO()
    stream.write(response_body)
    stream.seek(0)
  else:
    stream = None
  if not extra_msg:
    msg = response_info.reason
  else:
    msg = response_info.reason + ' ' + extra_msg
  raise urllib2.HTTPError(url, response_info.status, msg, response_info, stream)


class HttpRpcServerHttpLib2(object):
  """A variant of HttpRpcServer which uses httplib2.

  This follows the same interface as appengine_rpc.AbstractRpcServer,
  but is a totally separate implementation.
  """

  def __init__(self, host, auth_function, user_agent, source,
               host_override=None, extra_headers=None, save_cookies=False,
               auth_tries=None, account_type=None, debug_data=True, secure=True,
               ignore_certs=False, rpc_tries=3, conflict_max_errors=10,
               timeout_max_errors=2, http_class=None):
    """Creates a new HttpRpcServerHttpLib2.

    Args:
      host: The host to send requests to.
      auth_function: Saved but ignored; may be used by subclasses.
      user_agent: The user-agent string to send to the server. Specify None to
        omit the user-agent header.
      source: Saved but ignored; may be used by subclasses.
      host_override: The host header to send to the server (defaults to host).
      extra_headers: A dict of extra headers to append to every request. Values
        supplied here will override other default headers that are supplied.
      save_cookies: Saved but ignored; may be used by subclasses.
      auth_tries: The number of times to attempt auth_function before failing.
      account_type: Saved but ignored; may be used by subclasses.
      debug_data: Whether debugging output should include data contents.
      secure: If the requests sent using Send should be sent over HTTPS.
      ignore_certs: If the certificate mismatches should be ignored.
      rpc_tries: The number of rpc retries upon http server error (i.e.
        Response code >= 500 and < 600) before failing.
      conflict_max_errors: The number of rpc retries upon http server error
        (i.e. Response code 409) before failing.
      timeout_max_errors: The number of rpc retries upon http server timeout
        (i.e. Response code 408) before failing.
      http_class: the httplib2.Http subclass to use. Defaults to httplib2.Http.
    """
    self.host = host
    self.auth_function = auth_function
    self.user_agent = user_agent
    self.source = source
    self.host_override = host_override
    self.extra_headers = extra_headers or {}
    self.save_cookies = save_cookies
    self.auth_max_errors = auth_tries
    self.account_type = account_type
    self.debug_data = debug_data
    self.secure = secure
    self.ignore_certs = ignore_certs
    self.rpc_max_errors = rpc_tries
    self.scheme = secure and 'https' or 'http'
    self.conflict_max_errors = conflict_max_errors
    self.timeout_max_errors = timeout_max_errors
    self.http_class = http_class if http_class is not None else httplib2.Http

    self.certpath = None
    self.cert_file_available = False
    if not self.ignore_certs:



      self.certpath = os.path.normpath(os.path.join(
          os.path.dirname(__file__), '..', '..', '..', 'lib', 'cacerts',
          'cacerts.txt'))
      self.cert_file_available = os.path.exists(self.certpath)

    self.memory_cache = MemoryCache()

  def _Authenticate(self, http, saw_error):
    """Pre or Re-auth stuff...

    Args:
      http: An 'Http' object from httplib2.
      saw_error: If the user has already tried to contact the server.
        If they have, it's OK to prompt them. If not, we should not be asking
        them for auth info--it's possible it'll suceed w/o auth.
    """


    raise NotImplementedError()

  def Send(self, request_path, payload='',
           content_type='application/octet-stream',
           timeout=None,
           **kwargs):
    """Sends an RPC and returns the response.

    Args:
      request_path: The path to send the request to, eg /api/appversion/create.
      payload: The body of the request, or None to send an empty request.
      content_type: The Content-Type header to use.
      timeout: timeout in seconds; default None i.e. no timeout.
        (Note: for large requests on OS X, the timeout doesn't work right.)
      Any keyword arguments are converted into query string parameters.

    Returns:
      The response body, as a string.

    Raises:
      AuthPermanentFail: If authorization failed in a permanent way.
      urllib2.HTTPError: On most HTTP errors.
    """









    self.http = self.http_class(
        cache=self.memory_cache, ca_certs=self.certpath,
        disable_ssl_certificate_validation=(not self.cert_file_available))
    self.http.follow_redirects = False
    self.http.timeout = timeout
    url = '%s://%s%s' % (self.scheme, self.host, request_path)
    if kwargs:
      url += '?' + urllib.urlencode(sorted(kwargs.items()))
    headers = {}
    if self.extra_headers:
      headers.update(self.extra_headers)



    headers['X-appcfg-api-version'] = '1'

    if payload is not None:
      method = 'POST'

      headers['content-length'] = str(len(payload))
      headers['Content-Type'] = content_type
    else:
      method = 'GET'
    if self.host_override:
      headers['Host'] = self.host_override

    rpc_errors = 0
    auth_errors = [0]
    conflict_errors = 0
    timeout_errors = 0

    def NeedAuth():
      """Marker that we need auth; it'll actually be tried next time around."""
      auth_errors[0] += 1
      logger.debug('Attempting to auth. This is try %s of %s.',
                   auth_errors[0], self.auth_max_errors)
      if auth_errors[0] > self.auth_max_errors:
        RaiseHttpError(url, response_info, response, 'Too many auth attempts.')

    while (rpc_errors < self.rpc_max_errors and
           conflict_errors < self.conflict_max_errors and
           timeout_errors < self.timeout_max_errors):
      self._Authenticate(self.http, auth_errors[0] > 0)
      logger.debug('Sending request to %s headers=%s body=%s',
                   url, headers,
                   self.debug_data and payload or payload and 'ELIDED' or '')
      try:
        response_info, response = self.http.request(
            url, method=method, body=payload, headers=headers)
      except client.AccessTokenRefreshError, e:

        logger.info('Got access token error', exc_info=1)
        response_info = httplib2.Response({'status': 401})
        response_info.reason = str(e)
        response = ''

      status = response_info.status
      if status == 200:
        return response
      logger.debug('Got http error %s.', response_info.status)
      if status == 401:
        NeedAuth()
        continue
      elif status == 408:
        timeout_errors += 1
        logger.debug('Got timeout error %s of %s. Retrying in %s seconds',
                     timeout_errors, self.timeout_max_errors,
                     _TIMEOUT_WAIT_TIME)
        time.sleep(_TIMEOUT_WAIT_TIME)
        continue
      elif status == 409:
        conflict_errors += 1

        wait_time = random.randint(0, 10)
        logger.debug('Got conflict error %s of %s. Retrying in %s seconds.',
                     conflict_errors, self.conflict_max_errors, wait_time)
        time.sleep(wait_time)
        continue
      elif status >= 500 and status < 600:

        rpc_errors += 1
        logger.debug('Retrying. This is attempt %s of %s.',
                     rpc_errors, self.rpc_max_errors)
        continue
      elif status == 302:


        loc = response_info.get('location')
        logger.debug('Got 302 redirect. Location: %s', loc)
        if (loc.startswith('https://www.google.com/accounts/ServiceLogin') or
            re.match(r'https://www\.google\.com/a/[a-z0-9.-]+/ServiceLogin',
                     loc)):
          NeedAuth()
          continue
        elif loc.startswith('http://%s/_ah/login' % (self.host,)):

          RaiseHttpError(url, response_info, response,
                         'dev_appserver login not supported')
        else:
          RaiseHttpError(url, response_info, response,
                         'Unexpected redirect to %s' % loc)
      else:
        logger.debug('Unexpected results: %s', response_info)
        RaiseHttpError(url, response_info, response,
                       'Unexpected HTTP status %s' % status)
    logging.info('Too many retries for url %s', url)
    RaiseHttpError(url, response_info, response)


class NoStorage(client.Storage):
  """A no-op implementation of storage."""

  def locked_get(self):
    return None

  def locked_put(self, credentials):
    pass


class HttpRpcServerOAuth2(HttpRpcServerHttpLib2):
  """A variant of HttpRpcServer which uses oauth2.

  This variant is specifically meant for interactive command line usage,
  as it will attempt to open a browser and ask the user to enter
  information from the resulting web page.
  """

  class OAuth2Parameters(ValueMixin):
    """Class encapsulating parameters related to OAuth2 authentication."""

    def __init__(self, access_token, client_id, client_secret, scope,
                 refresh_token, credential_file, token_uri=None,
                 credentials=None):
      self.access_token = access_token
      self.client_id = client_id
      self.client_secret = client_secret
      self.scope = scope
      self.refresh_token = refresh_token
      self.credential_file = credential_file
      self.token_uri = token_uri
      self.credentials = credentials

  class FlowFlags(object):

    def __init__(self, options):
      self.logging_level = logging.getLevelName(logging.getLogger().level)
      self.noauth_local_webserver = (not options.auth_local_webserver
                                     if options else True)
      self.auth_host_port = [8080, 8090]
      self.auth_host_name = 'localhost'

  def __init__(self, host, oauth2_parameters, user_agent, source,
               host_override=None, extra_headers=None, save_cookies=False,
               auth_tries=None, account_type=None, debug_data=True, secure=True,
               ignore_certs=False, rpc_tries=3, options=None, http_class=None):
    """Creates a new HttpRpcServerOAuth2.

    Args:
      host: The host to send requests to.
      oauth2_parameters: An object of type OAuth2Parameters (defined above)
        that specifies all parameters related to OAuth2 authentication. (This
        replaces the auth_function parameter in the parent class.)
      user_agent: The user-agent string to send to the server. Specify None to
        omit the user-agent header.
      source: Saved but ignored.
      host_override: The host header to send to the server (defaults to host).
      extra_headers: A dict of extra headers to append to every request. Values
        supplied here will override other default headers that are supplied.
      save_cookies: If the refresh token should be saved.
      auth_tries: The number of times to attempt auth_function before failing.
      account_type: Ignored.
      debug_data: Whether debugging output should include data contents.
      secure: If the requests sent using Send should be sent over HTTPS.
      ignore_certs: If the certificate mismatches should be ignored.
      rpc_tries: The number of rpc retries upon http server error (i.e.
        Response code >= 500 and < 600) before failing.
      options: the command line options.
      http_class: the httplib2.Http subclass to use. Defaults to httplib2.Http.
    """
    super(HttpRpcServerOAuth2, self).__init__(
        host, None, user_agent, source, host_override=host_override,
        extra_headers=extra_headers, auth_tries=auth_tries,
        debug_data=debug_data, secure=secure, ignore_certs=ignore_certs,
        rpc_tries=rpc_tries, save_cookies=save_cookies, http_class=http_class)

    if not isinstance(oauth2_parameters, self.OAuth2Parameters):
      raise TypeError('oauth2_parameters must be an OAuth2Parameters: %r' %
                      oauth2_parameters)
    self.oauth2_parameters = oauth2_parameters

    if save_cookies:
      oauth2_credential_file = (oauth2_parameters.credential_file
                                or '~/.appcfg_oauth2_tokens')
      self.storage = oauth2client_file.Storage(
          os.path.expanduser(oauth2_credential_file))
    else:
      self.storage = NoStorage()

    if oauth2_parameters.credentials:
      self.credentials = oauth2_parameters.credentials
    elif any((oauth2_parameters.access_token, oauth2_parameters.refresh_token,
              oauth2_parameters.token_uri)):
      token_uri = (oauth2_parameters.token_uri or
                   ('https://%s/o/oauth2/token' %
                    os.getenv('APPENGINE_AUTH_SERVER', 'accounts.google.com')))
      self.credentials = client.OAuth2Credentials(
          oauth2_parameters.access_token,
          oauth2_parameters.client_id,
          oauth2_parameters.client_secret,
          oauth2_parameters.refresh_token,
          None,
          token_uri,
          self.user_agent)
    else:
      self.credentials = self.storage.get()

    self.flags = self.FlowFlags(options)

  def _Authenticate(self, http, needs_auth):
    """Pre or Re-auth stuff...

    This will attempt to avoid making any OAuth related HTTP connections or
    user interactions unless it's needed.

    Args:
      http: An 'Http' object from httplib2.
      needs_auth: If the user has already tried to contact the server.
        If they have, it's OK to prompt them. If not, we should not be asking
        them for auth info--it's possible it'll suceed w/o auth, but if we have
        some credentials we'll use them anyway.

    Raises:
      AuthPermanentFail: The user has requested non-interactive auth but
        the token is invalid.
    """
    if needs_auth and (not self.credentials or self.credentials.invalid):




      if self.oauth2_parameters.access_token:
        logger.debug('_Authenticate skipping auth because user explicitly '
                     'supplied an access token.')
        raise AuthPermanentFail('Access token is invalid.')
      if self.oauth2_parameters.refresh_token:
        logger.debug('_Authenticate skipping auth because user explicitly '
                     'supplied a refresh token.')
        raise AuthPermanentFail('Refresh token is invalid.')
      if self.oauth2_parameters.token_uri:
        logger.debug('_Authenticate skipping auth because user explicitly '
                     'supplied a Token URI, for example for service account '
                     'authentication with Compute Engine')
        raise AuthPermanentFail('Token URI did not yield a valid token: ' +
                                self.oauth_parameters.token_uri)
      logger.debug('_Authenticate requesting auth')
      flow = client.OAuth2WebServerFlow(
          client_id=self.oauth2_parameters.client_id,
          client_secret=self.oauth2_parameters.client_secret,
          scope=_ScopesToString(self.oauth2_parameters.scope),
          user_agent=self.user_agent)
      self.credentials = tools.run_flow(flow, self.storage, self.flags)
    if self.credentials and not self.credentials.invalid:


      if not self.credentials.access_token_expired or needs_auth:
        logger.debug('_Authenticate configuring auth; needs_auth=%s',
                     needs_auth)
        self.credentials.authorize(http)
        return
    logger.debug('_Authenticate skipped auth; needs_auth=%s', needs_auth)


def _ScopesToString(scopes):
  """Converts scope value to a string."""


  if isinstance(scopes, types.StringTypes):
    return scopes
  else:
    return ' '.join(scopes)
