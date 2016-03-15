# Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007 Python Software
# Foundation; All Rights Reserved

"""A HTTPSConnection/Handler with additional proxy and cert validation features.

In particular, monkey patches in Python r74203 to provide support for CONNECT
proxies and adds SSL cert validation if the ssl module is present.
"""

__author__ = "{frew,nick.johnson}@google.com (Fred Wulff and Nick Johnson)"

import base64
import http.client
import logging
import socket
from urllib.parse import splitpasswd
from urllib.parse import splittype
from urllib.parse import splituser
import urllib.request, urllib.error, urllib.parse


class InvalidCertificateException(http.client.HTTPException):
  """Raised when a certificate is provided with an invalid hostname."""

  def __init__(self, host, cert, reason):
    """Constructor.

    Args:
      host: The hostname the connection was made to.
      cert: The SSL certificate (as a dictionary) the host returned.
      reason: user readable error reason.
    """
    http.client.HTTPException.__init__(self)
    self.host = host
    self.cert = cert
    self.reason = reason

  def __str__(self):
    return ("Host %s returned an invalid certificate (%s): %s\n"
            "To learn more, see "
            "http://code.google.com/appengine/kb/general.html#rpcssl" %
            (self.host, self.reason, self.cert))


try:
  import ssl
  _CAN_VALIDATE_CERTS = True
except ImportError:
  _CAN_VALIDATE_CERTS = False


def can_validate_certs():
  """Return True if we have the SSL package and can validate certificates."""
  return _CAN_VALIDATE_CERTS


# Reexport SSLError so clients don't have to to do their own checking for ssl's
# existence.
if can_validate_certs():
  SSLError = ssl.SSLError
else:
  SSLError = None


def create_fancy_connection(tunnel_host=None, key_file=None,
                            cert_file=None, ca_certs=None,
                            proxy_authorization=None):
  # This abomination brought to you by the fact that
  # the HTTPHandler creates the connection instance in the middle
  # of do_open so we need to add the tunnel host to the class.

  class PresetProxyHTTPSConnection(http.client.HTTPSConnection):
    """An HTTPS connection that uses a proxy defined by the enclosing scope."""

    def __init__(self, *args, **kwargs):
      http.client.HTTPSConnection.__init__(self, *args, **kwargs)

      self._tunnel_host = tunnel_host
      if tunnel_host:
        logging.debug("Creating preset proxy https conn: %s", tunnel_host)

      self.key_file = key_file
      self.cert_file = cert_file
      self.ca_certs = ca_certs
      if can_validate_certs():
        if self.ca_certs:
          self.cert_reqs = ssl.CERT_REQUIRED
        else:
          self.cert_reqs = ssl.CERT_NONE

    def _get_hostport(self, host, port):
      # Python 2.7.7rc1 (hg r90728:568041fd8090), 3.4.1 and 3.5 rename
      # _set_hostport to _get_hostport and changes it's functionality.  The
      # Python 2.7.7rc1 version of this method is included here for
      # compatibility with earlier versions of Python.  Without this, HTTPS over
      # HTTP CONNECT proxies cannot be used.

      # This method may be removed if compatibility with Python <2.7.7rc1 is not
      # required.

      # Python bug: http://bugs.python.org/issue7776
      if port is None:
        i = host.rfind(":")
        j = host.rfind("]")         # ipv6 addresses have [...]
        if i > j:
          try:
            port = int(host[i+1:])
          except ValueError:
            if host[i+1:] == "":  # http://foo.com:/ == http://foo.com/
              port = self.default_port
            else:
              raise http.client.InvalidURL("nonnumeric port: '%s'" % host[i+1:])
          host = host[:i]
        else:
          port = self.default_port
        if host and host[0] == "[" and host[-1] == "]":
          host = host[1:-1]

      return (host, port)

    def _tunnel(self):
      self.host, self.port = self._get_hostport(self._tunnel_host, None)
      logging.info("Connecting through tunnel to: %s:%d",
                   self.host, self.port)

      self.send("CONNECT %s:%d HTTP/1.0\r\n" % (self.host, self.port))

      if proxy_authorization:
        self.send("Proxy-Authorization: %s\r\n" % proxy_authorization)

      # blank line
      self.send("\r\n")

      response = self.response_class(self.sock, strict=self.strict,
                                     method=self._method)
      # pylint: disable=protected-access
      (_, code, message) = response._read_status()

      if code != 200:
        self.close()
        raise socket.error("Tunnel connection failed: %d %s" %
                           (code, message.strip()))

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
      if "subjectAltName" in cert:
        return [x[1] for x in cert["subjectAltName"] if x[0].lower() == "dns"]
      else:
        # Return a list of commonName fields
        return [x[0][1] for x in cert["subject"]
                if x[0][0].lower() == "commonname"]

    def _validate_certificate_hostname(self, cert, hostname):
      """Perform RFC2818/6125 validation against a cert and hostname.

      Args:
        cert: A dictionary representing an SSL certificate.
        hostname: The hostname to test.
      Returns:
        bool: Whether or not the hostname is valid for this certificate.
      """
      hosts = self._get_valid_hosts_for_cert(cert)
      for host in hosts:
        # Wildcards are only valid when the * exists at the end of the last
        # (left-most) label, and there are at least 3 labels in the expression.
        if ("*." in host and host.count("*") == 1 and
            host.count(".") > 1 and "." in hostname):
          left_expected, right_expected = host.split("*.")
          left_hostname, right_hostname = hostname.split(".", 1)
          if (left_hostname.startswith(left_expected) and
              right_expected == right_hostname):
            return True
        elif host == hostname:
          return True
      return False

    def connect(self):
      # TODO(frew): When we drop support for <2.6 (in the far distant future),
      # change this to socket.create_connection.
      self.sock = _create_connection((self.host, self.port))

      if self._tunnel_host:
        self._tunnel()

      # ssl and FakeSocket got deprecated. Try for the new hotness of wrap_ssl,
      # with fallback. Note: Since can_validate_certs() just checks for the
      # ssl module, it's equivalent to attempting to import ssl from
      # the function, but doesn't require a dynamic import, which doesn't
      # play nicely with dev_appserver.
      if can_validate_certs():
        self.sock = ssl.wrap_socket(self.sock,
                                    keyfile=self.key_file,
                                    certfile=self.cert_file,
                                    ca_certs=self.ca_certs,
                                    cert_reqs=self.cert_reqs)

        if self.cert_reqs & ssl.CERT_REQUIRED:
          cert = self.sock.getpeercert()
          hostname = self.host.split(":", 0)[0]
          if not self._validate_certificate_hostname(cert, hostname):
            raise InvalidCertificateException(hostname, cert,
                                              "hostname mismatch")
      else:
        ssl_socket = socket.ssl(self.sock,
                                keyfile=self.key_file,
                                certfile=self.cert_file)
        self.sock = http.client.FakeSocket(self.sock, ssl_socket)

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

    except socket.error as msg:
      if sock is not None:
        sock.close()

  raise socket.error(msg)


