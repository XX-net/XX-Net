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
from google.appengine.datastore.action_pb import *
import google.appengine.datastore.action_pb
from google.appengine.datastore.entity_pb import *
import google.appengine.datastore.entity_pb
from google.appengine.datastore.snapshot_pb import *
import google.appengine.datastore.snapshot_pb
class Transaction(ProtocolBuffer.ProtocolMessage):
  has_handle_ = 0
  handle_ = 0
  has_app_ = 0
  app_ = ""
  has_database_id_ = 0
  database_id_ = ""
  has_mark_changes_ = 0
  mark_changes_ = 0

  def __init__(self, contents=None):
    self.composite_index_ = []
    if contents is not None: self.MergeFromString(contents)

  def handle(self): return self.handle_

  def set_handle(self, x):
    self.has_handle_ = 1
    self.handle_ = x

  def clear_handle(self):
    if self.has_handle_:
      self.has_handle_ = 0
      self.handle_ = 0

  def has_handle(self): return self.has_handle_

  def app(self): return self.app_

  def set_app(self, x):
    self.has_app_ = 1
    self.app_ = x

  def clear_app(self):
    if self.has_app_:
      self.has_app_ = 0
      self.app_ = ""

  def has_app(self): return self.has_app_

  def database_id(self): return self.database_id_

  def set_database_id(self, x):
    self.has_database_id_ = 1
    self.database_id_ = x

  def clear_database_id(self):
    if self.has_database_id_:
      self.has_database_id_ = 0
      self.database_id_ = ""

  def has_database_id(self): return self.has_database_id_

  def mark_changes(self): return self.mark_changes_

  def set_mark_changes(self, x):
    self.has_mark_changes_ = 1
    self.mark_changes_ = x

  def clear_mark_changes(self):
    if self.has_mark_changes_:
      self.has_mark_changes_ = 0
      self.mark_changes_ = 0

  def has_mark_changes(self): return self.has_mark_changes_

  def composite_index_size(self): return len(self.composite_index_)
  def composite_index_list(self): return self.composite_index_

  def composite_index(self, i):
    return self.composite_index_[i]

  def mutable_composite_index(self, i):
    return self.composite_index_[i]

  def add_composite_index(self):
    x = CompositeIndex()
    self.composite_index_.append(x)
    return x

  def clear_composite_index(self):
    self.composite_index_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_handle()): self.set_handle(x.handle())
    if (x.has_app()): self.set_app(x.app())
    if (x.has_database_id()): self.set_database_id(x.database_id())
    if (x.has_mark_changes()): self.set_mark_changes(x.mark_changes())
    for i in xrange(x.composite_index_size()): self.add_composite_index().CopyFrom(x.composite_index(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_handle_ != x.has_handle_: return 0
    if self.has_handle_ and self.handle_ != x.handle_: return 0
    if self.has_app_ != x.has_app_: return 0
    if self.has_app_ and self.app_ != x.app_: return 0
    if self.has_database_id_ != x.has_database_id_: return 0
    if self.has_database_id_ and self.database_id_ != x.database_id_: return 0
    if self.has_mark_changes_ != x.has_mark_changes_: return 0
    if self.has_mark_changes_ and self.mark_changes_ != x.mark_changes_: return 0
    if len(self.composite_index_) != len(x.composite_index_): return 0
    for e1, e2 in zip(self.composite_index_, x.composite_index_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_handle_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: handle not set.')
    if (not self.has_app_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: app not set.')
    for p in self.composite_index_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.app_))
    if (self.has_database_id_): n += 1 + self.lengthString(len(self.database_id_))
    if (self.has_mark_changes_): n += 2
    n += 1 * len(self.composite_index_)
    for i in xrange(len(self.composite_index_)): n += self.lengthString(self.composite_index_[i].ByteSize())
    return n + 10

  def ByteSizePartial(self):
    n = 0
    if (self.has_handle_):
      n += 9
    if (self.has_app_):
      n += 1
      n += self.lengthString(len(self.app_))
    if (self.has_database_id_): n += 1 + self.lengthString(len(self.database_id_))
    if (self.has_mark_changes_): n += 2
    n += 1 * len(self.composite_index_)
    for i in xrange(len(self.composite_index_)): n += self.lengthString(self.composite_index_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_handle()
    self.clear_app()
    self.clear_database_id()
    self.clear_mark_changes()
    self.clear_composite_index()

  def OutputUnchecked(self, out):
    out.putVarInt32(9)
    out.put64(self.handle_)
    out.putVarInt32(18)
    out.putPrefixedString(self.app_)
    if (self.has_mark_changes_):
      out.putVarInt32(24)
      out.putBoolean(self.mark_changes_)
    for i in xrange(len(self.composite_index_)):
      out.putVarInt32(42)
      out.putVarInt32(self.composite_index_[i].ByteSize())
      self.composite_index_[i].OutputUnchecked(out)
    if (self.has_database_id_):
      out.putVarInt32(50)
      out.putPrefixedString(self.database_id_)

  def OutputPartial(self, out):
    if (self.has_handle_):
      out.putVarInt32(9)
      out.put64(self.handle_)
    if (self.has_app_):
      out.putVarInt32(18)
      out.putPrefixedString(self.app_)
    if (self.has_mark_changes_):
      out.putVarInt32(24)
      out.putBoolean(self.mark_changes_)
    for i in xrange(len(self.composite_index_)):
      out.putVarInt32(42)
      out.putVarInt32(self.composite_index_[i].ByteSizePartial())
      self.composite_index_[i].OutputPartial(out)
    if (self.has_database_id_):
      out.putVarInt32(50)
      out.putPrefixedString(self.database_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 9:
        self.set_handle(d.get64())
        continue
      if tt == 18:
        self.set_app(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_mark_changes(d.getBoolean())
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_composite_index().TryMerge(tmp)
        continue
      if tt == 50:
        self.set_database_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_handle_: res+=prefix+("handle: %s\n" % self.DebugFormatFixed64(self.handle_))
    if self.has_app_: res+=prefix+("app: %s\n" % self.DebugFormatString(self.app_))
    if self.has_database_id_: res+=prefix+("database_id: %s\n" % self.DebugFormatString(self.database_id_))
    if self.has_mark_changes_: res+=prefix+("mark_changes: %s\n" % self.DebugFormatBool(self.mark_changes_))
    cnt=0
    for e in self.composite_index_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("composite_index%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  khandle = 1
  kapp = 2
  kdatabase_id = 6
  kmark_changes = 3
  kcomposite_index = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "handle",
    2: "app",
    3: "mark_changes",
    5: "composite_index",
    6: "database_id",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.DOUBLE,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.STRING,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.Transaction'
class Query_Filter(ProtocolBuffer.ProtocolMessage):


  LESS_THAN    =    1
  LESS_THAN_OR_EQUAL =    2
  GREATER_THAN =    3
  GREATER_THAN_OR_EQUAL =    4
  EQUAL        =    5
  IN           =    6
  EXISTS       =    7
  CONTAINED_IN_REGION =    8

  _Operator_NAMES = {
    1: "LESS_THAN",
    2: "LESS_THAN_OR_EQUAL",
    3: "GREATER_THAN",
    4: "GREATER_THAN_OR_EQUAL",
    5: "EQUAL",
    6: "IN",
    7: "EXISTS",
    8: "CONTAINED_IN_REGION",
  }

  def Operator_Name(cls, x): return cls._Operator_NAMES.get(x, "")
  Operator_Name = classmethod(Operator_Name)

  has_op_ = 0
  op_ = 0
  has_geo_region_ = 0
  geo_region_ = None

  def __init__(self, contents=None):
    self.property_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def op(self): return self.op_

  def set_op(self, x):
    self.has_op_ = 1
    self.op_ = x

  def clear_op(self):
    if self.has_op_:
      self.has_op_ = 0
      self.op_ = 0

  def has_op(self): return self.has_op_

  def property_size(self): return len(self.property_)
  def property_list(self): return self.property_

  def property(self, i):
    return self.property_[i]

  def mutable_property(self, i):
    return self.property_[i]

  def add_property(self):
    x = Property()
    self.property_.append(x)
    return x

  def clear_property(self):
    self.property_ = []
  def geo_region(self):
    if self.geo_region_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.geo_region_ is None: self.geo_region_ = GeoRegion()
      finally:
        self.lazy_init_lock_.release()
    return self.geo_region_

  def mutable_geo_region(self): self.has_geo_region_ = 1; return self.geo_region()

  def clear_geo_region(self):

    if self.has_geo_region_:
      self.has_geo_region_ = 0;
      if self.geo_region_ is not None: self.geo_region_.Clear()

  def has_geo_region(self): return self.has_geo_region_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_op()): self.set_op(x.op())
    for i in xrange(x.property_size()): self.add_property().CopyFrom(x.property(i))
    if (x.has_geo_region()): self.mutable_geo_region().MergeFrom(x.geo_region())

  def Equals(self, x):
    if x is self: return 1
    if self.has_op_ != x.has_op_: return 0
    if self.has_op_ and self.op_ != x.op_: return 0
    if len(self.property_) != len(x.property_): return 0
    for e1, e2 in zip(self.property_, x.property_):
      if e1 != e2: return 0
    if self.has_geo_region_ != x.has_geo_region_: return 0
    if self.has_geo_region_ and self.geo_region_ != x.geo_region_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_op_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: op not set.')
    for p in self.property_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_geo_region_ and not self.geo_region_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.op_)
    n += 1 * len(self.property_)
    for i in xrange(len(self.property_)): n += self.lengthString(self.property_[i].ByteSize())
    if (self.has_geo_region_): n += 2 + self.lengthString(self.geo_region_.ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_op_):
      n += 1
      n += self.lengthVarInt64(self.op_)
    n += 1 * len(self.property_)
    for i in xrange(len(self.property_)): n += self.lengthString(self.property_[i].ByteSizePartial())
    if (self.has_geo_region_): n += 2 + self.lengthString(self.geo_region_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_op()
    self.clear_property()
    self.clear_geo_region()

  def OutputUnchecked(self, out):
    out.putVarInt32(48)
    out.putVarInt32(self.op_)
    for i in xrange(len(self.property_)):
      out.putVarInt32(114)
      out.putVarInt32(self.property_[i].ByteSize())
      self.property_[i].OutputUnchecked(out)
    if (self.has_geo_region_):
      out.putVarInt32(322)
      out.putVarInt32(self.geo_region_.ByteSize())
      self.geo_region_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_op_):
      out.putVarInt32(48)
      out.putVarInt32(self.op_)
    for i in xrange(len(self.property_)):
      out.putVarInt32(114)
      out.putVarInt32(self.property_[i].ByteSizePartial())
      self.property_[i].OutputPartial(out)
    if (self.has_geo_region_):
      out.putVarInt32(322)
      out.putVarInt32(self.geo_region_.ByteSizePartial())
      self.geo_region_.OutputPartial(out)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 36: break
      if tt == 48:
        self.set_op(d.getVarInt32())
        continue
      if tt == 114:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_property().TryMerge(tmp)
        continue
      if tt == 322:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_geo_region().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_op_: res+=prefix+("op: %s\n" % self.DebugFormatInt32(self.op_))
    cnt=0
    for e in self.property_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("property%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_geo_region_:
      res+=prefix+"geo_region <\n"
      res+=self.geo_region_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res

class Query_Order(ProtocolBuffer.ProtocolMessage):


  ASCENDING    =    1
  DESCENDING   =    2

  _Direction_NAMES = {
    1: "ASCENDING",
    2: "DESCENDING",
  }

  def Direction_Name(cls, x): return cls._Direction_NAMES.get(x, "")
  Direction_Name = classmethod(Direction_Name)

  has_property_ = 0
  property_ = ""
  has_direction_ = 0
  direction_ = 1

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def property(self): return self.property_

  def set_property(self, x):
    self.has_property_ = 1
    self.property_ = x

  def clear_property(self):
    if self.has_property_:
      self.has_property_ = 0
      self.property_ = ""

  def has_property(self): return self.has_property_

  def direction(self): return self.direction_

  def set_direction(self, x):
    self.has_direction_ = 1
    self.direction_ = x

  def clear_direction(self):
    if self.has_direction_:
      self.has_direction_ = 0
      self.direction_ = 1

  def has_direction(self): return self.has_direction_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_property()): self.set_property(x.property())
    if (x.has_direction()): self.set_direction(x.direction())

  def Equals(self, x):
    if x is self: return 1
    if self.has_property_ != x.has_property_: return 0
    if self.has_property_ and self.property_ != x.property_: return 0
    if self.has_direction_ != x.has_direction_: return 0
    if self.has_direction_ and self.direction_ != x.direction_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_property_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: property not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.property_))
    if (self.has_direction_): n += 1 + self.lengthVarInt64(self.direction_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_property_):
      n += 1
      n += self.lengthString(len(self.property_))
    if (self.has_direction_): n += 1 + self.lengthVarInt64(self.direction_)
    return n

  def Clear(self):
    self.clear_property()
    self.clear_direction()

  def OutputUnchecked(self, out):
    out.putVarInt32(82)
    out.putPrefixedString(self.property_)
    if (self.has_direction_):
      out.putVarInt32(88)
      out.putVarInt32(self.direction_)

  def OutputPartial(self, out):
    if (self.has_property_):
      out.putVarInt32(82)
      out.putPrefixedString(self.property_)
    if (self.has_direction_):
      out.putVarInt32(88)
      out.putVarInt32(self.direction_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 76: break
      if tt == 82:
        self.set_property(d.getPrefixedString())
        continue
      if tt == 88:
        self.set_direction(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_property_: res+=prefix+("property: %s\n" % self.DebugFormatString(self.property_))
    if self.has_direction_: res+=prefix+("direction: %s\n" % self.DebugFormatInt32(self.direction_))
    return res

class Query(ProtocolBuffer.ProtocolMessage):


  ORDER_FIRST  =    1
  ANCESTOR_FIRST =    2
  FILTER_FIRST =    3

  _Hint_NAMES = {
    1: "ORDER_FIRST",
    2: "ANCESTOR_FIRST",
    3: "FILTER_FIRST",
  }

  def Hint_Name(cls, x): return cls._Hint_NAMES.get(x, "")
  Hint_Name = classmethod(Hint_Name)

  has_app_ = 0
  app_ = ""
  has_database_id_ = 0
  database_id_ = ""
  has_name_space_ = 0
  name_space_ = ""
  has_kind_ = 0
  kind_ = ""
  has_ancestor_ = 0
  ancestor_ = None
  has_search_query_ = 0
  search_query_ = ""
  has_hint_ = 0
  hint_ = 0
  has_count_ = 0
  count_ = 0
  has_offset_ = 0
  offset_ = 0
  has_limit_ = 0
  limit_ = 0
  has_compiled_cursor_ = 0
  compiled_cursor_ = None
  has_end_compiled_cursor_ = 0
  end_compiled_cursor_ = None
  has_require_perfect_plan_ = 0
  require_perfect_plan_ = 0
  has_keys_only_ = 0
  keys_only_ = 0
  has_transaction_ = 0
  transaction_ = None
  has_compile_ = 0
  compile_ = 0
  has_failover_ms_ = 0
  failover_ms_ = 0
  has_strong_ = 0
  strong_ = 0
  has_distinct_ = 0
  distinct_ = 0
  has_min_safe_time_seconds_ = 0
  min_safe_time_seconds_ = 0
  has_persist_offset_ = 0
  persist_offset_ = 1

  def __init__(self, contents=None):
    self.filter_ = []
    self.order_ = []
    self.composite_index_ = []
    self.property_name_ = []
    self.group_by_property_name_ = []
    self.safe_replica_name_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def app(self): return self.app_

  def set_app(self, x):
    self.has_app_ = 1
    self.app_ = x

  def clear_app(self):
    if self.has_app_:
      self.has_app_ = 0
      self.app_ = ""

  def has_app(self): return self.has_app_

  def database_id(self): return self.database_id_

  def set_database_id(self, x):
    self.has_database_id_ = 1
    self.database_id_ = x

  def clear_database_id(self):
    if self.has_database_id_:
      self.has_database_id_ = 0
      self.database_id_ = ""

  def has_database_id(self): return self.has_database_id_

  def name_space(self): return self.name_space_

  def set_name_space(self, x):
    self.has_name_space_ = 1
    self.name_space_ = x

  def clear_name_space(self):
    if self.has_name_space_:
      self.has_name_space_ = 0
      self.name_space_ = ""

  def has_name_space(self): return self.has_name_space_

  def kind(self): return self.kind_

  def set_kind(self, x):
    self.has_kind_ = 1
    self.kind_ = x

  def clear_kind(self):
    if self.has_kind_:
      self.has_kind_ = 0
      self.kind_ = ""

  def has_kind(self): return self.has_kind_

  def ancestor(self):
    if self.ancestor_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.ancestor_ is None: self.ancestor_ = Reference()
      finally:
        self.lazy_init_lock_.release()
    return self.ancestor_

  def mutable_ancestor(self): self.has_ancestor_ = 1; return self.ancestor()

  def clear_ancestor(self):

    if self.has_ancestor_:
      self.has_ancestor_ = 0;
      if self.ancestor_ is not None: self.ancestor_.Clear()

  def has_ancestor(self): return self.has_ancestor_

  def filter_size(self): return len(self.filter_)
  def filter_list(self): return self.filter_

  def filter(self, i):
    return self.filter_[i]

  def mutable_filter(self, i):
    return self.filter_[i]

  def add_filter(self):
    x = Query_Filter()
    self.filter_.append(x)
    return x

  def clear_filter(self):
    self.filter_ = []
  def search_query(self): return self.search_query_

  def set_search_query(self, x):
    self.has_search_query_ = 1
    self.search_query_ = x

  def clear_search_query(self):
    if self.has_search_query_:
      self.has_search_query_ = 0
      self.search_query_ = ""

  def has_search_query(self): return self.has_search_query_

  def order_size(self): return len(self.order_)
  def order_list(self): return self.order_

  def order(self, i):
    return self.order_[i]

  def mutable_order(self, i):
    return self.order_[i]

  def add_order(self):
    x = Query_Order()
    self.order_.append(x)
    return x

  def clear_order(self):
    self.order_ = []
  def hint(self): return self.hint_

  def set_hint(self, x):
    self.has_hint_ = 1
    self.hint_ = x

  def clear_hint(self):
    if self.has_hint_:
      self.has_hint_ = 0
      self.hint_ = 0

  def has_hint(self): return self.has_hint_

  def count(self): return self.count_

  def set_count(self, x):
    self.has_count_ = 1
    self.count_ = x

  def clear_count(self):
    if self.has_count_:
      self.has_count_ = 0
      self.count_ = 0

  def has_count(self): return self.has_count_

  def offset(self): return self.offset_

  def set_offset(self, x):
    self.has_offset_ = 1
    self.offset_ = x

  def clear_offset(self):
    if self.has_offset_:
      self.has_offset_ = 0
      self.offset_ = 0

  def has_offset(self): return self.has_offset_

  def limit(self): return self.limit_

  def set_limit(self, x):
    self.has_limit_ = 1
    self.limit_ = x

  def clear_limit(self):
    if self.has_limit_:
      self.has_limit_ = 0
      self.limit_ = 0

  def has_limit(self): return self.has_limit_

  def compiled_cursor(self):
    if self.compiled_cursor_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.compiled_cursor_ is None: self.compiled_cursor_ = CompiledCursor()
      finally:
        self.lazy_init_lock_.release()
    return self.compiled_cursor_

  def mutable_compiled_cursor(self): self.has_compiled_cursor_ = 1; return self.compiled_cursor()

  def clear_compiled_cursor(self):

    if self.has_compiled_cursor_:
      self.has_compiled_cursor_ = 0;
      if self.compiled_cursor_ is not None: self.compiled_cursor_.Clear()

  def has_compiled_cursor(self): return self.has_compiled_cursor_

  def end_compiled_cursor(self):
    if self.end_compiled_cursor_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.end_compiled_cursor_ is None: self.end_compiled_cursor_ = CompiledCursor()
      finally:
        self.lazy_init_lock_.release()
    return self.end_compiled_cursor_

  def mutable_end_compiled_cursor(self): self.has_end_compiled_cursor_ = 1; return self.end_compiled_cursor()

  def clear_end_compiled_cursor(self):

    if self.has_end_compiled_cursor_:
      self.has_end_compiled_cursor_ = 0;
      if self.end_compiled_cursor_ is not None: self.end_compiled_cursor_.Clear()

  def has_end_compiled_cursor(self): return self.has_end_compiled_cursor_

  def composite_index_size(self): return len(self.composite_index_)
  def composite_index_list(self): return self.composite_index_

  def composite_index(self, i):
    return self.composite_index_[i]

  def mutable_composite_index(self, i):
    return self.composite_index_[i]

  def add_composite_index(self):
    x = CompositeIndex()
    self.composite_index_.append(x)
    return x

  def clear_composite_index(self):
    self.composite_index_ = []
  def require_perfect_plan(self): return self.require_perfect_plan_

  def set_require_perfect_plan(self, x):
    self.has_require_perfect_plan_ = 1
    self.require_perfect_plan_ = x

  def clear_require_perfect_plan(self):
    if self.has_require_perfect_plan_:
      self.has_require_perfect_plan_ = 0
      self.require_perfect_plan_ = 0

  def has_require_perfect_plan(self): return self.has_require_perfect_plan_

  def keys_only(self): return self.keys_only_

  def set_keys_only(self, x):
    self.has_keys_only_ = 1
    self.keys_only_ = x

  def clear_keys_only(self):
    if self.has_keys_only_:
      self.has_keys_only_ = 0
      self.keys_only_ = 0

  def has_keys_only(self): return self.has_keys_only_

  def transaction(self):
    if self.transaction_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.transaction_ is None: self.transaction_ = Transaction()
      finally:
        self.lazy_init_lock_.release()
    return self.transaction_

  def mutable_transaction(self): self.has_transaction_ = 1; return self.transaction()

  def clear_transaction(self):

    if self.has_transaction_:
      self.has_transaction_ = 0;
      if self.transaction_ is not None: self.transaction_.Clear()

  def has_transaction(self): return self.has_transaction_

  def compile(self): return self.compile_

  def set_compile(self, x):
    self.has_compile_ = 1
    self.compile_ = x

  def clear_compile(self):
    if self.has_compile_:
      self.has_compile_ = 0
      self.compile_ = 0

  def has_compile(self): return self.has_compile_

  def failover_ms(self): return self.failover_ms_

  def set_failover_ms(self, x):
    self.has_failover_ms_ = 1
    self.failover_ms_ = x

  def clear_failover_ms(self):
    if self.has_failover_ms_:
      self.has_failover_ms_ = 0
      self.failover_ms_ = 0

  def has_failover_ms(self): return self.has_failover_ms_

  def strong(self): return self.strong_

  def set_strong(self, x):
    self.has_strong_ = 1
    self.strong_ = x

  def clear_strong(self):
    if self.has_strong_:
      self.has_strong_ = 0
      self.strong_ = 0

  def has_strong(self): return self.has_strong_

  def property_name_size(self): return len(self.property_name_)
  def property_name_list(self): return self.property_name_

  def property_name(self, i):
    return self.property_name_[i]

  def set_property_name(self, i, x):
    self.property_name_[i] = x

  def add_property_name(self, x):
    self.property_name_.append(x)

  def clear_property_name(self):
    self.property_name_ = []

  def group_by_property_name_size(self): return len(self.group_by_property_name_)
  def group_by_property_name_list(self): return self.group_by_property_name_

  def group_by_property_name(self, i):
    return self.group_by_property_name_[i]

  def set_group_by_property_name(self, i, x):
    self.group_by_property_name_[i] = x

  def add_group_by_property_name(self, x):
    self.group_by_property_name_.append(x)

  def clear_group_by_property_name(self):
    self.group_by_property_name_ = []

  def distinct(self): return self.distinct_

  def set_distinct(self, x):
    self.has_distinct_ = 1
    self.distinct_ = x

  def clear_distinct(self):
    if self.has_distinct_:
      self.has_distinct_ = 0
      self.distinct_ = 0

  def has_distinct(self): return self.has_distinct_

  def min_safe_time_seconds(self): return self.min_safe_time_seconds_

  def set_min_safe_time_seconds(self, x):
    self.has_min_safe_time_seconds_ = 1
    self.min_safe_time_seconds_ = x

  def clear_min_safe_time_seconds(self):
    if self.has_min_safe_time_seconds_:
      self.has_min_safe_time_seconds_ = 0
      self.min_safe_time_seconds_ = 0

  def has_min_safe_time_seconds(self): return self.has_min_safe_time_seconds_

  def safe_replica_name_size(self): return len(self.safe_replica_name_)
  def safe_replica_name_list(self): return self.safe_replica_name_

  def safe_replica_name(self, i):
    return self.safe_replica_name_[i]

  def set_safe_replica_name(self, i, x):
    self.safe_replica_name_[i] = x

  def add_safe_replica_name(self, x):
    self.safe_replica_name_.append(x)

  def clear_safe_replica_name(self):
    self.safe_replica_name_ = []

  def persist_offset(self): return self.persist_offset_

  def set_persist_offset(self, x):
    self.has_persist_offset_ = 1
    self.persist_offset_ = x

  def clear_persist_offset(self):
    if self.has_persist_offset_:
      self.has_persist_offset_ = 0
      self.persist_offset_ = 1

  def has_persist_offset(self): return self.has_persist_offset_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app()): self.set_app(x.app())
    if (x.has_database_id()): self.set_database_id(x.database_id())
    if (x.has_name_space()): self.set_name_space(x.name_space())
    if (x.has_kind()): self.set_kind(x.kind())
    if (x.has_ancestor()): self.mutable_ancestor().MergeFrom(x.ancestor())
    for i in xrange(x.filter_size()): self.add_filter().CopyFrom(x.filter(i))
    if (x.has_search_query()): self.set_search_query(x.search_query())
    for i in xrange(x.order_size()): self.add_order().CopyFrom(x.order(i))
    if (x.has_hint()): self.set_hint(x.hint())
    if (x.has_count()): self.set_count(x.count())
    if (x.has_offset()): self.set_offset(x.offset())
    if (x.has_limit()): self.set_limit(x.limit())
    if (x.has_compiled_cursor()): self.mutable_compiled_cursor().MergeFrom(x.compiled_cursor())
    if (x.has_end_compiled_cursor()): self.mutable_end_compiled_cursor().MergeFrom(x.end_compiled_cursor())
    for i in xrange(x.composite_index_size()): self.add_composite_index().CopyFrom(x.composite_index(i))
    if (x.has_require_perfect_plan()): self.set_require_perfect_plan(x.require_perfect_plan())
    if (x.has_keys_only()): self.set_keys_only(x.keys_only())
    if (x.has_transaction()): self.mutable_transaction().MergeFrom(x.transaction())
    if (x.has_compile()): self.set_compile(x.compile())
    if (x.has_failover_ms()): self.set_failover_ms(x.failover_ms())
    if (x.has_strong()): self.set_strong(x.strong())
    for i in xrange(x.property_name_size()): self.add_property_name(x.property_name(i))
    for i in xrange(x.group_by_property_name_size()): self.add_group_by_property_name(x.group_by_property_name(i))
    if (x.has_distinct()): self.set_distinct(x.distinct())
    if (x.has_min_safe_time_seconds()): self.set_min_safe_time_seconds(x.min_safe_time_seconds())
    for i in xrange(x.safe_replica_name_size()): self.add_safe_replica_name(x.safe_replica_name(i))
    if (x.has_persist_offset()): self.set_persist_offset(x.persist_offset())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_ != x.has_app_: return 0
    if self.has_app_ and self.app_ != x.app_: return 0
    if self.has_database_id_ != x.has_database_id_: return 0
    if self.has_database_id_ and self.database_id_ != x.database_id_: return 0
    if self.has_name_space_ != x.has_name_space_: return 0
    if self.has_name_space_ and self.name_space_ != x.name_space_: return 0
    if self.has_kind_ != x.has_kind_: return 0
    if self.has_kind_ and self.kind_ != x.kind_: return 0
    if self.has_ancestor_ != x.has_ancestor_: return 0
    if self.has_ancestor_ and self.ancestor_ != x.ancestor_: return 0
    if len(self.filter_) != len(x.filter_): return 0
    for e1, e2 in zip(self.filter_, x.filter_):
      if e1 != e2: return 0
    if self.has_search_query_ != x.has_search_query_: return 0
    if self.has_search_query_ and self.search_query_ != x.search_query_: return 0
    if len(self.order_) != len(x.order_): return 0
    for e1, e2 in zip(self.order_, x.order_):
      if e1 != e2: return 0
    if self.has_hint_ != x.has_hint_: return 0
    if self.has_hint_ and self.hint_ != x.hint_: return 0
    if self.has_count_ != x.has_count_: return 0
    if self.has_count_ and self.count_ != x.count_: return 0
    if self.has_offset_ != x.has_offset_: return 0
    if self.has_offset_ and self.offset_ != x.offset_: return 0
    if self.has_limit_ != x.has_limit_: return 0
    if self.has_limit_ and self.limit_ != x.limit_: return 0
    if self.has_compiled_cursor_ != x.has_compiled_cursor_: return 0
    if self.has_compiled_cursor_ and self.compiled_cursor_ != x.compiled_cursor_: return 0
    if self.has_end_compiled_cursor_ != x.has_end_compiled_cursor_: return 0
    if self.has_end_compiled_cursor_ and self.end_compiled_cursor_ != x.end_compiled_cursor_: return 0
    if len(self.composite_index_) != len(x.composite_index_): return 0
    for e1, e2 in zip(self.composite_index_, x.composite_index_):
      if e1 != e2: return 0
    if self.has_require_perfect_plan_ != x.has_require_perfect_plan_: return 0
    if self.has_require_perfect_plan_ and self.require_perfect_plan_ != x.require_perfect_plan_: return 0
    if self.has_keys_only_ != x.has_keys_only_: return 0
    if self.has_keys_only_ and self.keys_only_ != x.keys_only_: return 0
    if self.has_transaction_ != x.has_transaction_: return 0
    if self.has_transaction_ and self.transaction_ != x.transaction_: return 0
    if self.has_compile_ != x.has_compile_: return 0
    if self.has_compile_ and self.compile_ != x.compile_: return 0
    if self.has_failover_ms_ != x.has_failover_ms_: return 0
    if self.has_failover_ms_ and self.failover_ms_ != x.failover_ms_: return 0
    if self.has_strong_ != x.has_strong_: return 0
    if self.has_strong_ and self.strong_ != x.strong_: return 0
    if len(self.property_name_) != len(x.property_name_): return 0
    for e1, e2 in zip(self.property_name_, x.property_name_):
      if e1 != e2: return 0
    if len(self.group_by_property_name_) != len(x.group_by_property_name_): return 0
    for e1, e2 in zip(self.group_by_property_name_, x.group_by_property_name_):
      if e1 != e2: return 0
    if self.has_distinct_ != x.has_distinct_: return 0
    if self.has_distinct_ and self.distinct_ != x.distinct_: return 0
    if self.has_min_safe_time_seconds_ != x.has_min_safe_time_seconds_: return 0
    if self.has_min_safe_time_seconds_ and self.min_safe_time_seconds_ != x.min_safe_time_seconds_: return 0
    if len(self.safe_replica_name_) != len(x.safe_replica_name_): return 0
    for e1, e2 in zip(self.safe_replica_name_, x.safe_replica_name_):
      if e1 != e2: return 0
    if self.has_persist_offset_ != x.has_persist_offset_: return 0
    if self.has_persist_offset_ and self.persist_offset_ != x.persist_offset_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_app_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: app not set.')
    if (self.has_ancestor_ and not self.ancestor_.IsInitialized(debug_strs)): initialized = 0
    for p in self.filter_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.order_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_compiled_cursor_ and not self.compiled_cursor_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_end_compiled_cursor_ and not self.end_compiled_cursor_.IsInitialized(debug_strs)): initialized = 0
    for p in self.composite_index_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_transaction_ and not self.transaction_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.app_))
    if (self.has_database_id_): n += 2 + self.lengthString(len(self.database_id_))
    if (self.has_name_space_): n += 2 + self.lengthString(len(self.name_space_))
    if (self.has_kind_): n += 1 + self.lengthString(len(self.kind_))
    if (self.has_ancestor_): n += 2 + self.lengthString(self.ancestor_.ByteSize())
    n += 2 * len(self.filter_)
    for i in xrange(len(self.filter_)): n += self.filter_[i].ByteSize()
    if (self.has_search_query_): n += 1 + self.lengthString(len(self.search_query_))
    n += 2 * len(self.order_)
    for i in xrange(len(self.order_)): n += self.order_[i].ByteSize()
    if (self.has_hint_): n += 2 + self.lengthVarInt64(self.hint_)
    if (self.has_count_): n += 2 + self.lengthVarInt64(self.count_)
    if (self.has_offset_): n += 1 + self.lengthVarInt64(self.offset_)
    if (self.has_limit_): n += 2 + self.lengthVarInt64(self.limit_)
    if (self.has_compiled_cursor_): n += 2 + self.lengthString(self.compiled_cursor_.ByteSize())
    if (self.has_end_compiled_cursor_): n += 2 + self.lengthString(self.end_compiled_cursor_.ByteSize())
    n += 2 * len(self.composite_index_)
    for i in xrange(len(self.composite_index_)): n += self.lengthString(self.composite_index_[i].ByteSize())
    if (self.has_require_perfect_plan_): n += 3
    if (self.has_keys_only_): n += 3
    if (self.has_transaction_): n += 2 + self.lengthString(self.transaction_.ByteSize())
    if (self.has_compile_): n += 3
    if (self.has_failover_ms_): n += 2 + self.lengthVarInt64(self.failover_ms_)
    if (self.has_strong_): n += 3
    n += 2 * len(self.property_name_)
    for i in xrange(len(self.property_name_)): n += self.lengthString(len(self.property_name_[i]))
    n += 2 * len(self.group_by_property_name_)
    for i in xrange(len(self.group_by_property_name_)): n += self.lengthString(len(self.group_by_property_name_[i]))
    if (self.has_distinct_): n += 3
    if (self.has_min_safe_time_seconds_): n += 2 + self.lengthVarInt64(self.min_safe_time_seconds_)
    n += 2 * len(self.safe_replica_name_)
    for i in xrange(len(self.safe_replica_name_)): n += self.lengthString(len(self.safe_replica_name_[i]))
    if (self.has_persist_offset_): n += 3
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_):
      n += 1
      n += self.lengthString(len(self.app_))
    if (self.has_database_id_): n += 2 + self.lengthString(len(self.database_id_))
    if (self.has_name_space_): n += 2 + self.lengthString(len(self.name_space_))
    if (self.has_kind_): n += 1 + self.lengthString(len(self.kind_))
    if (self.has_ancestor_): n += 2 + self.lengthString(self.ancestor_.ByteSizePartial())
    n += 2 * len(self.filter_)
    for i in xrange(len(self.filter_)): n += self.filter_[i].ByteSizePartial()
    if (self.has_search_query_): n += 1 + self.lengthString(len(self.search_query_))
    n += 2 * len(self.order_)
    for i in xrange(len(self.order_)): n += self.order_[i].ByteSizePartial()
    if (self.has_hint_): n += 2 + self.lengthVarInt64(self.hint_)
    if (self.has_count_): n += 2 + self.lengthVarInt64(self.count_)
    if (self.has_offset_): n += 1 + self.lengthVarInt64(self.offset_)
    if (self.has_limit_): n += 2 + self.lengthVarInt64(self.limit_)
    if (self.has_compiled_cursor_): n += 2 + self.lengthString(self.compiled_cursor_.ByteSizePartial())
    if (self.has_end_compiled_cursor_): n += 2 + self.lengthString(self.end_compiled_cursor_.ByteSizePartial())
    n += 2 * len(self.composite_index_)
    for i in xrange(len(self.composite_index_)): n += self.lengthString(self.composite_index_[i].ByteSizePartial())
    if (self.has_require_perfect_plan_): n += 3
    if (self.has_keys_only_): n += 3
    if (self.has_transaction_): n += 2 + self.lengthString(self.transaction_.ByteSizePartial())
    if (self.has_compile_): n += 3
    if (self.has_failover_ms_): n += 2 + self.lengthVarInt64(self.failover_ms_)
    if (self.has_strong_): n += 3
    n += 2 * len(self.property_name_)
    for i in xrange(len(self.property_name_)): n += self.lengthString(len(self.property_name_[i]))
    n += 2 * len(self.group_by_property_name_)
    for i in xrange(len(self.group_by_property_name_)): n += self.lengthString(len(self.group_by_property_name_[i]))
    if (self.has_distinct_): n += 3
    if (self.has_min_safe_time_seconds_): n += 2 + self.lengthVarInt64(self.min_safe_time_seconds_)
    n += 2 * len(self.safe_replica_name_)
    for i in xrange(len(self.safe_replica_name_)): n += self.lengthString(len(self.safe_replica_name_[i]))
    if (self.has_persist_offset_): n += 3
    return n

  def Clear(self):
    self.clear_app()
    self.clear_database_id()
    self.clear_name_space()
    self.clear_kind()
    self.clear_ancestor()
    self.clear_filter()
    self.clear_search_query()
    self.clear_order()
    self.clear_hint()
    self.clear_count()
    self.clear_offset()
    self.clear_limit()
    self.clear_compiled_cursor()
    self.clear_end_compiled_cursor()
    self.clear_composite_index()
    self.clear_require_perfect_plan()
    self.clear_keys_only()
    self.clear_transaction()
    self.clear_compile()
    self.clear_failover_ms()
    self.clear_strong()
    self.clear_property_name()
    self.clear_group_by_property_name()
    self.clear_distinct()
    self.clear_min_safe_time_seconds()
    self.clear_safe_replica_name()
    self.clear_persist_offset()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.app_)
    if (self.has_kind_):
      out.putVarInt32(26)
      out.putPrefixedString(self.kind_)
    for i in xrange(len(self.filter_)):
      out.putVarInt32(35)
      self.filter_[i].OutputUnchecked(out)
      out.putVarInt32(36)
    if (self.has_search_query_):
      out.putVarInt32(66)
      out.putPrefixedString(self.search_query_)
    for i in xrange(len(self.order_)):
      out.putVarInt32(75)
      self.order_[i].OutputUnchecked(out)
      out.putVarInt32(76)
    if (self.has_offset_):
      out.putVarInt32(96)
      out.putVarInt32(self.offset_)
    if (self.has_limit_):
      out.putVarInt32(128)
      out.putVarInt32(self.limit_)
    if (self.has_ancestor_):
      out.putVarInt32(138)
      out.putVarInt32(self.ancestor_.ByteSize())
      self.ancestor_.OutputUnchecked(out)
    if (self.has_hint_):
      out.putVarInt32(144)
      out.putVarInt32(self.hint_)
    for i in xrange(len(self.composite_index_)):
      out.putVarInt32(154)
      out.putVarInt32(self.composite_index_[i].ByteSize())
      self.composite_index_[i].OutputUnchecked(out)
    if (self.has_require_perfect_plan_):
      out.putVarInt32(160)
      out.putBoolean(self.require_perfect_plan_)
    if (self.has_keys_only_):
      out.putVarInt32(168)
      out.putBoolean(self.keys_only_)
    if (self.has_transaction_):
      out.putVarInt32(178)
      out.putVarInt32(self.transaction_.ByteSize())
      self.transaction_.OutputUnchecked(out)
    if (self.has_count_):
      out.putVarInt32(184)
      out.putVarInt32(self.count_)
    if (self.has_distinct_):
      out.putVarInt32(192)
      out.putBoolean(self.distinct_)
    if (self.has_compile_):
      out.putVarInt32(200)
      out.putBoolean(self.compile_)
    if (self.has_failover_ms_):
      out.putVarInt32(208)
      out.putVarInt64(self.failover_ms_)
    if (self.has_name_space_):
      out.putVarInt32(234)
      out.putPrefixedString(self.name_space_)
    if (self.has_compiled_cursor_):
      out.putVarInt32(242)
      out.putVarInt32(self.compiled_cursor_.ByteSize())
      self.compiled_cursor_.OutputUnchecked(out)
    if (self.has_end_compiled_cursor_):
      out.putVarInt32(250)
      out.putVarInt32(self.end_compiled_cursor_.ByteSize())
      self.end_compiled_cursor_.OutputUnchecked(out)
    if (self.has_strong_):
      out.putVarInt32(256)
      out.putBoolean(self.strong_)
    for i in xrange(len(self.property_name_)):
      out.putVarInt32(266)
      out.putPrefixedString(self.property_name_[i])
    for i in xrange(len(self.group_by_property_name_)):
      out.putVarInt32(274)
      out.putPrefixedString(self.group_by_property_name_[i])
    if (self.has_min_safe_time_seconds_):
      out.putVarInt32(280)
      out.putVarInt64(self.min_safe_time_seconds_)
    for i in xrange(len(self.safe_replica_name_)):
      out.putVarInt32(290)
      out.putPrefixedString(self.safe_replica_name_[i])
    if (self.has_persist_offset_):
      out.putVarInt32(296)
      out.putBoolean(self.persist_offset_)
    if (self.has_database_id_):
      out.putVarInt32(338)
      out.putPrefixedString(self.database_id_)

  def OutputPartial(self, out):
    if (self.has_app_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_)
    if (self.has_kind_):
      out.putVarInt32(26)
      out.putPrefixedString(self.kind_)
    for i in xrange(len(self.filter_)):
      out.putVarInt32(35)
      self.filter_[i].OutputPartial(out)
      out.putVarInt32(36)
    if (self.has_search_query_):
      out.putVarInt32(66)
      out.putPrefixedString(self.search_query_)
    for i in xrange(len(self.order_)):
      out.putVarInt32(75)
      self.order_[i].OutputPartial(out)
      out.putVarInt32(76)
    if (self.has_offset_):
      out.putVarInt32(96)
      out.putVarInt32(self.offset_)
    if (self.has_limit_):
      out.putVarInt32(128)
      out.putVarInt32(self.limit_)
    if (self.has_ancestor_):
      out.putVarInt32(138)
      out.putVarInt32(self.ancestor_.ByteSizePartial())
      self.ancestor_.OutputPartial(out)
    if (self.has_hint_):
      out.putVarInt32(144)
      out.putVarInt32(self.hint_)
    for i in xrange(len(self.composite_index_)):
      out.putVarInt32(154)
      out.putVarInt32(self.composite_index_[i].ByteSizePartial())
      self.composite_index_[i].OutputPartial(out)
    if (self.has_require_perfect_plan_):
      out.putVarInt32(160)
      out.putBoolean(self.require_perfect_plan_)
    if (self.has_keys_only_):
      out.putVarInt32(168)
      out.putBoolean(self.keys_only_)
    if (self.has_transaction_):
      out.putVarInt32(178)
      out.putVarInt32(self.transaction_.ByteSizePartial())
      self.transaction_.OutputPartial(out)
    if (self.has_count_):
      out.putVarInt32(184)
      out.putVarInt32(self.count_)
    if (self.has_distinct_):
      out.putVarInt32(192)
      out.putBoolean(self.distinct_)
    if (self.has_compile_):
      out.putVarInt32(200)
      out.putBoolean(self.compile_)
    if (self.has_failover_ms_):
      out.putVarInt32(208)
      out.putVarInt64(self.failover_ms_)
    if (self.has_name_space_):
      out.putVarInt32(234)
      out.putPrefixedString(self.name_space_)
    if (self.has_compiled_cursor_):
      out.putVarInt32(242)
      out.putVarInt32(self.compiled_cursor_.ByteSizePartial())
      self.compiled_cursor_.OutputPartial(out)
    if (self.has_end_compiled_cursor_):
      out.putVarInt32(250)
      out.putVarInt32(self.end_compiled_cursor_.ByteSizePartial())
      self.end_compiled_cursor_.OutputPartial(out)
    if (self.has_strong_):
      out.putVarInt32(256)
      out.putBoolean(self.strong_)
    for i in xrange(len(self.property_name_)):
      out.putVarInt32(266)
      out.putPrefixedString(self.property_name_[i])
    for i in xrange(len(self.group_by_property_name_)):
      out.putVarInt32(274)
      out.putPrefixedString(self.group_by_property_name_[i])
    if (self.has_min_safe_time_seconds_):
      out.putVarInt32(280)
      out.putVarInt64(self.min_safe_time_seconds_)
    for i in xrange(len(self.safe_replica_name_)):
      out.putVarInt32(290)
      out.putPrefixedString(self.safe_replica_name_[i])
    if (self.has_persist_offset_):
      out.putVarInt32(296)
      out.putBoolean(self.persist_offset_)
    if (self.has_database_id_):
      out.putVarInt32(338)
      out.putPrefixedString(self.database_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_kind(d.getPrefixedString())
        continue
      if tt == 35:
        self.add_filter().TryMerge(d)
        continue
      if tt == 66:
        self.set_search_query(d.getPrefixedString())
        continue
      if tt == 75:
        self.add_order().TryMerge(d)
        continue
      if tt == 96:
        self.set_offset(d.getVarInt32())
        continue
      if tt == 128:
        self.set_limit(d.getVarInt32())
        continue
      if tt == 138:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_ancestor().TryMerge(tmp)
        continue
      if tt == 144:
        self.set_hint(d.getVarInt32())
        continue
      if tt == 154:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_composite_index().TryMerge(tmp)
        continue
      if tt == 160:
        self.set_require_perfect_plan(d.getBoolean())
        continue
      if tt == 168:
        self.set_keys_only(d.getBoolean())
        continue
      if tt == 178:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_transaction().TryMerge(tmp)
        continue
      if tt == 184:
        self.set_count(d.getVarInt32())
        continue
      if tt == 192:
        self.set_distinct(d.getBoolean())
        continue
      if tt == 200:
        self.set_compile(d.getBoolean())
        continue
      if tt == 208:
        self.set_failover_ms(d.getVarInt64())
        continue
      if tt == 234:
        self.set_name_space(d.getPrefixedString())
        continue
      if tt == 242:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_compiled_cursor().TryMerge(tmp)
        continue
      if tt == 250:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_end_compiled_cursor().TryMerge(tmp)
        continue
      if tt == 256:
        self.set_strong(d.getBoolean())
        continue
      if tt == 266:
        self.add_property_name(d.getPrefixedString())
        continue
      if tt == 274:
        self.add_group_by_property_name(d.getPrefixedString())
        continue
      if tt == 280:
        self.set_min_safe_time_seconds(d.getVarInt64())
        continue
      if tt == 290:
        self.add_safe_replica_name(d.getPrefixedString())
        continue
      if tt == 296:
        self.set_persist_offset(d.getBoolean())
        continue
      if tt == 338:
        self.set_database_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_: res+=prefix+("app: %s\n" % self.DebugFormatString(self.app_))
    if self.has_database_id_: res+=prefix+("database_id: %s\n" % self.DebugFormatString(self.database_id_))
    if self.has_name_space_: res+=prefix+("name_space: %s\n" % self.DebugFormatString(self.name_space_))
    if self.has_kind_: res+=prefix+("kind: %s\n" % self.DebugFormatString(self.kind_))
    if self.has_ancestor_:
      res+=prefix+"ancestor <\n"
      res+=self.ancestor_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.filter_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Filter%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    if self.has_search_query_: res+=prefix+("search_query: %s\n" % self.DebugFormatString(self.search_query_))
    cnt=0
    for e in self.order_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Order%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    if self.has_hint_: res+=prefix+("hint: %s\n" % self.DebugFormatInt32(self.hint_))
    if self.has_count_: res+=prefix+("count: %s\n" % self.DebugFormatInt32(self.count_))
    if self.has_offset_: res+=prefix+("offset: %s\n" % self.DebugFormatInt32(self.offset_))
    if self.has_limit_: res+=prefix+("limit: %s\n" % self.DebugFormatInt32(self.limit_))
    if self.has_compiled_cursor_:
      res+=prefix+"compiled_cursor <\n"
      res+=self.compiled_cursor_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_end_compiled_cursor_:
      res+=prefix+"end_compiled_cursor <\n"
      res+=self.end_compiled_cursor_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.composite_index_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("composite_index%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_require_perfect_plan_: res+=prefix+("require_perfect_plan: %s\n" % self.DebugFormatBool(self.require_perfect_plan_))
    if self.has_keys_only_: res+=prefix+("keys_only: %s\n" % self.DebugFormatBool(self.keys_only_))
    if self.has_transaction_:
      res+=prefix+"transaction <\n"
      res+=self.transaction_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_compile_: res+=prefix+("compile: %s\n" % self.DebugFormatBool(self.compile_))
    if self.has_failover_ms_: res+=prefix+("failover_ms: %s\n" % self.DebugFormatInt64(self.failover_ms_))
    if self.has_strong_: res+=prefix+("strong: %s\n" % self.DebugFormatBool(self.strong_))
    cnt=0
    for e in self.property_name_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("property_name%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    cnt=0
    for e in self.group_by_property_name_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("group_by_property_name%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_distinct_: res+=prefix+("distinct: %s\n" % self.DebugFormatBool(self.distinct_))
    if self.has_min_safe_time_seconds_: res+=prefix+("min_safe_time_seconds: %s\n" % self.DebugFormatInt64(self.min_safe_time_seconds_))
    cnt=0
    for e in self.safe_replica_name_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("safe_replica_name%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_persist_offset_: res+=prefix+("persist_offset: %s\n" % self.DebugFormatBool(self.persist_offset_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp = 1
  kdatabase_id = 42
  kname_space = 29
  kkind = 3
  kancestor = 17
  kFilterGroup = 4
  kFilterop = 6
  kFilterproperty = 14
  kFiltergeo_region = 40
  ksearch_query = 8
  kOrderGroup = 9
  kOrderproperty = 10
  kOrderdirection = 11
  khint = 18
  kcount = 23
  koffset = 12
  klimit = 16
  kcompiled_cursor = 30
  kend_compiled_cursor = 31
  kcomposite_index = 19
  krequire_perfect_plan = 20
  kkeys_only = 21
  ktransaction = 22
  kcompile = 25
  kfailover_ms = 26
  kstrong = 32
  kproperty_name = 33
  kgroup_by_property_name = 34
  kdistinct = 24
  kmin_safe_time_seconds = 35
  ksafe_replica_name = 36
  kpersist_offset = 37

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app",
    3: "kind",
    4: "Filter",
    6: "op",
    8: "search_query",
    9: "Order",
    10: "property",
    11: "direction",
    12: "offset",
    14: "property",
    16: "limit",
    17: "ancestor",
    18: "hint",
    19: "composite_index",
    20: "require_perfect_plan",
    21: "keys_only",
    22: "transaction",
    23: "count",
    24: "distinct",
    25: "compile",
    26: "failover_ms",
    29: "name_space",
    30: "compiled_cursor",
    31: "end_compiled_cursor",
    32: "strong",
    33: "property_name",
    34: "group_by_property_name",
    35: "min_safe_time_seconds",
    36: "safe_replica_name",
    37: "persist_offset",
    40: "geo_region",
    42: "database_id",
  }, 42)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STARTGROUP,
    6: ProtocolBuffer.Encoder.NUMERIC,
    8: ProtocolBuffer.Encoder.STRING,
    9: ProtocolBuffer.Encoder.STARTGROUP,
    10: ProtocolBuffer.Encoder.STRING,
    11: ProtocolBuffer.Encoder.NUMERIC,
    12: ProtocolBuffer.Encoder.NUMERIC,
    14: ProtocolBuffer.Encoder.STRING,
    16: ProtocolBuffer.Encoder.NUMERIC,
    17: ProtocolBuffer.Encoder.STRING,
    18: ProtocolBuffer.Encoder.NUMERIC,
    19: ProtocolBuffer.Encoder.STRING,
    20: ProtocolBuffer.Encoder.NUMERIC,
    21: ProtocolBuffer.Encoder.NUMERIC,
    22: ProtocolBuffer.Encoder.STRING,
    23: ProtocolBuffer.Encoder.NUMERIC,
    24: ProtocolBuffer.Encoder.NUMERIC,
    25: ProtocolBuffer.Encoder.NUMERIC,
    26: ProtocolBuffer.Encoder.NUMERIC,
    29: ProtocolBuffer.Encoder.STRING,
    30: ProtocolBuffer.Encoder.STRING,
    31: ProtocolBuffer.Encoder.STRING,
    32: ProtocolBuffer.Encoder.NUMERIC,
    33: ProtocolBuffer.Encoder.STRING,
    34: ProtocolBuffer.Encoder.STRING,
    35: ProtocolBuffer.Encoder.NUMERIC,
    36: ProtocolBuffer.Encoder.STRING,
    37: ProtocolBuffer.Encoder.NUMERIC,
    40: ProtocolBuffer.Encoder.STRING,
    42: ProtocolBuffer.Encoder.STRING,
  }, 42, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.Query'
class RegionPoint(ProtocolBuffer.ProtocolMessage):
  has_latitude_ = 0
  latitude_ = 0.0
  has_longitude_ = 0
  longitude_ = 0.0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def latitude(self): return self.latitude_

  def set_latitude(self, x):
    self.has_latitude_ = 1
    self.latitude_ = x

  def clear_latitude(self):
    if self.has_latitude_:
      self.has_latitude_ = 0
      self.latitude_ = 0.0

  def has_latitude(self): return self.has_latitude_

  def longitude(self): return self.longitude_

  def set_longitude(self, x):
    self.has_longitude_ = 1
    self.longitude_ = x

  def clear_longitude(self):
    if self.has_longitude_:
      self.has_longitude_ = 0
      self.longitude_ = 0.0

  def has_longitude(self): return self.has_longitude_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_latitude()): self.set_latitude(x.latitude())
    if (x.has_longitude()): self.set_longitude(x.longitude())

  def Equals(self, x):
    if x is self: return 1
    if self.has_latitude_ != x.has_latitude_: return 0
    if self.has_latitude_ and self.latitude_ != x.latitude_: return 0
    if self.has_longitude_ != x.has_longitude_: return 0
    if self.has_longitude_ and self.longitude_ != x.longitude_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_latitude_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: latitude not set.')
    if (not self.has_longitude_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: longitude not set.')
    return initialized

  def ByteSize(self):
    n = 0
    return n + 18

  def ByteSizePartial(self):
    n = 0
    if (self.has_latitude_):
      n += 9
    if (self.has_longitude_):
      n += 9
    return n

  def Clear(self):
    self.clear_latitude()
    self.clear_longitude()

  def OutputUnchecked(self, out):
    out.putVarInt32(9)
    out.putDouble(self.latitude_)
    out.putVarInt32(17)
    out.putDouble(self.longitude_)

  def OutputPartial(self, out):
    if (self.has_latitude_):
      out.putVarInt32(9)
      out.putDouble(self.latitude_)
    if (self.has_longitude_):
      out.putVarInt32(17)
      out.putDouble(self.longitude_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 9:
        self.set_latitude(d.getDouble())
        continue
      if tt == 17:
        self.set_longitude(d.getDouble())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_latitude_: res+=prefix+("latitude: %s\n" % self.DebugFormat(self.latitude_))
    if self.has_longitude_: res+=prefix+("longitude: %s\n" % self.DebugFormat(self.longitude_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  klatitude = 1
  klongitude = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "latitude",
    2: "longitude",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.DOUBLE,
    2: ProtocolBuffer.Encoder.DOUBLE,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.RegionPoint'
class CircleRegion(ProtocolBuffer.ProtocolMessage):
  has_center_ = 0
  has_radius_meters_ = 0
  radius_meters_ = 0.0

  def __init__(self, contents=None):
    self.center_ = RegionPoint()
    if contents is not None: self.MergeFromString(contents)

  def center(self): return self.center_

  def mutable_center(self): self.has_center_ = 1; return self.center_

  def clear_center(self):self.has_center_ = 0; self.center_.Clear()

  def has_center(self): return self.has_center_

  def radius_meters(self): return self.radius_meters_

  def set_radius_meters(self, x):
    self.has_radius_meters_ = 1
    self.radius_meters_ = x

  def clear_radius_meters(self):
    if self.has_radius_meters_:
      self.has_radius_meters_ = 0
      self.radius_meters_ = 0.0

  def has_radius_meters(self): return self.has_radius_meters_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_center()): self.mutable_center().MergeFrom(x.center())
    if (x.has_radius_meters()): self.set_radius_meters(x.radius_meters())

  def Equals(self, x):
    if x is self: return 1
    if self.has_center_ != x.has_center_: return 0
    if self.has_center_ and self.center_ != x.center_: return 0
    if self.has_radius_meters_ != x.has_radius_meters_: return 0
    if self.has_radius_meters_ and self.radius_meters_ != x.radius_meters_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_center_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: center not set.')
    elif not self.center_.IsInitialized(debug_strs): initialized = 0
    if (not self.has_radius_meters_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: radius_meters not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.center_.ByteSize())
    return n + 10

  def ByteSizePartial(self):
    n = 0
    if (self.has_center_):
      n += 1
      n += self.lengthString(self.center_.ByteSizePartial())
    if (self.has_radius_meters_):
      n += 9
    return n

  def Clear(self):
    self.clear_center()
    self.clear_radius_meters()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.center_.ByteSize())
    self.center_.OutputUnchecked(out)
    out.putVarInt32(17)
    out.putDouble(self.radius_meters_)

  def OutputPartial(self, out):
    if (self.has_center_):
      out.putVarInt32(10)
      out.putVarInt32(self.center_.ByteSizePartial())
      self.center_.OutputPartial(out)
    if (self.has_radius_meters_):
      out.putVarInt32(17)
      out.putDouble(self.radius_meters_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_center().TryMerge(tmp)
        continue
      if tt == 17:
        self.set_radius_meters(d.getDouble())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_center_:
      res+=prefix+"center <\n"
      res+=self.center_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_radius_meters_: res+=prefix+("radius_meters: %s\n" % self.DebugFormat(self.radius_meters_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kcenter = 1
  kradius_meters = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "center",
    2: "radius_meters",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.DOUBLE,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.CircleRegion'
class RectangleRegion(ProtocolBuffer.ProtocolMessage):
  has_southwest_ = 0
  has_northeast_ = 0

  def __init__(self, contents=None):
    self.southwest_ = RegionPoint()
    self.northeast_ = RegionPoint()
    if contents is not None: self.MergeFromString(contents)

  def southwest(self): return self.southwest_

  def mutable_southwest(self): self.has_southwest_ = 1; return self.southwest_

  def clear_southwest(self):self.has_southwest_ = 0; self.southwest_.Clear()

  def has_southwest(self): return self.has_southwest_

  def northeast(self): return self.northeast_

  def mutable_northeast(self): self.has_northeast_ = 1; return self.northeast_

  def clear_northeast(self):self.has_northeast_ = 0; self.northeast_.Clear()

  def has_northeast(self): return self.has_northeast_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_southwest()): self.mutable_southwest().MergeFrom(x.southwest())
    if (x.has_northeast()): self.mutable_northeast().MergeFrom(x.northeast())

  def Equals(self, x):
    if x is self: return 1
    if self.has_southwest_ != x.has_southwest_: return 0
    if self.has_southwest_ and self.southwest_ != x.southwest_: return 0
    if self.has_northeast_ != x.has_northeast_: return 0
    if self.has_northeast_ and self.northeast_ != x.northeast_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_southwest_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: southwest not set.')
    elif not self.southwest_.IsInitialized(debug_strs): initialized = 0
    if (not self.has_northeast_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: northeast not set.')
    elif not self.northeast_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.southwest_.ByteSize())
    n += self.lengthString(self.northeast_.ByteSize())
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_southwest_):
      n += 1
      n += self.lengthString(self.southwest_.ByteSizePartial())
    if (self.has_northeast_):
      n += 1
      n += self.lengthString(self.northeast_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_southwest()
    self.clear_northeast()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.southwest_.ByteSize())
    self.southwest_.OutputUnchecked(out)
    out.putVarInt32(18)
    out.putVarInt32(self.northeast_.ByteSize())
    self.northeast_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_southwest_):
      out.putVarInt32(10)
      out.putVarInt32(self.southwest_.ByteSizePartial())
      self.southwest_.OutputPartial(out)
    if (self.has_northeast_):
      out.putVarInt32(18)
      out.putVarInt32(self.northeast_.ByteSizePartial())
      self.northeast_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_southwest().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_northeast().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_southwest_:
      res+=prefix+"southwest <\n"
      res+=self.southwest_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_northeast_:
      res+=prefix+"northeast <\n"
      res+=self.northeast_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksouthwest = 1
  knortheast = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "southwest",
    2: "northeast",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.RectangleRegion'
class GeoRegion(ProtocolBuffer.ProtocolMessage):
  has_circle_ = 0
  circle_ = None
  has_rectangle_ = 0
  rectangle_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def circle(self):
    if self.circle_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.circle_ is None: self.circle_ = CircleRegion()
      finally:
        self.lazy_init_lock_.release()
    return self.circle_

  def mutable_circle(self): self.has_circle_ = 1; return self.circle()

  def clear_circle(self):

    if self.has_circle_:
      self.has_circle_ = 0;
      if self.circle_ is not None: self.circle_.Clear()

  def has_circle(self): return self.has_circle_

  def rectangle(self):
    if self.rectangle_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.rectangle_ is None: self.rectangle_ = RectangleRegion()
      finally:
        self.lazy_init_lock_.release()
    return self.rectangle_

  def mutable_rectangle(self): self.has_rectangle_ = 1; return self.rectangle()

  def clear_rectangle(self):

    if self.has_rectangle_:
      self.has_rectangle_ = 0;
      if self.rectangle_ is not None: self.rectangle_.Clear()

  def has_rectangle(self): return self.has_rectangle_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_circle()): self.mutable_circle().MergeFrom(x.circle())
    if (x.has_rectangle()): self.mutable_rectangle().MergeFrom(x.rectangle())

  def Equals(self, x):
    if x is self: return 1
    if self.has_circle_ != x.has_circle_: return 0
    if self.has_circle_ and self.circle_ != x.circle_: return 0
    if self.has_rectangle_ != x.has_rectangle_: return 0
    if self.has_rectangle_ and self.rectangle_ != x.rectangle_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_circle_ and not self.circle_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_rectangle_ and not self.rectangle_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_circle_): n += 1 + self.lengthString(self.circle_.ByteSize())
    if (self.has_rectangle_): n += 1 + self.lengthString(self.rectangle_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_circle_): n += 1 + self.lengthString(self.circle_.ByteSizePartial())
    if (self.has_rectangle_): n += 1 + self.lengthString(self.rectangle_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_circle()
    self.clear_rectangle()

  def OutputUnchecked(self, out):
    if (self.has_circle_):
      out.putVarInt32(10)
      out.putVarInt32(self.circle_.ByteSize())
      self.circle_.OutputUnchecked(out)
    if (self.has_rectangle_):
      out.putVarInt32(18)
      out.putVarInt32(self.rectangle_.ByteSize())
      self.rectangle_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_circle_):
      out.putVarInt32(10)
      out.putVarInt32(self.circle_.ByteSizePartial())
      self.circle_.OutputPartial(out)
    if (self.has_rectangle_):
      out.putVarInt32(18)
      out.putVarInt32(self.rectangle_.ByteSizePartial())
      self.rectangle_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_circle().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_rectangle().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_circle_:
      res+=prefix+"circle <\n"
      res+=self.circle_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_rectangle_:
      res+=prefix+"rectangle <\n"
      res+=self.rectangle_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kcircle = 1
  krectangle = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "circle",
    2: "rectangle",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.GeoRegion'
class CompiledQuery_PrimaryScan(ProtocolBuffer.ProtocolMessage):
  has_index_name_ = 0
  index_name_ = ""
  has_start_key_ = 0
  start_key_ = ""
  has_start_inclusive_ = 0
  start_inclusive_ = 0
  has_end_key_ = 0
  end_key_ = ""
  has_end_inclusive_ = 0
  end_inclusive_ = 0
  has_end_unapplied_log_timestamp_us_ = 0
  end_unapplied_log_timestamp_us_ = 0

  def __init__(self, contents=None):
    self.start_postfix_value_ = []
    self.end_postfix_value_ = []
    if contents is not None: self.MergeFromString(contents)

  def index_name(self): return self.index_name_

  def set_index_name(self, x):
    self.has_index_name_ = 1
    self.index_name_ = x

  def clear_index_name(self):
    if self.has_index_name_:
      self.has_index_name_ = 0
      self.index_name_ = ""

  def has_index_name(self): return self.has_index_name_

  def start_key(self): return self.start_key_

  def set_start_key(self, x):
    self.has_start_key_ = 1
    self.start_key_ = x

  def clear_start_key(self):
    if self.has_start_key_:
      self.has_start_key_ = 0
      self.start_key_ = ""

  def has_start_key(self): return self.has_start_key_

  def start_inclusive(self): return self.start_inclusive_

  def set_start_inclusive(self, x):
    self.has_start_inclusive_ = 1
    self.start_inclusive_ = x

  def clear_start_inclusive(self):
    if self.has_start_inclusive_:
      self.has_start_inclusive_ = 0
      self.start_inclusive_ = 0

  def has_start_inclusive(self): return self.has_start_inclusive_

  def end_key(self): return self.end_key_

  def set_end_key(self, x):
    self.has_end_key_ = 1
    self.end_key_ = x

  def clear_end_key(self):
    if self.has_end_key_:
      self.has_end_key_ = 0
      self.end_key_ = ""

  def has_end_key(self): return self.has_end_key_

  def end_inclusive(self): return self.end_inclusive_

  def set_end_inclusive(self, x):
    self.has_end_inclusive_ = 1
    self.end_inclusive_ = x

  def clear_end_inclusive(self):
    if self.has_end_inclusive_:
      self.has_end_inclusive_ = 0
      self.end_inclusive_ = 0

  def has_end_inclusive(self): return self.has_end_inclusive_

  def start_postfix_value_size(self): return len(self.start_postfix_value_)
  def start_postfix_value_list(self): return self.start_postfix_value_

  def start_postfix_value(self, i):
    return self.start_postfix_value_[i]

  def set_start_postfix_value(self, i, x):
    self.start_postfix_value_[i] = x

  def add_start_postfix_value(self, x):
    self.start_postfix_value_.append(x)

  def clear_start_postfix_value(self):
    self.start_postfix_value_ = []

  def end_postfix_value_size(self): return len(self.end_postfix_value_)
  def end_postfix_value_list(self): return self.end_postfix_value_

  def end_postfix_value(self, i):
    return self.end_postfix_value_[i]

  def set_end_postfix_value(self, i, x):
    self.end_postfix_value_[i] = x

  def add_end_postfix_value(self, x):
    self.end_postfix_value_.append(x)

  def clear_end_postfix_value(self):
    self.end_postfix_value_ = []

  def end_unapplied_log_timestamp_us(self): return self.end_unapplied_log_timestamp_us_

  def set_end_unapplied_log_timestamp_us(self, x):
    self.has_end_unapplied_log_timestamp_us_ = 1
    self.end_unapplied_log_timestamp_us_ = x

  def clear_end_unapplied_log_timestamp_us(self):
    if self.has_end_unapplied_log_timestamp_us_:
      self.has_end_unapplied_log_timestamp_us_ = 0
      self.end_unapplied_log_timestamp_us_ = 0

  def has_end_unapplied_log_timestamp_us(self): return self.has_end_unapplied_log_timestamp_us_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_index_name()): self.set_index_name(x.index_name())
    if (x.has_start_key()): self.set_start_key(x.start_key())
    if (x.has_start_inclusive()): self.set_start_inclusive(x.start_inclusive())
    if (x.has_end_key()): self.set_end_key(x.end_key())
    if (x.has_end_inclusive()): self.set_end_inclusive(x.end_inclusive())
    for i in xrange(x.start_postfix_value_size()): self.add_start_postfix_value(x.start_postfix_value(i))
    for i in xrange(x.end_postfix_value_size()): self.add_end_postfix_value(x.end_postfix_value(i))
    if (x.has_end_unapplied_log_timestamp_us()): self.set_end_unapplied_log_timestamp_us(x.end_unapplied_log_timestamp_us())

  def Equals(self, x):
    if x is self: return 1
    if self.has_index_name_ != x.has_index_name_: return 0
    if self.has_index_name_ and self.index_name_ != x.index_name_: return 0
    if self.has_start_key_ != x.has_start_key_: return 0
    if self.has_start_key_ and self.start_key_ != x.start_key_: return 0
    if self.has_start_inclusive_ != x.has_start_inclusive_: return 0
    if self.has_start_inclusive_ and self.start_inclusive_ != x.start_inclusive_: return 0
    if self.has_end_key_ != x.has_end_key_: return 0
    if self.has_end_key_ and self.end_key_ != x.end_key_: return 0
    if self.has_end_inclusive_ != x.has_end_inclusive_: return 0
    if self.has_end_inclusive_ and self.end_inclusive_ != x.end_inclusive_: return 0
    if len(self.start_postfix_value_) != len(x.start_postfix_value_): return 0
    for e1, e2 in zip(self.start_postfix_value_, x.start_postfix_value_):
      if e1 != e2: return 0
    if len(self.end_postfix_value_) != len(x.end_postfix_value_): return 0
    for e1, e2 in zip(self.end_postfix_value_, x.end_postfix_value_):
      if e1 != e2: return 0
    if self.has_end_unapplied_log_timestamp_us_ != x.has_end_unapplied_log_timestamp_us_: return 0
    if self.has_end_unapplied_log_timestamp_us_ and self.end_unapplied_log_timestamp_us_ != x.end_unapplied_log_timestamp_us_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_index_name_): n += 1 + self.lengthString(len(self.index_name_))
    if (self.has_start_key_): n += 1 + self.lengthString(len(self.start_key_))
    if (self.has_start_inclusive_): n += 2
    if (self.has_end_key_): n += 1 + self.lengthString(len(self.end_key_))
    if (self.has_end_inclusive_): n += 2
    n += 2 * len(self.start_postfix_value_)
    for i in xrange(len(self.start_postfix_value_)): n += self.lengthString(len(self.start_postfix_value_[i]))
    n += 2 * len(self.end_postfix_value_)
    for i in xrange(len(self.end_postfix_value_)): n += self.lengthString(len(self.end_postfix_value_[i]))
    if (self.has_end_unapplied_log_timestamp_us_): n += 2 + self.lengthVarInt64(self.end_unapplied_log_timestamp_us_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_index_name_): n += 1 + self.lengthString(len(self.index_name_))
    if (self.has_start_key_): n += 1 + self.lengthString(len(self.start_key_))
    if (self.has_start_inclusive_): n += 2
    if (self.has_end_key_): n += 1 + self.lengthString(len(self.end_key_))
    if (self.has_end_inclusive_): n += 2
    n += 2 * len(self.start_postfix_value_)
    for i in xrange(len(self.start_postfix_value_)): n += self.lengthString(len(self.start_postfix_value_[i]))
    n += 2 * len(self.end_postfix_value_)
    for i in xrange(len(self.end_postfix_value_)): n += self.lengthString(len(self.end_postfix_value_[i]))
    if (self.has_end_unapplied_log_timestamp_us_): n += 2 + self.lengthVarInt64(self.end_unapplied_log_timestamp_us_)
    return n

  def Clear(self):
    self.clear_index_name()
    self.clear_start_key()
    self.clear_start_inclusive()
    self.clear_end_key()
    self.clear_end_inclusive()
    self.clear_start_postfix_value()
    self.clear_end_postfix_value()
    self.clear_end_unapplied_log_timestamp_us()

  def OutputUnchecked(self, out):
    if (self.has_index_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.index_name_)
    if (self.has_start_key_):
      out.putVarInt32(26)
      out.putPrefixedString(self.start_key_)
    if (self.has_start_inclusive_):
      out.putVarInt32(32)
      out.putBoolean(self.start_inclusive_)
    if (self.has_end_key_):
      out.putVarInt32(42)
      out.putPrefixedString(self.end_key_)
    if (self.has_end_inclusive_):
      out.putVarInt32(48)
      out.putBoolean(self.end_inclusive_)
    if (self.has_end_unapplied_log_timestamp_us_):
      out.putVarInt32(152)
      out.putVarInt64(self.end_unapplied_log_timestamp_us_)
    for i in xrange(len(self.start_postfix_value_)):
      out.putVarInt32(178)
      out.putPrefixedString(self.start_postfix_value_[i])
    for i in xrange(len(self.end_postfix_value_)):
      out.putVarInt32(186)
      out.putPrefixedString(self.end_postfix_value_[i])

  def OutputPartial(self, out):
    if (self.has_index_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.index_name_)
    if (self.has_start_key_):
      out.putVarInt32(26)
      out.putPrefixedString(self.start_key_)
    if (self.has_start_inclusive_):
      out.putVarInt32(32)
      out.putBoolean(self.start_inclusive_)
    if (self.has_end_key_):
      out.putVarInt32(42)
      out.putPrefixedString(self.end_key_)
    if (self.has_end_inclusive_):
      out.putVarInt32(48)
      out.putBoolean(self.end_inclusive_)
    if (self.has_end_unapplied_log_timestamp_us_):
      out.putVarInt32(152)
      out.putVarInt64(self.end_unapplied_log_timestamp_us_)
    for i in xrange(len(self.start_postfix_value_)):
      out.putVarInt32(178)
      out.putPrefixedString(self.start_postfix_value_[i])
    for i in xrange(len(self.end_postfix_value_)):
      out.putVarInt32(186)
      out.putPrefixedString(self.end_postfix_value_[i])

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 12: break
      if tt == 18:
        self.set_index_name(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_start_key(d.getPrefixedString())
        continue
      if tt == 32:
        self.set_start_inclusive(d.getBoolean())
        continue
      if tt == 42:
        self.set_end_key(d.getPrefixedString())
        continue
      if tt == 48:
        self.set_end_inclusive(d.getBoolean())
        continue
      if tt == 152:
        self.set_end_unapplied_log_timestamp_us(d.getVarInt64())
        continue
      if tt == 178:
        self.add_start_postfix_value(d.getPrefixedString())
        continue
      if tt == 186:
        self.add_end_postfix_value(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_index_name_: res+=prefix+("index_name: %s\n" % self.DebugFormatString(self.index_name_))
    if self.has_start_key_: res+=prefix+("start_key: %s\n" % self.DebugFormatString(self.start_key_))
    if self.has_start_inclusive_: res+=prefix+("start_inclusive: %s\n" % self.DebugFormatBool(self.start_inclusive_))
    if self.has_end_key_: res+=prefix+("end_key: %s\n" % self.DebugFormatString(self.end_key_))
    if self.has_end_inclusive_: res+=prefix+("end_inclusive: %s\n" % self.DebugFormatBool(self.end_inclusive_))
    cnt=0
    for e in self.start_postfix_value_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("start_postfix_value%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    cnt=0
    for e in self.end_postfix_value_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("end_postfix_value%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_end_unapplied_log_timestamp_us_: res+=prefix+("end_unapplied_log_timestamp_us: %s\n" % self.DebugFormatInt64(self.end_unapplied_log_timestamp_us_))
    return res

class CompiledQuery_MergeJoinScan(ProtocolBuffer.ProtocolMessage):
  has_index_name_ = 0
  index_name_ = ""
  has_value_prefix_ = 0
  value_prefix_ = 0

  def __init__(self, contents=None):
    self.prefix_value_ = []
    if contents is not None: self.MergeFromString(contents)

  def index_name(self): return self.index_name_

  def set_index_name(self, x):
    self.has_index_name_ = 1
    self.index_name_ = x

  def clear_index_name(self):
    if self.has_index_name_:
      self.has_index_name_ = 0
      self.index_name_ = ""

  def has_index_name(self): return self.has_index_name_

  def prefix_value_size(self): return len(self.prefix_value_)
  def prefix_value_list(self): return self.prefix_value_

  def prefix_value(self, i):
    return self.prefix_value_[i]

  def set_prefix_value(self, i, x):
    self.prefix_value_[i] = x

  def add_prefix_value(self, x):
    self.prefix_value_.append(x)

  def clear_prefix_value(self):
    self.prefix_value_ = []

  def value_prefix(self): return self.value_prefix_

  def set_value_prefix(self, x):
    self.has_value_prefix_ = 1
    self.value_prefix_ = x

  def clear_value_prefix(self):
    if self.has_value_prefix_:
      self.has_value_prefix_ = 0
      self.value_prefix_ = 0

  def has_value_prefix(self): return self.has_value_prefix_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_index_name()): self.set_index_name(x.index_name())
    for i in xrange(x.prefix_value_size()): self.add_prefix_value(x.prefix_value(i))
    if (x.has_value_prefix()): self.set_value_prefix(x.value_prefix())

  def Equals(self, x):
    if x is self: return 1
    if self.has_index_name_ != x.has_index_name_: return 0
    if self.has_index_name_ and self.index_name_ != x.index_name_: return 0
    if len(self.prefix_value_) != len(x.prefix_value_): return 0
    for e1, e2 in zip(self.prefix_value_, x.prefix_value_):
      if e1 != e2: return 0
    if self.has_value_prefix_ != x.has_value_prefix_: return 0
    if self.has_value_prefix_ and self.value_prefix_ != x.value_prefix_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_index_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: index_name not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.index_name_))
    n += 1 * len(self.prefix_value_)
    for i in xrange(len(self.prefix_value_)): n += self.lengthString(len(self.prefix_value_[i]))
    if (self.has_value_prefix_): n += 3
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_index_name_):
      n += 1
      n += self.lengthString(len(self.index_name_))
    n += 1 * len(self.prefix_value_)
    for i in xrange(len(self.prefix_value_)): n += self.lengthString(len(self.prefix_value_[i]))
    if (self.has_value_prefix_): n += 3
    return n

  def Clear(self):
    self.clear_index_name()
    self.clear_prefix_value()
    self.clear_value_prefix()

  def OutputUnchecked(self, out):
    out.putVarInt32(66)
    out.putPrefixedString(self.index_name_)
    for i in xrange(len(self.prefix_value_)):
      out.putVarInt32(74)
      out.putPrefixedString(self.prefix_value_[i])
    if (self.has_value_prefix_):
      out.putVarInt32(160)
      out.putBoolean(self.value_prefix_)

  def OutputPartial(self, out):
    if (self.has_index_name_):
      out.putVarInt32(66)
      out.putPrefixedString(self.index_name_)
    for i in xrange(len(self.prefix_value_)):
      out.putVarInt32(74)
      out.putPrefixedString(self.prefix_value_[i])
    if (self.has_value_prefix_):
      out.putVarInt32(160)
      out.putBoolean(self.value_prefix_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 60: break
      if tt == 66:
        self.set_index_name(d.getPrefixedString())
        continue
      if tt == 74:
        self.add_prefix_value(d.getPrefixedString())
        continue
      if tt == 160:
        self.set_value_prefix(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_index_name_: res+=prefix+("index_name: %s\n" % self.DebugFormatString(self.index_name_))
    cnt=0
    for e in self.prefix_value_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("prefix_value%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_value_prefix_: res+=prefix+("value_prefix: %s\n" % self.DebugFormatBool(self.value_prefix_))
    return res

class CompiledQuery_EntityFilter(ProtocolBuffer.ProtocolMessage):
  has_distinct_ = 0
  distinct_ = 0
  has_kind_ = 0
  kind_ = ""
  has_ancestor_ = 0
  ancestor_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def distinct(self): return self.distinct_

  def set_distinct(self, x):
    self.has_distinct_ = 1
    self.distinct_ = x

  def clear_distinct(self):
    if self.has_distinct_:
      self.has_distinct_ = 0
      self.distinct_ = 0

  def has_distinct(self): return self.has_distinct_

  def kind(self): return self.kind_

  def set_kind(self, x):
    self.has_kind_ = 1
    self.kind_ = x

  def clear_kind(self):
    if self.has_kind_:
      self.has_kind_ = 0
      self.kind_ = ""

  def has_kind(self): return self.has_kind_

  def ancestor(self):
    if self.ancestor_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.ancestor_ is None: self.ancestor_ = Reference()
      finally:
        self.lazy_init_lock_.release()
    return self.ancestor_

  def mutable_ancestor(self): self.has_ancestor_ = 1; return self.ancestor()

  def clear_ancestor(self):

    if self.has_ancestor_:
      self.has_ancestor_ = 0;
      if self.ancestor_ is not None: self.ancestor_.Clear()

  def has_ancestor(self): return self.has_ancestor_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_distinct()): self.set_distinct(x.distinct())
    if (x.has_kind()): self.set_kind(x.kind())
    if (x.has_ancestor()): self.mutable_ancestor().MergeFrom(x.ancestor())

  def Equals(self, x):
    if x is self: return 1
    if self.has_distinct_ != x.has_distinct_: return 0
    if self.has_distinct_ and self.distinct_ != x.distinct_: return 0
    if self.has_kind_ != x.has_kind_: return 0
    if self.has_kind_ and self.kind_ != x.kind_: return 0
    if self.has_ancestor_ != x.has_ancestor_: return 0
    if self.has_ancestor_ and self.ancestor_ != x.ancestor_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_ancestor_ and not self.ancestor_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_distinct_): n += 2
    if (self.has_kind_): n += 2 + self.lengthString(len(self.kind_))
    if (self.has_ancestor_): n += 2 + self.lengthString(self.ancestor_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_distinct_): n += 2
    if (self.has_kind_): n += 2 + self.lengthString(len(self.kind_))
    if (self.has_ancestor_): n += 2 + self.lengthString(self.ancestor_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_distinct()
    self.clear_kind()
    self.clear_ancestor()

  def OutputUnchecked(self, out):
    if (self.has_distinct_):
      out.putVarInt32(112)
      out.putBoolean(self.distinct_)
    if (self.has_kind_):
      out.putVarInt32(138)
      out.putPrefixedString(self.kind_)
    if (self.has_ancestor_):
      out.putVarInt32(146)
      out.putVarInt32(self.ancestor_.ByteSize())
      self.ancestor_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_distinct_):
      out.putVarInt32(112)
      out.putBoolean(self.distinct_)
    if (self.has_kind_):
      out.putVarInt32(138)
      out.putPrefixedString(self.kind_)
    if (self.has_ancestor_):
      out.putVarInt32(146)
      out.putVarInt32(self.ancestor_.ByteSizePartial())
      self.ancestor_.OutputPartial(out)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 108: break
      if tt == 112:
        self.set_distinct(d.getBoolean())
        continue
      if tt == 138:
        self.set_kind(d.getPrefixedString())
        continue
      if tt == 146:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_ancestor().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_distinct_: res+=prefix+("distinct: %s\n" % self.DebugFormatBool(self.distinct_))
    if self.has_kind_: res+=prefix+("kind: %s\n" % self.DebugFormatString(self.kind_))
    if self.has_ancestor_:
      res+=prefix+"ancestor <\n"
      res+=self.ancestor_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res

class CompiledQuery(ProtocolBuffer.ProtocolMessage):
  has_primaryscan_ = 0
  has_index_def_ = 0
  index_def_ = None
  has_offset_ = 0
  offset_ = 0
  has_limit_ = 0
  limit_ = 0
  has_keys_only_ = 0
  keys_only_ = 0
  has_distinct_infix_size_ = 0
  distinct_infix_size_ = 0
  has_entityfilter_ = 0
  entityfilter_ = None
  has_plan_label_ = 0
  plan_label_ = ""

  def __init__(self, contents=None):
    self.primaryscan_ = CompiledQuery_PrimaryScan()
    self.mergejoinscan_ = []
    self.property_name_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def primaryscan(self): return self.primaryscan_

  def mutable_primaryscan(self): self.has_primaryscan_ = 1; return self.primaryscan_

  def clear_primaryscan(self):self.has_primaryscan_ = 0; self.primaryscan_.Clear()

  def has_primaryscan(self): return self.has_primaryscan_

  def mergejoinscan_size(self): return len(self.mergejoinscan_)
  def mergejoinscan_list(self): return self.mergejoinscan_

  def mergejoinscan(self, i):
    return self.mergejoinscan_[i]

  def mutable_mergejoinscan(self, i):
    return self.mergejoinscan_[i]

  def add_mergejoinscan(self):
    x = CompiledQuery_MergeJoinScan()
    self.mergejoinscan_.append(x)
    return x

  def clear_mergejoinscan(self):
    self.mergejoinscan_ = []
  def index_def(self):
    if self.index_def_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.index_def_ is None: self.index_def_ = Index()
      finally:
        self.lazy_init_lock_.release()
    return self.index_def_

  def mutable_index_def(self): self.has_index_def_ = 1; return self.index_def()

  def clear_index_def(self):

    if self.has_index_def_:
      self.has_index_def_ = 0;
      if self.index_def_ is not None: self.index_def_.Clear()

  def has_index_def(self): return self.has_index_def_

  def offset(self): return self.offset_

  def set_offset(self, x):
    self.has_offset_ = 1
    self.offset_ = x

  def clear_offset(self):
    if self.has_offset_:
      self.has_offset_ = 0
      self.offset_ = 0

  def has_offset(self): return self.has_offset_

  def limit(self): return self.limit_

  def set_limit(self, x):
    self.has_limit_ = 1
    self.limit_ = x

  def clear_limit(self):
    if self.has_limit_:
      self.has_limit_ = 0
      self.limit_ = 0

  def has_limit(self): return self.has_limit_

  def keys_only(self): return self.keys_only_

  def set_keys_only(self, x):
    self.has_keys_only_ = 1
    self.keys_only_ = x

  def clear_keys_only(self):
    if self.has_keys_only_:
      self.has_keys_only_ = 0
      self.keys_only_ = 0

  def has_keys_only(self): return self.has_keys_only_

  def property_name_size(self): return len(self.property_name_)
  def property_name_list(self): return self.property_name_

  def property_name(self, i):
    return self.property_name_[i]

  def set_property_name(self, i, x):
    self.property_name_[i] = x

  def add_property_name(self, x):
    self.property_name_.append(x)

  def clear_property_name(self):
    self.property_name_ = []

  def distinct_infix_size(self): return self.distinct_infix_size_

  def set_distinct_infix_size(self, x):
    self.has_distinct_infix_size_ = 1
    self.distinct_infix_size_ = x

  def clear_distinct_infix_size(self):
    if self.has_distinct_infix_size_:
      self.has_distinct_infix_size_ = 0
      self.distinct_infix_size_ = 0

  def has_distinct_infix_size(self): return self.has_distinct_infix_size_

  def entityfilter(self):
    if self.entityfilter_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.entityfilter_ is None: self.entityfilter_ = CompiledQuery_EntityFilter()
      finally:
        self.lazy_init_lock_.release()
    return self.entityfilter_

  def mutable_entityfilter(self): self.has_entityfilter_ = 1; return self.entityfilter()

  def clear_entityfilter(self):

    if self.has_entityfilter_:
      self.has_entityfilter_ = 0;
      if self.entityfilter_ is not None: self.entityfilter_.Clear()

  def has_entityfilter(self): return self.has_entityfilter_

  def plan_label(self): return self.plan_label_

  def set_plan_label(self, x):
    self.has_plan_label_ = 1
    self.plan_label_ = x

  def clear_plan_label(self):
    if self.has_plan_label_:
      self.has_plan_label_ = 0
      self.plan_label_ = ""

  def has_plan_label(self): return self.has_plan_label_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_primaryscan()): self.mutable_primaryscan().MergeFrom(x.primaryscan())
    for i in xrange(x.mergejoinscan_size()): self.add_mergejoinscan().CopyFrom(x.mergejoinscan(i))
    if (x.has_index_def()): self.mutable_index_def().MergeFrom(x.index_def())
    if (x.has_offset()): self.set_offset(x.offset())
    if (x.has_limit()): self.set_limit(x.limit())
    if (x.has_keys_only()): self.set_keys_only(x.keys_only())
    for i in xrange(x.property_name_size()): self.add_property_name(x.property_name(i))
    if (x.has_distinct_infix_size()): self.set_distinct_infix_size(x.distinct_infix_size())
    if (x.has_entityfilter()): self.mutable_entityfilter().MergeFrom(x.entityfilter())
    if (x.has_plan_label()): self.set_plan_label(x.plan_label())

  def Equals(self, x):
    if x is self: return 1
    if self.has_primaryscan_ != x.has_primaryscan_: return 0
    if self.has_primaryscan_ and self.primaryscan_ != x.primaryscan_: return 0
    if len(self.mergejoinscan_) != len(x.mergejoinscan_): return 0
    for e1, e2 in zip(self.mergejoinscan_, x.mergejoinscan_):
      if e1 != e2: return 0
    if self.has_index_def_ != x.has_index_def_: return 0
    if self.has_index_def_ and self.index_def_ != x.index_def_: return 0
    if self.has_offset_ != x.has_offset_: return 0
    if self.has_offset_ and self.offset_ != x.offset_: return 0
    if self.has_limit_ != x.has_limit_: return 0
    if self.has_limit_ and self.limit_ != x.limit_: return 0
    if self.has_keys_only_ != x.has_keys_only_: return 0
    if self.has_keys_only_ and self.keys_only_ != x.keys_only_: return 0
    if len(self.property_name_) != len(x.property_name_): return 0
    for e1, e2 in zip(self.property_name_, x.property_name_):
      if e1 != e2: return 0
    if self.has_distinct_infix_size_ != x.has_distinct_infix_size_: return 0
    if self.has_distinct_infix_size_ and self.distinct_infix_size_ != x.distinct_infix_size_: return 0
    if self.has_entityfilter_ != x.has_entityfilter_: return 0
    if self.has_entityfilter_ and self.entityfilter_ != x.entityfilter_: return 0
    if self.has_plan_label_ != x.has_plan_label_: return 0
    if self.has_plan_label_ and self.plan_label_ != x.plan_label_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_primaryscan_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: primaryscan not set.')
    elif not self.primaryscan_.IsInitialized(debug_strs): initialized = 0
    for p in self.mergejoinscan_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_index_def_ and not self.index_def_.IsInitialized(debug_strs)): initialized = 0
    if (not self.has_keys_only_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: keys_only not set.')
    if (self.has_entityfilter_ and not self.entityfilter_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.primaryscan_.ByteSize()
    n += 2 * len(self.mergejoinscan_)
    for i in xrange(len(self.mergejoinscan_)): n += self.mergejoinscan_[i].ByteSize()
    if (self.has_index_def_): n += 2 + self.lengthString(self.index_def_.ByteSize())
    if (self.has_offset_): n += 1 + self.lengthVarInt64(self.offset_)
    if (self.has_limit_): n += 1 + self.lengthVarInt64(self.limit_)
    n += 2 * len(self.property_name_)
    for i in xrange(len(self.property_name_)): n += self.lengthString(len(self.property_name_[i]))
    if (self.has_distinct_infix_size_): n += 2 + self.lengthVarInt64(self.distinct_infix_size_)
    if (self.has_entityfilter_): n += 2 + self.entityfilter_.ByteSize()
    if (self.has_plan_label_): n += 2 + self.lengthString(len(self.plan_label_))
    return n + 4

  def ByteSizePartial(self):
    n = 0
    if (self.has_primaryscan_):
      n += 2
      n += self.primaryscan_.ByteSizePartial()
    n += 2 * len(self.mergejoinscan_)
    for i in xrange(len(self.mergejoinscan_)): n += self.mergejoinscan_[i].ByteSizePartial()
    if (self.has_index_def_): n += 2 + self.lengthString(self.index_def_.ByteSizePartial())
    if (self.has_offset_): n += 1 + self.lengthVarInt64(self.offset_)
    if (self.has_limit_): n += 1 + self.lengthVarInt64(self.limit_)
    if (self.has_keys_only_):
      n += 2
    n += 2 * len(self.property_name_)
    for i in xrange(len(self.property_name_)): n += self.lengthString(len(self.property_name_[i]))
    if (self.has_distinct_infix_size_): n += 2 + self.lengthVarInt64(self.distinct_infix_size_)
    if (self.has_entityfilter_): n += 2 + self.entityfilter_.ByteSizePartial()
    if (self.has_plan_label_): n += 2 + self.lengthString(len(self.plan_label_))
    return n

  def Clear(self):
    self.clear_primaryscan()
    self.clear_mergejoinscan()
    self.clear_index_def()
    self.clear_offset()
    self.clear_limit()
    self.clear_keys_only()
    self.clear_property_name()
    self.clear_distinct_infix_size()
    self.clear_entityfilter()
    self.clear_plan_label()

  def OutputUnchecked(self, out):
    out.putVarInt32(11)
    self.primaryscan_.OutputUnchecked(out)
    out.putVarInt32(12)
    for i in xrange(len(self.mergejoinscan_)):
      out.putVarInt32(59)
      self.mergejoinscan_[i].OutputUnchecked(out)
      out.putVarInt32(60)
    if (self.has_offset_):
      out.putVarInt32(80)
      out.putVarInt32(self.offset_)
    if (self.has_limit_):
      out.putVarInt32(88)
      out.putVarInt32(self.limit_)
    out.putVarInt32(96)
    out.putBoolean(self.keys_only_)
    if (self.has_entityfilter_):
      out.putVarInt32(107)
      self.entityfilter_.OutputUnchecked(out)
      out.putVarInt32(108)
    if (self.has_index_def_):
      out.putVarInt32(170)
      out.putVarInt32(self.index_def_.ByteSize())
      self.index_def_.OutputUnchecked(out)
    for i in xrange(len(self.property_name_)):
      out.putVarInt32(194)
      out.putPrefixedString(self.property_name_[i])
    if (self.has_distinct_infix_size_):
      out.putVarInt32(200)
      out.putVarInt32(self.distinct_infix_size_)
    if (self.has_plan_label_):
      out.putVarInt32(210)
      out.putPrefixedString(self.plan_label_)

  def OutputPartial(self, out):
    if (self.has_primaryscan_):
      out.putVarInt32(11)
      self.primaryscan_.OutputPartial(out)
      out.putVarInt32(12)
    for i in xrange(len(self.mergejoinscan_)):
      out.putVarInt32(59)
      self.mergejoinscan_[i].OutputPartial(out)
      out.putVarInt32(60)
    if (self.has_offset_):
      out.putVarInt32(80)
      out.putVarInt32(self.offset_)
    if (self.has_limit_):
      out.putVarInt32(88)
      out.putVarInt32(self.limit_)
    if (self.has_keys_only_):
      out.putVarInt32(96)
      out.putBoolean(self.keys_only_)
    if (self.has_entityfilter_):
      out.putVarInt32(107)
      self.entityfilter_.OutputPartial(out)
      out.putVarInt32(108)
    if (self.has_index_def_):
      out.putVarInt32(170)
      out.putVarInt32(self.index_def_.ByteSizePartial())
      self.index_def_.OutputPartial(out)
    for i in xrange(len(self.property_name_)):
      out.putVarInt32(194)
      out.putPrefixedString(self.property_name_[i])
    if (self.has_distinct_infix_size_):
      out.putVarInt32(200)
      out.putVarInt32(self.distinct_infix_size_)
    if (self.has_plan_label_):
      out.putVarInt32(210)
      out.putPrefixedString(self.plan_label_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 11:
        self.mutable_primaryscan().TryMerge(d)
        continue
      if tt == 59:
        self.add_mergejoinscan().TryMerge(d)
        continue
      if tt == 80:
        self.set_offset(d.getVarInt32())
        continue
      if tt == 88:
        self.set_limit(d.getVarInt32())
        continue
      if tt == 96:
        self.set_keys_only(d.getBoolean())
        continue
      if tt == 107:
        self.mutable_entityfilter().TryMerge(d)
        continue
      if tt == 170:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_index_def().TryMerge(tmp)
        continue
      if tt == 194:
        self.add_property_name(d.getPrefixedString())
        continue
      if tt == 200:
        self.set_distinct_infix_size(d.getVarInt32())
        continue
      if tt == 210:
        self.set_plan_label(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_primaryscan_:
      res+=prefix+"PrimaryScan {\n"
      res+=self.primaryscan_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
    cnt=0
    for e in self.mergejoinscan_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("MergeJoinScan%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    if self.has_index_def_:
      res+=prefix+"index_def <\n"
      res+=self.index_def_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_offset_: res+=prefix+("offset: %s\n" % self.DebugFormatInt32(self.offset_))
    if self.has_limit_: res+=prefix+("limit: %s\n" % self.DebugFormatInt32(self.limit_))
    if self.has_keys_only_: res+=prefix+("keys_only: %s\n" % self.DebugFormatBool(self.keys_only_))
    cnt=0
    for e in self.property_name_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("property_name%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_distinct_infix_size_: res+=prefix+("distinct_infix_size: %s\n" % self.DebugFormatInt32(self.distinct_infix_size_))
    if self.has_entityfilter_:
      res+=prefix+"EntityFilter {\n"
      res+=self.entityfilter_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
    if self.has_plan_label_: res+=prefix+("plan_label: %s\n" % self.DebugFormatString(self.plan_label_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kPrimaryScanGroup = 1
  kPrimaryScanindex_name = 2
  kPrimaryScanstart_key = 3
  kPrimaryScanstart_inclusive = 4
  kPrimaryScanend_key = 5
  kPrimaryScanend_inclusive = 6
  kPrimaryScanstart_postfix_value = 22
  kPrimaryScanend_postfix_value = 23
  kPrimaryScanend_unapplied_log_timestamp_us = 19
  kMergeJoinScanGroup = 7
  kMergeJoinScanindex_name = 8
  kMergeJoinScanprefix_value = 9
  kMergeJoinScanvalue_prefix = 20
  kindex_def = 21
  koffset = 10
  klimit = 11
  kkeys_only = 12
  kproperty_name = 24
  kdistinct_infix_size = 25
  kEntityFilterGroup = 13
  kEntityFilterdistinct = 14
  kEntityFilterkind = 17
  kEntityFilterancestor = 18
  kplan_label = 26

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "PrimaryScan",
    2: "index_name",
    3: "start_key",
    4: "start_inclusive",
    5: "end_key",
    6: "end_inclusive",
    7: "MergeJoinScan",
    8: "index_name",
    9: "prefix_value",
    10: "offset",
    11: "limit",
    12: "keys_only",
    13: "EntityFilter",
    14: "distinct",
    17: "kind",
    18: "ancestor",
    19: "end_unapplied_log_timestamp_us",
    20: "value_prefix",
    21: "index_def",
    22: "start_postfix_value",
    23: "end_postfix_value",
    24: "property_name",
    25: "distinct_infix_size",
    26: "plan_label",
  }, 26)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STARTGROUP,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.NUMERIC,
    7: ProtocolBuffer.Encoder.STARTGROUP,
    8: ProtocolBuffer.Encoder.STRING,
    9: ProtocolBuffer.Encoder.STRING,
    10: ProtocolBuffer.Encoder.NUMERIC,
    11: ProtocolBuffer.Encoder.NUMERIC,
    12: ProtocolBuffer.Encoder.NUMERIC,
    13: ProtocolBuffer.Encoder.STARTGROUP,
    14: ProtocolBuffer.Encoder.NUMERIC,
    17: ProtocolBuffer.Encoder.STRING,
    18: ProtocolBuffer.Encoder.STRING,
    19: ProtocolBuffer.Encoder.NUMERIC,
    20: ProtocolBuffer.Encoder.NUMERIC,
    21: ProtocolBuffer.Encoder.STRING,
    22: ProtocolBuffer.Encoder.STRING,
    23: ProtocolBuffer.Encoder.STRING,
    24: ProtocolBuffer.Encoder.STRING,
    25: ProtocolBuffer.Encoder.NUMERIC,
    26: ProtocolBuffer.Encoder.STRING,
  }, 26, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.CompiledQuery'
class CompiledCursor_PositionIndexValue(ProtocolBuffer.ProtocolMessage):
  has_property_ = 0
  property_ = ""
  has_value_ = 0

  def __init__(self, contents=None):
    self.value_ = PropertyValue()
    if contents is not None: self.MergeFromString(contents)

  def property(self): return self.property_

  def set_property(self, x):
    self.has_property_ = 1
    self.property_ = x

  def clear_property(self):
    if self.has_property_:
      self.has_property_ = 0
      self.property_ = ""

  def has_property(self): return self.has_property_

  def value(self): return self.value_

  def mutable_value(self): self.has_value_ = 1; return self.value_

  def clear_value(self):self.has_value_ = 0; self.value_.Clear()

  def has_value(self): return self.has_value_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_property()): self.set_property(x.property())
    if (x.has_value()): self.mutable_value().MergeFrom(x.value())

  def Equals(self, x):
    if x is self: return 1
    if self.has_property_ != x.has_property_: return 0
    if self.has_property_ and self.property_ != x.property_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_value_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: value not set.')
    elif not self.value_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_property_): n += 2 + self.lengthString(len(self.property_))
    n += self.lengthString(self.value_.ByteSize())
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_property_): n += 2 + self.lengthString(len(self.property_))
    if (self.has_value_):
      n += 2
      n += self.lengthString(self.value_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_property()
    self.clear_value()

  def OutputUnchecked(self, out):
    if (self.has_property_):
      out.putVarInt32(242)
      out.putPrefixedString(self.property_)
    out.putVarInt32(250)
    out.putVarInt32(self.value_.ByteSize())
    self.value_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_property_):
      out.putVarInt32(242)
      out.putPrefixedString(self.property_)
    if (self.has_value_):
      out.putVarInt32(250)
      out.putVarInt32(self.value_.ByteSizePartial())
      self.value_.OutputPartial(out)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 236: break
      if tt == 242:
        self.set_property(d.getPrefixedString())
        continue
      if tt == 250:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_value().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_property_: res+=prefix+("property: %s\n" % self.DebugFormatString(self.property_))
    if self.has_value_:
      res+=prefix+"value <\n"
      res+=self.value_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res

class CompiledCursor_Position(ProtocolBuffer.ProtocolMessage):
  has_start_key_ = 0
  start_key_ = ""
  has_key_ = 0
  key_ = None
  has_start_inclusive_ = 0
  start_inclusive_ = 1
  has_before_ascending_ = 0
  before_ascending_ = 0

  def __init__(self, contents=None):
    self.indexvalue_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def start_key(self): return self.start_key_

  def set_start_key(self, x):
    self.has_start_key_ = 1
    self.start_key_ = x

  def clear_start_key(self):
    if self.has_start_key_:
      self.has_start_key_ = 0
      self.start_key_ = ""

  def has_start_key(self): return self.has_start_key_

  def indexvalue_size(self): return len(self.indexvalue_)
  def indexvalue_list(self): return self.indexvalue_

  def indexvalue(self, i):
    return self.indexvalue_[i]

  def mutable_indexvalue(self, i):
    return self.indexvalue_[i]

  def add_indexvalue(self):
    x = CompiledCursor_PositionIndexValue()
    self.indexvalue_.append(x)
    return x

  def clear_indexvalue(self):
    self.indexvalue_ = []
  def key(self):
    if self.key_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.key_ is None: self.key_ = Reference()
      finally:
        self.lazy_init_lock_.release()
    return self.key_

  def mutable_key(self): self.has_key_ = 1; return self.key()

  def clear_key(self):

    if self.has_key_:
      self.has_key_ = 0;
      if self.key_ is not None: self.key_.Clear()

  def has_key(self): return self.has_key_

  def start_inclusive(self): return self.start_inclusive_

  def set_start_inclusive(self, x):
    self.has_start_inclusive_ = 1
    self.start_inclusive_ = x

  def clear_start_inclusive(self):
    if self.has_start_inclusive_:
      self.has_start_inclusive_ = 0
      self.start_inclusive_ = 1

  def has_start_inclusive(self): return self.has_start_inclusive_

  def before_ascending(self): return self.before_ascending_

  def set_before_ascending(self, x):
    self.has_before_ascending_ = 1
    self.before_ascending_ = x

  def clear_before_ascending(self):
    if self.has_before_ascending_:
      self.has_before_ascending_ = 0
      self.before_ascending_ = 0

  def has_before_ascending(self): return self.has_before_ascending_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_start_key()): self.set_start_key(x.start_key())
    for i in xrange(x.indexvalue_size()): self.add_indexvalue().CopyFrom(x.indexvalue(i))
    if (x.has_key()): self.mutable_key().MergeFrom(x.key())
    if (x.has_start_inclusive()): self.set_start_inclusive(x.start_inclusive())
    if (x.has_before_ascending()): self.set_before_ascending(x.before_ascending())

  def Equals(self, x):
    if x is self: return 1
    if self.has_start_key_ != x.has_start_key_: return 0
    if self.has_start_key_ and self.start_key_ != x.start_key_: return 0
    if len(self.indexvalue_) != len(x.indexvalue_): return 0
    for e1, e2 in zip(self.indexvalue_, x.indexvalue_):
      if e1 != e2: return 0
    if self.has_key_ != x.has_key_: return 0
    if self.has_key_ and self.key_ != x.key_: return 0
    if self.has_start_inclusive_ != x.has_start_inclusive_: return 0
    if self.has_start_inclusive_ and self.start_inclusive_ != x.start_inclusive_: return 0
    if self.has_before_ascending_ != x.has_before_ascending_: return 0
    if self.has_before_ascending_ and self.before_ascending_ != x.before_ascending_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.indexvalue_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_key_ and not self.key_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_start_key_): n += 2 + self.lengthString(len(self.start_key_))
    n += 4 * len(self.indexvalue_)
    for i in xrange(len(self.indexvalue_)): n += self.indexvalue_[i].ByteSize()
    if (self.has_key_): n += 2 + self.lengthString(self.key_.ByteSize())
    if (self.has_start_inclusive_): n += 3
    if (self.has_before_ascending_): n += 3
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_start_key_): n += 2 + self.lengthString(len(self.start_key_))
    n += 4 * len(self.indexvalue_)
    for i in xrange(len(self.indexvalue_)): n += self.indexvalue_[i].ByteSizePartial()
    if (self.has_key_): n += 2 + self.lengthString(self.key_.ByteSizePartial())
    if (self.has_start_inclusive_): n += 3
    if (self.has_before_ascending_): n += 3
    return n

  def Clear(self):
    self.clear_start_key()
    self.clear_indexvalue()
    self.clear_key()
    self.clear_start_inclusive()
    self.clear_before_ascending()

  def OutputUnchecked(self, out):
    if (self.has_start_key_):
      out.putVarInt32(218)
      out.putPrefixedString(self.start_key_)
    if (self.has_start_inclusive_):
      out.putVarInt32(224)
      out.putBoolean(self.start_inclusive_)
    for i in xrange(len(self.indexvalue_)):
      out.putVarInt32(235)
      self.indexvalue_[i].OutputUnchecked(out)
      out.putVarInt32(236)
    if (self.has_key_):
      out.putVarInt32(258)
      out.putVarInt32(self.key_.ByteSize())
      self.key_.OutputUnchecked(out)
    if (self.has_before_ascending_):
      out.putVarInt32(264)
      out.putBoolean(self.before_ascending_)

  def OutputPartial(self, out):
    if (self.has_start_key_):
      out.putVarInt32(218)
      out.putPrefixedString(self.start_key_)
    if (self.has_start_inclusive_):
      out.putVarInt32(224)
      out.putBoolean(self.start_inclusive_)
    for i in xrange(len(self.indexvalue_)):
      out.putVarInt32(235)
      self.indexvalue_[i].OutputPartial(out)
      out.putVarInt32(236)
    if (self.has_key_):
      out.putVarInt32(258)
      out.putVarInt32(self.key_.ByteSizePartial())
      self.key_.OutputPartial(out)
    if (self.has_before_ascending_):
      out.putVarInt32(264)
      out.putBoolean(self.before_ascending_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 20: break
      if tt == 218:
        self.set_start_key(d.getPrefixedString())
        continue
      if tt == 224:
        self.set_start_inclusive(d.getBoolean())
        continue
      if tt == 235:
        self.add_indexvalue().TryMerge(d)
        continue
      if tt == 258:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_key().TryMerge(tmp)
        continue
      if tt == 264:
        self.set_before_ascending(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_start_key_: res+=prefix+("start_key: %s\n" % self.DebugFormatString(self.start_key_))
    cnt=0
    for e in self.indexvalue_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("IndexValue%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    if self.has_key_:
      res+=prefix+"key <\n"
      res+=self.key_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_start_inclusive_: res+=prefix+("start_inclusive: %s\n" % self.DebugFormatBool(self.start_inclusive_))
    if self.has_before_ascending_: res+=prefix+("before_ascending: %s\n" % self.DebugFormatBool(self.before_ascending_))
    return res

class CompiledCursor(ProtocolBuffer.ProtocolMessage):
  has_position_ = 0
  position_ = None
  has_postfix_position_ = 0
  postfix_position_ = None
  has_absolute_position_ = 0
  absolute_position_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def position(self):
    if self.position_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.position_ is None: self.position_ = CompiledCursor_Position()
      finally:
        self.lazy_init_lock_.release()
    return self.position_

  def mutable_position(self): self.has_position_ = 1; return self.position()

  def clear_position(self):

    if self.has_position_:
      self.has_position_ = 0;
      if self.position_ is not None: self.position_.Clear()

  def has_position(self): return self.has_position_

  def postfix_position(self):
    if self.postfix_position_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.postfix_position_ is None: self.postfix_position_ = IndexPostfix()
      finally:
        self.lazy_init_lock_.release()
    return self.postfix_position_

  def mutable_postfix_position(self): self.has_postfix_position_ = 1; return self.postfix_position()

  def clear_postfix_position(self):

    if self.has_postfix_position_:
      self.has_postfix_position_ = 0;
      if self.postfix_position_ is not None: self.postfix_position_.Clear()

  def has_postfix_position(self): return self.has_postfix_position_

  def absolute_position(self):
    if self.absolute_position_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.absolute_position_ is None: self.absolute_position_ = IndexPosition()
      finally:
        self.lazy_init_lock_.release()
    return self.absolute_position_

  def mutable_absolute_position(self): self.has_absolute_position_ = 1; return self.absolute_position()

  def clear_absolute_position(self):

    if self.has_absolute_position_:
      self.has_absolute_position_ = 0;
      if self.absolute_position_ is not None: self.absolute_position_.Clear()

  def has_absolute_position(self): return self.has_absolute_position_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_position()): self.mutable_position().MergeFrom(x.position())
    if (x.has_postfix_position()): self.mutable_postfix_position().MergeFrom(x.postfix_position())
    if (x.has_absolute_position()): self.mutable_absolute_position().MergeFrom(x.absolute_position())

  def Equals(self, x):
    if x is self: return 1
    if self.has_position_ != x.has_position_: return 0
    if self.has_position_ and self.position_ != x.position_: return 0
    if self.has_postfix_position_ != x.has_postfix_position_: return 0
    if self.has_postfix_position_ and self.postfix_position_ != x.postfix_position_: return 0
    if self.has_absolute_position_ != x.has_absolute_position_: return 0
    if self.has_absolute_position_ and self.absolute_position_ != x.absolute_position_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_position_ and not self.position_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_postfix_position_ and not self.postfix_position_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_absolute_position_ and not self.absolute_position_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_position_): n += 2 + self.position_.ByteSize()
    if (self.has_postfix_position_): n += 1 + self.lengthString(self.postfix_position_.ByteSize())
    if (self.has_absolute_position_): n += 1 + self.lengthString(self.absolute_position_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_position_): n += 2 + self.position_.ByteSizePartial()
    if (self.has_postfix_position_): n += 1 + self.lengthString(self.postfix_position_.ByteSizePartial())
    if (self.has_absolute_position_): n += 1 + self.lengthString(self.absolute_position_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_position()
    self.clear_postfix_position()
    self.clear_absolute_position()

  def OutputUnchecked(self, out):
    if (self.has_postfix_position_):
      out.putVarInt32(10)
      out.putVarInt32(self.postfix_position_.ByteSize())
      self.postfix_position_.OutputUnchecked(out)
    if (self.has_position_):
      out.putVarInt32(19)
      self.position_.OutputUnchecked(out)
      out.putVarInt32(20)
    if (self.has_absolute_position_):
      out.putVarInt32(26)
      out.putVarInt32(self.absolute_position_.ByteSize())
      self.absolute_position_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_postfix_position_):
      out.putVarInt32(10)
      out.putVarInt32(self.postfix_position_.ByteSizePartial())
      self.postfix_position_.OutputPartial(out)
    if (self.has_position_):
      out.putVarInt32(19)
      self.position_.OutputPartial(out)
      out.putVarInt32(20)
    if (self.has_absolute_position_):
      out.putVarInt32(26)
      out.putVarInt32(self.absolute_position_.ByteSizePartial())
      self.absolute_position_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_postfix_position().TryMerge(tmp)
        continue
      if tt == 19:
        self.mutable_position().TryMerge(d)
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_absolute_position().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_position_:
      res+=prefix+"Position {\n"
      res+=self.position_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
    if self.has_postfix_position_:
      res+=prefix+"postfix_position <\n"
      res+=self.postfix_position_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_absolute_position_:
      res+=prefix+"absolute_position <\n"
      res+=self.absolute_position_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kPositionGroup = 2
  kPositionstart_key = 27
  kPositionIndexValueGroup = 29
  kPositionIndexValueproperty = 30
  kPositionIndexValuevalue = 31
  kPositionkey = 32
  kPositionstart_inclusive = 28
  kPositionbefore_ascending = 33
  kpostfix_position = 1
  kabsolute_position = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "postfix_position",
    2: "Position",
    3: "absolute_position",
    27: "start_key",
    28: "start_inclusive",
    29: "IndexValue",
    30: "property",
    31: "value",
    32: "key",
    33: "before_ascending",
  }, 33)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STARTGROUP,
    3: ProtocolBuffer.Encoder.STRING,
    27: ProtocolBuffer.Encoder.STRING,
    28: ProtocolBuffer.Encoder.NUMERIC,
    29: ProtocolBuffer.Encoder.STARTGROUP,
    30: ProtocolBuffer.Encoder.STRING,
    31: ProtocolBuffer.Encoder.STRING,
    32: ProtocolBuffer.Encoder.STRING,
    33: ProtocolBuffer.Encoder.NUMERIC,
  }, 33, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.CompiledCursor'
