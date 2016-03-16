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

class Scope(ProtocolBuffer.ProtocolMessage):


  USER_BY_CANONICAL_ID =    1
  USER_BY_EMAIL =    2
  GROUP_BY_CANONICAL_ID =    3
  GROUP_BY_EMAIL =    4
  GROUP_BY_DOMAIN =    5
  ALL_USERS    =    6
  ALL_AUTHENTICATED_USERS =    7

  _Type_NAMES = {
    1: "USER_BY_CANONICAL_ID",
    2: "USER_BY_EMAIL",
    3: "GROUP_BY_CANONICAL_ID",
    4: "GROUP_BY_EMAIL",
    5: "GROUP_BY_DOMAIN",
    6: "ALL_USERS",
    7: "ALL_AUTHENTICATED_USERS",
  }

  def Type_Name(cls, x): return cls._Type_NAMES.get(x, "")
  Type_Name = classmethod(Type_Name)

  has_type_ = 0
  type_ = 0
  has_value_ = 0
  value_ = ""

  def __init__(self, contents=None):
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

  def value(self): return self.value_

  def set_value(self, x):
    self.has_value_ = 1
    self.value_ = x

  def clear_value(self):
    if self.has_value_:
      self.has_value_ = 0
      self.value_ = ""

  def has_value(self): return self.has_value_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_type()): self.set_type(x.type())
    if (x.has_value()): self.set_value(x.value())

  def Equals(self, x):
    if x is self: return 1
    if self.has_type_ != x.has_type_: return 0
    if self.has_type_ and self.type_ != x.type_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_type_): n += 1 + self.lengthVarInt64(self.type_)
    if (self.has_value_): n += 1 + self.lengthString(len(self.value_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_type_): n += 1 + self.lengthVarInt64(self.type_)
    if (self.has_value_): n += 1 + self.lengthString(len(self.value_))
    return n

  def Clear(self):
    self.clear_type()
    self.clear_value()

  def OutputUnchecked(self, out):
    if (self.has_type_):
      out.putVarInt32(8)
      out.putVarInt32(self.type_)
    if (self.has_value_):
      out.putVarInt32(18)
      out.putPrefixedString(self.value_)

  def OutputPartial(self, out):
    if (self.has_type_):
      out.putVarInt32(8)
      out.putVarInt32(self.type_)
    if (self.has_value_):
      out.putVarInt32(18)
      out.putPrefixedString(self.value_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_type(d.getVarInt32())
        continue
      if tt == 18:
        self.set_value(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_type_: res+=prefix+("type: %s\n" % self.DebugFormatInt32(self.type_))
    if self.has_value_: res+=prefix+("value: %s\n" % self.DebugFormatString(self.value_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktype = 1
  kvalue = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "type",
    2: "value",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.Scope'
class Entry(ProtocolBuffer.ProtocolMessage):


  READ         =    1
  WRITE        =    2
  FULL_CONTROL =    3

  _Permission_NAMES = {
    1: "READ",
    2: "WRITE",
    3: "FULL_CONTROL",
  }

  def Permission_Name(cls, x): return cls._Permission_NAMES.get(x, "")
  Permission_Name = classmethod(Permission_Name)

  has_scope_ = 0
  scope_ = None
  has_permission_ = 0
  permission_ = 0
  has_display_name_ = 0
  display_name_ = ""

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def scope(self):
    if self.scope_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.scope_ is None: self.scope_ = Scope()
      finally:
        self.lazy_init_lock_.release()
    return self.scope_

  def mutable_scope(self): self.has_scope_ = 1; return self.scope()

  def clear_scope(self):

    if self.has_scope_:
      self.has_scope_ = 0;
      if self.scope_ is not None: self.scope_.Clear()

  def has_scope(self): return self.has_scope_

  def permission(self): return self.permission_

  def set_permission(self, x):
    self.has_permission_ = 1
    self.permission_ = x

  def clear_permission(self):
    if self.has_permission_:
      self.has_permission_ = 0
      self.permission_ = 0

  def has_permission(self): return self.has_permission_

  def display_name(self): return self.display_name_

  def set_display_name(self, x):
    self.has_display_name_ = 1
    self.display_name_ = x

  def clear_display_name(self):
    if self.has_display_name_:
      self.has_display_name_ = 0
      self.display_name_ = ""

  def has_display_name(self): return self.has_display_name_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_scope()): self.mutable_scope().MergeFrom(x.scope())
    if (x.has_permission()): self.set_permission(x.permission())
    if (x.has_display_name()): self.set_display_name(x.display_name())

  def Equals(self, x):
    if x is self: return 1
    if self.has_scope_ != x.has_scope_: return 0
    if self.has_scope_ and self.scope_ != x.scope_: return 0
    if self.has_permission_ != x.has_permission_: return 0
    if self.has_permission_ and self.permission_ != x.permission_: return 0
    if self.has_display_name_ != x.has_display_name_: return 0
    if self.has_display_name_ and self.display_name_ != x.display_name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_scope_ and not self.scope_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_scope_): n += 1 + self.lengthString(self.scope_.ByteSize())
    if (self.has_permission_): n += 1 + self.lengthVarInt64(self.permission_)
    if (self.has_display_name_): n += 1 + self.lengthString(len(self.display_name_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_scope_): n += 1 + self.lengthString(self.scope_.ByteSizePartial())
    if (self.has_permission_): n += 1 + self.lengthVarInt64(self.permission_)
    if (self.has_display_name_): n += 1 + self.lengthString(len(self.display_name_))
    return n

  def Clear(self):
    self.clear_scope()
    self.clear_permission()
    self.clear_display_name()

  def OutputUnchecked(self, out):
    if (self.has_scope_):
      out.putVarInt32(10)
      out.putVarInt32(self.scope_.ByteSize())
      self.scope_.OutputUnchecked(out)
    if (self.has_permission_):
      out.putVarInt32(16)
      out.putVarInt32(self.permission_)
    if (self.has_display_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.display_name_)

  def OutputPartial(self, out):
    if (self.has_scope_):
      out.putVarInt32(10)
      out.putVarInt32(self.scope_.ByteSizePartial())
      self.scope_.OutputPartial(out)
    if (self.has_permission_):
      out.putVarInt32(16)
      out.putVarInt32(self.permission_)
    if (self.has_display_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.display_name_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_scope().TryMerge(tmp)
        continue
      if tt == 16:
        self.set_permission(d.getVarInt32())
        continue
      if tt == 26:
        self.set_display_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_scope_:
      res+=prefix+"scope <\n"
      res+=self.scope_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_permission_: res+=prefix+("permission: %s\n" % self.DebugFormatInt32(self.permission_))
    if self.has_display_name_: res+=prefix+("display_name: %s\n" % self.DebugFormatString(self.display_name_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kscope = 1
  kpermission = 2
  kdisplay_name = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "scope",
    2: "permission",
    3: "display_name",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.Entry'
class AccessControlList(ProtocolBuffer.ProtocolMessage):
  has_owner_ = 0
  owner_ = ""

  def __init__(self, contents=None):
    self.entries_ = []
    if contents is not None: self.MergeFromString(contents)

  def owner(self): return self.owner_

  def set_owner(self, x):
    self.has_owner_ = 1
    self.owner_ = x

  def clear_owner(self):
    if self.has_owner_:
      self.has_owner_ = 0
      self.owner_ = ""

  def has_owner(self): return self.has_owner_

  def entries_size(self): return len(self.entries_)
  def entries_list(self): return self.entries_

  def entries(self, i):
    return self.entries_[i]

  def mutable_entries(self, i):
    return self.entries_[i]

  def add_entries(self):
    x = Entry()
    self.entries_.append(x)
    return x

  def clear_entries(self):
    self.entries_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_owner()): self.set_owner(x.owner())
    for i in xrange(x.entries_size()): self.add_entries().CopyFrom(x.entries(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_owner_ != x.has_owner_: return 0
    if self.has_owner_ and self.owner_ != x.owner_: return 0
    if len(self.entries_) != len(x.entries_): return 0
    for e1, e2 in zip(self.entries_, x.entries_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.entries_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_owner_): n += 1 + self.lengthString(len(self.owner_))
    n += 1 * len(self.entries_)
    for i in xrange(len(self.entries_)): n += self.lengthString(self.entries_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_owner_): n += 1 + self.lengthString(len(self.owner_))
    n += 1 * len(self.entries_)
    for i in xrange(len(self.entries_)): n += self.lengthString(self.entries_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_owner()
    self.clear_entries()

  def OutputUnchecked(self, out):
    if (self.has_owner_):
      out.putVarInt32(10)
      out.putPrefixedString(self.owner_)
    for i in xrange(len(self.entries_)):
      out.putVarInt32(18)
      out.putVarInt32(self.entries_[i].ByteSize())
      self.entries_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_owner_):
      out.putVarInt32(10)
      out.putPrefixedString(self.owner_)
    for i in xrange(len(self.entries_)):
      out.putVarInt32(18)
      out.putVarInt32(self.entries_[i].ByteSizePartial())
      self.entries_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_owner(d.getPrefixedString())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_entries().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_owner_: res+=prefix+("owner: %s\n" % self.DebugFormatString(self.owner_))
    cnt=0
    for e in self.entries_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("entries%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kowner = 1
  kentries = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "owner",
    2: "entries",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.AccessControlList'
if _extension_runtime:
  pass

__all__ = ['Scope','Entry','AccessControlList']
