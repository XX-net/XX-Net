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














"""Imports data over HTTP.

Usage:
  %(arg0)s [flags]

    --debug                 Show debugging information. (Optional)
    --application=<string>  Application ID of endpoint (Optional for
                            *.appspot.com)
    --auth_domain=<domain>  The auth domain to use for logging in and for
                            UserProperties. (Default: gmail.com)
    --bandwidth_limit=<int> The maximum number of bytes per second for the
                            aggregate transfer of data to/from the server.
                            Bursts may exceed this, but overall transfer rate is
                            restricted to this rate. (Default: 250000)
    --batch_size=<int>      Number of Entity objects to include in each request
                            to/from the URL endpoint. The more data per
                            row/Entity, the smaller the batch size should be.
                            (Default: downloads 100, uploads 10)
    --config_file=<path>    File containing Model and Loader definitions or
                            bulkloader.yaml transforms. (Required unless --dump,
                            --restore, or --create_config are used.)
    --create_config         Write a bulkloader.yaml configuration file to
                            --filename based on the server side datastore state.
    --db_filename=<path>    Specific progress database to write to, or to
                            resume from. If not supplied, then a new database
                            will be started, named:
                            bulkloader-progress-TIMESTAMP.
                            The special filename "skip" may be used to simply
                            skip reading/writing any progress information.
    --download              Export entities to a file.
    --dry_run               Do not execute any remote_api calls.
    --dump                  Use zero-configuration dump format.
    --email=<string>        The username to use. Will prompt if omitted.
    --exporter_opts=<string>
                            A string to pass to the Exporter.initialize method.
    --filename=<path>       Path to the file to import/export. (Required when
                            importing or exporting, not mapping.)
    --has_header            Skip the first row of the input.
    --http_limit=<int>      The maximum numer of HTTP requests per second to
                            send to the server. (Default: 8)
    --kind=<string>         Name of the Entity object kind to put in the
                            datastore. (Required)
    --loader_opts=<string>  A string to pass to the Loader.initialize method.
    --log_file=<path>       File to write bulkloader logs.  If not supplied
                            then a new log file will be created, named:
                            bulkloader-log-TIMESTAMP.
    --map                   Map an action across datastore entities.
    --mapper_opts=<string>  A string to pass to the Mapper.Initialize method.
    --num_threads=<int>     Number of threads to use for uploading/downloading
                            entities (Default: 10)
    --passin                Read the login password from stdin.
    --restore               Restore from zero-configuration dump format.
    --result_db_filename=<path>
                            Result database to write to for downloads.
    --rps_limit=<int>       The maximum number of records per second to
                            transfer to/from the server. (Default: 20)
    --url=<string>          URL endpoint to post to for importing/exporting
                            data.  (Required)
    --namespace=<string>    Use specified namespace instead of the default one
                            for all datastore operations.

The exit status will be 0 on success, non-zero on import failure.

Works with the remote_api mix-in library for google.appengine.ext.remote_api.
Please look there for documentation about how to setup the server side.

Example:

%(arg0)s --url=http://app.appspot.com/remote_api --kind=Model \
 --filename=data.csv --config_file=loader_config.py

"""








import csv
import errno
import getopt
import getpass
import imp
import logging
import os
import Queue
import re
import shutil
import signal
import StringIO
import sys
import threading
import time
import traceback
import urllib2
import urlparse

from google.appengine.datastore import entity_pb

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore
from google.appengine.api import datastore_errors
from google.appengine.api.namespace_manager import namespace_manager
from google.appengine.datastore import datastore_pb
from google.appengine.ext import db
from google.appengine.ext import key_range as key_range_module
from google.appengine.ext.bulkload import bulkloader_config
from google.appengine.ext.db import polymodel
from google.appengine.ext.db import stats
from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.ext.remote_api import throttle as remote_api_throttle
from google.appengine.runtime import apiproxy_errors
from google.appengine.tools import adaptive_thread_pool
from google.appengine.tools import appengine_rpc
from google.appengine.tools.requeue import ReQueue





try:
  import sqlite3
except ImportError:
  pass

logger = logging.getLogger('google.appengine.tools.bulkloader')

KeyRange = key_range_module.KeyRange


DEFAULT_THREAD_COUNT = 10


DEFAULT_BATCH_SIZE = 10


DEFAULT_DOWNLOAD_BATCH_SIZE = 100


DEFAULT_QUEUE_SIZE = DEFAULT_THREAD_COUNT * 10


_THREAD_SHOULD_EXIT = '_THREAD_SHOULD_EXIT'


STATE_READ = 0
STATE_SENDING = 1
STATE_SENT = 2
STATE_NOT_SENT = 3



STATE_GETTING = 1
STATE_GOT = 2
STATE_ERROR = 3



DATA_CONSUMED_TO_HERE = 'DATA_CONSUMED_TO_HERE'




INITIAL_BACKOFF = 1.0


BACKOFF_FACTOR = 2.0






DEFAULT_BANDWIDTH_LIMIT = 250000


DEFAULT_RPS_LIMIT = 20


DEFAULT_REQUEST_LIMIT = 8








MAXIMUM_INCREASE_DURATION = 5.0
MAXIMUM_HOLD_DURATION = 12.0


def ImportStateMessage(state):
  """Converts a numeric state identifier to a status message."""
  return ({
      STATE_READ: 'Batch read from file.',
      STATE_SENDING: 'Sending batch to server.',
      STATE_SENT: 'Batch successfully sent.',
      STATE_NOT_SENT: 'Error while sending batch.'
  }[state])


def ExportStateMessage(state):
  """Converts a numeric state identifier to a status message."""
  return ({
      STATE_READ: 'Batch read from file.',
      STATE_GETTING: 'Fetching batch from server',
      STATE_GOT: 'Batch successfully fetched.',
      STATE_ERROR: 'Error while fetching batch'
  }[state])


def MapStateMessage(state):
  """Converts a numeric state identifier to a status message."""
  return ({
      STATE_READ: 'Batch read from file.',
      STATE_GETTING: 'Querying for batch from server',
      STATE_GOT: 'Batch successfully fetched.',
      STATE_ERROR: 'Error while fetching or mapping.'
  }[state])


def ExportStateName(state):
  """Converts a numeric state identifier to a string."""
  return ({
      STATE_READ: 'READ',
      STATE_GETTING: 'GETTING',
      STATE_GOT: 'GOT',
      STATE_ERROR: 'NOT_GOT'
  }[state])


def ImportStateName(state):
  """Converts a numeric state identifier to a string."""
  return ({
      STATE_READ: 'READ',
      STATE_GETTING: 'SENDING',
      STATE_GOT: 'SENT',
      STATE_NOT_SENT: 'NOT_SENT'
  }[state])


class Error(Exception):
  """Base-class for exceptions in this module."""


class MissingPropertyError(Error):
  """An expected field is missing from an entity, and no default was given."""


class FatalServerError(Error):
  """An unrecoverable error occurred while posting data to the server."""


class ResumeError(Error):
  """Error while trying to resume a partial upload."""


class ConfigurationError(Error):
  """Error in configuration options."""


class AuthenticationError(Error):
  """Error while trying to authenticate with the server."""


class FileNotFoundError(Error):
  """A filename passed in by the user refers to a non-existent input file."""


class FileNotReadableError(Error):
  """A filename passed in by the user refers to a non-readable input file."""


class FileExistsError(Error):
  """A filename passed in by the user refers to an existing output file."""


class FileNotWritableError(Error):
  """A filename passed in by the user refers to a non-writable output file."""


class BadStateError(Error):
  """A work item in an unexpected state was encountered."""


class KeyRangeError(Error):
  """An error during construction of a KeyRangeItem."""


class KindStatError(Error):
  """Unable to find kind stats for an all-kinds download."""


class FieldSizeLimitError(Error):
  """The csv module tried to read a field larger than the size limit."""

  def __init__(self, limit):
    self.message = """
A field in your CSV input file has exceeded the current limit of %d.

You can raise this limit by adding the following lines to your config file:

import csv
csv.field_size_limit(new_limit)

where new_limit is number larger than the size in bytes of the largest
field in your CSV.
""" % limit
    Error.__init__(self, self.message)


class NameClashError(Error):
  """A name clash occurred while trying to alias old method names."""

  def __init__(self, old_name, new_name, klass):
    Error.__init__(self, old_name, new_name, klass)
    self.old_name = old_name
    self.new_name = new_name
    self.klass = klass


def GetCSVGeneratorFactory(kind, csv_filename, batch_size, csv_has_header,
                           openfile=open, create_csv_reader=csv.reader):
  """Return a factory that creates a CSV-based UploadWorkItem generator.

  Args:
    kind: The kind of the entities being uploaded.
    csv_filename: File on disk containing CSV data.
    batch_size: Maximum number of CSV rows to stash into an UploadWorkItem.
    csv_has_header: Whether to skip the first row of the CSV.
    openfile: Used for dependency injection.
    create_csv_reader: Used for dependency injection.

  Returns:
    A callable (accepting the Progress Queue and Progress Generators
    as input) which creates the UploadWorkItem generator.
  """
  loader = Loader.RegisteredLoader(kind)
  loader._Loader__openfile = openfile
  loader._Loader__create_csv_reader = create_csv_reader
  record_generator = loader.generate_records(csv_filename)

  def CreateGenerator(request_manager, progress_queue, progress_generator,
                      unused_kinds):
    """Initialize a UploadWorkItem generator.

    Args:
      request_manager: A RequestManager instance.
      progress_queue: A ProgressQueue instance to send progress information.
      progress_generator: A generator of progress information or None.
      unused_kinds: The kinds being generated (ignored in this method).

    Returns:
      An UploadWorkItemGenerator instance.
    """
    return UploadWorkItemGenerator(request_manager,
                                   progress_queue,
                                   progress_generator,
                                   record_generator,
                                   csv_has_header,
                                   batch_size)

  return CreateGenerator


class UploadWorkItemGenerator(object):
  """Reads rows from a row generator and generates UploadWorkItems."""

  def __init__(self,
               request_manager,
               progress_queue,
               progress_generator,
               record_generator,
               skip_first,
               batch_size):
    """Initialize a WorkItemGenerator.

    Args:
      request_manager: A RequestManager instance with which to associate
        WorkItems.
      progress_queue: A progress queue with which to associate WorkItems.
      progress_generator: A generator of progress information.
      record_generator: A generator of data records.
      skip_first: Whether to skip the first data record.
      batch_size: The number of data records per WorkItem.
    """
    self.request_manager = request_manager
    self.progress_queue = progress_queue
    self.progress_generator = progress_generator
    self.reader = record_generator
    self.skip_first = skip_first
    self.batch_size = batch_size
    self.line_number = 1
    self.column_count = None
    self.read_rows = []
    self.row_count = 0
    self.xfer_count = 0

  def _AdvanceTo(self, line):
    """Advance the reader to the given line.

    Args:
      line: A line number to advance to.
    """
    while self.line_number < line:
      self.reader.next()
      self.line_number += 1
      self.row_count += 1
      self.xfer_count += 1

  def _ReadRows(self, key_start, key_end):
    """Attempts to read and encode rows [key_start, key_end].

    The encoded rows are stored in self.read_rows.

    Args:
      key_start: The starting line number.
      key_end: The ending line number.

    Raises:
      StopIteration: if the reader runs out of rows
      ResumeError: if there are an inconsistent number of columns.
    """
    assert self.line_number == key_start



    self.read_rows = []
    while self.line_number <= key_end:
      row = self.reader.next()
      self.row_count += 1
      if self.column_count is None:
        self.column_count = len(row)
      self.read_rows.append((self.line_number, row))
      self.line_number += 1

  def _MakeItem(self, key_start, key_end, rows, progress_key=None):
    """Makes a UploadWorkItem containing the given rows, with the given keys.

    Args:
      key_start: The start key for the UploadWorkItem.
      key_end: The end key for the UploadWorkItem.
      rows: A list of the rows for the UploadWorkItem.
      progress_key: The progress key for the UploadWorkItem

    Returns:
      An UploadWorkItem instance for the given batch.
    """
    assert rows

    item = UploadWorkItem(self.request_manager, self.progress_queue, rows,
                          key_start, key_end, progress_key=progress_key)

    return item

  def Batches(self):
    """Reads from the record_generator and generates UploadWorkItems.

    Yields:
      Instances of class UploadWorkItem

    Raises:
      ResumeError: If the progress database and data file indicate a different
        number of rows.
    """
    if self.skip_first:


      logger.info('Skipping header line.')
      try:
        self.reader.next()
      except StopIteration:


        return

    exhausted = False

    self.line_number = 1
    self.column_count = None

    logger.info('Starting import; maximum %d entities per post',
                self.batch_size)

    state = None


    if self.progress_generator:
      for progress_key, state, kind, key_start, key_end in (
          self.progress_generator):
        if key_start:
          try:
            self._AdvanceTo(key_start)
            self._ReadRows(key_start, key_end)
            yield self._MakeItem(key_start,
                                 key_end,
                                 self.read_rows,
                                 progress_key=progress_key)
          except StopIteration:


            logger.error('Mismatch between data file and progress database')
            raise ResumeError(
                'Mismatch between data file and progress database')
        elif state == DATA_CONSUMED_TO_HERE:
          try:
            self._AdvanceTo(key_end + 1)
          except StopIteration:


            state = None

    if self.progress_generator is None or state == DATA_CONSUMED_TO_HERE:


      while not exhausted:
        key_start = self.line_number
        key_end = self.line_number + self.batch_size - 1
        try:
          self._ReadRows(key_start, key_end)
        except StopIteration:
          exhausted = True


          key_end = self.line_number - 1
        if key_start <= key_end:
          yield self._MakeItem(key_start, key_end, self.read_rows)


class CSVGenerator(object):
  """Reads a CSV file and generates data records."""

  def __init__(self,
               csv_filename,
               openfile=open,
               create_csv_reader=csv.reader):
    """Initializes a CSV generator.

    Args:
      csv_filename: File on disk containing CSV data.
      openfile: Used for dependency injection of 'open'.
      create_csv_reader: Used for dependency injection of 'csv.reader'.
    """
    self.csv_filename = csv_filename
    self.openfile = openfile
    self.create_csv_reader = create_csv_reader

  def Records(self):
    """Reads the CSV data file and generates row records.

    Yields:
      Lists of strings

    Raises:
      ResumeError: If the progress database and data file indicate a different
        number of rows.
    """
    csv_file = self.openfile(self.csv_filename, 'rb')
    reader = self.create_csv_reader(csv_file, skipinitialspace=True)
    try:

      for record in reader:
        yield record
    except csv.Error, e:
      if e.args and e.args[0].startswith('field larger than field limit'):
        raise FieldSizeLimitError(csv.field_size_limit())
      else:
        raise


