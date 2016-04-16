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

class CapabilityConfigList(ProtocolBuffer.ProtocolMessage):
  has_default_config_ = 0
  default_config_ = None

  def __init__(self, contents=None):
    self.config_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def config_size(self): return len(self.config_)
  def config_list(self): return self.config_

  def config(self, i):
    return self.config_[i]

  def mutable_config(self, i):
    return self.config_[i]

  def add_config(self):
    x = CapabilityConfig()
    self.config_.append(x)
    return x

  def clear_config(self):
    self.config_ = []
  def default_config(self):
    if self.default_config_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.default_config_ is None: self.default_config_ = CapabilityConfig()
      finally:
        self.lazy_init_lock_.release()
    return self.default_config_

  def mutable_default_config(self): self.has_default_config_ = 1; return self.default_config()

  def clear_default_config(self):

    if self.has_default_config_:
      self.has_default_config_ = 0;
      if self.default_config_ is not None: self.default_config_.Clear()

  def has_default_config(self): return self.has_default_config_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.config_size()): self.add_config().CopyFrom(x.config(i))
    if (x.has_default_config()): self.mutable_default_config().MergeFrom(x.default_config())

  def Equals(self, x):
    if x is self: return 1
    if len(self.config_) != len(x.config_): return 0
    for e1, e2 in zip(self.config_, x.config_):
      if e1 != e2: return 0
    if self.has_default_config_ != x.has_default_config_: return 0
    if self.has_default_config_ and self.default_config_ != x.default_config_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.config_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_default_config_ and not self.default_config_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.config_)
    for i in xrange(len(self.config_)): n += self.lengthString(self.config_[i].ByteSize())
    if (self.has_default_config_): n += 1 + self.lengthString(self.default_config_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.config_)
    for i in xrange(len(self.config_)): n += self.lengthString(self.config_[i].ByteSizePartial())
    if (self.has_default_config_): n += 1 + self.lengthString(self.default_config_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_config()
    self.clear_default_config()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.config_)):
      out.putVarInt32(10)
      out.putVarInt32(self.config_[i].ByteSize())
      self.config_[i].OutputUnchecked(out)
    if (self.has_default_config_):
      out.putVarInt32(18)
      out.putVarInt32(self.default_config_.ByteSize())
      self.default_config_.OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.config_)):
      out.putVarInt32(10)
      out.putVarInt32(self.config_[i].ByteSizePartial())
      self.config_[i].OutputPartial(out)
    if (self.has_default_config_):
      out.putVarInt32(18)
      out.putVarInt32(self.default_config_.ByteSizePartial())
      self.default_config_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_config().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_default_config().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.config_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("config%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_default_config_:
      res+=prefix+"default_config <\n"
      res+=self.default_config_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kconfig = 1
  kdefault_config = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "config",
    2: "default_config",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CapabilityConfigList'
class CapabilityConfig(ProtocolBuffer.ProtocolMessage):


  DEFAULT      =    0
  ENABLED      =    1
  SCHEDULED    =    2
  DISABLED     =    3
  UNKNOWN      =    4

  _Status_NAMES = {
    0: "DEFAULT",
    1: "ENABLED",
    2: "SCHEDULED",
    3: "DISABLED",
    4: "UNKNOWN",
  }

  def Status_Name(cls, x): return cls._Status_NAMES.get(x, "")
  Status_Name = classmethod(Status_Name)

  has_package_ = 0
  package_ = ""
  has_capability_ = 0
  capability_ = ""
  has_status_ = 0
  status_ = 4
  has_scheduled_time_ = 0
  scheduled_time_ = ""
  has_internal_message_ = 0
  internal_message_ = ""
  has_admin_message_ = 0
  admin_message_ = ""
  has_error_message_ = 0
  error_message_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def package(self): return self.package_

  def set_package(self, x):
    self.has_package_ = 1
    self.package_ = x

  def clear_package(self):
    if self.has_package_:
      self.has_package_ = 0
      self.package_ = ""

  def has_package(self): return self.has_package_

  def capability(self): return self.capability_

  def set_capability(self, x):
    self.has_capability_ = 1
    self.capability_ = x

  def clear_capability(self):
    if self.has_capability_:
      self.has_capability_ = 0
      self.capability_ = ""

  def has_capability(self): return self.has_capability_

  def status(self): return self.status_

  def set_status(self, x):
    self.has_status_ = 1
    self.status_ = x

  def clear_status(self):
    if self.has_status_:
      self.has_status_ = 0
      self.status_ = 4

  def has_status(self): return self.has_status_

  def scheduled_time(self): return self.scheduled_time_

  def set_scheduled_time(self, x):
    self.has_scheduled_time_ = 1
    self.scheduled_time_ = x

  def clear_scheduled_time(self):
    if self.has_scheduled_time_:
      self.has_scheduled_time_ = 0
      self.scheduled_time_ = ""

  def has_scheduled_time(self): return self.has_scheduled_time_

  def internal_message(self): return self.internal_message_

  def set_internal_message(self, x):
    self.has_internal_message_ = 1
    self.internal_message_ = x

  def clear_internal_message(self):
    if self.has_internal_message_:
      self.has_internal_message_ = 0
      self.internal_message_ = ""

  def has_internal_message(self): return self.has_internal_message_

  def admin_message(self): return self.admin_message_

  def set_admin_message(self, x):
    self.has_admin_message_ = 1
    self.admin_message_ = x

  def clear_admin_message(self):
    if self.has_admin_message_:
      self.has_admin_message_ = 0
      self.admin_message_ = ""

  def has_admin_message(self): return self.has_admin_message_

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
    if (x.has_package()): self.set_package(x.package())
    if (x.has_capability()): self.set_capability(x.capability())
    if (x.has_status()): self.set_status(x.status())
    if (x.has_scheduled_time()): self.set_scheduled_time(x.scheduled_time())
    if (x.has_internal_message()): self.set_internal_message(x.internal_message())
    if (x.has_admin_message()): self.set_admin_message(x.admin_message())
    if (x.has_error_message()): self.set_error_message(x.error_message())

  def Equals(self, x):
    if x is self: return 1
    if self.has_package_ != x.has_package_: return 0
    if self.has_package_ and self.package_ != x.package_: return 0
    if self.has_capability_ != x.has_capability_: return 0
    if self.has_capability_ and self.capability_ != x.capability_: return 0
    if self.has_status_ != x.has_status_: return 0
    if self.has_status_ and self.status_ != x.status_: return 0
    if self.has_scheduled_time_ != x.has_scheduled_time_: return 0
    if self.has_scheduled_time_ and self.scheduled_time_ != x.scheduled_time_: return 0
    if self.has_internal_message_ != x.has_internal_message_: return 0
    if self.has_internal_message_ and self.internal_message_ != x.internal_message_: return 0
    if self.has_admin_message_ != x.has_admin_message_: return 0
    if self.has_admin_message_ and self.admin_message_ != x.admin_message_: return 0
    if self.has_error_message_ != x.has_error_message_: return 0
    if self.has_error_message_ and self.error_message_ != x.error_message_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_package_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: package not set.')
    if (not self.has_capability_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: capability not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.package_))
    n += self.lengthString(len(self.capability_))
    if (self.has_status_): n += 1 + self.lengthVarInt64(self.status_)
    if (self.has_scheduled_time_): n += 1 + self.lengthString(len(self.scheduled_time_))
    if (self.has_internal_message_): n += 1 + self.lengthString(len(self.internal_message_))
    if (self.has_admin_message_): n += 1 + self.lengthString(len(self.admin_message_))
    if (self.has_error_message_): n += 1 + self.lengthString(len(self.error_message_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_package_):
      n += 1
      n += self.lengthString(len(self.package_))
    if (self.has_capability_):
      n += 1
      n += self.lengthString(len(self.capability_))
    if (self.has_status_): n += 1 + self.lengthVarInt64(self.status_)
    if (self.has_scheduled_time_): n += 1 + self.lengthString(len(self.scheduled_time_))
    if (self.has_internal_message_): n += 1 + self.lengthString(len(self.internal_message_))
    if (self.has_admin_message_): n += 1 + self.lengthString(len(self.admin_message_))
    if (self.has_error_message_): n += 1 + self.lengthString(len(self.error_message_))
    return n

  def Clear(self):
    self.clear_package()
    self.clear_capability()
    self.clear_status()
    self.clear_scheduled_time()
    self.clear_internal_message()
    self.clear_admin_message()
    self.clear_error_message()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.package_)
    out.putVarInt32(18)
    out.putPrefixedString(self.capability_)
    if (self.has_status_):
      out.putVarInt32(24)
      out.putVarInt32(self.status_)
    if (self.has_internal_message_):
      out.putVarInt32(34)
      out.putPrefixedString(self.internal_message_)
    if (self.has_admin_message_):
      out.putVarInt32(42)
      out.putPrefixedString(self.admin_message_)
    if (self.has_error_message_):
      out.putVarInt32(50)
      out.putPrefixedString(self.error_message_)
    if (self.has_scheduled_time_):
      out.putVarInt32(58)
      out.putPrefixedString(self.scheduled_time_)

  def OutputPartial(self, out):
    if (self.has_package_):
      out.putVarInt32(10)
      out.putPrefixedString(self.package_)
    if (self.has_capability_):
      out.putVarInt32(18)
      out.putPrefixedString(self.capability_)
    if (self.has_status_):
      out.putVarInt32(24)
      out.putVarInt32(self.status_)
    if (self.has_internal_message_):
      out.putVarInt32(34)
      out.putPrefixedString(self.internal_message_)
    if (self.has_admin_message_):
      out.putVarInt32(42)
      out.putPrefixedString(self.admin_message_)
    if (self.has_error_message_):
      out.putVarInt32(50)
      out.putPrefixedString(self.error_message_)
    if (self.has_scheduled_time_):
      out.putVarInt32(58)
      out.putPrefixedString(self.scheduled_time_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_package(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_capability(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_status(d.getVarInt32())
        continue
      if tt == 34:
        self.set_internal_message(d.getPrefixedString())
        continue
      if tt == 42:
        self.set_admin_message(d.getPrefixedString())
        continue
      if tt == 50:
        self.set_error_message(d.getPrefixedString())
        continue
      if tt == 58:
        self.set_scheduled_time(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_package_: res+=prefix+("package: %s\n" % self.DebugFormatString(self.package_))
    if self.has_capability_: res+=prefix+("capability: %s\n" % self.DebugFormatString(self.capability_))
    if self.has_status_: res+=prefix+("status: %s\n" % self.DebugFormatInt32(self.status_))
    if self.has_scheduled_time_: res+=prefix+("scheduled_time: %s\n" % self.DebugFormatString(self.scheduled_time_))
    if self.has_internal_message_: res+=prefix+("internal_message: %s\n" % self.DebugFormatString(self.internal_message_))
    if self.has_admin_message_: res+=prefix+("admin_message: %s\n" % self.DebugFormatString(self.admin_message_))
    if self.has_error_message_: res+=prefix+("error_message: %s\n" % self.DebugFormatString(self.error_message_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kpackage = 1
  kcapability = 2
  kstatus = 3
  kscheduled_time = 7
  kinternal_message = 4
  kadmin_message = 5
  kerror_message = 6

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "package",
    2: "capability",
    3: "status",
    4: "internal_message",
    5: "admin_message",
    6: "error_message",
    7: "scheduled_time",
  }, 7)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.STRING,
    7: ProtocolBuffer.Encoder.STRING,
  }, 7, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CapabilityConfig'
if _extension_runtime:
  pass

__all__ = ['CapabilityConfigList','CapabilityConfig']
