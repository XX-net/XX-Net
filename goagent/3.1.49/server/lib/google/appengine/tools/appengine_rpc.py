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




"""Tool for performing authenticated RPCs against App Engine."""


import google

import cookielib
import fancy_urllib
import logging
import os
import re
import socket
import sys
import urllib
import urllib2

#from google.appengine.tools import dev_appserver_login


logger = logging.getLogger('google.appengine.tools.appengine_rpc')

def GetPlatformToken(os_module=os, sys_module=sys, platform=sys.platform):
  """Returns a 'User-agent' token for the host system platform.

  Args:
    os_module, sys_module, platform: Used for testing.

  Returns:
    String containing the platform token for the host system.
  """
  if hasattr(sys_module, "getwindowsversion"):
    windows_version = sys_module.getwindowsversion()
    version_info = ".".join(str(i) for i in windows_version[:4])
    return platform + "/" + version_info
  elif hasattr(os_module, "uname"):
    uname = os_module.uname()
    return "%s/%s" % (uname[0], uname[2])
  else:
    return "unknown"

def HttpRequestToString(req, include_data=True):
  """Converts a urllib2.Request to a string.

  Args:
    req: urllib2.Request
  Returns:
    Multi-line string representing the request.
  """

  headers = ""
  for header in req.header_items():
    headers += "%s: %s\n" % (header[0], header[1])

  template = ("%(method)s %(selector)s %(type)s/1.1\n"
              "Host: %(host)s\n"
              "%(headers)s")
  if include_data:
    template = template + "\n%(data)s"

  return template % {
      'method' : req.get_method(),
      'selector' : req.get_selector(),
      'type' : req.get_type().upper(),
      'host' : req.get_host(),
      'headers': headers,
      'data': req.get_data(),
      }

class ClientLoginError(urllib2.HTTPError):
  """Raised to indicate there was an error authenticating with ClientLogin."""

  def __init__(self, url, code, msg, headers, args):
    urllib2.HTTPError.__init__(self, url, code, msg, headers, None)
    self.args = args
    self.app_reason = args["Error"]
    self.info = args.get("Info")

  def read(self):
    return '%d %s: %s' % (self.code, self.msg, self.reason)


