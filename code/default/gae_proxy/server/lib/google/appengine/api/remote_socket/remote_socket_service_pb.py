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

class RemoteSocketServiceError(ProtocolBuffer.ProtocolMessage):


  SYSTEM_ERROR =    1
  GAI_ERROR    =    2
  FAILURE      =    4
  PERMISSION_DENIED =    5
  INVALID_REQUEST =    6
  SOCKET_CLOSED =    7

  _ErrorCode_NAMES = {
    1: "SYSTEM_ERROR",
    2: "GAI_ERROR",
    4: "FAILURE",
    5: "PERMISSION_DENIED",
    6: "INVALID_REQUEST",
    7: "SOCKET_CLOSED",
  }

  def ErrorCode_Name(cls, x): return cls._ErrorCode_NAMES.get(x, "")
  ErrorCode_Name = classmethod(ErrorCode_Name)



  SYS_SUCCESS  =    0
  SYS_EPERM    =    1
  SYS_ENOENT   =    2
  SYS_ESRCH    =    3
  SYS_EINTR    =    4
  SYS_EIO      =    5
  SYS_ENXIO    =    6
  SYS_E2BIG    =    7
  SYS_ENOEXEC  =    8
  SYS_EBADF    =    9
  SYS_ECHILD   =   10
  SYS_EAGAIN   =   11
  SYS_EWOULDBLOCK =   11
  SYS_ENOMEM   =   12
  SYS_EACCES   =   13
  SYS_EFAULT   =   14
  SYS_ENOTBLK  =   15
  SYS_EBUSY    =   16
  SYS_EEXIST   =   17
  SYS_EXDEV    =   18
  SYS_ENODEV   =   19
  SYS_ENOTDIR  =   20
  SYS_EISDIR   =   21
  SYS_EINVAL   =   22
  SYS_ENFILE   =   23
  SYS_EMFILE   =   24
  SYS_ENOTTY   =   25
  SYS_ETXTBSY  =   26
  SYS_EFBIG    =   27
  SYS_ENOSPC   =   28
  SYS_ESPIPE   =   29
  SYS_EROFS    =   30
  SYS_EMLINK   =   31
  SYS_EPIPE    =   32
  SYS_EDOM     =   33
  SYS_ERANGE   =   34
  SYS_EDEADLK  =   35
  SYS_EDEADLOCK =   35
  SYS_ENAMETOOLONG =   36
  SYS_ENOLCK   =   37
  SYS_ENOSYS   =   38
  SYS_ENOTEMPTY =   39
  SYS_ELOOP    =   40
  SYS_ENOMSG   =   42
  SYS_EIDRM    =   43
  SYS_ECHRNG   =   44
  SYS_EL2NSYNC =   45
  SYS_EL3HLT   =   46
  SYS_EL3RST   =   47
  SYS_ELNRNG   =   48
  SYS_EUNATCH  =   49
  SYS_ENOCSI   =   50
  SYS_EL2HLT   =   51
  SYS_EBADE    =   52
  SYS_EBADR    =   53
  SYS_EXFULL   =   54
  SYS_ENOANO   =   55
  SYS_EBADRQC  =   56
  SYS_EBADSLT  =   57
  SYS_EBFONT   =   59
  SYS_ENOSTR   =   60
  SYS_ENODATA  =   61
  SYS_ETIME    =   62
  SYS_ENOSR    =   63
  SYS_ENONET   =   64
  SYS_ENOPKG   =   65
  SYS_EREMOTE  =   66
  SYS_ENOLINK  =   67
  SYS_EADV     =   68
  SYS_ESRMNT   =   69
  SYS_ECOMM    =   70
  SYS_EPROTO   =   71
  SYS_EMULTIHOP =   72
  SYS_EDOTDOT  =   73
  SYS_EBADMSG  =   74
  SYS_EOVERFLOW =   75
  SYS_ENOTUNIQ =   76
  SYS_EBADFD   =   77
  SYS_EREMCHG  =   78
  SYS_ELIBACC  =   79
  SYS_ELIBBAD  =   80
  SYS_ELIBSCN  =   81
  SYS_ELIBMAX  =   82
  SYS_ELIBEXEC =   83
  SYS_EILSEQ   =   84
  SYS_ERESTART =   85
  SYS_ESTRPIPE =   86
  SYS_EUSERS   =   87
  SYS_ENOTSOCK =   88
  SYS_EDESTADDRREQ =   89
  SYS_EMSGSIZE =   90
  SYS_EPROTOTYPE =   91
  SYS_ENOPROTOOPT =   92
  SYS_EPROTONOSUPPORT =   93
  SYS_ESOCKTNOSUPPORT =   94
  SYS_EOPNOTSUPP =   95
  SYS_ENOTSUP  =   95
  SYS_EPFNOSUPPORT =   96
  SYS_EAFNOSUPPORT =   97
  SYS_EADDRINUSE =   98
  SYS_EADDRNOTAVAIL =   99
  SYS_ENETDOWN =  100
  SYS_ENETUNREACH =  101
  SYS_ENETRESET =  102
  SYS_ECONNABORTED =  103
  SYS_ECONNRESET =  104
  SYS_ENOBUFS  =  105
  SYS_EISCONN  =  106
  SYS_ENOTCONN =  107
  SYS_ESHUTDOWN =  108
  SYS_ETOOMANYREFS =  109
  SYS_ETIMEDOUT =  110
  SYS_ECONNREFUSED =  111
  SYS_EHOSTDOWN =  112
  SYS_EHOSTUNREACH =  113
  SYS_EALREADY =  114
  SYS_EINPROGRESS =  115
  SYS_ESTALE   =  116
  SYS_EUCLEAN  =  117
  SYS_ENOTNAM  =  118
  SYS_ENAVAIL  =  119
  SYS_EISNAM   =  120
  SYS_EREMOTEIO =  121
  SYS_EDQUOT   =  122
  SYS_ENOMEDIUM =  123
  SYS_EMEDIUMTYPE =  124
  SYS_ECANCELED =  125
  SYS_ENOKEY   =  126
  SYS_EKEYEXPIRED =  127
  SYS_EKEYREVOKED =  128
  SYS_EKEYREJECTED =  129
  SYS_EOWNERDEAD =  130
  SYS_ENOTRECOVERABLE =  131
  SYS_ERFKILL  =  132

  _SystemError_NAMES = {
    0: "SYS_SUCCESS",
    1: "SYS_EPERM",
    2: "SYS_ENOENT",
    3: "SYS_ESRCH",
    4: "SYS_EINTR",
    5: "SYS_EIO",
    6: "SYS_ENXIO",
    7: "SYS_E2BIG",
    8: "SYS_ENOEXEC",
    9: "SYS_EBADF",
    10: "SYS_ECHILD",
    11: "SYS_EAGAIN",
    11: "SYS_EWOULDBLOCK",
    12: "SYS_ENOMEM",
    13: "SYS_EACCES",
    14: "SYS_EFAULT",
    15: "SYS_ENOTBLK",
    16: "SYS_EBUSY",
    17: "SYS_EEXIST",
    18: "SYS_EXDEV",
    19: "SYS_ENODEV",
    20: "SYS_ENOTDIR",
    21: "SYS_EISDIR",
    22: "SYS_EINVAL",
    23: "SYS_ENFILE",
    24: "SYS_EMFILE",
    25: "SYS_ENOTTY",
    26: "SYS_ETXTBSY",
    27: "SYS_EFBIG",
    28: "SYS_ENOSPC",
    29: "SYS_ESPIPE",
    30: "SYS_EROFS",
    31: "SYS_EMLINK",
    32: "SYS_EPIPE",
    33: "SYS_EDOM",
    34: "SYS_ERANGE",
    35: "SYS_EDEADLK",
    35: "SYS_EDEADLOCK",
    36: "SYS_ENAMETOOLONG",
    37: "SYS_ENOLCK",
    38: "SYS_ENOSYS",
    39: "SYS_ENOTEMPTY",
    40: "SYS_ELOOP",
    42: "SYS_ENOMSG",
    43: "SYS_EIDRM",
    44: "SYS_ECHRNG",
    45: "SYS_EL2NSYNC",
    46: "SYS_EL3HLT",
    47: "SYS_EL3RST",
    48: "SYS_ELNRNG",
    49: "SYS_EUNATCH",
    50: "SYS_ENOCSI",
    51: "SYS_EL2HLT",
    52: "SYS_EBADE",
    53: "SYS_EBADR",
    54: "SYS_EXFULL",
    55: "SYS_ENOANO",
    56: "SYS_EBADRQC",
    57: "SYS_EBADSLT",
    59: "SYS_EBFONT",
    60: "SYS_ENOSTR",
    61: "SYS_ENODATA",
    62: "SYS_ETIME",
    63: "SYS_ENOSR",
    64: "SYS_ENONET",
    65: "SYS_ENOPKG",
    66: "SYS_EREMOTE",
    67: "SYS_ENOLINK",
    68: "SYS_EADV",
    69: "SYS_ESRMNT",
    70: "SYS_ECOMM",
    71: "SYS_EPROTO",
    72: "SYS_EMULTIHOP",
    73: "SYS_EDOTDOT",
    74: "SYS_EBADMSG",
    75: "SYS_EOVERFLOW",
    76: "SYS_ENOTUNIQ",
    77: "SYS_EBADFD",
    78: "SYS_EREMCHG",
    79: "SYS_ELIBACC",
    80: "SYS_ELIBBAD",
    81: "SYS_ELIBSCN",
    82: "SYS_ELIBMAX",
    83: "SYS_ELIBEXEC",
    84: "SYS_EILSEQ",
    85: "SYS_ERESTART",
    86: "SYS_ESTRPIPE",
    87: "SYS_EUSERS",
    88: "SYS_ENOTSOCK",
    89: "SYS_EDESTADDRREQ",
    90: "SYS_EMSGSIZE",
    91: "SYS_EPROTOTYPE",
    92: "SYS_ENOPROTOOPT",
    93: "SYS_EPROTONOSUPPORT",
    94: "SYS_ESOCKTNOSUPPORT",
    95: "SYS_EOPNOTSUPP",
    95: "SYS_ENOTSUP",
    96: "SYS_EPFNOSUPPORT",
    97: "SYS_EAFNOSUPPORT",
    98: "SYS_EADDRINUSE",
    99: "SYS_EADDRNOTAVAIL",
    100: "SYS_ENETDOWN",
    101: "SYS_ENETUNREACH",
    102: "SYS_ENETRESET",
    103: "SYS_ECONNABORTED",
    104: "SYS_ECONNRESET",
    105: "SYS_ENOBUFS",
    106: "SYS_EISCONN",
    107: "SYS_ENOTCONN",
    108: "SYS_ESHUTDOWN",
    109: "SYS_ETOOMANYREFS",
    110: "SYS_ETIMEDOUT",
    111: "SYS_ECONNREFUSED",
    112: "SYS_EHOSTDOWN",
    113: "SYS_EHOSTUNREACH",
    114: "SYS_EALREADY",
    115: "SYS_EINPROGRESS",
    116: "SYS_ESTALE",
    117: "SYS_EUCLEAN",
    118: "SYS_ENOTNAM",
    119: "SYS_ENAVAIL",
    120: "SYS_EISNAM",
    121: "SYS_EREMOTEIO",
    122: "SYS_EDQUOT",
    123: "SYS_ENOMEDIUM",
    124: "SYS_EMEDIUMTYPE",
    125: "SYS_ECANCELED",
    126: "SYS_ENOKEY",
    127: "SYS_EKEYEXPIRED",
    128: "SYS_EKEYREVOKED",
    129: "SYS_EKEYREJECTED",
    130: "SYS_EOWNERDEAD",
    131: "SYS_ENOTRECOVERABLE",
    132: "SYS_ERFKILL",
  }

  def SystemError_Name(cls, x): return cls._SystemError_NAMES.get(x, "")
  SystemError_Name = classmethod(SystemError_Name)

  has_system_error_ = 0
  system_error_ = 0
  has_error_detail_ = 0
  error_detail_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def system_error(self): return self.system_error_

  def set_system_error(self, x):
    self.has_system_error_ = 1
    self.system_error_ = x

  def clear_system_error(self):
    if self.has_system_error_:
      self.has_system_error_ = 0
      self.system_error_ = 0

  def has_system_error(self): return self.has_system_error_

  def error_detail(self): return self.error_detail_

  def set_error_detail(self, x):
    self.has_error_detail_ = 1
    self.error_detail_ = x

  def clear_error_detail(self):
    if self.has_error_detail_:
      self.has_error_detail_ = 0
      self.error_detail_ = ""

  def has_error_detail(self): return self.has_error_detail_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_system_error()): self.set_system_error(x.system_error())
    if (x.has_error_detail()): self.set_error_detail(x.error_detail())

  def Equals(self, x):
    if x is self: return 1
    if self.has_system_error_ != x.has_system_error_: return 0
    if self.has_system_error_ and self.system_error_ != x.system_error_: return 0
    if self.has_error_detail_ != x.has_error_detail_: return 0
    if self.has_error_detail_ and self.error_detail_ != x.error_detail_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_system_error_): n += 1 + self.lengthVarInt64(self.system_error_)
    if (self.has_error_detail_): n += 1 + self.lengthString(len(self.error_detail_))
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_system_error_): n += 1 + self.lengthVarInt64(self.system_error_)
    if (self.has_error_detail_): n += 1 + self.lengthString(len(self.error_detail_))
    return n

  def Clear(self):
    self.clear_system_error()
    self.clear_error_detail()

  def OutputUnchecked(self, out):
    if (self.has_system_error_):
      out.putVarInt32(8)
      out.putVarInt32(self.system_error_)
    if (self.has_error_detail_):
      out.putVarInt32(18)
      out.putPrefixedString(self.error_detail_)

  def OutputPartial(self, out):
    if (self.has_system_error_):
      out.putVarInt32(8)
      out.putVarInt32(self.system_error_)
    if (self.has_error_detail_):
      out.putVarInt32(18)
      out.putPrefixedString(self.error_detail_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_system_error(d.getVarInt32())
        continue
      if tt == 18:
        self.set_error_detail(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_system_error_: res+=prefix+("system_error: %s\n" % self.DebugFormatInt32(self.system_error_))
    if self.has_error_detail_: res+=prefix+("error_detail: %s\n" % self.DebugFormatString(self.error_detail_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksystem_error = 1
  kerror_detail = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "system_error",
    2: "error_detail",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.RemoteSocketServiceError'
class AddressPort(ProtocolBuffer.ProtocolMessage):
  has_port_ = 0
  port_ = 0
  has_packed_address_ = 0
  packed_address_ = ""
  has_hostname_hint_ = 0
  hostname_hint_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def port(self): return self.port_

  def set_port(self, x):
    self.has_port_ = 1
    self.port_ = x

  def clear_port(self):
    if self.has_port_:
      self.has_port_ = 0
      self.port_ = 0

  def has_port(self): return self.has_port_

  def packed_address(self): return self.packed_address_

  def set_packed_address(self, x):
    self.has_packed_address_ = 1
    self.packed_address_ = x

  def clear_packed_address(self):
    if self.has_packed_address_:
      self.has_packed_address_ = 0
      self.packed_address_ = ""

  def has_packed_address(self): return self.has_packed_address_

  def hostname_hint(self): return self.hostname_hint_

  def set_hostname_hint(self, x):
    self.has_hostname_hint_ = 1
    self.hostname_hint_ = x

  def clear_hostname_hint(self):
    if self.has_hostname_hint_:
      self.has_hostname_hint_ = 0
      self.hostname_hint_ = ""

  def has_hostname_hint(self): return self.has_hostname_hint_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_port()): self.set_port(x.port())
    if (x.has_packed_address()): self.set_packed_address(x.packed_address())
    if (x.has_hostname_hint()): self.set_hostname_hint(x.hostname_hint())

  def Equals(self, x):
    if x is self: return 1
    if self.has_port_ != x.has_port_: return 0
    if self.has_port_ and self.port_ != x.port_: return 0
    if self.has_packed_address_ != x.has_packed_address_: return 0
    if self.has_packed_address_ and self.packed_address_ != x.packed_address_: return 0
    if self.has_hostname_hint_ != x.has_hostname_hint_: return 0
    if self.has_hostname_hint_ and self.hostname_hint_ != x.hostname_hint_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_port_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: port not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.port_)
    if (self.has_packed_address_): n += 1 + self.lengthString(len(self.packed_address_))
    if (self.has_hostname_hint_): n += 1 + self.lengthString(len(self.hostname_hint_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_port_):
      n += 1
      n += self.lengthVarInt64(self.port_)
    if (self.has_packed_address_): n += 1 + self.lengthString(len(self.packed_address_))
    if (self.has_hostname_hint_): n += 1 + self.lengthString(len(self.hostname_hint_))
    return n

  def Clear(self):
    self.clear_port()
    self.clear_packed_address()
    self.clear_hostname_hint()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt32(self.port_)
    if (self.has_packed_address_):
      out.putVarInt32(18)
      out.putPrefixedString(self.packed_address_)
    if (self.has_hostname_hint_):
      out.putVarInt32(26)
      out.putPrefixedString(self.hostname_hint_)

  def OutputPartial(self, out):
    if (self.has_port_):
      out.putVarInt32(8)
      out.putVarInt32(self.port_)
    if (self.has_packed_address_):
      out.putVarInt32(18)
      out.putPrefixedString(self.packed_address_)
    if (self.has_hostname_hint_):
      out.putVarInt32(26)
      out.putPrefixedString(self.hostname_hint_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_port(d.getVarInt32())
        continue
      if tt == 18:
        self.set_packed_address(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_hostname_hint(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_port_: res+=prefix+("port: %s\n" % self.DebugFormatInt32(self.port_))
    if self.has_packed_address_: res+=prefix+("packed_address: %s\n" % self.DebugFormatString(self.packed_address_))
    if self.has_hostname_hint_: res+=prefix+("hostname_hint: %s\n" % self.DebugFormatString(self.hostname_hint_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kport = 1
  kpacked_address = 2
  khostname_hint = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "port",
    2: "packed_address",
    3: "hostname_hint",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.AddressPort'
class CreateSocketRequest(ProtocolBuffer.ProtocolMessage):


  IPv4         =    1
  IPv6         =    2

  _SocketFamily_NAMES = {
    1: "IPv4",
    2: "IPv6",
  }

  def SocketFamily_Name(cls, x): return cls._SocketFamily_NAMES.get(x, "")
  SocketFamily_Name = classmethod(SocketFamily_Name)



  TCP          =    1
  UDP          =    2

  _SocketProtocol_NAMES = {
    1: "TCP",
    2: "UDP",
  }

  def SocketProtocol_Name(cls, x): return cls._SocketProtocol_NAMES.get(x, "")
  SocketProtocol_Name = classmethod(SocketProtocol_Name)

  has_family_ = 0
  family_ = 0
  has_protocol_ = 0
  protocol_ = 0
  has_proxy_external_ip_ = 0
  proxy_external_ip_ = None
  has_listen_backlog_ = 0
  listen_backlog_ = 0
  has_remote_ip_ = 0
  remote_ip_ = None
  has_app_id_ = 0
  app_id_ = ""
  has_project_id_ = 0
  project_id_ = 0
  has_pool_ = 0
  pool_ = ""

  def __init__(self, contents=None):
    self.socket_options_ = []
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def family(self): return self.family_

  def set_family(self, x):
    self.has_family_ = 1
    self.family_ = x

  def clear_family(self):
    if self.has_family_:
      self.has_family_ = 0
      self.family_ = 0

  def has_family(self): return self.has_family_

  def protocol(self): return self.protocol_

  def set_protocol(self, x):
    self.has_protocol_ = 1
    self.protocol_ = x

  def clear_protocol(self):
    if self.has_protocol_:
      self.has_protocol_ = 0
      self.protocol_ = 0

  def has_protocol(self): return self.has_protocol_

  def socket_options_size(self): return len(self.socket_options_)
  def socket_options_list(self): return self.socket_options_

  def socket_options(self, i):
    return self.socket_options_[i]

  def mutable_socket_options(self, i):
    return self.socket_options_[i]

  def add_socket_options(self):
    x = SocketOption()
    self.socket_options_.append(x)
    return x

  def clear_socket_options(self):
    self.socket_options_ = []
  def proxy_external_ip(self):
    if self.proxy_external_ip_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.proxy_external_ip_ is None: self.proxy_external_ip_ = AddressPort()
      finally:
        self.lazy_init_lock_.release()
    return self.proxy_external_ip_

  def mutable_proxy_external_ip(self): self.has_proxy_external_ip_ = 1; return self.proxy_external_ip()

  def clear_proxy_external_ip(self):

    if self.has_proxy_external_ip_:
      self.has_proxy_external_ip_ = 0;
      if self.proxy_external_ip_ is not None: self.proxy_external_ip_.Clear()

  def has_proxy_external_ip(self): return self.has_proxy_external_ip_

  def listen_backlog(self): return self.listen_backlog_

  def set_listen_backlog(self, x):
    self.has_listen_backlog_ = 1
    self.listen_backlog_ = x

  def clear_listen_backlog(self):
    if self.has_listen_backlog_:
      self.has_listen_backlog_ = 0
      self.listen_backlog_ = 0

  def has_listen_backlog(self): return self.has_listen_backlog_

  def remote_ip(self):
    if self.remote_ip_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.remote_ip_ is None: self.remote_ip_ = AddressPort()
      finally:
        self.lazy_init_lock_.release()
    return self.remote_ip_

  def mutable_remote_ip(self): self.has_remote_ip_ = 1; return self.remote_ip()

  def clear_remote_ip(self):

    if self.has_remote_ip_:
      self.has_remote_ip_ = 0;
      if self.remote_ip_ is not None: self.remote_ip_.Clear()

  def has_remote_ip(self): return self.has_remote_ip_

  def app_id(self): return self.app_id_

  def set_app_id(self, x):
    self.has_app_id_ = 1
    self.app_id_ = x

  def clear_app_id(self):
    if self.has_app_id_:
      self.has_app_id_ = 0
      self.app_id_ = ""

  def has_app_id(self): return self.has_app_id_

  def project_id(self): return self.project_id_

  def set_project_id(self, x):
    self.has_project_id_ = 1
    self.project_id_ = x

  def clear_project_id(self):
    if self.has_project_id_:
      self.has_project_id_ = 0
      self.project_id_ = 0

  def has_project_id(self): return self.has_project_id_

  def pool(self): return self.pool_

  def set_pool(self, x):
    self.has_pool_ = 1
    self.pool_ = x

  def clear_pool(self):
    if self.has_pool_:
      self.has_pool_ = 0
      self.pool_ = ""

  def has_pool(self): return self.has_pool_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_family()): self.set_family(x.family())
    if (x.has_protocol()): self.set_protocol(x.protocol())
    for i in xrange(x.socket_options_size()): self.add_socket_options().CopyFrom(x.socket_options(i))
    if (x.has_proxy_external_ip()): self.mutable_proxy_external_ip().MergeFrom(x.proxy_external_ip())
    if (x.has_listen_backlog()): self.set_listen_backlog(x.listen_backlog())
    if (x.has_remote_ip()): self.mutable_remote_ip().MergeFrom(x.remote_ip())
    if (x.has_app_id()): self.set_app_id(x.app_id())
    if (x.has_project_id()): self.set_project_id(x.project_id())
    if (x.has_pool()): self.set_pool(x.pool())

  def Equals(self, x):
    if x is self: return 1
    if self.has_family_ != x.has_family_: return 0
    if self.has_family_ and self.family_ != x.family_: return 0
    if self.has_protocol_ != x.has_protocol_: return 0
    if self.has_protocol_ and self.protocol_ != x.protocol_: return 0
    if len(self.socket_options_) != len(x.socket_options_): return 0
    for e1, e2 in zip(self.socket_options_, x.socket_options_):
      if e1 != e2: return 0
    if self.has_proxy_external_ip_ != x.has_proxy_external_ip_: return 0
    if self.has_proxy_external_ip_ and self.proxy_external_ip_ != x.proxy_external_ip_: return 0
    if self.has_listen_backlog_ != x.has_listen_backlog_: return 0
    if self.has_listen_backlog_ and self.listen_backlog_ != x.listen_backlog_: return 0
    if self.has_remote_ip_ != x.has_remote_ip_: return 0
    if self.has_remote_ip_ and self.remote_ip_ != x.remote_ip_: return 0
    if self.has_app_id_ != x.has_app_id_: return 0
    if self.has_app_id_ and self.app_id_ != x.app_id_: return 0
    if self.has_project_id_ != x.has_project_id_: return 0
    if self.has_project_id_ and self.project_id_ != x.project_id_: return 0
    if self.has_pool_ != x.has_pool_: return 0
    if self.has_pool_ and self.pool_ != x.pool_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_family_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: family not set.')
    if (not self.has_protocol_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: protocol not set.')
    for p in self.socket_options_:
      if not p.IsInitialized(debug_strs): initialized=0
    if (self.has_proxy_external_ip_ and not self.proxy_external_ip_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_remote_ip_ and not self.remote_ip_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.family_)
    n += self.lengthVarInt64(self.protocol_)
    n += 1 * len(self.socket_options_)
    for i in xrange(len(self.socket_options_)): n += self.lengthString(self.socket_options_[i].ByteSize())
    if (self.has_proxy_external_ip_): n += 1 + self.lengthString(self.proxy_external_ip_.ByteSize())
    if (self.has_listen_backlog_): n += 1 + self.lengthVarInt64(self.listen_backlog_)
    if (self.has_remote_ip_): n += 1 + self.lengthString(self.remote_ip_.ByteSize())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    if (self.has_project_id_): n += 1 + self.lengthVarInt64(self.project_id_)
    if (self.has_pool_): n += 1 + self.lengthString(len(self.pool_))
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_family_):
      n += 1
      n += self.lengthVarInt64(self.family_)
    if (self.has_protocol_):
      n += 1
      n += self.lengthVarInt64(self.protocol_)
    n += 1 * len(self.socket_options_)
    for i in xrange(len(self.socket_options_)): n += self.lengthString(self.socket_options_[i].ByteSizePartial())
    if (self.has_proxy_external_ip_): n += 1 + self.lengthString(self.proxy_external_ip_.ByteSizePartial())
    if (self.has_listen_backlog_): n += 1 + self.lengthVarInt64(self.listen_backlog_)
    if (self.has_remote_ip_): n += 1 + self.lengthString(self.remote_ip_.ByteSizePartial())
    if (self.has_app_id_): n += 1 + self.lengthString(len(self.app_id_))
    if (self.has_project_id_): n += 1 + self.lengthVarInt64(self.project_id_)
    if (self.has_pool_): n += 1 + self.lengthString(len(self.pool_))
    return n

  def Clear(self):
    self.clear_family()
    self.clear_protocol()
    self.clear_socket_options()
    self.clear_proxy_external_ip()
    self.clear_listen_backlog()
    self.clear_remote_ip()
    self.clear_app_id()
    self.clear_project_id()
    self.clear_pool()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt32(self.family_)
    out.putVarInt32(16)
    out.putVarInt32(self.protocol_)
    for i in xrange(len(self.socket_options_)):
      out.putVarInt32(26)
      out.putVarInt32(self.socket_options_[i].ByteSize())
      self.socket_options_[i].OutputUnchecked(out)
    if (self.has_proxy_external_ip_):
      out.putVarInt32(34)
      out.putVarInt32(self.proxy_external_ip_.ByteSize())
      self.proxy_external_ip_.OutputUnchecked(out)
    if (self.has_listen_backlog_):
      out.putVarInt32(40)
      out.putVarInt32(self.listen_backlog_)
    if (self.has_remote_ip_):
      out.putVarInt32(50)
      out.putVarInt32(self.remote_ip_.ByteSize())
      self.remote_ip_.OutputUnchecked(out)
    if (self.has_app_id_):
      out.putVarInt32(74)
      out.putPrefixedString(self.app_id_)
    if (self.has_project_id_):
      out.putVarInt32(80)
      out.putVarInt64(self.project_id_)
    if (self.has_pool_):
      out.putVarInt32(90)
      out.putPrefixedString(self.pool_)

  def OutputPartial(self, out):
    if (self.has_family_):
      out.putVarInt32(8)
      out.putVarInt32(self.family_)
    if (self.has_protocol_):
      out.putVarInt32(16)
      out.putVarInt32(self.protocol_)
    for i in xrange(len(self.socket_options_)):
      out.putVarInt32(26)
      out.putVarInt32(self.socket_options_[i].ByteSizePartial())
      self.socket_options_[i].OutputPartial(out)
    if (self.has_proxy_external_ip_):
      out.putVarInt32(34)
      out.putVarInt32(self.proxy_external_ip_.ByteSizePartial())
      self.proxy_external_ip_.OutputPartial(out)
    if (self.has_listen_backlog_):
      out.putVarInt32(40)
      out.putVarInt32(self.listen_backlog_)
    if (self.has_remote_ip_):
      out.putVarInt32(50)
      out.putVarInt32(self.remote_ip_.ByteSizePartial())
      self.remote_ip_.OutputPartial(out)
    if (self.has_app_id_):
      out.putVarInt32(74)
      out.putPrefixedString(self.app_id_)
    if (self.has_project_id_):
      out.putVarInt32(80)
      out.putVarInt64(self.project_id_)
    if (self.has_pool_):
      out.putVarInt32(90)
      out.putPrefixedString(self.pool_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_family(d.getVarInt32())
        continue
      if tt == 16:
        self.set_protocol(d.getVarInt32())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_socket_options().TryMerge(tmp)
        continue
      if tt == 34:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_proxy_external_ip().TryMerge(tmp)
        continue
      if tt == 40:
        self.set_listen_backlog(d.getVarInt32())
        continue
      if tt == 50:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_remote_ip().TryMerge(tmp)
        continue
      if tt == 74:
        self.set_app_id(d.getPrefixedString())
        continue
      if tt == 80:
        self.set_project_id(d.getVarInt64())
        continue
      if tt == 90:
        self.set_pool(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_family_: res+=prefix+("family: %s\n" % self.DebugFormatInt32(self.family_))
    if self.has_protocol_: res+=prefix+("protocol: %s\n" % self.DebugFormatInt32(self.protocol_))
    cnt=0
    for e in self.socket_options_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("socket_options%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_proxy_external_ip_:
      res+=prefix+"proxy_external_ip <\n"
      res+=self.proxy_external_ip_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_listen_backlog_: res+=prefix+("listen_backlog: %s\n" % self.DebugFormatInt32(self.listen_backlog_))
    if self.has_remote_ip_:
      res+=prefix+"remote_ip <\n"
      res+=self.remote_ip_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_app_id_: res+=prefix+("app_id: %s\n" % self.DebugFormatString(self.app_id_))
    if self.has_project_id_: res+=prefix+("project_id: %s\n" % self.DebugFormatInt64(self.project_id_))
    if self.has_pool_: res+=prefix+("pool: %s\n" % self.DebugFormatString(self.pool_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kfamily = 1
  kprotocol = 2
  ksocket_options = 3
  kproxy_external_ip = 4
  klisten_backlog = 5
  kremote_ip = 6
  kapp_id = 9
  kproject_id = 10
  kpool = 11

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "family",
    2: "protocol",
    3: "socket_options",
    4: "proxy_external_ip",
    5: "listen_backlog",
    6: "remote_ip",
    9: "app_id",
    10: "project_id",
    11: "pool",
  }, 11)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.NUMERIC,
    6: ProtocolBuffer.Encoder.STRING,
    9: ProtocolBuffer.Encoder.STRING,
    10: ProtocolBuffer.Encoder.NUMERIC,
    11: ProtocolBuffer.Encoder.STRING,
  }, 11, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CreateSocketRequest'
class CreateSocketReply(_ExtendableProtocolMessage):
  has_socket_descriptor_ = 0
  socket_descriptor_ = ""
  has_server_address_ = 0
  server_address_ = None
  has_proxy_external_ip_ = 0
  proxy_external_ip_ = None

  def __init__(self, contents=None):
    if _extension_runtime:
      self._extension_fields = {}
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def socket_descriptor(self): return self.socket_descriptor_

  def set_socket_descriptor(self, x):
    self.has_socket_descriptor_ = 1
    self.socket_descriptor_ = x

  def clear_socket_descriptor(self):
    if self.has_socket_descriptor_:
      self.has_socket_descriptor_ = 0
      self.socket_descriptor_ = ""

  def has_socket_descriptor(self): return self.has_socket_descriptor_

  def server_address(self):
    if self.server_address_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.server_address_ is None: self.server_address_ = AddressPort()
      finally:
        self.lazy_init_lock_.release()
    return self.server_address_

  def mutable_server_address(self): self.has_server_address_ = 1; return self.server_address()

  def clear_server_address(self):

    if self.has_server_address_:
      self.has_server_address_ = 0;
      if self.server_address_ is not None: self.server_address_.Clear()

  def has_server_address(self): return self.has_server_address_

  def proxy_external_ip(self):
    if self.proxy_external_ip_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.proxy_external_ip_ is None: self.proxy_external_ip_ = AddressPort()
      finally:
        self.lazy_init_lock_.release()
    return self.proxy_external_ip_

  def mutable_proxy_external_ip(self): self.has_proxy_external_ip_ = 1; return self.proxy_external_ip()

  def clear_proxy_external_ip(self):

    if self.has_proxy_external_ip_:
      self.has_proxy_external_ip_ = 0;
      if self.proxy_external_ip_ is not None: self.proxy_external_ip_.Clear()

  def has_proxy_external_ip(self): return self.has_proxy_external_ip_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_socket_descriptor()): self.set_socket_descriptor(x.socket_descriptor())
    if (x.has_server_address()): self.mutable_server_address().MergeFrom(x.server_address())
    if (x.has_proxy_external_ip()): self.mutable_proxy_external_ip().MergeFrom(x.proxy_external_ip())
    if _extension_runtime: self._MergeExtensionFields(x)

  def Equals(self, x):
    if x is self: return 1
    if self.has_socket_descriptor_ != x.has_socket_descriptor_: return 0
    if self.has_socket_descriptor_ and self.socket_descriptor_ != x.socket_descriptor_: return 0
    if self.has_server_address_ != x.has_server_address_: return 0
    if self.has_server_address_ and self.server_address_ != x.server_address_: return 0
    if self.has_proxy_external_ip_ != x.has_proxy_external_ip_: return 0
    if self.has_proxy_external_ip_ and self.proxy_external_ip_ != x.proxy_external_ip_: return 0
    if _extension_runtime and not self._ExtensionEquals(x): return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_server_address_ and not self.server_address_.IsInitialized(debug_strs)): initialized = 0
    if (self.has_proxy_external_ip_ and not self.proxy_external_ip_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_socket_descriptor_): n += 1 + self.lengthString(len(self.socket_descriptor_))
    if (self.has_server_address_): n += 1 + self.lengthString(self.server_address_.ByteSize())
    if (self.has_proxy_external_ip_): n += 1 + self.lengthString(self.proxy_external_ip_.ByteSize())
    if _extension_runtime:
      n += self._ExtensionByteSize(False)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_socket_descriptor_): n += 1 + self.lengthString(len(self.socket_descriptor_))
    if (self.has_server_address_): n += 1 + self.lengthString(self.server_address_.ByteSizePartial())
    if (self.has_proxy_external_ip_): n += 1 + self.lengthString(self.proxy_external_ip_.ByteSizePartial())
    if _extension_runtime:
      n += self._ExtensionByteSize(True)
    return n

  def Clear(self):
    self.clear_socket_descriptor()
    self.clear_server_address()
    self.clear_proxy_external_ip()
    if _extension_runtime: self._extension_fields.clear()

  def OutputUnchecked(self, out):
    if _extension_runtime:
      extensions = self._ListExtensions()
      extension_index = 0
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)
    if (self.has_server_address_):
      out.putVarInt32(26)
      out.putVarInt32(self.server_address_.ByteSize())
      self.server_address_.OutputUnchecked(out)
    if (self.has_proxy_external_ip_):
      out.putVarInt32(34)
      out.putVarInt32(self.proxy_external_ip_.ByteSize())
      self.proxy_external_ip_.OutputUnchecked(out)
    if _extension_runtime:
      extension_index = self._OutputExtensionFields(out, False, extensions, extension_index, 536870912)

  def OutputPartial(self, out):
    if _extension_runtime:
      extensions = self._ListExtensions()
      extension_index = 0
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)
    if (self.has_server_address_):
      out.putVarInt32(26)
      out.putVarInt32(self.server_address_.ByteSizePartial())
      self.server_address_.OutputPartial(out)
    if (self.has_proxy_external_ip_):
      out.putVarInt32(34)
      out.putVarInt32(self.proxy_external_ip_.ByteSizePartial())
      self.proxy_external_ip_.OutputPartial(out)
    if _extension_runtime:
      extension_index = self._OutputExtensionFields(out, True, extensions, extension_index, 536870912)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_socket_descriptor(d.getPrefixedString())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_server_address().TryMerge(tmp)
        continue
      if tt == 34:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_proxy_external_ip().TryMerge(tmp)
        continue
      if _extension_runtime:
        if (1000 <= tt):
          self._ParseOneExtensionField(tt, d)
          continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_socket_descriptor_: res+=prefix+("socket_descriptor: %s\n" % self.DebugFormatString(self.socket_descriptor_))
    if self.has_server_address_:
      res+=prefix+"server_address <\n"
      res+=self.server_address_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_proxy_external_ip_:
      res+=prefix+"proxy_external_ip <\n"
      res+=self.proxy_external_ip_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if _extension_runtime:
      res+=self._ExtensionDebugString(prefix, printElemNumber)
    return res

  if _extension_runtime:
    _extensions_by_field_number = {}

  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksocket_descriptor = 1
  kserver_address = 3
  kproxy_external_ip = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "socket_descriptor",
    3: "server_address",
    4: "proxy_external_ip",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CreateSocketReply'
class BindRequest(ProtocolBuffer.ProtocolMessage):
  has_socket_descriptor_ = 0
  socket_descriptor_ = ""
  has_proxy_external_ip_ = 0

  def __init__(self, contents=None):
    self.proxy_external_ip_ = AddressPort()
    if contents is not None: self.MergeFromString(contents)

  def socket_descriptor(self): return self.socket_descriptor_

  def set_socket_descriptor(self, x):
    self.has_socket_descriptor_ = 1
    self.socket_descriptor_ = x

  def clear_socket_descriptor(self):
    if self.has_socket_descriptor_:
      self.has_socket_descriptor_ = 0
      self.socket_descriptor_ = ""

  def has_socket_descriptor(self): return self.has_socket_descriptor_

  def proxy_external_ip(self): return self.proxy_external_ip_

  def mutable_proxy_external_ip(self): self.has_proxy_external_ip_ = 1; return self.proxy_external_ip_

  def clear_proxy_external_ip(self):self.has_proxy_external_ip_ = 0; self.proxy_external_ip_.Clear()

  def has_proxy_external_ip(self): return self.has_proxy_external_ip_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_socket_descriptor()): self.set_socket_descriptor(x.socket_descriptor())
    if (x.has_proxy_external_ip()): self.mutable_proxy_external_ip().MergeFrom(x.proxy_external_ip())

  def Equals(self, x):
    if x is self: return 1
    if self.has_socket_descriptor_ != x.has_socket_descriptor_: return 0
    if self.has_socket_descriptor_ and self.socket_descriptor_ != x.socket_descriptor_: return 0
    if self.has_proxy_external_ip_ != x.has_proxy_external_ip_: return 0
    if self.has_proxy_external_ip_ and self.proxy_external_ip_ != x.proxy_external_ip_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_socket_descriptor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: socket_descriptor not set.')
    if (not self.has_proxy_external_ip_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: proxy_external_ip not set.')
    elif not self.proxy_external_ip_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.socket_descriptor_))
    n += self.lengthString(self.proxy_external_ip_.ByteSize())
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_socket_descriptor_):
      n += 1
      n += self.lengthString(len(self.socket_descriptor_))
    if (self.has_proxy_external_ip_):
      n += 1
      n += self.lengthString(self.proxy_external_ip_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_socket_descriptor()
    self.clear_proxy_external_ip()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.socket_descriptor_)
    out.putVarInt32(18)
    out.putVarInt32(self.proxy_external_ip_.ByteSize())
    self.proxy_external_ip_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)
    if (self.has_proxy_external_ip_):
      out.putVarInt32(18)
      out.putVarInt32(self.proxy_external_ip_.ByteSizePartial())
      self.proxy_external_ip_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_socket_descriptor(d.getPrefixedString())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_proxy_external_ip().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_socket_descriptor_: res+=prefix+("socket_descriptor: %s\n" % self.DebugFormatString(self.socket_descriptor_))
    if self.has_proxy_external_ip_:
      res+=prefix+"proxy_external_ip <\n"
      res+=self.proxy_external_ip_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksocket_descriptor = 1
  kproxy_external_ip = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "socket_descriptor",
    2: "proxy_external_ip",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.BindRequest'
