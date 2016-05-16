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




"""A Python blobstore API used by app developers.

Contains methods used to interface with Blobstore API.  Includes db.Model-like
class representing a reference to a very large BLOB.  Imports db.Key-like
class representing a blob-key.
"""











import base64
import email
import email.message

from google.appengine.api import datastore
from google.appengine.api import datastore_errors
from google.appengine.api import datastore_types
from google.appengine.api.blobstore import blobstore
from google.appengine.ext import db

__all__ = ['BLOB_INFO_KIND',
           'BLOB_KEY_HEADER',
           'BLOB_MIGRATION_KIND',
           'BLOB_RANGE_HEADER',
           'BlobFetchSizeTooLargeError',
           'BlobInfo',
           'BlobInfoParseError',
           'BlobKey',
           'BlobMigrationRecord',
           'BlobNotFoundError',
           'BlobReferenceProperty',
           'BlobReader',
           'FileInfo',
           'FileInfoParseError',
           'DataIndexOutOfRangeError',
           'PermissionDeniedError',
           'Error',
           'InternalError',
           'MAX_BLOB_FETCH_SIZE',
           'UPLOAD_INFO_CREATION_HEADER',
           'CLOUD_STORAGE_OBJECT_HEADER',
           'create_rpc',
           'create_upload_url',
           'create_upload_url_async',
           'delete',
           'delete_async',
           'fetch_data',
           'fetch_data_async',
           'create_gs_key',
           'create_gs_key_async',
           'GS_PREFIX',
           'get',
           'parse_blob_info',
           'parse_file_info']

Error = blobstore.Error
InternalError = blobstore.InternalError
BlobFetchSizeTooLargeError = blobstore.BlobFetchSizeTooLargeError
BlobNotFoundError = blobstore.BlobNotFoundError
_CreationFormatError = blobstore._CreationFormatError
DataIndexOutOfRangeError = blobstore.DataIndexOutOfRangeError
PermissionDeniedError = blobstore.PermissionDeniedError

BlobKey = blobstore.BlobKey
create_rpc = blobstore.create_rpc
create_upload_url = blobstore.create_upload_url
create_upload_url_async = blobstore.create_upload_url_async
delete = blobstore.delete
delete_async = blobstore.delete_async
create_gs_key = blobstore.create_gs_key
create_gs_key_async = blobstore.create_gs_key_async


BLOB_INFO_KIND = blobstore.BLOB_INFO_KIND
BLOB_MIGRATION_KIND = blobstore.BLOB_MIGRATION_KIND
BLOB_KEY_HEADER = blobstore.BLOB_KEY_HEADER
BLOB_RANGE_HEADER = blobstore.BLOB_RANGE_HEADER
MAX_BLOB_FETCH_SIZE = blobstore.MAX_BLOB_FETCH_SIZE
UPLOAD_INFO_CREATION_HEADER = blobstore.UPLOAD_INFO_CREATION_HEADER
CLOUD_STORAGE_OBJECT_HEADER = blobstore.CLOUD_STORAGE_OBJECT_HEADER
GS_PREFIX = blobstore.GS_PREFIX


class BlobInfoParseError(Error):
  """CGI parameter does not contain valid BlobInfo record."""


class FileInfoParseError(Error):
  """CGI parameter does not contain valid FileInfo record."""




class _GqlQuery(db.GqlQuery):
  """GqlQuery class that explicitly sets model-class.

  This does the same as the original db.GqlQuery class except that it does
  not try to find the model class based on the compiled GQL query.  The
  caller instead provides the query with a model class to use for construction.

  This class is required for compatibility with the current db.py query
  mechanism but will be removed in the future.  DO NOT USE.
  """


  def __init__(self, query_string, model_class, *args, **kwds):
    """Constructor.

    Args:
      query_string: Properly formatted GQL query string.
      model_class: Model class from which entities are constructed.
      *args: Positional arguments used to bind numeric references in the query.
      **kwds: Dictionary-based arguments for named references.
    """


    from google.appengine.ext import gql
    app = kwds.pop('_app', None)
    self._proto_query = gql.GQL(query_string, _app=app, namespace='')

    super(db.GqlQuery, self).__init__(model_class)
    self.bind(*args, **kwds)




