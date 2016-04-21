import binascii
import cgi
import io
import os
import re
import sys
import tempfile
import mimetypes
try:
    import simplejson as json
except ImportError:
    import json
import warnings

from webob.acceptparse import (
    AcceptLanguage,
    AcceptCharset,
    MIMEAccept,
    MIMENilAccept,
    NoAccept,
    accept_property,
    )

from webob.cachecontrol import (
    CacheControl,
    serialize_cache_control,
    )

from webob.compat import (
    PY3,
    bytes_,
    integer_types,
    native_,
    parse_qsl_text,
    reraise,
    text_type,
    url_encode,
    url_quote,
    url_unquote,
    quote_plus,
    urlparse,
    )

from webob.cookies import RequestCookies

from webob.descriptors import (
    CHARSET_RE,
    SCHEME_RE,
    converter,
    converter_date,
    environ_getter,
    environ_decoder,
    parse_auth,
    parse_int,
    parse_int_safe,
    parse_range,
    serialize_auth,
    serialize_if_range,
    serialize_int,
    serialize_range,
    upath_property,
    deprecated_property,
    )

from webob.etag import (
    IfRange,
    AnyETag,
    NoETag,
    etag_property,
    )

from webob.headers import EnvironHeaders

from webob.multidict import (
    NestedMultiDict,
    MultiDict,
    NoVars,
    GetDict,
    )

from webob.util import warn_deprecation

__all__ = ['BaseRequest', 'Request', 'LegacyRequest']

class _NoDefault:
    def __repr__(self):
        return '(No Default)'
NoDefault = _NoDefault()

PATH_SAFE = '/:@&+$,'

http_method_probably_has_body = dict.fromkeys(
    ('GET', 'HEAD', 'DELETE', 'TRACE'), False)
http_method_probably_has_body.update(
    dict.fromkeys(('POST', 'PUT'), True))

_LATIN_ENCODINGS = (
    'ascii', 'latin-1', 'latin', 'latin_1', 'l1', 'latin1',
    'iso-8859-1', 'iso8859_1', 'iso_8859_1', 'iso8859', '8859',
    )

