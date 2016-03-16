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




"""Stub version of the Task Queue API.

This stub stores tasks and runs them via dev_appserver's AddEvent capability.
It also validates the tasks by checking their queue name against the queue.yaml.

As well as implementing Task Queue API functions, the stub exposes various other
functions that are used by the dev_appserver's admin console to display the
application's queues and tasks.
"""

from __future__ import with_statement












__all__ = []

import base64
import bisect
import calendar
import datetime
import logging
import os
import random
import string
import threading
import time

import taskqueue_service_pb
import taskqueue

from google.appengine.api import api_base_pb
from google.appengine.api import apiproxy_stub
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import queueinfo
from google.appengine.api import request_info
from google.appengine.api.taskqueue import taskqueue
from google.appengine.runtime import apiproxy_errors




DEFAULT_RATE = '5.00/s'
DEFAULT_RATE_FLOAT = 5.0





DEFAULT_BUCKET_SIZE = 5


MAX_ETA = datetime.timedelta(days=30)




MAX_PULL_TASK_SIZE_BYTES = 2 ** 20

MAX_PUSH_TASK_SIZE_BYTES = 100 * (2 ** 10)

MAX_TASK_SIZE = MAX_PUSH_TASK_SIZE_BYTES


MAX_REQUEST_SIZE = 32 << 20



BUILT_IN_HEADERS = set(['x-appengine-queuename',
                        'x-appengine-taskname',
                        'x-appengine-taskexecutioncount',
                        'x-appengine-taskpreviousresponse',
                        'x-appengine-taskretrycount',
                        'x-appengine-tasketa',
                        'x-appengine-development-payload',
                        'content-length'])



DEFAULT_QUEUE_NAME = 'default'




INF = 1e500


QUEUE_MODE = taskqueue_service_pb.TaskQueueMode

AUTOMATIC_QUEUES = {
    DEFAULT_QUEUE_NAME: (0.2, DEFAULT_BUCKET_SIZE, DEFAULT_RATE),


    '__cron': (1, 1, '1/s')}


def _GetAppId(request):
  """Returns the app id to use for the given request.

  Args:
    request: A protocol buffer that has an app_id field.

  Returns:
    A string containing the app id or None if no app id was specified.
  """
  if request.has_app_id():
    return request.app_id()
  else:
    return None


def _SecToUsec(t):
  """Converts a time in seconds since the epoch to usec since the epoch.

  Args:
    t: Time in seconds since the unix epoch

  Returns:
    An integer containing the number of usec since the unix epoch.
  """
  return int(t * 1e6)


def _UsecToSec(t):
  """Converts a time in usec since the epoch to seconds since the epoch.

  Args:
    t: Time in usec since the unix epoch

  Returns:
    A float containing the number of seconds since the unix epoch.
  """
  return t / 1e6



def _FormatEta(eta_usec):
  """Formats a task ETA as a date string in UTC."""
  eta = datetime.datetime.utcfromtimestamp(_UsecToSec(eta_usec))
  return eta.strftime('%Y/%m/%d %H:%M:%S')


def _TruncDelta(timedelta):
  """Strips the microseconds field from a timedelta.

  Args:
    timedelta: a datetime.timedelta.

  Returns:
    A datetime.timedelta with the microseconds field not filled.
  """
  return datetime.timedelta(days=timedelta.days, seconds=timedelta.seconds)


def _EtaDelta(eta_usec, now):
  """Formats a task ETA as a relative time string."""
  eta = datetime.datetime.utcfromtimestamp(_UsecToSec(eta_usec))
  if eta > now:
    return '%s from now' % _TruncDelta(eta - now)
  else:
    return '%s ago' % _TruncDelta(now - eta)


def QueryTasksResponseToDict(queue_name, task_response, now):
  """Converts a TaskQueueQueryTasksResponse_Task protobuf group into a dict.

  Args:
    queue_name: The name of the queue this task came from.
    task_response: An instance of TaskQueueQueryTasksResponse_Task.
    now: A datetime.datetime object containing the current time in UTC.

  Returns:
    A dict containing the fields used by the dev appserver's admin console.

  Raises:
    ValueError: A task response contains an unknown HTTP method type.
  """
  task = {}

  task['name'] = task_response.task_name()
  task['queue_name'] = queue_name
  task['url'] = task_response.url()
  method = task_response.method()
  if method == taskqueue_service_pb.TaskQueueQueryTasksResponse_Task.GET:
    task['method'] = 'GET'
  elif method == taskqueue_service_pb.TaskQueueQueryTasksResponse_Task.POST:
    task['method'] = 'POST'
  elif method == taskqueue_service_pb.TaskQueueQueryTasksResponse_Task.HEAD:
    task['method'] = 'HEAD'
  elif method == taskqueue_service_pb.TaskQueueQueryTasksResponse_Task.PUT:
    task['method'] = 'PUT'
  elif method == taskqueue_service_pb.TaskQueueQueryTasksResponse_Task.DELETE:
    task['method'] = 'DELETE'
  else:
    raise ValueError('Unexpected method: %d' % method)

  task['eta'] = _FormatEta(task_response.eta_usec())
  task['eta_usec'] = task_response.eta_usec()
  task['eta_delta'] = _EtaDelta(task_response.eta_usec(), now)
  task['body'] = base64.b64encode(task_response.body())



  headers = [(header.key(), header.value())
             for header in task_response.header_list()
             if header.key().lower() not in BUILT_IN_HEADERS]


  headers.append(('X-AppEngine-QueueName', queue_name))
  headers.append(('X-AppEngine-TaskName', task_response.task_name()))
  headers.append(('X-AppEngine-TaskRetryCount',
                  str(task_response.retry_count())))
  headers.append(('X-AppEngine-TaskETA',
                  str(_UsecToSec(task_response.eta_usec()))))
  headers.append(('X-AppEngine-Development-Payload', '1'))
  headers.append(('Content-Length', str(len(task['body']))))
  if 'content-type' not in frozenset(key.lower() for key, _ in headers):
    headers.append(('Content-Type', 'application/octet-stream'))
  headers.append(('X-AppEngine-TaskExecutionCount',
                  str(task_response.execution_count())))
  if task_response.has_runlog() and task_response.runlog().has_response_code():
    headers.append(('X-AppEngine-TaskPreviousResponse',
                    str(task_response.runlog().response_code())))
  task['headers'] = headers

  return task


