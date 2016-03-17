"""
Decorators to wrap functions to make them WSGI applications.

The main decorator :class:`wsgify` turns a function into a WSGI
application (while also allowing normal calling of the method with an
instantiated request).
"""

from webob.compat import (
    bytes_,
    text_type,
    )

from webob.request import Request
from webob.exc import HTTPException

__all__ = ['wsgify']

class wsgify(object):
    """Turns a request-taking, response-returning function into a WSGI
    app

    You can use this like::

        @wsgify
        def myfunc(req):
            return webob.Response('hey there')

    With that ``myfunc`` will be a WSGI application, callable like
    ``app_iter = myfunc(environ, start_response)``.  You can also call
    it like normal, e.g., ``resp = myfunc(req)``.  (You can also wrap
    methods, like ``def myfunc(self, req)``.)

    If you raise exceptions from :mod:`webob.exc` they will be turned
    into WSGI responses.

    There are also several parameters you can use to customize the
    decorator.  Most notably, you can use a :class:`webob.Request`
    subclass, like::

        class MyRequest(webob.Request):
            @property
            def is_local(self):
                return self.remote_addr == '127.0.0.1'
        @wsgify(RequestClass=MyRequest)
        def myfunc(req):
            if req.is_local:
                return Response('hi!')
            else:
                raise webob.exc.HTTPForbidden

    Another customization you can add is to add `args` (positional
    arguments) or `kwargs` (of course, keyword arguments).  While
    generally not that useful, you can use this to create multiple
    WSGI apps from one function, like::

        import simplejson
        def serve_json(req, json_obj):
            return Response(json.dumps(json_obj),
                            content_type='application/json')

        serve_ob1 = wsgify(serve_json, args=(ob1,))
        serve_ob2 = wsgify(serve_json, args=(ob2,))

    You can return several things from a function:

    * A :class:`webob.Response` object (or subclass)
    * *Any* WSGI application
    * None, and then ``req.response`` will be used (a pre-instantiated
      Response object)
    * A string, which will be written to ``req.response`` and then that
      response will be used.
    * Raise an exception from :mod:`webob.exc`

    Also see :func:`wsgify.middleware` for a way to make middleware.

    You can also subclass this decorator; the most useful things to do
    in a subclass would be to change `RequestClass` or override
    `call_func` (e.g., to add ``req.urlvars`` as keyword arguments to
    the function).
    """

    RequestClass = Request

    def __init__(self, func=None, RequestClass=None,
                 args=(), kwargs=None, middleware_wraps=None):
        self.func = func
        if (RequestClass is not None
            and RequestClass is not self.RequestClass):
            self.RequestClass = RequestClass
        self.args = tuple(args)
        if kwargs is None:
            kwargs = {}
        self.kwargs = kwargs
        self.middleware_wraps = middleware_wraps

    def __repr__(self):
        return '<%s at %s wrapping %r>' % (self.__class__.__name__,
                                           id(self), self.func)

    def __get__(self, obj, type=None):
        # This handles wrapping methods
        if hasattr(self.func, '__get__'):
            return self.clone(self.func.__get__(obj, type))
        else:
            return self

    def __call__(self, req, *args, **kw):
        """Call this as a WSGI application or with a request"""
        func = self.func
        if func is None:
            if args or kw:
                raise TypeError(
                    "Unbound %s can only be called with the function it "
                    "will wrap" % self.__class__.__name__)
            func = req
            return self.clone(func)
        if isinstance(req, dict):
            if len(args) != 1 or kw:
                raise TypeError(
                    "Calling %r as a WSGI app with the wrong signature")
            environ = req
            start_response = args[0]
            req = self.RequestClass(environ)
            req.response = req.ResponseClass()
            try:
                args = self.args
                if self.middleware_wraps:
                    args = (self.middleware_wraps,) + args
                resp = self.call_func(req, *args, **self.kwargs)
            except HTTPException as exc:
                resp = exc
            if resp is None:
                ## FIXME: I'm not sure what this should be?
                resp = req.response
            if isinstance(resp, text_type):
                resp = bytes_(resp, req.charset)
            if isinstance(resp, bytes):
                body = resp
                resp = req.response
                resp.write(body)
            if resp is not req.response:
                resp = req.response.merge_cookies(resp)
            return resp(environ, start_response)
        else:
            if self.middleware_wraps:
                args = (self.middleware_wraps,) + args
            return self.func(req, *args, **kw)

    def get(self, url, **kw):
        """Run a GET request on this application, returning a Response.

        This creates a request object using the given URL, and any
        other keyword arguments are set on the request object (e.g.,
        ``last_modified=datetime.now()``).

        ::

            resp = myapp.get('/article?id=10')
        """
        kw.setdefault('method', 'GET')
        req = self.RequestClass.blank(url, **kw)
        return self(req)

    def post(self, url, POST=None, **kw):
        """Run a POST request on this application, returning a Response.

        The second argument (`POST`) can be the request body (a
        string), or a dictionary or list of two-tuples, that give the
        POST body.

        ::

            resp = myapp.post('/article/new',
                              dict(title='My Day',
                                   content='I ate a sandwich'))
        """
        kw.setdefault('method', 'POST')
        req = self.RequestClass.blank(url, POST=POST, **kw)
        return self(req)

    def request(self, url, **kw):
        """Run a request on this application, returning a Response.

        This can be used for DELETE, PUT, etc requests.  E.g.::

            resp = myapp.request('/article/1', method='PUT', body='New article')
        """
        req = self.RequestClass.blank(url, **kw)
        return self(req)

    def call_func(self, req, *args, **kwargs):
        """Call the wrapped function; override this in a subclass to
        change how the function is called."""
        return self.func(req, *args, **kwargs)

    def clone(self, func=None, **kw):
        """Creates a copy/clone of this object, but with some
        parameters rebound
        """
        kwargs = {}
        if func is not None:
            kwargs['func'] = func
        if self.RequestClass is not self.__class__.RequestClass:
            kwargs['RequestClass'] = self.RequestClass
        if self.args:
            kwargs['args'] = self.args
        if self.kwargs:
            kwargs['kwargs'] = self.kwargs
        kwargs.update(kw)
        return self.__class__(**kwargs)

    # To match @decorator:
    @property
    def undecorated(self):
        return self.func

    @classmethod
    def middleware(cls, middle_func=None, app=None, **kw):
        """Creates middleware

        Use this like::

            @wsgify.middleware
            def restrict_ip(req, app, ips):
                if req.remote_addr not in ips:
                    raise webob.exc.HTTPForbidden('Bad IP: %s' % req.remote_addr)
                return app

            @wsgify
            def app(req):
                return 'hi'

            wrapped = restrict_ip(app, ips=['127.0.0.1'])

        Or if you want to write output-rewriting middleware::

            @wsgify.middleware
            def all_caps(req, app):
                resp = req.get_response(app)
                resp.body = resp.body.upper()
                return resp

            wrapped = all_caps(app)

        Note that you must call ``req.get_response(app)`` to get a WebOb
        response object.  If you are not modifying the output, you can just
        return the app.

        As you can see, this method doesn't actually create an application, but
        creates "middleware" that can be bound to an application, along with
        "configuration" (that is, any other keyword arguments you pass when
        binding the application).

        """
        if middle_func is None:
            return _UnboundMiddleware(cls, app, kw)
        if app is None:
            return _MiddlewareFactory(cls, middle_func, kw)
        return cls(middle_func, middleware_wraps=app, kwargs=kw)

class _UnboundMiddleware(object):
    """A `wsgify.middleware` invocation that has not yet wrapped a
    middleware function; the intermediate object when you do
    something like ``@wsgify.middleware(RequestClass=Foo)``
    """

    def __init__(self, wrapper_class, app, kw):
        self.wrapper_class = wrapper_class
        self.app = app
        self.kw = kw

    def __repr__(self):
        return '<%s at %s wrapping %r>' % (self.__class__.__name__,
                                           id(self), self.app)

    def __call__(self, func, app=None):
        if app is None:
            app = self.app
        return self.wrapper_class.middleware(func, app=app, **self.kw)

class _MiddlewareFactory(object):
    """A middleware that has not yet been bound to an application or
    configured.
    """

    def __init__(self, wrapper_class, middleware, kw):
        self.wrapper_class = wrapper_class
        self.middleware = middleware
        self.kw = kw

    def __repr__(self):
        return '<%s at %s wrapping %r>' % (self.__class__.__name__, id(self),
                                           self.middleware)

    def __call__(self, app, **config):
        kw = self.kw.copy()
        kw.update(config)
        return self.wrapper_class.middleware(self.middleware, app, **kw)
