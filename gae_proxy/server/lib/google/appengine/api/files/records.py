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




"""Files API.

.. deprecated:: 1.8.1
   Use Google Cloud Storage Client library instead.

Lightweight record format.

This format implements log file format from leveldb:
http://leveldb.googlecode.com/svn/trunk/doc/log_format.txt

Full specification of format follows in case leveldb decides to change it.


The log file contents are a sequence of 32KB blocks.  The only
exception is that the tail of the file may contain a partial block.

Each block consists of a sequence of records:
   block := record* trailer?
   record :=
      checksum: uint32  // masked crc32c of type and data[]
      length: uint16
      type: uint8       // One of FULL, FIRST, MIDDLE, LAST
      data: uint8[length]

A record never starts within the last six bytes of a block (since it
won't fit).  Any leftover bytes here form the trailer, which must
consist entirely of zero bytes and must be skipped by readers.

Aside: if exactly seven bytes are left in the current block, and a new
non-zero length record is added, the writer must emit a FIRST record
(which contains zero bytes of user data) to fill up the trailing seven
bytes of the block and then emit all of the user data in subsequent
blocks.

More types may be added in the future.  Some Readers may skip record
types they do not understand, others may report that some data was
skipped.

FULL == 1
FIRST == 2
MIDDLE == 3
LAST == 4

The FULL record contains the contents of an entire user record.

FIRST, MIDDLE, LAST are types used for user records that have been
split into multiple fragments (typically because of block boundaries).
FIRST is the type of the first fragment of a user record, LAST is the
type of the last fragment of a user record, and MID is the type of all
interior fragments of a user record.

Example: consider a sequence of user records:
   A: length 1000
   B: length 97270
   C: length 8000
A will be stored as a FULL record in the first block.

B will be split into three fragments: first fragment occupies the rest
of the first block, second fragment occupies the entirety of the
second block, and the third fragment occupies a prefix of the third
block.  This will leave six bytes free in the third block, which will
be left empty as the trailer.

C will be stored as a FULL record in the fourth block.

"""



import logging
import struct

import google
from google.appengine.api.files import crc32c



BLOCK_SIZE = 32 * 1024


HEADER_FORMAT = '<IHB'


HEADER_LENGTH = struct.calcsize(HEADER_FORMAT)


RECORD_TYPE_NONE = 0


RECORD_TYPE_FULL = 1


RECORD_TYPE_FIRST = 2


RECORD_TYPE_MIDDLE = 3


RECORD_TYPE_LAST = 4


class Error(Exception):
  """Base class for exceptions in this module."""


class InvalidRecordError(Error):
  """Raised when invalid record encountered."""


class FileWriter(object):
  """Interface specification for writers to be used with records module."""

  def write(self, data):
    """Write data to the file.

    Args:
      data: byte array, string or iterable over bytes.
    """
    raise NotImplementedError()


class FileReader(object):
  """Interface specification for writers to be used with recordrecords module.

  FileReader defines a reader with position and efficient seek/position
  determining. All reads occur at current position.
  """

  def read(self, size):
    """Read data from file.

    Reads data from current position and advances position past the read data
    block.

    Args:
      size: number of bytes to read.
    Returns:
      iterable over bytes. If number of bytes read is less then 'size' argument,
      it is assumed that end of file was reached.
    """
    raise NotImplementedError()

  def tell(self):
    """Get current file position.

    Returns:
      current position as a byte offset in the file as integer.
    """
    raise NotImplementedError()


_CRC_MASK_DELTA = 0xa282ead8

def _mask_crc(crc):
  """Mask crc.

  Args:
    crc: integer crc.
  Returns:
    masked integer crc.
  """
  return (((crc >> 15) | (crc << 17)) + _CRC_MASK_DELTA) & 0xFFFFFFFFL


def _unmask_crc(masked_crc):
  """Unmask crc.

  Args:
    masked_crc: masked integer crc.
  Retruns:
    orignal crc.
  """
  rot = (masked_crc - _CRC_MASK_DELTA) & 0xFFFFFFFFL
  return ((rot >> 17) | (rot << 15)) & 0xFFFFFFFFL