class KeyRangeItemGenerator(object):
  """Generates ranges of keys to download.

  Reads progress information from the progress database and creates
  KeyRangeItem objects corresponding to incompletely downloaded parts of an
  export.
  """

  def __init__(self, request_manager, kinds, progress_queue, progress_generator,
               key_range_item_factory):
    """Initialize the KeyRangeItemGenerator.

    Args:
      request_manager: A RequestManager instance.
      kinds: The kind of entities being transferred, or a list of kinds.
      progress_queue: A queue used for tracking progress information.
      progress_generator: A generator of prior progress information, or None
        if there is no prior status.
      key_range_item_factory: A factory to produce KeyRangeItems.
    """
    self.request_manager = request_manager
    if isinstance(kinds, basestring):
      self.kinds = [kinds]
    else:
      self.kinds = kinds
    self.row_count = 0
    self.xfer_count = 0
    self.progress_queue = progress_queue
    self.progress_generator = progress_generator
    self.key_range_item_factory = key_range_item_factory

  def Batches(self):
    """Iterate through saved progress information.

    Yields:
      KeyRangeItem instances corresponding to undownloaded key ranges.
    """
    if self.progress_generator is not None:
      for progress_key, state, kind, key_start, key_end in (
          self.progress_generator):
        if state is not None and state != STATE_GOT and key_start is not None:
          key_start = ParseKey(key_start)
          key_end = ParseKey(key_end)

          key_range = KeyRange(key_start=key_start,
                               key_end=key_end)

          result = self.key_range_item_factory(self.request_manager,
                                               self.progress_queue,
                                               kind,
                                               key_range,
                                               progress_key=progress_key,
                                               state=STATE_READ)
          yield result
    else:

      for kind in self.kinds:
        key_range = KeyRange()
        yield self.key_range_item_factory(self.request_manager,
                                          self.progress_queue,
                                          kind,
                                          key_range)


class DownloadResult(object):
  """Holds the result of an entity download."""

  def __init__(self, continued, direction, keys, entities):
    self.continued = continued
    self.direction = direction
    self.keys = keys
    self.entities = entities
    self.count = len(keys)
    assert self.count == len(entities)
    assert direction in (key_range_module.KeyRange.ASC,
                         key_range_module.KeyRange.DESC)
    if self.count > 0:
      if direction == key_range_module.KeyRange.ASC:
        self.key_start = keys[0]
        self.key_end = keys[-1]
      else:
        self.key_start = keys[-1]
        self.key_end = keys[0]

  def Entities(self):
    """Returns the list of entities for this result in key order."""
    if self.direction == key_range_module.KeyRange.ASC:
      return list(self.entities)
    else:
      result = list(self.entities)
      result.reverse()
      return result

  def __str__(self):
    return 'continued = %s\n%s' % (
        str(self.continued), '\n'.join(str(self.entities)))


class _WorkItem(adaptive_thread_pool.WorkItem):
  """Holds a description of a unit of upload or download work."""

  def __init__(self, progress_queue, key_start, key_end, state_namer,
               state=STATE_READ, progress_key=None):
    """Initialize the _WorkItem instance.

    Args:
      progress_queue: A queue used for tracking progress information.
      key_start: The start key of the work item.
      key_end: The end key of the work item.
      state_namer: Function to describe work item states.
      state: The initial state of the work item.
      progress_key: If this WorkItem represents state from a prior run,
        then this will be the key within the progress database.
    """
    adaptive_thread_pool.WorkItem.__init__(self,
                                           '[%s-%s]' % (key_start, key_end))
    self.progress_queue = progress_queue
    self.state_namer = state_namer
    self.state = state
    self.progress_key = progress_key
    self.progress_event = threading.Event()
    self.key_start = key_start
    self.key_end = key_end
    self.error = None
    self.traceback = None
    self.kind = None

  def _TransferItem(self, thread_pool):
    raise NotImplementedError()

  def SetError(self):
    """Sets the error and traceback information for this thread.

    This must be called from an exception handler.
    """
    if not self.error:
      exc_info = sys.exc_info()
      self.error = exc_info[1]
      self.traceback = exc_info[2]

  def PerformWork(self, thread_pool):
    """Perform the work of this work item and report the results.

    Args:
      thread_pool: An AdaptiveThreadPool instance.

    Returns:
      A tuple (status, instruction) of the work status and an instruction
      for the ThreadGate.
    """
    status = adaptive_thread_pool.WorkItem.FAILURE
    instruction = adaptive_thread_pool.ThreadGate.DECREASE


    try:
      self.MarkAsTransferring()



      try:
        transfer_time = self._TransferItem(thread_pool)
        if transfer_time is None:
          status = adaptive_thread_pool.WorkItem.RETRY
          instruction = adaptive_thread_pool.ThreadGate.HOLD
        else:
          logger.debug('[%s] %s Transferred %d entities in %0.1f seconds',
                       threading.currentThread().getName(), self, self.count,
                       transfer_time)
          sys.stdout.write('.')
          sys.stdout.flush()
          status = adaptive_thread_pool.WorkItem.SUCCESS
          if transfer_time <= MAXIMUM_INCREASE_DURATION:
            instruction = adaptive_thread_pool.ThreadGate.INCREASE
          elif transfer_time <= MAXIMUM_HOLD_DURATION:
            instruction = adaptive_thread_pool.ThreadGate.HOLD
      except (db.InternalError, db.NotSavedError, db.Timeout,
              db.TransactionFailedError,
              apiproxy_errors.OverQuotaError,
              apiproxy_errors.DeadlineExceededError,
              apiproxy_errors.ApplicationError), e:

        status = adaptive_thread_pool.WorkItem.RETRY
        logger.exception('Retrying on non-fatal datastore error: %s', e)
      except urllib2.HTTPError, e:
        http_status = e.code
        if http_status >= 500 and http_status < 600:

          status = adaptive_thread_pool.WorkItem.RETRY
          logger.exception('Retrying on non-fatal HTTP error: %d %s',
                           http_status, e.msg)
        else:
          self.SetError()
          status = adaptive_thread_pool.WorkItem.FAILURE
      except urllib2.URLError, e:
        if IsURLErrorFatal(e):
          self.SetError()
          status = adaptive_thread_pool.WorkItem.FAILURE
        else:
          status = adaptive_thread_pool.WorkItem.RETRY
          logger.exception('Retrying on non-fatal URL error: %s', e.reason)

    finally:
      if status == adaptive_thread_pool.WorkItem.SUCCESS:
        self.MarkAsTransferred()
      else:
        self.MarkAsError()

    return (status, instruction)

  def _AssertInState(self, *states):
    """Raises an Error if the state of this range is not in states."""
    if not self.state in states:
      raise BadStateError('%s:%s not in %s' %
                          (str(self),
                           self.state_namer(self.state),
                           map(self.state_namer, states)))

  def _AssertProgressKey(self):
    """Raises an Error if the progress key is None."""
    if self.progress_key is None:
      raise BadStateError('%s: Progress key is missing' % str(self))

  def MarkAsRead(self):
    """Mark this _WorkItem as read, updating the progress database."""
    self._AssertInState(STATE_READ)
    self._StateTransition(STATE_READ, blocking=True)

  def MarkAsTransferring(self):
    """Mark this _WorkItem as transferring, updating the progress database."""
    self._AssertInState(STATE_READ, STATE_ERROR)
    self._AssertProgressKey()
    self._StateTransition(STATE_GETTING, blocking=True)

  def MarkAsTransferred(self):
    """Mark this _WorkItem as transferred, updating the progress database."""
    raise NotImplementedError()

  def MarkAsError(self):
    """Mark this _WorkItem as failed, updating the progress database."""
    self._AssertInState(STATE_GETTING)
    self._AssertProgressKey()
    self._StateTransition(STATE_ERROR, blocking=True)

  def _StateTransition(self, new_state, blocking=False):
    """Transition the work item to a new state, storing progress information.

    Args:
      new_state: The state to transition to.
      blocking: Whether to block for the progress thread to acknowledge the
        transition.
    """

    assert not self.progress_event.isSet()


    self.state = new_state


    self.progress_queue.put(self)

    if blocking:



      self.progress_event.wait()


      self.progress_event.clear()







class UploadWorkItem(_WorkItem):
  """Holds a unit of uploading work.

  A UploadWorkItem represents a number of entities that need to be uploaded to
  Google App Engine. These entities are encoded in the "content" field of
  the UploadWorkItem, and will be POST'd as-is to the server.

  The entities are identified by a range of numeric keys, inclusively. In
  the case of a resumption of an upload, or a replay to correct errors,
  these keys must be able to identify the same set of entities.

  Note that keys specify a range. The entities do not have to sequentially
  fill the entire range, they must simply bound a range of valid keys.
  """

  def __init__(self, request_manager, progress_queue, rows, key_start, key_end,
               progress_key=None):
    """Initialize the UploadWorkItem instance.

    Args:
      request_manager: A RequestManager instance.
      progress_queue: A queue used for tracking progress information.
      rows: A list of pairs of a line number and a list of column values.
      key_start: The (numeric) starting key, inclusive.
      key_end: The (numeric) ending key, inclusive.
      progress_key: If this UploadWorkItem represents state from a prior run,
        then this will be the key within the progress database.
    """
    _WorkItem.__init__(self, progress_queue, key_start, key_end,
                       ImportStateName, state=STATE_READ,
                       progress_key=progress_key)


    assert isinstance(key_start, (int, long))
    assert isinstance(key_end, (int, long))
    assert key_start <= key_end

    self.request_manager = request_manager
    self.rows = rows
    self.content = None
    self.count = len(rows)

  def __str__(self):
    return '[%s-%s]' % (self.key_start, self.key_end)

  def _TransferItem(self, thread_pool, get_time=time.time):
    """Transfers the entities associated with an item.

    Args:
      thread_pool: An AdaptiveThreadPool instance.
      get_time: Used for dependency injection.
    """
    t = get_time()
    if not self.content:
      self.content = self.request_manager.EncodeContent(self.rows)
    try:
      self.request_manager.PostEntities(self.content)
    except:
      raise
    return get_time() - t

  def MarkAsTransferred(self):
    """Mark this UploadWorkItem as sucessfully-sent to the server."""

    self._AssertInState(STATE_SENDING)
    self._AssertProgressKey()

    self._StateTransition(STATE_SENT, blocking=False)


def GetImplementationClass(kind_or_class_key):
  """Returns the implementation class for a given kind or class key.

  Args:
    kind_or_class_key: A kind string or a tuple of kind strings.

  Return:
    A db.Model subclass for the given kind or class key.
  """
  if isinstance(kind_or_class_key, tuple):
    try:
      implementation_class = polymodel._class_map[kind_or_class_key]
    except KeyError:
      raise db.KindError('No implementation for class \'%s\'' %
                         kind_or_class_key)
  else:
    implementation_class = db.class_for_kind(kind_or_class_key)
  return implementation_class


def KeyLEQ(key1, key2):
  """Compare two keys for less-than-or-equal-to.

  All keys with numeric ids come before all keys with names. None represents
  an unbounded end-point so it is both greater and less than any other key.

  Args:
    key1: An int or datastore.Key instance.
    key2: An int or datastore.Key instance.

  Returns:
    True if key1 <= key2
  """
  if key1 is None or key2 is None:
    return True
  return key1 <= key2


class KeyRangeItem(_WorkItem):
  """Represents an item of work that scans over a key range.

  A KeyRangeItem object represents holds a KeyRange
  and has an associated state: STATE_READ, STATE_GETTING, STATE_GOT,
  and STATE_ERROR.

  - STATE_READ indicates the range ready to be downloaded by a worker thread.
  - STATE_GETTING indicates the range is currently being downloaded.
  - STATE_GOT indicates that the range was successfully downloaded
  - STATE_ERROR indicates that an error occurred during the last download
    attempt

  KeyRangeItems not in the STATE_GOT state are stored in the progress database.
  When a piece of KeyRangeItem work is downloaded, the download may cover only
  a portion of the range.  In this case, the old KeyRangeItem is removed from
  the progress database and ranges covering the undownloaded range are
  generated and stored as STATE_READ in the export progress database.
  """

  def __init__(self,
               request_manager,
               progress_queue,
               kind,
               key_range,
               progress_key=None,
               state=STATE_READ,
               first=False):
    """Initialize a KeyRangeItem object.

    Args:
      request_manager: A RequestManager instance.
      progress_queue: A queue used for tracking progress information.
      kind: The kind of entities for this range.
      key_range: A KeyRange instance for this work item.
      progress_key: The key for this range within the progress database.
      state: The initial state of this range.
      first: boolean, default False, whether this is the first WorkItem
        of its kind.
    """
    _WorkItem.__init__(self, progress_queue, key_range.key_start,
                       key_range.key_end, ExportStateName, state=state,
                       progress_key=progress_key)
    assert KeyLEQ(key_range.key_start, key_range.key_end), (
        '%s not less than %s' %
        (repr(key_range.key_start), repr(key_range.key_end)))
    self.request_manager = request_manager
    self.kind = kind
    self.key_range = key_range
    self.download_result = None
    self.count = 0
    self.key_start = key_range.key_start
    self.key_end = key_range.key_end
    self.first = first

  def __str__(self):
    return '%s-%s' % (self.kind, self.key_range)

  def __repr__(self):
    return self.__str__()

  def MarkAsTransferred(self):
    """Mark this KeyRangeItem as transferred, updating the progress database."""


    pass

  def Process(self, download_result, thread_pool, batch_size,
              new_state=STATE_GOT):
    """Mark this KeyRangeItem as success, updating the progress database.

    Process will split this KeyRangeItem based on the content of
    download_result and adds the unfinished ranges to the work queue.

    Args:
      download_result: A DownloadResult instance.
      thread_pool: An AdaptiveThreadPool instance.
      batch_size: The number of entities to transfer per request.
      new_state: The state to transition the completed range to.
    """
    self._AssertInState(STATE_GETTING)
    self._AssertProgressKey()

    self.download_result = download_result
    self.count = len(download_result.keys)
    if download_result.continued:
      self._FinishedRange()._StateTransition(new_state, blocking=True)
      self._AddUnfinishedRanges(thread_pool, batch_size)
    else:
      self._StateTransition(new_state, blocking=True)

  def _FinishedRange(self):
    """Returns the range completed by the download_result.

    Returns:
      A KeyRangeItem representing a completed range.
    """
    assert self.download_result is not None

    if self.key_range.direction == key_range_module.KeyRange.ASC:
      key_start = self.key_range.key_start
      if self.download_result.continued:
        key_end = self.download_result.key_end
      else:
        key_end = self.key_range.key_end
    else:
      key_end = self.key_range.key_end
      if self.download_result.continued:
        key_start = self.download_result.key_start
      else:
        key_start = self.key_range.key_start

    key_range = KeyRange(key_start=key_start,
                         key_end=key_end,
                         direction=self.key_range.direction)

    result = self.__class__(self.request_manager,
                            self.progress_queue,
                            self.kind,
                            key_range,
                            progress_key=self.progress_key,
                            state=self.state)

    result.download_result = self.download_result
    result.count = self.count
    return result

  def _SplitAndAddRanges(self, thread_pool, batch_size):
    """Split the key range [key_start, key_end] into a list of ranges."""

    if self.download_result.direction == key_range_module.KeyRange.ASC:
      key_range = KeyRange(
          key_start=self.download_result.key_end,
          key_end=self.key_range.key_end,
          include_start=False)
    else:
      key_range = KeyRange(
          key_start=self.key_range.key_start,
          key_end=self.download_result.key_start,
          include_end=False)

    if thread_pool.QueuedItemCount() > 2 * thread_pool.num_threads():

      ranges = [key_range]
    else:

      ranges = key_range.split_range(batch_size=batch_size)

    for key_range in ranges:
      key_range_item = self.__class__(self.request_manager,
                                      self.progress_queue,
                                      self.kind,
                                      key_range)
      key_range_item.MarkAsRead()
      thread_pool.SubmitItem(key_range_item, block=True)

  def _AddUnfinishedRanges(self, thread_pool, batch_size):
    """Adds incomplete KeyRanges to the thread_pool.

    Args:
      thread_pool: An AdaptiveThreadPool instance.
      batch_size: The number of entities to transfer per request.

    Returns:
      A list of KeyRanges representing incomplete datastore key ranges.

    Raises:
      KeyRangeError: if this key range has already been completely transferred.
    """
    assert self.download_result is not None
    if self.download_result.continued:
      self._SplitAndAddRanges(thread_pool, batch_size)
    else:
      raise KeyRangeError('No unfinished part of key range.')


