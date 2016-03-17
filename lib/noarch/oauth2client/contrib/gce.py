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

"""Utilities for Google Compute Engine

Utilities for making it easier to use OAuth 2.0 on Google Compute Engine.
"""

import json
import logging
import warnings

import httplib2
from six.moves import http_client
from six.moves import urllib

from oauth2client._helpers import _from_bytes
from oauth2client import util
from oauth2client.client import HttpAccessTokenRefreshError
from oauth2client.client import AssertionCredentials


__author__ = 'jcgregorio@google.com (Joe Gregorio)'

logger = logging.getLogger(__name__)

# URI Template for the endpoint that returns access_tokens.
_METADATA_ROOT = ('http://metadata.google.internal/computeMetadata/v1/'
                  'instance/service-accounts/default/')
META = _METADATA_ROOT + 'token'
_DEFAULT_EMAIL_METADATA = _METADATA_ROOT + 'email'
_SCOPES_WARNING = """\
You have requested explicit scopes to be used with a GCE service account.
Using this argument will have no effect on the actual scopes for tokens
requested. These scopes are set at VM instance creation time and
can't be overridden in the request.
"""


def _get_service_account_email(http_request=None):
    """Get the GCE service account email from the current environment.

    Args:
        http_request: callable, (Optional) a callable that matches the method
                      signature of httplib2.Http.request, used to make
                      the request to the metadata service.

    Returns:
        tuple, A pair where the first entry is an optional response (from a
        failed request) and the second is service account email found (as
        a string).
    """
    if http_request is None:
        http_request = httplib2.Http().request
    response, content = http_request(
        _DEFAULT_EMAIL_METADATA, headers={'Metadata-Flavor': 'Google'})
    if response.status == http_client.OK:
        content = _from_bytes(content)
        return None, content
    else:
        return response, content


class AppAssertionCredentials(AssertionCredentials):
    """Credentials object for Compute Engine Assertion Grants

    This object will allow a Compute Engine instance to identify itself to
    Google and other OAuth 2.0 servers that can verify assertions. It can be
    used for the purpose of accessing data stored under an account assigned to
    the Compute Engine instance itself.

    This credential does not require a flow to instantiate because it
    represents a two legged flow, and therefore has all of the required
    information to generate and refresh its own access tokens.
    """

    @util.positional(2)
    def __init__(self, scope='', **kwargs):
        """Constructor for AppAssertionCredentials

        Args:
            scope: string or iterable of strings, scope(s) of the credentials
                   being requested. Using this argument will have no effect on
                   the actual scopes for tokens requested. These scopes are
                   set at VM instance creation time and won't change.
        """
        if scope:
            warnings.warn(_SCOPES_WARNING)
        # This is just provided for backwards compatibility, but is not
        # used by this class.
        self.scope = util.scopes_to_string(scope)
        self.kwargs = kwargs

        # Assertion type is no longer used, but still in the
        # parent class signature.
        super(AppAssertionCredentials, self).__init__(None)
        self._service_account_email = None

    @classmethod
    def from_json(cls, json_data):
        data = json.loads(_from_bytes(json_data))
        return AppAssertionCredentials(data['scope'])

    def _refresh(self, http_request):
        """Refreshes the access_token.

        Skip all the storage hoops and just refresh using the API.

        Args:
            http_request: callable, a callable that matches the method
                          signature of httplib2.Http.request, used to make
                          the refresh request.

        Raises:
            HttpAccessTokenRefreshError: When the refresh fails.
        """
        response, content = http_request(
            META, headers={'Metadata-Flavor': 'Google'})
        content = _from_bytes(content)
        if response.status == http_client.OK:
            try:
                token_content = json.loads(content)
            except Exception as e:
                raise HttpAccessTokenRefreshError(str(e),
                                                  status=response.status)
            self.access_token = token_content['access_token']
        else:
            if response.status == http_client.NOT_FOUND:
                content += (' This can occur if a VM was created'
                            ' with no service account or scopes.')
            raise HttpAccessTokenRefreshError(content, status=response.status)

    @property
    def serialization_data(self):
        raise NotImplementedError(
            'Cannot serialize credentials for GCE service accounts.')

    def create_scoped_required(self):
        return False

    def create_scoped(self, scopes):
        return AppAssertionCredentials(scopes, **self.kwargs)

    def sign_blob(self, blob):
        """Cryptographically sign a blob (of bytes).

        This method is provided to support a common interface, but
        the actual key used for a Google Compute Engine service account
        is not available, so it can't be used to sign content.

        Args:
            blob: bytes, Message to be signed.

        Raises:
            NotImplementedError, always.
        """
        raise NotImplementedError(
            'Compute Engine service accounts cannot sign blobs')

    @property
    def service_account_email(self):
        """Get the email for the current service account.

        Uses the Google Compute Engine metadata service to retrieve the email
        of the default service account.

        Returns:
            string, The email associated with the Google Compute Engine
            service account.

        Raises:
            AttributeError, if the email can not be retrieved from the Google
            Compute Engine metadata service.
        """
        if self._service_account_email is None:
            failure, email = _get_service_account_email()
            if failure is None:
                self._service_account_email = email
            else:
                raise AttributeError('Failed to retrieve the email from the '
                                     'Google Compute Engine metadata service',
                                     failure, email)
        return self._service_account_email
