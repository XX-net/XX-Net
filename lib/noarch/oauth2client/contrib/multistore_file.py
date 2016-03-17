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

"""Multi-credential file store with lock support.

This module implements a JSON credential store where multiple
credentials can be stored in one file. That file supports locking
both in a single process and across processes.

The credential themselves are keyed off of:

* client_id
* user_agent
* scope

The format of the stored data is like so::

    {
      'file_version': 1,
      'data': [
          {
              'key': {
                  'clientId': '<client id>',
                  'userAgent': '<user agent>',
                  'scope': '<scope>'
              },
              'credential': {
                  # JSON serialized Credentials.
              }
          }
      ]
    }

"""

import errno
import json
import logging
import os
import threading

from oauth2client.client import Credentials
from oauth2client.client import Storage as BaseStorage
from oauth2client import util
from oauth2client.contrib.locked_file import LockedFile


__author__ = 'jbeda@google.com (Joe Beda)'

logger = logging.getLogger(__name__)

# A dict from 'filename'->_MultiStore instances
_multistores = {}
_multistores_lock = threading.Lock()


class Error(Exception):
    """Base error for this module."""


class NewerCredentialStoreError(Error):
    """The credential store is a newer version than supported."""


def _dict_to_tuple_key(dictionary):
    """Converts a dictionary to a tuple that can be used as an immutable key.

    The resulting key is always sorted so that logically equivalent
    dictionaries always produce an identical tuple for a key.

    Args:
        dictionary: the dictionary to use as the key.

    Returns:
        A tuple representing the dictionary in it's naturally sorted ordering.
    """
    return tuple(sorted(dictionary.items()))


@util.positional(4)
def get_credential_storage(filename, client_id, user_agent, scope,
                           warn_on_readonly=True):
    """Get a Storage instance for a credential.

    Args:
        filename: The JSON file storing a set of credentials
        client_id: The client_id for the credential
        user_agent: The user agent for the credential
        scope: string or iterable of strings, Scope(s) being requested
        warn_on_readonly: if True, log a warning if the store is readonly

    Returns:
        An object derived from client.Storage for getting/setting the
        credential.
    """
    # Recreate the legacy key with these specific parameters
    key = {'clientId': client_id, 'userAgent': user_agent,
           'scope': util.scopes_to_string(scope)}
    return get_credential_storage_custom_key(
      filename, key, warn_on_readonly=warn_on_readonly)


@util.positional(2)
def get_credential_storage_custom_string_key(filename, key_string,
                                             warn_on_readonly=True):
    """Get a Storage instance for a credential using a single string as a key.

    Allows you to provide a string as a custom key that will be used for
    credential storage and retrieval.

    Args:
        filename: The JSON file storing a set of credentials
        key_string: A string to use as the key for storing this credential.
        warn_on_readonly: if True, log a warning if the store is readonly

    Returns:
        An object derived from client.Storage for getting/setting the
        credential.
    """
    # Create a key dictionary that can be used
    key_dict = {'key': key_string}
    return get_credential_storage_custom_key(
      filename, key_dict, warn_on_readonly=warn_on_readonly)


@util.positional(2)
def get_credential_storage_custom_key(filename, key_dict,
                                      warn_on_readonly=True):
    """Get a Storage instance for a credential using a dictionary as a key.

    Allows you to provide a dictionary as a custom key that will be used for
    credential storage and retrieval.

    Args:
        filename: The JSON file storing a set of credentials
        key_dict: A dictionary to use as the key for storing this credential.
                  There is no ordering of the keys in the dictionary. Logically
                  equivalent dictionaries will produce equivalent storage keys.
        warn_on_readonly: if True, log a warning if the store is readonly

    Returns:
        An object derived from client.Storage for getting/setting the
        credential.
    """
    multistore = _get_multistore(filename, warn_on_readonly=warn_on_readonly)
    key = _dict_to_tuple_key(key_dict)
    return multistore._get_storage(key)


@util.positional(1)
def get_all_credential_keys(filename, warn_on_readonly=True):
    """Gets all the registered credential keys in the given Multistore.

    Args:
        filename: The JSON file storing a set of credentials
        warn_on_readonly: if True, log a warning if the store is readonly

    Returns:
        A list of the credential keys present in the file.  They are returned
        as dictionaries that can be passed into
        get_credential_storage_custom_key to get the actual credentials.
    """
    multistore = _get_multistore(filename, warn_on_readonly=warn_on_readonly)
    multistore._lock()
    try:
        return multistore._get_all_credential_keys()
    finally:
        multistore._unlock()