class BaseRequest(object):
    ## The limit after which request bodies should be stored on disk
    ## if they are read in (under this, and the request body is stored
    ## in memory):
    request_body_tempfile_limit = 10*1024

    _charset = None

    def __init__(self, environ, charset=None, unicode_errors=None,
                 decode_param_names=None, **kw):

        if type(environ) is not dict:
            raise TypeError(
                "WSGI environ must be a dict; you passed %r" % (environ,))
        if unicode_errors is not None:
            warnings.warn(
                "You unicode_errors=%r to the Request constructor.  Passing a "
                "``unicode_errors`` value to the Request is no longer "
                "supported in WebOb 1.2+.  This value has been ignored " % (
                    unicode_errors,),
                DeprecationWarning
                )
        if decode_param_names is not None:
            warnings.warn(
                "You passed decode_param_names=%r to the Request constructor. "
                "Passing a ``decode_param_names`` value to the Request "
                "is no longer supported in WebOb 1.2+.  This value has "
                "been ignored " % (decode_param_names,),
                DeprecationWarning
                )
        if not _is_utf8(charset):
            raise DeprecationWarning(
                "You passed charset=%r to the Request constructor. As of "
                "WebOb 1.2, if your application needs a non-UTF-8 request "
                "charset, please construct the request without a charset or "
                "with a charset of 'None',  then use ``req = "
                "req.decode(charset)``" % charset

            )
        d = self.__dict__
        d['environ'] = environ
        if kw:
            cls = self.__class__
            if 'method' in kw:
                # set method first, because .body setters
                # depend on it for checks
                self.method = kw.pop('method')
            for name, value in kw.items():
                if not hasattr(cls, name):
                    raise TypeError(
                        "Unexpected keyword: %s=%r" % (name, value))
                setattr(self, name, value)

    if PY3: # pragma: no cover
        def encget(self, key, default=NoDefault, encattr=None):
            val = self.environ.get(key, default)
            if val is NoDefault:
                raise KeyError(key)
            if val is default:
                return default
            if not encattr:
                return val
            encoding = getattr(self, encattr)
            if encoding in _LATIN_ENCODINGS: # shortcut
                return val
            return bytes_(val, 'latin-1').decode(encoding)
    else:
        def encget(self, key, default=NoDefault, encattr=None):
            val = self.environ.get(key, default)
            if val is NoDefault:
                raise KeyError(key)
            if val is default:
                return default
            if encattr is None:
                return val
            encoding = getattr(self, encattr)
            return val.decode(encoding)

    def encset(self, key, val, encattr=None):
        if encattr:
            encoding = getattr(self, encattr)
        else:
            encoding = 'ascii'
        if PY3: # pragma: no cover
            self.environ[key] = bytes_(val, encoding).decode('latin-1')
        else:
            self.environ[key] = bytes_(val, encoding)

    @property
    def charset(self):
        if self._charset is None:
            charset = detect_charset(self._content_type_raw)
            if _is_utf8(charset):
                charset = 'UTF-8'
            self._charset = charset
        return self._charset

    @charset.setter
    def charset(self, charset):
        if _is_utf8(charset):
            charset = 'UTF-8'
        if charset != self.charset:
            raise DeprecationWarning("Use req = req.decode(%r)" % charset)

    def decode(self, charset=None, errors='strict'):
        charset = charset or self.charset
        if charset == 'UTF-8':
            return self
        # cookies and path are always utf-8
        t = Transcoder(charset, errors)

        new_content_type = CHARSET_RE.sub('; charset="UTF-8"',
                                          self._content_type_raw)
        content_type = self.content_type
        r = self.__class__(
            self.environ.copy(),
            query_string=t.transcode_query(self.query_string),
            content_type=new_content_type,
        )

        if content_type == 'application/x-www-form-urlencoded':
            r.body = bytes_(t.transcode_query(native_(r.body)))
            return r
        elif content_type != 'multipart/form-data':
            return r

        fs_environ = self.environ.copy()
        fs_environ.setdefault('CONTENT_LENGTH', '0')
        fs_environ['QUERY_STRING'] = ''
        if PY3: # pragma: no cover
            fs = cgi.FieldStorage(fp=self.body_file,
                                  environ=fs_environ,
                                  keep_blank_values=True,
                                  encoding=charset,
                                  errors=errors)
        else:
            fs = cgi.FieldStorage(fp=self.body_file,
                                  environ=fs_environ,
                                  keep_blank_values=True)


        fout = t.transcode_fs(fs, r._content_type_raw)

        # this order is important, because setting body_file
        # resets content_length
        r.body_file = fout
        r.content_length = fout.tell()
        fout.seek(0)
        return r


    # this is necessary for correct warnings depth for both
    # BaseRequest and Request (due to AdhocAttrMixin.__setattr__)
    _setattr_stacklevel = 2

    def _body_file__get(self):
        """
            Input stream of the request (wsgi.input).
            Setting this property resets the content_length and seekable flag
            (unlike setting req.body_file_raw).
        """
        if not self.is_body_readable:
            return io.BytesIO()
        r = self.body_file_raw
        clen = self.content_length
        if not self.is_body_seekable and clen is not None:
            # we need to wrap input in LimitedLengthFile
            # but we have to cache the instance as well
            # otherwise this would stop working
            # (.remaining counter would reset between calls):
            #   req.body_file.read(100)
            #   req.body_file.read(100)
            env = self.environ
            wrapped, raw = env.get('webob._body_file', (0,0))
            if raw is not r:
                wrapped = LimitedLengthFile(r, clen)
                wrapped = io.BufferedReader(wrapped)
                env['webob._body_file'] = wrapped, r
            r = wrapped
        return r

    def _body_file__set(self, value):
        if isinstance(value, bytes):
            warn_deprecation(
                "Please use req.body = b'bytes' or req.body_file = fileobj",
                '1.2',
                self._setattr_stacklevel
            )
        self.content_length = None
        self.body_file_raw = value
        self.is_body_seekable = False
        self.is_body_readable = True
    def _body_file__del(self):
        self.body = b''
    body_file = property(_body_file__get,
                         _body_file__set,
                         _body_file__del,
                         doc=_body_file__get.__doc__)
    body_file_raw = environ_getter('wsgi.input')
    @property
    def body_file_seekable(self):
        """
            Get the body of the request (wsgi.input) as a seekable file-like
            object. Middleware and routing applications should use this
            attribute over .body_file.

            If you access this value, CONTENT_LENGTH will also be updated.
        """
        if not self.is_body_seekable:
            self.make_body_seekable()
        return self.body_file_raw

    url_encoding = environ_getter('webob.url_encoding', 'UTF-8')
    scheme = environ_getter('wsgi.url_scheme')
    method = environ_getter('REQUEST_METHOD', 'GET')
    http_version = environ_getter('SERVER_PROTOCOL')
    content_length = converter(
        environ_getter('CONTENT_LENGTH', None, '14.13'),
        parse_int_safe, serialize_int, 'int')
    remote_user = environ_getter('REMOTE_USER', None)
    remote_addr = environ_getter('REMOTE_ADDR', None)
    query_string = environ_getter('QUERY_STRING', '')
    server_name = environ_getter('SERVER_NAME')
    server_port = converter(
        environ_getter('SERVER_PORT'),
        parse_int, serialize_int, 'int')

    script_name = environ_decoder('SCRIPT_NAME', '', encattr='url_encoding')
    path_info = environ_decoder('PATH_INFO', encattr='url_encoding')

    # bw compat
    uscript_name = script_name
    upath_info = path_info

    _content_type_raw = environ_getter('CONTENT_TYPE', '')

    def _content_type__get(self):
        """Return the content type, but leaving off any parameters (like
        charset, but also things like the type in ``application/atom+xml;
        type=entry``)

        If you set this property, you can include parameters, or if
        you don't include any parameters in the value then existing
        parameters will be preserved.
        """
        return self._content_type_raw.split(';', 1)[0]
    def _content_type__set(self, value=None):
        if value is not None:
            value = str(value)
            if ';' not in value:
                content_type = self._content_type_raw
                if ';' in content_type:
                    value += ';' + content_type.split(';', 1)[1]
        self._content_type_raw = value

    content_type = property(_content_type__get,
                            _content_type__set,
                            _content_type__set,
                            _content_type__get.__doc__)

    _headers = None

    def _headers__get(self):
        """
        All the request headers as a case-insensitive dictionary-like
        object.
        """
        if self._headers is None:
            self._headers = EnvironHeaders(self.environ)
        return self._headers

    def _headers__set(self, value):
        self.headers.clear()
        self.headers.update(value)

    headers = property(_headers__get, _headers__set, doc=_headers__get.__doc__)

    @property
    def client_addr(self):
        """
        The effective client IP address as a string.  If the
        ``HTTP_X_FORWARDED_FOR`` header exists in the WSGI environ, this
        attribute returns the client IP address present in that header
        (e.g. if the header value is ``192.168.1.1, 192.168.1.2``, the value
        will be ``192.168.1.1``). If no ``HTTP_X_FORWARDED_FOR`` header is
        present in the environ at all, this attribute will return the value
        of the ``REMOTE_ADDR`` header.  If the ``REMOTE_ADDR`` header is
        unset, this attribute will return the value ``None``.

        .. warning::

           It is possible for user agents to put someone else's IP or just
           any string in ``HTTP_X_FORWARDED_FOR`` as it is a normal HTTP
           header. Forward proxies can also provide incorrect values (private
           IP addresses etc).  You cannot "blindly" trust the result of this
           method to provide you with valid data unless you're certain that
           ``HTTP_X_FORWARDED_FOR`` has the correct values.  The WSGI server
           must be behind a trusted proxy for this to be true.
        """
        e = self.environ
        xff = e.get('HTTP_X_FORWARDED_FOR')
        if xff is not None:
            addr = xff.split(',')[0].strip()
        else:
            addr = e.get('REMOTE_ADDR')
        return addr

    @property
    def host_port(self):
        """
        The effective server port number as a string.  If the ``HTTP_HOST``
        header exists in the WSGI environ, this attribute returns the port
        number present in that header. If the ``HTTP_HOST`` header exists but
        contains no explicit port number: if the WSGI url scheme is "https" ,
        this attribute returns "443", if the WSGI url scheme is "http", this
        attribute returns "80" .  If no ``HTTP_HOST`` header is present in
        the environ at all, this attribute will return the value of the
        ``SERVER_PORT`` header (which is guaranteed to be present).
        """
        e = self.environ
        host = e.get('HTTP_HOST')
        if host is not None:
            if ':' in host:
                host, port = host.split(':', 1)
            else:
                url_scheme = e['wsgi.url_scheme']
                if url_scheme == 'https':
                    port = '443'
                else:
                    port = '80'
        else:
            port = e['SERVER_PORT']
        return port

    @property
    def host_url(self):
        """
        The URL through the host (no path)
        """
        e = self.environ
        scheme = e.get('wsgi.url_scheme')
        url = scheme + '://'
        host = e.get('HTTP_HOST')
        if host is not None:
            if ':' in host:
                host, port = host.split(':', 1)
            else:
                port = None
        else:
            host = e.get('SERVER_NAME')
            port = e.get('SERVER_PORT')
        if scheme == 'https':
            if port == '443':
                port = None
        elif scheme == 'http':
            if port == '80':
                port = None
        url += host
        if port:
            url += ':%s' % port
        return url

    @property
    def application_url(self):
        """
        The URL including SCRIPT_NAME (no PATH_INFO or query string)
        """
        bscript_name = bytes_(self.script_name, self.url_encoding)
        return self.host_url + url_quote(bscript_name, PATH_SAFE)

    @property
    def path_url(self):
        """
        The URL including SCRIPT_NAME and PATH_INFO, but not QUERY_STRING
        """
        bpath_info = bytes_(self.path_info, self.url_encoding)
        return self.application_url + url_quote(bpath_info, PATH_SAFE)

    @property
    def path(self):
        """
        The path of the request, without host or query string
        """
        bscript = bytes_(self.script_name, self.url_encoding)
        bpath = bytes_(self.path_info, self.url_encoding)
        return url_quote(bscript, PATH_SAFE) + url_quote(bpath, PATH_SAFE)

    @property
    def path_qs(self):
        """
        The path of the request, without host but with query string
        """
        path = self.path
        qs = self.environ.get('QUERY_STRING')
        if qs:
            path += '?' + qs
        return path

    @property
    def url(self):
        """
        The full request URL, including QUERY_STRING
        """
        url = self.path_url
        qs = self.environ.get('QUERY_STRING')
        if qs:
            url += '?' + qs
        return url

    def relative_url(self, other_url, to_application=False):
        """
        Resolve other_url relative to the request URL.

        If ``to_application`` is True, then resolve it relative to the
        URL with only SCRIPT_NAME
        """
        if to_application:
            url = self.application_url
            if not url.endswith('/'):
                url += '/'
        else:
            url = self.path_url
        return urlparse.urljoin(url, other_url)

    def path_info_pop(self, pattern=None):
        """
        'Pops' off the next segment of PATH_INFO, pushing it onto
        SCRIPT_NAME, and returning the popped segment.  Returns None if
        there is nothing left on PATH_INFO.

        Does not return ``''`` when there's an empty segment (like
        ``/path//path``); these segments are just ignored.

        Optional ``pattern`` argument is a regexp to match the return value
        before returning. If there is no match, no changes are made to the
        request and None is returned.
        """
        path = self.path_info
        if not path:
            return None
        slashes = ''
        while path.startswith('/'):
            slashes += '/'
            path = path[1:]
        idx = path.find('/')
        if idx == -1:
            idx = len(path)
        r = path[:idx]
        if pattern is None or re.match(pattern, r):
            self.script_name += slashes + r
            self.path_info = path[idx:]
            return r

    def path_info_peek(self):
        """
        Returns the next segment on PATH_INFO, or None if there is no
        next segment.  Doesn't modify the environment.
        """
        path = self.path_info
        if not path:
            return None
        path = path.lstrip('/')
        return path.split('/', 1)[0]

    def _urlvars__get(self):
        """
        Return any *named* variables matched in the URL.

        Takes values from ``environ['wsgiorg.routing_args']``.
        Systems like ``routes`` set this value.
        """
        if 'paste.urlvars' in self.environ:
            return self.environ['paste.urlvars']
        elif 'wsgiorg.routing_args' in self.environ:
            return self.environ['wsgiorg.routing_args'][1]
        else:
            result = {}
            self.environ['wsgiorg.routing_args'] = ((), result)
            return result

    def _urlvars__set(self, value):
        environ = self.environ
        if 'wsgiorg.routing_args' in environ:
            environ['wsgiorg.routing_args'] = (
                    environ['wsgiorg.routing_args'][0], value)
            if 'paste.urlvars' in environ:
                del environ['paste.urlvars']
        elif 'paste.urlvars' in environ:
            environ['paste.urlvars'] = value
        else:
            environ['wsgiorg.routing_args'] = ((), value)

    def _urlvars__del(self):
        if 'paste.urlvars' in self.environ:
            del self.environ['paste.urlvars']
        if 'wsgiorg.routing_args' in self.environ:
            if not self.environ['wsgiorg.routing_args'][0]:
                del self.environ['wsgiorg.routing_args']
            else:
                self.environ['wsgiorg.routing_args'] = (
                        self.environ['wsgiorg.routing_args'][0], {})

    urlvars = property(_urlvars__get,
                       _urlvars__set,
                       _urlvars__del,
                       doc=_urlvars__get.__doc__)

    def _urlargs__get(self):
        """
        Return any *positional* variables matched in the URL.

        Takes values from ``environ['wsgiorg.routing_args']``.
        Systems like ``routes`` set this value.
        """
        if 'wsgiorg.routing_args' in self.environ:
            return self.environ['wsgiorg.routing_args'][0]
        else:
            # Since you can't update this value in-place, we don't need
            # to set the key in the environment
            return ()

    def _urlargs__set(self, value):
        environ = self.environ
        if 'paste.urlvars' in environ:
            # Some overlap between this and wsgiorg.routing_args; we need
            # wsgiorg.routing_args to make this work
            routing_args = (value, environ.pop('paste.urlvars'))
        elif 'wsgiorg.routing_args' in environ:
            routing_args = (value, environ['wsgiorg.routing_args'][1])
        else:
            routing_args = (value, {})
        environ['wsgiorg.routing_args'] = routing_args

    def _urlargs__del(self):
        if 'wsgiorg.routing_args' in self.environ:
            if not self.environ['wsgiorg.routing_args'][1]:
                del self.environ['wsgiorg.routing_args']
            else:
                self.environ['wsgiorg.routing_args'] = (
                        (), self.environ['wsgiorg.routing_args'][1])

    urlargs = property(_urlargs__get,
                       _urlargs__set,
                       _urlargs__del,
                       _urlargs__get.__doc__)

    @property
    def is_xhr(self):
        """Is X-Requested-With header present and equal to ``XMLHttpRequest``?

        Note: this isn't set by every XMLHttpRequest request, it is
        only set if you are using a Javascript library that sets it
        (or you set the header yourself manually).  Currently
        Prototype and jQuery are known to set this header."""
        return self.environ.get('HTTP_X_REQUESTED_WITH', '') == 'XMLHttpRequest'

    def _host__get(self):
        """Host name provided in HTTP_HOST, with fall-back to SERVER_NAME"""
        if 'HTTP_HOST' in self.environ:
            return self.environ['HTTP_HOST']
        else:
            return '%(SERVER_NAME)s:%(SERVER_PORT)s' % self.environ
    def _host__set(self, value):
        self.environ['HTTP_HOST'] = value
    def _host__del(self):
        if 'HTTP_HOST' in self.environ:
            del self.environ['HTTP_HOST']
    host = property(_host__get, _host__set, _host__del, doc=_host__get.__doc__)

    def _body__get(self):
        """
        Return the content of the request body.
        """
        if not self.is_body_readable:
            return b''
        self.make_body_seekable() # we need this to have content_length
        r = self.body_file.read(self.content_length)
        self.body_file_raw.seek(0)
        return r
    def _body__set(self, value):
        if value is None:
            value = b''
        if not isinstance(value, bytes):
            raise TypeError("You can only set Request.body to bytes (not %r)"
                                % type(value))
        if not http_method_probably_has_body.get(self.method, True):
            if not value:
                self.content_length = None
                self.body_file_raw = io.BytesIO()
                return
        self.content_length = len(value)
        self.body_file_raw = io.BytesIO(value)
        self.is_body_seekable = True
    def _body__del(self):
        self.body = b''
    body = property(_body__get, _body__set, _body__del, doc=_body__get.__doc__)

    def _json_body__get(self):
        """Access the body of the request as JSON"""
        return json.loads(self.body.decode(self.charset))

    def _json_body__set(self, value):
        self.body = json.dumps(value, separators=(',', ':')).encode(self.charset)

    def _json_body__del(self):
        del self.body

    json = json_body = property(_json_body__get, _json_body__set, _json_body__del)

    def _text__get(self):
        """
        Get/set the text value of the body
        """
        if not self.charset:
            raise AttributeError(
                "You cannot access Request.text unless charset is set")
        body = self.body
        return body.decode(self.charset)

    def _text__set(self, value):
        if not self.charset:
            raise AttributeError(
                "You cannot access Response.text unless charset is set")
        if not isinstance(value, text_type):
            raise TypeError(
                "You can only set Request.text to a unicode string "
                "(not %s)" % type(value))
        self.body = value.encode(self.charset)

    def _text__del(self):
        del self.body

    text = property(_text__get, _text__set, _text__del, doc=_text__get.__doc__)


    @property
    def POST(self):
        """
        Return a MultiDict containing all the variables from a form
        request. Returns an empty dict-like object for non-form requests.

        Form requests are typically POST requests, however PUT requests with
        an appropriate Content-Type are also supported.
        """
        env = self.environ
        if self.method not in ('POST', 'PUT'):
            return NoVars('Not a form request')
        if 'webob._parsed_post_vars' in env:
            vars, body_file = env['webob._parsed_post_vars']
            if body_file is self.body_file_raw:
                return vars
        content_type = self.content_type
        if ((self.method == 'PUT' and not content_type)
            or content_type not in
                ('',
                 'application/x-www-form-urlencoded',
                 'multipart/form-data')
                 ):
            # Not an HTML form submission
            return NoVars('Not an HTML form submission (Content-Type: %s)'
                          % content_type)
        self._check_charset()
        if self.is_body_seekable:
            self.body_file_raw.seek(0)
        fs_environ = env.copy()
        # FieldStorage assumes a missing CONTENT_LENGTH, but a
        # default of 0 is better:
        fs_environ.setdefault('CONTENT_LENGTH', '0')
        fs_environ['QUERY_STRING'] = ''
        if PY3: # pragma: no cover
            fs = cgi.FieldStorage(
                fp=self.body_file,
                environ=fs_environ,
                keep_blank_values=True,
                encoding='utf8')
            vars = MultiDict.from_fieldstorage(fs)
        else:
            fs = cgi.FieldStorage(
                fp=self.body_file,
                environ=fs_environ,
                keep_blank_values=True)
            vars = MultiDict.from_fieldstorage(fs)


        #ctype = self.content_type or 'application/x-www-form-urlencoded'
        ctype = self._content_type_raw or 'application/x-www-form-urlencoded'
        f = FakeCGIBody(vars, ctype)
        self.body_file = io.BufferedReader(f)
        env['webob._parsed_post_vars'] = (vars, self.body_file_raw)
        return vars

    @property
    def GET(self):
        """
        Return a MultiDict containing all the variables from the
        QUERY_STRING.
        """
        env = self.environ
        source = env.get('QUERY_STRING', '')
        if 'webob._parsed_query_vars' in env:
            vars, qs = env['webob._parsed_query_vars']
            if qs == source:
                return vars

        data = []
        if source:
            # this is disabled because we want to access req.GET
            # for text/plain; charset=ascii uploads for example
            #self._check_charset()
            data = parse_qsl_text(source)
            #d = lambda b: b.decode('utf8')
            #data = [(d(k), d(v)) for k,v in data]
        vars = GetDict(data, env)
        env['webob._parsed_query_vars'] = (vars, source)
        return vars

    def _check_charset(self):
        if self.charset != 'UTF-8':
            raise DeprecationWarning(
                "Requests are expected to be submitted in UTF-8, not %s. "
                "You can fix this by doing req = req.decode('%s')" % (
                    self.charset, self.charset)
            )

    @property
    def params(self):
        """
        A dictionary-like object containing both the parameters from
        the query string and request body.
        """
        params = NestedMultiDict(self.GET, self.POST)
        return params


    @property
    def cookies(self):
        """
        Return a dictionary of cookies as found in the request.
        """
        return RequestCookies(self.environ)

    @cookies.setter
    def cookies(self, val):
        self.environ.pop('HTTP_COOKIE', None)
        r = RequestCookies(self.environ)
        r.update(val)

    def copy(self):
        """
        Copy the request and environment object.

        This only does a shallow copy, except of wsgi.input
        """
        self.make_body_seekable()
        env = self.environ.copy()
        new_req = self.__class__(env)
        new_req.copy_body()
        return new_req

    def copy_get(self):
        """
        Copies the request and environment object, but turning this request
        into a GET along the way.  If this was a POST request (or any other
        verb) then it becomes GET, and the request body is thrown away.
        """
        env = self.environ.copy()
        return self.__class__(env, method='GET', content_type=None,
                              body=b'')

    # webob.is_body_seekable marks input streams that are seekable
    # this way we can have seekable input without testing the .seek() method
    is_body_seekable = environ_getter('webob.is_body_seekable', False)

    #is_body_readable = environ_getter('webob.is_body_readable', False)

    def _is_body_readable__get(self):
        """
            webob.is_body_readable is a flag that tells us
            that we can read the input stream even though
            CONTENT_LENGTH is missing. This allows FakeCGIBody
            to work and can be used by servers to support
            chunked encoding in requests.
            For background see https://bitbucket.org/ianb/webob/issue/6
        """
        if http_method_probably_has_body.get(self.method):
            # known HTTP method with body
            return True
        elif self.content_length is not None:
            # unknown HTTP method, but the Content-Length
            # header is present
            return True
        else:
            # last resort -- rely on the special flag
            return self.environ.get('webob.is_body_readable', False)

    def _is_body_readable__set(self, flag):
        self.environ['webob.is_body_readable'] = bool(flag)

    is_body_readable = property(_is_body_readable__get, _is_body_readable__set,
        doc=_is_body_readable__get.__doc__
    )



    def make_body_seekable(self):
        """
        This forces ``environ['wsgi.input']`` to be seekable.
        That means that, the content is copied into a BytesIO or temporary
        file and flagged as seekable, so that it will not be unnecessarily
        copied again.

        After calling this method the .body_file is always seeked to the
        start of file and .content_length is not None.

        The choice to copy to BytesIO is made from
        ``self.request_body_tempfile_limit``
        """
        if self.is_body_seekable:
            self.body_file_raw.seek(0)
        else:
            self.copy_body()


    def copy_body(self):
        """
        Copies the body, in cases where it might be shared with
        another request object and that is not desired.

        This copies the body in-place, either into a BytesIO object
        or a temporary file.
        """
        if not self.is_body_readable:
            # there's no body to copy
            self.body = b''
        elif self.content_length is None:
            # chunked body or FakeCGIBody
            self.body = self.body_file_raw.read()
            self._copy_body_tempfile()
        else:
            # try to read body into tempfile
            did_copy = self._copy_body_tempfile()
            if not did_copy:
                # it wasn't necessary, so just read it into memory
                self.body = self.body_file.read(self.content_length)

    def _copy_body_tempfile(self):
        """
            Copy wsgi.input to tempfile if necessary. Returns True if it did.
        """
        tempfile_limit = self.request_body_tempfile_limit
        todo = self.content_length
        assert isinstance(todo, integer_types), todo
        if not tempfile_limit or todo <= tempfile_limit:
            return False
        fileobj = self.make_tempfile()
        input = self.body_file
        while todo > 0:
            data = input.read(min(todo, 65536))
            if not data:
                # Normally this should not happen, because LimitedLengthFile
                # should have raised an exception by now.
                # It can happen if the is_body_seekable flag is incorrect.
                raise DisconnectionError(
                    "Client disconnected (%s more bytes were expected)"
                    % todo
                )
            fileobj.write(data)
            todo -= len(data)
        fileobj.seek(0)
        self.body_file_raw = fileobj
        self.is_body_seekable = True
        return True

    def make_tempfile(self):
        """
            Create a tempfile to store big request body.
            This API is not stable yet. A 'size' argument might be added.
        """
        return tempfile.TemporaryFile()


    def remove_conditional_headers(self,
                                   remove_encoding=True,
                                   remove_range=True,
                                   remove_match=True,
                                   remove_modified=True):
        """
        Remove headers that make the request conditional.

        These headers can cause the response to be 304 Not Modified,
        which in some cases you may not want to be possible.

        This does not remove headers like If-Match, which are used for
        conflict detection.
        """
        check_keys = []
        if remove_range:
            check_keys += ['HTTP_IF_RANGE', 'HTTP_RANGE']
        if remove_match:
            check_keys.append('HTTP_IF_NONE_MATCH')
        if remove_modified:
            check_keys.append('HTTP_IF_MODIFIED_SINCE')
        if remove_encoding:
            check_keys.append('HTTP_ACCEPT_ENCODING')

        for key in check_keys:
            if key in self.environ:
                del self.environ[key]


    accept = accept_property('Accept', '14.1', MIMEAccept, MIMENilAccept)
    accept_charset = accept_property('Accept-Charset', '14.2', AcceptCharset)
    accept_encoding = accept_property('Accept-Encoding', '14.3',
                                      NilClass=NoAccept)
    accept_language = accept_property('Accept-Language', '14.4', AcceptLanguage)

    authorization = converter(
        environ_getter('HTTP_AUTHORIZATION', None, '14.8'),
        parse_auth, serialize_auth,
    )


    def _cache_control__get(self):
        """
        Get/set/modify the Cache-Control header (`HTTP spec section 14.9
        <http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.9>`_)
        """
        env = self.environ
        value = env.get('HTTP_CACHE_CONTROL', '')
        cache_header, cache_obj = env.get('webob._cache_control', (None, None))
        if cache_obj is not None and cache_header == value:
            return cache_obj
        cache_obj = CacheControl.parse(value,
                                       updates_to=self._update_cache_control,
                                       type='request')
        env['webob._cache_control'] = (value, cache_obj)
        return cache_obj

    def _cache_control__set(self, value):
        env = self.environ
        value = value or ''
        if isinstance(value, dict):
            value = CacheControl(value, type='request')
        if isinstance(value, CacheControl):
            str_value = str(value)
            env['HTTP_CACHE_CONTROL'] = str_value
            env['webob._cache_control'] = (str_value, value)
        else:
            env['HTTP_CACHE_CONTROL'] = str(value)
            env['webob._cache_control'] = (None, None)

    def _cache_control__del(self):
        env = self.environ
        if 'HTTP_CACHE_CONTROL' in env:
            del env['HTTP_CACHE_CONTROL']
        if 'webob._cache_control' in env:
            del env['webob._cache_control']

    def _update_cache_control(self, prop_dict):
        self.environ['HTTP_CACHE_CONTROL'] = serialize_cache_control(prop_dict)

    cache_control = property(_cache_control__get,
                             _cache_control__set,
                             _cache_control__del,
                             doc=_cache_control__get.__doc__)


    if_match = etag_property('HTTP_IF_MATCH', AnyETag, '14.24')
    if_none_match = etag_property('HTTP_IF_NONE_MATCH', NoETag, '14.26',
                                  strong=False)

    date = converter_date(environ_getter('HTTP_DATE', None, '14.8'))
    if_modified_since = converter_date(
                    environ_getter('HTTP_IF_MODIFIED_SINCE', None, '14.25'))
    if_unmodified_since = converter_date(
                    environ_getter('HTTP_IF_UNMODIFIED_SINCE', None, '14.28'))
    if_range = converter(
        environ_getter('HTTP_IF_RANGE', None, '14.27'),
        IfRange.parse, serialize_if_range, 'IfRange object')


    max_forwards = converter(
        environ_getter('HTTP_MAX_FORWARDS', None, '14.31'),
        parse_int, serialize_int, 'int')

    pragma = environ_getter('HTTP_PRAGMA', None, '14.32')

    range = converter(
        environ_getter('HTTP_RANGE', None, '14.35'),
        parse_range, serialize_range, 'Range object')

    referer = environ_getter('HTTP_REFERER', None, '14.36')
    referrer = referer

    user_agent = environ_getter('HTTP_USER_AGENT', None, '14.43')

    def __repr__(self):
        try:
            name = '%s %s' % (self.method, self.url)
        except KeyError:
            name = '(invalid WSGI environ)'
        msg = '<%s at 0x%x %s>' % (
            self.__class__.__name__,
            abs(id(self)), name)
        return msg

    def as_bytes(self, skip_body=False):
        """
            Return HTTP bytes representing this request.
            If skip_body is True, exclude the body.
            If skip_body is an integer larger than one, skip body
            only if its length is bigger than that number.
        """
        url = self.url
        host = self.host_url
        assert url.startswith(host)
        url = url[len(host):]
        parts = [bytes_('%s %s %s' % (self.method, url, self.http_version))]
        #self.headers.setdefault('Host', self.host)

        # acquire body before we handle headers so that
        # content-length will be set
        body = None
        if self.method in ('PUT', 'POST'):
            if skip_body > 1:
                if len(self.body) > skip_body:
                    body = bytes_('<body skipped (len=%s)>' % len(self.body))
                else:
                    skip_body = False
            if not skip_body:
                body = self.body

        for k, v in sorted(self.headers.items()):
            header = bytes_('%s: %s'  % (k, v))
            parts.append(header)

        if body:
            parts.extend([b'', body])
        # HTTP clearly specifies CRLF
        return b'\r\n'.join(parts)

    def as_string(self, skip_body=False):
        warn_deprecation(
            "Please use req.as_bytes",
            '1.3',
            self._setattr_stacklevel
            )
        return self.as_bytes(skip_body=skip_body)

    def as_text(self):
        bytes = self.as_bytes()
        return bytes.decode(self.charset)

    __str__ = as_text

    @classmethod
    def from_bytes(cls, b):
        """
            Create a request from HTTP bytes data. If the bytes contain
            extra data after the request, raise a ValueError.
        """
        f = io.BytesIO(b)
        r = cls.from_file(f)
        if f.tell() != len(b):
            raise ValueError("The string contains more data than expected")
        return r

    @classmethod
    def from_string(cls, b):
        warn_deprecation(
            "Please use req.from_bytes",
            '1.3',
            cls._setattr_stacklevel
            )
        return cls.from_bytes(b)

    @classmethod
    def from_text(cls, s):
        b = bytes_(s, 'utf-8')
        return cls.from_bytes(b)

    @classmethod
    def from_file(cls, fp):
        """Read a request from a file-like object (it must implement
        ``.read(size)`` and ``.readline()``).

        It will read up to the end of the request, not the end of the
        file (unless the request is a POST or PUT and has no
        Content-Length, in that case, the entire file is read).

        This reads the request as represented by ``str(req)``; it may
        not read every valid HTTP request properly.
        """
        start_line = fp.readline()
        is_text = isinstance(start_line, text_type)
        if is_text:
            crlf = '\r\n'
            colon = ':'
        else:
            crlf = b'\r\n'
            colon = b':'
        try:
            header = start_line.rstrip(crlf)
            method, resource, http_version = header.split(None, 2)
            method = native_(method, 'utf-8')
            resource = native_(resource, 'utf-8')
            http_version = native_(http_version, 'utf-8')
        except ValueError:
            raise ValueError('Bad HTTP request line: %r' % start_line)
        r = cls(environ_from_url(resource),
                http_version=http_version,
                method=method.upper()
                )
        del r.environ['HTTP_HOST']
        while 1:
            line = fp.readline()
            if not line.strip():
                # end of headers
                break
            hname, hval = line.split(colon, 1)
            hname = native_(hname, 'utf-8')
            hval = native_(hval, 'utf-8').strip()
            if hname in r.headers:
                hval = r.headers[hname] + ', ' + hval
            r.headers[hname] = hval
        if r.method in ('PUT', 'POST'):
            clen = r.content_length
            if clen is None:
                body = fp.read()
            else:
                body = fp.read(clen)
            if is_text:
                body = bytes_(body, 'utf-8')
            r.body = body
        return r

    def call_application(self, application, catch_exc_info=False):
        """
        Call the given WSGI application, returning ``(status_string,
        headerlist, app_iter)``

        Be sure to call ``app_iter.close()`` if it's there.

        If catch_exc_info is true, then returns ``(status_string,
        headerlist, app_iter, exc_info)``, where the fourth item may
        be None, but won't be if there was an exception.  If you don't
        do this and there was an exception, the exception will be
        raised directly.
        """
        if self.is_body_seekable:
            self.body_file_raw.seek(0)
        captured = []
        output = []
        def start_response(status, headers, exc_info=None):
            if exc_info is not None and not catch_exc_info:
                reraise(exc_info)
            captured[:] = [status, headers, exc_info]
            return output.append
        app_iter = application(self.environ, start_response)
        if output or not captured:
            try:
                output.extend(app_iter)
            finally:
                if hasattr(app_iter, 'close'):
                    app_iter.close()
            app_iter = output
        if catch_exc_info:
            return (captured[0], captured[1], app_iter, captured[2])
        else:
            return (captured[0], captured[1], app_iter)

    # Will be filled in later:
    ResponseClass = None

    def send(self, application=None, catch_exc_info=False):
        """
        Like ``.call_application(application)``, except returns a
        response object with ``.status``, ``.headers``, and ``.body``
        attributes.

        This will use ``self.ResponseClass`` to figure out the class
        of the response object to return.

        If ``application`` is not given, this will send the request to
        ``self.make_default_send_app()``
        """
        if application is None:
            application = self.make_default_send_app()
        if catch_exc_info:
            status, headers, app_iter, exc_info = self.call_application(
                application, catch_exc_info=True)
            del exc_info
        else:
            status, headers, app_iter = self.call_application(
                application, catch_exc_info=False)
        return self.ResponseClass(
            status=status, headerlist=list(headers), app_iter=app_iter)

    get_response = send

    def make_default_send_app(self):
        global _client
        try:
            client = _client
        except NameError:
            from webob import client
            _client = client
        return client.send_request_app

    @classmethod
    def blank(cls, path, environ=None, base_url=None,
              headers=None, POST=None, **kw):
        """
        Create a blank request environ (and Request wrapper) with the
        given path (path should be urlencoded), and any keys from
        environ.

        The path will become path_info, with any query string split
        off and used.

        All necessary keys will be added to the environ, but the
        values you pass in will take precedence.  If you pass in
        base_url then wsgi.url_scheme, HTTP_HOST, and SCRIPT_NAME will
        be filled in from that value.

        Any extra keyword will be passed to ``__init__``.
        """
        env = environ_from_url(path)
        if base_url:
            scheme, netloc, path, query, fragment = urlparse.urlsplit(base_url)
            if query or fragment:
                raise ValueError(
                    "base_url (%r) cannot have a query or fragment"
                    % base_url)
            if scheme:
                env['wsgi.url_scheme'] = scheme
            if netloc:
                if ':' not in netloc:
                    if scheme == 'http':
                        netloc += ':80'
                    elif scheme == 'https':
                        netloc += ':443'
                    else:
                        raise ValueError(
                            "Unknown scheme: %r" % scheme)
                host, port = netloc.split(':', 1)
                env['SERVER_PORT'] = port
                env['SERVER_NAME'] = host
                env['HTTP_HOST'] = netloc
            if path:
                env['SCRIPT_NAME'] = url_unquote(path)
        if environ:
            env.update(environ)
        content_type = kw.get('content_type', env.get('CONTENT_TYPE'))
        if headers and 'Content-Type' in headers:
            content_type = headers['Content-Type']
        if content_type is not None:
            kw['content_type'] = content_type
        environ_add_POST(env, POST, content_type=content_type)
        obj = cls(env, **kw)
        if headers is not None:
            obj.headers.update(headers)
        return obj

