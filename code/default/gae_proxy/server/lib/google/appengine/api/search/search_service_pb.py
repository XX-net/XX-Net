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

from google.appengine.datastore.document_pb import *
import google.appengine.datastore.document_pb
class SearchServiceError(ProtocolBuffer.ProtocolMessage):


  OK           =    0
  INVALID_REQUEST =    1
  TRANSIENT_ERROR =    2
  INTERNAL_ERROR =    3
  PERMISSION_DENIED =    4
  TIMEOUT      =    5
  CONCURRENT_TRANSACTION =    6

  _ErrorCode_NAMES = {
    0: "OK",
    1: "INVALID_REQUEST",
    2: "TRANSIENT_ERROR",
    3: "INTERNAL_ERROR",
    4: "PERMISSION_DENIED",
    5: "TIMEOUT",
    6: "CONCURRENT_TRANSACTION",
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SearchServiceError'
class RequestStatus(ProtocolBuffer.ProtocolMessage):
  has_code_ = 0
  code_ = 0
  has_error_detail_ = 0
  error_detail_ = ""
  has_canonical_code_ = 0
  canonical_code_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def code(self): return self.code_

  def set_code(self, x):
    self.has_code_ = 1
    self.code_ = x

  def clear_code(self):
    if self.has_code_:
      self.has_code_ = 0
      self.code_ = 0

  def has_code(self): return self.has_code_

  def error_detail(self): return self.error_detail_

  def set_error_detail(self, x):
    self.has_error_detail_ = 1
    self.error_detail_ = x

  def clear_error_detail(self):
    if self.has_error_detail_:
      self.has_error_detail_ = 0
      self.error_detail_ = ""

  def has_error_detail(self): return self.has_error_detail_

  def canonical_code(self): return self.canonical_code_

  def set_canonical_code(self, x):
    self.has_canonical_code_ = 1
    self.canonical_code_ = x

  def clear_canonical_code(self):
    if self.has_canonical_code_:
      self.has_canonical_code_ = 0
      self.canonical_code_ = 0

  def has_canonical_code(self): return self.has_canonical_code_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_code()): self.set_code(x.code())
    if (x.has_error_detail()): self.set_error_detail(x.error_detail())
    if (x.has_canonical_code()): self.set_canonical_code(x.canonical_code())

  def Equals(self, x):
    if x is self: return 1
    if self.has_code_ != x.has_code_: return 0
    if self.has_code_ and self.code_ != x.code_: return 0
    if self.has_error_detail_ != x.has_error_detail_: return 0
    if self.has_error_detail_ and self.error_detail_ != x.error_detail_: return 0
    if self.has_canonical_code_ != x.has_canonical_code_: return 0
    if self.has_canonical_code_ and self.canonical_code_ != x.canonical_code_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_code_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: code not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.code_)
    if (self.has_error_detail_): n += 1 + self.lengthString(len(self.error_detail_))
    if (self.has_canonical_code_): n += 1 + self.lengthVarInt64(self.canonical_code_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_code_):
      n += 1
      n += self.lengthVarInt64(self.code_)
    if (self.has_error_detail_): n += 1 + self.lengthString(len(self.error_detail_))
    if (self.has_canonical_code_): n += 1 + self.lengthVarInt64(self.canonical_code_)
    return n

  def Clear(self):
    self.clear_code()
    self.clear_error_detail()
    self.clear_canonical_code()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt32(self.code_)
    if (self.has_error_detail_):
      out.putVarInt32(18)
      out.putPrefixedString(self.error_detail_)
    if (self.has_canonical_code_):
      out.putVarInt32(24)
      out.putVarInt32(self.canonical_code_)

  def OutputPartial(self, out):
    if (self.has_code_):
      out.putVarInt32(8)
      out.putVarInt32(self.code_)
    if (self.has_error_detail_):
      out.putVarInt32(18)
      out.putPrefixedString(self.error_detail_)
    if (self.has_canonical_code_):
      out.putVarInt32(24)
      out.putVarInt32(self.canonical_code_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_code(d.getVarInt32())
        continue
      if tt == 18:
        self.set_error_detail(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_canonical_code(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_code_: res+=prefix+("code: %s\n" % self.DebugFormatInt32(self.code_))
    if self.has_error_detail_: res+=prefix+("error_detail: %s\n" % self.DebugFormatString(self.error_detail_))
    if self.has_canonical_code_: res+=prefix+("canonical_code: %s\n" % self.DebugFormatInt32(self.canonical_code_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kcode = 1
  kerror_detail = 2
  kcanonical_code = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "code",
    2: "error_detail",
    3: "canonical_code",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.RequestStatus'
class IndexSpec(ProtocolBuffer.ProtocolMessage):


  GLOBAL       =    0
  PER_DOCUMENT =    1

  _Consistency_NAMES = {
    0: "GLOBAL",
    1: "PER_DOCUMENT",
  }

  def Consistency_Name(cls, x): return cls._Consistency_NAMES.get(x, "")
  Consistency_Name = classmethod(Consistency_Name)



  SEARCH       =    0
  DATASTORE    =    1
  CLOUD_STORAGE =    2

  _Source_NAMES = {
    0: "SEARCH",
    1: "DATASTORE",
    2: "CLOUD_STORAGE",
  }

  def Source_Name(cls, x): return cls._Source_NAMES.get(x, "")
  Source_Name = classmethod(Source_Name)



  PRIORITY     =    0
  BACKGROUND   =    1

  _Mode_NAMES = {
    0: "PRIORITY",
    1: "BACKGROUND",
  }

  def Mode_Name(cls, x): return cls._Mode_NAMES.get(x, "")
  Mode_Name = classmethod(Mode_Name)

  has_name_ = 0
  name_ = ""
  has_consistency_ = 0
  consistency_ = 1
  has_namespace_ = 0
  namespace_ = ""
  has_version_ = 0
  version_ = 0
  has_source_ = 0
  source_ = 0
  has_mode_ = 0
  mode_ = 0

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

  def consistency(self): return self.consistency_

  def set_consistency(self, x):
    self.has_consistency_ = 1
    self.consistency_ = x

  def clear_consistency(self):
    if self.has_consistency_:
      self.has_consistency_ = 0
      self.consistency_ = 1

  def has_consistency(self): return self.has_consistency_

  def namespace(self): return self.namespace_

  def set_namespace(self, x):
    self.has_namespace_ = 1
    self.namespace_ = x

  def clear_namespace(self):
    if self.has_namespace_:
      self.has_namespace_ = 0
      self.namespace_ = ""

  def has_namespace(self): return self.has_namespace_

  def version(self): return self.version_

  def set_version(self, x):
    self.has_version_ = 1
    self.version_ = x

  def clear_version(self):
    if self.has_version_:
      self.has_version_ = 0
      self.version_ = 0

  def has_version(self): return self.has_version_

  def source(self): return self.source_

  def set_source(self, x):
    self.has_source_ = 1
    self.source_ = x

  def clear_source(self):
    if self.has_source_:
      self.has_source_ = 0
      self.source_ = 0

  def has_source(self): return self.has_source_

  def mode(self): return self.mode_

  def set_mode(self, x):
    self.has_mode_ = 1
    self.mode_ = x

  def clear_mode(self):
    if self.has_mode_:
      self.has_mode_ = 0
      self.mode_ = 0

  def has_mode(self): return self.has_mode_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())
    if (x.has_consistency()): self.set_consistency(x.consistency())
    if (x.has_namespace()): self.set_namespace(x.namespace())
    if (x.has_version()): self.set_version(x.version())
    if (x.has_source()): self.set_source(x.source())
    if (x.has_mode()): self.set_mode(x.mode())

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if self.has_consistency_ != x.has_consistency_: return 0
    if self.has_consistency_ and self.consistency_ != x.consistency_: return 0
    if self.has_namespace_ != x.has_namespace_: return 0
    if self.has_namespace_ and self.namespace_ != x.namespace_: return 0
    if self.has_version_ != x.has_version_: return 0
    if self.has_version_ and self.version_ != x.version_: return 0
    if self.has_source_ != x.has_source_: return 0
    if self.has_source_ and self.source_ != x.source_: return 0
    if self.has_mode_ != x.has_mode_: return 0
    if self.has_mode_ and self.mode_ != x.mode_: return 0
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
    if (self.has_consistency_): n += 1 + self.lengthVarInt64(self.consistency_)
    if (self.has_namespace_): n += 1 + self.lengthString(len(self.namespace_))
    if (self.has_version_): n += 1 + self.lengthVarInt64(self.version_)
    if (self.has_source_): n += 1 + self.lengthVarInt64(self.source_)
    if (self.has_mode_): n += 1 + self.lengthVarInt64(self.mode_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    if (self.has_consistency_): n += 1 + self.lengthVarInt64(self.consistency_)
    if (self.has_namespace_): n += 1 + self.lengthString(len(self.namespace_))
    if (self.has_version_): n += 1 + self.lengthVarInt64(self.version_)
    if (self.has_source_): n += 1 + self.lengthVarInt64(self.source_)
    if (self.has_mode_): n += 1 + self.lengthVarInt64(self.mode_)
    return n

  def Clear(self):
    self.clear_name()
    self.clear_consistency()
    self.clear_namespace()
    self.clear_version()
    self.clear_source()
    self.clear_mode()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.name_)
    if (self.has_consistency_):
      out.putVarInt32(16)
      out.putVarInt32(self.consistency_)
    if (self.has_namespace_):
      out.putVarInt32(26)
      out.putPrefixedString(self.namespace_)
    if (self.has_version_):
      out.putVarInt32(32)
      out.putVarInt32(self.version_)
    if (self.has_source_):
      out.putVarInt32(40)
      out.putVarInt32(self.source_)
    if (self.has_mode_):
      out.putVarInt32(48)
      out.putVarInt32(self.mode_)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    if (self.has_consistency_):
      out.putVarInt32(16)
      out.putVarInt32(self.consistency_)
    if (self.has_namespace_):
      out.putVarInt32(26)
      out.putPrefixedString(self.namespace_)
    if (self.has_version_):
      out.putVarInt32(32)
      out.putVarInt32(self.version_)
    if (self.has_source_):
      out.putVarInt32(40)
      out.putVarInt32(self.source_)
    if (self.has_mode_):
      out.putVarInt32(48)
      out.putVarInt32(self.mode_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_name(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_consistency(d.getVarInt32())
        continue
      if tt == 26:
        self.set_namespace(d.getPrefixedString())
        continue
      if tt == 32:
        self.set_version(d.getVarInt32())
        continue
      if tt == 40:
        self.set_source(d.getVarInt32())
        continue
      if tt == 48:
        self.set_mode(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    if self.has_consistency_: res+=prefix+("consistency: %s\n" % self.DebugFormatInt32(self.consistency_))
    if self.has_namespace_: res+=prefix+("namespace: %s\n" % self.DebugFormatString(self.namespace_))
    if self.has_version_: res+=prefix+("version: %s\n" % self.DebugFormatInt32(self.version_))
    if self.has_source_: res+=prefix+("source: %s\n" % self.DebugFormatInt32(self.source_))
    if self.has_mode_: res+=prefix+("mode: %s\n" % self.DebugFormatInt32(self.mode_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 1
  kconsistency = 2
  knamespace = 3
  kversion = 4
  ksource = 5
  kmode = 6

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name",
    2: "consistency",
    3: "namespace",
    4: "version",
    5: "source",
    6: "mode",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.NUMERIC,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.IndexSpec'
class IndexMetadata_Storage(ProtocolBuffer.ProtocolMessage):
  has_amount_used_ = 0
  amount_used_ = 0
  has_limit_ = 0
  limit_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def amount_used(self): return self.amount_used_

  def set_amount_used(self, x):
    self.has_amount_used_ = 1
    self.amount_used_ = x

  def clear_amount_used(self):
    if self.has_amount_used_:
      self.has_amount_used_ = 0
      self.amount_used_ = 0

  def has_amount_used(self): return self.has_amount_used_

  def limit(self): return self.limit_

  def set_limit(self, x):
    self.has_limit_ = 1
    self.limit_ = x

  def clear_limit(self):
    if self.has_limit_:
      self.has_limit_ = 0
      self.limit_ = 0

  def has_limit(self): return self.has_limit_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_amount_used()): self.set_amount_used(x.amount_used())
    if (x.has_limit()): self.set_limit(x.limit())

  def Equals(self, x):
    if x is self: return 1
    if self.has_amount_used_ != x.has_amount_used_: return 0
    if self.has_amount_used_ and self.amount_used_ != x.amount_used_: return 0
    if self.has_limit_ != x.has_limit_: return 0
    if self.has_limit_ and self.limit_ != x.limit_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_amount_used_): n += 1 + self.lengthVarInt64(self.amount_used_)
    if (self.has_limit_): n += 1 + self.lengthVarInt64(self.limit_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_amount_used_): n += 1 + self.lengthVarInt64(self.amount_used_)
    if (self.has_limit_): n += 1 + self.lengthVarInt64(self.limit_)
    return n

  def Clear(self):
    self.clear_amount_used()
    self.clear_limit()

  def OutputUnchecked(self, out):
    if (self.has_amount_used_):
      out.putVarInt32(8)
      out.putVarInt64(self.amount_used_)
    if (self.has_limit_):
      out.putVarInt32(16)
      out.putVarInt64(self.limit_)

  def OutputPartial(self, out):
    if (self.has_amount_used_):
      out.putVarInt32(8)
      out.putVarInt64(self.amount_used_)
    if (self.has_limit_):
      out.putVarInt32(16)
      out.putVarInt64(self.limit_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_amount_used(d.getVarInt64())
        continue
      if tt == 16:
        self.set_limit(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_amount_used_: res+=prefix+("amount_used: %s\n" % self.DebugFormatInt64(self.amount_used_))
    if self.has_limit_: res+=prefix+("limit: %s\n" % self.DebugFormatInt64(self.limit_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kamount_used = 1
  klimit = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "amount_used",
    2: "limit",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.IndexMetadata_Storage'
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

  has_index_spec_ = 0
  has_storage_ = 0
  storage_ = None
  has_index_state_ = 0
  index_state_ = 0
  has_index_delete_time_ = 0
  index_delete_time_ = 0

  def __init__(self, contents=None):
    self.index_spec_ = IndexSpec()
    self.field_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def index_spec(self): return self.index_spec_

  def mutable_index_spec(self): self.has_index_spec_ = 1; return self.index_spec_

  def clear_index_spec(self):self.has_index_spec_ = 0; self.index_spec_.Clear()

  def has_index_spec(self): return self.has_index_spec_

  def field_size(self): return len(self.field_)
  def field_list(self): return self.field_

  def field(self, i):
    return self.field_[i]

  def mutable_field(self, i):
    return self.field_[i]

  def add_field(self):
    x = FieldTypes()
    self.field_.append(x)
    return x

  def clear_field(self):
    self.field_ = []
  def storage(self):
    if self.storage_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.storage_ is None: self.storage_ = IndexMetadata_Storage()
      finally:
        self.lazy_init_lock_.release()
    return self.storage_

  def mutable_storage(self): self.has_storage_ = 1; return self.storage()

  def clear_storage(self):

    if self.has_storage_:
      self.has_storage_ = 0;
      if self.storage_ is not None: self.storage_.Clear()

  def has_storage(self): return self.has_storage_

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


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_index_spec()): self.mutable_index_spec().MergeFrom(x.index_spec())
    for i in xrange(x.field_size()): self.add_field().CopyFrom(x.field(i))
    if (x.has_storage()): self.mutable_storage().MergeFrom(x.storage())
    if (x.has_index_state()): self.set_index_state(x.index_state())
    if (x.has_index_delete_time()): self.set_index_delete_time(x.index_delete_time())

  def Equals(self, x):
    if x is self: return 1
    if self.has_index_spec_ != x.has_index_spec_: return 0
    if self.has_index_spec_ and self.index_spec_ != x.index_spec_: return 0
    if len(self.field_) != len(x.field_): return 0
    for e1, e2 in zip(self.field_, x.field_):
      if e1 != e2: return 0
    if self.has_storage_ != x.has_storage_: return 0
    if self.has_storage_ and self.storage_ != x.storage_: return 0
    if self.has_index_state_ != x.has_index_state_: return 0
    if self.has_index_state_ and self.index_state_ != x.index_state_: return 0
    if self.has_index_delete_time_ != x.has_index_delete_time_: return 0
    if self.has_index_delete_time_ and self.index_delete_time_ != x.index_delete_time_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_index_spec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: index_spec not set.')
    elif not self.index_spec_.IsInitialized(debug_strs): initialized = 0
    for p in self.field_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_storage_ and not self.storage_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.index_spec_.ByteSize())
    n += 1 * len(self.field_)
    for i in xrange(len(self.field_)): n += self.lengthString(self.field_[i].ByteSize())
    if (self.has_storage_): n += 1 + self.lengthString(self.storage_.ByteSize())
    if (self.has_index_state_): n += 1 + self.lengthVarInt64(self.index_state_)
    if (self.has_index_delete_time_): n += 1 + self.lengthVarInt64(self.index_delete_time_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_index_spec_):
      n += 1
      n += self.lengthString(self.index_spec_.ByteSizePartial())
    n += 1 * len(self.field_)
    for i in xrange(len(self.field_)): n += self.lengthString(self.field_[i].ByteSizePartial())
    if (self.has_storage_): n += 1 + self.lengthString(self.storage_.ByteSizePartial())
    if (self.has_index_state_): n += 1 + self.lengthVarInt64(self.index_state_)
    if (self.has_index_delete_time_): n += 1 + self.lengthVarInt64(self.index_delete_time_)
    return n

  def Clear(self):
    self.clear_index_spec()
    self.clear_field()
    self.clear_storage()
    self.clear_index_state()
    self.clear_index_delete_time()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.index_spec_.ByteSize())
    self.index_spec_.OutputUnchecked(out)
    for i in xrange(len(self.field_)):
      out.putVarInt32(18)
      out.putVarInt32(self.field_[i].ByteSize())
      self.field_[i].OutputUnchecked(out)
    if (self.has_storage_):
      out.putVarInt32(26)
      out.putVarInt32(self.storage_.ByteSize())
      self.storage_.OutputUnchecked(out)
    if (self.has_index_state_):
      out.putVarInt32(32)
      out.putVarInt32(self.index_state_)
    if (self.has_index_delete_time_):
      out.putVarInt32(40)
      out.putVarInt64(self.index_delete_time_)

  def OutputPartial(self, out):
    if (self.has_index_spec_):
      out.putVarInt32(10)
      out.putVarInt32(self.index_spec_.ByteSizePartial())
      self.index_spec_.OutputPartial(out)
    for i in xrange(len(self.field_)):
      out.putVarInt32(18)
      out.putVarInt32(self.field_[i].ByteSizePartial())
      self.field_[i].OutputPartial(out)
    if (self.has_storage_):
      out.putVarInt32(26)
      out.putVarInt32(self.storage_.ByteSizePartial())
      self.storage_.OutputPartial(out)
    if (self.has_index_state_):
      out.putVarInt32(32)
      out.putVarInt32(self.index_state_)
    if (self.has_index_delete_time_):
      out.putVarInt32(40)
      out.putVarInt64(self.index_delete_time_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_index_spec().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_field().TryMerge(tmp)
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_storage().TryMerge(tmp)
        continue
      if tt == 32:
        self.set_index_state(d.getVarInt32())
        continue
      if tt == 40:
        self.set_index_delete_time(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_index_spec_:
      res+=prefix+"index_spec <\n"
      res+=self.index_spec_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.field_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("field%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_storage_:
      res+=prefix+"storage <\n"
      res+=self.storage_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_index_state_: res+=prefix+("index_state: %s\n" % self.DebugFormatInt32(self.index_state_))
    if self.has_index_delete_time_: res+=prefix+("index_delete_time: %s\n" % self.DebugFormatInt64(self.index_delete_time_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kindex_spec = 1
  kfield = 2
  kstorage = 3
  kindex_state = 4
  kindex_delete_time = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "index_spec",
    2: "field",
    3: "storage",
    4: "index_state",
    5: "index_delete_time",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.NUMERIC,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.IndexMetadata'
class IndexDocumentParams(ProtocolBuffer.ProtocolMessage):


  SYNCHRONOUSLY =    0
  WHEN_CONVENIENT =    1

  _Freshness_NAMES = {
    0: "SYNCHRONOUSLY",
    1: "WHEN_CONVENIENT",
  }

  def Freshness_Name(cls, x): return cls._Freshness_NAMES.get(x, "")
  Freshness_Name = classmethod(Freshness_Name)

  has_freshness_ = 0
  freshness_ = 0
  has_index_spec_ = 0

  def __init__(self, contents=None):
    self.document_ = []
    self.index_spec_ = IndexSpec()
    if contents is not None: self.MergeFromString(contents)

  def document_size(self): return len(self.document_)
  def document_list(self): return self.document_

  def document(self, i):
    return self.document_[i]

  def mutable_document(self, i):
    return self.document_[i]

  def add_document(self):
    x = Document()
    self.document_.append(x)
    return x

  def clear_document(self):
    self.document_ = []
  def freshness(self): return self.freshness_

  def set_freshness(self, x):
    self.has_freshness_ = 1
    self.freshness_ = x

  def clear_freshness(self):
    if self.has_freshness_:
      self.has_freshness_ = 0
      self.freshness_ = 0

  def has_freshness(self): return self.has_freshness_

  def index_spec(self): return self.index_spec_

  def mutable_index_spec(self): self.has_index_spec_ = 1; return self.index_spec_

  def clear_index_spec(self):self.has_index_spec_ = 0; self.index_spec_.Clear()

  def has_index_spec(self): return self.has_index_spec_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.document_size()): self.add_document().CopyFrom(x.document(i))
    if (x.has_freshness()): self.set_freshness(x.freshness())
    if (x.has_index_spec()): self.mutable_index_spec().MergeFrom(x.index_spec())

  def Equals(self, x):
    if x is self: return 1
    if len(self.document_) != len(x.document_): return 0
    for e1, e2 in zip(self.document_, x.document_):
      if e1 != e2: return 0
    if self.has_freshness_ != x.has_freshness_: return 0
    if self.has_freshness_ and self.freshness_ != x.freshness_: return 0
    if self.has_index_spec_ != x.has_index_spec_: return 0
    if self.has_index_spec_ and self.index_spec_ != x.index_spec_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.document_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (not self.has_index_spec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: index_spec not set.')
    elif not self.index_spec_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.document_)
    for i in xrange(len(self.document_)): n += self.lengthString(self.document_[i].ByteSize())
    if (self.has_freshness_): n += 1 + self.lengthVarInt64(self.freshness_)
    n += self.lengthString(self.index_spec_.ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.document_)
    for i in xrange(len(self.document_)): n += self.lengthString(self.document_[i].ByteSizePartial())
    if (self.has_freshness_): n += 1 + self.lengthVarInt64(self.freshness_)
    if (self.has_index_spec_):
      n += 1
      n += self.lengthString(self.index_spec_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_document()
    self.clear_freshness()
    self.clear_index_spec()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.document_)):
      out.putVarInt32(10)
      out.putVarInt32(self.document_[i].ByteSize())
      self.document_[i].OutputUnchecked(out)
    if (self.has_freshness_):
      out.putVarInt32(16)
      out.putVarInt32(self.freshness_)
    out.putVarInt32(26)
    out.putVarInt32(self.index_spec_.ByteSize())
    self.index_spec_.OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.document_)):
      out.putVarInt32(10)
      out.putVarInt32(self.document_[i].ByteSizePartial())
      self.document_[i].OutputPartial(out)
    if (self.has_freshness_):
      out.putVarInt32(16)
      out.putVarInt32(self.freshness_)
    if (self.has_index_spec_):
      out.putVarInt32(26)
      out.putVarInt32(self.index_spec_.ByteSizePartial())
      self.index_spec_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_document().TryMerge(tmp)
        continue
      if tt == 16:
        self.set_freshness(d.getVarInt32())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_index_spec().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.document_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("document%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_freshness_: res+=prefix+("freshness: %s\n" % self.DebugFormatInt32(self.freshness_))
    if self.has_index_spec_:
      res+=prefix+"index_spec <\n"
      res+=self.index_spec_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kdocument = 1
  kfreshness = 2
  kindex_spec = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "document",
    2: "freshness",
    3: "index_spec",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.IndexDocumentParams'
class IndexDocumentRequest(ProtocolBuffer.ProtocolMessage):
  has_params_ = 0
  has_app_id_ = 0
  app_id_ = ""

  def __init__(self, contents=None):
    self.params_ = IndexDocumentParams()
    if contents is not None: self.MergeFromString(contents)

  def params(self): return self.params_

  def mutable_params(self): self.has_params_ = 1; return self.params_

  def clear_params(self):self.has_params_ = 0; self.params_.Clear()

  def has_params(self): return self.has_params_

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
    if (x.has_params()): self.mutable_params().MergeFrom(x.params())
    if (x.has_app_id()): self.set_app_id(x.app_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_params_ != x.has_params_: return 0
    if self.has_params_ and self.params_ != x.params_: return 0
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_params_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: params not set.')
    elif not self.params_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.params_.ByteSize())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_params_):
      n += 1
      n += self.lengthString(self.params_.ByteSizePartial())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n

  def Clear(self):
    self.clear_params()
    self.clear_app_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.params_.ByteSize())
    self.params_.OutputUnchecked(out)
    if (self.has_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.app_id_)

  def OutputPartial(self, out):
    if (self.has_params_):
      out.putVarInt32(10)
      out.putVarInt32(self.params_.ByteSizePartial())
      self.params_.OutputPartial(out)
    if (self.has_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.app_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_params().TryMerge(tmp)
        continue
      if tt == 26:
        self.set_app_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_params_:
      res+=prefix+"params <\n"
      res+=self.params_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kparams = 1
  kapp_id = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "params",
    3: "app_id",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.IndexDocumentRequest'
class IndexDocumentResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.status_ = []
    self.doc_id_ = []
    if contents is not None: self.MergeFromString(contents)

  def status_size(self): return len(self.status_)
  def status_list(self): return self.status_

  def status(self, i):
    return self.status_[i]

  def mutable_status(self, i):
    return self.status_[i]

  def add_status(self):
    x = RequestStatus()
    self.status_.append(x)
    return x

  def clear_status(self):
    self.status_ = []
  def doc_id_size(self): return len(self.doc_id_)
  def doc_id_list(self): return self.doc_id_

  def doc_id(self, i):
    return self.doc_id_[i]

  def set_doc_id(self, i, x):
    self.doc_id_[i] = x

  def add_doc_id(self, x):
    self.doc_id_.append(x)

  def clear_doc_id(self):
    self.doc_id_ = []


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.status_size()): self.add_status().CopyFrom(x.status(i))
    for i in xrange(x.doc_id_size()): self.add_doc_id(x.doc_id(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.status_) != len(x.status_): return 0
    for e1, e2 in zip(self.status_, x.status_):
      if e1 != e2: return 0
    if len(self.doc_id_) != len(x.doc_id_): return 0
    for e1, e2 in zip(self.doc_id_, x.doc_id_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.status_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.status_)
    for i in xrange(len(self.status_)): n += self.lengthString(self.status_[i].ByteSize())
    n += 1 * len(self.doc_id_)
    for i in xrange(len(self.doc_id_)): n += self.lengthString(len(self.doc_id_[i]))
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.status_)
    for i in xrange(len(self.status_)): n += self.lengthString(self.status_[i].ByteSizePartial())
    n += 1 * len(self.doc_id_)
    for i in xrange(len(self.doc_id_)): n += self.lengthString(len(self.doc_id_[i]))
    return n

  def Clear(self):
    self.clear_status()
    self.clear_doc_id()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.status_)):
      out.putVarInt32(10)
      out.putVarInt32(self.status_[i].ByteSize())
      self.status_[i].OutputUnchecked(out)
    for i in xrange(len(self.doc_id_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.doc_id_[i])

  def OutputPartial(self, out):
    for i in xrange(len(self.status_)):
      out.putVarInt32(10)
      out.putVarInt32(self.status_[i].ByteSizePartial())
      self.status_[i].OutputPartial(out)
    for i in xrange(len(self.doc_id_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.doc_id_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_status().TryMerge(tmp)
        continue
      if tt == 18:
        self.add_doc_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.status_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("status%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.doc_id_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("doc_id%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kstatus = 1
  kdoc_id = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "status",
    2: "doc_id",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.IndexDocumentResponse'
class DeleteDocumentParams(ProtocolBuffer.ProtocolMessage):
  has_index_spec_ = 0

  def __init__(self, contents=None):
    self.doc_id_ = []
    self.index_spec_ = IndexSpec()
    if contents is not None: self.MergeFromString(contents)

  def doc_id_size(self): return len(self.doc_id_)
  def doc_id_list(self): return self.doc_id_

  def doc_id(self, i):
    return self.doc_id_[i]

  def set_doc_id(self, i, x):
    self.doc_id_[i] = x

  def add_doc_id(self, x):
    self.doc_id_.append(x)

  def clear_doc_id(self):
    self.doc_id_ = []

  def index_spec(self): return self.index_spec_

  def mutable_index_spec(self): self.has_index_spec_ = 1; return self.index_spec_

  def clear_index_spec(self):self.has_index_spec_ = 0; self.index_spec_.Clear()

  def has_index_spec(self): return self.has_index_spec_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.doc_id_size()): self.add_doc_id(x.doc_id(i))
    if (x.has_index_spec()): self.mutable_index_spec().MergeFrom(x.index_spec())

  def Equals(self, x):
    if x is self: return 1
    if len(self.doc_id_) != len(x.doc_id_): return 0
    for e1, e2 in zip(self.doc_id_, x.doc_id_):
      if e1 != e2: return 0
    if self.has_index_spec_ != x.has_index_spec_: return 0
    if self.has_index_spec_ and self.index_spec_ != x.index_spec_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_index_spec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: index_spec not set.')
    elif not self.index_spec_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.doc_id_)
    for i in xrange(len(self.doc_id_)): n += self.lengthString(len(self.doc_id_[i]))
    n += self.lengthString(self.index_spec_.ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.doc_id_)
    for i in xrange(len(self.doc_id_)): n += self.lengthString(len(self.doc_id_[i]))
    if (self.has_index_spec_):
      n += 1
      n += self.lengthString(self.index_spec_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_doc_id()
    self.clear_index_spec()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.doc_id_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.doc_id_[i])
    out.putVarInt32(18)
    out.putVarInt32(self.index_spec_.ByteSize())
    self.index_spec_.OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.doc_id_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.doc_id_[i])
    if (self.has_index_spec_):
      out.putVarInt32(18)
      out.putVarInt32(self.index_spec_.ByteSizePartial())
      self.index_spec_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.add_doc_id(d.getPrefixedString())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_index_spec().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.doc_id_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("doc_id%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_index_spec_:
      res+=prefix+"index_spec <\n"
      res+=self.index_spec_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kdoc_id = 1
  kindex_spec = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "doc_id",
    2: "index_spec",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.DeleteDocumentParams'
class DeleteDocumentRequest(ProtocolBuffer.ProtocolMessage):
  has_params_ = 0
  has_app_id_ = 0
  app_id_ = ""

  def __init__(self, contents=None):
    self.params_ = DeleteDocumentParams()
    if contents is not None: self.MergeFromString(contents)

  def params(self): return self.params_

  def mutable_params(self): self.has_params_ = 1; return self.params_

  def clear_params(self):self.has_params_ = 0; self.params_.Clear()

  def has_params(self): return self.has_params_

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
    if (x.has_params()): self.mutable_params().MergeFrom(x.params())
    if (x.has_app_id()): self.set_app_id(x.app_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_params_ != x.has_params_: return 0
    if self.has_params_ and self.params_ != x.params_: return 0
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_params_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: params not set.')
    elif not self.params_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.params_.ByteSize())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_params_):
      n += 1
      n += self.lengthString(self.params_.ByteSizePartial())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n

  def Clear(self):
    self.clear_params()
    self.clear_app_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.params_.ByteSize())
    self.params_.OutputUnchecked(out)
    if (self.has_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.app_id_)

  def OutputPartial(self, out):
    if (self.has_params_):
      out.putVarInt32(10)
      out.putVarInt32(self.params_.ByteSizePartial())
      self.params_.OutputPartial(out)
    if (self.has_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.app_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_params().TryMerge(tmp)
        continue
      if tt == 26:
        self.set_app_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_params_:
      res+=prefix+"params <\n"
      res+=self.params_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kparams = 1
  kapp_id = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "params",
    3: "app_id",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.DeleteDocumentRequest'
class DeleteDocumentResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.status_ = []
    if contents is not None: self.MergeFromString(contents)

  def status_size(self): return len(self.status_)
  def status_list(self): return self.status_

  def status(self, i):
    return self.status_[i]

  def mutable_status(self, i):
    return self.status_[i]

  def add_status(self):
    x = RequestStatus()
    self.status_.append(x)
    return x

  def clear_status(self):
    self.status_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.status_size()): self.add_status().CopyFrom(x.status(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.status_) != len(x.status_): return 0
    for e1, e2 in zip(self.status_, x.status_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.status_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.status_)
    for i in xrange(len(self.status_)): n += self.lengthString(self.status_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.status_)
    for i in xrange(len(self.status_)): n += self.lengthString(self.status_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_status()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.status_)):
      out.putVarInt32(10)
      out.putVarInt32(self.status_[i].ByteSize())
      self.status_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.status_)):
      out.putVarInt32(10)
      out.putVarInt32(self.status_[i].ByteSizePartial())
      self.status_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_status().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.status_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("status%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kstatus = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "status",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.DeleteDocumentResponse'
class ListDocumentsParams(ProtocolBuffer.ProtocolMessage):
  has_index_spec_ = 0
  has_start_doc_id_ = 0
  start_doc_id_ = ""
  has_include_start_doc_ = 0
  include_start_doc_ = 1
  has_limit_ = 0
  limit_ = 100
  has_keys_only_ = 0
  keys_only_ = 0

  def __init__(self, contents=None):
    self.index_spec_ = IndexSpec()
    if contents is not None: self.MergeFromString(contents)

  def index_spec(self): return self.index_spec_

  def mutable_index_spec(self): self.has_index_spec_ = 1; return self.index_spec_

  def clear_index_spec(self):self.has_index_spec_ = 0; self.index_spec_.Clear()

  def has_index_spec(self): return self.has_index_spec_

  def start_doc_id(self): return self.start_doc_id_

  def set_start_doc_id(self, x):
    self.has_start_doc_id_ = 1
    self.start_doc_id_ = x

  def clear_start_doc_id(self):
    if self.has_start_doc_id_:
      self.has_start_doc_id_ = 0
      self.start_doc_id_ = ""

  def has_start_doc_id(self): return self.has_start_doc_id_

  def include_start_doc(self): return self.include_start_doc_

  def set_include_start_doc(self, x):
    self.has_include_start_doc_ = 1
    self.include_start_doc_ = x

  def clear_include_start_doc(self):
    if self.has_include_start_doc_:
      self.has_include_start_doc_ = 0
      self.include_start_doc_ = 1

  def has_include_start_doc(self): return self.has_include_start_doc_

  def limit(self): return self.limit_

  def set_limit(self, x):
    self.has_limit_ = 1
    self.limit_ = x

  def clear_limit(self):
    if self.has_limit_:
      self.has_limit_ = 0
      self.limit_ = 100

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


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_index_spec()): self.mutable_index_spec().MergeFrom(x.index_spec())
    if (x.has_start_doc_id()): self.set_start_doc_id(x.start_doc_id())
    if (x.has_include_start_doc()): self.set_include_start_doc(x.include_start_doc())
    if (x.has_limit()): self.set_limit(x.limit())
    if (x.has_keys_only()): self.set_keys_only(x.keys_only())

  def Equals(self, x):
    if x is self: return 1
    if self.has_index_spec_ != x.has_index_spec_: return 0
    if self.has_index_spec_ and self.index_spec_ != x.index_spec_: return 0
    if self.has_start_doc_id_ != x.has_start_doc_id_: return 0
    if self.has_start_doc_id_ and self.start_doc_id_ != x.start_doc_id_: return 0
    if self.has_include_start_doc_ != x.has_include_start_doc_: return 0
    if self.has_include_start_doc_ and self.include_start_doc_ != x.include_start_doc_: return 0
    if self.has_limit_ != x.has_limit_: return 0
    if self.has_limit_ and self.limit_ != x.limit_: return 0
    if self.has_keys_only_ != x.has_keys_only_: return 0
    if self.has_keys_only_ and self.keys_only_ != x.keys_only_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_index_spec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: index_spec not set.')
    elif not self.index_spec_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.index_spec_.ByteSize())
    if (self.has_start_doc_id_): n += 1 + self.lengthString(len(self.start_doc_id_))
    if (self.has_include_start_doc_): n += 2
    if (self.has_limit_): n += 1 + self.lengthVarInt64(self.limit_)
    if (self.has_keys_only_): n += 2
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_index_spec_):
      n += 1
      n += self.lengthString(self.index_spec_.ByteSizePartial())
    if (self.has_start_doc_id_): n += 1 + self.lengthString(len(self.start_doc_id_))
    if (self.has_include_start_doc_): n += 2
    if (self.has_limit_): n += 1 + self.lengthVarInt64(self.limit_)
    if (self.has_keys_only_): n += 2
    return n

  def Clear(self):
    self.clear_index_spec()
    self.clear_start_doc_id()
    self.clear_include_start_doc()
    self.clear_limit()
    self.clear_keys_only()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.index_spec_.ByteSize())
    self.index_spec_.OutputUnchecked(out)
    if (self.has_start_doc_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.start_doc_id_)
    if (self.has_include_start_doc_):
      out.putVarInt32(24)
      out.putBoolean(self.include_start_doc_)
    if (self.has_limit_):
      out.putVarInt32(32)
      out.putVarInt32(self.limit_)
    if (self.has_keys_only_):
      out.putVarInt32(40)
      out.putBoolean(self.keys_only_)

  def OutputPartial(self, out):
    if (self.has_index_spec_):
      out.putVarInt32(10)
      out.putVarInt32(self.index_spec_.ByteSizePartial())
      self.index_spec_.OutputPartial(out)
    if (self.has_start_doc_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.start_doc_id_)
    if (self.has_include_start_doc_):
      out.putVarInt32(24)
      out.putBoolean(self.include_start_doc_)
    if (self.has_limit_):
      out.putVarInt32(32)
      out.putVarInt32(self.limit_)
    if (self.has_keys_only_):
      out.putVarInt32(40)
      out.putBoolean(self.keys_only_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_index_spec().TryMerge(tmp)
        continue
      if tt == 18:
        self.set_start_doc_id(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_include_start_doc(d.getBoolean())
        continue
      if tt == 32:
        self.set_limit(d.getVarInt32())
        continue
      if tt == 40:
        self.set_keys_only(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_index_spec_:
      res+=prefix+"index_spec <\n"
      res+=self.index_spec_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_start_doc_id_: res+=prefix+("start_doc_id: %s\n" % self.DebugFormatString(self.start_doc_id_))
    if self.has_include_start_doc_: res+=prefix+("include_start_doc: %s\n" % self.DebugFormatBool(self.include_start_doc_))
    if self.has_limit_: res+=prefix+("limit: %s\n" % self.DebugFormatInt32(self.limit_))
    if self.has_keys_only_: res+=prefix+("keys_only: %s\n" % self.DebugFormatBool(self.keys_only_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kindex_spec = 1
  kstart_doc_id = 2
  kinclude_start_doc = 3
  klimit = 4
  kkeys_only = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "index_spec",
    2: "start_doc_id",
    3: "include_start_doc",
    4: "limit",
    5: "keys_only",
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ListDocumentsParams'
class ListDocumentsRequest(ProtocolBuffer.ProtocolMessage):
  has_params_ = 0
  has_app_id_ = 0
  app_id_ = ""

  def __init__(self, contents=None):
    self.params_ = ListDocumentsParams()
    if contents is not None: self.MergeFromString(contents)

  def params(self): return self.params_

  def mutable_params(self): self.has_params_ = 1; return self.params_

  def clear_params(self):self.has_params_ = 0; self.params_.Clear()

  def has_params(self): return self.has_params_

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
    if (x.has_params()): self.mutable_params().MergeFrom(x.params())
    if (x.has_app_id()): self.set_app_id(x.app_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_params_ != x.has_params_: return 0
    if self.has_params_ and self.params_ != x.params_: return 0
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_params_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: params not set.')
    elif not self.params_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.params_.ByteSize())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_params_):
      n += 1
      n += self.lengthString(self.params_.ByteSizePartial())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n

  def Clear(self):
    self.clear_params()
    self.clear_app_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.params_.ByteSize())
    self.params_.OutputUnchecked(out)
    if (self.has_app_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.app_id_)

  def OutputPartial(self, out):
    if (self.has_params_):
      out.putVarInt32(10)
      out.putVarInt32(self.params_.ByteSizePartial())
      self.params_.OutputPartial(out)
    if (self.has_app_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.app_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_params().TryMerge(tmp)
        continue
      if tt == 18:
        self.set_app_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_params_:
      res+=prefix+"params <\n"
      res+=self.params_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kparams = 1
  kapp_id = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "params",
    2: "app_id",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ListDocumentsRequest'
class ListDocumentsResponse(ProtocolBuffer.ProtocolMessage):
  has_status_ = 0

  def __init__(self, contents=None):
    self.status_ = RequestStatus()
    self.document_ = []
    if contents is not None: self.MergeFromString(contents)

  def status(self): return self.status_

  def mutable_status(self): self.has_status_ = 1; return self.status_

  def clear_status(self):self.has_status_ = 0; self.status_.Clear()

  def has_status(self): return self.has_status_

  def document_size(self): return len(self.document_)
  def document_list(self): return self.document_

  def document(self, i):
    return self.document_[i]

  def mutable_document(self, i):
    return self.document_[i]

  def add_document(self):
    x = Document()
    self.document_.append(x)
    return x

  def clear_document(self):
    self.document_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_status()): self.mutable_status().MergeFrom(x.status())
    for i in xrange(x.document_size()): self.add_document().CopyFrom(x.document(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_status_ != x.has_status_: return 0
    if self.has_status_ and self.status_ != x.status_: return 0
    if len(self.document_) != len(x.document_): return 0
    for e1, e2 in zip(self.document_, x.document_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_status_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: status not set.')
    elif not self.status_.IsInitialized(debug_strs): initialized = 0
    for p in self.document_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.status_.ByteSize())
    n += 1 * len(self.document_)
    for i in xrange(len(self.document_)): n += self.lengthString(self.document_[i].ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_status_):
      n += 1
      n += self.lengthString(self.status_.ByteSizePartial())
    n += 1 * len(self.document_)
    for i in xrange(len(self.document_)): n += self.lengthString(self.document_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_status()
    self.clear_document()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.status_.ByteSize())
    self.status_.OutputUnchecked(out)
    for i in xrange(len(self.document_)):
      out.putVarInt32(18)
      out.putVarInt32(self.document_[i].ByteSize())
      self.document_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_status_):
      out.putVarInt32(10)
      out.putVarInt32(self.status_.ByteSizePartial())
      self.status_.OutputPartial(out)
    for i in xrange(len(self.document_)):
      out.putVarInt32(18)
      out.putVarInt32(self.document_[i].ByteSizePartial())
      self.document_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_status().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_document().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_status_:
      res+=prefix+"status <\n"
      res+=self.status_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.document_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("document%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kstatus = 1
  kdocument = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "status",
    2: "document",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ListDocumentsResponse'
class DeleteIndexParams(ProtocolBuffer.ProtocolMessage):
  has_index_spec_ = 0

  def __init__(self, contents=None):
    self.index_spec_ = IndexSpec()
    if contents is not None: self.MergeFromString(contents)

  def index_spec(self): return self.index_spec_

  def mutable_index_spec(self): self.has_index_spec_ = 1; return self.index_spec_

  def clear_index_spec(self):self.has_index_spec_ = 0; self.index_spec_.Clear()

  def has_index_spec(self): return self.has_index_spec_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_index_spec()): self.mutable_index_spec().MergeFrom(x.index_spec())

  def Equals(self, x):
    if x is self: return 1
    if self.has_index_spec_ != x.has_index_spec_: return 0
    if self.has_index_spec_ and self.index_spec_ != x.index_spec_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_index_spec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: index_spec not set.')
    elif not self.index_spec_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.index_spec_.ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_index_spec_):
      n += 1
      n += self.lengthString(self.index_spec_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_index_spec()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.index_spec_.ByteSize())
    self.index_spec_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_index_spec_):
      out.putVarInt32(10)
      out.putVarInt32(self.index_spec_.ByteSizePartial())
      self.index_spec_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_index_spec().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_index_spec_:
      res+=prefix+"index_spec <\n"
      res+=self.index_spec_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kindex_spec = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "index_spec",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.DeleteIndexParams'
class DeleteIndexRequest(ProtocolBuffer.ProtocolMessage):
  has_params_ = 0
  has_app_id_ = 0
  app_id_ = ""

  def __init__(self, contents=None):
    self.params_ = DeleteIndexParams()
    if contents is not None: self.MergeFromString(contents)

  def params(self): return self.params_

  def mutable_params(self): self.has_params_ = 1; return self.params_

  def clear_params(self):self.has_params_ = 0; self.params_.Clear()

  def has_params(self): return self.has_params_

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
    if (x.has_params()): self.mutable_params().MergeFrom(x.params())
    if (x.has_app_id()): self.set_app_id(x.app_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_params_ != x.has_params_: return 0
    if self.has_params_ and self.params_ != x.params_: return 0
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_params_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: params not set.')
    elif not self.params_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.params_.ByteSize())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_params_):
      n += 1
      n += self.lengthString(self.params_.ByteSizePartial())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n

  def Clear(self):
    self.clear_params()
    self.clear_app_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.params_.ByteSize())
    self.params_.OutputUnchecked(out)
    if (self.has_app_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.app_id_)

  def OutputPartial(self, out):
    if (self.has_params_):
      out.putVarInt32(10)
      out.putVarInt32(self.params_.ByteSizePartial())
      self.params_.OutputPartial(out)
    if (self.has_app_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.app_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_params().TryMerge(tmp)
        continue
      if tt == 18:
        self.set_app_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_params_:
      res+=prefix+"params <\n"
      res+=self.params_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kparams = 1
  kapp_id = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "params",
    2: "app_id",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.DeleteIndexRequest'
class DeleteIndexResponse(ProtocolBuffer.ProtocolMessage):
  has_status_ = 0

  def __init__(self, contents=None):
    self.status_ = RequestStatus()
    if contents is not None: self.MergeFromString(contents)

  def status(self): return self.status_

  def mutable_status(self): self.has_status_ = 1; return self.status_

  def clear_status(self):self.has_status_ = 0; self.status_.Clear()

  def has_status(self): return self.has_status_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_status()): self.mutable_status().MergeFrom(x.status())

  def Equals(self, x):
    if x is self: return 1
    if self.has_status_ != x.has_status_: return 0
    if self.has_status_ and self.status_ != x.status_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_status_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: status not set.')
    elif not self.status_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.status_.ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_status_):
      n += 1
      n += self.lengthString(self.status_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_status()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.status_.ByteSize())
    self.status_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_status_):
      out.putVarInt32(10)
      out.putVarInt32(self.status_.ByteSizePartial())
      self.status_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_status().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_status_:
      res+=prefix+"status <\n"
      res+=self.status_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kstatus = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "status",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.DeleteIndexResponse'
