# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""PyCrypto RSA implementation."""

from __future__ import print_function
import sys

from .cryptomath import *

from .rsakey import *
from .python_rsakey import Python_RSAKey
from .compat import compatLong

if pycryptoLoaded:

    from Crypto.PublicKey import RSA

    class PyCrypto_RSAKey(RSAKey):
        def __init__(self, n=0, e=0, d=0, p=0, q=0, dP=0, dQ=0, qInv=0,
                     key_type="rsa"):
            del dP, dQ, qInv  # pycrypto calculates them by its own
            if not d:
                self.rsa = RSA.construct((compatLong(n), compatLong(e)))
            else:
                self.rsa = RSA.construct((compatLong(n), compatLong(e),
                                          compatLong(d), compatLong(p),
                                          compatLong(q)))
            self.key_type = key_type

        def __getattr__(self, name):
            return getattr(self.rsa, name)

        def hasPrivateKey(self):
            return self.rsa.has_private()

        def _rawPrivateKeyOp(self, message):
            try:
                return self.rsa.decrypt((compatLong(message),))
            except ValueError as e:
                print("rsa: {0!r}".format(self.rsa), file=sys.stderr)
                values = []
                for name in ["n", "e", "d", "p", "q", "dP", "dQ", "qInv"]:
                    values.append("{0}: {1}".format(name,
                                                    getattr(self, name, None)))
                print(", ".join(values), file=sys.stderr)
                print("message: {0}".format(message), file=sys.stderr)
                raise


        def _rawPublicKeyOp(self, ciphertext):
            try:
                return self.rsa.encrypt(compatLong(ciphertext), None)[0]
            except ValueError as e:
                print("rsa: {0!r}".format(self.rsa), file=sys.stderr)
                values = []
                for name in ["n", "e", "d", "p", "q", "dP", "dQ", "qInv"]:
                    values.append("{0}: {1}".format(name,
                                                    getattr(self, name, None)))
                print(", ".join(values), file=sys.stderr)
                print("ciphertext: {0}".format(ciphertext), file=sys.stderr)
                raise

        @staticmethod
        def generate(bits, key_type="rsa"):
            key = PyCrypto_RSAKey()
            def f(numBytes):
                return bytes(getRandomBytes(numBytes))
            key.rsa = RSA.generate(bits, f)
            key.key_type = key_type
            return key
