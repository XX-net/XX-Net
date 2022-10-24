# Authors: 
#   Trevor Perrin
#   Dave Baggett (Arcode Corporation) - canonicalCipherName
#
# See the LICENSE file for legal information regarding use of this file.

"""Class representing a TLS session."""

from .utils.compat import *
from .mathtls import *
from .constants import *

class Session(object):
    """
    This class represents a TLS session.

    TLS distinguishes between connections and sessions.  A new
    handshake creates both a connection and a session.  Data is
    transmitted over the connection.

    The session contains a more permanent record of the handshake.  The
    session can be inspected to determine handshake results.  The
    session can also be used to create a new connection through
    "session resumption". If the client and server both support this,
    they can create a new connection based on an old session without
    the overhead of a full handshake.

    The session for a :py:class:`~tlslite.tlsconnection.TLSConnection` can be
    retrieved from the connection's 'session' attribute.

    :vartype srpUsername: str
    :ivar srpUsername: The client's SRP username (or None).

    :vartype clientCertChain: ~tlslite.x509certchain.X509CertChain
    :ivar clientCertChain: The client's certificate chain (or None).

    :vartype serverCertChain: ~tlslite.x509certchain.X509CertChain
    :ivar serverCertChain: The server's certificate chain (or None).

    :vartype tackExt: tack.structures.TackExtension.TackExtension
    :ivar tackExt: The server's TackExtension (or None).

    :vartype tackInHelloExt: bool
    :ivar tackInHelloExt: True if a TACK was presented via TLS Extension.

    :vartype ~.encryptThenMAC: bool
    :ivar ~.encryptThenMAC: True if connection uses CBC cipher in
        encrypt-then-MAC mode

    :vartype appProto: bytearray
    :ivar appProto: name of the negotiated application level protocol, None
        if not negotiated

    :vartype cl_app_secret: bytearray
    :ivar cl_app_secret: key used for deriving keys used by client to encrypt
        and protect data in TLS 1.3

    :vartype sr_app_secret: bytearray
    :ivar sr_app_secret: key used for deriving keys used by server to encrypt
        and protect data in TLS 1.3

    :vartype exporterMasterSecret: bytearray
    :ivar exporterMasterSecret: master secret used for TLS Exporter in TLS1.3

    :vartype resumptionMasterSecret: bytearray
    :ivar resumptionMasterSecret: master secret used for session resumption in
        TLS 1.3

    :vartype tickets: list
    :ivar tickets: list of tickets received from the server
    """

    def __init__(self):
        self.masterSecret = bytearray(0)
        self.sessionID = bytearray(0)
        self.cipherSuite = 0
        self.srpUsername = ""
        self.clientCertChain = None
        self.serverCertChain = None
        self.tackExt = None
        self.tackInHelloExt = False
        self.serverName = ""
        self.resumable = False
        self.encryptThenMAC = False
        self.extendedMasterSecret = False
        self.appProto = bytearray(0)
        self.cl_app_secret = bytearray(0)
        self.sr_app_secret = bytearray(0)
        self.exporterMasterSecret = bytearray(0)
        self.resumptionMasterSecret = bytearray(0)
        self.tickets = None

    def create(self, masterSecret, sessionID, cipherSuite,
               srpUsername, clientCertChain, serverCertChain,
               tackExt, tackInHelloExt, serverName, resumable=True,
               encryptThenMAC=False, extendedMasterSecret=False,
               appProto=bytearray(0), cl_app_secret=bytearray(0),
               sr_app_secret=bytearray(0), exporterMasterSecret=bytearray(0),
               resumptionMasterSecret=bytearray(0), tickets=None):
        self.masterSecret = masterSecret
        self.sessionID = sessionID
        self.cipherSuite = cipherSuite
        self.srpUsername = srpUsername
        self.clientCertChain = clientCertChain
        self.serverCertChain = serverCertChain
        self.tackExt = tackExt
        self.tackInHelloExt = tackInHelloExt  
        self.serverName = serverName
        self.resumable = resumable
        self.encryptThenMAC = encryptThenMAC
        self.extendedMasterSecret = extendedMasterSecret
        self.appProto = appProto
        self.cl_app_secret = cl_app_secret
        self.sr_app_secret = sr_app_secret
        self.exporterMasterSecret = exporterMasterSecret
        self.resumptionMasterSecret = resumptionMasterSecret
        # NOTE we need a reference copy not a copy of object here!
        self.tickets = tickets

    def _clone(self):
        other = Session()
        other.masterSecret = self.masterSecret
        other.sessionID = self.sessionID
        other.cipherSuite = self.cipherSuite
        other.srpUsername = self.srpUsername
        other.clientCertChain = self.clientCertChain
        other.serverCertChain = self.serverCertChain
        other.tackExt = self.tackExt
        other.tackInHelloExt = self.tackInHelloExt
        other.serverName = self.serverName
        other.resumable = self.resumable
        other.encryptThenMAC = self.encryptThenMAC
        other.extendedMasterSecret = self.extendedMasterSecret
        other.appProto = self.appProto
        other.cl_app_secret = self.cl_app_secret
        other.sr_app_secret = self.sr_app_secret
        other.exporterMasterSecret = self.exporterMasterSecret
        other.resumptionMasterSecret = self.resumptionMasterSecret
        other.tickets = self.tickets
        return other

    def valid(self):
        """If this session can be used for session resumption.

        :rtype: bool
        :returns: If this session can be used for session resumption.
        """
        # TODO add checks for tickets received from server (freshness etc.)
        return self.resumable and (self.sessionID or self.tickets)

    def _setResumable(self, boolean):
        #Only let it be set to True if the sessionID is non-null
        if (not boolean) or (boolean and self.sessionID):
            self.resumable = boolean

    def getTackId(self):
        if self.tackExt and self.tackExt.tack:
            return self.tackExt.tack.getTackId()
        else:
            return None
        
    def getBreakSigs(self):
        if self.tackExt and self.tackExt.break_sigs:
            return self.tackExt.break_sigs
        else:
            return None

    def getCipherName(self):
        """Get the name of the cipher used with this connection.

        :rtype: str
        :returns: The name of the cipher used with this connection.
        """
        return CipherSuite.canonicalCipherName(self.cipherSuite)
        
    def getMacName(self):
        """Get the name of the HMAC hash algo used with this connection.

        :rtype: str
        :returns: The name of the HMAC hash algo used with this connection.
        """
        return CipherSuite.canonicalMacName(self.cipherSuite)
