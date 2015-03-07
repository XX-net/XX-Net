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




"""A thread-safe queue in which removed objects put back to the front."""


import logging
import Queue
import threading
import time

logger = logging.getLogger('google.appengine.tools.requeue')


class ReQueue(object):
  """A special thread-safe queue.

  A ReQueue allows unfinished work items to be returned with a call to
  reput().  When an item is reput, task_done() should *not* be called
  in addition, getting an item that has been reput does not increase
  the number of outstanding tasks.

  This class shares an interface with Queue.Queue and provides the
  additional reput method.
  """

  def __init__(self,
               queue_capacity,
               requeue_capacity=None,
               queue_factory=Queue.Queue,
               get_time=time.time):
    """Initialize a ReQueue instance.

    Args:
      queue_capacity: The number of items that can be put in the ReQueue.
      requeue_capacity: The numer of items that can be reput in the ReQueue.
      queue_factory: Used for dependency injection.
      get_time: Used for dependency injection.
    """
    if requeue_capacity is None:
      requeue_capacity = queue_capacity

    self.get_time = get_time
    self.queue = queue_factory(queue_capacity)
    self.requeue = queue_factory(requeue_capacity)
    self.lock = threading.Lock()
    self.put_cond = threading.Condition(self.lock)
    self.get_cond = threading.Condition(self.lock)

  def _DoWithTimeout(self,
                     action,
                     exc,
                     wait_cond,
                     done_cond,
                     lock,
                     timeout=None,
                     block=True):
    """Performs the given action with a timeout.

    The action must be non-blocking, and raise an instance of exc on a
    recoverable failure.  If the action fails with an instance of exc,
    we wait on wait_cond before trying again.  Failure after the
    timeout is reached is propagated as an exception.  Success is
    signalled by notifying on done_cond and returning the result of
    the action.  If action raises any exception besides an instance of
    exc, it is immediately propagated.

    Args:
      action: A callable that performs a non-blocking action.
      exc: An exception type that is thrown by the action to indicate
        a recoverable error.
      wait_cond: A condition variable which should be waited on when
        action throws exc.
      done_cond: A condition variable to signal if the action returns.
      lock: The lock used by wait_cond and done_cond.
      timeout: A non-negative float indicating the maximum time to wait.
      block: Whether to block if the action cannot complete immediately.

    Returns:
      The result of the action, if it is successful.

    Raises:
      ValueError: If the timeout argument is negative.
    """
    if timeout is not None and timeout < 0.0:
      raise ValueError('\'timeout\' must not be a negative  number')
    if not block:
      timeout = 0.0
    result = None
    success = False
    start_time = self.get_time()
    lock.acquire()
    try:
      while not success:
        try:
          result = action()
          success = True
        except Exception, e:

          if not isinstance(e, exc):
            raise e
          if timeout is not None:
            elapsed_time = self.get_time() - start_time
            timeout -= elapsed_time
            if timeout <= 0.0:
              raise e
          wait_cond.wait(timeout)
    finally:
      if success:
        done_cond.notify()
      lock.release()
    return result

  def put(self, item, block=True, timeout=None):
    """Put an item into the requeue.

    Args:
      item: An item to add to the requeue.
      block: Whether to block if the requeue is full.
      timeout: Maximum on how long to wait until the queue is non-full.

    Raises:
      Queue.Full if the queue is full and the timeout expires.
    """
    def PutAction():
      self.queue.put(item, block=False)
    self._DoWithTimeout(PutAction,
                        Queue.Full,
                        self.get_cond,
                        self.put_cond,
                        self.lock,
                        timeout=timeout,
                        block=block)

  def reput(self, item, block=True, timeout=None):
    """Re-put an item back into the requeue.

    Re-putting an item does not increase the number of outstanding
    tasks, so the reput item should be uniquely associated with an
    item that was previously removed from the requeue and for which
    TaskDone has not been called.

    Args:
      item: An item to add to the requeue.
      block: Whether to block if the requeue is full.
      timeout: Maximum on how long to wait until the queue is non-full.

    Raises:
      Queue.Full is the queue is full and the timeout expires.
    """
    def ReputAction():
      self.requeue.put(item, block=False)
    self._DoWithTimeout(ReputAction,
                        Queue.Full,
                        self.get_cond,
                        self.put_cond,
                        self.lock,
                        timeout=timeout,
                        block=block)

  def get(self, block=True, timeout=None):
    """Get an item from the requeue.

    Args:
      block: Whether to block if the requeue is empty.
      timeout: Maximum on how long to wait until the requeue is non-empty.

    Returns:
      An item from the requeue.

    Raises:
      Queue.Empty if the queue is empty and the timeout expires.
    """
    def GetAction():

      try:
        result = self.requeue.get(block=False)


        self.requeue.task_done()
      except Queue.Empty:

        result = self.queue.get(block=False)

      return result
    return self._DoWithTimeout(GetAction,
                               Queue.Empty,
                               self.put_cond,
                               self.get_cond,
                               self.lock,
                               timeout=timeout,
                               block=block)

  def join(self):
    """Blocks until all of the items in the requeue have been processed."""
    self.queue.join()

  def task_done(self):
    """Indicate that a previously enqueued item has been fully processed."""
    self.queue.task_done()

  def empty(self):
    """Returns true if the requeue is empty."""
    return self.queue.empty() and self.requeue.empty()

  def get_nowait(self):
    """Try to get an item from the queue without blocking."""
    return self.get(block=False)

  def qsize(self):
    return self.queue.qsize() + self.requeue.qsize()
