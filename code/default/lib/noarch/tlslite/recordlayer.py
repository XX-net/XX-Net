# Copyright (c) 2014, Hubert Kario
#
# See the LICENSE file for legal information regarding use of this file.

"""Implementation of the TLS Record Layer protocol"""

import socket
import errno
import copy
try:
    # in python 3 the native zip() returns iterator
    from itertools import izip
except ImportError:
    izip = zip
try:
    # in python 3 the native range() returns an object/iterator
    xrange
except NameError:
    xrange = range

from .utils import tlshashlib as hashlib
from .constants import ContentType, CipherSuite
from .messages import RecordHeader3, RecordHeader2, Message
from .utils.cipherfactory import createAESCCM, createAESCCM_8, createAESGCM,\
        createAES, createRC4, createTripleDES, createCHACHA20
from .utils.codec import Parser, Writer
from .utils.compat import compatHMAC
from .utils.cryptomath import getRandomBytes, MD5, HKDF_expand_label
from .utils.constanttime import ct_compare_digest, ct_check_cbc_mac_and_pad
from .errors import TLSRecordOverflow, TLSIllegalParameterException,\
        TLSAbruptCloseError, TLSDecryptionFailed, TLSBadRecordMAC, \
        TLSUnexpectedMessage
from .mathtls import createMAC_SSL, createHMAC, calc_key