class Cursor(ProtocolBuffer.ProtocolMessage):
  has_cursor_ = 0
  cursor_ = 0
  has_app_ = 0
  app_ = ""
  has_database_id_ = 0
  database_id_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def cursor(self): return self.cursor_

  def set_cursor(self, x):
    self.has_cursor_ = 1
    self.cursor_ = x

  def clear_cursor(self):
    if self.has_cursor_:
      self.has_cursor_ = 0
      self.cursor_ = 0

  def has_cursor(self): return self.has_cursor_

  def app(self): return self.app_

  def set_app(self, x):
    self.has_app_ = 1
    self.app_ = x

  def clear_app(self):
    if self.has_app_:
      self.has_app_ = 0
      self.app_ = ""

  def has_app(self): return self.has_app_

  def database_id(self): return self.database_id_

  def set_database_id(self, x):
    self.has_database_id_ = 1
    self.database_id_ = x

  def clear_database_id(self):
    if self.has_database_id_:
      self.has_database_id_ = 0
      self.database_id_ = ""

  def has_database_id(self): return self.has_database_id_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_cursor()): self.set_cursor(x.cursor())
    if (x.has_app()): self.set_app(x.app())
    if (x.has_database_id()): self.set_database_id(x.database_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_cursor_ != x.has_cursor_: return 0
    if self.has_cursor_ and self.cursor_ != x.cursor_: return 0
    if self.has_app_ != x.has_app_: return 0
    if self.has_app_ and self.app_ != x.app_: return 0
    if self.has_database_id_ != x.has_database_id_: return 0
    if self.has_database_id_ and self.database_id_ != x.database_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_cursor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: cursor not set.')
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_app_): n += 1 + self.lengthString(len(self.app_))
    if (self.has_database_id_): n += 1 + self.lengthString(len(self.database_id_))
    return n + 9

  def ByteSizePartial(self):
    n = 0
    if (self.has_cursor_):
      n += 9
    if (self.has_app_): n += 1 + self.lengthString(len(self.app_))
    if (self.has_database_id_): n += 1 + self.lengthString(len(self.database_id_))
    return n

  def Clear(self):
    self.clear_cursor()
    self.clear_app()
    self.clear_database_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(9)
    out.put64(self.cursor_)
    if (self.has_app_):
      out.putVarInt32(18)
      out.putPrefixedString(self.app_)
    if (self.has_database_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.database_id_)

  def OutputPartial(self, out):
    if (self.has_cursor_):
      out.putVarInt32(9)
      out.put64(self.cursor_)
    if (self.has_app_):
      out.putVarInt32(18)
      out.putPrefixedString(self.app_)
    if (self.has_database_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.database_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 9:
        self.set_cursor(d.get64())
        continue
      if tt == 18:
        self.set_app(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_database_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_cursor_: res+=prefix+("cursor: %s\n" % self.DebugFormatFixed64(self.cursor_))
    if self.has_app_: res+=prefix+("app: %s\n" % self.DebugFormatString(self.app_))
    if self.has_database_id_: res+=prefix+("database_id: %s\n" % self.DebugFormatString(self.database_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kcursor = 1
  kapp = 2
  kdatabase_id = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "cursor",
    2: "app",
    3: "database_id",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.DOUBLE,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.Cursor'
class Error(ProtocolBuffer.ProtocolMessage):


  BAD_REQUEST  =    1
  CONCURRENT_TRANSACTION =    2
  INTERNAL_ERROR =    3
  NEED_INDEX   =    4
  TIMEOUT      =    5
  PERMISSION_DENIED =    6
  BIGTABLE_ERROR =    7
  COMMITTED_BUT_STILL_APPLYING =    8
  CAPABILITY_DISABLED =    9
  TRY_ALTERNATE_BACKEND =   10
  SAFE_TIME_TOO_OLD =   11
  RESOURCE_EXHAUSTED =   12

  _ErrorCode_NAMES = {
    1: "BAD_REQUEST",
    2: "CONCURRENT_TRANSACTION",
    3: "INTERNAL_ERROR",
    4: "NEED_INDEX",
    5: "TIMEOUT",
    6: "PERMISSION_DENIED",
    7: "BIGTABLE_ERROR",
    8: "COMMITTED_BUT_STILL_APPLYING",
    9: "CAPABILITY_DISABLED",
    10: "TRY_ALTERNATE_BACKEND",
    11: "SAFE_TIME_TOO_OLD",
    12: "RESOURCE_EXHAUSTED",
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.Error'
class Cost_CommitCost(ProtocolBuffer.ProtocolMessage):
  has_requested_entity_puts_ = 0
  requested_entity_puts_ = 0
  has_requested_entity_deletes_ = 0
  requested_entity_deletes_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def requested_entity_puts(self): return self.requested_entity_puts_

  def set_requested_entity_puts(self, x):
    self.has_requested_entity_puts_ = 1
    self.requested_entity_puts_ = x

  def clear_requested_entity_puts(self):
    if self.has_requested_entity_puts_:
      self.has_requested_entity_puts_ = 0
      self.requested_entity_puts_ = 0

  def has_requested_entity_puts(self): return self.has_requested_entity_puts_

  def requested_entity_deletes(self): return self.requested_entity_deletes_

  def set_requested_entity_deletes(self, x):
    self.has_requested_entity_deletes_ = 1
    self.requested_entity_deletes_ = x

  def clear_requested_entity_deletes(self):
    if self.has_requested_entity_deletes_:
      self.has_requested_entity_deletes_ = 0
      self.requested_entity_deletes_ = 0

  def has_requested_entity_deletes(self): return self.has_requested_entity_deletes_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_requested_entity_puts()): self.set_requested_entity_puts(x.requested_entity_puts())
    if (x.has_requested_entity_deletes()): self.set_requested_entity_deletes(x.requested_entity_deletes())

  def Equals(self, x):
    if x is self: return 1
    if self.has_requested_entity_puts_ != x.has_requested_entity_puts_: return 0
    if self.has_requested_entity_puts_ and self.requested_entity_puts_ != x.requested_entity_puts_: return 0
    if self.has_requested_entity_deletes_ != x.has_requested_entity_deletes_: return 0
    if self.has_requested_entity_deletes_ and self.requested_entity_deletes_ != x.requested_entity_deletes_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_requested_entity_puts_): n += 1 + self.lengthVarInt64(self.requested_entity_puts_)
    if (self.has_requested_entity_deletes_): n += 1 + self.lengthVarInt64(self.requested_entity_deletes_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_requested_entity_puts_): n += 1 + self.lengthVarInt64(self.requested_entity_puts_)
    if (self.has_requested_entity_deletes_): n += 1 + self.lengthVarInt64(self.requested_entity_deletes_)
    return n

  def Clear(self):
    self.clear_requested_entity_puts()
    self.clear_requested_entity_deletes()

  def OutputUnchecked(self, out):
    if (self.has_requested_entity_puts_):
      out.putVarInt32(48)
      out.putVarInt32(self.requested_entity_puts_)
    if (self.has_requested_entity_deletes_):
      out.putVarInt32(56)
      out.putVarInt32(self.requested_entity_deletes_)

  def OutputPartial(self, out):
    if (self.has_requested_entity_puts_):
      out.putVarInt32(48)
      out.putVarInt32(self.requested_entity_puts_)
    if (self.has_requested_entity_deletes_):
      out.putVarInt32(56)
      out.putVarInt32(self.requested_entity_deletes_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 44: break
      if tt == 48:
        self.set_requested_entity_puts(d.getVarInt32())
        continue
      if tt == 56:
        self.set_requested_entity_deletes(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_requested_entity_puts_: res+=prefix+("requested_entity_puts: %s\n" % self.DebugFormatInt32(self.requested_entity_puts_))
    if self.has_requested_entity_deletes_: res+=prefix+("requested_entity_deletes: %s\n" % self.DebugFormatInt32(self.requested_entity_deletes_))
    return res

class Cost(ProtocolBuffer.ProtocolMessage):
  has_index_writes_ = 0
  index_writes_ = 0
  has_index_write_bytes_ = 0
  index_write_bytes_ = 0
  has_entity_writes_ = 0
  entity_writes_ = 0
  has_entity_write_bytes_ = 0
  entity_write_bytes_ = 0
  has_commitcost_ = 0
  commitcost_ = None
  has_approximate_storage_delta_ = 0
  approximate_storage_delta_ = 0
  has_id_sequence_updates_ = 0
  id_sequence_updates_ = 0

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def index_writes(self): return self.index_writes_

  def set_index_writes(self, x):
    self.has_index_writes_ = 1
    self.index_writes_ = x

  def clear_index_writes(self):
    if self.has_index_writes_:
      self.has_index_writes_ = 0
      self.index_writes_ = 0

  def has_index_writes(self): return self.has_index_writes_

  def index_write_bytes(self): return self.index_write_bytes_

  def set_index_write_bytes(self, x):
    self.has_index_write_bytes_ = 1
    self.index_write_bytes_ = x

  def clear_index_write_bytes(self):
    if self.has_index_write_bytes_:
      self.has_index_write_bytes_ = 0
      self.index_write_bytes_ = 0

  def has_index_write_bytes(self): return self.has_index_write_bytes_

  def entity_writes(self): return self.entity_writes_

  def set_entity_writes(self, x):
    self.has_entity_writes_ = 1
    self.entity_writes_ = x

  def clear_entity_writes(self):
    if self.has_entity_writes_:
      self.has_entity_writes_ = 0
      self.entity_writes_ = 0

  def has_entity_writes(self): return self.has_entity_writes_

  def entity_write_bytes(self): return self.entity_write_bytes_

  def set_entity_write_bytes(self, x):
    self.has_entity_write_bytes_ = 1
    self.entity_write_bytes_ = x

  def clear_entity_write_bytes(self):
    if self.has_entity_write_bytes_:
      self.has_entity_write_bytes_ = 0
      self.entity_write_bytes_ = 0

  def has_entity_write_bytes(self): return self.has_entity_write_bytes_

  def commitcost(self):
    if self.commitcost_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.commitcost_ is None: self.commitcost_ = Cost_CommitCost()
      finally:
        self.lazy_init_lock_.release()
    return self.commitcost_

  def mutable_commitcost(self): self.has_commitcost_ = 1; return self.commitcost()

  def clear_commitcost(self):

    if self.has_commitcost_:
      self.has_commitcost_ = 0;
      if self.commitcost_ is not None: self.commitcost_.Clear()

  def has_commitcost(self): return self.has_commitcost_

  def approximate_storage_delta(self): return self.approximate_storage_delta_

  def set_approximate_storage_delta(self, x):
    self.has_approximate_storage_delta_ = 1
    self.approximate_storage_delta_ = x

  def clear_approximate_storage_delta(self):
    if self.has_approximate_storage_delta_:
      self.has_approximate_storage_delta_ = 0
      self.approximate_storage_delta_ = 0

  def has_approximate_storage_delta(self): return self.has_approximate_storage_delta_

  def id_sequence_updates(self): return self.id_sequence_updates_

  def set_id_sequence_updates(self, x):
    self.has_id_sequence_updates_ = 1
    self.id_sequence_updates_ = x

  def clear_id_sequence_updates(self):
    if self.has_id_sequence_updates_:
      self.has_id_sequence_updates_ = 0
      self.id_sequence_updates_ = 0

  def has_id_sequence_updates(self): return self.has_id_sequence_updates_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_index_writes()): self.set_index_writes(x.index_writes())
    if (x.has_index_write_bytes()): self.set_index_write_bytes(x.index_write_bytes())
    if (x.has_entity_writes()): self.set_entity_writes(x.entity_writes())
    if (x.has_entity_write_bytes()): self.set_entity_write_bytes(x.entity_write_bytes())
    if (x.has_commitcost()): self.mutable_commitcost().MergeFrom(x.commitcost())
    if (x.has_approximate_storage_delta()): self.set_approximate_storage_delta(x.approximate_storage_delta())
    if (x.has_id_sequence_updates()): self.set_id_sequence_updates(x.id_sequence_updates())

  def Equals(self, x):
    if x is self: return 1
    if self.has_index_writes_ != x.has_index_writes_: return 0
    if self.has_index_writes_ and self.index_writes_ != x.index_writes_: return 0
    if self.has_index_write_bytes_ != x.has_index_write_bytes_: return 0
    if self.has_index_write_bytes_ and self.index_write_bytes_ != x.index_write_bytes_: return 0
    if self.has_entity_writes_ != x.has_entity_writes_: return 0
    if self.has_entity_writes_ and self.entity_writes_ != x.entity_writes_: return 0
    if self.has_entity_write_bytes_ != x.has_entity_write_bytes_: return 0
    if self.has_entity_write_bytes_ and self.entity_write_bytes_ != x.entity_write_bytes_: return 0
    if self.has_commitcost_ != x.has_commitcost_: return 0
    if self.has_commitcost_ and self.commitcost_ != x.commitcost_: return 0
    if self.has_approximate_storage_delta_ != x.has_approximate_storage_delta_: return 0
    if self.has_approximate_storage_delta_ and self.approximate_storage_delta_ != x.approximate_storage_delta_: return 0
    if self.has_id_sequence_updates_ != x.has_id_sequence_updates_: return 0
    if self.has_id_sequence_updates_ and self.id_sequence_updates_ != x.id_sequence_updates_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_commitcost_ and not self.commitcost_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_index_writes_): n += 1 + self.lengthVarInt64(self.index_writes_)
    if (self.has_index_write_bytes_): n += 1 + self.lengthVarInt64(self.index_write_bytes_)
    if (self.has_entity_writes_): n += 1 + self.lengthVarInt64(self.entity_writes_)
    if (self.has_entity_write_bytes_): n += 1 + self.lengthVarInt64(self.entity_write_bytes_)
    if (self.has_commitcost_): n += 2 + self.commitcost_.ByteSize()
    if (self.has_approximate_storage_delta_): n += 1 + self.lengthVarInt64(self.approximate_storage_delta_)
    if (self.has_id_sequence_updates_): n += 1 + self.lengthVarInt64(self.id_sequence_updates_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_index_writes_): n += 1 + self.lengthVarInt64(self.index_writes_)
    if (self.has_index_write_bytes_): n += 1 + self.lengthVarInt64(self.index_write_bytes_)
    if (self.has_entity_writes_): n += 1 + self.lengthVarInt64(self.entity_writes_)
    if (self.has_entity_write_bytes_): n += 1 + self.lengthVarInt64(self.entity_write_bytes_)
    if (self.has_commitcost_): n += 2 + self.commitcost_.ByteSizePartial()
    if (self.has_approximate_storage_delta_): n += 1 + self.lengthVarInt64(self.approximate_storage_delta_)
    if (self.has_id_sequence_updates_): n += 1 + self.lengthVarInt64(self.id_sequence_updates_)
    return n

  def Clear(self):
    self.clear_index_writes()
    self.clear_index_write_bytes()
    self.clear_entity_writes()
    self.clear_entity_write_bytes()
    self.clear_commitcost()
    self.clear_approximate_storage_delta()
    self.clear_id_sequence_updates()

  def OutputUnchecked(self, out):
    if (self.has_index_writes_):
      out.putVarInt32(8)
      out.putVarInt32(self.index_writes_)
    if (self.has_index_write_bytes_):
      out.putVarInt32(16)
      out.putVarInt32(self.index_write_bytes_)
    if (self.has_entity_writes_):
      out.putVarInt32(24)
      out.putVarInt32(self.entity_writes_)
    if (self.has_entity_write_bytes_):
      out.putVarInt32(32)
      out.putVarInt32(self.entity_write_bytes_)
    if (self.has_commitcost_):
      out.putVarInt32(43)
      self.commitcost_.OutputUnchecked(out)
      out.putVarInt32(44)
    if (self.has_approximate_storage_delta_):
      out.putVarInt32(64)
      out.putVarInt32(self.approximate_storage_delta_)
    if (self.has_id_sequence_updates_):
      out.putVarInt32(72)
      out.putVarInt32(self.id_sequence_updates_)

  def OutputPartial(self, out):
    if (self.has_index_writes_):
      out.putVarInt32(8)
      out.putVarInt32(self.index_writes_)
    if (self.has_index_write_bytes_):
      out.putVarInt32(16)
      out.putVarInt32(self.index_write_bytes_)
    if (self.has_entity_writes_):
      out.putVarInt32(24)
      out.putVarInt32(self.entity_writes_)
    if (self.has_entity_write_bytes_):
      out.putVarInt32(32)
      out.putVarInt32(self.entity_write_bytes_)
    if (self.has_commitcost_):
      out.putVarInt32(43)
      self.commitcost_.OutputPartial(out)
      out.putVarInt32(44)
    if (self.has_approximate_storage_delta_):
      out.putVarInt32(64)
      out.putVarInt32(self.approximate_storage_delta_)
    if (self.has_id_sequence_updates_):
      out.putVarInt32(72)
      out.putVarInt32(self.id_sequence_updates_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_index_writes(d.getVarInt32())
        continue
      if tt == 16:
        self.set_index_write_bytes(d.getVarInt32())
        continue
      if tt == 24:
        self.set_entity_writes(d.getVarInt32())
        continue
      if tt == 32:
        self.set_entity_write_bytes(d.getVarInt32())
        continue
      if tt == 43:
        self.mutable_commitcost().TryMerge(d)
        continue
      if tt == 64:
        self.set_approximate_storage_delta(d.getVarInt32())
        continue
      if tt == 72:
        self.set_id_sequence_updates(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_index_writes_: res+=prefix+("index_writes: %s\n" % self.DebugFormatInt32(self.index_writes_))
    if self.has_index_write_bytes_: res+=prefix+("index_write_bytes: %s\n" % self.DebugFormatInt32(self.index_write_bytes_))
    if self.has_entity_writes_: res+=prefix+("entity_writes: %s\n" % self.DebugFormatInt32(self.entity_writes_))
    if self.has_entity_write_bytes_: res+=prefix+("entity_write_bytes: %s\n" % self.DebugFormatInt32(self.entity_write_bytes_))
    if self.has_commitcost_:
      res+=prefix+"CommitCost {\n"
      res+=self.commitcost_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
    if self.has_approximate_storage_delta_: res+=prefix+("approximate_storage_delta: %s\n" % self.DebugFormatInt32(self.approximate_storage_delta_))
    if self.has_id_sequence_updates_: res+=prefix+("id_sequence_updates: %s\n" % self.DebugFormatInt32(self.id_sequence_updates_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kindex_writes = 1
  kindex_write_bytes = 2
  kentity_writes = 3
  kentity_write_bytes = 4
  kCommitCostGroup = 5
  kCommitCostrequested_entity_puts = 6
  kCommitCostrequested_entity_deletes = 7
  kapproximate_storage_delta = 8
  kid_sequence_updates = 9

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "index_writes",
    2: "index_write_bytes",
    3: "entity_writes",
    4: "entity_write_bytes",
    5: "CommitCost",
    6: "requested_entity_puts",
    7: "requested_entity_deletes",
    8: "approximate_storage_delta",
    9: "id_sequence_updates",
  }, 9)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STARTGROUP,
    6: ProtocolBuffer.Encoder.NUMERIC,
    7: ProtocolBuffer.Encoder.NUMERIC,
    8: ProtocolBuffer.Encoder.NUMERIC,
    9: ProtocolBuffer.Encoder.NUMERIC,
  }, 9, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.Cost'
class GetRequest(ProtocolBuffer.ProtocolMessage):
  has_transaction_ = 0
  transaction_ = None
  has_failover_ms_ = 0
  failover_ms_ = 0
  has_strong_ = 0
  strong_ = 0
  has_allow_deferred_ = 0
  allow_deferred_ = 0

  def __init__(self, contents=None):
    self.key_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def key_size(self): return len(self.key_)
  def key_list(self): return self.key_

  def key(self, i):
    return self.key_[i]

  def mutable_key(self, i):
    return self.key_[i]

  def add_key(self):
    x = Reference()
    self.key_.append(x)
    return x

  def clear_key(self):
    self.key_ = []
  def transaction(self):
    if self.transaction_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.transaction_ is None: self.transaction_ = Transaction()
      finally:
        self.lazy_init_lock_.release()
    return self.transaction_

  def mutable_transaction(self): self.has_transaction_ = 1; return self.transaction()

  def clear_transaction(self):

    if self.has_transaction_:
      self.has_transaction_ = 0;
      if self.transaction_ is not None: self.transaction_.Clear()

  def has_transaction(self): return self.has_transaction_

  def failover_ms(self): return self.failover_ms_

  def set_failover_ms(self, x):
    self.has_failover_ms_ = 1
    self.failover_ms_ = x

  def clear_failover_ms(self):
    if self.has_failover_ms_:
      self.has_failover_ms_ = 0
      self.failover_ms_ = 0

  def has_failover_ms(self): return self.has_failover_ms_

  def strong(self): return self.strong_

  def set_strong(self, x):
    self.has_strong_ = 1
    self.strong_ = x

  def clear_strong(self):
    if self.has_strong_:
      self.has_strong_ = 0
      self.strong_ = 0

  def has_strong(self): return self.has_strong_

  def allow_deferred(self): return self.allow_deferred_

  def set_allow_deferred(self, x):
    self.has_allow_deferred_ = 1
    self.allow_deferred_ = x

  def clear_allow_deferred(self):
    if self.has_allow_deferred_:
      self.has_allow_deferred_ = 0
      self.allow_deferred_ = 0

  def has_allow_deferred(self): return self.has_allow_deferred_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.key_size()): self.add_key().CopyFrom(x.key(i))
    if (x.has_transaction()): self.mutable_transaction().MergeFrom(x.transaction())
    if (x.has_failover_ms()): self.set_failover_ms(x.failover_ms())
    if (x.has_strong()): self.set_strong(x.strong())
    if (x.has_allow_deferred()): self.set_allow_deferred(x.allow_deferred())

  def Equals(self, x):
    if x is self: return 1
    if len(self.key_) != len(x.key_): return 0
    for e1, e2 in zip(self.key_, x.key_):
      if e1 != e2: return 0
    if self.has_transaction_ != x.has_transaction_: return 0
    if self.has_transaction_ and self.transaction_ != x.transaction_: return 0
    if self.has_failover_ms_ != x.has_failover_ms_: return 0
    if self.has_failover_ms_ and self.failover_ms_ != x.failover_ms_: return 0
    if self.has_strong_ != x.has_strong_: return 0
    if self.has_strong_ and self.strong_ != x.strong_: return 0
    if self.has_allow_deferred_ != x.has_allow_deferred_: return 0
    if self.has_allow_deferred_ and self.allow_deferred_ != x.allow_deferred_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.key_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_transaction_ and not self.transaction_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.key_)
    for i in xrange(len(self.key_)): n += self.lengthString(self.key_[i].ByteSize())
    if (self.has_transaction_): n += 1 + self.lengthString(self.transaction_.ByteSize())
    if (self.has_failover_ms_): n += 1 + self.lengthVarInt64(self.failover_ms_)
    if (self.has_strong_): n += 2
    if (self.has_allow_deferred_): n += 2
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.key_)
    for i in xrange(len(self.key_)): n += self.lengthString(self.key_[i].ByteSizePartial())
    if (self.has_transaction_): n += 1 + self.lengthString(self.transaction_.ByteSizePartial())
    if (self.has_failover_ms_): n += 1 + self.lengthVarInt64(self.failover_ms_)
    if (self.has_strong_): n += 2
    if (self.has_allow_deferred_): n += 2
    return n

  def Clear(self):
    self.clear_key()
    self.clear_transaction()
    self.clear_failover_ms()
    self.clear_strong()
    self.clear_allow_deferred()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.key_)):
      out.putVarInt32(10)
      out.putVarInt32(self.key_[i].ByteSize())
      self.key_[i].OutputUnchecked(out)
    if (self.has_transaction_):
      out.putVarInt32(18)
      out.putVarInt32(self.transaction_.ByteSize())
      self.transaction_.OutputUnchecked(out)
    if (self.has_failover_ms_):
      out.putVarInt32(24)
      out.putVarInt64(self.failover_ms_)
    if (self.has_strong_):
      out.putVarInt32(32)
      out.putBoolean(self.strong_)
    if (self.has_allow_deferred_):
      out.putVarInt32(40)
      out.putBoolean(self.allow_deferred_)

  def OutputPartial(self, out):
    for i in xrange(len(self.key_)):
      out.putVarInt32(10)
      out.putVarInt32(self.key_[i].ByteSizePartial())
      self.key_[i].OutputPartial(out)
    if (self.has_transaction_):
      out.putVarInt32(18)
      out.putVarInt32(self.transaction_.ByteSizePartial())
      self.transaction_.OutputPartial(out)
    if (self.has_failover_ms_):
      out.putVarInt32(24)
      out.putVarInt64(self.failover_ms_)
    if (self.has_strong_):
      out.putVarInt32(32)
      out.putBoolean(self.strong_)
    if (self.has_allow_deferred_):
      out.putVarInt32(40)
      out.putBoolean(self.allow_deferred_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_key().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_transaction().TryMerge(tmp)
        continue
      if tt == 24:
        self.set_failover_ms(d.getVarInt64())
        continue
      if tt == 32:
        self.set_strong(d.getBoolean())
        continue
      if tt == 40:
        self.set_allow_deferred(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.key_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("key%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_transaction_:
      res+=prefix+"transaction <\n"
      res+=self.transaction_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_failover_ms_: res+=prefix+("failover_ms: %s\n" % self.DebugFormatInt64(self.failover_ms_))
    if self.has_strong_: res+=prefix+("strong: %s\n" % self.DebugFormatBool(self.strong_))
    if self.has_allow_deferred_: res+=prefix+("allow_deferred: %s\n" % self.DebugFormatBool(self.allow_deferred_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kkey = 1
  ktransaction = 2
  kfailover_ms = 3
  kstrong = 4
  kallow_deferred = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "key",
    2: "transaction",
    3: "failover_ms",
    4: "strong",
    5: "allow_deferred",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.NUMERIC,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.GetRequest'
class GetResponse_Entity(ProtocolBuffer.ProtocolMessage):
  has_entity_ = 0
  entity_ = None
  has_key_ = 0
  key_ = None
  has_version_ = 0
  version_ = 0

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def entity(self):
    if self.entity_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.entity_ is None: self.entity_ = EntityProto()
      finally:
        self.lazy_init_lock_.release()
    return self.entity_

  def mutable_entity(self): self.has_entity_ = 1; return self.entity()

  def clear_entity(self):

    if self.has_entity_:
      self.has_entity_ = 0;
      if self.entity_ is not None: self.entity_.Clear()

  def has_entity(self): return self.has_entity_

  def key(self):
    if self.key_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.key_ is None: self.key_ = Reference()
      finally:
        self.lazy_init_lock_.release()
    return self.key_

  def mutable_key(self): self.has_key_ = 1; return self.key()

  def clear_key(self):

    if self.has_key_:
      self.has_key_ = 0;
      if self.key_ is not None: self.key_.Clear()

  def has_key(self): return self.has_key_

  def version(self): return self.version_

  def set_version(self, x):
    self.has_version_ = 1
    self.version_ = x

  def clear_version(self):
    if self.has_version_:
      self.has_version_ = 0
      self.version_ = 0

  def has_version(self): return self.has_version_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_entity()): self.mutable_entity().MergeFrom(x.entity())
    if (x.has_key()): self.mutable_key().MergeFrom(x.key())
    if (x.has_version()): self.set_version(x.version())

  def Equals(self, x):
    if x is self: return 1
    if self.has_entity_ != x.has_entity_: return 0
    if self.has_entity_ and self.entity_ != x.entity_: return 0
    if self.has_key_ != x.has_key_: return 0
    if self.has_key_ and self.key_ != x.key_: return 0
    if self.has_version_ != x.has_version_: return 0
    if self.has_version_ and self.version_ != x.version_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_entity_ and not self.entity_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_key_ and not self.key_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_entity_): n += 1 + self.lengthString(self.entity_.ByteSize())
    if (self.has_key_): n += 1 + self.lengthString(self.key_.ByteSize())
    if (self.has_version_): n += 1 + self.lengthVarInt64(self.version_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_entity_): n += 1 + self.lengthString(self.entity_.ByteSizePartial())
    if (self.has_key_): n += 1 + self.lengthString(self.key_.ByteSizePartial())
    if (self.has_version_): n += 1 + self.lengthVarInt64(self.version_)
    return n

  def Clear(self):
    self.clear_entity()
    self.clear_key()
    self.clear_version()

  def OutputUnchecked(self, out):
    if (self.has_entity_):
      out.putVarInt32(18)
      out.putVarInt32(self.entity_.ByteSize())
      self.entity_.OutputUnchecked(out)
    if (self.has_version_):
      out.putVarInt32(24)
      out.putVarInt64(self.version_)
    if (self.has_key_):
      out.putVarInt32(34)
      out.putVarInt32(self.key_.ByteSize())
      self.key_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_entity_):
      out.putVarInt32(18)
      out.putVarInt32(self.entity_.ByteSizePartial())
      self.entity_.OutputPartial(out)
    if (self.has_version_):
      out.putVarInt32(24)
      out.putVarInt64(self.version_)
    if (self.has_key_):
      out.putVarInt32(34)
      out.putVarInt32(self.key_.ByteSizePartial())
      self.key_.OutputPartial(out)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 12: break
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_entity().TryMerge(tmp)
        continue
      if tt == 24:
        self.set_version(d.getVarInt64())
        continue
      if tt == 34:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_key().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_entity_:
      res+=prefix+"entity <\n"
      res+=self.entity_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_key_:
      res+=prefix+"key <\n"
      res+=self.key_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_version_: res+=prefix+("version: %s\n" % self.DebugFormatInt64(self.version_))
    return res

class GetResponse(ProtocolBuffer.ProtocolMessage):
  has_in_order_ = 0
  in_order_ = 1

  def __init__(self, contents=None):
    self.entity_ = []
    self.deferred_ = []
    if contents is not None: self.MergeFromString(contents)

  def entity_size(self): return len(self.entity_)
  def entity_list(self): return self.entity_

  def entity(self, i):
    return self.entity_[i]

  def mutable_entity(self, i):
    return self.entity_[i]

  def add_entity(self):
    x = GetResponse_Entity()
    self.entity_.append(x)
    return x

  def clear_entity(self):
    self.entity_ = []
  def deferred_size(self): return len(self.deferred_)
  def deferred_list(self): return self.deferred_

  def deferred(self, i):
    return self.deferred_[i]

  def mutable_deferred(self, i):
    return self.deferred_[i]

  def add_deferred(self):
    x = Reference()
    self.deferred_.append(x)
    return x

  def clear_deferred(self):
    self.deferred_ = []
  def in_order(self): return self.in_order_

  def set_in_order(self, x):
    self.has_in_order_ = 1
    self.in_order_ = x

  def clear_in_order(self):
    if self.has_in_order_:
      self.has_in_order_ = 0
      self.in_order_ = 1

  def has_in_order(self): return self.has_in_order_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.entity_size()): self.add_entity().CopyFrom(x.entity(i))
    for i in xrange(x.deferred_size()): self.add_deferred().CopyFrom(x.deferred(i))
    if (x.has_in_order()): self.set_in_order(x.in_order())

  def Equals(self, x):
    if x is self: return 1
    if len(self.entity_) != len(x.entity_): return 0
    for e1, e2 in zip(self.entity_, x.entity_):
      if e1 != e2: return 0
    if len(self.deferred_) != len(x.deferred_): return 0
    for e1, e2 in zip(self.deferred_, x.deferred_):
      if e1 != e2: return 0
    if self.has_in_order_ != x.has_in_order_: return 0
    if self.has_in_order_ and self.in_order_ != x.in_order_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.entity_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.deferred_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 2 * len(self.entity_)
    for i in xrange(len(self.entity_)): n += self.entity_[i].ByteSize()
    n += 1 * len(self.deferred_)
    for i in xrange(len(self.deferred_)): n += self.lengthString(self.deferred_[i].ByteSize())
    if (self.has_in_order_): n += 2
    return n

  def ByteSizePartial(self):
    n = 0
    n += 2 * len(self.entity_)
    for i in xrange(len(self.entity_)): n += self.entity_[i].ByteSizePartial()
    n += 1 * len(self.deferred_)
    for i in xrange(len(self.deferred_)): n += self.lengthString(self.deferred_[i].ByteSizePartial())
    if (self.has_in_order_): n += 2
    return n

  def Clear(self):
    self.clear_entity()
    self.clear_deferred()
    self.clear_in_order()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.entity_)):
      out.putVarInt32(11)
      self.entity_[i].OutputUnchecked(out)
      out.putVarInt32(12)
    for i in xrange(len(self.deferred_)):
      out.putVarInt32(42)
      out.putVarInt32(self.deferred_[i].ByteSize())
      self.deferred_[i].OutputUnchecked(out)
    if (self.has_in_order_):
      out.putVarInt32(48)
      out.putBoolean(self.in_order_)

  def OutputPartial(self, out):
    for i in xrange(len(self.entity_)):
      out.putVarInt32(11)
      self.entity_[i].OutputPartial(out)
      out.putVarInt32(12)
    for i in xrange(len(self.deferred_)):
      out.putVarInt32(42)
      out.putVarInt32(self.deferred_[i].ByteSizePartial())
      self.deferred_[i].OutputPartial(out)
    if (self.has_in_order_):
      out.putVarInt32(48)
      out.putBoolean(self.in_order_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 11:
        self.add_entity().TryMerge(d)
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_deferred().TryMerge(tmp)
        continue
      if tt == 48:
        self.set_in_order(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.entity_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Entity%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    cnt=0
    for e in self.deferred_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("deferred%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_in_order_: res+=prefix+("in_order: %s\n" % self.DebugFormatBool(self.in_order_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kEntityGroup = 1
  kEntityentity = 2
  kEntitykey = 4
  kEntityversion = 3
  kdeferred = 5
  kin_order = 6

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "Entity",
    2: "entity",
    3: "version",
    4: "key",
    5: "deferred",
    6: "in_order",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STARTGROUP,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.NUMERIC,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.GetResponse'
class PutRequest(ProtocolBuffer.ProtocolMessage):


  CURRENT      =    0
  SEQUENTIAL   =    1

  _AutoIdPolicy_NAMES = {
    0: "CURRENT",
    1: "SEQUENTIAL",
  }

  def AutoIdPolicy_Name(cls, x): return cls._AutoIdPolicy_NAMES.get(x, "")
  AutoIdPolicy_Name = classmethod(AutoIdPolicy_Name)

  has_transaction_ = 0
  transaction_ = None
  has_trusted_ = 0
  trusted_ = 0
  has_force_ = 0
  force_ = 0
  has_mark_changes_ = 0
  mark_changes_ = 0
  has_auto_id_policy_ = 0
  auto_id_policy_ = 0

  def __init__(self, contents=None):
    self.entity_ = []
    self.composite_index_ = []
    self.snapshot_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def entity_size(self): return len(self.entity_)
  def entity_list(self): return self.entity_

  def entity(self, i):
    return self.entity_[i]

  def mutable_entity(self, i):
    return self.entity_[i]

  def add_entity(self):
    x = EntityProto()
    self.entity_.append(x)
    return x

  def clear_entity(self):
    self.entity_ = []
  def transaction(self):
    if self.transaction_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.transaction_ is None: self.transaction_ = Transaction()
      finally:
        self.lazy_init_lock_.release()
    return self.transaction_

  def mutable_transaction(self): self.has_transaction_ = 1; return self.transaction()

  def clear_transaction(self):

    if self.has_transaction_:
      self.has_transaction_ = 0;
      if self.transaction_ is not None: self.transaction_.Clear()

  def has_transaction(self): return self.has_transaction_

  def composite_index_size(self): return len(self.composite_index_)
  def composite_index_list(self): return self.composite_index_

  def composite_index(self, i):
    return self.composite_index_[i]

  def mutable_composite_index(self, i):
    return self.composite_index_[i]

  def add_composite_index(self):
    x = CompositeIndex()
    self.composite_index_.append(x)
    return x

  def clear_composite_index(self):
    self.composite_index_ = []
  def trusted(self): return self.trusted_

  def set_trusted(self, x):
    self.has_trusted_ = 1
    self.trusted_ = x

  def clear_trusted(self):
    if self.has_trusted_:
      self.has_trusted_ = 0
      self.trusted_ = 0

  def has_trusted(self): return self.has_trusted_

  def force(self): return self.force_

  def set_force(self, x):
    self.has_force_ = 1
    self.force_ = x

  def clear_force(self):
    if self.has_force_:
      self.has_force_ = 0
      self.force_ = 0

  def has_force(self): return self.has_force_

  def mark_changes(self): return self.mark_changes_

  def set_mark_changes(self, x):
    self.has_mark_changes_ = 1
    self.mark_changes_ = x

  def clear_mark_changes(self):
    if self.has_mark_changes_:
      self.has_mark_changes_ = 0
      self.mark_changes_ = 0

  def has_mark_changes(self): return self.has_mark_changes_

  def snapshot_size(self): return len(self.snapshot_)
  def snapshot_list(self): return self.snapshot_

  def snapshot(self, i):
    return self.snapshot_[i]

  def mutable_snapshot(self, i):
    return self.snapshot_[i]

  def add_snapshot(self):
    x = Snapshot()
    self.snapshot_.append(x)
    return x

  def clear_snapshot(self):
    self.snapshot_ = []
  def auto_id_policy(self): return self.auto_id_policy_

  def set_auto_id_policy(self, x):
    self.has_auto_id_policy_ = 1
    self.auto_id_policy_ = x

  def clear_auto_id_policy(self):
    if self.has_auto_id_policy_:
      self.has_auto_id_policy_ = 0
      self.auto_id_policy_ = 0

  def has_auto_id_policy(self): return self.has_auto_id_policy_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.entity_size()): self.add_entity().CopyFrom(x.entity(i))
    if (x.has_transaction()): self.mutable_transaction().MergeFrom(x.transaction())
    for i in xrange(x.composite_index_size()): self.add_composite_index().CopyFrom(x.composite_index(i))
    if (x.has_trusted()): self.set_trusted(x.trusted())
    if (x.has_force()): self.set_force(x.force())
    if (x.has_mark_changes()): self.set_mark_changes(x.mark_changes())
    for i in xrange(x.snapshot_size()): self.add_snapshot().CopyFrom(x.snapshot(i))
    if (x.has_auto_id_policy()): self.set_auto_id_policy(x.auto_id_policy())

  def Equals(self, x):
    if x is self: return 1
    if len(self.entity_) != len(x.entity_): return 0
    for e1, e2 in zip(self.entity_, x.entity_):
      if e1 != e2: return 0
    if self.has_transaction_ != x.has_transaction_: return 0
    if self.has_transaction_ and self.transaction_ != x.transaction_: return 0
    if len(self.composite_index_) != len(x.composite_index_): return 0
    for e1, e2 in zip(self.composite_index_, x.composite_index_):
      if e1 != e2: return 0
    if self.has_trusted_ != x.has_trusted_: return 0
    if self.has_trusted_ and self.trusted_ != x.trusted_: return 0
    if self.has_force_ != x.has_force_: return 0
    if self.has_force_ and self.force_ != x.force_: return 0
    if self.has_mark_changes_ != x.has_mark_changes_: return 0
    if self.has_mark_changes_ and self.mark_changes_ != x.mark_changes_: return 0
    if len(self.snapshot_) != len(x.snapshot_): return 0
    for e1, e2 in zip(self.snapshot_, x.snapshot_):
      if e1 != e2: return 0
    if self.has_auto_id_policy_ != x.has_auto_id_policy_: return 0
    if self.has_auto_id_policy_ and self.auto_id_policy_ != x.auto_id_policy_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.entity_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_transaction_ and not self.transaction_.IsInitialized(debug_strs)): initialized = 0
    for p in self.composite_index_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.snapshot_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.entity_)
    for i in xrange(len(self.entity_)): n += self.lengthString(self.entity_[i].ByteSize())
    if (self.has_transaction_): n += 1 + self.lengthString(self.transaction_.ByteSize())
    n += 1 * len(self.composite_index_)
    for i in xrange(len(self.composite_index_)): n += self.lengthString(self.composite_index_[i].ByteSize())
    if (self.has_trusted_): n += 2
    if (self.has_force_): n += 2
    if (self.has_mark_changes_): n += 2
    n += 1 * len(self.snapshot_)
    for i in xrange(len(self.snapshot_)): n += self.lengthString(self.snapshot_[i].ByteSize())
    if (self.has_auto_id_policy_): n += 1 + self.lengthVarInt64(self.auto_id_policy_)
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.entity_)
    for i in xrange(len(self.entity_)): n += self.lengthString(self.entity_[i].ByteSizePartial())
    if (self.has_transaction_): n += 1 + self.lengthString(self.transaction_.ByteSizePartial())
    n += 1 * len(self.composite_index_)
    for i in xrange(len(self.composite_index_)): n += self.lengthString(self.composite_index_[i].ByteSizePartial())
    if (self.has_trusted_): n += 2
    if (self.has_force_): n += 2
    if (self.has_mark_changes_): n += 2
    n += 1 * len(self.snapshot_)
    for i in xrange(len(self.snapshot_)): n += self.lengthString(self.snapshot_[i].ByteSizePartial())
    if (self.has_auto_id_policy_): n += 1 + self.lengthVarInt64(self.auto_id_policy_)
    return n

  def Clear(self):
    self.clear_entity()
    self.clear_transaction()
    self.clear_composite_index()
    self.clear_trusted()
    self.clear_force()
    self.clear_mark_changes()
    self.clear_snapshot()
    self.clear_auto_id_policy()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.entity_)):
      out.putVarInt32(10)
      out.putVarInt32(self.entity_[i].ByteSize())
      self.entity_[i].OutputUnchecked(out)
    if (self.has_transaction_):
      out.putVarInt32(18)
      out.putVarInt32(self.transaction_.ByteSize())
      self.transaction_.OutputUnchecked(out)
    for i in xrange(len(self.composite_index_)):
      out.putVarInt32(26)
      out.putVarInt32(self.composite_index_[i].ByteSize())
      self.composite_index_[i].OutputUnchecked(out)
    if (self.has_trusted_):
      out.putVarInt32(32)
      out.putBoolean(self.trusted_)
    if (self.has_force_):
      out.putVarInt32(56)
      out.putBoolean(self.force_)
    if (self.has_mark_changes_):
      out.putVarInt32(64)
      out.putBoolean(self.mark_changes_)
    for i in xrange(len(self.snapshot_)):
      out.putVarInt32(74)
      out.putVarInt32(self.snapshot_[i].ByteSize())
      self.snapshot_[i].OutputUnchecked(out)
    if (self.has_auto_id_policy_):
      out.putVarInt32(80)
      out.putVarInt32(self.auto_id_policy_)

  def OutputPartial(self, out):
    for i in xrange(len(self.entity_)):
      out.putVarInt32(10)
      out.putVarInt32(self.entity_[i].ByteSizePartial())
      self.entity_[i].OutputPartial(out)
    if (self.has_transaction_):
      out.putVarInt32(18)
      out.putVarInt32(self.transaction_.ByteSizePartial())
      self.transaction_.OutputPartial(out)
    for i in xrange(len(self.composite_index_)):
      out.putVarInt32(26)
      out.putVarInt32(self.composite_index_[i].ByteSizePartial())
      self.composite_index_[i].OutputPartial(out)
    if (self.has_trusted_):
      out.putVarInt32(32)
      out.putBoolean(self.trusted_)
    if (self.has_force_):
      out.putVarInt32(56)
      out.putBoolean(self.force_)
    if (self.has_mark_changes_):
      out.putVarInt32(64)
      out.putBoolean(self.mark_changes_)
    for i in xrange(len(self.snapshot_)):
      out.putVarInt32(74)
      out.putVarInt32(self.snapshot_[i].ByteSizePartial())
      self.snapshot_[i].OutputPartial(out)
    if (self.has_auto_id_policy_):
      out.putVarInt32(80)
      out.putVarInt32(self.auto_id_policy_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_entity().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_transaction().TryMerge(tmp)
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_composite_index().TryMerge(tmp)
        continue
      if tt == 32:
        self.set_trusted(d.getBoolean())
        continue
      if tt == 56:
        self.set_force(d.getBoolean())
        continue
      if tt == 64:
        self.set_mark_changes(d.getBoolean())
        continue
      if tt == 74:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_snapshot().TryMerge(tmp)
        continue
      if tt == 80:
        self.set_auto_id_policy(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.entity_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("entity%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_transaction_:
      res+=prefix+"transaction <\n"
      res+=self.transaction_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.composite_index_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("composite_index%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_trusted_: res+=prefix+("trusted: %s\n" % self.DebugFormatBool(self.trusted_))
    if self.has_force_: res+=prefix+("force: %s\n" % self.DebugFormatBool(self.force_))
    if self.has_mark_changes_: res+=prefix+("mark_changes: %s\n" % self.DebugFormatBool(self.mark_changes_))
    cnt=0
    for e in self.snapshot_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("snapshot%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_auto_id_policy_: res+=prefix+("auto_id_policy: %s\n" % self.DebugFormatInt32(self.auto_id_policy_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kentity = 1
  ktransaction = 2
  kcomposite_index = 3
  ktrusted = 4
  kforce = 7
  kmark_changes = 8
  ksnapshot = 9
  kauto_id_policy = 10

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "entity",
    2: "transaction",
    3: "composite_index",
    4: "trusted",
    7: "force",
    8: "mark_changes",
    9: "snapshot",
    10: "auto_id_policy",
  }, 10)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
    7: ProtocolBuffer.Encoder.NUMERIC,
    8: ProtocolBuffer.Encoder.NUMERIC,
    9: ProtocolBuffer.Encoder.STRING,
    10: ProtocolBuffer.Encoder.NUMERIC,
  }, 10, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.PutRequest'
class PutResponse(ProtocolBuffer.ProtocolMessage):
  has_cost_ = 0
  cost_ = None

  def __init__(self, contents=None):
    self.key_ = []
    self.version_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def key_size(self): return len(self.key_)
  def key_list(self): return self.key_

  def key(self, i):
    return self.key_[i]

  def mutable_key(self, i):
    return self.key_[i]

  def add_key(self):
    x = Reference()
    self.key_.append(x)
    return x

  def clear_key(self):
    self.key_ = []
  def cost(self):
    if self.cost_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.cost_ is None: self.cost_ = Cost()
      finally:
        self.lazy_init_lock_.release()
    return self.cost_

  def mutable_cost(self): self.has_cost_ = 1; return self.cost()

  def clear_cost(self):

    if self.has_cost_:
      self.has_cost_ = 0;
      if self.cost_ is not None: self.cost_.Clear()

  def has_cost(self): return self.has_cost_

  def version_size(self): return len(self.version_)
  def version_list(self): return self.version_

  def version(self, i):
    return self.version_[i]

  def set_version(self, i, x):
    self.version_[i] = x

  def add_version(self, x):
    self.version_.append(x)

  def clear_version(self):
    self.version_ = []


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.key_size()): self.add_key().CopyFrom(x.key(i))
    if (x.has_cost()): self.mutable_cost().MergeFrom(x.cost())
    for i in xrange(x.version_size()): self.add_version(x.version(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.key_) != len(x.key_): return 0
    for e1, e2 in zip(self.key_, x.key_):
      if e1 != e2: return 0
    if self.has_cost_ != x.has_cost_: return 0
    if self.has_cost_ and self.cost_ != x.cost_: return 0
    if len(self.version_) != len(x.version_): return 0
    for e1, e2 in zip(self.version_, x.version_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.key_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_cost_ and not self.cost_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.key_)
    for i in xrange(len(self.key_)): n += self.lengthString(self.key_[i].ByteSize())
    if (self.has_cost_): n += 1 + self.lengthString(self.cost_.ByteSize())
    n += 1 * len(self.version_)
    for i in xrange(len(self.version_)): n += self.lengthVarInt64(self.version_[i])
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.key_)
    for i in xrange(len(self.key_)): n += self.lengthString(self.key_[i].ByteSizePartial())
    if (self.has_cost_): n += 1 + self.lengthString(self.cost_.ByteSizePartial())
    n += 1 * len(self.version_)
    for i in xrange(len(self.version_)): n += self.lengthVarInt64(self.version_[i])
    return n

  def Clear(self):
    self.clear_key()
    self.clear_cost()
    self.clear_version()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.key_)):
      out.putVarInt32(10)
      out.putVarInt32(self.key_[i].ByteSize())
      self.key_[i].OutputUnchecked(out)
    if (self.has_cost_):
      out.putVarInt32(18)
      out.putVarInt32(self.cost_.ByteSize())
      self.cost_.OutputUnchecked(out)
    for i in xrange(len(self.version_)):
      out.putVarInt32(24)
      out.putVarInt64(self.version_[i])

  def OutputPartial(self, out):
    for i in xrange(len(self.key_)):
      out.putVarInt32(10)
      out.putVarInt32(self.key_[i].ByteSizePartial())
      self.key_[i].OutputPartial(out)
    if (self.has_cost_):
      out.putVarInt32(18)
      out.putVarInt32(self.cost_.ByteSizePartial())
      self.cost_.OutputPartial(out)
    for i in xrange(len(self.version_)):
      out.putVarInt32(24)
      out.putVarInt64(self.version_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_key().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_cost().TryMerge(tmp)
        continue
      if tt == 24:
        self.add_version(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.key_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("key%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_cost_:
      res+=prefix+"cost <\n"
      res+=self.cost_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.version_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("version%s: %s\n" % (elm, self.DebugFormatInt64(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kkey = 1
  kcost = 2
  kversion = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "key",
    2: "cost",
    3: "version",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.PutResponse'
class TouchRequest(ProtocolBuffer.ProtocolMessage):
  has_force_ = 0
  force_ = 0

  def __init__(self, contents=None):
    self.key_ = []
    self.composite_index_ = []
    self.snapshot_ = []
    if contents is not None: self.MergeFromString(contents)

  def key_size(self): return len(self.key_)
  def key_list(self): return self.key_

  def key(self, i):
    return self.key_[i]

  def mutable_key(self, i):
    return self.key_[i]

  def add_key(self):
    x = Reference()
    self.key_.append(x)
    return x

  def clear_key(self):
    self.key_ = []
  def composite_index_size(self): return len(self.composite_index_)
  def composite_index_list(self): return self.composite_index_

  def composite_index(self, i):
    return self.composite_index_[i]

  def mutable_composite_index(self, i):
    return self.composite_index_[i]

  def add_composite_index(self):
    x = CompositeIndex()
    self.composite_index_.append(x)
    return x

  def clear_composite_index(self):
    self.composite_index_ = []
  def force(self): return self.force_

  def set_force(self, x):
    self.has_force_ = 1
    self.force_ = x

  def clear_force(self):
    if self.has_force_:
      self.has_force_ = 0
      self.force_ = 0

  def has_force(self): return self.has_force_

  def snapshot_size(self): return len(self.snapshot_)
  def snapshot_list(self): return self.snapshot_

  def snapshot(self, i):
    return self.snapshot_[i]

  def mutable_snapshot(self, i):
    return self.snapshot_[i]

  def add_snapshot(self):
    x = Snapshot()
    self.snapshot_.append(x)
    return x

  def clear_snapshot(self):
    self.snapshot_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.key_size()): self.add_key().CopyFrom(x.key(i))
    for i in xrange(x.composite_index_size()): self.add_composite_index().CopyFrom(x.composite_index(i))
    if (x.has_force()): self.set_force(x.force())
    for i in xrange(x.snapshot_size()): self.add_snapshot().CopyFrom(x.snapshot(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.key_) != len(x.key_): return 0
    for e1, e2 in zip(self.key_, x.key_):
      if e1 != e2: return 0
    if len(self.composite_index_) != len(x.composite_index_): return 0
    for e1, e2 in zip(self.composite_index_, x.composite_index_):
      if e1 != e2: return 0
    if self.has_force_ != x.has_force_: return 0
    if self.has_force_ and self.force_ != x.force_: return 0
    if len(self.snapshot_) != len(x.snapshot_): return 0
    for e1, e2 in zip(self.snapshot_, x.snapshot_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.key_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.composite_index_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.snapshot_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.key_)
    for i in xrange(len(self.key_)): n += self.lengthString(self.key_[i].ByteSize())
    n += 1 * len(self.composite_index_)
    for i in xrange(len(self.composite_index_)): n += self.lengthString(self.composite_index_[i].ByteSize())
    if (self.has_force_): n += 2
    n += 1 * len(self.snapshot_)
    for i in xrange(len(self.snapshot_)): n += self.lengthString(self.snapshot_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.key_)
    for i in xrange(len(self.key_)): n += self.lengthString(self.key_[i].ByteSizePartial())
    n += 1 * len(self.composite_index_)
    for i in xrange(len(self.composite_index_)): n += self.lengthString(self.composite_index_[i].ByteSizePartial())
    if (self.has_force_): n += 2
    n += 1 * len(self.snapshot_)
    for i in xrange(len(self.snapshot_)): n += self.lengthString(self.snapshot_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_key()
    self.clear_composite_index()
    self.clear_force()
    self.clear_snapshot()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.key_)):
      out.putVarInt32(10)
      out.putVarInt32(self.key_[i].ByteSize())
      self.key_[i].OutputUnchecked(out)
    for i in xrange(len(self.composite_index_)):
      out.putVarInt32(18)
      out.putVarInt32(self.composite_index_[i].ByteSize())
      self.composite_index_[i].OutputUnchecked(out)
    if (self.has_force_):
      out.putVarInt32(24)
      out.putBoolean(self.force_)
    for i in xrange(len(self.snapshot_)):
      out.putVarInt32(74)
      out.putVarInt32(self.snapshot_[i].ByteSize())
      self.snapshot_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.key_)):
      out.putVarInt32(10)
      out.putVarInt32(self.key_[i].ByteSizePartial())
      self.key_[i].OutputPartial(out)
    for i in xrange(len(self.composite_index_)):
      out.putVarInt32(18)
      out.putVarInt32(self.composite_index_[i].ByteSizePartial())
      self.composite_index_[i].OutputPartial(out)
    if (self.has_force_):
      out.putVarInt32(24)
      out.putBoolean(self.force_)
    for i in xrange(len(self.snapshot_)):
      out.putVarInt32(74)
      out.putVarInt32(self.snapshot_[i].ByteSizePartial())
      self.snapshot_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_key().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_composite_index().TryMerge(tmp)
        continue
      if tt == 24:
        self.set_force(d.getBoolean())
        continue
      if tt == 74:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_snapshot().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.key_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("key%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.composite_index_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("composite_index%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_force_: res+=prefix+("force: %s\n" % self.DebugFormatBool(self.force_))
    cnt=0
    for e in self.snapshot_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("snapshot%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kkey = 1
  kcomposite_index = 2
  kforce = 3
  ksnapshot = 9

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "key",
    2: "composite_index",
    3: "force",
    9: "snapshot",
  }, 9)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    9: ProtocolBuffer.Encoder.STRING,
  }, 9, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.TouchRequest'
class TouchResponse(ProtocolBuffer.ProtocolMessage):
  has_cost_ = 0
  cost_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def cost(self):
    if self.cost_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.cost_ is None: self.cost_ = Cost()
      finally:
        self.lazy_init_lock_.release()
    return self.cost_

  def mutable_cost(self): self.has_cost_ = 1; return self.cost()

  def clear_cost(self):

    if self.has_cost_:
      self.has_cost_ = 0;
      if self.cost_ is not None: self.cost_.Clear()

  def has_cost(self): return self.has_cost_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_cost()): self.mutable_cost().MergeFrom(x.cost())

  def Equals(self, x):
    if x is self: return 1
    if self.has_cost_ != x.has_cost_: return 0
    if self.has_cost_ and self.cost_ != x.cost_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_cost_ and not self.cost_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_cost_): n += 1 + self.lengthString(self.cost_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_cost_): n += 1 + self.lengthString(self.cost_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_cost()

  def OutputUnchecked(self, out):
    if (self.has_cost_):
      out.putVarInt32(10)
      out.putVarInt32(self.cost_.ByteSize())
      self.cost_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_cost_):
      out.putVarInt32(10)
      out.putVarInt32(self.cost_.ByteSizePartial())
      self.cost_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_cost().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_cost_:
      res+=prefix+"cost <\n"
      res+=self.cost_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kcost = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "cost",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.TouchResponse'
