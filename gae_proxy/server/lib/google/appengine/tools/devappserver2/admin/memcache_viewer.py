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
"""A memcache viewer and editor UI.

Memcache associates a key with a value and an integer flag. The Go API maps
keys to strings and lets the user control the flag. Java, PHP and Python
map keys to an arbitrary type and uses the flag to indicate the type
information. Java, PHP and Python map types in inconsistent ways, see:
- google/appengine/api/memcache/__init__.py
- google/appengine/api/memcache/MemcacheSerialization.java
- google/appengine/runtime/MemcacheUtils.php
"""



import datetime
import logging
import urllib

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import memcache
from google.appengine.api.memcache import memcache_service_pb
from google.appengine.tools.devappserver2.admin import admin_request_handler


class StringValueConverter(object):
  memcache_type = memcache.TYPE_STR
  placeholder = 'hello world!'
  can_edit = True
  friendly_type_name = 'String'

  @staticmethod
  def to_display(cache_value):
    """Convert a memcache string into a displayable representation.

    Make a memcache string into a text string that can be displayed or edited.
    While called a string, it is technically just an array of bytes. Because
    we do not know what encoding the bytes are (and possibly they are not an
    encoded text string - for example they could be an MD5 hash) we display
    in string-escaped form.

    Args:
      cache_value: an array of bytes

    Returns:
      A unicode string that represents the sequence of bytes and can be
      roundtripped back to the sequence of bytes.
    """

    # As we don't know what encoding the bytes are, we string escape so any
    # byte sequence is legal ASCII. Once we have a legal ASCII byte sequence
    # we can safely convert to a unicode/text string.
    return cache_value.encode('string-escape').decode('ascii')

  @staticmethod
  def to_cache(display_value):
    """Convert a displayable representation to a memcache string.

    Take a displayable/editable text string and convert into a memcache string.
    As a memcache string is technically an array of bytes, we only allow
    characters from the ASCII range and require all other bytes to be indicated
    via string escape. (because if we see the Unicode character Yen sign
    (U+00A5) we don't know if they want the byte 0xA5 or the UTF-8 two byte
    sequence 0xC2 0xA5).

    Args:
      display_value: a text (i.e. unicode string) using only ASCII characters;
        non-ASCII characters must be represented string escapes.

    Returns:
      An array of bytes.

    Raises:
      UnicodeEncodeError: a non-ASCII character is part of the input.
    """

    # Since we don't know how they want their Unicode encoded, this will raise
    # an exception (which will be displayed nicely) if they include non-ASCII.
    return display_value.encode('ascii').decode('string-escape')


class UnicodeValueConverter(object):
  memcache_type = memcache.TYPE_UNICODE
  # Hello world in Japanese.
  placeholder = u'\u3053\u3093\u306b\u3061\u306f\u4e16\u754c'
  can_edit = True
  friendly_type_name = 'Unicode String'

  @staticmethod
  def to_display(cache_value):
    return cache_value.decode('utf-8')

  @staticmethod
  def to_cache(display_value):
    return display_value.encode('utf-8')


class BooleanValueConverter(object):
  memcache_type = memcache.TYPE_BOOL
  placeholder = 'true'
  can_edit = True
  friendly_type_name = 'Boolean'

  @staticmethod
  def to_display(cache_value):
    if cache_value == '0':
      return 'false'
    elif cache_value == '1':
      return 'true'
    else:
      raise ValueError('unexpected boolean %r' % cache_value)

  @staticmethod
  def to_cache(display_value):
    if display_value.lower() in ('false', 'no', 'off', '0'):
      return '0'
    elif display_value.lower() in ('true', 'yes', 'on', '1'):
      return '1'

    raise ValueError(
        'invalid literal for boolean: %s (must be "true" or "false")' %
        display_value)


class IntValueConverter(object):
  memcache_type = memcache.TYPE_INT
  placeholder = '42'
  can_edit = True
  friendly_type_name = 'Integer'

  @staticmethod
  def to_display(cache_value):
    return str(cache_value)

  @staticmethod
  def to_cache(display_value):
    return str(int(display_value))


class OtherValueConverter(object):
  memcache_type = None
  placeholder = None
  can_edit = False
  friendly_type_name = 'Unknown Type'

  @staticmethod
  def to_display(cache_value):
    return repr(cache_value)[1:-1]

  @staticmethod
  def to_cache(display_value):
    raise NotImplementedError('cannot to a memcache value of unknown type')


