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
import sys
try:
  __import__('google.net.rpc.python.rpc_internals_lite')
  __import__('google.net.rpc.python.pywraprpc_lite')
  rpc_internals = sys.modules.get('google.net.rpc.python.rpc_internals_lite')
  pywraprpc = sys.modules.get('google.net.rpc.python.pywraprpc_lite')
  _client_stub_base_class = rpc_internals.StubbyRPCBaseStub
except ImportError:
  _client_stub_base_class = object
try:
  __import__('google.net.rpc.python.rpcserver')
  rpcserver = sys.modules.get('google.net.rpc.python.rpcserver')
  _server_stub_base_class = rpcserver.BaseRpcServer
except ImportError:
  _server_stub_base_class = object

__pychecker__ = """maxreturns=0 maxbranches=0 no-callinit
                   unusednames=printElemNumber,debug_strs no-special"""

if hasattr(ProtocolBuffer, 'ExtendableProtocolMessage'):
  _extension_runtime = True
  _ExtendableProtocolMessage = ProtocolBuffer.ExtendableProtocolMessage
else:
  _extension_runtime = False
  _ExtendableProtocolMessage = ProtocolBuffer.ProtocolMessage

class AppIdentityServiceError(ProtocolBuffer.ProtocolMessage):


  SUCCESS      =    0
  UNKNOWN_SCOPE =    9
  BLOB_TOO_LARGE = 1000
  DEADLINE_EXCEEDED = 1001
  NOT_A_VALID_APP = 1002
  UNKNOWN_ERROR = 1003
  GAIAMINT_NOT_INITIAILIZED = 1004
  NOT_ALLOWED  = 1005
  NOT_IMPLEMENTED = 1006

  _ErrorCode_NAMES = {
    0: "SUCCESS",
    9: "UNKNOWN_SCOPE",
    1000: "BLOB_TOO_LARGE",
    1001: "DEADLINE_EXCEEDED",
    1002: "NOT_A_VALID_APP",
    1003: "UNKNOWN_ERROR",
    1004: "GAIAMINT_NOT_INITIAILIZED",
    1005: "NOT_ALLOWED",
    1006: "NOT_IMPLEMENTED",
  }

  def ErrorCode_Name(cls, x): return cls._ErrorCode_NAMES.get(x, "")
  ErrorCode_Name = classmethod(ErrorCode_Name)


  def __init__(self, contents=None):
    pass
    if contents is not None: self.MergeFromString(contents)


  def MergeFrom(self, x):
    assert x is not self

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.AppIdentityServiceError', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.AppIdentityServiceError')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.AppIdentityServiceError')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.AppIdentityServiceError', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.AppIdentityServiceError', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.AppIdentityServiceError', s)


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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.AppIdentityServiceError'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WjZhcHBob3N0aW5nL2FwaS9hcHBfaWRlbnRpdHkvYXBwX2lkZW50aXR5X3NlcnZpY2UucHJvdG8KImFwcGhvc3RpbmcuQXBwSWRlbnRpdHlTZXJ2aWNlRXJyb3JzeglFcnJvckNvZGWLAZIBB1NVQ0NFU1OYAQCMAYsBkgENVU5LTk9XTl9TQ09QRZgBCYwBiwGSAQ5CTE9CX1RPT19MQVJHRZgB6AeMAYsBkgERREVBRExJTkVfRVhDRUVERUSYAekHjAGLAZIBD05PVF9BX1ZBTElEX0FQUJgB6geMAYsBkgENVU5LTk9XTl9FUlJPUpgB6weMAYsBkgEZR0FJQU1JTlRfTk9UX0lOSVRJQUlMSVpFRJgB7AeMAYsBkgELTk9UX0FMTE9XRUSYAe0HjAGLAZIBD05PVF9JTVBMRU1FTlRFRJgB7geMAXS6AekMCjZhcHBob3N0aW5nL2FwaS9hcHBfaWRlbnRpdHkvYXBwX2lkZW50aXR5X3NlcnZpY2UucHJvdG8SCmFwcGhvc3Rpbmci5gEKF0FwcElkZW50aXR5U2VydmljZUVycm9yIsoBCglFcnJvckNvZGUSCwoHU1VDQ0VTUxAAEhEKDVVOS05PV05fU0NPUEUQCRITCg5CTE9CX1RPT19MQVJHRRDoBxIWChFERUFETElORV9FWENFRURFRBDpBxIUCg9OT1RfQV9WQUxJRF9BUFAQ6gcSEgoNVU5LTk9XTl9FUlJPUhDrBxIeChlHQUlBTUlOVF9OT1RfSU5JVElBSUxJWkVEEOwHEhAKC05PVF9BTExPV0VEEO0HEhQKD05PVF9JTVBMRU1FTlRFRBDuByIqChFTaWduRm9yQXBwUmVxdWVzdBIVCg1ieXRlc190b19zaWduGAEgASgMIj8KElNpZ25Gb3JBcHBSZXNwb25zZRIQCghrZXlfbmFtZRgBIAEoCRIXCg9zaWduYXR1cmVfYnl0ZXMYAiABKAwiIwohR2V0UHVibGljQ2VydGlmaWNhdGVGb3JBcHBSZXF1ZXN0IkMKEVB1YmxpY0NlcnRpZmljYXRlEhAKCGtleV9uYW1lGAEgASgJEhwKFHg1MDlfY2VydGlmaWNhdGVfcGVtGAIgASgJIo0BCiJHZXRQdWJsaWNDZXJ0aWZpY2F0ZUZvckFwcFJlc3BvbnNlEj4KF3B1YmxpY19jZXJ0aWZpY2F0ZV9saXN0GAEgAygLMh0uYXBwaG9zdGluZy5QdWJsaWNDZXJ0aWZpY2F0ZRInCh9tYXhfY2xpZW50X2NhY2hlX3RpbWVfaW5fc2Vjb25kGAIgASgDIh4KHEdldFNlcnZpY2VBY2NvdW50TmFtZVJlcXVlc3QiPQodR2V0U2VydmljZUFjY291bnROYW1lUmVzcG9uc2USHAoUc2VydmljZV9hY2NvdW50X25hbWUYASABKAkiYAoVR2V0QWNjZXNzVG9rZW5SZXF1ZXN0Eg0KBXNjb3BlGAEgAygJEhoKEnNlcnZpY2VfYWNjb3VudF9pZBgCIAEoAxIcChRzZXJ2aWNlX2FjY291bnRfbmFtZRgDIAEoCSJHChZHZXRBY2Nlc3NUb2tlblJlc3BvbnNlEhQKDGFjY2Vzc190b2tlbhgBIAEoCRIXCg9leHBpcmF0aW9uX3RpbWUYAiABKAMiIAoeR2V0RGVmYXVsdEdjc0J1Y2tldE5hbWVSZXF1ZXN0IkIKH0dldERlZmF1bHRHY3NCdWNrZXROYW1lUmVzcG9uc2USHwoXZGVmYXVsdF9nY3NfYnVja2V0X25hbWUYASABKAkyoAQKDlNpZ25pbmdTZXJ2aWNlEk0KClNpZ25Gb3JBcHASHS5hcHBob3N0aW5nLlNpZ25Gb3JBcHBSZXF1ZXN0Gh4uYXBwaG9zdGluZy5TaWduRm9yQXBwUmVzcG9uc2UiABJ+ChtHZXRQdWJsaWNDZXJ0aWZpY2F0ZXNGb3JBcHASLS5hcHBob3N0aW5nLkdldFB1YmxpY0NlcnRpZmljYXRlRm9yQXBwUmVxdWVzdBouLmFwcGhvc3RpbmcuR2V0UHVibGljQ2VydGlmaWNhdGVGb3JBcHBSZXNwb25zZSIAEm4KFUdldFNlcnZpY2VBY2NvdW50TmFtZRIoLmFwcGhvc3RpbmcuR2V0U2VydmljZUFjY291bnROYW1lUmVxdWVzdBopLmFwcGhvc3RpbmcuR2V0U2VydmljZUFjY291bnROYW1lUmVzcG9uc2UiABJZCg5HZXRBY2Nlc3NUb2tlbhIhLmFwcGhvc3RpbmcuR2V0QWNjZXNzVG9rZW5SZXF1ZXN0GiIuYXBwaG9zdGluZy5HZXRBY2Nlc3NUb2tlblJlc3BvbnNlIgASdAoXR2V0RGVmYXVsdEdjc0J1Y2tldE5hbWUSKi5hcHBob3N0aW5nLkdldERlZmF1bHRHY3NCdWNrZXROYW1lUmVxdWVzdBorLmFwcGhvc3RpbmcuR2V0RGVmYXVsdEdjc0J1Y2tldE5hbWVSZXNwb25zZSIAQkAKJGNvbS5nb29nbGUuYXBwZW5naW5lLmFwaS5hcHBpZGVudGl0eSABKAJCFEFwcElkZW50aXR5U2VydmljZVBi"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class SignForAppRequest(ProtocolBuffer.ProtocolMessage):
  has_bytes_to_sign_ = 0
  bytes_to_sign_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def bytes_to_sign(self): return self.bytes_to_sign_

  def set_bytes_to_sign(self, x):
    self.has_bytes_to_sign_ = 1
    self.bytes_to_sign_ = x

  def clear_bytes_to_sign(self):
    if self.has_bytes_to_sign_:
      self.has_bytes_to_sign_ = 0
      self.bytes_to_sign_ = ""

  def has_bytes_to_sign(self): return self.has_bytes_to_sign_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_bytes_to_sign()): self.set_bytes_to_sign(x.bytes_to_sign())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.SignForAppRequest', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.SignForAppRequest')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.SignForAppRequest')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.SignForAppRequest', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.SignForAppRequest', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.SignForAppRequest', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_bytes_to_sign_ != x.has_bytes_to_sign_: return 0
    if self.has_bytes_to_sign_ and self.bytes_to_sign_ != x.bytes_to_sign_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_bytes_to_sign_): n += 1 + self.lengthString(len(self.bytes_to_sign_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_bytes_to_sign_): n += 1 + self.lengthString(len(self.bytes_to_sign_))
    return n

  def Clear(self):
    self.clear_bytes_to_sign()

  def OutputUnchecked(self, out):
    if (self.has_bytes_to_sign_):
      out.putVarInt32(10)
      out.putPrefixedString(self.bytes_to_sign_)

  def OutputPartial(self, out):
    if (self.has_bytes_to_sign_):
      out.putVarInt32(10)
      out.putPrefixedString(self.bytes_to_sign_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_bytes_to_sign(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_bytes_to_sign_: res+=prefix+("bytes_to_sign: %s\n" % self.DebugFormatString(self.bytes_to_sign_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kbytes_to_sign = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "bytes_to_sign",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SignForAppRequest'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WjZhcHBob3N0aW5nL2FwaS9hcHBfaWRlbnRpdHkvYXBwX2lkZW50aXR5X3NlcnZpY2UucHJvdG8KHGFwcGhvc3RpbmcuU2lnbkZvckFwcFJlcXVlc3QTGg1ieXRlc190b19zaWduIAEoAjAJOAEUwgEiYXBwaG9zdGluZy5BcHBJZGVudGl0eVNlcnZpY2VFcnJvcg=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class SignForAppResponse(ProtocolBuffer.ProtocolMessage):
  has_key_name_ = 0
  key_name_ = ""
  has_signature_bytes_ = 0
  signature_bytes_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def key_name(self): return self.key_name_

  def set_key_name(self, x):
    self.has_key_name_ = 1
    self.key_name_ = x

  def clear_key_name(self):
    if self.has_key_name_:
      self.has_key_name_ = 0
      self.key_name_ = ""

  def has_key_name(self): return self.has_key_name_

  def signature_bytes(self): return self.signature_bytes_

  def set_signature_bytes(self, x):
    self.has_signature_bytes_ = 1
    self.signature_bytes_ = x

  def clear_signature_bytes(self):
    if self.has_signature_bytes_:
      self.has_signature_bytes_ = 0
      self.signature_bytes_ = ""

  def has_signature_bytes(self): return self.has_signature_bytes_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_key_name()): self.set_key_name(x.key_name())
    if (x.has_signature_bytes()): self.set_signature_bytes(x.signature_bytes())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.SignForAppResponse', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.SignForAppResponse')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.SignForAppResponse')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.SignForAppResponse', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.SignForAppResponse', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.SignForAppResponse', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_key_name_ != x.has_key_name_: return 0
    if self.has_key_name_ and self.key_name_ != x.key_name_: return 0
    if self.has_signature_bytes_ != x.has_signature_bytes_: return 0
    if self.has_signature_bytes_ and self.signature_bytes_ != x.signature_bytes_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_key_name_): n += 1 + self.lengthString(len(self.key_name_))
    if (self.has_signature_bytes_): n += 1 + self.lengthString(len(self.signature_bytes_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_key_name_): n += 1 + self.lengthString(len(self.key_name_))
    if (self.has_signature_bytes_): n += 1 + self.lengthString(len(self.signature_bytes_))
    return n

  def Clear(self):
    self.clear_key_name()
    self.clear_signature_bytes()

  def OutputUnchecked(self, out):
    if (self.has_key_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.key_name_)
    if (self.has_signature_bytes_):
      out.putVarInt32(18)
      out.putPrefixedString(self.signature_bytes_)

  def OutputPartial(self, out):
    if (self.has_key_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.key_name_)
    if (self.has_signature_bytes_):
      out.putVarInt32(18)
      out.putPrefixedString(self.signature_bytes_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_key_name(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_signature_bytes(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_name_: res+=prefix+("key_name: %s\n" % self.DebugFormatString(self.key_name_))
    if self.has_signature_bytes_: res+=prefix+("signature_bytes: %s\n" % self.DebugFormatString(self.signature_bytes_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kkey_name = 1
  ksignature_bytes = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "key_name",
    2: "signature_bytes",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SignForAppResponse'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WjZhcHBob3N0aW5nL2FwaS9hcHBfaWRlbnRpdHkvYXBwX2lkZW50aXR5X3NlcnZpY2UucHJvdG8KHWFwcGhvc3RpbmcuU2lnbkZvckFwcFJlc3BvbnNlExoIa2V5X25hbWUgASgCMAk4ARQTGg9zaWduYXR1cmVfYnl0ZXMgAigCMAk4ARTCASJhcHBob3N0aW5nLkFwcElkZW50aXR5U2VydmljZUVycm9y"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class GetPublicCertificateForAppRequest(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    pass
    if contents is not None: self.MergeFromString(contents)


  def MergeFrom(self, x):
    assert x is not self

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.GetPublicCertificateForAppRequest', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.GetPublicCertificateForAppRequest')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.GetPublicCertificateForAppRequest')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.GetPublicCertificateForAppRequest', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.GetPublicCertificateForAppRequest', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.GetPublicCertificateForAppRequest', s)


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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetPublicCertificateForAppRequest'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WjZhcHBob3N0aW5nL2FwaS9hcHBfaWRlbnRpdHkvYXBwX2lkZW50aXR5X3NlcnZpY2UucHJvdG8KLGFwcGhvc3RpbmcuR2V0UHVibGljQ2VydGlmaWNhdGVGb3JBcHBSZXF1ZXN0wgEiYXBwaG9zdGluZy5BcHBJZGVudGl0eVNlcnZpY2VFcnJvcg=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class PublicCertificate(ProtocolBuffer.ProtocolMessage):
  has_key_name_ = 0
  key_name_ = ""
  has_x509_certificate_pem_ = 0
  x509_certificate_pem_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def key_name(self): return self.key_name_

  def set_key_name(self, x):
    self.has_key_name_ = 1
    self.key_name_ = x

  def clear_key_name(self):
    if self.has_key_name_:
      self.has_key_name_ = 0
      self.key_name_ = ""

  def has_key_name(self): return self.has_key_name_

  def x509_certificate_pem(self): return self.x509_certificate_pem_

  def set_x509_certificate_pem(self, x):
    self.has_x509_certificate_pem_ = 1
    self.x509_certificate_pem_ = x

  def clear_x509_certificate_pem(self):
    if self.has_x509_certificate_pem_:
      self.has_x509_certificate_pem_ = 0
      self.x509_certificate_pem_ = ""

  def has_x509_certificate_pem(self): return self.has_x509_certificate_pem_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_key_name()): self.set_key_name(x.key_name())
    if (x.has_x509_certificate_pem()): self.set_x509_certificate_pem(x.x509_certificate_pem())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.PublicCertificate', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.PublicCertificate')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.PublicCertificate')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.PublicCertificate', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.PublicCertificate', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.PublicCertificate', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_key_name_ != x.has_key_name_: return 0
    if self.has_key_name_ and self.key_name_ != x.key_name_: return 0
    if self.has_x509_certificate_pem_ != x.has_x509_certificate_pem_: return 0
    if self.has_x509_certificate_pem_ and self.x509_certificate_pem_ != x.x509_certificate_pem_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_key_name_): n += 1 + self.lengthString(len(self.key_name_))
    if (self.has_x509_certificate_pem_): n += 1 + self.lengthString(len(self.x509_certificate_pem_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_key_name_): n += 1 + self.lengthString(len(self.key_name_))
    if (self.has_x509_certificate_pem_): n += 1 + self.lengthString(len(self.x509_certificate_pem_))
    return n

  def Clear(self):
    self.clear_key_name()
    self.clear_x509_certificate_pem()

  def OutputUnchecked(self, out):
    if (self.has_key_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.key_name_)
    if (self.has_x509_certificate_pem_):
      out.putVarInt32(18)
      out.putPrefixedString(self.x509_certificate_pem_)

  def OutputPartial(self, out):
    if (self.has_key_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.key_name_)
    if (self.has_x509_certificate_pem_):
      out.putVarInt32(18)
      out.putPrefixedString(self.x509_certificate_pem_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_key_name(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_x509_certificate_pem(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_name_: res+=prefix+("key_name: %s\n" % self.DebugFormatString(self.key_name_))
    if self.has_x509_certificate_pem_: res+=prefix+("x509_certificate_pem: %s\n" % self.DebugFormatString(self.x509_certificate_pem_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kkey_name = 1
  kx509_certificate_pem = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "key_name",
    2: "x509_certificate_pem",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.PublicCertificate'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WjZhcHBob3N0aW5nL2FwaS9hcHBfaWRlbnRpdHkvYXBwX2lkZW50aXR5X3NlcnZpY2UucHJvdG8KHGFwcGhvc3RpbmcuUHVibGljQ2VydGlmaWNhdGUTGghrZXlfbmFtZSABKAIwCTgBFBMaFHg1MDlfY2VydGlmaWNhdGVfcGVtIAIoAjAJOAEUwgEiYXBwaG9zdGluZy5BcHBJZGVudGl0eVNlcnZpY2VFcnJvcg=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class GetPublicCertificateForAppResponse(ProtocolBuffer.ProtocolMessage):
  has_max_client_cache_time_in_second_ = 0
  max_client_cache_time_in_second_ = 0

  def __init__(self, contents=None):
    self.public_certificate_list_ = []
    if contents is not None: self.MergeFromString(contents)

  def public_certificate_list_size(self): return len(self.public_certificate_list_)
  def public_certificate_list_list(self): return self.public_certificate_list_

  def public_certificate_list(self, i):
    return self.public_certificate_list_[i]

  def mutable_public_certificate_list(self, i):
    return self.public_certificate_list_[i]

  def add_public_certificate_list(self):
    x = PublicCertificate()
    self.public_certificate_list_.append(x)
    return x

  def clear_public_certificate_list(self):
    self.public_certificate_list_ = []
  def max_client_cache_time_in_second(self): return self.max_client_cache_time_in_second_

  def set_max_client_cache_time_in_second(self, x):
    self.has_max_client_cache_time_in_second_ = 1
    self.max_client_cache_time_in_second_ = x

  def clear_max_client_cache_time_in_second(self):
    if self.has_max_client_cache_time_in_second_:
      self.has_max_client_cache_time_in_second_ = 0
      self.max_client_cache_time_in_second_ = 0

  def has_max_client_cache_time_in_second(self): return self.has_max_client_cache_time_in_second_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.public_certificate_list_size()): self.add_public_certificate_list().CopyFrom(x.public_certificate_list(i))
    if (x.has_max_client_cache_time_in_second()): self.set_max_client_cache_time_in_second(x.max_client_cache_time_in_second())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.GetPublicCertificateForAppResponse', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.GetPublicCertificateForAppResponse')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.GetPublicCertificateForAppResponse')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.GetPublicCertificateForAppResponse', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.GetPublicCertificateForAppResponse', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.GetPublicCertificateForAppResponse', s)


  def Equals(self, x):
    if x is self: return 1
    if len(self.public_certificate_list_) != len(x.public_certificate_list_): return 0
    for e1, e2 in zip(self.public_certificate_list_, x.public_certificate_list_):
      if e1 != e2: return 0
    if self.has_max_client_cache_time_in_second_ != x.has_max_client_cache_time_in_second_: return 0
    if self.has_max_client_cache_time_in_second_ and self.max_client_cache_time_in_second_ != x.max_client_cache_time_in_second_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.public_certificate_list_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.public_certificate_list_)
    for i in xrange(len(self.public_certificate_list_)): n += self.lengthString(self.public_certificate_list_[i].ByteSize())
    if (self.has_max_client_cache_time_in_second_): n += 1 + self.lengthVarInt64(self.max_client_cache_time_in_second_)
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.public_certificate_list_)
    for i in xrange(len(self.public_certificate_list_)): n += self.lengthString(self.public_certificate_list_[i].ByteSizePartial())
    if (self.has_max_client_cache_time_in_second_): n += 1 + self.lengthVarInt64(self.max_client_cache_time_in_second_)
    return n

  def Clear(self):
    self.clear_public_certificate_list()
    self.clear_max_client_cache_time_in_second()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.public_certificate_list_)):
      out.putVarInt32(10)
      out.putVarInt32(self.public_certificate_list_[i].ByteSize())
      self.public_certificate_list_[i].OutputUnchecked(out)
    if (self.has_max_client_cache_time_in_second_):
      out.putVarInt32(16)
      out.putVarInt64(self.max_client_cache_time_in_second_)

  def OutputPartial(self, out):
    for i in xrange(len(self.public_certificate_list_)):
      out.putVarInt32(10)
      out.putVarInt32(self.public_certificate_list_[i].ByteSizePartial())
      self.public_certificate_list_[i].OutputPartial(out)
    if (self.has_max_client_cache_time_in_second_):
      out.putVarInt32(16)
      out.putVarInt64(self.max_client_cache_time_in_second_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_public_certificate_list().TryMerge(tmp)
        continue
      if tt == 16:
        self.set_max_client_cache_time_in_second(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.public_certificate_list_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("public_certificate_list%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_max_client_cache_time_in_second_: res+=prefix+("max_client_cache_time_in_second: %s\n" % self.DebugFormatInt64(self.max_client_cache_time_in_second_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kpublic_certificate_list = 1
  kmax_client_cache_time_in_second = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "public_certificate_list",
    2: "max_client_cache_time_in_second",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetPublicCertificateForAppResponse'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WjZhcHBob3N0aW5nL2FwaS9hcHBfaWRlbnRpdHkvYXBwX2lkZW50aXR5X3NlcnZpY2UucHJvdG8KLWFwcGhvc3RpbmcuR2V0UHVibGljQ2VydGlmaWNhdGVGb3JBcHBSZXNwb25zZRMaF3B1YmxpY19jZXJ0aWZpY2F0ZV9saXN0IAEoAjALOANKHGFwcGhvc3RpbmcuUHVibGljQ2VydGlmaWNhdGWjAaoBBWN0eXBlsgEGcHJvdG8ypAEUExofbWF4X2NsaWVudF9jYWNoZV90aW1lX2luX3NlY29uZCACKAAwAzgBFMIBImFwcGhvc3RpbmcuQXBwSWRlbnRpdHlTZXJ2aWNlRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class GetServiceAccountNameRequest(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    pass
    if contents is not None: self.MergeFromString(contents)


  def MergeFrom(self, x):
    assert x is not self

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.GetServiceAccountNameRequest', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.GetServiceAccountNameRequest')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.GetServiceAccountNameRequest')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.GetServiceAccountNameRequest', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.GetServiceAccountNameRequest', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.GetServiceAccountNameRequest', s)


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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetServiceAccountNameRequest'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WjZhcHBob3N0aW5nL2FwaS9hcHBfaWRlbnRpdHkvYXBwX2lkZW50aXR5X3NlcnZpY2UucHJvdG8KJ2FwcGhvc3RpbmcuR2V0U2VydmljZUFjY291bnROYW1lUmVxdWVzdMIBImFwcGhvc3RpbmcuQXBwSWRlbnRpdHlTZXJ2aWNlRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class GetServiceAccountNameResponse(ProtocolBuffer.ProtocolMessage):
  has_service_account_name_ = 0
  service_account_name_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def service_account_name(self): return self.service_account_name_

  def set_service_account_name(self, x):
    self.has_service_account_name_ = 1
    self.service_account_name_ = x

  def clear_service_account_name(self):
    if self.has_service_account_name_:
      self.has_service_account_name_ = 0
      self.service_account_name_ = ""

  def has_service_account_name(self): return self.has_service_account_name_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_service_account_name()): self.set_service_account_name(x.service_account_name())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.GetServiceAccountNameResponse', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.GetServiceAccountNameResponse')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.GetServiceAccountNameResponse')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.GetServiceAccountNameResponse', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.GetServiceAccountNameResponse', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.GetServiceAccountNameResponse', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_service_account_name_ != x.has_service_account_name_: return 0
    if self.has_service_account_name_ and self.service_account_name_ != x.service_account_name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_service_account_name_): n += 1 + self.lengthString(len(self.service_account_name_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_service_account_name_): n += 1 + self.lengthString(len(self.service_account_name_))
    return n

  def Clear(self):
    self.clear_service_account_name()

  def OutputUnchecked(self, out):
    if (self.has_service_account_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.service_account_name_)

  def OutputPartial(self, out):
    if (self.has_service_account_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.service_account_name_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_service_account_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_service_account_name_: res+=prefix+("service_account_name: %s\n" % self.DebugFormatString(self.service_account_name_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kservice_account_name = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "service_account_name",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetServiceAccountNameResponse'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WjZhcHBob3N0aW5nL2FwaS9hcHBfaWRlbnRpdHkvYXBwX2lkZW50aXR5X3NlcnZpY2UucHJvdG8KKGFwcGhvc3RpbmcuR2V0U2VydmljZUFjY291bnROYW1lUmVzcG9uc2UTGhRzZXJ2aWNlX2FjY291bnRfbmFtZSABKAIwCTgBFMIBImFwcGhvc3RpbmcuQXBwSWRlbnRpdHlTZXJ2aWNlRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class GetAccessTokenRequest(ProtocolBuffer.ProtocolMessage):
  has_service_account_id_ = 0
  service_account_id_ = 0
  has_service_account_name_ = 0
  service_account_name_ = ""

  def __init__(self, contents=None):
    self.scope_ = []
    if contents is not None: self.MergeFromString(contents)

  def scope_size(self): return len(self.scope_)
  def scope_list(self): return self.scope_

  def scope(self, i):
    return self.scope_[i]

  def set_scope(self, i, x):
    self.scope_[i] = x

  def add_scope(self, x):
    self.scope_.append(x)

  def clear_scope(self):
    self.scope_ = []

  def service_account_id(self): return self.service_account_id_

  def set_service_account_id(self, x):
    self.has_service_account_id_ = 1
    self.service_account_id_ = x

  def clear_service_account_id(self):
    if self.has_service_account_id_:
      self.has_service_account_id_ = 0
      self.service_account_id_ = 0

  def has_service_account_id(self): return self.has_service_account_id_

  def service_account_name(self): return self.service_account_name_

  def set_service_account_name(self, x):
    self.has_service_account_name_ = 1
    self.service_account_name_ = x

  def clear_service_account_name(self):
    if self.has_service_account_name_:
      self.has_service_account_name_ = 0
      self.service_account_name_ = ""

  def has_service_account_name(self): return self.has_service_account_name_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.scope_size()): self.add_scope(x.scope(i))
    if (x.has_service_account_id()): self.set_service_account_id(x.service_account_id())
    if (x.has_service_account_name()): self.set_service_account_name(x.service_account_name())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.GetAccessTokenRequest', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.GetAccessTokenRequest')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.GetAccessTokenRequest')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.GetAccessTokenRequest', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.GetAccessTokenRequest', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.GetAccessTokenRequest', s)


  def Equals(self, x):
    if x is self: return 1
    if len(self.scope_) != len(x.scope_): return 0
    for e1, e2 in zip(self.scope_, x.scope_):
      if e1 != e2: return 0
    if self.has_service_account_id_ != x.has_service_account_id_: return 0
    if self.has_service_account_id_ and self.service_account_id_ != x.service_account_id_: return 0
    if self.has_service_account_name_ != x.has_service_account_name_: return 0
    if self.has_service_account_name_ and self.service_account_name_ != x.service_account_name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.scope_)
    for i in xrange(len(self.scope_)): n += self.lengthString(len(self.scope_[i]))
    if (self.has_service_account_id_): n += 1 + self.lengthVarInt64(self.service_account_id_)
    if (self.has_service_account_name_): n += 1 + self.lengthString(len(self.service_account_name_))
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.scope_)
    for i in xrange(len(self.scope_)): n += self.lengthString(len(self.scope_[i]))
    if (self.has_service_account_id_): n += 1 + self.lengthVarInt64(self.service_account_id_)
    if (self.has_service_account_name_): n += 1 + self.lengthString(len(self.service_account_name_))
    return n

  def Clear(self):
    self.clear_scope()
    self.clear_service_account_id()
    self.clear_service_account_name()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.scope_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.scope_[i])
    if (self.has_service_account_id_):
      out.putVarInt32(16)
      out.putVarInt64(self.service_account_id_)
    if (self.has_service_account_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.service_account_name_)

  def OutputPartial(self, out):
    for i in xrange(len(self.scope_)):
      out.putVarInt32(10)
      out.putPrefixedString(self.scope_[i])
    if (self.has_service_account_id_):
      out.putVarInt32(16)
      out.putVarInt64(self.service_account_id_)
    if (self.has_service_account_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.service_account_name_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.add_scope(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_service_account_id(d.getVarInt64())
        continue
      if tt == 26:
        self.set_service_account_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.scope_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("scope%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_service_account_id_: res+=prefix+("service_account_id: %s\n" % self.DebugFormatInt64(self.service_account_id_))
    if self.has_service_account_name_: res+=prefix+("service_account_name: %s\n" % self.DebugFormatString(self.service_account_name_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kscope = 1
  kservice_account_id = 2
  kservice_account_name = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "scope",
    2: "service_account_id",
    3: "service_account_name",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetAccessTokenRequest'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WjZhcHBob3N0aW5nL2FwaS9hcHBfaWRlbnRpdHkvYXBwX2lkZW50aXR5X3NlcnZpY2UucHJvdG8KIGFwcGhvc3RpbmcuR2V0QWNjZXNzVG9rZW5SZXF1ZXN0ExoFc2NvcGUgASgCMAk4AxQTGhJzZXJ2aWNlX2FjY291bnRfaWQgAigAMAM4ARQTGhRzZXJ2aWNlX2FjY291bnRfbmFtZSADKAIwCTgBFMIBImFwcGhvc3RpbmcuQXBwSWRlbnRpdHlTZXJ2aWNlRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class GetAccessTokenResponse(ProtocolBuffer.ProtocolMessage):
  has_access_token_ = 0
  access_token_ = ""
  has_expiration_time_ = 0
  expiration_time_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def access_token(self): return self.access_token_

  def set_access_token(self, x):
    self.has_access_token_ = 1
    self.access_token_ = x

  def clear_access_token(self):
    if self.has_access_token_:
      self.has_access_token_ = 0
      self.access_token_ = ""

  def has_access_token(self): return self.has_access_token_

  def expiration_time(self): return self.expiration_time_

  def set_expiration_time(self, x):
    self.has_expiration_time_ = 1
    self.expiration_time_ = x

  def clear_expiration_time(self):
    if self.has_expiration_time_:
      self.has_expiration_time_ = 0
      self.expiration_time_ = 0

  def has_expiration_time(self): return self.has_expiration_time_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_access_token()): self.set_access_token(x.access_token())
    if (x.has_expiration_time()): self.set_expiration_time(x.expiration_time())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.GetAccessTokenResponse', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.GetAccessTokenResponse')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.GetAccessTokenResponse')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.GetAccessTokenResponse', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.GetAccessTokenResponse', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.GetAccessTokenResponse', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_access_token_ != x.has_access_token_: return 0
    if self.has_access_token_ and self.access_token_ != x.access_token_: return 0
    if self.has_expiration_time_ != x.has_expiration_time_: return 0
    if self.has_expiration_time_ and self.expiration_time_ != x.expiration_time_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_access_token_): n += 1 + self.lengthString(len(self.access_token_))
    if (self.has_expiration_time_): n += 1 + self.lengthVarInt64(self.expiration_time_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_access_token_): n += 1 + self.lengthString(len(self.access_token_))
    if (self.has_expiration_time_): n += 1 + self.lengthVarInt64(self.expiration_time_)
    return n

  def Clear(self):
    self.clear_access_token()
    self.clear_expiration_time()

  def OutputUnchecked(self, out):
    if (self.has_access_token_):
      out.putVarInt32(10)
      out.putPrefixedString(self.access_token_)
    if (self.has_expiration_time_):
      out.putVarInt32(16)
      out.putVarInt64(self.expiration_time_)

  def OutputPartial(self, out):
    if (self.has_access_token_):
      out.putVarInt32(10)
      out.putPrefixedString(self.access_token_)
    if (self.has_expiration_time_):
      out.putVarInt32(16)
      out.putVarInt64(self.expiration_time_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_access_token(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_expiration_time(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_access_token_: res+=prefix+("access_token: %s\n" % self.DebugFormatString(self.access_token_))
    if self.has_expiration_time_: res+=prefix+("expiration_time: %s\n" % self.DebugFormatInt64(self.expiration_time_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kaccess_token = 1
  kexpiration_time = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "access_token",
    2: "expiration_time",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetAccessTokenResponse'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WjZhcHBob3N0aW5nL2FwaS9hcHBfaWRlbnRpdHkvYXBwX2lkZW50aXR5X3NlcnZpY2UucHJvdG8KIWFwcGhvc3RpbmcuR2V0QWNjZXNzVG9rZW5SZXNwb25zZRMaDGFjY2Vzc190b2tlbiABKAIwCTgBFBMaD2V4cGlyYXRpb25fdGltZSACKAAwAzgBFMIBImFwcGhvc3RpbmcuQXBwSWRlbnRpdHlTZXJ2aWNlRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class GetDefaultGcsBucketNameRequest(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    pass
    if contents is not None: self.MergeFromString(contents)


  def MergeFrom(self, x):
    assert x is not self

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.GetDefaultGcsBucketNameRequest', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.GetDefaultGcsBucketNameRequest')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.GetDefaultGcsBucketNameRequest')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.GetDefaultGcsBucketNameRequest', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.GetDefaultGcsBucketNameRequest', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.GetDefaultGcsBucketNameRequest', s)


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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetDefaultGcsBucketNameRequest'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WjZhcHBob3N0aW5nL2FwaS9hcHBfaWRlbnRpdHkvYXBwX2lkZW50aXR5X3NlcnZpY2UucHJvdG8KKWFwcGhvc3RpbmcuR2V0RGVmYXVsdEdjc0J1Y2tldE5hbWVSZXF1ZXN0wgEiYXBwaG9zdGluZy5BcHBJZGVudGl0eVNlcnZpY2VFcnJvcg=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class GetDefaultGcsBucketNameResponse(ProtocolBuffer.ProtocolMessage):
  has_default_gcs_bucket_name_ = 0
  default_gcs_bucket_name_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def default_gcs_bucket_name(self): return self.default_gcs_bucket_name_

  def set_default_gcs_bucket_name(self, x):
    self.has_default_gcs_bucket_name_ = 1
    self.default_gcs_bucket_name_ = x

  def clear_default_gcs_bucket_name(self):
    if self.has_default_gcs_bucket_name_:
      self.has_default_gcs_bucket_name_ = 0
      self.default_gcs_bucket_name_ = ""

  def has_default_gcs_bucket_name(self): return self.has_default_gcs_bucket_name_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_default_gcs_bucket_name()): self.set_default_gcs_bucket_name(x.default_gcs_bucket_name())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.GetDefaultGcsBucketNameResponse', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.GetDefaultGcsBucketNameResponse')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.GetDefaultGcsBucketNameResponse')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.GetDefaultGcsBucketNameResponse', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.GetDefaultGcsBucketNameResponse', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.GetDefaultGcsBucketNameResponse', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_default_gcs_bucket_name_ != x.has_default_gcs_bucket_name_: return 0
    if self.has_default_gcs_bucket_name_ and self.default_gcs_bucket_name_ != x.default_gcs_bucket_name_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_default_gcs_bucket_name_): n += 1 + self.lengthString(len(self.default_gcs_bucket_name_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_default_gcs_bucket_name_): n += 1 + self.lengthString(len(self.default_gcs_bucket_name_))
    return n

  def Clear(self):
    self.clear_default_gcs_bucket_name()

  def OutputUnchecked(self, out):
    if (self.has_default_gcs_bucket_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.default_gcs_bucket_name_)

  def OutputPartial(self, out):
    if (self.has_default_gcs_bucket_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.default_gcs_bucket_name_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_default_gcs_bucket_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_default_gcs_bucket_name_: res+=prefix+("default_gcs_bucket_name: %s\n" % self.DebugFormatString(self.default_gcs_bucket_name_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kdefault_gcs_bucket_name = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "default_gcs_bucket_name",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetDefaultGcsBucketNameResponse'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WjZhcHBob3N0aW5nL2FwaS9hcHBfaWRlbnRpdHkvYXBwX2lkZW50aXR5X3NlcnZpY2UucHJvdG8KKmFwcGhvc3RpbmcuR2V0RGVmYXVsdEdjc0J1Y2tldE5hbWVSZXNwb25zZRMaF2RlZmF1bHRfZ2NzX2J1Y2tldF9uYW1lIAEoAjAJOAEUwgEiYXBwaG9zdGluZy5BcHBJZGVudGl0eVNlcnZpY2VFcnJvcg=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())



class _SigningService_ClientBaseStub(_client_stub_base_class):
  """Makes Stubby RPC calls to a SigningService server."""

  __slots__ = (
      '_protorpc_SignForApp', '_full_name_SignForApp',
      '_protorpc_GetPublicCertificatesForApp', '_full_name_GetPublicCertificatesForApp',
      '_protorpc_GetServiceAccountName', '_full_name_GetServiceAccountName',
      '_protorpc_GetAccessToken', '_full_name_GetAccessToken',
      '_protorpc_GetDefaultGcsBucketName', '_full_name_GetDefaultGcsBucketName',
  )

  def __init__(self, rpc_stub):
    self._stub = rpc_stub

    self._protorpc_SignForApp = pywraprpc.RPC()
    self._full_name_SignForApp = self._stub.GetFullMethodName(
        'SignForApp')

    self._protorpc_GetPublicCertificatesForApp = pywraprpc.RPC()
    self._full_name_GetPublicCertificatesForApp = self._stub.GetFullMethodName(
        'GetPublicCertificatesForApp')

    self._protorpc_GetServiceAccountName = pywraprpc.RPC()
    self._full_name_GetServiceAccountName = self._stub.GetFullMethodName(
        'GetServiceAccountName')

    self._protorpc_GetAccessToken = pywraprpc.RPC()
    self._full_name_GetAccessToken = self._stub.GetFullMethodName(
        'GetAccessToken')

    self._protorpc_GetDefaultGcsBucketName = pywraprpc.RPC()
    self._full_name_GetDefaultGcsBucketName = self._stub.GetFullMethodName(
        'GetDefaultGcsBucketName')

  def SignForApp(self, request, rpc=None, callback=None, response=None):
    """Make a SignForApp RPC call.

    Args:
      request: a SignForAppRequest instance.
      rpc: Optional RPC instance to use for the call.
      callback: Optional final callback. Will be called as
          callback(rpc, result) when the rpc completes. If None, the
          call is synchronous.
      response: Optional ProtocolMessage to be filled in with response.

    Returns:
      The SignForAppResponse if callback is None. Otherwise, returns None.
    """

    if response is None:
      response = SignForAppResponse
    return self._MakeCall(rpc,
                          self._full_name_SignForApp,
                          'SignForApp',
                          request,
                          response,
                          callback,
                          self._protorpc_SignForApp,
                          package_name='apphosting')

  def GetPublicCertificatesForApp(self, request, rpc=None, callback=None, response=None):
    """Make a GetPublicCertificatesForApp RPC call.

    Args:
      request: a GetPublicCertificateForAppRequest instance.
      rpc: Optional RPC instance to use for the call.
      callback: Optional final callback. Will be called as
          callback(rpc, result) when the rpc completes. If None, the
          call is synchronous.
      response: Optional ProtocolMessage to be filled in with response.

    Returns:
      The GetPublicCertificateForAppResponse if callback is None. Otherwise, returns None.
    """

    if response is None:
      response = GetPublicCertificateForAppResponse
    return self._MakeCall(rpc,
                          self._full_name_GetPublicCertificatesForApp,
                          'GetPublicCertificatesForApp',
                          request,
                          response,
                          callback,
                          self._protorpc_GetPublicCertificatesForApp,
                          package_name='apphosting')

  def GetServiceAccountName(self, request, rpc=None, callback=None, response=None):
    """Make a GetServiceAccountName RPC call.

    Args:
      request: a GetServiceAccountNameRequest instance.
      rpc: Optional RPC instance to use for the call.
      callback: Optional final callback. Will be called as
          callback(rpc, result) when the rpc completes. If None, the
          call is synchronous.
      response: Optional ProtocolMessage to be filled in with response.

    Returns:
      The GetServiceAccountNameResponse if callback is None. Otherwise, returns None.
    """

    if response is None:
      response = GetServiceAccountNameResponse
    return self._MakeCall(rpc,
                          self._full_name_GetServiceAccountName,
                          'GetServiceAccountName',
                          request,
                          response,
                          callback,
                          self._protorpc_GetServiceAccountName,
                          package_name='apphosting')

  def GetAccessToken(self, request, rpc=None, callback=None, response=None):
    """Make a GetAccessToken RPC call.

    Args:
      request: a GetAccessTokenRequest instance.
      rpc: Optional RPC instance to use for the call.
      callback: Optional final callback. Will be called as
          callback(rpc, result) when the rpc completes. If None, the
          call is synchronous.
      response: Optional ProtocolMessage to be filled in with response.

    Returns:
      The GetAccessTokenResponse if callback is None. Otherwise, returns None.
    """

    if response is None:
      response = GetAccessTokenResponse
    return self._MakeCall(rpc,
                          self._full_name_GetAccessToken,
                          'GetAccessToken',
                          request,
                          response,
                          callback,
                          self._protorpc_GetAccessToken,
                          package_name='apphosting')

  def GetDefaultGcsBucketName(self, request, rpc=None, callback=None, response=None):
    """Make a GetDefaultGcsBucketName RPC call.

    Args:
      request: a GetDefaultGcsBucketNameRequest instance.
      rpc: Optional RPC instance to use for the call.
      callback: Optional final callback. Will be called as
          callback(rpc, result) when the rpc completes. If None, the
          call is synchronous.
      response: Optional ProtocolMessage to be filled in with response.

    Returns:
      The GetDefaultGcsBucketNameResponse if callback is None. Otherwise, returns None.
    """

    if response is None:
      response = GetDefaultGcsBucketNameResponse
    return self._MakeCall(rpc,
                          self._full_name_GetDefaultGcsBucketName,
                          'GetDefaultGcsBucketName',
                          request,
                          response,
                          callback,
                          self._protorpc_GetDefaultGcsBucketName,
                          package_name='apphosting')


class _SigningService_ClientStub(_SigningService_ClientBaseStub):
  __slots__ = ('_params',)
  def __init__(self, rpc_stub_parameters, service_name):
    if service_name is None:
      service_name = 'SigningService'
    _SigningService_ClientBaseStub.__init__(self, pywraprpc.RPC_GenericStub(service_name, rpc_stub_parameters))
    self._params = rpc_stub_parameters


class _SigningService_RPC2ClientStub(_SigningService_ClientBaseStub):
  __slots__ = ()
  def __init__(self, server, channel, service_name):
    if service_name is None:
      service_name = 'SigningService'
    if channel is not None:
      if channel.version() == 1:
        raise RuntimeError('Expecting an RPC2 channel to create the stub')
      _SigningService_ClientBaseStub.__init__(self, pywraprpc.RPC_GenericStub(service_name, channel))
    elif server is not None:
      _SigningService_ClientBaseStub.__init__(self, pywraprpc.RPC_GenericStub(service_name, pywraprpc.NewClientChannel(server)))
    else:
      raise RuntimeError('Invalid argument combination to create a stub')


class SigningService(_server_stub_base_class):
  """Base class for SigningService Stubby servers."""

  @classmethod
  def _MethodSignatures(cls):
    """Returns a dict of {<method-name>: (<request-type>, <response-type>)}."""
    return {
      'SignForApp': (SignForAppRequest, SignForAppResponse),
      'GetPublicCertificatesForApp': (GetPublicCertificateForAppRequest, GetPublicCertificateForAppResponse),
      'GetServiceAccountName': (GetServiceAccountNameRequest, GetServiceAccountNameResponse),
      'GetAccessToken': (GetAccessTokenRequest, GetAccessTokenResponse),
      'GetDefaultGcsBucketName': (GetDefaultGcsBucketNameRequest, GetDefaultGcsBucketNameResponse),
      }

  @classmethod
  def _StreamMethodSignatures(cls):
    """Returns a dict of {<method-name>: (<request-type>, <stream-type>, <response-type>)}."""
    return {
      }

  def __init__(self, *args, **kwargs):
    """Creates a Stubby RPC server.

    The arguments to this constructor are the same as the arguments to
    BaseRpcServer.__init__ in rpcserver.py *MINUS* export_name. This
    constructor passes its own value for export_name to
    BaseRpcServer.__init__, so callers of this constructor should only
    pass to this constructor values corresponding to
    BaseRpcServer.__init__'s remaining arguments.
    """
    if _server_stub_base_class is object:
      raise NotImplementedError('Add //net/rpc/python:rpcserver as a '
                                'dependency for Stubby server support.')
    _server_stub_base_class.__init__(self, 'apphosting.SigningService', *args, **kwargs)

  @staticmethod
  def NewStub(rpc_stub_parameters, service_name=None):
    """Creates a new SigningService Stubby client stub.

    Args:
      rpc_stub_parameters: an RPC_StubParameters instance.
      service_name: the service name used by the Stubby server.
    """

    if _client_stub_base_class is object:
      raise RuntimeError('Add //net/rpc/python as a dependency to use Stubby')
    return _SigningService_ClientStub(rpc_stub_parameters, service_name)

  @staticmethod
  def NewRPC2Stub(server=None, channel=None, service_name=None):
    """Creates a new SigningService Stubby2 client stub.

    Args:
      server: host:port or bns address.
      channel: directly use a channel to create a stub. Will ignore server
          argument if this is specified.
      service_name: the service name used by the Stubby server.
    """

    if _client_stub_base_class is object:
      raise RuntimeError('Add //net/rpc/python as a dependency to use Stubby')
    return _SigningService_RPC2ClientStub(server, channel, service_name)

  def SignForApp(self, rpc, request, response):
    """Handles a SignForApp RPC call. You should override this.

    Args:
      rpc: a Stubby RPC object
      request: a SignForAppRequest that contains the client request
      response: a SignForAppResponse that should be modified to send the response
    """
    raise NotImplementedError


  def GetPublicCertificatesForApp(self, rpc, request, response):
    """Handles a GetPublicCertificatesForApp RPC call. You should override this.

    Args:
      rpc: a Stubby RPC object
      request: a GetPublicCertificateForAppRequest that contains the client request
      response: a GetPublicCertificateForAppResponse that should be modified to send the response
    """
    raise NotImplementedError


  def GetServiceAccountName(self, rpc, request, response):
    """Handles a GetServiceAccountName RPC call. You should override this.

    Args:
      rpc: a Stubby RPC object
      request: a GetServiceAccountNameRequest that contains the client request
      response: a GetServiceAccountNameResponse that should be modified to send the response
    """
    raise NotImplementedError


  def GetAccessToken(self, rpc, request, response):
    """Handles a GetAccessToken RPC call. You should override this.

    Args:
      rpc: a Stubby RPC object
      request: a GetAccessTokenRequest that contains the client request
      response: a GetAccessTokenResponse that should be modified to send the response
    """
    raise NotImplementedError


  def GetDefaultGcsBucketName(self, rpc, request, response):
    """Handles a GetDefaultGcsBucketName RPC call. You should override this.

    Args:
      rpc: a Stubby RPC object
      request: a GetDefaultGcsBucketNameRequest that contains the client request
      response: a GetDefaultGcsBucketNameResponse that should be modified to send the response
    """
    raise NotImplementedError

  def _AddMethodAttributes(self):
    """Sets attributes on Python RPC handlers.

    See BaseRpcServer in rpcserver.py for details.
    """
    rpcserver._GetHandlerDecorator(
        getattr(self.SignForApp, '__func__'),
        SignForAppRequest,
        SignForAppResponse,
        None,
        'INTEGRITY')
    rpcserver._GetHandlerDecorator(
        getattr(self.GetPublicCertificatesForApp, '__func__'),
        GetPublicCertificateForAppRequest,
        GetPublicCertificateForAppResponse,
        None,
        'INTEGRITY')
    rpcserver._GetHandlerDecorator(
        getattr(self.GetServiceAccountName, '__func__'),
        GetServiceAccountNameRequest,
        GetServiceAccountNameResponse,
        None,
        'INTEGRITY')
    rpcserver._GetHandlerDecorator(
        getattr(self.GetAccessToken, '__func__'),
        GetAccessTokenRequest,
        GetAccessTokenResponse,
        None,
        'INTEGRITY')
    rpcserver._GetHandlerDecorator(
        getattr(self.GetDefaultGcsBucketName, '__func__'),
        GetDefaultGcsBucketNameRequest,
        GetDefaultGcsBucketNameResponse,
        None,
        'INTEGRITY')

if _extension_runtime:
  pass

__all__ = ['AppIdentityServiceError','SignForAppRequest','SignForAppResponse','GetPublicCertificateForAppRequest','PublicCertificate','GetPublicCertificateForAppResponse','GetServiceAccountNameRequest','GetServiceAccountNameResponse','GetAccessTokenRequest','GetAccessTokenResponse','GetDefaultGcsBucketNameRequest','GetDefaultGcsBucketNameResponse','SigningService']
