"""Open an arbitrary URL.

See the following document for more info on URLs:
"Names and Addresses, URIs, URLs, URNs, URCs", at
http://www.w3.org/pub/WWW/Addressing/Overview.html

See also the HTTP spec (from which the error codes are derived):
"HTTP - Hypertext Transfer Protocol", at
http://www.w3.org/pub/WWW/Protocols/

Related standards and specs:
- RFC1808: the "relative URL" spec. (authoritative status)
- RFC1738 - the "URL standard". (authoritative status)
- RFC1630 - the "URI spec". (informational status)

The object returned by URLopener().open(file) will differ per
protocol.  All you know is that is has methods read(), readline(),
readlines(), fileno(), close() and info().  The read*(), fileno()
and close() methods work like those of open files.
The info() method returns a mimetools.Message object which can be
used to query various info about the object, if available.
(mimetools.Message objects are queried with the getheader() method.)
"""

import string
import socket
import os
import time
import sys
import base64
import re

from urlparse import urljoin as basejoin

__all__ = ["urlopen", "URLopener", "FancyURLopener", "urlretrieve",
           "urlcleanup", "quote", "quote_plus", "unquote", "unquote_plus",
           "urlencode", "url2pathname", "pathname2url", "splittag",
           "localhost", "thishost", "ftperrors", "basejoin", "unwrap",
           "splittype", "splithost", "splituser", "splitpasswd", "splitport",
           "splitnport", "splitquery", "splitattr", "splitvalue",
           "getproxies"]

__version__ = '1.17'    # XXX This version is not always updated :-(

MAXFTPCACHE = 10        # Trim the ftp cache beyond this size

# Helper for non-unix systems
if os.name == 'nt':
    from nturl2path import url2pathname, pathname2url
elif os.name == 'riscos':
    from rourl2path import url2pathname, pathname2url
else:
    def url2pathname(pathname):
        """OS-specific conversion from a relative URL of the 'file' scheme
        to a file system path; not recommended for general use."""
        return unquote(pathname)

    def pathname2url(pathname):
        """OS-specific conversion from a file system path to a relative URL
        of the 'file' scheme; not recommended for general use."""
        return quote(pathname)

# This really consists of two pieces:
# (1) a class which handles opening of all sorts of URLs
#     (plus assorted utilities etc.)
# (2) a set of functions for parsing URLs
# XXX Should these be separated out into different modules?


# Shortcut for basic usage
_urlopener = None
def urlopen(url, data=None, proxies=None, context=None):
    """Create a file-like object for the specified URL to read from."""
    from warnings import warnpy3k
    warnpy3k("urllib.urlopen() has been removed in Python 3.0 in "
             "favor of urllib2.urlopen()", stacklevel=2)

    global _urlopener
    if proxies is not None or context is not None:
        opener = FancyURLopener(proxies=proxies, context=context)
    elif not _urlopener:
        opener = FancyURLopener()
        _urlopener = opener
    else:
        opener = _urlopener
    if data is None:
        return opener.open(url)
    else:
        return opener.open(url, data)
def urlretrieve(url, filename=None, reporthook=None, data=None, context=None):
    global _urlopener
    if context is not None:
        opener = FancyURLopener(context=context)
    elif not _urlopener:
        _urlopener = opener = FancyURLopener()
    else:
        opener = _urlopener
    return opener.retrieve(url, filename, reporthook, data)
def urlcleanup():
    if _urlopener:
        _urlopener.cleanup()
    _safe_quoters.clear()
    ftpcache.clear()

# check for SSL
try:
    import ssl
except:
    _have_ssl = False
else:
    _have_ssl = True

# exception raised when downloaded size does not match content-length
class ContentTooShortError(IOError):
    def __init__(self, message, content):
        IOError.__init__(self, message)
        self.content = content

