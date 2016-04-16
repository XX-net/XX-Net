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
from google.appengine.api.source_pb import *
import google.appengine.api.source_pb
class LogServiceError(ProtocolBuffer.ProtocolMessage):


  OK           =    0
  INVALID_REQUEST =    1
  STORAGE_ERROR =    2

  _ErrorCode_NAMES = {
    0: "OK",
    1: "INVALID_REQUEST",
    2: "STORAGE_ERROR",
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.LogServiceError'
class UserAppLogLine(ProtocolBuffer.ProtocolMessage):
  has_timestamp_usec_ = 0
  timestamp_usec_ = 0
  has_level_ = 0
  level_ = 0
  has_message_ = 0
  message_ = ""
  has_source_location_ = 0
  source_location_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def timestamp_usec(self): return self.timestamp_usec_

  def set_timestamp_usec(self, x):
    self.has_timestamp_usec_ = 1
    self.timestamp_usec_ = x

  def clear_timestamp_usec(self):
    if self.has_timestamp_usec_:
      self.has_timestamp_usec_ = 0
      self.timestamp_usec_ = 0

  def has_timestamp_usec(self): return self.has_timestamp_usec_

  def level(self): return self.level_

  def set_level(self, x):
    self.has_level_ = 1
    self.level_ = x

  def clear_level(self):
    if self.has_level_:
      self.has_level_ = 0
      self.level_ = 0

  def has_level(self): return self.has_level_

  def message(self): return self.message_

  def set_message(self, x):
    self.has_message_ = 1
    self.message_ = x

  def clear_message(self):
    if self.has_message_:
      self.has_message_ = 0
      self.message_ = ""

  def has_message(self): return self.has_message_

  def source_location(self):
    if self.source_location_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.source_location_ is None: self.source_location_ = SourceLocation()
      finally:
        self.lazy_init_lock_.release()
    return self.source_location_

  def mutable_source_location(self): self.has_source_location_ = 1; return self.source_location()

  def clear_source_location(self):

    if self.has_source_location_:
      self.has_source_location_ = 0;
      if self.source_location_ is not None: self.source_location_.Clear()

  def has_source_location(self): return self.has_source_location_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_timestamp_usec()): self.set_timestamp_usec(x.timestamp_usec())
    if (x.has_level()): self.set_level(x.level())
    if (x.has_message()): self.set_message(x.message())
    if (x.has_source_location()): self.mutable_source_location().MergeFrom(x.source_location())

  def Equals(self, x):
    if x is self: return 1
    if self.has_timestamp_usec_ != x.has_timestamp_usec_: return 0
    if self.has_timestamp_usec_ and self.timestamp_usec_ != x.timestamp_usec_: return 0
    if self.has_level_ != x.has_level_: return 0
    if self.has_level_ and self.level_ != x.level_: return 0
    if self.has_message_ != x.has_message_: return 0
    if self.has_message_ and self.message_ != x.message_: return 0
    if self.has_source_location_ != x.has_source_location_: return 0
    if self.has_source_location_ and self.source_location_ != x.source_location_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_timestamp_usec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: timestamp_usec not set.')
    if (not self.has_level_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: level not set.')
    if (not self.has_message_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: message not set.')
    if (self.has_source_location_ and not self.source_location_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.timestamp_usec_)
    n += self.lengthVarInt64(self.level_)
    n += self.lengthString(len(self.message_))
    if (self.has_source_location_): n += 1 + self.lengthString(self.source_location_.ByteSize())
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_timestamp_usec_):
      n += 1
      n += self.lengthVarInt64(self.timestamp_usec_)
    if (self.has_level_):
      n += 1
      n += self.lengthVarInt64(self.level_)
    if (self.has_message_):
      n += 1
      n += self.lengthString(len(self.message_))
    if (self.has_source_location_): n += 1 + self.lengthString(self.source_location_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_timestamp_usec()
    self.clear_level()
    self.clear_message()
    self.clear_source_location()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt64(self.timestamp_usec_)
    out.putVarInt32(16)
    out.putVarInt64(self.level_)
    out.putVarInt32(26)
    out.putPrefixedString(self.message_)
    if (self.has_source_location_):
      out.putVarInt32(34)
      out.putVarInt32(self.source_location_.ByteSize())
      self.source_location_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_timestamp_usec_):
      out.putVarInt32(8)
      out.putVarInt64(self.timestamp_usec_)
    if (self.has_level_):
      out.putVarInt32(16)
      out.putVarInt64(self.level_)
    if (self.has_message_):
      out.putVarInt32(26)
      out.putPrefixedString(self.message_)
    if (self.has_source_location_):
      out.putVarInt32(34)
      out.putVarInt32(self.source_location_.ByteSizePartial())
      self.source_location_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_timestamp_usec(d.getVarInt64())
        continue
      if tt == 16:
        self.set_level(d.getVarInt64())
        continue
      if tt == 26:
        self.set_message(d.getPrefixedString())
        continue
      if tt == 34:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_source_location().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_timestamp_usec_: res+=prefix+("timestamp_usec: %s\n" % self.DebugFormatInt64(self.timestamp_usec_))
    if self.has_level_: res+=prefix+("level: %s\n" % self.DebugFormatInt64(self.level_))
    if self.has_message_: res+=prefix+("message: %s\n" % self.DebugFormatString(self.message_))
    if self.has_source_location_:
      res+=prefix+"source_location <\n"
      res+=self.source_location_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktimestamp_usec = 1
  klevel = 2
  kmessage = 3
  ksource_location = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "timestamp_usec",
    2: "level",
    3: "message",
    4: "source_location",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.UserAppLogLine'
class UserAppLogGroup(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.log_line_ = []
    if contents is not None: self.MergeFromString(contents)

  def log_line_size(self): return len(self.log_line_)
  def log_line_list(self): return self.log_line_

  def log_line(self, i):
    return self.log_line_[i]

  def mutable_log_line(self, i):
    return self.log_line_[i]

  def add_log_line(self):
    x = UserAppLogLine()
    self.log_line_.append(x)
    return x

  def clear_log_line(self):
    self.log_line_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.log_line_size()): self.add_log_line().CopyFrom(x.log_line(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.log_line_) != len(x.log_line_): return 0
    for e1, e2 in zip(self.log_line_, x.log_line_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.log_line_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.log_line_)
    for i in xrange(len(self.log_line_)): n += self.lengthString(self.log_line_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.log_line_)
    for i in xrange(len(self.log_line_)): n += self.lengthString(self.log_line_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_log_line()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.log_line_)):
      out.putVarInt32(18)
      out.putVarInt32(self.log_line_[i].ByteSize())
      self.log_line_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.log_line_)):
      out.putVarInt32(18)
      out.putVarInt32(self.log_line_[i].ByteSizePartial())
      self.log_line_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_log_line().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.log_line_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("log_line%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  klog_line = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    2: "log_line",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.UserAppLogGroup'
class FlushRequest(ProtocolBuffer.ProtocolMessage):
  has_logs_ = 0
  logs_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def logs(self): return self.logs_

  def set_logs(self, x):
    self.has_logs_ = 1
    self.logs_ = x

  def clear_logs(self):
    if self.has_logs_:
      self.has_logs_ = 0
      self.logs_ = ""

  def has_logs(self): return self.has_logs_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_logs()): self.set_logs(x.logs())

  def Equals(self, x):
    if x is self: return 1
    if self.has_logs_ != x.has_logs_: return 0
    if self.has_logs_ and self.logs_ != x.logs_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_logs_): n += 1 + self.lengthString(len(self.logs_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_logs_): n += 1 + self.lengthString(len(self.logs_))
    return n

  def Clear(self):
    self.clear_logs()

  def OutputUnchecked(self, out):
    if (self.has_logs_):
      out.putVarInt32(10)
      out.putPrefixedString(self.logs_)

  def OutputPartial(self, out):
    if (self.has_logs_):
      out.putVarInt32(10)
      out.putPrefixedString(self.logs_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_logs(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_logs_: res+=prefix+("logs: %s\n" % self.DebugFormatString(self.logs_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  klogs = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "logs",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.FlushRequest'
class SetStatusRequest(ProtocolBuffer.ProtocolMessage):
  has_status_ = 0
  status_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def status(self): return self.status_

  def set_status(self, x):
    self.has_status_ = 1
    self.status_ = x

  def clear_status(self):
    if self.has_status_:
      self.has_status_ = 0
      self.status_ = ""

  def has_status(self): return self.has_status_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_status()): self.set_status(x.status())

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
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.status_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_status_):
      n += 1
      n += self.lengthString(len(self.status_))
    return n

  def Clear(self):
    self.clear_status()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.status_)

  def OutputPartial(self, out):
    if (self.has_status_):
      out.putVarInt32(10)
      out.putPrefixedString(self.status_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_status(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_status_: res+=prefix+("status: %s\n" % self.DebugFormatString(self.status_))
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SetStatusRequest'
class LogOffset(ProtocolBuffer.ProtocolMessage):
  has_request_id_ = 0
  request_id_ = ""
  has_request_id_set_ = 0
  request_id_set_ = 0

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

  def request_id_set(self): return self.request_id_set_

  def set_request_id_set(self, x):
    self.has_request_id_set_ = 1
    self.request_id_set_ = x

  def clear_request_id_set(self):
    if self.has_request_id_set_:
      self.has_request_id_set_ = 0
      self.request_id_set_ = 0

  def has_request_id_set(self): return self.has_request_id_set_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_request_id()): self.set_request_id(x.request_id())
    if (x.has_request_id_set()): self.set_request_id_set(x.request_id_set())

  def Equals(self, x):
    if x is self: return 1
    if self.has_request_id_ != x.has_request_id_: return 0
    if self.has_request_id_ and self.request_id_ != x.request_id_: return 0
    if self.has_request_id_set_ != x.has_request_id_set_: return 0
    if self.has_request_id_set_ and self.request_id_set_ != x.request_id_set_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_request_id_): n += 1 + self.lengthString(len(self.request_id_))
    if (self.has_request_id_set_): n += 3
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_request_id_): n += 1 + self.lengthString(len(self.request_id_))
    if (self.has_request_id_set_): n += 3
    return n

  def Clear(self):
    self.clear_request_id()
    self.clear_request_id_set()

  def OutputUnchecked(self, out):
    if (self.has_request_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.request_id_)
    if (self.has_request_id_set_):
      out.putVarInt32(808)
      out.putBoolean(self.request_id_set_)

  def OutputPartial(self, out):
    if (self.has_request_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.request_id_)
    if (self.has_request_id_set_):
      out.putVarInt32(808)
      out.putBoolean(self.request_id_set_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_request_id(d.getPrefixedString())
        continue
      if tt == 808:
        self.set_request_id_set(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_request_id_: res+=prefix+("request_id: %s\n" % self.DebugFormatString(self.request_id_))
    if self.has_request_id_set_: res+=prefix+("request_id_set: %s\n" % self.DebugFormatBool(self.request_id_set_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  krequest_id = 1
  krequest_id_set = 101

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "request_id",
    101: "request_id_set",
  }, 101)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    101: ProtocolBuffer.Encoder.NUMERIC,
  }, 101, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.LogOffset'
class LogLine(ProtocolBuffer.ProtocolMessage):
  has_time_ = 0
  time_ = 0
  has_level_ = 0
  level_ = 0
  has_log_message_ = 0
  log_message_ = ""
  has_source_location_ = 0
  source_location_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def time(self): return self.time_

  def set_time(self, x):
    self.has_time_ = 1
    self.time_ = x

  def clear_time(self):
    if self.has_time_:
      self.has_time_ = 0
      self.time_ = 0

  def has_time(self): return self.has_time_

  def level(self): return self.level_

  def set_level(self, x):
    self.has_level_ = 1
    self.level_ = x

  def clear_level(self):
    if self.has_level_:
      self.has_level_ = 0
      self.level_ = 0

  def has_level(self): return self.has_level_

  def log_message(self): return self.log_message_

  def set_log_message(self, x):
    self.has_log_message_ = 1
    self.log_message_ = x

  def clear_log_message(self):
    if self.has_log_message_:
      self.has_log_message_ = 0
      self.log_message_ = ""

  def has_log_message(self): return self.has_log_message_

  def source_location(self):
    if self.source_location_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.source_location_ is None: self.source_location_ = SourceLocation()
      finally:
        self.lazy_init_lock_.release()
    return self.source_location_

  def mutable_source_location(self): self.has_source_location_ = 1; return self.source_location()

  def clear_source_location(self):

    if self.has_source_location_:
      self.has_source_location_ = 0;
      if self.source_location_ is not None: self.source_location_.Clear()

  def has_source_location(self): return self.has_source_location_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_time()): self.set_time(x.time())
    if (x.has_level()): self.set_level(x.level())
    if (x.has_log_message()): self.set_log_message(x.log_message())
    if (x.has_source_location()): self.mutable_source_location().MergeFrom(x.source_location())

  def Equals(self, x):
    if x is self: return 1
    if self.has_time_ != x.has_time_: return 0
    if self.has_time_ and self.time_ != x.time_: return 0
    if self.has_level_ != x.has_level_: return 0
    if self.has_level_ and self.level_ != x.level_: return 0
    if self.has_log_message_ != x.has_log_message_: return 0
    if self.has_log_message_ and self.log_message_ != x.log_message_: return 0
    if self.has_source_location_ != x.has_source_location_: return 0
    if self.has_source_location_ and self.source_location_ != x.source_location_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_time_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: time not set.')
    if (not self.has_level_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: level not set.')
    if (not self.has_log_message_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: log_message not set.')
    if (self.has_source_location_ and not self.source_location_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.time_)
    n += self.lengthVarInt64(self.level_)
    n += self.lengthString(len(self.log_message_))
    if (self.has_source_location_): n += 1 + self.lengthString(self.source_location_.ByteSize())
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_time_):
      n += 1
      n += self.lengthVarInt64(self.time_)
    if (self.has_level_):
      n += 1
      n += self.lengthVarInt64(self.level_)
    if (self.has_log_message_):
      n += 1
      n += self.lengthString(len(self.log_message_))
    if (self.has_source_location_): n += 1 + self.lengthString(self.source_location_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_time()
    self.clear_level()
    self.clear_log_message()
    self.clear_source_location()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt64(self.time_)
    out.putVarInt32(16)
    out.putVarInt32(self.level_)
    out.putVarInt32(26)
    out.putPrefixedString(self.log_message_)
    if (self.has_source_location_):
      out.putVarInt32(34)
      out.putVarInt32(self.source_location_.ByteSize())
      self.source_location_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_time_):
      out.putVarInt32(8)
      out.putVarInt64(self.time_)
    if (self.has_level_):
      out.putVarInt32(16)
      out.putVarInt32(self.level_)
    if (self.has_log_message_):
      out.putVarInt32(26)
      out.putPrefixedString(self.log_message_)
    if (self.has_source_location_):
      out.putVarInt32(34)
      out.putVarInt32(self.source_location_.ByteSizePartial())
      self.source_location_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_time(d.getVarInt64())
        continue
      if tt == 16:
        self.set_level(d.getVarInt32())
        continue
      if tt == 26:
        self.set_log_message(d.getPrefixedString())
        continue
      if tt == 34:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_source_location().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_time_: res+=prefix+("time: %s\n" % self.DebugFormatInt64(self.time_))
    if self.has_level_: res+=prefix+("level: %s\n" % self.DebugFormatInt32(self.level_))
    if self.has_log_message_: res+=prefix+("log_message: %s\n" % self.DebugFormatString(self.log_message_))
    if self.has_source_location_:
      res+=prefix+"source_location <\n"
      res+=self.source_location_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktime = 1
  klevel = 2
  klog_message = 3
  ksource_location = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "time",
    2: "level",
    3: "log_message",
    4: "source_location",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.LogLine'
class RequestLog(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_module_id_ = 0
  module_id_ = "default"
  has_version_id_ = 0
  version_id_ = ""
  has_request_id_ = 0
  request_id_ = ""
  has_offset_ = 0
  offset_ = None
  has_ip_ = 0
  ip_ = ""
  has_nickname_ = 0
  nickname_ = ""
  has_start_time_ = 0
  start_time_ = 0
  has_end_time_ = 0
  end_time_ = 0
  has_latency_ = 0
  latency_ = 0
  has_mcycles_ = 0
  mcycles_ = 0
  has_method_ = 0
  method_ = ""
  has_resource_ = 0
  resource_ = ""
  has_http_version_ = 0
  http_version_ = ""
  has_status_ = 0
  status_ = 0
  has_response_size_ = 0
  response_size_ = 0
  has_referrer_ = 0
  referrer_ = ""
  has_user_agent_ = 0
  user_agent_ = ""
  has_url_map_entry_ = 0
  url_map_entry_ = ""
  has_combined_ = 0
  combined_ = ""
  has_api_mcycles_ = 0
  api_mcycles_ = 0
  has_host_ = 0
  host_ = ""
  has_cost_ = 0
  cost_ = 0.0
  has_task_queue_name_ = 0
  task_queue_name_ = ""
  has_task_name_ = 0
  task_name_ = ""
  has_was_loading_request_ = 0
  was_loading_request_ = 0
  has_pending_time_ = 0
  pending_time_ = 0
  has_replica_index_ = 0
  replica_index_ = -1
  has_finished_ = 0
  finished_ = 1
  has_clone_key_ = 0
  clone_key_ = ""
  has_lines_incomplete_ = 0
  lines_incomplete_ = 0
  has_app_engine_release_ = 0
  app_engine_release_ = ""
  has_trace_id_ = 0
  trace_id_ = ""
  has_exit_reason_ = 0
  exit_reason_ = 0
  has_was_throttled_for_time_ = 0
  was_throttled_for_time_ = 0
  has_was_throttled_for_requests_ = 0
  was_throttled_for_requests_ = 0
  has_throttled_time_ = 0
  throttled_time_ = 0
  has_server_name_ = 0
  server_name_ = ""

  def __init__(self, contents=None):
    self.line_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
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

  def module_id(self): return self.module_id_

  def set_module_id(self, x):
    self.has_module_id_ = 1
    self.module_id_ = x

  def clear_module_id(self):
    if self.has_module_id_:
      self.has_module_id_ = 0
      self.module_id_ = "default"

  def has_module_id(self): return self.has_module_id_

  def version_id(self): return self.version_id_

  def set_version_id(self, x):
    self.has_version_id_ = 1
    self.version_id_ = x

  def clear_version_id(self):
    if self.has_version_id_:
      self.has_version_id_ = 0
      self.version_id_ = ""

  def has_version_id(self): return self.has_version_id_

  def request_id(self): return self.request_id_

  def set_request_id(self, x):
    self.has_request_id_ = 1
    self.request_id_ = x

  def clear_request_id(self):
    if self.has_request_id_:
      self.has_request_id_ = 0
      self.request_id_ = ""

  def has_request_id(self): return self.has_request_id_

  def offset(self):
    if self.offset_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.offset_ is None: self.offset_ = LogOffset()
      finally:
        self.lazy_init_lock_.release()
    return self.offset_

  def mutable_offset(self): self.has_offset_ = 1; return self.offset()

  def clear_offset(self):

    if self.has_offset_:
      self.has_offset_ = 0;
      if self.offset_ is not None: self.offset_.Clear()

  def has_offset(self): return self.has_offset_

  def ip(self): return self.ip_

  def set_ip(self, x):
    self.has_ip_ = 1
    self.ip_ = x

  def clear_ip(self):
    if self.has_ip_:
      self.has_ip_ = 0
      self.ip_ = ""

  def has_ip(self): return self.has_ip_

  def nickname(self): return self.nickname_

  def set_nickname(self, x):
    self.has_nickname_ = 1
    self.nickname_ = x

  def clear_nickname(self):
    if self.has_nickname_:
      self.has_nickname_ = 0
      self.nickname_ = ""

  def has_nickname(self): return self.has_nickname_

  def start_time(self): return self.start_time_

  def set_start_time(self, x):
    self.has_start_time_ = 1
    self.start_time_ = x

  def clear_start_time(self):
    if self.has_start_time_:
      self.has_start_time_ = 0
      self.start_time_ = 0

  def has_start_time(self): return self.has_start_time_

  def end_time(self): return self.end_time_

  def set_end_time(self, x):
    self.has_end_time_ = 1
    self.end_time_ = x

  def clear_end_time(self):
    if self.has_end_time_:
      self.has_end_time_ = 0
      self.end_time_ = 0

  def has_end_time(self): return self.has_end_time_

  def latency(self): return self.latency_

  def set_latency(self, x):
    self.has_latency_ = 1
    self.latency_ = x

  def clear_latency(self):
    if self.has_latency_:
      self.has_latency_ = 0
      self.latency_ = 0

  def has_latency(self): return self.has_latency_

  def mcycles(self): return self.mcycles_

  def set_mcycles(self, x):
    self.has_mcycles_ = 1
    self.mcycles_ = x

  def clear_mcycles(self):
    if self.has_mcycles_:
      self.has_mcycles_ = 0
      self.mcycles_ = 0

  def has_mcycles(self): return self.has_mcycles_

  def method(self): return self.method_

  def set_method(self, x):
    self.has_method_ = 1
    self.method_ = x

  def clear_method(self):
    if self.has_method_:
      self.has_method_ = 0
      self.method_ = ""

  def has_method(self): return self.has_method_

  def resource(self): return self.resource_

  def set_resource(self, x):
    self.has_resource_ = 1
    self.resource_ = x

  def clear_resource(self):
    if self.has_resource_:
      self.has_resource_ = 0
      self.resource_ = ""

  def has_resource(self): return self.has_resource_

  def http_version(self): return self.http_version_

  def set_http_version(self, x):
    self.has_http_version_ = 1
    self.http_version_ = x

  def clear_http_version(self):
    if self.has_http_version_:
      self.has_http_version_ = 0
      self.http_version_ = ""

  def has_http_version(self): return self.has_http_version_

  def status(self): return self.status_

  def set_status(self, x):
    self.has_status_ = 1
    self.status_ = x

  def clear_status(self):
    if self.has_status_:
      self.has_status_ = 0
      self.status_ = 0

  def has_status(self): return self.has_status_

  def response_size(self): return self.response_size_

  def set_response_size(self, x):
    self.has_response_size_ = 1
    self.response_size_ = x

  def clear_response_size(self):
    if self.has_response_size_:
      self.has_response_size_ = 0
      self.response_size_ = 0

  def has_response_size(self): return self.has_response_size_

  def referrer(self): return self.referrer_

  def set_referrer(self, x):
    self.has_referrer_ = 1
    self.referrer_ = x

  def clear_referrer(self):
    if self.has_referrer_:
      self.has_referrer_ = 0
      self.referrer_ = ""

  def has_referrer(self): return self.has_referrer_

  def user_agent(self): return self.user_agent_

  def set_user_agent(self, x):
    self.has_user_agent_ = 1
    self.user_agent_ = x

  def clear_user_agent(self):
    if self.has_user_agent_:
      self.has_user_agent_ = 0
      self.user_agent_ = ""

  def has_user_agent(self): return self.has_user_agent_

  def url_map_entry(self): return self.url_map_entry_

  def set_url_map_entry(self, x):
    self.has_url_map_entry_ = 1
    self.url_map_entry_ = x

  def clear_url_map_entry(self):
    if self.has_url_map_entry_:
      self.has_url_map_entry_ = 0
      self.url_map_entry_ = ""

  def has_url_map_entry(self): return self.has_url_map_entry_

  def combined(self): return self.combined_

  def set_combined(self, x):
    self.has_combined_ = 1
    self.combined_ = x

  def clear_combined(self):
    if self.has_combined_:
      self.has_combined_ = 0
      self.combined_ = ""

  def has_combined(self): return self.has_combined_

  def api_mcycles(self): return self.api_mcycles_

  def set_api_mcycles(self, x):
    self.has_api_mcycles_ = 1
    self.api_mcycles_ = x

  def clear_api_mcycles(self):
    if self.has_api_mcycles_:
      self.has_api_mcycles_ = 0
      self.api_mcycles_ = 0

  def has_api_mcycles(self): return self.has_api_mcycles_

  def host(self): return self.host_

  def set_host(self, x):
    self.has_host_ = 1
    self.host_ = x

  def clear_host(self):
    if self.has_host_:
      self.has_host_ = 0
      self.host_ = ""

  def has_host(self): return self.has_host_

  def cost(self): return self.cost_

  def set_cost(self, x):
    self.has_cost_ = 1
    self.cost_ = x

  def clear_cost(self):
    if self.has_cost_:
      self.has_cost_ = 0
      self.cost_ = 0.0

  def has_cost(self): return self.has_cost_

  def task_queue_name(self): return self.task_queue_name_

  def set_task_queue_name(self, x):
    self.has_task_queue_name_ = 1
    self.task_queue_name_ = x

  def clear_task_queue_name(self):
    if self.has_task_queue_name_:
      self.has_task_queue_name_ = 0
      self.task_queue_name_ = ""

  def has_task_queue_name(self): return self.has_task_queue_name_

  def task_name(self): return self.task_name_

  def set_task_name(self, x):
    self.has_task_name_ = 1
    self.task_name_ = x

  def clear_task_name(self):
    if self.has_task_name_:
      self.has_task_name_ = 0
      self.task_name_ = ""

  def has_task_name(self): return self.has_task_name_

  def was_loading_request(self): return self.was_loading_request_

  def set_was_loading_request(self, x):
    self.has_was_loading_request_ = 1
    self.was_loading_request_ = x

  def clear_was_loading_request(self):
    if self.has_was_loading_request_:
      self.has_was_loading_request_ = 0
      self.was_loading_request_ = 0

  def has_was_loading_request(self): return self.has_was_loading_request_

  def pending_time(self): return self.pending_time_

  def set_pending_time(self, x):
    self.has_pending_time_ = 1
    self.pending_time_ = x

  def clear_pending_time(self):
    if self.has_pending_time_:
      self.has_pending_time_ = 0
      self.pending_time_ = 0

  def has_pending_time(self): return self.has_pending_time_

  def replica_index(self): return self.replica_index_

  def set_replica_index(self, x):
    self.has_replica_index_ = 1
    self.replica_index_ = x

  def clear_replica_index(self):
    if self.has_replica_index_:
      self.has_replica_index_ = 0
      self.replica_index_ = -1

  def has_replica_index(self): return self.has_replica_index_

  def finished(self): return self.finished_

  def set_finished(self, x):
    self.has_finished_ = 1
    self.finished_ = x

  def clear_finished(self):
    if self.has_finished_:
      self.has_finished_ = 0
      self.finished_ = 1

  def has_finished(self): return self.has_finished_

  def clone_key(self): return self.clone_key_

  def set_clone_key(self, x):
    self.has_clone_key_ = 1
    self.clone_key_ = x

  def clear_clone_key(self):
    if self.has_clone_key_:
      self.has_clone_key_ = 0
      self.clone_key_ = ""

  def has_clone_key(self): return self.has_clone_key_

  def line_size(self): return len(self.line_)
  def line_list(self): return self.line_

  def line(self, i):
    return self.line_[i]

  def mutable_line(self, i):
    return self.line_[i]

  def add_line(self):
    x = LogLine()
    self.line_.append(x)
    return x

  def clear_line(self):
    self.line_ = []
  def lines_incomplete(self): return self.lines_incomplete_

  def set_lines_incomplete(self, x):
    self.has_lines_incomplete_ = 1
    self.lines_incomplete_ = x

  def clear_lines_incomplete(self):
    if self.has_lines_incomplete_:
      self.has_lines_incomplete_ = 0
      self.lines_incomplete_ = 0

  def has_lines_incomplete(self): return self.has_lines_incomplete_

  def app_engine_release(self): return self.app_engine_release_

  def set_app_engine_release(self, x):
    self.has_app_engine_release_ = 1
    self.app_engine_release_ = x

  def clear_app_engine_release(self):
    if self.has_app_engine_release_:
      self.has_app_engine_release_ = 0
      self.app_engine_release_ = ""

  def has_app_engine_release(self): return self.has_app_engine_release_

  def trace_id(self): return self.trace_id_

  def set_trace_id(self, x):
    self.has_trace_id_ = 1
    self.trace_id_ = x

  def clear_trace_id(self):
    if self.has_trace_id_:
      self.has_trace_id_ = 0
      self.trace_id_ = ""

  def has_trace_id(self): return self.has_trace_id_

  def exit_reason(self): return self.exit_reason_

  def set_exit_reason(self, x):
    self.has_exit_reason_ = 1
    self.exit_reason_ = x

  def clear_exit_reason(self):
    if self.has_exit_reason_:
      self.has_exit_reason_ = 0
      self.exit_reason_ = 0

  def has_exit_reason(self): return self.has_exit_reason_

  def was_throttled_for_time(self): return self.was_throttled_for_time_

  def set_was_throttled_for_time(self, x):
    self.has_was_throttled_for_time_ = 1
    self.was_throttled_for_time_ = x

  def clear_was_throttled_for_time(self):
    if self.has_was_throttled_for_time_:
      self.has_was_throttled_for_time_ = 0
      self.was_throttled_for_time_ = 0

  def has_was_throttled_for_time(self): return self.has_was_throttled_for_time_

  def was_throttled_for_requests(self): return self.was_throttled_for_requests_

  def set_was_throttled_for_requests(self, x):
    self.has_was_throttled_for_requests_ = 1
    self.was_throttled_for_requests_ = x

  def clear_was_throttled_for_requests(self):
    if self.has_was_throttled_for_requests_:
      self.has_was_throttled_for_requests_ = 0
      self.was_throttled_for_requests_ = 0

  def has_was_throttled_for_requests(self): return self.has_was_throttled_for_requests_

  def throttled_time(self): return self.throttled_time_

  def set_throttled_time(self, x):
    self.has_throttled_time_ = 1
    self.throttled_time_ = x

  def clear_throttled_time(self):
    if self.has_throttled_time_:
      self.has_throttled_time_ = 0
      self.throttled_time_ = 0

  def has_throttled_time(self): return self.has_throttled_time_

  def server_name(self): return self.server_name_

  def set_server_name(self, x):
    self.has_server_name_ = 1
    self.server_name_ = x

  def clear_server_name(self):
    if self.has_server_name_:
      self.has_server_name_ = 0
      self.server_name_ = ""

  def has_server_name(self): return self.has_server_name_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_module_id()): self.set_module_id(x.module_id())
    if (x.has_version_id()): self.set_version_id(x.version_id())
    if (x.has_request_id()): self.set_request_id(x.request_id())
    if (x.has_offset()): self.mutable_offset().MergeFrom(x.offset())
    if (x.has_ip()): self.set_ip(x.ip())
    if (x.has_nickname()): self.set_nickname(x.nickname())
    if (x.has_start_time()): self.set_start_time(x.start_time())
    if (x.has_end_time()): self.set_end_time(x.end_time())
    if (x.has_latency()): self.set_latency(x.latency())
    if (x.has_mcycles()): self.set_mcycles(x.mcycles())
    if (x.has_method()): self.set_method(x.method())
    if (x.has_resource()): self.set_resource(x.resource())
    if (x.has_http_version()): self.set_http_version(x.http_version())
    if (x.has_status()): self.set_status(x.status())
    if (x.has_response_size()): self.set_response_size(x.response_size())
    if (x.has_referrer()): self.set_referrer(x.referrer())
    if (x.has_user_agent()): self.set_user_agent(x.user_agent())
    if (x.has_url_map_entry()): self.set_url_map_entry(x.url_map_entry())
    if (x.has_combined()): self.set_combined(x.combined())
    if (x.has_api_mcycles()): self.set_api_mcycles(x.api_mcycles())
    if (x.has_host()): self.set_host(x.host())
    if (x.has_cost()): self.set_cost(x.cost())
    if (x.has_task_queue_name()): self.set_task_queue_name(x.task_queue_name())
    if (x.has_task_name()): self.set_task_name(x.task_name())
    if (x.has_was_loading_request()): self.set_was_loading_request(x.was_loading_request())
    if (x.has_pending_time()): self.set_pending_time(x.pending_time())
    if (x.has_replica_index()): self.set_replica_index(x.replica_index())
    if (x.has_finished()): self.set_finished(x.finished())
    if (x.has_clone_key()): self.set_clone_key(x.clone_key())
    for i in xrange(x.line_size()): self.add_line().CopyFrom(x.line(i))
    if (x.has_lines_incomplete()): self.set_lines_incomplete(x.lines_incomplete())
    if (x.has_app_engine_release()): self.set_app_engine_release(x.app_engine_release())
    if (x.has_trace_id()): self.set_trace_id(x.trace_id())
    if (x.has_exit_reason()): self.set_exit_reason(x.exit_reason())
    if (x.has_was_throttled_for_time()): self.set_was_throttled_for_time(x.was_throttled_for_time())
    if (x.has_was_throttled_for_requests()): self.set_was_throttled_for_requests(x.was_throttled_for_requests())
    if (x.has_throttled_time()): self.set_throttled_time(x.throttled_time())
    if (x.has_server_name()): self.set_server_name(x.server_name())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_module_id_ != x.has_module_id_: return 0
    if self.has_module_id_ and self.module_id_ != x.module_id_: return 0
    if self.has_version_id_ != x.has_version_id_: return 0
    if self.has_version_id_ and self.version_id_ != x.version_id_: return 0
    if self.has_request_id_ != x.has_request_id_: return 0
    if self.has_request_id_ and self.request_id_ != x.request_id_: return 0
    if self.has_offset_ != x.has_offset_: return 0
    if self.has_offset_ and self.offset_ != x.offset_: return 0
    if self.has_ip_ != x.has_ip_: return 0
    if self.has_ip_ and self.ip_ != x.ip_: return 0
    if self.has_nickname_ != x.has_nickname_: return 0
    if self.has_nickname_ and self.nickname_ != x.nickname_: return 0
    if self.has_start_time_ != x.has_start_time_: return 0
    if self.has_start_time_ and self.start_time_ != x.start_time_: return 0
    if self.has_end_time_ != x.has_end_time_: return 0
    if self.has_end_time_ and self.end_time_ != x.end_time_: return 0
    if self.has_latency_ != x.has_latency_: return 0
    if self.has_latency_ and self.latency_ != x.latency_: return 0
    if self.has_mcycles_ != x.has_mcycles_: return 0
    if self.has_mcycles_ and self.mcycles_ != x.mcycles_: return 0
    if self.has_method_ != x.has_method_: return 0
    if self.has_method_ and self.method_ != x.method_: return 0
    if self.has_resource_ != x.has_resource_: return 0
    if self.has_resource_ and self.resource_ != x.resource_: return 0
    if self.has_http_version_ != x.has_http_version_: return 0
    if self.has_http_version_ and self.http_version_ != x.http_version_: return 0
    if self.has_status_ != x.has_status_: return 0
    if self.has_status_ and self.status_ != x.status_: return 0
    if self.has_response_size_ != x.has_response_size_: return 0
    if self.has_response_size_ and self.response_size_ != x.response_size_: return 0
    if self.has_referrer_ != x.has_referrer_: return 0
    if self.has_referrer_ and self.referrer_ != x.referrer_: return 0
    if self.has_user_agent_ != x.has_user_agent_: return 0
    if self.has_user_agent_ and self.user_agent_ != x.user_agent_: return 0
    if self.has_url_map_entry_ != x.has_url_map_entry_: return 0
    if self.has_url_map_entry_ and self.url_map_entry_ != x.url_map_entry_: return 0
    if self.has_combined_ != x.has_combined_: return 0
    if self.has_combined_ and self.combined_ != x.combined_: return 0
    if self.has_api_mcycles_ != x.has_api_mcycles_: return 0
    if self.has_api_mcycles_ and self.api_mcycles_ != x.api_mcycles_: return 0
    if self.has_host_ != x.has_host_: return 0
    if self.has_host_ and self.host_ != x.host_: return 0
    if self.has_cost_ != x.has_cost_: return 0
    if self.has_cost_ and self.cost_ != x.cost_: return 0
    if self.has_task_queue_name_ != x.has_task_queue_name_: return 0
    if self.has_task_queue_name_ and self.task_queue_name_ != x.task_queue_name_: return 0
    if self.has_task_name_ != x.has_task_name_: return 0
    if self.has_task_name_ and self.task_name_ != x.task_name_: return 0
    if self.has_was_loading_request_ != x.has_was_loading_request_: return 0
    if self.has_was_loading_request_ and self.was_loading_request_ != x.was_loading_request_: return 0
    if self.has_pending_time_ != x.has_pending_time_: return 0
    if self.has_pending_time_ and self.pending_time_ != x.pending_time_: return 0
    if self.has_replica_index_ != x.has_replica_index_: return 0
    if self.has_replica_index_ and self.replica_index_ != x.replica_index_: return 0
    if self.has_finished_ != x.has_finished_: return 0
    if self.has_finished_ and self.finished_ != x.finished_: return 0
    if self.has_clone_key_ != x.has_clone_key_: return 0
    if self.has_clone_key_ and self.clone_key_ != x.clone_key_: return 0
    if len(self.line_) != len(x.line_): return 0
    for e1, e2 in zip(self.line_, x.line_):
      if e1 != e2: return 0
    if self.has_lines_incomplete_ != x.has_lines_incomplete_: return 0
    if self.has_lines_incomplete_ and self.lines_incomplete_ != x.lines_incomplete_: return 0
    if self.has_app_engine_release_ != x.has_app_engine_release_: return 0
    if self.has_app_engine_release_ and self.app_engine_release_ != x.app_engine_release_: return 0
    if self.has_trace_id_ != x.has_trace_id_: return 0
    if self.has_trace_id_ and self.trace_id_ != x.trace_id_: return 0
    if self.has_exit_reason_ != x.has_exit_reason_: return 0
    if self.has_exit_reason_ and self.exit_reason_ != x.exit_reason_: return 0
    if self.has_was_throttled_for_time_ != x.has_was_throttled_for_time_: return 0
    if self.has_was_throttled_for_time_ and self.was_throttled_for_time_ != x.was_throttled_for_time_: return 0
    if self.has_was_throttled_for_requests_ != x.has_was_throttled_for_requests_: return 0
    if self.has_was_throttled_for_requests_ and self.was_throttled_for_requests_ != x.was_throttled_for_requests_: return 0
    if self.has_throttled_time_ != x.has_throttled_time_: return 0
    if self.has_throttled_time_ and self.throttled_time_ != x.throttled_time_: return 0
    if self.has_server_name_ != x.has_server_name_: return 0
    if self.has_server_name_ and self.server_name_ != x.server_name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_app_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: app_id not set.')
    if (not self.has_version_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: version_id not set.')
    if (not self.has_request_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: request_id not set.')
    if (self.has_offset_ and not self.offset_.IsInitialized(debug_strs)): initialized = 0
    if (not self.has_ip_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: ip not set.')
    if (not self.has_start_time_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: start_time not set.')
    if (not self.has_end_time_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: end_time not set.')
    if (not self.has_latency_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: latency not set.')
    if (not self.has_mcycles_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: mcycles not set.')
    if (not self.has_method_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: method not set.')
    if (not self.has_resource_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: resource not set.')
    if (not self.has_http_version_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: http_version not set.')
    if (not self.has_status_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: status not set.')
    if (not self.has_response_size_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: response_size not set.')
    if (not self.has_url_map_entry_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: url_map_entry not set.')
    if (not self.has_combined_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: combined not set.')
    for p in self.line_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.app_id_))
    if (self.has_module_id_): n += 2 + self.lengthString(len(self.module_id_))
    n += self.lengthString(len(self.version_id_))
    n += self.lengthString(len(self.request_id_))
    if (self.has_offset_): n += 2 + self.lengthString(self.offset_.ByteSize())
    n += self.lengthString(len(self.ip_))
    if (self.has_nickname_): n += 1 + self.lengthString(len(self.nickname_))
    n += self.lengthVarInt64(self.start_time_)
    n += self.lengthVarInt64(self.end_time_)
    n += self.lengthVarInt64(self.latency_)
    n += self.lengthVarInt64(self.mcycles_)
    n += self.lengthString(len(self.method_))
    n += self.lengthString(len(self.resource_))
    n += self.lengthString(len(self.http_version_))
    n += self.lengthVarInt64(self.status_)
    n += self.lengthVarInt64(self.response_size_)
    if (self.has_referrer_): n += 1 + self.lengthString(len(self.referrer_))
    if (self.has_user_agent_): n += 2 + self.lengthString(len(self.user_agent_))
    n += self.lengthString(len(self.url_map_entry_))
    n += self.lengthString(len(self.combined_))
    if (self.has_api_mcycles_): n += 2 + self.lengthVarInt64(self.api_mcycles_)
    if (self.has_host_): n += 2 + self.lengthString(len(self.host_))
    if (self.has_cost_): n += 10
    if (self.has_task_queue_name_): n += 2 + self.lengthString(len(self.task_queue_name_))
    if (self.has_task_name_): n += 2 + self.lengthString(len(self.task_name_))
    if (self.has_was_loading_request_): n += 3
    if (self.has_pending_time_): n += 2 + self.lengthVarInt64(self.pending_time_)
    if (self.has_replica_index_): n += 2 + self.lengthVarInt64(self.replica_index_)
    if (self.has_finished_): n += 3
    if (self.has_clone_key_): n += 2 + self.lengthString(len(self.clone_key_))
    n += 2 * len(self.line_)
    for i in xrange(len(self.line_)): n += self.lengthString(self.line_[i].ByteSize())
    if (self.has_lines_incomplete_): n += 3
    if (self.has_app_engine_release_): n += 2 + self.lengthString(len(self.app_engine_release_))
    if (self.has_trace_id_): n += 2 + self.lengthString(len(self.trace_id_))
    if (self.has_exit_reason_): n += 2 + self.lengthVarInt64(self.exit_reason_)
    if (self.has_was_throttled_for_time_): n += 3
    if (self.has_was_throttled_for_requests_): n += 3
    if (self.has_throttled_time_): n += 2 + self.lengthVarInt64(self.throttled_time_)
    if (self.has_server_name_): n += 2 + self.lengthString(len(self.server_name_))
    return n + 17

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_):
      n += 1
      n += self.lengthString(len(self.app_id_))
    if (self.has_module_id_): n += 2 + self.lengthString(len(self.module_id_))
    if (self.has_version_id_):
      n += 1
      n += self.lengthString(len(self.version_id_))
    if (self.has_request_id_):
      n += 1
      n += self.lengthString(len(self.request_id_))
    if (self.has_offset_): n += 2 + self.lengthString(self.offset_.ByteSizePartial())
    if (self.has_ip_):
      n += 1
      n += self.lengthString(len(self.ip_))
    if (self.has_nickname_): n += 1 + self.lengthString(len(self.nickname_))
    if (self.has_start_time_):
      n += 1
      n += self.lengthVarInt64(self.start_time_)
    if (self.has_end_time_):
      n += 1
      n += self.lengthVarInt64(self.end_time_)
    if (self.has_latency_):
      n += 1
      n += self.lengthVarInt64(self.latency_)
    if (self.has_mcycles_):
      n += 1
      n += self.lengthVarInt64(self.mcycles_)
    if (self.has_method_):
      n += 1
      n += self.lengthString(len(self.method_))
    if (self.has_resource_):
      n += 1
      n += self.lengthString(len(self.resource_))
    if (self.has_http_version_):
      n += 1
      n += self.lengthString(len(self.http_version_))
    if (self.has_status_):
      n += 1
      n += self.lengthVarInt64(self.status_)
    if (self.has_response_size_):
      n += 1
      n += self.lengthVarInt64(self.response_size_)
    if (self.has_referrer_): n += 1 + self.lengthString(len(self.referrer_))
    if (self.has_user_agent_): n += 2 + self.lengthString(len(self.user_agent_))
    if (self.has_url_map_entry_):
      n += 2
      n += self.lengthString(len(self.url_map_entry_))
    if (self.has_combined_):
      n += 2
      n += self.lengthString(len(self.combined_))
    if (self.has_api_mcycles_): n += 2 + self.lengthVarInt64(self.api_mcycles_)
    if (self.has_host_): n += 2 + self.lengthString(len(self.host_))
    if (self.has_cost_): n += 10
    if (self.has_task_queue_name_): n += 2 + self.lengthString(len(self.task_queue_name_))
    if (self.has_task_name_): n += 2 + self.lengthString(len(self.task_name_))
    if (self.has_was_loading_request_): n += 3
    if (self.has_pending_time_): n += 2 + self.lengthVarInt64(self.pending_time_)
    if (self.has_replica_index_): n += 2 + self.lengthVarInt64(self.replica_index_)
    if (self.has_finished_): n += 3
    if (self.has_clone_key_): n += 2 + self.lengthString(len(self.clone_key_))
    n += 2 * len(self.line_)
    for i in xrange(len(self.line_)): n += self.lengthString(self.line_[i].ByteSizePartial())
    if (self.has_lines_incomplete_): n += 3
    if (self.has_app_engine_release_): n += 2 + self.lengthString(len(self.app_engine_release_))
    if (self.has_trace_id_): n += 2 + self.lengthString(len(self.trace_id_))
    if (self.has_exit_reason_): n += 2 + self.lengthVarInt64(self.exit_reason_)
    if (self.has_was_throttled_for_time_): n += 3
    if (self.has_was_throttled_for_requests_): n += 3
    if (self.has_throttled_time_): n += 2 + self.lengthVarInt64(self.throttled_time_)
    if (self.has_server_name_): n += 2 + self.lengthString(len(self.server_name_))
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_module_id()
    self.clear_version_id()
    self.clear_request_id()
    self.clear_offset()
    self.clear_ip()
    self.clear_nickname()
    self.clear_start_time()
    self.clear_end_time()
    self.clear_latency()
    self.clear_mcycles()
    self.clear_method()
    self.clear_resource()
    self.clear_http_version()
    self.clear_status()
    self.clear_response_size()
    self.clear_referrer()
    self.clear_user_agent()
    self.clear_url_map_entry()
    self.clear_combined()
    self.clear_api_mcycles()
    self.clear_host()
    self.clear_cost()
    self.clear_task_queue_name()
    self.clear_task_name()
    self.clear_was_loading_request()
    self.clear_pending_time()
    self.clear_replica_index()
    self.clear_finished()
    self.clear_clone_key()
    self.clear_line()
    self.clear_lines_incomplete()
    self.clear_app_engine_release()
    self.clear_trace_id()
    self.clear_exit_reason()
    self.clear_was_throttled_for_time()
    self.clear_was_throttled_for_requests()
    self.clear_throttled_time()
    self.clear_server_name()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.app_id_)
    out.putVarInt32(18)
    out.putPrefixedString(self.version_id_)
    out.putVarInt32(26)
    out.putPrefixedString(self.request_id_)
    out.putVarInt32(34)
    out.putPrefixedString(self.ip_)
    if (self.has_nickname_):
      out.putVarInt32(42)
      out.putPrefixedString(self.nickname_)
    out.putVarInt32(48)
    out.putVarInt64(self.start_time_)
    out.putVarInt32(56)
    out.putVarInt64(self.end_time_)
    out.putVarInt32(64)
    out.putVarInt64(self.latency_)
    out.putVarInt32(72)
    out.putVarInt64(self.mcycles_)
    out.putVarInt32(82)
    out.putPrefixedString(self.method_)
    out.putVarInt32(90)
    out.putPrefixedString(self.resource_)
    out.putVarInt32(98)
    out.putPrefixedString(self.http_version_)
    out.putVarInt32(104)
    out.putVarInt32(self.status_)
    out.putVarInt32(112)
    out.putVarInt64(self.response_size_)
    if (self.has_referrer_):
      out.putVarInt32(122)
      out.putPrefixedString(self.referrer_)
    if (self.has_user_agent_):
      out.putVarInt32(130)
      out.putPrefixedString(self.user_agent_)
    out.putVarInt32(138)
    out.putPrefixedString(self.url_map_entry_)
    out.putVarInt32(146)
    out.putPrefixedString(self.combined_)
    if (self.has_api_mcycles_):
      out.putVarInt32(152)
      out.putVarInt64(self.api_mcycles_)
    if (self.has_host_):
      out.putVarInt32(162)
      out.putPrefixedString(self.host_)
    if (self.has_cost_):
      out.putVarInt32(169)
      out.putDouble(self.cost_)
    if (self.has_task_queue_name_):
      out.putVarInt32(178)
      out.putPrefixedString(self.task_queue_name_)
    if (self.has_task_name_):
      out.putVarInt32(186)
      out.putPrefixedString(self.task_name_)
    if (self.has_was_loading_request_):
      out.putVarInt32(192)
      out.putBoolean(self.was_loading_request_)
    if (self.has_pending_time_):
      out.putVarInt32(200)
      out.putVarInt64(self.pending_time_)
    if (self.has_replica_index_):
      out.putVarInt32(208)
      out.putVarInt32(self.replica_index_)
    if (self.has_finished_):
      out.putVarInt32(216)
      out.putBoolean(self.finished_)
    if (self.has_clone_key_):
      out.putVarInt32(226)
      out.putPrefixedString(self.clone_key_)
    for i in xrange(len(self.line_)):
      out.putVarInt32(234)
      out.putVarInt32(self.line_[i].ByteSize())
      self.line_[i].OutputUnchecked(out)
    if (self.has_exit_reason_):
      out.putVarInt32(240)
      out.putVarInt32(self.exit_reason_)
    if (self.has_was_throttled_for_time_):
      out.putVarInt32(248)
      out.putBoolean(self.was_throttled_for_time_)
    if (self.has_was_throttled_for_requests_):
      out.putVarInt32(256)
      out.putBoolean(self.was_throttled_for_requests_)
    if (self.has_throttled_time_):
      out.putVarInt32(264)
      out.putVarInt64(self.throttled_time_)
    if (self.has_server_name_):
      out.putVarInt32(274)
      out.putPrefixedString(self.server_name_)
    if (self.has_offset_):
      out.putVarInt32(282)
      out.putVarInt32(self.offset_.ByteSize())
      self.offset_.OutputUnchecked(out)
    if (self.has_lines_incomplete_):
      out.putVarInt32(288)
      out.putBoolean(self.lines_incomplete_)
    if (self.has_module_id_):
      out.putVarInt32(298)
      out.putPrefixedString(self.module_id_)
    if (self.has_app_engine_release_):
      out.putVarInt32(306)
      out.putPrefixedString(self.app_engine_release_)
    if (self.has_trace_id_):
      out.putVarInt32(314)
      out.putPrefixedString(self.trace_id_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    if (self.has_version_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_id_)
    if (self.has_request_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.request_id_)
    if (self.has_ip_):
      out.putVarInt32(34)
      out.putPrefixedString(self.ip_)
    if (self.has_nickname_):
      out.putVarInt32(42)
      out.putPrefixedString(self.nickname_)
    if (self.has_start_time_):
      out.putVarInt32(48)
      out.putVarInt64(self.start_time_)
    if (self.has_end_time_):
      out.putVarInt32(56)
      out.putVarInt64(self.end_time_)
    if (self.has_latency_):
      out.putVarInt32(64)
      out.putVarInt64(self.latency_)
    if (self.has_mcycles_):
      out.putVarInt32(72)
      out.putVarInt64(self.mcycles_)
    if (self.has_method_):
      out.putVarInt32(82)
      out.putPrefixedString(self.method_)
    if (self.has_resource_):
      out.putVarInt32(90)
      out.putPrefixedString(self.resource_)
    if (self.has_http_version_):
      out.putVarInt32(98)
      out.putPrefixedString(self.http_version_)
    if (self.has_status_):
      out.putVarInt32(104)
      out.putVarInt32(self.status_)
    if (self.has_response_size_):
      out.putVarInt32(112)
      out.putVarInt64(self.response_size_)
    if (self.has_referrer_):
      out.putVarInt32(122)
      out.putPrefixedString(self.referrer_)
    if (self.has_user_agent_):
      out.putVarInt32(130)
      out.putPrefixedString(self.user_agent_)
    if (self.has_url_map_entry_):
      out.putVarInt32(138)
      out.putPrefixedString(self.url_map_entry_)
    if (self.has_combined_):
      out.putVarInt32(146)
      out.putPrefixedString(self.combined_)
    if (self.has_api_mcycles_):
      out.putVarInt32(152)
      out.putVarInt64(self.api_mcycles_)
    if (self.has_host_):
      out.putVarInt32(162)
      out.putPrefixedString(self.host_)
    if (self.has_cost_):
      out.putVarInt32(169)
      out.putDouble(self.cost_)
    if (self.has_task_queue_name_):
      out.putVarInt32(178)
      out.putPrefixedString(self.task_queue_name_)
    if (self.has_task_name_):
      out.putVarInt32(186)
      out.putPrefixedString(self.task_name_)
    if (self.has_was_loading_request_):
      out.putVarInt32(192)
      out.putBoolean(self.was_loading_request_)
    if (self.has_pending_time_):
      out.putVarInt32(200)
      out.putVarInt64(self.pending_time_)
    if (self.has_replica_index_):
      out.putVarInt32(208)
      out.putVarInt32(self.replica_index_)
    if (self.has_finished_):
      out.putVarInt32(216)
      out.putBoolean(self.finished_)
    if (self.has_clone_key_):
      out.putVarInt32(226)
      out.putPrefixedString(self.clone_key_)
    for i in xrange(len(self.line_)):
      out.putVarInt32(234)
      out.putVarInt32(self.line_[i].ByteSizePartial())
      self.line_[i].OutputPartial(out)
    if (self.has_exit_reason_):
      out.putVarInt32(240)
      out.putVarInt32(self.exit_reason_)
    if (self.has_was_throttled_for_time_):
      out.putVarInt32(248)
      out.putBoolean(self.was_throttled_for_time_)
    if (self.has_was_throttled_for_requests_):
      out.putVarInt32(256)
      out.putBoolean(self.was_throttled_for_requests_)
    if (self.has_throttled_time_):
      out.putVarInt32(264)
      out.putVarInt64(self.throttled_time_)
    if (self.has_server_name_):
      out.putVarInt32(274)
      out.putPrefixedString(self.server_name_)
    if (self.has_offset_):
      out.putVarInt32(282)
      out.putVarInt32(self.offset_.ByteSizePartial())
      self.offset_.OutputPartial(out)
    if (self.has_lines_incomplete_):
      out.putVarInt32(288)
      out.putBoolean(self.lines_incomplete_)
    if (self.has_module_id_):
      out.putVarInt32(298)
      out.putPrefixedString(self.module_id_)
    if (self.has_app_engine_release_):
      out.putVarInt32(306)
      out.putPrefixedString(self.app_engine_release_)
    if (self.has_trace_id_):
      out.putVarInt32(314)
      out.putPrefixedString(self.trace_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_version_id(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_request_id(d.getPrefixedString())
        continue
      if tt == 34:
        self.set_ip(d.getPrefixedString())
        continue
      if tt == 42:
        self.set_nickname(d.getPrefixedString())
        continue
      if tt == 48:
        self.set_start_time(d.getVarInt64())
        continue
      if tt == 56:
        self.set_end_time(d.getVarInt64())
        continue
      if tt == 64:
        self.set_latency(d.getVarInt64())
        continue
      if tt == 72:
        self.set_mcycles(d.getVarInt64())
        continue
      if tt == 82:
        self.set_method(d.getPrefixedString())
        continue
      if tt == 90:
        self.set_resource(d.getPrefixedString())
        continue
      if tt == 98:
        self.set_http_version(d.getPrefixedString())
        continue
      if tt == 104:
        self.set_status(d.getVarInt32())
        continue
      if tt == 112:
        self.set_response_size(d.getVarInt64())
        continue
      if tt == 122:
        self.set_referrer(d.getPrefixedString())
        continue
      if tt == 130:
        self.set_user_agent(d.getPrefixedString())
        continue
      if tt == 138:
        self.set_url_map_entry(d.getPrefixedString())
        continue
      if tt == 146:
        self.set_combined(d.getPrefixedString())
        continue
      if tt == 152:
        self.set_api_mcycles(d.getVarInt64())
        continue
      if tt == 162:
        self.set_host(d.getPrefixedString())
        continue
      if tt == 169:
        self.set_cost(d.getDouble())
        continue
      if tt == 178:
        self.set_task_queue_name(d.getPrefixedString())
        continue
      if tt == 186:
        self.set_task_name(d.getPrefixedString())
        continue
      if tt == 192:
        self.set_was_loading_request(d.getBoolean())
        continue
      if tt == 200:
        self.set_pending_time(d.getVarInt64())
        continue
      if tt == 208:
        self.set_replica_index(d.getVarInt32())
        continue
      if tt == 216:
        self.set_finished(d.getBoolean())
        continue
      if tt == 226:
        self.set_clone_key(d.getPrefixedString())
        continue
      if tt == 234:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_line().TryMerge(tmp)
        continue
      if tt == 240:
        self.set_exit_reason(d.getVarInt32())
        continue
      if tt == 248:
        self.set_was_throttled_for_time(d.getBoolean())
        continue
      if tt == 256:
        self.set_was_throttled_for_requests(d.getBoolean())
        continue
      if tt == 264:
        self.set_throttled_time(d.getVarInt64())
        continue
      if tt == 274:
        self.set_server_name(d.getPrefixedString())
        continue
      if tt == 282:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_offset().TryMerge(tmp)
        continue
      if tt == 288:
        self.set_lines_incomplete(d.getBoolean())
        continue
      if tt == 298:
        self.set_module_id(d.getPrefixedString())
        continue
      if tt == 306:
        self.set_app_engine_release(d.getPrefixedString())
        continue
      if tt == 314:
        self.set_trace_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_module_id_: res+=prefix+("module_id: %s\n" % self.DebugFormatString(self.module_id_))
    if self.has_version_id_: res+=prefix+("version_id: %s\n" % self.DebugFormatString(self.version_id_))
    if self.has_request_id_: res+=prefix+("request_id: %s\n" % self.DebugFormatString(self.request_id_))
    if self.has_offset_:
      res+=prefix+"offset <\n"
      res+=self.offset_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_ip_: res+=prefix+("ip: %s\n" % self.DebugFormatString(self.ip_))
    if self.has_nickname_: res+=prefix+("nickname: %s\n" % self.DebugFormatString(self.nickname_))
    if self.has_start_time_: res+=prefix+("start_time: %s\n" % self.DebugFormatInt64(self.start_time_))
    if self.has_end_time_: res+=prefix+("end_time: %s\n" % self.DebugFormatInt64(self.end_time_))
    if self.has_latency_: res+=prefix+("latency: %s\n" % self.DebugFormatInt64(self.latency_))
    if self.has_mcycles_: res+=prefix+("mcycles: %s\n" % self.DebugFormatInt64(self.mcycles_))
    if self.has_method_: res+=prefix+("method: %s\n" % self.DebugFormatString(self.method_))
    if self.has_resource_: res+=prefix+("resource: %s\n" % self.DebugFormatString(self.resource_))
    if self.has_http_version_: res+=prefix+("http_version: %s\n" % self.DebugFormatString(self.http_version_))
    if self.has_status_: res+=prefix+("status: %s\n" % self.DebugFormatInt32(self.status_))
    if self.has_response_size_: res+=prefix+("response_size: %s\n" % self.DebugFormatInt64(self.response_size_))
    if self.has_referrer_: res+=prefix+("referrer: %s\n" % self.DebugFormatString(self.referrer_))
    if self.has_user_agent_: res+=prefix+("user_agent: %s\n" % self.DebugFormatString(self.user_agent_))
    if self.has_url_map_entry_: res+=prefix+("url_map_entry: %s\n" % self.DebugFormatString(self.url_map_entry_))
    if self.has_combined_: res+=prefix+("combined: %s\n" % self.DebugFormatString(self.combined_))
    if self.has_api_mcycles_: res+=prefix+("api_mcycles: %s\n" % self.DebugFormatInt64(self.api_mcycles_))
    if self.has_host_: res+=prefix+("host: %s\n" % self.DebugFormatString(self.host_))
    if self.has_cost_: res+=prefix+("cost: %s\n" % self.DebugFormat(self.cost_))
    if self.has_task_queue_name_: res+=prefix+("task_queue_name: %s\n" % self.DebugFormatString(self.task_queue_name_))
    if self.has_task_name_: res+=prefix+("task_name: %s\n" % self.DebugFormatString(self.task_name_))
    if self.has_was_loading_request_: res+=prefix+("was_loading_request: %s\n" % self.DebugFormatBool(self.was_loading_request_))
    if self.has_pending_time_: res+=prefix+("pending_time: %s\n" % self.DebugFormatInt64(self.pending_time_))
    if self.has_replica_index_: res+=prefix+("replica_index: %s\n" % self.DebugFormatInt32(self.replica_index_))
    if self.has_finished_: res+=prefix+("finished: %s\n" % self.DebugFormatBool(self.finished_))
    if self.has_clone_key_: res+=prefix+("clone_key: %s\n" % self.DebugFormatString(self.clone_key_))
    cnt=0
    for e in self.line_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("line%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_lines_incomplete_: res+=prefix+("lines_incomplete: %s\n" % self.DebugFormatBool(self.lines_incomplete_))
    if self.has_app_engine_release_: res+=prefix+("app_engine_release: %s\n" % self.DebugFormatString(self.app_engine_release_))
    if self.has_trace_id_: res+=prefix+("trace_id: %s\n" % self.DebugFormatString(self.trace_id_))
    if self.has_exit_reason_: res+=prefix+("exit_reason: %s\n" % self.DebugFormatInt32(self.exit_reason_))
    if self.has_was_throttled_for_time_: res+=prefix+("was_throttled_for_time: %s\n" % self.DebugFormatBool(self.was_throttled_for_time_))
    if self.has_was_throttled_for_requests_: res+=prefix+("was_throttled_for_requests: %s\n" % self.DebugFormatBool(self.was_throttled_for_requests_))
    if self.has_throttled_time_: res+=prefix+("throttled_time: %s\n" % self.DebugFormatInt64(self.throttled_time_))
    if self.has_server_name_: res+=prefix+("server_name: %s\n" % self.DebugFormatString(self.server_name_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  kmodule_id = 37
  kversion_id = 2
  krequest_id = 3
  koffset = 35
  kip = 4
  knickname = 5
  kstart_time = 6
  kend_time = 7
  klatency = 8
  kmcycles = 9
  kmethod = 10
  kresource = 11
  khttp_version = 12
  kstatus = 13
  kresponse_size = 14
  kreferrer = 15
  kuser_agent = 16
  kurl_map_entry = 17
  kcombined = 18
  kapi_mcycles = 19
  khost = 20
  kcost = 21
  ktask_queue_name = 22
  ktask_name = 23
  kwas_loading_request = 24
  kpending_time = 25
  kreplica_index = 26
  kfinished = 27
  kclone_key = 28
  kline = 29
  klines_incomplete = 36
  kapp_engine_release = 38
  ktrace_id = 39
  kexit_reason = 30
  kwas_throttled_for_time = 31
  kwas_throttled_for_requests = 32
  kthrottled_time = 33
  kserver_name = 34

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "version_id",
    3: "request_id",
    4: "ip",
    5: "nickname",
    6: "start_time",
    7: "end_time",
    8: "latency",
    9: "mcycles",
    10: "method",
    11: "resource",
    12: "http_version",
    13: "status",
    14: "response_size",
    15: "referrer",
    16: "user_agent",
    17: "url_map_entry",
    18: "combined",
    19: "api_mcycles",
    20: "host",
    21: "cost",
    22: "task_queue_name",
    23: "task_name",
    24: "was_loading_request",
    25: "pending_time",
    26: "replica_index",
    27: "finished",
    28: "clone_key",
    29: "line",
    30: "exit_reason",
    31: "was_throttled_for_time",
    32: "was_throttled_for_requests",
    33: "throttled_time",
    34: "server_name",
    35: "offset",
    36: "lines_incomplete",
    37: "module_id",
    38: "app_engine_release",
    39: "trace_id",
  }, 39)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.NUMERIC,
    7: ProtocolBuffer.Encoder.NUMERIC,
    8: ProtocolBuffer.Encoder.NUMERIC,
    9: ProtocolBuffer.Encoder.NUMERIC,
    10: ProtocolBuffer.Encoder.STRING,
    11: ProtocolBuffer.Encoder.STRING,
    12: ProtocolBuffer.Encoder.STRING,
    13: ProtocolBuffer.Encoder.NUMERIC,
    14: ProtocolBuffer.Encoder.NUMERIC,
    15: ProtocolBuffer.Encoder.STRING,
    16: ProtocolBuffer.Encoder.STRING,
    17: ProtocolBuffer.Encoder.STRING,
    18: ProtocolBuffer.Encoder.STRING,
    19: ProtocolBuffer.Encoder.NUMERIC,
    20: ProtocolBuffer.Encoder.STRING,
    21: ProtocolBuffer.Encoder.DOUBLE,
    22: ProtocolBuffer.Encoder.STRING,
    23: ProtocolBuffer.Encoder.STRING,
    24: ProtocolBuffer.Encoder.NUMERIC,
    25: ProtocolBuffer.Encoder.NUMERIC,
    26: ProtocolBuffer.Encoder.NUMERIC,
    27: ProtocolBuffer.Encoder.NUMERIC,
    28: ProtocolBuffer.Encoder.STRING,
    29: ProtocolBuffer.Encoder.STRING,
    30: ProtocolBuffer.Encoder.NUMERIC,
    31: ProtocolBuffer.Encoder.NUMERIC,
    32: ProtocolBuffer.Encoder.NUMERIC,
    33: ProtocolBuffer.Encoder.NUMERIC,
    34: ProtocolBuffer.Encoder.STRING,
    35: ProtocolBuffer.Encoder.STRING,
    36: ProtocolBuffer.Encoder.NUMERIC,
    37: ProtocolBuffer.Encoder.STRING,
    38: ProtocolBuffer.Encoder.STRING,
    39: ProtocolBuffer.Encoder.STRING,
  }, 39, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.RequestLog'
class LogModuleVersion(ProtocolBuffer.ProtocolMessage):
  has_module_id_ = 0
  module_id_ = "default"
  has_module_id_set_ = 0
  module_id_set_ = 0
  has_version_id_ = 0
  version_id_ = ""
  has_version_id_set_ = 0
  version_id_set_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def module_id(self): return self.module_id_

  def set_module_id(self, x):
    self.has_module_id_ = 1
    self.module_id_ = x

  def clear_module_id(self):
    if self.has_module_id_:
      self.has_module_id_ = 0
      self.module_id_ = "default"

  def has_module_id(self): return self.has_module_id_

  def module_id_set(self): return self.module_id_set_

  def set_module_id_set(self, x):
    self.has_module_id_set_ = 1
    self.module_id_set_ = x

  def clear_module_id_set(self):
    if self.has_module_id_set_:
      self.has_module_id_set_ = 0
      self.module_id_set_ = 0

  def has_module_id_set(self): return self.has_module_id_set_

  def version_id(self): return self.version_id_

  def set_version_id(self, x):
    self.has_version_id_ = 1
    self.version_id_ = x

  def clear_version_id(self):
    if self.has_version_id_:
      self.has_version_id_ = 0
      self.version_id_ = ""

  def has_version_id(self): return self.has_version_id_

  def version_id_set(self): return self.version_id_set_

  def set_version_id_set(self, x):
    self.has_version_id_set_ = 1
    self.version_id_set_ = x

  def clear_version_id_set(self):
    if self.has_version_id_set_:
      self.has_version_id_set_ = 0
      self.version_id_set_ = 0

  def has_version_id_set(self): return self.has_version_id_set_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_module_id()): self.set_module_id(x.module_id())
    if (x.has_module_id_set()): self.set_module_id_set(x.module_id_set())
    if (x.has_version_id()): self.set_version_id(x.version_id())
    if (x.has_version_id_set()): self.set_version_id_set(x.version_id_set())

  def Equals(self, x):
    if x is self: return 1
    if self.has_module_id_ != x.has_module_id_: return 0
    if self.has_module_id_ and self.module_id_ != x.module_id_: return 0
    if self.has_module_id_set_ != x.has_module_id_set_: return 0
    if self.has_module_id_set_ and self.module_id_set_ != x.module_id_set_: return 0
    if self.has_version_id_ != x.has_version_id_: return 0
    if self.has_version_id_ and self.version_id_ != x.version_id_: return 0
    if self.has_version_id_set_ != x.has_version_id_set_: return 0
    if self.has_version_id_set_ and self.version_id_set_ != x.version_id_set_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_module_id_): n += 1 + self.lengthString(len(self.module_id_))
    if (self.has_module_id_set_): n += 3
    if (self.has_version_id_): n += 1 + self.lengthString(len(self.version_id_))
    if (self.has_version_id_set_): n += 3
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_module_id_): n += 1 + self.lengthString(len(self.module_id_))
    if (self.has_module_id_set_): n += 3
    if (self.has_version_id_): n += 1 + self.lengthString(len(self.version_id_))
    if (self.has_version_id_set_): n += 3
    return n

  def Clear(self):
    self.clear_module_id()
    self.clear_module_id_set()
    self.clear_version_id()
    self.clear_version_id_set()

  def OutputUnchecked(self, out):
    if (self.has_module_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_id_)
    if (self.has_version_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_id_)
    if (self.has_module_id_set_):
      out.putVarInt32(808)
      out.putBoolean(self.module_id_set_)
    if (self.has_version_id_set_):
      out.putVarInt32(816)
      out.putBoolean(self.version_id_set_)

  def OutputPartial(self, out):
    if (self.has_module_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.module_id_)
    if (self.has_version_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_id_)
    if (self.has_module_id_set_):
      out.putVarInt32(808)
      out.putBoolean(self.module_id_set_)
    if (self.has_version_id_set_):
      out.putVarInt32(816)
      out.putBoolean(self.version_id_set_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_module_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_version_id(d.getPrefixedString())
        continue
      if tt == 808:
        self.set_module_id_set(d.getBoolean())
        continue
      if tt == 816:
        self.set_version_id_set(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_module_id_: res+=prefix+("module_id: %s\n" % self.DebugFormatString(self.module_id_))
    if self.has_module_id_set_: res+=prefix+("module_id_set: %s\n" % self.DebugFormatBool(self.module_id_set_))
    if self.has_version_id_: res+=prefix+("version_id: %s\n" % self.DebugFormatString(self.version_id_))
    if self.has_version_id_set_: res+=prefix+("version_id_set: %s\n" % self.DebugFormatBool(self.version_id_set_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kmodule_id = 1
  kmodule_id_set = 101
  kversion_id = 2
  kversion_id_set = 102

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "module_id",
    2: "version_id",
    101: "module_id_set",
    102: "version_id_set",
  }, 102)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    101: ProtocolBuffer.Encoder.NUMERIC,
    102: ProtocolBuffer.Encoder.NUMERIC,
  }, 102, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.LogModuleVersion'
class LogReadRequest(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_start_time_ = 0
  start_time_ = 0
  has_start_time_set_ = 0
  start_time_set_ = 0
  has_end_time_ = 0
  end_time_ = 0
  has_end_time_set_ = 0
  end_time_set_ = 0
  has_offset_ = 0
  offset_ = None
  has_minimum_log_level_ = 0
  minimum_log_level_ = 0
  has_minimum_log_level_set_ = 0
  minimum_log_level_set_ = 0
  has_include_incomplete_ = 0
  include_incomplete_ = 0
  has_count_ = 0
  count_ = 0
  has_count_set_ = 0
  count_set_ = 0
  has_combined_log_regex_ = 0
  combined_log_regex_ = ""
  has_combined_log_regex_set_ = 0
  combined_log_regex_set_ = 0
  has_host_regex_ = 0
  host_regex_ = ""
  has_host_regex_set_ = 0
  host_regex_set_ = 0
  has_replica_index_ = 0
  replica_index_ = 0
  has_replica_index_set_ = 0
  replica_index_set_ = 0
  has_include_app_logs_ = 0
  include_app_logs_ = 0
  has_app_logs_per_request_ = 0
  app_logs_per_request_ = 0
  has_app_logs_per_request_set_ = 0
  app_logs_per_request_set_ = 0
  has_include_host_ = 0
  include_host_ = 0
  has_include_all_ = 0
  include_all_ = 0
  has_cache_iterator_ = 0
  cache_iterator_ = 0
  has_num_shards_ = 0
  num_shards_ = 0
  has_num_shards_set_ = 0
  num_shards_set_ = 0

  def __init__(self, contents=None):
    self.version_id_ = []
    self.module_version_ = []
    self.request_id_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
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

  def version_id_size(self): return len(self.version_id_)
  def version_id_list(self): return self.version_id_

  def version_id(self, i):
    return self.version_id_[i]

  def set_version_id(self, i, x):
    self.version_id_[i] = x

  def add_version_id(self, x):
    self.version_id_.append(x)

  def clear_version_id(self):
    self.version_id_ = []

  def module_version_size(self): return len(self.module_version_)
  def module_version_list(self): return self.module_version_

  def module_version(self, i):
    return self.module_version_[i]

  def mutable_module_version(self, i):
    return self.module_version_[i]

  def add_module_version(self):
    x = LogModuleVersion()
    self.module_version_.append(x)
    return x

  def clear_module_version(self):
    self.module_version_ = []
  def start_time(self): return self.start_time_

  def set_start_time(self, x):
    self.has_start_time_ = 1
    self.start_time_ = x

  def clear_start_time(self):
    if self.has_start_time_:
      self.has_start_time_ = 0
      self.start_time_ = 0

  def has_start_time(self): return self.has_start_time_

  def start_time_set(self): return self.start_time_set_

  def set_start_time_set(self, x):
    self.has_start_time_set_ = 1
    self.start_time_set_ = x

  def clear_start_time_set(self):
    if self.has_start_time_set_:
      self.has_start_time_set_ = 0
      self.start_time_set_ = 0

  def has_start_time_set(self): return self.has_start_time_set_

  def end_time(self): return self.end_time_

  def set_end_time(self, x):
    self.has_end_time_ = 1
    self.end_time_ = x

  def clear_end_time(self):
    if self.has_end_time_:
      self.has_end_time_ = 0
      self.end_time_ = 0

  def has_end_time(self): return self.has_end_time_

  def end_time_set(self): return self.end_time_set_

  def set_end_time_set(self, x):
    self.has_end_time_set_ = 1
    self.end_time_set_ = x

  def clear_end_time_set(self):
    if self.has_end_time_set_:
      self.has_end_time_set_ = 0
      self.end_time_set_ = 0

  def has_end_time_set(self): return self.has_end_time_set_

  def offset(self):
    if self.offset_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.offset_ is None: self.offset_ = LogOffset()
      finally:
        self.lazy_init_lock_.release()
    return self.offset_

  def mutable_offset(self): self.has_offset_ = 1; return self.offset()

  def clear_offset(self):

    if self.has_offset_:
      self.has_offset_ = 0;
      if self.offset_ is not None: self.offset_.Clear()

  def has_offset(self): return self.has_offset_

  def request_id_size(self): return len(self.request_id_)
  def request_id_list(self): return self.request_id_

  def request_id(self, i):
    return self.request_id_[i]

  def set_request_id(self, i, x):
    self.request_id_[i] = x

  def add_request_id(self, x):
    self.request_id_.append(x)

  def clear_request_id(self):
    self.request_id_ = []

  def minimum_log_level(self): return self.minimum_log_level_

  def set_minimum_log_level(self, x):
    self.has_minimum_log_level_ = 1
    self.minimum_log_level_ = x

  def clear_minimum_log_level(self):
    if self.has_minimum_log_level_:
      self.has_minimum_log_level_ = 0
      self.minimum_log_level_ = 0

  def has_minimum_log_level(self): return self.has_minimum_log_level_

  def minimum_log_level_set(self): return self.minimum_log_level_set_

  def set_minimum_log_level_set(self, x):
    self.has_minimum_log_level_set_ = 1
    self.minimum_log_level_set_ = x

  def clear_minimum_log_level_set(self):
    if self.has_minimum_log_level_set_:
      self.has_minimum_log_level_set_ = 0
      self.minimum_log_level_set_ = 0

  def has_minimum_log_level_set(self): return self.has_minimum_log_level_set_

  def include_incomplete(self): return self.include_incomplete_

  def set_include_incomplete(self, x):
    self.has_include_incomplete_ = 1
    self.include_incomplete_ = x

  def clear_include_incomplete(self):
    if self.has_include_incomplete_:
      self.has_include_incomplete_ = 0
      self.include_incomplete_ = 0

  def has_include_incomplete(self): return self.has_include_incomplete_

  def count(self): return self.count_

  def set_count(self, x):
    self.has_count_ = 1
    self.count_ = x

  def clear_count(self):
    if self.has_count_:
      self.has_count_ = 0
      self.count_ = 0

  def has_count(self): return self.has_count_

  def count_set(self): return self.count_set_

  def set_count_set(self, x):
    self.has_count_set_ = 1
    self.count_set_ = x

  def clear_count_set(self):
    if self.has_count_set_:
      self.has_count_set_ = 0
      self.count_set_ = 0

  def has_count_set(self): return self.has_count_set_

  def combined_log_regex(self): return self.combined_log_regex_

  def set_combined_log_regex(self, x):
    self.has_combined_log_regex_ = 1
    self.combined_log_regex_ = x

  def clear_combined_log_regex(self):
    if self.has_combined_log_regex_:
      self.has_combined_log_regex_ = 0
      self.combined_log_regex_ = ""

  def has_combined_log_regex(self): return self.has_combined_log_regex_

  def combined_log_regex_set(self): return self.combined_log_regex_set_

  def set_combined_log_regex_set(self, x):
    self.has_combined_log_regex_set_ = 1
    self.combined_log_regex_set_ = x

  def clear_combined_log_regex_set(self):
    if self.has_combined_log_regex_set_:
      self.has_combined_log_regex_set_ = 0
      self.combined_log_regex_set_ = 0

  def has_combined_log_regex_set(self): return self.has_combined_log_regex_set_

  def host_regex(self): return self.host_regex_

  def set_host_regex(self, x):
    self.has_host_regex_ = 1
    self.host_regex_ = x

  def clear_host_regex(self):
    if self.has_host_regex_:
      self.has_host_regex_ = 0
      self.host_regex_ = ""

  def has_host_regex(self): return self.has_host_regex_

  def host_regex_set(self): return self.host_regex_set_

  def set_host_regex_set(self, x):
    self.has_host_regex_set_ = 1
    self.host_regex_set_ = x

  def clear_host_regex_set(self):
    if self.has_host_regex_set_:
      self.has_host_regex_set_ = 0
      self.host_regex_set_ = 0

  def has_host_regex_set(self): return self.has_host_regex_set_

  def replica_index(self): return self.replica_index_

  def set_replica_index(self, x):
    self.has_replica_index_ = 1
    self.replica_index_ = x

  def clear_replica_index(self):
    if self.has_replica_index_:
      self.has_replica_index_ = 0
      self.replica_index_ = 0

  def has_replica_index(self): return self.has_replica_index_

  def replica_index_set(self): return self.replica_index_set_

  def set_replica_index_set(self, x):
    self.has_replica_index_set_ = 1
    self.replica_index_set_ = x

  def clear_replica_index_set(self):
    if self.has_replica_index_set_:
      self.has_replica_index_set_ = 0
      self.replica_index_set_ = 0

  def has_replica_index_set(self): return self.has_replica_index_set_

  def include_app_logs(self): return self.include_app_logs_

  def set_include_app_logs(self, x):
    self.has_include_app_logs_ = 1
    self.include_app_logs_ = x

  def clear_include_app_logs(self):
    if self.has_include_app_logs_:
      self.has_include_app_logs_ = 0
      self.include_app_logs_ = 0

  def has_include_app_logs(self): return self.has_include_app_logs_

  def app_logs_per_request(self): return self.app_logs_per_request_

  def set_app_logs_per_request(self, x):
    self.has_app_logs_per_request_ = 1
    self.app_logs_per_request_ = x

  def clear_app_logs_per_request(self):
    if self.has_app_logs_per_request_:
      self.has_app_logs_per_request_ = 0
      self.app_logs_per_request_ = 0

  def has_app_logs_per_request(self): return self.has_app_logs_per_request_

  def app_logs_per_request_set(self): return self.app_logs_per_request_set_

  def set_app_logs_per_request_set(self, x):
    self.has_app_logs_per_request_set_ = 1
    self.app_logs_per_request_set_ = x

  def clear_app_logs_per_request_set(self):
    if self.has_app_logs_per_request_set_:
      self.has_app_logs_per_request_set_ = 0
      self.app_logs_per_request_set_ = 0

  def has_app_logs_per_request_set(self): return self.has_app_logs_per_request_set_

  def include_host(self): return self.include_host_

  def set_include_host(self, x):
    self.has_include_host_ = 1
    self.include_host_ = x

  def clear_include_host(self):
    if self.has_include_host_:
      self.has_include_host_ = 0
      self.include_host_ = 0

  def has_include_host(self): return self.has_include_host_

  def include_all(self): return self.include_all_

  def set_include_all(self, x):
    self.has_include_all_ = 1
    self.include_all_ = x

  def clear_include_all(self):
    if self.has_include_all_:
      self.has_include_all_ = 0
      self.include_all_ = 0

  def has_include_all(self): return self.has_include_all_

  def cache_iterator(self): return self.cache_iterator_

  def set_cache_iterator(self, x):
    self.has_cache_iterator_ = 1
    self.cache_iterator_ = x

  def clear_cache_iterator(self):
    if self.has_cache_iterator_:
      self.has_cache_iterator_ = 0
      self.cache_iterator_ = 0

  def has_cache_iterator(self): return self.has_cache_iterator_

  def num_shards(self): return self.num_shards_

  def set_num_shards(self, x):
    self.has_num_shards_ = 1
    self.num_shards_ = x

  def clear_num_shards(self):
    if self.has_num_shards_:
      self.has_num_shards_ = 0
      self.num_shards_ = 0

  def has_num_shards(self): return self.has_num_shards_

  def num_shards_set(self): return self.num_shards_set_

  def set_num_shards_set(self, x):
    self.has_num_shards_set_ = 1
    self.num_shards_set_ = x

  def clear_num_shards_set(self):
    if self.has_num_shards_set_:
      self.has_num_shards_set_ = 0
      self.num_shards_set_ = 0

  def has_num_shards_set(self): return self.has_num_shards_set_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    for i in xrange(x.version_id_size()): self.add_version_id(x.version_id(i))
    for i in xrange(x.module_version_size()): self.add_module_version().CopyFrom(x.module_version(i))
    if (x.has_start_time()): self.set_start_time(x.start_time())
    if (x.has_start_time_set()): self.set_start_time_set(x.start_time_set())
    if (x.has_end_time()): self.set_end_time(x.end_time())
    if (x.has_end_time_set()): self.set_end_time_set(x.end_time_set())
    if (x.has_offset()): self.mutable_offset().MergeFrom(x.offset())
    for i in xrange(x.request_id_size()): self.add_request_id(x.request_id(i))
    if (x.has_minimum_log_level()): self.set_minimum_log_level(x.minimum_log_level())
    if (x.has_minimum_log_level_set()): self.set_minimum_log_level_set(x.minimum_log_level_set())
    if (x.has_include_incomplete()): self.set_include_incomplete(x.include_incomplete())
    if (x.has_count()): self.set_count(x.count())
    if (x.has_count_set()): self.set_count_set(x.count_set())
    if (x.has_combined_log_regex()): self.set_combined_log_regex(x.combined_log_regex())
    if (x.has_combined_log_regex_set()): self.set_combined_log_regex_set(x.combined_log_regex_set())
    if (x.has_host_regex()): self.set_host_regex(x.host_regex())
    if (x.has_host_regex_set()): self.set_host_regex_set(x.host_regex_set())
    if (x.has_replica_index()): self.set_replica_index(x.replica_index())
    if (x.has_replica_index_set()): self.set_replica_index_set(x.replica_index_set())
    if (x.has_include_app_logs()): self.set_include_app_logs(x.include_app_logs())
    if (x.has_app_logs_per_request()): self.set_app_logs_per_request(x.app_logs_per_request())
    if (x.has_app_logs_per_request_set()): self.set_app_logs_per_request_set(x.app_logs_per_request_set())
    if (x.has_include_host()): self.set_include_host(x.include_host())
    if (x.has_include_all()): self.set_include_all(x.include_all())
    if (x.has_cache_iterator()): self.set_cache_iterator(x.cache_iterator())
    if (x.has_num_shards()): self.set_num_shards(x.num_shards())
    if (x.has_num_shards_set()): self.set_num_shards_set(x.num_shards_set())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if len(self.version_id_) != len(x.version_id_): return 0
    for e1, e2 in zip(self.version_id_, x.version_id_):
      if e1 != e2: return 0
    if len(self.module_version_) != len(x.module_version_): return 0
    for e1, e2 in zip(self.module_version_, x.module_version_):
      if e1 != e2: return 0
    if self.has_start_time_ != x.has_start_time_: return 0
    if self.has_start_time_ and self.start_time_ != x.start_time_: return 0
    if self.has_start_time_set_ != x.has_start_time_set_: return 0
    if self.has_start_time_set_ and self.start_time_set_ != x.start_time_set_: return 0
    if self.has_end_time_ != x.has_end_time_: return 0
    if self.has_end_time_ and self.end_time_ != x.end_time_: return 0
    if self.has_end_time_set_ != x.has_end_time_set_: return 0
    if self.has_end_time_set_ and self.end_time_set_ != x.end_time_set_: return 0
    if self.has_offset_ != x.has_offset_: return 0
    if self.has_offset_ and self.offset_ != x.offset_: return 0
    if len(self.request_id_) != len(x.request_id_): return 0
    for e1, e2 in zip(self.request_id_, x.request_id_):
      if e1 != e2: return 0
    if self.has_minimum_log_level_ != x.has_minimum_log_level_: return 0
    if self.has_minimum_log_level_ and self.minimum_log_level_ != x.minimum_log_level_: return 0
    if self.has_minimum_log_level_set_ != x.has_minimum_log_level_set_: return 0
    if self.has_minimum_log_level_set_ and self.minimum_log_level_set_ != x.minimum_log_level_set_: return 0
    if self.has_include_incomplete_ != x.has_include_incomplete_: return 0
    if self.has_include_incomplete_ and self.include_incomplete_ != x.include_incomplete_: return 0
    if self.has_count_ != x.has_count_: return 0
    if self.has_count_ and self.count_ != x.count_: return 0
    if self.has_count_set_ != x.has_count_set_: return 0
    if self.has_count_set_ and self.count_set_ != x.count_set_: return 0
    if self.has_combined_log_regex_ != x.has_combined_log_regex_: return 0
    if self.has_combined_log_regex_ and self.combined_log_regex_ != x.combined_log_regex_: return 0
    if self.has_combined_log_regex_set_ != x.has_combined_log_regex_set_: return 0
    if self.has_combined_log_regex_set_ and self.combined_log_regex_set_ != x.combined_log_regex_set_: return 0
    if self.has_host_regex_ != x.has_host_regex_: return 0
    if self.has_host_regex_ and self.host_regex_ != x.host_regex_: return 0
    if self.has_host_regex_set_ != x.has_host_regex_set_: return 0
    if self.has_host_regex_set_ and self.host_regex_set_ != x.host_regex_set_: return 0
    if self.has_replica_index_ != x.has_replica_index_: return 0
    if self.has_replica_index_ and self.replica_index_ != x.replica_index_: return 0
    if self.has_replica_index_set_ != x.has_replica_index_set_: return 0
    if self.has_replica_index_set_ and self.replica_index_set_ != x.replica_index_set_: return 0
    if self.has_include_app_logs_ != x.has_include_app_logs_: return 0
    if self.has_include_app_logs_ and self.include_app_logs_ != x.include_app_logs_: return 0
    if self.has_app_logs_per_request_ != x.has_app_logs_per_request_: return 0
    if self.has_app_logs_per_request_ and self.app_logs_per_request_ != x.app_logs_per_request_: return 0
    if self.has_app_logs_per_request_set_ != x.has_app_logs_per_request_set_: return 0
    if self.has_app_logs_per_request_set_ and self.app_logs_per_request_set_ != x.app_logs_per_request_set_: return 0
    if self.has_include_host_ != x.has_include_host_: return 0
    if self.has_include_host_ and self.include_host_ != x.include_host_: return 0
    if self.has_include_all_ != x.has_include_all_: return 0
    if self.has_include_all_ and self.include_all_ != x.include_all_: return 0
    if self.has_cache_iterator_ != x.has_cache_iterator_: return 0
    if self.has_cache_iterator_ and self.cache_iterator_ != x.cache_iterator_: return 0
    if self.has_num_shards_ != x.has_num_shards_: return 0
    if self.has_num_shards_ and self.num_shards_ != x.num_shards_: return 0
    if self.has_num_shards_set_ != x.has_num_shards_set_: return 0
    if self.has_num_shards_set_ and self.num_shards_set_ != x.num_shards_set_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_app_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: app_id not set.')
    for p in self.module_version_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_offset_ and not self.offset_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.app_id_))
    n += 1 * len(self.version_id_)
    for i in xrange(len(self.version_id_)): n += self.lengthString(len(self.version_id_[i]))
    n += 2 * len(self.module_version_)
    for i in xrange(len(self.module_version_)): n += self.lengthString(self.module_version_[i].ByteSize())
    if (self.has_start_time_): n += 1 + self.lengthVarInt64(self.start_time_)
    if (self.has_start_time_set_): n += 3
    if (self.has_end_time_): n += 1 + self.lengthVarInt64(self.end_time_)
    if (self.has_end_time_set_): n += 3
    if (self.has_offset_): n += 1 + self.lengthString(self.offset_.ByteSize())
    n += 1 * len(self.request_id_)
    for i in xrange(len(self.request_id_)): n += self.lengthString(len(self.request_id_[i]))
    if (self.has_minimum_log_level_): n += 1 + self.lengthVarInt64(self.minimum_log_level_)
    if (self.has_minimum_log_level_set_): n += 3
    if (self.has_include_incomplete_): n += 2
    if (self.has_count_): n += 1 + self.lengthVarInt64(self.count_)
    if (self.has_count_set_): n += 3
    if (self.has_combined_log_regex_): n += 1 + self.lengthString(len(self.combined_log_regex_))
    if (self.has_combined_log_regex_set_): n += 3
    if (self.has_host_regex_): n += 1 + self.lengthString(len(self.host_regex_))
    if (self.has_host_regex_set_): n += 3
    if (self.has_replica_index_): n += 2 + self.lengthVarInt64(self.replica_index_)
    if (self.has_replica_index_set_): n += 3
    if (self.has_include_app_logs_): n += 2
    if (self.has_app_logs_per_request_): n += 2 + self.lengthVarInt64(self.app_logs_per_request_)
    if (self.has_app_logs_per_request_set_): n += 3
    if (self.has_include_host_): n += 2
    if (self.has_include_all_): n += 2
    if (self.has_cache_iterator_): n += 2
    if (self.has_num_shards_): n += 2 + self.lengthVarInt64(self.num_shards_)
    if (self.has_num_shards_set_): n += 3
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_):
      n += 1
      n += self.lengthString(len(self.app_id_))
    n += 1 * len(self.version_id_)
    for i in xrange(len(self.version_id_)): n += self.lengthString(len(self.version_id_[i]))
    n += 2 * len(self.module_version_)
    for i in xrange(len(self.module_version_)): n += self.lengthString(self.module_version_[i].ByteSizePartial())
    if (self.has_start_time_): n += 1 + self.lengthVarInt64(self.start_time_)
    if (self.has_start_time_set_): n += 3
    if (self.has_end_time_): n += 1 + self.lengthVarInt64(self.end_time_)
    if (self.has_end_time_set_): n += 3
    if (self.has_offset_): n += 1 + self.lengthString(self.offset_.ByteSizePartial())
    n += 1 * len(self.request_id_)
    for i in xrange(len(self.request_id_)): n += self.lengthString(len(self.request_id_[i]))
    if (self.has_minimum_log_level_): n += 1 + self.lengthVarInt64(self.minimum_log_level_)
    if (self.has_minimum_log_level_set_): n += 3
    if (self.has_include_incomplete_): n += 2
    if (self.has_count_): n += 1 + self.lengthVarInt64(self.count_)
    if (self.has_count_set_): n += 3
    if (self.has_combined_log_regex_): n += 1 + self.lengthString(len(self.combined_log_regex_))
    if (self.has_combined_log_regex_set_): n += 3
    if (self.has_host_regex_): n += 1 + self.lengthString(len(self.host_regex_))
    if (self.has_host_regex_set_): n += 3
    if (self.has_replica_index_): n += 2 + self.lengthVarInt64(self.replica_index_)
    if (self.has_replica_index_set_): n += 3
    if (self.has_include_app_logs_): n += 2
    if (self.has_app_logs_per_request_): n += 2 + self.lengthVarInt64(self.app_logs_per_request_)
    if (self.has_app_logs_per_request_set_): n += 3
    if (self.has_include_host_): n += 2
    if (self.has_include_all_): n += 2
    if (self.has_cache_iterator_): n += 2
    if (self.has_num_shards_): n += 2 + self.lengthVarInt64(self.num_shards_)
    if (self.has_num_shards_set_): n += 3
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_version_id()
    self.clear_module_version()
    self.clear_start_time()
    self.clear_start_time_set()
    self.clear_end_time()
    self.clear_end_time_set()
    self.clear_offset()
    self.clear_request_id()
    self.clear_minimum_log_level()
    self.clear_minimum_log_level_set()
    self.clear_include_incomplete()
    self.clear_count()
    self.clear_count_set()
    self.clear_combined_log_regex()
    self.clear_combined_log_regex_set()
    self.clear_host_regex()
    self.clear_host_regex_set()
    self.clear_replica_index()
    self.clear_replica_index_set()
    self.clear_include_app_logs()
    self.clear_app_logs_per_request()
    self.clear_app_logs_per_request_set()
    self.clear_include_host()
    self.clear_include_all()
    self.clear_cache_iterator()
    self.clear_num_shards()
    self.clear_num_shards_set()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.app_id_)
    for i in xrange(len(self.version_id_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_id_[i])
    if (self.has_start_time_):
      out.putVarInt32(24)
      out.putVarInt64(self.start_time_)
    if (self.has_end_time_):
      out.putVarInt32(32)
      out.putVarInt64(self.end_time_)
    if (self.has_offset_):
      out.putVarInt32(42)
      out.putVarInt32(self.offset_.ByteSize())
      self.offset_.OutputUnchecked(out)
    for i in xrange(len(self.request_id_)):
      out.putVarInt32(50)
      out.putPrefixedString(self.request_id_[i])
    if (self.has_minimum_log_level_):
      out.putVarInt32(56)
      out.putVarInt32(self.minimum_log_level_)
    if (self.has_include_incomplete_):
      out.putVarInt32(64)
      out.putBoolean(self.include_incomplete_)
    if (self.has_count_):
      out.putVarInt32(72)
      out.putVarInt64(self.count_)
    if (self.has_include_app_logs_):
      out.putVarInt32(80)
      out.putBoolean(self.include_app_logs_)
    if (self.has_include_host_):
      out.putVarInt32(88)
      out.putBoolean(self.include_host_)
    if (self.has_include_all_):
      out.putVarInt32(96)
      out.putBoolean(self.include_all_)
    if (self.has_cache_iterator_):
      out.putVarInt32(104)
      out.putBoolean(self.cache_iterator_)
    if (self.has_combined_log_regex_):
      out.putVarInt32(114)
      out.putPrefixedString(self.combined_log_regex_)
    if (self.has_host_regex_):
      out.putVarInt32(122)
      out.putPrefixedString(self.host_regex_)
    if (self.has_replica_index_):
      out.putVarInt32(128)
      out.putVarInt32(self.replica_index_)
    if (self.has_app_logs_per_request_):
      out.putVarInt32(136)
      out.putVarInt32(self.app_logs_per_request_)
    if (self.has_num_shards_):
      out.putVarInt32(144)
      out.putVarInt32(self.num_shards_)
    for i in xrange(len(self.module_version_)):
      out.putVarInt32(154)
      out.putVarInt32(self.module_version_[i].ByteSize())
      self.module_version_[i].OutputUnchecked(out)
    if (self.has_start_time_set_):
      out.putVarInt32(824)
      out.putBoolean(self.start_time_set_)
    if (self.has_end_time_set_):
      out.putVarInt32(832)
      out.putBoolean(self.end_time_set_)
    if (self.has_minimum_log_level_set_):
      out.putVarInt32(856)
      out.putBoolean(self.minimum_log_level_set_)
    if (self.has_count_set_):
      out.putVarInt32(872)
      out.putBoolean(self.count_set_)
    if (self.has_combined_log_regex_set_):
      out.putVarInt32(912)
      out.putBoolean(self.combined_log_regex_set_)
    if (self.has_host_regex_set_):
      out.putVarInt32(920)
      out.putBoolean(self.host_regex_set_)
    if (self.has_replica_index_set_):
      out.putVarInt32(928)
      out.putBoolean(self.replica_index_set_)
    if (self.has_app_logs_per_request_set_):
      out.putVarInt32(936)
      out.putBoolean(self.app_logs_per_request_set_)
    if (self.has_num_shards_set_):
      out.putVarInt32(944)
      out.putBoolean(self.num_shards_set_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    for i in xrange(len(self.version_id_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_id_[i])
    if (self.has_start_time_):
      out.putVarInt32(24)
      out.putVarInt64(self.start_time_)
    if (self.has_end_time_):
      out.putVarInt32(32)
      out.putVarInt64(self.end_time_)
    if (self.has_offset_):
      out.putVarInt32(42)
      out.putVarInt32(self.offset_.ByteSizePartial())
      self.offset_.OutputPartial(out)
    for i in xrange(len(self.request_id_)):
      out.putVarInt32(50)
      out.putPrefixedString(self.request_id_[i])
    if (self.has_minimum_log_level_):
      out.putVarInt32(56)
      out.putVarInt32(self.minimum_log_level_)
    if (self.has_include_incomplete_):
      out.putVarInt32(64)
      out.putBoolean(self.include_incomplete_)
    if (self.has_count_):
      out.putVarInt32(72)
      out.putVarInt64(self.count_)
    if (self.has_include_app_logs_):
      out.putVarInt32(80)
      out.putBoolean(self.include_app_logs_)
    if (self.has_include_host_):
      out.putVarInt32(88)
      out.putBoolean(self.include_host_)
    if (self.has_include_all_):
      out.putVarInt32(96)
      out.putBoolean(self.include_all_)
    if (self.has_cache_iterator_):
      out.putVarInt32(104)
      out.putBoolean(self.cache_iterator_)
    if (self.has_combined_log_regex_):
      out.putVarInt32(114)
      out.putPrefixedString(self.combined_log_regex_)
    if (self.has_host_regex_):
      out.putVarInt32(122)
      out.putPrefixedString(self.host_regex_)
    if (self.has_replica_index_):
      out.putVarInt32(128)
      out.putVarInt32(self.replica_index_)
    if (self.has_app_logs_per_request_):
      out.putVarInt32(136)
      out.putVarInt32(self.app_logs_per_request_)
    if (self.has_num_shards_):
      out.putVarInt32(144)
      out.putVarInt32(self.num_shards_)
    for i in xrange(len(self.module_version_)):
      out.putVarInt32(154)
      out.putVarInt32(self.module_version_[i].ByteSizePartial())
      self.module_version_[i].OutputPartial(out)
    if (self.has_start_time_set_):
      out.putVarInt32(824)
      out.putBoolean(self.start_time_set_)
    if (self.has_end_time_set_):
      out.putVarInt32(832)
      out.putBoolean(self.end_time_set_)
    if (self.has_minimum_log_level_set_):
      out.putVarInt32(856)
      out.putBoolean(self.minimum_log_level_set_)
    if (self.has_count_set_):
      out.putVarInt32(872)
      out.putBoolean(self.count_set_)
    if (self.has_combined_log_regex_set_):
      out.putVarInt32(912)
      out.putBoolean(self.combined_log_regex_set_)
    if (self.has_host_regex_set_):
      out.putVarInt32(920)
      out.putBoolean(self.host_regex_set_)
    if (self.has_replica_index_set_):
      out.putVarInt32(928)
      out.putBoolean(self.replica_index_set_)
    if (self.has_app_logs_per_request_set_):
      out.putVarInt32(936)
      out.putBoolean(self.app_logs_per_request_set_)
    if (self.has_num_shards_set_):
      out.putVarInt32(944)
      out.putBoolean(self.num_shards_set_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.add_version_id(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_start_time(d.getVarInt64())
        continue
      if tt == 32:
        self.set_end_time(d.getVarInt64())
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_offset().TryMerge(tmp)
        continue
      if tt == 50:
        self.add_request_id(d.getPrefixedString())
        continue
      if tt == 56:
        self.set_minimum_log_level(d.getVarInt32())
        continue
      if tt == 64:
        self.set_include_incomplete(d.getBoolean())
        continue
      if tt == 72:
        self.set_count(d.getVarInt64())
        continue
      if tt == 80:
        self.set_include_app_logs(d.getBoolean())
        continue
      if tt == 88:
        self.set_include_host(d.getBoolean())
        continue
      if tt == 96:
        self.set_include_all(d.getBoolean())
        continue
      if tt == 104:
        self.set_cache_iterator(d.getBoolean())
        continue
      if tt == 114:
        self.set_combined_log_regex(d.getPrefixedString())
        continue
      if tt == 122:
        self.set_host_regex(d.getPrefixedString())
        continue
      if tt == 128:
        self.set_replica_index(d.getVarInt32())
        continue
      if tt == 136:
        self.set_app_logs_per_request(d.getVarInt32())
        continue
      if tt == 144:
        self.set_num_shards(d.getVarInt32())
        continue
      if tt == 154:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_module_version().TryMerge(tmp)
        continue
      if tt == 824:
        self.set_start_time_set(d.getBoolean())
        continue
      if tt == 832:
        self.set_end_time_set(d.getBoolean())
        continue
      if tt == 856:
        self.set_minimum_log_level_set(d.getBoolean())
        continue
      if tt == 872:
        self.set_count_set(d.getBoolean())
        continue
      if tt == 912:
        self.set_combined_log_regex_set(d.getBoolean())
        continue
      if tt == 920:
        self.set_host_regex_set(d.getBoolean())
        continue
      if tt == 928:
        self.set_replica_index_set(d.getBoolean())
        continue
      if tt == 936:
        self.set_app_logs_per_request_set(d.getBoolean())
        continue
      if tt == 944:
        self.set_num_shards_set(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    cnt=0
    for e in self.version_id_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("version_id%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    cnt=0
    for e in self.module_version_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("module_version%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_start_time_: res+=prefix+("start_time: %s\n" % self.DebugFormatInt64(self.start_time_))
    if self.has_start_time_set_: res+=prefix+("start_time_set: %s\n" % self.DebugFormatBool(self.start_time_set_))
    if self.has_end_time_: res+=prefix+("end_time: %s\n" % self.DebugFormatInt64(self.end_time_))
    if self.has_end_time_set_: res+=prefix+("end_time_set: %s\n" % self.DebugFormatBool(self.end_time_set_))
    if self.has_offset_:
      res+=prefix+"offset <\n"
      res+=self.offset_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.request_id_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("request_id%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_minimum_log_level_: res+=prefix+("minimum_log_level: %s\n" % self.DebugFormatInt32(self.minimum_log_level_))
    if self.has_minimum_log_level_set_: res+=prefix+("minimum_log_level_set: %s\n" % self.DebugFormatBool(self.minimum_log_level_set_))
    if self.has_include_incomplete_: res+=prefix+("include_incomplete: %s\n" % self.DebugFormatBool(self.include_incomplete_))
    if self.has_count_: res+=prefix+("count: %s\n" % self.DebugFormatInt64(self.count_))
    if self.has_count_set_: res+=prefix+("count_set: %s\n" % self.DebugFormatBool(self.count_set_))
    if self.has_combined_log_regex_: res+=prefix+("combined_log_regex: %s\n" % self.DebugFormatString(self.combined_log_regex_))
    if self.has_combined_log_regex_set_: res+=prefix+("combined_log_regex_set: %s\n" % self.DebugFormatBool(self.combined_log_regex_set_))
    if self.has_host_regex_: res+=prefix+("host_regex: %s\n" % self.DebugFormatString(self.host_regex_))
    if self.has_host_regex_set_: res+=prefix+("host_regex_set: %s\n" % self.DebugFormatBool(self.host_regex_set_))
    if self.has_replica_index_: res+=prefix+("replica_index: %s\n" % self.DebugFormatInt32(self.replica_index_))
    if self.has_replica_index_set_: res+=prefix+("replica_index_set: %s\n" % self.DebugFormatBool(self.replica_index_set_))
    if self.has_include_app_logs_: res+=prefix+("include_app_logs: %s\n" % self.DebugFormatBool(self.include_app_logs_))
    if self.has_app_logs_per_request_: res+=prefix+("app_logs_per_request: %s\n" % self.DebugFormatInt32(self.app_logs_per_request_))
    if self.has_app_logs_per_request_set_: res+=prefix+("app_logs_per_request_set: %s\n" % self.DebugFormatBool(self.app_logs_per_request_set_))
    if self.has_include_host_: res+=prefix+("include_host: %s\n" % self.DebugFormatBool(self.include_host_))
    if self.has_include_all_: res+=prefix+("include_all: %s\n" % self.DebugFormatBool(self.include_all_))
    if self.has_cache_iterator_: res+=prefix+("cache_iterator: %s\n" % self.DebugFormatBool(self.cache_iterator_))
    if self.has_num_shards_: res+=prefix+("num_shards: %s\n" % self.DebugFormatInt32(self.num_shards_))
    if self.has_num_shards_set_: res+=prefix+("num_shards_set: %s\n" % self.DebugFormatBool(self.num_shards_set_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  kversion_id = 2
  kmodule_version = 19
  kstart_time = 3
  kstart_time_set = 103
  kend_time = 4
  kend_time_set = 104
  koffset = 5
  krequest_id = 6
  kminimum_log_level = 7
  kminimum_log_level_set = 107
  kinclude_incomplete = 8
  kcount = 9
  kcount_set = 109
  kcombined_log_regex = 14
  kcombined_log_regex_set = 114
  khost_regex = 15
  khost_regex_set = 115
  kreplica_index = 16
  kreplica_index_set = 116
  kinclude_app_logs = 10
  kapp_logs_per_request = 17
  kapp_logs_per_request_set = 117
  kinclude_host = 11
  kinclude_all = 12
  kcache_iterator = 13
  knum_shards = 18
  knum_shards_set = 118

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "version_id",
    3: "start_time",
    4: "end_time",
    5: "offset",
    6: "request_id",
    7: "minimum_log_level",
    8: "include_incomplete",
    9: "count",
    10: "include_app_logs",
    11: "include_host",
    12: "include_all",
    13: "cache_iterator",
    14: "combined_log_regex",
    15: "host_regex",
    16: "replica_index",
    17: "app_logs_per_request",
    18: "num_shards",
    19: "module_version",
    103: "start_time_set",
    104: "end_time_set",
    107: "minimum_log_level_set",
    109: "count_set",
    114: "combined_log_regex_set",
    115: "host_regex_set",
    116: "replica_index_set",
    117: "app_logs_per_request_set",
    118: "num_shards_set",
  }, 118)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.STRING,
    7: ProtocolBuffer.Encoder.NUMERIC,
    8: ProtocolBuffer.Encoder.NUMERIC,
    9: ProtocolBuffer.Encoder.NUMERIC,
    10: ProtocolBuffer.Encoder.NUMERIC,
    11: ProtocolBuffer.Encoder.NUMERIC,
    12: ProtocolBuffer.Encoder.NUMERIC,
    13: ProtocolBuffer.Encoder.NUMERIC,
    14: ProtocolBuffer.Encoder.STRING,
    15: ProtocolBuffer.Encoder.STRING,
    16: ProtocolBuffer.Encoder.NUMERIC,
    17: ProtocolBuffer.Encoder.NUMERIC,
    18: ProtocolBuffer.Encoder.NUMERIC,
    19: ProtocolBuffer.Encoder.STRING,
    103: ProtocolBuffer.Encoder.NUMERIC,
    104: ProtocolBuffer.Encoder.NUMERIC,
    107: ProtocolBuffer.Encoder.NUMERIC,
    109: ProtocolBuffer.Encoder.NUMERIC,
    114: ProtocolBuffer.Encoder.NUMERIC,
    115: ProtocolBuffer.Encoder.NUMERIC,
    116: ProtocolBuffer.Encoder.NUMERIC,
    117: ProtocolBuffer.Encoder.NUMERIC,
    118: ProtocolBuffer.Encoder.NUMERIC,
  }, 118, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.LogReadRequest'
class LogReadResponse(ProtocolBuffer.ProtocolMessage):
  has_offset_ = 0
  offset_ = None
  has_last_end_time_ = 0
  last_end_time_ = 0

  def __init__(self, contents=None):
    self.log_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def log_size(self): return len(self.log_)
  def log_list(self): return self.log_

  def log(self, i):
    return self.log_[i]

  def mutable_log(self, i):
    return self.log_[i]

  def add_log(self):
    x = RequestLog()
    self.log_.append(x)
    return x

  def clear_log(self):
    self.log_ = []
  def offset(self):
    if self.offset_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.offset_ is None: self.offset_ = LogOffset()
      finally:
        self.lazy_init_lock_.release()
    return self.offset_

  def mutable_offset(self): self.has_offset_ = 1; return self.offset()

  def clear_offset(self):

    if self.has_offset_:
      self.has_offset_ = 0;
      if self.offset_ is not None: self.offset_.Clear()

  def has_offset(self): return self.has_offset_

  def last_end_time(self): return self.last_end_time_

  def set_last_end_time(self, x):
    self.has_last_end_time_ = 1
    self.last_end_time_ = x

  def clear_last_end_time(self):
    if self.has_last_end_time_:
      self.has_last_end_time_ = 0
      self.last_end_time_ = 0

  def has_last_end_time(self): return self.has_last_end_time_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.log_size()): self.add_log().CopyFrom(x.log(i))
    if (x.has_offset()): self.mutable_offset().MergeFrom(x.offset())
    if (x.has_last_end_time()): self.set_last_end_time(x.last_end_time())

  def Equals(self, x):
    if x is self: return 1
    if len(self.log_) != len(x.log_): return 0
    for e1, e2 in zip(self.log_, x.log_):
      if e1 != e2: return 0
    if self.has_offset_ != x.has_offset_: return 0
    if self.has_offset_ and self.offset_ != x.offset_: return 0
    if self.has_last_end_time_ != x.has_last_end_time_: return 0
    if self.has_last_end_time_ and self.last_end_time_ != x.last_end_time_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.log_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_offset_ and not self.offset_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.log_)
    for i in xrange(len(self.log_)): n += self.lengthString(self.log_[i].ByteSize())
    if (self.has_offset_): n += 1 + self.lengthString(self.offset_.ByteSize())
    if (self.has_last_end_time_): n += 1 + self.lengthVarInt64(self.last_end_time_)
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.log_)
    for i in xrange(len(self.log_)): n += self.lengthString(self.log_[i].ByteSizePartial())
    if (self.has_offset_): n += 1 + self.lengthString(self.offset_.ByteSizePartial())
    if (self.has_last_end_time_): n += 1 + self.lengthVarInt64(self.last_end_time_)
    return n

  def Clear(self):
    self.clear_log()
    self.clear_offset()
    self.clear_last_end_time()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.log_)):
      out.putVarInt32(10)
      out.putVarInt32(self.log_[i].ByteSize())
      self.log_[i].OutputUnchecked(out)
    if (self.has_offset_):
      out.putVarInt32(18)
      out.putVarInt32(self.offset_.ByteSize())
      self.offset_.OutputUnchecked(out)
    if (self.has_last_end_time_):
      out.putVarInt32(24)
      out.putVarInt64(self.last_end_time_)

  def OutputPartial(self, out):
    for i in xrange(len(self.log_)):
      out.putVarInt32(10)
      out.putVarInt32(self.log_[i].ByteSizePartial())
      self.log_[i].OutputPartial(out)
    if (self.has_offset_):
      out.putVarInt32(18)
      out.putVarInt32(self.offset_.ByteSizePartial())
      self.offset_.OutputPartial(out)
    if (self.has_last_end_time_):
      out.putVarInt32(24)
      out.putVarInt64(self.last_end_time_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_log().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_offset().TryMerge(tmp)
        continue
      if tt == 24:
        self.set_last_end_time(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.log_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("log%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_offset_:
      res+=prefix+"offset <\n"
      res+=self.offset_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_last_end_time_: res+=prefix+("last_end_time: %s\n" % self.DebugFormatInt64(self.last_end_time_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  klog = 1
  koffset = 2
  klast_end_time = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "log",
    2: "offset",
    3: "last_end_time",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.LogReadResponse'
class LogUsageRecord(ProtocolBuffer.ProtocolMessage):
  has_version_id_ = 0
  version_id_ = ""
  has_start_time_ = 0
  start_time_ = 0
  has_end_time_ = 0
  end_time_ = 0
  has_count_ = 0
  count_ = 0
  has_total_size_ = 0
  total_size_ = 0
  has_records_ = 0
  records_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def version_id(self): return self.version_id_

  def set_version_id(self, x):
    self.has_version_id_ = 1
    self.version_id_ = x

  def clear_version_id(self):
    if self.has_version_id_:
      self.has_version_id_ = 0
      self.version_id_ = ""

  def has_version_id(self): return self.has_version_id_

  def start_time(self): return self.start_time_

  def set_start_time(self, x):
    self.has_start_time_ = 1
    self.start_time_ = x

  def clear_start_time(self):
    if self.has_start_time_:
      self.has_start_time_ = 0
      self.start_time_ = 0

  def has_start_time(self): return self.has_start_time_

  def end_time(self): return self.end_time_

  def set_end_time(self, x):
    self.has_end_time_ = 1
    self.end_time_ = x

  def clear_end_time(self):
    if self.has_end_time_:
      self.has_end_time_ = 0
      self.end_time_ = 0

  def has_end_time(self): return self.has_end_time_

  def count(self): return self.count_

  def set_count(self, x):
    self.has_count_ = 1
    self.count_ = x

  def clear_count(self):
    if self.has_count_:
      self.has_count_ = 0
      self.count_ = 0

  def has_count(self): return self.has_count_

  def total_size(self): return self.total_size_

  def set_total_size(self, x):
    self.has_total_size_ = 1
    self.total_size_ = x

  def clear_total_size(self):
    if self.has_total_size_:
      self.has_total_size_ = 0
      self.total_size_ = 0

  def has_total_size(self): return self.has_total_size_

  def records(self): return self.records_

  def set_records(self, x):
    self.has_records_ = 1
    self.records_ = x

  def clear_records(self):
    if self.has_records_:
      self.has_records_ = 0
      self.records_ = 0

  def has_records(self): return self.has_records_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_version_id()): self.set_version_id(x.version_id())
    if (x.has_start_time()): self.set_start_time(x.start_time())
    if (x.has_end_time()): self.set_end_time(x.end_time())
    if (x.has_count()): self.set_count(x.count())
    if (x.has_total_size()): self.set_total_size(x.total_size())
    if (x.has_records()): self.set_records(x.records())

  def Equals(self, x):
    if x is self: return 1
    if self.has_version_id_ != x.has_version_id_: return 0
    if self.has_version_id_ and self.version_id_ != x.version_id_: return 0
    if self.has_start_time_ != x.has_start_time_: return 0
    if self.has_start_time_ and self.start_time_ != x.start_time_: return 0
    if self.has_end_time_ != x.has_end_time_: return 0
    if self.has_end_time_ and self.end_time_ != x.end_time_: return 0
    if self.has_count_ != x.has_count_: return 0
    if self.has_count_ and self.count_ != x.count_: return 0
    if self.has_total_size_ != x.has_total_size_: return 0
    if self.has_total_size_ and self.total_size_ != x.total_size_: return 0
    if self.has_records_ != x.has_records_: return 0
    if self.has_records_ and self.records_ != x.records_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_version_id_): n += 1 + self.lengthString(len(self.version_id_))
    if (self.has_start_time_): n += 1 + self.lengthVarInt64(self.start_time_)
    if (self.has_end_time_): n += 1 + self.lengthVarInt64(self.end_time_)
    if (self.has_count_): n += 1 + self.lengthVarInt64(self.count_)
    if (self.has_total_size_): n += 1 + self.lengthVarInt64(self.total_size_)
    if (self.has_records_): n += 1 + self.lengthVarInt64(self.records_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_version_id_): n += 1 + self.lengthString(len(self.version_id_))
    if (self.has_start_time_): n += 1 + self.lengthVarInt64(self.start_time_)
    if (self.has_end_time_): n += 1 + self.lengthVarInt64(self.end_time_)
    if (self.has_count_): n += 1 + self.lengthVarInt64(self.count_)
    if (self.has_total_size_): n += 1 + self.lengthVarInt64(self.total_size_)
    if (self.has_records_): n += 1 + self.lengthVarInt64(self.records_)
    return n

  def Clear(self):
    self.clear_version_id()
    self.clear_start_time()
    self.clear_end_time()
    self.clear_count()
    self.clear_total_size()
    self.clear_records()

  def OutputUnchecked(self, out):
    if (self.has_version_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.version_id_)
    if (self.has_start_time_):
      out.putVarInt32(16)
      out.putVarInt32(self.start_time_)
    if (self.has_end_time_):
      out.putVarInt32(24)
      out.putVarInt32(self.end_time_)
    if (self.has_count_):
      out.putVarInt32(32)
      out.putVarInt64(self.count_)
    if (self.has_total_size_):
      out.putVarInt32(40)
      out.putVarInt64(self.total_size_)
    if (self.has_records_):
      out.putVarInt32(48)
      out.putVarInt32(self.records_)

  def OutputPartial(self, out):
    if (self.has_version_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.version_id_)
    if (self.has_start_time_):
      out.putVarInt32(16)
      out.putVarInt32(self.start_time_)
    if (self.has_end_time_):
      out.putVarInt32(24)
      out.putVarInt32(self.end_time_)
    if (self.has_count_):
      out.putVarInt32(32)
      out.putVarInt64(self.count_)
    if (self.has_total_size_):
      out.putVarInt32(40)
      out.putVarInt64(self.total_size_)
    if (self.has_records_):
      out.putVarInt32(48)
      out.putVarInt32(self.records_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_version_id(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_start_time(d.getVarInt32())
        continue
      if tt == 24:
        self.set_end_time(d.getVarInt32())
        continue
      if tt == 32:
        self.set_count(d.getVarInt64())
        continue
      if tt == 40:
        self.set_total_size(d.getVarInt64())
        continue
      if tt == 48:
        self.set_records(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_version_id_: res+=prefix+("version_id: %s\n" % self.DebugFormatString(self.version_id_))
    if self.has_start_time_: res+=prefix+("start_time: %s\n" % self.DebugFormatInt32(self.start_time_))
    if self.has_end_time_: res+=prefix+("end_time: %s\n" % self.DebugFormatInt32(self.end_time_))
    if self.has_count_: res+=prefix+("count: %s\n" % self.DebugFormatInt64(self.count_))
    if self.has_total_size_: res+=prefix+("total_size: %s\n" % self.DebugFormatInt64(self.total_size_))
    if self.has_records_: res+=prefix+("records: %s\n" % self.DebugFormatInt32(self.records_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kversion_id = 1
  kstart_time = 2
  kend_time = 3
  kcount = 4
  ktotal_size = 5
  krecords = 6

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "version_id",
    2: "start_time",
    3: "end_time",
    4: "count",
    5: "total_size",
    6: "records",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.NUMERIC,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.LogUsageRecord'
class LogUsageRequest(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_start_time_ = 0
  start_time_ = 0
  has_end_time_ = 0
  end_time_ = 0
  has_resolution_hours_ = 0
  resolution_hours_ = 1
  has_resolution_hours_set_ = 0
  resolution_hours_set_ = 0
  has_combine_versions_ = 0
  combine_versions_ = 0
  has_usage_version_ = 0
  usage_version_ = 0
  has_usage_version_set_ = 0
  usage_version_set_ = 0
  has_versions_only_ = 0
  versions_only_ = 0

  def __init__(self, contents=None):
    self.version_id_ = []
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

  def version_id_size(self): return len(self.version_id_)
  def version_id_list(self): return self.version_id_

  def version_id(self, i):
    return self.version_id_[i]

  def set_version_id(self, i, x):
    self.version_id_[i] = x

  def add_version_id(self, x):
    self.version_id_.append(x)

  def clear_version_id(self):
    self.version_id_ = []

  def start_time(self): return self.start_time_

  def set_start_time(self, x):
    self.has_start_time_ = 1
    self.start_time_ = x

  def clear_start_time(self):
    if self.has_start_time_:
      self.has_start_time_ = 0
      self.start_time_ = 0

  def has_start_time(self): return self.has_start_time_

  def end_time(self): return self.end_time_

  def set_end_time(self, x):
    self.has_end_time_ = 1
    self.end_time_ = x

  def clear_end_time(self):
    if self.has_end_time_:
      self.has_end_time_ = 0
      self.end_time_ = 0

  def has_end_time(self): return self.has_end_time_

  def resolution_hours(self): return self.resolution_hours_

  def set_resolution_hours(self, x):
    self.has_resolution_hours_ = 1
    self.resolution_hours_ = x

  def clear_resolution_hours(self):
    if self.has_resolution_hours_:
      self.has_resolution_hours_ = 0
      self.resolution_hours_ = 1

  def has_resolution_hours(self): return self.has_resolution_hours_

  def resolution_hours_set(self): return self.resolution_hours_set_

  def set_resolution_hours_set(self, x):
    self.has_resolution_hours_set_ = 1
    self.resolution_hours_set_ = x

  def clear_resolution_hours_set(self):
    if self.has_resolution_hours_set_:
      self.has_resolution_hours_set_ = 0
      self.resolution_hours_set_ = 0

  def has_resolution_hours_set(self): return self.has_resolution_hours_set_

  def combine_versions(self): return self.combine_versions_

  def set_combine_versions(self, x):
    self.has_combine_versions_ = 1
    self.combine_versions_ = x

  def clear_combine_versions(self):
    if self.has_combine_versions_:
      self.has_combine_versions_ = 0
      self.combine_versions_ = 0

  def has_combine_versions(self): return self.has_combine_versions_

  def usage_version(self): return self.usage_version_

  def set_usage_version(self, x):
    self.has_usage_version_ = 1
    self.usage_version_ = x

  def clear_usage_version(self):
    if self.has_usage_version_:
      self.has_usage_version_ = 0
      self.usage_version_ = 0

  def has_usage_version(self): return self.has_usage_version_

  def usage_version_set(self): return self.usage_version_set_

  def set_usage_version_set(self, x):
    self.has_usage_version_set_ = 1
    self.usage_version_set_ = x

  def clear_usage_version_set(self):
    if self.has_usage_version_set_:
      self.has_usage_version_set_ = 0
      self.usage_version_set_ = 0

  def has_usage_version_set(self): return self.has_usage_version_set_

  def versions_only(self): return self.versions_only_

  def set_versions_only(self, x):
    self.has_versions_only_ = 1
    self.versions_only_ = x

  def clear_versions_only(self):
    if self.has_versions_only_:
      self.has_versions_only_ = 0
      self.versions_only_ = 0

  def has_versions_only(self): return self.has_versions_only_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    for i in xrange(x.version_id_size()): self.add_version_id(x.version_id(i))
    if (x.has_start_time()): self.set_start_time(x.start_time())
    if (x.has_end_time()): self.set_end_time(x.end_time())
    if (x.has_resolution_hours()): self.set_resolution_hours(x.resolution_hours())
    if (x.has_resolution_hours_set()): self.set_resolution_hours_set(x.resolution_hours_set())
    if (x.has_combine_versions()): self.set_combine_versions(x.combine_versions())
    if (x.has_usage_version()): self.set_usage_version(x.usage_version())
    if (x.has_usage_version_set()): self.set_usage_version_set(x.usage_version_set())
    if (x.has_versions_only()): self.set_versions_only(x.versions_only())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if len(self.version_id_) != len(x.version_id_): return 0
    for e1, e2 in zip(self.version_id_, x.version_id_):
      if e1 != e2: return 0
    if self.has_start_time_ != x.has_start_time_: return 0
    if self.has_start_time_ and self.start_time_ != x.start_time_: return 0
    if self.has_end_time_ != x.has_end_time_: return 0
    if self.has_end_time_ and self.end_time_ != x.end_time_: return 0
    if self.has_resolution_hours_ != x.has_resolution_hours_: return 0
    if self.has_resolution_hours_ and self.resolution_hours_ != x.resolution_hours_: return 0
    if self.has_resolution_hours_set_ != x.has_resolution_hours_set_: return 0
    if self.has_resolution_hours_set_ and self.resolution_hours_set_ != x.resolution_hours_set_: return 0
    if self.has_combine_versions_ != x.has_combine_versions_: return 0
    if self.has_combine_versions_ and self.combine_versions_ != x.combine_versions_: return 0
    if self.has_usage_version_ != x.has_usage_version_: return 0
    if self.has_usage_version_ and self.usage_version_ != x.usage_version_: return 0
    if self.has_usage_version_set_ != x.has_usage_version_set_: return 0
    if self.has_usage_version_set_ and self.usage_version_set_ != x.usage_version_set_: return 0
    if self.has_versions_only_ != x.has_versions_only_: return 0
    if self.has_versions_only_ and self.versions_only_ != x.versions_only_: return 0
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
    n += 1 * len(self.version_id_)
    for i in xrange(len(self.version_id_)): n += self.lengthString(len(self.version_id_[i]))
    if (self.has_start_time_): n += 1 + self.lengthVarInt64(self.start_time_)
    if (self.has_end_time_): n += 1 + self.lengthVarInt64(self.end_time_)
    if (self.has_resolution_hours_): n += 1 + self.lengthVarInt64(self.resolution_hours_)
    if (self.has_resolution_hours_set_): n += 3
    if (self.has_combine_versions_): n += 2
    if (self.has_usage_version_): n += 1 + self.lengthVarInt64(self.usage_version_)
    if (self.has_usage_version_set_): n += 3
    if (self.has_versions_only_): n += 2
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_):
      n += 1
      n += self.lengthString(len(self.app_id_))
    n += 1 * len(self.version_id_)
    for i in xrange(len(self.version_id_)): n += self.lengthString(len(self.version_id_[i]))
    if (self.has_start_time_): n += 1 + self.lengthVarInt64(self.start_time_)
    if (self.has_end_time_): n += 1 + self.lengthVarInt64(self.end_time_)
    if (self.has_resolution_hours_): n += 1 + self.lengthVarInt64(self.resolution_hours_)
    if (self.has_resolution_hours_set_): n += 3
    if (self.has_combine_versions_): n += 2
    if (self.has_usage_version_): n += 1 + self.lengthVarInt64(self.usage_version_)
    if (self.has_usage_version_set_): n += 3
    if (self.has_versions_only_): n += 2
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_version_id()
    self.clear_start_time()
    self.clear_end_time()
    self.clear_resolution_hours()
    self.clear_resolution_hours_set()
    self.clear_combine_versions()
    self.clear_usage_version()
    self.clear_usage_version_set()
    self.clear_versions_only()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.app_id_)
    for i in xrange(len(self.version_id_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_id_[i])
    if (self.has_start_time_):
      out.putVarInt32(24)
      out.putVarInt32(self.start_time_)
    if (self.has_end_time_):
      out.putVarInt32(32)
      out.putVarInt32(self.end_time_)
    if (self.has_resolution_hours_):
      out.putVarInt32(40)
      out.putVarUint64(self.resolution_hours_)
    if (self.has_combine_versions_):
      out.putVarInt32(48)
      out.putBoolean(self.combine_versions_)
    if (self.has_usage_version_):
      out.putVarInt32(56)
      out.putVarInt32(self.usage_version_)
    if (self.has_versions_only_):
      out.putVarInt32(64)
      out.putBoolean(self.versions_only_)
    if (self.has_resolution_hours_set_):
      out.putVarInt32(840)
      out.putBoolean(self.resolution_hours_set_)
    if (self.has_usage_version_set_):
      out.putVarInt32(856)
      out.putBoolean(self.usage_version_set_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    for i in xrange(len(self.version_id_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.version_id_[i])
    if (self.has_start_time_):
      out.putVarInt32(24)
      out.putVarInt32(self.start_time_)
    if (self.has_end_time_):
      out.putVarInt32(32)
      out.putVarInt32(self.end_time_)
    if (self.has_resolution_hours_):
      out.putVarInt32(40)
      out.putVarUint64(self.resolution_hours_)
    if (self.has_combine_versions_):
      out.putVarInt32(48)
      out.putBoolean(self.combine_versions_)
    if (self.has_usage_version_):
      out.putVarInt32(56)
      out.putVarInt32(self.usage_version_)
    if (self.has_versions_only_):
      out.putVarInt32(64)
      out.putBoolean(self.versions_only_)
    if (self.has_resolution_hours_set_):
      out.putVarInt32(840)
      out.putBoolean(self.resolution_hours_set_)
    if (self.has_usage_version_set_):
      out.putVarInt32(856)
      out.putBoolean(self.usage_version_set_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.add_version_id(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_start_time(d.getVarInt32())
        continue
      if tt == 32:
        self.set_end_time(d.getVarInt32())
        continue
      if tt == 40:
        self.set_resolution_hours(d.getVarUint64())
        continue
      if tt == 48:
        self.set_combine_versions(d.getBoolean())
        continue
      if tt == 56:
        self.set_usage_version(d.getVarInt32())
        continue
      if tt == 64:
        self.set_versions_only(d.getBoolean())
        continue
      if tt == 840:
        self.set_resolution_hours_set(d.getBoolean())
        continue
      if tt == 856:
        self.set_usage_version_set(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    cnt=0
    for e in self.version_id_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("version_id%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_start_time_: res+=prefix+("start_time: %s\n" % self.DebugFormatInt32(self.start_time_))
    if self.has_end_time_: res+=prefix+("end_time: %s\n" % self.DebugFormatInt32(self.end_time_))
    if self.has_resolution_hours_: res+=prefix+("resolution_hours: %s\n" % self.DebugFormatInt64(self.resolution_hours_))
    if self.has_resolution_hours_set_: res+=prefix+("resolution_hours_set: %s\n" % self.DebugFormatBool(self.resolution_hours_set_))
    if self.has_combine_versions_: res+=prefix+("combine_versions: %s\n" % self.DebugFormatBool(self.combine_versions_))
    if self.has_usage_version_: res+=prefix+("usage_version: %s\n" % self.DebugFormatInt32(self.usage_version_))
    if self.has_usage_version_set_: res+=prefix+("usage_version_set: %s\n" % self.DebugFormatBool(self.usage_version_set_))
    if self.has_versions_only_: res+=prefix+("versions_only: %s\n" % self.DebugFormatBool(self.versions_only_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  kversion_id = 2
  kstart_time = 3
  kend_time = 4
  kresolution_hours = 5
  kresolution_hours_set = 105
  kcombine_versions = 6
  kusage_version = 7
  kusage_version_set = 107
  kversions_only = 8

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "version_id",
    3: "start_time",
    4: "end_time",
    5: "resolution_hours",
    6: "combine_versions",
    7: "usage_version",
    8: "versions_only",
    105: "resolution_hours_set",
    107: "usage_version_set",
  }, 107)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.NUMERIC,
    7: ProtocolBuffer.Encoder.NUMERIC,
    8: ProtocolBuffer.Encoder.NUMERIC,
    105: ProtocolBuffer.Encoder.NUMERIC,
    107: ProtocolBuffer.Encoder.NUMERIC,
  }, 107, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.LogUsageRequest'
class LogUsageResponse(ProtocolBuffer.ProtocolMessage):
  has_summary_ = 0
  summary_ = None

  def __init__(self, contents=None):
    self.usage_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def usage_size(self): return len(self.usage_)
  def usage_list(self): return self.usage_

  def usage(self, i):
    return self.usage_[i]

  def mutable_usage(self, i):
    return self.usage_[i]

  def add_usage(self):
    x = LogUsageRecord()
    self.usage_.append(x)
    return x

  def clear_usage(self):
    self.usage_ = []
  def summary(self):
    if self.summary_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.summary_ is None: self.summary_ = LogUsageRecord()
      finally:
        self.lazy_init_lock_.release()
    return self.summary_

  def mutable_summary(self): self.has_summary_ = 1; return self.summary()

  def clear_summary(self):

    if self.has_summary_:
      self.has_summary_ = 0;
      if self.summary_ is not None: self.summary_.Clear()

  def has_summary(self): return self.has_summary_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.usage_size()): self.add_usage().CopyFrom(x.usage(i))
    if (x.has_summary()): self.mutable_summary().MergeFrom(x.summary())

  def Equals(self, x):
    if x is self: return 1
    if len(self.usage_) != len(x.usage_): return 0
    for e1, e2 in zip(self.usage_, x.usage_):
      if e1 != e2: return 0
    if self.has_summary_ != x.has_summary_: return 0
    if self.has_summary_ and self.summary_ != x.summary_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.usage_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_summary_ and not self.summary_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.usage_)
    for i in xrange(len(self.usage_)): n += self.lengthString(self.usage_[i].ByteSize())
    if (self.has_summary_): n += 1 + self.lengthString(self.summary_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.usage_)
    for i in xrange(len(self.usage_)): n += self.lengthString(self.usage_[i].ByteSizePartial())
    if (self.has_summary_): n += 1 + self.lengthString(self.summary_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_usage()
    self.clear_summary()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.usage_)):
      out.putVarInt32(10)
      out.putVarInt32(self.usage_[i].ByteSize())
      self.usage_[i].OutputUnchecked(out)
    if (self.has_summary_):
      out.putVarInt32(18)
      out.putVarInt32(self.summary_.ByteSize())
      self.summary_.OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.usage_)):
      out.putVarInt32(10)
      out.putVarInt32(self.usage_[i].ByteSizePartial())
      self.usage_[i].OutputPartial(out)
    if (self.has_summary_):
      out.putVarInt32(18)
      out.putVarInt32(self.summary_.ByteSizePartial())
      self.summary_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_usage().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_summary().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.usage_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("usage%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_summary_:
      res+=prefix+"summary <\n"
      res+=self.summary_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kusage = 1
  ksummary = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "usage",
    2: "summary",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.LogUsageResponse'
if _extension_runtime:
  pass

__all__ = ['LogServiceError','UserAppLogLine','UserAppLogGroup','FlushRequest','SetStatusRequest','LogOffset','LogLine','RequestLog','LogModuleVersion','LogReadRequest','LogReadResponse','LogUsageRecord','LogUsageRequest','LogUsageResponse']
