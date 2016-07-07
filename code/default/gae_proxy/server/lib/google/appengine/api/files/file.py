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




"""Files API.

.. deprecated:: 1.8.1
   Use Google Cloud Storage Client library instead."""

from __future__ import with_statement



__all__ = [
           'ApiTemporaryUnavailableError',
           'BLOBSTORE_FILESYSTEM',
           'Error',
           'ExclusiveLockFailedError',
           'ExistenceError',
           'FileNotOpenedError',
           'FileTemporaryUnavailableError',
           'FILESYSTEMS',
           'FinalizationError',
           'GS_FILESYSTEM',
           'InvalidArgumentError',
           'InvalidFileNameError',
           'InvalidParameterError',
           'OperationNotSupportedError',
           'PermissionDeniedError',
           'ReadOnlyError',
           'SequenceKeyOutOfOrderError',
           'UnknownError',
           'UnsupportedContentTypeError',
           'UnsupportedOpenModeError',
           'WrongContentTypeError' ,
           'WrongOpenModeError',

           'RAW',
           'READ_BLOCK_SIZE',

           'delete',
           'finalize',
           'listdir',
           'open',
           'stat',

           'BufferedFile',
           ]

import os
import sys
import StringIO

from google.appengine.api import apiproxy_stub_map
from google.appengine.api.files import file_service_pb
from google.appengine.runtime import apiproxy_errors


BLOBSTORE_FILESYSTEM = 'blobstore'
GS_FILESYSTEM = 'gs'
FILESYSTEMS = (BLOBSTORE_FILESYSTEM, GS_FILESYSTEM)
READ_BLOCK_SIZE = 1024 * 512
_CREATION_HANDLE_PREFIX = 'writable:'
_DEFAULT_BUFFER_SIZE = 512 * 1024


class Error(Exception):
  """Base error class for this module."""


class UnsupportedOpenModeError(Error):
  """Unsupported file open mode was specified."""


class UnsupportedContentTypeError(Error):
  """Specified file content type is not supported by this api."""


class InvalidArgumentError(Error):
  """Function argument has invalid value."""


class FinalizationError(Error):
  """File is in wrong finalization state."""


class ExistenceError(Error):
  """File is in wrong existence state."""


class UnknownError(Error):
  """Unknown unexpected io error occured."""


class SequenceKeyOutOfOrderError(Error):
  """Sequence key specified is out of order.

  Attributes:
    last_sequence_key: last sequence key which was written to the file.
  """

  def __init__(self, last_sequence_key, cause=None):
    Error.__init__(self, cause)
    self.last_sequence_key = last_sequence_key


class InvalidFileNameError(Error):
  """File name is invalid."""


class FileNotOpenedError(Error):
  """File was not opened."""


class ReadOnlyError(Error):
  """File is read-only mode."""


class WrongContentTypeError(Error):
  """File has a different content type."""


class WrongOpenModeError(Error):
  """Incorrect file open mode."""


class OperationNotSupportedError(Error):
  """Incorrect file open mode."""


class PermissionDeniedError(Error):
  """Application doesn't have permissions to perform the operation."""


class ApiTemporaryUnavailableError(Error):
  """Files API is temporary unavailable. Request should be retried soon."""


class FileTemporaryUnavailableError(Error):
  """File is temporary unavailable. Request should be retried soon."""


class InvalidParameterError(Error):
  """Parameter specified in Create() call is invalid."""


class ExclusiveLockFailedError(Error):
  """Exclusive lock can't be obtained."""



RAW = file_service_pb.FileContentType.RAW


