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
"""Schedule callables to run at a particular time."""

import heapq
import threading
import time


class _Event(object):

  def __init__(self, eta, runnable, key):
    self._eta = eta
    self._runnable = runnable
    self._key = key

  def __lt__(self, other):
    return self.eta < other.eta

  def cancel(self):
    self._runnable = None

  @property
  def eta(self):
    return self._eta

  @property
  def key(self):
    return self._key

  @property
  def cancelled(self):
    return self._runnable is None

  def copy(self, new_eta):
    return _Event(new_eta, self._runnable, self.key)

  def run(self):
    self._runnable()


class ScheduledExecutor(object):
  """An executor that supports scheduling."""

  def __init__(self, thread_pool):
    self._thread_pool = thread_pool
    self._quit_event = threading.Event()
    self._work_ready_condition = threading.Condition()
    self._queue = []
    self._key_to_events = {}
    self._worker_thread = threading.Thread(
        target=self._loop_and_run_scheduled_events, name="Scheduled Executor")

  def start(self):
    self._worker_thread.start()

  def quit(self):
    self._quit_event.set()
    with self._work_ready_condition:
      self._work_ready_condition.notify()

  def add_event(self, runnable, eta, key=None):
    """Schedule an event to be run.

    Args:
      runnable: A callable to run.
      eta: An int containing when to run runnable in seconds since the epoch.
      key: An optional key that implements __hash__ that can be passed to
          update_event.
    """
    event = _Event(eta, runnable, key)
    with self._work_ready_condition:
      if key is not None:
        self._key_to_events[key] = event
      self._enqueue_event(event)

  def update_event(self, eta, key):
    """Modify when an event should be run.

    Args:
      eta: An int containing when to schedule the event in seconds since the
          epoch.
      key: The key of the event to modify.
    """
    with self._work_ready_condition:
      old_event = self._key_to_events.get(key)
      if old_event:
        event = old_event.copy(eta)
        old_event.cancel()
        self._key_to_events[key] = event
        self._enqueue_event(event)

  def _enqueue_event(self, event):
    # Must be called with _work_ready_condition acquired.
    if self._queue:
      old_next_event_eta = self._queue[0].eta
    else:
      old_next_event_eta = event.eta + 1
    heapq.heappush(self._queue, event)
    if event.eta < old_next_event_eta:
      self._work_ready_condition.notify()

  def _loop_and_run_scheduled_events(self):
    with self._work_ready_condition:
      while not self._quit_event.is_set():
        now = time.time()
        while self._queue and self._queue[0].eta <= now:
          event = heapq.heappop(self._queue)
          if not event.cancelled:
            # Only remove uncancelled events because when an Event is cancelled,
            # its entry in _key_to_events is replaced with the replacement
            # Event.
            if event.key:
              del self._key_to_events[event.key]
            self._work_ready_condition.release()
            self._thread_pool.submit(event.run)
            self._work_ready_condition.acquire()
          now = time.time()
        if self._queue:
          self._work_ready_condition.wait(self._queue[0].eta - now)
        else:
          self._work_ready_condition.wait()