class LegacyRequest(BaseRequest):
    uscript_name = upath_property('SCRIPT_NAME')
    upath_info = upath_property('PATH_INFO')

    def encget(self, key, default=NoDefault, encattr=None):
        val = self.environ.get(key, default)
        if val is NoDefault:
            raise KeyError(key)
        if val is default:
            return default
        return val

class AdhocAttrMixin(object):
    _setattr_stacklevel = 3

    def __setattr__(self, attr, value, DEFAULT=object()):
        if (getattr(self.__class__, attr, DEFAULT) is not DEFAULT or
                    attr.startswith('_')):
            object.__setattr__(self, attr, value)
        else:
            self.environ.setdefault('webob.adhoc_attrs', {})[attr] = value

    def __getattr__(self, attr, DEFAULT=object()):
        try:
            return self.environ['webob.adhoc_attrs'][attr]
        except KeyError:
            raise AttributeError(attr)

    def __delattr__(self, attr, DEFAULT=object()):
        if getattr(self.__class__, attr, DEFAULT) is not DEFAULT:
            return object.__delattr__(self, attr)
        try:
            del self.environ['webob.adhoc_attrs'][attr]
        except KeyError:
            raise AttributeError(attr)

class Request(AdhocAttrMixin, BaseRequest):
    """ The default request implementation """

