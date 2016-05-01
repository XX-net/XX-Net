from datetime import (
    date,
    datetime,
    )

import re

from webob.byterange import (
    ContentRange,
    Range,
    )

from webob.compat import (
    PY3,
    text_type,
    )

from webob.datetime_utils import (
    parse_date,
    serialize_date,
    )

from webob.util import (
    header_docstring,
    warn_deprecation,
    )


CHARSET_RE = re.compile(r';\s*charset=([^;]*)', re.I)
SCHEME_RE = re.compile(r'^[a-z]+:', re.I)


_not_given = object()

def environ_getter(key, default=_not_given, rfc_section=None):
    if rfc_section:
        doc = header_docstring(key, rfc_section)
    else:
        doc = "Gets and sets the ``%s`` key in the environment." % key
    if default is _not_given:
        def fget(req):
            return req.environ[key]
        def fset(req, val):
            req.environ[key] = val
        fdel = None
    else:
        def fget(req):
            return req.environ.get(key, default)
        def fset(req, val):
            if val is None:
                if key in req.environ:
                    del req.environ[key]
            else:
                req.environ[key] = val
        def fdel(req):
            del req.environ[key]
    return property(fget, fset, fdel, doc=doc)


def environ_decoder(key, default=_not_given, rfc_section=None,
                    encattr=None):
    if rfc_section:
        doc = header_docstring(key, rfc_section)
    else:
        doc = "Gets and sets the ``%s`` key in the environment." % key
    if default is _not_given:
        def fget(req):
            return req.encget(key, encattr=encattr)
        def fset(req, val):
            return req.encset(key, val, encattr=encattr)
        fdel = None
    else:
        def fget(req):
            return req.encget(key, default, encattr=encattr)
        def fset(req, val):
            if val is None:
                if key in req.environ:
                    del req.environ[key]
            else:
                return req.encset(key, val, encattr=encattr)
        def fdel(req):
            del req.environ[key]
    return property(fget, fset, fdel, doc=doc)

def upath_property(key):
    if PY3: # pragma: no cover
        def fget(req):
            encoding = req.url_encoding
            return req.environ.get(key, '').encode('latin-1').decode(encoding)
        def fset(req, val):
            encoding = req.url_encoding
            req.environ[key] = val.encode(encoding).decode('latin-1')
    else:
        def fget(req):
            encoding = req.url_encoding
            return req.environ.get(key, '').decode(encoding)
        def fset(req, val):
            encoding = req.url_encoding
            if isinstance(val, text_type):
                val = val.encode(encoding)
            req.environ[key] = val
    return property(fget, fset, doc='upath_property(%r)' % key)


def deprecated_property(attr, name, text, version): # pragma: no cover
    """
    Wraps a descriptor, with a deprecation warning or error
    """
    def warn():
        warn_deprecation('The attribute %s is deprecated: %s'
            % (attr, text),
            version,
            3
        )
    def fget(self):
        warn()
        return attr.__get__(self, type(self))
    def fset(self, val):
        warn()
        attr.__set__(self, val)
    def fdel(self):
        warn()
        attr.__delete__(self)
    return property(fget, fset, fdel,
        '<Deprecated attribute %s>' % attr
    )


def header_getter(header, rfc_section):
    doc = header_docstring(header, rfc_section)
    key = header.lower()

    def fget(r):
        for k, v in r._headerlist:
            if k.lower() == key:
                return v

    def fset(r, value):
        fdel(r)
        if value is not None:
            if isinstance(value, text_type) and not PY3:
                value = value.encode('latin-1')
            r._headerlist.append((header, value))

    def fdel(r):
        items = r._headerlist
        for i in range(len(items)-1, -1, -1):
            if items[i][0].lower() == key:
                del items[i]

    return property(fget, fset, fdel, doc)




def converter(prop, parse, serialize, convert_name=None):
    assert isinstance(prop, property)
    convert_name = convert_name or "``%s`` and ``%s``" % (parse.__name__,
                                                  serialize.__name__)
    doc = prop.__doc__ or ''
    doc += "  Converts it using %s." % convert_name
    hget, hset = prop.fget, prop.fset
    def fget(r):
        return parse(hget(r))
    def fset(r, val):
        if val is not None:
            val = serialize(val)
        hset(r, val)
    return property(fget, fset, prop.fdel, doc)