class _Group(object):
  """A taskqueue group.

  This class contains all of the queues for an application.
  """

  def __init__(self, queue_yaml_parser=None, app_id=None,
               _all_queues_valid=False, _update_newest_eta=None,
               _testing_validate_state=False):
    """Constructor.

    Args:
      queue_yaml_parser: A function that takes no parameters and returns the
          parsed results of the queue.yaml file. If this queue is not based on a
          queue.yaml file use None.
      app_id: The app id this Group is representing or None if it is the
          currently running application.
      _all_queues_valid: Automatically generate queues on first access.
      _update_newest_eta: Callable for automatically executing tasks.
          Takes the ETA of the task in seconds since the epoch, the queue_name
          and a task name. May be None if automatic task running is disabled.
      _testing_validate_state: Should this _Group and all of its _Queues
          validate their state after each operation? This should only be used
          during testing of the taskqueue_stub.
    """


    self._queues = {}
    self._queue_yaml_parser = queue_yaml_parser
    self._all_queues_valid = _all_queues_valid
    self._next_task_id = 1
    self._app_id = app_id
    if _update_newest_eta is None:
      self._update_newest_eta = lambda x: None
    else:
      self._update_newest_eta = _update_newest_eta
    self._testing_validate_state = _testing_validate_state




  def GetQueuesAsDicts(self):
    """Gets all the applications's queues.

    Returns:
      A list of dictionaries, where each dictionary contains one queue's
      attributes. E.g.:
        [{'name': 'some-queue',
          'max_rate': '1/s',
          'bucket_size': 5,
          'oldest_task': '2009/02/02 05:37:42',
          'eta_delta': '0:00:06.342511 ago',
          'tasks_in_queue': 12,
          'acl': ['user1@gmail.com']}, ...]
      The list of queues always includes the default queue.
    """
    self._ReloadQueuesFromYaml()
    now = datetime.datetime.utcnow()

    queues = []
    for queue_name, queue in sorted(self._queues.items()):
      queue_dict = {}
      queues.append(queue_dict)

      queue_dict['name'] = queue_name
      queue_dict['bucket_size'] = queue.bucket_capacity
      if queue.user_specified_rate is not None:
        queue_dict['max_rate'] = queue.user_specified_rate
      else:
        queue_dict['max_rate'] = ''
      if queue.queue_mode == QUEUE_MODE.PULL:
        queue_dict['mode'] = 'pull'
      else:
        queue_dict['mode'] = 'push'
      queue_dict['acl'] = queue.acl


      oldest_eta = queue.Oldest()
      if oldest_eta:
        queue_dict['oldest_task'] = _FormatEta(oldest_eta)
        queue_dict['eta_delta'] = _EtaDelta(oldest_eta, now)
      else:
        queue_dict['oldest_task'] = ''
        queue_dict['eta_delta'] = ''
      queue_dict['tasks_in_queue'] = queue.Count()

      if queue.retry_parameters:
        retry_proto = queue.retry_parameters
        retry_dict = {}

        if retry_proto.has_retry_limit():
          retry_dict['retry_limit'] = retry_proto.retry_limit()
        if retry_proto.has_age_limit_sec():
          retry_dict['age_limit_sec'] = retry_proto.age_limit_sec()
        if retry_proto.has_min_backoff_sec():
          retry_dict['min_backoff_sec'] = retry_proto.min_backoff_sec()
        if retry_proto.has_max_backoff_sec():
          retry_dict['max_backoff_sec'] = retry_proto.max_backoff_sec()
        if retry_proto.has_max_doublings():
          retry_dict['max_doublings'] = retry_proto.max_doublings()

        queue_dict['retry_parameters'] = retry_dict
    return queues

  def HasQueue(self, queue_name):
    """Check if the specified queue_name references a valid queue.

    Args:
      queue_name: The name of the queue to check.

    Returns:
      True if the queue exists, False otherwise.
    """
    self._ReloadQueuesFromYaml()
    return queue_name in self._queues and (
        self._queues[queue_name] is not None)

  def GetQueue(self, queue_name):
    """Gets the _Queue instance for the specified queue.

    Args:
      queue_name: The name of the queue to fetch.

    Returns:
      The _Queue instance for the specified queue.

    Raises:
      KeyError if the queue does not exist.
    """
    self._ReloadQueuesFromYaml()
    return self._queues[queue_name]

  def GetNextPushTask(self):
    """Finds the task with the lowest eta.

    Returns:
      A tuple containing the queue and task instance for the task with the
      lowest eta, or (None, None) if there are no tasks.
    """
    min_eta = INF
    result = None, None


    for queue in self._queues.itervalues():
      if queue.queue_mode == QUEUE_MODE.PULL:
        continue
      task = queue.OldestTask()
      if not task:
        continue
      if task.eta_usec() < min_eta:
        result = queue, task
        min_eta = task.eta_usec()
    return result

  def _ConstructQueue(self, queue_name, *args, **kwargs):
    if '_testing_validate_state' in kwargs:
      raise TypeError(
          '_testing_validate_state should not be passed to _ConstructQueue')
    kwargs['_testing_validate_state'] = self._testing_validate_state
    self._queues[queue_name] = _Queue(queue_name, *args, **kwargs)

  def _ConstructAutomaticQueue(self, queue_name):
    if queue_name in AUTOMATIC_QUEUES:
      self._ConstructQueue(queue_name, *AUTOMATIC_QUEUES[queue_name])
    else:


      assert self._all_queues_valid
      self._ConstructQueue(queue_name)

  def _ReloadQueuesFromYaml(self):
    """Update the queue map with the contents of the queue.yaml file.

    This function will remove queues that no longer exist in the queue.yaml
    file.

    If no queue yaml parser has been defined, this function is a no-op.
    """
    if not self._queue_yaml_parser:
      return

    queue_info = self._queue_yaml_parser()

    if queue_info and queue_info.queue:
      queues = queue_info.queue
    else:
      queues = []

    old_queues = set(self._queues)
    new_queues = set()

    for entry in queues:
      queue_name = entry.name
      new_queues.add(queue_name)

      retry_parameters = None


      if entry.bucket_size:
        bucket_size = entry.bucket_size
      else:
        bucket_size = DEFAULT_BUCKET_SIZE
      if entry.retry_parameters:
        retry_parameters = queueinfo.TranslateRetryParameters(
            entry.retry_parameters)

      if entry.mode == 'pull':
        mode = QUEUE_MODE.PULL
        if entry.rate is not None:
          logging.warning(
              'Refill rate must not be specified for pull-based queue. '
              'Please check queue.yaml file.')
      else:
        mode = QUEUE_MODE.PUSH
        if entry.rate is None:
          logging.warning(
              'Refill rate must be specified for push-based queue. '
              'Please check queue.yaml file.')
      max_rate = entry.rate

      if entry.acl is not None:
        acl = taskqueue_service_pb.TaskQueueAcl()
        for acl_entry in entry.acl:
          acl.add_user_email(acl_entry.user_email)
      else:
        acl = None

      if self._queues.get(queue_name) is None:

        self._ConstructQueue(queue_name, bucket_capacity=bucket_size,
                             user_specified_rate=max_rate, queue_mode=mode,
                             acl=acl, retry_parameters=retry_parameters,
                             target=entry.target)
      else:


        queue = self._queues[queue_name]
        queue.bucket_size = bucket_size
        queue.user_specified_rate = max_rate
        queue.acl = acl
        queue.queue_mode = mode
        queue.retry_parameters = retry_parameters
        if mode == QUEUE_MODE.PUSH:
          eta = queue.Oldest()
          if eta:
            self._update_newest_eta(_UsecToSec(eta))

    if DEFAULT_QUEUE_NAME not in self._queues:
      self._ConstructAutomaticQueue(DEFAULT_QUEUE_NAME)


    new_queues.add(DEFAULT_QUEUE_NAME)
    if not self._all_queues_valid:

      for queue_name in old_queues - new_queues:



        del self._queues[queue_name]




  def _ValidateQueueName(self, queue_name):
    """Tests if the specified queue exists and creates it if needed.

    This function replicates the behaviour of the taskqueue service by
    automatically creating the 'automatic' queues when they are first accessed.

    Args:
      queue_name: The name queue of the queue to check.

    Returns:
      If there are no problems, returns TaskQueueServiceError.OK. Otherwise
          returns the correct constant from TaskQueueServiceError.
    """
    if not queue_name:
      return taskqueue_service_pb.TaskQueueServiceError.INVALID_QUEUE_NAME
    elif queue_name not in self._queues:
      if queue_name in AUTOMATIC_QUEUES or self._all_queues_valid:

        self._ConstructAutomaticQueue(queue_name)
      else:
        return taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_QUEUE
    elif self._queues[queue_name] is None:
      return taskqueue_service_pb.TaskQueueServiceError.TOMBSTONED_QUEUE

    return taskqueue_service_pb.TaskQueueServiceError.OK

  def _CheckQueueForRpc(self, queue_name):
    """Ensures the specified queue exists and creates it if needed.

    This function replicates the behaviour of the taskqueue service by
    automatically creating the 'automatic' queues when they are first accessed.

    Args:
      queue_name: The name queue of the queue to check

    Raises:
      ApplicationError: If the queue name is invalid, tombstoned or does not
          exist.
    """
    self._ReloadQueuesFromYaml()

    response = self._ValidateQueueName(queue_name)
    if response != taskqueue_service_pb.TaskQueueServiceError.OK:
      raise apiproxy_errors.ApplicationError(response)

  def _ChooseTaskName(self):
    """Returns a string containing a unique task name."""




    self._next_task_id += 1
    return 'task%d' % (self._next_task_id - 1)

  def _VerifyTaskQueueAddRequest(self, request, now):
    """Checks that a TaskQueueAddRequest is valid.

    Checks that a TaskQueueAddRequest specifies a valid eta and a valid queue.

    Args:
      request: The taskqueue_service_pb.TaskQueueAddRequest to validate.
      now: A datetime.datetime object containing the current time in UTC.

    Returns:
      A taskqueue_service_pb.TaskQueueServiceError indicating any problems with
      the request or taskqueue_service_pb.TaskQueueServiceError.OK if it is
      valid.
    """
    if request.eta_usec() < 0:
      return taskqueue_service_pb.TaskQueueServiceError.INVALID_ETA

    eta = datetime.datetime.utcfromtimestamp(_UsecToSec(request.eta_usec()))
    max_eta = now + MAX_ETA
    if eta > max_eta:
      return taskqueue_service_pb.TaskQueueServiceError.INVALID_ETA


    queue_name_response = self._ValidateQueueName(request.queue_name())
    if queue_name_response != taskqueue_service_pb.TaskQueueServiceError.OK:
      return queue_name_response


    if request.has_crontimetable() and self._app_id is None:
      return taskqueue_service_pb.TaskQueueServiceError.PERMISSION_DENIED

    if request.mode() == QUEUE_MODE.PULL:
      max_task_size_bytes = MAX_PULL_TASK_SIZE_BYTES
    else:
      max_task_size_bytes = MAX_PUSH_TASK_SIZE_BYTES

    if request.ByteSize() > max_task_size_bytes:
      return taskqueue_service_pb.TaskQueueServiceError.TASK_TOO_LARGE

    return taskqueue_service_pb.TaskQueueServiceError.OK




  def BulkAdd_Rpc(self, request, response):
    """Add many tasks to a queue using a single request.

    Args:
      request: The taskqueue_service_pb.TaskQueueBulkAddRequest. See
          taskqueue_service.proto.
      response: The taskqueue_service_pb.TaskQueueBulkAddResponse. See
          taskqueue_service.proto.
    """
    self._ReloadQueuesFromYaml()


    if not request.add_request(0).queue_name():
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_QUEUE)

    error_found = False
    task_results_with_chosen_names = set()
    now = datetime.datetime.utcfromtimestamp(time.time())


    for add_request in request.add_request_list():
      task_result = response.add_taskresult()
      result = self._VerifyTaskQueueAddRequest(add_request, now)
      if result == taskqueue_service_pb.TaskQueueServiceError.OK:
        if not add_request.task_name():
          chosen_name = self._ChooseTaskName()
          add_request.set_task_name(chosen_name)
          task_results_with_chosen_names.add(id(task_result))



        task_result.set_result(
            taskqueue_service_pb.TaskQueueServiceError.SKIPPED)
      else:
        error_found = True
        task_result.set_result(result)

    if error_found:
      return


    if (request.add_request(0).has_transaction()
        or request.add_request(0).has_datastore_transaction()):
      self._TransactionalBulkAdd(request)
    else:
      self._NonTransactionalBulkAdd(request, response, now)


    for add_request, task_result in zip(request.add_request_list(),
                                        response.taskresult_list()):
      if (task_result.result() ==
          taskqueue_service_pb.TaskQueueServiceError.SKIPPED):
        task_result.set_result(taskqueue_service_pb.TaskQueueServiceError.OK)
      if id(task_result) in task_results_with_chosen_names:
        task_result.set_chosen_task_name(add_request.task_name())

  def _TransactionalBulkAdd(self, request):
    """Uses datastore.AddActions to associate tasks with a transaction.

    Args:
      request: The taskqueue_service_pb.TaskQueueBulkAddRequest containing the
        tasks to add. N.B. all tasks in the request have been validated and
        assigned unique names.
    """
    try:



      apiproxy_stub_map.MakeSyncCall(
          'datastore_v3', 'AddActions', request, api_base_pb.VoidProto())
    except apiproxy_errors.ApplicationError, e:
      raise apiproxy_errors.ApplicationError(
          e.application_error +
          taskqueue_service_pb.TaskQueueServiceError.DATASTORE_ERROR,
          e.error_detail)

  def _NonTransactionalBulkAdd(self, request, response, now):
    """Adds tasks to the appropriate _Queue instance.

    Args:
      request: The taskqueue_service_pb.TaskQueueBulkAddRequest containing the
        tasks to add. N.B. all tasks in the request have been validated and
        those with empty names have been assigned unique names.
      response: The taskqueue_service_pb.TaskQueueBulkAddResponse to populate
        with the results. N.B. the chosen_task_name field in the response will
        not be filled-in.
      now: A datetime.datetime object containing the current time in UTC.
    """
    queue_mode = request.add_request(0).mode()


    queue_name = request.add_request(0).queue_name()
    store = self._queues[queue_name]
    if store.queue_mode != queue_mode:
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.INVALID_QUEUE_MODE)

    for add_request, task_result in zip(request.add_request_list(),
                                        response.taskresult_list()):
      try:
        store.Add(add_request, now)
      except apiproxy_errors.ApplicationError, e:
        task_result.set_result(e.application_error)
      else:
        task_result.set_result(taskqueue_service_pb.TaskQueueServiceError.OK)
        if (store.queue_mode == QUEUE_MODE.PUSH and
            store.Oldest() == add_request.eta_usec()):
          self._update_newest_eta(_UsecToSec(add_request.eta_usec()))

  def UpdateQueue_Rpc(self, request, response):
    """Implementation of the UpdateQueue RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueUpdateQueueRequest.
      response: A taskqueue_service_pb.TaskQueueUpdateQueueResponse.
    """
    queue_name = request.queue_name()

    response = self._ValidateQueueName(queue_name)

    is_unknown_queue = (
        response == taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_QUEUE)
    if response != taskqueue_service_pb.TaskQueueServiceError.OK and (
        not is_unknown_queue):
      raise apiproxy_errors.ApplicationError(response)

    if is_unknown_queue:
      self._queues[queue_name] = _Queue(request.queue_name())



      if self._app_id is not None:
        self._queues[queue_name].Populate(random.randint(10, 100))
    self._queues[queue_name].UpdateQueue_Rpc(request, response)

  def FetchQueues_Rpc(self, request, response):
    """Implementation of the FetchQueues RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueFetchQueuesRequest.
      response: A taskqueue_service_pb.TaskQueueFetchQueuesResponse.
    """
    self._ReloadQueuesFromYaml()
    for queue_name in sorted(self._queues):
      if response.queue_size() > request.max_rows():
        break


      if self._queues[queue_name] is None:
        continue


      self._queues[queue_name].FetchQueues_Rpc(request, response)

  def FetchQueueStats_Rpc(self, request, response):
    """Implementation of the FetchQueueStats rpc which returns 'random' data.

    This implementation loads some stats from the task store, the rest are
    random numbers.

    Args:
      request: A taskqueue_service_pb.TaskQueueFetchQueueStatsRequest.
      response: A taskqueue_service_pb.TaskQueueFetchQueueStatsResponse.
    """
    for queue_name in request.queue_name_list():
      stats = response.add_queuestats()
      if queue_name not in self._queues:

        stats.set_num_tasks(0)
        stats.set_oldest_eta_usec(-1)
        continue
      store = self._queues[queue_name]

      stats.set_num_tasks(store.Count())
      if stats.num_tasks() == 0:
        stats.set_oldest_eta_usec(-1)
      else:
        stats.set_oldest_eta_usec(store.Oldest())


      if random.randint(0, 9) > 0:
        scanner_info = stats.mutable_scanner_info()
        scanner_info.set_executed_last_minute(random.randint(0, 10))
        scanner_info.set_executed_last_hour(scanner_info.executed_last_minute()
                                            + random.randint(0, 100))
        scanner_info.set_sampling_duration_seconds(random.random() * 10000.0)
        scanner_info.set_requests_in_flight(random.randint(0, 10))

  def QueryTasks_Rpc(self, request, response):
    """Implementation of the QueryTasks RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueQueryTasksRequest.
      response: A taskqueue_service_pb.TaskQueueQueryTasksResponse.
    """
    self._CheckQueueForRpc(request.queue_name())
    self._queues[request.queue_name()].QueryTasks_Rpc(request, response)

  def FetchTask_Rpc(self, request, response):
    """Implementation of the FetchTask RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueFetchTaskRequest.
      response: A taskqueue_service_pb.TaskQueueFetchTaskResponse.
    """
    self._ReloadQueuesFromYaml()

    self._CheckQueueForRpc(request.queue_name())
    self._queues[request.queue_name()].FetchTask_Rpc(request, response)

  def Delete_Rpc(self, request, response):
    """Implementation of the Delete RPC.

    Deletes tasks from the task store.

    Args:
      request: A taskqueue_service_pb.TaskQueueDeleteRequest.
      response: A taskqueue_service_pb.TaskQueueDeleteResponse.
    """
    self._ReloadQueuesFromYaml()

    def _AddResultForAll(result):
      for _ in request.task_name_list():
        response.add_result(result)
    if request.queue_name() not in self._queues:
      _AddResultForAll(taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_QUEUE)
    elif self._queues[request.queue_name()] is None:
      _AddResultForAll(
          taskqueue_service_pb.TaskQueueServiceError.TOMBSTONED_QUEUE)
    else:
      self._queues[request.queue_name()].Delete_Rpc(request, response)

  def DeleteQueue_Rpc(self, request, response):
    """Implementation of the DeleteQueue RPC.

    Tombstones the queue.

    Args:
      request: A taskqueue_service_pb.TaskQueueDeleteQueueRequest.
      response: A taskqueue_service_pb.TaskQueueDeleteQueueResponse.
    """
    self._CheckQueueForRpc(request.queue_name())


    self._queues[request.queue_name()] = None

  def PauseQueue_Rpc(self, request, response):
    """Implementation of the PauseQueue RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueuePauseQueueRequest.
      response: A taskqueue_service_pb.TaskQueuePauseQueueResponse.
    """
    self._CheckQueueForRpc(request.queue_name())
    self._queues[request.queue_name()].paused = request.pause()

  def PurgeQueue_Rpc(self, request, response):
    """Implementation of the PurgeQueue RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueuePurgeQueueRequest.
      response: A taskqueue_service_pb.TaskQueuePurgeQueueResponse.
    """
    self._CheckQueueForRpc(request.queue_name())
    self._queues[request.queue_name()].PurgeQueue()

  def QueryAndOwnTasks_Rpc(self, request, response):
    """Implementation of the QueryAndOwnTasks RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueQueryAndOwnTasksRequest.
      response: A taskqueue_service_pb.TaskQueueQueryAndOwnTasksResponse.
    """
    self._CheckQueueForRpc(request.queue_name())



    self._queues[request.queue_name()].QueryAndOwnTasks_Rpc(request, response)

  def ModifyTaskLease_Rpc(self, request, response):
    """Implementation of the ModifyTaskLease RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueModifyTaskLeaseRequest.
      response: A taskqueue_service_pb.TaskQueueModifyTaskLeaseResponse.
    """
    self._CheckQueueForRpc(request.queue_name())
    self._queues[request.queue_name()].ModifyTaskLease_Rpc(request, response)


