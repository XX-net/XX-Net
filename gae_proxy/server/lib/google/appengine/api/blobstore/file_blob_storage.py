#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#




"""Implementation of Blobstore stub storage based on file system.

Contains implementation of blobstore_stub.BlobStorage that writes
blobs directly to a filesystem.
"""











import errno
import os

from google.appengine.api import blobstore
from google.appengine.api.blobstore import blobstore_stub


__all__ = ['FileBlobStorage']



import __builtin__
_local_open = __builtin__.open


class FileBlobStorage(blobstore_stub.BlobStorage):
  """Storage mechanism for storing blob data on local disk."""

  def __init__(self, storage_directory, app_id):
    """Constructor.

    Args:
      storage_directory: Directory within which to store blobs.
      app_id: App id to store blobs on behalf of.
    """
    self._storage_directory = storage_directory
    self._app_id = app_id

  @classmethod
  def _BlobKey(cls, blob_key):
    """Normalize to instance of BlobKey."""
    if not isinstance(blob_key, blobstore.BlobKey):
      return blobstore.BlobKey(unicode(blob_key))
    return blob_key

  def _DirectoryForBlob(self, blob_key):
    """Determine which directory where a blob is stored.

    Each blob gets written to a directory underneath the storage objects
    storage directory based on the blobs kind, app-id and first character of
    its name.  So blobs with blob-keys:

      _ACFDEDG
      _MNOPQRS
      _RSTUVWX

    Are stored in:

      <storage-dir>/blob/myapp/A
      <storage-dir>/blob/myapp/M
      <storage-dir>/R

    Args:
      blob_key: Blob key to determine directory for.

    Returns:
      Directory relative to this objects storage directory to
      where blob is stored or should be stored.
    """
    blob_key = self._BlobKey(blob_key)
    return os.path.join(self._storage_directory,
                        self._app_id,
                        str(blob_key)[1])

  def _FileForBlob(self, blob_key):
    """Calculate full filename to store blob contents in.

    This method does not check to see if the file actually exists.

    Args:
      blob_key: Blob key of blob to calculate file for.

    Returns:
      Complete path for file used for storing blob.
    """
    blob_key = self._BlobKey(blob_key)
    return os.path.join(self._DirectoryForBlob(blob_key), str(blob_key)[1:])

  def StoreBlob(self, blob_key, blob_stream):
    """Store blob stream to disk.

    Args:
      blob_key: Blob key of blob to store.
      blob_stream: Stream or stream-like object that will generate blob content.
    """
    blob_key = self._BlobKey(blob_key)
    blob_directory = self._DirectoryForBlob(blob_key)
    if not os.path.exists(blob_directory):
      os.makedirs(blob_directory)
    blob_file = self._FileForBlob(blob_key)
    output = _local_open(blob_file, 'wb')

    try:


      while True:
        block = blob_stream.read(1 << 20)
        if not block:
          break
        output.write(block)
    finally:
      output.close()

  def OpenBlob(self, blob_key):
    """Open blob file for streaming.

    Args:
      blob_key: Blob-key of existing blob to open for reading.

    Returns:
      Open file stream for reading blob from disk.
    """
    return _local_open(self._FileForBlob(blob_key), 'rb')

  def DeleteBlob(self, blob_key):
    """Delete blob data from disk.

    Deleting an unknown blob will not raise an error.

    Args:
      blob_key: Blob-key of existing blob to delete.
    """
    try:
      os.remove(self._FileForBlob(blob_key))
    except OSError, e:
      if e.errno != errno.ENOENT:
        raise e
