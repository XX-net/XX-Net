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

class SystemServiceError(ProtocolBuffer.ProtocolMessage):


  OK           =    0
  INTERNAL_ERROR =    1
  BACKEND_REQUIRED =    2
  LIMIT_REACHED =    3

  _ErrorCode_NAMES = {
    0: "OK",
    1: "INTERNAL_ERROR",
    2: "BACKEND_REQUIRED",
    3: "LIMIT_REACHED",
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SystemServiceError'
class SystemStat(ProtocolBuffer.ProtocolMessage):
  has_current_ = 0
  current_ = 0.0
  has_average1m_ = 0
  average1m_ = 0.0
  has_average10m_ = 0
  average10m_ = 0.0
  has_total_ = 0
  total_ = 0.0
  has_rate1m_ = 0
  rate1m_ = 0.0
  has_rate10m_ = 0
  rate10m_ = 0.0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def current(self): return self.current_

  def set_current(self, x):
    self.has_current_ = 1
    self.current_ = x

  def clear_current(self):
    if self.has_current_:
      self.has_current_ = 0
      self.current_ = 0.0

  def has_current(self): return self.has_current_

  def average1m(self): return self.average1m_

  def set_average1m(self, x):
    self.has_average1m_ = 1
    self.average1m_ = x

  def clear_average1m(self):
    if self.has_average1m_:
      self.has_average1m_ = 0
      self.average1m_ = 0.0

  def has_average1m(self): return self.has_average1m_

  def average10m(self): return self.average10m_

  def set_average10m(self, x):
    self.has_average10m_ = 1
    self.average10m_ = x

  def clear_average10m(self):
    if self.has_average10m_:
      self.has_average10m_ = 0
      self.average10m_ = 0.0

  def has_average10m(self): return self.has_average10m_

  def total(self): return self.total_

  def set_total(self, x):
    self.has_total_ = 1
    self.total_ = x

  def clear_total(self):
    if self.has_total_:
      self.has_total_ = 0
      self.total_ = 0.0

  def has_total(self): return self.has_total_

  def rate1m(self): return self.rate1m_

  def set_rate1m(self, x):
    self.has_rate1m_ = 1
    self.rate1m_ = x

  def clear_rate1m(self):
    if self.has_rate1m_:
      self.has_rate1m_ = 0
      self.rate1m_ = 0.0

  def has_rate1m(self): return self.has_rate1m_

  def rate10m(self): return self.rate10m_

  def set_rate10m(self, x):
    self.has_rate10m_ = 1
    self.rate10m_ = x

  def clear_rate10m(self):
    if self.has_rate10m_:
      self.has_rate10m_ = 0
      self.rate10m_ = 0.0

  def has_rate10m(self): return self.has_rate10m_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_current()): self.set_current(x.current())
    if (x.has_average1m()): self.set_average1m(x.average1m())
    if (x.has_average10m()): self.set_average10m(x.average10m())
    if (x.has_total()): self.set_total(x.total())
    if (x.has_rate1m()): self.set_rate1m(x.rate1m())
    if (x.has_rate10m()): self.set_rate10m(x.rate10m())

  def Equals(self, x):
    if x is self: return 1
    if self.has_current_ != x.has_current_: return 0
    if self.has_current_ and self.current_ != x.current_: return 0
    if self.has_average1m_ != x.has_average1m_: return 0
    if self.has_average1m_ and self.average1m_ != x.average1m_: return 0
    if self.has_average10m_ != x.has_average10m_: return 0
    if self.has_average10m_ and self.average10m_ != x.average10m_: return 0
    if self.has_total_ != x.has_total_: return 0
    if self.has_total_ and self.total_ != x.total_: return 0
    if self.has_rate1m_ != x.has_rate1m_: return 0
    if self.has_rate1m_ and self.rate1m_ != x.rate1m_: return 0
    if self.has_rate10m_ != x.has_rate10m_: return 0
    if self.has_rate10m_ and self.rate10m_ != x.rate10m_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_current_): n += 9
    if (self.has_average1m_): n += 9
    if (self.has_average10m_): n += 9
    if (self.has_total_): n += 9
    if (self.has_rate1m_): n += 9
    if (self.has_rate10m_): n += 9
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_current_): n += 9
    if (self.has_average1m_): n += 9
    if (self.has_average10m_): n += 9
    if (self.has_total_): n += 9
    if (self.has_rate1m_): n += 9
    if (self.has_rate10m_): n += 9
    return n

  def Clear(self):
    self.clear_current()
    self.clear_average1m()
    self.clear_average10m()
    self.clear_total()
    self.clear_rate1m()
    self.clear_rate10m()

  def OutputUnchecked(self, out):
    if (self.has_current_):
      out.putVarInt32(9)
      out.putDouble(self.current_)
    if (self.has_total_):
      out.putVarInt32(17)
      out.putDouble(self.total_)
    if (self.has_average1m_):
      out.putVarInt32(25)
      out.putDouble(self.average1m_)
    if (self.has_average10m_):
      out.putVarInt32(33)
      out.putDouble(self.average10m_)
    if (self.has_rate1m_):
      out.putVarInt32(41)
      out.putDouble(self.rate1m_)
    if (self.has_rate10m_):
      out.putVarInt32(49)
      out.putDouble(self.rate10m_)

  def OutputPartial(self, out):
    if (self.has_current_):
      out.putVarInt32(9)
      out.putDouble(self.current_)
    if (self.has_total_):
      out.putVarInt32(17)
      out.putDouble(self.total_)
    if (self.has_average1m_):
      out.putVarInt32(25)
      out.putDouble(self.average1m_)
    if (self.has_average10m_):
      out.putVarInt32(33)
      out.putDouble(self.average10m_)
    if (self.has_rate1m_):
      out.putVarInt32(41)
      out.putDouble(self.rate1m_)
    if (self.has_rate10m_):
      out.putVarInt32(49)
      out.putDouble(self.rate10m_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 9:
        self.set_current(d.getDouble())
        continue
      if tt == 17:
        self.set_total(d.getDouble())
        continue
      if tt == 25:
        self.set_average1m(d.getDouble())
        continue
      if tt == 33:
        self.set_average10m(d.getDouble())
        continue
      if tt == 41:
        self.set_rate1m(d.getDouble())
        continue
      if tt == 49:
        self.set_rate10m(d.getDouble())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_current_: res+=prefix+("current: %s\n" % self.DebugFormat(self.current_))
    if self.has_average1m_: res+=prefix+("average1m: %s\n" % self.DebugFormat(self.average1m_))
    if self.has_average10m_: res+=prefix+("average10m: %s\n" % self.DebugFormat(self.average10m_))
    if self.has_total_: res+=prefix+("total: %s\n" % self.DebugFormat(self.total_))
    if self.has_rate1m_: res+=prefix+("rate1m: %s\n" % self.DebugFormat(self.rate1m_))
    if self.has_rate10m_: res+=prefix+("rate10m: %s\n" % self.DebugFormat(self.rate10m_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kcurrent = 1
  kaverage1m = 3
  kaverage10m = 4
  ktotal = 2
  krate1m = 5
  krate10m = 6

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "current",
    2: "total",
    3: "average1m",
    4: "average10m",
    5: "rate1m",
    6: "rate10m",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.DOUBLE,
    2: ProtocolBuffer.Encoder.DOUBLE,
    3: ProtocolBuffer.Encoder.DOUBLE,
    4: ProtocolBuffer.Encoder.DOUBLE,
    5: ProtocolBuffer.Encoder.DOUBLE,
    6: ProtocolBuffer.Encoder.DOUBLE,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SystemStat'
class GetSystemStatsRequest(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetSystemStatsRequest'
class GetSystemStatsResponse(ProtocolBuffer.ProtocolMessage):
  has_cpu_ = 0
  cpu_ = None
  has_memory_ = 0
  memory_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def cpu(self):
    if self.cpu_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.cpu_ is None: self.cpu_ = SystemStat()
      finally:
        self.lazy_init_lock_.release()
    return self.cpu_

  def mutable_cpu(self): self.has_cpu_ = 1; return self.cpu()

  def clear_cpu(self):

    if self.has_cpu_:
      self.has_cpu_ = 0;
      if self.cpu_ is not None: self.cpu_.Clear()

  def has_cpu(self): return self.has_cpu_

  def memory(self):
    if self.memory_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.memory_ is None: self.memory_ = SystemStat()
      finally:
        self.lazy_init_lock_.release()
    return self.memory_

  def mutable_memory(self): self.has_memory_ = 1; return self.memory()

  def clear_memory(self):

    if self.has_memory_:
      self.has_memory_ = 0;
      if self.memory_ is not None: self.memory_.Clear()

  def has_memory(self): return self.has_memory_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_cpu()): self.mutable_cpu().MergeFrom(x.cpu())
    if (x.has_memory()): self.mutable_memory().MergeFrom(x.memory())

  def Equals(self, x):
    if x is self: return 1
    if self.has_cpu_ != x.has_cpu_: return 0
    if self.has_cpu_ and self.cpu_ != x.cpu_: return 0
    if self.has_memory_ != x.has_memory_: return 0
    if self.has_memory_ and self.memory_ != x.memory_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_cpu_ and not self.cpu_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_memory_ and not self.memory_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_cpu_): n += 1 + self.lengthString(self.cpu_.ByteSize())
    if (self.has_memory_): n += 1 + self.lengthString(self.memory_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_cpu_): n += 1 + self.lengthString(self.cpu_.ByteSizePartial())
    if (self.has_memory_): n += 1 + self.lengthString(self.memory_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_cpu()
    self.clear_memory()

  def OutputUnchecked(self, out):
    if (self.has_cpu_):
      out.putVarInt32(10)
      out.putVarInt32(self.cpu_.ByteSize())
      self.cpu_.OutputUnchecked(out)
    if (self.has_memory_):
      out.putVarInt32(18)
      out.putVarInt32(self.memory_.ByteSize())
      self.memory_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_cpu_):
      out.putVarInt32(10)
      out.putVarInt32(self.cpu_.ByteSizePartial())
      self.cpu_.OutputPartial(out)
    if (self.has_memory_):
      out.putVarInt32(18)
      out.putVarInt32(self.memory_.ByteSizePartial())
      self.memory_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_cpu().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_memory().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_cpu_:
      res+=prefix+"cpu <\n"
      res+=self.cpu_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_memory_:
      res+=prefix+"memory <\n"
      res+=self.memory_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kcpu = 1
  kmemory = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "cpu",
    2: "memory",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetSystemStatsResponse'
class StartBackgroundRequestRequest(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.StartBackgroundRequestRequest'
class StartBackgroundRequestResponse(ProtocolBuffer.ProtocolMessage):
  has_request_id_ = 0
  request_id_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def request_id(self): return self.request_id_

  def set_request_id(self, x):
    self.has_request_id_ = 1
    self.request_id_ = x

  def clear_request_id(self):
    if self.has_request_id_:
      self.has_request_id_ = 0
      self.request_id_ = ""

  def has_request_id(self): return self.has_request_id_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_request_id()): self.set_request_id(x.request_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_request_id_ != x.has_request_id_: return 0
    if self.has_request_id_ and self.request_id_ != x.request_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_request_id_): n += 1 + self.lengthString(len(self.request_id_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_request_id_): n += 1 + self.lengthString(len(self.request_id_))
    return n

  def Clear(self):
    self.clear_request_id()

  def OutputUnchecked(self, out):
    if (self.has_request_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.request_id_)

  def OutputPartial(self, out):
    if (self.has_request_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.request_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_request_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_request_id_: res+=prefix+("request_id: %s\n" % self.DebugFormatString(self.request_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  krequest_id = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "request_id",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.StartBackgroundRequestResponse'
if _extension_runtime:
  pass

__all__ = ['SystemServiceError','SystemStat','GetSystemStatsRequest','GetSystemStatsResponse','StartBackgroundRequestRequest','StartBackgroundRequestResponse']
