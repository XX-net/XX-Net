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




"""Helper CGI for POST uploads.

Utility library contains the main logic behind simulating the blobstore
uploading mechanism.

Contents:
  GenerateBlobKey: Function for generation unique blob-keys.
  UploadCGIHandler: Main CGI handler class for post uploads.
"""


import base64
import cStringIO
import datetime
import random
import time
import hashlib

from google.appengine.api import datastore
from google.appengine.api import datastore_errors
from google.appengine.api.blobstore import blobstore



try:
  from email.mime import base
  from email.mime import multipart
  from email import generator
except ImportError:
  from email import Generator as generator
  from email import MIMEBase as base
  from email import MIMEMultipart as multipart




STRIPPED_HEADERS = frozenset(('content-length',
                              'content-md5',
                              'content-type',
                             ))


class Error(Exception):
  """Base class for upload processing errors."""


class InvalidMIMETypeFormatError(Error):
  """MIME type was formatted incorrectly."""


class UploadEntityTooLargeError(Error):
  """Entity being uploaded exceeded the allowed size."""


def GenerateBlobKey(time_func=time.time, random_func=random.random):
  """Generate a unique BlobKey.

  BlobKey is generated using the current time stamp combined with a random
  number.  The two values are subject to an md5 digest and base64 url-safe
  encoded.  The new key is checked against the possibility of existence within
  the datastore and the random number is regenerated until there is no match.

  Args:
    time_func: Function used for generating the timestamp.  Used for
      dependency injection.  Allows for predictable results during tests.
      Must return a floating point UTC timestamp.
    random_func: Function used for generating the random number.  Used for
      dependency injection.  Allows for predictable results during tests.

  Returns:
    String version of BlobKey that is unique within the BlobInfo datastore.
    None if there are too many name conflicts.
  """
  timestamp = str(time_func())
  tries = 0
  while tries < 10:
    number = str(random_func())
    digester = hashlib.md5()
    digester.update(timestamp)
    digester.update(number)
    blob_key = base64.urlsafe_b64encode(digester.digest())
    datastore_key = datastore.Key.from_path(blobstore.BLOB_INFO_KIND,
                                            blob_key,
                                            namespace='')
    try:
      datastore.Get(datastore_key)
      tries += 1
    except datastore_errors.EntityNotFoundError:
      return blob_key
  return None


def _SplitMIMEType(mime_type):
  """Split MIME-type in to main and sub type.

  Args:
    mime_type: full MIME type string.

  Returns:
    (main, sub):
      main: Main part of mime type (application, image, text, etc).
      sub: Subtype part of mime type (pdf, png, html, etc).

  Raises:
    InvalidMIMETypeFormatError: If form item has incorrectly formatted MIME
      type.
  """
  if mime_type:
    mime_type_array = mime_type.split('/')

    if len(mime_type_array) == 1:
        raise InvalidMIMETypeFormatError('Missing MIME sub-type.')
    elif len(mime_type_array) == 2:
      main_type, sub_type = mime_type_array
      if not(main_type and sub_type):
        raise InvalidMIMETypeFormatError(
            'Incorrectly formatted MIME type: %s' % mime_type)
      return main_type, sub_type
    else:
      raise InvalidMIMETypeFormatError(
          'Incorrectly formatted MIME type: %s' % mime_type)
  else:
    return 'application', 'octet-stream'