class Retry(object):
  """Task retry caclulator class.

  Determines if and when a task should next be run
  """



  _default_params = taskqueue_service_pb.TaskQueueRetryParameters()

  def __init__(self, task, queue):
    """Constructor.

    Args:
      task: A taskqueue_service_pb.TaskQueueQueryTasksResponse_Task instance.
          May be None.
      queue: A _Queue instance. May be None.
    """
    if task is not None and task.has_retry_parameters():
      self._params = task.retry_parameters()
    elif queue is not None and queue.retry_parameters is not None:
      self._params = queue.retry_parameters
    else:
      self._params = self._default_params

  def CanRetry(self, retry_count, age_usec):
    """Computes whether a task can be retried.

    Args:
      retry_count: An integer specifying which retry this is.
      age_usec: An integer specifying the microseconds since the first try.

    Returns:
     True if a task is eligible for retrying.
    """
    if self._params.has_retry_limit() and self._params.has_age_limit_sec():
      return (self._params.retry_limit() >= retry_count or
              self._params.age_limit_sec() >= _UsecToSec(age_usec))

    if self._params.has_retry_limit():
      return self._params.retry_limit() >= retry_count

    if self._params.has_age_limit_sec():
      return self._params.age_limit_sec() >= _UsecToSec(age_usec)

    return True

  def CalculateBackoffUsec(self, retry_count):
    """Calculates time before the specified retry.

    Args:
      retry_count: An integer specifying which retry this is.

    Returns:
      The number of microseconds before a task should be retried.
    """
    exponent = min(retry_count - 1, self._params.max_doublings())
    linear_steps = retry_count - exponent
    min_backoff_usec = _SecToUsec(self._params.min_backoff_sec())
    max_backoff_usec = _SecToUsec(self._params.max_backoff_sec())
    backoff_usec = min_backoff_usec
    if exponent > 0:
      backoff_usec *= (2 ** (min(1023, exponent)))
    if linear_steps > 1:
      backoff_usec *= linear_steps

    return int(min(max_backoff_usec, backoff_usec))


