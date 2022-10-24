# Author: Trevor Perrin
# Patch from Google adding getChildBytes()
#
# See the LICENSE file for legal information regarding use of this file.

"""Abstract Syntax Notation One (ASN.1) parsing"""

from .codec import Parser


class ASN1Type(object):
    """
    Class that represents the ASN.1 type bit octet.
    Consists of a class (universal(0), application(1), context-specific(2)
    or private(3)), boolean value that indicates if a type is constructed or
    primitive and the ASN1 type itself.

    :vartype bytes: bytearray
    :ivar field: bit octet

    :vartype tagClass: int
    :ivar tagClass: type's class

    :vartype isPrimitive: int
    :ivar isPrimitive: equals to 0 if the type is primitive, 1 if not

    :vartype tagId: int
    :ivar tagId: ANS1 tag number
    """

    def __init__(self, tag_class, is_primitive, tag_id):
        self.tag_class = tag_class
        self.is_primitive = is_primitive
        self.tag_id = tag_id


class ASN1Parser(object):
    """
    Parser and storage of ASN.1 DER encoded objects.

    :vartype length: int
    :ivar length: length of the value of the tag
    :vartype value: bytearray
    :ivar value: literal value of the tag
    """

    def __init__(self, bytes):
        """Create an object from bytes.

        :type bytes: bytearray
        :param bytes: DER encoded ASN.1 object
        """
        p = Parser(bytes)

        # Get Type
        self.type = self._parse_type(p)

        #Get Length
        self.length = self._getASN1Length(p)

        #Get Value
        self.value = p.getFixBytes(self.length)

    def getChild(self, which):
        """
        Return n-th child assuming that the object is a SEQUENCE.

        :type which: int
        :param which: ordinal of the child to return

        :rtype: ASN1Parser
        :returns: decoded child object
        """
        return ASN1Parser(self.getChildBytes(which))

    def getChildCount(self):
        """
        Return number of children, assuming that the object is a SEQUENCE.

        :rtype: int
        :returns: number of children in the object
        """
        p = Parser(self.value)
        count = 0
        while True:
            if p.getRemainingLength() == 0:
                break
            p.skip_bytes(1)  # skip Type
            length = self._getASN1Length(p)
            p.skip_bytes(length)  # skip value
            count += 1
        return count

    def getChildBytes(self, which):
        """
        Return raw encoding of n-th child, assume self is a SEQUENCE

        :type which: int
        :param which: ordinal of the child to return

        :rtype: bytearray
        :returns: raw child object
        """
        p = Parser(self.value)
        for _ in range(which+1):
            markIndex = p.index
            p.skip_bytes(1)  # skip Type
            length = self._getASN1Length(p)
            p.skip_bytes(length)
        return p.bytes[markIndex : p.index]

    @staticmethod
    def _getASN1Length(p):
        """Decode the ASN.1 DER length field"""
        firstLength = p.get(1)
        if firstLength <= 127:
            return firstLength
        else:
            lengthLength = firstLength & 0x7F
            return p.get(lengthLength)

    @staticmethod
    def _parse_type(parser):
        """Decode the ASN.1 DER type field"""
        header = parser.get(1)
        tag_class = (header & 0xc0) >> 6
        tag_is_primitive = (header & 0x20) >> 5
        tag_id = header & 0x1f

        if tag_id == 0x1f:
            tag_id = 0
            while True:
                value = parser.get(1)
                tag_id += value & 0x7f
                if not value & 0x80:
                    break
                tag_id <<= 7

        asn1type = ASN1Type(tag_class, tag_is_primitive, tag_id)
        return asn1type
