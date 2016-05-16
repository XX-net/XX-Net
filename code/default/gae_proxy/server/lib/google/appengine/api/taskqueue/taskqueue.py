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




"""Task Queue API.

Enables an application to queue background work for itself. Work is done
through webhooks that process tasks pushed from a queue, or workers that
manually pull tasks from a queue. In push queues, Tasks will execute in
best-effort order of ETA. Webhooks that fail will cause tasks to be retried
at a later time. In pull queues, workers are responsible of leasing tasks for
processing and deleting the tasks when completed. Multiple queues may exist
with independent throttling controls.

Webhook URLs may be specified directly for push Tasks, or the default URL scheme
may be used, which will translate Task names into URLs relative to a Queue's
base path. A default queue is also provided for simple usage.
"""













__all__ = [

    'BadTaskStateError', 'BadTransactionState', 'BadTransactionStateError',
    'DatastoreError', 'DuplicateTaskNameError', 'Error', 'InternalError',
    'InvalidQueueError', 'InvalidQueueNameError', 'InvalidTaskError',
    'InvalidTaskNameError', 'InvalidUrlError', 'PermissionDeniedError',
    'TaskAlreadyExistsError', 'TaskTooLargeError', 'TombstonedTaskError',
    'TooManyTasksError', 'TransientError', 'UnknownQueueError',
    'InvalidLeaseTimeError', 'InvalidMaxTasksError', 'InvalidDeadlineError',
    'InvalidQueueModeError', 'TransactionalRequestTooLargeError',
    'TaskLeaseExpiredError', 'QueuePausedError', 'InvalidEtaError',
    'InvalidTagError',

    'MAX_QUEUE_NAME_LENGTH', 'MAX_TASK_NAME_LENGTH', 'MAX_TASK_SIZE_BYTES',
    'MAX_PULL_TASK_SIZE_BYTES', 'MAX_PUSH_TASK_SIZE_BYTES',
    'MAX_LEASE_SECONDS', 'MAX_TASKS_PER_ADD',
    'MAX_TASKS_PER_LEASE',
    'MAX_URL_LENGTH',

    'DEFAULT_APP_VERSION',

    'Queue', 'QueueStatistics', 'Task', 'TaskRetryOptions', 'add', 'create_rpc']


import calendar
import cgi
import datetime
import logging
import math
import os
import re
import time
import urllib
import urlparse

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import app_identity
from google.appengine.api import namespace_manager
from google.appengine.api import urlfetch
from google.appengine.api.taskqueue import taskqueue_service_pb
from google.appengine.runtime import apiproxy_errors


class Error(Exception):
  """Base-class for exceptions in this module."""


class UnknownQueueError(Error):
  """The queue specified is unknown."""


class TransientError(Error):
  """There was a transient error while accessing the queue.

  Please Try again later.
  """


class InternalError(Error):
  """There was an internal error while accessing this queue.

  If this problem continues, please contact the App Engine team through
  our support forum with a description of your problem.
  """


class InvalidTaskError(Error):
  """The task's parameters, headers, or method is invalid."""


class InvalidTaskNameError(InvalidTaskError):
  """The task's name is invalid."""


class TaskTooLargeError(InvalidTaskError):
  """The task is too large with its headers and payload."""


class TaskAlreadyExistsError(InvalidTaskError):
  """Task already exists. It has not yet run."""


class TombstonedTaskError(InvalidTaskError):
  """Task has been tombstoned."""


class InvalidUrlError(InvalidTaskError):
  """The task's relative URL is invalid."""


class InvalidEtaError(InvalidTaskError):
  """The task's ETA is invalid."""


class BadTaskStateError(Error):
  """The task is in the wrong state for the requested operation."""


class InvalidQueueError(Error):
  """The Queue's configuration is invalid."""


class InvalidQueueNameError(InvalidQueueError):
  """The Queue's name is invalid."""


class _RelativeUrlError(Error):
  """The relative URL supplied is invalid."""


class PermissionDeniedError(Error):
  """The requested operation is not allowed for this app."""


class DuplicateTaskNameError(Error):
  """The add arguments contain tasks with identical names."""


class TooManyTasksError(Error):
  """Too many tasks were present in a single function call."""


class DatastoreError(Error):
  """There was a datastore error while accessing the queue."""


class BadTransactionStateError(Error):
  """The state of the current transaction does not permit this operation."""


class InvalidTaskRetryOptionsError(Error):
  """The task retry configuration is invalid."""


class InvalidLeaseTimeError(Error):
  """The lease time period is invalid."""


class InvalidMaxTasksError(Error):
  """The requested max tasks in lease_tasks is invalid."""


class InvalidDeadlineError(Error):
  """The requested deadline in lease_tasks is invalid."""


class InvalidQueueModeError(Error):
  """Invoking PULL queue operation on a PUSH queue or vice versa."""


class TransactionalRequestTooLargeError(TaskTooLargeError):
  """The total size of this transaction (including tasks) was too large."""


class TaskLeaseExpiredError(Error):
  """The task lease could not be renewed because it had already expired."""


class QueuePausedError(Error):
  """The queue is paused and cannot process modify task lease requests."""


class InvalidTagError(Error):
  """The specified tag is invalid."""


class _DefaultAppVersionSingleton(object):
  def __repr__(self):
    return '<DefaultApplicationVersion>'


class _UnknownAppVersionSingleton(object):
  def __repr__(self):
    return '<UnknownApplicationVersion>'




BadTransactionState = BadTransactionStateError

MAX_QUEUE_NAME_LENGTH = 100

MAX_PULL_TASK_SIZE_BYTES = 2 ** 20

MAX_PUSH_TASK_SIZE_BYTES = 100 * (2 ** 10)

MAX_TASK_NAME_LENGTH = 500

MAX_TASK_SIZE_BYTES = MAX_PUSH_TASK_SIZE_BYTES

MAX_TASKS_PER_ADD = 100

MAX_TRANSACTIONAL_REQUEST_SIZE_BYTES = 2 ** 20


MAX_URL_LENGTH = 2083

MAX_TASKS_PER_LEASE = 1000

MAX_TAG_LENGTH = 500

MAX_LEASE_SECONDS = 3600 * 24 * 7


DEFAULT_APP_VERSION = _DefaultAppVersionSingleton()
_UNKNOWN_APP_VERSION = _UnknownAppVersionSingleton()

_DEFAULT_QUEUE = 'default'

_DEFAULT_QUEUE_PATH = '/_ah/queue'

_MAX_COUNTDOWN_SECONDS = 3600 * 24 * 30

_METHOD_MAP = {
    'GET': taskqueue_service_pb.TaskQueueAddRequest.GET,
    'POST': taskqueue_service_pb.TaskQueueAddRequest.POST,
    'HEAD': taskqueue_service_pb.TaskQueueAddRequest.HEAD,
    'PUT': taskqueue_service_pb.TaskQueueAddRequest.PUT,
    'DELETE': taskqueue_service_pb.TaskQueueAddRequest.DELETE,
}

_NON_POST_HTTP_METHODS = frozenset(['GET', 'HEAD', 'PUT', 'DELETE'])

_BODY_METHODS = frozenset(['POST', 'PUT', 'PULL'])

_TASK_NAME_PATTERN = r'^[a-zA-Z0-9_-]{1,%s}$' % MAX_TASK_NAME_LENGTH

_TASK_NAME_RE = re.compile(_TASK_NAME_PATTERN)

_QUEUE_NAME_PATTERN = r'^[a-zA-Z0-9-]{1,%s}$' % MAX_QUEUE_NAME_LENGTH

_QUEUE_NAME_RE = re.compile(_QUEUE_NAME_PATTERN)

_ERROR_MAPPING = {
    taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_QUEUE: UnknownQueueError,
    taskqueue_service_pb.TaskQueueServiceError.TRANSIENT_ERROR:
        TransientError,
    taskqueue_service_pb.TaskQueueServiceError.INTERNAL_ERROR: InternalError,
    taskqueue_service_pb.TaskQueueServiceError.TASK_TOO_LARGE:
        TaskTooLargeError,
    taskqueue_service_pb.TaskQueueServiceError.INVALID_TASK_NAME:
    InvalidTaskNameError,
        taskqueue_service_pb.TaskQueueServiceError.INVALID_QUEUE_NAME:
    InvalidQueueNameError,
    taskqueue_service_pb.TaskQueueServiceError.INVALID_URL: InvalidUrlError,
    taskqueue_service_pb.TaskQueueServiceError.INVALID_QUEUE_RATE:
        InvalidQueueError,
    taskqueue_service_pb.TaskQueueServiceError.PERMISSION_DENIED:
        PermissionDeniedError,
    taskqueue_service_pb.TaskQueueServiceError.TASK_ALREADY_EXISTS:
        TaskAlreadyExistsError,
    taskqueue_service_pb.TaskQueueServiceError.TOMBSTONED_TASK:
        TombstonedTaskError,
    taskqueue_service_pb.TaskQueueServiceError.INVALID_ETA: InvalidEtaError,
    taskqueue_service_pb.TaskQueueServiceError.INVALID_REQUEST: Error,
    taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_TASK: Error,
    taskqueue_service_pb.TaskQueueServiceError.TOMBSTONED_QUEUE: Error,
    taskqueue_service_pb.TaskQueueServiceError.DUPLICATE_TASK_NAME:
        DuplicateTaskNameError,
    taskqueue_service_pb.TaskQueueServiceError.INVALID_QUEUE_MODE:
        InvalidQueueModeError,

    taskqueue_service_pb.TaskQueueServiceError.TOO_MANY_TASKS:
        TooManyTasksError,
    taskqueue_service_pb.TaskQueueServiceError.TRANSACTIONAL_REQUEST_TOO_LARGE:
        TransactionalRequestTooLargeError,
    taskqueue_service_pb.TaskQueueServiceError.TASK_LEASE_EXPIRED:
        TaskLeaseExpiredError,
    taskqueue_service_pb.TaskQueueServiceError.QUEUE_PAUSED:
        QueuePausedError,
    taskqueue_service_pb.TaskQueueServiceError.INVALID_TAG:
        InvalidTagError,

}