ftpcache = {}
class URLopener:
    """Class to open URLs.
    This is a class rather than just a subroutine because we may need
    more than one set of global protocol-specific options.
    Note -- this is a base class for those who don't want the
    automatic handling of errors type 302 (relocated) and 401
    (authorization needed)."""

    __tempfiles = None

    version = "Python-urllib/%s" % __version__

    # Constructor
    def __init__(self, proxies=None, context=None, **x509):
        if proxies is None:
            proxies = getproxies()
        assert hasattr(proxies, 'has_key'), "proxies must be a mapping"
        self.proxies = proxies
        self.key_file = x509.get('key_file')
        self.cert_file = x509.get('cert_file')
        self.context = context
        self.addheaders = [('User-Agent', self.version)]
        self.__tempfiles = []
        self.__unlink = os.unlink # See cleanup()
        self.tempcache = None
        # Undocumented feature: if you assign {} to tempcache,
        # it is used to cache files retrieved with
        # self.retrieve().  This is not enabled by default
        # since it does not work for changing documents (and I
        # haven't got the logic to check expiration headers
        # yet).
        self.ftpcache = ftpcache
        # Undocumented feature: you can use a different
        # ftp cache by assigning to the .ftpcache member;
        # in case you want logically independent URL openers
        # XXX This is not threadsafe.  Bah.

    def __del__(self):
        self.close()

    def close(self):
        self.cleanup()

    def cleanup(self):
        # This code sometimes runs when the rest of this module
        # has already been deleted, so it can't use any globals
        # or import anything.
        if self.__tempfiles:
            for file in self.__tempfiles:
                try:
                    self.__unlink(file)
                except OSError:
                    pass
            del self.__tempfiles[:]
        if self.tempcache:
            self.tempcache.clear()

    def addheader(self, *args):
        """Add a header to be used by the HTTP interface only
        e.g. u.addheader('Accept', 'sound/basic')"""
        self.addheaders.append(args)

    # External interface
    def open(self, fullurl, data=None):
        """Use URLopener().open(file) instead of open(file, 'r')."""
        fullurl = unwrap(toBytes(fullurl))
        # percent encode url, fixing lame server errors for e.g, like space
        # within url paths.
        fullurl = quote(fullurl, safe="%/:=&?~#+!$,;'@()*[]|")
        if self.tempcache and fullurl in self.tempcache:
            filename, headers = self.tempcache[fullurl]
            fp = open(filename, 'rb')
            return addinfourl(fp, headers, fullurl)
        urltype, url = splittype(fullurl)
        if not urltype:
            urltype = 'file'
        if urltype in self.proxies:
            proxy = self.proxies[urltype]
            urltype, proxyhost = splittype(proxy)
            host, selector = splithost(proxyhost)
            url = (host, fullurl) # Signal special case to open_*()
        else:
            proxy = None
        name = 'open_' + urltype
        self.type = urltype
        name = name.replace('-', '_')
        if not hasattr(self, name):
            if proxy:
                return self.open_unknown_proxy(proxy, fullurl, data)
            else:
                return self.open_unknown(fullurl, data)
        try:
            if data is None:
                return getattr(self, name)(url)
            else:
                return getattr(self, name)(url, data)
        except socket.error, msg:
            raise IOError, ('socket error', msg), sys.exc_info()[2]

    def open_unknown(self, fullurl, data=None):
        """Overridable interface to open unknown URL type."""
        type, url = splittype(fullurl)
        raise IOError, ('url error', 'unknown url type', type)

    def open_unknown_proxy(self, proxy, fullurl, data=None):
        """Overridable interface to open unknown URL type."""
        type, url = splittype(fullurl)
        raise IOError, ('url error', 'invalid proxy for %s' % type, proxy)

    # External interface
    def retrieve(self, url, filename=None, reporthook=None, data=None):
        """retrieve(url) returns (filename, headers) for a local object
        or (tempfilename, headers) for a remote object."""
        url = unwrap(toBytes(url))
        if self.tempcache and url in self.tempcache:
            return self.tempcache[url]
        type, url1 = splittype(url)
        if filename is None and (not type or type == 'file'):
            try:
                fp = self.open_local_file(url1)
                hdrs = fp.info()
                fp.close()
                return url2pathname(splithost(url1)[1]), hdrs
            except IOError:
                pass
        fp = self.open(url, data)
        try:
            headers = fp.info()
            if filename:
                tfp = open(filename, 'wb')
            else:
                import tempfile
                garbage, path = splittype(url)
                garbage, path = splithost(path or "")
                path, garbage = splitquery(path or "")
                path, garbage = splitattr(path or "")
                suffix = os.path.splitext(path)[1]
                (fd, filename) = tempfile.mkstemp(suffix)
                self.__tempfiles.append(filename)
                tfp = os.fdopen(fd, 'wb')
            try:
                result = filename, headers
                if self.tempcache is not None:
                    self.tempcache[url] = result
                bs = 1024*8
                size = -1
                read = 0
                blocknum = 0
                if "content-length" in headers:
                    size = int(headers["Content-Length"])
                if reporthook:
                    reporthook(blocknum, bs, size)
                while 1:
                    block = fp.read(bs)
                    if block == "":
                        break
                    read += len(block)
                    tfp.write(block)
                    blocknum += 1
                    if reporthook:
                        reporthook(blocknum, bs, size)
            finally:
                tfp.close()
        finally:
            fp.close()

        # raise exception if actual size does not match content-length header
        if size >= 0 and read < size:
            raise ContentTooShortError("retrieval incomplete: got only %i out "
                                       "of %i bytes" % (read, size), result)

        return result

    # Each method named open_<type> knows how to open that type of URL

    def open_http(self, url, data=None):
        """Use HTTP protocol."""
        import httplib
        user_passwd = None
        proxy_passwd= None
        if isinstance(url, str):
            host, selector = splithost(url)
            if host:
                user_passwd, host = splituser(host)
                host = unquote(host)
            realhost = host
        else:
            host, selector = url
            # check whether the proxy contains authorization information
            proxy_passwd, host = splituser(host)
            # now we proceed with the url we want to obtain
            urltype, rest = splittype(selector)
            url = rest
            user_passwd = None
            if urltype.lower() != 'http':
                realhost = None
            else:
                realhost, rest = splithost(rest)
                if realhost:
                    user_passwd, realhost = splituser(realhost)
                if user_passwd:
                    selector = "%s://%s%s" % (urltype, realhost, rest)
                if proxy_bypass(realhost):
                    host = realhost

            #print "proxy via http:", host, selector
        if not host: raise IOError, ('http error', 'no host given')

        if proxy_passwd:
            proxy_passwd = unquote(proxy_passwd)
            proxy_auth = base64.b64encode(proxy_passwd).strip()
        else:
            proxy_auth = None

        if user_passwd:
            user_passwd = unquote(user_passwd)
            auth = base64.b64encode(user_passwd).strip()
        else:
            auth = None
        h = httplib.HTTP(host)
        if data is not None:
            h.putrequest('POST', selector)
            h.putheader('Content-Type', 'application/x-www-form-urlencoded')
            h.putheader('Content-Length', '%d' % len(data))
        else:
            h.putrequest('GET', selector)
        if proxy_auth: h.putheader('Proxy-Authorization', 'Basic %s' % proxy_auth)
        if auth: h.putheader('Authorization', 'Basic %s' % auth)
        if realhost: h.putheader('Host', realhost)
        for args in self.addheaders: h.putheader(*args)
        h.endheaders(data)
        errcode, errmsg, headers = h.getreply()
        fp = h.getfile()
        if errcode == -1:
            if fp: fp.close()
            # something went wrong with the HTTP status line
            raise IOError, ('http protocol error', 0,
                            'got a bad status line', None)
        # According to RFC 2616, "2xx" code indicates that the client's
        # request was successfully received, understood, and accepted.
        if (200 <= errcode < 300):
            return addinfourl(fp, headers, "http:" + url, errcode)
        else:
            if data is None:
                return self.http_error(url, fp, errcode, errmsg, headers)
            else:
                return self.http_error(url, fp, errcode, errmsg, headers, data)

    def http_error(self, url, fp, errcode, errmsg, headers, data=None):
        """Handle http errors.
        Derived class can override this, or provide specific handlers
        named http_error_DDD where DDD is the 3-digit error code."""
        # First check if there's a specific handler for this error
        name = 'http_error_%d' % errcode
        if hasattr(self, name):
            method = getattr(self, name)
            if data is None:
                result = method(url, fp, errcode, errmsg, headers)
            else:
                result = method(url, fp, errcode, errmsg, headers, data)
            if result: return result
        return self.http_error_default(url, fp, errcode, errmsg, headers)

    def http_error_default(self, url, fp, errcode, errmsg, headers):
        """Default error handler: close the connection and raise IOError."""
        fp.close()
        raise IOError, ('http error', errcode, errmsg, headers)

    if _have_ssl:
        def open_https(self, url, data=None):
            """Use HTTPS protocol."""

            import httplib
            user_passwd = None
            proxy_passwd = None
            if isinstance(url, str):
                host, selector = splithost(url)
                if host:
                    user_passwd, host = splituser(host)
                    host = unquote(host)
                realhost = host
            else:
                host, selector = url
                # here, we determine, whether the proxy contains authorization information
                proxy_passwd, host = splituser(host)
                urltype, rest = splittype(selector)
                url = rest
                user_passwd = None
                if urltype.lower() != 'https':
                    realhost = None
                else:
                    realhost, rest = splithost(rest)
                    if realhost:
                        user_passwd, realhost = splituser(realhost)
                    if user_passwd:
                        selector = "%s://%s%s" % (urltype, realhost, rest)
                #print "proxy via https:", host, selector
            if not host: raise IOError, ('https error', 'no host given')
            if proxy_passwd:
                proxy_passwd = unquote(proxy_passwd)
                proxy_auth = base64.b64encode(proxy_passwd).strip()
            else:
                proxy_auth = None
            if user_passwd:
                user_passwd = unquote(user_passwd)
                auth = base64.b64encode(user_passwd).strip()
            else:
                auth = None
            h = httplib.HTTPS(host, 0,
                              key_file=self.key_file,
                              cert_file=self.cert_file,
                              context=self.context)
            if data is not None:
                h.putrequest('POST', selector)
                h.putheader('Content-Type',
                            'application/x-www-form-urlencoded')
                h.putheader('Content-Length', '%d' % len(data))
            else:
                h.putrequest('GET', selector)
            if proxy_auth: h.putheader('Proxy-Authorization', 'Basic %s' % proxy_auth)
            if auth: h.putheader('Authorization', 'Basic %s' % auth)
            if realhost: h.putheader('Host', realhost)
            for args in self.addheaders: h.putheader(*args)
            h.endheaders(data)
            errcode, errmsg, headers = h.getreply()
            fp = h.getfile()
            if errcode == -1:
                if fp: fp.close()
                # something went wrong with the HTTP status line
                raise IOError, ('http protocol error', 0,
                                'got a bad status line', None)
            # According to RFC 2616, "2xx" code indicates that the client's
            # request was successfully received, understood, and accepted.
            if (200 <= errcode < 300):
                return addinfourl(fp, headers, "https:" + url, errcode)
            else:
                if data is None:
                    return self.http_error(url, fp, errcode, errmsg, headers)
                else:
                    return self.http_error(url, fp, errcode, errmsg, headers,
                                           data)

    def open_file(self, url):
        """Use local file or FTP depending on form of URL."""
        if not isinstance(url, str):
            raise IOError, ('file error', 'proxy support for file protocol currently not implemented')
        if url[:2] == '//' and url[2:3] != '/' and url[2:12].lower() != 'localhost/':
            return self.open_ftp(url)
        else:
            return self.open_local_file(url)

    def open_local_file(self, url):
        """Use local file."""
        import mimetypes, mimetools, email.utils
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        host, file = splithost(url)
        localname = url2pathname(file)
        try:
            stats = os.stat(localname)
        except OSError, e:
            raise IOError(e.errno, e.strerror, e.filename)
        size = stats.st_size
        modified = email.utils.formatdate(stats.st_mtime, usegmt=True)
        mtype = mimetypes.guess_type(url)[0]
        headers = mimetools.Message(StringIO(
            'Content-Type: %s\nContent-Length: %d\nLast-modified: %s\n' %
            (mtype or 'text/plain', size, modified)))
        if not host:
            urlfile = file
            if file[:1] == '/':
                urlfile = 'file://' + file
            elif file[:2] == './':
                raise ValueError("local file url may start with / or file:. Unknown url of type: %s" % url)
            return addinfourl(open(localname, 'rb'),
                              headers, urlfile)
        host, port = splitport(host)
        if not port \
           and socket.gethostbyname(host) in (localhost(), thishost()):
            urlfile = file
            if file[:1] == '/':
                urlfile = 'file://' + file
            return addinfourl(open(localname, 'rb'),
                              headers, urlfile)
        raise IOError, ('local file error', 'not on local host')

    def open_ftp(self, url):
        """Use FTP protocol."""
        if not isinstance(url, str):
            raise IOError, ('ftp error', 'proxy support for ftp protocol currently not implemented')
        import mimetypes, mimetools
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        host, path = splithost(url)
        if not host: raise IOError, ('ftp error', 'no host given')
        host, port = splitport(host)
        user, host = splituser(host)
        if user: user, passwd = splitpasswd(user)
        else: passwd = None
        host = unquote(host)
        user = user or ''
        passwd = passwd or ''
        host = socket.gethostbyname(host)
        if not port:
            import ftplib
            port = ftplib.FTP_PORT
        else:
            port = int(port)
        path, attrs = splitattr(path)
        path = unquote(path)
        dirs = path.split('/')
        dirs, file = dirs[:-1], dirs[-1]
        if dirs and not dirs[0]: dirs = dirs[1:]
        if dirs and not dirs[0]: dirs[0] = '/'
        key = user, host, port, '/'.join(dirs)
        # XXX thread unsafe!
        if len(self.ftpcache) > MAXFTPCACHE:
            # Prune the cache, rather arbitrarily
            for k in self.ftpcache.keys():
                if k != key:
                    v = self.ftpcache[k]
                    del self.ftpcache[k]
                    v.close()
        try:
            if not key in self.ftpcache:
                self.ftpcache[key] = \
                    ftpwrapper(user, passwd, host, port, dirs)
            if not file: type = 'D'
            else: type = 'I'
            for attr in attrs:
                attr, value = splitvalue(attr)
                if attr.lower() == 'type' and \
                   value in ('a', 'A', 'i', 'I', 'd', 'D'):
                    type = value.upper()
            (fp, retrlen) = self.ftpcache[key].retrfile(file, type)
            mtype = mimetypes.guess_type("ftp:" + url)[0]
            headers = ""
            if mtype:
                headers += "Content-Type: %s\n" % mtype
            if retrlen is not None and retrlen >= 0:
                headers += "Content-Length: %d\n" % retrlen
            headers = mimetools.Message(StringIO(headers))
            return addinfourl(fp, headers, "ftp:" + url)
        except ftperrors(), msg:
            raise IOError, ('ftp error', msg), sys.exc_info()[2]

    def open_data(self, url, data=None):
        """Use "data" URL."""
        if not isinstance(url, str):
            raise IOError, ('data error', 'proxy support for data protocol currently not implemented')
        # ignore POSTed data
        #
        # syntax of data URLs:
        # dataurl   := "data:" [ mediatype ] [ ";base64" ] "," data
        # mediatype := [ type "/" subtype ] *( ";" parameter )
        # data      := *urlchar
        # parameter := attribute "=" value
        import mimetools
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        try:
            [type, data] = url.split(',', 1)
        except ValueError:
            raise IOError, ('data error', 'bad data URL')
        if not type:
            type = 'text/plain;charset=US-ASCII'
        semi = type.rfind(';')
        if semi >= 0 and '=' not in type[semi:]:
            encoding = type[semi+1:]
            type = type[:semi]
        else:
            encoding = ''
        msg = []
        msg.append('Date: %s'%time.strftime('%a, %d %b %Y %H:%M:%S GMT',
                                            time.gmtime(time.time())))
        msg.append('Content-type: %s' % type)
        if encoding == 'base64':
            data = base64.decodestring(data)
        else:
            data = unquote(data)
        msg.append('Content-Length: %d' % len(data))
        msg.append('')
        msg.append(data)
        msg = '\n'.join(msg)
        f = StringIO(msg)
        headers = mimetools.Message(f, 0)
        #f.fileno = None     # needed for addinfourl
        return addinfourl(f, headers, url)


