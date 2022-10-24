# Author: Google
# See the LICENSE file for legal information regarding use of this file.

"""PyCrypto AES-GCM implementation."""

from .cryptomath import *
from .aesgcm import AESGCM

if pycryptoLoaded:
    import Crypto.Cipher.AES

    def new(key):
        cipher = Crypto.Cipher.AES.new(bytes(key))
        def encrypt(plaintext):
            return bytearray(cipher.encrypt(bytes(plaintext)))
        return AESGCM(key, "pycrypto", encrypt)