def environ_from_url(path):
    if SCHEME_RE.search(path):
        scheme, netloc, path, qs, fragment = urlparse.urlsplit(path)
        if fragment:
            raise TypeError("Path cannot contain a fragment (%r)" % fragment)
        if qs:
            path += '?' + qs
        if ':' not in netloc:
            if scheme == 'http':
                netloc += ':80'
            elif scheme == 'https':
                netloc += ':443'
            else:
                raise TypeError("Unknown scheme: %r" % scheme)
    else:
        scheme = 'http'
        netloc = 'localhost:80'
    if path and '?' in path:
        path_info, query_string = path.split('?', 1)
        path_info = url_unquote(path_info)
    else:
        path_info = url_unquote(path)
        query_string = ''
    env = {
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '',
        'PATH_INFO': path_info or '',
        'QUERY_STRING': query_string,
        'SERVER_NAME': netloc.split(':')[0],
        'SERVER_PORT': netloc.split(':')[1],
        'HTTP_HOST': netloc,
        'SERVER_PROTOCOL': 'HTTP/1.0',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': scheme,
        'wsgi.input': io.BytesIO(),
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        #'webob.is_body_seekable': True,
    }
    return env


def environ_add_POST(env, data, content_type=None):
    if data is None:
        return
    elif isinstance(data, text_type): # pragma: no cover
        data = data.encode('ascii')
    if env['REQUEST_METHOD'] not in ('POST', 'PUT'):
        env['REQUEST_METHOD'] = 'POST'
    has_files = False
    if hasattr(data, 'items'):
        data = sorted(data.items())
        for k, v in data:
            if isinstance(v, (tuple, list)):
                has_files = True
                break
    if content_type is None:
        if has_files:
            content_type = 'multipart/form-data'
        else:
            content_type = 'application/x-www-form-urlencoded'
    if content_type.startswith('multipart/form-data'):
        if not isinstance(data, bytes):
            content_type, data = _encode_multipart(data, content_type)
    elif content_type.startswith('application/x-www-form-urlencoded'):
        if has_files:
            raise ValueError('Submiting files is not allowed for'
                             ' content type `%s`' % content_type)
        if not isinstance(data, bytes):
            data = url_encode(data)
    else:
        if not isinstance(data, bytes):
            raise ValueError('Please provide `POST` data as string'
                             ' for content type `%s`' % content_type)
    data = bytes_(data, 'utf8')
    env['wsgi.input'] = io.BytesIO(data)
    env['webob.is_body_seekable'] = True
    env['CONTENT_LENGTH'] = str(len(data))
    env['CONTENT_TYPE'] = content_type



