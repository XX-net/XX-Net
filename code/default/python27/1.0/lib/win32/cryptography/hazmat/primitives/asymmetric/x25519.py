# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import absolute_import, division, print_function

import abc

import six

from cryptography.exceptions import UnsupportedAlgorithm, _Reasons


@six.add_metaclass(abc.ABCMeta)
class X25519PublicKey(object):
    @classmethod
    def from_public_bytes(cls, data):
        from cryptography.hazmat.backends.openssl.backend import backend
        if not backend.x25519_supported():
            raise UnsupportedAlgorithm(
                "X25519 is not supported by this version of OpenSSL.",
                _Reasons.UNSUPPORTED_EXCHANGE_ALGORITHM
            )
        return backend.x25519_load_public_bytes(data)

    @abc.abstractmethod
    def public_bytes(self):
        pass


@six.add_metaclass(abc.ABCMeta)
class X25519PrivateKey(object):
    @classmethod
    def generate(cls):
        from cryptography.hazmat.backends.openssl.backend import backend
        if not backend.x25519_supported():
            raise UnsupportedAlgorithm(
                "X25519 is not supported by this version of OpenSSL.",
                _Reasons.UNSUPPORTED_EXCHANGE_ALGORITHM
            )
        return backend.x25519_generate_key()

    @classmethod
    def _from_private_bytes(cls, data):
        from cryptography.hazmat.backends.openssl.backend import backend
        return backend.x25519_load_private_bytes(data)

    @abc.abstractmethod
    def public_key(self):
        pass

    @abc.abstractmethod
    def exchange(self, peer_public_key):
        pass