def _raise_app_error(e):
  """Convert RPC error into api-specific exception."""
  if (e.application_error in
      [file_service_pb.FileServiceErrors.EXISTENCE_ERROR,
       file_service_pb.FileServiceErrors.EXISTENCE_ERROR_METADATA_NOT_FOUND,
       file_service_pb.FileServiceErrors.EXISTENCE_ERROR_METADATA_FOUND,
       file_service_pb.FileServiceErrors.EXISTENCE_ERROR_SHARDING_MISMATCH,
       file_service_pb.FileServiceErrors.EXISTENCE_ERROR_OBJECT_NOT_FOUND,
       file_service_pb.FileServiceErrors.EXISTENCE_ERROR_BUCKET_NOT_FOUND,
       ]):
    raise ExistenceError(e)
  elif (e.application_error ==
        file_service_pb.FileServiceErrors.API_TEMPORARILY_UNAVAILABLE):
    raise ApiTemporaryUnavailableError(e)
  elif (e.application_error ==
        file_service_pb.FileServiceErrors.FINALIZATION_ERROR):
    raise FinalizationError(e)
  elif (e.application_error ==
        file_service_pb.FileServiceErrors.IO_ERROR):
    raise UnknownError(e)
  elif (e.application_error ==
        file_service_pb.FileServiceErrors.SEQUENCE_KEY_OUT_OF_ORDER):
    raise SequenceKeyOutOfOrderError(e.error_detail, e)
  elif (e.application_error ==
        file_service_pb.FileServiceErrors.INVALID_FILE_NAME):
    raise InvalidFileNameError(e)
  elif (e.application_error ==
        file_service_pb.FileServiceErrors.FILE_NOT_OPENED):
    raise FileNotOpenedError(e)
  elif (e.application_error ==
        file_service_pb.FileServiceErrors.READ_ONLY):
    raise ReadOnlyError(e)
  elif (e.application_error ==
        file_service_pb.FileServiceErrors.WRONG_CONTENT_TYPE):
    raise WrongContentTypeError(e)
  elif (e.application_error ==
        file_service_pb.FileServiceErrors.WRONG_OPEN_MODE):
    raise WrongOpenModeError(e)
  elif (e.application_error ==
        file_service_pb.FileServiceErrors.OPERATION_NOT_SUPPORTED):
    raise OperationNotSupportedError(e)
  elif (e.application_error ==
        file_service_pb.FileServiceErrors.PERMISSION_DENIED):
    raise PermissionDeniedError(e)
  elif (e.application_error ==
        file_service_pb.FileServiceErrors.FILE_TEMPORARILY_UNAVAILABLE):
    raise FileTemporaryUnavailableError(e)
  elif (e.application_error ==
        file_service_pb.FileServiceErrors.INVALID_PARAMETER):
    raise InvalidParameterError(e)
  elif (e.application_error ==
        file_service_pb.FileServiceErrors.EXCLUSIVE_LOCK_FAILED):
    raise ExclusiveLockFailedError(e)
  raise Error(e)


def _create_rpc(deadline):
  """Create RPC object for file service.

  Args:
    deadling: Request deadline in seconds.
  """
  return apiproxy_stub_map.UserRPC('file', deadline)


def _make_call(method, request, response,
               deadline=30):
  """Perform File RPC call.

  Args:
    method: Service method name as string.
    request: Request protocol buffer.
    response: Response protocol buffer.
    deadline: Request deadline in seconds.

  Raises:
    Error or it's descendant if any File API specific error has happened.
  """

  rpc = _create_rpc(deadline=deadline)
  rpc.make_call(method, request, response)
  rpc.wait()
  try:
    rpc.check_success()
  except apiproxy_errors.ApplicationError, e:
    _raise_app_error(e)


