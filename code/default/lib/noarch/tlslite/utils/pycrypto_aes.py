# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""PyCrypto AES implementation."""

from .cryptomath import *
from .aes import *

if pycryptoLoaded:
    import Crypto.Cipher.AES

    def new(key, mode, IV):
        return PyCrypto_AES(key, mode, IV)

    class PyCrypto_AES(AES):

        def __init__(self, key, mode, IV):
            AES.__init__(self, key, mode, IV, "pycrypto")
            key = bytes(key)
            IV = bytes(IV)
            self.context = Crypto.Cipher.AES.new(key, mode, IV)

        def encrypt(self, plaintext):
            plaintext = bytes(plaintext)
            return bytearray(self.context.encrypt(plaintext))

        def decrypt(self, ciphertext):
            ciphertext = bytes(ciphertext)
            return bytearray(self.context.decrypt(ciphertext))