class DownloadItem(KeyRangeItem):
  """A KeyRangeItem for downloading key ranges."""

  def _TransferItem(self, thread_pool, get_time=time.time):
    """Transfers the entities associated with an item."""
    t = get_time()
    download_result = self.request_manager.GetEntities(
        self, retry_parallel=self.first)
    transfer_time = get_time() - t
    self.Process(download_result, thread_pool,
                 self.request_manager.batch_size)
    return transfer_time


class MapperItem(KeyRangeItem):
  """A KeyRangeItem for mapping over key ranges."""

  def _TransferItem(self, thread_pool, get_time=time.time):
    t = get_time()
    mapper = self.request_manager.GetMapper(self.kind)

    download_result = self.request_manager.GetEntities(
        self, keys_only=mapper.map_over_keys_only(), retry_parallel=self.first)
    transfer_time = get_time() - t
    try:
      mapper.batch_apply(download_result.Entities())
    except MapperRetry:
      return None
    self.Process(download_result, thread_pool,
                 self.request_manager.batch_size)
    return transfer_time


def IncrementId(high_id_key):
  """Increment unique id counter associated with high_id_key beyond high_id_key.

  Args:
    high_id_key: A key with a full path to the desired kind and id
        value to which to increment the unique id counter beyond.
  """
  unused_start, end = datastore.AllocateIds(high_id_key, max=high_id_key.id())
  assert end >= high_id_key.id()


def _AuthFunction(host, email, passin, raw_input_fn, password_input_fn):
  """Internal method shared between RequestManager and _GetRemoteAppId.

  Args:
    host: Hostname to present to the user.
    email: Existing email address to use; if none, will prompt the user.
    passin: Value of the --passin command line flag. If true, will get the
      password using raw_input_fn insetad of password_input_fn.
    raw_input_fn: Method to get a string, typically raw_input.
    password_input_fn: Method to get a string, typically getpass.

  Returns:
    Pair, (email, password).
  """
  if not email:
    print 'Please enter login credentials for %s' % host
    email = raw_input_fn('Email: ')

  if email:
    password_prompt = 'Password for %s: ' % email
    if passin:
      password = raw_input_fn(password_prompt)
    else:
      password = password_input_fn(password_prompt)
  else:
    password = None

  return email, password


class RequestManager(object):
  """A class which wraps a connection to the server."""

  def __init__(self,
               app_id,
               host_port,
               url_path,
               kind,
               throttle,
               batch_size,
               secure,
               email,
               passin,
               dry_run=False,
               server=None,
               throttle_class=None):
    """Initialize a RequestManager object.

    Args:
      app_id: String containing the application id for requests.
      host_port: String containing the "host:port" pair; the port is optional.
      url_path: partial URL (path) to post entity data to.
      kind: Kind of the Entity records being posted.
      throttle: A Throttle instance.
      batch_size: The number of entities to transfer per request.
      secure: Use SSL when communicating with server.
      email: If not none, the username to log in with.
      passin: If True, the password will be read from standard in.
      server: An existing AbstractRpcServer to reuse.
      throttle_class: A class to use instead of the default
        ThrottledHttpRpcServer.
    """
    self.app_id = app_id
    self.host_port = host_port
    self.host = host_port.split(':')[0]
    if url_path and url_path[0] != '/':
      url_path = '/' + url_path
    self.url_path = url_path
    self.kind = kind
    self.throttle = throttle
    self.batch_size = batch_size
    self.secure = secure
    self.authenticated = False
    self.auth_called = False
    self.parallel_download = True
    self.email = email
    self.passin = passin
    self.mapper = None
    self.dry_run = dry_run

    if self.dry_run:
      logger.info('Running in dry run mode, skipping remote_api setup')
      return

    logger.debug('Configuring remote_api. url_path = %s, '
                 'servername = %s' % (url_path, host_port))

    throttled_rpc_server_factory = (
        remote_api_throttle.ThrottledHttpRpcServerFactory(
            self.throttle, throttle_class=throttle_class))

    if server:
      remote_api_stub.ConfigureRemoteApiFromServer(server, url_path, app_id)
    else:
      remote_api_stub.ConfigureRemoteApi(
          app_id,
          url_path,
          self.AuthFunction,
          servername=host_port,
          rpc_server_factory=throttled_rpc_server_factory,
          secure=self.secure)

    remote_api_throttle.ThrottleRemoteDatastore(self.throttle)
    logger.debug('Bulkloader using app_id: %s', os.environ['APPLICATION_ID'])

  def Authenticate(self):
    """Invoke authentication if necessary."""
    logger.info('Connecting to %s%s', self.host_port, self.url_path)
    if self.dry_run:
      self.authenticated = True
      return

    remote_api_stub.MaybeInvokeAuthentication()
    self.authenticated = True

  def AuthFunction(self,
                   raw_input_fn=raw_input,
                   password_input_fn=getpass.getpass):
    """Prompts the user for a username and password.

    Caches the results the first time it is called and returns the
    same result every subsequent time.

    Args:
      raw_input_fn: Used for dependency injection.
      password_input_fn: Used for dependency injection.

    Returns:
      A pair of the username and password.
    """
    self.auth_called = True
    return _AuthFunction(self.host, self.email, self.passin,
                         raw_input_fn, password_input_fn)

  def IncrementId(self, ancestor_path, kind, high_id):
    """Increment the unique id counter associated with ancestor_path and kind.

    Args:
      ancestor_path: A list encoding the path of a key.
      kind: The string name of a kind.
      high_id: The int value to which to increment the unique id counter.
    """
    if self.dry_run:
      return
    high_id_key = datastore.Key.from_path(*(ancestor_path + [kind, high_id]))
    IncrementId(high_id_key)

  def GetSchemaKinds(self):
    """Returns the list of kinds for this app."""
    global_stat = stats.GlobalStat.all().get()
    if not global_stat:
      raise KindStatError()
    timestamp = global_stat.timestamp
    kind_stat = stats.KindStat.all().filter(
        "timestamp =", timestamp).fetch(1000)
    kind_list = [stat.kind_name for stat in kind_stat
                 if stat.kind_name and not stat.kind_name.startswith('__')]
    kind_set = set(kind_list)
    return list(kind_set)

  def EncodeContent(self, rows, loader=None):
    """Encodes row data to the wire format.

    Args:
      rows: A list of pairs of a line number and a list of column values.
      loader: Used for dependency injection.

    Returns:
      A list of datastore.Entity instances.

    Raises:
      ConfigurationError: if no loader is defined for self.kind
    """
    if not loader:
      try:
        loader = Loader.RegisteredLoader(self.kind)
      except KeyError:
        logger.error('No Loader defined for kind %s.' % self.kind)
        raise ConfigurationError('No Loader defined for kind %s.' % self.kind)
    entities = []
    for line_number, values in rows:
      key = loader.generate_key(line_number, values)
      if isinstance(key, datastore.Key):
        parent = key.parent()
        key = key.name()
      else:
        parent = None
      entity = loader.create_entity(values, key_name=key, parent=parent)

      def ToEntity(entity):
        if isinstance(entity, db.Model):
          return entity._populate_entity()
        else:
          return entity

      if not entity:

        continue
      if isinstance(entity, list):
        entities.extend(map(ToEntity, entity))
      elif entity:
        entities.append(ToEntity(entity))

    return entities

  def PostEntities(self, entities):
    """Posts Entity records to a remote endpoint over HTTP.

    Args:
      entities: A list of datastore entities.
    """
    if self.dry_run:
      return
    datastore.Put(entities)

  def _QueryForPbs(self, query):
    """Perform the given query and return a list of entity_pb's."""
    try:
      query_pb = query._ToPb(limit=self.batch_size, count=self.batch_size)
      result_pb = datastore_pb.QueryResult()
      apiproxy_stub_map.MakeSyncCall('datastore_v3', 'RunQuery', query_pb,
                                     result_pb)
      results = result_pb.result_list()

      while result_pb.more_results():
        next_pb = datastore_pb.NextRequest()
        next_pb.set_count(self.batch_size - len(results))
        next_pb.mutable_cursor().CopyFrom(result_pb.cursor())
        result_pb = datastore_pb.QueryResult()
        apiproxy_stub_map.MakeSyncCall('datastore_v3', 'Next', next_pb,
                                       result_pb)
        results += result_pb.result_list()

      return results
    except apiproxy_errors.ApplicationError, e:
      raise datastore._ToDatastoreError(e)

  def GetEntities(
      self, key_range_item, key_factory=datastore.Key, keys_only=False,
      retry_parallel=False):
    """Gets Entity records from a remote endpoint over HTTP.

    Args:
     key_range_item: Range of keys to get.
     key_factory: Used for dependency injection.
     keys_only: bool, default False, only get keys values
     retry_parallel: bool, default False, to try a parallel download despite
       past parallel download failures.
    Returns:
      A DownloadResult instance.

    Raises:
      ConfigurationError: if no Exporter is defined for key_range_item.kind
    """
    keys = []
    entities = []
    kind = key_range_item.kind
    if retry_parallel:
      self.parallel_download = True

    if self.parallel_download:
      query = key_range_item.key_range.make_directed_datastore_query(
          kind, keys_only=keys_only)
      try:
        results = self._QueryForPbs(query)
      except datastore_errors.NeedIndexError:

        logger.info('%s: No descending index on __key__, '
                    'performing serial download', kind)
        self.parallel_download = False

    if not self.parallel_download:


      key_range_item.key_range.direction = key_range_module.KeyRange.ASC
      query = key_range_item.key_range.make_ascending_datastore_query(
          kind, keys_only=keys_only)
      results = self._QueryForPbs(query)

    size = len(results)

    for entity in results:


      key = key_factory()
      key._Key__reference = entity.key()
      entities.append(entity)
      keys.append(key)

    continued = (size == self.batch_size)
    key_range_item.count = size

    return DownloadResult(continued, key_range_item.key_range.direction,
                          keys, entities)

  def GetMapper(self, kind):
    """Returns a mapper for the registered kind.

    Returns:
      A Mapper instance.

    Raises:
      ConfigurationError: if no Mapper is defined for kind
    """
    if not self.mapper:
      try:
        self.mapper = Mapper.RegisteredMapper(kind)
      except KeyError:
        logger.error('No Mapper defined for kind %s.' % kind)
        raise ConfigurationError('No Mapper defined for kind %s.' % kind)
    return self.mapper


def InterruptibleSleep(sleep_time):
  """Puts thread to sleep, checking this threads exit_flag twice a second.

  Args:
    sleep_time: Time to sleep.
  """
  slept = 0.0
  epsilon = .0001
  thread = threading.currentThread()
  while slept < sleep_time - epsilon:
    remaining = sleep_time - slept
    this_sleep_time = min(remaining, 0.5)
    time.sleep(this_sleep_time)
    slept += this_sleep_time
    if thread.exit_flag:
      return


class _ThreadBase(threading.Thread):
  """Provide some basic features for the threads used in the uploader.

  This abstract base class is used to provide some common features:

  * Flag to ask thread to exit as soon as possible.
  * Record exit/error status for the primary thread to pick up.
  * Capture exceptions and record them for pickup.
  * Some basic logging of thread start/stop.
  * All threads are "daemon" threads.
  * Friendly names for presenting to users.

  Concrete sub-classes must implement PerformWork().

  Either self.NAME should be set or GetFriendlyName() be overridden to
  return a human-friendly name for this thread.

  The run() method starts the thread and prints start/exit messages.

  self.exit_flag is intended to signal that this thread should exit
  when it gets the chance.  PerformWork() should check self.exit_flag
  whenever it has the opportunity to exit gracefully.
  """

  def __init__(self):
    threading.Thread.__init__(self)




    self.setDaemon(True)

    self.exit_flag = False
    self.error = None
    self.traceback = None

  def run(self):
    """Perform the work of the thread."""
    logger.debug('[%s] %s: started', self.getName(), self.__class__.__name__)

    try:
      self.PerformWork()
    except:
      self.SetError()
      logger.exception('[%s] %s:', self.getName(), self.__class__.__name__)

    logger.debug('[%s] %s: exiting', self.getName(), self.__class__.__name__)

  def SetError(self):
    """Sets the error and traceback information for this thread.

    This must be called from an exception handler.
    """
    if not self.error:
      exc_info = sys.exc_info()
      self.error = exc_info[1]
      self.traceback = exc_info[2]

  def PerformWork(self):
    """Perform the thread-specific work."""
    raise NotImplementedError()

  def CheckError(self):
    """If an error is present, then log it."""
    if self.error:
      logger.error('Error in %s: %s', self.GetFriendlyName(), self.error)
      if self.traceback:
        logger.debug(''.join(traceback.format_exception(self.error.__class__,
                                                        self.error,
                                                        self.traceback)))

  def GetFriendlyName(self):
    """Returns a human-friendly description of the thread."""
    if hasattr(self, 'NAME'):
      return self.NAME
    return 'unknown thread'


non_fatal_error_codes = set([errno.EAGAIN,
                             errno.ENETUNREACH,
                             errno.ENETRESET,
                             errno.ECONNRESET,
                             errno.ETIMEDOUT,
                             errno.EHOSTUNREACH])


def IsURLErrorFatal(error):
  """Returns False if the given URLError may be from a transient failure.

  Args:
    error: A urllib2.URLError instance.
  """
  assert isinstance(error, urllib2.URLError)
  if not hasattr(error, 'reason'):
    return True
  if not isinstance(error.reason[0], int):
    return True
  return error.reason[0] not in non_fatal_error_codes


