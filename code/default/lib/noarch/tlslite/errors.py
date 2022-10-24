# Authors: 
#   Trevor Perrin
#   Dave Baggett (Arcode Corporation) - Added TLSUnsupportedError.
#
# See the LICENSE file for legal information regarding use of this file.

"""Exception classes."""
import socket

from .constants import AlertDescription, AlertLevel

class BaseTLSException(Exception):
    """
    Metaclass for TLS Lite exceptions.

    Look to :py:class:`tlslite.errors.TLSError` for exceptions that should be
    caught by tlslite
    consumers
    """

    pass


class EncryptionError(BaseTLSException):
    """Base class for exceptions thrown while encrypting."""

    pass


class TLSError(BaseTLSException):
    """Base class for all TLS Lite exceptions."""

    def __str__(self):
        """At least print out the Exception time for str(...)."""
        return repr(self)


class TLSClosedConnectionError(TLSError, socket.error):
    """An attempt was made to use the connection after it was closed."""

    pass


class TLSAbruptCloseError(TLSError):
    """The socket was closed without a proper TLS shutdown.

    The TLS specification mandates that an alert of some sort
    must be sent before the underlying socket is closed.  If the socket
    is closed without this, it could signify that an attacker is trying
    to truncate the connection.  It could also signify a misbehaving
    TLS implementation, or a random network failure.
    """

    pass


class TLSAlert(TLSError):
    """A TLS alert has been signalled."""

    pass


class TLSLocalAlert(TLSAlert):
    """A TLS alert has been signalled by the local implementation.

    :vartype description: int
    :ivar description: Set to one of the constants in
        :py:class:`tlslite.constants.AlertDescription`

    :vartype level: int
    :ivar level: Set to one of the constants in
        :py:class:`tlslite.constants.AlertLevel`

    :vartype message: str
    :ivar message: Description of what went wrong.
    """

    def __init__(self, alert, message=None):
        self.description = alert.description
        self.level = alert.level
        self.message = message

    def __str__(self):
        alertStr = AlertDescription.toStr(self.description)
        if self.message:
            return alertStr + ": " + self.message
        else:
            return alertStr


class TLSRemoteAlert(TLSAlert):
    """
    A TLS alert has been signalled by the remote implementation.

    :vartype description: int
    :ivar description: Set to one of the constants in
        :py:class:`tlslite.constants.AlertDescription`

    :vartype level: int
    :ivar level: Set to one of the constants in
        :py:class:`tlslite.constants.AlertLevel`
    """

    def __init__(self, alert):
        self.description = alert.description
        self.level = alert.level

    def __str__(self):
        alertStr = AlertDescription.toStr(self.description)
        return alertStr


class TLSAuthenticationError(TLSError):
    """
    The handshake succeeded, but the other party's authentication
    was inadequate.

    This exception will only be raised when a
    :py:class:`tlslite.Checker.Checker` has been passed to a handshake
    function.
    The Checker will be invoked once the handshake completes, and if
    the Checker objects to how the other party authenticated, a
    subclass of this exception will be raised.
    """

    pass


class TLSNoAuthenticationError(TLSAuthenticationError):
    """The Checker was expecting the other party to authenticate with a
    certificate chain, but this did not occur."""

    pass


class TLSAuthenticationTypeError(TLSAuthenticationError):
    """The Checker was expecting the other party to authenticate with a
    different type of certificate chain."""

    pass


class TLSFingerprintError(TLSAuthenticationError):
    """The Checker was expecting the other party to authenticate with a
    certificate chain that matches a different fingerprint."""

    pass


class TLSAuthorizationError(TLSAuthenticationError):
    """The Checker was expecting the other party to authenticate with a
    certificate chain that has a different authorization."""

    pass


class TLSValidationError(TLSAuthenticationError):
    """The Checker has determined that the other party's certificate
    chain is invalid."""

    def __init__(self, msg, info=None):
        # Include a dict containing info about this validation failure
        TLSAuthenticationError.__init__(self, msg)
        self.info = info


class TLSFaultError(TLSError):
    """The other party responded incorrectly to an induced fault.

    This exception will only occur during fault testing, when a
    :py:class:`tlslite.tlsconnection.TLSConnection`'s fault variable is
    set to induce some sort of
    faulty behavior, and the other party doesn't respond appropriately.
    """

    pass


class TLSUnsupportedError(TLSError):
    """The implementation doesn't support the requested (or required)
    capabilities."""

    pass


class TLSInternalError(TLSError):
    """The internal state of object is unexpected or invalid.

    Caused by incorrect use of API.
    """

    pass


class TLSProtocolException(BaseTLSException):
    """Exceptions used internally for handling errors in received messages"""

    pass


class TLSIllegalParameterException(TLSProtocolException):
    """Parameters specified in message were incorrect or invalid"""

    pass


class TLSDecodeError(TLSProtocolException):
    """The received message encoding does not match specification."""

    pass


class TLSUnexpectedMessage(TLSProtocolException):
    """
    The received message was unexpected or parsing of Inner Plaintext
    failed
    """

    pass


class TLSRecordOverflow(TLSProtocolException):
    """The received record size was too big"""

    pass


class TLSDecryptionFailed(TLSProtocolException):
    """Decryption of data was unsuccessful"""

    pass


class TLSBadRecordMAC(TLSProtocolException):
    """Bad MAC (or padding in case of mac-then-encrypt)"""

    pass


class TLSInsufficientSecurity(TLSProtocolException):
    """Parameters selected by user are too weak"""

    pass


class TLSUnknownPSKIdentity(TLSProtocolException):
    """The PSK or SRP identity is unknown"""

    pass


class TLSHandshakeFailure(TLSProtocolException):
    """Could not find acceptable set of handshake parameters"""

    pass


class MaskTooLongError(EncryptionError):
    """The maskLen passed into function is too high"""

    pass


class MessageTooLongError(EncryptionError):
    """The message passed into function is too long"""

    pass


class EncodingError(EncryptionError):
    """An error appeared while encoding"""

    pass


class InvalidSignature(EncryptionError):
    """Verification function found invalid signature"""

    pass


class UnknownRSAType(EncryptionError):
    """Unknown RSA algorithm type passed"""

    pass
