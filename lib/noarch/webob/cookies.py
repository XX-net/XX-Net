import collections

import base64
import binascii
import hashlib
import hmac
import json
from datetime import (
    date,
    datetime,
    timedelta,
    )
import re
import string
import time
import warnings

from webob.compat import (
    PY3,
    text_type,
    bytes_,
    text_,
    native_,
    string_types,
    )

from webob.util import strings_differ

__all__ = ['Cookie', 'CookieProfile', 'SignedCookieProfile', 'SignedSerializer',
           'JSONSerializer', 'Base64Serializer', 'make_cookie']

_marker = object()

class RequestCookies(collections.MutableMapping):

    _cache_key = 'webob._parsed_cookies'

    def __init__(self, environ):
        self._environ = environ

    @property
    def _cache(self):
        env = self._environ
        header = env.get('HTTP_COOKIE', '')
        cache, cache_header = env.get(self._cache_key, ({}, None))
        if cache_header == header:
            return cache
        d = lambda b: b.decode('utf8')
        cache = dict((d(k), d(v)) for k,v in parse_cookie(header))
        env[self._cache_key] = (cache, header)
        return cache

    def _mutate_header(self, name, value):
        header = self._environ.get('HTTP_COOKIE')
        had_header = header is not None
        header = header or ''
        if PY3: # pragma: no cover
                header = header.encode('latin-1')
        bytes_name = bytes_(name, 'ascii')
        if value is None:
            replacement = None
        else:
            bytes_val = _value_quote(bytes_(value, 'utf-8'))
            replacement = bytes_name + b'=' + bytes_val
        matches = _rx_cookie.finditer(header)
        found = False
        for match in matches:
            start, end = match.span()
            match_name = match.group(1)
            if match_name == bytes_name:
                found = True
                if replacement is None: # remove value
                    header = header[:start].rstrip(b' ;') + header[end:]
                else: # replace value
                    header = header[:start] + replacement + header[end:]
                break
        else:
            if replacement is not None:
                if header:
                    header += b'; ' + replacement
                else:
                    header = replacement

        if header:
            self._environ['HTTP_COOKIE'] = native_(header, 'latin-1')
        elif had_header:
            self._environ['HTTP_COOKIE'] = ''

        return found

    def _valid_cookie_name(self, name):
        if not isinstance(name, string_types):
            raise TypeError(name, 'cookie name must be a string')
        if not isinstance(name, text_type):
            name = text_(name, 'utf-8')
        try:
            bytes_cookie_name = bytes_(name, 'ascii')
        except UnicodeEncodeError:
            raise TypeError('cookie name must be encodable to ascii')
        if not _valid_cookie_name(bytes_cookie_name):
            raise TypeError('cookie name must be valid according to RFC 6265')
        return name

    def __setitem__(self, name, value):
        name = self._valid_cookie_name(name)
        if not isinstance(value, string_types):
            raise ValueError(value, 'cookie value must be a string')
        if not isinstance(value, text_type):
            try:
                value = text_(value, 'utf-8')
            except UnicodeDecodeError:
                raise ValueError(
                    value, 'cookie value must be utf-8 binary or unicode')
        self._mutate_header(name, value)

    def __getitem__(self, name):
        return self._cache[name]

    def get(self, name, default=None):
        return self._cache.get(name, default)

    def __delitem__(self, name):
        name = self._valid_cookie_name(name)
        found = self._mutate_header(name, None)
        if not found:
            raise KeyError(name)

    def keys(self):
        return self._cache.keys()

    def values(self):
        return self._cache.values()

    def items(self):
        return self._cache.items()

    if not PY3:
        def iterkeys(self):
            return self._cache.iterkeys()

        def itervalues(self):
            return self._cache.itervalues()

        def iteritems(self):
            return self._cache.iteritems()

    def __contains__(self, name):
        return name in self._cache

    def __iter__(self):
        return self._cache.__iter__()

    def __len__(self):
        return len(self._cache)

    def clear(self):
        self._environ['HTTP_COOKIE'] = ''

    def __repr__(self):
        return '<RequestCookies (dict-like) with values %r>' % (self._cache,)


