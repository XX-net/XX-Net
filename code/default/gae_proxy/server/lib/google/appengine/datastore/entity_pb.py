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

class PropertyValue_ReferenceValuePathElement(ProtocolBuffer.ProtocolMessage):
  has_type_ = 0
  type_ = ""
  has_id_ = 0
  id_ = 0
  has_name_ = 0
  name_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def type(self): return self.type_

  def set_type(self, x):
    self.has_type_ = 1
    self.type_ = x

  def clear_type(self):
    if self.has_type_:
      self.has_type_ = 0
      self.type_ = ""

  def has_type(self): return self.has_type_

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
    if (x.has_type()): self.set_type(x.type())
    if (x.has_id()): self.set_id(x.id())
    if (x.has_name()): self.set_name(x.name())

  def Equals(self, x):
    if x is self: return 1
    if self.has_type_ != x.has_type_: return 0
    if self.has_type_ and self.type_ != x.type_: return 0
    if self.has_id_ != x.has_id_: return 0
    if self.has_id_ and self.id_ != x.id_: return 0
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_type_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: type not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.type_))
    if (self.has_id_): n += 2 + self.lengthVarInt64(self.id_)
    if (self.has_name_): n += 2 + self.lengthString(len(self.name_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_type_):
      n += 1
      n += self.lengthString(len(self.type_))
    if (self.has_id_): n += 2 + self.lengthVarInt64(self.id_)
    if (self.has_name_): n += 2 + self.lengthString(len(self.name_))
    return n

  def Clear(self):
    self.clear_type()
    self.clear_id()
    self.clear_name()

  def OutputUnchecked(self, out):
    out.putVarInt32(122)
    out.putPrefixedString(self.type_)
    if (self.has_id_):
      out.putVarInt32(128)
      out.putVarInt64(self.id_)
    if (self.has_name_):
      out.putVarInt32(138)
      out.putPrefixedString(self.name_)

  def OutputPartial(self, out):
    if (self.has_type_):
      out.putVarInt32(122)
      out.putPrefixedString(self.type_)
    if (self.has_id_):
      out.putVarInt32(128)
      out.putVarInt64(self.id_)
    if (self.has_name_):
      out.putVarInt32(138)
      out.putPrefixedString(self.name_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 116: break
      if tt == 122:
        self.set_type(d.getPrefixedString())
        continue
      if tt == 128:
        self.set_id(d.getVarInt64())
        continue
      if tt == 138:
        self.set_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_type_: res+=prefix+("type: %s\n" % self.DebugFormatString(self.type_))
    if self.has_id_: res+=prefix+("id: %s\n" % self.DebugFormatInt64(self.id_))
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    return res

class PropertyValue_PointValue(ProtocolBuffer.ProtocolMessage):
  has_x_ = 0
  x_ = 0.0
  has_y_ = 0
  y_ = 0.0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def x(self): return self.x_

  def set_x(self, x):
    self.has_x_ = 1
    self.x_ = x

  def clear_x(self):
    if self.has_x_:
      self.has_x_ = 0
      self.x_ = 0.0

  def has_x(self): return self.has_x_

  def y(self): return self.y_

  def set_y(self, x):
    self.has_y_ = 1
    self.y_ = x

  def clear_y(self):
    if self.has_y_:
      self.has_y_ = 0
      self.y_ = 0.0

  def has_y(self): return self.has_y_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_x()): self.set_x(x.x())
    if (x.has_y()): self.set_y(x.y())

  def Equals(self, x):
    if x is self: return 1
    if self.has_x_ != x.has_x_: return 0
    if self.has_x_ and self.x_ != x.x_: return 0
    if self.has_y_ != x.has_y_: return 0
    if self.has_y_ and self.y_ != x.y_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_x_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: x not set.')
    if (not self.has_y_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: y not set.')
    return initialized

  def ByteSize(self):
    n = 0
    return n + 18

  def ByteSizePartial(self):
    n = 0
    if (self.has_x_):
      n += 9
    if (self.has_y_):
      n += 9
    return n

  def Clear(self):
    self.clear_x()
    self.clear_y()

  def OutputUnchecked(self, out):
    out.putVarInt32(49)
    out.putDouble(self.x_)
    out.putVarInt32(57)
    out.putDouble(self.y_)

  def OutputPartial(self, out):
    if (self.has_x_):
      out.putVarInt32(49)
      out.putDouble(self.x_)
    if (self.has_y_):
      out.putVarInt32(57)
      out.putDouble(self.y_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 44: break
      if tt == 49:
        self.set_x(d.getDouble())
        continue
      if tt == 57:
        self.set_y(d.getDouble())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_x_: res+=prefix+("x: %s\n" % self.DebugFormat(self.x_))
    if self.has_y_: res+=prefix+("y: %s\n" % self.DebugFormat(self.y_))
    return res

class PropertyValue_UserValue(ProtocolBuffer.ProtocolMessage):
  has_email_ = 0
  email_ = ""
  has_auth_domain_ = 0
  auth_domain_ = ""
  has_nickname_ = 0
  nickname_ = ""
  has_gaiaid_ = 0
  gaiaid_ = 0
  has_obfuscated_gaiaid_ = 0
  obfuscated_gaiaid_ = ""
  has_federated_identity_ = 0
  federated_identity_ = ""
  has_federated_provider_ = 0
  federated_provider_ = ""

  def __init__(self, contents=None):
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

  def auth_domain(self): return self.auth_domain_

  def set_auth_domain(self, x):
    self.has_auth_domain_ = 1
    self.auth_domain_ = x

  def clear_auth_domain(self):
    if self.has_auth_domain_:
      self.has_auth_domain_ = 0
      self.auth_domain_ = ""

  def has_auth_domain(self): return self.has_auth_domain_

  def nickname(self): return self.nickname_

  def set_nickname(self, x):
    self.has_nickname_ = 1
    self.nickname_ = x

  def clear_nickname(self):
    if self.has_nickname_:
      self.has_nickname_ = 0
      self.nickname_ = ""

  def has_nickname(self): return self.has_nickname_

  def gaiaid(self): return self.gaiaid_

  def set_gaiaid(self, x):
    self.has_gaiaid_ = 1
    self.gaiaid_ = x

  def clear_gaiaid(self):
    if self.has_gaiaid_:
      self.has_gaiaid_ = 0
      self.gaiaid_ = 0

  def has_gaiaid(self): return self.has_gaiaid_

  def obfuscated_gaiaid(self): return self.obfuscated_gaiaid_

  def set_obfuscated_gaiaid(self, x):
    self.has_obfuscated_gaiaid_ = 1
    self.obfuscated_gaiaid_ = x

  def clear_obfuscated_gaiaid(self):
    if self.has_obfuscated_gaiaid_:
      self.has_obfuscated_gaiaid_ = 0
      self.obfuscated_gaiaid_ = ""

  def has_obfuscated_gaiaid(self): return self.has_obfuscated_gaiaid_

  def federated_identity(self): return self.federated_identity_

  def set_federated_identity(self, x):
    self.has_federated_identity_ = 1
    self.federated_identity_ = x

  def clear_federated_identity(self):
    if self.has_federated_identity_:
      self.has_federated_identity_ = 0
      self.federated_identity_ = ""

  def has_federated_identity(self): return self.has_federated_identity_

  def federated_provider(self): return self.federated_provider_

  def set_federated_provider(self, x):
    self.has_federated_provider_ = 1
    self.federated_provider_ = x

  def clear_federated_provider(self):
    if self.has_federated_provider_:
      self.has_federated_provider_ = 0
      self.federated_provider_ = ""

  def has_federated_provider(self): return self.has_federated_provider_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_email()): self.set_email(x.email())
    if (x.has_auth_domain()): self.set_auth_domain(x.auth_domain())
    if (x.has_nickname()): self.set_nickname(x.nickname())
    if (x.has_gaiaid()): self.set_gaiaid(x.gaiaid())
    if (x.has_obfuscated_gaiaid()): self.set_obfuscated_gaiaid(x.obfuscated_gaiaid())
    if (x.has_federated_identity()): self.set_federated_identity(x.federated_identity())
    if (x.has_federated_provider()): self.set_federated_provider(x.federated_provider())

  def Equals(self, x):
    if x is self: return 1
    if self.has_email_ != x.has_email_: return 0
    if self.has_email_ and self.email_ != x.email_: return 0
    if self.has_auth_domain_ != x.has_auth_domain_: return 0
    if self.has_auth_domain_ and self.auth_domain_ != x.auth_domain_: return 0
    if self.has_nickname_ != x.has_nickname_: return 0
    if self.has_nickname_ and self.nickname_ != x.nickname_: return 0
    if self.has_gaiaid_ != x.has_gaiaid_: return 0
    if self.has_gaiaid_ and self.gaiaid_ != x.gaiaid_: return 0
    if self.has_obfuscated_gaiaid_ != x.has_obfuscated_gaiaid_: return 0
    if self.has_obfuscated_gaiaid_ and self.obfuscated_gaiaid_ != x.obfuscated_gaiaid_: return 0
    if self.has_federated_identity_ != x.has_federated_identity_: return 0
    if self.has_federated_identity_ and self.federated_identity_ != x.federated_identity_: return 0
    if self.has_federated_provider_ != x.has_federated_provider_: return 0
    if self.has_federated_provider_ and self.federated_provider_ != x.federated_provider_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_email_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: email not set.')
    if (not self.has_auth_domain_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: auth_domain not set.')
    if (not self.has_gaiaid_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: gaiaid not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.email_))
    n += self.lengthString(len(self.auth_domain_))
    if (self.has_nickname_): n += 1 + self.lengthString(len(self.nickname_))
    n += self.lengthVarInt64(self.gaiaid_)
    if (self.has_obfuscated_gaiaid_): n += 2 + self.lengthString(len(self.obfuscated_gaiaid_))
    if (self.has_federated_identity_): n += 2 + self.lengthString(len(self.federated_identity_))
    if (self.has_federated_provider_): n += 2 + self.lengthString(len(self.federated_provider_))
    return n + 4

  def ByteSizePartial(self):
    n = 0
    if (self.has_email_):
      n += 1
      n += self.lengthString(len(self.email_))
    if (self.has_auth_domain_):
      n += 1
      n += self.lengthString(len(self.auth_domain_))
    if (self.has_nickname_): n += 1 + self.lengthString(len(self.nickname_))
    if (self.has_gaiaid_):
      n += 2
      n += self.lengthVarInt64(self.gaiaid_)
    if (self.has_obfuscated_gaiaid_): n += 2 + self.lengthString(len(self.obfuscated_gaiaid_))
    if (self.has_federated_identity_): n += 2 + self.lengthString(len(self.federated_identity_))
    if (self.has_federated_provider_): n += 2 + self.lengthString(len(self.federated_provider_))
    return n

  def Clear(self):
    self.clear_email()
    self.clear_auth_domain()
    self.clear_nickname()
    self.clear_gaiaid()
    self.clear_obfuscated_gaiaid()
    self.clear_federated_identity()
    self.clear_federated_provider()

  def OutputUnchecked(self, out):
    out.putVarInt32(74)
    out.putPrefixedString(self.email_)
    out.putVarInt32(82)
    out.putPrefixedString(self.auth_domain_)
    if (self.has_nickname_):
      out.putVarInt32(90)
      out.putPrefixedString(self.nickname_)
    out.putVarInt32(144)
    out.putVarInt64(self.gaiaid_)
    if (self.has_obfuscated_gaiaid_):
      out.putVarInt32(154)
      out.putPrefixedString(self.obfuscated_gaiaid_)
    if (self.has_federated_identity_):
      out.putVarInt32(170)
      out.putPrefixedString(self.federated_identity_)
    if (self.has_federated_provider_):
      out.putVarInt32(178)
      out.putPrefixedString(self.federated_provider_)

  def OutputPartial(self, out):
    if (self.has_email_):
      out.putVarInt32(74)
      out.putPrefixedString(self.email_)
    if (self.has_auth_domain_):
      out.putVarInt32(82)
      out.putPrefixedString(self.auth_domain_)
    if (self.has_nickname_):
      out.putVarInt32(90)
      out.putPrefixedString(self.nickname_)
    if (self.has_gaiaid_):
      out.putVarInt32(144)
      out.putVarInt64(self.gaiaid_)
    if (self.has_obfuscated_gaiaid_):
      out.putVarInt32(154)
      out.putPrefixedString(self.obfuscated_gaiaid_)
    if (self.has_federated_identity_):
      out.putVarInt32(170)
      out.putPrefixedString(self.federated_identity_)
    if (self.has_federated_provider_):
      out.putVarInt32(178)
      out.putPrefixedString(self.federated_provider_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 68: break
      if tt == 74:
        self.set_email(d.getPrefixedString())
        continue
      if tt == 82:
        self.set_auth_domain(d.getPrefixedString())
        continue
      if tt == 90:
        self.set_nickname(d.getPrefixedString())
        continue
      if tt == 144:
        self.set_gaiaid(d.getVarInt64())
        continue
      if tt == 154:
        self.set_obfuscated_gaiaid(d.getPrefixedString())
        continue
      if tt == 170:
        self.set_federated_identity(d.getPrefixedString())
        continue
      if tt == 178:
        self.set_federated_provider(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_email_: res+=prefix+("email: %s\n" % self.DebugFormatString(self.email_))
    if self.has_auth_domain_: res+=prefix+("auth_domain: %s\n" % self.DebugFormatString(self.auth_domain_))
    if self.has_nickname_: res+=prefix+("nickname: %s\n" % self.DebugFormatString(self.nickname_))
    if self.has_gaiaid_: res+=prefix+("gaiaid: %s\n" % self.DebugFormatInt64(self.gaiaid_))
    if self.has_obfuscated_gaiaid_: res+=prefix+("obfuscated_gaiaid: %s\n" % self.DebugFormatString(self.obfuscated_gaiaid_))
    if self.has_federated_identity_: res+=prefix+("federated_identity: %s\n" % self.DebugFormatString(self.federated_identity_))
    if self.has_federated_provider_: res+=prefix+("federated_provider: %s\n" % self.DebugFormatString(self.federated_provider_))
    return res

class PropertyValue_ReferenceValue(ProtocolBuffer.ProtocolMessage):
  has_app_ = 0
  app_ = ""
  has_name_space_ = 0
  name_space_ = ""
  has_database_id_ = 0
  database_id_ = ""

  def __init__(self, contents=None):
    self.pathelement_ = []
    if contents is not None: self.MergeFromString(contents)

  def app(self): return self.app_

  def set_app(self, x):
    self.has_app_ = 1
    self.app_ = x

  def clear_app(self):
    if self.has_app_:
      self.has_app_ = 0
      self.app_ = ""

  def has_app(self): return self.has_app_

  def name_space(self): return self.name_space_

  def set_name_space(self, x):
    self.has_name_space_ = 1
    self.name_space_ = x

  def clear_name_space(self):
    if self.has_name_space_:
      self.has_name_space_ = 0
      self.name_space_ = ""

  def has_name_space(self): return self.has_name_space_

  def pathelement_size(self): return len(self.pathelement_)
  def pathelement_list(self): return self.pathelement_

  def pathelement(self, i):
    return self.pathelement_[i]

  def mutable_pathelement(self, i):
    return self.pathelement_[i]

  def add_pathelement(self):
    x = PropertyValue_ReferenceValuePathElement()
    self.pathelement_.append(x)
    return x

  def clear_pathelement(self):
    self.pathelement_ = []
  def database_id(self): return self.database_id_

  def set_database_id(self, x):
    self.has_database_id_ = 1
    self.database_id_ = x

  def clear_database_id(self):
    if self.has_database_id_:
      self.has_database_id_ = 0
      self.database_id_ = ""

  def has_database_id(self): return self.has_database_id_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app()): self.set_app(x.app())
    if (x.has_name_space()): self.set_name_space(x.name_space())
    for i in xrange(x.pathelement_size()): self.add_pathelement().CopyFrom(x.pathelement(i))
    if (x.has_database_id()): self.set_database_id(x.database_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_ != x.has_app_: return 0
    if self.has_app_ and self.app_ != x.app_: return 0
    if self.has_name_space_ != x.has_name_space_: return 0
    if self.has_name_space_ and self.name_space_ != x.name_space_: return 0
    if len(self.pathelement_) != len(x.pathelement_): return 0
    for e1, e2 in zip(self.pathelement_, x.pathelement_):
      if e1 != e2: return 0
    if self.has_database_id_ != x.has_database_id_: return 0
    if self.has_database_id_ and self.database_id_ != x.database_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_app_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: app not set.')
    for p in self.pathelement_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.app_))
    if (self.has_name_space_): n += 2 + self.lengthString(len(self.name_space_))
    n += 2 * len(self.pathelement_)
    for i in xrange(len(self.pathelement_)): n += self.pathelement_[i].ByteSize()
    if (self.has_database_id_): n += 2 + self.lengthString(len(self.database_id_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_):
      n += 1
      n += self.lengthString(len(self.app_))
    if (self.has_name_space_): n += 2 + self.lengthString(len(self.name_space_))
    n += 2 * len(self.pathelement_)
    for i in xrange(len(self.pathelement_)): n += self.pathelement_[i].ByteSizePartial()
    if (self.has_database_id_): n += 2 + self.lengthString(len(self.database_id_))
    return n

  def Clear(self):
    self.clear_app()
    self.clear_name_space()
    self.clear_pathelement()
    self.clear_database_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(106)
    out.putPrefixedString(self.app_)
    for i in xrange(len(self.pathelement_)):
      out.putVarInt32(115)
      self.pathelement_[i].OutputUnchecked(out)
      out.putVarInt32(116)
    if (self.has_name_space_):
      out.putVarInt32(162)
      out.putPrefixedString(self.name_space_)
    if (self.has_database_id_):
      out.putVarInt32(186)
      out.putPrefixedString(self.database_id_)

  def OutputPartial(self, out):
    if (self.has_app_):
      out.putVarInt32(106)
      out.putPrefixedString(self.app_)
    for i in xrange(len(self.pathelement_)):
      out.putVarInt32(115)
      self.pathelement_[i].OutputPartial(out)
      out.putVarInt32(116)
    if (self.has_name_space_):
      out.putVarInt32(162)
      out.putPrefixedString(self.name_space_)
    if (self.has_database_id_):
      out.putVarInt32(186)
      out.putPrefixedString(self.database_id_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 100: break
      if tt == 106:
        self.set_app(d.getPrefixedString())
        continue
      if tt == 115:
        self.add_pathelement().TryMerge(d)
        continue
      if tt == 162:
        self.set_name_space(d.getPrefixedString())
        continue
      if tt == 186:
        self.set_database_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_: res+=prefix+("app: %s\n" % self.DebugFormatString(self.app_))
    if self.has_name_space_: res+=prefix+("name_space: %s\n" % self.DebugFormatString(self.name_space_))
    cnt=0
    for e in self.pathelement_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("PathElement%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    if self.has_database_id_: res+=prefix+("database_id: %s\n" % self.DebugFormatString(self.database_id_))
    return res

class PropertyValue(ProtocolBuffer.ProtocolMessage):
  has_int64value_ = 0
  int64value_ = 0
  has_booleanvalue_ = 0
  booleanvalue_ = 0
  has_stringvalue_ = 0
  stringvalue_ = ""
  has_doublevalue_ = 0
  doublevalue_ = 0.0
  has_pointvalue_ = 0
  pointvalue_ = None
  has_uservalue_ = 0
  uservalue_ = None
  has_referencevalue_ = 0
  referencevalue_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def int64value(self): return self.int64value_

  def set_int64value(self, x):
    self.has_int64value_ = 1
    self.int64value_ = x

  def clear_int64value(self):
    if self.has_int64value_:
      self.has_int64value_ = 0
      self.int64value_ = 0

  def has_int64value(self): return self.has_int64value_

  def booleanvalue(self): return self.booleanvalue_

  def set_booleanvalue(self, x):
    self.has_booleanvalue_ = 1
    self.booleanvalue_ = x

  def clear_booleanvalue(self):
    if self.has_booleanvalue_:
      self.has_booleanvalue_ = 0
      self.booleanvalue_ = 0

  def has_booleanvalue(self): return self.has_booleanvalue_

  def stringvalue(self): return self.stringvalue_

  def set_stringvalue(self, x):
    self.has_stringvalue_ = 1
    self.stringvalue_ = x

  def clear_stringvalue(self):
    if self.has_stringvalue_:
      self.has_stringvalue_ = 0
      self.stringvalue_ = ""

  def has_stringvalue(self): return self.has_stringvalue_

  def doublevalue(self): return self.doublevalue_

  def set_doublevalue(self, x):
    self.has_doublevalue_ = 1
    self.doublevalue_ = x

  def clear_doublevalue(self):
    if self.has_doublevalue_:
      self.has_doublevalue_ = 0
      self.doublevalue_ = 0.0

  def has_doublevalue(self): return self.has_doublevalue_

  def pointvalue(self):
    if self.pointvalue_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.pointvalue_ is None: self.pointvalue_ = PropertyValue_PointValue()
      finally:
        self.lazy_init_lock_.release()
    return self.pointvalue_

  def mutable_pointvalue(self): self.has_pointvalue_ = 1; return self.pointvalue()

  def clear_pointvalue(self):

    if self.has_pointvalue_:
      self.has_pointvalue_ = 0;
      if self.pointvalue_ is not None: self.pointvalue_.Clear()

  def has_pointvalue(self): return self.has_pointvalue_

  def uservalue(self):
    if self.uservalue_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.uservalue_ is None: self.uservalue_ = PropertyValue_UserValue()
      finally:
        self.lazy_init_lock_.release()
    return self.uservalue_

  def mutable_uservalue(self): self.has_uservalue_ = 1; return self.uservalue()

  def clear_uservalue(self):

    if self.has_uservalue_:
      self.has_uservalue_ = 0;
      if self.uservalue_ is not None: self.uservalue_.Clear()

  def has_uservalue(self): return self.has_uservalue_

  def referencevalue(self):
    if self.referencevalue_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.referencevalue_ is None: self.referencevalue_ = PropertyValue_ReferenceValue()
      finally:
        self.lazy_init_lock_.release()
    return self.referencevalue_

  def mutable_referencevalue(self): self.has_referencevalue_ = 1; return self.referencevalue()

  def clear_referencevalue(self):

    if self.has_referencevalue_:
      self.has_referencevalue_ = 0;
      if self.referencevalue_ is not None: self.referencevalue_.Clear()

  def has_referencevalue(self): return self.has_referencevalue_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_int64value()): self.set_int64value(x.int64value())
    if (x.has_booleanvalue()): self.set_booleanvalue(x.booleanvalue())
    if (x.has_stringvalue()): self.set_stringvalue(x.stringvalue())
    if (x.has_doublevalue()): self.set_doublevalue(x.doublevalue())
    if (x.has_pointvalue()): self.mutable_pointvalue().MergeFrom(x.pointvalue())
    if (x.has_uservalue()): self.mutable_uservalue().MergeFrom(x.uservalue())
    if (x.has_referencevalue()): self.mutable_referencevalue().MergeFrom(x.referencevalue())

  def Equals(self, x):
    if x is self: return 1
    if self.has_int64value_ != x.has_int64value_: return 0
    if self.has_int64value_ and self.int64value_ != x.int64value_: return 0
    if self.has_booleanvalue_ != x.has_booleanvalue_: return 0
    if self.has_booleanvalue_ and self.booleanvalue_ != x.booleanvalue_: return 0
    if self.has_stringvalue_ != x.has_stringvalue_: return 0
    if self.has_stringvalue_ and self.stringvalue_ != x.stringvalue_: return 0
    if self.has_doublevalue_ != x.has_doublevalue_: return 0
    if self.has_doublevalue_ and self.doublevalue_ != x.doublevalue_: return 0
    if self.has_pointvalue_ != x.has_pointvalue_: return 0
    if self.has_pointvalue_ and self.pointvalue_ != x.pointvalue_: return 0
    if self.has_uservalue_ != x.has_uservalue_: return 0
    if self.has_uservalue_ and self.uservalue_ != x.uservalue_: return 0
    if self.has_referencevalue_ != x.has_referencevalue_: return 0
    if self.has_referencevalue_ and self.referencevalue_ != x.referencevalue_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_pointvalue_ and not self.pointvalue_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_uservalue_ and not self.uservalue_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_referencevalue_ and not self.referencevalue_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_int64value_): n += 1 + self.lengthVarInt64(self.int64value_)
    if (self.has_booleanvalue_): n += 2
    if (self.has_stringvalue_): n += 1 + self.lengthString(len(self.stringvalue_))
    if (self.has_doublevalue_): n += 9
    if (self.has_pointvalue_): n += 2 + self.pointvalue_.ByteSize()
    if (self.has_uservalue_): n += 2 + self.uservalue_.ByteSize()
    if (self.has_referencevalue_): n += 2 + self.referencevalue_.ByteSize()
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_int64value_): n += 1 + self.lengthVarInt64(self.int64value_)
    if (self.has_booleanvalue_): n += 2
    if (self.has_stringvalue_): n += 1 + self.lengthString(len(self.stringvalue_))
    if (self.has_doublevalue_): n += 9
    if (self.has_pointvalue_): n += 2 + self.pointvalue_.ByteSizePartial()
    if (self.has_uservalue_): n += 2 + self.uservalue_.ByteSizePartial()
    if (self.has_referencevalue_): n += 2 + self.referencevalue_.ByteSizePartial()
    return n

  def Clear(self):
    self.clear_int64value()
    self.clear_booleanvalue()
    self.clear_stringvalue()
    self.clear_doublevalue()
    self.clear_pointvalue()
    self.clear_uservalue()
    self.clear_referencevalue()

  def OutputUnchecked(self, out):
    if (self.has_int64value_):
      out.putVarInt32(8)
      out.putVarInt64(self.int64value_)
    if (self.has_booleanvalue_):
      out.putVarInt32(16)
      out.putBoolean(self.booleanvalue_)
    if (self.has_stringvalue_):
      out.putVarInt32(26)
      out.putPrefixedString(self.stringvalue_)
    if (self.has_doublevalue_):
      out.putVarInt32(33)
      out.putDouble(self.doublevalue_)
    if (self.has_pointvalue_):
      out.putVarInt32(43)
      self.pointvalue_.OutputUnchecked(out)
      out.putVarInt32(44)
    if (self.has_uservalue_):
      out.putVarInt32(67)
      self.uservalue_.OutputUnchecked(out)
      out.putVarInt32(68)
    if (self.has_referencevalue_):
      out.putVarInt32(99)
      self.referencevalue_.OutputUnchecked(out)
      out.putVarInt32(100)

  def OutputPartial(self, out):
    if (self.has_int64value_):
      out.putVarInt32(8)
      out.putVarInt64(self.int64value_)
    if (self.has_booleanvalue_):
      out.putVarInt32(16)
      out.putBoolean(self.booleanvalue_)
    if (self.has_stringvalue_):
      out.putVarInt32(26)
      out.putPrefixedString(self.stringvalue_)
    if (self.has_doublevalue_):
      out.putVarInt32(33)
      out.putDouble(self.doublevalue_)
    if (self.has_pointvalue_):
      out.putVarInt32(43)
      self.pointvalue_.OutputPartial(out)
      out.putVarInt32(44)
    if (self.has_uservalue_):
      out.putVarInt32(67)
      self.uservalue_.OutputPartial(out)
      out.putVarInt32(68)
    if (self.has_referencevalue_):
      out.putVarInt32(99)
      self.referencevalue_.OutputPartial(out)
      out.putVarInt32(100)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_int64value(d.getVarInt64())
        continue
      if tt == 16:
        self.set_booleanvalue(d.getBoolean())
        continue
      if tt == 26:
        self.set_stringvalue(d.getPrefixedString())
        continue
      if tt == 33:
        self.set_doublevalue(d.getDouble())
        continue
      if tt == 43:
        self.mutable_pointvalue().TryMerge(d)
        continue
      if tt == 67:
        self.mutable_uservalue().TryMerge(d)
        continue
      if tt == 99:
        self.mutable_referencevalue().TryMerge(d)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_int64value_: res+=prefix+("int64Value: %s\n" % self.DebugFormatInt64(self.int64value_))
    if self.has_booleanvalue_: res+=prefix+("booleanValue: %s\n" % self.DebugFormatBool(self.booleanvalue_))
    if self.has_stringvalue_: res+=prefix+("stringValue: %s\n" % self.DebugFormatString(self.stringvalue_))
    if self.has_doublevalue_: res+=prefix+("doubleValue: %s\n" % self.DebugFormat(self.doublevalue_))
    if self.has_pointvalue_:
      res+=prefix+"PointValue {\n"
      res+=self.pointvalue_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
    if self.has_uservalue_:
      res+=prefix+"UserValue {\n"
      res+=self.uservalue_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
    if self.has_referencevalue_:
      res+=prefix+"ReferenceValue {\n"
      res+=self.referencevalue_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kint64Value = 1
  kbooleanValue = 2
  kstringValue = 3
  kdoubleValue = 4
  kPointValueGroup = 5
  kPointValuex = 6
  kPointValuey = 7
  kUserValueGroup = 8
  kUserValueemail = 9
  kUserValueauth_domain = 10
  kUserValuenickname = 11
  kUserValuegaiaid = 18
  kUserValueobfuscated_gaiaid = 19
  kUserValuefederated_identity = 21
  kUserValuefederated_provider = 22
  kReferenceValueGroup = 12
  kReferenceValueapp = 13
  kReferenceValuename_space = 20
  kReferenceValuePathElementGroup = 14
  kReferenceValuePathElementtype = 15
  kReferenceValuePathElementid = 16
  kReferenceValuePathElementname = 17
  kReferenceValuedatabase_id = 23

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "int64Value",
    2: "booleanValue",
    3: "stringValue",
    4: "doubleValue",
    5: "PointValue",
    6: "x",
    7: "y",
    8: "UserValue",
    9: "email",
    10: "auth_domain",
    11: "nickname",
    12: "ReferenceValue",
    13: "app",
    14: "PathElement",
    15: "type",
    16: "id",
    17: "name",
    18: "gaiaid",
    19: "obfuscated_gaiaid",
    20: "name_space",
    21: "federated_identity",
    22: "federated_provider",
    23: "database_id",
  }, 23)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.DOUBLE,
    5: ProtocolBuffer.Encoder.STARTGROUP,
    6: ProtocolBuffer.Encoder.DOUBLE,
    7: ProtocolBuffer.Encoder.DOUBLE,
    8: ProtocolBuffer.Encoder.STARTGROUP,
    9: ProtocolBuffer.Encoder.STRING,
    10: ProtocolBuffer.Encoder.STRING,
    11: ProtocolBuffer.Encoder.STRING,
    12: ProtocolBuffer.Encoder.STARTGROUP,
    13: ProtocolBuffer.Encoder.STRING,
    14: ProtocolBuffer.Encoder.STARTGROUP,
    15: ProtocolBuffer.Encoder.STRING,
    16: ProtocolBuffer.Encoder.NUMERIC,
    17: ProtocolBuffer.Encoder.STRING,
    18: ProtocolBuffer.Encoder.NUMERIC,
    19: ProtocolBuffer.Encoder.STRING,
    20: ProtocolBuffer.Encoder.STRING,
    21: ProtocolBuffer.Encoder.STRING,
    22: ProtocolBuffer.Encoder.STRING,
    23: ProtocolBuffer.Encoder.STRING,
  }, 23, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.PropertyValue'
