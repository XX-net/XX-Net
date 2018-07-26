# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import absolute_import, division, print_function

import warnings

from asn1crypto.algos import DSASignature

import six

from cryptography import utils
from cryptography.hazmat.primitives import hashes


def decode_rfc6979_signature(signature):
    warnings.warn(
        "decode_rfc6979_signature is deprecated and will "
        "be removed in a future version, use decode_dss_signature instead.",
        utils.PersistentlyDeprecated,
        stacklevel=2
    )
    return decode_dss_signature(signature)


def decode_dss_signature(signature):
    data = DSASignature.load(signature, strict=True).native
    return data['r'], data['s']


def encode_rfc6979_signature(r, s):
    warnings.warn(
        "encode_rfc6979_signature is deprecated and will "
        "be removed in a future version, use encode_dss_signature instead.",
        utils.PersistentlyDeprecated,
        stacklevel=2
    )
    return encode_dss_signature(r, s)


def encode_dss_signature(r, s):
    if (
        not isinstance(r, six.integer_types) or
        not isinstance(s, six.integer_types)
    ):
        raise ValueError("Both r and s must be integers")

    return DSASignature({'r': r, 's': s}).dump()


class Prehashed(object):
    def __init__(self, algorithm):
        if not isinstance(algorithm, hashes.HashAlgorithm):
            raise TypeError("Expected instance of HashAlgorithm.")

        self._algorithm = algorithm
        self._digest_size = algorithm.digest_size

    digest_size = utils.read_only_property("_digest_size")
