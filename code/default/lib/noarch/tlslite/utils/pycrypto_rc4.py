# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""PyCrypto RC4 implementation."""

from .cryptomath import *
from .rc4 import *

if pycryptoLoaded:
    import Crypto.Cipher.ARC4

    def new(key):
        return PyCrypto_RC4(key)

    class PyCrypto_RC4(RC4):

        def __init__(self, key):
            RC4.__init__(self, key, "pycrypto")
            key = bytes(key)
            self.context = Crypto.Cipher.ARC4.new(key)

        def encrypt(self, plaintext):
            plaintext = bytes(plaintext)
            return bytearray(self.context.encrypt(plaintext))

        def decrypt(self, ciphertext):
            ciphertext = bytes(ciphertext)
            return bytearray(self.context.decrypt(ciphertext))