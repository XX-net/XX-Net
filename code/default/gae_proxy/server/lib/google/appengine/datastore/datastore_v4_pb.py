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

from google.appengine.datastore.entity_v4_pb import *
import google.appengine.datastore.entity_v4_pb
class Error(ProtocolBuffer.ProtocolMessage):


  BAD_REQUEST  =    1
  CONCURRENT_TRANSACTION =    2
  INTERNAL_ERROR =    3
  NEED_INDEX   =    4
  TIMEOUT      =    5
  PERMISSION_DENIED =    6
  BIGTABLE_ERROR =    7
  COMMITTED_BUT_STILL_APPLYING =    8
  CAPABILITY_DISABLED =    9
  TRY_ALTERNATE_BACKEND =   10
  SAFE_TIME_TOO_OLD =   11
  RESOURCE_EXHAUSTED =   12

  _ErrorCode_NAMES = {
    1: "BAD_REQUEST",
    2: "CONCURRENT_TRANSACTION",
    3: "INTERNAL_ERROR",
    4: "NEED_INDEX",
    5: "TIMEOUT",
    6: "PERMISSION_DENIED",
    7: "BIGTABLE_ERROR",
    8: "COMMITTED_BUT_STILL_APPLYING",
    9: "CAPABILITY_DISABLED",
    10: "TRY_ALTERNATE_BACKEND",
    11: "SAFE_TIME_TOO_OLD",
    12: "RESOURCE_EXHAUSTED",
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
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.Error', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.Error')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.Error')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.Error', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.Error', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.Error', s)


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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.Error'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVycm9yc3oJRXJyb3JDb2RliwGSAQtCQURfUkVRVUVTVJgBAYwBiwGSARZDT05DVVJSRU5UX1RSQU5TQUNUSU9OmAECjAGLAZIBDklOVEVSTkFMX0VSUk9SmAEDjAGLAZIBCk5FRURfSU5ERViYAQSMAYsBkgEHVElNRU9VVJgBBYwBiwGSARFQRVJNSVNTSU9OX0RFTklFRJgBBowBiwGSAQ5CSUdUQUJMRV9FUlJPUpgBB4wBiwGSARxDT01NSVRURURfQlVUX1NUSUxMX0FQUExZSU5HmAEIjAGLAZIBE0NBUEFCSUxJVFlfRElTQUJMRUSYAQmMAYsBkgEVVFJZX0FMVEVSTkFURV9CQUNLRU5EmAEKjAGLAZIBEVNBRkVfVElNRV9UT09fT0xEmAELjAGLAZIBElJFU09VUkNFX0VYSEFVU1RFRJgBDIwBdLoBmTEKJ2FwcGhvc3RpbmcvZGF0YXN0b3JlL2RhdGFzdG9yZV92NC5wcm90bxIXYXBwaG9zdGluZy5kYXRhc3RvcmUudjQaJGFwcGhvc3RpbmcvZGF0YXN0b3JlL2VudGl0eV92NC5wcm90byKjAgoFRXJyb3IimQIKCUVycm9yQ29kZRIPCgtCQURfUkVRVUVTVBABEhoKFkNPTkNVUlJFTlRfVFJBTlNBQ1RJT04QAhISCg5JTlRFUk5BTF9FUlJPUhADEg4KCk5FRURfSU5ERVgQBBILCgdUSU1FT1VUEAUSFQoRUEVSTUlTU0lPTl9ERU5JRUQQBhISCg5CSUdUQUJMRV9FUlJPUhAHEiAKHENPTU1JVFRFRF9CVVRfU1RJTExfQVBQTFlJTkcQCBIXChNDQVBBQklMSVRZX0RJU0FCTEVEEAkSGQoVVFJZX0FMVEVSTkFURV9CQUNLRU5EEAoSFQoRU0FGRV9USU1FX1RPT19PTEQQCxIWChJSRVNPVVJDRV9FWEhBVVNURUQQDCKWAQoMRW50aXR5UmVzdWx0Ei8KBmVudGl0eRgBIAIoCzIfLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVudGl0eRIPCgd2ZXJzaW9uGAIgASgDEg4KBmN1cnNvchgDIAEoDCI0CgpSZXN1bHRUeXBlEggKBEZVTEwQARIOCgpQUk9KRUNUSU9OEAISDAoIS0VZX09OTFkQAyLxAgoFUXVlcnkSPwoKcHJvamVjdGlvbhgCIAMoCzIrLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlByb3BlcnR5RXhwcmVzc2lvbhI1CgRraW5kGAMgAygLMicuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuS2luZEV4cHJlc3Npb24SLwoGZmlsdGVyGAQgASgLMh8uYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRmlsdGVyEjUKBW9yZGVyGAUgAygLMiYuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUHJvcGVydHlPcmRlchI8Cghncm91cF9ieRgGIAMoCzIqLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlByb3BlcnR5UmVmZXJlbmNlEhQKDHN0YXJ0X2N1cnNvchgHIAEoDBISCgplbmRfY3Vyc29yGAggASgMEhEKBm9mZnNldBgKIAEoBToBMBINCgVsaW1pdBgLIAEoBSIeCg5LaW5kRXhwcmVzc2lvbhIMCgRuYW1lGAEgAigJIiEKEVByb3BlcnR5UmVmZXJlbmNlEgwKBG5hbWUYAiACKAki0wEKElByb3BlcnR5RXhwcmVzc2lvbhI8Cghwcm9wZXJ0eRgBIAIoCzIqLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlByb3BlcnR5UmVmZXJlbmNlEl0KFGFnZ3JlZ2F0aW9uX2Z1bmN0aW9uGAIgASgOMj8uYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUHJvcGVydHlFeHByZXNzaW9uLkFnZ3JlZ2F0aW9uRnVuY3Rpb24iIAoTQWdncmVnYXRpb25GdW5jdGlvbhIJCgVGSVJTVBABIskBCg1Qcm9wZXJ0eU9yZGVyEjwKCHByb3BlcnR5GAEgAigLMiouYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUHJvcGVydHlSZWZlcmVuY2USTgoJZGlyZWN0aW9uGAIgASgOMjAuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUHJvcGVydHlPcmRlci5EaXJlY3Rpb246CUFTQ0VORElORyIqCglEaXJlY3Rpb24SDQoJQVNDRU5ESU5HEAESDgoKREVTQ0VORElORxACIo4BCgZGaWx0ZXISQgoQY29tcG9zaXRlX2ZpbHRlchgBIAEoCzIoLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkNvbXBvc2l0ZUZpbHRlchJACg9wcm9wZXJ0eV9maWx0ZXIYAiABKAsyJy5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5Qcm9wZXJ0eUZpbHRlciKcAQoPQ29tcG9zaXRlRmlsdGVyEkMKCG9wZXJhdG9yGAEgAigOMjEuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuQ29tcG9zaXRlRmlsdGVyLk9wZXJhdG9yEi8KBmZpbHRlchgCIAMoCzIfLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkZpbHRlciITCghPcGVyYXRvchIHCgNBTkQQASK+AgoOUHJvcGVydHlGaWx0ZXISPAoIcHJvcGVydHkYASACKAsyKi5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5Qcm9wZXJ0eVJlZmVyZW5jZRJCCghvcGVyYXRvchgCIAIoDjIwLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlByb3BlcnR5RmlsdGVyLk9wZXJhdG9yEi0KBXZhbHVlGAMgAigLMh4uYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuVmFsdWUiewoIT3BlcmF0b3ISDQoJTEVTU19USEFOEAESFgoSTEVTU19USEFOX09SX0VRVUFMEAISEAoMR1JFQVRFUl9USEFOEAMSGQoVR1JFQVRFUl9USEFOX09SX0VRVUFMEAQSCQoFRVFVQUwQBRIQCgxIQVNfQU5DRVNUT1IQCyKwAQoIR3FsUXVlcnkSFAoMcXVlcnlfc3RyaW5nGAEgAigJEhwKDWFsbG93X2xpdGVyYWwYAiABKAg6BWZhbHNlEjYKCG5hbWVfYXJnGAMgAygLMiQuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuR3FsUXVlcnlBcmcSOAoKbnVtYmVyX2FyZxgEIAMoCzIkLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkdxbFF1ZXJ5QXJnIloKC0dxbFF1ZXJ5QXJnEgwKBG5hbWUYASABKAkSLQoFdmFsdWUYAiABKAsyHi5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5WYWx1ZRIOCgZjdXJzb3IYAyABKAwiqQMKEFF1ZXJ5UmVzdWx0QmF0Y2gSTAoSZW50aXR5X3Jlc3VsdF90eXBlGAEgAigOMjAuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRW50aXR5UmVzdWx0LlJlc3VsdFR5cGUSPAoNZW50aXR5X3Jlc3VsdBgCIAMoCzIlLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVudGl0eVJlc3VsdBIWCg5za2lwcGVkX2N1cnNvchgDIAEoDBISCgplbmRfY3Vyc29yGAQgASgMEk8KDG1vcmVfcmVzdWx0cxgFIAIoDjI5LmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlF1ZXJ5UmVzdWx0QmF0Y2guTW9yZVJlc3VsdHNUeXBlEhoKD3NraXBwZWRfcmVzdWx0cxgGIAEoBToBMBIYChBzbmFwc2hvdF92ZXJzaW9uGAcgASgDIlYKD01vcmVSZXN1bHRzVHlwZRIQCgxOT1RfRklOSVNIRUQQARIcChhNT1JFX1JFU1VMVFNfQUZURVJfTElNSVQQAhITCg9OT19NT1JFX1JFU1VMVFMQAyLyAQoITXV0YXRpb24SQAoCb3AYASABKA4yKy5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5NdXRhdGlvbi5PcGVyYXRpb246B1VOS05PV04SKQoDa2V5GAIgASgLMhwuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuS2V5Ei8KBmVudGl0eRgDIAEoCzIfLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVudGl0eSJICglPcGVyYXRpb24SCwoHVU5LTk9XThAAEgoKBklOU0VSVBABEgoKBlVQREFURRACEgoKBlVQU0VSVBADEgoKBkRFTEVURRAEIlMKDk11dGF0aW9uUmVzdWx0EikKA2tleRgDIAEoCzIcLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktleRIWCgtuZXdfdmVyc2lvbhgEIAEoAzoBMCKkAgoSRGVwcmVjYXRlZE11dGF0aW9uEi8KBnVwc2VydBgBIAMoCzIfLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVudGl0eRIvCgZ1cGRhdGUYAiADKAsyHy5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5FbnRpdHkSLwoGaW5zZXJ0GAMgAygLMh8uYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRW50aXR5EjcKDmluc2VydF9hdXRvX2lkGAQgAygLMh8uYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRW50aXR5EiwKBmRlbGV0ZRgFIAMoCzIcLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktleRIUCgVmb3JjZRgGIAEoCDoFZmFsc2Ui6wEKGERlcHJlY2F0ZWRNdXRhdGlvblJlc3VsdBIVCg1pbmRleF91cGRhdGVzGAEgAigFEjgKEmluc2VydF9hdXRvX2lkX2tleRgCIAMoCzIcLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktleRIWCg51cHNlcnRfdmVyc2lvbhgDIAMoAxIWCg51cGRhdGVfdmVyc2lvbhgEIAMoAxIWCg5pbnNlcnRfdmVyc2lvbhgFIAMoAxIeChZpbnNlcnRfYXV0b19pZF92ZXJzaW9uGAYgAygDEhYKDmRlbGV0ZV92ZXJzaW9uGAcgAygDIrUBCgtSZWFkT3B0aW9ucxJXChByZWFkX2NvbnNpc3RlbmN5GAEgASgOMjQuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUmVhZE9wdGlvbnMuUmVhZENvbnNpc3RlbmN5OgdERUZBVUxUEhMKC3RyYW5zYWN0aW9uGAIgASgMIjgKD1JlYWRDb25zaXN0ZW5jeRILCgdERUZBVUxUEAASCgoGU1RST05HEAESDAoIRVZFTlRVQUwQAiJ2Cg1Mb29rdXBSZXF1ZXN0EjoKDHJlYWRfb3B0aW9ucxgBIAEoCzIkLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlJlYWRPcHRpb25zEikKA2tleRgDIAMoCzIcLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktleSKuAQoOTG9va3VwUmVzcG9uc2USNAoFZm91bmQYASADKAsyJS5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5FbnRpdHlSZXN1bHQSNgoHbWlzc2luZxgCIAMoCzIlLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVudGl0eVJlc3VsdBIuCghkZWZlcnJlZBgDIAMoCzIcLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktleSKrAgoPUnVuUXVlcnlSZXF1ZXN0EjoKDHJlYWRfb3B0aW9ucxgBIAEoCzIkLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlJlYWRPcHRpb25zEjoKDHBhcnRpdGlvbl9pZBgCIAEoCzIkLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlBhcnRpdGlvbklkEi0KBXF1ZXJ5GAMgASgLMh4uYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUXVlcnkSNAoJZ3FsX3F1ZXJ5GAcgASgLMiEuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuR3FsUXVlcnkSHQoVbWluX3NhZmVfdGltZV9zZWNvbmRzGAQgASgDEhwKFHN1Z2dlc3RlZF9iYXRjaF9zaXplGAUgASgFImIKEFJ1blF1ZXJ5UmVzcG9uc2USOAoFYmF0Y2gYASACKAsyKS5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5RdWVyeVJlc3VsdEJhdGNoEhQKDHF1ZXJ5X2hhbmRsZRgCIAEoDCIsChRDb250aW51ZVF1ZXJ5UmVxdWVzdBIUCgxxdWVyeV9oYW5kbGUYASACKAwiUQoVQ29udGludWVRdWVyeVJlc3BvbnNlEjgKBWJhdGNoGAEgAigLMikuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUXVlcnlSZXN1bHRCYXRjaCJTChdCZWdpblRyYW5zYWN0aW9uUmVxdWVzdBIaCgtjcm9zc19ncm91cBgBIAEoCDoFZmFsc2USHAoNY3Jvc3NfcmVxdWVzdBgCIAEoCDoFZmFsc2UiLwoYQmVnaW5UcmFuc2FjdGlvblJlc3BvbnNlEhMKC3RyYW5zYWN0aW9uGAEgAigMIiYKD1JvbGxiYWNrUmVxdWVzdBITCgt0cmFuc2FjdGlvbhgBIAIoDCISChBSb2xsYmFja1Jlc3BvbnNlIsACCg1Db21taXRSZXF1ZXN0EhMKC3RyYW5zYWN0aW9uGAEgASgMEjMKCG11dGF0aW9uGAUgAygLMiEuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuTXV0YXRpb24SSAoTZGVwcmVjYXRlZF9tdXRhdGlvbhgCIAEoCzIrLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkRlcHJlY2F0ZWRNdXRhdGlvbhJICgRtb2RlGAQgASgOMisuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuQ29tbWl0UmVxdWVzdC5Nb2RlOg1UUkFOU0FDVElPTkFMEh8KEGlnbm9yZV9yZWFkX29ubHkYBiABKAg6BWZhbHNlIjAKBE1vZGUSEQoNVFJBTlNBQ1RJT05BTBABEhUKEU5PTl9UUkFOU0FDVElPTkFMEAIiwAEKDkNvbW1pdFJlc3BvbnNlEkAKD211dGF0aW9uX3Jlc3VsdBgDIAMoCzInLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0Lk11dGF0aW9uUmVzdWx0ElUKGmRlcHJlY2F0ZWRfbXV0YXRpb25fcmVzdWx0GAEgASgLMjEuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRGVwcmVjYXRlZE11dGF0aW9uUmVzdWx0EhUKDWluZGV4X3VwZGF0ZXMYBCABKAUicwoSQWxsb2NhdGVJZHNSZXF1ZXN0Ei4KCGFsbG9jYXRlGAEgAygLMhwuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuS2V5Ei0KB3Jlc2VydmUYAiADKAsyHC5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5LZXkiRgoTQWxsb2NhdGVJZHNSZXNwb25zZRIvCglhbGxvY2F0ZWQYASADKAsyHC5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5LZXky7QUKEkRhdGFzdG9yZVY0U2VydmljZRJ5ChBCZWdpblRyYW5zYWN0aW9uEjAuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuQmVnaW5UcmFuc2FjdGlvblJlcXVlc3QaMS5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5CZWdpblRyYW5zYWN0aW9uUmVzcG9uc2UiABJhCghSb2xsYmFjaxIoLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlJvbGxiYWNrUmVxdWVzdBopLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlJvbGxiYWNrUmVzcG9uc2UiABJbCgZDb21taXQSJi5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5Db21taXRSZXF1ZXN0GicuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuQ29tbWl0UmVzcG9uc2UiABJhCghSdW5RdWVyeRIoLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlJ1blF1ZXJ5UmVxdWVzdBopLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlJ1blF1ZXJ5UmVzcG9uc2UiABJwCg1Db250aW51ZVF1ZXJ5Ei0uYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuQ29udGludWVRdWVyeVJlcXVlc3QaLi5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5Db250aW51ZVF1ZXJ5UmVzcG9uc2UiABJbCgZMb29rdXASJi5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5Mb29rdXBSZXF1ZXN0GicuYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuTG9va3VwUmVzcG9uc2UiABJqCgtBbGxvY2F0ZUlkcxIrLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkFsbG9jYXRlSWRzUmVxdWVzdBosLmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkFsbG9jYXRlSWRzUmVzcG9uc2UiAEIjCh9jb20uZ29vZ2xlLmFwcGhvc3RpbmcuZGF0YXN0b3JlIAE="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class EntityResult(ProtocolBuffer.ProtocolMessage):


  FULL         =    1
  PROJECTION   =    2
  KEY_ONLY     =    3

  _ResultType_NAMES = {
    1: "FULL",
    2: "PROJECTION",
    3: "KEY_ONLY",
  }

  def ResultType_Name(cls, x): return cls._ResultType_NAMES.get(x, "")
  ResultType_Name = classmethod(ResultType_Name)

  has_entity_ = 0
  has_version_ = 0
  version_ = 0
  has_cursor_ = 0
  cursor_ = ""

  def __init__(self, contents=None):
    self.entity_ = google.appengine.datastore.entity_v4_pb.Entity()
    if contents is not None: self.MergeFromString(contents)

  def entity(self): return self.entity_

  def mutable_entity(self): self.has_entity_ = 1; return self.entity_

  def clear_entity(self):self.has_entity_ = 0; self.entity_.Clear()

  def has_entity(self): return self.has_entity_

  def version(self): return self.version_

  def set_version(self, x):
    self.has_version_ = 1
    self.version_ = x

  def clear_version(self):
    if self.has_version_:
      self.has_version_ = 0
      self.version_ = 0

  def has_version(self): return self.has_version_

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
    if (x.has_entity()): self.mutable_entity().MergeFrom(x.entity())
    if (x.has_version()): self.set_version(x.version())
    if (x.has_cursor()): self.set_cursor(x.cursor())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.EntityResult', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.EntityResult')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.EntityResult')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.EntityResult', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.EntityResult', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.EntityResult', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_entity_ != x.has_entity_: return 0
    if self.has_entity_ and self.entity_ != x.entity_: return 0
    if self.has_version_ != x.has_version_: return 0
    if self.has_version_ and self.version_ != x.version_: return 0
    if self.has_cursor_ != x.has_cursor_: return 0
    if self.has_cursor_ and self.cursor_ != x.cursor_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_entity_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: entity not set.')
    elif not self.entity_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.entity_.ByteSize())
    if (self.has_version_): n += 1 + self.lengthVarInt64(self.version_)
    if (self.has_cursor_): n += 1 + self.lengthString(len(self.cursor_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_entity_):
      n += 1
      n += self.lengthString(self.entity_.ByteSizePartial())
    if (self.has_version_): n += 1 + self.lengthVarInt64(self.version_)
    if (self.has_cursor_): n += 1 + self.lengthString(len(self.cursor_))
    return n

  def Clear(self):
    self.clear_entity()
    self.clear_version()
    self.clear_cursor()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.entity_.ByteSize())
    self.entity_.OutputUnchecked(out)
    if (self.has_version_):
      out.putVarInt32(16)
      out.putVarInt64(self.version_)
    if (self.has_cursor_):
      out.putVarInt32(26)
      out.putPrefixedString(self.cursor_)

  def OutputPartial(self, out):
    if (self.has_entity_):
      out.putVarInt32(10)
      out.putVarInt32(self.entity_.ByteSizePartial())
      self.entity_.OutputPartial(out)
    if (self.has_version_):
      out.putVarInt32(16)
      out.putVarInt64(self.version_)
    if (self.has_cursor_):
      out.putVarInt32(26)
      out.putPrefixedString(self.cursor_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_entity().TryMerge(tmp)
        continue
      if tt == 16:
        self.set_version(d.getVarInt64())
        continue
      if tt == 26:
        self.set_cursor(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_entity_:
      res+=prefix+"entity <\n"
      res+=self.entity_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_version_: res+=prefix+("version: %s\n" % self.DebugFormatInt64(self.version_))
    if self.has_cursor_: res+=prefix+("cursor: %s\n" % self.DebugFormatString(self.cursor_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kentity = 1
  kversion = 2
  kcursor = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "entity",
    2: "version",
    3: "cursor",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.EntityResult'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KJGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVudGl0eVJlc3VsdBMaBmVudGl0eSABKAIwCzgCSh5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5FbnRpdHmjAaoBBWN0eXBlsgEGcHJvdG8ypAEUExoHdmVyc2lvbiACKAAwAzgBFBMaBmN1cnNvciADKAIwCTgBFHN6ClJlc3VsdFR5cGWLAZIBBEZVTEyYAQGMAYsBkgEKUFJPSkVDVElPTpgBAowBiwGSAQhLRVlfT05MWZgBA4wBdMIBHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVycm9y"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class Query(ProtocolBuffer.ProtocolMessage):
  has_filter_ = 0
  filter_ = None
  has_start_cursor_ = 0
  start_cursor_ = ""
  has_end_cursor_ = 0
  end_cursor_ = ""
  has_offset_ = 0
  offset_ = 0
  has_limit_ = 0
  limit_ = 0

  def __init__(self, contents=None):
    self.projection_ = []
    self.kind_ = []
    self.order_ = []
    self.group_by_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def projection_size(self): return len(self.projection_)
  def projection_list(self): return self.projection_

  def projection(self, i):
    return self.projection_[i]

  def mutable_projection(self, i):
    return self.projection_[i]

  def add_projection(self):
    x = PropertyExpression()
    self.projection_.append(x)
    return x

  def clear_projection(self):
    self.projection_ = []
  def kind_size(self): return len(self.kind_)
  def kind_list(self): return self.kind_

  def kind(self, i):
    return self.kind_[i]

  def mutable_kind(self, i):
    return self.kind_[i]

  def add_kind(self):
    x = KindExpression()
    self.kind_.append(x)
    return x

  def clear_kind(self):
    self.kind_ = []
  def filter(self):
    if self.filter_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.filter_ is None: self.filter_ = Filter()
      finally:
        self.lazy_init_lock_.release()
    return self.filter_

  def mutable_filter(self): self.has_filter_ = 1; return self.filter()

  def clear_filter(self):

    if self.has_filter_:
      self.has_filter_ = 0;
      if self.filter_ is not None: self.filter_.Clear()

  def has_filter(self): return self.has_filter_

  def order_size(self): return len(self.order_)
  def order_list(self): return self.order_

  def order(self, i):
    return self.order_[i]

  def mutable_order(self, i):
    return self.order_[i]

  def add_order(self):
    x = PropertyOrder()
    self.order_.append(x)
    return x

  def clear_order(self):
    self.order_ = []
  def group_by_size(self): return len(self.group_by_)
  def group_by_list(self): return self.group_by_

  def group_by(self, i):
    return self.group_by_[i]

  def mutable_group_by(self, i):
    return self.group_by_[i]

  def add_group_by(self):
    x = PropertyReference()
    self.group_by_.append(x)
    return x

  def clear_group_by(self):
    self.group_by_ = []
  def start_cursor(self): return self.start_cursor_

  def set_start_cursor(self, x):
    self.has_start_cursor_ = 1
    self.start_cursor_ = x

  def clear_start_cursor(self):
    if self.has_start_cursor_:
      self.has_start_cursor_ = 0
      self.start_cursor_ = ""

  def has_start_cursor(self): return self.has_start_cursor_

  def end_cursor(self): return self.end_cursor_

  def set_end_cursor(self, x):
    self.has_end_cursor_ = 1
    self.end_cursor_ = x

  def clear_end_cursor(self):
    if self.has_end_cursor_:
      self.has_end_cursor_ = 0
      self.end_cursor_ = ""

  def has_end_cursor(self): return self.has_end_cursor_

  def offset(self): return self.offset_

  def set_offset(self, x):
    self.has_offset_ = 1
    self.offset_ = x

  def clear_offset(self):
    if self.has_offset_:
      self.has_offset_ = 0
      self.offset_ = 0

  def has_offset(self): return self.has_offset_

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
    for i in xrange(x.projection_size()): self.add_projection().CopyFrom(x.projection(i))
    for i in xrange(x.kind_size()): self.add_kind().CopyFrom(x.kind(i))
    if (x.has_filter()): self.mutable_filter().MergeFrom(x.filter())
    for i in xrange(x.order_size()): self.add_order().CopyFrom(x.order(i))
    for i in xrange(x.group_by_size()): self.add_group_by().CopyFrom(x.group_by(i))
    if (x.has_start_cursor()): self.set_start_cursor(x.start_cursor())
    if (x.has_end_cursor()): self.set_end_cursor(x.end_cursor())
    if (x.has_offset()): self.set_offset(x.offset())
    if (x.has_limit()): self.set_limit(x.limit())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.Query', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.Query')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.Query')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.Query', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.Query', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.Query', s)


  def Equals(self, x):
    if x is self: return 1
    if len(self.projection_) != len(x.projection_): return 0
    for e1, e2 in zip(self.projection_, x.projection_):
      if e1 != e2: return 0
    if len(self.kind_) != len(x.kind_): return 0
    for e1, e2 in zip(self.kind_, x.kind_):
      if e1 != e2: return 0
    if self.has_filter_ != x.has_filter_: return 0
    if self.has_filter_ and self.filter_ != x.filter_: return 0
    if len(self.order_) != len(x.order_): return 0
    for e1, e2 in zip(self.order_, x.order_):
      if e1 != e2: return 0
    if len(self.group_by_) != len(x.group_by_): return 0
    for e1, e2 in zip(self.group_by_, x.group_by_):
      if e1 != e2: return 0
    if self.has_start_cursor_ != x.has_start_cursor_: return 0
    if self.has_start_cursor_ and self.start_cursor_ != x.start_cursor_: return 0
    if self.has_end_cursor_ != x.has_end_cursor_: return 0
    if self.has_end_cursor_ and self.end_cursor_ != x.end_cursor_: return 0
    if self.has_offset_ != x.has_offset_: return 0
    if self.has_offset_ and self.offset_ != x.offset_: return 0
    if self.has_limit_ != x.has_limit_: return 0
    if self.has_limit_ and self.limit_ != x.limit_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.projection_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.kind_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_filter_ and not self.filter_.IsInitialized(debug_strs)): initialized = 0
    for p in self.order_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.group_by_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.projection_)
    for i in xrange(len(self.projection_)): n += self.lengthString(self.projection_[i].ByteSize())
    n += 1 * len(self.kind_)
    for i in xrange(len(self.kind_)): n += self.lengthString(self.kind_[i].ByteSize())
    if (self.has_filter_): n += 1 + self.lengthString(self.filter_.ByteSize())
    n += 1 * len(self.order_)
    for i in xrange(len(self.order_)): n += self.lengthString(self.order_[i].ByteSize())
    n += 1 * len(self.group_by_)
    for i in xrange(len(self.group_by_)): n += self.lengthString(self.group_by_[i].ByteSize())
    if (self.has_start_cursor_): n += 1 + self.lengthString(len(self.start_cursor_))
    if (self.has_end_cursor_): n += 1 + self.lengthString(len(self.end_cursor_))
    if (self.has_offset_): n += 1 + self.lengthVarInt64(self.offset_)
    if (self.has_limit_): n += 1 + self.lengthVarInt64(self.limit_)
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.projection_)
    for i in xrange(len(self.projection_)): n += self.lengthString(self.projection_[i].ByteSizePartial())
    n += 1 * len(self.kind_)
    for i in xrange(len(self.kind_)): n += self.lengthString(self.kind_[i].ByteSizePartial())
    if (self.has_filter_): n += 1 + self.lengthString(self.filter_.ByteSizePartial())
    n += 1 * len(self.order_)
    for i in xrange(len(self.order_)): n += self.lengthString(self.order_[i].ByteSizePartial())
    n += 1 * len(self.group_by_)
    for i in xrange(len(self.group_by_)): n += self.lengthString(self.group_by_[i].ByteSizePartial())
    if (self.has_start_cursor_): n += 1 + self.lengthString(len(self.start_cursor_))
    if (self.has_end_cursor_): n += 1 + self.lengthString(len(self.end_cursor_))
    if (self.has_offset_): n += 1 + self.lengthVarInt64(self.offset_)
    if (self.has_limit_): n += 1 + self.lengthVarInt64(self.limit_)
    return n

  def Clear(self):
    self.clear_projection()
    self.clear_kind()
    self.clear_filter()
    self.clear_order()
    self.clear_group_by()
    self.clear_start_cursor()
    self.clear_end_cursor()
    self.clear_offset()
    self.clear_limit()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.projection_)):
      out.putVarInt32(18)
      out.putVarInt32(self.projection_[i].ByteSize())
      self.projection_[i].OutputUnchecked(out)
    for i in xrange(len(self.kind_)):
      out.putVarInt32(26)
      out.putVarInt32(self.kind_[i].ByteSize())
      self.kind_[i].OutputUnchecked(out)
    if (self.has_filter_):
      out.putVarInt32(34)
      out.putVarInt32(self.filter_.ByteSize())
      self.filter_.OutputUnchecked(out)
    for i in xrange(len(self.order_)):
      out.putVarInt32(42)
      out.putVarInt32(self.order_[i].ByteSize())
      self.order_[i].OutputUnchecked(out)
    for i in xrange(len(self.group_by_)):
      out.putVarInt32(50)
      out.putVarInt32(self.group_by_[i].ByteSize())
      self.group_by_[i].OutputUnchecked(out)
    if (self.has_start_cursor_):
      out.putVarInt32(58)
      out.putPrefixedString(self.start_cursor_)
    if (self.has_end_cursor_):
      out.putVarInt32(66)
      out.putPrefixedString(self.end_cursor_)
    if (self.has_offset_):
      out.putVarInt32(80)
      out.putVarInt32(self.offset_)
    if (self.has_limit_):
      out.putVarInt32(88)
      out.putVarInt32(self.limit_)

  def OutputPartial(self, out):
    for i in xrange(len(self.projection_)):
      out.putVarInt32(18)
      out.putVarInt32(self.projection_[i].ByteSizePartial())
      self.projection_[i].OutputPartial(out)
    for i in xrange(len(self.kind_)):
      out.putVarInt32(26)
      out.putVarInt32(self.kind_[i].ByteSizePartial())
      self.kind_[i].OutputPartial(out)
    if (self.has_filter_):
      out.putVarInt32(34)
      out.putVarInt32(self.filter_.ByteSizePartial())
      self.filter_.OutputPartial(out)
    for i in xrange(len(self.order_)):
      out.putVarInt32(42)
      out.putVarInt32(self.order_[i].ByteSizePartial())
      self.order_[i].OutputPartial(out)
    for i in xrange(len(self.group_by_)):
      out.putVarInt32(50)
      out.putVarInt32(self.group_by_[i].ByteSizePartial())
      self.group_by_[i].OutputPartial(out)
    if (self.has_start_cursor_):
      out.putVarInt32(58)
      out.putPrefixedString(self.start_cursor_)
    if (self.has_end_cursor_):
      out.putVarInt32(66)
      out.putPrefixedString(self.end_cursor_)
    if (self.has_offset_):
      out.putVarInt32(80)
      out.putVarInt32(self.offset_)
    if (self.has_limit_):
      out.putVarInt32(88)
      out.putVarInt32(self.limit_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_projection().TryMerge(tmp)
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_kind().TryMerge(tmp)
        continue
      if tt == 34:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_filter().TryMerge(tmp)
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_order().TryMerge(tmp)
        continue
      if tt == 50:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_group_by().TryMerge(tmp)
        continue
      if tt == 58:
        self.set_start_cursor(d.getPrefixedString())
        continue
      if tt == 66:
        self.set_end_cursor(d.getPrefixedString())
        continue
      if tt == 80:
        self.set_offset(d.getVarInt32())
        continue
      if tt == 88:
        self.set_limit(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.projection_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("projection%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.kind_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("kind%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_filter_:
      res+=prefix+"filter <\n"
      res+=self.filter_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.order_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("order%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.group_by_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("group_by%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_start_cursor_: res+=prefix+("start_cursor: %s\n" % self.DebugFormatString(self.start_cursor_))
    if self.has_end_cursor_: res+=prefix+("end_cursor: %s\n" % self.DebugFormatString(self.end_cursor_))
    if self.has_offset_: res+=prefix+("offset: %s\n" % self.DebugFormatInt32(self.offset_))
    if self.has_limit_: res+=prefix+("limit: %s\n" % self.DebugFormatInt32(self.limit_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kprojection = 2
  kkind = 3
  kfilter = 4
  korder = 5
  kgroup_by = 6
  kstart_cursor = 7
  kend_cursor = 8
  koffset = 10
  klimit = 11

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    2: "projection",
    3: "kind",
    4: "filter",
    5: "order",
    6: "group_by",
    7: "start_cursor",
    8: "end_cursor",
    10: "offset",
    11: "limit",
  }, 11)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.STRING,
    7: ProtocolBuffer.Encoder.STRING,
    8: ProtocolBuffer.Encoder.STRING,
    10: ProtocolBuffer.Encoder.NUMERIC,
    11: ProtocolBuffer.Encoder.NUMERIC,
  }, 11, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.Query'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlF1ZXJ5ExoKcHJvamVjdGlvbiACKAIwCzgDSiphcHBob3N0aW5nLmRhdGFzdG9yZS52NC5Qcm9wZXJ0eUV4cHJlc3Npb26jAaoBBWN0eXBlsgEGcHJvdG8ypAEUExoEa2luZCADKAIwCzgDSiZhcHBob3N0aW5nLmRhdGFzdG9yZS52NC5LaW5kRXhwcmVzc2lvbqMBqgEFY3R5cGWyAQZwcm90bzKkARQTGgZmaWx0ZXIgBCgCMAs4AUoeYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRmlsdGVyowGqAQVjdHlwZbIBBnByb3RvMqQBFBMaBW9yZGVyIAUoAjALOANKJWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlByb3BlcnR5T3JkZXKjAaoBBWN0eXBlsgEGcHJvdG8ypAEUExoIZ3JvdXBfYnkgBigCMAs4A0opYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUHJvcGVydHlSZWZlcmVuY2WjAaoBBWN0eXBlsgEGcHJvdG8ypAEUExoMc3RhcnRfY3Vyc29yIAcoAjAJOAEUExoKZW5kX2N1cnNvciAIKAIwCTgBFBMaBm9mZnNldCAKKAAwBTgBQgEwowGqAQdkZWZhdWx0sgEBMKQBFBMaBWxpbWl0IAsoADAFOAEUwgEdYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class KindExpression(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""

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


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.KindExpression', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.KindExpression')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.KindExpression')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.KindExpression', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.KindExpression', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.KindExpression', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
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
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    return n

  def Clear(self):
    self.clear_name()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.name_)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.KindExpression'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KJmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktpbmRFeHByZXNzaW9uExoEbmFtZSABKAIwCTgCFMIBHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVycm9y"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class PropertyReference(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""

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


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.PropertyReference', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.PropertyReference')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.PropertyReference')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.PropertyReference', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.PropertyReference', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.PropertyReference', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
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
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    return n

  def Clear(self):
    self.clear_name()

  def OutputUnchecked(self, out):
    out.putVarInt32(18)
    out.putPrefixedString(self.name_)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(18)
      out.putPrefixedString(self.name_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 18:
        self.set_name(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    2: "name",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.PropertyReference'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KKWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlByb3BlcnR5UmVmZXJlbmNlExoEbmFtZSACKAIwCTgCFMIBHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVycm9y"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class PropertyExpression(ProtocolBuffer.ProtocolMessage):


  FIRST        =    1

  _AggregationFunction_NAMES = {
    1: "FIRST",
  }

  def AggregationFunction_Name(cls, x): return cls._AggregationFunction_NAMES.get(x, "")
  AggregationFunction_Name = classmethod(AggregationFunction_Name)

  has_property_ = 0
  has_aggregation_function_ = 0
  aggregation_function_ = 0

  def __init__(self, contents=None):
    self.property_ = PropertyReference()
    if contents is not None: self.MergeFromString(contents)

  def property(self): return self.property_

  def mutable_property(self): self.has_property_ = 1; return self.property_

  def clear_property(self):self.has_property_ = 0; self.property_.Clear()

  def has_property(self): return self.has_property_

  def aggregation_function(self): return self.aggregation_function_

  def set_aggregation_function(self, x):
    self.has_aggregation_function_ = 1
    self.aggregation_function_ = x

  def clear_aggregation_function(self):
    if self.has_aggregation_function_:
      self.has_aggregation_function_ = 0
      self.aggregation_function_ = 0

  def has_aggregation_function(self): return self.has_aggregation_function_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_property()): self.mutable_property().MergeFrom(x.property())
    if (x.has_aggregation_function()): self.set_aggregation_function(x.aggregation_function())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.PropertyExpression', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.PropertyExpression')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.PropertyExpression')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.PropertyExpression', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.PropertyExpression', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.PropertyExpression', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_property_ != x.has_property_: return 0
    if self.has_property_ and self.property_ != x.property_: return 0
    if self.has_aggregation_function_ != x.has_aggregation_function_: return 0
    if self.has_aggregation_function_ and self.aggregation_function_ != x.aggregation_function_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_property_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: property not set.')
    elif not self.property_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.property_.ByteSize())
    if (self.has_aggregation_function_): n += 1 + self.lengthVarInt64(self.aggregation_function_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_property_):
      n += 1
      n += self.lengthString(self.property_.ByteSizePartial())
    if (self.has_aggregation_function_): n += 1 + self.lengthVarInt64(self.aggregation_function_)
    return n

  def Clear(self):
    self.clear_property()
    self.clear_aggregation_function()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.property_.ByteSize())
    self.property_.OutputUnchecked(out)
    if (self.has_aggregation_function_):
      out.putVarInt32(16)
      out.putVarInt32(self.aggregation_function_)

  def OutputPartial(self, out):
    if (self.has_property_):
      out.putVarInt32(10)
      out.putVarInt32(self.property_.ByteSizePartial())
      self.property_.OutputPartial(out)
    if (self.has_aggregation_function_):
      out.putVarInt32(16)
      out.putVarInt32(self.aggregation_function_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_property().TryMerge(tmp)
        continue
      if tt == 16:
        self.set_aggregation_function(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_property_:
      res+=prefix+"property <\n"
      res+=self.property_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_aggregation_function_: res+=prefix+("aggregation_function: %s\n" % self.DebugFormatInt32(self.aggregation_function_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kproperty = 1
  kaggregation_function = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "property",
    2: "aggregation_function",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.PropertyExpression'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KKmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlByb3BlcnR5RXhwcmVzc2lvbhMaCHByb3BlcnR5IAEoAjALOAJKKWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlByb3BlcnR5UmVmZXJlbmNlowGqAQVjdHlwZbIBBnByb3RvMqQBFBMaFGFnZ3JlZ2F0aW9uX2Z1bmN0aW9uIAIoADAFOAFoABRzehNBZ2dyZWdhdGlvbkZ1bmN0aW9uiwGSAQVGSVJTVJgBAYwBdMIBHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVycm9y"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class PropertyOrder(ProtocolBuffer.ProtocolMessage):


  ASCENDING    =    1
  DESCENDING   =    2

  _Direction_NAMES = {
    1: "ASCENDING",
    2: "DESCENDING",
  }

  def Direction_Name(cls, x): return cls._Direction_NAMES.get(x, "")
  Direction_Name = classmethod(Direction_Name)

  has_property_ = 0
  has_direction_ = 0
  direction_ = 1

  def __init__(self, contents=None):
    self.property_ = PropertyReference()
    if contents is not None: self.MergeFromString(contents)

  def property(self): return self.property_

  def mutable_property(self): self.has_property_ = 1; return self.property_

  def clear_property(self):self.has_property_ = 0; self.property_.Clear()

  def has_property(self): return self.has_property_

  def direction(self): return self.direction_

  def set_direction(self, x):
    self.has_direction_ = 1
    self.direction_ = x

  def clear_direction(self):
    if self.has_direction_:
      self.has_direction_ = 0
      self.direction_ = 1

  def has_direction(self): return self.has_direction_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_property()): self.mutable_property().MergeFrom(x.property())
    if (x.has_direction()): self.set_direction(x.direction())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.PropertyOrder', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.PropertyOrder')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.PropertyOrder')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.PropertyOrder', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.PropertyOrder', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.PropertyOrder', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_property_ != x.has_property_: return 0
    if self.has_property_ and self.property_ != x.property_: return 0
    if self.has_direction_ != x.has_direction_: return 0
    if self.has_direction_ and self.direction_ != x.direction_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_property_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: property not set.')
    elif not self.property_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.property_.ByteSize())
    if (self.has_direction_): n += 1 + self.lengthVarInt64(self.direction_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_property_):
      n += 1
      n += self.lengthString(self.property_.ByteSizePartial())
    if (self.has_direction_): n += 1 + self.lengthVarInt64(self.direction_)
    return n

  def Clear(self):
    self.clear_property()
    self.clear_direction()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.property_.ByteSize())
    self.property_.OutputUnchecked(out)
    if (self.has_direction_):
      out.putVarInt32(16)
      out.putVarInt32(self.direction_)

  def OutputPartial(self, out):
    if (self.has_property_):
      out.putVarInt32(10)
      out.putVarInt32(self.property_.ByteSizePartial())
      self.property_.OutputPartial(out)
    if (self.has_direction_):
      out.putVarInt32(16)
      out.putVarInt32(self.direction_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_property().TryMerge(tmp)
        continue
      if tt == 16:
        self.set_direction(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_property_:
      res+=prefix+"property <\n"
      res+=self.property_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_direction_: res+=prefix+("direction: %s\n" % self.DebugFormatInt32(self.direction_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kproperty = 1
  kdirection = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "property",
    2: "direction",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.PropertyOrder'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KJWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlByb3BlcnR5T3JkZXITGghwcm9wZXJ0eSABKAIwCzgCSilhcHBob3N0aW5nLmRhdGFzdG9yZS52NC5Qcm9wZXJ0eVJlZmVyZW5jZaMBqgEFY3R5cGWyAQZwcm90bzKkARQTGglkaXJlY3Rpb24gAigAMAU4AUIBMWgAowGqAQdkZWZhdWx0sgEJQVNDRU5ESU5HpAEUc3oJRGlyZWN0aW9uiwGSAQlBU0NFTkRJTkeYAQGMAYsBkgEKREVTQ0VORElOR5gBAowBdMIBHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVycm9y"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class Filter(ProtocolBuffer.ProtocolMessage):
  has_composite_filter_ = 0
  composite_filter_ = None
  has_property_filter_ = 0
  property_filter_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def composite_filter(self):
    if self.composite_filter_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.composite_filter_ is None: self.composite_filter_ = CompositeFilter()
      finally:
        self.lazy_init_lock_.release()
    return self.composite_filter_

  def mutable_composite_filter(self): self.has_composite_filter_ = 1; return self.composite_filter()

  def clear_composite_filter(self):

    if self.has_composite_filter_:
      self.has_composite_filter_ = 0;
      if self.composite_filter_ is not None: self.composite_filter_.Clear()

  def has_composite_filter(self): return self.has_composite_filter_

  def property_filter(self):
    if self.property_filter_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.property_filter_ is None: self.property_filter_ = PropertyFilter()
      finally:
        self.lazy_init_lock_.release()
    return self.property_filter_

  def mutable_property_filter(self): self.has_property_filter_ = 1; return self.property_filter()

  def clear_property_filter(self):

    if self.has_property_filter_:
      self.has_property_filter_ = 0;
      if self.property_filter_ is not None: self.property_filter_.Clear()

  def has_property_filter(self): return self.has_property_filter_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_composite_filter()): self.mutable_composite_filter().MergeFrom(x.composite_filter())
    if (x.has_property_filter()): self.mutable_property_filter().MergeFrom(x.property_filter())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.Filter', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.Filter')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.Filter')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.Filter', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.Filter', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.Filter', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_composite_filter_ != x.has_composite_filter_: return 0
    if self.has_composite_filter_ and self.composite_filter_ != x.composite_filter_: return 0
    if self.has_property_filter_ != x.has_property_filter_: return 0
    if self.has_property_filter_ and self.property_filter_ != x.property_filter_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_composite_filter_ and not self.composite_filter_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_property_filter_ and not self.property_filter_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_composite_filter_): n += 1 + self.lengthString(self.composite_filter_.ByteSize())
    if (self.has_property_filter_): n += 1 + self.lengthString(self.property_filter_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_composite_filter_): n += 1 + self.lengthString(self.composite_filter_.ByteSizePartial())
    if (self.has_property_filter_): n += 1 + self.lengthString(self.property_filter_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_composite_filter()
    self.clear_property_filter()

  def OutputUnchecked(self, out):
    if (self.has_composite_filter_):
      out.putVarInt32(10)
      out.putVarInt32(self.composite_filter_.ByteSize())
      self.composite_filter_.OutputUnchecked(out)
    if (self.has_property_filter_):
      out.putVarInt32(18)
      out.putVarInt32(self.property_filter_.ByteSize())
      self.property_filter_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_composite_filter_):
      out.putVarInt32(10)
      out.putVarInt32(self.composite_filter_.ByteSizePartial())
      self.composite_filter_.OutputPartial(out)
    if (self.has_property_filter_):
      out.putVarInt32(18)
      out.putVarInt32(self.property_filter_.ByteSizePartial())
      self.property_filter_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_composite_filter().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_property_filter().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_composite_filter_:
      res+=prefix+"composite_filter <\n"
      res+=self.composite_filter_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_property_filter_:
      res+=prefix+"property_filter <\n"
      res+=self.property_filter_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kcomposite_filter = 1
  kproperty_filter = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "composite_filter",
    2: "property_filter",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.Filter'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KHmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkZpbHRlchMaEGNvbXBvc2l0ZV9maWx0ZXIgASgCMAs4AUonYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuQ29tcG9zaXRlRmlsdGVyowGqAQVjdHlwZbIBBnByb3RvMqQBFBMaD3Byb3BlcnR5X2ZpbHRlciACKAIwCzgBSiZhcHBob3N0aW5nLmRhdGFzdG9yZS52NC5Qcm9wZXJ0eUZpbHRlcqMBqgEFY3R5cGWyAQZwcm90bzKkARTCAR1hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5FcnJvcg=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class CompositeFilter(ProtocolBuffer.ProtocolMessage):


  AND          =    1

  _Operator_NAMES = {
    1: "AND",
  }

  def Operator_Name(cls, x): return cls._Operator_NAMES.get(x, "")
  Operator_Name = classmethod(Operator_Name)

  has_operator_ = 0
  operator_ = 0

  def __init__(self, contents=None):
    self.filter_ = []
    if contents is not None: self.MergeFromString(contents)

  def operator(self): return self.operator_

  def set_operator(self, x):
    self.has_operator_ = 1
    self.operator_ = x

  def clear_operator(self):
    if self.has_operator_:
      self.has_operator_ = 0
      self.operator_ = 0

  def has_operator(self): return self.has_operator_

  def filter_size(self): return len(self.filter_)
  def filter_list(self): return self.filter_

  def filter(self, i):
    return self.filter_[i]

  def mutable_filter(self, i):
    return self.filter_[i]

  def add_filter(self):
    x = Filter()
    self.filter_.append(x)
    return x

  def clear_filter(self):
    self.filter_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_operator()): self.set_operator(x.operator())
    for i in xrange(x.filter_size()): self.add_filter().CopyFrom(x.filter(i))

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.CompositeFilter', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.CompositeFilter')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.CompositeFilter')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.CompositeFilter', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.CompositeFilter', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.CompositeFilter', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_operator_ != x.has_operator_: return 0
    if self.has_operator_ and self.operator_ != x.operator_: return 0
    if len(self.filter_) != len(x.filter_): return 0
    for e1, e2 in zip(self.filter_, x.filter_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_operator_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: operator not set.')
    for p in self.filter_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.operator_)
    n += 1 * len(self.filter_)
    for i in xrange(len(self.filter_)): n += self.lengthString(self.filter_[i].ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_operator_):
      n += 1
      n += self.lengthVarInt64(self.operator_)
    n += 1 * len(self.filter_)
    for i in xrange(len(self.filter_)): n += self.lengthString(self.filter_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_operator()
    self.clear_filter()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt32(self.operator_)
    for i in xrange(len(self.filter_)):
      out.putVarInt32(18)
      out.putVarInt32(self.filter_[i].ByteSize())
      self.filter_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_operator_):
      out.putVarInt32(8)
      out.putVarInt32(self.operator_)
    for i in xrange(len(self.filter_)):
      out.putVarInt32(18)
      out.putVarInt32(self.filter_[i].ByteSizePartial())
      self.filter_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_operator(d.getVarInt32())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_filter().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_operator_: res+=prefix+("operator: %s\n" % self.DebugFormatInt32(self.operator_))
    cnt=0
    for e in self.filter_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("filter%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  koperator = 1
  kfilter = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "operator",
    2: "filter",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.CompositeFilter'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KJ2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkNvbXBvc2l0ZUZpbHRlchMaCG9wZXJhdG9yIAEoADAFOAJoABQTGgZmaWx0ZXIgAigCMAs4A0oeYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRmlsdGVyowGqAQVjdHlwZbIBBnByb3RvMqQBFHN6CE9wZXJhdG9yiwGSAQNBTkSYAQGMAXTCAR1hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5FcnJvcg=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class PropertyFilter(ProtocolBuffer.ProtocolMessage):


  LESS_THAN    =    1
  LESS_THAN_OR_EQUAL =    2
  GREATER_THAN =    3
  GREATER_THAN_OR_EQUAL =    4
  EQUAL        =    5
  HAS_ANCESTOR =   11

  _Operator_NAMES = {
    1: "LESS_THAN",
    2: "LESS_THAN_OR_EQUAL",
    3: "GREATER_THAN",
    4: "GREATER_THAN_OR_EQUAL",
    5: "EQUAL",
    11: "HAS_ANCESTOR",
  }

  def Operator_Name(cls, x): return cls._Operator_NAMES.get(x, "")
  Operator_Name = classmethod(Operator_Name)

  has_property_ = 0
  has_operator_ = 0
  operator_ = 0
  has_value_ = 0

  def __init__(self, contents=None):
    self.property_ = PropertyReference()
    self.value_ = google.appengine.datastore.entity_v4_pb.Value()
    if contents is not None: self.MergeFromString(contents)

  def property(self): return self.property_

  def mutable_property(self): self.has_property_ = 1; return self.property_

  def clear_property(self):self.has_property_ = 0; self.property_.Clear()

  def has_property(self): return self.has_property_

  def operator(self): return self.operator_

  def set_operator(self, x):
    self.has_operator_ = 1
    self.operator_ = x

  def clear_operator(self):
    if self.has_operator_:
      self.has_operator_ = 0
      self.operator_ = 0

  def has_operator(self): return self.has_operator_

  def value(self): return self.value_

  def mutable_value(self): self.has_value_ = 1; return self.value_

  def clear_value(self):self.has_value_ = 0; self.value_.Clear()

  def has_value(self): return self.has_value_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_property()): self.mutable_property().MergeFrom(x.property())
    if (x.has_operator()): self.set_operator(x.operator())
    if (x.has_value()): self.mutable_value().MergeFrom(x.value())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.PropertyFilter', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.PropertyFilter')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.PropertyFilter')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.PropertyFilter', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.PropertyFilter', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.PropertyFilter', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_property_ != x.has_property_: return 0
    if self.has_property_ and self.property_ != x.property_: return 0
    if self.has_operator_ != x.has_operator_: return 0
    if self.has_operator_ and self.operator_ != x.operator_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_property_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: property not set.')
    elif not self.property_.IsInitialized(debug_strs): initialized = 0
    if (not self.has_operator_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: operator not set.')
    if (not self.has_value_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: value not set.')
    elif not self.value_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.property_.ByteSize())
    n += self.lengthVarInt64(self.operator_)
    n += self.lengthString(self.value_.ByteSize())
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_property_):
      n += 1
      n += self.lengthString(self.property_.ByteSizePartial())
    if (self.has_operator_):
      n += 1
      n += self.lengthVarInt64(self.operator_)
    if (self.has_value_):
      n += 1
      n += self.lengthString(self.value_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_property()
    self.clear_operator()
    self.clear_value()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.property_.ByteSize())
    self.property_.OutputUnchecked(out)
    out.putVarInt32(16)
    out.putVarInt32(self.operator_)
    out.putVarInt32(26)
    out.putVarInt32(self.value_.ByteSize())
    self.value_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_property_):
      out.putVarInt32(10)
      out.putVarInt32(self.property_.ByteSizePartial())
      self.property_.OutputPartial(out)
    if (self.has_operator_):
      out.putVarInt32(16)
      out.putVarInt32(self.operator_)
    if (self.has_value_):
      out.putVarInt32(26)
      out.putVarInt32(self.value_.ByteSizePartial())
      self.value_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_property().TryMerge(tmp)
        continue
      if tt == 16:
        self.set_operator(d.getVarInt32())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_value().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_property_:
      res+=prefix+"property <\n"
      res+=self.property_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_operator_: res+=prefix+("operator: %s\n" % self.DebugFormatInt32(self.operator_))
    if self.has_value_:
      res+=prefix+"value <\n"
      res+=self.value_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kproperty = 1
  koperator = 2
  kvalue = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "property",
    2: "operator",
    3: "value",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.PropertyFilter'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KJmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlByb3BlcnR5RmlsdGVyExoIcHJvcGVydHkgASgCMAs4AkopYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUHJvcGVydHlSZWZlcmVuY2WjAaoBBWN0eXBlsgEGcHJvdG8ypAEUExoIb3BlcmF0b3IgAigAMAU4AmgAFBMaBXZhbHVlIAMoAjALOAJKHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlZhbHVlowGqAQVjdHlwZbIBBnByb3RvMqQBFHN6CE9wZXJhdG9yiwGSAQlMRVNTX1RIQU6YAQGMAYsBkgESTEVTU19USEFOX09SX0VRVUFMmAECjAGLAZIBDEdSRUFURVJfVEhBTpgBA4wBiwGSARVHUkVBVEVSX1RIQU5fT1JfRVFVQUyYAQSMAYsBkgEFRVFVQUyYAQWMAYsBkgEMSEFTX0FOQ0VTVE9SmAELjAF0wgEdYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class GqlQuery(ProtocolBuffer.ProtocolMessage):
  has_query_string_ = 0
  query_string_ = ""
  has_allow_literal_ = 0
  allow_literal_ = 0

  def __init__(self, contents=None):
    self.name_arg_ = []
    self.number_arg_ = []
    if contents is not None: self.MergeFromString(contents)

  def query_string(self): return self.query_string_

  def set_query_string(self, x):
    self.has_query_string_ = 1
    self.query_string_ = x

  def clear_query_string(self):
    if self.has_query_string_:
      self.has_query_string_ = 0
      self.query_string_ = ""

  def has_query_string(self): return self.has_query_string_

  def allow_literal(self): return self.allow_literal_

  def set_allow_literal(self, x):
    self.has_allow_literal_ = 1
    self.allow_literal_ = x

  def clear_allow_literal(self):
    if self.has_allow_literal_:
      self.has_allow_literal_ = 0
      self.allow_literal_ = 0

  def has_allow_literal(self): return self.has_allow_literal_

  def name_arg_size(self): return len(self.name_arg_)
  def name_arg_list(self): return self.name_arg_

  def name_arg(self, i):
    return self.name_arg_[i]

  def mutable_name_arg(self, i):
    return self.name_arg_[i]

  def add_name_arg(self):
    x = GqlQueryArg()
    self.name_arg_.append(x)
    return x

  def clear_name_arg(self):
    self.name_arg_ = []
  def number_arg_size(self): return len(self.number_arg_)
  def number_arg_list(self): return self.number_arg_

  def number_arg(self, i):
    return self.number_arg_[i]

  def mutable_number_arg(self, i):
    return self.number_arg_[i]

  def add_number_arg(self):
    x = GqlQueryArg()
    self.number_arg_.append(x)
    return x

  def clear_number_arg(self):
    self.number_arg_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_query_string()): self.set_query_string(x.query_string())
    if (x.has_allow_literal()): self.set_allow_literal(x.allow_literal())
    for i in xrange(x.name_arg_size()): self.add_name_arg().CopyFrom(x.name_arg(i))
    for i in xrange(x.number_arg_size()): self.add_number_arg().CopyFrom(x.number_arg(i))

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.GqlQuery', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.GqlQuery')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.GqlQuery')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.GqlQuery', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.GqlQuery', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.GqlQuery', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_query_string_ != x.has_query_string_: return 0
    if self.has_query_string_ and self.query_string_ != x.query_string_: return 0
    if self.has_allow_literal_ != x.has_allow_literal_: return 0
    if self.has_allow_literal_ and self.allow_literal_ != x.allow_literal_: return 0
    if len(self.name_arg_) != len(x.name_arg_): return 0
    for e1, e2 in zip(self.name_arg_, x.name_arg_):
      if e1 != e2: return 0
    if len(self.number_arg_) != len(x.number_arg_): return 0
    for e1, e2 in zip(self.number_arg_, x.number_arg_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_query_string_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: query_string not set.')
    for p in self.name_arg_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.number_arg_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.query_string_))
    if (self.has_allow_literal_): n += 2
    n += 1 * len(self.name_arg_)
    for i in xrange(len(self.name_arg_)): n += self.lengthString(self.name_arg_[i].ByteSize())
    n += 1 * len(self.number_arg_)
    for i in xrange(len(self.number_arg_)): n += self.lengthString(self.number_arg_[i].ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_query_string_):
      n += 1
      n += self.lengthString(len(self.query_string_))
    if (self.has_allow_literal_): n += 2
    n += 1 * len(self.name_arg_)
    for i in xrange(len(self.name_arg_)): n += self.lengthString(self.name_arg_[i].ByteSizePartial())
    n += 1 * len(self.number_arg_)
    for i in xrange(len(self.number_arg_)): n += self.lengthString(self.number_arg_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_query_string()
    self.clear_allow_literal()
    self.clear_name_arg()
    self.clear_number_arg()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.query_string_)
    if (self.has_allow_literal_):
      out.putVarInt32(16)
      out.putBoolean(self.allow_literal_)
    for i in xrange(len(self.name_arg_)):
      out.putVarInt32(26)
      out.putVarInt32(self.name_arg_[i].ByteSize())
      self.name_arg_[i].OutputUnchecked(out)
    for i in xrange(len(self.number_arg_)):
      out.putVarInt32(34)
      out.putVarInt32(self.number_arg_[i].ByteSize())
      self.number_arg_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_query_string_):
      out.putVarInt32(10)
      out.putPrefixedString(self.query_string_)
    if (self.has_allow_literal_):
      out.putVarInt32(16)
      out.putBoolean(self.allow_literal_)
    for i in xrange(len(self.name_arg_)):
      out.putVarInt32(26)
      out.putVarInt32(self.name_arg_[i].ByteSizePartial())
      self.name_arg_[i].OutputPartial(out)
    for i in xrange(len(self.number_arg_)):
      out.putVarInt32(34)
      out.putVarInt32(self.number_arg_[i].ByteSizePartial())
      self.number_arg_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_query_string(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_allow_literal(d.getBoolean())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_name_arg().TryMerge(tmp)
        continue
      if tt == 34:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_number_arg().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_query_string_: res+=prefix+("query_string: %s\n" % self.DebugFormatString(self.query_string_))
    if self.has_allow_literal_: res+=prefix+("allow_literal: %s\n" % self.DebugFormatBool(self.allow_literal_))
    cnt=0
    for e in self.name_arg_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("name_arg%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.number_arg_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("number_arg%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kquery_string = 1
  kallow_literal = 2
  kname_arg = 3
  knumber_arg = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "query_string",
    2: "allow_literal",
    3: "name_arg",
    4: "number_arg",
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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.GqlQuery'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KIGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkdxbFF1ZXJ5ExoMcXVlcnlfc3RyaW5nIAEoAjAJOAIUExoNYWxsb3dfbGl0ZXJhbCACKAAwCDgBQgVmYWxzZaMBqgEHZGVmYXVsdLIBBWZhbHNlpAEUExoIbmFtZV9hcmcgAygCMAs4A0ojYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuR3FsUXVlcnlBcmejAaoBBWN0eXBlsgEGcHJvdG8ypAEUExoKbnVtYmVyX2FyZyAEKAIwCzgDSiNhcHBob3N0aW5nLmRhdGFzdG9yZS52NC5HcWxRdWVyeUFyZ6MBqgEFY3R5cGWyAQZwcm90bzKkARTCAR1hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5FcnJvcg=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class GqlQueryArg(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""
  has_value_ = 0
  value_ = None
  has_cursor_ = 0
  cursor_ = ""

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

  def value(self):
    if self.value_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.value_ is None: self.value_ = google.appengine.datastore.entity_v4_pb.Value()
      finally:
        self.lazy_init_lock_.release()
    return self.value_

  def mutable_value(self): self.has_value_ = 1; return self.value()

  def clear_value(self):

    if self.has_value_:
      self.has_value_ = 0;
      if self.value_ is not None: self.value_.Clear()

  def has_value(self): return self.has_value_

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
    if (x.has_name()): self.set_name(x.name())
    if (x.has_value()): self.mutable_value().MergeFrom(x.value())
    if (x.has_cursor()): self.set_cursor(x.cursor())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.GqlQueryArg', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.GqlQueryArg')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.GqlQueryArg')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.GqlQueryArg', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.GqlQueryArg', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.GqlQueryArg', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    if self.has_cursor_ != x.has_cursor_: return 0
    if self.has_cursor_ and self.cursor_ != x.cursor_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_value_ and not self.value_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_name_): n += 1 + self.lengthString(len(self.name_))
    if (self.has_value_): n += 1 + self.lengthString(self.value_.ByteSize())
    if (self.has_cursor_): n += 1 + self.lengthString(len(self.cursor_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_): n += 1 + self.lengthString(len(self.name_))
    if (self.has_value_): n += 1 + self.lengthString(self.value_.ByteSizePartial())
    if (self.has_cursor_): n += 1 + self.lengthString(len(self.cursor_))
    return n

  def Clear(self):
    self.clear_name()
    self.clear_value()
    self.clear_cursor()

  def OutputUnchecked(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    if (self.has_value_):
      out.putVarInt32(18)
      out.putVarInt32(self.value_.ByteSize())
      self.value_.OutputUnchecked(out)
    if (self.has_cursor_):
      out.putVarInt32(26)
      out.putPrefixedString(self.cursor_)

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    if (self.has_value_):
      out.putVarInt32(18)
      out.putVarInt32(self.value_.ByteSizePartial())
      self.value_.OutputPartial(out)
    if (self.has_cursor_):
      out.putVarInt32(26)
      out.putPrefixedString(self.cursor_)

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
        self.mutable_value().TryMerge(tmp)
        continue
      if tt == 26:
        self.set_cursor(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    if self.has_value_:
      res+=prefix+"value <\n"
      res+=self.value_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_cursor_: res+=prefix+("cursor: %s\n" % self.DebugFormatString(self.cursor_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 1
  kvalue = 2
  kcursor = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name",
    2: "value",
    3: "cursor",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.GqlQueryArg'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KI2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkdxbFF1ZXJ5QXJnExoEbmFtZSABKAIwCTgBFBMaBXZhbHVlIAIoAjALOAFKHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlZhbHVlowGqAQVjdHlwZbIBBnByb3RvMqQBFBMaBmN1cnNvciADKAIwCTgBFMIBHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVycm9y"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class QueryResultBatch(ProtocolBuffer.ProtocolMessage):


  NOT_FINISHED =    1
  MORE_RESULTS_AFTER_LIMIT =    2
  NO_MORE_RESULTS =    3

  _MoreResultsType_NAMES = {
    1: "NOT_FINISHED",
    2: "MORE_RESULTS_AFTER_LIMIT",
    3: "NO_MORE_RESULTS",
  }

  def MoreResultsType_Name(cls, x): return cls._MoreResultsType_NAMES.get(x, "")
  MoreResultsType_Name = classmethod(MoreResultsType_Name)

  has_entity_result_type_ = 0
  entity_result_type_ = 0
  has_skipped_cursor_ = 0
  skipped_cursor_ = ""
  has_end_cursor_ = 0
  end_cursor_ = ""
  has_more_results_ = 0
  more_results_ = 0
  has_skipped_results_ = 0
  skipped_results_ = 0
  has_snapshot_version_ = 0
  snapshot_version_ = 0

  def __init__(self, contents=None):
    self.entity_result_ = []
    if contents is not None: self.MergeFromString(contents)

  def entity_result_type(self): return self.entity_result_type_

  def set_entity_result_type(self, x):
    self.has_entity_result_type_ = 1
    self.entity_result_type_ = x

  def clear_entity_result_type(self):
    if self.has_entity_result_type_:
      self.has_entity_result_type_ = 0
      self.entity_result_type_ = 0

  def has_entity_result_type(self): return self.has_entity_result_type_

  def entity_result_size(self): return len(self.entity_result_)
  def entity_result_list(self): return self.entity_result_

  def entity_result(self, i):
    return self.entity_result_[i]

  def mutable_entity_result(self, i):
    return self.entity_result_[i]

  def add_entity_result(self):
    x = EntityResult()
    self.entity_result_.append(x)
    return x

  def clear_entity_result(self):
    self.entity_result_ = []
  def skipped_cursor(self): return self.skipped_cursor_

  def set_skipped_cursor(self, x):
    self.has_skipped_cursor_ = 1
    self.skipped_cursor_ = x

  def clear_skipped_cursor(self):
    if self.has_skipped_cursor_:
      self.has_skipped_cursor_ = 0
      self.skipped_cursor_ = ""

  def has_skipped_cursor(self): return self.has_skipped_cursor_

  def end_cursor(self): return self.end_cursor_

  def set_end_cursor(self, x):
    self.has_end_cursor_ = 1
    self.end_cursor_ = x

  def clear_end_cursor(self):
    if self.has_end_cursor_:
      self.has_end_cursor_ = 0
      self.end_cursor_ = ""

  def has_end_cursor(self): return self.has_end_cursor_

  def more_results(self): return self.more_results_

  def set_more_results(self, x):
    self.has_more_results_ = 1
    self.more_results_ = x

  def clear_more_results(self):
    if self.has_more_results_:
      self.has_more_results_ = 0
      self.more_results_ = 0

  def has_more_results(self): return self.has_more_results_

  def skipped_results(self): return self.skipped_results_

  def set_skipped_results(self, x):
    self.has_skipped_results_ = 1
    self.skipped_results_ = x

  def clear_skipped_results(self):
    if self.has_skipped_results_:
      self.has_skipped_results_ = 0
      self.skipped_results_ = 0

  def has_skipped_results(self): return self.has_skipped_results_

  def snapshot_version(self): return self.snapshot_version_

  def set_snapshot_version(self, x):
    self.has_snapshot_version_ = 1
    self.snapshot_version_ = x

  def clear_snapshot_version(self):
    if self.has_snapshot_version_:
      self.has_snapshot_version_ = 0
      self.snapshot_version_ = 0

  def has_snapshot_version(self): return self.has_snapshot_version_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_entity_result_type()): self.set_entity_result_type(x.entity_result_type())
    for i in xrange(x.entity_result_size()): self.add_entity_result().CopyFrom(x.entity_result(i))
    if (x.has_skipped_cursor()): self.set_skipped_cursor(x.skipped_cursor())
    if (x.has_end_cursor()): self.set_end_cursor(x.end_cursor())
    if (x.has_more_results()): self.set_more_results(x.more_results())
    if (x.has_skipped_results()): self.set_skipped_results(x.skipped_results())
    if (x.has_snapshot_version()): self.set_snapshot_version(x.snapshot_version())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.QueryResultBatch', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.QueryResultBatch')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.QueryResultBatch')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.QueryResultBatch', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.QueryResultBatch', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.QueryResultBatch', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_entity_result_type_ != x.has_entity_result_type_: return 0
    if self.has_entity_result_type_ and self.entity_result_type_ != x.entity_result_type_: return 0
    if len(self.entity_result_) != len(x.entity_result_): return 0
    for e1, e2 in zip(self.entity_result_, x.entity_result_):
      if e1 != e2: return 0
    if self.has_skipped_cursor_ != x.has_skipped_cursor_: return 0
    if self.has_skipped_cursor_ and self.skipped_cursor_ != x.skipped_cursor_: return 0
    if self.has_end_cursor_ != x.has_end_cursor_: return 0
    if self.has_end_cursor_ and self.end_cursor_ != x.end_cursor_: return 0
    if self.has_more_results_ != x.has_more_results_: return 0
    if self.has_more_results_ and self.more_results_ != x.more_results_: return 0
    if self.has_skipped_results_ != x.has_skipped_results_: return 0
    if self.has_skipped_results_ and self.skipped_results_ != x.skipped_results_: return 0
    if self.has_snapshot_version_ != x.has_snapshot_version_: return 0
    if self.has_snapshot_version_ and self.snapshot_version_ != x.snapshot_version_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_entity_result_type_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: entity_result_type not set.')
    for p in self.entity_result_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (not self.has_more_results_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: more_results not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.entity_result_type_)
    n += 1 * len(self.entity_result_)
    for i in xrange(len(self.entity_result_)): n += self.lengthString(self.entity_result_[i].ByteSize())
    if (self.has_skipped_cursor_): n += 1 + self.lengthString(len(self.skipped_cursor_))
    if (self.has_end_cursor_): n += 1 + self.lengthString(len(self.end_cursor_))
    n += self.lengthVarInt64(self.more_results_)
    if (self.has_skipped_results_): n += 1 + self.lengthVarInt64(self.skipped_results_)
    if (self.has_snapshot_version_): n += 1 + self.lengthVarInt64(self.snapshot_version_)
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_entity_result_type_):
      n += 1
      n += self.lengthVarInt64(self.entity_result_type_)
    n += 1 * len(self.entity_result_)
    for i in xrange(len(self.entity_result_)): n += self.lengthString(self.entity_result_[i].ByteSizePartial())
    if (self.has_skipped_cursor_): n += 1 + self.lengthString(len(self.skipped_cursor_))
    if (self.has_end_cursor_): n += 1 + self.lengthString(len(self.end_cursor_))
    if (self.has_more_results_):
      n += 1
      n += self.lengthVarInt64(self.more_results_)
    if (self.has_skipped_results_): n += 1 + self.lengthVarInt64(self.skipped_results_)
    if (self.has_snapshot_version_): n += 1 + self.lengthVarInt64(self.snapshot_version_)
    return n

  def Clear(self):
    self.clear_entity_result_type()
    self.clear_entity_result()
    self.clear_skipped_cursor()
    self.clear_end_cursor()
    self.clear_more_results()
    self.clear_skipped_results()
    self.clear_snapshot_version()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt32(self.entity_result_type_)
    for i in xrange(len(self.entity_result_)):
      out.putVarInt32(18)
      out.putVarInt32(self.entity_result_[i].ByteSize())
      self.entity_result_[i].OutputUnchecked(out)
    if (self.has_skipped_cursor_):
      out.putVarInt32(26)
      out.putPrefixedString(self.skipped_cursor_)
    if (self.has_end_cursor_):
      out.putVarInt32(34)
      out.putPrefixedString(self.end_cursor_)
    out.putVarInt32(40)
    out.putVarInt32(self.more_results_)
    if (self.has_skipped_results_):
      out.putVarInt32(48)
      out.putVarInt32(self.skipped_results_)
    if (self.has_snapshot_version_):
      out.putVarInt32(56)
      out.putVarInt64(self.snapshot_version_)

  def OutputPartial(self, out):
    if (self.has_entity_result_type_):
      out.putVarInt32(8)
      out.putVarInt32(self.entity_result_type_)
    for i in xrange(len(self.entity_result_)):
      out.putVarInt32(18)
      out.putVarInt32(self.entity_result_[i].ByteSizePartial())
      self.entity_result_[i].OutputPartial(out)
    if (self.has_skipped_cursor_):
      out.putVarInt32(26)
      out.putPrefixedString(self.skipped_cursor_)
    if (self.has_end_cursor_):
      out.putVarInt32(34)
      out.putPrefixedString(self.end_cursor_)
    if (self.has_more_results_):
      out.putVarInt32(40)
      out.putVarInt32(self.more_results_)
    if (self.has_skipped_results_):
      out.putVarInt32(48)
      out.putVarInt32(self.skipped_results_)
    if (self.has_snapshot_version_):
      out.putVarInt32(56)
      out.putVarInt64(self.snapshot_version_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_entity_result_type(d.getVarInt32())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_entity_result().TryMerge(tmp)
        continue
      if tt == 26:
        self.set_skipped_cursor(d.getPrefixedString())
        continue
      if tt == 34:
        self.set_end_cursor(d.getPrefixedString())
        continue
      if tt == 40:
        self.set_more_results(d.getVarInt32())
        continue
      if tt == 48:
        self.set_skipped_results(d.getVarInt32())
        continue
      if tt == 56:
        self.set_snapshot_version(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_entity_result_type_: res+=prefix+("entity_result_type: %s\n" % self.DebugFormatInt32(self.entity_result_type_))
    cnt=0
    for e in self.entity_result_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("entity_result%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_skipped_cursor_: res+=prefix+("skipped_cursor: %s\n" % self.DebugFormatString(self.skipped_cursor_))
    if self.has_end_cursor_: res+=prefix+("end_cursor: %s\n" % self.DebugFormatString(self.end_cursor_))
    if self.has_more_results_: res+=prefix+("more_results: %s\n" % self.DebugFormatInt32(self.more_results_))
    if self.has_skipped_results_: res+=prefix+("skipped_results: %s\n" % self.DebugFormatInt32(self.skipped_results_))
    if self.has_snapshot_version_: res+=prefix+("snapshot_version: %s\n" % self.DebugFormatInt64(self.snapshot_version_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kentity_result_type = 1
  kentity_result = 2
  kskipped_cursor = 3
  kend_cursor = 4
  kmore_results = 5
  kskipped_results = 6
  ksnapshot_version = 7

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "entity_result_type",
    2: "entity_result",
    3: "skipped_cursor",
    4: "end_cursor",
    5: "more_results",
    6: "skipped_results",
    7: "snapshot_version",
  }, 7)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.NUMERIC,
    7: ProtocolBuffer.Encoder.NUMERIC,
  }, 7, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.QueryResultBatch'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KKGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlF1ZXJ5UmVzdWx0QmF0Y2gTGhJlbnRpdHlfcmVzdWx0X3R5cGUgASgAMAU4AhQTGg1lbnRpdHlfcmVzdWx0IAIoAjALOANKJGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVudGl0eVJlc3VsdKMBqgEFY3R5cGWyAQZwcm90bzKkARQTGg5za2lwcGVkX2N1cnNvciADKAIwCTgBFBMaCmVuZF9jdXJzb3IgBCgCMAk4ARQTGgxtb3JlX3Jlc3VsdHMgBSgAMAU4AmgAFBMaD3NraXBwZWRfcmVzdWx0cyAGKAAwBTgBQgEwowGqAQdkZWZhdWx0sgEBMKQBFBMaEHNuYXBzaG90X3ZlcnNpb24gBygAMAM4ARRzeg9Nb3JlUmVzdWx0c1R5cGWLAZIBDE5PVF9GSU5JU0hFRJgBAYwBiwGSARhNT1JFX1JFU1VMVFNfQUZURVJfTElNSVSYAQKMAYsBkgEPTk9fTU9SRV9SRVNVTFRTmAEDjAF0wgEdYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class Mutation(ProtocolBuffer.ProtocolMessage):


  UNKNOWN      =    0
  INSERT       =    1
  UPDATE       =    2
  UPSERT       =    3
  DELETE       =    4

  _Operation_NAMES = {
    0: "UNKNOWN",
    1: "INSERT",
    2: "UPDATE",
    3: "UPSERT",
    4: "DELETE",
  }

  def Operation_Name(cls, x): return cls._Operation_NAMES.get(x, "")
  Operation_Name = classmethod(Operation_Name)

  has_op_ = 0
  op_ = 0
  has_key_ = 0
  key_ = None
  has_entity_ = 0
  entity_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def op(self): return self.op_

  def set_op(self, x):
    self.has_op_ = 1
    self.op_ = x

  def clear_op(self):
    if self.has_op_:
      self.has_op_ = 0
      self.op_ = 0

  def has_op(self): return self.has_op_

  def key(self):
    if self.key_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.key_ is None: self.key_ = google.appengine.datastore.entity_v4_pb.Key()
      finally:
        self.lazy_init_lock_.release()
    return self.key_

  def mutable_key(self): self.has_key_ = 1; return self.key()

  def clear_key(self):

    if self.has_key_:
      self.has_key_ = 0;
      if self.key_ is not None: self.key_.Clear()

  def has_key(self): return self.has_key_

  def entity(self):
    if self.entity_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.entity_ is None: self.entity_ = google.appengine.datastore.entity_v4_pb.Entity()
      finally:
        self.lazy_init_lock_.release()
    return self.entity_

  def mutable_entity(self): self.has_entity_ = 1; return self.entity()

  def clear_entity(self):

    if self.has_entity_:
      self.has_entity_ = 0;
      if self.entity_ is not None: self.entity_.Clear()

  def has_entity(self): return self.has_entity_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_op()): self.set_op(x.op())
    if (x.has_key()): self.mutable_key().MergeFrom(x.key())
    if (x.has_entity()): self.mutable_entity().MergeFrom(x.entity())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.Mutation', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.Mutation')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.Mutation')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.Mutation', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.Mutation', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.Mutation', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_op_ != x.has_op_: return 0
    if self.has_op_ and self.op_ != x.op_: return 0
    if self.has_key_ != x.has_key_: return 0
    if self.has_key_ and self.key_ != x.key_: return 0
    if self.has_entity_ != x.has_entity_: return 0
    if self.has_entity_ and self.entity_ != x.entity_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_key_ and not self.key_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_entity_ and not self.entity_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_op_): n += 1 + self.lengthVarInt64(self.op_)
    if (self.has_key_): n += 1 + self.lengthString(self.key_.ByteSize())
    if (self.has_entity_): n += 1 + self.lengthString(self.entity_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_op_): n += 1 + self.lengthVarInt64(self.op_)
    if (self.has_key_): n += 1 + self.lengthString(self.key_.ByteSizePartial())
    if (self.has_entity_): n += 1 + self.lengthString(self.entity_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_op()
    self.clear_key()
    self.clear_entity()

  def OutputUnchecked(self, out):
    if (self.has_op_):
      out.putVarInt32(8)
      out.putVarInt32(self.op_)
    if (self.has_key_):
      out.putVarInt32(18)
      out.putVarInt32(self.key_.ByteSize())
      self.key_.OutputUnchecked(out)
    if (self.has_entity_):
      out.putVarInt32(26)
      out.putVarInt32(self.entity_.ByteSize())
      self.entity_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_op_):
      out.putVarInt32(8)
      out.putVarInt32(self.op_)
    if (self.has_key_):
      out.putVarInt32(18)
      out.putVarInt32(self.key_.ByteSizePartial())
      self.key_.OutputPartial(out)
    if (self.has_entity_):
      out.putVarInt32(26)
      out.putVarInt32(self.entity_.ByteSizePartial())
      self.entity_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_op(d.getVarInt32())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_key().TryMerge(tmp)
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_entity().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_op_: res+=prefix+("op: %s\n" % self.DebugFormatInt32(self.op_))
    if self.has_key_:
      res+=prefix+"key <\n"
      res+=self.key_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_entity_:
      res+=prefix+"entity <\n"
      res+=self.entity_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kop = 1
  kkey = 2
  kentity = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "op",
    2: "key",
    3: "entity",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.Mutation'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KIGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0Lk11dGF0aW9uExoCb3AgASgAMAU4AUIBMGgAowGqAQdkZWZhdWx0sgEHVU5LTk9XTqQBFBMaA2tleSACKAIwCzgBShthcHBob3N0aW5nLmRhdGFzdG9yZS52NC5LZXmjAaoBBWN0eXBlsgEGcHJvdG8ypAEUExoGZW50aXR5IAMoAjALOAFKHmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVudGl0eaMBqgEFY3R5cGWyAQZwcm90bzKkARRzeglPcGVyYXRpb26LAZIBB1VOS05PV06YAQCMAYsBkgEGSU5TRVJUmAEBjAGLAZIBBlVQREFURZgBAowBiwGSAQZVUFNFUlSYAQOMAYsBkgEGREVMRVRFmAEEjAF0wgEdYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class MutationResult(ProtocolBuffer.ProtocolMessage):
  has_key_ = 0
  key_ = None
  has_new_version_ = 0
  new_version_ = 0

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def key(self):
    if self.key_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.key_ is None: self.key_ = google.appengine.datastore.entity_v4_pb.Key()
      finally:
        self.lazy_init_lock_.release()
    return self.key_

  def mutable_key(self): self.has_key_ = 1; return self.key()

  def clear_key(self):

    if self.has_key_:
      self.has_key_ = 0;
      if self.key_ is not None: self.key_.Clear()

  def has_key(self): return self.has_key_

  def new_version(self): return self.new_version_

  def set_new_version(self, x):
    self.has_new_version_ = 1
    self.new_version_ = x

  def clear_new_version(self):
    if self.has_new_version_:
      self.has_new_version_ = 0
      self.new_version_ = 0

  def has_new_version(self): return self.has_new_version_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_key()): self.mutable_key().MergeFrom(x.key())
    if (x.has_new_version()): self.set_new_version(x.new_version())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.MutationResult', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.MutationResult')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.MutationResult')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.MutationResult', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.MutationResult', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.MutationResult', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_key_ != x.has_key_: return 0
    if self.has_key_ and self.key_ != x.key_: return 0
    if self.has_new_version_ != x.has_new_version_: return 0
    if self.has_new_version_ and self.new_version_ != x.new_version_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_key_ and not self.key_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_key_): n += 1 + self.lengthString(self.key_.ByteSize())
    if (self.has_new_version_): n += 1 + self.lengthVarInt64(self.new_version_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_key_): n += 1 + self.lengthString(self.key_.ByteSizePartial())
    if (self.has_new_version_): n += 1 + self.lengthVarInt64(self.new_version_)
    return n

  def Clear(self):
    self.clear_key()
    self.clear_new_version()

  def OutputUnchecked(self, out):
    if (self.has_key_):
      out.putVarInt32(26)
      out.putVarInt32(self.key_.ByteSize())
      self.key_.OutputUnchecked(out)
    if (self.has_new_version_):
      out.putVarInt32(32)
      out.putVarInt64(self.new_version_)

  def OutputPartial(self, out):
    if (self.has_key_):
      out.putVarInt32(26)
      out.putVarInt32(self.key_.ByteSizePartial())
      self.key_.OutputPartial(out)
    if (self.has_new_version_):
      out.putVarInt32(32)
      out.putVarInt64(self.new_version_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_key().TryMerge(tmp)
        continue
      if tt == 32:
        self.set_new_version(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_key_:
      res+=prefix+"key <\n"
      res+=self.key_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_new_version_: res+=prefix+("new_version: %s\n" % self.DebugFormatInt64(self.new_version_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kkey = 3
  knew_version = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    3: "key",
    4: "new_version",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.MutationResult'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KJmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0Lk11dGF0aW9uUmVzdWx0ExoDa2V5IAMoAjALOAFKG2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktleaMBqgEFY3R5cGWyAQZwcm90bzKkARQTGgtuZXdfdmVyc2lvbiAEKAAwAzgBQgEwowGqAQdkZWZhdWx0sgEBMKQBFMIBHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVycm9y"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class DeprecatedMutation(ProtocolBuffer.ProtocolMessage):
  has_force_ = 0
  force_ = 0

  def __init__(self, contents=None):
    self.upsert_ = []
    self.update_ = []
    self.insert_ = []
    self.insert_auto_id_ = []
    self.delete_ = []
    if contents is not None: self.MergeFromString(contents)

  def upsert_size(self): return len(self.upsert_)
  def upsert_list(self): return self.upsert_

  def upsert(self, i):
    return self.upsert_[i]

  def mutable_upsert(self, i):
    return self.upsert_[i]

  def add_upsert(self):
    x = google.appengine.datastore.entity_v4_pb.Entity()
    self.upsert_.append(x)
    return x

  def clear_upsert(self):
    self.upsert_ = []
  def update_size(self): return len(self.update_)
  def update_list(self): return self.update_

  def update(self, i):
    return self.update_[i]

  def mutable_update(self, i):
    return self.update_[i]

  def add_update(self):
    x = google.appengine.datastore.entity_v4_pb.Entity()
    self.update_.append(x)
    return x

  def clear_update(self):
    self.update_ = []
  def insert_size(self): return len(self.insert_)
  def insert_list(self): return self.insert_

  def insert(self, i):
    return self.insert_[i]

  def mutable_insert(self, i):
    return self.insert_[i]

  def add_insert(self):
    x = google.appengine.datastore.entity_v4_pb.Entity()
    self.insert_.append(x)
    return x

  def clear_insert(self):
    self.insert_ = []
  def insert_auto_id_size(self): return len(self.insert_auto_id_)
  def insert_auto_id_list(self): return self.insert_auto_id_

  def insert_auto_id(self, i):
    return self.insert_auto_id_[i]

  def mutable_insert_auto_id(self, i):
    return self.insert_auto_id_[i]

  def add_insert_auto_id(self):
    x = google.appengine.datastore.entity_v4_pb.Entity()
    self.insert_auto_id_.append(x)
    return x

  def clear_insert_auto_id(self):
    self.insert_auto_id_ = []
  def delete_size(self): return len(self.delete_)
  def delete_list(self): return self.delete_

  def delete(self, i):
    return self.delete_[i]

  def mutable_delete(self, i):
    return self.delete_[i]

  def add_delete(self):
    x = google.appengine.datastore.entity_v4_pb.Key()
    self.delete_.append(x)
    return x

  def clear_delete(self):
    self.delete_ = []
  def force(self): return self.force_

  def set_force(self, x):
    self.has_force_ = 1
    self.force_ = x

  def clear_force(self):
    if self.has_force_:
      self.has_force_ = 0
      self.force_ = 0

  def has_force(self): return self.has_force_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.upsert_size()): self.add_upsert().CopyFrom(x.upsert(i))
    for i in xrange(x.update_size()): self.add_update().CopyFrom(x.update(i))
    for i in xrange(x.insert_size()): self.add_insert().CopyFrom(x.insert(i))
    for i in xrange(x.insert_auto_id_size()): self.add_insert_auto_id().CopyFrom(x.insert_auto_id(i))
    for i in xrange(x.delete_size()): self.add_delete().CopyFrom(x.delete(i))
    if (x.has_force()): self.set_force(x.force())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.DeprecatedMutation', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.DeprecatedMutation')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.DeprecatedMutation')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.DeprecatedMutation', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.DeprecatedMutation', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.DeprecatedMutation', s)


  def Equals(self, x):
    if x is self: return 1
    if len(self.upsert_) != len(x.upsert_): return 0
    for e1, e2 in zip(self.upsert_, x.upsert_):
      if e1 != e2: return 0
    if len(self.update_) != len(x.update_): return 0
    for e1, e2 in zip(self.update_, x.update_):
      if e1 != e2: return 0
    if len(self.insert_) != len(x.insert_): return 0
    for e1, e2 in zip(self.insert_, x.insert_):
      if e1 != e2: return 0
    if len(self.insert_auto_id_) != len(x.insert_auto_id_): return 0
    for e1, e2 in zip(self.insert_auto_id_, x.insert_auto_id_):
      if e1 != e2: return 0
    if len(self.delete_) != len(x.delete_): return 0
    for e1, e2 in zip(self.delete_, x.delete_):
      if e1 != e2: return 0
    if self.has_force_ != x.has_force_: return 0
    if self.has_force_ and self.force_ != x.force_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.upsert_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.update_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.insert_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.insert_auto_id_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.delete_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.upsert_)
    for i in xrange(len(self.upsert_)): n += self.lengthString(self.upsert_[i].ByteSize())
    n += 1 * len(self.update_)
    for i in xrange(len(self.update_)): n += self.lengthString(self.update_[i].ByteSize())
    n += 1 * len(self.insert_)
    for i in xrange(len(self.insert_)): n += self.lengthString(self.insert_[i].ByteSize())
    n += 1 * len(self.insert_auto_id_)
    for i in xrange(len(self.insert_auto_id_)): n += self.lengthString(self.insert_auto_id_[i].ByteSize())
    n += 1 * len(self.delete_)
    for i in xrange(len(self.delete_)): n += self.lengthString(self.delete_[i].ByteSize())
    if (self.has_force_): n += 2
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.upsert_)
    for i in xrange(len(self.upsert_)): n += self.lengthString(self.upsert_[i].ByteSizePartial())
    n += 1 * len(self.update_)
    for i in xrange(len(self.update_)): n += self.lengthString(self.update_[i].ByteSizePartial())
    n += 1 * len(self.insert_)
    for i in xrange(len(self.insert_)): n += self.lengthString(self.insert_[i].ByteSizePartial())
    n += 1 * len(self.insert_auto_id_)
    for i in xrange(len(self.insert_auto_id_)): n += self.lengthString(self.insert_auto_id_[i].ByteSizePartial())
    n += 1 * len(self.delete_)
    for i in xrange(len(self.delete_)): n += self.lengthString(self.delete_[i].ByteSizePartial())
    if (self.has_force_): n += 2
    return n

  def Clear(self):
    self.clear_upsert()
    self.clear_update()
    self.clear_insert()
    self.clear_insert_auto_id()
    self.clear_delete()
    self.clear_force()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.upsert_)):
      out.putVarInt32(10)
      out.putVarInt32(self.upsert_[i].ByteSize())
      self.upsert_[i].OutputUnchecked(out)
    for i in xrange(len(self.update_)):
      out.putVarInt32(18)
      out.putVarInt32(self.update_[i].ByteSize())
      self.update_[i].OutputUnchecked(out)
    for i in xrange(len(self.insert_)):
      out.putVarInt32(26)
      out.putVarInt32(self.insert_[i].ByteSize())
      self.insert_[i].OutputUnchecked(out)
    for i in xrange(len(self.insert_auto_id_)):
      out.putVarInt32(34)
      out.putVarInt32(self.insert_auto_id_[i].ByteSize())
      self.insert_auto_id_[i].OutputUnchecked(out)
    for i in xrange(len(self.delete_)):
      out.putVarInt32(42)
      out.putVarInt32(self.delete_[i].ByteSize())
      self.delete_[i].OutputUnchecked(out)
    if (self.has_force_):
      out.putVarInt32(48)
      out.putBoolean(self.force_)

  def OutputPartial(self, out):
    for i in xrange(len(self.upsert_)):
      out.putVarInt32(10)
      out.putVarInt32(self.upsert_[i].ByteSizePartial())
      self.upsert_[i].OutputPartial(out)
    for i in xrange(len(self.update_)):
      out.putVarInt32(18)
      out.putVarInt32(self.update_[i].ByteSizePartial())
      self.update_[i].OutputPartial(out)
    for i in xrange(len(self.insert_)):
      out.putVarInt32(26)
      out.putVarInt32(self.insert_[i].ByteSizePartial())
      self.insert_[i].OutputPartial(out)
    for i in xrange(len(self.insert_auto_id_)):
      out.putVarInt32(34)
      out.putVarInt32(self.insert_auto_id_[i].ByteSizePartial())
      self.insert_auto_id_[i].OutputPartial(out)
    for i in xrange(len(self.delete_)):
      out.putVarInt32(42)
      out.putVarInt32(self.delete_[i].ByteSizePartial())
      self.delete_[i].OutputPartial(out)
    if (self.has_force_):
      out.putVarInt32(48)
      out.putBoolean(self.force_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_upsert().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_update().TryMerge(tmp)
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_insert().TryMerge(tmp)
        continue
      if tt == 34:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_insert_auto_id().TryMerge(tmp)
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_delete().TryMerge(tmp)
        continue
      if tt == 48:
        self.set_force(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.upsert_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("upsert%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.update_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("update%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.insert_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("insert%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.insert_auto_id_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("insert_auto_id%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.delete_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("delete%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_force_: res+=prefix+("force: %s\n" % self.DebugFormatBool(self.force_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kupsert = 1
  kupdate = 2
  kinsert = 3
  kinsert_auto_id = 4
  kdelete = 5
  kforce = 6

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "upsert",
    2: "update",
    3: "insert",
    4: "insert_auto_id",
    5: "delete",
    6: "force",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.NUMERIC,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.DeprecatedMutation'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KKmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkRlcHJlY2F0ZWRNdXRhdGlvbhMaBnVwc2VydCABKAIwCzgDSh5hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5FbnRpdHmjAaoBBWN0eXBlsgEGcHJvdG8ypAEUExoGdXBkYXRlIAIoAjALOANKHmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVudGl0eaMBqgEFY3R5cGWyAQZwcm90bzKkARQTGgZpbnNlcnQgAygCMAs4A0oeYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRW50aXR5owGqAQVjdHlwZbIBBnByb3RvMqQBFBMaDmluc2VydF9hdXRvX2lkIAQoAjALOANKHmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVudGl0eaMBqgEFY3R5cGWyAQZwcm90bzKkARQTGgZkZWxldGUgBSgCMAs4A0obYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuS2V5owGqAQVjdHlwZbIBBnByb3RvMqQBFBMaBWZvcmNlIAYoADAIOAFCBWZhbHNlowGqAQdkZWZhdWx0sgEFZmFsc2WkARTCAR1hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5FcnJvcg=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class DeprecatedMutationResult(ProtocolBuffer.ProtocolMessage):
  has_index_updates_ = 0
  index_updates_ = 0

  def __init__(self, contents=None):
    self.insert_auto_id_key_ = []
    self.upsert_version_ = []
    self.update_version_ = []
    self.insert_version_ = []
    self.insert_auto_id_version_ = []
    self.delete_version_ = []
    if contents is not None: self.MergeFromString(contents)

  def index_updates(self): return self.index_updates_

  def set_index_updates(self, x):
    self.has_index_updates_ = 1
    self.index_updates_ = x

  def clear_index_updates(self):
    if self.has_index_updates_:
      self.has_index_updates_ = 0
      self.index_updates_ = 0

  def has_index_updates(self): return self.has_index_updates_

  def insert_auto_id_key_size(self): return len(self.insert_auto_id_key_)
  def insert_auto_id_key_list(self): return self.insert_auto_id_key_

  def insert_auto_id_key(self, i):
    return self.insert_auto_id_key_[i]

  def mutable_insert_auto_id_key(self, i):
    return self.insert_auto_id_key_[i]

  def add_insert_auto_id_key(self):
    x = google.appengine.datastore.entity_v4_pb.Key()
    self.insert_auto_id_key_.append(x)
    return x

  def clear_insert_auto_id_key(self):
    self.insert_auto_id_key_ = []
  def upsert_version_size(self): return len(self.upsert_version_)
  def upsert_version_list(self): return self.upsert_version_

  def upsert_version(self, i):
    return self.upsert_version_[i]

  def set_upsert_version(self, i, x):
    self.upsert_version_[i] = x

  def add_upsert_version(self, x):
    self.upsert_version_.append(x)

  def clear_upsert_version(self):
    self.upsert_version_ = []

  def update_version_size(self): return len(self.update_version_)
  def update_version_list(self): return self.update_version_

  def update_version(self, i):
    return self.update_version_[i]

  def set_update_version(self, i, x):
    self.update_version_[i] = x

  def add_update_version(self, x):
    self.update_version_.append(x)

  def clear_update_version(self):
    self.update_version_ = []

  def insert_version_size(self): return len(self.insert_version_)
  def insert_version_list(self): return self.insert_version_

  def insert_version(self, i):
    return self.insert_version_[i]

  def set_insert_version(self, i, x):
    self.insert_version_[i] = x

  def add_insert_version(self, x):
    self.insert_version_.append(x)

  def clear_insert_version(self):
    self.insert_version_ = []

  def insert_auto_id_version_size(self): return len(self.insert_auto_id_version_)
  def insert_auto_id_version_list(self): return self.insert_auto_id_version_

  def insert_auto_id_version(self, i):
    return self.insert_auto_id_version_[i]

  def set_insert_auto_id_version(self, i, x):
    self.insert_auto_id_version_[i] = x

  def add_insert_auto_id_version(self, x):
    self.insert_auto_id_version_.append(x)

  def clear_insert_auto_id_version(self):
    self.insert_auto_id_version_ = []

  def delete_version_size(self): return len(self.delete_version_)
  def delete_version_list(self): return self.delete_version_

  def delete_version(self, i):
    return self.delete_version_[i]

  def set_delete_version(self, i, x):
    self.delete_version_[i] = x

  def add_delete_version(self, x):
    self.delete_version_.append(x)

  def clear_delete_version(self):
    self.delete_version_ = []


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_index_updates()): self.set_index_updates(x.index_updates())
    for i in xrange(x.insert_auto_id_key_size()): self.add_insert_auto_id_key().CopyFrom(x.insert_auto_id_key(i))
    for i in xrange(x.upsert_version_size()): self.add_upsert_version(x.upsert_version(i))
    for i in xrange(x.update_version_size()): self.add_update_version(x.update_version(i))
    for i in xrange(x.insert_version_size()): self.add_insert_version(x.insert_version(i))
    for i in xrange(x.insert_auto_id_version_size()): self.add_insert_auto_id_version(x.insert_auto_id_version(i))
    for i in xrange(x.delete_version_size()): self.add_delete_version(x.delete_version(i))

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.DeprecatedMutationResult', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.DeprecatedMutationResult')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.DeprecatedMutationResult')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.DeprecatedMutationResult', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.DeprecatedMutationResult', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.DeprecatedMutationResult', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_index_updates_ != x.has_index_updates_: return 0
    if self.has_index_updates_ and self.index_updates_ != x.index_updates_: return 0
    if len(self.insert_auto_id_key_) != len(x.insert_auto_id_key_): return 0
    for e1, e2 in zip(self.insert_auto_id_key_, x.insert_auto_id_key_):
      if e1 != e2: return 0
    if len(self.upsert_version_) != len(x.upsert_version_): return 0
    for e1, e2 in zip(self.upsert_version_, x.upsert_version_):
      if e1 != e2: return 0
    if len(self.update_version_) != len(x.update_version_): return 0
    for e1, e2 in zip(self.update_version_, x.update_version_):
      if e1 != e2: return 0
    if len(self.insert_version_) != len(x.insert_version_): return 0
    for e1, e2 in zip(self.insert_version_, x.insert_version_):
      if e1 != e2: return 0
    if len(self.insert_auto_id_version_) != len(x.insert_auto_id_version_): return 0
    for e1, e2 in zip(self.insert_auto_id_version_, x.insert_auto_id_version_):
      if e1 != e2: return 0
    if len(self.delete_version_) != len(x.delete_version_): return 0
    for e1, e2 in zip(self.delete_version_, x.delete_version_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_index_updates_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: index_updates not set.')
    for p in self.insert_auto_id_key_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.index_updates_)
    n += 1 * len(self.insert_auto_id_key_)
    for i in xrange(len(self.insert_auto_id_key_)): n += self.lengthString(self.insert_auto_id_key_[i].ByteSize())
    n += 1 * len(self.upsert_version_)
    for i in xrange(len(self.upsert_version_)): n += self.lengthVarInt64(self.upsert_version_[i])
    n += 1 * len(self.update_version_)
    for i in xrange(len(self.update_version_)): n += self.lengthVarInt64(self.update_version_[i])
    n += 1 * len(self.insert_version_)
    for i in xrange(len(self.insert_version_)): n += self.lengthVarInt64(self.insert_version_[i])
    n += 1 * len(self.insert_auto_id_version_)
    for i in xrange(len(self.insert_auto_id_version_)): n += self.lengthVarInt64(self.insert_auto_id_version_[i])
    n += 1 * len(self.delete_version_)
    for i in xrange(len(self.delete_version_)): n += self.lengthVarInt64(self.delete_version_[i])
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_index_updates_):
      n += 1
      n += self.lengthVarInt64(self.index_updates_)
    n += 1 * len(self.insert_auto_id_key_)
    for i in xrange(len(self.insert_auto_id_key_)): n += self.lengthString(self.insert_auto_id_key_[i].ByteSizePartial())
    n += 1 * len(self.upsert_version_)
    for i in xrange(len(self.upsert_version_)): n += self.lengthVarInt64(self.upsert_version_[i])
    n += 1 * len(self.update_version_)
    for i in xrange(len(self.update_version_)): n += self.lengthVarInt64(self.update_version_[i])
    n += 1 * len(self.insert_version_)
    for i in xrange(len(self.insert_version_)): n += self.lengthVarInt64(self.insert_version_[i])
    n += 1 * len(self.insert_auto_id_version_)
    for i in xrange(len(self.insert_auto_id_version_)): n += self.lengthVarInt64(self.insert_auto_id_version_[i])
    n += 1 * len(self.delete_version_)
    for i in xrange(len(self.delete_version_)): n += self.lengthVarInt64(self.delete_version_[i])
    return n

  def Clear(self):
    self.clear_index_updates()
    self.clear_insert_auto_id_key()
    self.clear_upsert_version()
    self.clear_update_version()
    self.clear_insert_version()
    self.clear_insert_auto_id_version()
    self.clear_delete_version()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt32(self.index_updates_)
    for i in xrange(len(self.insert_auto_id_key_)):
      out.putVarInt32(18)
      out.putVarInt32(self.insert_auto_id_key_[i].ByteSize())
      self.insert_auto_id_key_[i].OutputUnchecked(out)
    for i in xrange(len(self.upsert_version_)):
      out.putVarInt32(24)
      out.putVarInt64(self.upsert_version_[i])
    for i in xrange(len(self.update_version_)):
      out.putVarInt32(32)
      out.putVarInt64(self.update_version_[i])
    for i in xrange(len(self.insert_version_)):
      out.putVarInt32(40)
      out.putVarInt64(self.insert_version_[i])
    for i in xrange(len(self.insert_auto_id_version_)):
      out.putVarInt32(48)
      out.putVarInt64(self.insert_auto_id_version_[i])
    for i in xrange(len(self.delete_version_)):
      out.putVarInt32(56)
      out.putVarInt64(self.delete_version_[i])

  def OutputPartial(self, out):
    if (self.has_index_updates_):
      out.putVarInt32(8)
      out.putVarInt32(self.index_updates_)
    for i in xrange(len(self.insert_auto_id_key_)):
      out.putVarInt32(18)
      out.putVarInt32(self.insert_auto_id_key_[i].ByteSizePartial())
      self.insert_auto_id_key_[i].OutputPartial(out)
    for i in xrange(len(self.upsert_version_)):
      out.putVarInt32(24)
      out.putVarInt64(self.upsert_version_[i])
    for i in xrange(len(self.update_version_)):
      out.putVarInt32(32)
      out.putVarInt64(self.update_version_[i])
    for i in xrange(len(self.insert_version_)):
      out.putVarInt32(40)
      out.putVarInt64(self.insert_version_[i])
    for i in xrange(len(self.insert_auto_id_version_)):
      out.putVarInt32(48)
      out.putVarInt64(self.insert_auto_id_version_[i])
    for i in xrange(len(self.delete_version_)):
      out.putVarInt32(56)
      out.putVarInt64(self.delete_version_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_index_updates(d.getVarInt32())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_insert_auto_id_key().TryMerge(tmp)
        continue
      if tt == 24:
        self.add_upsert_version(d.getVarInt64())
        continue
      if tt == 32:
        self.add_update_version(d.getVarInt64())
        continue
      if tt == 40:
        self.add_insert_version(d.getVarInt64())
        continue
      if tt == 48:
        self.add_insert_auto_id_version(d.getVarInt64())
        continue
      if tt == 56:
        self.add_delete_version(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_index_updates_: res+=prefix+("index_updates: %s\n" % self.DebugFormatInt32(self.index_updates_))
    cnt=0
    for e in self.insert_auto_id_key_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("insert_auto_id_key%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.upsert_version_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("upsert_version%s: %s\n" % (elm, self.DebugFormatInt64(e)))
      cnt+=1
    cnt=0
    for e in self.update_version_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("update_version%s: %s\n" % (elm, self.DebugFormatInt64(e)))
      cnt+=1
    cnt=0
    for e in self.insert_version_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("insert_version%s: %s\n" % (elm, self.DebugFormatInt64(e)))
      cnt+=1
    cnt=0
    for e in self.insert_auto_id_version_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("insert_auto_id_version%s: %s\n" % (elm, self.DebugFormatInt64(e)))
      cnt+=1
    cnt=0
    for e in self.delete_version_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("delete_version%s: %s\n" % (elm, self.DebugFormatInt64(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kindex_updates = 1
  kinsert_auto_id_key = 2
  kupsert_version = 3
  kupdate_version = 4
  kinsert_version = 5
  kinsert_auto_id_version = 6
  kdelete_version = 7

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "index_updates",
    2: "insert_auto_id_key",
    3: "upsert_version",
    4: "update_version",
    5: "insert_version",
    6: "insert_auto_id_version",
    7: "delete_version",
  }, 7)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.NUMERIC,
    7: ProtocolBuffer.Encoder.NUMERIC,
  }, 7, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.DeprecatedMutationResult'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KMGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkRlcHJlY2F0ZWRNdXRhdGlvblJlc3VsdBMaDWluZGV4X3VwZGF0ZXMgASgAMAU4AhQTGhJpbnNlcnRfYXV0b19pZF9rZXkgAigCMAs4A0obYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuS2V5owGqAQVjdHlwZbIBBnByb3RvMqQBFBMaDnVwc2VydF92ZXJzaW9uIAMoADADOAMUExoOdXBkYXRlX3ZlcnNpb24gBCgAMAM4AxQTGg5pbnNlcnRfdmVyc2lvbiAFKAAwAzgDFBMaFmluc2VydF9hdXRvX2lkX3ZlcnNpb24gBigAMAM4AxQTGg5kZWxldGVfdmVyc2lvbiAHKAAwAzgDFMIBHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVycm9y"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class ReadOptions(ProtocolBuffer.ProtocolMessage):


  DEFAULT      =    0
  STRONG       =    1
  EVENTUAL     =    2

  _ReadConsistency_NAMES = {
    0: "DEFAULT",
    1: "STRONG",
    2: "EVENTUAL",
  }

  def ReadConsistency_Name(cls, x): return cls._ReadConsistency_NAMES.get(x, "")
  ReadConsistency_Name = classmethod(ReadConsistency_Name)

  has_read_consistency_ = 0
  read_consistency_ = 0
  has_transaction_ = 0
  transaction_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def read_consistency(self): return self.read_consistency_

  def set_read_consistency(self, x):
    self.has_read_consistency_ = 1
    self.read_consistency_ = x

  def clear_read_consistency(self):
    if self.has_read_consistency_:
      self.has_read_consistency_ = 0
      self.read_consistency_ = 0

  def has_read_consistency(self): return self.has_read_consistency_

  def transaction(self): return self.transaction_

  def set_transaction(self, x):
    self.has_transaction_ = 1
    self.transaction_ = x

  def clear_transaction(self):
    if self.has_transaction_:
      self.has_transaction_ = 0
      self.transaction_ = ""

  def has_transaction(self): return self.has_transaction_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_read_consistency()): self.set_read_consistency(x.read_consistency())
    if (x.has_transaction()): self.set_transaction(x.transaction())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.ReadOptions', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.ReadOptions')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.ReadOptions')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.ReadOptions', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.ReadOptions', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.ReadOptions', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_read_consistency_ != x.has_read_consistency_: return 0
    if self.has_read_consistency_ and self.read_consistency_ != x.read_consistency_: return 0
    if self.has_transaction_ != x.has_transaction_: return 0
    if self.has_transaction_ and self.transaction_ != x.transaction_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_read_consistency_): n += 1 + self.lengthVarInt64(self.read_consistency_)
    if (self.has_transaction_): n += 1 + self.lengthString(len(self.transaction_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_read_consistency_): n += 1 + self.lengthVarInt64(self.read_consistency_)
    if (self.has_transaction_): n += 1 + self.lengthString(len(self.transaction_))
    return n

  def Clear(self):
    self.clear_read_consistency()
    self.clear_transaction()

  def OutputUnchecked(self, out):
    if (self.has_read_consistency_):
      out.putVarInt32(8)
      out.putVarInt32(self.read_consistency_)
    if (self.has_transaction_):
      out.putVarInt32(18)
      out.putPrefixedString(self.transaction_)

  def OutputPartial(self, out):
    if (self.has_read_consistency_):
      out.putVarInt32(8)
      out.putVarInt32(self.read_consistency_)
    if (self.has_transaction_):
      out.putVarInt32(18)
      out.putPrefixedString(self.transaction_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_read_consistency(d.getVarInt32())
        continue
      if tt == 18:
        self.set_transaction(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_read_consistency_: res+=prefix+("read_consistency: %s\n" % self.DebugFormatInt32(self.read_consistency_))
    if self.has_transaction_: res+=prefix+("transaction: %s\n" % self.DebugFormatString(self.transaction_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kread_consistency = 1
  ktransaction = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "read_consistency",
    2: "transaction",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.ReadOptions'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KI2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlJlYWRPcHRpb25zExoQcmVhZF9jb25zaXN0ZW5jeSABKAAwBTgBQgEwaACjAaoBB2RlZmF1bHSyAQdERUZBVUxUpAEUExoLdHJhbnNhY3Rpb24gAigCMAk4ARRzeg9SZWFkQ29uc2lzdGVuY3mLAZIBB0RFRkFVTFSYAQCMAYsBkgEGU1RST05HmAEBjAGLAZIBCEVWRU5UVUFMmAECjAF0wgEdYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class LookupRequest(ProtocolBuffer.ProtocolMessage):
  has_read_options_ = 0
  read_options_ = None

  def __init__(self, contents=None):
    self.key_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def read_options(self):
    if self.read_options_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.read_options_ is None: self.read_options_ = ReadOptions()
      finally:
        self.lazy_init_lock_.release()
    return self.read_options_

  def mutable_read_options(self): self.has_read_options_ = 1; return self.read_options()

  def clear_read_options(self):

    if self.has_read_options_:
      self.has_read_options_ = 0;
      if self.read_options_ is not None: self.read_options_.Clear()

  def has_read_options(self): return self.has_read_options_

  def key_size(self): return len(self.key_)
  def key_list(self): return self.key_

  def key(self, i):
    return self.key_[i]

  def mutable_key(self, i):
    return self.key_[i]

  def add_key(self):
    x = google.appengine.datastore.entity_v4_pb.Key()
    self.key_.append(x)
    return x

  def clear_key(self):
    self.key_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_read_options()): self.mutable_read_options().MergeFrom(x.read_options())
    for i in xrange(x.key_size()): self.add_key().CopyFrom(x.key(i))

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.LookupRequest', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.LookupRequest')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.LookupRequest')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.LookupRequest', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.LookupRequest', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.LookupRequest', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_read_options_ != x.has_read_options_: return 0
    if self.has_read_options_ and self.read_options_ != x.read_options_: return 0
    if len(self.key_) != len(x.key_): return 0
    for e1, e2 in zip(self.key_, x.key_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_read_options_ and not self.read_options_.IsInitialized(debug_strs)): initialized = 0
    for p in self.key_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_read_options_): n += 1 + self.lengthString(self.read_options_.ByteSize())
    n += 1 * len(self.key_)
    for i in xrange(len(self.key_)): n += self.lengthString(self.key_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_read_options_): n += 1 + self.lengthString(self.read_options_.ByteSizePartial())
    n += 1 * len(self.key_)
    for i in xrange(len(self.key_)): n += self.lengthString(self.key_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_read_options()
    self.clear_key()

  def OutputUnchecked(self, out):
    if (self.has_read_options_):
      out.putVarInt32(10)
      out.putVarInt32(self.read_options_.ByteSize())
      self.read_options_.OutputUnchecked(out)
    for i in xrange(len(self.key_)):
      out.putVarInt32(26)
      out.putVarInt32(self.key_[i].ByteSize())
      self.key_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_read_options_):
      out.putVarInt32(10)
      out.putVarInt32(self.read_options_.ByteSizePartial())
      self.read_options_.OutputPartial(out)
    for i in xrange(len(self.key_)):
      out.putVarInt32(26)
      out.putVarInt32(self.key_[i].ByteSizePartial())
      self.key_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_read_options().TryMerge(tmp)
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_key().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_read_options_:
      res+=prefix+"read_options <\n"
      res+=self.read_options_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    cnt=0
    for e in self.key_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("key%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kread_options = 1
  kkey = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "read_options",
    3: "key",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.LookupRequest'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KJWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0Lkxvb2t1cFJlcXVlc3QTGgxyZWFkX29wdGlvbnMgASgCMAs4AUojYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUmVhZE9wdGlvbnOjAaoBBWN0eXBlsgEGcHJvdG8ypAEUExoDa2V5IAMoAjALOANKG2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktleaMBqgEFY3R5cGWyAQZwcm90bzKkARTCAR1hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5FcnJvcg=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class LookupResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.found_ = []
    self.missing_ = []
    self.deferred_ = []
    if contents is not None: self.MergeFromString(contents)

  def found_size(self): return len(self.found_)
  def found_list(self): return self.found_

  def found(self, i):
    return self.found_[i]

  def mutable_found(self, i):
    return self.found_[i]

  def add_found(self):
    x = EntityResult()
    self.found_.append(x)
    return x

  def clear_found(self):
    self.found_ = []
  def missing_size(self): return len(self.missing_)
  def missing_list(self): return self.missing_

  def missing(self, i):
    return self.missing_[i]

  def mutable_missing(self, i):
    return self.missing_[i]

  def add_missing(self):
    x = EntityResult()
    self.missing_.append(x)
    return x

  def clear_missing(self):
    self.missing_ = []
  def deferred_size(self): return len(self.deferred_)
  def deferred_list(self): return self.deferred_

  def deferred(self, i):
    return self.deferred_[i]

  def mutable_deferred(self, i):
    return self.deferred_[i]

  def add_deferred(self):
    x = google.appengine.datastore.entity_v4_pb.Key()
    self.deferred_.append(x)
    return x

  def clear_deferred(self):
    self.deferred_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.found_size()): self.add_found().CopyFrom(x.found(i))
    for i in xrange(x.missing_size()): self.add_missing().CopyFrom(x.missing(i))
    for i in xrange(x.deferred_size()): self.add_deferred().CopyFrom(x.deferred(i))

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.LookupResponse', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.LookupResponse')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.LookupResponse')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.LookupResponse', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.LookupResponse', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.LookupResponse', s)


  def Equals(self, x):
    if x is self: return 1
    if len(self.found_) != len(x.found_): return 0
    for e1, e2 in zip(self.found_, x.found_):
      if e1 != e2: return 0
    if len(self.missing_) != len(x.missing_): return 0
    for e1, e2 in zip(self.missing_, x.missing_):
      if e1 != e2: return 0
    if len(self.deferred_) != len(x.deferred_): return 0
    for e1, e2 in zip(self.deferred_, x.deferred_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.found_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.missing_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.deferred_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.found_)
    for i in xrange(len(self.found_)): n += self.lengthString(self.found_[i].ByteSize())
    n += 1 * len(self.missing_)
    for i in xrange(len(self.missing_)): n += self.lengthString(self.missing_[i].ByteSize())
    n += 1 * len(self.deferred_)
    for i in xrange(len(self.deferred_)): n += self.lengthString(self.deferred_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.found_)
    for i in xrange(len(self.found_)): n += self.lengthString(self.found_[i].ByteSizePartial())
    n += 1 * len(self.missing_)
    for i in xrange(len(self.missing_)): n += self.lengthString(self.missing_[i].ByteSizePartial())
    n += 1 * len(self.deferred_)
    for i in xrange(len(self.deferred_)): n += self.lengthString(self.deferred_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_found()
    self.clear_missing()
    self.clear_deferred()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.found_)):
      out.putVarInt32(10)
      out.putVarInt32(self.found_[i].ByteSize())
      self.found_[i].OutputUnchecked(out)
    for i in xrange(len(self.missing_)):
      out.putVarInt32(18)
      out.putVarInt32(self.missing_[i].ByteSize())
      self.missing_[i].OutputUnchecked(out)
    for i in xrange(len(self.deferred_)):
      out.putVarInt32(26)
      out.putVarInt32(self.deferred_[i].ByteSize())
      self.deferred_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.found_)):
      out.putVarInt32(10)
      out.putVarInt32(self.found_[i].ByteSizePartial())
      self.found_[i].OutputPartial(out)
    for i in xrange(len(self.missing_)):
      out.putVarInt32(18)
      out.putVarInt32(self.missing_[i].ByteSizePartial())
      self.missing_[i].OutputPartial(out)
    for i in xrange(len(self.deferred_)):
      out.putVarInt32(26)
      out.putVarInt32(self.deferred_[i].ByteSizePartial())
      self.deferred_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_found().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_missing().TryMerge(tmp)
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_deferred().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.found_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("found%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.missing_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("missing%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.deferred_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("deferred%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kfound = 1
  kmissing = 2
  kdeferred = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "found",
    2: "missing",
    3: "deferred",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.LookupResponse'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KJmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0Lkxvb2t1cFJlc3BvbnNlExoFZm91bmQgASgCMAs4A0okYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRW50aXR5UmVzdWx0owGqAQVjdHlwZbIBBnByb3RvMqQBFBMaB21pc3NpbmcgAigCMAs4A0okYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRW50aXR5UmVzdWx0owGqAQVjdHlwZbIBBnByb3RvMqQBFBMaCGRlZmVycmVkIAMoAjALOANKG2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktleaMBqgEFY3R5cGWyAQZwcm90bzKkARTCAR1hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5FcnJvcg=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class RunQueryRequest(ProtocolBuffer.ProtocolMessage):
  has_read_options_ = 0
  read_options_ = None
  has_partition_id_ = 0
  partition_id_ = None
  has_query_ = 0
  query_ = None
  has_gql_query_ = 0
  gql_query_ = None
  has_min_safe_time_seconds_ = 0
  min_safe_time_seconds_ = 0
  has_suggested_batch_size_ = 0
  suggested_batch_size_ = 0

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def read_options(self):
    if self.read_options_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.read_options_ is None: self.read_options_ = ReadOptions()
      finally:
        self.lazy_init_lock_.release()
    return self.read_options_

  def mutable_read_options(self): self.has_read_options_ = 1; return self.read_options()

  def clear_read_options(self):

    if self.has_read_options_:
      self.has_read_options_ = 0;
      if self.read_options_ is not None: self.read_options_.Clear()

  def has_read_options(self): return self.has_read_options_

  def partition_id(self):
    if self.partition_id_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.partition_id_ is None: self.partition_id_ = google.appengine.datastore.entity_v4_pb.PartitionId()
      finally:
        self.lazy_init_lock_.release()
    return self.partition_id_

  def mutable_partition_id(self): self.has_partition_id_ = 1; return self.partition_id()

  def clear_partition_id(self):

    if self.has_partition_id_:
      self.has_partition_id_ = 0;
      if self.partition_id_ is not None: self.partition_id_.Clear()

  def has_partition_id(self): return self.has_partition_id_

  def query(self):
    if self.query_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.query_ is None: self.query_ = Query()
      finally:
        self.lazy_init_lock_.release()
    return self.query_

  def mutable_query(self): self.has_query_ = 1; return self.query()

  def clear_query(self):

    if self.has_query_:
      self.has_query_ = 0;
      if self.query_ is not None: self.query_.Clear()

  def has_query(self): return self.has_query_

  def gql_query(self):
    if self.gql_query_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.gql_query_ is None: self.gql_query_ = GqlQuery()
      finally:
        self.lazy_init_lock_.release()
    return self.gql_query_

  def mutable_gql_query(self): self.has_gql_query_ = 1; return self.gql_query()

  def clear_gql_query(self):

    if self.has_gql_query_:
      self.has_gql_query_ = 0;
      if self.gql_query_ is not None: self.gql_query_.Clear()

  def has_gql_query(self): return self.has_gql_query_

  def min_safe_time_seconds(self): return self.min_safe_time_seconds_

  def set_min_safe_time_seconds(self, x):
    self.has_min_safe_time_seconds_ = 1
    self.min_safe_time_seconds_ = x

  def clear_min_safe_time_seconds(self):
    if self.has_min_safe_time_seconds_:
      self.has_min_safe_time_seconds_ = 0
      self.min_safe_time_seconds_ = 0

  def has_min_safe_time_seconds(self): return self.has_min_safe_time_seconds_

  def suggested_batch_size(self): return self.suggested_batch_size_

  def set_suggested_batch_size(self, x):
    self.has_suggested_batch_size_ = 1
    self.suggested_batch_size_ = x

  def clear_suggested_batch_size(self):
    if self.has_suggested_batch_size_:
      self.has_suggested_batch_size_ = 0
      self.suggested_batch_size_ = 0

  def has_suggested_batch_size(self): return self.has_suggested_batch_size_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_read_options()): self.mutable_read_options().MergeFrom(x.read_options())
    if (x.has_partition_id()): self.mutable_partition_id().MergeFrom(x.partition_id())
    if (x.has_query()): self.mutable_query().MergeFrom(x.query())
    if (x.has_gql_query()): self.mutable_gql_query().MergeFrom(x.gql_query())
    if (x.has_min_safe_time_seconds()): self.set_min_safe_time_seconds(x.min_safe_time_seconds())
    if (x.has_suggested_batch_size()): self.set_suggested_batch_size(x.suggested_batch_size())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.RunQueryRequest', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.RunQueryRequest')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.RunQueryRequest')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.RunQueryRequest', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.RunQueryRequest', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.RunQueryRequest', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_read_options_ != x.has_read_options_: return 0
    if self.has_read_options_ and self.read_options_ != x.read_options_: return 0
    if self.has_partition_id_ != x.has_partition_id_: return 0
    if self.has_partition_id_ and self.partition_id_ != x.partition_id_: return 0
    if self.has_query_ != x.has_query_: return 0
    if self.has_query_ and self.query_ != x.query_: return 0
    if self.has_gql_query_ != x.has_gql_query_: return 0
    if self.has_gql_query_ and self.gql_query_ != x.gql_query_: return 0
    if self.has_min_safe_time_seconds_ != x.has_min_safe_time_seconds_: return 0
    if self.has_min_safe_time_seconds_ and self.min_safe_time_seconds_ != x.min_safe_time_seconds_: return 0
    if self.has_suggested_batch_size_ != x.has_suggested_batch_size_: return 0
    if self.has_suggested_batch_size_ and self.suggested_batch_size_ != x.suggested_batch_size_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_read_options_ and not self.read_options_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_partition_id_ and not self.partition_id_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_query_ and not self.query_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_gql_query_ and not self.gql_query_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_read_options_): n += 1 + self.lengthString(self.read_options_.ByteSize())
    if (self.has_partition_id_): n += 1 + self.lengthString(self.partition_id_.ByteSize())
    if (self.has_query_): n += 1 + self.lengthString(self.query_.ByteSize())
    if (self.has_gql_query_): n += 1 + self.lengthString(self.gql_query_.ByteSize())
    if (self.has_min_safe_time_seconds_): n += 1 + self.lengthVarInt64(self.min_safe_time_seconds_)
    if (self.has_suggested_batch_size_): n += 1 + self.lengthVarInt64(self.suggested_batch_size_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_read_options_): n += 1 + self.lengthString(self.read_options_.ByteSizePartial())
    if (self.has_partition_id_): n += 1 + self.lengthString(self.partition_id_.ByteSizePartial())
    if (self.has_query_): n += 1 + self.lengthString(self.query_.ByteSizePartial())
    if (self.has_gql_query_): n += 1 + self.lengthString(self.gql_query_.ByteSizePartial())
    if (self.has_min_safe_time_seconds_): n += 1 + self.lengthVarInt64(self.min_safe_time_seconds_)
    if (self.has_suggested_batch_size_): n += 1 + self.lengthVarInt64(self.suggested_batch_size_)
    return n

  def Clear(self):
    self.clear_read_options()
    self.clear_partition_id()
    self.clear_query()
    self.clear_gql_query()
    self.clear_min_safe_time_seconds()
    self.clear_suggested_batch_size()

  def OutputUnchecked(self, out):
    if (self.has_read_options_):
      out.putVarInt32(10)
      out.putVarInt32(self.read_options_.ByteSize())
      self.read_options_.OutputUnchecked(out)
    if (self.has_partition_id_):
      out.putVarInt32(18)
      out.putVarInt32(self.partition_id_.ByteSize())
      self.partition_id_.OutputUnchecked(out)
    if (self.has_query_):
      out.putVarInt32(26)
      out.putVarInt32(self.query_.ByteSize())
      self.query_.OutputUnchecked(out)
    if (self.has_min_safe_time_seconds_):
      out.putVarInt32(32)
      out.putVarInt64(self.min_safe_time_seconds_)
    if (self.has_suggested_batch_size_):
      out.putVarInt32(40)
      out.putVarInt32(self.suggested_batch_size_)
    if (self.has_gql_query_):
      out.putVarInt32(58)
      out.putVarInt32(self.gql_query_.ByteSize())
      self.gql_query_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_read_options_):
      out.putVarInt32(10)
      out.putVarInt32(self.read_options_.ByteSizePartial())
      self.read_options_.OutputPartial(out)
    if (self.has_partition_id_):
      out.putVarInt32(18)
      out.putVarInt32(self.partition_id_.ByteSizePartial())
      self.partition_id_.OutputPartial(out)
    if (self.has_query_):
      out.putVarInt32(26)
      out.putVarInt32(self.query_.ByteSizePartial())
      self.query_.OutputPartial(out)
    if (self.has_min_safe_time_seconds_):
      out.putVarInt32(32)
      out.putVarInt64(self.min_safe_time_seconds_)
    if (self.has_suggested_batch_size_):
      out.putVarInt32(40)
      out.putVarInt32(self.suggested_batch_size_)
    if (self.has_gql_query_):
      out.putVarInt32(58)
      out.putVarInt32(self.gql_query_.ByteSizePartial())
      self.gql_query_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_read_options().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_partition_id().TryMerge(tmp)
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_query().TryMerge(tmp)
        continue
      if tt == 32:
        self.set_min_safe_time_seconds(d.getVarInt64())
        continue
      if tt == 40:
        self.set_suggested_batch_size(d.getVarInt32())
        continue
      if tt == 58:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_gql_query().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_read_options_:
      res+=prefix+"read_options <\n"
      res+=self.read_options_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_partition_id_:
      res+=prefix+"partition_id <\n"
      res+=self.partition_id_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_query_:
      res+=prefix+"query <\n"
      res+=self.query_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_gql_query_:
      res+=prefix+"gql_query <\n"
      res+=self.gql_query_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_min_safe_time_seconds_: res+=prefix+("min_safe_time_seconds: %s\n" % self.DebugFormatInt64(self.min_safe_time_seconds_))
    if self.has_suggested_batch_size_: res+=prefix+("suggested_batch_size: %s\n" % self.DebugFormatInt32(self.suggested_batch_size_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kread_options = 1
  kpartition_id = 2
  kquery = 3
  kgql_query = 7
  kmin_safe_time_seconds = 4
  ksuggested_batch_size = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "read_options",
    2: "partition_id",
    3: "query",
    4: "min_safe_time_seconds",
    5: "suggested_batch_size",
    7: "gql_query",
  }, 7)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.NUMERIC,
    7: ProtocolBuffer.Encoder.STRING,
  }, 7, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.RunQueryRequest'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KJ2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlJ1blF1ZXJ5UmVxdWVzdBMaDHJlYWRfb3B0aW9ucyABKAIwCzgBSiNhcHBob3N0aW5nLmRhdGFzdG9yZS52NC5SZWFkT3B0aW9uc6MBqgEFY3R5cGWyAQZwcm90bzKkARQTGgxwYXJ0aXRpb25faWQgAigCMAs4AUojYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUGFydGl0aW9uSWSjAaoBBWN0eXBlsgEGcHJvdG8ypAEUExoFcXVlcnkgAygCMAs4AUodYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuUXVlcnmjAaoBBWN0eXBlsgEGcHJvdG8ypAEUExoJZ3FsX3F1ZXJ5IAcoAjALOAFKIGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkdxbFF1ZXJ5owGqAQVjdHlwZbIBBnByb3RvMqQBFBMaFW1pbl9zYWZlX3RpbWVfc2Vjb25kcyAEKAAwAzgBFBMaFHN1Z2dlc3RlZF9iYXRjaF9zaXplIAUoADAFOAEUwgEdYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class RunQueryResponse(ProtocolBuffer.ProtocolMessage):
  has_batch_ = 0
  has_query_handle_ = 0
  query_handle_ = ""

  def __init__(self, contents=None):
    self.batch_ = QueryResultBatch()
    if contents is not None: self.MergeFromString(contents)

  def batch(self): return self.batch_

  def mutable_batch(self): self.has_batch_ = 1; return self.batch_

  def clear_batch(self):self.has_batch_ = 0; self.batch_.Clear()

  def has_batch(self): return self.has_batch_

  def query_handle(self): return self.query_handle_

  def set_query_handle(self, x):
    self.has_query_handle_ = 1
    self.query_handle_ = x

  def clear_query_handle(self):
    if self.has_query_handle_:
      self.has_query_handle_ = 0
      self.query_handle_ = ""

  def has_query_handle(self): return self.has_query_handle_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_batch()): self.mutable_batch().MergeFrom(x.batch())
    if (x.has_query_handle()): self.set_query_handle(x.query_handle())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.RunQueryResponse', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.RunQueryResponse')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.RunQueryResponse')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.RunQueryResponse', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.RunQueryResponse', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.RunQueryResponse', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_batch_ != x.has_batch_: return 0
    if self.has_batch_ and self.batch_ != x.batch_: return 0
    if self.has_query_handle_ != x.has_query_handle_: return 0
    if self.has_query_handle_ and self.query_handle_ != x.query_handle_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_batch_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: batch not set.')
    elif not self.batch_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.batch_.ByteSize())
    if (self.has_query_handle_): n += 1 + self.lengthString(len(self.query_handle_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_batch_):
      n += 1
      n += self.lengthString(self.batch_.ByteSizePartial())
    if (self.has_query_handle_): n += 1 + self.lengthString(len(self.query_handle_))
    return n

  def Clear(self):
    self.clear_batch()
    self.clear_query_handle()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.batch_.ByteSize())
    self.batch_.OutputUnchecked(out)
    if (self.has_query_handle_):
      out.putVarInt32(18)
      out.putPrefixedString(self.query_handle_)

  def OutputPartial(self, out):
    if (self.has_batch_):
      out.putVarInt32(10)
      out.putVarInt32(self.batch_.ByteSizePartial())
      self.batch_.OutputPartial(out)
    if (self.has_query_handle_):
      out.putVarInt32(18)
      out.putPrefixedString(self.query_handle_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_batch().TryMerge(tmp)
        continue
      if tt == 18:
        self.set_query_handle(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_batch_:
      res+=prefix+"batch <\n"
      res+=self.batch_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_query_handle_: res+=prefix+("query_handle: %s\n" % self.DebugFormatString(self.query_handle_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kbatch = 1
  kquery_handle = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "batch",
    2: "query_handle",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.RunQueryResponse'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KKGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlJ1blF1ZXJ5UmVzcG9uc2UTGgViYXRjaCABKAIwCzgCSihhcHBob3N0aW5nLmRhdGFzdG9yZS52NC5RdWVyeVJlc3VsdEJhdGNoowGqAQVjdHlwZbIBBnByb3RvMqQBFBMaDHF1ZXJ5X2hhbmRsZSACKAIwCTgBFMIBHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVycm9y"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class ContinueQueryRequest(ProtocolBuffer.ProtocolMessage):
  has_query_handle_ = 0
  query_handle_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def query_handle(self): return self.query_handle_

  def set_query_handle(self, x):
    self.has_query_handle_ = 1
    self.query_handle_ = x

  def clear_query_handle(self):
    if self.has_query_handle_:
      self.has_query_handle_ = 0
      self.query_handle_ = ""

  def has_query_handle(self): return self.has_query_handle_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_query_handle()): self.set_query_handle(x.query_handle())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.ContinueQueryRequest', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.ContinueQueryRequest')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.ContinueQueryRequest')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.ContinueQueryRequest', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.ContinueQueryRequest', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.ContinueQueryRequest', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_query_handle_ != x.has_query_handle_: return 0
    if self.has_query_handle_ and self.query_handle_ != x.query_handle_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_query_handle_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: query_handle not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.query_handle_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_query_handle_):
      n += 1
      n += self.lengthString(len(self.query_handle_))
    return n

  def Clear(self):
    self.clear_query_handle()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.query_handle_)

  def OutputPartial(self, out):
    if (self.has_query_handle_):
      out.putVarInt32(10)
      out.putPrefixedString(self.query_handle_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_query_handle(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_query_handle_: res+=prefix+("query_handle: %s\n" % self.DebugFormatString(self.query_handle_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kquery_handle = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "query_handle",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.ContinueQueryRequest'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KLGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkNvbnRpbnVlUXVlcnlSZXF1ZXN0ExoMcXVlcnlfaGFuZGxlIAEoAjAJOAIUwgEdYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class ContinueQueryResponse(ProtocolBuffer.ProtocolMessage):
  has_batch_ = 0

  def __init__(self, contents=None):
    self.batch_ = QueryResultBatch()
    if contents is not None: self.MergeFromString(contents)

  def batch(self): return self.batch_

  def mutable_batch(self): self.has_batch_ = 1; return self.batch_

  def clear_batch(self):self.has_batch_ = 0; self.batch_.Clear()

  def has_batch(self): return self.has_batch_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_batch()): self.mutable_batch().MergeFrom(x.batch())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.ContinueQueryResponse', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.ContinueQueryResponse')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.ContinueQueryResponse')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.ContinueQueryResponse', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.ContinueQueryResponse', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.ContinueQueryResponse', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_batch_ != x.has_batch_: return 0
    if self.has_batch_ and self.batch_ != x.batch_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_batch_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: batch not set.')
    elif not self.batch_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(self.batch_.ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_batch_):
      n += 1
      n += self.lengthString(self.batch_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_batch()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putVarInt32(self.batch_.ByteSize())
    self.batch_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_batch_):
      out.putVarInt32(10)
      out.putVarInt32(self.batch_.ByteSizePartial())
      self.batch_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_batch().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_batch_:
      res+=prefix+"batch <\n"
      res+=self.batch_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kbatch = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "batch",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.ContinueQueryResponse'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KLWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkNvbnRpbnVlUXVlcnlSZXNwb25zZRMaBWJhdGNoIAEoAjALOAJKKGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlF1ZXJ5UmVzdWx0QmF0Y2ijAaoBBWN0eXBlsgEGcHJvdG8ypAEUwgEdYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class BeginTransactionRequest(ProtocolBuffer.ProtocolMessage):
  has_cross_group_ = 0
  cross_group_ = 0
  has_cross_request_ = 0
  cross_request_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def cross_group(self): return self.cross_group_

  def set_cross_group(self, x):
    self.has_cross_group_ = 1
    self.cross_group_ = x

  def clear_cross_group(self):
    if self.has_cross_group_:
      self.has_cross_group_ = 0
      self.cross_group_ = 0

  def has_cross_group(self): return self.has_cross_group_

  def cross_request(self): return self.cross_request_

  def set_cross_request(self, x):
    self.has_cross_request_ = 1
    self.cross_request_ = x

  def clear_cross_request(self):
    if self.has_cross_request_:
      self.has_cross_request_ = 0
      self.cross_request_ = 0

  def has_cross_request(self): return self.has_cross_request_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_cross_group()): self.set_cross_group(x.cross_group())
    if (x.has_cross_request()): self.set_cross_request(x.cross_request())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.BeginTransactionRequest', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.BeginTransactionRequest')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.BeginTransactionRequest')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.BeginTransactionRequest', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.BeginTransactionRequest', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.BeginTransactionRequest', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_cross_group_ != x.has_cross_group_: return 0
    if self.has_cross_group_ and self.cross_group_ != x.cross_group_: return 0
    if self.has_cross_request_ != x.has_cross_request_: return 0
    if self.has_cross_request_ and self.cross_request_ != x.cross_request_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_cross_group_): n += 2
    if (self.has_cross_request_): n += 2
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_cross_group_): n += 2
    if (self.has_cross_request_): n += 2
    return n

  def Clear(self):
    self.clear_cross_group()
    self.clear_cross_request()

  def OutputUnchecked(self, out):
    if (self.has_cross_group_):
      out.putVarInt32(8)
      out.putBoolean(self.cross_group_)
    if (self.has_cross_request_):
      out.putVarInt32(16)
      out.putBoolean(self.cross_request_)

  def OutputPartial(self, out):
    if (self.has_cross_group_):
      out.putVarInt32(8)
      out.putBoolean(self.cross_group_)
    if (self.has_cross_request_):
      out.putVarInt32(16)
      out.putBoolean(self.cross_request_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_cross_group(d.getBoolean())
        continue
      if tt == 16:
        self.set_cross_request(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_cross_group_: res+=prefix+("cross_group: %s\n" % self.DebugFormatBool(self.cross_group_))
    if self.has_cross_request_: res+=prefix+("cross_request: %s\n" % self.DebugFormatBool(self.cross_request_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kcross_group = 1
  kcross_request = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "cross_group",
    2: "cross_request",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.BeginTransactionRequest'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KL2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkJlZ2luVHJhbnNhY3Rpb25SZXF1ZXN0ExoLY3Jvc3NfZ3JvdXAgASgAMAg4AUIFZmFsc2WjAaoBB2RlZmF1bHSyAQVmYWxzZaQBFBMaDWNyb3NzX3JlcXVlc3QgAigAMAg4AUIFZmFsc2WjAaoBB2RlZmF1bHSyAQVmYWxzZaQBFMIBHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVycm9y"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class BeginTransactionResponse(ProtocolBuffer.ProtocolMessage):
  has_transaction_ = 0
  transaction_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def transaction(self): return self.transaction_

  def set_transaction(self, x):
    self.has_transaction_ = 1
    self.transaction_ = x

  def clear_transaction(self):
    if self.has_transaction_:
      self.has_transaction_ = 0
      self.transaction_ = ""

  def has_transaction(self): return self.has_transaction_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_transaction()): self.set_transaction(x.transaction())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.BeginTransactionResponse', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.BeginTransactionResponse')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.BeginTransactionResponse')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.BeginTransactionResponse', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.BeginTransactionResponse', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.BeginTransactionResponse', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_transaction_ != x.has_transaction_: return 0
    if self.has_transaction_ and self.transaction_ != x.transaction_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_transaction_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: transaction not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.transaction_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_transaction_):
      n += 1
      n += self.lengthString(len(self.transaction_))
    return n

  def Clear(self):
    self.clear_transaction()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.transaction_)

  def OutputPartial(self, out):
    if (self.has_transaction_):
      out.putVarInt32(10)
      out.putPrefixedString(self.transaction_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_transaction(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_transaction_: res+=prefix+("transaction: %s\n" % self.DebugFormatString(self.transaction_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktransaction = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "transaction",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.BeginTransactionResponse'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KMGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkJlZ2luVHJhbnNhY3Rpb25SZXNwb25zZRMaC3RyYW5zYWN0aW9uIAEoAjAJOAIUwgEdYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class RollbackRequest(ProtocolBuffer.ProtocolMessage):
  has_transaction_ = 0
  transaction_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def transaction(self): return self.transaction_

  def set_transaction(self, x):
    self.has_transaction_ = 1
    self.transaction_ = x

  def clear_transaction(self):
    if self.has_transaction_:
      self.has_transaction_ = 0
      self.transaction_ = ""

  def has_transaction(self): return self.has_transaction_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_transaction()): self.set_transaction(x.transaction())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.RollbackRequest', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.RollbackRequest')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.RollbackRequest')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.RollbackRequest', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.RollbackRequest', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.RollbackRequest', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_transaction_ != x.has_transaction_: return 0
    if self.has_transaction_ and self.transaction_ != x.transaction_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_transaction_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: transaction not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.transaction_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_transaction_):
      n += 1
      n += self.lengthString(len(self.transaction_))
    return n

  def Clear(self):
    self.clear_transaction()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.transaction_)

  def OutputPartial(self, out):
    if (self.has_transaction_):
      out.putVarInt32(10)
      out.putPrefixedString(self.transaction_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_transaction(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_transaction_: res+=prefix+("transaction: %s\n" % self.DebugFormatString(self.transaction_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktransaction = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "transaction",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.RollbackRequest'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KJ2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlJvbGxiYWNrUmVxdWVzdBMaC3RyYW5zYWN0aW9uIAEoAjAJOAIUwgEdYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class RollbackResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    pass
    if contents is not None: self.MergeFromString(contents)


  def MergeFrom(self, x):
    assert x is not self

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.RollbackResponse', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.RollbackResponse')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.RollbackResponse')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.RollbackResponse', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.RollbackResponse', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.RollbackResponse', s)


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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.RollbackResponse'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KKGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LlJvbGxiYWNrUmVzcG9uc2XCAR1hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5FcnJvcg=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class CommitRequest(ProtocolBuffer.ProtocolMessage):


  TRANSACTIONAL =    1
  NON_TRANSACTIONAL =    2

  _Mode_NAMES = {
    1: "TRANSACTIONAL",
    2: "NON_TRANSACTIONAL",
  }

  def Mode_Name(cls, x): return cls._Mode_NAMES.get(x, "")
  Mode_Name = classmethod(Mode_Name)

  has_transaction_ = 0
  transaction_ = ""
  has_deprecated_mutation_ = 0
  deprecated_mutation_ = None
  has_mode_ = 0
  mode_ = 1
  has_ignore_read_only_ = 0
  ignore_read_only_ = 0

  def __init__(self, contents=None):
    self.mutation_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def transaction(self): return self.transaction_

  def set_transaction(self, x):
    self.has_transaction_ = 1
    self.transaction_ = x

  def clear_transaction(self):
    if self.has_transaction_:
      self.has_transaction_ = 0
      self.transaction_ = ""

  def has_transaction(self): return self.has_transaction_

  def mutation_size(self): return len(self.mutation_)
  def mutation_list(self): return self.mutation_

  def mutation(self, i):
    return self.mutation_[i]

  def mutable_mutation(self, i):
    return self.mutation_[i]

  def add_mutation(self):
    x = Mutation()
    self.mutation_.append(x)
    return x

  def clear_mutation(self):
    self.mutation_ = []
  def deprecated_mutation(self):
    if self.deprecated_mutation_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.deprecated_mutation_ is None: self.deprecated_mutation_ = DeprecatedMutation()
      finally:
        self.lazy_init_lock_.release()
    return self.deprecated_mutation_

  def mutable_deprecated_mutation(self): self.has_deprecated_mutation_ = 1; return self.deprecated_mutation()

  def clear_deprecated_mutation(self):

    if self.has_deprecated_mutation_:
      self.has_deprecated_mutation_ = 0;
      if self.deprecated_mutation_ is not None: self.deprecated_mutation_.Clear()

  def has_deprecated_mutation(self): return self.has_deprecated_mutation_

  def mode(self): return self.mode_

  def set_mode(self, x):
    self.has_mode_ = 1
    self.mode_ = x

  def clear_mode(self):
    if self.has_mode_:
      self.has_mode_ = 0
      self.mode_ = 1

  def has_mode(self): return self.has_mode_

  def ignore_read_only(self): return self.ignore_read_only_

  def set_ignore_read_only(self, x):
    self.has_ignore_read_only_ = 1
    self.ignore_read_only_ = x

  def clear_ignore_read_only(self):
    if self.has_ignore_read_only_:
      self.has_ignore_read_only_ = 0
      self.ignore_read_only_ = 0

  def has_ignore_read_only(self): return self.has_ignore_read_only_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_transaction()): self.set_transaction(x.transaction())
    for i in xrange(x.mutation_size()): self.add_mutation().CopyFrom(x.mutation(i))
    if (x.has_deprecated_mutation()): self.mutable_deprecated_mutation().MergeFrom(x.deprecated_mutation())
    if (x.has_mode()): self.set_mode(x.mode())
    if (x.has_ignore_read_only()): self.set_ignore_read_only(x.ignore_read_only())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.CommitRequest', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.CommitRequest')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.CommitRequest')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.CommitRequest', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.CommitRequest', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.CommitRequest', s)


  def Equals(self, x):
    if x is self: return 1
    if self.has_transaction_ != x.has_transaction_: return 0
    if self.has_transaction_ and self.transaction_ != x.transaction_: return 0
    if len(self.mutation_) != len(x.mutation_): return 0
    for e1, e2 in zip(self.mutation_, x.mutation_):
      if e1 != e2: return 0
    if self.has_deprecated_mutation_ != x.has_deprecated_mutation_: return 0
    if self.has_deprecated_mutation_ and self.deprecated_mutation_ != x.deprecated_mutation_: return 0
    if self.has_mode_ != x.has_mode_: return 0
    if self.has_mode_ and self.mode_ != x.mode_: return 0
    if self.has_ignore_read_only_ != x.has_ignore_read_only_: return 0
    if self.has_ignore_read_only_ and self.ignore_read_only_ != x.ignore_read_only_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.mutation_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_deprecated_mutation_ and not self.deprecated_mutation_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_transaction_): n += 1 + self.lengthString(len(self.transaction_))
    n += 1 * len(self.mutation_)
    for i in xrange(len(self.mutation_)): n += self.lengthString(self.mutation_[i].ByteSize())
    if (self.has_deprecated_mutation_): n += 1 + self.lengthString(self.deprecated_mutation_.ByteSize())
    if (self.has_mode_): n += 1 + self.lengthVarInt64(self.mode_)
    if (self.has_ignore_read_only_): n += 2
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_transaction_): n += 1 + self.lengthString(len(self.transaction_))
    n += 1 * len(self.mutation_)
    for i in xrange(len(self.mutation_)): n += self.lengthString(self.mutation_[i].ByteSizePartial())
    if (self.has_deprecated_mutation_): n += 1 + self.lengthString(self.deprecated_mutation_.ByteSizePartial())
    if (self.has_mode_): n += 1 + self.lengthVarInt64(self.mode_)
    if (self.has_ignore_read_only_): n += 2
    return n

  def Clear(self):
    self.clear_transaction()
    self.clear_mutation()
    self.clear_deprecated_mutation()
    self.clear_mode()
    self.clear_ignore_read_only()

  def OutputUnchecked(self, out):
    if (self.has_transaction_):
      out.putVarInt32(10)
      out.putPrefixedString(self.transaction_)
    if (self.has_deprecated_mutation_):
      out.putVarInt32(18)
      out.putVarInt32(self.deprecated_mutation_.ByteSize())
      self.deprecated_mutation_.OutputUnchecked(out)
    if (self.has_mode_):
      out.putVarInt32(32)
      out.putVarInt32(self.mode_)
    for i in xrange(len(self.mutation_)):
      out.putVarInt32(42)
      out.putVarInt32(self.mutation_[i].ByteSize())
      self.mutation_[i].OutputUnchecked(out)
    if (self.has_ignore_read_only_):
      out.putVarInt32(48)
      out.putBoolean(self.ignore_read_only_)

  def OutputPartial(self, out):
    if (self.has_transaction_):
      out.putVarInt32(10)
      out.putPrefixedString(self.transaction_)
    if (self.has_deprecated_mutation_):
      out.putVarInt32(18)
      out.putVarInt32(self.deprecated_mutation_.ByteSizePartial())
      self.deprecated_mutation_.OutputPartial(out)
    if (self.has_mode_):
      out.putVarInt32(32)
      out.putVarInt32(self.mode_)
    for i in xrange(len(self.mutation_)):
      out.putVarInt32(42)
      out.putVarInt32(self.mutation_[i].ByteSizePartial())
      self.mutation_[i].OutputPartial(out)
    if (self.has_ignore_read_only_):
      out.putVarInt32(48)
      out.putBoolean(self.ignore_read_only_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_transaction(d.getPrefixedString())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_deprecated_mutation().TryMerge(tmp)
        continue
      if tt == 32:
        self.set_mode(d.getVarInt32())
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_mutation().TryMerge(tmp)
        continue
      if tt == 48:
        self.set_ignore_read_only(d.getBoolean())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_transaction_: res+=prefix+("transaction: %s\n" % self.DebugFormatString(self.transaction_))
    cnt=0
    for e in self.mutation_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("mutation%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_deprecated_mutation_:
      res+=prefix+"deprecated_mutation <\n"
      res+=self.deprecated_mutation_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_mode_: res+=prefix+("mode: %s\n" % self.DebugFormatInt32(self.mode_))
    if self.has_ignore_read_only_: res+=prefix+("ignore_read_only: %s\n" % self.DebugFormatBool(self.ignore_read_only_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ktransaction = 1
  kmutation = 5
  kdeprecated_mutation = 2
  kmode = 4
  kignore_read_only = 6

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "transaction",
    2: "deprecated_mutation",
    4: "mode",
    5: "mutation",
    6: "ignore_read_only",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.NUMERIC,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.CommitRequest'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KJWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkNvbW1pdFJlcXVlc3QTGgt0cmFuc2FjdGlvbiABKAIwCTgBFBMaCG11dGF0aW9uIAUoAjALOANKIGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0Lk11dGF0aW9uowGqAQVjdHlwZbIBBnByb3RvMqQBFBMaE2RlcHJlY2F0ZWRfbXV0YXRpb24gAigCMAs4AUoqYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRGVwcmVjYXRlZE11dGF0aW9uowGqAQVjdHlwZbIBBnByb3RvMqQBFBMaBG1vZGUgBCgAMAU4AUIBMWgAowGqAQdkZWZhdWx0sgENVFJBTlNBQ1RJT05BTKQBFBMaEGlnbm9yZV9yZWFkX29ubHkgBigAMAg4AUIFZmFsc2WjAaoBB2RlZmF1bHSyAQVmYWxzZaQBFHN6BE1vZGWLAZIBDVRSQU5TQUNUSU9OQUyYAQGMAYsBkgERTk9OX1RSQU5TQUNUSU9OQUyYAQKMAXTCAR1hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5FcnJvcg=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class CommitResponse(ProtocolBuffer.ProtocolMessage):
  has_deprecated_mutation_result_ = 0
  deprecated_mutation_result_ = None
  has_index_updates_ = 0
  index_updates_ = 0

  def __init__(self, contents=None):
    self.mutation_result_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def mutation_result_size(self): return len(self.mutation_result_)
  def mutation_result_list(self): return self.mutation_result_

  def mutation_result(self, i):
    return self.mutation_result_[i]

  def mutable_mutation_result(self, i):
    return self.mutation_result_[i]

  def add_mutation_result(self):
    x = MutationResult()
    self.mutation_result_.append(x)
    return x

  def clear_mutation_result(self):
    self.mutation_result_ = []
  def deprecated_mutation_result(self):
    if self.deprecated_mutation_result_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.deprecated_mutation_result_ is None: self.deprecated_mutation_result_ = DeprecatedMutationResult()
      finally:
        self.lazy_init_lock_.release()
    return self.deprecated_mutation_result_

  def mutable_deprecated_mutation_result(self): self.has_deprecated_mutation_result_ = 1; return self.deprecated_mutation_result()

  def clear_deprecated_mutation_result(self):

    if self.has_deprecated_mutation_result_:
      self.has_deprecated_mutation_result_ = 0;
      if self.deprecated_mutation_result_ is not None: self.deprecated_mutation_result_.Clear()

  def has_deprecated_mutation_result(self): return self.has_deprecated_mutation_result_

  def index_updates(self): return self.index_updates_

  def set_index_updates(self, x):
    self.has_index_updates_ = 1
    self.index_updates_ = x

  def clear_index_updates(self):
    if self.has_index_updates_:
      self.has_index_updates_ = 0
      self.index_updates_ = 0

  def has_index_updates(self): return self.has_index_updates_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.mutation_result_size()): self.add_mutation_result().CopyFrom(x.mutation_result(i))
    if (x.has_deprecated_mutation_result()): self.mutable_deprecated_mutation_result().MergeFrom(x.deprecated_mutation_result())
    if (x.has_index_updates()): self.set_index_updates(x.index_updates())

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.CommitResponse', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.CommitResponse')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.CommitResponse')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.CommitResponse', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.CommitResponse', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.CommitResponse', s)


  def Equals(self, x):
    if x is self: return 1
    if len(self.mutation_result_) != len(x.mutation_result_): return 0
    for e1, e2 in zip(self.mutation_result_, x.mutation_result_):
      if e1 != e2: return 0
    if self.has_deprecated_mutation_result_ != x.has_deprecated_mutation_result_: return 0
    if self.has_deprecated_mutation_result_ and self.deprecated_mutation_result_ != x.deprecated_mutation_result_: return 0
    if self.has_index_updates_ != x.has_index_updates_: return 0
    if self.has_index_updates_ and self.index_updates_ != x.index_updates_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.mutation_result_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_deprecated_mutation_result_ and not self.deprecated_mutation_result_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.mutation_result_)
    for i in xrange(len(self.mutation_result_)): n += self.lengthString(self.mutation_result_[i].ByteSize())
    if (self.has_deprecated_mutation_result_): n += 1 + self.lengthString(self.deprecated_mutation_result_.ByteSize())
    if (self.has_index_updates_): n += 1 + self.lengthVarInt64(self.index_updates_)
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.mutation_result_)
    for i in xrange(len(self.mutation_result_)): n += self.lengthString(self.mutation_result_[i].ByteSizePartial())
    if (self.has_deprecated_mutation_result_): n += 1 + self.lengthString(self.deprecated_mutation_result_.ByteSizePartial())
    if (self.has_index_updates_): n += 1 + self.lengthVarInt64(self.index_updates_)
    return n

  def Clear(self):
    self.clear_mutation_result()
    self.clear_deprecated_mutation_result()
    self.clear_index_updates()

  def OutputUnchecked(self, out):
    if (self.has_deprecated_mutation_result_):
      out.putVarInt32(10)
      out.putVarInt32(self.deprecated_mutation_result_.ByteSize())
      self.deprecated_mutation_result_.OutputUnchecked(out)
    for i in xrange(len(self.mutation_result_)):
      out.putVarInt32(26)
      out.putVarInt32(self.mutation_result_[i].ByteSize())
      self.mutation_result_[i].OutputUnchecked(out)
    if (self.has_index_updates_):
      out.putVarInt32(32)
      out.putVarInt32(self.index_updates_)

  def OutputPartial(self, out):
    if (self.has_deprecated_mutation_result_):
      out.putVarInt32(10)
      out.putVarInt32(self.deprecated_mutation_result_.ByteSizePartial())
      self.deprecated_mutation_result_.OutputPartial(out)
    for i in xrange(len(self.mutation_result_)):
      out.putVarInt32(26)
      out.putVarInt32(self.mutation_result_[i].ByteSizePartial())
      self.mutation_result_[i].OutputPartial(out)
    if (self.has_index_updates_):
      out.putVarInt32(32)
      out.putVarInt32(self.index_updates_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_deprecated_mutation_result().TryMerge(tmp)
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_mutation_result().TryMerge(tmp)
        continue
      if tt == 32:
        self.set_index_updates(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.mutation_result_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("mutation_result%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_deprecated_mutation_result_:
      res+=prefix+"deprecated_mutation_result <\n"
      res+=self.deprecated_mutation_result_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_index_updates_: res+=prefix+("index_updates: %s\n" % self.DebugFormatInt32(self.index_updates_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kmutation_result = 3
  kdeprecated_mutation_result = 1
  kindex_updates = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "deprecated_mutation_result",
    3: "mutation_result",
    4: "index_updates",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.NUMERIC,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.CommitResponse'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KJmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkNvbW1pdFJlc3BvbnNlExoPbXV0YXRpb25fcmVzdWx0IAMoAjALOANKJmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0Lk11dGF0aW9uUmVzdWx0owGqAQVjdHlwZbIBBnByb3RvMqQBFBMaGmRlcHJlY2F0ZWRfbXV0YXRpb25fcmVzdWx0IAEoAjALOAFKMGFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkRlcHJlY2F0ZWRNdXRhdGlvblJlc3VsdKMBqgEFY3R5cGWyAQZwcm90bzKkARQTGg1pbmRleF91cGRhdGVzIAQoADAFOAEUwgEdYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuRXJyb3I="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class AllocateIdsRequest(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.allocate_ = []
    self.reserve_ = []
    if contents is not None: self.MergeFromString(contents)

  def allocate_size(self): return len(self.allocate_)
  def allocate_list(self): return self.allocate_

  def allocate(self, i):
    return self.allocate_[i]

  def mutable_allocate(self, i):
    return self.allocate_[i]

  def add_allocate(self):
    x = google.appengine.datastore.entity_v4_pb.Key()
    self.allocate_.append(x)
    return x

  def clear_allocate(self):
    self.allocate_ = []
  def reserve_size(self): return len(self.reserve_)
  def reserve_list(self): return self.reserve_

  def reserve(self, i):
    return self.reserve_[i]

  def mutable_reserve(self, i):
    return self.reserve_[i]

  def add_reserve(self):
    x = google.appengine.datastore.entity_v4_pb.Key()
    self.reserve_.append(x)
    return x

  def clear_reserve(self):
    self.reserve_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.allocate_size()): self.add_allocate().CopyFrom(x.allocate(i))
    for i in xrange(x.reserve_size()): self.add_reserve().CopyFrom(x.reserve(i))

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.AllocateIdsRequest', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.AllocateIdsRequest')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.AllocateIdsRequest')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.AllocateIdsRequest', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.AllocateIdsRequest', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.AllocateIdsRequest', s)


  def Equals(self, x):
    if x is self: return 1
    if len(self.allocate_) != len(x.allocate_): return 0
    for e1, e2 in zip(self.allocate_, x.allocate_):
      if e1 != e2: return 0
    if len(self.reserve_) != len(x.reserve_): return 0
    for e1, e2 in zip(self.reserve_, x.reserve_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.allocate_:
      if not p.IsInitialized(debug_strs): initialized=0
    for p in self.reserve_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.allocate_)
    for i in xrange(len(self.allocate_)): n += self.lengthString(self.allocate_[i].ByteSize())
    n += 1 * len(self.reserve_)
    for i in xrange(len(self.reserve_)): n += self.lengthString(self.reserve_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.allocate_)
    for i in xrange(len(self.allocate_)): n += self.lengthString(self.allocate_[i].ByteSizePartial())
    n += 1 * len(self.reserve_)
    for i in xrange(len(self.reserve_)): n += self.lengthString(self.reserve_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_allocate()
    self.clear_reserve()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.allocate_)):
      out.putVarInt32(10)
      out.putVarInt32(self.allocate_[i].ByteSize())
      self.allocate_[i].OutputUnchecked(out)
    for i in xrange(len(self.reserve_)):
      out.putVarInt32(18)
      out.putVarInt32(self.reserve_[i].ByteSize())
      self.reserve_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.allocate_)):
      out.putVarInt32(10)
      out.putVarInt32(self.allocate_[i].ByteSizePartial())
      self.allocate_[i].OutputPartial(out)
    for i in xrange(len(self.reserve_)):
      out.putVarInt32(18)
      out.putVarInt32(self.reserve_[i].ByteSizePartial())
      self.reserve_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_allocate().TryMerge(tmp)
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_reserve().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.allocate_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("allocate%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    cnt=0
    for e in self.reserve_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("reserve%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kallocate = 1
  kreserve = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "allocate",
    2: "reserve",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.AllocateIdsRequest'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KKmFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkFsbG9jYXRlSWRzUmVxdWVzdBMaCGFsbG9jYXRlIAEoAjALOANKG2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktleaMBqgEFY3R5cGWyAQZwcm90bzKkARQTGgdyZXNlcnZlIAIoAjALOANKG2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LktleaMBqgEFY3R5cGWyAQZwcm90bzKkARTCAR1hcHBob3N0aW5nLmRhdGFzdG9yZS52NC5FcnJvcg=="))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())

class AllocateIdsResponse(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.allocated_ = []
    if contents is not None: self.MergeFromString(contents)

  def allocated_size(self): return len(self.allocated_)
  def allocated_list(self): return self.allocated_

  def allocated(self, i):
    return self.allocated_[i]

  def mutable_allocated(self, i):
    return self.allocated_[i]

  def add_allocated(self):
    x = google.appengine.datastore.entity_v4_pb.Key()
    self.allocated_.append(x)
    return x

  def clear_allocated(self):
    self.allocated_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.allocated_size()): self.add_allocated().CopyFrom(x.allocated(i))

  if _net_proto___parse__python is not None:
    def _CMergeFromString(self, s):
      _net_proto___parse__python.MergeFromString(self, 'apphosting.datastore.v4.AllocateIdsResponse', s)

  if _net_proto___parse__python is not None:
    def _CEncode(self):
      return _net_proto___parse__python.Encode(self, 'apphosting.datastore.v4.AllocateIdsResponse')

  if _net_proto___parse__python is not None:
    def _CEncodePartial(self):
      return _net_proto___parse__python.EncodePartial(self, 'apphosting.datastore.v4.AllocateIdsResponse')

  if _net_proto___parse__python is not None:
    def _CToASCII(self, output_format):
      return _net_proto___parse__python.ToASCII(self, 'apphosting.datastore.v4.AllocateIdsResponse', output_format)


  if _net_proto___parse__python is not None:
    def ParseASCII(self, s):
      _net_proto___parse__python.ParseASCII(self, 'apphosting.datastore.v4.AllocateIdsResponse', s)


  if _net_proto___parse__python is not None:
    def ParseASCIIIgnoreUnknown(self, s):
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(self, 'apphosting.datastore.v4.AllocateIdsResponse', s)


  def Equals(self, x):
    if x is self: return 1
    if len(self.allocated_) != len(x.allocated_): return 0
    for e1, e2 in zip(self.allocated_, x.allocated_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.allocated_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.allocated_)
    for i in xrange(len(self.allocated_)): n += self.lengthString(self.allocated_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.allocated_)
    for i in xrange(len(self.allocated_)): n += self.lengthString(self.allocated_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_allocated()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.allocated_)):
      out.putVarInt32(10)
      out.putVarInt32(self.allocated_[i].ByteSize())
      self.allocated_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.allocated_)):
      out.putVarInt32(10)
      out.putVarInt32(self.allocated_[i].ByteSizePartial())
      self.allocated_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_allocated().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.allocated_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("allocated%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kallocated = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "allocated",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.datastore.v4.AllocateIdsResponse'
  _SERIALIZED_DESCRIPTOR = array.array('B')
  _SERIALIZED_DESCRIPTOR.fromstring(base64.decodestring("WidhcHBob3N0aW5nL2RhdGFzdG9yZS9kYXRhc3RvcmVfdjQucHJvdG8KK2FwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkFsbG9jYXRlSWRzUmVzcG9uc2UTGglhbGxvY2F0ZWQgASgCMAs4A0obYXBwaG9zdGluZy5kYXRhc3RvcmUudjQuS2V5owGqAQVjdHlwZbIBBnByb3RvMqQBFMIBHWFwcGhvc3RpbmcuZGF0YXN0b3JlLnY0LkVycm9y"))
  if _net_proto___parse__python is not None:
    _net_proto___parse__python.RegisterType(
        _SERIALIZED_DESCRIPTOR.tostring())



class _DatastoreV4Service_ClientBaseStub(_client_stub_base_class):
  """Makes Stubby RPC calls to a DatastoreV4Service server."""

  __slots__ = (
      '_protorpc_BeginTransaction', '_full_name_BeginTransaction',
      '_protorpc_Rollback', '_full_name_Rollback',
      '_protorpc_Commit', '_full_name_Commit',
      '_protorpc_RunQuery', '_full_name_RunQuery',
      '_protorpc_ContinueQuery', '_full_name_ContinueQuery',
      '_protorpc_Lookup', '_full_name_Lookup',
      '_protorpc_AllocateIds', '_full_name_AllocateIds',
  )

  def __init__(self, rpc_stub):
    self._stub = rpc_stub

    self._protorpc_BeginTransaction = pywraprpc.RPC()
    self._full_name_BeginTransaction = self._stub.GetFullMethodName(
        'BeginTransaction')

    self._protorpc_Rollback = pywraprpc.RPC()
    self._full_name_Rollback = self._stub.GetFullMethodName(
        'Rollback')

    self._protorpc_Commit = pywraprpc.RPC()
    self._full_name_Commit = self._stub.GetFullMethodName(
        'Commit')

    self._protorpc_RunQuery = pywraprpc.RPC()
    self._full_name_RunQuery = self._stub.GetFullMethodName(
        'RunQuery')

    self._protorpc_ContinueQuery = pywraprpc.RPC()
    self._full_name_ContinueQuery = self._stub.GetFullMethodName(
        'ContinueQuery')

    self._protorpc_Lookup = pywraprpc.RPC()
    self._full_name_Lookup = self._stub.GetFullMethodName(
        'Lookup')

    self._protorpc_AllocateIds = pywraprpc.RPC()
    self._full_name_AllocateIds = self._stub.GetFullMethodName(
        'AllocateIds')

  def BeginTransaction(self, request, rpc=None, callback=None, response=None):
    """Make a BeginTransaction RPC call.

    Args:
      request: a BeginTransactionRequest instance.
      rpc: Optional RPC instance to use for the call.
      callback: Optional final callback. Will be called as
          callback(rpc, result) when the rpc completes. If None, the
          call is synchronous.
      response: Optional ProtocolMessage to be filled in with response.

    Returns:
      The BeginTransactionResponse if callback is None. Otherwise, returns None.
    """

    if response is None:
      response = BeginTransactionResponse
    return self._MakeCall(rpc,
                          self._full_name_BeginTransaction,
                          'BeginTransaction',
                          request,
                          response,
                          callback,
                          self._protorpc_BeginTransaction,
                          package_name='apphosting.datastore.v4')

  def Rollback(self, request, rpc=None, callback=None, response=None):
    """Make a Rollback RPC call.

    Args:
      request: a RollbackRequest instance.
      rpc: Optional RPC instance to use for the call.
      callback: Optional final callback. Will be called as
          callback(rpc, result) when the rpc completes. If None, the
          call is synchronous.
      response: Optional ProtocolMessage to be filled in with response.

    Returns:
      The RollbackResponse if callback is None. Otherwise, returns None.
    """

    if response is None:
      response = RollbackResponse
    return self._MakeCall(rpc,
                          self._full_name_Rollback,
                          'Rollback',
                          request,
                          response,
                          callback,
                          self._protorpc_Rollback,
                          package_name='apphosting.datastore.v4')

  def Commit(self, request, rpc=None, callback=None, response=None):
    """Make a Commit RPC call.

    Args:
      request: a CommitRequest instance.
      rpc: Optional RPC instance to use for the call.
      callback: Optional final callback. Will be called as
          callback(rpc, result) when the rpc completes. If None, the
          call is synchronous.
      response: Optional ProtocolMessage to be filled in with response.

    Returns:
      The CommitResponse if callback is None. Otherwise, returns None.
    """

    if response is None:
      response = CommitResponse
    return self._MakeCall(rpc,
                          self._full_name_Commit,
                          'Commit',
                          request,
                          response,
                          callback,
                          self._protorpc_Commit,
                          package_name='apphosting.datastore.v4')

  def RunQuery(self, request, rpc=None, callback=None, response=None):
    """Make a RunQuery RPC call.

    Args:
      request: a RunQueryRequest instance.
      rpc: Optional RPC instance to use for the call.
      callback: Optional final callback. Will be called as
          callback(rpc, result) when the rpc completes. If None, the
          call is synchronous.
      response: Optional ProtocolMessage to be filled in with response.

    Returns:
      The RunQueryResponse if callback is None. Otherwise, returns None.
    """

    if response is None:
      response = RunQueryResponse
    return self._MakeCall(rpc,
                          self._full_name_RunQuery,
                          'RunQuery',
                          request,
                          response,
                          callback,
                          self._protorpc_RunQuery,
                          package_name='apphosting.datastore.v4')

  def ContinueQuery(self, request, rpc=None, callback=None, response=None):
    """Make a ContinueQuery RPC call.

    Args:
      request: a ContinueQueryRequest instance.
      rpc: Optional RPC instance to use for the call.
      callback: Optional final callback. Will be called as
          callback(rpc, result) when the rpc completes. If None, the
          call is synchronous.
      response: Optional ProtocolMessage to be filled in with response.

    Returns:
      The ContinueQueryResponse if callback is None. Otherwise, returns None.
    """

    if response is None:
      response = ContinueQueryResponse
    return self._MakeCall(rpc,
                          self._full_name_ContinueQuery,
                          'ContinueQuery',
                          request,
                          response,
                          callback,
                          self._protorpc_ContinueQuery,
                          package_name='apphosting.datastore.v4')

  def Lookup(self, request, rpc=None, callback=None, response=None):
    """Make a Lookup RPC call.

    Args:
      request: a LookupRequest instance.
      rpc: Optional RPC instance to use for the call.
      callback: Optional final callback. Will be called as
          callback(rpc, result) when the rpc completes. If None, the
          call is synchronous.
      response: Optional ProtocolMessage to be filled in with response.

    Returns:
      The LookupResponse if callback is None. Otherwise, returns None.
    """

    if response is None:
      response = LookupResponse
    return self._MakeCall(rpc,
                          self._full_name_Lookup,
                          'Lookup',
                          request,
                          response,
                          callback,
                          self._protorpc_Lookup,
                          package_name='apphosting.datastore.v4')

  def AllocateIds(self, request, rpc=None, callback=None, response=None):
    """Make a AllocateIds RPC call.

    Args:
      request: a AllocateIdsRequest instance.
      rpc: Optional RPC instance to use for the call.
      callback: Optional final callback. Will be called as
          callback(rpc, result) when the rpc completes. If None, the
          call is synchronous.
      response: Optional ProtocolMessage to be filled in with response.

    Returns:
      The AllocateIdsResponse if callback is None. Otherwise, returns None.
    """

    if response is None:
      response = AllocateIdsResponse
    return self._MakeCall(rpc,
                          self._full_name_AllocateIds,
                          'AllocateIds',
                          request,
                          response,
                          callback,
                          self._protorpc_AllocateIds,
                          package_name='apphosting.datastore.v4')


class _DatastoreV4Service_ClientStub(_DatastoreV4Service_ClientBaseStub):
  __slots__ = ('_params',)
  def __init__(self, rpc_stub_parameters, service_name):
    if service_name is None:
      service_name = 'DatastoreV4Service'
    _DatastoreV4Service_ClientBaseStub.__init__(self, pywraprpc.RPC_GenericStub(service_name, rpc_stub_parameters))
    self._params = rpc_stub_parameters


class _DatastoreV4Service_RPC2ClientStub(_DatastoreV4Service_ClientBaseStub):
  __slots__ = ()
  def __init__(self, server, channel, service_name):
    if service_name is None:
      service_name = 'DatastoreV4Service'
    if channel is not None:
      if channel.version() == 1:
        raise RuntimeError('Expecting an RPC2 channel to create the stub')
      _DatastoreV4Service_ClientBaseStub.__init__(self, pywraprpc.RPC_GenericStub(service_name, channel))
    elif server is not None:
      _DatastoreV4Service_ClientBaseStub.__init__(self, pywraprpc.RPC_GenericStub(service_name, pywraprpc.NewClientChannel(server)))
    else:
      raise RuntimeError('Invalid argument combination to create a stub')


class DatastoreV4Service(_server_stub_base_class):
  """Base class for DatastoreV4Service Stubby servers."""

  @classmethod
  def _MethodSignatures(cls):
    """Returns a dict of {<method-name>: (<request-type>, <response-type>)}."""
    return {
      'BeginTransaction': (BeginTransactionRequest, BeginTransactionResponse),
      'Rollback': (RollbackRequest, RollbackResponse),
      'Commit': (CommitRequest, CommitResponse),
      'RunQuery': (RunQueryRequest, RunQueryResponse),
      'ContinueQuery': (ContinueQueryRequest, ContinueQueryResponse),
      'Lookup': (LookupRequest, LookupResponse),
      'AllocateIds': (AllocateIdsRequest, AllocateIdsResponse),
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
    _server_stub_base_class.__init__(self, 'apphosting.datastore.v4.DatastoreV4Service', *args, **kwargs)

  @staticmethod
  def NewStub(rpc_stub_parameters, service_name=None):
    """Creates a new DatastoreV4Service Stubby client stub.

    Args:
      rpc_stub_parameters: an RPC_StubParameters instance.
      service_name: the service name used by the Stubby server.
    """

    if _client_stub_base_class is object:
      raise RuntimeError('Add //net/rpc/python as a dependency to use Stubby')
    return _DatastoreV4Service_ClientStub(rpc_stub_parameters, service_name)

  @staticmethod
  def NewRPC2Stub(server=None, channel=None, service_name=None):
    """Creates a new DatastoreV4Service Stubby2 client stub.

    Args:
      server: host:port or bns address.
      channel: directly use a channel to create a stub. Will ignore server
          argument if this is specified.
      service_name: the service name used by the Stubby server.
    """

    if _client_stub_base_class is object:
      raise RuntimeError('Add //net/rpc/python as a dependency to use Stubby')
    return _DatastoreV4Service_RPC2ClientStub(server, channel, service_name)

  def BeginTransaction(self, rpc, request, response):
    """Handles a BeginTransaction RPC call. You should override this.

    Args:
      rpc: a Stubby RPC object
      request: a BeginTransactionRequest that contains the client request
      response: a BeginTransactionResponse that should be modified to send the response
    """
    raise NotImplementedError


  def Rollback(self, rpc, request, response):
    """Handles a Rollback RPC call. You should override this.

    Args:
      rpc: a Stubby RPC object
      request: a RollbackRequest that contains the client request
      response: a RollbackResponse that should be modified to send the response
    """
    raise NotImplementedError


  def Commit(self, rpc, request, response):
    """Handles a Commit RPC call. You should override this.

    Args:
      rpc: a Stubby RPC object
      request: a CommitRequest that contains the client request
      response: a CommitResponse that should be modified to send the response
    """
    raise NotImplementedError


  def RunQuery(self, rpc, request, response):
    """Handles a RunQuery RPC call. You should override this.

    Args:
      rpc: a Stubby RPC object
      request: a RunQueryRequest that contains the client request
      response: a RunQueryResponse that should be modified to send the response
    """
    raise NotImplementedError


  def ContinueQuery(self, rpc, request, response):
    """Handles a ContinueQuery RPC call. You should override this.

    Args:
      rpc: a Stubby RPC object
      request: a ContinueQueryRequest that contains the client request
      response: a ContinueQueryResponse that should be modified to send the response
    """
    raise NotImplementedError


  def Lookup(self, rpc, request, response):
    """Handles a Lookup RPC call. You should override this.

    Args:
      rpc: a Stubby RPC object
      request: a LookupRequest that contains the client request
      response: a LookupResponse that should be modified to send the response
    """
    raise NotImplementedError


  def AllocateIds(self, rpc, request, response):
    """Handles a AllocateIds RPC call. You should override this.

    Args:
      rpc: a Stubby RPC object
      request: a AllocateIdsRequest that contains the client request
      response: a AllocateIdsResponse that should be modified to send the response
    """
    raise NotImplementedError

  def _AddMethodAttributes(self):
    """Sets attributes on Python RPC handlers.

    See BaseRpcServer in rpcserver.py for details.
    """
    rpcserver._GetHandlerDecorator(
        getattr(self.BeginTransaction, '__func__'),
        BeginTransactionRequest,
        BeginTransactionResponse,
        None,
        'INTEGRITY')
    rpcserver._GetHandlerDecorator(
        getattr(self.Rollback, '__func__'),
        RollbackRequest,
        RollbackResponse,
        None,
        'INTEGRITY')
    rpcserver._GetHandlerDecorator(
        getattr(self.Commit, '__func__'),
        CommitRequest,
        CommitResponse,
        None,
        'INTEGRITY')
    rpcserver._GetHandlerDecorator(
        getattr(self.RunQuery, '__func__'),
        RunQueryRequest,
        RunQueryResponse,
        None,
        'INTEGRITY')
    rpcserver._GetHandlerDecorator(
        getattr(self.ContinueQuery, '__func__'),
        ContinueQueryRequest,
        ContinueQueryResponse,
        None,
        'INTEGRITY')
    rpcserver._GetHandlerDecorator(
        getattr(self.Lookup, '__func__'),
        LookupRequest,
        LookupResponse,
        None,
        'INTEGRITY')
    rpcserver._GetHandlerDecorator(
        getattr(self.AllocateIds, '__func__'),
        AllocateIdsRequest,
        AllocateIdsResponse,
        None,
        'INTEGRITY')

if _extension_runtime:
  pass

__all__ = ['Error','EntityResult','Query','KindExpression','PropertyReference','PropertyExpression','PropertyOrder','Filter','CompositeFilter','PropertyFilter','GqlQuery','GqlQueryArg','QueryResultBatch','Mutation','MutationResult','DeprecatedMutation','DeprecatedMutationResult','ReadOptions','LookupRequest','LookupResponse','RunQueryRequest','RunQueryResponse','ContinueQueryRequest','ContinueQueryResponse','BeginTransactionRequest','BeginTransactionResponse','RollbackRequest','RollbackResponse','CommitRequest','CommitResponse','AllocateIdsRequest','AllocateIdsResponse','DatastoreV4Service']