class CancelDeleteIndexParams(ProtocolBuffer.ProtocolMessage):
  has_index_spec_ = 0

  def __init__(self, contents=None):
    self.index_spec_ = IndexSpec()
    if contents is not None: self.MergeFromString(contents)

  def index_spec(self): return self.index_spec_

  def mutable_index_spec(self): self.has_index_spec_ = 1; return self.index_spec_

  def clear_index_spec(self):self.has_index_spec_ = 0; self.index_spec_.Clear()

  def has_index_spec(self): return self.has_index_spec_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_index_spec()): self.mutable_index_spec().MergeFrom(x.index_spec())

  def Equals(self, x):
    if x is self: return 1
    if self.has_index_spec_ != x.has_index_spec_: return 0
    if self.has_index_spec_ and self.index_spec_ != x.index_spec_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_index_spec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: index_spec not set.')
    elif not self.index_spec_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.index_spec_.ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_index_spec_):
      n += 1
      n += self.lengthString(self.index_spec_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_index_spec()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.index_spec_.ByteSize())
    self.index_spec_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_index_spec_):
      out.putVarInt32(10)
      out.putVarInt32(self.index_spec_.ByteSizePartial())
      self.index_spec_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_index_spec().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_index_spec_:
      res+=prefix+"index_spec <\n"
      res+=self.index_spec_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kindex_spec = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "index_spec",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CancelDeleteIndexParams'