class UploadCGIHandler(object):
  """Class used for handling an upload post.

  The main interface to this class is the UploadCGI method.  This will recieve
  the upload form, store the blobs contained in the post and rewrite the blobs
  to contain BlobKeys instead of blobs.
  """

  def __init__(self,
               blob_storage,
               generate_blob_key=GenerateBlobKey,
               now_func=datetime.datetime.now):
    """Constructor.

    Args:
      blob_storage: BlobStorage instance where actual blobs are stored.
      generate_blob_key: Function used for generating unique blob keys.
      now_func: Function that returns the current timestamp.
    """
    self.__blob_storage = blob_storage
    self.__generate_blob_key = generate_blob_key
    self.__now_func = now_func

  def StoreBlob(self, form_item, creation):
    """Store form-item to blob storage.

    Args:
      form_item: FieldStorage instance that represents a specific form field.
        This instance should have a non-empty filename attribute, meaning that
        it is an uploaded blob rather than a normal form field.
      creation: Timestamp to associate with new blobs creation time.  This
        parameter is provided so that all blobs in the same upload form can have
        the same creation date.

    Returns:
      datastore.Entity('__BlobInfo__') associated with the upload.
    """
    main_type, sub_type = _SplitMIMEType(form_item.type)

    blob_key = self.__generate_blob_key()
    blob_file = form_item.file
    if 'Content-Transfer-Encoding' in form_item.headers:
      if form_item.headers['Content-Transfer-Encoding'] == 'base64':
        blob_file = cStringIO.StringIO(
            base64.urlsafe_b64decode(blob_file.read()))
    self.__blob_storage.StoreBlob(blob_key, blob_file)
    content_type_formatter = base.MIMEBase(main_type, sub_type,
                                           **form_item.type_options)

    blob_entity = datastore.Entity('__BlobInfo__',
                                   name=str(blob_key),
                                   namespace='')
    blob_entity['content_type'] = (
        content_type_formatter['content-type'].decode('utf-8'))
    blob_entity['creation'] = creation
    blob_entity['filename'] = form_item.filename.decode('utf-8')

    blob_file.seek(0)
    digester = hashlib.md5()
    while True:
      block = blob_file.read(1 << 20)
      if not block:
        break
      digester.update(block)

    blob_entity['md5_hash'] = digester.hexdigest()
    blob_entity['size'] = blob_file.tell()
    blob_file.seek(0)

    datastore.Put(blob_entity)
    return blob_entity

  def _GenerateMIMEMessage(self,
                           form,
                           boundary=None,
                           max_bytes_per_blob=None,
                           max_bytes_total=None):
    """Generate a new post from original form.

    Also responsible for storing blobs in the datastore.

    Args:
      form: Instance of cgi.FieldStorage representing the whole form
        derived from original post data.
      boundary: Boundary to use for resulting form.  Used only in tests so
        that the boundary is always consistent.
      max_bytes_per_blob: The maximum size in bytes that any single blob
        in the form is allowed to be.
      max_bytes_total: The maximum size in bytes that the total of all blobs
        in the form is allowed to be.

    Returns:
      A MIMEMultipart instance representing the new HTTP post which should be
      forwarded to the developers actual CGI handler. DO NOT use the return
      value of this method to generate a string unless you know what you're
      doing and properly handle folding whitespace (from rfc822) properly.

    Raises:
      UploadEntityTooLargeError: The upload exceeds either the
        max_bytes_per_blob or max_bytes_total limits.
    """
    message = multipart.MIMEMultipart('form-data', boundary)
    for name, value in form.headers.items():
      if name.lower() not in STRIPPED_HEADERS:
        message.add_header(name, value)

    def IterateForm():
      """Flattens form in to single sequence of cgi.FieldStorage instances.

      The resulting cgi.FieldStorage objects are a little bit irregular in
      their structure.  A single name can have mulitple sub-items.  In this
      case, the root FieldStorage object has a list associated with that field
      name.  Otherwise, the root FieldStorage object just refers to a single
      nested instance.

      Lists of FieldStorage instances occur when a form has multiple values
      for the same name.

      Yields:
        cgi.FieldStorage irrespective of their nesting level.
      """


      for key in sorted(form):
        form_item = form[key]
        if isinstance(form_item, list):
          for list_item in form_item:
            yield list_item
        else:
          yield form_item

    creation = self.__now_func()
    total_bytes_uploaded = 0
    created_blobs = []
    upload_too_large = False

    for form_item in IterateForm():








      disposition_parameters = {'name': form_item.name}

      if form_item.filename is None:

        variable = base.MIMEBase('text', 'plain')
        variable.set_payload(form_item.value)
      else:



        if not form_item.filename:
          continue

        disposition_parameters['filename'] = form_item.filename

        main_type, sub_type = _SplitMIMEType(form_item.type)


        form_item.file.seek(0, 2)
        content_length = form_item.file.tell()
        form_item.file.seek(0)

        total_bytes_uploaded += content_length

        if max_bytes_per_blob is not None:
          if max_bytes_per_blob < content_length:
            upload_too_large = True
            break
        if max_bytes_total is not None:
          if max_bytes_total < total_bytes_uploaded:
            upload_too_large = True
            break


        blob_entity = self.StoreBlob(form_item, creation)


        created_blobs.append(blob_entity)

        variable = base.MIMEBase('message',
                                 'external-body',
                                 access_type=blobstore.BLOB_KEY_HEADER,
                                 blob_key=blob_entity.key().name())


        form_item.file.seek(0)
        digester = hashlib.md5()
        while True:
          block = form_item.file.read(1 << 20)
          if not block:
            break
          digester.update(block)

        blob_key = base64.urlsafe_b64encode(digester.hexdigest())
        form_item.file.seek(0)

        external = base.MIMEBase(main_type,
                                 sub_type,
                                 **form_item.type_options)
        headers = dict(form_item.headers)
        headers['Content-Length'] = str(content_length)
        headers[blobstore.UPLOAD_INFO_CREATION_HEADER] = (
            blobstore._format_creation(creation))
        headers['Content-MD5'] = blob_key
        for key, value in headers.iteritems():
          external.add_header(key, value)


        external_disposition_parameters = dict(disposition_parameters)


        external_disposition_parameters['filename'] = form_item.filename
        if not external.get('Content-Disposition'):
          external.add_header('Content-Disposition',
                              'form-data',
                              **external_disposition_parameters)
        variable.set_payload([external])


      variable.add_header('Content-Disposition',
                          'form-data',
                          **disposition_parameters)
      message.attach(variable)

    if upload_too_large:
      for blob in created_blobs:
        datastore.Delete(blob)
      raise UploadEntityTooLargeError()

    return message

  def GenerateMIMEMessageString(self,
                                form,
                                boundary=None,
                                max_bytes_per_blob=None,
                                max_bytes_total=None):
    """Generate a new post string from original form.

    Args:
      form: Instance of cgi.FieldStorage representing the whole form
        derived from original post data.
      boundary: Boundary to use for resulting form.  Used only in tests so
        that the boundary is always consistent.
      max_bytes_per_blob: The maximum size in bytes that any single blob
        in the form is allowed to be.
      max_bytes_total: The maximum size in bytes that the total of all blobs
        in the form is allowed to be.

    Returns:
      A string rendering of a MIMEMultipart instance.
    """
    message = self._GenerateMIMEMessage(form,
                                        boundary=boundary,
                                        max_bytes_per_blob=max_bytes_per_blob,
                                        max_bytes_total=max_bytes_total)
    message_out = cStringIO.StringIO()
    gen = generator.Generator(message_out, maxheaderlen=0)
    gen.flatten(message, unixfrom=False)
    return message_out.getvalue()
