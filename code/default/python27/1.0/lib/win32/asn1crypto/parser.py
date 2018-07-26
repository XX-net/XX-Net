# coding: utf-8

"""
Functions for parsing and dumping using the ASN.1 DER encoding. Exports the
following items:

 - emit()
 - parse()
 - peek()

Other type classes are defined that help compose the types listed above.
"""

from __future__ import unicode_literals, division, absolute_import, print_function

import sys

from ._types import byte_cls, chr_cls, type_name
from .util import int_from_bytes, int_to_bytes

_PY2 = sys.version_info <= (3,)
_INSUFFICIENT_DATA_MESSAGE = 'Insufficient data - %s bytes requested but only %s available'


def emit(class_, method, tag, contents):
    """
    Constructs a byte string of an ASN.1 DER-encoded value

    This is typically not useful. Instead, use one of the standard classes from
    asn1crypto.core, or construct a new class with specific fields, and call the
    .dump() method.

    :param class_:
        An integer ASN.1 class value: 0 (universal), 1 (application),
        2 (context), 3 (private)

    :param method:
        An integer ASN.1 method value: 0 (primitive), 1 (constructed)

    :param tag:
        An integer ASN.1 tag value

    :param contents:
        A byte string of the encoded byte contents

    :return:
        A byte string of the ASN.1 DER value (header and contents)
    """

    if not isinstance(class_, int):
        raise TypeError('class_ must be an integer, not %s' % type_name(class_))

    if class_ < 0 or class_ > 3:
        raise ValueError('class_ must be one of 0, 1, 2 or 3, not %s' % class_)

    if not isinstance(method, int):
        raise TypeError('method must be an integer, not %s' % type_name(method))

    if method < 0 or method > 1:
        raise ValueError('method must be 0 or 1, not %s' % method)

    if not isinstance(tag, int):
        raise TypeError('tag must be an integer, not %s' % type_name(tag))

    if tag < 0:
        raise ValueError('tag must be greater than zero, not %s' % tag)

    if not isinstance(contents, byte_cls):
        raise TypeError('contents must be a byte string, not %s' % type_name(contents))

    return _dump_header(class_, method, tag, contents) + contents


def parse(contents, strict=False):
    """
    Parses a byte string of ASN.1 BER/DER-encoded data.

    This is typically not useful. Instead, use one of the standard classes from
    asn1crypto.core, or construct a new class with specific fields, and call the
    .load() class method.

    :param contents:
        A byte string of BER/DER-encoded data

    :param strict:
        A boolean indicating if trailing data should be forbidden - if so, a
        ValueError will be raised when trailing data exists

    :raises:
        ValueError - when the contents do not contain an ASN.1 header or are truncated in some way
        TypeError - when contents is not a byte string

    :return:
        A 6-element tuple:
         - 0: integer class (0 to 3)
         - 1: integer method
         - 2: integer tag
         - 3: byte string header
         - 4: byte string content
         - 5: byte string trailer
    """

    if not isinstance(contents, byte_cls):
        raise TypeError('contents must be a byte string, not %s' % type_name(contents))

    contents_len = len(contents)
    info, consumed = _parse(contents, contents_len)
    if strict and consumed != contents_len:
        raise ValueError('Extra data - %d bytes of trailing data were provided' % (contents_len - consumed))
    return info


def peek(contents):
    """
    Parses a byte string of ASN.1 BER/DER-encoded data to find the length

    This is typically used to look into an encoded value to see how long the
    next chunk of ASN.1-encoded data is. Primarily it is useful when a
    value is a concatenation of multiple values.

    :param contents:
        A byte string of BER/DER-encoded data

    :raises:
        ValueError - when the contents do not contain an ASN.1 header or are truncated in some way
        TypeError - when contents is not a byte string

    :return:
        An integer with the number of bytes occupied by the ASN.1 value
    """

    if not isinstance(contents, byte_cls):
        raise TypeError('contents must be a byte string, not %s' % type_name(contents))

    info, consumed = _parse(contents, len(contents))
    return consumed


