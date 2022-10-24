# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

try:
    from tack.structures.Tack import Tack
    from tack.structures.TackExtension import TackExtension
    from tack.tls.TlsCertificate import TlsCertificate
    
    tackpyLoaded = True
except ImportError:
    tackpyLoaded = False
