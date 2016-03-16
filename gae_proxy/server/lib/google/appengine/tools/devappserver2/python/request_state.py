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
"""Tracking of active requests."""

import ctypes
import threading


class RequestState(object):
  """State for a single request."""

  def __init__(self, request_id):
    self.request_id = request_id
    self._threads = set([threading.current_thread().ident])
    self._condition = threading.Condition()

  def start_thread(self):
    """Records the start of a user-created thread as part of this request."""
    thread_id = threading.current_thread().ident
    with self._condition:
      self._threads.add(thread_id)

  def end_thread(self):
    """Records the end of a user-created thread as part of this request."""
    thread_id = threading.current_thread().ident
    with self._condition:
      self._threads.remove(thread_id)
      self._condition.notify()

  def end_request(self):
    """Ends the request and blocks until all threads for this request finish."""
    thread_id = threading.current_thread().ident
    with self._condition:
      self._threads.remove(thread_id)
      while self._threads:
        self._condition.wait()

  def inject_exception(self, exception):
    """Injects an exception to all threads running as part of this request."""
    with self._condition:
      thread_ids = list(self._threads)
    for thread_id in thread_ids:
      ctypes.pythonapi.PyThreadState_SetAsyncExc(
          ctypes.c_long(thread_id), ctypes.py_object(exception))

_request_states = {}
_request_states_lock = threading.RLock()


def start_request(request_id):
  """Starts a request with the provided request id."""
  with _request_states_lock:
    _request_states[request_id] = RequestState(request_id)


def end_request(request_id):
  """Ends the request with the provided request id."""
  with _request_states_lock:
    request_state = _request_states[request_id]
  request_state.end_request()
  with _request_states_lock:
    del _request_states[request_id]


def get_request_state(request_id):
  """Returns the RequestState for the provided request id."""
  with _request_states_lock:
    return _request_states[request_id]


def get_request_states():
  """Returns a list of RequestState instances for all current requests."""
  with _request_states_lock:
    return _request_states.values()