def _parse(encoded_data, data_len, pointer=0, lengths_only=False):
    """
    Parses a byte string into component parts

    :param encoded_data:
        A byte string that contains BER-encoded data

    :param data_len:
        The integer length of the encoded data

    :param pointer:
        The index in the byte string to parse from

    :param lengths_only:
        A boolean to cause the call to return a 2-element tuple of the integer
        number of bytes in the header and the integer number of bytes in the
        contents. Internal use only.

    :return:
        A 2-element tuple:
         - 0: A tuple of (class_, method, tag, header, content, trailer)
         - 1: An integer indicating how many bytes were consumed
    """

    if data_len < pointer + 2:
        raise ValueError(_INSUFFICIENT_DATA_MESSAGE % (2, data_len - pointer))

    start = pointer
    first_octet = ord(encoded_data[pointer]) if _PY2 else encoded_data[pointer]
    pointer += 1

    tag = first_octet & 31
    # Base 128 length using 8th bit as continuation indicator
    if tag == 31:
        tag = 0
        while True:
            num = ord(encoded_data[pointer]) if _PY2 else encoded_data[pointer]
            pointer += 1
            tag *= 128
            tag += num & 127
            if num >> 7 == 0:
                break

    length_octet = ord(encoded_data[pointer]) if _PY2 else encoded_data[pointer]
    pointer += 1

    if length_octet >> 7 == 0:
        if lengths_only:
            return (pointer, pointer + (length_octet & 127))
        contents_end = pointer + (length_octet & 127)

    else:
        length_octets = length_octet & 127
        if length_octets:
            pointer += length_octets
            contents_end = pointer + int_from_bytes(encoded_data[pointer - length_octets:pointer], signed=False)
            if lengths_only:
                return (pointer, contents_end)

        else:
            # To properly parse indefinite length values, we need to scan forward
            # parsing headers until we find a value with a length of zero. If we
            # just scanned looking for \x00\x00, nested indefinite length values
            # would not work.
            contents_end = pointer
            # Unfortunately we need to understand the contents of the data to
            # properly scan forward, which bleeds some representation info into
            # the parser. This condition handles the unused bits byte in
            # constructed bit strings.
            if tag == 3:
                contents_end += 1
            while contents_end < data_len:
                sub_header_end, contents_end = _parse(encoded_data, data_len, contents_end, lengths_only=True)
                if contents_end == sub_header_end and encoded_data[contents_end - 2:contents_end] == b'\x00\x00':
                    break
            if lengths_only:
                return (pointer, contents_end)
            if contents_end > data_len:
                raise ValueError(_INSUFFICIENT_DATA_MESSAGE % (contents_end, data_len))
            return (
                (
                    first_octet >> 6,
                    (first_octet >> 5) & 1,
                    tag,
                    encoded_data[start:pointer],
                    encoded_data[pointer:contents_end - 2],
                    b'\x00\x00'
                ),
                contents_end
            )

    if contents_end > data_len:
        raise ValueError(_INSUFFICIENT_DATA_MESSAGE % (contents_end, data_len))
    return (
        (
            first_octet >> 6,
            (first_octet >> 5) & 1,
            tag,
            encoded_data[start:pointer],
            encoded_data[pointer:contents_end],
            b''
        ),
        contents_end
    )


def _dump_header(class_, method, tag, contents):
    """
    Constructs the header bytes for an ASN.1 object

    :param class_:
        An integer ASN.1 class value: 0 (universal), 1 (application),
        2 (context), 3 (private)

    :param method:
        An integer ASN.1 method value: 0 (primitive), 1 (constructed)

    :param tag:
        An integer ASN.1 tag value

    :param contents:
        A byte string of the encoded byte contents

    :return:
        A byte string of the ASN.1 DER header
    """

    header = b''

    id_num = 0
    id_num |= class_ << 6
    id_num |= method << 5

    if tag >= 31:
        header += chr_cls(id_num | 31)
        while tag > 0:
            continuation_bit = 0x80 if tag > 0x7F else 0
            header += chr_cls(continuation_bit | (tag & 0x7F))
            tag = tag >> 7
    else:
        header += chr_cls(id_num | tag)

    length = len(contents)
    if length <= 127:
        header += chr_cls(length)
    else:
        length_bytes = int_to_bytes(length)
        header += chr_cls(0x80 | len(length_bytes))
        header += length_bytes

    return header