class MemcacheViewerRequestHandler(admin_request_handler.AdminRequestHandler):
  CONVERTERS = [StringValueConverter, UnicodeValueConverter,
                BooleanValueConverter, IntValueConverter,
                OtherValueConverter]
  MEMCACHE_TYPE_TO_CONVERTER = {c.memcache_type: c for c in CONVERTERS
                                if c.memcache_type is not None}
  FRIENDLY_TYPE_NAME_TO_CONVERTER = {c.friendly_type_name: c
                                     for c in CONVERTERS}

  def _get_memcache_value_and_flags(self, key):
    """Return a 2-tuple containing a memcache value and its flags."""
    request = memcache_service_pb.MemcacheGetRequest()
    response = memcache_service_pb.MemcacheGetResponse()

    request.add_key(key)
    apiproxy_stub_map.MakeSyncCall('memcache', 'Get', request, response)
    assert response.item_size() < 2
    if response.item_size() == 0:
      return None, None
    else:
      return response.item(0).value(), response.item(0).flags()

  def _set_memcache_value(self, key, value, flags):
    """Store a value in memcache."""
    request = memcache_service_pb.MemcacheSetRequest()
    response = memcache_service_pb.MemcacheSetResponse()

    item = request.add_item()
    item.set_key(key)
    item.set_value(value)
    item.set_flags(flags)

    apiproxy_stub_map.MakeSyncCall('memcache', 'Set', request, response)
    return (response.set_status(0) ==
            memcache_service_pb.MemcacheSetResponse.STORED)

  def get(self):
    """Show template and prepare stats and/or key+value to display/edit."""
    values = {'request': self.request,
              'message': self.request.get('message')}

    edit = self.request.get('edit')
    key = self.request.get('key')
    if edit:
      # Show the form to edit/create the value.
      key = edit
      values['show_stats'] = False
      values['show_value'] = False
      values['show_valueform'] = True
      values['types'] = [type_value.friendly_type_name
                         for type_value in self.CONVERTERS
                         if type_value.can_edit]
    elif key:
      # A key was given, show it's value on the stats page.
      values['show_stats'] = True
      values['show_value'] = True
      values['show_valueform'] = False
    else:
      # Plain stats display + key lookup form.
      values['show_stats'] = True
      values['show_valueform'] = False
      values['show_value'] = False

    if key:
      values['key'] = key
      memcache_value, memcache_flags = self._get_memcache_value_and_flags(key)
      if memcache_value is not None:
        converter = self.MEMCACHE_TYPE_TO_CONVERTER.get(memcache_flags,
                                                        OtherValueConverter)
        try:
          values['value'] = converter.to_display(memcache_value)
        except ValueError:
          # This exception is possible in the case where the value was set by
          # Go, which allows for arbitrary user-assigned flag values.
          logging.exception('Could not convert %s value %s',
                            converter.friendly_type_name, memcache_value)
          converter = OtherValueConverter
          values['value'] = converter.to_display(memcache_value)

        values['type'] = converter.friendly_type_name
        values['writable'] = converter.can_edit
        values['key_exists'] = True
        values['value_placeholder'] = converter.placeholder
      else:
        values['writable'] = True
        values['key_exists'] = False

    if values['show_stats']:
      memcache_stats = memcache.get_stats()
      if not memcache_stats:
        # No stats means no memcache usage.
        memcache_stats = {'hits': 0, 'misses': 0, 'byte_hits': 0, 'items': 0,
                          'bytes': 0, 'oldest_item_age': 0}
      values['stats'] = memcache_stats
      try:
        hitratio = memcache_stats['hits'] * 100 / (memcache_stats['hits']
                                                   + memcache_stats['misses'])
      except ZeroDivisionError:
        hitratio = 0
      values['hitratio'] = hitratio
      # TODO: oldest_item_age should be formatted in a more useful
      # way.
      delta_t = datetime.timedelta(seconds=memcache_stats['oldest_item_age'])
      values['oldest_item_age'] = datetime.datetime.now() - delta_t

    self.response.write(self.render('memcache_viewer.html', values))

  def _urlencode(self, query):
    """Encode a dictionary into a URL query string.

    In contrast to urllib this encodes unicode characters as UTF8.

    Args:
      query: Dictionary of key/value pairs.

    Returns:
      String.
    """
    return '&'.join('%s=%s' % (urllib.quote_plus(k.encode('utf8')),
                               urllib.quote_plus(v.encode('utf8')))
                    for k, v in query.iteritems())

  def post(self):
    """Handle modifying actions and/or redirect to GET page."""
    next_param = {}

    if self.request.get('action:flush'):
      if memcache.flush_all():
        next_param['message'] = 'Cache flushed, all keys dropped.'
      else:
        next_param['message'] = 'Flushing the cache failed.  Please try again.'

    elif self.request.get('action:display'):
      next_param['key'] = self.request.get('key')

    elif self.request.get('action:edit'):
      next_param['edit'] = self.request.get('key')

    elif self.request.get('action:delete'):
      key = self.request.get('key')
      result = memcache.delete(key)
      if result == memcache.DELETE_NETWORK_FAILURE:
        next_param['message'] = ('ERROR: Network failure, key "%s" not deleted.'
                                 % key)
      elif result == memcache.DELETE_ITEM_MISSING:
        next_param['message'] = 'Key "%s" not in cache.' % key
      elif result == memcache.DELETE_SUCCESSFUL:
        next_param['message'] = 'Key "%s" deleted.' % key
      else:
        next_param['message'] = ('Unknown return value.  Key "%s" might still '
                                 'exist.' % key)

    elif self.request.get('action:save'):
      key = self.request.get('key')
      value = self.request.get('value')
      type_ = self.request.get('type')
      next_param['key'] = key

      converter = self.FRIENDLY_TYPE_NAME_TO_CONVERTER[type_]
      try:
        memcache_value = converter.to_cache(value)
      except ValueError as e:
        next_param['message'] = 'ERROR: Failed to save key "%s": %s.' % (key, e)
      else:
        if self._set_memcache_value(key,
                                    memcache_value,
                                    converter.memcache_type):
          next_param['message'] = 'Key "%s" saved.' % key
        else:
          next_param['message'] = 'ERROR: Failed to save key "%s".' % key
    elif self.request.get('action:cancel'):
      next_param['key'] = self.request.get('key')
    else:
      next_param['message'] = 'Unknown action.'

    next = self.request.path_url
    if next_param:
      next = '%s?%s' % (next, self._urlencode(next_param))
    self.redirect(next)