#########################
## Helper classes and monkeypatching
#########################

class DisconnectionError(IOError):
    pass


class LimitedLengthFile(io.RawIOBase):
    def __init__(self, file, maxlen):
        self.file = file
        self.maxlen = maxlen
        self.remaining = maxlen

    def __repr__(self):
        return '<%s(%r, maxlen=%s)>' % (
            self.__class__.__name__,
            self.file,
            self.maxlen
        )

    def fileno(self):
        return self.file.fileno()

    @staticmethod
    def readable():
        return True

    def readinto(self, buff):
        if not self.remaining:
            return 0
        sz0 = min(len(buff), self.remaining)
        data = self.file.read(sz0)
        sz = len(data)
        self.remaining -= sz
        #if not data:
        if sz < sz0 and self.remaining:
            raise DisconnectionError(
                "The client disconnected while sending the POST/PUT body "
                + "(%d more bytes were expected)" % self.remaining
            )
        buff[:sz] = data
        return sz


def _cgi_FieldStorage__repr__patch(self):
    """ monkey patch for FieldStorage.__repr__

    Unbelievably, the default __repr__ on FieldStorage reads
    the entire file content instead of being sane about it.
    This is a simple replacement that doesn't do that
    """
    if self.file:
        return "FieldStorage(%r, %r)" % (self.name, self.filename)
    return "FieldStorage(%r, %r, %r)" % (self.name, self.filename, self.value)

