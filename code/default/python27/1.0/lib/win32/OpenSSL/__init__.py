# Copyright (C) AB Strakt
# See LICENSE for details.

"""
pyOpenSSL - A simple wrapper around the OpenSSL library
"""
# eGenix: Load the embedded OpenSSL libraries rather than the system
# provided ones.
import sys
import sysconfig
import os
import ctypes


def load_openssl():
    import pkg_resources
    LIBEAY32_pathname = pkg_resources.resource_filename(__name__, 'LIBEAY32.dll')
    SSLEAY32_pathname = pkg_resources.resource_filename(__name__, 'SSLEAY32.dll')
    ctypes.cdll.LoadLibrary(LIBEAY32_pathname)
    ctypes.cdll.LoadLibrary(SSLEAY32_pathname)

#load_openssl()

del sys, sysconfig, os, ctypes

from OpenSSL import crypto, rand, SSL
from OpenSSL.version import __version__

__all__ = [
    'rand', 'crypto', 'SSL', 'tsafe', '__version__']
