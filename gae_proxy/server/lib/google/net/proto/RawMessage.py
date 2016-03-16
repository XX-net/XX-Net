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


"""
This is the Python counterpart to the RawMessage class defined in rawmessage.h.

To use this, put the following line in your .proto file:

python from google.net.proto.RawMessage import RawMessage

"""


__pychecker__ = 'no-callinit no-argsused'

from google.net.proto import ProtocolBuffer

class RawMessage(ProtocolBuffer.ProtocolMessage):
  """
  This is a special subclass of ProtocolMessage that doesn't interpret its data
  in any way. Instead, it just stores it in a string.

  See rawmessage.h for more details.
  """

  def __init__(self, initial=None):
    self.__contents = ''
    if initial is not None:
      self.MergeFromString(initial)

  def contents(self):
    return self.__contents

  def set_contents(self, contents):
    self.__contents = contents

  def Clear(self):
    self.__contents = ''

  def IsInitialized(self, debug_strs=None):
    return 1

  def __str__(self, prefix="", printElemNumber=0):
    return prefix + self.DebugFormatString(self.__contents)

  def OutputUnchecked(self, e):
    e.putRawString(self.__contents)

  def OutputPartial(self, e):
    return self.OutputUnchecked(e)

  def TryMerge(self, d):
    self.__contents = d.getRawString()

  def MergeFrom(self, pb):
    assert pb is not self
    if pb.__class__ != self.__class__:
      return 0
    self.__contents = pb.__contents
    return 1

  def Equals(self, pb):
    return self.__contents == pb.__contents

  def __eq__(self, other):
    return (other is not None) and (other.__class__ == self.__class__) and self.Equals(other)

  def __ne__(self, other):
    return not (self == other)

  def ByteSize(self):
    return len(self.__contents)

  def ByteSizePartial(self):
    return self.ByteSize()