class Cookie(dict):
    def __init__(self, input=None):
        if input:
            self.load(input)

    def load(self, data):
        morsel = {}
        for key, val in _parse_cookie(data):
            if key.lower() in _c_keys:
                morsel[key] = val
            else:
                morsel = self.add(key, val)

    def add(self, key, val):
        if not isinstance(key, bytes):
           key = key.encode('ascii', 'replace')
        if not _valid_cookie_name(key):
            return {}
        r = Morsel(key, val)
        dict.__setitem__(self, key, r)
        return r
    __setitem__ = add

    def serialize(self, full=True):
        return '; '.join(m.serialize(full) for m in self.values())

    def values(self):
        return [m for _, m in sorted(self.items())]

    __str__ = serialize

    def __repr__(self):
        return '<%s: [%s]>' % (self.__class__.__name__,
                               ', '.join(map(repr, self.values())))


def _parse_cookie(data):
    if PY3: # pragma: no cover
        data = data.encode('latin-1')
    for key, val in _rx_cookie.findall(data):
        yield key, _unquote(val)

def parse_cookie(data):
    """
    Parse cookies ignoring anything except names and values
    """
    return ((k,v) for k,v in _parse_cookie(data) if _valid_cookie_name(k))


def cookie_property(key, serialize=lambda v: v):
    def fset(self, v):
        self[key] = serialize(v)
    return property(lambda self: self[key], fset)

def serialize_max_age(v):
    if isinstance(v, timedelta):
        v = str(v.seconds + v.days*24*60*60)
    elif isinstance(v, int):
        v = str(v)
    return bytes_(v)

def serialize_cookie_date(v):
    if v is None:
        return None
    elif isinstance(v, bytes):
        return v
    elif isinstance(v, text_type):
        return v.encode('ascii')
    elif isinstance(v, int):
        v = timedelta(seconds=v)
    if isinstance(v, timedelta):
        v = datetime.utcnow() + v
    if isinstance(v, (datetime, date)):
        v = v.timetuple()
    r = time.strftime('%%s, %d-%%s-%Y %H:%M:%S GMT', v)
    return bytes_(r % (weekdays[v[6]], months[v[1]]), 'ascii')

class Morsel(dict):
    __slots__ = ('name', 'value')
    def __init__(self, name, value):
        self.name = bytes_(name, encoding='ascii')
        self.value = bytes_(value, encoding='ascii')
        assert _valid_cookie_name(self.name)
        self.update(dict.fromkeys(_c_keys, None))

    path = cookie_property(b'path')
    domain = cookie_property(b'domain')
    comment = cookie_property(b'comment')
    expires = cookie_property(b'expires', serialize_cookie_date)
    max_age = cookie_property(b'max-age', serialize_max_age)
    httponly = cookie_property(b'httponly', bool)
    secure = cookie_property(b'secure', bool)

    def __setitem__(self, k, v):
        k = bytes_(k.lower(), 'ascii')
        if k in _c_keys:
            dict.__setitem__(self, k, v)

    def serialize(self, full=True):
        result = []
        add = result.append
        add(self.name + b'=' + _value_quote(self.value))
        if full:
            for k in _c_valkeys:
                v = self[k]
                if v:
                    info = _c_renames[k]
                    name = info['name']
                    quoter = info['quoter']
                    add(name + b'=' + quoter(v))
            expires = self[b'expires']
            if expires:
                add(b'expires=' + expires)
            if self.secure:
                add(b'secure')
            if self.httponly:
                add(b'HttpOnly')
        return native_(b'; '.join(result), 'ascii')

    __str__ = serialize

    def __repr__(self):
        return '<%s: %s=%r>' % (self.__class__.__name__,
            native_(self.name),
            native_(self.value)
        )

