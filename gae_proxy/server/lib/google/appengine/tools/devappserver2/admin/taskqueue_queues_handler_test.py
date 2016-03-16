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
"""Tests for devappserver2.admin.taskqueue_queues_handler."""



import unittest

import google
import mox
import webapp2

from google.appengine.api import apiproxy_stub_map
from google.appengine.api.taskqueue import taskqueue_service_pb

from google.appengine.tools.devappserver2.admin import admin_request_handler
from google.appengine.tools.devappserver2.admin import taskqueue_queues_handler
from google.appengine.tools.devappserver2.admin import taskqueue_utils


class TestTaskQueueQueuesHandler(unittest.TestCase):
  """Tests for taskqueue_queues_handler.TaskQueueQueuesHandler."""

  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(taskqueue_utils.QueueInfo, 'get')
    self.mox.StubOutWithMock(admin_request_handler.AdminRequestHandler,
                             'render')

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_get(self):
    queue1 = taskqueue_utils.QueueInfo(
        name='queue1',
        mode=taskqueue_service_pb.TaskQueueMode.PUSH,
        rate='10/s',
        bucket_size=20,
        tasks_in_queue=10,
        oldest_eta_usec=-1)
    queue2 = taskqueue_utils.QueueInfo(
        name='queue1',
        mode=taskqueue_service_pb.TaskQueueMode.PUSH,
        rate='20/s',
        bucket_size=20,
        tasks_in_queue=10,
        oldest_eta_usec=-1)
    queue3 = taskqueue_utils.QueueInfo(
        name='queue1',
        mode=taskqueue_service_pb.TaskQueueMode.PULL,
        rate='20/s',
        bucket_size=20,
        tasks_in_queue=10,
        oldest_eta_usec=-1)

    taskqueue_utils.QueueInfo.get().AndReturn([queue1, queue2, queue3])
    request = webapp2.Request.blank('/taskqueue')
    response = webapp2.Response()

    handler = taskqueue_queues_handler.TaskQueueQueuesHandler(request, response)
    handler.render('taskqueue_queues.html',
                   {'push_queues': [queue1, queue2],
                    'pull_queues': [queue3]})

    self.mox.ReplayAll()
    handler.get()
    self.mox.VerifyAll()

if __name__ == '__main__':
  unittest.main()
