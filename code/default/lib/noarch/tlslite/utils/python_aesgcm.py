# Author: Google
# See the LICENSE file for legal information regarding use of this file.

"""Pure-Python AES-GCM implementation."""

from .aesgcm import AESGCM
from .rijndael import Rijndael


def new(key):
    return AESGCM(key, "python", Rijndael(key, 16).encrypt)
