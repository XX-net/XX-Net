from base64 import b64encode
from datetime import (
    datetime,
    timedelta,
    )
from hashlib import md5
import re
import struct
import zlib
try:
    import simplejson as json
except ImportError:
    import json

from webob.byterange import ContentRange

from webob.cachecontrol import (
    CacheControl,
    serialize_cache_control,
    )

from webob.compat import (
    PY3,
    bytes_,
    native_,
    text_type,
    url_quote,
    urlparse,
    )

from webob.cookies import (
    Cookie,
    Morsel,
    )

from webob.datetime_utils import (
    parse_date_delta,
    serialize_date_delta,
    timedelta_to_seconds,
    )

from webob.descriptors import (
    CHARSET_RE,
    SCHEME_RE,
    converter,
    date_header,
    header_getter,
    list_header,
    parse_auth,
    parse_content_range,
    parse_etag_response,
    parse_int,
    parse_int_safe,
    serialize_auth,
    serialize_content_range,
    serialize_etag_response,
    serialize_int,
    )

from webob.headers import ResponseHeaders
from webob.request import BaseRequest
from webob.util import status_reasons, status_generic_reasons

__all__ = ['Response']

_PARAM_RE = re.compile(r'([a-z0-9]+)=(?:"([^"]*)"|([a-z0-9_.-]*))', re.I)
_OK_PARAM_RE = re.compile(r'^[a-z0-9_.-]+$', re.I)

_gzip_header = b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff'

