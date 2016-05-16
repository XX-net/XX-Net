from __future__ import generators
"""
httplib2

A caching http interface that supports ETags and gzip
to conserve bandwidth.

Requires Python 2.3 or later

Changelog:
2007-08-18, Rick: Modified so it's able to use a socks proxy if needed.

"""

__author__ = "Joe Gregorio (joe@bitworking.org)"
__copyright__ = "Copyright 2006, Joe Gregorio"
__contributors__ = ["Thomas Broyer (t.broyer@ltgt.net)",
    "James Antill",
    "Xavier Verges Farrero",
    "Jonathan Feinberg",
    "Blair Zajac",
    "Sam Ruby",
    "Louis Nyffenegger"]
__license__ = "MIT"
__version__ = "0.7.5"

import re
import sys
import email
import email.Utils
import email.Message
import email.FeedParser
import StringIO
import gzip
import zlib
import httplib
import urlparse
import urllib
import base64
import os
import copy
import calendar
import time
import random
import errno
import logging
try:
    from hashlib import sha1 as _sha, md5 as _md5
except ImportError:
    # prior to Python 2.5, these were separate modules
    import sha
    import md5
    _sha = sha.new
    _md5 = md5.new
import hmac
from gettext import gettext as _
import socket

try:
    from httplib2 import socks
except ImportError:
    try:
        import socks
    except ImportError:
        socks = None

# Build the appropriate socket wrapper for ssl
try:
    import ssl # python 2.6
    ssl_SSLError = ssl.SSLError
    def _ssl_wrap_socket(sock, key_file, cert_file,
                         disable_validation, ca_certs):
        disable_validation = True
        # Force to disable validation
        if disable_validation:
            cert_reqs = ssl.CERT_NONE
            ca_certs = None
        else:
            cert_reqs = ssl.CERT_REQUIRED
        # We should be specifying SSL version 3 or TLS v1, but the ssl module
        # doesn't expose the necessary knobs. So we need to go with the default
        # of SSLv23.
        return ssl.wrap_socket(sock, keyfile=key_file, certfile=cert_file,
                               cert_reqs=cert_reqs, ca_certs=ca_certs)
except (AttributeError, ImportError):
    ssl_SSLError = None
    def _ssl_wrap_socket(sock, key_file, cert_file,
                         disable_validation, ca_certs):
        if not disable_validation:
            raise CertificateValidationUnsupported(
                    "SSL certificate validation is not supported without "
                    "the ssl module installed. To avoid this error, install "
                    "the ssl module, or explicity disable validation.")
        ssl_sock = socket.ssl(sock, key_file, cert_file)
        return httplib.FakeSocket(sock, ssl_sock)


if sys.version_info >= (2,3):
    from iri2uri import iri2uri
else:
    def iri2uri(uri):
        return uri

def has_timeout(timeout): # python 2.6
    if hasattr(socket, '_GLOBAL_DEFAULT_TIMEOUT'):
        return (timeout is not None and timeout is not socket._GLOBAL_DEFAULT_TIMEOUT)
    return (timeout is not None)

__all__ = ['Http', 'Response', 'ProxyInfo', 'HttpLib2Error',
  'RedirectMissingLocation', 'RedirectLimit', 'FailedToDecompressContent',
  'UnimplementedDigestAuthOptionError', 'UnimplementedHmacDigestAuthOptionError',
  'debuglevel', 'ProxiesUnavailableError']


# The httplib debug level, set to a non-zero value to get debug output
debuglevel = 0

# A request will be tried 'RETRIES' times if it fails at the socket/connection level.
RETRIES = 2

# Python 2.3 support
if sys.version_info < (2,4):
    def sorted(seq):
        seq.sort()
        return seq

# Python 2.3 support
def HTTPResponse__getheaders(self):
    """Return list of (header, value) tuples."""
    if self.msg is None:
        raise httplib.ResponseNotReady()
    return self.msg.items()

if not hasattr(httplib.HTTPResponse, 'getheaders'):
    httplib.HTTPResponse.getheaders = HTTPResponse__getheaders

# All exceptions raised here derive from HttpLib2Error
class HttpLib2Error(Exception): pass

# Some exceptions can be caught and optionally
# be turned back into responses.
class HttpLib2ErrorWithResponse(HttpLib2Error):
    def __init__(self, desc, response, content):
        self.response = response
        self.content = content
        HttpLib2Error.__init__(self, desc)

class RedirectMissingLocation(HttpLib2ErrorWithResponse): pass
class RedirectLimit(HttpLib2ErrorWithResponse): pass
class FailedToDecompressContent(HttpLib2ErrorWithResponse): pass
class UnimplementedDigestAuthOptionError(HttpLib2ErrorWithResponse): pass
class UnimplementedHmacDigestAuthOptionError(HttpLib2ErrorWithResponse): pass

class MalformedHeader(HttpLib2Error): pass
class RelativeURIError(HttpLib2Error): pass
class ServerNotFoundError(HttpLib2Error): pass
class ProxiesUnavailableError(HttpLib2Error): pass
class CertificateValidationUnsupported(HttpLib2Error): pass
class SSLHandshakeError(HttpLib2Error): pass
class NotSupportedOnThisPlatform(HttpLib2Error): pass
class CertificateHostnameMismatch(SSLHandshakeError):
  def __init__(self, desc, host, cert):
    HttpLib2Error.__init__(self, desc)
    self.host = host
    self.cert = cert

# Open Items:
# -----------
# Proxy support

# Are we removing the cached content too soon on PUT (only delete on 200 Maybe?)

# Pluggable cache storage (supports storing the cache in
#   flat files by default. We need a plug-in architecture
#   that can support Berkeley DB and Squid)

# == Known Issues ==
# Does not handle a resource that uses conneg and Last-Modified but no ETag as a cache validator.
# Does not handle Cache-Control: max-stale
# Does not use Age: headers when calculating cache freshness.


# The number of redirections to follow before giving up.
# Note that only GET redirects are automatically followed.
# Will also honor 301 requests by saving that info and never
# requesting that URI again.
DEFAULT_MAX_REDIRECTS = 5

# Default CA certificates file bundled with httplib2.
CA_CERTS = os.path.join(
        os.path.dirname(os.path.abspath(__file__ )), "cacerts.txt")

# Which headers are hop-by-hop headers by default
HOP_BY_HOP = ['connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade']

def _get_end2end_headers(response):
    hopbyhop = list(HOP_BY_HOP)
    hopbyhop.extend([x.strip() for x in response.get('connection', '').split(',')])
    return [header for header in response.keys() if header not in hopbyhop]

