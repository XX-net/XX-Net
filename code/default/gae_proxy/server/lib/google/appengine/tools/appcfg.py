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
"""Tool for deploying apps to an app server.

Currently, the application only uploads new appversions. To do this, it first
walks the directory tree rooted at the path the user specifies, adding all the
files it finds to a list. It then uploads the application configuration
(app.yaml) to the server using HTTP, followed by uploading each of the files.
It then commits the transaction with another request.

The bulk of this work is handled by the AppVersionUpload class, which exposes
methods to add to the list of files, fetch a list of modified files, upload
files, and commit or rollback the transaction.
"""
from __future__ import with_statement



import calendar
import contextlib
import copy
import datetime
import errno
import hashlib
import logging
import mimetypes
import optparse
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib
import urllib2



import google
from oauth2client import devshell
import yaml

from google.appengine.cron import groctimespecification
from google.appengine.api import appinfo
from google.appengine.api import appinfo_includes
from google.appengine.api import backendinfo
from google.appengine.api import client_deployinfo
from google.appengine.api import croninfo
from google.appengine.api import dispatchinfo
from google.appengine.api import dosinfo
from google.appengine.api import queueinfo
from google.appengine.api import validation
from google.appengine.api import yaml_errors
from google.appengine.api import yaml_object
from google.appengine.datastore import datastore_index
from google.appengine.tools import appengine_rpc

try:


  from google.appengine.tools import appengine_rpc_httplib2
except ImportError:
  appengine_rpc_httplib2 = None
if sys.version_info[:2] >= (2, 7):



  from google.appengine.tools import appcfg_java
else:
  appcfg_java = None

from google.appengine.tools import augment_mimetypes
from google.appengine.tools import bulkloader
from google.appengine.tools import sdk_update_checker



LIST_DELIMITER = '\n'
TUPLE_DELIMITER = '|'
BACKENDS_ACTION = 'backends'
BACKENDS_MESSAGE = ('Warning: This application uses Backends, a deprecated '
                    'feature that has been replaced by Modules, which '
                    'offers additional functionality. Please convert your '
                    'backends to modules as described at: ')
_CONVERTING_URL = (
    'https://developers.google.com/appengine/docs/%s/modules/converting')


MAX_LOG_LEVEL = 4


MAX_BATCH_SIZE = 3200000
MAX_BATCH_COUNT = 100
MAX_BATCH_FILE_SIZE = 200000
BATCH_OVERHEAD = 500






verbosity = 1


PREFIXED_BY_ADMIN_CONSOLE_RE = '^(?:admin-console)(.*)'


SDK_PRODUCT = 'appcfg_py'


DAY = 24*3600
SUNDAY = 6




MEGA = 1024 * 1024
MILLION = 1000 * 1000
DEFAULT_RESOURCE_LIMITS = {
    'max_file_size': 32 * MILLION,
    'max_blob_size': 32 * MILLION,
    'max_files_to_clone': 100,
    'max_total_file_size': 150 * MEGA,
    'max_file_count': 10000,
}

# Client ID and secrets are managed in the Google API console.





APPCFG_CLIENT_ID = '550516889912.apps.googleusercontent.com'
APPCFG_CLIENT_NOTSOSECRET = 'ykPq-0UYfKNprLRjVx1hBBar'
APPCFG_SCOPES = ('https://www.googleapis.com/auth/appengine.admin',
                 'https://www.googleapis.com/auth/cloud-platform',
                 'https://www.googleapis.com/auth/userinfo.email')


STATIC_FILE_PREFIX = '__static__'



METADATA_BASE = 'http://metadata.google.internal'
SERVICE_ACCOUNT_BASE = (
    'computeMetadata/v1beta1/instance/service-accounts/default')


APP_YAML_FILENAME = 'app.yaml'




GO_APP_BUILDER = os.path.join('goroot', 'bin', 'go-app-builder')
if sys.platform.startswith('win'):
  GO_APP_BUILDER += '.exe'

GCLOUD_ONLY_RUNTIMES = set(['custom', 'nodejs'])



augment_mimetypes.init()


class Error(Exception):
  pass


class CannotStartServingError(Error):
  """We could not start serving the version being uploaded."""
  pass


def PrintUpdate(msg, error_fh=sys.stderr):
  """Print a message to stderr or the given file-like object.

  If 'verbosity' is greater than 0, print the message.

  Args:
    msg: The string to print.
    error_fh: Where to send the message.
  """
  if verbosity > 0:
    timestamp = datetime.datetime.now()
    print >>error_fh, '%s %s' % (timestamp.strftime('%I:%M %p'), msg)


def StatusUpdate(msg, error_fh=sys.stderr):
  """Print a status message to stderr or the given file-like object."""
  PrintUpdate(msg, error_fh)


def BackendsStatusUpdate(runtime, error_fh=sys.stderr):
  """Print the Backends status message based on current runtime.

  Args:
    runtime: String name of current runtime.
    error_fh: Where to send the message.
  """
  language = runtime
  if language == 'python27':
    language = 'python'
  elif language == 'java7':
    language = 'java'
  if language == 'python' or language == 'java':
    StatusUpdate(BACKENDS_MESSAGE + (_CONVERTING_URL % language), error_fh)


def ErrorUpdate(msg, error_fh=sys.stderr):
  """Print an error message to stderr."""
  PrintUpdate(msg, error_fh)


def _PrintErrorAndExit(stream, msg, exit_code=2):
  """Prints the given error message and exists the program.

  Args:
    stream: The stream (e.g. StringIO or file) to write the message to.
    msg: The error message to display as a string.
    exit_code: The integer code to pass to sys.exit().
  """
  stream.write(msg)
  sys.exit(exit_code)


def JavaSupported():
  """True if Java is supported by this SDK."""


  if appcfg_java:
    tools_java_dir = os.path.join(os.path.dirname(appcfg_java.__file__), 'java')
    return os.path.isdir(tools_java_dir)
  else:
    return False


@contextlib.contextmanager
def TempChangeField(obj, field_name, new_value):
  """Context manager to change a field value on an object temporarily.

  Args:
    obj: The object to change the field on.
    field_name: The field name to change.
    new_value: The new value.

  Yields:
    The old value.
  """
  old_value = getattr(obj, field_name)
  setattr(obj, field_name, new_value)
  yield old_value
  setattr(obj, field_name, old_value)


class FileClassification(object):
  """A class to hold a file's classification.

  This class both abstracts away the details of how we determine
  whether a file is a regular, static or error file as well as acting
  as a container for various metadata about the file.
  """

  def __init__(self, config, filename, error_fh=sys.stderr):
    """Initializes a FileClassification instance.

    Args:
      config: The app.yaml object to check the filename against.
      filename: The name of the file.
      error_fh: Where to send status and error messages.
    """
    self.__error_fh = error_fh
    self.__static_mime_type = self.__GetMimeTypeIfStaticFile(config, filename)
    self.__static_app_readable = self.__GetAppReadableIfStaticFile(config,
                                                                   filename)
    self.__error_mime_type, self.__error_code = self.__LookupErrorBlob(config,
                                                                       filename)

  def __GetMimeTypeIfStaticFile(self, config, filename):
    """Looks up the mime type for 'filename'.

    Uses the handlers in 'config' to determine if the file should
    be treated as a static file.

    Args:
      config: The app.yaml object to check the filename against.
      filename: The name of the file.

    Returns:
      The mime type string.  For example, 'text/plain' or 'image/gif'.
      None if this is not a static file.
    """
    if self.__FileNameImpliesStaticFile(filename):
      return self.__MimeType(filename)
    for handler in config.handlers:
      handler_type = handler.GetHandlerType()
      if handler_type in ('static_dir', 'static_files'):
        if handler_type == 'static_dir':
          regex = os.path.join(re.escape(handler.GetHandler()), '.*')
        else:
          regex = handler.upload
        if re.match(regex, filename):
          return handler.mime_type or self.__MimeType(filename)
    return None

  @staticmethod
  def __FileNameImpliesStaticFile(filename):
    """True if the name of a file implies that it is a static resource.

    For Java applications specified with web.xml and appengine-web.xml, we
    create a staging directory that includes a __static__ hierarchy containing
    links to all files that are implied static by the contents of those XML
    files. So if a file has been copied into that directory then we can assume
    it is static.

    Args:
      filename: The full path to the file.

    Returns:
      True if the file should be considered a static resource based on its name.
    """
    static = '__static__' + os.sep
    return static in filename

  @staticmethod
  def __GetAppReadableIfStaticFile(config, filename):
    """Looks up whether a static file is readable by the application.

    Uses the handlers in 'config' to determine if the file should
    be treated as a static file and if so, if the file should be readable by the
    application.

    Args:
      config: The AppInfoExternal object to check the filename against.
      filename: The name of the file.

    Returns:
      True if the file is static and marked as app readable, False otherwise.
    """
    for handler in config.handlers:
      handler_type = handler.GetHandlerType()
      if handler_type in ('static_dir', 'static_files'):
        if handler_type == 'static_dir':
          regex = os.path.join(re.escape(handler.GetHandler()), '.*')
        else:
          regex = handler.upload
        if re.match(regex, filename):
          return handler.application_readable
    return False

  def __LookupErrorBlob(self, config, filename):
    """Looks up the mime type and error_code for 'filename'.

    Uses the error handlers in 'config' to determine if the file should
    be treated as an error blob.

    Args:
      config: The app.yaml object to check the filename against.
      filename: The name of the file.

    Returns:

      A tuple of (mime_type, error_code), or (None, None) if this is not an
      error blob.  For example, ('text/plain', default) or ('image/gif',
      timeout) or (None, None).
    """
    if not config.error_handlers:
      return (None, None)
    for error_handler in config.error_handlers:
      if error_handler.file == filename:
        error_code = error_handler.error_code
        error_code = error_code or 'default'
        if error_handler.mime_type:
          return (error_handler.mime_type, error_code)
        else:
          return (self.__MimeType(filename), error_code)
    return (None, None)

  def __MimeType(self, filename, default='application/octet-stream'):
    guess = mimetypes.guess_type(filename)[0]
    if guess is None:
      print >>self.__error_fh, ('Could not guess mimetype for %s.  Using %s.'
                                % (filename, default))
      return default
    return guess

  def IsApplicationFile(self):
    return bool((not self.IsStaticFile() or self.__static_app_readable) and
                not self.IsErrorFile())

  def IsStaticFile(self):
    return bool(self.__static_mime_type)

  def StaticMimeType(self):
    return self.__static_mime_type

  def IsErrorFile(self):
    return bool(self.__error_mime_type)

  def ErrorMimeType(self):
    return self.__error_mime_type

  def ErrorCode(self):
    return self.__error_code


def BuildClonePostBody(file_tuples):
  """Build the post body for the /api/clone{files,blobs,errorblobs} urls.

  Args:
    file_tuples: A list of tuples.  Each tuple should contain the entries
      appropriate for the endpoint in question.

  Returns:
    A string containing the properly delimited tuples.
  """
  file_list = []
  for tup in file_tuples:
    path = tup[1]
    tup = tup[2:]
    file_list.append(TUPLE_DELIMITER.join([path] + list(tup)))
  return LIST_DELIMITER.join(file_list)


def _GetRemoteResourceLimits(logging_context):
  """Get the resource limit as reported by the admin console.

  Get the resource limits by querying the admin_console/appserver. The
  actual limits returned depends on the server we are talking to and
  could be missing values we expect or include extra values.

  Args:
    logging_context: The _ClientDeployLoggingContext for this upload.

  Returns:
    A dictionary.
  """
  try:
    yaml_data = logging_context.Send('/api/appversion/getresourcelimits')

  except urllib2.HTTPError, err:



    if err.code != 404:
      raise
    return {}

  return yaml.safe_load(yaml_data)


def GetResourceLimits(logging_context, error_fh=sys.stderr):
  """Gets the resource limits.

  Gets the resource limits that should be applied to apps. Any values
  that the server does not know about will have their default value
  reported (although it is also possible for the server to report
  values we don't know about).

  Args:
    logging_context: The _ClientDeployLoggingContext for this upload.
    error_fh: Where to send status and error messages.

  Returns:
    A dictionary.
  """
  resource_limits = DEFAULT_RESOURCE_LIMITS.copy()
  StatusUpdate('Getting current resource limits.', error_fh)
  resource_limits.update(_GetRemoteResourceLimits(logging_context))
  logging.debug('Using resource limits: %s', resource_limits)
  return resource_limits


def RetryWithBackoff(callable_func, retry_notify_func,
                     initial_delay=1, backoff_factor=2,
                     max_delay=60, max_tries=20):
  """Calls a function multiple times, backing off more and more each time.

  Args:
    callable_func: A function that performs some operation that should be
      retried a number of times upon failure.  Signature: () -> (done, value)
      If 'done' is True, we'll immediately return (True, value)
      If 'done' is False, we'll delay a bit and try again, unless we've
      hit the 'max_tries' limit, in which case we'll return (False, value).
    retry_notify_func: This function will be called immediately before the
      next retry delay.  Signature: (value, delay) -> None
      'value' is the value returned by the last call to 'callable_func'
      'delay' is the retry delay, in seconds
    initial_delay: Initial delay after first try, in seconds.
    backoff_factor: Delay will be multiplied by this factor after each try.
    max_delay: Maximum delay, in seconds.
    max_tries: Maximum number of tries (the first one counts).

  Returns:
    What the last call to 'callable_func' returned, which is of the form
    (done, value).  If 'done' is True, you know 'callable_func' returned True
    before we ran out of retries.  If 'done' is False, you know 'callable_func'
    kept returning False and we ran out of retries.

  Raises:
    Whatever the function raises--an exception will immediately stop retries.
  """

  delay = initial_delay
  num_tries = 0

  while True:
    done, opaque_value = callable_func()
    num_tries += 1

    if done:
      return True, opaque_value

    if num_tries >= max_tries:
      return False, opaque_value

    retry_notify_func(opaque_value, delay)
    time.sleep(delay)
    delay = min(delay * backoff_factor, max_delay)


def RetryNoBackoff(callable_func,
                   retry_notify_func,
                   delay=5,
                   max_tries=200):
  """Calls a function multiple times, with the same delay each time.

  Args:
    callable_func: A function that performs some operation that should be
      retried a number of times upon failure.  Signature: () -> (done, value)
      If 'done' is True, we'll immediately return (True, value)
      If 'done' is False, we'll delay a bit and try again, unless we've
      hit the 'max_tries' limit, in which case we'll return (False, value).
    retry_notify_func: This function will be called immediately before the
      next retry delay.  Signature: (value, delay) -> None
      'value' is the value returned by the last call to 'callable_func'
      'delay' is the retry delay, in seconds
    delay: Delay between tries, in seconds.
    max_tries: Maximum number of tries (the first one counts).

  Returns:
    What the last call to 'callable_func' returned, which is of the form
    (done, value).  If 'done' is True, you know 'callable_func' returned True
    before we ran out of retries.  If 'done' is False, you know 'callable_func'
    kept returning False and we ran out of retries.

  Raises:
    Whatever the function raises--an exception will immediately stop retries.
  """

  return RetryWithBackoff(callable_func,
                          retry_notify_func,
                          delay,
                          1,
                          delay,
                          max_tries)


def MigratePython27Notice():
  """Tells the user that Python 2.5 runtime is deprecated.

  Encourages the user to migrate from Python 2.5 to Python 2.7.

  Prints a message to sys.stdout. The caller should have tested that the user is
  using Python 2.5, so as not to spuriously display this message.
  """
  ErrorUpdate(
      'WARNING: This application is using the Python 2.5 runtime, which is '
      'deprecated! It should be updated to the Python 2.7 runtime as soon as '
      'possible, which offers performance improvements and many new features. '
      'Learn how simple it is to migrate your application to Python 2.7 at '
      'https://developers.google.com/appengine/docs/python/python25/migrate27.')


class IndexDefinitionUpload(object):
  """Provides facilities to upload index definitions to the hosting service."""

  def __init__(self, rpcserver, definitions, error_fh=sys.stderr):
    """Creates a new DatastoreIndexUpload.

    Args:
      rpcserver: The RPC server to use.  Should be an instance of HttpRpcServer
        or TestRpcServer.
      definitions: An IndexDefinitions object.
      error_fh: Where to send status and error messages.
    """
    self.rpcserver = rpcserver
    self.definitions = definitions
    self.error_fh = error_fh

  def DoUpload(self):
    """Uploads the index definitions."""
    StatusUpdate('Uploading index definitions.', self.error_fh)

    with TempChangeField(self.definitions, 'application', None) as app_id:
      self.rpcserver.Send('/api/datastore/index/add',
                          app_id=app_id,
                          payload=self.definitions.ToYAML())


class CronEntryUpload(object):
  """Provides facilities to upload cron entries to the hosting service."""

  def __init__(self, rpcserver, cron, error_fh=sys.stderr):
    """Creates a new CronEntryUpload.

    Args:
      rpcserver: The RPC server to use.  Should be an instance of a subclass of
      AbstractRpcServer
      cron: The CronInfoExternal object loaded from the cron.yaml file.
      error_fh: Where to send status and error messages.
    """
    self.rpcserver = rpcserver
    self.cron = cron
    self.error_fh = error_fh

  def DoUpload(self):
    """Uploads the cron entries."""
    StatusUpdate('Uploading cron entries.', self.error_fh)

    with TempChangeField(self.cron, 'application', None) as app_id:
      self.rpcserver.Send('/api/cron/update',
                          app_id=app_id,
                          payload=self.cron.ToYAML())


class QueueEntryUpload(object):
  """Provides facilities to upload task queue entries to the hosting service."""

  def __init__(self, rpcserver, queue, error_fh=sys.stderr):
    """Creates a new QueueEntryUpload.

    Args:
      rpcserver: The RPC server to use.  Should be an instance of a subclass of
        AbstractRpcServer
      queue: The QueueInfoExternal object loaded from the queue.yaml file.
      error_fh: Where to send status and error messages.
    """
    self.rpcserver = rpcserver
    self.queue = queue
    self.error_fh = error_fh

  def DoUpload(self):
    """Uploads the task queue entries."""
    StatusUpdate('Uploading task queue entries.', self.error_fh)

    with TempChangeField(self.queue, 'application', None) as app_id:
      self.rpcserver.Send('/api/queue/update',
                          app_id=app_id,
                          payload=self.queue.ToYAML())


class DispatchEntryUpload(object):
  """Provides facilities to upload dispatch entries to the hosting service."""

  def __init__(self, rpcserver, dispatch, error_fh=sys.stderr):
    """Creates a new DispatchEntryUpload.

    Args:
      rpcserver: The RPC server to use.  Should be an instance of a subclass of
        AbstractRpcServer
      dispatch: The DispatchInfoExternal object loaded from the dispatch.yaml
        file.
      error_fh: Where to send status and error messages.
    """
    self.rpcserver = rpcserver
    self.dispatch = dispatch
    self.error_fh = error_fh

  def DoUpload(self):
    """Uploads the dispatch entries."""
    StatusUpdate('Uploading dispatch entries.', self.error_fh)
    self.rpcserver.Send('/api/dispatch/update',
                        app_id=self.dispatch.application,
                        payload=self.dispatch.ToYAML())


class DosEntryUpload(object):
  """Provides facilities to upload dos entries to the hosting service."""

  def __init__(self, rpcserver, dos, error_fh=sys.stderr):
    """Creates a new DosEntryUpload.

    Args:
      rpcserver: The RPC server to use. Should be an instance of a subclass of
        AbstractRpcServer.
      dos: The DosInfoExternal object loaded from the dos.yaml file.
      error_fh: Where to send status and error messages.
    """
    self.rpcserver = rpcserver
    self.dos = dos
    self.error_fh = error_fh

  def DoUpload(self):
    """Uploads the dos entries."""
    StatusUpdate('Uploading DOS entries.', self.error_fh)

    with TempChangeField(self.dos, 'application', None) as app_id:
      self.rpcserver.Send('/api/dos/update',
                          app_id=app_id,
                          payload=self.dos.ToYAML())