#
# parsing
#


_re_quoted = r'"(?:\\"|.)*?"' # any doublequoted string
_legal_special_chars = "~!@#$%^&*()_+=-`.?|:/(){}<>'"
_re_legal_char  = r"[\w\d%s]" % re.escape(_legal_special_chars)
_re_expires_val = r"\w{3},\s[\w\d-]{9,11}\s[\d:]{8}\sGMT"
_re_cookie_str_key = r"(%s+?)" % _re_legal_char
_re_cookie_str_equal = r"\s*=\s*"
_re_unquoted_val = r"(?:%s|\\(?:[0-3][0-7][0-7]|.))*" % _re_legal_char
_re_cookie_str_val = r"(%s|%s|%s)" % (_re_quoted, _re_expires_val,
                                       _re_unquoted_val)
_re_cookie_str = _re_cookie_str_key + _re_cookie_str_equal + _re_cookie_str_val

_rx_cookie = re.compile(bytes_(_re_cookie_str, 'ascii'))
_rx_unquote = re.compile(bytes_(r'\\([0-3][0-7][0-7]|.)', 'ascii'))

_bchr = (lambda i: bytes([i])) if PY3 else chr
_ch_unquote_map = dict((bytes_('%03o' % i), _bchr(i))
    for i in range(256)
)
_ch_unquote_map.update((v, v) for v in list(_ch_unquote_map.values()))

_b_dollar_sign = ord('$') if PY3 else '$'
_b_quote_mark = ord('"') if PY3 else '"'

def _unquote(v):
    #assert isinstance(v, bytes)
    if v and v[0] == v[-1] == _b_quote_mark:
        v = v[1:-1]
    return _rx_unquote.sub(_ch_unquote, v)

def _ch_unquote(m):
    return _ch_unquote_map[m.group(1)]


#
# serializing
#

# these chars can be in cookie value see
# http://tools.ietf.org/html/rfc6265#section-4.1.1 and
# https://github.com/Pylons/webob/pull/104#issuecomment-28044314
#
# ! (0x21), "#$%&'()*+" (0x25-0x2B), "-./0123456789:" (0x2D-0x3A),
# "<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[" (0x3C-0x5B),
# "]^_`abcdefghijklmnopqrstuvwxyz{|}~" (0x5D-0x7E)

_allowed_special_chars = "!#$%&'()*+-./:<=>?@[]^_`{|}~"
_allowed_cookie_chars = (string.ascii_letters + string.digits +
                    _allowed_special_chars)
_allowed_cookie_bytes = bytes_(_allowed_cookie_chars)

# these are the characters accepted in cookie *names*
# From http://tools.ietf.org/html/rfc2616#section-2.2:
# token          = 1*<any CHAR except CTLs or separators>
# separators     = "(" | ")" | "<" | ">" | "@"
#                | "," | ";" | ":" | "\" | <">
#                | "/" | "[" | "]" | "?" | "="
#                | "{" | "}" | SP | HT
#
# CTL            = <any US-ASCII control character
#                         (octets 0 - 31) and DEL (127)>
#
_valid_token_chars = string.ascii_letters + string.digits + "!#$%&'*+-.^_`|~"
_valid_token_bytes = bytes_(_valid_token_chars)

# this is a map used to escape the values

_escape_noop_chars = _allowed_cookie_chars + ' '
_escape_map = dict((chr(i), '\\%03o' % i) for i in range(256))
_escape_map.update(zip(_escape_noop_chars, _escape_noop_chars))
if PY3: # pragma: no cover
    # convert to {int -> bytes}
    _escape_map = dict(
        (ord(k), bytes_(v, 'ascii')) for k, v in _escape_map.items()
        )
_escape_char = _escape_map.__getitem__

weekdays = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
months = (None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
          'Oct', 'Nov', 'Dec')


# This is temporary, until we can remove this from _value_quote
_should_raise = None