class DataSourceThread(_ThreadBase):
  """A thread which reads WorkItems and pushes them into queue.

  This thread will read/consume WorkItems from a generator (produced by
  the generator factory). These WorkItems will then be pushed into the
  thread_pool. Note that reading will block if/when the thread_pool becomes
  full. Information on content consumed from the generator will be pushed
  into the progress_queue.
  """

  NAME = 'data source thread'

  def __init__(self,
               request_manager,
               kinds,
               thread_pool,
               progress_queue,
               workitem_generator_factory,
               progress_generator_factory):
    """Initialize the DataSourceThread instance.

    Args:
      request_manager: A RequestManager instance.
      kinds: The kinds of entities being transferred.
      thread_pool: An AdaptiveThreadPool instance.
      progress_queue: A queue used for tracking progress information.
      workitem_generator_factory: A factory that creates a WorkItem generator
      progress_generator_factory: A factory that creates a generator which
        produces prior progress status, or None if there is no prior status
        to use.
    """
    _ThreadBase.__init__(self)

    self.request_manager = request_manager
    self.kinds = kinds
    self.thread_pool = thread_pool
    self.progress_queue = progress_queue
    self.workitem_generator_factory = workitem_generator_factory
    self.progress_generator_factory = progress_generator_factory

    self.entity_count = 0

  def PerformWork(self):
    """Performs the work of a DataSourceThread."""


    if self.progress_generator_factory:
      progress_gen = self.progress_generator_factory()
    else:
      progress_gen = None

    content_gen = self.workitem_generator_factory(self.request_manager,
                                                  self.progress_queue,
                                                  progress_gen,
                                                  self.kinds)

    self.xfer_count = 0
    self.read_count = 0
    self.read_all = False

    for item in content_gen.Batches():





      item.MarkAsRead()




      while not self.exit_flag:
        try:

          self.thread_pool.SubmitItem(item, block=True, timeout=1.0)
          self.entity_count += item.count
          break
        except Queue.Full:
          pass


      if self.exit_flag:
        break

    if not self.exit_flag:
      self.read_all = True
    self.read_count = content_gen.row_count
    self.xfer_count = content_gen.xfer_count




def _RunningInThread(thread):
  """Return True if we are running within the specified thread."""
  return threading.currentThread().getName() == thread.getName()


class _Database(object):
  """Base class for database connections in this module.

  The table is created by a primary thread (the python main thread)
  but all future lookups and updates are performed by a secondary
  thread.
  """

  SIGNATURE_TABLE_NAME = 'bulkloader_database_signature'

  def __init__(self,
               db_filename,
               create_table,
               signature,
               index=None,
               commit_periodicity=100):
    """Initialize the _Database instance.

    Args:
      db_filename: The sqlite3 file to use for the database.
      create_table: A string containing the SQL table creation command.
      signature: A string identifying the important invocation options,
        used to make sure we are not using an old database.
      index: An optional string to create an index for the database.
      commit_periodicity: Number of operations between database commits.
    """


    self.db_filename = db_filename



    logger.info('Opening database: %s', db_filename)
    self.primary_conn = sqlite3.connect(db_filename, isolation_level=None)
    self.primary_thread = threading.currentThread()


    self.secondary_conn = None
    self.secondary_thread = None

    self.operation_count = 0
    self.commit_periodicity = commit_periodicity



    try:
      self.primary_conn.execute(create_table)
    except sqlite3.OperationalError, e:

      if 'already exists' not in e.message:
        raise

    if index:
      try:
        self.primary_conn.execute(index)
      except sqlite3.OperationalError, e:

        if 'already exists' not in e.message:
          raise

    self.existing_table = False
    signature_cursor = self.primary_conn.cursor()
    create_signature = """
      create table %s (
      value TEXT not null)
    """ % _Database.SIGNATURE_TABLE_NAME
    try:
      self.primary_conn.execute(create_signature)
      self.primary_conn.cursor().execute(
          'insert into %s (value) values (?)' % _Database.SIGNATURE_TABLE_NAME,
          (signature,))
    except sqlite3.OperationalError, e:
      if 'already exists' not in e.message:
        logger.exception('Exception creating table:')
        raise
      else:
        self.existing_table = True
        signature_cursor.execute(
            'select * from %s' % _Database.SIGNATURE_TABLE_NAME)
        (result,) = signature_cursor.fetchone()
        if result and result != signature:
          logger.error('Database signature mismatch:\n\n'
                       'Found:\n'
                       '%s\n\n'
                       'Expecting:\n'
                       '%s\n',
                       result, signature)
          raise ResumeError('Database signature mismatch: %s != %s' % (
                            signature, result))

  def ThreadComplete(self):
    """Finalize any operations the secondary thread has performed.

    The database aggregates lots of operations into a single commit, and
    this method is used to commit any pending operations as the thread
    is about to shut down.
    """
    if self.secondary_conn:
      self._MaybeCommit(force_commit=True)

  def _MaybeCommit(self, force_commit=False):
    """Periodically commit changes into the SQLite database.

    Committing every operation is quite expensive, and slows down the
    operation of the script. Thus, we only commit after every N operations,
    as determined by the self.commit_periodicity value. Optionally, the
    caller can force a commit.

    Args:
      force_commit: Pass True in order for a commit to occur regardless
        of the current operation count.
    """
    self.operation_count += 1
    if force_commit or (self.operation_count % self.commit_periodicity) == 0:
      self.secondary_conn.commit()

  def _OpenSecondaryConnection(self):
    """Possibly open a database connection for the secondary thread.

    If the connection is not open (for the calling thread, which is assumed
    to be the unique secondary thread), then open it. We also open a couple
    cursors for later use (and reuse).
    """
    if self.secondary_conn:
      return

    assert not _RunningInThread(self.primary_thread)

    self.secondary_thread = threading.currentThread()







    self.secondary_conn = sqlite3.connect(self.db_filename)


    self.insert_cursor = self.secondary_conn.cursor()
    self.update_cursor = self.secondary_conn.cursor()



zero_matcher = re.compile(r'\x00')

zero_one_matcher = re.compile(r'\x00\x01')


def KeyStr(key):
  """Returns a string to represent a key, preserving ordering.

  Unlike datastore.Key.__str__(), we have the property:

    key1 < key2 ==> KeyStr(key1) < KeyStr(key2)

  The key string is constructed from the key path as follows:
    (1) Strings are prepended with ':' and numeric id's are padded to
        20 digits.
    (2) Any null characters (u'\0') present are replaced with u'\0\1'
    (3) The sequence u'\0\0' is used to separate each component of the path.

  (1) assures that names and ids compare properly, while (2) and (3) enforce
  the part-by-part comparison of pieces of the path.

  Args:
    key: A datastore.Key instance.

  Returns:
    A string representation of the key, which preserves ordering.
  """
  assert isinstance(key, datastore.Key)
  path = key.to_path()

  out_path = []
  for part in path:
    if isinstance(part, (int, long)):


      part = '%020d' % part
    else:

      part = ':%s' % part

    out_path.append(zero_matcher.sub(u'\0\1', part))

  out_str = u'\0\0'.join(out_path)

  return out_str


def StrKey(key_str):
  """The inverse of the KeyStr function.

  Args:
    key_str: A string in the range of KeyStr.

  Returns:
    A datastore.Key instance k, such that KeyStr(k) == key_str.
  """
  parts = key_str.split(u'\0\0')
  for i in xrange(len(parts)):
    if parts[i][0] == ':':

      part = parts[i][1:]
      part = zero_one_matcher.sub(u'\0', part)
      parts[i] = part
    else:
      parts[i] = int(parts[i])
  return datastore.Key.from_path(*parts)


class ResultDatabase(_Database):
  """Persistently record all the entities downloaded during an export.

  The entities are held in the database by their unique datastore key
  in order to avoid duplication if an export is restarted.
  """

  def __init__(self, db_filename, signature, commit_periodicity=1,
               exporter=None):
    """Initialize a ResultDatabase object.

    Args:
      db_filename: The name of the SQLite database to use.
      signature: A string identifying the important invocation options,
        used to make sure we are not using an old database.
      commit_periodicity: How many operations to perform between commits.
      exporter: Exporter instance; if exporter.calculate_sort_key_from_entity
        is true then exporter.sort_key_from_entity(entity) will be called.
    """
    self.complete = False
    create_table = ('create table result (\n'
                    'id BLOB primary key,\n'
                    'value BLOB not null,\n'
                    'sort_key BLOB)')

    _Database.__init__(self,
                       db_filename,
                       create_table,
                       signature,
                       commit_periodicity=commit_periodicity)
    if self.existing_table:
      cursor = self.primary_conn.cursor()
      cursor.execute('select count(*) from result')
      self.existing_count = int(cursor.fetchone()[0])
    else:
      self.existing_count = 0
    self.count = self.existing_count
    if exporter and getattr(exporter, 'calculate_sort_key_from_entity', False):
      self.sort_key_from_entity = exporter.sort_key_from_entity
    else:
      self.sort_key_from_entity = None

  def _StoreEntity(self, entity_id, entity):
    """Store an entity in the result database.

    Args:
      entity_id: A datastore.Key for the entity.
      entity: The entity to store.

    Returns:
      True if this entities is not already present in the result database.
    """
    assert _RunningInThread(self.secondary_thread)
    assert isinstance(entity_id, datastore.Key), (
        'expected a datastore.Key, got a %s' % entity_id.__class__.__name__)

    key_str = buffer(KeyStr(entity_id).encode('utf-8'))
    self.insert_cursor.execute(
        'select count(*) from result where id = ?', (key_str,))

    already_present = self.insert_cursor.fetchone()[0]
    result = True
    if already_present:
      result = False
      self.insert_cursor.execute('delete from result where id = ?',
                                 (key_str,))
    else:
      self.count += 1
    if self.sort_key_from_entity:
      sort_key = self.sort_key_from_entity(datastore.Entity._FromPb(entity))
    else:
      sort_key = ''
    value = entity.Encode()
    self.insert_cursor.execute(
        'insert into result (id, value, sort_key) values (?, ?, ?)',
        (key_str, buffer(value), sort_key))
    return result

  def StoreEntities(self, keys, entities):
    """Store a group of entities in the result database.

    Args:
      keys: A list of entity keys.
      entities: A list of entities.

    Returns:
      The number of new entities stored in the result database.
    """
    self._OpenSecondaryConnection()
    t = time.time()
    count = 0
    for entity_id, entity in zip(keys,
                                 entities):
      if self._StoreEntity(entity_id, entity):
        count += 1
    logger.debug('%s insert: delta=%.3f',
                 self.db_filename,
                 time.time() - t)
    logger.debug('Entities transferred total: %s', self.count)
    self._MaybeCommit()
    return count

  def ResultsComplete(self):
    """Marks the result database as containing complete results."""
    self.complete = True

  def AllEntities(self):
    """Yields all pairs of (id, value) from the result table."""

    conn = sqlite3.connect(self.db_filename, isolation_level=None)
    cursor = conn.cursor()




    cursor.execute(
        'select id, value from result order by sort_key, id')

    for unused_entity_id, entity in cursor:
      entity_proto = entity_pb.EntityProto(contents=entity)
      yield datastore.Entity._FromPb(entity_proto)


class _ProgressDatabase(_Database):
  """Persistently record all progress information during an upload.

  This class wraps a very simple SQLite database which records each of
  the relevant details from a chunk of work. If the loader is
  resumed, then data is replayed out of the database.
  """

  def __init__(self,
               db_filename,
               sql_type,
               py_type,
               signature,
               commit_periodicity=100):
    """Initialize the ProgressDatabase instance.

    Args:
      db_filename: The name of the SQLite database to use.
      sql_type: A string of the SQL type to use for entity keys.
      py_type: The python type of entity keys.
      signature: A string identifying the important invocation options,
        used to make sure we are not using an old database.
      commit_periodicity: How many operations to perform between commits.
    """
    self.prior_key_end = None






    create_table = ('create table progress (\n'
                    'id integer primary key autoincrement,\n'
                    'state integer not null,\n'
                    'kind text not null,\n'
                    'key_start %s,\n'
                    'key_end %s)'
                    % (sql_type, sql_type))
    self.py_type = py_type

    index = 'create index i_state on progress (state)'
    _Database.__init__(self,
                       db_filename,
                       create_table,
                       signature,
                       index=index,
                       commit_periodicity=commit_periodicity)

  def UseProgressData(self):
    """Returns True if the database has progress information.

    Note there are two basic cases for progress information:
    1) All saved records indicate a successful upload. In this case, we
       need to skip everything transmitted so far and then send the rest.
    2) Some records for incomplete transfer are present. These need to be
       sent again, and then we resume sending after all the successful
       data.

    Returns:
      True: if the database has progress information.

    Raises:
      ResumeError: if there is an error retrieving rows from the database.
    """
    assert _RunningInThread(self.primary_thread)



    cursor = self.primary_conn.cursor()
    cursor.execute('select count(*) from progress')
    row = cursor.fetchone()
    if row is None:
      raise ResumeError('Cannot retrieve progress information from database.')


    return row[0] != 0

  def StoreKeys(self, kind, key_start, key_end):
    """Record a new progress record, returning a key for later updates.

    The specified progress information will be persisted into the database.
    A unique key will be returned that identifies this progress state. The
    key is later used to (quickly) update this record.

    For the progress resumption to proceed properly, calls to StoreKeys
    MUST specify monotonically increasing key ranges. This will result in
    a database whereby the ID, KEY_START, and KEY_END rows are all
    increasing (rather than having ranges out of order).

    NOTE: the above precondition is NOT tested by this method (since it
    would imply an additional table read or two on each invocation).

    Args:
      kind: The kind for the WorkItem
      key_start: The starting key of the WorkItem (inclusive)
      key_end: The end key of the WorkItem (inclusive)

    Returns:
      A string to later be used as a unique key to update this state.
    """
    self._OpenSecondaryConnection()

    assert _RunningInThread(self.secondary_thread)
    assert (not key_start) or isinstance(key_start, self.py_type), (
        '%s is a %s, %s expected %s' % (key_start,
                                        key_start.__class__,
                                        self.__class__.__name__,
                                        self.py_type))
    assert (not key_end) or isinstance(key_end, self.py_type), (
        '%s is a %s, %s expected %s' % (key_end,
                                        key_end.__class__,
                                        self.__class__.__name__,
                                        self.py_type))
    assert KeyLEQ(key_start, key_end), '%s not less than %s' % (
        repr(key_start), repr(key_end))

    self.insert_cursor.execute(
        'insert into progress (state, kind, key_start, key_end)'
        ' values (?, ?, ?, ?)',
        (STATE_READ, unicode(kind), unicode(key_start), unicode(key_end)))

    progress_key = self.insert_cursor.lastrowid

    self._MaybeCommit()

    return progress_key

  def UpdateState(self, key, new_state):
    """Update a specified progress record with new information.

    Args:
      key: The key for this progress record, returned from StoreKeys
      new_state: The new state to associate with this progress record.
    """
    self._OpenSecondaryConnection()

    assert _RunningInThread(self.secondary_thread)
    assert isinstance(new_state, int)

    self.update_cursor.execute('update progress set state=? where id=?',
                               (new_state, key))

    self._MaybeCommit()

  def DeleteKey(self, progress_key):
    """Delete the entities with the given key from the result database."""
    self._OpenSecondaryConnection()

    assert _RunningInThread(self.secondary_thread)

    t = time.time()
    self.insert_cursor.execute(
        'delete from progress where rowid = ?', (progress_key,))

    logger.debug('delete: delta=%.3f', time.time() - t)

    self._MaybeCommit()

  def GetProgressStatusGenerator(self):
    """Get a generator which yields progress information.

    The returned generator will yield a series of 5-tuples that specify
    progress information about a prior run of the uploader. The 5-tuples
    have the following values:

      progress_key: The unique key to later update this record with new
                    progress information.
      state: The last state saved for this progress record.
      kind: The datastore kind of the items for uploading.
      key_start: The starting key of the items for uploading (inclusive).
      key_end: The ending key of the items for uploading (inclusive).

    After all incompletely-transferred records are provided, then one
    more 5-tuple will be generated:

      None
      DATA_CONSUMED_TO_HERE: A unique string value indicating this record
                             is being provided.
      None
      None
      key_end: An integer value specifying the last data source key that
               was handled by the previous run of the uploader.

    The caller should begin uploading records which occur after key_end.

    Yields:
      Five-tuples of (progress_key, state, kind, key_start, key_end)
    """



    conn = sqlite3.connect(self.db_filename, isolation_level=None)
    cursor = conn.cursor()



    cursor.execute('select max(key_end) from progress')

    result = cursor.fetchone()
    if result is not None:
      key_end = result[0]
    else:
      logger.debug('No rows in progress database.')
      return

    self.prior_key_end = key_end



    cursor.execute(
        'select id, state, kind, key_start, key_end from progress'
        '  where state != ?'
        '  order by id',
        (STATE_SENT,))



    rows = cursor.fetchall()

    for row in rows:
      if row is None:
        break
      progress_key, state, kind, key_start, key_end = row

      yield progress_key, state, kind, key_start, key_end


    yield None, DATA_CONSUMED_TO_HERE, None, None, key_end


