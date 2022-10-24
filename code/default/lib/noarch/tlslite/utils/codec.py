# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""Classes for reading/writing binary data (such as TLS records)."""

from __future__ import division

import sys
import struct
from struct import pack
from .compat import bytes_to_int


class DecodeError(SyntaxError):
    """Exception raised in case of decoding errors."""
    pass


class BadCertificateError(SyntaxError):
    """Exception raised in case of bad certificate."""
    pass


class Writer(object):
    """Serialisation helper for complex byte-based structures."""

    def __init__(self):
        """Initialise the serializer with no data."""
        self.bytes = bytearray(0)

    def addOne(self, val):
        """Add a single-byte wide element to buffer, see add()."""
        self.bytes.append(val)

    if sys.version_info < (2, 7):
        # struct.pack on Python2.6 does not raise exception if the value
        # is larger than can fit inside the specified size
        def addTwo(self, val):
            """Add a double-byte wide element to buffer, see add()."""
            if not 0 <= val <= 0xffff:
                raise ValueError("Can't represent value in specified length")
            self.bytes += pack('>H', val)

        def addThree(self, val):
            """Add a three-byte wide element to buffer, see add()."""
            if not 0 <= val <= 0xffffff:
                raise ValueError("Can't represent value in specified length")
            self.bytes += pack('>BH', val >> 16, val & 0xffff)

        def addFour(self, val):
            """Add a four-byte wide element to buffer, see add()."""
            if not 0 <= val <= 0xffffffff:
                raise ValueError("Can't represent value in specified length")
            self.bytes += pack('>I', val)
    else:
        def addTwo(self, val):
            """Add a double-byte wide element to buffer, see add()."""
            try:
                self.bytes += pack('>H', val)
            except struct.error:
                raise ValueError("Can't represent value in specified length")

        def addThree(self, val):
            """Add a three-byte wide element to buffer, see add()."""
            try:
                self.bytes += pack('>BH', val >> 16, val & 0xffff)
            except struct.error:
                raise ValueError("Can't represent value in specified length")

        def addFour(self, val):
            """Add a four-byte wide element to buffer, see add()."""
            try:
                self.bytes += pack('>I', val)
            except struct.error:
                raise ValueError("Can't represent value in specified length")

    if sys.version_info >= (3, 0):
        # the method is called thousands of times, so it's better to extern
        # the version info check
        def add(self, x, length):
            """
            Add a single positive integer value x, encode it in length bytes

            Encode positive integer x in big-endian format using length bytes,
            add to the internal buffer.

            :type x: int
            :param x: value to encode

            :type length: int
            :param length: number of bytes to use for encoding the value
            """
            try:
                self.bytes += x.to_bytes(length, 'big')
            except OverflowError:
                raise ValueError("Can't represent value in specified length")
    else:
        _addMethods = {1: addOne, 2: addTwo, 3: addThree, 4: addFour}

        def add(self, x, length):
            """
            Add a single positive integer value x, encode it in length bytes

            Encode positive iteger x in big-endian format using length bytes,
            add to the internal buffer.

            :type x: int
            :param x: value to encode

            :type length: int
            :param length: number of bytes to use for encoding the value
            """
            try:
                self._addMethods[length](self, x)
            except KeyError:
                self.bytes += bytearray(length)
                newIndex = len(self.bytes) - 1
                for i in range(newIndex, newIndex - length, -1):
                    self.bytes[i] = x & 0xFF
                    x >>= 8
                if x != 0:
                    raise ValueError("Can't represent value in specified "
                                     "length")

    def addFixSeq(self, seq, length):
        """
        Add a list of items, encode every item in length bytes

        Uses the unbounded iterable seq to produce items, each of
        which is then encoded to length bytes

        :type seq: iterable of int
        :param seq: list of positive integers to encode

        :type length: int
        :param length: number of bytes to which encode every element
        """
        for e in seq:
            self.add(e, length)

    if sys.version_info < (2, 7):
        # struct.pack on Python2.6 does not raise exception if the value
        # is larger than can fit inside the specified size
        def _addVarSeqTwo(self, seq):
            """Helper method for addVarSeq"""
            if not all(0 <= i <= 0xffff for i in seq):
                raise ValueError("Can't represent value in specified "
                                 "length")
            self.bytes += pack('>' + 'H' * len(seq), *seq)

        def addVarSeq(self, seq, length, lengthLength):
            """
            Add a bounded list of same-sized values

            Create a list of specific length with all items being of the same
            size

            :type seq: list of int
            :param seq: list of positive integers to encode

            :type length: int
            :param length: amount of bytes in which to encode every item

            :type lengthLength: int
            :param lengthLength: amount of bytes in which to encode the overall
                length of the array
            """
            self.add(len(seq)*length, lengthLength)
            if length == 1:
                self.bytes.extend(seq)
            elif length == 2:
                self._addVarSeqTwo(seq)
            else:
                for i in seq:
                    self.add(i, length)
    else:
        def addVarSeq(self, seq, length, lengthLength):
            """
            Add a bounded list of same-sized values

            Create a list of specific length with all items being of the same
            size

            :type seq: list of int
            :param seq: list of positive integers to encode

            :type length: int
            :param length: amount of bytes in which to encode every item

            :type lengthLength: int
            :param lengthLength: amount of bytes in which to encode the overall
                length of the array
            """
            seqLen = len(seq)
            self.add(seqLen*length, lengthLength)
            if length == 1:
                self.bytes.extend(seq)
            elif length == 2:
                try:
                    self.bytes += pack('>' + 'H' * seqLen, *seq)
                except struct.error:
                    raise ValueError("Can't represent value in specified "
                                     "length")
            else:
                for i in seq:
                    self.add(i, length)

    def addVarTupleSeq(self, seq, length, lengthLength):
        """
        Add a variable length list of same-sized element tuples.

        Note that all tuples must have the same size.

        Inverse of Parser.getVarTupleList()

        :type seq: enumerable
        :param seq: list of tuples

        :type length: int
        :param length: length of single element in tuple

        :type lengthLength: int
        :param lengthLength: length in bytes of overall length field
        """
        if not seq:
            self.add(0, lengthLength)
        else:
            startPos = len(self.bytes)
            dataLength = len(seq) * len(seq[0]) * length
            self.add(dataLength, lengthLength)
            # since at the time of writing, all the calls encode single byte
            # elements, and it's very easy to speed up that case, give it
            # special case
            if length == 1:
                for elemTuple in seq:
                    self.bytes.extend(elemTuple)
            else:
                for elemTuple in seq:
                    self.addFixSeq(elemTuple, length)
            if startPos + dataLength + lengthLength != len(self.bytes):
                raise ValueError("Tuples of different lengths")

    def add_var_bytes(self, data, length_length):
        """
        Add a variable length array of bytes.

        Inverse of Parser.getVarBytes()

        :type data: bytes
        :param data: bytes to add to the buffer

        :param int length_length: size of the field to represent the length
            of the data string
        """
        length = len(data)
        self.add(length, length_length)
        self.bytes += data


