# Copyright 2015 Google Inc. All rights reserved.
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
"""pyCrypto Crypto-related routines for oauth2client."""

from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from Crypto.Util.asn1 import DerSequence

from oauth2client._helpers import _parse_pem_key
from oauth2client._helpers import _to_bytes
from oauth2client._helpers import _urlsafe_b64decode


class PyCryptoVerifier(object):
    """Verifies the signature on a message."""

    def __init__(self, pubkey):
        """Constructor.

        Args:
            pubkey: OpenSSL.crypto.PKey (or equiv), The public key to verify
            with.
        """
        self._pubkey = pubkey

    def verify(self, message, signature):
        """Verifies a message against a signature.

        Args:
            message: string or bytes, The message to verify. If string, will be
                     encoded to bytes as utf-8.
            signature: string or bytes, The signature on the message.

        Returns:
            True if message was signed by the private key associated with the
            public key that this object was constructed with.
        """
        message = _to_bytes(message, encoding='utf-8')
        return PKCS1_v1_5.new(self._pubkey).verify(
            SHA256.new(message), signature)

    @staticmethod
    def from_string(key_pem, is_x509_cert):
        """Construct a Verified instance from a string.

        Args:
            key_pem: string, public key in PEM format.
            is_x509_cert: bool, True if key_pem is an X509 cert, otherwise it
                          is expected to be an RSA key in PEM format.

        Returns:
            Verifier instance.
        """
        if is_x509_cert:
            key_pem = _to_bytes(key_pem)
            pemLines = key_pem.replace(b' ', b'').split()
            certDer = _urlsafe_b64decode(b''.join(pemLines[1:-1]))
            certSeq = DerSequence()
            certSeq.decode(certDer)
            tbsSeq = DerSequence()
            tbsSeq.decode(certSeq[0])
            pubkey = RSA.importKey(tbsSeq[6])
        else:
            pubkey = RSA.importKey(key_pem)
        return PyCryptoVerifier(pubkey)


class PyCryptoSigner(object):
    """Signs messages with a private key."""

    def __init__(self, pkey):
        """Constructor.

        Args:
            pkey, OpenSSL.crypto.PKey (or equiv), The private key to sign with.
        """
        self._key = pkey

    def sign(self, message):
        """Signs a message.

        Args:
            message: string, Message to be signed.

        Returns:
            string, The signature of the message for the given key.
        """
        message = _to_bytes(message, encoding='utf-8')
        return PKCS1_v1_5.new(self._key).sign(SHA256.new(message))

    @staticmethod
    def from_string(key, password='notasecret'):
        """Construct a Signer instance from a string.

        Args:
            key: string, private key in PEM format.
            password: string, password for private key file. Unused for PEM
                      files.

        Returns:
            Signer instance.

        Raises:
            NotImplementedError if the key isn't in PEM format.
        """
        parsed_pem_key = _parse_pem_key(_to_bytes(key))
        if parsed_pem_key:
            pkey = RSA.importKey(parsed_pem_key)
        else:
            raise NotImplementedError(
                'No key in PEM format was detected. This implementation '
                'can only use the PyCrypto library for keys in PEM '
                'format.')
        return PyCryptoSigner(pkey)
