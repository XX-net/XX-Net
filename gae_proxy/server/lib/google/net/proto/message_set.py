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





"""This module contains the MessageSet class, which is a special kind of
protocol message which can contain other protocol messages without knowing
their types.  See the class's doc string for more information."""








from google.net.proto import ProtocolBuffer
import logging



try:
  from google3.net.proto import _net_proto___parse__python
except ImportError:
  _net_proto___parse__python = None


TAG_BEGIN_ITEM_GROUP = 11
TAG_END_ITEM_GROUP   = 12
TAG_TYPE_ID          = 16
TAG_MESSAGE          = 26

class Item:







  def __init__(self, message, message_class=None):
    self.message = message
    self.message_class = message_class

  def SetToDefaultInstance(self, message_class):
    self.message = message_class()
    self.message_class = message_class

  def Parse(self, message_class):


    if self.message_class is not None:
      return 1

    try:
      message_obj = message_class()
      message_obj.MergePartialFromString(self.message)
      self.message = message_obj
      self.message_class = message_class
      return 1
    except ProtocolBuffer.ProtocolBufferDecodeError:
      logging.warn("Parse error in message inside MessageSet.  Tried "
                   "to parse as: " + message_class.__name__)
      return 0

  def MergeFrom(self, other):





    if self.message_class is not None:
      if other.Parse(self.message_class):
        self.message.MergeFrom(other.message)



    elif other.message_class is not None:
      if not self.Parse(other.message_class):

        self.message = other.message_class()
        self.message_class = other.message_class
      self.message.MergeFrom(other.message)

    else:
      self.message += other.message

  def Copy(self):


    if self.message_class is None:
      return Item(self.message)
    else:
      new_message = self.message_class()
      new_message.CopyFrom(self.message)
      return Item(new_message, self.message_class)

  def Equals(self, other):





    if self.message_class is not None:
      if not other.Parse(self.message_class): return 0
      return self.message.Equals(other.message)

    elif other.message_class is not None:
      if not self.Parse(other.message_class): return 0
      return self.message.Equals(other.message)

    else:
      return self.message == other.message

  def IsInitialized(self, debug_strs=None):



    if self.message_class is None:
      return 1
    else:
      return self.message.IsInitialized(debug_strs)

  def ByteSize(self, pb, type_id):


    message_length = 0
    if self.message_class is None:
      message_length = len(self.message)
    else:
      message_length = self.message.ByteSize()


    return pb.lengthString(message_length) + pb.lengthVarInt64(type_id) + 2

  def ByteSizePartial(self, pb, type_id):


    message_length = 0
    if self.message_class is None:
      message_length = len(self.message)
    else:
      message_length = self.message.ByteSizePartial()


    return pb.lengthString(message_length) + pb.lengthVarInt64(type_id) + 2

  def OutputUnchecked(self, out, type_id):


    out.putVarInt32(TAG_TYPE_ID)




    out.putVarUint64(type_id)
    out.putVarInt32(TAG_MESSAGE)
    if self.message_class is None:
      out.putPrefixedString(self.message)
    else:
      out.putVarInt32(self.message.ByteSize())
      self.message.OutputUnchecked(out)

  def OutputPartial(self, out, type_id):



    out.putVarInt32(TAG_TYPE_ID)




    out.putVarUint64(type_id)
    out.putVarInt32(TAG_MESSAGE)
    if self.message_class is None:
      out.putPrefixedString(self.message)
    else:
      out.putVarInt32(self.message.ByteSizePartial())
      self.message.OutputPartial(out)

  def Decode(decoder):




    type_id = 0
    message = None
    while 1:
      tag = decoder.getVarInt32()
      if tag == TAG_END_ITEM_GROUP:
        break
      if tag == TAG_TYPE_ID:




        type_id = decoder.getVarUint64()
        continue
      if tag == TAG_MESSAGE:
        message = decoder.getPrefixedString()
        continue


      if tag == 0: raise ProtocolBuffer.ProtocolBufferDecodeError
      decoder.skipData(tag)

    if type_id == 0 or message is None:
      raise ProtocolBuffer.ProtocolBufferDecodeError
    return (type_id, message)
  Decode = staticmethod(Decode)


