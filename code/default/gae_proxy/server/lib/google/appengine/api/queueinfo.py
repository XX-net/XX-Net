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




"""QueueInfo tools.

A library for working with QueueInfo records, describing task queue entries
for an application. Supports loading the records from queue.yaml.

A queue has two required parameters and various optional ones. The required
parameters are 'name' (must be unique for an appid) and 'rate' (the rate
at which jobs in the queue are run). There is an optional parameter
'bucket_size' that will allow tokens to be 'saved up' (for more on the
algorithm, see http://en.wikipedia.org/wiki/Token_Bucket). rate is expressed
as number/unit, with number being an int or a float, and unit being one of
's' (seconds), 'm' (minutes), 'h' (hours) or 'd' (days). bucket_size is
an integer.

An example of the use of bucket_size rate: the free email quota is 2000/d,
and the maximum you can send in a single minute is 11. So we can define a
queue for sending email like this:

queue:
- name: mail-queue
  rate: 2000/d
  bucket_size: 10

If this queue had been idle for a while before some jobs were submitted to it,
the first 10 jobs submitted would be run immediately, then subsequent ones
would be run once every 40s or so. The limit of 2000 per day would still apply.

Another optional parameter is 'max_concurrent_requests', which pertains to the
requests being made by the queue. It specifies the maximum number of requests
that may be in-flight at any one time. An example:

queue:
- name: server-queue
  rate: 50/s
  max_concurrent_requests: 5

Each queue has an optional 'mode' parameter with legal values 'push' and 'pull'.
If mode is not specified, it defaults to 'push'. Tasks in queues with mode
'push' are invoked (pushed) at the specified rate. Tasks in queues with mode
'pull' are not directly invoked by App Engine. These tasks are leased for a
period by client code, and deleted by client code when the task's work is
finished. If not deleted before the expiry of the lease, the tasks are available
for lease again.

Each queue has an optional 'target' parameter. If specified all tasks inserted
into the queue will be executed on the specified alternate version/server
instance.

A queue may also optionally specify retry_parameters.

  retry_parameters:
    task_retry_limit: 100
    task_age_limit: 1d
    min_backoff_seconds: 0.1
    max_backoff_seconds: 3600
    max_doublings: 10

Each task in the queue that fails during execution will be retried using these
parameters.  All these fields are optional.

task_retry_limit: A non-negative integer. Tasks will be retried a maximum of
  task_retry_limit times before failing permanently.  If task_age_limit is also
  specified, both task_retry_limit and task_age_limit must be exceeded before a
  task fails permanently.

task_age_limit: A non-negative floating point number followed by a suffix s
  (seconds), m (minutes), h (hours) or d (days). If the time since a task was
  first tried exceeds task_age_limit, it will fail permanently. If
  task_retry_limit is also specified, both task_retry_limit and task_age_limit
  must be exceeded before a task fails permanently.

min_backoff_seconds: A non-negative floating point number. This is the minimum
  interval after the first failure and the first retry of a task. If
  max_backoff_seconds is also specified, min_backoff_seconds must not be greater
  than max_backoff_seconds.

max_backoff_seconds: A non-negative floating point number. This is the maximum
  allowed interval between successive retries of a failed task. If
  min_backoff_seconds is also specified, min_backoff_seconds must not be greater
  than max_backoff_seconds.

max_doublings: A non-negative integer. On successive failures, the retry backoff
  interval will be successively doubled up to max_doublings times, starting at
  min_backoff_seconds and not exceeding max_backoff_seconds.  For retries after
  max_doublings, the retry backoff will increase by the value of the backoff
  when doubling ceased. e.g. for min_backoff_seconds of 1 ,max_doublings of 5,
  we have successive retry backoffs of 1, 2, 4, 8, 16, 32, 64, 96, 128, ...
  not exceeding max_backoff_seconds.

A queue may optionally specify an acl (Access Control List).
  acl:
  - user_email: a@foo.com
  - writer_email: b@gmail.com
Each email must correspond to an account hosted by Google. The acl is
enforced for queue access from outside AppEngine.

An app's queues are also subject to storage quota limits for their stored tasks,
i.e. those tasks that have been added to queues but not yet executed. This quota
is part of their total storage quota (including datastore and blobstore quota).
We allow an app to override the default portion of this quota available for
taskqueue storage (100M) with a top level field "total_storage_limit".

total_storage_limit: 1.2G

If no suffix is specified, the number is interpreted as bytes. Supported
suffices are B (bytes), K (kilobytes), M (megabytes), G (gigabytes) and
T (terabytes). If total_storage_limit exceeds the total disk storage
available to an app, it is clamped.
"""








from google.appengine.api import appinfo
from google.appengine.api import validation
from google.appengine.api import yaml_builder
from google.appengine.api import yaml_listener
from google.appengine.api import yaml_object
from google.appengine.api.taskqueue import taskqueue_service_pb