class RecordSocket(object):
    """
    Socket wrapper for reading and writing TLS Records.

    :ivar sock: wrapped socket
    :ivar ~.version: version for the records to be encoded on the wire
    :ivar tls13record: flag to indicate that TLS 1.3 specific record limits
        should be used for received records
    :ivar int recv_record_limit: negotiated maximum size of record plaintext
        size
    """

    def __init__(self, sock):
        """
        Assign socket to wrapper

        :type sock: socket.socket
        """
        self.sock = sock
        self.version = (0, 0)
        self.tls13record = False
        self.recv_record_limit = 2**14

    def _sockSendAll(self, data):
        """
        Send all data through socket

        :type data: bytearray
        :param data: data to send
        :raises socket.error: when write to socket failed
        """
        while 1:
            try:
                bytesSent = self.sock.send(data)
            except socket.error as why:
                if why.args[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    yield 1
                    continue
                raise

            if bytesSent == len(data):
                return
            data = data[bytesSent:]
            yield 1

    def send(self, msg, padding=0):
        """
        Send the message through socket.

        :type msg: bytearray
        :param msg: TLS message to send
        :type padding: int
        :param padding: amount of padding to specify for SSLv2
        :raises socket.error: when write to socket failed
        """
        data = msg.write()

        if self.version in ((2, 0), (0, 2)):
            header = RecordHeader2().create(len(data),
                                            padding)
        else:
            header = RecordHeader3().create(self.version,
                                            msg.contentType,
                                            len(data))

        data = header.write() + data

        for result in self._sockSendAll(data):
            yield result

    def _sockRecvAll(self, length):
        """
        Read exactly the amount of bytes specified in L{length} from raw socket.

        :rtype: generator
        :returns: generator that will return 0 or 1 in case the socket is non
            blocking and would block and bytearray in case the read finished
        :raises TLSAbruptCloseError: when the socket closed
        """
        buf = bytearray(0)

        if length == 0:
            yield buf

        while True:
            try:
                socketBytes = self.sock.recv(length - len(buf))
            except socket.error as why:
                if why.args[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    yield 0
                    continue
                else:
                    raise

            #if the connection closed, raise socket error
            if len(socketBytes) == 0:
                raise TLSAbruptCloseError()

            buf += bytearray(socketBytes)
            if len(buf) == length:
                yield buf

    def _recvHeader(self):
        """Read a single record header from socket"""
        #Read the next record header
        buf = bytearray(0)
        ssl2 = False

        result = None
        for result in self._sockRecvAll(1):
            if result in (0, 1):
                yield result
            else: break
        assert result is not None

        buf += result

        if buf[0] in ContentType.all:
            ssl2 = False
            # SSLv3 record layer header is 5 bytes long, we already read 1
            result = None
            for result in self._sockRecvAll(4):
                if result in (0, 1):
                    yield result
                else: break
            assert result is not None
            buf += result
        else:
            # if header has no pading the header is 2 bytes long, 3 otherwise
            # at the same time we already read 1 byte
            ssl2 = True
            if buf[0] & 0x80:
                readLen = 1
            else:
                readLen = 2
            result = None
            for result in self._sockRecvAll(readLen):
                if result in (0, 1):
                    yield result
                else: break
            assert result is not None
            buf += result


        #Parse the record header
        if ssl2:
            record = RecordHeader2().parse(Parser(buf))
            # padding can't be longer than overall length and if it is present
            # the overall size must be a multiple of cipher block size
            if ((record.padding > record.length) or
                    (record.padding and record.length % 8)):
                raise TLSIllegalParameterException(\
                        "Malformed record layer header")
        else:
            record = RecordHeader3().parse(Parser(buf))

        yield record

    def recv(self):
        """
        Read a single record from socket, handle SSLv2 and SSLv3 record layer

        :rtype: generator
        :returns: generator that returns 0 or 1 in case the read would be
            blocking or a tuple containing record header (object) and record
            data (bytearray) read from socket
        :raises socket.error: In case of network error
        :raises TLSAbruptCloseError: When the socket was closed on the other
            side in middle of record receiving
        :raises TLSRecordOverflow: When the received record was longer than
            allowed by TLS
        :raises TLSIllegalParameterException: When the record header was
            malformed
        """
        record = None
        for record in self._recvHeader():
            if record in (0, 1):
                yield record
            else: break
        assert record is not None

        #Check the record header fields
        # 18432 = 2**14 (default record size limit) + 1024 (maximum compression
        # overhead) + 1024 (maximum encryption overhead)
        if record.length > self.recv_record_limit + 1024 + 1024:
            raise TLSRecordOverflow()
        if self.tls13record and record.length > self.recv_record_limit + 256:
            raise TLSRecordOverflow()

        #Read the record contents
        buf = bytearray(0)

        result = None
        for result in self._sockRecvAll(record.length):
            if result in (0, 1):
                yield result
            else: break
        assert result is not None

        buf += result

        yield (record, buf)


class ConnectionState(object):

    """Preserve the connection state for reading and writing data to records"""

    def __init__(self):
        """Create an instance with empty encryption and MACing contexts"""
        self.macContext = None
        self.encContext = None
        self.fixedNonce = None
        self.seqnum = 0
        self.encryptThenMAC = False

    def getSeqNumBytes(self):
        """Return encoded sequence number and increment it."""
        writer = Writer()
        writer.add(self.seqnum, 8)
        self.seqnum += 1
        return writer.bytes

    def __copy__(self):
        """Return a copy of the object."""
        ret = ConnectionState()
        ret.macContext = copy.copy(self.macContext)
        ret.encContext = copy.copy(self.encContext)
        ret.fixedNonce = self.fixedNonce
        ret.seqnum = self.seqnum
        ret.encryptThenMAC = self.encryptThenMAC
        return ret


class RecordLayer(object):

    """
    Implementation of TLS record layer protocol

    :ivar ~.version: the TLS version to use (tuple encoded as on the wire)
    :ivar sock: underlying socket
    :ivar client: whether the connection should use encryption
    :ivar handshake_finished: used in SSL2, True if handshake protocol is over
    :ivar tls13record: if True, the record layer will use the TLS 1.3 version
        and content type hiding
    :ivar bool early_data_ok: if True, it's ok to ignore undecryptable records
        up to the size of max_early_data (sum of payloads)
    :ivar int max_early_data: maximum number of bytes that will be processed
        before aborting the connection on data that can not be validated,
        works only if early_data_ok is set to True
    :ivar callable padding_cb: callback used for calculating the size of
        padding to add in TLSv1.3 records
    :ivar int send_record_limit: hint provided to padding callback to not
        generate records larger than the receiving size expects
    :ivar int recv_record_limit: negotiated size of records we are willing to
        accept, TLSRecordOverflow will be raised when records with larger
        plaintext size are received (in TLS 1.3 padding is included in this
        size but encrypted content type is not)
    """

    def __init__(self, sock):
        self.sock = sock
        self._recordSocket = RecordSocket(sock)
        self._version = (0, 0)
        self._tls13record = False

        self.client = True

        self._writeState = ConnectionState()
        self._readState = ConnectionState()
        self._pendingWriteState = ConnectionState()
        self._pendingReadState = ConnectionState()
        self.fixedIVBlock = None

        self.handshake_finished = False

        self.padding_cb = None

        self._early_data_ok = False
        self.max_early_data = 0
        self._early_data_processed = 0
        self.send_record_limit = 2**14

    @property
    def recv_record_limit(self):
        """Maximum record size that is permitted for receiving."""
        return self._recordSocket.recv_record_limit

    @recv_record_limit.setter
    def recv_record_limit(self, value):
        self._recordSocket.recv_record_limit = value

    @property
    def early_data_ok(self):
        """
        Set or get the state of early data acceptability.

        If processing of the early_data records is to suceed, even if the
        encryption is not correct, set this property to True. It will be
        automatically reset to False as soon as a decryptable record is
        processed.

        Use max_early_data to set the limit of the total size of records
        that will be processed like this.
        """
        return self._early_data_ok

    @early_data_ok.setter
    def early_data_ok(self, val):
        self._early_data_processed = 0
        self._early_data_ok = val

    @property
    def encryptThenMAC(self):
        """
        Set or get the setting of Encrypt Then MAC mechanism.

        set the encrypt-then-MAC mechanism for record
        integrity for next parameter change (after CCS),
        gets current state
        """
        return self._writeState.encryptThenMAC

    @encryptThenMAC.setter
    def encryptThenMAC(self, value):
        self._pendingWriteState.encryptThenMAC = value
        self._pendingReadState.encryptThenMAC = value

    @property
    def blockSize(self):
        """Return the size of block used by current symmetric cipher (R/O)"""
        return self._writeState.encContext.block_size

    @property
    def tls13record(self):
        """Return the value of the tls13record state."""
        return self._tls13record

    @tls13record.setter
    def tls13record(self, val):
        """Change the record layer to TLS1.3-like operation, if applicable."""
        self._tls13record = val
        self._recordSocket.tls13record = val
        self._handle_tls13_record()

    def _is_tls13_plus(self):
        """Returns True if we're doing real TLS 1.3."""
        return self._version > (3, 3) and self._tls13record

    def _handle_tls13_record(self):
        """Make sure that the version and tls13record setting is consistent."""
        if self._is_tls13_plus():
            # in TLS 1.3 all records need to be sent with the generic version
            # which is the same as TLS 1.2
            self._recordSocket.version = (3, 3)
        else:
            self._recordSocket.version = self._version

    @property
    def version(self):
        """Return the TLS version used by record layer"""
        return self._version

    @version.setter
    def version(self, val):
        """Set the TLS version used by record layer"""
        self._version = val
        self._handle_tls13_record()

    def getCipherName(self):
        """
        Return the name of the bulk cipher used by this connection

        :rtype: str
        :returns: The name of the cipher, like 'aes128', 'rc4', etc.
        """
        if self._writeState.encContext is None:
            return None
        return self._writeState.encContext.name

    def getCipherImplementation(self):
        """
        Return the name of the implementation used for the connection

        'python' for tlslite internal implementation, 'openssl' for M2crypto
        and 'pycrypto' for pycrypto
        :rtype: str
        :returns: Name of cipher implementation used, None if not initialised
        """
        if self._writeState.encContext is None:
            return None
        return self._writeState.encContext.implementation

    def shutdown(self):
        """Clear read and write states"""
        self._writeState = ConnectionState()
        self._readState = ConnectionState()
        self._pendingWriteState = ConnectionState()
        self._pendingReadState = ConnectionState()

    def isCBCMode(self):
        """Returns true if cipher uses CBC mode"""
        if self._writeState and self._writeState.encContext and \
                self._writeState.encContext.isBlockCipher:
            return True
        else:
            return False
    #
    # sending messages
    #

    def addPadding(self, data):
        """Add padding to data so that it is multiple of block size"""
        currentLength = len(data)
        blockLength = self.blockSize
        paddingLength = blockLength - 1 - (currentLength % blockLength)

        paddingBytes = bytearray([paddingLength] * (paddingLength+1))
        data += paddingBytes
        return data

    def calculateMAC(self, mac, seqnumBytes, contentType, data):
        """Calculate the SSL/TLS version of a MAC"""
        mac.update(compatHMAC(seqnumBytes))
        mac.update(compatHMAC(bytearray([contentType])))
        assert self.version in ((3, 0), (3, 1), (3, 2), (3, 3))
        if self.version != (3, 0):
            mac.update(compatHMAC(bytearray([self.version[0]])))
            mac.update(compatHMAC(bytearray([self.version[1]])))
        mac.update(compatHMAC(bytearray([len(data)//256])))
        mac.update(compatHMAC(bytearray([len(data)%256])))
        mac.update(compatHMAC(data))
        return bytearray(mac.digest())

    def _macThenEncrypt(self, data, contentType):
        """MAC, pad then encrypt data"""
        if self._writeState.macContext:
            seqnumBytes = self._writeState.getSeqNumBytes()
            mac = self._writeState.macContext.copy()
            macBytes = self.calculateMAC(mac, seqnumBytes, contentType, data)
            data += macBytes

        #Encrypt for Block or Stream Cipher
        if self._writeState.encContext:
            #Add padding (for Block Cipher):
            if self._writeState.encContext.isBlockCipher:

                #Add TLS 1.1 fixed block
                if self.version >= (3, 2):
                    data = self.fixedIVBlock + data

                data = self.addPadding(data)

            #Encrypt
            data = self._writeState.encContext.encrypt(data)

        return data

    def _encryptThenMAC(self, buf, contentType):
        """Pad, encrypt and then MAC the data"""
        if self._writeState.encContext:
            # add IV for TLS1.1+
            if self.version >= (3, 2):
                buf = self.fixedIVBlock + buf

            buf = self.addPadding(buf)

            buf = self._writeState.encContext.encrypt(buf)

        # add MAC
        if self._writeState.macContext:
            seqnumBytes = self._writeState.getSeqNumBytes()
            mac = self._writeState.macContext.copy()

            # append MAC
            macBytes = self.calculateMAC(mac, seqnumBytes, contentType, buf)
            buf += macBytes

        return buf

    def _getNonce(self, state, seqnum):
        """Calculate a nonce for a given enc/dec context"""
        # ChaCha is using the draft-TLS1.3-like nonce derivation
        if (state.encContext.name == "chacha20-poly1305" and
                len(state.fixedNonce) == 12) or self._is_tls13_plus():
            # 4 byte nonce is used by the draft cipher
            pad = bytearray(len(state.fixedNonce) - len(seqnum))
            nonce = bytearray(i ^ j for i, j in zip(pad + seqnum,
                                                    state.fixedNonce))
        else:
            nonce = state.fixedNonce + seqnum
        return nonce


    def _encryptThenSeal(self, buf, contentType):
        """Encrypt with AEAD cipher"""
        #Assemble the authenticated data.
        seqNumBytes = self._writeState.getSeqNumBytes()
        if not self._is_tls13_plus():
            authData = seqNumBytes + bytearray([contentType,
                                                self.version[0],
                                                self.version[1],
                                                len(buf)//256,
                                                len(buf)%256])
        else:  # TLS 1.3
            out_len = len(buf) + self._writeState.encContext.tagLength
            # this is just recreated Record Layer header
            authData = bytearray([contentType,
                                  self._recordSocket.version[0],
                                  self._recordSocket.version[1],
                                  out_len // 256, out_len % 256])

        nonce = self._getNonce(self._writeState, seqNumBytes)

        assert len(nonce) == self._writeState.encContext.nonceLength

        buf = self._writeState.encContext.seal(nonce, buf, authData)

        #AES-GCM, has an explicit variable nonce.
        if "aes" in self._writeState.encContext.name and \
                not self._is_tls13_plus():
            buf = seqNumBytes + buf

        return buf

    def _ssl2Encrypt(self, data):
        """Encrypt in SSL2 mode"""
        # in SSLv2 sequence numbers are incremented for plaintext records too
        seqnumBytes = self._writeState.getSeqNumBytes()

        if (self._writeState.encContext and
                self._writeState.encContext.isBlockCipher):
            plaintext_len = len(data)
            data = self.addPadding(data)
            padding = len(data) - plaintext_len
        else:
            padding = 0

        if self._writeState.macContext:
            mac = self._writeState.macContext.copy()
            mac.update(compatHMAC(data))
            mac.update(compatHMAC(seqnumBytes[-4:]))

            data = bytearray(mac.digest()) + data

        if self._writeState.encContext:
            data = self._writeState.encContext.encrypt(data)

        return data, padding

    def sendRecord(self, msg):
        """
        Encrypt, MAC and send arbitrary message as-is through socket.

        Note that if the message was not fragmented to below 2**14 bytes
        it will be rejected by the other connection side.

        :param msg: TLS message to send
        :type msg: ApplicationData, HandshakeMessage, etc.
        """
        data = msg.write()
        contentType = msg.contentType

        # TLS 1.3 hides the content type of messages
        # but CCS is always not encrypted
        if self._is_tls13_plus() and self._writeState.encContext and \
                contentType != ContentType.change_cipher_spec:
            data += bytearray([contentType])
            if self.padding_cb:
                max_padding = self.send_record_limit - len(data) - 1
                # add number of zero bytes specified by padding_cb()
                data += bytearray(self.padding_cb(len(data),
                                                  contentType,
                                                  max_padding))
            # in TLS 1.3 contentType is ignored by _encryptThenSeal
            contentType = ContentType.application_data

        padding = 0
        if self.version in ((0, 2), (2, 0)):
            data, padding = self._ssl2Encrypt(data)
        elif self.version > (3, 3) and \
                contentType == ContentType.change_cipher_spec:
            # TLS 1.3 does not encrypt CCS messages
            pass
        elif self._writeState.encContext and \
                self._writeState.encContext.isAEAD:
            data = self._encryptThenSeal(data, contentType)
        elif self._writeState.encryptThenMAC:
            data = self._encryptThenMAC(data, contentType)
        else:
            data = self._macThenEncrypt(data, contentType)

        encryptedMessage = Message(contentType, data)

        for result in self._recordSocket.send(encryptedMessage, padding):
            yield result

    #
    # receiving messages
    #

    def _decryptStreamThenMAC(self, recordType, data):
        """Decrypt a stream cipher and check MAC"""
        if self._readState.encContext:
            assert self.version in ((3, 0), (3, 1), (3, 2), (3, 3))

            data = self._readState.encContext.decrypt(data)

        if self._readState.macContext:
            #Check MAC
            macGood = True
            macLength = self._readState.macContext.digest_size
            endLength = macLength
            if endLength > len(data):
                macGood = False
            else:
                #Read MAC
                startIndex = len(data) - endLength
                endIndex = startIndex + macLength
                checkBytes = data[startIndex : endIndex]

                #Calculate MAC
                seqnumBytes = self._readState.getSeqNumBytes()
                data = data[:-endLength]
                mac = self._readState.macContext.copy()
                macBytes = self.calculateMAC(mac, seqnumBytes, recordType,
                                             data)

                #Compare MACs
                if not ct_compare_digest(macBytes, checkBytes):
                    macGood = False

            if not macGood:
                raise TLSBadRecordMAC()

        return data


    def _decryptThenMAC(self, recordType, data):
        """Decrypt data, check padding and MAC"""
        if self._readState.encContext:
            assert self.version in ((3, 0), (3, 1), (3, 2), (3, 3))
            assert self._readState.encContext.isBlockCipher
            assert self._readState.macContext

            #
            # decrypt the record
            #
            blockLength = self._readState.encContext.block_size
            if len(data) % blockLength != 0:
                raise TLSDecryptionFailed()
            data = self._readState.encContext.decrypt(data)
            if self.version >= (3, 2): #For TLS 1.1, remove explicit IV
                data = data[self._readState.encContext.block_size : ]

            #
            # check padding and MAC
            #
            seqnumBytes = self._readState.getSeqNumBytes()

            if not ct_check_cbc_mac_and_pad(
                    data,
                    self._readState.macContext,
                    seqnumBytes,
                    recordType,
                    self.version,
                    self._readState.encContext.block_size):
                raise TLSBadRecordMAC()

            #
            # strip padding and MAC
            #

            endLength = data[-1] + 1 + self._readState.macContext.digest_size

            data = data[:-endLength]

        return data

    def _macThenDecrypt(self, recordType, buf):
        """
        Check MAC of data, then decrypt and remove padding

        :raises TLSBadRecordMAC: when the mac value is invalid
        :raises TLSDecryptionFailed: when the data to decrypt has invalid size
        """
        if self._readState.macContext:
            macLength = self._readState.macContext.digest_size
            if len(buf) < macLength:
                raise TLSBadRecordMAC("Truncated data")

            checkBytes = buf[-macLength:]
            buf = buf[:-macLength]

            seqnumBytes = self._readState.getSeqNumBytes()
            mac = self._readState.macContext.copy()

            macBytes = self.calculateMAC(mac, seqnumBytes, recordType, buf)

            if not ct_compare_digest(macBytes, checkBytes):
                raise TLSBadRecordMAC("MAC mismatch")

        if self._readState.encContext:
            blockLength = self._readState.encContext.block_size
            if len(buf) % blockLength != 0:
                raise TLSDecryptionFailed("data length not multiple of "\
                                          "block size")

            buf = self._readState.encContext.decrypt(buf)

            # remove explicit IV
            if self.version >= (3, 2):
                buf = buf[blockLength:]

            if len(buf) == 0:
                raise TLSBadRecordMAC("No data left after IV removal")

            # check padding
            paddingLength = buf[-1]
            if paddingLength + 1 > len(buf):
                raise TLSBadRecordMAC("Invalid padding length")

            paddingGood = True
            totalPaddingLength = paddingLength+1
            if self.version != (3, 0):
                paddingBytes = buf[-totalPaddingLength:-1]
                for byte in paddingBytes:
                    if byte != paddingLength:
                        paddingGood = False

            if not paddingGood:
                raise TLSBadRecordMAC("Invalid padding byte values")

            # remove padding
            buf = buf[:-totalPaddingLength]

        return buf

    def _decryptAndUnseal(self, header, buf):
        """Decrypt AEAD encrypted data"""
        seqnumBytes = self._readState.getSeqNumBytes()
        # AES-GCM has an explicit variable nonce in TLS 1.2
        if "aes" in self._readState.encContext.name and \
                not self._is_tls13_plus():
            explicitNonceLength = 8
            if explicitNonceLength > len(buf):
                #Publicly invalid.
                raise TLSBadRecordMAC("Truncated nonce")
            nonce = self._readState.fixedNonce + buf[:explicitNonceLength]
            buf = buf[8:]
        else:
            # for TLS 1.3 and Chacha20 in TLS 1.2 share nonce generation
            # algorithm
            nonce = self._getNonce(self._readState, seqnumBytes)

        if self._readState.encContext.tagLength > len(buf):
            #Publicly invalid.
            raise TLSBadRecordMAC("Truncated tag")

        if not self._is_tls13_plus():
            plaintextLen = len(buf) - self._readState.encContext.tagLength
            authData = seqnumBytes + bytearray([header.type, self.version[0],
                                                self.version[1],
                                                plaintextLen//256,
                                                plaintextLen%256])
        else:  # TLS 1.3
            # enforce the checks for encrypted records
            if header.type != ContentType.application_data:
                raise TLSUnexpectedMessage(
                    "Invalid ContentType for encrypted record: {0}"
                    .format(ContentType.toStr(header.type)))
            if header.version != (3, 3):
                raise TLSIllegalParameterException(
                    "Unexpected version in encrypted record: {0}"
                    .format(header.version))
            if header.length != len(buf):
                raise TLSBadRecordMAC("Length mismatch")
            authData = header.write()

        buf = self._readState.encContext.open(nonce, buf, authData)
        if buf is None:
            raise TLSBadRecordMAC("Invalid tag, decryption failure")
        return buf

    def _decryptSSL2(self, data, padding):
        """Decrypt SSL2 encrypted data"""
        # sequence numbers are incremented for plaintext records too
        seqnumBytes = self._readState.getSeqNumBytes()

        #
        # decrypt
        #
        if self._readState.encContext:
            if self._readState.encContext.isBlockCipher:
                blockLength = self._readState.encContext.block_size
                if len(data) % blockLength:
                    raise TLSDecryptionFailed()
            data = self._readState.encContext.decrypt(data)

        #
        # strip and check MAC
        #
        if self._readState.macContext:
            macBytes = data[:16]
            data = data[16:]

            mac = self._readState.macContext.copy()
            mac.update(compatHMAC(data))
            mac.update(compatHMAC(seqnumBytes[-4:]))
            calcMac = bytearray(mac.digest())
            if macBytes != calcMac:
                raise TLSBadRecordMAC()

        #
        # strip padding
        #
        if padding:
            data = data[:-padding]
        return data

    @staticmethod
    def _tls13_de_pad(data):
        """
        Remove the padding and extract content type from TLSInnerPlaintext.

        :param bytearray data: decrypted plaintext TLS 1.3 record payload
            (the serialised TLSInnerPlaintext data structure)

        :rtype: tuple
        """
        # the padding is at the end and the first non-zero byte is the
        # padding
        # could be reversed(enumerate(data)), if that worked at all
        # could be reversed(list(enumerate(data))), if that didn't double
        # memory usage
        for pos, value in izip(reversed(xrange(len(data))), reversed(data)):
            if value != 0:
                break
        else:
            raise TLSUnexpectedMessage("Malformed record layer inner plaintext"
                                       " - content type missing")

        return data[:pos], value

    def recvRecord(self):
        """
        Read, decrypt and check integrity of a single record

        :rtype: tuple
        :returns: message header and decrypted message payload
        :raises TLSDecryptionFailed: when decryption of data failed
        :raises TLSBadRecordMAC: when record has bad MAC or padding
        :raises socket.error: when reading from socket was unsuccessful
        :raises TLSRecordOverflow: when the received record was longer than
            allowed by negotiated version of TLS
        """
        while True:
            result = None
            for result in self._recordSocket.recv():
                if result in (0, 1):
                    yield result
                else: break
            assert result is not None

            (header, data) = result
            # as trying decryption increments sequence number, we need to
            # keep the old one (we do copy of the whole object in case
            # some cipher has an internal state itself)
            read_state_copy = None
            if self.early_data_ok:
                # do the copy only when needed
                read_state_copy = copy.copy(self._readState)

            try:
                if isinstance(header, RecordHeader2):
                    data = self._decryptSSL2(data, header.padding)
                    if self.handshake_finished:
                        header.type = ContentType.application_data
                # in TLS 1.3, the other party may send an unprotected CCS
                # message at any point in connection
                elif self._is_tls13_plus() and \
                        header.type == ContentType.change_cipher_spec:
                    pass
                elif self._readState and \
                    self._readState.encContext and \
                    self._readState.encContext.isAEAD:
                    data = self._decryptAndUnseal(header, data)
                elif self._readState and self._readState.encryptThenMAC:
                    data = self._macThenDecrypt(header.type, data)
                elif self._readState and \
                        self._readState.encContext and \
                        self._readState.encContext.isBlockCipher:
                    data = self._decryptThenMAC(header.type, data)
                else:
                    data = self._decryptStreamThenMAC(header.type, data)
                # if we don't have an encryption context established
                # and early data is ok, that means we have received
                # encrypted record in case the type of record is
                # application_data (from TLS 1.3)
                if not self._readState.encContext \
                        and not self._readState.macContext \
                        and self.early_data_ok and \
                        header.type == ContentType.application_data:
                    raise TLSBadRecordMAC("early data received")
            except TLSBadRecordMAC:
                if self.early_data_ok and (
                        self._early_data_processed + len(data)
                        < self.max_early_data):
                    # ignore exception, retry reading
                    self._early_data_processed += len(data)
                    # reload state for decryption
                    self._readState = read_state_copy
                    continue
                raise
            # as soon as we're able to decrypt messages again, we must
            # start checking the MACs
            self.early_data_ok = False

            # TLS 1.3 encrypts the type, CCS is not encrypted
            if self._is_tls13_plus() and self._readState and \
                    self._readState.encContext and\
                    header.type != ContentType.change_cipher_spec:
                # check if plaintext is not too big, RFC 8446, section 5.4
                if len(data) > self.recv_record_limit + 1:
                    raise TLSRecordOverflow()
                data, contentType = self._tls13_de_pad(data)
                header = RecordHeader3().create((3, 4), contentType, len(data))

            # RFC 5246, section 6.2.1
            if len(data) > self.recv_record_limit:
                raise TLSRecordOverflow()

            yield (header, Parser(data))

    #
    # cryptography state methods
    #

    def changeWriteState(self):
        """
        Change the cipher state to the pending one for write operations.

        This should be done only once after a call to
        :py:meth:`calcPendingStates` was
        performed and directly after sending a :py:class:`ChangeCipherSpec`
        message.
        """
        if self.version in ((0, 2), (2, 0)):
            # in SSLv2 sequence numbers carry over from plaintext to encrypted
            # context
            self._pendingWriteState.seqnum = self._writeState.seqnum
        self._writeState = self._pendingWriteState
        self._pendingWriteState = ConnectionState()

    def changeReadState(self):
        """
        Change the cipher state to the pending one for read operations.

        This should be done only once after a call to
        :py:meth:`calcPendingStates` was
        performed and directly after receiving a :py:class:`ChangeCipherSpec`
        message.
        """
        if self.version in ((0, 2), (2, 0)):
            # in SSLv2 sequence numbers carry over from plaintext to encrypted
            # context
            self._pendingReadState.seqnum = self._readState.seqnum
        self._readState = self._pendingReadState
        self._pendingReadState = ConnectionState()

    @staticmethod
    def _getCipherSettings(cipherSuite):
        """Get the settings for cipher suite used"""
        if cipherSuite in CipherSuite.aes256GcmSuites:
            keyLength = 32
            ivLength = 4
            createCipherFunc = createAESGCM
        elif cipherSuite in CipherSuite.aes128GcmSuites:
            keyLength = 16
            ivLength = 4
            createCipherFunc = createAESGCM
        elif cipherSuite in CipherSuite.aes256Ccm_8Suites:
            keyLength = 32
            ivLength = 4
            createCipherFunc = createAESCCM_8
        elif cipherSuite in CipherSuite.aes256CcmSuites:
            keyLength = 32
            ivLength = 4
            createCipherFunc = createAESCCM
        elif cipherSuite in CipherSuite.aes128Ccm_8Suites:
            keyLength = 16
            ivLength = 4
            createCipherFunc = createAESCCM_8
        elif cipherSuite in CipherSuite.aes128CcmSuites:
            keyLength = 16
            ivLength = 4
            createCipherFunc = createAESCCM
        elif cipherSuite in CipherSuite.chacha20Suites:
            keyLength = 32
            ivLength = 12
            createCipherFunc = createCHACHA20
        elif cipherSuite in CipherSuite.chacha20draft00Suites:
            keyLength = 32
            ivLength = 4
            createCipherFunc = createCHACHA20
        elif cipherSuite in CipherSuite.aes128Suites:
            keyLength = 16
            ivLength = 16
            createCipherFunc = createAES
        elif cipherSuite in CipherSuite.aes256Suites:
            keyLength = 32
            ivLength = 16
            createCipherFunc = createAES
        elif cipherSuite in CipherSuite.rc4Suites:
            keyLength = 16
            ivLength = 0
            createCipherFunc = createRC4
        elif cipherSuite in CipherSuite.tripleDESSuites:
            keyLength = 24
            ivLength = 8
            createCipherFunc = createTripleDES
        elif cipherSuite in CipherSuite.nullSuites:
            keyLength = 0
            ivLength = 0
            createCipherFunc = None
        else:
            raise AssertionError()

        return (keyLength, ivLength, createCipherFunc)

    @staticmethod
    def _getMacSettings(cipherSuite):
        """Get settings for HMAC used"""
        if cipherSuite in CipherSuite.aeadSuites:
            macLength = 0
            digestmod = None
        elif cipherSuite in CipherSuite.shaSuites:
            macLength = 20
            digestmod = hashlib.sha1
        elif cipherSuite in CipherSuite.sha256Suites:
            macLength = 32
            digestmod = hashlib.sha256
        elif cipherSuite in CipherSuite.sha384Suites:
            macLength = 48
            digestmod = hashlib.sha384
        elif cipherSuite in CipherSuite.md5Suites:
            macLength = 16
            digestmod = hashlib.md5
        else:
            raise AssertionError()

        return macLength, digestmod

    @staticmethod
    def _getHMACMethod(version):
        """Get the HMAC method"""
        assert version in ((3, 0), (3, 1), (3, 2), (3, 3))
        if version == (3, 0):
            createMACFunc = createMAC_SSL
        elif version in ((3, 1), (3, 2), (3, 3)):
            createMACFunc = createHMAC

        return createMACFunc

    def calcSSL2PendingStates(self, cipherSuite, masterSecret, clientRandom,
                              serverRandom, implementations):
        """
        Create the keys for encryption and decryption in SSLv2

        While we could reuse calcPendingStates(), we need to provide the
        key-arg data for the server that needs to be passed up to handshake
        protocol.
        """
        if cipherSuite in CipherSuite.ssl2_128Key:
            key_length = 16
        elif cipherSuite in CipherSuite.ssl2_192Key:
            key_length = 24
        elif cipherSuite in CipherSuite.ssl2_64Key:
            key_length = 8
        else:
            raise ValueError("Unknown cipher specified")

        key_material = bytearray(key_length * 2)
        md5_output_size = 16
        for i, pos in enumerate(range(0, key_length * 2, md5_output_size)):
            key_material[pos:pos+md5_output_size] = MD5(\
                    masterSecret +
                    bytearray(str(i), "ascii") +
                    clientRandom + serverRandom)

        serverWriteKey = key_material[:key_length]
        clientWriteKey = key_material[key_length:]

        # specification draft says that DES key should not use the
        # incrementing label but all implementations use it anyway
        #elif cipherSuite in CipherSuite.ssl2_64Key:
        #    key_material = MD5(masterSecret + clientRandom + serverRandom)
        #    serverWriteKey = key_material[0:8]
        #    clientWriteKey = key_material[8:16]

        # RC4 cannot use initialisation vector
        if cipherSuite not in CipherSuite.ssl2rc4:
            iv = getRandomBytes(8)
        else:
            iv = bytearray(0)

        clientPendingState = ConnectionState()
        serverPendingState = ConnectionState()

        # MAC
        clientPendingState.macContext = hashlib.md5()
        clientPendingState.macContext.update(compatHMAC(clientWriteKey))
        serverPendingState.macContext = hashlib.md5()
        serverPendingState.macContext.update(compatHMAC(serverWriteKey))

        # ciphers
        if cipherSuite in CipherSuite.ssl2rc4:
            cipherMethod = createRC4
        elif cipherSuite in CipherSuite.ssl2_3des:
            cipherMethod = createTripleDES
        else:
            raise NotImplementedError("Unknown cipher")

        clientPendingState.encContext = cipherMethod(clientWriteKey, iv,
                                                     implementations)
        serverPendingState.encContext = cipherMethod(serverWriteKey, iv,
                                                     implementations)

        # Assign new connection states to pending states
        if self.client:
            self._pendingWriteState = clientPendingState
            self._pendingReadState = serverPendingState
        else:
            self._pendingWriteState = serverPendingState
            self._pendingReadState = clientPendingState

        return iv

    def calcPendingStates(self, cipherSuite, masterSecret, clientRandom,
                          serverRandom, implementations):
        """Create pending states for encryption and decryption."""
        keyLength, ivLength, createCipherFunc = \
                self._getCipherSettings(cipherSuite)

        macLength, digestmod = self._getMacSettings(cipherSuite)

        if not digestmod:
            createMACFunc = None
        else:
            createMACFunc = self._getHMACMethod(self.version)

        outputLength = (macLength*2) + (keyLength*2) + (ivLength*2)

        #Calculate Keying Material from Master Secret
        keyBlock = calc_key(self.version, masterSecret, cipherSuite,
                            b"key expansion", client_random=clientRandom,
                            server_random=serverRandom,
                            output_length=outputLength)

        #Slice up Keying Material
        clientPendingState = ConnectionState()
        serverPendingState = ConnectionState()
        parser = Parser(keyBlock)
        clientMACBlock = parser.getFixBytes(macLength)
        serverMACBlock = parser.getFixBytes(macLength)
        clientKeyBlock = parser.getFixBytes(keyLength)
        serverKeyBlock = parser.getFixBytes(keyLength)
        clientIVBlock = parser.getFixBytes(ivLength)
        serverIVBlock = parser.getFixBytes(ivLength)

        if digestmod:
            # Legacy cipher
            clientPendingState.macContext = createMACFunc(
                compatHMAC(clientMACBlock), digestmod=digestmod)
            serverPendingState.macContext = createMACFunc(
                compatHMAC(serverMACBlock), digestmod=digestmod)
            if createCipherFunc is not None:
                clientPendingState.encContext = \
                                            createCipherFunc(clientKeyBlock,
                                                             clientIVBlock,
                                                             implementations)
                serverPendingState.encContext = \
                                            createCipherFunc(serverKeyBlock,
                                                             serverIVBlock,
                                                             implementations)
        else:
            # AEAD
            clientPendingState.macContext = None
            serverPendingState.macContext = None
            clientPendingState.encContext = createCipherFunc(clientKeyBlock,
                                                             implementations)
            serverPendingState.encContext = createCipherFunc(serverKeyBlock,
                                                             implementations)
            clientPendingState.fixedNonce = clientIVBlock
            serverPendingState.fixedNonce = serverIVBlock

        #Assign new connection states to pending states
        if self.client:
            clientPendingState.encryptThenMAC = \
                    self._pendingWriteState.encryptThenMAC
            self._pendingWriteState = clientPendingState
            serverPendingState.encryptThenMAC = \
                    self._pendingReadState.encryptThenMAC
            self._pendingReadState = serverPendingState
        else:
            serverPendingState.encryptThenMAC = \
                    self._pendingWriteState.encryptThenMAC
            self._pendingWriteState = serverPendingState
            clientPendingState.encryptThenMAC = \
                    self._pendingReadState.encryptThenMAC
            self._pendingReadState = clientPendingState

        if self.version >= (3, 2) and ivLength:
            #Choose fixedIVBlock for TLS 1.1 (this is encrypted with the CBC
            #residue to create the IV for each sent block)
            self.fixedIVBlock = getRandomBytes(ivLength)

    def calcTLS1_3PendingState(self, cipherSuite, cl_traffic_secret,
                               sr_traffic_secret,
                               implementations):
        """
        Create pending state for encryption in TLS 1.3.

        :param int cipherSuite: cipher suite that will be used for encrypting
            and decrypting data
        :param bytearray cl_traffic_secret: Client Traffic Secret, either
            handshake secret or application data secret
        :param bytearray sr_traffic_secret: Server Traffic Secret, either
            handshake secret or application data secret
        :param list implementations: list of names of implementations that
            are permitted for the connection
        """
        prf_name = 'sha384' if cipherSuite \
                   in CipherSuite.sha384PrfSuites \
                   else 'sha256'

        key_length, iv_length, cipher_func = \
            self._getCipherSettings(cipherSuite)
        iv_length = 12

        clientPendingState = ConnectionState()
        serverPendingState = ConnectionState()

        clientPendingState.macContext = None
        clientPendingState.encContext = \
            cipher_func(HKDF_expand_label(cl_traffic_secret,
                                          b"key", b"",
                                          key_length,
                                          prf_name),
                        implementations)
        clientPendingState.fixedNonce = HKDF_expand_label(cl_traffic_secret,
                                                          b"iv", b"",
                                                          iv_length,
                                                          prf_name)

        serverPendingState.macContext = None
        serverPendingState.encContext = \
            cipher_func(HKDF_expand_label(sr_traffic_secret,
                                          b"key", b"",
                                          key_length,
                                          prf_name),
                        implementations)
        serverPendingState.fixedNonce = HKDF_expand_label(sr_traffic_secret,
                                                          b"iv", b"",
                                                          iv_length,
                                                          prf_name)

        if self.client:
            self._pendingWriteState = clientPendingState
            self._pendingReadState = serverPendingState
        else:
            self._pendingWriteState = serverPendingState
            self._pendingReadState = clientPendingState

    def _calcTLS1_3KeyUpdate(self, cipherSuite, app_secret):
        prf_name, prf_length = ('sha384', 48) if cipherSuite \
                                in CipherSuite.sha384PrfSuites \
                                else ('sha256', 32)
        key_length, iv_length, cipher_func = \
            self._getCipherSettings(cipherSuite)
        iv_length = 12

        new_app_secret = HKDF_expand_label(app_secret,
                                           b"traffic upd", b"",
                                           prf_length,
                                           prf_name)
        new_state = ConnectionState()
        new_state.macContext = None
        new_state.encContext = \
            cipher_func(HKDF_expand_label(new_app_secret,
                                          b"key", b"",
                                          key_length,
                                          prf_name),
                        None)
        new_state.fixedNonce = HKDF_expand_label(new_app_secret,
                                                 b"iv", b"",
                                                 iv_length,
                                                 prf_name)
        return new_app_secret, new_state

    def calcTLS1_3KeyUpdate_sender(self, cipherSuite, cl_app_secret,
                                   sr_app_secret):
        if self.client:
            new_sr_app_secret, server_state = self._calcTLS1_3KeyUpdate(
                cipherSuite, sr_app_secret)
            self._readState = server_state
            return cl_app_secret, new_sr_app_secret
        else:
            new_cl_app_secret, client_state = self._calcTLS1_3KeyUpdate(
                cipherSuite, cl_app_secret)
            self._readState = client_state
            return new_cl_app_secret, sr_app_secret

    def calcTLS1_3KeyUpdate_reciever(self, cipherSuite, cl_app_secret,
                                     sr_app_secret):
        if self.client:
            new_cl_app_secret, client_state = self._calcTLS1_3KeyUpdate(
                cipherSuite, cl_app_secret)
            self._writeState = client_state
            return new_cl_app_secret, sr_app_secret
        else:
            new_sr_app_secret, server_state = self._calcTLS1_3KeyUpdate(
                cipherSuite, sr_app_secret)
            self._writeState = server_state
            return cl_app_secret, new_sr_app_secret