class CancelDeleteIndexRequest(ProtocolBuffer.ProtocolMessage):
  has_params_ = 0
  has_app_id_ = 0
  app_id_ = ""

  def __init__(self, contents=None):
    self.params_ = CancelDeleteIndexParams()
    if contents is not None: self.MergeFromString(contents)

  def params(self): return self.params_

  def mutable_params(self): self.has_params_ = 1; return self.params_

  def clear_params(self):self.has_params_ = 0; self.params_.Clear()

  def has_params(self): return self.has_params_

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
    if (x.has_params()): self.mutable_params().MergeFrom(x.params())
    if (x.has_app_id()): self.set_app_id(x.app_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_params_ != x.has_params_: return 0
    if self.has_params_ and self.params_ != x.params_: return 0
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_params_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: params not set.')
    elif not self.params_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.params_.ByteSize())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_params_):
      n += 1
      n += self.lengthString(self.params_.ByteSizePartial())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n

  def Clear(self):
    self.clear_params()
    self.clear_app_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.params_.ByteSize())
    self.params_.OutputUnchecked(out)
    if (self.has_app_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.app_id_)

  def OutputPartial(self, out):
    if (self.has_params_):
      out.putVarInt32(10)
      out.putVarInt32(self.params_.ByteSizePartial())
      self.params_.OutputPartial(out)
    if (self.has_app_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.app_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_params().TryMerge(tmp)
        continue
      if tt == 18:
        self.set_app_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_params_:
      res+=prefix+"params <\n"
      res+=self.params_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kparams = 1
  kapp_id = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "params",
    2: "app_id",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CancelDeleteIndexRequest'
class CancelDeleteIndexResponse(ProtocolBuffer.ProtocolMessage):
  has_status_ = 0

  def __init__(self, contents=None):
    self.status_ = RequestStatus()
    if contents is not None: self.MergeFromString(contents)

  def status(self): return self.status_

  def mutable_status(self): self.has_status_ = 1; return self.status_

  def clear_status(self):self.has_status_ = 0; self.status_.Clear()

  def has_status(self): return self.has_status_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_status()): self.mutable_status().MergeFrom(x.status())

  def Equals(self, x):
    if x is self: return 1
    if self.has_status_ != x.has_status_: return 0
    if self.has_status_ and self.status_ != x.status_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_status_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: status not set.')
    elif not self.status_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.status_.ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_status_):
      n += 1
      n += self.lengthString(self.status_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_status()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.status_.ByteSize())
    self.status_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_status_):
      out.putVarInt32(10)
      out.putVarInt32(self.status_.ByteSizePartial())
      self.status_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_status().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_status_:
      res+=prefix+"status <\n"
      res+=self.status_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kstatus = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "status",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CancelDeleteIndexResponse'
