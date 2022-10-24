# Authors:
#   Trevor Perrin
#   Google - parsing subject field
#
# See the LICENSE file for legal information regarding use of this file.

"""Class representing an X.509 certificate."""

from ecdsa.keys import VerifyingKey

from .utils.asn1parser import ASN1Parser
from .utils.cryptomath import *
from .utils.keyfactory import _createPublicRSAKey, _create_public_ecdsa_key, \
    _create_public_dsa_key, _create_public_eddsa_key
from .utils.pem import *
from .utils.compat import compatHMAC, b2a_hex
from .constants import AlgorithmOID, RSA_PSS_OID


class X509(object):
    """
    This class represents an X.509 certificate.

    :vartype bytes: bytearray
    :ivar bytes: The DER-encoded ASN.1 certificate

    :vartype publicKey: ~tlslite.utils.rsakey.RSAKey
    :ivar publicKey: The subject public key from the certificate.

    :vartype subject: bytearray
    :ivar subject: The DER-encoded ASN.1 subject distinguished name.

    :vartype certAlg: str
    :ivar certAlg: algorithm of the public key, "rsa" for RSASSA-PKCS#1 v1.5,
        "rsa-pss" for RSASSA-PSS, "ecdsa" for ECDSA
    """

    def __init__(self):
        """Create empty certificate object."""
        self.bytes = bytearray(0)
        self.serial_number = None
        self.subject_public_key = None
        self.publicKey = None
        self.subject = None
        self.certAlg = None
        self.sigalg = None
        self.issuer = None

    def __hash__(self):
        """Calculate hash of object."""
        return hash(bytes(self.bytes))

    def __eq__(self, other):
        """Compare other object for equality."""
        if not hasattr(other, "bytes"):
            return NotImplemented
        return self.bytes == other.bytes

    def __ne__(self, other):
        """Compare with other object for inequality."""
        if not hasattr(other, "bytes"):
            return NotImplemented
        return not self == other

    def parse(self, s):
        """
        Parse a PEM-encoded X.509 certificate.

        :type s: str
        :param s: A PEM-encoded X.509 certificate (i.e. a base64-encoded
            certificate wrapped with "-----BEGIN CERTIFICATE-----" and
            "-----END CERTIFICATE-----" tags).
        """
        bytes = dePem(s, "CERTIFICATE")
        self.parseBinary(bytes)
        return self

    def parseBinary(self, cert_bytes):
        """
        Parse a DER-encoded X.509 certificate.

        :type bytes: L{str} (in python2) or L{bytearray} of unsigned bytes
        :param bytes: A DER-encoded X.509 certificate.
        """
        self.bytes = bytearray(cert_bytes)
        parser = ASN1Parser(self.bytes)

        # Get the SignatureAlgorithm
        signature_algorithm_identifier = parser.getChild(1)
        self.sigalg = bytes(signature_algorithm_identifier.getChildBytes(0))

        # Finally get the (hash, signature) pair coresponding to it
        # If it is rsa-pss we need to check the aditional parameters field
        # to extract the hash algorithm
        if self.sigalg == RSA_PSS_OID:
            sigalg_hash = signature_algorithm_identifier.getChild(1)
            sigalg_hash = bytes(sigalg_hash.getChild(0).value)
            self.sigalg = AlgorithmOID.oid[sigalg_hash]
        else:
            self.sigalg = AlgorithmOID.oid[self.sigalg]

        # Get the tbsCertificate
        tbs_certificate = parser.getChild(0)
        # Is the optional version field present?
        # This determines which index the key is at.
        if tbs_certificate.value[0] == 0xA0:
            serial_number_index = 1
            subject_public_key_info_index = 6
        else:
            serial_number_index = 0
            subject_public_key_info_index = 5

        # Get serial number
        self.serial_number = bytesToNumber(tbs_certificate.getChild(serial_number_index).value)

        # Get the issuer
        self.issuer = tbs_certificate.getChildBytes(
            subject_public_key_info_index - 3)

        # Get the subject
        self.subject = tbs_certificate.getChildBytes(
            subject_public_key_info_index - 1)

        # Get the subjectPublicKeyInfo
        subject_public_key_info = tbs_certificate.getChild(
            subject_public_key_info_index)

        # Get the AlgorithmIdentifier
        alg_identifier = subject_public_key_info.getChild(0)
        alg_identifier_len = alg_identifier.getChildCount()

        # first item of AlgorithmIdentifier is the algorithm
        alg = alg_identifier.getChild(0)
        alg_oid = alg.value
        if list(alg_oid) == [42, 134, 72, 134, 247, 13, 1, 1, 1]:
            self.certAlg = "rsa"
        elif list(alg_oid) == [42, 134, 72, 134, 247, 13, 1, 1, 10]:
            self.certAlg = "rsa-pss"
        elif list(alg_oid) == [42, 134, 72, 206, 56, 4, 1]:
            self.certAlg = "dsa"
        elif list(alg_oid) == [42, 134, 72, 206, 61, 2, 1]:
            self.certAlg = "ecdsa"
        elif list(alg_oid) == [43, 101, 112]:
            self.certAlg = "Ed25519"
        elif list(alg_oid) == [43, 101, 113]:
            self.certAlg = "Ed448"
        else:
            raise SyntaxError("Unrecognized AlgorithmIdentifier")

        # for RSA the parameters of AlgorithmIdentifier shuld be a NULL
        if self.certAlg == "rsa":
            if alg_identifier_len != 2:
                raise SyntaxError("Missing parameters in AlgorithmIdentifier")
            params = alg_identifier.getChild(1)
            if params.value != bytearray(0):
                raise SyntaxError("Unexpected non-NULL parameters in "
                                  "AlgorithmIdentifier")
        elif self.certAlg == "ecdsa":
            self._ecdsa_pubkey_parsing(
                tbs_certificate.getChildBytes(subject_public_key_info_index))
            return
        elif self.certAlg == "dsa":
            self._dsa_pubkey_parsing(subject_public_key_info)
            return
        elif self.certAlg == "Ed25519" or self.certAlg == "Ed448":
            self._eddsa_pubkey_parsing(
                tbs_certificate.getChildBytes(subject_public_key_info_index))
            return
        else:  # rsa-pss
            pass  # ignore parameters, if any - don't apply key restrictions

        self._rsa_pubkey_parsing(subject_public_key_info)

    def _eddsa_pubkey_parsing(self, subject_public_key_info):
        """
        Convert the raw DER encoded EdDSA parameters into public key object.

        :param subject_public_key_info: bytes like object with the DER encoded
            public key in it
        """
        try:
            # python ecdsa knows how to parse curve OIDs so re-use that
            # code
            public_key = VerifyingKey.from_der(compatHMAC(
                subject_public_key_info))
        except Exception:
            raise SyntaxError("Malformed or unsupported public key in "
                              "certificate")
        self.publicKey = _create_public_eddsa_key(public_key)

    def _rsa_pubkey_parsing(self, subject_public_key_info):
        """
        Parse the RSA public key from the certificate.

        :param subject_public_key_info: ASN1Parser object with subject
            public key info of X.509 certificate
        """

        # Get the subjectPublicKey
        subject_public_key = subject_public_key_info.getChild(1)
        self.subject_public_key = subject_public_key_info.getChildBytes(1)
        self.subject_public_key = ASN1Parser(self.subject_public_key).value[1:]

        # Adjust for BIT STRING encapsulation
        if subject_public_key.value[0]:
            raise SyntaxError()
        subject_public_key = ASN1Parser(subject_public_key.value[1:])

        # Get the modulus and exponent
        modulus = subject_public_key.getChild(0)
        public_exponent = subject_public_key.getChild(1)

        # Decode them into numbers
        # pylint: disable=invalid-name
        # 'n' and 'e' are the universally used parameters in RSA algorithm
        # definition
        n = bytesToNumber(modulus.value)
        e = bytesToNumber(public_exponent.value)

        # Create a public key instance
        self.publicKey = _createPublicRSAKey(n, e, self.certAlg)
        # pylint: enable=invalid-name

    def _ecdsa_pubkey_parsing(self, subject_public_key_info):
        """
        Convert the raw DER encoded ECDSA parameters into public key object

        :param subject_public_key_info: bytes like object with DER encoded
            public key in it
        """
        try:
            # python ecdsa knows how to parse curve OIDs so re-use that
            # code
            public_key = VerifyingKey.from_der(compatHMAC(
                subject_public_key_info))
        except Exception:
            raise SyntaxError("Malformed or unsupported public key in "
                              "certificate")
        x = public_key.pubkey.point.x()
        y = public_key.pubkey.point.y()
        curve_name = public_key.curve.name
        self.publicKey = _create_public_ecdsa_key(x, y, curve_name)

    def _dsa_pubkey_parsing(self, subject_public_key_info):
        """
        Convert the raw DER encoded DSA parameters into public key object

        :param subject_public_key_info: bytes like object with DER encoded
          global parameters and public key in it
        """
        global_parameters = (subject_public_key_info.getChild(0)).getChild(1)
        # Get the subjectPublicKey
        public_key = subject_public_key_info.getChild(1)

        # Adjust for BIT STRING encapsulation and get hex value
        if public_key.value[0]:
            raise SyntaxError()
        y = ASN1Parser(public_key.value[1:])

        # Get the {A, p, q}
        p = global_parameters.getChild(0)
        q = global_parameters.getChild(1)
        g = global_parameters.getChild(2)

        # Decode them into numbers
        y = bytesToNumber(y.value)
        p = bytesToNumber(p.value)
        q = bytesToNumber(q.value)
        g = bytesToNumber(g.value)

        # Create a public key instance
        self.publicKey = _create_public_dsa_key(p, q, g, y)

    def getFingerprint(self):
        """
        Get the hex-encoded fingerprint of this certificate.

        :rtype: str
        :returns: A hex-encoded fingerprint.
        """
        return b2a_hex(SHA1(self.bytes))

    def writeBytes(self):
        """Serialise object to a DER encoded string."""
        return self.bytes


