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

from google.appengine.datastore.datastore_v3_pb import *
import google.appengine.datastore.datastore_v3_pb
from google.net.proto.message_set import MessageSet
class TaskQueueServiceError(ProtocolBuffer.ProtocolMessage):


  OK           =    0
  UNKNOWN_QUEUE =    1
  TRANSIENT_ERROR =    2
  INTERNAL_ERROR =    3
  TASK_TOO_LARGE =    4
  INVALID_TASK_NAME =    5
  INVALID_QUEUE_NAME =    6
  INVALID_URL  =    7
  INVALID_QUEUE_RATE =    8
  PERMISSION_DENIED =    9
  TASK_ALREADY_EXISTS =   10
  TOMBSTONED_TASK =   11
  INVALID_ETA  =   12
  INVALID_REQUEST =   13
  UNKNOWN_TASK =   14
  TOMBSTONED_QUEUE =   15
  DUPLICATE_TASK_NAME =   16
  SKIPPED      =   17
  TOO_MANY_TASKS =   18
  INVALID_PAYLOAD =   19
  INVALID_RETRY_PARAMETERS =   20
  INVALID_QUEUE_MODE =   21
  ACL_LOOKUP_ERROR =   22
  TRANSACTIONAL_REQUEST_TOO_LARGE =   23
  INCORRECT_CREATOR_NAME =   24
  TASK_LEASE_EXPIRED =   25
  QUEUE_PAUSED =   26
  INVALID_TAG  =   27
  DATASTORE_ERROR = 10000

  _ErrorCode_NAMES = {
    0: "OK",
    1: "UNKNOWN_QUEUE",
    2: "TRANSIENT_ERROR",
    3: "INTERNAL_ERROR",
    4: "TASK_TOO_LARGE",
    5: "INVALID_TASK_NAME",
    6: "INVALID_QUEUE_NAME",
    7: "INVALID_URL",
    8: "INVALID_QUEUE_RATE",
    9: "PERMISSION_DENIED",
    10: "TASK_ALREADY_EXISTS",
    11: "TOMBSTONED_TASK",
    12: "INVALID_ETA",
    13: "INVALID_REQUEST",
    14: "UNKNOWN_TASK",
    15: "TOMBSTONED_QUEUE",
    16: "DUPLICATE_TASK_NAME",
    17: "SKIPPED",
    18: "TOO_MANY_TASKS",
    19: "INVALID_PAYLOAD",
    20: "INVALID_RETRY_PARAMETERS",
    21: "INVALID_QUEUE_MODE",
    22: "ACL_LOOKUP_ERROR",
    23: "TRANSACTIONAL_REQUEST_TOO_LARGE",
    24: "INCORRECT_CREATOR_NAME",
    25: "TASK_LEASE_EXPIRED",
    26: "QUEUE_PAUSED",
    27: "INVALID_TAG",
    10000: "DATASTORE_ERROR",
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueServiceError'
class TaskQueueRetryParameters(ProtocolBuffer.ProtocolMessage):
  has_retry_limit_ = 0
  retry_limit_ = 0
  has_age_limit_sec_ = 0
  age_limit_sec_ = 0
  has_min_backoff_sec_ = 0
  min_backoff_sec_ = 0.1
  has_max_backoff_sec_ = 0
  max_backoff_sec_ = 3600.0
  has_max_doublings_ = 0
  max_doublings_ = 16

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def retry_limit(self): return self.retry_limit_

  def set_retry_limit(self, x):
    self.has_retry_limit_ = 1
    self.retry_limit_ = x

  def clear_retry_limit(self):
    if self.has_retry_limit_:
      self.has_retry_limit_ = 0
      self.retry_limit_ = 0

  def has_retry_limit(self): return self.has_retry_limit_

  def age_limit_sec(self): return self.age_limit_sec_

  def set_age_limit_sec(self, x):
    self.has_age_limit_sec_ = 1
    self.age_limit_sec_ = x

  def clear_age_limit_sec(self):
    if self.has_age_limit_sec_:
      self.has_age_limit_sec_ = 0
      self.age_limit_sec_ = 0

  def has_age_limit_sec(self): return self.has_age_limit_sec_

  def min_backoff_sec(self): return self.min_backoff_sec_

  def set_min_backoff_sec(self, x):
    self.has_min_backoff_sec_ = 1
    self.min_backoff_sec_ = x

  def clear_min_backoff_sec(self):
    if self.has_min_backoff_sec_:
      self.has_min_backoff_sec_ = 0
      self.min_backoff_sec_ = 0.1

  def has_min_backoff_sec(self): return self.has_min_backoff_sec_

  def max_backoff_sec(self): return self.max_backoff_sec_

  def set_max_backoff_sec(self, x):
    self.has_max_backoff_sec_ = 1
    self.max_backoff_sec_ = x

  def clear_max_backoff_sec(self):
    if self.has_max_backoff_sec_:
      self.has_max_backoff_sec_ = 0
      self.max_backoff_sec_ = 3600.0

  def has_max_backoff_sec(self): return self.has_max_backoff_sec_

  def max_doublings(self): return self.max_doublings_

  def set_max_doublings(self, x):
    self.has_max_doublings_ = 1
    self.max_doublings_ = x

  def clear_max_doublings(self):
    if self.has_max_doublings_:
      self.has_max_doublings_ = 0
      self.max_doublings_ = 16

  def has_max_doublings(self): return self.has_max_doublings_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_retry_limit()): self.set_retry_limit(x.retry_limit())
    if (x.has_age_limit_sec()): self.set_age_limit_sec(x.age_limit_sec())
    if (x.has_min_backoff_sec()): self.set_min_backoff_sec(x.min_backoff_sec())
    if (x.has_max_backoff_sec()): self.set_max_backoff_sec(x.max_backoff_sec())
    if (x.has_max_doublings()): self.set_max_doublings(x.max_doublings())

  def Equals(self, x):
    if x is self: return 1
    if self.has_retry_limit_ != x.has_retry_limit_: return 0
    if self.has_retry_limit_ and self.retry_limit_ != x.retry_limit_: return 0
    if self.has_age_limit_sec_ != x.has_age_limit_sec_: return 0
    if self.has_age_limit_sec_ and self.age_limit_sec_ != x.age_limit_sec_: return 0
    if self.has_min_backoff_sec_ != x.has_min_backoff_sec_: return 0
    if self.has_min_backoff_sec_ and self.min_backoff_sec_ != x.min_backoff_sec_: return 0
    if self.has_max_backoff_sec_ != x.has_max_backoff_sec_: return 0
    if self.has_max_backoff_sec_ and self.max_backoff_sec_ != x.max_backoff_sec_: return 0
    if self.has_max_doublings_ != x.has_max_doublings_: return 0
    if self.has_max_doublings_ and self.max_doublings_ != x.max_doublings_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_retry_limit_): n += 1 + self.lengthVarInt64(self.retry_limit_)
    if (self.has_age_limit_sec_): n += 1 + self.lengthVarInt64(self.age_limit_sec_)
    if (self.has_min_backoff_sec_): n += 9
    if (self.has_max_backoff_sec_): n += 9
    if (self.has_max_doublings_): n += 1 + self.lengthVarInt64(self.max_doublings_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_retry_limit_): n += 1 + self.lengthVarInt64(self.retry_limit_)
    if (self.has_age_limit_sec_): n += 1 + self.lengthVarInt64(self.age_limit_sec_)
    if (self.has_min_backoff_sec_): n += 9
    if (self.has_max_backoff_sec_): n += 9
    if (self.has_max_doublings_): n += 1 + self.lengthVarInt64(self.max_doublings_)
    return n

  def Clear(self):
    self.clear_retry_limit()
    self.clear_age_limit_sec()
    self.clear_min_backoff_sec()
    self.clear_max_backoff_sec()
    self.clear_max_doublings()

  def OutputUnchecked(self, out):
    if (self.has_retry_limit_):
      out.putVarInt32(8)
      out.putVarInt32(self.retry_limit_)
    if (self.has_age_limit_sec_):
      out.putVarInt32(16)
      out.putVarInt64(self.age_limit_sec_)
    if (self.has_min_backoff_sec_):
      out.putVarInt32(25)
      out.putDouble(self.min_backoff_sec_)
    if (self.has_max_backoff_sec_):
      out.putVarInt32(33)
      out.putDouble(self.max_backoff_sec_)
    if (self.has_max_doublings_):
      out.putVarInt32(40)
      out.putVarInt32(self.max_doublings_)

  def OutputPartial(self, out):
    if (self.has_retry_limit_):
      out.putVarInt32(8)
      out.putVarInt32(self.retry_limit_)
    if (self.has_age_limit_sec_):
      out.putVarInt32(16)
      out.putVarInt64(self.age_limit_sec_)
    if (self.has_min_backoff_sec_):
      out.putVarInt32(25)
      out.putDouble(self.min_backoff_sec_)
    if (self.has_max_backoff_sec_):
      out.putVarInt32(33)
      out.putDouble(self.max_backoff_sec_)
    if (self.has_max_doublings_):
      out.putVarInt32(40)
      out.putVarInt32(self.max_doublings_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_retry_limit(d.getVarInt32())
        continue
      if tt == 16:
        self.set_age_limit_sec(d.getVarInt64())
        continue
      if tt == 25:
        self.set_min_backoff_sec(d.getDouble())
        continue
      if tt == 33:
        self.set_max_backoff_sec(d.getDouble())
        continue
      if tt == 40:
        self.set_max_doublings(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_retry_limit_: res+=prefix+("retry_limit: %s\n" % self.DebugFormatInt32(self.retry_limit_))
    if self.has_age_limit_sec_: res+=prefix+("age_limit_sec: %s\n" % self.DebugFormatInt64(self.age_limit_sec_))
    if self.has_min_backoff_sec_: res+=prefix+("min_backoff_sec: %s\n" % self.DebugFormat(self.min_backoff_sec_))
    if self.has_max_backoff_sec_: res+=prefix+("max_backoff_sec: %s\n" % self.DebugFormat(self.max_backoff_sec_))
    if self.has_max_doublings_: res+=prefix+("max_doublings: %s\n" % self.DebugFormatInt32(self.max_doublings_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kretry_limit = 1
  kage_limit_sec = 2
  kmin_backoff_sec = 3
  kmax_backoff_sec = 4
  kmax_doublings = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "retry_limit",
    2: "age_limit_sec",
    3: "min_backoff_sec",
    4: "max_backoff_sec",
    5: "max_doublings",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.DOUBLE,
    4: ProtocolBuffer.Encoder.DOUBLE,
    5: ProtocolBuffer.Encoder.NUMERIC,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueRetryParameters'
class TaskQueueAcl(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.user_email_ = []
    self.writer_email_ = []
    if contents is not None: self.MergeFromString(contents)

  def user_email_size(self): return len(self.user_email_)
  def user_email_list(self): return self.user_email_

  def user_email(self, i):
    return self.user_email_[i]

  def set_user_email(self, i, x):
    self.user_email_[i] = x

  def add_user_email(self, x):
    self.user_email_.append(x)

  def clear_user_email(self):
    self.user_email_ = []

  def writer_email_size(self): return len(self.writer_email_)
  def writer_email_list(self): return self.writer_email_

  def writer_email(self, i):
    return self.writer_email_[i]

  def set_writer_email(self, i, x):
    self.writer_email_[i] = x

  def add_writer_email(self, x):
    self.writer_email_.append(x)

  def clear_writer_email(self):
    self.writer_email_ = []


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.user_email_size()): self.add_user_email(x.user_email(i))
    for i in xrange(x.writer_email_size()): self.add_writer_email(x.writer_email(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.user_email_) != len(x.user_email_): return 0
    for e1, e2 in zip(self.user_email_, x.user_email_):
      if e1 != e2: return 0
    if len(self.writer_email_) != len(x.writer_email_): return 0
    for e1, e2 in zip(self.writer_email_, x.writer_email_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.user_email_)
    for i in xrange(len(self.user_email_)): n += self.lengthString(len(self.user_email_[i]))
    n += 1 * len(self.writer_email_)
    for i in xrange(len(self.writer_email_)): n += self.lengthString(len(self.writer_email_[i]))
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.user_email_)
    for i in xrange(len(self.user_email_)): n += self.lengthString(len(self.user_email_[i]))
    n += 1 * len(self.writer_email_)
    for i in xrange(len(self.writer_email_)): n += self.lengthString(len(self.writer_email_[i]))
    return n

  def Clear(self):
    self.clear_user_email()
    self.clear_writer_email()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.user_email_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.user_email_[i])
    for i in xrange(len(self.writer_email_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.writer_email_[i])

  def OutputPartial(self, out):
    for i in xrange(len(self.user_email_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.user_email_[i])
    for i in xrange(len(self.writer_email_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.writer_email_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.add_user_email(d.getPrefixedString())
        continue
      if tt == 18:
        self.add_writer_email(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.user_email_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("user_email%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    cnt=0
    for e in self.writer_email_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("writer_email%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kuser_email = 1
  kwriter_email = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "user_email",
    2: "writer_email",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueAcl'
class TaskQueueHttpHeader(ProtocolBuffer.ProtocolMessage):
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
    out.putVarInt32(10)
    out.putPrefixedString(self.key_)
    out.putVarInt32(18)
    out.putPrefixedString(self.value_)

  def OutputPartial(self, out):
    if (self.has_key_):
      out.putVarInt32(10)
      out.putPrefixedString(self.key_)
    if (self.has_value_):
      out.putVarInt32(18)
      out.putPrefixedString(self.value_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_key(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_value(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_: res+=prefix+("key: %s\n" % self.DebugFormatString(self.key_))
    if self.has_value_: res+=prefix+("value: %s\n" % self.DebugFormatString(self.value_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kkey = 1
  kvalue = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "key",
    2: "value",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueHttpHeader'
class TaskQueueMode(ProtocolBuffer.ProtocolMessage):


  PUSH         =    0
  PULL         =    1

  _Mode_NAMES = {
    0: "PUSH",
    1: "PULL",
  }

  def Mode_Name(cls, x): return cls._Mode_NAMES.get(x, "")
  Mode_Name = classmethod(Mode_Name)


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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueMode'
class TaskQueueAddRequest_Header(ProtocolBuffer.ProtocolMessage):
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
    out.putVarInt32(58)
    out.putPrefixedString(self.key_)
    out.putVarInt32(66)
    out.putPrefixedString(self.value_)

  def OutputPartial(self, out):
    if (self.has_key_):
      out.putVarInt32(58)
      out.putPrefixedString(self.key_)
    if (self.has_value_):
      out.putVarInt32(66)
      out.putPrefixedString(self.value_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 52: break
      if tt == 58:
        self.set_key(d.getPrefixedString())
        continue
      if tt == 66:
        self.set_value(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_: res+=prefix+("key: %s\n" % self.DebugFormatString(self.key_))
    if self.has_value_: res+=prefix+("value: %s\n" % self.DebugFormatString(self.value_))
    return res

class TaskQueueAddRequest_CronTimetable(ProtocolBuffer.ProtocolMessage):
  has_schedule_ = 0
  schedule_ = ""
  has_timezone_ = 0
  timezone_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def schedule(self): return self.schedule_

  def set_schedule(self, x):
    self.has_schedule_ = 1
    self.schedule_ = x

  def clear_schedule(self):
    if self.has_schedule_:
      self.has_schedule_ = 0
      self.schedule_ = ""

  def has_schedule(self): return self.has_schedule_

  def timezone(self): return self.timezone_

  def set_timezone(self, x):
    self.has_timezone_ = 1
    self.timezone_ = x

  def clear_timezone(self):
    if self.has_timezone_:
      self.has_timezone_ = 0
      self.timezone_ = ""

  def has_timezone(self): return self.has_timezone_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_schedule()): self.set_schedule(x.schedule())
    if (x.has_timezone()): self.set_timezone(x.timezone())

  def Equals(self, x):
    if x is self: return 1
    if self.has_schedule_ != x.has_schedule_: return 0
    if self.has_schedule_ and self.schedule_ != x.schedule_: return 0
    if self.has_timezone_ != x.has_timezone_: return 0
    if self.has_timezone_ and self.timezone_ != x.timezone_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_schedule_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: schedule not set.')
    if (not self.has_timezone_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: timezone not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.schedule_))
    n += self.lengthString(len(self.timezone_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_schedule_):
      n += 1
      n += self.lengthString(len(self.schedule_))
    if (self.has_timezone_):
      n += 1
      n += self.lengthString(len(self.timezone_))
    return n

  def Clear(self):
    self.clear_schedule()
    self.clear_timezone()

  def OutputUnchecked(self, out):
    out.putVarInt32(106)
    out.putPrefixedString(self.schedule_)
    out.putVarInt32(114)
    out.putPrefixedString(self.timezone_)

  def OutputPartial(self, out):
    if (self.has_schedule_):
      out.putVarInt32(106)
      out.putPrefixedString(self.schedule_)
    if (self.has_timezone_):
      out.putVarInt32(114)
      out.putPrefixedString(self.timezone_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 100: break
      if tt == 106:
        self.set_schedule(d.getPrefixedString())
        continue
      if tt == 114:
        self.set_timezone(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_schedule_: res+=prefix+("schedule: %s\n" % self.DebugFormatString(self.schedule_))
    if self.has_timezone_: res+=prefix+("timezone: %s\n" % self.DebugFormatString(self.timezone_))
    return res

class TaskQueueAddRequest(ProtocolBuffer.ProtocolMessage):


  GET          =    1
  POST         =    2
  HEAD         =    3
  PUT          =    4
  DELETE       =    5

  _RequestMethod_NAMES = {
    1: "GET",
    2: "POST",
    3: "HEAD",
    4: "PUT",
    5: "DELETE",
  }

  def RequestMethod_Name(cls, x): return cls._RequestMethod_NAMES.get(x, "")
  RequestMethod_Name = classmethod(RequestMethod_Name)

  has_queue_name_ = 0
  queue_name_ = ""
  has_task_name_ = 0
  task_name_ = ""
  has_eta_usec_ = 0
  eta_usec_ = 0
  has_method_ = 0
  method_ = 2
  has_url_ = 0
  url_ = ""
  has_body_ = 0
  body_ = ""
  has_transaction_ = 0
  transaction_ = None
  has_datastore_transaction_ = 0
  datastore_transaction_ = ""
  has_app_id_ = 0
  app_id_ = ""
  has_crontimetable_ = 0
  crontimetable_ = None
  has_description_ = 0
  description_ = ""
  has_payload_ = 0
  payload_ = None
  has_retry_parameters_ = 0
  retry_parameters_ = None
  has_mode_ = 0
  mode_ = 0
  has_tag_ = 0
  tag_ = ""
  has_cron_retry_parameters_ = 0
  cron_retry_parameters_ = None

  def __init__(self, contents=None):
    self.header_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def queue_name(self): return self.queue_name_

  def set_queue_name(self, x):
    self.has_queue_name_ = 1
    self.queue_name_ = x

  def clear_queue_name(self):
    if self.has_queue_name_:
      self.has_queue_name_ = 0
      self.queue_name_ = ""

  def has_queue_name(self): return self.has_queue_name_

  def task_name(self): return self.task_name_

  def set_task_name(self, x):
    self.has_task_name_ = 1
    self.task_name_ = x

  def clear_task_name(self):
    if self.has_task_name_:
      self.has_task_name_ = 0
      self.task_name_ = ""

  def has_task_name(self): return self.has_task_name_

  def eta_usec(self): return self.eta_usec_

  def set_eta_usec(self, x):
    self.has_eta_usec_ = 1
    self.eta_usec_ = x

  def clear_eta_usec(self):
    if self.has_eta_usec_:
      self.has_eta_usec_ = 0
      self.eta_usec_ = 0

  def has_eta_usec(self): return self.has_eta_usec_

  def method(self): return self.method_

  def set_method(self, x):
    self.has_method_ = 1
    self.method_ = x

  def clear_method(self):
    if self.has_method_:
      self.has_method_ = 0
      self.method_ = 2

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
    x = TaskQueueAddRequest_Header()
    self.header_.append(x)
    return x

  def clear_header(self):
    self.header_ = []
  def body(self): return self.body_

  def set_body(self, x):
    self.has_body_ = 1
    self.body_ = x

  def clear_body(self):
    if self.has_body_:
      self.has_body_ = 0
      self.body_ = ""

  def has_body(self): return self.has_body_

  def transaction(self):
    if self.transaction_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.transaction_ is None: self.transaction_ = Transaction()
      finally:
        self.lazy_init_lock_.release()
    return self.transaction_

  def mutable_transaction(self): self.has_transaction_ = 1; return self.transaction()

  def clear_transaction(self):

    if self.has_transaction_:
      self.has_transaction_ = 0;
      if self.transaction_ is not None: self.transaction_.Clear()

  def has_transaction(self): return self.has_transaction_

  def datastore_transaction(self): return self.datastore_transaction_

  def set_datastore_transaction(self, x):
    self.has_datastore_transaction_ = 1
    self.datastore_transaction_ = x

  def clear_datastore_transaction(self):
    if self.has_datastore_transaction_:
      self.has_datastore_transaction_ = 0
      self.datastore_transaction_ = ""

  def has_datastore_transaction(self): return self.has_datastore_transaction_

  def app_id(self): return self.app_id_

  def set_app_id(self, x):
    self.has_app_id_ = 1
    self.app_id_ = x

  def clear_app_id(self):
    if self.has_app_id_:
      self.has_app_id_ = 0
      self.app_id_ = ""

  def has_app_id(self): return self.has_app_id_

  def crontimetable(self):
    if self.crontimetable_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.crontimetable_ is None: self.crontimetable_ = TaskQueueAddRequest_CronTimetable()
      finally:
        self.lazy_init_lock_.release()
    return self.crontimetable_

  def mutable_crontimetable(self): self.has_crontimetable_ = 1; return self.crontimetable()

  def clear_crontimetable(self):

    if self.has_crontimetable_:
      self.has_crontimetable_ = 0;
      if self.crontimetable_ is not None: self.crontimetable_.Clear()

  def has_crontimetable(self): return self.has_crontimetable_

  def description(self): return self.description_

  def set_description(self, x):
    self.has_description_ = 1
    self.description_ = x

  def clear_description(self):
    if self.has_description_:
      self.has_description_ = 0
      self.description_ = ""

  def has_description(self): return self.has_description_

  def payload(self):
    if self.payload_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.payload_ is None: self.payload_ = MessageSet()
      finally:
        self.lazy_init_lock_.release()
    return self.payload_

  def mutable_payload(self): self.has_payload_ = 1; return self.payload()

  def clear_payload(self):

    if self.has_payload_:
      self.has_payload_ = 0;
      if self.payload_ is not None: self.payload_.Clear()

  def has_payload(self): return self.has_payload_

  def retry_parameters(self):
    if self.retry_parameters_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.retry_parameters_ is None: self.retry_parameters_ = TaskQueueRetryParameters()
      finally:
        self.lazy_init_lock_.release()
    return self.retry_parameters_

  def mutable_retry_parameters(self): self.has_retry_parameters_ = 1; return self.retry_parameters()

  def clear_retry_parameters(self):

    if self.has_retry_parameters_:
      self.has_retry_parameters_ = 0;
      if self.retry_parameters_ is not None: self.retry_parameters_.Clear()

  def has_retry_parameters(self): return self.has_retry_parameters_

  def mode(self): return self.mode_

  def set_mode(self, x):
    self.has_mode_ = 1
    self.mode_ = x

  def clear_mode(self):
    if self.has_mode_:
      self.has_mode_ = 0
      self.mode_ = 0

  def has_mode(self): return self.has_mode_

  def tag(self): return self.tag_

  def set_tag(self, x):
    self.has_tag_ = 1
    self.tag_ = x

  def clear_tag(self):
    if self.has_tag_:
      self.has_tag_ = 0
      self.tag_ = ""

  def has_tag(self): return self.has_tag_

  def cron_retry_parameters(self):
    if self.cron_retry_parameters_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.cron_retry_parameters_ is None: self.cron_retry_parameters_ = TaskQueueRetryParameters()
      finally:
        self.lazy_init_lock_.release()
    return self.cron_retry_parameters_

  def mutable_cron_retry_parameters(self): self.has_cron_retry_parameters_ = 1; return self.cron_retry_parameters()

  def clear_cron_retry_parameters(self):

    if self.has_cron_retry_parameters_:
      self.has_cron_retry_parameters_ = 0;
      if self.cron_retry_parameters_ is not None: self.cron_retry_parameters_.Clear()

  def has_cron_retry_parameters(self): return self.has_cron_retry_parameters_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_queue_name()): self.set_queue_name(x.queue_name())
    if (x.has_task_name()): self.set_task_name(x.task_name())
    if (x.has_eta_usec()): self.set_eta_usec(x.eta_usec())
    if (x.has_method()): self.set_method(x.method())
    if (x.has_url()): self.set_url(x.url())
    for i in xrange(x.header_size()): self.add_header().CopyFrom(x.header(i))
    if (x.has_body()): self.set_body(x.body())
    if (x.has_transaction()): self.mutable_transaction().MergeFrom(x.transaction())
    if (x.has_datastore_transaction()): self.set_datastore_transaction(x.datastore_transaction())
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_crontimetable()): self.mutable_crontimetable().MergeFrom(x.crontimetable())
    if (x.has_description()): self.set_description(x.description())
    if (x.has_payload()): self.mutable_payload().MergeFrom(x.payload())
    if (x.has_retry_parameters()): self.mutable_retry_parameters().MergeFrom(x.retry_parameters())
    if (x.has_mode()): self.set_mode(x.mode())
    if (x.has_tag()): self.set_tag(x.tag())
    if (x.has_cron_retry_parameters()): self.mutable_cron_retry_parameters().MergeFrom(x.cron_retry_parameters())

  def Equals(self, x):
    if x is self: return 1
    if self.has_queue_name_ != x.has_queue_name_: return 0
    if self.has_queue_name_ and self.queue_name_ != x.queue_name_: return 0
    if self.has_task_name_ != x.has_task_name_: return 0
    if self.has_task_name_ and self.task_name_ != x.task_name_: return 0
    if self.has_eta_usec_ != x.has_eta_usec_: return 0
    if self.has_eta_usec_ and self.eta_usec_ != x.eta_usec_: return 0
    if self.has_method_ != x.has_method_: return 0
    if self.has_method_ and self.method_ != x.method_: return 0
    if self.has_url_ != x.has_url_: return 0
    if self.has_url_ and self.url_ != x.url_: return 0
    if len(self.header_) != len(x.header_): return 0
    for e1, e2 in zip(self.header_, x.header_):
      if e1 != e2: return 0
    if self.has_body_ != x.has_body_: return 0
    if self.has_body_ and self.body_ != x.body_: return 0
    if self.has_transaction_ != x.has_transaction_: return 0
    if self.has_transaction_ and self.transaction_ != x.transaction_: return 0
    if self.has_datastore_transaction_ != x.has_datastore_transaction_: return 0
    if self.has_datastore_transaction_ and self.datastore_transaction_ != x.datastore_transaction_: return 0
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_crontimetable_ != x.has_crontimetable_: return 0
    if self.has_crontimetable_ and self.crontimetable_ != x.crontimetable_: return 0
    if self.has_description_ != x.has_description_: return 0
    if self.has_description_ and self.description_ != x.description_: return 0
    if self.has_payload_ != x.has_payload_: return 0
    if self.has_payload_ and self.payload_ != x.payload_: return 0
    if self.has_retry_parameters_ != x.has_retry_parameters_: return 0
    if self.has_retry_parameters_ and self.retry_parameters_ != x.retry_parameters_: return 0
    if self.has_mode_ != x.has_mode_: return 0
    if self.has_mode_ and self.mode_ != x.mode_: return 0
    if self.has_tag_ != x.has_tag_: return 0
    if self.has_tag_ and self.tag_ != x.tag_: return 0
    if self.has_cron_retry_parameters_ != x.has_cron_retry_parameters_: return 0
    if self.has_cron_retry_parameters_ and self.cron_retry_parameters_ != x.cron_retry_parameters_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_queue_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: queue_name not set.')
    if (not self.has_task_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: task_name not set.')
    if (not self.has_eta_usec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: eta_usec not set.')
    for p in self.header_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_transaction_ and not self.transaction_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_crontimetable_ and not self.crontimetable_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_payload_ and not self.payload_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_retry_parameters_ and not self.retry_parameters_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_cron_retry_parameters_ and not self.cron_retry_parameters_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.queue_name_))
    n += self.lengthString(len(self.task_name_))
    n += self.lengthVarInt64(self.eta_usec_)
    if (self.has_method_): n += 1 + self.lengthVarInt64(self.method_)
    if (self.has_url_): n += 1 + self.lengthString(len(self.url_))
    n += 2 * len(self.header_)
    for i in xrange(len(self.header_)): n += self.header_[i].ByteSize()
    if (self.has_body_): n += 1 + self.lengthString(len(self.body_))
    if (self.has_transaction_): n += 1 + self.lengthString(self.transaction_.ByteSize())
    if (self.has_datastore_transaction_): n += 2 + self.lengthString(len(self.datastore_transaction_))
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    if (self.has_crontimetable_): n += 2 + self.crontimetable_.ByteSize()
    if (self.has_description_): n += 1 + self.lengthString(len(self.description_))
    if (self.has_payload_): n += 2 + self.lengthString(self.payload_.ByteSize())
    if (self.has_retry_parameters_): n += 2 + self.lengthString(self.retry_parameters_.ByteSize())
    if (self.has_mode_): n += 2 + self.lengthVarInt64(self.mode_)
    if (self.has_tag_): n += 2 + self.lengthString(len(self.tag_))
    if (self.has_cron_retry_parameters_): n += 2 + self.lengthString(self.cron_retry_parameters_.ByteSize())
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_queue_name_):
      n += 1
      n += self.lengthString(len(self.queue_name_))
    if (self.has_task_name_):
      n += 1
      n += self.lengthString(len(self.task_name_))
    if (self.has_eta_usec_):
      n += 1
      n += self.lengthVarInt64(self.eta_usec_)
    if (self.has_method_): n += 1 + self.lengthVarInt64(self.method_)
    if (self.has_url_): n += 1 + self.lengthString(len(self.url_))
    n += 2 * len(self.header_)
    for i in xrange(len(self.header_)): n += self.header_[i].ByteSizePartial()
    if (self.has_body_): n += 1 + self.lengthString(len(self.body_))
    if (self.has_transaction_): n += 1 + self.lengthString(self.transaction_.ByteSizePartial())
    if (self.has_datastore_transaction_): n += 2 + self.lengthString(len(self.datastore_transaction_))
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    if (self.has_crontimetable_): n += 2 + self.crontimetable_.ByteSizePartial()
    if (self.has_description_): n += 1 + self.lengthString(len(self.description_))
    if (self.has_payload_): n += 2 + self.lengthString(self.payload_.ByteSizePartial())
    if (self.has_retry_parameters_): n += 2 + self.lengthString(self.retry_parameters_.ByteSizePartial())
    if (self.has_mode_): n += 2 + self.lengthVarInt64(self.mode_)
    if (self.has_tag_): n += 2 + self.lengthString(len(self.tag_))
    if (self.has_cron_retry_parameters_): n += 2 + self.lengthString(self.cron_retry_parameters_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_queue_name()
    self.clear_task_name()
    self.clear_eta_usec()
    self.clear_method()
    self.clear_url()
    self.clear_header()
    self.clear_body()
    self.clear_transaction()
    self.clear_datastore_transaction()
    self.clear_app_id()
    self.clear_crontimetable()
    self.clear_description()
    self.clear_payload()
    self.clear_retry_parameters()
    self.clear_mode()
    self.clear_tag()
    self.clear_cron_retry_parameters()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.queue_name_)
    out.putVarInt32(18)
    out.putPrefixedString(self.task_name_)
    out.putVarInt32(24)
    out.putVarInt64(self.eta_usec_)
    if (self.has_url_):
      out.putVarInt32(34)
      out.putPrefixedString(self.url_)
    if (self.has_method_):
      out.putVarInt32(40)
      out.putVarInt32(self.method_)
    for i in xrange(len(self.header_)):
      out.putVarInt32(51)
      self.header_[i].OutputUnchecked(out)
      out.putVarInt32(52)
    if (self.has_body_):
      out.putVarInt32(74)
      out.putPrefixedString(self.body_)
    if (self.has_transaction_):
      out.putVarInt32(82)
      out.putVarInt32(self.transaction_.ByteSize())
      self.transaction_.OutputUnchecked(out)
    if (self.has_app_id_):
      out.putVarInt32(90)
      out.putPrefixedString(self.app_id_)
    if (self.has_crontimetable_):
      out.putVarInt32(99)
      self.crontimetable_.OutputUnchecked(out)
      out.putVarInt32(100)
    if (self.has_description_):
      out.putVarInt32(122)
      out.putPrefixedString(self.description_)
    if (self.has_payload_):
      out.putVarInt32(130)
      out.putVarInt32(self.payload_.ByteSize())
      self.payload_.OutputUnchecked(out)
    if (self.has_retry_parameters_):
      out.putVarInt32(138)
      out.putVarInt32(self.retry_parameters_.ByteSize())
      self.retry_parameters_.OutputUnchecked(out)
    if (self.has_mode_):
      out.putVarInt32(144)
      out.putVarInt32(self.mode_)
    if (self.has_tag_):
      out.putVarInt32(154)
      out.putPrefixedString(self.tag_)
    if (self.has_cron_retry_parameters_):
      out.putVarInt32(162)
      out.putVarInt32(self.cron_retry_parameters_.ByteSize())
      self.cron_retry_parameters_.OutputUnchecked(out)
    if (self.has_datastore_transaction_):
      out.putVarInt32(170)
      out.putPrefixedString(self.datastore_transaction_)

  def OutputPartial(self, out):
    if (self.has_queue_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.queue_name_)
    if (self.has_task_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.task_name_)
    if (self.has_eta_usec_):
      out.putVarInt32(24)
      out.putVarInt64(self.eta_usec_)
    if (self.has_url_):
      out.putVarInt32(34)
      out.putPrefixedString(self.url_)
    if (self.has_method_):
      out.putVarInt32(40)
      out.putVarInt32(self.method_)
    for i in xrange(len(self.header_)):
      out.putVarInt32(51)
      self.header_[i].OutputPartial(out)
      out.putVarInt32(52)
    if (self.has_body_):
      out.putVarInt32(74)
      out.putPrefixedString(self.body_)
    if (self.has_transaction_):
      out.putVarInt32(82)
      out.putVarInt32(self.transaction_.ByteSizePartial())
      self.transaction_.OutputPartial(out)
    if (self.has_app_id_):
      out.putVarInt32(90)
      out.putPrefixedString(self.app_id_)
    if (self.has_crontimetable_):
      out.putVarInt32(99)
      self.crontimetable_.OutputPartial(out)
      out.putVarInt32(100)
    if (self.has_description_):
      out.putVarInt32(122)
      out.putPrefixedString(self.description_)
    if (self.has_payload_):
      out.putVarInt32(130)
      out.putVarInt32(self.payload_.ByteSizePartial())
      self.payload_.OutputPartial(out)
    if (self.has_retry_parameters_):
      out.putVarInt32(138)
      out.putVarInt32(self.retry_parameters_.ByteSizePartial())
      self.retry_parameters_.OutputPartial(out)
    if (self.has_mode_):
      out.putVarInt32(144)
      out.putVarInt32(self.mode_)
    if (self.has_tag_):
      out.putVarInt32(154)
      out.putPrefixedString(self.tag_)
    if (self.has_cron_retry_parameters_):
      out.putVarInt32(162)
      out.putVarInt32(self.cron_retry_parameters_.ByteSizePartial())
      self.cron_retry_parameters_.OutputPartial(out)
    if (self.has_datastore_transaction_):
      out.putVarInt32(170)
      out.putPrefixedString(self.datastore_transaction_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_queue_name(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_task_name(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_eta_usec(d.getVarInt64())
        continue
      if tt == 34:
        self.set_url(d.getPrefixedString())
        continue
      if tt == 40:
        self.set_method(d.getVarInt32())
        continue
      if tt == 51:
        self.add_header().TryMerge(d)
        continue
      if tt == 74:
        self.set_body(d.getPrefixedString())
        continue
      if tt == 82:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_transaction().TryMerge(tmp)
        continue
      if tt == 90:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 99:
        self.mutable_crontimetable().TryMerge(d)
        continue
      if tt == 122:
        self.set_description(d.getPrefixedString())
        continue
      if tt == 130:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_payload().TryMerge(tmp)
        continue
      if tt == 138:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_retry_parameters().TryMerge(tmp)
        continue
      if tt == 144:
        self.set_mode(d.getVarInt32())
        continue
      if tt == 154:
        self.set_tag(d.getPrefixedString())
        continue
      if tt == 162:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_cron_retry_parameters().TryMerge(tmp)
        continue
      if tt == 170:
        self.set_datastore_transaction(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_queue_name_: res+=prefix+("queue_name: %s\n" % self.DebugFormatString(self.queue_name_))
    if self.has_task_name_: res+=prefix+("task_name: %s\n" % self.DebugFormatString(self.task_name_))
    if self.has_eta_usec_: res+=prefix+("eta_usec: %s\n" % self.DebugFormatInt64(self.eta_usec_))
    if self.has_method_: res+=prefix+("method: %s\n" % self.DebugFormatInt32(self.method_))
    if self.has_url_: res+=prefix+("url: %s\n" % self.DebugFormatString(self.url_))
    cnt=0
    for e in self.header_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Header%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    if self.has_body_: res+=prefix+("body: %s\n" % self.DebugFormatString(self.body_))
    if self.has_transaction_:
      res+=prefix+"transaction <\n"
      res+=self.transaction_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_datastore_transaction_: res+=prefix+("datastore_transaction: %s\n" % self.DebugFormatString(self.datastore_transaction_))
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_crontimetable_:
      res+=prefix+"CronTimetable {\n"
      res+=self.crontimetable_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
    if self.has_description_: res+=prefix+("description: %s\n" % self.DebugFormatString(self.description_))
    if self.has_payload_:
      res+=prefix+"payload <\n"
      res+=self.payload_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_retry_parameters_:
      res+=prefix+"retry_parameters <\n"
      res+=self.retry_parameters_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_mode_: res+=prefix+("mode: %s\n" % self.DebugFormatInt32(self.mode_))
    if self.has_tag_: res+=prefix+("tag: %s\n" % self.DebugFormatString(self.tag_))
    if self.has_cron_retry_parameters_:
      res+=prefix+"cron_retry_parameters <\n"
      res+=self.cron_retry_parameters_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kqueue_name = 1
  ktask_name = 2
  keta_usec = 3
  kmethod = 5
  kurl = 4
  kHeaderGroup = 6
  kHeaderkey = 7
  kHeadervalue = 8
  kbody = 9
  ktransaction = 10
  kdatastore_transaction = 21
  kapp_id = 11
  kCronTimetableGroup = 12
  kCronTimetableschedule = 13
  kCronTimetabletimezone = 14
  kdescription = 15
  kpayload = 16
  kretry_parameters = 17
  kmode = 18
  ktag = 19
  kcron_retry_parameters = 20

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "queue_name",
    2: "task_name",
    3: "eta_usec",
    4: "url",
    5: "method",
    6: "Header",
    7: "key",
    8: "value",
    9: "body",
    10: "transaction",
    11: "app_id",
    12: "CronTimetable",
    13: "schedule",
    14: "timezone",
    15: "description",
    16: "payload",
    17: "retry_parameters",
    18: "mode",
    19: "tag",
    20: "cron_retry_parameters",
    21: "datastore_transaction",
  }, 21)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.STARTGROUP,
    7: ProtocolBuffer.Encoder.STRING,
    8: ProtocolBuffer.Encoder.STRING,
    9: ProtocolBuffer.Encoder.STRING,
    10: ProtocolBuffer.Encoder.STRING,
    11: ProtocolBuffer.Encoder.STRING,
    12: ProtocolBuffer.Encoder.STARTGROUP,
    13: ProtocolBuffer.Encoder.STRING,
    14: ProtocolBuffer.Encoder.STRING,
    15: ProtocolBuffer.Encoder.STRING,
    16: ProtocolBuffer.Encoder.STRING,
    17: ProtocolBuffer.Encoder.STRING,
    18: ProtocolBuffer.Encoder.NUMERIC,
    19: ProtocolBuffer.Encoder.STRING,
    20: ProtocolBuffer.Encoder.STRING,
    21: ProtocolBuffer.Encoder.STRING,
  }, 21, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueAddRequest'
class TaskQueueAddResponse(ProtocolBuffer.ProtocolMessage):
  has_chosen_task_name_ = 0
  chosen_task_name_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def chosen_task_name(self): return self.chosen_task_name_

  def set_chosen_task_name(self, x):
    self.has_chosen_task_name_ = 1
    self.chosen_task_name_ = x

  def clear_chosen_task_name(self):
    if self.has_chosen_task_name_:
      self.has_chosen_task_name_ = 0
      self.chosen_task_name_ = ""

  def has_chosen_task_name(self): return self.has_chosen_task_name_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_chosen_task_name()): self.set_chosen_task_name(x.chosen_task_name())

  def Equals(self, x):
    if x is self: return 1
    if self.has_chosen_task_name_ != x.has_chosen_task_name_: return 0
    if self.has_chosen_task_name_ and self.chosen_task_name_ != x.chosen_task_name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_chosen_task_name_): n += 1 + self.lengthString(len(self.chosen_task_name_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_chosen_task_name_): n += 1 + self.lengthString(len(self.chosen_task_name_))
    return n

  def Clear(self):
    self.clear_chosen_task_name()

  def OutputUnchecked(self, out):
    if (self.has_chosen_task_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.chosen_task_name_)

  def OutputPartial(self, out):
    if (self.has_chosen_task_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.chosen_task_name_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_chosen_task_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_chosen_task_name_: res+=prefix+("chosen_task_name: %s\n" % self.DebugFormatString(self.chosen_task_name_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kchosen_task_name = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "chosen_task_name",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueAddResponse'
class TaskQueueBulkAddRequest(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.add_request_ = []
    if contents is not None: self.MergeFromString(contents)

  def add_request_size(self): return len(self.add_request_)
  def add_request_list(self): return self.add_request_

  def add_request(self, i):
    return self.add_request_[i]

  def mutable_add_request(self, i):
    return self.add_request_[i]

  def add_add_request(self):
    x = TaskQueueAddRequest()
    self.add_request_.append(x)
    return x

  def clear_add_request(self):
    self.add_request_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.add_request_size()): self.add_add_request().CopyFrom(x.add_request(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.add_request_) != len(x.add_request_): return 0
    for e1, e2 in zip(self.add_request_, x.add_request_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.add_request_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.add_request_)
    for i in xrange(len(self.add_request_)): n += self.lengthString(self.add_request_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.add_request_)
    for i in xrange(len(self.add_request_)): n += self.lengthString(self.add_request_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_add_request()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.add_request_)):
      out.putVarInt32(10)
      out.putVarInt32(self.add_request_[i].ByteSize())
      self.add_request_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.add_request_)):
      out.putVarInt32(10)
      out.putVarInt32(self.add_request_[i].ByteSizePartial())
      self.add_request_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_add_request().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.add_request_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("add_request%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kadd_request = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "add_request",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueBulkAddRequest'
class TaskQueueBulkAddResponse_TaskResult(ProtocolBuffer.ProtocolMessage):
  has_result_ = 0
  result_ = 0
  has_chosen_task_name_ = 0
  chosen_task_name_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def result(self): return self.result_

  def set_result(self, x):
    self.has_result_ = 1
    self.result_ = x

  def clear_result(self):
    if self.has_result_:
      self.has_result_ = 0
      self.result_ = 0

  def has_result(self): return self.has_result_

  def chosen_task_name(self): return self.chosen_task_name_

  def set_chosen_task_name(self, x):
    self.has_chosen_task_name_ = 1
    self.chosen_task_name_ = x

  def clear_chosen_task_name(self):
    if self.has_chosen_task_name_:
      self.has_chosen_task_name_ = 0
      self.chosen_task_name_ = ""

  def has_chosen_task_name(self): return self.has_chosen_task_name_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_result()): self.set_result(x.result())
    if (x.has_chosen_task_name()): self.set_chosen_task_name(x.chosen_task_name())

  def Equals(self, x):
    if x is self: return 1
    if self.has_result_ != x.has_result_: return 0
    if self.has_result_ and self.result_ != x.result_: return 0
    if self.has_chosen_task_name_ != x.has_chosen_task_name_: return 0
    if self.has_chosen_task_name_ and self.chosen_task_name_ != x.chosen_task_name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_result_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: result not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.result_)
    if (self.has_chosen_task_name_): n += 1 + self.lengthString(len(self.chosen_task_name_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_result_):
      n += 1
      n += self.lengthVarInt64(self.result_)
    if (self.has_chosen_task_name_): n += 1 + self.lengthString(len(self.chosen_task_name_))
    return n

  def Clear(self):
    self.clear_result()
    self.clear_chosen_task_name()

  def OutputUnchecked(self, out):
    out.putVarInt32(16)
    out.putVarInt32(self.result_)
    if (self.has_chosen_task_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.chosen_task_name_)

  def OutputPartial(self, out):
    if (self.has_result_):
      out.putVarInt32(16)
      out.putVarInt32(self.result_)
    if (self.has_chosen_task_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.chosen_task_name_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 12: break
      if tt == 16:
        self.set_result(d.getVarInt32())
        continue
      if tt == 26:
        self.set_chosen_task_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_result_: res+=prefix+("result: %s\n" % self.DebugFormatInt32(self.result_))
    if self.has_chosen_task_name_: res+=prefix+("chosen_task_name: %s\n" % self.DebugFormatString(self.chosen_task_name_))
    return res

class TaskQueueBulkAddResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.taskresult_ = []
    if contents is not None: self.MergeFromString(contents)

  def taskresult_size(self): return len(self.taskresult_)
  def taskresult_list(self): return self.taskresult_

  def taskresult(self, i):
    return self.taskresult_[i]

  def mutable_taskresult(self, i):
    return self.taskresult_[i]

  def add_taskresult(self):
    x = TaskQueueBulkAddResponse_TaskResult()
    self.taskresult_.append(x)
    return x

  def clear_taskresult(self):
    self.taskresult_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.taskresult_size()): self.add_taskresult().CopyFrom(x.taskresult(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.taskresult_) != len(x.taskresult_): return 0
    for e1, e2 in zip(self.taskresult_, x.taskresult_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.taskresult_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 2 * len(self.taskresult_)
    for i in xrange(len(self.taskresult_)): n += self.taskresult_[i].ByteSize()
    return n

  def ByteSizePartial(self):
    n = 0
    n += 2 * len(self.taskresult_)
    for i in xrange(len(self.taskresult_)): n += self.taskresult_[i].ByteSizePartial()
    return n

  def Clear(self):
    self.clear_taskresult()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.taskresult_)):
      out.putVarInt32(11)
      self.taskresult_[i].OutputUnchecked(out)
      out.putVarInt32(12)

  def OutputPartial(self, out):
    for i in xrange(len(self.taskresult_)):
      out.putVarInt32(11)
      self.taskresult_[i].OutputPartial(out)
      out.putVarInt32(12)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 11:
        self.add_taskresult().TryMerge(d)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.taskresult_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("TaskResult%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kTaskResultGroup = 1
  kTaskResultresult = 2
  kTaskResultchosen_task_name = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "TaskResult",
    2: "result",
    3: "chosen_task_name",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STARTGROUP,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueBulkAddResponse'
class TaskQueueDeleteRequest(ProtocolBuffer.ProtocolMessage):
  has_queue_name_ = 0
  queue_name_ = ""
  has_app_id_ = 0
  app_id_ = ""

  def __init__(self, contents=None):
    self.task_name_ = []
    if contents is not None: self.MergeFromString(contents)

  def queue_name(self): return self.queue_name_

  def set_queue_name(self, x):
    self.has_queue_name_ = 1
    self.queue_name_ = x

  def clear_queue_name(self):
    if self.has_queue_name_:
      self.has_queue_name_ = 0
      self.queue_name_ = ""

  def has_queue_name(self): return self.has_queue_name_

  def task_name_size(self): return len(self.task_name_)
  def task_name_list(self): return self.task_name_

  def task_name(self, i):
    return self.task_name_[i]

  def set_task_name(self, i, x):
    self.task_name_[i] = x

  def add_task_name(self, x):
    self.task_name_.append(x)

  def clear_task_name(self):
    self.task_name_ = []

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
    if (x.has_queue_name()): self.set_queue_name(x.queue_name())
    for i in xrange(x.task_name_size()): self.add_task_name(x.task_name(i))
    if (x.has_app_id()): self.set_app_id(x.app_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_queue_name_ != x.has_queue_name_: return 0
    if self.has_queue_name_ and self.queue_name_ != x.queue_name_: return 0
    if len(self.task_name_) != len(x.task_name_): return 0
    for e1, e2 in zip(self.task_name_, x.task_name_):
      if e1 != e2: return 0
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_queue_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: queue_name not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.queue_name_))
    n += 1 * len(self.task_name_)
    for i in xrange(len(self.task_name_)): n += self.lengthString(len(self.task_name_[i]))
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_queue_name_):
      n += 1
      n += self.lengthString(len(self.queue_name_))
    n += 1 * len(self.task_name_)
    for i in xrange(len(self.task_name_)): n += self.lengthString(len(self.task_name_[i]))
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    return n

  def Clear(self):
    self.clear_queue_name()
    self.clear_task_name()
    self.clear_app_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.queue_name_)
    for i in xrange(len(self.task_name_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.task_name_[i])
    if (self.has_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.app_id_)

  def OutputPartial(self, out):
    if (self.has_queue_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.queue_name_)
    for i in xrange(len(self.task_name_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.task_name_[i])
    if (self.has_app_id_):
      out.putVarInt32(26)
      out.putPrefixedString(self.app_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_queue_name(d.getPrefixedString())
        continue
      if tt == 18:
        self.add_task_name(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_app_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_queue_name_: res+=prefix+("queue_name: %s\n" % self.DebugFormatString(self.queue_name_))
    cnt=0
    for e in self.task_name_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("task_name%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kqueue_name = 1
  ktask_name = 2
  kapp_id = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "queue_name",
    2: "task_name",
    3: "app_id",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueDeleteRequest'
class TaskQueueDeleteResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.result_ = []
    if contents is not None: self.MergeFromString(contents)

  def result_size(self): return len(self.result_)
  def result_list(self): return self.result_

  def result(self, i):
    return self.result_[i]

  def set_result(self, i, x):
    self.result_[i] = x

  def add_result(self, x):
    self.result_.append(x)

  def clear_result(self):
    self.result_ = []


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.result_size()): self.add_result(x.result(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.result_) != len(x.result_): return 0
    for e1, e2 in zip(self.result_, x.result_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.result_)
    for i in xrange(len(self.result_)): n += self.lengthVarInt64(self.result_[i])
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.result_)
    for i in xrange(len(self.result_)): n += self.lengthVarInt64(self.result_[i])
    return n

  def Clear(self):
    self.clear_result()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.result_)):
      out.putVarInt32(24)
      out.putVarInt32(self.result_[i])

  def OutputPartial(self, out):
    for i in xrange(len(self.result_)):
      out.putVarInt32(24)
      out.putVarInt32(self.result_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 24:
        self.add_result(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.result_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("result%s: %s\n" % (elm, self.DebugFormatInt32(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kresult = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    3: "result",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueDeleteResponse'
class TaskQueueForceRunRequest(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_queue_name_ = 0
  queue_name_ = ""
  has_task_name_ = 0
  task_name_ = ""

  def __init__(self, contents=None):
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

  def queue_name(self): return self.queue_name_

  def set_queue_name(self, x):
    self.has_queue_name_ = 1
    self.queue_name_ = x

  def clear_queue_name(self):
    if self.has_queue_name_:
      self.has_queue_name_ = 0
      self.queue_name_ = ""

  def has_queue_name(self): return self.has_queue_name_

  def task_name(self): return self.task_name_

  def set_task_name(self, x):
    self.has_task_name_ = 1
    self.task_name_ = x

  def clear_task_name(self):
    if self.has_task_name_:
      self.has_task_name_ = 0
      self.task_name_ = ""

  def has_task_name(self): return self.has_task_name_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_queue_name()): self.set_queue_name(x.queue_name())
    if (x.has_task_name()): self.set_task_name(x.task_name())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_queue_name_ != x.has_queue_name_: return 0
    if self.has_queue_name_ and self.queue_name_ != x.queue_name_: return 0
    if self.has_task_name_ != x.has_task_name_: return 0
    if self.has_task_name_ and self.task_name_ != x.task_name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_queue_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: queue_name not set.')
    if (not self.has_task_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: task_name not set.')
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    n += self.lengthString(len(self.queue_name_))
    n += self.lengthString(len(self.task_name_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    if (self.has_queue_name_):
      n += 1
      n += self.lengthString(len(self.queue_name_))
    if (self.has_task_name_):
      n += 1
      n += self.lengthString(len(self.task_name_))
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_queue_name()
    self.clear_task_name()

  def OutputUnchecked(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    out.putVarInt32(18)
    out.putPrefixedString(self.queue_name_)
    out.putVarInt32(26)
    out.putPrefixedString(self.task_name_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    if (self.has_queue_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.queue_name_)
    if (self.has_task_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.task_name_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_queue_name(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_task_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_queue_name_: res+=prefix+("queue_name: %s\n" % self.DebugFormatString(self.queue_name_))
    if self.has_task_name_: res+=prefix+("task_name: %s\n" % self.DebugFormatString(self.task_name_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  kqueue_name = 2
  ktask_name = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "queue_name",
    3: "task_name",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueForceRunRequest'
class TaskQueueForceRunResponse(ProtocolBuffer.ProtocolMessage):
  has_result_ = 0
  result_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def result(self): return self.result_

  def set_result(self, x):
    self.has_result_ = 1
    self.result_ = x

  def clear_result(self):
    if self.has_result_:
      self.has_result_ = 0
      self.result_ = 0

  def has_result(self): return self.has_result_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_result()): self.set_result(x.result())

  def Equals(self, x):
    if x is self: return 1
    if self.has_result_ != x.has_result_: return 0
    if self.has_result_ and self.result_ != x.result_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_result_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: result not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.result_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_result_):
      n += 1
      n += self.lengthVarInt64(self.result_)
    return n

  def Clear(self):
    self.clear_result()

  def OutputUnchecked(self, out):
    out.putVarInt32(24)
    out.putVarInt32(self.result_)

  def OutputPartial(self, out):
    if (self.has_result_):
      out.putVarInt32(24)
      out.putVarInt32(self.result_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 24:
        self.set_result(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_result_: res+=prefix+("result: %s\n" % self.DebugFormatInt32(self.result_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kresult = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    3: "result",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueForceRunResponse'
class TaskQueueUpdateQueueRequest(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_queue_name_ = 0
  queue_name_ = ""
  has_bucket_refill_per_second_ = 0
  bucket_refill_per_second_ = 0.0
  has_bucket_capacity_ = 0
  bucket_capacity_ = 0
  has_user_specified_rate_ = 0
  user_specified_rate_ = ""
  has_retry_parameters_ = 0
  retry_parameters_ = None
  has_max_concurrent_requests_ = 0
  max_concurrent_requests_ = 0
  has_mode_ = 0
  mode_ = 0
  has_acl_ = 0
  acl_ = None

  def __init__(self, contents=None):
    self.header_override_ = []
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

  def queue_name(self): return self.queue_name_

  def set_queue_name(self, x):
    self.has_queue_name_ = 1
    self.queue_name_ = x

  def clear_queue_name(self):
    if self.has_queue_name_:
      self.has_queue_name_ = 0
      self.queue_name_ = ""

  def has_queue_name(self): return self.has_queue_name_

  def bucket_refill_per_second(self): return self.bucket_refill_per_second_

  def set_bucket_refill_per_second(self, x):
    self.has_bucket_refill_per_second_ = 1
    self.bucket_refill_per_second_ = x

  def clear_bucket_refill_per_second(self):
    if self.has_bucket_refill_per_second_:
      self.has_bucket_refill_per_second_ = 0
      self.bucket_refill_per_second_ = 0.0

  def has_bucket_refill_per_second(self): return self.has_bucket_refill_per_second_

  def bucket_capacity(self): return self.bucket_capacity_

  def set_bucket_capacity(self, x):
    self.has_bucket_capacity_ = 1
    self.bucket_capacity_ = x

  def clear_bucket_capacity(self):
    if self.has_bucket_capacity_:
      self.has_bucket_capacity_ = 0
      self.bucket_capacity_ = 0

  def has_bucket_capacity(self): return self.has_bucket_capacity_

  def user_specified_rate(self): return self.user_specified_rate_

  def set_user_specified_rate(self, x):
    self.has_user_specified_rate_ = 1
    self.user_specified_rate_ = x

  def clear_user_specified_rate(self):
    if self.has_user_specified_rate_:
      self.has_user_specified_rate_ = 0
      self.user_specified_rate_ = ""

  def has_user_specified_rate(self): return self.has_user_specified_rate_

  def retry_parameters(self):
    if self.retry_parameters_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.retry_parameters_ is None: self.retry_parameters_ = TaskQueueRetryParameters()
      finally:
        self.lazy_init_lock_.release()
    return self.retry_parameters_

  def mutable_retry_parameters(self): self.has_retry_parameters_ = 1; return self.retry_parameters()

  def clear_retry_parameters(self):

    if self.has_retry_parameters_:
      self.has_retry_parameters_ = 0;
      if self.retry_parameters_ is not None: self.retry_parameters_.Clear()

  def has_retry_parameters(self): return self.has_retry_parameters_

  def max_concurrent_requests(self): return self.max_concurrent_requests_

  def set_max_concurrent_requests(self, x):
    self.has_max_concurrent_requests_ = 1
    self.max_concurrent_requests_ = x

  def clear_max_concurrent_requests(self):
    if self.has_max_concurrent_requests_:
      self.has_max_concurrent_requests_ = 0
      self.max_concurrent_requests_ = 0

  def has_max_concurrent_requests(self): return self.has_max_concurrent_requests_

  def mode(self): return self.mode_

  def set_mode(self, x):
    self.has_mode_ = 1
    self.mode_ = x

  def clear_mode(self):
    if self.has_mode_:
      self.has_mode_ = 0
      self.mode_ = 0

  def has_mode(self): return self.has_mode_

  def acl(self):
    if self.acl_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.acl_ is None: self.acl_ = TaskQueueAcl()
      finally:
        self.lazy_init_lock_.release()
    return self.acl_

  def mutable_acl(self): self.has_acl_ = 1; return self.acl()

  def clear_acl(self):

    if self.has_acl_:
      self.has_acl_ = 0;
      if self.acl_ is not None: self.acl_.Clear()

  def has_acl(self): return self.has_acl_

  def header_override_size(self): return len(self.header_override_)
  def header_override_list(self): return self.header_override_

  def header_override(self, i):
    return self.header_override_[i]

  def mutable_header_override(self, i):
    return self.header_override_[i]

  def add_header_override(self):
    x = TaskQueueHttpHeader()
    self.header_override_.append(x)
    return x

  def clear_header_override(self):
    self.header_override_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_queue_name()): self.set_queue_name(x.queue_name())
    if (x.has_bucket_refill_per_second()): self.set_bucket_refill_per_second(x.bucket_refill_per_second())
    if (x.has_bucket_capacity()): self.set_bucket_capacity(x.bucket_capacity())
    if (x.has_user_specified_rate()): self.set_user_specified_rate(x.user_specified_rate())
    if (x.has_retry_parameters()): self.mutable_retry_parameters().MergeFrom(x.retry_parameters())
    if (x.has_max_concurrent_requests()): self.set_max_concurrent_requests(x.max_concurrent_requests())
    if (x.has_mode()): self.set_mode(x.mode())
    if (x.has_acl()): self.mutable_acl().MergeFrom(x.acl())
    for i in xrange(x.header_override_size()): self.add_header_override().CopyFrom(x.header_override(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_queue_name_ != x.has_queue_name_: return 0
    if self.has_queue_name_ and self.queue_name_ != x.queue_name_: return 0
    if self.has_bucket_refill_per_second_ != x.has_bucket_refill_per_second_: return 0
    if self.has_bucket_refill_per_second_ and self.bucket_refill_per_second_ != x.bucket_refill_per_second_: return 0
    if self.has_bucket_capacity_ != x.has_bucket_capacity_: return 0
    if self.has_bucket_capacity_ and self.bucket_capacity_ != x.bucket_capacity_: return 0
    if self.has_user_specified_rate_ != x.has_user_specified_rate_: return 0
    if self.has_user_specified_rate_ and self.user_specified_rate_ != x.user_specified_rate_: return 0
    if self.has_retry_parameters_ != x.has_retry_parameters_: return 0
    if self.has_retry_parameters_ and self.retry_parameters_ != x.retry_parameters_: return 0
    if self.has_max_concurrent_requests_ != x.has_max_concurrent_requests_: return 0
    if self.has_max_concurrent_requests_ and self.max_concurrent_requests_ != x.max_concurrent_requests_: return 0
    if self.has_mode_ != x.has_mode_: return 0
    if self.has_mode_ and self.mode_ != x.mode_: return 0
    if self.has_acl_ != x.has_acl_: return 0
    if self.has_acl_ and self.acl_ != x.acl_: return 0
    if len(self.header_override_) != len(x.header_override_): return 0
    for e1, e2 in zip(self.header_override_, x.header_override_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_queue_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: queue_name not set.')
    if (not self.has_bucket_refill_per_second_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: bucket_refill_per_second not set.')
    if (not self.has_bucket_capacity_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: bucket_capacity not set.')
    if (self.has_retry_parameters_ and not self.retry_parameters_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_acl_ and not self.acl_.IsInitialized(debug_strs)): initialized = 0
    for p in self.header_override_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    n += self.lengthString(len(self.queue_name_))
    n += self.lengthVarInt64(self.bucket_capacity_)
    if (self.has_user_specified_rate_): n += 1 + self.lengthString(len(self.user_specified_rate_))
    if (self.has_retry_parameters_): n += 1 + self.lengthString(self.retry_parameters_.ByteSize())
    if (self.has_max_concurrent_requests_): n += 1 + self.lengthVarInt64(self.max_concurrent_requests_)
    if (self.has_mode_): n += 1 + self.lengthVarInt64(self.mode_)
    if (self.has_acl_): n += 1 + self.lengthString(self.acl_.ByteSize())
    n += 1 * len(self.header_override_)
    for i in xrange(len(self.header_override_)): n += self.lengthString(self.header_override_[i].ByteSize())
    return n + 11

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    if (self.has_queue_name_):
      n += 1
      n += self.lengthString(len(self.queue_name_))
    if (self.has_bucket_refill_per_second_):
      n += 9
    if (self.has_bucket_capacity_):
      n += 1
      n += self.lengthVarInt64(self.bucket_capacity_)
    if (self.has_user_specified_rate_): n += 1 + self.lengthString(len(self.user_specified_rate_))
    if (self.has_retry_parameters_): n += 1 + self.lengthString(self.retry_parameters_.ByteSizePartial())
    if (self.has_max_concurrent_requests_): n += 1 + self.lengthVarInt64(self.max_concurrent_requests_)
    if (self.has_mode_): n += 1 + self.lengthVarInt64(self.mode_)
    if (self.has_acl_): n += 1 + self.lengthString(self.acl_.ByteSizePartial())
    n += 1 * len(self.header_override_)
    for i in xrange(len(self.header_override_)): n += self.lengthString(self.header_override_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_queue_name()
    self.clear_bucket_refill_per_second()
    self.clear_bucket_capacity()
    self.clear_user_specified_rate()
    self.clear_retry_parameters()
    self.clear_max_concurrent_requests()
    self.clear_mode()
    self.clear_acl()
    self.clear_header_override()

  def OutputUnchecked(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    out.putVarInt32(18)
    out.putPrefixedString(self.queue_name_)
    out.putVarInt32(25)
    out.putDouble(self.bucket_refill_per_second_)
    out.putVarInt32(32)
    out.putVarInt32(self.bucket_capacity_)
    if (self.has_user_specified_rate_):
      out.putVarInt32(42)
      out.putPrefixedString(self.user_specified_rate_)
    if (self.has_retry_parameters_):
      out.putVarInt32(50)
      out.putVarInt32(self.retry_parameters_.ByteSize())
      self.retry_parameters_.OutputUnchecked(out)
    if (self.has_max_concurrent_requests_):
      out.putVarInt32(56)
      out.putVarInt32(self.max_concurrent_requests_)
    if (self.has_mode_):
      out.putVarInt32(64)
      out.putVarInt32(self.mode_)
    if (self.has_acl_):
      out.putVarInt32(74)
      out.putVarInt32(self.acl_.ByteSize())
      self.acl_.OutputUnchecked(out)
    for i in xrange(len(self.header_override_)):
      out.putVarInt32(82)
      out.putVarInt32(self.header_override_[i].ByteSize())
      self.header_override_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    if (self.has_queue_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.queue_name_)
    if (self.has_bucket_refill_per_second_):
      out.putVarInt32(25)
      out.putDouble(self.bucket_refill_per_second_)
    if (self.has_bucket_capacity_):
      out.putVarInt32(32)
      out.putVarInt32(self.bucket_capacity_)
    if (self.has_user_specified_rate_):
      out.putVarInt32(42)
      out.putPrefixedString(self.user_specified_rate_)
    if (self.has_retry_parameters_):
      out.putVarInt32(50)
      out.putVarInt32(self.retry_parameters_.ByteSizePartial())
      self.retry_parameters_.OutputPartial(out)
    if (self.has_max_concurrent_requests_):
      out.putVarInt32(56)
      out.putVarInt32(self.max_concurrent_requests_)
    if (self.has_mode_):
      out.putVarInt32(64)
      out.putVarInt32(self.mode_)
    if (self.has_acl_):
      out.putVarInt32(74)
      out.putVarInt32(self.acl_.ByteSizePartial())
      self.acl_.OutputPartial(out)
    for i in xrange(len(self.header_override_)):
      out.putVarInt32(82)
      out.putVarInt32(self.header_override_[i].ByteSizePartial())
      self.header_override_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_queue_name(d.getPrefixedString())
        continue
      if tt == 25:
        self.set_bucket_refill_per_second(d.getDouble())
        continue
      if tt == 32:
        self.set_bucket_capacity(d.getVarInt32())
        continue
      if tt == 42:
        self.set_user_specified_rate(d.getPrefixedString())
        continue
      if tt == 50:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_retry_parameters().TryMerge(tmp)
        continue
      if tt == 56:
        self.set_max_concurrent_requests(d.getVarInt32())
        continue
      if tt == 64:
        self.set_mode(d.getVarInt32())
        continue
      if tt == 74:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_acl().TryMerge(tmp)
        continue
      if tt == 82:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_header_override().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_queue_name_: res+=prefix+("queue_name: %s\n" % self.DebugFormatString(self.queue_name_))
    if self.has_bucket_refill_per_second_: res+=prefix+("bucket_refill_per_second: %s\n" % self.DebugFormat(self.bucket_refill_per_second_))
    if self.has_bucket_capacity_: res+=prefix+("bucket_capacity: %s\n" % self.DebugFormatInt32(self.bucket_capacity_))
    if self.has_user_specified_rate_: res+=prefix+("user_specified_rate: %s\n" % self.DebugFormatString(self.user_specified_rate_))
    if self.has_retry_parameters_:
      res+=prefix+"retry_parameters <\n"
      res+=self.retry_parameters_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_max_concurrent_requests_: res+=prefix+("max_concurrent_requests: %s\n" % self.DebugFormatInt32(self.max_concurrent_requests_))
    if self.has_mode_: res+=prefix+("mode: %s\n" % self.DebugFormatInt32(self.mode_))
    if self.has_acl_:
      res+=prefix+"acl <\n"
      res+=self.acl_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.header_override_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("header_override%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  kqueue_name = 2
  kbucket_refill_per_second = 3
  kbucket_capacity = 4
  kuser_specified_rate = 5
  kretry_parameters = 6
  kmax_concurrent_requests = 7
  kmode = 8
  kacl = 9
  kheader_override = 10

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "queue_name",
    3: "bucket_refill_per_second",
    4: "bucket_capacity",
    5: "user_specified_rate",
    6: "retry_parameters",
    7: "max_concurrent_requests",
    8: "mode",
    9: "acl",
    10: "header_override",
  }, 10)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.DOUBLE,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.STRING,
    7: ProtocolBuffer.Encoder.NUMERIC,
    8: ProtocolBuffer.Encoder.NUMERIC,
    9: ProtocolBuffer.Encoder.STRING,
    10: ProtocolBuffer.Encoder.STRING,
  }, 10, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueUpdateQueueRequest'
class TaskQueueUpdateQueueResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueUpdateQueueResponse'
class TaskQueueFetchQueuesRequest(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_max_rows_ = 0
  max_rows_ = 0

  def __init__(self, contents=None):
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

  def max_rows(self): return self.max_rows_

  def set_max_rows(self, x):
    self.has_max_rows_ = 1
    self.max_rows_ = x

  def clear_max_rows(self):
    if self.has_max_rows_:
      self.has_max_rows_ = 0
      self.max_rows_ = 0

  def has_max_rows(self): return self.has_max_rows_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_max_rows()): self.set_max_rows(x.max_rows())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_max_rows_ != x.has_max_rows_: return 0
    if self.has_max_rows_ and self.max_rows_ != x.max_rows_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_max_rows_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: max_rows not set.')
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    n += self.lengthVarInt64(self.max_rows_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    if (self.has_max_rows_):
      n += 1
      n += self.lengthVarInt64(self.max_rows_)
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_max_rows()

  def OutputUnchecked(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    out.putVarInt32(16)
    out.putVarInt32(self.max_rows_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    if (self.has_max_rows_):
      out.putVarInt32(16)
      out.putVarInt32(self.max_rows_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_max_rows(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_max_rows_: res+=prefix+("max_rows: %s\n" % self.DebugFormatInt32(self.max_rows_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  kmax_rows = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "max_rows",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueFetchQueuesRequest'
class TaskQueueFetchQueuesResponse_Queue(ProtocolBuffer.ProtocolMessage):
  has_queue_name_ = 0
  queue_name_ = ""
  has_bucket_refill_per_second_ = 0
  bucket_refill_per_second_ = 0.0
  has_bucket_capacity_ = 0
  bucket_capacity_ = 0.0
  has_user_specified_rate_ = 0
  user_specified_rate_ = ""
  has_paused_ = 0
  paused_ = 0
  has_retry_parameters_ = 0
  retry_parameters_ = None
  has_max_concurrent_requests_ = 0
  max_concurrent_requests_ = 0
  has_mode_ = 0
  mode_ = 0
  has_acl_ = 0
  acl_ = None
  has_creator_name_ = 0
  creator_name_ = "apphosting"

  def __init__(self, contents=None):
    self.header_override_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def queue_name(self): return self.queue_name_

  def set_queue_name(self, x):
    self.has_queue_name_ = 1
    self.queue_name_ = x

  def clear_queue_name(self):
    if self.has_queue_name_:
      self.has_queue_name_ = 0
      self.queue_name_ = ""

  def has_queue_name(self): return self.has_queue_name_

  def bucket_refill_per_second(self): return self.bucket_refill_per_second_

  def set_bucket_refill_per_second(self, x):
    self.has_bucket_refill_per_second_ = 1
    self.bucket_refill_per_second_ = x

  def clear_bucket_refill_per_second(self):
    if self.has_bucket_refill_per_second_:
      self.has_bucket_refill_per_second_ = 0
      self.bucket_refill_per_second_ = 0.0

  def has_bucket_refill_per_second(self): return self.has_bucket_refill_per_second_

  def bucket_capacity(self): return self.bucket_capacity_

  def set_bucket_capacity(self, x):
    self.has_bucket_capacity_ = 1
    self.bucket_capacity_ = x

  def clear_bucket_capacity(self):
    if self.has_bucket_capacity_:
      self.has_bucket_capacity_ = 0
      self.bucket_capacity_ = 0.0

  def has_bucket_capacity(self): return self.has_bucket_capacity_

  def user_specified_rate(self): return self.user_specified_rate_

  def set_user_specified_rate(self, x):
    self.has_user_specified_rate_ = 1
    self.user_specified_rate_ = x

  def clear_user_specified_rate(self):
    if self.has_user_specified_rate_:
      self.has_user_specified_rate_ = 0
      self.user_specified_rate_ = ""

  def has_user_specified_rate(self): return self.has_user_specified_rate_

  def paused(self): return self.paused_

  def set_paused(self, x):
    self.has_paused_ = 1
    self.paused_ = x

  def clear_paused(self):
    if self.has_paused_:
      self.has_paused_ = 0
      self.paused_ = 0

  def has_paused(self): return self.has_paused_

  def retry_parameters(self):
    if self.retry_parameters_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.retry_parameters_ is None: self.retry_parameters_ = TaskQueueRetryParameters()
      finally:
        self.lazy_init_lock_.release()
    return self.retry_parameters_

  def mutable_retry_parameters(self): self.has_retry_parameters_ = 1; return self.retry_parameters()

  def clear_retry_parameters(self):

    if self.has_retry_parameters_:
      self.has_retry_parameters_ = 0;
      if self.retry_parameters_ is not None: self.retry_parameters_.Clear()

  def has_retry_parameters(self): return self.has_retry_parameters_

  def max_concurrent_requests(self): return self.max_concurrent_requests_

  def set_max_concurrent_requests(self, x):
    self.has_max_concurrent_requests_ = 1
    self.max_concurrent_requests_ = x

  def clear_max_concurrent_requests(self):
    if self.has_max_concurrent_requests_:
      self.has_max_concurrent_requests_ = 0
      self.max_concurrent_requests_ = 0

  def has_max_concurrent_requests(self): return self.has_max_concurrent_requests_

  def mode(self): return self.mode_

  def set_mode(self, x):
    self.has_mode_ = 1
    self.mode_ = x

  def clear_mode(self):
    if self.has_mode_:
      self.has_mode_ = 0
      self.mode_ = 0

  def has_mode(self): return self.has_mode_

  def acl(self):
    if self.acl_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.acl_ is None: self.acl_ = TaskQueueAcl()
      finally:
        self.lazy_init_lock_.release()
    return self.acl_

  def mutable_acl(self): self.has_acl_ = 1; return self.acl()

  def clear_acl(self):

    if self.has_acl_:
      self.has_acl_ = 0;
      if self.acl_ is not None: self.acl_.Clear()

  def has_acl(self): return self.has_acl_

  def header_override_size(self): return len(self.header_override_)
  def header_override_list(self): return self.header_override_

  def header_override(self, i):
    return self.header_override_[i]

  def mutable_header_override(self, i):
    return self.header_override_[i]

  def add_header_override(self):
    x = TaskQueueHttpHeader()
    self.header_override_.append(x)
    return x

  def clear_header_override(self):
    self.header_override_ = []
  def creator_name(self): return self.creator_name_

  def set_creator_name(self, x):
    self.has_creator_name_ = 1
    self.creator_name_ = x

  def clear_creator_name(self):
    if self.has_creator_name_:
      self.has_creator_name_ = 0
      self.creator_name_ = "apphosting"

  def has_creator_name(self): return self.has_creator_name_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_queue_name()): self.set_queue_name(x.queue_name())
    if (x.has_bucket_refill_per_second()): self.set_bucket_refill_per_second(x.bucket_refill_per_second())
    if (x.has_bucket_capacity()): self.set_bucket_capacity(x.bucket_capacity())
    if (x.has_user_specified_rate()): self.set_user_specified_rate(x.user_specified_rate())
    if (x.has_paused()): self.set_paused(x.paused())
    if (x.has_retry_parameters()): self.mutable_retry_parameters().MergeFrom(x.retry_parameters())
    if (x.has_max_concurrent_requests()): self.set_max_concurrent_requests(x.max_concurrent_requests())
    if (x.has_mode()): self.set_mode(x.mode())
    if (x.has_acl()): self.mutable_acl().MergeFrom(x.acl())
    for i in xrange(x.header_override_size()): self.add_header_override().CopyFrom(x.header_override(i))
    if (x.has_creator_name()): self.set_creator_name(x.creator_name())

  def Equals(self, x):
    if x is self: return 1
    if self.has_queue_name_ != x.has_queue_name_: return 0
    if self.has_queue_name_ and self.queue_name_ != x.queue_name_: return 0
    if self.has_bucket_refill_per_second_ != x.has_bucket_refill_per_second_: return 0
    if self.has_bucket_refill_per_second_ and self.bucket_refill_per_second_ != x.bucket_refill_per_second_: return 0
    if self.has_bucket_capacity_ != x.has_bucket_capacity_: return 0
    if self.has_bucket_capacity_ and self.bucket_capacity_ != x.bucket_capacity_: return 0
    if self.has_user_specified_rate_ != x.has_user_specified_rate_: return 0
    if self.has_user_specified_rate_ and self.user_specified_rate_ != x.user_specified_rate_: return 0
    if self.has_paused_ != x.has_paused_: return 0
    if self.has_paused_ and self.paused_ != x.paused_: return 0
    if self.has_retry_parameters_ != x.has_retry_parameters_: return 0
    if self.has_retry_parameters_ and self.retry_parameters_ != x.retry_parameters_: return 0
    if self.has_max_concurrent_requests_ != x.has_max_concurrent_requests_: return 0
    if self.has_max_concurrent_requests_ and self.max_concurrent_requests_ != x.max_concurrent_requests_: return 0
    if self.has_mode_ != x.has_mode_: return 0
    if self.has_mode_ and self.mode_ != x.mode_: return 0
    if self.has_acl_ != x.has_acl_: return 0
    if self.has_acl_ and self.acl_ != x.acl_: return 0
    if len(self.header_override_) != len(x.header_override_): return 0
    for e1, e2 in zip(self.header_override_, x.header_override_):
      if e1 != e2: return 0
    if self.has_creator_name_ != x.has_creator_name_: return 0
    if self.has_creator_name_ and self.creator_name_ != x.creator_name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_queue_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: queue_name not set.')
    if (not self.has_bucket_refill_per_second_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: bucket_refill_per_second not set.')
    if (not self.has_bucket_capacity_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: bucket_capacity not set.')
    if (not self.has_paused_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: paused not set.')
    if (self.has_retry_parameters_ and not self.retry_parameters_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_acl_ and not self.acl_.IsInitialized(debug_strs)): initialized = 0
    for p in self.header_override_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.queue_name_))
    if (self.has_user_specified_rate_): n += 1 + self.lengthString(len(self.user_specified_rate_))
    if (self.has_retry_parameters_): n += 1 + self.lengthString(self.retry_parameters_.ByteSize())
    if (self.has_max_concurrent_requests_): n += 1 + self.lengthVarInt64(self.max_concurrent_requests_)
    if (self.has_mode_): n += 1 + self.lengthVarInt64(self.mode_)
    if (self.has_acl_): n += 1 + self.lengthString(self.acl_.ByteSize())
    n += 1 * len(self.header_override_)
    for i in xrange(len(self.header_override_)): n += self.lengthString(self.header_override_[i].ByteSize())
    if (self.has_creator_name_): n += 1 + self.lengthString(len(self.creator_name_))
    return n + 21

  def ByteSizePartial(self):
    n = 0
    if (self.has_queue_name_):
      n += 1
      n += self.lengthString(len(self.queue_name_))
    if (self.has_bucket_refill_per_second_):
      n += 9
    if (self.has_bucket_capacity_):
      n += 9
    if (self.has_user_specified_rate_): n += 1 + self.lengthString(len(self.user_specified_rate_))
    if (self.has_paused_):
      n += 2
    if (self.has_retry_parameters_): n += 1 + self.lengthString(self.retry_parameters_.ByteSizePartial())
    if (self.has_max_concurrent_requests_): n += 1 + self.lengthVarInt64(self.max_concurrent_requests_)
    if (self.has_mode_): n += 1 + self.lengthVarInt64(self.mode_)
    if (self.has_acl_): n += 1 + self.lengthString(self.acl_.ByteSizePartial())
    n += 1 * len(self.header_override_)
    for i in xrange(len(self.header_override_)): n += self.lengthString(self.header_override_[i].ByteSizePartial())
    if (self.has_creator_name_): n += 1 + self.lengthString(len(self.creator_name_))
    return n

  def Clear(self):
    self.clear_queue_name()
    self.clear_bucket_refill_per_second()
    self.clear_bucket_capacity()
    self.clear_user_specified_rate()
    self.clear_paused()
    self.clear_retry_parameters()
    self.clear_max_concurrent_requests()
    self.clear_mode()
    self.clear_acl()
    self.clear_header_override()
    self.clear_creator_name()

  def OutputUnchecked(self, out):
    out.putVarInt32(18)
    out.putPrefixedString(self.queue_name_)
    out.putVarInt32(25)
    out.putDouble(self.bucket_refill_per_second_)
    out.putVarInt32(33)
    out.putDouble(self.bucket_capacity_)
    if (self.has_user_specified_rate_):
      out.putVarInt32(42)
      out.putPrefixedString(self.user_specified_rate_)
    out.putVarInt32(48)
    out.putBoolean(self.paused_)
    if (self.has_retry_parameters_):
      out.putVarInt32(58)
      out.putVarInt32(self.retry_parameters_.ByteSize())
      self.retry_parameters_.OutputUnchecked(out)
    if (self.has_max_concurrent_requests_):
      out.putVarInt32(64)
      out.putVarInt32(self.max_concurrent_requests_)
    if (self.has_mode_):
      out.putVarInt32(72)
      out.putVarInt32(self.mode_)
    if (self.has_acl_):
      out.putVarInt32(82)
      out.putVarInt32(self.acl_.ByteSize())
      self.acl_.OutputUnchecked(out)
    for i in xrange(len(self.header_override_)):
      out.putVarInt32(90)
      out.putVarInt32(self.header_override_[i].ByteSize())
      self.header_override_[i].OutputUnchecked(out)
    if (self.has_creator_name_):
      out.putVarInt32(98)
      out.putPrefixedString(self.creator_name_)

  def OutputPartial(self, out):
    if (self.has_queue_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.queue_name_)
    if (self.has_bucket_refill_per_second_):
      out.putVarInt32(25)
      out.putDouble(self.bucket_refill_per_second_)
    if (self.has_bucket_capacity_):
      out.putVarInt32(33)
      out.putDouble(self.bucket_capacity_)
    if (self.has_user_specified_rate_):
      out.putVarInt32(42)
      out.putPrefixedString(self.user_specified_rate_)
    if (self.has_paused_):
      out.putVarInt32(48)
      out.putBoolean(self.paused_)
    if (self.has_retry_parameters_):
      out.putVarInt32(58)
      out.putVarInt32(self.retry_parameters_.ByteSizePartial())
      self.retry_parameters_.OutputPartial(out)
    if (self.has_max_concurrent_requests_):
      out.putVarInt32(64)
      out.putVarInt32(self.max_concurrent_requests_)
    if (self.has_mode_):
      out.putVarInt32(72)
      out.putVarInt32(self.mode_)
    if (self.has_acl_):
      out.putVarInt32(82)
      out.putVarInt32(self.acl_.ByteSizePartial())
      self.acl_.OutputPartial(out)
    for i in xrange(len(self.header_override_)):
      out.putVarInt32(90)
      out.putVarInt32(self.header_override_[i].ByteSizePartial())
      self.header_override_[i].OutputPartial(out)
    if (self.has_creator_name_):
      out.putVarInt32(98)
      out.putPrefixedString(self.creator_name_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 12: break
      if tt == 18:
        self.set_queue_name(d.getPrefixedString())
        continue
      if tt == 25:
        self.set_bucket_refill_per_second(d.getDouble())
        continue
      if tt == 33:
        self.set_bucket_capacity(d.getDouble())
        continue
      if tt == 42:
        self.set_user_specified_rate(d.getPrefixedString())
        continue
      if tt == 48:
        self.set_paused(d.getBoolean())
        continue
      if tt == 58:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_retry_parameters().TryMerge(tmp)
        continue
      if tt == 64:
        self.set_max_concurrent_requests(d.getVarInt32())
        continue
      if tt == 72:
        self.set_mode(d.getVarInt32())
        continue
      if tt == 82:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_acl().TryMerge(tmp)
        continue
      if tt == 90:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_header_override().TryMerge(tmp)
        continue
      if tt == 98:
        self.set_creator_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_queue_name_: res+=prefix+("queue_name: %s\n" % self.DebugFormatString(self.queue_name_))
    if self.has_bucket_refill_per_second_: res+=prefix+("bucket_refill_per_second: %s\n" % self.DebugFormat(self.bucket_refill_per_second_))
    if self.has_bucket_capacity_: res+=prefix+("bucket_capacity: %s\n" % self.DebugFormat(self.bucket_capacity_))
    if self.has_user_specified_rate_: res+=prefix+("user_specified_rate: %s\n" % self.DebugFormatString(self.user_specified_rate_))
    if self.has_paused_: res+=prefix+("paused: %s\n" % self.DebugFormatBool(self.paused_))
    if self.has_retry_parameters_:
      res+=prefix+"retry_parameters <\n"
      res+=self.retry_parameters_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_max_concurrent_requests_: res+=prefix+("max_concurrent_requests: %s\n" % self.DebugFormatInt32(self.max_concurrent_requests_))
    if self.has_mode_: res+=prefix+("mode: %s\n" % self.DebugFormatInt32(self.mode_))
    if self.has_acl_:
      res+=prefix+"acl <\n"
      res+=self.acl_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.header_override_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("header_override%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_creator_name_: res+=prefix+("creator_name: %s\n" % self.DebugFormatString(self.creator_name_))
    return res

class TaskQueueFetchQueuesResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.queue_ = []
    if contents is not None: self.MergeFromString(contents)

  def queue_size(self): return len(self.queue_)
  def queue_list(self): return self.queue_

  def queue(self, i):
    return self.queue_[i]

  def mutable_queue(self, i):
    return self.queue_[i]

  def add_queue(self):
    x = TaskQueueFetchQueuesResponse_Queue()
    self.queue_.append(x)
    return x

  def clear_queue(self):
    self.queue_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.queue_size()): self.add_queue().CopyFrom(x.queue(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.queue_) != len(x.queue_): return 0
    for e1, e2 in zip(self.queue_, x.queue_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.queue_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 2 * len(self.queue_)
    for i in xrange(len(self.queue_)): n += self.queue_[i].ByteSize()
    return n

  def ByteSizePartial(self):
    n = 0
    n += 2 * len(self.queue_)
    for i in xrange(len(self.queue_)): n += self.queue_[i].ByteSizePartial()
    return n

  def Clear(self):
    self.clear_queue()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.queue_)):
      out.putVarInt32(11)
      self.queue_[i].OutputUnchecked(out)
      out.putVarInt32(12)

  def OutputPartial(self, out):
    for i in xrange(len(self.queue_)):
      out.putVarInt32(11)
      self.queue_[i].OutputPartial(out)
      out.putVarInt32(12)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 11:
        self.add_queue().TryMerge(d)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.queue_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Queue%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kQueueGroup = 1
  kQueuequeue_name = 2
  kQueuebucket_refill_per_second = 3
  kQueuebucket_capacity = 4
  kQueueuser_specified_rate = 5
  kQueuepaused = 6
  kQueueretry_parameters = 7
  kQueuemax_concurrent_requests = 8
  kQueuemode = 9
  kQueueacl = 10
  kQueueheader_override = 11
  kQueuecreator_name = 12

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "Queue",
    2: "queue_name",
    3: "bucket_refill_per_second",
    4: "bucket_capacity",
    5: "user_specified_rate",
    6: "paused",
    7: "retry_parameters",
    8: "max_concurrent_requests",
    9: "mode",
    10: "acl",
    11: "header_override",
    12: "creator_name",
  }, 12)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STARTGROUP,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.DOUBLE,
    4: ProtocolBuffer.Encoder.DOUBLE,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.NUMERIC,
    7: ProtocolBuffer.Encoder.STRING,
    8: ProtocolBuffer.Encoder.NUMERIC,
    9: ProtocolBuffer.Encoder.NUMERIC,
    10: ProtocolBuffer.Encoder.STRING,
    11: ProtocolBuffer.Encoder.STRING,
    12: ProtocolBuffer.Encoder.STRING,
  }, 12, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueFetchQueuesResponse'
class TaskQueueFetchQueueStatsRequest(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_max_num_tasks_ = 0
  max_num_tasks_ = 0

  def __init__(self, contents=None):
    self.queue_name_ = []
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

  def queue_name_size(self): return len(self.queue_name_)
  def queue_name_list(self): return self.queue_name_

  def queue_name(self, i):
    return self.queue_name_[i]

  def set_queue_name(self, i, x):
    self.queue_name_[i] = x

  def add_queue_name(self, x):
    self.queue_name_.append(x)

  def clear_queue_name(self):
    self.queue_name_ = []

  def max_num_tasks(self): return self.max_num_tasks_

  def set_max_num_tasks(self, x):
    self.has_max_num_tasks_ = 1
    self.max_num_tasks_ = x

  def clear_max_num_tasks(self):
    if self.has_max_num_tasks_:
      self.has_max_num_tasks_ = 0
      self.max_num_tasks_ = 0

  def has_max_num_tasks(self): return self.has_max_num_tasks_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    for i in xrange(x.queue_name_size()): self.add_queue_name(x.queue_name(i))
    if (x.has_max_num_tasks()): self.set_max_num_tasks(x.max_num_tasks())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if len(self.queue_name_) != len(x.queue_name_): return 0
    for e1, e2 in zip(self.queue_name_, x.queue_name_):
      if e1 != e2: return 0
    if self.has_max_num_tasks_ != x.has_max_num_tasks_: return 0
    if self.has_max_num_tasks_ and self.max_num_tasks_ != x.max_num_tasks_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    n += 1 * len(self.queue_name_)
    for i in xrange(len(self.queue_name_)): n += self.lengthString(len(self.queue_name_[i]))
    if (self.has_max_num_tasks_): n += 1 + self.lengthVarInt64(self.max_num_tasks_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    n += 1 * len(self.queue_name_)
    for i in xrange(len(self.queue_name_)): n += self.lengthString(len(self.queue_name_[i]))
    if (self.has_max_num_tasks_): n += 1 + self.lengthVarInt64(self.max_num_tasks_)
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_queue_name()
    self.clear_max_num_tasks()

  def OutputUnchecked(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    for i in xrange(len(self.queue_name_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.queue_name_[i])
    if (self.has_max_num_tasks_):
      out.putVarInt32(24)
      out.putVarInt32(self.max_num_tasks_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    for i in xrange(len(self.queue_name_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.queue_name_[i])
    if (self.has_max_num_tasks_):
      out.putVarInt32(24)
      out.putVarInt32(self.max_num_tasks_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.add_queue_name(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_max_num_tasks(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    cnt=0
    for e in self.queue_name_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("queue_name%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_max_num_tasks_: res+=prefix+("max_num_tasks: %s\n" % self.DebugFormatInt32(self.max_num_tasks_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  kqueue_name = 2
  kmax_num_tasks = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "queue_name",
    3: "max_num_tasks",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueFetchQueueStatsRequest'
class TaskQueueScannerQueueInfo(ProtocolBuffer.ProtocolMessage):
  has_executed_last_minute_ = 0
  executed_last_minute_ = 0
  has_executed_last_hour_ = 0
  executed_last_hour_ = 0
  has_sampling_duration_seconds_ = 0
  sampling_duration_seconds_ = 0.0
  has_requests_in_flight_ = 0
  requests_in_flight_ = 0
  has_enforced_rate_ = 0
  enforced_rate_ = 0.0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def executed_last_minute(self): return self.executed_last_minute_

  def set_executed_last_minute(self, x):
    self.has_executed_last_minute_ = 1
    self.executed_last_minute_ = x

  def clear_executed_last_minute(self):
    if self.has_executed_last_minute_:
      self.has_executed_last_minute_ = 0
      self.executed_last_minute_ = 0

  def has_executed_last_minute(self): return self.has_executed_last_minute_

  def executed_last_hour(self): return self.executed_last_hour_

  def set_executed_last_hour(self, x):
    self.has_executed_last_hour_ = 1
    self.executed_last_hour_ = x

  def clear_executed_last_hour(self):
    if self.has_executed_last_hour_:
      self.has_executed_last_hour_ = 0
      self.executed_last_hour_ = 0

  def has_executed_last_hour(self): return self.has_executed_last_hour_

  def sampling_duration_seconds(self): return self.sampling_duration_seconds_

  def set_sampling_duration_seconds(self, x):
    self.has_sampling_duration_seconds_ = 1
    self.sampling_duration_seconds_ = x

  def clear_sampling_duration_seconds(self):
    if self.has_sampling_duration_seconds_:
      self.has_sampling_duration_seconds_ = 0
      self.sampling_duration_seconds_ = 0.0

  def has_sampling_duration_seconds(self): return self.has_sampling_duration_seconds_

  def requests_in_flight(self): return self.requests_in_flight_

  def set_requests_in_flight(self, x):
    self.has_requests_in_flight_ = 1
    self.requests_in_flight_ = x

  def clear_requests_in_flight(self):
    if self.has_requests_in_flight_:
      self.has_requests_in_flight_ = 0
      self.requests_in_flight_ = 0

  def has_requests_in_flight(self): return self.has_requests_in_flight_

  def enforced_rate(self): return self.enforced_rate_

  def set_enforced_rate(self, x):
    self.has_enforced_rate_ = 1
    self.enforced_rate_ = x

  def clear_enforced_rate(self):
    if self.has_enforced_rate_:
      self.has_enforced_rate_ = 0
      self.enforced_rate_ = 0.0

  def has_enforced_rate(self): return self.has_enforced_rate_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_executed_last_minute()): self.set_executed_last_minute(x.executed_last_minute())
    if (x.has_executed_last_hour()): self.set_executed_last_hour(x.executed_last_hour())
    if (x.has_sampling_duration_seconds()): self.set_sampling_duration_seconds(x.sampling_duration_seconds())
    if (x.has_requests_in_flight()): self.set_requests_in_flight(x.requests_in_flight())
    if (x.has_enforced_rate()): self.set_enforced_rate(x.enforced_rate())

  def Equals(self, x):
    if x is self: return 1
    if self.has_executed_last_minute_ != x.has_executed_last_minute_: return 0
    if self.has_executed_last_minute_ and self.executed_last_minute_ != x.executed_last_minute_: return 0
    if self.has_executed_last_hour_ != x.has_executed_last_hour_: return 0
    if self.has_executed_last_hour_ and self.executed_last_hour_ != x.executed_last_hour_: return 0
    if self.has_sampling_duration_seconds_ != x.has_sampling_duration_seconds_: return 0
    if self.has_sampling_duration_seconds_ and self.sampling_duration_seconds_ != x.sampling_duration_seconds_: return 0
    if self.has_requests_in_flight_ != x.has_requests_in_flight_: return 0
    if self.has_requests_in_flight_ and self.requests_in_flight_ != x.requests_in_flight_: return 0
    if self.has_enforced_rate_ != x.has_enforced_rate_: return 0
    if self.has_enforced_rate_ and self.enforced_rate_ != x.enforced_rate_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_executed_last_minute_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: executed_last_minute not set.')
    if (not self.has_executed_last_hour_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: executed_last_hour not set.')
    if (not self.has_sampling_duration_seconds_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: sampling_duration_seconds not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.executed_last_minute_)
    n += self.lengthVarInt64(self.executed_last_hour_)
    if (self.has_requests_in_flight_): n += 1 + self.lengthVarInt64(self.requests_in_flight_)
    if (self.has_enforced_rate_): n += 9
    return n + 11

  def ByteSizePartial(self):
    n = 0
    if (self.has_executed_last_minute_):
      n += 1
      n += self.lengthVarInt64(self.executed_last_minute_)
    if (self.has_executed_last_hour_):
      n += 1
      n += self.lengthVarInt64(self.executed_last_hour_)
    if (self.has_sampling_duration_seconds_):
      n += 9
    if (self.has_requests_in_flight_): n += 1 + self.lengthVarInt64(self.requests_in_flight_)
    if (self.has_enforced_rate_): n += 9
    return n

  def Clear(self):
    self.clear_executed_last_minute()
    self.clear_executed_last_hour()
    self.clear_sampling_duration_seconds()
    self.clear_requests_in_flight()
    self.clear_enforced_rate()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt64(self.executed_last_minute_)
    out.putVarInt32(16)
    out.putVarInt64(self.executed_last_hour_)
    out.putVarInt32(25)
    out.putDouble(self.sampling_duration_seconds_)
    if (self.has_requests_in_flight_):
      out.putVarInt32(32)
      out.putVarInt32(self.requests_in_flight_)
    if (self.has_enforced_rate_):
      out.putVarInt32(41)
      out.putDouble(self.enforced_rate_)

  def OutputPartial(self, out):
    if (self.has_executed_last_minute_):
      out.putVarInt32(8)
      out.putVarInt64(self.executed_last_minute_)
    if (self.has_executed_last_hour_):
      out.putVarInt32(16)
      out.putVarInt64(self.executed_last_hour_)
    if (self.has_sampling_duration_seconds_):
      out.putVarInt32(25)
      out.putDouble(self.sampling_duration_seconds_)
    if (self.has_requests_in_flight_):
      out.putVarInt32(32)
      out.putVarInt32(self.requests_in_flight_)
    if (self.has_enforced_rate_):
      out.putVarInt32(41)
      out.putDouble(self.enforced_rate_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_executed_last_minute(d.getVarInt64())
        continue
      if tt == 16:
        self.set_executed_last_hour(d.getVarInt64())
        continue
      if tt == 25:
        self.set_sampling_duration_seconds(d.getDouble())
        continue
      if tt == 32:
        self.set_requests_in_flight(d.getVarInt32())
        continue
      if tt == 41:
        self.set_enforced_rate(d.getDouble())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_executed_last_minute_: res+=prefix+("executed_last_minute: %s\n" % self.DebugFormatInt64(self.executed_last_minute_))
    if self.has_executed_last_hour_: res+=prefix+("executed_last_hour: %s\n" % self.DebugFormatInt64(self.executed_last_hour_))
    if self.has_sampling_duration_seconds_: res+=prefix+("sampling_duration_seconds: %s\n" % self.DebugFormat(self.sampling_duration_seconds_))
    if self.has_requests_in_flight_: res+=prefix+("requests_in_flight: %s\n" % self.DebugFormatInt32(self.requests_in_flight_))
    if self.has_enforced_rate_: res+=prefix+("enforced_rate: %s\n" % self.DebugFormat(self.enforced_rate_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kexecuted_last_minute = 1
  kexecuted_last_hour = 2
  ksampling_duration_seconds = 3
  krequests_in_flight = 4
  kenforced_rate = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "executed_last_minute",
    2: "executed_last_hour",
    3: "sampling_duration_seconds",
    4: "requests_in_flight",
    5: "enforced_rate",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.DOUBLE,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.DOUBLE,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueScannerQueueInfo'
class TaskQueueFetchQueueStatsResponse_QueueStats(ProtocolBuffer.ProtocolMessage):
  has_num_tasks_ = 0
  num_tasks_ = 0
  has_oldest_eta_usec_ = 0
  oldest_eta_usec_ = 0
  has_scanner_info_ = 0
  scanner_info_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def num_tasks(self): return self.num_tasks_

  def set_num_tasks(self, x):
    self.has_num_tasks_ = 1
    self.num_tasks_ = x

  def clear_num_tasks(self):
    if self.has_num_tasks_:
      self.has_num_tasks_ = 0
      self.num_tasks_ = 0

  def has_num_tasks(self): return self.has_num_tasks_

  def oldest_eta_usec(self): return self.oldest_eta_usec_

  def set_oldest_eta_usec(self, x):
    self.has_oldest_eta_usec_ = 1
    self.oldest_eta_usec_ = x

  def clear_oldest_eta_usec(self):
    if self.has_oldest_eta_usec_:
      self.has_oldest_eta_usec_ = 0
      self.oldest_eta_usec_ = 0

  def has_oldest_eta_usec(self): return self.has_oldest_eta_usec_

  def scanner_info(self):
    if self.scanner_info_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.scanner_info_ is None: self.scanner_info_ = TaskQueueScannerQueueInfo()
      finally:
        self.lazy_init_lock_.release()
    return self.scanner_info_

  def mutable_scanner_info(self): self.has_scanner_info_ = 1; return self.scanner_info()

  def clear_scanner_info(self):

    if self.has_scanner_info_:
      self.has_scanner_info_ = 0;
      if self.scanner_info_ is not None: self.scanner_info_.Clear()

  def has_scanner_info(self): return self.has_scanner_info_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_num_tasks()): self.set_num_tasks(x.num_tasks())
    if (x.has_oldest_eta_usec()): self.set_oldest_eta_usec(x.oldest_eta_usec())
    if (x.has_scanner_info()): self.mutable_scanner_info().MergeFrom(x.scanner_info())

  def Equals(self, x):
    if x is self: return 1
    if self.has_num_tasks_ != x.has_num_tasks_: return 0
    if self.has_num_tasks_ and self.num_tasks_ != x.num_tasks_: return 0
    if self.has_oldest_eta_usec_ != x.has_oldest_eta_usec_: return 0
    if self.has_oldest_eta_usec_ and self.oldest_eta_usec_ != x.oldest_eta_usec_: return 0
    if self.has_scanner_info_ != x.has_scanner_info_: return 0
    if self.has_scanner_info_ and self.scanner_info_ != x.scanner_info_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_num_tasks_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: num_tasks not set.')
    if (not self.has_oldest_eta_usec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: oldest_eta_usec not set.')
    if (self.has_scanner_info_ and not self.scanner_info_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.num_tasks_)
    n += self.lengthVarInt64(self.oldest_eta_usec_)
    if (self.has_scanner_info_): n += 1 + self.lengthString(self.scanner_info_.ByteSize())
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_num_tasks_):
      n += 1
      n += self.lengthVarInt64(self.num_tasks_)
    if (self.has_oldest_eta_usec_):
      n += 1
      n += self.lengthVarInt64(self.oldest_eta_usec_)
    if (self.has_scanner_info_): n += 1 + self.lengthString(self.scanner_info_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_num_tasks()
    self.clear_oldest_eta_usec()
    self.clear_scanner_info()

  def OutputUnchecked(self, out):
    out.putVarInt32(16)
    out.putVarInt32(self.num_tasks_)
    out.putVarInt32(24)
    out.putVarInt64(self.oldest_eta_usec_)
    if (self.has_scanner_info_):
      out.putVarInt32(34)
      out.putVarInt32(self.scanner_info_.ByteSize())
      self.scanner_info_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_num_tasks_):
      out.putVarInt32(16)
      out.putVarInt32(self.num_tasks_)
    if (self.has_oldest_eta_usec_):
      out.putVarInt32(24)
      out.putVarInt64(self.oldest_eta_usec_)
    if (self.has_scanner_info_):
      out.putVarInt32(34)
      out.putVarInt32(self.scanner_info_.ByteSizePartial())
      self.scanner_info_.OutputPartial(out)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 12: break
      if tt == 16:
        self.set_num_tasks(d.getVarInt32())
        continue
      if tt == 24:
        self.set_oldest_eta_usec(d.getVarInt64())
        continue
      if tt == 34:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_scanner_info().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_num_tasks_: res+=prefix+("num_tasks: %s\n" % self.DebugFormatInt32(self.num_tasks_))
    if self.has_oldest_eta_usec_: res+=prefix+("oldest_eta_usec: %s\n" % self.DebugFormatInt64(self.oldest_eta_usec_))
    if self.has_scanner_info_:
      res+=prefix+"scanner_info <\n"
      res+=self.scanner_info_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res

class TaskQueueFetchQueueStatsResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.queuestats_ = []
    if contents is not None: self.MergeFromString(contents)

  def queuestats_size(self): return len(self.queuestats_)
  def queuestats_list(self): return self.queuestats_

  def queuestats(self, i):
    return self.queuestats_[i]

  def mutable_queuestats(self, i):
    return self.queuestats_[i]

  def add_queuestats(self):
    x = TaskQueueFetchQueueStatsResponse_QueueStats()
    self.queuestats_.append(x)
    return x

  def clear_queuestats(self):
    self.queuestats_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.queuestats_size()): self.add_queuestats().CopyFrom(x.queuestats(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.queuestats_) != len(x.queuestats_): return 0
    for e1, e2 in zip(self.queuestats_, x.queuestats_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.queuestats_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 2 * len(self.queuestats_)
    for i in xrange(len(self.queuestats_)): n += self.queuestats_[i].ByteSize()
    return n

  def ByteSizePartial(self):
    n = 0
    n += 2 * len(self.queuestats_)
    for i in xrange(len(self.queuestats_)): n += self.queuestats_[i].ByteSizePartial()
    return n

  def Clear(self):
    self.clear_queuestats()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.queuestats_)):
      out.putVarInt32(11)
      self.queuestats_[i].OutputUnchecked(out)
      out.putVarInt32(12)

  def OutputPartial(self, out):
    for i in xrange(len(self.queuestats_)):
      out.putVarInt32(11)
      self.queuestats_[i].OutputPartial(out)
      out.putVarInt32(12)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 11:
        self.add_queuestats().TryMerge(d)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.queuestats_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("QueueStats%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kQueueStatsGroup = 1
  kQueueStatsnum_tasks = 2
  kQueueStatsoldest_eta_usec = 3
  kQueueStatsscanner_info = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "QueueStats",
    2: "num_tasks",
    3: "oldest_eta_usec",
    4: "scanner_info",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STARTGROUP,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueFetchQueueStatsResponse'
class TaskQueuePauseQueueRequest(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_queue_name_ = 0
  queue_name_ = ""
  has_pause_ = 0
  pause_ = 0

  def __init__(self, contents=None):
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

  def queue_name(self): return self.queue_name_

  def set_queue_name(self, x):
    self.has_queue_name_ = 1
    self.queue_name_ = x

  def clear_queue_name(self):
    if self.has_queue_name_:
      self.has_queue_name_ = 0
      self.queue_name_ = ""

  def has_queue_name(self): return self.has_queue_name_

  def pause(self): return self.pause_

  def set_pause(self, x):
    self.has_pause_ = 1
    self.pause_ = x

  def clear_pause(self):
    if self.has_pause_:
      self.has_pause_ = 0
      self.pause_ = 0

  def has_pause(self): return self.has_pause_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_queue_name()): self.set_queue_name(x.queue_name())
    if (x.has_pause()): self.set_pause(x.pause())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_queue_name_ != x.has_queue_name_: return 0
    if self.has_queue_name_ and self.queue_name_ != x.queue_name_: return 0
    if self.has_pause_ != x.has_pause_: return 0
    if self.has_pause_ and self.pause_ != x.pause_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_app_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: app_id not set.')
    if (not self.has_queue_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: queue_name not set.')
    if (not self.has_pause_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: pause not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.app_id_))
    n += self.lengthString(len(self.queue_name_))
    return n + 4

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_):
      n += 1
      n += self.lengthString(len(self.app_id_))
    if (self.has_queue_name_):
      n += 1
      n += self.lengthString(len(self.queue_name_))
    if (self.has_pause_):
      n += 2
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_queue_name()
    self.clear_pause()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.app_id_)
    out.putVarInt32(18)
    out.putPrefixedString(self.queue_name_)
    out.putVarInt32(24)
    out.putBoolean(self.pause_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    if (self.has_queue_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.queue_name_)
    if (self.has_pause_):
      out.putVarInt32(24)
      out.putBoolean(self.pause_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_queue_name(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_pause(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_queue_name_: res+=prefix+("queue_name: %s\n" % self.DebugFormatString(self.queue_name_))
    if self.has_pause_: res+=prefix+("pause: %s\n" % self.DebugFormatBool(self.pause_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  kqueue_name = 2
  kpause = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "queue_name",
    3: "pause",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueuePauseQueueRequest'
class TaskQueuePauseQueueResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueuePauseQueueResponse'
class TaskQueuePurgeQueueRequest(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_queue_name_ = 0
  queue_name_ = ""

  def __init__(self, contents=None):
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

  def queue_name(self): return self.queue_name_

  def set_queue_name(self, x):
    self.has_queue_name_ = 1
    self.queue_name_ = x

  def clear_queue_name(self):
    if self.has_queue_name_:
      self.has_queue_name_ = 0
      self.queue_name_ = ""

  def has_queue_name(self): return self.has_queue_name_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_queue_name()): self.set_queue_name(x.queue_name())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_queue_name_ != x.has_queue_name_: return 0
    if self.has_queue_name_ and self.queue_name_ != x.queue_name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_queue_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: queue_name not set.')
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    n += self.lengthString(len(self.queue_name_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    if (self.has_queue_name_):
      n += 1
      n += self.lengthString(len(self.queue_name_))
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_queue_name()

  def OutputUnchecked(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    out.putVarInt32(18)
    out.putPrefixedString(self.queue_name_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    if (self.has_queue_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.queue_name_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_queue_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_queue_name_: res+=prefix+("queue_name: %s\n" % self.DebugFormatString(self.queue_name_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  kqueue_name = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "queue_name",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueuePurgeQueueRequest'
class TaskQueuePurgeQueueResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueuePurgeQueueResponse'
class TaskQueueDeleteQueueRequest(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_queue_name_ = 0
  queue_name_ = ""

  def __init__(self, contents=None):
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

  def queue_name(self): return self.queue_name_

  def set_queue_name(self, x):
    self.has_queue_name_ = 1
    self.queue_name_ = x

  def clear_queue_name(self):
    if self.has_queue_name_:
      self.has_queue_name_ = 0
      self.queue_name_ = ""

  def has_queue_name(self): return self.has_queue_name_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_queue_name()): self.set_queue_name(x.queue_name())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_queue_name_ != x.has_queue_name_: return 0
    if self.has_queue_name_ and self.queue_name_ != x.queue_name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_app_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: app_id not set.')
    if (not self.has_queue_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: queue_name not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.app_id_))
    n += self.lengthString(len(self.queue_name_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_):
      n += 1
      n += self.lengthString(len(self.app_id_))
    if (self.has_queue_name_):
      n += 1
      n += self.lengthString(len(self.queue_name_))
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_queue_name()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.app_id_)
    out.putVarInt32(18)
    out.putPrefixedString(self.queue_name_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    if (self.has_queue_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.queue_name_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_queue_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_queue_name_: res+=prefix+("queue_name: %s\n" % self.DebugFormatString(self.queue_name_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  kqueue_name = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "queue_name",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueDeleteQueueRequest'
class TaskQueueDeleteQueueResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueDeleteQueueResponse'
class TaskQueueDeleteGroupRequest(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""

  def __init__(self, contents=None):
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


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
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
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_):
      n += 1
      n += self.lengthString(len(self.app_id_))
    return n

  def Clear(self):
    self.clear_app_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.app_id_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueDeleteGroupRequest'
class TaskQueueDeleteGroupResponse(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueDeleteGroupResponse'
class TaskQueueQueryTasksRequest(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_queue_name_ = 0
  queue_name_ = ""
  has_start_task_name_ = 0
  start_task_name_ = ""
  has_start_eta_usec_ = 0
  start_eta_usec_ = 0
  has_start_tag_ = 0
  start_tag_ = ""
  has_max_rows_ = 0
  max_rows_ = 1

  def __init__(self, contents=None):
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

  def queue_name(self): return self.queue_name_

  def set_queue_name(self, x):
    self.has_queue_name_ = 1
    self.queue_name_ = x

  def clear_queue_name(self):
    if self.has_queue_name_:
      self.has_queue_name_ = 0
      self.queue_name_ = ""

  def has_queue_name(self): return self.has_queue_name_

  def start_task_name(self): return self.start_task_name_

  def set_start_task_name(self, x):
    self.has_start_task_name_ = 1
    self.start_task_name_ = x

  def clear_start_task_name(self):
    if self.has_start_task_name_:
      self.has_start_task_name_ = 0
      self.start_task_name_ = ""

  def has_start_task_name(self): return self.has_start_task_name_

  def start_eta_usec(self): return self.start_eta_usec_

  def set_start_eta_usec(self, x):
    self.has_start_eta_usec_ = 1
    self.start_eta_usec_ = x

  def clear_start_eta_usec(self):
    if self.has_start_eta_usec_:
      self.has_start_eta_usec_ = 0
      self.start_eta_usec_ = 0

  def has_start_eta_usec(self): return self.has_start_eta_usec_

  def start_tag(self): return self.start_tag_

  def set_start_tag(self, x):
    self.has_start_tag_ = 1
    self.start_tag_ = x

  def clear_start_tag(self):
    if self.has_start_tag_:
      self.has_start_tag_ = 0
      self.start_tag_ = ""

  def has_start_tag(self): return self.has_start_tag_

  def max_rows(self): return self.max_rows_

  def set_max_rows(self, x):
    self.has_max_rows_ = 1
    self.max_rows_ = x

  def clear_max_rows(self):
    if self.has_max_rows_:
      self.has_max_rows_ = 0
      self.max_rows_ = 1

  def has_max_rows(self): return self.has_max_rows_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_queue_name()): self.set_queue_name(x.queue_name())
    if (x.has_start_task_name()): self.set_start_task_name(x.start_task_name())
    if (x.has_start_eta_usec()): self.set_start_eta_usec(x.start_eta_usec())
    if (x.has_start_tag()): self.set_start_tag(x.start_tag())
    if (x.has_max_rows()): self.set_max_rows(x.max_rows())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_queue_name_ != x.has_queue_name_: return 0
    if self.has_queue_name_ and self.queue_name_ != x.queue_name_: return 0
    if self.has_start_task_name_ != x.has_start_task_name_: return 0
    if self.has_start_task_name_ and self.start_task_name_ != x.start_task_name_: return 0
    if self.has_start_eta_usec_ != x.has_start_eta_usec_: return 0
    if self.has_start_eta_usec_ and self.start_eta_usec_ != x.start_eta_usec_: return 0
    if self.has_start_tag_ != x.has_start_tag_: return 0
    if self.has_start_tag_ and self.start_tag_ != x.start_tag_: return 0
    if self.has_max_rows_ != x.has_max_rows_: return 0
    if self.has_max_rows_ and self.max_rows_ != x.max_rows_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_queue_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: queue_name not set.')
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    n += self.lengthString(len(self.queue_name_))
    if (self.has_start_task_name_): n += 1 + self.lengthString(len(self.start_task_name_))
    if (self.has_start_eta_usec_): n += 1 + self.lengthVarInt64(self.start_eta_usec_)
    if (self.has_start_tag_): n += 1 + self.lengthString(len(self.start_tag_))
    if (self.has_max_rows_): n += 1 + self.lengthVarInt64(self.max_rows_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    if (self.has_queue_name_):
      n += 1
      n += self.lengthString(len(self.queue_name_))
    if (self.has_start_task_name_): n += 1 + self.lengthString(len(self.start_task_name_))
    if (self.has_start_eta_usec_): n += 1 + self.lengthVarInt64(self.start_eta_usec_)
    if (self.has_start_tag_): n += 1 + self.lengthString(len(self.start_tag_))
    if (self.has_max_rows_): n += 1 + self.lengthVarInt64(self.max_rows_)
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_queue_name()
    self.clear_start_task_name()
    self.clear_start_eta_usec()
    self.clear_start_tag()
    self.clear_max_rows()

  def OutputUnchecked(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    out.putVarInt32(18)
    out.putPrefixedString(self.queue_name_)
    if (self.has_start_task_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.start_task_name_)
    if (self.has_start_eta_usec_):
      out.putVarInt32(32)
      out.putVarInt64(self.start_eta_usec_)
    if (self.has_max_rows_):
      out.putVarInt32(40)
      out.putVarInt32(self.max_rows_)
    if (self.has_start_tag_):
      out.putVarInt32(50)
      out.putPrefixedString(self.start_tag_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    if (self.has_queue_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.queue_name_)
    if (self.has_start_task_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.start_task_name_)
    if (self.has_start_eta_usec_):
      out.putVarInt32(32)
      out.putVarInt64(self.start_eta_usec_)
    if (self.has_max_rows_):
      out.putVarInt32(40)
      out.putVarInt32(self.max_rows_)
    if (self.has_start_tag_):
      out.putVarInt32(50)
      out.putPrefixedString(self.start_tag_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_queue_name(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_start_task_name(d.getPrefixedString())
        continue
      if tt == 32:
        self.set_start_eta_usec(d.getVarInt64())
        continue
      if tt == 40:
        self.set_max_rows(d.getVarInt32())
        continue
      if tt == 50:
        self.set_start_tag(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_queue_name_: res+=prefix+("queue_name: %s\n" % self.DebugFormatString(self.queue_name_))
    if self.has_start_task_name_: res+=prefix+("start_task_name: %s\n" % self.DebugFormatString(self.start_task_name_))
    if self.has_start_eta_usec_: res+=prefix+("start_eta_usec: %s\n" % self.DebugFormatInt64(self.start_eta_usec_))
    if self.has_start_tag_: res+=prefix+("start_tag: %s\n" % self.DebugFormatString(self.start_tag_))
    if self.has_max_rows_: res+=prefix+("max_rows: %s\n" % self.DebugFormatInt32(self.max_rows_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  kqueue_name = 2
  kstart_task_name = 3
  kstart_eta_usec = 4
  kstart_tag = 6
  kmax_rows = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "queue_name",
    3: "start_task_name",
    4: "start_eta_usec",
    5: "max_rows",
    6: "start_tag",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.STRING,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueQueryTasksRequest'
class TaskQueueQueryTasksResponse_TaskHeader(ProtocolBuffer.ProtocolMessage):
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
    out.putVarInt32(66)
    out.putPrefixedString(self.key_)
    out.putVarInt32(74)
    out.putPrefixedString(self.value_)

  def OutputPartial(self, out):
    if (self.has_key_):
      out.putVarInt32(66)
      out.putPrefixedString(self.key_)
    if (self.has_value_):
      out.putVarInt32(74)
      out.putPrefixedString(self.value_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 60: break
      if tt == 66:
        self.set_key(d.getPrefixedString())
        continue
      if tt == 74:
        self.set_value(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_: res+=prefix+("key: %s\n" % self.DebugFormatString(self.key_))
    if self.has_value_: res+=prefix+("value: %s\n" % self.DebugFormatString(self.value_))
    return res

class TaskQueueQueryTasksResponse_TaskCronTimetable(ProtocolBuffer.ProtocolMessage):
  has_schedule_ = 0
  schedule_ = ""
  has_timezone_ = 0
  timezone_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def schedule(self): return self.schedule_

  def set_schedule(self, x):
    self.has_schedule_ = 1
    self.schedule_ = x

  def clear_schedule(self):
    if self.has_schedule_:
      self.has_schedule_ = 0
      self.schedule_ = ""

  def has_schedule(self): return self.has_schedule_

  def timezone(self): return self.timezone_

  def set_timezone(self, x):
    self.has_timezone_ = 1
    self.timezone_ = x

  def clear_timezone(self):
    if self.has_timezone_:
      self.has_timezone_ = 0
      self.timezone_ = ""

  def has_timezone(self): return self.has_timezone_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_schedule()): self.set_schedule(x.schedule())
    if (x.has_timezone()): self.set_timezone(x.timezone())

  def Equals(self, x):
    if x is self: return 1
    if self.has_schedule_ != x.has_schedule_: return 0
    if self.has_schedule_ and self.schedule_ != x.schedule_: return 0
    if self.has_timezone_ != x.has_timezone_: return 0
    if self.has_timezone_ and self.timezone_ != x.timezone_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_schedule_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: schedule not set.')
    if (not self.has_timezone_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: timezone not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.schedule_))
    n += self.lengthString(len(self.timezone_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_schedule_):
      n += 1
      n += self.lengthString(len(self.schedule_))
    if (self.has_timezone_):
      n += 1
      n += self.lengthString(len(self.timezone_))
    return n

  def Clear(self):
    self.clear_schedule()
    self.clear_timezone()

  def OutputUnchecked(self, out):
    out.putVarInt32(114)
    out.putPrefixedString(self.schedule_)
    out.putVarInt32(122)
    out.putPrefixedString(self.timezone_)

  def OutputPartial(self, out):
    if (self.has_schedule_):
      out.putVarInt32(114)
      out.putPrefixedString(self.schedule_)
    if (self.has_timezone_):
      out.putVarInt32(122)
      out.putPrefixedString(self.timezone_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 108: break
      if tt == 114:
        self.set_schedule(d.getPrefixedString())
        continue
      if tt == 122:
        self.set_timezone(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_schedule_: res+=prefix+("schedule: %s\n" % self.DebugFormatString(self.schedule_))
    if self.has_timezone_: res+=prefix+("timezone: %s\n" % self.DebugFormatString(self.timezone_))
    return res

class TaskQueueQueryTasksResponse_TaskRunLog(ProtocolBuffer.ProtocolMessage):
  has_dispatched_usec_ = 0
  dispatched_usec_ = 0
  has_lag_usec_ = 0
  lag_usec_ = 0
  has_elapsed_usec_ = 0
  elapsed_usec_ = 0
  has_response_code_ = 0
  response_code_ = 0
  has_retry_reason_ = 0
  retry_reason_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def dispatched_usec(self): return self.dispatched_usec_

  def set_dispatched_usec(self, x):
    self.has_dispatched_usec_ = 1
    self.dispatched_usec_ = x

  def clear_dispatched_usec(self):
    if self.has_dispatched_usec_:
      self.has_dispatched_usec_ = 0
      self.dispatched_usec_ = 0

  def has_dispatched_usec(self): return self.has_dispatched_usec_

  def lag_usec(self): return self.lag_usec_

  def set_lag_usec(self, x):
    self.has_lag_usec_ = 1
    self.lag_usec_ = x

  def clear_lag_usec(self):
    if self.has_lag_usec_:
      self.has_lag_usec_ = 0
      self.lag_usec_ = 0

  def has_lag_usec(self): return self.has_lag_usec_

  def elapsed_usec(self): return self.elapsed_usec_

  def set_elapsed_usec(self, x):
    self.has_elapsed_usec_ = 1
    self.elapsed_usec_ = x

  def clear_elapsed_usec(self):
    if self.has_elapsed_usec_:
      self.has_elapsed_usec_ = 0
      self.elapsed_usec_ = 0

  def has_elapsed_usec(self): return self.has_elapsed_usec_

  def response_code(self): return self.response_code_

  def set_response_code(self, x):
    self.has_response_code_ = 1
    self.response_code_ = x

  def clear_response_code(self):
    if self.has_response_code_:
      self.has_response_code_ = 0
      self.response_code_ = 0

  def has_response_code(self): return self.has_response_code_

  def retry_reason(self): return self.retry_reason_

  def set_retry_reason(self, x):
    self.has_retry_reason_ = 1
    self.retry_reason_ = x

  def clear_retry_reason(self):
    if self.has_retry_reason_:
      self.has_retry_reason_ = 0
      self.retry_reason_ = ""

  def has_retry_reason(self): return self.has_retry_reason_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_dispatched_usec()): self.set_dispatched_usec(x.dispatched_usec())
    if (x.has_lag_usec()): self.set_lag_usec(x.lag_usec())
    if (x.has_elapsed_usec()): self.set_elapsed_usec(x.elapsed_usec())
    if (x.has_response_code()): self.set_response_code(x.response_code())
    if (x.has_retry_reason()): self.set_retry_reason(x.retry_reason())

  def Equals(self, x):
    if x is self: return 1
    if self.has_dispatched_usec_ != x.has_dispatched_usec_: return 0
    if self.has_dispatched_usec_ and self.dispatched_usec_ != x.dispatched_usec_: return 0
    if self.has_lag_usec_ != x.has_lag_usec_: return 0
    if self.has_lag_usec_ and self.lag_usec_ != x.lag_usec_: return 0
    if self.has_elapsed_usec_ != x.has_elapsed_usec_: return 0
    if self.has_elapsed_usec_ and self.elapsed_usec_ != x.elapsed_usec_: return 0
    if self.has_response_code_ != x.has_response_code_: return 0
    if self.has_response_code_ and self.response_code_ != x.response_code_: return 0
    if self.has_retry_reason_ != x.has_retry_reason_: return 0
    if self.has_retry_reason_ and self.retry_reason_ != x.retry_reason_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_dispatched_usec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: dispatched_usec not set.')
    if (not self.has_lag_usec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: lag_usec not set.')
    if (not self.has_elapsed_usec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: elapsed_usec not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.dispatched_usec_)
    n += self.lengthVarInt64(self.lag_usec_)
    n += self.lengthVarInt64(self.elapsed_usec_)
    if (self.has_response_code_): n += 2 + self.lengthVarInt64(self.response_code_)
    if (self.has_retry_reason_): n += 2 + self.lengthString(len(self.retry_reason_))
    return n + 6

  def ByteSizePartial(self):
    n = 0
    if (self.has_dispatched_usec_):
      n += 2
      n += self.lengthVarInt64(self.dispatched_usec_)
    if (self.has_lag_usec_):
      n += 2
      n += self.lengthVarInt64(self.lag_usec_)
    if (self.has_elapsed_usec_):
      n += 2
      n += self.lengthVarInt64(self.elapsed_usec_)
    if (self.has_response_code_): n += 2 + self.lengthVarInt64(self.response_code_)
    if (self.has_retry_reason_): n += 2 + self.lengthString(len(self.retry_reason_))
    return n

  def Clear(self):
    self.clear_dispatched_usec()
    self.clear_lag_usec()
    self.clear_elapsed_usec()
    self.clear_response_code()
    self.clear_retry_reason()

  def OutputUnchecked(self, out):
    out.putVarInt32(136)
    out.putVarInt64(self.dispatched_usec_)
    out.putVarInt32(144)
    out.putVarInt64(self.lag_usec_)
    out.putVarInt32(152)
    out.putVarInt64(self.elapsed_usec_)
    if (self.has_response_code_):
      out.putVarInt32(160)
      out.putVarInt64(self.response_code_)
    if (self.has_retry_reason_):
      out.putVarInt32(218)
      out.putPrefixedString(self.retry_reason_)

  def OutputPartial(self, out):
    if (self.has_dispatched_usec_):
      out.putVarInt32(136)
      out.putVarInt64(self.dispatched_usec_)
    if (self.has_lag_usec_):
      out.putVarInt32(144)
      out.putVarInt64(self.lag_usec_)
    if (self.has_elapsed_usec_):
      out.putVarInt32(152)
      out.putVarInt64(self.elapsed_usec_)
    if (self.has_response_code_):
      out.putVarInt32(160)
      out.putVarInt64(self.response_code_)
    if (self.has_retry_reason_):
      out.putVarInt32(218)
      out.putPrefixedString(self.retry_reason_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 132: break
      if tt == 136:
        self.set_dispatched_usec(d.getVarInt64())
        continue
      if tt == 144:
        self.set_lag_usec(d.getVarInt64())
        continue
      if tt == 152:
        self.set_elapsed_usec(d.getVarInt64())
        continue
      if tt == 160:
        self.set_response_code(d.getVarInt64())
        continue
      if tt == 218:
        self.set_retry_reason(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_dispatched_usec_: res+=prefix+("dispatched_usec: %s\n" % self.DebugFormatInt64(self.dispatched_usec_))
    if self.has_lag_usec_: res+=prefix+("lag_usec: %s\n" % self.DebugFormatInt64(self.lag_usec_))
    if self.has_elapsed_usec_: res+=prefix+("elapsed_usec: %s\n" % self.DebugFormatInt64(self.elapsed_usec_))
    if self.has_response_code_: res+=prefix+("response_code: %s\n" % self.DebugFormatInt64(self.response_code_))
    if self.has_retry_reason_: res+=prefix+("retry_reason: %s\n" % self.DebugFormatString(self.retry_reason_))
    return res

class TaskQueueQueryTasksResponse_Task(ProtocolBuffer.ProtocolMessage):


  GET          =    1
  POST         =    2
  HEAD         =    3
  PUT          =    4
  DELETE       =    5

  _RequestMethod_NAMES = {
    1: "GET",
    2: "POST",
    3: "HEAD",
    4: "PUT",
    5: "DELETE",
  }

  def RequestMethod_Name(cls, x): return cls._RequestMethod_NAMES.get(x, "")
  RequestMethod_Name = classmethod(RequestMethod_Name)

  has_task_name_ = 0
  task_name_ = ""
  has_eta_usec_ = 0
  eta_usec_ = 0
  has_url_ = 0
  url_ = ""
  has_method_ = 0
  method_ = 0
  has_retry_count_ = 0
  retry_count_ = 0
  has_body_size_ = 0
  body_size_ = 0
  has_body_ = 0
  body_ = ""
  has_creation_time_usec_ = 0
  creation_time_usec_ = 0
  has_crontimetable_ = 0
  crontimetable_ = None
  has_runlog_ = 0
  runlog_ = None
  has_description_ = 0
  description_ = ""
  has_payload_ = 0
  payload_ = None
  has_retry_parameters_ = 0
  retry_parameters_ = None
  has_first_try_usec_ = 0
  first_try_usec_ = 0
  has_tag_ = 0
  tag_ = ""
  has_execution_count_ = 0
  execution_count_ = 0

  def __init__(self, contents=None):
    self.header_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def task_name(self): return self.task_name_

  def set_task_name(self, x):
    self.has_task_name_ = 1
    self.task_name_ = x

  def clear_task_name(self):
    if self.has_task_name_:
      self.has_task_name_ = 0
      self.task_name_ = ""

  def has_task_name(self): return self.has_task_name_

  def eta_usec(self): return self.eta_usec_

  def set_eta_usec(self, x):
    self.has_eta_usec_ = 1
    self.eta_usec_ = x

  def clear_eta_usec(self):
    if self.has_eta_usec_:
      self.has_eta_usec_ = 0
      self.eta_usec_ = 0

  def has_eta_usec(self): return self.has_eta_usec_

  def url(self): return self.url_

  def set_url(self, x):
    self.has_url_ = 1
    self.url_ = x

  def clear_url(self):
    if self.has_url_:
      self.has_url_ = 0
      self.url_ = ""

  def has_url(self): return self.has_url_

  def method(self): return self.method_

  def set_method(self, x):
    self.has_method_ = 1
    self.method_ = x

  def clear_method(self):
    if self.has_method_:
      self.has_method_ = 0
      self.method_ = 0

  def has_method(self): return self.has_method_

  def retry_count(self): return self.retry_count_

  def set_retry_count(self, x):
    self.has_retry_count_ = 1
    self.retry_count_ = x

  def clear_retry_count(self):
    if self.has_retry_count_:
      self.has_retry_count_ = 0
      self.retry_count_ = 0

  def has_retry_count(self): return self.has_retry_count_

  def header_size(self): return len(self.header_)
  def header_list(self): return self.header_

  def header(self, i):
    return self.header_[i]

  def mutable_header(self, i):
    return self.header_[i]

  def add_header(self):
    x = TaskQueueQueryTasksResponse_TaskHeader()
    self.header_.append(x)
    return x

  def clear_header(self):
    self.header_ = []
  def body_size(self): return self.body_size_

  def set_body_size(self, x):
    self.has_body_size_ = 1
    self.body_size_ = x

  def clear_body_size(self):
    if self.has_body_size_:
      self.has_body_size_ = 0
      self.body_size_ = 0

  def has_body_size(self): return self.has_body_size_

  def body(self): return self.body_

  def set_body(self, x):
    self.has_body_ = 1
    self.body_ = x

  def clear_body(self):
    if self.has_body_:
      self.has_body_ = 0
      self.body_ = ""

  def has_body(self): return self.has_body_

  def creation_time_usec(self): return self.creation_time_usec_

  def set_creation_time_usec(self, x):
    self.has_creation_time_usec_ = 1
    self.creation_time_usec_ = x

  def clear_creation_time_usec(self):
    if self.has_creation_time_usec_:
      self.has_creation_time_usec_ = 0
      self.creation_time_usec_ = 0

  def has_creation_time_usec(self): return self.has_creation_time_usec_

  def crontimetable(self):
    if self.crontimetable_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.crontimetable_ is None: self.crontimetable_ = TaskQueueQueryTasksResponse_TaskCronTimetable()
      finally:
        self.lazy_init_lock_.release()
    return self.crontimetable_

  def mutable_crontimetable(self): self.has_crontimetable_ = 1; return self.crontimetable()

  def clear_crontimetable(self):

    if self.has_crontimetable_:
      self.has_crontimetable_ = 0;
      if self.crontimetable_ is not None: self.crontimetable_.Clear()

  def has_crontimetable(self): return self.has_crontimetable_

  def runlog(self):
    if self.runlog_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.runlog_ is None: self.runlog_ = TaskQueueQueryTasksResponse_TaskRunLog()
      finally:
        self.lazy_init_lock_.release()
    return self.runlog_

  def mutable_runlog(self): self.has_runlog_ = 1; return self.runlog()

  def clear_runlog(self):

    if self.has_runlog_:
      self.has_runlog_ = 0;
      if self.runlog_ is not None: self.runlog_.Clear()

  def has_runlog(self): return self.has_runlog_

  def description(self): return self.description_

  def set_description(self, x):
    self.has_description_ = 1
    self.description_ = x

  def clear_description(self):
    if self.has_description_:
      self.has_description_ = 0
      self.description_ = ""

  def has_description(self): return self.has_description_

  def payload(self):
    if self.payload_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.payload_ is None: self.payload_ = MessageSet()
      finally:
        self.lazy_init_lock_.release()
    return self.payload_

  def mutable_payload(self): self.has_payload_ = 1; return self.payload()

  def clear_payload(self):

    if self.has_payload_:
      self.has_payload_ = 0;
      if self.payload_ is not None: self.payload_.Clear()

  def has_payload(self): return self.has_payload_

  def retry_parameters(self):
    if self.retry_parameters_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.retry_parameters_ is None: self.retry_parameters_ = TaskQueueRetryParameters()
      finally:
        self.lazy_init_lock_.release()
    return self.retry_parameters_

  def mutable_retry_parameters(self): self.has_retry_parameters_ = 1; return self.retry_parameters()

  def clear_retry_parameters(self):

    if self.has_retry_parameters_:
      self.has_retry_parameters_ = 0;
      if self.retry_parameters_ is not None: self.retry_parameters_.Clear()

  def has_retry_parameters(self): return self.has_retry_parameters_

  def first_try_usec(self): return self.first_try_usec_

  def set_first_try_usec(self, x):
    self.has_first_try_usec_ = 1
    self.first_try_usec_ = x

  def clear_first_try_usec(self):
    if self.has_first_try_usec_:
      self.has_first_try_usec_ = 0
      self.first_try_usec_ = 0

  def has_first_try_usec(self): return self.has_first_try_usec_

  def tag(self): return self.tag_

  def set_tag(self, x):
    self.has_tag_ = 1
    self.tag_ = x

  def clear_tag(self):
    if self.has_tag_:
      self.has_tag_ = 0
      self.tag_ = ""

  def has_tag(self): return self.has_tag_

  def execution_count(self): return self.execution_count_

  def set_execution_count(self, x):
    self.has_execution_count_ = 1
    self.execution_count_ = x

  def clear_execution_count(self):
    if self.has_execution_count_:
      self.has_execution_count_ = 0
      self.execution_count_ = 0

  def has_execution_count(self): return self.has_execution_count_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_task_name()): self.set_task_name(x.task_name())
    if (x.has_eta_usec()): self.set_eta_usec(x.eta_usec())
    if (x.has_url()): self.set_url(x.url())
    if (x.has_method()): self.set_method(x.method())
    if (x.has_retry_count()): self.set_retry_count(x.retry_count())
    for i in xrange(x.header_size()): self.add_header().CopyFrom(x.header(i))
    if (x.has_body_size()): self.set_body_size(x.body_size())
    if (x.has_body()): self.set_body(x.body())
    if (x.has_creation_time_usec()): self.set_creation_time_usec(x.creation_time_usec())
    if (x.has_crontimetable()): self.mutable_crontimetable().MergeFrom(x.crontimetable())
    if (x.has_runlog()): self.mutable_runlog().MergeFrom(x.runlog())
    if (x.has_description()): self.set_description(x.description())
    if (x.has_payload()): self.mutable_payload().MergeFrom(x.payload())
    if (x.has_retry_parameters()): self.mutable_retry_parameters().MergeFrom(x.retry_parameters())
    if (x.has_first_try_usec()): self.set_first_try_usec(x.first_try_usec())
    if (x.has_tag()): self.set_tag(x.tag())
    if (x.has_execution_count()): self.set_execution_count(x.execution_count())

  def Equals(self, x):
    if x is self: return 1
    if self.has_task_name_ != x.has_task_name_: return 0
    if self.has_task_name_ and self.task_name_ != x.task_name_: return 0
    if self.has_eta_usec_ != x.has_eta_usec_: return 0
    if self.has_eta_usec_ and self.eta_usec_ != x.eta_usec_: return 0
    if self.has_url_ != x.has_url_: return 0
    if self.has_url_ and self.url_ != x.url_: return 0
    if self.has_method_ != x.has_method_: return 0
    if self.has_method_ and self.method_ != x.method_: return 0
    if self.has_retry_count_ != x.has_retry_count_: return 0
    if self.has_retry_count_ and self.retry_count_ != x.retry_count_: return 0
    if len(self.header_) != len(x.header_): return 0
    for e1, e2 in zip(self.header_, x.header_):
      if e1 != e2: return 0
    if self.has_body_size_ != x.has_body_size_: return 0
    if self.has_body_size_ and self.body_size_ != x.body_size_: return 0
    if self.has_body_ != x.has_body_: return 0
    if self.has_body_ and self.body_ != x.body_: return 0
    if self.has_creation_time_usec_ != x.has_creation_time_usec_: return 0
    if self.has_creation_time_usec_ and self.creation_time_usec_ != x.creation_time_usec_: return 0
    if self.has_crontimetable_ != x.has_crontimetable_: return 0
    if self.has_crontimetable_ and self.crontimetable_ != x.crontimetable_: return 0
    if self.has_runlog_ != x.has_runlog_: return 0
    if self.has_runlog_ and self.runlog_ != x.runlog_: return 0
    if self.has_description_ != x.has_description_: return 0
    if self.has_description_ and self.description_ != x.description_: return 0
    if self.has_payload_ != x.has_payload_: return 0
    if self.has_payload_ and self.payload_ != x.payload_: return 0
    if self.has_retry_parameters_ != x.has_retry_parameters_: return 0
    if self.has_retry_parameters_ and self.retry_parameters_ != x.retry_parameters_: return 0
    if self.has_first_try_usec_ != x.has_first_try_usec_: return 0
    if self.has_first_try_usec_ and self.first_try_usec_ != x.first_try_usec_: return 0
    if self.has_tag_ != x.has_tag_: return 0
    if self.has_tag_ and self.tag_ != x.tag_: return 0
    if self.has_execution_count_ != x.has_execution_count_: return 0
    if self.has_execution_count_ and self.execution_count_ != x.execution_count_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_task_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: task_name not set.')
    if (not self.has_eta_usec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: eta_usec not set.')
    for p in self.header_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (not self.has_creation_time_usec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: creation_time_usec not set.')
    if (self.has_crontimetable_ and not self.crontimetable_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_runlog_ and not self.runlog_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_payload_ and not self.payload_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_retry_parameters_ and not self.retry_parameters_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.task_name_))
    n += self.lengthVarInt64(self.eta_usec_)
    if (self.has_url_): n += 1 + self.lengthString(len(self.url_))
    if (self.has_method_): n += 1 + self.lengthVarInt64(self.method_)
    if (self.has_retry_count_): n += 1 + self.lengthVarInt64(self.retry_count_)
    n += 2 * len(self.header_)
    for i in xrange(len(self.header_)): n += self.header_[i].ByteSize()
    if (self.has_body_size_): n += 1 + self.lengthVarInt64(self.body_size_)
    if (self.has_body_): n += 1 + self.lengthString(len(self.body_))
    n += self.lengthVarInt64(self.creation_time_usec_)
    if (self.has_crontimetable_): n += 2 + self.crontimetable_.ByteSize()
    if (self.has_runlog_): n += 4 + self.runlog_.ByteSize()
    if (self.has_description_): n += 2 + self.lengthString(len(self.description_))
    if (self.has_payload_): n += 2 + self.lengthString(self.payload_.ByteSize())
    if (self.has_retry_parameters_): n += 2 + self.lengthString(self.retry_parameters_.ByteSize())
    if (self.has_first_try_usec_): n += 2 + self.lengthVarInt64(self.first_try_usec_)
    if (self.has_tag_): n += 2 + self.lengthString(len(self.tag_))
    if (self.has_execution_count_): n += 2 + self.lengthVarInt64(self.execution_count_)
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_task_name_):
      n += 1
      n += self.lengthString(len(self.task_name_))
    if (self.has_eta_usec_):
      n += 1
      n += self.lengthVarInt64(self.eta_usec_)
    if (self.has_url_): n += 1 + self.lengthString(len(self.url_))
    if (self.has_method_): n += 1 + self.lengthVarInt64(self.method_)
    if (self.has_retry_count_): n += 1 + self.lengthVarInt64(self.retry_count_)
    n += 2 * len(self.header_)
    for i in xrange(len(self.header_)): n += self.header_[i].ByteSizePartial()
    if (self.has_body_size_): n += 1 + self.lengthVarInt64(self.body_size_)
    if (self.has_body_): n += 1 + self.lengthString(len(self.body_))
    if (self.has_creation_time_usec_):
      n += 1
      n += self.lengthVarInt64(self.creation_time_usec_)
    if (self.has_crontimetable_): n += 2 + self.crontimetable_.ByteSizePartial()
    if (self.has_runlog_): n += 4 + self.runlog_.ByteSizePartial()
    if (self.has_description_): n += 2 + self.lengthString(len(self.description_))
    if (self.has_payload_): n += 2 + self.lengthString(self.payload_.ByteSizePartial())
    if (self.has_retry_parameters_): n += 2 + self.lengthString(self.retry_parameters_.ByteSizePartial())
    if (self.has_first_try_usec_): n += 2 + self.lengthVarInt64(self.first_try_usec_)
    if (self.has_tag_): n += 2 + self.lengthString(len(self.tag_))
    if (self.has_execution_count_): n += 2 + self.lengthVarInt64(self.execution_count_)
    return n

  def Clear(self):
    self.clear_task_name()
    self.clear_eta_usec()
    self.clear_url()
    self.clear_method()
    self.clear_retry_count()
    self.clear_header()
    self.clear_body_size()
    self.clear_body()
    self.clear_creation_time_usec()
    self.clear_crontimetable()
    self.clear_runlog()
    self.clear_description()
    self.clear_payload()
    self.clear_retry_parameters()
    self.clear_first_try_usec()
    self.clear_tag()
    self.clear_execution_count()

  def OutputUnchecked(self, out):
    out.putVarInt32(18)
    out.putPrefixedString(self.task_name_)
    out.putVarInt32(24)
    out.putVarInt64(self.eta_usec_)
    if (self.has_url_):
      out.putVarInt32(34)
      out.putPrefixedString(self.url_)
    if (self.has_method_):
      out.putVarInt32(40)
      out.putVarInt32(self.method_)
    if (self.has_retry_count_):
      out.putVarInt32(48)
      out.putVarInt32(self.retry_count_)
    for i in xrange(len(self.header_)):
      out.putVarInt32(59)
      self.header_[i].OutputUnchecked(out)
      out.putVarInt32(60)
    if (self.has_body_size_):
      out.putVarInt32(80)
      out.putVarInt32(self.body_size_)
    if (self.has_body_):
      out.putVarInt32(90)
      out.putPrefixedString(self.body_)
    out.putVarInt32(96)
    out.putVarInt64(self.creation_time_usec_)
    if (self.has_crontimetable_):
      out.putVarInt32(107)
      self.crontimetable_.OutputUnchecked(out)
      out.putVarInt32(108)
    if (self.has_runlog_):
      out.putVarInt32(131)
      self.runlog_.OutputUnchecked(out)
      out.putVarInt32(132)
    if (self.has_description_):
      out.putVarInt32(170)
      out.putPrefixedString(self.description_)
    if (self.has_payload_):
      out.putVarInt32(178)
      out.putVarInt32(self.payload_.ByteSize())
      self.payload_.OutputUnchecked(out)
    if (self.has_retry_parameters_):
      out.putVarInt32(186)
      out.putVarInt32(self.retry_parameters_.ByteSize())
      self.retry_parameters_.OutputUnchecked(out)
    if (self.has_first_try_usec_):
      out.putVarInt32(192)
      out.putVarInt64(self.first_try_usec_)
    if (self.has_tag_):
      out.putVarInt32(202)
      out.putPrefixedString(self.tag_)
    if (self.has_execution_count_):
      out.putVarInt32(208)
      out.putVarInt32(self.execution_count_)

  def OutputPartial(self, out):
    if (self.has_task_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.task_name_)
    if (self.has_eta_usec_):
      out.putVarInt32(24)
      out.putVarInt64(self.eta_usec_)
    if (self.has_url_):
      out.putVarInt32(34)
      out.putPrefixedString(self.url_)
    if (self.has_method_):
      out.putVarInt32(40)
      out.putVarInt32(self.method_)
    if (self.has_retry_count_):
      out.putVarInt32(48)
      out.putVarInt32(self.retry_count_)
    for i in xrange(len(self.header_)):
      out.putVarInt32(59)
      self.header_[i].OutputPartial(out)
      out.putVarInt32(60)
    if (self.has_body_size_):
      out.putVarInt32(80)
      out.putVarInt32(self.body_size_)
    if (self.has_body_):
      out.putVarInt32(90)
      out.putPrefixedString(self.body_)
    if (self.has_creation_time_usec_):
      out.putVarInt32(96)
      out.putVarInt64(self.creation_time_usec_)
    if (self.has_crontimetable_):
      out.putVarInt32(107)
      self.crontimetable_.OutputPartial(out)
      out.putVarInt32(108)
    if (self.has_runlog_):
      out.putVarInt32(131)
      self.runlog_.OutputPartial(out)
      out.putVarInt32(132)
    if (self.has_description_):
      out.putVarInt32(170)
      out.putPrefixedString(self.description_)
    if (self.has_payload_):
      out.putVarInt32(178)
      out.putVarInt32(self.payload_.ByteSizePartial())
      self.payload_.OutputPartial(out)
    if (self.has_retry_parameters_):
      out.putVarInt32(186)
      out.putVarInt32(self.retry_parameters_.ByteSizePartial())
      self.retry_parameters_.OutputPartial(out)
    if (self.has_first_try_usec_):
      out.putVarInt32(192)
      out.putVarInt64(self.first_try_usec_)
    if (self.has_tag_):
      out.putVarInt32(202)
      out.putPrefixedString(self.tag_)
    if (self.has_execution_count_):
      out.putVarInt32(208)
      out.putVarInt32(self.execution_count_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 12: break
      if tt == 18:
        self.set_task_name(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_eta_usec(d.getVarInt64())
        continue
      if tt == 34:
        self.set_url(d.getPrefixedString())
        continue
      if tt == 40:
        self.set_method(d.getVarInt32())
        continue
      if tt == 48:
        self.set_retry_count(d.getVarInt32())
        continue
      if tt == 59:
        self.add_header().TryMerge(d)
        continue
      if tt == 80:
        self.set_body_size(d.getVarInt32())
        continue
      if tt == 90:
        self.set_body(d.getPrefixedString())
        continue
      if tt == 96:
        self.set_creation_time_usec(d.getVarInt64())
        continue
      if tt == 107:
        self.mutable_crontimetable().TryMerge(d)
        continue
      if tt == 131:
        self.mutable_runlog().TryMerge(d)
        continue
      if tt == 170:
        self.set_description(d.getPrefixedString())
        continue
      if tt == 178:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_payload().TryMerge(tmp)
        continue
      if tt == 186:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_retry_parameters().TryMerge(tmp)
        continue
      if tt == 192:
        self.set_first_try_usec(d.getVarInt64())
        continue
      if tt == 202:
        self.set_tag(d.getPrefixedString())
        continue
      if tt == 208:
        self.set_execution_count(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_task_name_: res+=prefix+("task_name: %s\n" % self.DebugFormatString(self.task_name_))
    if self.has_eta_usec_: res+=prefix+("eta_usec: %s\n" % self.DebugFormatInt64(self.eta_usec_))
    if self.has_url_: res+=prefix+("url: %s\n" % self.DebugFormatString(self.url_))
    if self.has_method_: res+=prefix+("method: %s\n" % self.DebugFormatInt32(self.method_))
    if self.has_retry_count_: res+=prefix+("retry_count: %s\n" % self.DebugFormatInt32(self.retry_count_))
    cnt=0
    for e in self.header_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Header%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    if self.has_body_size_: res+=prefix+("body_size: %s\n" % self.DebugFormatInt32(self.body_size_))
    if self.has_body_: res+=prefix+("body: %s\n" % self.DebugFormatString(self.body_))
    if self.has_creation_time_usec_: res+=prefix+("creation_time_usec: %s\n" % self.DebugFormatInt64(self.creation_time_usec_))
    if self.has_crontimetable_:
      res+=prefix+"CronTimetable {\n"
      res+=self.crontimetable_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
    if self.has_runlog_:
      res+=prefix+"RunLog {\n"
      res+=self.runlog_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
    if self.has_description_: res+=prefix+("description: %s\n" % self.DebugFormatString(self.description_))
    if self.has_payload_:
      res+=prefix+"payload <\n"
      res+=self.payload_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_retry_parameters_:
      res+=prefix+"retry_parameters <\n"
      res+=self.retry_parameters_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_first_try_usec_: res+=prefix+("first_try_usec: %s\n" % self.DebugFormatInt64(self.first_try_usec_))
    if self.has_tag_: res+=prefix+("tag: %s\n" % self.DebugFormatString(self.tag_))
    if self.has_execution_count_: res+=prefix+("execution_count: %s\n" % self.DebugFormatInt32(self.execution_count_))
    return res

class TaskQueueQueryTasksResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.task_ = []
    if contents is not None: self.MergeFromString(contents)

  def task_size(self): return len(self.task_)
  def task_list(self): return self.task_

  def task(self, i):
    return self.task_[i]

  def mutable_task(self, i):
    return self.task_[i]

  def add_task(self):
    x = TaskQueueQueryTasksResponse_Task()
    self.task_.append(x)
    return x

  def clear_task(self):
    self.task_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.task_size()): self.add_task().CopyFrom(x.task(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.task_) != len(x.task_): return 0
    for e1, e2 in zip(self.task_, x.task_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.task_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 2 * len(self.task_)
    for i in xrange(len(self.task_)): n += self.task_[i].ByteSize()
    return n

  def ByteSizePartial(self):
    n = 0
    n += 2 * len(self.task_)
    for i in xrange(len(self.task_)): n += self.task_[i].ByteSizePartial()
    return n

  def Clear(self):
    self.clear_task()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.task_)):
      out.putVarInt32(11)
      self.task_[i].OutputUnchecked(out)
      out.putVarInt32(12)

  def OutputPartial(self, out):
    for i in xrange(len(self.task_)):
      out.putVarInt32(11)
      self.task_[i].OutputPartial(out)
      out.putVarInt32(12)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 11:
        self.add_task().TryMerge(d)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.task_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Task%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kTaskGroup = 1
  kTasktask_name = 2
  kTasketa_usec = 3
  kTaskurl = 4
  kTaskmethod = 5
  kTaskretry_count = 6
  kTaskHeaderGroup = 7
  kTaskHeaderkey = 8
  kTaskHeadervalue = 9
  kTaskbody_size = 10
  kTaskbody = 11
  kTaskcreation_time_usec = 12
  kTaskCronTimetableGroup = 13
  kTaskCronTimetableschedule = 14
  kTaskCronTimetabletimezone = 15
  kTaskRunLogGroup = 16
  kTaskRunLogdispatched_usec = 17
  kTaskRunLoglag_usec = 18
  kTaskRunLogelapsed_usec = 19
  kTaskRunLogresponse_code = 20
  kTaskRunLogretry_reason = 27
  kTaskdescription = 21
  kTaskpayload = 22
  kTaskretry_parameters = 23
  kTaskfirst_try_usec = 24
  kTasktag = 25
  kTaskexecution_count = 26

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "Task",
    2: "task_name",
    3: "eta_usec",
    4: "url",
    5: "method",
    6: "retry_count",
    7: "Header",
    8: "key",
    9: "value",
    10: "body_size",
    11: "body",
    12: "creation_time_usec",
    13: "CronTimetable",
    14: "schedule",
    15: "timezone",
    16: "RunLog",
    17: "dispatched_usec",
    18: "lag_usec",
    19: "elapsed_usec",
    20: "response_code",
    21: "description",
    22: "payload",
    23: "retry_parameters",
    24: "first_try_usec",
    25: "tag",
    26: "execution_count",
    27: "retry_reason",
  }, 27)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STARTGROUP,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.NUMERIC,
    7: ProtocolBuffer.Encoder.STARTGROUP,
    8: ProtocolBuffer.Encoder.STRING,
    9: ProtocolBuffer.Encoder.STRING,
    10: ProtocolBuffer.Encoder.NUMERIC,
    11: ProtocolBuffer.Encoder.STRING,
    12: ProtocolBuffer.Encoder.NUMERIC,
    13: ProtocolBuffer.Encoder.STARTGROUP,
    14: ProtocolBuffer.Encoder.STRING,
    15: ProtocolBuffer.Encoder.STRING,
    16: ProtocolBuffer.Encoder.STARTGROUP,
    17: ProtocolBuffer.Encoder.NUMERIC,
    18: ProtocolBuffer.Encoder.NUMERIC,
    19: ProtocolBuffer.Encoder.NUMERIC,
    20: ProtocolBuffer.Encoder.NUMERIC,
    21: ProtocolBuffer.Encoder.STRING,
    22: ProtocolBuffer.Encoder.STRING,
    23: ProtocolBuffer.Encoder.STRING,
    24: ProtocolBuffer.Encoder.NUMERIC,
    25: ProtocolBuffer.Encoder.STRING,
    26: ProtocolBuffer.Encoder.NUMERIC,
    27: ProtocolBuffer.Encoder.STRING,
  }, 27, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueQueryTasksResponse'
class TaskQueueFetchTaskRequest(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_queue_name_ = 0
  queue_name_ = ""
  has_task_name_ = 0
  task_name_ = ""

  def __init__(self, contents=None):
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

  def queue_name(self): return self.queue_name_

  def set_queue_name(self, x):
    self.has_queue_name_ = 1
    self.queue_name_ = x

  def clear_queue_name(self):
    if self.has_queue_name_:
      self.has_queue_name_ = 0
      self.queue_name_ = ""

  def has_queue_name(self): return self.has_queue_name_

  def task_name(self): return self.task_name_

  def set_task_name(self, x):
    self.has_task_name_ = 1
    self.task_name_ = x

  def clear_task_name(self):
    if self.has_task_name_:
      self.has_task_name_ = 0
      self.task_name_ = ""

  def has_task_name(self): return self.has_task_name_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_queue_name()): self.set_queue_name(x.queue_name())
    if (x.has_task_name()): self.set_task_name(x.task_name())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_queue_name_ != x.has_queue_name_: return 0
    if self.has_queue_name_ and self.queue_name_ != x.queue_name_: return 0
    if self.has_task_name_ != x.has_task_name_: return 0
    if self.has_task_name_ and self.task_name_ != x.task_name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_queue_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: queue_name not set.')
    if (not self.has_task_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: task_name not set.')
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    n += self.lengthString(len(self.queue_name_))
    n += self.lengthString(len(self.task_name_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    if (self.has_queue_name_):
      n += 1
      n += self.lengthString(len(self.queue_name_))
    if (self.has_task_name_):
      n += 1
      n += self.lengthString(len(self.task_name_))
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_queue_name()
    self.clear_task_name()

  def OutputUnchecked(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    out.putVarInt32(18)
    out.putPrefixedString(self.queue_name_)
    out.putVarInt32(26)
    out.putPrefixedString(self.task_name_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    if (self.has_queue_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.queue_name_)
    if (self.has_task_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.task_name_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_queue_name(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_task_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_queue_name_: res+=prefix+("queue_name: %s\n" % self.DebugFormatString(self.queue_name_))
    if self.has_task_name_: res+=prefix+("task_name: %s\n" % self.DebugFormatString(self.task_name_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  kqueue_name = 2
  ktask_name = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "queue_name",
    3: "task_name",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueFetchTaskRequest'
class TaskQueueFetchTaskResponse(ProtocolBuffer.ProtocolMessage):
  has_task_ = 0

  def __init__(self, contents=None):
    self.task_ = TaskQueueQueryTasksResponse()
    if contents is not None: self.MergeFromString(contents)

  def task(self): return self.task_

  def mutable_task(self): self.has_task_ = 1; return self.task_

  def clear_task(self):self.has_task_ = 0; self.task_.Clear()

  def has_task(self): return self.has_task_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_task()): self.mutable_task().MergeFrom(x.task())

  def Equals(self, x):
    if x is self: return 1
    if self.has_task_ != x.has_task_: return 0
    if self.has_task_ and self.task_ != x.task_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_task_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: task not set.')
    elif not self.task_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.task_.ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_task_):
      n += 1
      n += self.lengthString(self.task_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_task()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.task_.ByteSize())
    self.task_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_task_):
      out.putVarInt32(10)
      out.putVarInt32(self.task_.ByteSizePartial())
      self.task_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_task().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_task_:
      res+=prefix+"task <\n"
      res+=self.task_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktask = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "task",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueFetchTaskResponse'
class TaskQueueUpdateStorageLimitRequest(ProtocolBuffer.ProtocolMessage):
  has_app_id_ = 0
  app_id_ = ""
  has_limit_ = 0
  limit_ = 0

  def __init__(self, contents=None):
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
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_limit()): self.set_limit(x.limit())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_limit_ != x.has_limit_: return 0
    if self.has_limit_ and self.limit_ != x.limit_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_app_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: app_id not set.')
    if (not self.has_limit_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: limit not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.app_id_))
    n += self.lengthVarInt64(self.limit_)
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_):
      n += 1
      n += self.lengthString(len(self.app_id_))
    if (self.has_limit_):
      n += 1
      n += self.lengthVarInt64(self.limit_)
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_limit()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.app_id_)
    out.putVarInt32(16)
    out.putVarInt64(self.limit_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    if (self.has_limit_):
      out.putVarInt32(16)
      out.putVarInt64(self.limit_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_limit(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_limit_: res+=prefix+("limit: %s\n" % self.DebugFormatInt64(self.limit_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  klimit = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "limit",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueUpdateStorageLimitRequest'
class TaskQueueUpdateStorageLimitResponse(ProtocolBuffer.ProtocolMessage):
  has_new_limit_ = 0
  new_limit_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def new_limit(self): return self.new_limit_

  def set_new_limit(self, x):
    self.has_new_limit_ = 1
    self.new_limit_ = x

  def clear_new_limit(self):
    if self.has_new_limit_:
      self.has_new_limit_ = 0
      self.new_limit_ = 0

  def has_new_limit(self): return self.has_new_limit_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_new_limit()): self.set_new_limit(x.new_limit())

  def Equals(self, x):
    if x is self: return 1
    if self.has_new_limit_ != x.has_new_limit_: return 0
    if self.has_new_limit_ and self.new_limit_ != x.new_limit_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_new_limit_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: new_limit not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.new_limit_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_new_limit_):
      n += 1
      n += self.lengthVarInt64(self.new_limit_)
    return n

  def Clear(self):
    self.clear_new_limit()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt64(self.new_limit_)

  def OutputPartial(self, out):
    if (self.has_new_limit_):
      out.putVarInt32(8)
      out.putVarInt64(self.new_limit_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_new_limit(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_new_limit_: res+=prefix+("new_limit: %s\n" % self.DebugFormatInt64(self.new_limit_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  knew_limit = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "new_limit",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueUpdateStorageLimitResponse'
class TaskQueueQueryAndOwnTasksRequest(ProtocolBuffer.ProtocolMessage):
  has_queue_name_ = 0
  queue_name_ = ""
  has_lease_seconds_ = 0
  lease_seconds_ = 0.0
  has_max_tasks_ = 0
  max_tasks_ = 0
  has_group_by_tag_ = 0
  group_by_tag_ = 0
  has_tag_ = 0
  tag_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def queue_name(self): return self.queue_name_

  def set_queue_name(self, x):
    self.has_queue_name_ = 1
    self.queue_name_ = x

  def clear_queue_name(self):
    if self.has_queue_name_:
      self.has_queue_name_ = 0
      self.queue_name_ = ""

  def has_queue_name(self): return self.has_queue_name_

  def lease_seconds(self): return self.lease_seconds_

  def set_lease_seconds(self, x):
    self.has_lease_seconds_ = 1
    self.lease_seconds_ = x

  def clear_lease_seconds(self):
    if self.has_lease_seconds_:
      self.has_lease_seconds_ = 0
      self.lease_seconds_ = 0.0

  def has_lease_seconds(self): return self.has_lease_seconds_

  def max_tasks(self): return self.max_tasks_

  def set_max_tasks(self, x):
    self.has_max_tasks_ = 1
    self.max_tasks_ = x

  def clear_max_tasks(self):
    if self.has_max_tasks_:
      self.has_max_tasks_ = 0
      self.max_tasks_ = 0

  def has_max_tasks(self): return self.has_max_tasks_

  def group_by_tag(self): return self.group_by_tag_

  def set_group_by_tag(self, x):
    self.has_group_by_tag_ = 1
    self.group_by_tag_ = x

  def clear_group_by_tag(self):
    if self.has_group_by_tag_:
      self.has_group_by_tag_ = 0
      self.group_by_tag_ = 0

  def has_group_by_tag(self): return self.has_group_by_tag_

  def tag(self): return self.tag_

  def set_tag(self, x):
    self.has_tag_ = 1
    self.tag_ = x

  def clear_tag(self):
    if self.has_tag_:
      self.has_tag_ = 0
      self.tag_ = ""

  def has_tag(self): return self.has_tag_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_queue_name()): self.set_queue_name(x.queue_name())
    if (x.has_lease_seconds()): self.set_lease_seconds(x.lease_seconds())
    if (x.has_max_tasks()): self.set_max_tasks(x.max_tasks())
    if (x.has_group_by_tag()): self.set_group_by_tag(x.group_by_tag())
    if (x.has_tag()): self.set_tag(x.tag())

  def Equals(self, x):
    if x is self: return 1
    if self.has_queue_name_ != x.has_queue_name_: return 0
    if self.has_queue_name_ and self.queue_name_ != x.queue_name_: return 0
    if self.has_lease_seconds_ != x.has_lease_seconds_: return 0
    if self.has_lease_seconds_ and self.lease_seconds_ != x.lease_seconds_: return 0
    if self.has_max_tasks_ != x.has_max_tasks_: return 0
    if self.has_max_tasks_ and self.max_tasks_ != x.max_tasks_: return 0
    if self.has_group_by_tag_ != x.has_group_by_tag_: return 0
    if self.has_group_by_tag_ and self.group_by_tag_ != x.group_by_tag_: return 0
    if self.has_tag_ != x.has_tag_: return 0
    if self.has_tag_ and self.tag_ != x.tag_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_queue_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: queue_name not set.')
    if (not self.has_lease_seconds_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: lease_seconds not set.')
    if (not self.has_max_tasks_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: max_tasks not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.queue_name_))
    n += self.lengthVarInt64(self.max_tasks_)
    if (self.has_group_by_tag_): n += 2
    if (self.has_tag_): n += 1 + self.lengthString(len(self.tag_))
    return n + 11

  def ByteSizePartial(self):
    n = 0
    if (self.has_queue_name_):
      n += 1
      n += self.lengthString(len(self.queue_name_))
    if (self.has_lease_seconds_):
      n += 9
    if (self.has_max_tasks_):
      n += 1
      n += self.lengthVarInt64(self.max_tasks_)
    if (self.has_group_by_tag_): n += 2
    if (self.has_tag_): n += 1 + self.lengthString(len(self.tag_))
    return n

  def Clear(self):
    self.clear_queue_name()
    self.clear_lease_seconds()
    self.clear_max_tasks()
    self.clear_group_by_tag()
    self.clear_tag()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.queue_name_)
    out.putVarInt32(17)
    out.putDouble(self.lease_seconds_)
    out.putVarInt32(24)
    out.putVarInt64(self.max_tasks_)
    if (self.has_group_by_tag_):
      out.putVarInt32(32)
      out.putBoolean(self.group_by_tag_)
    if (self.has_tag_):
      out.putVarInt32(42)
      out.putPrefixedString(self.tag_)

  def OutputPartial(self, out):
    if (self.has_queue_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.queue_name_)
    if (self.has_lease_seconds_):
      out.putVarInt32(17)
      out.putDouble(self.lease_seconds_)
    if (self.has_max_tasks_):
      out.putVarInt32(24)
      out.putVarInt64(self.max_tasks_)
    if (self.has_group_by_tag_):
      out.putVarInt32(32)
      out.putBoolean(self.group_by_tag_)
    if (self.has_tag_):
      out.putVarInt32(42)
      out.putPrefixedString(self.tag_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_queue_name(d.getPrefixedString())
        continue
      if tt == 17:
        self.set_lease_seconds(d.getDouble())
        continue
      if tt == 24:
        self.set_max_tasks(d.getVarInt64())
        continue
      if tt == 32:
        self.set_group_by_tag(d.getBoolean())
        continue
      if tt == 42:
        self.set_tag(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_queue_name_: res+=prefix+("queue_name: %s\n" % self.DebugFormatString(self.queue_name_))
    if self.has_lease_seconds_: res+=prefix+("lease_seconds: %s\n" % self.DebugFormat(self.lease_seconds_))
    if self.has_max_tasks_: res+=prefix+("max_tasks: %s\n" % self.DebugFormatInt64(self.max_tasks_))
    if self.has_group_by_tag_: res+=prefix+("group_by_tag: %s\n" % self.DebugFormatBool(self.group_by_tag_))
    if self.has_tag_: res+=prefix+("tag: %s\n" % self.DebugFormatString(self.tag_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kqueue_name = 1
  klease_seconds = 2
  kmax_tasks = 3
  kgroup_by_tag = 4
  ktag = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "queue_name",
    2: "lease_seconds",
    3: "max_tasks",
    4: "group_by_tag",
    5: "tag",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.DOUBLE,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueQueryAndOwnTasksRequest'
class TaskQueueQueryAndOwnTasksResponse_Task(ProtocolBuffer.ProtocolMessage):
  has_task_name_ = 0
  task_name_ = ""
  has_eta_usec_ = 0
  eta_usec_ = 0
  has_retry_count_ = 0
  retry_count_ = 0
  has_body_ = 0
  body_ = ""
  has_tag_ = 0
  tag_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def task_name(self): return self.task_name_

  def set_task_name(self, x):
    self.has_task_name_ = 1
    self.task_name_ = x

  def clear_task_name(self):
    if self.has_task_name_:
      self.has_task_name_ = 0
      self.task_name_ = ""

  def has_task_name(self): return self.has_task_name_

  def eta_usec(self): return self.eta_usec_

  def set_eta_usec(self, x):
    self.has_eta_usec_ = 1
    self.eta_usec_ = x

  def clear_eta_usec(self):
    if self.has_eta_usec_:
      self.has_eta_usec_ = 0
      self.eta_usec_ = 0

  def has_eta_usec(self): return self.has_eta_usec_

  def retry_count(self): return self.retry_count_

  def set_retry_count(self, x):
    self.has_retry_count_ = 1
    self.retry_count_ = x

  def clear_retry_count(self):
    if self.has_retry_count_:
      self.has_retry_count_ = 0
      self.retry_count_ = 0

  def has_retry_count(self): return self.has_retry_count_

  def body(self): return self.body_

  def set_body(self, x):
    self.has_body_ = 1
    self.body_ = x

  def clear_body(self):
    if self.has_body_:
      self.has_body_ = 0
      self.body_ = ""

  def has_body(self): return self.has_body_

  def tag(self): return self.tag_

  def set_tag(self, x):
    self.has_tag_ = 1
    self.tag_ = x

  def clear_tag(self):
    if self.has_tag_:
      self.has_tag_ = 0
      self.tag_ = ""

  def has_tag(self): return self.has_tag_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_task_name()): self.set_task_name(x.task_name())
    if (x.has_eta_usec()): self.set_eta_usec(x.eta_usec())
    if (x.has_retry_count()): self.set_retry_count(x.retry_count())
    if (x.has_body()): self.set_body(x.body())
    if (x.has_tag()): self.set_tag(x.tag())

  def Equals(self, x):
    if x is self: return 1
    if self.has_task_name_ != x.has_task_name_: return 0
    if self.has_task_name_ and self.task_name_ != x.task_name_: return 0
    if self.has_eta_usec_ != x.has_eta_usec_: return 0
    if self.has_eta_usec_ and self.eta_usec_ != x.eta_usec_: return 0
    if self.has_retry_count_ != x.has_retry_count_: return 0
    if self.has_retry_count_ and self.retry_count_ != x.retry_count_: return 0
    if self.has_body_ != x.has_body_: return 0
    if self.has_body_ and self.body_ != x.body_: return 0
    if self.has_tag_ != x.has_tag_: return 0
    if self.has_tag_ and self.tag_ != x.tag_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_task_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: task_name not set.')
    if (not self.has_eta_usec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: eta_usec not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.task_name_))
    n += self.lengthVarInt64(self.eta_usec_)
    if (self.has_retry_count_): n += 1 + self.lengthVarInt64(self.retry_count_)
    if (self.has_body_): n += 1 + self.lengthString(len(self.body_))
    if (self.has_tag_): n += 1 + self.lengthString(len(self.tag_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_task_name_):
      n += 1
      n += self.lengthString(len(self.task_name_))
    if (self.has_eta_usec_):
      n += 1
      n += self.lengthVarInt64(self.eta_usec_)
    if (self.has_retry_count_): n += 1 + self.lengthVarInt64(self.retry_count_)
    if (self.has_body_): n += 1 + self.lengthString(len(self.body_))
    if (self.has_tag_): n += 1 + self.lengthString(len(self.tag_))
    return n

  def Clear(self):
    self.clear_task_name()
    self.clear_eta_usec()
    self.clear_retry_count()
    self.clear_body()
    self.clear_tag()

  def OutputUnchecked(self, out):
    out.putVarInt32(18)
    out.putPrefixedString(self.task_name_)
    out.putVarInt32(24)
    out.putVarInt64(self.eta_usec_)
    if (self.has_retry_count_):
      out.putVarInt32(32)
      out.putVarInt32(self.retry_count_)
    if (self.has_body_):
      out.putVarInt32(42)
      out.putPrefixedString(self.body_)
    if (self.has_tag_):
      out.putVarInt32(50)
      out.putPrefixedString(self.tag_)

  def OutputPartial(self, out):
    if (self.has_task_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.task_name_)
    if (self.has_eta_usec_):
      out.putVarInt32(24)
      out.putVarInt64(self.eta_usec_)
    if (self.has_retry_count_):
      out.putVarInt32(32)
      out.putVarInt32(self.retry_count_)
    if (self.has_body_):
      out.putVarInt32(42)
      out.putPrefixedString(self.body_)
    if (self.has_tag_):
      out.putVarInt32(50)
      out.putPrefixedString(self.tag_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 12: break
      if tt == 18:
        self.set_task_name(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_eta_usec(d.getVarInt64())
        continue
      if tt == 32:
        self.set_retry_count(d.getVarInt32())
        continue
      if tt == 42:
        self.set_body(d.getPrefixedString())
        continue
      if tt == 50:
        self.set_tag(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_task_name_: res+=prefix+("task_name: %s\n" % self.DebugFormatString(self.task_name_))
    if self.has_eta_usec_: res+=prefix+("eta_usec: %s\n" % self.DebugFormatInt64(self.eta_usec_))
    if self.has_retry_count_: res+=prefix+("retry_count: %s\n" % self.DebugFormatInt32(self.retry_count_))
    if self.has_body_: res+=prefix+("body: %s\n" % self.DebugFormatString(self.body_))
    if self.has_tag_: res+=prefix+("tag: %s\n" % self.DebugFormatString(self.tag_))
    return res

class TaskQueueQueryAndOwnTasksResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.task_ = []
    if contents is not None: self.MergeFromString(contents)

  def task_size(self): return len(self.task_)
  def task_list(self): return self.task_

  def task(self, i):
    return self.task_[i]

  def mutable_task(self, i):
    return self.task_[i]

  def add_task(self):
    x = TaskQueueQueryAndOwnTasksResponse_Task()
    self.task_.append(x)
    return x

  def clear_task(self):
    self.task_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.task_size()): self.add_task().CopyFrom(x.task(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.task_) != len(x.task_): return 0
    for e1, e2 in zip(self.task_, x.task_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.task_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 2 * len(self.task_)
    for i in xrange(len(self.task_)): n += self.task_[i].ByteSize()
    return n

  def ByteSizePartial(self):
    n = 0
    n += 2 * len(self.task_)
    for i in xrange(len(self.task_)): n += self.task_[i].ByteSizePartial()
    return n

  def Clear(self):
    self.clear_task()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.task_)):
      out.putVarInt32(11)
      self.task_[i].OutputUnchecked(out)
      out.putVarInt32(12)

  def OutputPartial(self, out):
    for i in xrange(len(self.task_)):
      out.putVarInt32(11)
      self.task_[i].OutputPartial(out)
      out.putVarInt32(12)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 11:
        self.add_task().TryMerge(d)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.task_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Task%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kTaskGroup = 1
  kTasktask_name = 2
  kTasketa_usec = 3
  kTaskretry_count = 4
  kTaskbody = 5
  kTasktag = 6

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "Task",
    2: "task_name",
    3: "eta_usec",
    4: "retry_count",
    5: "body",
    6: "tag",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STARTGROUP,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.STRING,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueQueryAndOwnTasksResponse'
class TaskQueueModifyTaskLeaseRequest(ProtocolBuffer.ProtocolMessage):
  has_queue_name_ = 0
  queue_name_ = ""
  has_task_name_ = 0
  task_name_ = ""
  has_eta_usec_ = 0
  eta_usec_ = 0
  has_lease_seconds_ = 0
  lease_seconds_ = 0.0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def queue_name(self): return self.queue_name_

  def set_queue_name(self, x):
    self.has_queue_name_ = 1
    self.queue_name_ = x

  def clear_queue_name(self):
    if self.has_queue_name_:
      self.has_queue_name_ = 0
      self.queue_name_ = ""

  def has_queue_name(self): return self.has_queue_name_

  def task_name(self): return self.task_name_

  def set_task_name(self, x):
    self.has_task_name_ = 1
    self.task_name_ = x

  def clear_task_name(self):
    if self.has_task_name_:
      self.has_task_name_ = 0
      self.task_name_ = ""

  def has_task_name(self): return self.has_task_name_

  def eta_usec(self): return self.eta_usec_

  def set_eta_usec(self, x):
    self.has_eta_usec_ = 1
    self.eta_usec_ = x

  def clear_eta_usec(self):
    if self.has_eta_usec_:
      self.has_eta_usec_ = 0
      self.eta_usec_ = 0

  def has_eta_usec(self): return self.has_eta_usec_

  def lease_seconds(self): return self.lease_seconds_

  def set_lease_seconds(self, x):
    self.has_lease_seconds_ = 1
    self.lease_seconds_ = x

  def clear_lease_seconds(self):
    if self.has_lease_seconds_:
      self.has_lease_seconds_ = 0
      self.lease_seconds_ = 0.0

  def has_lease_seconds(self): return self.has_lease_seconds_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_queue_name()): self.set_queue_name(x.queue_name())
    if (x.has_task_name()): self.set_task_name(x.task_name())
    if (x.has_eta_usec()): self.set_eta_usec(x.eta_usec())
    if (x.has_lease_seconds()): self.set_lease_seconds(x.lease_seconds())

  def Equals(self, x):
    if x is self: return 1
    if self.has_queue_name_ != x.has_queue_name_: return 0
    if self.has_queue_name_ and self.queue_name_ != x.queue_name_: return 0
    if self.has_task_name_ != x.has_task_name_: return 0
    if self.has_task_name_ and self.task_name_ != x.task_name_: return 0
    if self.has_eta_usec_ != x.has_eta_usec_: return 0
    if self.has_eta_usec_ and self.eta_usec_ != x.eta_usec_: return 0
    if self.has_lease_seconds_ != x.has_lease_seconds_: return 0
    if self.has_lease_seconds_ and self.lease_seconds_ != x.lease_seconds_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_queue_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: queue_name not set.')
    if (not self.has_task_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: task_name not set.')
    if (not self.has_eta_usec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: eta_usec not set.')
    if (not self.has_lease_seconds_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: lease_seconds not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.queue_name_))
    n += self.lengthString(len(self.task_name_))
    n += self.lengthVarInt64(self.eta_usec_)
    return n + 12

  def ByteSizePartial(self):
    n = 0
    if (self.has_queue_name_):
      n += 1
      n += self.lengthString(len(self.queue_name_))
    if (self.has_task_name_):
      n += 1
      n += self.lengthString(len(self.task_name_))
    if (self.has_eta_usec_):
      n += 1
      n += self.lengthVarInt64(self.eta_usec_)
    if (self.has_lease_seconds_):
      n += 9
    return n

  def Clear(self):
    self.clear_queue_name()
    self.clear_task_name()
    self.clear_eta_usec()
    self.clear_lease_seconds()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.queue_name_)
    out.putVarInt32(18)
    out.putPrefixedString(self.task_name_)
    out.putVarInt32(24)
    out.putVarInt64(self.eta_usec_)
    out.putVarInt32(33)
    out.putDouble(self.lease_seconds_)

  def OutputPartial(self, out):
    if (self.has_queue_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.queue_name_)
    if (self.has_task_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.task_name_)
    if (self.has_eta_usec_):
      out.putVarInt32(24)
      out.putVarInt64(self.eta_usec_)
    if (self.has_lease_seconds_):
      out.putVarInt32(33)
      out.putDouble(self.lease_seconds_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_queue_name(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_task_name(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_eta_usec(d.getVarInt64())
        continue
      if tt == 33:
        self.set_lease_seconds(d.getDouble())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_queue_name_: res+=prefix+("queue_name: %s\n" % self.DebugFormatString(self.queue_name_))
    if self.has_task_name_: res+=prefix+("task_name: %s\n" % self.DebugFormatString(self.task_name_))
    if self.has_eta_usec_: res+=prefix+("eta_usec: %s\n" % self.DebugFormatInt64(self.eta_usec_))
    if self.has_lease_seconds_: res+=prefix+("lease_seconds: %s\n" % self.DebugFormat(self.lease_seconds_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kqueue_name = 1
  ktask_name = 2
  keta_usec = 3
  klease_seconds = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "queue_name",
    2: "task_name",
    3: "eta_usec",
    4: "lease_seconds",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.DOUBLE,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueModifyTaskLeaseRequest'
class TaskQueueModifyTaskLeaseResponse(ProtocolBuffer.ProtocolMessage):
  has_updated_eta_usec_ = 0
  updated_eta_usec_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def updated_eta_usec(self): return self.updated_eta_usec_

  def set_updated_eta_usec(self, x):
    self.has_updated_eta_usec_ = 1
    self.updated_eta_usec_ = x

  def clear_updated_eta_usec(self):
    if self.has_updated_eta_usec_:
      self.has_updated_eta_usec_ = 0
      self.updated_eta_usec_ = 0

  def has_updated_eta_usec(self): return self.has_updated_eta_usec_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_updated_eta_usec()): self.set_updated_eta_usec(x.updated_eta_usec())

  def Equals(self, x):
    if x is self: return 1
    if self.has_updated_eta_usec_ != x.has_updated_eta_usec_: return 0
    if self.has_updated_eta_usec_ and self.updated_eta_usec_ != x.updated_eta_usec_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_updated_eta_usec_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: updated_eta_usec not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.updated_eta_usec_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_updated_eta_usec_):
      n += 1
      n += self.lengthVarInt64(self.updated_eta_usec_)
    return n

  def Clear(self):
    self.clear_updated_eta_usec()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt64(self.updated_eta_usec_)

  def OutputPartial(self, out):
    if (self.has_updated_eta_usec_):
      out.putVarInt32(8)
      out.putVarInt64(self.updated_eta_usec_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_updated_eta_usec(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_updated_eta_usec_: res+=prefix+("updated_eta_usec: %s\n" % self.DebugFormatInt64(self.updated_eta_usec_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kupdated_eta_usec = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "updated_eta_usec",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.TaskQueueModifyTaskLeaseResponse'
if _extension_runtime:
  pass

__all__ = ['TaskQueueServiceError','TaskQueueRetryParameters','TaskQueueAcl','TaskQueueHttpHeader','TaskQueueMode','TaskQueueAddRequest','TaskQueueAddRequest_Header','TaskQueueAddRequest_CronTimetable','TaskQueueAddResponse','TaskQueueBulkAddRequest','TaskQueueBulkAddResponse','TaskQueueBulkAddResponse_TaskResult','TaskQueueDeleteRequest','TaskQueueDeleteResponse','TaskQueueForceRunRequest','TaskQueueForceRunResponse','TaskQueueUpdateQueueRequest','TaskQueueUpdateQueueResponse','TaskQueueFetchQueuesRequest','TaskQueueFetchQueuesResponse','TaskQueueFetchQueuesResponse_Queue','TaskQueueFetchQueueStatsRequest','TaskQueueScannerQueueInfo','TaskQueueFetchQueueStatsResponse','TaskQueueFetchQueueStatsResponse_QueueStats','TaskQueuePauseQueueRequest','TaskQueuePauseQueueResponse','TaskQueuePurgeQueueRequest','TaskQueuePurgeQueueResponse','TaskQueueDeleteQueueRequest','TaskQueueDeleteQueueResponse','TaskQueueDeleteGroupRequest','TaskQueueDeleteGroupResponse','TaskQueueQueryTasksRequest','TaskQueueQueryTasksResponse','TaskQueueQueryTasksResponse_TaskHeader','TaskQueueQueryTasksResponse_TaskCronTimetable','TaskQueueQueryTasksResponse_TaskRunLog','TaskQueueQueryTasksResponse_Task','TaskQueueFetchTaskRequest','TaskQueueFetchTaskResponse','TaskQueueUpdateStorageLimitRequest','TaskQueueUpdateStorageLimitResponse','TaskQueueQueryAndOwnTasksRequest','TaskQueueQueryAndOwnTasksResponse','TaskQueueQueryAndOwnTasksResponse_Task','TaskQueueModifyTaskLeaseRequest','TaskQueueModifyTaskLeaseResponse']
