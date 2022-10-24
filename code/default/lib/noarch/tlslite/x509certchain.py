# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""Class representing an X.509 certificate chain."""

from .utils import cryptomath
from .utils.tackwrapper import *
from .utils.pem import *
from .x509 import X509

class X509CertChain(object):
    """This class represents a chain of X.509 certificates.

    :vartype x509List: list
    :ivar x509List: A list of :py:class:`tlslite.x509.X509` instances,
        starting with the end-entity certificate and with every
        subsequent certificate certifying the previous.
    """

    def __init__(self, x509List=None):
        """Create a new X509CertChain.

        :type x509List: list
        :param x509List: A list of :py:class:`tlslite.x509.X509` instances,
            starting with the end-entity certificate and with every
            subsequent certificate certifying the previous.
        """
        if x509List:
            self.x509List = x509List
        else:
            self.x509List = []

    def __hash__(self):
        """Return hash of the object."""
        return hash(tuple(self.x509List))

    def __eq__(self, other):
        """Compare objects with each-other."""
        if not hasattr(other, "x509List"):
            return NotImplemented
        return self.x509List == other.x509List

    def __ne__(self, other):
        """Compare object for inequality."""
        if not hasattr(other, "x509List"):
            return NotImplemented
        return self.x509List != other.x509List

    def parsePemList(self, s):
        """Parse a string containing a sequence of PEM certs.

        Raise a SyntaxError if input is malformed.
        """
        x509List = []
        bList = dePemList(s, "CERTIFICATE")
        for b in bList:
            x509 = X509()
            x509.parseBinary(b)
            x509List.append(x509)
        self.x509List = x509List

    def getNumCerts(self):
        """Get the number of certificates in this chain.

        :rtype: int
        """
        return len(self.x509List)

    def getEndEntityPublicKey(self):
        """Get the public key from the end-entity certificate.

        :rtype: ~tlslite.utils.rsakey.RSAKey`
        """
        if self.getNumCerts() == 0:
            raise AssertionError()
        return self.x509List[0].publicKey

    def getFingerprint(self):
        """Get the hex-encoded fingerprint of the end-entity certificate.

        :rtype: str
        :returns: A hex-encoded fingerprint.
        """
        if self.getNumCerts() == 0:
            raise AssertionError()
        return self.x509List[0].getFingerprint()

    def checkTack(self, tack):
        if self.x509List:
            tlsCert = TlsCertificate(self.x509List[0].bytes)
            if tlsCert.matches(tack):
                return True
        return False
        
    def getTackExt(self):
        """Get the TACK and/or Break Sigs from a TACK Cert in the chain."""
        tackExt = None
        # Search list in backwards order
        for x509 in self.x509List[::-1]:
            tlsCert = TlsCertificate(x509.bytes)
            if tlsCert.tackExt:
                if tackExt:
                    raise SyntaxError("Multiple TACK Extensions")
                else:
                    tackExt = tlsCert.tackExt
        return tackExt
                
