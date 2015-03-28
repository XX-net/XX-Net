# Copyright (C) AB Strakt
# See LICENSE for details.

"""
pyOpenSSL - A simple wrapper around the OpenSSL library
"""

import sys

try:
    orig = sys.getdlopenflags()
except AttributeError:
    from OpenSSL import crypto
else:
    try:
        import DLFCN
    except ImportError:
        try:
            import dl
        except ImportError:
            try:
                import ctypes
            except ImportError:
                flags = 2 | 256
            else:
                flags = 2 | ctypes.RTLD_GLOBAL
                del ctypes
        else:
            flags = dl.RTLD_NOW | dl.RTLD_GLOBAL
            del dl
    else:
        flags = DLFCN.RTLD_NOW | DLFCN.RTLD_GLOBAL
        del DLFCN

    sys.setdlopenflags(flags)
    from OpenSSL import crypto
    sys.setdlopenflags(orig)
    del orig, flags
del sys

from OpenSSL import rand, SSL
from OpenSSL.version import __version__

__all__ = [
    'rand', 'crypto', 'SSL', 'tsafe', '__version__']
