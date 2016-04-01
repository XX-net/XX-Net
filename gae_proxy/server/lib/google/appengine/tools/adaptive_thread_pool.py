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
"""Provides thread-pool-like functionality for workers accessing App Engine.

The pool adapts to slow or timing out requests by reducing the number of
active workers, or increasing the number when requests latency reduces.
"""








import logging
import Queue
import sys
import threading
import time
import traceback

from google.appengine.tools.requeue import ReQueue

logger = logging.getLogger('google.appengine.tools.adaptive_thread_pool')


_THREAD_SHOULD_EXIT = '_THREAD_SHOULD_EXIT'




INITIAL_BACKOFF = 1.0


BACKOFF_FACTOR = 2.0


class Error(Exception):
  """Base-class for exceptions in this module."""


class WorkItemError(Error):
  """Error while processing a WorkItem."""


class RetryException(Error):
  """A non-fatal exception that indicates that a work item should be retried."""


def InterruptibleSleep(sleep_time):
  """Puts thread to sleep, checking this threads exit_flag four times a second.

  Args:
    sleep_time: Time to sleep.
  """
  slept = 0.0
  epsilon = .0001
  thread = threading.currentThread()
  while slept < sleep_time - epsilon:
    remaining = sleep_time - slept
    this_sleep_time = min(remaining, 0.25)
    time.sleep(this_sleep_time)
    slept += this_sleep_time
    if thread.exit_flag:
      return


class WorkerThread(threading.Thread):
  """A WorkerThread to execute WorkItems.

  Attributes:
    exit_flag: A boolean indicating whether this thread should stop
      its work and exit.
  """

  def __init__(self, thread_pool, thread_gate, name=None):
    """Initialize a WorkerThread instance.

    Args:
      thread_pool: An AdaptiveThreadPool instance.
      thread_gate: A ThreadGate instance.
      name: A name for this WorkerThread.
    """
    threading.Thread.__init__(self)




    self.setDaemon(True)

    self.exit_flag = False
    self.__error = None
    self.__traceback = None
    self.__thread_pool = thread_pool
    self.__work_queue = thread_pool.requeue
    self.__thread_gate = thread_gate
    if not name:
      self.__name = 'Anonymous_' + self.__class__.__name__
    else:
      self.__name = name

  def run(self):
    """Perform the work of the thread."""
    logger.debug('[%s] %s: started', self.getName(), self.__class__.__name__)


    try:
      self.WorkOnItems()
    except:
      self.SetError()

    logger.debug('[%s] %s: exiting', self.getName(), self.__class__.__name__)

  def SetError(self):
    """Sets the error and traceback information for this thread.

    This must be called from an exception handler.
    """
    if not self.__error:
      exc_info = sys.exc_info()
      self.__error = exc_info[1]
      self.__traceback = exc_info[2]
      logger.exception('[%s] %s:', self.getName(), self.__class__.__name__)

  def WorkOnItems(self):
    """Perform the work of a WorkerThread."""
    while not self.exit_flag:
      item = None
      self.__thread_gate.StartWork()

      try:

        status, instruction = WorkItem.FAILURE, ThreadGate.DECREASE


        try:
          if self.exit_flag:

            instruction = ThreadGate.HOLD
            break


          try:
            item = self.__work_queue.get(block=True, timeout=1.0)
          except Queue.Empty:

            instruction = ThreadGate.HOLD
            continue
          if item == _THREAD_SHOULD_EXIT or self.exit_flag:


            status, instruction = WorkItem.SUCCESS, ThreadGate.HOLD
            break

          logger.debug('[%s] Got work item %s', self.getName(), item)

          status, instruction = item.PerformWork(self.__thread_pool)
        except RetryException:
          status, instruction = WorkItem.RETRY, ThreadGate.HOLD
        except:
          self.SetError()
          raise

      finally:

        try:

          if item:
            if status == WorkItem.SUCCESS:
              self.__work_queue.task_done()
            elif status == WorkItem.RETRY:


              try:
                self.__work_queue.reput(item, block=False)
              except Queue.Full:
                logger.error('[%s] Failed to reput work item.', self.getName())
                raise Error('Failed to reput work item')
            else:
              if not self.__error:
                if item.error:
                  self.__error = item.error
                  self.__traceback = item.traceback
                else:

                  self.__error = WorkItemError(
                      'Fatal error while processing %s' % item)

                raise self.__error

        finally:
          self.__thread_gate.FinishWork(instruction=instruction)

  def CheckError(self):
    """If an error is present, then log it."""
    if self.__error:
      logger.error('Error in %s: %s', self.getName(), self.__error)
      if self.__traceback:
        logger.debug('%s', ''.join(traceback.format_exception(
            self.__error.__class__,
            self.__error,
            self.__traceback)))

  def __str__(self):
    return self.__name


