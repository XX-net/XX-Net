"""
Does parsing of ETag-related headers: If-None-Matches, If-Matches

Also If-Range parsing
"""

from webob.datetime_utils import (
    parse_date,
    serialize_date,
    )
from webob.descriptors import _rx_etag

from webob.util import (
    header_docstring,
    warn_deprecation,
    )

__all__ = ['AnyETag', 'NoETag', 'ETagMatcher', 'IfRange', 'etag_property']

def etag_property(key, default, rfc_section, strong=True):
    doc = header_docstring(key, rfc_section)
    doc += "  Converts it as a Etag."
    def fget(req):
        value = req.environ.get(key)
        if not value:
            return default
        else:
            return ETagMatcher.parse(value, strong=strong)
    def fset(req, val):
        if val is None:
            req.environ[key] = None
        else:
            req.environ[key] = str(val)
    def fdel(req):
        del req.environ[key]
    return property(fget, fset, fdel, doc=doc)

def _warn_weak_match_deprecated():
    warn_deprecation("weak_match is deprecated", '1.2', 3)

def _warn_if_range_match_deprecated(*args, **kw): # pragma: no cover
    raise DeprecationWarning("IfRange.match[_response] API is deprecated")


class _AnyETag(object):
    """
    Represents an ETag of *, or a missing ETag when matching is 'safe'
    """

    def __repr__(self):
        return '<ETag *>'

    def __nonzero__(self):
        return False

    __bool__ = __nonzero__ # python 3

    def __contains__(self, other):
        return True

    def weak_match(self, other):
        _warn_weak_match_deprecated()

    def __str__(self):
        return '*'

AnyETag = _AnyETag()

class _NoETag(object):
    """
    Represents a missing ETag when matching is unsafe
    """

    def __repr__(self):
        return '<No ETag>'

    def __nonzero__(self):
        return False

    __bool__ = __nonzero__ # python 3

    def __contains__(self, other):
        return False

    def weak_match(self, other): # pragma: no cover
        _warn_weak_match_deprecated()

    def __str__(self):
        return ''

NoETag = _NoETag()


# TODO: convert into a simple tuple

class ETagMatcher(object):
    def __init__(self, etags):
        self.etags = etags

    def __contains__(self, other):
        return other in self.etags

    def weak_match(self, other): # pragma: no cover
        _warn_weak_match_deprecated()

    def __repr__(self):
        return '<ETag %s>' % (' or '.join(self.etags))

    @classmethod
    def parse(cls, value, strong=True):
        """
        Parse this from a header value
        """
        if value == '*':
            return AnyETag
        if not value:
            return cls([])
        matches = _rx_etag.findall(value)
        if not matches:
            return cls([value])
        elif strong:
            return cls([t for w,t in matches if not w])
        else:
            return cls([t for w,t in matches])

    def __str__(self):
        return ', '.join(map('"%s"'.__mod__, self.etags))


class IfRange(object):
    def __init__(self, etag):
        self.etag = etag

    @classmethod
    def parse(cls, value):
        """
        Parse this from a header value.
        """
        if not value:
            return cls(AnyETag)
        elif value.endswith(' GMT'):
            # Must be a date
            return IfRangeDate(parse_date(value))
        else:
            return cls(ETagMatcher.parse(value))

    def __contains__(self, resp):
        """
        Return True if the If-Range header matches the given etag or last_modified
        """
        return resp.etag_strong in self.etag

    def __nonzero__(self):
        return bool(self.etag)

    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            self.etag
        )

    def __str__(self):
        return str(self.etag) if self.etag else ''

    match = match_response = _warn_if_range_match_deprecated

    __bool__ = __nonzero__ # python 3

class IfRangeDate(object):
    def __init__(self, date):
        self.date = date

    def __contains__(self, resp):
        last_modified = resp.last_modified
        #if isinstance(last_modified, str):
        #    last_modified = parse_date(last_modified)
        return last_modified and (last_modified <= self.date)

    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            self.date
            #serialize_date(self.date)
        )

    def __str__(self):
        return serialize_date(self.date)

    match = match_response = _warn_if_range_match_deprecated