_PRESERVE_ENVIRONMENT_HEADERS = (
    ('X-AppEngine-Default-Namespace', 'HTTP_X_APPENGINE_DEFAULT_NAMESPACE'),)



class _UTCTimeZone(datetime.tzinfo):
  """UTC timezone."""

  ZERO = datetime.timedelta(0)

  def utcoffset(self, dt):
    return self.ZERO

  def dst(self, dt):
    return self.ZERO

  def tzname(self, dt):
    return 'UTC'

  def __repr__(self):
    return '_UTCTimeZone()'


_UTC = _UTCTimeZone()


def _parse_relative_url(relative_url):
  """Parses a relative URL and splits it into its path and query string.

  Args:
    relative_url: The relative URL, starting with a '/'.

  Returns:
    Tuple (path, query) where:
      path: The path in the relative URL.
      query: The query string in the URL without the '?' character.

  Raises:
    _RelativeUrlError if the relative_url is invalid for whatever reason.
  """
  if not relative_url:
    raise _RelativeUrlError('Relative URL is empty')
  (scheme, netloc, path, query, fragment) = urlparse.urlsplit(relative_url)
  if scheme or netloc:
    raise _RelativeUrlError('Relative URL may not have a scheme or location')
  if fragment:
    raise _RelativeUrlError('Relative URL may not specify a fragment')
  if not path or path[0] != '/':
    raise _RelativeUrlError('Relative URL path must start with "/"')
  return path, query


def _flatten_params(params):
  """Converts a dictionary of parameters to a list of parameters.

  Any unicode strings in keys or values will be encoded as UTF-8.

  Args:
    params: Dictionary mapping parameter keys to values. Values will be
      converted to a string and added to the list as tuple (key, value). If
      a values is iterable and not a string, each contained value will be
      added as a separate (key, value) tuple.

  Returns:
    List of (key, value) tuples.
  """

  def get_string(value):
    if isinstance(value, unicode):
      return unicode(value).encode('utf-8')
    else:




      return str(value)

  param_list = []
  for key, value in params.iteritems():
    key = get_string(key)
    if isinstance(value, basestring):
      param_list.append((key, get_string(value)))
    else:
      try:
        iterator = iter(value)
      except TypeError:
        param_list.append((key, str(value)))
      else:
        param_list.extend((key, get_string(v)) for v in iterator)

  return param_list


def _MakeAsyncCall(method, request, response, get_result_hook=None, rpc=None):
  """Internal helper to schedule an asynchronous RPC.

  Args:
    method: The name of the taskqueue_service method that should be called,
      e.g. 'BulkAdd'.
    request: The protocol buffer containing the request argument.
    response: The protocol buffer to be populated with the response.
    get_result_hook: An optional hook function used to process results
      (See UserRPC.make_call() for more info).
    rpc: An optional UserRPC object that will be used to make the call.

  Returns:
    A UserRPC object; either the one passed in as the rpc argument,
    or a new one if no rpc was passed in.
  """
  if rpc is None:
    rpc = create_rpc()
  assert rpc.service == 'taskqueue', repr(rpc.service)
  rpc.make_call(method, request, response, get_result_hook, None)
  return rpc


def _TranslateError(error, detail=''):
  """Translates a TaskQueueServiceError into an exception.

  Args:
    error: Value from TaskQueueServiceError enum.
    detail: A human-readable description of the error.

  Returns:
    The corresponding Exception sub-class for that error code.
  """
  if (error >= taskqueue_service_pb.TaskQueueServiceError.DATASTORE_ERROR
      and isinstance(error, int)):
    from google.appengine.api import datastore
    datastore_exception = datastore._DatastoreExceptionFromErrorCodeAndDetail(
        error - taskqueue_service_pb.TaskQueueServiceError.DATASTORE_ERROR,
        detail)

    class JointException(datastore_exception.__class__, DatastoreError):
      """There was a datastore error while accessing the queue."""
      __msg = (u'taskqueue.DatastoreError caused by: %s %s' %
               (datastore_exception.__class__, detail))

      def __str__(self):
        return JointException.__msg

    return JointException()
  else:
    exception_class = _ERROR_MAPPING.get(error, None)
    if exception_class:
      return exception_class(detail)
    else:
      return Error('Application error %s: %s' % (error, detail))


def _ValidateDeadline(deadline):
  if not isinstance(deadline, (int, long, float)):
    raise TypeError(
        'deadline must be numeric')

  if deadline <= 0:
    raise InvalidDeadlineError(
        'Negative or zero deadline requested')


def create_rpc(deadline=None, callback=None):
  """Creates an RPC object for use with the Task Queue API.

  Args:
    deadline: Optional deadline in seconds for the operation; the default
      is a system-specific deadline (typically 5 seconds).
    callback: Optional callable to invoke on completion.

  Returns:
    An apiproxy_stub_map.UserRPC object specialized for this service.
  """
  if deadline is not None:
    _ValidateDeadline(deadline)
  return apiproxy_stub_map.UserRPC('taskqueue', deadline, callback)


class TaskRetryOptions(object):
  """The options used to decide when a failed Task will be retried."""

  __CONSTRUCTOR_KWARGS = frozenset(
      ['min_backoff_seconds', 'max_backoff_seconds',
       'task_age_limit', 'max_doublings', 'task_retry_limit'])

  def __init__(self, **kwargs):
    """Initializer.

    Args:
      min_backoff_seconds: The minimum number of seconds to wait before retrying
        a task after failure. (optional)
      max_backoff_seconds: The maximum number of seconds to wait before retrying
        a task after failure. (optional)
      task_age_limit: The number of seconds after creation afterwhich a failed
        task will no longer be retried. The given value will be rounded up to
        the nearest integer. If task_retry_limit is also specified then the task
        will be retried until both limits are reached. (optional)
      max_doublings: The maximum number of times that the interval between
        failed task retries will be doubled before the increase becomes
        constant. The constant will be:
        2**(max_doublings - 1) * min_backoff_seconds. (optional)
      task_retry_limit: The maximum number of times to retry a failed task
        before giving up. If task_age_limit is specified then the task will be
        retried until both limits are reached. (optional)

    Raises:
      InvalidTaskRetryOptionsError if any of the parameters are invalid.
    """
    args_diff = set(kwargs.iterkeys()) - self.__CONSTRUCTOR_KWARGS
    if args_diff:
      raise TypeError('Invalid arguments: %s' % ', '.join(args_diff))

    self.__min_backoff_seconds = kwargs.get('min_backoff_seconds')
    if (self.__min_backoff_seconds is not None and
        self.__min_backoff_seconds < 0):
      raise InvalidTaskRetryOptionsError(
          'The minimum retry interval cannot be negative')

    self.__max_backoff_seconds = kwargs.get('max_backoff_seconds')
    if (self.__max_backoff_seconds is not None and
        self.__max_backoff_seconds < 0):
      raise InvalidTaskRetryOptionsError(
          'The maximum retry interval cannot be negative')

    if (self.__min_backoff_seconds is not None and
        self.__max_backoff_seconds is not None and
        self.__max_backoff_seconds < self.__min_backoff_seconds):
      raise InvalidTaskRetryOptionsError(
          'The maximum retry interval cannot be less than the '
          'minimum retry interval')

    self.__max_doublings = kwargs.get('max_doublings')
    if self.__max_doublings is not None and self.__max_doublings < 0:
      raise InvalidTaskRetryOptionsError(
          'The maximum number of retry interval doublings cannot be negative')

    self.__task_retry_limit = kwargs.get('task_retry_limit')
    if self.__task_retry_limit is not None and self.__task_retry_limit < 0:
      raise InvalidTaskRetryOptionsError(
          'The maximum number of retries cannot be negative')

    self.__task_age_limit = kwargs.get('task_age_limit')
    if self.__task_age_limit is not None:
      if self.__task_age_limit < 0:
        raise InvalidTaskRetryOptionsError(
            'The expiry countdown cannot be negative')
      self.__task_age_limit = int(math.ceil(self.__task_age_limit))

  @property
  def min_backoff_seconds(self):
    """The minimum number of seconds to wait before retrying a task."""
    return self.__min_backoff_seconds

  @property
  def max_backoff_seconds(self):
    """The maximum number of seconds to wait before retrying a task."""
    return self.__max_backoff_seconds

  @property
  def task_age_limit(self):
    """The number of seconds afterwhich a failed task will not be retried."""
    return self.__task_age_limit

  @property
  def max_doublings(self):
    """The number of times that the retry interval will be doubled."""
    return self.__max_doublings

  @property
  def task_retry_limit(self):
    """The number of times that a failed task will be retried."""
    return self.__task_retry_limit

  def __repr__(self):
    properties = ['%s=%r' % (attr, getattr(self, attr)) for attr in
                  self.__CONSTRUCTOR_KWARGS]
    return 'TaskRetryOptions(%s)' % ', '.join(properties)