class BlobInfo(object):
  """Information about blobs in Blobstore.

  This is a db.Model-like class that contains information about blobs stored
  by an application.  Like db.Model, this class is backed by an Datastore
  entity, however, BlobInfo instances are read-only and have a much more
  limited interface.

  Each BlobInfo has a key of type BlobKey associated with it. This key is
  specific to the Blobstore API and is not compatible with db.get.  The key
  can be used for quick lookup by passing it to BlobInfo.get.  This
  key converts easily to a string, which is web safe and can be embedded
  in URLs.

  Properties:
    content_type: Content type of blob.
    creation: Creation date of blob, when it was uploaded.
    filename: Filename user selected from their machine.
    size: Size of uncompressed blob.
    md5_hash: The md5 hash value of the uploaded blob.

  All properties are read-only.  Attempting to assign a value to a property
  will raise NotImplementedError.
  """

  _unindexed_properties = frozenset([])


  _all_properties = frozenset(['content_type', 'creation', 'filename',
                               'size', 'md5_hash'])

  @property
  def content_type(self):
    return self.__get_value('content_type')

  @property
  def creation(self):
    return self.__get_value('creation')

  @property
  def filename(self):
    return self.__get_value('filename')

  @property
  def size(self):
    return self.__get_value('size')

  @property
  def md5_hash(self):
    return self.__get_value('md5_hash')

  def __init__(self, entity_or_blob_key, _values=None):
    """Constructor for wrapping blobstore entity.

    The constructor should not be used outside this package and tests.

    Args:
      entity: Datastore entity that represents the blob reference.
    """
    if isinstance(entity_or_blob_key, datastore.Entity):
      self.__entity = entity_or_blob_key
      self.__key = BlobKey(entity_or_blob_key.key().name())
    elif isinstance(entity_or_blob_key, BlobKey):
      self.__entity = _values
      self.__key = entity_or_blob_key
    else:
      raise TypeError('Must provide Entity or BlobKey')



  @classmethod
  def from_entity(cls, entity):
    """Convert entity to BlobInfo.

    This method is required for compatibility with the current db.py query
    mechanism but will be removed in the future.  DO NOT USE.
    """
    return BlobInfo(entity)



  @classmethod
  def properties(cls):
    """Set of properties that belong to BlobInfo.

    This method is required for compatibility with the current db.py query
    mechanism but will be removed in the future.  DO NOT USE.
    """
    return set(cls._all_properties)

  def __get_value(self, name):
    """Get a BlobInfo value, loading entity if necessary.

    This method allows lazy loading of the underlying datastore entity.  It
    should never be invoked directly.

    Args:
      name: Name of property to get value for.

    Returns:
      Value of BlobInfo property from entity.
    """
    if self.__entity is None:
      self.__entity = datastore.Get(
          datastore_types.Key.from_path(
              self.kind(), str(self.__key), namespace=''))
    try:
      return self.__entity[name]
    except KeyError:
      raise AttributeError(name)


  def key(self):
    """Get key for blob.

    Returns:
      BlobKey instance that identifies this blob.
    """
    return self.__key

  def delete(self, _token=None):
    """Permanently delete blob from Blobstore."""
    delete(self.key(), _token=_token)

  def open(self, *args, **kwargs):
    """Returns a BlobReader for this blob.

    Args:
      *args, **kwargs: Passed to BlobReader constructor.
    Returns:
      A BlobReader instance.
    """
    return BlobReader(self, *args, **kwargs)

  @classmethod
  def get(cls, blob_keys):
    """Retrieve BlobInfo by key or list of keys.

    Args:
      blob_keys: A key or a list of keys.  Keys may be instances of str,
      unicode and BlobKey.

    Returns:
      A BlobInfo instance associated with provided key or a list of BlobInfo
      instances if a list of keys was provided.  Keys that are not found in
      Blobstore return None as their values.
    """
    blob_keys = cls.__normalize_and_convert_keys(blob_keys)
    try:
      entities = datastore.Get(blob_keys)
    except datastore_errors.EntityNotFoundError:
      return None
    if isinstance(entities, datastore.Entity):
      return BlobInfo(entities)
    else:
      references = []
      for entity in entities:
        if entity is not None:
          references.append(BlobInfo(entity))
        else:
          references.append(None)
      return references

  @classmethod
  def all(cls):
    """Get query for all Blobs associated with application.

    Returns:
      A db.Query object querying over BlobInfo's datastore kind.
    """
    return db.Query(model_class=cls, namespace='')

  @classmethod
  def __factory_for_kind(cls, kind):
    if kind == BLOB_INFO_KIND:
      return BlobInfo
    raise ValueError('Cannot query for kind %s' % kind)

  @classmethod
  def gql(cls, query_string, *args, **kwds):
    """Returns a query using GQL query string.

    See appengine/ext/gql for more information about GQL.

    Args:
      query_string: Properly formatted GQL query string with the
        'SELECT * FROM <entity>' part omitted
      *args: rest of the positional arguments used to bind numeric references
        in the query.
      **kwds: dictionary-based arguments (for named parameters).

    Returns:
      A gql.GqlQuery object querying over BlobInfo's datastore kind.
    """
    return _GqlQuery('SELECT * FROM %s %s'
                       % (cls.kind(), query_string),
                     cls,
                     *args,
                     **kwds)


  @classmethod
  def kind(self):
    """Get the entity kind for the BlobInfo.

    This method is required for compatibility with the current db.py query
    mechanism but will be removed in the future.  DO NOT USE.
    """
    return BLOB_INFO_KIND

  @classmethod
  def __normalize_and_convert_keys(cls, keys):
    """Normalize and convert all keys to BlobKey type.

    This method is based on datastore.NormalizeAndTypeCheck().

    Args:
      keys: A single key or a list/tuple of keys.  Keys may be a string
        or BlobKey

    Returns:
      Single key or list with all strings replaced by BlobKey instances.
    """
    if isinstance(keys, (list, tuple)):
      multiple = True

      keys = list(keys)
    else:
      multiple = False
      keys = [keys]

    for index, key in enumerate(keys):
      if not isinstance(key, (basestring, BlobKey)):
        raise datastore_errors.BadArgumentError(
            'Expected str or BlobKey; received %s (a %s)' % (
                key,
                datastore.typename(key)))
      keys[index] = datastore.Key.from_path(cls.kind(), str(key), namespace='')

    if multiple:
      return keys
    else:
      return keys[0]


