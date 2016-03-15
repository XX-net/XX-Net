"""
Represents the Cache-Control header
"""
import re

class UpdateDict(dict):
    """
    Dict that has a callback on all updates
    """
    # these are declared as class attributes so that
    # we don't need to override constructor just to
    # set some defaults
    updated = None
    updated_args = None

    def _updated(self):
        """
        Assign to new_dict.updated to track updates
        """
        updated = self.updated
        if updated is not None:
            args = self.updated_args
            if args is None:
                args = (self,)
            updated(*args)

    def __setitem__(self, key, item):
        dict.__setitem__(self, key, item)
        self._updated()

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._updated()

    def clear(self):
        dict.clear(self)
        self._updated()

    def update(self, *args, **kw):
        dict.update(self, *args, **kw)
        self._updated()

    def setdefault(self, key, value=None):
        val = dict.setdefault(self, key, value)
        if val is value:
            self._updated()
        return val

    def pop(self, *args):
        v = dict.pop(self, *args)
        self._updated()
        return v

    def popitem(self):
        v = dict.popitem(self)
        self._updated()
        return v


token_re = re.compile(
    r'([a-zA-Z][a-zA-Z_-]*)\s*(?:=(?:"([^"]*)"|([^ \t",;]*)))?')
need_quote_re = re.compile(r'[^a-zA-Z0-9._-]')


class exists_property(object):
    """
    Represents a property that either is listed in the Cache-Control
    header, or is not listed (has no value)
    """
    def __init__(self, prop, type=None):
        self.prop = prop
        self.type = type

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return self.prop in obj.properties

    def __set__(self, obj, value):
        if (self.type is not None
            and self.type != obj.type):
            raise AttributeError(
                "The property %s only applies to %s Cache-Control" % (
                    self.prop, self.type))

        if value:
            obj.properties[self.prop] = None
        else:
            if self.prop in obj.properties:
                del obj.properties[self.prop]

    def __delete__(self, obj):
        self.__set__(obj, False)


class value_property(object):
    """
    Represents a property that has a value in the Cache-Control header.

    When no value is actually given, the value of self.none is returned.
    """
    def __init__(self, prop, default=None, none=None, type=None):
        self.prop = prop
        self.default = default
        self.none = none
        self.type = type

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        if self.prop in obj.properties:
            value = obj.properties[self.prop]
            if value is None:
                return self.none
            else:
                return value
        else:
            return self.default

    def __set__(self, obj, value):
        if (self.type is not None
            and self.type != obj.type):
            raise AttributeError(
                "The property %s only applies to %s Cache-Control" % (
                    self.prop, self.type))
        if value == self.default:
            if self.prop in obj.properties:
                del obj.properties[self.prop]
        elif value is True:
            obj.properties[self.prop] = None # Empty value, but present
        else:
            obj.properties[self.prop] = value

    def __delete__(self, obj):
        if self.prop in obj.properties:
            del obj.properties[self.prop]


class CacheControl(object):

    """
    Represents the Cache-Control header.

    By giving a type of ``'request'`` or ``'response'`` you can
    control what attributes are allowed (some Cache-Control values
    only apply to requests or responses).
    """

    update_dict = UpdateDict

    def __init__(self, properties, type):
        self.properties = properties
        self.type = type

    @classmethod
    def parse(cls, header, updates_to=None, type=None):
        """
        Parse the header, returning a CacheControl object.

        The object is bound to the request or response object
        ``updates_to``, if that is given.
        """
        if updates_to:
            props = cls.update_dict()
            props.updated = updates_to
        else:
            props = {}
        for match in token_re.finditer(header):
            name = match.group(1)
            value = match.group(2) or match.group(3) or None
            if value:
                try:
                    value = int(value)
                except ValueError:
                    pass
            props[name] = value
        obj = cls(props, type=type)
        if updates_to:
            props.updated_args = (obj,)
        return obj

    def __repr__(self):
        return '<CacheControl %r>' % str(self)

    # Request values:
    # no-cache shared (below)
    # no-store shared (below)
    # max-age shared  (below)
    max_stale = value_property('max-stale', none='*', type='request')
    min_fresh = value_property('min-fresh', type='request')
    # no-transform shared (below)
    only_if_cached = exists_property('only-if-cached', type='request')

    # Response values:
    public = exists_property('public', type='response')
    private = value_property('private', none='*', type='response')
    no_cache = value_property('no-cache', none='*')
    no_store = exists_property('no-store')
    no_transform = exists_property('no-transform')
    must_revalidate = exists_property('must-revalidate', type='response')
    proxy_revalidate = exists_property('proxy-revalidate', type='response')
    max_age = value_property('max-age', none=-1)
    s_maxage = value_property('s-maxage', type='response')
    s_max_age = s_maxage
    stale_while_revalidate = value_property(
        'stale-while-revalidate', type='response')
    stale_if_error = value_property('stale-if-error', type='response')

    def __str__(self):
        return serialize_cache_control(self.properties)

    def copy(self):
        """
        Returns a copy of this object.
        """
        return self.__class__(self.properties.copy(), type=self.type)


def serialize_cache_control(properties):
    if isinstance(properties, CacheControl):
        properties = properties.properties
    parts = []
    for name, value in sorted(properties.items()):
        if value is None:
            parts.append(name)
            continue
        value = str(value)
        if need_quote_re.search(value):
            value = '"%s"' % value
        parts.append('%s=%s' % (name, value))
    return ', '.join(parts)
