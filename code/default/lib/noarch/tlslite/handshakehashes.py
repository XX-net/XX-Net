# Copyright (c) 2015, Hubert Kario
#
# See the LICENSE file for legal information regarding use of this file.
"""Handling cryptographic hashes for handshake protocol"""

from .utils.compat import compat26Str, compatHMAC
from .utils.cryptomath import MD5, SHA1
from .utils import tlshashlib as hashlib

class HandshakeHashes(object):

    """
    Store and calculate necessary hashes for handshake protocol

    Calculates message digests of messages exchanged in handshake protocol
    of SSLv3 and TLS.
    """

    def __init__(self):
        """Create instance"""
        self._handshakeMD5 = hashlib.md5()
        self._handshakeSHA = hashlib.sha1()
        self._handshakeSHA224 = hashlib.sha224()
        self._handshakeSHA256 = hashlib.sha256()
        self._handshakeSHA384 = hashlib.sha384()
        self._handshakeSHA512 = hashlib.sha512()
        self._handshake_buffer = bytearray()

    def update(self, data):
        """
        Add `data` to hash input.

        :param bytearray data: serialized TLS handshake message
        """
        text = compat26Str(data)
        self._handshakeMD5.update(text)
        self._handshakeSHA.update(text)
        self._handshakeSHA224.update(text)
        self._handshakeSHA256.update(text)
        self._handshakeSHA384.update(text)
        self._handshakeSHA512.update(text)
        self._handshake_buffer += text

    def digest(self, digest=None):
        """
        Calculate and return digest for the already consumed data.

        Used for Finished and CertificateVerify messages.

        :param str digest: name of digest to return
        """
        if digest is None:
            return self._handshakeMD5.digest() + self._handshakeSHA.digest()
        elif digest == 'md5':
            return self._handshakeMD5.digest()
        elif digest == 'sha1':
            return self._handshakeSHA.digest()
        elif digest == 'sha224':
            return self._handshakeSHA224.digest()
        elif digest == 'sha256':
            return self._handshakeSHA256.digest()
        elif digest == 'sha384':
            return self._handshakeSHA384.digest()
        elif digest == 'sha512':
            return self._handshakeSHA512.digest()
        elif digest == "intrinsic":
            return self._handshake_buffer
        else:
            raise ValueError("Unknown digest name")

    def digestSSL(self, masterSecret, label):
        """
        Calculate and return digest for already consumed data (SSLv3 version)

        Used for Finished and CertificateVerify messages.

        :param bytearray masterSecret: value of the master secret
        :param bytearray label: label to include in the calculation
        """
        #pylint: disable=maybe-no-member
        imacMD5 = self._handshakeMD5.copy()
        imacSHA = self._handshakeSHA.copy()
        #pylint: enable=maybe-no-member

        # the below difference in input for MD5 and SHA-1 is why we can't reuse
        # digest() method
        imacMD5.update(compatHMAC(label + masterSecret + bytearray([0x36]*48)))
        imacSHA.update(compatHMAC(label + masterSecret + bytearray([0x36]*40)))

        md5Bytes = MD5(masterSecret + bytearray([0x5c]*48) + \
                         bytearray(imacMD5.digest()))
        shaBytes = SHA1(masterSecret + bytearray([0x5c]*40) + \
                         bytearray(imacSHA.digest()))

        return md5Bytes + shaBytes

    #pylint: disable=protected-access, maybe-no-member
    def copy(self):
        """
        Copy object

        Return a copy of the object with all the hashes in the same state
        as the source object.

        :rtype: HandshakeHashes
        """
        other = HandshakeHashes()
        other._handshakeMD5 = self._handshakeMD5.copy()
        other._handshakeSHA = self._handshakeSHA.copy()
        other._handshakeSHA224 = self._handshakeSHA224.copy()
        other._handshakeSHA256 = self._handshakeSHA256.copy()
        other._handshakeSHA384 = self._handshakeSHA384.copy()
        other._handshakeSHA512 = self._handshakeSHA512.copy()
        other._handshake_buffer = bytearray(self._handshake_buffer)
        return other
