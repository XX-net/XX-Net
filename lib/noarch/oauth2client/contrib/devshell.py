# Copyright 2015 Google Inc. All Rights Reserved.
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

"""OAuth 2.0 utitilies for Google Developer Shell environment."""

import datetime
import json
import os
import socket

from oauth2client._helpers import _to_bytes
from oauth2client import client

# Expose utcnow() at module level to allow for
# easier testing (by replacing with a stub).
_UTCNOW = datetime.datetime.utcnow

DEVSHELL_ENV = 'DEVSHELL_CLIENT_PORT'


class Error(Exception):
    """Errors for this module."""
    pass


class CommunicationError(Error):
    """Errors for communication with the Developer Shell server."""


class NoDevshellServer(Error):
    """Error when no Developer Shell server can be contacted."""

# The request for credential information to the Developer Shell client socket
# is always an empty PBLite-formatted JSON object, so just define it as a
# constant.
CREDENTIAL_INFO_REQUEST_JSON = '[]'


class CredentialInfoResponse(object):
    """Credential information response from Developer Shell server.

    The credential information response from Developer Shell socket is a
    PBLite-formatted JSON array with fields encoded by their index in the
    array:

    * Index 0 - user email
    * Index 1 - default project ID. None if the project context is not known.
    * Index 2 - OAuth2 access token. None if there is no valid auth context.
    * Index 3 - Seconds until the access token expires. None if not present.
    """

    def __init__(self, json_string):
        """Initialize the response data from JSON PBLite array."""
        pbl = json.loads(json_string)
        if not isinstance(pbl, list):
            raise ValueError('Not a list: ' + str(pbl))
        pbl_len = len(pbl)
        self.user_email = pbl[0] if pbl_len > 0 else None
        self.project_id = pbl[1] if pbl_len > 1 else None
        self.access_token = pbl[2] if pbl_len > 2 else None
        self.expires_in = pbl[3] if pbl_len > 3 else None


def _SendRecv():
    """Communicate with the Developer Shell server socket."""

    port = int(os.getenv(DEVSHELL_ENV, 0))
    if port == 0:
        raise NoDevshellServer()

    sock = socket.socket()
    sock.connect(('localhost', port))

    data = CREDENTIAL_INFO_REQUEST_JSON
    msg = '%s\n%s' % (len(data), data)
    sock.sendall(_to_bytes(msg, encoding='utf-8'))

    header = sock.recv(6).decode()
    if '\n' not in header:
        raise CommunicationError('saw no newline in the first 6 bytes')
    len_str, json_str = header.split('\n', 1)
    to_read = int(len_str) - len(json_str)
    if to_read > 0:
        json_str += sock.recv(to_read, socket.MSG_WAITALL).decode()

    return CredentialInfoResponse(json_str)


class DevshellCredentials(client.GoogleCredentials):
    """Credentials object for Google Developer Shell environment.

    This object will allow a Google Developer Shell session to identify its
    user to Google and other OAuth 2.0 servers that can verify assertions. It
    can be used for the purpose of accessing data stored under the user
    account.

    This credential does not require a flow to instantiate because it
    represents a two legged flow, and therefore has all of the required
    information to generate and refresh its own access tokens.
    """

    def __init__(self, user_agent=None):
        super(DevshellCredentials, self).__init__(
            None,  # access_token, initialized below
            None,  # client_id
            None,  # client_secret
            None,  # refresh_token
            None,  # token_expiry
            None,  # token_uri
            user_agent)
        self._refresh(None)

    def _refresh(self, http_request):
        self.devshell_response = _SendRecv()
        self.access_token = self.devshell_response.access_token
        expires_in = self.devshell_response.expires_in
        if expires_in is not None:
            delta = datetime.timedelta(seconds=expires_in)
            self.token_expiry = _UTCNOW() + delta
        else:
            self.token_expiry = None

    @property
    def user_email(self):
        return self.devshell_response.user_email

    @property
    def project_id(self):
        return self.devshell_response.project_id

    @classmethod
    def from_json(cls, json_data):
        raise NotImplementedError(
            'Cannot load Developer Shell credentials from JSON.')

    @property
    def serialization_data(self):
        raise NotImplementedError(
            'Cannot serialize Developer Shell credentials.')
