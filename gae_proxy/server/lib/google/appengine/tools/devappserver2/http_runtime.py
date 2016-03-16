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
"""Serves content for "script" handlers using an HTTP runtime.

http_runtime supports two ways to start the runtime instance.

START_PROCESS sends the runtime_config protobuf (serialized and base64 encoded
as not all platforms support binary data over stdin) to the runtime instance
over stdin and requires the runtime instance to send the port it is listening on
over stdout.

START_PROCESS_FILE creates two temporary files and adds the paths of both files
to the runtime instance command line. The first file is written by http_runtime
with the runtime_config proto (serialized); the runtime instance is expected to
delete the file after reading it. The second file is written by the runtime
instance with the port it is listening on (the line must be newline terminated);
http_runtime is expected to delete the file after reading it.

START_PROCESS_REVERSE Works by passing config in via a file and passes the HTTP
port number created in http_runtime.py as an environment variable to the runtime
process.

START_PROCESS_REVERSE_NO_FILE equivalent to START_PROCESS, but passes the HTTP
port number created in http_runtime.py as an environment variable to the runtime
process.

"""



import base64
import logging
import os
import subprocess
import sys
import threading
import time

import portpicker

from google.appengine.tools.devappserver2 import application_configuration
from google.appengine.tools.devappserver2 import http_proxy
from google.appengine.tools.devappserver2 import http_runtime_constants
from google.appengine.tools.devappserver2 import instance
from google.appengine.tools.devappserver2 import safe_subprocess
from google.appengine.tools.devappserver2 import tee

# These are different approaches to passing configuration into the runtimes
# and getting configuration back out of the runtime.

# Works by passing config in via stdin and reading the port over stdout.
START_PROCESS = -1

# Works by passing config in via a file and reading the port over a file.
START_PROCESS_FILE = -2

# Works by passing config in via a file and passes the port via
# a command line flag.
START_PROCESS_REVERSE = -3

# Works by passing config in via stdin and passes the port in via
# an environment variable.
START_PROCESS_REVERSE_NO_FILE = -4


def _sleep_between_retries(attempt, max_attempts, sleep_base):
  """Sleep between retry attempts.

  Do an exponential backoff between retry attempts on an operation. The general
  pattern for use is:
    for attempt in range(max_attempts):
      # Try operation, either return or break on success
      _sleep_between_retries(attempt, max_attempts, sleep_base)

  Args:
    attempt: Which attempt just failed (0 based).
    max_attempts: The maximum number of attempts that will be made.
    sleep_base: How long in seconds to sleep between the first and second
      attempt (the time will be doubled between each successive attempt). The
      value may be any numeric type that is convertible to float (complex
      won't work but user types that are sufficiently numeric-like will).
  """
  # Don't sleep after the last attempt as we're about to give up.
  if attempt < (max_attempts - 1):
    time.sleep((2 ** attempt) * sleep_base)


def _remove_retry_sharing_violation(path, max_attempts=10, sleep_base=.125):
  """Removes a file (with retries on Windows for sharing violations).

  Args:
    path: The filesystem path to remove.
    max_attempts: The maximum number of attempts to try to remove the path
      before giving up.
    sleep_base: How long in seconds to sleep between the first and second
      attempt (the time will be doubled between each successive attempt). The
      value may be any numeric type that is convertible to float (complex
      won't work but user types that are sufficiently numeric-like will).

  Raises:
    WindowsError: When an error other than a sharing violation occurs.
  """
  if sys.platform == 'win32':
    for attempt in range(max_attempts):
      try:
        os.remove(path)
        break
      except WindowsError as e:
        import winerror
        # Sharing violations are expected to occasionally occur when the runtime
        # instance is context swapped after writing the port but before closing
        # the file. Ignore these and try again.
        if e.winerror != winerror.ERROR_SHARING_VIOLATION:
          raise
      _sleep_between_retries(attempt, max_attempts, sleep_base)
    else:
      logging.warn('Unable to delete %s', path)
  else:
    os.remove(path)


def get_vm_environment_variables(module_configuration, runtime_config):
  """Returns VM-specific environment variables."""
  keys_values = [
      ('API_HOST', runtime_config.api_host),
      ('API_PORT', runtime_config.api_port),
      ('GAE_LONG_APP_ID', module_configuration.application_external_name),
      ('GAE_PARTITION', module_configuration.partition),
      ('GAE_MODULE_NAME', module_configuration.module_name),
      ('GAE_MODULE_VERSION', module_configuration.major_version),
      ('GAE_MINOR_VERSION', module_configuration.minor_version),
      ('GAE_MODULE_INSTANCE', runtime_config.instance_id),
      ('GAE_SERVER_PORT', runtime_config.server_port),
      ('MODULE_YAML_PATH', os.path.basename(module_configuration.config_path)),
      ('SERVER_SOFTWARE', http_runtime_constants.SERVER_SOFTWARE),
  ]
  for entry in runtime_config.environ:
    keys_values.append((entry.key, entry.value))

  return {key: str(value) for key, value in keys_values}