def __warn_or_raise(text, warn_class, to_raise, raise_reason):
    if _should_raise:
        raise to_raise(raise_reason)

    else:
        warnings.warn(text, warn_class, stacklevel=2)


def _value_quote(v):
    # This looks scary, but is simple. We remove all valid characters from the
    # string, if we end up with leftovers (string is longer than 0, we have
    # invalid characters in our value)

    leftovers = v.translate(None, _allowed_cookie_bytes)
    if leftovers:
        __warn_or_raise(
                "Cookie value contains invalid bytes: (%s). Future versions "
                "will raise ValueError upon encountering invalid bytes." %
                (leftovers,),
                RuntimeWarning, ValueError, 'Invalid characters in cookie value'
                )
        #raise ValueError('Invalid characters in cookie value')
        return b'"' + b''.join(map(_escape_char, v)) + b'"'

    return v

def _valid_cookie_name(key):
    return isinstance(key, bytes) and not (
        key.translate(None, _valid_token_bytes)
        # Not explicitly required by RFC6265, may consider removing later:
        or key[0] == _b_dollar_sign
        or key.lower() in _c_keys
    )

def _path_quote(v):
    return b''.join(map(_escape_char, v))

_domain_quote = _path_quote
_max_age_quote = _path_quote

_c_renames = {
    b"path" : {'name':b"Path", 'quoter':_path_quote},
    b"comment" : {'name':b"Comment", 'quoter':_value_quote},
    b"domain" : {'name':b"Domain", 'quoter':_domain_quote},
    b"max-age" : {'name':b"Max-Age", 'quoter':_max_age_quote},
    }
_c_valkeys = sorted(_c_renames)
_c_keys = set(_c_renames)
_c_keys.update([b'expires', b'secure', b'httponly'])


def make_cookie(name, value, max_age=None, path='/', domain=None,
                secure=False, httponly=False, comment=None):
    """ Generate a cookie value.  If ``value`` is None, generate a cookie value
    with an expiration date in the past"""

    # We are deleting the cookie, override max_age and expires
    if value is None:
        value = b''
        # Note that the max-age value of zero is technically contraspec;
        # RFC6265 says that max-age cannot be zero.  However, all browsers
        # appear to support this to mean "delete immediately".
        # http://www.timwilson.id.au/news-three-critical-problems-with-rfc6265.html
        max_age = 0
        expires = 'Wed, 31-Dec-97 23:59:59 GMT'

    # Convert max_age to seconds
    elif isinstance(max_age, timedelta):
        max_age = (max_age.days * 60 * 60 * 24) + max_age.seconds
        expires = max_age
    elif max_age is not None:
        try:
            max_age = int(max_age)
        except ValueError:
            raise ValueError('max_age should be an integer. Amount of seconds until expiration.')

        expires = max_age
    else:
        expires = None

    morsel = Morsel(name, value)

    if domain is not None:
        morsel.domain = bytes_(domain)
    if path is not None:
        morsel.path = bytes_(path)
    if httponly:
        morsel.httponly = True
    if secure:
        morsel.secure = True
    if max_age is not None:
        morsel.max_age = max_age
    if expires is not None:
        morsel.expires = expires
    if comment is not None:
        morsel.comment = bytes_(comment)
    return morsel.serialize()

class JSONSerializer(object):
    """ A serializer which uses `json.dumps`` and ``json.loads``"""
    def dumps(self, appstruct):
        return bytes_(json.dumps(appstruct), encoding='utf-8')

    def loads(self, bstruct):
        # NB: json.loads raises ValueError if no json object can be decoded
        # so we don't have to do it explicitly here.
        return json.loads(text_(bstruct, encoding='utf-8'))

