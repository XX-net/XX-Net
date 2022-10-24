# Author: Hubert Kario (c) 2015
#
# See the LICENSE file for legal information regarding use of this file.

"""Pure-Python ChaCha20/Poly1305 implementation."""

from .chacha20_poly1305 import CHACHA20_POLY1305

def new(key):
    """Return an AEAD cipher implementation"""
    return CHACHA20_POLY1305(key, "python")