class _Queue(object):
  """A Taskqueue Queue.

  This class contains all of the properties of a queue and a sorted list of
  tasks.
  """

  def __init__(self, queue_name, bucket_refill_per_second=DEFAULT_RATE_FLOAT,
               bucket_capacity=DEFAULT_BUCKET_SIZE,
               user_specified_rate=DEFAULT_RATE, retry_parameters=None,
               max_concurrent_requests=None, paused=False,
               queue_mode=QUEUE_MODE.PUSH, acl=None,
               _testing_validate_state=None, target=None):

    self.queue_name = queue_name
    self.bucket_refill_per_second = bucket_refill_per_second
    self.bucket_capacity = bucket_capacity
    self.user_specified_rate = user_specified_rate
    self.retry_parameters = retry_parameters
    self.max_concurrent_requests = max_concurrent_requests
    self.paused = paused
    self.queue_mode = queue_mode
    self.acl = acl
    self.target = target
    self._testing_validate_state = _testing_validate_state


    self.task_name_archive = set()

    self._sorted_by_name = []

    self._sorted_by_eta = []

    self._sorted_by_tag = []


    self._lock = threading.Lock()

  def VerifyIndexes(self):
    """Ensures that all three indexes are in a valid state.

    This method is used by internal tests and should not need to be called in
    any other circumstances.

    Raises:
      AssertionError: if the indexes are not in a valid state.
    """
    assert self._IsInOrder(self._sorted_by_name)
    assert self._IsInOrder(self._sorted_by_eta)
    assert self._IsInOrder(self._sorted_by_tag)

    tasks_by_name = set()
    tasks_with_tags = set()
    for name, task in self._sorted_by_name:
      assert name == task.task_name()
      assert name not in tasks_by_name
      tasks_by_name.add(name)
      if task.has_tag():
        tasks_with_tags.add(name)

    tasks_by_eta = set()
    for eta, name, task in self._sorted_by_eta:
      assert name == task.task_name()
      assert eta == task.eta_usec()
      assert name not in tasks_by_eta
      tasks_by_eta.add(name)

    assert tasks_by_eta == tasks_by_name

    tasks_by_tag = set()
    for tag, eta, name, task in self._sorted_by_tag:
      assert name == task.task_name()
      assert eta == task.eta_usec()
      assert task.has_tag() and task.tag()
      assert tag == task.tag()
      assert name not in tasks_by_tag
      tasks_by_tag.add(name)
    assert tasks_by_tag == tasks_with_tags

  @staticmethod
  def _IsInOrder(l):
    """Determine if the specified list is in ascending order.

    Args:
      l: The list to check

    Returns:
      True if the list is in order, False otherwise
    """
    sorted_list = sorted(l)
    return l == sorted_list

  def _WithLock(f):
    """Runs the decorated function within self._lock.

    Args:
      f: The function to be delegated to. Must be a member function (take self
          as the first parameter).

    Returns:
      The result of f.
    """

    def _Inner(self, *args, **kwargs):
      with self._lock:
        ret = f(self, *args, **kwargs)
        if self._testing_validate_state:
          self.VerifyIndexes()
        return ret
    _Inner.__doc__ = f.__doc__
    return _Inner




  @_WithLock
  def UpdateQueue_Rpc(self, request, response):
    """Implementation of the UpdateQueue RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueUpdateQueueRequest.
      response: A taskqueue_service_pb.TaskQueueUpdateQueueResponse.
    """
    assert request.queue_name() == self.queue_name



    self.bucket_refill_per_second = request.bucket_refill_per_second()
    self.bucket_capacity = request.bucket_capacity()
    if request.has_user_specified_rate():
      self.user_specified_rate = request.user_specified_rate()
    else:
      self.user_specified_rate = None
    if request.has_retry_parameters():
      self.retry_parameters = request.retry_parameters()
    else:
      self.retry_parameters = None
    if request.has_max_concurrent_requests():
      self.max_concurrent_requests = request.max_concurrent_requests()
    else:
      self.max_concurrent_requests = None
    self.queue_mode = request.mode()
    if request.has_acl():
      self.acl = request.acl()
    else:
      self.acl = None

  @_WithLock
  def FetchQueues_Rpc(self, request, response):
    """Fills out a queue message on the provided TaskQueueFetchQueuesResponse.

    Args:
      request: A taskqueue_service_pb.TaskQueueFetchQueuesRequest.
      response: A taskqueue_service_pb.TaskQueueFetchQueuesResponse.
    """
    response_queue = response.add_queue()

    response_queue.set_queue_name(self.queue_name)
    response_queue.set_bucket_refill_per_second(
        self.bucket_refill_per_second)
    response_queue.set_bucket_capacity(self.bucket_capacity)
    if self.user_specified_rate is not None:
      response_queue.set_user_specified_rate(self.user_specified_rate)
    if self.max_concurrent_requests is not None:
      response_queue.set_max_concurrent_requests(
          self.max_concurrent_requests)
    if self.retry_parameters is not None:
      response_queue.retry_parameters().CopyFrom(self.retry_parameters)
    response_queue.set_paused(self.paused)
    if self.queue_mode is not None:
      response_queue.set_mode(self.queue_mode)
    if self.acl is not None:
      response_queue.mutable_acl().CopyFrom(self.acl)

  @_WithLock
  def QueryTasks_Rpc(self, request, response):
    """Implementation of the QueryTasks RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueQueryTasksRequest.
      response: A taskqueue_service_pb.TaskQueueQueryTasksResponse.
    """

    assert not request.has_start_tag()

    if request.has_start_eta_usec():
      tasks = self._LookupNoAcquireLock(request.max_rows(),
                                        name=request.start_task_name(),
                                        eta=request.start_eta_usec())
    else:
      tasks = self._LookupNoAcquireLock(request.max_rows(),
                                        name=request.start_task_name())
    for task in tasks:
      response.add_task().MergeFrom(task)

  @_WithLock
  def FetchTask_Rpc(self, request, response):
    """Implementation of the FetchTask RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueFetchTaskRequest.
      response: A taskqueue_service_pb.TaskQueueFetchTaskResponse.
    """
    task_name = request.task_name()
    pos = self._LocateTaskByName(task_name)
    if pos is None:
      if task_name in self.task_name_archive:
        error = taskqueue_service_pb.TaskQueueServiceError.TOMBSTONED_TASK
      else:
        error = taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_TASK
      raise apiproxy_errors.ApplicationError(error)

    _, task = self._sorted_by_name[pos]
    response.mutable_task().add_task().CopyFrom(task)

  @_WithLock
  def Delete_Rpc(self, request, response):
    """Implementation of the Delete RPC.

    Deletes tasks from the task store. We mimic a 1/20 chance of a
    TRANSIENT_ERROR when the request has an app_id.

    Args:
      request: A taskqueue_service_pb.TaskQueueDeleteRequest.
      response: A taskqueue_service_pb.TaskQueueDeleteResponse.
    """
    for taskname in request.task_name_list():
      if request.has_app_id() and random.random() <= 0.05:
        response.add_result(
            taskqueue_service_pb.TaskQueueServiceError.TRANSIENT_ERROR)
      else:
        response.add_result(self._DeleteNoAcquireLock(taskname))

  def _QueryAndOwnTasksGetTaskList(self, max_rows, group_by_tag, now_eta_usec,
                                   tag=None):
    assert self._lock.locked()
    if group_by_tag and tag:

      return self._IndexScan(self._sorted_by_tag,
                             start_key=(tag, None, None,),
                             end_key=(tag, now_eta_usec, None,),
                             max_rows=max_rows)
    elif group_by_tag:

      tasks = self._IndexScan(self._sorted_by_eta,
                              start_key=(None, None,),
                              end_key=(now_eta_usec, None,),
                              max_rows=max_rows)
      if not tasks:
        return []

      if tasks[0].has_tag():
        tag = tasks[0].tag()
        return self._QueryAndOwnTasksGetTaskList(
            max_rows, True, now_eta_usec, tag)
      else:

        return [task for task in tasks if not task.has_tag()]
    else:
      return self._IndexScan(self._sorted_by_eta,
                             start_key=(None, None,),
                             end_key=(now_eta_usec, None,),
                             max_rows=max_rows)

  @_WithLock
  def QueryAndOwnTasks_Rpc(self, request, response):
    """Implementation of the QueryAndOwnTasks RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueQueryAndOwnTasksRequest.
      response: A taskqueue_service_pb.TaskQueueQueryAndOwnTasksResponse.
    """
    if self.queue_mode != QUEUE_MODE.PULL:
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.INVALID_QUEUE_MODE)


    lease_seconds = request.lease_seconds()
    if lease_seconds < 0:
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.INVALID_REQUEST)
    max_tasks = request.max_tasks()
    if max_tasks <= 0:
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.INVALID_REQUEST)


    if request.has_tag() and not request.group_by_tag():
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.INVALID_REQUEST,
          'Tag specified, but group_by_tag was not.')

    now_eta_usec = _SecToUsec(time.time())
    tasks = self._QueryAndOwnTasksGetTaskList(
        max_tasks, request.group_by_tag(), now_eta_usec, request.tag())

    tasks_to_delete = []
    for task in tasks:
      retry = Retry(task, self)
      if not retry.CanRetry(task.retry_count() + 1, 0):
        logging.warning(
            'Task %s in queue %s cannot be leased again after %d leases.',
            task.task_name(), self.queue_name, task.retry_count())
        tasks_to_delete.append(task)
        continue

      self._PostponeTaskNoAcquireLock(
          task, now_eta_usec + _SecToUsec(lease_seconds))


      task_response = response.add_task()
      task_response.set_task_name(task.task_name())
      task_response.set_eta_usec(task.eta_usec())
      task_response.set_retry_count(task.retry_count())
      if task.has_tag():
        task_response.set_tag(task.tag())



      task_response.set_body(task.body())


    for task in tasks_to_delete:
      self._DeleteNoAcquireLock(task.task_name())

  @_WithLock
  def ModifyTaskLease_Rpc(self, request, response):
    """Implementation of the ModifyTaskLease RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueQueryAndOwnTasksRequest.
      response: A taskqueue_service_pb.TaskQueueQueryAndOwnTasksResponse.
    """
    if self.queue_mode != QUEUE_MODE.PULL:
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.INVALID_QUEUE_MODE)

    if self.paused:
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.QUEUE_PAUSED)


    lease_seconds = request.lease_seconds()
    if lease_seconds < 0:
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.INVALID_REQUEST)

    pos = self._LocateTaskByName(request.task_name())
    if pos is None:
      if request.task_name() in self.task_name_archive:
        raise apiproxy_errors.ApplicationError(
            taskqueue_service_pb.TaskQueueServiceError.TOMBSTONED_TASK)
      else:
        raise apiproxy_errors.ApplicationError(
            taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_TASK)


    _, task = self._sorted_by_name[pos]
    if task.eta_usec() != request.eta_usec():
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.TASK_LEASE_EXPIRED)

    now_usec = _SecToUsec(time.time())

    if task.eta_usec() < now_usec:
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.TASK_LEASE_EXPIRED)


    future_eta_usec = now_usec + _SecToUsec(lease_seconds)
    self._PostponeTaskNoAcquireLock(
        task, future_eta_usec, increase_retries=False)
    response.set_updated_eta_usec(future_eta_usec)

  @_WithLock
  def IncRetryCount(self, task_name):
    """Increment the retry count of a task by 1.

    Args:
      task_name: The name of the task to update.
    """
    pos = self._LocateTaskByName(task_name)
    assert pos is not None, (
        'Task does not exist when trying to increase retry count.')

    task = self._sorted_by_name[pos][1]
    self._IncRetryCount(task)

  def _IncRetryCount(self, task):
    assert self._lock.locked()
    retry_count = task.retry_count()
    task.set_retry_count(retry_count + 1)

    task.set_execution_count(task.execution_count() + 1)




  @_WithLock
  def GetTasksAsDicts(self):
    """Gets all of the tasks in this queue.

    Returns:
      A list of dictionaries, where each dictionary contains one task's
      attributes. E.g.
        [{'name': 'task-123',
          'queue_name': 'default',
          'url': '/update',
          'method': 'GET',
          'eta': '2009/02/02 05:37:42',
          'eta_delta': '0:00:06.342511 ago',
          'body': '',
          'headers': [('user-header', 'some-value')
                      ('X-AppEngine-QueueName': 'update-queue'),
                      ('X-AppEngine-TaskName': 'task-123'),
                      ('X-AppEngine-TaskExecutionCount': '1'),
                      ('X-AppEngine-TaskRetryCount': '1'),
                      ('X-AppEngine-TaskETA': '1234567890.123456'),
                      ('X-AppEngine-Development-Payload': '1'),
                      ('X-AppEngine-TaskPreviousResponse': '300'),
                      ('Content-Length': 0),
                      ('Content-Type': 'application/octet-stream')]

    Raises:
      ValueError: A task request contains an unknown HTTP method type.
    """
    tasks = []
    now = datetime.datetime.utcnow()

    for _, _, task_response in self._sorted_by_eta:
      tasks.append(QueryTasksResponseToDict(
          self.queue_name, task_response, now))
    return tasks

  @_WithLock
  def GetTaskAsDict(self, task_name):
    """Gets a specific task from this queue.

    Returns:
      A dictionary containing one task's attributes. E.g.
        [{'name': 'task-123',
          'queue_name': 'default',
          'url': '/update',
          'method': 'GET',
          'eta': '2009/02/02 05:37:42',
          'eta_delta': '0:00:06.342511 ago',
          'body': '',
          'headers': [('user-header', 'some-value')
                      ('X-AppEngine-QueueName': 'update-queue'),
                      ('X-AppEngine-TaskName': 'task-123'),
                      ('X-AppEngine-TaskExecutionCount': '1'),
                      ('X-AppEngine-TaskRetryCount': '1'),
                      ('X-AppEngine-TaskETA': '1234567890.123456'),
                      ('X-AppEngine-Development-Payload': '1'),
                      ('X-AppEngine-TaskPreviousResponse': '300'),
                      ('Content-Length': 0),
                      ('Content-Type': 'application/octet-stream')]

    Raises:
      ValueError: A task request contains an unknown HTTP method type.
    """
    task_responses = self._LookupNoAcquireLock(maximum=1, name=task_name)
    if not task_responses:
      return
    task_response, = task_responses
    if task_response.task_name() != task_name:
      return

    now = datetime.datetime.utcnow()
    return QueryTasksResponseToDict(self.queue_name, task_response, now)

  @_WithLock
  def PurgeQueue(self):
    """Removes all content from the queue."""
    self._sorted_by_name = []
    self._sorted_by_eta = []
    self._sorted_by_tag = []

  @_WithLock
  def _GetTasks(self):
    """Helper method for tests returning all tasks sorted by eta.

    Returns:
      A list of taskqueue_service_pb.TaskQueueQueryTasksResponse_Task objects
        sorted by eta.
    """
    return self._GetTasksNoAcquireLock()

  def _GetTasksNoAcquireLock(self):
    """Helper method for tests returning all tasks sorted by eta.

    Returns:
      A list of taskqueue_service_pb.TaskQueueQueryTasksResponse_Task objects
        sorted by eta.
    """
    assert self._lock.locked()
    tasks = []
    for eta, task_name, task in self._sorted_by_eta:
      tasks.append(task)
    return tasks

  def _InsertTask(self, task):
    """Insert a task into the store, keeps lists sorted.

    Args:
      task: the new task.
    """
    assert self._lock.locked()
    eta = task.eta_usec()
    name = task.task_name()
    bisect.insort_left(self._sorted_by_eta, (eta, name, task))
    if task.has_tag():
      bisect.insort_left(self._sorted_by_tag, (task.tag(), eta, name, task))
    bisect.insort_left(self._sorted_by_name, (name, task))
    self.task_name_archive.add(name)

  @_WithLock
  def RunTaskNow(self, task):
    """Change the eta of a task to now.

    Args:
      task: The TaskQueueQueryTasksResponse_Task run now. This must be
          stored in this queue (otherwise an AssertionError is raised).
    """
    self._PostponeTaskNoAcquireLock(task, 0, increase_retries=False)

  @_WithLock
  def PostponeTask(self, task, new_eta_usec):
    """Postpone the task to a future time and increment the retry count.

    Args:
      task: The TaskQueueQueryTasksResponse_Task to postpone. This must be
          stored in this queue (otherwise an AssertionError is raised).
      new_eta_usec: The new eta to set on the task. This must be greater then
          the current eta on the task.
    """
    assert new_eta_usec > task.eta_usec()
    self._PostponeTaskNoAcquireLock(task, new_eta_usec)

  def _PostponeTaskNoAcquireLock(self, task, new_eta_usec,
                                 increase_retries=True):
    assert self._lock.locked()
    if increase_retries:
      self._IncRetryCount(task)
    name = task.task_name()
    eta = task.eta_usec()
    assert self._RemoveTaskFromIndex(
        self._sorted_by_eta, (eta, name, None), task)
    if task.has_tag():
      assert self._RemoveTaskFromIndex(
          self._sorted_by_tag, (task.tag(), eta, name, None), task)
    self._PostponeTaskInsertOnly(task, new_eta_usec)

  def _PostponeTaskInsertOnly(self, task, new_eta_usec):
    assert self._lock.locked()
    task.set_eta_usec(new_eta_usec)
    name = task.task_name()
    bisect.insort_left(self._sorted_by_eta, (new_eta_usec, name, task))
    if task.has_tag():
      tag = task.tag()
      bisect.insort_left(self._sorted_by_tag, (tag, new_eta_usec, name, task))

  @_WithLock
  def Lookup(self, maximum, name=None, eta=None):
    """Lookup a number of sorted tasks from the store.

    If 'eta' is specified, the tasks are looked up in a list sorted by 'eta',
    then 'name'. Otherwise they are sorted by 'name'. We need to be able to
    sort by 'eta' and 'name' because tasks can have identical eta. If you had
    20 tasks with the same ETA, you wouldn't be able to page past them, since
    the 'next eta' would give the first one again. Names are unique, though.

    Args:
      maximum: the maximum number of tasks to return.
      name: a task name to start with.
      eta: an eta to start with.

    Returns:
      A list of up to 'maximum' tasks.

    Raises:
      ValueError: if the task store gets corrupted.
    """
    return self._LookupNoAcquireLock(maximum, name, eta)

  def _IndexScan(self, index, start_key, end_key=None, max_rows=None):
    """Return the result of a 'scan' over the given index.

    The scan is inclusive of start_key and exclusive of end_key. It returns at
    most max_rows from the index.

    Args:
      index: One of the index lists, eg self._sorted_by_tag.
      start_key: The key to start at.
      end_key: Optional end key.
      max_rows: The maximum number of rows to yield.

    Returns:
      a list of up to 'max_rows' TaskQueueQueryTasksResponse_Task instances from
      the given index, in sorted order.
    """
    assert self._lock.locked()

    start_pos = bisect.bisect_left(index, start_key)
    end_pos = INF
    if end_key is not None:
      end_pos = bisect.bisect_left(index, end_key)
    if max_rows is not None:
      end_pos = min(end_pos, start_pos + max_rows)
    end_pos = min(end_pos, len(index))

    tasks = []
    for pos in xrange(start_pos, end_pos):
      tasks.append(index[pos][-1])
    return tasks

  def _LookupNoAcquireLock(self, maximum, name=None, eta=None, tag=None):
    assert self._lock.locked()
    if tag is not None:

      return self._IndexScan(self._sorted_by_tag,
                             start_key=(tag, eta, name,),
                             end_key=('%s\x00' % tag, None, None,),
                             max_rows=maximum)
    elif eta is not None:

      return self._IndexScan(self._sorted_by_eta,
                             start_key=(eta, name,),
                             max_rows=maximum)
    else:

      return self._IndexScan(self._sorted_by_name,
                             start_key=(name,),
                             max_rows=maximum)

  @_WithLock
  def Count(self):
    """Returns the number of tasks in the store."""
    return len(self._sorted_by_name)

  @_WithLock
  def OldestTask(self):
    """Returns the task with the oldest eta in the store."""
    if self._sorted_by_eta:
      return self._sorted_by_eta[0][2]
    return None

  @_WithLock
  def Oldest(self):
    """Returns the oldest eta in the store, or None if no tasks."""
    if self._sorted_by_eta:
      return self._sorted_by_eta[0][0]
    return None

  def _LocateTaskByName(self, task_name):
    """Locate the index of a task in _sorted_by_name list.

    If the task does not exist in the list, return None.

    Args:
      task_name: Name of task to be located.

    Returns:
      Index of the task in _sorted_by_name list if task exists,
      None otherwise.
    """
    assert self._lock.locked()
    pos = bisect.bisect_left(self._sorted_by_name, (task_name,))
    if (pos >= len(self._sorted_by_name) or
        self._sorted_by_name[pos][0] != task_name):
      return None
    return pos

  @_WithLock
  def Add(self, request, now):
    """Inserts a new task into the store.

    Args:
      request: A taskqueue_service_pb.TaskQueueAddRequest.
      now: A datetime.datetime object containing the current time in UTC.

    Raises:
      apiproxy_errors.ApplicationError: If a task with the same name is already
      in the store, or the task is tombstoned.
    """

    if self._LocateTaskByName(request.task_name()) is not None:
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.TASK_ALREADY_EXISTS)
    if request.task_name() in self.task_name_archive:
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.TOMBSTONED_TASK)

    now_sec = calendar.timegm(now.utctimetuple())
    task = taskqueue_service_pb.TaskQueueQueryTasksResponse_Task()
    task.set_task_name(request.task_name())
    task.set_eta_usec(request.eta_usec())
    task.set_creation_time_usec(_SecToUsec(now_sec))
    task.set_retry_count(0)
    task.set_method(request.method())

    if request.has_url():
      task.set_url(request.url())
    for keyvalue in request.header_list():
      header = task.add_header()
      header.set_key(keyvalue.key())
      header.set_value(keyvalue.value())
    if request.has_description():
      task.set_description(request.description())
    if request.has_body():
      task.set_body(request.body())
    if request.has_crontimetable():
      task.mutable_crontimetable().set_schedule(
          request.crontimetable().schedule())
      task.mutable_crontimetable().set_timezone(
          request.crontimetable().timezone())
    if request.has_retry_parameters():
      task.mutable_retry_parameters().CopyFrom(request.retry_parameters())
    if request.has_tag():
      task.set_tag(request.tag())
    self._InsertTask(task)

  @_WithLock
  def Delete(self, name):
    """Deletes a task from the store by name.

    Args:
      name: the name of the task to delete.

    Returns:
      TaskQueueServiceError.UNKNOWN_TASK: if the task is unknown.
      TaskQueueServiceError.INTERNAL_ERROR: if the store is corrupted.
      TaskQueueServiceError.TOMBSTONED: if the task was deleted.
      TaskQueueServiceError.OK: otherwise.
    """
    return self._DeleteNoAcquireLock(name)

  def _RemoveTaskFromIndex(self, index, index_tuple, task):
    """Remove a task from the specified index.

    Args:
      index: The index list that needs to be mutated.
      index_tuple: The tuple to search for in the index.
      task: The task instance that is expected to be stored at this location.

    Returns:
      True if the task was successfully removed from the index, False otherwise.
    """
    assert self._lock.locked()
    pos = bisect.bisect_left(index, index_tuple)
    if index[pos][-1] is not task:
      logging.debug('Expected %s, found %s', task, index[pos][-1])
      return False
    index.pop(pos)
    return True

  def _DeleteNoAcquireLock(self, name):
    assert self._lock.locked()
    pos = self._LocateTaskByName(name)
    if pos is None:
      if name in self.task_name_archive:
        return taskqueue_service_pb.TaskQueueServiceError.TOMBSTONED_TASK
      else:
        return taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_TASK

    old_task = self._sorted_by_name.pop(pos)[-1]


    eta = old_task.eta_usec()
    if not self._RemoveTaskFromIndex(
        self._sorted_by_eta, (eta, name, None), old_task):
      return taskqueue_service_pb.TaskQueueServiceError.INTERNAL_ERROR


    if old_task.has_tag():
      tag = old_task.tag()
      if not self._RemoveTaskFromIndex(
          self._sorted_by_tag, (tag, eta, name, None), old_task):
        return taskqueue_service_pb.TaskQueueServiceError.INTERNAL_ERROR

    return taskqueue_service_pb.TaskQueueServiceError.OK

  @_WithLock
  def Populate(self, num_tasks):
    """Populates the store with a number of tasks.

    Args:
      num_tasks: the number of tasks to insert.
    """

    def RandomTask():
      """Creates a new task and randomly populates values."""
      assert self._lock.locked()
      task = taskqueue_service_pb.TaskQueueQueryTasksResponse_Task()
      task.set_task_name(''.join(random.choice(string.ascii_lowercase)
                                 for x in range(20)))

      task.set_eta_usec(now_usec + random.randint(_SecToUsec(-10),
                                                  _SecToUsec(600)))



      task.set_creation_time_usec(min(now_usec, task.eta_usec()) -
                                  random.randint(0, _SecToUsec(20)))

      task.set_url(random.choice(['/a', '/b', '/c', '/d']))
      if random.random() < 0.2:
        task.set_method(
            taskqueue_service_pb.TaskQueueQueryTasksResponse_Task.POST)
        task.set_body('A' * 2000)
      else:
        task.set_method(
            taskqueue_service_pb.TaskQueueQueryTasksResponse_Task.GET)
      retry_count = max(0, random.randint(-10, 5))
      task.set_retry_count(retry_count)
      task.set_execution_count(retry_count)
      if random.random() < 0.3:
        random_headers = [('nexus', 'one'),
                          ('foo', 'bar'),
                          ('content-type', 'text/plain'),
                          ('from', 'user@email.com')]
        for _ in xrange(random.randint(1, 4)):
          elem = random.randint(0, len(random_headers) - 1)
          key, value = random_headers.pop(elem)
          header_proto = task.add_header()
          header_proto.set_key(key)
          header_proto.set_value(value)
      return task

    now_usec = _SecToUsec(time.time())
    for _ in range(num_tasks):
      self._InsertTask(RandomTask())


