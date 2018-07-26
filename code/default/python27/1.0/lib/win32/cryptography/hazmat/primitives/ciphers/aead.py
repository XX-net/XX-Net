# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import absolute_import, division, print_function

import os

from cryptography import exceptions, utils
from cryptography.hazmat.backends.openssl import aead
from cryptography.hazmat.backends.openssl.backend import backend


class ChaCha20Poly1305(object):
    _MAX_SIZE = 2 ** 32

    def __init__(self, key):
        if not backend.aead_cipher_supported(self):
            raise exceptions.UnsupportedAlgorithm(
                "ChaCha20Poly1305 is not supported by this version of OpenSSL",
                exceptions._Reasons.UNSUPPORTED_CIPHER
            )
        utils._check_bytes("key", key)

        if len(key) != 32:
            raise ValueError("ChaCha20Poly1305 key must be 32 bytes.")

        self._key = key

    @classmethod
    def generate_key(cls):
        return os.urandom(32)

    def encrypt(self, nonce, data, associated_data):
        if associated_data is None:
            associated_data = b""

        if len(data) > self._MAX_SIZE or len(associated_data) > self._MAX_SIZE:
            # This is OverflowError to match what cffi would raise
            raise OverflowError(
                "Data or associated data too long. Max 2**32 bytes"
            )

        self._check_params(nonce, data, associated_data)
        return aead._encrypt(
            backend, self, nonce, data, associated_data, 16
        )

    def decrypt(self, nonce, data, associated_data):
        if associated_data is None:
            associated_data = b""

        self._check_params(nonce, data, associated_data)
        return aead._decrypt(
            backend, self, nonce, data, associated_data, 16
        )

    def _check_params(self, nonce, data, associated_data):
        utils._check_bytes("nonce", nonce)
        utils._check_bytes("data", data)
        utils._check_bytes("associated_data", associated_data)
        if len(nonce) != 12:
            raise ValueError("Nonce must be 12 bytes")


class AESCCM(object):
    _MAX_SIZE = 2 ** 32

    def __init__(self, key, tag_length=16):
        utils._check_bytes("key", key)
        if len(key) not in (16, 24, 32):
            raise ValueError("AESCCM key must be 128, 192, or 256 bits.")

        self._key = key
        if not isinstance(tag_length, int):
            raise TypeError("tag_length must be an integer")

        if tag_length not in (4, 6, 8, 12, 14, 16):
            raise ValueError("Invalid tag_length")

        self._tag_length = tag_length

        if not backend.aead_cipher_supported(self):
            raise exceptions.UnsupportedAlgorithm(
                "AESCCM is not supported by this version of OpenSSL",
                exceptions._Reasons.UNSUPPORTED_CIPHER
            )

    @classmethod
    def generate_key(cls, bit_length):
        if not isinstance(bit_length, int):
            raise TypeError("bit_length must be an integer")

        if bit_length not in (128, 192, 256):
            raise ValueError("bit_length must be 128, 192, or 256")

        return os.urandom(bit_length // 8)

    def encrypt(self, nonce, data, associated_data):
        if associated_data is None:
            associated_data = b""

        if len(data) > self._MAX_SIZE or len(associated_data) > self._MAX_SIZE:
            # This is OverflowError to match what cffi would raise
            raise OverflowError(
                "Data or associated data too long. Max 2**32 bytes"
            )

        self._check_params(nonce, data, associated_data)
        self._validate_lengths(nonce, len(data))
        return aead._encrypt(
            backend, self, nonce, data, associated_data, self._tag_length
        )

    def decrypt(self, nonce, data, associated_data):
        if associated_data is None:
            associated_data = b""

        self._check_params(nonce, data, associated_data)
        return aead._decrypt(
            backend, self, nonce, data, associated_data, self._tag_length
        )

    def _validate_lengths(self, nonce, data_len):
        # For information about computing this, see
        # https://tools.ietf.org/html/rfc3610#section-2.1
        l_val = 15 - len(nonce)
        if 2 ** (8 * l_val) < data_len:
            raise ValueError("Nonce too long for data")

    def _check_params(self, nonce, data, associated_data):
        utils._check_bytes("nonce", nonce)
        utils._check_bytes("data", data)
        utils._check_bytes("associated_data", associated_data)
        if not 7 <= len(nonce) <= 13:
            raise ValueError("Nonce must be between 7 and 13 bytes")


class AESGCM(object):
    _MAX_SIZE = 2 ** 32

    def __init__(self, key):
        utils._check_bytes("key", key)
        if len(key) not in (16, 24, 32):
            raise ValueError("AESGCM key must be 128, 192, or 256 bits.")

        self._key = key

    @classmethod
    def generate_key(cls, bit_length):
        if not isinstance(bit_length, int):
            raise TypeError("bit_length must be an integer")

        if bit_length not in (128, 192, 256):
            raise ValueError("bit_length must be 128, 192, or 256")

        return os.urandom(bit_length // 8)

    def encrypt(self, nonce, data, associated_data):
        if associated_data is None:
            associated_data = b""

        if len(data) > self._MAX_SIZE or len(associated_data) > self._MAX_SIZE:
            # This is OverflowError to match what cffi would raise
            raise OverflowError(
                "Data or associated data too long. Max 2**32 bytes"
            )

        self._check_params(nonce, data, associated_data)
        return aead._encrypt(
            backend, self, nonce, data, associated_data, 16
        )

    def decrypt(self, nonce, data, associated_data):
        if associated_data is None:
            associated_data = b""

        self._check_params(nonce, data, associated_data)
        return aead._decrypt(
            backend, self, nonce, data, associated_data, 16
        )

    def _check_params(self, nonce, data, associated_data):
        utils._check_bytes("nonce", nonce)
        utils._check_bytes("data", data)
        utils._check_bytes("associated_data", associated_data)
        if len(nonce) == 0:
            raise ValueError("Nonce must be at least 1 byte")