_NAME_REGEX = r'^[A-Za-z0-9-]{0,499}$'
_RATE_REGEX = r'^(0|[0-9]+(\.[0-9]*)?/[smhd])'
_TOTAL_STORAGE_LIMIT_REGEX = r'^([0-9]+(\.[0-9]*)?[BKMGT]?)'
_MODE_REGEX = r'(pull)|(push)'




MODULE_ID_RE_STRING = r'(?!-)[a-z\d\-]{1,63}'


MODULE_VERSION_RE_STRING = r'(?!-)[a-z\d\-]{1,100}'
_VERSION_REGEX = r'^(?:(?:(%s)\.)?)(%s)$' % (MODULE_VERSION_RE_STRING,
                                            MODULE_ID_RE_STRING)

QUEUE = 'queue'

NAME = 'name'
RATE = 'rate'
BUCKET_SIZE = 'bucket_size'
MODE = 'mode'
TARGET = 'target'
MAX_CONCURRENT_REQUESTS = 'max_concurrent_requests'
TOTAL_STORAGE_LIMIT = 'total_storage_limit'

BYTE_SUFFIXES = 'BKMGT'

RETRY_PARAMETERS = 'retry_parameters'
TASK_RETRY_LIMIT = 'task_retry_limit'
TASK_AGE_LIMIT = 'task_age_limit'
MIN_BACKOFF_SECONDS = 'min_backoff_seconds'
MAX_BACKOFF_SECONDS = 'max_backoff_seconds'
MAX_DOUBLINGS = 'max_doublings'

ACL = 'acl'
USER_EMAIL = 'user_email'
WRITER_EMAIL = 'writer_email'


class MalformedQueueConfiguration(Exception):
  """Configuration file for Task Queue is malformed."""


class RetryParameters(validation.Validated):
  """Retry parameters for a single task queue."""
  ATTRIBUTES = {
      TASK_RETRY_LIMIT: validation.Optional(validation.TYPE_INT),
      TASK_AGE_LIMIT: validation.Optional(validation.TimeValue()),
      MIN_BACKOFF_SECONDS: validation.Optional(validation.TYPE_FLOAT),
      MAX_BACKOFF_SECONDS: validation.Optional(validation.TYPE_FLOAT),
      MAX_DOUBLINGS: validation.Optional(validation.TYPE_INT),
  }


class Acl(validation.Validated):
  """Access control list for a single task queue."""
  ATTRIBUTES = {
      USER_EMAIL: validation.Optional(validation.TYPE_STR),
      WRITER_EMAIL: validation.Optional(validation.TYPE_STR),
  }


class QueueEntry(validation.Validated):
  """A queue entry describes a single task queue."""
  ATTRIBUTES = {
      NAME: _NAME_REGEX,
      RATE: validation.Optional(_RATE_REGEX),
      MODE: validation.Optional(_MODE_REGEX),
      BUCKET_SIZE: validation.Optional(validation.TYPE_INT),
      MAX_CONCURRENT_REQUESTS: validation.Optional(validation.TYPE_INT),
      RETRY_PARAMETERS: validation.Optional(RetryParameters),
      ACL: validation.Optional(validation.Repeated(Acl)),


      TARGET: validation.Optional(_VERSION_REGEX),
  }


class QueueInfoExternal(validation.Validated):
  """QueueInfoExternal describes all queue entries for an application."""
  ATTRIBUTES = {
      appinfo.APPLICATION: validation.Optional(appinfo.APPLICATION_RE_STRING),
      TOTAL_STORAGE_LIMIT: validation.Optional(_TOTAL_STORAGE_LIMIT_REGEX),
      QUEUE: validation.Optional(validation.Repeated(QueueEntry)),
  }


def LoadSingleQueue(queue_info, open_fn=None):
  """Load a queue.yaml file or string and return a QueueInfoExternal object.

  Args:
    queue_info: the contents of a queue.yaml file, as a string.
    open_fn: Function for opening files. Unused.

  Returns:
    A QueueInfoExternal object.
  """
  builder = yaml_object.ObjectBuilder(QueueInfoExternal)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)
  listener.Parse(queue_info)

  queue_info = handler.GetResults()
  if len(queue_info) < 1:
    raise MalformedQueueConfiguration('Empty queue configuration.')
  if len(queue_info) > 1:
    raise MalformedQueueConfiguration('Multiple queue: sections '
                                      'in configuration.')
  return queue_info[0]


def ParseRate(rate):
  """Parses a rate string in the form number/unit, or the literal 0.

  The unit is one of s (seconds), m (minutes), h (hours) or d (days).

  Args:
    rate: the rate string.

  Returns:
    a floating point number representing the rate/second.

  Raises:
    MalformedQueueConfiguration: if the rate is invalid
  """
  if rate == "0":
    return 0.0
  elements = rate.split('/')
  if len(elements) != 2:
    raise MalformedQueueConfiguration('Rate "%s" is invalid.' % rate)
  number, unit = elements
  try:
    number = float(number)
  except ValueError:
    raise MalformedQueueConfiguration('Rate "%s" is invalid:'
                                          ' "%s" is not a number.' %
                                          (rate, number))
  if unit not in 'smhd':
    raise MalformedQueueConfiguration('Rate "%s" is invalid:'
                                          ' "%s" is not one of s, m, h, d.' %
                                          (rate, unit))
  if unit == 's':
    return number
  if unit == 'm':
    return number/60
  if unit == 'h':
    return number/(60 * 60)
  if unit == 'd':
    return number/(24 * 60 * 60)