class AbstractRpcServer(object):
  """Provides a common interface for a simple RPC server."""

  def __init__(self, host, auth_function, user_agent, source,
               host_override=None, extra_headers=None, save_cookies=False,
               auth_tries=3, account_type=None, debug_data=True, secure=True,
               rpc_tries=3):
    """Creates a new HttpRpcServer.

    Args:
      host: The host to send requests to.
      auth_function: A function that takes no arguments and returns an
        (email, password) tuple when called. Will be called if authentication
        is required.
      user_agent: The user-agent string to send to the server. Specify None to
        omit the user-agent header.
      source: The source to specify in authentication requests.
      host_override: The host header to send to the server (defaults to host).
      extra_headers: A dict of extra headers to append to every request. Values
        supplied here will override other default headers that are supplied.
      save_cookies: If True, save the authentication cookies to local disk.
        If False, use an in-memory cookiejar instead.  Subclasses must
        implement this functionality.  Defaults to False.
      auth_tries: The number of times to attempt auth_function before failing.
      account_type: One of GOOGLE, HOSTED_OR_GOOGLE, or None for automatic.
      debug_data: Whether debugging output should include data contents.
      rpc_tries: The number of rpc retries upon http server error (i.e.
        Response code >= 500 and < 600) before failing.
    """
    if secure:
      self.scheme = "https"
    else:
      self.scheme = "http"
    self.host = host
    self.host_override = host_override
    self.auth_function = auth_function
    self.source = source
    self.authenticated = False
    self.auth_tries = auth_tries
    self.debug_data = debug_data
    self.rpc_tries = rpc_tries


    self.account_type = account_type

    self.extra_headers = {}
    if user_agent:
      self.extra_headers["User-Agent"] = user_agent
    if extra_headers:
      self.extra_headers.update(extra_headers)

    self.save_cookies = save_cookies

    self.cookie_jar = cookielib.MozillaCookieJar()
    self.opener = self._GetOpener()
    if self.host_override:
      logger.info("Server: %s; Host: %s", self.host, self.host_override)
    else:
      logger.info("Server: %s", self.host)


    if ((self.host_override and self.host_override == "localhost") or
        self.host == "localhost" or self.host.startswith("localhost:")):
      self._DevAppServerAuthenticate()

  def _GetOpener(self):
    """Returns an OpenerDirector for making HTTP requests.

    Returns:
      A urllib2.OpenerDirector object.
    """
    raise NotImplemented()

  def _CreateRequest(self, url, data=None):
    """Creates a new urllib request."""
    req = fancy_urllib.FancyRequest(url, data=data)
    if self.host_override:
      req.add_header("Host", self.host_override)
    for key, value in self.extra_headers.iteritems():
      req.add_header(key, value)
    return req

  def _GetAuthToken(self, email, password):
    """Uses ClientLogin to authenticate the user, returning an auth token.

    Args:
      email:    The user's email address
      password: The user's password

    Raises:
      ClientLoginError: If there was an error authenticating with ClientLogin.
      HTTPError: If there was some other form of HTTP error.

    Returns:
      The authentication token returned by ClientLogin.
    """
    account_type = self.account_type
    if not account_type:

      if (self.host.split(':')[0].endswith(".google.com")
          or (self.host_override
              and self.host_override.split(':')[0].endswith(".google.com"))):

        account_type = "HOSTED_OR_GOOGLE"
      else:
        account_type = "GOOGLE"
    data = {
        "Email": email,
        "Passwd": password,
        "service": "ah",
        "source": self.source,
        "accountType": account_type
    }

    req = self._CreateRequest(
        url="https://www.google.com/accounts/ClientLogin",
        data=urllib.urlencode(data))
    try:
      response = self.opener.open(req, data=None, timeout=50)
      response_body = response.read()
      response_dict = dict(x.split("=")
                           for x in response_body.split("\n") if x)
      if os.getenv("APPENGINE_RPC_USE_SID", "0") == "1":
        self.extra_headers["Cookie"] = (
            'SID=%s; Path=/;' % response_dict["SID"])
      return response_dict["Auth"]
    except urllib2.HTTPError, e:
      if e.code == 403:
        body = e.read()
        # Add a line bellow to see the actual error
        logger.warn(body)
        response_dict = dict(x.split("=", 1) for x in body.split("\n") if x)
        raise ClientLoginError(req.get_full_url(), e.code, e.msg,
                               e.headers, response_dict)
      else:
        raise

  def _GetAuthCookie(self, auth_token):
    """Fetches authentication cookies for an authentication token.

    Args:
      auth_token: The authentication token returned by ClientLogin.

    Raises:
      HTTPError: If there was an error fetching the authentication cookies.
    """

    continue_location = "http://localhost/"
    args = {"continue": continue_location, "auth": auth_token}
    login_path = os.environ.get("APPCFG_LOGIN_PATH", "/_ah")
    req = self._CreateRequest("%s://%s%s/login?%s" %
                              (self.scheme, self.host, login_path,
                               urllib.urlencode(args)))
    try:
      response = self.opener.open(req)
    except urllib2.HTTPError, e:
      response = e
    if (response.code != 302 or
        response.info()["location"] != continue_location):
      raise urllib2.HTTPError(req.get_full_url(), response.code, response.msg,
                              response.headers, response.fp)
    self.authenticated = True

  def _Authenticate(self):
    """Authenticates the user.

    The authentication process works as follows:
     1) We get a username and password from the user
     2) We use ClientLogin to obtain an AUTH token for the user
        (see http://code.google.com/apis/accounts/AuthForInstalledApps.html).
     3) We pass the auth token to /_ah/login on the server to obtain an
        authentication cookie. If login was successful, it tries to redirect
        us to the URL we provided.

    If we attempt to access the upload API without first obtaining an
    authentication cookie, it returns a 401 response and directs us to
    authenticate ourselves with ClientLogin.
    """
    for unused_i in range(self.auth_tries):
      credentials = self.auth_function()
      try:
        auth_token = self._GetAuthToken(credentials[0], credentials[1])
        if os.getenv("APPENGINE_RPC_USE_SID", "0") == "1":
          return
      except ClientLoginError, e:
        if hasattr(e, 'app_reason') and e.app_reason == "BadAuthentication":
          if e.info == "InvalidSecondFactor":
            print >>sys.stderr, ("Use an application-specific password instead "
                                 "of your regular account password.")
            print >>sys.stderr, ("See http://www.google.com/"
                                 "support/accounts/bin/answer.py?answer=185833")
          else:
            print >>sys.stderr, "Invalid username or password."
            raise e
          continue
        if hasattr(e, 'app_reason') and e.app_reason == "CaptchaRequired":
          print >>sys.stderr, (
              "Please go to\n"
              "https://www.google.com/accounts/DisplayUnlockCaptcha\n"
              "and verify you are a human.  Then try again.")
          break
        if hasattr(e, 'app_reason') and e.app_reason == "NotVerified":
          print >>sys.stderr, "Account not verified."
          break
        if hasattr(e, 'app_reason') and e.app_reason == "TermsNotAgreed":
          print >>sys.stderr, "User has not agreed to TOS."
          break
        if hasattr(e, 'app_reason') and e.app_reason == "AccountDeleted":
          print >>sys.stderr, "The user account has been deleted."
          break
        if hasattr(e, 'app_reason') and e.app_reason == "AccountDisabled":
          print >>sys.stderr, "The user account has been disabled."
          break
        if hasattr(e, 'app_reason') and e.app_reason == "ServiceDisabled":
          print >>sys.stderr, ("The user's access to the service has been "
                               "disabled.")
          break
        if hasattr(e, 'app_reason') and e.app_reason == "ServiceUnavailable":
          print >>sys.stderr, "The service is not available; try again later."
          break
        raise
      self._GetAuthCookie(auth_token)
      return

  def _DevAppServerAuthenticate(self):
    """Authenticates the user on the dev_appserver."""
    credentials = self.auth_function()
    value = dev_appserver_login.CreateCookieData(credentials[0], True)
    self.extra_headers["Cookie"] = ('dev_appserver_login="%s"; Path=/;' % value)

  def Send(self, request_path, payload="",
           content_type="application/octet-stream",
           timeout=20,
           **kwargs):
    """Sends an RPC and returns the response.

    Args:
      request_path: The path to send the request to, eg /api/appversion/create.
      payload: The body of the request, or None to send an empty request.
      content_type: The Content-Type header to use.
      timeout: timeout in seconds; default None i.e. no timeout.
        (Note: for large requests on OS X, the timeout doesn't work right.)
      kwargs: Any keyword arguments are converted into query string parameters.

    Returns:
      The response body, as a string.
    """
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
      tries = 0
      auth_tried = False
      while True:
        tries += 1
        url = "%s://%s%s" % (self.scheme, self.host, request_path)
        if kwargs:
          url += "?" + urllib.urlencode(kwargs)
        req = self._CreateRequest(url=url, data=payload)
        req.add_header("Content-Type", content_type)



        req.add_header("X-appcfg-api-version", "1")
        try:
          logger.debug('Sending %s request:\n%s',
                       self.scheme.upper(),
                       HttpRequestToString(req, include_data=self.debug_data))
          f = self.opener.open(req)
          response = f.read()
          f.close()
          return response
        except urllib2.HTTPError, e:
          logger.debug("Got http error, this is try #%s", tries)
          if tries > self.rpc_tries:
            raise
          elif e.code == 401:

            if auth_tried:
              raise
            auth_tried = True
            self._Authenticate()
          elif e.code >= 500 and e.code < 600:

            continue
          elif e.code == 302:


            if auth_tried:
              raise
            auth_tried = True
            loc = e.info()["location"]
            logger.debug("Got 302 redirect. Location: %s", loc)
            if loc.startswith("https://www.google.com/accounts/ServiceLogin"):
              self._Authenticate()
            elif re.match(r"https://www.google.com/a/[a-z0-9.-]+/ServiceLogin",
                          loc):
              self.account_type = os.getenv("APPENGINE_RPC_HOSTED_LOGIN_TYPE",
                                            "HOSTED")
              self._Authenticate()
            elif loc.startswith("http://%s/_ah/login" % (self.host,)):
              self._DevAppServerAuthenticate()
            else:
              raise
          else:
            raise
    finally:
      socket.setdefaulttimeout(old_timeout)


