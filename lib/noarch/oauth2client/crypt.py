# -*- coding: utf-8 -*-
#
# Copyright 2014 Google Inc. All rights reserved.
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
"""Crypto-related routines for oauth2client."""

import json
import logging
import time

from oauth2client._helpers import _from_bytes
from oauth2client._helpers import _json_encode
from oauth2client._helpers import _to_bytes
from oauth2client._helpers import _urlsafe_b64decode
from oauth2client._helpers import _urlsafe_b64encode
from oauth2client._pure_python_crypt import RsaSigner
from oauth2client._pure_python_crypt import RsaVerifier


CLOCK_SKEW_SECS = 300  # 5 minutes in seconds
AUTH_TOKEN_LIFETIME_SECS = 300  # 5 minutes in seconds
MAX_TOKEN_LIFETIME_SECS = 86400  # 1 day in seconds

logger = logging.getLogger(__name__)


class AppIdentityError(Exception):
    """Error to indicate crypto failure."""


def _bad_pkcs12_key_as_pem(*args, **kwargs):
    raise NotImplementedError('pkcs12_key_as_pem requires OpenSSL.')


try:
    from oauth2client._openssl_crypt import OpenSSLVerifier
    from oauth2client._openssl_crypt import OpenSSLSigner
    from oauth2client._openssl_crypt import pkcs12_key_as_pem
except ImportError:  # pragma: NO COVER
    OpenSSLVerifier = None
    OpenSSLSigner = None
    pkcs12_key_as_pem = _bad_pkcs12_key_as_pem

try:
    from oauth2client._pycrypto_crypt import PyCryptoVerifier
    from oauth2client._pycrypto_crypt import PyCryptoSigner
except ImportError:  # pragma: NO COVER
    PyCryptoVerifier = None
    PyCryptoSigner = None


if OpenSSLSigner:
    Signer = OpenSSLSigner
    Verifier = OpenSSLVerifier
elif PyCryptoSigner:  # pragma: NO COVER
    Signer = PyCryptoSigner
    Verifier = PyCryptoVerifier
else:  # pragma: NO COVER
    Signer = RsaSigner
    Verifier = RsaVerifier


def make_signed_jwt(signer, payload, key_id=None):
    """Make a signed JWT.

    See http://self-issued.info/docs/draft-jones-json-web-token.html.

    Args:
        signer: crypt.Signer, Cryptographic signer.
        payload: dict, Dictionary of data to convert to JSON and then sign.
        key_id: string, (Optional) Key ID header.

    Returns:
        string, The JWT for the payload.
    """
    header = {'typ': 'JWT', 'alg': 'RS256'}
    if key_id is not None:
        header['kid'] = key_id

    segments = [
        _urlsafe_b64encode(_json_encode(header)),
        _urlsafe_b64encode(_json_encode(payload)),
    ]
    signing_input = b'.'.join(segments)

    signature = signer.sign(signing_input)
    segments.append(_urlsafe_b64encode(signature))

    logger.debug(str(segments))

    return b'.'.join(segments)


def _verify_signature(message, signature, certs):
    """Verifies signed content using a list of certificates.

    Args:
        message: string or bytes, The message to verify.
        signature: string or bytes, The signature on the message.
        certs: iterable, certificates in PEM format.

    Raises:
        AppIdentityError: If none of the certificates can verify the message
                          against the signature.
    """
    for pem in certs:
        verifier = Verifier.from_string(pem, is_x509_cert=True)
        if verifier.verify(message, signature):
            return

    # If we have not returned, no certificate confirms the signature.
    raise AppIdentityError('Invalid token signature')