class Base64Serializer(object):
    """ A serializer which uses base64 to encode/decode data"""

    def __init__(self, serializer=None):
        if serializer is None:
            serializer = JSONSerializer()

        self.serializer = serializer

    def dumps(self, appstruct):
        """
        Given an ``appstruct``, serialize and sign the data.

        Returns a bytestring.
        """
        cstruct = self.serializer.dumps(appstruct) # will be bytes
        return base64.urlsafe_b64encode(cstruct)

    def loads(self, bstruct):
        """
        Given a ``bstruct`` (a bytestring), verify the signature and then
        deserialize and return the deserialized value.

        A ``ValueError`` will be raised if the signature fails to validate.
        """
        try:
            cstruct = base64.urlsafe_b64decode(bytes_(bstruct))
        except (binascii.Error, TypeError) as e:
            raise ValueError('Badly formed base64 data: %s' % e)

        return self.serializer.loads(cstruct)

class SignedSerializer(object):
    """
    A helper to cryptographically sign arbitrary content using HMAC.

    The serializer accepts arbitrary functions for performing the actual
    serialization and deserialization.

    ``secret``
      A string which is used to sign the cookie. The secret should be at
      least as long as the block size of the selected hash algorithm. For
      ``sha512`` this would mean a 128 bit (64 character) secret.

    ``salt``
      A namespace to avoid collisions between different uses of a shared
      secret.

    ``hashalg``
      The HMAC digest algorithm to use for signing. The algorithm must be
      supported by the :mod:`hashlib` library. Default: ``'sha512'``.

    ``serializer``
      An object with two methods: `loads`` and ``dumps``.  The ``loads`` method
      should accept bytes and return a Python object.  The ``dumps`` method
      should accept a Python object and return bytes.  A ``ValueError`` should
      be raised for malformed inputs.  Default: ``None`, which will use a
      derivation of :func:`json.dumps` and ``json.loads``.

    """

    def __init__(self,
                 secret,
                 salt,
                 hashalg='sha512',
                 serializer=None,
                 ):
        self.salt = salt
        self.secret = secret
        self.hashalg = hashalg

        try:
            # bwcompat with webob <= 1.3.1, leave latin-1 as the default
            self.salted_secret = bytes_(salt or '') + bytes_(secret)
        except UnicodeEncodeError:
            self.salted_secret = (
                bytes_(salt or '', 'utf-8') + bytes_(secret, 'utf-8'))

        self.digestmod = lambda string=b'': hashlib.new(self.hashalg, string)
        self.digest_size = self.digestmod().digest_size

        if serializer is None:
            serializer = JSONSerializer()

        self.serializer = serializer

    def dumps(self, appstruct):
        """
        Given an ``appstruct``, serialize and sign the data.

        Returns a bytestring.
        """
        cstruct = self.serializer.dumps(appstruct) # will be bytes
        sig = hmac.new(self.salted_secret, cstruct, self.digestmod).digest()
        return base64.urlsafe_b64encode(sig + cstruct).rstrip(b'=')

    def loads(self, bstruct):
        """
        Given a ``bstruct`` (a bytestring), verify the signature and then
        deserialize and return the deserialized value.

        A ``ValueError`` will be raised if the signature fails to validate.
        """
        try:
            b64padding = b'=' * (-len(bstruct) % 4)
            fstruct = base64.urlsafe_b64decode(bytes_(bstruct) + b64padding)
        except (binascii.Error, TypeError) as e:
            raise ValueError('Badly formed base64 data: %s' % e)

        cstruct = fstruct[self.digest_size:]
        expected_sig = fstruct[:self.digest_size]

        sig = hmac.new(
            self.salted_secret, bytes_(cstruct), self.digestmod).digest()

        if strings_differ(sig, expected_sig):
            raise ValueError('Invalid signature')

        return self.serializer.loads(cstruct)


_default = object()

