# Author Hubert Kario, copyright 2019

from .ecdsakey import ECDSAKey
from ecdsa.curves import curves
from ecdsa.util import sigencode_der, sigdecode_der
from ecdsa.keys import VerifyingKey, SigningKey, BadSignatureError
from ecdsa.ellipticcurve import Point
from ecdsa.der import UnexpectedDER
from . import tlshashlib
from .cryptomath import numBits
from .compat import compatHMAC

class Python_ECDSAKey(ECDSAKey):
    """
    Concrete implementation of ECDSA object backed by python-ecdsa.

    Object that uses the common, abstract API of asymmetric keys
    that uses the python-ecdsa library for the cryptographic operations.

    :vartype public_key: VerifyingKey
    :ivar public_key: python-ecdsa object for veryfying ECDSA signatures, if
        `private_key` is set, it should match it (should be able to verify
        signatures created by it)

    :vartype private_key: SigningKey
    :ivar private_key: python-ecdsa object for creating ECDSA signatures

    :vartype key_type: str
    :ivar key_type: type of assymetric algorithm used by the keys - for this
        objects it is always 'ecdsa'
    """

    def __init__(self, x, y, curve_name, secret_multiplier=None):
        if not curve_name:
            raise ValueError("curve_name must be specified")
        self.curve_name = curve_name

        for c in curves:
            if c.name == curve_name or c.openssl_name == curve_name:
                curve = c
                break
        else:
            raise ValueError("Curve '{0}' not supported by python-ecdsa"
                             .format(curve_name))

        self.private_key = None
        self.public_key = None
        self.key_type = "ecdsa"

        if secret_multiplier:
            self.private_key = SigningKey.from_secret_exponent(
                secret_multiplier, curve)

        if x and y:
            point = Point(curve.curve, x, y)
            self.public_key = VerifyingKey.from_public_point(point, curve)

        if not self.public_key:
            self.public_key = self.private_key.get_verifying_key()

    def __len__(self):
        return numBits(self.public_key.curve.order)

    def hasPrivateKey(self):
        return bool(self.private_key)

    def acceptsPassword(self):
        return False

    @staticmethod
    def generate(bits):
        raise NotImplementedError()

    def _sign(self, data, hAlg):
        func = getattr(tlshashlib, hAlg)

        return self.private_key.\
            sign_digest_deterministic(compatHMAC(data),
                                      hashfunc=func,
                                      sigencode=sigencode_der)

    def _hashAndSign(self, data, hAlg):
        return self.private_key.sign_deterministic(compatHMAC(data),
                                                   hash=getattr(tlshashlib,
                                                                hAlg),
                                                   sigencode=sigencode_der)

    def _verify(self, signature, hash_bytes):
        try:
            return self.public_key.verify_digest(compatHMAC(signature),
                                                 compatHMAC(hash_bytes),
                                                 sigdecode_der)
        # https://github.com/warner/python-ecdsa/issues/114
        except (BadSignatureError, UnexpectedDER, IndexError, AssertionError):
            return False
