# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""Factory functions for symmetric cryptography."""

import os

from tlslite.utils import python_aes
from tlslite.utils import python_aesgcm
from tlslite.utils import python_aesccm
from tlslite.utils import python_chacha20_poly1305
from tlslite.utils import python_rc4
from tlslite.utils import python_tripledes
from tlslite.utils import openssl_aesccm
from tlslite.utils import openssl_aesgcm

from tlslite.utils import cryptomath

tripleDESPresent = True
"""Inform if the 3DES algorithm is supported."""

if cryptomath.m2cryptoLoaded:
    from tlslite.utils import openssl_aes
    from tlslite.utils import openssl_rc4
    from tlslite.utils import openssl_tripledes

if cryptomath.pycryptoLoaded:
    from tlslite.utils import pycrypto_aes
    from tlslite.utils import pycrypto_aesgcm
    from tlslite.utils import pycrypto_rc4
    from tlslite.utils import pycrypto_tripledes

# **************************************************************************
# Factory Functions for AES
# **************************************************************************

def createAES(key, IV, implList=None):
    """Create a new AES object.

    :type key: str
    :param key: A 16, 24, or 32 byte string.

    :type IV: str
    :param IV: A 16 byte string

    :rtype: tlslite.utils.AES
    :returns: An AES object.
    """
    if implList is None:
        implList = ["openssl", "pycrypto", "python"]

    for impl in implList:
        if impl == "openssl" and cryptomath.m2cryptoLoaded:
            return openssl_aes.new(key, 2, IV)
        elif impl == "pycrypto" and cryptomath.pycryptoLoaded:
            return pycrypto_aes.new(key, 2, IV)
        elif impl == "python":
                return python_aes.new(key, 2, IV)
    raise NotImplementedError()

def createAESCTR(key, IV, implList=None):
    """Create a new AESCTR object.

    :type key: str
    :param key: A 16, 24, or 32 byte string.

    :type IV: str
    :param IV: A 8 or 12 byte string

    :rtype: tlslite.utils.AES
    :returns: An AES object.
    """
    if implList is None:
        implList = ["python"]

    for impl in implList:
        if impl == "python":
            return python_aes.new(key, 6, IV)
    raise NotImplementedError()

def createAESGCM(key, implList=None):
    """Create a new AESGCM object.

    :type key: bytearray
    :param key: A 16 or 32 byte byte array.

    :rtype: tlslite.utils.AESGCM
    :returns: An AESGCM object.
    """
    if implList is None:
        implList = ["openssl", "pycrypto", "python"]

    for impl in implList:
        if impl == "openssl" and cryptomath.m2cryptoLoaded:
            return openssl_aesgcm.new(key)
        if impl == "pycrypto" and cryptomath.pycryptoLoaded:
            return pycrypto_aesgcm.new(key)
        if impl == "python":
            return python_aesgcm.new(key)
    raise NotImplementedError()

def createAESCCM(key, implList=None):
    """ Create a new AESCCM object.

    :type key: bytearray
    :param key: A 16 or 32 byte byte array to serve as key.

    :rtype: tlslite.utils.AESCCM
    :returns: An AESCCM object.
    """

    if implList is None:
        implList = ["openssl", "python"]

    for impl in implList:
        if impl == "openssl" and cryptomath.m2cryptoLoaded:
            return openssl_aesccm.new(key)
        if impl == "python":
            return python_aesccm.new(key)

    raise NotImplementedError()

def createAESCCM_8(key, implList=None):
    """ Create a new AESCCM object with truncated tag.

    :type key: bytearray
    :param key: A 16 or 32 byte byte array to serve as key.

    :rtype: tlslite.utils.AESCCM
    :returns: An AESCCM object.
    """

    if implList is None:
        implList = ["openssl", "python"]

    for impl in implList:
        if impl == "openssl" and cryptomath.m2cryptoLoaded:
            return openssl_aesccm.new(key, 8)
        if impl == "python":
            return python_aesccm.new(key, 8)

    raise NotImplementedError()

def createCHACHA20(key, implList=None):
    """Create a new CHACHA20_POLY1305 object.

    :type key: bytearray
    :param key: a 32 byte array to serve as key

    :rtype: tlslite.utils.CHACHA20_POLY1305
    :returns: A ChaCha20/Poly1305 object
    """
    if implList is None:
        implList = ["python"]

    for impl in implList:
        if impl == "python":
            return python_chacha20_poly1305.new(key)
    raise NotImplementedError()

def createRC4(key, IV, implList=None):
    """Create a new RC4 object.

    :type key: str
    :param key: A 16 to 32 byte string.

    :type IV: object
    :param IV: Ignored, whatever it is.

    :rtype: tlslite.utils.RC4
    :returns: An RC4 object.
    """
    if implList is None:
        implList = ["openssl", "pycrypto", "python"]

    if len(IV) != 0:
        raise AssertionError()
    for impl in implList:
        if impl == "openssl" and cryptomath.m2cryptoLoaded:
            return openssl_rc4.new(key)
        elif impl == "pycrypto" and cryptomath.pycryptoLoaded:
            return pycrypto_rc4.new(key)
        elif impl == "python":
            return python_rc4.new(key)
    raise NotImplementedError()

#Create a new TripleDES instance
def createTripleDES(key, IV, implList=None):
    """Create a new 3DES object.

    :type key: str
    :param key: A 24 byte string.

    :type IV: str
    :param IV: An 8 byte string

    :rtype: tlslite.utils.TripleDES
    :returns: A 3DES object.
    """
    if implList is None:
        implList = ["openssl", "pycrypto", "python"]

    for impl in implList:
        if impl == "openssl" and cryptomath.m2cryptoLoaded:
            return openssl_tripledes.new(key, 2, IV)
        elif impl == "pycrypto" and cryptomath.pycryptoLoaded:
            return pycrypto_tripledes.new(key, 2, IV)
        elif impl == "python":
            return python_tripledes.new(key, IV)
    raise NotImplementedError()
