# Copyright (c) 2009-2010 Denis Bilenko. See LICENSE for details.
import sys
import traceback
from urllib import unquote
from datetime import datetime
socket = __import__('socket')

import gevent
from gevent.http import HTTPServer
from gevent.hub import GreenletExit


__all__ = ['WSGIServer',
           'WSGIHandler']


class WSGIHandler(object):

    def __init__(self, request, server):
        self.request = request
        self.server = server
        self.code = None
        self.reason = None
        self.headers = None
        self.data = []

    def start_response(self, status, headers, exc_info=None):
        if not exc_info:
            assert self.reason is None, 'start_response was already called'
        else:
            self.data = []
        code, self.reason = status.split(' ', 1)
        self.code = int(code)
        self.headers = headers
        return self.write

    def write(self, data):
        self.data.append(data)

    def end(self, env):
        assert self.headers is not None, 'Application did not call start_response()'
        has_content_length = False
        for header, value in self.headers:
            self.request.add_output_header(header, str(value))
            if header == 'Content-Length':
                has_content_length = True
        data = ''.join(self.data)
        if not has_content_length:
            self.request.add_output_header('Content-Length', str(len(data)))

        # QQQ work around bug in libevent 2.0.2 (and probably in older)
        if (self.request.find_input_header('Transfer-Encoding') or '').lower() == 'chunked':
            # if input is chunked, libevent assumes output chunked as well regardless
            # of presence of 'Content-Length'
            self.request.remove_output_header('Content-Length')
        # QQQ end of work around
        # QQQ when this is fixed, add version guard

        SERVER_SOFTWARE = env.get('SERVER_SOFTWARE')
        if SERVER_SOFTWARE and not self.request.find_output_header('Server'):
            self.request.add_output_header('Server', SERVER_SOFTWARE)

        self.request.send_reply(self.code, self.reason, data)
        self.log_request(len(data))

    def format_request(self, length='-'):
        req = self.request
        referer = req.find_input_header('Referer') or '-'
        agent = req.find_input_header('User-Agent') or '-'
        # QQQ fix datetime format
        now = datetime.now().replace(microsecond=0)
        args = (req.remote_host, now, req.typestr, req.uri,
                req.major, req.minor, req.response_code, length, referer, agent)
        return '%s - - [%s] "%s %s HTTP/%s.%s" %s %s "%s" "%s"' % args

    def log_request(self, *args):
        log = self.server.log
        if log:
            log.write(self.format_request(*args) + '\n')

    def prepare_env(self):
        req = self.request
        env = self.server.get_environ()
        if '?' in req.uri:
            path, query = req.uri.split('?', 1)
        else:
            path, query = req.uri, ''
        path = unquote(path)
        env.update({'REQUEST_METHOD': req.typestr,
                    'PATH_INFO': path,
                    'QUERY_STRING': query,
                    'SERVER_PROTOCOL': 'HTTP/%d.%d' % req.version,
                    'REMOTE_ADDR': req.remote_host,
                    'REMOTE_PORT': str(req.remote_port),
                    'REQUEST_URI': req.uri,
                    'wsgi.input': req.input_buffer})
        for header, value in req.get_input_headers():
            header = header.replace('-', '_').upper()
            if header not in ('CONTENT_LENGTH', 'CONTENT_TYPE'):
                header = 'HTTP_' + header
            if header in env:
                if 'COOKIE' in header:
                    env[header] += '; ' + value
                else:
                    env[header] += ',' + value
            else:
                env[header] = value
        return env

    def handle(self):
        env = self.prepare_env()
        try:
            try:
                result = self.server.application(env, self.start_response)
                try:
                    self.data.extend(result)
                finally:
                    if hasattr(result, 'close'):
                        result.close()
            except GreenletExit:
                self._reply500()
                raise
            except:
                traceback.print_exc()
                try:
                    sys.stderr.write('%s: Failed to handle request:\n  request = %s\n  application = %s\n\n' %
                                     (self.server, self.request, self.server.application))
                except Exception:
                    pass
                self._reply500()
        finally:
            sys.exc_clear()
            if self is not None and self.code is not None:
                self.end(env)

    def _reply500(self):
        self.reason = None
        self.start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        self.write('Internal Server Error')