class _TaskExecutor(object):
  """Executor for a task object.

  Converts a TaskQueueQueryTasksResponse_Task into a http request, then uses the
  httplib library to send it to the http server.
  """

  def __init__(self, default_host, request_data):
    """Constructor.

    Args:
      default_host: a string to use as the host/port to connect to if the host
          header is not specified in the task.
      request_data: A request_info.RequestInfo instance used to look up state
          associated with the request that generated an API call.
    """
    self._default_host = default_host
    self._request_data = request_data

  def _HeadersFromTask(self, task, queue):
    """Constructs the http headers for the given task.

    This function will remove special headers (values in BUILT_IN_HEADERS) and
    add the taskqueue headers.

    Args:
      task: The task, a TaskQueueQueryTasksResponse_Task instance.
      queue: The queue that this task belongs to, an _Queue instance.

    Returns:
      A list of tuples containing the http header and value. There
          may be be mutiple entries with the same key.
    """
    headers = []
    for header in task.header_list():
      header_key_lower = header.key().lower()

      if header_key_lower == 'host' and queue.target is not None:
        headers.append(
            (header.key(), '.'.join([queue.target, self._default_host])))
      elif header_key_lower not in BUILT_IN_HEADERS:
        headers.append((header.key(), header.value()))


    headers.append(('X-AppEngine-QueueName', queue.queue_name))
    headers.append(('X-AppEngine-TaskName', task.task_name()))
    headers.append(('X-AppEngine-TaskRetryCount', str(task.retry_count())))
    headers.append(('X-AppEngine-TaskETA',
                    str(_UsecToSec(task.eta_usec()))))
    headers.append(('X-AppEngine-Fake-Is-Admin', '1'))
    headers.append(('Content-Length', str(len(task.body()))))
    if (task.has_body() and 'content-type' not in
        [key.lower() for key, _ in headers]):
      headers.append(('Content-Type', 'application/octet-stream'))
    headers.append(('X-AppEngine-TaskExecutionCount',
                    str(task.execution_count())))
    if task.has_runlog() and task.runlog().has_response_code():
      headers.append(('X-AppEngine-TaskPreviousResponse',
                      str(task.runlog().response_code())))

    return headers

  def ExecuteTask(self, task, queue):
    """Construct a http request from the task and dispatch it.

    Args:
      task: The task to convert to a http request and then send. An instance of
          taskqueue_service_pb.TaskQueueQueryTasksResponse_Task
      queue: The queue that this task belongs to. An instance of _Queue.

    Returns:
      Http Response code from the task's execution, 0 if an exception occurred.
    """
    method = task.RequestMethod_Name(task.method())
    headers = self._HeadersFromTask(task, queue)
    dispatcher = self._request_data.get_dispatcher()
    try:
      response = dispatcher.add_request(method, task.url(), headers,
                                        task.body() if task.has_body() else '',
                                        '0.1.0.2')
    except request_info.ModuleDoesNotExistError:
      logging.exception('Failed to dispatch task')
      return 0
    return int(response.status.split(' ', 1)[0])


