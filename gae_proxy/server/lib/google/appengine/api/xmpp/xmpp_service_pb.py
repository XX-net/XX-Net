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

from google.appengine.api.api_base_pb import *
import google.appengine.api.api_base_pb
from google.appengine.api.channel.channel_service_pb import *
import google.appengine.api.channel.channel_service_pb
class XmppServiceError(ProtocolBuffer.ProtocolMessage):


  UNSPECIFIED_ERROR =    1
  INVALID_JID  =    2
  NO_BODY      =    3
  INVALID_XML  =    4
  INVALID_TYPE =    5
  INVALID_SHOW =    6
  EXCEEDED_MAX_SIZE =    7
  APPID_ALIAS_REQUIRED =    8
  NONDEFAULT_MODULE =    9

  _ErrorCode_NAMES = {
    1: "UNSPECIFIED_ERROR",
    2: "INVALID_JID",
    3: "NO_BODY",
    4: "INVALID_XML",
    5: "INVALID_TYPE",
    6: "INVALID_SHOW",
    7: "EXCEEDED_MAX_SIZE",
    8: "APPID_ALIAS_REQUIRED",
    9: "NONDEFAULT_MODULE",
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.XmppServiceError'
class PresenceRequest(ProtocolBuffer.ProtocolMessage):
  has_jid_ = 0
  jid_ = ""
  has_from_jid_ = 0
  from_jid_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def jid(self): return self.jid_

  def set_jid(self, x):
    self.has_jid_ = 1
    self.jid_ = x

  def clear_jid(self):
    if self.has_jid_:
      self.has_jid_ = 0
      self.jid_ = ""

  def has_jid(self): return self.has_jid_

  def from_jid(self): return self.from_jid_

  def set_from_jid(self, x):
    self.has_from_jid_ = 1
    self.from_jid_ = x

  def clear_from_jid(self):
    if self.has_from_jid_:
      self.has_from_jid_ = 0
      self.from_jid_ = ""

  def has_from_jid(self): return self.has_from_jid_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_jid()): self.set_jid(x.jid())
    if (x.has_from_jid()): self.set_from_jid(x.from_jid())

  def Equals(self, x):
    if x is self: return 1
    if self.has_jid_ != x.has_jid_: return 0
    if self.has_jid_ and self.jid_ != x.jid_: return 0
    if self.has_from_jid_ != x.has_from_jid_: return 0
    if self.has_from_jid_ and self.from_jid_ != x.from_jid_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_jid_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: jid not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.jid_))
    if (self.has_from_jid_): n += 1 + self.lengthString(len(self.from_jid_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_jid_):
      n += 1
      n += self.lengthString(len(self.jid_))
    if (self.has_from_jid_): n += 1 + self.lengthString(len(self.from_jid_))
    return n

  def Clear(self):
    self.clear_jid()
    self.clear_from_jid()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.jid_)
    if (self.has_from_jid_):
      out.putVarInt32(18)
      out.putPrefixedString(self.from_jid_)

  def OutputPartial(self, out):
    if (self.has_jid_):
      out.putVarInt32(10)
      out.putPrefixedString(self.jid_)
    if (self.has_from_jid_):
      out.putVarInt32(18)
      out.putPrefixedString(self.from_jid_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_jid(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_from_jid(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_jid_: res+=prefix+("jid: %s\n" % self.DebugFormatString(self.jid_))
    if self.has_from_jid_: res+=prefix+("from_jid: %s\n" % self.DebugFormatString(self.from_jid_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kjid = 1
  kfrom_jid = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "jid",
    2: "from_jid",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.PresenceRequest'
class PresenceResponse(ProtocolBuffer.ProtocolMessage):


  NORMAL       =    0
  AWAY         =    1
  DO_NOT_DISTURB =    2
  CHAT         =    3
  EXTENDED_AWAY =    4

  _SHOW_NAMES = {
    0: "NORMAL",
    1: "AWAY",
    2: "DO_NOT_DISTURB",
    3: "CHAT",
    4: "EXTENDED_AWAY",
  }

  def SHOW_Name(cls, x): return cls._SHOW_NAMES.get(x, "")
  SHOW_Name = classmethod(SHOW_Name)

  has_is_available_ = 0
  is_available_ = 0
  has_presence_ = 0
  presence_ = 0
  has_valid_ = 0
  valid_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def is_available(self): return self.is_available_

  def set_is_available(self, x):
    self.has_is_available_ = 1
    self.is_available_ = x

  def clear_is_available(self):
    if self.has_is_available_:
      self.has_is_available_ = 0
      self.is_available_ = 0

  def has_is_available(self): return self.has_is_available_

  def presence(self): return self.presence_

  def set_presence(self, x):
    self.has_presence_ = 1
    self.presence_ = x

  def clear_presence(self):
    if self.has_presence_:
      self.has_presence_ = 0
      self.presence_ = 0

  def has_presence(self): return self.has_presence_

  def valid(self): return self.valid_

  def set_valid(self, x):
    self.has_valid_ = 1
    self.valid_ = x

  def clear_valid(self):
    if self.has_valid_:
      self.has_valid_ = 0
      self.valid_ = 0

  def has_valid(self): return self.has_valid_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_is_available()): self.set_is_available(x.is_available())
    if (x.has_presence()): self.set_presence(x.presence())
    if (x.has_valid()): self.set_valid(x.valid())

  def Equals(self, x):
    if x is self: return 1
    if self.has_is_available_ != x.has_is_available_: return 0
    if self.has_is_available_ and self.is_available_ != x.is_available_: return 0
    if self.has_presence_ != x.has_presence_: return 0
    if self.has_presence_ and self.presence_ != x.presence_: return 0
    if self.has_valid_ != x.has_valid_: return 0
    if self.has_valid_ and self.valid_ != x.valid_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_is_available_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: is_available not set.')
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_presence_): n += 1 + self.lengthVarInt64(self.presence_)
    if (self.has_valid_): n += 2
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_is_available_):
      n += 2
    if (self.has_presence_): n += 1 + self.lengthVarInt64(self.presence_)
    if (self.has_valid_): n += 2
    return n

  def Clear(self):
    self.clear_is_available()
    self.clear_presence()
    self.clear_valid()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putBoolean(self.is_available_)
    if (self.has_presence_):
      out.putVarInt32(16)
      out.putVarInt32(self.presence_)
    if (self.has_valid_):
      out.putVarInt32(24)
      out.putBoolean(self.valid_)

  def OutputPartial(self, out):
    if (self.has_is_available_):
      out.putVarInt32(8)
      out.putBoolean(self.is_available_)
    if (self.has_presence_):
      out.putVarInt32(16)
      out.putVarInt32(self.presence_)
    if (self.has_valid_):
      out.putVarInt32(24)
      out.putBoolean(self.valid_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_is_available(d.getBoolean())
        continue
      if tt == 16:
        self.set_presence(d.getVarInt32())
        continue
      if tt == 24:
        self.set_valid(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_is_available_: res+=prefix+("is_available: %s\n" % self.DebugFormatBool(self.is_available_))
    if self.has_presence_: res+=prefix+("presence: %s\n" % self.DebugFormatInt32(self.presence_))
    if self.has_valid_: res+=prefix+("valid: %s\n" % self.DebugFormatBool(self.valid_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kis_available = 1
  kpresence = 2
  kvalid = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "is_available",
    2: "presence",
    3: "valid",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.PresenceResponse'
class BulkPresenceRequest(ProtocolBuffer.ProtocolMessage):
  has_from_jid_ = 0
  from_jid_ = ""

  def __init__(self, contents=None):
    self.jid_ = []
    if contents is not None: self.MergeFromString(contents)

  def jid_size(self): return len(self.jid_)
  def jid_list(self): return self.jid_

  def jid(self, i):
    return self.jid_[i]

  def set_jid(self, i, x):
    self.jid_[i] = x

  def add_jid(self, x):
    self.jid_.append(x)

  def clear_jid(self):
    self.jid_ = []

  def from_jid(self): return self.from_jid_

  def set_from_jid(self, x):
    self.has_from_jid_ = 1
    self.from_jid_ = x

  def clear_from_jid(self):
    if self.has_from_jid_:
      self.has_from_jid_ = 0
      self.from_jid_ = ""

  def has_from_jid(self): return self.has_from_jid_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.jid_size()): self.add_jid(x.jid(i))
    if (x.has_from_jid()): self.set_from_jid(x.from_jid())

  def Equals(self, x):
    if x is self: return 1
    if len(self.jid_) != len(x.jid_): return 0
    for e1, e2 in zip(self.jid_, x.jid_):
      if e1 != e2: return 0
    if self.has_from_jid_ != x.has_from_jid_: return 0
    if self.has_from_jid_ and self.from_jid_ != x.from_jid_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.jid_)
    for i in xrange(len(self.jid_)): n += self.lengthString(len(self.jid_[i]))
    if (self.has_from_jid_): n += 1 + self.lengthString(len(self.from_jid_))
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.jid_)
    for i in xrange(len(self.jid_)): n += self.lengthString(len(self.jid_[i]))
    if (self.has_from_jid_): n += 1 + self.lengthString(len(self.from_jid_))
    return n

  def Clear(self):
    self.clear_jid()
    self.clear_from_jid()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.jid_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.jid_[i])
    if (self.has_from_jid_):
      out.putVarInt32(18)
      out.putPrefixedString(self.from_jid_)

  def OutputPartial(self, out):
    for i in xrange(len(self.jid_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.jid_[i])
    if (self.has_from_jid_):
      out.putVarInt32(18)
      out.putPrefixedString(self.from_jid_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.add_jid(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_from_jid(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.jid_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("jid%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_from_jid_: res+=prefix+("from_jid: %s\n" % self.DebugFormatString(self.from_jid_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kjid = 1
  kfrom_jid = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "jid",
    2: "from_jid",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.BulkPresenceRequest'
class BulkPresenceResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.presence_response_ = []
    if contents is not None: self.MergeFromString(contents)

  def presence_response_size(self): return len(self.presence_response_)
  def presence_response_list(self): return self.presence_response_

  def presence_response(self, i):
    return self.presence_response_[i]

  def mutable_presence_response(self, i):
    return self.presence_response_[i]

  def add_presence_response(self):
    x = PresenceResponse()
    self.presence_response_.append(x)
    return x

  def clear_presence_response(self):
    self.presence_response_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.presence_response_size()): self.add_presence_response().CopyFrom(x.presence_response(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.presence_response_) != len(x.presence_response_): return 0
    for e1, e2 in zip(self.presence_response_, x.presence_response_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.presence_response_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.presence_response_)
    for i in xrange(len(self.presence_response_)): n += self.lengthString(self.presence_response_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.presence_response_)
    for i in xrange(len(self.presence_response_)): n += self.lengthString(self.presence_response_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_presence_response()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.presence_response_)):
      out.putVarInt32(10)
      out.putVarInt32(self.presence_response_[i].ByteSize())
      self.presence_response_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.presence_response_)):
      out.putVarInt32(10)
      out.putVarInt32(self.presence_response_[i].ByteSizePartial())
      self.presence_response_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_presence_response().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.presence_response_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("presence_response%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kpresence_response = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "presence_response",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.BulkPresenceResponse'
class XmppMessageRequest(ProtocolBuffer.ProtocolMessage):
  has_body_ = 0
  body_ = ""
  has_raw_xml_ = 0
  raw_xml_ = 0
  has_type_ = 0
  type_ = "chat"
  has_from_jid_ = 0
  from_jid_ = ""

  def __init__(self, contents=None):
    self.jid_ = []
    if contents is not None: self.MergeFromString(contents)

  def jid_size(self): return len(self.jid_)
  def jid_list(self): return self.jid_

  def jid(self, i):
    return self.jid_[i]

  def set_jid(self, i, x):
    self.jid_[i] = x

  def add_jid(self, x):
    self.jid_.append(x)

  def clear_jid(self):
    self.jid_ = []

  def body(self): return self.body_

  def set_body(self, x):
    self.has_body_ = 1
    self.body_ = x

  def clear_body(self):
    if self.has_body_:
      self.has_body_ = 0
      self.body_ = ""

  def has_body(self): return self.has_body_

  def raw_xml(self): return self.raw_xml_

  def set_raw_xml(self, x):
    self.has_raw_xml_ = 1
    self.raw_xml_ = x

  def clear_raw_xml(self):
    if self.has_raw_xml_:
      self.has_raw_xml_ = 0
      self.raw_xml_ = 0

  def has_raw_xml(self): return self.has_raw_xml_

  def type(self): return self.type_

  def set_type(self, x):
    self.has_type_ = 1
    self.type_ = x

  def clear_type(self):
    if self.has_type_:
      self.has_type_ = 0
      self.type_ = "chat"

  def has_type(self): return self.has_type_

  def from_jid(self): return self.from_jid_

  def set_from_jid(self, x):
    self.has_from_jid_ = 1
    self.from_jid_ = x

  def clear_from_jid(self):
    if self.has_from_jid_:
      self.has_from_jid_ = 0
      self.from_jid_ = ""

  def has_from_jid(self): return self.has_from_jid_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.jid_size()): self.add_jid(x.jid(i))
    if (x.has_body()): self.set_body(x.body())
    if (x.has_raw_xml()): self.set_raw_xml(x.raw_xml())
    if (x.has_type()): self.set_type(x.type())
    if (x.has_from_jid()): self.set_from_jid(x.from_jid())

  def Equals(self, x):
    if x is self: return 1
    if len(self.jid_) != len(x.jid_): return 0
    for e1, e2 in zip(self.jid_, x.jid_):
      if e1 != e2: return 0
    if self.has_body_ != x.has_body_: return 0
    if self.has_body_ and self.body_ != x.body_: return 0
    if self.has_raw_xml_ != x.has_raw_xml_: return 0
    if self.has_raw_xml_ and self.raw_xml_ != x.raw_xml_: return 0
    if self.has_type_ != x.has_type_: return 0
    if self.has_type_ and self.type_ != x.type_: return 0
    if self.has_from_jid_ != x.has_from_jid_: return 0
    if self.has_from_jid_ and self.from_jid_ != x.from_jid_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_body_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: body not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.jid_)
    for i in xrange(len(self.jid_)): n += self.lengthString(len(self.jid_[i]))
    n += self.lengthString(len(self.body_))
    if (self.has_raw_xml_): n += 2
    if (self.has_type_): n += 1 + self.lengthString(len(self.type_))
    if (self.has_from_jid_): n += 1 + self.lengthString(len(self.from_jid_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.jid_)
    for i in xrange(len(self.jid_)): n += self.lengthString(len(self.jid_[i]))
    if (self.has_body_):
      n += 1
      n += self.lengthString(len(self.body_))
    if (self.has_raw_xml_): n += 2
    if (self.has_type_): n += 1 + self.lengthString(len(self.type_))
    if (self.has_from_jid_): n += 1 + self.lengthString(len(self.from_jid_))
    return n

  def Clear(self):
    self.clear_jid()
    self.clear_body()
    self.clear_raw_xml()
    self.clear_type()
    self.clear_from_jid()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.jid_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.jid_[i])
    out.putVarInt32(18)
    out.putPrefixedString(self.body_)
    if (self.has_raw_xml_):
      out.putVarInt32(24)
      out.putBoolean(self.raw_xml_)
    if (self.has_type_):
      out.putVarInt32(34)
      out.putPrefixedString(self.type_)
    if (self.has_from_jid_):
      out.putVarInt32(42)
      out.putPrefixedString(self.from_jid_)

  def OutputPartial(self, out):
    for i in xrange(len(self.jid_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.jid_[i])
    if (self.has_body_):
      out.putVarInt32(18)
      out.putPrefixedString(self.body_)
    if (self.has_raw_xml_):
      out.putVarInt32(24)
      out.putBoolean(self.raw_xml_)
    if (self.has_type_):
      out.putVarInt32(34)
      out.putPrefixedString(self.type_)
    if (self.has_from_jid_):
      out.putVarInt32(42)
      out.putPrefixedString(self.from_jid_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.add_jid(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_body(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_raw_xml(d.getBoolean())
        continue
      if tt == 34:
        self.set_type(d.getPrefixedString())
        continue
      if tt == 42:
        self.set_from_jid(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.jid_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("jid%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_body_: res+=prefix+("body: %s\n" % self.DebugFormatString(self.body_))
    if self.has_raw_xml_: res+=prefix+("raw_xml: %s\n" % self.DebugFormatBool(self.raw_xml_))
    if self.has_type_: res+=prefix+("type: %s\n" % self.DebugFormatString(self.type_))
    if self.has_from_jid_: res+=prefix+("from_jid: %s\n" % self.DebugFormatString(self.from_jid_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kjid = 1
  kbody = 2
  kraw_xml = 3
  ktype = 4
  kfrom_jid = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "jid",
    2: "body",
    3: "raw_xml",
    4: "type",
    5: "from_jid",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.XmppMessageRequest'
class XmppMessageResponse(ProtocolBuffer.ProtocolMessage):


  NO_ERROR     =    0
  INVALID_JID  =    1
  OTHER_ERROR  =    2

  _XmppMessageStatus_NAMES = {
    0: "NO_ERROR",
    1: "INVALID_JID",
    2: "OTHER_ERROR",
  }

  def XmppMessageStatus_Name(cls, x): return cls._XmppMessageStatus_NAMES.get(x, "")
  XmppMessageStatus_Name = classmethod(XmppMessageStatus_Name)


  def __init__(self, contents=None):
    self.status_ = []
    if contents is not None: self.MergeFromString(contents)

  def status_size(self): return len(self.status_)
  def status_list(self): return self.status_

  def status(self, i):
    return self.status_[i]

  def set_status(self, i, x):
    self.status_[i] = x

  def add_status(self, x):
    self.status_.append(x)

  def clear_status(self):
    self.status_ = []


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.status_size()): self.add_status(x.status(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.status_) != len(x.status_): return 0
    for e1, e2 in zip(self.status_, x.status_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.status_)
    for i in xrange(len(self.status_)): n += self.lengthVarInt64(self.status_[i])
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.status_)
    for i in xrange(len(self.status_)): n += self.lengthVarInt64(self.status_[i])
    return n

  def Clear(self):
    self.clear_status()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.status_)):
      out.putVarInt32(8)
      out.putVarInt32(self.status_[i])

  def OutputPartial(self, out):
    for i in xrange(len(self.status_)):
      out.putVarInt32(8)
      out.putVarInt32(self.status_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.add_status(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.status_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("status%s: %s\n" % (elm, self.DebugFormatInt32(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kstatus = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "status",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.XmppMessageResponse'
class XmppSendPresenceRequest(ProtocolBuffer.ProtocolMessage):
  has_jid_ = 0
  jid_ = ""
  has_type_ = 0
  type_ = ""
  has_show_ = 0
  show_ = ""
  has_status_ = 0
  status_ = ""
  has_from_jid_ = 0
  from_jid_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def jid(self): return self.jid_

  def set_jid(self, x):
    self.has_jid_ = 1
    self.jid_ = x

  def clear_jid(self):
    if self.has_jid_:
      self.has_jid_ = 0
      self.jid_ = ""

  def has_jid(self): return self.has_jid_

  def type(self): return self.type_

  def set_type(self, x):
    self.has_type_ = 1
    self.type_ = x

  def clear_type(self):
    if self.has_type_:
      self.has_type_ = 0
      self.type_ = ""

  def has_type(self): return self.has_type_

  def show(self): return self.show_

  def set_show(self, x):
    self.has_show_ = 1
    self.show_ = x

  def clear_show(self):
    if self.has_show_:
      self.has_show_ = 0
      self.show_ = ""

  def has_show(self): return self.has_show_

  def status(self): return self.status_

  def set_status(self, x):
    self.has_status_ = 1
    self.status_ = x

  def clear_status(self):
    if self.has_status_:
      self.has_status_ = 0
      self.status_ = ""

  def has_status(self): return self.has_status_

  def from_jid(self): return self.from_jid_

  def set_from_jid(self, x):
    self.has_from_jid_ = 1
    self.from_jid_ = x

  def clear_from_jid(self):
    if self.has_from_jid_:
      self.has_from_jid_ = 0
      self.from_jid_ = ""

  def has_from_jid(self): return self.has_from_jid_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_jid()): self.set_jid(x.jid())
    if (x.has_type()): self.set_type(x.type())
    if (x.has_show()): self.set_show(x.show())
    if (x.has_status()): self.set_status(x.status())
    if (x.has_from_jid()): self.set_from_jid(x.from_jid())

  def Equals(self, x):
    if x is self: return 1
    if self.has_jid_ != x.has_jid_: return 0
    if self.has_jid_ and self.jid_ != x.jid_: return 0
    if self.has_type_ != x.has_type_: return 0
    if self.has_type_ and self.type_ != x.type_: return 0
    if self.has_show_ != x.has_show_: return 0
    if self.has_show_ and self.show_ != x.show_: return 0
    if self.has_status_ != x.has_status_: return 0
    if self.has_status_ and self.status_ != x.status_: return 0
    if self.has_from_jid_ != x.has_from_jid_: return 0
    if self.has_from_jid_ and self.from_jid_ != x.from_jid_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_jid_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: jid not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.jid_))
    if (self.has_type_): n += 1 + self.lengthString(len(self.type_))
    if (self.has_show_): n += 1 + self.lengthString(len(self.show_))
    if (self.has_status_): n += 1 + self.lengthString(len(self.status_))
    if (self.has_from_jid_): n += 1 + self.lengthString(len(self.from_jid_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_jid_):
      n += 1
      n += self.lengthString(len(self.jid_))
    if (self.has_type_): n += 1 + self.lengthString(len(self.type_))
    if (self.has_show_): n += 1 + self.lengthString(len(self.show_))
    if (self.has_status_): n += 1 + self.lengthString(len(self.status_))
    if (self.has_from_jid_): n += 1 + self.lengthString(len(self.from_jid_))
    return n

  def Clear(self):
    self.clear_jid()
    self.clear_type()
    self.clear_show()
    self.clear_status()
    self.clear_from_jid()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.jid_)
    if (self.has_type_):
      out.putVarInt32(18)
      out.putPrefixedString(self.type_)
    if (self.has_show_):
      out.putVarInt32(26)
      out.putPrefixedString(self.show_)
    if (self.has_status_):
      out.putVarInt32(34)
      out.putPrefixedString(self.status_)
    if (self.has_from_jid_):
      out.putVarInt32(42)
      out.putPrefixedString(self.from_jid_)

  def OutputPartial(self, out):
    if (self.has_jid_):
      out.putVarInt32(10)
      out.putPrefixedString(self.jid_)
    if (self.has_type_):
      out.putVarInt32(18)
      out.putPrefixedString(self.type_)
    if (self.has_show_):
      out.putVarInt32(26)
      out.putPrefixedString(self.show_)
    if (self.has_status_):
      out.putVarInt32(34)
      out.putPrefixedString(self.status_)
    if (self.has_from_jid_):
      out.putVarInt32(42)
      out.putPrefixedString(self.from_jid_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_jid(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_type(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_show(d.getPrefixedString())
        continue
      if tt == 34:
        self.set_status(d.getPrefixedString())
        continue
      if tt == 42:
        self.set_from_jid(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_jid_: res+=prefix+("jid: %s\n" % self.DebugFormatString(self.jid_))
    if self.has_type_: res+=prefix+("type: %s\n" % self.DebugFormatString(self.type_))
    if self.has_show_: res+=prefix+("show: %s\n" % self.DebugFormatString(self.show_))
    if self.has_status_: res+=prefix+("status: %s\n" % self.DebugFormatString(self.status_))
    if self.has_from_jid_: res+=prefix+("from_jid: %s\n" % self.DebugFormatString(self.from_jid_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kjid = 1
  ktype = 2
  kshow = 3
  kstatus = 4
  kfrom_jid = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "jid",
    2: "type",
    3: "show",
    4: "status",
    5: "from_jid",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.XmppSendPresenceRequest'
class XmppSendPresenceResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.XmppSendPresenceResponse'
class XmppInviteRequest(ProtocolBuffer.ProtocolMessage):
  has_jid_ = 0
  jid_ = ""
  has_from_jid_ = 0
  from_jid_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def jid(self): return self.jid_

  def set_jid(self, x):
    self.has_jid_ = 1
    self.jid_ = x

  def clear_jid(self):
    if self.has_jid_:
      self.has_jid_ = 0
      self.jid_ = ""

  def has_jid(self): return self.has_jid_

  def from_jid(self): return self.from_jid_

  def set_from_jid(self, x):
    self.has_from_jid_ = 1
    self.from_jid_ = x

  def clear_from_jid(self):
    if self.has_from_jid_:
      self.has_from_jid_ = 0
      self.from_jid_ = ""

  def has_from_jid(self): return self.has_from_jid_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_jid()): self.set_jid(x.jid())
    if (x.has_from_jid()): self.set_from_jid(x.from_jid())

  def Equals(self, x):
    if x is self: return 1
    if self.has_jid_ != x.has_jid_: return 0
    if self.has_jid_ and self.jid_ != x.jid_: return 0
    if self.has_from_jid_ != x.has_from_jid_: return 0
    if self.has_from_jid_ and self.from_jid_ != x.from_jid_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_jid_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: jid not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.jid_))
    if (self.has_from_jid_): n += 1 + self.lengthString(len(self.from_jid_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_jid_):
      n += 1
      n += self.lengthString(len(self.jid_))
    if (self.has_from_jid_): n += 1 + self.lengthString(len(self.from_jid_))
    return n

  def Clear(self):
    self.clear_jid()
    self.clear_from_jid()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.jid_)
    if (self.has_from_jid_):
      out.putVarInt32(18)
      out.putPrefixedString(self.from_jid_)

  def OutputPartial(self, out):
    if (self.has_jid_):
      out.putVarInt32(10)
      out.putPrefixedString(self.jid_)
    if (self.has_from_jid_):
      out.putVarInt32(18)
      out.putPrefixedString(self.from_jid_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_jid(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_from_jid(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_jid_: res+=prefix+("jid: %s\n" % self.DebugFormatString(self.jid_))
    if self.has_from_jid_: res+=prefix+("from_jid: %s\n" % self.DebugFormatString(self.from_jid_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kjid = 1
  kfrom_jid = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "jid",
    2: "from_jid",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.XmppInviteRequest'
class XmppInviteResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.XmppInviteResponse'
if _extension_runtime:
  pass

__all__ = ['XmppServiceError','PresenceRequest','PresenceResponse','BulkPresenceRequest','BulkPresenceResponse','XmppMessageRequest','XmppMessageResponse','XmppSendPresenceRequest','XmppSendPresenceResponse','XmppInviteRequest','XmppInviteResponse']