@util.positional(1)
def _get_multistore(filename, warn_on_readonly=True):
    """A helper method to initialize the multistore with proper locking.

    Args:
        filename: The JSON file storing a set of credentials
        warn_on_readonly: if True, log a warning if the store is readonly

    Returns:
        A multistore object
    """
    filename = os.path.expanduser(filename)
    _multistores_lock.acquire()
    try:
        multistore = _multistores.setdefault(
            filename, _MultiStore(filename, warn_on_readonly=warn_on_readonly))
    finally:
        _multistores_lock.release()
    return multistore


class _MultiStore(object):
    """A file backed store for multiple credentials."""

    @util.positional(2)
    def __init__(self, filename, warn_on_readonly=True):
        """Initialize the class.

        This will create the file if necessary.
        """
        self._file = LockedFile(filename, 'r+', 'r')
        self._thread_lock = threading.Lock()
        self._read_only = False
        self._warn_on_readonly = warn_on_readonly

        self._create_file_if_needed()

        # Cache of deserialized store. This is only valid after the
        # _MultiStore is locked or _refresh_data_cache is called. This is
        # of the form of:
        #
        # ((key, value), (key, value)...) -> OAuth2Credential
        #
        # If this is None, then the store hasn't been read yet.
        self._data = None

    class _Storage(BaseStorage):
        """A Storage object that can read/write a single credential."""

        def __init__(self, multistore, key):
            self._multistore = multistore
            self._key = key

        def acquire_lock(self):
            """Acquires any lock necessary to access this Storage.

            This lock is not reentrant.
            """
            self._multistore._lock()

        def release_lock(self):
            """Release the Storage lock.

            Trying to release a lock that isn't held will result in a
            RuntimeError.
            """
            self._multistore._unlock()

        def locked_get(self):
            """Retrieve credential.

            The Storage lock must be held when this is called.

            Returns:
                oauth2client.client.Credentials
            """
            credential = self._multistore._get_credential(self._key)
            if credential:
                credential.set_store(self)
            return credential

        def locked_put(self, credentials):
            """Write a credential.

            The Storage lock must be held when this is called.

            Args:
                credentials: Credentials, the credentials to store.
            """
            self._multistore._update_credential(self._key, credentials)

        def locked_delete(self):
            """Delete a credential.

            The Storage lock must be held when this is called.

            Args:
                credentials: Credentials, the credentials to store.
            """
            self._multistore._delete_credential(self._key)

    def _create_file_if_needed(self):
        """Create an empty file if necessary.

        This method will not initialize the file. Instead it implements a
        simple version of "touch" to ensure the file has been created.
        """
        if not os.path.exists(self._file.filename()):
            old_umask = os.umask(0o177)
            try:
                open(self._file.filename(), 'a+b').close()
            finally:
                os.umask(old_umask)

    def _lock(self):
        """Lock the entire multistore."""
        self._thread_lock.acquire()
        try:
            self._file.open_and_lock()
        except IOError as e:
            if e.errno == errno.ENOSYS:
                logger.warn('File system does not support locking the '
                            'credentials file.')
            elif e.errno == errno.ENOLCK:
                logger.warn('File system is out of resources for writing the '
                            'credentials file (is your disk full?).')
            elif e.errno == errno.EDEADLK:
                logger.warn('Lock contention on multistore file, opening '
                            'in read-only mode.')
            elif e.errno == errno.EACCES:
                logger.warn('Cannot access credentials file.')
            else:
                raise
        if not self._file.is_locked():
            self._read_only = True
            if self._warn_on_readonly:
                logger.warn('The credentials file (%s) is not writable. '
                            'Opening in read-only mode. Any refreshed '
                            'credentials will only be '
                            'valid for this run.', self._file.filename())
        if os.path.getsize(self._file.filename()) == 0:
            logger.debug('Initializing empty multistore file')
            # The multistore is empty so write out an empty file.
            self._data = {}
            self._write()
        elif not self._read_only or self._data is None:
            # Only refresh the data if we are read/write or we haven't
            # cached the data yet. If we are readonly, we assume is isn't
            # changing out from under us and that we only have to read it
            # once. This prevents us from whacking any new access keys that
            # we have cached in memory but were unable to write out.
            self._refresh_data_cache()

    def _unlock(self):
        """Release the lock on the multistore."""
        self._file.unlock_and_close()
        self._thread_lock.release()

    def _locked_json_read(self):
        """Get the raw content of the multistore file.

        The multistore must be locked when this is called.

        Returns:
            The contents of the multistore decoded as JSON.
        """
        assert self._thread_lock.locked()
        self._file.file_handle().seek(0)
        return json.load(self._file.file_handle())

    def _locked_json_write(self, data):
        """Write a JSON serializable data structure to the multistore.

        The multistore must be locked when this is called.

        Args:
            data: The data to be serialized and written.
        """
        assert self._thread_lock.locked()
        if self._read_only:
            return
        self._file.file_handle().seek(0)
        json.dump(data, self._file.file_handle(),
                  sort_keys=True, indent=2, separators=(',', ': '))
        self._file.file_handle().truncate()

    def _refresh_data_cache(self):
        """Refresh the contents of the multistore.

        The multistore must be locked when this is called.

        Raises:
            NewerCredentialStoreError: Raised when a newer client has written
            the store.
        """
        self._data = {}
        try:
            raw_data = self._locked_json_read()
        except Exception:
            logger.warn('Credential data store could not be loaded. '
                        'Will ignore and overwrite.')
            return

        version = 0
        try:
            version = raw_data['file_version']
        except Exception:
            logger.warn('Missing version for credential data store. It may be '
                        'corrupt or an old version. Overwriting.')
        if version > 1:
            raise NewerCredentialStoreError(
                'Credential file has file_version of %d. '
                'Only file_version of 1 is supported.' % version)

        credentials = []
        try:
            credentials = raw_data['data']
        except (TypeError, KeyError):
            pass

        for cred_entry in credentials:
            try:
                key, credential = self._decode_credential_from_json(cred_entry)
                self._data[key] = credential
            except:
                # If something goes wrong loading a credential, just ignore it
                logger.info('Error decoding credential, skipping',
                            exc_info=True)

    def _decode_credential_from_json(self, cred_entry):
        """Load a credential from our JSON serialization.

        Args:
            cred_entry: A dict entry from the data member of our format

        Returns:
            (key, cred) where the key is the key tuple and the cred is the
            OAuth2Credential object.
        """
        raw_key = cred_entry['key']
        key = _dict_to_tuple_key(raw_key)
        credential = None
        credential = Credentials.new_from_json(
            json.dumps(cred_entry['credential']))
        return (key, credential)

    def _write(self):
        """Write the cached data back out.

        The multistore must be locked.
        """
        raw_data = {'file_version': 1}
        raw_creds = []
        raw_data['data'] = raw_creds
        for (cred_key, cred) in self._data.items():
            raw_key = dict(cred_key)
            raw_cred = json.loads(cred.to_json())
            raw_creds.append({'key': raw_key, 'credential': raw_cred})
        self._locked_json_write(raw_data)

    def _get_all_credential_keys(self):
        """Gets all the registered credential keys in the multistore.

        Returns:
            A list of dictionaries corresponding to all the keys currently
            registered
        """
        return [dict(key) for key in self._data.keys()]

    def _get_credential(self, key):
        """Get a credential from the multistore.

        The multistore must be locked.

        Args:
            key: The key used to retrieve the credential

        Returns:
            The credential specified or None if not present
        """
        return self._data.get(key, None)

    def _update_credential(self, key, cred):
        """Update a credential and write the multistore.

        This must be called when the multistore is locked.

        Args:
            key: The key used to retrieve the credential
            cred: The OAuth2Credential to update/set
        """
        self._data[key] = cred
        self._write()

    def _delete_credential(self, key):
        """Delete a credential and write the multistore.

        This must be called when the multistore is locked.

        Args:
            key: The key used to retrieve the credential
        """
        try:
            del self._data[key]
        except KeyError:
            pass
        self._write()

    def _get_storage(self, key):
        """Get a Storage object to get/set a credential.

        This Storage is a 'view' into the multistore.

        Args:
            key: The key used to retrieve the credential

        Returns:
            A Storage object that can be used to get/set this cred
        """
        return self._Storage(self, key)