def get(blob_key):
  """Get a BlobInfo record from blobstore.

  Does the same as BlobInfo.get.
  """
  return BlobInfo.get(blob_key)


def _get_upload_content(field_storage):
  """Returns an email.Message holding the values of the file transfer.

  It decodes the content of the field storage and creates a new email.Message.

  Args:
    field_storage: cgi.FieldStorage that represents uploaded blob.

  Returns:
    An email.message.Message holding the upload information.
  """
  message = email.message.Message()
  message.add_header(
      'content-transfer-encoding',
      field_storage.headers.getheader('Content-Transfer-Encoding', ''))
  message.set_payload(field_storage.file.read())
  payload = message.get_payload(decode=True)
  return email.message_from_string(payload)


def _parse_upload_info(field_storage, error_class):
  """Parse the upload info from file upload field_storage.

  Args:
    field_storage: cgi.FieldStorage that represents uploaded blob.
    error_class: error to raise.

  Returns:
    A dictionary containing the parsed values. None if there was no
    field_storage.

  Raises:
    error_class when provided a field_storage that does not contain enough
    information.
  """
  if field_storage is None:
    return None

  field_name = field_storage.name

  def get_value(dict, name):
    value = dict.get(name, None)
    if value is None:
      raise error_class(
          'Field %s has no %s.' % (field_name, name))
    return value

  filename = get_value(field_storage.disposition_options, 'filename')
  blob_key = field_storage.type_options.get('blob-key', None)

  upload_content = _get_upload_content(field_storage)


  field_storage.file.seek(0)
  content_type = get_value(upload_content, 'content-type')
  size = get_value(upload_content, 'content-length')
  creation_string = get_value(upload_content, UPLOAD_INFO_CREATION_HEADER)
  md5_hash_encoded = get_value(upload_content, 'content-md5')
  md5_hash = base64.urlsafe_b64decode(md5_hash_encoded)
  gs_object_name = upload_content.get(CLOUD_STORAGE_OBJECT_HEADER, None)

  try:
    size = int(size)
  except (TypeError, ValueError):
    raise error_class(
        '%s is not a valid value for %s size.' % (size, field_name))

  try:
    creation = blobstore._parse_creation(creation_string, field_name)
  except blobstore._CreationFormatError, err:
    raise error_class(str(err))

  return {'blob_key': blob_key,
          'content_type': content_type,
          'creation': creation,
          'filename': filename,
          'size': size,
          'md5_hash': md5_hash,
          'gs_object_name': gs_object_name,
         }