class _BackgroundTaskScheduler(object):
  """The task scheduler class.

  This class is designed to be run in a background thread.

  Note: There must not be more than one instance of _BackgroundTaskScheduler per
  group.
  """

  def __init__(self, group, task_executor, retry_seconds, **kwargs):
    """Constructor.

    Args:
      group: The group that we will automatically execute tasks from. Must be an
          instance of _Group.
      task_executor: The class used to convert a task into a http request. Must
          be an instance of _TaskExecutor.
      retry_seconds: The number of seconds to delay a task by if its execution
          fails.
      _get_time: a callable that returns the current time in seconds since the
          epoch. This argument may only be passed in by keyword. If unset, use
          time.time.
    """
    self._group = group
    self._should_exit = False
    self._next_wakeup = INF
    self._event = threading.Event()
    self._wakeup_lock = threading.Lock()
    self.task_executor = task_executor
    self.default_retry_seconds = retry_seconds

    self._get_time = kwargs.pop('_get_time', time.time)
    if kwargs:
      raise TypeError('Unknown parameters: %s' % ', '.join(kwargs))

  def UpdateNextEventTime(self, next_event_time):
    """Notify the TaskExecutor of the closest event it needs to process.

    Args:
      next_event_time: The time of the event in seconds since the epoch.
    """
    with self._wakeup_lock:
      if next_event_time < self._next_wakeup:
        self._next_wakeup = next_event_time
        self._event.set()

  def Shutdown(self):
    """Request this TaskExecutor to exit."""
    self._should_exit = True
    self._event.set()

  def _ProcessQueues(self):
    with self._wakeup_lock:
      self._next_wakeup = INF

    now = self._get_time()
    queue, task = self._group.GetNextPushTask()
    while task and _UsecToSec(task.eta_usec()) <= now:
      if task.retry_count() == 0:
        task.set_first_try_usec(_SecToUsec(now))

      response_code = self.task_executor.ExecuteTask(task, queue)
      if response_code:
        task.mutable_runlog().set_response_code(response_code)
      else:
        logging.error(
            'An error occured while sending the task "%s" '
            '(Url: "%s") in queue "%s". Treating as a task error.',
            task.task_name(), task.url(), queue.queue_name)




      now = self._get_time()
      if 200 <= response_code < 300:
        queue.Delete(task.task_name())
      else:
        retry = Retry(task, queue)
        age_usec = _SecToUsec(now) - task.first_try_usec()
        if retry.CanRetry(task.retry_count() + 1, age_usec):
          retry_usec = retry.CalculateBackoffUsec(task.retry_count() + 1)
          logging.warning(
              'Task %s failed to execute. This task will retry in %.3f seconds',
              task.task_name(), _UsecToSec(retry_usec))



          queue.PostponeTask(task, _SecToUsec(now) + retry_usec)
        else:
          logging.warning(
              'Task %s failed to execute. The task has no remaining retries. '
              'Failing permanently after %d retries and %d seconds',
              task.task_name(), task.retry_count(), _UsecToSec(age_usec))
          queue.Delete(task.task_name())
      queue, task = self._group.GetNextPushTask()

    if task:
      with self._wakeup_lock:
        eta = _UsecToSec(task.eta_usec())
        if eta < self._next_wakeup:
          self._next_wakeup = eta

  def _Wait(self):
    """Block until we need to process a task or we need to exit."""


    now = self._get_time()
    while not self._should_exit and self._next_wakeup > now:
      timeout = self._next_wakeup - now
      self._event.wait(timeout)
      self._event.clear()
      now = self._get_time()

  def MainLoop(self):
    """The main loop of the scheduler."""
    while not self._should_exit:
      self._ProcessQueues()
      self._Wait()


