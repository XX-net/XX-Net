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


"""Token classes for the Full Text Search API stub."""





from google.appengine.api.search import search_util


class Token(object):
  """Represents a token, usually a word, extracted from some document field."""

  def __init__(self, chars=None, position=None, field_name=None):
    """Initializer.

    Args:
      chars: The string representation of the token.
      position: The position of the token in the sequence from the document
        field.
      field_name: The name of the field the token occured in.

    Raises:
      TypeError: If an unknown argument is passed.
    """
    if isinstance(chars, basestring) and not isinstance(chars, unicode):
      chars = unicode(chars, 'utf-8')
    self._chars = chars
    self._position = position
    self._field_name = field_name

  @property
  def chars(self):
    """Returns a list of fields of the document."""
    value = self._chars
    if not isinstance(value, basestring):
      value = str(self._chars)
    if self._field_name:
      return self._field_name + ':' + value
    return value

  @property
  def position(self):
    """Returns a list of fields of the document."""
    return self._position

  def RestrictField(self, field_name):
    """Creates a copy of this Token and sets field_name."""
    return Token(chars=self.chars, position=self.position,
                 field_name=field_name)

  def __repr__(self):
    return search_util.Repr(
        self, [('chars', self.chars), ('position', self.position)])

  def __eq__(self, other):
    return (isinstance(other, Token) and
            self.chars.lower() == other.chars.lower())

  def __hash__(self):
    return hash(self.chars)


class Quote(Token):
  """Represents a single or double quote in a document field or query."""

  def __init__(self, **kwargs):
    Token.__init__(self, **kwargs)


class Number(Token):
  """Represents a number in a document field or query."""

  def __init__(self, **kwargs):
    Token.__init__(self, **kwargs)


class GeoPoint(Token):
  """Represents a geo point in a document field or query."""

  def __init__(self, **kwargs):
    self._latitude = kwargs.pop('latitude')
    self._longitude = kwargs.pop('longitude')
    Token.__init__(self, **kwargs)

  @property
  def latitude(self):
    """Returns the angle between equatorial plan and line thru the geo point."""
    return self._latitude

  @property
  def longitude(self):
    """Returns the angle from a reference meridian to another meridian."""
    return self._longitude
