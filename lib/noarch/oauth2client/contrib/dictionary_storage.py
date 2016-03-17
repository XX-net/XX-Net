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

"""Dictionary storage for OAuth2 Credentials."""

from oauth2client.client import OAuth2Credentials
from oauth2client.client import Storage


class DictionaryStorage(Storage):
    """Store and retrieve credentials to and from a dictionary-like object.

    Args:
        dictionary: A dictionary or dictionary-like object.
        key: A string or other hashable. The credentials will be stored in
             ``dictionary[key]``.
        lock: An optional threading.Lock-like object. The lock will be
              acquired before anything is written or read from the
              dictionary.
    """

    def __init__(self, dictionary, key, lock=None):
        """Construct a DictionaryStorage instance."""
        super(DictionaryStorage, self).__init__(lock=lock)
        self._dictionary = dictionary
        self._key = key

    def locked_get(self):
        """Retrieve the credentials from the dictionary, if they exist.

        Returns: A :class:`oauth2client.client.OAuth2Credentials` instance.
        """
        serialized = self._dictionary.get(self._key)

        if serialized is None:
            return None

        credentials = OAuth2Credentials.from_json(serialized)
        credentials.set_store(self)

        return credentials

    def locked_put(self, credentials):
        """Save the credentials to the dictionary.

        Args:
            credentials: A :class:`oauth2client.client.OAuth2Credentials`
                         instance.
        """
        serialized = credentials.to_json()
        self._dictionary[self._key] = serialized

    def locked_delete(self):
        """Remove the credentials from the dictionary, if they exist."""
        self._dictionary.pop(self._key, None)