URI = re.compile(r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?")

def parse_uri(uri):
    """Parses a URI using the regex given in Appendix B of RFC 3986.

        (scheme, authority, path, query, fragment) = parse_uri(uri)
    """
    groups = URI.match(uri).groups()
    return (groups[1], groups[3], groups[4], groups[6], groups[8])

def urlnorm(uri):
    (scheme, authority, path, query, fragment) = parse_uri(uri)
    if not scheme or not authority:
        raise RelativeURIError("Only absolute URIs are allowed. uri = %s" % uri)
    authority = authority.lower()
    scheme = scheme.lower()
    if not path:
        path = "/"
    # Could do syntax based normalization of the URI before
    # computing the digest. See Section 6.2.2 of Std 66.
    request_uri = query and "?".join([path, query]) or path
    scheme = scheme.lower()
    defrag_uri = scheme + "://" + authority + request_uri
    return scheme, authority, request_uri, defrag_uri


# Cache filename construction (original borrowed from Venus http://intertwingly.net/code/venus/)
re_url_scheme    = re.compile(r'^\w+://')
re_slash         = re.compile(r'[?/:|]+')

def safename(filename):
    """Return a filename suitable for the cache.

    Strips dangerous and common characters to create a filename we
    can use to store the cache in.
    """

    try:
        if re_url_scheme.match(filename):
            if isinstance(filename,str):
                filename = filename.decode('utf-8')
                filename = filename.encode('idna')
            else:
                filename = filename.encode('idna')
    except UnicodeError:
        pass
    if isinstance(filename,unicode):
        filename=filename.encode('utf-8')
    filemd5 = _md5(filename).hexdigest()
    filename = re_url_scheme.sub("", filename)
    filename = re_slash.sub(",", filename)

    # limit length of filename
    if len(filename)>200:
        filename=filename[:200]
    return ",".join((filename, filemd5))

NORMALIZE_SPACE = re.compile(r'(?:\r\n)?[ \t]+')
def _normalize_headers(headers):
    return dict([ (key.lower(), NORMALIZE_SPACE.sub(value, ' ').strip())  for (key, value) in headers.iteritems()])

def _parse_cache_control(headers):
    retval = {}
    if headers.has_key('cache-control'):
        parts =  headers['cache-control'].split(',')
        parts_with_args = [tuple([x.strip().lower() for x in part.split("=", 1)]) for part in parts if -1 != part.find("=")]
        parts_wo_args = [(name.strip().lower(), 1) for name in parts if -1 == name.find("=")]
        retval = dict(parts_with_args + parts_wo_args)
    return retval

# Whether to use a strict mode to parse WWW-Authenticate headers
# Might lead to bad results in case of ill-formed header value,
# so disabled by default, falling back to relaxed parsing.
# Set to true to turn on, usefull for testing servers.
USE_WWW_AUTH_STRICT_PARSING = 0

# In regex below:
#    [^\0-\x1f\x7f-\xff()<>@,;:\\\"/[\]?={} \t]+             matches a "token" as defined by HTTP
#    "(?:[^\0-\x08\x0A-\x1f\x7f-\xff\\\"]|\\[\0-\x7f])*?"    matches a "quoted-string" as defined by HTTP, when LWS have already been replaced by a single space
# Actually, as an auth-param value can be either a token or a quoted-string, they are combined in a single pattern which matches both:
#    \"?((?<=\")(?:[^\0-\x1f\x7f-\xff\\\"]|\\[\0-\x7f])*?(?=\")|(?<!\")[^\0-\x08\x0A-\x1f\x7f-\xff()<>@,;:\\\"/[\]?={} \t]+(?!\"))\"?
WWW_AUTH_STRICT = re.compile(r"^(?:\s*(?:,\s*)?([^\0-\x1f\x7f-\xff()<>@,;:\\\"/[\]?={} \t]+)\s*=\s*\"?((?<=\")(?:[^\0-\x08\x0A-\x1f\x7f-\xff\\\"]|\\[\0-\x7f])*?(?=\")|(?<!\")[^\0-\x1f\x7f-\xff()<>@,;:\\\"/[\]?={} \t]+(?!\"))\"?)(.*)$")
WWW_AUTH_RELAXED = re.compile(r"^(?:\s*(?:,\s*)?([^ \t\r\n=]+)\s*=\s*\"?((?<=\")(?:[^\\\"]|\\.)*?(?=\")|(?<!\")[^ \t\r\n,]+(?!\"))\"?)(.*)$")
UNQUOTE_PAIRS = re.compile(r'\\(.)')
def _parse_www_authenticate(headers, headername='www-authenticate'):
    """Returns a dictionary of dictionaries, one dict
    per auth_scheme."""
    retval = {}
    if headers.has_key(headername):
        try:
          authenticate = headers[headername].strip()
          www_auth = USE_WWW_AUTH_STRICT_PARSING and WWW_AUTH_STRICT or WWW_AUTH_RELAXED
          while authenticate:
              # Break off the scheme at the beginning of the line
              if headername == 'authentication-info':
                  (auth_scheme, the_rest) = ('digest', authenticate)
              else:
                  (auth_scheme, the_rest) = authenticate.split(" ", 1)
              # Now loop over all the key value pairs that come after the scheme,
              # being careful not to roll into the next scheme
              match = www_auth.search(the_rest)
              auth_params = {}
              while match:
                  if match and len(match.groups()) == 3:
                      (key, value, the_rest) = match.groups()
                      auth_params[key.lower()] = UNQUOTE_PAIRS.sub(r'\1', value) # '\\'.join([x.replace('\\', '') for x in value.split('\\\\')])
                  match = www_auth.search(the_rest)
              retval[auth_scheme.lower()] = auth_params
              authenticate = the_rest.strip()
        except ValueError:
          raise MalformedHeader("WWW-Authenticate")
    return retval


def _entry_disposition(response_headers, request_headers):
    """Determine freshness from the Date, Expires and Cache-Control headers.

    We don't handle the following:

    1. Cache-Control: max-stale
    2. Age: headers are not used in the calculations.

    Not that this algorithm is simpler than you might think
    because we are operating as a private (non-shared) cache.
    This lets us ignore 's-maxage'. We can also ignore
    'proxy-invalidate' since we aren't a proxy.
    We will never return a stale document as
    fresh as a design decision, and thus the non-implementation
    of 'max-stale'. This also lets us safely ignore 'must-revalidate'
    since we operate as if every server has sent 'must-revalidate'.
    Since we are private we get to ignore both 'public' and
    'private' parameters. We also ignore 'no-transform' since
    we don't do any transformations.
    The 'no-store' parameter is handled at a higher level.
    So the only Cache-Control parameters we look at are:

    no-cache
    only-if-cached
    max-age
    min-fresh
    """

    retval = "STALE"
    cc = _parse_cache_control(request_headers)
    cc_response = _parse_cache_control(response_headers)

    if request_headers.has_key('pragma') and request_headers['pragma'].lower().find('no-cache') != -1:
        retval = "TRANSPARENT"
        if 'cache-control' not in request_headers:
            request_headers['cache-control'] = 'no-cache'
    elif cc.has_key('no-cache'):
        retval = "TRANSPARENT"
    elif cc_response.has_key('no-cache'):
        retval = "STALE"
    elif cc.has_key('only-if-cached'):
        retval = "FRESH"
    elif response_headers.has_key('date'):
        date = calendar.timegm(email.Utils.parsedate_tz(response_headers['date']))
        now = time.time()
        current_age = max(0, now - date)
        if cc_response.has_key('max-age'):
            try:
                freshness_lifetime = int(cc_response['max-age'])
            except ValueError:
                freshness_lifetime = 0
        elif response_headers.has_key('expires'):
            expires = email.Utils.parsedate_tz(response_headers['expires'])
            if None == expires:
                freshness_lifetime = 0
            else:
                freshness_lifetime = max(0, calendar.timegm(expires) - date)
        else:
            freshness_lifetime = 0
        if cc.has_key('max-age'):
            try:
                freshness_lifetime = int(cc['max-age'])
            except ValueError:
                freshness_lifetime = 0
        if cc.has_key('min-fresh'):
            try:
                min_fresh = int(cc['min-fresh'])
            except ValueError:
                min_fresh = 0
            current_age += min_fresh
        if freshness_lifetime > current_age:
            retval = "FRESH"
    return retval

def _decompressContent(response, new_content):
    content = new_content
    try:
        encoding = response.get('content-encoding', None)
        if encoding in ['gzip', 'deflate']:
            if encoding == 'gzip':
                content = gzip.GzipFile(fileobj=StringIO.StringIO(new_content)).read()
            if encoding == 'deflate':
                content = zlib.decompress(content)
            response['content-length'] = str(len(content))
            # Record the historical presence of the encoding in a way the won't interfere.
            response['-content-encoding'] = response['content-encoding']
            del response['content-encoding']
    except IOError:
        content = ""
        raise FailedToDecompressContent(_("Content purported to be compressed with %s but failed to decompress.") % response.get('content-encoding'), response, content)
    return content

def _updateCache(request_headers, response_headers, content, cache, cachekey):
    if cachekey:
        cc = _parse_cache_control(request_headers)
        cc_response = _parse_cache_control(response_headers)
        if cc.has_key('no-store') or cc_response.has_key('no-store'):
            cache.delete(cachekey)
        else:
            info = email.Message.Message()
            for key, value in response_headers.iteritems():
                if key not in ['status','content-encoding','transfer-encoding']:
                    info[key] = value

            # Add annotations to the cache to indicate what headers
            # are variant for this request.
            vary = response_headers.get('vary', None)
            if vary:
                vary_headers = vary.lower().replace(' ', '').split(',')
                for header in vary_headers:
                    key = '-varied-%s' % header
                    try:
                        info[key] = request_headers[header]
                    except KeyError:
                        pass

            status = response_headers.status
            if status == 304:
                status = 200

            status_header = 'status: %d\r\n' % status

            header_str = info.as_string()

            header_str = re.sub("\r(?!\n)|(?<!\r)\n", "\r\n", header_str)
            text = "".join([status_header, header_str, content])

            cache.set(cachekey, text)

def _cnonce():
    dig = _md5("%s:%s" % (time.ctime(), ["0123456789"[random.randrange(0, 9)] for i in range(20)])).hexdigest()
    return dig[:16]

def _wsse_username_token(cnonce, iso_now, password):
    return base64.b64encode(_sha("%s%s%s" % (cnonce, iso_now, password)).digest()).strip()


# For credentials we need two things, first
# a pool of credential to try (not necesarily tied to BAsic, Digest, etc.)
# Then we also need a list of URIs that have already demanded authentication
# That list is tricky since sub-URIs can take the same auth, or the
# auth scheme may change as you descend the tree.
# So we also need each Auth instance to be able to tell us
# how close to the 'top' it is.

class Authentication(object):
    def __init__(self, credentials, host, request_uri, headers, response, content, http):
        (scheme, authority, path, query, fragment) = parse_uri(request_uri)
        self.path = path
        self.host = host
        self.credentials = credentials
        self.http = http

    def depth(self, request_uri):
        (scheme, authority, path, query, fragment) = parse_uri(request_uri)
        return request_uri[len(self.path):].count("/")

    def inscope(self, host, request_uri):
        # XXX Should we normalize the request_uri?
        (scheme, authority, path, query, fragment) = parse_uri(request_uri)
        return (host == self.host) and path.startswith(self.path)

    def request(self, method, request_uri, headers, content):
        """Modify the request headers to add the appropriate
        Authorization header. Over-ride this in sub-classes."""
        pass

    def response(self, response, content):
        """Gives us a chance to update with new nonces
        or such returned from the last authorized response.
        Over-rise this in sub-classes if necessary.

        Return TRUE is the request is to be retried, for
        example Digest may return stale=true.
        """
        return False



class BasicAuthentication(Authentication):
    def __init__(self, credentials, host, request_uri, headers, response, content, http):
        Authentication.__init__(self, credentials, host, request_uri, headers, response, content, http)

    def request(self, method, request_uri, headers, content):
        """Modify the request headers to add the appropriate
        Authorization header."""
        headers['authorization'] = 'Basic ' + base64.b64encode("%s:%s" % self.credentials).strip()


class DigestAuthentication(Authentication):
    """Only do qop='auth' and MD5, since that
    is all Apache currently implements"""
    def __init__(self, credentials, host, request_uri, headers, response, content, http):
        Authentication.__init__(self, credentials, host, request_uri, headers, response, content, http)
        challenge = _parse_www_authenticate(response, 'www-authenticate')
        self.challenge = challenge['digest']
        qop = self.challenge.get('qop', 'auth')
        self.challenge['qop'] = ('auth' in [x.strip() for x in qop.split()]) and 'auth' or None
        if self.challenge['qop'] is None:
            raise UnimplementedDigestAuthOptionError( _("Unsupported value for qop: %s." % qop))
        self.challenge['algorithm'] = self.challenge.get('algorithm', 'MD5').upper()
        if self.challenge['algorithm'] != 'MD5':
            raise UnimplementedDigestAuthOptionError( _("Unsupported value for algorithm: %s." % self.challenge['algorithm']))
        self.A1 = "".join([self.credentials[0], ":", self.challenge['realm'], ":", self.credentials[1]])
        self.challenge['nc'] = 1

    def request(self, method, request_uri, headers, content, cnonce = None):
        """Modify the request headers"""
        H = lambda x: _md5(x).hexdigest()
        KD = lambda s, d: H("%s:%s" % (s, d))
        A2 = "".join([method, ":", request_uri])
        self.challenge['cnonce'] = cnonce or _cnonce()
        request_digest  = '"%s"' % KD(H(self.A1), "%s:%s:%s:%s:%s" % (self.challenge['nonce'],
                    '%08x' % self.challenge['nc'],
                    self.challenge['cnonce'],
                    self.challenge['qop'], H(A2)
                    ))
        headers['authorization'] = 'Digest username="%s", realm="%s", nonce="%s", uri="%s", algorithm=%s, response=%s, qop=%s, nc=%08x, cnonce="%s"' % (
                self.credentials[0],
                self.challenge['realm'],
                self.challenge['nonce'],
                request_uri,
                self.challenge['algorithm'],
                request_digest,
                self.challenge['qop'],
                self.challenge['nc'],
                self.challenge['cnonce'],
                )
        if self.challenge.get('opaque'):
            headers['authorization'] += ', opaque="%s"' % self.challenge['opaque']
        self.challenge['nc'] += 1

    def response(self, response, content):
        if not response.has_key('authentication-info'):
            challenge = _parse_www_authenticate(response, 'www-authenticate').get('digest', {})
            if 'true' == challenge.get('stale'):
                self.challenge['nonce'] = challenge['nonce']
                self.challenge['nc'] = 1
                return True
        else:
            updated_challenge = _parse_www_authenticate(response, 'authentication-info').get('digest', {})

            if updated_challenge.has_key('nextnonce'):
                self.challenge['nonce'] = updated_challenge['nextnonce']
                self.challenge['nc'] = 1
        return False


class HmacDigestAuthentication(Authentication):
    """Adapted from Robert Sayre's code and DigestAuthentication above."""
    __author__ = "Thomas Broyer (t.broyer@ltgt.net)"

    def __init__(self, credentials, host, request_uri, headers, response, content, http):
        Authentication.__init__(self, credentials, host, request_uri, headers, response, content, http)
        challenge = _parse_www_authenticate(response, 'www-authenticate')
        self.challenge = challenge['hmacdigest']
        # TODO: self.challenge['domain']
        self.challenge['reason'] = self.challenge.get('reason', 'unauthorized')
        if self.challenge['reason'] not in ['unauthorized', 'integrity']:
            self.challenge['reason'] = 'unauthorized'
        self.challenge['salt'] = self.challenge.get('salt', '')
        if not self.challenge.get('snonce'):
            raise UnimplementedHmacDigestAuthOptionError( _("The challenge doesn't contain a server nonce, or this one is empty."))
        self.challenge['algorithm'] = self.challenge.get('algorithm', 'HMAC-SHA-1')
        if self.challenge['algorithm'] not in ['HMAC-SHA-1', 'HMAC-MD5']:
            raise UnimplementedHmacDigestAuthOptionError( _("Unsupported value for algorithm: %s." % self.challenge['algorithm']))
        self.challenge['pw-algorithm'] = self.challenge.get('pw-algorithm', 'SHA-1')
        if self.challenge['pw-algorithm'] not in ['SHA-1', 'MD5']:
            raise UnimplementedHmacDigestAuthOptionError( _("Unsupported value for pw-algorithm: %s." % self.challenge['pw-algorithm']))
        if self.challenge['algorithm'] == 'HMAC-MD5':
            self.hashmod = _md5
        else:
            self.hashmod = _sha
        if self.challenge['pw-algorithm'] == 'MD5':
            self.pwhashmod = _md5
        else:
            self.pwhashmod = _sha
        self.key = "".join([self.credentials[0], ":",
                    self.pwhashmod.new("".join([self.credentials[1], self.challenge['salt']])).hexdigest().lower(),
                    ":", self.challenge['realm']
                    ])
        self.key = self.pwhashmod.new(self.key).hexdigest().lower()

    def request(self, method, request_uri, headers, content):
        """Modify the request headers"""
        keys = _get_end2end_headers(headers)
        keylist = "".join(["%s " % k for k in keys])
        headers_val = "".join([headers[k] for k in keys])
        created = time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        cnonce = _cnonce()
        request_digest = "%s:%s:%s:%s:%s" % (method, request_uri, cnonce, self.challenge['snonce'], headers_val)
        request_digest  = hmac.new(self.key, request_digest, self.hashmod).hexdigest().lower()
        headers['authorization'] = 'HMACDigest username="%s", realm="%s", snonce="%s", cnonce="%s", uri="%s", created="%s", response="%s", headers="%s"' % (
                self.credentials[0],
                self.challenge['realm'],
                self.challenge['snonce'],
                cnonce,
                request_uri,
                created,
                request_digest,
                keylist,
                )

    def response(self, response, content):
        challenge = _parse_www_authenticate(response, 'www-authenticate').get('hmacdigest', {})
        if challenge.get('reason') in ['integrity', 'stale']:
            return True
        return False


class WsseAuthentication(Authentication):
    """This is thinly tested and should not be relied upon.
    At this time there isn't any third party server to test against.
    Blogger and TypePad implemented this algorithm at one point
    but Blogger has since switched to Basic over HTTPS and
    TypePad has implemented it wrong, by never issuing a 401
    challenge but instead requiring your client to telepathically know that
    their endpoint is expecting WSSE profile="UsernameToken"."""
    def __init__(self, credentials, host, request_uri, headers, response, content, http):
        Authentication.__init__(self, credentials, host, request_uri, headers, response, content, http)

    def request(self, method, request_uri, headers, content):
        """Modify the request headers to add the appropriate
        Authorization header."""
        headers['authorization'] = 'WSSE profile="UsernameToken"'
        iso_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        cnonce = _cnonce()
        password_digest = _wsse_username_token(cnonce, iso_now, self.credentials[1])
        headers['X-WSSE'] = 'UsernameToken Username="%s", PasswordDigest="%s", Nonce="%s", Created="%s"' % (
                self.credentials[0],
                password_digest,
                cnonce,
                iso_now)

class GoogleLoginAuthentication(Authentication):
    def __init__(self, credentials, host, request_uri, headers, response, content, http):
        from urllib import urlencode
        Authentication.__init__(self, credentials, host, request_uri, headers, response, content, http)
        challenge = _parse_www_authenticate(response, 'www-authenticate')
        service = challenge['googlelogin'].get('service', 'xapi')
        # Bloggger actually returns the service in the challenge
        # For the rest we guess based on the URI
        if service == 'xapi' and  request_uri.find("calendar") > 0:
            service = "cl"
        # No point in guessing Base or Spreadsheet
        #elif request_uri.find("spreadsheets") > 0:
        #    service = "wise"

        auth = dict(Email=credentials[0], Passwd=credentials[1], service=service, source=headers['user-agent'])
        resp, content = self.http.request("https://www.google.com/accounts/ClientLogin", method="POST", body=urlencode(auth), headers={'Content-Type': 'application/x-www-form-urlencoded'})
        lines = content.split('\n')
        d = dict([tuple(line.split("=", 1)) for line in lines if line])
        if resp.status == 403:
            self.Auth = ""
        else:
            self.Auth = d['Auth']

    def request(self, method, request_uri, headers, content):
        """Modify the request headers to add the appropriate
        Authorization header."""
        headers['authorization'] = 'GoogleLogin Auth=' + self.Auth


AUTH_SCHEME_CLASSES = {
    "basic": BasicAuthentication,
    "wsse": WsseAuthentication,
    "digest": DigestAuthentication,
    "hmacdigest": HmacDigestAuthentication,
    "googlelogin": GoogleLoginAuthentication
}

AUTH_SCHEME_ORDER = ["hmacdigest", "googlelogin", "digest", "wsse", "basic"]

class FileCache(object):
    """Uses a local directory as a store for cached files.
    Not really safe to use if multiple threads or processes are going to
    be running on the same cache.
    """
    def __init__(self, cache, safe=safename): # use safe=lambda x: md5.new(x).hexdigest() for the old behavior
        self.cache = cache
        self.safe = safe
        if not os.path.exists(cache):
            os.makedirs(self.cache)

    def get(self, key):
        retval = None
        cacheFullPath = os.path.join(self.cache, self.safe(key))
        try:
            f = file(cacheFullPath, "rb")
            retval = f.read()
            f.close()
        except IOError:
            pass
        return retval

    def set(self, key, value):
        cacheFullPath = os.path.join(self.cache, self.safe(key))
        f = file(cacheFullPath, "wb")
        f.write(value)
        f.close()

    def delete(self, key):
        cacheFullPath = os.path.join(self.cache, self.safe(key))
        if os.path.exists(cacheFullPath):
            os.remove(cacheFullPath)

class Credentials(object):
    def __init__(self):
        self.credentials = []

    def add(self, name, password, domain=""):
        self.credentials.append((domain.lower(), name, password))

    def clear(self):
        self.credentials = []

    def iter(self, domain):
        for (cdomain, name, password) in self.credentials:
            if cdomain == "" or domain == cdomain:
                yield (name, password)

class KeyCerts(Credentials):
    """Identical to Credentials except that
    name/password are mapped to key/cert."""
    pass

class AllHosts(object):
  pass

class ProxyInfo(object):
    """Collect information required to use a proxy."""
    bypass_hosts = ()

    def __init__(self, proxy_type, proxy_host, proxy_port,
        proxy_rdns=True, proxy_user=None, proxy_pass=None):
        """The parameter proxy_type must be set to one of socks.PROXY_TYPE_XXX
        constants. For example:

        p = ProxyInfo(proxy_type=socks.PROXY_TYPE_HTTP,
            proxy_host='localhost', proxy_port=8000)
        """
        self.proxy_type = proxy_type
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_rdns = proxy_rdns
        self.proxy_user = proxy_user
        self.proxy_pass = proxy_pass

    def astuple(self):
        return (self.proxy_type, self.proxy_host, self.proxy_port,
            self.proxy_rdns, self.proxy_user, self.proxy_pass)

    def isgood(self):
        return (self.proxy_host != None) and (self.proxy_port != None)

    @classmethod
    def from_environment(cls, method='http'):
        """
        Read proxy info from the environment variables.
        """
        if method not in ['http', 'https']:
          return

        env_var = method + '_proxy'
        url = os.environ.get(env_var, os.environ.get(env_var.upper()))
        if not url:
          return
        pi = cls.from_url(url, method)

        no_proxy = os.environ.get('no_proxy', os.environ.get('NO_PROXY', ''))
        bypass_hosts = []
        if no_proxy:
          bypass_hosts = no_proxy.split(',')
        # special case, no_proxy=* means all hosts bypassed
        if no_proxy == '*':
          bypass_hosts = AllHosts

        pi.bypass_hosts = bypass_hosts
        return pi

    @classmethod
    def from_url(cls, url, method='http'):
        """
        Construct a ProxyInfo from a URL (such as http_proxy env var)
        """
        url = urlparse.urlparse(url)
        username = None
        password = None
        port = None
        if '@' in url[1]:
          ident, host_port = url[1].split('@', 1)
          if ':' in ident:
            username, password = ident.split(':', 1)
          else:
            password = ident
        else:
          host_port = url[1]
        if ':' in host_port:
          host, port = host_port.split(':', 1)
        else:
          host = host_port

        if port:
            port = int(port)
        else:
            port = dict(https=443, http=80)[method]

        proxy_type = 3 # socks.PROXY_TYPE_HTTP
        return cls(
            proxy_type = proxy_type,
            proxy_host = host,
            proxy_port = port,
            proxy_user = username or None,
            proxy_pass = password or None,
        )

    def applies_to(self, hostname):
        return not self.bypass_host(hostname)

    def bypass_host(self, hostname):
        """Has this host been excluded from the proxy config"""
        if self.bypass_hosts is AllHosts:
          return True

        bypass = False
        for domain in self.bypass_hosts:
          if hostname.endswith(domain):
            bypass = True

        return bypass


class HTTPConnectionWithTimeout(httplib.HTTPConnection):
    """
    HTTPConnection subclass that supports timeouts

    All timeouts are in seconds. If None is passed for timeout then
    Python's default timeout for sockets will be used. See for example
    the docs of socket.setdefaulttimeout():
    http://docs.python.org/library/socket.html#socket.setdefaulttimeout
    """

    def __init__(self, host, port=None, strict=None, timeout=None, proxy_info=None):
        httplib.HTTPConnection.__init__(self, host, port, strict)
        self.timeout = timeout
        self.proxy_info = proxy_info

    def connect(self):
        """Connect to the host and port specified in __init__."""
        # Mostly verbatim from httplib.py.
        if self.proxy_info and socks is None:
            raise ProxiesUnavailableError(
                'Proxy support missing but proxy use was requested!')
        msg = "getaddrinfo returns an empty list"
        if self.proxy_info and self.proxy_info.isgood():
            use_proxy = True
            proxy_type, proxy_host, proxy_port, proxy_rdns, proxy_user, proxy_pass = self.proxy_info.astuple()
        else:
            use_proxy = False
        if use_proxy and proxy_rdns:
            host = proxy_host
            port = proxy_port
        else:
            host = self.host
            port = self.port

        for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                if use_proxy:
                    self.sock = socks.socksocket(af, socktype, proto)
                    self.sock.setproxy(proxy_type, proxy_host, proxy_port, proxy_rdns, proxy_user, proxy_pass)
                else:
                    self.sock = socket.socket(af, socktype, proto)
                    self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                # Different from httplib: support timeouts.
                if has_timeout(self.timeout):
                    self.sock.settimeout(self.timeout)
                    # End of difference from httplib.
                if self.debuglevel > 0:
                    print "connect: (%s, %s) ************" % (self.host, self.port)
                    if use_proxy:
                        print "proxy: %s ************" % str((proxy_host, proxy_port, proxy_rdns, proxy_user, proxy_pass))

                self.sock.connect((self.host, self.port) + sa[2:])
            except socket.error, msg:
                if self.debuglevel > 0:
                    print "connect fail: (%s, %s)" % (self.host, self.port)
                    if use_proxy:
                        print "proxy: %s" % str((proxy_host, proxy_port, proxy_rdns, proxy_user, proxy_pass))
                if self.sock:
                    self.sock.close()
                self.sock = None
                continue
            break
        if not self.sock:
            raise socket.error, msg

class HTTPSConnectionWithTimeout(httplib.HTTPSConnection):
    """
    This class allows communication via SSL.

    All timeouts are in seconds. If None is passed for timeout then
    Python's default timeout for sockets will be used. See for example
    the docs of socket.setdefaulttimeout():
    http://docs.python.org/library/socket.html#socket.setdefaulttimeout
    """
    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 strict=None, timeout=None, proxy_info=None,
                 ca_certs=None, disable_ssl_certificate_validation=True):
        httplib.HTTPSConnection.__init__(self, host, port=port, key_file=key_file,
                cert_file=cert_file, strict=strict)
        self.timeout = timeout
        self.proxy_info = proxy_info
        if ca_certs is None:
          ca_certs = CA_CERTS
        self.ca_certs = ca_certs
        self.disable_ssl_certificate_validation = \
                disable_ssl_certificate_validation

        if not self.disable_ssl_certificate_validation:
            print("err")
            self.disable_ssl_certificate_validation = True

    # The following two methods were adapted from https_wrapper.py, released
    # with the Google Appengine SDK at
    # http://googleappengine.googlecode.com/svn-history/r136/trunk/python/google/appengine/tools/https_wrapper.py
    # under the following license:
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

    def _GetValidHostsForCert(self, cert):
        """Returns a list of valid host globs for an SSL certificate.

        Args:
          cert: A dictionary representing an SSL certificate.
        Returns:
          list: A list of valid host globs.
        """
        if 'subjectAltName' in cert:
            return [x[1] for x in cert['subjectAltName']
                    if x[0].lower() == 'dns']
        else:
            return [x[0][1] for x in cert['subject']
                    if x[0][0].lower() == 'commonname']

    def _ValidateCertificateHostname(self, cert, hostname):
        """Validates that a given hostname is valid for an SSL certificate.

        Args:
          cert: A dictionary representing an SSL certificate.
          hostname: The hostname to test.
        Returns:
          bool: Whether or not the hostname is valid for this certificate.
        """
        hosts = self._GetValidHostsForCert(cert)
        for host in hosts:
            host_re = host.replace('.', '\.').replace('*', '[^.]*')
            if re.search('^%s$' % (host_re,), hostname, re.I):
                return True
        return False

    def connect(self):
        "Connect to a host on a given (SSL) port."

        msg = "getaddrinfo returns an empty list"
        if self.proxy_info and self.proxy_info.isgood():
            use_proxy = True
            proxy_type, proxy_host, proxy_port, proxy_rdns, proxy_user, proxy_pass = self.proxy_info.astuple()
        else:
            use_proxy = False
        if use_proxy:
            host = proxy_host
            port = proxy_port
        else:
            host = self.host
            port = self.port

        for family, socktype, proto, canonname, sockaddr in socket.getaddrinfo(
            host, port, 0, socket.SOCK_STREAM):
            try:
                if use_proxy:
                    sock = socks.socksocket(family, socktype, proto)

                    sock.setproxy(proxy_type, proxy_host, proxy_port, proxy_rdns, proxy_user, proxy_pass)
                else:
                    sock = socket.socket(family, socktype, proto)
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                if has_timeout(self.timeout):
                    sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))
                self.sock =_ssl_wrap_socket(
                    sock, self.key_file, self.cert_file,
                    self.disable_ssl_certificate_validation, self.ca_certs)
                if self.debuglevel > 0:
                    print "connect: (%s, %s)" % (self.host, self.port)
                    if use_proxy:
                        print "proxy: %s" % str((proxy_host, proxy_port, proxy_rdns, proxy_user, proxy_pass))
                if not self.disable_ssl_certificate_validation:
                    cert = self.sock.getpeercert()
                    hostname = self.host.split(':', 0)[0]
                    if not self._ValidateCertificateHostname(cert, hostname):
                        raise CertificateHostnameMismatch(
                            'Server presented certificate that does not match '
                            'host %s: %s' % (hostname, cert), hostname, cert)
            except ssl_SSLError as e:
                logging.exception("connect error:%r", e)
                if sock:
                    sock.close()
                if self.sock:
                    self.sock.close()
                self.sock = None
                # Unfortunately the ssl module doesn't seem to provide any way
                # to get at more detailed error information, in particular
                # whether the error is due to certificate validation or
                # something else (such as SSL protocol mismatch).
                if e.errno == ssl.SSL_ERROR_SSL:
                    raise SSLHandshakeError(e)
                else:
                    raise
            except (socket.timeout, socket.gaierror):
              raise
            except socket.error, msg:
              if self.debuglevel > 0:
                  print "connect fail: (%s, %s)" % (self.host, self.port)
                  if use_proxy:
                      print "proxy: %s" % str((proxy_host, proxy_port, proxy_rdns, proxy_user, proxy_pass))
              if self.sock:
                  self.sock.close()
              self.sock = None
              continue
            break
        if not self.sock:
          raise socket.error, msg

