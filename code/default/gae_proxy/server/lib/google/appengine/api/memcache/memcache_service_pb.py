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

class MemcacheServiceError(ProtocolBuffer.ProtocolMessage):


  OK           =    0
  UNSPECIFIED_ERROR =    1
  NAMESPACE_NOT_SET =    2
  PERMISSION_DENIED =    3
  INVALID_VALUE =    6
  UNAVAILABLE  =    9

  _ErrorCode_NAMES = {
    0: "OK",
    1: "UNSPECIFIED_ERROR",
    2: "NAMESPACE_NOT_SET",
    3: "PERMISSION_DENIED",
    6: "INVALID_VALUE",
    9: "UNAVAILABLE",
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheServiceError'
class AppOverride(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_num_memcacheg_backends_ = 0
  num_memcacheg_backends_ = 0
  has_ignore_shardlock_ = 0
  ignore_shardlock_ = 0
  has_memcache_pool_hint_ = 0
  memcache_pool_hint_ = ""
  has_memcache_sharding_strategy_ = 0
  memcache_sharding_strategy_ = ""

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

  def num_memcacheg_backends(self): return self.num_memcacheg_backends_

  def set_num_memcacheg_backends(self, x):
    self.has_num_memcacheg_backends_ = 1
    self.num_memcacheg_backends_ = x

  def clear_num_memcacheg_backends(self):
    if self.has_num_memcacheg_backends_:
      self.has_num_memcacheg_backends_ = 0
      self.num_memcacheg_backends_ = 0

  def has_num_memcacheg_backends(self): return self.has_num_memcacheg_backends_

  def ignore_shardlock(self): return self.ignore_shardlock_

  def set_ignore_shardlock(self, x):
    self.has_ignore_shardlock_ = 1
    self.ignore_shardlock_ = x

  def clear_ignore_shardlock(self):
    if self.has_ignore_shardlock_:
      self.has_ignore_shardlock_ = 0
      self.ignore_shardlock_ = 0

  def has_ignore_shardlock(self): return self.has_ignore_shardlock_

  def memcache_pool_hint(self): return self.memcache_pool_hint_

  def set_memcache_pool_hint(self, x):
    self.has_memcache_pool_hint_ = 1
    self.memcache_pool_hint_ = x

  def clear_memcache_pool_hint(self):
    if self.has_memcache_pool_hint_:
      self.has_memcache_pool_hint_ = 0
      self.memcache_pool_hint_ = ""

  def has_memcache_pool_hint(self): return self.has_memcache_pool_hint_

  def memcache_sharding_strategy(self): return self.memcache_sharding_strategy_

  def set_memcache_sharding_strategy(self, x):
    self.has_memcache_sharding_strategy_ = 1
    self.memcache_sharding_strategy_ = x

  def clear_memcache_sharding_strategy(self):
    if self.has_memcache_sharding_strategy_:
      self.has_memcache_sharding_strategy_ = 0
      self.memcache_sharding_strategy_ = ""

  def has_memcache_sharding_strategy(self): return self.has_memcache_sharding_strategy_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_num_memcacheg_backends()): self.set_num_memcacheg_backends(x.num_memcacheg_backends())
    if (x.has_ignore_shardlock()): self.set_ignore_shardlock(x.ignore_shardlock())
    if (x.has_memcache_pool_hint()): self.set_memcache_pool_hint(x.memcache_pool_hint())
    if (x.has_memcache_sharding_strategy()): self.set_memcache_sharding_strategy(x.memcache_sharding_strategy())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_num_memcacheg_backends_ != x.has_num_memcacheg_backends_: return 0
    if self.has_num_memcacheg_backends_ and self.num_memcacheg_backends_ != x.num_memcacheg_backends_: return 0
    if self.has_ignore_shardlock_ != x.has_ignore_shardlock_: return 0
    if self.has_ignore_shardlock_ and self.ignore_shardlock_ != x.ignore_shardlock_: return 0
    if self.has_memcache_pool_hint_ != x.has_memcache_pool_hint_: return 0
    if self.has_memcache_pool_hint_ and self.memcache_pool_hint_ != x.memcache_pool_hint_: return 0
    if self.has_memcache_sharding_strategy_ != x.has_memcache_sharding_strategy_: return 0
    if self.has_memcache_sharding_strategy_ and self.memcache_sharding_strategy_ != x.memcache_sharding_strategy_: return 0
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
    if (self.has_num_memcacheg_backends_): n += 1 + self.lengthVarInt64(self.num_memcacheg_backends_)
    if (self.has_ignore_shardlock_): n += 2
    if (self.has_memcache_pool_hint_): n += 1 + self.lengthString(len(self.memcache_pool_hint_))
    if (self.has_memcache_sharding_strategy_): n += 1 + self.lengthString(len(self.memcache_sharding_strategy_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_):
      n += 1
      n += self.lengthString(len(self.app_id_))
    if (self.has_num_memcacheg_backends_): n += 1 + self.lengthVarInt64(self.num_memcacheg_backends_)
    if (self.has_ignore_shardlock_): n += 2
    if (self.has_memcache_pool_hint_): n += 1 + self.lengthString(len(self.memcache_pool_hint_))
    if (self.has_memcache_sharding_strategy_): n += 1 + self.lengthString(len(self.memcache_sharding_strategy_))
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_num_memcacheg_backends()
    self.clear_ignore_shardlock()
    self.clear_memcache_pool_hint()
    self.clear_memcache_sharding_strategy()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.app_id_)
    if (self.has_num_memcacheg_backends_):
      out.putVarInt32(16)
      out.putVarInt32(self.num_memcacheg_backends_)
    if (self.has_ignore_shardlock_):
      out.putVarInt32(24)
      out.putBoolean(self.ignore_shardlock_)
    if (self.has_memcache_pool_hint_):
      out.putVarInt32(34)
      out.putPrefixedString(self.memcache_pool_hint_)
    if (self.has_memcache_sharding_strategy_):
      out.putVarInt32(42)
      out.putPrefixedString(self.memcache_sharding_strategy_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    if (self.has_num_memcacheg_backends_):
      out.putVarInt32(16)
      out.putVarInt32(self.num_memcacheg_backends_)
    if (self.has_ignore_shardlock_):
      out.putVarInt32(24)
      out.putBoolean(self.ignore_shardlock_)
    if (self.has_memcache_pool_hint_):
      out.putVarInt32(34)
      out.putPrefixedString(self.memcache_pool_hint_)
    if (self.has_memcache_sharding_strategy_):
      out.putVarInt32(42)
      out.putPrefixedString(self.memcache_sharding_strategy_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_num_memcacheg_backends(d.getVarInt32())
        continue
      if tt == 24:
        self.set_ignore_shardlock(d.getBoolean())
        continue
      if tt == 34:
        self.set_memcache_pool_hint(d.getPrefixedString())
        continue
      if tt == 42:
        self.set_memcache_sharding_strategy(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_num_memcacheg_backends_: res+=prefix+("num_memcacheg_backends: %s\n" % self.DebugFormatInt32(self.num_memcacheg_backends_))
    if self.has_ignore_shardlock_: res+=prefix+("ignore_shardlock: %s\n" % self.DebugFormatBool(self.ignore_shardlock_))
    if self.has_memcache_pool_hint_: res+=prefix+("memcache_pool_hint: %s\n" % self.DebugFormatString(self.memcache_pool_hint_))
    if self.has_memcache_sharding_strategy_: res+=prefix+("memcache_sharding_strategy: %s\n" % self.DebugFormatString(self.memcache_sharding_strategy_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  knum_memcacheg_backends = 2
  kignore_shardlock = 3
  kmemcache_pool_hint = 4
  kmemcache_sharding_strategy = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "num_memcacheg_backends",
    3: "ignore_shardlock",
    4: "memcache_pool_hint",
    5: "memcache_sharding_strategy",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.AppOverride'
class MemcacheGetRequest(ProtocolBuffer.ProtocolMessage):
  has_name_space_ = 0
  name_space_ = ""
  has_for_cas_ = 0
  for_cas_ = 0
  has_override_ = 0
  override_ = None

  def __init__(self, contents=None):
    self.key_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def key_size(self): return len(self.key_)
  def key_list(self): return self.key_

  def key(self, i):
    return self.key_[i]

  def set_key(self, i, x):
    self.key_[i] = x

  def add_key(self, x):
    self.key_.append(x)

  def clear_key(self):
    self.key_ = []

  def name_space(self): return self.name_space_

  def set_name_space(self, x):
    self.has_name_space_ = 1
    self.name_space_ = x

  def clear_name_space(self):
    if self.has_name_space_:
      self.has_name_space_ = 0
      self.name_space_ = ""

  def has_name_space(self): return self.has_name_space_

  def for_cas(self): return self.for_cas_

  def set_for_cas(self, x):
    self.has_for_cas_ = 1
    self.for_cas_ = x

  def clear_for_cas(self):
    if self.has_for_cas_:
      self.has_for_cas_ = 0
      self.for_cas_ = 0

  def has_for_cas(self): return self.has_for_cas_

  def override(self):
    if self.override_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.override_ is None: self.override_ = AppOverride()
      finally:
        self.lazy_init_lock_.release()
    return self.override_

  def mutable_override(self): self.has_override_ = 1; return self.override()

  def clear_override(self):

    if self.has_override_:
      self.has_override_ = 0;
      if self.override_ is not None: self.override_.Clear()

  def has_override(self): return self.has_override_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.key_size()): self.add_key(x.key(i))
    if (x.has_name_space()): self.set_name_space(x.name_space())
    if (x.has_for_cas()): self.set_for_cas(x.for_cas())
    if (x.has_override()): self.mutable_override().MergeFrom(x.override())

  def Equals(self, x):
    if x is self: return 1
    if len(self.key_) != len(x.key_): return 0
    for e1, e2 in zip(self.key_, x.key_):
      if e1 != e2: return 0
    if self.has_name_space_ != x.has_name_space_: return 0
    if self.has_name_space_ and self.name_space_ != x.name_space_: return 0
    if self.has_for_cas_ != x.has_for_cas_: return 0
    if self.has_for_cas_ and self.for_cas_ != x.for_cas_: return 0
    if self.has_override_ != x.has_override_: return 0
    if self.has_override_ and self.override_ != x.override_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_override_ and not self.override_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.key_)
    for i in xrange(len(self.key_)): n += self.lengthString(len(self.key_[i]))
    if (self.has_name_space_): n += 1 + self.lengthString(len(self.name_space_))
    if (self.has_for_cas_): n += 2
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.key_)
    for i in xrange(len(self.key_)): n += self.lengthString(len(self.key_[i]))
    if (self.has_name_space_): n += 1 + self.lengthString(len(self.name_space_))
    if (self.has_for_cas_): n += 2
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_key()
    self.clear_name_space()
    self.clear_for_cas()
    self.clear_override()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.key_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.key_[i])
    if (self.has_name_space_):
      out.putVarInt32(18)
      out.putPrefixedString(self.name_space_)
    if (self.has_for_cas_):
      out.putVarInt32(32)
      out.putBoolean(self.for_cas_)
    if (self.has_override_):
      out.putVarInt32(42)
      out.putVarInt32(self.override_.ByteSize())
      self.override_.OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.key_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.key_[i])
    if (self.has_name_space_):
      out.putVarInt32(18)
      out.putPrefixedString(self.name_space_)
    if (self.has_for_cas_):
      out.putVarInt32(32)
      out.putBoolean(self.for_cas_)
    if (self.has_override_):
      out.putVarInt32(42)
      out.putVarInt32(self.override_.ByteSizePartial())
      self.override_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.add_key(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_name_space(d.getPrefixedString())
        continue
      if tt == 32:
        self.set_for_cas(d.getBoolean())
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_override().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.key_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("key%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_name_space_: res+=prefix+("name_space: %s\n" % self.DebugFormatString(self.name_space_))
    if self.has_for_cas_: res+=prefix+("for_cas: %s\n" % self.DebugFormatBool(self.for_cas_))
    if self.has_override_:
      res+=prefix+"override <\n"
      res+=self.override_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kkey = 1
  kname_space = 2
  kfor_cas = 4
  koverride = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "key",
    2: "name_space",
    4: "for_cas",
    5: "override",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheGetRequest'
class MemcacheGetResponse_Item(ProtocolBuffer.ProtocolMessage):
  has_key_ = 0
  key_ = ""
  has_value_ = 0
  value_ = ""
  has_flags_ = 0
  flags_ = 0
  has_cas_id_ = 0
  cas_id_ = 0
  has_expires_in_seconds_ = 0
  expires_in_seconds_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def key(self): return self.key_

  def set_key(self, x):
    self.has_key_ = 1
    self.key_ = x

  def clear_key(self):
    if self.has_key_:
      self.has_key_ = 0
      self.key_ = ""

  def has_key(self): return self.has_key_

  def value(self): return self.value_

  def set_value(self, x):
    self.has_value_ = 1
    self.value_ = x

  def clear_value(self):
    if self.has_value_:
      self.has_value_ = 0
      self.value_ = ""

  def has_value(self): return self.has_value_

  def flags(self): return self.flags_

  def set_flags(self, x):
    self.has_flags_ = 1
    self.flags_ = x

  def clear_flags(self):
    if self.has_flags_:
      self.has_flags_ = 0
      self.flags_ = 0

  def has_flags(self): return self.has_flags_

  def cas_id(self): return self.cas_id_

  def set_cas_id(self, x):
    self.has_cas_id_ = 1
    self.cas_id_ = x

  def clear_cas_id(self):
    if self.has_cas_id_:
      self.has_cas_id_ = 0
      self.cas_id_ = 0

  def has_cas_id(self): return self.has_cas_id_

  def expires_in_seconds(self): return self.expires_in_seconds_

  def set_expires_in_seconds(self, x):
    self.has_expires_in_seconds_ = 1
    self.expires_in_seconds_ = x

  def clear_expires_in_seconds(self):
    if self.has_expires_in_seconds_:
      self.has_expires_in_seconds_ = 0
      self.expires_in_seconds_ = 0

  def has_expires_in_seconds(self): return self.has_expires_in_seconds_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_key()): self.set_key(x.key())
    if (x.has_value()): self.set_value(x.value())
    if (x.has_flags()): self.set_flags(x.flags())
    if (x.has_cas_id()): self.set_cas_id(x.cas_id())
    if (x.has_expires_in_seconds()): self.set_expires_in_seconds(x.expires_in_seconds())

  def Equals(self, x):
    if x is self: return 1
    if self.has_key_ != x.has_key_: return 0
    if self.has_key_ and self.key_ != x.key_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    if self.has_flags_ != x.has_flags_: return 0
    if self.has_flags_ and self.flags_ != x.flags_: return 0
    if self.has_cas_id_ != x.has_cas_id_: return 0
    if self.has_cas_id_ and self.cas_id_ != x.cas_id_: return 0
    if self.has_expires_in_seconds_ != x.has_expires_in_seconds_: return 0
    if self.has_expires_in_seconds_ and self.expires_in_seconds_ != x.expires_in_seconds_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_key_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: key not set.')
    if (not self.has_value_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: value not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.key_))
    n += self.lengthString(len(self.value_))
    if (self.has_flags_): n += 5
    if (self.has_cas_id_): n += 9
    if (self.has_expires_in_seconds_): n += 1 + self.lengthVarInt64(self.expires_in_seconds_)
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_key_):
      n += 1
      n += self.lengthString(len(self.key_))
    if (self.has_value_):
      n += 1
      n += self.lengthString(len(self.value_))
    if (self.has_flags_): n += 5
    if (self.has_cas_id_): n += 9
    if (self.has_expires_in_seconds_): n += 1 + self.lengthVarInt64(self.expires_in_seconds_)
    return n

  def Clear(self):
    self.clear_key()
    self.clear_value()
    self.clear_flags()
    self.clear_cas_id()
    self.clear_expires_in_seconds()

  def OutputUnchecked(self, out):
    out.putVarInt32(18)
    out.putPrefixedString(self.key_)
    out.putVarInt32(26)
    out.putPrefixedString(self.value_)
    if (self.has_flags_):
      out.putVarInt32(37)
      out.put32(self.flags_)
    if (self.has_cas_id_):
      out.putVarInt32(41)
      out.put64(self.cas_id_)
    if (self.has_expires_in_seconds_):
      out.putVarInt32(48)
      out.putVarInt32(self.expires_in_seconds_)

  def OutputPartial(self, out):
    if (self.has_key_):
      out.putVarInt32(18)
      out.putPrefixedString(self.key_)
    if (self.has_value_):
      out.putVarInt32(26)
      out.putPrefixedString(self.value_)
    if (self.has_flags_):
      out.putVarInt32(37)
      out.put32(self.flags_)
    if (self.has_cas_id_):
      out.putVarInt32(41)
      out.put64(self.cas_id_)
    if (self.has_expires_in_seconds_):
      out.putVarInt32(48)
      out.putVarInt32(self.expires_in_seconds_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 12: break
      if tt == 18:
        self.set_key(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_value(d.getPrefixedString())
        continue
      if tt == 37:
        self.set_flags(d.get32())
        continue
      if tt == 41:
        self.set_cas_id(d.get64())
        continue
      if tt == 48:
        self.set_expires_in_seconds(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_: res+=prefix+("key: %s\n" % self.DebugFormatString(self.key_))
    if self.has_value_: res+=prefix+("value: %s\n" % self.DebugFormatString(self.value_))
    if self.has_flags_: res+=prefix+("flags: %s\n" % self.DebugFormatFixed32(self.flags_))
    if self.has_cas_id_: res+=prefix+("cas_id: %s\n" % self.DebugFormatFixed64(self.cas_id_))
    if self.has_expires_in_seconds_: res+=prefix+("expires_in_seconds: %s\n" % self.DebugFormatInt32(self.expires_in_seconds_))
    return res

class MemcacheGetResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.item_ = []
    if contents is not None: self.MergeFromString(contents)

  def item_size(self): return len(self.item_)
  def item_list(self): return self.item_

  def item(self, i):
    return self.item_[i]

  def mutable_item(self, i):
    return self.item_[i]

  def add_item(self):
    x = MemcacheGetResponse_Item()
    self.item_.append(x)
    return x

  def clear_item(self):
    self.item_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.item_size()): self.add_item().CopyFrom(x.item(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.item_) != len(x.item_): return 0
    for e1, e2 in zip(self.item_, x.item_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.item_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 2 * len(self.item_)
    for i in xrange(len(self.item_)): n += self.item_[i].ByteSize()
    return n

  def ByteSizePartial(self):
    n = 0
    n += 2 * len(self.item_)
    for i in xrange(len(self.item_)): n += self.item_[i].ByteSizePartial()
    return n

  def Clear(self):
    self.clear_item()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.item_)):
      out.putVarInt32(11)
      self.item_[i].OutputUnchecked(out)
      out.putVarInt32(12)

  def OutputPartial(self, out):
    for i in xrange(len(self.item_)):
      out.putVarInt32(11)
      self.item_[i].OutputPartial(out)
      out.putVarInt32(12)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 11:
        self.add_item().TryMerge(d)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.item_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Item%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kItemGroup = 1
  kItemkey = 2
  kItemvalue = 3
  kItemflags = 4
  kItemcas_id = 5
  kItemexpires_in_seconds = 6

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "Item",
    2: "key",
    3: "value",
    4: "flags",
    5: "cas_id",
    6: "expires_in_seconds",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STARTGROUP,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.FLOAT,
    5: ProtocolBuffer.Encoder.DOUBLE,
    6: ProtocolBuffer.Encoder.NUMERIC,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheGetResponse'
class MemcacheSetRequest_Item(ProtocolBuffer.ProtocolMessage):
  has_key_ = 0
  key_ = ""
  has_value_ = 0
  value_ = ""
  has_flags_ = 0
  flags_ = 0
  has_set_policy_ = 0
  set_policy_ = 1
  has_expiration_time_ = 0
  expiration_time_ = 0
  has_cas_id_ = 0
  cas_id_ = 0
  has_for_cas_ = 0
  for_cas_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def key(self): return self.key_

  def set_key(self, x):
    self.has_key_ = 1
    self.key_ = x

  def clear_key(self):
    if self.has_key_:
      self.has_key_ = 0
      self.key_ = ""

  def has_key(self): return self.has_key_

  def value(self): return self.value_

  def set_value(self, x):
    self.has_value_ = 1
    self.value_ = x

  def clear_value(self):
    if self.has_value_:
      self.has_value_ = 0
      self.value_ = ""

  def has_value(self): return self.has_value_

  def flags(self): return self.flags_

  def set_flags(self, x):
    self.has_flags_ = 1
    self.flags_ = x

  def clear_flags(self):
    if self.has_flags_:
      self.has_flags_ = 0
      self.flags_ = 0

  def has_flags(self): return self.has_flags_

  def set_policy(self): return self.set_policy_

  def set_set_policy(self, x):
    self.has_set_policy_ = 1
    self.set_policy_ = x

  def clear_set_policy(self):
    if self.has_set_policy_:
      self.has_set_policy_ = 0
      self.set_policy_ = 1

  def has_set_policy(self): return self.has_set_policy_

  def expiration_time(self): return self.expiration_time_

  def set_expiration_time(self, x):
    self.has_expiration_time_ = 1
    self.expiration_time_ = x

  def clear_expiration_time(self):
    if self.has_expiration_time_:
      self.has_expiration_time_ = 0
      self.expiration_time_ = 0

  def has_expiration_time(self): return self.has_expiration_time_

  def cas_id(self): return self.cas_id_

  def set_cas_id(self, x):
    self.has_cas_id_ = 1
    self.cas_id_ = x

  def clear_cas_id(self):
    if self.has_cas_id_:
      self.has_cas_id_ = 0
      self.cas_id_ = 0

  def has_cas_id(self): return self.has_cas_id_

  def for_cas(self): return self.for_cas_

  def set_for_cas(self, x):
    self.has_for_cas_ = 1
    self.for_cas_ = x

  def clear_for_cas(self):
    if self.has_for_cas_:
      self.has_for_cas_ = 0
      self.for_cas_ = 0

  def has_for_cas(self): return self.has_for_cas_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_key()): self.set_key(x.key())
    if (x.has_value()): self.set_value(x.value())
    if (x.has_flags()): self.set_flags(x.flags())
    if (x.has_set_policy()): self.set_set_policy(x.set_policy())
    if (x.has_expiration_time()): self.set_expiration_time(x.expiration_time())
    if (x.has_cas_id()): self.set_cas_id(x.cas_id())
    if (x.has_for_cas()): self.set_for_cas(x.for_cas())

  def Equals(self, x):
    if x is self: return 1
    if self.has_key_ != x.has_key_: return 0
    if self.has_key_ and self.key_ != x.key_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    if self.has_flags_ != x.has_flags_: return 0
    if self.has_flags_ and self.flags_ != x.flags_: return 0
    if self.has_set_policy_ != x.has_set_policy_: return 0
    if self.has_set_policy_ and self.set_policy_ != x.set_policy_: return 0
    if self.has_expiration_time_ != x.has_expiration_time_: return 0
    if self.has_expiration_time_ and self.expiration_time_ != x.expiration_time_: return 0
    if self.has_cas_id_ != x.has_cas_id_: return 0
    if self.has_cas_id_ and self.cas_id_ != x.cas_id_: return 0
    if self.has_for_cas_ != x.has_for_cas_: return 0
    if self.has_for_cas_ and self.for_cas_ != x.for_cas_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_key_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: key not set.')
    if (not self.has_value_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: value not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.key_))
    n += self.lengthString(len(self.value_))
    if (self.has_flags_): n += 5
    if (self.has_set_policy_): n += 1 + self.lengthVarInt64(self.set_policy_)
    if (self.has_expiration_time_): n += 5
    if (self.has_cas_id_): n += 9
    if (self.has_for_cas_): n += 2
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_key_):
      n += 1
      n += self.lengthString(len(self.key_))
    if (self.has_value_):
      n += 1
      n += self.lengthString(len(self.value_))
    if (self.has_flags_): n += 5
    if (self.has_set_policy_): n += 1 + self.lengthVarInt64(self.set_policy_)
    if (self.has_expiration_time_): n += 5
    if (self.has_cas_id_): n += 9
    if (self.has_for_cas_): n += 2
    return n

  def Clear(self):
    self.clear_key()
    self.clear_value()
    self.clear_flags()
    self.clear_set_policy()
    self.clear_expiration_time()
    self.clear_cas_id()
    self.clear_for_cas()

  def OutputUnchecked(self, out):
    out.putVarInt32(18)
    out.putPrefixedString(self.key_)
    out.putVarInt32(26)
    out.putPrefixedString(self.value_)
    if (self.has_flags_):
      out.putVarInt32(37)
      out.put32(self.flags_)
    if (self.has_set_policy_):
      out.putVarInt32(40)
      out.putVarInt32(self.set_policy_)
    if (self.has_expiration_time_):
      out.putVarInt32(53)
      out.put32(self.expiration_time_)
    if (self.has_cas_id_):
      out.putVarInt32(65)
      out.put64(self.cas_id_)
    if (self.has_for_cas_):
      out.putVarInt32(72)
      out.putBoolean(self.for_cas_)

  def OutputPartial(self, out):
    if (self.has_key_):
      out.putVarInt32(18)
      out.putPrefixedString(self.key_)
    if (self.has_value_):
      out.putVarInt32(26)
      out.putPrefixedString(self.value_)
    if (self.has_flags_):
      out.putVarInt32(37)
      out.put32(self.flags_)
    if (self.has_set_policy_):
      out.putVarInt32(40)
      out.putVarInt32(self.set_policy_)
    if (self.has_expiration_time_):
      out.putVarInt32(53)
      out.put32(self.expiration_time_)
    if (self.has_cas_id_):
      out.putVarInt32(65)
      out.put64(self.cas_id_)
    if (self.has_for_cas_):
      out.putVarInt32(72)
      out.putBoolean(self.for_cas_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 12: break
      if tt == 18:
        self.set_key(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_value(d.getPrefixedString())
        continue
      if tt == 37:
        self.set_flags(d.get32())
        continue
      if tt == 40:
        self.set_set_policy(d.getVarInt32())
        continue
      if tt == 53:
        self.set_expiration_time(d.get32())
        continue
      if tt == 65:
        self.set_cas_id(d.get64())
        continue
      if tt == 72:
        self.set_for_cas(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_: res+=prefix+("key: %s\n" % self.DebugFormatString(self.key_))
    if self.has_value_: res+=prefix+("value: %s\n" % self.DebugFormatString(self.value_))
    if self.has_flags_: res+=prefix+("flags: %s\n" % self.DebugFormatFixed32(self.flags_))
    if self.has_set_policy_: res+=prefix+("set_policy: %s\n" % self.DebugFormatInt32(self.set_policy_))
    if self.has_expiration_time_: res+=prefix+("expiration_time: %s\n" % self.DebugFormatFixed32(self.expiration_time_))
    if self.has_cas_id_: res+=prefix+("cas_id: %s\n" % self.DebugFormatFixed64(self.cas_id_))
    if self.has_for_cas_: res+=prefix+("for_cas: %s\n" % self.DebugFormatBool(self.for_cas_))
    return res

class MemcacheSetRequest(ProtocolBuffer.ProtocolMessage):


  SET          =    1
  ADD          =    2
  REPLACE      =    3
  CAS          =    4

  _SetPolicy_NAMES = {
    1: "SET",
    2: "ADD",
    3: "REPLACE",
    4: "CAS",
  }

  def SetPolicy_Name(cls, x): return cls._SetPolicy_NAMES.get(x, "")
  SetPolicy_Name = classmethod(SetPolicy_Name)

  has_name_space_ = 0
  name_space_ = ""
  has_override_ = 0
  override_ = None

  def __init__(self, contents=None):
    self.item_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def item_size(self): return len(self.item_)
  def item_list(self): return self.item_

  def item(self, i):
    return self.item_[i]

  def mutable_item(self, i):
    return self.item_[i]

  def add_item(self):
    x = MemcacheSetRequest_Item()
    self.item_.append(x)
    return x

  def clear_item(self):
    self.item_ = []
  def name_space(self): return self.name_space_

  def set_name_space(self, x):
    self.has_name_space_ = 1
    self.name_space_ = x

  def clear_name_space(self):
    if self.has_name_space_:
      self.has_name_space_ = 0
      self.name_space_ = ""

  def has_name_space(self): return self.has_name_space_

  def override(self):
    if self.override_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.override_ is None: self.override_ = AppOverride()
      finally:
        self.lazy_init_lock_.release()
    return self.override_

  def mutable_override(self): self.has_override_ = 1; return self.override()

  def clear_override(self):

    if self.has_override_:
      self.has_override_ = 0;
      if self.override_ is not None: self.override_.Clear()

  def has_override(self): return self.has_override_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.item_size()): self.add_item().CopyFrom(x.item(i))
    if (x.has_name_space()): self.set_name_space(x.name_space())
    if (x.has_override()): self.mutable_override().MergeFrom(x.override())

  def Equals(self, x):
    if x is self: return 1
    if len(self.item_) != len(x.item_): return 0
    for e1, e2 in zip(self.item_, x.item_):
      if e1 != e2: return 0
    if self.has_name_space_ != x.has_name_space_: return 0
    if self.has_name_space_ and self.name_space_ != x.name_space_: return 0
    if self.has_override_ != x.has_override_: return 0
    if self.has_override_ and self.override_ != x.override_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.item_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_override_ and not self.override_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += 2 * len(self.item_)
    for i in xrange(len(self.item_)): n += self.item_[i].ByteSize()
    if (self.has_name_space_): n += 1 + self.lengthString(len(self.name_space_))
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 2 * len(self.item_)
    for i in xrange(len(self.item_)): n += self.item_[i].ByteSizePartial()
    if (self.has_name_space_): n += 1 + self.lengthString(len(self.name_space_))
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_item()
    self.clear_name_space()
    self.clear_override()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.item_)):
      out.putVarInt32(11)
      self.item_[i].OutputUnchecked(out)
      out.putVarInt32(12)
    if (self.has_name_space_):
      out.putVarInt32(58)
      out.putPrefixedString(self.name_space_)
    if (self.has_override_):
      out.putVarInt32(82)
      out.putVarInt32(self.override_.ByteSize())
      self.override_.OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.item_)):
      out.putVarInt32(11)
      self.item_[i].OutputPartial(out)
      out.putVarInt32(12)
    if (self.has_name_space_):
      out.putVarInt32(58)
      out.putPrefixedString(self.name_space_)
    if (self.has_override_):
      out.putVarInt32(82)
      out.putVarInt32(self.override_.ByteSizePartial())
      self.override_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 11:
        self.add_item().TryMerge(d)
        continue
      if tt == 58:
        self.set_name_space(d.getPrefixedString())
        continue
      if tt == 82:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_override().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.item_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Item%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    if self.has_name_space_: res+=prefix+("name_space: %s\n" % self.DebugFormatString(self.name_space_))
    if self.has_override_:
      res+=prefix+"override <\n"
      res+=self.override_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kItemGroup = 1
  kItemkey = 2
  kItemvalue = 3
  kItemflags = 4
  kItemset_policy = 5
  kItemexpiration_time = 6
  kItemcas_id = 8
  kItemfor_cas = 9
  kname_space = 7
  koverride = 10

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "Item",
    2: "key",
    3: "value",
    4: "flags",
    5: "set_policy",
    6: "expiration_time",
    7: "name_space",
    8: "cas_id",
    9: "for_cas",
    10: "override",
  }, 10)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STARTGROUP,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.FLOAT,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.FLOAT,
    7: ProtocolBuffer.Encoder.STRING,
    8: ProtocolBuffer.Encoder.DOUBLE,
    9: ProtocolBuffer.Encoder.NUMERIC,
    10: ProtocolBuffer.Encoder.STRING,
  }, 10, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheSetRequest'
