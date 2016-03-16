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
"""Tests for google.appengine.tools.devappserver2.scheduled_executor."""

import threading
import time
import unittest

from google.appengine.tools.devappserver2 import scheduled_executor


class FakeThreadPool(object):
  def submit(self, runnable, *args, **kwargs):
    runnable(*args, **kwargs)


class ScheduledExecutorTest(unittest.TestCase):

  def setUp(self):
    self.executor = scheduled_executor.ScheduledExecutor(FakeThreadPool())
    self.executor.start()

  def tearDown(self):
    self.executor.quit()

  def test_add_and_execute(self):
    event = threading.Event()
    self.executor.add_event(event.set, time.time() + 3)
    event.wait(5)
    self.assertTrue(event.is_set())

  def test_add_two_with_same_eta_and_execute(self):
    event = threading.Event()
    event2 = threading.Event()
    eta = time.time() + 3
    self.executor.add_event(event.set, eta)
    self.executor.add_event(event2.set, eta)
    event.wait(5)
    event2.wait(5)
    self.assertTrue(event.is_set())
    self.assertTrue(event2.is_set())

  def test_add_and_update_and_execute(self):
    event = threading.Event()
    self.executor.add_event(event.set, time.time() + 3, 0)
    self.executor.update_event(time.time() + 1000, 0)
    event.wait(5)
    self.assertFalse(event.is_set())

  def test_add_and_update_different_event_and_execute(self):
    event = threading.Event()
    self.executor.add_event(event.set, time.time() + 3, 1)
    self.executor.update_event(time.time() + 1000, 0)
    event.wait(5)
    self.assertTrue(event.is_set())


if __name__ == '__main__':
  unittest.main()
