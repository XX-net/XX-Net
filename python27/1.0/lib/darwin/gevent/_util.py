def __bootstrap__():
   global __bootstrap__, __loader__, __file__
   import pkg_resources, imp
   __file__ = pkg_resources.resource_filename(__name__,'_util.so')
   __loader__ = None; del __bootstrap__, __loader__
   imp.load_dynamic(__name__,__file__)
try:
   __bootstrap__()
except (ImportError, LookupError):
   raise ImportError('No module named %s' % __name__)
