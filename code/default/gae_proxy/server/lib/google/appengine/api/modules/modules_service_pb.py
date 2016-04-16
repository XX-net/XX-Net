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

class ModulesServiceError(ProtocolBuffer.ProtocolMessage):


  OK           =    0
  INVALID_MODULE =    1
  INVALID_VERSION =    2
  INVALID_INSTANCES =    3
  TRANSIENT_ERROR =    4
  UNEXPECTED_STATE =    5

  _ErrorCode_NAMES = {
    0: "OK",
    1: "INVALID_MODULE",
    2: "INVALID_VERSION",
    3: "INVALID_INSTANCES",
    4: "TRANSIENT_ERROR",
    5: "UNEXPECTED_STATE",
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ModulesServiceError'
class GetModulesRequest(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetModulesRequest'
class GetModulesResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.module_ = []
    if contents is not None: self.MergeFromString(contents)

  def module_size(self): return len(self.module_)
  def module_list(self): return self.module_

  def module(self, i):
    return self.module_[i]

  def set_module(self, i, x):
    self.module_[i] = x

  def add_module(self, x):
    self.module_.append(x)

  def clear_module(self):
    self.module_ = []


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.module_size()): self.add_module(x.module(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.module_) != len(x.module_): return 0
    for e1, e2 in zip(self.module_, x.module_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.module_)
    for i in xrange(len(self.module_)): n += self.lengthString(len(self.module_[i]))
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.module_)
    for i in xrange(len(self.module_)): n += self.lengthString(len(self.module_[i]))
    return n

  def Clear(self):
    self.clear_module()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.module_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_[i])

  def OutputPartial(self, out):
    for i in xrange(len(self.module_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.add_module(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.module_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("module%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kmodule = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "module",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetModulesResponse'
class GetVersionsRequest(ProtocolBuffer.ProtocolMessage):
  has_module_ = 0
  module_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def module(self): return self.module_

  def set_module(self, x):
    self.has_module_ = 1
    self.module_ = x

  def clear_module(self):
    if self.has_module_:
      self.has_module_ = 0
      self.module_ = ""

  def has_module(self): return self.has_module_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_module()): self.set_module(x.module())

  def Equals(self, x):
    if x is self: return 1
    if self.has_module_ != x.has_module_: return 0
    if self.has_module_ and self.module_ != x.module_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_module_): n += 1 + self.lengthString(len(self.module_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_module_): n += 1 + self.lengthString(len(self.module_))
    return n

  def Clear(self):
    self.clear_module()

  def OutputUnchecked(self, out):
    if (self.has_module_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_)

  def OutputPartial(self, out):
    if (self.has_module_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_module(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_module_: res+=prefix+("module: %s\n" % self.DebugFormatString(self.module_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kmodule = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "module",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetVersionsRequest'
class GetVersionsResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.version_ = []
    if contents is not None: self.MergeFromString(contents)

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
    for i in xrange(x.version_size()): self.add_version(x.version(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.version_) != len(x.version_): return 0
    for e1, e2 in zip(self.version_, x.version_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.version_)
    for i in xrange(len(self.version_)): n += self.lengthString(len(self.version_[i]))
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.version_)
    for i in xrange(len(self.version_)): n += self.lengthString(len(self.version_[i]))
    return n

  def Clear(self):
    self.clear_version()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.version_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.version_[i])

  def OutputPartial(self, out):
    for i in xrange(len(self.version_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.version_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.add_version(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.version_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("version%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kversion = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "version",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetVersionsResponse'
class GetDefaultVersionRequest(ProtocolBuffer.ProtocolMessage):
  has_module_ = 0
  module_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def module(self): return self.module_

  def set_module(self, x):
    self.has_module_ = 1
    self.module_ = x

  def clear_module(self):
    if self.has_module_:
      self.has_module_ = 0
      self.module_ = ""

  def has_module(self): return self.has_module_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_module()): self.set_module(x.module())

  def Equals(self, x):
    if x is self: return 1
    if self.has_module_ != x.has_module_: return 0
    if self.has_module_ and self.module_ != x.module_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_module_): n += 1 + self.lengthString(len(self.module_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_module_): n += 1 + self.lengthString(len(self.module_))
    return n

  def Clear(self):
    self.clear_module()

  def OutputUnchecked(self, out):
    if (self.has_module_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_)

  def OutputPartial(self, out):
    if (self.has_module_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_module(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_module_: res+=prefix+("module: %s\n" % self.DebugFormatString(self.module_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kmodule = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "module",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetDefaultVersionRequest'
class GetDefaultVersionResponse(ProtocolBuffer.ProtocolMessage):
  has_version_ = 0
  version_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def version(self): return self.version_

  def set_version(self, x):
    self.has_version_ = 1
    self.version_ = x

  def clear_version(self):
    if self.has_version_:
      self.has_version_ = 0
      self.version_ = ""

  def has_version(self): return self.has_version_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_version()): self.set_version(x.version())

  def Equals(self, x):
    if x is self: return 1
    if self.has_version_ != x.has_version_: return 0
    if self.has_version_ and self.version_ != x.version_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_version_): n += 1 + self.lengthString(len(self.version_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_version_): n += 1 + self.lengthString(len(self.version_))
    return n

  def Clear(self):
    self.clear_version()

  def OutputUnchecked(self, out):
    if (self.has_version_):
      out.putVarInt32(10)
      out.putPrefixedString(self.version_)

  def OutputPartial(self, out):
    if (self.has_version_):
      out.putVarInt32(10)
      out.putPrefixedString(self.version_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_version(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_version_: res+=prefix+("version: %s\n" % self.DebugFormatString(self.version_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kversion = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "version",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetDefaultVersionResponse'
class GetNumInstancesRequest(ProtocolBuffer.ProtocolMessage):
  has_module_ = 0
  module_ = ""
  has_version_ = 0
  version_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def module(self): return self.module_

  def set_module(self, x):
    self.has_module_ = 1
    self.module_ = x

  def clear_module(self):
    if self.has_module_:
      self.has_module_ = 0
      self.module_ = ""

  def has_module(self): return self.has_module_

  def version(self): return self.version_

  def set_version(self, x):
    self.has_version_ = 1
    self.version_ = x

  def clear_version(self):
    if self.has_version_:
      self.has_version_ = 0
      self.version_ = ""

  def has_version(self): return self.has_version_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_module()): self.set_module(x.module())
    if (x.has_version()): self.set_version(x.version())

  def Equals(self, x):
    if x is self: return 1
    if self.has_module_ != x.has_module_: return 0
    if self.has_module_ and self.module_ != x.module_: return 0
    if self.has_version_ != x.has_version_: return 0
    if self.has_version_ and self.version_ != x.version_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_module_): n += 1 + self.lengthString(len(self.module_))
    if (self.has_version_): n += 1 + self.lengthString(len(self.version_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_module_): n += 1 + self.lengthString(len(self.module_))
    if (self.has_version_): n += 1 + self.lengthString(len(self.version_))
    return n

  def Clear(self):
    self.clear_module()
    self.clear_version()

  def OutputUnchecked(self, out):
    if (self.has_module_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_)
    if (self.has_version_):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_)

  def OutputPartial(self, out):
    if (self.has_module_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_)
    if (self.has_version_):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_module(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_version(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_module_: res+=prefix+("module: %s\n" % self.DebugFormatString(self.module_))
    if self.has_version_: res+=prefix+("version: %s\n" % self.DebugFormatString(self.version_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kmodule = 1
  kversion = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "module",
    2: "version",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetNumInstancesRequest'
class GetNumInstancesResponse(ProtocolBuffer.ProtocolMessage):
  has_instances_ = 0
  instances_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def instances(self): return self.instances_

  def set_instances(self, x):
    self.has_instances_ = 1
    self.instances_ = x

  def clear_instances(self):
    if self.has_instances_:
      self.has_instances_ = 0
      self.instances_ = 0

  def has_instances(self): return self.has_instances_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_instances()): self.set_instances(x.instances())

  def Equals(self, x):
    if x is self: return 1
    if self.has_instances_ != x.has_instances_: return 0
    if self.has_instances_ and self.instances_ != x.instances_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_instances_): n += 1 + self.lengthVarInt64(self.instances_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_instances_): n += 1 + self.lengthVarInt64(self.instances_)
    return n

  def Clear(self):
    self.clear_instances()

  def OutputUnchecked(self, out):
    if (self.has_instances_):
      out.putVarInt32(8)
      out.putVarInt64(self.instances_)

  def OutputPartial(self, out):
    if (self.has_instances_):
      out.putVarInt32(8)
      out.putVarInt64(self.instances_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_instances(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_instances_: res+=prefix+("instances: %s\n" % self.DebugFormatInt64(self.instances_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kinstances = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "instances",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetNumInstancesResponse'
class SetNumInstancesRequest(ProtocolBuffer.ProtocolMessage):
  has_module_ = 0
  module_ = ""
  has_version_ = 0
  version_ = ""
  has_instances_ = 0
  instances_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def module(self): return self.module_

  def set_module(self, x):
    self.has_module_ = 1
    self.module_ = x

  def clear_module(self):
    if self.has_module_:
      self.has_module_ = 0
      self.module_ = ""

  def has_module(self): return self.has_module_

  def version(self): return self.version_

  def set_version(self, x):
    self.has_version_ = 1
    self.version_ = x

  def clear_version(self):
    if self.has_version_:
      self.has_version_ = 0
      self.version_ = ""

  def has_version(self): return self.has_version_

  def instances(self): return self.instances_

  def set_instances(self, x):
    self.has_instances_ = 1
    self.instances_ = x

  def clear_instances(self):
    if self.has_instances_:
      self.has_instances_ = 0
      self.instances_ = 0

  def has_instances(self): return self.has_instances_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_module()): self.set_module(x.module())
    if (x.has_version()): self.set_version(x.version())
    if (x.has_instances()): self.set_instances(x.instances())

  def Equals(self, x):
    if x is self: return 1
    if self.has_module_ != x.has_module_: return 0
    if self.has_module_ and self.module_ != x.module_: return 0
    if self.has_version_ != x.has_version_: return 0
    if self.has_version_ and self.version_ != x.version_: return 0
    if self.has_instances_ != x.has_instances_: return 0
    if self.has_instances_ and self.instances_ != x.instances_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_instances_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: instances not set.')
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_module_): n += 1 + self.lengthString(len(self.module_))
    if (self.has_version_): n += 1 + self.lengthString(len(self.version_))
    n += self.lengthVarInt64(self.instances_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_module_): n += 1 + self.lengthString(len(self.module_))
    if (self.has_version_): n += 1 + self.lengthString(len(self.version_))
    if (self.has_instances_):
      n += 1
      n += self.lengthVarInt64(self.instances_)
    return n

  def Clear(self):
    self.clear_module()
    self.clear_version()
    self.clear_instances()

  def OutputUnchecked(self, out):
    if (self.has_module_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_)
    if (self.has_version_):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_)
    out.putVarInt32(24)
    out.putVarInt64(self.instances_)

  def OutputPartial(self, out):
    if (self.has_module_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_)
    if (self.has_version_):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_)
    if (self.has_instances_):
      out.putVarInt32(24)
      out.putVarInt64(self.instances_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_module(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_version(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_instances(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_module_: res+=prefix+("module: %s\n" % self.DebugFormatString(self.module_))
    if self.has_version_: res+=prefix+("version: %s\n" % self.DebugFormatString(self.version_))
    if self.has_instances_: res+=prefix+("instances: %s\n" % self.DebugFormatInt64(self.instances_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kmodule = 1
  kversion = 2
  kinstances = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "module",
    2: "version",
    3: "instances",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SetNumInstancesRequest'
class SetNumInstancesResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SetNumInstancesResponse'
class StartModuleRequest(ProtocolBuffer.ProtocolMessage):
  has_module_ = 0
  module_ = ""
  has_version_ = 0
  version_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def module(self): return self.module_

  def set_module(self, x):
    self.has_module_ = 1
    self.module_ = x

  def clear_module(self):
    if self.has_module_:
      self.has_module_ = 0
      self.module_ = ""

  def has_module(self): return self.has_module_

  def version(self): return self.version_

  def set_version(self, x):
    self.has_version_ = 1
    self.version_ = x

  def clear_version(self):
    if self.has_version_:
      self.has_version_ = 0
      self.version_ = ""

  def has_version(self): return self.has_version_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_module()): self.set_module(x.module())
    if (x.has_version()): self.set_version(x.version())

  def Equals(self, x):
    if x is self: return 1
    if self.has_module_ != x.has_module_: return 0
    if self.has_module_ and self.module_ != x.module_: return 0
    if self.has_version_ != x.has_version_: return 0
    if self.has_version_ and self.version_ != x.version_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_module_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: module not set.')
    if (not self.has_version_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: version not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.module_))
    n += self.lengthString(len(self.version_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_module_):
      n += 1
      n += self.lengthString(len(self.module_))
    if (self.has_version_):
      n += 1
      n += self.lengthString(len(self.version_))
    return n

  def Clear(self):
    self.clear_module()
    self.clear_version()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.module_)
    out.putVarInt32(18)
    out.putPrefixedString(self.version_)

  def OutputPartial(self, out):
    if (self.has_module_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_)
    if (self.has_version_):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_module(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_version(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_module_: res+=prefix+("module: %s\n" % self.DebugFormatString(self.module_))
    if self.has_version_: res+=prefix+("version: %s\n" % self.DebugFormatString(self.version_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kmodule = 1
  kversion = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "module",
    2: "version",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.StartModuleRequest'
class StartModuleResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.StartModuleResponse'
class StopModuleRequest(ProtocolBuffer.ProtocolMessage):
  has_module_ = 0
  module_ = ""
  has_version_ = 0
  version_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def module(self): return self.module_

  def set_module(self, x):
    self.has_module_ = 1
    self.module_ = x

  def clear_module(self):
    if self.has_module_:
      self.has_module_ = 0
      self.module_ = ""

  def has_module(self): return self.has_module_

  def version(self): return self.version_

  def set_version(self, x):
    self.has_version_ = 1
    self.version_ = x

  def clear_version(self):
    if self.has_version_:
      self.has_version_ = 0
      self.version_ = ""

  def has_version(self): return self.has_version_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_module()): self.set_module(x.module())
    if (x.has_version()): self.set_version(x.version())

  def Equals(self, x):
    if x is self: return 1
    if self.has_module_ != x.has_module_: return 0
    if self.has_module_ and self.module_ != x.module_: return 0
    if self.has_version_ != x.has_version_: return 0
    if self.has_version_ and self.version_ != x.version_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_module_): n += 1 + self.lengthString(len(self.module_))
    if (self.has_version_): n += 1 + self.lengthString(len(self.version_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_module_): n += 1 + self.lengthString(len(self.module_))
    if (self.has_version_): n += 1 + self.lengthString(len(self.version_))
    return n

  def Clear(self):
    self.clear_module()
    self.clear_version()

  def OutputUnchecked(self, out):
    if (self.has_module_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_)
    if (self.has_version_):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_)

  def OutputPartial(self, out):
    if (self.has_module_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_)
    if (self.has_version_):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_module(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_version(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_module_: res+=prefix+("module: %s\n" % self.DebugFormatString(self.module_))
    if self.has_version_: res+=prefix+("version: %s\n" % self.DebugFormatString(self.version_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kmodule = 1
  kversion = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "module",
    2: "version",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.StopModuleRequest'
class StopModuleResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.StopModuleResponse'
class GetHostnameRequest(ProtocolBuffer.ProtocolMessage):
  has_module_ = 0
  module_ = ""
  has_version_ = 0
  version_ = ""
  has_instance_ = 0
  instance_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def module(self): return self.module_

  def set_module(self, x):
    self.has_module_ = 1
    self.module_ = x

  def clear_module(self):
    if self.has_module_:
      self.has_module_ = 0
      self.module_ = ""

  def has_module(self): return self.has_module_

  def version(self): return self.version_

  def set_version(self, x):
    self.has_version_ = 1
    self.version_ = x

  def clear_version(self):
    if self.has_version_:
      self.has_version_ = 0
      self.version_ = ""

  def has_version(self): return self.has_version_

  def instance(self): return self.instance_

  def set_instance(self, x):
    self.has_instance_ = 1
    self.instance_ = x

  def clear_instance(self):
    if self.has_instance_:
      self.has_instance_ = 0
      self.instance_ = ""

  def has_instance(self): return self.has_instance_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_module()): self.set_module(x.module())
    if (x.has_version()): self.set_version(x.version())
    if (x.has_instance()): self.set_instance(x.instance())

  def Equals(self, x):
    if x is self: return 1
    if self.has_module_ != x.has_module_: return 0
    if self.has_module_ and self.module_ != x.module_: return 0
    if self.has_version_ != x.has_version_: return 0
    if self.has_version_ and self.version_ != x.version_: return 0
    if self.has_instance_ != x.has_instance_: return 0
    if self.has_instance_ and self.instance_ != x.instance_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_module_): n += 1 + self.lengthString(len(self.module_))
    if (self.has_version_): n += 1 + self.lengthString(len(self.version_))
    if (self.has_instance_): n += 1 + self.lengthString(len(self.instance_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_module_): n += 1 + self.lengthString(len(self.module_))
    if (self.has_version_): n += 1 + self.lengthString(len(self.version_))
    if (self.has_instance_): n += 1 + self.lengthString(len(self.instance_))
    return n

  def Clear(self):
    self.clear_module()
    self.clear_version()
    self.clear_instance()

  def OutputUnchecked(self, out):
    if (self.has_module_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_)
    if (self.has_version_):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_)
    if (self.has_instance_):
      out.putVarInt32(26)
      out.putPrefixedString(self.instance_)

  def OutputPartial(self, out):
    if (self.has_module_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_)
    if (self.has_version_):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_)
    if (self.has_instance_):
      out.putVarInt32(26)
      out.putPrefixedString(self.instance_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_module(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_version(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_instance(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_module_: res+=prefix+("module: %s\n" % self.DebugFormatString(self.module_))
    if self.has_version_: res+=prefix+("version: %s\n" % self.DebugFormatString(self.version_))
    if self.has_instance_: res+=prefix+("instance: %s\n" % self.DebugFormatString(self.instance_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kmodule = 1
  kversion = 2
  kinstance = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "module",
    2: "version",
    3: "instance",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetHostnameRequest'
class GetHostnameResponse(ProtocolBuffer.ProtocolMessage):
  has_hostname_ = 0
  hostname_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def hostname(self): return self.hostname_

  def set_hostname(self, x):
    self.has_hostname_ = 1
    self.hostname_ = x

  def clear_hostname(self):
    if self.has_hostname_:
      self.has_hostname_ = 0
      self.hostname_ = ""

  def has_hostname(self): return self.has_hostname_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_hostname()): self.set_hostname(x.hostname())

  def Equals(self, x):
    if x is self: return 1
    if self.has_hostname_ != x.has_hostname_: return 0
    if self.has_hostname_ and self.hostname_ != x.hostname_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_hostname_): n += 1 + self.lengthString(len(self.hostname_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_hostname_): n += 1 + self.lengthString(len(self.hostname_))
    return n

  def Clear(self):
    self.clear_hostname()

  def OutputUnchecked(self, out):
    if (self.has_hostname_):
      out.putVarInt32(10)
      out.putPrefixedString(self.hostname_)

  def OutputPartial(self, out):
    if (self.has_hostname_):
      out.putVarInt32(10)
      out.putPrefixedString(self.hostname_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_hostname(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_hostname_: res+=prefix+("hostname: %s\n" % self.DebugFormatString(self.hostname_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  khostname = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "hostname",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetHostnameResponse'
if _extension_runtime:
  pass

__all__ = ['ModulesServiceError','GetModulesRequest','GetModulesResponse','GetVersionsRequest','GetVersionsResponse','GetDefaultVersionRequest','GetDefaultVersionResponse','GetNumInstancesRequest','GetNumInstancesResponse','SetNumInstancesRequest','SetNumInstancesResponse','StartModuleRequest','StartModuleResponse','StopModuleRequest','StopModuleResponse','GetHostnameRequest','GetHostnameResponse']
