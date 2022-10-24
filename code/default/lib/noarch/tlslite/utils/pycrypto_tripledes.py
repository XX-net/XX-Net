# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""PyCrypto 3DES implementation."""

from .cryptomath import *
from .tripledes import *

if pycryptoLoaded:
    import Crypto.Cipher.DES3

    def new(key, mode, IV):
        return PyCrypto_TripleDES(key, mode, IV)

    class PyCrypto_TripleDES(TripleDES):

        def __init__(self, key, mode, IV):
            TripleDES.__init__(self, key, mode, IV, "pycrypto")
            key = bytes(key)
            IV = bytes(IV)
            self.context = Crypto.Cipher.DES3.new(key, mode, IV)

        def encrypt(self, plaintext):
            plaintext = bytes(plaintext)
            return bytearray(self.context.encrypt(plaintext))

        def decrypt(self, ciphertext):
            ciphertext = bytes(ciphertext)
            return bytearray(self.context.decrypt(ciphertext))