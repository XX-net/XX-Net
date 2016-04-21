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




"""Blobstore support classes.

Classes:

  DownloadRewriter:
    Rewriter responsible for transforming an application response to one
    that serves a blob to the user.

  CreateUploadDispatcher:
    Creates a dispatcher that is added to dispatcher chain.  Handles uploads
    by storing blobs rewriting requests and returning a redirect.
"""



import cgi
import cStringIO
import logging
import mimetools
import re
import sys

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import blobstore
from google.appengine.api import datastore
from google.appengine.api import datastore_errors
from google.appengine.tools import dev_appserver_upload

from webob import byterange



UPLOAD_URL_PATH = '_ah/upload/'


UPLOAD_URL_PATTERN = '/%s(.*)' % UPLOAD_URL_PATH


AUTO_MIME_TYPE = 'application/vnd.google.appengine.auto'


ERROR_RESPONSE_TEMPLATE = """
<html>
  <head>
    <title>%(response_code)d %(response_string)s</title>
  </head>
  <body text=#000000 bgcolor=#ffffff>
    <h1>Error: %(response_string)s</h1>
    <h2>%(response_text)s</h2>
  </body>
</html>
"""


def GetBlobStorage():
  """Get blob-storage from api-proxy stub map.

  Returns:
    BlobStorage instance as registered with blobstore API in stub map.
  """
  return apiproxy_stub_map.apiproxy.GetStub('blobstore').storage



















_BYTESRANGE_IS_EXCLUSIVE = not hasattr(byterange.Range, 'serialize_bytes')

if _BYTESRANGE_IS_EXCLUSIVE:

  ParseRange = byterange.Range.parse_bytes

  MakeContentRange = byterange.ContentRange

  def GetContentRangeStop(content_range):
    return content_range.stop







  _orig_is_content_range_valid = byterange._is_content_range_valid

  def _new_is_content_range_valid(start, stop, length, response=False):
    return _orig_is_content_range_valid(start, stop, length, False)

  def ParseContentRange(content_range_header):



    try:
      byterange._is_content_range_valid = _new_is_content_range_valid
      return byterange.ContentRange.parse(content_range_header)
    finally:
      byterange._is_content_range_valid = _orig_is_content_range_valid

else:

  def ParseRange(range_header):


    original_stdout = sys.stdout
    sys.stdout = cStringIO.StringIO()
    try:
      parse_result = byterange.Range.parse_bytes(range_header)
    finally:
      sys.stdout = original_stdout
    if parse_result is None:
      return None
    else:
      ranges = []
      for start, end in parse_result[1]:
        if end is not None:
          end += 1
        ranges.append((start, end))
      return parse_result[0], ranges

  class _FixedContentRange(byterange.ContentRange):







    def __init__(self, start, stop, length):

      self.start = start
      self.stop = stop
      self.length = length









  def MakeContentRange(start, stop, length):
    if stop is not None:
      stop -= 2
    content_range = _FixedContentRange(start, stop, length)
    return content_range

  def GetContentRangeStop(content_range):
    stop = content_range.stop
    if stop is not None:
      stop += 2
    return stop

  def ParseContentRange(content_range_header):
    return _FixedContentRange.parse(content_range_header)


def ParseRangeHeader(range_header):
  """Parse HTTP Range header.

  Args:
    range_header: Range header as retrived from Range or X-AppEngine-BlobRange.

  Returns:
    Tuple (start, end):
      start: Start index of blob to retrieve.  May be negative index.
      end: None or end index.  End index is exclusive.
    (None, None) if there is a parse error.
  """
  if not range_header:
    return None, None
  parsed_range = ParseRange(range_header)
  if parsed_range:
    range_tuple = parsed_range[1]
    if len(range_tuple) == 1:
      return range_tuple[0]
  return None, None