class _File(object):
  """File object.

  File object must be obtained by open() function and closed by its close()
  method. It supports scoped closing by with operator.
  """

  def __init__(self, filename, mode, content_type, exclusive_lock):
    """Constructor.

    Args:
      filename: File's name as string.
      content_type: File's content type. Value from FileContentType.ContentType
        enum.
    """
    self._filename = filename
    self._closed = False
    self._content_type = content_type
    self._mode = mode
    self._exclusive_lock = exclusive_lock
    self._offset = 0
    self._open()

  def close(self, finalize=False):
    """Close file.

    Args:
      finalize: Specifies if file should be finalized upon closing.
    """
    if self._closed:
      return
    self._closed = True
    request = file_service_pb.CloseRequest()
    response = file_service_pb.CloseResponse()
    request.set_filename(self._filename)
    request.set_finalize(finalize)
    self._make_rpc_call_with_retry('Close', request, response)

  def __enter__(self):
    return self

  def __exit__(self, atype, value, traceback):
    self.close()

  def write(self, data, sequence_key=None):
    """Write data to file.

    Args:
      data: Data to be written to the file. For RAW files it should be a string
        or byte sequence.
      sequence_key: Sequence key to use for write. Is used for RAW files only.
        File API infrastructure ensures that sequence_key are monotonically
        increasing. If sequence key less than previous one is used, a
        SequenceKeyOutOfOrderError exception with last recorded sequence key
        will be raised. If part of already written content is lost due to
        infrastructure failure, last_sequence_key will point to last
        successfully written key.

    Raises:
      SequenceKeyOutOfOrderError: Raised when passed sequence keys are not
        monotonically increasing.
      InvalidArgumentError: Raised when wrong object type is apssed in as data.
      Error: Error or its descendants are raised when other error has happened.
    """
    if self._content_type == RAW:
      request = file_service_pb.AppendRequest()
      response = file_service_pb.AppendResponse()
      request.set_filename(self._filename)
      request.set_data(data)
      if sequence_key:
        request.set_sequence_key(sequence_key)
      self._make_rpc_call_with_retry('Append', request, response)
    else:
      raise UnsupportedContentTypeError(
          'Unsupported content type: %s' % self._content_type)

  def tell(self):
    """Return file's current position.

    Is valid only when file is opened for read.
    """
    self._verify_read_mode()
    return self._offset

  def seek(self, offset, whence=os.SEEK_SET):
    """Set the file's current position.

    Args:
      offset: seek offset as number.
      whence: seek mode. Supported modes are os.SEEK_SET (absolute seek),
        and os.SEEK_CUR (seek relative to the current position) and os.SEEK_END
        (seek relative to the end, offset should be negative).
    """
    self._verify_read_mode()
    if whence == os.SEEK_SET:
      self._offset = offset
    elif whence == os.SEEK_CUR:
      self._offset += offset
    elif whence == os.SEEK_END:
      file_stat = self.stat()
      self._offset = file_stat.st_size + offset
    else:
      raise InvalidArgumentError('Whence mode %d is not supported', whence)

  def read(self, size=None):
    """Read data from RAW file.

    Args:
      size: Number of bytes to read as integer. Actual number of bytes
        read might be less than specified, but it's never 0 unless current
        offset is at the end of the file. If it is None, then file is read
        until the end.

    Returns:
      A string with data read.
    """
    self._verify_read_mode()
    if self._content_type != RAW:
      raise UnsupportedContentTypeError(
          'Unsupported content type: %s' % self._content_type)

    buf = StringIO.StringIO()
    original_offset = self._offset

    try:
      if size is None:
        size = sys.maxint

      while size > 0:
        request = file_service_pb.ReadRequest()
        response = file_service_pb.ReadResponse()
        request.set_filename(self._filename)
        request.set_pos(self._offset)
        request.set_max_bytes(min(READ_BLOCK_SIZE, size))
        self._make_rpc_call_with_retry('Read', request, response)
        chunk = response.data()
        self._offset += len(chunk)
        if len(chunk) == 0:
          break
        buf.write(chunk)
        size -= len(chunk)

      return buf.getvalue()
    except:
      self._offset = original_offset
      raise
    finally:
      buf.close()

  def _verify_read_mode(self):
    if self._mode not in ('r', 'rb'):
      raise WrongOpenModeError('File is opened for write.')

  def _open(self):
    request = file_service_pb.OpenRequest()
    response = file_service_pb.OpenResponse()

    request.set_filename(self._filename)
    request.set_exclusive_lock(self._exclusive_lock)
    request.set_content_type(self._content_type)

    if self._mode in ('a', 'ab'):
      request.set_open_mode(file_service_pb.OpenRequest.APPEND)
    elif self._mode in ('r', 'rb'):
      request.set_open_mode(file_service_pb.OpenRequest.READ)
    else:
      raise UnsupportedOpenModeError('Unsupported open mode: %s', self._mode)

    self._make_rpc_call_with_retry('Open', request, response)

  def _make_rpc_call_with_retry(self, method, request, response):
    try:
      _make_call(method, request, response)
    except (ApiTemporaryUnavailableError, FileTemporaryUnavailableError):

      if method == 'Open':
        _make_call(method, request, response)
        return
      if self._exclusive_lock:

        raise

      self._open()
      _make_call(method, request, response)

  def stat(self):
    """Get status of a finalized file.

    Returns:
      a _FileStat object similar to that returned by python's os.stat(path).

    Throws:
      FinalizationError if file is not finalized.
    """
    self._verify_read_mode()

    request = file_service_pb.StatRequest()
    response = file_service_pb.StatResponse()
    request.set_filename(self._filename)

    _make_call('Stat', request, response)

    if response.stat_size() == 0:
      raise ExistenceError("File %s not found." % self._filename)

    if response.stat_size() > 1:
      raise ValueError(
          "Requested stat for one file. Got more than one response.")

    file_stat_pb = response.stat(0)
    file_stat = _FileStat()
    file_stat.filename = file_stat_pb.filename()
    file_stat.finalized = file_stat_pb.finalized()
    file_stat.st_size = file_stat_pb.length()
    file_stat.st_mtime = file_stat_pb.mtime()
    file_stat.st_ctime = file_stat_pb.ctime()

    return file_stat


