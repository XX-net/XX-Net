#!/usr/bin/python2.4
#
# Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007 Python Software
# Foundation; All Rights Reserved

"""A HTTPSConnection/Handler with additional proxy and cert validation features.

In particular, monkey patches in Python r74203 to provide support for CONNECT
proxies and adds SSL cert validation if the ssl module is present.
"""

__author__ = "{frew,nick.johnson}@google.com (Fred Wulff and Nick Johnson)"

import base64
import httplib
import logging
import re
import socket
import urllib2

from urllib import splittype
from urllib import splituser
from urllib import splitpasswd

class InvalidCertificateException(httplib.HTTPException):
  """Raised when a certificate is provided with an invalid hostname."""

  def __init__(self, host, cert, reason):
    """Constructor.

    Args:
      host: The hostname the connection was made to.
      cert: The SSL certificate (as a dictionary) the host returned.
    """
    httplib.HTTPException.__init__(self)
    self.host = host
    self.cert = cert
    self.reason = reason

  def __str__(self):
    return ('Host %s returned an invalid certificate (%s): %s\n'
            'To learn more, see '
            'http://code.google.com/appengine/kb/general.html#rpcssl' %
            (self.host, self.reason, self.cert))

def can_validate_certs():
  """Return True if we have the SSL package and can validate certificates."""
  try:
    import ssl
    return True
  except ImportError:
    return False

def _create_fancy_connection(tunnel_host=None, key_file=None,
                             cert_file=None, ca_certs=None):
  # This abomination brought to you by the fact that
  # the HTTPHandler creates the connection instance in the middle
  # of do_open so we need to add the tunnel host to the class.

  class PresetProxyHTTPSConnection(httplib.HTTPSConnection):
    """An HTTPS connection that uses a proxy defined by the enclosing scope."""

    def __init__(self, *args, **kwargs):
      httplib.HTTPSConnection.__init__(self, *args, **kwargs)

      self._tunnel_host = tunnel_host
      if tunnel_host:
        logging.debug("Creating preset proxy https conn: %s", tunnel_host)

      self.key_file = key_file
      self.cert_file = cert_file
      self.ca_certs = ca_certs
      try:
        import ssl
        if self.ca_certs:
          self.cert_reqs = ssl.CERT_REQUIRED
        else:
          self.cert_reqs = ssl.CERT_NONE
      except ImportError:
        pass

    def _tunnel(self):
      self._set_hostport(self._tunnel_host, None)
      logging.info("Connecting through tunnel to: %s:%d",
                   self.host, self.port)
      self.send("CONNECT %s:%d HTTP/1.0\r\n\r\n" % (self.host, self.port))
      response = self.response_class(self.sock, strict=self.strict,
                                     method=self._method)
      (_, code, message) = response._read_status()

      if code != 200:
        self.close()
        raise socket.error, "Tunnel connection failed: %d %s" % (
            code, message.strip())

      while True:
        line = response.fp.readline()
        if line == "\r\n":
          break

    def _get_valid_hosts_for_cert(self, cert):
      """Returns a list of valid host globs for an SSL certificate.

      Args:
        cert: A dictionary representing an SSL certificate.
      Returns:
        list: A list of valid host globs.
      """
      if 'subjectAltName' in cert:
        return [x[1] for x in cert['subjectAltName'] if x[0].lower() == 'dns']
      else:
        # Return a list of commonName fields
        return [x[0][1] for x in cert['subject']
                if x[0][0].lower() == 'commonname']

    def _validate_certificate_hostname(self, cert, hostname):
      """Validates that a given hostname is valid for an SSL certificate.

      Args:
        cert: A dictionary representing an SSL certificate.
        hostname: The hostname to test.
      Returns:
        bool: Whether or not the hostname is valid for this certificate.
      """
      hosts = self._get_valid_hosts_for_cert(cert)
      for host in hosts:
        # Convert the glob-style hostname expression (eg, '*.google.com') into a
        # valid regular expression.
        host_re = host.replace('.', '\.').replace('*', '[^.]*')
        if re.search('^%s$' % (host_re,), hostname, re.I):
          return True
      return False


    def connect(self):
      # TODO(frew): When we drop support for <2.6 (in the far distant future),
      # change this to socket.create_connection.
      self.sock = _create_connection((self.host, self.port))

      if self._tunnel_host:
        self._tunnel()

      # ssl and FakeSocket got deprecated. Try for the new hotness of wrap_ssl,
      # with fallback.
      try:
        import ssl
        self.sock = ssl.wrap_socket(self.sock,
                                    keyfile=self.key_file,
                                    certfile=self.cert_file,
                                    ca_certs=self.ca_certs,
                                    cert_reqs=self.cert_reqs)

        if self.cert_reqs & ssl.CERT_REQUIRED:
          cert = self.sock.getpeercert()
          hostname = self.host.split(':', 0)[0]
          if not self._validate_certificate_hostname(cert, hostname):
            raise InvalidCertificateException(hostname, cert,
                                              'hostname mismatch')
      except ImportError:
        ssl = socket.ssl(self.sock,
                         keyfile=self.key_file,
                         certfile=self.cert_file)
        self.sock = httplib.FakeSocket(self.sock, ssl)

  return PresetProxyHTTPSConnection


