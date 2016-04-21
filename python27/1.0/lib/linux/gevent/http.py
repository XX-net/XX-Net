# Copyright (c) 2009-2010 Denis Bilenko. See LICENSE for details.
from gevent import core
from gevent.baseserver import BaseServer


__all__ = ['HTTPServer']


class HTTPServer(BaseServer):
    """An HTTP server based on libevent-http.

    *handle* is called with one argument: an :class:`gevent.core.http_request` instance.
    """

    default_response_headers = [('Connection', 'close')]

    def __init__(self, listener, handle=None, backlog=None, spawn='default', default_response_headers='default'):
        BaseServer.__init__(self, listener, handle=handle, backlog=backlog, spawn=spawn)
        self.http = None
        if default_response_headers != 'default':
            self.default_response_headers = default_response_headers

    def _on_request(self, request):
        spawn = self._spawn
        if spawn is None:
            self.handle(request)
        else:
            if self.full():
                self._on_full(request)
            else:
                spawn(self.handle, request)

    def _on_full(self, request):
        msg = 'Service Temporarily Unavailable'
        request.add_output_header('Connection', 'close')
        request.add_output_header('Content-type', 'text/plain')
        request.add_output_header('Content-length', str(len(msg)))
        request.send_reply(503, 'Service Unavailable', msg)

    def start_accepting(self):
        self.http = core.http(self._on_request, self.default_response_headers)
        self.http.accept(self.socket.fileno())

    def stop_accepting(self):
        self.http = None