class Task(object):
  """Represents a single Task on a queue."""


  __CONSTRUCTOR_KWARGS = frozenset([
      'countdown', 'eta', 'headers', 'method', 'name', 'params',
      'retry_options', 'tag', 'target', 'url', '_size_check'])


  __eta_posix = None
  __target = None


  def __init__(self, payload=None, **kwargs):
    """Initializer.

    All parameters are optional.

    Args:
      payload: The payload data for this Task that will either be delivered
        to the webhook as the HTTP request body or fetched by workers for pull
        queues. This is only allowed for POST, PUT and PULL methods.
      name: Name to give the Task; if not specified, a name will be
        auto-generated when added to a queue and assigned to this object. Must
        match the _TASK_NAME_PATTERN regular expression.
      method: Method to use when accessing the webhook. Defaults to 'POST'. If
        set to 'PULL', task will not be automatically delivered to the webhook,
        instead it stays in the queue until leased.
      url: Relative URL where the webhook that should handle this task is
        located for this application. May have a query string unless this is
        a POST method. Must not be specified if method is PULL.
      headers: Dictionary of headers to pass to the webhook. Values in the
        dictionary may be iterable to indicate repeated header fields. Must not
        be specified if method is PULL.
      params: Dictionary of parameters to use for Task. For POST and PULL
        requests these params will be encoded as
        'application/x-www-form-urlencoded' and set to the payload. For all
        other methods, the parameters will be converted to a query string. Must
        not be specified if the URL already contains a query string, or the
        task already has payload.
      countdown: Time in seconds into the future that this Task should execute.
        Defaults to zero.
      eta: A datetime.datetime specifying the absolute time at which the task
        should be executed. Must not be specified if 'countdown' is specified.
        This may be timezone-aware or timezone-naive. If None, defaults to now.
        For pull tasks, no worker will be able to lease this task before the
        time indicated by eta.
      retry_options: TaskRetryOptions used to control when the task will be
        retried if it fails.
      target: The alternate version/backend on which to execute this task, or
        DEFAULT_APP_VERSION to execute on the application's default version.
      tag: The tag to be used when grouping by tag (PULL tasks only).

    Raises:
      InvalidEtaError: if the ETA is too far into the future;
      InvalidTagError: if the tag is too long;
      InvalidTaskError: if any of the parameters are invalid;
      InvalidTaskNameError: if the task name is invalid;
      InvalidUrlError: if the task URL is invalid or too long;
      TaskTooLargeError: if the task with its payload is too large.
    """
    args_diff = set(kwargs.iterkeys()) - self.__CONSTRUCTOR_KWARGS
    if args_diff:
      raise TypeError('Invalid arguments: %s' % ', '.join(args_diff))

    self.__name = kwargs.get('name')
    if self.__name and not _TASK_NAME_RE.match(self.__name):
      raise InvalidTaskNameError(
          'Task name does not match expression "%s"; found %s' %
          (_TASK_NAME_PATTERN, self.__name))

    self.__default_url, self.__relative_url, query = Task.__determine_url(
        kwargs.get('url', ''))
    self.__headers = urlfetch._CaselessDict()
    self.__headers.update(kwargs.get('headers', {}))
    self.__method = kwargs.get('method', 'POST').upper()
    self.__tag = kwargs.get('tag')
    self.__payload = None
    self.__retry_count = 0
    self.__queue_name = None


    size_check = kwargs.get('_size_check', True)
    params = kwargs.get('params', {})


    for header_name, environ_name in _PRESERVE_ENVIRONMENT_HEADERS:
      value = os.environ.get(environ_name)
      if value is not None:
        self.__headers.setdefault(header_name, value)

    self.__headers.setdefault('X-AppEngine-Current-Namespace',
                              namespace_manager.get_namespace())
    if query and params:
      raise InvalidTaskError('Query string and parameters both present; '
                             'only one of these may be supplied')

    if self.__method != 'PULL' and self.__tag is not None:
      raise InvalidTaskError('tag may only be specified for PULL tasks')

    if self.__method == 'PULL':
      if not self.__default_url:
        raise InvalidTaskError('url must not be specified for PULL tasks')
      if kwargs.get('headers'):
        raise InvalidTaskError('headers must not be specified for PULL tasks')
      if kwargs.get('target'):
        raise InvalidTaskError('target must not be specified for PULL tasks')
      if params:
        if payload:
          raise InvalidTaskError(
              'Message body and parameters both present for '
              'PULL method; only one of these may be supplied')
        payload = Task.__encode_params(params)
      if payload is None:
        raise InvalidTaskError('payload must be specified for PULL task')
      self.__payload = Task.__convert_payload(payload, self.__headers)
    elif self.__method == 'POST':
      if payload and params:
        raise InvalidTaskError('Message body and parameters both present for '
                               'POST method; only one of these may be '
                               'supplied')
      elif query:
        raise InvalidTaskError('POST method may not have a query string; '
                               'use the "params" keyword argument instead')
      elif params:
        self.__payload = Task.__encode_params(params)
        self.__headers.setdefault(
            'content-type', 'application/x-www-form-urlencoded')
      elif payload is not None:
        self.__payload = Task.__convert_payload(payload, self.__headers)
    elif self.__method in _NON_POST_HTTP_METHODS:
      if payload and self.__method not in _BODY_METHODS:
        raise InvalidTaskError(
            'Payload may only be specified for methods %s' %
            ', '.join(_BODY_METHODS))
      if payload:
        self.__payload = Task.__convert_payload(payload, self.__headers)
      if params:
        query = Task.__encode_params(params)
      if query:
        self.__relative_url = '%s?%s' % (self.__relative_url, query)
    else:
      raise InvalidTaskError('Invalid method: %s' % self.__method)

    self.__target = kwargs.get('target')
    self.__resolve_hostname_and_target()

    self.__headers_list = _flatten_params(self.__headers)
    self.__eta_posix = Task.__determine_eta_posix(
        kwargs.get('eta'), kwargs.get('countdown'))
    self.__eta = None
    self.__retry_options = kwargs.get('retry_options')
    self.__enqueued = False
    self.__deleted = False

    if self.__eta_posix - time.time() > _MAX_COUNTDOWN_SECONDS:
      raise InvalidEtaError('ETA too far in the future')

    if size_check:
      if self.__method == 'PULL':
        max_task_size_bytes = MAX_PULL_TASK_SIZE_BYTES
      else:
        max_task_size_bytes = MAX_PUSH_TASK_SIZE_BYTES
      if self.size > max_task_size_bytes:
        raise TaskTooLargeError('Task size must be less than %d; found %d' %
                                (max_task_size_bytes, self.size))
      if self.__tag and len(self.__tag) > MAX_TAG_LENGTH:
        raise InvalidTagError(
            'Tag must be <= %d bytes. Got a %d byte tag.' % (
                MAX_TAG_LENGTH, len(self.__tag)))

  def __resolve_hostname_and_target(self):
    """Resolve the values of the target parameter and the `Host' header.

    Requires that the attributes __target and __headers exist before this method
    is called.

    This function should only be called once from the __init__ function of the
    Task class.

    Raises:
      InvalidTaskError: If the task is invalid.
    """





    if 'HTTP_HOST' not in os.environ:
      logging.warning(
          'The HTTP_HOST environment variable was not set, but is required '
          'to determine the correct value for the `Task.target\' property. '
          'Please update your unit tests to specify a correct value for this '
          'environment variable.')

    if self.__target is not None and 'Host' in self.__headers:
      raise InvalidTaskError(
          'A host header may not be set when a target is specified.')
    elif self.__target is not None:
      host = self.__host_from_target(self.__target)
      if host:


        self.__headers['Host'] = host
    elif 'Host' in self.__headers:
      self.__target = self.__target_from_host(self.__headers['Host'])
    else:
      if 'HTTP_HOST' in os.environ:
        self.__headers['Host'] = os.environ['HTTP_HOST']
        self.__target = self.__target_from_host(self.__headers['Host'])
      else:


        self.__target = _UNKNOWN_APP_VERSION

  @staticmethod
  def __target_from_host(host):
    """Calculate the value of the target parameter from a host header.

    Args:
      host: A string representing the hostname for this task.

    Returns:
      A string containing the target of this task, or the constant
      DEFAULT_APP_VERSION if it is the default version.

      If this code is running in a unit-test where the environment variable
      `DEFAULT_VERSION_HOSTNAME' is not set then the constant
      _UNKNOWN_APP_VERSION is returned.
    """
    default_hostname = app_identity.get_default_version_hostname()
    if default_hostname is None:



      return _UNKNOWN_APP_VERSION

    if host.endswith(default_hostname):

      version_name = host[:-(len(default_hostname) + 1)]
      if version_name:
        return version_name





    return DEFAULT_APP_VERSION

  @staticmethod
  def __host_from_target(target):
    """Calculate the value of the host header from a target.

    Args:
      target: A string representing the target hostname or the constant
          DEFAULT_APP_VERSION.

    Returns:
      The string to be used as the host header, or None if it can not be
      determined.
    """
    default_hostname = app_identity.get_default_version_hostname()
    if default_hostname is None:



      return None

    if target is DEFAULT_APP_VERSION:
      return default_hostname
    else:


      return '%s.%s' % (target, default_hostname)

  @staticmethod
  def __determine_url(relative_url):
    """Determines the URL of a task given a relative URL and a name.

    Args:
      relative_url: The relative URL for the Task.

    Returns:
      Tuple (default_url, relative_url, query) where:
        default_url: True if this Task is using the default URL scheme;
          False otherwise.
        relative_url: String containing the relative URL for this Task.
        query: The query string for this task.

    Raises:
      InvalidUrlError if the relative_url is invalid.
    """
    if not relative_url:
      default_url, query = True, ''
    else:
      default_url = False
      try:
        relative_url, query = _parse_relative_url(relative_url)
      except _RelativeUrlError, e:
        raise InvalidUrlError(e)

    if len(relative_url) > MAX_URL_LENGTH:
      raise InvalidUrlError(
          'Task URL must be less than %d characters; found %d' %
          (MAX_URL_LENGTH, len(relative_url)))

    return (default_url, relative_url, query)

  @staticmethod
  def __determine_eta_posix(eta=None, countdown=None, current_time=None):
    """Determines the ETA for a task.

    If 'eta' and 'countdown' are both None, the current time will be used.
    Otherwise, only one of them may be specified.

    Args:
      eta: A datetime.datetime specifying the absolute ETA or None;
        this may be timezone-aware or timezone-naive.
      countdown: Count in seconds into the future from the present time that
        the ETA should be assigned to.
      current_time: Function that returns the current datetime. (Defaults to
        time.time if None is provided.)

    Returns:
      A float giving a POSIX timestamp containing the ETA.

    Raises:
      InvalidTaskError if the parameters are invalid.
    """
    if not current_time:
      current_time = time.time

    if eta is not None and countdown is not None:
      raise InvalidTaskError('May not use a countdown and ETA together')
    elif eta is not None:
      if not isinstance(eta, datetime.datetime):
        raise InvalidTaskError('ETA must be a datetime.datetime instance')
      elif eta.tzinfo is None:

        return time.mktime(eta.timetuple()) + eta.microsecond*1e-6
      else:

        return calendar.timegm(eta.utctimetuple()) + eta.microsecond*1e-6
    elif countdown is not None:
      try:
        countdown = float(countdown)
      except ValueError:
        raise InvalidTaskError('Countdown must be a number')
      except OverflowError:
        raise InvalidTaskError('Countdown out of range')
      else:
        return current_time() + countdown
    else:
      return current_time()

  @staticmethod
  def __encode_params(params):
    """URL-encodes a list of parameters.

    Args:
      params: Dictionary of parameters, possibly with iterable values.

    Returns:
      URL-encoded version of the params, ready to be added to a query string or
      POST body.
    """
    return urllib.urlencode(_flatten_params(params))

  @staticmethod
  def __convert_payload(payload, headers):
    """Converts a Task payload into UTF-8 and sets headers if necessary.

    Args:
      payload: The payload data to convert.
      headers: Dictionary of headers.

    Returns:
      The payload as a non-unicode string.

    Raises:
      InvalidTaskError if the payload is not a string or unicode instance.
    """
    if isinstance(payload, unicode):
      headers.setdefault('content-type', 'text/plain; charset=utf-8')
      payload = payload.encode('utf-8')
    elif not isinstance(payload, str):
      raise InvalidTaskError(
          'Task payloads must be strings; invalid payload: %r' % payload)
    return payload

  @classmethod
  def _FromQueryAndOwnResponseTask(cls, queue_name, response_task):
    kwargs = {
        '_size_check': False,
        'payload': response_task.body(),
        'name': response_task.task_name(),
        'method': 'PULL'}
    if response_task.has_tag():
      kwargs['tag'] = response_task.tag()
    self = cls(**kwargs)




    self.__eta_posix = response_task.eta_usec() * 1e-6
    self.__retry_count = response_task.retry_count()
    self.__queue_name = queue_name
    self.__enqueued = True
    return self

  @property
  def eta_posix(self):
    """Returns a POSIX timestamp giving when this Task will execute."""
    if self.__eta_posix is None and self.__eta is not None:

      self.__eta_posix = Task.__determine_eta_posix(self.__eta)
    return self.__eta_posix

  @property
  def eta(self):
    """Returns a datetime when this Task will execute."""
    if self.__eta is None and self.__eta_posix is not None:
      self.__eta = datetime.datetime.fromtimestamp(self.__eta_posix, _UTC)
    return self.__eta

  @property
  def _eta_usec(self):
    """Returns a int microseconds timestamp when this Task will execute."""








    return int(round(self.eta_posix * 1e6))

  @property
  def headers(self):
    """Returns a copy of the headers for this Task."""
    return self.__headers.copy()

  @property
  def method(self):
    """Returns the method to use for this Task."""
    return self.__method

  @property
  def name(self):
    """Returns the name of this Task.

    Will be None if using auto-assigned Task names and this Task has not yet
    been added to a Queue.
    """
    return self.__name

  @property
  def on_queue_url(self):
    """Returns True if this Task will run on the queue's URL."""
    return self.__default_url

  @property
  def payload(self):
    """Returns the payload for this task, which may be None."""
    return self.__payload

  @property
  def queue_name(self):
    """Returns the name of the queue this Task is associated with.

    Will be None if this Task has not yet been added to a queue.
    """
    return self.__queue_name

  @property
  def retry_count(self):
    """Returns the number of retries have been done on the task."""
    return self.__retry_count

  @property
  def retry_options(self):
    """Returns the TaskRetryOptions for this task, which may be None."""
    return self.__retry_options

  @property
  def size(self):
    """Returns the size of this task in bytes."""
    HEADER_SEPERATOR = len(': \r\n')
    header_size = sum((len(key) + len(value) + HEADER_SEPERATOR)
                      for key, value in self.__headers_list)
    return (len(self.__method) + len(self.__payload or '') +
            len(self.__relative_url) + header_size)

  @property
  def tag(self):
    """Returns the tag for this Task."""
    return self.__tag

  @property
  def target(self):
    """Returns the target for this Task."""
    return self.__target

  @property
  def url(self):
    """Returns the relative URL for this Task."""
    return self.__relative_url

  @property
  def was_enqueued(self):
    """Returns True if this Task has been enqueued.

    Note: This will not check if this task already exists in the queue.
    """
    return self.__enqueued

  @property
  def was_deleted(self):
    """Returns True if this Task has been successfully deleted."""
    return self.__deleted

  def add_async(self, queue_name=_DEFAULT_QUEUE, transactional=False, rpc=None):
    """Asynchronously adds this Task to a queue. See Queue.add_async."""
    return Queue(queue_name).add_async(self, transactional, rpc)

  def add(self, queue_name=_DEFAULT_QUEUE, transactional=False):
    """Adds this Task to a queue. See Queue.add."""
    return self.add_async(queue_name, transactional).get_result()

  def extract_params(self):
    """Returns the parameters for this task.

    Returns:
      A dictionary of strings mapping parameter names to their values as
      strings. If the same name parameter has several values then the value will
      be a list of strings. For POST and PULL requests then the parameters are
      extracted from the task payload. For all other methods, the parameters are
      extracted from the url query string. An empty dictionary is returned if
      the task contains an empty payload or query string.

    Raises:
      ValueError: if the payload does not contain valid
        'application/x-www-form-urlencoded' data (for POST and PULL) or the url
        does not contain a valid query (all other methods).
    """
    if self.__method in ('PULL', 'POST'):

      query = self.__payload
    else:
      query = urlparse.urlparse(self.__relative_url).query

    p = {}
    if not query:
      return p

    for key, value in cgi.parse_qsl(
        query, keep_blank_values=True, strict_parsing=True):
      p.setdefault(key, []).append(value)

    for key, value in p.items():
      if len(value) == 1:
        p[key] = value[0]

    return p

  def __repr__(self):
    COMMON_ATTRS = ['eta', 'method', 'name', 'queue_name', 'payload', 'size',
                    'retry_options', 'was_enqueued', 'was_deleted']
    PULL_QUEUE_ATTRS = ['tag']
    PUSH_QUEUE_ATTRS = ['headers', 'url', 'target']

    if self.method == 'PULL':
      attrs = COMMON_ATTRS + PULL_QUEUE_ATTRS
    else:
      attrs = COMMON_ATTRS + PUSH_QUEUE_ATTRS

    properties = ['%s=%r' % (attr, getattr(self, attr))
                  for attr in sorted(attrs)]
    return 'Task<%s>' % ', '.join(properties)