class CookieProfile(object):
    """
    A helper class that helps bring some sanity to the insanity that is cookie
    handling.

    The helper is capable of generating multiple cookies if necessary to
    support subdomains and parent domains.

    ``cookie_name``
      The name of the cookie used for sessioning. Default: ``'session'``.

    ``max_age``
      The maximum age of the cookie used for sessioning (in seconds).
      Default: ``None`` (browser scope).

    ``secure``
      The 'secure' flag of the session cookie. Default: ``False``.

    ``httponly``
      Hide the cookie from Javascript by setting the 'HttpOnly' flag of the
      session cookie. Default: ``False``.

    ``path``
      The path used for the session cookie. Default: ``'/'``.

    ``domains``
      The domain(s) used for the session cookie. Default: ``None`` (no domain).
      Can be passed an iterable containing multiple domains, this will set
      multiple cookies one for each domain.

    ``serializer``
      An object with two methods: ``loads`` and ``dumps``.  The ``loads`` method
      should accept a bytestring and return a Python object.  The ``dumps``
      method should accept a Python object and return bytes.  A ``ValueError``
      should be raised for malformed inputs.  Default: ``None``, which will use
      a derivation of :func:`json.dumps` and :func:`json.loads`.

    """

    def __init__(self,
                 cookie_name,
                 secure=False,
                 max_age=None,
                 httponly=None,
                 path='/',
                 domains=None,
                 serializer=None
                 ):
        self.cookie_name = cookie_name
        self.secure = secure
        self.max_age = max_age
        self.httponly = httponly
        self.path = path
        self.domains = domains

        if serializer is None:
            serializer = Base64Serializer()

        self.serializer = serializer
        self.request = None

    def __call__(self, request):
        """ Bind a request to a copy of this instance and return it"""

        return self.bind(request)

    def bind(self, request):
        """ Bind a request to a copy of this instance and return it"""

        selfish = CookieProfile(
            self.cookie_name,
            self.secure,
            self.max_age,
            self.httponly,
            self.path,
            self.domains,
            self.serializer,
            )
        selfish.request = request
        return selfish

    def get_value(self):
        """ Looks for a cookie by name in the currently bound request, and
        returns its value.  If the cookie profile is not bound to a request,
        this method will raise a :exc:`ValueError`.

        Looks for the cookie in the cookies jar, and if it can find it it will
        attempt to deserialize it.  Returns ``None`` if there is no cookie or
        if the value in the cookie cannot be successfully deserialized.
        """

        if not self.request:
            raise ValueError('No request bound to cookie profile')

        cookie = self.request.cookies.get(self.cookie_name)

        if cookie is not None:
            try:
                return self.serializer.loads(bytes_(cookie))
            except ValueError:
                return None

    def set_cookies(self, response, value, domains=_default, max_age=_default,
                    path=_default, secure=_default, httponly=_default):
        """ Set the cookies on a response."""
        cookies = self.get_headers(
            value,
            domains=domains,
            max_age=max_age,
            path=path,
            secure=secure,
            httponly=httponly
            )
        response.headerlist.extend(cookies)
        return response

    def get_headers(self, value, domains=_default, max_age=_default,
                    path=_default, secure=_default, httponly=_default):
        """ Retrieve raw headers for setting cookies.

        Returns a list of headers that should be set for the cookies to
        be correctly tracked.
        """
        if value is None:
            max_age = 0
            bstruct = None
        else:
            bstruct = self.serializer.dumps(value)

        return self._get_cookies(
            bstruct,
            domains=domains,
            max_age=max_age,
            path=path,
            secure=secure,
            httponly=httponly
            )

    def _get_cookies(self, value, domains, max_age, path, secure, httponly):
        """Internal function

        This returns a list of cookies that are valid HTTP Headers.

        :environ: The request environment
        :value: The value to store in the cookie
        :domains: The domains, overrides any set in the CookieProfile
        :max_age: The max_age, overrides any set in the CookieProfile
        :path: The path, overrides any set in the CookieProfile
        :secure: Set this cookie to secure, overrides any set in CookieProfile
        :httponly: Set this cookie to HttpOnly, overrides any set in CookieProfile

        """

        # If the user doesn't provide values, grab the defaults
        if domains is _default:
            domains = self.domains

        if max_age is _default:
            max_age = self.max_age

        if path is _default:
            path = self.path

        if secure is _default:
            secure = self.secure

        if httponly is _default:
            httponly = self.httponly

        # Length selected based upon http://browsercookielimits.x64.me
        if value is not None and len(value) > 4093:
            raise ValueError(
                'Cookie value is too long to store (%s bytes)' %
                len(value)
            )

        cookies = []

        if not domains:
            cookievalue = make_cookie(
                    self.cookie_name,
                    value,
                    path=path,
                    max_age=max_age,
                    httponly=httponly,
                    secure=secure
            )
            cookies.append(('Set-Cookie', cookievalue))

        else:
            for domain in domains:
                cookievalue = make_cookie(
                    self.cookie_name,
                    value,
                    path=path,
                    domain=domain,
                    max_age=max_age,
                    httponly=httponly,
                    secure=secure,
                )
                cookies.append(('Set-Cookie', cookievalue))

        return cookies


