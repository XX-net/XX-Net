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





"""Utilities for interacting with the Python Runtime."""






from __future__ import with_statement


import threading

from google.appengine.api import apiproxy_stub_map
from google.appengine.api.system import system_service_pb


def cpu_usage():
  """Returns a SystemStat describing cpu usage, expressed in mcycles.

  The returned object has the following accessors:

    - total(): total mcycles consumed by this instance
    - rate1m(): average mcycles consumed per second over the last minute
    - rate10m(): average mcycles consumed per second over the last ten minutes

  Functions for converting from mcycles to cpu-seconds are located in the quotas
  API.
  """
  return _GetSystemStats().cpu()


def memory_usage():
  """Returns a SystemStat describing memory usage, expressed in bytes.

  The returned object has the following accessors:

    - current(): memory currently used by this instance
    - average1m(): average memory use, over the last minute
    - average10m(): average memory use, over the last ten minutes
  """
  return _GetSystemStats().memory()


def _GetSystemStats():
  """Returns stats about the current instance."""
  request = system_service_pb.GetSystemStatsRequest()
  response = system_service_pb.GetSystemStatsResponse()
  apiproxy_stub_map.MakeSyncCall('system', 'GetSystemStats', request, response)
  return response


__shutdown_mutex = threading.Lock()
__shutdown_hook = None
__shuting_down = False


def is_shutting_down():
  """Returns true if the server is shutting down."""
  with __shutdown_mutex:
    shutting_down = __shuting_down
  return shutting_down


def set_shutdown_hook(hook):
  """Registers a function to be called when the server is shutting down.

  The shutdown hook will be called when the server shuts down.  Your code
  will have a short amount of time to save state and exit. The shutdown
  hook should interrupt any long running code you have, e.g. by calling
  apiproxy_stub_map.apiproxy.CancelApiCalls and/or raising an exception.

  Args:
    hook: A no-argument callable which will be called when the server is
    shutting down.

  Returns:
    The previously registered shutdown hook, or None if no hook was
    registered before.

  In some cases it may not be possible to run the shutdown hook
  before the server exits.
  """
  if hook is not None and not callable(hook):
    raise TypeError("hook must be callable, got %s" % hook.__class__)
  global __shutdown_hook
  with __shutdown_mutex:
    old_hook = __shutdown_hook
    __shutdown_hook = hook
  return old_hook


def __BeginShutdown():


  global __shuting_down
  with __shutdown_mutex:
    __shuting_down = True
    shutdown_hook = __shutdown_hook
  if shutdown_hook:
    shutdown_hook()
