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

class ChannelServiceError(ProtocolBuffer.ProtocolMessage):


  OK           =    0
  INTERNAL_ERROR =    1
  INVALID_CHANNEL_KEY =    2
  BAD_MESSAGE  =    3
  INVALID_CHANNEL_TOKEN_DURATION =    4
  APPID_ALIAS_REQUIRED =    5

  _ErrorCode_NAMES = {
    0: "OK",
    1: "INTERNAL_ERROR",
    2: "INVALID_CHANNEL_KEY",
    3: "BAD_MESSAGE",
    4: "INVALID_CHANNEL_TOKEN_DURATION",
    5: "APPID_ALIAS_REQUIRED",
  }

  def ErrorCode_Name(cls, x): return cls._ErrorCode_NAMES.get(x, "")
  ErrorCode_Name = classmethod(ErrorCode_Name)


  def __init__(self, contents=None):
    pass
    if contents is not None: self.MergeFromString(contents)


  def MergeFrom(self, x):
    assert x is not self

  def Equals(self, x):
    if x is self: return 1
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    return n

  def ByteSizePartial(self):
    n = 0
    return n

  def Clear(self):
    pass

  def OutputUnchecked(self, out):
    pass

  def OutputPartial(self, out):
    pass

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])


  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
  }, 0)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
  }, 0, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ChannelServiceError'
