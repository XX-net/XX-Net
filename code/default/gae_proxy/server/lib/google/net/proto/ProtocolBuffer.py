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























import array
import httplib
import re
import struct
try:


  import google.net.proto.proto1 as proto1
except ImportError:

  class ProtocolBufferDecodeError(Exception): pass
  class ProtocolBufferEncodeError(Exception): pass
  class ProtocolBufferReturnError(Exception): pass
else:
  ProtocolBufferDecodeError = proto1.ProtocolBufferDecodeError
  ProtocolBufferEncodeError = proto1.ProtocolBufferEncodeError
  ProtocolBufferReturnError = proto1.ProtocolBufferReturnError

__all__ = ['ProtocolMessage', 'Encoder', 'Decoder',
           'ExtendableProtocolMessage',
           'ProtocolBufferDecodeError',
           'ProtocolBufferEncodeError',
           'ProtocolBufferReturnError']

URL_RE = re.compile('^(https?)://([^/]+)(/.*)$')


class ProtocolMessage:















  def __init__(self, contents=None):


    raise NotImplementedError

  def Clear(self):


    raise NotImplementedError

  def IsInitialized(self, debug_strs=None):

    raise NotImplementedError

  def Encode(self):

    try:
      return self._CEncode()
    except (NotImplementedError, AttributeError):
      e = Encoder()
      self.Output(e)
      return e.buffer().tostring()

  def SerializeToString(self):

    return self.Encode()

  def SerializePartialToString(self):



    try:
      return self._CEncodePartial()
    except (NotImplementedError, AttributeError):
      e = Encoder()
      self.OutputPartial(e)
      return e.buffer().tostring()

  def _CEncode(self):







    raise NotImplementedError

  def _CEncodePartial(self):

    raise NotImplementedError

  def ParseFromString(self, s):



    self.Clear()
    self.MergeFromString(s)

  def ParsePartialFromString(self, s):


    self.Clear()
    self.MergePartialFromString(s)

  def MergeFromString(self, s):



    self.MergePartialFromString(s)
    dbg = []
    if not self.IsInitialized(dbg):
      raise ProtocolBufferDecodeError, '\n\t'.join(dbg)

  def MergePartialFromString(self, s):


    try:
      self._CMergeFromString(s)
    except (NotImplementedError, AttributeError):


      a = array.array('B')
      a.fromstring(s)
      d = Decoder(a, 0, len(a))
      self.TryMerge(d)

  def _CMergeFromString(self, s):









    raise NotImplementedError

  def __getstate__(self):


    return self.Encode()

  def __setstate__(self, contents_):


    self.__init__(contents=contents_)

  def sendCommand(self, server, url, response, follow_redirects=1,
                  secure=0, keyfile=None, certfile=None):















    data = self.Encode()
    if secure:
      if keyfile and certfile:
        conn = httplib.HTTPSConnection(server, key_file=keyfile,
                                       cert_file=certfile)
      else:
        conn = httplib.HTTPSConnection(server)
    else:
      conn = httplib.HTTPConnection(server)
    conn.putrequest("POST", url)
    conn.putheader("Content-Length", "%d" %len(data))
    conn.endheaders()
    conn.send(data)
    resp = conn.getresponse()
    if follow_redirects > 0 and resp.status == 302:
      m = URL_RE.match(resp.getheader('Location'))
      if m:
        protocol, server, url = m.groups()
        return self.sendCommand(server, url, response,
                                follow_redirects=follow_redirects - 1,
                                secure=(protocol == 'https'),
                                keyfile=keyfile,
                                certfile=certfile)
    if resp.status != 200:
      raise ProtocolBufferReturnError(resp.status)
    if response is not None:
      response.ParseFromString(resp.read())
    return response

  def sendSecureCommand(self, server, keyfile, certfile, url, response,
                        follow_redirects=1):















    return self.sendCommand(server, url, response,
                            follow_redirects=follow_redirects,
                            secure=1, keyfile=keyfile, certfile=certfile)

  def __str__(self, prefix="", printElemNumber=0):

    raise NotImplementedError

  def ToASCII(self):

    return self._CToASCII(ProtocolMessage._SYMBOLIC_FULL_ASCII)

  def ToCompactASCII(self):




    return self._CToASCII(ProtocolMessage._NUMERIC_ASCII)

  def ToShortASCII(self):




    return self._CToASCII(ProtocolMessage._SYMBOLIC_SHORT_ASCII)



  _NUMERIC_ASCII = 0
  _SYMBOLIC_SHORT_ASCII = 1
  _SYMBOLIC_FULL_ASCII = 2

  def _CToASCII(self, output_format):





    raise NotImplementedError

  def ParseASCII(self, ascii_string):




    raise NotImplementedError

  def ParseASCIIIgnoreUnknown(self, ascii_string):




    raise NotImplementedError

  def Equals(self, other):




    raise NotImplementedError

  def __eq__(self, other):






    if other.__class__ is self.__class__:
      return self.Equals(other)
    return NotImplemented

  def __ne__(self, other):






    if other.__class__ is self.__class__:
      return not self.Equals(other)
    return NotImplemented





  def Output(self, e):

    dbg = []
    if not self.IsInitialized(dbg):
      raise ProtocolBufferEncodeError, '\n\t'.join(dbg)
    self.OutputUnchecked(e)
    return

  def OutputUnchecked(self, e):

    raise NotImplementedError

  def OutputPartial(self, e):


    raise NotImplementedError

  def Parse(self, d):

    self.Clear()
    self.Merge(d)
    return

  def Merge(self, d):

    self.TryMerge(d)
    dbg = []
    if not self.IsInitialized(dbg):
      raise ProtocolBufferDecodeError, '\n\t'.join(dbg)
    return

  def TryMerge(self, d):

    raise NotImplementedError

  def CopyFrom(self, pb):

    if (pb == self): return
    self.Clear()
    self.MergeFrom(pb)

  def MergeFrom(self, pb):

    raise NotImplementedError





  def lengthVarInt32(self, n):
    return self.lengthVarInt64(n)

  def lengthVarInt64(self, n):
    if n < 0:
      return 10
    result = 0
    while 1:
      result += 1
      n >>= 7
      if n == 0:
        break
    return result

  def lengthString(self, n):
    return self.lengthVarInt32(n) + n

  def DebugFormat(self, value):
    return "%s" % value
  def DebugFormatInt32(self, value):
    if (value <= -2000000000 or value >= 2000000000):
      return self.DebugFormatFixed32(value)
    return "%d" % value
  def DebugFormatInt64(self, value):
    if (value <= -20000000000000 or value >= 20000000000000):
      return self.DebugFormatFixed64(value)
    return "%d" % value
  def DebugFormatString(self, value):



    def escape(c):
      o = ord(c)
      if o == 10: return r"\n"
      if o == 39: return r"\'"

      if o == 34: return r'\"'
      if o == 92: return r"\\"

      if o >= 127 or o < 32: return "\\%03o" % o
      return c
    return '"' + "".join([escape(c) for c in value]) + '"'
  def DebugFormatFloat(self, value):
    return "%ff" % value
  def DebugFormatFixed32(self, value):
    if (value < 0): value += (1L<<32)
    return "0x%x" % value
  def DebugFormatFixed64(self, value):
    if (value < 0): value += (1L<<64)
    return "0x%x" % value
  def DebugFormatBool(self, value):
    if value:
      return "true"
    else:
      return "false"