class QueueStatistics(object):
  """Represents the current state of a Queue."""

  _ATTRS = ['queue', 'tasks', 'oldest_eta_usec', 'executed_last_minute',
            'in_flight', 'enforced_rate']

  def __init__(self,
               queue,
               tasks,
               oldest_eta_usec=None,
               executed_last_minute=None,
               in_flight=None,
               enforced_rate=None):
    """Constructor.

    Args:
      queue: The Queue instance this QueueStatistics is for.
      tasks: The number of tasks left.
      oldest_eta_usec: The eta of the oldest non-completed task for the queue;
        None if unknown.
      executed_last_minute: The number of tasks executed in the last minute.
      in_flight: The number of tasks that are currently executing.
      enforced_rate: The current enforced rate. In tasks/second.
    """
    self.queue = queue
    self.tasks = tasks
    self.oldest_eta_usec = oldest_eta_usec
    self.executed_last_minute = executed_last_minute
    self.in_flight = in_flight
    self.enforced_rate = enforced_rate

  def __eq__(self, o):
    if not isinstance(o, QueueStatistics):
      return NotImplemented

    result = True
    for attr in self._ATTRS:
      result = result and (getattr(self, attr) == getattr(o, attr))
    return result

  def __ne__(self, o):
    if not isinstance(o, QueueStatistics):
      return NotImplemented

    result = False
    for attr in self._ATTRS:
      result = result or (getattr(self, attr) != getattr(o, attr))
    return result

  def __repr__(self):
    properties = ['%s=%r' % (attr, getattr(self, attr)) for attr in self._ATTRS]
    return 'QueueStatistics(%s)' % ', '.join(properties)

  @classmethod
  def _ConstructFromFetchQueueStatsResponse(cls, queue, response):
    """Helper for converting from a FetchQeueueStatsResponse_QueueStats proto.

    Args:
      queue: A Queue instance.
      response: a FetchQeueueStatsResponse_QueueStats instance.

    Returns:
      A new QueueStatistics instance.
    """
    args = {'queue': queue, 'tasks': response.num_tasks()}
    if response.oldest_eta_usec() >= 0:
      args['oldest_eta_usec'] = response.oldest_eta_usec()
    else:
      args['oldest_eta_usec'] = None

    if response.has_scanner_info():
      scanner_info = response.scanner_info()
      args['executed_last_minute'] = scanner_info.executed_last_minute()
      if scanner_info.has_requests_in_flight():
        args['in_flight'] = scanner_info.requests_in_flight()
      if scanner_info.has_enforced_rate():
        args['enforced_rate'] = scanner_info.enforced_rate()
    return cls(**args)

  @classmethod
  def fetch_async(cls, queue_or_queues, rpc=None):
    """Asynchronously get the queue details for multiple queues.

    Args:
      queue_or_queues: An iterable of Queue instances, or an iterable of
          strings corresponding to queue names, or a Queue instance or a string
          corresponding to a queue name.
      rpc: An optional UserRPC object.

    Returns:
      A UserRPC object, call get_result to complete the RPC and obtain the
      result.

      If an iterable (other than string) is provided as input, the result will
      be a list of of QueueStatistics objects, one for each queue in the order
      requested.

      Otherwise, if a single item was provided as input, then the result will be
      a single QueueStatistics object.

    Raises:
      TypeError: If queue_or_queues is not one of: Queue instance, string, an
          iterable containing only Queue instances or an iterable containing
          only strings.
    """
    wants_list = True


    if isinstance(queue_or_queues, basestring):
      queue_or_queues = [queue_or_queues]
      wants_list = False

    try:
      queues_list = [queue for queue in queue_or_queues]
    except TypeError:
      queues_list = [queue_or_queues]
      wants_list = False

    contains_strs = any(isinstance(queue, basestring) for queue in queues_list)
    contains_queues = any(isinstance(queue, Queue) for queue in queues_list)

    if contains_strs and contains_queues:
      raise TypeError('queue_or_queues must contain either strings or Queue '
                      'instances, not both.')

    if contains_strs:
      queues_list = [Queue(queue_name) for queue_name in queues_list]

    return cls._FetchMultipleQueues(queues_list, wants_list, rpc)

  @classmethod
  def fetch(cls, queue_or_queues, deadline=10):
    """Get the queue details for multiple queues.

    Args:
      queue_or_queues: An iterable of Queue instances, or an iterable of
          strings corresponding to queue names, or a Queue instance or a string
          corresponding to a queue name.
      deadline: The maximum number of seconds to wait before aborting the
          method call.

    Returns:
      If an iterable (other than string) is provided as input, a list of of
      QueueStatistics objects will be returned, one for each queue in the order
      requested.

      Otherwise, if a single item was provided as input, then a single
      QueueStatistics object will be returned.

    Raises:
      TypeError: If queue_or_queues is not one of: Queue instance, string, an
          iterable containing only Queue instances or an iterable containing
          only strings.
      Error-subclass on application errors.
    """
    _ValidateDeadline(deadline)

    if not queue_or_queues:

      return []

    rpc = create_rpc(deadline)
    cls.fetch_async(queue_or_queues, rpc)
    return rpc.get_result()

  @classmethod
  def _FetchMultipleQueues(cls, queues, multiple, rpc=None):
    """Internal implementation of fetch stats where queues must be a list."""

    def ResultHook(rpc):
      """Process the TaskQueueFetchQueueStatsResponse."""
      try:
        rpc.check_success()
      except apiproxy_errors.ApplicationError, e:
        raise _TranslateError(e.application_error, e.error_detail)

      assert len(queues) == rpc.response.queuestats_size(), (
          'Expected %d results, got %d' % (
              len(queues), rpc.response.queuestats_size()))
      queue_stats = [cls._ConstructFromFetchQueueStatsResponse(queue, response)
                     for queue, response in zip(queues,
                                                rpc.response.queuestats_list())]
      if multiple:
        return queue_stats
      else:
        assert len(queue_stats) == 1
        return queue_stats[0]

    request = taskqueue_service_pb.TaskQueueFetchQueueStatsRequest()
    response = taskqueue_service_pb.TaskQueueFetchQueueStatsResponse()

    requested_app_id = queues[0]._app

    for queue in queues:
      request.add_queue_name(queue.name)
      if queue._app != requested_app_id:
        raise InvalidQueueError('Inconsistent app ids requested.')
    if requested_app_id:
      request.set_app_id(requested_app_id)

    return _MakeAsyncCall('FetchQueueStats',
                          request,
                          response,
                          ResultHook,
                          rpc)