class Parser(object):
    """
    Parser for TLV and LV byte-based encodings.

    Parser that can handle arbitrary byte-based encodings usually employed in
    Type-Length-Value or Length-Value binary encoding protocols like ASN.1
    or TLS

    Note: if the raw bytes don't match expected values (like trying to
    read a 4-byte integer from a 2-byte buffer), most methods will raise a
    DecodeError exception.

    TODO: don't use an exception used by language parser to indicate errors
    in application code.

    :vartype bytes: bytearray
    :ivar bytes: data to be interpreted (buffer)

    :vartype index: int
    :ivar index: current position in the buffer

    :vartype lengthCheck: int
    :ivar lengthCheck: size of struct being parsed

    :vartype indexCheck: int
    :ivar indexCheck: position at which the structure begins in buffer
    """

    def __init__(self, bytes):
        """
        Bind raw bytes with parser.

        :type bytes: bytearray
        :param bytes: bytes to be parsed/interpreted
        """
        self.bytes = bytes
        self.index = 0
        self.indexCheck = 0
        self.lengthCheck = 0

    def get(self, length):
        """
        Read a single big-endian integer value encoded in 'length' bytes.

        :type length: int
        :param length: number of bytes in which the value is encoded in

        :rtype: int
        """
        ret = self.getFixBytes(length)
        return bytes_to_int(ret, 'big')

    def getFixBytes(self, lengthBytes):
        """
        Read a string of bytes encoded in 'lengthBytes' bytes.

        :type lengthBytes: int
        :param lengthBytes: number of bytes to return

        :rtype: bytearray
        """
        end = self.index + lengthBytes
        if end > len(self.bytes):
            raise DecodeError("Read past end of buffer")
        ret = self.bytes[self.index : end]
        self.index += lengthBytes
        return ret

    def skip_bytes(self, length):
        """Move the internal pointer ahead length bytes."""
        if self.index + length > len(self.bytes):
            raise DecodeError("Read past end of buffer")
        self.index += length

    def getVarBytes(self, lengthLength):
        """
        Read a variable length string with a fixed length.

        see Writer.add_var_bytes() for an inverse of this method

        :type lengthLength: int
        :param lengthLength: number of bytes in which the length of the string
            is encoded in

        :rtype: bytearray
        """
        lengthBytes = self.get(lengthLength)
        return self.getFixBytes(lengthBytes)

    def getFixList(self, length, lengthList):
        """
        Read a list of static length with same-sized ints.

        :type length: int
        :param length: size in bytes of a single element in list

        :type lengthList: int
        :param lengthList: number of elements in list

        :rtype: list of int
        """
        l = [0] * lengthList
        for x in range(lengthList):
            l[x] = self.get(length)
        return l

    def getVarList(self, length, lengthLength):
        """
        Read a variable length list of same-sized integers.

        :type length: int
        :param length: size in bytes of a single element

        :type lengthLength: int
        :param lengthLength: size of the encoded length of the list

        :rtype: list of int
        """
        lengthList = self.get(lengthLength)
        if lengthList % length != 0:
            raise DecodeError("Encoded length not a multiple of element "
                              "length")
        lengthList = lengthList // length
        l = [0] * lengthList
        for x in range(lengthList):
            l[x] = self.get(length)
        return l

    def getVarTupleList(self, elemLength, elemNum, lengthLength):
        """
        Read a variable length list of same sized tuples.

        :type elemLength: int
        :param elemLength: length in bytes of single tuple element

        :type elemNum: int
        :param elemNum: number of elements in tuple

        :type lengthLength: int
        :param lengthLength: length in bytes of the list length variable

        :rtype: list of tuple of int
        """
        lengthList = self.get(lengthLength)
        if lengthList % (elemLength * elemNum) != 0:
            raise DecodeError("Encoded length not a multiple of element "
                              "length")
        tupleCount = lengthList // (elemLength * elemNum)
        tupleList = []
        for _ in range(tupleCount):
            currentTuple = []
            for _ in range(elemNum):
                currentTuple.append(self.get(elemLength))
            tupleList.append(tuple(currentTuple))
        return tupleList

    def startLengthCheck(self, lengthLength):
        """
        Read length of struct and start a length check for parsing.

        :type lengthLength: int
        :param lengthLength: number of bytes in which the length is encoded
        """
        self.lengthCheck = self.get(lengthLength)
        self.indexCheck = self.index

    def setLengthCheck(self, length):
        """
        Set length of struct and start a length check for parsing.

        :type length: int
        :param length: expected size of parsed struct in bytes
        """
        self.lengthCheck = length
        self.indexCheck = self.index

    def stopLengthCheck(self):
        """
        Stop struct parsing, verify that no under- or overflow occurred.

        In case the expected length was mismatched with actual length of
        processed data, raises an exception.
        """
        if (self.index - self.indexCheck) != self.lengthCheck:
            raise DecodeError("Under- or over-flow while reading buffer")

    def atLengthCheck(self):
        """
        Check if there is data in structure left for parsing.

        Returns True if the whole structure was parsed, False if there is
        some data left.

        Will raise an exception if overflow occured (amount of data read was
        greater than expected size)
        """
        if (self.index - self.indexCheck) < self.lengthCheck:
            return False
        elif (self.index - self.indexCheck) == self.lengthCheck:
            return True
        else:
            raise DecodeError("Read past end of buffer")

    def getRemainingLength(self):
        """Return amount of data remaining in struct being parsed."""
        return len(self.bytes) - self.index
