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

"""A keyring based Storage.

A Storage for Credentials that uses the keyring module.
"""

import threading

import keyring

from oauth2client.client import Credentials
from oauth2client.client import Storage as BaseStorage


__author__ = 'jcgregorio@google.com (Joe Gregorio)'


class Storage(BaseStorage):
    """Store and retrieve a single credential to and from the keyring.

    To use this module you must have the keyring module installed. See
    <http://pypi.python.org/pypi/keyring/>. This is an optional module and is
    not installed with oauth2client by default because it does not work on all
    the platforms that oauth2client supports, such as Google App Engine.

    The keyring module <http://pypi.python.org/pypi/keyring/> is a
    cross-platform library for access the keyring capabilities of the local
    system. The user will be prompted for their keyring password when this
    module is used, and the manner in which the user is prompted will vary per
    platform.

    Usage::

        from oauth2client.keyring_storage import Storage

        s = Storage('name_of_application', 'user1')
        credentials = s.get()

    """

    def __init__(self, service_name, user_name):
        """Constructor.

        Args:
            service_name: string, The name of the service under which the
                          credentials are stored.
            user_name: string, The name of the user to store credentials for.
        """
        super(Storage, self).__init__(lock=threading.Lock())
        self._service_name = service_name
        self._user_name = user_name

    def locked_get(self):
        """Retrieve Credential from file.

        Returns:
            oauth2client.client.Credentials
        """
        credentials = None
        content = keyring.get_password(self._service_name, self._user_name)

        if content is not None:
            try:
                credentials = Credentials.new_from_json(content)
                credentials.set_store(self)
            except ValueError:
                pass

        return credentials

    def locked_put(self, credentials):
        """Write Credentials to file.

        Args:
            credentials: Credentials, the credentials to store.
        """
        keyring.set_password(self._service_name, self._user_name,
                             credentials.to_json())

    def locked_delete(self):
        """Delete Credentials file.

        Args:
            credentials: Credentials, the credentials to store.
        """
        keyring.set_password(self._service_name, self._user_name, '')