# Here to end of _create_connection copied wholesale from Python 2.6"s socket.py
_GLOBAL_DEFAULT_TIMEOUT = object()


def _create_connection(address, timeout=_GLOBAL_DEFAULT_TIMEOUT):
  """Connect to *address* and return the socket object.

  Convenience function.  Connect to *address* (a 2-tuple ``(host,
  port)``) and return the socket object.  Passing the optional
  *timeout* parameter will set the timeout on the socket instance
  before attempting to connect.  If no *timeout* is supplied, the
  global default timeout setting returned by :func:`getdefaulttimeout`
  is used.
  """

  msg = "getaddrinfo returns an empty list"
  host, port = address
  for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
    af, socktype, proto, canonname, sa = res
    sock = None
    try:
      sock = socket.socket(af, socktype, proto)
      if timeout is not _GLOBAL_DEFAULT_TIMEOUT:
        sock.settimeout(timeout)
      sock.connect(sa)
      return sock

    except socket.error, msg:
      if sock is not None:
        sock.close()

  raise socket.error, msg


class FancyRequest(urllib2.Request):
  """A request that allows the use of a CONNECT proxy."""

  def __init__(self, *args, **kwargs):
    urllib2.Request.__init__(self, *args, **kwargs)
    self._tunnel_host = None
    self._key_file = None
    self._cert_file = None
    self._ca_certs = None

  def set_proxy(self, host, type):
    saved_type = None
    if self.get_type() == "https" and not self._tunnel_host:
      self._tunnel_host = self.get_host()
      saved_type = self.get_type()
    urllib2.Request.set_proxy(self, host, type)

    if saved_type:
      # Don't set self.type, we want to preserve the
      # type for tunneling.
      self.type = saved_type

  def set_ssl_info(self, key_file=None, cert_file=None, ca_certs=None):
    self._key_file = key_file
    self._cert_file = cert_file
    self._ca_certs = ca_certs


