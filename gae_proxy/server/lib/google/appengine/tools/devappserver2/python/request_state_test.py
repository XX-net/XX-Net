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
"""Tests for google.appengine.tools.devappserver2.python.request_state."""

import ctypes
import threading
import unittest

import google

import mox

from google.appengine.tools.devappserver2.python import request_state


class CtypesComparator(mox.Comparator):

  def __init__(self, lhs):
    self.lhs = lhs.value

  def equals(self, rhs):
    return self.lhs == rhs.value


class RequestStateTest(unittest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(ctypes.pythonapi, 'PyThreadState_SetAsyncExc')
    self.request_state = request_state.RequestState('id')

  def tearDown(self):
    self.mox.UnsetStubs()
    request_state._request_states = {}

  def test_start_and_end_thread(self):
    self.request_state._threads = set()
    self.request_state.start_thread()
    self.assertEquals(set([threading.current_thread().ident]),
                      self.request_state._threads)
    self.request_state.end_thread()
    self.assertEquals(set(), self.request_state._threads)

  def test_inject_exception(self):
    ctypes.pythonapi.PyThreadState_SetAsyncExc(
        CtypesComparator(ctypes.c_long(threading.current_thread().ident)),
        CtypesComparator(ctypes.py_object(Exception)))
    self.mox.ReplayAll()
    self.request_state.inject_exception(Exception)
    self.mox.VerifyAll()

  def test_end_request(self):

    def remove_fake_thread():
      self.request_state._threads.remove('fake thread id')

    self.mox.StubOutWithMock(self.request_state._condition, 'wait')
    self.request_state._threads.add('fake thread id')
    self.request_state._condition.wait().WithSideEffects(remove_fake_thread)
    self.mox.ReplayAll()
    self.request_state.end_request()
    self.mox.VerifyAll()

  def test_start_request_function(self):
    request_state.start_request('id')
    self.assertEqual(1, len(request_state.get_request_states()))
    self.assertEqual('id', request_state.get_request_state('id').request_id)

  def test_end_request_function(self):
    request_state._request_states = {'id': self.request_state}
    self.mox.StubOutWithMock(self.request_state, 'end_request')
    self.request_state.end_request()
    self.mox.ReplayAll()
    request_state.end_request('id')
    self.mox.VerifyAll()
    self.assertEqual([], request_state.get_request_states())

  def test_get_request_states(self):
    request_state.start_request('1')
    request_state.start_request('2')
    request_state.start_request('3')
    self.assertEqual(3, len(request_state.get_request_states()))
    self.assertItemsEqual(
        [request_state.get_request_state(request_id) for
         request_id in ['1', '2', '3']], request_state.get_request_states())

if __name__ == '__main__':
  unittest.main()
