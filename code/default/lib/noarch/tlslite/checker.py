# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""Class for post-handshake certificate checking."""

from .x509 import X509
from .x509certchain import X509CertChain
from .errors import *


class Checker(object):
    """
    This class is passed to a handshake function to check the other
    party's certificate chain.

    If a handshake function completes successfully, but the Checker
    judges the other party's certificate chain to be missing or
    inadequate, a subclass of
    :py:class:`tlslite.errors.TLSAuthenticationError`
    will be raised.

    Currently, the Checker can check an X.509 chain.
    """

    def __init__(self,
                 x509Fingerprint=None,
                 checkResumedSession=False):
        """
        Create a new Checker instance.

        You must pass in one of these argument combinations:
         - x509Fingerprint

        :param str x509Fingerprint: A hex-encoded X.509 end-entity
            fingerprint which the other party's end-entity certificate must
            match.

        :param bool checkResumedSession: If resumed sessions should be
            checked.  This defaults to False, on the theory that if the
            session was checked once, we don't need to bother
            re-checking it.
        """

        self.x509Fingerprint = x509Fingerprint
        self.checkResumedSession = checkResumedSession

    def __call__(self, connection):
        """Check a TLSConnection.

        When a Checker is passed to a handshake function, this will
        be called at the end of the function.

        :param tlslite.tlsconnection.TLSConnection connection: The
            TLSConnection to examine.

        :raises tlslite.errors.TLSAuthenticationError: If the other
            party's certificate chain is missing or bad.
        """
        if not self.checkResumedSession and connection.resumed:
            return

        if self.x509Fingerprint:
            if connection._client:
                chain = connection.session.serverCertChain
            else:
                chain = connection.session.clientCertChain

            if self.x509Fingerprint:
                if isinstance(chain, X509CertChain):
                    if self.x509Fingerprint:
                        if chain.getFingerprint() != self.x509Fingerprint:
                            raise TLSFingerprintError(\
                                "X.509 fingerprint mismatch: %s, %s" % \
                                (chain.getFingerprint(), self.x509Fingerprint))
                elif chain:
                    raise TLSAuthenticationTypeError()
                else:
                    raise TLSNoAuthenticationError()
