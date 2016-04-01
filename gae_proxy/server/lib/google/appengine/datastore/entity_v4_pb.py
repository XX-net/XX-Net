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
import base64
import dummy_thread as thread
try:
  from google3.net.proto import _net_proto___parse__python
except ImportError:
  _net_proto___parse__python = None

__pychecker__ = """maxreturns=0 maxbranches=0 no-callinit
                   unusednames=printElemNumber,debug_strs no-special"""

if hasattr(ProtocolBuffer, 'ExtendableProtocolMessage'):
  _extension_runtime = True
  _ExtendableProtocolMessage = ProtocolBuffer.ExtendableProtocolMessage
else:
  _extension_runtime = False
  _ExtendableProtocolMessage = ProtocolBuffer.ProtocolMessage

class PartitionId(ProtocolBuffer.ProtocolMessage):


  MAX_DIMENSION_TAG =  100

  _Constants_NAMES = {
    100: "MAX_DIMENSION_TAG",
  }

  def Constants_Name(cls, x): return cls._Constants_NAMES.get(x, "")
  Constants_Name = classmethod(Constants_Name)

  has_dataset_id_ = 0
  dataset_id_ = ""
  has_namespace_ = 0
  namespace_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def dataset_id(self): return self.dataset_id_

  def set_dataset_id(self, x):
    self.has_dataset_id_ = 1
    self.dataset_id_ = x

  def clear_dataset_id(self):
    if self.has_dataset_id_:
      self.has_dataset_id_ = 0
      self.dataset_id_ = ""

  def has_dataset_id(self): return self.has_dataset_id_

  def namespace(self): return self.namespace_

  def set_namespace(self, x):
    self.has_namespace_ = 1
    self.namespace_ = x

  def clear_namespace(self):
    if self.has_namespace_:
      self.has_namespace_ = 0
      self.namespace_ = ""

  def has_namespace(self): return self.has_namespace_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_dataset_id()): self.set_dataset_id(x.dataset_id())
    if (x.has_namespace()): self.set_namespace(x.namespace())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.PartitionId', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.PartitionId')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.PartitionId')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.PartitionId', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.PartitionId', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.PartitionId', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_dataset_id_ != x.has_dataset_id_: return 0
    if self.has_dataset_id_ and self.dataset_id_ != x.dataset_id_: return 0
    if self.has_namespace_ != x.has_namespace_: return 0
    if self.has_namespace_ and self.namespace_ != x.namespace_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_dataset_id_): n += 1 + self.lengthString(len(self.dataset_id_))
    if (self.has_namespace_): n += 1 + self.lengthString(len(self.namespace_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_dataset_id_): n += 1 + self.lengthString(len(self.dataset_id_))
    if (self.has_namespace_): n += 1 + self.lengthString(len(self.namespace_))
    return n

  def Clear(self):
    self.clear_dataset_id()
    self.clear_namespace()

  def OutputUnchecked(self, out):
    if (self.has_dataset_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.dataset_id_)
    if (self.has_namespace_):
      out.putVarInt32(34)
      out.putPrefixedString(self.namespace_)

  def OutputPartial(self, out):
    if (self.has_dataset_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.dataset_id_)
    if (self.has_namespace_):
      out.putVarInt32(34)
      out.putPrefixedString(self.namespace_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 26:
        self.set_dataset_id(d.getPrefixedString())
        continue
      if tt == 34:
        self.set_namespace(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_dataset_id_: res+=prefix+("dataset_id: %s\n" % self.DebugFormatString(self.dataset_id_))
    if self.has_namespace_: res+=prefix+("namespace: %s\n" % self.DebugFormatString(self.namespace_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kdataset_id = 3
  knamespace = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    3: "dataset_id",
    4: "namespace",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.PartitionId'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WiRhcHBob3N0aW5nL2RhdGFzdG9yZS9lbnRpdHlfdjQucHJvdG8KI2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlBhcnRpdGlvbklkExoKZGF0YXNldF9pZCADKAIwCTgBFBMaCW5hbWVzcGFjZSAEKAIwCTgBFHN6CUNvbnN0YW50c4sBkgERTUFYX0RJTUVOU0lPTl9UQUeYAWSMAXS6AfcICiRhcHBob3N0aW5nL2RhdGFzdG9yZS9lbnRpdHlfdjQucHJvdG8SF2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0IlgKC1BhcnRpdGlvbklkEhIKCmRhdGFzZXRfaWQYAyABKAkSEQoJbmFtZXNwYWNlGAQgASgJIiIKCUNvbnN0YW50cxIVChFNQVhfRElNRU5TSU9OX1RBRxBkIrgBCgNLZXkSOgoMcGFydGl0aW9uX2lkGAEgASgLMiQuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUGFydGl0aW9uSWQSPgoMcGF0aF9lbGVtZW50GAIgAygLMiguYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuS2V5LlBhdGhFbGVtZW50GjUKC1BhdGhFbGVtZW50EgwKBGtpbmQYASACKAkSCgoCaWQYAiABKAMSDAoEbmFtZRgDIAEoCSIvCghHZW9Qb2ludBIQCghsYXRpdHVkZRgBIAIoARIRCglsb25naXR1ZGUYAiACKAEiswMKBVZhbHVlEhUKDWJvb2xlYW5fdmFsdWUYASABKAgSFQoNaW50ZWdlcl92YWx1ZRgCIAEoAxIUCgxkb3VibGVfdmFsdWUYAyABKAESJAocdGltZXN0YW1wX21pY3Jvc2Vjb25kc192YWx1ZRgEIAEoAxIvCglrZXlfdmFsdWUYBSABKAsyHC5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5LZXkSFgoOYmxvYl9rZXlfdmFsdWUYECABKAkSFAoMc3RyaW5nX3ZhbHVlGBEgASgJEhIKCmJsb2JfdmFsdWUYEiABKAwSNQoMZW50aXR5X3ZhbHVlGAYgASgLMh8uYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRW50aXR5EjoKD2dlb19wb2ludF92YWx1ZRgIIAEoCzIhLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0Lkdlb1BvaW50EjIKCmxpc3RfdmFsdWUYByADKAsyHi5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5WYWx1ZRIPCgdtZWFuaW5nGA4gASgFEhUKB2luZGV4ZWQYDyABKAg6BHRydWUiqgEKCFByb3BlcnR5EgwKBG5hbWUYASACKAkSIwoQZGVwcmVjYXRlZF9tdWx0aRgCIAEoCDoFZmFsc2VCAhgBEjwKEGRlcHJlY2F0ZWRfdmFsdWUYAyADKAsyHi5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5WYWx1ZUICGAESLQoFdmFsdWUYBCABKAsyHi5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5WYWx1ZSJoCgZFbnRpdHkSKQoDa2V5GAEgASgLMhwuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuS2V5EjMKCHByb3BlcnR5GAIgAygLMiEuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUHJvcGVydHlCIwofY29tLmdvb2dsZS5hcHBob3N0aW5nLmRhdGFzdG9yZSAB"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class Key_PathElement(ProtocolBuffer.ProtocolMessage):
  has_kind_ = 0
  kind_ = ""
  has_id_ = 0
  id_ = 0
  has_name_ = 0
  name_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def kind(self): return self.kind_

  def set_kind(self, x):
    self.has_kind_ = 1
    self.kind_ = x

  def clear_kind(self):
    if self.has_kind_:
      self.has_kind_ = 0
      self.kind_ = ""

  def has_kind(self): return self.has_kind_

  def id(self): return self.id_

  def set_id(self, x):
    self.has_id_ = 1
    self.id_ = x

  def clear_id(self):
    if self.has_id_:
      self.has_id_ = 0
      self.id_ = 0

  def has_id(self): return self.has_id_

  def name(self): return self.name_

  def set_name(self, x):
    self.has_name_ = 1
    self.name_ = x

  def clear_name(self):
    if self.has_name_:
      self.has_name_ = 0
      self.name_ = ""

  def has_name(self): return self.has_name_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_kind()): self.set_kind(x.kind())
    if (x.has_id()): self.set_id(x.id())
    if (x.has_name()): self.set_name(x.name())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.Key_PathElement', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.Key_PathElement')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.Key_PathElement')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.Key_PathElement', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.Key_PathElement', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.Key_PathElement', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_kind_ != x.has_kind_: return 0
    if self.has_kind_ and self.kind_ != x.kind_: return 0
    if self.has_id_ != x.has_id_: return 0
    if self.has_id_ and self.id_ != x.id_: return 0
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_kind_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: kind not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.kind_))
    if (self.has_id_): n += 1 + self.lengthVarInt64(self.id_)
    if (self.has_name_): n += 1 + self.lengthString(len(self.name_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_kind_):
      n += 1
      n += self.lengthString(len(self.kind_))
    if (self.has_id_): n += 1 + self.lengthVarInt64(self.id_)
    if (self.has_name_): n += 1 + self.lengthString(len(self.name_))
    return n

  def Clear(self):
    self.clear_kind()
    self.clear_id()
    self.clear_name()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.kind_)
    if (self.has_id_):
      out.putVarInt32(16)
      out.putVarInt64(self.id_)
    if (self.has_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.name_)

  def OutputPartial(self, out):
    if (self.has_kind_):
      out.putVarInt32(10)
      out.putPrefixedString(self.kind_)
    if (self.has_id_):
      out.putVarInt32(16)
      out.putVarInt64(self.id_)
    if (self.has_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.name_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_kind(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_id(d.getVarInt64())
        continue
      if tt == 26:
        self.set_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_kind_: res+=prefix+("kind: %s\n" % self.DebugFormatString(self.kind_))
    if self.has_id_: res+=prefix+("id: %s\n" % self.DebugFormatInt64(self.id_))
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kkind = 1
  kid = 2
  kname = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "kind",
    2: "id",
    3: "name",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.Key_PathElement'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WiRhcHBob3N0aW5nL2RhdGFzdG9yZS9lbnRpdHlfdjQucHJvdG8KJ2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktleV9QYXRoRWxlbWVudBMaBGtpbmQgASgCMAk4AhQTGgJpZCACKAAwAzgBFBMaBG5hbWUgAygCMAk4ARTCASNhcHBob3N0aW5nLmRhdGFzdG9yZS52NC5QYXJ0aXRpb25JZMoBJ2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktleS5QYXRoRWxlbWVudA=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class Key(ProtocolBuffer.ProtocolMessage):
  has_partition_id_ = 0
  partition_id_ = None

  def __init__(self, contents=None):
    self.path_element_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def partition_id(self):
    if self.partition_id_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.partition_id_ is None: self.partition_id_ = PartitionId()
      finally:
        self.lazy_init_lock_.release()
    return self.partition_id_

  def mutable_partition_id(self): self.has_partition_id_ = 1; return self.partition_id()

  def clear_partition_id(self):

    if self.has_partition_id_:
      self.has_partition_id_ = 0;
      if self.partition_id_ is not None: self.partition_id_.Clear()

  def has_partition_id(self): return self.has_partition_id_

  def path_element_size(self): return len(self.path_element_)
  def path_element_list(self): return self.path_element_

  def path_element(self, i):
    return self.path_element_[i]

  def mutable_path_element(self, i):
    return self.path_element_[i]

  def add_path_element(self):
    x = Key_PathElement()
    self.path_element_.append(x)
    return x

  def clear_path_element(self):
    self.path_element_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_partition_id()): self.mutable_partition_id().MergeFrom(x.partition_id())
    for i in xrange(x.path_element_size()): self.add_path_element().CopyFrom(x.path_element(i))

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.Key', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.Key')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.Key')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.Key', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.Key', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.Key', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_partition_id_ != x.has_partition_id_: return 0
    if self.has_partition_id_ and self.partition_id_ != x.partition_id_: return 0
    if len(self.path_element_) != len(x.path_element_): return 0
    for e1, e2 in zip(self.path_element_, x.path_element_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_partition_id_ and not self.partition_id_.IsInitialized(debug_strs)): initialized = 0
    for p in self.path_element_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_partition_id_): n += 1 + self.lengthString(self.partition_id_.ByteSize())
    n += 1 * len(self.path_element_)
    for i in xrange(len(self.path_element_)): n += self.lengthString(self.path_element_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_partition_id_): n += 1 + self.lengthString(self.partition_id_.ByteSizePartial())
    n += 1 * len(self.path_element_)
    for i in xrange(len(self.path_element_)): n += self.lengthString(self.path_element_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_partition_id()
    self.clear_path_element()

  def OutputUnchecked(self, out):
    if (self.has_partition_id_):
      out.putVarInt32(10)
      out.putVarInt32(self.partition_id_.ByteSize())
      self.partition_id_.OutputUnchecked(out)
    for i in xrange(len(self.path_element_)):
      out.putVarInt32(18)
      out.putVarInt32(self.path_element_[i].ByteSize())
      self.path_element_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_partition_id_):
      out.putVarInt32(10)
      out.putVarInt32(self.partition_id_.ByteSizePartial())
      self.partition_id_.OutputPartial(out)
    for i in xrange(len(self.path_element_)):
      out.putVarInt32(18)
      out.putVarInt32(self.path_element_[i].ByteSizePartial())
      self.path_element_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_partition_id().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_path_element().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_partition_id_:
      res+=prefix+"partition_id <\n"
      res+=self.partition_id_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.path_element_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("path_element%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kpartition_id = 1
  kpath_element = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "partition_id",
    2: "path_element",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.Key'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WiRhcHBob3N0aW5nL2RhdGFzdG9yZS9lbnRpdHlfdjQucHJvdG8KG2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktleRMaDHBhcnRpdGlvbl9pZCABKAIwCzgBSiNhcHBob3N0aW5nLmRhdGFzdG9yZS52NC5QYXJ0aXRpb25JZKMBqgEFY3R5cGWyAQZwcm90bzKkARQTGgxwYXRoX2VsZW1lbnQgAigCMAs4A0onYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuS2V5X1BhdGhFbGVtZW50owGqAQVjdHlwZbIBBnByb3RvMqQBFMIBI2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlBhcnRpdGlvbklk"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class GeoPoint(ProtocolBuffer.ProtocolMessage):
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

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.GeoPoint', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.GeoPoint')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.GeoPoint')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.GeoPoint', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.GeoPoint', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.GeoPoint', s)


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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.GeoPoint'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WiRhcHBob3N0aW5nL2RhdGFzdG9yZS9lbnRpdHlfdjQucHJvdG8KIGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0Lkdlb1BvaW50ExoIbGF0aXR1ZGUgASgBMAE4AhQTGglsb25naXR1ZGUgAigBMAE4AhTCASNhcHBob3N0aW5nLmRhdGFzdG9yZS52NC5QYXJ0aXRpb25JZA=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class Value(ProtocolBuffer.ProtocolMessage):
  has_boolean_value_ = 0
  boolean_value_ = 0
  has_integer_value_ = 0
  integer_value_ = 0
  has_double_value_ = 0
  double_value_ = 0.0
  has_timestamp_microseconds_value_ = 0
  timestamp_microseconds_value_ = 0
  has_key_value_ = 0
  key_value_ = None
  has_blob_key_value_ = 0
  blob_key_value_ = ""
  has_string_value_ = 0
  string_value_ = ""
  has_blob_value_ = 0
  blob_value_ = ""
  has_entity_value_ = 0
  entity_value_ = None
  has_geo_point_value_ = 0
  geo_point_value_ = None
  has_meaning_ = 0
  meaning_ = 0
  has_indexed_ = 0
  indexed_ = 1

  def __init__(self, contents=None):
    self.list_value_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def boolean_value(self): return self.boolean_value_

  def set_boolean_value(self, x):
    self.has_boolean_value_ = 1
    self.boolean_value_ = x

  def clear_boolean_value(self):
    if self.has_boolean_value_:
      self.has_boolean_value_ = 0
      self.boolean_value_ = 0

  def has_boolean_value(self): return self.has_boolean_value_

  def integer_value(self): return self.integer_value_

  def set_integer_value(self, x):
    self.has_integer_value_ = 1
    self.integer_value_ = x

  def clear_integer_value(self):
    if self.has_integer_value_:
      self.has_integer_value_ = 0
      self.integer_value_ = 0

  def has_integer_value(self): return self.has_integer_value_

  def double_value(self): return self.double_value_

  def set_double_value(self, x):
    self.has_double_value_ = 1
    self.double_value_ = x

  def clear_double_value(self):
    if self.has_double_value_:
      self.has_double_value_ = 0
      self.double_value_ = 0.0

  def has_double_value(self): return self.has_double_value_

  def timestamp_microseconds_value(self): return self.timestamp_microseconds_value_

  def set_timestamp_microseconds_value(self, x):
    self.has_timestamp_microseconds_value_ = 1
    self.timestamp_microseconds_value_ = x

  def clear_timestamp_microseconds_value(self):
    if self.has_timestamp_microseconds_value_:
      self.has_timestamp_microseconds_value_ = 0
      self.timestamp_microseconds_value_ = 0

  def has_timestamp_microseconds_value(self): return self.has_timestamp_microseconds_value_

  def key_value(self):
    if self.key_value_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.key_value_ is None: self.key_value_ = Key()
      finally:
        self.lazy_init_lock_.release()
    return self.key_value_

  def mutable_key_value(self): self.has_key_value_ = 1; return self.key_value()

  def clear_key_value(self):

    if self.has_key_value_:
      self.has_key_value_ = 0;
      if self.key_value_ is not None: self.key_value_.Clear()

  def has_key_value(self): return self.has_key_value_

  def blob_key_value(self): return self.blob_key_value_

  def set_blob_key_value(self, x):
    self.has_blob_key_value_ = 1
    self.blob_key_value_ = x

  def clear_blob_key_value(self):
    if self.has_blob_key_value_:
      self.has_blob_key_value_ = 0
      self.blob_key_value_ = ""

  def has_blob_key_value(self): return self.has_blob_key_value_

  def string_value(self): return self.string_value_

  def set_string_value(self, x):
    self.has_string_value_ = 1
    self.string_value_ = x

  def clear_string_value(self):
    if self.has_string_value_:
      self.has_string_value_ = 0
      self.string_value_ = ""

  def has_string_value(self): return self.has_string_value_

  def blob_value(self): return self.blob_value_

  def set_blob_value(self, x):
    self.has_blob_value_ = 1
    self.blob_value_ = x

  def clear_blob_value(self):
    if self.has_blob_value_:
      self.has_blob_value_ = 0
      self.blob_value_ = ""

  def has_blob_value(self): return self.has_blob_value_

  def entity_value(self):
    if self.entity_value_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.entity_value_ is None: self.entity_value_ = Entity()
      finally:
        self.lazy_init_lock_.release()
    return self.entity_value_

  def mutable_entity_value(self): self.has_entity_value_ = 1; return self.entity_value()

  def clear_entity_value(self):

    if self.has_entity_value_:
      self.has_entity_value_ = 0;
      if self.entity_value_ is not None: self.entity_value_.Clear()

  def has_entity_value(self): return self.has_entity_value_

  def geo_point_value(self):
    if self.geo_point_value_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.geo_point_value_ is None: self.geo_point_value_ = GeoPoint()
      finally:
        self.lazy_init_lock_.release()
    return self.geo_point_value_

  def mutable_geo_point_value(self): self.has_geo_point_value_ = 1; return self.geo_point_value()

  def clear_geo_point_value(self):

    if self.has_geo_point_value_:
      self.has_geo_point_value_ = 0;
      if self.geo_point_value_ is not None: self.geo_point_value_.Clear()

  def has_geo_point_value(self): return self.has_geo_point_value_

  def list_value_size(self): return len(self.list_value_)
  def list_value_list(self): return self.list_value_

  def list_value(self, i):
    return self.list_value_[i]

  def mutable_list_value(self, i):
    return self.list_value_[i]

  def add_list_value(self):
    x = Value()
    self.list_value_.append(x)
    return x

  def clear_list_value(self):
    self.list_value_ = []
  def meaning(self): return self.meaning_

  def set_meaning(self, x):
    self.has_meaning_ = 1
    self.meaning_ = x

  def clear_meaning(self):
    if self.has_meaning_:
      self.has_meaning_ = 0
      self.meaning_ = 0

  def has_meaning(self): return self.has_meaning_

  def indexed(self): return self.indexed_

  def set_indexed(self, x):
    self.has_indexed_ = 1
    self.indexed_ = x

  def clear_indexed(self):
    if self.has_indexed_:
      self.has_indexed_ = 0
      self.indexed_ = 1

  def has_indexed(self): return self.has_indexed_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_boolean_value()): self.set_boolean_value(x.boolean_value())
    if (x.has_integer_value()): self.set_integer_value(x.integer_value())
    if (x.has_double_value()): self.set_double_value(x.double_value())
    if (x.has_timestamp_microseconds_value()): self.set_timestamp_microseconds_value(x.timestamp_microseconds_value())
    if (x.has_key_value()): self.mutable_key_value().MergeFrom(x.key_value())
    if (x.has_blob_key_value()): self.set_blob_key_value(x.blob_key_value())
    if (x.has_string_value()): self.set_string_value(x.string_value())
    if (x.has_blob_value()): self.set_blob_value(x.blob_value())
    if (x.has_entity_value()): self.mutable_entity_value().MergeFrom(x.entity_value())
    if (x.has_geo_point_value()): self.mutable_geo_point_value().MergeFrom(x.geo_point_value())
    for i in xrange(x.list_value_size()): self.add_list_value().CopyFrom(x.list_value(i))
    if (x.has_meaning()): self.set_meaning(x.meaning())
    if (x.has_indexed()): self.set_indexed(x.indexed())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.Value', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.Value')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.Value')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.Value', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.Value', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.Value', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_boolean_value_ != x.has_boolean_value_: return 0
    if self.has_boolean_value_ and self.boolean_value_ != x.boolean_value_: return 0
    if self.has_integer_value_ != x.has_integer_value_: return 0
    if self.has_integer_value_ and self.integer_value_ != x.integer_value_: return 0
    if self.has_double_value_ != x.has_double_value_: return 0
    if self.has_double_value_ and self.double_value_ != x.double_value_: return 0
    if self.has_timestamp_microseconds_value_ != x.has_timestamp_microseconds_value_: return 0
    if self.has_timestamp_microseconds_value_ and self.timestamp_microseconds_value_ != x.timestamp_microseconds_value_: return 0
    if self.has_key_value_ != x.has_key_value_: return 0
    if self.has_key_value_ and self.key_value_ != x.key_value_: return 0
    if self.has_blob_key_value_ != x.has_blob_key_value_: return 0
    if self.has_blob_key_value_ and self.blob_key_value_ != x.blob_key_value_: return 0
    if self.has_string_value_ != x.has_string_value_: return 0
    if self.has_string_value_ and self.string_value_ != x.string_value_: return 0
    if self.has_blob_value_ != x.has_blob_value_: return 0
    if self.has_blob_value_ and self.blob_value_ != x.blob_value_: return 0
    if self.has_entity_value_ != x.has_entity_value_: return 0
    if self.has_entity_value_ and self.entity_value_ != x.entity_value_: return 0
    if self.has_geo_point_value_ != x.has_geo_point_value_: return 0
    if self.has_geo_point_value_ and self.geo_point_value_ != x.geo_point_value_: return 0
    if len(self.list_value_) != len(x.list_value_): return 0
    for e1, e2 in zip(self.list_value_, x.list_value_):
      if e1 != e2: return 0
    if self.has_meaning_ != x.has_meaning_: return 0
    if self.has_meaning_ and self.meaning_ != x.meaning_: return 0
    if self.has_indexed_ != x.has_indexed_: return 0
    if self.has_indexed_ and self.indexed_ != x.indexed_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_key_value_ and not self.key_value_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_entity_value_ and not self.entity_value_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_geo_point_value_ and not self.geo_point_value_.IsInitialized(debug_strs)): initialized = 0
    for p in self.list_value_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_boolean_value_): n += 2
    if (self.has_integer_value_): n += 1 + self.lengthVarInt64(self.integer_value_)
    if (self.has_double_value_): n += 9
    if (self.has_timestamp_microseconds_value_): n += 1 + self.lengthVarInt64(self.timestamp_microseconds_value_)
    if (self.has_key_value_): n += 1 + self.lengthString(self.key_value_.ByteSize())
    if (self.has_blob_key_value_): n += 2 + self.lengthString(len(self.blob_key_value_))
    if (self.has_string_value_): n += 2 + self.lengthString(len(self.string_value_))
    if (self.has_blob_value_): n += 2 + self.lengthString(len(self.blob_value_))
    if (self.has_entity_value_): n += 1 + self.lengthString(self.entity_value_.ByteSize())
    if (self.has_geo_point_value_): n += 1 + self.lengthString(self.geo_point_value_.ByteSize())
    n += 1 * len(self.list_value_)
    for i in xrange(len(self.list_value_)): n += self.lengthString(self.list_value_[i].ByteSize())
    if (self.has_meaning_): n += 1 + self.lengthVarInt64(self.meaning_)
    if (self.has_indexed_): n += 2
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_boolean_value_): n += 2
    if (self.has_integer_value_): n += 1 + self.lengthVarInt64(self.integer_value_)
    if (self.has_double_value_): n += 9
    if (self.has_timestamp_microseconds_value_): n += 1 + self.lengthVarInt64(self.timestamp_microseconds_value_)
    if (self.has_key_value_): n += 1 + self.lengthString(self.key_value_.ByteSizePartial())
    if (self.has_blob_key_value_): n += 2 + self.lengthString(len(self.blob_key_value_))
    if (self.has_string_value_): n += 2 + self.lengthString(len(self.string_value_))
    if (self.has_blob_value_): n += 2 + self.lengthString(len(self.blob_value_))
    if (self.has_entity_value_): n += 1 + self.lengthString(self.entity_value_.ByteSizePartial())
    if (self.has_geo_point_value_): n += 1 + self.lengthString(self.geo_point_value_.ByteSizePartial())
    n += 1 * len(self.list_value_)
    for i in xrange(len(self.list_value_)): n += self.lengthString(self.list_value_[i].ByteSizePartial())
    if (self.has_meaning_): n += 1 + self.lengthVarInt64(self.meaning_)
    if (self.has_indexed_): n += 2
    return n

  def Clear(self):
    self.clear_boolean_value()
    self.clear_integer_value()
    self.clear_double_value()
    self.clear_timestamp_microseconds_value()
    self.clear_key_value()
    self.clear_blob_key_value()
    self.clear_string_value()
    self.clear_blob_value()
    self.clear_entity_value()
    self.clear_geo_point_value()
    self.clear_list_value()
    self.clear_meaning()
    self.clear_indexed()

  def OutputUnchecked(self, out):
    if (self.has_boolean_value_):
      out.putVarInt32(8)
      out.putBoolean(self.boolean_value_)
    if (self.has_integer_value_):
      out.putVarInt32(16)
      out.putVarInt64(self.integer_value_)
    if (self.has_double_value_):
      out.putVarInt32(25)
      out.putDouble(self.double_value_)
    if (self.has_timestamp_microseconds_value_):
      out.putVarInt32(32)
      out.putVarInt64(self.timestamp_microseconds_value_)
    if (self.has_key_value_):
      out.putVarInt32(42)
      out.putVarInt32(self.key_value_.ByteSize())
      self.key_value_.OutputUnchecked(out)
    if (self.has_entity_value_):
      out.putVarInt32(50)
      out.putVarInt32(self.entity_value_.ByteSize())
      self.entity_value_.OutputUnchecked(out)
    for i in xrange(len(self.list_value_)):
      out.putVarInt32(58)
      out.putVarInt32(self.list_value_[i].ByteSize())
      self.list_value_[i].OutputUnchecked(out)
    if (self.has_geo_point_value_):
      out.putVarInt32(66)
      out.putVarInt32(self.geo_point_value_.ByteSize())
      self.geo_point_value_.OutputUnchecked(out)
    if (self.has_meaning_):
      out.putVarInt32(112)
      out.putVarInt32(self.meaning_)
    if (self.has_indexed_):
      out.putVarInt32(120)
      out.putBoolean(self.indexed_)
    if (self.has_blob_key_value_):
      out.putVarInt32(130)
      out.putPrefixedString(self.blob_key_value_)
    if (self.has_string_value_):
      out.putVarInt32(138)
      out.putPrefixedString(self.string_value_)
    if (self.has_blob_value_):
      out.putVarInt32(146)
      out.putPrefixedString(self.blob_value_)

  def OutputPartial(self, out):
    if (self.has_boolean_value_):
      out.putVarInt32(8)
      out.putBoolean(self.boolean_value_)
    if (self.has_integer_value_):
      out.putVarInt32(16)
      out.putVarInt64(self.integer_value_)
    if (self.has_double_value_):
      out.putVarInt32(25)
      out.putDouble(self.double_value_)
    if (self.has_timestamp_microseconds_value_):
      out.putVarInt32(32)
      out.putVarInt64(self.timestamp_microseconds_value_)
    if (self.has_key_value_):
      out.putVarInt32(42)
      out.putVarInt32(self.key_value_.ByteSizePartial())
      self.key_value_.OutputPartial(out)
    if (self.has_entity_value_):
      out.putVarInt32(50)
      out.putVarInt32(self.entity_value_.ByteSizePartial())
      self.entity_value_.OutputPartial(out)
    for i in xrange(len(self.list_value_)):
      out.putVarInt32(58)
      out.putVarInt32(self.list_value_[i].ByteSizePartial())
      self.list_value_[i].OutputPartial(out)
    if (self.has_geo_point_value_):
      out.putVarInt32(66)
      out.putVarInt32(self.geo_point_value_.ByteSizePartial())
      self.geo_point_value_.OutputPartial(out)
    if (self.has_meaning_):
      out.putVarInt32(112)
      out.putVarInt32(self.meaning_)
    if (self.has_indexed_):
      out.putVarInt32(120)
      out.putBoolean(self.indexed_)
    if (self.has_blob_key_value_):
      out.putVarInt32(130)
      out.putPrefixedString(self.blob_key_value_)
    if (self.has_string_value_):
      out.putVarInt32(138)
      out.putPrefixedString(self.string_value_)
    if (self.has_blob_value_):
      out.putVarInt32(146)
      out.putPrefixedString(self.blob_value_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_boolean_value(d.getBoolean())
        continue
      if tt == 16:
        self.set_integer_value(d.getVarInt64())
        continue
      if tt == 25:
        self.set_double_value(d.getDouble())
        continue
      if tt == 32:
        self.set_timestamp_microseconds_value(d.getVarInt64())
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_key_value().TryMerge(tmp)
        continue
      if tt == 50:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_entity_value().TryMerge(tmp)
        continue
      if tt == 58:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_list_value().TryMerge(tmp)
        continue
      if tt == 66:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_geo_point_value().TryMerge(tmp)
        continue
      if tt == 112:
        self.set_meaning(d.getVarInt32())
        continue
      if tt == 120:
        self.set_indexed(d.getBoolean())
        continue
      if tt == 130:
        self.set_blob_key_value(d.getPrefixedString())
        continue
      if tt == 138:
        self.set_string_value(d.getPrefixedString())
        continue
      if tt == 146:
        self.set_blob_value(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_boolean_value_: res+=prefix+("boolean_value: %s\n" % self.DebugFormatBool(self.boolean_value_))
    if self.has_integer_value_: res+=prefix+("integer_value: %s\n" % self.DebugFormatInt64(self.integer_value_))
    if self.has_double_value_: res+=prefix+("double_value: %s\n" % self.DebugFormat(self.double_value_))
    if self.has_timestamp_microseconds_value_: res+=prefix+("timestamp_microseconds_value: %s\n" % self.DebugFormatInt64(self.timestamp_microseconds_value_))
    if self.has_key_value_:
      res+=prefix+"key_value <\n"
      res+=self.key_value_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_blob_key_value_: res+=prefix+("blob_key_value: %s\n" % self.DebugFormatString(self.blob_key_value_))
    if self.has_string_value_: res+=prefix+("string_value: %s\n" % self.DebugFormatString(self.string_value_))
    if self.has_blob_value_: res+=prefix+("blob_value: %s\n" % self.DebugFormatString(self.blob_value_))
    if self.has_entity_value_:
      res+=prefix+"entity_value <\n"
      res+=self.entity_value_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_geo_point_value_:
      res+=prefix+"geo_point_value <\n"
      res+=self.geo_point_value_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.list_value_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("list_value%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_meaning_: res+=prefix+("meaning: %s\n" % self.DebugFormatInt32(self.meaning_))
    if self.has_indexed_: res+=prefix+("indexed: %s\n" % self.DebugFormatBool(self.indexed_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kboolean_value = 1
  kinteger_value = 2
  kdouble_value = 3
  ktimestamp_microseconds_value = 4
  kkey_value = 5
  kblob_key_value = 16
  kstring_value = 17
  kblob_value = 18
  kentity_value = 6
  kgeo_point_value = 8
  klist_value = 7
  kmeaning = 14
  kindexed = 15

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "boolean_value",
    2: "integer_value",
    3: "double_value",
    4: "timestamp_microseconds_value",
    5: "key_value",
    6: "entity_value",
    7: "list_value",
    8: "geo_point_value",
    14: "meaning",
    15: "indexed",
    16: "blob_key_value",
    17: "string_value",
    18: "blob_value",
  }, 18)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.DOUBLE,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.STRING,
    7: ProtocolBuffer.Encoder.STRING,
    8: ProtocolBuffer.Encoder.STRING,
    14: ProtocolBuffer.Encoder.NUMERIC,
    15: ProtocolBuffer.Encoder.NUMERIC,
    16: ProtocolBuffer.Encoder.STRING,
    17: ProtocolBuffer.Encoder.STRING,
    18: ProtocolBuffer.Encoder.STRING,
  }, 18, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.Value'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WiRhcHBob3N0aW5nL2RhdGFzdG9yZS9lbnRpdHlfdjQucHJvdG8KHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlZhbHVlExoNYm9vbGVhbl92YWx1ZSABKAAwCDgBFBMaDWludGVnZXJfdmFsdWUgAigAMAM4ARQTGgxkb3VibGVfdmFsdWUgAygBMAE4ARQTGhx0aW1lc3RhbXBfbWljcm9zZWNvbmRzX3ZhbHVlIAQoADADOAEUExoJa2V5X3ZhbHVlIAUoAjALOAFKG2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktleaMBqgEFY3R5cGWyAQZwcm90bzKkARQTGg5ibG9iX2tleV92YWx1ZSAQKAIwCTgBFBMaDHN0cmluZ192YWx1ZSARKAIwCTgBFBMaCmJsb2JfdmFsdWUgEigCMAk4ARQTGgxlbnRpdHlfdmFsdWUgBigCMAs4AUoeYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRW50aXR5owGqAQVjdHlwZbIBBnByb3RvMqQBFBMaD2dlb19wb2ludF92YWx1ZSAIKAIwCzgBSiBhcHBob3N0aW5nLmRhdGFzdG9yZS52NC5HZW9Qb2ludKMBqgEFY3R5cGWyAQZwcm90bzKkARQTGgpsaXN0X3ZhbHVlIAcoAjALOANKHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlZhbHVlowGqAQVjdHlwZbIBBnByb3RvMqQBFBMaB21lYW5pbmcgDigAMAU4ARQTGgdpbmRleGVkIA8oADAIOAFCBHRydWWjAaoBB2RlZmF1bHSyAQR0cnVlpAEUwgEjYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUGFydGl0aW9uSWQ="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class Property(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""
  has_deprecated_multi_ = 0
  deprecated_multi_ = 0
  has_value_ = 0
  value_ = None

  def __init__(self, contents=None):
    self.deprecated_value_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
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

  def deprecated_multi(self): return self.deprecated_multi_

  def set_deprecated_multi(self, x):
    self.has_deprecated_multi_ = 1
    self.deprecated_multi_ = x

  def clear_deprecated_multi(self):
    if self.has_deprecated_multi_:
      self.has_deprecated_multi_ = 0
      self.deprecated_multi_ = 0

  def has_deprecated_multi(self): return self.has_deprecated_multi_

  def deprecated_value_size(self): return len(self.deprecated_value_)
  def deprecated_value_list(self): return self.deprecated_value_

  def deprecated_value(self, i):
    return self.deprecated_value_[i]

  def mutable_deprecated_value(self, i):
    return self.deprecated_value_[i]

  def add_deprecated_value(self):
    x = Value()
    self.deprecated_value_.append(x)
    return x

  def clear_deprecated_value(self):
    self.deprecated_value_ = []
  def value(self):
    if self.value_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.value_ is None: self.value_ = Value()
      finally:
        self.lazy_init_lock_.release()
    return self.value_

  def mutable_value(self): self.has_value_ = 1; return self.value()

  def clear_value(self):

    if self.has_value_:
      self.has_value_ = 0;
      if self.value_ is not None: self.value_.Clear()

  def has_value(self): return self.has_value_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())
    if (x.has_deprecated_multi()): self.set_deprecated_multi(x.deprecated_multi())
    for i in xrange(x.deprecated_value_size()): self.add_deprecated_value().CopyFrom(x.deprecated_value(i))
    if (x.has_value()): self.mutable_value().MergeFrom(x.value())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.Property', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.Property')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.Property')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.Property', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.Property', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.Property', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if self.has_deprecated_multi_ != x.has_deprecated_multi_: return 0
    if self.has_deprecated_multi_ and self.deprecated_multi_ != x.deprecated_multi_: return 0
    if len(self.deprecated_value_) != len(x.deprecated_value_): return 0
    for e1, e2 in zip(self.deprecated_value_, x.deprecated_value_):
      if e1 != e2: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: name not set.')
    for p in self.deprecated_value_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_value_ and not self.value_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.name_))
    if (self.has_deprecated_multi_): n += 2
    n += 1 * len(self.deprecated_value_)
    for i in xrange(len(self.deprecated_value_)): n += self.lengthString(self.deprecated_value_[i].ByteSize())
    if (self.has_value_): n += 1 + self.lengthString(self.value_.ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    if (self.has_deprecated_multi_): n += 2
    n += 1 * len(self.deprecated_value_)
    for i in xrange(len(self.deprecated_value_)): n += self.lengthString(self.deprecated_value_[i].ByteSizePartial())
    if (self.has_value_): n += 1 + self.lengthString(self.value_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_name()
    self.clear_deprecated_multi()
    self.clear_deprecated_value()
    self.clear_value()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.name_)
    if (self.has_deprecated_multi_):
      out.putVarInt32(16)
      out.putBoolean(self.deprecated_multi_)
    for i in xrange(len(self.deprecated_value_)):
      out.putVarInt32(26)
      out.putVarInt32(self.deprecated_value_[i].ByteSize())
      self.deprecated_value_[i].OutputUnchecked(out)
    if (self.has_value_):
      out.putVarInt32(34)
      out.putVarInt32(self.value_.ByteSize())
      self.value_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    if (self.has_deprecated_multi_):
      out.putVarInt32(16)
      out.putBoolean(self.deprecated_multi_)
    for i in xrange(len(self.deprecated_value_)):
      out.putVarInt32(26)
      out.putVarInt32(self.deprecated_value_[i].ByteSizePartial())
      self.deprecated_value_[i].OutputPartial(out)
    if (self.has_value_):
      out.putVarInt32(34)
      out.putVarInt32(self.value_.ByteSizePartial())
      self.value_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_name(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_deprecated_multi(d.getBoolean())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_deprecated_value().TryMerge(tmp)
        continue
      if tt == 34:
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
    if self.has_deprecated_multi_: res+=prefix+("deprecated_multi: %s\n" % self.DebugFormatBool(self.deprecated_multi_))
    cnt=0
    for e in self.deprecated_value_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("deprecated_value%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_value_:
      res+=prefix+"value <\n"
      res+=self.value_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 1
  kdeprecated_multi = 2
  kdeprecated_value = 3
  kvalue = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name",
    2: "deprecated_multi",
    3: "deprecated_value",
    4: "value",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.Property'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WiRhcHBob3N0aW5nL2RhdGFzdG9yZS9lbnRpdHlfdjQucHJvdG8KIGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlByb3BlcnR5ExoEbmFtZSABKAIwCTgCFBMaEGRlcHJlY2F0ZWRfbXVsdGkgAigAMAg4AUIFZmFsc2XQAQGjAaoBB2RlZmF1bHSyAQVmYWxzZaQBFBMaEGRlcHJlY2F0ZWRfdmFsdWUgAygCMAs4A0odYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuVmFsdWXQAQGjAaoBBWN0eXBlsgEGcHJvdG8ypAEUExoFdmFsdWUgBCgCMAs4AUodYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuVmFsdWWjAaoBBWN0eXBlsgEGcHJvdG8ypAEUwgEjYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUGFydGl0aW9uSWQ="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class Entity(ProtocolBuffer.ProtocolMessage):
  has_key_ = 0
  key_ = None

  def __init__(self, contents=None):
    self.property_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def key(self):
    if self.key_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.key_ is None: self.key_ = Key()
      finally:
        self.lazy_init_lock_.release()
    return self.key_

  def mutable_key(self): self.has_key_ = 1; return self.key()

  def clear_key(self):

    if self.has_key_:
      self.has_key_ = 0;
      if self.key_ is not None: self.key_.Clear()

  def has_key(self): return self.has_key_

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

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_key()): self.mutable_key().MergeFrom(x.key())
    for i in xrange(x.property_size()): self.add_property().CopyFrom(x.property(i))

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.Entity', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.Entity')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.Entity')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.Entity', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.Entity', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.Entity', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_key_ != x.has_key_: return 0
    if self.has_key_ and self.key_ != x.key_: return 0
    if len(self.property_) != len(x.property_): return 0
    for e1, e2 in zip(self.property_, x.property_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_key_ and not self.key_.IsInitialized(debug_strs)): initialized = 0
    for p in self.property_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_key_): n += 1 + self.lengthString(self.key_.ByteSize())
    n += 1 * len(self.property_)
    for i in xrange(len(self.property_)): n += self.lengthString(self.property_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_key_): n += 1 + self.lengthString(self.key_.ByteSizePartial())
    n += 1 * len(self.property_)
    for i in xrange(len(self.property_)): n += self.lengthString(self.property_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_key()
    self.clear_property()

  def OutputUnchecked(self, out):
    if (self.has_key_):
      out.putVarInt32(10)
      out.putVarInt32(self.key_.ByteSize())
      self.key_.OutputUnchecked(out)
    for i in xrange(len(self.property_)):
      out.putVarInt32(18)
      out.putVarInt32(self.property_[i].ByteSize())
      self.property_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_key_):
      out.putVarInt32(10)
      out.putVarInt32(self.key_.ByteSizePartial())
      self.key_.OutputPartial(out)
    for i in xrange(len(self.property_)):
      out.putVarInt32(18)
      out.putVarInt32(self.property_[i].ByteSizePartial())
      self.property_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_key().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_property().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_:
      res+=prefix+"key <\n"
      res+=self.key_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.property_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("property%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kkey = 1
  kproperty = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "key",
    2: "property",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.Entity'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WiRhcHBob3N0aW5nL2RhdGFzdG9yZS9lbnRpdHlfdjQucHJvdG8KHmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVudGl0eRMaA2tleSABKAIwCzgBShthcHBob3N0aW5nLmRhdGFzdG9yZS52NC5LZXmjAaoBBWN0eXBlsgEGcHJvdG8ypAEUExoIcHJvcGVydHkgAigCMAs4A0ogYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUHJvcGVydHmjAaoBBWN0eXBlsgEGcHJvdG8ypAEUwgEjYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUGFydGl0aW9uSWQ="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

if _extension_runtime:
  pass

__all__ = ['PartitionId','Key_PathElement','Key','GeoPoint','Value','Property','Entity']