class Queue(object):
  """Represents a Queue."""

  def __init__(self, name=_DEFAULT_QUEUE):
    """Initializer.

    Args:
      name: Name of this queue. If not supplied, defaults to the default queue.

    Raises:
      InvalidQueueNameError if the queue name is invalid.
    """


    if not _QUEUE_NAME_RE.match(name):
      raise InvalidQueueNameError(
          'Queue name does not match pattern "%s"; found %s' %
          (_QUEUE_NAME_PATTERN, name))
    self.__name = name
    self.__url = '%s/%s' % (_DEFAULT_QUEUE_PATH, self.__name)





    self._app = None

  def purge(self):
    """Removes all the tasks in this Queue.

    This function takes constant time to purge a Queue and some delay may apply
    before the call is effective.

    Raises:
      Error-subclass on application errors.
    """
    request = taskqueue_service_pb.TaskQueuePurgeQueueRequest()
    response = taskqueue_service_pb.TaskQueuePurgeQueueResponse()

    request.set_queue_name(self.__name)
    if self._app:
      request.set_app_id(self._app)

    try:
      apiproxy_stub_map.MakeSyncCall('taskqueue',
                                     'PurgeQueue',
                                     request,
                                     response)
    except apiproxy_errors.ApplicationError, e:
      raise _TranslateError(e.application_error, e.error_detail)

  def delete_tasks_by_name_async(self, task_name, rpc=None):
    """Asynchronously deletes a Task or list of Tasks in this Queue, by name.

    This function is identical to delete_tasks_by_name() except that it returns
    an asynchronous object. You can call get_result() on the return value to
    block on the call.

    Args:
      task_name: A string corresponding to a task name, or an iterable of
      strings corresponding to task names.
      rpc: An optional UserRPC object.

    Returns:
      A UserRPC object, call get_result to complete the RPC and obtain the
      result.

      If an iterable (other than string) is provided as input, the result will
      be a list of of Task objects, one for each task name in the order
      requested. The Task.was_deleted property will be True for each task
      deleted by this call, and will be False for unknown and tombstoned tasks.

      Otherwise, if a single string was provided as input, then the result will
      be a single Task object.

    Raises:
      DuplicateTaskNameError: if a Task name is repeated in the request.
    """
    if isinstance(task_name, str):
      return self.delete_tasks_async(Task(name=task_name), rpc)
    else:
      tasks = [Task(name=name) for name in task_name]
      return self.delete_tasks_async(tasks, rpc)

  def delete_tasks_by_name(self, task_name):
    """Deletes a Task or list of Tasks in this Queue, by name.

    When multiple tasks are specified, an exception will be raised if any
    individual task fails to be deleted.

    Args:
      task_name: A string corresponding to a task name, or an iterable of
      strings corresponding to task names.

    Returns:
      If an iterable (other than string) is provided as input,  a list of of
      Task objects, one for each task name in the order requested. The
      Task.was_deleted property will be True for each task deleted by this call,
      and will be False for unknown and tombstoned tasks.

      Otherwise, if a single string was provided as input, a single Task object.

    Raises:
      DuplicateTaskNameError: if a Task name is repeated in the request.
      Error-subclass on application errors.
    """
    return self.delete_tasks_by_name_async(task_name).get_result()

  def delete_tasks_async(self, task, rpc=None):
    """Asynchronously deletes a Task or list of Tasks in this Queue.

    This function is identical to delete_tasks() except that it returns an
    asynchronous object. You can call get_result() on the return value to block
    on the call.

    Args:
      task: A Task instance or a list of Task instances that will be deleted
        from the Queue.
      rpc: An optional UserRPC object.

    Returns:
      A UserRPC object, call get_result to complete the RPC and obtain the Task
        or list of tasks passed into this call.

    Raises:
      BadTaskStateError: if the Task(s) to be deleted do not have task names or
        have already been deleted.
      DuplicateTaskNameError: if a Task is repeated in the request.
    """
    try:
      tasks = list(iter(task))
    except TypeError:
      tasks = [task]
      multiple = False
    else:
      multiple = True

    return self.__DeleteTasks(tasks, multiple, rpc)

  def delete_tasks(self, task):
    """Deletes a Task or list of Tasks in this Queue.

    When multiple tasks are specified, an exception will be raised if any
    individual task fails to be deleted. Check the task.was_deleted property.

    Task name is the only task attribute used to select tasks for deletion. If
    there is any task with was_deleted property set to True, or without a task
    name, a BadTaskStateError will be raised immediately.

    Args:
      task: A Task instance or a list of Task instances that will be deleted
        from the Queue.

    Returns:
      The Task or list of tasks passed into this call.

    Raises:
      BadTaskStateError: if the Task(s) to be deleted do not have task names or
        have already been deleted.
      DuplicateTaskNameError: if a Task is repeated in the request.
      Error-subclass on application errors.
    """
    return self.delete_tasks_async(task).get_result()

  def __DeleteTasks(self, tasks, multiple, rpc=None):
    """Internal implementation of delete_tasks_async(), tasks must be a list."""

    def ResultHook(rpc):
      """Process the TaskQueueDeleteResponse."""
      try:
        rpc.check_success()
      except apiproxy_errors.ApplicationError, e:
        raise _TranslateError(e.application_error, e.error_detail)

      assert rpc.response.result_size() == len(tasks), (
          'expected %d results from delete(), got %d' % (
              len(tasks), rpc.response.result_size()))

      IGNORED_STATES = [
          taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_TASK,
          taskqueue_service_pb.TaskQueueServiceError.TOMBSTONED_TASK]

      exception = None
      for task, result in zip(tasks, rpc.response.result_list()):
        if result == taskqueue_service_pb.TaskQueueServiceError.OK:

          task._Task__deleted = True
        elif result in IGNORED_STATES:

          task._Task__deleted = False
        elif exception is None:
          exception = _TranslateError(result)

      if exception is not None:
        raise exception

      if multiple:
        return tasks
      else:
        assert len(tasks) == 1
        return tasks[0]

    request = taskqueue_service_pb.TaskQueueDeleteRequest()
    response = taskqueue_service_pb.TaskQueueDeleteResponse()

    request.set_queue_name(self.__name)
    task_names = set()
    for task in tasks:
      if not task.name:
        raise BadTaskStateError('Task name must be specified for a task')
      if task.was_deleted:
        raise BadTaskStateError('Task %s has already been deleted' % task.name)
      if task.name in task_names:
        raise DuplicateTaskNameError(
            'The task name %r is used more than once in the request' %
            task.name)
      task_names.add(task.name)
      request.add_task_name(task.name)

    return _MakeAsyncCall('Delete',
                          request,
                          response,
                          ResultHook,
                          rpc)

  @staticmethod
  def _ValidateLeaseSeconds(lease_seconds):

    if not isinstance(lease_seconds, (float, int, long)):
      raise TypeError(
          'lease_seconds must be a float or an integer')
    lease_seconds = float(lease_seconds)

    if lease_seconds < 0.0:
      raise InvalidLeaseTimeError(
          'lease_seconds must not be negative')
    if lease_seconds > MAX_LEASE_SECONDS:
      raise InvalidLeaseTimeError(
          'Lease time must not be greater than %d seconds' %
          MAX_LEASE_SECONDS)
    return lease_seconds

  @staticmethod
  def _ValidateMaxTasks(max_tasks):
    if not isinstance(max_tasks, (int, long)):
      raise TypeError(
          'max_tasks must be an integer')

    if max_tasks <= 0:
      raise InvalidMaxTasksError(
          'Negative or zero tasks requested')
    if max_tasks > MAX_TASKS_PER_LEASE:
      raise InvalidMaxTasksError(
          'Only %d tasks can be leased at once' %
          MAX_TASKS_PER_LEASE)

  def _QueryAndOwnTasks(self, request, response, queue_name, rpc=None):

    def ResultHook(rpc):
      """Process the TaskQueueQueryAndOwnTasksResponse."""
      try:
        rpc.check_success()
      except apiproxy_errors.ApplicationError, e:
        raise _TranslateError(e.application_error, e.error_detail)

      tasks = []
      for response_task in rpc.response.task_list():
        tasks.append(
            Task._FromQueryAndOwnResponseTask(queue_name, response_task))
      return tasks

    return _MakeAsyncCall('QueryAndOwnTasks',
                          request,
                          response,
                          ResultHook,
                          rpc)

  def lease_tasks_async(self, lease_seconds, max_tasks, rpc=None):
    """Asynchronously leases a number of tasks from the Queue.

    This function is identical to lease_tasks() except that it returns an
    asynchronous object. You can call get_result() on the return value to block
    on the call.

    Args:
      lease_seconds: Number of seconds to lease the tasks.
      max_tasks: Max number of tasks to lease from the pull Queue.
      rpc: An optional UserRPC object.

    Returns:
      A UserRPC object, call get_result to complete the RPC and obtain the list
        of tasks leased from the Queue.

    Raises:
      InvalidLeaseTimeError: if lease_seconds is not a valid float or integer
        number or is outside the valid range.
      InvalidMaxTasksError: if max_tasks is not a valid integer or is outside
        the valid range.
    """
    lease_seconds = self._ValidateLeaseSeconds(lease_seconds)
    self._ValidateMaxTasks(max_tasks)

    request = taskqueue_service_pb.TaskQueueQueryAndOwnTasksRequest()
    response = taskqueue_service_pb.TaskQueueQueryAndOwnTasksResponse()

    request.set_queue_name(self.__name)
    request.set_lease_seconds(lease_seconds)
    request.set_max_tasks(max_tasks)

    return self._QueryAndOwnTasks(request, response, self.__name, rpc)

  def lease_tasks(self, lease_seconds, max_tasks, deadline=10):
    """Leases a number of tasks from the Queue for a period of time.

    This method can only be performed on a pull Queue. Any non-pull tasks in
    the pull Queue will be converted into pull tasks when being leased. If
    fewer than max_tasks are available, all available tasks will be returned.
    The lease_tasks method supports leasing at most 1000 tasks for no longer
    than a week in a single call.

    Args:
      lease_seconds: Number of seconds to lease the tasks.
      max_tasks: Max number of tasks to lease from the pull Queue.
      deadline: The maximum number of seconds to wait before aborting the
        method call.

    Returns:
      A list of tasks leased from the Queue.

    Raises:
      InvalidLeaseTimeError: if lease_seconds is not a valid float or integer
        number or is outside the valid range.
      InvalidMaxTasksError: if max_tasks is not a valid integer or is outside
        the valid range.
      InvalidQueueModeError: if invoked on a queue that is not in pull mode.
      Error-subclass on application errors.
    """
    _ValidateDeadline(deadline)
    rpc = create_rpc(deadline)
    self.lease_tasks_async(lease_seconds, max_tasks, rpc)
    return rpc.get_result()

  def lease_tasks_by_tag_async(self,
                               lease_seconds,
                               max_tasks,
                               tag=None,
                               rpc=None):
    """Asynchronously leases a number of tasks from the Queue.

    This function is identical to lease_tasks_by_tag() except that it returns an
    asynchronous object. You can call get_result() on the return value to block
    on the call.

    Args:
      lease_seconds: Number of seconds to lease the tasks.
      max_tasks: Max number of tasks to lease from the pull Queue.
      tag: The to query for, or None to group by the first available tag.
      rpc: An optional UserRPC object.

    Returns:
      A UserRPC object, call get_result to complete the RPC and obtain the list
        of tasks leased from the Queue.

    Raises:
      InvalidLeaseTimeError: if lease_seconds is not a valid float or integer
        number or is outside the valid range.
      InvalidMaxTasksError: if max_tasks is not a valid integer or is outside
        the valid range.
    """
    lease_seconds = self._ValidateLeaseSeconds(lease_seconds)
    self._ValidateMaxTasks(max_tasks)

    request = taskqueue_service_pb.TaskQueueQueryAndOwnTasksRequest()
    response = taskqueue_service_pb.TaskQueueQueryAndOwnTasksResponse()

    request.set_queue_name(self.__name)
    request.set_lease_seconds(lease_seconds)
    request.set_max_tasks(max_tasks)
    request.set_group_by_tag(True)
    if tag is not None:
      request.set_tag(tag)

    return self._QueryAndOwnTasks(request, response, self.__name, rpc)

  def lease_tasks_by_tag(self, lease_seconds, max_tasks, tag=None, deadline=10):
    """Leases a number of tasks from the Queue for a period of time.

    This method can only be performed on a pull Queue. Any non-pull tasks in
    the pull Queue will be converted into pull tasks when being leased. If
    fewer than max_tasks are available, all available tasks will be returned.
    The lease_tasks method supports leasing at most 1000 tasks for no longer
    than a week in a single call.

    Args:
      lease_seconds: Number of seconds to lease the tasks.
      max_tasks: Max number of tasks to lease from the pull Queue.
      tag: The to query for, or None to group by the first available tag.
      deadline: The maximum number of seconds to wait before aborting the
        method call.

    Returns:
      A list of tasks leased from the Queue.

    Raises:
      InvalidLeaseTimeError: if lease_seconds is not a valid float or integer
        number or is outside the valid range.
      InvalidMaxTasksError: if max_tasks is not a valid integer or is outside
        the valid range.
      InvalidQueueModeError: if invoked on a queue that is not in pull mode.
      Error-subclass on application errors.
    """
    _ValidateDeadline(deadline)
    rpc = create_rpc(deadline)
    self.lease_tasks_by_tag_async(lease_seconds, max_tasks, tag, rpc)
    return rpc.get_result()

  def add_async(self, task, transactional=False, rpc=None):
    """Asynchronously adds a Task or list of Tasks into this Queue.

    This function is identical to add() except that it returns an asynchronous
    object. You can call get_result() on the return value to block on the call.

    Args:
      task: A Task instance or a list of Task instances that will be added to
        the queue.
      transactional: If True, transactional Tasks will be added to the queue but
        cannot be run or leased until after the transaction succeeds.  If the
        transaction fails then the Tasks will be removed from the queue (and
        therefore never run).  If False, the added task(s) are available to run
        immediately; any enclosing transaction's success or failure is ignored.
      rpc: An optional UserRPC object.

    Returns:
      A UserRPC object; call get_result to complete the RPC and obtain the Task
        or list of Tasks that was supplied to this method. Successfully
        queued Tasks will have a valid queue name and task name after the
        call; such Task objects are marked as queued and cannot be added
        again.

      Note: Task objects returned from transactional adds are not
        notified or updated when the enclosing transaction succeeds or fails.

    Raises:
      BadTaskStateError: if the Task(s) has already been added to a queue.
      BadTransactionStateError: if the transactional argument is true but this
        call is being made outside of the context of a transaction.
      DuplicateTaskNameError: if a Task name is repeated in the request.
      InvalidTaskError: if both push and pull tasks exist in the task list.
      InvalidTaskNameError: if a Task name is provided but is not legal.
      TooManyTasksError: if task contains more than MAX_TASKS_PER_ADD tasks.
      TransactionalRequestTooLargeError: if transactional is True and the total
        size of the tasks and supporting request data exceeds
        MAX_TRANSACTIONAL_REQUEST_SIZE_BYTES.
    """
    try:
      tasks = list(iter(task))
    except TypeError:
      tasks = [task]
      multiple = False
    else:
      multiple = True




    has_push_task = False
    has_pull_task = False
    for task in tasks:
      if task.method == 'PULL':
        has_pull_task = True
      else:
        has_push_task = True

    if has_push_task and has_pull_task:
      raise InvalidTaskError(
          'Can not add both push and pull tasks in a single call.')

    if has_push_task:
      fill_function = self.__FillAddPushTasksRequest
    else:
      fill_function = self.__FillAddPullTasksRequest
    return self.__AddTasks(tasks,
                           transactional,
                           fill_function,
                           multiple,
                           rpc)

  def add(self, task, transactional=False):
    """Adds a Task or list of Tasks into this Queue.

    If a list of more than one Tasks is given, a raised exception does not
    guarantee that no tasks were added to the queue (unless transactional is set
    to True). To determine which tasks were successfully added when an exception
    is raised, check the Task.was_enqueued property.

    Push tasks, i.e. those with method not equal to PULL, may not be added to
    queues in pull mode. Similarly, pull tasks may not be added to queues in
    push mode.

    If a TaskAlreadyExistsError or TombstonedTaskError is raised, the caller can
    be guaranteed that for each one of the provided tasks, either the
    corresponding task was successfully added, or a task with the given name was
    successfully added in the past.

    Args:
      task: A Task instance or a list of Task instances that will be added to
        the queue.
      transactional: If True, transactional Tasks will be added to the queue but
        cannot be run or leased until after the transaction succeeds.  If the
        transaction fails then the Tasks will be removed from the queue (and
        therefore never run).  If False, the added task(s) are available to run
        immediately; any enclosing transaction's success or failure is ignored.

    Returns:
      The Task or list of tasks that was supplied to this method. Successfully
        queued Tasks will have a valid queue name and task name after the
        call; such Task objects are marked as queued and cannot be added
        again.

      Note: Task objects returned from transactional adds are not
        notified or updated when the enclosing transaction succeeds or fails.

    Raises:
      BadTaskStateError: if the Task(s) has already been added to a queue.
      BadTransactionStateError: if the transactional argument is true but this
        call is being made outside of the context of a transaction.
      DuplicateTaskNameError: if a Task name is repeated in the request.
      InvalidTaskNameError: if a Task name is provided but is not legal.
      InvalidTaskError: if both push and pull tasks exist in the task list.
      InvalidQueueModeError: if a task with method PULL is added to a queue in
        push mode, or a task with method not equal to PULL is added to a queue
        in pull mode.
      TaskAlreadyExistsError: if a task with the same name as a given name has
        previously been added to the queue.
      TombstonedTaskError: if a task with the same name as a given name has
        previously been added to the queue and deleted.
      TooManyTasksError: if task contains more than MAX_TASKS_PER_ADD tasks.
      TransactionalRequestTooLargeError: if transactional is True and the total
        size of the tasks and supporting request data exceeds
        MAX_TRANSACTIONAL_REQUEST_SIZE_BYTES.
      Error-subclass on application errors.
    """
    if task:
      return self.add_async(task, transactional).get_result()
    else:
      return []

  def __AddTasks(self, tasks, transactional, fill_request, multiple, rpc=None):
    """Internal implementation of adding tasks where tasks must be a list."""

    def ResultHook(rpc):
      """Process the TaskQueueBulkAddResponse."""
      try:
        rpc.check_success()
      except apiproxy_errors.ApplicationError, e:
        raise _TranslateError(e.application_error, e.error_detail)

      assert rpc.response.taskresult_size() == len(tasks), (
          'expected %d results from BulkAdd(), got %d' % (
              len(tasks), rpc.response.taskresult_size()))

      exception = None
      for task, task_result in zip(tasks, rpc.response.taskresult_list()):
        if (task_result.result() ==
            taskqueue_service_pb.TaskQueueServiceError.OK):
          if task_result.has_chosen_task_name():
            task._Task__name = task_result.chosen_task_name()
          task._Task__queue_name = self.__name
          task._Task__enqueued = True
        elif (task_result.result() ==
              taskqueue_service_pb.TaskQueueServiceError.SKIPPED):
          pass
        elif (exception is None or isinstance(exception, TaskAlreadyExistsError)
              or isinstance(exception, TombstonedTaskError)):
          exception = _TranslateError(task_result.result())

      if exception is not None:
        raise exception

      if multiple:
        return tasks
      else:
        assert len(tasks) == 1
        return tasks[0]

    if len(tasks) > MAX_TASKS_PER_ADD:
      raise TooManyTasksError(
          'No more than %d tasks can be added in a single call' %
          MAX_TASKS_PER_ADD)

    request = taskqueue_service_pb.TaskQueueBulkAddRequest()
    response = taskqueue_service_pb.TaskQueueBulkAddResponse()

    task_names = set()
    for task in tasks:
      if task.name:
        if task.name in task_names:
          raise DuplicateTaskNameError(
              'The task name %r is used more than once in the request' %
              task.name)
        task_names.add(task.name)
      if task.was_enqueued:
        raise BadTaskStateError('Task has already been enqueued.')

      fill_request(task, request.add_add_request(), transactional)

    if transactional and (request.ByteSize() >
                          MAX_TRANSACTIONAL_REQUEST_SIZE_BYTES):
      raise TransactionalRequestTooLargeError(
          'Transactional request size must be less than %d; found %d' %
          (MAX_TRANSACTIONAL_REQUEST_SIZE_BYTES, request.ByteSize()))

    return _MakeAsyncCall('BulkAdd',
                          request,
                          response,
                          ResultHook,
                          rpc)

  def __FillTaskQueueRetryParameters(self,
                                     retry_options,
                                     retry_retry_parameters):
    """Populates a TaskQueueRetryParameters with data from a TaskRetryOptions.

    Args:
      retry_options: The TaskRetryOptions instance to use as a source for the
        data to be added to retry_retry_parameters.
      retry_retry_parameters: A taskqueue_service_pb.TaskQueueRetryParameters
        to populate.
    """
    if retry_options.min_backoff_seconds is not None:
      retry_retry_parameters.set_min_backoff_sec(
          retry_options.min_backoff_seconds)

    if retry_options.max_backoff_seconds is not None:
      retry_retry_parameters.set_max_backoff_sec(
          retry_options.max_backoff_seconds)

    if retry_options.task_retry_limit is not None:
      retry_retry_parameters.set_retry_limit(retry_options.task_retry_limit)

    if retry_options.task_age_limit is not None:
      retry_retry_parameters.set_age_limit_sec(retry_options.task_age_limit)

    if retry_options.max_doublings is not None:
      retry_retry_parameters.set_max_doublings(retry_options.max_doublings)

  def __FillAddPushTasksRequest(self, task, task_request, transactional):
    """Populates a TaskQueueAddRequest with the data from a push Task instance.

    Args:
      task: The Task instance to use as a source for the data to be added to
        task_request.
      task_request: The taskqueue_service_pb.TaskQueueAddRequest to populate.
      transactional: If true then populates the task_request.transaction message
        with information from the enclosing transaction (if any).

    Raises:
      BadTaskStateError: If the task was already added to a Queue.
      BadTransactionStateError: If the transactional argument is True and there
        is no enclosing transaction.
      InvalidTaskNameError: If the transactional argument is True and the task
        is named.
    """
    task_request.set_mode(taskqueue_service_pb.TaskQueueMode.PUSH)
    self.__FillTaskCommon(task, task_request, transactional)

    adjusted_url = task.url
    if task.on_queue_url:
      adjusted_url = self.__url + task.url








    task_request.set_method(_METHOD_MAP.get(task.method))
    task_request.set_url(adjusted_url)

    if task.payload:
      task_request.set_body(task.payload)
    for key, value in _flatten_params(task.headers):
      header = task_request.add_header()
      header.set_key(key)
      header.set_value(value)

    if task.retry_options:
      self.__FillTaskQueueRetryParameters(
          task.retry_options, task_request.mutable_retry_parameters())

  def __FillAddPullTasksRequest(self, task, task_request, transactional):
    """Populates a TaskQueueAddRequest with the data from a pull Task instance.

    Args:
      task: The Task instance to use as a source for the data to be added to
        task_request.
      task_request: The taskqueue_service_pb.TaskQueueAddRequest to populate.
      transactional: If true then populates the task_request.transaction message
        with information from the enclosing transaction (if any).

    Raises:
      BadTaskStateError: if the task doesn't have a payload, or has already been
        added to a Queue.
      BadTransactionStateError: if the transactional argument is True and there
        is no enclosing transaction.
      InvalidTaskNameError: if the transactional argument is True and the task
        is named.
    """
    task_request.set_mode(taskqueue_service_pb.TaskQueueMode.PULL)
    self.__FillTaskCommon(task, task_request, transactional)
    if task.payload is not None:
      task_request.set_body(task.payload)
    else:
      raise BadTaskStateError('Pull task must have a payload')

  def __FillTaskCommon(self, task, task_request, transactional):
    """Fills common fields for both push tasks and pull tasks."""
    if self._app:
      task_request.set_app_id(self._app)
    task_request.set_queue_name(self.__name)
    task_request.set_eta_usec(task._eta_usec)
    if task.name:
      task_request.set_task_name(task.name)
    else:
      task_request.set_task_name('')
    if task.tag:
      task_request.set_tag(task.tag)



    if transactional:
      from google.appengine.api import datastore
      if not datastore._MaybeSetupTransaction(task_request, []):
        raise BadTransactionStateError(
            'Transactional adds are not allowed outside of transactions')

    if task_request.has_transaction() and task.name:
      raise InvalidTaskNameError(
          'Task bound to a transaction cannot be named.')

  @property
  def name(self):
    """Returns the name of this queue."""
    return self.__name

  def modify_task_lease(self, task, lease_seconds):
    """Modifies the lease of a task in this queue.

    Args:
      task: A task instance that will have its lease modified.
      lease_seconds: Number of seconds, from the current time, that the task
        lease will be modified to. If lease_seconds is 0, then the task lease
        is removed and the task will be available for leasing again using
        the lease_tasks method.

    Raises:
      TypeError: if lease_seconds is not a valid float or integer.
      InvalidLeaseTimeError: if lease_seconds is outside the valid range.
      Error-subclass on application errors.
    """
    lease_seconds = self._ValidateLeaseSeconds(lease_seconds)

    request = taskqueue_service_pb.TaskQueueModifyTaskLeaseRequest()
    response = taskqueue_service_pb.TaskQueueModifyTaskLeaseResponse()

    request.set_queue_name(self.__name)
    request.set_task_name(task.name)
    request.set_eta_usec(task._eta_usec)
    request.set_lease_seconds(lease_seconds)

    try:
      apiproxy_stub_map.MakeSyncCall('taskqueue',
                                     'ModifyTaskLease',
                                     request,
                                     response)
    except apiproxy_errors.ApplicationError, e:
      raise _TranslateError(e.application_error, e.error_detail)

    task._Task__eta_posix = response.updated_eta_usec() * 1e-6
    task._Task__eta = None

  def fetch_statistics_async(self, rpc=None):
    """Asynchronously get the current details about this queue.

    Args:
      rpc: An optional UserRPC object.

    Returns:
      A UserRPC object, call get_result to complete the RPC and obtain a
          QueueStatistics instance containing information about this queue.
    """
    return QueueStatistics.fetch_async(self, rpc)

  def fetch_statistics(self, deadline=10):
    """Get the current details about this queue.

    Args:
      deadline: The maximum number of seconds to wait before aborting the
          method call.

    Returns:
      A QueueStatistics instance containing information about this queue.
      Error-subclass on application errors.
    """
    _ValidateDeadline(deadline)
    rpc = create_rpc(deadline)
    self.fetch_statistics_async(rpc)
    return rpc.get_result()

  def __repr__(self):
    ATTRS = ['name']
    if self._app:

      ATTRS.append('_app')
    properties = ['%s=%r' % (attr, getattr(self, attr)) for attr in ATTRS]
    return 'Queue<%s>' % ', '.join(properties)

  def __eq__(self, o):
    if not isinstance(o, Queue):
      return NotImplemented
    return self.name == o.name and self._app == o._app

  def __ne__(self, o):
    if not isinstance(o, Queue):
      return NotImplemented
    return self.name != o.name or self._app != o._app