class FancyURLopener(URLopener):
    """Derived class with handlers for errors we can handle (perhaps)."""

    def __init__(self, *args, **kwargs):
        URLopener.__init__(self, *args, **kwargs)
        self.auth_cache = {}
        self.tries = 0
        self.maxtries = 10

    def http_error_default(self, url, fp, errcode, errmsg, headers):
        """Default error handling -- don't raise an exception."""
        return addinfourl(fp, headers, "http:" + url, errcode)

    def http_error_302(self, url, fp, errcode, errmsg, headers, data=None):
        """Error 302 -- relocated (temporarily)."""
        self.tries += 1
        if self.maxtries and self.tries >= self.maxtries:
            if hasattr(self, "http_error_500"):
                meth = self.http_error_500
            else:
                meth = self.http_error_default
            self.tries = 0
            return meth(url, fp, 500,
                        "Internal Server Error: Redirect Recursion", headers)
        result = self.redirect_internal(url, fp, errcode, errmsg, headers,
                                        data)
        self.tries = 0
        return result

    def redirect_internal(self, url, fp, errcode, errmsg, headers, data):
        if 'location' in headers:
            newurl = headers['location']
        elif 'uri' in headers:
            newurl = headers['uri']
        else:
            return
        fp.close()
        # In case the server sent a relative URL, join with original:
        newurl = basejoin(self.type + ":" + url, newurl)

        # For security reasons we do not allow redirects to protocols
        # other than HTTP, HTTPS or FTP.
        newurl_lower = newurl.lower()
        if not (newurl_lower.startswith('http://') or
                newurl_lower.startswith('https://') or
                newurl_lower.startswith('ftp://')):
            raise IOError('redirect error', errcode,
                          errmsg + " - Redirection to url '%s' is not allowed" %
                          newurl,
                          headers)

        return self.open(newurl)

    def http_error_301(self, url, fp, errcode, errmsg, headers, data=None):
        """Error 301 -- also relocated (permanently)."""
        return self.http_error_302(url, fp, errcode, errmsg, headers, data)

    def http_error_303(self, url, fp, errcode, errmsg, headers, data=None):
        """Error 303 -- also relocated (essentially identical to 302)."""
        return self.http_error_302(url, fp, errcode, errmsg, headers, data)

    def http_error_307(self, url, fp, errcode, errmsg, headers, data=None):
        """Error 307 -- relocated, but turn POST into error."""
        if data is None:
            return self.http_error_302(url, fp, errcode, errmsg, headers, data)
        else:
            return self.http_error_default(url, fp, errcode, errmsg, headers)

    def http_error_401(self, url, fp, errcode, errmsg, headers, data=None):
        """Error 401 -- authentication required.
        This function supports Basic authentication only."""
        if not 'www-authenticate' in headers:
            URLopener.http_error_default(self, url, fp,
                                         errcode, errmsg, headers)
        stuff = headers['www-authenticate']
        import re
        match = re.match('[ \t]*([^ \t]+)[ \t]+realm="([^"]*)"', stuff)
        if not match:
            URLopener.http_error_default(self, url, fp,
                                         errcode, errmsg, headers)
        scheme, realm = match.groups()
        if scheme.lower() != 'basic':
            URLopener.http_error_default(self, url, fp,
                                         errcode, errmsg, headers)
        name = 'retry_' + self.type + '_basic_auth'
        if data is None:
            return getattr(self,name)(url, realm)
        else:
            return getattr(self,name)(url, realm, data)

    def http_error_407(self, url, fp, errcode, errmsg, headers, data=None):
        """Error 407 -- proxy authentication required.
        This function supports Basic authentication only."""
        if not 'proxy-authenticate' in headers:
            URLopener.http_error_default(self, url, fp,
                                         errcode, errmsg, headers)
        stuff = headers['proxy-authenticate']
        import re
        match = re.match('[ \t]*([^ \t]+)[ \t]+realm="([^"]*)"', stuff)
        if not match:
            URLopener.http_error_default(self, url, fp,
                                         errcode, errmsg, headers)
        scheme, realm = match.groups()
        if scheme.lower() != 'basic':
            URLopener.http_error_default(self, url, fp,
                                         errcode, errmsg, headers)
        name = 'retry_proxy_' + self.type + '_basic_auth'
        if data is None:
            return getattr(self,name)(url, realm)
        else:
            return getattr(self,name)(url, realm, data)

    def retry_proxy_http_basic_auth(self, url, realm, data=None):
        host, selector = splithost(url)
        newurl = 'http://' + host + selector
        proxy = self.proxies['http']
        urltype, proxyhost = splittype(proxy)
        proxyhost, proxyselector = splithost(proxyhost)
        i = proxyhost.find('@') + 1
        proxyhost = proxyhost[i:]
        user, passwd = self.get_user_passwd(proxyhost, realm, i)
        if not (user or passwd): return None
        proxyhost = quote(user, safe='') + ':' + quote(passwd, safe='') + '@' + proxyhost
        self.proxies['http'] = 'http://' + proxyhost + proxyselector
        if data is None:
            return self.open(newurl)
        else:
            return self.open(newurl, data)

    def retry_proxy_https_basic_auth(self, url, realm, data=None):
        host, selector = splithost(url)
        newurl = 'https://' + host + selector
        proxy = self.proxies['https']
        urltype, proxyhost = splittype(proxy)
        proxyhost, proxyselector = splithost(proxyhost)
        i = proxyhost.find('@') + 1
        proxyhost = proxyhost[i:]
        user, passwd = self.get_user_passwd(proxyhost, realm, i)
        if not (user or passwd): return None
        proxyhost = quote(user, safe='') + ':' + quote(passwd, safe='') + '@' + proxyhost
        self.proxies['https'] = 'https://' + proxyhost + proxyselector
        if data is None:
            return self.open(newurl)
        else:
            return self.open(newurl, data)

    def retry_http_basic_auth(self, url, realm, data=None):
        host, selector = splithost(url)
        i = host.find('@') + 1
        host = host[i:]
        user, passwd = self.get_user_passwd(host, realm, i)
        if not (user or passwd): return None
        host = quote(user, safe='') + ':' + quote(passwd, safe='') + '@' + host
        newurl = 'http://' + host + selector
        if data is None:
            return self.open(newurl)
        else:
            return self.open(newurl, data)

    def retry_https_basic_auth(self, url, realm, data=None):
        host, selector = splithost(url)
        i = host.find('@') + 1
        host = host[i:]
        user, passwd = self.get_user_passwd(host, realm, i)
        if not (user or passwd): return None
        host = quote(user, safe='') + ':' + quote(passwd, safe='') + '@' + host
        newurl = 'https://' + host + selector
        if data is None:
            return self.open(newurl)
        else:
            return self.open(newurl, data)

    def get_user_passwd(self, host, realm, clear_cache=0):
        key = realm + '@' + host.lower()
        if key in self.auth_cache:
            if clear_cache:
                del self.auth_cache[key]
            else:
                return self.auth_cache[key]
        user, passwd = self.prompt_user_passwd(host, realm)
        if user or passwd: self.auth_cache[key] = (user, passwd)
        return user, passwd

    def prompt_user_passwd(self, host, realm):
        """Override this in a GUI environment!"""
        import getpass
        try:
            user = raw_input("Enter username for %s at %s: " % (realm,
                                                                host))
            passwd = getpass.getpass("Enter password for %s in %s at %s: " %
                (user, realm, host))
            return user, passwd
        except KeyboardInterrupt:
            print
            return None, None


