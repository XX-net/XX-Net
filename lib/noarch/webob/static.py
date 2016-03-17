import mimetypes
import os

from webob import exc
from webob.dec import wsgify
from webob.response import Response

__all__ = [
    'FileApp', 'DirectoryApp',
]

mimetypes._winreg = None # do not load mimetypes from windows registry
mimetypes.add_type('text/javascript', '.js') # stdlib default is application/x-javascript
mimetypes.add_type('image/x-icon', '.ico') # not among defaults

BLOCK_SIZE = 1<<16


class FileApp(object):
    """An application that will send the file at the given filename.

    Adds a mime type based on `mimetypes.guess_type()`.
    """

    def __init__(self, filename, **kw):
        self.filename = filename
        content_type, content_encoding = mimetypes.guess_type(filename)
        kw.setdefault('content_type', content_type)
        kw.setdefault('content_encoding', content_encoding)
        kw.setdefault('accept_ranges', 'bytes')
        self.kw = kw
        # Used for testing purpose
        self._open = open

    @wsgify
    def __call__(self, req):
        if req.method not in ('GET', 'HEAD'):
            return exc.HTTPMethodNotAllowed("You cannot %s a file" %
                                            req.method)
        try:
            stat = os.stat(self.filename)
        except (IOError, OSError) as e:
            msg = "Can't open %r: %s" % (self.filename, e)
            return exc.HTTPNotFound(comment=msg)

        try:
            file = self._open(self.filename, 'rb')
        except (IOError, OSError) as e:
            msg = "You are not permitted to view this file (%s)" % e
            return exc.HTTPForbidden(msg)

        if 'wsgi.file_wrapper' in req.environ:
            app_iter = req.environ['wsgi.file_wrapper'](file, BLOCK_SIZE)
        else:
            app_iter = FileIter(file)

        return Response(
            app_iter = app_iter,
            content_length = stat.st_size,
            last_modified = stat.st_mtime,
            #@@ etag
            **self.kw
        ).conditional_response_app


class FileIter(object):
    def __init__(self, file):
        self.file = file

    def app_iter_range(self, seek=None, limit=None, block_size=None):
        """Iter over the content of the file.

        You can set the `seek` parameter to read the file starting from a
        specific position.

        You can set the `limit` parameter to read the file up to specific
        position.

        Finally, you can change the number of bytes read at once by setting the
        `block_size` parameter.
        """

        if block_size is None:
            block_size = BLOCK_SIZE

        if seek:
            self.file.seek(seek)
            if limit is not None:
                limit -= seek
        try:
            while True:
                data = self.file.read(min(block_size, limit)
                                      if limit is not None
                                      else block_size)
                if not data:
                    return
                yield data
                if limit is not None:
                    limit -= len(data)
                    if limit <= 0:
                        return
        finally:
            self.file.close()

    __iter__ = app_iter_range


class DirectoryApp(object):
    """An application that serves up the files in a given directory.

    This will serve index files (by default ``index.html``), or set
    ``index_page=None`` to disable this.  If you set
    ``hide_index_with_redirect=True`` (it defaults to False) then
    requests to, e.g., ``/index.html`` will be redirected to ``/``.

    To customize `FileApp` instances creation (which is what actually
    serves the responses), override the `make_fileapp` method.
    """

    def __init__(self, path, index_page='index.html', hide_index_with_redirect=False,
                 **kw):
        self.path = os.path.abspath(path)
        if not self.path.endswith(os.path.sep):
            self.path += os.path.sep
        if not os.path.isdir(self.path):
            raise IOError(
                "Path does not exist or is not directory: %r" % self.path)
        self.index_page = index_page
        self.hide_index_with_redirect = hide_index_with_redirect
        self.fileapp_kw = kw

    def make_fileapp(self, path):
        return FileApp(path, **self.fileapp_kw)

    @wsgify
    def __call__(self, req):
        path = os.path.abspath(os.path.join(self.path,
                                            req.path_info.lstrip('/')))
        if os.path.isdir(path) and self.index_page:
            return self.index(req, path)
        if (self.index_page and self.hide_index_with_redirect
            and path.endswith(os.path.sep + self.index_page)):
            new_url = req.path_url.rsplit('/', 1)[0]
            new_url += '/'
            if req.query_string:
                new_url += '?' + req.query_string
            return Response(
                status=301,
                location=new_url)
        if not os.path.isfile(path):
            return exc.HTTPNotFound(comment=path)
        elif not path.startswith(self.path):
            return exc.HTTPForbidden()
        else:
            return self.make_fileapp(path)

    def index(self, req, path):
        index_path = os.path.join(path, self.index_page)
        if not os.path.isfile(index_path):
            return exc.HTTPNotFound(comment=index_path)
        if not req.path_info.endswith('/'):
            url = req.path_url + '/'
            if req.query_string:
                url += '?' + req.query_string
            return Response(
                status=301,
                location=url)
        return self.make_fileapp(index_path)