def _check_audience(payload_dict, audience):
    """Checks audience field from a JWT payload.

    Does nothing if the passed in ``audience`` is null.

    Args:
        payload_dict: dict, A dictionary containing a JWT payload.
        audience: string or NoneType, an audience to check for in
                  the JWT payload.

    Raises:
        AppIdentityError: If there is no ``'aud'`` field in the payload
                          dictionary but there is an ``audience`` to check.
        AppIdentityError: If the ``'aud'`` field in the payload dictionary
                          does not match the ``audience``.
    """
    if audience is None:
        return

    audience_in_payload = payload_dict.get('aud')
    if audience_in_payload is None:
        raise AppIdentityError('No aud field in token: %s' %
                               (payload_dict,))
    if audience_in_payload != audience:
        raise AppIdentityError('Wrong recipient, %s != %s: %s' %
                               (audience_in_payload, audience, payload_dict))


def _verify_time_range(payload_dict):
    """Verifies the issued at and expiration from a JWT payload.

    Makes sure the current time (in UTC) falls between the issued at and
    expiration for the JWT (with some skew allowed for via
    ``CLOCK_SKEW_SECS``).

    Args:
        payload_dict: dict, A dictionary containing a JWT payload.

    Raises:
        AppIdentityError: If there is no ``'iat'`` field in the payload
                          dictionary.
        AppIdentityError: If there is no ``'exp'`` field in the payload
                          dictionary.
        AppIdentityError: If the JWT expiration is too far in the future (i.e.
                          if the expiration would imply a token lifetime
                          longer than what is allowed.)
        AppIdentityError: If the token appears to have been issued in the
                          future (up to clock skew).
        AppIdentityError: If the token appears to have expired in the past
                          (up to clock skew).
    """
    # Get the current time to use throughout.
    now = int(time.time())

    # Make sure issued at and expiration are in the payload.
    issued_at = payload_dict.get('iat')
    if issued_at is None:
        raise AppIdentityError('No iat field in token: %s' % (payload_dict,))
    expiration = payload_dict.get('exp')
    if expiration is None:
        raise AppIdentityError('No exp field in token: %s' % (payload_dict,))

    # Make sure the expiration gives an acceptable token lifetime.
    if expiration >= now + MAX_TOKEN_LIFETIME_SECS:
        raise AppIdentityError('exp field too far in future: %s' %
                               (payload_dict,))

    # Make sure (up to clock skew) that the token wasn't issued in the future.
    earliest = issued_at - CLOCK_SKEW_SECS
    if now < earliest:
        raise AppIdentityError('Token used too early, %d < %d: %s' %
                               (now, earliest, payload_dict))
    # Make sure (up to clock skew) that the token isn't already expired.
    latest = expiration + CLOCK_SKEW_SECS
    if now > latest:
        raise AppIdentityError('Token used too late, %d > %d: %s' %
                               (now, latest, payload_dict))


def verify_signed_jwt_with_certs(jwt, certs, audience=None):
    """Verify a JWT against public certs.

    See http://self-issued.info/docs/draft-jones-json-web-token.html.

    Args:
        jwt: string, A JWT.
        certs: dict, Dictionary where values of public keys in PEM format.
        audience: string, The audience, 'aud', that this JWT should contain. If
                  None then the JWT's 'aud' parameter is not verified.

    Returns:
        dict, The deserialized JSON payload in the JWT.

    Raises:
        AppIdentityError: if any checks are failed.
    """
    jwt = _to_bytes(jwt)

    if jwt.count(b'.') != 2:
        raise AppIdentityError(
            'Wrong number of segments in token: %s' % (jwt,))

    header, payload, signature = jwt.split(b'.')
    message_to_sign = header + b'.' + payload
    signature = _urlsafe_b64decode(signature)

    # Parse token.
    payload_bytes = _urlsafe_b64decode(payload)
    try:
        payload_dict = json.loads(_from_bytes(payload_bytes))
    except:
        raise AppIdentityError('Can\'t parse token: %s' % (payload_bytes,))

    # Verify that the signature matches the message.
    _verify_signature(message_to_sign, signature, certs.values())

    # Verify the issued at and created times in the payload.
    _verify_time_range(payload_dict)

    # Check audience.
    _check_audience(payload_dict, audience)

    return payload_dict