def add(*args, **kwargs):
  """Convenience method will create a Task and add it to a queue.

  All parameters are optional.

  Push tasks, i.e. those with method not equal to PULL, may not be added to
  queues in pull mode. Similarly, pull tasks may not be added to queues in push
  mode.

  Args:
    payload: The payload data for this Task that will be delivered to the
      webhook as the HTTP request body or fetched by workers for pull queues.
      This is only allowed for POST, PUT, and PULL methods.
    queue_name: Name of queue to insert task into. If not supplied, defaults to
      the default queue.
    name: Name to give the Task; if not specified, a name will be
      auto-generated when added to a queue and assigned to this object. Must
      match the _TASK_NAME_PATTERN regular expression.
    method: Method to use when accessing the webhook. Defaults to 'POST'. If
      set to 'PULL', task will not be automatiacally delivered to the webhook,
      instead it stays in the queue until leased.
    url: Relative URL where the webhook that should handle this task is
      located for this application. May have a query string unless this is
      a POST method. Must not be specified if method is PULL.
    headers: Dictionary of headers to pass to the webhook. Values in the
      dictionary may be iterable to indicate repeated header fields. Must not be
      specified if method is PULL.
    params: Dictionary of parameters to use for this Task. For POST and PULL
      requests these params will be encoded as
      'application/x-www-form-urlencoded' and set to the payload. For all other
      methods, the parameters will be converted to a query string. Must not be
      specified if the URL already contains a query string, or the task already
      has a payload.
    transactional: If True, adds the task(s) if and only if the enclosing
      transaction is successfully committed. It is an error for transactional
      to be True in the absence of an enclosing transaction. If False, adds
      the task(s) immediately, ignoring any enclosing transaction's success or
      failure.
    countdown: Time in seconds into the future that this Task should execute.
      Defaults to zero.
    eta: A datetime.datetime specifying the absolute time at which the task
      should be executed. Must not be specified if 'countdown' is specified.
      This may be timezone-aware or timezone-naive. If None, defaults to now.
      For pull tasks, no worker will be able to lease this task before the time
      indicated by eta.
    retry_options: TaskRetryOptions used to control when the task will be
      retried if it fails.
    tag: The tag to be used when grouping by tag (PULL tasks only).
    target: The alternate version/backend on which to execute this task, or
      DEFAULT_APP_VERSION to execute on the application's default version.

  Returns:
    The Task that was added to the queue.

  Raises:
    BadTransactionStateError: if the transactional argument is true but this
      call is being made outside of the context of a transaction.
    InvalidEtaError: if the ETA is too far into the future.
    InvalidQueueModeError if a task with method PULL is added to a queue in push
      mode, or a task with method not equal to PULL is added to a queue in pull
      mode.
    InvalidTagError: if the tag is too long.
    InvalidTaskError if any of the parameters are invalid.
    InvalidTaskNameError if the task name is invalid.
    InvalidUrlError if the task URL is invalid or too long.
    TaskTooLargeError if the task with its payload is too large.
    TransactionalRequestTooLargeError: if transactional is True and the total
      size of the tasks and supporting request data exceeds
      MAX_TRANSACTIONAL_REQUEST_SIZE_BYTES.
  """
  transactional = kwargs.pop('transactional', False)
  queue_name = kwargs.pop('queue_name', _DEFAULT_QUEUE)
  return Task(*args, **kwargs).add(
      queue_name=queue_name, transactional=transactional)
