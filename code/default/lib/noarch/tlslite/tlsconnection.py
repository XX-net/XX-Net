# Authors:
#   Trevor Perrin
#   Google - added reqCAs parameter
#   Google (adapted by Sam Rushing and Marcelo Fernandez) - NPN support
#   Google - FALLBACK_SCSV
#   Dimitris Moraitis - Anon ciphersuites
#   Martin von Loewis - python 3 port
#   Yngve Pettersen (ported by Paul Sokolovsky) - TLS 1.2
#   Hubert Kario - complete refactoring of key exchange methods, addition
#          of ECDH support
#
# See the LICENSE file for legal information regarding use of this file.

"""
MAIN CLASS FOR TLS LITE (START HERE!).
"""

from __future__ import division

import random
import time
import socket
from itertools import chain
from .utils.compat import formatExceptionTrace
from .tlsrecordlayer import TLSRecordLayer
from .session import Session
from .constants import *
from .utils.cryptomath import derive_secret, getRandomBytes, HKDF_expand_label
from .utils.dns_utils import is_valid_hostname
from .utils.lists import getFirstMatching
from .errors import *
from .messages import *
from .mathtls import *
from .handshakesettings import HandshakeSettings, KNOWN_VERSIONS, CURVE_ALIASES
from .handshakehashes import HandshakeHashes
from .utils.tackwrapper import *
from .utils.deprecations import deprecated_params
from .keyexchange import KeyExchange, RSAKeyExchange, DHE_RSAKeyExchange, \
        ECDHE_RSAKeyExchange, SRPKeyExchange, ADHKeyExchange, \
        AECDHKeyExchange, FFDHKeyExchange, ECDHKeyExchange
from .handshakehelpers import HandshakeHelpers
from .utils.cipherfactory import createAESCCM, createAESCCM_8, \
        createAESGCM, createCHACHA20