# Utility functions

_localhost = None
def localhost():
    """Return the IP address of the magic hostname 'localhost'."""
    global _localhost
    if _localhost is None:
        _localhost = socket.gethostbyname('localhost')
    return _localhost

_thishost = None
def thishost():
    """Return the IP address of the current host."""
    global _thishost
    if _thishost is None:
        try:
            _thishost = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            _thishost = socket.gethostbyname('localhost')
    return _thishost

_ftperrors = None
def ftperrors():
    """Return the set of errors raised by the FTP class."""
    global _ftperrors
    if _ftperrors is None:
        import ftplib
        _ftperrors = ftplib.all_errors
    return _ftperrors

_noheaders = None
def noheaders():
    """Return an empty mimetools.Message object."""
    global _noheaders
    if _noheaders is None:
        import mimetools
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        _noheaders = mimetools.Message(StringIO(), 0)
        _noheaders.fp.close()   # Recycle file descriptor
    return _noheaders


# Utility classes

class ftpwrapper:
    """Class used by open_ftp() for cache of open FTP connections."""

    def __init__(self, user, passwd, host, port, dirs,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                 persistent=True):
        self.user = user
        self.passwd = passwd
        self.host = host
        self.port = port
        self.dirs = dirs
        self.timeout = timeout
        self.refcount = 0
        self.keepalive = persistent
        try:
            self.init()
        except:
            self.close()
            raise

    def init(self):
        import ftplib
        self.busy = 0
        self.ftp = ftplib.FTP()
        self.ftp.connect(self.host, self.port, self.timeout)
        self.ftp.login(self.user, self.passwd)
        _target = '/'.join(self.dirs)
        self.ftp.cwd(_target)

    def retrfile(self, file, type):
        import ftplib
        self.endtransfer()
        if type in ('d', 'D'): cmd = 'TYPE A'; isdir = 1
        else: cmd = 'TYPE ' + type; isdir = 0
        try:
            self.ftp.voidcmd(cmd)
        except ftplib.all_errors:
            self.init()
            self.ftp.voidcmd(cmd)
        conn = None
        if file and not isdir:
            # Try to retrieve as a file
            try:
                cmd = 'RETR ' + file
                conn, retrlen = self.ftp.ntransfercmd(cmd)
            except ftplib.error_perm, reason:
                if str(reason)[:3] != '550':
                    raise IOError, ('ftp error', reason), sys.exc_info()[2]
        if not conn:
            # Set transfer mode to ASCII!
            self.ftp.voidcmd('TYPE A')
            # Try a directory listing. Verify that directory exists.
            if file:
                pwd = self.ftp.pwd()
                try:
                    try:
                        self.ftp.cwd(file)
                    except ftplib.error_perm, reason:
                        raise IOError, ('ftp error', reason), sys.exc_info()[2]
                finally:
                    self.ftp.cwd(pwd)
                cmd = 'LIST ' + file
            else:
                cmd = 'LIST'
            conn, retrlen = self.ftp.ntransfercmd(cmd)
        self.busy = 1
        ftpobj = addclosehook(conn.makefile('rb'), self.file_close)
        self.refcount += 1
        conn.close()
        # Pass back both a suitably decorated object and a retrieval length
        return (ftpobj, retrlen)

    def endtransfer(self):
        if not self.busy:
            return
        self.busy = 0
        try:
            self.ftp.voidresp()
        except ftperrors():
            pass

    def close(self):
        self.keepalive = False
        if self.refcount <= 0:
            self.real_close()

    def file_close(self):
        self.endtransfer()
        self.refcount -= 1
        if self.refcount <= 0 and not self.keepalive:
            self.real_close()

    def real_close(self):
        self.endtransfer()
        try:
            self.ftp.close()
        except ftperrors():
            pass

