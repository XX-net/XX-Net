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
"""A handler that displays information about blobstore blobs."""

from google.appengine.ext import blobstore

from google.appengine.tools.devappserver2.admin import admin_request_handler


def _get_blobs(start, limit):
  """Return a list of BlobInfo objects ordered by most recently created.

  Args:
    start: The offset of the first blobstore.BlobInfo instances to return,
        ordered by descending creation time.
    limit: The maximum number of blobstore.BlobInfo blobstore to return.

  Returns:
    A list of blobstore.BlobInfo blobstore ordered by most recently created.
  """
  q = blobstore.BlobInfo.all().order('-creation')
  return q.fetch(limit, offset=start)


class BlobstoreRequestHandler(admin_request_handler.AdminRequestHandler):
  """A handler that displays information about blobstore blobs."""

  BLOBS_PER_PAGE = 20

  def get(self):
    offset = int(self.request.get('offset', 0))
    # Fetch an extra item to check if the next button should be enabled.
    blob_infos = _get_blobs(offset, self.BLOBS_PER_PAGE+1)

    if len(blob_infos) == self.BLOBS_PER_PAGE + 1:
      next_offset = offset + self.BLOBS_PER_PAGE
    else:
      next_offset = None
    previous = max(0, offset - self.BLOBS_PER_PAGE) if offset > 0 else None

    self.response.write(self.render('blobstore_viewer.html', {
        'blob_infos': blob_infos[:self.BLOBS_PER_PAGE],
        'offset': offset,
        'next': next_offset,
        'previous': previous,
        'return_to': self.request.uri}))

  def post(self):
    """Deletes blobs identified in 'blob_key' form variables.

    Multiple keys can be specified e.g. '...&blob_key=key1&blob_key=key2'.

    Redirects the client back to the value specified in the 'return_to' form
    variable.
    """
    redirect_url = str(self.request.get('return_to', '/blobstore'))
    keys = self.request.get_all('blob_key')
    blobstore.delete(keys)
    self.redirect(redirect_url)


class BlobRequestHandler(admin_request_handler.AdminRequestHandler):
  """A handler that displays information about a single blobstore blobs."""

  # Content types that can be displayed with 'content-disposition: inline'.
  # Some browsers can inline other contents, e.g. application/pdf,
  # but not all so, those types are not in the list.
  INLINEABLE_TYPES = ('image/', 'text/plain')

  def get(self, key):
    blob_info = blobstore.BlobInfo.get(key)
    if blob_info is None:
      # TODO: Display a message saying that this blob no longer
      # exists.
      self.redirect('/blobstore')
      return
    display = self.request.get('display')
    if display:
      self._display_blob(blob_info, display)
    else:
      self._display_blob_info(blob_info,
                              self.request.get('return_to', '/blobstore'))

  def _display_blob_info(self, blob_info, return_url):
    inlineable = False
    for t in self.INLINEABLE_TYPES:
      if blob_info.content_type.startswith(t):
        inlineable = True
        break
    self.response.write(self.render('blob_viewer.html', {
        'blob_info': blob_info,
        'delete_uri': '/blobstore',
        'download_uri': '%s?display=attachment' % self.request.path,
        'inline_uri': '%s?display=inline' % self.request.path,
        'inlineable': inlineable,
        'return_to': return_url}))

  def _display_blob(self, blob_info, content_disposition):
    content_type = str(blob_info.content_type)
    if (content_type == 'application/octet-stream' and
        content_disposition == 'inline'):
      # Try to display blob bytes as characters since some files (e.g. diffs)
      # may be uploaded as application/octet stream but still have plain text
      # content.
      content_type = 'text/plain'
    if content_disposition == 'attachment' and blob_info.filename:
      content_disposition += '; filename=%s' % blob_info.filename
    self.response.headers['Content-Type'] = content_type
    self.response.headers['Content-Disposition'] = str(content_disposition)
    reader = blob_info.open()
    self.response.write(reader.read())
    reader.close()