class WSGIServer(HTTPServer):
    """A fast WSGI server based on :class:`HTTPServer`."""

    handler_class = WSGIHandler
    base_env = {'GATEWAY_INTERFACE': 'CGI/1.1',
                'SERVER_SOFTWARE': 'gevent/%d.%d Python/%d.%d' % (gevent.version_info[:2] + sys.version_info[:2]),
                'SCRIPT_NAME': '',
                'wsgi.version': (1, 0),
                'wsgi.url_scheme': 'http',
                'wsgi.multithread': False,
                'wsgi.multiprocess': False,
                'wsgi.run_once': False}
    # If 'wsgi.errors' is not present in base_env, it will be set to sys.stderr

    def __init__(self, listener, application=None, backlog=None, spawn='default', log='default', handler_class=None, environ=None):
        HTTPServer.__init__(self, listener, backlog=backlog, spawn=spawn)
        if application is not None:
            self.application = application
        if handler_class is not None:
            self.handler_class = handler_class
        if log == 'default':
            self.log = sys.stderr
        else:
            self.log = log
        self.set_environ(environ)

    def set_environ(self, environ=None):
        if environ is not None:
            self.environ = environ
        environ_update = getattr(self, 'environ', None)
        self.environ = self.base_env.copy()
        if environ_update is not None:
            self.environ.update(environ_update)
        if self.environ.get('wsgi.errors') is None:
            self.environ['wsgi.errors'] = sys.stderr

    def get_environ(self):
        return self.environ.copy()

    def pre_start(self):
        HTTPServer.pre_start(self)
        if 'SERVER_NAME' not in self.environ:
            self.environ['SERVER_NAME'] = socket.getfqdn(self.server_host)
        self.environ.setdefault('SERVER_PORT', str(self.server_port))

    def kill(self):
        super(WSGIServer, self).kill()
        self.__dict__.pop('application', None)
        self.__dict__.pop('log', None)
        self.__dict__.pop('environ', None)
        self.__dict__.pop('handler_class', None)

    def handle(self, req):
        handler = self.handler_class(req, self)
        handler.handle()


def extract_application(filename):
    import imp
    import os
    basename = os.path.basename(filename)
    if '.' in basename:
        name, suffix = basename.rsplit('.', 1)
    else:
        name, suffix = basename, ''
    module = imp.load_module(name, open(filename), filename, (suffix, 'r', imp.PY_SOURCE))
    return module.application


if __name__ == '__main__':
    USAGE = '''python -m gevent.wsgi [options] /path/to/myapp.wsgi
Where /path/to/myapp.wsgi is a Python script that defines "application" callable.'''
    import optparse
    parser = optparse.OptionParser(USAGE)
    parser.add_option('-p', '--port', default='8080', type='int', help='Set listening port (default is 8080)')
    parser.add_option('-i', '--interface', metavar='IP', default='127.0.0.1', help='Set listening interface (default is 127.0.0.1)')
    parser.add_option('--pool', metavar='SIZE', dest='spawn', type='int', help='Maximum number of concurrent connections')
    parser.add_option('--no-spawn', action='store_true', help='Do not spawn greenlets (no blocking calls)')
    options, args = parser.parse_args()
    if options.no_spawn is not None and options.spawn is not None:
        sys.exit('Please specify either --pool or --no-spawn but not both')
    if options.no_spawn:
        options.spawn = None
    elif options.spawn is None:
        options.spawn = 'default'
    if len(args) == 1:
        filename = args[0]
        try:
            application = extract_application(filename)
        except AttributeError:
            sys.exit("Could not find application in %s" % filename)
        server = WSGIServer((options.interface, options.port), application, spawn=options.spawn)
        print 'Serving %s on %s:%s' % (filename, options.interface, options.port)
        server.serve_forever()
    else:
        sys.stderr.write(parser.format_help())