class CreateChannelRequest(ProtocolBuffer.ProtocolMessage):
  has_application_key_ = 0
  application_key_ = ""
  has_duration_minutes_ = 0
  duration_minutes_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def application_key(self): return self.application_key_

  def set_application_key(self, x):
    self.has_application_key_ = 1
    self.application_key_ = x

  def clear_application_key(self):
    if self.has_application_key_:
      self.has_application_key_ = 0
      self.application_key_ = ""

  def has_application_key(self): return self.has_application_key_

  def duration_minutes(self): return self.duration_minutes_

  def set_duration_minutes(self, x):
    self.has_duration_minutes_ = 1
    self.duration_minutes_ = x

  def clear_duration_minutes(self):
    if self.has_duration_minutes_:
      self.has_duration_minutes_ = 0
      self.duration_minutes_ = 0

  def has_duration_minutes(self): return self.has_duration_minutes_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_application_key()): self.set_application_key(x.application_key())
    if (x.has_duration_minutes()): self.set_duration_minutes(x.duration_minutes())

  def Equals(self, x):
    if x is self: return 1
    if self.has_application_key_ != x.has_application_key_: return 0
    if self.has_application_key_ and self.application_key_ != x.application_key_: return 0
    if self.has_duration_minutes_ != x.has_duration_minutes_: return 0
    if self.has_duration_minutes_ and self.duration_minutes_ != x.duration_minutes_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_application_key_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: application_key not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.application_key_))
    if (self.has_duration_minutes_): n += 1 + self.lengthVarInt64(self.duration_minutes_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_application_key_):
      n += 1
      n += self.lengthString(len(self.application_key_))
    if (self.has_duration_minutes_): n += 1 + self.lengthVarInt64(self.duration_minutes_)
    return n

  def Clear(self):
    self.clear_application_key()
    self.clear_duration_minutes()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.application_key_)
    if (self.has_duration_minutes_):
      out.putVarInt32(16)
      out.putVarInt32(self.duration_minutes_)

  def OutputPartial(self, out):
    if (self.has_application_key_):
      out.putVarInt32(10)
      out.putPrefixedString(self.application_key_)
    if (self.has_duration_minutes_):
      out.putVarInt32(16)
      out.putVarInt32(self.duration_minutes_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_application_key(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_duration_minutes(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_application_key_: res+=prefix+("application_key: %s\n" % self.DebugFormatString(self.application_key_))
    if self.has_duration_minutes_: res+=prefix+("duration_minutes: %s\n" % self.DebugFormatInt32(self.duration_minutes_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapplication_key = 1
  kduration_minutes = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "application_key",
    2: "duration_minutes",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CreateChannelRequest'
class CreateChannelResponse(ProtocolBuffer.ProtocolMessage):
  has_token_ = 0
  token_ = ""
  has_duration_minutes_ = 0
  duration_minutes_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def token(self): return self.token_

  def set_token(self, x):
    self.has_token_ = 1
    self.token_ = x

  def clear_token(self):
    if self.has_token_:
      self.has_token_ = 0
      self.token_ = ""

  def has_token(self): return self.has_token_

  def duration_minutes(self): return self.duration_minutes_

  def set_duration_minutes(self, x):
    self.has_duration_minutes_ = 1
    self.duration_minutes_ = x

  def clear_duration_minutes(self):
    if self.has_duration_minutes_:
      self.has_duration_minutes_ = 0
      self.duration_minutes_ = 0

  def has_duration_minutes(self): return self.has_duration_minutes_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_token()): self.set_token(x.token())
    if (x.has_duration_minutes()): self.set_duration_minutes(x.duration_minutes())

  def Equals(self, x):
    if x is self: return 1
    if self.has_token_ != x.has_token_: return 0
    if self.has_token_ and self.token_ != x.token_: return 0
    if self.has_duration_minutes_ != x.has_duration_minutes_: return 0
    if self.has_duration_minutes_ and self.duration_minutes_ != x.duration_minutes_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_token_): n += 1 + self.lengthString(len(self.token_))
    if (self.has_duration_minutes_): n += 1 + self.lengthVarInt64(self.duration_minutes_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_token_): n += 1 + self.lengthString(len(self.token_))
    if (self.has_duration_minutes_): n += 1 + self.lengthVarInt64(self.duration_minutes_)
    return n

  def Clear(self):
    self.clear_token()
    self.clear_duration_minutes()

  def OutputUnchecked(self, out):
    if (self.has_token_):
      out.putVarInt32(18)
      out.putPrefixedString(self.token_)
    if (self.has_duration_minutes_):
      out.putVarInt32(24)
      out.putVarInt32(self.duration_minutes_)

  def OutputPartial(self, out):
    if (self.has_token_):
      out.putVarInt32(18)
      out.putPrefixedString(self.token_)
    if (self.has_duration_minutes_):
      out.putVarInt32(24)
      out.putVarInt32(self.duration_minutes_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 18:
        self.set_token(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_duration_minutes(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_token_: res+=prefix+("token: %s\n" % self.DebugFormatString(self.token_))
    if self.has_duration_minutes_: res+=prefix+("duration_minutes: %s\n" % self.DebugFormatInt32(self.duration_minutes_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktoken = 2
  kduration_minutes = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    2: "token",
    3: "duration_minutes",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CreateChannelResponse'
class SendMessageRequest(ProtocolBuffer.ProtocolMessage):
  has_application_key_ = 0
  application_key_ = ""
  has_message_ = 0
  message_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def application_key(self): return self.application_key_

  def set_application_key(self, x):
    self.has_application_key_ = 1
    self.application_key_ = x

  def clear_application_key(self):
    if self.has_application_key_:
      self.has_application_key_ = 0
      self.application_key_ = ""

  def has_application_key(self): return self.has_application_key_

  def message(self): return self.message_

  def set_message(self, x):
    self.has_message_ = 1
    self.message_ = x

  def clear_message(self):
    if self.has_message_:
      self.has_message_ = 0
      self.message_ = ""

  def has_message(self): return self.has_message_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_application_key()): self.set_application_key(x.application_key())
    if (x.has_message()): self.set_message(x.message())

  def Equals(self, x):
    if x is self: return 1
    if self.has_application_key_ != x.has_application_key_: return 0
    if self.has_application_key_ and self.application_key_ != x.application_key_: return 0
    if self.has_message_ != x.has_message_: return 0
    if self.has_message_ and self.message_ != x.message_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_application_key_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: application_key not set.')
    if (not self.has_message_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: message not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.application_key_))
    n += self.lengthString(len(self.message_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_application_key_):
      n += 1
      n += self.lengthString(len(self.application_key_))
    if (self.has_message_):
      n += 1
      n += self.lengthString(len(self.message_))
    return n

  def Clear(self):
    self.clear_application_key()
    self.clear_message()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.application_key_)
    out.putVarInt32(18)
    out.putPrefixedString(self.message_)

  def OutputPartial(self, out):
    if (self.has_application_key_):
      out.putVarInt32(10)
      out.putPrefixedString(self.application_key_)
    if (self.has_message_):
      out.putVarInt32(18)
      out.putPrefixedString(self.message_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_application_key(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_message(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_application_key_: res+=prefix+("application_key: %s\n" % self.DebugFormatString(self.application_key_))
    if self.has_message_: res+=prefix+("message: %s\n" % self.DebugFormatString(self.message_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapplication_key = 1
  kmessage = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "application_key",
    2: "message",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SendMessageRequest'
if _extension_runtime:
  pass

__all__ = ['ChannelServiceError','CreateChannelRequest','CreateChannelResponse','SendMessageRequest']
