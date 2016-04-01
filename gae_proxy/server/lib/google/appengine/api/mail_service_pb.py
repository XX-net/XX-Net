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
class MailServiceError(ProtocolBuffer.ProtocolMessage):


  OK           =    0
  INTERNAL_ERROR =    1
  BAD_REQUEST  =    2
  UNAUTHORIZED_SENDER =    3
  INVALID_ATTACHMENT_TYPE =    4
  INVALID_HEADER_NAME =    5
  INVALID_CONTENT_ID =    6

  _ErrorCode_NAMES = {
    0: "OK",
    1: "INTERNAL_ERROR",
    2: "BAD_REQUEST",
    3: "UNAUTHORIZED_SENDER",
    4: "INVALID_ATTACHMENT_TYPE",
    5: "INVALID_HEADER_NAME",
    6: "INVALID_CONTENT_ID",
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MailServiceError'
class MailAttachment(ProtocolBuffer.ProtocolMessage):
  has_filename_ = 0
  filename_ = ""
  has_data_ = 0
  data_ = ""
  has_contentid_ = 0
  contentid_ = ""
  has_contentid_set_ = 0
  contentid_set_ = 0

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

  def data(self): return self.data_

  def set_data(self, x):
    self.has_data_ = 1
    self.data_ = x

  def clear_data(self):
    if self.has_data_:
      self.has_data_ = 0
      self.data_ = ""

  def has_data(self): return self.has_data_

  def contentid(self): return self.contentid_

  def set_contentid(self, x):
    self.has_contentid_ = 1
    self.contentid_ = x

  def clear_contentid(self):
    if self.has_contentid_:
      self.has_contentid_ = 0
      self.contentid_ = ""

  def has_contentid(self): return self.has_contentid_

  def contentid_set(self): return self.contentid_set_

  def set_contentid_set(self, x):
    self.has_contentid_set_ = 1
    self.contentid_set_ = x

  def clear_contentid_set(self):
    if self.has_contentid_set_:
      self.has_contentid_set_ = 0
      self.contentid_set_ = 0

  def has_contentid_set(self): return self.has_contentid_set_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_filename()): self.set_filename(x.filename())
    if (x.has_data()): self.set_data(x.data())
    if (x.has_contentid()): self.set_contentid(x.contentid())
    if (x.has_contentid_set()): self.set_contentid_set(x.contentid_set())

  def Equals(self, x):
    if x is self: return 1
    if self.has_filename_ != x.has_filename_: return 0
    if self.has_filename_ and self.filename_ != x.filename_: return 0
    if self.has_data_ != x.has_data_: return 0
    if self.has_data_ and self.data_ != x.data_: return 0
    if self.has_contentid_ != x.has_contentid_: return 0
    if self.has_contentid_ and self.contentid_ != x.contentid_: return 0
    if self.has_contentid_set_ != x.has_contentid_set_: return 0
    if self.has_contentid_set_ and self.contentid_set_ != x.contentid_set_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_filename_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: filename not set.')
    if (not self.has_data_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: data not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.filename_))
    n += self.lengthString(len(self.data_))
    if (self.has_contentid_): n += 1 + self.lengthString(len(self.contentid_))
    if (self.has_contentid_set_): n += 2
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_filename_):
      n += 1
      n += self.lengthString(len(self.filename_))
    if (self.has_data_):
      n += 1
      n += self.lengthString(len(self.data_))
    if (self.has_contentid_): n += 1 + self.lengthString(len(self.contentid_))
    if (self.has_contentid_set_): n += 2
    return n

  def Clear(self):
    self.clear_filename()
    self.clear_data()
    self.clear_contentid()
    self.clear_contentid_set()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.filename_)
    out.putVarInt32(18)
    out.putPrefixedString(self.data_)
    if (self.has_contentid_):
      out.putVarInt32(26)
      out.putPrefixedString(self.contentid_)
    if (self.has_contentid_set_):
      out.putVarInt32(104)
      out.putBoolean(self.contentid_set_)

  def OutputPartial(self, out):
    if (self.has_filename_):
      out.putVarInt32(10)
      out.putPrefixedString(self.filename_)
    if (self.has_data_):
      out.putVarInt32(18)
      out.putPrefixedString(self.data_)
    if (self.has_contentid_):
      out.putVarInt32(26)
      out.putPrefixedString(self.contentid_)
    if (self.has_contentid_set_):
      out.putVarInt32(104)
      out.putBoolean(self.contentid_set_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_filename(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_data(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_contentid(d.getPrefixedString())
        continue
      if tt == 104:
        self.set_contentid_set(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_filename_: res+=prefix+("FileName: %s\n" % self.DebugFormatString(self.filename_))
    if self.has_data_: res+=prefix+("Data: %s\n" % self.DebugFormatString(self.data_))
    if self.has_contentid_: res+=prefix+("ContentID: %s\n" % self.DebugFormatString(self.contentid_))
    if self.has_contentid_set_: res+=prefix+("ContentID_set: %s\n" % self.DebugFormatBool(self.contentid_set_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kFileName = 1
  kData = 2
  kContentID = 3
  kContentID_set = 13

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "FileName",
    2: "Data",
    3: "ContentID",
    13: "ContentID_set",
  }, 13)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    13: ProtocolBuffer.Encoder.NUMERIC,
  }, 13, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MailAttachment'
class MailHeader(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""
  has_value_ = 0
  value_ = ""

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
    if (x.has_name()): self.set_name(x.name())
    if (x.has_value()): self.set_value(x.value())

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: name not set.')
    if (not self.has_value_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: value not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.name_))
    n += self.lengthString(len(self.value_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    if (self.has_value_):
      n += 1
      n += self.lengthString(len(self.value_))
    return n

  def Clear(self):
    self.clear_name()
    self.clear_value()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.name_)
    out.putVarInt32(18)
    out.putPrefixedString(self.value_)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    if (self.has_value_):
      out.putVarInt32(18)
      out.putPrefixedString(self.value_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_name(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_value(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    if self.has_value_: res+=prefix+("value: %s\n" % self.DebugFormatString(self.value_))
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MailHeader'
class MailMessage(ProtocolBuffer.ProtocolMessage):
  has_sender_ = 0
  sender_ = ""
  has_replyto_ = 0
  replyto_ = ""
  has_subject_ = 0
  subject_ = ""
  has_textbody_ = 0
  textbody_ = ""
  has_htmlbody_ = 0
  htmlbody_ = ""

  def __init__(self, contents=None):
    self.to_ = []
    self.cc_ = []
    self.bcc_ = []
    self.attachment_ = []
    self.header_ = []
    if contents is not None: self.MergeFromString(contents)

  def sender(self): return self.sender_

  def set_sender(self, x):
    self.has_sender_ = 1
    self.sender_ = x

  def clear_sender(self):
    if self.has_sender_:
      self.has_sender_ = 0
      self.sender_ = ""

  def has_sender(self): return self.has_sender_

  def replyto(self): return self.replyto_

  def set_replyto(self, x):
    self.has_replyto_ = 1
    self.replyto_ = x

  def clear_replyto(self):
    if self.has_replyto_:
      self.has_replyto_ = 0
      self.replyto_ = ""

  def has_replyto(self): return self.has_replyto_

  def to_size(self): return len(self.to_)
  def to_list(self): return self.to_

  def to(self, i):
    return self.to_[i]

  def set_to(self, i, x):
    self.to_[i] = x

  def add_to(self, x):
    self.to_.append(x)

  def clear_to(self):
    self.to_ = []

  def cc_size(self): return len(self.cc_)
  def cc_list(self): return self.cc_

  def cc(self, i):
    return self.cc_[i]

  def set_cc(self, i, x):
    self.cc_[i] = x

  def add_cc(self, x):
    self.cc_.append(x)

  def clear_cc(self):
    self.cc_ = []

  def bcc_size(self): return len(self.bcc_)
  def bcc_list(self): return self.bcc_

  def bcc(self, i):
    return self.bcc_[i]

  def set_bcc(self, i, x):
    self.bcc_[i] = x

  def add_bcc(self, x):
    self.bcc_.append(x)

  def clear_bcc(self):
    self.bcc_ = []

  def subject(self): return self.subject_

  def set_subject(self, x):
    self.has_subject_ = 1
    self.subject_ = x

  def clear_subject(self):
    if self.has_subject_:
      self.has_subject_ = 0
      self.subject_ = ""

  def has_subject(self): return self.has_subject_

  def textbody(self): return self.textbody_

  def set_textbody(self, x):
    self.has_textbody_ = 1
    self.textbody_ = x

  def clear_textbody(self):
    if self.has_textbody_:
      self.has_textbody_ = 0
      self.textbody_ = ""

  def has_textbody(self): return self.has_textbody_

  def htmlbody(self): return self.htmlbody_

  def set_htmlbody(self, x):
    self.has_htmlbody_ = 1
    self.htmlbody_ = x

  def clear_htmlbody(self):
    if self.has_htmlbody_:
      self.has_htmlbody_ = 0
      self.htmlbody_ = ""

  def has_htmlbody(self): return self.has_htmlbody_

  def attachment_size(self): return len(self.attachment_)
  def attachment_list(self): return self.attachment_

  def attachment(self, i):
    return self.attachment_[i]

  def mutable_attachment(self, i):
    return self.attachment_[i]

  def add_attachment(self):
    x = MailAttachment()
    self.attachment_.append(x)
    return x

  def clear_attachment(self):
    self.attachment_ = []
  def header_size(self): return len(self.header_)
  def header_list(self): return self.header_

  def header(self, i):
    return self.header_[i]

  def mutable_header(self, i):
    return self.header_[i]

  def add_header(self):
    x = MailHeader()
    self.header_.append(x)
    return x

  def clear_header(self):
    self.header_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_sender()): self.set_sender(x.sender())
    if (x.has_replyto()): self.set_replyto(x.replyto())
    for i in xrange(x.to_size()): self.add_to(x.to(i))
    for i in xrange(x.cc_size()): self.add_cc(x.cc(i))
    for i in xrange(x.bcc_size()): self.add_bcc(x.bcc(i))
    if (x.has_subject()): self.set_subject(x.subject())
    if (x.has_textbody()): self.set_textbody(x.textbody())
    if (x.has_htmlbody()): self.set_htmlbody(x.htmlbody())
    for i in xrange(x.attachment_size()): self.add_attachment().CopyFrom(x.attachment(i))
    for i in xrange(x.header_size()): self.add_header().CopyFrom(x.header(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_sender_ != x.has_sender_: return 0
    if self.has_sender_ and self.sender_ != x.sender_: return 0
    if self.has_replyto_ != x.has_replyto_: return 0
    if self.has_replyto_ and self.replyto_ != x.replyto_: return 0
    if len(self.to_) != len(x.to_): return 0
    for e1, e2 in zip(self.to_, x.to_):
      if e1 != e2: return 0
    if len(self.cc_) != len(x.cc_): return 0
    for e1, e2 in zip(self.cc_, x.cc_):
      if e1 != e2: return 0
    if len(self.bcc_) != len(x.bcc_): return 0
    for e1, e2 in zip(self.bcc_, x.bcc_):
      if e1 != e2: return 0
    if self.has_subject_ != x.has_subject_: return 0
    if self.has_subject_ and self.subject_ != x.subject_: return 0
    if self.has_textbody_ != x.has_textbody_: return 0
    if self.has_textbody_ and self.textbody_ != x.textbody_: return 0
    if self.has_htmlbody_ != x.has_htmlbody_: return 0
    if self.has_htmlbody_ and self.htmlbody_ != x.htmlbody_: return 0
    if len(self.attachment_) != len(x.attachment_): return 0
    for e1, e2 in zip(self.attachment_, x.attachment_):
      if e1 != e2: return 0
    if len(self.header_) != len(x.header_): return 0
    for e1, e2 in zip(self.header_, x.header_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_sender_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: sender not set.')
    if (not self.has_subject_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: subject not set.')
    for p in self.attachment_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.header_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.sender_))
    if (self.has_replyto_): n += 1 + self.lengthString(len(self.replyto_))
    n += 1 * len(self.to_)
    for i in xrange(len(self.to_)): n += self.lengthString(len(self.to_[i]))
    n += 1 * len(self.cc_)
    for i in xrange(len(self.cc_)): n += self.lengthString(len(self.cc_[i]))
    n += 1 * len(self.bcc_)
    for i in xrange(len(self.bcc_)): n += self.lengthString(len(self.bcc_[i]))
    n += self.lengthString(len(self.subject_))
    if (self.has_textbody_): n += 1 + self.lengthString(len(self.textbody_))
    if (self.has_htmlbody_): n += 1 + self.lengthString(len(self.htmlbody_))
    n += 1 * len(self.attachment_)
    for i in xrange(len(self.attachment_)): n += self.lengthString(self.attachment_[i].ByteSize())
    n += 1 * len(self.header_)
    for i in xrange(len(self.header_)): n += self.lengthString(self.header_[i].ByteSize())
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_sender_):
      n += 1
      n += self.lengthString(len(self.sender_))
    if (self.has_replyto_): n += 1 + self.lengthString(len(self.replyto_))
    n += 1 * len(self.to_)
    for i in xrange(len(self.to_)): n += self.lengthString(len(self.to_[i]))
    n += 1 * len(self.cc_)
    for i in xrange(len(self.cc_)): n += self.lengthString(len(self.cc_[i]))
    n += 1 * len(self.bcc_)
    for i in xrange(len(self.bcc_)): n += self.lengthString(len(self.bcc_[i]))
    if (self.has_subject_):
      n += 1
      n += self.lengthString(len(self.subject_))
    if (self.has_textbody_): n += 1 + self.lengthString(len(self.textbody_))
    if (self.has_htmlbody_): n += 1 + self.lengthString(len(self.htmlbody_))
    n += 1 * len(self.attachment_)
    for i in xrange(len(self.attachment_)): n += self.lengthString(self.attachment_[i].ByteSizePartial())
    n += 1 * len(self.header_)
    for i in xrange(len(self.header_)): n += self.lengthString(self.header_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_sender()
    self.clear_replyto()
    self.clear_to()
    self.clear_cc()
    self.clear_bcc()
    self.clear_subject()
    self.clear_textbody()
    self.clear_htmlbody()
    self.clear_attachment()
    self.clear_header()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.sender_)
    if (self.has_replyto_):
      out.putVarInt32(18)
      out.putPrefixedString(self.replyto_)
    for i in xrange(len(self.to_)):
      out.putVarInt32(26)
      out.putPrefixedString(self.to_[i])
    for i in xrange(len(self.cc_)):
      out.putVarInt32(34)
      out.putPrefixedString(self.cc_[i])
    for i in xrange(len(self.bcc_)):
      out.putVarInt32(42)
      out.putPrefixedString(self.bcc_[i])
    out.putVarInt32(50)
    out.putPrefixedString(self.subject_)
    if (self.has_textbody_):
      out.putVarInt32(58)
      out.putPrefixedString(self.textbody_)
    if (self.has_htmlbody_):
      out.putVarInt32(66)
      out.putPrefixedString(self.htmlbody_)
    for i in xrange(len(self.attachment_)):
      out.putVarInt32(74)
      out.putVarInt32(self.attachment_[i].ByteSize())
      self.attachment_[i].OutputUnchecked(out)
    for i in xrange(len(self.header_)):
      out.putVarInt32(82)
      out.putVarInt32(self.header_[i].ByteSize())
      self.header_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_sender_):
      out.putVarInt32(10)
      out.putPrefixedString(self.sender_)
    if (self.has_replyto_):
      out.putVarInt32(18)
      out.putPrefixedString(self.replyto_)
    for i in xrange(len(self.to_)):
      out.putVarInt32(26)
      out.putPrefixedString(self.to_[i])
    for i in xrange(len(self.cc_)):
      out.putVarInt32(34)
      out.putPrefixedString(self.cc_[i])
    for i in xrange(len(self.bcc_)):
      out.putVarInt32(42)
      out.putPrefixedString(self.bcc_[i])
    if (self.has_subject_):
      out.putVarInt32(50)
      out.putPrefixedString(self.subject_)
    if (self.has_textbody_):
      out.putVarInt32(58)
      out.putPrefixedString(self.textbody_)
    if (self.has_htmlbody_):
      out.putVarInt32(66)
      out.putPrefixedString(self.htmlbody_)
    for i in xrange(len(self.attachment_)):
      out.putVarInt32(74)
      out.putVarInt32(self.attachment_[i].ByteSizePartial())
      self.attachment_[i].OutputPartial(out)
    for i in xrange(len(self.header_)):
      out.putVarInt32(82)
      out.putVarInt32(self.header_[i].ByteSizePartial())
      self.header_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_sender(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_replyto(d.getPrefixedString())
        continue
      if tt == 26:
        self.add_to(d.getPrefixedString())
        continue
      if tt == 34:
        self.add_cc(d.getPrefixedString())
        continue
      if tt == 42:
        self.add_bcc(d.getPrefixedString())
        continue
      if tt == 50:
        self.set_subject(d.getPrefixedString())
        continue
      if tt == 58:
        self.set_textbody(d.getPrefixedString())
        continue
      if tt == 66:
        self.set_htmlbody(d.getPrefixedString())
        continue
      if tt == 74:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_attachment().TryMerge(tmp)
        continue
      if tt == 82:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_header().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_sender_: res+=prefix+("Sender: %s\n" % self.DebugFormatString(self.sender_))
    if self.has_replyto_: res+=prefix+("ReplyTo: %s\n" % self.DebugFormatString(self.replyto_))
    cnt=0
    for e in self.to_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("To%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    cnt=0
    for e in self.cc_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Cc%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    cnt=0
    for e in self.bcc_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Bcc%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_subject_: res+=prefix+("Subject: %s\n" % self.DebugFormatString(self.subject_))
    if self.has_textbody_: res+=prefix+("TextBody: %s\n" % self.DebugFormatString(self.textbody_))
    if self.has_htmlbody_: res+=prefix+("HtmlBody: %s\n" % self.DebugFormatString(self.htmlbody_))
    cnt=0
    for e in self.attachment_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Attachment%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.header_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Header%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kSender = 1
  kReplyTo = 2
  kTo = 3
  kCc = 4
  kBcc = 5
  kSubject = 6
  kTextBody = 7
  kHtmlBody = 8
  kAttachment = 9
  kHeader = 10

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "Sender",
    2: "ReplyTo",
    3: "To",
    4: "Cc",
    5: "Bcc",
    6: "Subject",
    7: "TextBody",
    8: "HtmlBody",
    9: "Attachment",
    10: "Header",
  }, 10)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.STRING,
    7: ProtocolBuffer.Encoder.STRING,
    8: ProtocolBuffer.Encoder.STRING,
    9: ProtocolBuffer.Encoder.STRING,
    10: ProtocolBuffer.Encoder.STRING,
  }, 10, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.MailMessage'
if _extension_runtime:
  pass

__all__ = ['MailServiceError','MailAttachment','MailHeader','MailMessage']