def ParseTotalStorageLimit(limit):
  """Parses a string representing the storage bytes limit.

  Optional limit suffixes are:
      B (bytes), K (kilobytes), M (megabytes), G (gigabytes), T (terabytes)

  Args:
    limit: The storage bytes limit string.

  Returns:
    An int representing the storage limit in bytes.

  Raises:
    MalformedQueueConfiguration: if the limit argument isn't a valid python
    double followed by an optional suffix.
  """
  limit = limit.strip()
  if not limit:
    raise MalformedQueueConfiguration('Total Storage Limit must not be empty.')
  try:
    if limit[-1] in BYTE_SUFFIXES:
      number = float(limit[0:-1])
      for c in BYTE_SUFFIXES:
        if limit[-1] != c:
          number = number * 1024
        else:
          return int(number)
    else:


      return int(limit)
  except ValueError:
    raise MalformedQueueConfiguration('Total Storage Limit "%s" is invalid.' %
                                      limit)


def ParseTaskAgeLimit(age_limit):
  """Parses a string representing the task's age limit (maximum allowed age).

  The string must be a non-negative integer or floating point number followed by
  one of s, m, h, or d (seconds, minutes, hours or days respectively).

  Args:
    age_limit: The task age limit string.

  Returns:
    An int representing the age limit in seconds.

  Raises:
    MalformedQueueConfiguration: if the limit argument isn't a valid python
    double followed by a required suffix.
 """
  age_limit = age_limit.strip()
  if not age_limit:
    raise MalformedQueueConfiguration('Task Age Limit must not be empty.')
  unit = age_limit[-1]
  if unit not in "smhd":
    raise MalformedQueueConfiguration('Task Age_Limit must be in s (seconds), '
                                      'm (minutes), h (hours) or d (days)')
  try:
    number = float(age_limit[0:-1])
    if unit == 's':
      return int(number)
    if unit == 'm':
      return int(number * 60)
    if unit == 'h':
      return int(number * 3600)
    if unit == 'd':
      return int(number * 86400)

  except ValueError:
    raise MalformedQueueConfiguration('Task Age_Limit "%s" is invalid.' %
                                      age_limit)


def TranslateRetryParameters(retry):
  """Populates a TaskQueueRetryParameters from a queueinfo.RetryParameters.

  Args:
    retry: A queueinfo.RetryParameters read from queue.yaml that describes the
        queue's retry parameters.

  Returns:
    A taskqueue_service_pb.TaskQueueRetryParameters proto populated with the
    data from "retry".

  Raises:
    MalformedQueueConfiguration: if the retry parameters are invalid.
  """
  params = taskqueue_service_pb.TaskQueueRetryParameters()
  if retry.task_retry_limit is not None:
    params.set_retry_limit(int(retry.task_retry_limit))
  if retry.task_age_limit is not None:

    params.set_age_limit_sec(ParseTaskAgeLimit(retry.task_age_limit))
  if retry.min_backoff_seconds is not None:
    params.set_min_backoff_sec(float(retry.min_backoff_seconds))
  if retry.max_backoff_seconds is not None:
    params.set_max_backoff_sec(float(retry.max_backoff_seconds))
  if retry.max_doublings is not None:
    params.set_max_doublings(int(retry.max_doublings))





  if params.has_min_backoff_sec() and not params.has_max_backoff_sec():
    if params.min_backoff_sec() > params.max_backoff_sec():
      params.set_max_backoff_sec(params.min_backoff_sec())

  if not params.has_min_backoff_sec() and params.has_max_backoff_sec():
    if params.min_backoff_sec() > params.max_backoff_sec():
      params.set_min_backoff_sec(params.max_backoff_sec())


  if params.has_retry_limit() and params.retry_limit() < 0:
    raise MalformedQueueConfiguration(
        'Task retry limit must not be less than zero.')

  if params.has_age_limit_sec() and not params.age_limit_sec() > 0:
    raise MalformedQueueConfiguration(
        'Task age limit must be greater than zero.')

  if params.has_min_backoff_sec() and params.min_backoff_sec() < 0:
    raise MalformedQueueConfiguration(
        'Min backoff seconds must not be less than zero.')

  if params.has_max_backoff_sec() and params.max_backoff_sec() < 0:
    raise MalformedQueueConfiguration(
        'Max backoff seconds must not be less than zero.')

  if params.has_max_doublings() and params.max_doublings() < 0:
    raise MalformedQueueConfiguration(
        'Max doublings must not be less than zero.')

  if (params.has_min_backoff_sec() and params.has_max_backoff_sec() and
      params.min_backoff_sec() > params.max_backoff_sec()):
    raise MalformedQueueConfiguration(
        'Min backoff sec must not be greater than than max backoff sec.')

  return params
