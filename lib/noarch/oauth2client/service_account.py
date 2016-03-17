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

"""oauth2client Service account credentials class."""

import base64
import copy
import datetime
import json
import time

from oauth2client import GOOGLE_REVOKE_URI
from oauth2client import GOOGLE_TOKEN_URI
from oauth2client._helpers import _json_encode
from oauth2client._helpers import _from_bytes
from oauth2client._helpers import _urlsafe_b64encode
from oauth2client import util
from oauth2client.client import AssertionCredentials
from oauth2client.client import EXPIRY_FORMAT
from oauth2client.client import SERVICE_ACCOUNT
from oauth2client import crypt


_PASSWORD_DEFAULT = 'notasecret'
_PKCS12_KEY = '_private_key_pkcs12'
_PKCS12_ERROR = r"""
This library only implements PKCS#12 support via the pyOpenSSL library.
Either install pyOpenSSL, or please convert the .p12 file
to .pem format:
    $ cat key.p12 | \
    >   openssl pkcs12 -nodes -nocerts -passin pass:notasecret | \
    >   openssl rsa > key.pem
"""


class ServiceAccountCredentials(AssertionCredentials):
    """Service Account credential for OAuth 2.0 signed JWT grants.

    Supports

    * JSON keyfile (typically contains a PKCS8 key stored as
      PEM text)
    * ``.p12`` key (stores PKCS12 key and certificate)

    Makes an assertion to server using a signed JWT assertion in exchange
    for an access token.

    This credential does not require a flow to instantiate because it
    represents a two legged flow, and therefore has all of the required
    information to generate and refresh its own access tokens.

    Args:
        service_account_email: string, The email associated with the
                               service account.
        signer: ``crypt.Signer``, A signer which can be used to sign content.
        scopes: List or string, (Optional) Scopes to use when acquiring
                an access token.
        private_key_id: string, (Optional) Private key identifier. Typically
                        only used with a JSON keyfile. Can be sent in the
                        header of a JWT token assertion.
        client_id: string, (Optional) Client ID for the project that owns the
                   service account.
        user_agent: string, (Optional) User agent to use when sending
                    request.
        kwargs: dict, Extra key-value pairs (both strings) to send in the
                payload body when making an assertion.
    """

    MAX_TOKEN_LIFETIME_SECS = 3600
    """Max lifetime of the token (one hour, in seconds)."""

    NON_SERIALIZED_MEMBERS =  (
        frozenset(['_signer']) |
        AssertionCredentials.NON_SERIALIZED_MEMBERS)
    """Members that aren't serialized when object is converted to JSON."""

    # Can be over-ridden by factory constructors. Used for
    # serialization/deserialization purposes.
    _private_key_pkcs8_pem = None
    _private_key_pkcs12 = None
    _private_key_password = None

    def __init__(self,
                 service_account_email,
                 signer,
                 scopes='',
                 private_key_id=None,
                 client_id=None,
                 user_agent=None,
                 **kwargs):

        super(ServiceAccountCredentials, self).__init__(
            None, user_agent=user_agent)

        self._service_account_email = service_account_email
        self._signer = signer
        self._scopes = util.scopes_to_string(scopes)
        self._private_key_id = private_key_id
        self.client_id = client_id
        self._user_agent = user_agent
        self._kwargs = kwargs

    def _to_json(self, strip, to_serialize=None):
        """Utility function that creates JSON repr. of a credentials object.

        Over-ride is needed since PKCS#12 keys will not in general be JSON
        serializable.

        Args:
            strip: array, An array of names of members to exclude from the
                   JSON.
            to_serialize: dict, (Optional) The properties for this object
                          that will be serialized. This allows callers to modify
                          before serializing.

        Returns:
            string, a JSON representation of this instance, suitable to pass to
            from_json().
        """
        if to_serialize is None:
            to_serialize = copy.copy(self.__dict__)
        pkcs12_val = to_serialize.get(_PKCS12_KEY)
        if pkcs12_val is not None:
            to_serialize[_PKCS12_KEY] = base64.b64encode(pkcs12_val)
        return super(ServiceAccountCredentials, self)._to_json(
            strip, to_serialize=to_serialize)

    @classmethod
    def _from_parsed_json_keyfile(cls, keyfile_dict, scopes):
        """Helper for factory constructors from JSON keyfile.

        Args:
            keyfile_dict: dict-like object, The parsed dictionary-like object
                          containing the contents of the JSON keyfile.
            scopes: List or string, Scopes to use when acquiring an
                    access token.

        Returns:
            ServiceAccountCredentials, a credentials object created from
            the keyfile contents.

        Raises:
            ValueError, if the credential type is not :data:`SERVICE_ACCOUNT`.
            KeyError, if one of the expected keys is not present in
                the keyfile.
        """
        creds_type = keyfile_dict.get('type')
        if creds_type != SERVICE_ACCOUNT:
            raise ValueError('Unexpected credentials type', creds_type,
                             'Expected', SERVICE_ACCOUNT)

        service_account_email = keyfile_dict['client_email']
        private_key_pkcs8_pem = keyfile_dict['private_key']
        private_key_id = keyfile_dict['private_key_id']
        client_id = keyfile_dict['client_id']

        signer = crypt.Signer.from_string(private_key_pkcs8_pem)
        credentials = cls(service_account_email, signer, scopes=scopes,
                          private_key_id=private_key_id,
                          client_id=client_id)
        credentials._private_key_pkcs8_pem = private_key_pkcs8_pem
        return credentials

    @classmethod
    def from_json_keyfile_name(cls, filename, scopes=''):
        """Factory constructor from JSON keyfile by name.

        Args:
            filename: string, The location of the keyfile.
            scopes: List or string, (Optional) Scopes to use when acquiring an
                    access token.

        Returns:
            ServiceAccountCredentials, a credentials object created from
            the keyfile.

        Raises:
            ValueError, if the credential type is not :data:`SERVICE_ACCOUNT`.
            KeyError, if one of the expected keys is not present in
                the keyfile.
        """
        with open(filename, 'r') as file_obj:
            client_credentials = json.load(file_obj)
        return cls._from_parsed_json_keyfile(client_credentials, scopes)

    @classmethod
    def from_json_keyfile_dict(cls, keyfile_dict, scopes=''):
        """Factory constructor from parsed JSON keyfile.

        Args:
            keyfile_dict: dict-like object, The parsed dictionary-like object
                          containing the contents of the JSON keyfile.
            scopes: List or string, (Optional) Scopes to use when acquiring an
                    access token.

        Returns:
            ServiceAccountCredentials, a credentials object created from
            the keyfile.

        Raises:
            ValueError, if the credential type is not :data:`SERVICE_ACCOUNT`.
            KeyError, if one of the expected keys is not present in
                the keyfile.
        """
        return cls._from_parsed_json_keyfile(keyfile_dict, scopes)

    @classmethod
    def _from_p12_keyfile_contents(cls, service_account_email,
                                   private_key_pkcs12,
                                   private_key_password=None, scopes=''):
        """Factory constructor from JSON keyfile.

        Args:
            service_account_email: string, The email associated with the
                                   service account.
            private_key_pkcs12: string, The contents of a PKCS#12 keyfile.
            private_key_password: string, (Optional) Password for PKCS#12
                                  private key. Defaults to ``notasecret``.
            scopes: List or string, (Optional) Scopes to use when acquiring an
                    access token.

        Returns:
            ServiceAccountCredentials, a credentials object created from
            the keyfile.

        Raises:
            NotImplementedError if pyOpenSSL is not installed / not the
            active crypto library.
        """
        if private_key_password is None:
            private_key_password = _PASSWORD_DEFAULT
        if crypt.Signer is not crypt.OpenSSLSigner:
            raise NotImplementedError(_PKCS12_ERROR)
        signer = crypt.Signer.from_string(private_key_pkcs12,
                                          private_key_password)
        credentials = cls(service_account_email, signer, scopes=scopes)
        credentials._private_key_pkcs12 = private_key_pkcs12
        credentials._private_key_password = private_key_password
        return credentials

    @classmethod
    def from_p12_keyfile(cls, service_account_email, filename,
                         private_key_password=None, scopes=''):
        """Factory constructor from JSON keyfile.

        Args:
            service_account_email: string, The email associated with the
                                   service account.
            filename: string, The location of the PKCS#12 keyfile.
            private_key_password: string, (Optional) Password for PKCS#12
                                  private key. Defaults to ``notasecret``.
            scopes: List or string, (Optional) Scopes to use when acquiring an
                    access token.

        Returns:
            ServiceAccountCredentials, a credentials object created from
            the keyfile.

        Raises:
            NotImplementedError if pyOpenSSL is not installed / not the
            active crypto library.
        """
        with open(filename, 'rb') as file_obj:
            private_key_pkcs12 = file_obj.read()
        return cls._from_p12_keyfile_contents(
            service_account_email, private_key_pkcs12,
            private_key_password=private_key_password, scopes=scopes)

    @classmethod
    def from_p12_keyfile_buffer(cls, service_account_email, file_buffer,
                                private_key_password=None, scopes=''):
        """Factory constructor from JSON keyfile.

        Args:
            service_account_email: string, The email associated with the
                                   service account.
            file_buffer: stream, A buffer that implements ``read()``
                         and contains the PKCS#12 key contents.
            private_key_password: string, (Optional) Password for PKCS#12
                                  private key. Defaults to ``notasecret``.
            scopes: List or string, (Optional) Scopes to use when acquiring an
                    access token.

        Returns:
            ServiceAccountCredentials, a credentials object created from
            the keyfile.

        Raises:
            NotImplementedError if pyOpenSSL is not installed / not the
            active crypto library.
        """
        private_key_pkcs12 = file_buffer.read()
        return cls._from_p12_keyfile_contents(
            service_account_email, private_key_pkcs12,
            private_key_password=private_key_password, scopes=scopes)

    def _generate_assertion(self):
        """Generate the assertion that will be used in the request."""
        now = int(time.time())
        payload = {
            'aud': self.token_uri,
            'scope': self._scopes,
            'iat': now,
            'exp': now + self.MAX_TOKEN_LIFETIME_SECS,
            'iss': self._service_account_email,
        }
        payload.update(self._kwargs)
        return crypt.make_signed_jwt(self._signer, payload,
                                     key_id=self._private_key_id)

    def sign_blob(self, blob):
        """Cryptographically sign a blob (of bytes).

        Implements abstract method
        :meth:`oauth2client.client.AssertionCredentials.sign_blob`.

        Args:
            blob: bytes, Message to be signed.

        Returns:
            tuple, A pair of the private key ID used to sign the blob and
            the signed contents.
        """
        return self._private_key_id, self._signer.sign(blob)

    @property
    def service_account_email(self):
        """Get the email for the current service account.

        Returns:
            string, The email associated with the service account.
        """
        return self._service_account_email

    @property
    def serialization_data(self):
        # NOTE: This is only useful for JSON keyfile.
        return {
            'type': 'service_account',
            'client_email': self._service_account_email,
            'private_key_id': self._private_key_id,
            'private_key': self._private_key_pkcs8_pem,
            'client_id': self.client_id,
        }

    @classmethod
    def from_json(cls, json_data):
        """Deserialize a JSON-serialized instance.

        Inverse to :meth:`to_json`.

        Args:
            json_data: dict or string, Serialized JSON (as a string or an
                       already parsed dictionary) representing a credential.

        Returns:
            ServiceAccountCredentials from the serialized data.
        """
        if not isinstance(json_data, dict):
            json_data = json.loads(_from_bytes(json_data))

        private_key_pkcs8_pem = None
        pkcs12_val = json_data.get(_PKCS12_KEY)
        password = None
        if pkcs12_val is None:
            private_key_pkcs8_pem = json_data['_private_key_pkcs8_pem']
            signer = crypt.Signer.from_string(private_key_pkcs8_pem)
        else:
            # NOTE: This assumes that private_key_pkcs8_pem is not also
            #       in the serialized data. This would be very incorrect
            #       state.
            pkcs12_val = base64.b64decode(pkcs12_val)
            password = json_data['_private_key_password']
            signer = crypt.Signer.from_string(pkcs12_val, password)

        credentials = cls(
            json_data['_service_account_email'],
            signer,
            scopes=json_data['_scopes'],
            private_key_id=json_data['_private_key_id'],
            client_id=json_data['client_id'],
            user_agent=json_data['_user_agent'],
            **json_data['_kwargs']
        )
        if private_key_pkcs8_pem is not None:
            credentials._private_key_pkcs8_pem = private_key_pkcs8_pem
        if pkcs12_val is not None:
            credentials._private_key_pkcs12 = pkcs12_val
        if password is not None:
            credentials._private_key_password = password
        credentials.invalid = json_data['invalid']
        credentials.access_token = json_data['access_token']
        credentials.token_uri = json_data['token_uri']
        credentials.revoke_uri = json_data['revoke_uri']
        token_expiry = json_data.get('token_expiry', None)
        if token_expiry is not None:
            credentials.token_expiry = datetime.datetime.strptime(
                token_expiry, EXPIRY_FORMAT)
        return credentials

    def create_scoped_required(self):
        return not self._scopes

    def create_scoped(self, scopes):
        result = self.__class__(self._service_account_email,
                                self._signer,
                                scopes=scopes,
                                private_key_id=self._private_key_id,
                                client_id=self.client_id,
                                user_agent=self._user_agent,
                                **self._kwargs)
        result.token_uri = self.token_uri
        result.revoke_uri = self.revoke_uri
        result._private_key_pkcs8_pem = self._private_key_pkcs8_pem
        result._private_key_pkcs12 = self._private_key_pkcs12
        result._private_key_password = self._private_key_password
        return result

    def create_delegated(self, sub):
        """Create credentials that act as domain-wide delegation of authority.

        Use the ``sub`` parameter as the subject to delegate on behalf of
        that user.

        For example::

          >>> account_sub = 'foo@email.com'
          >>> delegate_creds = creds.create_delegated(account_sub)

        Args:
            sub: string, An email address that this service account will
                 act on behalf of (via domain-wide delegation).

        Returns:
            ServiceAccountCredentials, a copy of the current service account
            updated to act on behalf of ``sub``.
        """
        new_kwargs = dict(self._kwargs)
        new_kwargs['sub'] = sub
        result = self.__class__(self._service_account_email,
                                self._signer,
                                scopes=self._scopes,
                                private_key_id=self._private_key_id,
                                client_id=self.client_id,
                                user_agent=self._user_agent,
                                **new_kwargs)
        result.token_uri = self.token_uri
        result.revoke_uri = self.revoke_uri
        result._private_key_pkcs8_pem = self._private_key_pkcs8_pem
        result._private_key_pkcs12 = self._private_key_pkcs12
        result._private_key_password = self._private_key_password
        return result