class DeleteRequest(ProtocolBuffer.ProtocolMessage):
  has_transaction_ = 0
  transaction_ = None
  has_trusted_ = 0
  trusted_ = 0
  has_force_ = 0
  force_ = 0
  has_mark_changes_ = 0
  mark_changes_ = 0

  def __init__(self, contents=None):
    self.key_ = []
    self.composite_index_ = []
    self.snapshot_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def key_size(self): return len(self.key_)
  def key_list(self): return self.key_

  def key(self, i):
    return self.key_[i]

  def mutable_key(self, i):
    return self.key_[i]

  def add_key(self):
    x = Reference()
    self.key_.append(x)
    return x

  def clear_key(self):
    self.key_ = []
  def transaction(self):
    if self.transaction_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.transaction_ is None: self.transaction_ = Transaction()
      finally:
        self.lazy_init_lock_.release()
    return self.transaction_

  def mutable_transaction(self): self.has_transaction_ = 1; return self.transaction()

  def clear_transaction(self):

    if self.has_transaction_:
      self.has_transaction_ = 0;
      if self.transaction_ is not None: self.transaction_.Clear()

  def has_transaction(self): return self.has_transaction_

  def composite_index_size(self): return len(self.composite_index_)
  def composite_index_list(self): return self.composite_index_

  def composite_index(self, i):
    return self.composite_index_[i]

  def mutable_composite_index(self, i):
    return self.composite_index_[i]

  def add_composite_index(self):
    x = CompositeIndex()
    self.composite_index_.append(x)
    return x

  def clear_composite_index(self):
    self.composite_index_ = []
  def trusted(self): return self.trusted_

  def set_trusted(self, x):
    self.has_trusted_ = 1
    self.trusted_ = x

  def clear_trusted(self):
    if self.has_trusted_:
      self.has_trusted_ = 0
      self.trusted_ = 0

  def has_trusted(self): return self.has_trusted_

  def force(self): return self.force_

  def set_force(self, x):
    self.has_force_ = 1
    self.force_ = x

  def clear_force(self):
    if self.has_force_:
      self.has_force_ = 0
      self.force_ = 0

  def has_force(self): return self.has_force_

  def mark_changes(self): return self.mark_changes_

  def set_mark_changes(self, x):
    self.has_mark_changes_ = 1
    self.mark_changes_ = x

  def clear_mark_changes(self):
    if self.has_mark_changes_:
      self.has_mark_changes_ = 0
      self.mark_changes_ = 0

  def has_mark_changes(self): return self.has_mark_changes_

  def snapshot_size(self): return len(self.snapshot_)
  def snapshot_list(self): return self.snapshot_

  def snapshot(self, i):
    return self.snapshot_[i]

  def mutable_snapshot(self, i):
    return self.snapshot_[i]

  def add_snapshot(self):
    x = Snapshot()
    self.snapshot_.append(x)
    return x

  def clear_snapshot(self):
    self.snapshot_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.key_size()): self.add_key().CopyFrom(x.key(i))
    if (x.has_transaction()): self.mutable_transaction().MergeFrom(x.transaction())
    for i in xrange(x.composite_index_size()): self.add_composite_index().CopyFrom(x.composite_index(i))
    if (x.has_trusted()): self.set_trusted(x.trusted())
    if (x.has_force()): self.set_force(x.force())
    if (x.has_mark_changes()): self.set_mark_changes(x.mark_changes())
    for i in xrange(x.snapshot_size()): self.add_snapshot().CopyFrom(x.snapshot(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.key_) != len(x.key_): return 0
    for e1, e2 in zip(self.key_, x.key_):
      if e1 != e2: return 0
    if self.has_transaction_ != x.has_transaction_: return 0
    if self.has_transaction_ and self.transaction_ != x.transaction_: return 0
    if len(self.composite_index_) != len(x.composite_index_): return 0
    for e1, e2 in zip(self.composite_index_, x.composite_index_):
      if e1 != e2: return 0
    if self.has_trusted_ != x.has_trusted_: return 0
    if self.has_trusted_ and self.trusted_ != x.trusted_: return 0
    if self.has_force_ != x.has_force_: return 0
    if self.has_force_ and self.force_ != x.force_: return 0
    if self.has_mark_changes_ != x.has_mark_changes_: return 0
    if self.has_mark_changes_ and self.mark_changes_ != x.mark_changes_: return 0
    if len(self.snapshot_) != len(x.snapshot_): return 0
    for e1, e2 in zip(self.snapshot_, x.snapshot_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.key_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_transaction_ and not self.transaction_.IsInitialized(debug_strs)): initialized = 0
    for p in self.composite_index_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.snapshot_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.key_)
    for i in xrange(len(self.key_)): n += self.lengthString(self.key_[i].ByteSize())
    if (self.has_transaction_): n += 1 + self.lengthString(self.transaction_.ByteSize())
    n += 1 * len(self.composite_index_)
    for i in xrange(len(self.composite_index_)): n += self.lengthString(self.composite_index_[i].ByteSize())
    if (self.has_trusted_): n += 2
    if (self.has_force_): n += 2
    if (self.has_mark_changes_): n += 2
    n += 1 * len(self.snapshot_)
    for i in xrange(len(self.snapshot_)): n += self.lengthString(self.snapshot_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.key_)
    for i in xrange(len(self.key_)): n += self.lengthString(self.key_[i].ByteSizePartial())
    if (self.has_transaction_): n += 1 + self.lengthString(self.transaction_.ByteSizePartial())
    n += 1 * len(self.composite_index_)
    for i in xrange(len(self.composite_index_)): n += self.lengthString(self.composite_index_[i].ByteSizePartial())
    if (self.has_trusted_): n += 2
    if (self.has_force_): n += 2
    if (self.has_mark_changes_): n += 2
    n += 1 * len(self.snapshot_)
    for i in xrange(len(self.snapshot_)): n += self.lengthString(self.snapshot_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_key()
    self.clear_transaction()
    self.clear_composite_index()
    self.clear_trusted()
    self.clear_force()
    self.clear_mark_changes()
    self.clear_snapshot()

  def OutputUnchecked(self, out):
    if (self.has_trusted_):
      out.putVarInt32(32)
      out.putBoolean(self.trusted_)
    if (self.has_transaction_):
      out.putVarInt32(42)
      out.putVarInt32(self.transaction_.ByteSize())
      self.transaction_.OutputUnchecked(out)
    for i in xrange(len(self.key_)):
      out.putVarInt32(50)
      out.putVarInt32(self.key_[i].ByteSize())
      self.key_[i].OutputUnchecked(out)
    if (self.has_force_):
      out.putVarInt32(56)
      out.putBoolean(self.force_)
    if (self.has_mark_changes_):
      out.putVarInt32(64)
      out.putBoolean(self.mark_changes_)
    for i in xrange(len(self.snapshot_)):
      out.putVarInt32(74)
      out.putVarInt32(self.snapshot_[i].ByteSize())
      self.snapshot_[i].OutputUnchecked(out)
    for i in xrange(len(self.composite_index_)):
      out.putVarInt32(90)
      out.putVarInt32(self.composite_index_[i].ByteSize())
      self.composite_index_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_trusted_):
      out.putVarInt32(32)
      out.putBoolean(self.trusted_)
    if (self.has_transaction_):
      out.putVarInt32(42)
      out.putVarInt32(self.transaction_.ByteSizePartial())
      self.transaction_.OutputPartial(out)
    for i in xrange(len(self.key_)):
      out.putVarInt32(50)
      out.putVarInt32(self.key_[i].ByteSizePartial())
      self.key_[i].OutputPartial(out)
    if (self.has_force_):
      out.putVarInt32(56)
      out.putBoolean(self.force_)
    if (self.has_mark_changes_):
      out.putVarInt32(64)
      out.putBoolean(self.mark_changes_)
    for i in xrange(len(self.snapshot_)):
      out.putVarInt32(74)
      out.putVarInt32(self.snapshot_[i].ByteSizePartial())
      self.snapshot_[i].OutputPartial(out)
    for i in xrange(len(self.composite_index_)):
      out.putVarInt32(90)
      out.putVarInt32(self.composite_index_[i].ByteSizePartial())
      self.composite_index_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 32:
        self.set_trusted(d.getBoolean())
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_transaction().TryMerge(tmp)
        continue
      if tt == 50:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_key().TryMerge(tmp)
        continue
      if tt == 56:
        self.set_force(d.getBoolean())
        continue
      if tt == 64:
        self.set_mark_changes(d.getBoolean())
        continue
      if tt == 74:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_snapshot().TryMerge(tmp)
        continue
      if tt == 90:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_composite_index().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.key_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("key%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_transaction_:
      res+=prefix+"transaction <\n"
      res+=self.transaction_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.composite_index_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("composite_index%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_trusted_: res+=prefix+("trusted: %s\n" % self.DebugFormatBool(self.trusted_))
    if self.has_force_: res+=prefix+("force: %s\n" % self.DebugFormatBool(self.force_))
    if self.has_mark_changes_: res+=prefix+("mark_changes: %s\n" % self.DebugFormatBool(self.mark_changes_))
    cnt=0
    for e in self.snapshot_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("snapshot%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kkey = 6
  ktransaction = 5
  kcomposite_index = 11
  ktrusted = 4
  kforce = 7
  kmark_changes = 8
  ksnapshot = 9

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    4: "trusted",
    5: "transaction",
    6: "key",
    7: "force",
    8: "mark_changes",
    9: "snapshot",
    11: "composite_index",
  }, 11)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.STRING,
    7: ProtocolBuffer.Encoder.NUMERIC,
    8: ProtocolBuffer.Encoder.NUMERIC,
    9: ProtocolBuffer.Encoder.STRING,
    11: ProtocolBuffer.Encoder.STRING,
  }, 11, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.DeleteRequest'