class DefaultVersionSet(object):
  """Provides facilities to set the default (serving) version."""

  def __init__(self, rpcserver, app_id, module, version, error_fh=sys.stderr):
    """Creates a new DefaultVersionSet.

    Args:
      rpcserver: The RPC server to use. Should be an instance of a subclass of
        AbstractRpcServer.
      app_id: The application to make the change to.
      module: The module to set the default version of (if any).
      version: The version to set as the default.
      error_fh: Where to send status and error messages.
    """
    self.rpcserver = rpcserver
    self.app_id = app_id
    self.module = module
    self.version = version
    self.error_fh = error_fh

  def SetVersion(self):
    """Sets the default version."""
    if self.module:

      modules = self.module.split(',')
      if len(modules) > 1:
        StatusUpdate('Setting the default version of modules %s of application '
                     '%s to %s.' % (', '.join(modules),
                                    self.app_id,
                                    self.version),
                     self.error_fh)




        params = [('app_id', self.app_id), ('version', self.version)]
        params.extend(('module', module) for module in modules)
        url = '/api/appversion/setdefault?' + urllib.urlencode(sorted(params))
        self.rpcserver.Send(url)
        return

      else:
        StatusUpdate('Setting default version of module %s of application %s '
                     'to %s.' % (self.module, self.app_id, self.version),
                     self.error_fh)
    else:
      StatusUpdate('Setting default version of application %s to %s.'
                   % (self.app_id, self.version), self.error_fh)
    self.rpcserver.Send('/api/appversion/setdefault',
                        app_id=self.app_id,
                        module=self.module,
                        version=self.version)


class TrafficMigrator(object):
  """Provides facilities to migrate traffic."""

  def __init__(self, rpcserver, app_id, version, error_fh=sys.stderr):
    """Creates a new TrafficMigrator.

    Args:
      rpcserver: The RPC server to use. Should be an instance of a subclass of
        AbstractRpcServer.
      app_id: The application to make the change to.
      version: The version to set as the default.
      error_fh: Where to send status and error messages.
    """
    self.rpcserver = rpcserver
    self.app_id = app_id
    self.version = version
    self.error_fh = error_fh

  def MigrateTraffic(self):
    """Migrates traffic."""
    StatusUpdate('Migrating traffic of application %s to %s.'
                 % (self.app_id, self.version), self.error_fh)
    self.rpcserver.Send('/api/appversion/migratetraffic',
                        app_id=self.app_id,
                        version=self.version)


class IndexOperation(object):
  """Provide facilities for writing Index operation commands."""

  def __init__(self, rpcserver, error_fh=sys.stderr):
    """Creates a new IndexOperation.

    Args:
      rpcserver: The RPC server to use.  Should be an instance of HttpRpcServer
        or TestRpcServer.
      error_fh: Where to send status and error messages.
    """
    self.rpcserver = rpcserver
    self.error_fh = error_fh

  def DoDiff(self, definitions):
    """Retrieve diff file from the server.

    Args:
      definitions: datastore_index.IndexDefinitions as loaded from users
        index.yaml file.

    Returns:
      A pair of datastore_index.IndexDefinitions objects.  The first record
      is the set of indexes that are present in the index.yaml file but missing
      from the server.  The second record is the set of indexes that are
      present on the server but missing from the index.yaml file (indicating
      that these indexes should probably be vacuumed).
    """
    StatusUpdate('Fetching index definitions diff.', self.error_fh)
    with TempChangeField(definitions, 'application', None) as app_id:
      response = self.rpcserver.Send('/api/datastore/index/diff',
                                     app_id=app_id,
                                     payload=definitions.ToYAML())

    return datastore_index.ParseMultipleIndexDefinitions(response)

  def DoDelete(self, definitions, app_id):
    """Delete indexes from the server.

    Args:
      definitions: Index definitions to delete from datastore.
      app_id: The application id.

    Returns:
      A single datstore_index.IndexDefinitions containing indexes that were
      not deleted, probably because they were already removed.  This may
      be normal behavior as there is a potential race condition between fetching
      the index-diff and sending deletion confirmation through.
    """
    StatusUpdate('Deleting selected index definitions.', self.error_fh)

    response = self.rpcserver.Send('/api/datastore/index/delete',
                                   app_id=app_id,
                                   payload=definitions.ToYAML())
    return datastore_index.ParseIndexDefinitions(response)


class VacuumIndexesOperation(IndexOperation):
  """Provide facilities to request the deletion of datastore indexes."""

  def __init__(self, rpcserver, force, confirmation_fn=raw_input,
               error_fh=sys.stderr):
    """Creates a new VacuumIndexesOperation.

    Args:
      rpcserver: The RPC server to use.  Should be an instance of HttpRpcServer
        or TestRpcServer.
      force: True to force deletion of indexes, else False.
      confirmation_fn: Function used for getting input form user.
      error_fh: Where to send status and error messages.
    """
    super(VacuumIndexesOperation, self).__init__(rpcserver, error_fh)
    self.force = force
    self.confirmation_fn = confirmation_fn

  def GetConfirmation(self, index):
    """Get confirmation from user to delete an index.

    This method will enter an input loop until the user provides a
    response it is expecting.  Valid input is one of three responses:

      y: Confirm deletion of index.
      n: Do not delete index.
      a: Delete all indexes without asking for further confirmation.

    If the user enters nothing at all, the default action is to skip
    that index and do not delete.

    If the user selects 'a', as a side effect, the 'force' flag is set.

    Args:
      index: Index to confirm.

    Returns:
      True if user enters 'y' or 'a'.  False if user enter 'n'.
    """
    while True:

      print 'This index is no longer defined in your index.yaml file.'
      print
      print index.ToYAML()
      print


      confirmation = self.confirmation_fn(
          'Are you sure you want to delete this index? (N/y/a): ')
      confirmation = confirmation.strip().lower()


      if confirmation == 'y':
        return True
      elif confirmation == 'n' or not confirmation:
        return False
      elif confirmation == 'a':
        self.force = True
        return True
      else:
        print 'Did not understand your response.'

  def DoVacuum(self, definitions):
    """Vacuum indexes in datastore.

    This method will query the server to determine which indexes are not
    being used according to the user's local index.yaml file.  Once it has
    made this determination, it confirms with the user which unused indexes
    should be deleted.  Once confirmation for each index is receives, it
    deletes those indexes.

    Because another user may in theory delete the same indexes at the same
    time as the user, there is a potential race condition.  In this rare cases,
    some of the indexes previously confirmed for deletion will not be found.
    The user is notified which indexes these were.

    Args:
      definitions: datastore_index.IndexDefinitions as loaded from users
        index.yaml file.
    """

    unused_new_indexes, notused_indexes = self.DoDiff(definitions)


    deletions = datastore_index.IndexDefinitions(indexes=[])
    if notused_indexes.indexes is not None:
      for index in notused_indexes.indexes:
        if self.force or self.GetConfirmation(index):
          deletions.indexes.append(index)


    if deletions.indexes:
      not_deleted = self.DoDelete(deletions, definitions.application)


      if not_deleted.indexes:
        not_deleted_count = len(not_deleted.indexes)
        if not_deleted_count == 1:
          warning_message = ('An index was not deleted.  Most likely this is '
                             'because it no longer exists.\n\n')
        else:
          warning_message = ('%d indexes were not deleted.  Most likely this '
                             'is because they no longer exist.\n\n'
                             % not_deleted_count)
        for index in not_deleted.indexes:
          warning_message += index.ToYAML()
        logging.warning(warning_message)


class LogsRequester(object):
  """Provide facilities to export request logs."""

  def __init__(self,
               rpcserver,
               app_id,
               module,
               version_id,
               output_file,
               num_days,
               append,
               severity,
               end,
               vhost,
               include_vhost,
               include_all=None,
               time_func=time.time,
               error_fh=sys.stderr):
    """Constructor.

    Args:
      rpcserver: The RPC server to use.  Should be an instance of HttpRpcServer
        or TestRpcServer.
      app_id: The application to fetch logs from.
      module: The module of the app to fetch logs from, optional.
      version_id: The version of the app to fetch logs for.
      output_file: Output file name.
      num_days: Number of days worth of logs to export; 0 for all available.
      append: True if appending to an existing file.
      severity: App log severity to request (0-4); None for no app logs.
      end: date object representing last day of logs to return.
      vhost: The virtual host of log messages to get. None for all hosts.
      include_vhost: If true, the virtual host is included in log messages.
      include_all: If true, we add to the log message everything we know
        about the request.
      time_func: A time.time() compatible function, which can be overridden for
        testing.
      error_fh: Where to send status and error messages.
    """

    self.rpcserver = rpcserver
    self.app_id = app_id
    self.output_file = output_file
    self.append = append
    self.num_days = num_days
    self.severity = severity
    self.vhost = vhost
    self.include_vhost = include_vhost
    self.include_all = include_all
    self.error_fh = error_fh

    self.module = module
    self.version_id = version_id
    self.sentinel = None
    self.write_mode = 'w'
    if self.append:
      self.sentinel = FindSentinel(self.output_file)
      self.write_mode = 'a'


    self.skip_until = False
    now = PacificDate(time_func())
    if end < now:
      self.skip_until = end
    else:

      end = now

    self.valid_dates = None
    if self.num_days:
      start = end - datetime.timedelta(self.num_days - 1)
      self.valid_dates = (start, end)

  def DownloadLogs(self):
    """Download the requested logs.

    This will write the logs to the file designated by
    self.output_file, or to stdout if the filename is '-'.
    Multiple roundtrips to the server may be made.
    """
    if self.module:
      StatusUpdate('Downloading request logs for app %s module %s version %s.' %
                   (self.app_id, self.module, self.version_id), self.error_fh)
    else:
      StatusUpdate('Downloading request logs for app %s version %s.' %
                   (self.app_id, self.version_id), self.error_fh)





    tf = tempfile.TemporaryFile()
    last_offset = None
    try:
      while True:
        try:
          new_offset = self.RequestLogLines(tf, last_offset)
          if not new_offset or new_offset == last_offset:
            break
          last_offset = new_offset
        except KeyboardInterrupt:
          StatusUpdate('Keyboard interrupt; saving data downloaded so far.',
                       self.error_fh)
          break
      StatusUpdate('Copying request logs to %r.' % self.output_file,
                   self.error_fh)
      if self.output_file == '-':
        of = sys.stdout
      else:
        try:
          of = open(self.output_file, self.write_mode)
        except IOError, err:
          StatusUpdate('Can\'t write %r: %s.' % (self.output_file, err))
          sys.exit(1)
      try:
        line_count = CopyReversedLines(tf, of)
      finally:
        of.flush()
        if of is not sys.stdout:
          of.close()
    finally:
      tf.close()
    StatusUpdate('Copied %d records.' % line_count, self.error_fh)

  def RequestLogLines(self, tf, offset):
    """Make a single roundtrip to the server.

    Args:
      tf: Writable binary stream to which the log lines returned by
        the server are written, stripped of headers, and excluding
        lines skipped due to self.sentinel or self.valid_dates filtering.
      offset: Offset string for a continued request; None for the first.

    Returns:
      The offset string to be used for the next request, if another
      request should be issued; or None, if not.
    """
    logging.info('Request with offset %r.', offset)
    kwds = {'app_id': self.app_id,
            'version': self.version_id,
            'limit': 1000,
            'no_header': 1,
           }
    if self.module:
      kwds['module'] = self.module
    if offset:
      kwds['offset'] = offset
    if self.severity is not None:
      kwds['severity'] = str(self.severity)
    if self.vhost is not None:
      kwds['vhost'] = str(self.vhost)
    if self.include_vhost is not None:
      kwds['include_vhost'] = str(self.include_vhost)
    if self.include_all is not None:
      kwds['include_all'] = str(self.include_all)
    response = self.rpcserver.Send('/api/request_logs', payload=None, **kwds)
    response = response.replace('\r', '\0')
    lines = response.splitlines()
    logging.info('Received %d bytes, %d records.', len(response), len(lines))
    offset = None

    valid_dates = self.valid_dates
    sentinel = self.sentinel
    skip_until = self.skip_until
    len_sentinel = None
    if sentinel:
      len_sentinel = len(sentinel)
    for line in lines:
      if line.startswith('#'):
        match = re.match(r'^#\s*next_offset=(\S+)\s*$', line)


        if match and match.group(1) != 'None':
          offset = match.group(1)
        continue

      if (sentinel and
          line.startswith(sentinel) and
          line[len_sentinel : len_sentinel+1] in ('', '\0')):
        return None

      linedate = DateOfLogLine(line)

      if not linedate:
        continue

      if skip_until:
        if linedate > skip_until:
          continue
        else:

          self.skip_until = skip_until = False

      if valid_dates and not valid_dates[0] <= linedate <= valid_dates[1]:
        return None
      tf.write(line + '\n')
    if not lines:
      return None
    return offset


def DateOfLogLine(line):
  """Returns a date object representing the log line's timestamp.

  Args:
    line: a log line string.
  Returns:
    A date object representing the timestamp or None if parsing fails.
  """
  m = re.compile(r'[^[]+\[(\d+/[A-Za-z]+/\d+):[^\d]*').match(line)
  if not m:
    return None
  try:
    return datetime.date(*time.strptime(m.group(1), '%d/%b/%Y')[:3])
  except ValueError:
    return None


def PacificDate(now):
  """For a UTC timestamp, return the date in the US/Pacific timezone.

  Args:
    now: A posix timestamp giving current UTC time.

  Returns:
    A date object representing what day it is in the US/Pacific timezone.
  """

  return datetime.date(*time.gmtime(PacificTime(now))[:3])


def PacificTime(now):
  """Helper to return the number of seconds between UTC and Pacific time.

  This is needed to compute today's date in Pacific time (more
  specifically: Mountain View local time), which is how request logs
  are reported.  (Google servers always report times in Mountain View
  local time, regardless of where they are physically located.)

  This takes (post-2006) US DST into account.  Pacific time is either
  8 hours or 7 hours west of UTC, depending on whether DST is in
  effect.  Since 2007, US DST starts on the Second Sunday in March
  March, and ends on the first Sunday in November.  (Reference:
  http://aa.usno.navy.mil/faq/docs/daylight_time.php.)

  Note that the server doesn't report its local time (the HTTP Date
  header uses UTC), and the client's local time is irrelevant.

  Args:
    now: A posix timestamp giving current UTC time.

  Returns:
    A pseudo-posix timestamp giving current Pacific time.  Passing
    this through time.gmtime() will produce a tuple in Pacific local
    time.
  """
  now -= 8*3600
  if IsPacificDST(now):
    now += 3600
  return now


def IsPacificDST(now):
  """Helper for PacificTime to decide whether now is Pacific DST (PDT).

  Args:
    now: A pseudo-posix timestamp giving current time in PST.

  Returns:
    True if now falls within the range of DST, False otherwise.
  """
  pst = time.gmtime(now)
  year = pst[0]
  assert year >= 2007

  begin = calendar.timegm((year, 3, 8, 2, 0, 0, 0, 0, 0))
  while time.gmtime(begin).tm_wday != SUNDAY:
    begin += DAY

  end = calendar.timegm((year, 11, 1, 2, 0, 0, 0, 0, 0))
  while time.gmtime(end).tm_wday != SUNDAY:
    end += DAY
  return begin <= now < end


def CopyReversedLines(instream, outstream, blocksize=2**16):
  r"""Copy lines from input stream to output stream in reverse order.

  As a special feature, null bytes in the input are turned into
  newlines followed by tabs in the output, but these 'sub-lines'
  separated by null bytes are not reversed.  E.g. If the input is
  'A\0B\nC\0D\n', the output is 'C\n\tD\nA\n\tB\n'.

  Args:
    instream: A seekable stream open for reading in binary mode.
    outstream: A stream open for writing; doesn't have to be seekable or binary.
    blocksize: Optional block size for buffering, for unit testing.

  Returns:
    The number of lines copied.
  """
  line_count = 0
  instream.seek(0, 2)
  last_block = instream.tell() // blocksize
  spillover = ''
  for iblock in xrange(last_block + 1, -1, -1):
    instream.seek(iblock * blocksize)
    data = instream.read(blocksize)
    lines = data.splitlines(True)
    lines[-1:] = ''.join(lines[-1:] + [spillover]).splitlines(True)
    if lines and not lines[-1].endswith('\n'):

      lines[-1] += '\n'
    lines.reverse()
    if lines and iblock > 0:
      spillover = lines.pop()
    if lines:
      line_count += len(lines)
      data = ''.join(lines).replace('\0', '\n\t')
      outstream.write(data)
  return line_count


def FindSentinel(filename, blocksize=2**16, error_fh=sys.stderr):
  """Return the sentinel line from the output file.

  Args:
    filename: The filename of the output file.  (We'll read this file.)
    blocksize: Optional block size for buffering, for unit testing.
    error_fh: Where to send status and error messages.

  Returns:
    The contents of the last line in the file that doesn't start with
    a tab, with its trailing newline stripped; or None if the file
    couldn't be opened or no such line could be found by inspecting
    the last 'blocksize' bytes of the file.
  """
  if filename == '-':
    StatusUpdate('Can\'t combine --append with output to stdout.',
                 error_fh)
    sys.exit(2)
  try:
    fp = open(filename, 'rb')
  except IOError, err:
    StatusUpdate('Append mode disabled: can\'t read %r: %s.' % (filename, err),
                 error_fh)
    return None
  try:
    fp.seek(0, 2)
    fp.seek(max(0, fp.tell() - blocksize))
    lines = fp.readlines()
    del lines[:1]
    sentinel = None
    for line in lines:
      if not line.startswith('\t'):
        sentinel = line
    if not sentinel:

      StatusUpdate('Append mode disabled: can\'t find sentinel in %r.' %
                   filename, error_fh)
      return None
    return sentinel.rstrip('\n')
  finally:
    fp.close()


class UploadBatcher(object):
  """Helper to batch file uploads."""

  def __init__(self, what, logging_context):
    """Constructor.

    Args:
      what: Either 'file' or 'blob' or 'errorblob' indicating what kind of
        objects this batcher uploads.  Used in messages and URLs.
      logging_context: The _ClientDeployLoggingContext for this upload.
    """
    assert what in ('file', 'blob', 'errorblob'), repr(what)
    self.what = what
    self.logging_context = logging_context
    self.single_url = '/api/appversion/add' + what
    self.batch_url = self.single_url + 's'
    self.batching = True
    self.batch = []
    self.batch_size = 0

  def SendBatch(self):
    """Send the current batch on its way.

    If successful, resets self.batch and self.batch_size.

    Raises:
      HTTPError with code=404 if the server doesn't support batching.
    """
    boundary = 'boundary'
    parts = []
    for path, payload, mime_type in self.batch:
      while boundary in payload:
        boundary += '%04x' % random.randint(0, 0xffff)
        assert len(boundary) < 80, 'Unexpected error, please try again.'
      part = '\n'.join(['',
                        'X-Appcfg-File: %s' % urllib.quote(path),
                        'X-Appcfg-Hash: %s' % _Hash(payload),
                        'Content-Type: %s' % mime_type,
                        'Content-Length: %d' % len(payload),
                        'Content-Transfer-Encoding: 8bit',
                        '',
                        payload,
                       ])
      parts.append(part)
    parts.insert(0,
                 'MIME-Version: 1.0\n'
                 'Content-Type: multipart/mixed; boundary="%s"\n'
                 '\n'
                 'This is a message with multiple parts in MIME format.' %
                 boundary)
    parts.append('--\n')
    delimiter = '\n--%s' % boundary
    payload = delimiter.join(parts)
    logging.info('Uploading batch of %d %ss to %s with boundary="%s".',
                 len(self.batch), self.what, self.batch_url, boundary)
    self.logging_context.Send(self.batch_url,
                              payload=payload,
                              content_type='message/rfc822')
    self.batch = []
    self.batch_size = 0

  def SendSingleFile(self, path, payload, mime_type):
    """Send a single file on its way."""
    logging.info('Uploading %s %s (%s bytes, type=%s) to %s.',
                 self.what, path, len(payload), mime_type, self.single_url)
    self.logging_context.Send(self.single_url,
                              payload=payload,
                              content_type=mime_type,
                              path=path)

  def Flush(self):
    """Flush the current batch.

    This first attempts to send the batch as a single request; if that
    fails because the server doesn't support batching, the files are
    sent one by one, and self.batching is reset to False.

    At the end, self.batch and self.batch_size are reset.
    """
    if not self.batch:
      return
    try:
      self.SendBatch()
    except urllib2.HTTPError, err:
      if err.code != 404:
        raise


      logging.info('Old server detected; turning off %s batching.', self.what)
      self.batching = False


      for path, payload, mime_type in self.batch:
        self.SendSingleFile(path, payload, mime_type)


      self.batch = []
      self.batch_size = 0

  def AddToBatch(self, path, payload, mime_type):
    """Batch a file, possibly flushing first, or perhaps upload it directly.

    Args:
      path: The name of the file.
      payload: The contents of the file.
      mime_type: The MIME Content-type of the file, or None.

    If mime_type is None, application/octet-stream is substituted.
    """
    if not mime_type:
      mime_type = 'application/octet-stream'
    size = len(payload)
    if size <= MAX_BATCH_FILE_SIZE:
      if (len(self.batch) >= MAX_BATCH_COUNT or
          self.batch_size + size > MAX_BATCH_SIZE):
        self.Flush()
      if self.batching:
        logging.info('Adding %s %s (%s bytes, type=%s) to batch.',
                     self.what, path, size, mime_type)
        self.batch.append((path, payload, mime_type))
        self.batch_size += size + BATCH_OVERHEAD
        return
    self.SendSingleFile(path, payload, mime_type)


