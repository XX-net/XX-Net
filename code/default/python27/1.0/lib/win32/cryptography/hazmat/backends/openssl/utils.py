# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import absolute_import, division, print_function

import warnings

from cryptography import utils
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed


def _calculate_digest_and_algorithm(backend, data, algorithm):
    if not isinstance(algorithm, Prehashed):
        hash_ctx = hashes.Hash(algorithm, backend)
        hash_ctx.update(data)
        data = hash_ctx.finalize()
    else:
        algorithm = algorithm._algorithm

    if len(data) != algorithm.digest_size:
        raise ValueError(
            "The provided data must be the same length as the hash "
            "algorithm's digest size."
        )

    return (data, algorithm)


def _check_not_prehashed(signature_algorithm):
    if isinstance(signature_algorithm, Prehashed):
        raise TypeError(
            "Prehashed is only supported in the sign and verify methods. "
            "It cannot be used with signer or verifier."
        )


def _warn_sign_verify_deprecated():
    warnings.warn(
        "signer and verifier have been deprecated. Please use sign "
        "and verify instead.",
        utils.PersistentlyDeprecated,
        stacklevel=3
    )