def ProgressDatabase(db_filename, signature):
  """Returns a database to store upload progress information."""
  return _ProgressDatabase(db_filename, 'INTEGER', int, signature)


class ExportProgressDatabase(_ProgressDatabase):
  """A database to store download progress information."""

  def __init__(self, db_filename, signature):
    """Initialize an ExportProgressDatabase."""
    _ProgressDatabase.__init__(self,
                               db_filename,
                               'TEXT',
                               datastore.Key,
                               signature,
                               commit_periodicity=1)

  def UseProgressData(self):
    """Check if the progress database contains progress data.

    Returns:
      True: if the database contains progress data.
    """




    return self.existing_table


class StubProgressDatabase(object):
  """A stub implementation of ProgressDatabase which does nothing."""

  def UseProgressData(self):
    """Whether the stub database has progress information (it doesn't)."""
    return False

  def StoreKeys(self, unused_kind, unused_key_start, unused_key_end):
    """Pretend to store a key in the stub database."""
    return 'fake-key'

  def UpdateState(self, unused_key, unused_new_state):
    """Pretend to update the state of a progress item."""
    pass

  def ThreadComplete(self):
    """Finalize operations on the stub database (i.e. do nothing)."""
    pass

  def DeleteKey(self, unused_key):
    """Delete the operations with a given key (but, do nothing.)"""
    pass


class _ProgressThreadBase(_ThreadBase):
  """A thread which records progress information for the upload process.

  The progress information is stored into the provided progress database.
  This class is not responsible for replaying a prior run's progress
  information out of the database. Separate mechanisms must be used to
  resume a prior upload attempt.
  """

  NAME = 'progress tracking thread'

  def __init__(self, progress_queue, progress_db):
    """Initialize the ProgressTrackerThread instance.

    Args:
      progress_queue: A Queue used for tracking progress information.
      progress_db: The database for tracking progress information; should
        be an instance of ProgressDatabase.
    """
    _ThreadBase.__init__(self)

    self.progress_queue = progress_queue
    self.db = progress_db
    self.entities_transferred = 0

  def EntitiesTransferred(self):
    """Return the total number of unique entities transferred."""
    return self.entities_transferred

  def UpdateProgress(self, item):
    """Updates the progress information for the given item.

    Args:
      item: A work item whose new state will be recorded
    """
    raise NotImplementedError()

  def WorkFinished(self):
    """Performs final actions after the entity transfer is complete."""
    raise NotImplementedError()

  def PerformWork(self):
    """Performs the work of a ProgressTrackerThread."""
    while not self.exit_flag:
      try:
        item = self.progress_queue.get(block=True, timeout=1.0)
      except Queue.Empty:

        continue
      if item == _THREAD_SHOULD_EXIT:
        break

      if item.state == STATE_READ and item.progress_key is None:


        item.progress_key = self.db.StoreKeys(item.kind,
                                              item.key_start,
                                              item.key_end)
      else:



        assert item.progress_key is not None
        self.UpdateProgress(item)


      item.progress_event.set()

      self.progress_queue.task_done()

    self.db.ThreadComplete()




class ProgressTrackerThread(_ProgressThreadBase):
  """A thread which records progress information for the upload process.

  The progress information is stored into the provided progress database.
  This class is not responsible for replaying a prior run's progress
  information out of the database. Separate mechanisms must be used to
  resume a prior upload attempt.
  """
  NAME = 'progress tracking thread'

  def __init__(self, progress_queue, progress_db):
    """Initialize the ProgressTrackerThread instance.

    Args:
      progress_queue: A Queue used for tracking progress information.
      progress_db: The database for tracking progress information; should
        be an instance of ProgressDatabase.
    """
    _ProgressThreadBase.__init__(self, progress_queue, progress_db)

  def UpdateProgress(self, item):
    """Update the state of the given WorkItem.

    Args:
      item: A WorkItem instance.
    """
    self.db.UpdateState(item.progress_key, item.state)
    if item.state == STATE_SENT:
      self.entities_transferred += item.count

  def WorkFinished(self):
    """Performs final actions after the entity transfer is complete."""
    pass


class ExportProgressThread(_ProgressThreadBase):
  """A thread to record progress information and write record data for exports.

  The progress information is stored into a provided progress database.
  Exported results are stored in the result database and dumped to an output
  file at the end of the download.
  """

  def __init__(self, exporter, progress_queue, progress_db, result_db):
    """Initialize the ExportProgressThread instance.

    Args:
      exporter: An Exporter instance for the download.
      progress_queue: A Queue used for tracking progress information.
      progress_db: The database for tracking progress information; should
        be an instance of ProgressDatabase.
      result_db: The database for holding exported entities; should be an
        instance of ResultDatabase.
    """
    _ProgressThreadBase.__init__(self, progress_queue, progress_db)

    self.exporter = exporter
    self.existing_count = result_db.existing_count
    self.result_db = result_db

  def EntitiesTransferred(self):
    """Return the total number of unique entities transferred."""
    return self.result_db.count

  def WorkFinished(self):
    """Write the contents of the result database."""
    self.exporter.output_entities(self.result_db.AllEntities())

  def UpdateProgress(self, item):
    """Update the state of the given KeyRangeItem.

    Args:
      item: A KeyRange instance.
    """
    if item.state == STATE_GOT:
      count = self.result_db.StoreEntities(item.download_result.keys,
                                           item.download_result.entities)

      self.db.DeleteKey(item.progress_key)
      self.entities_transferred += count
    else:
      self.db.UpdateState(item.progress_key, item.state)


class MapperProgressThread(_ProgressThreadBase):
  """A thread to record progress information for maps over the datastore."""

  def __init__(self, mapper, progress_queue, progress_db):
    """Initialize the MapperProgressThread instance.

    Args:
      mapper: A Mapper object for this map run.
      progress_queue: A Queue used for tracking progress information.
      progress_db: The database for tracking progress information; should
        be an instance of ProgressDatabase.
    """
    _ProgressThreadBase.__init__(self, progress_queue, progress_db)

    self.mapper = mapper

  def EntitiesTransferred(self):
    """Return the total number of unique entities transferred."""
    return self.entities_transferred

  def WorkFinished(self):
    """Perform actions after map is complete."""
    pass

  def UpdateProgress(self, item):
    """Update the state of the given KeyRangeItem.

    Args:
      item: A KeyRange instance.
    """
    if item.state == STATE_GOT:
      self.entities_transferred += item.count

      self.db.DeleteKey(item.progress_key)
    else:
      self.db.UpdateState(item.progress_key, item.state)


def ParseKey(key_string):
  """Turn a key stored in the database into a Key or None.

  Args:
    key_string: The string representation of a Key.

  Returns:
    A datastore.Key instance or None
  """
  if not key_string:
    return None
  if key_string == 'None':
    return None
  return datastore.Key(encoded=key_string)


def Validate(value, typ):
  """Checks that value is non-empty and of the right type.

  Args:
    value: any value
    typ: a type or tuple of types

  Raises:
    ValueError: if value is None or empty.
    TypeError: if it's not the given type.
  """
  if not value:
    raise ValueError('Value should not be empty; received %s.' % value)
  elif not isinstance(value, typ):
    raise TypeError('Expected a %s, but received %s (a %s).' %
                    (typ, value, value.__class__))


def CheckFile(filename):
  """Check that the given file exists and can be opened for reading.

  Args:
    filename: The name of the file.

  Raises:
    FileNotFoundError: if the given filename is not found
    FileNotReadableError: if the given filename is not readable.
  """
  if not os.path.exists(filename):
    raise FileNotFoundError('%s: file not found' % filename)
  elif not os.access(filename, os.R_OK):
    raise FileNotReadableError('%s: file not readable' % filename)


class Loader(object):
  """A base class for creating datastore entities from input data.

  To add a handler for bulk loading a new entity kind into your datastore,
  write a subclass of this class that calls Loader.__init__ from your
  class's __init__.

  If you need to run extra code to convert entities from the input
  data, create new properties, or otherwise modify the entities before
  they're inserted, override handle_entity.

  See the create_entity method for the creation of entities from the
  (parsed) input data.
  """

  __loaders = {}
  kind = None
  __properties = None

  def __init__(self, kind, properties):
    """Constructor.

    Populates this Loader's kind and properties map.

    Args:
      kind: a string containing the entity kind that this loader handles

      properties: list of (name, converter) tuples.

        This is used to automatically convert the input columns into
        properties.  The converter should be a function that takes one
        argument, a string value from the input file, and returns a
        correctly typed property value that should be inserted. The
        tuples in this list should match the columns in your input file,
        in order.

        For example:
          [('name', str),
           ('id_number', int),
           ('email', datastore_types.Email),
           ('user', users.User),
           ('birthdate', lambda x: datetime.datetime.fromtimestamp(float(x))),
           ('description', datastore_types.Text),
           ]
    """
    Validate(kind, (basestring, tuple))
    self.kind = kind
    self.__openfile = open
    self.__create_csv_reader = csv.reader


    GetImplementationClass(kind)

    Validate(properties, list)
    for name, fn in properties:
      Validate(name, basestring)
      assert callable(fn), (
        'Conversion function %s for property %s is not callable.' % (fn, name))

    self.__properties = properties

  @staticmethod
  def RegisterLoader(loader):
    """Register loader and the Loader instance for its kind.

    Args:
      loader: A Loader instance.
    """
    Loader.__loaders[loader.kind] = loader

  def get_high_ids(self):
    """Returns dict {ancestor_path : {kind : id}} with high id values.

    The returned dictionary is used to increment the id counters
    associated with each ancestor_path and kind to be at least id.
    """
    return {}

  def alias_old_names(self):
    """Aliases method names so that Loaders defined with old names work."""
    aliases = (
        ('CreateEntity', 'create_entity'),
        ('HandleEntity', 'handle_entity'),
        ('GenerateKey', 'generate_key'),
        )
    for old_name, new_name in aliases:


      setattr(Loader, old_name, getattr(Loader, new_name))


      if hasattr(self.__class__, old_name) and not (
          getattr(self.__class__, old_name).im_func ==
          getattr(Loader, new_name).im_func):
        if hasattr(self.__class__, new_name) and not (
            getattr(self.__class__, new_name).im_func ==
            getattr(Loader, new_name).im_func):

          raise NameClashError(old_name, new_name, self.__class__)

        setattr(self, new_name, getattr(self, old_name))

  def create_entity(self, values, key_name=None, parent=None):
    """Creates a entity from a list of property values.

    Args:
      values: list/tuple of str
      key_name: if provided, the name for the (single) resulting entity
      parent: A datastore.Key instance for the parent, or None

    Returns:
      list of db.Model

      The returned entities are populated with the property values from the
      argument, converted to native types using the properties map given in
      the constructor, and passed through handle_entity. They're ready to be
      inserted.

    Raises:
      AssertionError: if the number of values doesn't match the number
        of properties in the properties map.
      ValueError: if any element of values is None or empty.
      TypeError: if values is not a list or tuple.
    """
    Validate(values, (list, tuple))
    assert len(values) == len(self.__properties), (
        'Expected %d columns, found %d.' %
        (len(self.__properties), len(values)))

    model_class = GetImplementationClass(self.kind)

    properties = {
        'key_name': key_name,
        'parent': parent,
        }
    for (name, converter), val in zip(self.__properties, values):
      if converter is bool and val.lower() in ('0', 'false', 'no'):
        val = False
      properties[name] = converter(val)

    entity = model_class(**properties)
    entities = self.handle_entity(entity)

    if entities:
      if not isinstance(entities, (list, tuple)):
        entities = [entities]

      for entity in entities:
        if not isinstance(entity, db.Model):
          raise TypeError('Expected a db.Model, received %s (a %s).' %
                          (entity, entity.__class__))

    return entities

  def generate_key(self, i, values):
    """Generates a key_name to be used in creating the underlying object.

    The default implementation returns None.

    This method can be overridden to control the key generation for
    uploaded entities. The value returned should be None (to use a
    server generated numeric key), or a string which neither starts
    with a digit nor has the form __*__ (see
    http://code.google.com/appengine/docs/python/datastore/keysandentitygroups.html),
    or a datastore.Key instance.

    If you generate your own string keys, keep in mind:

    1. The key name for each entity must be unique.
    2. If an entity of the same kind and key already exists in the
       datastore, it will be overwritten.

    Args:
      i: Number corresponding to this object (assume it's run in a loop,
        this is your current count.
      values: list/tuple of str.

    Returns:
      A string to be used as the key_name for an entity.
    """
    return None

  def handle_entity(self, entity):
    """Subclasses can override this to add custom entity conversion code.

    This is called for each entity, after its properties are populated
    from the input but before it is stored. Subclasses can override
    this to add custom entity handling code.

    The entity to be inserted should be returned. If multiple entities
    should be inserted, return a list of entities. If no entities
    should be inserted, return None or [].

    Args:
      entity: db.Model

    Returns:
      db.Model or list of db.Model
    """
    return entity

  def initialize(self, filename, loader_opts):
    """Performs initialization and validation of the input file.

    This implementation checks that the input file exists and can be
    opened for reading.

    Args:
      filename: The string given as the --filename flag argument.
      loader_opts: The string given as the --loader_opts flag argument.
    """
    CheckFile(filename)

  def finalize(self):
    """Performs finalization actions after the upload completes."""
    pass

  def generate_records(self, filename):
    """Subclasses can override this to add custom data input code.

    This method must yield fixed-length lists of strings.

    The default implementation uses csv.reader to read CSV rows
    from filename.

    Args:
      filename: The string input for the --filename option.

    Yields:
      Lists of strings.
    """
    csv_generator = CSVGenerator(filename, openfile=self.__openfile,
                                 create_csv_reader=self.__create_csv_reader
                                ).Records()
    return csv_generator

  @staticmethod
  def RegisteredLoaders():
    """Returns a dict of the Loader instances that have been created."""

    return dict(Loader.__loaders)

  @staticmethod
  def RegisteredLoader(kind):
    """Returns the loader instance for the given kind if it exists."""
    return Loader.__loaders[kind]


