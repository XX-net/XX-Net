# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Pure Python crypto-related routines for oauth2client.

Uses the ``rsa``, ``pyasn1`` and ``pyasn1_modules`` packages
to parse PEM files storing PKCS#1 or PKCS#8 keys as well as
certificates.
"""

from pyasn1.codec.der import decoder
from pyasn1_modules import pem
from pyasn1_modules.rfc2459 import Certificate
from pyasn1_modules.rfc5208 import PrivateKeyInfo
import rsa
import six

from oauth2client._helpers import _from_bytes
from oauth2client._helpers import _to_bytes


_PKCS12_ERROR = r"""\
PKCS12 format is not supported by the RSA library.
Either install PyOpenSSL, or please convert .p12 format
to .pem format:
    $ cat key.p12 | \
    >   openssl pkcs12 -nodes -nocerts -passin pass:notasecret | \
    >   openssl rsa > key.pem
"""

_POW2 = (128, 64, 32, 16, 8, 4, 2, 1)
_PKCS1_MARKER = ('-----BEGIN RSA PRIVATE KEY-----',
                 '-----END RSA PRIVATE KEY-----')
_PKCS8_MARKER = ('-----BEGIN PRIVATE KEY-----',
                 '-----END PRIVATE KEY-----')
_PKCS8_SPEC = PrivateKeyInfo()


def _bit_list_to_bytes(bit_list):
    """Converts an iterable of 1's and 0's to bytes.

    Combines the list 8 at a time, treating each group of 8 bits
    as a single byte.
    """
    num_bits = len(bit_list)
    byte_vals = bytearray()
    for start in six.moves.xrange(0, num_bits, 8):
        curr_bits = bit_list[start:start + 8]
        char_val = sum(val * digit
                       for val, digit in zip(_POW2, curr_bits))
        byte_vals.append(char_val)
    return bytes(byte_vals)


class RsaVerifier(object):
    """Verifies the signature on a message.

    Args:
        pubkey: rsa.key.PublicKey (or equiv), The public key to verify with.
    """

    def __init__(self, pubkey):
        self._pubkey = pubkey

    def verify(self, message, signature):
        """Verifies a message against a signature.

        Args:
            message: string or bytes, The message to verify. If string, will be
                     encoded to bytes as utf-8.
            signature: string or bytes, The signature on the message. If
                       string, will be encoded to bytes as utf-8.

        Returns:
            True if message was signed by the private key associated with the
            public key that this object was constructed with.
        """
        message = _to_bytes(message, encoding='utf-8')
        try:
            return rsa.pkcs1.verify(message, signature, self._pubkey)
        except (ValueError, rsa.pkcs1.VerificationError):
            return False

    @classmethod
    def from_string(cls, key_pem, is_x509_cert):
        """Construct an RsaVerifier instance from a string.

        Args:
            key_pem: string, public key in PEM format.
            is_x509_cert: bool, True if key_pem is an X509 cert, otherwise it
                          is expected to be an RSA key in PEM format.

        Returns:
            RsaVerifier instance.

        Raises:
            ValueError: if the key_pem can't be parsed. In either case, error
                        will begin with 'No PEM start marker'. If
                        ``is_x509_cert`` is True, will fail to find the
                        "-----BEGIN CERTIFICATE-----" error, otherwise fails
                        to find "-----BEGIN RSA PUBLIC KEY-----".
        """
        key_pem = _to_bytes(key_pem)
        if is_x509_cert:
            der = rsa.pem.load_pem(key_pem, 'CERTIFICATE')
            asn1_cert, remaining = decoder.decode(der, asn1Spec=Certificate())
            if remaining != b'':
                raise ValueError('Unused bytes', remaining)

            cert_info = asn1_cert['tbsCertificate']['subjectPublicKeyInfo']
            key_bytes = _bit_list_to_bytes(cert_info['subjectPublicKey'])
            pubkey = rsa.PublicKey.load_pkcs1(key_bytes, 'DER')
        else:
            pubkey = rsa.PublicKey.load_pkcs1(key_pem, 'PEM')
        return cls(pubkey)


class RsaSigner(object):
    """Signs messages with a private key.

    Args:
        pkey: rsa.key.PrivateKey (or equiv), The private key to sign with.
    """

    def __init__(self, pkey):
        self._key = pkey

    def sign(self, message):
        """Signs a message.

        Args:
            message: bytes, Message to be signed.

        Returns:
            string, The signature of the message for the given key.
        """
        message = _to_bytes(message, encoding='utf-8')
        return rsa.pkcs1.sign(message, self._key, 'SHA-256')

    @classmethod
    def from_string(cls, key, password='notasecret'):
        """Construct an RsaSigner instance from a string.

        Args:
            key: string, private key in PEM format.
            password: string, password for private key file. Unused for PEM
                      files.

        Returns:
            RsaSigner instance.

        Raises:
            ValueError if the key cannot be parsed as PKCS#1 or PKCS#8 in
            PEM format.
        """
        key = _from_bytes(key)  # pem expects str in Py3
        marker_id, key_bytes = pem.readPemBlocksFromFile(
            six.StringIO(key), _PKCS1_MARKER, _PKCS8_MARKER)

        if marker_id == 0:
            pkey = rsa.key.PrivateKey.load_pkcs1(key_bytes,
                                                 format='DER')
        elif marker_id == 1:
            key_info, remaining = decoder.decode(
                key_bytes, asn1Spec=_PKCS8_SPEC)
            if remaining != b'':
                raise ValueError('Unused bytes', remaining)
            pkey_info = key_info.getComponentByName('privateKey')
            pkey = rsa.key.PrivateKey.load_pkcs1(pkey_info.asOctets(),
                                                 format='DER')
        else:
            raise ValueError('No key could be detected.')

        return cls(pkey)