TYPE_DOUBLE  = 1
TYPE_FLOAT   = 2
TYPE_INT64   = 3
TYPE_UINT64  = 4
TYPE_INT32   = 5
TYPE_FIXED64 = 6
TYPE_FIXED32 = 7
TYPE_BOOL    = 8
TYPE_STRING  = 9
TYPE_GROUP   = 10
TYPE_FOREIGN = 11


_TYPE_TO_DEBUG_STRING = {
    TYPE_INT32:   ProtocolMessage.DebugFormatInt32,
    TYPE_INT64:   ProtocolMessage.DebugFormatInt64,
    TYPE_UINT64:  ProtocolMessage.DebugFormatInt64,
    TYPE_FLOAT:   ProtocolMessage.DebugFormatFloat,
    TYPE_STRING:  ProtocolMessage.DebugFormatString,
    TYPE_FIXED32: ProtocolMessage.DebugFormatFixed32,
    TYPE_FIXED64: ProtocolMessage.DebugFormatFixed64,
    TYPE_BOOL:    ProtocolMessage.DebugFormatBool }



class Encoder:


  NUMERIC     = 0
  DOUBLE      = 1
  STRING      = 2
  STARTGROUP  = 3
  ENDGROUP    = 4
  FLOAT       = 5
  MAX_TYPE    = 6

  def __init__(self):
    self.buf = array.array('B')
    return

  def buffer(self):
    return self.buf

  def put8(self, v):
    if v < 0 or v >= (1<<8): raise ProtocolBufferEncodeError, "u8 too big"
    self.buf.append(v & 255)
    return

  def put16(self, v):
    if v < 0 or v >= (1<<16): raise ProtocolBufferEncodeError, "u16 too big"
    self.buf.append((v >> 0) & 255)
    self.buf.append((v >> 8) & 255)
    return

  def put32(self, v):
    if v < 0 or v >= (1L<<32): raise ProtocolBufferEncodeError, "u32 too big"
    self.buf.append((v >> 0) & 255)
    self.buf.append((v >> 8) & 255)
    self.buf.append((v >> 16) & 255)
    self.buf.append((v >> 24) & 255)
    return

  def put64(self, v):
    if v < 0 or v >= (1L<<64): raise ProtocolBufferEncodeError, "u64 too big"
    self.buf.append((v >> 0) & 255)
    self.buf.append((v >> 8) & 255)
    self.buf.append((v >> 16) & 255)
    self.buf.append((v >> 24) & 255)
    self.buf.append((v >> 32) & 255)
    self.buf.append((v >> 40) & 255)
    self.buf.append((v >> 48) & 255)
    self.buf.append((v >> 56) & 255)
    return

  def putVarInt32(self, v):








    buf_append = self.buf.append
    if v & 127 == v:
      buf_append(v)
      return
    if v >= 0x80000000 or v < -0x80000000:
      raise ProtocolBufferEncodeError, "int32 too big"
    if v < 0:
      v += 0x10000000000000000
    while True:
      bits = v & 127
      v >>= 7
      if v:
        bits |= 128
      buf_append(bits)
      if not v:
        break
    return

  def putVarInt64(self, v):
    buf_append = self.buf.append
    if v >= 0x8000000000000000 or v < -0x8000000000000000:
      raise ProtocolBufferEncodeError, "int64 too big"
    if v < 0:
      v += 0x10000000000000000
    while True:
      bits = v & 127
      v >>= 7
      if v:
        bits |= 128
      buf_append(bits)
      if not v:
        break
    return

  def putVarUint64(self, v):
    buf_append = self.buf.append
    if v < 0 or v >= 0x10000000000000000:
      raise ProtocolBufferEncodeError, "uint64 too big"
    while True:
      bits = v & 127
      v >>= 7
      if v:
        bits |= 128
      buf_append(bits)
      if not v:
        break
    return






  def putFloat(self, v):
    a = array.array('B')
    a.fromstring(struct.pack("<f", v))
    self.buf.extend(a)
    return

  def putDouble(self, v):
    a = array.array('B')
    a.fromstring(struct.pack("<d", v))
    self.buf.extend(a)
    return

  def putBoolean(self, v):
    if v:
      self.buf.append(1)
    else:
      self.buf.append(0)
    return

  def putPrefixedString(self, v):



    v = str(v)
    self.putVarInt32(len(v))
    self.buf.fromstring(v)
    return

  def putRawString(self, v):
    self.buf.fromstring(v)

  _TYPE_TO_METHOD = {
      TYPE_DOUBLE:   putDouble,
      TYPE_FLOAT:    putFloat,
      TYPE_FIXED64:  put64,
      TYPE_FIXED32:  put32,
      TYPE_INT32:    putVarInt32,
      TYPE_INT64:    putVarInt64,
      TYPE_UINT64:   putVarUint64,
      TYPE_BOOL:     putBoolean,
      TYPE_STRING:   putPrefixedString }

  _TYPE_TO_BYTE_SIZE = {
      TYPE_DOUBLE:  8,
      TYPE_FLOAT:   4,
      TYPE_FIXED64: 8,
      TYPE_FIXED32: 4,
      TYPE_BOOL:    1 }