class MessageSet(ProtocolBuffer.ProtocolMessage):



































  def __init__(self, contents=None):


    self.items = dict()
    if contents is not None: self.MergeFromString(contents)




  def get(self, message_class):











    if message_class.MESSAGE_TYPE_ID not in self.items:
      return message_class()
    item = self.items[message_class.MESSAGE_TYPE_ID]
    if item.Parse(message_class):
      return item.message
    else:
      return message_class()

  def mutable(self, message_class):






    if message_class.MESSAGE_TYPE_ID not in self.items:
      message = message_class()
      self.items[message_class.MESSAGE_TYPE_ID] = Item(message, message_class)
      return message
    item = self.items[message_class.MESSAGE_TYPE_ID]
    if not item.Parse(message_class):
      item.SetToDefaultInstance(message_class)
    return item.message

  def has(self, message_class):


    if message_class.MESSAGE_TYPE_ID not in self.items:
      return 0
    item = self.items[message_class.MESSAGE_TYPE_ID]
    return item.Parse(message_class)

  def has_unparsed(self, message_class):






    return message_class.MESSAGE_TYPE_ID in self.items

  def GetTypeIds(self):






    return self.items.keys()

  def NumMessages(self):







    return len(self.items)

  def remove(self, message_class):

    if message_class.MESSAGE_TYPE_ID in self.items:
      del self.items[message_class.MESSAGE_TYPE_ID]




  def __getitem__(self, message_class):
    if message_class.MESSAGE_TYPE_ID not in self.items:
      raise KeyError(message_class)
    item = self.items[message_class.MESSAGE_TYPE_ID]
    if item.Parse(message_class):
      return item.message
    else:
      raise KeyError(message_class)

  def __setitem__(self, message_class, message):
    self.items[message_class.MESSAGE_TYPE_ID] = Item(message, message_class)

  def __contains__(self, message_class):
    return self.has(message_class)

  def __delitem__(self, message_class):
    self.remove(message_class)

  def __len__(self):
    return len(self.items)




  def MergeFrom(self, other):






    assert other is not self

    for (type_id, item) in other.items.items():
      if type_id in self.items:
        self.items[type_id].MergeFrom(item)
      else:
        self.items[type_id] = item.Copy()

  def Equals(self, other):

    if other is self: return 1
    if len(self.items) != len(other.items): return 0

    for (type_id, item) in other.items.items():
      if type_id not in self.items: return 0
      if not self.items[type_id].Equals(item): return 0

    return 1

  def __eq__(self, other):
    return ((other is not None)
        and (other.__class__ == self.__class__)
        and self.Equals(other))

  def __ne__(self, other):
    return not (self == other)

  def IsInitialized(self, debug_strs=None):



    initialized = 1
    for item in self.items.values():
      if not item.IsInitialized(debug_strs):
        initialized = 0
    return initialized

  def ByteSize(self):

    n = 2 * len(self.items)
    for (type_id, item) in self.items.items():
      n += item.ByteSize(self, type_id)
    return n

  def ByteSizePartial(self):


    n = 2 * len(self.items)
    for (type_id, item) in self.items.items():
      n += item.ByteSizePartial(self, type_id)
    return n

  def Clear(self):

    self.items = dict()

  def OutputUnchecked(self, out):

    for (type_id, item) in self.items.items():
      out.putVarInt32(TAG_BEGIN_ITEM_GROUP)
      item.OutputUnchecked(out, type_id)
      out.putVarInt32(TAG_END_ITEM_GROUP)

  def OutputPartial(self, out):


    for (type_id, item) in self.items.items():
      out.putVarInt32(TAG_BEGIN_ITEM_GROUP)
      item.OutputPartial(out, type_id)
      out.putVarInt32(TAG_END_ITEM_GROUP)

  def TryMerge(self, decoder):


    while decoder.avail() > 0:
      tag = decoder.getVarInt32()
      if tag == TAG_BEGIN_ITEM_GROUP:
        (type_id, message) = Item.Decode(decoder)
        if type_id in self.items:
          self.items[type_id].MergeFrom(Item(message))
        else:
          self.items[type_id] = Item(message)
        continue


      if (tag == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      decoder.skipData(tag)


  def _CToASCII(self, output_format):
    if _net_proto___parse__python is None:
      return ProtocolBuffer.ProtocolMessage._CToASCII(self, output_format)
    else:
      return _net_proto___parse__python.ToASCII(
          self, "MessageSetInternal", output_format)

  def ParseASCII(self, s):
    if _net_proto___parse__python is None:
      ProtocolBuffer.ProtocolMessage.ParseASCII(self, s)
    else:
      _net_proto___parse__python.ParseASCII(self, "MessageSetInternal", s)

  def ParseASCIIIgnoreUnknown(self, s):
    if _net_proto___parse__python is None:
      ProtocolBuffer.ProtocolMessage.ParseASCIIIgnoreUnknown(self, s)
    else:
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(
          self, "MessageSetInternal", s)







  def __str__(self, prefix="", printElemNumber=0):
    text = ""
    for (type_id, item) in self.items.items():
      if item.message_class is None:
        text += "%s[%d] <\n" % (prefix, type_id)
        text += "%s  (%d bytes)\n" % (prefix, len(item.message))
        text += "%s>\n" % prefix
      else:
        text += "%s[%s] <\n" % (prefix, item.message_class.__name__)
        text += item.message.__str__(prefix + "  ", printElemNumber)
        text += "%s>\n" % prefix
    return text


  _PROTO_DESCRIPTOR_NAME = 'MessageSet'

__all__ = ['MessageSet']