class RecordsWriter(object):
  """A writer for records format.

  This writer should be used only inside with statement:

    with records.RecordsWriter(file) as writer:
      writer.write("record")

  RecordsWriter will pad last block with 0 when exiting with statement scope.
  """

  def __init__(self, writer, _pad_last_block=True):
    """Constructor.

    Args:
      writer: a writer to use. Should conform to FileWriter interface.
    """
    self.__writer = writer
    self.__position = 0
    self.__entered = False
    self.__pad_last_block = _pad_last_block

  def __write_record(self, record_type, data):
    """Write single physical record."""
    length = len(data)

    crc = crc32c.crc_update(crc32c.CRC_INIT, [record_type])
    crc = crc32c.crc_update(crc, data)
    crc = crc32c.crc_finalize(crc)

    self.__writer.write(
        struct.pack(HEADER_FORMAT, _mask_crc(crc), length, record_type))
    self.__writer.write(data)
    self.__position += HEADER_LENGTH + length

  def write(self, data):
    """Write single record.

    Args:
      data: record data to write as string, byte array or byte sequence.
    """
    if not self.__entered:
      raise Exception("RecordWriter should be used only with 'with' statement.")
    block_remaining = BLOCK_SIZE - self.__position % BLOCK_SIZE

    if block_remaining < HEADER_LENGTH:

      self.__writer.write('\x00' * block_remaining)
      self.__position += block_remaining
      block_remaining = BLOCK_SIZE

    if block_remaining < len(data) + HEADER_LENGTH:
      first_chunk = data[:block_remaining - HEADER_LENGTH]
      self.__write_record(RECORD_TYPE_FIRST, first_chunk)
      data = data[len(first_chunk):]

      while True:
        block_remaining = BLOCK_SIZE - self.__position % BLOCK_SIZE
        if block_remaining >= len(data) + HEADER_LENGTH:
          self.__write_record(RECORD_TYPE_LAST, data)
          break
        else:
          chunk = data[:block_remaining - HEADER_LENGTH]
          self.__write_record(RECORD_TYPE_MIDDLE, chunk)
          data = data[len(chunk):]
    else:
      self.__write_record(RECORD_TYPE_FULL, data)

  def __enter__(self):
    self.__entered = True
    return self

  def __exit__(self, atype, value, traceback):
    self.close()

  def close(self):
    if self.__pad_last_block:
      pad_length = BLOCK_SIZE - self.__position % BLOCK_SIZE
      if pad_length and pad_length != BLOCK_SIZE:
        self.__writer.write('\x00' * pad_length)


class RecordsReader(object):
  """A reader for records format."""

  def __init__(self, reader):
    self.__reader = reader

  def __try_read_record(self):
    """Try reading a record.

    Returns:
      (data, record_type) tuple.
    Raises:
      EOFError: when end of file was reached.
      InvalidRecordError: when valid record could not be read.
    """
    block_remaining = BLOCK_SIZE - self.__reader.tell() % BLOCK_SIZE
    if block_remaining < HEADER_LENGTH:
      return ('', RECORD_TYPE_NONE)

    header = self.__reader.read(HEADER_LENGTH)
    if len(header) != HEADER_LENGTH:
      raise EOFError('Read %s bytes instead of %s' %
                     (len(header), HEADER_LENGTH))

    (masked_crc, length, record_type) = struct.unpack(HEADER_FORMAT, header)
    crc = _unmask_crc(masked_crc)

    if length + HEADER_LENGTH > block_remaining:

      raise InvalidRecordError('Length is too big')

    data = self.__reader.read(length)
    if len(data) != length:
      raise EOFError('Not enough data read. Expected: %s but got %s' %
                     (length, len(data)))

    if record_type == RECORD_TYPE_NONE:
      return ('', record_type)

    actual_crc = crc32c.crc_update(crc32c.CRC_INIT, [record_type])
    actual_crc = crc32c.crc_update(actual_crc, data)
    actual_crc = crc32c.crc_finalize(actual_crc)

    if actual_crc != crc:
      raise InvalidRecordError('Data crc does not match')
    return (data, record_type)

  def __sync(self):
    """Skip reader to the block boundary."""
    pad_length = BLOCK_SIZE - self.__reader.tell() % BLOCK_SIZE
    if pad_length and pad_length != BLOCK_SIZE:
      data = self.__reader.read(pad_length)
      if len(data) != pad_length:
        raise EOFError('Read %d bytes instead of %d' %
                       (len(data), pad_length))

  def read(self):
    """Reads record from current position in reader."""
    data = None
    while True:
      last_offset = self.tell()
      try:
        (chunk, record_type) = self.__try_read_record()
        if record_type == RECORD_TYPE_NONE:
          self.__sync()
        elif record_type == RECORD_TYPE_FULL:
          if data is not None:
            logging.warning(
                "Ordering corruption: Got FULL record while already "
                "in a chunk at offset %d", last_offset)
          return chunk
        elif record_type == RECORD_TYPE_FIRST:
          if data is not None:
            logging.warning(
                "Ordering corruption: Got FIRST record while already "
                "in a chunk at offset %d", last_offset)
          data = chunk
        elif record_type == RECORD_TYPE_MIDDLE:
          if data is None:
            logging.warning(
                "Ordering corruption: Got MIDDLE record before FIRST "
                "record at offset %d", last_offset)
          else:
            data += chunk
        elif record_type == RECORD_TYPE_LAST:
          if data is None:
            logging.warning(
                "Ordering corruption: Got LAST record but no chunk is in "
                "progress at offset %d", last_offset)
          else:
            result = data + chunk
            data = None
            return result
        else:
          raise InvalidRecordError("Unsupported record type: %s" % record_type)

      except InvalidRecordError, e:
        logging.warning("Invalid record encountered at %s (%s). Syncing to "
                        "the next block", last_offset, e)
        data = None
        self.__sync()

  def __iter__(self):
    try:
      while True:
        yield self.read()
    except EOFError:
      pass

  def tell(self):
    """Return file's current position."""
    return self.__reader.tell()

  def seek(self, *args, **kwargs):
    """Set the file's current position.

    Arguments are passed directly to the underlying reader.
    """
    return self.__reader.seek(*args, **kwargs)
