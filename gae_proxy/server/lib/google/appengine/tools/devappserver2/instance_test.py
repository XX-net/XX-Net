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
"""Tests for google.apphosting.tools.devappserver2.instance."""



import time
import unittest

import google
import mox

from google.appengine.tools.devappserver2 import instance
from google.appengine.tools.devappserver2 import wsgi_request_info


class TestInstance(unittest.TestCase):
  """Tests for instance.Instance."""

  def setUp(self):
    self.mox = mox.Mox()
    self.proxy = self.mox.CreateMock(instance.RuntimeProxy)
    self.environ = object()
    self.start_response = object()
    self.url_map = object()
    self.match = object()
    self.request_id = object()
    self.response = [object()]
    self.request_data = self.mox.CreateMock(wsgi_request_info.WSGIRequestInfo)

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_new_instance(self):
    inst = instance.Instance(
        self.request_data, 'name', self.proxy, max_concurrent_requests=5,
        expect_ready_request=True)
    self.assertEqual(0, inst.total_requests)
    self.assertEqual(5, inst.remaining_request_capacity)
    self.assertEqual(0, inst.num_outstanding_requests)
    self.assertFalse(inst.can_accept_requests)
    self.assertTrue(inst.handling_ready_request)
    self.assertAlmostEqual(0, inst.idle_seconds, places=2)
    self.assertEqual(0, inst.get_latency_60s())
    self.assertEqual(0, inst.get_qps_60s())
    self.assertEqual('name', inst.instance_id)

  def test_handle(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    self.mox.StubOutWithMock(inst._condition, 'notify')

    self.proxy.start()
    self.environ = {}
    self.request_data.set_request_instance(self.request_id, inst)
    self.proxy.handle(self.environ,
                      self.start_response,
                      self.url_map,
                      self.match,
                      self.request_id,
                      instance.NORMAL_REQUEST).AndReturn(self.response)
    inst._condition.notify()
    self.mox.ReplayAll()
    now = time.time()
    inst._request_history.append((now - 100, now - 80))
    inst.start()
    self.assertTrue(inst.can_accept_requests)
    self.assertEqual(
        self.response,
        list(inst.handle(self.environ,
                         self.start_response,
                         self.url_map,
                         self.match,
                         self.request_id,
                         instance.NORMAL_REQUEST)))
    self.mox.VerifyAll()

    self.assertEqual(1, len(inst._request_history))
    self.assertEqual(1, inst.total_requests)
    self.assertEqual(5, inst.remaining_request_capacity)
    self.assertEqual(0, inst.num_outstanding_requests)
    self.assertTrue(0 < inst.get_qps_60s())

  def test_handle_ready_request(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5,
                             expect_ready_request=True)
    self.mox.StubOutWithMock(inst._condition, 'notify')

    self.proxy.start()
    self.environ = {}
    self.request_data.set_request_instance(self.request_id, inst)
    self.proxy.handle(self.environ,
                      self.start_response,
                      self.url_map,
                      self.match,
                      self.request_id,
                      instance.READY_REQUEST).AndReturn(self.response)
    inst._condition.notify(5)
    self.mox.ReplayAll()
    inst.start()
    self.assertFalse(inst.can_accept_requests)
    self.assertRaises(instance.CannotAcceptRequests,
                      inst.handle,
                      self.environ,
                      self.start_response,
                      self.url_map,
                      self.match,
                      self.request_id,
                      instance.NORMAL_REQUEST)
    self.assertEqual(
        self.response,
        list(inst.handle(self.environ,
                         self.start_response,
                         self.url_map,
                         self.match,
                         self.request_id,
                         instance.READY_REQUEST)))
    self.mox.VerifyAll()

    self.assertEqual(1, inst.total_requests)
    self.assertEqual(5, inst.remaining_request_capacity)
    self.assertEqual(0, inst.num_outstanding_requests)
    self.assertTrue(0 < inst.get_qps_60s())
    self.assertFalse(inst.handling_ready_request)

  def test_handle_background_request(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5,
                             max_background_threads=2)
    inst._num_running_background_threads = 1
    self.mox.StubOutWithMock(inst._condition, 'notify')

    self.proxy.start()
    self.environ = {}
    self.request_data.set_request_instance(self.request_id, inst)
    self.proxy.handle(self.environ,
                      self.start_response,
                      self.url_map,
                      self.match,
                      self.request_id,
                      instance.BACKGROUND_REQUEST).AndReturn(self.response)
    self.mox.ReplayAll()
    inst.start()
    self.assertTrue(inst.can_accept_requests)
    self.assertEqual(1, inst.remaining_background_thread_capacity)
    self.assertEqual(
        self.response,
        list(inst.handle(self.environ,
                         self.start_response,
                         self.url_map,
                         self.match,
                         self.request_id,
                         instance.BACKGROUND_REQUEST)))
    self.mox.VerifyAll()

    self.assertEqual(1, inst.total_requests)
    self.assertEqual(5, inst.remaining_request_capacity)
    self.assertEqual(0, inst.num_outstanding_requests)
    self.assertTrue(0 < inst.get_qps_60s())
    self.assertEqual(2, inst.remaining_background_thread_capacity)
    self.assertFalse(inst.handling_ready_request)

  def test_handle_shutdown_request(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=1)
    inst._num_outstanding_requests = 0
    self.mox.StubOutWithMock(inst._condition, 'notify_all')

    self.proxy.start()
    self.environ = {}
    self.request_data.set_request_instance(self.request_id, inst)
    self.proxy.handle(self.environ,
                      self.start_response,
                      self.url_map,
                      self.match,
                      self.request_id,
                      instance.SHUTDOWN_REQUEST).AndReturn(self.response)
    self.proxy.quit()
    inst._condition.notify_all()
    self.mox.ReplayAll()
    inst.start()
    self.assertTrue(inst.can_accept_requests)
    self.assertFalse(inst.has_quit)
    inst.quit(expect_shutdown=True)
    self.assertFalse(inst.can_accept_requests)
    self.assertTrue(inst.has_quit)
    self.assertEqual(
        self.response,
        list(inst.handle(self.environ,
                         self.start_response,
                         self.url_map,
                         self.match,
                         self.request_id,
                         instance.SHUTDOWN_REQUEST)))
    self.mox.VerifyAll()

    self.assertEqual(1, inst.total_requests)
    self.assertEqual(1, inst.remaining_request_capacity)
    self.assertEqual(0, inst.num_outstanding_requests)
    self.assertTrue(0 < inst.get_qps_60s())
    self.assertFalse(inst._quitting)
    self.assertTrue(inst._quit)

  def test_handle_shutdown_request_running_request(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=1)
    inst._num_outstanding_requests = 1
    self.mox.StubOutWithMock(inst._condition, 'notify_all')

    self.proxy.start()
    self.environ = {}
    self.request_data.set_request_instance(self.request_id, inst)
    self.proxy.handle(self.environ,
                      self.start_response,
                      self.url_map,
                      self.match,
                      self.request_id,
                      instance.SHUTDOWN_REQUEST).AndReturn(self.response)
    self.mox.ReplayAll()
    inst.start()
    self.assertTrue(inst.can_accept_requests)
    self.assertFalse(inst.has_quit)
    inst.quit(expect_shutdown=True)
    self.assertFalse(inst.can_accept_requests)
    self.assertTrue(inst.has_quit)
    self.assertEqual(
        self.response,
        list(inst.handle(self.environ,
                         self.start_response,
                         self.url_map,
                         self.match,
                         self.request_id,
                         instance.SHUTDOWN_REQUEST)))
    self.mox.VerifyAll()

    self.assertEqual(1, inst.total_requests)
    self.assertEqual(0, inst.remaining_request_capacity)
    self.assertEqual(1, inst.num_outstanding_requests)
    self.assertEqual(0, inst.idle_seconds)
    self.assertTrue(0 < inst.get_qps_60s())
    self.assertTrue(inst._quitting)
    self.assertFalse(inst._quit)

  def test_handle_before_start(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    self.mox.StubOutWithMock(inst._condition, 'notify')

    self.assertRaises(instance.CannotAcceptRequests,
                      inst.handle,
                      self.environ,
                      self.start_response,
                      self.url_map,
                      self.match,
                      self.request_id,
                      instance.NORMAL_REQUEST)

  def test_handle_after_quit(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    self.mox.StubOutWithMock(inst._condition, 'notify')
    self.mox.StubOutWithMock(inst._condition, 'notify_all')

    self.proxy.start()
    self.proxy.quit()
    inst._condition.notify_all()

    self.mox.ReplayAll()
    inst.start()
    inst.quit()

    self.assertRaises(instance.CannotAcceptRequests,
                      inst.handle,
                      self.environ,
                      self.start_response,
                      self.url_map,
                      self.match,
                      self.request_id,
                      instance.NORMAL_REQUEST)
    self.mox.VerifyAll()

  def test_handle_while_quitting(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    self.mox.StubOutWithMock(inst._condition, 'notify')
    inst._num_outstanding_requests = 1

    self.proxy.start()
    self.mox.ReplayAll()
    inst.start()
    inst.quit(allow_async=True)
    self.mox.VerifyAll()

    self.assertRaises(instance.CannotAcceptRequests,
                      inst.handle,
                      self.environ,
                      self.start_response,
                      self.url_map,
                      self.match,
                      self.request_id,
                      instance.NORMAL_REQUEST)

  def test_handle_no_capacity(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=1)
    self.mox.StubOutWithMock(inst._condition, 'notify')
    inst._num_outstanding_requests = 1
    self.proxy.start()
    self.assertRaises(instance.CannotAcceptRequests,
                      inst.handle,
                      self.environ,
                      self.start_response,
                      self.url_map,
                      self.match,
                      self.request_id,
                      instance.NORMAL_REQUEST)

  def test_reserve_background_thread_success(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5,
                             max_background_threads=2)
    inst._started = True

    self.mox.ReplayAll()
    self.assertEqual(2, inst.remaining_background_thread_capacity)
    inst.reserve_background_thread()
    self.assertEqual(1, inst.remaining_background_thread_capacity)
    self.mox.VerifyAll()

  def test_reserve_background_thread_quitting(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5,
                             max_background_threads=2)
    inst._started = True
    inst._quitting = True

    self.mox.ReplayAll()
    self.assertEqual(2, inst.remaining_background_thread_capacity)
    inst.reserve_background_thread()
    self.assertEqual(1, inst.remaining_background_thread_capacity)
    self.mox.VerifyAll()

  def test_reserve_background_thread_no_capacity(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5,
                             max_background_threads=0)
    inst._started = True
    self.mox.ReplayAll()
    self.assertEqual(0, inst.remaining_background_thread_capacity)
    self.assertRaises(instance.CannotAcceptRequests,
                      inst.reserve_background_thread)
    self.mox.VerifyAll()
    self.assertEqual(0, inst.remaining_background_thread_capacity)

  def test_reserve_background_thread_not_started(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5,
                             max_background_threads=1)
    self.mox.ReplayAll()
    self.assertEqual(1, inst.remaining_background_thread_capacity)
    self.assertRaises(instance.CannotAcceptRequests,
                      inst.reserve_background_thread)
    self.mox.VerifyAll()
    self.assertEqual(1, inst.remaining_background_thread_capacity)

  def test_reserve_background_thread_quit(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5,
                             max_background_threads=1)
    inst._started = True
    inst._quit = True
    self.mox.ReplayAll()
    self.assertEqual(1, inst.remaining_background_thread_capacity)
    self.assertRaises(instance.CannotAcceptRequests,
                      inst.reserve_background_thread)
    self.mox.VerifyAll()
    self.assertEqual(1, inst.remaining_background_thread_capacity)

  def test_reserve_background_thread_not_ready(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5,
                             max_background_threads=2,
                             expect_ready_request=True)
    inst._started = True
    self.mox.ReplayAll()
    self.assertEqual(2, inst.remaining_background_thread_capacity)
    inst.reserve_background_thread()
    self.mox.VerifyAll()
    self.assertEqual(1, inst.remaining_background_thread_capacity)

  def test_wait_with_capacity(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=1)
    inst._started = True
    self.mox.StubOutWithMock(inst._condition, 'wait')
    self.mox.stubs.Set(time, 'time', lambda: 0)
    self.mox.ReplayAll()
    self.assertTrue(inst.wait(1))
    self.mox.VerifyAll()

  def test_wait_waiting_for_can_accept(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=1,
                             expect_ready_request=True)
    inst._started = True
    self.mox.StubOutWithMock(inst._condition, 'wait')
    self.time = 0
    self.mox.stubs.Set(time, 'time', lambda: self.time)

    def advance_time(*unused_args):
      self.time += 10

    inst._condition.wait(1).WithSideEffects(advance_time)
    self.mox.ReplayAll()
    self.assertFalse(inst.wait(1))
    self.mox.VerifyAll()

  def test_wait_timed_out_with_capacity(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=1)
    inst._started = True
    self.mox.StubOutWithMock(inst._condition, 'wait')
    self.mox.ReplayAll()
    self.assertTrue(inst.wait(0))
    self.mox.VerifyAll()

  def test_wait_without_capacity(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=0)
    inst._started = True
    self.mox.StubOutWithMock(inst._condition, 'wait')
    self.time = 0
    self.mox.stubs.Set(time, 'time', lambda: self.time)

    def advance_time(*unused_args):
      self.time += 10

    inst._condition.wait(1).WithSideEffects(advance_time)
    self.mox.ReplayAll()
    self.assertFalse(inst.wait(1))
    self.mox.VerifyAll()

  def test_wait_timed_out_without_capacity(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=0)
    inst._started = True
    self.mox.StubOutWithMock(inst._condition, 'wait')
    self.mox.ReplayAll()
    self.assertFalse(inst.wait(0))
    self.mox.VerifyAll()

  def test_wait_quit_while_starting(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    self.mox.StubOutWithMock(inst._condition, 'notify_all')
    self.proxy.start().WithSideEffects(inst.quit)

    self.proxy.quit()

    self.mox.ReplayAll()
    inst.start()
    self.mox.VerifyAll()
    self.assertFalse(inst.can_accept_requests)

  def test_wait_quit_while_waiting(self):
    self.mox.stubs.Set(time, 'time', lambda: 0)
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=0)
    self.mox.StubOutWithMock(inst._condition, 'wait')
    inst._condition.wait(1).WithSideEffects(lambda *unused_args: inst.quit())
    self.mox.ReplayAll()
    self.assertFalse(inst.wait(1))
    self.mox.VerifyAll()

  def test_health(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    self.mox.StubOutWithMock(inst._condition, 'notify_all')
    self.proxy.start()

    self.proxy.quit()
    inst._condition.notify_all()

    self.mox.ReplayAll()
    inst.start()
    self.assertTrue(inst.can_accept_requests)
    inst.set_health(False)
    self.assertFalse(inst.can_accept_requests)
    inst.set_health(True)
    self.assertTrue(inst.can_accept_requests)

  def test_quit(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    self.mox.StubOutWithMock(inst._condition, 'notify_all')
    self.proxy.start()

    self.proxy.quit()
    inst._condition.notify_all()

    self.mox.ReplayAll()
    inst.start()
    self.assertTrue(inst.can_accept_requests)
    inst.quit()
    self.mox.VerifyAll()
    self.assertFalse(inst.can_accept_requests)

  def test_quit_with_request(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    self.mox.StubOutWithMock(inst._condition, 'notify_all')
    self.proxy.start()

    self.mox.ReplayAll()
    inst.start()
    self.mox.VerifyAll()
    inst._num_outstanding_requests = 1
    self.assertRaises(instance.CannotQuitServingInstance,
                      inst.quit)

  def test_quit_with_request_force(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    self.mox.StubOutWithMock(inst._condition, 'notify_all')

    inst._num_outstanding_requests = 1
    self.proxy.start()
    self.proxy.quit()
    inst._condition.notify_all()

    self.mox.ReplayAll()
    inst.start()
    inst.quit(force=True)
    self.mox.VerifyAll()

  def test_quit_with_request_force_and_allow_async(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    self.mox.StubOutWithMock(inst._condition, 'notify_all')

    inst._num_outstanding_requests = 1
    self.proxy.start()
    self.proxy.quit()
    inst._condition.notify_all()

    self.mox.ReplayAll()
    inst.start()
    inst.quit(force=True, allow_async=True)
    self.mox.VerifyAll()

  def test_quit_with_request_allow_async(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    self.mox.StubOutWithMock(inst._condition, 'notify_all')

    inst._num_outstanding_requests = 1
    self.proxy.start()

    self.mox.ReplayAll()
    inst.start()
    inst.quit(allow_async=True)
    self.mox.VerifyAll()
    self.assertTrue(inst._quitting)

  def test_quit_shutdown(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    self.mox.StubOutWithMock(inst._condition, 'notify_all')

    inst._num_outstanding_requests = 1
    self.proxy.start()

    self.mox.ReplayAll()
    inst.start()
    inst.quit(expect_shutdown=True)
    self.mox.VerifyAll()
    self.assertTrue(inst._expecting_shutdown_request)
    self.assertFalse(inst._quitting)

  def test_get_latency_60s(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    now = time.time()
    inst._request_history = [(now, now+1), (now+2, now+4)]
    self.assertEqual(1.5, inst.get_latency_60s())

  def test_get_qps_60s(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    now = time.time()
    inst._request_history = [(now, now+1)] * 120
    self.assertEqual(2.0, inst.get_qps_60s())

  def test__trim_request_history_to_60s(self):
    inst = instance.Instance(self.request_data, 'name', self.proxy,
                             max_concurrent_requests=5)
    inst._request_history.append((0, 100))
    inst._request_history.append((1.0, 101))
    inst._request_history.append((1.2, 102))
    inst._request_history.append((2.5, 103))

    now = time.time()
    inst._request_history.append((now, 42))
    inst._request_history.append((now + 1, 43))
    inst._request_history.append((now + 3, 44))
    inst._request_history.append((now + 4, 45))

    inst._trim_request_history_to_60s()
    self.assertEqual([(now, 42), (now + 1, 43), (now + 3, 44), (now + 4, 45)],
                     list(inst._request_history))


if __name__ == '__main__':
  unittest.main()
