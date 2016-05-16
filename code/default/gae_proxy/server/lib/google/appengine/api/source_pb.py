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



from google.net.proto import ProtocolBuffer
import array
import dummy_thread as thread

__pychecker__ = """maxreturns=0 maxbranches=0 no-callinit
                   unusednames=printElemNumber,debug_strs no-special"""

if hasattr(ProtocolBuffer, 'ExtendableProtocolMessage'):
  _extension_runtime = True
  _ExtendableProtocolMessage = ProtocolBuffer.ExtendableProtocolMessage
else:
  _extension_runtime = False
  _ExtendableProtocolMessage = ProtocolBuffer.ProtocolMessage

class SourceLocation(ProtocolBuffer.ProtocolMessage):
  has_file_ = 0
  file_ = ""
  has_line_ = 0
  line_ = 0
  has_function_name_ = 0
  function_name_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def file(self): return self.file_

  def set_file(self, x):
    self.has_file_ = 1
    self.file_ = x

  def clear_file(self):
    if self.has_file_:
      self.has_file_ = 0
      self.file_ = ""

  def has_file(self): return self.has_file_

  def line(self): return self.line_

  def set_line(self, x):
    self.has_line_ = 1
    self.line_ = x

  def clear_line(self):
    if self.has_line_:
      self.has_line_ = 0
      self.line_ = 0

  def has_line(self): return self.has_line_

  def function_name(self): return self.function_name_

  def set_function_name(self, x):
    self.has_function_name_ = 1
    self.function_name_ = x

  def clear_function_name(self):
    if self.has_function_name_:
      self.has_function_name_ = 0
      self.function_name_ = ""

  def has_function_name(self): return self.has_function_name_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_file()): self.set_file(x.file())
    if (x.has_line()): self.set_line(x.line())
    if (x.has_function_name()): self.set_function_name(x.function_name())

  def Equals(self, x):
    if x is self: return 1
    if self.has_file_ != x.has_file_: return 0
    if self.has_file_ and self.file_ != x.file_: return 0
    if self.has_line_ != x.has_line_: return 0
    if self.has_line_ and self.line_ != x.line_: return 0
    if self.has_function_name_ != x.has_function_name_: return 0
    if self.has_function_name_ and self.function_name_ != x.function_name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_file_): n += 1 + self.lengthString(len(self.file_))
    if (self.has_line_): n += 1 + self.lengthVarInt64(self.line_)
    if (self.has_function_name_): n += 1 + self.lengthString(len(self.function_name_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_file_): n += 1 + self.lengthString(len(self.file_))
    if (self.has_line_): n += 1 + self.lengthVarInt64(self.line_)
    if (self.has_function_name_): n += 1 + self.lengthString(len(self.function_name_))
    return n

  def Clear(self):
    self.clear_file()
    self.clear_line()
    self.clear_function_name()

  def OutputUnchecked(self, out):
    if (self.has_file_):
      out.putVarInt32(10)
      out.putPrefixedString(self.file_)
    if (self.has_line_):
      out.putVarInt32(16)
      out.putVarInt64(self.line_)
    if (self.has_function_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.function_name_)

  def OutputPartial(self, out):
    if (self.has_file_):
      out.putVarInt32(10)
      out.putPrefixedString(self.file_)
    if (self.has_line_):
      out.putVarInt32(16)
      out.putVarInt64(self.line_)
    if (self.has_function_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.function_name_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_file(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_line(d.getVarInt64())
        continue
      if tt == 26:
        self.set_function_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_file_: res+=prefix+("file: %s\n" % self.DebugFormatString(self.file_))
    if self.has_line_: res+=prefix+("line: %s\n" % self.DebugFormatInt64(self.line_))
    if self.has_function_name_: res+=prefix+("function_name: %s\n" % self.DebugFormatString(self.function_name_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kfile = 1
  kline = 2
  kfunction_name = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "file",
    2: "line",
    3: "function_name",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SourceLocation'
if _extension_runtime:
  pass

__all__ = ['SourceLocation']
