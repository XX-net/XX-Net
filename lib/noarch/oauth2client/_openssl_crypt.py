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
"""OpenSSL Crypto-related routines for oauth2client."""

import base64

from OpenSSL import crypto

from oauth2client._helpers import _parse_pem_key
from oauth2client._helpers import _to_bytes


class OpenSSLVerifier(object):
    """Verifies the signature on a message."""

    def __init__(self, pubkey):
        """Constructor.

        Args:
            pubkey: OpenSSL.crypto.PKey, The public key to verify with.
        """
        self._pubkey = pubkey

    def verify(self, message, signature):
        """Verifies a message against a signature.

        Args:
        message: string or bytes, The message to verify. If string, will be
                 encoded to bytes as utf-8.
        signature: string or bytes, The signature on the message. If string,
                   will be encoded to bytes as utf-8.

        Returns:
            True if message was signed by the private key associated with the
            public key that this object was constructed with.
        """
        message = _to_bytes(message, encoding='utf-8')
        signature = _to_bytes(signature, encoding='utf-8')
        try:
            crypto.verify(self._pubkey, signature, message, 'sha256')
            return True
        except crypto.Error:
            return False

    @staticmethod
    def from_string(key_pem, is_x509_cert):
        """Construct a Verified instance from a string.

        Args:
            key_pem: string, public key in PEM format.
            is_x509_cert: bool, True if key_pem is an X509 cert, otherwise it
                          is expected to be an RSA key in PEM format.

        Returns:
            Verifier instance.

        Raises:
            OpenSSL.crypto.Error: if the key_pem can't be parsed.
        """
        key_pem = _to_bytes(key_pem)
        if is_x509_cert:
            pubkey = crypto.load_certificate(crypto.FILETYPE_PEM, key_pem)
        else:
            pubkey = crypto.load_privatekey(crypto.FILETYPE_PEM, key_pem)
        return OpenSSLVerifier(pubkey)


class OpenSSLSigner(object):
    """Signs messages with a private key."""

    def __init__(self, pkey):
        """Constructor.

        Args:
            pkey: OpenSSL.crypto.PKey (or equiv), The private key to sign with.
        """
        self._key = pkey

    def sign(self, message):
        """Signs a message.

        Args:
            message: bytes, Message to be signed.

        Returns:
            string, The signature of the message for the given key.
        """
        message = _to_bytes(message, encoding='utf-8')
        return crypto.sign(self._key, message, 'sha256')

    @staticmethod
    def from_string(key, password=b'notasecret'):
        """Construct a Signer instance from a string.

        Args:
            key: string, private key in PKCS12 or PEM format.
            password: string, password for the private key file.

        Returns:
            Signer instance.

        Raises:
            OpenSSL.crypto.Error if the key can't be parsed.
        """
        key = _to_bytes(key)
        parsed_pem_key = _parse_pem_key(key)
        if parsed_pem_key:
            pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, parsed_pem_key)
        else:
            password = _to_bytes(password, encoding='utf-8')
            pkey = crypto.load_pkcs12(key, password).get_privatekey()
        return OpenSSLSigner(pkey)


def pkcs12_key_as_pem(private_key_bytes, private_key_password):
    """Convert the contents of a PKCS#12 key to PEM using pyOpenSSL.

    Args:
        private_key_bytes: Bytes. PKCS#12 key in DER format.
        private_key_password: String. Password for PKCS#12 key.

    Returns:
        String. PEM contents of ``private_key_bytes``.
    """
    private_key_password = _to_bytes(private_key_password)
    pkcs12 = crypto.load_pkcs12(private_key_bytes, private_key_password)
    return crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                  pkcs12.get_privatekey())