class TaskQueueServiceStub(apiproxy_stub.APIProxyStub):
  """Python only task queue service stub.

  This stub executes tasks when enabled by using the dev_appserver's AddEvent
  capability. When task running is disabled this stub will store tasks for
  display on a console, where the user may manually execute the tasks.
  """

  def __init__(self,
               service_name='taskqueue',
               root_path=None,
               auto_task_running=False,
               task_retry_seconds=30,
               _all_queues_valid=False,
               default_http_server='localhost',
               _testing_validate_state=False,
               request_data=None):
    """Constructor.

    Args:
      service_name: Service name expected for all calls.
      root_path: Root path to the directory of the application which may contain
        a queue.yaml file. If None, then it's assumed no queue.yaml file is
        available.
      auto_task_running: When True, the dev_appserver should automatically
        run tasks after they are enqueued.
      task_retry_seconds: How long to wait between task executions after a
        task fails.
      _testing_validate_state: Should this stub and all of its  _Groups (and
          thus and all of its _Queues) validate their state after each
          operation? This should only be used during testing of the
          taskqueue_stub.
      request_data: A request_info.RequestInfo instance used to look up state
          associated with the request that generated an API call.
    """
    super(TaskQueueServiceStub, self).__init__(
        service_name, max_request_size=MAX_REQUEST_SIZE,
        request_data=request_data)


    self._queues = {}





    self._all_queues_valid = _all_queues_valid

    self._root_path = root_path
    self._testing_validate_state = _testing_validate_state


    self._queues[None] = _Group(
        self._ParseQueueYaml, app_id=None,
        _all_queues_valid=_all_queues_valid,
        _update_newest_eta=self._UpdateNextEventTime,
        _testing_validate_state=self._testing_validate_state)

    self._auto_task_running = auto_task_running
    self._started = False

    self._task_scheduler = _BackgroundTaskScheduler(
        self._queues[None], _TaskExecutor(default_http_server,
                                          self.request_data),
        retry_seconds=task_retry_seconds)
    self._yaml_last_modified = None

  def StartBackgroundExecution(self):
    """Start automatic task execution."""
    if not self._started and self._auto_task_running:
      task_scheduler_thread = threading.Thread(
          target=self._task_scheduler.MainLoop)
      task_scheduler_thread.setDaemon(True)
      task_scheduler_thread.start()
      self._started = True

  def Shutdown(self):
    """Requests the task scheduler to shutdown."""
    self._task_scheduler.Shutdown()

  def _ParseQueueYaml(self):
    """Loads the queue.yaml file and parses it.

    Returns:
      None if queue.yaml doesn't exist, otherwise a queueinfo.QueueEntry object
      populated from the queue.yaml.
    """
    if hasattr(self, 'queue_yaml_parser'):

      return self.queue_yaml_parser(self._root_path)



    if self._root_path is None:
      return None
    for queueyaml in (
        'queue.yaml', 'queue.yml',
        os.path.join('WEB-INF', 'appengine-generated', 'queue.yaml')):
      try:
        path = os.path.join(self._root_path, queueyaml)
        modified = os.stat(path).st_mtime
        if self._yaml_last_modified and self._yaml_last_modified == modified:
          return self._last_queue_info
        fh = open(path, 'r')
      except (IOError, OSError):
        continue
      try:
        queue_info = queueinfo.LoadSingleQueue(fh)
        self._last_queue_info = queue_info
        self._yaml_last_modified = modified
        return queue_info
      finally:
        fh.close()
    return None

  def _UpdateNextEventTime(self, callback_time):
    """Enqueue a task to be automatically scheduled.

    Note: If auto task running is disabled, this function is a no-op.

    Args:
      callback_time: The earliest time this task may be run, in seconds since
        the epoch.
    """
    self._task_scheduler.UpdateNextEventTime(callback_time)

  def _GetGroup(self, app_id=None):
    """Get the _Group instance for app_id, creating a new one if needed.

    Args:
      app_id: The app id in question. Note: This field is not validated.
    """
    if app_id not in self._queues:
      self._queues[app_id] = _Group(
          app_id=app_id, _all_queues_valid=self._all_queues_valid,
          _testing_validate_state=self._testing_validate_state)
    return self._queues[app_id]

  def _Dynamic_Add(self, request, response):
    """Add a single task to a queue.

    This method is a wrapper around the BulkAdd RPC request.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: The taskqueue_service_pb.TaskQueueAddRequest. See
          taskqueue_service.proto.
      response: The taskqueue_service_pb.TaskQueueAddResponse. See
          taskqueue_service.proto.
    """
    bulk_request = taskqueue_service_pb.TaskQueueBulkAddRequest()
    bulk_response = taskqueue_service_pb.TaskQueueBulkAddResponse()

    bulk_request.add_add_request().CopyFrom(request)
    self._Dynamic_BulkAdd(bulk_request, bulk_response)

    assert bulk_response.taskresult_size() == 1
    result = bulk_response.taskresult(0).result()

    if result != taskqueue_service_pb.TaskQueueServiceError.OK:
      raise apiproxy_errors.ApplicationError(result)
    elif bulk_response.taskresult(0).has_chosen_task_name():
      response.set_chosen_task_name(
          bulk_response.taskresult(0).chosen_task_name())

  def _Dynamic_BulkAdd(self, request, response):
    """Add many tasks to a queue using a single request.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: The taskqueue_service_pb.TaskQueueBulkAddRequest. See
          taskqueue_service.proto.
      response: The taskqueue_service_pb.TaskQueueBulkAddResponse. See
          taskqueue_service.proto.
    """














    assert request.add_request_size(), 'taskqueue should prevent empty requests'
    self._GetGroup(_GetAppId(request.add_request(0))).BulkAdd_Rpc(
        request, response)

  def GetQueues(self):
    """Gets all the application's queues.

    Returns:
      A list of dictionaries, where each dictionary contains one queue's
      attributes. E.g.:
        [{'name': 'some-queue',
          'max_rate': '1/s',
          'bucket_size': 5,
          'oldest_task': '2009/02/02 05:37:42',
          'eta_delta': '0:00:06.342511 ago',
          'tasks_in_queue': 12}, ...]
      The list of queues always includes the default queue.
    """
    return self._GetGroup().GetQueuesAsDicts()

  def GetTasks(self, queue_name):
    """Gets a queue's tasks.

    Args:
      queue_name: Queue's name to return tasks for.

    Returns:
      A list of dictionaries, where each dictionary contains one task's
      attributes. E.g.
        [{'name': 'task-123',
          'queue_name': 'default',
          'url': '/update',
          'method': 'GET',
          'eta': '2009/02/02 05:37:42',
          'eta_delta': '0:00:06.342511 ago',
          'body': '',
          'headers': [('user-header', 'some-value')
                      ('X-AppEngine-QueueName': 'update-queue'),
                      ('X-AppEngine-TaskName': 'task-123'),
                      ('X-AppEngine-TaskRetryCount': '0'),
                      ('X-AppEngine-TaskETA': '1234567890.123456'),
                      ('X-AppEngine-Development-Payload': '1'),
                      ('Content-Length': 0),
                      ('Content-Type': 'application/octet-stream')]

    Raises:
      ValueError: A task request contains an unknown HTTP method type.
      KeyError: An invalid queue name was specified.
    """
    return self._GetGroup().GetQueue(queue_name).GetTasksAsDicts()

  def DeleteTask(self, queue_name, task_name):
    """Deletes a task from a queue, without leaving a tombstone.

    Args:
      queue_name: the name of the queue to delete the task from.
      task_name: the name of the task to delete.
    """
    if self._GetGroup().HasQueue(queue_name):
      queue = self._GetGroup().GetQueue(queue_name)
      queue.Delete(task_name)
      queue.task_name_archive.discard(task_name)

  def FlushQueue(self, queue_name):
    """Removes all tasks from a queue, without leaving tombstones.

    Args:
      queue_name: the name of the queue to remove tasks from.
    """
    if self._GetGroup().HasQueue(queue_name):
      self._GetGroup().GetQueue(queue_name).PurgeQueue()
      self._GetGroup().GetQueue(queue_name).task_name_archive.clear()

  def _Dynamic_UpdateQueue(self, request, unused_response):
    """Local implementation of the UpdateQueue RPC in TaskQueueService.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueUpdateQueueRequest.
      unused_response: A taskqueue_service_pb.TaskQueueUpdateQueueResponse.
                       Not used.
    """
    self._GetGroup(_GetAppId(request)).UpdateQueue_Rpc(request, unused_response)

  def _Dynamic_FetchQueues(self, request, response):
    """Local implementation of the FetchQueues RPC in TaskQueueService.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueFetchQueuesRequest.
      response: A taskqueue_service_pb.TaskQueueFetchQueuesResponse.
    """
    self._GetGroup(_GetAppId(request)).FetchQueues_Rpc(request, response)

  def _Dynamic_FetchQueueStats(self, request, response):
    """Local 'random' implementation of the TaskQueueService.FetchQueueStats.

    This implementation loads some stats from the task store, the rest with
    random numbers.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueFetchQueueStatsRequest.
      response: A taskqueue_service_pb.TaskQueueFetchQueueStatsResponse.
    """
    self._GetGroup(_GetAppId(request)).FetchQueueStats_Rpc(request, response)

  def _Dynamic_QueryTasks(self, request, response):
    """Local implementation of the TaskQueueService.QueryTasks RPC.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueQueryTasksRequest.
      response: A taskqueue_service_pb.TaskQueueQueryTasksResponse.
    """
    self._GetGroup(_GetAppId(request)).QueryTasks_Rpc(request, response)

  def _Dynamic_FetchTask(self, request, response):
    """Local implementation of the TaskQueueService.FetchTask RPC.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueFetchTaskRequest.
      response: A taskqueue_service_pb.TaskQueueFetchTaskResponse.
    """
    self._GetGroup(_GetAppId(request)).FetchTask_Rpc(request, response)

  def _Dynamic_Delete(self, request, response):
    """Local delete implementation of TaskQueueService.Delete.

    Deletes tasks from the task store. A 1/20 chance of a transient error.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueDeleteRequest.
      response: A taskqueue_service_pb.TaskQueueDeleteResponse.
    """
    self._GetGroup(_GetAppId(request)).Delete_Rpc(request, response)

  def _Dynamic_ForceRun(self, request, response):
    """Local force run implementation of TaskQueueService.ForceRun.

    Forces running of a task in a queue. This will fail randomly for testing if
    the app id is non-empty.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueForceRunRequest.
      response: A taskqueue_service_pb.TaskQueueForceRunResponse.
    """
    if _GetAppId(request) is not None:

      if random.random() <= 0.05:
        response.set_result(
            taskqueue_service_pb.TaskQueueServiceError.TRANSIENT_ERROR)
      elif random.random() <= 0.052:
        response.set_result(
            taskqueue_service_pb.TaskQueueServiceError.INTERNAL_ERROR)
      else:
        response.set_result(
            taskqueue_service_pb.TaskQueueServiceError.OK)
    else:
      group = self._GetGroup(None)
      if not group.HasQueue(request.queue_name()):
        response.set_result(
            taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_QUEUE)
        return
      queue = group.GetQueue(request.queue_name())
      task = queue.Lookup(1, name=request.task_name())
      if not task:
        response.set_result(
            taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_TASK)
        return
      queue.RunTaskNow(task[0])
      self._UpdateNextEventTime(0)
      response.set_result(
          taskqueue_service_pb.TaskQueueServiceError.OK)

  def _Dynamic_DeleteQueue(self, request, response):
    """Local delete implementation of TaskQueueService.DeleteQueue.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueDeleteQueueRequest.
      response: A taskqueue_service_pb.TaskQueueDeleteQueueResponse.
    """
    app_id = _GetAppId(request)
    if app_id is None:
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.PERMISSION_DENIED)
    self._GetGroup(app_id).DeleteQueue_Rpc(request, response)

  def _Dynamic_PauseQueue(self, request, response):
    """Local pause implementation of TaskQueueService.PauseQueue.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueuePauseQueueRequest.
      response: A taskqueue_service_pb.TaskQueuePauseQueueResponse.
    """
    app_id = _GetAppId(request)
    if app_id is None:
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.PERMISSION_DENIED)
    self._GetGroup(app_id).PauseQueue_Rpc(request, response)

  def _Dynamic_PurgeQueue(self, request, response):
    """Local purge implementation of TaskQueueService.PurgeQueue.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueuePurgeQueueRequest.
      response: A taskqueue_service_pb.TaskQueuePurgeQueueResponse.
    """

    self._GetGroup(_GetAppId(request)).PurgeQueue_Rpc(request, response)

  def _Dynamic_DeleteGroup(self, request, response):
    """Local delete implementation of TaskQueueService.DeleteGroup.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueDeleteGroupRequest.
      response: A taskqueue_service_pb.TaskQueueDeleteGroupResponse.
    """
    app_id = _GetAppId(request)
    if app_id is None:
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.PERMISSION_DENIED)

    if app_id in self._queues:
      del self._queues[app_id]
    else:

      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_QUEUE)

  def _Dynamic_UpdateStorageLimit(self, request, response):
    """Local implementation of TaskQueueService.UpdateStorageLimit.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueUpdateStorageLimitRequest.
      response: A taskqueue_service_pb.TaskQueueUpdateStorageLimitResponse.
    """
    if _GetAppId(request) is None:
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.PERMISSION_DENIED)

    if request.limit() < 0 or request.limit() > 1000 * (1024 ** 4):
      raise apiproxy_errors.ApplicationError(
          taskqueue_service_pb.TaskQueueServiceError.INVALID_REQUEST)

    response.set_new_limit(request.limit())

  def _Dynamic_QueryAndOwnTasks(self, request, response):
    """Local implementation of TaskQueueService.QueryAndOwnTasks.

    Must adhere to the '_Dynamic_' naming convention for stubbing to work.
    See taskqueue_service.proto for a full description of the RPC.

    Args:
      request: A taskqueue_service_pb.TaskQueueQueryAndOwnTasksRequest.
      response: A taskqueue_service_pb.TaskQueueQueryAndOwnTasksResponse.

    Raises:
      InvalidQueueModeError: If target queue is not a pull queue.
    """





    self._GetGroup().QueryAndOwnTasks_Rpc(request, response)

  def _Dynamic_ModifyTaskLease(self, request, response):
    """Local implementation of TaskQueueService.ModifyTaskLease.

    Args:
      request: A taskqueue_service_pb.TaskQueueModifyTaskLeaseRequest.
      response: A taskqueue_service_pb.TaskQueueModifyTaskLeaseResponse.

    Raises:
      InvalidQueueModeError: If target queue is not a pull queue.
    """

    self._GetGroup().ModifyTaskLease_Rpc(request, response)





  def get_filtered_tasks(self, url=None, name=None, queue_names=None):
    """Get the tasks in the task queue with filters.

    Args:
      url: A URL that all returned tasks should point at.
      name: The name of all returned tasks.
      queue_names: A list of queue names to retrieve tasks from. If left blank
        this will get default to all queues available.

    Returns:
      A list of taskqueue.Task objects.
    """
    all_queue_names = [queue['name'] for queue in self.GetQueues()]


    if isinstance(queue_names, basestring):
      queue_names = [queue_names]


    if queue_names is None:
      queue_names = all_queue_names


    task_dicts = []
    for queue_name in queue_names:
      if queue_name in all_queue_names:
        for task in self.GetTasks(queue_name):
          if url is not None and task['url'] != url:
            continue
          if name is not None and task['name'] != name:
            continue
          task_dicts.append(task)

    tasks = []
    for task in task_dicts:

      payload = base64.b64decode(task['body'])

      headers = dict(task['headers'])
      headers['Content-Length'] = str(len(payload))


      eta = datetime.datetime.strptime(task['eta'], '%Y/%m/%d %H:%M:%S')
      eta = eta.replace(tzinfo=taskqueue._UTC)

      task_object = taskqueue.Task(name=task['name'], method=task['method'],
                                   url=task['url'], headers=headers,
                                   payload=payload, eta=eta)
      tasks.append(task_object)
    return tasks
