#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#




"""A mechanism for library configuration.

Whenever App Engine library code has the need for a user-configurable
value, it should use the following protocol:

1. Pick a prefix unique to the library module, e.g. 'mylib'.

2. Call lib_config.register(prefix, mapping) with that prefix as
   the first argument and a dict mapping suffixes to default functions
   as the second.

3. The register() function returns a config handle unique to this
   prefix.  The config handle object has attributes corresponding to
   each of the suffixes given in the mapping.  Call these functions
   (they're not really methods even though they look like methods) to
   access the user's configuration value.  If the user didn't
   configure a function, the default function from the mapping is
   called instead.

4. Document the function name and its signature and semantics.

Users wanting to provide configuration values should create a module
named appengine_config.py in the top-level directory of their
application, and define functions as documented by various App Engine
library components in that module.  To change the configuration, edit
the file and re-deploy the application.  (When using the SDK, no
redeployment is required: the development server will pick up the
changes the next time it handles a request.)

Third party libraries can also use this mechanism.  For casual use,
just calling the register() method with a unique prefix is okay.  For
carefull libraries, however, it is recommended to instantiate a new
LibConfigRegistry instance using a different module name.

Example appengine_config.py file:

  from somewhere import MyMiddleWareClass

  def mylib_add_middleware(app):
    app = MyMiddleWareClass(app)
    return app

Example library use:

  from google.appengine.api import lib_config

  config_handle = lib_config.register(
      'mylib',
      {'add_middleware': lambda app: app})

  def add_middleware(app):
    return config_handle.add_middleware(app)
"""


__all__ = ['DEFAULT_MODNAME',
           'LibConfigRegistry',
           'ConfigHandle',
           'register',
           'main',
           ]


import logging
import os
import sys
import threading


DEFAULT_MODNAME = 'appengine_config'





class LibConfigRegistry(object):
  """A registry for library configuration values."""

  def __init__(self, modname):
    """Constructor.

    Args:
      modname: The module name to be imported.

    Note: the actual import of this module is deferred until the first
    time a configuration value is requested through attribute access
    on a ConfigHandle instance.
    """
    self._modname = modname
    self._registrations = {}
    self._module = None
    self._lock = threading.RLock()

  def register(self, prefix, mapping):
    """Register a set of configuration names.

    Args:
      prefix: A shared prefix for the configuration names being registered.
          If the prefix doesn't end in '_', that character is appended.
      mapping: A dict mapping suffix strings to default values.

    Returns:
      A ConfigHandle instance.

    It's okay to re-register the same prefix: the mappings are merged,
    and for duplicate suffixes the most recent registration wins.
    """
    if not prefix.endswith('_'):
      prefix += '_'
    self._lock.acquire()
    try:
      handle = self._registrations.get(prefix)
      if handle is None:
        handle = ConfigHandle(prefix, self)
        self._registrations[prefix] = handle
    finally:
      self._lock.release()
    handle._update_defaults(mapping)
    return handle

  def initialize(self, import_func=__import__):
    """Attempt to import the config module, if not already imported.

    This function always sets self._module to a value unequal
    to None: either the imported module (if imported successfully), or
    a dummy object() instance (if an ImportError was raised).  Other
    exceptions are *not* caught.

    When a dummy instance is used, it is also put in sys.modules.
    This allows us to detect when sys.modules was changed (as
    dev_appserver.py does when it notices source code changes) and
    re-try the __import__ in that case, while skipping it (for speed)
    if nothing has changed.

    Args:
      import_func: Used for dependency injection.
    """
    self._lock.acquire()
    try:
      if (self._module is not None and
          self._module is sys.modules.get(self._modname)):
        return
      try:
        import_func(self._modname)
      except ImportError, err:
        if str(err) != 'No module named %s' % self._modname:

          raise
        self._module = object()
        sys.modules[self._modname] = self._module
      else:
        self._module = sys.modules[self._modname]
    finally:
      self._lock.release()

  def reset(self):
    """Drops the imported config module.

    If the config module has not been imported then this is a no-op.
    """
    self._lock.acquire()
    try:
      if self._module is None:

        return

      self._module = None
      handles = self._registrations.values()
    finally:
      self._lock.release()
    for handle in handles:
      handle._clear_cache()

  def _pairs(self, prefix):
    """Generate (key, value) pairs from the config module matching prefix.

    Args:
      prefix: A prefix string ending in '_', e.g. 'mylib_'.

    Yields:
      (key, value) pairs where key is the configuration name with
      prefix removed, and value is the corresponding value.
    """
    self._lock.acquire()
    try:
      mapping = getattr(self._module, '__dict__', None)
      if not mapping:
        return
      items = mapping.items()
    finally:
      self._lock.release()
    nskip = len(prefix)
    for key, value in items:
      if key.startswith(prefix):
        yield key[nskip:], value

  def _dump(self):
    """Print info about all registrations to stdout."""
    self.initialize()
    handles = []
    self._lock.acquire()
    try:
      if not hasattr(self._module, '__dict__'):
        print 'Module %s.py does not exist.' % self._modname
      elif not self._registrations:
        print 'No registrations for %s.py.' % self._modname
      else:
        print 'Registrations in %s.py:' % self._modname
        print '-'*40
        handles = self._registrations.items()
    finally:
      self._lock.release()
    for _, handle in sorted(handles):
      handle._dump()


