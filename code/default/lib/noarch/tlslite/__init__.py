# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""TLS Lite is a free python library that implements SSL and TLS. TLS Lite
supports RSA and SRP ciphersuites. TLS Lite is pure python, however it can use
other libraries for faster crypto operations. TLS Lite integrates with several
stdlib neworking libraries.

API documentation is available in the 'docs' directory.

If you have questions or feedback, feel free to contact me.

To use, do::

    from tlslite import TLSConnection, ...

If you want to import the most useful objects, the cleanest way is::

    from tlslite.api import *

Then use the :py:class:`TLSConnection` class with a socket.
(Or, use one of the integration classes in :py:mod:`tlslite.integration`).
"""

from tlslite.api import *
from tlslite.api import __version__ # Unsure why this is needed, but it is
