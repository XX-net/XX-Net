# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for reading OAuth 2.0 client secret files.

A client_secrets.json file contains all the information needed to interact with
an OAuth 2.0 protected service.
"""

__author__ = 'jcgregorio@google.com (Joe Gregorio)'

import json
import six


# Properties that make a client_secrets.json file valid.
TYPE_WEB = 'web'
TYPE_INSTALLED = 'installed'

VALID_CLIENT = {
    TYPE_WEB: {
        'required': [
            'client_id',
            'client_secret',
            'redirect_uris',
            'auth_uri',
            'token_uri',
        ],
        'string': [
            'client_id',
            'client_secret',
        ],
    },
    TYPE_INSTALLED: {
        'required': [
            'client_id',
            'client_secret',
            'redirect_uris',
            'auth_uri',
            'token_uri',
        ],
        'string': [
            'client_id',
            'client_secret',
        ],
    },
}


class Error(Exception):
  """Base error for this module."""
  pass


class InvalidClientSecretsError(Error):
  """Format of ClientSecrets file is invalid."""
  pass


def _validate_clientsecrets(obj):
  _INVALID_FILE_FORMAT_MSG = (
    'Invalid file format. See '
    'https://developers.google.com/api-client-library/'
    'python/guide/aaa_client_secrets')

  if obj is None:
    raise InvalidClientSecretsError(_INVALID_FILE_FORMAT_MSG)
  if len(obj) != 1:
    raise InvalidClientSecretsError(
      _INVALID_FILE_FORMAT_MSG + ' '
      'Expected a JSON object with a single property for a "web" or '
      '"installed" application')
  client_type = tuple(obj)[0]
  if client_type not in VALID_CLIENT:
    raise InvalidClientSecretsError('Unknown client type: %s.' % (client_type,))
  client_info = obj[client_type]
  for prop_name in VALID_CLIENT[client_type]['required']:
    if prop_name not in client_info:
      raise InvalidClientSecretsError(
        'Missing property "%s" in a client type of "%s".' % (prop_name,
                                                           client_type))
  for prop_name in VALID_CLIENT[client_type]['string']:
    if client_info[prop_name].startswith('[['):
      raise InvalidClientSecretsError(
        'Property "%s" is not configured.' % prop_name)
  return client_type, client_info


def load(fp):
  obj = json.load(fp)
  return _validate_clientsecrets(obj)


def loads(s):
  obj = json.loads(s)
  return _validate_clientsecrets(obj)


def _loadfile(filename):
  try:
    with open(filename, 'r') as fp:
      obj = json.load(fp)
  except IOError:
    raise InvalidClientSecretsError('File not found: "%s"' % filename)
  return _validate_clientsecrets(obj)


def loadfile(filename, cache=None):
  """Loading of client_secrets JSON file, optionally backed by a cache.

  Typical cache storage would be App Engine memcache service,
  but you can pass in any other cache client that implements
  these methods:

  * ``get(key, namespace=ns)``
  * ``set(key, value, namespace=ns)``

  Usage::

    # without caching
    client_type, client_info = loadfile('secrets.json')
    # using App Engine memcache service
    from google.appengine.api import memcache
    client_type, client_info = loadfile('secrets.json', cache=memcache)

  Args:
    filename: string, Path to a client_secrets.json file on a filesystem.
    cache: An optional cache service client that implements get() and set()
      methods. If not specified, the file is always being loaded from
      a filesystem.

  Raises:
    InvalidClientSecretsError: In case of a validation error or some
      I/O failure. Can happen only on cache miss.

  Returns:
    (client_type, client_info) tuple, as _loadfile() normally would.
    JSON contents is validated only during first load. Cache hits are not
    validated.
  """
  _SECRET_NAMESPACE = 'oauth2client:secrets#ns'

  if not cache:
    return _loadfile(filename)

  obj = cache.get(filename, namespace=_SECRET_NAMESPACE)
  if obj is None:
    client_type, client_info = _loadfile(filename)
    obj = {client_type: client_info}
    cache.set(filename, obj, namespace=_SECRET_NAMESPACE)

  return next(six.iteritems(obj))