class MemcacheSetResponse(ProtocolBuffer.ProtocolMessage):


  STORED       =    1
  NOT_STORED   =    2
  ERROR        =    3
  EXISTS       =    4

  _SetStatusCode_NAMES = {
    1: "STORED",
    2: "NOT_STORED",
    3: "ERROR",
    4: "EXISTS",
  }

  def SetStatusCode_Name(cls, x): return cls._SetStatusCode_NAMES.get(x, "")
  SetStatusCode_Name = classmethod(SetStatusCode_Name)


  def __init__(self, contents=None):
    self.set_status_ = []
    if contents is not None: self.MergeFromString(contents)

  def set_status_size(self): return len(self.set_status_)
  def set_status_list(self): return self.set_status_

  def set_status(self, i):
    return self.set_status_[i]

  def set_set_status(self, i, x):
    self.set_status_[i] = x

  def add_set_status(self, x):
    self.set_status_.append(x)

  def clear_set_status(self):
    self.set_status_ = []


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.set_status_size()): self.add_set_status(x.set_status(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.set_status_) != len(x.set_status_): return 0
    for e1, e2 in zip(self.set_status_, x.set_status_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.set_status_)
    for i in xrange(len(self.set_status_)): n += self.lengthVarInt64(self.set_status_[i])
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.set_status_)
    for i in xrange(len(self.set_status_)): n += self.lengthVarInt64(self.set_status_[i])
    return n

  def Clear(self):
    self.clear_set_status()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.set_status_)):
      out.putVarInt32(8)
      out.putVarInt32(self.set_status_[i])

  def OutputPartial(self, out):
    for i in xrange(len(self.set_status_)):
      out.putVarInt32(8)
      out.putVarInt32(self.set_status_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.add_set_status(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.set_status_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("set_status%s: %s\n" % (elm, self.DebugFormatInt32(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kset_status = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "set_status",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheSetResponse'
class MemcacheDeleteRequest_Item(ProtocolBuffer.ProtocolMessage):
  has_key_ = 0
  key_ = ""
  has_delete_time_ = 0
  delete_time_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def key(self): return self.key_

  def set_key(self, x):
    self.has_key_ = 1
    self.key_ = x

  def clear_key(self):
    if self.has_key_:
      self.has_key_ = 0
      self.key_ = ""

  def has_key(self): return self.has_key_

  def delete_time(self): return self.delete_time_

  def set_delete_time(self, x):
    self.has_delete_time_ = 1
    self.delete_time_ = x

  def clear_delete_time(self):
    if self.has_delete_time_:
      self.has_delete_time_ = 0
      self.delete_time_ = 0

  def has_delete_time(self): return self.has_delete_time_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_key()): self.set_key(x.key())
    if (x.has_delete_time()): self.set_delete_time(x.delete_time())

  def Equals(self, x):
    if x is self: return 1
    if self.has_key_ != x.has_key_: return 0
    if self.has_key_ and self.key_ != x.key_: return 0
    if self.has_delete_time_ != x.has_delete_time_: return 0
    if self.has_delete_time_ and self.delete_time_ != x.delete_time_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_key_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: key not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.key_))
    if (self.has_delete_time_): n += 5
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_key_):
      n += 1
      n += self.lengthString(len(self.key_))
    if (self.has_delete_time_): n += 5
    return n

  def Clear(self):
    self.clear_key()
    self.clear_delete_time()

  def OutputUnchecked(self, out):
    out.putVarInt32(18)
    out.putPrefixedString(self.key_)
    if (self.has_delete_time_):
      out.putVarInt32(29)
      out.put32(self.delete_time_)

  def OutputPartial(self, out):
    if (self.has_key_):
      out.putVarInt32(18)
      out.putPrefixedString(self.key_)
    if (self.has_delete_time_):
      out.putVarInt32(29)
      out.put32(self.delete_time_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 12: break
      if tt == 18:
        self.set_key(d.getPrefixedString())
        continue
      if tt == 29:
        self.set_delete_time(d.get32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_: res+=prefix+("key: %s\n" % self.DebugFormatString(self.key_))
    if self.has_delete_time_: res+=prefix+("delete_time: %s\n" % self.DebugFormatFixed32(self.delete_time_))
    return res

class MemcacheDeleteRequest(ProtocolBuffer.ProtocolMessage):
  has_name_space_ = 0
  name_space_ = ""
  has_override_ = 0
  override_ = None

  def __init__(self, contents=None):
    self.item_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def item_size(self): return len(self.item_)
  def item_list(self): return self.item_

  def item(self, i):
    return self.item_[i]

  def mutable_item(self, i):
    return self.item_[i]

  def add_item(self):
    x = MemcacheDeleteRequest_Item()
    self.item_.append(x)
    return x

  def clear_item(self):
    self.item_ = []
  def name_space(self): return self.name_space_

  def set_name_space(self, x):
    self.has_name_space_ = 1
    self.name_space_ = x

  def clear_name_space(self):
    if self.has_name_space_:
      self.has_name_space_ = 0
      self.name_space_ = ""

  def has_name_space(self): return self.has_name_space_

  def override(self):
    if self.override_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.override_ is None: self.override_ = AppOverride()
      finally:
        self.lazy_init_lock_.release()
    return self.override_

  def mutable_override(self): self.has_override_ = 1; return self.override()

  def clear_override(self):

    if self.has_override_:
      self.has_override_ = 0;
      if self.override_ is not None: self.override_.Clear()

  def has_override(self): return self.has_override_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.item_size()): self.add_item().CopyFrom(x.item(i))
    if (x.has_name_space()): self.set_name_space(x.name_space())
    if (x.has_override()): self.mutable_override().MergeFrom(x.override())

  def Equals(self, x):
    if x is self: return 1
    if len(self.item_) != len(x.item_): return 0
    for e1, e2 in zip(self.item_, x.item_):
      if e1 != e2: return 0
    if self.has_name_space_ != x.has_name_space_: return 0
    if self.has_name_space_ and self.name_space_ != x.name_space_: return 0
    if self.has_override_ != x.has_override_: return 0
    if self.has_override_ and self.override_ != x.override_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.item_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_override_ and not self.override_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += 2 * len(self.item_)
    for i in xrange(len(self.item_)): n += self.item_[i].ByteSize()
    if (self.has_name_space_): n += 1 + self.lengthString(len(self.name_space_))
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 2 * len(self.item_)
    for i in xrange(len(self.item_)): n += self.item_[i].ByteSizePartial()
    if (self.has_name_space_): n += 1 + self.lengthString(len(self.name_space_))
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_item()
    self.clear_name_space()
    self.clear_override()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.item_)):
      out.putVarInt32(11)
      self.item_[i].OutputUnchecked(out)
      out.putVarInt32(12)
    if (self.has_name_space_):
      out.putVarInt32(34)
      out.putPrefixedString(self.name_space_)
    if (self.has_override_):
      out.putVarInt32(42)
      out.putVarInt32(self.override_.ByteSize())
      self.override_.OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.item_)):
      out.putVarInt32(11)
      self.item_[i].OutputPartial(out)
      out.putVarInt32(12)
    if (self.has_name_space_):
      out.putVarInt32(34)
      out.putPrefixedString(self.name_space_)
    if (self.has_override_):
      out.putVarInt32(42)
      out.putVarInt32(self.override_.ByteSizePartial())
      self.override_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 11:
        self.add_item().TryMerge(d)
        continue
      if tt == 34:
        self.set_name_space(d.getPrefixedString())
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_override().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.item_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Item%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    if self.has_name_space_: res+=prefix+("name_space: %s\n" % self.DebugFormatString(self.name_space_))
    if self.has_override_:
      res+=prefix+"override <\n"
      res+=self.override_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kItemGroup = 1
  kItemkey = 2
  kItemdelete_time = 3
  kname_space = 4
  koverride = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "Item",
    2: "key",
    3: "delete_time",
    4: "name_space",
    5: "override",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STARTGROUP,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.FLOAT,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheDeleteRequest'
