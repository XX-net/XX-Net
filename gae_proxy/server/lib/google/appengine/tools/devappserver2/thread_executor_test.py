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
"""Tests for google.apphosting.tools.devappserver2.threadexecutor."""



import unittest

from google.appengine.tools.devappserver2 import thread_executor


class TestThreadExecutor(unittest.TestCase):
  """Tests for thread_executor.ThreadExecutor."""

  def setUp(self):
    self.executor = thread_executor.ThreadExecutor()

  def tearDown(self):
    self.executor.shutdown()

  def test_success(self):
    self.assertEqual(32, self.executor.submit(pow, 2, 5).result())

  def test_exception(self):
    self.assertIsInstance(self.executor.submit(divmod, 2, 0).exception(),
                          ZeroDivisionError)

if __name__ == '__main__':
  unittest.main()
