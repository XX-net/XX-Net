# Author: Stanislav Zidek
# See the LICENSE file for legal information regarding use of this file.

"""Abstract class for ECDSA."""

from .cryptomath import secureHash


class ECDSAKey(object):
    """This is an abstract base class for ECDSA keys.

    Particular implementations of ECDSA keys, such as
    :py:class:`~.python_ecdsakey.Python_ECDSAKey`
    ... more coming
    inherit from this.

    To create or parse an ECDSA key, don't use one of these classes
    directly.  Instead, use the factory functions in
    :py:class:`~tlslite.utils.keyfactory`.
    """

    def __init__(self, public_key, private_key):
        """Create a new ECDSA key.

        If public_key or private_key are passed in, the new key
        will be initialized.

        :param public_key: ECDSA public key.

        :param private_key: ECDSA private key.
        """
        raise NotImplementedError()

    def __len__(self):
        """Return the size of the order of the curve of this key, in bits.

        :rtype: int
        """
        raise NotImplementedError()

    def hasPrivateKey(self):
        """Return whether or not this key has a private component.

        :rtype: bool
        """
        raise NotImplementedError()

    def _sign(self, data, hash_alg):
        raise NotImplementedError()

    def _hashAndSign(self, data, hAlg):
        raise NotImplementedError()

    def _verify(self, signature, hash_bytes):
        raise NotImplementedError()

    def hashAndSign(self, bytes, rsaScheme=None, hAlg='sha1', sLen=None):
        """Hash and sign the passed-in bytes.

        This requires the key to have a private component. It performs
        a signature on the passed-in data with selected hash algorithm.

        :type bytes: bytes-like object
        :param bytes: The value which will be hashed and signed.

        :type rsaScheme: str
        :param rsaScheme: Ignored, present for API compatibility with RSA

        :type hAlg: str
        :param hAlg: The hash algorithm that will be used to hash data

        :type sLen: int
        :param sLen: Ignored, present for API compatibility with RSA

        :rtype: bytearray
        :returns: An ECDSA signature on the passed-in data.
        """
        hAlg = hAlg.lower()
        hashBytes = secureHash(bytearray(bytes), hAlg)
        return self.sign(hashBytes, padding=rsaScheme, hashAlg=hAlg,
                         saltLen=sLen)

    def hashAndVerify(self, sigBytes, bytes, rsaScheme=None, hAlg='sha1',
                      sLen=None):
        """Hash and verify the passed-in bytes with the signature.

        This verifies an ECDSA signature on the passed-in data
        with selected hash algorithm.

        :type sigBytes: bytearray
        :param sigBytes: An ECDSA signature, DER encoded.

        :type bytes: str or bytearray
        :param bytes: The value which will be hashed and verified.

        :type rsaScheme: str
        :param rsaScheme: Ignored, present for API compatibility with RSA

        :type hAlg: str
        :param hAlg: The hash algorithm that will be used

        :type sLen: int
        :param sLen: Ignored, present for API compatibility with RSA

        :rtype: bool
        :returns: Whether the signature matches the passed-in data.
        """
        hAlg = hAlg.lower()

        hashBytes = secureHash(bytearray(bytes), hAlg)
        return self.verify(sigBytes, hashBytes, rsaScheme, hAlg, sLen)

    def sign(self, bytes, padding=None, hashAlg="sha1", saltLen=None):
        """Sign the passed-in bytes.

        This requires the key to have a private component.  It performs
        an ECDSA signature on the passed-in data.

        :type bytes: bytearray
        :param bytes: The value which will be signed (generally a binary
            encoding of hash output.

        :type padding: str
        :param padding: Ignored, present for API compatibility with RSA

        :type hashAlg: str
        :param hashAlg: name of hash that was used for calculating the bytes

        :type saltLen: int
        :param saltLen: Ignored, present for API compatibility with RSA

        :rtype: bytearray
        :returns: An ECDSA signature on the passed-in data.
        """
        sigBytes = self._sign(bytes, hashAlg)
        return sigBytes

    def verify(self, sigBytes, bytes, padding=None, hashAlg=None,
               saltLen=None):
        """Verify the passed-in bytes with the signature.

        This verifies a PKCS1 signature on the passed-in data.

        :type sigBytes: bytearray
        :param sigBytes: A PKCS1 signature.

        :type bytes: bytearray
        :param bytes: The value which will be verified.

        :type padding: str
        :param padding: Ignored, present for API compatibility with RSA

        :rtype: bool
        :returns: Whether the signature matches the passed-in data.
        """
        return self._verify(sigBytes, bytes)

    def acceptsPassword(self):
        """Return True if the write() method accepts a password for use
        in encrypting the private key.

        :rtype: bool
        """
        raise NotImplementedError()

    def write(self, password=None):
        """Return a string containing the key.

        :rtype: str
        :returns: A string describing the key, in whichever format (PEM)
            is native to the implementation.
        """
        raise NotImplementedError()

    @staticmethod
    def generate(bits):
        """Generate a new key with the specified curve.

        :rtype: ~tlslite.utils.ECDSAKey.ECDSAKey
        """
        raise NotImplementedError()
