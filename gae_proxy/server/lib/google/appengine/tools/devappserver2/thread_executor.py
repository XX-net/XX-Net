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
"""A thread-based executor that creates a new thread per work submission.

The advantage of this approach over ThreadPoolExecutor is:
1. there is no upper bound to the number of threads.
2. threads exit as soon as their work is done.

The disadvantage is the cost of one thread creation per work submission so
ThreadExecutor is only efficient when the cost of creating a thread is small
compared to the work being done.
"""



import threading

import google
from concurrent import futures


def _worker(future, fn, args, kwargs):
  if not future.set_running_or_notify_cancel():
    return

  try:
    result = fn(*args, **kwargs)
  except BaseException as e:
    future.set_exception(e)
  else:
    future.set_result(result)


class ThreadExecutor(futures.Executor):
  """A thread-based executor that creates a new thread per work submission."""

  def __init__(self):
    """Initializes a new ThreadExecutor instance."""
    self._shutdown = False
    self._shutdown_lock = threading.Lock()

  def submit(self, fn, *args, **kwargs):
    with self._shutdown_lock:
      if self._shutdown:
        raise RuntimeError('cannot schedule new futures after shutdown')

    f = futures.Future()
    t = threading.Thread(
        target=_worker, args=(f, fn, args, kwargs),
        name='Executor for %s args=%s kwargs=%s' % (fn, args, kwargs))
    t.start()
    return f
  submit.__doc__ = futures.Executor.submit.__doc__

  def shutdown(self, wait=True):
    with self._shutdown_lock:
      self._shutdown = True
  shutdown.__doc__ = futures.Executor.shutdown.__doc__