def _FormatHash(h):
  """Return a string representation of a hash.

  The hash is a sha1 hash. It is computed both for files that need to be
  pushed to App Engine and for data payloads of requests made to App Engine.

  Args:
    h: The hash

  Returns:
    The string representation of the hash.
  """
  return '%s_%s_%s_%s_%s' % (h[0:8], h[8:16], h[16:24], h[24:32], h[32:40])


def _Hash(content):
  """Compute the sha1 hash of the content.

  Args:
    content: The data to hash as a string.

  Returns:
    The string representation of the hash.
  """
  h = hashlib.sha1(content).hexdigest()
  return _FormatHash(h)


def _HashFromFileHandle(file_handle):
  """Compute the hash of the content of the file pointed to by file_handle.

  Args:
    file_handle: File-like object which provides seek, read and tell.

  Returns:
    The string representation of the hash.
  """







  pos = file_handle.tell()
  content_hash = _Hash(file_handle.read())
  file_handle.seek(pos, 0)
  return content_hash


def EnsureDir(path):
  """Makes sure that a directory exists at the given path.

  If a directory already exists at that path, nothing is done.
  Otherwise, try to create a directory at that path with os.makedirs.
  If that fails, propagate the resulting OSError exception.

  Args:
    path: The path that you want to refer to a directory.
  """
  try:
    os.makedirs(path)
  except OSError, exc:


    if not (exc.errno == errno.EEXIST and os.path.isdir(path)):
      raise


def DoDownloadApp(rpcserver, out_dir, app_id, module, app_version,
                  error_fh=sys.stderr):
  """Downloads the files associated with a particular app version.

  Args:
    rpcserver: The RPC server to use to download.
    out_dir: The directory the files should be downloaded to.
    app_id: The app ID of the app whose files we want to download.
    module: The module we want to download from.  Can be:
      - None: We'll download from the default module.
      - <module>: We'll download from the specified module.
    app_version: The version number we want to download.  Can be:
      - None: We'll download the latest default version.
      - <major>: We'll download the latest minor version.
      - <major>/<minor>: We'll download that exact version.
    error_fh: Where to send status and error messages.
  """

  StatusUpdate('Fetching file list...', error_fh)

  url_args = {'app_id': app_id}
  if module:
    url_args['module'] = module
  if app_version is not None:
    url_args['version_match'] = app_version

  result = rpcserver.Send('/api/files/list', **url_args)

  StatusUpdate('Fetching files...', error_fh)

  lines = result.splitlines()

  if len(lines) < 1:
    logging.error('Invalid response from server: empty')
    return

  full_version = lines[0]
  file_lines = lines[1:]

  current_file_number = 0
  num_files = len(file_lines)

  num_errors = 0

  for line in file_lines:
    parts = line.split('|', 2)
    if len(parts) != 3:
      logging.error('Invalid response from server: expecting '
                    '"<id>|<size>|<path>", found: "%s"\n', line)
      return

    current_file_number += 1

    file_id, size_str, path = parts
    try:
      size = int(size_str)
    except ValueError:
      logging.error('Invalid file list entry from server: invalid size: '
                    '"%s"', size_str)
      return

    StatusUpdate('[%d/%d] %s' % (current_file_number, num_files, path),
                 error_fh)

    def TryGet():
      """A request to /api/files/get which works with the RetryWithBackoff."""
      try:
        contents = rpcserver.Send('/api/files/get', app_id=app_id,
                                  version=full_version, id=file_id)
        return True, contents
      except urllib2.HTTPError, exc:


        if exc.code == 503:
          return False, exc
        else:
          raise

    def PrintRetryMessage(_, delay):
      StatusUpdate('Server busy.  Will try again in %d seconds.' % delay,
                   error_fh)

    success, contents = RetryWithBackoff(TryGet, PrintRetryMessage)
    if not success:
      logging.error('Unable to download file "%s".', path)
      num_errors += 1
      continue

    if len(contents) != size:
      logging.error('File "%s": server listed as %d bytes but served '
                    '%d bytes.', path, size, len(contents))
      num_errors += 1

    full_path = os.path.join(out_dir, path)

    if os.path.exists(full_path):
      logging.error('Unable to create file "%s": path conflicts with '
                    'an existing file or directory', path)
      num_errors += 1
      continue

    full_dir = os.path.dirname(full_path)
    try:
      EnsureDir(full_dir)
    except OSError, exc:
      logging.error('Couldn\'t create directory "%s": %s', full_dir, exc)
      num_errors += 1
      continue

    try:
      out_file = open(full_path, 'wb')
    except IOError, exc:
      logging.error('Couldn\'t open file "%s": %s', full_path, exc)
      num_errors += 1
      continue

    try:
      try:
        out_file.write(contents)
      except IOError, exc:
        logging.error('Couldn\'t write to file "%s": %s', full_path, exc)
        num_errors += 1
        continue
    finally:
      out_file.close()

  if num_errors > 0:
    logging.error('Number of errors: %d.  See output for details.', num_errors)


class _ClientDeployLoggingContext(object):
  """Context for sending and recording server rpc requests.

  Attributes:
    rpcserver: The AbstractRpcServer to use for the upload.
    requests: A list of client_deployinfo.Request objects to include
      with the client deploy log.
    time_func: Function to get the current time in milliseconds.
    request_params: A dictionary with params to append to requests
  """

  def __init__(self,
               rpcserver,
               request_params,
               usage_reporting,
               time_func=time.time):
    """Creates a new AppVersionUpload.

    Args:
      rpcserver: The RPC server to use. Should be an instance of HttpRpcServer
        or TestRpcServer.
      request_params: A dictionary with params to append to requests
      usage_reporting: Whether to actually upload data.
      time_func: Function to return the current time in millisecods
        (default time.time).
    """
    self.rpcserver = rpcserver
    self.request_params = request_params
    self.usage_reporting = usage_reporting
    self.time_func = time_func
    self.requests = []

  def Send(self, url, payload='', **kwargs):
    """Sends a request to the server, with common params."""
    start_time_usec = self.GetCurrentTimeUsec()
    request_size_bytes = len(payload)
    try:
      logging.info('Send: %s, params=%s', url, self.request_params)

      kwargs.update(self.request_params)
      result = self.rpcserver.Send(url, payload=payload, **kwargs)
      self._RegisterReqestForLogging(url, 200, start_time_usec,
                                     request_size_bytes)
      return result
    except urllib2.HTTPError, e:
      self._RegisterReqestForLogging(url, e.code, start_time_usec,
                                     request_size_bytes)
      raise e

  def GetCurrentTimeUsec(self):
    """Returns the current time in microseconds."""
    return int(round(self.time_func() * 1000 * 1000))

  def GetSdkVersion(self):
    """Returns the current SDK Version."""
    sdk_version = sdk_update_checker.GetVersionObject()
    return sdk_version.get('release', '?') if sdk_version else '?'

  def _RegisterReqestForLogging(self, path, response_code, start_time_usec,
                                request_size_bytes):
    """Registers a request for client deploy logging purposes."""
    end_time_usec = self.GetCurrentTimeUsec()
    self.requests.append(client_deployinfo.Request(
        path=path,
        response_code=response_code,
        start_time_usec=start_time_usec,
        end_time_usec=end_time_usec,
        request_size_bytes=request_size_bytes))

  def LogClientDeploy(self, runtime, start_time_usec, success):
    """Logs a client deployment attempt.

    Args:
      runtime: The runtime for the app being deployed.
      start_time_usec: The start time of the deployment in micro seconds.
      success: True if the deployment succeeded otherwise False.
    """
    if not self.usage_reporting:
      logging.info('Skipping usage reporting.')
      return
    end_time_usec = self.GetCurrentTimeUsec()
    try:
      info = client_deployinfo.ClientDeployInfoExternal(
          runtime=runtime,
          start_time_usec=start_time_usec,
          end_time_usec=end_time_usec,
          requests=self.requests,
          success=success,
          sdk_version=self.GetSdkVersion())
      self.Send('/api/logclientdeploy', info.ToYAML())
    except BaseException, e:
      logging.debug('Exception logging deploy info continuing - %s', e)


class EndpointsState(object):
  SERVING = 'serving'
  PENDING = 'pending'
  FAILED = 'failed'
  _STATES = frozenset((SERVING, PENDING, FAILED))

  @classmethod
  def Parse(cls, value):
    state = value.lower()
    if state not in cls._STATES:
      lst = sorted(cls._STATES)
      pretty_states = ', '.join(lst[:-1]) + ', or ' + lst[-1]
      raise ValueError('Unexpected Endpoints state "%s"; should be %s.' %
                       (value, pretty_states))
    return state