cgi.FieldStorage.__repr__ = _cgi_FieldStorage__repr__patch

class FakeCGIBody(io.RawIOBase):
    def __init__(self, vars, content_type):
        if content_type.startswith('multipart/form-data'):
            if not _get_multipart_boundary(content_type):
                raise ValueError('Content-type: %r does not contain boundary'
                            % content_type)
        self.vars = vars
        self.content_type = content_type
        self.file = None

    def __repr__(self):
        inner = repr(self.vars)
        if len(inner) > 20:
            inner = inner[:15] + '...' + inner[-5:]
        return '<%s at 0x%x viewing %s>' % (
            self.__class__.__name__,
            abs(id(self)), inner)

    def fileno(self):
        return None

    @staticmethod
    def readable():
        return True

    def readinto(self, buff):
        if self.file is None:
            if self.content_type.startswith(
                'application/x-www-form-urlencoded'):
                data = '&'.join(
                    '%s=%s' % (quote_plus(bytes_(k, 'utf8')), quote_plus(bytes_(v, 'utf8')))
                    for k,v in self.vars.items()
                )
                self.file = io.BytesIO(bytes_(data))
            elif self.content_type.startswith('multipart/form-data'):
                self.file = _encode_multipart(
                    self.vars.items(),
                    self.content_type,
                    fout=io.BytesIO()
                )[1]
                self.file.seek(0)
            else:
                assert 0, ('Bad content type: %r' % self.content_type)
        return self.file.readinto(buff)