class ConfigHandle(object):
  """A set of configuration for a single library module or package.

  Public attributes of instances of this class are configuration
  values.  Attributes are dynamically computed (in __getattr__()) and
  cached as regular instance attributes.
  """

  _initialized = False

  def __init__(self, prefix, registry):
    """Constructor.

    Args:
      prefix: A shared prefix for the configuration names being registered.
          It *must* end in '_'.  (This is enforced by LibConfigRegistry.)
      registry: A LibConfigRegistry instance.
    """
    assert prefix.endswith('_')
    self._prefix = prefix
    self._defaults = {}
    self._overrides = {}
    self._registry = registry
    self._lock = threading.RLock()

  def _update_defaults(self, mapping):
    """Update the default mappings.

    Args:
      mapping: A dict mapping suffix strings to default values.
    """
    self._lock.acquire()
    try:
      for key, value in mapping.iteritems():
        if key.startswith('__') and key.endswith('__'):
          continue
        self._defaults[key] = value
      if self._initialized:
        self._update_configs()
    finally:
      self._lock.release()

  def _update_configs(self):
    """Update the configuration values.

    This clears the cached values, initializes the registry, and loads
    the configuration values from the config module.
    """
    self._lock.acquire()
    try:
      if self._initialized:
        self._clear_cache()
      self._registry.initialize()
      for key, value in self._registry._pairs(self._prefix):
        if key not in self._defaults:
          logging.warn('Configuration "%s" not recognized', self._prefix + key)
        else:
          self._overrides[key] = value
      self._initialized = True
    finally:
      self._lock.release()

  def _clear_cache(self):
    """Clear the cached values."""
    self._lock.acquire()
    try:
      self._initialized = False
      for key in self._defaults:
        try:
          delattr(self, key)
        except AttributeError:
          pass
    finally:
      self._lock.release()

  def _dump(self):
    """Print info about this set of registrations to stdout."""
    self._lock.acquire()
    try:
      print 'Prefix %s:' % self._prefix
      if self._overrides:
        print '  Overrides:'
        for key in sorted(self._overrides):
          print '    %s = %r' % (key, self._overrides[key])
      else:
        print '  No overrides'
      if self._defaults:
        print '  Defaults:'
        for key in sorted(self._defaults):
          print '    %s = %r' % (key, self._defaults[key])
      else:
        print '  No defaults'
      print '-'*40
    finally:
      self._lock.release()

  def __getattr__(self, suffix):
    """Dynamic attribute access.

    Args:
      suffix: The attribute name.

    Returns:
      A configuration values.

    Raises:
      AttributeError if the suffix is not a registered suffix.

    The first time an attribute is referenced, this method is invoked.
    The value returned taken either from the config module or from the
    registered default.
    """
    self._lock.acquire()
    try:
      if not self._initialized:
        self._update_configs()
      if suffix in self._overrides:
        value = self._overrides[suffix]
      elif suffix in self._defaults:
        value = self._defaults[suffix]
      else:
        raise AttributeError(suffix)

      setattr(self, suffix, value)
      return value
    finally:
      self._lock.release()



_default_registry = LibConfigRegistry(DEFAULT_MODNAME)


def register(prefix, mapping):
  """Register a set of configurations with the default config module.

  Args:
    prefix: A shared prefix for the configuration names being registered.
        If the prefix doesn't end in '_', that character is appended.
    mapping: A dict mapping suffix strings to default values.

  Returns:
    A ConfigHandle instance.
  """
  return _default_registry.register(prefix, mapping)


def main():
  """CGI-style request handler to dump the configuration.

  Put this in your app.yaml to enable (you can pick any URL):

  - url: /lib_config
    script: $PYTHON_LIB/google/appengine/api/lib_config.py

  Note: unless you are using the SDK, you must be admin.
  """
  if not os.getenv('SERVER_SOFTWARE', '').startswith('Dev'):
    from google.appengine.api import users
    if not users.is_current_user_admin():
      if users.get_current_user() is None:
        print 'Status: 302'
        print 'Location:', users.create_login_url(os.getenv('PATH_INFO', ''))
      else:
        print 'Status: 403'
        print
        print 'Forbidden'
      return

  print 'Content-type: text/plain'
  print
  _default_registry._dump()


if __name__ == '__main__':
  main()