class BindReply(ProtocolBuffer.ProtocolMessage):
  has_proxy_external_ip_ = 0
  proxy_external_ip_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def proxy_external_ip(self):
    if self.proxy_external_ip_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.proxy_external_ip_ is None: self.proxy_external_ip_ = AddressPort()
      finally:
        self.lazy_init_lock_.release()
    return self.proxy_external_ip_

  def mutable_proxy_external_ip(self): self.has_proxy_external_ip_ = 1; return self.proxy_external_ip()

  def clear_proxy_external_ip(self):

    if self.has_proxy_external_ip_:
      self.has_proxy_external_ip_ = 0;
      if self.proxy_external_ip_ is not None: self.proxy_external_ip_.Clear()

  def has_proxy_external_ip(self): return self.has_proxy_external_ip_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_proxy_external_ip()): self.mutable_proxy_external_ip().MergeFrom(x.proxy_external_ip())

  def Equals(self, x):
    if x is self: return 1
    if self.has_proxy_external_ip_ != x.has_proxy_external_ip_: return 0
    if self.has_proxy_external_ip_ and self.proxy_external_ip_ != x.proxy_external_ip_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_proxy_external_ip_ and not self.proxy_external_ip_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_proxy_external_ip_): n += 1 + self.lengthString(self.proxy_external_ip_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_proxy_external_ip_): n += 1 + self.lengthString(self.proxy_external_ip_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_proxy_external_ip()

  def OutputUnchecked(self, out):
    if (self.has_proxy_external_ip_):
      out.putVarInt32(10)
      out.putVarInt32(self.proxy_external_ip_.ByteSize())
      self.proxy_external_ip_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_proxy_external_ip_):
      out.putVarInt32(10)
      out.putVarInt32(self.proxy_external_ip_.ByteSizePartial())
      self.proxy_external_ip_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_proxy_external_ip().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_proxy_external_ip_:
      res+=prefix+"proxy_external_ip <\n"
      res+=self.proxy_external_ip_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kproxy_external_ip = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "proxy_external_ip",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.BindReply'