class AdaptiveThreadPool(object):
  """A thread pool which processes WorkItems from a queue.

  Attributes:
    requeue: The requeue instance which holds work items for this
      thread pool.
  """

  def __init__(self,
               num_threads,
               queue_size=None,
               base_thread_name=None,
               worker_thread_factory=WorkerThread,
               queue_factory=Queue.Queue):
    """Initialize an AdaptiveThreadPool.

    An adaptive thread pool executes WorkItems using a number of
    WorkerThreads.  WorkItems represent items of work that may
    succeed, soft fail, or hard fail. In addition, a completed work
    item can signal this AdaptiveThreadPool to enable more or fewer
    threads.  Initially one thread is active.  Soft failures are
    reqeueud to be retried.  Hard failures cause this
    AdaptiveThreadPool to shut down entirely.  See the WorkItem class
    for more details.

    Args:
      num_threads: The number of threads to use.
      queue_size: The size of the work item queue to use.
      base_thread_name: A string from which worker thread names are derived.
      worker_thread_factory: A factory which procudes WorkerThreads.
      queue_factory: Used for dependency injection.
    """
    if queue_size is None:
      queue_size = num_threads
    self.requeue = ReQueue(queue_size, queue_factory=queue_factory)
    self.__thread_gate = ThreadGate(num_threads)
    self.__num_threads = num_threads
    self.__threads = []
    for i in xrange(num_threads):
      thread = worker_thread_factory(self, self.__thread_gate)
      if base_thread_name:
        base = base_thread_name
      else:
        base = thread.__class__.__name__
      thread.name = '%s-%d' % (base, i)
      self.__threads.append(thread)
      thread.start()

  def num_threads(self):
    """Return the number of threads in this thread pool."""
    return self.__num_threads

  def Threads(self):
    """Yields the registered threads."""
    for thread in self.__threads:
      yield thread

  def SubmitItem(self, item, block=True, timeout=0.0):
    """Submit a WorkItem to the AdaptiveThreadPool.

    Args:
      item: A WorkItem instance.
      block: Whether to block on submitting if the submit queue is full.
      timeout: Time wait for room in the queue if block is True, 0.0 to
        block indefinitely.

    Raises:
      Queue.Full if the submit queue is full.
    """
    self.requeue.put(item, block=block, timeout=timeout)

  def QueuedItemCount(self):
    """Returns the number of items currently in the queue."""
    return self.requeue.qsize()

  def Shutdown(self):
    """Shutdown the thread pool.

    Tasks may remain unexecuted in the submit queue.
    """

    while not self.requeue.empty():
      try:
        unused_item = self.requeue.get_nowait()
        self.requeue.task_done()
      except Queue.Empty:

        pass
    for thread in self.__threads:
      thread.exit_flag = True
      self.requeue.put(_THREAD_SHOULD_EXIT)
    self.__thread_gate.EnableAllThreads()

  def Wait(self):
    """Wait until all work items have been completed."""
    self.requeue.join()

  def JoinThreads(self):
    """Wait for all threads to exit."""
    for thread in self.__threads:
      logger.debug('Waiting for %s to exit' % str(thread))
      thread.join()

  def CheckErrors(self):
    """Output logs for any errors that occurred in the worker threads."""
    for thread in self.__threads:
      thread.CheckError()


