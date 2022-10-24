# Author: Ivan Nikolchev
# See the LICENSE file for legal information regarding use of this file.

"""AESCCM with CTR and CBC from m2crypto"""

from tlslite.utils.cryptomath import m2cryptoLoaded
from tlslite.utils.aesccm import AESCCM
from tlslite.utils import openssl_aes


if m2cryptoLoaded:
    def new(key, tagLength=16):
        return OPENSSL_AESCCM(key, "openssl", bytearray(16), tagLength)


class OPENSSL_AESCCM(AESCCM):
    def __init__(self, key, implementation, rawAesEncrypt, tagLength):
        super(OPENSSL_AESCCM, self).__init__(key, implementation, rawAesEncrypt, tagLength)

        self._ctr = openssl_aes.new(key, 6, bytearray(b'\x00' * 16))
        self._cbc = openssl_aes.new(key, 2, bytearray(b'\x00' * 16))
