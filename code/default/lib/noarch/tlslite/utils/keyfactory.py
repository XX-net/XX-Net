# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""Factory functions for asymmetric cryptography."""

from .compat import *

from .rsakey import RSAKey
from .python_rsakey import Python_RSAKey
from .python_ecdsakey import Python_ECDSAKey
from .python_dsakey import Python_DSAKey
from .python_eddsakey import Python_EdDSAKey
from tlslite.utils import cryptomath

if cryptomath.m2cryptoLoaded:
    from .openssl_rsakey import OpenSSL_RSAKey

if cryptomath.pycryptoLoaded:
    from .pycrypto_rsakey import PyCrypto_RSAKey

# **************************************************************************
# Factory Functions for RSA Keys
# **************************************************************************

def generateRSAKey(bits, implementations=["openssl", "python"]):
    """Generate an RSA key with the specified bit length.

    :type bits: int
    :param bits: Desired bit length of the new key's modulus.

    :rtype: ~tlslite.utils.rsakey.RSAKey
    :returns: A new RSA private key.
    """
    for implementation in implementations:
        if implementation == "openssl" and cryptomath.m2cryptoLoaded:
            return OpenSSL_RSAKey.generate(bits)
        elif implementation == "python":
            return Python_RSAKey.generate(bits)
    raise ValueError("No acceptable implementations")

#Parse as an OpenSSL or Python key
def parsePEMKey(s, private=False, public=False, passwordCallback=None,
                implementations=["openssl", "python"]):
    """Parse a PEM-format key.

    The PEM format is used by OpenSSL and other tools.  The
    format is typically used to store both the public and private
    components of a key.  For example::

       -----BEGIN RSA PRIVATE KEY-----
        MIICXQIBAAKBgQDYscuoMzsGmW0pAYsmyHltxB2TdwHS0dImfjCMfaSDkfLdZY5+
        dOWORVns9etWnr194mSGA1F0Pls/VJW8+cX9+3vtJV8zSdANPYUoQf0TP7VlJxkH
        dSRkUbEoz5bAAs/+970uos7n7iXQIni+3erUTdYEk2iWnMBjTljfgbK/dQIDAQAB
        AoGAJHoJZk75aKr7DSQNYIHuruOMdv5ZeDuJvKERWxTrVJqE32/xBKh42/IgqRrc
        esBN9ZregRCd7YtxoL+EVUNWaJNVx2mNmezEznrc9zhcYUrgeaVdFO2yBF1889zO
        gCOVwrO8uDgeyj6IKa25H6c1N13ih/o7ZzEgWbGG+ylU1yECQQDv4ZSJ4EjSh/Fl
        aHdz3wbBa/HKGTjC8iRy476Cyg2Fm8MZUe9Yy3udOrb5ZnS2MTpIXt5AF3h2TfYV
        VoFXIorjAkEA50FcJmzT8sNMrPaV8vn+9W2Lu4U7C+K/O2g1iXMaZms5PC5zV5aV
        CKXZWUX1fq2RaOzlbQrpgiolhXpeh8FjxwJBAOFHzSQfSsTNfttp3KUpU0LbiVvv
        i+spVSnA0O4rq79KpVNmK44Mq67hsW1P11QzrzTAQ6GVaUBRv0YS061td1kCQHnP
        wtN2tboFR6lABkJDjxoGRvlSt4SOPr7zKGgrWjeiuTZLHXSAnCY+/hr5L9Q3ZwXG
        6x6iBdgLjVIe4BZQNtcCQQDXGv/gWinCNTN3MPWfTW/RGzuMYVmyBFais0/VrgdH
        h1dLpztmpQqfyH/zrBXQ9qL/zR4ojS6XYneO/U18WpEe
        -----END RSA PRIVATE KEY-----

    To generate a key like this with OpenSSL, run::

        openssl genrsa 2048 > key.pem

    This format also supports password-encrypted private keys.  TLS
    Lite can only handle password-encrypted private keys when OpenSSL
    and M2Crypto are installed.  In this case, passwordCallback will be
    invoked to query the user for the password.

    :type s: str
    :param s: A string containing a PEM-encoded public or private key.

    :type private: bool
    :param private: If True, a :py:class:`SyntaxError` will be raised if the
        private key component is not present.

    :type public: bool
    :param public: If True, the private key component (if present) will
        be discarded, so this function will always return a public key.

    :type passwordCallback: callable
    :param passwordCallback: This function will be called, with no
        arguments, if the PEM-encoded private key is password-encrypted.
        The callback should return the password string.  If the password is
        incorrect, SyntaxError will be raised.  If no callback is passed
        and the key is password-encrypted, a prompt will be displayed at
        the console.

    :rtype: ~tlslite.utils.rsakey.RSAKey
    :returns: An RSA key.

    :raises SyntaxError: If the key is not properly formatted.
    """
    # as old versions of openssl can't handle RSA-PSS or ECDSA keys, first
    # try to detect what kind of key it is (we ignore errors as the python
    # code can't handle encrypted key files while m2crypto/openssl can)
    key_type = "rsa"
    try:
        key = Python_RSAKey.parsePEM(s)
        key_type = key.key_type
        del key
    except Exception:
        pass

    for implementation in implementations:
        if implementation == "openssl" and cryptomath.m2cryptoLoaded \
                and key_type == "rsa":
            key = OpenSSL_RSAKey.parse(s, passwordCallback)
            break
        elif implementation == "python":
            key = Python_RSAKey.parsePEM(s)
            break
    else:
        raise ValueError("No acceptable implementations")

    return _parseKeyHelper(key, private, public)


