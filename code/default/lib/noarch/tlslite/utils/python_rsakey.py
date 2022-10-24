# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""Pure-Python RSA implementation."""
import threading
from .cryptomath import *
from .rsakey import *
from .pem import *
from .deprecations import deprecated_params
if GMPY2_LOADED:
    from gmpy2 import mpz
elif gmpyLoaded:
    from gmpy import mpz

class Python_RSAKey(RSAKey):
    def __init__(self, n=0, e=0, d=0, p=0, q=0, dP=0, dQ=0, qInv=0,
                 key_type="rsa"):
        """Initialise key directly from integers.

        see also generate() and parsePEM()."""
        if (n and not e) or (e and not n):
            raise AssertionError()
        if gmpyLoaded or GMPY2_LOADED:
            n = mpz(n)
            e = mpz(e)
            d = mpz(d)
            p = mpz(p)
            q = mpz(q)
            dP = mpz(dP)
            dQ = mpz(dQ)
            qInv = mpz(qInv)
        self.n = n
        self.e = e
        if p and not q or not p and q:
            raise ValueError("p and q must be set or left unset together")
        if not d and p and q:
            t = lcm(p - 1, q - 1)
            d = invMod(e, t)
        self.d = d
        self.p = p
        self.q = q
        if not dP and p:
            dP = d % (p - 1)
        self.dP = dP
        if not dQ and q:
            dQ = d % (q - 1)
        self.dQ = dQ
        if not qInv:
            qInv = invMod(q, p)
        self.qInv = qInv
        self.blinder = 0
        self.unblinder = 0
        self._lock = threading.Lock()
        self.key_type = key_type

    def hasPrivateKey(self):
        """
        Does the key has the associated private key (True) or is it only
        the public part (False).
        """
        return self.d != 0

    def _rawPrivateKeyOp(self, message):
        n = self.n
        with self._lock:
            # Create blinding values, on the first pass:
            if not self.blinder:
                self.unblinder = getRandomNumber(2, n)
                self.blinder = powMod(invMod(self.unblinder, n), self.e,
                                      n)
            unblinder = self.unblinder
            blinder = self.blinder

            # Update blinding values
            self.blinder = (blinder * blinder) % n
            self.unblinder = (unblinder * unblinder) % n

        # Blind the input
        message = (message * blinder) % n

        # Perform the RSA operation
        cipher = self._rawPrivateKeyOpHelper(message)

        # Unblind the output
        cipher = (cipher * unblinder) % n

        # Return the output
        return cipher

    def _rawPrivateKeyOpHelper(self, m):
        #Non-CRT version
        #c = pow(m, self.d, self.n)

        #CRT version  (~3x faster).
        p, q = self.p, self.q
        s1 = pow(m, self.dP, p)
        s2 = pow(m, self.dQ, q)
        h = ((s1 - s2) * self.qInv) % p
        c = s2 + q * h
        return c

    def _rawPublicKeyOp(self, ciphertext):
        msg = pow(ciphertext, self.e, self.n)
        return msg

    def acceptsPassword(self):
        """Does it support encrypted key files."""
        return False

    @staticmethod
    def generate(bits, key_type="rsa"):
        """Generate a private key with modulus 'bits' bit big.

        key_type can be "rsa" for a universal rsaEncryption key or
        "rsa-pss" for a key that can be used only for RSASSA-PSS."""
        # p, q, and t are standard names for the variables in RSA, so
        # ignore the fact those are one character long variable names
        # pylint: disable=invalid-name
        key = Python_RSAKey()
        while True:
            p = getRandomPrime(bits//2, False)
            q = getRandomPrime(bits//2, False)
            if gmpyLoaded or GMPY2_LOADED:
                p = mpz(p)
                q = mpz(q)
            t = lcm(p-1, q-1)
            # since we need to calculate inverse of 65537 mod t, they
            # must be relatively prime (coprime)
            if gcd(t, 65537) == 1:
                break
        key.n = p * q
        if gmpyLoaded or GMPY2_LOADED:
            key.e = mpz(65537)
        else:
            key.e = 65537
        key.d = invMod(key.e, t)
        key.p = p
        key.q = q
        key.dP = key.d % (p-1)
        key.dQ = key.d % (q-1)
        key.qInv = invMod(q, p)
        key.key_type = key_type
        # pylint: enable=invalid-name
        return key

    @staticmethod
    @deprecated_params({"data": "s", "password_callback": "passwordCallback"})
    def parsePEM(data, password_callback=None):
        """Parse a string containing a PEM-encoded <privateKey>."""
        from .python_key import Python_Key
        return Python_Key.parsePEM(data, password_callback)
