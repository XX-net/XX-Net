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
"""Tests for google.appengine.tools.devappserver2.shutdown."""

import os
import signal
import time
import unittest

import google

import mox

from google.appengine.tools.devappserver2 import shutdown


class ShutdownTest(unittest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(os, 'abort')
    shutdown._shutting_down = False
    shutdown._num_terminate_requests = 0
    self._sigint_handler = signal.getsignal(signal.SIGINT)
    self._sigterm_handler = signal.getsignal(signal.SIGTERM)

  def tearDown(self):
    self.mox.UnsetStubs()
    signal.signal(signal.SIGINT, self._sigint_handler)
    signal.signal(signal.SIGTERM, self._sigterm_handler)

  def test_async_quit(self):
    self.mox.ReplayAll()
    shutdown.async_quit()
    self.assertTrue(shutdown._shutting_down)
    self.mox.VerifyAll()

  def test_async_terminate(self):
    self.mox.ReplayAll()
    shutdown._async_terminate()
    self.assertTrue(shutdown._shutting_down)
    shutdown._async_terminate()
    self.mox.VerifyAll()

  def test_async_terminate_abort(self):
    os.abort()
    self.mox.ReplayAll()
    shutdown._async_terminate()
    self.assertTrue(shutdown._shutting_down)
    shutdown._async_terminate()
    shutdown._async_terminate()
    self.mox.VerifyAll()

  def test_install_signal_handlers(self):
    shutdown.install_signal_handlers()
    self.assertEqual(shutdown._async_terminate, signal.getsignal(signal.SIGINT))
    self.assertEqual(shutdown._async_terminate,
                     signal.getsignal(signal.SIGTERM))

  def test_wait_until_shutdown(self):
    self.mox.StubOutWithMock(time, 'sleep')
    time.sleep(1).WithSideEffects(lambda _: shutdown.async_quit())
    self.mox.ReplayAll()
    shutdown.wait_until_shutdown()
    self.mox.VerifyAll()

  def test_wait_until_shutdown_raise_interrupted_io(self):

    def quit_and_raise(*_):
      shutdown.async_quit()
      raise IOError

    self.mox.StubOutWithMock(time, 'sleep')
    time.sleep(1).WithSideEffects(quit_and_raise)
    self.mox.ReplayAll()
    shutdown.wait_until_shutdown()
    self.mox.VerifyAll()


if __name__ == '__main__':
  unittest.main()
