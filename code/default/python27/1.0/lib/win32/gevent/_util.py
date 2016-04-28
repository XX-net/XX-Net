def __bootstrap__():
   global __bootstrap__, __loader__, __file__
   import _memimporter, sys
   _memimporter.set_find_proc(lambda x: __loader__.get_data(r'%s%s' % (__loader__.prefix, x)))
   __file__ = r'%s%s.pyd' % (__loader__.prefix, __name__.split('.')[-1])
   mod = _memimporter.import_module(__loader__.get_data(__file__), 'init'+__name__.split('.')[-1], __name__, __file__)
   mod.__file__ = __file__
   mod.__loader__ = __loader__
   sys.modules[__name__] = mod
   del __bootstrap__, __loader__, __file__, _memimporter, sys
__bootstrap__()