class AppVersionUpload(object):
  """Provides facilities to upload a new appversion to the hosting service.

  Attributes:
    rpcserver: The AbstractRpcServer to use for the upload.
    config: The AppInfoExternal object derived from the app.yaml file.
    app_id: The application string from 'config'.
    version: The version string from 'config'.
    backend: The backend to update, if any.
    files: A dictionary of files to upload to the rpcserver, mapping path to
      hash of the file contents.
    in_transaction: True iff a transaction with the server has started.
      An AppVersionUpload can do only one transaction at a time.
    deployed: True iff the Deploy method has been called.
    started: True iff the StartServing method has been called.
    logging_context: The _ClientDeployLoggingContext for this upload.
    ignore_endpoints_failures: True to finish deployment even if there are
      errors updating the Google Cloud Endpoints configuration (if there is
      one). False if these errors should cause a failure/rollback.
  """

  def __init__(self, rpcserver, config, module_yaml_path='app.yaml',
               backend=None,
               error_fh=None,
               usage_reporting=False, ignore_endpoints_failures=True):
    """Creates a new AppVersionUpload.

    Args:
      rpcserver: The RPC server to use. Should be an instance of HttpRpcServer
        or TestRpcServer.
      config: An AppInfoExternal object that specifies the configuration for
        this application.
      module_yaml_path: The (string) path to the yaml file corresponding to
        <config>, relative to the bundle directory.
      backend: If specified, indicates the update applies to the given backend.
        The backend name must match an entry in the backends: stanza.
      error_fh: Unexpected HTTPErrors are printed to this file handle.
      usage_reporting: Whether or not to report usage.
      ignore_endpoints_failures: True to finish deployment even if there are
        errors updating the Google Cloud Endpoints configuration (if there is
        one). False if these errors should cause a failure/rollback.
    """
    self.rpcserver = rpcserver
    self.config = config
    self.app_id = self.config.application
    self.module = self.config.module
    self.backend = backend
    self.error_fh = error_fh or sys.stderr

    self.version = self.config.version

    self.params = {}
    if self.app_id:
      self.params['app_id'] = self.app_id
    if self.module:
      self.params['module'] = self.module
    if self.backend:
      self.params['backend'] = self.backend
    elif self.version:
      self.params['version'] = self.version




    self.files = {}


    self.all_files = set()

    self.in_transaction = False
    self.deployed = False
    self.started = False
    self.batching = True
    self.logging_context = _ClientDeployLoggingContext(rpcserver,
                                                       self.params,
                                                       usage_reporting)
    self.file_batcher = UploadBatcher('file', self.logging_context)
    self.blob_batcher = UploadBatcher('blob', self.logging_context)
    self.errorblob_batcher = UploadBatcher('errorblob', self.logging_context)

    if not self.config.vm_settings:
      self.config.vm_settings = appinfo.VmSettings()
    self.config.vm_settings['module_yaml_path'] = module_yaml_path

    if not self.config.auto_id_policy:
      self.config.auto_id_policy = appinfo.DATASTORE_ID_POLICY_DEFAULT
    self.ignore_endpoints_failures = ignore_endpoints_failures

  def AddFile(self, path, file_handle):
    """Adds the provided file to the list to be pushed to the server.

    Args:
      path: The path the file should be uploaded as.
      file_handle: A stream containing data to upload.
    """
    assert not self.in_transaction, 'Already in a transaction.'
    assert file_handle is not None

    reason = appinfo.ValidFilename(path)
    if reason:
      logging.error(reason)
      return

    content_hash = _HashFromFileHandle(file_handle)

    self.files[path] = content_hash
    self.all_files.add(path)

  def Describe(self):
    """Returns a string describing the object being updated."""
    result = 'app: %s' % self.app_id
    if self.module is not None and self.module != appinfo.DEFAULT_MODULE:
      result += ', module: %s' % self.module
    if self.backend:
      result += ', backend: %s' % self.backend
    elif self.version:
      result += ', version: %s' % self.version
    return result

  @staticmethod
  def _ValidateBeginYaml(resp):
    """Validates the given /api/appversion/create response string."""
    response_dict = yaml.safe_load(resp)
    if not response_dict or 'warnings' not in response_dict:
      return False
    return response_dict

  def Begin(self):
    """Begins the transaction, returning a list of files that need uploading.

    All calls to AddFile must be made before calling Begin().

    Returns:
      A list of pathnames for files that should be uploaded using UploadFile()
      before Commit() can be called.
    """
    assert not self.in_transaction, 'Already in a transaction.'




    config_copy = copy.deepcopy(self.config)
    for url in config_copy.handlers:
      handler_type = url.GetHandlerType()
      if url.application_readable:


        if handler_type == 'static_dir':
          url.static_dir = '%s/%s' % (STATIC_FILE_PREFIX, url.static_dir)
        elif handler_type == 'static_files':
          url.static_files = '%s/%s' % (STATIC_FILE_PREFIX, url.static_files)
          url.upload = '%s/%s' % (STATIC_FILE_PREFIX, url.upload)

    response = self.logging_context.Send(
        '/api/appversion/create',
        payload=config_copy.ToYAML())

    result = self._ValidateBeginYaml(response)
    if result:
      warnings = result.get('warnings')
      for warning in warnings:
        StatusUpdate('WARNING: %s' % warning, self.error_fh)

    self.in_transaction = True

    files_to_clone = []
    blobs_to_clone = []
    errorblobs = {}
    for path, content_hash in self.files.iteritems():
      file_classification = FileClassification(
          self.config, path, error_fh=self.error_fh)

      if file_classification.IsStaticFile():
        upload_path = path
        if file_classification.IsApplicationFile():
          upload_path = '%s/%s' % (STATIC_FILE_PREFIX, path)
        blobs_to_clone.append((path, upload_path, content_hash,
                               file_classification.StaticMimeType()))



      if file_classification.IsErrorFile():



        errorblobs[path] = content_hash

      if file_classification.IsApplicationFile():
        files_to_clone.append((path, path, content_hash))

    files_to_upload = {}

    def CloneFiles(url, files, file_type):
      """Sends files to the given url.

      Args:
        url: the server URL to use.
        files: a list of files
        file_type: the type of the files
      """
      if not files:
        return

      StatusUpdate('Cloning %d %s file%s.' %
                   (len(files), file_type, len(files) != 1 and 's' or ''),
                   self.error_fh)

      max_files = self.resource_limits['max_files_to_clone']
      for i in xrange(0, len(files), max_files):
        if i > 0 and i % max_files == 0:
          StatusUpdate('Cloned %d files.' % i, self.error_fh)

        chunk = files[i:min(len(files), i + max_files)]
        result = self.logging_context.Send(url,
                                           payload=BuildClonePostBody(chunk))
        if result:
          to_upload = {}
          for f in result.split(LIST_DELIMITER):
            for entry in files:
              real_path, upload_path = entry[:2]
              if f == upload_path:
                to_upload[real_path] = self.files[real_path]
                break
          files_to_upload.update(to_upload)

    CloneFiles('/api/appversion/cloneblobs', blobs_to_clone, 'static')
    CloneFiles('/api/appversion/clonefiles', files_to_clone, 'application')

    logging.debug('Files to upload: %s', files_to_upload)

    for (path, content_hash) in errorblobs.iteritems():
      files_to_upload[path] = content_hash
    self.files = files_to_upload
    return sorted(files_to_upload.iterkeys())

  def UploadFile(self, path, file_handle):
    """Uploads a file to the hosting service.

    Must only be called after Begin().
    The path provided must be one of those that were returned by Begin().

    Args:
      path: The path the file is being uploaded as.
      file_handle: A file-like object containing the data to upload.

    Raises:
      KeyError: The provided file is not amongst those to be uploaded.
    """
    assert self.in_transaction, 'Begin() must be called before UploadFile().'
    if path not in self.files:
      raise KeyError('File \'%s\' is not in the list of files to be uploaded.'
                     % path)

    del self.files[path]

    file_classification = FileClassification(
        self.config, path, error_fh=self.error_fh)
    payload = file_handle.read()
    if file_classification.IsStaticFile():
      upload_path = path
      if file_classification.IsApplicationFile():
        upload_path = '%s/%s' % (STATIC_FILE_PREFIX, path)
      self.blob_batcher.AddToBatch(upload_path, payload,
                                   file_classification.StaticMimeType())



    if file_classification.IsErrorFile():


      self.errorblob_batcher.AddToBatch(file_classification.ErrorCode(),
                                        payload,
                                        file_classification.ErrorMimeType())

    if file_classification.IsApplicationFile():

      self.file_batcher.AddToBatch(path, payload, None)

  def Precompile(self):
    """Handle precompilation."""

    StatusUpdate('Compilation starting.', self.error_fh)

    files = []
    if self.config.GetEffectiveRuntime() == 'go':


      for f in self.all_files:
        if f.endswith('.go') and not self.config.nobuild_files.match(f):
          files.append(f)

    while True:
      if files:
        StatusUpdate('Compilation: %d files left.' % len(files), self.error_fh)
      files = self.PrecompileBatch(files)
      if not files:
        break
    StatusUpdate('Compilation completed.', self.error_fh)

  def PrecompileBatch(self, files):
    """Precompile a batch of files.

    Args:
      files: Either an empty list (for the initial request) or a list
        of files to be precompiled.

    Returns:
      Either an empty list (if no more files need to be precompiled)
      or a list of files to be precompiled subsequently.
    """
    payload = LIST_DELIMITER.join(files)
    response = self.logging_context.Send('/api/appversion/precompile',
                                         payload=payload)
    if not response:
      return []
    return response.split(LIST_DELIMITER)

  def Commit(self):
    """Commits the transaction, making the new app version available.

    All the files returned by Begin() must have been uploaded with UploadFile()
    before Commit() can be called.

    This tries the new 'deploy' method; if that fails it uses the old 'commit'.

    Returns:
      An appinfo.AppInfoSummary if one was returned from the Deploy, None
      otherwise.

    Raises:
      RuntimeError: Some required files were not uploaded.
      CannotStartServingError: Another operation is in progress on this version.
    """
    assert self.in_transaction, 'Begin() must be called before Commit().'
    if self.files:
      raise RuntimeError('Not all required files have been uploaded.')

    def PrintRetryMessage(_, delay):
      StatusUpdate('Will check again in %s seconds.' % delay, self.error_fh)

    app_summary = self.Deploy()


    success, unused_contents = RetryWithBackoff(
        lambda: (self.IsReady(), None), PrintRetryMessage, 1, 2, 60, 20)
    if not success:

      logging.warning('Version still not ready to serve, aborting.')
      raise RuntimeError('Version not ready.')

    result = self.StartServing()
    if not result:


      self.in_transaction = False
    else:
      if result == '0':
        raise CannotStartServingError(
            'Another operation on this version is in progress.')
      success, response = RetryNoBackoff(self.IsServing, PrintRetryMessage)
      if not success:

        logging.warning('Version still not serving, aborting.')
        raise RuntimeError('Version not ready.')



      check_config_updated = response.get('check_endpoints_config')
      if check_config_updated:
        unused_done, (last_state, user_error) = RetryWithBackoff(
            self.IsEndpointsConfigUpdated,
            PrintRetryMessage, 1, 2, 60, 20)
        if last_state != EndpointsState.SERVING:
          self.HandleEndpointsError(user_error)
      self.in_transaction = False

    return app_summary

  def Deploy(self):
    """Deploys the new app version but does not make it default.

    All the files returned by Begin() must have been uploaded with UploadFile()
    before Deploy() can be called.

    Returns:
      An appinfo.AppInfoSummary if one was returned from the Deploy, None
      otherwise.

    Raises:
      RuntimeError: Some required files were not uploaded.
    """
    assert self.in_transaction, 'Begin() must be called before Deploy().'
    if self.files:
      raise RuntimeError('Not all required files have been uploaded.')

    StatusUpdate('Starting deployment.', self.error_fh)
    result = self.logging_context.Send('/api/appversion/deploy')
    self.deployed = True

    if result:
      return yaml_object.BuildSingleObject(appinfo.AppInfoSummary, result)
    else:
      return None

  def IsReady(self):
    """Check if the new app version is ready to serve traffic.

    Raises:
      RuntimeError: Deploy has not yet been called.

    Returns:
      True if the server returned the app is ready to serve.
    """
    assert self.deployed, 'Deploy() must be called before IsReady().'

    StatusUpdate('Checking if deployment succeeded.', self.error_fh)
    result = self.logging_context.Send('/api/appversion/isready')
    return result == '1'

  def StartServing(self):
    """Start serving with the newly created version.

    Raises:
      RuntimeError: Deploy has not yet been called.

    Returns:
      The response body, as a string.
    """
    assert self.deployed, 'Deploy() must be called before StartServing().'

    StatusUpdate('Deployment successful.', self.error_fh)
    self.params['willcheckserving'] = '1'
    result = self.logging_context.Send('/api/appversion/startserving')
    del self.params['willcheckserving']
    self.started = True
    return result

  @staticmethod
  def _ValidateIsServingYaml(resp):
    """Validates the given /isserving YAML string.

    Args:
      resp: the response from an RPC to a URL such as /api/appversion/isserving.

    Returns:
      The resulting dictionary if the response is valid, or None otherwise.
    """
    response_dict = yaml.safe_load(resp)
    if 'serving' not in response_dict:
      return None
    return response_dict

  def IsServing(self):
    """Check if the new app version is serving.

    Raises:
      RuntimeError: Deploy has not yet been called.
      CannotStartServingError: A bad response was received from the isserving
        API call.

    Returns:
      (serving, response) Where serving is True if the deployed app version is
        serving, False otherwise.  response is a dict containing the parsed
        response from the server, or an empty dict if the server's response was
        an old style 0/1 response.
    """
    assert self.started, 'StartServing() must be called before IsServing().'

    StatusUpdate('Checking if updated app version is serving.', self.error_fh)

    self.params['new_serving_resp'] = '1'
    result = self.logging_context.Send('/api/appversion/isserving')
    del self.params['new_serving_resp']
    if result in ['0', '1']:
      return result == '1', {}
    result = AppVersionUpload._ValidateIsServingYaml(result)
    if not result:
      raise CannotStartServingError(
          'Internal error: Could not parse IsServing response.')
    message = result.get('message')
    fatal = result.get('fatal')
    if message:
      StatusUpdate(message, self.error_fh)
    if fatal:
      raise CannotStartServingError(message or 'Unknown error.')
    return result['serving'], result

  @staticmethod
  def _ValidateIsEndpointsConfigUpdatedYaml(resp):
    """Validates the YAML string response from an isconfigupdated request.

    Args:
      resp: A string containing the response from the server.

    Returns:
      The dictionary with the parsed response if the response is valid.
      Otherwise returns False.
    """
    response_dict = yaml.safe_load(resp)

    if 'updated' not in response_dict and 'updatedDetail2' not in response_dict:
      return None
    return response_dict

  def GetLogUrl(self):
    """Get the URL for the app's logs."""
    module = '%s:' % self.module if self.module else ''
    return ('https://appengine.google.com/logs?' +
            urllib.urlencode((('app_id', self.app_id),
                              ('version_id', module + self.version))))

  def IsEndpointsConfigUpdated(self):
    """Check if the Endpoints configuration for this app has been updated.

    This should only be called if the app has a Google Cloud Endpoints
    handler, or if it's removing one.  The server performs the check to see
    if Endpoints support is added/updated/removed, and the response to the
    isserving call indicates whether IsEndpointsConfigUpdated should be called.

    Raises:
      AssertionError: Deploy has not yet been called.
      CannotStartServingError: There was an unexpected error with the server
        response.

    Returns:
      (done, updated_state), where done is False if this function should
      be called again to retry, True if not.  updated_state is an
      EndpointsState value indicating whether the Endpoints configuration has
      been updated on the server.
    """

    assert self.started, ('StartServing() must be called before '
                          'IsEndpointsConfigUpdated().')

    StatusUpdate('Checking if Endpoints configuration has been updated.',
                 self.error_fh)

    result = self.logging_context.Send('/api/isconfigupdated')
    result = AppVersionUpload._ValidateIsEndpointsConfigUpdatedYaml(result)
    if result is None:
      raise CannotStartServingError(
          'Internal error: Could not parse IsEndpointsConfigUpdated response.')
    if 'updatedDetail2' in result:
      updated_state = EndpointsState.Parse(result['updatedDetail2'])
      user_error = result.get('errorMessage')
    else:





      updated_state = (EndpointsState.SERVING if result['updated']
                       else EndpointsState.PENDING)
      user_error = None
    return updated_state != EndpointsState.PENDING, (updated_state, user_error)

  def HandleEndpointsError(self, user_error):
    """Handle an error state returned by IsEndpointsConfigUpdated.

    Args:
      user_error: Either None or a string with a message from the server
        that indicates what the error was and how the user should resolve it.

    Raises:
      RuntimeError: The update state is fatal and the user hasn't chosen
        to ignore Endpoints errors.
    """
    detailed_error = user_error or (
        "Check the app's AppEngine logs for errors: %s" % self.GetLogUrl())
    error_message = ('Failed to update Endpoints configuration.  %s' %
                     detailed_error)
    StatusUpdate(error_message, self.error_fh)


    doc_link = ('https://developers.google.com/appengine/docs/python/'
                'endpoints/test_deploy#troubleshooting_a_deployment_failure')
    StatusUpdate('See the deployment troubleshooting documentation for more '
                 'information: %s' % doc_link, self.error_fh)

    if self.ignore_endpoints_failures:
      StatusUpdate('Ignoring Endpoints failure and proceeding with update.',
                   self.error_fh)
    else:
      raise RuntimeError(error_message)

  def Rollback(self, force_rollback=False):
    """Rolls back the transaction if one is in progress."""
    if not self.in_transaction:
      return
    msg = 'Rolling back the update.'
    if self.config.vm and not force_rollback:
      msg += ('  This can sometimes take a while since a VM version is being '
              'rolled back.')
    StatusUpdate(msg, self.error_fh)
    self.logging_context.Send('/api/appversion/rollback',
                              force_rollback='1' if force_rollback else '0')
    self.in_transaction = False
    self.files = {}

  def DoUpload(self, paths, openfunc):
    """Uploads a new appversion with the given config and files to the server.

    Args:
      paths: An iterator that yields the relative paths of the files to upload.
      openfunc: A function that takes a path and returns a file-like object.

    Returns:
      An appinfo.AppInfoSummary if one was returned from the server, None
      otherwise.
    """
    start_time_usec = self.logging_context.GetCurrentTimeUsec()
    logging.info('Reading app configuration.')

    StatusUpdate('\nStarting update of %s' % self.Describe(), self.error_fh)


    path = ''
    try:
      self.resource_limits = GetResourceLimits(self.logging_context,
                                               self.error_fh)
      self._AddFilesThatAreSmallEnough(paths, openfunc)
    except KeyboardInterrupt:
      logging.info('User interrupted. Aborting.')
      raise
    except EnvironmentError, e:
      if self._IsExceptionClientDeployLoggable(e):
        self.logging_context.LogClientDeploy(self.config.runtime,
                                             start_time_usec, False)
      logging.error('An error occurred processing file \'%s\': %s. Aborting.',
                    path, e)
      raise

    try:
      missing_files = self.Begin()
      self._UploadMissingFiles(missing_files, openfunc)


      if (self.config.derived_file_type and
          appinfo.PYTHON_PRECOMPILED in self.config.derived_file_type):
        try:
          self.Precompile()
        except urllib2.HTTPError, e:
          ErrorUpdate('Error %d: --- begin server output ---\n'
                      '%s\n--- end server output ---' %
                      (e.code, e.read().rstrip('\n')))
          if e.code == 422 or self.config.GetEffectiveRuntime() == 'go':






            raise
          print >>self.error_fh, (
              'Precompilation failed. Your app can still serve but may '
              'have reduced startup performance. You can retry the update '
              'later to retry the precompilation step.')


      app_summary = self.Commit()
      StatusUpdate('Completed update of %s' % self.Describe(), self.error_fh)
      self.logging_context.LogClientDeploy(self.config.runtime, start_time_usec,
                                           True)
    except BaseException, e:
      try:
        self._LogDoUploadException(e)
        self.Rollback()
      finally:
        if self._IsExceptionClientDeployLoggable(e):
          self.logging_context.LogClientDeploy(self.config.runtime,
                                               start_time_usec, False)

      raise

    logging.info('Done!')
    return app_summary

  def _IsExceptionClientDeployLoggable(self, exception):
    """Determines if an exception qualifes for client deploy log reistration.

    Args:
      exception: The exception to check.

    Returns:
      True iff exception qualifies for client deploy logging - basically a
      system error rather than a user or error or cancellation.
    """

    if isinstance(exception, KeyboardInterrupt):
      return False

    if (isinstance(exception, urllib2.HTTPError)
        and 400 <= exception.code <= 499):
      return False

    return True

  def _AddFilesThatAreSmallEnough(self, paths, openfunc):
    """Calls self.AddFile on files that are small enough.

    By small enough, we mean that their size is within
    self.resource_limits['max_file_size'] for application files, and
    'max_blob_size' otherwise. Files that are too large are logged as errors,
    and dropped (not sure why this isn't handled by raising an exception...).

    Args:
      paths: List of paths, relative to the app's base path.
      openfunc: A function that takes a paths element, and returns a file-like
        object.
    """
    StatusUpdate('Scanning files on local disk.', self.error_fh)
    num_files = 0
    for path in paths:
      file_handle = openfunc(path)
      try:
        file_length = GetFileLength(file_handle)


        file_classification = FileClassification(
            self.config, path, self.error_fh)
        if file_classification.IsApplicationFile():
          max_size = self.resource_limits['max_file_size']
        else:
          max_size = self.resource_limits['max_blob_size']


        if file_length > max_size:
          extra_msg = (' Consider --enable_jar_splitting.'
                       if JavaSupported() and path.endswith('jar')
                       else '')
          logging.error('Ignoring file \'%s\': Too long '
                        '(max %d bytes, file is %d bytes).%s',
                        path, max_size, file_length, extra_msg)
        else:
          logging.info('Processing file \'%s\'', path)
          self.AddFile(path, file_handle)
      finally:
        file_handle.close()


      num_files += 1
      if num_files % 500 == 0:
        StatusUpdate('Scanned %d files.' % num_files, self.error_fh)

  def _UploadMissingFiles(self, missing_files, openfunc):
    """DoUpload helper to upload files that need to be uploaded.

    Args:
      missing_files: List of files that need to be uploaded. Begin returns such
        a list. Design note: we don't call Begin here, because we want DoUpload
        to call it directly so that Begin/Commit are more clearly paired.
      openfunc: Function that takes a path relative to the app's base path, and
        returns a file-like object.
    """
    if not missing_files:
      return

    StatusUpdate('Uploading %d files and blobs.' % len(missing_files),
                 self.error_fh)
    num_files = 0
    for missing_file in missing_files:
      file_handle = openfunc(missing_file)
      try:
        self.UploadFile(missing_file, file_handle)
      finally:
        file_handle.close()


      num_files += 1
      if num_files % 500 == 0:
        StatusUpdate('Processed %d out of %s.' %
                     (num_files, len(missing_files)), self.error_fh)


    self.file_batcher.Flush()
    self.blob_batcher.Flush()
    self.errorblob_batcher.Flush()
    StatusUpdate('Uploaded %d files and blobs.' % num_files, self.error_fh)

  @staticmethod
  def _LogDoUploadException(exception):
    """Helper that logs exceptions that occurred during DoUpload.

    Args:
      exception: An exception that was thrown during DoUpload.
    """
    def InstanceOf(tipe):
      return isinstance(exception, tipe)

    if InstanceOf(KeyboardInterrupt):
      logging.info('User interrupted. Aborting.')
    elif InstanceOf(urllib2.HTTPError):
      logging.info('HTTP Error (%s)', exception)
    elif InstanceOf(CannotStartServingError):
      logging.error(exception.message)
    else:
      logging.exception('An unexpected error occurred. Aborting.')


class DoLockAction(object):
  """Locks/unlocks a particular vm app version and shows state."""

  def __init__(
      self, url, rpcserver, app_id, version, module, instance, file_handle):
    self.url = url
    self.rpcserver = rpcserver
    self.app_id = app_id
    self.version = version
    self.module = module
    self.instance = instance
    self.file_handle = file_handle

  def GetState(self):
    yaml_data = self.rpcserver.Send('/api/vms/debugstate',
                                    app_id=self.app_id,
                                    version_match=self.version,
                                    module=self.module)
    state = yaml.safe_load(yaml_data)
    done = state['state'] != 'PENDING'
    if done:
      print >> self.file_handle, state['message']
    return (done, state['message'])

  def PrintRetryMessage(self, msg, delay):
    StatusUpdate('%s.  Will try again in %d seconds.' % (msg, delay),
                 self.file_handle)

  def Do(self):
    kwargs = {'app_id': self.app_id,
              'version_match': self.version,
              'module': self.module}
    if self.instance:
      kwargs['instance'] = self.instance

    response = self.rpcserver.Send(self.url, **kwargs)
    print >> self.file_handle, response
    RetryWithBackoff(self.GetState, self.PrintRetryMessage, 1, 2, 5, 20)


def FileIterator(base, skip_files, runtime, separator=os.path.sep):
  """Walks a directory tree, returning all the files. Follows symlinks.

  Args:
    base: The base path to search for files under.
    skip_files: A regular expression object for files/directories to skip.
    runtime: The name of the runtime e.g. "python". If "python27" then .pyc
      files with matching .py files will be skipped.
    separator: Path separator used by the running system's platform.

  Yields:
    Paths of files found, relative to base.
  """
  dirs = ['']
  while dirs:
    current_dir = dirs.pop()
    entries = set(os.listdir(os.path.join(base, current_dir)))
    for entry in sorted(entries):
      name = os.path.join(current_dir, entry)
      fullname = os.path.join(base, name)




      if separator == '\\':
        name = name.replace('\\', '/')

      if runtime == 'python27' and not skip_files.match(name):
        root, extension = os.path.splitext(entry)
        if extension == '.pyc' and (root + '.py') in entries:
          logging.warning('Ignoring file \'%s\': Cannot upload both '
                          '<filename>.py and <filename>.pyc', name)
          continue

      if os.path.isfile(fullname):
        if skip_files.match(name):
          logging.info('Ignoring file \'%s\': File matches ignore regex.', name)
        else:
          yield name
      elif os.path.isdir(fullname):
        if skip_files.match(name):
          logging.info(
              'Ignoring directory \'%s\': Directory matches ignore regex.',
              name)
        else:
          dirs.append(name)


def GetFileLength(fh):
  """Returns the length of the file represented by fh.

  This function is capable of finding the length of any seekable stream,
  unlike os.fstat, which only works on file streams.

  Args:
    fh: The stream to get the length of.

  Returns:
    The length of the stream.
  """
  pos = fh.tell()

  fh.seek(0, 2)
  length = fh.tell()
  fh.seek(pos, 0)
  return length


def GetUserAgent(get_version=sdk_update_checker.GetVersionObject,
                 get_platform=appengine_rpc.GetPlatformToken,
                 sdk_product=SDK_PRODUCT):
  """Determines the value of the 'User-agent' header to use for HTTP requests.

  If the 'APPCFG_SDK_NAME' environment variable is present, that will be
  used as the first product token in the user-agent.

  Args:
    get_version: Used for testing.
    get_platform: Used for testing.
    sdk_product: Used as part of sdk/version product token.

  Returns:
    String containing the 'user-agent' header value, which includes the SDK
    version, the platform information, and the version of Python;
    e.g., 'appcfg_py/1.0.1 Darwin/9.2.0 Python/2.5.2'.
  """
  product_tokens = []


  sdk_name = os.environ.get('APPCFG_SDK_NAME')
  if sdk_name:
    product_tokens.append(sdk_name)
  else:
    version = get_version()
    if version is None:
      release = 'unknown'
    else:
      release = version['release']

    product_tokens.append('%s/%s' % (sdk_product, release))


  product_tokens.append(get_platform())


  python_version = '.'.join(str(i) for i in sys.version_info)
  product_tokens.append('Python/%s' % python_version)

  return ' '.join(product_tokens)


def GetSourceName(get_version=sdk_update_checker.GetVersionObject):
  """Gets the name of this source version."""
  version = get_version()
  if version is None:
    release = 'unknown'
  else:
    release = version['release']
  return 'Google-appcfg-%s' % (release,)


def _ReadUrlContents(url):
  """Reads the contents of a URL into a string.

  Args:
    url: a string that is the URL to read.

  Returns:
    A string that is the contents read from the URL.

  Raises:
    urllib2.URLError: If the URL cannot be read.
  """
  req = urllib2.Request(url)
  return urllib2.urlopen(req).read()