class DeleteResponse(ProtocolBuffer.ProtocolMessage):
  has_cost_ = 0
  cost_ = None

  def __init__(self, contents=None):
    self.version_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def cost(self):
    if self.cost_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.cost_ is None: self.cost_ = Cost()
      finally:
        self.lazy_init_lock_.release()
    return self.cost_

  def mutable_cost(self): self.has_cost_ = 1; return self.cost()

  def clear_cost(self):

    if self.has_cost_:
      self.has_cost_ = 0;
      if self.cost_ is not None: self.cost_.Clear()

  def has_cost(self): return self.has_cost_

  def version_size(self): return len(self.version_)
  def version_list(self): return self.version_

  def version(self, i):
    return self.version_[i]

  def set_version(self, i, x):
    self.version_[i] = x

  def add_version(self, x):
    self.version_.append(x)

  def clear_version(self):
    self.version_ = []


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_cost()): self.mutable_cost().MergeFrom(x.cost())
    for i in xrange(x.version_size()): self.add_version(x.version(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_cost_ != x.has_cost_: return 0
    if self.has_cost_ and self.cost_ != x.cost_: return 0
    if len(self.version_) != len(x.version_): return 0
    for e1, e2 in zip(self.version_, x.version_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_cost_ and not self.cost_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_cost_): n += 1 + self.lengthString(self.cost_.ByteSize())
    n += 1 * len(self.version_)
    for i in xrange(len(self.version_)): n += self.lengthVarInt64(self.version_[i])
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_cost_): n += 1 + self.lengthString(self.cost_.ByteSizePartial())
    n += 1 * len(self.version_)
    for i in xrange(len(self.version_)): n += self.lengthVarInt64(self.version_[i])
    return n

  def Clear(self):
    self.clear_cost()
    self.clear_version()

  def OutputUnchecked(self, out):
    if (self.has_cost_):
      out.putVarInt32(10)
      out.putVarInt32(self.cost_.ByteSize())
      self.cost_.OutputUnchecked(out)
    for i in xrange(len(self.version_)):
      out.putVarInt32(24)
      out.putVarInt64(self.version_[i])

  def OutputPartial(self, out):
    if (self.has_cost_):
      out.putVarInt32(10)
      out.putVarInt32(self.cost_.ByteSizePartial())
      self.cost_.OutputPartial(out)
    for i in xrange(len(self.version_)):
      out.putVarInt32(24)
      out.putVarInt64(self.version_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_cost().TryMerge(tmp)
        continue
      if tt == 24:
        self.add_version(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_cost_:
      res+=prefix+"cost <\n"
      res+=self.cost_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.version_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("version%s: %s\n" % (elm, self.DebugFormatInt64(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kcost = 1
  kversion = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "cost",
    3: "version",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.DeleteResponse'
class NextRequest(ProtocolBuffer.ProtocolMessage):
  has_cursor_ = 0
  has_count_ = 0
  count_ = 0
  has_offset_ = 0
  offset_ = 0
  has_compile_ = 0
  compile_ = 0

  def __init__(self, contents=None):
    self.cursor_ = Cursor()
    if contents is not None: self.MergeFromString(contents)

  def cursor(self): return self.cursor_

  def mutable_cursor(self): self.has_cursor_ = 1; return self.cursor_

  def clear_cursor(self):self.has_cursor_ = 0; self.cursor_.Clear()

  def has_cursor(self): return self.has_cursor_

  def count(self): return self.count_

  def set_count(self, x):
    self.has_count_ = 1
    self.count_ = x

  def clear_count(self):
    if self.has_count_:
      self.has_count_ = 0
      self.count_ = 0

  def has_count(self): return self.has_count_

  def offset(self): return self.offset_

  def set_offset(self, x):
    self.has_offset_ = 1
    self.offset_ = x

  def clear_offset(self):
    if self.has_offset_:
      self.has_offset_ = 0
      self.offset_ = 0

  def has_offset(self): return self.has_offset_

  def compile(self): return self.compile_

  def set_compile(self, x):
    self.has_compile_ = 1
    self.compile_ = x

  def clear_compile(self):
    if self.has_compile_:
      self.has_compile_ = 0
      self.compile_ = 0

  def has_compile(self): return self.has_compile_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_cursor()): self.mutable_cursor().MergeFrom(x.cursor())
    if (x.has_count()): self.set_count(x.count())
    if (x.has_offset()): self.set_offset(x.offset())
    if (x.has_compile()): self.set_compile(x.compile())

  def Equals(self, x):
    if x is self: return 1
    if self.has_cursor_ != x.has_cursor_: return 0
    if self.has_cursor_ and self.cursor_ != x.cursor_: return 0
    if self.has_count_ != x.has_count_: return 0
    if self.has_count_ and self.count_ != x.count_: return 0
    if self.has_offset_ != x.has_offset_: return 0
    if self.has_offset_ and self.offset_ != x.offset_: return 0
    if self.has_compile_ != x.has_compile_: return 0
    if self.has_compile_ and self.compile_ != x.compile_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_cursor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: cursor not set.')
    elif not self.cursor_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.cursor_.ByteSize())
    if (self.has_count_): n += 1 + self.lengthVarInt64(self.count_)
    if (self.has_offset_): n += 1 + self.lengthVarInt64(self.offset_)
    if (self.has_compile_): n += 2
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_cursor_):
      n += 1
      n += self.lengthString(self.cursor_.ByteSizePartial())
    if (self.has_count_): n += 1 + self.lengthVarInt64(self.count_)
    if (self.has_offset_): n += 1 + self.lengthVarInt64(self.offset_)
    if (self.has_compile_): n += 2
    return n

  def Clear(self):
    self.clear_cursor()
    self.clear_count()
    self.clear_offset()
    self.clear_compile()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.cursor_.ByteSize())
    self.cursor_.OutputUnchecked(out)
    if (self.has_count_):
      out.putVarInt32(16)
      out.putVarInt32(self.count_)
    if (self.has_compile_):
      out.putVarInt32(24)
      out.putBoolean(self.compile_)
    if (self.has_offset_):
      out.putVarInt32(32)
      out.putVarInt32(self.offset_)

  def OutputPartial(self, out):
    if (self.has_cursor_):
      out.putVarInt32(10)
      out.putVarInt32(self.cursor_.ByteSizePartial())
      self.cursor_.OutputPartial(out)
    if (self.has_count_):
      out.putVarInt32(16)
      out.putVarInt32(self.count_)
    if (self.has_compile_):
      out.putVarInt32(24)
      out.putBoolean(self.compile_)
    if (self.has_offset_):
      out.putVarInt32(32)
      out.putVarInt32(self.offset_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_cursor().TryMerge(tmp)
        continue
      if tt == 16:
        self.set_count(d.getVarInt32())
        continue
      if tt == 24:
        self.set_compile(d.getBoolean())
        continue
      if tt == 32:
        self.set_offset(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_cursor_:
      res+=prefix+"cursor <\n"
      res+=self.cursor_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_count_: res+=prefix+("count: %s\n" % self.DebugFormatInt32(self.count_))
    if self.has_offset_: res+=prefix+("offset: %s\n" % self.DebugFormatInt32(self.offset_))
    if self.has_compile_: res+=prefix+("compile: %s\n" % self.DebugFormatBool(self.compile_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kcursor = 1
  kcount = 2
  koffset = 4
  kcompile = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "cursor",
    2: "count",
    3: "compile",
    4: "offset",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.NextRequest'
class QueryResult(ProtocolBuffer.ProtocolMessage):
  has_cursor_ = 0
  cursor_ = None
  has_skipped_results_ = 0
  skipped_results_ = 0
  has_more_results_ = 0
  more_results_ = 0
  has_keys_only_ = 0
  keys_only_ = 0
  has_index_only_ = 0
  index_only_ = 0
  has_small_ops_ = 0
  small_ops_ = 0
  has_compiled_query_ = 0
  compiled_query_ = None
  has_compiled_cursor_ = 0
  compiled_cursor_ = None
  has_skipped_results_compiled_cursor_ = 0
  skipped_results_compiled_cursor_ = None

  def __init__(self, contents=None):
    self.result_ = []
    self.index_ = []
    self.version_ = []
    self.result_compiled_cursor_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def cursor(self):
    if self.cursor_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.cursor_ is None: self.cursor_ = Cursor()
      finally:
        self.lazy_init_lock_.release()
    return self.cursor_

  def mutable_cursor(self): self.has_cursor_ = 1; return self.cursor()

  def clear_cursor(self):

    if self.has_cursor_:
      self.has_cursor_ = 0;
      if self.cursor_ is not None: self.cursor_.Clear()

  def has_cursor(self): return self.has_cursor_

  def result_size(self): return len(self.result_)
  def result_list(self): return self.result_

  def result(self, i):
    return self.result_[i]

  def mutable_result(self, i):
    return self.result_[i]

  def add_result(self):
    x = EntityProto()
    self.result_.append(x)
    return x

  def clear_result(self):
    self.result_ = []
  def skipped_results(self): return self.skipped_results_

  def set_skipped_results(self, x):
    self.has_skipped_results_ = 1
    self.skipped_results_ = x

  def clear_skipped_results(self):
    if self.has_skipped_results_:
      self.has_skipped_results_ = 0
      self.skipped_results_ = 0

  def has_skipped_results(self): return self.has_skipped_results_

  def more_results(self): return self.more_results_

  def set_more_results(self, x):
    self.has_more_results_ = 1
    self.more_results_ = x

  def clear_more_results(self):
    if self.has_more_results_:
      self.has_more_results_ = 0
      self.more_results_ = 0

  def has_more_results(self): return self.has_more_results_

  def keys_only(self): return self.keys_only_

  def set_keys_only(self, x):
    self.has_keys_only_ = 1
    self.keys_only_ = x

  def clear_keys_only(self):
    if self.has_keys_only_:
      self.has_keys_only_ = 0
      self.keys_only_ = 0

  def has_keys_only(self): return self.has_keys_only_

  def index_only(self): return self.index_only_

  def set_index_only(self, x):
    self.has_index_only_ = 1
    self.index_only_ = x

  def clear_index_only(self):
    if self.has_index_only_:
      self.has_index_only_ = 0
      self.index_only_ = 0

  def has_index_only(self): return self.has_index_only_

  def small_ops(self): return self.small_ops_

  def set_small_ops(self, x):
    self.has_small_ops_ = 1
    self.small_ops_ = x

  def clear_small_ops(self):
    if self.has_small_ops_:
      self.has_small_ops_ = 0
      self.small_ops_ = 0

  def has_small_ops(self): return self.has_small_ops_

  def compiled_query(self):
    if self.compiled_query_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.compiled_query_ is None: self.compiled_query_ = CompiledQuery()
      finally:
        self.lazy_init_lock_.release()
    return self.compiled_query_

  def mutable_compiled_query(self): self.has_compiled_query_ = 1; return self.compiled_query()

  def clear_compiled_query(self):

    if self.has_compiled_query_:
      self.has_compiled_query_ = 0;
      if self.compiled_query_ is not None: self.compiled_query_.Clear()

  def has_compiled_query(self): return self.has_compiled_query_

  def compiled_cursor(self):
    if self.compiled_cursor_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.compiled_cursor_ is None: self.compiled_cursor_ = CompiledCursor()
      finally:
        self.lazy_init_lock_.release()
    return self.compiled_cursor_

  def mutable_compiled_cursor(self): self.has_compiled_cursor_ = 1; return self.compiled_cursor()

  def clear_compiled_cursor(self):

    if self.has_compiled_cursor_:
      self.has_compiled_cursor_ = 0;
      if self.compiled_cursor_ is not None: self.compiled_cursor_.Clear()

  def has_compiled_cursor(self): return self.has_compiled_cursor_

  def index_size(self): return len(self.index_)
  def index_list(self): return self.index_

  def index(self, i):
    return self.index_[i]

  def mutable_index(self, i):
    return self.index_[i]

  def add_index(self):
    x = CompositeIndex()
    self.index_.append(x)
    return x

  def clear_index(self):
    self.index_ = []
  def version_size(self): return len(self.version_)
  def version_list(self): return self.version_

  def version(self, i):
    return self.version_[i]

  def set_version(self, i, x):
    self.version_[i] = x

  def add_version(self, x):
    self.version_.append(x)

  def clear_version(self):
    self.version_ = []

  def result_compiled_cursor_size(self): return len(self.result_compiled_cursor_)
  def result_compiled_cursor_list(self): return self.result_compiled_cursor_

  def result_compiled_cursor(self, i):
    return self.result_compiled_cursor_[i]

  def mutable_result_compiled_cursor(self, i):
    return self.result_compiled_cursor_[i]

  def add_result_compiled_cursor(self):
    x = CompiledCursor()
    self.result_compiled_cursor_.append(x)
    return x

  def clear_result_compiled_cursor(self):
    self.result_compiled_cursor_ = []
  def skipped_results_compiled_cursor(self):
    if self.skipped_results_compiled_cursor_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.skipped_results_compiled_cursor_ is None: self.skipped_results_compiled_cursor_ = CompiledCursor()
      finally:
        self.lazy_init_lock_.release()
    return self.skipped_results_compiled_cursor_

  def mutable_skipped_results_compiled_cursor(self): self.has_skipped_results_compiled_cursor_ = 1; return self.skipped_results_compiled_cursor()

  def clear_skipped_results_compiled_cursor(self):

    if self.has_skipped_results_compiled_cursor_:
      self.has_skipped_results_compiled_cursor_ = 0;
      if self.skipped_results_compiled_cursor_ is not None: self.skipped_results_compiled_cursor_.Clear()

  def has_skipped_results_compiled_cursor(self): return self.has_skipped_results_compiled_cursor_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_cursor()): self.mutable_cursor().MergeFrom(x.cursor())
    for i in xrange(x.result_size()): self.add_result().CopyFrom(x.result(i))
    if (x.has_skipped_results()): self.set_skipped_results(x.skipped_results())
    if (x.has_more_results()): self.set_more_results(x.more_results())
    if (x.has_keys_only()): self.set_keys_only(x.keys_only())
    if (x.has_index_only()): self.set_index_only(x.index_only())
    if (x.has_small_ops()): self.set_small_ops(x.small_ops())
    if (x.has_compiled_query()): self.mutable_compiled_query().MergeFrom(x.compiled_query())
    if (x.has_compiled_cursor()): self.mutable_compiled_cursor().MergeFrom(x.compiled_cursor())
    for i in xrange(x.index_size()): self.add_index().CopyFrom(x.index(i))
    for i in xrange(x.version_size()): self.add_version(x.version(i))
    for i in xrange(x.result_compiled_cursor_size()): self.add_result_compiled_cursor().CopyFrom(x.result_compiled_cursor(i))
    if (x.has_skipped_results_compiled_cursor()): self.mutable_skipped_results_compiled_cursor().MergeFrom(x.skipped_results_compiled_cursor())

  def Equals(self, x):
    if x is self: return 1
    if self.has_cursor_ != x.has_cursor_: return 0
    if self.has_cursor_ and self.cursor_ != x.cursor_: return 0
    if len(self.result_) != len(x.result_): return 0
    for e1, e2 in zip(self.result_, x.result_):
      if e1 != e2: return 0
    if self.has_skipped_results_ != x.has_skipped_results_: return 0
    if self.has_skipped_results_ and self.skipped_results_ != x.skipped_results_: return 0
    if self.has_more_results_ != x.has_more_results_: return 0
    if self.has_more_results_ and self.more_results_ != x.more_results_: return 0
    if self.has_keys_only_ != x.has_keys_only_: return 0
    if self.has_keys_only_ and self.keys_only_ != x.keys_only_: return 0
    if self.has_index_only_ != x.has_index_only_: return 0
    if self.has_index_only_ and self.index_only_ != x.index_only_: return 0
    if self.has_small_ops_ != x.has_small_ops_: return 0
    if self.has_small_ops_ and self.small_ops_ != x.small_ops_: return 0
    if self.has_compiled_query_ != x.has_compiled_query_: return 0
    if self.has_compiled_query_ and self.compiled_query_ != x.compiled_query_: return 0
    if self.has_compiled_cursor_ != x.has_compiled_cursor_: return 0
    if self.has_compiled_cursor_ and self.compiled_cursor_ != x.compiled_cursor_: return 0
    if len(self.index_) != len(x.index_): return 0
    for e1, e2 in zip(self.index_, x.index_):
      if e1 != e2: return 0
    if len(self.version_) != len(x.version_): return 0
    for e1, e2 in zip(self.version_, x.version_):
      if e1 != e2: return 0
    if len(self.result_compiled_cursor_) != len(x.result_compiled_cursor_): return 0
    for e1, e2 in zip(self.result_compiled_cursor_, x.result_compiled_cursor_):
      if e1 != e2: return 0
    if self.has_skipped_results_compiled_cursor_ != x.has_skipped_results_compiled_cursor_: return 0
    if self.has_skipped_results_compiled_cursor_ and self.skipped_results_compiled_cursor_ != x.skipped_results_compiled_cursor_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_cursor_ and not self.cursor_.IsInitialized(debug_strs)): initialized = 0
    for p in self.result_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (not self.has_more_results_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: more_results not set.')
    if (self.has_compiled_query_ and not self.compiled_query_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_compiled_cursor_ and not self.compiled_cursor_.IsInitialized(debug_strs)): initialized = 0
    for p in self.index_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.result_compiled_cursor_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_skipped_results_compiled_cursor_ and not self.skipped_results_compiled_cursor_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_cursor_): n += 1 + self.lengthString(self.cursor_.ByteSize())
    n += 1 * len(self.result_)
    for i in xrange(len(self.result_)): n += self.lengthString(self.result_[i].ByteSize())
    if (self.has_skipped_results_): n += 1 + self.lengthVarInt64(self.skipped_results_)
    if (self.has_keys_only_): n += 2
    if (self.has_index_only_): n += 2
    if (self.has_small_ops_): n += 2
    if (self.has_compiled_query_): n += 1 + self.lengthString(self.compiled_query_.ByteSize())
    if (self.has_compiled_cursor_): n += 1 + self.lengthString(self.compiled_cursor_.ByteSize())
    n += 1 * len(self.index_)
    for i in xrange(len(self.index_)): n += self.lengthString(self.index_[i].ByteSize())
    n += 1 * len(self.version_)
    for i in xrange(len(self.version_)): n += self.lengthVarInt64(self.version_[i])
    n += 1 * len(self.result_compiled_cursor_)
    for i in xrange(len(self.result_compiled_cursor_)): n += self.lengthString(self.result_compiled_cursor_[i].ByteSize())
    if (self.has_skipped_results_compiled_cursor_): n += 1 + self.lengthString(self.skipped_results_compiled_cursor_.ByteSize())
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_cursor_): n += 1 + self.lengthString(self.cursor_.ByteSizePartial())
    n += 1 * len(self.result_)
    for i in xrange(len(self.result_)): n += self.lengthString(self.result_[i].ByteSizePartial())
    if (self.has_skipped_results_): n += 1 + self.lengthVarInt64(self.skipped_results_)
    if (self.has_more_results_):
      n += 2
    if (self.has_keys_only_): n += 2
    if (self.has_index_only_): n += 2
    if (self.has_small_ops_): n += 2
    if (self.has_compiled_query_): n += 1 + self.lengthString(self.compiled_query_.ByteSizePartial())
    if (self.has_compiled_cursor_): n += 1 + self.lengthString(self.compiled_cursor_.ByteSizePartial())
    n += 1 * len(self.index_)
    for i in xrange(len(self.index_)): n += self.lengthString(self.index_[i].ByteSizePartial())
    n += 1 * len(self.version_)
    for i in xrange(len(self.version_)): n += self.lengthVarInt64(self.version_[i])
    n += 1 * len(self.result_compiled_cursor_)
    for i in xrange(len(self.result_compiled_cursor_)): n += self.lengthString(self.result_compiled_cursor_[i].ByteSizePartial())
    if (self.has_skipped_results_compiled_cursor_): n += 1 + self.lengthString(self.skipped_results_compiled_cursor_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_cursor()
    self.clear_result()
    self.clear_skipped_results()
    self.clear_more_results()
    self.clear_keys_only()
    self.clear_index_only()
    self.clear_small_ops()
    self.clear_compiled_query()
    self.clear_compiled_cursor()
    self.clear_index()
    self.clear_version()
    self.clear_result_compiled_cursor()
    self.clear_skipped_results_compiled_cursor()

  def OutputUnchecked(self, out):
    if (self.has_cursor_):
      out.putVarInt32(10)
      out.putVarInt32(self.cursor_.ByteSize())
      self.cursor_.OutputUnchecked(out)
    for i in xrange(len(self.result_)):
      out.putVarInt32(18)
      out.putVarInt32(self.result_[i].ByteSize())
      self.result_[i].OutputUnchecked(out)
    out.putVarInt32(24)
    out.putBoolean(self.more_results_)
    if (self.has_keys_only_):
      out.putVarInt32(32)
      out.putBoolean(self.keys_only_)
    if (self.has_compiled_query_):
      out.putVarInt32(42)
      out.putVarInt32(self.compiled_query_.ByteSize())
      self.compiled_query_.OutputUnchecked(out)
    if (self.has_compiled_cursor_):
      out.putVarInt32(50)
      out.putVarInt32(self.compiled_cursor_.ByteSize())
      self.compiled_cursor_.OutputUnchecked(out)
    if (self.has_skipped_results_):
      out.putVarInt32(56)
      out.putVarInt32(self.skipped_results_)
    for i in xrange(len(self.index_)):
      out.putVarInt32(66)
      out.putVarInt32(self.index_[i].ByteSize())
      self.index_[i].OutputUnchecked(out)
    if (self.has_index_only_):
      out.putVarInt32(72)
      out.putBoolean(self.index_only_)
    if (self.has_small_ops_):
      out.putVarInt32(80)
      out.putBoolean(self.small_ops_)
    for i in xrange(len(self.version_)):
      out.putVarInt32(88)
      out.putVarInt64(self.version_[i])
    for i in xrange(len(self.result_compiled_cursor_)):
      out.putVarInt32(98)
      out.putVarInt32(self.result_compiled_cursor_[i].ByteSize())
      self.result_compiled_cursor_[i].OutputUnchecked(out)
    if (self.has_skipped_results_compiled_cursor_):
      out.putVarInt32(106)
      out.putVarInt32(self.skipped_results_compiled_cursor_.ByteSize())
      self.skipped_results_compiled_cursor_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_cursor_):
      out.putVarInt32(10)
      out.putVarInt32(self.cursor_.ByteSizePartial())
      self.cursor_.OutputPartial(out)
    for i in xrange(len(self.result_)):
      out.putVarInt32(18)
      out.putVarInt32(self.result_[i].ByteSizePartial())
      self.result_[i].OutputPartial(out)
    if (self.has_more_results_):
      out.putVarInt32(24)
      out.putBoolean(self.more_results_)
    if (self.has_keys_only_):
      out.putVarInt32(32)
      out.putBoolean(self.keys_only_)
    if (self.has_compiled_query_):
      out.putVarInt32(42)
      out.putVarInt32(self.compiled_query_.ByteSizePartial())
      self.compiled_query_.OutputPartial(out)
    if (self.has_compiled_cursor_):
      out.putVarInt32(50)
      out.putVarInt32(self.compiled_cursor_.ByteSizePartial())
      self.compiled_cursor_.OutputPartial(out)
    if (self.has_skipped_results_):
      out.putVarInt32(56)
      out.putVarInt32(self.skipped_results_)
    for i in xrange(len(self.index_)):
      out.putVarInt32(66)
      out.putVarInt32(self.index_[i].ByteSizePartial())
      self.index_[i].OutputPartial(out)
    if (self.has_index_only_):
      out.putVarInt32(72)
      out.putBoolean(self.index_only_)
    if (self.has_small_ops_):
      out.putVarInt32(80)
      out.putBoolean(self.small_ops_)
    for i in xrange(len(self.version_)):
      out.putVarInt32(88)
      out.putVarInt64(self.version_[i])
    for i in xrange(len(self.result_compiled_cursor_)):
      out.putVarInt32(98)
      out.putVarInt32(self.result_compiled_cursor_[i].ByteSizePartial())
      self.result_compiled_cursor_[i].OutputPartial(out)
    if (self.has_skipped_results_compiled_cursor_):
      out.putVarInt32(106)
      out.putVarInt32(self.skipped_results_compiled_cursor_.ByteSizePartial())
      self.skipped_results_compiled_cursor_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_cursor().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_result().TryMerge(tmp)
        continue
      if tt == 24:
        self.set_more_results(d.getBoolean())
        continue
      if tt == 32:
        self.set_keys_only(d.getBoolean())
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_compiled_query().TryMerge(tmp)
        continue
      if tt == 50:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_compiled_cursor().TryMerge(tmp)
        continue
      if tt == 56:
        self.set_skipped_results(d.getVarInt32())
        continue
      if tt == 66:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_index().TryMerge(tmp)
        continue
      if tt == 72:
        self.set_index_only(d.getBoolean())
        continue
      if tt == 80:
        self.set_small_ops(d.getBoolean())
        continue
      if tt == 88:
        self.add_version(d.getVarInt64())
        continue
      if tt == 98:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_result_compiled_cursor().TryMerge(tmp)
        continue
      if tt == 106:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_skipped_results_compiled_cursor().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_cursor_:
      res+=prefix+"cursor <\n"
      res+=self.cursor_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.result_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("result%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_skipped_results_: res+=prefix+("skipped_results: %s\n" % self.DebugFormatInt32(self.skipped_results_))
    if self.has_more_results_: res+=prefix+("more_results: %s\n" % self.DebugFormatBool(self.more_results_))
    if self.has_keys_only_: res+=prefix+("keys_only: %s\n" % self.DebugFormatBool(self.keys_only_))
    if self.has_index_only_: res+=prefix+("index_only: %s\n" % self.DebugFormatBool(self.index_only_))
    if self.has_small_ops_: res+=prefix+("small_ops: %s\n" % self.DebugFormatBool(self.small_ops_))
    if self.has_compiled_query_:
      res+=prefix+"compiled_query <\n"
      res+=self.compiled_query_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_compiled_cursor_:
      res+=prefix+"compiled_cursor <\n"
      res+=self.compiled_cursor_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.index_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("index%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.version_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("version%s: %s\n" % (elm, self.DebugFormatInt64(e)))
      cnt+=1
    cnt=0
    for e in self.result_compiled_cursor_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("result_compiled_cursor%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_skipped_results_compiled_cursor_:
      res+=prefix+"skipped_results_compiled_cursor <\n"
      res+=self.skipped_results_compiled_cursor_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kcursor = 1
  kresult = 2
  kskipped_results = 7
  kmore_results = 3
  kkeys_only = 4
  kindex_only = 9
  ksmall_ops = 10
  kcompiled_query = 5
  kcompiled_cursor = 6
  kindex = 8
  kversion = 11
  kresult_compiled_cursor = 12
  kskipped_results_compiled_cursor = 13

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "cursor",
    2: "result",
    3: "more_results",
    4: "keys_only",
    5: "compiled_query",
    6: "compiled_cursor",
    7: "skipped_results",
    8: "index",
    9: "index_only",
    10: "small_ops",
    11: "version",
    12: "result_compiled_cursor",
    13: "skipped_results_compiled_cursor",
  }, 13)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.STRING,
    7: ProtocolBuffer.Encoder.NUMERIC,
    8: ProtocolBuffer.Encoder.STRING,
    9: ProtocolBuffer.Encoder.NUMERIC,
    10: ProtocolBuffer.Encoder.NUMERIC,
    11: ProtocolBuffer.Encoder.NUMERIC,
    12: ProtocolBuffer.Encoder.STRING,
    13: ProtocolBuffer.Encoder.STRING,
  }, 13, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.QueryResult'
class AllocateIdsRequest(ProtocolBuffer.ProtocolMessage):
  has_model_key_ = 0
  model_key_ = None
  has_size_ = 0
  size_ = 0
  has_max_ = 0
  max_ = 0
  has_trusted_ = 0
  trusted_ = 0

  def __init__(self, contents=None):
    self.reserve_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def model_key(self):
    if self.model_key_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.model_key_ is None: self.model_key_ = Reference()
      finally:
        self.lazy_init_lock_.release()
    return self.model_key_

  def mutable_model_key(self): self.has_model_key_ = 1; return self.model_key()

  def clear_model_key(self):

    if self.has_model_key_:
      self.has_model_key_ = 0;
      if self.model_key_ is not None: self.model_key_.Clear()

  def has_model_key(self): return self.has_model_key_

  def size(self): return self.size_

  def set_size(self, x):
    self.has_size_ = 1
    self.size_ = x

  def clear_size(self):
    if self.has_size_:
      self.has_size_ = 0
      self.size_ = 0

  def has_size(self): return self.has_size_

  def max(self): return self.max_

  def set_max(self, x):
    self.has_max_ = 1
    self.max_ = x

  def clear_max(self):
    if self.has_max_:
      self.has_max_ = 0
      self.max_ = 0

  def has_max(self): return self.has_max_

  def reserve_size(self): return len(self.reserve_)
  def reserve_list(self): return self.reserve_

  def reserve(self, i):
    return self.reserve_[i]

  def mutable_reserve(self, i):
    return self.reserve_[i]

  def add_reserve(self):
    x = Reference()
    self.reserve_.append(x)
    return x

  def clear_reserve(self):
    self.reserve_ = []
  def trusted(self): return self.trusted_

  def set_trusted(self, x):
    self.has_trusted_ = 1
    self.trusted_ = x

  def clear_trusted(self):
    if self.has_trusted_:
      self.has_trusted_ = 0
      self.trusted_ = 0

  def has_trusted(self): return self.has_trusted_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_model_key()): self.mutable_model_key().MergeFrom(x.model_key())
    if (x.has_size()): self.set_size(x.size())
    if (x.has_max()): self.set_max(x.max())
    for i in xrange(x.reserve_size()): self.add_reserve().CopyFrom(x.reserve(i))
    if (x.has_trusted()): self.set_trusted(x.trusted())

  def Equals(self, x):
    if x is self: return 1
    if self.has_model_key_ != x.has_model_key_: return 0
    if self.has_model_key_ and self.model_key_ != x.model_key_: return 0
    if self.has_size_ != x.has_size_: return 0
    if self.has_size_ and self.size_ != x.size_: return 0
    if self.has_max_ != x.has_max_: return 0
    if self.has_max_ and self.max_ != x.max_: return 0
    if len(self.reserve_) != len(x.reserve_): return 0
    for e1, e2 in zip(self.reserve_, x.reserve_):
      if e1 != e2: return 0
    if self.has_trusted_ != x.has_trusted_: return 0
    if self.has_trusted_ and self.trusted_ != x.trusted_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_model_key_ and not self.model_key_.IsInitialized(debug_strs)): initialized = 0
    for p in self.reserve_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_model_key_): n += 1 + self.lengthString(self.model_key_.ByteSize())
    if (self.has_size_): n += 1 + self.lengthVarInt64(self.size_)
    if (self.has_max_): n += 1 + self.lengthVarInt64(self.max_)
    n += 1 * len(self.reserve_)
    for i in xrange(len(self.reserve_)): n += self.lengthString(self.reserve_[i].ByteSize())
    if (self.has_trusted_): n += 2
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_model_key_): n += 1 + self.lengthString(self.model_key_.ByteSizePartial())
    if (self.has_size_): n += 1 + self.lengthVarInt64(self.size_)
    if (self.has_max_): n += 1 + self.lengthVarInt64(self.max_)
    n += 1 * len(self.reserve_)
    for i in xrange(len(self.reserve_)): n += self.lengthString(self.reserve_[i].ByteSizePartial())
    if (self.has_trusted_): n += 2
    return n

  def Clear(self):
    self.clear_model_key()
    self.clear_size()
    self.clear_max()
    self.clear_reserve()
    self.clear_trusted()

  def OutputUnchecked(self, out):
    if (self.has_model_key_):
      out.putVarInt32(10)
      out.putVarInt32(self.model_key_.ByteSize())
      self.model_key_.OutputUnchecked(out)
    if (self.has_size_):
      out.putVarInt32(16)
      out.putVarInt64(self.size_)
    if (self.has_max_):
      out.putVarInt32(24)
      out.putVarInt64(self.max_)
    for i in xrange(len(self.reserve_)):
      out.putVarInt32(42)
      out.putVarInt32(self.reserve_[i].ByteSize())
      self.reserve_[i].OutputUnchecked(out)
    if (self.has_trusted_):
      out.putVarInt32(48)
      out.putBoolean(self.trusted_)

  def OutputPartial(self, out):
    if (self.has_model_key_):
      out.putVarInt32(10)
      out.putVarInt32(self.model_key_.ByteSizePartial())
      self.model_key_.OutputPartial(out)
    if (self.has_size_):
      out.putVarInt32(16)
      out.putVarInt64(self.size_)
    if (self.has_max_):
      out.putVarInt32(24)
      out.putVarInt64(self.max_)
    for i in xrange(len(self.reserve_)):
      out.putVarInt32(42)
      out.putVarInt32(self.reserve_[i].ByteSizePartial())
      self.reserve_[i].OutputPartial(out)
    if (self.has_trusted_):
      out.putVarInt32(48)
      out.putBoolean(self.trusted_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_model_key().TryMerge(tmp)
        continue
      if tt == 16:
        self.set_size(d.getVarInt64())
        continue
      if tt == 24:
        self.set_max(d.getVarInt64())
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_reserve().TryMerge(tmp)
        continue
      if tt == 48:
        self.set_trusted(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_model_key_:
      res+=prefix+"model_key <\n"
      res+=self.model_key_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_size_: res+=prefix+("size: %s\n" % self.DebugFormatInt64(self.size_))
    if self.has_max_: res+=prefix+("max: %s\n" % self.DebugFormatInt64(self.max_))
    cnt=0
    for e in self.reserve_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("reserve%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_trusted_: res+=prefix+("trusted: %s\n" % self.DebugFormatBool(self.trusted_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kmodel_key = 1
  ksize = 2
  kmax = 3
  kreserve = 5
  ktrusted = 6

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "model_key",
    2: "size",
    3: "max",
    5: "reserve",
    6: "trusted",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.NUMERIC,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.AllocateIdsRequest'
class AllocateIdsResponse(ProtocolBuffer.ProtocolMessage):
  has_start_ = 0
  start_ = 0
  has_end_ = 0
  end_ = 0
  has_cost_ = 0
  cost_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def start(self): return self.start_

  def set_start(self, x):
    self.has_start_ = 1
    self.start_ = x

  def clear_start(self):
    if self.has_start_:
      self.has_start_ = 0
      self.start_ = 0

  def has_start(self): return self.has_start_

  def end(self): return self.end_

  def set_end(self, x):
    self.has_end_ = 1
    self.end_ = x

  def clear_end(self):
    if self.has_end_:
      self.has_end_ = 0
      self.end_ = 0

  def has_end(self): return self.has_end_

  def cost(self):
    if self.cost_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.cost_ is None: self.cost_ = Cost()
      finally:
        self.lazy_init_lock_.release()
    return self.cost_

  def mutable_cost(self): self.has_cost_ = 1; return self.cost()

  def clear_cost(self):

    if self.has_cost_:
      self.has_cost_ = 0;
      if self.cost_ is not None: self.cost_.Clear()

  def has_cost(self): return self.has_cost_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_start()): self.set_start(x.start())
    if (x.has_end()): self.set_end(x.end())
    if (x.has_cost()): self.mutable_cost().MergeFrom(x.cost())

  def Equals(self, x):
    if x is self: return 1
    if self.has_start_ != x.has_start_: return 0
    if self.has_start_ and self.start_ != x.start_: return 0
    if self.has_end_ != x.has_end_: return 0
    if self.has_end_ and self.end_ != x.end_: return 0
    if self.has_cost_ != x.has_cost_: return 0
    if self.has_cost_ and self.cost_ != x.cost_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_start_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: start not set.')
    if (not self.has_end_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: end not set.')
    if (self.has_cost_ and not self.cost_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.start_)
    n += self.lengthVarInt64(self.end_)
    if (self.has_cost_): n += 1 + self.lengthString(self.cost_.ByteSize())
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_start_):
      n += 1
      n += self.lengthVarInt64(self.start_)
    if (self.has_end_):
      n += 1
      n += self.lengthVarInt64(self.end_)
    if (self.has_cost_): n += 1 + self.lengthString(self.cost_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_start()
    self.clear_end()
    self.clear_cost()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt64(self.start_)
    out.putVarInt32(16)
    out.putVarInt64(self.end_)
    if (self.has_cost_):
      out.putVarInt32(26)
      out.putVarInt32(self.cost_.ByteSize())
      self.cost_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_start_):
      out.putVarInt32(8)
      out.putVarInt64(self.start_)
    if (self.has_end_):
      out.putVarInt32(16)
      out.putVarInt64(self.end_)
    if (self.has_cost_):
      out.putVarInt32(26)
      out.putVarInt32(self.cost_.ByteSizePartial())
      self.cost_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_start(d.getVarInt64())
        continue
      if tt == 16:
        self.set_end(d.getVarInt64())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_cost().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_start_: res+=prefix+("start: %s\n" % self.DebugFormatInt64(self.start_))
    if self.has_end_: res+=prefix+("end: %s\n" % self.DebugFormatInt64(self.end_))
    if self.has_cost_:
      res+=prefix+"cost <\n"
      res+=self.cost_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kstart = 1
  kend = 2
  kcost = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "start",
    2: "end",
    3: "cost",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.AllocateIdsResponse'
class CompositeIndices(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.index_ = []
    if contents is not None: self.MergeFromString(contents)

  def index_size(self): return len(self.index_)
  def index_list(self): return self.index_

  def index(self, i):
    return self.index_[i]

  def mutable_index(self, i):
    return self.index_[i]

  def add_index(self):
    x = CompositeIndex()
    self.index_.append(x)
    return x

  def clear_index(self):
    self.index_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.index_size()): self.add_index().CopyFrom(x.index(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.index_) != len(x.index_): return 0
    for e1, e2 in zip(self.index_, x.index_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.index_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.index_)
    for i in xrange(len(self.index_)): n += self.lengthString(self.index_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.index_)
    for i in xrange(len(self.index_)): n += self.lengthString(self.index_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_index()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.index_)):
      out.putVarInt32(10)
      out.putVarInt32(self.index_[i].ByteSize())
      self.index_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.index_)):
      out.putVarInt32(10)
      out.putVarInt32(self.index_[i].ByteSizePartial())
      self.index_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_index().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.index_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("index%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kindex = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "index",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.CompositeIndices'
class AddActionsRequest(ProtocolBuffer.ProtocolMessage):
  has_transaction_ = 0

  def __init__(self, contents=None):
    self.transaction_ = Transaction()
    self.action_ = []
    if contents is not None: self.MergeFromString(contents)

  def transaction(self): return self.transaction_

  def mutable_transaction(self): self.has_transaction_ = 1; return self.transaction_

  def clear_transaction(self):self.has_transaction_ = 0; self.transaction_.Clear()

  def has_transaction(self): return self.has_transaction_

  def action_size(self): return len(self.action_)
  def action_list(self): return self.action_

  def action(self, i):
    return self.action_[i]

  def mutable_action(self, i):
    return self.action_[i]

  def add_action(self):
    x = Action()
    self.action_.append(x)
    return x

  def clear_action(self):
    self.action_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_transaction()): self.mutable_transaction().MergeFrom(x.transaction())
    for i in xrange(x.action_size()): self.add_action().CopyFrom(x.action(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_transaction_ != x.has_transaction_: return 0
    if self.has_transaction_ and self.transaction_ != x.transaction_: return 0
    if len(self.action_) != len(x.action_): return 0
    for e1, e2 in zip(self.action_, x.action_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_transaction_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: transaction not set.')
    elif not self.transaction_.IsInitialized(debug_strs): initialized = 0
    for p in self.action_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.transaction_.ByteSize())
    n += 1 * len(self.action_)
    for i in xrange(len(self.action_)): n += self.lengthString(self.action_[i].ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_transaction_):
      n += 1
      n += self.lengthString(self.transaction_.ByteSizePartial())
    n += 1 * len(self.action_)
    for i in xrange(len(self.action_)): n += self.lengthString(self.action_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_transaction()
    self.clear_action()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.transaction_.ByteSize())
    self.transaction_.OutputUnchecked(out)
    for i in xrange(len(self.action_)):
      out.putVarInt32(18)
      out.putVarInt32(self.action_[i].ByteSize())
      self.action_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_transaction_):
      out.putVarInt32(10)
      out.putVarInt32(self.transaction_.ByteSizePartial())
      self.transaction_.OutputPartial(out)
    for i in xrange(len(self.action_)):
      out.putVarInt32(18)
      out.putVarInt32(self.action_[i].ByteSizePartial())
      self.action_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_transaction().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_action().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_transaction_:
      res+=prefix+"transaction <\n"
      res+=self.transaction_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.action_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("action%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktransaction = 1
  kaction = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "transaction",
    2: "action",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.AddActionsRequest'
class AddActionsResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.AddActionsResponse'
class BeginTransactionRequest(ProtocolBuffer.ProtocolMessage):
  has_app_ = 0
  app_ = ""
  has_allow_multiple_eg_ = 0
  allow_multiple_eg_ = 0
  has_database_id_ = 0
  database_id_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def app(self): return self.app_

  def set_app(self, x):
    self.has_app_ = 1
    self.app_ = x

  def clear_app(self):
    if self.has_app_:
      self.has_app_ = 0
      self.app_ = ""

  def has_app(self): return self.has_app_

  def allow_multiple_eg(self): return self.allow_multiple_eg_

  def set_allow_multiple_eg(self, x):
    self.has_allow_multiple_eg_ = 1
    self.allow_multiple_eg_ = x

  def clear_allow_multiple_eg(self):
    if self.has_allow_multiple_eg_:
      self.has_allow_multiple_eg_ = 0
      self.allow_multiple_eg_ = 0

  def has_allow_multiple_eg(self): return self.has_allow_multiple_eg_

  def database_id(self): return self.database_id_

  def set_database_id(self, x):
    self.has_database_id_ = 1
    self.database_id_ = x

  def clear_database_id(self):
    if self.has_database_id_:
      self.has_database_id_ = 0
      self.database_id_ = ""

  def has_database_id(self): return self.has_database_id_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app()): self.set_app(x.app())
    if (x.has_allow_multiple_eg()): self.set_allow_multiple_eg(x.allow_multiple_eg())
    if (x.has_database_id()): self.set_database_id(x.database_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_ != x.has_app_: return 0
    if self.has_app_ and self.app_ != x.app_: return 0
    if self.has_allow_multiple_eg_ != x.has_allow_multiple_eg_: return 0
    if self.has_allow_multiple_eg_ and self.allow_multiple_eg_ != x.allow_multiple_eg_: return 0
    if self.has_database_id_ != x.has_database_id_: return 0
    if self.has_database_id_ and self.database_id_ != x.database_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_app_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: app not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.app_))
    if (self.has_allow_multiple_eg_): n += 2
    if (self.has_database_id_): n += 1 + self.lengthString(len(self.database_id_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_):
      n += 1
      n += self.lengthString(len(self.app_))
    if (self.has_allow_multiple_eg_): n += 2
    if (self.has_database_id_): n += 1 + self.lengthString(len(self.database_id_))
    return n

  def Clear(self):
    self.clear_app()
    self.clear_allow_multiple_eg()
    self.clear_database_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.app_)
    if (self.has_allow_multiple_eg_):
      out.putVarInt32(16)
      out.putBoolean(self.allow_multiple_eg_)
    if (self.has_database_id_):
      out.putVarInt32(34)
      out.putPrefixedString(self.database_id_)

  def OutputPartial(self, out):
    if (self.has_app_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_)
    if (self.has_allow_multiple_eg_):
      out.putVarInt32(16)
      out.putBoolean(self.allow_multiple_eg_)
    if (self.has_database_id_):
      out.putVarInt32(34)
      out.putPrefixedString(self.database_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_allow_multiple_eg(d.getBoolean())
        continue
      if tt == 34:
        self.set_database_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_: res+=prefix+("app: %s\n" % self.DebugFormatString(self.app_))
    if self.has_allow_multiple_eg_: res+=prefix+("allow_multiple_eg: %s\n" % self.DebugFormatBool(self.allow_multiple_eg_))
    if self.has_database_id_: res+=prefix+("database_id: %s\n" % self.DebugFormatString(self.database_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp = 1
  kallow_multiple_eg = 2
  kdatabase_id = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app",
    2: "allow_multiple_eg",
    4: "database_id",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.BeginTransactionRequest'
class CommitResponse_Version(ProtocolBuffer.ProtocolMessage):
  has_root_entity_key_ = 0
  has_version_ = 0
  version_ = 0

  def __init__(self, contents=None):
    self.root_entity_key_ = Reference()
    if contents is not None: self.MergeFromString(contents)

  def root_entity_key(self): return self.root_entity_key_

  def mutable_root_entity_key(self): self.has_root_entity_key_ = 1; return self.root_entity_key_

  def clear_root_entity_key(self):self.has_root_entity_key_ = 0; self.root_entity_key_.Clear()

  def has_root_entity_key(self): return self.has_root_entity_key_

  def version(self): return self.version_

  def set_version(self, x):
    self.has_version_ = 1
    self.version_ = x

  def clear_version(self):
    if self.has_version_:
      self.has_version_ = 0
      self.version_ = 0

  def has_version(self): return self.has_version_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_root_entity_key()): self.mutable_root_entity_key().MergeFrom(x.root_entity_key())
    if (x.has_version()): self.set_version(x.version())

  def Equals(self, x):
    if x is self: return 1
    if self.has_root_entity_key_ != x.has_root_entity_key_: return 0
    if self.has_root_entity_key_ and self.root_entity_key_ != x.root_entity_key_: return 0
    if self.has_version_ != x.has_version_: return 0
    if self.has_version_ and self.version_ != x.version_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_root_entity_key_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: root_entity_key not set.')
    elif not self.root_entity_key_.IsInitialized(debug_strs): initialized = 0
    if (not self.has_version_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: version not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.root_entity_key_.ByteSize())
    n += self.lengthVarInt64(self.version_)
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_root_entity_key_):
      n += 1
      n += self.lengthString(self.root_entity_key_.ByteSizePartial())
    if (self.has_version_):
      n += 1
      n += self.lengthVarInt64(self.version_)
    return n

  def Clear(self):
    self.clear_root_entity_key()
    self.clear_version()

  def OutputUnchecked(self, out):
    out.putVarInt32(34)
    out.putVarInt32(self.root_entity_key_.ByteSize())
    self.root_entity_key_.OutputUnchecked(out)
    out.putVarInt32(40)
    out.putVarInt64(self.version_)

  def OutputPartial(self, out):
    if (self.has_root_entity_key_):
      out.putVarInt32(34)
      out.putVarInt32(self.root_entity_key_.ByteSizePartial())
      self.root_entity_key_.OutputPartial(out)
    if (self.has_version_):
      out.putVarInt32(40)
      out.putVarInt64(self.version_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 28: break
      if tt == 34:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_root_entity_key().TryMerge(tmp)
        continue
      if tt == 40:
        self.set_version(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_root_entity_key_:
      res+=prefix+"root_entity_key <\n"
      res+=self.root_entity_key_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_version_: res+=prefix+("version: %s\n" % self.DebugFormatInt64(self.version_))
    return res

class CommitResponse(ProtocolBuffer.ProtocolMessage):
  has_cost_ = 0
  cost_ = None

  def __init__(self, contents=None):
    self.version_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def cost(self):
    if self.cost_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.cost_ is None: self.cost_ = Cost()
      finally:
        self.lazy_init_lock_.release()
    return self.cost_

  def mutable_cost(self): self.has_cost_ = 1; return self.cost()

  def clear_cost(self):

    if self.has_cost_:
      self.has_cost_ = 0;
      if self.cost_ is not None: self.cost_.Clear()

  def has_cost(self): return self.has_cost_

  def version_size(self): return len(self.version_)
  def version_list(self): return self.version_

  def version(self, i):
    return self.version_[i]

  def mutable_version(self, i):
    return self.version_[i]

  def add_version(self):
    x = CommitResponse_Version()
    self.version_.append(x)
    return x

  def clear_version(self):
    self.version_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_cost()): self.mutable_cost().MergeFrom(x.cost())
    for i in xrange(x.version_size()): self.add_version().CopyFrom(x.version(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_cost_ != x.has_cost_: return 0
    if self.has_cost_ and self.cost_ != x.cost_: return 0
    if len(self.version_) != len(x.version_): return 0
    for e1, e2 in zip(self.version_, x.version_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_cost_ and not self.cost_.IsInitialized(debug_strs)): initialized = 0
    for p in self.version_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_cost_): n += 1 + self.lengthString(self.cost_.ByteSize())
    n += 2 * len(self.version_)
    for i in xrange(len(self.version_)): n += self.version_[i].ByteSize()
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_cost_): n += 1 + self.lengthString(self.cost_.ByteSizePartial())
    n += 2 * len(self.version_)
    for i in xrange(len(self.version_)): n += self.version_[i].ByteSizePartial()
    return n

  def Clear(self):
    self.clear_cost()
    self.clear_version()

  def OutputUnchecked(self, out):
    if (self.has_cost_):
      out.putVarInt32(10)
      out.putVarInt32(self.cost_.ByteSize())
      self.cost_.OutputUnchecked(out)
    for i in xrange(len(self.version_)):
      out.putVarInt32(27)
      self.version_[i].OutputUnchecked(out)
      out.putVarInt32(28)

  def OutputPartial(self, out):
    if (self.has_cost_):
      out.putVarInt32(10)
      out.putVarInt32(self.cost_.ByteSizePartial())
      self.cost_.OutputPartial(out)
    for i in xrange(len(self.version_)):
      out.putVarInt32(27)
      self.version_[i].OutputPartial(out)
      out.putVarInt32(28)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_cost().TryMerge(tmp)
        continue
      if tt == 27:
        self.add_version().TryMerge(d)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_cost_:
      res+=prefix+"cost <\n"
      res+=self.cost_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.version_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Version%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kcost = 1
  kVersionGroup = 3
  kVersionroot_entity_key = 4
  kVersionversion = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "cost",
    3: "Version",
    4: "root_entity_key",
    5: "version",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STARTGROUP,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.NUMERIC,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.CommitResponse'
class GetIndicesRequest(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_database_id_ = 0
  database_id_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def app_id(self): return self.app_id_

  def set_app_id(self, x):
    self.has_app_id_ = 1
    self.app_id_ = x

  def clear_app_id(self):
    if self.has_app_id_:
      self.has_app_id_ = 0
      self.app_id_ = ""

  def has_app_id(self): return self.has_app_id_

  def database_id(self): return self.database_id_

  def set_database_id(self, x):
    self.has_database_id_ = 1
    self.database_id_ = x

  def clear_database_id(self):
    if self.has_database_id_:
      self.has_database_id_ = 0
      self.database_id_ = ""

  def has_database_id(self): return self.has_database_id_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_database_id()): self.set_database_id(x.database_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_database_id_ != x.has_database_id_: return 0
    if self.has_database_id_ and self.database_id_ != x.database_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_app_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: app_id not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.app_id_))
    if (self.has_database_id_): n += 1 + self.lengthString(len(self.database_id_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_):
      n += 1
      n += self.lengthString(len(self.app_id_))
    if (self.has_database_id_): n += 1 + self.lengthString(len(self.database_id_))
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_database_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.app_id_)
    if (self.has_database_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.database_id_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    if (self.has_database_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.database_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_database_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_database_id_: res+=prefix+("database_id: %s\n" % self.DebugFormatString(self.database_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  kdatabase_id = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "database_id",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.GetIndicesRequest'
class DatastoreService_3(ProtocolBuffer.ProtocolMessage):


  Get          =    1
  Put          =    2
  Touch        =    3
  Delete       =    4
  RunQuery     =    5
  AddActions   =    6
  Next         =    7
  DeleteCursor =    8
  BeginTransaction =    9
  Commit       =   10
  Rollback     =   11
  AllocateIds  =   12
  CreateIndex  =   13
  UpdateIndex  =   14
  GetIndices   =   15
  DeleteIndex  =   16

  _Method_NAMES = {
    1: "Get",
    2: "Put",
    3: "Touch",
    4: "Delete",
    5: "RunQuery",
    6: "AddActions",
    7: "Next",
    8: "DeleteCursor",
    9: "BeginTransaction",
    10: "Commit",
    11: "Rollback",
    12: "AllocateIds",
    13: "CreateIndex",
    14: "UpdateIndex",
    15: "GetIndices",
    16: "DeleteIndex",
  }

  def Method_Name(cls, x): return cls._Method_NAMES.get(x, "")
  Method_Name = classmethod(Method_Name)


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
  _PROTO_DESCRIPTOR_NAME = 'apphosting_datastore_v3.DatastoreService_3'
if _extension_runtime:
  pass

__all__ = ['Transaction','Query','Query_Filter','Query_Order','RegionPoint','CircleRegion','RectangleRegion','GeoRegion','CompiledQuery','CompiledQuery_PrimaryScan','CompiledQuery_MergeJoinScan','CompiledQuery_EntityFilter','CompiledCursor','CompiledCursor_PositionIndexValue','CompiledCursor_Position','Cursor','Error','Cost','Cost_CommitCost','GetRequest','GetResponse','GetResponse_Entity','PutRequest','PutResponse','TouchRequest','TouchResponse','DeleteRequest','DeleteResponse','NextRequest','QueryResult','AllocateIdsRequest','AllocateIdsResponse','CompositeIndices','AddActionsRequest','AddActionsResponse','BeginTransactionRequest','CommitResponse','CommitResponse_Version','GetIndicesRequest','DatastoreService_3']