def open(filename,
         mode='r',
         content_type=RAW,
         exclusive_lock=False,
         buffering=0):
  """Open a file.

  Args:
    filename: A name of the file as string.
    mode: File open mode. Either 'a' or 'r'.
    content_type: File's content type. Value from FileContentType.ContentType
      enum.
    exclusive_lock: If file should be exclusively locked. All other exclusive
      lock attempts will file until file is correctly closed.
    buffering: optional argument similar to the one in Python's open.
      It specifies the file's desired buffer size: 0 means unbuffered, positive
      value means use a buffer of that size, any negative value means the
      default size. Only read buffering is supported.

  Returns:
    File object.

  Raises:
    InvalidArgumentError: Raised when given illegal argument value or type.
  """
  if not filename:
    raise InvalidArgumentError('Filename is empty')
  if not isinstance(filename, basestring):
    raise InvalidArgumentError('Filename should be a string but is %s (%s)' %
                               (filename.__class__, filename))
  if content_type != RAW:
    raise InvalidArgumentError('Invalid content type')
  if not (isinstance(buffering, int) or isinstance(buffering, long)):
    raise InvalidArgumentError('buffering should be an int but is %s'
                               % buffering)

  if mode == 'r' or mode == 'rb':
    if buffering > 0:
      return BufferedFile(filename, buffering)
    elif buffering < 0:
      return BufferedFile(filename, _DEFAULT_BUFFER_SIZE)

  return _File(filename,
               mode=mode,
               content_type=content_type,
               exclusive_lock=exclusive_lock)


def listdir(path, **kwargs):
  """Return a sorted list of filenames (matching a pattern) in the given path.

  Only Google Cloud Storage paths are supported in current implementation.

  Args:
    path: a Google Cloud Storage path of "/gs/bucketname" form.
    kwargs: other keyword arguments to be relayed to Google Cloud Storage.
      This can be used to select certain files with names matching a pattern.
      See google.appengine.api.files.gs.listdir for details.

  Returns:
    a list containing filenames (matching a pattern) from the given path.
    Sorted by Python String.
  """

  from google.appengine.api.files import gs

  if not isinstance(path, basestring):
    raise InvalidArgumentError('path should be a string, but is %s(%r)' %
                               (path.__class__.__name__, path))

  if path.startswith(gs._GS_PREFIX):
    return gs.listdir(path, kwargs)
  else:
    raise InvalidFileNameError('Unsupported path: %s' % path)


def finalize(filename, content_type=RAW):
  """Finalize a file.

  Args:
    filename: File name as string.
    content_type: File's content type. Value from FileContentType.ContentType
      enum.
  """
  if not filename:
    raise InvalidArgumentError('Filename is empty')
  if not isinstance(filename, basestring):
    raise InvalidArgumentError('Filename should be a string')
  if content_type != RAW:
    raise InvalidArgumentError('Invalid content type')

  try:
    f = open(filename, 'a', exclusive_lock=True, content_type=content_type)
    f.close(finalize=True)
  except FinalizationError:

    pass


