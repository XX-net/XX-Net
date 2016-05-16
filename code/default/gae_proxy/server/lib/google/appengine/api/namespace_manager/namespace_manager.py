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




"""Control the namespacing system used by various APIs.

A namespace may be specified in various API calls exemplified
by the datastore and memcache interfaces.  The default can be
specified using this module.
"""








import os
import re
import warnings

from google.appengine.api import lib_config

__all__ = ['BadValueError',
           'set_namespace',
           'get_namespace',
           'google_apps_namespace',
           'enable_request_namespace',
           'validate_namespace',
          ]




_ENV_DEFAULT_NAMESPACE = 'HTTP_X_APPENGINE_DEFAULT_NAMESPACE'
_ENV_CURRENT_NAMESPACE = 'HTTP_X_APPENGINE_CURRENT_NAMESPACE'






_NAMESPACE_MAX_LENGTH = 100
_NAMESPACE_PATTERN = r'^[0-9A-Za-z._-]{0,%s}$' % _NAMESPACE_MAX_LENGTH
_NAMESPACE_RE = re.compile(_NAMESPACE_PATTERN)

class _ConfigDefaults(object):
  def default_namespace_for_request():
      return None

_config = lib_config.register('namespace_manager_', _ConfigDefaults.__dict__)

def set_namespace(namespace):
  """Set the default namespace for the current HTTP request.

  Args:
    namespace: A string naming the new namespace to use. A value of None
      will unset the default namespace value.
  """
  if namespace is None:
    os.environ.pop(_ENV_CURRENT_NAMESPACE, None)
  else:
    validate_namespace(namespace)
    os.environ[_ENV_CURRENT_NAMESPACE] = namespace


def get_namespace():
  """Get the current default namespace or ('') namespace if unset."""
  name = os.environ.get(_ENV_CURRENT_NAMESPACE, None)
  if name is None:
    name = _config.default_namespace_for_request()
    if name is not None:
      set_namespace(name)
  if name is None:
    name = ''
  return name


def google_apps_namespace():
  return os.environ.get(_ENV_DEFAULT_NAMESPACE, None)

def enable_request_namespace():
  """Set the default namespace to the Google Apps domain referring this request.

  This method is deprecated, use lib_config instead.

  Calling this function will set the default namespace to the
  Google Apps domain that was used to create the url used for this request
  and only for the current request and only if the current default namespace
  is unset.

  """
  warnings.warn('namespace_manager.enable_request_namespace() is deprecated: '
                'use lib_config instead.',
                DeprecationWarning,
                stacklevel=2)
  if _ENV_CURRENT_NAMESPACE not in os.environ:
    if _ENV_DEFAULT_NAMESPACE in os.environ:
      os.environ[_ENV_CURRENT_NAMESPACE] = os.environ[_ENV_DEFAULT_NAMESPACE]


class BadValueError(Exception):
  """Raised by ValidateNamespaceString."""


def validate_namespace(value, exception=BadValueError):
  """Raises an exception if value is not a valid Namespace string.

  A namespace must match the regular expression ([0-9A-Za-z._-]{0,100}).

  Args:
    value: string, the value to validate.
    exception: exception type to raise.
  """
  if not isinstance(value, basestring):
    raise exception('value should be a string; received %r (a %s):' %
                    (value, type(value)))
  if not _NAMESPACE_RE.match(value):
    raise exception('value "%s" does not match regex "%s"' %
                    (value, _NAMESPACE_PATTERN))