class MemcacheDeleteResponse(ProtocolBuffer.ProtocolMessage):


  DELETED      =    1
  NOT_FOUND    =    2

  _DeleteStatusCode_NAMES = {
    1: "DELETED",
    2: "NOT_FOUND",
  }

  def DeleteStatusCode_Name(cls, x): return cls._DeleteStatusCode_NAMES.get(x, "")
  DeleteStatusCode_Name = classmethod(DeleteStatusCode_Name)


  def __init__(self, contents=None):
    self.delete_status_ = []
    if contents is not None: self.MergeFromString(contents)

  def delete_status_size(self): return len(self.delete_status_)
  def delete_status_list(self): return self.delete_status_

  def delete_status(self, i):
    return self.delete_status_[i]

  def set_delete_status(self, i, x):
    self.delete_status_[i] = x

  def add_delete_status(self, x):
    self.delete_status_.append(x)

  def clear_delete_status(self):
    self.delete_status_ = []


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.delete_status_size()): self.add_delete_status(x.delete_status(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.delete_status_) != len(x.delete_status_): return 0
    for e1, e2 in zip(self.delete_status_, x.delete_status_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.delete_status_)
    for i in xrange(len(self.delete_status_)): n += self.lengthVarInt64(self.delete_status_[i])
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.delete_status_)
    for i in xrange(len(self.delete_status_)): n += self.lengthVarInt64(self.delete_status_[i])
    return n

  def Clear(self):
    self.clear_delete_status()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.delete_status_)):
      out.putVarInt32(8)
      out.putVarInt32(self.delete_status_[i])

  def OutputPartial(self, out):
    for i in xrange(len(self.delete_status_)):
      out.putVarInt32(8)
      out.putVarInt32(self.delete_status_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.add_delete_status(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.delete_status_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("delete_status%s: %s\n" % (elm, self.DebugFormatInt32(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kdelete_status = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "delete_status",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheDeleteResponse'
class MemcacheIncrementRequest(ProtocolBuffer.ProtocolMessage):


  INCREMENT    =    1
  DECREMENT    =    2

  _Direction_NAMES = {
    1: "INCREMENT",
    2: "DECREMENT",
  }

  def Direction_Name(cls, x): return cls._Direction_NAMES.get(x, "")
  Direction_Name = classmethod(Direction_Name)

  has_key_ = 0
  key_ = ""
  has_name_space_ = 0
  name_space_ = ""
  has_delta_ = 0
  delta_ = 1
  has_direction_ = 0
  direction_ = 1
  has_initial_value_ = 0
  initial_value_ = 0
  has_initial_flags_ = 0
  initial_flags_ = 0
  has_override_ = 0
  override_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def key(self): return self.key_

  def set_key(self, x):
    self.has_key_ = 1
    self.key_ = x

  def clear_key(self):
    if self.has_key_:
      self.has_key_ = 0
      self.key_ = ""

  def has_key(self): return self.has_key_

  def name_space(self): return self.name_space_

  def set_name_space(self, x):
    self.has_name_space_ = 1
    self.name_space_ = x

  def clear_name_space(self):
    if self.has_name_space_:
      self.has_name_space_ = 0
      self.name_space_ = ""

  def has_name_space(self): return self.has_name_space_

  def delta(self): return self.delta_

  def set_delta(self, x):
    self.has_delta_ = 1
    self.delta_ = x

  def clear_delta(self):
    if self.has_delta_:
      self.has_delta_ = 0
      self.delta_ = 1

  def has_delta(self): return self.has_delta_

  def direction(self): return self.direction_

  def set_direction(self, x):
    self.has_direction_ = 1
    self.direction_ = x

  def clear_direction(self):
    if self.has_direction_:
      self.has_direction_ = 0
      self.direction_ = 1

  def has_direction(self): return self.has_direction_

  def initial_value(self): return self.initial_value_

  def set_initial_value(self, x):
    self.has_initial_value_ = 1
    self.initial_value_ = x

  def clear_initial_value(self):
    if self.has_initial_value_:
      self.has_initial_value_ = 0
      self.initial_value_ = 0

  def has_initial_value(self): return self.has_initial_value_

  def initial_flags(self): return self.initial_flags_

  def set_initial_flags(self, x):
    self.has_initial_flags_ = 1
    self.initial_flags_ = x

  def clear_initial_flags(self):
    if self.has_initial_flags_:
      self.has_initial_flags_ = 0
      self.initial_flags_ = 0

  def has_initial_flags(self): return self.has_initial_flags_

  def override(self):
    if self.override_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.override_ is None: self.override_ = AppOverride()
      finally:
        self.lazy_init_lock_.release()
    return self.override_

  def mutable_override(self): self.has_override_ = 1; return self.override()

  def clear_override(self):

    if self.has_override_:
      self.has_override_ = 0;
      if self.override_ is not None: self.override_.Clear()

  def has_override(self): return self.has_override_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_key()): self.set_key(x.key())
    if (x.has_name_space()): self.set_name_space(x.name_space())
    if (x.has_delta()): self.set_delta(x.delta())
    if (x.has_direction()): self.set_direction(x.direction())
    if (x.has_initial_value()): self.set_initial_value(x.initial_value())
    if (x.has_initial_flags()): self.set_initial_flags(x.initial_flags())
    if (x.has_override()): self.mutable_override().MergeFrom(x.override())

  def Equals(self, x):
    if x is self: return 1
    if self.has_key_ != x.has_key_: return 0
    if self.has_key_ and self.key_ != x.key_: return 0
    if self.has_name_space_ != x.has_name_space_: return 0
    if self.has_name_space_ and self.name_space_ != x.name_space_: return 0
    if self.has_delta_ != x.has_delta_: return 0
    if self.has_delta_ and self.delta_ != x.delta_: return 0
    if self.has_direction_ != x.has_direction_: return 0
    if self.has_direction_ and self.direction_ != x.direction_: return 0
    if self.has_initial_value_ != x.has_initial_value_: return 0
    if self.has_initial_value_ and self.initial_value_ != x.initial_value_: return 0
    if self.has_initial_flags_ != x.has_initial_flags_: return 0
    if self.has_initial_flags_ and self.initial_flags_ != x.initial_flags_: return 0
    if self.has_override_ != x.has_override_: return 0
    if self.has_override_ and self.override_ != x.override_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_key_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: key not set.')
    if (self.has_override_ and not self.override_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.key_))
    if (self.has_name_space_): n += 1 + self.lengthString(len(self.name_space_))
    if (self.has_delta_): n += 1 + self.lengthVarInt64(self.delta_)
    if (self.has_direction_): n += 1 + self.lengthVarInt64(self.direction_)
    if (self.has_initial_value_): n += 1 + self.lengthVarInt64(self.initial_value_)
    if (self.has_initial_flags_): n += 5
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_key_):
      n += 1
      n += self.lengthString(len(self.key_))
    if (self.has_name_space_): n += 1 + self.lengthString(len(self.name_space_))
    if (self.has_delta_): n += 1 + self.lengthVarInt64(self.delta_)
    if (self.has_direction_): n += 1 + self.lengthVarInt64(self.direction_)
    if (self.has_initial_value_): n += 1 + self.lengthVarInt64(self.initial_value_)
    if (self.has_initial_flags_): n += 5
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_key()
    self.clear_name_space()
    self.clear_delta()
    self.clear_direction()
    self.clear_initial_value()
    self.clear_initial_flags()
    self.clear_override()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.key_)
    if (self.has_delta_):
      out.putVarInt32(16)
      out.putVarUint64(self.delta_)
    if (self.has_direction_):
      out.putVarInt32(24)
      out.putVarInt32(self.direction_)
    if (self.has_name_space_):
      out.putVarInt32(34)
      out.putPrefixedString(self.name_space_)
    if (self.has_initial_value_):
      out.putVarInt32(40)
      out.putVarUint64(self.initial_value_)
    if (self.has_initial_flags_):
      out.putVarInt32(53)
      out.put32(self.initial_flags_)
    if (self.has_override_):
      out.putVarInt32(58)
      out.putVarInt32(self.override_.ByteSize())
      self.override_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_key_):
      out.putVarInt32(10)
      out.putPrefixedString(self.key_)
    if (self.has_delta_):
      out.putVarInt32(16)
      out.putVarUint64(self.delta_)
    if (self.has_direction_):
      out.putVarInt32(24)
      out.putVarInt32(self.direction_)
    if (self.has_name_space_):
      out.putVarInt32(34)
      out.putPrefixedString(self.name_space_)
    if (self.has_initial_value_):
      out.putVarInt32(40)
      out.putVarUint64(self.initial_value_)
    if (self.has_initial_flags_):
      out.putVarInt32(53)
      out.put32(self.initial_flags_)
    if (self.has_override_):
      out.putVarInt32(58)
      out.putVarInt32(self.override_.ByteSizePartial())
      self.override_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_key(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_delta(d.getVarUint64())
        continue
      if tt == 24:
        self.set_direction(d.getVarInt32())
        continue
      if tt == 34:
        self.set_name_space(d.getPrefixedString())
        continue
      if tt == 40:
        self.set_initial_value(d.getVarUint64())
        continue
      if tt == 53:
        self.set_initial_flags(d.get32())
        continue
      if tt == 58:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_override().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_: res+=prefix+("key: %s\n" % self.DebugFormatString(self.key_))
    if self.has_name_space_: res+=prefix+("name_space: %s\n" % self.DebugFormatString(self.name_space_))
    if self.has_delta_: res+=prefix+("delta: %s\n" % self.DebugFormatInt64(self.delta_))
    if self.has_direction_: res+=prefix+("direction: %s\n" % self.DebugFormatInt32(self.direction_))
    if self.has_initial_value_: res+=prefix+("initial_value: %s\n" % self.DebugFormatInt64(self.initial_value_))
    if self.has_initial_flags_: res+=prefix+("initial_flags: %s\n" % self.DebugFormatFixed32(self.initial_flags_))
    if self.has_override_:
      res+=prefix+"override <\n"
      res+=self.override_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kkey = 1
  kname_space = 4
  kdelta = 2
  kdirection = 3
  kinitial_value = 5
  kinitial_flags = 6
  koverride = 7

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "key",
    2: "delta",
    3: "direction",
    4: "name_space",
    5: "initial_value",
    6: "initial_flags",
    7: "override",
  }, 7)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.FLOAT,
    7: ProtocolBuffer.Encoder.STRING,
  }, 7, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheIncrementRequest'
