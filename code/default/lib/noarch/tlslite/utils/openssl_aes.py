# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""OpenSSL/M2Crypto AES implementation."""

from .cryptomath import *
from .aes import *
from .python_aes import Python_AES_CTR

if m2cryptoLoaded:

    def new(key, mode, IV):
        # IV argument name is a part of the interface
        # pylint: disable=invalid-name
        """
        Try using AES CTR from m2crpyto,
        if it is not available fall back to the
        python implementation.
        """
        if mode == 2:
            return OpenSSL_AES(key, mode, IV)
        elif mode == 6:
            if M2CRYPTO_AES_CTR:
                return OpenSSL_CTR(key, mode, IV)
            return Python_AES_CTR(key, mode, IV)
        else:
            raise NotImplementedError()


    class OpenSSL_AES(AES):

        def __init__(self, key, mode, IV):
            # IV argument/field names are a part of the interface
            # pylint: disable=invalid-name
            AES.__init__(self, key, mode, IV, "openssl")
            self._IV, self._key = IV, key
            self._context = None
            self._encrypt = None

        @property
        def IV(self):
            return self._IV

        @IV.setter
        def IV(self, iv):
            if self._context is not None:
                m2.cipher_ctx_free(self._context)
            self._IV = iv
            self._init_context()

        def _init_context(self, encrypt=True):
            if len(self._key) == 16:
                cipherType = m2.aes_128_cbc()
            if len(self._key) == 24:
                cipherType = m2.aes_192_cbc()
            if len(self._key) == 32:
                cipherType = m2.aes_256_cbc()
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
            AES.encrypt(self, plaintext)
            ciphertext = m2.cipher_update(self._context, plaintext)
            return bytearray(ciphertext)

        def decrypt(self, ciphertext):
            if self._context is None:
                self._init_context(encrypt=False)
            else:
                assert not self._encrypt, \
                       '.decrypt() not allowed after .encrypt()'
            AES.decrypt(self, ciphertext)
            plaintext = m2.cipher_update(self._context, ciphertext)
            return bytearray(plaintext)

        def __del__(self):
            if self._context is not None:
                m2.cipher_ctx_free(self._context)


    class OpenSSL_CTR(AES):

        def __init__(self, key, mode, IV):
            # IV argument/field names are a part of the interface
            # pylint: disable=invalid-name
            AES.__init__(self, key, mode, IV, "openssl")
            self._IV = IV
            self.key = key
            self._context = None
            self._encrypt = None
            if len(key) not in (16, 24, 32):
                raise AssertionError()

        @property
        def counter(self):
            return self._IV

        @counter.setter
        def counter(self, ctr):
            if self._context is not None:
                m2.cipher_ctx_free(self._context)
            self._IV = ctr
            self._init_context()

        def _init_context(self, encrypt=True):
            if len(self.key) == 16:
                cipherType = m2.aes_128_ctr()
            if len(self.key) == 24:
                cipherType = m2.aes_192_ctr()
            if len(self.key) == 32:
                cipherType = m2.aes_256_ctr()
            self._context = m2.cipher_ctx_new()
            m2.cipher_init(self._context, cipherType, self.key, self._IV,
                           int(encrypt))
            m2.cipher_set_padding(self._context, 0)
            self._encrypt = encrypt

        def encrypt(self, plaintext):
            ciphertext = m2.cipher_update(self._context, plaintext)
            return bytearray(ciphertext)

        def decrypt(self, ciphertext):
            plaintext = m2.cipher_update(self._context, ciphertext)
            return bytearray(plaintext)

        def __del__(self):
            if self._context is not None:
                m2.cipher_ctx_free(self._context)