def _get_multipart_boundary(ctype):
    m = re.search(r'boundary=([^ ]+)', ctype, re.I)
    if m:
        return native_(m.group(1).strip('"'))


def _encode_multipart(vars, content_type, fout=None):
    """Encode a multipart request body into a string"""
    f = fout or io.BytesIO()
    w = f.write
    wt = lambda t: f.write(t.encode('utf8'))
    CRLF = b'\r\n'
    boundary = _get_multipart_boundary(content_type)
    if not boundary:
        boundary = native_(binascii.hexlify(os.urandom(10)))
        content_type += ('; boundary=%s' % boundary)
    for name, value in vars:
        w(b'--')
        wt(boundary)
        w(CRLF)
        assert name is not None, 'Value associated with no name: %r' % value
        wt('Content-Disposition: form-data; name="%s"' % name)
        filename = None
        if getattr(value, 'filename', None):
            filename = value.filename
        elif isinstance(value, (list, tuple)):
            filename, value = value
            if hasattr(value, 'read'):
                value = value.read()

        if filename is not None:
            wt('; filename="%s"' % filename)
            mime_type = mimetypes.guess_type(filename)[0]
        else:
            mime_type = None

        w(CRLF)

        # TODO: should handle value.disposition_options
        if getattr(value, 'type', None):
            wt('Content-type: %s' % value.type)
            if value.type_options:
                for ct_name, ct_value in sorted(value.type_options.items()):
                    wt('; %s="%s"' % (ct_name, ct_value))
            w(CRLF)
        elif mime_type:
            wt('Content-type: %s' % mime_type)
            w(CRLF)
        w(CRLF)
        if hasattr(value, 'value'):
            value = value.value
        if isinstance(value, bytes):
            w(value)
        else:
            wt(value)
        w(CRLF)
    wt('--%s--' % boundary)
    if fout:
        return content_type, fout
    else:
        return content_type, f.getvalue()

