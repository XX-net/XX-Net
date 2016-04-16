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

from google.appengine.datastore.entity_pb import *
import google.appengine.datastore.entity_pb
class SchemaEntry(ProtocolBuffer.ProtocolMessage):


  STRING       =    1
  INT32        =    2
  BOOLEAN      =    3
  DOUBLE       =    4
  POINT        =    5
  USER         =    6
  REFERENCE    =    7

  _Type_NAMES = {
    1: "STRING",
    2: "INT32",
    3: "BOOLEAN",
    4: "DOUBLE",
    5: "POINT",
    6: "USER",
    7: "REFERENCE",
  }

  def Type_Name(cls, x): return cls._Type_NAMES.get(x, "")
  Type_Name = classmethod(Type_Name)

  has_name_ = 0
  name_ = ""
  has_type_ = 0
  type_ = 0
  has_meaning_ = 0
  meaning_ = 0
  has_meaning_set_ = 0
  meaning_set_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def name(self): return self.name_

  def set_name(self, x):
    self.has_name_ = 1
    self.name_ = x

  def clear_name(self):
    if self.has_name_:
      self.has_name_ = 0
      self.name_ = ""

  def has_name(self): return self.has_name_

  def type(self): return self.type_

  def set_type(self, x):
    self.has_type_ = 1
    self.type_ = x

  def clear_type(self):
    if self.has_type_:
      self.has_type_ = 0
      self.type_ = 0

  def has_type(self): return self.has_type_

  def meaning(self): return self.meaning_

  def set_meaning(self, x):
    self.has_meaning_ = 1
    self.meaning_ = x

  def clear_meaning(self):
    if self.has_meaning_:
      self.has_meaning_ = 0
      self.meaning_ = 0

  def has_meaning(self): return self.has_meaning_

  def meaning_set(self): return self.meaning_set_

  def set_meaning_set(self, x):
    self.has_meaning_set_ = 1
    self.meaning_set_ = x

  def clear_meaning_set(self):
    if self.has_meaning_set_:
      self.has_meaning_set_ = 0
      self.meaning_set_ = 0

  def has_meaning_set(self): return self.has_meaning_set_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())
    if (x.has_type()): self.set_type(x.type())
    if (x.has_meaning()): self.set_meaning(x.meaning())
    if (x.has_meaning_set()): self.set_meaning_set(x.meaning_set())

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if self.has_type_ != x.has_type_: return 0
    if self.has_type_ and self.type_ != x.type_: return 0
    if self.has_meaning_ != x.has_meaning_: return 0
    if self.has_meaning_ and self.meaning_ != x.meaning_: return 0
    if self.has_meaning_set_ != x.has_meaning_set_: return 0
    if self.has_meaning_set_ and self.meaning_set_ != x.meaning_set_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: name not set.')
    if (not self.has_type_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: type not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.name_))
    n += self.lengthVarInt64(self.type_)
    if (self.has_meaning_): n += 1 + self.lengthVarInt64(self.meaning_)
    if (self.has_meaning_set_): n += 3
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    if (self.has_type_):
      n += 1
      n += self.lengthVarInt64(self.type_)
    if (self.has_meaning_): n += 1 + self.lengthVarInt64(self.meaning_)
    if (self.has_meaning_set_): n += 3
    return n

  def Clear(self):
    self.clear_name()
    self.clear_type()
    self.clear_meaning()
    self.clear_meaning_set()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.name_)
    out.putVarInt32(16)
    out.putVarInt32(self.type_)
    if (self.has_meaning_):
      out.putVarInt32(24)
      out.putVarInt32(self.meaning_)
    if (self.has_meaning_set_):
      out.putVarInt32(824)
      out.putBoolean(self.meaning_set_)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    if (self.has_type_):
      out.putVarInt32(16)
      out.putVarInt32(self.type_)
    if (self.has_meaning_):
      out.putVarInt32(24)
      out.putVarInt32(self.meaning_)
    if (self.has_meaning_set_):
      out.putVarInt32(824)
      out.putBoolean(self.meaning_set_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_name(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_type(d.getVarInt32())
        continue
      if tt == 24:
        self.set_meaning(d.getVarInt32())
        continue
      if tt == 824:
        self.set_meaning_set(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    if self.has_type_: res+=prefix+("type: %s\n" % self.DebugFormatInt32(self.type_))
    if self.has_meaning_: res+=prefix+("meaning: %s\n" % self.DebugFormatInt32(self.meaning_))
    if self.has_meaning_set_: res+=prefix+("meaning_set: %s\n" % self.DebugFormatBool(self.meaning_set_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 1
  ktype = 2
  kmeaning = 3
  kmeaning_set = 103

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name",
    2: "type",
    3: "meaning",
    103: "meaning_set",
  }, 103)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
    103: ProtocolBuffer.Encoder.NUMERIC,
  }, 103, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.prospective_search.SchemaEntry'
class SubscribeRequest(ProtocolBuffer.ProtocolMessage):
  has_topic_ = 0
  topic_ = ""
  has_sub_id_ = 0
  sub_id_ = ""
  has_lease_duration_sec_ = 0
  lease_duration_sec_ = 0.0
  has_vanilla_query_ = 0
  vanilla_query_ = ""

  def __init__(self, contents=None):
    self.schema_entry_ = []
    if contents is not None: self.MergeFromString(contents)

  def topic(self): return self.topic_

  def set_topic(self, x):
    self.has_topic_ = 1
    self.topic_ = x

  def clear_topic(self):
    if self.has_topic_:
      self.has_topic_ = 0
      self.topic_ = ""

  def has_topic(self): return self.has_topic_

  def sub_id(self): return self.sub_id_

  def set_sub_id(self, x):
    self.has_sub_id_ = 1
    self.sub_id_ = x

  def clear_sub_id(self):
    if self.has_sub_id_:
      self.has_sub_id_ = 0
      self.sub_id_ = ""

  def has_sub_id(self): return self.has_sub_id_

  def lease_duration_sec(self): return self.lease_duration_sec_

  def set_lease_duration_sec(self, x):
    self.has_lease_duration_sec_ = 1
    self.lease_duration_sec_ = x

  def clear_lease_duration_sec(self):
    if self.has_lease_duration_sec_:
      self.has_lease_duration_sec_ = 0
      self.lease_duration_sec_ = 0.0

  def has_lease_duration_sec(self): return self.has_lease_duration_sec_

  def vanilla_query(self): return self.vanilla_query_

  def set_vanilla_query(self, x):
    self.has_vanilla_query_ = 1
    self.vanilla_query_ = x

  def clear_vanilla_query(self):
    if self.has_vanilla_query_:
      self.has_vanilla_query_ = 0
      self.vanilla_query_ = ""

  def has_vanilla_query(self): return self.has_vanilla_query_

  def schema_entry_size(self): return len(self.schema_entry_)
  def schema_entry_list(self): return self.schema_entry_

  def schema_entry(self, i):
    return self.schema_entry_[i]

  def mutable_schema_entry(self, i):
    return self.schema_entry_[i]

  def add_schema_entry(self):
    x = SchemaEntry()
    self.schema_entry_.append(x)
    return x

  def clear_schema_entry(self):
    self.schema_entry_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_topic()): self.set_topic(x.topic())
    if (x.has_sub_id()): self.set_sub_id(x.sub_id())
    if (x.has_lease_duration_sec()): self.set_lease_duration_sec(x.lease_duration_sec())
    if (x.has_vanilla_query()): self.set_vanilla_query(x.vanilla_query())
    for i in xrange(x.schema_entry_size()): self.add_schema_entry().CopyFrom(x.schema_entry(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_topic_ != x.has_topic_: return 0
    if self.has_topic_ and self.topic_ != x.topic_: return 0
    if self.has_sub_id_ != x.has_sub_id_: return 0
    if self.has_sub_id_ and self.sub_id_ != x.sub_id_: return 0
    if self.has_lease_duration_sec_ != x.has_lease_duration_sec_: return 0
    if self.has_lease_duration_sec_ and self.lease_duration_sec_ != x.lease_duration_sec_: return 0
    if self.has_vanilla_query_ != x.has_vanilla_query_: return 0
    if self.has_vanilla_query_ and self.vanilla_query_ != x.vanilla_query_: return 0
    if len(self.schema_entry_) != len(x.schema_entry_): return 0
    for e1, e2 in zip(self.schema_entry_, x.schema_entry_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_topic_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: topic not set.')
    if (not self.has_sub_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: sub_id not set.')
    if (not self.has_lease_duration_sec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: lease_duration_sec not set.')
    if (not self.has_vanilla_query_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: vanilla_query not set.')
    for p in self.schema_entry_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.topic_))
    n += self.lengthString(len(self.sub_id_))
    n += self.lengthString(len(self.vanilla_query_))
    n += 1 * len(self.schema_entry_)
    for i in xrange(len(self.schema_entry_)): n += self.lengthString(self.schema_entry_[i].ByteSize())
    return n + 12

  def ByteSizePartial(self):
    n = 0
    if (self.has_topic_):
      n += 1
      n += self.lengthString(len(self.topic_))
    if (self.has_sub_id_):
      n += 1
      n += self.lengthString(len(self.sub_id_))
    if (self.has_lease_duration_sec_):
      n += 9
    if (self.has_vanilla_query_):
      n += 1
      n += self.lengthString(len(self.vanilla_query_))
    n += 1 * len(self.schema_entry_)
    for i in xrange(len(self.schema_entry_)): n += self.lengthString(self.schema_entry_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_topic()
    self.clear_sub_id()
    self.clear_lease_duration_sec()
    self.clear_vanilla_query()
    self.clear_schema_entry()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.topic_)
    out.putVarInt32(18)
    out.putPrefixedString(self.sub_id_)
    out.putVarInt32(25)
    out.putDouble(self.lease_duration_sec_)
    out.putVarInt32(34)
    out.putPrefixedString(self.vanilla_query_)
    for i in xrange(len(self.schema_entry_)):
      out.putVarInt32(42)
      out.putVarInt32(self.schema_entry_[i].ByteSize())
      self.schema_entry_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_topic_):
      out.putVarInt32(10)
      out.putPrefixedString(self.topic_)
    if (self.has_sub_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.sub_id_)
    if (self.has_lease_duration_sec_):
      out.putVarInt32(25)
      out.putDouble(self.lease_duration_sec_)
    if (self.has_vanilla_query_):
      out.putVarInt32(34)
      out.putPrefixedString(self.vanilla_query_)
    for i in xrange(len(self.schema_entry_)):
      out.putVarInt32(42)
      out.putVarInt32(self.schema_entry_[i].ByteSizePartial())
      self.schema_entry_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_topic(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_sub_id(d.getPrefixedString())
        continue
      if tt == 25:
        self.set_lease_duration_sec(d.getDouble())
        continue
      if tt == 34:
        self.set_vanilla_query(d.getPrefixedString())
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_schema_entry().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_topic_: res+=prefix+("topic: %s\n" % self.DebugFormatString(self.topic_))
    if self.has_sub_id_: res+=prefix+("sub_id: %s\n" % self.DebugFormatString(self.sub_id_))
    if self.has_lease_duration_sec_: res+=prefix+("lease_duration_sec: %s\n" % self.DebugFormat(self.lease_duration_sec_))
    if self.has_vanilla_query_: res+=prefix+("vanilla_query: %s\n" % self.DebugFormatString(self.vanilla_query_))
    cnt=0
    for e in self.schema_entry_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("schema_entry%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktopic = 1
  ksub_id = 2
  klease_duration_sec = 3
  kvanilla_query = 4
  kschema_entry = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "topic",
    2: "sub_id",
    3: "lease_duration_sec",
    4: "vanilla_query",
    5: "schema_entry",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.DOUBLE,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.prospective_search.SubscribeRequest'
class SubscribeResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.prospective_search.SubscribeResponse'
class UnsubscribeRequest(ProtocolBuffer.ProtocolMessage):
  has_topic_ = 0
  topic_ = ""
  has_sub_id_ = 0
  sub_id_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def topic(self): return self.topic_

  def set_topic(self, x):
    self.has_topic_ = 1
    self.topic_ = x

  def clear_topic(self):
    if self.has_topic_:
      self.has_topic_ = 0
      self.topic_ = ""

  def has_topic(self): return self.has_topic_

  def sub_id(self): return self.sub_id_

  def set_sub_id(self, x):
    self.has_sub_id_ = 1
    self.sub_id_ = x

  def clear_sub_id(self):
    if self.has_sub_id_:
      self.has_sub_id_ = 0
      self.sub_id_ = ""

  def has_sub_id(self): return self.has_sub_id_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_topic()): self.set_topic(x.topic())
    if (x.has_sub_id()): self.set_sub_id(x.sub_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_topic_ != x.has_topic_: return 0
    if self.has_topic_ and self.topic_ != x.topic_: return 0
    if self.has_sub_id_ != x.has_sub_id_: return 0
    if self.has_sub_id_ and self.sub_id_ != x.sub_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_topic_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: topic not set.')
    if (not self.has_sub_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: sub_id not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.topic_))
    n += self.lengthString(len(self.sub_id_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_topic_):
      n += 1
      n += self.lengthString(len(self.topic_))
    if (self.has_sub_id_):
      n += 1
      n += self.lengthString(len(self.sub_id_))
    return n

  def Clear(self):
    self.clear_topic()
    self.clear_sub_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.topic_)
    out.putVarInt32(18)
    out.putPrefixedString(self.sub_id_)

  def OutputPartial(self, out):
    if (self.has_topic_):
      out.putVarInt32(10)
      out.putPrefixedString(self.topic_)
    if (self.has_sub_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.sub_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_topic(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_sub_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_topic_: res+=prefix+("topic: %s\n" % self.DebugFormatString(self.topic_))
    if self.has_sub_id_: res+=prefix+("sub_id: %s\n" % self.DebugFormatString(self.sub_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktopic = 1
  ksub_id = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "topic",
    2: "sub_id",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.prospective_search.UnsubscribeRequest'
class UnsubscribeResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.prospective_search.UnsubscribeResponse'
class SubscriptionRecord(ProtocolBuffer.ProtocolMessage):


  OK           =    0
  PENDING      =    1
  ERROR        =    2

  _State_NAMES = {
    0: "OK",
    1: "PENDING",
    2: "ERROR",
  }

  def State_Name(cls, x): return cls._State_NAMES.get(x, "")
  State_Name = classmethod(State_Name)

  has_id_ = 0
  id_ = ""
  has_vanilla_query_ = 0
  vanilla_query_ = ""
  has_expiration_time_sec_ = 0
  expiration_time_sec_ = 0.0
  has_state_ = 0
  state_ = 0
  has_error_message_ = 0
  error_message_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def id(self): return self.id_

  def set_id(self, x):
    self.has_id_ = 1
    self.id_ = x

  def clear_id(self):
    if self.has_id_:
      self.has_id_ = 0
      self.id_ = ""

  def has_id(self): return self.has_id_

  def vanilla_query(self): return self.vanilla_query_

  def set_vanilla_query(self, x):
    self.has_vanilla_query_ = 1
    self.vanilla_query_ = x

  def clear_vanilla_query(self):
    if self.has_vanilla_query_:
      self.has_vanilla_query_ = 0
      self.vanilla_query_ = ""

  def has_vanilla_query(self): return self.has_vanilla_query_

  def expiration_time_sec(self): return self.expiration_time_sec_

  def set_expiration_time_sec(self, x):
    self.has_expiration_time_sec_ = 1
    self.expiration_time_sec_ = x

  def clear_expiration_time_sec(self):
    if self.has_expiration_time_sec_:
      self.has_expiration_time_sec_ = 0
      self.expiration_time_sec_ = 0.0

  def has_expiration_time_sec(self): return self.has_expiration_time_sec_

  def state(self): return self.state_

  def set_state(self, x):
    self.has_state_ = 1
    self.state_ = x

  def clear_state(self):
    if self.has_state_:
      self.has_state_ = 0
      self.state_ = 0

  def has_state(self): return self.has_state_

  def error_message(self): return self.error_message_

  def set_error_message(self, x):
    self.has_error_message_ = 1
    self.error_message_ = x

  def clear_error_message(self):
    if self.has_error_message_:
      self.has_error_message_ = 0
      self.error_message_ = ""

  def has_error_message(self): return self.has_error_message_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_id()): self.set_id(x.id())
    if (x.has_vanilla_query()): self.set_vanilla_query(x.vanilla_query())
    if (x.has_expiration_time_sec()): self.set_expiration_time_sec(x.expiration_time_sec())
    if (x.has_state()): self.set_state(x.state())
    if (x.has_error_message()): self.set_error_message(x.error_message())

  def Equals(self, x):
    if x is self: return 1
    if self.has_id_ != x.has_id_: return 0
    if self.has_id_ and self.id_ != x.id_: return 0
    if self.has_vanilla_query_ != x.has_vanilla_query_: return 0
    if self.has_vanilla_query_ and self.vanilla_query_ != x.vanilla_query_: return 0
    if self.has_expiration_time_sec_ != x.has_expiration_time_sec_: return 0
    if self.has_expiration_time_sec_ and self.expiration_time_sec_ != x.expiration_time_sec_: return 0
    if self.has_state_ != x.has_state_: return 0
    if self.has_state_ and self.state_ != x.state_: return 0
    if self.has_error_message_ != x.has_error_message_: return 0
    if self.has_error_message_ and self.error_message_ != x.error_message_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: id not set.')
    if (not self.has_vanilla_query_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: vanilla_query not set.')
    if (not self.has_expiration_time_sec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: expiration_time_sec not set.')
    if (not self.has_state_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: state not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.id_))
    n += self.lengthString(len(self.vanilla_query_))
    n += self.lengthVarInt64(self.state_)
    if (self.has_error_message_): n += 1 + self.lengthString(len(self.error_message_))
    return n + 12

  def ByteSizePartial(self):
    n = 0
    if (self.has_id_):
      n += 1
      n += self.lengthString(len(self.id_))
    if (self.has_vanilla_query_):
      n += 1
      n += self.lengthString(len(self.vanilla_query_))
    if (self.has_expiration_time_sec_):
      n += 9
    if (self.has_state_):
      n += 1
      n += self.lengthVarInt64(self.state_)
    if (self.has_error_message_): n += 1 + self.lengthString(len(self.error_message_))
    return n

  def Clear(self):
    self.clear_id()
    self.clear_vanilla_query()
    self.clear_expiration_time_sec()
    self.clear_state()
    self.clear_error_message()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.id_)
    out.putVarInt32(18)
    out.putPrefixedString(self.vanilla_query_)
    out.putVarInt32(25)
    out.putDouble(self.expiration_time_sec_)
    out.putVarInt32(32)
    out.putVarInt32(self.state_)
    if (self.has_error_message_):
      out.putVarInt32(42)
      out.putPrefixedString(self.error_message_)

  def OutputPartial(self, out):
    if (self.has_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.id_)
    if (self.has_vanilla_query_):
      out.putVarInt32(18)
      out.putPrefixedString(self.vanilla_query_)
    if (self.has_expiration_time_sec_):
      out.putVarInt32(25)
      out.putDouble(self.expiration_time_sec_)
    if (self.has_state_):
      out.putVarInt32(32)
      out.putVarInt32(self.state_)
    if (self.has_error_message_):
      out.putVarInt32(42)
      out.putPrefixedString(self.error_message_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_vanilla_query(d.getPrefixedString())
        continue
      if tt == 25:
        self.set_expiration_time_sec(d.getDouble())
        continue
      if tt == 32:
        self.set_state(d.getVarInt32())
        continue
      if tt == 42:
        self.set_error_message(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_id_: res+=prefix+("id: %s\n" % self.DebugFormatString(self.id_))
    if self.has_vanilla_query_: res+=prefix+("vanilla_query: %s\n" % self.DebugFormatString(self.vanilla_query_))
    if self.has_expiration_time_sec_: res+=prefix+("expiration_time_sec: %s\n" % self.DebugFormat(self.expiration_time_sec_))
    if self.has_state_: res+=prefix+("state: %s\n" % self.DebugFormatInt32(self.state_))
    if self.has_error_message_: res+=prefix+("error_message: %s\n" % self.DebugFormatString(self.error_message_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kid = 1
  kvanilla_query = 2
  kexpiration_time_sec = 3
  kstate = 4
  kerror_message = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "id",
    2: "vanilla_query",
    3: "expiration_time_sec",
    4: "state",
    5: "error_message",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.DOUBLE,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.prospective_search.SubscriptionRecord'
class ListSubscriptionsRequest(ProtocolBuffer.ProtocolMessage):
  has_topic_ = 0
  topic_ = ""
  has_max_results_ = 0
  max_results_ = 1000
  has_max_results_set_ = 0
  max_results_set_ = 0
  has_expires_before_ = 0
  expires_before_ = 0
  has_subscription_id_start_ = 0
  subscription_id_start_ = ""
  has_app_id_ = 0
  app_id_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def topic(self): return self.topic_

  def set_topic(self, x):
    self.has_topic_ = 1
    self.topic_ = x

  def clear_topic(self):
    if self.has_topic_:
      self.has_topic_ = 0
      self.topic_ = ""

  def has_topic(self): return self.has_topic_

  def max_results(self): return self.max_results_

  def set_max_results(self, x):
    self.has_max_results_ = 1
    self.max_results_ = x

  def clear_max_results(self):
    if self.has_max_results_:
      self.has_max_results_ = 0
      self.max_results_ = 1000

  def has_max_results(self): return self.has_max_results_

  def max_results_set(self): return self.max_results_set_

  def set_max_results_set(self, x):
    self.has_max_results_set_ = 1
    self.max_results_set_ = x

  def clear_max_results_set(self):
    if self.has_max_results_set_:
      self.has_max_results_set_ = 0
      self.max_results_set_ = 0

  def has_max_results_set(self): return self.has_max_results_set_

  def expires_before(self): return self.expires_before_

  def set_expires_before(self, x):
    self.has_expires_before_ = 1
    self.expires_before_ = x

  def clear_expires_before(self):
    if self.has_expires_before_:
      self.has_expires_before_ = 0
      self.expires_before_ = 0

  def has_expires_before(self): return self.has_expires_before_

  def subscription_id_start(self): return self.subscription_id_start_

  def set_subscription_id_start(self, x):
    self.has_subscription_id_start_ = 1
    self.subscription_id_start_ = x

  def clear_subscription_id_start(self):
    if self.has_subscription_id_start_:
      self.has_subscription_id_start_ = 0
      self.subscription_id_start_ = ""

  def has_subscription_id_start(self): return self.has_subscription_id_start_

  def app_id(self): return self.app_id_

  def set_app_id(self, x):
    self.has_app_id_ = 1
    self.app_id_ = x

  def clear_app_id(self):
    if self.has_app_id_:
      self.has_app_id_ = 0
      self.app_id_ = ""

  def has_app_id(self): return self.has_app_id_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_topic()): self.set_topic(x.topic())
    if (x.has_max_results()): self.set_max_results(x.max_results())
    if (x.has_max_results_set()): self.set_max_results_set(x.max_results_set())
    if (x.has_expires_before()): self.set_expires_before(x.expires_before())
    if (x.has_subscription_id_start()): self.set_subscription_id_start(x.subscription_id_start())
    if (x.has_app_id()): self.set_app_id(x.app_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_topic_ != x.has_topic_: return 0
    if self.has_topic_ and self.topic_ != x.topic_: return 0
    if self.has_max_results_ != x.has_max_results_: return 0
    if self.has_max_results_ and self.max_results_ != x.max_results_: return 0
    if self.has_max_results_set_ != x.has_max_results_set_: return 0
    if self.has_max_results_set_ and self.max_results_set_ != x.max_results_set_: return 0
    if self.has_expires_before_ != x.has_expires_before_: return 0
    if self.has_expires_before_ and self.expires_before_ != x.expires_before_: return 0
    if self.has_subscription_id_start_ != x.has_subscription_id_start_: return 0
    if self.has_subscription_id_start_ and self.subscription_id_start_ != x.subscription_id_start_: return 0
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_topic_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: topic not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.topic_))
    if (self.has_max_results_): n += 1 + self.lengthVarInt64(self.max_results_)
    if (self.has_max_results_set_): n += 3
    if (self.has_expires_before_): n += 1 + self.lengthVarInt64(self.expires_before_)
    if (self.has_subscription_id_start_): n += 1 + self.lengthString(len(self.subscription_id_start_))
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_topic_):
      n += 1
      n += self.lengthString(len(self.topic_))
    if (self.has_max_results_): n += 1 + self.lengthVarInt64(self.max_results_)
    if (self.has_max_results_set_): n += 3
    if (self.has_expires_before_): n += 1 + self.lengthVarInt64(self.expires_before_)
    if (self.has_subscription_id_start_): n += 1 + self.lengthString(len(self.subscription_id_start_))
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n

  def Clear(self):
    self.clear_topic()
    self.clear_max_results()
    self.clear_max_results_set()
    self.clear_expires_before()
    self.clear_subscription_id_start()
    self.clear_app_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.topic_)
    if (self.has_max_results_):
      out.putVarInt32(16)
      out.putVarInt64(self.max_results_)
    if (self.has_expires_before_):
      out.putVarInt32(24)
      out.putVarInt64(self.expires_before_)
    if (self.has_subscription_id_start_):
      out.putVarInt32(34)
      out.putPrefixedString(self.subscription_id_start_)
    if (self.has_app_id_):
      out.putVarInt32(42)
      out.putPrefixedString(self.app_id_)
    if (self.has_max_results_set_):
      out.putVarInt32(816)
      out.putBoolean(self.max_results_set_)

  def OutputPartial(self, out):
    if (self.has_topic_):
      out.putVarInt32(10)
      out.putPrefixedString(self.topic_)
    if (self.has_max_results_):
      out.putVarInt32(16)
      out.putVarInt64(self.max_results_)
    if (self.has_expires_before_):
      out.putVarInt32(24)
      out.putVarInt64(self.expires_before_)
    if (self.has_subscription_id_start_):
      out.putVarInt32(34)
      out.putPrefixedString(self.subscription_id_start_)
    if (self.has_app_id_):
      out.putVarInt32(42)
      out.putPrefixedString(self.app_id_)
    if (self.has_max_results_set_):
      out.putVarInt32(816)
      out.putBoolean(self.max_results_set_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_topic(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_max_results(d.getVarInt64())
        continue
      if tt == 24:
        self.set_expires_before(d.getVarInt64())
        continue
      if tt == 34:
        self.set_subscription_id_start(d.getPrefixedString())
        continue
      if tt == 42:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 816:
        self.set_max_results_set(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_topic_: res+=prefix+("topic: %s\n" % self.DebugFormatString(self.topic_))
    if self.has_max_results_: res+=prefix+("max_results: %s\n" % self.DebugFormatInt64(self.max_results_))
    if self.has_max_results_set_: res+=prefix+("max_results_set: %s\n" % self.DebugFormatBool(self.max_results_set_))
    if self.has_expires_before_: res+=prefix+("expires_before: %s\n" % self.DebugFormatInt64(self.expires_before_))
    if self.has_subscription_id_start_: res+=prefix+("subscription_id_start: %s\n" % self.DebugFormatString(self.subscription_id_start_))
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktopic = 1
  kmax_results = 2
  kmax_results_set = 102
  kexpires_before = 3
  ksubscription_id_start = 4
  kapp_id = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "topic",
    2: "max_results",
    3: "expires_before",
    4: "subscription_id_start",
    5: "app_id",
    102: "max_results_set",
  }, 102)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
    102: ProtocolBuffer.Encoder.NUMERIC,
  }, 102, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.prospective_search.ListSubscriptionsRequest'
class ListSubscriptionsResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.subscription_ = []
    if contents is not None: self.MergeFromString(contents)

  def subscription_size(self): return len(self.subscription_)
  def subscription_list(self): return self.subscription_

  def subscription(self, i):
    return self.subscription_[i]

  def mutable_subscription(self, i):
    return self.subscription_[i]

  def add_subscription(self):
    x = SubscriptionRecord()
    self.subscription_.append(x)
    return x

  def clear_subscription(self):
    self.subscription_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.subscription_size()): self.add_subscription().CopyFrom(x.subscription(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.subscription_) != len(x.subscription_): return 0
    for e1, e2 in zip(self.subscription_, x.subscription_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.subscription_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.subscription_)
    for i in xrange(len(self.subscription_)): n += self.lengthString(self.subscription_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.subscription_)
    for i in xrange(len(self.subscription_)): n += self.lengthString(self.subscription_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_subscription()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.subscription_)):
      out.putVarInt32(10)
      out.putVarInt32(self.subscription_[i].ByteSize())
      self.subscription_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.subscription_)):
      out.putVarInt32(10)
      out.putVarInt32(self.subscription_[i].ByteSizePartial())
      self.subscription_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_subscription().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.subscription_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("subscription%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksubscription = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "subscription",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.prospective_search.ListSubscriptionsResponse'
class ListTopicsRequest(ProtocolBuffer.ProtocolMessage):
  has_topic_start_ = 0
  topic_start_ = ""
  has_max_results_ = 0
  max_results_ = 1000
  has_max_results_set_ = 0
  max_results_set_ = 0
  has_app_id_ = 0
  app_id_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def topic_start(self): return self.topic_start_

  def set_topic_start(self, x):
    self.has_topic_start_ = 1
    self.topic_start_ = x

  def clear_topic_start(self):
    if self.has_topic_start_:
      self.has_topic_start_ = 0
      self.topic_start_ = ""

  def has_topic_start(self): return self.has_topic_start_

  def max_results(self): return self.max_results_

  def set_max_results(self, x):
    self.has_max_results_ = 1
    self.max_results_ = x

  def clear_max_results(self):
    if self.has_max_results_:
      self.has_max_results_ = 0
      self.max_results_ = 1000

  def has_max_results(self): return self.has_max_results_

  def max_results_set(self): return self.max_results_set_

  def set_max_results_set(self, x):
    self.has_max_results_set_ = 1
    self.max_results_set_ = x

  def clear_max_results_set(self):
    if self.has_max_results_set_:
      self.has_max_results_set_ = 0
      self.max_results_set_ = 0

  def has_max_results_set(self): return self.has_max_results_set_

  def app_id(self): return self.app_id_

  def set_app_id(self, x):
    self.has_app_id_ = 1
    self.app_id_ = x

  def clear_app_id(self):
    if self.has_app_id_:
      self.has_app_id_ = 0
      self.app_id_ = ""

  def has_app_id(self): return self.has_app_id_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_topic_start()): self.set_topic_start(x.topic_start())
    if (x.has_max_results()): self.set_max_results(x.max_results())
    if (x.has_max_results_set()): self.set_max_results_set(x.max_results_set())
    if (x.has_app_id()): self.set_app_id(x.app_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_topic_start_ != x.has_topic_start_: return 0
    if self.has_topic_start_ and self.topic_start_ != x.topic_start_: return 0
    if self.has_max_results_ != x.has_max_results_: return 0
    if self.has_max_results_ and self.max_results_ != x.max_results_: return 0
    if self.has_max_results_set_ != x.has_max_results_set_: return 0
    if self.has_max_results_set_ and self.max_results_set_ != x.max_results_set_: return 0
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_topic_start_): n += 1 + self.lengthString(len(self.topic_start_))
    if (self.has_max_results_): n += 1 + self.lengthVarInt64(self.max_results_)
    if (self.has_max_results_set_): n += 3
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_topic_start_): n += 1 + self.lengthString(len(self.topic_start_))
    if (self.has_max_results_): n += 1 + self.lengthVarInt64(self.max_results_)
    if (self.has_max_results_set_): n += 3
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n

  def Clear(self):
    self.clear_topic_start()
    self.clear_max_results()
    self.clear_max_results_set()
    self.clear_app_id()

  def OutputUnchecked(self, out):
    if (self.has_topic_start_):
      out.putVarInt32(10)
      out.putPrefixedString(self.topic_start_)
    if (self.has_max_results_):
      out.putVarInt32(16)
      out.putVarInt64(self.max_results_)
    if (self.has_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.app_id_)
    if (self.has_max_results_set_):
      out.putVarInt32(816)
      out.putBoolean(self.max_results_set_)

  def OutputPartial(self, out):
    if (self.has_topic_start_):
      out.putVarInt32(10)
      out.putPrefixedString(self.topic_start_)
    if (self.has_max_results_):
      out.putVarInt32(16)
      out.putVarInt64(self.max_results_)
    if (self.has_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.app_id_)
    if (self.has_max_results_set_):
      out.putVarInt32(816)
      out.putBoolean(self.max_results_set_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_topic_start(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_max_results(d.getVarInt64())
        continue
      if tt == 26:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 816:
        self.set_max_results_set(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_topic_start_: res+=prefix+("topic_start: %s\n" % self.DebugFormatString(self.topic_start_))
    if self.has_max_results_: res+=prefix+("max_results: %s\n" % self.DebugFormatInt64(self.max_results_))
    if self.has_max_results_set_: res+=prefix+("max_results_set: %s\n" % self.DebugFormatBool(self.max_results_set_))
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktopic_start = 1
  kmax_results = 2
  kmax_results_set = 102
  kapp_id = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "topic_start",
    2: "max_results",
    3: "app_id",
    102: "max_results_set",
  }, 102)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
    102: ProtocolBuffer.Encoder.NUMERIC,
  }, 102, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.prospective_search.ListTopicsRequest'
class ListTopicsResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.topic_ = []
    if contents is not None: self.MergeFromString(contents)

  def topic_size(self): return len(self.topic_)
  def topic_list(self): return self.topic_

  def topic(self, i):
    return self.topic_[i]

  def set_topic(self, i, x):
    self.topic_[i] = x

  def add_topic(self, x):
    self.topic_.append(x)

  def clear_topic(self):
    self.topic_ = []


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.topic_size()): self.add_topic(x.topic(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.topic_) != len(x.topic_): return 0
    for e1, e2 in zip(self.topic_, x.topic_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.topic_)
    for i in xrange(len(self.topic_)): n += self.lengthString(len(self.topic_[i]))
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.topic_)
    for i in xrange(len(self.topic_)): n += self.lengthString(len(self.topic_[i]))
    return n

  def Clear(self):
    self.clear_topic()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.topic_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.topic_[i])

  def OutputPartial(self, out):
    for i in xrange(len(self.topic_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.topic_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.add_topic(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.topic_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("topic%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktopic = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "topic",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.prospective_search.ListTopicsResponse'
class MatchRequest(ProtocolBuffer.ProtocolMessage):


  ENTITY       =    1
  MODEL        =    2

  _PythonDocumentClass_NAMES = {
    1: "ENTITY",
    2: "MODEL",
  }

  def PythonDocumentClass_Name(cls, x): return cls._PythonDocumentClass_NAMES.get(x, "")
  PythonDocumentClass_Name = classmethod(PythonDocumentClass_Name)

  has_topic_ = 0
  topic_ = ""
  has_document_ = 0
  has_result_batch_size_ = 0
  result_batch_size_ = 0
  has_result_task_queue_ = 0
  result_task_queue_ = ""
  has_result_relative_url_ = 0
  result_relative_url_ = ""
  has_result_key_ = 0
  result_key_ = ""
  has_result_python_document_class_ = 0
  result_python_document_class_ = 0

  def __init__(self, contents=None):
    self.document_ = EntityProto()
    if contents is not None: self.MergeFromString(contents)

  def topic(self): return self.topic_

  def set_topic(self, x):
    self.has_topic_ = 1
    self.topic_ = x

  def clear_topic(self):
    if self.has_topic_:
      self.has_topic_ = 0
      self.topic_ = ""

  def has_topic(self): return self.has_topic_

  def document(self): return self.document_

  def mutable_document(self): self.has_document_ = 1; return self.document_

  def clear_document(self):self.has_document_ = 0; self.document_.Clear()

  def has_document(self): return self.has_document_

  def result_batch_size(self): return self.result_batch_size_

  def set_result_batch_size(self, x):
    self.has_result_batch_size_ = 1
    self.result_batch_size_ = x

  def clear_result_batch_size(self):
    if self.has_result_batch_size_:
      self.has_result_batch_size_ = 0
      self.result_batch_size_ = 0

  def has_result_batch_size(self): return self.has_result_batch_size_

  def result_task_queue(self): return self.result_task_queue_

  def set_result_task_queue(self, x):
    self.has_result_task_queue_ = 1
    self.result_task_queue_ = x

  def clear_result_task_queue(self):
    if self.has_result_task_queue_:
      self.has_result_task_queue_ = 0
      self.result_task_queue_ = ""

  def has_result_task_queue(self): return self.has_result_task_queue_

  def result_relative_url(self): return self.result_relative_url_

  def set_result_relative_url(self, x):
    self.has_result_relative_url_ = 1
    self.result_relative_url_ = x

  def clear_result_relative_url(self):
    if self.has_result_relative_url_:
      self.has_result_relative_url_ = 0
      self.result_relative_url_ = ""

  def has_result_relative_url(self): return self.has_result_relative_url_

  def result_key(self): return self.result_key_

  def set_result_key(self, x):
    self.has_result_key_ = 1
    self.result_key_ = x

  def clear_result_key(self):
    if self.has_result_key_:
      self.has_result_key_ = 0
      self.result_key_ = ""

  def has_result_key(self): return self.has_result_key_

  def result_python_document_class(self): return self.result_python_document_class_

  def set_result_python_document_class(self, x):
    self.has_result_python_document_class_ = 1
    self.result_python_document_class_ = x

  def clear_result_python_document_class(self):
    if self.has_result_python_document_class_:
      self.has_result_python_document_class_ = 0
      self.result_python_document_class_ = 0

  def has_result_python_document_class(self): return self.has_result_python_document_class_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_topic()): self.set_topic(x.topic())
    if (x.has_document()): self.mutable_document().MergeFrom(x.document())
    if (x.has_result_batch_size()): self.set_result_batch_size(x.result_batch_size())
    if (x.has_result_task_queue()): self.set_result_task_queue(x.result_task_queue())
    if (x.has_result_relative_url()): self.set_result_relative_url(x.result_relative_url())
    if (x.has_result_key()): self.set_result_key(x.result_key())
    if (x.has_result_python_document_class()): self.set_result_python_document_class(x.result_python_document_class())

  def Equals(self, x):
    if x is self: return 1
    if self.has_topic_ != x.has_topic_: return 0
    if self.has_topic_ and self.topic_ != x.topic_: return 0
    if self.has_document_ != x.has_document_: return 0
    if self.has_document_ and self.document_ != x.document_: return 0
    if self.has_result_batch_size_ != x.has_result_batch_size_: return 0
    if self.has_result_batch_size_ and self.result_batch_size_ != x.result_batch_size_: return 0
    if self.has_result_task_queue_ != x.has_result_task_queue_: return 0
    if self.has_result_task_queue_ and self.result_task_queue_ != x.result_task_queue_: return 0
    if self.has_result_relative_url_ != x.has_result_relative_url_: return 0
    if self.has_result_relative_url_ and self.result_relative_url_ != x.result_relative_url_: return 0
    if self.has_result_key_ != x.has_result_key_: return 0
    if self.has_result_key_ and self.result_key_ != x.result_key_: return 0
    if self.has_result_python_document_class_ != x.has_result_python_document_class_: return 0
    if self.has_result_python_document_class_ and self.result_python_document_class_ != x.result_python_document_class_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_topic_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: topic not set.')
    if (not self.has_document_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: document not set.')
    elif not self.document_.IsInitialized(debug_strs): initialized = 0
    if (not self.has_result_batch_size_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: result_batch_size not set.')
    if (not self.has_result_task_queue_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: result_task_queue not set.')
    if (not self.has_result_relative_url_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: result_relative_url not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.topic_))
    n += self.lengthString(self.document_.ByteSize())
    n += self.lengthVarInt64(self.result_batch_size_)
    n += self.lengthString(len(self.result_task_queue_))
    n += self.lengthString(len(self.result_relative_url_))
    if (self.has_result_key_): n += 1 + self.lengthString(len(self.result_key_))
    if (self.has_result_python_document_class_): n += 1 + self.lengthVarInt64(self.result_python_document_class_)
    return n + 5

  def ByteSizePartial(self):
    n = 0
    if (self.has_topic_):
      n += 1
      n += self.lengthString(len(self.topic_))
    if (self.has_document_):
      n += 1
      n += self.lengthString(self.document_.ByteSizePartial())
    if (self.has_result_batch_size_):
      n += 1
      n += self.lengthVarInt64(self.result_batch_size_)
    if (self.has_result_task_queue_):
      n += 1
      n += self.lengthString(len(self.result_task_queue_))
    if (self.has_result_relative_url_):
      n += 1
      n += self.lengthString(len(self.result_relative_url_))
    if (self.has_result_key_): n += 1 + self.lengthString(len(self.result_key_))
    if (self.has_result_python_document_class_): n += 1 + self.lengthVarInt64(self.result_python_document_class_)
    return n

  def Clear(self):
    self.clear_topic()
    self.clear_document()
    self.clear_result_batch_size()
    self.clear_result_task_queue()
    self.clear_result_relative_url()
    self.clear_result_key()
    self.clear_result_python_document_class()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.topic_)
    out.putVarInt32(18)
    out.putVarInt32(self.document_.ByteSize())
    self.document_.OutputUnchecked(out)
    out.putVarInt32(24)
    out.putVarInt32(self.result_batch_size_)
    out.putVarInt32(34)
    out.putPrefixedString(self.result_task_queue_)
    out.putVarInt32(42)
    out.putPrefixedString(self.result_relative_url_)
    if (self.has_result_key_):
      out.putVarInt32(50)
      out.putPrefixedString(self.result_key_)
    if (self.has_result_python_document_class_):
      out.putVarInt32(56)
      out.putVarInt32(self.result_python_document_class_)

  def OutputPartial(self, out):
    if (self.has_topic_):
      out.putVarInt32(10)
      out.putPrefixedString(self.topic_)
    if (self.has_document_):
      out.putVarInt32(18)
      out.putVarInt32(self.document_.ByteSizePartial())
      self.document_.OutputPartial(out)
    if (self.has_result_batch_size_):
      out.putVarInt32(24)
      out.putVarInt32(self.result_batch_size_)
    if (self.has_result_task_queue_):
      out.putVarInt32(34)
      out.putPrefixedString(self.result_task_queue_)
    if (self.has_result_relative_url_):
      out.putVarInt32(42)
      out.putPrefixedString(self.result_relative_url_)
    if (self.has_result_key_):
      out.putVarInt32(50)
      out.putPrefixedString(self.result_key_)
    if (self.has_result_python_document_class_):
      out.putVarInt32(56)
      out.putVarInt32(self.result_python_document_class_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_topic(d.getPrefixedString())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_document().TryMerge(tmp)
        continue
      if tt == 24:
        self.set_result_batch_size(d.getVarInt32())
        continue
      if tt == 34:
        self.set_result_task_queue(d.getPrefixedString())
        continue
      if tt == 42:
        self.set_result_relative_url(d.getPrefixedString())
        continue
      if tt == 50:
        self.set_result_key(d.getPrefixedString())
        continue
      if tt == 56:
        self.set_result_python_document_class(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_topic_: res+=prefix+("topic: %s\n" % self.DebugFormatString(self.topic_))
    if self.has_document_:
      res+=prefix+"document <\n"
      res+=self.document_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_result_batch_size_: res+=prefix+("result_batch_size: %s\n" % self.DebugFormatInt32(self.result_batch_size_))
    if self.has_result_task_queue_: res+=prefix+("result_task_queue: %s\n" % self.DebugFormatString(self.result_task_queue_))
    if self.has_result_relative_url_: res+=prefix+("result_relative_url: %s\n" % self.DebugFormatString(self.result_relative_url_))
    if self.has_result_key_: res+=prefix+("result_key: %s\n" % self.DebugFormatString(self.result_key_))
    if self.has_result_python_document_class_: res+=prefix+("result_python_document_class: %s\n" % self.DebugFormatInt32(self.result_python_document_class_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktopic = 1
  kdocument = 2
  kresult_batch_size = 3
  kresult_task_queue = 4
  kresult_relative_url = 5
  kresult_key = 6
  kresult_python_document_class = 7

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "topic",
    2: "document",
    3: "result_batch_size",
    4: "result_task_queue",
    5: "result_relative_url",
    6: "result_key",
    7: "result_python_document_class",
  }, 7)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.STRING,
    7: ProtocolBuffer.Encoder.NUMERIC,
  }, 7, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.prospective_search.MatchRequest'
class MatchResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.prospective_search.MatchResponse'
if _extension_runtime:
  pass

__all__ = ['SchemaEntry','SubscribeRequest','SubscribeResponse','UnsubscribeRequest','UnsubscribeResponse','SubscriptionRecord','ListSubscriptionsRequest','ListSubscriptionsResponse','ListTopicsRequest','ListTopicsResponse','MatchRequest','MatchResponse']