def _parseKeyHelper(key, private, public):
    if private and not key.hasPrivateKey():
        raise SyntaxError("Not a private key!")

    if public:
        return _createPublicKey(key)

    if private:
        if cryptomath.m2cryptoLoaded:
            if type(key) == Python_RSAKey:
                return _createPrivateKey(key)
            assert type(key) in (OpenSSL_RSAKey, Python_ECDSAKey,
                Python_DSAKey, Python_EdDSAKey), type(key)
            return key
        elif hasattr(key, "d"):
            return _createPrivateKey(key)
    return key


def parseAsPublicKey(s):
    """Parse a PEM-formatted public key.

    :type s: str
    :param s: A string containing a PEM-encoded public or private key.

    :rtype: ~tlslite.utils.rsakey.RSAKey
    :returns: An RSA public key.

    :raises SyntaxError: If the key is not properly formatted.
    """
    return parsePEMKey(s, public=True)

def parsePrivateKey(s):
    """Parse a PEM-formatted private key.

    :type s: str
    :param s: A string containing a PEM-encoded private key.

    :rtype: ~tlslite.utils.rsakey.RSAKey
    :returns: An RSA private key.

    :raises SyntaxError: If the key is not properly formatted.
    """
    return parsePEMKey(s, private=True)

def _createPublicKey(key):
    """
    Create a new public key.  Discard any private component,
    and return the most efficient key possible.
    """
    if not isinstance(key, RSAKey):
        raise AssertionError()
    return _createPublicRSAKey(key.n, key.e, key.key_type)

def _createPrivateKey(key):
    """
    Create a new private key.  Return the most efficient key possible.
    """
    if not isinstance(key, RSAKey):
        raise AssertionError()
    if not key.hasPrivateKey():
        raise AssertionError()
    return _createPrivateRSAKey(key.n, key.e, key.d, key.p, key.q, key.dP,
                                key.dQ, key.qInv, key.key_type)

# n, e, d, etc. are the names used in mathematical proofs for the variables
# so using so short names makes it actually more readable
# pylint: disable=invalid-name
def _createPublicRSAKey(n, e, key_type,
                        implementations=("openssl", "pycrypto", "python")):
    for implementation in implementations:
        if implementation == "openssl" and cryptomath.m2cryptoLoaded:
            return OpenSSL_RSAKey(n, e, key_type=key_type)
        elif implementation == "pycrypto" and cryptomath.pycryptoLoaded:
            return PyCrypto_RSAKey(n, e, key_type=key_type)
        elif implementation == "python":
            return Python_RSAKey(n, e, key_type=key_type)
    raise ValueError("No acceptable implementations")

def _createPrivateRSAKey(n, e, d, p, q, dP, dQ, qInv, key_type,
                         implementations=("pycrypto", "python")):
    for implementation in implementations:
        if implementation == "pycrypto" and cryptomath.pycryptoLoaded:
            return PyCrypto_RSAKey(n, e, d, p, q, dP, dQ, qInv,
                                   key_type=key_type)
        elif implementation == "python":
            return Python_RSAKey(n, e, d, p, q, dP, dQ, qInv,
                                 key_type=key_type)
    raise ValueError("No acceptable implementations")
# pylint: enable=invalid-name


def _create_public_ecdsa_key(point_x, point_y, curve_name,
                             implementations=("python",)):
    """
    Convert public key parameters into concrete implementation of verifier.

    The public key in ECDSA is a point on elliptic curve, so it consists of
    two integers that identify the point and the name of the curve on which
    it needs to lie on.

    :type point_x: int
    :param point_x: the 'x' coordinate of the point
    :type point_y: int
    :param point_y: the 'y' coordinate of the point
    :type curve_name: str
    :param curve_name: well known name of the curve (e.g. 'NIST256p' or
        'SECP256k1')
    :type implementations: iterable of str
    :param implementations: list of implementations that can be used as the
        concrete implementation of the verifying key (only 'python' is
        supported currently)
    """
    for impl in implementations:
        if impl == "python":
            return Python_ECDSAKey(point_x, point_y, curve_name)
    raise ValueError("No acceptable implementation")


def _create_public_eddsa_key(public_key,
                             implementations=("python",)):
    """
    Convert the python-ecdsa public key into concrete implementation of
    verifier.
    """
    for impl in implementations:
        if impl == "python":
            return Python_EdDSAKey(public_key)
    raise ValueError("No acceptable implementation")


def _create_public_dsa_key(p, q, g, y,
                           implementations=("python",)):
    """
    Convert public key parameters into concrete implementation of verifier.

    The public key in DSA consists of four integers.

    :type p: int
    :param p: domain parameter, prime num defining Gaolis Field
    :type q: int
    :param q: domain parameter, prime factor of p-1
    :type g: int
    :param g: domain parameter, generator of q-order cyclic group GP(p)
    :type y: int
    :param y: public key
    :type implementations: iterable of str
    :param implementations: list of implementations that can be used as the
        concrete implementation of the verifying key (only 'python' is
        supported currently)
    """
    for impl in implementations:
        if impl == "python":
            return Python_DSAKey(p=p, q=q, g=g, y=y)
    raise ValueError("No acceptable implementation")
