# Author Hubert Kario, copyright 2021

from .eddsakey import EdDSAKey
from ecdsa.keys import BadSignatureError
from ecdsa.der import UnexpectedDER
from .cryptomath import numBits
from .compat import compatHMAC


class Python_EdDSAKey(EdDSAKey):
    """
    Concrete implementation of EdDSA object backed by python-ecdsa.

    Object that uses the common, abstract API of asymmetric keys
    that uses the python-ecdsa library for the cryptographic operations.

    :vartype public_key: VerifyingKey
    :ivar public_key: python-ecdsa object for veryfying EdDSA signatures, if
        `private_key` is set, it should match it (should be able to verify
        signatures created by it)

    :vartype private_key: SigningKey
    :ivar private_key: python-ecdsa object for creating EdDSA signatures

    :vartype key_type: str
    :ivar key_type: type of assymetric algorithm used by the keys - for this
        objects it is either "Ed25519" or "Ed448"
    """

    def __init__(self, public_key, private_key=None):
        if not public_key and not private_key:
            raise ValueError("at least one key must be provided")
        if not public_key:
            public_key = private_key.verifying_key

        self.curve_name = public_key.curve.name

        self.private_key = private_key
        self.public_key = public_key
        self.key_type = self.curve_name

    def __len__(self):
        return numBits(self.public_key.curve.order)

    def hasPrivateKey(self):
        return bool(self.private_key)

    def acceptsPassword(self):
        return False

    @staticmethod
    def generate(bits):
        raise NotImplementedError()

    def _hashAndSign(self, data):
        return self.private_key.sign_deterministic(compatHMAC(data))

    def _hashAndVerify(self, signature, data):
        try:
            return self.public_key.verify(compatHMAC(signature),
                                          compatHMAC(data))
        # https://github.com/warner/python-ecdsa/issues/114
        except (BadSignatureError, UnexpectedDER, IndexError, AssertionError):
            return False