class RestoreThread(_ThreadBase):
  """A thread to read saved entity_pbs from sqlite3."""
  NAME = 'RestoreThread'
  _ENTITIES_DONE = 'Entities Done'

  def __init__(self, queue, filename):
    _ThreadBase.__init__(self)
    self.queue = queue
    self.filename = filename

  def PerformWork(self):
    db_conn = sqlite3.connect(self.filename)
    cursor = db_conn.cursor()
    cursor.execute('select id, value from result')
    for entity_id, value in cursor:
      self.queue.put(value, block=True)
    self.queue.put(RestoreThread._ENTITIES_DONE, block=True)


class RestoreLoader(Loader):
  """A Loader which imports protobuffers from a file."""

  def __init__(self, kind, app_id):
    self.kind = kind
    self.app_id = app_id




    self.namespace = namespace_manager.get_namespace()

  def initialize(self, filename, loader_opts):
    CheckFile(filename)
    self.queue = Queue.Queue(1000)
    restore_thread = RestoreThread(self.queue, filename)
    restore_thread.start()
    self.high_id_table = self._find_high_id(self.generate_records(filename))
    restore_thread = RestoreThread(self.queue, filename)
    restore_thread.start()

  def get_high_ids(self):
    return dict(self.high_id_table)

  def _find_high_id(self, record_generator):
    """Find the highest numeric id used for each ancestor-path, kind pair.

    Args:
      record_generator: A generator of entity_encoding strings.

    Returns:
      A map from ancestor-path to maps from kind to id. {path : {kind : id}}
    """
    high_id = {}
    for values in record_generator:
      entity = self.create_entity(values)
      key = entity.key()

      if not key.id():
        continue
      kind = key.kind()
      ancestor_path = []
      if key.parent():
        ancestor_path = key.parent().to_path()
      if tuple(ancestor_path) not in high_id:
        high_id[tuple(ancestor_path)] = {}
      kind_map = high_id[tuple(ancestor_path)]
      if kind not in kind_map or kind_map[kind] < key.id():
        kind_map[kind] = key.id()
    return high_id

  def generate_records(self, filename):
    while True:
      record = self.queue.get(block=True)
      if id(record) == id(RestoreThread._ENTITIES_DONE):
        break
      entity_proto = entity_pb.EntityProto(contents=str(record))
      fixed_entity_proto = self._translate_entity_proto(entity_proto)
      yield datastore.Entity._FromPb(fixed_entity_proto)

  def create_entity(self, values, key_name=None, parent=None):
    return values

  def rewrite_reference_proto(self, entity_namespace, reference_proto):
    """Transform the Reference protobuffer which underlies keys and references.

    Args:
      entity_namespace: The 'before' namespace of the entity that has this
        reference property.  If this value does not match the reference
        properties current namespace, then the reference property namespace will
        not be modified.
      reference_proto: A Onestore Reference proto
    """
    reference_proto.set_app(self.app_id)
    if entity_namespace != reference_proto.name_space():
      return

    if self.namespace:
      reference_proto.set_name_space(self.namespace)
    else:
      reference_proto.clear_name_space()

  def _translate_entity_proto(self, entity_proto):
    """Transform the ReferenceProperties of the given entity to fix app_id."""
    entity_key = entity_proto.mutable_key()
    entity_key.set_app(self.app_id)
    original_entity_namespace = entity_key.name_space()
    if self.namespace:
      entity_key.set_name_space(self.namespace)
    else:
      entity_key.clear_name_space()

    for prop in entity_proto.property_list():
      prop_value = prop.mutable_value()
      if prop_value.has_referencevalue():
        self.rewrite_reference_proto(original_entity_namespace,
                                     prop_value.mutable_referencevalue())

    for prop in entity_proto.raw_property_list():
      prop_value = prop.mutable_value()
      if prop_value.has_referencevalue():
        self.rewrite_reference_proto(original_entity_namespace,
                                     prop_value.mutable_referencevalue())

    return entity_proto


class Exporter(object):
  """A base class for serializing datastore entities.

  To add a handler for exporting an entity kind from your datastore,
  write a subclass of this class that calls Exporter.__init__ from your
  class's __init__.

  If you need to run extra code to convert entities from the input
  data, create new properties, or otherwise modify the entities before
  they're inserted, override handle_entity.

  See the output_entities method for the writing of data from entities.
  """

  __exporters = {}
  kind = None
  __properties = None
  calculate_sort_key_from_entity = False

  def __init__(self, kind, properties):
    """Constructor.

    Populates this Exporters's kind and properties map.

    Args:
      kind: a string containing the entity kind that this exporter handles

      properties: list of (name, converter, default) tuples.

      This is used to automatically convert the entities to strings.
      The converter should be a function that takes one argument, a property
      value of the appropriate type, and returns a str or unicode.  The default
      is a string to be used if the property is not present, or None to fail
      with an error if the property is missing.

      For example:
        [('name', str, None),
         ('id_number', str, None),
         ('email', str, ''),
         ('user', str, None),
         ('birthdate',
          lambda x: str(datetime.datetime.fromtimestamp(float(x))),
          None),
         ('description', str, ''),
         ]
    """
    Validate(kind, basestring)
    self.kind = kind


    GetImplementationClass(kind)

    Validate(properties, list)
    for name, fn, default in properties:
      Validate(name, basestring)
      assert callable(fn), (
          'Conversion function %s for property %s is not callable.' % (
              fn, name))
      if default:
        Validate(default, basestring)

    self.__properties = properties

  @staticmethod
  def RegisterExporter(exporter):
    """Register exporter and the Exporter instance for its kind.

    Args:
      exporter: A Exporter instance.
    """
    Exporter.__exporters[exporter.kind] = exporter

  def __ExtractProperties(self, entity):
    """Converts an entity into a list of string values.

    Args:
      entity: An entity to extract the properties from.

    Returns:
      A list of the properties of the entity.

    Raises:
      MissingPropertyError: if an expected field on the entity is missing.
    """
    encoding = []
    for name, fn, default in self.__properties:
      try:
        encoding.append(fn(entity[name]))
      except KeyError:
        if name == '__key__':
          encoding.append(fn(entity.key()))
        elif default is None:
          raise MissingPropertyError(name)
        else:
          encoding.append(default)
    return encoding

  def __EncodeEntity(self, entity):
    """Convert the given entity into CSV string.

    Args:
      entity: The entity to encode.

    Returns:
      A CSV string.
    """
    output = StringIO.StringIO()
    writer = csv.writer(output)
    writer.writerow(self.__ExtractProperties(entity))
    return output.getvalue()

  def __SerializeEntity(self, entity):
    """Creates a string representation of an entity.

    Args:
      entity: The entity to serialize.

    Returns:
      A serialized representation of an entity.
    """
    encoding = self.__EncodeEntity(entity)
    if not isinstance(encoding, unicode):
      encoding = unicode(encoding, 'utf-8')
    encoding = encoding.encode('utf-8')
    return encoding

  def output_entities(self, entity_generator):
    """Outputs the downloaded entities.

    This implementation writes CSV.

    Args:
      entity_generator: A generator that yields the downloaded entities
        in key order.
    """
    CheckOutputFile(self.output_filename)
    output_file = open(self.output_filename, 'w')
    logger.debug('Export complete, writing to file')
    output_file.writelines(self.__SerializeEntity(entity)
                           for entity in entity_generator)

  def initialize(self, filename, exporter_opts):
    """Performs initialization and validation of the output file.

    This implementation checks that the input file exists and can be
    opened for writing.

    Args:
      filename: The string given as the --filename flag argument.
      exporter_opts: The string given as the --exporter_opts flag argument.
    """
    CheckOutputFile(filename)
    self.output_filename = filename

  def finalize(self):
    """Performs finalization actions after the download completes."""
    pass

  def sort_key_from_entity(self, entity):
    """A value to alter sorting of entities in output_entities entity_generator.

    Will only be called if calculate_sort_key_from_entity is true.
    Args:
      entity: A datastore.Entity.
    Returns:
      A value to store in the intermediate sqlite table. The table will later
      be sorted by this value then by the datastore key, so the sort_key need
      not be unique.
    """
    return ''

  @staticmethod
  def RegisteredExporters():
    """Returns a dictionary of the exporter instances that have been created."""

    return dict(Exporter.__exporters)

  @staticmethod
  def RegisteredExporter(kind):
    """Returns an exporter instance for the given kind if it exists."""
    return Exporter.__exporters[kind]


class DumpExporter(Exporter):
  """An exporter which dumps protobuffers to a file."""

  def __init__(self, kind, result_db_filename):
    self.kind = kind
    self.result_db_filename = result_db_filename

  def output_entities(self, entity_generator):

    shutil.copyfile(self.result_db_filename, self.output_filename)


class MapperRetry(Error):
  """An exception that indicates a non-fatal error during mapping."""


class Mapper(object):
  """A base class for serializing datastore entities.

  To add a handler for exporting an entity kind from your datastore,
  write a subclass of this class that calls Mapper.__init__ from your
  class's __init__.

  You need to implement to batch_apply or apply method on your subclass
  for the map to do anything.
  """

  __mappers = {}
  kind = None

  def __init__(self, kind):
    """Constructor.

    Populates this Mappers's kind.

    Args:
      kind: a string containing the entity kind that this mapper handles
    """
    Validate(kind, basestring)
    self.kind = kind


    GetImplementationClass(kind)

  @staticmethod
  def RegisterMapper(mapper):
    """Register mapper and the Mapper instance for its kind.

    Args:
      mapper: A Mapper instance.
    """
    Mapper.__mappers[mapper.kind] = mapper

  def initialize(self, mapper_opts):
    """Performs initialization.

    Args:
      mapper_opts: The string given as the --mapper_opts flag argument.
    """
    pass

  def finalize(self):
    """Performs finalization actions after the download completes."""
    pass

  def apply(self, entity):
    print 'Default map function doing nothing to %s' % entity

  def batch_apply(self, entities):
    for entity in entities:
      self.apply(entity)

  def map_over_keys_only(self):
    """Return whether this mapper should iterate over only keys or not.

    Override this method in subclasses to return True values.

    Returns:
      True or False
    """
    return False

  @staticmethod
  def RegisteredMappers():
    """Returns a dictionary of the mapper instances that have been created."""

    return dict(Mapper.__mappers)

  @staticmethod
  def RegisteredMapper(kind):
    """Returns an mapper instance for the given kind if it exists."""
    return Mapper.__mappers[kind]


class QueueJoinThread(threading.Thread):
  """A thread that joins a queue and exits.

  Queue joins do not have a timeout.  To simulate a queue join with
  timeout, run this thread and join it with a timeout.
  """

  def __init__(self, queue):
    """Initialize a QueueJoinThread.

    Args:
      queue: The queue for this thread to join.
    """
    threading.Thread.__init__(self)
    assert isinstance(queue, (Queue.Queue, ReQueue))
    self.queue = queue

  def run(self):
    """Perform the queue join in this thread."""
    self.queue.join()


def InterruptibleQueueJoin(queue,
                           thread_local,
                           thread_pool,
                           queue_join_thread_factory=QueueJoinThread,
                           check_workers=True):
  """Repeatedly joins the given ReQueue or Queue.Queue with short timeout.

  Between each timeout on the join, worker threads are checked.

  Args:
    queue: A Queue.Queue or ReQueue instance.
    thread_local: A threading.local instance which indicates interrupts.
    thread_pool: An AdaptiveThreadPool instance.
    queue_join_thread_factory: Used for dependency injection.
    check_workers: Whether to interrupt the join on worker death.

  Returns:
    True unless the queue join is interrupted by SIGINT or worker death.
  """
  thread = queue_join_thread_factory(queue)
  thread.start()
  while True:
    thread.join(timeout=.5)
    if not thread.isAlive():
      return True
    if thread_local.shut_down:
      logger.debug('Queue join interrupted')
      return False
    if check_workers:
      for worker_thread in thread_pool.Threads():
        if not worker_thread.isAlive():
          return False


def ShutdownThreads(data_source_thread, thread_pool):
  """Shuts down the worker and data source threads.

  Args:
    data_source_thread: A running DataSourceThread instance.
    thread_pool: An AdaptiveThreadPool instance with workers registered.
  """
  logger.info('An error occurred. Shutting down...')


  data_source_thread.exit_flag = True

  thread_pool.Shutdown()






  data_source_thread.join(timeout=3.0)
  if data_source_thread.isAlive():




    logger.warn('%s hung while trying to exit',
                data_source_thread.GetFriendlyName())