class Decoder:
  def __init__(self, buf, idx, limit):
    self.buf = buf
    self.idx = idx
    self.limit = limit
    return

  def avail(self):
    return self.limit - self.idx

  def buffer(self):
    return self.buf

  def pos(self):
    return self.idx

  def skip(self, n):
    if self.idx + n > self.limit: raise ProtocolBufferDecodeError, "truncated"
    self.idx += n
    return

  def skipData(self, tag):
    t = tag & 7
    if t == Encoder.NUMERIC:
      self.getVarInt64()
    elif t == Encoder.DOUBLE:
      self.skip(8)
    elif t == Encoder.STRING:
      n = self.getVarInt32()
      self.skip(n)
    elif t == Encoder.STARTGROUP:
      while 1:
        t = self.getVarInt32()
        if (t & 7) == Encoder.ENDGROUP:
          break
        else:
          self.skipData(t)
      if (t - Encoder.ENDGROUP) != (tag - Encoder.STARTGROUP):
        raise ProtocolBufferDecodeError, "corrupted"
    elif t == Encoder.ENDGROUP:
      raise ProtocolBufferDecodeError, "corrupted"
    elif t == Encoder.FLOAT:
      self.skip(4)
    else:
      raise ProtocolBufferDecodeError, "corrupted"


  def get8(self):
    if self.idx >= self.limit: raise ProtocolBufferDecodeError, "truncated"
    c = self.buf[self.idx]
    self.idx += 1
    return c

  def get16(self):
    if self.idx + 2 > self.limit: raise ProtocolBufferDecodeError, "truncated"
    c = self.buf[self.idx]
    d = self.buf[self.idx + 1]
    self.idx += 2
    return (d << 8) | c

  def get32(self):
    if self.idx + 4 > self.limit: raise ProtocolBufferDecodeError, "truncated"
    c = self.buf[self.idx]
    d = self.buf[self.idx + 1]
    e = self.buf[self.idx + 2]
    f = long(self.buf[self.idx + 3])
    self.idx += 4
    return (f << 24) | (e << 16) | (d << 8) | c

  def get64(self):
    if self.idx + 8 > self.limit: raise ProtocolBufferDecodeError, "truncated"
    c = self.buf[self.idx]
    d = self.buf[self.idx + 1]
    e = self.buf[self.idx + 2]
    f = long(self.buf[self.idx + 3])
    g = long(self.buf[self.idx + 4])
    h = long(self.buf[self.idx + 5])
    i = long(self.buf[self.idx + 6])
    j = long(self.buf[self.idx + 7])
    self.idx += 8
    return ((j << 56) | (i << 48) | (h << 40) | (g << 32) | (f << 24)
            | (e << 16) | (d << 8) | c)

  def getVarInt32(self):



    b = self.get8()
    if not (b & 128):
      return b

    result = long(0)
    shift = 0

    while 1:
      result |= (long(b & 127) << shift)
      shift += 7
      if not (b & 128):
        if result >= 0x10000000000000000L:
          raise ProtocolBufferDecodeError, "corrupted"
        break
      if shift >= 64: raise ProtocolBufferDecodeError, "corrupted"
      b = self.get8()

    if result >= 0x8000000000000000L:
      result -= 0x10000000000000000L
    if result >= 0x80000000L or result < -0x80000000L:
      raise ProtocolBufferDecodeError, "corrupted"
    return result

  def getVarInt64(self):
    result = self.getVarUint64()
    if result >= (1L << 63):
      result -= (1L << 64)
    return result

  def getVarUint64(self):
    result = long(0)
    shift = 0
    while 1:
      if shift >= 64: raise ProtocolBufferDecodeError, "corrupted"
      b = self.get8()
      result |= (long(b & 127) << shift)
      shift += 7
      if not (b & 128):
        if result >= (1L << 64): raise ProtocolBufferDecodeError, "corrupted"
        return result
    return result

  def getFloat(self):
    if self.idx + 4 > self.limit: raise ProtocolBufferDecodeError, "truncated"
    a = self.buf[self.idx:self.idx+4]
    self.idx += 4
    return struct.unpack("<f", a)[0]

  def getDouble(self):
    if self.idx + 8 > self.limit: raise ProtocolBufferDecodeError, "truncated"
    a = self.buf[self.idx:self.idx+8]
    self.idx += 8
    return struct.unpack("<d", a)[0]

  def getBoolean(self):
    b = self.get8()
    if b != 0 and b != 1: raise ProtocolBufferDecodeError, "corrupted"
    return b

  def getPrefixedString(self):
    length = self.getVarInt32()
    if self.idx + length > self.limit:
      raise ProtocolBufferDecodeError, "truncated"
    r = self.buf[self.idx : self.idx + length]
    self.idx += length
    return r.tostring()

  def getRawString(self):
    r = self.buf[self.idx:self.limit]
    self.idx = self.limit
    return r.tostring()

  _TYPE_TO_METHOD = {
      TYPE_DOUBLE:   getDouble,
      TYPE_FLOAT:    getFloat,
      TYPE_FIXED64:  get64,
      TYPE_FIXED32:  get32,
      TYPE_INT32:    getVarInt32,
      TYPE_INT64:    getVarInt64,
      TYPE_UINT64:   getVarUint64,
      TYPE_BOOL:     getBoolean,
      TYPE_STRING:   getPrefixedString }