class GetSocketNameRequest(ProtocolBuffer.ProtocolMessage):
  has_socket_descriptor_ = 0
  socket_descriptor_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def socket_descriptor(self): return self.socket_descriptor_

  def set_socket_descriptor(self, x):
    self.has_socket_descriptor_ = 1
    self.socket_descriptor_ = x

  def clear_socket_descriptor(self):
    if self.has_socket_descriptor_:
      self.has_socket_descriptor_ = 0
      self.socket_descriptor_ = ""

  def has_socket_descriptor(self): return self.has_socket_descriptor_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_socket_descriptor()): self.set_socket_descriptor(x.socket_descriptor())

  def Equals(self, x):
    if x is self: return 1
    if self.has_socket_descriptor_ != x.has_socket_descriptor_: return 0
    if self.has_socket_descriptor_ and self.socket_descriptor_ != x.socket_descriptor_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_socket_descriptor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: socket_descriptor not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.socket_descriptor_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_socket_descriptor_):
      n += 1
      n += self.lengthString(len(self.socket_descriptor_))
    return n

  def Clear(self):
    self.clear_socket_descriptor()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.socket_descriptor_)

  def OutputPartial(self, out):
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_socket_descriptor(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_socket_descriptor_: res+=prefix+("socket_descriptor: %s\n" % self.DebugFormatString(self.socket_descriptor_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksocket_descriptor = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "socket_descriptor",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetSocketNameRequest'
class GetSocketNameReply(ProtocolBuffer.ProtocolMessage):
  has_proxy_external_ip_ = 0
  proxy_external_ip_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def proxy_external_ip(self):
    if self.proxy_external_ip_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.proxy_external_ip_ is None: self.proxy_external_ip_ = AddressPort()
      finally:
        self.lazy_init_lock_.release()
    return self.proxy_external_ip_

  def mutable_proxy_external_ip(self): self.has_proxy_external_ip_ = 1; return self.proxy_external_ip()

  def clear_proxy_external_ip(self):

    if self.has_proxy_external_ip_:
      self.has_proxy_external_ip_ = 0;
      if self.proxy_external_ip_ is not None: self.proxy_external_ip_.Clear()

  def has_proxy_external_ip(self): return self.has_proxy_external_ip_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_proxy_external_ip()): self.mutable_proxy_external_ip().MergeFrom(x.proxy_external_ip())

  def Equals(self, x):
    if x is self: return 1
    if self.has_proxy_external_ip_ != x.has_proxy_external_ip_: return 0
    if self.has_proxy_external_ip_ and self.proxy_external_ip_ != x.proxy_external_ip_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_proxy_external_ip_ and not self.proxy_external_ip_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_proxy_external_ip_): n += 1 + self.lengthString(self.proxy_external_ip_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_proxy_external_ip_): n += 1 + self.lengthString(self.proxy_external_ip_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_proxy_external_ip()

  def OutputUnchecked(self, out):
    if (self.has_proxy_external_ip_):
      out.putVarInt32(18)
      out.putVarInt32(self.proxy_external_ip_.ByteSize())
      self.proxy_external_ip_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_proxy_external_ip_):
      out.putVarInt32(18)
      out.putVarInt32(self.proxy_external_ip_.ByteSizePartial())
      self.proxy_external_ip_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_proxy_external_ip().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_proxy_external_ip_:
      res+=prefix+"proxy_external_ip <\n"
      res+=self.proxy_external_ip_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kproxy_external_ip = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    2: "proxy_external_ip",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetSocketNameReply'
class GetPeerNameRequest(ProtocolBuffer.ProtocolMessage):
  has_socket_descriptor_ = 0
  socket_descriptor_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def socket_descriptor(self): return self.socket_descriptor_

  def set_socket_descriptor(self, x):
    self.has_socket_descriptor_ = 1
    self.socket_descriptor_ = x

  def clear_socket_descriptor(self):
    if self.has_socket_descriptor_:
      self.has_socket_descriptor_ = 0
      self.socket_descriptor_ = ""

  def has_socket_descriptor(self): return self.has_socket_descriptor_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_socket_descriptor()): self.set_socket_descriptor(x.socket_descriptor())

  def Equals(self, x):
    if x is self: return 1
    if self.has_socket_descriptor_ != x.has_socket_descriptor_: return 0
    if self.has_socket_descriptor_ and self.socket_descriptor_ != x.socket_descriptor_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_socket_descriptor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: socket_descriptor not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.socket_descriptor_))
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_socket_descriptor_):
      n += 1
      n += self.lengthString(len(self.socket_descriptor_))
    return n

  def Clear(self):
    self.clear_socket_descriptor()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.socket_descriptor_)

  def OutputPartial(self, out):
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_socket_descriptor(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_socket_descriptor_: res+=prefix+("socket_descriptor: %s\n" % self.DebugFormatString(self.socket_descriptor_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksocket_descriptor = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "socket_descriptor",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetPeerNameRequest'
class GetPeerNameReply(ProtocolBuffer.ProtocolMessage):
  has_peer_ip_ = 0
  peer_ip_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def peer_ip(self):
    if self.peer_ip_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.peer_ip_ is None: self.peer_ip_ = AddressPort()
      finally:
        self.lazy_init_lock_.release()
    return self.peer_ip_

  def mutable_peer_ip(self): self.has_peer_ip_ = 1; return self.peer_ip()

  def clear_peer_ip(self):

    if self.has_peer_ip_:
      self.has_peer_ip_ = 0;
      if self.peer_ip_ is not None: self.peer_ip_.Clear()

  def has_peer_ip(self): return self.has_peer_ip_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_peer_ip()): self.mutable_peer_ip().MergeFrom(x.peer_ip())

  def Equals(self, x):
    if x is self: return 1
    if self.has_peer_ip_ != x.has_peer_ip_: return 0
    if self.has_peer_ip_ and self.peer_ip_ != x.peer_ip_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_peer_ip_ and not self.peer_ip_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_peer_ip_): n += 1 + self.lengthString(self.peer_ip_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_peer_ip_): n += 1 + self.lengthString(self.peer_ip_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_peer_ip()

  def OutputUnchecked(self, out):
    if (self.has_peer_ip_):
      out.putVarInt32(18)
      out.putVarInt32(self.peer_ip_.ByteSize())
      self.peer_ip_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_peer_ip_):
      out.putVarInt32(18)
      out.putVarInt32(self.peer_ip_.ByteSizePartial())
      self.peer_ip_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_peer_ip().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_peer_ip_:
      res+=prefix+"peer_ip <\n"
      res+=self.peer_ip_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kpeer_ip = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    2: "peer_ip",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetPeerNameReply'
class SocketOption(ProtocolBuffer.ProtocolMessage):


  SOCKET_SOL_IP =    0
  SOCKET_SOL_SOCKET =    1
  SOCKET_SOL_TCP =    6
  SOCKET_SOL_UDP =   17

  _SocketOptionLevel_NAMES = {
    0: "SOCKET_SOL_IP",
    1: "SOCKET_SOL_SOCKET",
    6: "SOCKET_SOL_TCP",
    17: "SOCKET_SOL_UDP",
  }

  def SocketOptionLevel_Name(cls, x): return cls._SocketOptionLevel_NAMES.get(x, "")
  SocketOptionLevel_Name = classmethod(SocketOptionLevel_Name)



  SOCKET_SO_DEBUG =    1
  SOCKET_SO_REUSEADDR =    2
  SOCKET_SO_TYPE =    3
  SOCKET_SO_ERROR =    4
  SOCKET_SO_DONTROUTE =    5
  SOCKET_SO_BROADCAST =    6
  SOCKET_SO_SNDBUF =    7
  SOCKET_SO_RCVBUF =    8
  SOCKET_SO_KEEPALIVE =    9
  SOCKET_SO_OOBINLINE =   10
  SOCKET_SO_LINGER =   13
  SOCKET_SO_RCVTIMEO =   20
  SOCKET_SO_SNDTIMEO =   21
  SOCKET_IP_TOS =    1
  SOCKET_IP_TTL =    2
  SOCKET_IP_HDRINCL =    3
  SOCKET_IP_OPTIONS =    4
  SOCKET_TCP_NODELAY =    1
  SOCKET_TCP_MAXSEG =    2
  SOCKET_TCP_CORK =    3
  SOCKET_TCP_KEEPIDLE =    4
  SOCKET_TCP_KEEPINTVL =    5
  SOCKET_TCP_KEEPCNT =    6
  SOCKET_TCP_SYNCNT =    7
  SOCKET_TCP_LINGER2 =    8
  SOCKET_TCP_DEFER_ACCEPT =    9
  SOCKET_TCP_WINDOW_CLAMP =   10
  SOCKET_TCP_INFO =   11
  SOCKET_TCP_QUICKACK =   12

  _SocketOptionName_NAMES = {
    1: "SOCKET_SO_DEBUG",
    2: "SOCKET_SO_REUSEADDR",
    3: "SOCKET_SO_TYPE",
    4: "SOCKET_SO_ERROR",
    5: "SOCKET_SO_DONTROUTE",
    6: "SOCKET_SO_BROADCAST",
    7: "SOCKET_SO_SNDBUF",
    8: "SOCKET_SO_RCVBUF",
    9: "SOCKET_SO_KEEPALIVE",
    10: "SOCKET_SO_OOBINLINE",
    13: "SOCKET_SO_LINGER",
    20: "SOCKET_SO_RCVTIMEO",
    21: "SOCKET_SO_SNDTIMEO",
    1: "SOCKET_IP_TOS",
    2: "SOCKET_IP_TTL",
    3: "SOCKET_IP_HDRINCL",
    4: "SOCKET_IP_OPTIONS",
    1: "SOCKET_TCP_NODELAY",
    2: "SOCKET_TCP_MAXSEG",
    3: "SOCKET_TCP_CORK",
    4: "SOCKET_TCP_KEEPIDLE",
    5: "SOCKET_TCP_KEEPINTVL",
    6: "SOCKET_TCP_KEEPCNT",
    7: "SOCKET_TCP_SYNCNT",
    8: "SOCKET_TCP_LINGER2",
    9: "SOCKET_TCP_DEFER_ACCEPT",
    10: "SOCKET_TCP_WINDOW_CLAMP",
    11: "SOCKET_TCP_INFO",
    12: "SOCKET_TCP_QUICKACK",
  }

  def SocketOptionName_Name(cls, x): return cls._SocketOptionName_NAMES.get(x, "")
  SocketOptionName_Name = classmethod(SocketOptionName_Name)

  has_level_ = 0
  level_ = 0
  has_option_ = 0
  option_ = 0
  has_value_ = 0
  value_ = ""

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def level(self): return self.level_

  def set_level(self, x):
    self.has_level_ = 1
    self.level_ = x

  def clear_level(self):
    if self.has_level_:
      self.has_level_ = 0
      self.level_ = 0

  def has_level(self): return self.has_level_

  def option(self): return self.option_

  def set_option(self, x):
    self.has_option_ = 1
    self.option_ = x

  def clear_option(self):
    if self.has_option_:
      self.has_option_ = 0
      self.option_ = 0

  def has_option(self): return self.has_option_

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
    if (x.has_level()): self.set_level(x.level())
    if (x.has_option()): self.set_option(x.option())
    if (x.has_value()): self.set_value(x.value())

  def Equals(self, x):
    if x is self: return 1
    if self.has_level_ != x.has_level_: return 0
    if self.has_level_ and self.level_ != x.level_: return 0
    if self.has_option_ != x.has_option_: return 0
    if self.has_option_ and self.option_ != x.option_: return 0
    if self.has_value_ != x.has_value_: return 0
    if self.has_value_ and self.value_ != x.value_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_level_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: level not set.')
    if (not self.has_option_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: option not set.')
    if (not self.has_value_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: value not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthVarInt64(self.level_)
    n += self.lengthVarInt64(self.option_)
    n += self.lengthString(len(self.value_))
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_level_):
      n += 1
      n += self.lengthVarInt64(self.level_)
    if (self.has_option_):
      n += 1
      n += self.lengthVarInt64(self.option_)
    if (self.has_value_):
      n += 1
      n += self.lengthString(len(self.value_))
    return n

  def Clear(self):
    self.clear_level()
    self.clear_option()
    self.clear_value()

  def OutputUnchecked(self, out):
    out.putVarInt32(8)
    out.putVarInt32(self.level_)
    out.putVarInt32(16)
    out.putVarInt32(self.option_)
    out.putVarInt32(26)
    out.putPrefixedString(self.value_)

  def OutputPartial(self, out):
    if (self.has_level_):
      out.putVarInt32(8)
      out.putVarInt32(self.level_)
    if (self.has_option_):
      out.putVarInt32(16)
      out.putVarInt32(self.option_)
    if (self.has_value_):
      out.putVarInt32(26)
      out.putPrefixedString(self.value_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_level(d.getVarInt32())
        continue
      if tt == 16:
        self.set_option(d.getVarInt32())
        continue
      if tt == 26:
        self.set_value(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_level_: res+=prefix+("level: %s\n" % self.DebugFormatInt32(self.level_))
    if self.has_option_: res+=prefix+("option: %s\n" % self.DebugFormatInt32(self.option_))
    if self.has_value_: res+=prefix+("value: %s\n" % self.DebugFormatString(self.value_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  klevel = 1
  koption = 2
  kvalue = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "level",
    2: "option",
    3: "value",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SocketOption'
class SetSocketOptionsRequest(ProtocolBuffer.ProtocolMessage):
  has_socket_descriptor_ = 0
  socket_descriptor_ = ""

  def __init__(self, contents=None):
    self.options_ = []
    if contents is not None: self.MergeFromString(contents)

  def socket_descriptor(self): return self.socket_descriptor_

  def set_socket_descriptor(self, x):
    self.has_socket_descriptor_ = 1
    self.socket_descriptor_ = x

  def clear_socket_descriptor(self):
    if self.has_socket_descriptor_:
      self.has_socket_descriptor_ = 0
      self.socket_descriptor_ = ""

  def has_socket_descriptor(self): return self.has_socket_descriptor_

  def options_size(self): return len(self.options_)
  def options_list(self): return self.options_

  def options(self, i):
    return self.options_[i]

  def mutable_options(self, i):
    return self.options_[i]

  def add_options(self):
    x = SocketOption()
    self.options_.append(x)
    return x

  def clear_options(self):
    self.options_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_socket_descriptor()): self.set_socket_descriptor(x.socket_descriptor())
    for i in xrange(x.options_size()): self.add_options().CopyFrom(x.options(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_socket_descriptor_ != x.has_socket_descriptor_: return 0
    if self.has_socket_descriptor_ and self.socket_descriptor_ != x.socket_descriptor_: return 0
    if len(self.options_) != len(x.options_): return 0
    for e1, e2 in zip(self.options_, x.options_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_socket_descriptor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: socket_descriptor not set.')
    for p in self.options_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.socket_descriptor_))
    n += 1 * len(self.options_)
    for i in xrange(len(self.options_)): n += self.lengthString(self.options_[i].ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_socket_descriptor_):
      n += 1
      n += self.lengthString(len(self.socket_descriptor_))
    n += 1 * len(self.options_)
    for i in xrange(len(self.options_)): n += self.lengthString(self.options_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_socket_descriptor()
    self.clear_options()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.socket_descriptor_)
    for i in xrange(len(self.options_)):
      out.putVarInt32(18)
      out.putVarInt32(self.options_[i].ByteSize())
      self.options_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)
    for i in xrange(len(self.options_)):
      out.putVarInt32(18)
      out.putVarInt32(self.options_[i].ByteSizePartial())
      self.options_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_socket_descriptor(d.getPrefixedString())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_options().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_socket_descriptor_: res+=prefix+("socket_descriptor: %s\n" % self.DebugFormatString(self.socket_descriptor_))
    cnt=0
    for e in self.options_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("options%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksocket_descriptor = 1
  koptions = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "socket_descriptor",
    2: "options",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SetSocketOptionsRequest'
class SetSocketOptionsReply(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SetSocketOptionsReply'
class GetSocketOptionsRequest(ProtocolBuffer.ProtocolMessage):
  has_socket_descriptor_ = 0
  socket_descriptor_ = ""

  def __init__(self, contents=None):
    self.options_ = []
    if contents is not None: self.MergeFromString(contents)

  def socket_descriptor(self): return self.socket_descriptor_

  def set_socket_descriptor(self, x):
    self.has_socket_descriptor_ = 1
    self.socket_descriptor_ = x

  def clear_socket_descriptor(self):
    if self.has_socket_descriptor_:
      self.has_socket_descriptor_ = 0
      self.socket_descriptor_ = ""

  def has_socket_descriptor(self): return self.has_socket_descriptor_

  def options_size(self): return len(self.options_)
  def options_list(self): return self.options_

  def options(self, i):
    return self.options_[i]

  def mutable_options(self, i):
    return self.options_[i]

  def add_options(self):
    x = SocketOption()
    self.options_.append(x)
    return x

  def clear_options(self):
    self.options_ = []

  def MergeFrom(self, x):
    assert x is not self
    if (x.has_socket_descriptor()): self.set_socket_descriptor(x.socket_descriptor())
    for i in xrange(x.options_size()): self.add_options().CopyFrom(x.options(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_socket_descriptor_ != x.has_socket_descriptor_: return 0
    if self.has_socket_descriptor_ and self.socket_descriptor_ != x.socket_descriptor_: return 0
    if len(self.options_) != len(x.options_): return 0
    for e1, e2 in zip(self.options_, x.options_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_socket_descriptor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: socket_descriptor not set.')
    for p in self.options_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.socket_descriptor_))
    n += 1 * len(self.options_)
    for i in xrange(len(self.options_)): n += self.lengthString(self.options_[i].ByteSize())
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_socket_descriptor_):
      n += 1
      n += self.lengthString(len(self.socket_descriptor_))
    n += 1 * len(self.options_)
    for i in xrange(len(self.options_)): n += self.lengthString(self.options_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_socket_descriptor()
    self.clear_options()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.socket_descriptor_)
    for i in xrange(len(self.options_)):
      out.putVarInt32(18)
      out.putVarInt32(self.options_[i].ByteSize())
      self.options_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)
    for i in xrange(len(self.options_)):
      out.putVarInt32(18)
      out.putVarInt32(self.options_[i].ByteSizePartial())
      self.options_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_socket_descriptor(d.getPrefixedString())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_options().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_socket_descriptor_: res+=prefix+("socket_descriptor: %s\n" % self.DebugFormatString(self.socket_descriptor_))
    cnt=0
    for e in self.options_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("options%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksocket_descriptor = 1
  koptions = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "socket_descriptor",
    2: "options",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetSocketOptionsRequest'
class GetSocketOptionsReply(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.options_ = []
    if contents is not None: self.MergeFromString(contents)

  def options_size(self): return len(self.options_)
  def options_list(self): return self.options_

  def options(self, i):
    return self.options_[i]

  def mutable_options(self, i):
    return self.options_[i]

  def add_options(self):
    x = SocketOption()
    self.options_.append(x)
    return x

  def clear_options(self):
    self.options_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.options_size()): self.add_options().CopyFrom(x.options(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.options_) != len(x.options_): return 0
    for e1, e2 in zip(self.options_, x.options_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.options_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.options_)
    for i in xrange(len(self.options_)): n += self.lengthString(self.options_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.options_)
    for i in xrange(len(self.options_)): n += self.lengthString(self.options_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_options()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.options_)):
      out.putVarInt32(18)
      out.putVarInt32(self.options_[i].ByteSize())
      self.options_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.options_)):
      out.putVarInt32(18)
      out.putVarInt32(self.options_[i].ByteSizePartial())
      self.options_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_options().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.options_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("options%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  koptions = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    2: "options",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.GetSocketOptionsReply'
class ConnectRequest(ProtocolBuffer.ProtocolMessage):
  has_socket_descriptor_ = 0
  socket_descriptor_ = ""
  has_remote_ip_ = 0
  has_timeout_seconds_ = 0
  timeout_seconds_ = -1.0

  def __init__(self, contents=None):
    self.remote_ip_ = AddressPort()
    if contents is not None: self.MergeFromString(contents)

  def socket_descriptor(self): return self.socket_descriptor_

  def set_socket_descriptor(self, x):
    self.has_socket_descriptor_ = 1
    self.socket_descriptor_ = x

  def clear_socket_descriptor(self):
    if self.has_socket_descriptor_:
      self.has_socket_descriptor_ = 0
      self.socket_descriptor_ = ""

  def has_socket_descriptor(self): return self.has_socket_descriptor_

  def remote_ip(self): return self.remote_ip_

  def mutable_remote_ip(self): self.has_remote_ip_ = 1; return self.remote_ip_

  def clear_remote_ip(self):self.has_remote_ip_ = 0; self.remote_ip_.Clear()

  def has_remote_ip(self): return self.has_remote_ip_

  def timeout_seconds(self): return self.timeout_seconds_

  def set_timeout_seconds(self, x):
    self.has_timeout_seconds_ = 1
    self.timeout_seconds_ = x

  def clear_timeout_seconds(self):
    if self.has_timeout_seconds_:
      self.has_timeout_seconds_ = 0
      self.timeout_seconds_ = -1.0

  def has_timeout_seconds(self): return self.has_timeout_seconds_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_socket_descriptor()): self.set_socket_descriptor(x.socket_descriptor())
    if (x.has_remote_ip()): self.mutable_remote_ip().MergeFrom(x.remote_ip())
    if (x.has_timeout_seconds()): self.set_timeout_seconds(x.timeout_seconds())

  def Equals(self, x):
    if x is self: return 1
    if self.has_socket_descriptor_ != x.has_socket_descriptor_: return 0
    if self.has_socket_descriptor_ and self.socket_descriptor_ != x.socket_descriptor_: return 0
    if self.has_remote_ip_ != x.has_remote_ip_: return 0
    if self.has_remote_ip_ and self.remote_ip_ != x.remote_ip_: return 0
    if self.has_timeout_seconds_ != x.has_timeout_seconds_: return 0
    if self.has_timeout_seconds_ and self.timeout_seconds_ != x.timeout_seconds_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_socket_descriptor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: socket_descriptor not set.')
    if (not self.has_remote_ip_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: remote_ip not set.')
    elif not self.remote_ip_.IsInitialized(debug_strs): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.socket_descriptor_))
    n += self.lengthString(self.remote_ip_.ByteSize())
    if (self.has_timeout_seconds_): n += 9
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_socket_descriptor_):
      n += 1
      n += self.lengthString(len(self.socket_descriptor_))
    if (self.has_remote_ip_):
      n += 1
      n += self.lengthString(self.remote_ip_.ByteSizePartial())
    if (self.has_timeout_seconds_): n += 9
    return n

  def Clear(self):
    self.clear_socket_descriptor()
    self.clear_remote_ip()
    self.clear_timeout_seconds()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.socket_descriptor_)
    out.putVarInt32(18)
    out.putVarInt32(self.remote_ip_.ByteSize())
    self.remote_ip_.OutputUnchecked(out)
    if (self.has_timeout_seconds_):
      out.putVarInt32(25)
      out.putDouble(self.timeout_seconds_)

  def OutputPartial(self, out):
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)
    if (self.has_remote_ip_):
      out.putVarInt32(18)
      out.putVarInt32(self.remote_ip_.ByteSizePartial())
      self.remote_ip_.OutputPartial(out)
    if (self.has_timeout_seconds_):
      out.putVarInt32(25)
      out.putDouble(self.timeout_seconds_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_socket_descriptor(d.getPrefixedString())
        continue
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_remote_ip().TryMerge(tmp)
        continue
      if tt == 25:
        self.set_timeout_seconds(d.getDouble())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_socket_descriptor_: res+=prefix+("socket_descriptor: %s\n" % self.DebugFormatString(self.socket_descriptor_))
    if self.has_remote_ip_:
      res+=prefix+"remote_ip <\n"
      res+=self.remote_ip_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_timeout_seconds_: res+=prefix+("timeout_seconds: %s\n" % self.DebugFormat(self.timeout_seconds_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksocket_descriptor = 1
  kremote_ip = 2
  ktimeout_seconds = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "socket_descriptor",
    2: "remote_ip",
    3: "timeout_seconds",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.DOUBLE,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ConnectRequest'
class ConnectReply(_ExtendableProtocolMessage):
  has_proxy_external_ip_ = 0
  proxy_external_ip_ = None

  def __init__(self, contents=None):
    if _extension_runtime:
      self._extension_fields = {}
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def proxy_external_ip(self):
    if self.proxy_external_ip_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.proxy_external_ip_ is None: self.proxy_external_ip_ = AddressPort()
      finally:
        self.lazy_init_lock_.release()
    return self.proxy_external_ip_

  def mutable_proxy_external_ip(self): self.has_proxy_external_ip_ = 1; return self.proxy_external_ip()

  def clear_proxy_external_ip(self):

    if self.has_proxy_external_ip_:
      self.has_proxy_external_ip_ = 0;
      if self.proxy_external_ip_ is not None: self.proxy_external_ip_.Clear()

  def has_proxy_external_ip(self): return self.has_proxy_external_ip_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_proxy_external_ip()): self.mutable_proxy_external_ip().MergeFrom(x.proxy_external_ip())
    if _extension_runtime: self._MergeExtensionFields(x)

  def Equals(self, x):
    if x is self: return 1
    if self.has_proxy_external_ip_ != x.has_proxy_external_ip_: return 0
    if self.has_proxy_external_ip_ and self.proxy_external_ip_ != x.proxy_external_ip_: return 0
    if _extension_runtime and not self._ExtensionEquals(x): return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_proxy_external_ip_ and not self.proxy_external_ip_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_proxy_external_ip_): n += 1 + self.lengthString(self.proxy_external_ip_.ByteSize())
    if _extension_runtime:
      n += self._ExtensionByteSize(False)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_proxy_external_ip_): n += 1 + self.lengthString(self.proxy_external_ip_.ByteSizePartial())
    if _extension_runtime:
      n += self._ExtensionByteSize(True)
    return n

  def Clear(self):
    self.clear_proxy_external_ip()
    if _extension_runtime: self._extension_fields.clear()

  def OutputUnchecked(self, out):
    if _extension_runtime:
      extensions = self._ListExtensions()
      extension_index = 0
    if (self.has_proxy_external_ip_):
      out.putVarInt32(10)
      out.putVarInt32(self.proxy_external_ip_.ByteSize())
      self.proxy_external_ip_.OutputUnchecked(out)
    if _extension_runtime:
      extension_index = self._OutputExtensionFields(out, False, extensions, extension_index, 536870912)

  def OutputPartial(self, out):
    if _extension_runtime:
      extensions = self._ListExtensions()
      extension_index = 0
    if (self.has_proxy_external_ip_):
      out.putVarInt32(10)
      out.putVarInt32(self.proxy_external_ip_.ByteSizePartial())
      self.proxy_external_ip_.OutputPartial(out)
    if _extension_runtime:
      extension_index = self._OutputExtensionFields(out, True, extensions, extension_index, 536870912)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_proxy_external_ip().TryMerge(tmp)
        continue
      if _extension_runtime:
        if (1000 <= tt):
          self._ParseOneExtensionField(tt, d)
          continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_proxy_external_ip_:
      res+=prefix+"proxy_external_ip <\n"
      res+=self.proxy_external_ip_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if _extension_runtime:
      res+=self._ExtensionDebugString(prefix, printElemNumber)
    return res

  if _extension_runtime:
    _extensions_by_field_number = {}

  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kproxy_external_ip = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "proxy_external_ip",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ConnectReply'
class ListenRequest(ProtocolBuffer.ProtocolMessage):
  has_socket_descriptor_ = 0
  socket_descriptor_ = ""
  has_backlog_ = 0
  backlog_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def socket_descriptor(self): return self.socket_descriptor_

  def set_socket_descriptor(self, x):
    self.has_socket_descriptor_ = 1
    self.socket_descriptor_ = x

  def clear_socket_descriptor(self):
    if self.has_socket_descriptor_:
      self.has_socket_descriptor_ = 0
      self.socket_descriptor_ = ""

  def has_socket_descriptor(self): return self.has_socket_descriptor_

  def backlog(self): return self.backlog_

  def set_backlog(self, x):
    self.has_backlog_ = 1
    self.backlog_ = x

  def clear_backlog(self):
    if self.has_backlog_:
      self.has_backlog_ = 0
      self.backlog_ = 0

  def has_backlog(self): return self.has_backlog_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_socket_descriptor()): self.set_socket_descriptor(x.socket_descriptor())
    if (x.has_backlog()): self.set_backlog(x.backlog())

  def Equals(self, x):
    if x is self: return 1
    if self.has_socket_descriptor_ != x.has_socket_descriptor_: return 0
    if self.has_socket_descriptor_ and self.socket_descriptor_ != x.socket_descriptor_: return 0
    if self.has_backlog_ != x.has_backlog_: return 0
    if self.has_backlog_ and self.backlog_ != x.backlog_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_socket_descriptor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: socket_descriptor not set.')
    if (not self.has_backlog_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: backlog not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.socket_descriptor_))
    n += self.lengthVarInt64(self.backlog_)
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_socket_descriptor_):
      n += 1
      n += self.lengthString(len(self.socket_descriptor_))
    if (self.has_backlog_):
      n += 1
      n += self.lengthVarInt64(self.backlog_)
    return n

  def Clear(self):
    self.clear_socket_descriptor()
    self.clear_backlog()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.socket_descriptor_)
    out.putVarInt32(16)
    out.putVarInt32(self.backlog_)

  def OutputPartial(self, out):
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)
    if (self.has_backlog_):
      out.putVarInt32(16)
      out.putVarInt32(self.backlog_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_socket_descriptor(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_backlog(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_socket_descriptor_: res+=prefix+("socket_descriptor: %s\n" % self.DebugFormatString(self.socket_descriptor_))
    if self.has_backlog_: res+=prefix+("backlog: %s\n" % self.DebugFormatInt32(self.backlog_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksocket_descriptor = 1
  kbacklog = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "socket_descriptor",
    2: "backlog",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ListenRequest'
class ListenReply(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ListenReply'
class AcceptRequest(ProtocolBuffer.ProtocolMessage):
  has_socket_descriptor_ = 0
  socket_descriptor_ = ""
  has_timeout_seconds_ = 0
  timeout_seconds_ = -1.0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def socket_descriptor(self): return self.socket_descriptor_

  def set_socket_descriptor(self, x):
    self.has_socket_descriptor_ = 1
    self.socket_descriptor_ = x

  def clear_socket_descriptor(self):
    if self.has_socket_descriptor_:
      self.has_socket_descriptor_ = 0
      self.socket_descriptor_ = ""

  def has_socket_descriptor(self): return self.has_socket_descriptor_

  def timeout_seconds(self): return self.timeout_seconds_

  def set_timeout_seconds(self, x):
    self.has_timeout_seconds_ = 1
    self.timeout_seconds_ = x

  def clear_timeout_seconds(self):
    if self.has_timeout_seconds_:
      self.has_timeout_seconds_ = 0
      self.timeout_seconds_ = -1.0

  def has_timeout_seconds(self): return self.has_timeout_seconds_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_socket_descriptor()): self.set_socket_descriptor(x.socket_descriptor())
    if (x.has_timeout_seconds()): self.set_timeout_seconds(x.timeout_seconds())

  def Equals(self, x):
    if x is self: return 1
    if self.has_socket_descriptor_ != x.has_socket_descriptor_: return 0
    if self.has_socket_descriptor_ and self.socket_descriptor_ != x.socket_descriptor_: return 0
    if self.has_timeout_seconds_ != x.has_timeout_seconds_: return 0
    if self.has_timeout_seconds_ and self.timeout_seconds_ != x.timeout_seconds_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_socket_descriptor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: socket_descriptor not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.socket_descriptor_))
    if (self.has_timeout_seconds_): n += 9
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_socket_descriptor_):
      n += 1
      n += self.lengthString(len(self.socket_descriptor_))
    if (self.has_timeout_seconds_): n += 9
    return n

  def Clear(self):
    self.clear_socket_descriptor()
    self.clear_timeout_seconds()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.socket_descriptor_)
    if (self.has_timeout_seconds_):
      out.putVarInt32(17)
      out.putDouble(self.timeout_seconds_)

  def OutputPartial(self, out):
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)
    if (self.has_timeout_seconds_):
      out.putVarInt32(17)
      out.putDouble(self.timeout_seconds_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_socket_descriptor(d.getPrefixedString())
        continue
      if tt == 17:
        self.set_timeout_seconds(d.getDouble())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_socket_descriptor_: res+=prefix+("socket_descriptor: %s\n" % self.DebugFormatString(self.socket_descriptor_))
    if self.has_timeout_seconds_: res+=prefix+("timeout_seconds: %s\n" % self.DebugFormat(self.timeout_seconds_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksocket_descriptor = 1
  ktimeout_seconds = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "socket_descriptor",
    2: "timeout_seconds",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.DOUBLE,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.AcceptRequest'
class AcceptReply(ProtocolBuffer.ProtocolMessage):
  has_new_socket_descriptor_ = 0
  new_socket_descriptor_ = ""
  has_remote_address_ = 0
  remote_address_ = None

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def new_socket_descriptor(self): return self.new_socket_descriptor_

  def set_new_socket_descriptor(self, x):
    self.has_new_socket_descriptor_ = 1
    self.new_socket_descriptor_ = x

  def clear_new_socket_descriptor(self):
    if self.has_new_socket_descriptor_:
      self.has_new_socket_descriptor_ = 0
      self.new_socket_descriptor_ = ""

  def has_new_socket_descriptor(self): return self.has_new_socket_descriptor_

  def remote_address(self):
    if self.remote_address_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.remote_address_ is None: self.remote_address_ = AddressPort()
      finally:
        self.lazy_init_lock_.release()
    return self.remote_address_

  def mutable_remote_address(self): self.has_remote_address_ = 1; return self.remote_address()

  def clear_remote_address(self):

    if self.has_remote_address_:
      self.has_remote_address_ = 0;
      if self.remote_address_ is not None: self.remote_address_.Clear()

  def has_remote_address(self): return self.has_remote_address_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_new_socket_descriptor()): self.set_new_socket_descriptor(x.new_socket_descriptor())
    if (x.has_remote_address()): self.mutable_remote_address().MergeFrom(x.remote_address())

  def Equals(self, x):
    if x is self: return 1
    if self.has_new_socket_descriptor_ != x.has_new_socket_descriptor_: return 0
    if self.has_new_socket_descriptor_ and self.new_socket_descriptor_ != x.new_socket_descriptor_: return 0
    if self.has_remote_address_ != x.has_remote_address_: return 0
    if self.has_remote_address_ and self.remote_address_ != x.remote_address_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_remote_address_ and not self.remote_address_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_new_socket_descriptor_): n += 1 + self.lengthString(len(self.new_socket_descriptor_))
    if (self.has_remote_address_): n += 1 + self.lengthString(self.remote_address_.ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_new_socket_descriptor_): n += 1 + self.lengthString(len(self.new_socket_descriptor_))
    if (self.has_remote_address_): n += 1 + self.lengthString(self.remote_address_.ByteSizePartial())
    return n

  def Clear(self):
    self.clear_new_socket_descriptor()
    self.clear_remote_address()

  def OutputUnchecked(self, out):
    if (self.has_new_socket_descriptor_):
      out.putVarInt32(18)
      out.putPrefixedString(self.new_socket_descriptor_)
    if (self.has_remote_address_):
      out.putVarInt32(26)
      out.putVarInt32(self.remote_address_.ByteSize())
      self.remote_address_.OutputUnchecked(out)

  def OutputPartial(self, out):
    if (self.has_new_socket_descriptor_):
      out.putVarInt32(18)
      out.putPrefixedString(self.new_socket_descriptor_)
    if (self.has_remote_address_):
      out.putVarInt32(26)
      out.putVarInt32(self.remote_address_.ByteSizePartial())
      self.remote_address_.OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 18:
        self.set_new_socket_descriptor(d.getPrefixedString())
        continue
      if tt == 26:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_remote_address().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_new_socket_descriptor_: res+=prefix+("new_socket_descriptor: %s\n" % self.DebugFormatString(self.new_socket_descriptor_))
    if self.has_remote_address_:
      res+=prefix+"remote_address <\n"
      res+=self.remote_address_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  knew_socket_descriptor = 2
  kremote_address = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    2: "new_socket_descriptor",
    3: "remote_address",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.AcceptReply'
class ShutDownRequest(ProtocolBuffer.ProtocolMessage):


  SOCKET_SHUT_RD =    1
  SOCKET_SHUT_WR =    2
  SOCKET_SHUT_RDWR =    3

  _How_NAMES = {
    1: "SOCKET_SHUT_RD",
    2: "SOCKET_SHUT_WR",
    3: "SOCKET_SHUT_RDWR",
  }

  def How_Name(cls, x): return cls._How_NAMES.get(x, "")
  How_Name = classmethod(How_Name)

  has_socket_descriptor_ = 0
  socket_descriptor_ = ""
  has_how_ = 0
  how_ = 0
  has_send_offset_ = 0
  send_offset_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def socket_descriptor(self): return self.socket_descriptor_

  def set_socket_descriptor(self, x):
    self.has_socket_descriptor_ = 1
    self.socket_descriptor_ = x

  def clear_socket_descriptor(self):
    if self.has_socket_descriptor_:
      self.has_socket_descriptor_ = 0
      self.socket_descriptor_ = ""

  def has_socket_descriptor(self): return self.has_socket_descriptor_

  def how(self): return self.how_

  def set_how(self, x):
    self.has_how_ = 1
    self.how_ = x

  def clear_how(self):
    if self.has_how_:
      self.has_how_ = 0
      self.how_ = 0

  def has_how(self): return self.has_how_

  def send_offset(self): return self.send_offset_

  def set_send_offset(self, x):
    self.has_send_offset_ = 1
    self.send_offset_ = x

  def clear_send_offset(self):
    if self.has_send_offset_:
      self.has_send_offset_ = 0
      self.send_offset_ = 0

  def has_send_offset(self): return self.has_send_offset_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_socket_descriptor()): self.set_socket_descriptor(x.socket_descriptor())
    if (x.has_how()): self.set_how(x.how())
    if (x.has_send_offset()): self.set_send_offset(x.send_offset())

  def Equals(self, x):
    if x is self: return 1
    if self.has_socket_descriptor_ != x.has_socket_descriptor_: return 0
    if self.has_socket_descriptor_ and self.socket_descriptor_ != x.socket_descriptor_: return 0
    if self.has_how_ != x.has_how_: return 0
    if self.has_how_ and self.how_ != x.how_: return 0
    if self.has_send_offset_ != x.has_send_offset_: return 0
    if self.has_send_offset_ and self.send_offset_ != x.send_offset_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_socket_descriptor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: socket_descriptor not set.')
    if (not self.has_how_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: how not set.')
    if (not self.has_send_offset_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: send_offset not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.socket_descriptor_))
    n += self.lengthVarInt64(self.how_)
    n += self.lengthVarInt64(self.send_offset_)
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_socket_descriptor_):
      n += 1
      n += self.lengthString(len(self.socket_descriptor_))
    if (self.has_how_):
      n += 1
      n += self.lengthVarInt64(self.how_)
    if (self.has_send_offset_):
      n += 1
      n += self.lengthVarInt64(self.send_offset_)
    return n

  def Clear(self):
    self.clear_socket_descriptor()
    self.clear_how()
    self.clear_send_offset()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.socket_descriptor_)
    out.putVarInt32(16)
    out.putVarInt32(self.how_)
    out.putVarInt32(24)
    out.putVarInt64(self.send_offset_)

  def OutputPartial(self, out):
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)
    if (self.has_how_):
      out.putVarInt32(16)
      out.putVarInt32(self.how_)
    if (self.has_send_offset_):
      out.putVarInt32(24)
      out.putVarInt64(self.send_offset_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_socket_descriptor(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_how(d.getVarInt32())
        continue
      if tt == 24:
        self.set_send_offset(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_socket_descriptor_: res+=prefix+("socket_descriptor: %s\n" % self.DebugFormatString(self.socket_descriptor_))
    if self.has_how_: res+=prefix+("how: %s\n" % self.DebugFormatInt32(self.how_))
    if self.has_send_offset_: res+=prefix+("send_offset: %s\n" % self.DebugFormatInt64(self.send_offset_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksocket_descriptor = 1
  khow = 2
  ksend_offset = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "socket_descriptor",
    2: "how",
    3: "send_offset",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ShutDownRequest'
class ShutDownReply(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ShutDownReply'
class CloseRequest(ProtocolBuffer.ProtocolMessage):
  has_socket_descriptor_ = 0
  socket_descriptor_ = ""
  has_send_offset_ = 0
  send_offset_ = -1

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def socket_descriptor(self): return self.socket_descriptor_

  def set_socket_descriptor(self, x):
    self.has_socket_descriptor_ = 1
    self.socket_descriptor_ = x

  def clear_socket_descriptor(self):
    if self.has_socket_descriptor_:
      self.has_socket_descriptor_ = 0
      self.socket_descriptor_ = ""

  def has_socket_descriptor(self): return self.has_socket_descriptor_

  def send_offset(self): return self.send_offset_

  def set_send_offset(self, x):
    self.has_send_offset_ = 1
    self.send_offset_ = x

  def clear_send_offset(self):
    if self.has_send_offset_:
      self.has_send_offset_ = 0
      self.send_offset_ = -1

  def has_send_offset(self): return self.has_send_offset_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_socket_descriptor()): self.set_socket_descriptor(x.socket_descriptor())
    if (x.has_send_offset()): self.set_send_offset(x.send_offset())

  def Equals(self, x):
    if x is self: return 1
    if self.has_socket_descriptor_ != x.has_socket_descriptor_: return 0
    if self.has_socket_descriptor_ and self.socket_descriptor_ != x.socket_descriptor_: return 0
    if self.has_send_offset_ != x.has_send_offset_: return 0
    if self.has_send_offset_ and self.send_offset_ != x.send_offset_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_socket_descriptor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: socket_descriptor not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.socket_descriptor_))
    if (self.has_send_offset_): n += 1 + self.lengthVarInt64(self.send_offset_)
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_socket_descriptor_):
      n += 1
      n += self.lengthString(len(self.socket_descriptor_))
    if (self.has_send_offset_): n += 1 + self.lengthVarInt64(self.send_offset_)
    return n

  def Clear(self):
    self.clear_socket_descriptor()
    self.clear_send_offset()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.socket_descriptor_)
    if (self.has_send_offset_):
      out.putVarInt32(16)
      out.putVarInt64(self.send_offset_)

  def OutputPartial(self, out):
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)
    if (self.has_send_offset_):
      out.putVarInt32(16)
      out.putVarInt64(self.send_offset_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_socket_descriptor(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_send_offset(d.getVarInt64())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_socket_descriptor_: res+=prefix+("socket_descriptor: %s\n" % self.DebugFormatString(self.socket_descriptor_))
    if self.has_send_offset_: res+=prefix+("send_offset: %s\n" % self.DebugFormatInt64(self.send_offset_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksocket_descriptor = 1
  ksend_offset = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "socket_descriptor",
    2: "send_offset",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CloseRequest'
class CloseReply(ProtocolBuffer.ProtocolMessage):

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
  _PROTO_DESCRIPTOR_NAME = 'apphosting.CloseReply'
class SendRequest(ProtocolBuffer.ProtocolMessage):
  has_socket_descriptor_ = 0
  socket_descriptor_ = ""
  has_data_ = 0
  data_ = ""
  has_stream_offset_ = 0
  stream_offset_ = 0
  has_flags_ = 0
  flags_ = 0
  has_send_to_ = 0
  send_to_ = None
  has_timeout_seconds_ = 0
  timeout_seconds_ = -1.0

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def socket_descriptor(self): return self.socket_descriptor_

  def set_socket_descriptor(self, x):
    self.has_socket_descriptor_ = 1
    self.socket_descriptor_ = x

  def clear_socket_descriptor(self):
    if self.has_socket_descriptor_:
      self.has_socket_descriptor_ = 0
      self.socket_descriptor_ = ""

  def has_socket_descriptor(self): return self.has_socket_descriptor_

  def data(self): return self.data_

  def set_data(self, x):
    self.has_data_ = 1
    self.data_ = x

  def clear_data(self):
    if self.has_data_:
      self.has_data_ = 0
      self.data_ = ""

  def has_data(self): return self.has_data_

  def stream_offset(self): return self.stream_offset_

  def set_stream_offset(self, x):
    self.has_stream_offset_ = 1
    self.stream_offset_ = x

  def clear_stream_offset(self):
    if self.has_stream_offset_:
      self.has_stream_offset_ = 0
      self.stream_offset_ = 0

  def has_stream_offset(self): return self.has_stream_offset_

  def flags(self): return self.flags_

  def set_flags(self, x):
    self.has_flags_ = 1
    self.flags_ = x

  def clear_flags(self):
    if self.has_flags_:
      self.has_flags_ = 0
      self.flags_ = 0

  def has_flags(self): return self.has_flags_

  def send_to(self):
    if self.send_to_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.send_to_ is None: self.send_to_ = AddressPort()
      finally:
        self.lazy_init_lock_.release()
    return self.send_to_

  def mutable_send_to(self): self.has_send_to_ = 1; return self.send_to()

  def clear_send_to(self):

    if self.has_send_to_:
      self.has_send_to_ = 0;
      if self.send_to_ is not None: self.send_to_.Clear()

  def has_send_to(self): return self.has_send_to_

  def timeout_seconds(self): return self.timeout_seconds_

  def set_timeout_seconds(self, x):
    self.has_timeout_seconds_ = 1
    self.timeout_seconds_ = x

  def clear_timeout_seconds(self):
    if self.has_timeout_seconds_:
      self.has_timeout_seconds_ = 0
      self.timeout_seconds_ = -1.0

  def has_timeout_seconds(self): return self.has_timeout_seconds_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_socket_descriptor()): self.set_socket_descriptor(x.socket_descriptor())
    if (x.has_data()): self.set_data(x.data())
    if (x.has_stream_offset()): self.set_stream_offset(x.stream_offset())
    if (x.has_flags()): self.set_flags(x.flags())
    if (x.has_send_to()): self.mutable_send_to().MergeFrom(x.send_to())
    if (x.has_timeout_seconds()): self.set_timeout_seconds(x.timeout_seconds())

  def Equals(self, x):
    if x is self: return 1
    if self.has_socket_descriptor_ != x.has_socket_descriptor_: return 0
    if self.has_socket_descriptor_ and self.socket_descriptor_ != x.socket_descriptor_: return 0
    if self.has_data_ != x.has_data_: return 0
    if self.has_data_ and self.data_ != x.data_: return 0
    if self.has_stream_offset_ != x.has_stream_offset_: return 0
    if self.has_stream_offset_ and self.stream_offset_ != x.stream_offset_: return 0
    if self.has_flags_ != x.has_flags_: return 0
    if self.has_flags_ and self.flags_ != x.flags_: return 0
    if self.has_send_to_ != x.has_send_to_: return 0
    if self.has_send_to_ and self.send_to_ != x.send_to_: return 0
    if self.has_timeout_seconds_ != x.has_timeout_seconds_: return 0
    if self.has_timeout_seconds_ and self.timeout_seconds_ != x.timeout_seconds_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_socket_descriptor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: socket_descriptor not set.')
    if (not self.has_data_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: data not set.')
    if (not self.has_stream_offset_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: stream_offset not set.')
    if (self.has_send_to_ and not self.send_to_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.socket_descriptor_))
    n += self.lengthString(len(self.data_))
    n += self.lengthVarInt64(self.stream_offset_)
    if (self.has_flags_): n += 1 + self.lengthVarInt64(self.flags_)
    if (self.has_send_to_): n += 1 + self.lengthString(self.send_to_.ByteSize())
    if (self.has_timeout_seconds_): n += 9
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_socket_descriptor_):
      n += 1
      n += self.lengthString(len(self.socket_descriptor_))
    if (self.has_data_):
      n += 1
      n += self.lengthString(len(self.data_))
    if (self.has_stream_offset_):
      n += 1
      n += self.lengthVarInt64(self.stream_offset_)
    if (self.has_flags_): n += 1 + self.lengthVarInt64(self.flags_)
    if (self.has_send_to_): n += 1 + self.lengthString(self.send_to_.ByteSizePartial())
    if (self.has_timeout_seconds_): n += 9
    return n

  def Clear(self):
    self.clear_socket_descriptor()
    self.clear_data()
    self.clear_stream_offset()
    self.clear_flags()
    self.clear_send_to()
    self.clear_timeout_seconds()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.socket_descriptor_)
    out.putVarInt32(18)
    out.putPrefixedString(self.data_)
    out.putVarInt32(24)
    out.putVarInt64(self.stream_offset_)
    if (self.has_flags_):
      out.putVarInt32(32)
      out.putVarInt32(self.flags_)
    if (self.has_send_to_):
      out.putVarInt32(42)
      out.putVarInt32(self.send_to_.ByteSize())
      self.send_to_.OutputUnchecked(out)
    if (self.has_timeout_seconds_):
      out.putVarInt32(49)
      out.putDouble(self.timeout_seconds_)

  def OutputPartial(self, out):
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)
    if (self.has_data_):
      out.putVarInt32(18)
      out.putPrefixedString(self.data_)
    if (self.has_stream_offset_):
      out.putVarInt32(24)
      out.putVarInt64(self.stream_offset_)
    if (self.has_flags_):
      out.putVarInt32(32)
      out.putVarInt32(self.flags_)
    if (self.has_send_to_):
      out.putVarInt32(42)
      out.putVarInt32(self.send_to_.ByteSizePartial())
      self.send_to_.OutputPartial(out)
    if (self.has_timeout_seconds_):
      out.putVarInt32(49)
      out.putDouble(self.timeout_seconds_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_socket_descriptor(d.getPrefixedString())
        continue
      if tt == 18:
        self.set_data(d.getPrefixedString())
        continue
      if tt == 24:
        self.set_stream_offset(d.getVarInt64())
        continue
      if tt == 32:
        self.set_flags(d.getVarInt32())
        continue
      if tt == 42:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_send_to().TryMerge(tmp)
        continue
      if tt == 49:
        self.set_timeout_seconds(d.getDouble())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_socket_descriptor_: res+=prefix+("socket_descriptor: %s\n" % self.DebugFormatString(self.socket_descriptor_))
    if self.has_data_: res+=prefix+("data: %s\n" % self.DebugFormatString(self.data_))
    if self.has_stream_offset_: res+=prefix+("stream_offset: %s\n" % self.DebugFormatInt64(self.stream_offset_))
    if self.has_flags_: res+=prefix+("flags: %s\n" % self.DebugFormatInt32(self.flags_))
    if self.has_send_to_:
      res+=prefix+"send_to <\n"
      res+=self.send_to_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_timeout_seconds_: res+=prefix+("timeout_seconds: %s\n" % self.DebugFormat(self.timeout_seconds_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksocket_descriptor = 1
  kdata = 2
  kstream_offset = 3
  kflags = 4
  ksend_to = 5
  ktimeout_seconds = 6

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "socket_descriptor",
    2: "data",
    3: "stream_offset",
    4: "flags",
    5: "send_to",
    6: "timeout_seconds",
  }, 6)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.NUMERIC,
    4: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.STRING,
    6: ProtocolBuffer.Encoder.DOUBLE,
  }, 6, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SendRequest'
class SendReply(ProtocolBuffer.ProtocolMessage):
  has_data_sent_ = 0
  data_sent_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def data_sent(self): return self.data_sent_

  def set_data_sent(self, x):
    self.has_data_sent_ = 1
    self.data_sent_ = x

  def clear_data_sent(self):
    if self.has_data_sent_:
      self.has_data_sent_ = 0
      self.data_sent_ = 0

  def has_data_sent(self): return self.has_data_sent_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_data_sent()): self.set_data_sent(x.data_sent())

  def Equals(self, x):
    if x is self: return 1
    if self.has_data_sent_ != x.has_data_sent_: return 0
    if self.has_data_sent_ and self.data_sent_ != x.data_sent_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_data_sent_): n += 1 + self.lengthVarInt64(self.data_sent_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_data_sent_): n += 1 + self.lengthVarInt64(self.data_sent_)
    return n

  def Clear(self):
    self.clear_data_sent()

  def OutputUnchecked(self, out):
    if (self.has_data_sent_):
      out.putVarInt32(8)
      out.putVarInt32(self.data_sent_)

  def OutputPartial(self, out):
    if (self.has_data_sent_):
      out.putVarInt32(8)
      out.putVarInt32(self.data_sent_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 8:
        self.set_data_sent(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_data_sent_: res+=prefix+("data_sent: %s\n" % self.DebugFormatInt32(self.data_sent_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kdata_sent = 1

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "data_sent",
  }, 1)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.NUMERIC,
  }, 1, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.SendReply'
class ReceiveRequest(ProtocolBuffer.ProtocolMessage):


  MSG_OOB      =    1
  MSG_PEEK     =    2

  _Flags_NAMES = {
    1: "MSG_OOB",
    2: "MSG_PEEK",
  }

  def Flags_Name(cls, x): return cls._Flags_NAMES.get(x, "")
  Flags_Name = classmethod(Flags_Name)

  has_socket_descriptor_ = 0
  socket_descriptor_ = ""
  has_data_size_ = 0
  data_size_ = 0
  has_flags_ = 0
  flags_ = 0
  has_timeout_seconds_ = 0
  timeout_seconds_ = -1.0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def socket_descriptor(self): return self.socket_descriptor_

  def set_socket_descriptor(self, x):
    self.has_socket_descriptor_ = 1
    self.socket_descriptor_ = x

  def clear_socket_descriptor(self):
    if self.has_socket_descriptor_:
      self.has_socket_descriptor_ = 0
      self.socket_descriptor_ = ""

  def has_socket_descriptor(self): return self.has_socket_descriptor_

  def data_size(self): return self.data_size_

  def set_data_size(self, x):
    self.has_data_size_ = 1
    self.data_size_ = x

  def clear_data_size(self):
    if self.has_data_size_:
      self.has_data_size_ = 0
      self.data_size_ = 0

  def has_data_size(self): return self.has_data_size_

  def flags(self): return self.flags_

  def set_flags(self, x):
    self.has_flags_ = 1
    self.flags_ = x

  def clear_flags(self):
    if self.has_flags_:
      self.has_flags_ = 0
      self.flags_ = 0

  def has_flags(self): return self.has_flags_

  def timeout_seconds(self): return self.timeout_seconds_

  def set_timeout_seconds(self, x):
    self.has_timeout_seconds_ = 1
    self.timeout_seconds_ = x

  def clear_timeout_seconds(self):
    if self.has_timeout_seconds_:
      self.has_timeout_seconds_ = 0
      self.timeout_seconds_ = -1.0

  def has_timeout_seconds(self): return self.has_timeout_seconds_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_socket_descriptor()): self.set_socket_descriptor(x.socket_descriptor())
    if (x.has_data_size()): self.set_data_size(x.data_size())
    if (x.has_flags()): self.set_flags(x.flags())
    if (x.has_timeout_seconds()): self.set_timeout_seconds(x.timeout_seconds())

  def Equals(self, x):
    if x is self: return 1
    if self.has_socket_descriptor_ != x.has_socket_descriptor_: return 0
    if self.has_socket_descriptor_ and self.socket_descriptor_ != x.socket_descriptor_: return 0
    if self.has_data_size_ != x.has_data_size_: return 0
    if self.has_data_size_ and self.data_size_ != x.data_size_: return 0
    if self.has_flags_ != x.has_flags_: return 0
    if self.has_flags_ and self.flags_ != x.flags_: return 0
    if self.has_timeout_seconds_ != x.has_timeout_seconds_: return 0
    if self.has_timeout_seconds_ and self.timeout_seconds_ != x.timeout_seconds_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_socket_descriptor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: socket_descriptor not set.')
    if (not self.has_data_size_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: data_size not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.socket_descriptor_))
    n += self.lengthVarInt64(self.data_size_)
    if (self.has_flags_): n += 1 + self.lengthVarInt64(self.flags_)
    if (self.has_timeout_seconds_): n += 9
    return n + 2

  def ByteSizePartial(self):
    n = 0
    if (self.has_socket_descriptor_):
      n += 1
      n += self.lengthString(len(self.socket_descriptor_))
    if (self.has_data_size_):
      n += 1
      n += self.lengthVarInt64(self.data_size_)
    if (self.has_flags_): n += 1 + self.lengthVarInt64(self.flags_)
    if (self.has_timeout_seconds_): n += 9
    return n

  def Clear(self):
    self.clear_socket_descriptor()
    self.clear_data_size()
    self.clear_flags()
    self.clear_timeout_seconds()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.socket_descriptor_)
    out.putVarInt32(16)
    out.putVarInt32(self.data_size_)
    if (self.has_flags_):
      out.putVarInt32(24)
      out.putVarInt32(self.flags_)
    if (self.has_timeout_seconds_):
      out.putVarInt32(41)
      out.putDouble(self.timeout_seconds_)

  def OutputPartial(self, out):
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)
    if (self.has_data_size_):
      out.putVarInt32(16)
      out.putVarInt32(self.data_size_)
    if (self.has_flags_):
      out.putVarInt32(24)
      out.putVarInt32(self.flags_)
    if (self.has_timeout_seconds_):
      out.putVarInt32(41)
      out.putDouble(self.timeout_seconds_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_socket_descriptor(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_data_size(d.getVarInt32())
        continue
      if tt == 24:
        self.set_flags(d.getVarInt32())
        continue
      if tt == 41:
        self.set_timeout_seconds(d.getDouble())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_socket_descriptor_: res+=prefix+("socket_descriptor: %s\n" % self.DebugFormatString(self.socket_descriptor_))
    if self.has_data_size_: res+=prefix+("data_size: %s\n" % self.DebugFormatInt32(self.data_size_))
    if self.has_flags_: res+=prefix+("flags: %s\n" % self.DebugFormatInt32(self.flags_))
    if self.has_timeout_seconds_: res+=prefix+("timeout_seconds: %s\n" % self.DebugFormat(self.timeout_seconds_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksocket_descriptor = 1
  kdata_size = 2
  kflags = 3
  ktimeout_seconds = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "socket_descriptor",
    2: "data_size",
    3: "flags",
    5: "timeout_seconds",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
    5: ProtocolBuffer.Encoder.DOUBLE,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ReceiveRequest'
class ReceiveReply(ProtocolBuffer.ProtocolMessage):
  has_stream_offset_ = 0
  stream_offset_ = 0
  has_data_ = 0
  data_ = ""
  has_received_from_ = 0
  received_from_ = None
  has_buffer_size_ = 0
  buffer_size_ = 0

  def __init__(self, contents=None):
    self.lazy_init_lock_ = thread.allocate_lock()
    if contents is not None: self.MergeFromString(contents)

  def stream_offset(self): return self.stream_offset_

  def set_stream_offset(self, x):
    self.has_stream_offset_ = 1
    self.stream_offset_ = x

  def clear_stream_offset(self):
    if self.has_stream_offset_:
      self.has_stream_offset_ = 0
      self.stream_offset_ = 0

  def has_stream_offset(self): return self.has_stream_offset_

  def data(self): return self.data_

  def set_data(self, x):
    self.has_data_ = 1
    self.data_ = x

  def clear_data(self):
    if self.has_data_:
      self.has_data_ = 0
      self.data_ = ""

  def has_data(self): return self.has_data_

  def received_from(self):
    if self.received_from_ is None:
      self.lazy_init_lock_.acquire()
      try:
        if self.received_from_ is None: self.received_from_ = AddressPort()
      finally:
        self.lazy_init_lock_.release()
    return self.received_from_

  def mutable_received_from(self): self.has_received_from_ = 1; return self.received_from()

  def clear_received_from(self):

    if self.has_received_from_:
      self.has_received_from_ = 0;
      if self.received_from_ is not None: self.received_from_.Clear()

  def has_received_from(self): return self.has_received_from_

  def buffer_size(self): return self.buffer_size_

  def set_buffer_size(self, x):
    self.has_buffer_size_ = 1
    self.buffer_size_ = x

  def clear_buffer_size(self):
    if self.has_buffer_size_:
      self.has_buffer_size_ = 0
      self.buffer_size_ = 0

  def has_buffer_size(self): return self.has_buffer_size_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_stream_offset()): self.set_stream_offset(x.stream_offset())
    if (x.has_data()): self.set_data(x.data())
    if (x.has_received_from()): self.mutable_received_from().MergeFrom(x.received_from())
    if (x.has_buffer_size()): self.set_buffer_size(x.buffer_size())

  def Equals(self, x):
    if x is self: return 1
    if self.has_stream_offset_ != x.has_stream_offset_: return 0
    if self.has_stream_offset_ and self.stream_offset_ != x.stream_offset_: return 0
    if self.has_data_ != x.has_data_: return 0
    if self.has_data_ and self.data_ != x.data_: return 0
    if self.has_received_from_ != x.has_received_from_: return 0
    if self.has_received_from_ and self.received_from_ != x.received_from_: return 0
    if self.has_buffer_size_ != x.has_buffer_size_: return 0
    if self.has_buffer_size_ and self.buffer_size_ != x.buffer_size_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (self.has_received_from_ and not self.received_from_.IsInitialized(debug_strs)): initialized = 0
    return initialized

  def ByteSize(self):
    n = 0
    if (self.has_stream_offset_): n += 1 + self.lengthVarInt64(self.stream_offset_)
    if (self.has_data_): n += 1 + self.lengthString(len(self.data_))
    if (self.has_received_from_): n += 1 + self.lengthString(self.received_from_.ByteSize())
    if (self.has_buffer_size_): n += 1 + self.lengthVarInt64(self.buffer_size_)
    return n

  def ByteSizePartial(self):
    n = 0
    if (self.has_stream_offset_): n += 1 + self.lengthVarInt64(self.stream_offset_)
    if (self.has_data_): n += 1 + self.lengthString(len(self.data_))
    if (self.has_received_from_): n += 1 + self.lengthString(self.received_from_.ByteSizePartial())
    if (self.has_buffer_size_): n += 1 + self.lengthVarInt64(self.buffer_size_)
    return n

  def Clear(self):
    self.clear_stream_offset()
    self.clear_data()
    self.clear_received_from()
    self.clear_buffer_size()

  def OutputUnchecked(self, out):
    if (self.has_stream_offset_):
      out.putVarInt32(16)
      out.putVarInt64(self.stream_offset_)
    if (self.has_data_):
      out.putVarInt32(26)
      out.putPrefixedString(self.data_)
    if (self.has_received_from_):
      out.putVarInt32(34)
      out.putVarInt32(self.received_from_.ByteSize())
      self.received_from_.OutputUnchecked(out)
    if (self.has_buffer_size_):
      out.putVarInt32(40)
      out.putVarInt32(self.buffer_size_)

  def OutputPartial(self, out):
    if (self.has_stream_offset_):
      out.putVarInt32(16)
      out.putVarInt64(self.stream_offset_)
    if (self.has_data_):
      out.putVarInt32(26)
      out.putPrefixedString(self.data_)
    if (self.has_received_from_):
      out.putVarInt32(34)
      out.putVarInt32(self.received_from_.ByteSizePartial())
      self.received_from_.OutputPartial(out)
    if (self.has_buffer_size_):
      out.putVarInt32(40)
      out.putVarInt32(self.buffer_size_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 16:
        self.set_stream_offset(d.getVarInt64())
        continue
      if tt == 26:
        self.set_data(d.getPrefixedString())
        continue
      if tt == 34:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.mutable_received_from().TryMerge(tmp)
        continue
      if tt == 40:
        self.set_buffer_size(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_stream_offset_: res+=prefix+("stream_offset: %s\n" % self.DebugFormatInt64(self.stream_offset_))
    if self.has_data_: res+=prefix+("data: %s\n" % self.DebugFormatString(self.data_))
    if self.has_received_from_:
      res+=prefix+"received_from <\n"
      res+=self.received_from_.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
    if self.has_buffer_size_: res+=prefix+("buffer_size: %s\n" % self.DebugFormatInt32(self.buffer_size_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kstream_offset = 2
  kdata = 3
  kreceived_from = 4
  kbuffer_size = 5

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    2: "stream_offset",
    3: "data",
    4: "received_from",
    5: "buffer_size",
  }, 5)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
    5: ProtocolBuffer.Encoder.NUMERIC,
  }, 5, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ReceiveReply'
class PollEvent(ProtocolBuffer.ProtocolMessage):


  SOCKET_POLLNONE =    0
  SOCKET_POLLIN =    1
  SOCKET_POLLPRI =    2
  SOCKET_POLLOUT =    4
  SOCKET_POLLERR =    8
  SOCKET_POLLHUP =   16
  SOCKET_POLLNVAL =   32
  SOCKET_POLLRDNORM =   64
  SOCKET_POLLRDBAND =  128
  SOCKET_POLLWRNORM =  256
  SOCKET_POLLWRBAND =  512
  SOCKET_POLLMSG = 1024
  SOCKET_POLLREMOVE = 4096
  SOCKET_POLLRDHUP = 8192

  _PollEventFlag_NAMES = {
    0: "SOCKET_POLLNONE",
    1: "SOCKET_POLLIN",
    2: "SOCKET_POLLPRI",
    4: "SOCKET_POLLOUT",
    8: "SOCKET_POLLERR",
    16: "SOCKET_POLLHUP",
    32: "SOCKET_POLLNVAL",
    64: "SOCKET_POLLRDNORM",
    128: "SOCKET_POLLRDBAND",
    256: "SOCKET_POLLWRNORM",
    512: "SOCKET_POLLWRBAND",
    1024: "SOCKET_POLLMSG",
    4096: "SOCKET_POLLREMOVE",
    8192: "SOCKET_POLLRDHUP",
  }

  def PollEventFlag_Name(cls, x): return cls._PollEventFlag_NAMES.get(x, "")
  PollEventFlag_Name = classmethod(PollEventFlag_Name)

  has_socket_descriptor_ = 0
  socket_descriptor_ = ""
  has_requested_events_ = 0
  requested_events_ = 0
  has_observed_events_ = 0
  observed_events_ = 0

  def __init__(self, contents=None):
    if contents is not None: self.MergeFromString(contents)

  def socket_descriptor(self): return self.socket_descriptor_

  def set_socket_descriptor(self, x):
    self.has_socket_descriptor_ = 1
    self.socket_descriptor_ = x

  def clear_socket_descriptor(self):
    if self.has_socket_descriptor_:
      self.has_socket_descriptor_ = 0
      self.socket_descriptor_ = ""

  def has_socket_descriptor(self): return self.has_socket_descriptor_

  def requested_events(self): return self.requested_events_

  def set_requested_events(self, x):
    self.has_requested_events_ = 1
    self.requested_events_ = x

  def clear_requested_events(self):
    if self.has_requested_events_:
      self.has_requested_events_ = 0
      self.requested_events_ = 0

  def has_requested_events(self): return self.has_requested_events_

  def observed_events(self): return self.observed_events_

  def set_observed_events(self, x):
    self.has_observed_events_ = 1
    self.observed_events_ = x

  def clear_observed_events(self):
    if self.has_observed_events_:
      self.has_observed_events_ = 0
      self.observed_events_ = 0

  def has_observed_events(self): return self.has_observed_events_


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_socket_descriptor()): self.set_socket_descriptor(x.socket_descriptor())
    if (x.has_requested_events()): self.set_requested_events(x.requested_events())
    if (x.has_observed_events()): self.set_observed_events(x.observed_events())

  def Equals(self, x):
    if x is self: return 1
    if self.has_socket_descriptor_ != x.has_socket_descriptor_: return 0
    if self.has_socket_descriptor_ and self.socket_descriptor_ != x.socket_descriptor_: return 0
    if self.has_requested_events_ != x.has_requested_events_: return 0
    if self.has_requested_events_ and self.requested_events_ != x.requested_events_: return 0
    if self.has_observed_events_ != x.has_observed_events_: return 0
    if self.has_observed_events_ and self.observed_events_ != x.observed_events_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    if (not self.has_socket_descriptor_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: socket_descriptor not set.')
    if (not self.has_requested_events_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: requested_events not set.')
    if (not self.has_observed_events_):
      initialized = 0
      if debug_strs is not None:
        debug_strs.append('Required field: observed_events not set.')
    return initialized

  def ByteSize(self):
    n = 0
    n += self.lengthString(len(self.socket_descriptor_))
    n += self.lengthVarInt64(self.requested_events_)
    n += self.lengthVarInt64(self.observed_events_)
    return n + 3

  def ByteSizePartial(self):
    n = 0
    if (self.has_socket_descriptor_):
      n += 1
      n += self.lengthString(len(self.socket_descriptor_))
    if (self.has_requested_events_):
      n += 1
      n += self.lengthVarInt64(self.requested_events_)
    if (self.has_observed_events_):
      n += 1
      n += self.lengthVarInt64(self.observed_events_)
    return n

  def Clear(self):
    self.clear_socket_descriptor()
    self.clear_requested_events()
    self.clear_observed_events()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.socket_descriptor_)
    out.putVarInt32(16)
    out.putVarInt32(self.requested_events_)
    out.putVarInt32(24)
    out.putVarInt32(self.observed_events_)

  def OutputPartial(self, out):
    if (self.has_socket_descriptor_):
      out.putVarInt32(10)
      out.putPrefixedString(self.socket_descriptor_)
    if (self.has_requested_events_):
      out.putVarInt32(16)
      out.putVarInt32(self.requested_events_)
    if (self.has_observed_events_):
      out.putVarInt32(24)
      out.putVarInt32(self.observed_events_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_socket_descriptor(d.getPrefixedString())
        continue
      if tt == 16:
        self.set_requested_events(d.getVarInt32())
        continue
      if tt == 24:
        self.set_observed_events(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_socket_descriptor_: res+=prefix+("socket_descriptor: %s\n" % self.DebugFormatString(self.socket_descriptor_))
    if self.has_requested_events_: res+=prefix+("requested_events: %s\n" % self.DebugFormatInt32(self.requested_events_))
    if self.has_observed_events_: res+=prefix+("observed_events: %s\n" % self.DebugFormatInt32(self.observed_events_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  ksocket_descriptor = 1
  krequested_events = 2
  kobserved_events = 3

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "socket_descriptor",
    2: "requested_events",
    3: "observed_events",
  }, 3)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
    3: ProtocolBuffer.Encoder.NUMERIC,
  }, 3, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.PollEvent'
class PollRequest(ProtocolBuffer.ProtocolMessage):
  has_timeout_seconds_ = 0
  timeout_seconds_ = -1.0

  def __init__(self, contents=None):
    self.events_ = []
    if contents is not None: self.MergeFromString(contents)

  def events_size(self): return len(self.events_)
  def events_list(self): return self.events_

  def events(self, i):
    return self.events_[i]

  def mutable_events(self, i):
    return self.events_[i]

  def add_events(self):
    x = PollEvent()
    self.events_.append(x)
    return x

  def clear_events(self):
    self.events_ = []
  def timeout_seconds(self): return self.timeout_seconds_

  def set_timeout_seconds(self, x):
    self.has_timeout_seconds_ = 1
    self.timeout_seconds_ = x

  def clear_timeout_seconds(self):
    if self.has_timeout_seconds_:
      self.has_timeout_seconds_ = 0
      self.timeout_seconds_ = -1.0

  def has_timeout_seconds(self): return self.has_timeout_seconds_


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.events_size()): self.add_events().CopyFrom(x.events(i))
    if (x.has_timeout_seconds()): self.set_timeout_seconds(x.timeout_seconds())

  def Equals(self, x):
    if x is self: return 1
    if len(self.events_) != len(x.events_): return 0
    for e1, e2 in zip(self.events_, x.events_):
      if e1 != e2: return 0
    if self.has_timeout_seconds_ != x.has_timeout_seconds_: return 0
    if self.has_timeout_seconds_ and self.timeout_seconds_ != x.timeout_seconds_: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.events_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.events_)
    for i in xrange(len(self.events_)): n += self.lengthString(self.events_[i].ByteSize())
    if (self.has_timeout_seconds_): n += 9
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.events_)
    for i in xrange(len(self.events_)): n += self.lengthString(self.events_[i].ByteSizePartial())
    if (self.has_timeout_seconds_): n += 9
    return n

  def Clear(self):
    self.clear_events()
    self.clear_timeout_seconds()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.events_)):
      out.putVarInt32(10)
      out.putVarInt32(self.events_[i].ByteSize())
      self.events_[i].OutputUnchecked(out)
    if (self.has_timeout_seconds_):
      out.putVarInt32(17)
      out.putDouble(self.timeout_seconds_)

  def OutputPartial(self, out):
    for i in xrange(len(self.events_)):
      out.putVarInt32(10)
      out.putVarInt32(self.events_[i].ByteSizePartial())
      self.events_[i].OutputPartial(out)
    if (self.has_timeout_seconds_):
      out.putVarInt32(17)
      out.putDouble(self.timeout_seconds_)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_events().TryMerge(tmp)
        continue
      if tt == 17:
        self.set_timeout_seconds(d.getDouble())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.events_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("events%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    if self.has_timeout_seconds_: res+=prefix+("timeout_seconds: %s\n" % self.DebugFormat(self.timeout_seconds_))
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kevents = 1
  ktimeout_seconds = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "events",
    2: "timeout_seconds",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.DOUBLE,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.PollRequest'
class PollReply(ProtocolBuffer.ProtocolMessage):

  def __init__(self, contents=None):
    self.events_ = []
    if contents is not None: self.MergeFromString(contents)

  def events_size(self): return len(self.events_)
  def events_list(self): return self.events_

  def events(self, i):
    return self.events_[i]

  def mutable_events(self, i):
    return self.events_[i]

  def add_events(self):
    x = PollEvent()
    self.events_.append(x)
    return x

  def clear_events(self):
    self.events_ = []

  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.events_size()): self.add_events().CopyFrom(x.events(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.events_) != len(x.events_): return 0
    for e1, e2 in zip(self.events_, x.events_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    for p in self.events_:
      if not p.IsInitialized(debug_strs): initialized=0
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.events_)
    for i in xrange(len(self.events_)): n += self.lengthString(self.events_[i].ByteSize())
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.events_)
    for i in xrange(len(self.events_)): n += self.lengthString(self.events_[i].ByteSizePartial())
    return n

  def Clear(self):
    self.clear_events()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.events_)):
      out.putVarInt32(18)
      out.putVarInt32(self.events_[i].ByteSize())
      self.events_[i].OutputUnchecked(out)

  def OutputPartial(self, out):
    for i in xrange(len(self.events_)):
      out.putVarInt32(18)
      out.putVarInt32(self.events_[i].ByteSizePartial())
      self.events_[i].OutputPartial(out)

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 18:
        length = d.getVarInt32()
        tmp = ProtocolBuffer.Decoder(d.buffer(), d.pos(), d.pos() + length)
        d.skip(length)
        self.add_events().TryMerge(tmp)
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.events_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("events%s <\n" % elm)
      res+=e.__str__(prefix + "  ", printElemNumber)
      res+=prefix+">\n"
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kevents = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    2: "events",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.PollReply'
class ResolveRequest(ProtocolBuffer.ProtocolMessage):
  has_name_ = 0
  name_ = ""

  def __init__(self, contents=None):
    self.address_families_ = []
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

  def address_families_size(self): return len(self.address_families_)
  def address_families_list(self): return self.address_families_

  def address_families(self, i):
    return self.address_families_[i]

  def set_address_families(self, i, x):
    self.address_families_[i] = x

  def add_address_families(self, x):
    self.address_families_.append(x)

  def clear_address_families(self):
    self.address_families_ = []


  def MergeFrom(self, x):
    assert x is not self
    if (x.has_name()): self.set_name(x.name())
    for i in xrange(x.address_families_size()): self.add_address_families(x.address_families(i))

  def Equals(self, x):
    if x is self: return 1
    if self.has_name_ != x.has_name_: return 0
    if self.has_name_ and self.name_ != x.name_: return 0
    if len(self.address_families_) != len(x.address_families_): return 0
    for e1, e2 in zip(self.address_families_, x.address_families_):
      if e1 != e2: return 0
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
    n += 1 * len(self.address_families_)
    for i in xrange(len(self.address_families_)): n += self.lengthVarInt64(self.address_families_[i])
    return n + 1

  def ByteSizePartial(self):
    n = 0
    if (self.has_name_):
      n += 1
      n += self.lengthString(len(self.name_))
    n += 1 * len(self.address_families_)
    for i in xrange(len(self.address_families_)): n += self.lengthVarInt64(self.address_families_[i])
    return n

  def Clear(self):
    self.clear_name()
    self.clear_address_families()

  def OutputUnchecked(self, out):
    out.putVarInt32(10)
    out.putPrefixedString(self.name_)
    for i in xrange(len(self.address_families_)):
      out.putVarInt32(16)
      out.putVarInt32(self.address_families_[i])

  def OutputPartial(self, out):
    if (self.has_name_):
      out.putVarInt32(10)
      out.putPrefixedString(self.name_)
    for i in xrange(len(self.address_families_)):
      out.putVarInt32(16)
      out.putVarInt32(self.address_families_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 10:
        self.set_name(d.getPrefixedString())
        continue
      if tt == 16:
        self.add_address_families(d.getVarInt32())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    if self.has_name_: res+=prefix+("name: %s\n" % self.DebugFormatString(self.name_))
    cnt=0
    for e in self.address_families_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("address_families%s: %s\n" % (elm, self.DebugFormatInt32(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kname = 1
  kaddress_families = 2

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    1: "name",
    2: "address_families",
  }, 2)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    1: ProtocolBuffer.Encoder.STRING,
    2: ProtocolBuffer.Encoder.NUMERIC,
  }, 2, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ResolveRequest'
class ResolveReply(ProtocolBuffer.ProtocolMessage):


  SOCKET_EAI_ADDRFAMILY =    1
  SOCKET_EAI_AGAIN =    2
  SOCKET_EAI_BADFLAGS =    3
  SOCKET_EAI_FAIL =    4
  SOCKET_EAI_FAMILY =    5
  SOCKET_EAI_MEMORY =    6
  SOCKET_EAI_NODATA =    7
  SOCKET_EAI_NONAME =    8
  SOCKET_EAI_SERVICE =    9
  SOCKET_EAI_SOCKTYPE =   10
  SOCKET_EAI_SYSTEM =   11
  SOCKET_EAI_BADHINTS =   12
  SOCKET_EAI_PROTOCOL =   13
  SOCKET_EAI_OVERFLOW =   14
  SOCKET_EAI_MAX =   15

  _ErrorCode_NAMES = {
    1: "SOCKET_EAI_ADDRFAMILY",
    2: "SOCKET_EAI_AGAIN",
    3: "SOCKET_EAI_BADFLAGS",
    4: "SOCKET_EAI_FAIL",
    5: "SOCKET_EAI_FAMILY",
    6: "SOCKET_EAI_MEMORY",
    7: "SOCKET_EAI_NODATA",
    8: "SOCKET_EAI_NONAME",
    9: "SOCKET_EAI_SERVICE",
    10: "SOCKET_EAI_SOCKTYPE",
    11: "SOCKET_EAI_SYSTEM",
    12: "SOCKET_EAI_BADHINTS",
    13: "SOCKET_EAI_PROTOCOL",
    14: "SOCKET_EAI_OVERFLOW",
    15: "SOCKET_EAI_MAX",
  }

  def ErrorCode_Name(cls, x): return cls._ErrorCode_NAMES.get(x, "")
  ErrorCode_Name = classmethod(ErrorCode_Name)

  has_canonical_name_ = 0
  canonical_name_ = ""

  def __init__(self, contents=None):
    self.packed_address_ = []
    self.aliases_ = []
    if contents is not None: self.MergeFromString(contents)

  def packed_address_size(self): return len(self.packed_address_)
  def packed_address_list(self): return self.packed_address_

  def packed_address(self, i):
    return self.packed_address_[i]

  def set_packed_address(self, i, x):
    self.packed_address_[i] = x

  def add_packed_address(self, x):
    self.packed_address_.append(x)

  def clear_packed_address(self):
    self.packed_address_ = []

  def canonical_name(self): return self.canonical_name_

  def set_canonical_name(self, x):
    self.has_canonical_name_ = 1
    self.canonical_name_ = x

  def clear_canonical_name(self):
    if self.has_canonical_name_:
      self.has_canonical_name_ = 0
      self.canonical_name_ = ""

  def has_canonical_name(self): return self.has_canonical_name_

  def aliases_size(self): return len(self.aliases_)
  def aliases_list(self): return self.aliases_

  def aliases(self, i):
    return self.aliases_[i]

  def set_aliases(self, i, x):
    self.aliases_[i] = x

  def add_aliases(self, x):
    self.aliases_.append(x)

  def clear_aliases(self):
    self.aliases_ = []


  def MergeFrom(self, x):
    assert x is not self
    for i in xrange(x.packed_address_size()): self.add_packed_address(x.packed_address(i))
    if (x.has_canonical_name()): self.set_canonical_name(x.canonical_name())
    for i in xrange(x.aliases_size()): self.add_aliases(x.aliases(i))

  def Equals(self, x):
    if x is self: return 1
    if len(self.packed_address_) != len(x.packed_address_): return 0
    for e1, e2 in zip(self.packed_address_, x.packed_address_):
      if e1 != e2: return 0
    if self.has_canonical_name_ != x.has_canonical_name_: return 0
    if self.has_canonical_name_ and self.canonical_name_ != x.canonical_name_: return 0
    if len(self.aliases_) != len(x.aliases_): return 0
    for e1, e2 in zip(self.aliases_, x.aliases_):
      if e1 != e2: return 0
    return 1

  def IsInitialized(self, debug_strs=None):
    initialized = 1
    return initialized

  def ByteSize(self):
    n = 0
    n += 1 * len(self.packed_address_)
    for i in xrange(len(self.packed_address_)): n += self.lengthString(len(self.packed_address_[i]))
    if (self.has_canonical_name_): n += 1 + self.lengthString(len(self.canonical_name_))
    n += 1 * len(self.aliases_)
    for i in xrange(len(self.aliases_)): n += self.lengthString(len(self.aliases_[i]))
    return n

  def ByteSizePartial(self):
    n = 0
    n += 1 * len(self.packed_address_)
    for i in xrange(len(self.packed_address_)): n += self.lengthString(len(self.packed_address_[i]))
    if (self.has_canonical_name_): n += 1 + self.lengthString(len(self.canonical_name_))
    n += 1 * len(self.aliases_)
    for i in xrange(len(self.aliases_)): n += self.lengthString(len(self.aliases_[i]))
    return n

  def Clear(self):
    self.clear_packed_address()
    self.clear_canonical_name()
    self.clear_aliases()

  def OutputUnchecked(self, out):
    for i in xrange(len(self.packed_address_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.packed_address_[i])
    if (self.has_canonical_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.canonical_name_)
    for i in xrange(len(self.aliases_)):
      out.putVarInt32(34)
      out.putPrefixedString(self.aliases_[i])

  def OutputPartial(self, out):
    for i in xrange(len(self.packed_address_)):
      out.putVarInt32(18)
      out.putPrefixedString(self.packed_address_[i])
    if (self.has_canonical_name_):
      out.putVarInt32(26)
      out.putPrefixedString(self.canonical_name_)
    for i in xrange(len(self.aliases_)):
      out.putVarInt32(34)
      out.putPrefixedString(self.aliases_[i])

  def TryMerge(self, d):
    while d.avail() > 0:
      tt = d.getVarInt32()
      if tt == 18:
        self.add_packed_address(d.getPrefixedString())
        continue
      if tt == 26:
        self.set_canonical_name(d.getPrefixedString())
        continue
      if tt == 34:
        self.add_aliases(d.getPrefixedString())
        continue


      if (tt == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      d.skipData(tt)


  def __str__(self, prefix="", printElemNumber=0):
    res=""
    cnt=0
    for e in self.packed_address_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("packed_address%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    if self.has_canonical_name_: res+=prefix+("canonical_name: %s\n" % self.DebugFormatString(self.canonical_name_))
    cnt=0
    for e in self.aliases_:
      elm=""
      if printElemNumber: elm="(%d)" % cnt
      res+=prefix+("aliases%s: %s\n" % (elm, self.DebugFormatString(e)))
      cnt+=1
    return res


  def _BuildTagLookupTable(sparse, maxtag, default=None):
    return tuple([sparse.get(i, default) for i in xrange(0, 1+maxtag)])

  kpacked_address = 2
  kcanonical_name = 3
  kaliases = 4

  _TEXT = _BuildTagLookupTable({
    0: "ErrorCode",
    2: "packed_address",
    3: "canonical_name",
    4: "aliases",
  }, 4)

  _TYPES = _BuildTagLookupTable({
    0: ProtocolBuffer.Encoder.NUMERIC,
    2: ProtocolBuffer.Encoder.STRING,
    3: ProtocolBuffer.Encoder.STRING,
    4: ProtocolBuffer.Encoder.STRING,
  }, 4, ProtocolBuffer.Encoder.MAX_TYPE)


  _STYLE = """"""
  _STYLE_CONTENT_TYPE = """"""
  _PROTO_DESCRIPTOR_NAME = 'apphosting.ResolveReply'
if _extension_runtime:
  pass

__all__ = ['RemoteSocketServiceError','AddressPort','CreateSocketRequest','CreateSocketReply','BindRequest','BindReply','GetSocketNameRequest','GetSocketNameReply','GetPeerNameRequest','GetPeerNameReply','SocketOption','SetSocketOptionsRequest','SetSocketOptionsReply','GetSocketOptionsRequest','GetSocketOptionsReply','ConnectRequest','ConnectReply','ListenRequest','ListenReply','AcceptRequest','AcceptReply','ShutDownRequest','ShutDownReply','CloseRequest','CloseReply','SendRequest','SendReply','ReceiveRequest','ReceiveReply','PollEvent','PollRequest','PollReply','ResolveRequest','ResolveReply']