class AppCfgApp(object):
  """Singleton class to wrap AppCfg tool functionality.

  This class is responsible for parsing the command line and executing
  the desired action on behalf of the user.  Processing files and
  communicating with the server is handled by other classes.

  Attributes:
    actions: A dictionary mapping action names to Action objects.
    action: The Action specified on the command line.
    parser: An instance of optparse.OptionParser.
    options: The command line options parsed by 'parser'.
    argv: The original command line as a list.
    args: The positional command line args left over after parsing the options.
    error_fh: Unexpected HTTPErrors are printed to this file handle.

  Attributes for testing:
    parser_class: The class to use for parsing the command line.  Because
      OptionsParser will exit the program when there is a parse failure, it
      is nice to subclass OptionsParser and catch the error before exiting.
    read_url_contents: A function to read the contents of a URL.
  """

  def __init__(self, argv, parser_class=optparse.OptionParser,
               rpc_server_class=None,
               out_fh=sys.stdout,
               error_fh=sys.stderr,
               update_check_class=sdk_update_checker.SDKUpdateChecker,
               throttle_class=None,
               opener=open,
               file_iterator=FileIterator,
               time_func=time.time,
               wrap_server_error_message=True,
               oauth_client_id=APPCFG_CLIENT_ID,
               oauth_client_secret=APPCFG_CLIENT_NOTSOSECRET,
               oauth_scopes=APPCFG_SCOPES):
    """Initializer.  Parses the cmdline and selects the Action to use.

    Initializes all of the attributes described in the class docstring.
    Prints help or error messages if there is an error parsing the cmdline.

    Args:
      argv: The list of arguments passed to this program.
      parser_class: Options parser to use for this application.
      rpc_server_class: RPC server class to use for this application.
      out_fh: All normal output is printed to this file handle.
      error_fh: Unexpected HTTPErrors are printed to this file handle.
      update_check_class: sdk_update_checker.SDKUpdateChecker class (can be
        replaced for testing).
      throttle_class: A class to use instead of ThrottledHttpRpcServer
        (only used in the bulkloader).
      opener: Function used for opening files.
      file_iterator: Callable that takes (basepath, skip_files, file_separator)
        and returns a generator that yields all filenames in the file tree
        rooted at that path, skipping files that match the skip_files compiled
        regular expression.
      time_func: A time.time() compatible function, which can be overridden for
        testing.
      wrap_server_error_message: If true, the error messages from
          urllib2.HTTPError exceptions in Run() are wrapped with
          '--- begin server output ---' and '--- end server output ---',
          otherwise the error message is printed as is.
      oauth_client_id: The client ID of the project providing Auth. Defaults to
          the SDK default project client ID, the constant APPCFG_CLIENT_ID.
      oauth_client_secret: The client secret of the project providing Auth.
          Defaults to the SDK default project client secret, the constant
          APPCFG_CLIENT_NOTSOSECRET.
      oauth_scopes: The scope or set of scopes to be accessed by the OAuth2
          token retrieved. Defaults to APPCFG_SCOPES. Can be a string or
          iterable of strings, representing the scope(s) to request.
    """
    self.parser_class = parser_class
    self.argv = argv
    self.rpc_server_class = rpc_server_class
    self.out_fh = out_fh
    self.error_fh = error_fh
    self.update_check_class = update_check_class
    self.throttle_class = throttle_class
    self.time_func = time_func
    self.wrap_server_error_message = wrap_server_error_message
    self.oauth_client_id = oauth_client_id
    self.oauth_client_secret = oauth_client_secret
    self.oauth_scopes = oauth_scopes

    self.read_url_contents = _ReadUrlContents





    self.parser = self._GetOptionParser()
    for action in self.actions.itervalues():
      action.options(self, self.parser)


    self.options, self.args = self.parser.parse_args(argv[1:])

    if len(self.args) < 1:
      self._PrintHelpAndExit()

    if not self.options.allow_any_runtime:
      if self.options.runtime:
        if self.options.runtime not in appinfo.GetAllRuntimes():
          _PrintErrorAndExit(self.error_fh,
                             '"%s" is not a supported runtime\n' %
                             self.options.runtime)
      else:
        appinfo.AppInfoExternal.ATTRIBUTES[appinfo.RUNTIME] = (
            '|'.join(appinfo.GetAllRuntimes()))

    if self.options.redundant_oauth2:
      print >>sys.stderr, (
          '\nNote: the --oauth2 flag is now the default and can be omitted.\n')

    action = self.args.pop(0)

    def RaiseParseError(actionname, action):


      self.parser, self.options = self._MakeSpecificParser(action)
      error_desc = action.error_desc
      if not error_desc:
        error_desc = "Expected a <directory> argument after '%s'." % (
            actionname.split(' ')[0])
      self.parser.error(error_desc)




    if action == BACKENDS_ACTION:
      if len(self.args) < 1:
        RaiseParseError(action, self.actions[BACKENDS_ACTION])

      backend_action_first = BACKENDS_ACTION + ' ' + self.args[0]
      if backend_action_first in self.actions:
        self.args.pop(0)
        action = backend_action_first

      elif len(self.args) > 1:
        backend_directory_first = BACKENDS_ACTION + ' ' + self.args[1]
        if backend_directory_first in self.actions:
          self.args.pop(1)
          action = backend_directory_first


      if len(self.args) < 1 or action == BACKENDS_ACTION:
        RaiseParseError(action, self.actions[action])

    if action not in self.actions:
      self.parser.error("Unknown action: '%s'\n%s" %
                        (action, self.parser.get_description()))


    self.action = self.actions[action]




    if not self.action.uses_basepath or self.options.help:
      self.basepath = None
    else:
      if not self.args:
        RaiseParseError(action, self.action)
      self.basepath = self.args.pop(0)





    self.parser, self.options = self._MakeSpecificParser(self.action)



    if self.options.help:
      self._PrintHelpAndExit()

    if self.options.verbose == 2:
      logging.getLogger().setLevel(logging.INFO)
    elif self.options.verbose == 3:
      logging.getLogger().setLevel(logging.DEBUG)




    global verbosity
    verbosity = self.options.verbose


    if self.options.oauth2_client_id:
      self.oauth_client_id = self.options.oauth2_client_id
    if self.options.oauth2_client_secret:
      self.oauth_client_secret = self.options.oauth2_client_secret




    self.opener = opener
    self.file_iterator = file_iterator

  def Run(self):
    """Executes the requested action.

    Catches any HTTPErrors raised by the action and prints them to stderr.

    Returns:
      1 on error, 0 if successful.
    """
    try:
      self.action(self)
    except urllib2.HTTPError, e:
      body = e.read()
      if self.wrap_server_error_message:
        error_format = ('Error %d: --- begin server output ---\n'
                        '%s\n--- end server output ---')
      else:
        error_format = 'Error %d: %s'

      print >>self.error_fh, (error_format % (e.code, body.rstrip('\n')))
      return 1
    except yaml_errors.EventListenerError, e:
      print >>self.error_fh, ('Error parsing yaml file:\n%s' % e)
      return 1
    except CannotStartServingError:
      print >>self.error_fh, 'Could not start serving the given version.'
      return 1
    return 0

  def _GetActionDescriptions(self):
    """Returns a formatted string containing the short_descs for all actions."""
    action_names = self.actions.keys()
    action_names.sort()
    desc = ''
    for action_name in action_names:
      if not self.actions[action_name].hidden:
        desc += '  %s: %s\n' % (action_name,
                                self.actions[action_name].short_desc)
    return desc

  def _GetOptionParser(self):
    """Creates an OptionParser with generic usage and description strings.

    Returns:
      An OptionParser instance.
    """

    def AppendSourceReference(option, opt_str, value, parser):
      """Validates the source reference string and appends it to the list."""
      try:
        appinfo.ValidateSourceReference(value)
      except validation.ValidationError, e:
        raise optparse.OptionValueError('option %s: %s' % (opt_str, e.message))
      getattr(parser.values, option.dest).append(value)

    class Formatter(optparse.IndentedHelpFormatter):
      """Custom help formatter that does not reformat the description."""

      def format_description(self, description):
        """Very simple formatter."""
        return description + '\n'

    class AppCfgOption(optparse.Option):
      """Custom Option for AppCfg.

      Adds an 'update' action for storing key-value pairs as a dict.
      """

      _ACTION = 'update'
      ACTIONS = optparse.Option.ACTIONS + (_ACTION,)
      STORE_ACTIONS = optparse.Option.STORE_ACTIONS + (_ACTION,)
      TYPED_ACTIONS = optparse.Option.TYPED_ACTIONS + (_ACTION,)
      ALWAYS_TYPED_ACTIONS = optparse.Option.ALWAYS_TYPED_ACTIONS + (_ACTION,)

      def take_action(self, action, dest, opt, value, values, parser):
        if action != self._ACTION:
          return optparse.Option.take_action(
              self, action, dest, opt, value, values, parser)
        try:
          key, value = value.split(':', 1)
        except ValueError:
          raise optparse.OptionValueError(
              'option %s: invalid value: %s (must match NAME:VALUE)' % (
                  opt, value))
        values.ensure_value(dest, {})[key] = value

    desc = self._GetActionDescriptions()
    desc = ('Action must be one of:\n%s'
            'Use \'help <action>\' for a detailed description.') % desc



    parser = self.parser_class(usage='%prog [options] <action>',
                               description=desc,
                               formatter=Formatter(),
                               conflict_handler='resolve',
                               option_class=AppCfgOption)




    parser.add_option('-h', '--help', action='store_true',
                      dest='help', help='Show the help message and exit.')
    parser.add_option('-q', '--quiet', action='store_const', const=0,
                      dest='verbose', help='Print errors only.')
    parser.add_option('-v', '--verbose', action='store_const', const=2,
                      dest='verbose', default=1,
                      help='Print info level logs.')
    parser.add_option('--noisy', action='store_const', const=3,
                      dest='verbose', help='Print all logs.')
    parser.add_option('-s', '--server', action='store', dest='server',
                      default='appengine.google.com',
                      metavar='SERVER', help='The App Engine server.')
    parser.add_option('--secure', action='store_true', dest='secure',
                      default=True, help=optparse.SUPPRESS_HELP)
    parser.add_option('--ignore_bad_cert', action='store_true',
                      dest='ignore_certs', default=False,
                      help=optparse.SUPPRESS_HELP)
    parser.add_option('--insecure', action='store_false', dest='secure',
                      help=optparse.SUPPRESS_HELP)
    parser.add_option('-e', '--email', action='store', dest='email',
                      metavar='EMAIL', default=None,
                      help='The username to use. Will prompt if omitted.')
    parser.add_option('-H', '--host', action='store', dest='host',
                      metavar='HOST', default=None,
                      help='Overrides the Host header sent with all RPCs.')
    parser.add_option('--no_cookies', action='store_false',
                      dest='save_cookies', default=True,
                      help='Do not save authentication cookies to local disk.')
    parser.add_option('--skip_sdk_update_check', action='store_true',
                      dest='skip_sdk_update_check', default=False,
                      help='Do not check for SDK updates.')
    parser.add_option('-A', '--application', action='store', dest='app_id',
                      help=('Set the application, overriding the application '
                            'value from app.yaml file.'))
    parser.add_option('-M', '--module', action='store', dest='module',
                      help=('Set the module, overriding the module value '
                            'from app.yaml.'))
    parser.add_option('-V', '--version', action='store', dest='version',
                      help=('Set the (major) version, overriding the version '
                            'value from app.yaml file.'))
    parser.add_option('-r', '--runtime', action='store', dest='runtime',
                      help='Override runtime from app.yaml file.')
    parser.add_option('--source_ref', metavar='[repository_uri#]revision',
                      type='string', action='callback',
                      callback=AppendSourceReference, dest='source_ref',
                      default=[],
                      help=optparse.SUPPRESS_HELP)
    parser.add_option('-E', '--env_variable', action='update',
                      dest='env_variables', metavar='NAME:VALUE',
                      help=('Set an environment variable, potentially '
                            'overriding an env_variable value from app.yaml '
                            'file (flag may be repeated to set multiple '
                            'variables).'))
    parser.add_option('-R', '--allow_any_runtime', action='store_true',
                      dest='allow_any_runtime', default=False,
                      help='Do not validate the runtime in app.yaml')
    parser.add_option('--oauth2', action='store_true',
                      dest='redundant_oauth2', default=False,
                      help='Ignored (OAuth2 is the default).')
    parser.add_option('--oauth2_refresh_token', action='store',
                      dest='oauth2_refresh_token', default=None,
                      help='An existing OAuth2 refresh token to use. Will '
                      'not attempt interactive OAuth approval.')
    parser.add_option('--oauth2_access_token', action='store',
                      dest='oauth2_access_token', default=None,
                      help='An existing OAuth2 access token to use. Will '
                      'not attempt interactive OAuth approval.')
    parser.add_option('--oauth2_client_id', action='store',
                      dest='oauth2_client_id', default=None,
                      help=optparse.SUPPRESS_HELP)
    parser.add_option('--oauth2_client_secret', action='store',
                      dest='oauth2_client_secret', default=None,
                      help=optparse.SUPPRESS_HELP)
    parser.add_option('--oauth2_credential_file', action='store',
                      dest='oauth2_credential_file', default=None,
                      help=optparse.SUPPRESS_HELP)
    parser.add_option('--authenticate_service_account', action='store_true',
                      dest='authenticate_service_account', default=False,
                      help='Authenticate using the default service account '
                      'for the Google Compute Engine VM in which appcfg is '
                      'being called')
    parser.add_option('--noauth_local_webserver', action='store_false',
                      dest='auth_local_webserver', default=True,
                      help='Do not run a local web server to handle redirects '
                      'during OAuth authorization.')
    parser.add_option('--called_by_gcloud',
                      action='store_true', default=False,
                      help=optparse.SUPPRESS_HELP)


    parser.add_option('--ignore_endpoints_failures', action='store_true',
                      dest='ignore_endpoints_failures', default=True,
                      help=optparse.SUPPRESS_HELP)
    parser.add_option('--no_ignore_endpoints_failures', action='store_false',
                      dest='ignore_endpoints_failures',
                      help=optparse.SUPPRESS_HELP)
    return parser

  def _MakeSpecificParser(self, action):
    """Creates a new parser with documentation specific to 'action'.

    Args:
      action: An Action instance to be used when initializing the new parser.

    Returns:
      A tuple containing:
      parser: An instance of OptionsParser customized to 'action'.
      options: The command line options after re-parsing.
    """
    parser = self._GetOptionParser()
    parser.set_usage(action.usage)
    parser.set_description('%s\n%s' % (action.short_desc, action.long_desc))
    action.options(self, parser)
    options, unused_args = parser.parse_args(self.argv[1:])
    return parser, options

  def _PrintHelpAndExit(self, exit_code=2):
    """Prints the parser's help message and exits the program.

    Args:
      exit_code: The integer code to pass to sys.exit().
    """
    self.parser.print_help()
    sys.exit(exit_code)

  def _GetRpcServer(self):
    """Returns an instance of an AbstractRpcServer.

    Returns:
      A new AbstractRpcServer, on which RPC calls can be made.

    Raises:
      RuntimeError: The user has request non-interactive authentication but the
        environment is not correct for that to work.
    """

    StatusUpdate('Host: %s' % self.options.server, self.error_fh)

    source = GetSourceName()

    dev_appserver = self.options.host in ['localhost', '127.0.0.1']

    if dev_appserver:
      if not self.rpc_server_class:
        self.rpc_server_class = appengine_rpc.HttpRpcServer
        if hasattr(self, 'runtime'):
          self.rpc_server_class.RUNTIME = self.runtime
      email = self.options.email
      if email is None:
        email = 'test@example.com'
        logging.info('Using debug user %s.  Override with --email', email)
      rpcserver = self.rpc_server_class(
          self.options.server,
          lambda: (email, 'password'),
          GetUserAgent(),
          source,
          host_override=self.options.host,
          save_cookies=self.options.save_cookies,

          secure=False)

      rpcserver.authenticated = True
      return rpcserver

    if not self.rpc_server_class:
      self.rpc_server_class = appengine_rpc_httplib2.HttpRpcServerOAuth2


    oauth2_parameters = self._GetOAuth2Parameters()


    return self.rpc_server_class(self.options.server, oauth2_parameters,
                                 GetUserAgent(), source,
                                 host_override=self.options.host,
                                 save_cookies=self.options.save_cookies,
                                 auth_tries=3,
                                 account_type='HOSTED_OR_GOOGLE',
                                 secure=self.options.secure,
                                 ignore_certs=self.options.ignore_certs,
                                 options=self.options)

  def _MaybeGetDevshellOAuth2AccessToken(self):
    """Returns a valid OAuth2 access token when running in Cloud Shell."""
    try:
      creds = devshell.DevshellCredentials()
      return creds.access_token
    except devshell.NoDevshellServer:
      return None

  def _GetOAuth2Parameters(self):
    """Returns appropriate an OAuth2Parameters object for authentication."""
    oauth2_parameters = (
        appengine_rpc_httplib2.HttpRpcServerOAuth2.OAuth2Parameters(
            access_token=(self.options.oauth2_access_token or
                          self._MaybeGetDevshellOAuth2AccessToken()),
            client_id=self.oauth_client_id,
            client_secret=self.oauth_client_secret,
            scope=self.oauth_scopes,
            refresh_token=self.options.oauth2_refresh_token,
            credential_file=self.options.oauth2_credential_file,
            token_uri=self._GetTokenUri()))
    return oauth2_parameters

  def _GetTokenUri(self):
    """Returns the OAuth2 token_uri, or None to use the default URI.

    Returns:
      A string that is the token_uri, or None.

    Raises:
      RuntimeError: The user has requested authentication for a service account
        but the environment is not correct for that to work.
    """
    if self.options.authenticate_service_account:



      url = '%s/%s/scopes' % (METADATA_BASE, SERVICE_ACCOUNT_BASE)
      try:
        vm_scopes_string = self.read_url_contents(url)
      except urllib2.URLError, e:
        raise RuntimeError('Could not obtain scope list from metadata service: '
                           '%s: %s. This may be because we are not running in '
                           'a Google Compute Engine VM.' % (url, e))
      vm_scopes = vm_scopes_string.split()
      missing = list(set(self.oauth_scopes).difference(vm_scopes))
      if missing:
        raise RuntimeError('Required scopes %s missing from %s. '
                           'This VM instance probably needs to be recreated '
                           'with the missing scopes.' % (missing, vm_scopes))
      return '%s/%s/token' % (METADATA_BASE, SERVICE_ACCOUNT_BASE)
    else:
      return None

  def _FindYaml(self, basepath, file_name):
    """Find yaml files in application directory.

    Args:
      basepath: Base application directory.
      file_name: Relative file path from basepath, without extension, to search
        for.

    Returns:
      Path to located yaml file if one exists, else None.
    """
    if not os.path.isdir(basepath):
      self.parser.error('Not a directory: %s' % basepath)



    alt_basepath = os.path.join(basepath, 'WEB-INF', 'appengine-generated')

    for yaml_basepath in (basepath, alt_basepath):
      for yaml_file in (file_name + '.yaml', file_name + '.yml'):
        yaml_path = os.path.join(yaml_basepath, yaml_file)
        if os.path.isfile(yaml_path):
          return yaml_path

    return None

  def _ParseAppInfoFromYaml(self, basepath, basename='app'):
    """Parses the app.yaml file.

    Args:
      basepath: The directory of the application.
      basename: The relative file path, from basepath, to search for.

    Returns:
      An AppInfoExternal object.
    """
    try:
      appyaml = self._ParseYamlFile(basepath, basename, appinfo_includes.Parse)
    except yaml_errors.EventListenerError, e:
      self.parser.error('Error parsing %s.yaml: %s.' % (
          os.path.join(basepath, basename), e))
    if not appyaml:
      if JavaSupported():
        if appcfg_java.IsWarFileWithoutYaml(basepath):
          java_app_update = appcfg_java.JavaAppUpdate(basepath, self.options)
          appyaml_string = java_app_update.GenerateAppYamlString([])
          appyaml = appinfo.LoadSingleAppInfo(appyaml_string)
        if not appyaml:
          self.parser.error('Directory contains neither an %s.yaml '
                            'configuration file nor a WEB-INF subdirectory '
                            'with web.xml and appengine-web.xml.' % basename)
      else:
        self.parser.error('Directory %r does not contain configuration file '
                          '%s.yaml' %
                          (os.path.abspath(basepath), basename))

    orig_application = appyaml.application
    orig_module = appyaml.module
    orig_version = appyaml.version
    if self.options.app_id:
      appyaml.application = self.options.app_id
    if self.options.module:
      appyaml.module = self.options.module
    if self.options.version:
      appyaml.version = self.options.version
    if self.options.runtime:
      appyaml.SetEffectiveRuntime(self.options.runtime)
    if self.options.env_variables:
      if appyaml.env_variables is None:
        appyaml.env_variables = appinfo.EnvironmentVariables()
      appyaml.env_variables.update(self.options.env_variables)
    if self.options.source_ref:
      try:
        combined_refs = '\n'.join(self.options.source_ref)
        appinfo.ValidateCombinedSourceReferencesString(combined_refs)
        if appyaml.beta_settings is None:
          appyaml.beta_settings = appinfo.BetaSettings()
        appyaml.beta_settings['source_reference'] = combined_refs
      except validation.ValidationError, e:
        self.parser.error(e.message)

    if not appyaml.application:
      self.parser.error('Expected -A app_id when application property in file '
                        '%s.yaml is not set.' % basename)

    msg = 'Application: %s' % appyaml.application
    if appyaml.application != orig_application:
      msg += ' (was: %s)' % orig_application
    if self.action.function is 'Update':

      if (appyaml.module is not None and
          appyaml.module != appinfo.DEFAULT_MODULE):
        msg += '; module: %s' % appyaml.module
        if appyaml.module != orig_module:
          msg += ' (was: %s)' % orig_module
      msg += '; version: %s' % appyaml.version
      if appyaml.version != orig_version:
        msg += ' (was: %s)' % orig_version
    StatusUpdate(msg, self.error_fh)
    return appyaml

  def _ParseYamlFile(self, basepath, basename, parser):
    """Parses a yaml file.

    Args:
      basepath: The base directory of the application.
      basename: The relative file path, from basepath, (with the '.yaml'
        stripped off).
      parser: the function or method used to parse the file.

    Returns:
      A single parsed yaml file or None if the file does not exist.
    """
    file_name = self._FindYaml(basepath, basename)
    if file_name is not None:
      fh = self.opener(file_name, 'r')
      try:
        defns = parser(fh, open_fn=self.opener)
      finally:
        fh.close()
      return defns
    return None

  def _ParseBackendsYaml(self, basepath):
    """Parses the backends.yaml file.

    Args:
      basepath: the directory of the application.

    Returns:
      A BackendsInfoExternal object or None if the file does not exist.
    """
    return self._ParseYamlFile(basepath, 'backends',
                               backendinfo.LoadBackendInfo)

  def _ParseIndexYaml(self, basepath, appyaml=None):
    """Parses the index.yaml file.

    Args:
      basepath: the directory of the application.
      appyaml: The app.yaml, if present.
    Returns:
      A single parsed yaml file or None if the file does not exist.
    """
    index_yaml = self._ParseYamlFile(basepath,
                                     'index',
                                     datastore_index.ParseIndexDefinitions)
    if not index_yaml:
      return None
    self._SetApplication(index_yaml, 'index', appyaml)

    return index_yaml

  def _SetApplication(self, dest_yaml, basename, appyaml=None):
    """Parses and sets the application property onto the dest_yaml parameter.

    The order of precendence is:
    1. Command line (-A application)
    2. Specified dest_yaml file
    3. App.yaml file

    This exits with a parse error if application is not present in any of these
    locations.

    Args:
      dest_yaml: The yaml object to set 'application' on.
      basename: The name of the dest_yaml file for use in errors.
      appyaml: The already parsed appyaml, if present. If none, this method will
          attempt to parse app.yaml.
    """
    if self.options.app_id:
      dest_yaml.application = self.options.app_id
    if not dest_yaml.application:
      if not appyaml:
        appyaml = self._ParseYamlFile(self.basepath,
                                      'app',
                                      appinfo_includes.Parse)
      if appyaml:
        dest_yaml.application = appyaml.application
      else:
        self.parser.error('Expected -A app_id when %s.yaml.application is not '
                          'set and app.yaml is not present.' % basename)

  def _ParseCronYaml(self, basepath, appyaml=None):
    """Parses the cron.yaml file.

    Args:
      basepath: the directory of the application.
      appyaml: The app.yaml, if present.

    Returns:
      A CronInfoExternal object or None if the file does not exist.
    """
    cron_yaml = self._ParseYamlFile(basepath, 'cron', croninfo.LoadSingleCron)
    if not cron_yaml:
      return None
    self._SetApplication(cron_yaml, 'cron', appyaml)

    return cron_yaml

  def _ParseQueueYaml(self, basepath, appyaml=None):
    """Parses the queue.yaml file.

    Args:
      basepath: the directory of the application.
      appyaml: The app.yaml, if present.

    Returns:
      A QueueInfoExternal object or None if the file does not exist.
    """
    queue_yaml = self._ParseYamlFile(basepath,
                                     'queue',
                                     queueinfo.LoadSingleQueue)
    if not queue_yaml:
      return None

    self._SetApplication(queue_yaml, 'queue', appyaml)
    return queue_yaml

  def _ParseDispatchYaml(self, basepath, appyaml=None):
    """Parses the dispatch.yaml file.

    Args:
      basepath: the directory of the application.
      appyaml: The app.yaml, if present.

    Returns:
      A DispatchInfoExternal object or None if the file does not exist.
    """
    dispatch_yaml = self._ParseYamlFile(basepath,
                                        'dispatch',
                                        dispatchinfo.LoadSingleDispatch)

    if not dispatch_yaml:
      return None

    self._SetApplication(dispatch_yaml, 'dispatch', appyaml)
    return dispatch_yaml

  def _ParseDosYaml(self, basepath, appyaml=None):
    """Parses the dos.yaml file.

    Args:
      basepath: the directory of the application.
      appyaml: The app.yaml, if present.

    Returns:
      A DosInfoExternal object or None if the file does not exist.
    """
    dos_yaml = self._ParseYamlFile(basepath, 'dos', dosinfo.LoadSingleDos)
    if not dos_yaml:
      return None

    self._SetApplication(dos_yaml, 'dos', appyaml)
    return dos_yaml

  def Help(self, action=None):
    """Prints help for a specific action.

    Args:
      action: If provided, print help for the action provided.

    Expects self.args[0], or 'action', to contain the name of the action in
    question.  Exits the program after printing the help message.
    """
    if not action:
      if len(self.args) > 1:
        self.args = [' '.join(self.args)]

      if len(self.args) != 1 or self.args[0] not in self.actions:
        self.parser.error('Expected a single action argument. '
                          ' Must be one of:\n' +
                          self._GetActionDescriptions())
      action = self.args[0]
    action = self.actions[action]
    self.parser, unused_options = self._MakeSpecificParser(action)
    self._PrintHelpAndExit(exit_code=0)

  def DownloadApp(self):
    """Downloads the given app+version."""
    if len(self.args) != 1:
      self.parser.error('\"download_app\" expects one non-option argument, '
                        'found ' + str(len(self.args)) + '.')

    out_dir = self.args[0]

    app_id = self.options.app_id
    if app_id is None:
      self.parser.error('You must specify an app ID via -A or --application.')

    module = self.options.module
    app_version = self.options.version



    if os.path.exists(out_dir):
      if not os.path.isdir(out_dir):
        self.parser.error('Cannot download to path "%s": '
                          'there\'s a file in the way.' % out_dir)
      elif os.listdir(out_dir):
        self.parser.error('Cannot download to path "%s": directory already '
                          'exists and it isn\'t empty.' % out_dir)

    rpcserver = self._GetRpcServer()

    DoDownloadApp(rpcserver, out_dir, app_id, module, app_version)

  def UpdateVersion(self, rpcserver, basepath, appyaml, module_yaml_path,
                    backend=None):
    """Updates and deploys a new appversion.

    Args:
      rpcserver: An AbstractRpcServer instance on which RPC calls can be made.
      basepath: The root directory of the version to update.
      appyaml: The AppInfoExternal object parsed from an app.yaml-like file.
      module_yaml_path: The (string) path to the yaml file, relative to the
        bundle directory.
      backend: The name of the backend to update, if any.

    Returns:
      An appinfo.AppInfoSummary if one was returned from the Deploy, None
      otherwise.

    Raises:
      RuntimeError: If go-app-builder fails to generate a mapping from relative
      paths to absolute paths, its stderr is raised.
    """















    runtime = appyaml.GetEffectiveRuntime()
    if appyaml.vm and (self.options.called_by_gcloud or runtime != 'go'):
      self.options.precompilation = False
    elif runtime == 'dart':
      self.options.precompilation = False
    elif runtime == 'go' and not self.options.precompilation:
      logging.warning('Precompilation is required for Go apps; '
                      'ignoring --no_precompilation')
      self.options.precompilation = True
    elif (runtime.startswith('java') and
          appinfo.JAVA_PRECOMPILED not in (appyaml.derived_file_type or [])):
      self.options.precompilation = False

    if runtime in GCLOUD_ONLY_RUNTIMES:
      raise RuntimeError('The runtime: \'%s\' is only supported with '
                         'gcloud.' % runtime)

    if self.options.precompilation:
      if not appyaml.derived_file_type:
        appyaml.derived_file_type = []
      if appinfo.PYTHON_PRECOMPILED not in appyaml.derived_file_type:
        appyaml.derived_file_type.append(appinfo.PYTHON_PRECOMPILED)

    paths = self.file_iterator(basepath, appyaml.skip_files, appyaml.runtime)
    openfunc = lambda path: self.opener(os.path.join(basepath, path), 'rb')

    if appyaml.GetEffectiveRuntime() == 'go':
      if appyaml.runtime == 'vm':
        raise RuntimeError(
            'The Go runtime with "vm: true" is only supported with gcloud.')

      sdk_base = os.path.normpath(os.path.join(
          google.appengine.__file__, '..', '..', '..'))

      gopath = os.environ.get('GOPATH')
      if not gopath:
        gopath = os.path.join(sdk_base, 'gopath')





      goroot = os.path.join(sdk_base, 'goroot')
      if not os.path.exists(goroot):

        goroot = None
      gab = os.path.join(sdk_base, GO_APP_BUILDER)
      if os.path.exists(gab):
        app_paths = list(paths)
        go_files = [f for f in app_paths
                    if f.endswith('.go') and not appyaml.nobuild_files.match(f)]
        if not go_files:
          raise RuntimeError('no Go source files to upload '
                             '(-nobuild_files applied)')
        gab_argv = [
            gab,
            '-api_version', appyaml.api_version,
            '-app_base', self.basepath,
            '-arch', '6',
            '-gopath', gopath,
            '-print_extras',
        ]
        if goroot:
          gab_argv.extend(['-goroot', goroot])
        if appyaml.runtime == 'vm':
          gab_argv.append('-vm')
        gab_argv.extend(go_files)

        env = {
            'GOOS': 'linux',
            'GOARCH': 'amd64',
        }
        logging.info('Invoking go-app-builder: %s', ' '.join(gab_argv))
        try:
          p = subprocess.Popen(gab_argv, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=env)
          (stdout, stderr) = p.communicate()
        except Exception, e:
          raise RuntimeError('failed running go-app-builder', e)
        if p.returncode != 0:
          raise RuntimeError(stderr)




        overlay = dict([l.split('|') for l in stdout.split('\n') if l])
        logging.info('GOPATH overlay: %s', overlay)

        def Open(path):
          if path in overlay:
            return self.opener(overlay[path], 'rb')
          return self.opener(os.path.join(basepath, path), 'rb')
        paths = app_paths + overlay.keys()
        openfunc = Open

    appversion = AppVersionUpload(
        rpcserver,
        appyaml,
        module_yaml_path=module_yaml_path,
        backend=backend,
        error_fh=self.error_fh,
        usage_reporting=self.options.usage_reporting,
        ignore_endpoints_failures=self.options.ignore_endpoints_failures)
    return appversion.DoUpload(paths, openfunc)

  def UpdateUsingSpecificFiles(self):
    """Updates and deploys new app versions based on given config files."""
    rpcserver = self._GetRpcServer()
    all_files = [self.basepath] + self.args
    has_python25_version = False

    for yaml_path in all_files:
      file_name = os.path.basename(yaml_path)
      self.basepath = os.path.dirname(yaml_path)
      if not self.basepath:
        self.basepath = '.'
      module_yaml = self._ParseAppInfoFromYaml(self.basepath,
                                               os.path.splitext(file_name)[0])
      if module_yaml.runtime == 'python':
        has_python25_version = True



      if not module_yaml.module and file_name != 'app.yaml':
        ErrorUpdate("Error: 'module' parameter not specified in %s" %
                    yaml_path)
        continue
      self.UpdateVersion(rpcserver, self.basepath, module_yaml, file_name)
    if has_python25_version:
      MigratePython27Notice()

  def Update(self):
    """Updates and deploys a new appversion and global app configs."""
    if not os.path.isdir(self.basepath):

      self.UpdateUsingSpecificFiles()
      return

    if JavaSupported() and appcfg_java.IsWarFileWithoutYaml(self.basepath):
      java_app_update = appcfg_java.JavaAppUpdate(self.basepath, self.options)
      self.options.compile_jsps = not java_app_update.app_engine_web_xml.vm






      sdk_root = os.path.dirname(appcfg_java.__file__)
      self.stage_dir = java_app_update.CreateStagingDirectory(sdk_root)
      try:
        appyaml = self._ParseAppInfoFromYaml(
            self.stage_dir,
            basename=os.path.splitext(APP_YAML_FILENAME)[0])
        self._UpdateWithParsedAppYaml(appyaml, self.stage_dir)
      finally:
        if self.options.retain_upload_dir:
          StatusUpdate(
              'Temporary staging directory left in %s' % self.stage_dir,
              self.error_fh)
        else:
          shutil.rmtree(self.stage_dir)
    else:
      appyaml = self._ParseAppInfoFromYaml(
          self.basepath,
          basename=os.path.splitext(APP_YAML_FILENAME)[0])
      self._UpdateWithParsedAppYaml(appyaml, self.basepath)

  def _UpdateWithParsedAppYaml(self, appyaml, basepath):
    """Completes update command.

    Helper to Update.

    Args:
      appyaml: AppInfoExternal for the app.
      basepath: Path where application's files can be found.
    """
    self.runtime = appyaml.runtime
    rpcserver = self._GetRpcServer()




    if self.options.skip_sdk_update_check:
      logging.info('Skipping update check')
    else:
      updatecheck = self.update_check_class(rpcserver, appyaml)
      updatecheck.CheckForUpdates()

    def _AbortAppMismatch(yaml_name):
      StatusUpdate('Error: Aborting upload because application in %s does not '
                   'match application in app.yaml' % yaml_name, self.error_fh)


    dos_yaml = self._ParseDosYaml(basepath, appyaml)
    if dos_yaml and dos_yaml.application != appyaml.application:
      _AbortAppMismatch('dos.yaml')
      return

    queue_yaml = self._ParseQueueYaml(basepath, appyaml)
    if queue_yaml and queue_yaml.application != appyaml.application:
      _AbortAppMismatch('queue.yaml')
      return

    cron_yaml = self._ParseCronYaml(basepath, appyaml)
    if cron_yaml and cron_yaml.application != appyaml.application:
      _AbortAppMismatch('cron.yaml')
      return

    index_defs = self._ParseIndexYaml(basepath, appyaml)
    if index_defs and index_defs.application != appyaml.application:
      _AbortAppMismatch('index.yaml')
      return

    dispatch_yaml = self._ParseDispatchYaml(basepath, appyaml)
    if dispatch_yaml and dispatch_yaml.application != appyaml.application:
      _AbortAppMismatch('dispatch.yaml')
      return

    self.UpdateVersion(rpcserver, basepath, appyaml, APP_YAML_FILENAME)

    if appyaml.runtime == 'python':
      MigratePython27Notice()


    if self.options.backends:
      self.BackendsUpdate()






    if index_defs:
      index_upload = IndexDefinitionUpload(rpcserver, index_defs, self.error_fh)
      try:
        index_upload.DoUpload()
      except urllib2.HTTPError, e:
        ErrorUpdate('Error %d: --- begin server output ---\n'
                    '%s\n--- end server output ---' %
                    (e.code, e.read().rstrip('\n')))
        print >> self.error_fh, (
            'Your app was updated, but there was an error updating your '
            'indexes. Please retry later with appcfg.py update_indexes.')


    if cron_yaml:
      cron_upload = CronEntryUpload(rpcserver, cron_yaml, self.error_fh)
      try:
        cron_upload.DoUpload()
      except urllib2.HTTPError, e:
        ErrorUpdate('Error %d: --- begin server output ---\n'
                    '%s\n--- end server output ---' %
                    (e.code, e.read().rstrip('\n')))
        print >> self.error_fh, (
            'Your app was updated, but there was an error updating your '
            'cron tasks. Please retry later with appcfg.py update_cron.')


    if queue_yaml:
      queue_upload = QueueEntryUpload(rpcserver, queue_yaml, self.error_fh)
      try:
        queue_upload.DoUpload()
      except urllib2.HTTPError, e:
        ErrorUpdate('Error %d: --- begin server output ---\n'
                    '%s\n--- end server output ---' %
                    (e.code, e.read().rstrip('\n')))
        print >> self.error_fh, (
            'Your app was updated, but there was an error updating your '
            'queues. Please retry later with appcfg.py update_queues.')


    if dos_yaml:
      dos_upload = DosEntryUpload(rpcserver, dos_yaml, self.error_fh)
      dos_upload.DoUpload()


    if dispatch_yaml:
      dispatch_upload = DispatchEntryUpload(rpcserver,
                                            dispatch_yaml,
                                            self.error_fh)
      dispatch_upload.DoUpload()

  def _UpdateOptions(self, parser):
    """Adds update-specific options to 'parser'.

    Args:
      parser: An instance of OptionsParser.
    """
    parser.add_option('--no_precompilation', action='store_false',
                      dest='precompilation', default=True,
                      help='Disable automatic precompilation '
                      '(ignored for Go apps).')
    parser.add_option('--backends', action='store_true',
                      dest='backends', default=False,
                      help='Update backends when performing appcfg update.')
    parser.add_option('--no_usage_reporting', action='store_false',
                      dest='usage_reporting', default=True,
                      help='Disable usage reporting.')
    if JavaSupported():
      appcfg_java.AddUpdateOptions(parser)

  def VacuumIndexes(self):
    """Deletes unused indexes."""
    if self.args:
      self.parser.error('Expected a single <directory> argument.')


    index_defs = self._ParseIndexYaml(self.basepath)
    if index_defs is None:
      index_defs = datastore_index.IndexDefinitions()

    rpcserver = self._GetRpcServer()
    vacuum = VacuumIndexesOperation(rpcserver,
                                    self.options.force_delete)
    vacuum.DoVacuum(index_defs)

  def _VacuumIndexesOptions(self, parser):
    """Adds vacuum_indexes-specific options to 'parser'.

    Args:
      parser: An instance of OptionsParser.
    """
    parser.add_option('-f', '--force', action='store_true', dest='force_delete',
                      default=False,
                      help='Force deletion without being prompted.')

  def UpdateCron(self):
    """Updates any new or changed cron definitions."""
    if self.args:
      self.parser.error('Expected a single <directory> argument.')

    rpcserver = self._GetRpcServer()


    cron_yaml = self._ParseCronYaml(self.basepath)
    if cron_yaml:
      cron_upload = CronEntryUpload(rpcserver, cron_yaml, self.error_fh)
      cron_upload.DoUpload()
    else:
      print >>self.error_fh, (
          'Could not find cron configuration. No action taken.')

  def UpdateIndexes(self):
    """Updates indexes."""
    if self.args:
      self.parser.error('Expected a single <directory> argument.')

    rpcserver = self._GetRpcServer()


    index_defs = self._ParseIndexYaml(self.basepath)
    if index_defs:
      index_upload = IndexDefinitionUpload(rpcserver, index_defs, self.error_fh)
      index_upload.DoUpload()
    else:
      print >>self.error_fh, (
          'Could not find index configuration. No action taken.')

  def UpdateQueues(self):
    """Updates any new or changed task queue definitions."""
    if self.args:
      self.parser.error('Expected a single <directory> argument.')
    rpcserver = self._GetRpcServer()


    queue_yaml = self._ParseQueueYaml(self.basepath)
    if queue_yaml:
      queue_upload = QueueEntryUpload(rpcserver, queue_yaml, self.error_fh)
      queue_upload.DoUpload()
    else:
      print >>self.error_fh, (
          'Could not find queue configuration. No action taken.')

  def UpdateDispatch(self):
    """Updates new or changed dispatch definitions."""
    if self.args:
      self.parser.error('Expected a single <directory> argument.')

    rpcserver = self._GetRpcServer()


    dispatch_yaml = self._ParseDispatchYaml(self.basepath)
    if dispatch_yaml:
      dispatch_upload = DispatchEntryUpload(rpcserver,
                                            dispatch_yaml,
                                            self.error_fh)
      dispatch_upload.DoUpload()
    else:
      print >>self.error_fh, ('Could not find dispatch configuration. No action'
                              ' taken.')

  def UpdateDos(self):
    """Updates any new or changed dos definitions."""
    if self.args:
      self.parser.error('Expected a single <directory> argument.')
    rpcserver = self._GetRpcServer()


    dos_yaml = self._ParseDosYaml(self.basepath)
    if dos_yaml:
      dos_upload = DosEntryUpload(rpcserver, dos_yaml, self.error_fh)
      dos_upload.DoUpload()
    else:
      print >>self.error_fh, (
          'Could not find dos configuration. No action taken.')

  def BackendsAction(self):
    """Placeholder; we never expect this action to be invoked."""
    pass

  def BackendsPhpCheck(self, appyaml):
    """Don't support backends with the PHP runtime.

    This should be used to prevent use of backends update/start/configure
    with the PHP runtime.  We continue to allow backends
    stop/delete/list/rollback just in case there are existing PHP backends.

    Args:
      appyaml: A parsed app.yaml file.
    """
    if appyaml.runtime.startswith('php'):
      _PrintErrorAndExit(
          self.error_fh,
          'Error: Backends are not supported with the PHP runtime. '
          'Please use Modules instead.\n')

  def BackendsYamlCheck(self, basepath, appyaml, backend=None):
    """Check the backends.yaml file is sane and which backends to update."""


    if appyaml.backends:
      self.parser.error('Backends are not allowed in app.yaml.')

    backends_yaml = self._ParseBackendsYaml(basepath)
    appyaml.backends = backends_yaml.backends

    if not appyaml.backends:
      self.parser.error('No backends found in backends.yaml.')

    backends = []
    for backend_entry in appyaml.backends:
      entry = backendinfo.LoadBackendEntry(backend_entry.ToYAML())
      if entry.name in backends:
        self.parser.error('Duplicate entry for backend: %s.' % entry.name)
      else:
        backends.append(entry.name)

    backends_to_update = []

    if backend:

      if backend in backends:
        backends_to_update = [backend]
      else:
        self.parser.error("Backend '%s' not found in backends.yaml." %
                          backend)
    else:

      backends_to_update = backends

    return backends_to_update

  def BackendsUpdate(self):
    """Updates a backend."""
    self.backend = None
    if len(self.args) == 1:
      self.backend = self.args[0]
    elif len(self.args) > 1:
      self.parser.error('Expected an optional <backend> argument.')
    if JavaSupported() and appcfg_java.IsWarFileWithoutYaml(self.basepath):
      java_app_update = appcfg_java.JavaAppUpdate(self.basepath, self.options)
      self.options.compile_jsps = True
      sdk_root = os.path.dirname(appcfg_java.__file__)
      basepath = java_app_update.CreateStagingDirectory(sdk_root)
    else:
      basepath = self.basepath

    yaml_file_basename = 'app'
    appyaml = self._ParseAppInfoFromYaml(basepath,
                                         basename=yaml_file_basename)
    BackendsStatusUpdate(appyaml.runtime, self.error_fh)
    self.BackendsPhpCheck(appyaml)
    rpcserver = self._GetRpcServer()

    backends_to_update = self.BackendsYamlCheck(basepath, appyaml, self.backend)
    for backend in backends_to_update:
      self.UpdateVersion(rpcserver, basepath, appyaml, yaml_file_basename,
                         backend=backend)

  def BackendsList(self):
    """Lists all backends for an app."""
    if self.args:
      self.parser.error('Expected no arguments.')




    appyaml = self._ParseAppInfoFromYaml(self.basepath)
    BackendsStatusUpdate(appyaml.runtime, self.error_fh)
    rpcserver = self._GetRpcServer()
    response = rpcserver.Send('/api/backends/list', app_id=appyaml.application)
    print >> self.out_fh, response

  def BackendsRollback(self):
    """Does a rollback of an existing transaction on this backend."""
    if len(self.args) != 1:
      self.parser.error('Expected a single <backend> argument.')

    self._Rollback(self.args[0])

  def BackendsStart(self):
    """Starts a backend."""
    if len(self.args) != 1:
      self.parser.error('Expected a single <backend> argument.')

    backend = self.args[0]
    appyaml = self._ParseAppInfoFromYaml(self.basepath)
    BackendsStatusUpdate(appyaml.runtime, self.error_fh)
    self.BackendsPhpCheck(appyaml)
    rpcserver = self._GetRpcServer()
    response = rpcserver.Send('/api/backends/start',
                              app_id=appyaml.application,
                              backend=backend)
    print >> self.out_fh, response

  def BackendsStop(self):
    """Stops a backend."""
    if len(self.args) != 1:
      self.parser.error('Expected a single <backend> argument.')

    backend = self.args[0]
    appyaml = self._ParseAppInfoFromYaml(self.basepath)
    BackendsStatusUpdate(appyaml.runtime, self.error_fh)
    rpcserver = self._GetRpcServer()
    response = rpcserver.Send('/api/backends/stop',
                              app_id=appyaml.application,
                              backend=backend)
    print >> self.out_fh, response

  def BackendsDelete(self):
    """Deletes a backend."""
    if len(self.args) != 1:
      self.parser.error('Expected a single <backend> argument.')

    backend = self.args[0]
    appyaml = self._ParseAppInfoFromYaml(self.basepath)
    BackendsStatusUpdate(appyaml.runtime, self.error_fh)
    rpcserver = self._GetRpcServer()
    response = rpcserver.Send('/api/backends/delete',
                              app_id=appyaml.application,
                              backend=backend)
    print >> self.out_fh, response

  def BackendsConfigure(self):
    """Changes the configuration of an existing backend."""
    if len(self.args) != 1:
      self.parser.error('Expected a single <backend> argument.')

    backend = self.args[0]
    appyaml = self._ParseAppInfoFromYaml(self.basepath)
    BackendsStatusUpdate(appyaml.runtime, self.error_fh)
    self.BackendsPhpCheck(appyaml)
    backends_yaml = self._ParseBackendsYaml(self.basepath)
    rpcserver = self._GetRpcServer()
    response = rpcserver.Send('/api/backends/configure',
                              app_id=appyaml.application,
                              backend=backend,
                              payload=backends_yaml.ToYAML())
    print >> self.out_fh, response

  def ListVersions(self):
    """Lists all versions for an app."""
    if len(self.args) == 0:
      if not self.options.app_id:
        self.parser.error('Expected <directory> argument or -A <app id>.')
      app_id = self.options.app_id
    elif len(self.args) == 1:
      if self.options.app_id:
        self.parser.error('<directory> argument is not needed with -A.')
      appyaml = self._ParseAppInfoFromYaml(self.args[0])
      app_id = appyaml.application
    else:
      self.parser.error('Expected 1 argument, not %d.' % len(self.args))

    rpcserver = self._GetRpcServer()
    response = rpcserver.Send('/api/versions/list', app_id=app_id)

    parsed_response = yaml.safe_load(response)
    if not parsed_response:
      print >> self.out_fh, ('No versions uploaded for app: %s.' % app_id)
    else:
      print >> self.out_fh, response

  def DeleteVersion(self):
    """Deletes the specified version for an app."""
    if not (self.options.app_id and self.options.version):
      self.parser.error('Expected an <app_id> argument, a <version> argument '
                        'and an optional <module> argument.')
    if self.options.module:
      module = self.options.module
    else:
      module = ''

    rpcserver = self._GetRpcServer()
    response = rpcserver.Send('/api/versions/delete',
                              app_id=self.options.app_id,
                              version_match=self.options.version,
                              module=module)

    print >> self.out_fh, response

  def _LockingAction(self, url):
    """Changes the locking state for a given version."""
    if len(self.args) == 1:
      appyaml = self._ParseAppInfoFromYaml(self.args[0])
      app_id = appyaml.application
      module = appyaml.module or ''
      version = appyaml.version
    elif not self.args:
      if not (self.options.app_id and self.options.version):
        self.parser.error(
            ('Expected a <directory> argument or both --application and '
             '--version flags.'))
      module = ''
    else:
      self._PrintHelpAndExit()



    if self.options.app_id:
      app_id = self.options.app_id
    if self.options.module:
      module = self.options.module
    if self.options.version:
      version = self.options.version

    rpcserver = self._GetRpcServer()
    DoLockAction(
        url,
        rpcserver,
        app_id, version, module,
        self.options.instance,
        self.out_fh).Do()

  def DebugAction(self):
    """Sets the specified version and instance for an app to be debuggable."""
    self._LockingAction('/api/vms/debug')

  def LockAction(self):
    """Locks the specified version and instance for an app."""
    self._LockingAction('/api/vms/lock')

  def _LockActionOptions(self, parser):
    """Adds lock/unlock-specific options to 'parser'.

    Args:
      parser: An instance of OptionsParser.
    """
    parser.add_option('-I', '--instance', type='string', dest='instance',
                      help='Instance to lock/unlock.')

  def PrepareVmRuntimeAction(self):
    """Prepare the application for vm runtimes and return state."""
    if not self.options.app_id:
      self.parser.error('Expected an --application argument')
    rpcserver = self._GetRpcServer()
    response = rpcserver.Send('/api/vms/prepare',
                              app_id=self.options.app_id)
    print >> self.out_fh, response

  def _ParseAndValidateModuleYamls(self, yaml_paths):
    """Validates given yaml paths and returns the parsed yaml objects.

    Args:
      yaml_paths: List of paths to AppInfo yaml files.

    Returns:
      List of parsed AppInfo yamls.
    """
    results = []
    app_id = None
    last_yaml_path = None
    for yaml_path in yaml_paths:
      if not os.path.isfile(yaml_path):
        _PrintErrorAndExit(
            self.error_fh,
            ("Error: The given path '%s' is not to a YAML configuration "
             "file.\n") % yaml_path)
      file_name = os.path.basename(yaml_path)
      base_path = os.path.dirname(yaml_path)
      if not base_path:
        base_path = '.'
      module_yaml = self._ParseAppInfoFromYaml(base_path,
                                               os.path.splitext(file_name)[0])

      if not module_yaml.module and file_name != 'app.yaml':
        _PrintErrorAndExit(
            self.error_fh,
            "Error: 'module' parameter not specified in %s" % yaml_path)



      if app_id is not None and module_yaml.application != app_id:
        _PrintErrorAndExit(
            self.error_fh,
            "Error: 'application' value '%s' in %s does not match the value "
            "'%s', found in %s" % (module_yaml.application,
                                   yaml_path,
                                   app_id,
                                   last_yaml_path))
      app_id = module_yaml.application
      last_yaml_path = yaml_path
      results.append(module_yaml)

    return results

  def _ModuleAction(self, action_path):
    """Process flags and yaml files and make a call to the given path.

    The 'start_module_version' and 'stop_module_version' actions are extremely
    similar in how they process input to appcfg.py and only really differ in
    what path they hit on the RPCServer.

    Args:
      action_path: Path on the RPCServer to send the call to.
    """

    modules_to_process = []
    if not self.args:

      if not (self.options.app_id and
              self.options.module and
              self.options.version):
        _PrintErrorAndExit(self.error_fh,
                           'Expected at least one <file> argument or the '
                           '--application, --module and --version flags to'
                           ' be set.')
      else:
        modules_to_process.append((self.options.app_id,
                                   self.options.module,
                                   self.options.version))
    else:


      if self.options.module:

        _PrintErrorAndExit(self.error_fh,
                           'You may not specify a <file> argument with the '
                           '--module flag.')

      module_yamls = self._ParseAndValidateModuleYamls(self.args)
      for serv_yaml in module_yamls:


        app_id = serv_yaml.application
        modules_to_process.append((self.options.app_id or serv_yaml.application,
                                   serv_yaml.module or appinfo.DEFAULT_MODULE,
                                   self.options.version or serv_yaml.version))

    rpcserver = self._GetRpcServer()


    for app_id, module, version in modules_to_process:
      response = rpcserver.Send(action_path,
                                app_id=app_id,
                                module=module,
                                version=version)
      print >> self.out_fh, response

  def StartModuleVersion(self):
    """Starts one or more versions."""
    self._ModuleAction('/api/modules/start')

  def StopModuleVersion(self):
    """Stops one or more versions."""
    self._ModuleAction('/api/modules/stop')

  def Rollback(self):
    """Does a rollback of an existing transaction for this app version."""
    self._Rollback()

  def _RollbackOptions(self, parser):
    """Adds rollback-specific options to parser.

    Args:
      parser: An instance of OptionsParser.
    """
    parser.add_option('--force_rollback', action='store_true',
                      dest='force_rollback', default=False,
                      help='Force rollback.')

  def _Rollback(self, backend=None):
    """Does a rollback of an existing transaction.

    Args:
      backend: name of a backend to rollback, or None

    If a backend is specified the rollback will affect only that backend, if no
    backend is specified the rollback will affect the current app version.
    """
    if os.path.isdir(self.basepath):
      module_yaml = self._ParseAppInfoFromYaml(self.basepath)
    else:

      file_name = os.path.basename(self.basepath)
      self.basepath = os.path.dirname(self.basepath)
      if not self.basepath:
        self.basepath = '.'
      module_yaml = self._ParseAppInfoFromYaml(self.basepath,
                                               os.path.splitext(file_name)[0])

    appversion = AppVersionUpload(self._GetRpcServer(), module_yaml,
                                  module_yaml_path='app.yaml',
                                  backend=backend)

    appversion.in_transaction = True




    force_rollback = False
    if hasattr(self.options, 'force_rollback'):
      force_rollback = self.options.force_rollback

    appversion.Rollback(force_rollback)

  def SetDefaultVersion(self):
    """Sets the default version."""
    module = ''
    if len(self.args) == 1:



      stored_modules = self.options.module
      self.options.module = None
      try:
        appyaml = self._ParseAppInfoFromYaml(self.args[0])
      finally:
        self.options.module = stored_modules

      app_id = appyaml.application
      module = appyaml.module or ''
      version = appyaml.version
    elif not self.args:
      if not (self.options.app_id and self.options.version):
        self.parser.error(
            ('Expected a <directory> argument or both --application and '
             '--version flags.'))
    else:
      self._PrintHelpAndExit()


    if self.options.app_id:
      app_id = self.options.app_id
    if self.options.module:
      module = self.options.module
    if self.options.version:
      version = self.options.version

    version_setter = DefaultVersionSet(self._GetRpcServer(),
                                       app_id,
                                       module,
                                       version,
                                       self.error_fh)
    version_setter.SetVersion()


  def MigrateTraffic(self):
    """Migrates traffic."""
    module = 'default'
    if len(self.args) == 1:
      appyaml = self._ParseAppInfoFromYaml(self.args[0])
      app_id = appyaml.application
      module = appyaml.module or 'default'
      version = appyaml.version
    elif not self.args:
      if not (self.options.app_id and self.options.version):
        self.parser.error(
            ('Expected a <directory> argument or both --application and '
             '--version flags.'))
    else:
      self._PrintHelpAndExit()


    if self.options.app_id:
      app_id = self.options.app_id
    if self.options.module:
      module = self.options.module
    if self.options.version:
      version = self.options.version

    if module not in ['', 'default']:
      StatusUpdate('migrate_traffic does not support non-default module at '
                   'this time.')
      return

    traffic_migrator = TrafficMigrator(
        self._GetRpcServer(), app_id, version, self.error_fh)
    traffic_migrator.MigrateTraffic()

  def RequestLogs(self):
    """Write request logs to a file."""

    args_length = len(self.args)
    module = ''
    if args_length == 2:
      appyaml = self._ParseAppInfoFromYaml(self.args.pop(0))
      app_id = appyaml.application
      module = appyaml.module or ''
      version = appyaml.version
    elif args_length == 1:
      if not (self.options.app_id and self.options.version):
        self.parser.error(
            ('Expected the --application and --version flags if <directory> '
             'argument is not specified.'))
    else:
      self._PrintHelpAndExit()


    if self.options.app_id:
      app_id = self.options.app_id
    if self.options.module:
      module = self.options.module
    if self.options.version:
      version = self.options.version

    if (self.options.severity is not None and
        not 0 <= self.options.severity <= MAX_LOG_LEVEL):
      self.parser.error(
          'Severity range is 0 (DEBUG) through %s (CRITICAL).' % MAX_LOG_LEVEL)

    if self.options.num_days is None:
      self.options.num_days = int(not self.options.append)

    try:
      end_date = self._ParseEndDate(self.options.end_date)
    except (TypeError, ValueError):
      self.parser.error('End date must be in the format YYYY-MM-DD.')

    rpcserver = self._GetRpcServer()

    logs_requester = LogsRequester(rpcserver,
                                   app_id,
                                   module,
                                   version,
                                   self.args[0],
                                   self.options.num_days,
                                   self.options.append,
                                   self.options.severity,
                                   end_date,
                                   self.options.vhost,
                                   self.options.include_vhost,
                                   self.options.include_all,
                                   time_func=self.time_func)
    logs_requester.DownloadLogs()

  @staticmethod
  def _ParseEndDate(date, time_func=time.time):
    """Translates an ISO 8601 date to a date object.

    Args:
      date: A date string as YYYY-MM-DD.
      time_func: A time.time() compatible function, which can be overridden for
        testing.

    Returns:
      A date object representing the last day of logs to get.
      If no date is given, returns today in the US/Pacific timezone.
    """
    if not date:
      return PacificDate(time_func())
    return datetime.date(*[int(i) for i in date.split('-')])

  def _RequestLogsOptions(self, parser):
    """Adds request_logs-specific options to 'parser'.

    Args:
      parser: An instance of OptionsParser.
    """
    parser.add_option('-n', '--num_days', type='int', dest='num_days',
                      action='store', default=None,
                      help='Number of days worth of log data to get. '
                      'The cut-off point is midnight US/Pacific. '
                      'Use 0 to get all available logs. '
                      'Default is 1, unless --append is also given; '
                      'then the default is 0.')
    parser.add_option('-a', '--append', dest='append',
                      action='store_true', default=False,
                      help='Append to existing file.')
    parser.add_option('--severity', type='int', dest='severity',
                      action='store', default=None,
                      help='Severity of app-level log messages to get. '
                      'The range is 0 (DEBUG) through 4 (CRITICAL). '
                      'If omitted, only request logs are returned.')
    parser.add_option('--vhost', type='string', dest='vhost',
                      action='store', default=None,
                      help='The virtual host of log messages to get. '
                      'If omitted, all log messages are returned.')
    parser.add_option('--include_vhost', dest='include_vhost',
                      action='store_true', default=False,
                      help='Include virtual host in log messages.')
    parser.add_option('--include_all', dest='include_all',
                      action='store_true', default=None,
                      help='Include everything in log messages.')
    parser.add_option('--end_date', dest='end_date',
                      action='store', default='',
                      help='End date (as YYYY-MM-DD) of period for log data. '
                      'Defaults to today.')

  def CronInfo(self, now=None, output=sys.stdout):
    """Displays information about cron definitions.

    Args:
      now: used for testing.
      output: Used for testing.
    """
    if self.args:
      self.parser.error('Expected a single <directory> argument.')
    if now is None:
      now = datetime.datetime.utcnow()

    cron_yaml = self._ParseCronYaml(self.basepath)
    if cron_yaml and cron_yaml.cron:
      for entry in cron_yaml.cron:
        description = entry.description
        if not description:
          description = '<no description>'
        if not entry.timezone:
          entry.timezone = 'UTC'

        print >>output, '\n%s:\nURL: %s\nSchedule: %s (%s)' % (description,
                                                               entry.url,
                                                               entry.schedule,
                                                               entry.timezone)
        if entry.timezone != 'UTC':
          print >>output, ('Note: Schedules with timezones won\'t be calculated'
                           ' correctly here')
        schedule = groctimespecification.GrocTimeSpecification(entry.schedule)

        matches = schedule.GetMatches(now, self.options.num_runs)
        for match in matches:
          print >>output, '%s, %s from now' % (
              match.strftime('%Y-%m-%d %H:%M:%SZ'), match - now)

  def _CronInfoOptions(self, parser):
    """Adds cron_info-specific options to 'parser'.

    Args:
      parser: An instance of OptionsParser.
    """
    parser.add_option('-n', '--num_runs', type='int', dest='num_runs',
                      action='store', default=5,
                      help='Number of runs of each cron job to display'
                      'Default is 5')

  def _CheckRequiredLoadOptions(self):
    """Checks that upload/download options are present."""
    for option in ['filename']:
      if getattr(self.options, option) is None:
        self.parser.error('Option \'%s\' is required.' % option)
    if not self.options.url:
      self.parser.error('You must have google.appengine.ext.remote_api.handler '
                        'assigned to an endpoint in app.yaml, or provide '
                        'the url of the handler via the \'url\' option.')

  def InferRemoteApiUrl(self, appyaml):
    """Uses app.yaml to determine the remote_api endpoint.

    Args:
      appyaml: A parsed app.yaml file.

    Returns:
      The url of the remote_api endpoint as a string, or None
    """

    handlers = appyaml.handlers
    handler_suffixes = ['remote_api/handler.py',
                        'remote_api.handler.application']
    app_id = appyaml.application
    for handler in handlers:
      if hasattr(handler, 'script') and handler.script:
        if any(handler.script.endswith(suffix) for suffix in handler_suffixes):
          server = self.options.server
          url = handler.url
          if url.endswith('(/.*)?'):


            url = url[:-6]
          if server == 'appengine.google.com':
            return 'http://%s.appspot.com%s' % (app_id, url)
          else:
            match = re.match(PREFIXED_BY_ADMIN_CONSOLE_RE, server)
            if match:
              return 'http://%s%s%s' % (app_id, match.group(1), url)
            else:
              return 'http://%s%s' % (server, url)
    return None

  def RunBulkloader(self, arg_dict):
    """Invokes the bulkloader with the given keyword arguments.

    Args:
      arg_dict: Dictionary of arguments to pass to bulkloader.Run().
    """

    try:

      import sqlite3
    except ImportError:
      logging.error('upload_data action requires SQLite3 and the python '
                    'sqlite3 module (included in python since 2.5).')
      sys.exit(1)

    sys.exit(bulkloader.Run(arg_dict, self._GetOAuth2Parameters()))

  def _SetupLoad(self):
    """Performs common verification and set up for upload and download."""

    if len(self.args) != 1 and not self.options.url:
      self.parser.error('Expected either --url or a single <directory> '
                        'argument.')

    if len(self.args) == 1:
      self.basepath = self.args[0]
      appyaml = self._ParseAppInfoFromYaml(self.basepath)

      self.options.app_id = appyaml.application

      if not self.options.url:
        url = self.InferRemoteApiUrl(appyaml)
        if url is not None:
          self.options.url = url

    self._CheckRequiredLoadOptions()

    if self.options.batch_size < 1:
      self.parser.error('batch_size must be 1 or larger.')



    if verbosity == 1:
      logging.getLogger().setLevel(logging.INFO)
      self.options.debug = False
    else:
      logging.getLogger().setLevel(logging.DEBUG)
      self.options.debug = True

  def _MakeLoaderArgs(self):
    """Returns a dict made from many attributes of self.options, plus others.

    See body for list of self.options attributes included. In addition, result
    includes
      'application' = self.options.app_id
      'throttle_class' = self.throttle_class

    Returns:
      A dict.
    """
    args = dict([(arg_name, getattr(self.options, arg_name, None)) for
                 arg_name in (
                     'url',
                     'filename',
                     'batch_size',
                     'kind',
                     'num_threads',
                     'bandwidth_limit',
                     'rps_limit',
                     'http_limit',
                     'db_filename',
                     'config_file',
                     'auth_domain',
                     'has_header',
                     'loader_opts',
                     'log_file',
                     'debug',
                     'exporter_opts',
                     'mapper_opts',
                     'result_db_filename',
                     'dry_run',
                     'dump',
                     'restore',
                     'namespace',
                     'create_config',
                     )])
    args['application'] = self.options.app_id
    args['throttle_class'] = self.throttle_class
    return args

  def PerformDownload(self, run_fn=None):
    """Performs a datastore download via the bulkloader.

    Args:
      run_fn: Function to invoke the bulkloader, used for testing.
    """
    if run_fn is None:
      run_fn = self.RunBulkloader
    self._SetupLoad()

    StatusUpdate('Downloading data records.', self.error_fh)

    args = self._MakeLoaderArgs()
    args['download'] = bool(args['config_file'])
    args['has_header'] = False
    args['map'] = False
    args['dump'] = not args['config_file']
    args['restore'] = False
    args['create_config'] = False

    run_fn(args)

  def PerformUpload(self, run_fn=None):
    """Performs a datastore upload via the bulkloader.

    Args:
      run_fn: Function to invoke the bulkloader, used for testing.
    """
    if run_fn is None:
      run_fn = self.RunBulkloader
    self._SetupLoad()

    StatusUpdate('Uploading data records.', self.error_fh)

    args = self._MakeLoaderArgs()
    args['download'] = False
    args['map'] = False
    args['dump'] = False
    args['restore'] = not args['config_file']
    args['create_config'] = False

    run_fn(args)

  def CreateBulkloadConfig(self, run_fn=None):
    """Create a bulkloader config via the bulkloader wizard.

    Args:
      run_fn: Function to invoke the bulkloader, used for testing.
    """
    if run_fn is None:
      run_fn = self.RunBulkloader
    self._SetupLoad()

    StatusUpdate('Creating bulkloader configuration.', self.error_fh)

    args = self._MakeLoaderArgs()
    args['download'] = False
    args['has_header'] = False
    args['map'] = False
    args['dump'] = False
    args['restore'] = False
    args['create_config'] = True

    run_fn(args)

  def _PerformLoadOptions(self, parser):
    """Adds options common to 'upload_data' and 'download_data'.

    Args:
      parser: An instance of OptionsParser.
    """
    parser.add_option('--url', type='string', dest='url',
                      action='store',
                      help='The location of the remote_api endpoint.')
    parser.add_option('--batch_size', type='int', dest='batch_size',
                      action='store', default=10,
                      help='Number of records to post in each request.')
    parser.add_option('--bandwidth_limit', type='int', dest='bandwidth_limit',
                      action='store', default=250000,
                      help='The maximum bytes/second bandwidth for transfers.')
    parser.add_option('--rps_limit', type='int', dest='rps_limit',
                      action='store', default=20,
                      help='The maximum records/second for transfers.')
    parser.add_option('--http_limit', type='int', dest='http_limit',
                      action='store', default=8,
                      help='The maximum requests/second for transfers.')
    parser.add_option('--db_filename', type='string', dest='db_filename',
                      action='store',
                      help='Name of the progress database file.')
    parser.add_option('--auth_domain', type='string', dest='auth_domain',
                      action='store', default='gmail.com',
                      help='The name of the authorization domain to use.')
    parser.add_option('--log_file', type='string', dest='log_file',
                      help='File to write bulkloader logs.  If not supplied '
                      'then a new log file will be created, named: '
                      'bulkloader-log-TIMESTAMP.')
    parser.add_option('--dry_run', action='store_true',
                      dest='dry_run', default=False,
                      help='Do not execute any remote_api calls')
    parser.add_option('--namespace', type='string', dest='namespace',
                      action='store', default='',
                      help='Namespace to use when accessing datastore.')
    parser.add_option('--num_threads', type='int', dest='num_threads',
                      action='store', default=10,
                      help='Number of threads to transfer records with.')

  def _PerformUploadOptions(self, parser):
    """Adds 'upload_data' specific options to the 'parser' passed in.

    Args:
      parser: An instance of OptionsParser.
    """
    self._PerformLoadOptions(parser)
    parser.add_option('--filename', type='string', dest='filename',
                      action='store',
                      help='The name of the file containing the input data.'
                      ' (Required)')
    parser.add_option('--kind', type='string', dest='kind',
                      action='store',
                      help='The kind of the entities to store.')
    parser.add_option('--has_header', dest='has_header',
                      action='store_true', default=False,
                      help='Whether the first line of the input file should be'
                      ' skipped')
    parser.add_option('--loader_opts', type='string', dest='loader_opts',
                      help='A string to pass to the Loader.initialize method.')
    parser.add_option('--config_file', type='string', dest='config_file',
                      action='store',
                      help='Name of the configuration file.')

  def _PerformDownloadOptions(self, parser):
    """Adds 'download_data' specific options to the 'parser' passed in.

    Args:
      parser: An instance of OptionsParser.
    """
    self._PerformLoadOptions(parser)
    parser.add_option('--filename', type='string', dest='filename',
                      action='store',
                      help='The name of the file where output data is to be'
                      ' written. (Required)')
    parser.add_option('--kind', type='string', dest='kind',
                      action='store',
                      help='The kind of the entities to retrieve.')
    parser.add_option('--exporter_opts', type='string', dest='exporter_opts',
                      help='A string to pass to the Exporter.initialize method.'
                     )
    parser.add_option('--result_db_filename', type='string',
                      dest='result_db_filename',
                      action='store',
                      help='Database to write entities to for download.')
    parser.add_option('--config_file', type='string', dest='config_file',
                      action='store',
                      help='Name of the configuration file.')

  def _CreateBulkloadConfigOptions(self, parser):
    """Adds 'download_data' specific options to the 'parser' passed in.

    Args:
      parser: An instance of OptionsParser.
    """
    self._PerformLoadOptions(parser)
    parser.add_option('--filename', type='string', dest='filename',
                      action='store',
                      help='The name of the file where the generated template'
                      ' is to be written. (Required)')
    parser.add_option('--result_db_filename', type='string',
                      dest='result_db_filename',
                      action='store',
                      help='Database to write entities to during config '
                      'generation.')

  def ResourceLimitsInfo(self, output=None):
    """Outputs the current resource limits.

    Args:
      output: The file handle to write the output to (used for testing).
    """
    rpcserver = self._GetRpcServer()
    appyaml = self._ParseAppInfoFromYaml(self.basepath)
    request_params = {'app_id': appyaml.application, 'version': appyaml.version}
    logging_context = _ClientDeployLoggingContext(rpcserver, request_params,
                                                  usage_reporting=False)
    resource_limits = GetResourceLimits(logging_context, self.error_fh)


    for attr_name in sorted(resource_limits):
      print >>output, '%s: %s' % (attr_name, resource_limits[attr_name])

  class Action(object):
    """Contains information about a command line action.

    Attributes:
      function: The name of a function defined on AppCfg or its subclasses
        that will perform the appropriate action.
      usage: A command line usage string.
      short_desc: A one-line description of the action.
      long_desc: A detailed description of the action.  Whitespace and
        formatting will be preserved.
      error_desc: An error message to display when the incorrect arguments are
        given.
      options: A function that will add extra options to a given OptionParser
        object.
      uses_basepath: Does the action use a basepath/app-directory (and hence
        app.yaml).
      hidden: Should this command be shown in the help listing.
    """






    def __init__(self, function, usage, short_desc, long_desc='',
                 error_desc=None, options=lambda obj, parser: None,
                 uses_basepath=True, hidden=False):
      """Initializer for the class attributes."""
      self.function = function
      self.usage = usage
      self.short_desc = short_desc
      self.long_desc = long_desc
      self.error_desc = error_desc
      self.options = options
      self.uses_basepath = uses_basepath
      self.hidden = hidden

    def __call__(self, appcfg):
      """Invoke this Action on the specified AppCfg.

      This calls the function of the appropriate name on AppCfg, and
      respects polymophic overrides.

      Args:
        appcfg: The appcfg to use.
      Returns:
        The result of the function call.
      """
      method = getattr(appcfg, self.function)
      return method()

  actions = {

      'help': Action(
          function='Help',
          usage='%prog help <action>',
          short_desc='Print help for a specific action.',
          uses_basepath=False),

      'update': Action(
          function='Update',
          usage='%prog [options] update <directory> | [file, ...]',
          options=_UpdateOptions,
          short_desc='Create or update an app version.',
          long_desc="""
Specify a directory that contains all of the files required by
the app, and appcfg.py will create/update the app version referenced
in the app.yaml file at the top level of that directory.  appcfg.py
will follow symlinks and recursively upload all files to the server.
Temporary or source control files (e.g. foo~, .svn/*) will be skipped.

If you are using the Modules feature, then you may prefer to pass multiple files
to update, rather than a directory, to specify which modules you would like
updated."""),

      'download_app': Action(
          function='DownloadApp',
          usage='%prog [options] download_app -A app_id [ -V version ]'
          ' <out-dir>',
          short_desc='Download a previously-uploaded app.',
          long_desc="""
Download a previously-uploaded app to the specified directory.  The app
ID is specified by the \"-A\" option.  The optional version is specified
by the \"-V\" option.""",
          uses_basepath=False),

      'update_cron': Action(
          function='UpdateCron',
          usage='%prog [options] update_cron <directory>',
          short_desc='Update application cron definitions.',
          long_desc="""
The 'update_cron' command will update any new, removed or changed cron
definitions from the optional cron.yaml file."""),

      'update_indexes': Action(
          function='UpdateIndexes',
          usage='%prog [options] update_indexes <directory>',
          short_desc='Update application indexes.',
          long_desc="""
The 'update_indexes' command will add additional indexes which are not currently
in production as well as restart any indexes that were not completed."""),

      'update_queues': Action(
          function='UpdateQueues',
          usage='%prog [options] update_queues <directory>',
          short_desc='Update application task queue definitions.',
          long_desc="""
The 'update_queue' command will update any new, removed or changed task queue
definitions from the optional queue.yaml file."""),

      'update_dispatch': Action(
          function='UpdateDispatch',
          usage='%prog [options] update_dispatch <directory>',
          short_desc='Update application dispatch definitions.',
          long_desc="""
The 'update_dispatch' command will update any new, removed or changed dispatch
definitions from the optional dispatch.yaml file."""),

      'update_dos': Action(
          function='UpdateDos',
          usage='%prog [options] update_dos <directory>',
          short_desc='Update application dos definitions.',
          long_desc="""
The 'update_dos' command will update any new, removed or changed dos
definitions from the optional dos.yaml file."""),

      'backends': Action(
          function='BackendsAction',
          usage='%prog [options] backends <directory> <action>',
          short_desc='Perform a backend action.',
          long_desc="""
The 'backends' command will perform a backends action.""",
          error_desc="""\
Expected a <directory> and <action> argument."""),

      'backends list': Action(
          function='BackendsList',
          usage='%prog [options] backends <directory> list',
          short_desc='List all backends configured for the app.',
          long_desc="""
The 'backends list' command will list all backends configured for the app."""),

      'backends update': Action(
          function='BackendsUpdate',
          usage='%prog [options] backends <directory> update [<backend>]',
          options=_UpdateOptions,
          short_desc='Update one or more backends.',
          long_desc="""
The 'backends update' command updates one or more backends.  This command
updates backend configuration settings and deploys new code to the server.  Any
existing instances will stop and be restarted.  Updates all backends, or a
single backend if the <backend> argument is provided."""),

      'backends rollback': Action(
          function='BackendsRollback',
          usage='%prog [options] backends <directory> rollback <backend>',
          short_desc='Roll back an update of a backend.',
          long_desc="""
The 'backends update' command requires a server-side transaction.
Use 'backends rollback' if you experience an error during 'backends update'
and want to start the update over again."""),

      'backends start': Action(
          function='BackendsStart',
          usage='%prog [options] backends <directory> start <backend>',
          short_desc='Start a backend.',
          long_desc="""
The 'backends start' command will put a backend into the START state."""),

      'backends stop': Action(
          function='BackendsStop',
          usage='%prog [options] backends <directory> stop <backend>',
          short_desc='Stop a backend.',
          long_desc="""
The 'backends start' command will put a backend into the STOP state."""),

      'backends delete': Action(
          function='BackendsDelete',
          usage='%prog [options] backends <directory> delete <backend>',
          short_desc='Delete a backend.',
          long_desc="""
The 'backends delete' command will delete a backend."""),

      'backends configure': Action(
          function='BackendsConfigure',
          usage='%prog [options] backends <directory> configure <backend>',
          short_desc='Reconfigure a backend without stopping it.',
          long_desc="""
The 'backends configure' command performs an online update of a backend, without
stopping instances that are currently running.  No code or handlers are updated,
only certain configuration settings specified in backends.yaml.  Valid settings
are: instances, options: public, and options: failfast."""),

      'vacuum_indexes': Action(
          function='VacuumIndexes',
          usage='%prog [options] vacuum_indexes <directory>',
          options=_VacuumIndexesOptions,
          short_desc='Delete unused indexes from application.',
          long_desc="""
The 'vacuum_indexes' command will help clean up indexes which are no longer
in use.  It does this by comparing the local index configuration with
indexes that are actually defined on the server.  If any indexes on the
server do not exist in the index configuration file, the user is given the
option to delete them."""),

      'rollback': Action(
          function='Rollback',
          usage='%prog [options] rollback <directory> | <file>',
          options=_RollbackOptions,
          short_desc='Rollback an in-progress update.',
          long_desc="""
The 'update' command requires a server-side transaction.
Use 'rollback' if you experience an error during 'update'
and want to begin a new update transaction."""),

      'request_logs': Action(
          function='RequestLogs',
          usage='%prog [options] request_logs [<directory>] <output_file>',
          options=_RequestLogsOptions,
          uses_basepath=False,
          short_desc='Write request logs in Apache common log format.',
          long_desc="""
The 'request_logs' command exports the request logs from your application
to a file.  It will write Apache common log format records ordered
chronologically.  If output file is '-' stdout will be written.""",
          error_desc="""\
Expected an optional <directory> and mandatory <output_file> argument."""),

      'cron_info': Action(
          function='CronInfo',
          usage='%prog [options] cron_info <directory>',
          options=_CronInfoOptions,
          short_desc='Display information about cron jobs.',
          long_desc="""
The 'cron_info' command will display the next 'number' runs (default 5) for
each cron job defined in the cron.yaml file."""),

      'start_module_version': Action(
          function='StartModuleVersion',
          uses_basepath=False,
          usage='%prog [options] start_module_version [file, ...]',
          short_desc='Start a module version.',
          long_desc="""
The 'start_module_version' command will put a module version into the START
state."""),

      'stop_module_version': Action(
          function='StopModuleVersion',
          uses_basepath=False,
          usage='%prog [options] stop_module_version [file, ...]',
          short_desc='Stop a module version.',
          long_desc="""
The 'stop_module_version' command will put a module version into the STOP
state."""),





      'upload_data': Action(
          function='PerformUpload',
          usage='%prog [options] upload_data <directory>',
          options=_PerformUploadOptions,
          short_desc='Upload data records to datastore.',
          long_desc="""
The 'upload_data' command translates input records into datastore entities and
uploads them into your application's datastore.""",
          uses_basepath=False),

      'download_data': Action(
          function='PerformDownload',
          usage='%prog [options] download_data <directory>',
          options=_PerformDownloadOptions,
          short_desc='Download entities from datastore.',
          long_desc="""
The 'download_data' command downloads datastore entities and writes them to
file as CSV or developer defined format.""",
          uses_basepath=False),

      'create_bulkloader_config': Action(
          function='CreateBulkloadConfig',
          usage='%prog [options] create_bulkload_config <directory>',
          options=_CreateBulkloadConfigOptions,
          short_desc='Create a bulkloader.yaml from a running application.',
          long_desc="""
The 'create_bulkloader_config' command creates a bulkloader.yaml configuration
template for use with upload_data or download_data.""",
          uses_basepath=False),


      'set_default_version': Action(
          function='SetDefaultVersion',
          usage='%prog [options] set_default_version [directory]',
          short_desc='Set the default (serving) version.',
          long_desc="""
The 'set_default_version' command sets the default (serving) version of the app.
Defaults to using the application, version and module specified in app.yaml;
use the --application, --version and --module flags to override these values.
The --module flag can also be a comma-delimited string of several modules. (ex.
module1,module2,module3) In this case, the default version of each module will
be changed to the version specified.

The 'migrate_traffic' command can be thought of as a safer version of this
command.""",
          uses_basepath=False),

      'migrate_traffic': Action(
          function='MigrateTraffic',
          usage='%prog [options] migrate_traffic [directory]',
          short_desc='Migrates traffic to another version.',
          long_desc="""
The 'migrate_traffic' command gradually gradually sends an increasing fraction
of traffic your app's traffic from the current default version to another
version. Once all traffic has been migrated, the new version is set as the
default version.

app.yaml specifies the target application, version, and (optionally) module; use
the --application, --version and --module flags to override these values.

Can be thought of as an enhanced version of the 'set_default_version'
command.""",

          uses_basepath=False,

          hidden=True),

      'resource_limits_info': Action(
          function='ResourceLimitsInfo',
          usage='%prog [options] resource_limits_info <directory>',
          short_desc='Get the resource limits.',
          long_desc="""
The 'resource_limits_info' command prints the current resource limits that
are enforced."""),

      'list_versions': Action(
          function='ListVersions',
          usage='%prog [options] list_versions [directory]',
          short_desc='List all uploaded versions for an app.',
          long_desc="""
The 'list_versions' command outputs the uploaded versions for each module of
an application in YAML. The YAML is in formatted as an associative array,
mapping module_ids to the list of versions uploaded for that module. The
default version will be first in the list.""",
          uses_basepath=False),

      'delete_version': Action(
          function='DeleteVersion',
          usage='%prog [options] delete_version -A app_id -V version '
          '[-M module]',
          uses_basepath=False,
          short_desc='Delete the specified version for an app.',
          long_desc="""
The 'delete_version' command deletes the specified version for the specified
application."""),

      'debug': Action(
          function='DebugAction',
          usage='%prog [options] debug [-A app_id] [-V version]'
          ' [-M module] [-I instance] [directory]',
          options=_LockActionOptions,
          short_desc='Debug a vm runtime application.',
          hidden=True,
          uses_basepath=False,
          long_desc="""
The 'debug' command configures a vm runtime application to be accessable
for debugging."""),

      'lock': Action(
          function='LockAction',
          usage='%prog [options] lock [-A app_id] [-V version]'
          ' [-M module] [-I instance] [directory]',
          options=_LockActionOptions,
          short_desc='Lock a debugged vm runtime application.',
          hidden=True,
          uses_basepath=False,
          long_desc="""
The 'lock' command relocks a debugged vm runtime application."""),

      'prepare_vm_runtime': Action(
          function='PrepareVmRuntimeAction',
          usage='%prog [options] prepare_vm_runtime -A app_id',
          short_desc='Prepare an application for the VM runtime.',
          hidden=True,
          uses_basepath=False,
          long_desc="""
The 'prepare_vm_runtime' prepares an application for the VM runtime."""),
  }


def main(argv):
  logging.basicConfig(format=('%(asctime)s %(levelname)s %(filename)s:'
                              '%(lineno)s %(message)s '))
  try:
    result = AppCfgApp(argv).Run()
    if result:
      sys.exit(result)
  except KeyboardInterrupt:
    StatusUpdate('Interrupted.')
    sys.exit(1)


if __name__ == '__main__':
  main(sys.argv)
