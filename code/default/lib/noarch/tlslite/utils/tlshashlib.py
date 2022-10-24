# Author: Hubert Kario (c) 2015
# see LICENCE file for legal information regarding use of this file

"""hashlib that handles FIPS mode."""

# Because we are extending the hashlib module, we need to import all its
# fields to suppport the same uses
# pylint: disable=unused-wildcard-import, wildcard-import
from hashlib import *
# pylint: enable=unused-wildcard-import, wildcard-import
import hashlib


def _fipsFunction(func, *args, **kwargs):
    """Make hash function support FIPS mode."""
    try:
        return func(*args, **kwargs)
    except ValueError:
        return func(*args, usedforsecurity=False, **kwargs)


# redefining the function is exactly what we intend to do
# pylint: disable=function-redefined
def md5(*args, **kwargs):
    """MD5 constructor that works in FIPS mode."""
    return _fipsFunction(hashlib.md5, *args, **kwargs)


def new(*args, **kwargs):
    """General constructor that works in FIPS mode."""
    return _fipsFunction(hashlib.new, *args, **kwargs)
# pylint: enable=function-redefined
