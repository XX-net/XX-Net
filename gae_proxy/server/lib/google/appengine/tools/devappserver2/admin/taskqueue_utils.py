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
"""Shared utilities for dealing with taskqueue."""



import datetime

from google.appengine.api import apiproxy_stub_map
from google.appengine.api.taskqueue import taskqueue_service_pb


def _human_readable_eta(eta_usec):
  eta = datetime.datetime.utcfromtimestamp(eta_usec / 1e6)
  return eta.strftime('%Y/%m/%d %H:%M:%S')


def _timedelta_without_microseconds(delta):
  return datetime.timedelta(days=delta.days, seconds=delta.seconds)


def _human_readable_eta_delta(eta_usec):
  now = datetime.datetime.utcnow()
  eta = datetime.datetime.utcfromtimestamp(eta_usec / 1e6)
  if eta > now:
    return '%s from now' % _timedelta_without_microseconds(eta - now)
  else:
    return '%s ago' % _timedelta_without_microseconds(now - eta)


class QueueInfo(object):
  """Represents information about a Queue."""

  def __init__(self,
               name,
               mode,
               rate,
               bucket_size,
               tasks_in_queue,
               oldest_eta_usec):
    """Initializer for _QueueInfo.

    Args:
      name: The name of the queue e.g. "default".
      mode: A taskqueue_service_pb.TaskQueueMode constant representing the queue
          type e.g. PULL.
      rate: The execution rate of the queue as a string e.g. "10/s". May be None
          for pull queues.
      bucket_size: An int representing the size of the queues token bucket.
      tasks_in_queue: The number of tasks in the queue.
      oldest_eta_usec: The eta of the oldest task in the queue in microseconds
          from the epoch.
    """
    self.name = name
    self.mode = mode
    self.rate = rate
    self.bucket_size = bucket_size
    self.tasks_in_queue = tasks_in_queue
    if oldest_eta_usec == -1:  # No non-completed task in the queue.
      self.oldest_eta_usec = None
    else:
      self.oldest_eta_usec = oldest_eta_usec

  @property
  def human_readable_oldest_task_eta(self):
    if self.oldest_eta_usec:
      return _human_readable_eta(self.oldest_eta_usec)
    else:
      return None

  @property
  def human_readable_oldest_task_eta_delta(self):
    if self.oldest_eta_usec:
      return _human_readable_eta_delta(self.oldest_eta_usec)
    else:
      return None

  @classmethod
  def _from_queue_and_stats(cls, queue, queue_stats):
    """Return a new _QueueInfo given information from the taskqueue service.

    Args:
      queue: A taskqueue_service_pb.TaskQueueFetchQueuesResponse_Queue instance
          containing information about the queue.
      queue_stats: A
          taskqueue_service_pb.TaskQueueFetchQueueStatsResponse_QueueStats
          instance containing information about the queue.

    Returns:
      A _QueueInfo constructed using the provided queue information.
    """
    return cls(queue.queue_name(),
               queue.mode(),
               queue.user_specified_rate(),
               queue.bucket_capacity(),
               queue_stats.num_tasks(),
               queue_stats.oldest_eta_usec())


  @classmethod
  def get(cls, queue_names=frozenset()):
    """Returns a 2-tuple: (list of push _QueueInfo, list of pull _QueueInfo)."""
    fetch_queue_request = taskqueue_service_pb.TaskQueueFetchQueuesRequest()
    fetch_queue_request.set_max_rows(1000)
    fetch_queue_response = taskqueue_service_pb.TaskQueueFetchQueuesResponse()
    apiproxy_stub_map.MakeSyncCall('taskqueue',
                                   'FetchQueues',
                                   fetch_queue_request,
                                   fetch_queue_response)

    queue_stats_request = taskqueue_service_pb.TaskQueueFetchQueueStatsRequest()
    for queue in fetch_queue_response.queue_list():
      queue_stats_request.add_queue_name(queue.queue_name())
    queue_stats_response = (
        taskqueue_service_pb.TaskQueueFetchQueueStatsResponse())
    apiproxy_stub_map.MakeSyncCall('taskqueue',
                                   'FetchQueueStats',
                                   queue_stats_request,
                                   queue_stats_response)

    for queue, queue_stats in zip(
        fetch_queue_response.queue_list(),
        queue_stats_response.queuestats_list()):
      if queue_names and queue.queue_name() not in queue_names:
        continue
      yield cls._from_queue_and_stats(queue, queue_stats)
