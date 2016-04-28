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

from google.appengine.base.capabilities_pb import *
import google.appengine.base.capabilities_pb
class IsEnabledRequest(ProtocolBuffer.ProtocolMessage):
  has_package_ = 0
  package_ = ""

  def __init__(self, contents=None):
    self.capability_ = []
    self.call_ = []
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

  def capability_size(self): return len(self.capability_)
  def capability_list(self): return self.capability_

  def capability(self, i):
    return self.capability_[i]

  def set_capability(self, i, x):
    self.capability_[i] = x

  def add_capability(self, x):
    self.capability_.append(x)

  def clear_capability(self):
    self.capability_ = []

  def call_size(self): return len(self.call_)
  def call_list(self): return self.call_

  def call(self, i):
    return self.call_[i]

  def set_call(self, i, x):
    self.call_[i] = x

  def add_call(self, x):
    self.call_.append(x)

  def clear_call(self):
    self.call_ = []


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_package()): self.set_package(x.package())
    for i in xrange(x.capability_size()): self.add_capability(x.capability(i))
    for i in xrange(x.call_size()): self.add_call(x.call(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_package_ != x.has_package_: return 0
    if self.has_package_ and self.package_ != x.package_: return 0
    if len(self.capability_) != len(x.capability_): return 0
    for e1, e2 in zip(self.capability_, x.capability_):
      if e1 != e2: return 0
    if len(self.call_) != len(x.call_): return 0
    for e1, e2 in zip(self.call_, x.call_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_package_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: package not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.package_))
    n += 1 * len(self.capability_)
    for i in xrange(len(self.capability_)): n += self.lengthString(len(self.capability_[i]))
    n += 1 * len(self.call_)
    for i in xrange(len(self.call_)): n += self.lengthString(len(self.call_[i]))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_package_):
      n += 1
      n += self.lengthString(len(self.package_))
    n += 1 * len(self.capability_)
    for i in xrange(len(self.capability_)): n += self.lengthString(len(self.capability_[i]))
    n += 1 * len(self.call_)
    for i in xrange(len(self.call_)): n += self.lengthString(len(self.call_[i]))
    return n

  def Clear(self):
    self.clear_package()
    self.clear_capability()
    self.clear_call()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.package_)
    for i in xrange(len(self.capability_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.capability_[i])
    for i in xrange(len(self.call_)):
      out.putVarInt32(26)
      out.putPrefixedString(self.call_[i])

  def OutputPartial(self, out):
    if (self.has_package_):
      out.putVarInt32(10)
      out.putPrefixedString(self.package_)
    for i in xrange(len(self.capability_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.capability_[i])
    for i in xrange(len(self.call_)):
      out.putVarInt32(26)
      out.putPrefixedString(self.call_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_package(d.getPrefixedString())
        continue
      if tt == 18:
        self.add_capability(d.getPrefixedString())
        continue
      if tt == 26:
        self.add_call(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_package_: res+=prefix+("package: %s\n" % self.DebugFormatString(self.package_))
    cnt=0
    for e in self.capability_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("capability%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    cnt=0
    for e in self.call_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("call%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kpackage = 1
  kcapability = 2
  kcall = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "package",
    2: "capability",
    3: "call",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.IsEnabledRequest'
class IsEnabledResponse(ProtocolBuffer.ProtocolMessage):


  DEFAULT      =    0
  ENABLED      =    1
  SCHEDULED_FUTURE =    2
  SCHEDULED_NOW =    3
  DISABLED     =    4
  UNKNOWN      =    5

  _SummaryStatus_NAMES = {
    0: "DEFAULT",
    1: "ENABLED",
    2: "SCHEDULED_FUTURE",
    3: "SCHEDULED_NOW",
    4: "DISABLED",
    5: "UNKNOWN",
  }

  def SummaryStatus_Name(cls, x): return cls._SummaryStatus_NAMES.get(x, "")
  SummaryStatus_Name = classmethod(SummaryStatus_Name)

  has_summary_status_ = 0
  summary_status_ = 0
  has_time_until_scheduled_ = 0
  time_until_scheduled_ = 0

  def __init__(self, contents=None):
    self.config_ = []
    if contents is not None: self.MergeFromString(contents)

  def summary_status(self): return self.summary_status_

  def set_summary_status(self, x):
    self.has_summary_status_ = 1
    self.summary_status_ = x

  def clear_summary_status(self):
    if self.has_summary_status_:
      self.has_summary_status_ = 0
      self.summary_status_ = 0

  def has_summary_status(self): return self.has_summary_status_

  def time_until_scheduled(self): return self.time_until_scheduled_

  def set_time_until_scheduled(self, x):
    self.has_time_until_scheduled_ = 1
    self.time_until_scheduled_ = x

  def clear_time_until_scheduled(self):
    if self.has_time_until_scheduled_:
      self.has_time_until_scheduled_ = 0
      self.time_until_scheduled_ = 0

  def has_time_until_scheduled(self): return self.has_time_until_scheduled_

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

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_summary_status()): self.set_summary_status(x.summary_status())
    if (x.has_time_until_scheduled()): self.set_time_until_scheduled(x.time_until_scheduled())
    for i in xrange(x.config_size()): self.add_config().CopyFrom(x.config(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_summary_status_ != x.has_summary_status_: return 0
    if self.has_summary_status_ and self.summary_status_ != x.summary_status_: return 0
    if self.has_time_until_scheduled_ != x.has_time_until_scheduled_: return 0
    if self.has_time_until_scheduled_ and self.time_until_scheduled_ != x.time_until_scheduled_: return 0
    if len(self.config_) != len(x.config_): return 0
    for e1, e2 in zip(self.config_, x.config_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.config_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_summary_status_): n += 1 + self.lengthVarInt64(self.summary_status_)
    if (self.has_time_until_scheduled_): n += 1 + self.lengthVarInt64(self.time_until_scheduled_)
    n += 1 * len(self.config_)
    for i in xrange(len(self.config_)): n += self.lengthString(self.config_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_summary_status_): n += 1 + self.lengthVarInt64(self.summary_status_)
    if (self.has_time_until_scheduled_): n += 1 + self.lengthVarInt64(self.time_until_scheduled_)
    n += 1 * len(self.config_)
    for i in xrange(len(self.config_)): n += self.lengthString(self.config_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_summary_status()
    self.clear_time_until_scheduled()
    self.clear_config()

  def OutputUnchecked(self, out):
    if (self.has_summary_status_):
      out.putVarInt32(8)
      out.putVarInt32(self.summary_status_)
    if (self.has_time_until_scheduled_):
      out.putVarInt32(16)
      out.putVarInt64(self.time_until_scheduled_)
    for i in xrange(len(self.config_)):
      out.putVarInt32(26)
      out.putVarInt32(self.config_[i].ByteSize())
      self.config_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_summary_status_):
      out.putVarInt32(8)
      out.putVarInt32(self.summary_status_)
    if (self.has_time_until_scheduled_):
      out.putVarInt32(16)
      out.putVarInt64(self.time_until_scheduled_)
    for i in xrange(len(self.config_)):
      out.putVarInt32(26)
      out.putVarInt32(self.config_[i].ByteSizePartial())
      self.config_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_summary_status(d.getVarInt32())
        continue
      if tt == 16:
        self.set_time_until_scheduled(d.getVarInt64())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_config().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_summary_status_: res+=prefix+("summary_status: %s\n" % self.DebugFormatInt32(self.summary_status_))
    if self.has_time_until_scheduled_: res+=prefix+("time_until_scheduled: %s\n" % self.DebugFormatInt64(self.time_until_scheduled_))
    cnt=0
    for e in self.config_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("config%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksummary_status = 1
  ktime_until_scheduled = 2
  kconfig = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "summary_status",
    2: "time_until_scheduled",
    3: "config",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.IsEnabledResponse'
if _extension_runtime:
  pass

__all__ = ['IsEnabledRequest','IsEnabledResponse']