SCHEME_TO_CONNECTION = {
    'http': HTTPConnectionWithTimeout,
    'https': HTTPSConnectionWithTimeout
    }

# Use a different connection object for Google App Engine
try:
  from google.appengine.api import apiproxy_stub_map
  if apiproxy_stub_map.apiproxy.GetStub('urlfetch') is None:
    raise ImportError  # Bail out; we're not actually running on App Engine.
  from google.appengine.api.urlfetch import fetch
  from google.appengine.api.urlfetch import InvalidURLError
  from google.appengine.api.urlfetch import DownloadError
  from google.appengine.api.urlfetch import ResponseTooLargeError
  from google.appengine.api.urlfetch import SSLCertificateError


  class ResponseDict(dict):
    """Is a dictionary that also has a read() method, so
    that it can pass itself off as an httlib.HTTPResponse()."""
    def read(self):
      pass


  class AppEngineHttpConnection(object):
    """Emulates an httplib.HTTPConnection object, but actually uses the Google
    App Engine urlfetch library. This allows the timeout to be properly used on
    Google App Engine, and avoids using httplib, which on Google App Engine is
    just another wrapper around urlfetch.
    """
    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 strict=None, timeout=None, proxy_info=None, ca_certs=None,
                 disable_ssl_certificate_validation=False):
      self.host = host
      self.port = port
      self.timeout = timeout
      if key_file or cert_file or proxy_info or ca_certs:
        raise NotSupportedOnThisPlatform()
      self.response = None
      self.scheme = 'http'
      self.validate_certificate = not disable_ssl_certificate_validation
      self.sock = True

    def request(self, method, url, body, headers):
      # Calculate the absolute URI, which fetch requires
      netloc = self.host
      if self.port:
        netloc = '%s:%s' % (self.host, self.port)
      absolute_uri = '%s://%s%s' % (self.scheme, netloc, url)
      try:
        response = fetch(absolute_uri, payload=body, method=method,
            headers=headers, allow_truncated=False, follow_redirects=False,
            deadline=self.timeout,
            validate_certificate=self.validate_certificate)
        self.response = ResponseDict(response.headers)
        self.response['status'] = str(response.status_code)
        self.response['reason'] = httplib.responses.get(response.status_code, 'Ok')
        self.response.status = response.status_code
        setattr(self.response, 'read', lambda : response.content)

      # Make sure the exceptions raised match the exceptions expected.
      except InvalidURLError:
        raise socket.gaierror('')
      except (DownloadError, ResponseTooLargeError, SSLCertificateError):
        raise httplib.HTTPException()

    def getresponse(self):
      if self.response:
        return self.response
      else:
        raise httplib.HTTPException()

    def set_debuglevel(self, level):
      pass

    def connect(self):
      pass

    def close(self):
      pass


  class AppEngineHttpsConnection(AppEngineHttpConnection):
    """Same as AppEngineHttpConnection, but for HTTPS URIs."""
    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 strict=None, timeout=None, proxy_info=None, ca_certs=None,
                 disable_ssl_certificate_validation=False):
      AppEngineHttpConnection.__init__(self, host, port, key_file, cert_file,
          strict, timeout, proxy_info, ca_certs, disable_ssl_certificate_validation)
      self.scheme = 'https'

  # Update the connection classes to use the Googel App Engine specific ones.
  SCHEME_TO_CONNECTION = {
      'http': AppEngineHttpConnection,
      'https': AppEngineHttpsConnection
      }