def parse_blob_info(field_storage):
  """Parse a BlobInfo record from file upload field_storage.

  Args:
    field_storage: cgi.FieldStorage that represents uploaded blob.

  Returns:
    BlobInfo record as parsed from the field-storage instance.
    None if there was no field_storage.

  Raises:
    BlobInfoParseError when provided field_storage does not contain enough
    information to construct a BlobInfo object.
  """
  info = _parse_upload_info(field_storage, BlobInfoParseError)

  if info is None:
    return None

  key = info.pop('blob_key', None)
  if not key:
    raise BlobInfoParseError('Field %s has no %s.' % (field_storage.name,
                                                      'blob_key'))

  info.pop('gs_object_name', None)

  return BlobInfo(BlobKey(key), info)


class FileInfo(object):
  """Information about uploaded files.

  This is a class that contains information about blobs stored by an
  application.

  This class is similar to BlobInfo, however this has no key and it is not
  persisted in the datastore.

  Properties:
    content_type: Content type of uploaded file.
    creation: Creation date of uploaded file, when it was uploaded.
    filename: Filename user selected from their machine.
    size: Size of uncompressed file.
    md5_hash: The md5 hash value of the uploaded file.
    gs_object_name: Name of the file written to Google Cloud Storage or None if
      the file was not uploaded to Google Cloud Storage.

  All properties are read-only.  Attempting to assign a value to a property
  will raise AttributeError.
  """

  def __init__(self, filename=None, content_type=None, creation=None,
               size=None, md5_hash=None, gs_object_name=None):
    self.__filename = filename
    self.__content_type = content_type
    self.__creation = creation
    self.__size = size
    self.__md5_hash = md5_hash
    self.__gs_object_name = gs_object_name

  @property
  def filename(self):
    return self.__filename

  @property
  def content_type(self):
    return self.__content_type

  @property
  def creation(self):
    return self.__creation

  @property
  def size(self):
    return self.__size

  @property
  def md5_hash(self):
    return self.__md5_hash

  @property
  def gs_object_name(self):
    return self.__gs_object_name


def parse_file_info(field_storage):
  """Parse an FileInfo record from file upload field_storage.

  Args:
    field_storage: cgi.FieldStorage that represents uploaded file.

  Returns:
    FileInfo record as parsed from the field-storage instance.
    None if there was no field_storage.

  Raises:
    FileInfoParseError when provided a field_storage that does not contain
    enough information to construct a FileInfo object.
  """
  info = _parse_upload_info(field_storage, FileInfoParseError)

  if info is None:
    return None

  info.pop('blob_key', None)

  return FileInfo(**info)