def list_header(header, rfc_section):
    prop = header_getter(header, rfc_section)
    return converter(prop, parse_list, serialize_list, 'list')

def parse_list(value):
    if not value:
        return None
    return tuple(filter(None, [v.strip() for v in value.split(',')]))

def serialize_list(value):
    if isinstance(value, (text_type, bytes)):
        return str(value)
    else:
        return ', '.join(map(str, value))




def converter_date(prop):
    return converter(prop, parse_date, serialize_date, 'HTTP date')

def date_header(header, rfc_section):
    return converter_date(header_getter(header, rfc_section))









########################
## Converter functions
########################


_rx_etag = re.compile(r'(?:^|\s)(W/)?"((?:\\"|.)*?)"')

def parse_etag_response(value, strong=False):
    """
    Parse a response ETag.
    See:
        * http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.19
        * http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html#sec3.11
    """
    if not value:
        return None
    m = _rx_etag.match(value)
    if not m:
        # this etag is invalid, but we'll just return it anyway
        return value
    elif strong and m.group(1):
        # this is a weak etag and we want only strong ones
        return None
    else:
        return m.group(2).replace('\\"', '"')

def serialize_etag_response(value): #return '"%s"' % value.replace('"', '\\"')
    strong = True
    if isinstance(value, tuple):
        value, strong = value
    elif _rx_etag.match(value):
        # this is a valid etag already
        return value
    # let's quote the value
    r = '"%s"' % value.replace('"', '\\"')
    if not strong:
        r = 'W/' + r
    return r

def serialize_if_range(value):
    if isinstance(value, (datetime, date)):
        return serialize_date(value)
    value = str(value)
    return value or None

def parse_range(value):
    if not value:
        return None
    # Might return None too:
    return Range.parse(value)

def serialize_range(value):
    if not value:
        return None
    elif isinstance(value, (list, tuple)):
        return str(Range(*value))
    else:
        assert isinstance(value, str)
        return value

def parse_int(value):
    if value is None or value == '':
        return None
    return int(value)

def parse_int_safe(value):
    if value is None or value == '':
        return None
    try:
        return int(value)
    except ValueError:
        return None

serialize_int = str

def parse_content_range(value):
    if not value or not value.strip():
        return None
    # May still return None
    return ContentRange.parse(value)

def serialize_content_range(value):
    if isinstance(value, (tuple, list)):
        if len(value) not in (2, 3):
            raise ValueError(
                "When setting content_range to a list/tuple, it must "
                "be length 2 or 3 (not %r)" % value)
        if len(value) == 2:
            begin, end = value
            length = None
        else:
            begin, end, length = value
        value = ContentRange(begin, end, length)
    value = str(value).strip()
    if not value:
        return None
    return value




_rx_auth_param = re.compile(r'([a-z]+)=(".*?"|[^,]*)(?:\Z|, *)')

def parse_auth_params(params):
    r = {}
    for k, v in _rx_auth_param.findall(params):
        r[k] = v.strip('"')
    return r

# see http://lists.w3.org/Archives/Public/ietf-http-wg/2009OctDec/0297.html
known_auth_schemes = ['Basic', 'Digest', 'WSSE', 'HMACDigest', 'GoogleLogin',
                      'Cookie', 'OpenID']
known_auth_schemes = dict.fromkeys(known_auth_schemes, None)

def parse_auth(val):
    if val is not None:
        authtype, params = val.split(' ', 1)
        if authtype in known_auth_schemes:
            if authtype == 'Basic' and '"' not in params:
                # this is the "Authentication: Basic XXXXX==" case
                pass
            else:
                params = parse_auth_params(params)
        return authtype, params
    return val

def serialize_auth(val):
    if isinstance(val, (tuple, list)):
        authtype, params = val
        if isinstance(params, dict):
            params = ', '.join(map('%s="%s"'.__mod__, params.items()))
        assert isinstance(params, str)
        return '%s %s' % (authtype, params)
    return val