class ListIndexesParams(ProtocolBuffer.ProtocolMessage):
  has_fetch_schema_ = 0
  fetch_schema_ = 0
  has_limit_ = 0
  limit_ = 20
  has_namespace_ = 0
  namespace_ = ""
  has_start_index_name_ = 0
  start_index_name_ = ""
  has_include_start_index_ = 0
  include_start_index_ = 1
  has_index_name_prefix_ = 0
  index_name_prefix_ = ""
  has_offset_ = 0
  offset_ = 0
  has_source_ = 0
  source_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def fetch_schema(self): return self.fetch_schema_

  def set_fetch_schema(self, x):
    self.has_fetch_schema_ = 1
    self.fetch_schema_ = x

  def clear_fetch_schema(self):
    if self.has_fetch_schema_:
      self.has_fetch_schema_ = 0
      self.fetch_schema_ = 0

  def has_fetch_schema(self): return self.has_fetch_schema_

  def limit(self): return self.limit_

  def set_limit(self, x):
    self.has_limit_ = 1
    self.limit_ = x

  def clear_limit(self):
    if self.has_limit_:
      self.has_limit_ = 0
      self.limit_ = 20

  def has_limit(self): return self.has_limit_

  def namespace(self): return self.namespace_

  def set_namespace(self, x):
    self.has_namespace_ = 1
    self.namespace_ = x

  def clear_namespace(self):
    if self.has_namespace_:
      self.has_namespace_ = 0
      self.namespace_ = ""

  def has_namespace(self): return self.has_namespace_

  def start_index_name(self): return self.start_index_name_

  def set_start_index_name(self, x):
    self.has_start_index_name_ = 1
    self.start_index_name_ = x

  def clear_start_index_name(self):
    if self.has_start_index_name_:
      self.has_start_index_name_ = 0
      self.start_index_name_ = ""

  def has_start_index_name(self): return self.has_start_index_name_

  def include_start_index(self): return self.include_start_index_

  def set_include_start_index(self, x):
    self.has_include_start_index_ = 1
    self.include_start_index_ = x

  def clear_include_start_index(self):
    if self.has_include_start_index_:
      self.has_include_start_index_ = 0
      self.include_start_index_ = 1

  def has_include_start_index(self): return self.has_include_start_index_

  def index_name_prefix(self): return self.index_name_prefix_

  def set_index_name_prefix(self, x):
    self.has_index_name_prefix_ = 1
    self.index_name_prefix_ = x

  def clear_index_name_prefix(self):
    if self.has_index_name_prefix_:
      self.has_index_name_prefix_ = 0
      self.index_name_prefix_ = ""

  def has_index_name_prefix(self): return self.has_index_name_prefix_

  def offset(self): return self.offset_

  def set_offset(self, x):
    self.has_offset_ = 1
    self.offset_ = x

  def clear_offset(self):
    if self.has_offset_:
      self.has_offset_ = 0
      self.offset_ = 0

  def has_offset(self): return self.has_offset_

  def source(self): return self.source_

  def set_source(self, x):
    self.has_source_ = 1
    self.source_ = x

  def clear_source(self):
    if self.has_source_:
      self.has_source_ = 0
      self.source_ = 0

  def has_source(self): return self.has_source_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_fetch_schema()): self.set_fetch_schema(x.fetch_schema())
    if (x.has_limit()): self.set_limit(x.limit())
    if (x.has_namespace()): self.set_namespace(x.namespace())
    if (x.has_start_index_name()): self.set_start_index_name(x.start_index_name())
    if (x.has_include_start_index()): self.set_include_start_index(x.include_start_index())
    if (x.has_index_name_prefix()): self.set_index_name_prefix(x.index_name_prefix())
    if (x.has_offset()): self.set_offset(x.offset())
    if (x.has_source()): self.set_source(x.source())

  def Equals(self, x):
    if x is self: return 1
    if self.has_fetch_schema_ != x.has_fetch_schema_: return 0
    if self.has_fetch_schema_ and self.fetch_schema_ != x.fetch_schema_: return 0
    if self.has_limit_ != x.has_limit_: return 0
    if self.has_limit_ and self.limit_ != x.limit_: return 0
    if self.has_namespace_ != x.has_namespace_: return 0
    if self.has_namespace_ and self.namespace_ != x.namespace_: return 0
    if self.has_start_index_name_ != x.has_start_index_name_: return 0
    if self.has_start_index_name_ and self.start_index_name_ != x.start_index_name_: return 0
    if self.has_include_start_index_ != x.has_include_start_index_: return 0
    if self.has_include_start_index_ and self.include_start_index_ != x.include_start_index_: return 0
    if self.has_index_name_prefix_ != x.has_index_name_prefix_: return 0
    if self.has_index_name_prefix_ and self.index_name_prefix_ != x.index_name_prefix_: return 0
    if self.has_offset_ != x.has_offset_: return 0
    if self.has_offset_ and self.offset_ != x.offset_: return 0
    if self.has_source_ != x.has_source_: return 0
    if self.has_source_ and self.source_ != x.source_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_fetch_schema_): n += 2
    if (self.has_limit_): n += 1 + self.lengthVarInt64(self.limit_)
    if (self.has_namespace_): n += 1 + self.lengthString(len(self.namespace_))
    if (self.has_start_index_name_): n += 1 + self.lengthString(len(self.start_index_name_))
    if (self.has_include_start_index_): n += 2
    if (self.has_index_name_prefix_): n += 1 + self.lengthString(len(self.index_name_prefix_))
    if (self.has_offset_): n += 1 + self.lengthVarInt64(self.offset_)
    if (self.has_source_): n += 1 + self.lengthVarInt64(self.source_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_fetch_schema_): n += 2
    if (self.has_limit_): n += 1 + self.lengthVarInt64(self.limit_)
    if (self.has_namespace_): n += 1 + self.lengthString(len(self.namespace_))
    if (self.has_start_index_name_): n += 1 + self.lengthString(len(self.start_index_name_))
    if (self.has_include_start_index_): n += 2
    if (self.has_index_name_prefix_): n += 1 + self.lengthString(len(self.index_name_prefix_))
    if (self.has_offset_): n += 1 + self.lengthVarInt64(self.offset_)
    if (self.has_source_): n += 1 + self.lengthVarInt64(self.source_)
    return n

  def Clear(self):
    self.clear_fetch_schema()
    self.clear_limit()
    self.clear_namespace()
    self.clear_start_index_name()
    self.clear_include_start_index()
    self.clear_index_name_prefix()
    self.clear_offset()
    self.clear_source()

  def OutputUnchecked(self, out):
    if (self.has_fetch_schema_):
      out.putVarInt32(8)
      out.putBoolean(self.fetch_schema_)
    if (self.has_limit_):
      out.putVarInt32(16)
      out.putVarInt32(self.limit_)
    if (self.has_namespace_):
      out.putVarInt32(26)
      out.putPrefixedString(self.namespace_)
    if (self.has_start_index_name_):
      out.putVarInt32(34)
      out.putPrefixedString(self.start_index_name_)
    if (self.has_include_start_index_):
      out.putVarInt32(40)
      out.putBoolean(self.include_start_index_)
    if (self.has_index_name_prefix_):
      out.putVarInt32(50)
      out.putPrefixedString(self.index_name_prefix_)
    if (self.has_offset_):
      out.putVarInt32(56)
      out.putVarInt32(self.offset_)
    if (self.has_source_):
      out.putVarInt32(64)
      out.putVarInt32(self.source_)

  def OutputPartial(self, out):
    if (self.has_fetch_schema_):
      out.putVarInt32(8)
      out.putBoolean(self.fetch_schema_)
    if (self.has_limit_):
      out.putVarInt32(16)
      out.putVarInt32(self.limit_)
    if (self.has_namespace_):
      out.putVarInt32(26)
      out.putPrefixedString(self.namespace_)
    if (self.has_start_index_name_):
      out.putVarInt32(34)
      out.putPrefixedString(self.start_index_name_)
    if (self.has_include_start_index_):
      out.putVarInt32(40)
      out.putBoolean(self.include_start_index_)
    if (self.has_index_name_prefix_):
      out.putVarInt32(50)
      out.putPrefixedString(self.index_name_prefix_)
    if (self.has_offset_):
      out.putVarInt32(56)
      out.putVarInt32(self.offset_)
    if (self.has_source_):
      out.putVarInt32(64)
      out.putVarInt32(self.source_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_fetch_schema(d.getBoolean())
        continue
      if tt == 16:
        self.set_limit(d.getVarInt32())
        continue
      if tt == 26:
        self.set_namespace(d.getPrefixedString())
        continue
      if tt == 34:
        self.set_start_index_name(d.getPrefixedString())
        continue
      if tt == 40:
        self.set_include_start_index(d.getBoolean())
        continue
      if tt == 50:
        self.set_index_name_prefix(d.getPrefixedString())
        continue
      if tt == 56:
        self.set_offset(d.getVarInt32())
        continue
      if tt == 64:
        self.set_source(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_fetch_schema_: res+=prefix+("fetch_schema: %s\n" % self.DebugFormatBool(self.fetch_schema_))
    if self.has_limit_: res+=prefix+("limit: %s\n" % self.DebugFormatInt32(self.limit_))
    if self.has_namespace_: res+=prefix+("namespace: %s\n" % self.DebugFormatString(self.namespace_))
    if self.has_start_index_name_: res+=prefix+("start_index_name: %s\n" % self.DebugFormatString(self.start_index_name_))
    if self.has_include_start_index_: res+=prefix+("include_start_index: %s\n" % self.DebugFormatBool(self.include_start_index_))
    if self.has_index_name_prefix_: res+=prefix+("index_name_prefix: %s\n" % self.DebugFormatString(self.index_name_prefix_))
    if self.has_offset_: res+=prefix+("offset: %s\n" % self.DebugFormatInt32(self.offset_))
    if self.has_source_: res+=prefix+("source: %s\n" % self.DebugFormatInt32(self.source_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kfetch_schema = 1
  klimit = 2
  knamespace = 3
  kstart_index_name = 4
  kinclude_start_index = 5
  kindex_name_prefix = 6
  koffset = 7
  ksource = 8

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "fetch_schema",
    2: "limit",
    3: "namespace",
    4: "start_index_name",
    5: "include_start_index",
    6: "index_name_prefix",
    7: "offset",
    8: "source",
  }, 8)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.STRING,
    7: ProtocolBuffer.Encoder.NUMERIC,
    8: ProtocolBuffer.Encoder.NUMERIC,
  }, 8, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ListIndexesParams'
class ListIndexesRequest(ProtocolBuffer.ProtocolMessage):
  has_params_ = 0
  has_app_id_ = 0
  app_id_ = ""

  def __init__(self, contents=None):
    self.params_ = ListIndexesParams()
    if contents is not None: self.MergeFromString(contents)

  def params(self): return self.params_

  def mutable_params(self): self.has_params_ = 1; return self.params_

  def clear_params(self):self.has_params_ = 0; self.params_.Clear()

  def has_params(self): return self.has_params_

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
    if (x.has_params()): self.mutable_params().MergeFrom(x.params())
    if (x.has_app_id()): self.set_app_id(x.app_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_params_ != x.has_params_: return 0
    if self.has_params_ and self.params_ != x.params_: return 0
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_params_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: params not set.')
    elif not self.params_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.params_.ByteSize())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_params_):
      n += 1
      n += self.lengthString(self.params_.ByteSizePartial())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n

  def Clear(self):
    self.clear_params()
    self.clear_app_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.params_.ByteSize())
    self.params_.OutputUnchecked(out)
    if (self.has_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.app_id_)

  def OutputPartial(self, out):
    if (self.has_params_):
      out.putVarInt32(10)
      out.putVarInt32(self.params_.ByteSizePartial())
      self.params_.OutputPartial(out)
    if (self.has_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.app_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_params().TryMerge(tmp)
        continue
      if tt == 26:
        self.set_app_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_params_:
      res+=prefix+"params <\n"
      res+=self.params_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kparams = 1
  kapp_id = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "params",
    3: "app_id",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ListIndexesRequest'
class ListIndexesResponse(ProtocolBuffer.ProtocolMessage):
  has_status_ = 0

  def __init__(self, contents=None):
    self.status_ = RequestStatus()
    self.index_metadata_ = []
    if contents is not None: self.MergeFromString(contents)

  def status(self): return self.status_

  def mutable_status(self): self.has_status_ = 1; return self.status_

  def clear_status(self):self.has_status_ = 0; self.status_.Clear()

  def has_status(self): return self.has_status_

  def index_metadata_size(self): return len(self.index_metadata_)
  def index_metadata_list(self): return self.index_metadata_

  def index_metadata(self, i):
    return self.index_metadata_[i]

  def mutable_index_metadata(self, i):
    return self.index_metadata_[i]

  def add_index_metadata(self):
    x = IndexMetadata()
    self.index_metadata_.append(x)
    return x

  def clear_index_metadata(self):
    self.index_metadata_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_status()): self.mutable_status().MergeFrom(x.status())
    for i in xrange(x.index_metadata_size()): self.add_index_metadata().CopyFrom(x.index_metadata(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_status_ != x.has_status_: return 0
    if self.has_status_ and self.status_ != x.status_: return 0
    if len(self.index_metadata_) != len(x.index_metadata_): return 0
    for e1, e2 in zip(self.index_metadata_, x.index_metadata_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_status_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: status not set.')
    elif not self.status_.IsInitialized(debug_strs): initialized = 0
    for p in self.index_metadata_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.status_.ByteSize())
    n += 1 * len(self.index_metadata_)
    for i in xrange(len(self.index_metadata_)): n += self.lengthString(self.index_metadata_[i].ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_status_):
      n += 1
      n += self.lengthString(self.status_.ByteSizePartial())
    n += 1 * len(self.index_metadata_)
    for i in xrange(len(self.index_metadata_)): n += self.lengthString(self.index_metadata_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_status()
    self.clear_index_metadata()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.status_.ByteSize())
    self.status_.OutputUnchecked(out)
    for i in xrange(len(self.index_metadata_)):
      out.putVarInt32(18)
      out.putVarInt32(self.index_metadata_[i].ByteSize())
      self.index_metadata_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_status_):
      out.putVarInt32(10)
      out.putVarInt32(self.status_.ByteSizePartial())
      self.status_.OutputPartial(out)
    for i in xrange(len(self.index_metadata_)):
      out.putVarInt32(18)
      out.putVarInt32(self.index_metadata_[i].ByteSizePartial())
      self.index_metadata_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_status().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_index_metadata().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_status_:
      res+=prefix+"status <\n"
      res+=self.status_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.index_metadata_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("index_metadata%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kstatus = 1
  kindex_metadata = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "status",
    2: "index_metadata",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ListIndexesResponse'
class DeleteSchemaParams(ProtocolBuffer.ProtocolMessage):
  has_source_ = 0
  source_ = 0

  def __init__(self, contents=None):
    self.index_spec_ = []
    if contents is not None: self.MergeFromString(contents)

  def source(self): return self.source_

  def set_source(self, x):
    self.has_source_ = 1
    self.source_ = x

  def clear_source(self):
    if self.has_source_:
      self.has_source_ = 0
      self.source_ = 0

  def has_source(self): return self.has_source_

  def index_spec_size(self): return len(self.index_spec_)
  def index_spec_list(self): return self.index_spec_

  def index_spec(self, i):
    return self.index_spec_[i]

  def mutable_index_spec(self, i):
    return self.index_spec_[i]

  def add_index_spec(self):
    x = IndexSpec()
    self.index_spec_.append(x)
    return x

  def clear_index_spec(self):
    self.index_spec_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_source()): self.set_source(x.source())
    for i in xrange(x.index_spec_size()): self.add_index_spec().CopyFrom(x.index_spec(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_source_ != x.has_source_: return 0
    if self.has_source_ and self.source_ != x.source_: return 0
    if len(self.index_spec_) != len(x.index_spec_): return 0
    for e1, e2 in zip(self.index_spec_, x.index_spec_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.index_spec_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_source_): n += 1 + self.lengthVarInt64(self.source_)
    n += 1 * len(self.index_spec_)
    for i in xrange(len(self.index_spec_)): n += self.lengthString(self.index_spec_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_source_): n += 1 + self.lengthVarInt64(self.source_)
    n += 1 * len(self.index_spec_)
    for i in xrange(len(self.index_spec_)): n += self.lengthString(self.index_spec_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_source()
    self.clear_index_spec()

  def OutputUnchecked(self, out):
    if (self.has_source_):
      out.putVarInt32(8)
      out.putVarInt32(self.source_)
    for i in xrange(len(self.index_spec_)):
      out.putVarInt32(18)
      out.putVarInt32(self.index_spec_[i].ByteSize())
      self.index_spec_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_source_):
      out.putVarInt32(8)
      out.putVarInt32(self.source_)
    for i in xrange(len(self.index_spec_)):
      out.putVarInt32(18)
      out.putVarInt32(self.index_spec_[i].ByteSizePartial())
      self.index_spec_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_source(d.getVarInt32())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_index_spec().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_source_: res+=prefix+("source: %s\n" % self.DebugFormatInt32(self.source_))
    cnt=0
    for e in self.index_spec_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("index_spec%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksource = 1
  kindex_spec = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "source",
    2: "index_spec",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.DeleteSchemaParams'
class DeleteSchemaRequest(ProtocolBuffer.ProtocolMessage):
  has_params_ = 0
  has_app_id_ = 0
  app_id_ = ""

  def __init__(self, contents=None):
    self.params_ = DeleteSchemaParams()
    if contents is not None: self.MergeFromString(contents)

  def params(self): return self.params_

  def mutable_params(self): self.has_params_ = 1; return self.params_

  def clear_params(self):self.has_params_ = 0; self.params_.Clear()

  def has_params(self): return self.has_params_

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
    if (x.has_params()): self.mutable_params().MergeFrom(x.params())
    if (x.has_app_id()): self.set_app_id(x.app_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_params_ != x.has_params_: return 0
    if self.has_params_ and self.params_ != x.params_: return 0
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_params_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: params not set.')
    elif not self.params_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.params_.ByteSize())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_params_):
      n += 1
      n += self.lengthString(self.params_.ByteSizePartial())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n

  def Clear(self):
    self.clear_params()
    self.clear_app_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.params_.ByteSize())
    self.params_.OutputUnchecked(out)
    if (self.has_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.app_id_)

  def OutputPartial(self, out):
    if (self.has_params_):
      out.putVarInt32(10)
      out.putVarInt32(self.params_.ByteSizePartial())
      self.params_.OutputPartial(out)
    if (self.has_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.app_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_params().TryMerge(tmp)
        continue
      if tt == 26:
        self.set_app_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_params_:
      res+=prefix+"params <\n"
      res+=self.params_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kparams = 1
  kapp_id = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "params",
    3: "app_id",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.DeleteSchemaRequest'
class DeleteSchemaResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.status_ = []
    if contents is not None: self.MergeFromString(contents)

  def status_size(self): return len(self.status_)
  def status_list(self): return self.status_

  def status(self, i):
    return self.status_[i]

  def mutable_status(self, i):
    return self.status_[i]

  def add_status(self):
    x = RequestStatus()
    self.status_.append(x)
    return x

  def clear_status(self):
    self.status_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.status_size()): self.add_status().CopyFrom(x.status(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.status_) != len(x.status_): return 0
    for e1, e2 in zip(self.status_, x.status_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.status_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.status_)
    for i in xrange(len(self.status_)): n += self.lengthString(self.status_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.status_)
    for i in xrange(len(self.status_)): n += self.lengthString(self.status_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_status()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.status_)):
      out.putVarInt32(10)
      out.putVarInt32(self.status_[i].ByteSize())
      self.status_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.status_)):
      out.putVarInt32(10)
      out.putVarInt32(self.status_[i].ByteSizePartial())
      self.status_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_status().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.status_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("status%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kstatus = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "status",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.DeleteSchemaResponse'
class SortSpec(ProtocolBuffer.ProtocolMessage):
  has_sort_expression_ = 0
  sort_expression_ = ""
  has_sort_descending_ = 0
  sort_descending_ = 1
  has_default_value_text_ = 0
  default_value_text_ = ""
  has_default_value_numeric_ = 0
  default_value_numeric_ = 0.0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def sort_expression(self): return self.sort_expression_

  def set_sort_expression(self, x):
    self.has_sort_expression_ = 1
    self.sort_expression_ = x

  def clear_sort_expression(self):
    if self.has_sort_expression_:
      self.has_sort_expression_ = 0
      self.sort_expression_ = ""

  def has_sort_expression(self): return self.has_sort_expression_

  def sort_descending(self): return self.sort_descending_

  def set_sort_descending(self, x):
    self.has_sort_descending_ = 1
    self.sort_descending_ = x

  def clear_sort_descending(self):
    if self.has_sort_descending_:
      self.has_sort_descending_ = 0
      self.sort_descending_ = 1

  def has_sort_descending(self): return self.has_sort_descending_

  def default_value_text(self): return self.default_value_text_

  def set_default_value_text(self, x):
    self.has_default_value_text_ = 1
    self.default_value_text_ = x

  def clear_default_value_text(self):
    if self.has_default_value_text_:
      self.has_default_value_text_ = 0
      self.default_value_text_ = ""

  def has_default_value_text(self): return self.has_default_value_text_

  def default_value_numeric(self): return self.default_value_numeric_

  def set_default_value_numeric(self, x):
    self.has_default_value_numeric_ = 1
    self.default_value_numeric_ = x

  def clear_default_value_numeric(self):
    if self.has_default_value_numeric_:
      self.has_default_value_numeric_ = 0
      self.default_value_numeric_ = 0.0

  def has_default_value_numeric(self): return self.has_default_value_numeric_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_sort_expression()): self.set_sort_expression(x.sort_expression())
    if (x.has_sort_descending()): self.set_sort_descending(x.sort_descending())
    if (x.has_default_value_text()): self.set_default_value_text(x.default_value_text())
    if (x.has_default_value_numeric()): self.set_default_value_numeric(x.default_value_numeric())

  def Equals(self, x):
    if x is self: return 1
    if self.has_sort_expression_ != x.has_sort_expression_: return 0
    if self.has_sort_expression_ and self.sort_expression_ != x.sort_expression_: return 0
    if self.has_sort_descending_ != x.has_sort_descending_: return 0
    if self.has_sort_descending_ and self.sort_descending_ != x.sort_descending_: return 0
    if self.has_default_value_text_ != x.has_default_value_text_: return 0
    if self.has_default_value_text_ and self.default_value_text_ != x.default_value_text_: return 0
    if self.has_default_value_numeric_ != x.has_default_value_numeric_: return 0
    if self.has_default_value_numeric_ and self.default_value_numeric_ != x.default_value_numeric_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_sort_expression_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: sort_expression not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.sort_expression_))
    if (self.has_sort_descending_): n += 2
    if (self.has_default_value_text_): n += 1 + self.lengthString(len(self.default_value_text_))
    if (self.has_default_value_numeric_): n += 9
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_sort_expression_):
      n += 1
      n += self.lengthString(len(self.sort_expression_))
    if (self.has_sort_descending_): n += 2
    if (self.has_default_value_text_): n += 1 + self.lengthString(len(self.default_value_text_))
    if (self.has_default_value_numeric_): n += 9
    return n

  def Clear(self):
    self.clear_sort_expression()
    self.clear_sort_descending()
    self.clear_default_value_text()
    self.clear_default_value_numeric()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.sort_expression_)
    if (self.has_sort_descending_):
      out.putVarInt32(16)
      out.putBoolean(self.sort_descending_)
    if (self.has_default_value_text_):
      out.putVarInt32(34)
      out.putPrefixedString(self.default_value_text_)
    if (self.has_default_value_numeric_):
      out.putVarInt32(41)
      out.putDouble(self.default_value_numeric_)

  def OutputPartial(self, out):
    if (self.has_sort_expression_):
      out.putVarInt32(10)
      out.putPrefixedString(self.sort_expression_)
    if (self.has_sort_descending_):
      out.putVarInt32(16)
      out.putBoolean(self.sort_descending_)
    if (self.has_default_value_text_):
      out.putVarInt32(34)
      out.putPrefixedString(self.default_value_text_)
    if (self.has_default_value_numeric_):
      out.putVarInt32(41)
      out.putDouble(self.default_value_numeric_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_sort_expression(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_sort_descending(d.getBoolean())
        continue
      if tt == 34:
        self.set_default_value_text(d.getPrefixedString())
        continue
      if tt == 41:
        self.set_default_value_numeric(d.getDouble())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_sort_expression_: res+=prefix+("sort_expression: %s\n" % self.DebugFormatString(self.sort_expression_))
    if self.has_sort_descending_: res+=prefix+("sort_descending: %s\n" % self.DebugFormatBool(self.sort_descending_))
    if self.has_default_value_text_: res+=prefix+("default_value_text: %s\n" % self.DebugFormatString(self.default_value_text_))
    if self.has_default_value_numeric_: res+=prefix+("default_value_numeric: %s\n" % self.DebugFormat(self.default_value_numeric_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksort_expression = 1
  ksort_descending = 2
  kdefault_value_text = 4
  kdefault_value_numeric = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "sort_expression",
    2: "sort_descending",
    4: "default_value_text",
    5: "default_value_numeric",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.DOUBLE,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SortSpec'
class ScorerSpec(ProtocolBuffer.ProtocolMessage):


  RESCORING_MATCH_SCORER =    0
  MATCH_SCORER =    2

  _Scorer_NAMES = {
    0: "RESCORING_MATCH_SCORER",
    2: "MATCH_SCORER",
  }

  def Scorer_Name(cls, x): return cls._Scorer_NAMES.get(x, "")
  Scorer_Name = classmethod(Scorer_Name)

  has_scorer_ = 0
  scorer_ = 2
  has_limit_ = 0
  limit_ = 1000
  has_match_scorer_parameters_ = 0
  match_scorer_parameters_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def scorer(self): return self.scorer_

  def set_scorer(self, x):
    self.has_scorer_ = 1
    self.scorer_ = x

  def clear_scorer(self):
    if self.has_scorer_:
      self.has_scorer_ = 0
      self.scorer_ = 2

  def has_scorer(self): return self.has_scorer_

  def limit(self): return self.limit_

  def set_limit(self, x):
    self.has_limit_ = 1
    self.limit_ = x

  def clear_limit(self):
    if self.has_limit_:
      self.has_limit_ = 0
      self.limit_ = 1000

  def has_limit(self): return self.has_limit_

  def match_scorer_parameters(self): return self.match_scorer_parameters_

  def set_match_scorer_parameters(self, x):
    self.has_match_scorer_parameters_ = 1
    self.match_scorer_parameters_ = x

  def clear_match_scorer_parameters(self):
    if self.has_match_scorer_parameters_:
      self.has_match_scorer_parameters_ = 0
      self.match_scorer_parameters_ = ""

  def has_match_scorer_parameters(self): return self.has_match_scorer_parameters_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_scorer()): self.set_scorer(x.scorer())
    if (x.has_limit()): self.set_limit(x.limit())
    if (x.has_match_scorer_parameters()): self.set_match_scorer_parameters(x.match_scorer_parameters())

  def Equals(self, x):
    if x is self: return 1
    if self.has_scorer_ != x.has_scorer_: return 0
    if self.has_scorer_ and self.scorer_ != x.scorer_: return 0
    if self.has_limit_ != x.has_limit_: return 0
    if self.has_limit_ and self.limit_ != x.limit_: return 0
    if self.has_match_scorer_parameters_ != x.has_match_scorer_parameters_: return 0
    if self.has_match_scorer_parameters_ and self.match_scorer_parameters_ != x.match_scorer_parameters_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_scorer_): n += 1 + self.lengthVarInt64(self.scorer_)
    if (self.has_limit_): n += 1 + self.lengthVarInt64(self.limit_)
    if (self.has_match_scorer_parameters_): n += 1 + self.lengthString(len(self.match_scorer_parameters_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_scorer_): n += 1 + self.lengthVarInt64(self.scorer_)
    if (self.has_limit_): n += 1 + self.lengthVarInt64(self.limit_)
    if (self.has_match_scorer_parameters_): n += 1 + self.lengthString(len(self.match_scorer_parameters_))
    return n

  def Clear(self):
    self.clear_scorer()
    self.clear_limit()
    self.clear_match_scorer_parameters()

  def OutputUnchecked(self, out):
    if (self.has_scorer_):
      out.putVarInt32(8)
      out.putVarInt32(self.scorer_)
    if (self.has_limit_):
      out.putVarInt32(16)
      out.putVarInt32(self.limit_)
    if (self.has_match_scorer_parameters_):
      out.putVarInt32(74)
      out.putPrefixedString(self.match_scorer_parameters_)

  def OutputPartial(self, out):
    if (self.has_scorer_):
      out.putVarInt32(8)
      out.putVarInt32(self.scorer_)
    if (self.has_limit_):
      out.putVarInt32(16)
      out.putVarInt32(self.limit_)
    if (self.has_match_scorer_parameters_):
      out.putVarInt32(74)
      out.putPrefixedString(self.match_scorer_parameters_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_scorer(d.getVarInt32())
        continue
      if tt == 16:
        self.set_limit(d.getVarInt32())
        continue
      if tt == 74:
        self.set_match_scorer_parameters(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_scorer_: res+=prefix+("scorer: %s\n" % self.DebugFormatInt32(self.scorer_))
    if self.has_limit_: res+=prefix+("limit: %s\n" % self.DebugFormatInt32(self.limit_))
    if self.has_match_scorer_parameters_: res+=prefix+("match_scorer_parameters: %s\n" % self.DebugFormatString(self.match_scorer_parameters_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kscorer = 1
  klimit = 2
  kmatch_scorer_parameters = 9

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "scorer",
    2: "limit",
    9: "match_scorer_parameters",
  }, 9)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    9: ProtocolBuffer.Encoder.STRING,
  }, 9, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ScorerSpec'
class FieldSpec_Expression(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""
  has_expression_ = 0
  expression_ = ""

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

  def expression(self): return self.expression_

  def set_expression(self, x):
    self.has_expression_ = 1
    self.expression_ = x

  def clear_expression(self):
    if self.has_expression_:
      self.has_expression_ = 0
      self.expression_ = ""

  def has_expression(self): return self.has_expression_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())
    if (x.has_expression()): self.set_expression(x.expression())

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if self.has_expression_ != x.has_expression_: return 0
    if self.has_expression_ and self.expression_ != x.expression_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: name not set.')
    if (not self.has_expression_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: expression not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.name_))
    n += self.lengthString(len(self.expression_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    if (self.has_expression_):
      n += 1
      n += self.lengthString(len(self.expression_))
    return n

  def Clear(self):
    self.clear_name()
    self.clear_expression()

  def OutputUnchecked(self, out):
    out.putVarInt32(26)
    out.putPrefixedString(self.name_)
    out.putVarInt32(34)
    out.putPrefixedString(self.expression_)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.name_)
    if (self.has_expression_):
      out.putVarInt32(34)
      out.putPrefixedString(self.expression_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 20: break
      if tt == 26:
        self.set_name(d.getPrefixedString())
        continue
      if tt == 34:
        self.set_expression(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    if self.has_expression_: res+=prefix+("expression: %s\n" % self.DebugFormatString(self.expression_))
    return res

class FieldSpec(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.name_ = []
    self.expression_ = []
    if contents is not None: self.MergeFromString(contents)

  def name_size(self): return len(self.name_)
  def name_list(self): return self.name_

  def name(self, i):
    return self.name_[i]

  def set_name(self, i, x):
    self.name_[i] = x

  def add_name(self, x):
    self.name_.append(x)

  def clear_name(self):
    self.name_ = []

  def expression_size(self): return len(self.expression_)
  def expression_list(self): return self.expression_

  def expression(self, i):
    return self.expression_[i]

  def mutable_expression(self, i):
    return self.expression_[i]

  def add_expression(self):
    x = FieldSpec_Expression()
    self.expression_.append(x)
    return x

  def clear_expression(self):
    self.expression_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.name_size()): self.add_name(x.name(i))
    for i in xrange(x.expression_size()): self.add_expression().CopyFrom(x.expression(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.name_) != len(x.name_): return 0
    for e1, e2 in zip(self.name_, x.name_):
      if e1 != e2: return 0
    if len(self.expression_) != len(x.expression_): return 0
    for e1, e2 in zip(self.expression_, x.expression_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.expression_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.name_)
    for i in xrange(len(self.name_)): n += self.lengthString(len(self.name_[i]))
    n += 2 * len(self.expression_)
    for i in xrange(len(self.expression_)): n += self.expression_[i].ByteSize()
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.name_)
    for i in xrange(len(self.name_)): n += self.lengthString(len(self.name_[i]))
    n += 2 * len(self.expression_)
    for i in xrange(len(self.expression_)): n += self.expression_[i].ByteSizePartial()
    return n

  def Clear(self):
    self.clear_name()
    self.clear_expression()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.name_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_[i])
    for i in xrange(len(self.expression_)):
      out.putVarInt32(19)
      self.expression_[i].OutputUnchecked(out)
      out.putVarInt32(20)

  def OutputPartial(self, out):
    for i in xrange(len(self.name_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_[i])
    for i in xrange(len(self.expression_)):
      out.putVarInt32(19)
      self.expression_[i].OutputPartial(out)
      out.putVarInt32(20)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.add_name(d.getPrefixedString())
        continue
      if tt == 19:
        self.add_expression().TryMerge(d)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.name_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("name%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    cnt=0
    for e in self.expression_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Expression%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 1
  kExpressionGroup = 2
  kExpressionname = 3
  kExpressionexpression = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name",
    2: "Expression",
    3: "name",
    4: "expression",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STARTGROUP,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.FieldSpec'
class FacetRange(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""
  has_start_ = 0
  start_ = ""
  has_end_ = 0
  end_ = ""

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

  def start(self): return self.start_

  def set_start(self, x):
    self.has_start_ = 1
    self.start_ = x

  def clear_start(self):
    if self.has_start_:
      self.has_start_ = 0
      self.start_ = ""

  def has_start(self): return self.has_start_

  def end(self): return self.end_

  def set_end(self, x):
    self.has_end_ = 1
    self.end_ = x

  def clear_end(self):
    if self.has_end_:
      self.has_end_ = 0
      self.end_ = ""

  def has_end(self): return self.has_end_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())
    if (x.has_start()): self.set_start(x.start())
    if (x.has_end()): self.set_end(x.end())

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if self.has_start_ != x.has_start_: return 0
    if self.has_start_ and self.start_ != x.start_: return 0
    if self.has_end_ != x.has_end_: return 0
    if self.has_end_ and self.end_ != x.end_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_name_): n += 1 + self.lengthString(len(self.name_))
    if (self.has_start_): n += 1 + self.lengthString(len(self.start_))
    if (self.has_end_): n += 1 + self.lengthString(len(self.end_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_): n += 1 + self.lengthString(len(self.name_))
    if (self.has_start_): n += 1 + self.lengthString(len(self.start_))
    if (self.has_end_): n += 1 + self.lengthString(len(self.end_))
    return n

  def Clear(self):
    self.clear_name()
    self.clear_start()
    self.clear_end()

  def OutputUnchecked(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    if (self.has_start_):
      out.putVarInt32(18)
      out.putPrefixedString(self.start_)
    if (self.has_end_):
      out.putVarInt32(26)
      out.putPrefixedString(self.end_)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    if (self.has_start_):
      out.putVarInt32(18)
      out.putPrefixedString(self.start_)
    if (self.has_end_):
      out.putVarInt32(26)
      out.putPrefixedString(self.end_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_name(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_start(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_end(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    if self.has_start_: res+=prefix+("start: %s\n" % self.DebugFormatString(self.start_))
    if self.has_end_: res+=prefix+("end: %s\n" % self.DebugFormatString(self.end_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 1
  kstart = 2
  kend = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name",
    2: "start",
    3: "end",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.FacetRange'
class FacetRequestParam(ProtocolBuffer.ProtocolMessage):
  has_value_limit_ = 0
  value_limit_ = 0

  def __init__(self, contents=None):
    self.range_ = []
    self.value_constraint_ = []
    if contents is not None: self.MergeFromString(contents)

  def value_limit(self): return self.value_limit_

  def set_value_limit(self, x):
    self.has_value_limit_ = 1
    self.value_limit_ = x

  def clear_value_limit(self):
    if self.has_value_limit_:
      self.has_value_limit_ = 0
      self.value_limit_ = 0

  def has_value_limit(self): return self.has_value_limit_

  def range_size(self): return len(self.range_)
  def range_list(self): return self.range_

  def range(self, i):
    return self.range_[i]

  def mutable_range(self, i):
    return self.range_[i]

  def add_range(self):
    x = FacetRange()
    self.range_.append(x)
    return x

  def clear_range(self):
    self.range_ = []
  def value_constraint_size(self): return len(self.value_constraint_)
  def value_constraint_list(self): return self.value_constraint_

  def value_constraint(self, i):
    return self.value_constraint_[i]

  def set_value_constraint(self, i, x):
    self.value_constraint_[i] = x

  def add_value_constraint(self, x):
    self.value_constraint_.append(x)

  def clear_value_constraint(self):
    self.value_constraint_ = []


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_value_limit()): self.set_value_limit(x.value_limit())
    for i in xrange(x.range_size()): self.add_range().CopyFrom(x.range(i))
    for i in xrange(x.value_constraint_size()): self.add_value_constraint(x.value_constraint(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_value_limit_ != x.has_value_limit_: return 0
    if self.has_value_limit_ and self.value_limit_ != x.value_limit_: return 0
    if len(self.range_) != len(x.range_): return 0
    for e1, e2 in zip(self.range_, x.range_):
      if e1 != e2: return 0
    if len(self.value_constraint_) != len(x.value_constraint_): return 0
    for e1, e2 in zip(self.value_constraint_, x.value_constraint_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.range_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_value_limit_): n += 1 + self.lengthVarInt64(self.value_limit_)
    n += 1 * len(self.range_)
    for i in xrange(len(self.range_)): n += self.lengthString(self.range_[i].ByteSize())
    n += 1 * len(self.value_constraint_)
    for i in xrange(len(self.value_constraint_)): n += self.lengthString(len(self.value_constraint_[i]))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_value_limit_): n += 1 + self.lengthVarInt64(self.value_limit_)
    n += 1 * len(self.range_)
    for i in xrange(len(self.range_)): n += self.lengthString(self.range_[i].ByteSizePartial())
    n += 1 * len(self.value_constraint_)
    for i in xrange(len(self.value_constraint_)): n += self.lengthString(len(self.value_constraint_[i]))
    return n

  def Clear(self):
    self.clear_value_limit()
    self.clear_range()
    self.clear_value_constraint()

  def OutputUnchecked(self, out):
    if (self.has_value_limit_):
      out.putVarInt32(8)
      out.putVarInt32(self.value_limit_)
    for i in xrange(len(self.range_)):
      out.putVarInt32(18)
      out.putVarInt32(self.range_[i].ByteSize())
      self.range_[i].OutputUnchecked(out)
    for i in xrange(len(self.value_constraint_)):
      out.putVarInt32(26)
      out.putPrefixedString(self.value_constraint_[i])

  def OutputPartial(self, out):
    if (self.has_value_limit_):
      out.putVarInt32(8)
      out.putVarInt32(self.value_limit_)
    for i in xrange(len(self.range_)):
      out.putVarInt32(18)
      out.putVarInt32(self.range_[i].ByteSizePartial())
      self.range_[i].OutputPartial(out)
    for i in xrange(len(self.value_constraint_)):
      out.putVarInt32(26)
      out.putPrefixedString(self.value_constraint_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_value_limit(d.getVarInt32())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_range().TryMerge(tmp)
        continue
      if tt == 26:
        self.add_value_constraint(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_value_limit_: res+=prefix+("value_limit: %s\n" % self.DebugFormatInt32(self.value_limit_))
    cnt=0
    for e in self.range_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("range%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.value_constraint_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("value_constraint%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kvalue_limit = 1
  krange = 2
  kvalue_constraint = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "value_limit",
    2: "range",
    3: "value_constraint",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.FacetRequestParam'
class FacetAutoDetectParam(ProtocolBuffer.ProtocolMessage):
  has_value_limit_ = 0
  value_limit_ = 10

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def value_limit(self): return self.value_limit_

  def set_value_limit(self, x):
    self.has_value_limit_ = 1
    self.value_limit_ = x

  def clear_value_limit(self):
    if self.has_value_limit_:
      self.has_value_limit_ = 0
      self.value_limit_ = 10

  def has_value_limit(self): return self.has_value_limit_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_value_limit()): self.set_value_limit(x.value_limit())

  def Equals(self, x):
    if x is self: return 1
    if self.has_value_limit_ != x.has_value_limit_: return 0
    if self.has_value_limit_ and self.value_limit_ != x.value_limit_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_value_limit_): n += 1 + self.lengthVarInt64(self.value_limit_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_value_limit_): n += 1 + self.lengthVarInt64(self.value_limit_)
    return n

  def Clear(self):
    self.clear_value_limit()

  def OutputUnchecked(self, out):
    if (self.has_value_limit_):
      out.putVarInt32(8)
      out.putVarInt32(self.value_limit_)

  def OutputPartial(self, out):
    if (self.has_value_limit_):
      out.putVarInt32(8)
      out.putVarInt32(self.value_limit_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_value_limit(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_value_limit_: res+=prefix+("value_limit: %s\n" % self.DebugFormatInt32(self.value_limit_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kvalue_limit = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "value_limit",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.FacetAutoDetectParam'
class FacetRequest(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""
  has_params_ = 0
  params_ = None

  def __init__(self, contents=None):
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

  def params(self):
    if self.params_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.params_ is None: self.params_ = FacetRequestParam()
      finally:
        self.lazy_init_lock_.release()
    return self.params_

  def mutable_params(self): self.has_params_ = 1; return self.params()

  def clear_params(self):

    if self.has_params_:
      self.has_params_ = 0;
      if self.params_ is not None: self.params_.Clear()

  def has_params(self): return self.has_params_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())
    if (x.has_params()): self.mutable_params().MergeFrom(x.params())

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if self.has_params_ != x.has_params_: return 0
    if self.has_params_ and self.params_ != x.params_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: name not set.')
    if (self.has_params_ and not self.params_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.name_))
    if (self.has_params_): n += 1 + self.lengthString(self.params_.ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    if (self.has_params_): n += 1 + self.lengthString(self.params_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_name()
    self.clear_params()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.name_)
    if (self.has_params_):
      out.putVarInt32(18)
      out.putVarInt32(self.params_.ByteSize())
      self.params_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    if (self.has_params_):
      out.putVarInt32(18)
      out.putVarInt32(self.params_.ByteSizePartial())
      self.params_.OutputPartial(out)

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
        self.mutable_params().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    if self.has_params_:
      res+=prefix+"params <\n"
      res+=self.params_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 1
  kparams = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name",
    2: "params",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.FacetRequest'
class FacetRefinement_Range(ProtocolBuffer.ProtocolMessage):
  has_start_ = 0
  start_ = ""
  has_end_ = 0
  end_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def start(self): return self.start_

  def set_start(self, x):
    self.has_start_ = 1
    self.start_ = x

  def clear_start(self):
    if self.has_start_:
      self.has_start_ = 0
      self.start_ = ""

  def has_start(self): return self.has_start_

  def end(self): return self.end_

  def set_end(self, x):
    self.has_end_ = 1
    self.end_ = x

  def clear_end(self):
    if self.has_end_:
      self.has_end_ = 0
      self.end_ = ""

  def has_end(self): return self.has_end_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_start()): self.set_start(x.start())
    if (x.has_end()): self.set_end(x.end())

  def Equals(self, x):
    if x is self: return 1
    if self.has_start_ != x.has_start_: return 0
    if self.has_start_ and self.start_ != x.start_: return 0
    if self.has_end_ != x.has_end_: return 0
    if self.has_end_ and self.end_ != x.end_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_start_): n += 1 + self.lengthString(len(self.start_))
    if (self.has_end_): n += 1 + self.lengthString(len(self.end_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_start_): n += 1 + self.lengthString(len(self.start_))
    if (self.has_end_): n += 1 + self.lengthString(len(self.end_))
    return n

  def Clear(self):
    self.clear_start()
    self.clear_end()

  def OutputUnchecked(self, out):
    if (self.has_start_):
      out.putVarInt32(10)
      out.putPrefixedString(self.start_)
    if (self.has_end_):
      out.putVarInt32(18)
      out.putPrefixedString(self.end_)

  def OutputPartial(self, out):
    if (self.has_start_):
      out.putVarInt32(10)
      out.putPrefixedString(self.start_)
    if (self.has_end_):
      out.putVarInt32(18)
      out.putPrefixedString(self.end_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_start(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_end(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_start_: res+=prefix+("start: %s\n" % self.DebugFormatString(self.start_))
    if self.has_end_: res+=prefix+("end: %s\n" % self.DebugFormatString(self.end_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kstart = 1
  kend = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "start",
    2: "end",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.FacetRefinement_Range'
class FacetRefinement(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""
  has_value_ = 0
  value_ = ""
  has_range_ = 0
  range_ = None

  def __init__(self, contents=None):
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

  def value(self): return self.value_

  def set_value(self, x):
    self.has_value_ = 1
    self.value_ = x

  def clear_value(self):
    if self.has_value_:
      self.has_value_ = 0
      self.value_ = ""

  def has_value(self): return self.has_value_

  def range(self):
    if self.range_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.range_ is None: self.range_ = FacetRefinement_Range()
      finally:
        self.lazy_init_lock_.release()
    return self.range_

  def mutable_range(self): self.has_range_ = 1; return self.range()

  def clear_range(self):

    if self.has_range_:
      self.has_range_ = 0;
      if self.range_ is not None: self.range_.Clear()

  def has_range(self): return self.has_range_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())
    if (x.has_value()): self.set_value(x.value())
    if (x.has_range()): self.mutable_range().MergeFrom(x.range())

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    if self.has_range_ != x.has_range_: return 0
    if self.has_range_ and self.range_ != x.range_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: name not set.')
    if (self.has_range_ and not self.range_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.name_))
    if (self.has_value_): n += 1 + self.lengthString(len(self.value_))
    if (self.has_range_): n += 1 + self.lengthString(self.range_.ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    if (self.has_value_): n += 1 + self.lengthString(len(self.value_))
    if (self.has_range_): n += 1 + self.lengthString(self.range_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_name()
    self.clear_value()
    self.clear_range()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.name_)
    if (self.has_value_):
      out.putVarInt32(18)
      out.putPrefixedString(self.value_)
    if (self.has_range_):
      out.putVarInt32(26)
      out.putVarInt32(self.range_.ByteSize())
      self.range_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    if (self.has_value_):
      out.putVarInt32(18)
      out.putPrefixedString(self.value_)
    if (self.has_range_):
      out.putVarInt32(26)
      out.putVarInt32(self.range_.ByteSizePartial())
      self.range_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_name(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_value(d.getPrefixedString())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_range().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    if self.has_value_: res+=prefix+("value: %s\n" % self.DebugFormatString(self.value_))
    if self.has_range_:
      res+=prefix+"range <\n"
      res+=self.range_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 1
  kvalue = 2
  krange = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name",
    2: "value",
    3: "range",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.FacetRefinement'
class SearchParams(ProtocolBuffer.ProtocolMessage):


  NONE         =    0
  SINGLE       =    1
  PER_RESULT   =    2

  _CursorType_NAMES = {
    0: "NONE",
    1: "SINGLE",
    2: "PER_RESULT",
  }

  def CursorType_Name(cls, x): return cls._CursorType_NAMES.get(x, "")
  CursorType_Name = classmethod(CursorType_Name)



  STRICT       =    0
  RELAXED      =    1

  _ParsingMode_NAMES = {
    0: "STRICT",
    1: "RELAXED",
  }

  def ParsingMode_Name(cls, x): return cls._ParsingMode_NAMES.get(x, "")
  ParsingMode_Name = classmethod(ParsingMode_Name)

  has_index_spec_ = 0
  has_query_ = 0
  query_ = ""
  has_cursor_ = 0
  cursor_ = ""
  has_offset_ = 0
  offset_ = 0
  has_cursor_type_ = 0
  cursor_type_ = 0
  has_limit_ = 0
  limit_ = 20
  has_matched_count_accuracy_ = 0
  matched_count_accuracy_ = 0
  has_scorer_spec_ = 0
  scorer_spec_ = None
  has_field_spec_ = 0
  field_spec_ = None
  has_keys_only_ = 0
  keys_only_ = 0
  has_parsing_mode_ = 0
  parsing_mode_ = 0
  has_auto_discover_facet_count_ = 0
  auto_discover_facet_count_ = 0
  has_facet_auto_detect_param_ = 0
  facet_auto_detect_param_ = None
  has_facet_depth_ = 0
  facet_depth_ = 1000

  def __init__(self, contents=None):
    self.index_spec_ = IndexSpec()
    self.sort_spec_ = []
    self.include_facet_ = []
    self.facet_refinement_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def index_spec(self): return self.index_spec_

  def mutable_index_spec(self): self.has_index_spec_ = 1; return self.index_spec_

  def clear_index_spec(self):self.has_index_spec_ = 0; self.index_spec_.Clear()

  def has_index_spec(self): return self.has_index_spec_

  def query(self): return self.query_

  def set_query(self, x):
    self.has_query_ = 1
    self.query_ = x

  def clear_query(self):
    if self.has_query_:
      self.has_query_ = 0
      self.query_ = ""

  def has_query(self): return self.has_query_

  def cursor(self): return self.cursor_

  def set_cursor(self, x):
    self.has_cursor_ = 1
    self.cursor_ = x

  def clear_cursor(self):
    if self.has_cursor_:
      self.has_cursor_ = 0
      self.cursor_ = ""

  def has_cursor(self): return self.has_cursor_

  def offset(self): return self.offset_

  def set_offset(self, x):
    self.has_offset_ = 1
    self.offset_ = x

  def clear_offset(self):
    if self.has_offset_:
      self.has_offset_ = 0
      self.offset_ = 0

  def has_offset(self): return self.has_offset_

  def cursor_type(self): return self.cursor_type_

  def set_cursor_type(self, x):
    self.has_cursor_type_ = 1
    self.cursor_type_ = x

  def clear_cursor_type(self):
    if self.has_cursor_type_:
      self.has_cursor_type_ = 0
      self.cursor_type_ = 0

  def has_cursor_type(self): return self.has_cursor_type_

  def limit(self): return self.limit_

  def set_limit(self, x):
    self.has_limit_ = 1
    self.limit_ = x

  def clear_limit(self):
    if self.has_limit_:
      self.has_limit_ = 0
      self.limit_ = 20

  def has_limit(self): return self.has_limit_

  def matched_count_accuracy(self): return self.matched_count_accuracy_

  def set_matched_count_accuracy(self, x):
    self.has_matched_count_accuracy_ = 1
    self.matched_count_accuracy_ = x

  def clear_matched_count_accuracy(self):
    if self.has_matched_count_accuracy_:
      self.has_matched_count_accuracy_ = 0
      self.matched_count_accuracy_ = 0

  def has_matched_count_accuracy(self): return self.has_matched_count_accuracy_

  def sort_spec_size(self): return len(self.sort_spec_)
  def sort_spec_list(self): return self.sort_spec_

  def sort_spec(self, i):
    return self.sort_spec_[i]

  def mutable_sort_spec(self, i):
    return self.sort_spec_[i]

  def add_sort_spec(self):
    x = SortSpec()
    self.sort_spec_.append(x)
    return x

  def clear_sort_spec(self):
    self.sort_spec_ = []
  def scorer_spec(self):
    if self.scorer_spec_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.scorer_spec_ is None: self.scorer_spec_ = ScorerSpec()
      finally:
        self.lazy_init_lock_.release()
    return self.scorer_spec_

  def mutable_scorer_spec(self): self.has_scorer_spec_ = 1; return self.scorer_spec()

  def clear_scorer_spec(self):

    if self.has_scorer_spec_:
      self.has_scorer_spec_ = 0;
      if self.scorer_spec_ is not None: self.scorer_spec_.Clear()

  def has_scorer_spec(self): return self.has_scorer_spec_

  def field_spec(self):
    if self.field_spec_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.field_spec_ is None: self.field_spec_ = FieldSpec()
      finally:
        self.lazy_init_lock_.release()
    return self.field_spec_

  def mutable_field_spec(self): self.has_field_spec_ = 1; return self.field_spec()

  def clear_field_spec(self):

    if self.has_field_spec_:
      self.has_field_spec_ = 0;
      if self.field_spec_ is not None: self.field_spec_.Clear()

  def has_field_spec(self): return self.has_field_spec_

  def keys_only(self): return self.keys_only_

  def set_keys_only(self, x):
    self.has_keys_only_ = 1
    self.keys_only_ = x

  def clear_keys_only(self):
    if self.has_keys_only_:
      self.has_keys_only_ = 0
      self.keys_only_ = 0

  def has_keys_only(self): return self.has_keys_only_

  def parsing_mode(self): return self.parsing_mode_

  def set_parsing_mode(self, x):
    self.has_parsing_mode_ = 1
    self.parsing_mode_ = x

  def clear_parsing_mode(self):
    if self.has_parsing_mode_:
      self.has_parsing_mode_ = 0
      self.parsing_mode_ = 0

  def has_parsing_mode(self): return self.has_parsing_mode_

  def auto_discover_facet_count(self): return self.auto_discover_facet_count_

  def set_auto_discover_facet_count(self, x):
    self.has_auto_discover_facet_count_ = 1
    self.auto_discover_facet_count_ = x

  def clear_auto_discover_facet_count(self):
    if self.has_auto_discover_facet_count_:
      self.has_auto_discover_facet_count_ = 0
      self.auto_discover_facet_count_ = 0

  def has_auto_discover_facet_count(self): return self.has_auto_discover_facet_count_

  def include_facet_size(self): return len(self.include_facet_)
  def include_facet_list(self): return self.include_facet_

  def include_facet(self, i):
    return self.include_facet_[i]

  def mutable_include_facet(self, i):
    return self.include_facet_[i]

  def add_include_facet(self):
    x = FacetRequest()
    self.include_facet_.append(x)
    return x

  def clear_include_facet(self):
    self.include_facet_ = []
  def facet_refinement_size(self): return len(self.facet_refinement_)
  def facet_refinement_list(self): return self.facet_refinement_

  def facet_refinement(self, i):
    return self.facet_refinement_[i]

  def mutable_facet_refinement(self, i):
    return self.facet_refinement_[i]

  def add_facet_refinement(self):
    x = FacetRefinement()
    self.facet_refinement_.append(x)
    return x

  def clear_facet_refinement(self):
    self.facet_refinement_ = []
  def facet_auto_detect_param(self):
    if self.facet_auto_detect_param_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.facet_auto_detect_param_ is None: self.facet_auto_detect_param_ = FacetAutoDetectParam()
      finally:
        self.lazy_init_lock_.release()
    return self.facet_auto_detect_param_

  def mutable_facet_auto_detect_param(self): self.has_facet_auto_detect_param_ = 1; return self.facet_auto_detect_param()

  def clear_facet_auto_detect_param(self):

    if self.has_facet_auto_detect_param_:
      self.has_facet_auto_detect_param_ = 0;
      if self.facet_auto_detect_param_ is not None: self.facet_auto_detect_param_.Clear()

  def has_facet_auto_detect_param(self): return self.has_facet_auto_detect_param_

  def facet_depth(self): return self.facet_depth_

  def set_facet_depth(self, x):
    self.has_facet_depth_ = 1
    self.facet_depth_ = x

  def clear_facet_depth(self):
    if self.has_facet_depth_:
      self.has_facet_depth_ = 0
      self.facet_depth_ = 1000

  def has_facet_depth(self): return self.has_facet_depth_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_index_spec()): self.mutable_index_spec().MergeFrom(x.index_spec())
    if (x.has_query()): self.set_query(x.query())
    if (x.has_cursor()): self.set_cursor(x.cursor())
    if (x.has_offset()): self.set_offset(x.offset())
    if (x.has_cursor_type()): self.set_cursor_type(x.cursor_type())
    if (x.has_limit()): self.set_limit(x.limit())
    if (x.has_matched_count_accuracy()): self.set_matched_count_accuracy(x.matched_count_accuracy())
    for i in xrange(x.sort_spec_size()): self.add_sort_spec().CopyFrom(x.sort_spec(i))
    if (x.has_scorer_spec()): self.mutable_scorer_spec().MergeFrom(x.scorer_spec())
    if (x.has_field_spec()): self.mutable_field_spec().MergeFrom(x.field_spec())
    if (x.has_keys_only()): self.set_keys_only(x.keys_only())
    if (x.has_parsing_mode()): self.set_parsing_mode(x.parsing_mode())
    if (x.has_auto_discover_facet_count()): self.set_auto_discover_facet_count(x.auto_discover_facet_count())
    for i in xrange(x.include_facet_size()): self.add_include_facet().CopyFrom(x.include_facet(i))
    for i in xrange(x.facet_refinement_size()): self.add_facet_refinement().CopyFrom(x.facet_refinement(i))
    if (x.has_facet_auto_detect_param()): self.mutable_facet_auto_detect_param().MergeFrom(x.facet_auto_detect_param())
    if (x.has_facet_depth()): self.set_facet_depth(x.facet_depth())

  def Equals(self, x):
    if x is self: return 1
    if self.has_index_spec_ != x.has_index_spec_: return 0
    if self.has_index_spec_ and self.index_spec_ != x.index_spec_: return 0
    if self.has_query_ != x.has_query_: return 0
    if self.has_query_ and self.query_ != x.query_: return 0
    if self.has_cursor_ != x.has_cursor_: return 0
    if self.has_cursor_ and self.cursor_ != x.cursor_: return 0
    if self.has_offset_ != x.has_offset_: return 0
    if self.has_offset_ and self.offset_ != x.offset_: return 0
    if self.has_cursor_type_ != x.has_cursor_type_: return 0
    if self.has_cursor_type_ and self.cursor_type_ != x.cursor_type_: return 0
    if self.has_limit_ != x.has_limit_: return 0
    if self.has_limit_ and self.limit_ != x.limit_: return 0
    if self.has_matched_count_accuracy_ != x.has_matched_count_accuracy_: return 0
    if self.has_matched_count_accuracy_ and self.matched_count_accuracy_ != x.matched_count_accuracy_: return 0
    if len(self.sort_spec_) != len(x.sort_spec_): return 0
    for e1, e2 in zip(self.sort_spec_, x.sort_spec_):
      if e1 != e2: return 0
    if self.has_scorer_spec_ != x.has_scorer_spec_: return 0
    if self.has_scorer_spec_ and self.scorer_spec_ != x.scorer_spec_: return 0
    if self.has_field_spec_ != x.has_field_spec_: return 0
    if self.has_field_spec_ and self.field_spec_ != x.field_spec_: return 0
    if self.has_keys_only_ != x.has_keys_only_: return 0
    if self.has_keys_only_ and self.keys_only_ != x.keys_only_: return 0
    if self.has_parsing_mode_ != x.has_parsing_mode_: return 0
    if self.has_parsing_mode_ and self.parsing_mode_ != x.parsing_mode_: return 0
    if self.has_auto_discover_facet_count_ != x.has_auto_discover_facet_count_: return 0
    if self.has_auto_discover_facet_count_ and self.auto_discover_facet_count_ != x.auto_discover_facet_count_: return 0
    if len(self.include_facet_) != len(x.include_facet_): return 0
    for e1, e2 in zip(self.include_facet_, x.include_facet_):
      if e1 != e2: return 0
    if len(self.facet_refinement_) != len(x.facet_refinement_): return 0
    for e1, e2 in zip(self.facet_refinement_, x.facet_refinement_):
      if e1 != e2: return 0
    if self.has_facet_auto_detect_param_ != x.has_facet_auto_detect_param_: return 0
    if self.has_facet_auto_detect_param_ and self.facet_auto_detect_param_ != x.facet_auto_detect_param_: return 0
    if self.has_facet_depth_ != x.has_facet_depth_: return 0
    if self.has_facet_depth_ and self.facet_depth_ != x.facet_depth_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_index_spec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: index_spec not set.')
    elif not self.index_spec_.IsInitialized(debug_strs): initialized = 0
    if (not self.has_query_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: query not set.')
    for p in self.sort_spec_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_scorer_spec_ and not self.scorer_spec_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_field_spec_ and not self.field_spec_.IsInitialized(debug_strs)): initialized = 0
    for p in self.include_facet_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.facet_refinement_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_facet_auto_detect_param_ and not self.facet_auto_detect_param_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.index_spec_.ByteSize())
    n += self.lengthString(len(self.query_))
    if (self.has_cursor_): n += 1 + self.lengthString(len(self.cursor_))
    if (self.has_offset_): n += 1 + self.lengthVarInt64(self.offset_)
    if (self.has_cursor_type_): n += 1 + self.lengthVarInt64(self.cursor_type_)
    if (self.has_limit_): n += 1 + self.lengthVarInt64(self.limit_)
    if (self.has_matched_count_accuracy_): n += 1 + self.lengthVarInt64(self.matched_count_accuracy_)
    n += 1 * len(self.sort_spec_)
    for i in xrange(len(self.sort_spec_)): n += self.lengthString(self.sort_spec_[i].ByteSize())
    if (self.has_scorer_spec_): n += 1 + self.lengthString(self.scorer_spec_.ByteSize())
    if (self.has_field_spec_): n += 1 + self.lengthString(self.field_spec_.ByteSize())
    if (self.has_keys_only_): n += 2
    if (self.has_parsing_mode_): n += 1 + self.lengthVarInt64(self.parsing_mode_)
    if (self.has_auto_discover_facet_count_): n += 1 + self.lengthVarInt64(self.auto_discover_facet_count_)
    n += 2 * len(self.include_facet_)
    for i in xrange(len(self.include_facet_)): n += self.lengthString(self.include_facet_[i].ByteSize())
    n += 2 * len(self.facet_refinement_)
    for i in xrange(len(self.facet_refinement_)): n += self.lengthString(self.facet_refinement_[i].ByteSize())
    if (self.has_facet_auto_detect_param_): n += 2 + self.lengthString(self.facet_auto_detect_param_.ByteSize())
    if (self.has_facet_depth_): n += 2 + self.lengthVarInt64(self.facet_depth_)
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_index_spec_):
      n += 1
      n += self.lengthString(self.index_spec_.ByteSizePartial())
    if (self.has_query_):
      n += 1
      n += self.lengthString(len(self.query_))
    if (self.has_cursor_): n += 1 + self.lengthString(len(self.cursor_))
    if (self.has_offset_): n += 1 + self.lengthVarInt64(self.offset_)
    if (self.has_cursor_type_): n += 1 + self.lengthVarInt64(self.cursor_type_)
    if (self.has_limit_): n += 1 + self.lengthVarInt64(self.limit_)
    if (self.has_matched_count_accuracy_): n += 1 + self.lengthVarInt64(self.matched_count_accuracy_)
    n += 1 * len(self.sort_spec_)
    for i in xrange(len(self.sort_spec_)): n += self.lengthString(self.sort_spec_[i].ByteSizePartial())
    if (self.has_scorer_spec_): n += 1 + self.lengthString(self.scorer_spec_.ByteSizePartial())
    if (self.has_field_spec_): n += 1 + self.lengthString(self.field_spec_.ByteSizePartial())
    if (self.has_keys_only_): n += 2
    if (self.has_parsing_mode_): n += 1 + self.lengthVarInt64(self.parsing_mode_)
    if (self.has_auto_discover_facet_count_): n += 1 + self.lengthVarInt64(self.auto_discover_facet_count_)
    n += 2 * len(self.include_facet_)
    for i in xrange(len(self.include_facet_)): n += self.lengthString(self.include_facet_[i].ByteSizePartial())
    n += 2 * len(self.facet_refinement_)
    for i in xrange(len(self.facet_refinement_)): n += self.lengthString(self.facet_refinement_[i].ByteSizePartial())
    if (self.has_facet_auto_detect_param_): n += 2 + self.lengthString(self.facet_auto_detect_param_.ByteSizePartial())
    if (self.has_facet_depth_): n += 2 + self.lengthVarInt64(self.facet_depth_)
    return n

  def Clear(self):
    self.clear_index_spec()
    self.clear_query()
    self.clear_cursor()
    self.clear_offset()
    self.clear_cursor_type()
    self.clear_limit()
    self.clear_matched_count_accuracy()
    self.clear_sort_spec()
    self.clear_scorer_spec()
    self.clear_field_spec()
    self.clear_keys_only()
    self.clear_parsing_mode()
    self.clear_auto_discover_facet_count()
    self.clear_include_facet()
    self.clear_facet_refinement()
    self.clear_facet_auto_detect_param()
    self.clear_facet_depth()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.index_spec_.ByteSize())
    self.index_spec_.OutputUnchecked(out)
    out.putVarInt32(18)
    out.putPrefixedString(self.query_)
    if (self.has_cursor_):
      out.putVarInt32(34)
      out.putPrefixedString(self.cursor_)
    if (self.has_cursor_type_):
      out.putVarInt32(40)
      out.putVarInt32(self.cursor_type_)
    if (self.has_limit_):
      out.putVarInt32(48)
      out.putVarInt32(self.limit_)
    if (self.has_matched_count_accuracy_):
      out.putVarInt32(56)
      out.putVarInt32(self.matched_count_accuracy_)
    for i in xrange(len(self.sort_spec_)):
      out.putVarInt32(66)
      out.putVarInt32(self.sort_spec_[i].ByteSize())
      self.sort_spec_[i].OutputUnchecked(out)
    if (self.has_scorer_spec_):
      out.putVarInt32(74)
      out.putVarInt32(self.scorer_spec_.ByteSize())
      self.scorer_spec_.OutputUnchecked(out)
    if (self.has_field_spec_):
      out.putVarInt32(82)
      out.putVarInt32(self.field_spec_.ByteSize())
      self.field_spec_.OutputUnchecked(out)
    if (self.has_offset_):
      out.putVarInt32(88)
      out.putVarInt32(self.offset_)
    if (self.has_keys_only_):
      out.putVarInt32(96)
      out.putBoolean(self.keys_only_)
    if (self.has_parsing_mode_):
      out.putVarInt32(104)
      out.putVarInt32(self.parsing_mode_)
    if (self.has_auto_discover_facet_count_):
      out.putVarInt32(120)
      out.putVarInt32(self.auto_discover_facet_count_)
    for i in xrange(len(self.include_facet_)):
      out.putVarInt32(130)
      out.putVarInt32(self.include_facet_[i].ByteSize())
      self.include_facet_[i].OutputUnchecked(out)
    for i in xrange(len(self.facet_refinement_)):
      out.putVarInt32(138)
      out.putVarInt32(self.facet_refinement_[i].ByteSize())
      self.facet_refinement_[i].OutputUnchecked(out)
    if (self.has_facet_auto_detect_param_):
      out.putVarInt32(146)
      out.putVarInt32(self.facet_auto_detect_param_.ByteSize())
      self.facet_auto_detect_param_.OutputUnchecked(out)
    if (self.has_facet_depth_):
      out.putVarInt32(152)
      out.putVarInt32(self.facet_depth_)

  def OutputPartial(self, out):
    if (self.has_index_spec_):
      out.putVarInt32(10)
      out.putVarInt32(self.index_spec_.ByteSizePartial())
      self.index_spec_.OutputPartial(out)
    if (self.has_query_):
      out.putVarInt32(18)
      out.putPrefixedString(self.query_)
    if (self.has_cursor_):
      out.putVarInt32(34)
      out.putPrefixedString(self.cursor_)
    if (self.has_cursor_type_):
      out.putVarInt32(40)
      out.putVarInt32(self.cursor_type_)
    if (self.has_limit_):
      out.putVarInt32(48)
      out.putVarInt32(self.limit_)
    if (self.has_matched_count_accuracy_):
      out.putVarInt32(56)
      out.putVarInt32(self.matched_count_accuracy_)
    for i in xrange(len(self.sort_spec_)):
      out.putVarInt32(66)
      out.putVarInt32(self.sort_spec_[i].ByteSizePartial())
      self.sort_spec_[i].OutputPartial(out)
    if (self.has_scorer_spec_):
      out.putVarInt32(74)
      out.putVarInt32(self.scorer_spec_.ByteSizePartial())
      self.scorer_spec_.OutputPartial(out)
    if (self.has_field_spec_):
      out.putVarInt32(82)
      out.putVarInt32(self.field_spec_.ByteSizePartial())
      self.field_spec_.OutputPartial(out)
    if (self.has_offset_):
      out.putVarInt32(88)
      out.putVarInt32(self.offset_)
    if (self.has_keys_only_):
      out.putVarInt32(96)
      out.putBoolean(self.keys_only_)
    if (self.has_parsing_mode_):
      out.putVarInt32(104)
      out.putVarInt32(self.parsing_mode_)
    if (self.has_auto_discover_facet_count_):
      out.putVarInt32(120)
      out.putVarInt32(self.auto_discover_facet_count_)
    for i in xrange(len(self.include_facet_)):
      out.putVarInt32(130)
      out.putVarInt32(self.include_facet_[i].ByteSizePartial())
      self.include_facet_[i].OutputPartial(out)
    for i in xrange(len(self.facet_refinement_)):
      out.putVarInt32(138)
      out.putVarInt32(self.facet_refinement_[i].ByteSizePartial())
      self.facet_refinement_[i].OutputPartial(out)
    if (self.has_facet_auto_detect_param_):
      out.putVarInt32(146)
      out.putVarInt32(self.facet_auto_detect_param_.ByteSizePartial())
      self.facet_auto_detect_param_.OutputPartial(out)
    if (self.has_facet_depth_):
      out.putVarInt32(152)
      out.putVarInt32(self.facet_depth_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_index_spec().TryMerge(tmp)
        continue
      if tt == 18:
        self.set_query(d.getPrefixedString())
        continue
      if tt == 34:
        self.set_cursor(d.getPrefixedString())
        continue
      if tt == 40:
        self.set_cursor_type(d.getVarInt32())
        continue
      if tt == 48:
        self.set_limit(d.getVarInt32())
        continue
      if tt == 56:
        self.set_matched_count_accuracy(d.getVarInt32())
        continue
      if tt == 66:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_sort_spec().TryMerge(tmp)
        continue
      if tt == 74:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_scorer_spec().TryMerge(tmp)
        continue
      if tt == 82:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_field_spec().TryMerge(tmp)
        continue
      if tt == 88:
        self.set_offset(d.getVarInt32())
        continue
      if tt == 96:
        self.set_keys_only(d.getBoolean())
        continue
      if tt == 104:
        self.set_parsing_mode(d.getVarInt32())
        continue
      if tt == 120:
        self.set_auto_discover_facet_count(d.getVarInt32())
        continue
      if tt == 130:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_include_facet().TryMerge(tmp)
        continue
      if tt == 138:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_facet_refinement().TryMerge(tmp)
        continue
      if tt == 146:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_facet_auto_detect_param().TryMerge(tmp)
        continue
      if tt == 152:
        self.set_facet_depth(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_index_spec_:
      res+=prefix+"index_spec <\n"
      res+=self.index_spec_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_query_: res+=prefix+("query: %s\n" % self.DebugFormatString(self.query_))
    if self.has_cursor_: res+=prefix+("cursor: %s\n" % self.DebugFormatString(self.cursor_))
    if self.has_offset_: res+=prefix+("offset: %s\n" % self.DebugFormatInt32(self.offset_))
    if self.has_cursor_type_: res+=prefix+("cursor_type: %s\n" % self.DebugFormatInt32(self.cursor_type_))
    if self.has_limit_: res+=prefix+("limit: %s\n" % self.DebugFormatInt32(self.limit_))
    if self.has_matched_count_accuracy_: res+=prefix+("matched_count_accuracy: %s\n" % self.DebugFormatInt32(self.matched_count_accuracy_))
    cnt=0
    for e in self.sort_spec_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("sort_spec%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_scorer_spec_:
      res+=prefix+"scorer_spec <\n"
      res+=self.scorer_spec_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_field_spec_:
      res+=prefix+"field_spec <\n"
      res+=self.field_spec_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_keys_only_: res+=prefix+("keys_only: %s\n" % self.DebugFormatBool(self.keys_only_))
    if self.has_parsing_mode_: res+=prefix+("parsing_mode: %s\n" % self.DebugFormatInt32(self.parsing_mode_))
    if self.has_auto_discover_facet_count_: res+=prefix+("auto_discover_facet_count: %s\n" % self.DebugFormatInt32(self.auto_discover_facet_count_))
    cnt=0
    for e in self.include_facet_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("include_facet%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.facet_refinement_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("facet_refinement%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_facet_auto_detect_param_:
      res+=prefix+"facet_auto_detect_param <\n"
      res+=self.facet_auto_detect_param_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_facet_depth_: res+=prefix+("facet_depth: %s\n" % self.DebugFormatInt32(self.facet_depth_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kindex_spec = 1
  kquery = 2
  kcursor = 4
  koffset = 11
  kcursor_type = 5
  klimit = 6
  kmatched_count_accuracy = 7
  ksort_spec = 8
  kscorer_spec = 9
  kfield_spec = 10
  kkeys_only = 12
  kparsing_mode = 13
  kauto_discover_facet_count = 15
  kinclude_facet = 16
  kfacet_refinement = 17
  kfacet_auto_detect_param = 18
  kfacet_depth = 19

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "index_spec",
    2: "query",
    4: "cursor",
    5: "cursor_type",
    6: "limit",
    7: "matched_count_accuracy",
    8: "sort_spec",
    9: "scorer_spec",
    10: "field_spec",
    11: "offset",
    12: "keys_only",
    13: "parsing_mode",
    15: "auto_discover_facet_count",
    16: "include_facet",
    17: "facet_refinement",
    18: "facet_auto_detect_param",
    19: "facet_depth",
  }, 19)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.NUMERIC,
    7: ProtocolBuffer.Encoder.NUMERIC,
    8: ProtocolBuffer.Encoder.STRING,
    9: ProtocolBuffer.Encoder.STRING,
    10: ProtocolBuffer.Encoder.STRING,
    11: ProtocolBuffer.Encoder.NUMERIC,
    12: ProtocolBuffer.Encoder.NUMERIC,
    13: ProtocolBuffer.Encoder.NUMERIC,
    15: ProtocolBuffer.Encoder.NUMERIC,
    16: ProtocolBuffer.Encoder.STRING,
    17: ProtocolBuffer.Encoder.STRING,
    18: ProtocolBuffer.Encoder.STRING,
    19: ProtocolBuffer.Encoder.NUMERIC,
  }, 19, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SearchParams'
class SearchRequest(ProtocolBuffer.ProtocolMessage):
  has_params_ = 0
  has_app_id_ = 0
  app_id_ = ""

  def __init__(self, contents=None):
    self.params_ = SearchParams()
    if contents is not None: self.MergeFromString(contents)

  def params(self): return self.params_

  def mutable_params(self): self.has_params_ = 1; return self.params_

  def clear_params(self):self.has_params_ = 0; self.params_.Clear()

  def has_params(self): return self.has_params_

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
    if (x.has_params()): self.mutable_params().MergeFrom(x.params())
    if (x.has_app_id()): self.set_app_id(x.app_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_params_ != x.has_params_: return 0
    if self.has_params_ and self.params_ != x.params_: return 0
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_params_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: params not set.')
    elif not self.params_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.params_.ByteSize())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_params_):
      n += 1
      n += self.lengthString(self.params_.ByteSizePartial())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n

  def Clear(self):
    self.clear_params()
    self.clear_app_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.params_.ByteSize())
    self.params_.OutputUnchecked(out)
    if (self.has_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.app_id_)

  def OutputPartial(self, out):
    if (self.has_params_):
      out.putVarInt32(10)
      out.putVarInt32(self.params_.ByteSizePartial())
      self.params_.OutputPartial(out)
    if (self.has_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.app_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_params().TryMerge(tmp)
        continue
      if tt == 26:
        self.set_app_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_params_:
      res+=prefix+"params <\n"
      res+=self.params_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kparams = 1
  kapp_id = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "params",
    3: "app_id",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SearchRequest'
class FacetResultValue(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""
  has_count_ = 0
  count_ = 0
  has_refinement_ = 0

  def __init__(self, contents=None):
    self.refinement_ = FacetRefinement()
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

  def count(self): return self.count_

  def set_count(self, x):
    self.has_count_ = 1
    self.count_ = x

  def clear_count(self):
    if self.has_count_:
      self.has_count_ = 0
      self.count_ = 0

  def has_count(self): return self.has_count_

  def refinement(self): return self.refinement_

  def mutable_refinement(self): self.has_refinement_ = 1; return self.refinement_

  def clear_refinement(self):self.has_refinement_ = 0; self.refinement_.Clear()

  def has_refinement(self): return self.has_refinement_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())
    if (x.has_count()): self.set_count(x.count())
    if (x.has_refinement()): self.mutable_refinement().MergeFrom(x.refinement())

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if self.has_count_ != x.has_count_: return 0
    if self.has_count_ and self.count_ != x.count_: return 0
    if self.has_refinement_ != x.has_refinement_: return 0
    if self.has_refinement_ and self.refinement_ != x.refinement_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: name not set.')
    if (not self.has_count_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: count not set.')
    if (not self.has_refinement_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: refinement not set.')
    elif not self.refinement_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.name_))
    n += self.lengthVarInt64(self.count_)
    n += self.lengthString(self.refinement_.ByteSize())
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    if (self.has_count_):
      n += 1
      n += self.lengthVarInt64(self.count_)
    if (self.has_refinement_):
      n += 1
      n += self.lengthString(self.refinement_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_name()
    self.clear_count()
    self.clear_refinement()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.name_)
    out.putVarInt32(16)
    out.putVarInt32(self.count_)
    out.putVarInt32(26)
    out.putVarInt32(self.refinement_.ByteSize())
    self.refinement_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    if (self.has_count_):
      out.putVarInt32(16)
      out.putVarInt32(self.count_)
    if (self.has_refinement_):
      out.putVarInt32(26)
      out.putVarInt32(self.refinement_.ByteSizePartial())
      self.refinement_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_name(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_count(d.getVarInt32())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_refinement().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    if self.has_count_: res+=prefix+("count: %s\n" % self.DebugFormatInt32(self.count_))
    if self.has_refinement_:
      res+=prefix+"refinement <\n"
      res+=self.refinement_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 1
  kcount = 2
  krefinement = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name",
    2: "count",
    3: "refinement",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.FacetResultValue'
class FacetResult(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""

  def __init__(self, contents=None):
    self.value_ = []
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

  def value_size(self): return len(self.value_)
  def value_list(self): return self.value_

  def value(self, i):
    return self.value_[i]

  def mutable_value(self, i):
    return self.value_[i]

  def add_value(self):
    x = FacetResultValue()
    self.value_.append(x)
    return x

  def clear_value(self):
    self.value_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())
    for i in xrange(x.value_size()): self.add_value().CopyFrom(x.value(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if len(self.value_) != len(x.value_): return 0
    for e1, e2 in zip(self.value_, x.value_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: name not set.')
    for p in self.value_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.name_))
    n += 1 * len(self.value_)
    for i in xrange(len(self.value_)): n += self.lengthString(self.value_[i].ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    n += 1 * len(self.value_)
    for i in xrange(len(self.value_)): n += self.lengthString(self.value_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_name()
    self.clear_value()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.name_)
    for i in xrange(len(self.value_)):
      out.putVarInt32(18)
      out.putVarInt32(self.value_[i].ByteSize())
      self.value_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    for i in xrange(len(self.value_)):
      out.putVarInt32(18)
      out.putVarInt32(self.value_[i].ByteSizePartial())
      self.value_[i].OutputPartial(out)

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
        self.add_value().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    cnt=0
    for e in self.value_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("value%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.FacetResult'
class SearchResult(ProtocolBuffer.ProtocolMessage):
  has_document_ = 0
  has_cursor_ = 0
  cursor_ = ""

  def __init__(self, contents=None):
    self.document_ = Document()
    self.expression_ = []
    self.score_ = []
    if contents is not None: self.MergeFromString(contents)

  def document(self): return self.document_

  def mutable_document(self): self.has_document_ = 1; return self.document_

  def clear_document(self):self.has_document_ = 0; self.document_.Clear()

  def has_document(self): return self.has_document_

  def expression_size(self): return len(self.expression_)
  def expression_list(self): return self.expression_

  def expression(self, i):
    return self.expression_[i]

  def mutable_expression(self, i):
    return self.expression_[i]

  def add_expression(self):
    x = Field()
    self.expression_.append(x)
    return x

  def clear_expression(self):
    self.expression_ = []
  def score_size(self): return len(self.score_)
  def score_list(self): return self.score_

  def score(self, i):
    return self.score_[i]

  def set_score(self, i, x):
    self.score_[i] = x

  def add_score(self, x):
    self.score_.append(x)

  def clear_score(self):
    self.score_ = []

  def cursor(self): return self.cursor_

  def set_cursor(self, x):
    self.has_cursor_ = 1
    self.cursor_ = x

  def clear_cursor(self):
    if self.has_cursor_:
      self.has_cursor_ = 0
      self.cursor_ = ""

  def has_cursor(self): return self.has_cursor_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_document()): self.mutable_document().MergeFrom(x.document())
    for i in xrange(x.expression_size()): self.add_expression().CopyFrom(x.expression(i))
    for i in xrange(x.score_size()): self.add_score(x.score(i))
    if (x.has_cursor()): self.set_cursor(x.cursor())

  def Equals(self, x):
    if x is self: return 1
    if self.has_document_ != x.has_document_: return 0
    if self.has_document_ and self.document_ != x.document_: return 0
    if len(self.expression_) != len(x.expression_): return 0
    for e1, e2 in zip(self.expression_, x.expression_):
      if e1 != e2: return 0
    if len(self.score_) != len(x.score_): return 0
    for e1, e2 in zip(self.score_, x.score_):
      if e1 != e2: return 0
    if self.has_cursor_ != x.has_cursor_: return 0
    if self.has_cursor_ and self.cursor_ != x.cursor_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_document_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: document not set.')
    elif not self.document_.IsInitialized(debug_strs): initialized = 0
    for p in self.expression_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.document_.ByteSize())
    n += 1 * len(self.expression_)
    for i in xrange(len(self.expression_)): n += self.lengthString(self.expression_[i].ByteSize())
    n += 9 * len(self.score_)
    if (self.has_cursor_): n += 1 + self.lengthString(len(self.cursor_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_document_):
      n += 1
      n += self.lengthString(self.document_.ByteSizePartial())
    n += 1 * len(self.expression_)
    for i in xrange(len(self.expression_)): n += self.lengthString(self.expression_[i].ByteSizePartial())
    n += 9 * len(self.score_)
    if (self.has_cursor_): n += 1 + self.lengthString(len(self.cursor_))
    return n

  def Clear(self):
    self.clear_document()
    self.clear_expression()
    self.clear_score()
    self.clear_cursor()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.document_.ByteSize())
    self.document_.OutputUnchecked(out)
    for i in xrange(len(self.score_)):
      out.putVarInt32(17)
      out.putDouble(self.score_[i])
    if (self.has_cursor_):
      out.putVarInt32(26)
      out.putPrefixedString(self.cursor_)
    for i in xrange(len(self.expression_)):
      out.putVarInt32(34)
      out.putVarInt32(self.expression_[i].ByteSize())
      self.expression_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_document_):
      out.putVarInt32(10)
      out.putVarInt32(self.document_.ByteSizePartial())
      self.document_.OutputPartial(out)
    for i in xrange(len(self.score_)):
      out.putVarInt32(17)
      out.putDouble(self.score_[i])
    if (self.has_cursor_):
      out.putVarInt32(26)
      out.putPrefixedString(self.cursor_)
    for i in xrange(len(self.expression_)):
      out.putVarInt32(34)
      out.putVarInt32(self.expression_[i].ByteSizePartial())
      self.expression_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_document().TryMerge(tmp)
        continue
      if tt == 17:
        self.add_score(d.getDouble())
        continue
      if tt == 26:
        self.set_cursor(d.getPrefixedString())
        continue
      if tt == 34:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_expression().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_document_:
      res+=prefix+"document <\n"
      res+=self.document_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.expression_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("expression%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.score_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("score%s: %s\n" % (elm, self.DebugFormat(e)))
      cnt+=1
    if self.has_cursor_: res+=prefix+("cursor: %s\n" % self.DebugFormatString(self.cursor_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kdocument = 1
  kexpression = 4
  kscore = 2
  kcursor = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "document",
    2: "score",
    3: "cursor",
    4: "expression",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.DOUBLE,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SearchResult'
class SearchResponse(_ExtendableProtocolMessage):
  has_matched_count_ = 0
  matched_count_ = 0
  has_status_ = 0
  has_cursor_ = 0
  cursor_ = ""
  has_docs_scored_ = 0
  docs_scored_ = 0

  def __init__(self, contents=None):
    if _extension_runtime:
      self._extension_fields = {}
    self.result_ = []
    self.status_ = RequestStatus()
    self.facet_result_ = []
    if contents is not None: self.MergeFromString(contents)

  def result_size(self): return len(self.result_)
  def result_list(self): return self.result_

  def result(self, i):
    return self.result_[i]

  def mutable_result(self, i):
    return self.result_[i]

  def add_result(self):
    x = SearchResult()
    self.result_.append(x)
    return x

  def clear_result(self):
    self.result_ = []
  def matched_count(self): return self.matched_count_

  def set_matched_count(self, x):
    self.has_matched_count_ = 1
    self.matched_count_ = x

  def clear_matched_count(self):
    if self.has_matched_count_:
      self.has_matched_count_ = 0
      self.matched_count_ = 0

  def has_matched_count(self): return self.has_matched_count_

  def status(self): return self.status_

  def mutable_status(self): self.has_status_ = 1; return self.status_

  def clear_status(self):self.has_status_ = 0; self.status_.Clear()

  def has_status(self): return self.has_status_

  def cursor(self): return self.cursor_

  def set_cursor(self, x):
    self.has_cursor_ = 1
    self.cursor_ = x

  def clear_cursor(self):
    if self.has_cursor_:
      self.has_cursor_ = 0
      self.cursor_ = ""

  def has_cursor(self): return self.has_cursor_

  def facet_result_size(self): return len(self.facet_result_)
  def facet_result_list(self): return self.facet_result_

  def facet_result(self, i):
    return self.facet_result_[i]

  def mutable_facet_result(self, i):
    return self.facet_result_[i]

  def add_facet_result(self):
    x = FacetResult()
    self.facet_result_.append(x)
    return x

  def clear_facet_result(self):
    self.facet_result_ = []
  def docs_scored(self): return self.docs_scored_

  def set_docs_scored(self, x):
    self.has_docs_scored_ = 1
    self.docs_scored_ = x

  def clear_docs_scored(self):
    if self.has_docs_scored_:
      self.has_docs_scored_ = 0
      self.docs_scored_ = 0

  def has_docs_scored(self): return self.has_docs_scored_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.result_size()): self.add_result().CopyFrom(x.result(i))
    if (x.has_matched_count()): self.set_matched_count(x.matched_count())
    if (x.has_status()): self.mutable_status().MergeFrom(x.status())
    if (x.has_cursor()): self.set_cursor(x.cursor())
    for i in xrange(x.facet_result_size()): self.add_facet_result().CopyFrom(x.facet_result(i))
    if (x.has_docs_scored()): self.set_docs_scored(x.docs_scored())
    if _extension_runtime: self._MergeExtensionFields(x)

  def Equals(self, x):
    if x is self: return 1
    if len(self.result_) != len(x.result_): return 0
    for e1, e2 in zip(self.result_, x.result_):
      if e1 != e2: return 0
    if self.has_matched_count_ != x.has_matched_count_: return 0
    if self.has_matched_count_ and self.matched_count_ != x.matched_count_: return 0
    if self.has_status_ != x.has_status_: return 0
    if self.has_status_ and self.status_ != x.status_: return 0
    if self.has_cursor_ != x.has_cursor_: return 0
    if self.has_cursor_ and self.cursor_ != x.cursor_: return 0
    if len(self.facet_result_) != len(x.facet_result_): return 0
    for e1, e2 in zip(self.facet_result_, x.facet_result_):
      if e1 != e2: return 0
    if self.has_docs_scored_ != x.has_docs_scored_: return 0
    if self.has_docs_scored_ and self.docs_scored_ != x.docs_scored_: return 0
    if _extension_runtime and not self._ExtensionEquals(x): return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.result_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (not self.has_matched_count_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: matched_count not set.')
    if (not self.has_status_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: status not set.')
    elif not self.status_.IsInitialized(debug_strs): initialized = 0
    for p in self.facet_result_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.result_)
    for i in xrange(len(self.result_)): n += self.lengthString(self.result_[i].ByteSize())
    n += self.lengthVarInt64(self.matched_count_)
    n += self.lengthString(self.status_.ByteSize())
    if (self.has_cursor_): n += 1 + self.lengthString(len(self.cursor_))
    n += 1 * len(self.facet_result_)
    for i in xrange(len(self.facet_result_)): n += self.lengthString(self.facet_result_[i].ByteSize())
    if (self.has_docs_scored_): n += 1 + self.lengthVarInt64(self.docs_scored_)
    if _extension_runtime:
      n += self._ExtensionByteSize(False)
    return n + 2

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.result_)
    for i in xrange(len(self.result_)): n += self.lengthString(self.result_[i].ByteSizePartial())
    if (self.has_matched_count_):
      n += 1
      n += self.lengthVarInt64(self.matched_count_)
    if (self.has_status_):
      n += 1
      n += self.lengthString(self.status_.ByteSizePartial())
    if (self.has_cursor_): n += 1 + self.lengthString(len(self.cursor_))
    n += 1 * len(self.facet_result_)
    for i in xrange(len(self.facet_result_)): n += self.lengthString(self.facet_result_[i].ByteSizePartial())
    if (self.has_docs_scored_): n += 1 + self.lengthVarInt64(self.docs_scored_)
    if _extension_runtime:
      n += self._ExtensionByteSize(True)
    return n

  def Clear(self):
    self.clear_result()
    self.clear_matched_count()
    self.clear_status()
    self.clear_cursor()
    self.clear_facet_result()
    self.clear_docs_scored()
    if _extension_runtime: self._extension_fields.clear()

  def OutputUnchecked(self, out):
    if _extension_runtime:
      extensions = self._ListExtensions()
      extension_index = 0
    for i in xrange(len(self.result_)):
      out.putVarInt32(10)
      out.putVarInt32(self.result_[i].ByteSize())
      self.result_[i].OutputUnchecked(out)
    out.putVarInt32(16)
    out.putVarInt64(self.matched_count_)
    out.putVarInt32(26)
    out.putVarInt32(self.status_.ByteSize())
    self.status_.OutputUnchecked(out)
    if (self.has_cursor_):
      out.putVarInt32(34)
      out.putPrefixedString(self.cursor_)
    for i in xrange(len(self.facet_result_)):
      out.putVarInt32(42)
      out.putVarInt32(self.facet_result_[i].ByteSize())
      self.facet_result_[i].OutputUnchecked(out)
    if (self.has_docs_scored_):
      out.putVarInt32(48)
      out.putVarInt32(self.docs_scored_)
    if _extension_runtime:
      extension_index = self._OutputExtensionFields(out, False, extensions, extension_index, 10000)

  def OutputPartial(self, out):
    if _extension_runtime:
      extensions = self._ListExtensions()
      extension_index = 0
    for i in xrange(len(self.result_)):
      out.putVarInt32(10)
      out.putVarInt32(self.result_[i].ByteSizePartial())
      self.result_[i].OutputPartial(out)
    if (self.has_matched_count_):
      out.putVarInt32(16)
      out.putVarInt64(self.matched_count_)
    if (self.has_status_):
      out.putVarInt32(26)
      out.putVarInt32(self.status_.ByteSizePartial())
      self.status_.OutputPartial(out)
    if (self.has_cursor_):
      out.putVarInt32(34)
      out.putPrefixedString(self.cursor_)
    for i in xrange(len(self.facet_result_)):
      out.putVarInt32(42)
      out.putVarInt32(self.facet_result_[i].ByteSizePartial())
      self.facet_result_[i].OutputPartial(out)
    if (self.has_docs_scored_):
      out.putVarInt32(48)
      out.putVarInt32(self.docs_scored_)
    if _extension_runtime:
      extension_index = self._OutputExtensionFields(out, True, extensions, extension_index, 10000)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_result().TryMerge(tmp)
        continue
      if tt == 16:
        self.set_matched_count(d.getVarInt64())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_status().TryMerge(tmp)
        continue
      if tt == 34:
        self.set_cursor(d.getPrefixedString())
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_facet_result().TryMerge(tmp)
        continue
      if tt == 48:
        self.set_docs_scored(d.getVarInt32())
        continue
      if _extension_runtime:
        if (1000 <= tt and tt < 10000):
          self._ParseOneExtensionField(tt, d)
          continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.result_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("result%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_matched_count_: res+=prefix+("matched_count: %s\n" % self.DebugFormatInt64(self.matched_count_))
    if self.has_status_:
      res+=prefix+"status <\n"
      res+=self.status_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_cursor_: res+=prefix+("cursor: %s\n" % self.DebugFormatString(self.cursor_))
    cnt=0
    for e in self.facet_result_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("facet_result%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_docs_scored_: res+=prefix+("docs_scored: %s\n" % self.DebugFormatInt32(self.docs_scored_))
    if _extension_runtime:
      res+=self._ExtensionDebugString(prefix, printElemNumber)
    return res

  if _extension_runtime:
    _extensions_by_field_number = {}

  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kresult = 1
  kmatched_count = 2
  kstatus = 3
  kcursor = 4
  kfacet_result = 5
  kdocs_scored = 6

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "result",
    2: "matched_count",
    3: "status",
    4: "cursor",
    5: "facet_result",
    6: "docs_scored",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.NUMERIC,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SearchResponse'
if _extension_runtime:
  pass

__all__ = ['SearchServiceError','RequestStatus','IndexSpec','IndexMetadata_Storage','IndexMetadata','IndexDocumentParams','IndexDocumentRequest','IndexDocumentResponse','DeleteDocumentParams','DeleteDocumentRequest','DeleteDocumentResponse','ListDocumentsParams','ListDocumentsRequest','ListDocumentsResponse','DeleteIndexParams','DeleteIndexRequest','DeleteIndexResponse','CancelDeleteIndexParams','CancelDeleteIndexRequest','CancelDeleteIndexResponse','ListIndexesParams','ListIndexesRequest','ListIndexesResponse','DeleteSchemaParams','DeleteSchemaRequest','DeleteSchemaResponse','SortSpec','ScorerSpec','FieldSpec','FieldSpec_Expression','FacetRange','FacetRequestParam','FacetAutoDetectParam','FacetRequest','FacetRefinement_Range','FacetRefinement','SearchParams','SearchRequest','FacetResultValue','FacetResult','SearchResult','SearchResponse']