class addbase:
    """Base class for addinfo and addclosehook."""

    def __init__(self, fp):
        self.fp = fp
        self.read = self.fp.read
        self.readline = self.fp.readline
        if hasattr(self.fp, "readlines"): self.readlines = self.fp.readlines
        if hasattr(self.fp, "fileno"):
            self.fileno = self.fp.fileno
        else:
            self.fileno = lambda: None
        if hasattr(self.fp, "__iter__"):
            self.__iter__ = self.fp.__iter__
            if hasattr(self.fp, "next"):
                self.next = self.fp.next

    def __repr__(self):
        return '<%s at %r whose fp = %r>' % (self.__class__.__name__,
                                             id(self), self.fp)

    def close(self):
        self.read = None
        self.readline = None
        self.readlines = None
        self.fileno = None
        if self.fp: self.fp.close()
        self.fp = None

class addclosehook(addbase):
    """Class to add a close hook to an open file."""

    def __init__(self, fp, closehook, *hookargs):
        addbase.__init__(self, fp)
        self.closehook = closehook
        self.hookargs = hookargs

    def close(self):
        try:
            closehook = self.closehook
            hookargs = self.hookargs
            if closehook:
                self.closehook = None
                self.hookargs = None
                closehook(*hookargs)
        finally:
            addbase.close(self)


