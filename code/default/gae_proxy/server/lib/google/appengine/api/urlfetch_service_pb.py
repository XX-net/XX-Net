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

class URLFetchServiceError(ProtocolBuffer.ProtocolMessage):


  OK           =    0
  INVALID_URL  =    1
  FETCH_ERROR  =    2
  UNSPECIFIED_ERROR =    3
  RESPONSE_TOO_LARGE =    4
  DEADLINE_EXCEEDED =    5
  SSL_CERTIFICATE_ERROR =    6
  DNS_ERROR    =    7
  CLOSED       =    8
  INTERNAL_TRANSIENT_ERROR =    9
  TOO_MANY_REDIRECTS =   10
  MALFORMED_REPLY =   11
  CONNECTION_ERROR =   12
  PAYLOAD_TOO_LARGE =   13

  _ErrorCode_NAMES = {
    0: "OK",
    1: "INVALID_URL",
    2: "FETCH_ERROR",
    3: "UNSPECIFIED_ERROR",
    4: "RESPONSE_TOO_LARGE",
    5: "DEADLINE_EXCEEDED",
    6: "SSL_CERTIFICATE_ERROR",
    7: "DNS_ERROR",
    8: "CLOSED",
    9: "INTERNAL_TRANSIENT_ERROR",
    10: "TOO_MANY_REDIRECTS",
    11: "MALFORMED_REPLY",
    12: "CONNECTION_ERROR",
    13: "PAYLOAD_TOO_LARGE",
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.URLFetchServiceError'
class URLFetchRequest_Header(ProtocolBuffer.ProtocolMessage):
  has_key_ = 0
  key_ = ""
  has_value_ = 0
  value_ = ""

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


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_key()): self.set_key(x.key())
    if (x.has_value()): self.set_value(x.value())

  def Equals(self, x):
    if x is self: return 1
    if self.has_key_ != x.has_key_: return 0
    if self.has_key_ and self.key_ != x.key_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
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
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_key_):
      n += 1
      n += self.lengthString(len(self.key_))
    if (self.has_value_):
      n += 1
      n += self.lengthString(len(self.value_))
    return n

  def Clear(self):
    self.clear_key()
    self.clear_value()

  def OutputUnchecked(self, out):
    out.putVarInt32(34)
    out.putPrefixedString(self.key_)
    out.putVarInt32(42)
    out.putPrefixedString(self.value_)

  def OutputPartial(self, out):
    if (self.has_key_):
      out.putVarInt32(34)
      out.putPrefixedString(self.key_)
    if (self.has_value_):
      out.putVarInt32(42)
      out.putPrefixedString(self.value_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 28: break
      if tt == 34:
        self.set_key(d.getPrefixedString())
        continue
      if tt == 42:
        self.set_value(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_: res+=prefix+("Key: %s\n" % self.DebugFormatString(self.key_))
    if self.has_value_: res+=prefix+("Value: %s\n" % self.DebugFormatString(self.value_))
    return res

class URLFetchRequest(ProtocolBuffer.ProtocolMessage):


  GET          =    1
  POST         =    2
  HEAD         =    3
  PUT          =    4
  DELETE       =    5
  PATCH        =    6

  _RequestMethod_NAMES = {
    1: "GET",
    2: "POST",
    3: "HEAD",
    4: "PUT",
    5: "DELETE",
    6: "PATCH",
  }

  def RequestMethod_Name(cls, x): return cls._RequestMethod_NAMES.get(x, "")
  RequestMethod_Name = classmethod(RequestMethod_Name)

  has_method_ = 0
  method_ = 0
  has_url_ = 0
  url_ = ""
  has_payload_ = 0
  payload_ = ""
  has_followredirects_ = 0
  followredirects_ = 1
  has_deadline_ = 0
  deadline_ = 0.0
  has_mustvalidateservercertificate_ = 0
  mustvalidateservercertificate_ = 1

  def __init__(self, contents=None):
    self.header_ = []
    if contents is not None: self.MergeFromString(contents)

  def method(self): return self.method_

  def set_method(self, x):
    self.has_method_ = 1
    self.method_ = x

  def clear_method(self):
    if self.has_method_:
      self.has_method_ = 0
      self.method_ = 0

  def has_method(self): return self.has_method_

  def url(self): return self.url_

  def set_url(self, x):
    self.has_url_ = 1
    self.url_ = x

  def clear_url(self):
    if self.has_url_:
      self.has_url_ = 0
      self.url_ = ""

  def has_url(self): return self.has_url_

  def header_size(self): return len(self.header_)
  def header_list(self): return self.header_

  def header(self, i):
    return self.header_[i]

  def mutable_header(self, i):
    return self.header_[i]

  def add_header(self):
    x = URLFetchRequest_Header()
    self.header_.append(x)
    return x

  def clear_header(self):
    self.header_ = []
  def payload(self): return self.payload_

  def set_payload(self, x):
    self.has_payload_ = 1
    self.payload_ = x

  def clear_payload(self):
    if self.has_payload_:
      self.has_payload_ = 0
      self.payload_ = ""

  def has_payload(self): return self.has_payload_

  def followredirects(self): return self.followredirects_

  def set_followredirects(self, x):
    self.has_followredirects_ = 1
    self.followredirects_ = x

  def clear_followredirects(self):
    if self.has_followredirects_:
      self.has_followredirects_ = 0
      self.followredirects_ = 1

  def has_followredirects(self): return self.has_followredirects_

  def deadline(self): return self.deadline_

  def set_deadline(self, x):
    self.has_deadline_ = 1
    self.deadline_ = x

  def clear_deadline(self):
    if self.has_deadline_:
      self.has_deadline_ = 0
      self.deadline_ = 0.0

  def has_deadline(self): return self.has_deadline_

  def mustvalidateservercertificate(self): return self.mustvalidateservercertificate_

  def set_mustvalidateservercertificate(self, x):
    self.has_mustvalidateservercertificate_ = 1
    self.mustvalidateservercertificate_ = x

  def clear_mustvalidateservercertificate(self):
    if self.has_mustvalidateservercertificate_:
      self.has_mustvalidateservercertificate_ = 0
      self.mustvalidateservercertificate_ = 1

  def has_mustvalidateservercertificate(self): return self.has_mustvalidateservercertificate_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_method()): self.set_method(x.method())
    if (x.has_url()): self.set_url(x.url())
    for i in xrange(x.header_size()): self.add_header().CopyFrom(x.header(i))
    if (x.has_payload()): self.set_payload(x.payload())
    if (x.has_followredirects()): self.set_followredirects(x.followredirects())
    if (x.has_deadline()): self.set_deadline(x.deadline())
    if (x.has_mustvalidateservercertificate()): self.set_mustvalidateservercertificate(x.mustvalidateservercertificate())

  def Equals(self, x):
    if x is self: return 1
    if self.has_method_ != x.has_method_: return 0
    if self.has_method_ and self.method_ != x.method_: return 0
    if self.has_url_ != x.has_url_: return 0
    if self.has_url_ and self.url_ != x.url_: return 0
    if len(self.header_) != len(x.header_): return 0
    for e1, e2 in zip(self.header_, x.header_):
      if e1 != e2: return 0
    if self.has_payload_ != x.has_payload_: return 0
    if self.has_payload_ and self.payload_ != x.payload_: return 0
    if self.has_followredirects_ != x.has_followredirects_: return 0
    if self.has_followredirects_ and self.followredirects_ != x.followredirects_: return 0
    if self.has_deadline_ != x.has_deadline_: return 0
    if self.has_deadline_ and self.deadline_ != x.deadline_: return 0
    if self.has_mustvalidateservercertificate_ != x.has_mustvalidateservercertificate_: return 0
    if self.has_mustvalidateservercertificate_ and self.mustvalidateservercertificate_ != x.mustvalidateservercertificate_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_method_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: method not set.')
    if (not self.has_url_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: url not set.')
    for p in self.header_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.method_)
    n += self.lengthString(len(self.url_))
    n += 2 * len(self.header_)
    for i in xrange(len(self.header_)): n += self.header_[i].ByteSize()
    if (self.has_payload_): n += 1 + self.lengthString(len(self.payload_))
    if (self.has_followredirects_): n += 2
    if (self.has_deadline_): n += 9
    if (self.has_mustvalidateservercertificate_): n += 2
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_method_):
      n += 1
      n += self.lengthVarInt64(self.method_)
    if (self.has_url_):
      n += 1
      n += self.lengthString(len(self.url_))
    n += 2 * len(self.header_)
    for i in xrange(len(self.header_)): n += self.header_[i].ByteSizePartial()
    if (self.has_payload_): n += 1 + self.lengthString(len(self.payload_))
    if (self.has_followredirects_): n += 2
    if (self.has_deadline_): n += 9
    if (self.has_mustvalidateservercertificate_): n += 2
    return n

  def Clear(self):
    self.clear_method()
    self.clear_url()
    self.clear_header()
    self.clear_payload()
    self.clear_followredirects()
    self.clear_deadline()
    self.clear_mustvalidateservercertificate()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt32(self.method_)
    out.putVarInt32(18)
    out.putPrefixedString(self.url_)
    for i in xrange(len(self.header_)):
      out.putVarInt32(27)
      self.header_[i].OutputUnchecked(out)
      out.putVarInt32(28)
    if (self.has_payload_):
      out.putVarInt32(50)
      out.putPrefixedString(self.payload_)
    if (self.has_followredirects_):
      out.putVarInt32(56)
      out.putBoolean(self.followredirects_)
    if (self.has_deadline_):
      out.putVarInt32(65)
      out.putDouble(self.deadline_)
    if (self.has_mustvalidateservercertificate_):
      out.putVarInt32(72)
      out.putBoolean(self.mustvalidateservercertificate_)

  def OutputPartial(self, out):
    if (self.has_method_):
      out.putVarInt32(8)
      out.putVarInt32(self.method_)
    if (self.has_url_):
      out.putVarInt32(18)
      out.putPrefixedString(self.url_)
    for i in xrange(len(self.header_)):
      out.putVarInt32(27)
      self.header_[i].OutputPartial(out)
      out.putVarInt32(28)
    if (self.has_payload_):
      out.putVarInt32(50)
      out.putPrefixedString(self.payload_)
    if (self.has_followredirects_):
      out.putVarInt32(56)
      out.putBoolean(self.followredirects_)
    if (self.has_deadline_):
      out.putVarInt32(65)
      out.putDouble(self.deadline_)
    if (self.has_mustvalidateservercertificate_):
      out.putVarInt32(72)
      out.putBoolean(self.mustvalidateservercertificate_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_method(d.getVarInt32())
        continue
      if tt == 18:
        self.set_url(d.getPrefixedString())
        continue
      if tt == 27:
        self.add_header().TryMerge(d)
        continue
      if tt == 50:
        self.set_payload(d.getPrefixedString())
        continue
      if tt == 56:
        self.set_followredirects(d.getBoolean())
        continue
      if tt == 65:
        self.set_deadline(d.getDouble())
        continue
      if tt == 72:
        self.set_mustvalidateservercertificate(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_method_: res+=prefix+("Method: %s\n" % self.DebugFormatInt32(self.method_))
    if self.has_url_: res+=prefix+("Url: %s\n" % self.DebugFormatString(self.url_))
    cnt=0
    for e in self.header_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Header%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    if self.has_payload_: res+=prefix+("Payload: %s\n" % self.DebugFormatString(self.payload_))
    if self.has_followredirects_: res+=prefix+("FollowRedirects: %s\n" % self.DebugFormatBool(self.followredirects_))
    if self.has_deadline_: res+=prefix+("Deadline: %s\n" % self.DebugFormat(self.deadline_))
    if self.has_mustvalidateservercertificate_: res+=prefix+("MustValidateServerCertificate: %s\n" % self.DebugFormatBool(self.mustvalidateservercertificate_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kMethod = 1
  kUrl = 2
  kHeaderGroup = 3
  kHeaderKey = 4
  kHeaderValue = 5
  kPayload = 6
  kFollowRedirects = 7
  kDeadline = 8
  kMustValidateServerCertificate = 9

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "Method",
    2: "Url",
    3: "Header",
    4: "Key",
    5: "Value",
    6: "Payload",
    7: "FollowRedirects",
    8: "Deadline",
    9: "MustValidateServerCertificate",
  }, 9)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STARTGROUP,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.STRING,
    7: ProtocolBuffer.Encoder.NUMERIC,
    8: ProtocolBuffer.Encoder.DOUBLE,
    9: ProtocolBuffer.Encoder.NUMERIC,
  }, 9, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.URLFetchRequest'
class URLFetchResponse_Header(ProtocolBuffer.ProtocolMessage):
  has_key_ = 0
  key_ = ""
  has_value_ = 0
  value_ = ""

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


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_key()): self.set_key(x.key())
    if (x.has_value()): self.set_value(x.value())

  def Equals(self, x):
    if x is self: return 1
    if self.has_key_ != x.has_key_: return 0
    if self.has_key_ and self.key_ != x.key_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
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
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_key_):
      n += 1
      n += self.lengthString(len(self.key_))
    if (self.has_value_):
      n += 1
      n += self.lengthString(len(self.value_))
    return n

  def Clear(self):
    self.clear_key()
    self.clear_value()

  def OutputUnchecked(self, out):
    out.putVarInt32(34)
    out.putPrefixedString(self.key_)
    out.putVarInt32(42)
    out.putPrefixedString(self.value_)

  def OutputPartial(self, out):
    if (self.has_key_):
      out.putVarInt32(34)
      out.putPrefixedString(self.key_)
    if (self.has_value_):
      out.putVarInt32(42)
      out.putPrefixedString(self.value_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 28: break
      if tt == 34:
        self.set_key(d.getPrefixedString())
        continue
      if tt == 42:
        self.set_value(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_: res+=prefix+("Key: %s\n" % self.DebugFormatString(self.key_))
    if self.has_value_: res+=prefix+("Value: %s\n" % self.DebugFormatString(self.value_))
    return res

class URLFetchResponse(ProtocolBuffer.ProtocolMessage):
  has_content_ = 0
  content_ = ""
  has_statuscode_ = 0
  statuscode_ = 0
  has_contentwastruncated_ = 0
  contentwastruncated_ = 0
  has_externalbytessent_ = 0
  externalbytessent_ = 0
  has_externalbytesreceived_ = 0
  externalbytesreceived_ = 0
  has_finalurl_ = 0
  finalurl_ = ""
  has_apicpumilliseconds_ = 0
  apicpumilliseconds_ = 0
  has_apibytessent_ = 0
  apibytessent_ = 0
  has_apibytesreceived_ = 0
  apibytesreceived_ = 0

  def __init__(self, contents=None):
    self.header_ = []
    if contents is not None: self.MergeFromString(contents)

  def content(self): return self.content_

  def set_content(self, x):
    self.has_content_ = 1
    self.content_ = x

  def clear_content(self):
    if self.has_content_:
      self.has_content_ = 0
      self.content_ = ""

  def has_content(self): return self.has_content_

  def statuscode(self): return self.statuscode_

  def set_statuscode(self, x):
    self.has_statuscode_ = 1
    self.statuscode_ = x

  def clear_statuscode(self):
    if self.has_statuscode_:
      self.has_statuscode_ = 0
      self.statuscode_ = 0

  def has_statuscode(self): return self.has_statuscode_

  def header_size(self): return len(self.header_)
  def header_list(self): return self.header_

  def header(self, i):
    return self.header_[i]

  def mutable_header(self, i):
    return self.header_[i]

  def add_header(self):
    x = URLFetchResponse_Header()
    self.header_.append(x)
    return x

  def clear_header(self):
    self.header_ = []
  def contentwastruncated(self): return self.contentwastruncated_

  def set_contentwastruncated(self, x):
    self.has_contentwastruncated_ = 1
    self.contentwastruncated_ = x

  def clear_contentwastruncated(self):
    if self.has_contentwastruncated_:
      self.has_contentwastruncated_ = 0
      self.contentwastruncated_ = 0

  def has_contentwastruncated(self): return self.has_contentwastruncated_

  def externalbytessent(self): return self.externalbytessent_

  def set_externalbytessent(self, x):
    self.has_externalbytessent_ = 1
    self.externalbytessent_ = x

  def clear_externalbytessent(self):
    if self.has_externalbytessent_:
      self.has_externalbytessent_ = 0
      self.externalbytessent_ = 0

  def has_externalbytessent(self): return self.has_externalbytessent_

  def externalbytesreceived(self): return self.externalbytesreceived_

  def set_externalbytesreceived(self, x):
    self.has_externalbytesreceived_ = 1
    self.externalbytesreceived_ = x

  def clear_externalbytesreceived(self):
    if self.has_externalbytesreceived_:
      self.has_externalbytesreceived_ = 0
      self.externalbytesreceived_ = 0

  def has_externalbytesreceived(self): return self.has_externalbytesreceived_

  def finalurl(self): return self.finalurl_

  def set_finalurl(self, x):
    self.has_finalurl_ = 1
    self.finalurl_ = x

  def clear_finalurl(self):
    if self.has_finalurl_:
      self.has_finalurl_ = 0
      self.finalurl_ = ""

  def has_finalurl(self): return self.has_finalurl_

  def apicpumilliseconds(self): return self.apicpumilliseconds_

  def set_apicpumilliseconds(self, x):
    self.has_apicpumilliseconds_ = 1
    self.apicpumilliseconds_ = x

  def clear_apicpumilliseconds(self):
    if self.has_apicpumilliseconds_:
      self.has_apicpumilliseconds_ = 0
      self.apicpumilliseconds_ = 0

  def has_apicpumilliseconds(self): return self.has_apicpumilliseconds_

  def apibytessent(self): return self.apibytessent_

  def set_apibytessent(self, x):
    self.has_apibytessent_ = 1
    self.apibytessent_ = x

  def clear_apibytessent(self):
    if self.has_apibytessent_:
      self.has_apibytessent_ = 0
      self.apibytessent_ = 0

  def has_apibytessent(self): return self.has_apibytessent_

  def apibytesreceived(self): return self.apibytesreceived_

  def set_apibytesreceived(self, x):
    self.has_apibytesreceived_ = 1
    self.apibytesreceived_ = x

  def clear_apibytesreceived(self):
    if self.has_apibytesreceived_:
      self.has_apibytesreceived_ = 0
      self.apibytesreceived_ = 0

  def has_apibytesreceived(self): return self.has_apibytesreceived_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_content()): self.set_content(x.content())
    if (x.has_statuscode()): self.set_statuscode(x.statuscode())
    for i in xrange(x.header_size()): self.add_header().CopyFrom(x.header(i))
    if (x.has_contentwastruncated()): self.set_contentwastruncated(x.contentwastruncated())
    if (x.has_externalbytessent()): self.set_externalbytessent(x.externalbytessent())
    if (x.has_externalbytesreceived()): self.set_externalbytesreceived(x.externalbytesreceived())
    if (x.has_finalurl()): self.set_finalurl(x.finalurl())
    if (x.has_apicpumilliseconds()): self.set_apicpumilliseconds(x.apicpumilliseconds())
    if (x.has_apibytessent()): self.set_apibytessent(x.apibytessent())
    if (x.has_apibytesreceived()): self.set_apibytesreceived(x.apibytesreceived())

  def Equals(self, x):
    if x is self: return 1
    if self.has_content_ != x.has_content_: return 0
    if self.has_content_ and self.content_ != x.content_: return 0
    if self.has_statuscode_ != x.has_statuscode_: return 0
    if self.has_statuscode_ and self.statuscode_ != x.statuscode_: return 0
    if len(self.header_) != len(x.header_): return 0
    for e1, e2 in zip(self.header_, x.header_):
      if e1 != e2: return 0
    if self.has_contentwastruncated_ != x.has_contentwastruncated_: return 0
    if self.has_contentwastruncated_ and self.contentwastruncated_ != x.contentwastruncated_: return 0
    if self.has_externalbytessent_ != x.has_externalbytessent_: return 0
    if self.has_externalbytessent_ and self.externalbytessent_ != x.externalbytessent_: return 0
    if self.has_externalbytesreceived_ != x.has_externalbytesreceived_: return 0
    if self.has_externalbytesreceived_ and self.externalbytesreceived_ != x.externalbytesreceived_: return 0
    if self.has_finalurl_ != x.has_finalurl_: return 0
    if self.has_finalurl_ and self.finalurl_ != x.finalurl_: return 0
    if self.has_apicpumilliseconds_ != x.has_apicpumilliseconds_: return 0
    if self.has_apicpumilliseconds_ and self.apicpumilliseconds_ != x.apicpumilliseconds_: return 0
    if self.has_apibytessent_ != x.has_apibytessent_: return 0
    if self.has_apibytessent_ and self.apibytessent_ != x.apibytessent_: return 0
    if self.has_apibytesreceived_ != x.has_apibytesreceived_: return 0
    if self.has_apibytesreceived_ and self.apibytesreceived_ != x.apibytesreceived_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_statuscode_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: statuscode not set.')
    for p in self.header_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_content_): n += 1 + self.lengthString(len(self.content_))
    n += self.lengthVarInt64(self.statuscode_)
    n += 2 * len(self.header_)
    for i in xrange(len(self.header_)): n += self.header_[i].ByteSize()
    if (self.has_contentwastruncated_): n += 2
    if (self.has_externalbytessent_): n += 1 + self.lengthVarInt64(self.externalbytessent_)
    if (self.has_externalbytesreceived_): n += 1 + self.lengthVarInt64(self.externalbytesreceived_)
    if (self.has_finalurl_): n += 1 + self.lengthString(len(self.finalurl_))
    if (self.has_apicpumilliseconds_): n += 1 + self.lengthVarInt64(self.apicpumilliseconds_)
    if (self.has_apibytessent_): n += 1 + self.lengthVarInt64(self.apibytessent_)
    if (self.has_apibytesreceived_): n += 1 + self.lengthVarInt64(self.apibytesreceived_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_content_): n += 1 + self.lengthString(len(self.content_))
    if (self.has_statuscode_):
      n += 1
      n += self.lengthVarInt64(self.statuscode_)
    n += 2 * len(self.header_)
    for i in xrange(len(self.header_)): n += self.header_[i].ByteSizePartial()
    if (self.has_contentwastruncated_): n += 2
    if (self.has_externalbytessent_): n += 1 + self.lengthVarInt64(self.externalbytessent_)
    if (self.has_externalbytesreceived_): n += 1 + self.lengthVarInt64(self.externalbytesreceived_)
    if (self.has_finalurl_): n += 1 + self.lengthString(len(self.finalurl_))
    if (self.has_apicpumilliseconds_): n += 1 + self.lengthVarInt64(self.apicpumilliseconds_)
    if (self.has_apibytessent_): n += 1 + self.lengthVarInt64(self.apibytessent_)
    if (self.has_apibytesreceived_): n += 1 + self.lengthVarInt64(self.apibytesreceived_)
    return n

  def Clear(self):
    self.clear_content()
    self.clear_statuscode()
    self.clear_header()
    self.clear_contentwastruncated()
    self.clear_externalbytessent()
    self.clear_externalbytesreceived()
    self.clear_finalurl()
    self.clear_apicpumilliseconds()
    self.clear_apibytessent()
    self.clear_apibytesreceived()

  def OutputUnchecked(self, out):
    if (self.has_content_):
      out.putVarInt32(10)
      out.putPrefixedString(self.content_)
    out.putVarInt32(16)
    out.putVarInt32(self.statuscode_)
    for i in xrange(len(self.header_)):
      out.putVarInt32(27)
      self.header_[i].OutputUnchecked(out)
      out.putVarInt32(28)
    if (self.has_contentwastruncated_):
      out.putVarInt32(48)
      out.putBoolean(self.contentwastruncated_)
    if (self.has_externalbytessent_):
      out.putVarInt32(56)
      out.putVarInt64(self.externalbytessent_)
    if (self.has_externalbytesreceived_):
      out.putVarInt32(64)
      out.putVarInt64(self.externalbytesreceived_)
    if (self.has_finalurl_):
      out.putVarInt32(74)
      out.putPrefixedString(self.finalurl_)
    if (self.has_apicpumilliseconds_):
      out.putVarInt32(80)
      out.putVarInt64(self.apicpumilliseconds_)
    if (self.has_apibytessent_):
      out.putVarInt32(88)
      out.putVarInt64(self.apibytessent_)
    if (self.has_apibytesreceived_):
      out.putVarInt32(96)
      out.putVarInt64(self.apibytesreceived_)

  def OutputPartial(self, out):
    if (self.has_content_):
      out.putVarInt32(10)
      out.putPrefixedString(self.content_)
    if (self.has_statuscode_):
      out.putVarInt32(16)
      out.putVarInt32(self.statuscode_)
    for i in xrange(len(self.header_)):
      out.putVarInt32(27)
      self.header_[i].OutputPartial(out)
      out.putVarInt32(28)
    if (self.has_contentwastruncated_):
      out.putVarInt32(48)
      out.putBoolean(self.contentwastruncated_)
    if (self.has_externalbytessent_):
      out.putVarInt32(56)
      out.putVarInt64(self.externalbytessent_)
    if (self.has_externalbytesreceived_):
      out.putVarInt32(64)
      out.putVarInt64(self.externalbytesreceived_)
    if (self.has_finalurl_):
      out.putVarInt32(74)
      out.putPrefixedString(self.finalurl_)
    if (self.has_apicpumilliseconds_):
      out.putVarInt32(80)
      out.putVarInt64(self.apicpumilliseconds_)
    if (self.has_apibytessent_):
      out.putVarInt32(88)
      out.putVarInt64(self.apibytessent_)
    if (self.has_apibytesreceived_):
      out.putVarInt32(96)
      out.putVarInt64(self.apibytesreceived_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_content(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_statuscode(d.getVarInt32())
        continue
      if tt == 27:
        self.add_header().TryMerge(d)
        continue
      if tt == 48:
        self.set_contentwastruncated(d.getBoolean())
        continue
      if tt == 56:
        self.set_externalbytessent(d.getVarInt64())
        continue
      if tt == 64:
        self.set_externalbytesreceived(d.getVarInt64())
        continue
      if tt == 74:
        self.set_finalurl(d.getPrefixedString())
        continue
      if tt == 80:
        self.set_apicpumilliseconds(d.getVarInt64())
        continue
      if tt == 88:
        self.set_apibytessent(d.getVarInt64())
        continue
      if tt == 96:
        self.set_apibytesreceived(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_content_: res+=prefix+("Content: %s\n" % self.DebugFormatString(self.content_))
    if self.has_statuscode_: res+=prefix+("StatusCode: %s\n" % self.DebugFormatInt32(self.statuscode_))
    cnt=0
    for e in self.header_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Header%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    if self.has_contentwastruncated_: res+=prefix+("ContentWasTruncated: %s\n" % self.DebugFormatBool(self.contentwastruncated_))
    if self.has_externalbytessent_: res+=prefix+("ExternalBytesSent: %s\n" % self.DebugFormatInt64(self.externalbytessent_))
    if self.has_externalbytesreceived_: res+=prefix+("ExternalBytesReceived: %s\n" % self.DebugFormatInt64(self.externalbytesreceived_))
    if self.has_finalurl_: res+=prefix+("FinalUrl: %s\n" % self.DebugFormatString(self.finalurl_))
    if self.has_apicpumilliseconds_: res+=prefix+("ApiCpuMilliseconds: %s\n" % self.DebugFormatInt64(self.apicpumilliseconds_))
    if self.has_apibytessent_: res+=prefix+("ApiBytesSent: %s\n" % self.DebugFormatInt64(self.apibytessent_))
    if self.has_apibytesreceived_: res+=prefix+("ApiBytesReceived: %s\n" % self.DebugFormatInt64(self.apibytesreceived_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kContent = 1
  kStatusCode = 2
  kHeaderGroup = 3
  kHeaderKey = 4
  kHeaderValue = 5
  kContentWasTruncated = 6
  kExternalBytesSent = 7
  kExternalBytesReceived = 8
  kFinalUrl = 9
  kApiCpuMilliseconds = 10
  kApiBytesSent = 11
  kApiBytesReceived = 12

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "Content",
    2: "StatusCode",
    3: "Header",
    4: "Key",
    5: "Value",
    6: "ContentWasTruncated",
    7: "ExternalBytesSent",
    8: "ExternalBytesReceived",
    9: "FinalUrl",
    10: "ApiCpuMilliseconds",
    11: "ApiBytesSent",
    12: "ApiBytesReceived",
  }, 12)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STARTGROUP,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.NUMERIC,
    7: ProtocolBuffer.Encoder.NUMERIC,
    8: ProtocolBuffer.Encoder.NUMERIC,
    9: ProtocolBuffer.Encoder.STRING,
    10: ProtocolBuffer.Encoder.NUMERIC,
    11: ProtocolBuffer.Encoder.NUMERIC,
    12: ProtocolBuffer.Encoder.NUMERIC,
  }, 12, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.URLFetchResponse'
if _extension_runtime:
  pass

__all__ = ['URLFetchServiceError','URLFetchRequest','URLFetchRequest_Header','URLFetchResponse','URLFetchResponse_Header']