class HttpRpcServer(AbstractRpcServer):
  """Provides a simplified RPC-style interface for HTTP requests."""

  DEFAULT_COOKIE_FILE_PATH = "~/.appcfg_cookies"

  def __init__(self, *args, **kwargs):
    self.certpath = os.path.normpath(os.path.join(
        os.path.dirname(__file__), '..', '..', '..', 'lib', 'cacerts',
        'cacerts.txt'))
    self.cert_file_available = os.path.exists(self.certpath)
    super(HttpRpcServer, self).__init__(*args, **kwargs)

  def _CreateRequest(self, url, data=None):
    """Creates a new urllib request."""
    req = super(HttpRpcServer, self)._CreateRequest(url, data)
    if self.cert_file_available and fancy_urllib.can_validate_certs():
      req.set_ssl_info(ca_certs=self.certpath)
    return req

  def _Authenticate(self):
    """Save the cookie jar after authentication."""
    if self.cert_file_available and not fancy_urllib.can_validate_certs():


      logger.warn("""ssl module not found.
Without the ssl module, the identity of the remote host cannot be verified, and
connections may NOT be secure. To fix this, please install the ssl module from
http://pypi.python.org/pypi/ssl .
To learn more, see http://code.google.com/appengine/kb/general.html#rpcssl .""")
    super(HttpRpcServer, self)._Authenticate()
    if self.cookie_jar.filename is not None and self.save_cookies:
      logger.info("Saving authentication cookies to %s",
                  self.cookie_jar.filename)
      self.cookie_jar.save()

  def _GetOpener(self):
    """Returns an OpenerDirector that supports cookies and ignores redirects.

    Returns:
      A urllib2.OpenerDirector object.
    """
    opener = urllib2.OpenerDirector()
    opener.add_handler(fancy_urllib.FancyProxyHandler())
    opener.add_handler(urllib2.UnknownHandler())
    opener.add_handler(urllib2.HTTPHandler())
    opener.add_handler(urllib2.HTTPDefaultErrorHandler())
    opener.add_handler(fancy_urllib.FancyHTTPSHandler())
    opener.add_handler(urllib2.HTTPErrorProcessor())

    if self.save_cookies:
      self.cookie_jar.filename = os.path.expanduser(
          HttpRpcServer.DEFAULT_COOKIE_FILE_PATH)

      if os.path.exists(self.cookie_jar.filename):
        try:
          self.cookie_jar.load()
          self.authenticated = True
          logger.info("Loaded authentication cookies from %s",
                      self.cookie_jar.filename)
        except (OSError, IOError, cookielib.LoadError), e:

          logger.debug("Could not load authentication cookies; %s: %s",
                       e.__class__.__name__, e)
          self.cookie_jar.filename = None
      else:


        try:
          fd = os.open(self.cookie_jar.filename, os.O_CREAT, 0600)
          os.close(fd)
        except (OSError, IOError), e:

          logger.debug("Could not create authentication cookies file; %s: %s",
                       e.__class__.__name__, e)
          self.cookie_jar.filename = None

    opener.add_handler(urllib2.HTTPCookieProcessor(self.cookie_jar))
    return opener