class Response(object):
    """
        Represents a WSGI response
    """

    default_content_type = 'text/html'
    default_charset = 'UTF-8' # TODO: deprecate
    unicode_errors = 'strict' # TODO: deprecate (why would response body have errors?)
    default_conditional_response = False
    request = None
    environ = None

    #
    # __init__, from_file, copy
    #

    def __init__(self, body=None, status=None, headerlist=None, app_iter=None,
                 content_type=None, conditional_response=None,
                 **kw):
        if app_iter is None and body is None and ('json_body' in kw or 'json' in kw):
            if 'json_body' in kw:
                json_body = kw.pop('json_body')
            else:
                json_body = kw.pop('json')
            body = json.dumps(json_body, separators=(',', ':'))
            if content_type is None:
                content_type = 'application/json'
        if app_iter is None:
            if body is None:
                body = b''
        elif body is not None:
            raise TypeError(
                "You may only give one of the body and app_iter arguments")
        if status is None:
            self._status = '200 OK'
        else:
            self.status = status
        if headerlist is None:
            self._headerlist = []
        else:
            self._headerlist = headerlist
        self._headers = None
        if content_type is None:
            content_type = self.default_content_type
        charset = None
        if 'charset' in kw:
            charset = kw.pop('charset')
        elif self.default_charset:
            if (content_type
                and 'charset=' not in content_type
                and (content_type == 'text/html'
                    or content_type.startswith('text/')
                    or content_type.startswith('application/xml')
                    or content_type.startswith('application/json')
                    or (content_type.startswith('application/')
                         and (content_type.endswith('+xml') or content_type.endswith('+json'))))):
                charset = self.default_charset
        if content_type and charset:
            content_type += '; charset=' + charset
        elif self._headerlist and charset:
            self.charset = charset
        if not self._headerlist and content_type:
            self._headerlist.append(('Content-Type', content_type))
        if conditional_response is None:
            self.conditional_response = self.default_conditional_response
        else:
            self.conditional_response = bool(conditional_response)
        if app_iter is None:
            if isinstance(body, text_type):
                if charset is None:
                    raise TypeError(
                        "You cannot set the body to a text value without a "
                        "charset")
                body = body.encode(charset)
            app_iter = [body]
            if headerlist is None:
                self._headerlist.append(('Content-Length', str(len(body))))
            else:
                self.headers['Content-Length'] = str(len(body))
        self._app_iter = app_iter
        for name, value in kw.items():
            if not hasattr(self.__class__, name):
                # Not a basic attribute
                raise TypeError(
                    "Unexpected keyword: %s=%r" % (name, value))
            setattr(self, name, value)


    @classmethod
    def from_file(cls, fp):
        """Reads a response from a file-like object (it must implement
        ``.read(size)`` and ``.readline()``).

        It will read up to the end of the response, not the end of the
        file.

        This reads the response as represented by ``str(resp)``; it
        may not read every valid HTTP response properly.  Responses
        must have a ``Content-Length``"""
        headerlist = []
        status = fp.readline().strip()
        is_text = isinstance(status, text_type)
        if is_text:
            _colon = ':'
        else:
            _colon = b':'
        while 1:
            line = fp.readline().strip()
            if not line:
                # end of headers
                break
            try:
                header_name, value = line.split(_colon, 1)
            except ValueError:
                raise ValueError('Bad header line: %r' % line)
            value = value.strip()
            if not is_text:
                header_name = header_name.decode('utf-8')
                value = value.decode('utf-8')
            headerlist.append((header_name, value))
        r = cls(
            status=status,
            headerlist=headerlist,
            app_iter=(),
        )
        body = fp.read(r.content_length or 0)
        if is_text:
            r.text = body
        else:
            r.body = body
        return r

    def copy(self):
        """Makes a copy of the response"""
        # we need to do this for app_iter to be reusable
        app_iter = list(self._app_iter)
        iter_close(self._app_iter)
        # and this to make sure app_iter instances are different
        self._app_iter = list(app_iter)
        return self.__class__(
            content_type=False,
            status=self._status,
            headerlist=self._headerlist[:],
            app_iter=app_iter,
            conditional_response=self.conditional_response)


    #
    # __repr__, __str__
    #

    def __repr__(self):
        return '<%s at 0x%x %s>' % (self.__class__.__name__, abs(id(self)),
                                    self.status)

    def __str__(self, skip_body=False):
        parts = [self.status]
        if not skip_body:
            # Force enumeration of the body (to set content-length)
            self.body
        parts += map('%s: %s'.__mod__, self.headerlist)
        if not skip_body and self.body:
            parts += ['', self.text if PY3 else self.body]
        return '\n'.join(parts)

    #
    # status, status_code/status_int
    #

    def _status__get(self):
        """
        The status string
        """
        return self._status

    def _status__set(self, value):
        if isinstance(value, int):
            self.status_code = value
            return
        if PY3: # pragma: no cover
            if isinstance(value, bytes):
                value = value.decode('ascii')
        elif isinstance(value, text_type):
            value = value.encode('ascii')
        if not isinstance(value, str):
            raise TypeError(
                "You must set status to a string or integer (not %s)"
                % type(value))
        if ' ' not in value:
             try:
                value += ' ' + status_reasons[int(value)]
             except KeyError:
                value += ' ' + status_generic_reasons[int(value) // 100]
        self._status = value

    status = property(_status__get, _status__set, doc=_status__get.__doc__)

    def _status_code__get(self):
        """
        The status as an integer
        """
        return int(self._status.split()[0])

    def _status_code__set(self, code):
        try:
            self._status = '%d %s' % (code, status_reasons[code])
        except KeyError:
            self._status = '%d %s' % (code, status_generic_reasons[code // 100])

    status_code = status_int = property(_status_code__get, _status_code__set,
                           doc=_status_code__get.__doc__)


    #
    # headerslist, headers
    #

    def _headerlist__get(self):
        """
        The list of response headers
        """
        return self._headerlist

    def _headerlist__set(self, value):
        self._headers = None
        if not isinstance(value, list):
            if hasattr(value, 'items'):
                value = value.items()
            value = list(value)
        self._headerlist = value

    def _headerlist__del(self):
        self.headerlist = []

    headerlist = property(_headerlist__get, _headerlist__set,
                          _headerlist__del, doc=_headerlist__get.__doc__)

    def _headers__get(self):
        """
        The headers in a dictionary-like object
        """
        if self._headers is None:
            self._headers = ResponseHeaders.view_list(self.headerlist)
        return self._headers

    def _headers__set(self, value):
        if hasattr(value, 'items'):
            value = value.items()
        self.headerlist = value
        self._headers = None

    headers = property(_headers__get, _headers__set, doc=_headers__get.__doc__)


    #
    # body
    #

    def _body__get(self):
        """
        The body of the response, as a ``str``.  This will read in the
        entire app_iter if necessary.
        """
        app_iter = self._app_iter
#         try:
#             if len(app_iter) == 1:
#                 return app_iter[0]
#         except:
#             pass
        if isinstance(app_iter, list) and len(app_iter) == 1:
            return app_iter[0]
        if app_iter is None:
            raise AttributeError("No body has been set")
        try:
            body = b''.join(app_iter)
        finally:
            iter_close(app_iter)
        if isinstance(body, text_type):
            raise _error_unicode_in_app_iter(app_iter, body)
        self._app_iter = [body]
        if len(body) == 0:
            # if body-length is zero, we assume it's a HEAD response and
            # leave content_length alone
            pass # pragma: no cover (no idea why necessary, it's hit)
        elif self.content_length is None:
            self.content_length = len(body)
        elif self.content_length != len(body):
            raise AssertionError(
                "Content-Length is different from actual app_iter length "
                "(%r!=%r)"
                % (self.content_length, len(body))
            )
        return body

    def _body__set(self, value=b''):
        if not isinstance(value, bytes):
            if isinstance(value, text_type):
                msg = ("You cannot set Response.body to a text object "
                       "(use Response.text)")
            else:
                msg = ("You can only set the body to a binary type (not %s)" %
                       type(value))
            raise TypeError(msg)
        if self._app_iter is not None:
            self.content_md5 = None
        self._app_iter = [value]
        self.content_length = len(value)

#     def _body__del(self):
#         self.body = ''
#         #self.content_length = None

    body = property(_body__get, _body__set, _body__set)

    def _json_body__get(self):
        """Access the body of the response as JSON"""
        # Note: UTF-8 is a content-type specific default for JSON:
        return json.loads(self.body.decode(self.charset or 'UTF-8'))

    def _json_body__set(self, value):
        self.body = json.dumps(value, separators=(',', ':')).encode(self.charset or 'UTF-8')

    def _json_body__del(self):
        del self.body

    json = json_body = property(_json_body__get, _json_body__set, _json_body__del)


    #
    # text, unicode_body, ubody
    #

    def _text__get(self):
        """
        Get/set the text value of the body (using the charset of the
        Content-Type)
        """
        if not self.charset:
            raise AttributeError(
                "You cannot access Response.text unless charset is set")
        body = self.body
        return body.decode(self.charset, self.unicode_errors)

    def _text__set(self, value):
        if not self.charset:
            raise AttributeError(
                "You cannot access Response.text unless charset is set")
        if not isinstance(value, text_type):
            raise TypeError(
                "You can only set Response.text to a unicode string "
                "(not %s)" % type(value))
        self.body = value.encode(self.charset)

    def _text__del(self):
        del self.body

    text = property(_text__get, _text__set, _text__del, doc=_text__get.__doc__)

    unicode_body = ubody = property(_text__get, _text__set, _text__del,
        "Deprecated alias for .text")

    #
    # body_file, write(text)
    #

    def _body_file__get(self):
        """
        A file-like object that can be used to write to the
        body.  If you passed in a list app_iter, that app_iter will be
        modified by writes.
        """
        return ResponseBodyFile(self)

    def _body_file__set(self, file):
        self.app_iter = iter_file(file)

    def _body_file__del(self):
        del self.body

    body_file = property(_body_file__get, _body_file__set, _body_file__del,
                         doc=_body_file__get.__doc__)

    def write(self, text):
        if not isinstance(text, bytes):
            if not isinstance(text, text_type):
                msg = "You can only write str to a Response.body_file, not %s"
                raise TypeError(msg % type(text))
            if not self.charset:
                msg = ("You can only write text to Response if charset has "
                       "been set")
                raise TypeError(msg)
            text = text.encode(self.charset)
        app_iter = self._app_iter
        if not isinstance(app_iter, list):
            try:
                new_app_iter = self._app_iter = list(app_iter)
            finally:
                iter_close(app_iter)
            app_iter = new_app_iter
            self.content_length = sum(len(chunk) for chunk in app_iter)
        app_iter.append(text)
        if self.content_length is not None:
            self.content_length += len(text)



    #
    # app_iter
    #

    def _app_iter__get(self):
        """
        Returns the app_iter of the response.

        If body was set, this will create an app_iter from that body
        (a single-item list)
        """
        return self._app_iter

    def _app_iter__set(self, value):
        if self._app_iter is not None:
            # Undo the automatically-set content-length
            self.content_length = None
            self.content_md5 = None
        self._app_iter = value

    def _app_iter__del(self):
        self._app_iter = []
        self.content_length = None

    app_iter = property(_app_iter__get, _app_iter__set, _app_iter__del,
                        doc=_app_iter__get.__doc__)



    #
    # headers attrs
    #

    allow = list_header('Allow', '14.7')
    # TODO: (maybe) support response.vary += 'something'
    # TODO: same thing for all listy headers
    vary = list_header('Vary', '14.44')

    content_length = converter(
        header_getter('Content-Length', '14.17'),
        parse_int, serialize_int, 'int')

    content_encoding = header_getter('Content-Encoding', '14.11')
    content_language = list_header('Content-Language', '14.12')
    content_location = header_getter('Content-Location', '14.14')
    content_md5 = header_getter('Content-MD5', '14.14')
    content_disposition = header_getter('Content-Disposition', '19.5.1')

    accept_ranges = header_getter('Accept-Ranges', '14.5')
    content_range = converter(
        header_getter('Content-Range', '14.16'),
        parse_content_range, serialize_content_range, 'ContentRange object')

    date = date_header('Date', '14.18')
    expires = date_header('Expires', '14.21')
    last_modified = date_header('Last-Modified', '14.29')

    _etag_raw = header_getter('ETag', '14.19')
    etag = converter(_etag_raw,
        parse_etag_response, serialize_etag_response,
        'Entity tag'
    )
    @property
    def etag_strong(self):
        return parse_etag_response(self._etag_raw, strong=True)

    location = header_getter('Location', '14.30')
    pragma = header_getter('Pragma', '14.32')
    age = converter(
        header_getter('Age', '14.6'),
        parse_int_safe, serialize_int, 'int')

    retry_after = converter(
        header_getter('Retry-After', '14.37'),
        parse_date_delta, serialize_date_delta, 'HTTP date or delta seconds')

    server = header_getter('Server', '14.38')

    # TODO: the standard allows this to be a list of challenges
    www_authenticate = converter(
        header_getter('WWW-Authenticate', '14.47'),
        parse_auth, serialize_auth,
    )


    #
    # charset
    #

    def _charset__get(self):
        """
        Get/set the charset (in the Content-Type)
        """
        header = self.headers.get('Content-Type')
        if not header:
            return None
        match = CHARSET_RE.search(header)
        if match:
            return match.group(1)
        return None

    def _charset__set(self, charset):
        if charset is None:
            del self.charset
            return
        header = self.headers.pop('Content-Type', None)
        if header is None:
            raise AttributeError("You cannot set the charset when no "
                                 "content-type is defined")
        match = CHARSET_RE.search(header)
        if match:
            header = header[:match.start()] + header[match.end():]
        header += '; charset=%s' % charset
        self.headers['Content-Type'] = header

    def _charset__del(self):
        header = self.headers.pop('Content-Type', None)
        if header is None:
            # Don't need to remove anything
            return
        match = CHARSET_RE.search(header)
        if match:
            header = header[:match.start()] + header[match.end():]
        self.headers['Content-Type'] = header

    charset = property(_charset__get, _charset__set, _charset__del,
                       doc=_charset__get.__doc__)


    #
    # content_type
    #

    def _content_type__get(self):
        """
        Get/set the Content-Type header (or None), *without* the
        charset or any parameters.

        If you include parameters (or ``;`` at all) when setting the
        content_type, any existing parameters will be deleted;
        otherwise they will be preserved.
        """
        header = self.headers.get('Content-Type')
        if not header:
            return None
        return header.split(';', 1)[0]

    def _content_type__set(self, value):
        if not value:
            self._content_type__del()
            return
        if ';' not in value:
            header = self.headers.get('Content-Type', '')
            if ';' in header:
                params = header.split(';', 1)[1]
                value += ';' + params
        self.headers['Content-Type'] = value

    def _content_type__del(self):
        self.headers.pop('Content-Type', None)

    content_type = property(_content_type__get, _content_type__set,
                            _content_type__del, doc=_content_type__get.__doc__)


    #
    # content_type_params
    #

    def _content_type_params__get(self):
        """
        A dictionary of all the parameters in the content type.

        (This is not a view, set to change, modifications of the dict would not
        be applied otherwise)
        """
        params = self.headers.get('Content-Type', '')
        if ';' not in params:
            return {}
        params = params.split(';', 1)[1]
        result = {}
        for match in _PARAM_RE.finditer(params):
            result[match.group(1)] = match.group(2) or match.group(3) or ''
        return result

    def _content_type_params__set(self, value_dict):
        if not value_dict:
            del self.content_type_params
            return
        params = []
        for k, v in sorted(value_dict.items()):
            if not _OK_PARAM_RE.search(v):
                v = '"%s"' % v.replace('"', '\\"')
            params.append('; %s=%s' % (k, v))
        ct = self.headers.pop('Content-Type', '').split(';', 1)[0]
        ct += ''.join(params)
        self.headers['Content-Type'] = ct

    def _content_type_params__del(self):
        self.headers['Content-Type'] = self.headers.get(
            'Content-Type', '').split(';', 1)[0]

    content_type_params = property(
        _content_type_params__get,
        _content_type_params__set,
        _content_type_params__del,
        _content_type_params__get.__doc__
    )




    #
    # set_cookie, unset_cookie, delete_cookie, merge_cookies
    #

    def set_cookie(self, key, value='', max_age=None,
                   path='/', domain=None, secure=False, httponly=False,
                   comment=None, expires=None, overwrite=False):
        """
        Set (add) a cookie for the response.

        Arguments are:

        ``key``

           The cookie name.

        ``value``

           The cookie value, which should be a string or ``None``.  If
           ``value`` is ``None``, it's equivalent to calling the
           :meth:`webob.response.Response.unset_cookie` method for this
           cookie key (it effectively deletes the cookie on the client).

        ``max_age``

           An integer representing a number of seconds or ``None``.  If this
           value is an integer, it is used as the ``Max-Age`` of the
           generated cookie.  If ``expires`` is not passed and this value is
           an integer, the ``max_age`` value will also influence the
           ``Expires`` value of the cookie (``Expires`` will be set to now +
           max_age).  If this value is ``None``, the cookie will not have a
           ``Max-Age`` value (unless ``expires`` is also sent).

        ``path``

           A string representing the cookie ``Path`` value.  It defaults to
           ``/``.

        ``domain``

           A string representing the cookie ``Domain``, or ``None``.  If
           domain is ``None``, no ``Domain`` value will be sent in the
           cookie.

        ``secure``

           A boolean.  If it's ``True``, the ``secure`` flag will be sent in
           the cookie, if it's ``False``, the ``secure`` flag will not be
           sent in the cookie.

        ``httponly``

           A boolean.  If it's ``True``, the ``HttpOnly`` flag will be sent
           in the cookie, if it's ``False``, the ``HttpOnly`` flag will not
           be sent in the cookie.

        ``comment``

           A string representing the cookie ``Comment`` value, or ``None``.
           If ``comment`` is ``None``, no ``Comment`` value will be sent in
           the cookie.

        ``expires``

           A ``datetime.timedelta`` object representing an amount of time or
           the value ``None``.  A non-``None`` value is used to generate the
           ``Expires`` value of the generated cookie.  If ``max_age`` is not
           passed, but this value is not ``None``, it will influence the
           ``Max-Age`` header (``Max-Age`` will be 'expires_value -
           datetime.utcnow()').  If this value is ``None``, the ``Expires``
           cookie value will be unset (unless ``max_age`` is also passed).

        ``overwrite``

           If this key is ``True``, before setting the cookie, unset any
           existing cookie.

        """
        if overwrite:
            self.unset_cookie(key, strict=False)
        if value is None: # delete the cookie from the client
            value = ''
            max_age = 0
            expires = timedelta(days=-5)
        elif expires is None and max_age is not None:
            if isinstance(max_age, int):
                max_age = timedelta(seconds=max_age)
            expires = datetime.utcnow() + max_age
        elif max_age is None and expires is not None:
            max_age = expires - datetime.utcnow()
        value = bytes_(value, 'utf8')
        key = bytes_(key, 'utf8')
        m = Morsel(key, value)
        m.path = bytes_(path, 'utf8')
        m.domain = bytes_(domain, 'utf8')
        m.comment = bytes_(comment, 'utf8')
        m.expires = expires
        m.max_age = max_age
        m.secure = secure
        m.httponly = httponly
        self.headerlist.append(('Set-Cookie', m.serialize()))

    def delete_cookie(self, key, path='/', domain=None):
        """
        Delete a cookie from the client.  Note that path and domain must match
        how the cookie was originally set.

        This sets the cookie to the empty string, and max_age=0 so
        that it should expire immediately.
        """
        self.set_cookie(key, None, path=path, domain=domain)

    def unset_cookie(self, key, strict=True):
        """
        Unset a cookie with the given name (remove it from the
        response).
        """
        existing = self.headers.getall('Set-Cookie')
        if not existing and not strict:
            return
        cookies = Cookie()
        for header in existing:
            cookies.load(header)
        if isinstance(key, text_type):
            key = key.encode('utf8')
        if key in cookies:
            del cookies[key]
            del self.headers['Set-Cookie']
            for m in cookies.values():
                self.headerlist.append(('Set-Cookie', m.serialize()))
        elif strict:
            raise KeyError("No cookie has been set with the name %r" % key)


    def merge_cookies(self, resp):
        """Merge the cookies that were set on this response with the
        given `resp` object (which can be any WSGI application).

        If the `resp` is a :class:`webob.Response` object, then the
        other object will be modified in-place.
        """
        if not self.headers.get('Set-Cookie'):
            return resp
        if isinstance(resp, Response):
            for header in self.headers.getall('Set-Cookie'):
                resp.headers.add('Set-Cookie', header)
            return resp
        else:
            c_headers = [h for h in self.headerlist if
                         h[0].lower() == 'set-cookie']
            def repl_app(environ, start_response):
                def repl_start_response(status, headers, exc_info=None):
                    return start_response(status, headers+c_headers,
                                          exc_info=exc_info)
                return resp(environ, repl_start_response)
            return repl_app


    #
    # cache_control
    #

    _cache_control_obj = None

    def _cache_control__get(self):
        """
        Get/set/modify the Cache-Control header (`HTTP spec section 14.9
        <http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.9>`_)
        """
        value = self.headers.get('cache-control', '')
        if self._cache_control_obj is None:
            self._cache_control_obj = CacheControl.parse(
                value, updates_to=self._update_cache_control, type='response')
            self._cache_control_obj.header_value = value
        if self._cache_control_obj.header_value != value:
            new_obj = CacheControl.parse(value, type='response')
            self._cache_control_obj.properties.clear()
            self._cache_control_obj.properties.update(new_obj.properties)
            self._cache_control_obj.header_value = value
        return self._cache_control_obj

    def _cache_control__set(self, value):
        # This actually becomes a copy
        if not value:
            value = ""
        if isinstance(value, dict):
            value = CacheControl(value, 'response')
        if isinstance(value, text_type):
            value = str(value)
        if isinstance(value, str):
            if self._cache_control_obj is None:
                self.headers['Cache-Control'] = value
                return
            value = CacheControl.parse(value, 'response')
        cache = self.cache_control
        cache.properties.clear()
        cache.properties.update(value.properties)

    def _cache_control__del(self):
        self.cache_control = {}

    def _update_cache_control(self, prop_dict):
        value = serialize_cache_control(prop_dict)
        if not value:
            if 'Cache-Control' in self.headers:
                del self.headers['Cache-Control']
        else:
            self.headers['Cache-Control'] = value

    cache_control = property(
        _cache_control__get, _cache_control__set,
        _cache_control__del, doc=_cache_control__get.__doc__)


    #
    # cache_expires
    #

    def _cache_expires(self, seconds=0, **kw):
        """
            Set expiration on this request.  This sets the response to
            expire in the given seconds, and any other attributes are used
            for cache_control (e.g., private=True, etc).
        """
        if seconds is True:
            seconds = 0
        elif isinstance(seconds, timedelta):
            seconds = timedelta_to_seconds(seconds)
        cache_control = self.cache_control
        if seconds is None:
            pass
        elif not seconds:
            # To really expire something, you have to force a
            # bunch of these cache control attributes, and IE may
            # not pay attention to those still so we also set
            # Expires.
            cache_control.no_store = True
            cache_control.no_cache = True
            cache_control.must_revalidate = True
            cache_control.max_age = 0
            cache_control.post_check = 0
            cache_control.pre_check = 0
            self.expires = datetime.utcnow()
            if 'last-modified' not in self.headers:
                self.last_modified = datetime.utcnow()
            self.pragma = 'no-cache'
        else:
            cache_control.properties.clear()
            cache_control.max_age = seconds
            self.expires = datetime.utcnow() + timedelta(seconds=seconds)
            self.pragma = None
        for name, value in kw.items():
            setattr(cache_control, name, value)

    cache_expires = property(lambda self: self._cache_expires, _cache_expires)



    #
    # encode_content, decode_content, md5_etag
    #

    def encode_content(self, encoding='gzip', lazy=False):
        """
        Encode the content with the given encoding (only gzip and
        identity are supported).
        """
        assert encoding in ('identity', 'gzip'), \
               "Unknown encoding: %r" % encoding
        if encoding == 'identity':
            self.decode_content()
            return
        if self.content_encoding == 'gzip':
            return
        if lazy:
            self.app_iter = gzip_app_iter(self._app_iter)
            self.content_length = None
        else:
            self.app_iter = list(gzip_app_iter(self._app_iter))
            self.content_length = sum(map(len, self._app_iter))
        self.content_encoding = 'gzip'

    def decode_content(self):
        content_encoding = self.content_encoding or 'identity'
        if content_encoding == 'identity':
            return
        if content_encoding not in ('gzip', 'deflate'):
            raise ValueError(
                "I don't know how to decode the content %s" % content_encoding)
        if content_encoding == 'gzip':
            from gzip import GzipFile
            from io import BytesIO
            gzip_f = GzipFile(filename='', mode='r', fileobj=BytesIO(self.body))
            self.body = gzip_f.read()
            self.content_encoding = None
            gzip_f.close()
        else:
            # Weird feature: http://bugs.python.org/issue5784
            self.body = zlib.decompress(self.body, -15)
            self.content_encoding = None

    def md5_etag(self, body=None, set_content_md5=False):
        """
        Generate an etag for the response object using an MD5 hash of
        the body (the body parameter, or ``self.body`` if not given)

        Sets ``self.etag``
        If ``set_content_md5`` is True sets ``self.content_md5`` as well
        """
        if body is None:
            body = self.body
        md5_digest = md5(body).digest()
        md5_digest = b64encode(md5_digest)
        md5_digest = md5_digest.replace(b'\n', b'')
        md5_digest = native_(md5_digest)
        self.etag = md5_digest.strip('=')
        if set_content_md5:
            self.content_md5 = md5_digest



    #
    # __call__, conditional_response_app
    #

    def __call__(self, environ, start_response):
        """
        WSGI application interface
        """
        if self.conditional_response:
            return self.conditional_response_app(environ, start_response)
        headerlist = self._abs_headerlist(environ)
        start_response(self.status, headerlist)
        if environ['REQUEST_METHOD'] == 'HEAD':
            # Special case here...
            return EmptyResponse(self._app_iter)
        return self._app_iter

    def _abs_headerlist(self, environ):
        """Returns a headerlist, with the Location header possibly
        made absolute given the request environ.
        """
        headerlist = list(self.headerlist)
        for i, (name, value) in enumerate(headerlist):
            if name.lower() == 'location':
                if SCHEME_RE.search(value):
                    break
                new_location = urlparse.urljoin(_request_uri(environ), value)
                headerlist[i] = (name, new_location)
                break
        return headerlist

    _safe_methods = ('GET', 'HEAD')

    def conditional_response_app(self, environ, start_response):
        """
        Like the normal __call__ interface, but checks conditional headers:

        * If-Modified-Since   (304 Not Modified; only on GET, HEAD)
        * If-None-Match       (304 Not Modified; only on GET, HEAD)
        * Range               (406 Partial Content; only on GET, HEAD)
        """
        req = BaseRequest(environ)
        headerlist = self._abs_headerlist(environ)
        method = environ.get('REQUEST_METHOD', 'GET')
        if method in self._safe_methods:
            status304 = False
            if req.if_none_match and self.etag:
                status304 = self.etag in req.if_none_match
            elif req.if_modified_since and self.last_modified:
                status304 = self.last_modified <= req.if_modified_since
            if status304:
                start_response('304 Not Modified', filter_headers(headerlist))
                return EmptyResponse(self._app_iter)
        if (req.range and self in req.if_range
            and self.content_range is None
            and method in ('HEAD', 'GET')
            and self.status_code == 200
            and self.content_length is not None
        ):
            content_range = req.range.content_range(self.content_length)
            if content_range is None:
                iter_close(self._app_iter)
                body = bytes_("Requested range not satisfiable: %s" % req.range)
                headerlist = [
                    ('Content-Length', str(len(body))),
                    ('Content-Range', str(ContentRange(None, None,
                                                       self.content_length))),
                    ('Content-Type', 'text/plain'),
                ] + filter_headers(headerlist)
                start_response('416 Requested Range Not Satisfiable',
                               headerlist)
                if method == 'HEAD':
                    return ()
                return [body]
            else:
                app_iter = self.app_iter_range(content_range.start,
                                               content_range.stop)
                if app_iter is not None:
                    # the following should be guaranteed by
                    # Range.range_for_length(length)
                    assert content_range.start is not None
                    headerlist = [
                        ('Content-Length',
                         str(content_range.stop - content_range.start)),
                        ('Content-Range', str(content_range)),
                    ] + filter_headers(headerlist, ('content-length',))
                    start_response('206 Partial Content', headerlist)
                    if method == 'HEAD':
                        return EmptyResponse(app_iter)
                    return app_iter

        start_response(self.status, headerlist)
        if method  == 'HEAD':
            return EmptyResponse(self._app_iter)
        return self._app_iter

    def app_iter_range(self, start, stop):
        """
        Return a new app_iter built from the response app_iter, that
        serves up only the given ``start:stop`` range.
        """
        app_iter = self._app_iter
        if hasattr(app_iter, 'app_iter_range'):
            return app_iter.app_iter_range(start, stop)
        return AppIterRange(app_iter, start, stop)


def filter_headers(hlist, remove_headers=('content-length', 'content-type')):
    return [h for h in hlist if (h[0].lower() not in remove_headers)]


def iter_file(file, block_size=1<<18): # 256Kb
    while True:
        data = file.read(block_size)
        if not data:
            break
        yield data

class ResponseBodyFile(object):
    mode = 'wb'
    closed = False

    def __init__(self, response):
        self.response = response
        self.write = response.write

    def __repr__(self):
        return '<body_file for %r>' % self.response

    encoding = property(
        lambda self: self.response.charset,
        doc="The encoding of the file (inherited from response.charset)"
    )

    def writelines(self, seq):
        for item in seq:
            self.write(item)

    def close(self):
        raise NotImplementedError("Response bodies cannot be closed")

    def flush(self):
        pass



class AppIterRange(object):
    """
    Wraps an app_iter, returning just a range of bytes
    """

    def __init__(self, app_iter, start, stop):
        assert start >= 0, "Bad start: %r" % start
        assert stop is None or (stop >= 0 and stop >= start), (
            "Bad stop: %r" % stop)
        self.app_iter = iter(app_iter)
        self._pos = 0 # position in app_iter
        self.start = start
        self.stop = stop

    def __iter__(self):
        return self

    def _skip_start(self):
        start, stop = self.start, self.stop
        for chunk in self.app_iter:
            self._pos += len(chunk)
            if self._pos < start:
                continue
            elif self._pos == start:
                return b''
            else:
                chunk = chunk[start-self._pos:]
                if stop is not None and self._pos > stop:
                    chunk = chunk[:stop-self._pos]
                    assert len(chunk) == stop - start
                return chunk
        else:
            raise StopIteration()


    def next(self):
        if self._pos < self.start:
            # need to skip some leading bytes
            return self._skip_start()
        stop = self.stop
        if stop is not None and self._pos >= stop:
            raise StopIteration

        chunk = next(self.app_iter)
        self._pos += len(chunk)

        if stop is None or self._pos <= stop:
            return chunk
        else:
            return chunk[:stop-self._pos]

    __next__ = next # py3

    def close(self):
        iter_close(self.app_iter)


class EmptyResponse(object):
    """An empty WSGI response.

    An iterator that immediately stops. Optionally provides a close
    method to close an underlying app_iter it replaces.
    """

    def __init__(self, app_iter=None):
        if app_iter and hasattr(app_iter, 'close'):
            self.close = app_iter.close

    def __iter__(self):
        return self

    def __len__(self):
        return 0

    def next(self):
        raise StopIteration()

    __next__ = next # py3

def _request_uri(environ):
    """Like wsgiref.url.request_uri, except eliminates :80 ports

    Return the full request URI"""
    url = environ['wsgi.url_scheme']+'://'

    if environ.get('HTTP_HOST'):
        url += environ['HTTP_HOST']
    else:
        url += environ['SERVER_NAME'] + ':' + environ['SERVER_PORT']
    if url.endswith(':80') and environ['wsgi.url_scheme'] == 'http':
        url = url[:-3]
    elif url.endswith(':443') and environ['wsgi.url_scheme'] == 'https':
        url = url[:-4]

    if PY3: # pragma: no cover
        script_name = bytes_(environ.get('SCRIPT_NAME', '/'), 'latin-1')
        path_info = bytes_(environ.get('PATH_INFO', ''), 'latin-1')
    else:
        script_name = environ.get('SCRIPT_NAME', '/')
        path_info = environ.get('PATH_INFO', '')

    url += url_quote(script_name)
    qpath_info = url_quote(path_info)
    if not 'SCRIPT_NAME' in environ:
        url += qpath_info[1:]
    else:
        url += qpath_info
    return url


def iter_close(iter):
    if hasattr(iter, 'close'):
        iter.close()

def gzip_app_iter(app_iter):
    size = 0
    crc = zlib.crc32(b"") & 0xffffffff
    compress = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS,
                                zlib.DEF_MEM_LEVEL, 0)

    yield _gzip_header
    for item in app_iter:
        size += len(item)
        crc = zlib.crc32(item, crc) & 0xffffffff
        yield compress.compress(item)
    yield compress.flush()
    yield struct.pack("<2L", crc, size & 0xffffffff)

def _error_unicode_in_app_iter(app_iter, body):
    app_iter_repr = repr(app_iter)
    if len(app_iter_repr) > 50:
        app_iter_repr = (
            app_iter_repr[:30] + '...' + app_iter_repr[-10:])
    raise TypeError(
        'An item of the app_iter (%s) was text, causing a '
        'text body: %r' % (app_iter_repr, body))