except ImportError:
  pass


class Http(object):
    """An HTTP client that handles:
- all methods
- caching
- ETags
- compression,
- HTTPS
- Basic
- Digest
- WSSE

and more.
    """
    def __init__(self, cache=None, timeout=None,
                 proxy_info=ProxyInfo.from_environment,
                 ca_certs=None, disable_ssl_certificate_validation=False):
        """If 'cache' is a string then it is used as a directory name for
        a disk cache. Otherwise it must be an object that supports the
        same interface as FileCache.

        All timeouts are in seconds. If None is passed for timeout
        then Python's default timeout for sockets will be used. See
        for example the docs of socket.setdefaulttimeout():
        http://docs.python.org/library/socket.html#socket.setdefaulttimeout

        `proxy_info` may be:
          - a callable that takes the http scheme ('http' or 'https') and
            returns a ProxyInfo instance per request. By default, uses
            ProxyInfo.from_environment.
          - a ProxyInfo instance (static proxy config).
          - None (proxy disabled).

        ca_certs is the path of a file containing root CA certificates for SSL
        server certificate validation.  By default, a CA cert file bundled with
        httplib2 is used.

        If disable_ssl_certificate_validation is true, SSL cert validation will
        not be performed.
        """
        self.proxy_info = proxy_info
        self.ca_certs = ca_certs
        self.disable_ssl_certificate_validation = \
                disable_ssl_certificate_validation

        # Map domain name to an httplib connection
        self.connections = {}
        # The location of the cache, for now a directory
        # where cached responses are held.
        if cache and isinstance(cache, basestring):
            self.cache = FileCache(cache)
        else:
            self.cache = cache

        # Name/password
        self.credentials = Credentials()

        # Key/cert
        self.certificates = KeyCerts()

        # authorization objects
        self.authorizations = []

        # If set to False then no redirects are followed, even safe ones.
        self.follow_redirects = True

        # Which HTTP methods do we apply optimistic concurrency to, i.e.
        # which methods get an "if-match:" etag header added to them.
        self.optimistic_concurrency_methods = ["PUT", "PATCH"]

        # If 'follow_redirects' is True, and this is set to True then
        # all redirecs are followed, including unsafe ones.
        self.follow_all_redirects = False

        self.ignore_etag = False

        self.force_exception_to_status_code = False

        self.timeout = timeout

        # Keep Authorization: headers on a redirect.
        self.forward_authorization_headers = False

    def _auth_from_challenge(self, host, request_uri, headers, response, content):
        """A generator that creates Authorization objects
           that can be applied to requests.
        """
        challenges = _parse_www_authenticate(response, 'www-authenticate')
        for cred in self.credentials.iter(host):
            for scheme in AUTH_SCHEME_ORDER:
                if challenges.has_key(scheme):
                    yield AUTH_SCHEME_CLASSES[scheme](cred, host, request_uri, headers, response, content, self)

    def add_credentials(self, name, password, domain=""):
        """Add a name and password that will be used
        any time a request requires authentication."""
        self.credentials.add(name, password, domain)

    def add_certificate(self, key, cert, domain):
        """Add a key and cert that will be used
        any time a request requires authentication."""
        self.certificates.add(key, cert, domain)

    def clear_credentials(self):
        """Remove all the names and passwords
        that are used for authentication"""
        self.credentials.clear()
        self.authorizations = []

    def _conn_request(self, conn, request_uri, method, body, headers):
        for i in range(RETRIES):
            try:
                if conn.sock is None:
                  conn.connect()
                conn.request(method, request_uri, body, headers)
            except socket.timeout:
                raise
            except socket.gaierror:
                conn.close()
                raise ServerNotFoundError("Unable to find the server at %s" % conn.host)
            except ssl_SSLError:
                conn.close()
                raise
            except socket.error, e:
                err = 0
                if hasattr(e, 'args'):
                    err = getattr(e, 'args')[0]
                else:
                    err = e.errno
                if err == errno.ECONNREFUSED: # Connection refused
                    raise
            except httplib.HTTPException:
                # Just because the server closed the connection doesn't apparently mean
                # that the server didn't send a response.
                if conn.sock is None:
                    if i < RETRIES-1:
                        conn.close()
                        conn.connect()
                        continue
                    else:
                        conn.close()
                        raise
                if i < RETRIES-1:
                    conn.close()
                    conn.connect()
                    continue
            try:
                response = conn.getresponse()
            except (socket.error, httplib.HTTPException):
                if i < RETRIES-1:
                    conn.close()
                    conn.connect()
                    continue
                else:
                    raise
            else:
                content = ""
                if method == "HEAD":
                    conn.close()
                else:
                    content = response.read()
                response = Response(response)
                if method != "HEAD":
                    content = _decompressContent(response, content)
            break
        return (response, content)


    def _request(self, conn, host, absolute_uri, request_uri, method, body, headers, redirections, cachekey):
        """Do the actual request using the connection object
        and also follow one level of redirects if necessary"""

        auths = [(auth.depth(request_uri), auth) for auth in self.authorizations if auth.inscope(host, request_uri)]
        auth = auths and sorted(auths)[0][1] or None
        if auth:
            auth.request(method, request_uri, headers, body)

        (response, content) = self._conn_request(conn, request_uri, method, body, headers)

        if auth:
            if auth.response(response, body):
                auth.request(method, request_uri, headers, body)
                (response, content) = self._conn_request(conn, request_uri, method, body, headers )
                response._stale_digest = 1

        if response.status == 401:
            for authorization in self._auth_from_challenge(host, request_uri, headers, response, content):
                authorization.request(method, request_uri, headers, body)
                (response, content) = self._conn_request(conn, request_uri, method, body, headers, )
                if response.status != 401:
                    self.authorizations.append(authorization)
                    authorization.response(response, body)
                    break

        if (self.follow_all_redirects or (method in ["GET", "HEAD"]) or response.status == 303):
            if self.follow_redirects and response.status in [300, 301, 302, 303, 307]:
                # Pick out the location header and basically start from the beginning
                # remembering first to strip the ETag header and decrement our 'depth'
                if redirections:
                    if not response.has_key('location') and response.status != 300:
                        raise RedirectMissingLocation( _("Redirected but the response is missing a Location: header."), response, content)
                    # Fix-up relative redirects (which violate an RFC 2616 MUST)
                    if response.has_key('location'):
                        location = response['location']
                        (scheme, authority, path, query, fragment) = parse_uri(location)
                        if authority == None:
                            response['location'] = urlparse.urljoin(absolute_uri, location)
                    if response.status == 301 and method in ["GET", "HEAD"]:
                        response['-x-permanent-redirect-url'] = response['location']
                        if not response.has_key('content-location'):
                            response['content-location'] = absolute_uri
                        _updateCache(headers, response, content, self.cache, cachekey)
                    if headers.has_key('if-none-match'):
                        del headers['if-none-match']
                    if headers.has_key('if-modified-since'):
                        del headers['if-modified-since']
                    if 'authorization' in headers and not self.forward_authorization_headers:
                        del headers['authorization']
                    if response.has_key('location'):
                        location = response['location']
                        old_response = copy.deepcopy(response)
                        if not old_response.has_key('content-location'):
                            old_response['content-location'] = absolute_uri
                        redirect_method = method
                        if response.status in [302, 303]:
                            redirect_method = "GET"
                            body = None
                        (response, content) = self.request(location, redirect_method, body=body, headers = headers, redirections = redirections - 1)
                        response.previous = old_response
                else:
                    raise RedirectLimit("Redirected more times than rediection_limit allows.", response, content)
            elif response.status in [200, 203] and method in ["GET", "HEAD"]:
                # Don't cache 206's since we aren't going to handle byte range requests
                if not response.has_key('content-location'):
                    response['content-location'] = absolute_uri
                _updateCache(headers, response, content, self.cache, cachekey)

        return (response, content)

    def _normalize_headers(self, headers):
        return _normalize_headers(headers)