class ExtensionIdentifier(object):
  __slots__ = ('full_name', 'number', 'field_type', 'wire_tag', 'is_repeated',
               'default', 'containing_cls', 'composite_cls', 'message_name')
  def __init__(self, full_name, number, field_type, wire_tag, is_repeated,
               default):
    self.full_name = full_name
    self.number = number
    self.field_type = field_type
    self.wire_tag = wire_tag
    self.is_repeated = is_repeated
    self.default = default

class ExtendableProtocolMessage(ProtocolMessage):
  def HasExtension(self, extension):

    self._VerifyExtensionIdentifier(extension)
    return extension in self._extension_fields

  def ClearExtension(self, extension):


    self._VerifyExtensionIdentifier(extension)
    if extension in self._extension_fields:
      del self._extension_fields[extension]

  def GetExtension(self, extension, index=None):











    self._VerifyExtensionIdentifier(extension)
    if extension in self._extension_fields:
      result = self._extension_fields[extension]
    else:
      if extension.is_repeated:
        result = []
      elif extension.composite_cls:
        result = extension.composite_cls()
      else:
        result = extension.default
    if extension.is_repeated:
      result = result[index]
    return result

  def SetExtension(self, extension, *args):
















    self._VerifyExtensionIdentifier(extension)
    if extension.composite_cls:
      raise TypeError(
          'Cannot assign to extension "%s" because it is a composite type.' %
          extension.full_name)
    if extension.is_repeated:
      if (len(args) != 2):
        raise TypeError(
            'SetExtension(extension, index, value) for repeated extension '
            'takes exactly 3 arguments: (%d given)' % len(args))
      index = args[0]
      value = args[1]
      self._extension_fields[extension][index] = value
    else:
      if (len(args) != 1):
        raise TypeError(
            'SetExtension(extension, value) for singular extension '
            'takes exactly 3 arguments: (%d given)' % len(args))
      value = args[0]
      self._extension_fields[extension] = value

  def MutableExtension(self, extension, index=None):

















    self._VerifyExtensionIdentifier(extension)
    if extension.composite_cls is None:
      raise TypeError(
          'MutableExtension() cannot be applied to "%s", because it is not a '
          'composite type.' % extension.full_name)
    if extension.is_repeated:
      if index is None:
        raise TypeError(
            'MutableExtension(extension, index) for repeated extension '
            'takes exactly 2 arguments: (1 given)')
      return self.GetExtension(extension, index)
    if extension in self._extension_fields:
      return self._extension_fields[extension]
    else:
      result = extension.composite_cls()
      self._extension_fields[extension] = result
      return result

  def ExtensionList(self, extension):





    self._VerifyExtensionIdentifier(extension)
    if not extension.is_repeated:
      raise TypeError(
          'ExtensionList() cannot be applied to "%s", because it is not a '
          'repeated extension.' % extension.full_name)
    if extension in self._extension_fields:
      return self._extension_fields[extension]
    result = []
    self._extension_fields[extension] = result
    return result

  def ExtensionSize(self, extension):





    self._VerifyExtensionIdentifier(extension)
    if not extension.is_repeated:
      raise TypeError(
          'ExtensionSize() cannot be applied to "%s", because it is not a '
          'repeated extension.' % extension.full_name)
    if extension in self._extension_fields:
      return len(self._extension_fields[extension])
    return 0

  def AddExtension(self, extension, value=None):





















    self._VerifyExtensionIdentifier(extension)
    if not extension.is_repeated:
      raise TypeError(
          'AddExtension() cannot be applied to "%s", because it is not a '
          'repeated extension.' % extension.full_name)
    if extension in self._extension_fields:
      field = self._extension_fields[extension]
    else:
      field = []
      self._extension_fields[extension] = field

    if extension.composite_cls:
      if value is not None:
        raise TypeError(
            'value must not be set in AddExtension() for "%s", because it is '
            'a message type extension. Set values on the returned message '
            'instead.' % extension.full_name)
      msg = extension.composite_cls()
      field.append(msg)
      return msg

    field.append(value)

  def _VerifyExtensionIdentifier(self, extension):
    if extension.containing_cls != self.__class__:
      raise TypeError("Containing type of %s is %s, but not %s."
                      % (extension.full_name,
                         extension.containing_cls.__name__,
                         self.__class__.__name__))

  def _MergeExtensionFields(self, x):
    for ext, val in x._extension_fields.items():
      if ext.is_repeated:
        for i in xrange(len(val)):
          if ext.composite_cls is None:
            self.AddExtension(ext, val[i])
          else:
            self.AddExtension(ext).MergeFrom(val[i])
      else:
        if ext.composite_cls is None:
          self.SetExtension(ext, val)
        else:
          self.MutableExtension(ext).MergeFrom(val)

  def _ListExtensions(self):
    result = [ext for ext in self._extension_fields.keys()
              if (not ext.is_repeated) or self.ExtensionSize(ext) > 0]
    result.sort(key = lambda item: item.number)
    return result

  def _ExtensionEquals(self, x):
    extensions = self._ListExtensions()
    if extensions != x._ListExtensions():
      return False
    for ext in extensions:
      if ext.is_repeated:
        if self.ExtensionSize(ext) != x.ExtensionSize(ext): return False
        for e1, e2 in zip(self.ExtensionList(ext),
                          x.ExtensionList(ext)):
          if e1 != e2: return False
      else:
        if self.GetExtension(ext) != x.GetExtension(ext): return False
    return True

  def _OutputExtensionFields(self, out, partial, extensions, start_index,
                             end_field_number):

























    def OutputSingleField(ext, value):
      out.putVarInt32(ext.wire_tag)
      if ext.field_type == TYPE_GROUP:
        if partial:
          value.OutputPartial(out)
        else:
          value.OutputUnchecked(out)
        out.putVarInt32(ext.wire_tag + 1)
      elif ext.field_type == TYPE_FOREIGN:
        if partial:
          out.putVarInt32(value.ByteSizePartial())
          value.OutputPartial(out)
        else:
          out.putVarInt32(value.ByteSize())
          value.OutputUnchecked(out)
      else:
        Encoder._TYPE_TO_METHOD[ext.field_type](out, value)

    size = len(extensions)
    for ext_index in xrange(start_index, size):
      ext = extensions[ext_index]
      if ext.number >= end_field_number:

        return ext_index
      if ext.is_repeated:
        for i in xrange(len(self._extension_fields[ext])):
          OutputSingleField(ext, self._extension_fields[ext][i])
      else:
        OutputSingleField(ext, self._extension_fields[ext])
    return size

  def _ParseOneExtensionField(self, wire_tag, d):
    number = wire_tag >> 3
    if number in self._extensions_by_field_number:
      ext = self._extensions_by_field_number[number]
      if wire_tag != ext.wire_tag:

        return
      if ext.field_type == TYPE_FOREIGN:
        length = d.getVarInt32()
        tmp = Decoder(d.buffer(), d.pos(), d.pos() + length)
        if ext.is_repeated:
          self.AddExtension(ext).TryMerge(tmp)
        else:
          self.MutableExtension(ext).TryMerge(tmp)
        d.skip(length)
      elif ext.field_type == TYPE_GROUP:
        if ext.is_repeated:
          self.AddExtension(ext).TryMerge(d)
        else:
          self.MutableExtension(ext).TryMerge(d)
      else:
        value = Decoder._TYPE_TO_METHOD[ext.field_type](d)
        if ext.is_repeated:
          self.AddExtension(ext, value)
        else:
          self.SetExtension(ext, value)
    else:

      d.skipData(wire_tag)

  def _ExtensionByteSize(self, partial):
    size = 0
    for extension, value in self._extension_fields.items():
      ftype = extension.field_type
      tag_size = self.lengthVarInt64(extension.wire_tag)
      if ftype == TYPE_GROUP:
        tag_size *= 2
      if extension.is_repeated:
        size += tag_size * len(value)
        for single_value in value:
          size += self._FieldByteSize(ftype, single_value, partial)
      else:
        size += tag_size + self._FieldByteSize(ftype, value, partial)
    return size

  def _FieldByteSize(self, ftype, value, partial):
    size = 0
    if ftype == TYPE_STRING:
      size = self.lengthString(len(value))
    elif ftype == TYPE_FOREIGN or ftype == TYPE_GROUP:
      if partial:
        size = self.lengthString(value.ByteSizePartial())
      else:
        size = self.lengthString(value.ByteSize())
    elif ftype == TYPE_INT64 or ftype == TYPE_UINT64 or ftype == TYPE_INT32:
      size = self.lengthVarInt64(value)
    else:
      if ftype in Encoder._TYPE_TO_BYTE_SIZE:
        size = Encoder._TYPE_TO_BYTE_SIZE[ftype]
      else:
        raise AssertionError(
            'Extension type %d is not recognized.' % ftype)
    return size

  def _ExtensionDebugString(self, prefix, printElemNumber):
    res = ''
    extensions = self._ListExtensions()
    for extension in extensions:
      value = self._extension_fields[extension]
      if extension.is_repeated:
        cnt = 0
        for e in value:
          elm=""
          if printElemNumber: elm = "(%d)" % cnt
          if extension.composite_cls is not None:
            res += prefix + "[%s%s] {\n" % (extension.full_name, elm)
            res += e.__str__(prefix + "  ", printElemNumber)
            res += prefix + "}\n"
      else:
        if extension.composite_cls is not None:
          res += prefix + "[%s] {\n" % extension.full_name
          res += value.__str__(
              prefix + "  ", printElemNumber)
          res += prefix + "}\n"
        else:
          if extension.field_type in _TYPE_TO_DEBUG_STRING:
            text_value = _TYPE_TO_DEBUG_STRING[
                extension.field_type](self, value)
          else:
            text_value = self.DebugFormat(value)
          res += prefix + "[%s]: %s\n" % (extension.full_name, text_value)
    return res

  @staticmethod
  def _RegisterExtension(cls, extension, composite_cls=None):
    extension.containing_cls = cls
    extension.composite_cls = composite_cls
    if composite_cls is not None:
      extension.message_name = composite_cls._PROTO_DESCRIPTOR_NAME
    actual_handle = cls._extensions_by_field_number.setdefault(
        extension.number, extension)
    if actual_handle is not extension:
      raise AssertionError(
          'Extensions "%s" and "%s" both try to extend message type "%s" with '
          'field number %d.' %
          (extension.full_name, actual_handle.full_name,
           cls.__name__, extension.number))