def detect_charset(ctype):
    m = CHARSET_RE.search(ctype)
    if m:
        return m.group(1).strip('"').strip()

def _is_utf8(charset):
    if not charset:
        return True
    else:
        return charset.lower().replace('-', '') == 'utf8'


class Transcoder(object):
    def __init__(self, charset, errors='strict'):
        self.charset = charset # source charset
        self.errors = errors # unicode errors
        self._trans = lambda b: b.decode(charset, errors).encode('utf8')

    def transcode_query(self, q):
        if PY3: # pragma: no cover
            q_orig = q
            if '=' not in q:
                # this doesn't look like a form submission
                return q_orig
            q = list(parse_qsl_text(q, self.charset))
            return url_encode(q)
        else:
            q_orig = q
            if '=' not in q:
                # this doesn't look like a form submission
                return q_orig
            q = urlparse.parse_qsl(q, self.charset)
            t = self._trans
            q = [(t(k), t(v)) for k,v in q]
            return url_encode(q)

    def transcode_fs(self, fs, content_type):
        # transcode FieldStorage
        if PY3: # pragma: no cover
            decode = lambda b: b
        else:
            decode = lambda b: b.decode(self.charset, self.errors)
        data = []
        for field in fs.list or ():
            field.name = decode(field.name)
            if field.filename:
                field.filename = decode(field.filename)
                data.append((field.name, field))
            else:
                data.append((field.name, decode(field.value)))

        # TODO: transcode big requests to temp file
        content_type, fout = _encode_multipart(
            data,
            content_type,
            fout=io.BytesIO()
        )
        return fout

# TODO: remove in 1.4
for _name in 'GET POST params cookies'.split():
    _str_name = 'str_'+_name
    _prop = deprecated_property(
        None, _str_name,
        "disabled starting WebOb 1.2, use %s instead" % _name, '1.2')
    setattr(BaseRequest, _str_name, _prop)