# Need to catch and rebrand some exceptions
# Then need to optionally turn all exceptions into status codes
# including all socket.* and httplib.* exceptions.


    def request(self, uri, method="GET", body=None, headers=None, redirections=DEFAULT_MAX_REDIRECTS, connection_type=None):
        """ Performs a single HTTP request.
The 'uri' is the URI of the HTTP resource and can begin
with either 'http' or 'https'. The value of 'uri' must be an absolute URI.

The 'method' is the HTTP method to perform, such as GET, POST, DELETE, etc.
There is no restriction on the methods allowed.

The 'body' is the entity body to be sent with the request. It is a string
object.

Any extra headers that are to be sent with the request should be provided in the
'headers' dictionary.

The maximum number of redirect to follow before raising an
exception is 'redirections. The default is 5.

The return value is a tuple of (response, content), the first
being and instance of the 'Response' class, the second being
a string that contains the response entity body.
        """
        try:
            if headers is None:
                headers = {}
            else:
                headers = self._normalize_headers(headers)

            if not headers.has_key('user-agent'):
                headers['user-agent'] = "Python-httplib2/%s (gzip)" % __version__

            uri = iri2uri(uri)

            (scheme, authority, request_uri, defrag_uri) = urlnorm(uri)
            domain_port = authority.split(":")[0:2]
            if len(domain_port) == 2 and domain_port[1] == '443' and scheme == 'http':
                scheme = 'https'
                authority = domain_port[0]

            proxy_info = self._get_proxy_info(scheme, authority)

            conn_key = scheme+":"+authority
            if conn_key in self.connections:
                conn = self.connections[conn_key]
            else:
                if not connection_type:
                  connection_type = SCHEME_TO_CONNECTION[scheme]
                certs = list(self.certificates.iter(authority))
                if scheme == 'https':
                    if certs:
                        conn = self.connections[conn_key] = connection_type(
                                authority, key_file=certs[0][0],
                                cert_file=certs[0][1], timeout=self.timeout,
                                proxy_info=proxy_info,
                                ca_certs=self.ca_certs,
                                disable_ssl_certificate_validation=
                                        self.disable_ssl_certificate_validation)
                    else:
                        conn = self.connections[conn_key] = connection_type(
                                authority, timeout=self.timeout,
                                proxy_info=proxy_info,
                                ca_certs=self.ca_certs,
                                disable_ssl_certificate_validation=
                                        self.disable_ssl_certificate_validation)
                else:
                    conn = self.connections[conn_key] = connection_type(
                            authority, timeout=self.timeout,
                            proxy_info=proxy_info)
                conn.set_debuglevel(debuglevel)

            if 'range' not in headers and 'accept-encoding' not in headers:
                headers['accept-encoding'] = 'gzip, deflate'

            info = email.Message.Message()
            cached_value = None
            if self.cache:
                cachekey = defrag_uri
                cached_value = self.cache.get(cachekey)
                if cached_value:
                    # info = email.message_from_string(cached_value)
                    #
                    # Need to replace the line above with the kludge below
                    # to fix the non-existent bug not fixed in this
                    # bug report: http://mail.python.org/pipermail/python-bugs-list/2005-September/030289.html
                    try:
                        info, content = cached_value.split('\r\n\r\n', 1)
                        feedparser = email.FeedParser.FeedParser()
                        feedparser.feed(info)
                        info = feedparser.close()
                        feedparser._parse = None
                    except (IndexError, ValueError):
                        self.cache.delete(cachekey)
                        cachekey = None
                        cached_value = None
            else:
                cachekey = None

            if method in self.optimistic_concurrency_methods and self.cache and info.has_key('etag') and not self.ignore_etag and 'if-match' not in headers:
                # http://www.w3.org/1999/04/Editing/
                headers['if-match'] = info['etag']

            if method not in ["GET", "HEAD"] and self.cache and cachekey:
                # RFC 2616 Section 13.10
                self.cache.delete(cachekey)

            # Check the vary header in the cache to see if this request
            # matches what varies in the cache.
            if method in ['GET', 'HEAD'] and 'vary' in info:
                vary = info['vary']
                vary_headers = vary.lower().replace(' ', '').split(',')
                for header in vary_headers:
                    key = '-varied-%s' % header
                    value = info[key]
                    if headers.get(header, None) != value:
                            cached_value = None
                            break

            if cached_value and method in ["GET", "HEAD"] and self.cache and 'range' not in headers:
                if info.has_key('-x-permanent-redirect-url'):
                    # Should cached permanent redirects be counted in our redirection count? For now, yes.
                    if redirections <= 0:
                      raise RedirectLimit("Redirected more times than rediection_limit allows.", {}, "")
                    (response, new_content) = self.request(info['-x-permanent-redirect-url'], "GET", headers = headers, redirections = redirections - 1)
                    response.previous = Response(info)
                    response.previous.fromcache = True
                else:
                    # Determine our course of action:
                    #   Is the cached entry fresh or stale?
                    #   Has the client requested a non-cached response?
                    #
                    # There seems to be three possible answers:
                    # 1. [FRESH] Return the cache entry w/o doing a GET
                    # 2. [STALE] Do the GET (but add in cache validators if available)
                    # 3. [TRANSPARENT] Do a GET w/o any cache validators (Cache-Control: no-cache) on the request
                    entry_disposition = _entry_disposition(info, headers)

                    if entry_disposition == "FRESH":
                        if not cached_value:
                            info['status'] = '504'
                            content = ""
                        response = Response(info)
                        if cached_value:
                            response.fromcache = True
                        return (response, content)

                    if entry_disposition == "STALE":
                        if info.has_key('etag') and not self.ignore_etag and not 'if-none-match' in headers:
                            headers['if-none-match'] = info['etag']
                        if info.has_key('last-modified') and not 'last-modified' in headers:
                            headers['if-modified-since'] = info['last-modified']
                    elif entry_disposition == "TRANSPARENT":
                        pass

                    (response, new_content) = self._request(conn, authority, uri, request_uri, method, body, headers, redirections, cachekey)

                if response.status == 304 and method == "GET":
                    # Rewrite the cache entry with the new end-to-end headers
                    # Take all headers that are in response
                    # and overwrite their values in info.
                    # unless they are hop-by-hop, or are listed in the connection header.

                    for key in _get_end2end_headers(response):
                        info[key] = response[key]
                    merged_response = Response(info)
                    if hasattr(response, "_stale_digest"):
                        merged_response._stale_digest = response._stale_digest
                    _updateCache(headers, merged_response, content, self.cache, cachekey)
                    response = merged_response
                    response.status = 200
                    response.fromcache = True

                elif response.status == 200:
                    content = new_content
                else:
                    self.cache.delete(cachekey)
                    content = new_content
            else:
                cc = _parse_cache_control(headers)
                if cc.has_key('only-if-cached'):
                    info['status'] = '504'
                    response = Response(info)
                    content = ""
                else:
                    (response, content) = self._request(conn, authority, uri, request_uri, method, body, headers, redirections, cachekey)
        except Exception, e:
            if self.force_exception_to_status_code:
                if isinstance(e, HttpLib2ErrorWithResponse):
                    response = e.response
                    content = e.content
                    response.status = 500
                    response.reason = str(e)
                elif isinstance(e, socket.timeout):
                    content = "Request Timeout"
                    response = Response( {
                            "content-type": "text/plain",
                            "status": "408",
                            "content-length": len(content)
                            })
                    response.reason = "Request Timeout"
                else:
                    content = str(e)
                    response = Response( {
                            "content-type": "text/plain",
                            "status": "400",
                            "content-length": len(content)
                            })
                    response.reason = "Bad Request"
            else:
                raise


        return (response, content)

    def _get_proxy_info(self, scheme, authority):
        """Return a ProxyInfo instance (or None) based on the scheme
        and authority.
        """
        hostname, port = urllib.splitport(authority)
        proxy_info = self.proxy_info
        if callable(proxy_info):
            proxy_info = proxy_info(scheme)

        if (hasattr(proxy_info, 'applies_to')
            and not proxy_info.applies_to(hostname)):
            proxy_info = None
        return proxy_info


class Response(dict):
    """An object more like email.Message than httplib.HTTPResponse."""

    """Is this response from our local cache"""
    fromcache = False

    """HTTP protocol version used by server. 10 for HTTP/1.0, 11 for HTTP/1.1. """
    version = 11

    "Status code returned by server. "
    status = 200

    """Reason phrase returned by server."""
    reason = "Ok"

    previous = None

    def __init__(self, info):
        # info is either an email.Message or
        # an httplib.HTTPResponse object.
        if isinstance(info, httplib.HTTPResponse):
            for key, value in info.getheaders():
                self[key.lower()] = value
            self.status = info.status
            self['status'] = str(self.status)
            self.reason = info.reason
            self.version = info.version
        elif isinstance(info, email.Message.Message):
            for key, value in info.items():
                self[key.lower()] = value
            self.status = int(self['status'])
        else:
            for key, value in info.iteritems():
                self[key.lower()] = value
            self.status = int(self.get('status', self.status))
            self.reason = self.get('reason', self.reason)


    def __getattr__(self, name):
        if name == 'dict':
            return self
        else:
            raise AttributeError, name
