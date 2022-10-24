# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""Abstract class for RC4."""


class RC4(object):
    def __init__(self, keyBytes, implementation):
        if len(keyBytes) < 16 or len(keyBytes) > 256:
            raise ValueError()
        self.isBlockCipher = False
        self.isAEAD = False
        self.name = "rc4"
        self.implementation = implementation

    def encrypt(self, plaintext):
        raise NotImplementedError()

    def decrypt(self, ciphertext):
        raise NotImplementedError()