class ThreadGate(object):
  """Manage the number of active worker threads.

  The ThreadGate limits the number of threads that are simultaneously
  active in order to implement adaptive rate control.

  Initially the ThreadGate allows only one thread to be active.  For
  each successful work item, another thread is activated and for each
  failed item, the number of active threads is reduced by one.  When only
  one thread is active, failures will cause exponential backoff.

  For example, a ThreadGate instance, thread_gate can be used in a number
  of threads as so:

  # Block until this thread is enabled for work.
  thread_gate.StartWork()
  try:
    status = DoSomeWorkInvolvingLimitedSharedResources()
    succeeded = IsStatusGood(status)
    badly_failed = IsStatusVeryBad(status)
  finally:
    if succeeded:
      # Succeeded, add more simultaneously enabled threads to the task.
      thread_gate.FinishWork(instruction=ThreadGate.INCREASE)
    elif badly_failed:
      # Failed, or succeeded but with high resource load, reduce number of
      # workers.
      thread_gate.FinishWork(instruction=ThreadGate.DECREASE)
    else:
      # We succeeded, but don't want to add more workers to the task.
      thread_gate.FinishWork(instruction=ThreadGate.HOLD)

  the thread_gate will enable and disable/backoff threads in response to
  resource load conditions.

  StartWork can block indefinitely. FinishWork, while not
  lock-free, should never block absent a demonic scheduler.
  """


  INCREASE = 'increase'
  HOLD = 'hold'
  DECREASE = 'decrease'

  def __init__(self,
               num_threads,
               sleep=InterruptibleSleep):
    """Constructor for ThreadGate instances.

    Args:
      num_threads: The total number of threads using this gate.
      sleep: Used for dependency injection.
    """
    self.__enabled_count = 1

    self.__lock = threading.Lock()

    self.__thread_semaphore = threading.Semaphore(self.__enabled_count)
    self.__num_threads = num_threads
    self.__backoff_time = 0
    self.__sleep = sleep

  def num_threads(self):
    return self.__num_threads

  def EnableThread(self):
    """Enable one more worker thread."""
    self.__lock.acquire()
    try:
      self.__enabled_count += 1
    finally:
      self.__lock.release()
    self.__thread_semaphore.release()

  def EnableAllThreads(self):
    """Enable all worker threads."""
    for unused_idx in xrange(self.__num_threads - self.__enabled_count):
      self.EnableThread()

  def StartWork(self):
    """Starts a critical section in which the number of workers is limited.

    Starts a critical section which allows self.__enabled_count
    simultaneously operating threads. The critical section is ended by
    calling self.FinishWork().
    """

    self.__thread_semaphore.acquire()

    if self.__backoff_time > 0.0:
      if not threading.currentThread().exit_flag:
        logger.info('[%s] Backing off due to errors: %.1f seconds',
                    threading.currentThread().getName(),
                    self.__backoff_time)
        self.__sleep(self.__backoff_time)

  def FinishWork(self, instruction=None):
    """Ends a critical section started with self.StartWork()."""
    if not instruction or instruction == ThreadGate.HOLD:

      self.__thread_semaphore.release()

    elif instruction == ThreadGate.INCREASE:

      if self.__backoff_time > 0.0:
        logger.info('Resetting backoff to 0.0')
        self.__backoff_time = 0.0
      do_enable = False
      self.__lock.acquire()
      try:

        if self.__num_threads > self.__enabled_count:
          do_enable = True
          self.__enabled_count += 1
      finally:
        self.__lock.release()

      if do_enable:
        logger.debug('Increasing active thread count to %d',
                     self.__enabled_count)
        self.__thread_semaphore.release()

      self.__thread_semaphore.release()

    elif instruction == ThreadGate.DECREASE:
      do_disable = False
      self.__lock.acquire()
      try:

        if self.__enabled_count > 1:
          do_disable = True
          self.__enabled_count -= 1
        else:
          if self.__backoff_time == 0.0:
            self.__backoff_time = INITIAL_BACKOFF
          else:
            self.__backoff_time *= BACKOFF_FACTOR
      finally:
        self.__lock.release()

        if do_disable:
          logger.debug('Decreasing the number of active threads to %d',
                       self.__enabled_count)

        else:
          self.__thread_semaphore.release()


class WorkItem(object):
  """Holds a unit of work."""


  SUCCESS = 'success'
  RETRY = 'retry'
  FAILURE = 'failure'

  def __init__(self, name):
    self.__name = name

  def PerformWork(self, thread_pool):
    """Perform the work of this work item and report the results.

    Args:
      thread_pool: The AdaptiveThreadPool instance associated with this
        thread.

    Returns:
      A tuple (status, instruction) of the work status and an instruction
      for the ThreadGate.
    """
    raise NotImplementedError

  def __str__(self):
    return self.__name
