# Author: Hubert Kario (c) 2019
# see LICENCE file for legal information regarding use of this file

"""
HMAC module that works in FIPS mode.

Note that this makes this code FIPS non-compliant!
"""

# Because we are extending the hashlib module, we need to import all its
# fields to suppport the same uses
from . import tlshashlib
from .compat import compatHMAC
try:
    from hmac import compare_digest
    __all__ = ["new", "compare_digest", "HMAC"]
except ImportError:
    __all__ = ["new", "HMAC"]

try:
    from hmac import HMAC, new
    # if we can calculate HMAC on MD5, then use the built-in HMAC
    # implementation
    _val = HMAC(b'some key', b'msg', 'md5')
    _val.digest()
    del _val
except Exception:
    # fallback only when MD5 doesn't work
    class HMAC(object):
        """Hacked version of HMAC that works in FIPS mode even with MD5."""

        def __init__(self, key, msg=None, digestmod=None):
            """
            Initialise the HMAC and hash first portion of data.

            msg: data to hash
            digestmod: name of hash or object that be used as a hash and be cloned
            """
            self.key = key
            if digestmod is None:
                digestmod = 'md5'
            if callable(digestmod):
                digestmod = digestmod()
            if not hasattr(digestmod, 'digest_size'):
                digestmod = tlshashlib.new(digestmod)
            self.block_size = digestmod.block_size
            self.digest_size = digestmod.digest_size
            self.digestmod = digestmod
            if len(key) > self.block_size:
                k_hash = digestmod.copy()
                k_hash.update(compatHMAC(key))
                key = k_hash.digest()
            if len(key) < self.block_size:
                key = key + b'\x00' * (self.block_size - len(key))
            key = bytearray(key)
            ipad = bytearray(b'\x36' * self.block_size)
            opad = bytearray(b'\x5c' * self.block_size)
            i_key = bytearray(i ^ j for i, j in zip(key, ipad))
            self._o_key = bytearray(i ^ j for i, j in zip(key, opad))
            self._context = digestmod.copy()
            self._context.update(compatHMAC(i_key))
            if msg:
                self._context.update(compatHMAC(msg))

        def update(self, msg):
            self._context.update(compatHMAC(msg))

        def digest(self):
            i_digest = self._context.digest()
            o_hash = self.digestmod.copy()
            o_hash.update(compatHMAC(self._o_key))
            o_hash.update(compatHMAC(i_digest))
            return o_hash.digest()

        def copy(self):
            new = HMAC.__new__(HMAC)
            new.key = self.key
            new.digestmod = self.digestmod
            new.block_size = self.block_size
            new.digest_size = self.digest_size
            new._o_key = self._o_key
            new._context = self._context.copy()
            return new


    def new(*args, **kwargs):
        """General constructor that works in FIPS mode."""
        return HMAC(*args, **kwargs)