class FancyRequest(urllib.request.Request):
  """A request that allows the use of a CONNECT proxy."""

  def __init__(self, *args, **kwargs):
    urllib.request.Request.__init__(self, *args, **kwargs)
    self._tunnel_host = None
    self._key_file = None
    self._cert_file = None
    self._ca_certs = None

  def set_proxy(self, host, type):
    saved_type = None

    if self.get_type() == "https" and not self._tunnel_host:
      self._tunnel_host = self.get_host()
      saved_type = self.get_type()
    urllib.request.Request.set_proxy(self, host, type)

    if saved_type:
      # Don't set self.type, we want to preserve the
      # type for tunneling.
      self.type = saved_type

  def set_ssl_info(self, key_file=None, cert_file=None, ca_certs=None):
    self._key_file = key_file
    self._cert_file = cert_file
    self._ca_certs = ca_certs


class FancyProxyHandler(urllib.request.ProxyHandler):
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
      user_pass = "%s:%s" % (urllib.parse.unquote(user), urllib.parse.unquote(password))
      creds = base64.b64encode(user_pass).strip()
      # Later calls overwrite earlier calls for the same header
      req.add_header("Proxy-authorization", "Basic " + creds)
    hostport = urllib.parse.unquote(hostport)
    req.set_proxy(hostport, proxy_type)
    # This condition is the change
    if orig_type == "https":
      return None

    return urllib.request.ProxyHandler.proxy_open(self, req, proxy, type)


class FancyHTTPSHandler(urllib.request.HTTPSHandler):
  """An HTTPSHandler that works with CONNECT-enabled proxies."""

  def do_open(self, http_class, req, **kwargs):
    proxy_authorization = None
    for header in req.headers:
      if header.lower() == "proxy-authorization":
        proxy_authorization = req.headers[header]
        break

    # Intentionally very specific so as to opt for false negatives
    # rather than false positives.
    try:
      return urllib.request.HTTPSHandler.do_open(
          self,
          create_fancy_connection(req._tunnel_host,
                                  req._key_file,
                                  req._cert_file,
                                  req._ca_certs,
                                  proxy_authorization),
          req,
          **kwargs)
    except urllib.error.URLError as url_error:
      try:
        import ssl
        if (type(url_error.reason) == ssl.SSLError and
            url_error.reason.args[0] == 1):
          # Display the reason to the user. Need to use args for python2.5
          # compat.
          raise InvalidCertificateException(req.host, "",
                                            url_error.reason.args[1])
      except ImportError:
        pass

      raise url_error


# We have to implement this so that we persist the tunneling behavior
# through redirects.
class FancyRedirectHandler(urllib.request.HTTPRedirectHandler):
  """A redirect handler that persists CONNECT-enabled proxy information."""

  def redirect_request(self, req, *args, **kwargs):
    new_req = urllib.request.HTTPRedirectHandler.redirect_request(
        self, req, *args, **kwargs)
    # Same thing as in our set_proxy implementation, but in this case
    # we"ve only got a Request to work with, so it was this or copy
    # everything over piecemeal.
    #
    # Note that we do not persist tunneling behavior from an http request
    # to an https request, because an http request does not set _tunnel_host.
    #
    # Also note that in Python < 2.6, you will get an error in
    # FancyHTTPSHandler.do_open() on an https urllib2.Request that uses an http
    # proxy, since the proxy type will be set to http instead of https.
    # (FancyRequest, and urllib2.Request in Python >= 2.6 set the proxy type to
    # https.)  Such an urllib2.Request could result from this redirect
    # if you are redirecting from an http request (since an an http request
    # does not have _tunnel_host set, and thus you will not set the proxy
    # in the code below), and if you have defined a proxy for https in, say,
    # FancyProxyHandler, and that proxy has type http.
    if hasattr(req, "_tunnel_host") and isinstance(new_req, urllib.request.Request):
      if new_req.get_type() == "https":
        if req._tunnel_host:
          # req is proxied, so copy the proxy info.
          new_req._tunnel_host = new_req.get_host()
          new_req.set_proxy(req.host, "https")
        else:
          # req is not proxied, so just make sure _tunnel_host is defined.
          new_req._tunnel_host = None
        new_req.type = "https"
    if hasattr(req, "_key_file") and isinstance(new_req, urllib.request.Request):
      # Copy the auxiliary data in case this or any further redirect is https
      new_req._key_file = req._key_file
      new_req._cert_file = req._cert_file
      new_req._ca_certs = req._ca_certs

    return new_req