def DownloadRewriter(response, request_headers):
  """Intercepts blob download key and rewrites response with large download.

  Checks for the X-AppEngine-BlobKey header in the response.  If found, it will
  discard the body of the request and replace it with the blob content
  indicated.

  If a valid blob is not found, it will send a 404 to the client.

  If the application itself provides a content-type header, it will override
  the content-type stored in the action blob.

  If Content-Range header is provided, blob will be partially served.  The
  application can set blobstore.BLOB_RANGE_HEADER if the size of the blob is
  not known.  If Range is present, and not blobstore.BLOB_RANGE_HEADER, will
  use Range instead.

  Args:
    response: Response object to be rewritten.
    request_headers: Original request headers.  Looks for 'Range' header to copy
      to response.
  """
  blob_key = response.headers.getheader(blobstore.BLOB_KEY_HEADER)
  if blob_key:
    del response.headers[blobstore.BLOB_KEY_HEADER]


    try:
      blob_info = datastore.Get(
          datastore.Key.from_path(blobstore.BLOB_INFO_KIND,
                                  blob_key,
                                  namespace=''))

      content_range_header = response.headers.getheader('Content-Range')
      blob_size = blob_info['size']
      range_header = response.headers.getheader(blobstore.BLOB_RANGE_HEADER)
      if range_header is not None:
        del response.headers[blobstore.BLOB_RANGE_HEADER]
      else:
        range_header = request_headers.getheader('Range')

      def not_satisfiable():
        """Short circuit response and return 416 error."""
        response.status_code = 416
        response.status_message = 'Requested Range Not Satisfiable'
        response.body = cStringIO.StringIO('')
        response.headers['Content-Length'] = '0'
        del response.headers['Content-Type']
        del response.headers['Content-Range']

      if range_header:
        start, end = ParseRangeHeader(range_header)
        if start is not None:
          if end is None:
            if start >= 0:
              content_range_start = start
            else:
              content_range_start = blob_size + start
            content_range = MakeContentRange(
                content_range_start, blob_size, blob_size)
            content_range_header = str(content_range)
          else:
            content_range = MakeContentRange(start, min(end, blob_size),
                                             blob_size)
            content_range_header = str(content_range)
          response.headers['Content-Range'] = content_range_header
        else:
          not_satisfiable()
          return

      content_range_header = response.headers.getheader('Content-Range')
      content_length = blob_size
      start = 0
      end = content_length
      if content_range_header is not None:
        content_range = ParseContentRange(content_range_header)
        if content_range:
          start = content_range.start
          stop = GetContentRangeStop(content_range)
          content_length = min(stop, blob_size) - start
          stop = start + content_length
          content_range = MakeContentRange(start, stop, blob_size)
          response.headers['Content-Range'] = str(content_range)
        else:
          not_satisfiable()
          return

      blob_stream = GetBlobStorage().OpenBlob(blob_key)
      blob_stream.seek(start)
      response.body = cStringIO.StringIO(blob_stream.read(content_length))
      response.headers['Content-Length'] = str(content_length)

      content_type = response.headers.getheader('Content-Type')
      if not content_type or content_type == AUTO_MIME_TYPE:
        response.headers['Content-Type'] = blob_info['content_type']
      response.large_response = True



    except datastore_errors.EntityNotFoundError:

      response.status_code = 500
      response.status_message = 'Internal Error'
      response.body = cStringIO.StringIO()

      if response.headers.getheader('status'):
        del response.headers['status']
      if response.headers.getheader('location'):
        del response.headers['location']
      if response.headers.getheader('content-type'):
        del response.headers['content-type']

      logging.error('Could not find blob with key %s.', blob_key)


def CreateUploadDispatcher(get_blob_storage=GetBlobStorage):
  """Function to create upload dispatcher.

  Returns:
    New dispatcher capable of handling large blob uploads.
  """


  from google.appengine.tools import dev_appserver

  class UploadDispatcher(dev_appserver.URLDispatcher):
    """Dispatcher that handles uploads."""

    def __init__(self):
      """Constructor.

      Args:
        blob_storage: A BlobStorage instance.
      """
      self.__cgi_handler = dev_appserver_upload.UploadCGIHandler(
          get_blob_storage())



    def Dispatch(self,
                 request,
                 outfile,
                 base_env_dict=None):
      """Handle post dispatch.

      This dispatcher will handle all uploaded files in the POST request, store
      the results in the blob-storage, close the upload session and transform
      the original request in to one where the uploaded files have external
      bodies.

      Returns:
        New AppServerRequest indicating request forward to upload success
        handler.
      """

      if base_env_dict['REQUEST_METHOD'] != 'POST':
        outfile.write('Status: 400\n\n')
        return


      upload_key = re.match(UPLOAD_URL_PATTERN, request.relative_url).group(1)
      try:
        upload_session = datastore.Get(upload_key)
      except datastore_errors.EntityNotFoundError:
        upload_session = None

      if upload_session:
        success_path = upload_session['success_path']
        max_bytes_per_blob = upload_session['max_bytes_per_blob']
        max_bytes_total = upload_session['max_bytes_total']

        upload_form = cgi.FieldStorage(fp=request.infile,
                                       headers=request.headers,
                                       environ=base_env_dict)

        try:


          mime_message_string = self.__cgi_handler.GenerateMIMEMessageString(
              upload_form,
              max_bytes_per_blob=max_bytes_per_blob,
              max_bytes_total=max_bytes_total)

          datastore.Delete(upload_session)
          self.current_session = upload_session


          header_end = mime_message_string.find('\n\n') + 1
          content_start = header_end + 1
          header_text = mime_message_string[:header_end].replace('\n', '\r\n')
          content_text = mime_message_string[content_start:].replace('\n',
                                                                     '\r\n')


          complete_headers = ('%s'
                              'Content-Length: %d\r\n'
                              '\r\n') % (header_text, len(content_text))

          return dev_appserver.AppServerRequest(
              success_path,
              None,
              mimetools.Message(cStringIO.StringIO(complete_headers)),
              cStringIO.StringIO(content_text),
              force_admin=True)
        except dev_appserver_upload.InvalidMIMETypeFormatError:
          outfile.write('Status: 400\n\n')
        except dev_appserver_upload.UploadEntityTooLargeError:
          outfile.write('Status: 413\n\n')
          response = ERROR_RESPONSE_TEMPLATE % {
              'response_code': 413,
              'response_string': 'Request Entity Too Large',
              'response_text': 'Your client issued a request that was too '
              'large.'}
          outfile.write(response)
      else:
        logging.error('Could not find session for %s', upload_key)
        outfile.write('Status: 404\n\n')


    def EndRedirect(self, dispatched_output, original_output):
      """Handle the end of upload complete notification.

      Makes sure the application upload handler returned an appropriate status
      code.
      """
      response = dev_appserver.RewriteResponse(dispatched_output)
      logging.info('Upload handler returned %d', response.status_code)
      outfile = cStringIO.StringIO()
      outfile.write('Status: %s\n' % response.status_code)

      if response.body and len(response.body.read()) > 0:
        response.body.seek(0)
        outfile.write(response.body.read())
      else:
        outfile.write(''.join(response.headers.headers))

      outfile.seek(0)
      dev_appserver.URLDispatcher.EndRedirect(self,
                                              outfile,
                                              original_output)

  return UploadDispatcher()
