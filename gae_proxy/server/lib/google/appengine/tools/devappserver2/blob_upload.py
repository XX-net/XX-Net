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
"""Handles blob store uploading and serving in the front-end.

Includes a WSGI application that handles upload requests and inserts the
contents into the blob store.
"""



import base64
import cgi
import cStringIO
import datetime
import email.generator
import email.message
from email.mime import multipart
import hashlib
import logging
import os
import random
import re
import sys
import time
import urlparse

import google
import webob.exc

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore
from google.appengine.api import datastore_errors
from google.appengine.api.blobstore import blobstore
from google.appengine.ext.cloudstorage import cloudstorage_stub
from google.appengine.tools.devappserver2 import constants

# Upload URL path.
UPLOAD_URL_PATH = '_ah/upload/'

# Upload URL pattern.
_UPLOAD_URL_PATTERN = re.compile(r'/%s(.*)' % UPLOAD_URL_PATH)

# Pattern for MIME types.
_MIME_PATTERN = re.compile(r'([^/; ]+)/([^/; ]+)$')

# These are environment variables that do not make any sense to transmit because
# the values contained in them would be obsolete after the request has been
# transformed from full upload objects to blob-info records.
_STRIPPED_ENVIRON = frozenset(('HTTP_CONTENT_LENGTH',
                               'HTTP_CONTENT_MD5',
                               'HTTP_CONTENT_TYPE',
                              ))

# These are the MIME headers that need to be removed from the external-body
# message, because we are going to set our own.
# cgi.FieldStorage makes these all lowercase.
_STRIPPED_FILE_HEADERS = frozenset(('content-type',
                                    'content-md5',
                                    'content-length',
                                   ))

# The maximum length of the content-type and filename fields as dictated by
# the maximum length of a string in the datastore
_MAX_STRING_NAME_LENGTH = 500


class Error(Exception):
  """Base class for upload processing errors."""


class _InvalidMIMETypeFormatError(Error):
  """MIME type was formatted incorrectly."""


class _TooManyConflictsError(Error):
  """There were too many conflicts generating a blob key."""


class _InvalidMetadataError(Error):
  """The filename or content type of the entity was not a valid UTF-8 string."""


def _get_blob_storage():
  """Gets the BlobStorage instance from the API proxy stub map.

  Returns:
    The BlobStorage instance as registered with blobstore API in stub map.
  """
  return apiproxy_stub_map.apiproxy.GetStub('blobstore').storage


def _generate_blob_key(time_func=time.time, random_func=random.random):
  """Generate a unique blob key.

  The key is generated using the current time stamp combined with a random
  number. The two values are hashed with MD5 and then base-64 encoded
  (url-safe). The new key is checked to see if it already exists within the
  datastore and the random number is regenerated until there is no match.

  Args:
    time_func: Function that generates a timestamp, as a floating-point number
      representing seconds since the epoch in UTC. Used for dependency injection
      (allows for predictable results during tests).
    random_func: Function used for generating the random number. Used for
      dependency injection (allows for predictable results during tests).

  Returns:
    String version of the blob key that is unique within the __BlobInfo__
    datastore.

  Raises:
    _TooManyConflictsError: There are too many name conflicts.
  """
  timestamp = str(time_func())
  tries = 0
  while tries < 10:
    number = str(random_func())
    digester = hashlib.md5()
    digester.update(timestamp)
    digester.update(number)
    blob_key = base64.urlsafe_b64encode(digester.digest())
    datastore_key = datastore.Key.from_path(blobstore.BLOB_INFO_KIND, blob_key,
                                            namespace='')
    try:
      datastore.Get(datastore_key)
      tries += 1
    except datastore_errors.EntityNotFoundError:
      return blob_key
  raise _TooManyConflictsError()


def _split_mime_type(mime_type):
  """Split MIME type into main type and subtype.

  Args:
    mime_type: The full MIME type string.

  Returns:
    (main, sub):
      main: Main part of MIME type (e.g., application, image, text, etc).
      sub: Subtype part of MIME type (e.g., pdf, png, html, etc).

  Raises:
    _InvalidMIMETypeFormatError: mime_type is incorrectly formatted.
  """
  if mime_type:
    match = _MIME_PATTERN.match(mime_type)
    if not match:
      raise _InvalidMIMETypeFormatError(
          'Incorrectly formatted MIME type: %s' % mime_type)
    return match.groups()
  else:
    return 'application', 'octet-stream'