class addinfo(addbase):
    """class to add an info() method to an open file."""

    def __init__(self, fp, headers):
        addbase.__init__(self, fp)
        self.headers = headers

    def info(self):
        return self.headers

class addinfourl(addbase):
    """class to add info() and geturl() methods to an open file."""

    def __init__(self, fp, headers, url, code=None):
        addbase.__init__(self, fp)
        self.headers = headers
        self.url = url
        self.code = code

    def info(self):
        return self.headers

    def getcode(self):
        return self.code

    def geturl(self):
        return self.url


# Utilities to parse URLs (most of these return None for missing parts):
# unwrap('<URL:type://host/path>') --> 'type://host/path'
# splittype('type:opaquestring') --> 'type', 'opaquestring'
# splithost('//host[:port]/path') --> 'host[:port]', '/path'
# splituser('user[:passwd]@host[:port]') --> 'user[:passwd]', 'host[:port]'
# splitpasswd('user:passwd') -> 'user', 'passwd'
# splitport('host:port') --> 'host', 'port'
# splitquery('/path?query') --> '/path', 'query'
# splittag('/path#tag') --> '/path', 'tag'
# splitattr('/path;attr1=value1;attr2=value2;...') ->
#   '/path', ['attr1=value1', 'attr2=value2', ...]
# splitvalue('attr=value') --> 'attr', 'value'
# unquote('abc%20def') -> 'abc def'
# quote('abc def') -> 'abc%20def')

try:
    unicode
except NameError:
    def _is_unicode(x):
        return 0
else:
    def _is_unicode(x):
        return isinstance(x, unicode)

def toBytes(url):
    """toBytes(u"URL") --> 'URL'."""
    # Most URL schemes require ASCII. If that changes, the conversion
    # can be relaxed
    if _is_unicode(url):
        try:
            url = url.encode("ASCII")
        except UnicodeError:
            raise UnicodeError("URL " + repr(url) +
                               " contains non-ASCII characters")
    return url

def unwrap(url):
    """unwrap('<URL:type://host/path>') --> 'type://host/path'."""
    url = url.strip()
    if url[:1] == '<' and url[-1:] == '>':
        url = url[1:-1].strip()
    if url[:4] == 'URL:': url = url[4:].strip()
    return url

_typeprog = None
def splittype(url):
    """splittype('type:opaquestring') --> 'type', 'opaquestring'."""
    global _typeprog
    if _typeprog is None:
        import re
        _typeprog = re.compile('^([^/:]+):')

    match = _typeprog.match(url)
    if match:
        scheme = match.group(1)
        return scheme.lower(), url[len(scheme) + 1:]
    return None, url

_hostprog = None
def splithost(url):
    """splithost('//host[:port]/path') --> 'host[:port]', '/path'."""
    global _hostprog
    if _hostprog is None:
        import re
        _hostprog = re.compile('^//([^/?]*)(.*)$')

    match = _hostprog.match(url)
    if match:
        host_port = match.group(1)
        path = match.group(2)
        if path and not path.startswith('/'):
            path = '/' + path
        return host_port, path
    return None, url

_userprog = None
def splituser(host):
    """splituser('user[:passwd]@host[:port]') --> 'user[:passwd]', 'host[:port]'."""
    global _userprog
    if _userprog is None:
        import re
        _userprog = re.compile('^(.*)@(.*)$')

    match = _userprog.match(host)
    if match: return match.group(1, 2)
    return None, host

_passwdprog = None
def splitpasswd(user):
    """splitpasswd('user:passwd') -> 'user', 'passwd'."""
    global _passwdprog
    if _passwdprog is None:
        import re
        _passwdprog = re.compile('^([^:]*):(.*)$',re.S)

    match = _passwdprog.match(user)
    if match: return match.group(1, 2)
    return user, None

# splittag('/path#tag') --> '/path', 'tag'
_portprog = None
def splitport(host):
    """splitport('host:port') --> 'host', 'port'."""
    global _portprog
    if _portprog is None:
        import re
        _portprog = re.compile('^(.*):([0-9]*)$')

    match = _portprog.match(host)
    if match:
        host, port = match.groups()
        if port:
            return host, port
    return host, None

_nportprog = None
def splitnport(host, defport=-1):
    """Split host and port, returning numeric port.
    Return given default port if no ':' found; defaults to -1.
    Return numerical port if a valid number are found after ':'.
    Return None if ':' but not a valid number."""
    global _nportprog
    if _nportprog is None:
        import re
        _nportprog = re.compile('^(.*):(.*)$')

    match = _nportprog.match(host)
    if match:
        host, port = match.group(1, 2)
        if port:
            try:
                nport = int(port)
            except ValueError:
                nport = None
            return host, nport
    return host, defport

_queryprog = None
def splitquery(url):
    """splitquery('/path?query') --> '/path', 'query'."""
    global _queryprog
    if _queryprog is None:
        import re
        _queryprog = re.compile('^(.*)\?([^?]*)$')

    match = _queryprog.match(url)
    if match: return match.group(1, 2)
    return url, None

_tagprog = None
def splittag(url):
    """splittag('/path#tag') --> '/path', 'tag'."""
    global _tagprog
    if _tagprog is None:
        import re
        _tagprog = re.compile('^(.*)#([^#]*)$')

    match = _tagprog.match(url)
    if match: return match.group(1, 2)
    return url, None

def splitattr(url):
    """splitattr('/path;attr1=value1;attr2=value2;...') ->
        '/path', ['attr1=value1', 'attr2=value2', ...]."""
    words = url.split(';')
    return words[0], words[1:]

