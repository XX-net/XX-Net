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


"""A simple tokenizer used for the Full Text Search API stub."""





import re


from google.appengine.datastore import document_pb
from google.appengine.api.search import search_util
from google.appengine.api.search.stub import tokens



_WORD_SEPARATORS = [
    r'!', r'\"', r'%', r'\(', r'\)', r'\*', r',', r'\.', r'/', r'\:', r'=',
    r'>', r'\?', r'@', r'\[', r'\\', r'\]', r'\^', r'\`', r'\{', r'\|', r'\}',
    r'~', r'\t', r'\n', r'\f', r'\r', r' ', r'&', r'#', r'$', r';']
_WORD_SEPARATOR_RE = re.compile('|'.join(_WORD_SEPARATORS))


def _StripSeparators(value):
  """Remove special characters and collapse spaces."""
  return re.sub(r'  [ ]*', ' ', re.sub(_WORD_SEPARATOR_RE, ' ', value))


def NormalizeString(value):
  """Lowers case, removes punctuation and collapses whitespace."""
  return _StripSeparators(value).lower().strip()


class SimpleTokenizer(object):
  """A tokenizer which converts text to a normalized stream of tokens.

  Text normalization lowers case, removes punctuation and splits on whitespace.
  """

  def __init__(self, split_restricts=True, preserve_case=False):
    self._split_restricts = split_restricts
    self._preserve_case = preserve_case
    self._html_pattern = re.compile(r'<[^>]*>')

  def SetCase(self, value):



    if hasattr(self, '_preserve_case') and self._preserve_case:
      return value
    else:
      return value.lower()

  def TokenizeText(self, text, token_position=0,
                   input_field_type=document_pb.FieldValue.TEXT):
    """Tokenizes the text into a sequence of Tokens."""
    return self._TokenizeForType(field_type=input_field_type,
                                 value=text, token_position=token_position)

  def TokenizeValue(self, field_value, token_position=0):
    """Tokenizes a document_pb.FieldValue into a sequence of Tokens."""
    if field_value.type() == document_pb.FieldValue.GEO:
      return self._TokenizeForType(field_type=field_value.type(),
                                   value=field_value.geo(),
                                   token_position=token_position)
    return self._TokenizeForType(
        field_type=field_value.type(),
        value=search_util.RemoveAccentsNfkd(field_value.string_value()),
        token_position=token_position)

  def _TokenizeString(self, value, field_type):
    value = self.SetCase(value)
    if field_type != document_pb.FieldValue.ATOM:
      if field_type == document_pb.FieldValue.HTML:
        value = self._StripHtmlTags(value)
      value = _StripSeparators(value)
      return value.split()
    else:
      return [value]

  def _StripHtmlTags(self, value):
    """Replace HTML tags with spaces."""
    return self._html_pattern.sub(' ', value)

  def _TokenizeForType(self, field_type, value, token_position=0):
    """Tokenizes value into a sequence of Tokens."""
    if field_type == document_pb.FieldValue.NUMBER:
      return [tokens.Token(chars=value, position=token_position)]

    if field_type == document_pb.FieldValue.GEO:
      return [tokens.GeoPoint(latitude=value.lat(), longitude=value.lng(),
                              position=token_position)]

    tokens_found = []
    token_strings = []

    if not self._split_restricts:
      token_strings = self.SetCase(value).split()
    else:
      token_strings = self._TokenizeString(value, field_type)
    for token in token_strings:
      if ':' in token and self._split_restricts:
        for subtoken in token.split(':'):
          tokens_found.append(
              tokens.Token(chars=subtoken, position=token_position))
          token_position += 1
      elif '"' in token:
        for subtoken in token.split('"'):
          if not subtoken:
            tokens_found.append(
                tokens.Quote(chars='"', position=token_position))
          else:
            tokens_found.append(
                tokens.Token(chars=subtoken, position=token_position))
          token_position += 1
      else:
        tokens_found.append(tokens.Token(chars=token, position=token_position))
        token_position += 1
    return tokens_found