class FancyProxyHandler(urllib2.ProxyHandler):
  """A ProxyHandler that works with CONNECT-enabled proxies."""

  # Taken verbatim from /usr/lib/python2.5/urllib2.py
  def _parse_proxy(self, proxy):
    """Return (scheme, user, password, host/port) given a URL or an authority.

    If a URL is supplied, it must have an authority (host:port) component.
    According to RFC 3986, having an authority component means the URL must
    have two slashes after the scheme:

    >>> _parse_proxy('file:/ftp.example.com/')
    Traceback (most recent call last):
    ValueError: proxy URL with no authority: 'file:/ftp.example.com/'

    The first three items of the returned tuple may be None.

    Examples of authority parsing:

    >>> _parse_proxy('proxy.example.com')
    (None, None, None, 'proxy.example.com')
    >>> _parse_proxy('proxy.example.com:3128')
    (None, None, None, 'proxy.example.com:3128')

    The authority component may optionally include userinfo (assumed to be
    username:password):

    >>> _parse_proxy('joe:password@proxy.example.com')
    (None, 'joe', 'password', 'proxy.example.com')
    >>> _parse_proxy('joe:password@proxy.example.com:3128')
    (None, 'joe', 'password', 'proxy.example.com:3128')

    Same examples, but with URLs instead:

    >>> _parse_proxy('http://proxy.example.com/')
    ('http', None, None, 'proxy.example.com')
    >>> _parse_proxy('http://proxy.example.com:3128/')
    ('http', None, None, 'proxy.example.com:3128')
    >>> _parse_proxy('http://joe:password@proxy.example.com/')
    ('http', 'joe', 'password', 'proxy.example.com')
    >>> _parse_proxy('http://joe:password@proxy.example.com:3128')
    ('http', 'joe', 'password', 'proxy.example.com:3128')

    Everything after the authority is ignored:

    >>> _parse_proxy('ftp://joe:password@proxy.example.com/rubbish:3128')
    ('ftp', 'joe', 'password', 'proxy.example.com')

    Test for no trailing '/' case:

    >>> _parse_proxy('http://joe:password@proxy.example.com')
    ('http', 'joe', 'password', 'proxy.example.com')

    """
    scheme, r_scheme = splittype(proxy)
    if not r_scheme.startswith("/"):
      # authority
      scheme = None
      authority = proxy
    else:
      # URL
      if not r_scheme.startswith("//"):
        raise ValueError("proxy URL with no authority: %r" % proxy)
      # We have an authority, so for RFC 3986-compliant URLs (by ss 3.
      # and 3.3.), path is empty or starts with '/'
      end = r_scheme.find("/", 2)
      if end == -1:
        end = None
      authority = r_scheme[2:end]
    userinfo, hostport = splituser(authority)
    if userinfo is not None:
      user, password = splitpasswd(userinfo)
    else:
      user = password = None
    return scheme, user, password, hostport

  def proxy_open(self, req, proxy, type):
    # This block is copied wholesale from Python2.6 urllib2.
    # It is idempotent, so the superclass method call executes as normal
    # if invoked.
    orig_type = req.get_type()
    proxy_type, user, password, hostport = self._parse_proxy(proxy)
    if proxy_type is None:
      proxy_type = orig_type
    if user and password:
      user_pass = "%s:%s" % (urllib2.unquote(user), urllib2.unquote(password))
      creds = base64.b64encode(user_pass).strip()
      # Later calls overwrite earlier calls for the same header
      req.add_header("Proxy-authorization", "Basic " + creds)
    hostport = urllib2.unquote(hostport)
    req.set_proxy(hostport, proxy_type)
    # This condition is the change
    if orig_type == "https":
      return None

    return urllib2.ProxyHandler.proxy_open(self, req, proxy, type)


class FancyHTTPSHandler(urllib2.HTTPSHandler):
  """An HTTPSHandler that works with CONNECT-enabled proxies."""

  def do_open(self, http_class, req):
    # Intentionally very specific so as to opt for false negatives
    # rather than false positives.
    try:
      return urllib2.HTTPSHandler.do_open(
          self,
          _create_fancy_connection(req._tunnel_host,
                                   req._key_file,
                                   req._cert_file,
                                   req._ca_certs),
          req)
    except urllib2.URLError, url_error:
      try:
        import ssl
        if (type(url_error.reason) == ssl.SSLError and
            url_error.reason.args[0] == 1):
          # Display the reason to the user. Need to use args for python2.5
          # compat.
          raise InvalidCertificateException(req.host, '',
                                            url_error.reason.args[1])
      except ImportError:
        pass

      raise url_error


# We have to implement this so that we persist the tunneling behavior
# through redirects.
class FancyRedirectHandler(urllib2.HTTPRedirectHandler):
  """A redirect handler that persists CONNECT-enabled proxy information."""

  def redirect_request(self, req, *args, **kwargs):
    new_req = urllib2.HTTPRedirectHandler.redirect_request(
        self, req, *args, **kwargs)
    # Same thing as in our set_proxy implementation, but in this case
    # we"ve only got a Request to work with, so it was this or copy
    # everything over piecemeal.
    if hasattr(req, "_tunnel_host") and isinstance(new_req, urllib2.Request):
      if new_req.get_type() == "https":
        new_req._tunnel_host = new_req.get_host()
        new_req.set_proxy(req.host, "https")
        new_req.type = "https"
        new_req._key_file = req._key_file
        new_req._cert_file = req._cert_file
        new_req._ca_certs = req._ca_certs

    return new_req
