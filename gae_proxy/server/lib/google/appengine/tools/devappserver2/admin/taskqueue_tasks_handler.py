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
"""A handler that displays task information for a single queue."""



import datetime
import urllib

from google.appengine.api import apiproxy_stub_map
from google.appengine.api.taskqueue import taskqueue_service_pb
from google.appengine.api.taskqueue import taskqueue_stub

from google.appengine.tools.devappserver2.admin import admin_request_handler
from google.appengine.tools.devappserver2.admin import taskqueue_utils


_TASKS_TO_LOAD = 1000

# TODO: Make "Run" work.

class TaskQueueTasksHandler(admin_request_handler.AdminRequestHandler):
  """A handler that displays queue information for the application."""

  @staticmethod
  def _get_tasks(queue_name,
                 count,
                 start_task_name=None,
                 start_eta_usec=None):
    request = taskqueue_service_pb.TaskQueueQueryTasksRequest()
    request.set_queue_name(queue_name)
    request.set_max_rows(count)
    if start_task_name is not None:
      request.set_start_task_name(start_task_name)
    if start_eta_usec is not None:
      request.set_start_eta_usec(start_eta_usec)

    response = taskqueue_service_pb.TaskQueueQueryTasksResponse()
    apiproxy_stub_map.MakeSyncCall('taskqueue',
                                   'QueryTasks',
                                   request,
                                   response)

    now = datetime.datetime.utcnow()
    for task in response.task_list():
      # Nothing is done with the body so save some memory and CPU by removing
      # it.
      task.set_body('')
      yield taskqueue_stub.QueryTasksResponseToDict(queue_name, task, now)

  @staticmethod
  def _delete_task(queue_name, task_name):
    request = taskqueue_service_pb.TaskQueueDeleteRequest()
    request.set_queue_name(queue_name)
    request.task_name_list().append(task_name)

    response = taskqueue_service_pb.TaskQueueDeleteResponse()
    apiproxy_stub_map.MakeSyncCall('taskqueue',
                                   'Delete',
                                   request,
                                   response)
    return response.result(0)

  @staticmethod
  def _run_task(queue_name, task_name):
    request = taskqueue_service_pb.TaskQueueForceRunRequest()
    request.set_queue_name(queue_name)
    request.set_task_name(task_name)

    response = taskqueue_service_pb.TaskQueueForceRunResponse()
    apiproxy_stub_map.MakeSyncCall('taskqueue',
                                   'ForceRun',
                                   request,
                                   response)
    return response.result()

  def get(self, queue_name):
    queue_info = taskqueue_utils.QueueInfo.get(
        queue_names=frozenset([queue_name])).next()
    tasks = list(self._get_tasks(queue_name, count=_TASKS_TO_LOAD))

    self.response.write(
        self.render(
            'taskqueue_tasks.html',
            {'is_push_queue':
             queue_info.mode == taskqueue_service_pb.TaskQueueMode.PUSH,
             'page': self.request.get('page'),
             'queue_info': queue_info,
             'queue_name': queue_name,
             'tasks': tasks,
             'error': self.request.get('message')}))

  def post(self, queue_name):
    """Handle modifying actions and redirect to a GET page."""
    task_name = self.request.get('task_name')

    if self.request.get('action:deletetask'):
      result = self._delete_task(queue_name, task_name)
    elif self.request.get('action:runtask'):
      result = self._run_task(queue_name, task_name)
    if result == taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_QUEUE:
      message = 'Queue "%s" not found' % queue_name
    elif result == taskqueue_service_pb.TaskQueueServiceError.UNKNOWN_TASK:
      message = 'Task "%s" not found' % task_name
    elif result != taskqueue_service_pb.TaskQueueServiceError.OK:
      message = 'Internal error'
    else:
      message = ''
    self.redirect(
        '%s?%s' % (self.request.path_url,
                   urllib.urlencode({'page': self.request.get('page'),
                                     'message': message})))
