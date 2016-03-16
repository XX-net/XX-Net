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
"""IP address helper functions.

This file contains alternative implementations of the following functions
normally provided by the system:

  - inet_(ntop|pton)
  - inet_(ntoa|aton)
  - (hton|ntoh)(sl)
"""

import errno
import os
import re
import struct
import sys



from google.appengine.api.remote_socket._remote_socket_error import *


AF_UNSPEC = 0
AF_UNIX = 1
AF_INET = 2
AF_INET6 = 30


def _TypeName(obj):
  if obj is None:
    return 'None'
  return type(obj).__name__


def _LongestRun(seq, value):
  """Finds the longest run (i.e. repeated adjacent values) of value in seq.

  Args:
    seq: A sequence to scan for runs.
    value: A value to scan for in seq.

  Returns:
    A tuple of the offset and run length for the longest run of value within
    seq, or (-1, 0) if value does not occur within seq.
  """
  off = -1
  max_run = 0
  i = 0
  while i < len(seq):
    run = 0
    while i + run < len(seq) and seq[i+run] == value:
      run += 1
    if run > max_run:
      off = i
      max_run = run
    i += 1 + run
  return off, max_run


def _GetBase(text):
  if text[:2].lower() == '0x':
    return 16
  elif text[:1] == '0':
    return 8
  return 10


def ntohs(integer):
  """ntohs(integer) -> integer

  Convert a 16-bit integer from network to host byte order.
  """
  if sys.byteorder == 'big':
    return integer
  if not isinstance(integer, (int, long)):
    raise TypeError('an integer is required')
  if integer < 0:
    raise OverflowError("can't convert negative number to unsigned long")
  if integer >= (1<<16):
    raise OverflowError('signed integer is greater than maximum')
  return int(
      ((integer&0xff00)>>8)|
      ((integer&0x00ff)<<8))


def ntohl(integer):
  """ntohl(integer) -> integer

  Convert a 32-bit integer from network to host byte order.
  """
  if sys.byteorder == 'big':
    return integer
  if not isinstance(integer, (int, long)):
    raise TypeError('expected int/long, %s found' % _TypeName(integer))
  if integer < 0:
    raise OverflowError('can\'t convert negative number to unsigned long')
  if integer >= (1<<32):
    raise OverflowError('long int larger than 32 bits')
  return int(
      ((integer&0xff000000)>>24)|
      ((integer&0x00ff0000)>>8)|
      ((integer&0x0000ff00)<<8)|
      ((integer&0x000000ff)<<24))


def htons(integer):
  """htons(integer) -> integer

  Convert a 16-bit integer from host to network byte order.
  """
  return ntohs(integer)


def htonl(integer):
  """htonl(integer) -> integer

  Convert a 32-bit integer from host to network byte order.
  """
  return ntohl(integer)


def inet_aton(ip_string):
  """inet_aton(string) -> packed 32-bit IP representation

  Convert an IP address in string format (123.45.67.89) to the 32-bit packed
  binary format used in low-level network functions.
  """

  if not isinstance(ip_string, basestring):
    raise error('inet_aton() argument 1 must be string, not %s' %
                _TypeName(ip_string))
  try:
    ret = 0
    bits = 32
    parts = [int(s, _GetBase(s)) for s in ip_string.split('.')]
    assert len(parts) >= 1 and len(parts) <= 4
    for n in parts[:-1]:
      assert n >= 0 and n <= 0xff
      bits -= 8
      ret |= ((n & 0xff) << bits)
    assert parts[-1] >= 0 and parts[-1] < (1 << bits)
    ret |= parts[-1]
    return struct.pack('!L', ret)
  except:
    raise error('illegal IP address string passed to inet_aton')