class BulkTransporterApp(object):
  """Class to wrap bulk transport application functionality."""

  def __init__(self,
               arg_dict,
               input_generator_factory,
               throttle,
               progress_db,
               progresstrackerthread_factory,
               max_queue_size=DEFAULT_QUEUE_SIZE,
               request_manager_factory=RequestManager,
               datasourcethread_factory=DataSourceThread,
               progress_queue_factory=Queue.Queue,
               thread_pool_factory=adaptive_thread_pool.AdaptiveThreadPool,
               server=None):
    """Instantiate a BulkTransporterApp.

    Uploads or downloads data to or from application using HTTP requests.
    When run, the class will spin up a number of threads to read entities
    from the data source, pass those to a number of worker threads
    for sending to the application, and track all of the progress in a
    small database in case an error or pause/termination requires a
    restart/resumption of the upload process.

    Args:
      arg_dict: Dictionary of command line options.
      input_generator_factory: A factory that creates a WorkItem generator.
      throttle: A Throttle instance.
      progress_db: The database to use for replaying/recording progress.
      progresstrackerthread_factory: Used for dependency injection.
      max_queue_size: Maximum size of the queues before they should block.
      request_manager_factory: Used for dependency injection.
      datasourcethread_factory: Used for dependency injection.
      progress_queue_factory: Used for dependency injection.
      thread_pool_factory: Used for dependency injection.
      server: An existing AbstractRpcServer to reuse.
    """
    self.app_id = arg_dict['application']
    self.post_url = arg_dict['url']
    self.kind = arg_dict['kind']
    self.batch_size = arg_dict['batch_size']
    self.input_generator_factory = input_generator_factory
    self.num_threads = arg_dict['num_threads']
    self.email = arg_dict['email']
    self.passin = arg_dict['passin']
    self.dry_run = arg_dict['dry_run']
    self.throttle_class = arg_dict['throttle_class']
    self.throttle = throttle
    self.progress_db = progress_db
    self.progresstrackerthread_factory = progresstrackerthread_factory
    self.max_queue_size = max_queue_size
    self.request_manager_factory = request_manager_factory
    self.datasourcethread_factory = datasourcethread_factory
    self.progress_queue_factory = progress_queue_factory
    self.thread_pool_factory = thread_pool_factory
    self.server = server
    (scheme,
     self.host_port, self.url_path,
     unused_query, unused_fragment) = urlparse.urlsplit(self.post_url)
    self.secure = (scheme == 'https')

  def RunPostAuthentication(self):
    """Method that gets called after authentication."""
    if isinstance(self.kind, basestring):
      return [self.kind]
    return self.kind

  def Run(self):
    """Perform the work of the BulkTransporterApp.

    Raises:
      AuthenticationError: If authentication is required and fails.

    Returns:
      Error code suitable for sys.exit, e.g. 0 on success, 1 on failure.
    """
    self.error = False
    thread_pool = self.thread_pool_factory(
        self.num_threads, queue_size=self.max_queue_size)

    progress_queue = self.progress_queue_factory(self.max_queue_size)
    self.request_manager = self.request_manager_factory(self.app_id,
                                                        self.host_port,
                                                        self.url_path,
                                                        self.kind,
                                                        self.throttle,
                                                        self.batch_size,
                                                        self.secure,
                                                        self.email,
                                                        self.passin,
                                                        self.dry_run,
                                                        self.server,
                                                        self.throttle_class)
    try:


      self.request_manager.Authenticate()
    except Exception, e:
      self.error = True


      if not isinstance(e, urllib2.HTTPError) or (
          e.code != 302 and e.code != 401):
        logger.exception('Exception during authentication')
      raise AuthenticationError()
    if (self.request_manager.auth_called and
        not self.request_manager.authenticated):


      self.error = True
      raise AuthenticationError('Authentication failed')

    kinds = self.RunPostAuthentication()

    for thread in thread_pool.Threads():
      self.throttle.Register(thread)

    self.progress_thread = self.progresstrackerthread_factory(
        progress_queue, self.progress_db)

    if self.progress_db.UseProgressData():
      logger.debug('Restarting upload using progress database')
      progress_generator_factory = self.progress_db.GetProgressStatusGenerator
    else:
      progress_generator_factory = None

    self.data_source_thread = (
        self.datasourcethread_factory(self.request_manager,
                                      kinds,
                                      thread_pool,
                                      progress_queue,
                                      self.input_generator_factory,
                                      progress_generator_factory))



    self.throttle.Register(self.data_source_thread)


    thread_local = threading.local()
    thread_local.shut_down = False

    def Interrupt(unused_signum, unused_frame):
      """Shutdown gracefully in response to a signal."""
      thread_local.shut_down = True
      self.error = True

    signal.signal(signal.SIGINT, Interrupt)


    self.progress_thread.start()
    self.data_source_thread.start()



    while not thread_local.shut_down:





      self.data_source_thread.join(timeout=0.25)


      if self.data_source_thread.isAlive():


        for thread in list(thread_pool.Threads()) + [self.progress_thread]:
          if not thread.isAlive():
            logger.info('Unexpected thread death: %s', thread.getName())
            thread_local.shut_down = True
            self.error = True
            break
      else:

        break

    def _Join(ob, msg):
      logger.debug('Waiting for %s...', msg)

      if isinstance(ob, threading.Thread):
        ob.join(timeout=3.0)
        if ob.isAlive():
          logger.debug('Joining %s failed', ob)
        else:
          logger.debug('... done.')
      elif isinstance(ob, (Queue.Queue, ReQueue)):
        if not InterruptibleQueueJoin(ob, thread_local, thread_pool):
          ShutdownThreads(self.data_source_thread, thread_pool)
      else:
        ob.join()
        logger.debug('... done.')


    if self.data_source_thread.error or thread_local.shut_down:
      ShutdownThreads(self.data_source_thread, thread_pool)
    else:

      _Join(thread_pool.requeue, 'worker threads to finish')

    thread_pool.Shutdown()

    thread_pool.JoinThreads()
    thread_pool.CheckErrors()
    print ''





    if self.progress_thread.isAlive():
      InterruptibleQueueJoin(progress_queue, thread_local, thread_pool,
                             check_workers=False)
    else:
      logger.warn('Progress thread exited prematurely')



    progress_queue.put(_THREAD_SHOULD_EXIT)
    _Join(self.progress_thread, 'progress_thread to terminate')
    self.progress_thread.CheckError()
    if not thread_local.shut_down:
      self.progress_thread.WorkFinished()


    self.data_source_thread.CheckError()

    return self.ReportStatus()

  def ReportStatus(self):
    """Display a message reporting the final status of the transfer."""
    raise NotImplementedError()


class BulkUploaderApp(BulkTransporterApp):
  """Class to encapsulate bulk uploader functionality."""

  def __init__(self, *args, **kwargs):
    BulkTransporterApp.__init__(self, *args, **kwargs)

  def RunPostAuthentication(self):
    loader = Loader.RegisteredLoader(self.kind)
    high_id_table = loader.get_high_ids()
    for ancestor_path, kind_map in high_id_table.iteritems():
      for kind, high_id in kind_map.iteritems():
        self.request_manager.IncrementId(list(ancestor_path), kind, high_id)
    return [self.kind]

  def ReportStatus(self):
    """Display a message reporting the final status of the transfer."""
    total_up, duration = self.throttle.TotalTransferred(
        remote_api_throttle.BANDWIDTH_UP)
    s_total_up, unused_duration = self.throttle.TotalTransferred(
        remote_api_throttle.HTTPS_BANDWIDTH_UP)
    total_up += s_total_up
    total = total_up
    logger.info('%d entities total, %d previously transferred',
                self.data_source_thread.read_count,
                self.data_source_thread.xfer_count)
    transfer_count = self.progress_thread.EntitiesTransferred()
    logger.info('%d entities (%d bytes) transferred in %.1f seconds',
                transfer_count, total, duration)
    if (self.data_source_thread.read_all and
        transfer_count +
        self.data_source_thread.xfer_count >=
        self.data_source_thread.read_count):
      logger.info('All entities successfully transferred')
      return 0
    else:
      logger.info('Some entities not successfully transferred')
      return 1


class BulkDownloaderApp(BulkTransporterApp):
  """Class to encapsulate bulk downloader functionality."""

  def __init__(self, *args, **kwargs):
    BulkTransporterApp.__init__(self, *args, **kwargs)

  def RunPostAuthentication(self):
    if not self.kind:
      return self.request_manager.GetSchemaKinds()
    elif isinstance(self.kind, basestring):
      return [self.kind]
    else:
      return self.kind

  def ReportStatus(self):
    """Display a message reporting the final status of the transfer."""
    total_down, duration = self.throttle.TotalTransferred(
        remote_api_throttle.BANDWIDTH_DOWN)
    s_total_down, unused_duration = self.throttle.TotalTransferred(
        remote_api_throttle.HTTPS_BANDWIDTH_DOWN)
    total_down += s_total_down
    total = total_down
    existing_count = self.progress_thread.existing_count
    xfer_count = self.progress_thread.EntitiesTransferred()
    logger.info('Have %d entities, %d previously transferred',
                xfer_count, existing_count)
    logger.info('%d entities (%d bytes) transferred in %.1f seconds',
                xfer_count, total, duration)
    if self.error:
      return 1
    else:
      return 0


class BulkMapperApp(BulkTransporterApp):
  """Class to encapsulate bulk map functionality."""

  def __init__(self, *args, **kwargs):
    BulkTransporterApp.__init__(self, *args, **kwargs)

  def ReportStatus(self):
    """Display a message reporting the final status of the transfer."""
    total_down, duration = self.throttle.TotalTransferred(
        remote_api_throttle.BANDWIDTH_DOWN)
    s_total_down, unused_duration = self.throttle.TotalTransferred(
        remote_api_throttle.HTTPS_BANDWIDTH_DOWN)
    total_down += s_total_down
    total = total_down
    xfer_count = self.progress_thread.EntitiesTransferred()
    logger.info('The following may be inaccurate if any mapper tasks '
                'encountered errors and had to be retried.')
    logger.info('Applied mapper to %s entities.',
                 xfer_count)
    logger.info('%s entities (%s bytes) transferred in %.1f seconds',
                 xfer_count, total, duration)
    if self.error:
      return 1
    else:
      return 0


def PrintUsageExit(code):
  """Prints usage information and exits with a status code.

  Args:
    code: Status code to pass to sys.exit() after displaying usage information.
  """
  print __doc__ % {'arg0': sys.argv[0]}
  sys.stdout.flush()
  sys.stderr.flush()
  sys.exit(code)


REQUIRED_OPTION = object()


BOOL_ARGS = ('create_config', 'debug', 'download', 'dry_run', 'dump',
             'has_header', 'map', 'passin', 'restore')
INT_ARGS = ('bandwidth_limit', 'batch_size', 'http_limit', 'num_threads',
            'rps_limit')
FILENAME_ARGS = ('config_file', 'db_filename', 'filename', 'log_file',
                 'result_db_filename')
STRING_ARGS = ('application', 'auth_domain', 'email', 'exporter_opts',
               'kind', 'loader_opts', 'mapper_opts', 'namespace', 'url')
DEPRECATED_OPTIONS = {'csv_has_header': 'has_header', 'app_id': 'application'}
FLAG_SPEC = (['csv_has_header', 'help', 'app_id='] +
             list(BOOL_ARGS) +
             [arg + '=' for arg in INT_ARGS + FILENAME_ARGS + STRING_ARGS])

def ParseArguments(argv, die_fn=lambda: PrintUsageExit(1)):
  """Parses command-line arguments.

  Prints out a help message if -h or --help is supplied.

  Args:
    argv: List of command-line arguments.
    die_fn: Function to invoke to end the program.

  Returns:
    A dictionary containing the value of command-line options.
  """
  opts, unused_args = getopt.getopt(
      argv[1:],
      'h',
      FLAG_SPEC)

  arg_dict = {}

  arg_dict['url'] = REQUIRED_OPTION
  arg_dict['filename'] = None
  arg_dict['config_file'] = None
  arg_dict['kind'] = None

  arg_dict['batch_size'] = None
  arg_dict['num_threads'] = DEFAULT_THREAD_COUNT
  arg_dict['bandwidth_limit'] = DEFAULT_BANDWIDTH_LIMIT
  arg_dict['rps_limit'] = DEFAULT_RPS_LIMIT
  arg_dict['http_limit'] = DEFAULT_REQUEST_LIMIT

  arg_dict['application'] = ''
  arg_dict['auth_domain'] = 'gmail.com'
  arg_dict['create_config'] = False
  arg_dict['db_filename'] = None
  arg_dict['debug'] = False
  arg_dict['download'] = False
  arg_dict['dry_run'] = False
  arg_dict['dump'] = False
  arg_dict['email'] = None
  arg_dict['exporter_opts'] = None
  arg_dict['has_header'] = False
  arg_dict['loader_opts'] = None
  arg_dict['log_file'] = None
  arg_dict['map'] = False
  arg_dict['mapper_opts'] = None
  arg_dict['namespace'] = ''
  arg_dict['passin'] = False
  arg_dict['restore'] = False
  arg_dict['result_db_filename'] = None
  arg_dict['throttle_class'] = None

  def ExpandFilename(filename):
    """Expand shell variables and ~usernames in filename."""
    return os.path.expandvars(os.path.expanduser(filename))

  for option, value in opts:
    if option in ('-h', '--help'):
      PrintUsageExit(0)
    if not option.startswith('--'):

      continue
    option = option[2:]
    if option in DEPRECATED_OPTIONS:
      print >>sys.stderr, ('--%s is deprecated, please use --%s.' %
                           (option, DEPRECATED_OPTIONS[option]))
      option = DEPRECATED_OPTIONS[option]

    if option in BOOL_ARGS:
      arg_dict[option] = True
    elif option in INT_ARGS:
      arg_dict[option] = int(value)
    elif option in FILENAME_ARGS:
      arg_dict[option] = ExpandFilename(value)
    elif option in STRING_ARGS:
      arg_dict[option] = value

  return ProcessArguments(arg_dict, die_fn=die_fn)


def ThrottleLayout(bandwidth_limit, http_limit, rps_limit):
  """Return a dictionary indicating the throttle options."""
  bulkloader_limits = dict(remote_api_throttle.NO_LIMITS)
  bulkloader_limits.update({
      remote_api_throttle.BANDWIDTH_UP: bandwidth_limit,
      remote_api_throttle.BANDWIDTH_DOWN: bandwidth_limit,
      remote_api_throttle.REQUESTS: http_limit,
      remote_api_throttle.HTTPS_BANDWIDTH_UP: bandwidth_limit,
      remote_api_throttle.HTTPS_BANDWIDTH_DOWN: bandwidth_limit,
      remote_api_throttle.HTTPS_REQUESTS: http_limit,
      remote_api_throttle.ENTITIES_FETCHED: rps_limit,
      remote_api_throttle.ENTITIES_MODIFIED: rps_limit,
  })
  return bulkloader_limits


def CheckOutputFile(filename):
  """Check that the given file does not exist and can be opened for writing.

  Args:
    filename: The name of the file.

  Raises:
    FileExistsError: if the given filename is not found
    FileNotWritableError: if the given filename is not readable.
    """
  full_path = os.path.abspath(filename)
  if os.path.exists(full_path):
    raise FileExistsError('%s: output file exists' % filename)
  elif not os.access(os.path.dirname(full_path), os.W_OK):
    raise FileNotWritableError(
        '%s: not writable' % os.path.dirname(full_path))


def LoadYamlConfig(config_file_name):
  """Loads a config file and registers any Loader classes present.

  Used for a the second generation Yaml configuration file.

  Args:
    config_file_name: The name of the configuration file.
  """
  (loaders, exporters) = bulkloader_config.load_config(config_file_name,
                                                       increment_id=IncrementId)
  for cls in loaders:
    Loader.RegisterLoader(cls())
  for cls in exporters:
    Exporter.RegisterExporter(cls())


def LoadConfig(config_file_name, exit_fn=sys.exit):
  """Loads a config file and registers any Loader classes present.

  Used for a legacy Python configuration file.

  Args:
    config_file_name: The name of the configuration file.
    exit_fn: Used for dependency injection.
  """
  if config_file_name:
    config_file = open(config_file_name, 'r')

    try:



      bulkloader_config = imp.load_module(
          'bulkloader_config', config_file, config_file_name,
          ('', 'r', imp.PY_SOURCE))
      sys.modules['bulkloader_config'] = bulkloader_config



      if hasattr(bulkloader_config, 'loaders'):
        for cls in bulkloader_config.loaders:
          Loader.RegisterLoader(cls())

      if hasattr(bulkloader_config, 'exporters'):
        for cls in bulkloader_config.exporters:
          Exporter.RegisterExporter(cls())

      if hasattr(bulkloader_config, 'mappers'):
        for cls in bulkloader_config.mappers:
          Mapper.RegisterMapper(cls())

    except NameError, e:


      m = re.search(r"[^']*'([^']*)'.*", str(e))
      if m.groups() and m.group(1) == 'Loader':
        print >>sys.stderr, """
The config file format has changed and you appear to be using an old-style
config file.  Please make the following changes:

1. At the top of the file, add this:

from google.appengine.tools.bulkloader import Loader

2. For each of your Loader subclasses add the following at the end of the
   __init__ definitioion:

self.alias_old_names()

3. At the bottom of the file, add this:

loaders = [MyLoader1,...,MyLoaderN]

Where MyLoader1,...,MyLoaderN are the Loader subclasses you want the bulkloader
to have access to.
"""
        exit_fn(1)
      else:
        raise
    except Exception, e:



      if isinstance(e, NameClashError) or 'bulkloader_config' in vars() and (
          hasattr(bulkloader_config, 'bulkloader') and
          isinstance(e, bulkloader_config.bulkloader.NameClashError)):
        print >> sys.stderr, (
            'Found both %s and %s while aliasing old names on %s.'%
            (e.old_name, e.new_name, e.klass))
        exit_fn(1)
      else:
        raise