class MemcacheIncrementResponse(ProtocolBuffer.ProtocolMessage):


  OK           =    1
  NOT_CHANGED  =    2
  ERROR        =    3

  _IncrementStatusCode_NAMES = {
    1: "OK",
    2: "NOT_CHANGED",
    3: "ERROR",
  }

  def IncrementStatusCode_Name(cls, x): return cls._IncrementStatusCode_NAMES.get(x, "")
  IncrementStatusCode_Name = classmethod(IncrementStatusCode_Name)

  has_new_value_ = 0
  new_value_ = 0
  has_increment_status_ = 0
  increment_status_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def new_value(self): return self.new_value_

  def set_new_value(self, x):
    self.has_new_value_ = 1
    self.new_value_ = x

  def clear_new_value(self):
    if self.has_new_value_:
      self.has_new_value_ = 0
      self.new_value_ = 0

  def has_new_value(self): return self.has_new_value_

  def increment_status(self): return self.increment_status_

  def set_increment_status(self, x):
    self.has_increment_status_ = 1
    self.increment_status_ = x

  def clear_increment_status(self):
    if self.has_increment_status_:
      self.has_increment_status_ = 0
      self.increment_status_ = 0

  def has_increment_status(self): return self.has_increment_status_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_new_value()): self.set_new_value(x.new_value())
    if (x.has_increment_status()): self.set_increment_status(x.increment_status())

  def Equals(self, x):
    if x is self: return 1
    if self.has_new_value_ != x.has_new_value_: return 0
    if self.has_new_value_ and self.new_value_ != x.new_value_: return 0
    if self.has_increment_status_ != x.has_increment_status_: return 0
    if self.has_increment_status_ and self.increment_status_ != x.increment_status_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_new_value_): n += 1 + self.lengthVarInt64(self.new_value_)
    if (self.has_increment_status_): n += 1 + self.lengthVarInt64(self.increment_status_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_new_value_): n += 1 + self.lengthVarInt64(self.new_value_)
    if (self.has_increment_status_): n += 1 + self.lengthVarInt64(self.increment_status_)
    return n

  def Clear(self):
    self.clear_new_value()
    self.clear_increment_status()

  def OutputUnchecked(self, out):
    if (self.has_new_value_):
      out.putVarInt32(8)
      out.putVarUint64(self.new_value_)
    if (self.has_increment_status_):
      out.putVarInt32(16)
      out.putVarInt32(self.increment_status_)

  def OutputPartial(self, out):
    if (self.has_new_value_):
      out.putVarInt32(8)
      out.putVarUint64(self.new_value_)
    if (self.has_increment_status_):
      out.putVarInt32(16)
      out.putVarInt32(self.increment_status_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_new_value(d.getVarUint64())
        continue
      if tt == 16:
        self.set_increment_status(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_new_value_: res+=prefix+("new_value: %s\n" % self.DebugFormatInt64(self.new_value_))
    if self.has_increment_status_: res+=prefix+("increment_status: %s\n" % self.DebugFormatInt32(self.increment_status_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  knew_value = 1
  kincrement_status = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "new_value",
    2: "increment_status",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheIncrementResponse'
class MemcacheBatchIncrementRequest(ProtocolBuffer.ProtocolMessage):
  has_name_space_ = 0
  name_space_ = ""
  has_override_ = 0
  override_ = None

  def __init__(self, contents=None):
    self.item_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def name_space(self): return self.name_space_

  def set_name_space(self, x):
    self.has_name_space_ = 1
    self.name_space_ = x

  def clear_name_space(self):
    if self.has_name_space_:
      self.has_name_space_ = 0
      self.name_space_ = ""

  def has_name_space(self): return self.has_name_space_

  def item_size(self): return len(self.item_)
  def item_list(self): return self.item_

  def item(self, i):
    return self.item_[i]

  def mutable_item(self, i):
    return self.item_[i]

  def add_item(self):
    x = MemcacheIncrementRequest()
    self.item_.append(x)
    return x

  def clear_item(self):
    self.item_ = []
  def override(self):
    if self.override_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.override_ is None: self.override_ = AppOverride()
      finally:
        self.lazy_init_lock_.release()
    return self.override_

  def mutable_override(self): self.has_override_ = 1; return self.override()

  def clear_override(self):

    if self.has_override_:
      self.has_override_ = 0;
      if self.override_ is not None: self.override_.Clear()

  def has_override(self): return self.has_override_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name_space()): self.set_name_space(x.name_space())
    for i in xrange(x.item_size()): self.add_item().CopyFrom(x.item(i))
    if (x.has_override()): self.mutable_override().MergeFrom(x.override())

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_space_ != x.has_name_space_: return 0
    if self.has_name_space_ and self.name_space_ != x.name_space_: return 0
    if len(self.item_) != len(x.item_): return 0
    for e1, e2 in zip(self.item_, x.item_):
      if e1 != e2: return 0
    if self.has_override_ != x.has_override_: return 0
    if self.has_override_ and self.override_ != x.override_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.item_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_override_ and not self.override_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_name_space_): n += 1 + self.lengthString(len(self.name_space_))
    n += 1 * len(self.item_)
    for i in xrange(len(self.item_)): n += self.lengthString(self.item_[i].ByteSize())
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_space_): n += 1 + self.lengthString(len(self.name_space_))
    n += 1 * len(self.item_)
    for i in xrange(len(self.item_)): n += self.lengthString(self.item_[i].ByteSizePartial())
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_name_space()
    self.clear_item()
    self.clear_override()

  def OutputUnchecked(self, out):
    if (self.has_name_space_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_space_)
    for i in xrange(len(self.item_)):
      out.putVarInt32(18)
      out.putVarInt32(self.item_[i].ByteSize())
      self.item_[i].OutputUnchecked(out)
    if (self.has_override_):
      out.putVarInt32(26)
      out.putVarInt32(self.override_.ByteSize())
      self.override_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_name_space_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_space_)
    for i in xrange(len(self.item_)):
      out.putVarInt32(18)
      out.putVarInt32(self.item_[i].ByteSizePartial())
      self.item_[i].OutputPartial(out)
    if (self.has_override_):
      out.putVarInt32(26)
      out.putVarInt32(self.override_.ByteSizePartial())
      self.override_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_name_space(d.getPrefixedString())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_item().TryMerge(tmp)
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_override().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_space_: res+=prefix+("name_space: %s\n" % self.DebugFormatString(self.name_space_))
    cnt=0
    for e in self.item_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("item%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_override_:
      res+=prefix+"override <\n"
      res+=self.override_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname_space = 1
  kitem = 2
  koverride = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name_space",
    2: "item",
    3: "override",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheBatchIncrementRequest'
class MemcacheBatchIncrementResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.item_ = []
    if contents is not None: self.MergeFromString(contents)

  def item_size(self): return len(self.item_)
  def item_list(self): return self.item_

  def item(self, i):
    return self.item_[i]

  def mutable_item(self, i):
    return self.item_[i]

  def add_item(self):
    x = MemcacheIncrementResponse()
    self.item_.append(x)
    return x

  def clear_item(self):
    self.item_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.item_size()): self.add_item().CopyFrom(x.item(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.item_) != len(x.item_): return 0
    for e1, e2 in zip(self.item_, x.item_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.item_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.item_)
    for i in xrange(len(self.item_)): n += self.lengthString(self.item_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.item_)
    for i in xrange(len(self.item_)): n += self.lengthString(self.item_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_item()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.item_)):
      out.putVarInt32(10)
      out.putVarInt32(self.item_[i].ByteSize())
      self.item_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.item_)):
      out.putVarInt32(10)
      out.putVarInt32(self.item_[i].ByteSizePartial())
      self.item_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_item().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.item_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("item%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kitem = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "item",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheBatchIncrementResponse'
class MemcacheFlushRequest(ProtocolBuffer.ProtocolMessage):
  has_override_ = 0
  override_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def override(self):
    if self.override_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.override_ is None: self.override_ = AppOverride()
      finally:
        self.lazy_init_lock_.release()
    return self.override_

  def mutable_override(self): self.has_override_ = 1; return self.override()

  def clear_override(self):

    if self.has_override_:
      self.has_override_ = 0;
      if self.override_ is not None: self.override_.Clear()

  def has_override(self): return self.has_override_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_override()): self.mutable_override().MergeFrom(x.override())

  def Equals(self, x):
    if x is self: return 1
    if self.has_override_ != x.has_override_: return 0
    if self.has_override_ and self.override_ != x.override_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_override_ and not self.override_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_override()

  def OutputUnchecked(self, out):
    if (self.has_override_):
      out.putVarInt32(10)
      out.putVarInt32(self.override_.ByteSize())
      self.override_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_override_):
      out.putVarInt32(10)
      out.putVarInt32(self.override_.ByteSizePartial())
      self.override_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_override().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_override_:
      res+=prefix+"override <\n"
      res+=self.override_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  koverride = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "override",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheFlushRequest'
class MemcacheFlushResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheFlushResponse'
class MemcacheStatsRequest(ProtocolBuffer.ProtocolMessage):
  has_override_ = 0
  override_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def override(self):
    if self.override_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.override_ is None: self.override_ = AppOverride()
      finally:
        self.lazy_init_lock_.release()
    return self.override_

  def mutable_override(self): self.has_override_ = 1; return self.override()

  def clear_override(self):

    if self.has_override_:
      self.has_override_ = 0;
      if self.override_ is not None: self.override_.Clear()

  def has_override(self): return self.has_override_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_override()): self.mutable_override().MergeFrom(x.override())

  def Equals(self, x):
    if x is self: return 1
    if self.has_override_ != x.has_override_: return 0
    if self.has_override_ and self.override_ != x.override_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_override_ and not self.override_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_override()

  def OutputUnchecked(self, out):
    if (self.has_override_):
      out.putVarInt32(10)
      out.putVarInt32(self.override_.ByteSize())
      self.override_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_override_):
      out.putVarInt32(10)
      out.putVarInt32(self.override_.ByteSizePartial())
      self.override_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_override().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_override_:
      res+=prefix+"override <\n"
      res+=self.override_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  koverride = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "override",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheStatsRequest'
class MergedNamespaceStats(ProtocolBuffer.ProtocolMessage):
  has_hits_ = 0
  hits_ = 0
  has_misses_ = 0
  misses_ = 0
  has_byte_hits_ = 0
  byte_hits_ = 0
  has_items_ = 0
  items_ = 0
  has_bytes_ = 0
  bytes_ = 0
  has_oldest_item_age_ = 0
  oldest_item_age_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def hits(self): return self.hits_

  def set_hits(self, x):
    self.has_hits_ = 1
    self.hits_ = x

  def clear_hits(self):
    if self.has_hits_:
      self.has_hits_ = 0
      self.hits_ = 0

  def has_hits(self): return self.has_hits_

  def misses(self): return self.misses_

  def set_misses(self, x):
    self.has_misses_ = 1
    self.misses_ = x

  def clear_misses(self):
    if self.has_misses_:
      self.has_misses_ = 0
      self.misses_ = 0

  def has_misses(self): return self.has_misses_

  def byte_hits(self): return self.byte_hits_

  def set_byte_hits(self, x):
    self.has_byte_hits_ = 1
    self.byte_hits_ = x

  def clear_byte_hits(self):
    if self.has_byte_hits_:
      self.has_byte_hits_ = 0
      self.byte_hits_ = 0

  def has_byte_hits(self): return self.has_byte_hits_

  def items(self): return self.items_

  def set_items(self, x):
    self.has_items_ = 1
    self.items_ = x

  def clear_items(self):
    if self.has_items_:
      self.has_items_ = 0
      self.items_ = 0

  def has_items(self): return self.has_items_

  def bytes(self): return self.bytes_

  def set_bytes(self, x):
    self.has_bytes_ = 1
    self.bytes_ = x

  def clear_bytes(self):
    if self.has_bytes_:
      self.has_bytes_ = 0
      self.bytes_ = 0

  def has_bytes(self): return self.has_bytes_

  def oldest_item_age(self): return self.oldest_item_age_

  def set_oldest_item_age(self, x):
    self.has_oldest_item_age_ = 1
    self.oldest_item_age_ = x

  def clear_oldest_item_age(self):
    if self.has_oldest_item_age_:
      self.has_oldest_item_age_ = 0
      self.oldest_item_age_ = 0

  def has_oldest_item_age(self): return self.has_oldest_item_age_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_hits()): self.set_hits(x.hits())
    if (x.has_misses()): self.set_misses(x.misses())
    if (x.has_byte_hits()): self.set_byte_hits(x.byte_hits())
    if (x.has_items()): self.set_items(x.items())
    if (x.has_bytes()): self.set_bytes(x.bytes())
    if (x.has_oldest_item_age()): self.set_oldest_item_age(x.oldest_item_age())

  def Equals(self, x):
    if x is self: return 1
    if self.has_hits_ != x.has_hits_: return 0
    if self.has_hits_ and self.hits_ != x.hits_: return 0
    if self.has_misses_ != x.has_misses_: return 0
    if self.has_misses_ and self.misses_ != x.misses_: return 0
    if self.has_byte_hits_ != x.has_byte_hits_: return 0
    if self.has_byte_hits_ and self.byte_hits_ != x.byte_hits_: return 0
    if self.has_items_ != x.has_items_: return 0
    if self.has_items_ and self.items_ != x.items_: return 0
    if self.has_bytes_ != x.has_bytes_: return 0
    if self.has_bytes_ and self.bytes_ != x.bytes_: return 0
    if self.has_oldest_item_age_ != x.has_oldest_item_age_: return 0
    if self.has_oldest_item_age_ and self.oldest_item_age_ != x.oldest_item_age_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_hits_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: hits not set.')
    if (not self.has_misses_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: misses not set.')
    if (not self.has_byte_hits_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: byte_hits not set.')
    if (not self.has_items_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: items not set.')
    if (not self.has_bytes_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: bytes not set.')
    if (not self.has_oldest_item_age_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: oldest_item_age not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.hits_)
    n += self.lengthVarInt64(self.misses_)
    n += self.lengthVarInt64(self.byte_hits_)
    n += self.lengthVarInt64(self.items_)
    n += self.lengthVarInt64(self.bytes_)
    return n + 10

  def ByteSizePartial(self):
    n = 0
    if (self.has_hits_):
      n += 1
      n += self.lengthVarInt64(self.hits_)
    if (self.has_misses_):
      n += 1
      n += self.lengthVarInt64(self.misses_)
    if (self.has_byte_hits_):
      n += 1
      n += self.lengthVarInt64(self.byte_hits_)
    if (self.has_items_):
      n += 1
      n += self.lengthVarInt64(self.items_)
    if (self.has_bytes_):
      n += 1
      n += self.lengthVarInt64(self.bytes_)
    if (self.has_oldest_item_age_):
      n += 5
    return n

  def Clear(self):
    self.clear_hits()
    self.clear_misses()
    self.clear_byte_hits()
    self.clear_items()
    self.clear_bytes()
    self.clear_oldest_item_age()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarUint64(self.hits_)
    out.putVarInt32(16)
    out.putVarUint64(self.misses_)
    out.putVarInt32(24)
    out.putVarUint64(self.byte_hits_)
    out.putVarInt32(32)
    out.putVarUint64(self.items_)
    out.putVarInt32(40)
    out.putVarUint64(self.bytes_)
    out.putVarInt32(53)
    out.put32(self.oldest_item_age_)

  def OutputPartial(self, out):
    if (self.has_hits_):
      out.putVarInt32(8)
      out.putVarUint64(self.hits_)
    if (self.has_misses_):
      out.putVarInt32(16)
      out.putVarUint64(self.misses_)
    if (self.has_byte_hits_):
      out.putVarInt32(24)
      out.putVarUint64(self.byte_hits_)
    if (self.has_items_):
      out.putVarInt32(32)
      out.putVarUint64(self.items_)
    if (self.has_bytes_):
      out.putVarInt32(40)
      out.putVarUint64(self.bytes_)
    if (self.has_oldest_item_age_):
      out.putVarInt32(53)
      out.put32(self.oldest_item_age_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_hits(d.getVarUint64())
        continue
      if tt == 16:
        self.set_misses(d.getVarUint64())
        continue
      if tt == 24:
        self.set_byte_hits(d.getVarUint64())
        continue
      if tt == 32:
        self.set_items(d.getVarUint64())
        continue
      if tt == 40:
        self.set_bytes(d.getVarUint64())
        continue
      if tt == 53:
        self.set_oldest_item_age(d.get32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_hits_: res+=prefix+("hits: %s\n" % self.DebugFormatInt64(self.hits_))
    if self.has_misses_: res+=prefix+("misses: %s\n" % self.DebugFormatInt64(self.misses_))
    if self.has_byte_hits_: res+=prefix+("byte_hits: %s\n" % self.DebugFormatInt64(self.byte_hits_))
    if self.has_items_: res+=prefix+("items: %s\n" % self.DebugFormatInt64(self.items_))
    if self.has_bytes_: res+=prefix+("bytes: %s\n" % self.DebugFormatInt64(self.bytes_))
    if self.has_oldest_item_age_: res+=prefix+("oldest_item_age: %s\n" % self.DebugFormatFixed32(self.oldest_item_age_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  khits = 1
  kmisses = 2
  kbyte_hits = 3
  kitems = 4
  kbytes = 5
  koldest_item_age = 6

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "hits",
    2: "misses",
    3: "byte_hits",
    4: "items",
    5: "bytes",
    6: "oldest_item_age",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.FLOAT,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MergedNamespaceStats'
class MemcacheStatsResponse(ProtocolBuffer.ProtocolMessage):
  has_stats_ = 0
  stats_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def stats(self):
    if self.stats_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.stats_ is None: self.stats_ = MergedNamespaceStats()
      finally:
        self.lazy_init_lock_.release()
    return self.stats_

  def mutable_stats(self): self.has_stats_ = 1; return self.stats()

  def clear_stats(self):

    if self.has_stats_:
      self.has_stats_ = 0;
      if self.stats_ is not None: self.stats_.Clear()

  def has_stats(self): return self.has_stats_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_stats()): self.mutable_stats().MergeFrom(x.stats())

  def Equals(self, x):
    if x is self: return 1
    if self.has_stats_ != x.has_stats_: return 0
    if self.has_stats_ and self.stats_ != x.stats_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_stats_ and not self.stats_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_stats_): n += 1 + self.lengthString(self.stats_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_stats_): n += 1 + self.lengthString(self.stats_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_stats()

  def OutputUnchecked(self, out):
    if (self.has_stats_):
      out.putVarInt32(10)
      out.putVarInt32(self.stats_.ByteSize())
      self.stats_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_stats_):
      out.putVarInt32(10)
      out.putVarInt32(self.stats_.ByteSizePartial())
      self.stats_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_stats().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_stats_:
      res+=prefix+"stats <\n"
      res+=self.stats_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kstats = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "stats",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheStatsResponse'
class MemcacheGrabTailRequest(ProtocolBuffer.ProtocolMessage):
  has_item_count_ = 0
  item_count_ = 0
  has_name_space_ = 0
  name_space_ = ""
  has_override_ = 0
  override_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def item_count(self): return self.item_count_

  def set_item_count(self, x):
    self.has_item_count_ = 1
    self.item_count_ = x

  def clear_item_count(self):
    if self.has_item_count_:
      self.has_item_count_ = 0
      self.item_count_ = 0

  def has_item_count(self): return self.has_item_count_

  def name_space(self): return self.name_space_

  def set_name_space(self, x):
    self.has_name_space_ = 1
    self.name_space_ = x

  def clear_name_space(self):
    if self.has_name_space_:
      self.has_name_space_ = 0
      self.name_space_ = ""

  def has_name_space(self): return self.has_name_space_

  def override(self):
    if self.override_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.override_ is None: self.override_ = AppOverride()
      finally:
        self.lazy_init_lock_.release()
    return self.override_

  def mutable_override(self): self.has_override_ = 1; return self.override()

  def clear_override(self):

    if self.has_override_:
      self.has_override_ = 0;
      if self.override_ is not None: self.override_.Clear()

  def has_override(self): return self.has_override_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_item_count()): self.set_item_count(x.item_count())
    if (x.has_name_space()): self.set_name_space(x.name_space())
    if (x.has_override()): self.mutable_override().MergeFrom(x.override())

  def Equals(self, x):
    if x is self: return 1
    if self.has_item_count_ != x.has_item_count_: return 0
    if self.has_item_count_ and self.item_count_ != x.item_count_: return 0
    if self.has_name_space_ != x.has_name_space_: return 0
    if self.has_name_space_ and self.name_space_ != x.name_space_: return 0
    if self.has_override_ != x.has_override_: return 0
    if self.has_override_ and self.override_ != x.override_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_item_count_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: item_count not set.')
    if (self.has_override_ and not self.override_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.item_count_)
    if (self.has_name_space_): n += 1 + self.lengthString(len(self.name_space_))
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_item_count_):
      n += 1
      n += self.lengthVarInt64(self.item_count_)
    if (self.has_name_space_): n += 1 + self.lengthString(len(self.name_space_))
    if (self.has_override_): n += 1 + self.lengthString(self.override_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_item_count()
    self.clear_name_space()
    self.clear_override()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt32(self.item_count_)
    if (self.has_name_space_):
      out.putVarInt32(18)
      out.putPrefixedString(self.name_space_)
    if (self.has_override_):
      out.putVarInt32(26)
      out.putVarInt32(self.override_.ByteSize())
      self.override_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_item_count_):
      out.putVarInt32(8)
      out.putVarInt32(self.item_count_)
    if (self.has_name_space_):
      out.putVarInt32(18)
      out.putPrefixedString(self.name_space_)
    if (self.has_override_):
      out.putVarInt32(26)
      out.putVarInt32(self.override_.ByteSizePartial())
      self.override_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_item_count(d.getVarInt32())
        continue
      if tt == 18:
        self.set_name_space(d.getPrefixedString())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_override().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_item_count_: res+=prefix+("item_count: %s\n" % self.DebugFormatInt32(self.item_count_))
    if self.has_name_space_: res+=prefix+("name_space: %s\n" % self.DebugFormatString(self.name_space_))
    if self.has_override_:
      res+=prefix+"override <\n"
      res+=self.override_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kitem_count = 1
  kname_space = 2
  koverride = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "item_count",
    2: "name_space",
    3: "override",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheGrabTailRequest'
class MemcacheGrabTailResponse_Item(ProtocolBuffer.ProtocolMessage):
  has_value_ = 0
  value_ = ""
  has_flags_ = 0
  flags_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def value(self): return self.value_

  def set_value(self, x):
    self.has_value_ = 1
    self.value_ = x

  def clear_value(self):
    if self.has_value_:
      self.has_value_ = 0
      self.value_ = ""

  def has_value(self): return self.has_value_

  def flags(self): return self.flags_

  def set_flags(self, x):
    self.has_flags_ = 1
    self.flags_ = x

  def clear_flags(self):
    if self.has_flags_:
      self.has_flags_ = 0
      self.flags_ = 0

  def has_flags(self): return self.has_flags_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_value()): self.set_value(x.value())
    if (x.has_flags()): self.set_flags(x.flags())

  def Equals(self, x):
    if x is self: return 1
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    if self.has_flags_ != x.has_flags_: return 0
    if self.has_flags_ and self.flags_ != x.flags_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_value_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: value not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.value_))
    if (self.has_flags_): n += 5
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_value_):
      n += 1
      n += self.lengthString(len(self.value_))
    if (self.has_flags_): n += 5
    return n

  def Clear(self):
    self.clear_value()
    self.clear_flags()

  def OutputUnchecked(self, out):
    out.putVarInt32(18)
    out.putPrefixedString(self.value_)
    if (self.has_flags_):
      out.putVarInt32(29)
      out.put32(self.flags_)

  def OutputPartial(self, out):
    if (self.has_value_):
      out.putVarInt32(18)
      out.putPrefixedString(self.value_)
    if (self.has_flags_):
      out.putVarInt32(29)
      out.put32(self.flags_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 12: break
      if tt == 18:
        self.set_value(d.getPrefixedString())
        continue
      if tt == 29:
        self.set_flags(d.get32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_value_: res+=prefix+("value: %s\n" % self.DebugFormatString(self.value_))
    if self.has_flags_: res+=prefix+("flags: %s\n" % self.DebugFormatFixed32(self.flags_))
    return res

class MemcacheGrabTailResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.item_ = []
    if contents is not None: self.MergeFromString(contents)

  def item_size(self): return len(self.item_)
  def item_list(self): return self.item_

  def item(self, i):
    return self.item_[i]

  def mutable_item(self, i):
    return self.item_[i]

  def add_item(self):
    x = MemcacheGrabTailResponse_Item()
    self.item_.append(x)
    return x

  def clear_item(self):
    self.item_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.item_size()): self.add_item().CopyFrom(x.item(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.item_) != len(x.item_): return 0
    for e1, e2 in zip(self.item_, x.item_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.item_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 2 * len(self.item_)
    for i in xrange(len(self.item_)): n += self.item_[i].ByteSize()
    return n

  def ByteSizePartial(self):
    n = 0
    n += 2 * len(self.item_)
    for i in xrange(len(self.item_)): n += self.item_[i].ByteSizePartial()
    return n

  def Clear(self):
    self.clear_item()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.item_)):
      out.putVarInt32(11)
      self.item_[i].OutputUnchecked(out)
      out.putVarInt32(12)

  def OutputPartial(self, out):
    for i in xrange(len(self.item_)):
      out.putVarInt32(11)
      self.item_[i].OutputPartial(out)
      out.putVarInt32(12)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 11:
        self.add_item().TryMerge(d)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.item_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Item%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kItemGroup = 1
  kItemvalue = 2
  kItemflags = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "Item",
    2: "value",
    3: "flags",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STARTGROUP,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.FLOAT,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MemcacheGrabTailResponse'
if _extension_runtime:
  pass

__all__ = ['MemcacheServiceError','AppOverride','MemcacheGetRequest','MemcacheGetResponse','MemcacheGetResponse_Item','MemcacheSetRequest','MemcacheSetRequest_Item','MemcacheSetResponse','MemcacheDeleteRequest','MemcacheDeleteRequest_Item','MemcacheDeleteResponse','MemcacheIncrementRequest','MemcacheIncrementResponse','MemcacheBatchIncrementRequest','MemcacheBatchIncrementResponse','MemcacheFlushRequest','MemcacheFlushResponse','MemcacheStatsRequest','MergedNamespaceStats','MemcacheStatsResponse','MemcacheGrabTailRequest','MemcacheGrabTailResponse','MemcacheGrabTailResponse_Item']