class Property(ProtocolBuffer.ProtocolMessage):


  NO_MEANING   =    0
  BLOB         =   14
  TEXT         =   15
  BYTESTRING   =   16
  ATOM_CATEGORY =    1
  ATOM_LINK    =    2
  ATOM_TITLE   =    3
  ATOM_CONTENT =    4
  ATOM_SUMMARY =    5
  ATOM_AUTHOR  =    6
  GD_WHEN      =    7
  GD_EMAIL     =    8
  GEORSS_POINT =    9
  GD_IM        =   10
  GD_PHONENUMBER =   11
  GD_POSTALADDRESS =   12
  GD_RATING    =   13
  BLOBKEY      =   17
  ENTITY_PROTO =   19
  INDEX_VALUE  =   18
  EMPTY_LIST   =   24

  _Meaning_NAMES = {
    0: "NO_MEANING",
    14: "BLOB",
    15: "TEXT",
    16: "BYTESTRING",
    1: "ATOM_CATEGORY",
    2: "ATOM_LINK",
    3: "ATOM_TITLE",
    4: "ATOM_CONTENT",
    5: "ATOM_SUMMARY",
    6: "ATOM_AUTHOR",
    7: "GD_WHEN",
    8: "GD_EMAIL",
    9: "GEORSS_POINT",
    10: "GD_IM",
    11: "GD_PHONENUMBER",
    12: "GD_POSTALADDRESS",
    13: "GD_RATING",
    17: "BLOBKEY",
    19: "ENTITY_PROTO",
    18: "INDEX_VALUE",
    24: "EMPTY_LIST",
  }

  def Meaning_Name(cls, x): return cls._Meaning_NAMES.get(x, "")
  Meaning_Name = classmethod(Meaning_Name)

  has_meaning_ = 0
  meaning_ = 0
  has_meaning_uri_ = 0
  meaning_uri_ = ""
  has_name_ = 0
  name_ = ""
  has_value_ = 0
  has_multiple_ = 0
  multiple_ = 0
  has_stashed_ = 0
  stashed_ = -1
  has_computed_ = 0
  computed_ = 0

  def __init__(self, contents=None):
    self.value_ = PropertyValue()
    if contents is not None: self.MergeFromString(contents)

  def meaning(self): return self.meaning_

  def set_meaning(self, x):
    self.has_meaning_ = 1
    self.meaning_ = x

  def clear_meaning(self):
    if self.has_meaning_:
      self.has_meaning_ = 0
      self.meaning_ = 0

  def has_meaning(self): return self.has_meaning_

  def meaning_uri(self): return self.meaning_uri_

  def set_meaning_uri(self, x):
    self.has_meaning_uri_ = 1
    self.meaning_uri_ = x

  def clear_meaning_uri(self):
    if self.has_meaning_uri_:
      self.has_meaning_uri_ = 0
      self.meaning_uri_ = ""

  def has_meaning_uri(self): return self.has_meaning_uri_

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

  def mutable_value(self): self.has_value_ = 1; return self.value_

  def clear_value(self):self.has_value_ = 0; self.value_.Clear()

  def has_value(self): return self.has_value_

  def multiple(self): return self.multiple_

  def set_multiple(self, x):
    self.has_multiple_ = 1
    self.multiple_ = x

  def clear_multiple(self):
    if self.has_multiple_:
      self.has_multiple_ = 0
      self.multiple_ = 0

  def has_multiple(self): return self.has_multiple_

  def stashed(self): return self.stashed_

  def set_stashed(self, x):
    self.has_stashed_ = 1
    self.stashed_ = x

  def clear_stashed(self):
    if self.has_stashed_:
      self.has_stashed_ = 0
      self.stashed_ = -1

  def has_stashed(self): return self.has_stashed_

  def computed(self): return self.computed_

  def set_computed(self, x):
    self.has_computed_ = 1
    self.computed_ = x

  def clear_computed(self):
    if self.has_computed_:
      self.has_computed_ = 0
      self.computed_ = 0

  def has_computed(self): return self.has_computed_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_meaning()): self.set_meaning(x.meaning())
    if (x.has_meaning_uri()): self.set_meaning_uri(x.meaning_uri())
    if (x.has_name()): self.set_name(x.name())
    if (x.has_value()): self.mutable_value().MergeFrom(x.value())
    if (x.has_multiple()): self.set_multiple(x.multiple())
    if (x.has_stashed()): self.set_stashed(x.stashed())
    if (x.has_computed()): self.set_computed(x.computed())

  def Equals(self, x):
    if x is self: return 1
    if self.has_meaning_ != x.has_meaning_: return 0
    if self.has_meaning_ and self.meaning_ != x.meaning_: return 0
    if self.has_meaning_uri_ != x.has_meaning_uri_: return 0
    if self.has_meaning_uri_ and self.meaning_uri_ != x.meaning_uri_: return 0
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    if self.has_multiple_ != x.has_multiple_: return 0
    if self.has_multiple_ and self.multiple_ != x.multiple_: return 0
    if self.has_stashed_ != x.has_stashed_: return 0
    if self.has_stashed_ and self.stashed_ != x.stashed_: return 0
    if self.has_computed_ != x.has_computed_: return 0
    if self.has_computed_ and self.computed_ != x.computed_: return 0
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
    elif not self.value_.IsInitialized(debug_strs): initialized = 0
    if (not self.has_multiple_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: multiple not set.')
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_meaning_): n += 1 + self.lengthVarInt64(self.meaning_)
    if (self.has_meaning_uri_): n += 1 + self.lengthString(len(self.meaning_uri_))
    n += self.lengthString(len(self.name_))
    n += self.lengthString(self.value_.ByteSize())
    if (self.has_stashed_): n += 1 + self.lengthVarInt64(self.stashed_)
    if (self.has_computed_): n += 2
    return n + 4

  def ByteSizePartial(self):
    n = 0
    if (self.has_meaning_): n += 1 + self.lengthVarInt64(self.meaning_)
    if (self.has_meaning_uri_): n += 1 + self.lengthString(len(self.meaning_uri_))
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    if (self.has_value_):
      n += 1
      n += self.lengthString(self.value_.ByteSizePartial())
    if (self.has_multiple_):
      n += 2
    if (self.has_stashed_): n += 1 + self.lengthVarInt64(self.stashed_)
    if (self.has_computed_): n += 2
    return n

  def Clear(self):
    self.clear_meaning()
    self.clear_meaning_uri()
    self.clear_name()
    self.clear_value()
    self.clear_multiple()
    self.clear_stashed()
    self.clear_computed()

  def OutputUnchecked(self, out):
    if (self.has_meaning_):
      out.putVarInt32(8)
      out.putVarInt32(self.meaning_)
    if (self.has_meaning_uri_):
      out.putVarInt32(18)
      out.putPrefixedString(self.meaning_uri_)
    out.putVarInt32(26)
    out.putPrefixedString(self.name_)
    out.putVarInt32(32)
    out.putBoolean(self.multiple_)
    out.putVarInt32(42)
    out.putVarInt32(self.value_.ByteSize())
    self.value_.OutputUnchecked(out)
    if (self.has_stashed_):
      out.putVarInt32(48)
      out.putVarInt32(self.stashed_)
    if (self.has_computed_):
      out.putVarInt32(56)
      out.putBoolean(self.computed_)

  def OutputPartial(self, out):
    if (self.has_meaning_):
      out.putVarInt32(8)
      out.putVarInt32(self.meaning_)
    if (self.has_meaning_uri_):
      out.putVarInt32(18)
      out.putPrefixedString(self.meaning_uri_)
    if (self.has_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.name_)
    if (self.has_multiple_):
      out.putVarInt32(32)
      out.putBoolean(self.multiple_)
    if (self.has_value_):
      out.putVarInt32(42)
      out.putVarInt32(self.value_.ByteSizePartial())
      self.value_.OutputPartial(out)
    if (self.has_stashed_):
      out.putVarInt32(48)
      out.putVarInt32(self.stashed_)
    if (self.has_computed_):
      out.putVarInt32(56)
      out.putBoolean(self.computed_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_meaning(d.getVarInt32())
        continue
      if tt == 18:
        self.set_meaning_uri(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_name(d.getPrefixedString())
        continue
      if tt == 32:
        self.set_multiple(d.getBoolean())
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_value().TryMerge(tmp)
        continue
      if tt == 48:
        self.set_stashed(d.getVarInt32())
        continue
      if tt == 56:
        self.set_computed(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_meaning_: res+=prefix+("meaning: %s\n" % self.DebugFormatInt32(self.meaning_))
    if self.has_meaning_uri_: res+=prefix+("meaning_uri: %s\n" % self.DebugFormatString(self.meaning_uri_))
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    if self.has_value_:
      res+=prefix+"value <\n"
      res+=self.value_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_multiple_: res+=prefix+("multiple: %s\n" % self.DebugFormatBool(self.multiple_))
    if self.has_stashed_: res+=prefix+("stashed: %s\n" % self.DebugFormatInt32(self.stashed_))
    if self.has_computed_: res+=prefix+("computed: %s\n" % self.DebugFormatBool(self.computed_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kmeaning = 1
  kmeaning_uri = 2
  kname = 3
  kvalue = 5
  kmultiple = 4
  kstashed = 6
  kcomputed = 7

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "meaning",
    2: "meaning_uri",
    3: "name",
    4: "multiple",
    5: "value",
    6: "stashed",
    7: "computed",
  }, 7)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.NUMERIC,
    7: ProtocolBuffer.Encoder.NUMERIC,
  }, 7, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.Property'
class Path_Element(ProtocolBuffer.ProtocolMessage):
  has_type_ = 0
  type_ = ""
  has_id_ = 0
  id_ = 0
  has_name_ = 0
  name_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def type(self): return self.type_

  def set_type(self, x):
    self.has_type_ = 1
    self.type_ = x

  def clear_type(self):
    if self.has_type_:
      self.has_type_ = 0
      self.type_ = ""

  def has_type(self): return self.has_type_

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
    if (x.has_type()): self.set_type(x.type())
    if (x.has_id()): self.set_id(x.id())
    if (x.has_name()): self.set_name(x.name())

  def Equals(self, x):
    if x is self: return 1
    if self.has_type_ != x.has_type_: return 0
    if self.has_type_ and self.type_ != x.type_: return 0
    if self.has_id_ != x.has_id_: return 0
    if self.has_id_ and self.id_ != x.id_: return 0
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_type_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: type not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.type_))
    if (self.has_id_): n += 1 + self.lengthVarInt64(self.id_)
    if (self.has_name_): n += 1 + self.lengthString(len(self.name_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_type_):
      n += 1
      n += self.lengthString(len(self.type_))
    if (self.has_id_): n += 1 + self.lengthVarInt64(self.id_)
    if (self.has_name_): n += 1 + self.lengthString(len(self.name_))
    return n

  def Clear(self):
    self.clear_type()
    self.clear_id()
    self.clear_name()

  def OutputUnchecked(self, out):
    out.putVarInt32(18)
    out.putPrefixedString(self.type_)
    if (self.has_id_):
      out.putVarInt32(24)
      out.putVarInt64(self.id_)
    if (self.has_name_):
      out.putVarInt32(34)
      out.putPrefixedString(self.name_)

  def OutputPartial(self, out):
    if (self.has_type_):
      out.putVarInt32(18)
      out.putPrefixedString(self.type_)
    if (self.has_id_):
      out.putVarInt32(24)
      out.putVarInt64(self.id_)
    if (self.has_name_):
      out.putVarInt32(34)
      out.putPrefixedString(self.name_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 12: break
      if tt == 18:
        self.set_type(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_id(d.getVarInt64())
        continue
      if tt == 34:
        self.set_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_type_: res+=prefix+("type: %s\n" % self.DebugFormatString(self.type_))
    if self.has_id_: res+=prefix+("id: %s\n" % self.DebugFormatInt64(self.id_))
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    return res

class Path(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.element_ = []
    if contents is not None: self.MergeFromString(contents)

  def element_size(self): return len(self.element_)
  def element_list(self): return self.element_

  def element(self, i):
    return self.element_[i]

  def mutable_element(self, i):
    return self.element_[i]

  def add_element(self):
    x = Path_Element()
    self.element_.append(x)
    return x

  def clear_element(self):
    self.element_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.element_size()): self.add_element().CopyFrom(x.element(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.element_) != len(x.element_): return 0
    for e1, e2 in zip(self.element_, x.element_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.element_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 2 * len(self.element_)
    for i in xrange(len(self.element_)): n += self.element_[i].ByteSize()
    return n

  def ByteSizePartial(self):
    n = 0
    n += 2 * len(self.element_)
    for i in xrange(len(self.element_)): n += self.element_[i].ByteSizePartial()
    return n

  def Clear(self):
    self.clear_element()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.element_)):
      out.putVarInt32(11)
      self.element_[i].OutputUnchecked(out)
      out.putVarInt32(12)

  def OutputPartial(self, out):
    for i in xrange(len(self.element_)):
      out.putVarInt32(11)
      self.element_[i].OutputPartial(out)
      out.putVarInt32(12)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 11:
        self.add_element().TryMerge(d)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.element_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Element%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kElementGroup = 1
  kElementtype = 2
  kElementid = 3
  kElementname = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "Element",
    2: "type",
    3: "id",
    4: "name",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STARTGROUP,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.STRING,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.Path'
class Reference(ProtocolBuffer.ProtocolMessage):
  has_app_ = 0
  app_ = ""
  has_name_space_ = 0
  name_space_ = ""
  has_path_ = 0
  has_database_id_ = 0
  database_id_ = ""

  def __init__(self, contents=None):
    self.path_ = Path()
    if contents is not None: self.MergeFromString(contents)

  def app(self): return self.app_

  def set_app(self, x):
    self.has_app_ = 1
    self.app_ = x

  def clear_app(self):
    if self.has_app_:
      self.has_app_ = 0
      self.app_ = ""

  def has_app(self): return self.has_app_

  def name_space(self): return self.name_space_

  def set_name_space(self, x):
    self.has_name_space_ = 1
    self.name_space_ = x

  def clear_name_space(self):
    if self.has_name_space_:
      self.has_name_space_ = 0
      self.name_space_ = ""

  def has_name_space(self): return self.has_name_space_

  def path(self): return self.path_

  def mutable_path(self): self.has_path_ = 1; return self.path_

  def clear_path(self):self.has_path_ = 0; self.path_.Clear()

  def has_path(self): return self.has_path_

  def database_id(self): return self.database_id_

  def set_database_id(self, x):
    self.has_database_id_ = 1
    self.database_id_ = x

  def clear_database_id(self):
    if self.has_database_id_:
      self.has_database_id_ = 0
      self.database_id_ = ""

  def has_database_id(self): return self.has_database_id_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app()): self.set_app(x.app())
    if (x.has_name_space()): self.set_name_space(x.name_space())
    if (x.has_path()): self.mutable_path().MergeFrom(x.path())
    if (x.has_database_id()): self.set_database_id(x.database_id())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_ != x.has_app_: return 0
    if self.has_app_ and self.app_ != x.app_: return 0
    if self.has_name_space_ != x.has_name_space_: return 0
    if self.has_name_space_ and self.name_space_ != x.name_space_: return 0
    if self.has_path_ != x.has_path_: return 0
    if self.has_path_ and self.path_ != x.path_: return 0
    if self.has_database_id_ != x.has_database_id_: return 0
    if self.has_database_id_ and self.database_id_ != x.database_id_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_app_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: app not set.')
    if (not self.has_path_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: path not set.')
    elif not self.path_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.app_))
    if (self.has_name_space_): n += 2 + self.lengthString(len(self.name_space_))
    n += self.lengthString(self.path_.ByteSize())
    if (self.has_database_id_): n += 2 + self.lengthString(len(self.database_id_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_):
      n += 1
      n += self.lengthString(len(self.app_))
    if (self.has_name_space_): n += 2 + self.lengthString(len(self.name_space_))
    if (self.has_path_):
      n += 1
      n += self.lengthString(self.path_.ByteSizePartial())
    if (self.has_database_id_): n += 2 + self.lengthString(len(self.database_id_))
    return n

  def Clear(self):
    self.clear_app()
    self.clear_name_space()
    self.clear_path()
    self.clear_database_id()

  def OutputUnchecked(self, out):
    out.putVarInt32(106)
    out.putPrefixedString(self.app_)
    out.putVarInt32(114)
    out.putVarInt32(self.path_.ByteSize())
    self.path_.OutputUnchecked(out)
    if (self.has_name_space_):
      out.putVarInt32(162)
      out.putPrefixedString(self.name_space_)
    if (self.has_database_id_):
      out.putVarInt32(186)
      out.putPrefixedString(self.database_id_)

  def OutputPartial(self, out):
    if (self.has_app_):
      out.putVarInt32(106)
      out.putPrefixedString(self.app_)
    if (self.has_path_):
      out.putVarInt32(114)
      out.putVarInt32(self.path_.ByteSizePartial())
      self.path_.OutputPartial(out)
    if (self.has_name_space_):
      out.putVarInt32(162)
      out.putPrefixedString(self.name_space_)
    if (self.has_database_id_):
      out.putVarInt32(186)
      out.putPrefixedString(self.database_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 106:
        self.set_app(d.getPrefixedString())
        continue
      if tt == 114:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_path().TryMerge(tmp)
        continue
      if tt == 162:
        self.set_name_space(d.getPrefixedString())
        continue
      if tt == 186:
        self.set_database_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_: res+=prefix+("app: %s\n" % self.DebugFormatString(self.app_))
    if self.has_name_space_: res+=prefix+("name_space: %s\n" % self.DebugFormatString(self.name_space_))
    if self.has_path_:
      res+=prefix+"path <\n"
      res+=self.path_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_database_id_: res+=prefix+("database_id: %s\n" % self.DebugFormatString(self.database_id_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp = 13
  kname_space = 20
  kpath = 14
  kdatabase_id = 23

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    13: "app",
    14: "path",
    20: "name_space",
    23: "database_id",
  }, 23)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    13: ProtocolBuffer.Encoder.STRING,
    14: ProtocolBuffer.Encoder.STRING,
    20: ProtocolBuffer.Encoder.STRING,
    23: ProtocolBuffer.Encoder.STRING,
  }, 23, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.Reference'
class User(ProtocolBuffer.ProtocolMessage):
  has_email_ = 0
  email_ = ""
  has_auth_domain_ = 0
  auth_domain_ = ""
  has_nickname_ = 0
  nickname_ = ""
  has_gaiaid_ = 0
  gaiaid_ = 0
  has_obfuscated_gaiaid_ = 0
  obfuscated_gaiaid_ = ""
  has_federated_identity_ = 0
  federated_identity_ = ""
  has_federated_provider_ = 0
  federated_provider_ = ""

  def __init__(self, contents=None):
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

  def auth_domain(self): return self.auth_domain_

  def set_auth_domain(self, x):
    self.has_auth_domain_ = 1
    self.auth_domain_ = x

  def clear_auth_domain(self):
    if self.has_auth_domain_:
      self.has_auth_domain_ = 0
      self.auth_domain_ = ""

  def has_auth_domain(self): return self.has_auth_domain_

  def nickname(self): return self.nickname_

  def set_nickname(self, x):
    self.has_nickname_ = 1
    self.nickname_ = x

  def clear_nickname(self):
    if self.has_nickname_:
      self.has_nickname_ = 0
      self.nickname_ = ""

  def has_nickname(self): return self.has_nickname_

  def gaiaid(self): return self.gaiaid_

  def set_gaiaid(self, x):
    self.has_gaiaid_ = 1
    self.gaiaid_ = x

  def clear_gaiaid(self):
    if self.has_gaiaid_:
      self.has_gaiaid_ = 0
      self.gaiaid_ = 0

  def has_gaiaid(self): return self.has_gaiaid_

  def obfuscated_gaiaid(self): return self.obfuscated_gaiaid_

  def set_obfuscated_gaiaid(self, x):
    self.has_obfuscated_gaiaid_ = 1
    self.obfuscated_gaiaid_ = x

  def clear_obfuscated_gaiaid(self):
    if self.has_obfuscated_gaiaid_:
      self.has_obfuscated_gaiaid_ = 0
      self.obfuscated_gaiaid_ = ""

  def has_obfuscated_gaiaid(self): return self.has_obfuscated_gaiaid_

  def federated_identity(self): return self.federated_identity_

  def set_federated_identity(self, x):
    self.has_federated_identity_ = 1
    self.federated_identity_ = x

  def clear_federated_identity(self):
    if self.has_federated_identity_:
      self.has_federated_identity_ = 0
      self.federated_identity_ = ""

  def has_federated_identity(self): return self.has_federated_identity_

  def federated_provider(self): return self.federated_provider_

  def set_federated_provider(self, x):
    self.has_federated_provider_ = 1
    self.federated_provider_ = x

  def clear_federated_provider(self):
    if self.has_federated_provider_:
      self.has_federated_provider_ = 0
      self.federated_provider_ = ""

  def has_federated_provider(self): return self.has_federated_provider_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_email()): self.set_email(x.email())
    if (x.has_auth_domain()): self.set_auth_domain(x.auth_domain())
    if (x.has_nickname()): self.set_nickname(x.nickname())
    if (x.has_gaiaid()): self.set_gaiaid(x.gaiaid())
    if (x.has_obfuscated_gaiaid()): self.set_obfuscated_gaiaid(x.obfuscated_gaiaid())
    if (x.has_federated_identity()): self.set_federated_identity(x.federated_identity())
    if (x.has_federated_provider()): self.set_federated_provider(x.federated_provider())

  def Equals(self, x):
    if x is self: return 1
    if self.has_email_ != x.has_email_: return 0
    if self.has_email_ and self.email_ != x.email_: return 0
    if self.has_auth_domain_ != x.has_auth_domain_: return 0
    if self.has_auth_domain_ and self.auth_domain_ != x.auth_domain_: return 0
    if self.has_nickname_ != x.has_nickname_: return 0
    if self.has_nickname_ and self.nickname_ != x.nickname_: return 0
    if self.has_gaiaid_ != x.has_gaiaid_: return 0
    if self.has_gaiaid_ and self.gaiaid_ != x.gaiaid_: return 0
    if self.has_obfuscated_gaiaid_ != x.has_obfuscated_gaiaid_: return 0
    if self.has_obfuscated_gaiaid_ and self.obfuscated_gaiaid_ != x.obfuscated_gaiaid_: return 0
    if self.has_federated_identity_ != x.has_federated_identity_: return 0
    if self.has_federated_identity_ and self.federated_identity_ != x.federated_identity_: return 0
    if self.has_federated_provider_ != x.has_federated_provider_: return 0
    if self.has_federated_provider_ and self.federated_provider_ != x.federated_provider_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_email_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: email not set.')
    if (not self.has_auth_domain_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: auth_domain not set.')
    if (not self.has_gaiaid_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: gaiaid not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.email_))
    n += self.lengthString(len(self.auth_domain_))
    if (self.has_nickname_): n += 1 + self.lengthString(len(self.nickname_))
    n += self.lengthVarInt64(self.gaiaid_)
    if (self.has_obfuscated_gaiaid_): n += 1 + self.lengthString(len(self.obfuscated_gaiaid_))
    if (self.has_federated_identity_): n += 1 + self.lengthString(len(self.federated_identity_))
    if (self.has_federated_provider_): n += 1 + self.lengthString(len(self.federated_provider_))
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_email_):
      n += 1
      n += self.lengthString(len(self.email_))
    if (self.has_auth_domain_):
      n += 1
      n += self.lengthString(len(self.auth_domain_))
    if (self.has_nickname_): n += 1 + self.lengthString(len(self.nickname_))
    if (self.has_gaiaid_):
      n += 1
      n += self.lengthVarInt64(self.gaiaid_)
    if (self.has_obfuscated_gaiaid_): n += 1 + self.lengthString(len(self.obfuscated_gaiaid_))
    if (self.has_federated_identity_): n += 1 + self.lengthString(len(self.federated_identity_))
    if (self.has_federated_provider_): n += 1 + self.lengthString(len(self.federated_provider_))
    return n

  def Clear(self):
    self.clear_email()
    self.clear_auth_domain()
    self.clear_nickname()
    self.clear_gaiaid()
    self.clear_obfuscated_gaiaid()
    self.clear_federated_identity()
    self.clear_federated_provider()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.email_)
    out.putVarInt32(18)
    out.putPrefixedString(self.auth_domain_)
    if (self.has_nickname_):
      out.putVarInt32(26)
      out.putPrefixedString(self.nickname_)
    out.putVarInt32(32)
    out.putVarInt64(self.gaiaid_)
    if (self.has_obfuscated_gaiaid_):
      out.putVarInt32(42)
      out.putPrefixedString(self.obfuscated_gaiaid_)
    if (self.has_federated_identity_):
      out.putVarInt32(50)
      out.putPrefixedString(self.federated_identity_)
    if (self.has_federated_provider_):
      out.putVarInt32(58)
      out.putPrefixedString(self.federated_provider_)

  def OutputPartial(self, out):
    if (self.has_email_):
      out.putVarInt32(10)
      out.putPrefixedString(self.email_)
    if (self.has_auth_domain_):
      out.putVarInt32(18)
      out.putPrefixedString(self.auth_domain_)
    if (self.has_nickname_):
      out.putVarInt32(26)
      out.putPrefixedString(self.nickname_)
    if (self.has_gaiaid_):
      out.putVarInt32(32)
      out.putVarInt64(self.gaiaid_)
    if (self.has_obfuscated_gaiaid_):
      out.putVarInt32(42)
      out.putPrefixedString(self.obfuscated_gaiaid_)
    if (self.has_federated_identity_):
      out.putVarInt32(50)
      out.putPrefixedString(self.federated_identity_)
    if (self.has_federated_provider_):
      out.putVarInt32(58)
      out.putPrefixedString(self.federated_provider_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_email(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_auth_domain(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_nickname(d.getPrefixedString())
        continue
      if tt == 32:
        self.set_gaiaid(d.getVarInt64())
        continue
      if tt == 42:
        self.set_obfuscated_gaiaid(d.getPrefixedString())
        continue
      if tt == 50:
        self.set_federated_identity(d.getPrefixedString())
        continue
      if tt == 58:
        self.set_federated_provider(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_email_: res+=prefix+("email: %s\n" % self.DebugFormatString(self.email_))
    if self.has_auth_domain_: res+=prefix+("auth_domain: %s\n" % self.DebugFormatString(self.auth_domain_))
    if self.has_nickname_: res+=prefix+("nickname: %s\n" % self.DebugFormatString(self.nickname_))
    if self.has_gaiaid_: res+=prefix+("gaiaid: %s\n" % self.DebugFormatInt64(self.gaiaid_))
    if self.has_obfuscated_gaiaid_: res+=prefix+("obfuscated_gaiaid: %s\n" % self.DebugFormatString(self.obfuscated_gaiaid_))
    if self.has_federated_identity_: res+=prefix+("federated_identity: %s\n" % self.DebugFormatString(self.federated_identity_))
    if self.has_federated_provider_: res+=prefix+("federated_provider: %s\n" % self.DebugFormatString(self.federated_provider_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kemail = 1
  kauth_domain = 2
  knickname = 3
  kgaiaid = 4
  kobfuscated_gaiaid = 5
  kfederated_identity = 6
  kfederated_provider = 7

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "email",
    2: "auth_domain",
    3: "nickname",
    4: "gaiaid",
    5: "obfuscated_gaiaid",
    6: "federated_identity",
    7: "federated_provider",
  }, 7)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.STRING,
    7: ProtocolBuffer.Encoder.STRING,
  }, 7, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.User'
class EntityProto(ProtocolBuffer.ProtocolMessage):


  GD_CONTACT   =    1
  GD_EVENT     =    2
  GD_MESSAGE   =    3

  _Kind_NAMES = {
    1: "GD_CONTACT",
    2: "GD_EVENT",
    3: "GD_MESSAGE",
  }

  def Kind_Name(cls, x): return cls._Kind_NAMES.get(x, "")
  Kind_Name = classmethod(Kind_Name)

  has_key_ = 0
  has_entity_group_ = 0
  has_owner_ = 0
  owner_ = None
  has_kind_ = 0
  kind_ = 0
  has_kind_uri_ = 0
  kind_uri_ = ""

  def __init__(self, contents=None):
    self.key_ = Reference()
    self.entity_group_ = Path()
    self.property_ = []
    self.raw_property_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def key(self): return self.key_

  def mutable_key(self): self.has_key_ = 1; return self.key_

  def clear_key(self):self.has_key_ = 0; self.key_.Clear()

  def has_key(self): return self.has_key_

  def entity_group(self): return self.entity_group_

  def mutable_entity_group(self): self.has_entity_group_ = 1; return self.entity_group_

  def clear_entity_group(self):self.has_entity_group_ = 0; self.entity_group_.Clear()

  def has_entity_group(self): return self.has_entity_group_

  def owner(self):
    if self.owner_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.owner_ is None: self.owner_ = User()
      finally:
        self.lazy_init_lock_.release()
    return self.owner_

  def mutable_owner(self): self.has_owner_ = 1; return self.owner()

  def clear_owner(self):

    if self.has_owner_:
      self.has_owner_ = 0;
      if self.owner_ is not None: self.owner_.Clear()

  def has_owner(self): return self.has_owner_

  def kind(self): return self.kind_

  def set_kind(self, x):
    self.has_kind_ = 1
    self.kind_ = x

  def clear_kind(self):
    if self.has_kind_:
      self.has_kind_ = 0
      self.kind_ = 0

  def has_kind(self): return self.has_kind_

  def kind_uri(self): return self.kind_uri_

  def set_kind_uri(self, x):
    self.has_kind_uri_ = 1
    self.kind_uri_ = x

  def clear_kind_uri(self):
    if self.has_kind_uri_:
      self.has_kind_uri_ = 0
      self.kind_uri_ = ""

  def has_kind_uri(self): return self.has_kind_uri_

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
  def raw_property_size(self): return len(self.raw_property_)
  def raw_property_list(self): return self.raw_property_

  def raw_property(self, i):
    return self.raw_property_[i]

  def mutable_raw_property(self, i):
    return self.raw_property_[i]

  def add_raw_property(self):
    x = Property()
    self.raw_property_.append(x)
    return x

  def clear_raw_property(self):
    self.raw_property_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_key()): self.mutable_key().MergeFrom(x.key())
    if (x.has_entity_group()): self.mutable_entity_group().MergeFrom(x.entity_group())
    if (x.has_owner()): self.mutable_owner().MergeFrom(x.owner())
    if (x.has_kind()): self.set_kind(x.kind())
    if (x.has_kind_uri()): self.set_kind_uri(x.kind_uri())
    for i in xrange(x.property_size()): self.add_property().CopyFrom(x.property(i))
    for i in xrange(x.raw_property_size()): self.add_raw_property().CopyFrom(x.raw_property(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_key_ != x.has_key_: return 0
    if self.has_key_ and self.key_ != x.key_: return 0
    if self.has_entity_group_ != x.has_entity_group_: return 0
    if self.has_entity_group_ and self.entity_group_ != x.entity_group_: return 0
    if self.has_owner_ != x.has_owner_: return 0
    if self.has_owner_ and self.owner_ != x.owner_: return 0
    if self.has_kind_ != x.has_kind_: return 0
    if self.has_kind_ and self.kind_ != x.kind_: return 0
    if self.has_kind_uri_ != x.has_kind_uri_: return 0
    if self.has_kind_uri_ and self.kind_uri_ != x.kind_uri_: return 0
    if len(self.property_) != len(x.property_): return 0
    for e1, e2 in zip(self.property_, x.property_):
      if e1 != e2: return 0
    if len(self.raw_property_) != len(x.raw_property_): return 0
    for e1, e2 in zip(self.raw_property_, x.raw_property_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_key_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: key not set.')
    elif not self.key_.IsInitialized(debug_strs): initialized = 0
    if (not self.has_entity_group_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: entity_group not set.')
    elif not self.entity_group_.IsInitialized(debug_strs): initialized = 0
    if (self.has_owner_ and not self.owner_.IsInitialized(debug_strs)): initialized = 0
    for p in self.property_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.raw_property_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.key_.ByteSize())
    n += self.lengthString(self.entity_group_.ByteSize())
    if (self.has_owner_): n += 2 + self.lengthString(self.owner_.ByteSize())
    if (self.has_kind_): n += 1 + self.lengthVarInt64(self.kind_)
    if (self.has_kind_uri_): n += 1 + self.lengthString(len(self.kind_uri_))
    n += 1 * len(self.property_)
    for i in xrange(len(self.property_)): n += self.lengthString(self.property_[i].ByteSize())
    n += 1 * len(self.raw_property_)
    for i in xrange(len(self.raw_property_)): n += self.lengthString(self.raw_property_[i].ByteSize())
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_key_):
      n += 1
      n += self.lengthString(self.key_.ByteSizePartial())
    if (self.has_entity_group_):
      n += 2
      n += self.lengthString(self.entity_group_.ByteSizePartial())
    if (self.has_owner_): n += 2 + self.lengthString(self.owner_.ByteSizePartial())
    if (self.has_kind_): n += 1 + self.lengthVarInt64(self.kind_)
    if (self.has_kind_uri_): n += 1 + self.lengthString(len(self.kind_uri_))
    n += 1 * len(self.property_)
    for i in xrange(len(self.property_)): n += self.lengthString(self.property_[i].ByteSizePartial())
    n += 1 * len(self.raw_property_)
    for i in xrange(len(self.raw_property_)): n += self.lengthString(self.raw_property_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_key()
    self.clear_entity_group()
    self.clear_owner()
    self.clear_kind()
    self.clear_kind_uri()
    self.clear_property()
    self.clear_raw_property()

  def OutputUnchecked(self, out):
    if (self.has_kind_):
      out.putVarInt32(32)
      out.putVarInt32(self.kind_)
    if (self.has_kind_uri_):
      out.putVarInt32(42)
      out.putPrefixedString(self.kind_uri_)
    out.putVarInt32(106)
    out.putVarInt32(self.key_.ByteSize())
    self.key_.OutputUnchecked(out)
    for i in xrange(len(self.property_)):
      out.putVarInt32(114)
      out.putVarInt32(self.property_[i].ByteSize())
      self.property_[i].OutputUnchecked(out)
    for i in xrange(len(self.raw_property_)):
      out.putVarInt32(122)
      out.putVarInt32(self.raw_property_[i].ByteSize())
      self.raw_property_[i].OutputUnchecked(out)
    out.putVarInt32(130)
    out.putVarInt32(self.entity_group_.ByteSize())
    self.entity_group_.OutputUnchecked(out)
    if (self.has_owner_):
      out.putVarInt32(138)
      out.putVarInt32(self.owner_.ByteSize())
      self.owner_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_kind_):
      out.putVarInt32(32)
      out.putVarInt32(self.kind_)
    if (self.has_kind_uri_):
      out.putVarInt32(42)
      out.putPrefixedString(self.kind_uri_)
    if (self.has_key_):
      out.putVarInt32(106)
      out.putVarInt32(self.key_.ByteSizePartial())
      self.key_.OutputPartial(out)
    for i in xrange(len(self.property_)):
      out.putVarInt32(114)
      out.putVarInt32(self.property_[i].ByteSizePartial())
      self.property_[i].OutputPartial(out)
    for i in xrange(len(self.raw_property_)):
      out.putVarInt32(122)
      out.putVarInt32(self.raw_property_[i].ByteSizePartial())
      self.raw_property_[i].OutputPartial(out)
    if (self.has_entity_group_):
      out.putVarInt32(130)
      out.putVarInt32(self.entity_group_.ByteSizePartial())
      self.entity_group_.OutputPartial(out)
    if (self.has_owner_):
      out.putVarInt32(138)
      out.putVarInt32(self.owner_.ByteSizePartial())
      self.owner_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 32:
        self.set_kind(d.getVarInt32())
        continue
      if tt == 42:
        self.set_kind_uri(d.getPrefixedString())
        continue
      if tt == 106:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_key().TryMerge(tmp)
        continue
      if tt == 114:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_property().TryMerge(tmp)
        continue
      if tt == 122:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_raw_property().TryMerge(tmp)
        continue
      if tt == 130:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_entity_group().TryMerge(tmp)
        continue
      if tt == 138:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_owner().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_:
      res+=prefix+"key <\n"
      res+=self.key_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_entity_group_:
      res+=prefix+"entity_group <\n"
      res+=self.entity_group_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_owner_:
      res+=prefix+"owner <\n"
      res+=self.owner_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_kind_: res+=prefix+("kind: %s\n" % self.DebugFormatInt32(self.kind_))
    if self.has_kind_uri_: res+=prefix+("kind_uri: %s\n" % self.DebugFormatString(self.kind_uri_))
    cnt=0
    for e in self.property_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("property%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.raw_property_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("raw_property%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kkey = 13
  kentity_group = 16
  kowner = 17
  kkind = 4
  kkind_uri = 5
  kproperty = 14
  kraw_property = 15

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    4: "kind",
    5: "kind_uri",
    13: "key",
    14: "property",
    15: "raw_property",
    16: "entity_group",
    17: "owner",
  }, 17)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
    13: ProtocolBuffer.Encoder.STRING,
    14: ProtocolBuffer.Encoder.STRING,
    15: ProtocolBuffer.Encoder.STRING,
    16: ProtocolBuffer.Encoder.STRING,
    17: ProtocolBuffer.Encoder.STRING,
  }, 17, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.EntityProto'
class EntityMetadata(ProtocolBuffer.ProtocolMessage):
  has_created_version_ = 0
  created_version_ = 0
  has_updated_version_ = 0
  updated_version_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def created_version(self): return self.created_version_

  def set_created_version(self, x):
    self.has_created_version_ = 1
    self.created_version_ = x

  def clear_created_version(self):
    if self.has_created_version_:
      self.has_created_version_ = 0
      self.created_version_ = 0

  def has_created_version(self): return self.has_created_version_

  def updated_version(self): return self.updated_version_

  def set_updated_version(self, x):
    self.has_updated_version_ = 1
    self.updated_version_ = x

  def clear_updated_version(self):
    if self.has_updated_version_:
      self.has_updated_version_ = 0
      self.updated_version_ = 0

  def has_updated_version(self): return self.has_updated_version_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_created_version()): self.set_created_version(x.created_version())
    if (x.has_updated_version()): self.set_updated_version(x.updated_version())

  def Equals(self, x):
    if x is self: return 1
    if self.has_created_version_ != x.has_created_version_: return 0
    if self.has_created_version_ and self.created_version_ != x.created_version_: return 0
    if self.has_updated_version_ != x.has_updated_version_: return 0
    if self.has_updated_version_ and self.updated_version_ != x.updated_version_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_created_version_): n += 1 + self.lengthVarInt64(self.created_version_)
    if (self.has_updated_version_): n += 1 + self.lengthVarInt64(self.updated_version_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_created_version_): n += 1 + self.lengthVarInt64(self.created_version_)
    if (self.has_updated_version_): n += 1 + self.lengthVarInt64(self.updated_version_)
    return n

  def Clear(self):
    self.clear_created_version()
    self.clear_updated_version()

  def OutputUnchecked(self, out):
    if (self.has_created_version_):
      out.putVarInt32(8)
      out.putVarInt64(self.created_version_)
    if (self.has_updated_version_):
      out.putVarInt32(16)
      out.putVarInt64(self.updated_version_)

  def OutputPartial(self, out):
    if (self.has_created_version_):
      out.putVarInt32(8)
      out.putVarInt64(self.created_version_)
    if (self.has_updated_version_):
      out.putVarInt32(16)
      out.putVarInt64(self.updated_version_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_created_version(d.getVarInt64())
        continue
      if tt == 16:
        self.set_updated_version(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_created_version_: res+=prefix+("created_version: %s\n" % self.DebugFormatInt64(self.created_version_))
    if self.has_updated_version_: res+=prefix+("updated_version: %s\n" % self.DebugFormatInt64(self.updated_version_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kcreated_version = 1
  kupdated_version = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "created_version",
    2: "updated_version",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.EntityMetadata'
class CompositeProperty(ProtocolBuffer.ProtocolMessage):
  has_index_id_ = 0
  index_id_ = 0

  def __init__(self, contents=None):
    self.value_ = []
    if contents is not None: self.MergeFromString(contents)

  def index_id(self): return self.index_id_

  def set_index_id(self, x):
    self.has_index_id_ = 1
    self.index_id_ = x

  def clear_index_id(self):
    if self.has_index_id_:
      self.has_index_id_ = 0
      self.index_id_ = 0

  def has_index_id(self): return self.has_index_id_

  def value_size(self): return len(self.value_)
  def value_list(self): return self.value_

  def value(self, i):
    return self.value_[i]

  def set_value(self, i, x):
    self.value_[i] = x

  def add_value(self, x):
    self.value_.append(x)

  def clear_value(self):
    self.value_ = []


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_index_id()): self.set_index_id(x.index_id())
    for i in xrange(x.value_size()): self.add_value(x.value(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_index_id_ != x.has_index_id_: return 0
    if self.has_index_id_ and self.index_id_ != x.index_id_: return 0
    if len(self.value_) != len(x.value_): return 0
    for e1, e2 in zip(self.value_, x.value_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_index_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: index_id not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.index_id_)
    n += 1 * len(self.value_)
    for i in xrange(len(self.value_)): n += self.lengthString(len(self.value_[i]))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_index_id_):
      n += 1
      n += self.lengthVarInt64(self.index_id_)
    n += 1 * len(self.value_)
    for i in xrange(len(self.value_)): n += self.lengthString(len(self.value_[i]))
    return n

  def Clear(self):
    self.clear_index_id()
    self.clear_value()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt64(self.index_id_)
    for i in xrange(len(self.value_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.value_[i])

  def OutputPartial(self, out):
    if (self.has_index_id_):
      out.putVarInt32(8)
      out.putVarInt64(self.index_id_)
    for i in xrange(len(self.value_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.value_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_index_id(d.getVarInt64())
        continue
      if tt == 18:
        self.add_value(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_index_id_: res+=prefix+("index_id: %s\n" % self.DebugFormatInt64(self.index_id_))
    cnt=0
    for e in self.value_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("value%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kindex_id = 1
  kvalue = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "index_id",
    2: "value",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.CompositeProperty'
class Index_Property(ProtocolBuffer.ProtocolMessage):


  DIRECTION_UNSPECIFIED =    0
  ASCENDING    =    1
  DESCENDING   =    2

  _Direction_NAMES = {
    0: "DIRECTION_UNSPECIFIED",
    1: "ASCENDING",
    2: "DESCENDING",
  }

  def Direction_Name(cls, x): return cls._Direction_NAMES.get(x, "")
  Direction_Name = classmethod(Direction_Name)



  MODE_UNSPECIFIED =    0
  GEOSPATIAL   =    3

  _Mode_NAMES = {
    0: "MODE_UNSPECIFIED",
    3: "GEOSPATIAL",
  }

  def Mode_Name(cls, x): return cls._Mode_NAMES.get(x, "")
  Mode_Name = classmethod(Mode_Name)

  has_name_ = 0
  name_ = ""
  has_direction_ = 0
  direction_ = 0
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

  def direction(self): return self.direction_

  def set_direction(self, x):
    self.has_direction_ = 1
    self.direction_ = x

  def clear_direction(self):
    if self.has_direction_:
      self.has_direction_ = 0
      self.direction_ = 0

  def has_direction(self): return self.has_direction_

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
    if (x.has_direction()): self.set_direction(x.direction())
    if (x.has_mode()): self.set_mode(x.mode())

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if self.has_direction_ != x.has_direction_: return 0
    if self.has_direction_ and self.direction_ != x.direction_: return 0
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
    if (self.has_direction_): n += 1 + self.lengthVarInt64(self.direction_)
    if (self.has_mode_): n += 1 + self.lengthVarInt64(self.mode_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    if (self.has_direction_): n += 1 + self.lengthVarInt64(self.direction_)
    if (self.has_mode_): n += 1 + self.lengthVarInt64(self.mode_)
    return n

  def Clear(self):
    self.clear_name()
    self.clear_direction()
    self.clear_mode()

  def OutputUnchecked(self, out):
    out.putVarInt32(26)
    out.putPrefixedString(self.name_)
    if (self.has_direction_):
      out.putVarInt32(32)
      out.putVarInt32(self.direction_)
    if (self.has_mode_):
      out.putVarInt32(48)
      out.putVarInt32(self.mode_)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.name_)
    if (self.has_direction_):
      out.putVarInt32(32)
      out.putVarInt32(self.direction_)
    if (self.has_mode_):
      out.putVarInt32(48)
      out.putVarInt32(self.mode_)

  def TryMerge(self, d):
    while 1:
      tt = d.getVarInt32()
      if tt == 20: break
      if tt == 26:
        self.set_name(d.getPrefixedString())
        continue
      if tt == 32:
        self.set_direction(d.getVarInt32())
        continue
      if tt == 48:
        self.set_mode(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    if self.has_direction_: res+=prefix+("direction: %s\n" % self.DebugFormatInt32(self.direction_))
    if self.has_mode_: res+=prefix+("mode: %s\n" % self.DebugFormatInt32(self.mode_))
    return res

class Index(ProtocolBuffer.ProtocolMessage):
  has_entity_type_ = 0
  entity_type_ = ""
  has_ancestor_ = 0
  ancestor_ = 0

  def __init__(self, contents=None):
    self.property_ = []
    if contents is not None: self.MergeFromString(contents)

  def entity_type(self): return self.entity_type_

  def set_entity_type(self, x):
    self.has_entity_type_ = 1
    self.entity_type_ = x

  def clear_entity_type(self):
    if self.has_entity_type_:
      self.has_entity_type_ = 0
      self.entity_type_ = ""

  def has_entity_type(self): return self.has_entity_type_

  def ancestor(self): return self.ancestor_

  def set_ancestor(self, x):
    self.has_ancestor_ = 1
    self.ancestor_ = x

  def clear_ancestor(self):
    if self.has_ancestor_:
      self.has_ancestor_ = 0
      self.ancestor_ = 0

  def has_ancestor(self): return self.has_ancestor_

  def property_size(self): return len(self.property_)
  def property_list(self): return self.property_

  def property(self, i):
    return self.property_[i]

  def mutable_property(self, i):
    return self.property_[i]

  def add_property(self):
    x = Index_Property()
    self.property_.append(x)
    return x

  def clear_property(self):
    self.property_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_entity_type()): self.set_entity_type(x.entity_type())
    if (x.has_ancestor()): self.set_ancestor(x.ancestor())
    for i in xrange(x.property_size()): self.add_property().CopyFrom(x.property(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_entity_type_ != x.has_entity_type_: return 0
    if self.has_entity_type_ and self.entity_type_ != x.entity_type_: return 0
    if self.has_ancestor_ != x.has_ancestor_: return 0
    if self.has_ancestor_ and self.ancestor_ != x.ancestor_: return 0
    if len(self.property_) != len(x.property_): return 0
    for e1, e2 in zip(self.property_, x.property_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_entity_type_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: entity_type not set.')
    if (not self.has_ancestor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: ancestor not set.')
    for p in self.property_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.entity_type_))
    n += 2 * len(self.property_)
    for i in xrange(len(self.property_)): n += self.property_[i].ByteSize()
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_entity_type_):
      n += 1
      n += self.lengthString(len(self.entity_type_))
    if (self.has_ancestor_):
      n += 2
    n += 2 * len(self.property_)
    for i in xrange(len(self.property_)): n += self.property_[i].ByteSizePartial()
    return n

  def Clear(self):
    self.clear_entity_type()
    self.clear_ancestor()
    self.clear_property()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.entity_type_)
    for i in xrange(len(self.property_)):
      out.putVarInt32(19)
      self.property_[i].OutputUnchecked(out)
      out.putVarInt32(20)
    out.putVarInt32(40)
    out.putBoolean(self.ancestor_)

  def OutputPartial(self, out):
    if (self.has_entity_type_):
      out.putVarInt32(10)
      out.putPrefixedString(self.entity_type_)
    for i in xrange(len(self.property_)):
      out.putVarInt32(19)
      self.property_[i].OutputPartial(out)
      out.putVarInt32(20)
    if (self.has_ancestor_):
      out.putVarInt32(40)
      out.putBoolean(self.ancestor_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_entity_type(d.getPrefixedString())
        continue
      if tt == 19:
        self.add_property().TryMerge(d)
        continue
      if tt == 40:
        self.set_ancestor(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_entity_type_: res+=prefix+("entity_type: %s\n" % self.DebugFormatString(self.entity_type_))
    if self.has_ancestor_: res+=prefix+("ancestor: %s\n" % self.DebugFormatBool(self.ancestor_))
    cnt=0
    for e in self.property_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("Property%s {\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+"}\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kentity_type = 1
  kancestor = 5
  kPropertyGroup = 2
  kPropertyname = 3
  kPropertydirection = 4
  kPropertymode = 6

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "entity_type",
    2: "Property",
    3: "name",
    4: "direction",
    5: "ancestor",
    6: "mode",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STARTGROUP,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.NUMERIC,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.Index'
class CompositeIndex(ProtocolBuffer.ProtocolMessage):


  WRITE_ONLY   =    1
  READ_WRITE   =    2
  DELETED      =    3
  ERROR        =    4

  _State_NAMES = {
    1: "WRITE_ONLY",
    2: "READ_WRITE",
    3: "DELETED",
    4: "ERROR",
  }

  def State_Name(cls, x): return cls._State_NAMES.get(x, "")
  State_Name = classmethod(State_Name)



  PENDING      =    1
  ACTIVE       =    2
  COMPLETED    =    3

  _WorkflowState_NAMES = {
    1: "PENDING",
    2: "ACTIVE",
    3: "COMPLETED",
  }

  def WorkflowState_Name(cls, x): return cls._WorkflowState_NAMES.get(x, "")
  WorkflowState_Name = classmethod(WorkflowState_Name)

  has_app_id_ = 0
  app_id_ = ""
  has_database_id_ = 0
  database_id_ = ""
  has_id_ = 0
  id_ = 0
  has_definition_ = 0
  has_state_ = 0
  state_ = 0
  has_workflow_state_ = 0
  workflow_state_ = 0
  has_error_message_ = 0
  error_message_ = ""
  has_only_use_if_required_ = 0
  only_use_if_required_ = 0
  has_disabled_index_ = 0
  disabled_index_ = 0
  has_write_division_family_ = 0
  write_division_family_ = ""

  def __init__(self, contents=None):
    self.definition_ = Index()
    self.read_division_family_ = []
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

  def database_id(self): return self.database_id_

  def set_database_id(self, x):
    self.has_database_id_ = 1
    self.database_id_ = x

  def clear_database_id(self):
    if self.has_database_id_:
      self.has_database_id_ = 0
      self.database_id_ = ""

  def has_database_id(self): return self.has_database_id_

  def id(self): return self.id_

  def set_id(self, x):
    self.has_id_ = 1
    self.id_ = x

  def clear_id(self):
    if self.has_id_:
      self.has_id_ = 0
      self.id_ = 0

  def has_id(self): return self.has_id_

  def definition(self): return self.definition_

  def mutable_definition(self): self.has_definition_ = 1; return self.definition_

  def clear_definition(self):self.has_definition_ = 0; self.definition_.Clear()

  def has_definition(self): return self.has_definition_

  def state(self): return self.state_

  def set_state(self, x):
    self.has_state_ = 1
    self.state_ = x

  def clear_state(self):
    if self.has_state_:
      self.has_state_ = 0
      self.state_ = 0

  def has_state(self): return self.has_state_

  def workflow_state(self): return self.workflow_state_

  def set_workflow_state(self, x):
    self.has_workflow_state_ = 1
    self.workflow_state_ = x

  def clear_workflow_state(self):
    if self.has_workflow_state_:
      self.has_workflow_state_ = 0
      self.workflow_state_ = 0

  def has_workflow_state(self): return self.has_workflow_state_

  def error_message(self): return self.error_message_

  def set_error_message(self, x):
    self.has_error_message_ = 1
    self.error_message_ = x

  def clear_error_message(self):
    if self.has_error_message_:
      self.has_error_message_ = 0
      self.error_message_ = ""

  def has_error_message(self): return self.has_error_message_

  def only_use_if_required(self): return self.only_use_if_required_

  def set_only_use_if_required(self, x):
    self.has_only_use_if_required_ = 1
    self.only_use_if_required_ = x

  def clear_only_use_if_required(self):
    if self.has_only_use_if_required_:
      self.has_only_use_if_required_ = 0
      self.only_use_if_required_ = 0

  def has_only_use_if_required(self): return self.has_only_use_if_required_

  def disabled_index(self): return self.disabled_index_

  def set_disabled_index(self, x):
    self.has_disabled_index_ = 1
    self.disabled_index_ = x

  def clear_disabled_index(self):
    if self.has_disabled_index_:
      self.has_disabled_index_ = 0
      self.disabled_index_ = 0

  def has_disabled_index(self): return self.has_disabled_index_

  def read_division_family_size(self): return len(self.read_division_family_)
  def read_division_family_list(self): return self.read_division_family_

  def read_division_family(self, i):
    return self.read_division_family_[i]

  def set_read_division_family(self, i, x):
    self.read_division_family_[i] = x

  def add_read_division_family(self, x):
    self.read_division_family_.append(x)

  def clear_read_division_family(self):
    self.read_division_family_ = []

  def write_division_family(self): return self.write_division_family_

  def set_write_division_family(self, x):
    self.has_write_division_family_ = 1
    self.write_division_family_ = x

  def clear_write_division_family(self):
    if self.has_write_division_family_:
      self.has_write_division_family_ = 0
      self.write_division_family_ = ""

  def has_write_division_family(self): return self.has_write_division_family_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_database_id()): self.set_database_id(x.database_id())
    if (x.has_id()): self.set_id(x.id())
    if (x.has_definition()): self.mutable_definition().MergeFrom(x.definition())
    if (x.has_state()): self.set_state(x.state())
    if (x.has_workflow_state()): self.set_workflow_state(x.workflow_state())
    if (x.has_error_message()): self.set_error_message(x.error_message())
    if (x.has_only_use_if_required()): self.set_only_use_if_required(x.only_use_if_required())
    if (x.has_disabled_index()): self.set_disabled_index(x.disabled_index())
    for i in xrange(x.read_division_family_size()): self.add_read_division_family(x.read_division_family(i))
    if (x.has_write_division_family()): self.set_write_division_family(x.write_division_family())

  def Equals(self, x):
    if x is self: return 1
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_database_id_ != x.has_database_id_: return 0
    if self.has_database_id_ and self.database_id_ != x.database_id_: return 0
    if self.has_id_ != x.has_id_: return 0
    if self.has_id_ and self.id_ != x.id_: return 0
    if self.has_definition_ != x.has_definition_: return 0
    if self.has_definition_ and self.definition_ != x.definition_: return 0
    if self.has_state_ != x.has_state_: return 0
    if self.has_state_ and self.state_ != x.state_: return 0
    if self.has_workflow_state_ != x.has_workflow_state_: return 0
    if self.has_workflow_state_ and self.workflow_state_ != x.workflow_state_: return 0
    if self.has_error_message_ != x.has_error_message_: return 0
    if self.has_error_message_ and self.error_message_ != x.error_message_: return 0
    if self.has_only_use_if_required_ != x.has_only_use_if_required_: return 0
    if self.has_only_use_if_required_ and self.only_use_if_required_ != x.only_use_if_required_: return 0
    if self.has_disabled_index_ != x.has_disabled_index_: return 0
    if self.has_disabled_index_ and self.disabled_index_ != x.disabled_index_: return 0
    if len(self.read_division_family_) != len(x.read_division_family_): return 0
    for e1, e2 in zip(self.read_division_family_, x.read_division_family_):
      if e1 != e2: return 0
    if self.has_write_division_family_ != x.has_write_division_family_: return 0
    if self.has_write_division_family_ and self.write_division_family_ != x.write_division_family_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_app_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: app_id not set.')
    if (not self.has_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: id not set.')
    if (not self.has_definition_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: definition not set.')
    elif not self.definition_.IsInitialized(debug_strs): initialized = 0
    if (not self.has_state_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: state not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.app_id_))
    if (self.has_database_id_): n += 1 + self.lengthString(len(self.database_id_))
    n += self.lengthVarInt64(self.id_)
    n += self.lengthString(self.definition_.ByteSize())
    n += self.lengthVarInt64(self.state_)
    if (self.has_workflow_state_): n += 1 + self.lengthVarInt64(self.workflow_state_)
    if (self.has_error_message_): n += 1 + self.lengthString(len(self.error_message_))
    if (self.has_only_use_if_required_): n += 2
    if (self.has_disabled_index_): n += 2
    n += 1 * len(self.read_division_family_)
    for i in xrange(len(self.read_division_family_)): n += self.lengthString(len(self.read_division_family_[i]))
    if (self.has_write_division_family_): n += 1 + self.lengthString(len(self.write_division_family_))
    return n + 4

  def ByteSizePartial(self):
    n = 0
    if (self.has_app_id_):
      n += 1
      n += self.lengthString(len(self.app_id_))
    if (self.has_database_id_): n += 1 + self.lengthString(len(self.database_id_))
    if (self.has_id_):
      n += 1
      n += self.lengthVarInt64(self.id_)
    if (self.has_definition_):
      n += 1
      n += self.lengthString(self.definition_.ByteSizePartial())
    if (self.has_state_):
      n += 1
      n += self.lengthVarInt64(self.state_)
    if (self.has_workflow_state_): n += 1 + self.lengthVarInt64(self.workflow_state_)
    if (self.has_error_message_): n += 1 + self.lengthString(len(self.error_message_))
    if (self.has_only_use_if_required_): n += 2
    if (self.has_disabled_index_): n += 2
    n += 1 * len(self.read_division_family_)
    for i in xrange(len(self.read_division_family_)): n += self.lengthString(len(self.read_division_family_[i]))
    if (self.has_write_division_family_): n += 1 + self.lengthString(len(self.write_division_family_))
    return n

  def Clear(self):
    self.clear_app_id()
    self.clear_database_id()
    self.clear_id()
    self.clear_definition()
    self.clear_state()
    self.clear_workflow_state()
    self.clear_error_message()
    self.clear_only_use_if_required()
    self.clear_disabled_index()
    self.clear_read_division_family()
    self.clear_write_division_family()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.app_id_)
    out.putVarInt32(16)
    out.putVarInt64(self.id_)
    out.putVarInt32(26)
    out.putVarInt32(self.definition_.ByteSize())
    self.definition_.OutputUnchecked(out)
    out.putVarInt32(32)
    out.putVarInt32(self.state_)
    if (self.has_only_use_if_required_):
      out.putVarInt32(48)
      out.putBoolean(self.only_use_if_required_)
    for i in xrange(len(self.read_division_family_)):
      out.putVarInt32(58)
      out.putPrefixedString(self.read_division_family_[i])
    if (self.has_write_division_family_):
      out.putVarInt32(66)
      out.putPrefixedString(self.write_division_family_)
    if (self.has_disabled_index_):
      out.putVarInt32(72)
      out.putBoolean(self.disabled_index_)
    if (self.has_workflow_state_):
      out.putVarInt32(80)
      out.putVarInt32(self.workflow_state_)
    if (self.has_error_message_):
      out.putVarInt32(90)
      out.putPrefixedString(self.error_message_)
    if (self.has_database_id_):
      out.putVarInt32(98)
      out.putPrefixedString(self.database_id_)

  def OutputPartial(self, out):
    if (self.has_app_id_):
      out.putVarInt32(10)
      out.putPrefixedString(self.app_id_)
    if (self.has_id_):
      out.putVarInt32(16)
      out.putVarInt64(self.id_)
    if (self.has_definition_):
      out.putVarInt32(26)
      out.putVarInt32(self.definition_.ByteSizePartial())
      self.definition_.OutputPartial(out)
    if (self.has_state_):
      out.putVarInt32(32)
      out.putVarInt32(self.state_)
    if (self.has_only_use_if_required_):
      out.putVarInt32(48)
      out.putBoolean(self.only_use_if_required_)
    for i in xrange(len(self.read_division_family_)):
      out.putVarInt32(58)
      out.putPrefixedString(self.read_division_family_[i])
    if (self.has_write_division_family_):
      out.putVarInt32(66)
      out.putPrefixedString(self.write_division_family_)
    if (self.has_disabled_index_):
      out.putVarInt32(72)
      out.putBoolean(self.disabled_index_)
    if (self.has_workflow_state_):
      out.putVarInt32(80)
      out.putVarInt32(self.workflow_state_)
    if (self.has_error_message_):
      out.putVarInt32(90)
      out.putPrefixedString(self.error_message_)
    if (self.has_database_id_):
      out.putVarInt32(98)
      out.putPrefixedString(self.database_id_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_id(d.getVarInt64())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_definition().TryMerge(tmp)
        continue
      if tt == 32:
        self.set_state(d.getVarInt32())
        continue
      if tt == 48:
        self.set_only_use_if_required(d.getBoolean())
        continue
      if tt == 58:
        self.add_read_division_family(d.getPrefixedString())
        continue
      if tt == 66:
        self.set_write_division_family(d.getPrefixedString())
        continue
      if tt == 72:
        self.set_disabled_index(d.getBoolean())
        continue
      if tt == 80:
        self.set_workflow_state(d.getVarInt32())
        continue
      if tt == 90:
        self.set_error_message(d.getPrefixedString())
        continue
      if tt == 98:
        self.set_database_id(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_database_id_: res+=prefix+("database_id: %s\n" % self.DebugFormatString(self.database_id_))
    if self.has_id_: res+=prefix+("id: %s\n" % self.DebugFormatInt64(self.id_))
    if self.has_definition_:
      res+=prefix+"definition <\n"
      res+=self.definition_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_state_: res+=prefix+("state: %s\n" % self.DebugFormatInt32(self.state_))
    if self.has_workflow_state_: res+=prefix+("workflow_state: %s\n" % self.DebugFormatInt32(self.workflow_state_))
    if self.has_error_message_: res+=prefix+("error_message: %s\n" % self.DebugFormatString(self.error_message_))
    if self.has_only_use_if_required_: res+=prefix+("only_use_if_required: %s\n" % self.DebugFormatBool(self.only_use_if_required_))
    if self.has_disabled_index_: res+=prefix+("disabled_index: %s\n" % self.DebugFormatBool(self.disabled_index_))
    cnt=0
    for e in self.read_division_family_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("read_division_family%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_write_division_family_: res+=prefix+("write_division_family: %s\n" % self.DebugFormatString(self.write_division_family_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kapp_id = 1
  kdatabase_id = 12
  kid = 2
  kdefinition = 3
  kstate = 4
  kworkflow_state = 10
  kerror_message = 11
  konly_use_if_required = 6
  kdisabled_index = 9
  kread_division_family = 7
  kwrite_division_family = 8

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "app_id",
    2: "id",
    3: "definition",
    4: "state",
    6: "only_use_if_required",
    7: "read_division_family",
    8: "write_division_family",
    9: "disabled_index",
    10: "workflow_state",
    11: "error_message",
    12: "database_id",
  }, 12)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.NUMERIC,
    7: ProtocolBuffer.Encoder.STRING,
    8: ProtocolBuffer.Encoder.STRING,
    9: ProtocolBuffer.Encoder.NUMERIC,
    10: ProtocolBuffer.Encoder.NUMERIC,
    11: ProtocolBuffer.Encoder.STRING,
    12: ProtocolBuffer.Encoder.STRING,
  }, 12, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.CompositeIndex'
class SearchIndexEntry(ProtocolBuffer.ProtocolMessage):
  has_index_id_ = 0
  index_id_ = 0
  has_write_division_family_ = 0
  write_division_family_ = ""
  has_fingerprint_1999_ = 0
  fingerprint_1999_ = 0
  has_fingerprint_2011_ = 0
  fingerprint_2011_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def index_id(self): return self.index_id_

  def set_index_id(self, x):
    self.has_index_id_ = 1
    self.index_id_ = x

  def clear_index_id(self):
    if self.has_index_id_:
      self.has_index_id_ = 0
      self.index_id_ = 0

  def has_index_id(self): return self.has_index_id_

  def write_division_family(self): return self.write_division_family_

  def set_write_division_family(self, x):
    self.has_write_division_family_ = 1
    self.write_division_family_ = x

  def clear_write_division_family(self):
    if self.has_write_division_family_:
      self.has_write_division_family_ = 0
      self.write_division_family_ = ""

  def has_write_division_family(self): return self.has_write_division_family_

  def fingerprint_1999(self): return self.fingerprint_1999_

  def set_fingerprint_1999(self, x):
    self.has_fingerprint_1999_ = 1
    self.fingerprint_1999_ = x

  def clear_fingerprint_1999(self):
    if self.has_fingerprint_1999_:
      self.has_fingerprint_1999_ = 0
      self.fingerprint_1999_ = 0

  def has_fingerprint_1999(self): return self.has_fingerprint_1999_

  def fingerprint_2011(self): return self.fingerprint_2011_

  def set_fingerprint_2011(self, x):
    self.has_fingerprint_2011_ = 1
    self.fingerprint_2011_ = x

  def clear_fingerprint_2011(self):
    if self.has_fingerprint_2011_:
      self.has_fingerprint_2011_ = 0
      self.fingerprint_2011_ = 0

  def has_fingerprint_2011(self): return self.has_fingerprint_2011_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_index_id()): self.set_index_id(x.index_id())
    if (x.has_write_division_family()): self.set_write_division_family(x.write_division_family())
    if (x.has_fingerprint_1999()): self.set_fingerprint_1999(x.fingerprint_1999())
    if (x.has_fingerprint_2011()): self.set_fingerprint_2011(x.fingerprint_2011())

  def Equals(self, x):
    if x is self: return 1
    if self.has_index_id_ != x.has_index_id_: return 0
    if self.has_index_id_ and self.index_id_ != x.index_id_: return 0
    if self.has_write_division_family_ != x.has_write_division_family_: return 0
    if self.has_write_division_family_ and self.write_division_family_ != x.write_division_family_: return 0
    if self.has_fingerprint_1999_ != x.has_fingerprint_1999_: return 0
    if self.has_fingerprint_1999_ and self.fingerprint_1999_ != x.fingerprint_1999_: return 0
    if self.has_fingerprint_2011_ != x.has_fingerprint_2011_: return 0
    if self.has_fingerprint_2011_ and self.fingerprint_2011_ != x.fingerprint_2011_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_index_id_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: index_id not set.')
    if (not self.has_write_division_family_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: write_division_family not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.index_id_)
    n += self.lengthString(len(self.write_division_family_))
    if (self.has_fingerprint_1999_): n += 9
    if (self.has_fingerprint_2011_): n += 9
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_index_id_):
      n += 1
      n += self.lengthVarInt64(self.index_id_)
    if (self.has_write_division_family_):
      n += 1
      n += self.lengthString(len(self.write_division_family_))
    if (self.has_fingerprint_1999_): n += 9
    if (self.has_fingerprint_2011_): n += 9
    return n

  def Clear(self):
    self.clear_index_id()
    self.clear_write_division_family()
    self.clear_fingerprint_1999()
    self.clear_fingerprint_2011()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt64(self.index_id_)
    out.putVarInt32(18)
    out.putPrefixedString(self.write_division_family_)
    if (self.has_fingerprint_1999_):
      out.putVarInt32(25)
      out.put64(self.fingerprint_1999_)
    if (self.has_fingerprint_2011_):
      out.putVarInt32(33)
      out.put64(self.fingerprint_2011_)

  def OutputPartial(self, out):
    if (self.has_index_id_):
      out.putVarInt32(8)
      out.putVarInt64(self.index_id_)
    if (self.has_write_division_family_):
      out.putVarInt32(18)
      out.putPrefixedString(self.write_division_family_)
    if (self.has_fingerprint_1999_):
      out.putVarInt32(25)
      out.put64(self.fingerprint_1999_)
    if (self.has_fingerprint_2011_):
      out.putVarInt32(33)
      out.put64(self.fingerprint_2011_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_index_id(d.getVarInt64())
        continue
      if tt == 18:
        self.set_write_division_family(d.getPrefixedString())
        continue
      if tt == 25:
        self.set_fingerprint_1999(d.get64())
        continue
      if tt == 33:
        self.set_fingerprint_2011(d.get64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_index_id_: res+=prefix+("index_id: %s\n" % self.DebugFormatInt64(self.index_id_))
    if self.has_write_division_family_: res+=prefix+("write_division_family: %s\n" % self.DebugFormatString(self.write_division_family_))
    if self.has_fingerprint_1999_: res+=prefix+("fingerprint_1999: %s\n" % self.DebugFormatFixed64(self.fingerprint_1999_))
    if self.has_fingerprint_2011_: res+=prefix+("fingerprint_2011: %s\n" % self.DebugFormatFixed64(self.fingerprint_2011_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kindex_id = 1
  kwrite_division_family = 2
  kfingerprint_1999 = 3
  kfingerprint_2011 = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "index_id",
    2: "write_division_family",
    3: "fingerprint_1999",
    4: "fingerprint_2011",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.DOUBLE,
    4: ProtocolBuffer.Encoder.DOUBLE,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.SearchIndexEntry'
class IndexPostfix_IndexValue(ProtocolBuffer.ProtocolMessage):
  has_property_name_ = 0
  property_name_ = ""
  has_value_ = 0

  def __init__(self, contents=None):
    self.value_ = PropertyValue()
    if contents is not None: self.MergeFromString(contents)

  def property_name(self): return self.property_name_

  def set_property_name(self, x):
    self.has_property_name_ = 1
    self.property_name_ = x

  def clear_property_name(self):
    if self.has_property_name_:
      self.has_property_name_ = 0
      self.property_name_ = ""

  def has_property_name(self): return self.has_property_name_

  def value(self): return self.value_

  def mutable_value(self): self.has_value_ = 1; return self.value_

  def clear_value(self):self.has_value_ = 0; self.value_.Clear()

  def has_value(self): return self.has_value_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_property_name()): self.set_property_name(x.property_name())
    if (x.has_value()): self.mutable_value().MergeFrom(x.value())

  def Equals(self, x):
    if x is self: return 1
    if self.has_property_name_ != x.has_property_name_: return 0
    if self.has_property_name_ and self.property_name_ != x.property_name_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_property_name_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: property_name not set.')
    if (not self.has_value_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: value not set.')
    elif not self.value_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.property_name_))
    n += self.lengthString(self.value_.ByteSize())
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_property_name_):
      n += 1
      n += self.lengthString(len(self.property_name_))
    if (self.has_value_):
      n += 1
      n += self.lengthString(self.value_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_property_name()
    self.clear_value()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.property_name_)
    out.putVarInt32(18)
    out.putVarInt32(self.value_.ByteSize())
    self.value_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_property_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.property_name_)
    if (self.has_value_):
      out.putVarInt32(18)
      out.putVarInt32(self.value_.ByteSizePartial())
      self.value_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_property_name(d.getPrefixedString())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_value().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_property_name_: res+=prefix+("property_name: %s\n" % self.DebugFormatString(self.property_name_))
    if self.has_value_:
      res+=prefix+"value <\n"
      res+=self.value_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kproperty_name = 1
  kvalue = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "property_name",
    2: "value",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.IndexPostfix_IndexValue'
class IndexPostfix(ProtocolBuffer.ProtocolMessage):
  has_key_ = 0
  key_ = None
  has_before_ = 0
  before_ = 1
  has_before_ascending_ = 0
  before_ascending_ = 0

  def __init__(self, contents=None):
    self.index_value_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def index_value_size(self): return len(self.index_value_)
  def index_value_list(self): return self.index_value_

  def index_value(self, i):
    return self.index_value_[i]

  def mutable_index_value(self, i):
    return self.index_value_[i]

  def add_index_value(self):
    x = IndexPostfix_IndexValue()
    self.index_value_.append(x)
    return x

  def clear_index_value(self):
    self.index_value_ = []
  def key(self):
    if self.key_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.key_ is None: self.key_ = Reference()
      finally:
        self.lazy_init_lock_.release()
    return self.key_

  def mutable_key(self): self.has_key_ = 1; return self.key()

  def clear_key(self):

    if self.has_key_:
      self.has_key_ = 0;
      if self.key_ is not None: self.key_.Clear()

  def has_key(self): return self.has_key_

  def before(self): return self.before_

  def set_before(self, x):
    self.has_before_ = 1
    self.before_ = x

  def clear_before(self):
    if self.has_before_:
      self.has_before_ = 0
      self.before_ = 1

  def has_before(self): return self.has_before_

  def before_ascending(self): return self.before_ascending_

  def set_before_ascending(self, x):
    self.has_before_ascending_ = 1
    self.before_ascending_ = x

  def clear_before_ascending(self):
    if self.has_before_ascending_:
      self.has_before_ascending_ = 0
      self.before_ascending_ = 0

  def has_before_ascending(self): return self.has_before_ascending_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.index_value_size()): self.add_index_value().CopyFrom(x.index_value(i))
    if (x.has_key()): self.mutable_key().MergeFrom(x.key())
    if (x.has_before()): self.set_before(x.before())
    if (x.has_before_ascending()): self.set_before_ascending(x.before_ascending())

  def Equals(self, x):
    if x is self: return 1
    if len(self.index_value_) != len(x.index_value_): return 0
    for e1, e2 in zip(self.index_value_, x.index_value_):
      if e1 != e2: return 0
    if self.has_key_ != x.has_key_: return 0
    if self.has_key_ and self.key_ != x.key_: return 0
    if self.has_before_ != x.has_before_: return 0
    if self.has_before_ and self.before_ != x.before_: return 0
    if self.has_before_ascending_ != x.has_before_ascending_: return 0
    if self.has_before_ascending_ and self.before_ascending_ != x.before_ascending_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.index_value_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_key_ and not self.key_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.index_value_)
    for i in xrange(len(self.index_value_)): n += self.lengthString(self.index_value_[i].ByteSize())
    if (self.has_key_): n += 1 + self.lengthString(self.key_.ByteSize())
    if (self.has_before_): n += 2
    if (self.has_before_ascending_): n += 2
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.index_value_)
    for i in xrange(len(self.index_value_)): n += self.lengthString(self.index_value_[i].ByteSizePartial())
    if (self.has_key_): n += 1 + self.lengthString(self.key_.ByteSizePartial())
    if (self.has_before_): n += 2
    if (self.has_before_ascending_): n += 2
    return n

  def Clear(self):
    self.clear_index_value()
    self.clear_key()
    self.clear_before()
    self.clear_before_ascending()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.index_value_)):
      out.putVarInt32(10)
      out.putVarInt32(self.index_value_[i].ByteSize())
      self.index_value_[i].OutputUnchecked(out)
    if (self.has_key_):
      out.putVarInt32(18)
      out.putVarInt32(self.key_.ByteSize())
      self.key_.OutputUnchecked(out)
    if (self.has_before_):
      out.putVarInt32(24)
      out.putBoolean(self.before_)
    if (self.has_before_ascending_):
      out.putVarInt32(32)
      out.putBoolean(self.before_ascending_)

  def OutputPartial(self, out):
    for i in xrange(len(self.index_value_)):
      out.putVarInt32(10)
      out.putVarInt32(self.index_value_[i].ByteSizePartial())
      self.index_value_[i].OutputPartial(out)
    if (self.has_key_):
      out.putVarInt32(18)
      out.putVarInt32(self.key_.ByteSizePartial())
      self.key_.OutputPartial(out)
    if (self.has_before_):
      out.putVarInt32(24)
      out.putBoolean(self.before_)
    if (self.has_before_ascending_):
      out.putVarInt32(32)
      out.putBoolean(self.before_ascending_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_index_value().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_key().TryMerge(tmp)
        continue
      if tt == 24:
        self.set_before(d.getBoolean())
        continue
      if tt == 32:
        self.set_before_ascending(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.index_value_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("index_value%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_key_:
      res+=prefix+"key <\n"
      res+=self.key_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_before_: res+=prefix+("before: %s\n" % self.DebugFormatBool(self.before_))
    if self.has_before_ascending_: res+=prefix+("before_ascending: %s\n" % self.DebugFormatBool(self.before_ascending_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kindex_value = 1
  kkey = 2
  kbefore = 3
  kbefore_ascending = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "index_value",
    2: "key",
    3: "before",
    4: "before_ascending",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.IndexPostfix'
class IndexPosition(ProtocolBuffer.ProtocolMessage):
  has_key_ = 0
  key_ = ""
  has_before_ = 0
  before_ = 1
  has_before_ascending_ = 0
  before_ascending_ = 0

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

  def before(self): return self.before_

  def set_before(self, x):
    self.has_before_ = 1
    self.before_ = x

  def clear_before(self):
    if self.has_before_:
      self.has_before_ = 0
      self.before_ = 1

  def has_before(self): return self.has_before_

  def before_ascending(self): return self.before_ascending_

  def set_before_ascending(self, x):
    self.has_before_ascending_ = 1
    self.before_ascending_ = x

  def clear_before_ascending(self):
    if self.has_before_ascending_:
      self.has_before_ascending_ = 0
      self.before_ascending_ = 0

  def has_before_ascending(self): return self.has_before_ascending_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_key()): self.set_key(x.key())
    if (x.has_before()): self.set_before(x.before())
    if (x.has_before_ascending()): self.set_before_ascending(x.before_ascending())

  def Equals(self, x):
    if x is self: return 1
    if self.has_key_ != x.has_key_: return 0
    if self.has_key_ and self.key_ != x.key_: return 0
    if self.has_before_ != x.has_before_: return 0
    if self.has_before_ and self.before_ != x.before_: return 0
    if self.has_before_ascending_ != x.has_before_ascending_: return 0
    if self.has_before_ascending_ and self.before_ascending_ != x.before_ascending_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_key_): n += 1 + self.lengthString(len(self.key_))
    if (self.has_before_): n += 2
    if (self.has_before_ascending_): n += 2
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_key_): n += 1 + self.lengthString(len(self.key_))
    if (self.has_before_): n += 2
    if (self.has_before_ascending_): n += 2
    return n

  def Clear(self):
    self.clear_key()
    self.clear_before()
    self.clear_before_ascending()

  def OutputUnchecked(self, out):
    if (self.has_key_):
      out.putVarInt32(10)
      out.putPrefixedString(self.key_)
    if (self.has_before_):
      out.putVarInt32(16)
      out.putBoolean(self.before_)
    if (self.has_before_ascending_):
      out.putVarInt32(24)
      out.putBoolean(self.before_ascending_)

  def OutputPartial(self, out):
    if (self.has_key_):
      out.putVarInt32(10)
      out.putPrefixedString(self.key_)
    if (self.has_before_):
      out.putVarInt32(16)
      out.putBoolean(self.before_)
    if (self.has_before_ascending_):
      out.putVarInt32(24)
      out.putBoolean(self.before_ascending_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_key(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_before(d.getBoolean())
        continue
      if tt == 24:
        self.set_before_ascending(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_: res+=prefix+("key: %s\n" % self.DebugFormatString(self.key_))
    if self.has_before_: res+=prefix+("before: %s\n" % self.DebugFormatBool(self.before_))
    if self.has_before_ascending_: res+=prefix+("before_ascending: %s\n" % self.DebugFormatBool(self.before_ascending_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kkey = 1
  kbefore = 2
  kbefore_ascending = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "key",
    2: "before",
    3: "before_ascending",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'storage_onestore_v3.IndexPosition'
if _extension_runtime:
  pass

__all__ = ['PropertyValue','PropertyValue_ReferenceValuePathElement','PropertyValue_PointValue','PropertyValue_UserValue','PropertyValue_ReferenceValue','Property','Path','Path_Element','Reference','User','EntityProto','EntityMetadata','CompositeProperty','Index','Index_Property','CompositeIndex','SearchIndexEntry','IndexPostfix_IndexValue','IndexPostfix','IndexPosition']