class BlobReferenceProperty(db.Property):
  """Property compatible with db.Model classes.

  Add references to blobs to domain models using BlobReferenceProperty:

    class Picture(db.Model):
      title = db.StringProperty()
      image = blobstore.BlobReferenceProperty()
      thumbnail = blobstore.BlobReferenceProperty()

  To find the size of a picture using this model:

    picture = Picture.get(picture_key)
    print picture.image.size

  BlobInfo objects are lazily loaded so iterating over models with
  for BlobKeys is efficient, the following does not need to hit
  Datastore for each image key:

    list_of_untitled_blobs = []
    for picture in Picture.gql("WHERE title=''"):
      list_of_untitled_blobs.append(picture.image.key())
  """

  data_type = BlobInfo

  def get_value_for_datastore(self, model_instance):
    """Translate model property to datastore value."""
    blob_info = super(BlobReferenceProperty,
                      self).get_value_for_datastore(model_instance)
    if blob_info is None:
      return None
    return blob_info.key()

  def make_value_from_datastore(self, value):
    """Translate datastore value to BlobInfo."""
    if value is None:
      return None
    return BlobInfo(value)

  def validate(self, value):
    """Validate that assigned value is BlobInfo.

    Automatically converts from strings and BlobKey instances.
    """
    if isinstance(value, (basestring)):
      value = BlobInfo(BlobKey(value))
    elif isinstance(value, BlobKey):
      value = BlobInfo(value)
    return super(BlobReferenceProperty, self).validate(value)


def fetch_data(blob, start_index, end_index, rpc=None):
  """Fetch data for blob.

  Fetches a fragment of a blob up to MAX_BLOB_FETCH_SIZE in length.  Attempting
  to fetch a fragment that extends beyond the boundaries of the blob will return
  the amount of data from start_index until the end of the blob, which will be
  a smaller size than requested.  Requesting a fragment which is entirely
  outside the boundaries of the blob will return empty string.  Attempting
  to fetch a negative index will raise an exception.

  Args:
    blob: BlobInfo, BlobKey, str or unicode representation of BlobKey of
      blob to fetch data from.
    start_index: Start index of blob data to fetch.  May not be negative.
    end_index: End index (inclusive) of blob data to fetch.  Must be
      >= start_index.
    rpc: Optional UserRPC object.

  Returns:
    str containing partial data of blob.  If the indexes are legal but outside
    the boundaries of the blob, will return empty string.

  Raises:
    TypeError if start_index or end_index are not indexes.  Also when blob
      is not a string, BlobKey or BlobInfo.
    DataIndexOutOfRangeError when start_index < 0 or end_index < start_index.
    BlobFetchSizeTooLargeError when request blob fragment is larger than
      MAX_BLOB_FETCH_SIZE.
    BlobNotFoundError when blob does not exist.
  """
  rpc = fetch_data_async(blob, start_index, end_index, rpc=rpc)
  return rpc.get_result()


def fetch_data_async(blob, start_index, end_index, rpc=None):
  """Fetch data for blob -- async version.

  Fetches a fragment of a blob up to MAX_BLOB_FETCH_SIZE in length.  Attempting
  to fetch a fragment that extends beyond the boundaries of the blob will return
  the amount of data from start_index until the end of the blob, which will be
  a smaller size than requested.  Requesting a fragment which is entirely
  outside the boundaries of the blob will return empty string.  Attempting
  to fetch a negative index will raise an exception.

  Args:
    blob: BlobInfo, BlobKey, str or unicode representation of BlobKey of
      blob to fetch data from.
    start_index: Start index of blob data to fetch.  May not be negative.
    end_index: End index (inclusive) of blob data to fetch.  Must be
      >= start_index.
    rpc: Optional UserRPC object.

  Returns:
    A UserRPC whose result will be a str as returned by fetch_data().

  Raises:
    TypeError if start_index or end_index are not indexes.  Also when blob
      is not a string, BlobKey or BlobInfo.
    The following exceptions may be raised when rpc.get_result() is
    called:
    DataIndexOutOfRangeError when start_index < 0 or end_index < start_index.
    BlobFetchSizeTooLargeError when request blob fragment is larger than
      MAX_BLOB_FETCH_SIZE.
    BlobNotFoundError when blob does not exist.
  """
  if isinstance(blob, BlobInfo):
    blob = blob.key()
  return blobstore.fetch_data_async(blob, start_index, end_index, rpc=rpc)


