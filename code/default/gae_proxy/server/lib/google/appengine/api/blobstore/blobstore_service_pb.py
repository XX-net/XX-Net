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
class BlobstoreServiceError(ProtocolBuffer.ProtocolMessage):


  OK           =    0
  INTERNAL_ERROR =    1
  URL_TOO_LONG =    2
  PERMISSION_DENIED =    3
  BLOB_NOT_FOUND =    4
  DATA_INDEX_OUT_OF_RANGE =    5
  BLOB_FETCH_SIZE_TOO_LARGE =    6
  ARGUMENT_OUT_OF_RANGE =    8
  INVALID_BLOB_KEY =    9

  _ErrorCode_NAMES = {
    0: "OK",
    1: "INTERNAL_ERROR",
    2: "URL_TOO_LONG",
    3: "PERMISSION_DENIED",
    4: "BLOB_NOT_FOUND",
    5: "DATA_INDEX_OUT_OF_RANGE",
    6: "BLOB_FETCH_SIZE_TOO_LARGE",
    8: "ARGUMENT_OUT_OF_RANGE",
    9: "INVALID_BLOB_KEY",
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.BlobstoreServiceError'
class CreateUploadURLRequest(ProtocolBuffer.ProtocolMessage):
  has_success_path_ = 0
  success_path_ = ""
  has_max_upload_size_bytes_ = 0
  max_upload_size_bytes_ = 0
  has_max_upload_size_per_blob_bytes_ = 0
  max_upload_size_per_blob_bytes_ = 0
  has_gs_bucket_name_ = 0
  gs_bucket_name_ = ""
  has_url_expiry_time_seconds_ = 0
  url_expiry_time_seconds_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def success_path(self): return self.success_path_

  def set_success_path(self, x):
    self.has_success_path_ = 1
    self.success_path_ = x

  def clear_success_path(self):
    if self.has_success_path_:
      self.has_success_path_ = 0
      self.success_path_ = ""

  def has_success_path(self): return self.has_success_path_

  def max_upload_size_bytes(self): return self.max_upload_size_bytes_

  def set_max_upload_size_bytes(self, x):
    self.has_max_upload_size_bytes_ = 1
    self.max_upload_size_bytes_ = x

  def clear_max_upload_size_bytes(self):
    if self.has_max_upload_size_bytes_:
      self.has_max_upload_size_bytes_ = 0
      self.max_upload_size_bytes_ = 0

  def has_max_upload_size_bytes(self): return self.has_max_upload_size_bytes_

  def max_upload_size_per_blob_bytes(self): return self.max_upload_size_per_blob_bytes_

  def set_max_upload_size_per_blob_bytes(self, x):
    self.has_max_upload_size_per_blob_bytes_ = 1
    self.max_upload_size_per_blob_bytes_ = x

  def clear_max_upload_size_per_blob_bytes(self):
    if self.has_max_upload_size_per_blob_bytes_:
      self.has_max_upload_size_per_blob_bytes_ = 0
      self.max_upload_size_per_blob_bytes_ = 0

  def has_max_upload_size_per_blob_bytes(self): return self.has_max_upload_size_per_blob_bytes_

  def gs_bucket_name(self): return self.gs_bucket_name_

  def set_gs_bucket_name(self, x):
    self.has_gs_bucket_name_ = 1
    self.gs_bucket_name_ = x

  def clear_gs_bucket_name(self):
    if self.has_gs_bucket_name_:
      self.has_gs_bucket_name_ = 0
      self.gs_bucket_name_ = ""

  def has_gs_bucket_name(self): return self.has_gs_bucket_name_

  def url_expiry_time_seconds(self): return self.url_expiry_time_seconds_

  def set_url_expiry_time_seconds(self, x):
    self.has_url_expiry_time_seconds_ = 1
    self.url_expiry_time_seconds_ = x

  def clear_url_expiry_time_seconds(self):
    if self.has_url_expiry_time_seconds_:
      self.has_url_expiry_time_seconds_ = 0
      self.url_expiry_time_seconds_ = 0

  def has_url_expiry_time_seconds(self): return self.has_url_expiry_time_seconds_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_success_path()): self.set_success_path(x.success_path())
    if (x.has_max_upload_size_bytes()): self.set_max_upload_size_bytes(x.max_upload_size_bytes())
    if (x.has_max_upload_size_per_blob_bytes()): self.set_max_upload_size_per_blob_bytes(x.max_upload_size_per_blob_bytes())
    if (x.has_gs_bucket_name()): self.set_gs_bucket_name(x.gs_bucket_name())
    if (x.has_url_expiry_time_seconds()): self.set_url_expiry_time_seconds(x.url_expiry_time_seconds())

  def Equals(self, x):
    if x is self: return 1
    if self.has_success_path_ != x.has_success_path_: return 0
    if self.has_success_path_ and self.success_path_ != x.success_path_: return 0
    if self.has_max_upload_size_bytes_ != x.has_max_upload_size_bytes_: return 0
    if self.has_max_upload_size_bytes_ and self.max_upload_size_bytes_ != x.max_upload_size_bytes_: return 0
    if self.has_max_upload_size_per_blob_bytes_ != x.has_max_upload_size_per_blob_bytes_: return 0
    if self.has_max_upload_size_per_blob_bytes_ and self.max_upload_size_per_blob_bytes_ != x.max_upload_size_per_blob_bytes_: return 0
    if self.has_gs_bucket_name_ != x.has_gs_bucket_name_: return 0
    if self.has_gs_bucket_name_ and self.gs_bucket_name_ != x.gs_bucket_name_: return 0
    if self.has_url_expiry_time_seconds_ != x.has_url_expiry_time_seconds_: return 0
    if self.has_url_expiry_time_seconds_ and self.url_expiry_time_seconds_ != x.url_expiry_time_seconds_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_success_path_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: success_path not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.success_path_))
    if (self.has_max_upload_size_bytes_): n += 1 + self.lengthVarInt64(self.max_upload_size_bytes_)
    if (self.has_max_upload_size_per_blob_bytes_): n += 1 + self.lengthVarInt64(self.max_upload_size_per_blob_bytes_)
    if (self.has_gs_bucket_name_): n += 1 + self.lengthString(len(self.gs_bucket_name_))
    if (self.has_url_expiry_time_seconds_): n += 1 + self.lengthVarInt64(self.url_expiry_time_seconds_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_success_path_):
      n += 1
      n += self.lengthString(len(self.success_path_))
    if (self.has_max_upload_size_bytes_): n += 1 + self.lengthVarInt64(self.max_upload_size_bytes_)
    if (self.has_max_upload_size_per_blob_bytes_): n += 1 + self.lengthVarInt64(self.max_upload_size_per_blob_bytes_)
    if (self.has_gs_bucket_name_): n += 1 + self.lengthString(len(self.gs_bucket_name_))
    if (self.has_url_expiry_time_seconds_): n += 1 + self.lengthVarInt64(self.url_expiry_time_seconds_)
    return n

  def Clear(self):
    self.clear_success_path()
    self.clear_max_upload_size_bytes()
    self.clear_max_upload_size_per_blob_bytes()
    self.clear_gs_bucket_name()
    self.clear_url_expiry_time_seconds()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.success_path_)
    if (self.has_max_upload_size_bytes_):
      out.putVarInt32(16)
      out.putVarInt64(self.max_upload_size_bytes_)
    if (self.has_max_upload_size_per_blob_bytes_):
      out.putVarInt32(24)
      out.putVarInt64(self.max_upload_size_per_blob_bytes_)
    if (self.has_gs_bucket_name_):
      out.putVarInt32(34)
      out.putPrefixedString(self.gs_bucket_name_)
    if (self.has_url_expiry_time_seconds_):
      out.putVarInt32(40)
      out.putVarInt32(self.url_expiry_time_seconds_)

  def OutputPartial(self, out):
    if (self.has_success_path_):
      out.putVarInt32(10)
      out.putPrefixedString(self.success_path_)
    if (self.has_max_upload_size_bytes_):
      out.putVarInt32(16)
      out.putVarInt64(self.max_upload_size_bytes_)
    if (self.has_max_upload_size_per_blob_bytes_):
      out.putVarInt32(24)
      out.putVarInt64(self.max_upload_size_per_blob_bytes_)
    if (self.has_gs_bucket_name_):
      out.putVarInt32(34)
      out.putPrefixedString(self.gs_bucket_name_)
    if (self.has_url_expiry_time_seconds_):
      out.putVarInt32(40)
      out.putVarInt32(self.url_expiry_time_seconds_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_success_path(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_max_upload_size_bytes(d.getVarInt64())
        continue
      if tt == 24:
        self.set_max_upload_size_per_blob_bytes(d.getVarInt64())
        continue
      if tt == 34:
        self.set_gs_bucket_name(d.getPrefixedString())
        continue
      if tt == 40:
        self.set_url_expiry_time_seconds(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_success_path_: res+=prefix+("success_path: %s\n" % self.DebugFormatString(self.success_path_))
    if self.has_max_upload_size_bytes_: res+=prefix+("max_upload_size_bytes: %s\n" % self.DebugFormatInt64(self.max_upload_size_bytes_))
    if self.has_max_upload_size_per_blob_bytes_: res+=prefix+("max_upload_size_per_blob_bytes: %s\n" % self.DebugFormatInt64(self.max_upload_size_per_blob_bytes_))
    if self.has_gs_bucket_name_: res+=prefix+("gs_bucket_name: %s\n" % self.DebugFormatString(self.gs_bucket_name_))
    if self.has_url_expiry_time_seconds_: res+=prefix+("url_expiry_time_seconds: %s\n" % self.DebugFormatInt32(self.url_expiry_time_seconds_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksuccess_path = 1
  kmax_upload_size_bytes = 2
  kmax_upload_size_per_blob_bytes = 3
  kgs_bucket_name = 4
  kurl_expiry_time_seconds = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "success_path",
    2: "max_upload_size_bytes",
    3: "max_upload_size_per_blob_bytes",
    4: "gs_bucket_name",
    5: "url_expiry_time_seconds",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.NUMERIC,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CreateUploadURLRequest'
class CreateUploadURLResponse(ProtocolBuffer.ProtocolMessage):
  has_url_ = 0
  url_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def url(self): return self.url_

  def set_url(self, x):
    self.has_url_ = 1
    self.url_ = x

  def clear_url(self):
    if self.has_url_:
      self.has_url_ = 0
      self.url_ = ""

  def has_url(self): return self.has_url_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_url()): self.set_url(x.url())

  def Equals(self, x):
    if x is self: return 1
    if self.has_url_ != x.has_url_: return 0
    if self.has_url_ and self.url_ != x.url_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_url_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: url not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.url_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_url_):
      n += 1
      n += self.lengthString(len(self.url_))
    return n

  def Clear(self):
    self.clear_url()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.url_)

  def OutputPartial(self, out):
    if (self.has_url_):
      out.putVarInt32(10)
      out.putPrefixedString(self.url_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_url(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_url_: res+=prefix+("url: %s\n" % self.DebugFormatString(self.url_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kurl = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "url",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CreateUploadURLResponse'
class DeleteBlobRequest(ProtocolBuffer.ProtocolMessage):
  has_token_ = 0
  token_ = ""

  def __init__(self, contents=None):
    self.blob_key_ = []
    if contents is not None: self.MergeFromString(contents)

  def blob_key_size(self): return len(self.blob_key_)
  def blob_key_list(self): return self.blob_key_

  def blob_key(self, i):
    return self.blob_key_[i]

  def set_blob_key(self, i, x):
    self.blob_key_[i] = x

  def add_blob_key(self, x):
    self.blob_key_.append(x)

  def clear_blob_key(self):
    self.blob_key_ = []

  def token(self): return self.token_

  def set_token(self, x):
    self.has_token_ = 1
    self.token_ = x

  def clear_token(self):
    if self.has_token_:
      self.has_token_ = 0
      self.token_ = ""

  def has_token(self): return self.has_token_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.blob_key_size()): self.add_blob_key(x.blob_key(i))
    if (x.has_token()): self.set_token(x.token())

  def Equals(self, x):
    if x is self: return 1
    if len(self.blob_key_) != len(x.blob_key_): return 0
    for e1, e2 in zip(self.blob_key_, x.blob_key_):
      if e1 != e2: return 0
    if self.has_token_ != x.has_token_: return 0
    if self.has_token_ and self.token_ != x.token_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.blob_key_)
    for i in xrange(len(self.blob_key_)): n += self.lengthString(len(self.blob_key_[i]))
    if (self.has_token_): n += 1 + self.lengthString(len(self.token_))
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.blob_key_)
    for i in xrange(len(self.blob_key_)): n += self.lengthString(len(self.blob_key_[i]))
    if (self.has_token_): n += 1 + self.lengthString(len(self.token_))
    return n

  def Clear(self):
    self.clear_blob_key()
    self.clear_token()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.blob_key_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.blob_key_[i])
    if (self.has_token_):
      out.putVarInt32(18)
      out.putPrefixedString(self.token_)

  def OutputPartial(self, out):
    for i in xrange(len(self.blob_key_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.blob_key_[i])
    if (self.has_token_):
      out.putVarInt32(18)
      out.putPrefixedString(self.token_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.add_blob_key(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_token(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.blob_key_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("blob_key%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_token_: res+=prefix+("token: %s\n" % self.DebugFormatString(self.token_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kblob_key = 1
  ktoken = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "blob_key",
    2: "token",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.DeleteBlobRequest'
class FetchDataRequest(ProtocolBuffer.ProtocolMessage):
  has_blob_key_ = 0
  blob_key_ = ""
  has_start_index_ = 0
  start_index_ = 0
  has_end_index_ = 0
  end_index_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def blob_key(self): return self.blob_key_

  def set_blob_key(self, x):
    self.has_blob_key_ = 1
    self.blob_key_ = x

  def clear_blob_key(self):
    if self.has_blob_key_:
      self.has_blob_key_ = 0
      self.blob_key_ = ""

  def has_blob_key(self): return self.has_blob_key_

  def start_index(self): return self.start_index_

  def set_start_index(self, x):
    self.has_start_index_ = 1
    self.start_index_ = x

  def clear_start_index(self):
    if self.has_start_index_:
      self.has_start_index_ = 0
      self.start_index_ = 0

  def has_start_index(self): return self.has_start_index_

  def end_index(self): return self.end_index_

  def set_end_index(self, x):
    self.has_end_index_ = 1
    self.end_index_ = x

  def clear_end_index(self):
    if self.has_end_index_:
      self.has_end_index_ = 0
      self.end_index_ = 0

  def has_end_index(self): return self.has_end_index_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_blob_key()): self.set_blob_key(x.blob_key())
    if (x.has_start_index()): self.set_start_index(x.start_index())
    if (x.has_end_index()): self.set_end_index(x.end_index())

  def Equals(self, x):
    if x is self: return 1
    if self.has_blob_key_ != x.has_blob_key_: return 0
    if self.has_blob_key_ and self.blob_key_ != x.blob_key_: return 0
    if self.has_start_index_ != x.has_start_index_: return 0
    if self.has_start_index_ and self.start_index_ != x.start_index_: return 0
    if self.has_end_index_ != x.has_end_index_: return 0
    if self.has_end_index_ and self.end_index_ != x.end_index_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_blob_key_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: blob_key not set.')
    if (not self.has_start_index_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: start_index not set.')
    if (not self.has_end_index_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: end_index not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.blob_key_))
    n += self.lengthVarInt64(self.start_index_)
    n += self.lengthVarInt64(self.end_index_)
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_blob_key_):
      n += 1
      n += self.lengthString(len(self.blob_key_))
    if (self.has_start_index_):
      n += 1
      n += self.lengthVarInt64(self.start_index_)
    if (self.has_end_index_):
      n += 1
      n += self.lengthVarInt64(self.end_index_)
    return n

  def Clear(self):
    self.clear_blob_key()
    self.clear_start_index()
    self.clear_end_index()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.blob_key_)
    out.putVarInt32(16)
    out.putVarInt64(self.start_index_)
    out.putVarInt32(24)
    out.putVarInt64(self.end_index_)

  def OutputPartial(self, out):
    if (self.has_blob_key_):
      out.putVarInt32(10)
      out.putPrefixedString(self.blob_key_)
    if (self.has_start_index_):
      out.putVarInt32(16)
      out.putVarInt64(self.start_index_)
    if (self.has_end_index_):
      out.putVarInt32(24)
      out.putVarInt64(self.end_index_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_blob_key(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_start_index(d.getVarInt64())
        continue
      if tt == 24:
        self.set_end_index(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_blob_key_: res+=prefix+("blob_key: %s\n" % self.DebugFormatString(self.blob_key_))
    if self.has_start_index_: res+=prefix+("start_index: %s\n" % self.DebugFormatInt64(self.start_index_))
    if self.has_end_index_: res+=prefix+("end_index: %s\n" % self.DebugFormatInt64(self.end_index_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kblob_key = 1
  kstart_index = 2
  kend_index = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "blob_key",
    2: "start_index",
    3: "end_index",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.FetchDataRequest'
class FetchDataResponse(ProtocolBuffer.ProtocolMessage):
  has_data_ = 0
  data_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def data(self): return self.data_

  def set_data(self, x):
    self.has_data_ = 1
    self.data_ = x

  def clear_data(self):
    if self.has_data_:
      self.has_data_ = 0
      self.data_ = ""

  def has_data(self): return self.has_data_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_data()): self.set_data(x.data())

  def Equals(self, x):
    if x is self: return 1
    if self.has_data_ != x.has_data_: return 0
    if self.has_data_ and self.data_ != x.data_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_data_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: data not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.data_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_data_):
      n += 2
      n += self.lengthString(len(self.data_))
    return n

  def Clear(self):
    self.clear_data()

  def OutputUnchecked(self, out):
    out.putVarInt32(8002)
    out.putPrefixedString(self.data_)

  def OutputPartial(self, out):
    if (self.has_data_):
      out.putVarInt32(8002)
      out.putPrefixedString(self.data_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8002:
        self.set_data(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_data_: res+=prefix+("data: %s\n" % self.DebugFormatString(self.data_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kdata = 1000

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1000: "data",
  }, 1000)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1000: ProtocolBuffer.Encoder.STRING,
  }, 1000, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.FetchDataResponse'
class CloneBlobRequest(ProtocolBuffer.ProtocolMessage):
  has_blob_key_ = 0
  blob_key_ = ""
  has_mime_type_ = 0
  mime_type_ = ""
  has_target_app_id_ = 0
  target_app_id_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def blob_key(self): return self.blob_key_

  def set_blob_key(self, x):
    self.has_blob_key_ = 1
    self.blob_key_ = x

  def clear_blob_key(self):
    if self.has_blob_key_:
      self.has_blob_key_ = 0
      self.blob_key_ = ""

  def has_blob_key(self): return self.has_blob_key_

  def mime_type(self): return self.mime_type_

  def set_mime_type(self, x):
    self.has_mime_type_ = 1
    self.mime_type_ = x

  def clear_mime_type(self):
    if self.has_mime_type_:
      self.has_mime_type_ = 0
      self.mime_type_ = ""

  def has_mime_type(self): return self.has_mime_type_

  def target_app_id(self): return self.target_app_id_

  def set_target_app_id(self, x):
    self.has_target_app_id_ = 1
    self.target_app_id_ = x

  def clear_target_app_id(self):
    if self.has_target_app_id_:
      self.has_target_app_id_ = 0
      self.target_app_id_ = ""

  def has_target_app_id(self): return self.has_target_app_id_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_blob_key()): self.set_blob_key(x.blob_key())
    if (x.has_mime_type()): self.set_mime_type(x.mime_type())
    if (x.has_target_app_id()): self.set_target_app_id(x.target_app_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_blob_key_ != x.has_blob_key_: return 0
    if self.has_blob_key_ and self.blob_key_ != x.blob_key_: return 0
    if self.has_mime_type_ != x.has_mime_type_: return 0
    if self.has_mime_type_ and self.mime_type_ != x.mime_type_: return 0
    if self.has_target_app_id_ != x.has_target_app_id_: return 0
    if self.has_target_app_id_ and self.target_app_id_ != x.target_app_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_blob_key_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: blob_key not set.')
    if (not self.has_mime_type_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: mime_type not set.')
    if (not self.has_target_app_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: target_app_id not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.blob_key_))
    n += self.lengthString(len(self.mime_type_))
    n += self.lengthString(len(self.target_app_id_))
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_blob_key_):
      n += 1
      n += self.lengthString(len(self.blob_key_))
    if (self.has_mime_type_):
      n += 1
      n += self.lengthString(len(self.mime_type_))
    if (self.has_target_app_id_):
      n += 1
      n += self.lengthString(len(self.target_app_id_))
    return n

  def Clear(self):
    self.clear_blob_key()
    self.clear_mime_type()
    self.clear_target_app_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.blob_key_)
    out.putVarInt32(18)
    out.putPrefixedString(self.mime_type_)
    out.putVarInt32(26)
    out.putPrefixedString(self.target_app_id_)

  def OutputPartial(self, out):
    if (self.has_blob_key_):
      out.putVarInt32(10)
      out.putPrefixedString(self.blob_key_)
    if (self.has_mime_type_):
      out.putVarInt32(18)
      out.putPrefixedString(self.mime_type_)
    if (self.has_target_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.target_app_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_blob_key(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_mime_type(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_target_app_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_blob_key_: res+=prefix+("blob_key: %s\n" % self.DebugFormatString(self.blob_key_))
    if self.has_mime_type_: res+=prefix+("mime_type: %s\n" % self.DebugFormatString(self.mime_type_))
    if self.has_target_app_id_: res+=prefix+("target_app_id: %s\n" % self.DebugFormatString(self.target_app_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kblob_key = 1
  kmime_type = 2
  ktarget_app_id = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "blob_key",
    2: "mime_type",
    3: "target_app_id",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CloneBlobRequest'
class CloneBlobResponse(ProtocolBuffer.ProtocolMessage):
  has_blob_key_ = 0
  blob_key_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def blob_key(self): return self.blob_key_

  def set_blob_key(self, x):
    self.has_blob_key_ = 1
    self.blob_key_ = x

  def clear_blob_key(self):
    if self.has_blob_key_:
      self.has_blob_key_ = 0
      self.blob_key_ = ""

  def has_blob_key(self): return self.has_blob_key_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_blob_key()): self.set_blob_key(x.blob_key())

  def Equals(self, x):
    if x is self: return 1
    if self.has_blob_key_ != x.has_blob_key_: return 0
    if self.has_blob_key_ and self.blob_key_ != x.blob_key_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_blob_key_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: blob_key not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.blob_key_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_blob_key_):
      n += 1
      n += self.lengthString(len(self.blob_key_))
    return n

  def Clear(self):
    self.clear_blob_key()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.blob_key_)

  def OutputPartial(self, out):
    if (self.has_blob_key_):
      out.putVarInt32(10)
      out.putPrefixedString(self.blob_key_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_blob_key(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_blob_key_: res+=prefix+("blob_key: %s\n" % self.DebugFormatString(self.blob_key_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kblob_key = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "blob_key",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CloneBlobResponse'
class DecodeBlobKeyRequest(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.blob_key_ = []
    if contents is not None: self.MergeFromString(contents)

  def blob_key_size(self): return len(self.blob_key_)
  def blob_key_list(self): return self.blob_key_

  def blob_key(self, i):
    return self.blob_key_[i]

  def set_blob_key(self, i, x):
    self.blob_key_[i] = x

  def add_blob_key(self, x):
    self.blob_key_.append(x)

  def clear_blob_key(self):
    self.blob_key_ = []


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.blob_key_size()): self.add_blob_key(x.blob_key(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.blob_key_) != len(x.blob_key_): return 0
    for e1, e2 in zip(self.blob_key_, x.blob_key_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.blob_key_)
    for i in xrange(len(self.blob_key_)): n += self.lengthString(len(self.blob_key_[i]))
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.blob_key_)
    for i in xrange(len(self.blob_key_)): n += self.lengthString(len(self.blob_key_[i]))
    return n

  def Clear(self):
    self.clear_blob_key()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.blob_key_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.blob_key_[i])

  def OutputPartial(self, out):
    for i in xrange(len(self.blob_key_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.blob_key_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.add_blob_key(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.blob_key_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("blob_key%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kblob_key = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "blob_key",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.DecodeBlobKeyRequest'
class DecodeBlobKeyResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.decoded_ = []
    if contents is not None: self.MergeFromString(contents)

  def decoded_size(self): return len(self.decoded_)
  def decoded_list(self): return self.decoded_

  def decoded(self, i):
    return self.decoded_[i]

  def set_decoded(self, i, x):
    self.decoded_[i] = x

  def add_decoded(self, x):
    self.decoded_.append(x)

  def clear_decoded(self):
    self.decoded_ = []


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.decoded_size()): self.add_decoded(x.decoded(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.decoded_) != len(x.decoded_): return 0
    for e1, e2 in zip(self.decoded_, x.decoded_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.decoded_)
    for i in xrange(len(self.decoded_)): n += self.lengthString(len(self.decoded_[i]))
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.decoded_)
    for i in xrange(len(self.decoded_)): n += self.lengthString(len(self.decoded_[i]))
    return n

  def Clear(self):
    self.clear_decoded()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.decoded_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.decoded_[i])

  def OutputPartial(self, out):
    for i in xrange(len(self.decoded_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.decoded_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.add_decoded(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.decoded_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("decoded%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kdecoded = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "decoded",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.DecodeBlobKeyResponse'
class CreateEncodedGoogleStorageKeyRequest(ProtocolBuffer.ProtocolMessage):
  has_filename_ = 0
  filename_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def filename(self): return self.filename_

  def set_filename(self, x):
    self.has_filename_ = 1
    self.filename_ = x

  def clear_filename(self):
    if self.has_filename_:
      self.has_filename_ = 0
      self.filename_ = ""

  def has_filename(self): return self.has_filename_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_filename()): self.set_filename(x.filename())

  def Equals(self, x):
    if x is self: return 1
    if self.has_filename_ != x.has_filename_: return 0
    if self.has_filename_ and self.filename_ != x.filename_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_filename_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: filename not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.filename_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_filename_):
      n += 1
      n += self.lengthString(len(self.filename_))
    return n

  def Clear(self):
    self.clear_filename()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.filename_)

  def OutputPartial(self, out):
    if (self.has_filename_):
      out.putVarInt32(10)
      out.putPrefixedString(self.filename_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_filename(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_filename_: res+=prefix+("filename: %s\n" % self.DebugFormatString(self.filename_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kfilename = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "filename",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CreateEncodedGoogleStorageKeyRequest'
class CreateEncodedGoogleStorageKeyResponse(ProtocolBuffer.ProtocolMessage):
  has_blob_key_ = 0
  blob_key_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def blob_key(self): return self.blob_key_

  def set_blob_key(self, x):
    self.has_blob_key_ = 1
    self.blob_key_ = x

  def clear_blob_key(self):
    if self.has_blob_key_:
      self.has_blob_key_ = 0
      self.blob_key_ = ""

  def has_blob_key(self): return self.has_blob_key_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_blob_key()): self.set_blob_key(x.blob_key())

  def Equals(self, x):
    if x is self: return 1
    if self.has_blob_key_ != x.has_blob_key_: return 0
    if self.has_blob_key_ and self.blob_key_ != x.blob_key_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_blob_key_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: blob_key not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.blob_key_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_blob_key_):
      n += 1
      n += self.lengthString(len(self.blob_key_))
    return n

  def Clear(self):
    self.clear_blob_key()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.blob_key_)

  def OutputPartial(self, out):
    if (self.has_blob_key_):
      out.putVarInt32(10)
      out.putPrefixedString(self.blob_key_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_blob_key(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_blob_key_: res+=prefix+("blob_key: %s\n" % self.DebugFormatString(self.blob_key_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kblob_key = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "blob_key",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CreateEncodedGoogleStorageKeyResponse'
if _extension_runtime:
  pass

__all__ = ['BlobstoreServiceError','CreateUploadURLRequest','CreateUploadURLResponse','DeleteBlobRequest','FetchDataRequest','FetchDataResponse','CloneBlobRequest','CloneBlobResponse','DecodeBlobKeyRequest','DecodeBlobKeyResponse','CreateEncodedGoogleStorageKeyRequest','CreateEncodedGoogleStorageKeyResponse']
