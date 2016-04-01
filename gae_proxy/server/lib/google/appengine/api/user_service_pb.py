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

class UserServiceError(ProtocolBuffer.ProtocolMessage):


  OK           =    0
  REDIRECT_URL_TOO_LONG =    1
  NOT_ALLOWED  =    2
  OAUTH_INVALID_TOKEN =    3
  OAUTH_INVALID_REQUEST =    4
  OAUTH_ERROR  =    5

  _ErrorCode_NAMES = {
    0: "OK",
    1: "REDIRECT_URL_TOO_LONG",
    2: "NOT_ALLOWED",
    3: "OAUTH_INVALID_TOKEN",
    4: "OAUTH_INVALID_REQUEST",
    5: "OAUTH_ERROR",
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.UserServiceError'
class CreateLoginURLRequest(ProtocolBuffer.ProtocolMessage):
  has_destination_url_ = 0
  destination_url_ = ""
  has_auth_domain_ = 0
  auth_domain_ = ""
  has_federated_identity_ = 0
  federated_identity_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def destination_url(self): return self.destination_url_

  def set_destination_url(self, x):
    self.has_destination_url_ = 1
    self.destination_url_ = x

  def clear_destination_url(self):
    if self.has_destination_url_:
      self.has_destination_url_ = 0
      self.destination_url_ = ""

  def has_destination_url(self): return self.has_destination_url_

  def auth_domain(self): return self.auth_domain_

  def set_auth_domain(self, x):
    self.has_auth_domain_ = 1
    self.auth_domain_ = x

  def clear_auth_domain(self):
    if self.has_auth_domain_:
      self.has_auth_domain_ = 0
      self.auth_domain_ = ""

  def has_auth_domain(self): return self.has_auth_domain_

  def federated_identity(self): return self.federated_identity_

  def set_federated_identity(self, x):
    self.has_federated_identity_ = 1
    self.federated_identity_ = x

  def clear_federated_identity(self):
    if self.has_federated_identity_:
      self.has_federated_identity_ = 0
      self.federated_identity_ = ""

  def has_federated_identity(self): return self.has_federated_identity_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_destination_url()): self.set_destination_url(x.destination_url())
    if (x.has_auth_domain()): self.set_auth_domain(x.auth_domain())
    if (x.has_federated_identity()): self.set_federated_identity(x.federated_identity())

  def Equals(self, x):
    if x is self: return 1
    if self.has_destination_url_ != x.has_destination_url_: return 0
    if self.has_destination_url_ and self.destination_url_ != x.destination_url_: return 0
    if self.has_auth_domain_ != x.has_auth_domain_: return 0
    if self.has_auth_domain_ and self.auth_domain_ != x.auth_domain_: return 0
    if self.has_federated_identity_ != x.has_federated_identity_: return 0
    if self.has_federated_identity_ and self.federated_identity_ != x.federated_identity_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_destination_url_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: destination_url not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.destination_url_))
    if (self.has_auth_domain_): n += 1 + self.lengthString(len(self.auth_domain_))
    if (self.has_federated_identity_): n += 1 + self.lengthString(len(self.federated_identity_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_destination_url_):
      n += 1
      n += self.lengthString(len(self.destination_url_))
    if (self.has_auth_domain_): n += 1 + self.lengthString(len(self.auth_domain_))
    if (self.has_federated_identity_): n += 1 + self.lengthString(len(self.federated_identity_))
    return n

  def Clear(self):
    self.clear_destination_url()
    self.clear_auth_domain()
    self.clear_federated_identity()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.destination_url_)
    if (self.has_auth_domain_):
      out.putVarInt32(18)
      out.putPrefixedString(self.auth_domain_)
    if (self.has_federated_identity_):
      out.putVarInt32(26)
      out.putPrefixedString(self.federated_identity_)

  def OutputPartial(self, out):
    if (self.has_destination_url_):
      out.putVarInt32(10)
      out.putPrefixedString(self.destination_url_)
    if (self.has_auth_domain_):
      out.putVarInt32(18)
      out.putPrefixedString(self.auth_domain_)
    if (self.has_federated_identity_):
      out.putVarInt32(26)
      out.putPrefixedString(self.federated_identity_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_destination_url(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_auth_domain(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_federated_identity(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_destination_url_: res+=prefix+("destination_url: %s\n" % self.DebugFormatString(self.destination_url_))
    if self.has_auth_domain_: res+=prefix+("auth_domain: %s\n" % self.DebugFormatString(self.auth_domain_))
    if self.has_federated_identity_: res+=prefix+("federated_identity: %s\n" % self.DebugFormatString(self.federated_identity_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kdestination_url = 1
  kauth_domain = 2
  kfederated_identity = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "destination_url",
    2: "auth_domain",
    3: "federated_identity",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CreateLoginURLRequest'
class CreateLoginURLResponse(ProtocolBuffer.ProtocolMessage):
  has_login_url_ = 0
  login_url_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def login_url(self): return self.login_url_

  def set_login_url(self, x):
    self.has_login_url_ = 1
    self.login_url_ = x

  def clear_login_url(self):
    if self.has_login_url_:
      self.has_login_url_ = 0
      self.login_url_ = ""

  def has_login_url(self): return self.has_login_url_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_login_url()): self.set_login_url(x.login_url())

  def Equals(self, x):
    if x is self: return 1
    if self.has_login_url_ != x.has_login_url_: return 0
    if self.has_login_url_ and self.login_url_ != x.login_url_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_login_url_): n += 1 + self.lengthString(len(self.login_url_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_login_url_): n += 1 + self.lengthString(len(self.login_url_))
    return n

  def Clear(self):
    self.clear_login_url()

  def OutputUnchecked(self, out):
    if (self.has_login_url_):
      out.putVarInt32(10)
      out.putPrefixedString(self.login_url_)

  def OutputPartial(self, out):
    if (self.has_login_url_):
      out.putVarInt32(10)
      out.putPrefixedString(self.login_url_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_login_url(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_login_url_: res+=prefix+("login_url: %s\n" % self.DebugFormatString(self.login_url_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  klogin_url = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "login_url",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CreateLoginURLResponse'
class CreateLogoutURLRequest(ProtocolBuffer.ProtocolMessage):
  has_destination_url_ = 0
  destination_url_ = ""
  has_auth_domain_ = 0
  auth_domain_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def destination_url(self): return self.destination_url_

  def set_destination_url(self, x):
    self.has_destination_url_ = 1
    self.destination_url_ = x

  def clear_destination_url(self):
    if self.has_destination_url_:
      self.has_destination_url_ = 0
      self.destination_url_ = ""

  def has_destination_url(self): return self.has_destination_url_

  def auth_domain(self): return self.auth_domain_

  def set_auth_domain(self, x):
    self.has_auth_domain_ = 1
    self.auth_domain_ = x

  def clear_auth_domain(self):
    if self.has_auth_domain_:
      self.has_auth_domain_ = 0
      self.auth_domain_ = ""

  def has_auth_domain(self): return self.has_auth_domain_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_destination_url()): self.set_destination_url(x.destination_url())
    if (x.has_auth_domain()): self.set_auth_domain(x.auth_domain())

  def Equals(self, x):
    if x is self: return 1
    if self.has_destination_url_ != x.has_destination_url_: return 0
    if self.has_destination_url_ and self.destination_url_ != x.destination_url_: return 0
    if self.has_auth_domain_ != x.has_auth_domain_: return 0
    if self.has_auth_domain_ and self.auth_domain_ != x.auth_domain_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_destination_url_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: destination_url not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.destination_url_))
    if (self.has_auth_domain_): n += 1 + self.lengthString(len(self.auth_domain_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_destination_url_):
      n += 1
      n += self.lengthString(len(self.destination_url_))
    if (self.has_auth_domain_): n += 1 + self.lengthString(len(self.auth_domain_))
    return n

  def Clear(self):
    self.clear_destination_url()
    self.clear_auth_domain()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.destination_url_)
    if (self.has_auth_domain_):
      out.putVarInt32(18)
      out.putPrefixedString(self.auth_domain_)

  def OutputPartial(self, out):
    if (self.has_destination_url_):
      out.putVarInt32(10)
      out.putPrefixedString(self.destination_url_)
    if (self.has_auth_domain_):
      out.putVarInt32(18)
      out.putPrefixedString(self.auth_domain_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_destination_url(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_auth_domain(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_destination_url_: res+=prefix+("destination_url: %s\n" % self.DebugFormatString(self.destination_url_))
    if self.has_auth_domain_: res+=prefix+("auth_domain: %s\n" % self.DebugFormatString(self.auth_domain_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kdestination_url = 1
  kauth_domain = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "destination_url",
    2: "auth_domain",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CreateLogoutURLRequest'
class CreateLogoutURLResponse(ProtocolBuffer.ProtocolMessage):
  has_logout_url_ = 0
  logout_url_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def logout_url(self): return self.logout_url_

  def set_logout_url(self, x):
    self.has_logout_url_ = 1
    self.logout_url_ = x

  def clear_logout_url(self):
    if self.has_logout_url_:
      self.has_logout_url_ = 0
      self.logout_url_ = ""

  def has_logout_url(self): return self.has_logout_url_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_logout_url()): self.set_logout_url(x.logout_url())

  def Equals(self, x):
    if x is self: return 1
    if self.has_logout_url_ != x.has_logout_url_: return 0
    if self.has_logout_url_ and self.logout_url_ != x.logout_url_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_logout_url_): n += 1 + self.lengthString(len(self.logout_url_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_logout_url_): n += 1 + self.lengthString(len(self.logout_url_))
    return n

  def Clear(self):
    self.clear_logout_url()

  def OutputUnchecked(self, out):
    if (self.has_logout_url_):
      out.putVarInt32(10)
      out.putPrefixedString(self.logout_url_)

  def OutputPartial(self, out):
    if (self.has_logout_url_):
      out.putVarInt32(10)
      out.putPrefixedString(self.logout_url_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_logout_url(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_logout_url_: res+=prefix+("logout_url: %s\n" % self.DebugFormatString(self.logout_url_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  klogout_url = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "logout_url",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CreateLogoutURLResponse'
class GetOAuthUserRequest(ProtocolBuffer.ProtocolMessage):
  has_scope_ = 0
  scope_ = ""
  has_request_writer_permission_ = 0
  request_writer_permission_ = 0

  def __init__(self, contents=None):
    self.scopes_ = []
    if contents is not None: self.MergeFromString(contents)

  def scope(self): return self.scope_

  def set_scope(self, x):
    self.has_scope_ = 1
    self.scope_ = x

  def clear_scope(self):
    if self.has_scope_:
      self.has_scope_ = 0
      self.scope_ = ""

  def has_scope(self): return self.has_scope_

  def scopes_size(self): return len(self.scopes_)
  def scopes_list(self): return self.scopes_

  def scopes(self, i):
    return self.scopes_[i]

  def set_scopes(self, i, x):
    self.scopes_[i] = x

  def add_scopes(self, x):
    self.scopes_.append(x)

  def clear_scopes(self):
    self.scopes_ = []

  def request_writer_permission(self): return self.request_writer_permission_

  def set_request_writer_permission(self, x):
    self.has_request_writer_permission_ = 1
    self.request_writer_permission_ = x

  def clear_request_writer_permission(self):
    if self.has_request_writer_permission_:
      self.has_request_writer_permission_ = 0
      self.request_writer_permission_ = 0

  def has_request_writer_permission(self): return self.has_request_writer_permission_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_scope()): self.set_scope(x.scope())
    for i in xrange(x.scopes_size()): self.add_scopes(x.scopes(i))
    if (x.has_request_writer_permission()): self.set_request_writer_permission(x.request_writer_permission())

  def Equals(self, x):
    if x is self: return 1
    if self.has_scope_ != x.has_scope_: return 0
    if self.has_scope_ and self.scope_ != x.scope_: return 0
    if len(self.scopes_) != len(x.scopes_): return 0
    for e1, e2 in zip(self.scopes_, x.scopes_):
      if e1 != e2: return 0
    if self.has_request_writer_permission_ != x.has_request_writer_permission_: return 0
    if self.has_request_writer_permission_ and self.request_writer_permission_ != x.request_writer_permission_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_scope_): n += 1 + self.lengthString(len(self.scope_))
    n += 1 * len(self.scopes_)
    for i in xrange(len(self.scopes_)): n += self.lengthString(len(self.scopes_[i]))
    if (self.has_request_writer_permission_): n += 2
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_scope_): n += 1 + self.lengthString(len(self.scope_))
    n += 1 * len(self.scopes_)
    for i in xrange(len(self.scopes_)): n += self.lengthString(len(self.scopes_[i]))
    if (self.has_request_writer_permission_): n += 2
    return n

  def Clear(self):
    self.clear_scope()
    self.clear_scopes()
    self.clear_request_writer_permission()

  def OutputUnchecked(self, out):
    if (self.has_scope_):
      out.putVarInt32(10)
      out.putPrefixedString(self.scope_)
    for i in xrange(len(self.scopes_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.scopes_[i])
    if (self.has_request_writer_permission_):
      out.putVarInt32(24)
      out.putBoolean(self.request_writer_permission_)

  def OutputPartial(self, out):
    if (self.has_scope_):
      out.putVarInt32(10)
      out.putPrefixedString(self.scope_)
    for i in xrange(len(self.scopes_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.scopes_[i])
    if (self.has_request_writer_permission_):
      out.putVarInt32(24)
      out.putBoolean(self.request_writer_permission_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_scope(d.getPrefixedString())
        continue
      if tt == 18:
        self.add_scopes(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_request_writer_permission(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_scope_: res+=prefix+("scope: %s\n" % self.DebugFormatString(self.scope_))
    cnt=0
    for e in self.scopes_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("scopes%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_request_writer_permission_: res+=prefix+("request_writer_permission: %s\n" % self.DebugFormatBool(self.request_writer_permission_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kscope = 1
  kscopes = 2
  krequest_writer_permission = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "scope",
    2: "scopes",
    3: "request_writer_permission",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetOAuthUserRequest'
class GetOAuthUserResponse(ProtocolBuffer.ProtocolMessage):
  has_email_ = 0
  email_ = ""
  has_user_id_ = 0
  user_id_ = ""
  has_auth_domain_ = 0
  auth_domain_ = ""
  has_user_organization_ = 0
  user_organization_ = ""
  has_is_admin_ = 0
  is_admin_ = 0
  has_client_id_ = 0
  client_id_ = ""
  has_is_project_writer_ = 0
  is_project_writer_ = 0

  def __init__(self, contents=None):
    self.scopes_ = []
    if contents is not None: self.MergeFromString(contents)

  def email(self): return self.email_

  def set_email(self, x):
    self.has_email_ = 1
    self.email_ = x

  def clear_email(self):
    if self.has_email_:
      self.has_email_ = 0
      self.email_ = ""

  def has_email(self): return self.has_email_

  def user_id(self): return self.user_id_

  def set_user_id(self, x):
    self.has_user_id_ = 1
    self.user_id_ = x

  def clear_user_id(self):
    if self.has_user_id_:
      self.has_user_id_ = 0
      self.user_id_ = ""

  def has_user_id(self): return self.has_user_id_

  def auth_domain(self): return self.auth_domain_

  def set_auth_domain(self, x):
    self.has_auth_domain_ = 1
    self.auth_domain_ = x

  def clear_auth_domain(self):
    if self.has_auth_domain_:
      self.has_auth_domain_ = 0
      self.auth_domain_ = ""

  def has_auth_domain(self): return self.has_auth_domain_

  def user_organization(self): return self.user_organization_

  def set_user_organization(self, x):
    self.has_user_organization_ = 1
    self.user_organization_ = x

  def clear_user_organization(self):
    if self.has_user_organization_:
      self.has_user_organization_ = 0
      self.user_organization_ = ""

  def has_user_organization(self): return self.has_user_organization_

  def is_admin(self): return self.is_admin_

  def set_is_admin(self, x):
    self.has_is_admin_ = 1
    self.is_admin_ = x

  def clear_is_admin(self):
    if self.has_is_admin_:
      self.has_is_admin_ = 0
      self.is_admin_ = 0

  def has_is_admin(self): return self.has_is_admin_

  def client_id(self): return self.client_id_

  def set_client_id(self, x):
    self.has_client_id_ = 1
    self.client_id_ = x

  def clear_client_id(self):
    if self.has_client_id_:
      self.has_client_id_ = 0
      self.client_id_ = ""

  def has_client_id(self): return self.has_client_id_

  def scopes_size(self): return len(self.scopes_)
  def scopes_list(self): return self.scopes_

  def scopes(self, i):
    return self.scopes_[i]

  def set_scopes(self, i, x):
    self.scopes_[i] = x

  def add_scopes(self, x):
    self.scopes_.append(x)

  def clear_scopes(self):
    self.scopes_ = []

  def is_project_writer(self): return self.is_project_writer_

  def set_is_project_writer(self, x):
    self.has_is_project_writer_ = 1
    self.is_project_writer_ = x

  def clear_is_project_writer(self):
    if self.has_is_project_writer_:
      self.has_is_project_writer_ = 0
      self.is_project_writer_ = 0

  def has_is_project_writer(self): return self.has_is_project_writer_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_email()): self.set_email(x.email())
    if (x.has_user_id()): self.set_user_id(x.user_id())
    if (x.has_auth_domain()): self.set_auth_domain(x.auth_domain())
    if (x.has_user_organization()): self.set_user_organization(x.user_organization())
    if (x.has_is_admin()): self.set_is_admin(x.is_admin())
    if (x.has_client_id()): self.set_client_id(x.client_id())
    for i in xrange(x.scopes_size()): self.add_scopes(x.scopes(i))
    if (x.has_is_project_writer()): self.set_is_project_writer(x.is_project_writer())

  def Equals(self, x):
    if x is self: return 1
    if self.has_email_ != x.has_email_: return 0
    if self.has_email_ and self.email_ != x.email_: return 0
    if self.has_user_id_ != x.has_user_id_: return 0
    if self.has_user_id_ and self.user_id_ != x.user_id_: return 0
    if self.has_auth_domain_ != x.has_auth_domain_: return 0
    if self.has_auth_domain_ and self.auth_domain_ != x.auth_domain_: return 0
    if self.has_user_organization_ != x.has_user_organization_: return 0
    if self.has_user_organization_ and self.user_organization_ != x.user_organization_: return 0
    if self.has_is_admin_ != x.has_is_admin_: return 0
    if self.has_is_admin_ and self.is_admin_ != x.is_admin_: return 0
    if self.has_client_id_ != x.has_client_id_: return 0
    if self.has_client_id_ and self.client_id_ != x.client_id_: return 0
    if len(self.scopes_) != len(x.scopes_): return 0
    for e1, e2 in zip(self.scopes_, x.scopes_):
      if e1 != e2: return 0
    if self.has_is_project_writer_ != x.has_is_project_writer_: return 0
    if self.has_is_project_writer_ and self.is_project_writer_ != x.is_project_writer_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_email_): n += 1 + self.lengthString(len(self.email_))
    if (self.has_user_id_): n += 1 + self.lengthString(len(self.user_id_))
    if (self.has_auth_domain_): n += 1 + self.lengthString(len(self.auth_domain_))
    if (self.has_user_organization_): n += 1 + self.lengthString(len(self.user_organization_))
    if (self.has_is_admin_): n += 2
    if (self.has_client_id_): n += 1 + self.lengthString(len(self.client_id_))
    n += 1 * len(self.scopes_)
    for i in xrange(len(self.scopes_)): n += self.lengthString(len(self.scopes_[i]))
    if (self.has_is_project_writer_): n += 2
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_email_): n += 1 + self.lengthString(len(self.email_))
    if (self.has_user_id_): n += 1 + self.lengthString(len(self.user_id_))
    if (self.has_auth_domain_): n += 1 + self.lengthString(len(self.auth_domain_))
    if (self.has_user_organization_): n += 1 + self.lengthString(len(self.user_organization_))
    if (self.has_is_admin_): n += 2
    if (self.has_client_id_): n += 1 + self.lengthString(len(self.client_id_))
    n += 1 * len(self.scopes_)
    for i in xrange(len(self.scopes_)): n += self.lengthString(len(self.scopes_[i]))
    if (self.has_is_project_writer_): n += 2
    return n

  def Clear(self):
    self.clear_email()
    self.clear_user_id()
    self.clear_auth_domain()
    self.clear_user_organization()
    self.clear_is_admin()
    self.clear_client_id()
    self.clear_scopes()
    self.clear_is_project_writer()

  def OutputUnchecked(self, out):
    if (self.has_email_):
      out.putVarInt32(10)
      out.putPrefixedString(self.email_)
    if (self.has_user_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.user_id_)
    if (self.has_auth_domain_):
      out.putVarInt32(26)
      out.putPrefixedString(self.auth_domain_)
    if (self.has_user_organization_):
      out.putVarInt32(34)
      out.putPrefixedString(self.user_organization_)
    if (self.has_is_admin_):
      out.putVarInt32(40)
      out.putBoolean(self.is_admin_)
    if (self.has_client_id_):
      out.putVarInt32(50)
      out.putPrefixedString(self.client_id_)
    for i in xrange(len(self.scopes_)):
      out.putVarInt32(58)
      out.putPrefixedString(self.scopes_[i])
    if (self.has_is_project_writer_):
      out.putVarInt32(64)
      out.putBoolean(self.is_project_writer_)

  def OutputPartial(self, out):
    if (self.has_email_):
      out.putVarInt32(10)
      out.putPrefixedString(self.email_)
    if (self.has_user_id_):
      out.putVarInt32(18)
      out.putPrefixedString(self.user_id_)
    if (self.has_auth_domain_):
      out.putVarInt32(26)
      out.putPrefixedString(self.auth_domain_)
    if (self.has_user_organization_):
      out.putVarInt32(34)
      out.putPrefixedString(self.user_organization_)
    if (self.has_is_admin_):
      out.putVarInt32(40)
      out.putBoolean(self.is_admin_)
    if (self.has_client_id_):
      out.putVarInt32(50)
      out.putPrefixedString(self.client_id_)
    for i in xrange(len(self.scopes_)):
      out.putVarInt32(58)
      out.putPrefixedString(self.scopes_[i])
    if (self.has_is_project_writer_):
      out.putVarInt32(64)
      out.putBoolean(self.is_project_writer_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_email(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_user_id(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_auth_domain(d.getPrefixedString())
        continue
      if tt == 34:
        self.set_user_organization(d.getPrefixedString())
        continue
      if tt == 40:
        self.set_is_admin(d.getBoolean())
        continue
      if tt == 50:
        self.set_client_id(d.getPrefixedString())
        continue
      if tt == 58:
        self.add_scopes(d.getPrefixedString())
        continue
      if tt == 64:
        self.set_is_project_writer(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_email_: res+=prefix+("email: %s\n" % self.DebugFormatString(self.email_))
    if self.has_user_id_: res+=prefix+("user_id: %s\n" % self.DebugFormatString(self.user_id_))
    if self.has_auth_domain_: res+=prefix+("auth_domain: %s\n" % self.DebugFormatString(self.auth_domain_))
    if self.has_user_organization_: res+=prefix+("user_organization: %s\n" % self.DebugFormatString(self.user_organization_))
    if self.has_is_admin_: res+=prefix+("is_admin: %s\n" % self.DebugFormatBool(self.is_admin_))
    if self.has_client_id_: res+=prefix+("client_id: %s\n" % self.DebugFormatString(self.client_id_))
    cnt=0
    for e in self.scopes_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("scopes%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_is_project_writer_: res+=prefix+("is_project_writer: %s\n" % self.DebugFormatBool(self.is_project_writer_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kemail = 1
  kuser_id = 2
  kauth_domain = 3
  kuser_organization = 4
  kis_admin = 5
  kclient_id = 6
  kscopes = 7
  kis_project_writer = 8

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "email",
    2: "user_id",
    3: "auth_domain",
    4: "user_organization",
    5: "is_admin",
    6: "client_id",
    7: "scopes",
    8: "is_project_writer",
  }, 8)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.STRING,
    7: ProtocolBuffer.Encoder.STRING,
    8: ProtocolBuffer.Encoder.NUMERIC,
  }, 8, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetOAuthUserResponse'
class CheckOAuthSignatureRequest(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CheckOAuthSignatureRequest'
class CheckOAuthSignatureResponse(ProtocolBuffer.ProtocolMessage):
  has_oauth_consumer_key_ = 0
  oauth_consumer_key_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def oauth_consumer_key(self): return self.oauth_consumer_key_

  def set_oauth_consumer_key(self, x):
    self.has_oauth_consumer_key_ = 1
    self.oauth_consumer_key_ = x

  def clear_oauth_consumer_key(self):
    if self.has_oauth_consumer_key_:
      self.has_oauth_consumer_key_ = 0
      self.oauth_consumer_key_ = ""

  def has_oauth_consumer_key(self): return self.has_oauth_consumer_key_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_oauth_consumer_key()): self.set_oauth_consumer_key(x.oauth_consumer_key())

  def Equals(self, x):
    if x is self: return 1
    if self.has_oauth_consumer_key_ != x.has_oauth_consumer_key_: return 0
    if self.has_oauth_consumer_key_ and self.oauth_consumer_key_ != x.oauth_consumer_key_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_oauth_consumer_key_): n += 1 + self.lengthString(len(self.oauth_consumer_key_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_oauth_consumer_key_): n += 1 + self.lengthString(len(self.oauth_consumer_key_))
    return n

  def Clear(self):
    self.clear_oauth_consumer_key()

  def OutputUnchecked(self, out):
    if (self.has_oauth_consumer_key_):
      out.putVarInt32(10)
      out.putPrefixedString(self.oauth_consumer_key_)

  def OutputPartial(self, out):
    if (self.has_oauth_consumer_key_):
      out.putVarInt32(10)
      out.putPrefixedString(self.oauth_consumer_key_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_oauth_consumer_key(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_oauth_consumer_key_: res+=prefix+("oauth_consumer_key: %s\n" % self.DebugFormatString(self.oauth_consumer_key_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  koauth_consumer_key = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "oauth_consumer_key",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CheckOAuthSignatureResponse'
if _extension_runtime:
  pass

__all__ = ['UserServiceError','CreateLoginURLRequest','CreateLoginURLResponse','CreateLogoutURLRequest','CreateLogoutURLResponse','GetOAuthUserRequest','GetOAuthUserResponse','CheckOAuthSignatureRequest','CheckOAuthSignatureResponse']