class SignedCookieProfile(CookieProfile):
    """
    A helper for generating cookies that are signed to prevent tampering.

    By default this will create a single cookie, given a value it will
    serialize it, then use HMAC to cryptographically sign the data. Finally
    the result is base64-encoded for transport. This way a remote user can
    not tamper with the value without uncovering the secret/salt used.

    ``secret``
      A string which is used to sign the cookie. The secret should be at
      least as long as the block size of the selected hash algorithm. For
      ``sha512`` this would mean a 128 bit (64 character) secret.

    ``salt``
      A namespace to avoid collisions between different uses of a shared
      secret.

    ``hashalg``
      The HMAC digest algorithm to use for signing. The algorithm must be
      supported by the :mod:`hashlib` library. Default: ``'sha512'``.

    ``cookie_name``
      The name of the cookie used for sessioning. Default: ``'session'``.

    ``max_age``
      The maximum age of the cookie used for sessioning (in seconds).
      Default: ``None`` (browser scope).

    ``secure``
      The 'secure' flag of the session cookie. Default: ``False``.

    ``httponly``
      Hide the cookie from Javascript by setting the 'HttpOnly' flag of the
      session cookie. Default: ``False``.

    ``path``
      The path used for the session cookie. Default: ``'/'``.

    ``domains``
      The domain(s) used for the session cookie. Default: ``None`` (no domain).
      Can be passed an iterable containing multiple domains, this will set
      multiple cookies one for each domain.

    ``serializer``
      An object with two methods: `loads`` and ``dumps``.  The ``loads`` method
      should accept bytes and return a Python object.  The ``dumps`` method
      should accept a Python object and return bytes.  A ``ValueError`` should
      be raised for malformed inputs.  Default: ``None`, which will use a
      derivation of :func:`json.dumps` and ``json.loads``.
    """
    def __init__(self,
                 secret,
                 salt,
                 cookie_name,
                 secure=False,
                 max_age=None,
                 httponly=False,
                 path="/",
                 domains=None,
                 hashalg='sha512',
                 serializer=None,
                 ):
        self.secret = secret
        self.salt = salt
        self.hashalg = hashalg
        self.original_serializer = serializer

        signed_serializer = SignedSerializer(
            secret,
            salt,
            hashalg,
            serializer=self.original_serializer,
            )
        CookieProfile.__init__(
            self,
            cookie_name,
            secure=secure,
            max_age=max_age,
            httponly=httponly,
            path=path,
            domains=domains,
            serializer=signed_serializer,
            )

    def bind(self, request):
        """ Bind a request to a copy of this instance and return it"""

        selfish = SignedCookieProfile(
            self.secret,
            self.salt,
            self.cookie_name,
            self.secure,
            self.max_age,
            self.httponly,
            self.path,
            self.domains,
            self.hashalg,
            self.original_serializer,
            )
        selfish.request = request
        return selfish

