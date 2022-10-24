# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""OpenSSL/M2Crypto 3DES implementation."""

from .cryptomath import *
from .tripledes import *

if m2cryptoLoaded:

    def new(key, mode, IV):
        return OpenSSL_TripleDES(key, mode, IV)

    class OpenSSL_TripleDES(TripleDES):

        def __init__(self, key, mode, IV):
            TripleDES.__init__(self, key, mode, IV, "openssl")
            self._IV, self._key = IV, key
            self._context = None
            self._encrypt = None

        def _init_context(self, encrypt=True):
            cipherType = m2.des_ede3_cbc()
            self._context = m2.cipher_ctx_new()
            m2.cipher_init(self._context, cipherType, self._key, self._IV,
                           int(encrypt))
            m2.cipher_set_padding(self._context, 0)
            self._encrypt = encrypt

        def encrypt(self, plaintext):
            if self._context is None:
                self._init_context(encrypt=True)
            else:
                assert self._encrypt, '.encrypt() not allowed after .decrypt()'
            TripleDES.encrypt(self, plaintext)
            ciphertext = m2.cipher_update(self._context, plaintext)
            return bytearray(ciphertext)

        def decrypt(self, ciphertext):
            if self._context is None:
                self._init_context(encrypt=False)
            else:
                assert not self._encrypt, \
                       '.decrypt() not allowed after .encrypt()'
            TripleDES.decrypt(self, ciphertext)
            plaintext = m2.cipher_update(self._context, ciphertext)
            return bytearray(plaintext)

        def __del__(self):
            if self._context is not None:
                m2.cipher_ctx_free(self._context)