def GetArgument(kwargs, name, die_fn):
  """Get the value of the key name in kwargs, or die with die_fn.

  Args:
    kwargs: A dictionary containing the options for the bulkloader.
    name: The name of a bulkloader option.
    die_fn: The function to call to exit the program.

  Returns:
    The value of kwargs[name] is name in kwargs
  """
  if name in kwargs:
    return kwargs[name]
  else:
    print >>sys.stderr, '%s argument required' % name
    die_fn()


def _MakeSignature(app_id=None,
                   url=None,
                   kind=None,
                   db_filename=None,
                   perform_map=None,
                   download=None,
                   has_header=None,
                   result_db_filename=None,
                   dump=None,
                   restore=None):
  """Returns a string that identifies the important options for the database."""

  if download:
    result_db_line = 'result_db: %s' % result_db_filename
  else:
    result_db_line = ''
  return u"""
  app_id: %s
  url: %s
  kind: %s
  download: %s
  map: %s
  dump: %s
  restore: %s
  progress_db: %s
  has_header: %s
  %s
  """ % (app_id, url, kind, download, perform_map, dump, restore, db_filename,
         has_header, result_db_line)


def ProcessArguments(arg_dict,
                     die_fn=lambda: sys.exit(1)):
  """Processes non command-line input arguments.

  Args:
    arg_dict: Dictionary containing the values of bulkloader options.
    die_fn: Function to call in case of an error during argument processing.

  Returns:
    A dictionary of bulkloader options.
  """


  unused_application = GetArgument(arg_dict, 'application', die_fn)
  url = GetArgument(arg_dict, 'url', die_fn)
  dump = GetArgument(arg_dict, 'dump', die_fn)
  restore = GetArgument(arg_dict, 'restore', die_fn)
  create_config = GetArgument(arg_dict, 'create_config', die_fn)
  filename = GetArgument(arg_dict, 'filename', die_fn)
  batch_size = GetArgument(arg_dict, 'batch_size', die_fn)
  kind = GetArgument(arg_dict, 'kind', die_fn)
  db_filename = GetArgument(arg_dict, 'db_filename', die_fn)
  config_file = GetArgument(arg_dict, 'config_file', die_fn)
  result_db_filename = GetArgument(arg_dict, 'result_db_filename', die_fn)
  download = GetArgument(arg_dict, 'download', die_fn)
  log_file = GetArgument(arg_dict, 'log_file', die_fn)
  perform_map = GetArgument(arg_dict, 'map', die_fn)
  namespace = GetArgument(arg_dict, 'namespace', die_fn)

  errors = []

  if batch_size is None:
    if download or perform_map or dump or create_config:
      arg_dict['batch_size'] = DEFAULT_DOWNLOAD_BATCH_SIZE
    else:
      arg_dict['batch_size'] = DEFAULT_BATCH_SIZE
  elif batch_size <= 0:
    errors.append('batch_size must be at least 1')

  if db_filename is None:
    arg_dict['db_filename'] = time.strftime(
        'bulkloader-progress-%Y%m%d.%H%M%S.sql3')

  if result_db_filename is None:
    arg_dict['result_db_filename'] = time.strftime(
        'bulkloader-results-%Y%m%d.%H%M%S.sql3')

  if log_file is None:
    arg_dict['log_file'] = time.strftime('bulkloader-log-%Y%m%d.%H%M%S')

  required = '%s argument required'


  if config_file is None and not dump and not restore and not create_config:
    errors.append('One of --config_file, --dump, --restore, or --create_config '
                  'is required')

  if url is REQUIRED_OPTION:
    errors.append(required % 'url')

  if not filename and not perform_map:
    errors.append(required % 'filename')

  if not kind:
    if download or perform_map:
      errors.append('kind argument required for this operation')
    elif not dump and not restore and not create_config:
      errors.append(
          'kind argument required unless --dump, --restore or --create_config '
          'specified')

  if namespace:
    try:
      namespace_manager.validate_namespace(namespace)
    except namespace_manager.BadValueError, msg:
      errors.append('namespace parameter %s' % msg)


  POSSIBLE_COMMANDS = ('create_config', 'download', 'dump', 'map', 'restore')
  commands = []
  for command in POSSIBLE_COMMANDS:
    if arg_dict[command]:
      commands.append(command)
  if len(commands) > 1:
    errors.append('%s are mutually exclusive.' % ' and '.join(commands))




  if errors:
    print >>sys.stderr, '\n'.join(errors)
    die_fn()

  return arg_dict


def _GetRemoteAppId(url, throttle, email, passin,
                    raw_input_fn=raw_input, password_input_fn=getpass.getpass,
                    throttle_class=None):
  """Get the App ID from the remote server."""
  scheme, host_port, url_path, _, _ = urlparse.urlsplit(url)

  secure = (scheme == 'https')

  throttled_rpc_server_factory = (
      remote_api_throttle.ThrottledHttpRpcServerFactory(
            throttle, throttle_class=throttle_class))

  def AuthFunction():
    return _AuthFunction(host_port, email, passin, raw_input_fn,
                         password_input_fn)

  app_id, server = remote_api_stub.GetRemoteAppId(
      host_port, url_path, AuthFunction,
      rpc_server_factory=throttled_rpc_server_factory, secure=secure)

  return app_id, server


def ParseKind(kind):
  if kind and kind[0] == '(' and kind[-1] == ')':
    return tuple(kind[1:-1].split(','))
  else:
    return kind


def _PerformBulkload(arg_dict,
                     check_file=CheckFile,
                     check_output_file=CheckOutputFile):
  """Runs the bulkloader, given the command line options.

  Args:
    arg_dict: Dictionary of bulkloader options.
    check_file: Used for dependency injection.
    check_output_file: Used for dependency injection.

  Returns:
    An exit code.

  Raises:
    ConfigurationError: if inconsistent options are passed.
  """
  app_id = arg_dict['application']
  url = arg_dict['url']
  filename = arg_dict['filename']
  batch_size = arg_dict['batch_size']
  kind = arg_dict['kind']
  num_threads = arg_dict['num_threads']
  bandwidth_limit = arg_dict['bandwidth_limit']
  rps_limit = arg_dict['rps_limit']
  http_limit = arg_dict['http_limit']
  db_filename = arg_dict['db_filename']
  config_file = arg_dict['config_file']
  auth_domain = arg_dict['auth_domain']
  has_header = arg_dict['has_header']
  download = arg_dict['download']
  result_db_filename = arg_dict['result_db_filename']
  loader_opts = arg_dict['loader_opts']
  exporter_opts = arg_dict['exporter_opts']
  mapper_opts = arg_dict['mapper_opts']
  email = arg_dict['email']
  passin = arg_dict['passin']
  perform_map = arg_dict['map']
  dump = arg_dict['dump']
  restore = arg_dict['restore']
  create_config = arg_dict['create_config']
  namespace = arg_dict['namespace']
  dry_run = arg_dict['dry_run']
  throttle_class = arg_dict['throttle_class']

  if namespace:
    namespace_manager.set_namespace(namespace)
  os.environ['AUTH_DOMAIN'] = auth_domain

  kind = ParseKind(kind)

  if not dump and not restore and not create_config:

    check_file(config_file)

  if download or dump or create_config:

    check_output_file(filename)
  elif not perform_map:
    check_file(filename)


  throttle_layout = ThrottleLayout(bandwidth_limit, http_limit, rps_limit)
  logger.info('Throttling transfers:')
  logger.info('Bandwidth: %s bytes/second', bandwidth_limit)
  logger.info('HTTP connections: %s/second', http_limit)
  logger.info('Entities inserted/fetched/modified: %s/second', rps_limit)
  logger.info('Batch Size: %s', batch_size)

  throttle = remote_api_throttle.Throttle(layout=throttle_layout)


  throttle.Register(threading.currentThread())
  threading.currentThread().exit_flag = False


  server = None
  if not app_id:
    if dry_run:

      raise ConfigurationError('Must sepcify application ID in dry run mode.')
    app_id, server = _GetRemoteAppId(url, throttle, email, passin,
                                       throttle_class=throttle_class)

    arg_dict['application'] = app_id

  if dump:
    Exporter.RegisterExporter(DumpExporter(kind, result_db_filename))
  elif restore:
    Loader.RegisterLoader(RestoreLoader(kind, app_id))
  elif create_config:

    kind = '__Stat_PropertyType_PropertyName_Kind__'
    arg_dict['kind'] = kind


    root_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(root_dir) == 'tools':
      root_dir = os.path.dirname(os.path.dirname(os.path.dirname(root_dir)))

    LoadYamlConfig(os.path.join(
        root_dir, os.path.normpath(
            'google/appengine/ext/bulkload/bulkloader_wizard.yaml')))
  elif (config_file and
        (config_file.endswith('.yaml') or config_file.endswith('.yml'))):
    LoadYamlConfig(config_file)
  else:
    LoadConfig(config_file)

  os.environ['APPLICATION_ID'] = app_id

  signature = _MakeSignature(app_id=app_id,
                             url=url,
                             kind=kind,
                             db_filename=db_filename,
                             download=download,
                             perform_map=perform_map,
                             has_header=has_header,
                             result_db_filename=result_db_filename,
                             dump=dump,
                             restore=restore)



  max_queue_size = max(DEFAULT_QUEUE_SIZE, 3 * num_threads + 5)

  upload = not (download or dump or restore or perform_map or create_config)

  if db_filename == 'skip':
    progress_db = StubProgressDatabase()
  elif upload or restore:
    progress_db = ProgressDatabase(db_filename, signature)
  else:
    progress_db = ExportProgressDatabase(db_filename, signature)

  return_code = 1

  if upload or restore:
    loader = Loader.RegisteredLoader(kind)
    try:
      loader.initialize(filename, loader_opts)


      workitem_generator_factory = GetCSVGeneratorFactory(
          kind, filename, batch_size, has_header)

      app = BulkUploaderApp(arg_dict,
                            workitem_generator_factory,
                            throttle,
                            progress_db,
                            ProgressTrackerThread,
                            max_queue_size,
                            RequestManager,
                            DataSourceThread,
                            Queue.Queue,
                            server=server)
      try:
        return_code = app.Run()
      except AuthenticationError:
        logger.info('Authentication Failed')
    finally:
      loader.finalize()
  elif download or dump or create_config:
    exporter = Exporter.RegisteredExporter(kind)
    result_db = ResultDatabase(result_db_filename, signature, exporter=exporter)
    try:
      exporter.initialize(filename, exporter_opts)

      def KeyRangeGeneratorFactory(request_manager, progress_queue,
                                   progress_gen, kinds):
        logger.info('Downloading kinds: %s', kinds)
        return KeyRangeItemGenerator(request_manager, kinds, progress_queue,
                                     progress_gen, DownloadItem)

      def ExportProgressThreadFactory(progress_queue, progress_db):
        return ExportProgressThread(exporter,
                                    progress_queue,
                                    progress_db,
                                    result_db)

      app = BulkDownloaderApp(arg_dict,
                              KeyRangeGeneratorFactory,
                              throttle,
                              progress_db,
                              ExportProgressThreadFactory,
                              0,
                              RequestManager,
                              DataSourceThread,
                              Queue.Queue,
                              server=server)
      try:
        return_code = app.Run()
      except AuthenticationError:
        logger.info('Authentication Failed')
      except KindStatError:
        logger.error('Unable to download kind stats for all-kinds download.')
        logger.error('Kind stats are generated periodically by the appserver')
        logger.error('Kind stats are not available on dev_appserver.')
    finally:
      exporter.finalize()
  elif perform_map:
    mapper = Mapper.RegisteredMapper(kind)
    try:
      mapper.initialize(mapper_opts)

      def KeyRangeGeneratorFactory(request_manager, progress_queue,
                                   progress_gen, kinds):
        return KeyRangeItemGenerator(request_manager, kinds, progress_queue,
                                     progress_gen, MapperItem)

      def MapperProgressThreadFactory(progress_queue, progress_db):
        return MapperProgressThread(mapper,
                                    progress_queue,
                                    progress_db)

      app = BulkMapperApp(arg_dict,
                          KeyRangeGeneratorFactory,
                          throttle,
                          progress_db,
                          MapperProgressThreadFactory,
                          0,
                          RequestManager,
                          DataSourceThread,
                          Queue.Queue,
                          server=server)
      try:
        return_code = app.Run()
      except AuthenticationError:
        logger.info('Authentication Failed')
    finally:
      mapper.finalize()
  return return_code


def SetupLogging(arg_dict):
  """Sets up logging for the bulkloader.

  Args:
    arg_dict: Dictionary mapping flag names to their arguments.
  """
  format = '[%(levelname)-8s %(asctime)s %(filename)s] %(message)s'
  debug = arg_dict['debug']
  log_file = arg_dict['log_file']

  logger.setLevel(logging.DEBUG)


  logger.propagate = False


  file_handler = logging.FileHandler(log_file, 'w')
  file_handler.setLevel(logging.DEBUG)
  file_formatter = logging.Formatter(format)
  file_handler.setFormatter(file_formatter)
  logger.addHandler(file_handler)


  console = logging.StreamHandler()
  level = logging.INFO
  if debug:
    level = logging.DEBUG
  console.setLevel(level)
  console_format = '[%(levelname)-8s] %(message)s'
  formatter = logging.Formatter(console_format)
  console.setFormatter(formatter)
  logger.addHandler(console)

  logger.info('Logging to %s', log_file)

  remote_api_throttle.logger.setLevel(level)
  remote_api_throttle.logger.addHandler(file_handler)
  remote_api_throttle.logger.addHandler(console)



  appengine_rpc.logger.setLevel(logging.WARN)

  adaptive_thread_pool.logger.setLevel(logging.DEBUG)
  adaptive_thread_pool.logger.addHandler(console)
  adaptive_thread_pool.logger.addHandler(file_handler)
  adaptive_thread_pool.logger.propagate = False


def Run(arg_dict):
  """Sets up and runs the bulkloader, given the options as keyword arguments.

  Args:
    arg_dict: Dictionary of bulkloader options

  Returns:
    An exit code.
  """
  arg_dict = ProcessArguments(arg_dict)

  SetupLogging(arg_dict)

  return _PerformBulkload(arg_dict)


def main(argv):
  """Runs the importer from the command line."""


  arg_dict = ParseArguments(argv)


  errors = ['%s argument required' % key
            for (key, value) in arg_dict.iteritems()
            if value is REQUIRED_OPTION]
  if errors:
    print >>sys.stderr, '\n'.join(errors)
    PrintUsageExit(1)

  SetupLogging(arg_dict)
  return _PerformBulkload(arg_dict)


if __name__ == '__main__':
  sys.exit(main(sys.argv))
