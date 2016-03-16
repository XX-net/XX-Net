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
"""Rewrites blob download headers in the response with full blob contents."""



import logging

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore
from google.appengine.api import datastore_errors
from google.appengine.api.blobstore import blobstore_stub
from google.appengine.ext import blobstore


# The MIME type from apps to tell Blobstore to select the mime type.
_AUTO_MIME_TYPE = 'application/vnd.google.appengine.auto'


def _get_blob_storage():
  """Gets the BlobStorage instance from the API proxy stub map.

  Returns:
    The BlobStorage instance as registered with blobstore API in stub map.
  """
  return apiproxy_stub_map.apiproxy.GetStub('blobstore').storage


def _parse_range_header(range_header):
  """Parse HTTP Range header.

  Args:
    range_header: A str representing the value of a range header as retrived
      from Range or X-AppEngine-BlobRange.

  Returns:
    Tuple (start, end):
      start: Start index of blob to retrieve.  May be negative index.
      end: None or end index.  End index is exclusive.
    (None, None) if there is a parse error.
  """
  if not range_header:
    return None, None
  try:
    # ValueError if <1 split.
    range_type, ranges = range_header.split('=', 1)
    if range_type != 'bytes':
      return None, None
    ranges = ranges.lstrip()
    if ',' in ranges:
      return None, None
    end = None
    if ranges.startswith('-'):
      start = int(ranges)
      if start == 0:
        return None, None
    else:
      split_range = ranges.split('-', 1)
      start = int(split_range[0])
      if len(split_range) == 2 and split_range[1].strip():
        end = int(split_range[1]) + 1
        if start > end:
          return None, None
    return start, end
  except ValueError:
    return None, None


def _get_blob_metadata(blob_key):
  """Retrieve the metadata about a blob from the blob_key.

  Args:
    blob_key: The BlobKey of the blob.

  Returns:
    Tuple (size, content_type, open_key):
      size: The size of the blob.
      content_type: The content type of the blob.
      open_key: The key used as an argument to BlobStorage to open the blob
        for reading. Same as blob_key
    (None, None, None) if the blob metadata was not found.
  """
  key = blobstore_stub.BlobstoreServiceStub.ToDatastoreBlobKey(blob_key)
  try:
    info = datastore.Get(key)
    return info['size'], info['content_type'], blob_key
  except datastore_errors.EntityNotFoundError:
    return None, None, None


def blobstore_download_rewriter(state):
  """Rewrite a response with blobstore download bodies.

  Checks for the X-AppEngine-BlobKey header in the response.  If found, it will
  discard the body of the request and replace it with the blob content
  indicated.

  If a valid blob is not found, it will send a 404 to the client.

  If the application itself provides a content-type header, it will override
  the content-type stored in the action blob.

  If blobstore.BLOB_RANGE_HEADER header is provided, blob will be partially
  served.  If Range is present, and not blobstore.BLOB_RANGE_HEADER, will use
  Range instead.

  Args:
    state: A request_rewriter.RewriterState to modify.
  """
  blob_key = state.headers.get(blobstore.BLOB_KEY_HEADER)
  if not blob_key:
    # Pass the download through unchanged.
    return

  def set_range_request_not_satisfiable(blob_size):
    """Short circuit response and return 416 error.

    Changes state into the error response.

    Args:
      blob_size: The size of the blob.
    """
    state.status = '416 Requested Range Not Satisfiable'
    state.headers['Content-Length'] = '0'
    state.headers['Content-Range'] = '*/%d' % blob_size
    del state.headers['Content-Type']

  # Rewrite the response to include the blob contents.
  state.body = []
  del state.headers[blobstore.BLOB_KEY_HEADER]

  blob_size, blob_content_type, blob_open_key = _get_blob_metadata(blob_key)
  if isinstance(blob_content_type, unicode):
    blob_content_type = blob_content_type.encode('ascii')

  range_header = state.headers.get(blobstore.BLOB_RANGE_HEADER)
  if range_header is not None:
    del state.headers[blobstore.BLOB_RANGE_HEADER]
  else:
    range_header = state.environ.get('HTTP_RANGE')

  status_code = state.status_code

  # If we found a blob, serve it.
  # It is an error if the response code returned by the user is not 200.
  if (blob_size is not None and blob_content_type is not None and
      status_code == 200):
    content_length = blob_size
    start = 0
    end = content_length

    if range_header:
      start, end = _parse_range_header(range_header)
      if start is None:
        set_range_request_not_satisfiable(blob_size)
        return
      else:
        if start < 0:
          start = max(blob_size + start, 0)  # Start is negative.
        elif start >= blob_size:
          set_range_request_not_satisfiable(blob_size)
          return
        if end is not None:
          end = min(end, blob_size)
        else:
          end = blob_size
        content_length = min(end, blob_size) - start
        end = start + content_length
        state.status = '206 Partial Content'
        state.headers['Content-Range'] = 'bytes %d-%d/%d' % (start, end - 1,
                                                             blob_size)

    blob_stream = _get_blob_storage().OpenBlob(blob_open_key)
    blob_stream.seek(start)
    state.body = [blob_stream.read(content_length)]
    state.headers['Content-Length'] = str(content_length)

    content_type = state.headers.get('Content-Type')
    if not content_type or content_type == _AUTO_MIME_TYPE:
      state.headers['Content-Type'] = blob_content_type
    # Allow responses beyond the maximum dynamic response size
    state.allow_large_response = True

  else:
    # Missing blobs should have been handled by application.
    if status_code != 200:
      logging.error('Blob-serving response with status %d, expected 200.',
                    status_code)
    else:
      logging.error('Could not find blob with key %s.', blob_key)

    state.status = '500 Internal Server Error'

    state.headers['Content-Length'] = '0'
    del state.headers['Content-Type']
