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




"""Shutdown handler.

Provides a Python 2.7 method which invokes a user-specified shutdown hook.
"""








import logging
import sys
import traceback

from google.appengine.api.logservice import logservice
from google.appengine.api.runtime import runtime as runtime_api
from google.appengine.runtime import request_environment


def Handle(environ):
  """Handles a shutdown request.

  Args:
    environ: A dict containing the environ for this request (i.e. for
        os.environ).

  Returns:
    A tuple with:
      A dict containing:
        error: App Engine error code. Always 0 for OK.
        response_code: The HTTP response code. Always 200.
        logs: A list of tuples (timestamp_usec, severity, message) of log
            entries.  timestamp_usec is a long, severity is int and message is
            str.  Severity levels are 0..4 for Debug, Info, Warning, Error,
            Critical.
      A tuple containing the result of sys.exc_info() if an exception occured,
      or None.
  """
  response = {}
  response['error'] = 0
  response['response_code'] = 200
  exc = None
  try:
    error = logservice.LogsBuffer()
    request_environment.current_request.Init(error, environ)
    getattr(runtime_api, '__BeginShutdown')()
  except:
    exc = sys.exc_info()
    message = ''.join(traceback.format_exception(exc[0], exc[1],
                                                 exc[2].tb_next))
    logging.info('Raised exception in shutdown handler:\n' + message)
  finally:
    request_environment.current_request.Clear()
    response['logs'] = error.parse_logs()
    return (response, exc)