class TLSConnection(TLSRecordLayer):
    """
    This class wraps a socket and provides TLS handshaking and data transfer.

    To use this class, create a new instance, passing a connected
    socket into the constructor.  Then call some handshake function.
    If the handshake completes without raising an exception, then a TLS
    connection has been negotiated.  You can transfer data over this
    connection as if it were a socket.

    This class provides both synchronous and asynchronous versions of
    its key functions.  The synchronous versions should be used when
    writing single-or multi-threaded code using blocking sockets.  The
    asynchronous versions should be used when performing asynchronous,
    event-based I/O with non-blocking sockets.

    Asynchronous I/O is a complicated subject; typically, you should
    not use the asynchronous functions directly, but should use some
    framework like asyncore or Twisted which TLS Lite integrates with
    (see
    :py:class:`~.integration.tlsasyncdispatchermixin.TLSAsyncDispatcherMixIn`).
    """

    def __init__(self, sock):
        """Create a new TLSConnection instance.

        :param sock: The socket data will be transmitted on.  The
            socket should already be connected.  It may be in blocking or
            non-blocking mode.

        :type sock: socket.socket
        """
        TLSRecordLayer.__init__(self, sock)
        self.serverSigAlg = None
        self.ecdhCurve = None
        self.dhGroupSize = None
        self.extendedMasterSecret = False
        self._clientRandom = bytearray(0)
        self._serverRandom = bytearray(0)
        self.next_proto = None
        # whether the CCS was already sent in the connection (for hello retry)
        self._ccs_sent = False
        # if and how big is the limit on records peer is willing to accept
        # used only for TLS 1.2 and earlier
        self._peer_record_size_limit = None
        self._pha_supported = False

    def keyingMaterialExporter(self, label, length=20):
        """Return keying material as described in RFC 5705

        :type label: bytearray
        :param label: label to be provided for the exporter

        :type length: int
        :param length: number of bytes of the keying material to export
        """
        if label in (b'server finished', b'client finished',
                     b'master secret', b'key expansion'):
            raise ValueError("Forbidden label value")
        if self.version < (3, 1):
            raise ValueError("Supported only in TLSv1.0 and later")
        elif self.version < (3, 3):
            return PRF(self.session.masterSecret, label,
                       self._clientRandom + self._serverRandom,
                       length)
        elif self.version == (3, 3):
            if self.session.cipherSuite in CipherSuite.sha384PrfSuites:
                return PRF_1_2_SHA384(self.session.masterSecret, label,
                                      self._clientRandom + self._serverRandom,
                                      length)
            else:
                return PRF_1_2(self.session.masterSecret, label,
                               self._clientRandom + self._serverRandom,
                               length)
        elif self.version == (3, 4):
            prf = 'sha256'
            if self.session.cipherSuite in CipherSuite.sha384PrfSuites:
                prf = 'sha384'
            secret = derive_secret(self.session.exporterMasterSecret, label,
                                   None, prf)
            ctxhash = secureHash(bytearray(b''), prf)
            return HKDF_expand_label(secret, b"exporter", ctxhash, length, prf)
        else:
            raise AssertionError("Unknown protocol version")

    #*********************************************************
    # Client Handshake Functions
    #*********************************************************

    @deprecated_params({"async_": "async"},
                       "'{old_name}' is a keyword in Python 3.7, use"
                       "'{new_name}'")
    def handshakeClientAnonymous(self, session=None, settings=None,
                                 checker=None, serverName=None,
                                 async_=False):
        """Perform an anonymous handshake in the role of client.

        This function performs an SSL or TLS handshake using an
        anonymous Diffie Hellman ciphersuite.

        Like any handshake function, this can be called on a closed
        TLS connection, or on a TLS connection that is already open.
        If called on an open connection it performs a re-handshake.

        If the function completes without raising an exception, the
        TLS connection will be open and available for data transfer.

        If an exception is raised, the connection will have been
        automatically closed (if it was ever open).

        :type session: ~tlslite.session.Session
        :param session: A TLS session to attempt to resume.  If the
            resumption does not succeed, a full handshake will be
            performed.

        :type settings: ~tlslite.handshakesettings.HandshakeSettings
        :param settings: Various settings which can be used to control
            the ciphersuites, certificate types, and SSL/TLS versions
            offered by the client.

        :type checker: ~tlslite.checker.Checker
        :param checker: A Checker instance.  This instance will be
            invoked to examine the other party's authentication
            credentials, if the handshake completes succesfully.

        :type serverName: string
        :param serverName: The ServerNameIndication TLS Extension.

        :type async_: bool
        :param async_: If False, this function will block until the
            handshake is completed.  If True, this function will return a
            generator.  Successive invocations of the generator will
            return 0 if it is waiting to read from the socket, 1 if it is
            waiting to write to the socket, or will raise StopIteration if
            the handshake operation is completed.

        :rtype: None or an iterable
        :returns: If 'async_' is True, a generator object will be
            returned.

        :raises socket.error: If a socket error occurs.
        :raises tlslite.errors.TLSAbruptCloseError: If the socket is closed
            without a preceding alert.
        :raises tlslite.errors.TLSAlert: If a TLS alert is signalled.
        :raises tlslite.errors.TLSAuthenticationError: If the checker
            doesn't like the other party's authentication credentials.
        """
        handshaker = self._handshakeClientAsync(anonParams=(True),
                                                session=session,
                                                settings=settings,
                                                checker=checker,
                                                serverName=serverName)
        if async_:
            return handshaker
        for result in handshaker:
            pass

    @deprecated_params({"async_": "async"},
                       "'{old_name}' is a keyword in Python 3.7, use"
                       "'{new_name}'")
    def handshakeClientSRP(self, username, password, session=None,
                           settings=None, checker=None,
                           reqTack=True, serverName=None,
                           async_=False):
        """Perform an SRP handshake in the role of client.

        This function performs a TLS/SRP handshake.  SRP mutually
        authenticates both parties to each other using only a
        username and password.  This function may also perform a
        combined SRP and server-certificate handshake, if the server
        chooses to authenticate itself with a certificate chain in
        addition to doing SRP.

        If the function completes without raising an exception, the
        TLS connection will be open and available for data transfer.

        If an exception is raised, the connection will have been
        automatically closed (if it was ever open).

        :type username: bytearray
        :param username: The SRP username.

        :type password: bytearray
        :param password: The SRP password.

        :type session: ~tlslite.session.Session
        :param session: A TLS session to attempt to resume.  This
            session must be an SRP session performed with the same username
            and password as were passed in.  If the resumption does not
            succeed, a full SRP handshake will be performed.

        :type settings: ~tlslite.handshakesettings.HandshakeSettings
        :param settings: Various settings which can be used to control
            the ciphersuites, certificate types, and SSL/TLS versions
            offered by the client.

        :type checker: ~tlslite.checker.Checker
        :param checker: A Checker instance.  This instance will be
            invoked to examine the other party's authentication
            credentials, if the handshake completes succesfully.

        :type reqTack: bool
        :param reqTack: Whether or not to send a "tack" TLS Extension,
            requesting the server return a TackExtension if it has one.

        :type serverName: string
        :param serverName: The ServerNameIndication TLS Extension.

        :type async_: bool
        :param async_: If False, this function will block until the
            handshake is completed.  If True, this function will return a
            generator.  Successive invocations of the generator will
            return 0 if it is waiting to read from the socket, 1 if it is
            waiting to write to the socket, or will raise StopIteration if
            the handshake operation is completed.

        :rtype: None or an iterable
        :returns: If 'async_' is True, a generator object will be
            returned.

        :raises socket.error: If a socket error occurs.
        :raises tlslite.errors.TLSAbruptCloseError: If the socket is closed
            without a preceding alert.
        :raises tlslite.errors.TLSAlert: If a TLS alert is signalled.
        :raises tlslite.errors.TLSAuthenticationError: If the checker
            doesn't like the other party's authentication credentials.
        """
        # TODO add deprecation warning
        if isinstance(username, str):
            username = bytearray(username, 'utf-8')
        if isinstance(password, str):
            password = bytearray(password, 'utf-8')
        handshaker = self._handshakeClientAsync(srpParams=(username, password),
                        session=session, settings=settings, checker=checker,
                        reqTack=reqTack, serverName=serverName)
        # The handshaker is a Python Generator which executes the handshake.
        # It allows the handshake to be run in a "piecewise", asynchronous
        # fashion, returning 1 when it is waiting to able to write, 0 when
        # it is waiting to read.
        #
        # If 'async_' is True, the generator is returned to the caller,
        # otherwise it is executed to completion here.
        if async_:
            return handshaker
        for result in handshaker:
            pass

    @deprecated_params({"async_": "async"},
                       "'{old_name}' is a keyword in Python 3.7, use"
                       "'{new_name}'")
    def handshakeClientCert(self, certChain=None, privateKey=None,
                            session=None, settings=None, checker=None,
                            nextProtos=None, reqTack=True, serverName=None,
                            async_=False, alpn=None):
        """Perform a certificate-based handshake in the role of client.

        This function performs an SSL or TLS handshake.  The server
        will authenticate itself using an X.509 certificate
        chain.  If the handshake succeeds, the server's certificate
        chain will be stored in the session's serverCertChain attribute.
        Unless a checker object is passed in, this function does no
        validation or checking of the server's certificate chain.

        If the server requests client authentication, the
        client will send the passed-in certificate chain, and use the
        passed-in private key to authenticate itself.  If no
        certificate chain and private key were passed in, the client
        will attempt to proceed without client authentication.  The
        server may or may not allow this.

        If the function completes without raising an exception, the
        TLS connection will be open and available for data transfer.

        If an exception is raised, the connection will have been
        automatically closed (if it was ever open).

        :type certChain: ~tlslite.x509certchain.X509CertChain
        :param certChain: The certificate chain to be used if the
            server requests client authentication.

        :type privateKey: ~tlslite.utils.rsakey.RSAKey
        :param privateKey: The private key to be used if the server
            requests client authentication.

        :type session: ~tlslite.session.Session
        :param session: A TLS session to attempt to resume.  If the
            resumption does not succeed, a full handshake will be
            performed.

        :type settings: ~tlslite.handshakesettings.HandshakeSettings
        :param settings: Various settings which can be used to control
            the ciphersuites, certificate types, and SSL/TLS versions
            offered by the client.

        :type checker: ~tlslite.checker.Checker
        :param checker: A Checker instance.  This instance will be
            invoked to examine the other party's authentication
            credentials, if the handshake completes succesfully.

        :type nextProtos: list of str
        :param nextProtos: A list of upper layer protocols ordered by
            preference, to use in the Next-Protocol Negotiation Extension.

        :type reqTack: bool
        :param reqTack: Whether or not to send a "tack" TLS Extension,
            requesting the server return a TackExtension if it has one.

        :type serverName: string
        :param serverName: The ServerNameIndication TLS Extension.

        :type async_: bool
        :param async_: If False, this function will block until the
            handshake is completed.  If True, this function will return a
            generator.  Successive invocations of the generator will
            return 0 if it is waiting to read from the socket, 1 if it is
            waiting to write to the socket, or will raise StopIteration if
            the handshake operation is completed.

        :type alpn: list of bytearrays
        :param alpn: protocol names to advertise to server as supported by
            client in the Application Layer Protocol Negotiation extension.
            Example items in the array include b'http/1.1' or b'h2'.

        :rtype: None or an iterable
        :returns: If 'async_' is True, a generator object will be
            returned.

        :raises socket.error: If a socket error occurs.
        :raises tlslite.errors.TLSAbruptCloseError: If the socket is closed
            without a preceding alert.
        :raises tlslite.errors.TLSAlert: If a TLS alert is signalled.
        :raises tlslite.errors.TLSAuthenticationError: If the checker
            doesn't like the other party's authentication credentials.
        """
        handshaker = \
                self._handshakeClientAsync(certParams=(certChain, privateKey),
                                           session=session, settings=settings,
                                           checker=checker,
                                           serverName=serverName,
                                           nextProtos=nextProtos,
                                           reqTack=reqTack,
                                           alpn=alpn)
        # The handshaker is a Python Generator which executes the handshake.
        # It allows the handshake to be run in a "piecewise", asynchronous
        # fashion, returning 1 when it is waiting to able to write, 0 when
        # it is waiting to read.
        #
        # If 'async_' is True, the generator is returned to the caller,
        # otherwise it is executed to completion here.
        if async_:
            return handshaker
        for result in handshaker:
            pass


    def _handshakeClientAsync(self, srpParams=(), certParams=(), anonParams=(),
                              session=None, settings=None, checker=None,
                              nextProtos=None, serverName=None, reqTack=True,
                              alpn=None):

        handshaker = self._handshakeClientAsyncHelper(srpParams=srpParams,
                certParams=certParams,
                anonParams=anonParams,
                session=session,
                settings=settings,
                serverName=serverName,
                nextProtos=nextProtos,
                reqTack=reqTack,
                alpn=alpn)
        for result in self._handshakeWrapperAsync(handshaker, checker):
            yield result


    def _handshakeClientAsyncHelper(self, srpParams, certParams, anonParams,
                               session, settings, serverName, nextProtos,
                               reqTack, alpn):

        self._handshakeStart(client=True)

        #Unpack parameters
        srpUsername = None      # srpParams[0]
        password = None         # srpParams[1]
        clientCertChain = None  # certParams[0]
        privateKey = None       # certParams[1]

        # Allow only one of (srpParams, certParams, anonParams)
        if srpParams:
            assert(not certParams)
            assert(not anonParams)
            srpUsername, password = srpParams
        if certParams:
            assert(not srpParams)
            assert(not anonParams)
            clientCertChain, privateKey = certParams
        if anonParams:
            assert(not srpParams)
            assert(not certParams)

        #Validate parameters
        if srpUsername and not password:
            raise ValueError("Caller passed a username but no password")
        if password and not srpUsername:
            raise ValueError("Caller passed a password but no username")
        if clientCertChain and not privateKey:
            raise ValueError("Caller passed a cert_chain but no privateKey")
        if privateKey and not clientCertChain:
            raise ValueError("Caller passed a privateKey but no cert_chain")
        if reqTack:
            if not tackpyLoaded:
                reqTack = False
            if not settings or not settings.useExperimentalTackExtension:
                reqTack = False
        if nextProtos is not None:
            if len(nextProtos) == 0:
                raise ValueError("Caller passed no nextProtos")
        if alpn is not None and not alpn:
            raise ValueError("Caller passed empty alpn list")
        # reject invalid hostnames but accept empty/None ones
        if serverName and not is_valid_hostname(serverName):
            raise ValueError("Caller provided invalid server host name: {0}"
                             .format(serverName))

        # Validates the settings and filters out any unsupported ciphers
        # or crypto libraries that were requested
        if not settings:
            settings = HandshakeSettings()
        settings = settings.validate()
        self.sock.padding_cb = settings.padding_cb

        if clientCertChain:
            if not isinstance(clientCertChain, X509CertChain):
                raise ValueError("Unrecognized certificate type")
            if "x509" not in settings.certificateTypes:
                raise ValueError("Client certificate doesn't match "\
                                 "Handshake Settings")

        if session:
            # session.valid() ensures session is resumable and has
            # non-empty sessionID
            if not session.valid():
                session = None #ignore non-resumable sessions...
            elif session.resumable:
                if session.srpUsername != srpUsername:
                    raise ValueError("Session username doesn't match")
                if session.serverName != serverName:
                    raise ValueError("Session servername doesn't match")

        #Add Faults to parameters
        if srpUsername and self.fault == Fault.badUsername:
            srpUsername += bytearray(b"GARBAGE")
        if password and self.fault == Fault.badPassword:
            password += bytearray(b"GARBAGE")

        # Tentatively set the client's record version.
        # We'll use this for the ClientHello, and if an error occurs
        # parsing the Server Hello, we'll use this version for the response
        # in TLS 1.3 it always needs to be set to TLS 1.0
        self.version = \
            (3, 1) if settings.maxVersion > (3, 3) else settings.maxVersion

        # OK Start sending messages!
        # *****************************

        # Send the ClientHello.
        for result in self._clientSendClientHello(settings, session,
                                        srpUsername, srpParams, certParams,
                                        anonParams, serverName, nextProtos,
                                        reqTack, alpn):
            if result in (0,1): yield result
            else: break
        clientHello = result

        #Get the ServerHello.
        for result in self._clientGetServerHello(settings, session,
                                                 clientHello):
            if result in (0,1): yield result
            else: break
        serverHello = result
        cipherSuite = serverHello.cipher_suite

        # Check the serverHello.random  if it includes the downgrade protection
        # values as described in RFC8446 section 4.1.3

        # For TLS1.3
        if (settings.maxVersion > (3, 3) and self.version <= (3, 3)) and \
                (serverHello.random[-8:] == TLS_1_2_DOWNGRADE_SENTINEL or
                 serverHello.random[-8:] == TLS_1_1_DOWNGRADE_SENTINEL):
            for result in self._sendError(AlertDescription.illegal_parameter,
                                          "Connection terminated because "
                                          "of downgrade protection."):
                yield result

        # For TLS1.2
        if settings.maxVersion == (3, 3) and self.version < (3, 3) and \
                serverHello.random[-8:] == TLS_1_1_DOWNGRADE_SENTINEL:
            for result in self._sendError(AlertDescription.illegal_parameter,
                                          "Connection terminated because "
                                          "of downgrade protection."):
                yield result

        # if we're doing tls1.3, use the new code as the negotiation is much
        # different
        ext = serverHello.getExtension(ExtensionType.supported_versions)
        if ext and ext.version > (3, 3):
            for result in self._clientTLS13Handshake(settings, session,
                                                     clientHello,
                                                     clientCertChain,
                                                     privateKey,
                                                     serverHello):
                if result in (0, 1):
                    yield result
                else:
                    break
            if result in ["finished", "resumed_and_finished"]:
                self._handshakeDone(resumed=(result == "resumed_and_finished"))
                self._serverRandom = serverHello.random
                self._clientRandom = clientHello.random
                return
            else:
                raise Exception("unexpected return")

        # Choose a matching Next Protocol from server list against ours
        # (string or None)
        nextProto = self._clientSelectNextProto(nextProtos, serverHello)

        # Check if server selected encrypt-then-MAC
        if serverHello.getExtension(ExtensionType.encrypt_then_mac):
            self._recordLayer.encryptThenMAC = True

        if serverHello.getExtension(ExtensionType.extended_master_secret):
            self.extendedMasterSecret = True

        #If the server elected to resume the session, it is handled here.
        for result in self._clientResume(session, serverHello,
                        clientHello.random,
                        settings.cipherImplementations,
                        nextProto, settings):
            if result in (0,1): yield result
            else: break
        if result == "resumed_and_finished":
            self._handshakeDone(resumed=True)
            self._serverRandom = serverHello.random
            self._clientRandom = clientHello.random
            # alpn protocol is independent of resumption and renegotiation
            # and needs to be negotiated every time
            alpnExt = serverHello.getExtension(ExtensionType.alpn)
            if alpnExt:
                session.appProto = alpnExt.protocol_names[0]
            return

        #If the server selected an SRP ciphersuite, the client finishes
        #reading the post-ServerHello messages, then derives a
        #premasterSecret and sends a corresponding ClientKeyExchange.
        if cipherSuite in CipherSuite.srpAllSuites:
            keyExchange = SRPKeyExchange(cipherSuite, clientHello,
                                         serverHello, None, None,
                                         srpUsername=srpUsername,
                                         password=password,
                                         settings=settings)

        #If the server selected an anonymous ciphersuite, the client
        #finishes reading the post-ServerHello messages.
        elif cipherSuite in CipherSuite.dhAllSuites:
            keyExchange = DHE_RSAKeyExchange(cipherSuite, clientHello,
                                             serverHello, None)

        elif cipherSuite in CipherSuite.ecdhAllSuites:
            acceptedCurves = self._curveNamesToList(settings)
            keyExchange = ECDHE_RSAKeyExchange(cipherSuite, clientHello,
                                               serverHello, None,
                                               acceptedCurves)

        #If the server selected a certificate-based RSA ciphersuite,
        #the client finishes reading the post-ServerHello messages. If
        #a CertificateRequest message was sent, the client responds with
        #a Certificate message containing its certificate chain (if any),
        #and also produces a CertificateVerify message that signs the
        #ClientKeyExchange.
        else:
            keyExchange = RSAKeyExchange(cipherSuite, clientHello,
                                         serverHello, None)

        # we'll send few messages here, send them in single TCP packet
        self.sock.buffer_writes = True
        for result in self._clientKeyExchange(settings, cipherSuite,
                                              clientCertChain,
                                              privateKey,
                                              serverHello.certificate_type,
                                              serverHello.tackExt,
                                              clientHello.random,
                                              serverHello.random,
                                              keyExchange):
            if result in (0, 1):
                yield result
            else: break
        (premasterSecret, serverCertChain, clientCertChain,
         tackExt) = result

        #After having previously sent a ClientKeyExchange, the client now
        #initiates an exchange of Finished messages.
        # socket buffering is turned off in _clientFinished
        for result in self._clientFinished(premasterSecret,
                            clientHello.random,
                            serverHello.random,
                            cipherSuite, settings.cipherImplementations,
                            nextProto, settings):
                if result in (0,1): yield result
                else: break
        masterSecret = result

        # check if an application layer protocol was negotiated
        alpnProto = None
        alpnExt = serverHello.getExtension(ExtensionType.alpn)
        if alpnExt:
            alpnProto = alpnExt.protocol_names[0]

        # Create the session object which is used for resumptions
        self.session = Session()
        self.session.create(masterSecret, serverHello.session_id, cipherSuite,
                            srpUsername, clientCertChain, serverCertChain,
                            tackExt, (serverHello.tackExt is not None),
                            serverName,
                            encryptThenMAC=self._recordLayer.encryptThenMAC,
                            extendedMasterSecret=self.extendedMasterSecret,
                            appProto=alpnProto,
                            # NOTE it must be a reference not a copy
                            tickets=self.tickets)
        self._handshakeDone(resumed=False)
        self._serverRandom = serverHello.random
        self._clientRandom = clientHello.random

    @staticmethod
    def _get_GREASE_version():
        n = random.randint(1, 10)
        ns = n * 16 + 10
        value = (ns, ns)
        return value

    @staticmethod
    def _get_GREASE():
        values = [0x1a1a, 0x2a2a, 0x3a3a, 0x4a4a, 0x5a5a, 0x6a6a, 0x7a7a, 0x8a8a, 0x9a9a, 0xaaaa, 0xbaba]
        return random.choice(values)

    def _clientSendClientHello(self, settings, session, srpUsername,
                                srpParams, certParams, anonParams,
                                serverName, nextProtos, reqTack, alpn):
        #Initialize acceptable ciphersuites
        # cipherSuites = [CipherSuite.TLS_EMPTY_RENEGOTIATION_INFO_SCSV]
        # if srpParams:
        #     cipherSuites += CipherSuite.getSrpAllSuites(settings)
        # elif certParams:
        #     cipherSuites += CipherSuite.getTLS13Suites(settings)
        #     cipherSuites += CipherSuite.getEcdsaSuites(settings)
        #     cipherSuites += CipherSuite.getEcdheCertSuites(settings)
        #     cipherSuites += CipherSuite.getDheCertSuites(settings)
        #     cipherSuites += CipherSuite.getCertSuites(settings)
        #     cipherSuites += CipherSuite.getDheDsaSuites(settings)
        # elif anonParams:
        #     cipherSuites += CipherSuite.getEcdhAnonSuites(settings)
        #     cipherSuites += CipherSuite.getAnonSuites(settings)
        # else:
        #     assert False

        cipherSuites = [
            self._get_GREASE(),
            CipherSuite.TLS_AES_128_GCM_SHA256,  # 1301
            CipherSuite.TLS_AES_256_GCM_SHA384,  # 1302
            CipherSuite.TLS_CHACHA20_POLY1305_SHA256,  # 1303
            CipherSuite.TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,  # C02B
            CipherSuite.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,  # C02F
            CipherSuite.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,  # C02C
            CipherSuite.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,  # C030
            CipherSuite.TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256,  # cca9
            CipherSuite.TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256,  # cca8
            CipherSuite.TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA,  # c013
            CipherSuite.TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA,  # c014
            CipherSuite.TLS_RSA_WITH_AES_128_GCM_SHA256,  # 009c
            CipherSuite.TLS_RSA_WITH_AES_256_GCM_SHA384,  # 009d
            CipherSuite.TLS_RSA_WITH_AES_128_CBC_SHA,  # 002f
            CipherSuite.TLS_RSA_WITH_AES_256_CBC_SHA,  # 0035
        ]

        #Add any SCSVs. These are not real cipher suites, but signaling
        #values which reuse the cipher suite field in the ClientHello.
        wireCipherSuites = list(cipherSuites)
        if settings.sendFallbackSCSV:
            wireCipherSuites.append(CipherSuite.TLS_FALLBACK_SCSV)

        #Initialize acceptable certificate types
        certificateTypes = None  # settings.getCertificateTypes()

        extensions = []
        extensions.append(TLSExtension().\
                          create(self._get_GREASE(),
                                 bytearray(0)))

        if serverName:
            serverName = bytearray(serverName, "utf-8")
            sni_ext = SNIExtension().create(serverName)
            extensions.append(sni_ext)

        extensions.append(TLSExtension().create(ExtensionType.extended_master_secret, bytearray(0)))

        extensions.append(TLSExtension().create(ExtensionType.renegotiation_info, bytearray(1)))

        groups = [self._get_GREASE(), 0x001d, 0x0017, 0x0018]
        extensions.append(SupportedGroupsExtension().create(groups))

        extensions.append(ECPointFormatsExtension().create([ECPointFormat.uncompressed]))

        extensions.append(TLSExtension().create(ExtensionType.session_ticket, bytearray(0)))

        extensions.append(ALPNExtension().create(alpn))

        extensions.append(StatusRequestExtension().create())

        # In TLS1.2 advertise support for additional signature types
        # sigList = self._sigHashesToList(settings)
        # assert len(sigList) > 0
        sigList = [
            (4, 3),
            (8, 4),
            (4, 1),
            (5, 3),
            (8, 5),
            (5, 1),
            (8, 6),
            (6, 1),
        ]
        extensions.append(SignatureAlgorithmsExtension().create(sigList))

        extensions.append(TLSExtension().create(ExtensionType.signed_certificate_timestamp, bytearray(0)))

        shares = []
        grease_key_share = KeyShareEntry().create(self._get_GREASE(), bytearray(1))
        shares.append(grease_key_share)
        for group_name in ["x25519"]:
            group_id = getattr(GroupName, group_name)
            key_share = self._genKeyShareEntry(group_id, (3, 4))

            shares.append(key_share)
        # if TLS 1.3 is enabled, key_share must always be sent
        # (unless only static PSK is used)
        extensions.append(ClientKeyShareExtension().create(shares))

        # add info on types of PSKs supported (also used for
        # NewSessionTicket so send basically always)
        psk_modes = ["psk_dhe_ke",]
        ext = PskKeyExchangeModesExtension().create([getattr(PskKeyExchangeMode, i) for i in psk_modes])
        extensions.append(ext)

        versions = [self._get_GREASE_version(), (3, 4), (3, 3)]
        extensions.append(SupportedVersionsExtension().create(versions))

        algorithms = [
            (0, 2)  # brotli
        ]
        extensions.append(CompressCertificateExtension().create(algorithms))

        alpn = [bytearray(b"h2")]
        extensions.append(ApplicationSettingsExtension().create(alpn))

        GREASE_ID = self._get_GREASE()
        extensions.append(TLSExtension().create(GREASE_ID, bytearray(1)))

        # when TLS 1.3 advertised, add key shares, set fake session_id
        # shares = None
        session_id = getRandomBytes(32)

        # don't send empty list of extensions or extensions in SSLv3
        if not extensions or settings.maxVersion == (3, 0):
            extensions = None

        sent_version = min(settings.maxVersion, (3, 3))

        #Either send ClientHello (with a resumable session)...
        # if session and session.sessionID:
        #     #If it's resumable, then its
        #     #ciphersuite must be one of the acceptable ciphersuites
        #     if session.cipherSuite not in cipherSuites:
        #         raise ValueError("Session's cipher suite not consistent "\
        #                          "with parameters")
        #     else:
        #         clientHello = ClientHello()
        #         clientHello.create(sent_version, getRandomBytes(32),
        #                            session.sessionID, wireCipherSuites,
        #                            certificateTypes,
        #                            session.srpUsername,
        #                            reqTack, nextProtos is not None,
        #                            session.serverName,
        #                            extensions=extensions)
        #
        # #Or send ClientHello (without)
        # else:
        clientHello = ClientHello()
        clientHello.create(sent_version, getRandomBytes(32),
                           session_id, wireCipherSuites,
                           certificateTypes,
                           srpUsername,
                           reqTack, nextProtos is not None,
                           serverName,
                           extensions=extensions)

        # Check if padding extension should be added
        # we want to add extensions even when using just SSLv3
        if settings.usePaddingExtension:
            HandshakeHelpers.alignClientHelloPadding(clientHello)

        # because TLS 1.3 PSK is sent in ClientHello and signs the ClientHello
        # we need to send it as the last extension
        if (settings.pskConfigs or (session and session.tickets)) \
                and settings.maxVersion >= (3, 4):
            ext = PreSharedKeyExtension()
            idens = []
            binders = []
            # if we have a previous session, include it in PSKs too
            if session and session.tickets:
                now = time.time()
                # clean the list from obsolete ones
                # RFC says that the tickets MUST NOT be cached longer than
                # 7 days
                session.tickets[:] = (i for i in session.tickets if
                                      i.time + i.ticket_lifetime > now and
                                      i.time + 7 * 24 * 60 * 60 > now)
                if session.tickets:
                    ticket = session.tickets[0]

                    # ticket.time is in seconds while the obfuscated time
                    # is in ms
                    ticket_time = int(
                        time.time() * 1000 -
                        ticket.time * 1000 +
                        ticket.ticket_age_add) % 2**32
                    idens.append(PskIdentity().create(ticket.ticket,
                                                      ticket_time))
                    binder_len = 48 if session.cipherSuite in \
                        CipherSuite.sha384PrfSuites else 32
                    binders.append(bytearray(binder_len))
            for psk in settings.pskConfigs:
                # skip PSKs with no identities as they're TLS1.3 incompatible
                if not psk[0]:
                    continue
                idens.append(PskIdentity().create(psk[0], 0))
                psk_hash = psk[2] if len(psk) > 2 else 'sha256'
                assert psk_hash in set(['sha256', 'sha384'])
                # create fake binder values to create correct length fields
                binders.append(bytearray(32 if psk_hash == 'sha256' else 48))

            if idens:
                ext.create(idens, binders)
                clientHello.extensions.append(ext)

                # for HRR case we'll need 1st CH and HRR in handshake hashes,
                # so pass them in, truncated CH will be added by the helpers to
                # the copy of the hashes
                HandshakeHelpers.update_binders(clientHello,
                                                self._handshake_hash,
                                                settings.pskConfigs,
                                                session.tickets if session
                                                else None,
                                                session.resumptionMasterSecret
                                                if session else None)

        for result in self._sendMsg(clientHello):
            yield result
        yield clientHello

    def _clientGetServerHello(self, settings, session, clientHello):
        client_hello_hash = self._handshake_hash.copy()
        for result in self._getMsg(ContentType.handshake,
                                   HandshakeType.server_hello):
            if result in (0,1): yield result
            else: break

        hello_retry = None
        ext = result.getExtension(ExtensionType.supported_versions)
        if result.random == TLS_1_3_HRR and ext and ext.version > (3, 3):
            self.version = ext.version
            hello_retry = result

            # create synthetic handshake hash
            prf_name, prf_size = self._getPRFParams(hello_retry.cipher_suite)

            self._handshake_hash = HandshakeHashes()
            writer = Writer()
            writer.add(HandshakeType.message_hash, 1)
            writer.addVarSeq(client_hello_hash.digest(prf_name), 1, 3)
            self._handshake_hash.update(writer.bytes)
            self._handshake_hash.update(hello_retry.write())

            # check if all extensions in the HRR were present in client hello
            ch_ext_types = set(i.extType for i in clientHello.extensions)
            ch_ext_types.add(ExtensionType.cookie)

            bad_ext = next((i for i in hello_retry.extensions
                            if i.extType not in ch_ext_types), None)
            if bad_ext:
                bad_ext = ExtensionType.toStr(bad_ext)
                for result in self._sendError(AlertDescription
                                              .unsupported_extension,
                                              ("Unexpected extension in HRR: "
                                               "{0}").format(bad_ext)):
                    yield result

            # handle cookie extension
            cookie = hello_retry.getExtension(ExtensionType.cookie)
            if cookie:
                clientHello.addExtension(cookie)

            # handle key share extension
            sr_key_share_ext = hello_retry.getExtension(ExtensionType
                                                        .key_share)
            if sr_key_share_ext:
                group_id = sr_key_share_ext.selected_group
                # check if group selected by server is valid
                groups_ext = clientHello.getExtension(ExtensionType
                                                      .supported_groups)
                if group_id not in groups_ext.groups:
                    for result in self._sendError(AlertDescription
                                                  .illegal_parameter,
                                                  "Server selected group we "
                                                  "did not advertise"):
                        yield result

                cl_key_share_ext = clientHello.getExtension(ExtensionType
                                                            .key_share)
                # check if the server didn't ask for a group we already sent
                if next((entry for entry in cl_key_share_ext.client_shares
                         if entry.group == group_id), None):
                    for result in self._sendError(AlertDescription
                                                  .illegal_parameter,
                                                  "Server selected group we "
                                                  "did sent the key share "
                                                  "for"):
                        yield result

                key_share = self._genKeyShareEntry(group_id, (3, 4))

                # old key shares need to be removed
                cl_key_share_ext.client_shares = [key_share]

            if not cookie and not sr_key_share_ext:
                # HRR did not result in change to Client Hello
                for result in self._sendError(AlertDescription.
                                              illegal_parameter,
                                              "Received HRR did not cause "
                                              "update to Client Hello"):
                    yield result

            if clientHello.session_id != hello_retry.session_id:
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        "Received HRR session_id does not match the one in "
                        "ClientHello"):
                    yield result

            ext = clientHello.getExtension(ExtensionType.pre_shared_key)
            if ext:
                # move the extension to end (in case extension like cookie was
                # added
                clientHello.extensions.remove(ext)
                clientHello.extensions.append(ext)
                HandshakeHelpers.update_binders(clientHello,
                                                self._handshake_hash,
                                                settings.pskConfigs,
                                                session.tickets if session
                                                else None,
                                                session.resumptionMasterSecret
                                                if session else None)

            # resend the client hello with performed changes
            msgs = []
            if clientHello.session_id:
                ccs = ChangeCipherSpec().create()
                msgs.append(ccs)
            msgs.append(clientHello)
            for result in self._sendMsgs(msgs):
                yield result
            self._ccs_sent = True

            # retry getting server hello
            for result in self._getMsg(ContentType.handshake,
                                       HandshakeType.server_hello):
                if result in (0, 1):
                    yield result
                else:
                    break

        serverHello = result

        #Get the server version.  Do this before anything else, so any
        #error alerts will use the server's version
        real_version = serverHello.server_version
        if serverHello.server_version >= (3, 3):
            ext = serverHello.getExtension(ExtensionType.supported_versions)
            if ext:
                real_version = ext.version
        self.version = real_version

        #Check ServerHello
        if hello_retry and \
                hello_retry.cipher_suite != serverHello.cipher_suite:
            for result in self._sendError(AlertDescription.illegal_parameter,
                                          "server selected different cipher "
                                          "in HRR and Server Hello"):
                yield result
        if real_version < settings.minVersion:
            for result in self._sendError(
                    AlertDescription.protocol_version,
                    "Too old version: {0} (min: {1})"
                    .format(real_version, settings.minVersion)):
                yield result
        if real_version > settings.maxVersion and \
                real_version not in settings.versions:
            for result in self._sendError(
                    AlertDescription.protocol_version,
                    "Too new version: {0} (max: {1})"
                    .format(real_version, settings.maxVersion)):
                yield result
        if real_version > (3, 3) and \
                serverHello.session_id != clientHello.session_id:
            for result in self._sendError(
                    AlertDescription.illegal_parameter,
                    "Received ServerHello session_id does not match the one "
                    "in ClientHello"):
                yield result
        cipherSuites = CipherSuite.filterForVersion(clientHello.cipher_suites,
                                                    minVersion=real_version,
                                                    maxVersion=real_version)
        if serverHello.cipher_suite not in cipherSuites:
            for result in self._sendError(\
                AlertDescription.illegal_parameter,
                "Server responded with incorrect ciphersuite"):
                yield result
        if serverHello.certificate_type not in clientHello.certificate_types:
            for result in self._sendError(\
                AlertDescription.illegal_parameter,
                "Server responded with incorrect certificate type"):
                yield result
        if serverHello.compression_method != 0:
            for result in self._sendError(\
                AlertDescription.illegal_parameter,
                "Server responded with incorrect compression method"):
                yield result
        if serverHello.tackExt:            
            if not clientHello.tack:
                for result in self._sendError(\
                    AlertDescription.illegal_parameter,
                    "Server responded with unrequested Tack Extension"):
                    yield result
            if not serverHello.tackExt.verifySignatures():
                for result in self._sendError(\
                    AlertDescription.decrypt_error,
                    "TackExtension contains an invalid signature"):
                    yield result
        if serverHello.next_protos and not clientHello.supports_npn:
            for result in self._sendError(\
                AlertDescription.illegal_parameter,
                "Server responded with unrequested NPN Extension"):
                yield result
        if not serverHello.getExtension(ExtensionType.extended_master_secret)\
            and settings.requireExtendedMasterSecret:
            for result in self._sendError(
                    AlertDescription.insufficient_security,
                    "Negotiation of Extended master Secret failed"):
                yield result
        alpnExt = serverHello.getExtension(ExtensionType.alpn)
        if alpnExt:
            if not alpnExt.protocol_names or \
                    len(alpnExt.protocol_names) != 1:
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        "Server responded with invalid ALPN extension"):
                    yield result
            clntAlpnExt = clientHello.getExtension(ExtensionType.alpn)
            if not clntAlpnExt:
                for result in self._sendError(
                        AlertDescription.unsupported_extension,
                        "Server sent ALPN extension without one in "
                        "client hello"):
                    yield result
            if alpnExt.protocol_names[0] not in clntAlpnExt.protocol_names:
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        "Server selected ALPN protocol we did not advertise"):
                    yield result
        heartbeat_ext = serverHello.getExtension(ExtensionType.heartbeat)
        if heartbeat_ext:
            if not settings.use_heartbeat_extension:
                for result in self._sendError(
                        AlertDescription.unsupported_extension,
                        "Server sent Heartbeat extension without one in "
                        "client hello"):
                    yield result
            if heartbeat_ext.mode == HeartbeatMode.PEER_ALLOWED_TO_SEND and \
                    settings.heartbeat_response_callback:
                self.heartbeat_can_send = True
                self.heartbeat_response_callback = settings.\
                    heartbeat_response_callback
            elif heartbeat_ext.mode == HeartbeatMode.\
                    PEER_NOT_ALLOWED_TO_SEND or not settings.\
                    heartbeat_response_callback:
                self.heartbeat_can_send = False
            else:
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        "Server responded with invalid Heartbeat extension"):
                    yield result
            self.heartbeat_supported = True
        size_limit_ext = serverHello.getExtension(
            ExtensionType.record_size_limit)
        if size_limit_ext:
            if size_limit_ext.record_size_limit is None:
                for result in self._sendError(
                        AlertDescription.decode_error,
                        "Malformed record_size_limit extension"):
                    yield result
            # if we got the extension in ServerHello it means we're doing
            # TLS 1.2 so the max value for extension is 2^14
            if not 64 <= size_limit_ext.record_size_limit <= 2**14:
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        "Server responed with invalid value in "
                        "record_size_limit extension"):
                    yield result
            self._peer_record_size_limit = size_limit_ext.record_size_limit
        yield serverHello

    @staticmethod
    def _getKEX(group, version):
        """Get object for performing key exchange."""
        if group in GroupName.allFF:
            return FFDHKeyExchange(group, version)
        return ECDHKeyExchange(group, version)

    @classmethod
    def _genKeyShareEntry(cls, group, version):
        """Generate KeyShareEntry object from randomly selected private value.
        """
        kex = cls._getKEX(group, version)
        private = kex.get_random_private_key()
        share = kex.calc_public_value(private)
        return KeyShareEntry().create(group, share, private)

    @staticmethod
    def _getPRFParams(cipher_suite):
        """Return name of hash used for PRF and the hash output size."""
        if cipher_suite in CipherSuite.sha384PrfSuites:
            return 'sha384', 48
        return 'sha256', 32

    def _clientTLS13Handshake(self, settings, session, clientHello,
                              clientCertChain, privateKey, serverHello):
        """Perform TLS 1.3 handshake as a client."""
        prfName, prf_size = self._getPRFParams(serverHello.cipher_suite)

        # we have client and server hello in TLS 1.3 so we have the necessary
        # key shares to derive the handshake receive key
        sr_kex = serverHello.getExtension(ExtensionType.key_share)
        sr_psk = serverHello.getExtension(ExtensionType.pre_shared_key)
        if not sr_kex and not sr_psk:
            raise TLSIllegalParameterException("Server did not select PSK nor "
                                               "an (EC)DH group")
        if sr_kex:
            sr_kex = sr_kex.server_share
            self.ecdhCurve = sr_kex.group
            cl_key_share_ex = clientHello.getExtension(ExtensionType.key_share)
            cl_kex = next((i for i in cl_key_share_ex.client_shares
                           if i.group == sr_kex.group), None)
            if cl_kex is None:
                raise TLSIllegalParameterException("Server selected not "
                                                   "advertised group.")
            kex = self._getKEX(sr_kex.group, self.version)

            shared_sec = kex.calc_shared_key(cl_kex.private,
                                             sr_kex.key_exchange)
        else:
            shared_sec = bytearray(prf_size)

        # if server agreed to perform resumption, find the matching secret key
        resuming = False
        if sr_psk:
            clPSK = clientHello.getExtension(ExtensionType.pre_shared_key)
            ident = clPSK.identities[sr_psk.selected]
            psk = [i[1] for i in settings.pskConfigs if i[0] == ident.identity]
            if psk:
                psk = psk[0]
            else:
                resuming = True
                psk = HandshakeHelpers.calc_res_binder_psk(
                    ident, session.resumptionMasterSecret,
                    session.tickets)
        else:
            psk = bytearray(prf_size)

        secret = bytearray(prf_size)
        # Early Secret
        secret = secureHMAC(secret, psk, prfName)

        # Handshake Secret
        secret = derive_secret(secret, bytearray(b'derived'),
                               None, prfName)
        secret = secureHMAC(secret, shared_sec, prfName)

        sr_handshake_traffic_secret = derive_secret(secret,
                                                    bytearray(b's hs traffic'),
                                                    self._handshake_hash,
                                                    prfName)
        cl_handshake_traffic_secret = derive_secret(secret,
                                                    bytearray(b'c hs traffic'),
                                                    self._handshake_hash,
                                                    prfName)

        # prepare for reading encrypted messages
        self._recordLayer.calcTLS1_3PendingState(
            serverHello.cipher_suite,
            cl_handshake_traffic_secret,
            sr_handshake_traffic_secret,
            settings.cipherImplementations)

        self._changeReadState()

        for result in self._getMsg(ContentType.handshake,
                                   HandshakeType.encrypted_extensions):
            if result in (0, 1):
                yield result
            else:
                break
        encrypted_extensions = result
        assert isinstance(encrypted_extensions, EncryptedExtensions)

        size_limit_ext = encrypted_extensions.getExtension(
            ExtensionType.record_size_limit)
        if size_limit_ext and not settings.record_size_limit:
            for result in self._sendError(
                    AlertDescription.illegal_parameter,
                    "Server sent record_size_limit extension despite us not "
                    "advertising it"):
                yield result
        if size_limit_ext:
            if size_limit_ext.record_size_limit is None:
                for result in self._sendError(
                        AlertDescription.decode_error,
                        "Malformed record_size_limit extension"):
                    yield result
            if not 64 <= size_limit_ext.record_size_limit <= 2**14+1:
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        "Invalid valid in record_size_limit extension"):
                    yield result
            # the record layer code expects a limit that excludes content type
            # from the value while extension is defined including it
            self._send_record_limit = size_limit_ext.record_size_limit - 1
            self._recv_record_limit = min(2**14, settings.record_size_limit - 1)

        # if we negotiated PSK then Certificate is not sent
        certificate_request = None
        certificate = None
        if not sr_psk:
            for result in self._getMsg(ContentType.handshake,
                                       (HandshakeType.certificate_request,
                                        HandshakeType.certificate,
                                        HandshakeType.compressed_certificate),
                                       CertificateType.x509):
                if result in (0, 1):
                    yield result
                else:
                    break

            if isinstance(result, CertificateRequest):
                certificate_request = result

                # we got CertificateRequest so now we'll get Certificate
                for result in self._getMsg(ContentType.handshake,
                                           HandshakeType.certificate,
                                           CertificateType.x509):
                    if result in (0, 1):
                        yield result
                    else:
                        break

            certificate = result
            assert isinstance(certificate, Certificate)

            srv_cert_verify_hh = self._handshake_hash.copy()

            for result in self._getMsg(ContentType.handshake,
                                       HandshakeType.certificate_verify):
                if result in (0, 1):
                    yield result
                else:
                    break
            certificate_verify = result
            assert isinstance(certificate_verify, CertificateVerify)

            signature_scheme = certificate_verify.signatureAlgorithm
            self.serverSigAlg = signature_scheme

            signature_context = KeyExchange.calcVerifyBytes((3, 4),
                                                            srv_cert_verify_hh,
                                                            signature_scheme,
                                                            None, None, None,
                                                            prfName, b'server')

            for result in self._clientGetKeyFromChain(certificate, settings):
                if result in (0, 1):
                    yield result
                else:
                    break
            publicKey, serverCertChain, tackExt = result

            if signature_scheme in (SignatureScheme.ed25519,
                                    SignatureScheme.ed448):
                pad_type = None
                hash_name = "intrinsic"
                salt_len = None
                method = publicKey.hashAndVerify
            elif signature_scheme[1] == SignatureAlgorithm.ecdsa:
                pad_type = None
                hash_name = HashAlgorithm.toRepr(signature_scheme[0])
                matching_hash = self._curve_name_to_hash_name(
                    publicKey.curve_name)
                if hash_name != matching_hash:
                    raise TLSIllegalParameterException(
                        "server selected signature method invalid for the "
                        "certificate it presented (curve mismatch)")

                salt_len = None
                method = publicKey.verify
            else:
                scheme = SignatureScheme.toRepr(signature_scheme)
                pad_type = SignatureScheme.getPadding(scheme)
                hash_name = SignatureScheme.getHash(scheme)
                salt_len = getattr(hashlib, hash_name)().digest_size
                method = publicKey.verify

            if not method(certificate_verify.signature,
                          signature_context,
                          pad_type,
                          hash_name,
                          salt_len):
                raise TLSDecryptionFailed("server Certificate Verify "
                                          "signature "
                                          "verification failed")

        transcript_hash = self._handshake_hash.digest(prfName)

        for result in self._getMsg(ContentType.handshake,
                                   HandshakeType.finished,
                                   prf_size):
            if result in (0, 1):
                yield result
            else:
                break
        finished = result

        server_finish_hs = self._handshake_hash.copy()

        assert isinstance(finished, Finished)

        finished_key = HKDF_expand_label(sr_handshake_traffic_secret,
                                         b"finished", b'', prf_size, prfName)
        verify_data = secureHMAC(finished_key, transcript_hash, prfName)

        if finished.verify_data != verify_data:
            raise TLSDecryptionFailed("Finished value is not valid")

        # now send client set of messages
        self._changeWriteState()

        # Master secret
        secret = derive_secret(secret, bytearray(b'derived'), None, prfName)
        secret = secureHMAC(secret, bytearray(prf_size), prfName)

        cl_app_traffic = derive_secret(secret, bytearray(b'c ap traffic'),
                                       server_finish_hs, prfName)
        sr_app_traffic = derive_secret(secret, bytearray(b's ap traffic'),
                                       server_finish_hs, prfName)

        if certificate_request:
            client_certificate = Certificate(serverHello.certificate_type,
                                             self.version)
            if clientCertChain:
                # Check to make sure we have the same type of certificates the
                # server requested
                if serverHello.certificate_type == CertificateType.x509 \
                    and not isinstance(clientCertChain, X509CertChain):
                    for result in self._sendError(
                            AlertDescription.handshake_failure,
                            "Client certificate is of wrong type"):
                        yield result

            client_certificate.create(clientCertChain)
            # we need to send the message even if we don't have a certificate
            for result in self._sendMsg(client_certificate):
                yield result

            if clientCertChain and privateKey:
                valid_sig_algs = certificate_request.supported_signature_algs
                if not valid_sig_algs:
                    for result in self._sendError(
                            AlertDescription.missing_extension,
                            "No Signature Algorithms found"):
                        yield result

                availSigAlgs = self._sigHashesToList(settings, privateKey,
                                                     clientCertChain,
                                                     version=(3, 4))
                signature_scheme = getFirstMatching(availSigAlgs,
                                                    valid_sig_algs)
                scheme = SignatureScheme.toRepr(signature_scheme)
                signature_scheme = getattr(SignatureScheme, scheme)

                signature_context = \
                    KeyExchange.calcVerifyBytes((3, 4), self._handshake_hash,
                                                signature_scheme, None, None,
                                                None, prfName, b'client')

                if signature_scheme in (SignatureScheme.ed25519,
                        SignatureScheme.ed448):
                    pad_type = None
                    hash_name = "intrinsic"
                    salt_len = None
                    sig_func = privateKey.hashAndSign
                    ver_func = privateKey.hashAndVerify
                elif signature_scheme[1] == SignatureAlgorithm.ecdsa:
                    pad_type = None
                    hash_name = HashAlgorithm.toRepr(signature_scheme[0])
                    salt_len = None
                    sig_func = privateKey.sign
                    ver_func = privateKey.verify
                else:
                    pad_type = SignatureScheme.getPadding(scheme)
                    hash_name = SignatureScheme.getHash(scheme)
                    salt_len = getattr(hashlib, hash_name)().digest_size
                    sig_func = privateKey.sign
                    ver_func = privateKey.verify

                signature = sig_func(signature_context,
                                     pad_type,
                                     hash_name,
                                     salt_len)
                if not ver_func(signature, signature_context,
                                pad_type,
                                hash_name,
                                salt_len):
                    for result in self._sendError(
                            AlertDescription.internal_error,
                            "Certificate Verify signature failed"):
                        yield result

                certificate_verify = CertificateVerify(self.version)
                certificate_verify.create(signature, signature_scheme)

                for result in self._sendMsg(certificate_verify):
                    yield result

        # Do after client cert and verify messages has been sent.
        exporter_master_secret = derive_secret(secret,
                                               bytearray(b'exp master'),
                                               self._handshake_hash, prfName)

        self._recordLayer.calcTLS1_3PendingState(
            serverHello.cipher_suite,
            cl_app_traffic,
            sr_app_traffic,
            settings.cipherImplementations)
        # be ready to process alert messages from the server, which
        # MUST be encrypted with ap traffic secret when they are sent after
        # Finished
        self._changeReadState()

        cl_finished_key = HKDF_expand_label(cl_handshake_traffic_secret,
                                            b"finished", b'',
                                            prf_size, prfName)
        cl_verify_data = secureHMAC(
            cl_finished_key,
            self._handshake_hash.digest(prfName),
            prfName)

        cl_finished = Finished(self.version, prf_size)
        cl_finished.create(cl_verify_data)

        if not self._ccs_sent and clientHello.session_id:
            ccs = ChangeCipherSpec().create()
            msgs = [ccs, cl_finished]
        else:
            msgs = [cl_finished]

        for result in self._sendMsgs(msgs):
            yield result

        # CCS messages are not allowed in post handshake authentication
        self._middlebox_compat_mode = False

        # fully switch to application data
        self._changeWriteState()

        self._first_handshake_hashes = self._handshake_hash.copy()

        resumption_master_secret = derive_secret(secret,
                                                 bytearray(b'res master'),
                                                 self._handshake_hash, prfName)

        self.session = Session()
        self.extendedMasterSecret = True

        serverName = None
        if clientHello.server_name:
            serverName = clientHello.server_name.decode("utf-8")

        appProto = None
        alpnExt = encrypted_extensions.getExtension(ExtensionType.alpn)
        if alpnExt:
            appProto = alpnExt.protocol_names[0]

        heartbeat_ext = encrypted_extensions.getExtension(ExtensionType.heartbeat)
        if heartbeat_ext:
            if not settings.use_heartbeat_extension:
                for result in self._sendError(
                        AlertDescription.unsupported_extension,
                        "Server sent Heartbeat extension without one in "
                        "client hello"):
                    yield result
            if heartbeat_ext.mode == HeartbeatMode.PEER_ALLOWED_TO_SEND and \
                    settings.heartbeat_response_callback:
                self.heartbeat_can_send = True
                self.heartbeat_response_callback = settings.\
                    heartbeat_response_callback
            elif heartbeat_ext.mode == HeartbeatMode.\
                    PEER_NOT_ALLOWED_TO_SEND or not settings.\
                    heartbeat_response_callback:
                self.heartbeat_can_send = False
            else:
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        "Server responded with invalid Heartbeat extension"):
                    yield result
            self.heartbeat_supported = True

        self.session.create(secret,
                            bytearray(b''),  # no session_id in TLS 1.3
                            serverHello.cipher_suite,
                            None,  # no SRP
                            clientCertChain,
                            certificate.cert_chain if certificate else None,
                            None,  # no TACK
                            False,  # no TACK in hello
                            serverName,
                            encryptThenMAC=False,  # all ciphers are AEAD
                            extendedMasterSecret=True,  # all TLS1.3 are EMS
                            appProto=appProto,
                            cl_app_secret=cl_app_traffic,
                            sr_app_secret=sr_app_traffic,
                            exporterMasterSecret=exporter_master_secret,
                            resumptionMasterSecret=resumption_master_secret,
                            # NOTE it must be a reference, not a copy!
                            tickets=self.tickets)

        yield "finished" if not resuming else "resumed_and_finished"

    def _clientSelectNextProto(self, nextProtos, serverHello):
        # nextProtos is None or non-empty list of strings
        # serverHello.next_protos is None or possibly-empty list of strings
        #
        # !!! We assume the client may have specified nextProtos as a list of
        # strings so we convert them to bytearrays (it's awkward to require
        # the user to specify a list of bytearrays or "bytes", and in 
        # Python 2.6 bytes() is just an alias for str() anyways...
        if nextProtos is not None and serverHello.next_protos is not None:
            for p in nextProtos:
                if bytearray(p) in serverHello.next_protos:
                    return bytearray(p)
            else:
                # If the client doesn't support any of server's protocols,
                # or the server doesn't advertise any (next_protos == [])
                # the client SHOULD select the first protocol it supports.
                return bytearray(nextProtos[0])
        return None
 
    def _clientResume(self, session, serverHello, clientRandom, 
                      cipherImplementations, nextProto, settings):
        #If the server agrees to resume
        if session and session.sessionID and \
            serverHello.session_id == session.sessionID:

            if serverHello.cipher_suite != session.cipherSuite:
                for result in self._sendError(\
                    AlertDescription.illegal_parameter,\
                    "Server's ciphersuite doesn't match session"):
                    yield result

            #Calculate pending connection states
            self._calcPendingStates(session.cipherSuite,
                                    session.masterSecret,
                                    clientRandom, serverHello.random,
                                    cipherImplementations)

            #Exchange ChangeCipherSpec and Finished messages
            for result in self._getFinished(session.masterSecret,
                                            session.cipherSuite):
                yield result
            # buffer writes so that CCS and Finished go out in one TCP packet
            self.sock.buffer_writes = True
            for result in self._sendFinished(session.masterSecret,
                                             session.cipherSuite,
                                             nextProto,
                                             settings=settings):
                yield result
            self.sock.flush()
            self.sock.buffer_writes = False

            #Set the session for this connection
            self.session = session
            yield "resumed_and_finished"

    def _clientKeyExchange(self, settings, cipherSuite,
                           clientCertChain, privateKey,
                           certificateType,
                           tackExt, clientRandom, serverRandom,
                           keyExchange):
        """Perform the client side of key exchange"""
        # if server chose cipher suite with authentication, get the certificate
        if cipherSuite in CipherSuite.certAllSuites or \
                cipherSuite in CipherSuite.ecdheEcdsaSuites or \
                cipherSuite in CipherSuite.dheDsaSuites:
            for result in self._getMsg(ContentType.handshake,
                                       HandshakeType.certificate,
                                       certificateType):
                if result in (0, 1):
                    yield result
                else: break
            serverCertificate = result
        else:
            serverCertificate = None
        # if server chose RSA key exchange, we need to skip SKE message
        if cipherSuite not in CipherSuite.certSuites:
            for result in self._getMsg(ContentType.handshake,
                                       HandshakeType.server_key_exchange,
                                       cipherSuite):
                if result in (0, 1):
                    yield result
                else: break
            serverKeyExchange = result
        else:
            serverKeyExchange = None

        for result in self._getMsg(ContentType.handshake,
                                   (HandshakeType.certificate_request,
                                    HandshakeType.server_hello_done)):
            if result in (0, 1):
                yield result
            else: break

        certificateRequest = None
        if isinstance(result, CertificateRequest):
            certificateRequest = result

            #abort if Certificate Request with inappropriate ciphersuite
            if cipherSuite not in CipherSuite.certAllSuites \
                and cipherSuite not in CipherSuite.ecdheEcdsaSuites \
                and CipherSuite not in CipherSuite.dheDsaSuites\
                or cipherSuite in CipherSuite.srpAllSuites:
                for result in self._sendError(\
                        AlertDescription.unexpected_message,
                        "Certificate Request with incompatible cipher suite"):
                    yield result

            # we got CertificateRequest so now we'll get ServerHelloDone
            for result in self._getMsg(ContentType.handshake,
                                       HandshakeType.server_hello_done):
                if result in (0, 1):
                    yield result
                else: break
        serverHelloDone = result

        serverCertChain = None
        publicKey = None
        if cipherSuite in CipherSuite.certAllSuites or \
                cipherSuite in CipherSuite.ecdheEcdsaSuites or \
                cipherSuite in CipherSuite.dheDsaSuites:
            # get the certificate
            for result in self._clientGetKeyFromChain(serverCertificate,
                                                      settings,
                                                      tackExt):
                if result in (0, 1):
                    yield result
                else: break
            publicKey, serverCertChain, tackExt = result

            #Check the server's signature, if the server chose an authenticated
            # PFS-enabled ciphersuite

            if serverKeyExchange:
                valid_sig_algs = \
                    self._sigHashesToList(settings,
                                          certList=serverCertChain)
                try:
                    KeyExchange.verifyServerKeyExchange(serverKeyExchange,
                                                        publicKey,
                                                        clientRandom,
                                                        serverRandom,
                                                        valid_sig_algs)
                except TLSIllegalParameterException:
                    for result in self._sendError(AlertDescription.\
                                                  illegal_parameter):
                        yield result
                except TLSDecryptionFailed:
                    for result in self._sendError(\
                            AlertDescription.decrypt_error):
                        yield result

        if serverKeyExchange:
            # store key exchange metadata for user applications
            if self.version >= (3, 3) \
                    and (cipherSuite in CipherSuite.certAllSuites or
                         cipherSuite in CipherSuite.ecdheEcdsaSuites) \
                    and cipherSuite not in CipherSuite.certSuites:
                self.serverSigAlg = (serverKeyExchange.hashAlg,
                                     serverKeyExchange.signAlg)

            if cipherSuite in CipherSuite.dhAllSuites:
                self.dhGroupSize = numBits(serverKeyExchange.dh_p)
            if cipherSuite in CipherSuite.ecdhAllSuites:
                self.ecdhCurve = serverKeyExchange.named_curve

        #Send Certificate if we were asked for it
        if certificateRequest:

            # if a peer doesn't advertise support for any algorithm in TLSv1.2,
            # support for SHA1+RSA can be assumed
            if self.version == (3, 3)\
                and not [sig for sig in \
                         certificateRequest.supported_signature_algs\
                         if sig[1] == SignatureAlgorithm.rsa]:
                for result in self._sendError(\
                        AlertDescription.handshake_failure,
                        "Server doesn't accept any sigalgs we support: " +
                        str(certificateRequest.supported_signature_algs)):
                    yield result
            clientCertificate = Certificate(certificateType)

            if clientCertChain:
                #Check to make sure we have the same type of
                #certificates the server requested
                if certificateType == CertificateType.x509 \
                    and not isinstance(clientCertChain, X509CertChain):
                    for result in self._sendError(\
                            AlertDescription.handshake_failure,
                            "Client certificate is of wrong type"):
                        yield result

                clientCertificate.create(clientCertChain)
            # we need to send the message even if we don't have a certificate
            for result in self._sendMsg(clientCertificate):
                yield result
        else:
            #Server didn't ask for cer, zeroise so session doesn't store them
            privateKey = None
            clientCertChain = None

        try:
            ske = serverKeyExchange
            premasterSecret = keyExchange.processServerKeyExchange(publicKey,
                                                                   ske)
        except TLSInsufficientSecurity as e:
            for result in self._sendError(\
                    AlertDescription.insufficient_security, e):
                yield result
        except TLSIllegalParameterException as e:
            for result in self._sendError(\
                    AlertDescription.illegal_parameter, e):
                yield result

        clientKeyExchange = keyExchange.makeClientKeyExchange()

        #Send ClientKeyExchange
        for result in self._sendMsg(clientKeyExchange):
            yield result

        # the Extended Master Secret calculation uses the same handshake
        # hashes as the Certificate Verify calculation so we need to
        # make a copy of it
        self._certificate_verify_handshake_hash = self._handshake_hash.copy()

        #if client auth was requested and we have a private key, send a
        #CertificateVerify
        if certificateRequest and privateKey:
            valid_sig_algs = self._sigHashesToList(settings, privateKey,
                                                   clientCertChain)
            try:
                certificateVerify = KeyExchange.makeCertificateVerify(
                    self.version,
                    self._certificate_verify_handshake_hash,
                    valid_sig_algs,
                    privateKey,
                    certificateRequest,
                    premasterSecret,
                    clientRandom,
                    serverRandom)
            except TLSInternalError as exception:
                for result in self._sendError(
                        AlertDescription.internal_error, exception):
                    yield result
            for result in self._sendMsg(certificateVerify):
                yield result

        yield (premasterSecret, serverCertChain, clientCertChain, tackExt)

    def _clientFinished(self, premasterSecret, clientRandom, serverRandom,
                        cipherSuite, cipherImplementations, nextProto,
                        settings):
        if self.extendedMasterSecret:
            cvhh = self._certificate_verify_handshake_hash
            # in case of session resumption, or when the handshake doesn't
            # use the certificate authentication, the hashes are the same
            if not cvhh:
                cvhh = self._handshake_hash
            masterSecret = calc_key(self.version, premasterSecret,
                                    cipherSuite, b"extended master secret",
                                    handshake_hashes=cvhh,
                                    output_length=48)
        else:
            masterSecret = calc_key(self.version, premasterSecret,
                                    cipherSuite, b"master secret",
                                    client_random=clientRandom,
                                    server_random=serverRandom,
                                    output_length=48)
        self._calcPendingStates(cipherSuite, masterSecret, 
                                clientRandom, serverRandom, 
                                cipherImplementations)

        #Exchange ChangeCipherSpec and Finished messages
        for result in self._sendFinished(masterSecret, cipherSuite, nextProto,
                settings=settings):
            yield result
        self.sock.flush()
        self.sock.buffer_writes = False
        for result in self._getFinished(masterSecret,
                                        cipherSuite,
                                        nextProto=nextProto):
            yield result
        yield masterSecret

    def _check_certchain_with_settings(self, cert_chain, settings):
        """
        Verify that the key parameters match enabled ones.

        Checks if the certificate key size matches the minimum and maximum
        sizes set or that it uses curves enabled in settings
        """
        #Get and check public key from the cert chain
        publicKey = cert_chain.getEndEntityPublicKey()
        cert_type = cert_chain.x509List[0].certAlg
        if cert_type == "ecdsa":
            curve_name = publicKey.curve_name
            for name, aliases in CURVE_ALIASES.items():
                if curve_name in aliases:
                    curve_name = name
                    break

            if self.version <= (3, 3) and curve_name not in settings.eccCurves:
                for result in self._sendError(
                        AlertDescription.handshake_failure,
                        "Peer sent certificate with curve we did not "
                        "advertise support for: {0}".format(curve_name)):
                    yield result
            if self.version >= (3, 4):
                if curve_name not in ('secp256r1', 'secp384r1', 'secp521r1'):
                    for result in self._sendError(
                            AlertDescription.illegal_parameter,
                            "Peer sent certificate with curve not supported "
                            "in TLS 1.3: {0}".format(curve_name)):
                        yield result
                if curve_name == 'secp256r1':
                    sig_alg_for_curve = 'sha256'
                elif curve_name == 'secp384r1':
                    sig_alg_for_curve = 'sha384'
                else:
                    assert curve_name == 'secp521r1'
                    sig_alg_for_curve = 'sha512'
                if sig_alg_for_curve not in settings.ecdsaSigHashes:
                    for result in self._sendError(
                            AlertDescription.illegal_parameter,
                            "Peer selected certificate with ECDSA curve we "
                            "did not advertise support for: {0}"
                            .format(curve_name)):
                        yield result
        elif cert_type in ("Ed25519", "Ed448"):
            if self.version < (3, 3):
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        "Peer sent certificate incompatible with negotiated "
                        "TLS version"):
                    yield result
            if cert_type not in settings.more_sig_schemes:
                for result in self._sendError(
                        AlertDescription.handshake_failure,
                        "Peer sent certificate we did not advertise support "
                        "for: {0}".format(cert_type)):
                    yield result

        else:
            # for RSA and DSA keys
            if len(publicKey) < settings.minKeySize:
                for result in self._sendError(
                        AlertDescription.handshake_failure,
                        "Other party's public key too small: %d" %
                        len(publicKey)):
                    yield result
            if len(publicKey) > settings.maxKeySize:
                for result in self._sendError(
                        AlertDescription.handshake_failure,
                        "Other party's public key too large: %d" %
                        len(publicKey)):
                    yield result
        yield publicKey

    def _clientGetKeyFromChain(self, certificate, settings, tack_ext=None):
        #Get and check cert chain from the Certificate message
        cert_chain = certificate.cert_chain
        if not cert_chain or cert_chain.getNumCerts() == 0:
            for result in self._sendError(
                    AlertDescription.illegal_parameter,
                    "Other party sent a Certificate message without "\
                    "certificates"):
                yield result

        for result in self._check_certchain_with_settings(
                cert_chain,
                settings):
            if result in (0, 1):
                yield result
            else: break
        public_key = result

        # If there's no TLS Extension, look for a TACK cert
        if tackpyLoaded:
            if not tack_ext:
                tack_ext = cert_chain.getTackExt()
         
            # If there's a TACK (whether via TLS or TACK Cert), check that it
            # matches the cert chain   
            if tack_ext and tack_ext.tacks:
                for tack in tack_ext.tacks:
                    if not cert_chain.checkTack(tack):
                        for result in self._sendError(  
                                AlertDescription.illegal_parameter,
                                "Other party's TACK doesn't match their public key"):
                                yield result

        yield public_key, cert_chain, tack_ext


    #*********************************************************
    # Server Handshake Functions
    #*********************************************************


    def handshakeServer(self, verifierDB=None,
                        certChain=None, privateKey=None, reqCert=False,
                        sessionCache=None, settings=None, checker=None,
                        reqCAs = None, 
                        tacks=None, activationFlags=0,
                        nextProtos=None, anon=False, alpn=None, sni=None):
        """Perform a handshake in the role of server.

        This function performs an SSL or TLS handshake.  Depending on
        the arguments and the behavior of the client, this function can
        perform an SRP, or certificate-based handshake.  It
        can also perform a combined SRP and server-certificate
        handshake.

        Like any handshake function, this can be called on a closed
        TLS connection, or on a TLS connection that is already open.
        If called on an open connection it performs a re-handshake.
        This function does not send a Hello Request message before
        performing the handshake, so if re-handshaking is required,
        the server must signal the client to begin the re-handshake
        through some other means.

        If the function completes without raising an exception, the
        TLS connection will be open and available for data transfer.

        If an exception is raised, the connection will have been
        automatically closed (if it was ever open).

        :type verifierDB: ~tlslite.verifierdb.VerifierDB
        :param verifierDB: A database of SRP password verifiers
            associated with usernames.  If the client performs an SRP
            handshake, the session's srpUsername attribute will be set.

        :type certChain: ~tlslite.x509certchain.X509CertChain
        :param certChain: The certificate chain to be used if the
            client requests server certificate authentication and no virtual
            host defined in HandshakeSettings matches ClientHello.

        :type privateKey: ~tlslite.utils.rsakey.RSAKey
        :param privateKey: The private key to be used if the client
            requests server certificate authentication and no virtual host
            defined in HandshakeSettings matches ClientHello.

        :type reqCert: bool
        :param reqCert: Whether to request client certificate
            authentication.  This only applies if the client chooses server
            certificate authentication; if the client chooses SRP
            authentication, this will be ignored.  If the client
            performs a client certificate authentication, the sessions's
            clientCertChain attribute will be set.

        :type sessionCache: ~tlslite.sessioncache.SessionCache
        :param sessionCache: An in-memory cache of resumable sessions.
            The client can resume sessions from this cache.  Alternatively,
            if the client performs a full handshake, a new session will be
            added to the cache.

        :type settings: ~tlslite.handshakesettings.HandshakeSettings
        :param settings: Various settings which can be used to control
            the ciphersuites and SSL/TLS version chosen by the server.

        :type checker: ~tlslite.checker.Checker
        :param checker: A Checker instance.  This instance will be
            invoked to examine the other party's authentication
            credentials, if the handshake completes succesfully.

        :type reqCAs: list of bytearray
        :param reqCAs: A collection of DER-encoded DistinguishedNames that
            will be sent along with a certificate request to help client pick
            a certificates. This does not affect verification.

        :type nextProtos: list of str
        :param nextProtos: A list of upper layer protocols to expose to the
            clients through the Next-Protocol Negotiation Extension,
            if they support it. Deprecated, use the `virtual_hosts` in
            HandshakeSettings.

        :type alpn: list of bytearray
        :param alpn: names of application layer protocols supported.
            Note that it will be used instead of NPN if both were advertised by
            client. Deprecated, use the `virtual_hosts` in HandshakeSettings.

        :type sni: bytearray
        :param sni: expected virtual name hostname. Deprecated, use the
            `virtual_hosts` in HandshakeSettings.

        :raises socket.error: If a socket error occurs.
        :raises tlslite.errors.TLSAbruptCloseError: If the socket is closed
            without a preceding alert.
        :raises tlslite.errors.TLSAlert: If a TLS alert is signalled.
        :raises tlslite.errors.TLSAuthenticationError: If the checker
            doesn't like the other party's authentication credentials.
        """
        for result in self.handshakeServerAsync(verifierDB,
                certChain, privateKey, reqCert, sessionCache, settings,
                checker, reqCAs,
                tacks=tacks, activationFlags=activationFlags,
                nextProtos=nextProtos, anon=anon, alpn=alpn, sni=sni):
            pass


    def handshakeServerAsync(self, verifierDB=None,
                             certChain=None, privateKey=None, reqCert=False,
                             sessionCache=None, settings=None, checker=None,
                             reqCAs=None, 
                             tacks=None, activationFlags=0,
                             nextProtos=None, anon=False, alpn=None, sni=None
                             ):
        """Start a server handshake operation on the TLS connection.

        This function returns a generator which behaves similarly to
        handshakeServer().  Successive invocations of the generator
        will return 0 if it is waiting to read from the socket, 1 if it is
        waiting to write to the socket, or it will raise StopIteration
        if the handshake operation is complete.

        :rtype: iterable
        :returns: A generator; see above for details.
        """
        handshaker = self._handshakeServerAsyncHelper(\
            verifierDB=verifierDB, cert_chain=certChain,
            privateKey=privateKey, reqCert=reqCert,
            sessionCache=sessionCache, settings=settings, 
            reqCAs=reqCAs, 
            tacks=tacks, activationFlags=activationFlags, 
            nextProtos=nextProtos, anon=anon, alpn=alpn, sni=sni)
        for result in self._handshakeWrapperAsync(handshaker, checker):
            yield result


    def _handshakeServerAsyncHelper(self, verifierDB,
                             cert_chain, privateKey, reqCert, sessionCache,
                             settings, reqCAs, 
                             tacks, activationFlags, 
                             nextProtos, anon, alpn, sni):

        self._handshakeStart(client=False)

        if not settings:
            settings = HandshakeSettings()
        settings = settings.validate()

        if (not verifierDB) and (not cert_chain) and not anon and \
                not settings.pskConfigs and not settings.virtual_hosts:
            raise ValueError("Caller passed no authentication credentials")
        if cert_chain and not privateKey:
            raise ValueError("Caller passed a cert_chain but no privateKey")
        if privateKey and not cert_chain:
            raise ValueError("Caller passed a privateKey but no cert_chain")
        if reqCAs and not reqCert:
            raise ValueError("Caller passed reqCAs but not reqCert")            
        if cert_chain and not isinstance(cert_chain, X509CertChain):
            raise ValueError("Unrecognized certificate type")
        if activationFlags and not tacks:
            raise ValueError("Nonzero activationFlags requires tacks")
        if tacks:
            if not tackpyLoaded:
                raise ValueError("tackpy is not loaded")
            if not settings.useExperimentalTackExtension:
                raise ValueError("useExperimentalTackExtension not enabled")
        if alpn is not None and not alpn:
            raise ValueError("Empty list of ALPN protocols")

        self.sock.padding_cb = settings.padding_cb

        # OK Start exchanging messages
        # ******************************
        
        # Handle ClientHello and resumption
        for result in self._serverGetClientHello(settings, privateKey,
                                                 cert_chain,
                                                 verifierDB, sessionCache,
                                                 anon, alpn, sni):
            if result in (0,1): yield result
            elif result == None:
                self._handshakeDone(resumed=True)                
                return # Handshake was resumed, we're done 
            else: break
        (clientHello, version, cipherSuite, sig_scheme, privateKey,
            cert_chain) = result

        # in TLS 1.3 the handshake is completely different
        # (extensions go into different messages, format of messages is
        # different, etc.)
        if version > (3, 3):
            for result in self._serverTLS13Handshake(settings, clientHello,
                                                     cipherSuite,
                                                     privateKey, cert_chain,
                                                     version, sig_scheme,
                                                     alpn, reqCert):
                if result in (0, 1):
                    yield result
                else:
                    break
            if result == "finished":
                self._handshakeDone(resumed=False)
            return

        #If not a resumption...

        # Create the ServerHello message
        if sessionCache:
            sessionID = getRandomBytes(32)
        else:
            sessionID = bytearray(0)
        
        if not clientHello.supports_npn:
            nextProtos = None

        alpnExt = clientHello.getExtension(ExtensionType.alpn)
        if alpnExt and alpn:
            # if there's ALPN, don't do NPN
            nextProtos = None

        # If not doing a certificate-based suite, discard the TACK
        if not cipherSuite in CipherSuite.certAllSuites and \
                not cipherSuite in CipherSuite.ecdheEcdsaSuites:
            tacks = None

        # Prepare a TACK Extension if requested
        if clientHello.tack:
            tackExt = TackExtension.create(tacks, activationFlags)
        else:
            tackExt = None

        extensions = []
        # Prepare other extensions if requested
        if settings.useEncryptThenMAC and \
                clientHello.getExtension(ExtensionType.encrypt_then_mac) and \
                cipherSuite not in CipherSuite.streamSuites and \
                cipherSuite not in CipherSuite.aeadSuites:
            extensions.append(TLSExtension().create(ExtensionType.
                                                    encrypt_then_mac,
                                                    bytearray(0)))
            self._recordLayer.encryptThenMAC = True

        if settings.useExtendedMasterSecret:
            if clientHello.getExtension(ExtensionType.extended_master_secret):
                extensions.append(TLSExtension().create(ExtensionType.
                                                        extended_master_secret,
                                                        bytearray(0)))
                self.extendedMasterSecret = True
            elif settings.requireExtendedMasterSecret:
                for result in self._sendError(
                        AlertDescription.insufficient_security,
                        "Failed to negotiate Extended Master Secret"):
                    yield result

        selectedALPN = None
        if alpnExt and alpn:
            for protoName in alpnExt.protocol_names:
                if protoName in alpn:
                    selectedALPN = protoName
                    ext = ALPNExtension().create([protoName])
                    extensions.append(ext)
                    break
            else:
                for result in self._sendError(
                        AlertDescription.no_application_protocol,
                        "No mutually supported application layer protocols"):
                    yield result
        # notify client that we understood its renegotiation info extension
        # or SCSV
        secureRenego = False
        renegoExt = clientHello.getExtension(ExtensionType.renegotiation_info)
        if renegoExt:
            if renegoExt.renegotiated_connection:
                for result in self._sendError(
                        AlertDescription.handshake_failure,
                        "Non empty renegotiation info extension in "
                        "initial Client Hello"):
                    yield result
            secureRenego = True
        elif CipherSuite.TLS_EMPTY_RENEGOTIATION_INFO_SCSV in \
                clientHello.cipher_suites:
            secureRenego = True
        if secureRenego:
            extensions.append(RenegotiationInfoExtension()
                              .create(bytearray(0)))

        # tell the client what point formats we support
        if clientHello.getExtension(ExtensionType.ec_point_formats):
            # even though the selected cipher may not use ECC, client may want
            # to send a CA certificate with ECDSA...
            extensions.append(ECPointFormatsExtension().create(
                [ECPointFormat.uncompressed]))

        # if client sent Heartbeat extension
        if clientHello.getExtension(ExtensionType.heartbeat):
            # and we want to accept it
            if settings.use_heartbeat_extension:
                extensions.append(HeartbeatExtension().create(
                    HeartbeatMode.PEER_ALLOWED_TO_SEND))

        if clientHello.getExtension(ExtensionType.record_size_limit) and \
                settings.record_size_limit:
            # in TLS 1.2 and earlier we can select at most 2^14B records
            extensions.append(RecordSizeLimitExtension().create(
                min(2**14, settings.record_size_limit)))


        # don't send empty list of extensions
        if not extensions:
            extensions = None

        serverHello = ServerHello()
        # RFC 8446, section 4.1.3
        random = getRandomBytes(32)
        if version == (3, 3) and settings.maxVersion > (3, 3):
            random[-8:] = TLS_1_2_DOWNGRADE_SENTINEL
        if version < (3, 3) and settings.maxVersion >= (3, 3):
            random[-8:] = TLS_1_1_DOWNGRADE_SENTINEL
        serverHello.create(self.version, random, sessionID,
                           cipherSuite, CertificateType.x509, tackExt,
                           nextProtos, extensions=extensions)

        # Perform the SRP key exchange
        clientCertChain = None
        if cipherSuite in CipherSuite.srpAllSuites:
            for result in self._serverSRPKeyExchange(clientHello, serverHello,
                                                     verifierDB, cipherSuite,
                                                     privateKey, cert_chain,
                                                     settings):
                if result in (0, 1):
                    yield result
                else: break
            premasterSecret, privateKey, cert_chain = result

        # Perform a certificate-based key exchange
        elif (cipherSuite in CipherSuite.certSuites or
              cipherSuite in CipherSuite.dheCertSuites or
              cipherSuite in CipherSuite.dheDsaSuites or
              cipherSuite in CipherSuite.ecdheCertSuites or
              cipherSuite in CipherSuite.ecdheEcdsaSuites):
            try:
                sig_hash_alg, cert_chain, privateKey = \
                    self._pickServerKeyExchangeSig(settings,
                                                   clientHello,
                                                   cert_chain,
                                                   privateKey)
            except TLSHandshakeFailure as alert:
                for result in self._sendError(
                        AlertDescription.handshake_failure,
                        str(alert)):
                    yield result

            if cipherSuite in CipherSuite.certSuites:
                keyExchange = RSAKeyExchange(cipherSuite,
                                             clientHello,
                                             serverHello,
                                             privateKey)
            elif cipherSuite in CipherSuite.dheCertSuites or \
                    cipherSuite in CipherSuite.dheDsaSuites:
                dhGroups = self._groupNamesToList(settings)
                keyExchange = DHE_RSAKeyExchange(cipherSuite,
                                                 clientHello,
                                                 serverHello,
                                                 privateKey,
                                                 settings.dhParams,
                                                 dhGroups)
            elif cipherSuite in CipherSuite.ecdheCertSuites or \
                    cipherSuite in CipherSuite.ecdheEcdsaSuites:
                acceptedCurves = self._curveNamesToList(settings)
                defaultCurve = getattr(GroupName, settings.defaultCurve)
                keyExchange = ECDHE_RSAKeyExchange(cipherSuite,
                                                   clientHello,
                                                   serverHello,
                                                   privateKey,
                                                   acceptedCurves,
                                                   defaultCurve)
            else:
                assert(False)
            for result in self._serverCertKeyExchange(clientHello, serverHello,
                                        sig_hash_alg, cert_chain, keyExchange,
                                        reqCert, reqCAs, cipherSuite,
                                        settings):
                if result in (0,1): yield result
                else: break
            (premasterSecret, clientCertChain) = result

        # Perform anonymous Diffie Hellman key exchange
        elif (cipherSuite in CipherSuite.anonSuites or
              cipherSuite in CipherSuite.ecdhAnonSuites):
            if cipherSuite in CipherSuite.anonSuites:
                dhGroups = self._groupNamesToList(settings)
                keyExchange = ADHKeyExchange(cipherSuite, clientHello,
                                             serverHello, settings.dhParams,
                                             dhGroups)
            else:
                acceptedCurves = self._curveNamesToList(settings)
                defaultCurve = getattr(GroupName, settings.defaultCurve)
                keyExchange = AECDHKeyExchange(cipherSuite, clientHello,
                                               serverHello, acceptedCurves,
                                               defaultCurve)
            for result in self._serverAnonKeyExchange(serverHello, keyExchange,
                                                      cipherSuite):
                if result in (0,1): yield result
                else: break
            premasterSecret = result

        else:
            assert(False)
                        
        # Exchange Finished messages      
        for result in self._serverFinished(premasterSecret, 
                                clientHello.random, serverHello.random,
                                cipherSuite, settings.cipherImplementations,
                                nextProtos, settings):
                if result in (0,1): yield result
                else: break
        masterSecret = result

        #Create the session object
        self.session = Session()
        if cipherSuite in CipherSuite.certAllSuites or \
                cipherSuite in CipherSuite.ecdheEcdsaSuites:
            serverCertChain = cert_chain
        else:
            serverCertChain = None
        srpUsername = None
        serverName = None
        if clientHello.srp_username:
            srpUsername = clientHello.srp_username.decode("utf-8")
        if clientHello.server_name:
            serverName = clientHello.server_name.decode("utf-8")
        self.session.create(masterSecret, serverHello.session_id, cipherSuite,
                            srpUsername, clientCertChain, serverCertChain,
                            tackExt, (serverHello.tackExt is not None),
                            serverName,
                            encryptThenMAC=self._recordLayer.encryptThenMAC,
                            extendedMasterSecret=self.extendedMasterSecret,
                            appProto=selectedALPN,
                            # NOTE it must be a reference, not a copy!
                            tickets=self.tickets)

        #Add the session object to the session cache
        if sessionCache and sessionID:
            sessionCache[sessionID] = self.session

        self._handshakeDone(resumed=False)
        self._serverRandom = serverHello.random
        self._clientRandom = clientHello.random

    def request_post_handshake_auth(self, settings=None):
        """
        Request Post-handshake Authentication from client.

        The PHA process is asynchronous, and client may send some data before
        its certificates are added to Session object. Calling this generator
        will only request for the new identity of client, it will not wait for
        it.
        """
        if self.version != (3, 4):
            raise ValueError("PHA is supported only in TLS 1.3")
        if self._client:
            raise ValueError("PHA can only be requested by server")
        if not self._pha_supported:
            raise ValueError("PHA not supported by client")

        settings = settings or HandshakeSettings()
        settings = settings.validate()

        valid_sig_algs = self._sigHashesToList(settings)
        if not valid_sig_algs:
            raise ValueError("No signature algorithms enabled in "
                             "HandshakeSettings")

        context = bytes(getRandomBytes(32))

        certificate_request = CertificateRequest(self.version)
        certificate_request.create(context=context, sig_algs=valid_sig_algs)

        self._cert_requests[context] = certificate_request

        for result in self._sendMsg(certificate_request):
            yield result

    @staticmethod
    def _derive_key_iv(nonce, user_key, settings):
        """Derive the IV and key for session ticket encryption."""
        if settings.ticketCipher == "aes128gcm":
            prf_name = "sha256"
            prf_size = 32
        else:
            prf_name = "sha384"
            prf_size = 48

        # mix the nonce with the key set by user
        secret = bytearray(prf_size)
        secret = secureHMAC(secret, nonce, prf_name)
        secret = derive_secret(secret, bytearray(b'derived'), None, prf_name)
        secret = secureHMAC(secret, user_key, prf_name)

        ticket_secret = derive_secret(secret,
                                      bytearray(b'SessionTicket secret'),
                                      None, prf_name)

        key = HKDF_expand_label(ticket_secret, b"key", b"", len(user_key),
                                prf_name)
        # all AEADs use 12 byte long IV
        iv = HKDF_expand_label(ticket_secret, b"iv", b"", 12, prf_name)
        return key, iv

    def _serverSendTickets(self, settings):
        """Send session tickets to client."""
        if not settings.ticketKeys:
            return

        for _ in range(settings.ticket_count):
            # prepare the ticket
            ticket = SessionTicketPayload()
            ticket.create(self.session.resumptionMasterSecret,
                          self.version,
                          self.session.cipherSuite,
                          int(time.time()),
                          getRandomBytes(len(settings.ticketKeys[0])),
                          client_cert_chain=self.session.clientCertChain)

            # encrypt the ticket

            # generate keys for the encryption
            nonce = getRandomBytes(32)
            key, iv = self._derive_key_iv(nonce, settings.ticketKeys[0],
                                          settings)

            if settings.ticketCipher in ("aes128gcm", "aes256gcm"):
                cipher = createAESGCM(key,
                                      settings.cipherImplementations)
            elif settings.ticketCipher in ("aes128ccm", "aes256ccm"):
                cipher = createAESCCM(key, settings.cipherImplementations)
            elif settings.ticketCipher in ("aes128ccm_8", "aes256ccm_8"):
                cipher = createAESCCM_8(key, settings.cipherImplementations)
            else:
                assert settings.ticketCipher == "chacha20-poly1305"
                cipher = createCHACHA20(key,
                                        settings.cipherImplementations)

            encrypted_ticket = cipher.seal(iv, ticket.write(), b'')

            # encapsulate the ticket and send to client
            new_ticket = NewSessionTicket()
            new_ticket.create(settings.ticketLifetime,
                              getRandomNumber(1, 8**4),
                              ticket.nonce,
                              nonce + encrypted_ticket,
                              [])
            self._queue_message(new_ticket)

        # send tickets to client
        if settings.ticket_count:
            for result in self._queue_flush():
                yield result

    def _tryDecrypt(self, settings, identity):
        if not settings.ticketKeys:
            return None, None

        if len(identity.identity) < 33:
            # too small for an encrypted ticket
            return None, None

        nonce, encrypted_ticket = identity.identity[:32], identity.identity[32:]
        for user_key in settings.ticketKeys:
            key, iv = self._derive_key_iv(nonce, user_key, settings)
            if settings.ticketCipher in ("aes128gcm", "aes256gcm"):
                cipher = createAESGCM(key, settings.cipherImplementations)
            elif settings.ticketCipher in ("aes128ccm", "aes256ccm"):
                cipher = createAESCCM(key, settings.cipherImplementations)
            elif settings.ticketCipher in ("aes128ccm_8", "aes256ccm_8"):
                cipher = createAESCCM_8(key, settings.cipherImplementations)
            else:
                assert settings.ticketCipher == "chacha20-poly1305"
                cipher = createCHACHA20(key, settings.cipherImplementations)

            ticket = cipher.open(iv, encrypted_ticket, b'')
            if not ticket:
                continue

            parser = Parser(ticket)
            try:
                ticket = SessionTicketPayload().parse(parser)
            except ValueError:
                continue

            prf = 'sha384' if ticket.cipher_suite \
                in CipherSuite.sha384PrfSuites else 'sha256'

            new_sess_ticket = NewSessionTicket()
            new_sess_ticket.ticket_nonce = ticket.nonce
            new_sess_ticket.ticket = identity.identity

            psk = HandshakeHelpers.calc_res_binder_psk(identity,
                                                       ticket.master_secret,
                                                       [new_sess_ticket])

            return ((identity.identity, psk, prf), ticket)

        # no keys
        return None, None

    def _serverTLS13Handshake(self, settings, clientHello, cipherSuite,
                              privateKey, serverCertChain, version, scheme,
                              srv_alpns, reqCert):
        """Perform a TLS 1.3 handshake"""
        prf_name, prf_size = self._getPRFParams(cipherSuite)

        secret = bytearray(prf_size)

        share = clientHello.getExtension(ExtensionType.key_share)
        if share:
            share_ids = [i.group for i in share.client_shares]
            for group_name in chain(settings.keyShares, settings.eccCurves,
                                    settings.dhGroups):
                selected_group = getattr(GroupName, group_name)
                if selected_group in share_ids:
                    cl_key_share = next(i for i in share.client_shares
                                        if i.group == selected_group)
                    break
            else:
                for result in self._sendError(AlertDescription.internal_error,
                                              "HRR did not work?!"):
                    yield result

        psk = None
        selected_psk = None
        resumed_client_cert_chain = None
        psks = clientHello.getExtension(ExtensionType.pre_shared_key)
        psk_types = clientHello.getExtension(
            ExtensionType.psk_key_exchange_modes)
        if psks and (PskKeyExchangeMode.psk_dhe_ke in psk_types.modes or
                     PskKeyExchangeMode.psk_ke in psk_types.modes) and \
                (settings.pskConfigs or settings.ticketKeys):
            for i, ident in enumerate(psks.identities):
                ticket = None
                external = True
                match = [j for j in settings.pskConfigs
                         if j[0] == ident.identity]
                if not match:
                    (match, ticket) = self._tryDecrypt(settings, ident)
                    external = False
                    if not match:
                        continue
                    match = [match]

                # check if PSK can be used with selected cipher suite
                psk_hash = match[0][2] if len(match[0]) > 2 else 'sha256'
                if psk_hash != prf_name:
                    continue

                psk = match[0][1]
                selected_psk = i
                if ticket:
                    resumed_client_cert_chain = ticket.client_cert_chain
                try:
                    HandshakeHelpers.verify_binder(
                        clientHello,
                        self._pre_client_hello_handshake_hash,
                        selected_psk,
                        psk,
                        psk_hash,
                        external)
                except TLSIllegalParameterException as e:
                    for result in self._sendError(
                            AlertDescription.illegal_parameter,
                            str(e)):
                        yield result
                break

        sh_extensions = []

        # we need to gen key share either when we selected psk_dhe_ke or
        # regular certificate authenticated key exchange (the default)
        if (psk and
                PskKeyExchangeMode.psk_dhe_ke in psk_types.modes and
                "psk_dhe_ke" in settings.psk_modes) or\
                (psk is None and privateKey):
            self.ecdhCurve = selected_group
            kex = self._getKEX(selected_group, version)
            key_share = self._genKeyShareEntry(selected_group, version)

            try:
                shared_sec = kex.calc_shared_key(key_share.private,
                                                 cl_key_share.key_exchange)
            except TLSIllegalParameterException as alert:
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        str(alert)):
                    yield result

            sh_extensions.append(ServerKeyShareExtension().create(key_share))
        elif (psk is not None and
              PskKeyExchangeMode.psk_ke in psk_types.modes and
              "psk_ke" in settings.psk_modes):
            shared_sec = bytearray(prf_size)
        else:
            for result in self._sendError(
                    AlertDescription.handshake_failure,
                    "Could not find acceptable PSK identity nor certificate"):
                yield result

        if psk is None:
            psk = bytearray(prf_size)

        sh_extensions.append(SrvSupportedVersionsExtension().create(version))
        if selected_psk is not None:
            sh_extensions.append(SrvPreSharedKeyExtension()
                                 .create(selected_psk))

        serverHello = ServerHello()
        # in TLS1.3 the version selected is sent in extension, (3, 3) is
        # just dummy value to workaround broken middleboxes
        serverHello.create((3, 3), getRandomBytes(32),
                           clientHello.session_id,
                           cipherSuite, extensions=sh_extensions)

        msgs = []
        msgs.append(serverHello)
        if not self._ccs_sent and clientHello.session_id:
            ccs = ChangeCipherSpec().create()
            msgs.append(ccs)
        for result in self._sendMsgs(msgs):
            yield result

        # Early secret
        secret = secureHMAC(secret, psk, prf_name)

        # Handshake Secret
        secret = derive_secret(secret, bytearray(b'derived'), None, prf_name)
        secret = secureHMAC(secret, shared_sec, prf_name)

        sr_handshake_traffic_secret = derive_secret(secret,
                                                    bytearray(b's hs traffic'),
                                                    self._handshake_hash,
                                                    prf_name)
        cl_handshake_traffic_secret = derive_secret(secret,
                                                    bytearray(b'c hs traffic'),
                                                    self._handshake_hash,
                                                    prf_name)
        self.version = version
        self._recordLayer.calcTLS1_3PendingState(
            cipherSuite,
            cl_handshake_traffic_secret,
            sr_handshake_traffic_secret,
            settings.cipherImplementations)

        self._changeWriteState()

        ee_extensions = []

        if clientHello.getExtension(ExtensionType.record_size_limit) and \
                settings.record_size_limit:
            ee_extensions.append(RecordSizeLimitExtension().create(
                min(2**14+1, settings.record_size_limit)))

        # a bit of a hack to detect if the HRR was sent
        # as that means that original key share didn't match what we wanted
        # send the client updated list of shares we support,
        # preferred ones first
        if clientHello.getExtension(ExtensionType.cookie):
            ext = SupportedGroupsExtension()
            groups = [getattr(GroupName, i) for i in settings.keyShares]
            groups += [getattr(GroupName, i) for i in settings.eccCurves
                       if getattr(GroupName, i) not in groups]
            groups += [getattr(GroupName, i) for i in settings.dhGroups
                       if getattr(GroupName, i) not in groups]
            if groups:
                ext.create(groups)
                ee_extensions.append(ext)

        alpn_ext = clientHello.getExtension(ExtensionType.alpn)
        if alpn_ext:
            # error handling was done when receiving ClientHello
            matched = [i for i in alpn_ext.protocol_names if i in srv_alpns]
            if matched:
                ext = ALPNExtension().create([matched[0]])
                ee_extensions.append(ext)

        if clientHello.getExtension(ExtensionType.heartbeat):
            if settings.use_heartbeat_extension:
                ee_extensions.append(HeartbeatExtension().create(
                    HeartbeatMode.PEER_ALLOWED_TO_SEND))

        encryptedExtensions = EncryptedExtensions().create(ee_extensions)
        self._queue_message(encryptedExtensions)

        if selected_psk is None:

            # optionally send the client a certificate request
            if reqCert:

                # the context SHALL be zero length except in post-handshake
                ctx = b''

                # Get list of valid Signing Algorithms
                # we don't support DSA for client certificates yet
                cr_settings = settings.validate()
                cr_settings.dsaSigHashes = []
                valid_sig_algs = self._sigHashesToList(cr_settings)
                assert valid_sig_algs

                certificate_request = CertificateRequest(self.version)
                certificate_request.create(context=ctx, sig_algs=valid_sig_algs)
                self._queue_message(certificate_request)

            certificate = Certificate(CertificateType.x509, self.version)
            certificate.create(serverCertChain, bytearray())
            self._queue_message(certificate)

            certificate_verify = CertificateVerify(self.version)

            signature_scheme = getattr(SignatureScheme, scheme)

            signature_context = \
                KeyExchange.calcVerifyBytes((3, 4), self._handshake_hash,
                                            signature_scheme, None, None, None,
                                            prf_name, b'server')

            if signature_scheme in (SignatureScheme.ed25519,
                    SignatureScheme.ed448):
                hashName = "intrinsic"
                padType = None
                saltLen = None
                sig_func = privateKey.hashAndSign
                ver_func = privateKey.hashAndVerify
            elif signature_scheme[1] == SignatureAlgorithm.ecdsa:
                hashName = HashAlgorithm.toRepr(signature_scheme[0])
                padType = None
                saltLen = None
                sig_func = privateKey.sign
                ver_func = privateKey.verify
            else:
                padType = SignatureScheme.getPadding(scheme)
                hashName = SignatureScheme.getHash(scheme)
                saltLen = getattr(hashlib, hashName)().digest_size
                sig_func = privateKey.sign
                ver_func = privateKey.verify

            signature = sig_func(signature_context,
                                 padType,
                                 hashName,
                                 saltLen)
            if not ver_func(signature, signature_context,
                            padType,
                            hashName,
                            saltLen):
                for result in self._sendError(
                        AlertDescription.internal_error,
                        "Certificate Verify signature failed"):
                    yield result
            certificate_verify.create(signature, signature_scheme)

            self._queue_message(certificate_verify)

        finished_key = HKDF_expand_label(sr_handshake_traffic_secret,
                                         b"finished", b'', prf_size, prf_name)
        verify_data = secureHMAC(finished_key,
                                 self._handshake_hash.digest(prf_name),
                                 prf_name)

        finished = Finished(self.version, prf_size).create(verify_data)

        self._queue_message(finished)
        for result in self._queue_flush():
            yield result

        self._changeReadState()

        # Master secret
        secret = derive_secret(secret, bytearray(b'derived'), None, prf_name)
        secret = secureHMAC(secret, bytearray(prf_size), prf_name)

        cl_app_traffic = derive_secret(secret, bytearray(b'c ap traffic'),
                                       self._handshake_hash, prf_name)
        sr_app_traffic = derive_secret(secret, bytearray(b's ap traffic'),
                                       self._handshake_hash, prf_name)
        self._recordLayer.calcTLS1_3PendingState(serverHello.cipher_suite,
                                                 cl_app_traffic,
                                                 sr_app_traffic,
                                                 settings
                                                 .cipherImplementations)

        # all the messages sent by the server after the Finished message
        # MUST be encrypted with ap traffic secret, even if they regard
        # problems in processing client Certificate, CertificateVerify or
        # Finished messages
        self._changeWriteState()

        client_cert_chain = None
        #Get [Certificate,] (if was requested)
        if reqCert and selected_psk is None:
            for result in self._getMsg(ContentType.handshake,
                                       HandshakeType.certificate,
                                       CertificateType.x509):
                if result in (0, 1):
                    yield result
                else:
                    break
            client_certificate = result
            assert isinstance(client_certificate, Certificate)
            client_cert_chain = client_certificate.cert_chain

        #Get and check CertificateVerify, if relevant
        cli_cert_verify_hh = self._handshake_hash.copy()
        if client_cert_chain and client_cert_chain.getNumCerts():
            for result in self._getMsg(ContentType.handshake,
                                       HandshakeType.certificate_verify):
                if result in (0, 1):
                    yield result
                else: break
            certificate_verify = result
            assert isinstance(certificate_verify, CertificateVerify)

            signature_scheme = certificate_verify.signatureAlgorithm

            valid_sig_algs = self._sigHashesToList(settings,
                                                   certList=client_cert_chain,
                                                   version=(3, 4))
            if signature_scheme not in valid_sig_algs:
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        "Invalid signature on Certificate Verify"):
                    yield result

            signature_context = \
                KeyExchange.calcVerifyBytes((3, 4), cli_cert_verify_hh,
                                            signature_scheme, None, None, None,
                                            prf_name, b'client')

            public_key = client_cert_chain.getEndEntityPublicKey()

            if signature_scheme in (SignatureScheme.ed25519,
                    SignatureScheme.ed448):
                hash_name = "intrinsic"
                pad_type = None
                salt_len = None
                ver_func = public_key.hashAndVerify
            elif signature_scheme[1] == SignatureAlgorithm.ecdsa:
                hash_name = HashAlgorithm.toRepr(signature_scheme[0])
                pad_type = None
                salt_len = None
                ver_func = public_key.verify
            else:
                scheme = SignatureScheme.toRepr(signature_scheme)
                pad_type = SignatureScheme.getPadding(scheme)
                hash_name = SignatureScheme.getHash(scheme)
                salt_len = getattr(hashlib, hash_name)().digest_size
                ver_func = public_key.verify

            if not ver_func(certificate_verify.signature,
                            signature_context,
                            pad_type,
                            hash_name,
                            salt_len):
                for result in self._sendError(
                        AlertDescription.decrypt_error,
                        "signature verification failed"):
                    yield result

        # as both exporter and resumption master secrets include handshake
        # transcript, we need to derive them early
        exporter_master_secret = derive_secret(secret,
                                               bytearray(b'exp master'),
                                               self._handshake_hash,
                                               prf_name)

        # verify Finished of client
        cl_finished_key = HKDF_expand_label(cl_handshake_traffic_secret,
                                            b"finished", b'',
                                            prf_size, prf_name)
        cl_verify_data = secureHMAC(cl_finished_key,
                                    self._handshake_hash.digest(prf_name),
                                    prf_name)
        for result in self._getMsg(ContentType.handshake,
                                   HandshakeType.finished,
                                   prf_size):
            if result in (0, 1):
                yield result
            else:
                break
        cl_finished = result
        assert isinstance(cl_finished, Finished)
        if cl_finished.verify_data != cl_verify_data:
            for result in self._sendError(
                    AlertDescription.decrypt_error,
                    "Finished value is not valid"):
                yield result

        # disallow CCS messages after handshake
        self._middlebox_compat_mode = False

        resumption_master_secret = derive_secret(secret,
                                                 bytearray(b'res master'),
                                                 self._handshake_hash,
                                                 prf_name)

        self._first_handshake_hashes = self._handshake_hash.copy()

        self.session = Session()
        self.extendedMasterSecret = True
        server_name = None
        if clientHello.server_name:
            server_name = clientHello.server_name.decode('utf-8')

        app_proto = None
        alpnExt = encryptedExtensions.getExtension(ExtensionType.alpn)
        if alpnExt:
            app_proto = alpnExt.protocol_names[0]

        if not client_cert_chain and resumed_client_cert_chain:
            client_cert_chain = resumed_client_cert_chain

        self.session.create(secret,
                            bytearray(b''),  # no session_id
                            serverHello.cipher_suite,
                            bytearray(b''),  # no SRP
                            client_cert_chain,
                            serverCertChain,
                            None,
                            False,
                            server_name,
                            encryptThenMAC=False,
                            extendedMasterSecret=True,
                            appProto=app_proto,
                            cl_app_secret=cl_app_traffic,
                            sr_app_secret=sr_app_traffic,
                            exporterMasterSecret=exporter_master_secret,
                            resumptionMasterSecret=resumption_master_secret,
                            # NOTE it must be a reference, not a copy
                            tickets=self.tickets)

        # switch to application_traffic_secret for client packets
        self._changeReadState()

        for result in self._serverSendTickets(settings):
            yield result

        yield "finished"

    def _serverGetClientHello(self, settings, private_key, cert_chain,
                              verifierDB,
                              sessionCache, anon, alpn, sni):
        # Tentatively set version to most-desirable version, so if an error
        # occurs parsing the ClientHello, this will be the version we'll use
        # for the error alert
        # If TLS 1.3 is enabled, use the "compatible" TLS 1.2 version
        self.version = min(settings.maxVersion, (3, 3))

        self._pre_client_hello_handshake_hash = self._handshake_hash.copy()
        #Get ClientHello
        for result in self._getMsg(ContentType.handshake,
                                   HandshakeType.client_hello):
            if result in (0,1): yield result
            else: break
        clientHello = result

        # check if the ClientHello and its extensions are well-formed

        #If client's version is too low, reject it
        real_version = clientHello.client_version
        if real_version >= (3, 3):
            ext = clientHello.getExtension(ExtensionType.supported_versions)
            if ext:
                for v in ext.versions:
                    if v in KNOWN_VERSIONS and v > real_version:
                        real_version = v
        if real_version < settings.minVersion:
            self.version = settings.minVersion
            for result in self._sendError(\
                  AlertDescription.protocol_version,
                  "Too old version: %s" % str(clientHello.client_version)):
                yield result

        # there MUST be at least one value in both of those
        if not clientHello.cipher_suites or \
                not clientHello.compression_methods:
            for result in self._sendError(
                    AlertDescription.decode_error,
                    "Malformed Client Hello message"):
                yield result

        # client hello MUST advertise uncompressed method
        if 0 not in clientHello.compression_methods:
            for result in self._sendError(
                    AlertDescription.illegal_parameter,
                    "Client Hello missing uncompressed method"):
                yield result

        # the list of signatures methods is defined as <2..2^16-2>, which
        # means it can't be empty, but it's only applicable to TLSv1.2 protocol
        ext = clientHello.getExtension(ExtensionType.signature_algorithms)
        if clientHello.client_version >= (3, 3) and ext and not ext.sigalgs:
            for result in self._sendError(
                    AlertDescription.decode_error,
                    "Malformed signature_algorithms extension"):
                yield result

        # Sanity check the ALPN extension
        alpnExt = clientHello.getExtension(ExtensionType.alpn)
        if alpnExt:
            if not alpnExt.protocol_names:
                for result in self._sendError(
                        AlertDescription.decode_error,
                        "Client sent empty list of ALPN names"):
                    yield result
            for protocolName in alpnExt.protocol_names:
                if not protocolName:
                    for result in self._sendError(
                            AlertDescription.decode_error,
                            "Client sent empty name in ALPN extension"):
                        yield result

        # Sanity check the SNI extension
        sniExt = clientHello.getExtension(ExtensionType.server_name)
        # check if extension is well formed
        if sniExt and (not sniExt.extData or not sniExt.serverNames):
            for result in self._sendError(
                    AlertDescription.decode_error,
                    "Recevived SNI extension is malformed"):
                yield result
        if sniExt and sniExt.hostNames:
            # RFC 6066 limitation
            if len(sniExt.hostNames) > 1:
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        "Client sent multiple host names in SNI extension"):
                    yield result
            if not sniExt.hostNames[0]:
                for result in self._sendError(
                        AlertDescription.decode_error,
                        "Received SNI extension is malformed"):
                    yield result
            try:
                name = sniExt.hostNames[0].decode('ascii', 'strict')
            except UnicodeDecodeError:
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        "Host name in SNI is not valid ASCII"):
                    yield result
            if not is_valid_hostname(name):
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        "Host name in SNI is not valid DNS name"):
                    yield result

        # sanity check the EMS extension
        emsExt = clientHello.getExtension(ExtensionType.extended_master_secret)
        if emsExt and emsExt.extData:
            for result in self._sendError(
                    AlertDescription.decode_error,
                    "Non empty payload of the Extended "
                    "Master Secret extension"):
                yield result

        # sanity check the TLS 1.3 extensions
        ver_ext = clientHello.getExtension(ExtensionType.supported_versions)
        if ver_ext and (3, 4) in ver_ext.versions:
            psk = clientHello.getExtension(ExtensionType.pre_shared_key)
            psk_modes = clientHello.getExtension(
                ExtensionType.psk_key_exchange_modes)
            key_share = clientHello.getExtension(ExtensionType.key_share)
            sup_groups = clientHello.getExtension(
                ExtensionType.supported_groups)

            pha = clientHello.getExtension(ExtensionType.post_handshake_auth)
            if pha:
                if pha.extData:
                    for result in self._sendError(
                            AlertDescription.decode_error,
                            "Invalid encoding of post_handshake_auth extension"
                            ):
                        yield result
                self._pha_supported = True

            key_exchange = None

            if psk_modes:
                if not psk_modes.modes:
                    for result in self._sendError(
                            AlertDescription.decode_error,
                            "Empty psk_key_exchange_modes extension"):
                        yield result
            # psk_ke
            if psk:
                if not psk.identities:
                    for result in self._sendError(
                            AlertDescription.decode_error,
                            "No identities in PSK extension"):
                        yield result
                if not psk.binders:
                    for result in self._sendError(
                            AlertDescription.decode_error,
                            "No binders in PSK extension"):
                        yield result
                if len(psk.identities) != len(psk.binders):
                    for result in self._sendError(
                            AlertDescription.illegal_parameter,
                            "Number of identities does not match number of "
                            "binders in PSK extension"):
                        yield result
                if any(not i.identity for i in psk.identities):
                    for result in self._sendError(
                            AlertDescription.decoder_error,
                            "Empty identity in PSK extension"):
                        yield result
                if any(not i for i in psk.binders):
                    for result in self._sendError(
                            AlertDescription.decoder_error,
                            "Empty binder in PSK extension"):
                        yield result
                if psk is not clientHello.extensions[-1]:
                    for result in self._sendError(
                            AlertDescription.illegal_parameter,
                            "PSK extension not last in client hello"):
                        yield result
                if not psk_modes:
                    for result in self._sendError(
                            AlertDescription.missing_extension,
                            "PSK extension without psk_key_exchange_modes "
                            "extension"):
                        yield result

                if PskKeyExchangeMode.psk_dhe_ke not in psk_modes.modes:
                    key_exchange = "psk_ke"
            # cert
            if not key_exchange:
                if not sup_groups:
                    for result in self._sendError(
                            AlertDescription.missing_extension,
                            "Missing supported_groups extension"):
                        yield result
                if not key_share:
                    for result in self._sendError(
                            AlertDescription.missing_extension,
                            "Missing key_share extension"):
                        yield result

                if not sup_groups.groups:
                    for result in self._sendError(
                            AlertDescription.decode_error,
                            "Empty supported_groups extension"):
                        yield result
                if key_share.client_shares is None:
                    for result in self._sendError(
                            AlertDescription.decode_error,
                            "Empty key_share extension"):
                        yield result

                # check supported_groups
                if TLS_1_3_FORBIDDEN_GROUPS.intersection(sup_groups.groups):
                    for result in self._sendError(
                            AlertDescription.illegal_parameter,
                            "Client advertised in TLS 1.3 Client Hello a key "
                            "exchange group forbidden in TLS 1.3"):
                        yield result

                # Check key_share
                mismatch = next((i for i in key_share.client_shares
                                 if i.group not in sup_groups.groups), None)
                if mismatch:
                    for result in self._sendError(
                            AlertDescription.illegal_parameter,
                            "Client sent key share for "
                            "group it did not advertise "
                            "support for: {0}"
                            .format(GroupName.toStr(mismatch))):
                        yield result

                key_share_ids = [i.group for i in key_share.client_shares]
                if len(set(key_share_ids)) != len(key_share_ids):
                    for result in self._sendError(
                            AlertDescription.illegal_parameter,
                            "Client sent multiple key shares for the same "
                            "group"):
                        yield result

                group_ids = sup_groups.groups
                diff = set(group_ids) - set(key_share_ids)
                if key_share_ids != [i for i in group_ids if i not in diff]:
                    for result in self._sendError(
                            AlertDescription.illegal_parameter,
                            "Client sent key shares in different order than "
                            "the advertised groups."):
                        yield result

                sig_algs = clientHello.getExtension(
                    ExtensionType.signature_algorithms)
                if (not psk_modes or not psk) and sig_algs:
                    key_exchange = "cert"

            # psk_dhe_ke
            if not key_exchange and psk:
                key_exchange = "psk_dhe_ke"

            if not key_exchange:
                for result in self._sendError(
                        AlertDescription.missing_extension,
                        "Missing extension"):
                    yield result

            early_data = clientHello.getExtension(ExtensionType.early_data)
            if early_data:
                if early_data.extData:
                    for result in self._sendError(
                            AlertDescription.decode_error,
                            "malformed early_data extension"):
                        yield result
                if not psk:
                    for result in self._sendError(
                            AlertDescription.illegal_parameter,
                            "early_data without PSK extension"):
                        yield result
                # if early data comes from version we don't support, client
                # MUST (section D.3 draft 28) abort the connection so we
                # enable early data tolerance only when versions match
                self._recordLayer.max_early_data = settings.max_early_data
                self._recordLayer.early_data_ok = True

        # negotiate the protocol version for the connection
        high_ver = None
        if ver_ext:
            high_ver = getFirstMatching(settings.versions,
                                        ver_ext.versions)
            if not high_ver:
                for result in self._sendError(
                        AlertDescription.protocol_version,
                        "supported_versions did not include version we "
                        "support"):
                    yield result
        if high_ver:
            # when we selected TLS 1.3, we cannot set the record layer to
            # it as well as that also switches it to a mode where the
            # content type is encrypted
            # use the backwards compatible TLS 1.2 version instead
            self.version = min((3, 3), high_ver)
            version = high_ver
        elif clientHello.client_version > settings.maxVersion:
            # in TLS 1.3 the version is negotiatied with extension,
            # but the settings use the (3, 4) as the max version
            self.version = min(settings.maxVersion, (3, 3))
            version = self.version
        else:
            #Set the version to the client's version
            self.version = min(clientHello.client_version, (3, 3))
            version = self.version

        #Detect if the client performed an inappropriate fallback.
        if version < settings.maxVersion and \
                CipherSuite.TLS_FALLBACK_SCSV in clientHello.cipher_suites:
            for result in self._sendError(
                    AlertDescription.inappropriate_fallback):
                yield result

        # TODO when TLS 1.3 is final, check the client hello random for
        # downgrade too

        # start negotiating the parameters of the connection

        sni_ext = clientHello.getExtension(ExtensionType.server_name)
        if sni_ext:
            name = sni_ext.hostNames[0].decode('ascii', 'strict')
            # warn the client if the name didn't match the expected value
            if sni and sni != name:
                alert = Alert().create(AlertDescription.unrecognized_name,
                                       AlertLevel.warning)
                for result in self._sendMsg(alert):
                    yield result

        #Check if there's intersection between supported curves by client and
        #server
        clientGroups = clientHello.getExtension(ExtensionType.supported_groups)
        # in case the client didn't advertise any curves, we can pick any so
        # enable ECDHE
        ecGroupIntersect = True
        # if there is no extension, then enable DHE
        ffGroupIntersect = True
        if clientGroups is not None:
            clientGroups = clientGroups.groups
            if not clientGroups:
                for result in self._sendError(
                        AlertDescription.decode_error,
                        "Received malformed supported_groups extension"):
                    yield result
            serverGroups = self._curveNamesToList(settings)
            ecGroupIntersect = getFirstMatching(clientGroups, serverGroups)
            # RFC 7919 groups
            serverGroups = self._groupNamesToList(settings)
            ffGroupIntersect = getFirstMatching(clientGroups, serverGroups)
            # if there is no overlap, but there are no FFDHE groups listed,
            # allow DHE, prohibit otherwise
            if not ffGroupIntersect:
                if clientGroups and \
                        any(i for i in clientGroups if i in range(256, 512)):
                    ffGroupIntersect = False
                else:
                    ffGroupIntersect = True

        # Check and save clients heartbeat extension mode
        heartbeat_ext = clientHello.getExtension(ExtensionType.heartbeat)
        if heartbeat_ext:
            if heartbeat_ext.mode == HeartbeatMode.PEER_ALLOWED_TO_SEND:
                if settings.heartbeat_response_callback:
                    self.heartbeat_can_send = True
                    self.heartbeat_response_callback = settings.\
                        heartbeat_response_callback
            elif heartbeat_ext.mode == HeartbeatMode.PEER_NOT_ALLOWED_TO_SEND:
                self.heartbeat_can_send = False
            else:
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        "Received invalid value in Heartbeat extension"):
                    yield result
            self.heartbeat_supported = True
            self.heartbeat_can_receive = True

        size_limit_ext = clientHello.getExtension(
            ExtensionType.record_size_limit)
        if size_limit_ext:
            if size_limit_ext.record_size_limit is None:
                for result in self._sendError(
                        AlertDescription.decode_error,
                        "Malformed record_size_limit extension"):
                    yield result
            if not 64 <= size_limit_ext.record_size_limit:
                for result in self._sendError(
                        AlertDescription.illegal_parameter,
                        "Invalid value in record_size_limit extension"):
                    yield result
            if settings.record_size_limit:
                # in TLS 1.3 handshake is encrypted so we need to switch
                # to sending smaller messages right away
                if version >= (3, 4):
                    # the client can send bigger values because it may
                    # know protocol versions or extensions we don't know about
                    # (but we need to still clamp it to protocol limit)
                    self._send_record_limit = min(
                        2**14, size_limit_ext.record_size_limit - 1)
                    # the record layer excludes content type, extension doesn't
                    # thus the "-1)
                    self._recv_record_limit = min(2**14,
                        settings.record_size_limit - 1)
                else:
                    # but in TLS 1.2 and earlier we need to postpone it till
                    # handling of Finished
                    self._peer_record_size_limit = min(
                        2**14, size_limit_ext.record_size_limit)

        #Now that the version is known, limit to only the ciphers available to
        #that version and client capabilities.
        cipherSuites = []
        if verifierDB:
            if cert_chain:
                cipherSuites += \
                    CipherSuite.getSrpCertSuites(settings, version)
            cipherSuites += CipherSuite.getSrpSuites(settings, version)
        elif cert_chain:
            if ecGroupIntersect or ffGroupIntersect:
                cipherSuites += CipherSuite.getTLS13Suites(settings,
                                                           version)
            if ecGroupIntersect:
                cipherSuites += CipherSuite.getEcdsaSuites(settings, version)
                cipherSuites += CipherSuite.getEcdheCertSuites(settings,
                                                               version)
            if ffGroupIntersect:
                cipherSuites += CipherSuite.getDheCertSuites(settings,
                                                             version)
                cipherSuites += CipherSuite.getDheDsaSuites(settings,
                                                            version)
            cipherSuites += CipherSuite.getCertSuites(settings, version)
        elif anon:
            cipherSuites += CipherSuite.getAnonSuites(settings, version)
            cipherSuites += CipherSuite.getEcdhAnonSuites(settings,
                                                          version)
        elif settings.pskConfigs:
            cipherSuites += CipherSuite.getTLS13Suites(settings,
                                                       version)
        else:
            assert False
        cipherSuites = CipherSuite.filterForVersion(cipherSuites,
                                                    minVersion=version,
                                                    maxVersion=version)

        #If resumption was requested and we have a session cache...
        if clientHello.session_id and sessionCache:
            session = None

            # Check if the session there is good enough and consistent with
            # new Client Hello
            try:
                session = sessionCache[clientHello.session_id]
                if not session.resumable:
                    raise AssertionError()
                # Check if we are willing to use that old cipher still
                if session.cipherSuite not in cipherSuites:
                    session = None
                    raise KeyError()
                # Check for consistency with ClientHello
                # see RFC 5246 section 7.4.1.2, description of
                # cipher_suites
                if session.cipherSuite not in clientHello.cipher_suites:
                    for result in self._sendError(
                            AlertDescription.illegal_parameter):
                        yield result
                if clientHello.srp_username:
                    if not session.srpUsername or \
                            clientHello.srp_username != \
                            bytearray(session.srpUsername, "utf-8"):
                        for result in self._sendError(
                                AlertDescription.handshake_failure):
                            yield result
                if clientHello.server_name:
                    if not session.serverName or \
                            clientHello.server_name != \
                            bytearray(session.serverName, "utf-8"):
                        for result in self._sendError(
                                AlertDescription.handshake_failure):
                            yield result
                if session.encryptThenMAC and \
                        not clientHello.getExtension(
                                ExtensionType.encrypt_then_mac):
                    for result in self._sendError(
                            AlertDescription.illegal_parameter):
                        yield result
                # if old session used EMS, new connection MUST use EMS
                if session.extendedMasterSecret and \
                        not clientHello.getExtension(
                                ExtensionType.extended_master_secret):
                    # RFC 7627, section 5.2 explicitly requires
                    # handshake_failure
                    for result in self._sendError(
                            AlertDescription.handshake_failure):
                        yield result
                # if old session didn't use EMS but new connection
                # advertises EMS, create a new session
                elif not session.extendedMasterSecret and \
                        clientHello.getExtension(
                                ExtensionType.extended_master_secret):
                    session = None
            except KeyError:
                pass

            #If a session is found..
            if session:
                #Send ServerHello
                extensions = []
                if session.encryptThenMAC:
                    self._recordLayer.encryptThenMAC = True
                    mte = TLSExtension().create(ExtensionType.encrypt_then_mac,
                                                bytearray(0))
                    extensions.append(mte)
                if session.extendedMasterSecret:
                    ems = TLSExtension().create(ExtensionType.
                                                extended_master_secret,
                                                bytearray(0))
                    extensions.append(ems)
                secureRenego = False
                renegoExt = clientHello.\
                    getExtension(ExtensionType.renegotiation_info)
                if renegoExt:
                    if renegoExt.renegotiated_connection:
                        for result in self._sendError(
                                AlertDescription.handshake_failure):
                            yield result
                    secureRenego = True
                elif CipherSuite.TLS_EMPTY_RENEGOTIATION_INFO_SCSV in \
                        clientHello.cipher_suites:
                    secureRenego = True
                if secureRenego:
                    extensions.append(RenegotiationInfoExtension()
                                      .create(bytearray(0)))
                selectedALPN = None
                if alpn:
                    alpnExt = clientHello.getExtension(ExtensionType.alpn)
                    if alpnExt:
                        for protocolName in alpnExt.protocol_names:
                            if protocolName in alpn:
                                ext = ALPNExtension().create([protocolName])
                                extensions.append(ext)
                                selectedALPN = protocolName
                                break
                        else:
                            for result in self._sendError(
                                    AlertDescription.no_application_protocol,
                                    "No commonly supported application layer"
                                    "protocol supported"):
                                yield result

                heartbeat_ext = clientHello.getExtension(
                    ExtensionType.heartbeat)
                if heartbeat_ext:
                    if heartbeat_ext.mode == HeartbeatMode.PEER_ALLOWED_TO_SEND:
                        self.heartbeat_can_send = True
                    elif heartbeat_ext.mode == \
                            HeartbeatMode.PEER_NOT_ALLOWED_TO_SEND:
                        self.heartbeat_can_send = False
                    else:
                        for result in self._sendError(
                                AlertDescription.illegal_parameter,
                                "Client sent invalid Heartbeat extension"):
                            yield result
                    heartbeat = HeartbeatExtension().create(
                        HeartbeatMode.PEER_ALLOWED_TO_SEND)
                    self.heartbeat_can_receive = True
                    self.heartbeat_supported = True
                    extensions.append(heartbeat)
                record_limit = clientHello.getExtension(
                    ExtensionType.record_size_limit)
                if record_limit and settings.record_size_limit:
                    extensions.append(RecordSizeLimitExtension().create(
                        min(2**14, settings.record_size_limit)))

                # don't send empty extensions
                if not extensions:
                    extensions = None
                serverHello = ServerHello()
                serverHello.create(version, getRandomBytes(32),
                                   session.sessionID, session.cipherSuite,
                                   CertificateType.x509, None, None,
                                   extensions=extensions)
                for result in self._sendMsg(serverHello):
                    yield result

                #Calculate pending connection states
                self._calcPendingStates(session.cipherSuite, 
                                        session.masterSecret,
                                        clientHello.random, 
                                        serverHello.random,
                                        settings.cipherImplementations)

                #Exchange ChangeCipherSpec and Finished messages
                for result in self._sendFinished(session.masterSecret,
                                                 session.cipherSuite,
                                                 settings=settings):
                    yield result
                for result in self._getFinished(session.masterSecret,
                                                session.cipherSuite):
                    yield result

                #Set the session
                self.session = session
                self._clientRandom = clientHello.random
                self._serverRandom = serverHello.random
                self.session.appProto = selectedALPN
                yield None # Handshake done!

        #Calculate the first cipher suite intersection.
        #This is the 'privileged' ciphersuite.  We'll use it if we're
        #doing a new negotiation.  In fact,
        #the only time we won't use it is if we're resuming a
        #session, in which case we use the ciphersuite from the session.
        #
        #Given the current ciphersuite ordering, this means we prefer SRP
        #over non-SRP.

        try:
            cipherSuite, sig_scheme, cert_chain, private_key = \
                    self._server_select_certificate(settings, clientHello,
                                                    cipherSuites, cert_chain,
                                                    private_key, version)
        except TLSHandshakeFailure as err:
            for result in self._sendError(
                    AlertDescription.handshake_failure,
                    str(err)):
                yield result
        except TLSInsufficientSecurity as err:
            for result in self._sendError(
                    AlertDescription.insufficient_security,
                    str(err)):
                yield result
        except TLSIllegalParameterException as err:
            for result in self._sendError(
                    AlertDescription.illegal_parameter,
                    str(err)):
                yield result

        #If an RSA suite is chosen, check for certificate type intersection
        if (cipherSuite in CipherSuite.certAllSuites or
            cipherSuite in CipherSuite.ecdheEcdsaSuites) \
                    and CertificateType.x509 \
                    not in clientHello.certificate_types:
            for result in self._sendError(\
                    AlertDescription.handshake_failure,
                    "the client doesn't support my certificate type"):
                yield result

        # when we have selected TLS 1.3, check if we don't have to ask for
        # a new client hello
        if version > (3, 3):
            self.version = version
            hrr_ext = []

            # check if we have good key share
            share = clientHello.getExtension(ExtensionType.key_share)
            if share:
                share_ids = [i.group for i in share.client_shares]
                acceptable_ids = [getattr(GroupName, i) for i in
                                  chain(settings.keyShares, settings.eccCurves,
                                        settings.dhGroups)]
                for selected_group in acceptable_ids:
                    if selected_group in share_ids:
                        cl_key_share = next(i for i in share.client_shares
                                            if i.group == selected_group)
                        break
                else:
                    # if no key share is acceptable, pick one of the supported
                    # groups that we support
                    supported = clientHello.getExtension(ExtensionType
                                                         .supported_groups)
                    supported_ids = supported.groups
                    selected_group = next((i for i in acceptable_ids
                                           if i in supported_ids), None)
                    if not selected_group:
                        for result in self._sendError(AlertDescription
                                                      .handshake_failure,
                                                      "No acceptable group "
                                                      "advertised by client"):
                            yield result
                    hrr_ks = HRRKeyShareExtension().create(selected_group)
                    hrr_ext.append(hrr_ks)

            if hrr_ext:
                cookie = TLSExtension(extType=ExtensionType.cookie)
                cookie = cookie.create(bytearray(b'\x00\x20') +
                                       getRandomBytes(32))
                hrr_ext.append(cookie)

            if hrr_ext:
                clientHello1 = clientHello

                # create synthetic handshake hash of the first Client Hello
                prf_name, prf_size = self._getPRFParams(cipherSuite)

                client_hello_hash = self._handshake_hash.digest(prf_name)
                self._handshake_hash = HandshakeHashes()
                writer = Writer()
                writer.add(HandshakeType.message_hash, 1)
                writer.addVarSeq(client_hello_hash, 1, 3)
                self._handshake_hash.update(writer.bytes)

                # send the version that was really selected
                vers = SrvSupportedVersionsExtension().create(version)
                hrr_ext.append(vers)

                # send the HRR
                hrr = ServerHello()
                # version is hardcoded in TLS 1.3, and real version
                # is sent as extension
                hrr.create((3, 3), TLS_1_3_HRR, clientHello.session_id,
                           cipherSuite, extensions=hrr_ext)

                msgs = [hrr]
                if clientHello.session_id:
                    ccs = ChangeCipherSpec().create()
                    msgs.append(ccs)
                for result in self._sendMsgs(msgs):
                    yield result
                self._ccs_sent = True

                # copy for calculating PSK binders
                self._pre_client_hello_handshake_hash = \
                    self._handshake_hash.copy()

                for result in self._getMsg(ContentType.handshake,
                                           HandshakeType.client_hello):
                    if result in (0, 1):
                        yield result
                    else:
                        break
                clientHello = result

                # verify that the new key share is present
                ext = clientHello.getExtension(ExtensionType.key_share)
                if not ext:
                    for result in self._sendError(AlertDescription
                                                  .missing_extension,
                                                  "Key share missing in "
                                                  "Client Hello"):
                        yield result

                # here we're assuming that the HRR was sent because of
                # missing key share, that may not always be the case
                if len(ext.client_shares) != 1:
                    for result in self._sendError(AlertDescription
                                                  .illegal_parameter,
                                                  "Multiple key shares in "
                                                  "second Client Hello"):
                        yield result
                if ext.client_shares[0].group != selected_group:
                    for result in self._sendError(AlertDescription
                                                  .illegal_parameter,
                                                  "Client key share does not "
                                                  "match Hello Retry Request"):
                        yield result

                # here we're assuming no 0-RTT and possibly no session
                # resumption
                # verify that new client hello is like the old client hello
                # with the exception of changes requested in HRR
                old_ext = clientHello1.getExtension(ExtensionType.key_share)
                new_ext = clientHello.getExtension(ExtensionType.key_share)
                old_ext.client_shares = new_ext.client_shares

                # TODO when 0-RTT supported, remove early_data from old hello

                if cookie:
                    # insert the extension at the same place in the old hello
                    # as it is in the new hello so that later binary compare
                    # works
                    for i, ext in enumerate(clientHello.extensions):
                        if ext.extType == ExtensionType.cookie:
                            if ext.extData != cookie.extData:
                                eType = AlertDescription.illegal_parameter
                                eText = "Malformed cookie extension"
                                for result in self._sendError(eType, eText):
                                    yield result
                            clientHello1.extensions.insert(i, ext)
                            break
                    else:
                        for result in self._sendError(AlertDescription
                                                      .missing_extension,
                                                      "Second client hello "
                                                      "does not contain "
                                                      "cookie extension"):
                            yield result

                # also padding extension may change
                old_ext = clientHello1.getExtension(
                    ExtensionType.client_hello_padding)
                new_ext = clientHello.getExtension(
                    ExtensionType.client_hello_padding)
                if old_ext != new_ext:
                    if old_ext is None and new_ext:
                        for i, ext in enumerate(clientHello.extensions):
                            if ext.extType == \
                                    ExtensionType.client_hello_padding:
                                clientHello1.extensions.insert(i, ext)
                                break
                    elif old_ext and new_ext is None:
                        # extension was removed, so remove it here too
                        clientHello1.extensions[:] = \
                            (i for i in clientHello1.extensions
                             if i.extType !=
                             ExtensionType.client_hello_padding)
                    else:
                        old_ext.paddingData = new_ext.paddingData

                # PSKs not compatible with cipher suite MAY
                # be removed, but must have updated obfuscated ticket age
                # and binders
                old_ext = clientHello1.getExtension(
                    ExtensionType.pre_shared_key)
                new_ext = clientHello.getExtension(
                    ExtensionType.pre_shared_key)
                if new_ext and old_ext:
                    clientHello1.extensions[-1] = new_ext
                    if clientHello.extensions[-1] is not new_ext:
                        for result in self._sendError(
                                AlertDescription.illegal_parameter,
                                "PSK extension not last in client hello"):
                            yield result
                # early_data extension MUST be dropped
                old_ext = clientHello1.getExtension(ExtensionType.early_data)
                if old_ext:
                    clientHello1.extensions.remove(old_ext)

                if clientHello1 != clientHello:
                    for result in self._sendError(AlertDescription
                                                  .illegal_parameter,
                                                  "Old Client Hello does not "
                                                  "match the updated Client "
                                                  "Hello"):
                        yield result

        # If resumption was not requested, or
        # we have no session cache, or
        # the client's session_id was not found in cache:
#pylint: disable = undefined-loop-variable
        yield (clientHello, version, cipherSuite, sig_scheme, private_key,
               cert_chain)
#pylint: enable = undefined-loop-variable

    def _serverSRPKeyExchange(self, clientHello, serverHello, verifierDB,
                              cipherSuite, privateKey, serverCertChain,
                              settings):
        """Perform the server side of SRP key exchange"""
        try:
            sigHash, serverCertChain, privateKey = \
                self._pickServerKeyExchangeSig(settings, clientHello,
                                               serverCertChain,
                                               privateKey)
        except TLSHandshakeFailure as alert:
            for result in self._sendError(
                    AlertDescription.handshake_failure,
                    str(alert)):
                yield result

        keyExchange = SRPKeyExchange(cipherSuite,
                                     clientHello,
                                     serverHello,
                                     privateKey,
                                     verifierDB)

        #Create ServerKeyExchange, signing it if necessary
        try:
            serverKeyExchange = keyExchange.makeServerKeyExchange(sigHash)
        except TLSUnknownPSKIdentity:
            for result in self._sendError(
                    AlertDescription.unknown_psk_identity):
                yield result
        except TLSInsufficientSecurity:
            for result in self._sendError(
                    AlertDescription.insufficient_security):
                yield result

        #Send ServerHello[, Certificate], ServerKeyExchange,
        #ServerHelloDone
        msgs = []
        msgs.append(serverHello)
        if cipherSuite in CipherSuite.srpCertSuites:
            certificateMsg = Certificate(CertificateType.x509)
            certificateMsg.create(serverCertChain)
            msgs.append(certificateMsg)
        msgs.append(serverKeyExchange)
        msgs.append(ServerHelloDone())
        for result in self._sendMsgs(msgs):
            yield result

        #Get and check ClientKeyExchange
        for result in self._getMsg(ContentType.handshake,
                                  HandshakeType.client_key_exchange,
                                  cipherSuite):
            if result in (0,1): yield result
            else: break
        try:
            premasterSecret = keyExchange.processClientKeyExchange(result)
        except TLSIllegalParameterException:
            for result in self._sendError(AlertDescription.illegal_parameter,
                                          "Suspicious A value"):
                yield result
        except TLSDecodeError as alert:
            for result in self._sendError(AlertDescription.decode_error,
                                          str(alert)):
                yield result

        yield premasterSecret, privateKey, serverCertChain

    def _server_select_certificate(self, settings, client_hello,
                                   cipher_suites, cert_chain,
                                   private_key, version):
        """
        This method makes the decision on which certificate/key pair,
        signature algorithm and cipher to use based on the certificate.
        """

        last_cert = False
        possible_certs = []

        # Get client groups
        client_groups = client_hello. \
                getExtension(ExtensionType.supported_groups)
        if client_groups is not None:
            client_groups = client_groups.groups

        # If client did send signature_algorithms_cert use it,
        # otherwise fallback to signature_algorithms.
        # Client can also decide not to send sigalg extension
        client_sigalgs = \
                client_hello. \
                getExtension(ExtensionType.signature_algorithms_cert)
        if client_sigalgs is not None:
            client_sigalgs = \
                    client_hello. \
                    getExtension(ExtensionType.signature_algorithms_cert). \
                    sigalgs
        else:
            client_sigalgs = \
                    client_hello. \
                    getExtension(ExtensionType.signature_algorithms)
            if client_sigalgs is not None:
                client_sigalgs = \
                        client_hello. \
                        getExtension(ExtensionType.signature_algorithms). \
                        sigalgs
            else:
                client_sigalgs = []

        # Get all the certificates we can offer
        alt_certs = ((X509CertChain(i.certificates), i.key) for vh in
                     settings.virtual_hosts for i in vh.keys)
        certs = [(cert, key)
                 for cert, key in chain([(cert_chain, private_key)], alt_certs)]

        for cert, key in certs:

            # Check if this is the last (cert, key) pair we have to check
            if (cert, key) == certs[-1]:
                last_cert = True

            # Mandatory checks. If any one of these checks fail, the certificate
            # is not usuable.
            try:
                # Find a suitable ciphersuite based on the certificate
                ciphers = CipherSuite.filter_for_certificate(cipher_suites, cert)
                for cipher in ciphers:
                    if cipher in client_hello.cipher_suites:
                        break
                else:
                    if client_groups and \
                        any(i in range(256, 512) for i in client_groups) and \
                        any(i in CipherSuite.dhAllSuites
                            for i in client_hello.cipher_suites):
                            raise TLSInsufficientSecurity(
                                    "FFDHE groups not acceptable and no other common "
                                    "ciphers")
                    raise TLSHandshakeFailure("No mutual ciphersuite")

                # Find a signature algorithm based on the certificate
                try:
                    sig_scheme, _, _ = \
                        self._pickServerKeyExchangeSig(settings,
                                                       client_hello,
                                                       cert,
                                                       key,
                                                       version,
                                                       False)
                except TLSHandshakeFailure:
                    raise TLSHandshakeFailure(
                        "No common signature algorithms")

                # If the certificate is ECDSA, we must check curve compatibility
                if cert and cert.x509List[0].certAlg == 'ecdsa' and \
                        client_groups and client_sigalgs:
                    public_key = cert.getEndEntityPublicKey()
                    curve = public_key.curve_name
                    for name, aliases in CURVE_ALIASES.items():
                        if curve in aliases:
                            curve = getattr(GroupName, name)
                            break

                    if version <= (3, 3) and curve not in client_groups:
                        raise TLSHandshakeFailure(
                            "The curve in the public key is not "
                            "supported by the client: {0}" \
                                    .format(GroupName.toRepr(curve)))

                    if version >= (3, 4):
                        if GroupName.toRepr(curve) not in \
                                ('secp256r1', 'secp384r1', 'secp521r1'):
                            raise TLSIllegalParameterException(
                                    "Curve in public key is not supported "
                                    "in TLS1.3")

                # If all mandatory checks passed add
                # this as possible certificate we can use.
                possible_certs.append((cipher, sig_scheme, cert, key))

            except Exception:
                if last_cert and not possible_certs:
                    raise
                continue

            # Non-mandatory checks, if these fail the certificate is still usable
            # but we should try to find one that passes all the checks

            # Check if every certificate(except the self-signed root CA)
            # in the certificate chain is signed with a signature algorithm
            # supported by the client.
            if cert:
                cert_chain_ok = True
                for i in range(len(cert.x509List)):
                    if cert.x509List[i].issuer != cert.x509List[i].subject:
                        if cert.x509List[i].sigalg not in client_sigalgs:
                            cert_chain_ok = False
                            break
                if not cert_chain_ok:
                    if not last_cert:
                        continue
                    break

            # If all mandatory and non-mandatory checks passed
            # return the (cert, key) pair, cipher and sig_scheme
            return cipher, sig_scheme, cert, key

        # If we can't find cert that passed all the checks, return the first usable one.
        return possible_certs[0]


    def _serverCertKeyExchange(self, clientHello, serverHello, sigHashAlg,
                                serverCertChain, keyExchange,
                                reqCert, reqCAs, cipherSuite,
                                settings):
        #Send ServerHello, Certificate[, ServerKeyExchange]
        #[, CertificateRequest], ServerHelloDone
        msgs = []

        # If we verify a client cert chain, return it
        clientCertChain = None

        msgs.append(serverHello)
        msgs.append(Certificate(CertificateType.x509).create(serverCertChain))
        try:
            serverKeyExchange = keyExchange.makeServerKeyExchange(sigHashAlg)
        except TLSInternalError as alert:
            for result in self._sendError(
                    AlertDescription.internal_error,
                    str(alert)):
                yield result
        except TLSInsufficientSecurity as alert:
            for result in self._sendError(
                    AlertDescription.insufficient_security,
                    str(alert)):
                yield result
        if serverKeyExchange is not None:
            msgs.append(serverKeyExchange)
        if reqCert:
            certificateRequest = CertificateRequest(self.version)
            if not reqCAs:
                reqCAs = []
            cr_settings = settings.validate()
            # we don't support DSA in client certificates yet
            cr_settings.dsaSigHashes = []
            valid_sig_algs = self._sigHashesToList(cr_settings)
            certificateRequest.create([ClientCertificateType.rsa_sign,
                                       ClientCertificateType.ecdsa_sign],
                                      reqCAs,
                                      valid_sig_algs)
            msgs.append(certificateRequest)
        msgs.append(ServerHelloDone())
        for result in self._sendMsgs(msgs):
            yield result

        #Get [Certificate,] (if was requested)
        if reqCert:
            if self.version == (3,0):
                for result in self._getMsg((ContentType.handshake,
                                           ContentType.alert),
                                           HandshakeType.certificate,
                                           CertificateType.x509):
                    if result in (0,1): yield result
                    else: break
                msg = result

                if isinstance(msg, Alert):
                    #If it's not a no_certificate alert, re-raise
                    alert = msg
                    if alert.description != \
                            AlertDescription.no_certificate:
                        self._shutdown(False)
                        raise TLSRemoteAlert(alert)
                elif isinstance(msg, Certificate):
                    clientCertificate = msg
                    if clientCertificate.cert_chain and \
                            clientCertificate.cert_chain.getNumCerts() != 0:
                        clientCertChain = clientCertificate.cert_chain
                else:
                    raise AssertionError()
            elif self.version in ((3,1), (3,2), (3,3)):
                for result in self._getMsg(ContentType.handshake,
                                          HandshakeType.certificate,
                                          CertificateType.x509):
                    if result in (0,1): yield result
                    else: break
                clientCertificate = result
                if clientCertificate.cert_chain and \
                        clientCertificate.cert_chain.getNumCerts() != 0:
                    clientCertChain = clientCertificate.cert_chain
            else:
                raise AssertionError()

        #Get ClientKeyExchange
        for result in self._getMsg(ContentType.handshake,
                                  HandshakeType.client_key_exchange,
                                  cipherSuite):
            if result in (0,1): yield result
            else: break
        clientKeyExchange = result

        #Process ClientKeyExchange
        try:
            premasterSecret = \
                keyExchange.processClientKeyExchange(clientKeyExchange)
        except TLSIllegalParameterException as alert:
            for result in self._sendError(AlertDescription.illegal_parameter,
                                          str(alert)):
                yield result
        except TLSDecodeError as alert:
            for result in self._sendError(AlertDescription.decode_error,
                                          str(alert)):
                yield result

        #Get and check CertificateVerify, if relevant
        self._certificate_verify_handshake_hash = self._handshake_hash.copy()
        if clientCertChain:
            for result in self._getMsg(ContentType.handshake,
                                       HandshakeType.certificate_verify):
                if result in (0, 1):
                    yield result
                else: break
            certificateVerify = result
            signatureAlgorithm = None
            if self.version == (3, 3):
                valid_sig_algs = \
                    self._sigHashesToList(settings,
                                          certList=clientCertChain)
                if certificateVerify.signatureAlgorithm not in valid_sig_algs:
                    for result in self._sendError(
                            AlertDescription.illegal_parameter,
                            "Invalid signature algorithm in Certificate "
                            "Verify"):
                        yield result
                signatureAlgorithm = certificateVerify.signatureAlgorithm
            if not signatureAlgorithm and \
                    clientCertChain.x509List[0].certAlg == "ecdsa":
                signatureAlgorithm = (HashAlgorithm.sha1,
                                      SignatureAlgorithm.ecdsa)

            cvhh = self._certificate_verify_handshake_hash
            verify_bytes = KeyExchange.calcVerifyBytes(
                self.version,
                cvhh,
                signatureAlgorithm,
                premasterSecret,
                clientHello.random,
                serverHello.random,
                key_type=clientCertChain.x509List[0].certAlg)

            for result in self._check_certchain_with_settings(
                    clientCertChain,
                    settings):
                if result in (0, 1):
                    yield result
                else: break
            public_key = result

            if signatureAlgorithm and signatureAlgorithm in (
                    SignatureScheme.ed25519, SignatureScheme.ed448):
                hash_name = "intrinsic"
                salt_len = None
                padding = None
                ver_func = public_key.hashAndVerify
            elif not signatureAlgorithm or \
                    signatureAlgorithm[1] != SignatureAlgorithm.ecdsa:
                scheme = SignatureScheme.toRepr(signatureAlgorithm)
                # for pkcs1 signatures hash is used to add PKCS#1 prefix, but
                # that was already done by calcVerifyBytes
                hash_name = None
                salt_len = 0
                if scheme is None:
                    padding = 'pkcs1'
                else:
                    padding = SignatureScheme.getPadding(scheme)
                    if padding == 'pss':
                        hash_name = SignatureScheme.getHash(scheme)
                        salt_len = getattr(hashlib, hash_name)().digest_size
                ver_func = public_key.verify
            else:
                hash_name = HashAlgorithm.toStr(signatureAlgorithm[0])
                verify_bytes = verify_bytes[
                    :public_key.public_key.curve.baselen]
                padding = None
                salt_len = None
                ver_func = public_key.verify

            if not ver_func(certificateVerify.signature,
                            verify_bytes,
                            padding,
                            hash_name,
                            salt_len):
                for result in self._sendError(
                        AlertDescription.decrypt_error,
                        "Signature failed to verify"):
                    yield result
        yield (premasterSecret, clientCertChain)


    def _serverAnonKeyExchange(self, serverHello, keyExchange, cipherSuite):

        # Create ServerKeyExchange
        serverKeyExchange = keyExchange.makeServerKeyExchange()

        # Send ServerHello[, Certificate], ServerKeyExchange,
        # ServerHelloDone
        msgs = []
        msgs.append(serverHello)
        msgs.append(serverKeyExchange)
        msgs.append(ServerHelloDone())
        for result in self._sendMsgs(msgs):
            yield result

        # Get and check ClientKeyExchange
        for result in self._getMsg(ContentType.handshake,
                                   HandshakeType.client_key_exchange,
                                   cipherSuite):
            if result in (0,1):
                yield result
            else:
                break
        cke = result
        try:
            premasterSecret = keyExchange.processClientKeyExchange(cke)
        except TLSIllegalParameterException as alert:
            for result in self._sendError(AlertDescription.illegal_parameter,
                                          str(alert)):
                yield result
        except TLSDecodeError as alert:
            for result in self._sendError(AlertDescription.decode_error,
                                          str(alert)):
                yield result

        yield premasterSecret


    def _serverFinished(self,  premasterSecret, clientRandom, serverRandom,
                        cipherSuite, cipherImplementations, nextProtos,
                        settings):
        if self.extendedMasterSecret:
            cvhh = self._certificate_verify_handshake_hash
            # in case of resumption or lack of certificate authentication,
            # the CVHH won't be initialised, but then it would also be equal
            # to regular handshake hash
            if not cvhh:
                cvhh = self._handshake_hash
            masterSecret = calc_key(self.version, premasterSecret,
                                    cipherSuite, b"extended master secret",
                                    handshake_hashes=cvhh,
                                    output_length=48)
        else:
            masterSecret = calc_key(self.version, premasterSecret,
                                    cipherSuite, b"master secret",
                                    client_random=clientRandom,
                                    server_random=serverRandom,
                                    output_length=48)

        #Calculate pending connection states
        self._calcPendingStates(cipherSuite, masterSecret, 
                                clientRandom, serverRandom,
                                cipherImplementations)

        #Exchange ChangeCipherSpec and Finished messages
        for result in self._getFinished(masterSecret,
                                        cipherSuite,
                                   expect_next_protocol=nextProtos is not None):
            yield result

        for result in self._sendFinished(masterSecret, cipherSuite,
                settings=settings):
            yield result
        
        yield masterSecret        


    #*********************************************************
    # Shared Handshake Functions
    #*********************************************************


    def _sendFinished(self, masterSecret, cipherSuite=None, nextProto=None,
            settings=None):
        # send the CCS and Finished in single TCP packet
        self.sock.buffer_writes = True
        #Send ChangeCipherSpec
        for result in self._sendMsg(ChangeCipherSpec()):
            yield result

        #Switch to pending write state
        self._changeWriteState()

        if self._peer_record_size_limit:
            self._send_record_limit = self._peer_record_size_limit
            # this is TLS 1.2 and earlier method, so the real limit may be
            # lower that what's in the settings
            self._recv_record_limit = min(2**14, settings.record_size_limit)

        if nextProto is not None:
            nextProtoMsg = NextProtocol().create(nextProto)
            for result in self._sendMsg(nextProtoMsg):
                yield result

        #Figure out the correct label to use
        if self._client:
            label = b"client finished"
        else:
            label = b"server finished"
        #Calculate verification data
        verifyData = calc_key(self.version, masterSecret,
                              cipherSuite, label,
                              handshake_hashes=self._handshake_hash,
                              output_length=12)
        if self.fault == Fault.badFinished:
            verifyData[0] = (verifyData[0]+1)%256

        #Send Finished message under new state
        finished = Finished(self.version).create(verifyData)
        for result in self._sendMsg(finished):
            yield result
        self.sock.flush()
        self.sock.buffer_writes = False

    def _getFinished(self, masterSecret, cipherSuite=None,
                     expect_next_protocol=False, nextProto=None):
        #Get and check ChangeCipherSpec
        for result in self._getMsg( (ContentType.change_cipher_spec, ContentType.handshake)):
            if result in (0,1):
                yield result
        changeCipherSpec = result

        if changeCipherSpec.type != 1:
            for result in self._sendError(AlertDescription.illegal_parameter,
                                         "ChangeCipherSpec type incorrect"):
                yield result

        #Switch to pending read state
        self._changeReadState()

        #Server Finish - Are we waiting for a next protocol echo? 
        if expect_next_protocol:
            for result in self._getMsg(ContentType.handshake, HandshakeType.next_protocol):
                if result in (0,1):
                    yield result
            if result is None:
                for result in self._sendError(AlertDescription.unexpected_message,
                                             "Didn't get NextProtocol message"):
                    yield result

            self.next_proto = result.next_proto
        else:
            self.next_proto = None

        #Client Finish - Only set the next_protocol selected in the connection
        if nextProto:
            self.next_proto = nextProto

        #Figure out which label to use.
        if self._client:
            label = b"server finished"
        else:
            label = b"client finished"

        #Calculate verification data
        verifyData = calc_key(self.version, masterSecret,
                              cipherSuite, label,
                              handshake_hashes=self._handshake_hash,
                              output_length=12)

        #Get and check Finished message under new state
        for result in self._getMsg(ContentType.handshake,
                                  HandshakeType.finished):
            if result in (0,1):
                yield result
        finished = result
        if finished.verify_data != verifyData:
            for result in self._sendError(AlertDescription.decrypt_error,
                                         "Finished message is incorrect"):
                yield result

    def _handshakeWrapperAsync(self, handshaker, checker):
        try:
            for result in handshaker:
                yield result
            if checker:
                try:
                    checker(self)
                except TLSAuthenticationError:
                    alert = Alert().create(AlertDescription.close_notify,
                                           AlertLevel.fatal)
                    for result in self._sendMsg(alert):
                        yield result
                    raise
        except GeneratorExit:
            raise
        except TLSAlert as alert:
            if not self.fault:
                raise
            if alert.description not in Fault.faultAlerts[self.fault]:
                raise TLSFaultError(str(alert))
            else:
                pass
        except:
            self._shutdown(False)
            raise

    @staticmethod
    def _pickServerKeyExchangeSig(settings, clientHello, certList=None,
                                  private_key=None,
                                  version=(3, 3), check_alt=True):
        """Pick a hash that matches most closely the supported ones"""
        hashAndAlgsExt = clientHello.getExtension(
            ExtensionType.signature_algorithms)

        if version > (3, 3):
            if not hashAndAlgsExt:
                # the error checking was done before hand, likely we're
                # doing PSK key exchange
                return None, certList, private_key

        if hashAndAlgsExt is None or hashAndAlgsExt.sigalgs is None:
            # RFC 5246 states that if there are no hashes advertised,
            # sha1 should be picked
            return "sha1", certList, private_key

        if check_alt:
            alt_certs = ((X509CertChain(i.certificates), i.key) for vh in
                         settings.virtual_hosts for i in vh.keys)
        else:
            alt_certs = ()

        for certs, key in chain([(certList, private_key)], alt_certs):
            supported = TLSConnection._sigHashesToList(settings,
                                                       certList=certs,
                                                       version=version)

            for schemeID in supported:
                if schemeID in hashAndAlgsExt.sigalgs:
                    name = SignatureScheme.toRepr(schemeID)
                    if not name and schemeID[1] in (SignatureAlgorithm.rsa,
                                                    SignatureAlgorithm.ecdsa,
                                                    SignatureAlgorithm.dsa):
                        name = HashAlgorithm.toRepr(schemeID[0])

                    if name:
                        return name, certs, key

        # if no match, we must abort per RFC 5246
        raise TLSHandshakeFailure("No common signature algorithms")

    @staticmethod
    def _sigHashesToList(settings, privateKey=None, certList=None,
                         version=(3, 3)):
        """Convert list of valid signature hashes to array of tuples"""
        certType = None
        publicKey = None
        if certList and certList.x509List:
            certType = certList.x509List[0].certAlg
            publicKey = certList.x509List[0].publicKey

        sigAlgs = []

        if not certType or certType == "Ed25519" or certType == "Ed448":
            for sig_scheme in settings.more_sig_schemes:
                if version < (3, 3):
                    # EdDSA is supported only in TLS 1.2 and 1.3
                    continue
                if certType and sig_scheme != certType:
                    continue
                sigAlgs.append(getattr(SignatureScheme, sig_scheme.lower()))

        if not certType or certType == "ecdsa":
            for hashName in settings.ecdsaSigHashes:
                # only SHA256, SHA384 and SHA512 are allowed in TLS 1.3
                if version > (3, 3) and hashName in ("sha1", "sha224"):
                    continue

                # in TLS 1.3 ECDSA key curve is bound to hash
                if publicKey and version > (3, 3):
                    curve = publicKey.curve_name
                    matching_hash = TLSConnection._curve_name_to_hash_name(
                        curve)
                    if hashName != matching_hash:
                        continue

                sigAlgs.append((getattr(HashAlgorithm, hashName),
                                SignatureAlgorithm.ecdsa))

        if not certType or certType == "dsa":
            for hashName in settings.dsaSigHashes:
                if version > (3, 3):
                    continue

                sigAlgs.append((getattr(HashAlgorithm, hashName),
                                SignatureAlgorithm.dsa))

        if not certType or certType in ("rsa", "rsa-pss"):
            for schemeName in settings.rsaSchemes:
                # pkcs#1 v1.5 signatures are not allowed in TLS 1.3
                if version > (3, 3) and schemeName == "pkcs1":
                    continue

                for hashName in settings.rsaSigHashes:
                    # rsa-pss certificates can't be used to make PKCS#1 v1.5
                    # signatures
                    if certType == "rsa-pss" and schemeName == "pkcs1":
                        continue
                    try:
                        # 1024 bit keys are too small to create valid
                        # rsa-pss-SHA512 signatures
                        if schemeName == 'pss' and hashName == 'sha512'\
                                and privateKey and privateKey.n < 2**2047:
                            continue
                        # advertise support for both rsaEncryption and RSA-PSS OID
                        # key type
                        if certType != 'rsa-pss':
                            sigAlgs.append(getattr(SignatureScheme,
                                                   "rsa_{0}_rsae_{1}"
                                                   .format(schemeName, hashName)))
                        if certType != 'rsa':
                            sigAlgs.append(getattr(SignatureScheme,
                                                   "rsa_{0}_pss_{1}"
                                                   .format(schemeName, hashName)))
                    except AttributeError:
                        if schemeName == 'pkcs1':
                            sigAlgs.append((getattr(HashAlgorithm, hashName),
                                            SignatureAlgorithm.rsa))
                        continue
        return sigAlgs

    @staticmethod
    def _curveNamesToList(settings):
        """Convert list of acceptable curves to array identifiers"""
        return [getattr(GroupName, val) for val in settings.eccCurves]

    @staticmethod
    def _groupNamesToList(settings):
        """Convert list of acceptable ff groups to TLS identifiers."""
        return [getattr(GroupName, val) for val in settings.dhGroups]

    @staticmethod
    def _curve_name_to_hash_name(curve_name):
        """Returns the matching hash for a given curve name, for TLS 1.3

        expects the python-ecdsa curve names as parameter
        """
        if curve_name == "NIST256p":
            return "sha256"
        if curve_name == "NIST384p":
            return "sha384"
        if curve_name == "NIST521p":
            return "sha512"
        raise TLSIllegalParameterException(
            "Curve {0} is not supported in TLS 1.3".format(curve_name))
