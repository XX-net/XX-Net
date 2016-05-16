import collections

from datetime import (
    date,
    datetime,
    timedelta,
    )
import re
import string
import time

from webob.compat import (
    PY3,
    text_type,
    bytes_,
    text_,
    native_,
    string_types,
    )

__all__ = ['Cookie']

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
            bytes_val = _quote(bytes_(value, 'utf-8'))
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
            raise TypeError('cookie name must be valid according to RFC 2109')
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
        assert _valid_cookie_name(name)
        assert isinstance(value, bytes)
        self.name = name
        self.value = value
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
        add(self.name + b'=' + _quote(self.value))
        if full:
            for k in _c_valkeys:
                v = self[k]
                if v:
                    add(_c_renames[k]+b'='+_quote(v))
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

_c_renames = {
    b"path" : b"Path",
    b"comment" : b"Comment",
    b"domain" : b"Domain",
    b"max-age" : b"Max-Age",
}
_c_valkeys = sorted(_c_renames)
_c_keys = set(_c_renames)
_c_keys.update([b'expires', b'secure', b'httponly'])




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

_b_dollar_sign = 36 if PY3 else '$'
_b_quote_mark = 34 if PY3 else '"'

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

# these chars can be in cookie value w/o causing it to be quoted
_no_escape_special_chars = "!#$%&'*+-.^_`|~/"
_no_escape_chars = (string.ascii_letters + string.digits +
                    _no_escape_special_chars)
_no_escape_bytes = bytes_(_no_escape_chars)
# these chars never need to be quoted
_escape_noop_chars = _no_escape_chars + ': '
# this is a map used to escape the values
_escape_map = dict((chr(i), '\\%03o' % i) for i in range(256))
_escape_map.update(zip(_escape_noop_chars, _escape_noop_chars))
_escape_map['"'] = r'\"'
_escape_map['\\'] = r'\\'
if PY3: # pragma: no cover
    # convert to {int -> bytes}
    _escape_map = dict((ord(k), bytes_(v, 'ascii')) for k, v in _escape_map.items())
_escape_char = _escape_map.__getitem__

weekdays = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
months = (None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
          'Oct', 'Nov', 'Dec')

_notrans_binary = b' '*256

def _needs_quoting(v):
    return v.translate(_notrans_binary, _no_escape_bytes)

def _quote(v):
    #assert isinstance(v, bytes)
    if _needs_quoting(v):
        return b'"' + b''.join(map(_escape_char, v)) + b'"'
    return v

def _valid_cookie_name(key):
    return isinstance(key, bytes) and not (
        _needs_quoting(key)
        or key[0] == _b_dollar_sign
        or key.lower() in _c_keys
    )
