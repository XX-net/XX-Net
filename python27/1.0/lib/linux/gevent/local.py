"""Greenlet-local objects.

This module is based on `_threading_local.py`__ from the standard library.

__ http://svn.python.org/view/python/trunk/Lib/_threading_local.py?view=markup&pathrev=78336

Greenlet-local objects support the management of greenlet-local data.
If you have data that you want to be local to a greenlet, simply create
a greenlet-local object and use its attributes:

  >>> mydata = local()
  >>> mydata.number = 42
  >>> mydata.number
  42

You can also access the local-object's dictionary:

  >>> mydata.__dict__
  {'number': 42}
  >>> mydata.__dict__.setdefault('widgets', [])
  []
  >>> mydata.widgets
  []

What's important about greenlet-local objects is that their data are
local to a greenlet. If we access the data in a different greenlet:

  >>> log = []
  >>> def f():
  ...     items = mydata.__dict__.items()
  ...     items.sort()
  ...     log.append(items)
  ...     mydata.number = 11
  ...     log.append(mydata.number)
  >>> greenlet = gevent.spawn(f)
  >>> greenlet.join()
  >>> log
  [[], 11]

we get different data.  Furthermore, changes made in the other greenlet
don't affect data seen in this greenlet:

  >>> mydata.number
  42

Of course, values you get from a local object, including a __dict__
attribute, are for whatever greenlet was current at the time the
attribute was read.  For that reason, you generally don't want to save
these values across greenlets, as they apply only to the greenlet they
came from.

You can create custom local objects by subclassing the local class:

  >>> class MyLocal(local):
  ...     number = 2
  ...     initialized = False
  ...     def __init__(self, **kw):
  ...         if self.initialized:
  ...             raise SystemError('__init__ called too many times')
  ...         self.initialized = True
  ...         self.__dict__.update(kw)
  ...     def squared(self):
  ...         return self.number ** 2

This can be useful to support default values, methods and
initialization.  Note that if you define an __init__ method, it will be
called each time the local object is used in a separate greenlet.  This
is necessary to initialize each greenlet's dictionary.

Now if we create a local object:

  >>> mydata = MyLocal(color='red')

Now we have a default number:

  >>> mydata.number
  2

an initial color:

  >>> mydata.color
  'red'
  >>> del mydata.color

And a method that operates on the data:

  >>> mydata.squared()
  4

As before, we can access the data in a separate greenlet:

  >>> log = []
  >>> greenlet = gevent.spawn(f)
  >>> greenlet.join()
  >>> log
  [[('color', 'red'), ('initialized', True)], 11]

without affecting this greenlet's data:

  >>> mydata.number
  2
  >>> mydata.color
  Traceback (most recent call last):
  ...
  AttributeError: 'MyLocal' object has no attribute 'color'

Note that subclasses can define slots, but they are not greenlet
local. They are shared across greenlets::

  >>> class MyLocal(local):
  ...     __slots__ = 'number'

  >>> mydata = MyLocal()
  >>> mydata.number = 42
  >>> mydata.color = 'red'

So, the separate greenlet:

  >>> greenlet = gevent.spawn(f)
  >>> greenlet.join()

affects what we see:

  >>> mydata.number
  11

>>> del mydata
"""
from weakref import WeakKeyDictionary
from copy import copy
from gevent.hub import getcurrent
from gevent.coros import RLock

__all__ = ["local"]


class _localbase(object):
    __slots__ = '_local__args', '_local__lock', '_local__dicts'

    def __new__(cls, *args, **kw):
        self = object.__new__(cls)
        object.__setattr__(self, '_local__args', (args, kw))
        object.__setattr__(self, '_local__lock', RLock())
        dicts = WeakKeyDictionary()
        object.__setattr__(self, '_local__dicts', dicts)

        if (args or kw) and (cls.__init__ is object.__init__):
            raise TypeError("Initialization arguments are not supported")

        # We need to create the greenlet dict in anticipation of
        # __init__ being called, to make sure we don't call it again ourselves.
        dict = object.__getattribute__(self, '__dict__')
        dicts[getcurrent()] = dict
        return self


def _init_locals(self):
    d = {}
    dicts = object.__getattribute__(self, '_local__dicts')
    dicts[getcurrent()] = d
    object.__setattr__(self, '__dict__', d)

    # we have a new instance dict, so call out __init__ if we have one
    cls = type(self)
    if cls.__init__ is not object.__init__:
        args, kw = object.__getattribute__(self, '_local__args')
        cls.__init__(self, *args, **kw)


class local(_localbase):

    def __getattribute__(self, name):
        d = object.__getattribute__(self, '_local__dicts').get(getcurrent())
        if d is None:
            # it's OK to acquire the lock here and not earlier, because the above code won't switch out
            # however, subclassed __init__ might switch, so we do need to acquire the lock here
            lock = object.__getattribute__(self, '_local__lock')
            lock.acquire()
            try:
                _init_locals(self)
                return object.__getattribute__(self, name)
            finally:
                lock.release()
        else:
            object.__setattr__(self, '__dict__', d)
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name == '__dict__':
            raise AttributeError("%r object attribute '__dict__' is read-only" % self.__class__.__name__)
        d = object.__getattribute__(self, '_local__dicts').get(getcurrent())
        if d is None:
            lock = object.__getattribute__(self, '_local__lock')
            lock.acquire()
            try:
                _init_locals(self)
                return object.__setattr__(self, name, value)
            finally:
                lock.release()
        else:
            object.__setattr__(self, '__dict__', d)
            return object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name == '__dict__':
            raise AttributeError("%r object attribute '__dict__' is read-only" % self.__class__.__name__)
        d = object.__getattribute__(self, '_local__dicts').get(getcurrent())
        if d is None:
            lock = object.__getattribute__(self, '_local__lock')
            lock.acquire()
            try:
                _init_locals(self)
                return object.__delattr__(self, name)
            finally:
                lock.release()
        else:
            object.__setattr__(self, '__dict__', d)
            return object.__delattr__(self, name)

    def __copy__(self):
        currentId = getcurrent()
        d = object.__getattribute__(self, '_local__dicts').get(currentId)
        duplicate = copy(d)

        cls = type(self)
        if cls.__init__ is not object.__init__:
            args, kw = object.__getattribute__(self, '_local__args')
            instance = cls(*args, **kw)
        else:
            instance = cls()

        object.__setattr__(instance, '_local__dicts', {
            currentId: duplicate
        })

        return instance