class Application(object):
  """A WSGI middleware application for handling blobstore upload requests.

  This application will handle all uploaded files in a POST request, store the
  results in the blob-storage, close the upload session and forward the request
  on to another WSGI application, with the environment transformed so that the
  uploaded file contents are replaced with their blob keys.
  """

  def __init__(self, forward_app, get_blob_storage=_get_blob_storage,
               generate_blob_key=_generate_blob_key,
               now_func=datetime.datetime.now):
    """Constructs a new Application.

    Args:
      forward_app: A WSGI application to forward successful upload requests to.
      get_blob_storage: Callable that returns a BlobStorage instance. The
        default is fine, but may be overridden for testing purposes.
      generate_blob_key: Function used for generating unique blob keys.
      now_func: Function that returns the current timestamp.
    """
    self._forward_app = forward_app
    self._blob_storage = get_blob_storage()
    self._generate_blob_key = generate_blob_key
    self._now_func = now_func

  def abort(self, code, detail=None):
    """Aborts the application by raising a webob.exc.HTTPException.

    Args:
      code: HTTP status code int.
      detail: Optional detail message str.

    Raises:
      webob.exc.HTTPException: Always.
    """
    exception = webob.exc.status_map[code]()
    if detail:
      exception.detail = detail
    raise exception

  def store_blob(self, content_type, filename, md5_hash, blob_file, creation):
    """Store a supplied form-data item to the blobstore.

    The appropriate metadata is stored into the datastore.

    Args:
      content_type: The MIME content type of the uploaded file.
      filename: The filename of the uploaded file.
      md5_hash: MD5 hash of the file contents, as a hashlib hash object.
      blob_file: A file-like object containing the contents of the file.
      creation: datetime.datetime instance to associate with new blobs creation
        time. This parameter is provided so that all blobs in the same upload
        form can have the same creation date.

    Returns:
      datastore.Entity('__BlobInfo__') associated with the upload.

    Raises:
      _TooManyConflictsError if there were too many name conflicts generating a
        blob key.
    """
    blob_key = self._generate_blob_key()

    # Store the blob contents in the blobstore.
    self._blob_storage.StoreBlob(blob_key, blob_file)

    # Store the blob metadata in the datastore as a __BlobInfo__ entity.
    blob_entity = datastore.Entity('__BlobInfo__', name=str(blob_key),
                                   namespace='')
    blob_entity['content_type'] = content_type
    blob_entity['creation'] = creation
    blob_entity['filename'] = filename
    blob_entity['md5_hash'] = md5_hash.hexdigest()
    blob_entity['size'] = blob_file.tell()

    datastore.Put(blob_entity)
    return blob_entity

  def store_gs_file(self, content_type, gs_filename, blob_file, filename):
    """Store a supplied form-data item to GS.

    Delegate all the work of gs file creation to CloudStorageStub.

    Args:
      content_type: The MIME content type of the uploaded file.
      gs_filename: The gs filename to create of format bucket/filename.
      blob_file: A file-like object containing the contents of the file.
      filename: user provided filename.

    Returns:
      datastore.Entity('__GsFileInfo__') associated with the upload.
    """
    gs_stub = cloudstorage_stub.CloudStorageStub(self._blob_storage)
    blobkey = gs_stub.post_start_creation('/' + gs_filename,
                                          {'content-type': content_type})
    content = blob_file.read()
    return gs_stub.put_continue_creation(
        blobkey, content, (0, len(content) - 1), len(content), filename)

  def _preprocess_data(self, content_type, blob_file,
                       filename, base64_encoding):
    """Preprocess data and metadata before storing them.

    Args:
      content_type: The MIME content type of the uploaded file.
      blob_file: A file-like object containing the contents of the file.
      filename: The filename of the uploaded file.
      base64_encoding: True, if the file contents are base-64 encoded.

    Returns:
      (content_type, blob_file, filename) after proper preprocessing.

    Raises:
      _InvalidMetadataError: when metadata are not utf-8 encoded.
    """
    if base64_encoding:
      blob_file = cStringIO.StringIO(base64.urlsafe_b64decode(blob_file.read()))

    # If content_type or filename are bytes, assume UTF-8 encoding.
    try:
      if not isinstance(content_type, unicode):
        content_type = content_type.decode('utf-8')
      if filename and not isinstance(filename, unicode):
        filename = filename.decode('utf-8')
    except UnicodeDecodeError:
      raise _InvalidMetadataError(
          'The uploaded entity contained invalid UTF-8 metadata. This may be '
          'because the page containing the upload form was served with a '
          'charset other than "utf-8".')
    return content_type, blob_file, filename

  def store_and_build_forward_message(self, form, boundary=None,
                                      max_bytes_per_blob=None,
                                      max_bytes_total=None,
                                      bucket_name=None):
    """Reads form data, stores blobs data and builds the forward request.

    This finds all of the file uploads in a set of form fields, converting them
    into blobs and storing them in the blobstore. It also generates the HTTP
    request to forward to the user's application.

    Args:
      form: cgi.FieldStorage instance representing the whole form derived from
        original POST data.
      boundary: The optional boundary to use for the resulting form. If omitted,
        one is randomly generated.
      max_bytes_per_blob: The maximum size in bytes that any single blob
        in the form is allowed to be.
      max_bytes_total: The maximum size in bytes that the total of all blobs
        in the form is allowed to be.
      bucket_name: The name of the Google Storage bucket to store the uploaded
                   files.

    Returns:
      A tuple (content_type, content_text), where content_type is the value of
      the Content-Type header, and content_text is a string containing the body
      of the HTTP request to forward to the application.

    Raises:
      webob.exc.HTTPException: The upload failed.
    """
    message = multipart.MIMEMultipart('form-data', boundary)

    creation = self._now_func()
    total_bytes_uploaded = 0
    created_blobs = []
    mime_type_error = None
    too_many_conflicts = False
    upload_too_large = False
    filename_too_large = False
    content_type_too_large = False

    # Extract all of the individual form items out of the FieldStorage.
    form_items = []
    # Sorting of forms is done merely to make testing a little easier since
    # it means blob-keys are generated in a predictable order.
    for key in sorted(form):
      form_item = form[key]
      if isinstance(form_item, list):
        form_items.extend(form_item)
      else:
        form_items.append(form_item)

    for form_item in form_items:
      disposition_parameters = {'name': form_item.name}

      variable = email.message.Message()

      if form_item.filename is None:
        # Copy as is
        variable.add_header('Content-Type', 'text/plain')
        variable.set_payload(form_item.value)
      else:
        # If there is no filename associated with this field it means that the
        # file form field was not filled in.  This blob should not be created
        # and forwarded to success handler.
        if not form_item.filename:
          continue

        disposition_parameters['filename'] = form_item.filename

        try:
          main_type, sub_type = _split_mime_type(form_item.type)
        except _InvalidMIMETypeFormatError, ex:
          mime_type_error = str(ex)
          break

        # Seek to the end of file and use the pos as the length.
        form_item.file.seek(0, os.SEEK_END)
        content_length = form_item.file.tell()
        form_item.file.seek(0)

        total_bytes_uploaded += content_length

        if max_bytes_per_blob is not None:
          if content_length > max_bytes_per_blob:
            upload_too_large = True
            break
        if max_bytes_total is not None:
          if total_bytes_uploaded > max_bytes_total:
            upload_too_large = True
            break
        if form_item.filename is not None:
          if len(form_item.filename) > _MAX_STRING_NAME_LENGTH:
            filename_too_large = True
            break
        if form_item.type is not None:
          if len(form_item.type) > _MAX_STRING_NAME_LENGTH:
            content_type_too_large = True
            break

        # Compute the MD5 hash of the upload.
        digester = hashlib.md5()
        while True:
          block = form_item.file.read(1 << 20)
          if not block:
            break
          digester.update(block)
        form_item.file.seek(0)

        # Create the external body message containing meta-data about the blob.
        external = email.message.Message()
        external.add_header('Content-Type', '%s/%s' % (main_type, sub_type),
                            **form_item.type_options)
        # NOTE: This is in violation of RFC 2616 (Content-MD5 should be the
        # base-64 encoding of the binary hash, not the hex digest), but it is
        # consistent with production.
        content_md5 = base64.urlsafe_b64encode(digester.hexdigest())
        # Create header MIME message
        headers = dict(form_item.headers)
        for name in _STRIPPED_FILE_HEADERS:
          if name in headers:
            del headers[name]
        headers['Content-Length'] = str(content_length)
        headers[blobstore.UPLOAD_INFO_CREATION_HEADER] = (
            blobstore._format_creation(creation))
        headers['Content-MD5'] = content_md5
        gs_filename = None
        if bucket_name:
          random_key = str(self._generate_blob_key())
          gs_filename = '%s/fake-%s' % (bucket_name, random_key)
          headers[blobstore.CLOUD_STORAGE_OBJECT_HEADER] = (
              blobstore.GS_PREFIX + gs_filename)
        for key, value in headers.iteritems():
          external.add_header(key, value)
        # Add disposition parameters (a clone of the outer message's field).
        if not external.get('Content-Disposition'):
          external.add_header('Content-Disposition', 'form-data',
                              **disposition_parameters)

        base64_encoding = (form_item.headers.get('Content-Transfer-Encoding') ==
                           'base64')
        content_type, blob_file, filename = self._preprocess_data(
            external['content-type'],
            form_item.file,
            form_item.filename,
            base64_encoding)

        # Store the actual contents to storage.
        if gs_filename:
          info_entity = self.store_gs_file(
              content_type, gs_filename, blob_file, filename)
        else:
          try:
            info_entity = self.store_blob(content_type, filename,
                                          digester, blob_file, creation)
          except _TooManyConflictsError:
            too_many_conflicts = True
            break

        # Track created blobs in case we need to roll them back.
        created_blobs.append(info_entity)

        variable.add_header('Content-Type', 'message/external-body',
                            access_type=blobstore.BLOB_KEY_HEADER,
                            blob_key=info_entity.key().name())
        variable.set_payload([external])

      # Set common information.
      variable.add_header('Content-Disposition', 'form-data',
                          **disposition_parameters)
      message.attach(variable)

    if (mime_type_error or too_many_conflicts or upload_too_large or
        filename_too_large or content_type_too_large):
      for blob in created_blobs:
        datastore.Delete(blob)
      if mime_type_error:
        self.abort(400, detail=mime_type_error)
      elif too_many_conflicts:
        self.abort(500, detail='Could not generate a blob key.')
      elif upload_too_large:
        self.abort(413)
      else:
        if filename_too_large:
          invalid_field = 'filename'
        elif content_type_too_large:
          invalid_field = 'Content-Type'
        detail = 'The %s exceeds the maximum allowed length of %s.' % (
            invalid_field, _MAX_STRING_NAME_LENGTH)
        self.abort(400, detail=detail)

    message_out = cStringIO.StringIO()
    gen = email.generator.Generator(message_out, maxheaderlen=0)
    gen.flatten(message, unixfrom=False)

    # Get the content text out of the message.
    message_text = message_out.getvalue()
    content_start = message_text.find('\n\n') + 2
    content_text = message_text[content_start:]
    content_text = content_text.replace('\n', '\r\n')

    return message.get('Content-Type'), content_text

  def store_blob_and_transform_request(self, environ):
    """Stores a blob in response to a WSGI request and transforms environ.

    environ is modified so that it is suitable for forwarding to the user's
    application.

    Args:
      environ: An environ dict for the current request as defined in PEP-333.

    Raises:
      webob.exc.HTTPException: The upload failed.
    """
    # Only permit POST.
    if environ['REQUEST_METHOD'].lower() != 'post':
      self.abort(405)

    url_match = _UPLOAD_URL_PATTERN.match(environ['PATH_INFO'])
    if not url_match:
      self.abort(404)
    upload_key = url_match.group(1)

    # Retrieve upload session.
    try:
      upload_session = datastore.Get(upload_key)
    except datastore_errors.EntityNotFoundError:
      detail = 'No such upload session: %s' % upload_key
      logging.error(detail)
      self.abort(404, detail=detail)

    success_path = upload_session['success_path'].encode('ascii')
    max_bytes_per_blob = upload_session['max_bytes_per_blob']
    max_bytes_total = upload_session['max_bytes_total']
    bucket_name = upload_session.get('gs_bucket_name', None)

    upload_form = cgi.FieldStorage(fp=environ['wsgi.input'],
                                   environ=environ)

    # Generate debug log message
    logstrings = []
    for k in sorted(upload_form):
      vs = upload_form[k]
      if not isinstance(vs, list):
        vs = [vs]
      for v in vs:
        if v.filename:
          logstrings.append('%s=%s' % (k, v.filename))
    logging.debug('Received blobstore upload: %s', ', '.join(logstrings))

    # It's ok to read the whole string in memory because the content is
    # merely a reference to the blob, not the blob itself.
    content_type, content_text = self.store_and_build_forward_message(
        upload_form,
        max_bytes_per_blob=max_bytes_per_blob,
        max_bytes_total=max_bytes_total,
        bucket_name=bucket_name)

    datastore.Delete(upload_session)

    # Ensure that certain HTTP_ variables are not forwarded.
    for name in _STRIPPED_ENVIRON:
      if name in environ:
        del environ[name]

    # Replace some HTTP headers in the forwarded environ.
    environ['CONTENT_TYPE'] = content_type
    environ['CONTENT_LENGTH'] = str(len(content_text))

    # Forward on to success_path. Like production, only the path and query
    # matter.
    parsed_url = urlparse.urlsplit(success_path)
    environ['PATH_INFO'] = parsed_url.path
    if parsed_url.query:
      environ['QUERY_STRING'] = parsed_url.query

    # The user is always an administrator for the forwarded request.
    environ[constants.FAKE_IS_ADMIN_HEADER] = '1'

    # Set the wsgi variables
    environ['wsgi.input'] = cStringIO.StringIO(content_text)

  def __call__(self, environ, start_response):
    """Handles WSGI requests.

    Args:
      environ: An environ dict for the current request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    # Handle any errors in the blob uploader, but do not catch errors raised by
    # the user's application.
    try:
      self.store_blob_and_transform_request(environ)
    except webob.exc.HTTPException, e:

      def start_response_with_exc_info(status, headers,
                                       exc_info=sys.exc_info()):
        start_response(status, headers, exc_info)

      return e(environ, start_response_with_exc_info)

    return self._forward_app(environ, start_response)