class BlobReader(object):
  """Provides a read-only file-like interface to a blobstore blob."""

  SEEK_SET = 0
  SEEK_CUR = 1
  SEEK_END = 2

  def __init__(self, blob, buffer_size=131072, position=0):
    """Constructor.

    Args:
      blob: The blob key, blob info, or string blob key to read from.
      buffer_size: The minimum size to fetch chunks of data from blobstore.
      position: The initial position in the file.

    Raises:
      ValueError if a blob key, blob info or string blob key is not supplied.
    """
    if not blob:
      raise ValueError('A BlobKey, BlobInfo or string is required.')
    if hasattr(blob, 'key'):
      self.__blob_key = blob.key()
      self.__blob_info = blob
    else:
      self.__blob_key = blob
      self.__blob_info = None
    self.__buffer_size = buffer_size
    self.__buffer = ""
    self.__position = position
    self.__buffer_position = 0
    self.__eof = False

  def __iter__(self):
    """Returns a file iterator for this BlobReader."""
    return self

  def __getstate__(self):
    """Returns the serialized state for this BlobReader."""
    return (self.__blob_key, self.__buffer_size, self.__position)

  def __setstate__(self, state):
    """Restores pickled state for this BlobReader."""
    self.__init__(*state)

  def close(self):
    """Close the file.

    A closed file cannot be read or written any more. Any operation which
    requires that the file be open will raise a ValueError after the file has
    been closed. Calling close() more than once is allowed.
    """
    self.__blob_key = None

  def flush(self):
    raise IOError("BlobReaders are read-only")

  def next(self):
    """Returns the next line from the file.

    Returns:
      A string, terminted by \n. The last line may not be terminated by \n.
      If EOF is reached, an empty string will be returned.
    """
    line = self.readline()
    if not line:
      raise StopIteration
    return line

  def __read_from_buffer(self, size):
    """Reads at most size bytes from the buffer.

    Args:
      size: Number of bytes to read, or negative to read the entire buffer.
    Returns:
      Tuple (data, size):
        data: The bytes read from the buffer.
        size: The remaining unread byte count. Negative when size
          is negative. Thus when remaining size != 0, the calling method
          may choose to fill the buffer again and keep reading.
    """

    if not self.__blob_key:
      raise ValueError("File is closed")

    if size < 0:
      end_pos = len(self.__buffer)
    else:
      end_pos = self.__buffer_position + size
    data = self.__buffer[self.__buffer_position:end_pos]


    data_length = len(data)
    size -= data_length
    self.__position += data_length
    self.__buffer_position += data_length


    if self.__buffer_position == len(self.__buffer):
      self.__buffer = ""
      self.__buffer_position = 0

    return data, size

  def __fill_buffer(self, size=0):
    """Fills the internal buffer.

    Args:
      size: Number of bytes to read. Will be clamped to
        [self.__buffer_size, MAX_BLOB_FETCH_SIZE].
    """
    read_size = min(max(size, self.__buffer_size), MAX_BLOB_FETCH_SIZE)

    self.__buffer = fetch_data(self.__blob_key, self.__position,
                               self.__position + read_size - 1)
    self.__buffer_position = 0
    self.__eof = len(self.__buffer) < read_size

  def read(self, size=-1):
    """Read at most size bytes from the file.

     Fewer bytes are read if the read hits EOF before obtaining size bytes.
     If the size argument is negative or omitted, read all data until EOF is
     reached. The bytes are returned as a string object. An empty string is
     returned when EOF is encountered immediately.

     Calling read() without a size specified is likely to be dangerous, as it
     may read excessive amounts of data.

     Args:
       size: Optional. The maximum number of bytes to read. When omitted, read()
         returns all remaining data in the file.

     Returns:
       The read data, as a string.
    """
    data_list = []
    while True:
      data, size = self.__read_from_buffer(size)
      data_list.append(data)
      if size == 0 or self.__eof:
        return ''.join(data_list)
      self.__fill_buffer(size)

  def readline(self, size=-1):
    """Read one entire line from the file.

    A trailing newline character is kept in the string (but may be absent when a
    file ends with an incomplete line). If the size argument is present and
    non-negative, it is a maximum byte count (including the trailing newline)
    and an incomplete line may be returned. An empty string is returned only
    when EOF is encountered immediately.

    Args:
      size: Optional. The maximum number of bytes to read.

    Returns:
      The read data, as a string.
    """
    data_list = []
    while True:
      if size < 0:
        end_pos = len(self.__buffer)
      else:
        end_pos = self.__buffer_position + size
      newline_pos = self.__buffer.find('\n', self.__buffer_position, end_pos)
      if newline_pos != -1:

        data_list.append(
            self.__read_from_buffer(newline_pos
                                    - self.__buffer_position + 1)[0])
        break
      else:

        data, size = self.__read_from_buffer(size)
        data_list.append(data)
        if size == 0 or self.__eof:
          break
        self.__fill_buffer()
    return ''.join(data_list)

  def readlines(self, sizehint=None):
    """Read until EOF using readline() and return a list of lines thus read.

    If the optional sizehint argument is present, instead of reading up to EOF,
    whole lines totalling approximately sizehint bytes (possibly after rounding
    up to an internal buffer size) are read.

    Args:
      sizehint: A hint as to the maximum number of bytes to read.

    Returns:
      A list of strings, each being a single line from the file.
    """
    lines = []
    while sizehint is None or sizehint > 0:
      line = self.readline()
      if sizehint:
        sizehint -= len(line)
      if not line:

        break
      lines.append(line)
    return lines

  def seek(self, offset, whence=SEEK_SET):
    """Set the file's current position, like stdio's fseek().

    The whence argument is optional and defaults to os.SEEK_SET or 0 (absolute
    file positioning); other values are os.SEEK_CUR or 1 (seek relative to the
    current position) and os.SEEK_END or 2 (seek relative to the file's end).

    Args:
      offset: The relative offset to seek to.
      whence: Defines what the offset is relative to. See description for
          details.
    """
    if whence == BlobReader.SEEK_CUR:
      offset = self.__position + offset
    elif whence == BlobReader.SEEK_END:
      offset = self.blob_info.size + offset
    self.__buffer = ""
    self.__buffer_position = 0
    self.__position = offset
    self.__eof = False

  def tell(self):
    """Return the file's current position, like stdio's ftell()."""
    return self.__position

  def truncate(self, size):
    raise IOError("BlobReaders are read-only")

  def write(self, str):
    raise IOError("BlobReaders are read-only")

  def writelines(self, sequence):
    raise IOError("BlobReaders are read-only")

  @property
  def blob_info(self):
    """Returns the BlobInfo for this file."""
    if not self.__blob_info:
      self.__blob_info = BlobInfo.get(self.__blob_key)
    return self.__blob_info

  @property
  def closed(self):
    """Returns True if this file is closed, False otherwise."""
    return self.__blob_key is None

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.close()


class BlobMigrationRecord(db.Model):
  """A model that records the result of a blob migration."""

  new_blob_ref = BlobReferenceProperty(indexed=False, name='new_blob_key')

  @classmethod
  def kind(cls):
    return blobstore.BLOB_MIGRATION_KIND

  @classmethod
  def get_by_blob_key(cls, old_blob_key):
    """Fetches the BlobMigrationRecord for the given blob key.

    Args:
      old_blob_key: The blob key used in the previous app.

    Returns:
      A instance of blobstore.BlobMigrationRecord or None
    """
    return cls.get_by_key_name(str(old_blob_key))

  @classmethod
  def get_new_blob_key(cls, old_blob_key):
    """Looks up the new key for a blob.

    Args:
      old_blob_key: The original blob key.

    Returns:
      The blobstore.BlobKey of the migrated blob.
    """
    record = cls.get_by_blob_key(old_blob_key)
    if record:
      return record.new_blob_ref.key()