class _FileStat(object):
  """_FileStat contains file attributes.

  Attributes:
    filename: the uploaded filename of the file;
    finalized: whether the file is finalized. This is always true by now;
    st_size: number of bytes of the file;
    st_ctime: creation time;
    st_mtime: modification time.
  """
  def __init__(self):
    self.filename = None
    self.finalized = True
    self.st_size = None
    self.st_ctime = None
    self.st_mtime = None


def stat(filename):
  """Get status of a finalized file given it's full path filename.

  Returns:
    a _FileStat object similar to that returned by python's os.stat(path).

  Throws:
    FinalizationError if file is not finalized.
  """
  if not filename:
    raise InvalidArgumentError('Filename is empty')
  if not isinstance(filename, basestring):
    raise InvalidArgumentError('Filename should be a string')

  with open(filename, 'r') as f:
    return f.stat()


def _create(filesystem, content_type=RAW, filename=None, params=None):
  """Create a file.

  Args:
    filesystem: File system to create a file at as string.
    content_type: File content type.
    filename: Requested file name as string. Some file system require this
      to be filled in, some require it to be None.
    params: {string: string} dict of file parameters. Each filesystem
      interprets them differently.
  """
  if not filesystem:
    raise InvalidArgumentError('Filesystem is empty')
  if not isinstance(filesystem, basestring):
    raise InvalidArgumentError('Filesystem should be a string')
  if content_type != RAW:
    raise InvalidArgumentError('Invalid content type')

  request = file_service_pb.CreateRequest()
  response = file_service_pb.CreateResponse()

  request.set_filesystem(filesystem)
  request.set_content_type(content_type)

  if filename:
    if not isinstance(filename, basestring):
      raise InvalidArgumentError('Filename should be a string')
    request.set_filename(filename)

  if params:
    if not isinstance(params, dict):
      raise InvalidArgumentError('Parameters should be a dictionary')
    for k,v in params.items():
      param = request.add_parameters()
      param.set_name(k)
      param.set_value(v)

  _make_call('Create', request, response)
  return response.filename()


def __checkIsFinalizedName(filename):
  """Check if a filename is finalized.

  A filename is finalized when it has creation handle prefix, which is the same
  for both blobstore and gs files.

  Args:
    filename: a gs or blobstore filename that starts with '/gs/' or
      '/blobstore/'

  Raises:
    InvalidFileNameError: raised when filename is finalized.
  """
  if filename.split('/')[2].startswith(_CREATION_HANDLE_PREFIX):
    raise InvalidFileNameError('File %s should have finalized filename' %
                               filename)


def delete(*filenames):
  """Permanently delete files.

  Delete on non-finalized/non-existent files is a no-op.

  Args:
    filenames: finalized file names as strings. filename should has format
      "/gs/bucket/filename" or "/blobstore/blobkey".

  Raises:
    InvalidFileNameError: Raised when any filename is not of valid format or
      not a finalized name.
    IOError: Raised if any problem occurs contacting the backend system.
  """

  from google.appengine.api.files import blobstore as files_blobstore
  from google.appengine.api.files import gs
  from google.appengine.ext import blobstore

  blobkeys = []

  for filename in filenames:
    if not isinstance(filename, basestring):
      raise InvalidArgumentError('Filename should be a string, but is %s(%r)' %
                                 (filename.__class__.__name__, filename))
    if filename.startswith(files_blobstore._BLOBSTORE_DIRECTORY):
      __checkIsFinalizedName(filename)
      blobkey = files_blobstore.get_blob_key(filename)
      if blobkey:
        blobkeys.append(blobkey)
    elif filename.startswith(gs._GS_PREFIX):

      __checkIsFinalizedName(filename)
      blobkeys.append(blobstore.create_gs_key(filename))
    else:
      raise InvalidFileNameError('Filename should start with /%s or /%s' %
                                 (files_blobstore._BLOBSTORE_DIRECTORY,
                                 gs._GS_PREFIX))

  try:
    blobstore.delete(blobkeys)
  except Exception, e:
    raise IOError('Blobstore failure.', e)


def _get_capabilities():
  """Get files API capabilities.

  Returns:
    An instance of file_service_pb.GetCapabilitiesResponse.
  """
  request = file_service_pb.GetCapabilitiesRequest()
  response = file_service_pb.GetCapabilitiesResponse()

  _make_call('GetCapabilities', request, response)
  return response