def inet_ntoa(packed_ip):
  """inet_ntoa(packed_ip) -> ip_address_string

  Convert an IP address from 32-bit packed binary format to string format
  """

  if not isinstance(packed_ip, basestring):
    raise TypeError('inet_ntoa() argument 1 must be string or read-only '
                    'buffer, not %s' % _TypeName(packed_ip))
  if len(packed_ip) != 4:
    raise error('packed IP wrong length for inet_ntoa')
  return '%u.%u.%u.%u' % struct.unpack('4B', packed_ip)


def inet_pton(af, ip):
  """inet_pton(af, ip) -> packed IP address string

  Convert an IP address from string format to a packed string suitable
  for use with low-level network functions.
  """

  if not isinstance(af, (int, long)):
    raise TypeError('an integer is required')
  if not isinstance(ip, basestring):
    raise TypeError('inet_pton() argument 2 must be string, not %s' %
                    _TypeName(ip))
  if af == AF_INET:
    parts = ip.split('.')
    if len(parts) != 4:
      raise error('illegal IP address string passed to inet_pton')
    ret = 0
    bits = 32
    for part in parts:
      if not re.match(r'^(0|[1-9]\d*)$', part) or int(part) > 0xff:
        raise error('illegal IP address string passed to inet_pton')
      bits -= 8
      ret |= ((int(part) & 0xff) << bits)
    return struct.pack('!L', ret)
  elif af == AF_INET6:
    parts = ip.split(':')

    if '.' in parts[-1]:
      ipv4_shorts = struct.unpack('!2H', inet_pton(AF_INET, parts[-1]))
      parts[-1:] = [hex(n)[2:] for n in ipv4_shorts]

    if '' in parts:
      if len(parts) == 1 or len(parts) >= 8:
        raise error('illegal IP address string passed to inet_pton')

      idx = parts.index('')
      count = parts.count('')
      pad = ['0']*(count+(8-len(parts)))

      if count == len(parts) == 3:
        parts = pad
      elif count == 2 and parts[0:2] == ['', '']:
        parts[0:2] = pad
      elif count == 2 and parts[-2:] == ['', '']:
        parts[-2:] = pad
      elif count == 1:
        parts[idx:idx+1] = pad
      else:
        raise error('illegal IP address string passed to inet_pton')
    if (len(parts) != 8 or
        [x for x in parts if not re.match(r'^[0-9A-Fa-f]{1,4}$', x)]):
      raise error('illegal IP address string passed to inet_pton')
    return struct.pack('!8H', *[int(x, 16) for x in parts])
  else:
    raise error(errno.EAFNOSUPPORT, os.strerror(errno.EAFNOSUPPORT))


def inet_ntop(af, packed_ip):
  """inet_ntop(af, packed_ip) -> string formatted IP address

  Convert a packed IP address of the given family to string format.
  """
  if not isinstance(af, (int, long)):
    raise TypeError('an integer is required')
  if not isinstance(packed_ip, basestring):
    raise TypeError('inet_ntop() argument 2 must be string or read-only '
                    'buffer, not %s' % _TypeName(packed_ip))
  if af == AF_INET:
    if len(packed_ip) != 4:
      raise ValueError('invalid length of packed IP address string')
    return '%u.%u.%u.%u' % struct.unpack('4B', packed_ip)
  elif af == AF_INET6:
    if len(packed_ip) != 16:
      raise ValueError('invalid length of packed IP address string')
    parts = [hex(n)[2:] for n in struct.unpack('!8H', packed_ip)]

    if (':'.join(parts[:-2]) in ('0:0:0:0:0:0', '0:0:0:0:0:ffff') and
        ':'.join(parts) not in ('0:0:0:0:0:0:0:0', '0:0:0:0:0:0:0:1')):
      parts[-2:] = [inet_ntop(AF_INET, packed_ip[-4:])]
    off, run = _LongestRun(parts, '0')
    if run >= 2:
      pad = ['']
      if off == 0:
        pad.append('')
      if off + run == len(parts):
        pad.append('')
      parts[off:off+run] = pad
    return ':'.join(parts)
  else:
    raise ValueError('unknown address family %u' % af)
