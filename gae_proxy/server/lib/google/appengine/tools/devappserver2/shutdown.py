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
"""Helper functions to quit the development server."""



import logging
import os
import signal
import time


_shutting_down = False
_num_terminate_requests = 0


def async_quit():
  """Quits the development server asynchronously in an organized fashion.

  Requests in progress may be dropped.
  """
  global _shutting_down
  _shutting_down = True


def _async_terminate(*_):
  async_quit()
  global _num_terminate_requests
  _num_terminate_requests += 1
  if _num_terminate_requests == 1:
    logging.info('Shutting down.')
  if _num_terminate_requests >= 3:
    logging.error('Received third interrupt signal. Terminating.')
    os.abort()


def wait_until_shutdown():
  while not _shutting_down:
    try:
      time.sleep(1)
    except IOError:
      # On Windows time.sleep raises IOError when interrupted.
      pass


def install_signal_handlers():
  """Installs a signal handler for SIGTERM and SIGINT to do orderly shutdown."""
  signal.signal(signal.SIGTERM, _async_terminate)
  signal.signal(signal.SIGINT, _async_terminate)


def shutting_down():
  """Returns True when we are shutting down."""
  return _shutting_down