class BufferedFile(object):
  """BufferedFile is a file-like object reading underlying file in chunks."""

  def __init__(self, filename, buffer_size=_DEFAULT_BUFFER_SIZE):
    """Constructor.

    Args:
      filename: the name of the file to read as string.
      buffer_size: buffer read size to use as int.
    """
    self._filename = filename
    self._position = 0
    self._buffer = ''
    self._buffer_pos = 0
    self._buffer_size = buffer_size
    self._eof = False

  def __enter__(self):
    return self

  def __exit__(self, atype, value, traceback):
    self.close()

  def close(self):
    self._buffer = ''
    self._eof = True
    self._buffer_pos = 0

  def tell(self):
    """Return file's current position."""
    return self._position

  def read(self, size=None):
    """Read data from RAW file.

    Args:
      size: Number of bytes to read as integer. Actual number of bytes
        read is always equal to size unless end if file was reached.

    Returns:
      A string with data read.
    """
    if size is None:
      size = sys.maxint
    data_list = []
    while True:
      result = self.__readBuffer(size)
      data_list.append(result)
      size -= len(result)
      if size == 0 or self._eof:
        return ''.join(data_list)
      self.__refillBuffer()

  def readline(self, size=-1):
    """Read one line delimited by '\n' from the file.

    A trailing newline character is kept in the string. It may be absent when a
    file ends with an incomplete line. If the size argument is non-negative,
    it specifies the maximum string size (counting the newline) to return. An
    empty string is returned only when EOF is encountered immediately.

    Args:
      size: Maximum number of bytes to read. If not specified, readline stops
        only on '\n' or EOF.

    Returns:
      The data read as a string.
    """
    data_list = []

    while True:

      if size < 0:
        end_pos = len(self._buffer)
      else:
        end_pos = self._buffer_pos + size
      newline_pos = self._buffer.find('\n', self._buffer_pos, end_pos)

      if newline_pos != -1:

        data_list.append(self.__readBuffer(newline_pos + 1 - self._buffer_pos))
        return ''.join(data_list)
      else:
        result = self.__readBuffer(size)
        data_list.append(result)
        size -= len(result)
        if size == 0 or self._eof:
          return ''.join(data_list)
        self.__refillBuffer()

  def __readBuffer(self, size):
    """Read chars from self._buffer.

    Args:
      size: number of chars to read. Read the entire buffer if negative.

    Returns:
      chars read in string.
    """
    if size < 0:
      size = len(self._buffer) - self._buffer_pos
    result = self._buffer[self._buffer_pos:self._buffer_pos+size]

    self._position += len(result)

    self._buffer_pos += len(result)
    return result

  def __refillBuffer(self):
    """Refill _buffer with another read from source."""
    with open(self._filename, 'r') as f:
      f.seek(self._position)
      data = f.read(self._buffer_size)
    self._eof = len(data) < self._buffer_size
    self._buffer = data
    self._buffer_pos = 0

  def seek(self, offset, whence=os.SEEK_SET):
    """Set the file's current position.

    Args:
      offset: seek offset as number.
      whence: seek mode. Supported modes are os.SEEK_SET (absolute seek),
        os.SEEK_CUR (seek relative to the current position), and os.SEEK_END
        (seek relative to the end, offset should be negative).
    """
    if whence == os.SEEK_SET:
      self._position = offset
    elif whence == os.SEEK_CUR:
      self._position += offset
    elif whence == os.SEEK_END:
      file_stat = stat(self._filename)
      self._position = file_stat.st_size + offset
    else:
      raise InvalidArgumentError('Whence mode %d is not supported', whence)
    self._buffer = ''
    self._buffer_pos = 0
    self._eof = False


def _default_gs_bucket_name():
  """Return the default Google Storage bucket name for the application.

  Returns:
    A string that is the default bucket name for the application.
  """
  request = file_service_pb.GetDefaultGsBucketNameRequest()
  response = file_service_pb.GetDefaultGsBucketNameResponse()

  _make_call('GetDefaultGsBucketName', request, response)

  return response.default_gs_bucket_name()