_valueprog = None
def splitvalue(attr):
    """splitvalue('attr=value') --> 'attr', 'value'."""
    global _valueprog
    if _valueprog is None:
        import re
        _valueprog = re.compile('^([^=]*)=(.*)$')

    match = _valueprog.match(attr)
    if match: return match.group(1, 2)
    return attr, None

# urlparse contains a duplicate of this method to avoid a circular import.  If
# you update this method, also update the copy in urlparse.  This code
# duplication does not exist in Python3.

_hexdig = '0123456789ABCDEFabcdef'
_hextochr = dict((a + b, chr(int(a + b, 16)))
                 for a in _hexdig for b in _hexdig)
_asciire = re.compile('([\x00-\x7f]+)')

def unquote(s):
    """unquote('abc%20def') -> 'abc def'."""
    if _is_unicode(s):
        if '%' not in s:
            return s
        bits = _asciire.split(s)
        res = [bits[0]]
        append = res.append
        for i in range(1, len(bits), 2):
            append(unquote(str(bits[i])).decode('latin1'))
            append(bits[i + 1])
        return ''.join(res)

    bits = s.split('%')
    # fastpath
    if len(bits) == 1:
        return s
    res = [bits[0]]
    append = res.append
    for item in bits[1:]:
        try:
            append(_hextochr[item[:2]])
            append(item[2:])
        except KeyError:
            append('%')
            append(item)
    return ''.join(res)

def unquote_plus(s):
    """unquote('%7e/abc+def') -> '~/abc def'"""
    s = s.replace('+', ' ')
    return unquote(s)

always_safe = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
               'abcdefghijklmnopqrstuvwxyz'
               '0123456789' '_.-')
_safe_map = {}
for i, c in zip(xrange(256), str(bytearray(xrange(256)))):
    _safe_map[c] = c if (i < 128 and c in always_safe) else '%{:02X}'.format(i)
_safe_quoters = {}

def quote(s, safe='/'):
    """quote('abc def') -> 'abc%20def'

    Each part of a URL, e.g. the path info, the query, etc., has a
    different set of reserved characters that must be quoted.

    RFC 2396 Uniform Resource Identifiers (URI): Generic Syntax lists
    the following reserved characters.

    reserved    = ";" | "/" | "?" | ":" | "@" | "&" | "=" | "+" |
                  "$" | ","

    Each of these characters is reserved in some component of a URL,
    but not necessarily in all of them.

    By default, the quote function is intended for quoting the path
    section of a URL.  Thus, it will not encode '/'.  This character
    is reserved, but in typical usage the quote function is being
    called on a path where the existing slash characters are used as
    reserved characters.
    """
    # fastpath
    if not s:
        if s is None:
            raise TypeError('None object cannot be quoted')
        return s
    cachekey = (safe, always_safe)
    try:
        (quoter, safe) = _safe_quoters[cachekey]
    except KeyError:
        safe_map = _safe_map.copy()
        safe_map.update([(c, c) for c in safe])
        quoter = safe_map.__getitem__
        safe = always_safe + safe
        _safe_quoters[cachekey] = (quoter, safe)
    if not s.rstrip(safe):
        return s
    return ''.join(map(quoter, s))

def quote_plus(s, safe=''):
    """Quote the query fragment of a URL; replacing ' ' with '+'"""
    if ' ' in s:
        s = quote(s, safe + ' ')
        return s.replace(' ', '+')
    return quote(s, safe)

def urlencode(query, doseq=0):
    """Encode a sequence of two-element tuples or dictionary into a URL query string.

    If any values in the query arg are sequences and doseq is true, each
    sequence element is converted to a separate parameter.

    If the query arg is a sequence of two-element tuples, the order of the
    parameters in the output will match the order of parameters in the
    input.
    """

    if hasattr(query,"items"):
        # mapping objects
        query = query.items()
    else:
        # it's a bother at times that strings and string-like objects are
        # sequences...
        try:
            # non-sequence items should not work with len()
            # non-empty strings will fail this
            if len(query) and not isinstance(query[0], tuple):
                raise TypeError
            # zero-length sequences of all types will get here and succeed,
            # but that's a minor nit - since the original implementation
            # allowed empty dicts that type of behavior probably should be
            # preserved for consistency
        except TypeError:
            ty,va,tb = sys.exc_info()
            raise TypeError, "not a valid non-string sequence or mapping object", tb

    l = []
    if not doseq:
        # preserve old behavior
        for k, v in query:
            k = quote_plus(str(k))
            v = quote_plus(str(v))
            l.append(k + '=' + v)
    else:
        for k, v in query:
            k = quote_plus(str(k))
            if isinstance(v, str):
                v = quote_plus(v)
                l.append(k + '=' + v)
            elif _is_unicode(v):
                # is there a reasonable way to convert to ASCII?
                # encode generates a string, but "replace" or "ignore"
                # lose information and "strict" can raise UnicodeError
                v = quote_plus(v.encode("ASCII","replace"))
                l.append(k + '=' + v)
            else:
                try:
                    # is this a sufficient test for sequence-ness?
                    len(v)
                except TypeError:
                    # not a sequence
                    v = quote_plus(str(v))
                    l.append(k + '=' + v)
                else:
                    # loop over the sequence
                    for elt in v:
                        l.append(k + '=' + quote_plus(str(elt)))
    return '&'.join(l)

# Proxy handling
def getproxies_environment():
    """Return a dictionary of scheme -> proxy server URL mappings.

    Scan the environment for variables named <scheme>_proxy;
    this seems to be the standard convention.  If you need a
    different way, you can pass a proxies dictionary to the
    [Fancy]URLopener constructor.

    """
    proxies = {}
    for name, value in os.environ.items():
        name = name.lower()
        if value and name[-6:] == '_proxy':
            proxies[name[:-6]] = value
    return proxies

def proxy_bypass_environment(host):
    """Test if proxies should not be used for a particular host.

    Checks the environment for a variable named no_proxy, which should
    be a list of DNS suffixes separated by commas, or '*' for all hosts.
    """
    no_proxy = os.environ.get('no_proxy', '') or os.environ.get('NO_PROXY', '')
    # '*' is special case for always bypass
    if no_proxy == '*':
        return 1
    # strip port off host
    hostonly, port = splitport(host)
    # check if the host ends with any of the DNS suffixes
    no_proxy_list = [proxy.strip() for proxy in no_proxy.split(',')]
    for name in no_proxy_list:
        if name and (hostonly.endswith(name) or host.endswith(name)):
            return 1
    # otherwise, don't bypass
    return 0


