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

class FieldValue_Geo(ProtocolBuffer.ProtocolMessage):
  has_lat_ = 0
  lat_ = 0.0
  has_lng_ = 0
  lng_ = 0.0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def lat(self): return self.lat_

  def set_lat(self, x):
    self.has_lat_ = 1
    self.lat_ = x

  def clear_lat(self):
    if self.has_lat_:
      self.has_lat_ = 0
      self.lat_ = 0.0

  def has_lat(self): return self.has_lat_

  def lng(self): return self.lng_

  def set_lng(self, x):
    self.has_lng_ = 1
    self.lng_ = x

  def clear_lng(self):
    if self.has_lng_:
      self.has_lng_ = 0
      self.lng_ = 0.0

  def has_lng(self): return self.has_lng_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_lat()): self.set_lat(x.lat())
    if (x.has_lng()): self.set_lng(x.lng())

  def Equals(self, x):
    if x is self: return 1
    if self.has_lat_ != x.has_lat_: return 0
    if self.has_lat_ and self.lat_ != x.lat_: return 0
    if self.has_lng_ != x.has_lng_: return 0
    if self.has_lng_ and self.lng_ != x.lng_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_lat_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: lat not set.')
    if (not self.has_lng_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: lng not set.')
    return initialized

  def ByteSize(self):
    n = 0
    return n + 18

  def ByteSizePartial(self):
    n = 0
    if (self.has_lat_):
      n += 9
    if (self.has_lng_):
      n += 9
    return n

  def Clear(self):
    self.clear_lat()
    self.clear_lng()

  def OutputUnchecked(self, out):
    out.putVarInt32(41)
    out.putDouble(self.lat_)
    out.putVarInt32(49)
    out.putDouble(self.lng_)

  def OutputPartial(self, out):
    if (self.has_lat_):
      out.putVarInt32(41)
      out.putDouble(self.lat_)
    if (self.has_lng_):
      out.putVarInt32(49)
      out.putDouble(self.lng_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 36: break
      if tt == 41:
        self.set_lat(d.getDouble())
        continue
      if tt == 49:
        self.set_lng(d.getDouble())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_lat_: res+=prefix+("lat: %s\n" % self.DebugFormat(self.lat_))
    if self.has_lng_: res+=prefix+("lng: %s\n" % self.DebugFormat(self.lng_))
    return res

class FieldValue(ProtocolBuffer.ProtocolMessage):


  TEXT         =    0
  HTML         =    1
  ATOM         =    2
  DATE         =    3
  NUMBER       =    4
  GEO          =    5
  UNTOKENIZED_PREFIX =    6
  TOKENIZED_PREFIX =    7
  VECTOR       =    8

  _ContentType_NAMES = {
    0: "TEXT",
    1: "HTML",
    2: "ATOM",
    3: "DATE",
    4: "NUMBER",
    5: "GEO",
    6: "UNTOKENIZED_PREFIX",
    7: "TOKENIZED_PREFIX",
    8: "VECTOR",
  }

  def ContentType_Name(cls, x): return cls._ContentType_NAMES.get(x, "")
  ContentType_Name = classmethod(ContentType_Name)

  has_type_ = 0
  type_ = 0
  has_language_ = 0
  language_ = "en"
  has_string_value_ = 0
  string_value_ = ""
  has_geo_ = 0
  geo_ = None

  def __init__(self, contents=None):
    self.vector_value_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def type(self): return self.type_

  def set_type(self, x):
    self.has_type_ = 1
    self.type_ = x

  def clear_type(self):
    if self.has_type_:
      self.has_type_ = 0
      self.type_ = 0

  def has_type(self): return self.has_type_

  def language(self): return self.language_

  def set_language(self, x):
    self.has_language_ = 1
    self.language_ = x

  def clear_language(self):
    if self.has_language_:
      self.has_language_ = 0
      self.language_ = "en"

  def has_language(self): return self.has_language_

  def string_value(self): return self.string_value_

  def set_string_value(self, x):
    self.has_string_value_ = 1
    self.string_value_ = x

  def clear_string_value(self):
    if self.has_string_value_:
      self.has_string_value_ = 0
      self.string_value_ = ""

  def has_string_value(self): return self.has_string_value_

  def geo(self):
    if self.geo_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.geo_ is None: self.geo_ = FieldValue_Geo()
      finally:
        self.lazy_init_lock_.release()
    return self.geo_

  def mutable_geo(self): self.has_geo_ = 1; return self.geo()

  def clear_geo(self):

    if self.has_geo_:
      self.has_geo_ = 0;
      if self.geo_ is not None: self.geo_.Clear()

  def has_geo(self): return self.has_geo_

  def vector_value_size(self): return len(self.vector_value_)
  def vector_value_list(self): return self.vector_value_

  def vector_value(self, i):
    return self.vector_value_[i]

  def set_vector_value(self, i, x):
    self.vector_value_[i] = x

  def add_vector_value(self, x):
    self.vector_value_.append(x)

  def clear_vector_value(self):
    self.vector_value_ = []


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_type()): self.set_type(x.type())
    if (x.has_language()): self.set_language(x.language())
    if (x.has_string_value()): self.set_string_value(x.string_value())
    if (x.has_geo()): self.mutable_geo().MergeFrom(x.geo())
    for i in xrange(x.vector_value_size()): self.add_vector_value(x.vector_value(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_type_ != x.has_type_: return 0
    if self.has_type_ and self.type_ != x.type_: return 0
    if self.has_language_ != x.has_language_: return 0
    if self.has_language_ and self.language_ != x.language_: return 0
    if self.has_string_value_ != x.has_string_value_: return 0
    if self.has_string_value_ and self.string_value_ != x.string_value_: return 0
    if self.has_geo_ != x.has_geo_: return 0
    if self.has_geo_ and self.geo_ != x.geo_: return 0
    if len(self.vector_value_) != len(x.vector_value_): return 0
    for e1, e2 in zip(self.vector_value_, x.vector_value_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_geo_ and not self.geo_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_type_): n += 1 + self.lengthVarInt64(self.type_)
    if (self.has_language_): n += 1 + self.lengthString(len(self.language_))
    if (self.has_string_value_): n += 1 + self.lengthString(len(self.string_value_))
    if (self.has_geo_): n += 2 + self.geo_.ByteSize()
    n += 9 * len(self.vector_value_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_type_): n += 1 + self.lengthVarInt64(self.type_)
    if (self.has_language_): n += 1 + self.lengthString(len(self.language_))
    if (self.has_string_value_): n += 1 + self.lengthString(len(self.string_value_))
    if (self.has_geo_): n += 2 + self.geo_.ByteSizePartial()
    n += 9 * len(self.vector_value_)
    return n

  def Clear(self):
    self.clear_type()
    self.clear_language()
    self.clear_string_value()
    self.clear_geo()
    self.clear_vector_value()

  def OutputUnchecked(self, out):
    if (self.has_type_):
      out.putVarInt32(8)
      out.putVarInt32(self.type_)
    if (self.has_language_):
      out.putVarInt32(18)
      out.putPrefixedString(self.language_)
    if (self.has_string_value_):
      out.putVarInt32(26)
      out.putPrefixedString(self.string_value_)
    if (self.has_geo_):
      out.putVarInt32(35)
      self.geo_.OutputUnchecked(out)
      out.putVarInt32(36)
    for i in xrange(len(self.vector_value_)):
      out.putVarInt32(57)
      out.putDouble(self.vector_value_[i])

  def OutputPartial(self, out):
    if (self.has_type_):
      out.putVarInt32(8)
      out.putVarInt32(self.type_)
    if (self.has_language_):
      out.putVarInt32(18)
      out.putPrefixedString(self.language_)
    if (self.has_string_value_):
      out.putVarInt32(26)
      out.putPrefixedString(self.string_value_)
    if (self.has_geo_):
      out.putVarInt32(35)
      self.geo_.OutputPartial(out)
      out.putVarInt32(36)
    for i in xrange(len(self.vector_value_)):
      out.putVarInt32(57)
      out.putDouble(self.vector_value_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_type(d.getVarInt32())
        continue
      if tt == 18:
        self.set_language(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_string_value(d.getPrefixedString())
        continue
      if tt == 35:
        self.mutable_geo().TryMerge(d)
        continue
      if tt == 57:
        self.add_vector_value(d.getDouble())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_type_: res+=prefix+("type: %s\n" % self.DebugFormatInt32(self.type_))
    if self.has_language_: res+=prefix+("language: %s\n" % self.DebugFormatString(self.language_))
    if self.has_string_value_: res+=prefix+("string_value: %s\n" % self.DebugFormatString(self.string_value_))
    if self.has_geo_:
      res+=prefix+"Geo {\n"
      res+=self.geo_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
    cnt=0
    for e in self.vector_value_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("vector_value%s: %s\n" % (elm, self.DebugFormat(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktype = 1
  klanguage = 2
  kstring_value = 3
  kGeoGroup = 4
  kGeolat = 5
  kGeolng = 6
  kvector_value = 7

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "type",
    2: "language",
    3: "string_value",
    4: "Geo",
    5: "lat",
    6: "lng",
    7: "vector_value",
  }, 7)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STARTGROUP,
    5: ProtocolBuffer.Encoder.DOUBLE,
    6: ProtocolBuffer.Encoder.DOUBLE,
    7: ProtocolBuffer.Encoder.DOUBLE,
  }, 7, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.FieldValue'
class Field(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""
  has_value_ = 0

  def __init__(self, contents=None):
    self.value_ = FieldValue()
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

  def value(self): return self.value_

  def mutable_value(self): self.has_value_ = 1; return self.value_

  def clear_value(self):self.has_value_ = 0; self.value_.Clear()

  def has_value(self): return self.has_value_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())
    if (x.has_value()): self.mutable_value().MergeFrom(x.value())

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: name not set.')
    if (not self.has_value_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: value not set.')
    elif not self.value_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.name_))
    n += self.lengthString(self.value_.ByteSize())
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    if (self.has_value_):
      n += 1
      n += self.lengthString(self.value_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_name()
    self.clear_value()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.name_)
    out.putVarInt32(18)
    out.putVarInt32(self.value_.ByteSize())
    self.value_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    if (self.has_value_):
      out.putVarInt32(18)
      out.putVarInt32(self.value_.ByteSizePartial())
      self.value_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_name(d.getPrefixedString())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_value().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    if self.has_value_:
      res+=prefix+"value <\n"
      res+=self.value_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 1
  kvalue = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name",
    2: "value",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.Field'
class FieldTypes(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""

  def __init__(self, contents=None):
    self.type_ = []
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

  def type_size(self): return len(self.type_)
  def type_list(self): return self.type_

  def type(self, i):
    return self.type_[i]

  def set_type(self, i, x):
    self.type_[i] = x

  def add_type(self, x):
    self.type_.append(x)

  def clear_type(self):
    self.type_ = []


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())
    for i in xrange(x.type_size()): self.add_type(x.type(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if len(self.type_) != len(x.type_): return 0
    for e1, e2 in zip(self.type_, x.type_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: name not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.name_))
    n += 1 * len(self.type_)
    for i in xrange(len(self.type_)): n += self.lengthVarInt64(self.type_[i])
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    n += 1 * len(self.type_)
    for i in xrange(len(self.type_)): n += self.lengthVarInt64(self.type_[i])
    return n

  def Clear(self):
    self.clear_name()
    self.clear_type()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.name_)
    for i in xrange(len(self.type_)):
      out.putVarInt32(16)
      out.putVarInt32(self.type_[i])

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    for i in xrange(len(self.type_)):
      out.putVarInt32(16)
      out.putVarInt32(self.type_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_name(d.getPrefixedString())
        continue
      if tt == 16:
        self.add_type(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    cnt=0
    for e in self.type_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("type%s: %s\n" % (elm, self.DebugFormatInt32(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 1
  ktype = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name",
    2: "type",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.FieldTypes'
class IndexShardSettings(ProtocolBuffer.ProtocolMessage):
  has_num_shards_ = 0
  num_shards_ = 1
  has_local_replica_ = 0
  local_replica_ = ""

  def __init__(self, contents=None):
    self.prev_num_shards_ = []
    self.prev_num_shards_search_false_ = []
    if contents is not None: self.MergeFromString(contents)

  def prev_num_shards_size(self): return len(self.prev_num_shards_)
  def prev_num_shards_list(self): return self.prev_num_shards_

  def prev_num_shards(self, i):
    return self.prev_num_shards_[i]

  def set_prev_num_shards(self, i, x):
    self.prev_num_shards_[i] = x

  def add_prev_num_shards(self, x):
    self.prev_num_shards_.append(x)

  def clear_prev_num_shards(self):
    self.prev_num_shards_ = []

  def num_shards(self): return self.num_shards_

  def set_num_shards(self, x):
    self.has_num_shards_ = 1
    self.num_shards_ = x

  def clear_num_shards(self):
    if self.has_num_shards_:
      self.has_num_shards_ = 0
      self.num_shards_ = 1

  def has_num_shards(self): return self.has_num_shards_

  def prev_num_shards_search_false_size(self): return len(self.prev_num_shards_search_false_)
  def prev_num_shards_search_false_list(self): return self.prev_num_shards_search_false_

  def prev_num_shards_search_false(self, i):
    return self.prev_num_shards_search_false_[i]

  def set_prev_num_shards_search_false(self, i, x):
    self.prev_num_shards_search_false_[i] = x

  def add_prev_num_shards_search_false(self, x):
    self.prev_num_shards_search_false_.append(x)

  def clear_prev_num_shards_search_false(self):
    self.prev_num_shards_search_false_ = []

  def local_replica(self): return self.local_replica_

  def set_local_replica(self, x):
    self.has_local_replica_ = 1
    self.local_replica_ = x

  def clear_local_replica(self):
    if self.has_local_replica_:
      self.has_local_replica_ = 0
      self.local_replica_ = ""

  def has_local_replica(self): return self.has_local_replica_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.prev_num_shards_size()): self.add_prev_num_shards(x.prev_num_shards(i))
    if (x.has_num_shards()): self.set_num_shards(x.num_shards())
    for i in xrange(x.prev_num_shards_search_false_size()): self.add_prev_num_shards_search_false(x.prev_num_shards_search_false(i))
    if (x.has_local_replica()): self.set_local_replica(x.local_replica())

  def Equals(self, x):
    if x is self: return 1
    if len(self.prev_num_shards_) != len(x.prev_num_shards_): return 0
    for e1, e2 in zip(self.prev_num_shards_, x.prev_num_shards_):
      if e1 != e2: return 0
    if self.has_num_shards_ != x.has_num_shards_: return 0
    if self.has_num_shards_ and self.num_shards_ != x.num_shards_: return 0
    if len(self.prev_num_shards_search_false_) != len(x.prev_num_shards_search_false_): return 0
    for e1, e2 in zip(self.prev_num_shards_search_false_, x.prev_num_shards_search_false_):
      if e1 != e2: return 0
    if self.has_local_replica_ != x.has_local_replica_: return 0
    if self.has_local_replica_ and self.local_replica_ != x.local_replica_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_num_shards_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: num_shards not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.prev_num_shards_)
    for i in xrange(len(self.prev_num_shards_)): n += self.lengthVarInt64(self.prev_num_shards_[i])
    n += self.lengthVarInt64(self.num_shards_)
    n += 1 * len(self.prev_num_shards_search_false_)
    for i in xrange(len(self.prev_num_shards_search_false_)): n += self.lengthVarInt64(self.prev_num_shards_search_false_[i])
    if (self.has_local_replica_): n += 1 + self.lengthString(len(self.local_replica_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.prev_num_shards_)
    for i in xrange(len(self.prev_num_shards_)): n += self.lengthVarInt64(self.prev_num_shards_[i])
    if (self.has_num_shards_):
      n += 1
      n += self.lengthVarInt64(self.num_shards_)
    n += 1 * len(self.prev_num_shards_search_false_)
    for i in xrange(len(self.prev_num_shards_search_false_)): n += self.lengthVarInt64(self.prev_num_shards_search_false_[i])
    if (self.has_local_replica_): n += 1 + self.lengthString(len(self.local_replica_))
    return n

  def Clear(self):
    self.clear_prev_num_shards()
    self.clear_num_shards()
    self.clear_prev_num_shards_search_false()
    self.clear_local_replica()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.prev_num_shards_)):
      out.putVarInt32(8)
      out.putVarInt32(self.prev_num_shards_[i])
    out.putVarInt32(16)
    out.putVarInt32(self.num_shards_)
    for i in xrange(len(self.prev_num_shards_search_false_)):
      out.putVarInt32(24)
      out.putVarInt32(self.prev_num_shards_search_false_[i])
    if (self.has_local_replica_):
      out.putVarInt32(34)
      out.putPrefixedString(self.local_replica_)

  def OutputPartial(self, out):
    for i in xrange(len(self.prev_num_shards_)):
      out.putVarInt32(8)
      out.putVarInt32(self.prev_num_shards_[i])
    if (self.has_num_shards_):
      out.putVarInt32(16)
      out.putVarInt32(self.num_shards_)
    for i in xrange(len(self.prev_num_shards_search_false_)):
      out.putVarInt32(24)
      out.putVarInt32(self.prev_num_shards_search_false_[i])
    if (self.has_local_replica_):
      out.putVarInt32(34)
      out.putPrefixedString(self.local_replica_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.add_prev_num_shards(d.getVarInt32())
        continue
      if tt == 16:
        self.set_num_shards(d.getVarInt32())
        continue
      if tt == 24:
        self.add_prev_num_shards_search_false(d.getVarInt32())
        continue
      if tt == 34:
        self.set_local_replica(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.prev_num_shards_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("prev_num_shards%s: %s\n" % (elm, self.DebugFormatInt32(e)))
      cnt+=1
    if self.has_num_shards_: res+=prefix+("num_shards: %s\n" % self.DebugFormatInt32(self.num_shards_))
    cnt=0
    for e in self.prev_num_shards_search_false_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("prev_num_shards_search_false%s: %s\n" % (elm, self.DebugFormatInt32(e)))
      cnt+=1
    if self.has_local_replica_: res+=prefix+("local_replica: %s\n" % self.DebugFormatString(self.local_replica_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kprev_num_shards = 1
  knum_shards = 2
  kprev_num_shards_search_false = 3
  klocal_replica = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "prev_num_shards",
    2: "num_shards",
    3: "prev_num_shards_search_false",
    4: "local_replica",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.IndexShardSettings'
class IndexMetadata(ProtocolBuffer.ProtocolMessage):


  ACTIVE       =    0
  SOFT_DELETED =    1
  PURGING      =    2

  _IndexState_NAMES = {
    0: "ACTIVE",
    1: "SOFT_DELETED",
    2: "PURGING",
  }

  def IndexState_Name(cls, x): return cls._IndexState_NAMES.get(x, "")
  IndexState_Name = classmethod(IndexState_Name)

  has_is_over_field_number_threshold_ = 0
  is_over_field_number_threshold_ = 0
  has_index_shard_settings_ = 0
  index_shard_settings_ = None
  has_index_state_ = 0
  index_state_ = 0
  has_index_delete_time_ = 0
  index_delete_time_ = 0
  has_max_index_size_bytes_ = 0
  max_index_size_bytes_ = 0

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def is_over_field_number_threshold(self): return self.is_over_field_number_threshold_

  def set_is_over_field_number_threshold(self, x):
    self.has_is_over_field_number_threshold_ = 1
    self.is_over_field_number_threshold_ = x

  def clear_is_over_field_number_threshold(self):
    if self.has_is_over_field_number_threshold_:
      self.has_is_over_field_number_threshold_ = 0
      self.is_over_field_number_threshold_ = 0

  def has_is_over_field_number_threshold(self): return self.has_is_over_field_number_threshold_

  def index_shard_settings(self):
    if self.index_shard_settings_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.index_shard_settings_ is None: self.index_shard_settings_ = IndexShardSettings()
      finally:
        self.lazy_init_lock_.release()
    return self.index_shard_settings_

  def mutable_index_shard_settings(self): self.has_index_shard_settings_ = 1; return self.index_shard_settings()

  def clear_index_shard_settings(self):

    if self.has_index_shard_settings_:
      self.has_index_shard_settings_ = 0;
      if self.index_shard_settings_ is not None: self.index_shard_settings_.Clear()

  def has_index_shard_settings(self): return self.has_index_shard_settings_

  def index_state(self): return self.index_state_

  def set_index_state(self, x):
    self.has_index_state_ = 1
    self.index_state_ = x

  def clear_index_state(self):
    if self.has_index_state_:
      self.has_index_state_ = 0
      self.index_state_ = 0

  def has_index_state(self): return self.has_index_state_

  def index_delete_time(self): return self.index_delete_time_

  def set_index_delete_time(self, x):
    self.has_index_delete_time_ = 1
    self.index_delete_time_ = x

  def clear_index_delete_time(self):
    if self.has_index_delete_time_:
      self.has_index_delete_time_ = 0
      self.index_delete_time_ = 0

  def has_index_delete_time(self): return self.has_index_delete_time_

  def max_index_size_bytes(self): return self.max_index_size_bytes_

  def set_max_index_size_bytes(self, x):
    self.has_max_index_size_bytes_ = 1
    self.max_index_size_bytes_ = x

  def clear_max_index_size_bytes(self):
    if self.has_max_index_size_bytes_:
      self.has_max_index_size_bytes_ = 0
      self.max_index_size_bytes_ = 0

  def has_max_index_size_bytes(self): return self.has_max_index_size_bytes_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_is_over_field_number_threshold()): self.set_is_over_field_number_threshold(x.is_over_field_number_threshold())
    if (x.has_index_shard_settings()): self.mutable_index_shard_settings().MergeFrom(x.index_shard_settings())
    if (x.has_index_state()): self.set_index_state(x.index_state())
    if (x.has_index_delete_time()): self.set_index_delete_time(x.index_delete_time())
    if (x.has_max_index_size_bytes()): self.set_max_index_size_bytes(x.max_index_size_bytes())

  def Equals(self, x):
    if x is self: return 1
    if self.has_is_over_field_number_threshold_ != x.has_is_over_field_number_threshold_: return 0
    if self.has_is_over_field_number_threshold_ and self.is_over_field_number_threshold_ != x.is_over_field_number_threshold_: return 0
    if self.has_index_shard_settings_ != x.has_index_shard_settings_: return 0
    if self.has_index_shard_settings_ and self.index_shard_settings_ != x.index_shard_settings_: return 0
    if self.has_index_state_ != x.has_index_state_: return 0
    if self.has_index_state_ and self.index_state_ != x.index_state_: return 0
    if self.has_index_delete_time_ != x.has_index_delete_time_: return 0
    if self.has_index_delete_time_ and self.index_delete_time_ != x.index_delete_time_: return 0
    if self.has_max_index_size_bytes_ != x.has_max_index_size_bytes_: return 0
    if self.has_max_index_size_bytes_ and self.max_index_size_bytes_ != x.max_index_size_bytes_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_index_shard_settings_ and not self.index_shard_settings_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_is_over_field_number_threshold_): n += 2
    if (self.has_index_shard_settings_): n += 1 + self.lengthString(self.index_shard_settings_.ByteSize())
    if (self.has_index_state_): n += 1 + self.lengthVarInt64(self.index_state_)
    if (self.has_index_delete_time_): n += 1 + self.lengthVarInt64(self.index_delete_time_)
    if (self.has_max_index_size_bytes_): n += 1 + self.lengthVarInt64(self.max_index_size_bytes_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_is_over_field_number_threshold_): n += 2
    if (self.has_index_shard_settings_): n += 1 + self.lengthString(self.index_shard_settings_.ByteSizePartial())
    if (self.has_index_state_): n += 1 + self.lengthVarInt64(self.index_state_)
    if (self.has_index_delete_time_): n += 1 + self.lengthVarInt64(self.index_delete_time_)
    if (self.has_max_index_size_bytes_): n += 1 + self.lengthVarInt64(self.max_index_size_bytes_)
    return n

  def Clear(self):
    self.clear_is_over_field_number_threshold()
    self.clear_index_shard_settings()
    self.clear_index_state()
    self.clear_index_delete_time()
    self.clear_max_index_size_bytes()

  def OutputUnchecked(self, out):
    if (self.has_is_over_field_number_threshold_):
      out.putVarInt32(8)
      out.putBoolean(self.is_over_field_number_threshold_)
    if (self.has_index_shard_settings_):
      out.putVarInt32(18)
      out.putVarInt32(self.index_shard_settings_.ByteSize())
      self.index_shard_settings_.OutputUnchecked(out)
    if (self.has_index_state_):
      out.putVarInt32(24)
      out.putVarInt32(self.index_state_)
    if (self.has_index_delete_time_):
      out.putVarInt32(32)
      out.putVarInt64(self.index_delete_time_)
    if (self.has_max_index_size_bytes_):
      out.putVarInt32(40)
      out.putVarInt64(self.max_index_size_bytes_)

  def OutputPartial(self, out):
    if (self.has_is_over_field_number_threshold_):
      out.putVarInt32(8)
      out.putBoolean(self.is_over_field_number_threshold_)
    if (self.has_index_shard_settings_):
      out.putVarInt32(18)
      out.putVarInt32(self.index_shard_settings_.ByteSizePartial())
      self.index_shard_settings_.OutputPartial(out)
    if (self.has_index_state_):
      out.putVarInt32(24)
      out.putVarInt32(self.index_state_)
    if (self.has_index_delete_time_):
      out.putVarInt32(32)
      out.putVarInt64(self.index_delete_time_)
    if (self.has_max_index_size_bytes_):
      out.putVarInt32(40)
      out.putVarInt64(self.max_index_size_bytes_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_is_over_field_number_threshold(d.getBoolean())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_index_shard_settings().TryMerge(tmp)
        continue
      if tt == 24:
        self.set_index_state(d.getVarInt32())
        continue
      if tt == 32:
        self.set_index_delete_time(d.getVarInt64())
        continue
      if tt == 40:
        self.set_max_index_size_bytes(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_is_over_field_number_threshold_: res+=prefix+("is_over_field_number_threshold: %s\n" % self.DebugFormatBool(self.is_over_field_number_threshold_))
    if self.has_index_shard_settings_:
      res+=prefix+"index_shard_settings <\n"
      res+=self.index_shard_settings_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_index_state_: res+=prefix+("index_state: %s\n" % self.DebugFormatInt32(self.index_state_))
    if self.has_index_delete_time_: res+=prefix+("index_delete_time: %s\n" % self.DebugFormatInt64(self.index_delete_time_))
    if self.has_max_index_size_bytes_: res+=prefix+("max_index_size_bytes: %s\n" % self.DebugFormatInt64(self.max_index_size_bytes_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kis_over_field_number_threshold = 1
  kindex_shard_settings = 2
  kindex_state = 3
  kindex_delete_time = 4
  kmax_index_size_bytes = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "is_over_field_number_threshold",
    2: "index_shard_settings",
    3: "index_state",
    4: "index_delete_time",
    5: "max_index_size_bytes",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.NUMERIC,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.IndexMetadata'
class FacetValue(ProtocolBuffer.ProtocolMessage):


  ATOM         =    2
  NUMBER       =    4

  _ContentType_NAMES = {
    2: "ATOM",
    4: "NUMBER",
  }

  def ContentType_Name(cls, x): return cls._ContentType_NAMES.get(x, "")
  ContentType_Name = classmethod(ContentType_Name)

  has_type_ = 0
  type_ = 2
  has_string_value_ = 0
  string_value_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def type(self): return self.type_

  def set_type(self, x):
    self.has_type_ = 1
    self.type_ = x

  def clear_type(self):
    if self.has_type_:
      self.has_type_ = 0
      self.type_ = 2

  def has_type(self): return self.has_type_

  def string_value(self): return self.string_value_

  def set_string_value(self, x):
    self.has_string_value_ = 1
    self.string_value_ = x

  def clear_string_value(self):
    if self.has_string_value_:
      self.has_string_value_ = 0
      self.string_value_ = ""

  def has_string_value(self): return self.has_string_value_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_type()): self.set_type(x.type())
    if (x.has_string_value()): self.set_string_value(x.string_value())

  def Equals(self, x):
    if x is self: return 1
    if self.has_type_ != x.has_type_: return 0
    if self.has_type_ and self.type_ != x.type_: return 0
    if self.has_string_value_ != x.has_string_value_: return 0
    if self.has_string_value_ and self.string_value_ != x.string_value_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_type_): n += 1 + self.lengthVarInt64(self.type_)
    if (self.has_string_value_): n += 1 + self.lengthString(len(self.string_value_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_type_): n += 1 + self.lengthVarInt64(self.type_)
    if (self.has_string_value_): n += 1 + self.lengthString(len(self.string_value_))
    return n

  def Clear(self):
    self.clear_type()
    self.clear_string_value()

  def OutputUnchecked(self, out):
    if (self.has_type_):
      out.putVarInt32(8)
      out.putVarInt32(self.type_)
    if (self.has_string_value_):
      out.putVarInt32(26)
      out.putPrefixedString(self.string_value_)

  def OutputPartial(self, out):
    if (self.has_type_):
      out.putVarInt32(8)
      out.putVarInt32(self.type_)
    if (self.has_string_value_):
      out.putVarInt32(26)
      out.putPrefixedString(self.string_value_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_type(d.getVarInt32())
        continue
      if tt == 26:
        self.set_string_value(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_type_: res+=prefix+("type: %s\n" % self.DebugFormatInt32(self.type_))
    if self.has_string_value_: res+=prefix+("string_value: %s\n" % self.DebugFormatString(self.string_value_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktype = 1
  kstring_value = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "type",
    3: "string_value",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.FacetValue'
class Facet(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""
  has_value_ = 0

  def __init__(self, contents=None):
    self.value_ = FacetValue()
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

  def value(self): return self.value_

  def mutable_value(self): self.has_value_ = 1; return self.value_

  def clear_value(self):self.has_value_ = 0; self.value_.Clear()

  def has_value(self): return self.has_value_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())
    if (x.has_value()): self.mutable_value().MergeFrom(x.value())

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: name not set.')
    if (not self.has_value_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: value not set.')
    elif not self.value_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.name_))
    n += self.lengthString(self.value_.ByteSize())
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    if (self.has_value_):
      n += 1
      n += self.lengthString(self.value_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_name()
    self.clear_value()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.name_)
    out.putVarInt32(18)
    out.putVarInt32(self.value_.ByteSize())
    self.value_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    if (self.has_value_):
      out.putVarInt32(18)
      out.putVarInt32(self.value_.ByteSizePartial())
      self.value_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_name(d.getPrefixedString())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_value().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    if self.has_value_:
      res+=prefix+"value <\n"
      res+=self.value_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 1
  kvalue = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name",
    2: "value",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.Facet'
class DocumentMetadata(ProtocolBuffer.ProtocolMessage):
  has_version_ = 0
  version_ = 0
  has_committed_st_version_ = 0
  committed_st_version_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def version(self): return self.version_

  def set_version(self, x):
    self.has_version_ = 1
    self.version_ = x

  def clear_version(self):
    if self.has_version_:
      self.has_version_ = 0
      self.version_ = 0

  def has_version(self): return self.has_version_

  def committed_st_version(self): return self.committed_st_version_

  def set_committed_st_version(self, x):
    self.has_committed_st_version_ = 1
    self.committed_st_version_ = x

  def clear_committed_st_version(self):
    if self.has_committed_st_version_:
      self.has_committed_st_version_ = 0
      self.committed_st_version_ = 0

  def has_committed_st_version(self): return self.has_committed_st_version_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_version()): self.set_version(x.version())
    if (x.has_committed_st_version()): self.set_committed_st_version(x.committed_st_version())

  def Equals(self, x):
    if x is self: return 1
    if self.has_version_ != x.has_version_: return 0
    if self.has_version_ and self.version_ != x.version_: return 0
    if self.has_committed_st_version_ != x.has_committed_st_version_: return 0
    if self.has_committed_st_version_ and self.committed_st_version_ != x.committed_st_version_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_version_): n += 1 + self.lengthVarInt64(self.version_)
    if (self.has_committed_st_version_): n += 1 + self.lengthVarInt64(self.committed_st_version_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_version_): n += 1 + self.lengthVarInt64(self.version_)
    if (self.has_committed_st_version_): n += 1 + self.lengthVarInt64(self.committed_st_version_)
    return n

  def Clear(self):
    self.clear_version()
    self.clear_committed_st_version()

  def OutputUnchecked(self, out):
    if (self.has_version_):
      out.putVarInt32(8)
      out.putVarInt64(self.version_)
    if (self.has_committed_st_version_):
      out.putVarInt32(16)
      out.putVarInt64(self.committed_st_version_)

  def OutputPartial(self, out):
    if (self.has_version_):
      out.putVarInt32(8)
      out.putVarInt64(self.version_)
    if (self.has_committed_st_version_):
      out.putVarInt32(16)
      out.putVarInt64(self.committed_st_version_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_version(d.getVarInt64())
        continue
      if tt == 16:
        self.set_committed_st_version(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_version_: res+=prefix+("version: %s\n" % self.DebugFormatInt64(self.version_))
    if self.has_committed_st_version_: res+=prefix+("committed_st_version: %s\n" % self.DebugFormatInt64(self.committed_st_version_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kversion = 1
  kcommitted_st_version = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "version",
    2: "committed_st_version",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.DocumentMetadata'
class Document(ProtocolBuffer.ProtocolMessage):


  DISK         =    0

  _Storage_NAMES = {
    0: "DISK",
  }

  def Storage_Name(cls, x): return cls._Storage_NAMES.get(x, "")
  Storage_Name = classmethod(Storage_Name)

  has_id_ = 0
  id_ = ""
  has_language_ = 0
  language_ = "en"
  has_order_id_ = 0
  order_id_ = 0
  has_storage_ = 0
  storage_ = 0

  def __init__(self, contents=None):
    self.field_ = []
    self.facet_ = []
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

  def language(self): return self.language_

  def set_language(self, x):
    self.has_language_ = 1
    self.language_ = x

  def clear_language(self):
    if self.has_language_:
      self.has_language_ = 0
      self.language_ = "en"

  def has_language(self): return self.has_language_

  def field_size(self): return len(self.field_)
  def field_list(self): return self.field_

  def field(self, i):
    return self.field_[i]

  def mutable_field(self, i):
    return self.field_[i]

  def add_field(self):
    x = Field()
    self.field_.append(x)
    return x

  def clear_field(self):
    self.field_ = []
  def order_id(self): return self.order_id_

  def set_order_id(self, x):
    self.has_order_id_ = 1
    self.order_id_ = x

  def clear_order_id(self):
    if self.has_order_id_:
      self.has_order_id_ = 0
      self.order_id_ = 0

  def has_order_id(self): return self.has_order_id_

  def storage(self): return self.storage_

  def set_storage(self, x):
    self.has_storage_ = 1
    self.storage_ = x

  def clear_storage(self):
    if self.has_storage_:
      self.has_storage_ = 0
      self.storage_ = 0

  def has_storage(self): return self.has_storage_

  def facet_size(self): return len(self.facet_)
  def facet_list(self): return self.facet_

  def facet(self, i):
    return self.facet_[i]

  def mutable_facet(self, i):
    return self.facet_[i]

  def add_facet(self):
    x = Facet()
    self.facet_.append(x)
    return x

  def clear_facet(self):
    self.facet_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_id()): self.set_id(x.id())
    if (x.has_language()): self.set_language(x.language())
    for i in xrange(x.field_size()): self.add_field().CopyFrom(x.field(i))
    if (x.has_order_id()): self.set_order_id(x.order_id())
    if (x.has_storage()): self.set_storage(x.storage())
    for i in xrange(x.facet_size()): self.add_facet().CopyFrom(x.facet(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_id_ != x.has_id_: return 0
    if self.has_id_ and self.id_ != x.id_: return 0
    if self.has_language_ != x.has_language_: return 0
    if self.has_language_ and self.language_ != x.language_: return 0
    if len(self.field_) != len(x.field_): return 0
    for e1, e2 in zip(self.field_, x.field_):
      if e1 != e2: return 0
    if self.has_order_id_ != x.has_order_id_: return 0
    if self.has_order_id_ and self.order_id_ != x.order_id_: return 0
    if self.has_storage_ != x.has_storage_: return 0
    if self.has_storage_ and self.storage_ != x.storage_: return 0
    if len(self.facet_) != len(x.facet_): return 0
    for e1, e2 in zip(self.facet_, x.facet_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.field_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.facet_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_id_): n += 1 + self.lengthString(len(self.id_))
    if (self.has_language_): n += 1 + self.lengthString(len(self.language_))
    n += 1 * len(self.field_)
    for i in xrange(len(self.field_)): n += self.lengthString(self.field_[i].ByteSize())
    if (self.has_order_id_): n += 1 + self.lengthVarInt64(self.order_id_)
    if (self.has_storage_): n += 1 + self.lengthVarInt64(self.storage_)
    n += 1 * len(self.facet_)
    for i in xrange(len(self.facet_)): n += self.lengthString(self.facet_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_id_): n += 1 + self.lengthString(len(self.id_))
    if (self.has_language_): n += 1 + self.lengthString(len(self.language_))
    n += 1 * len(self.field_)
    for i in xrange(len(self.field_)): n += self.lengthString(self.field_[i].ByteSizePartial())
    if (self.has_order_id_): n += 1 + self.lengthVarInt64(self.order_id_)
    if (self.has_storage_): n += 1 + self.lengthVarInt64(self.storage_)
    n += 1 * len(self.facet_)
    for i in xrange(len(self.facet_)): n += self.lengthString(self.facet_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_id()
    self.clear_language()
    self.clear_field()
    self.clear_order_id()
    self.clear_storage()
    self.clear_facet()

  def OutputUnchecked(self, out):
    if (self.has_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.id_)
    if (self.has_language_):
      out.putVarInt32(18)
      out.putPrefixedString(self.language_)
    for i in xrange(len(self.field_)):
      out.putVarInt32(26)
      out.putVarInt32(self.field_[i].ByteSize())
      self.field_[i].OutputUnchecked(out)
    if (self.has_order_id_):
      out.putVarInt32(32)
      out.putVarInt32(self.order_id_)
    if (self.has_storage_):
      out.putVarInt32(40)
      out.putVarInt32(self.storage_)
    for i in xrange(len(self.facet_)):
      out.putVarInt32(66)
      out.putVarInt32(self.facet_[i].ByteSize())
      self.facet_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.id_)
    if (self.has_language_):
      out.putVarInt32(18)
      out.putPrefixedString(self.language_)
    for i in xrange(len(self.field_)):
      out.putVarInt32(26)
      out.putVarInt32(self.field_[i].ByteSizePartial())
      self.field_[i].OutputPartial(out)
    if (self.has_order_id_):
      out.putVarInt32(32)
      out.putVarInt32(self.order_id_)
    if (self.has_storage_):
      out.putVarInt32(40)
      out.putVarInt32(self.storage_)
    for i in xrange(len(self.facet_)):
      out.putVarInt32(66)
      out.putVarInt32(self.facet_[i].ByteSizePartial())
      self.facet_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_language(d.getPrefixedString())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_field().TryMerge(tmp)
        continue
      if tt == 32:
        self.set_order_id(d.getVarInt32())
        continue
      if tt == 40:
        self.set_storage(d.getVarInt32())
        continue
      if tt == 66:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_facet().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_id_: res+=prefix+("id: %s\n" % self.DebugFormatString(self.id_))
    if self.has_language_: res+=prefix+("language: %s\n" % self.DebugFormatString(self.language_))
    cnt=0
    for e in self.field_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("field%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_order_id_: res+=prefix+("order_id: %s\n" % self.DebugFormatInt32(self.order_id_))
    if self.has_storage_: res+=prefix+("storage: %s\n" % self.DebugFormatInt32(self.storage_))
    cnt=0
    for e in self.facet_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("facet%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kid = 1
  klanguage = 2
  kfield = 3
  korder_id = 4
  kstorage = 5
  kfacet = 8

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "id",
    2: "language",
    3: "field",
    4: "order_id",
    5: "storage",
    8: "facet",
  }, 8)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.NUMERIC,
    8: ProtocolBuffer.Encoder.STRING,
  }, 8, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.Document'
if _extension_runtime:
  pass

__all__ = ['FieldValue','FieldValue_Geo','Field','FieldTypes','IndexShardSettings','IndexMetadata','FacetValue','Facet','DocumentMetadata','Document']