class HttpRuntimeProxy(instance.RuntimeProxy):
  """Manages a runtime subprocess used to handle dynamic content."""

  _VALID_START_PROCESS_FLAVORS = [START_PROCESS, START_PROCESS_FILE,
                                  START_PROCESS_REVERSE,
                                  START_PROCESS_REVERSE_NO_FILE]

  # TODO: Determine if we can always use SIGTERM.
  # Set this to True to quit with SIGTERM rather than SIGKILL




  _quit_with_sigterm = False

  @classmethod
  def stop_runtimes_with_sigterm(cls, quit_with_sigterm):
    """Configures the http_runtime module to kill the runtimes with SIGTERM.

    Args:
      quit_with_sigterm: True to enable stopping runtimes with SIGTERM.

    Returns:
      The previous value.
    """
    previous_quit_with_sigterm = cls._quit_with_sigterm
    cls._quit_with_sigterm = quit_with_sigterm
    return previous_quit_with_sigterm

  def __init__(self, args, runtime_config_getter, module_configuration,
               env=None, start_process_flavor=START_PROCESS,
               extra_args_getter=None):
    """Initializer for HttpRuntimeProxy.

    Args:
      args: Arguments to use to start the runtime subprocess.
      runtime_config_getter: A function that can be called without arguments
          and returns the runtime_config_pb2.Config containing the configuration
          for the runtime.
      module_configuration: An application_configuration.ModuleConfiguration
          instance respresenting the configuration of the module that owns the
          runtime.
      env: A dict of environment variables to pass to the runtime subprocess.
      start_process_flavor: Which version of start process to start your
        runtime process. Supported flavors are START_PROCESS, START_PROCESS_FILE
        START_PROCESS_REVERSE and START_PROCESS_REVERSE_NO_FILE
      extra_args_getter: A function that can be called with a port number picked
          by this http_runtime,
          and returns the extra command line parameter that refers to the port
          number.

    Raises:
      ValueError: An unknown value for start_process_flavor was used.
    """
    super(HttpRuntimeProxy, self).__init__()
    self._process = None
    self._process_lock = threading.Lock()  # Lock to guard self._process.
    self._stderr_tee = None
    self._runtime_config_getter = runtime_config_getter
    self._extra_args_getter = extra_args_getter
    self._args = args
    self._module_configuration = module_configuration
    self._env = env
    # This sets environment variables at the process level and works for
    # Java and Go. Python hacks os.environ to not really return the environment
    # variables, so Python needs to set these elsewhere.
    runtime_config = self._runtime_config_getter()
    if runtime_config.vm:
      self._env.update(get_vm_environment_variables(
          self._module_configuration, runtime_config))

    if start_process_flavor not in self._VALID_START_PROCESS_FLAVORS:
      raise ValueError('Invalid start_process_flavor.')
    self._start_process_flavor = start_process_flavor
    self._proxy = None

  def _get_instance_logs(self):
    # Give the runtime process a bit of time to write to stderr.
    time.sleep(0.1)
    return self._stderr_tee.get_buf()

  def _instance_died_unexpectedly(self):
    with self._process_lock:
      # If self._process is None then the process hasn't started yet, so it
      # it hasn't died either. Otherwise, if self._process.poll() returns a
      # non-None value then the process has exited and the poll() value is
      # its return code.
      return self._process and self._process.poll() is not None

  def handle(self, environ, start_response, url_map, match, request_id,
             request_type):
    """Serves this request by forwarding it to the runtime process.

    Args:
      environ: An environ dict for the request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.
      url_map: An appinfo.URLMap instance containing the configuration for the
          handler matching this request.
      match: A re.MatchObject containing the result of the matched URL pattern.
      request_id: A unique string id associated with the request.
      request_type: The type of the request. See instance.*_REQUEST module
          constants.

    Yields:
      A sequence of strings containing the body of the HTTP response.
    """

    return self._proxy.handle(environ, start_response, url_map, match,
                              request_id, request_type)

  def _read_start_process_file(self, max_attempts=10, sleep_base=.125):
    """Read the single line response expected in the start process file.

    The START_PROCESS_FILE flavor uses a file for the runtime instance to
    report back the port it is listening on. We can't rely on EOF semantics
    as that is a race condition when the runtime instance is simultaneously
    writing the file while the devappserver process is reading it; rather we
    rely on the line being terminated with a newline.

    Args:
      max_attempts: The maximum number of attempts to read the line.
      sleep_base: How long in seconds to sleep between the first and second
        attempt (the time will be doubled between each successive attempt). The
        value may be any numeric type that is convertible to float (complex
        won't work but user types that are sufficiently numeric-like will).

    Returns:
      If a full single line (as indicated by a newline terminator) is found, all
      data read up to that point is returned; return an empty string if no
      newline is read before the process exits or the max number of attempts are
      made.
    """
    try:
      for attempt in range(max_attempts):
        # Yes, the final data may already be in the file even though the
        # process exited. That said, since the process should stay alive
        # if it's exited we don't care anyway.
        if self._process.poll() is not None:
          return ''
        # On Mac, if the first read in this process occurs before the data is
        # written, no data will ever be read by this process without the seek.
        self._process.child_out.seek(0)
        line = self._process.child_out.read()
        if '\n' in line:
          return line
        _sleep_between_retries(attempt, max_attempts, sleep_base)
    finally:
      self._process.child_out.close()
    return ''

  def start(self):
    """Starts the runtime process and waits until it is ready to serve."""
    runtime_config = self._runtime_config_getter()
    # TODO: Use a different process group to isolate the child process
    # from signals sent to the parent. Only available in subprocess in
    # Python 2.7.
    assert self._start_process_flavor in self._VALID_START_PROCESS_FLAVORS
    if self._start_process_flavor == START_PROCESS:
      serialized_config = base64.b64encode(runtime_config.SerializeToString())
      with self._process_lock:
        assert not self._process, 'start() can only be called once'
        self._process = safe_subprocess.start_process(
            self._args,
            serialized_config,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self._env,
            cwd=self._module_configuration.application_root)
      port = self._process.stdout.readline()
    elif self._start_process_flavor == START_PROCESS_FILE:
      serialized_config = runtime_config.SerializeToString()
      with self._process_lock:
        assert not self._process, 'start() can only be called once'
        self._process = safe_subprocess.start_process_file(
            args=self._args,
            input_string=serialized_config,
            env=self._env,
            cwd=self._module_configuration.application_root,
            stderr=subprocess.PIPE)
      port = self._read_start_process_file()
      _remove_retry_sharing_violation(self._process.child_out.name)
    elif self._start_process_flavor == START_PROCESS_REVERSE:
      serialized_config = runtime_config.SerializeToString()
      with self._process_lock:
        assert not self._process, 'start() can only be called once'
        port = portpicker.PickUnusedPort()
        self._env['PORT'] = str(port)

        # If any of the strings in args contain {port}, replace that substring
        # with the selected port. This allows a user-specified runtime to
        # pass the port along to the subprocess as a command-line argument.
        args = [arg.replace('{port}', str(port)) for arg in self._args]

        self._process = safe_subprocess.start_process_file(
            args=args,
            input_string=serialized_config,
            env=self._env,
            cwd=self._module_configuration.application_root,
            stderr=subprocess.PIPE)
    elif self._start_process_flavor == START_PROCESS_REVERSE_NO_FILE:
      serialized_config = runtime_config.SerializeToString()
      with self._process_lock:
        assert not self._process, 'start() can only be called once'
        port = portpicker.PickUnusedPort()
        if self._extra_args_getter:
          self._args.append(self._extra_args_getter(port))

        # If any of the strings in _args contain {port}, {api_host}, {api_port},
        # replace that substring with the selected port. This allows
        # a user-specified runtime to pass the port along to the subprocess
        # as a command-line argument.
        args = [arg.replace('{port}', str(port))
                .replace('{api_port}', str(runtime_config.api_port))
                .replace('{api_host}', runtime_config.api_host)
                for arg in self._args]

        self._process = safe_subprocess.start_process(
            args=args,
            input_string=serialized_config,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self._env,
            cwd=self._module_configuration.application_root)

    # _stderr_tee may be pre-set by unit tests.
    if self._stderr_tee is None:
      self._stderr_tee = tee.Tee(self._process.stderr, sys.stderr)
      self._stderr_tee.start()

    error = None
    try:
      port = int(port)
    except ValueError:
      error = 'bad runtime process port [%r]' % port
      logging.error(error)
    finally:
      self._proxy = http_proxy.HttpProxy(
          host='localhost', port=port,
          instance_died_unexpectedly=self._instance_died_unexpectedly,
          instance_logs_getter=self._get_instance_logs,
          error_handler_file=application_configuration.get_app_error_file(
              self._module_configuration),
          prior_error=error)
      self._proxy.wait_for_connection()

  def quit(self):
    """Causes the runtime process to exit."""
    with self._process_lock:
      assert self._process, 'module was not running'
      try:
        if HttpRuntimeProxy._quit_with_sigterm:
          logging.debug('Calling process.terminate on child runtime.')
          self._process.terminate()
        else:
          self._process.kill()
      except OSError:
        pass
      # Mac leaks file descriptors without call to join. Suspect a race
      # condition where the interpreter is unable to close the subprocess pipe
      # as the thread hasn't returned from the readline call.
      self._stderr_tee.join(5)
      self._process = None