if sys.platform == 'darwin':
    from _scproxy import _get_proxy_settings, _get_proxies

    def proxy_bypass_macosx_sysconf(host):
        """
        Return True iff this host shouldn't be accessed using a proxy

        This function uses the MacOSX framework SystemConfiguration
        to fetch the proxy information.
        """
        import re
        import socket
        from fnmatch import fnmatch

        hostonly, port = splitport(host)

        def ip2num(ipAddr):
            parts = ipAddr.split('.')
            parts = map(int, parts)
            if len(parts) != 4:
                parts = (parts + [0, 0, 0, 0])[:4]
            return (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]

        proxy_settings = _get_proxy_settings()

        # Check for simple host names:
        if '.' not in host:
            if proxy_settings['exclude_simple']:
                return True

        hostIP = None

        for value in proxy_settings.get('exceptions', ()):
            # Items in the list are strings like these: *.local, 169.254/16
            if not value: continue

            m = re.match(r"(\d+(?:\.\d+)*)(/\d+)?", value)
            if m is not None:
                if hostIP is None:
                    try:
                        hostIP = socket.gethostbyname(hostonly)
                        hostIP = ip2num(hostIP)
                    except socket.error:
                        continue

                base = ip2num(m.group(1))
                mask = m.group(2)
                if mask is None:
                    mask = 8 * (m.group(1).count('.') + 1)

                else:
                    mask = int(mask[1:])
                mask = 32 - mask

                if (hostIP >> mask) == (base >> mask):
                    return True

            elif fnmatch(host, value):
                return True

        return False

    def getproxies_macosx_sysconf():
        """Return a dictionary of scheme -> proxy server URL mappings.

        This function uses the MacOSX framework SystemConfiguration
        to fetch the proxy information.
        """
        return _get_proxies()

    def proxy_bypass(host):
        if getproxies_environment():
            return proxy_bypass_environment(host)
        else:
            return proxy_bypass_macosx_sysconf(host)

    def getproxies():
        return getproxies_environment() or getproxies_macosx_sysconf()

elif os.name == 'nt':
    def getproxies_registry():
        """Return a dictionary of scheme -> proxy server URL mappings.

        Win32 uses the registry to store proxies.

        """
        proxies = {}
        try:
            import _winreg
        except ImportError:
            # Std module, so should be around - but you never know!
            return proxies
        try:
            internetSettings = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Internet Settings')
            proxyEnable = _winreg.QueryValueEx(internetSettings,
                                               'ProxyEnable')[0]
            if proxyEnable:
                # Returned as Unicode but problems if not converted to ASCII
                proxyServer = str(_winreg.QueryValueEx(internetSettings,
                                                       'ProxyServer')[0])
                if '=' in proxyServer:
                    # Per-protocol settings
                    for p in proxyServer.split(';'):
                        protocol, address = p.split('=', 1)
                        # See if address has a type:// prefix
                        import re
                        if not re.match('^([^/:]+)://', address):
                            address = '%s://%s' % (protocol, address)
                        proxies[protocol] = address
                else:
                    # Use one setting for all protocols
                    if proxyServer[:5] == 'http:':
                        proxies['http'] = proxyServer
                    else:
                        proxies['http'] = 'http://%s' % proxyServer
                        proxies['https'] = 'https://%s' % proxyServer
                        proxies['ftp'] = 'ftp://%s' % proxyServer
            internetSettings.Close()
        except (WindowsError, ValueError, TypeError):
            # Either registry key not found etc, or the value in an
            # unexpected format.
            # proxies already set up to be empty so nothing to do
            pass
        return proxies

    def getproxies():
        """Return a dictionary of scheme -> proxy server URL mappings.

        Returns settings gathered from the environment, if specified,
        or the registry.

        """
        return getproxies_environment() or getproxies_registry()

    def proxy_bypass_registry(host):
        try:
            import _winreg
            import re
        except ImportError:
            # Std modules, so should be around - but you never know!
            return 0
        try:
            internetSettings = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Internet Settings')
            proxyEnable = _winreg.QueryValueEx(internetSettings,
                                               'ProxyEnable')[0]
            proxyOverride = str(_winreg.QueryValueEx(internetSettings,
                                                     'ProxyOverride')[0])
            # ^^^^ Returned as Unicode but problems if not converted to ASCII
        except WindowsError:
            return 0
        if not proxyEnable or not proxyOverride:
            return 0
        # try to make a host list from name and IP address.
        rawHost, port = splitport(host)
        host = [rawHost]
        try:
            addr = socket.gethostbyname(rawHost)
            if addr != rawHost:
                host.append(addr)
        except socket.error:
            pass
        try:
            fqdn = socket.getfqdn(rawHost)
            if fqdn != rawHost:
                host.append(fqdn)
        except socket.error:
            pass
        # make a check value list from the registry entry: replace the
        # '<local>' string by the localhost entry and the corresponding
        # canonical entry.
        proxyOverride = proxyOverride.split(';')
        # now check if we match one of the registry values.
        for test in proxyOverride:
            if test == '<local>':
                if '.' not in rawHost:
                    return 1
            test = test.replace(".", r"\.")     # mask dots
            test = test.replace("*", r".*")     # change glob sequence
            test = test.replace("?", r".")      # change glob char
            for val in host:
                # print "%s <--> %s" %( test, val )
                if re.match(test, val, re.I):
                    return 1
        return 0

    def proxy_bypass(host):
        """Return a dictionary of scheme -> proxy server URL mappings.

        Returns settings gathered from the environment, if specified,
        or the registry.

        """
        if getproxies_environment():
            return proxy_bypass_environment(host)
        else:
            return proxy_bypass_registry(host)

else:
    # By default use environment variables
    getproxies = getproxies_environment
    proxy_bypass = proxy_bypass_environment

# Test and time quote() and unquote()
def test1():
    s = ''
    for i in range(256): s = s + chr(i)
    s = s*4
    t0 = time.time()
    qs = quote(s)
    uqs = unquote(qs)
    t1 = time.time()
    if uqs != s:
        print 'Wrong!'
    print repr(s)
    print repr(qs)
    print repr(uqs)
    print round(t1 - t0, 3), 'sec'


def reporthook(blocknum, blocksize, totalsize):
    # Report during remote transfers
    print "Block number: %d, Block size: %d, Total size: %d" % (
        blocknum, blocksize, totalsize)
