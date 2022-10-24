# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""Abstract class for RSA."""

from .cryptomath import *
from . import tlshashlib as hashlib
from ..errors import MaskTooLongError, MessageTooLongError, EncodingError, \
    InvalidSignature, UnknownRSAType
from .constanttime import ct_isnonzero_u32, ct_neq_u32, ct_lsb_prop_u8, \
    ct_lsb_prop_u16, ct_lt_u32


class RSAKey(object):
    """This is an abstract base class for RSA keys.

    Particular implementations of RSA keys, such as
    :py:class:`~.openssl_rsakey.OpenSSL_RSAKey`,
    :py:class:`~.python_rsakey.Python_RSAKey`, and
    :py:class:`~.pycrypto_rsakey.PyCrypto_RSAKey`,
    inherit from this.

    To create or parse an RSA key, don't use one of these classes
    directly.  Instead, use the factory functions in
    :py:class:`~tlslite.utils.keyfactory`.
    """

    def __init__(self, n=0, e=0, key_type="rsa"):
        """Create a new RSA key.

        If n and e are passed in, the new key will be initialized.

        :type n: int
        :param n: RSA modulus.

        :type e: int
        :param e: RSA public exponent.

        :type key_type: str
        :param key_type: type of the RSA key, "rsa" for rsaEncryption
            (universal, able to perform all operations) or "rsa-pss" for a
            RSASSA-PSS key (able to perform only RSA-PSS signature verification
            and creation)
        """
        # pylint: disable=invalid-name
        self.n = n
        self.e = e
        # pylint: enable=invalid-name
        self.key_type = key_type
        self._key_hash = None
        raise NotImplementedError()

    def __len__(self):
        """Return the length of this key in bits.

        :rtype: int
        """
        return numBits(self.n)

    def hasPrivateKey(self):
        """Return whether or not this key has a private component.

        :rtype: bool
        """
        raise NotImplementedError()

    def hashAndSign(self, bytes, rsaScheme='PKCS1', hAlg='sha1', sLen=0):
        """Hash and sign the passed-in bytes.

        This requires the key to have a private component.  It performs
        a PKCS1 or PSS signature on the passed-in data with selected hash
        algorithm.

        :type bytes: bytes-like object
        :param bytes: The value which will be hashed and signed.

        :type rsaScheme: str
        :param rsaScheme: The type of RSA scheme that will be applied,
                          "PKCS1" for RSASSA-PKCS#1 v1.5 signature and "PSS"
                          for RSASSA-PSS with MGF1 signature method

        :type hAlg: str
        :param hAlg: The hash algorithm that will be used

        :type sLen: int
        :param sLen: The length of intended salt value, applicable only
                     for RSASSA-PSS signatures

        :rtype: bytearray
        :returns: A PKCS1 or PSS signature on the passed-in data.
        """
        rsaScheme = rsaScheme.lower()
        hAlg = hAlg.lower()
        hashBytes = secureHash(bytearray(bytes), hAlg)
        return self.sign(hashBytes, padding=rsaScheme, hashAlg=hAlg,
                         saltLen=sLen)

    def hashAndVerify(self, sigBytes, bytes, rsaScheme='PKCS1', hAlg='sha1',
                      sLen=0):
        """Hash and verify the passed-in bytes with the signature.

        This verifies a PKCS1 or PSS signature on the passed-in data
        with selected hash algorithm.

        :type sigBytes: bytes-like object
        :param sigBytes: A PKCS1 or PSS signature.

        :type bytes: bytes-like object
        :param bytes: The value which will be hashed and verified.

        :type rsaScheme: str
        :param rsaScheme: The type of RSA scheme that will be applied,
                          "PKCS1" for RSASSA-PKCS#1 v1.5 signature and "PSS"
                          for RSASSA-PSS with MGF1 signature method

        :type hAlg: str
        :param hAlg: The hash algorithm that will be used

        :type sLen: int
        :param sLen: The length of intended salt value, applicable only
                     for RSASSA-PSS signatures

        :rtype: bool
        :returns: Whether the signature matches the passed-in data.
        """
        rsaScheme = rsaScheme.lower()
        hAlg = hAlg.lower()

        hashBytes = secureHash(bytearray(bytes), hAlg)
        return self.verify(sigBytes, hashBytes, rsaScheme, hAlg, sLen)

    def MGF1(self, mgfSeed, maskLen, hAlg):
        """Generate mask from passed-in seed.

        This generates mask based on passed-in seed and output maskLen.

        :type mgfSeed: bytearray
        :param mgfSeed: Seed from which mask will be generated.

        :type maskLen: int
        :param maskLen: Wished length of the mask, in octets

        :rtype: bytearray
        :returns: Mask
        """
        hashLen = getattr(hashlib, hAlg)().digest_size
        if maskLen > (2 ** 32) * hashLen:
            raise MaskTooLongError("Incorrect parameter maskLen")
        T = bytearray()
        end = divceil(maskLen, hashLen)
        for x in range(0, end):
            C = numberToByteArray(x, 4)
            T += secureHash(mgfSeed + C, hAlg)
        return T[:maskLen]

    def EMSA_PSS_encode(self, mHash, emBits, hAlg, sLen=0):
        """Encode the passed in message

        This encodes the message using selected hash algorithm

        :type mHash: bytearray
        :param mHash: Hash of message to be encoded

        :type emBits: int
        :param emBits: maximal length of returned EM

        :type hAlg: str
        :param hAlg: hash algorithm to be used

        :type sLen: int
        :param sLen: length of salt"""
        hashLen = getattr(hashlib, hAlg)().digest_size
        emLen = divceil(emBits, 8)
        if emLen < hashLen + sLen + 2:
            raise EncodingError("The ending limit too short for " +
                                "selected hash and salt length")
        salt = getRandomBytes(sLen)
        M2 = bytearray(8) + mHash + salt
        H = secureHash(M2, hAlg)
        PS = bytearray(emLen - sLen - hashLen - 2)
        DB = PS + bytearray(b'\x01') + salt
        dbMask = self.MGF1(H, emLen - hashLen - 1, hAlg)
        maskedDB = bytearray(i ^ j for i, j in zip(DB, dbMask))
        mLen = emLen*8 - emBits
        mask = (1 << 8 - mLen) - 1
        maskedDB[0] &= mask
        EM = maskedDB + H + bytearray(b'\xbc')
        return EM

    def RSASSA_PSS_sign(self, mHash, hAlg, sLen=0):
        """"Sign the passed in message

        This signs the message using selected hash algorithm

        :type mHash: bytes-like object
        :param mHash: Hash of message to be signed

        :type hAlg: str
        :param hAlg: hash algorithm to be used

        :type sLen: int
        :param sLen: length of salt"""
        EM = self.EMSA_PSS_encode(mHash, numBits(self.n) - 1, hAlg, sLen)
        try:
            ret = self._raw_private_key_op_bytes(EM)
        except ValueError:
            raise MessageTooLongError("Encode output too long")
        return ret

    def EMSA_PSS_verify(self, mHash, EM, emBits, hAlg, sLen=0):
        """Verify signature in passed in encoded message

        This verifies the signature in encoded message

        :type mHash: bytes-like object
        :param mHash: Hash of the original not signed message

        :type EM: bytes-like object
        :param EM: Encoded message

        :type emBits: int
        :param emBits: Length of the encoded message in bits

        :type hAlg: str
        :param hAlg: hash algorithm to be used

        :type sLen: int
        :param sLen: Length of salt
        """
        hashLen = getattr(hashlib, hAlg)().digest_size
        emLen = divceil(emBits, 8)
        if emLen < hashLen + sLen + 2:
            raise InvalidSignature("Invalid signature")
        if EM[-1] != 0xbc:
            raise InvalidSignature("Invalid signature")
        maskedDB = EM[0:emLen - hashLen - 1]
        H = EM[emLen - hashLen - 1:emLen - hashLen - 1 + hashLen]
        DBHelpMask = 1 << 8 - (8*emLen - emBits)
        DBHelpMask -= 1
        DBHelpMask = (~DBHelpMask) & 0xff
        if maskedDB[0] & DBHelpMask != 0:
            raise InvalidSignature("Invalid signature")
        dbMask = self.MGF1(H, emLen - hashLen - 1, hAlg)
        DB = bytearray(i ^ j for i, j in zip(maskedDB, dbMask))
        mLen = emLen*8 - emBits
        mask = (1 << 8 - mLen) - 1
        DB[0] &= mask
        if any(x != 0 for x in DB[0:emLen - hashLen - sLen - 2]):
            raise InvalidSignature("Invalid signature")
        if DB[emLen - hashLen - sLen - 2] != 0x01:
            raise InvalidSignature("Invalid signature")
        if sLen != 0:
            salt = DB[-sLen:]
        else:
            salt = bytearray()
        newM = bytearray(8) + mHash + salt
        newH = secureHash(newM, hAlg)
        if H == newH:
            return True
        else:
            raise InvalidSignature("Invalid signature")

    def RSASSA_PSS_verify(self, mHash, S, hAlg, sLen=0):
        """Verify the signature in passed in message

        This verifies the signature in the signed message

        :type mHash: bytes-like object
        :param mHash: Hash of original message

        :type S: bytes-like object
        :param S: Signed message

        :type hAlg: str
        :param hAlg: Hash algorithm to be used

        :type sLen: int
        :param sLen: Length of salt
        """
        try:
            EM = self._raw_public_key_op_bytes(S)
        except ValueError:
            raise InvalidSignature("Invalid signature")
        result = self.EMSA_PSS_verify(mHash, EM, numBits(self.n) - 1,
                                      hAlg, sLen)
        if result:
            return True
        else:
            raise InvalidSignature("Invalid signature")

    def _raw_pkcs1_sign(self, bytes):
        """Perform signature on raw data, add PKCS#1 padding."""
        if not self.hasPrivateKey():
            raise AssertionError()
        paddedBytes = self._addPKCS1Padding(bytes, 1)
        return self._raw_private_key_op_bytes(paddedBytes)

    def sign(self, bytes, padding='pkcs1', hashAlg=None, saltLen=None):
        """Sign the passed-in bytes.

        This requires the key to have a private component.  It performs
        a PKCS1 signature on the passed-in data.

        :type bytes: bytes-like object
        :param bytes: The value which will be signed.

        :type padding: str
        :param padding: name of the rsa padding mode to use, supported:
            "pkcs1" for RSASSA-PKCS1_1_5 and "pss" for RSASSA-PSS.

        :type hashAlg: str
        :param hashAlg: name of hash to be encoded using the PKCS#1 prefix
            for "pkcs1" padding or the hash used for MGF1 in "pss". Parameter
            is mandatory for "pss" padding.

        :type saltLen: int
        :param saltLen: length of salt used for the PSS padding. Default
            is the length of the hash output used.

        :rtype: bytearray
        :returns: A PKCS1 signature on the passed-in data.
        """
        padding = padding.lower()
        if padding == 'pkcs1':
            if hashAlg is not None:
                bytes = self.addPKCS1Prefix(bytes, hashAlg)
            sigBytes = self._raw_pkcs1_sign(bytes)
        elif padding == "pss":
            sigBytes = self.RSASSA_PSS_sign(bytes, hashAlg, saltLen)
        else:
            raise UnknownRSAType("Unknown RSA algorithm type")
        return sigBytes

    def _raw_pkcs1_verify(self, sigBytes, bytes):
        """Perform verification operation on raw PKCS#1 padded signature"""
        try:
            checkBytes = self._raw_public_key_op_bytes(sigBytes)
        except ValueError:
            return False
        paddedBytes = self._addPKCS1Padding(bytes, 1)
        return checkBytes == paddedBytes

    def verify(self, sigBytes, bytes, padding='pkcs1', hashAlg=None,
               saltLen=None):
        """Verify the passed-in bytes with the signature.

        This verifies a PKCS1 signature on the passed-in data.

        :type sigBytes: bytes-like object
        :param sigBytes: A PKCS1 signature.

        :type bytes: bytes-like object
        :param bytes: The value which will be verified.

        :rtype: bool
        :returns: Whether the signature matches the passed-in data.
        """
        if padding == "pkcs1" and self.key_type == "rsa-pss":
            return False
        if padding == "pkcs1" and hashAlg == 'sha1':
            # Try it with/without the embedded NULL
            prefixedHashBytes1 = self.addPKCS1SHA1Prefix(bytes, False)
            prefixedHashBytes2 = self.addPKCS1SHA1Prefix(bytes, True)
            result1 = self._raw_pkcs1_verify(sigBytes, prefixedHashBytes1)
            result2 = self._raw_pkcs1_verify(sigBytes, prefixedHashBytes2)
            return (result1 or result2)
        elif padding == 'pkcs1':
            if hashAlg is not None:
                bytes = self.addPKCS1Prefix(bytes, hashAlg)
            res = self._raw_pkcs1_verify(sigBytes, bytes)
            return res
        elif padding == "pss":
            try:
                res = self.RSASSA_PSS_verify(bytes, sigBytes, hashAlg, saltLen)
            except InvalidSignature:
                res = False
            return res
        else:
            raise UnknownRSAType("Unknown RSA algorithm type")

    def encrypt(self, bytes):
        """Encrypt the passed-in bytes.

        This performs PKCS1 encryption of the passed-in data.

        :type bytes: bytes-like object
        :param bytes: The value which will be encrypted.

        :rtype: bytearray
        :returns: A PKCS1 encryption of the passed-in data.
        """
        paddedBytes = self._addPKCS1Padding(bytes, 2)
        return self._raw_public_key_op_bytes(paddedBytes)

    def _dec_prf(self, key, label, out_len):
        """PRF for deterministic implicit rejection in the RSA decryption.

        :param bytes key: key to use for derivation
        :param bytes label: name of the keystream generated
        :param int out_len: length of output, in bits
        :rtype: bytes
        :returns: a random bytestring
        """
        out = bytearray()

        if out_len % 8 != 0:
            raise ValueError("only multiples of 8 supported as output size")

        iterator = 0
        while len(out) < out_len // 8:
            out += secureHMAC(
                key,
                numberToByteArray(iterator, 2) + label +
                numberToByteArray(out_len, 2),
                "sha256")
            iterator += 1

        return out[:out_len//8]

    def decrypt(self, encBytes):
        """Decrypt the passed-in bytes.

        This requires the key to have a private component.  It performs
        PKCS#1 v1.5 decryption operation of the passed-in data.

        Note: as a workaround against Bleichenbacher-like attacks, it will
        return a deterministically selected random message in case the padding
        checks failed. It returns an error (None) only in case the ciphertext
        is of incorrect length or encodes an integer bigger than the modulus
        of the key (i.e. it's publically invalid).

        :type encBytes: bytes-like object
        :param encBytes: The value which will be decrypted.

        :rtype: bytearray or None
        :returns: A PKCS#1 v1.5 decryption of the passed-in data or None if
            the provided data is not properly formatted. Note: encrypting
            an empty string is correct, so it may return an empty bytearray
            for some ciphertexts.
        """
        if not self.hasPrivateKey():
            raise AssertionError()
        if self.key_type != "rsa":
            raise ValueError("Decryption requires RSA key, \"{0}\" present"
                             .format(self.key_type))
        try:
            dec_bytes = self._raw_private_key_op_bytes(encBytes)
        except ValueError:
            # _raw_private_key_op_bytes fails only when encBytes >= self.n,
            # or when len(encBytes) != numBytes(self.n) and that's public
            # information, so we don't have to handle it
            # in sidechannel secure way
            return None

        ###################
        # here be dragons #
        ###################
        # While the code is written as-if it was side-channel secure, in
        # practice, because of cPython implementation details IT IS NOT
        # see:
        # https://securitypitfalls.wordpress.com/2018/08/03/constant-time-compare-in-python/

        n = self.n

        # maximum length we can return is reduced by the mandatory prefix:
        # (0x00 0x02), 8 bytes of padding, so this is the position of the
        # null separator byte, as counted from the last position
        max_sep_offset = numBytes(n) - 10

        # the private exponent (d) doesn't change so `_key_hash` doesn't
        # change, calculate it only once
        if not hasattr(self, '_key_hash') or not self._key_hash:
            self._key_hash = secureHash(numberToByteArray(self.d, numBytes(n)),
                                        "sha256")

        kdk = secureHMAC(self._key_hash, encBytes, "sha256")

        # we need 128 2-byte numbers, encoded as the number of bits
        length_randoms = self._dec_prf(kdk, b"length", 128 * 2 * 8)

        message_random = self._dec_prf(kdk, b"message", numBytes(n) * 8)

        # select the last length that's not too large to return
        synth_length = 0
        length_rand_iter = iter(length_randoms)
        length_mask = (1 << numBits(max_sep_offset)) - 1
        for high, low in zip(length_rand_iter, length_rand_iter):
            # interpret the two bytes from the PRF output as 16-bit big-endian
            # integer
            len_candidate = (high << 8) + low
            len_candidate &= length_mask
            # equivalent to:
            # if len_candidate < max_sep_offset:
            #    synth_length = len_candidate
            mask = ct_lt_u32(len_candidate, max_sep_offset)
            mask = ct_lsb_prop_u16(mask)
            synth_length = synth_length & (0xffff ^ mask) \
                | len_candidate & mask

        synth_msg_start = numBytes(n) - synth_length

        error_detected = 0

        # enumerate over all decrypted bytes
        em_bytes = enumerate(dec_bytes)
        # first check if first two bytes specify PKCS#1 v1.5 encryption padding
        _, val = next(em_bytes)
        error_detected |= ct_isnonzero_u32(val)
        _, val = next(em_bytes)
        error_detected |= ct_neq_u32(val, 0x02)
        # then look for for the null separator byte among the padding bytes
        # but inspect all decrypted bytes, even if we already find the
        # separator earlier
        msg_start = 0
        for pos, val in em_bytes:
            # padding must be at least 8 bytes long, fail if any of the first
            # 8 bytes of it are zero
            # equivalent to:
            # if pos < 10 and not val:
            #     error_detected = 0x01
            error_detected |= ct_lt_u32(pos, 10) & (1 ^ ct_isnonzero_u32(val))

            # update the msg_start only once; when it's 0
            # (pos+1) because we want to skip the null separator
            # equivalent to:
            # if pos >= 10 and not msg_start and not val:
            #     msg_start = pos+1
            mask = (1 ^ ct_lt_u32(pos, 10)) & (1 ^ ct_isnonzero_u32(val)) \
                & (1 ^ ct_isnonzero_u32(msg_start))
            mask = ct_lsb_prop_u16(mask)
            msg_start = msg_start & (0xffff ^ mask) | (pos+1) & mask

        # if separator wasn't found, it's an error
        # equivalent to:
        # if not msg_start:
        #     error_detected = 0x01
        error_detected |= 1 ^ ct_isnonzero_u32(msg_start)

        # equivalent to:
        # if error_detected:
        #     ret_msg_start = synth_msg_start
        # else:
        #     ret_msg_start = msg_start
        mask = ct_lsb_prop_u16(error_detected)
        ret_msg_start = msg_start & (0xffff ^ mask) | synth_msg_start & mask

        # as at this point the length doesn't leak the information if the
        # padding was correct or not, we don't have to worry about the
        # length of the returned value (and thus the size of the buffer we
        # pass to the caller); but we still need to read both buffers
        # to ensure that the memory access patern is preserved (that both
        # buffers are accessed, not just the one we return)

        # equivalent to:
        # if error_detected:
        #     return message_random[ret_msg_start:]
        # else:
        #     return dec_bytes[ret_msg_start:]
        mask = ct_lsb_prop_u8(error_detected)
        not_mask = 0xff ^ mask
        ret = bytearray(
            x & not_mask | y & mask for x, y in
            zip(dec_bytes[ret_msg_start:], message_random[ret_msg_start:]))

        return ret

    def _rawPrivateKeyOp(self, message):
        raise NotImplementedError()

    def _rawPublicKeyOp(self, ciphertext):
        raise NotImplementedError()

    def _raw_private_key_op_bytes(self, message):
        n = self.n
        if len(message) != numBytes(n):
            raise ValueError("Message has incorrect length for the key size")
        m_int = bytesToNumber(message)
        if m_int >= n:
            raise ValueError("Provided message value exceeds modulus")
        dec_int = self._rawPrivateKeyOp(m_int)
        return numberToByteArray(dec_int, numBytes(n))

    def _raw_public_key_op_bytes(self, ciphertext):
        n = self.n
        if len(ciphertext) != numBytes(n):
            raise ValueError("Message has incorrect length for the key size")
        c_int = bytesToNumber(ciphertext)
        if c_int >= n:
            raise ValueError("Provided message value exceeds modulus")
        enc_int = self._rawPublicKeyOp(c_int)
        return numberToByteArray(enc_int, numBytes(n))

    def acceptsPassword(self):
        """Return True if the write() method accepts a password for use
        in encrypting the private key.

        :rtype: bool
        """
        raise NotImplementedError()

    def write(self, password=None):
        """Return a string containing the key.

        :rtype: str
        :returns: A string describing the key, in whichever format (PEM)
            is native to the implementation.
        """
        raise NotImplementedError()

    @staticmethod
    def generate(bits, key_type="rsa"):
        """Generate a new key with the specified bit length.

        :rtype: ~tlslite.utils.RSAKey.RSAKey
        """
        raise NotImplementedError()


    # **************************************************************************
    # Helper Functions for RSA Keys
    # **************************************************************************

    @classmethod
    def addPKCS1SHA1Prefix(cls, hashBytes, withNULL=True):
        """Add PKCS#1 v1.5 algorithm identifier prefix to SHA1 hash bytes"""
        # There is a long history of confusion over whether the SHA1 
        # algorithmIdentifier should be encoded with a NULL parameter or 
        # with the parameter omitted.  While the original intention was 
        # apparently to omit it, many toolkits went the other way.  TLS 1.2
        # specifies the NULL should be included, and this behavior is also
        # mandated in recent versions of PKCS #1, and is what tlslite has
        # always implemented.  Anyways, verification code should probably 
        # accept both.
        if not withNULL:
            prefixBytes = bytearray([0x30, 0x1f, 0x30, 0x07, 0x06, 0x05, 0x2b,
                                     0x0e, 0x03, 0x02, 0x1a, 0x04, 0x14])
        else:
            prefixBytes = cls._pkcs1Prefixes['sha1']
        prefixedBytes = prefixBytes + hashBytes
        return prefixedBytes

    _pkcs1Prefixes = {'md5' : bytearray([0x30, 0x20, 0x30, 0x0c, 0x06, 0x08,
                                         0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d,
                                         0x02, 0x05, 0x05, 0x00, 0x04, 0x10]),
                      'sha1' : bytearray([0x30, 0x21, 0x30, 0x09, 0x06, 0x05,
                                          0x2b, 0x0e, 0x03, 0x02, 0x1a, 0x05,
                                          0x00, 0x04, 0x14]),
                      'sha224' : bytearray([0x30, 0x2d, 0x30, 0x0d, 0x06, 0x09,
                                            0x60, 0x86, 0x48, 0x01, 0x65, 0x03,
                                            0x04, 0x02, 0x04, 0x05, 0x00, 0x04,
                                            0x1c]),
                      'sha256' : bytearray([0x30, 0x31, 0x30, 0x0d, 0x06, 0x09,
                                            0x60, 0x86, 0x48, 0x01, 0x65, 0x03,
                                            0x04, 0x02, 0x01, 0x05, 0x00, 0x04,
                                            0x20]),
                      'sha384' : bytearray([0x30, 0x41, 0x30, 0x0d, 0x06, 0x09,
                                            0x60, 0x86, 0x48, 0x01, 0x65, 0x03,
                                            0x04, 0x02, 0x02, 0x05, 0x00, 0x04,
                                            0x30]),
                      'sha512' : bytearray([0x30, 0x51, 0x30, 0x0d, 0x06, 0x09,
                                            0x60, 0x86, 0x48, 0x01, 0x65, 0x03,
                                            0x04, 0x02, 0x03, 0x05, 0x00, 0x04,
                                            0x40])}

    @classmethod
    def addPKCS1Prefix(cls, data, hashName):
        """Add the PKCS#1 v1.5 algorithm identifier prefix to hash bytes"""
        hashName = hashName.lower()
        assert hashName in cls._pkcs1Prefixes
        prefixBytes = cls._pkcs1Prefixes[hashName]
        return prefixBytes + data

    def _addPKCS1Padding(self, bytes, blockType):
        padLength = (numBytes(self.n) - (len(bytes)+3))
        if blockType == 1: #Signature padding
            pad = [0xFF] * padLength
        elif blockType == 2: #Encryption padding
            pad = bytearray(0)
            while len(pad) < padLength:
                padBytes = getRandomBytes(padLength * 2)
                pad = [b for b in padBytes if b]
                pad = pad[:padLength]
        else:
            raise AssertionError()

        padding = bytearray([0,blockType] + pad + [0])
        return padding + bytes
