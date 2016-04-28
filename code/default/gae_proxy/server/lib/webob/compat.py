# code stolen from "six"

import sys
import types

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3

if PY3: # pragma: no cover
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    long = int
else:
    string_types = basestring,
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    long = long

# TODO check if errors is ever used

def text_(s, encoding='latin-1', errors='strict'):
    if isinstance(s, bytes):
        return s.decode(encoding, errors)
    return s

def bytes_(s, encoding='latin-1', errors='strict'):
    if isinstance(s, text_type):
        return s.encode(encoding, errors)
    return s

if PY3: # pragma: no cover
    def native_(s, encoding='latin-1', errors='strict'):
        if isinstance(s, text_type):
            return s
        return str(s, encoding, errors)
else:
    def native_(s, encoding='latin-1', errors='strict'):
        if isinstance(s, text_type):
            return s.encode(encoding, errors)
        return str(s)

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

if PY3: # pragma: no cover
    from urllib import parse
    urlparse = parse
    from urllib.parse import quote as url_quote
    from urllib.parse import urlencode as url_encode, quote_plus
    from urllib.request import urlopen as url_open
else:
    import urlparse
    from urllib import quote_plus
    from urllib import quote as url_quote
    from urllib import unquote as url_unquote
    from urllib import urlencode as url_encode
    from urllib2 import urlopen as url_open

if PY3: # pragma: no cover
    def reraise(exc_info):
        etype, exc, tb = exc_info
        if exc.__traceback__ is not tb:
            raise exc.with_traceback(tb)
        raise exc
else: # pragma: no cover
    exec("def reraise(exc): raise exc[0], exc[1], exc[2]")


if PY3: # pragma: no cover
    def iteritems_(d):
        return d.items()
    def itervalues_(d):
        return d.values()
else:
    def iteritems_(d):
        return d.iteritems()
    def itervalues_(d):
        return d.itervalues()


if PY3: # pragma: no cover
    def unquote(string):
        if not string:
            return b''
        res = string.split(b'%')
        if len(res) != 1:
            string = res[0]
            for item in res[1:]:
                try:
                    string += bytes([int(item[:2], 16)]) + item[2:]
                except ValueError:
                    string += b'%' + item
        return string

    def url_unquote(s):
        return unquote(s.encode('ascii')).decode('latin-1')

    def parse_qsl_text(qs, encoding='utf-8'):
        qs = qs.encode('latin-1')
        qs = qs.replace(b'+', b' ')
        pairs = [s2 for s1 in qs.split(b'&') for s2 in s1.split(b';') if s2]
        for name_value in pairs:
            nv = name_value.split(b'=', 1)
            if len(nv) != 2:
                nv.append('')
            name = unquote(nv[0])
            value = unquote(nv[1])
            yield (name.decode(encoding), value.decode(encoding))

else:
    from urlparse import parse_qsl

    def parse_qsl_text(qs, encoding='utf-8'):
        qsl = parse_qsl(
            qs,
            keep_blank_values=True,
            strict_parsing=False
        )
        for (x, y) in qsl:
            yield (x.decode(encoding), y.decode(encoding))


if PY3: # pragma no cover
    from html import escape
else:
    from cgi import escape
