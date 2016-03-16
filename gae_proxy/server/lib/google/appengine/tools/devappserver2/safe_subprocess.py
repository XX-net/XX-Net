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
"""A thread-safe wrapper for the subprocess module."""

import logging
import subprocess
import sys
import tempfile
import threading

# Subprocess creation is not threadsafe in Python. See
# http://bugs.python.org/issue1731717.
_popen_lock = threading.Lock()

# The provided Python binary on OS X also requires _popen_lock be held while
# writing to and closing the stdin of the subprocess.
if sys.platform == 'darwin':
  _SUBPROCESS_STDIN_IS_THREAD_HOSTILE = True
else:
  _SUBPROCESS_STDIN_IS_THREAD_HOSTILE = False


def start_process(args, input_string='', env=None, cwd=None, stdout=None,
                  stderr=None):
  """Starts a subprocess like subprocess.Popen, but is threadsafe.

  The value of input_string is passed to stdin of the subprocess, which is then
  closed.

  Args:
    args: A string or sequence of strings containing the program arguments.
    input_string: A string to pass to stdin of the subprocess.
    env: A dict containing environment variables for the subprocess.
    cwd: A string containing the directory to switch to before executing the
        subprocess.
    stdout: A file descriptor, file object or subprocess.PIPE to use for the
        stdout descriptor for the subprocess.
    stderr: A file descriptor, file object or subprocess.PIPE to use for the
        stderr descriptor for the subprocess.

  Returns:
    A subprocess.Popen instance for the created subprocess.
  """
  with _popen_lock:
    logging.debug('Starting process %r with input=%r, env=%r, cwd=%r',
                  args, input_string, env, cwd)

    # Suppress the display of the console window on Windows.
    # Note: subprocess.STARTF_USESHOWWINDOW & subprocess.SW_HIDE are only
    # availalbe after Python 2.7.2 on Windows.
    if (hasattr(subprocess, 'SW_HIDE') and
        hasattr(subprocess, 'STARTF_USESHOWWINDOW')):
      startupinfo = subprocess.STARTUPINFO()
      startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
      startupinfo.wShowWindow = subprocess.SW_HIDE
    else:
      startupinfo = None

    p = subprocess.Popen(args, env=env, cwd=cwd, stdout=stdout, stderr=stderr,
                         stdin=subprocess.PIPE, startupinfo=startupinfo)
    if _SUBPROCESS_STDIN_IS_THREAD_HOSTILE:
      p.stdin.write(input_string)
      p.stdin.close()
      p.stdin = None
  if not _SUBPROCESS_STDIN_IS_THREAD_HOSTILE:
    p.stdin.write(input_string)
    p.stdin.close()
    p.stdin = None
  return p


def start_process_file(args, input_string, env, cwd, stdin=None, stdout=None,
                       stderr=None):
  """Starts a subprocess thread safely with temporary files for communication.

  An alternate version of start_process that allows for the preservation
  of stdin and stdout by creating two files that can be used for communication
  between the processes. The paths to these files are added to the command
  line after any args provided by the caller. The first file is written with
  the value of input_string and the second file is returned to the caller.

  Args:
    args: A list of strings containing the program arguments.
    input_string: A string to pass to stdin of the subprocess.
    env: A dict containing environment variables for the subprocess.
    cwd: A string containing the directory to switch to before executing the
        subprocess.
    stdin: A file descriptor, file object or subprocess.PIPE to use for the
        stdin descriptor for the subprocess.
    stdout: A file descriptor, file object or subprocess.PIPE to use for the
        stdout descriptor for the subprocess.
    stderr: A file descriptor, file object or subprocess.PIPE to use for the
        stderr descriptor for the subprocess.

  Returns:
    A subprocess.Popen instance for the created subprocess. In addition to
    the standard attributes, an additional child_out attribute is attached
    that references a NamedTemporaryFile that the child process may write
    and this process may read; it is up to the caller to delete the file
    (path available as p.child_out.name).
  """
  # In addition to needing to control deletion time, we need delete=False
  # in order to allow multiple files to open the process on Windows.
  child_in = tempfile.NamedTemporaryFile(mode='wb', delete=False)
  child_out = tempfile.NamedTemporaryFile(mode='rb', delete=False)

  child_in.write(input_string)
  child_in.close()

  # pylint: disable=g-no-augmented-assignment
  # += modifies the original args which we don't want.
  args = args + [child_in.name, child_out.name]

  with _popen_lock:
    logging.debug('Starting process %r with input=%r, env=%r, cwd=%r',
                  args, input_string, env, cwd)
    p = subprocess.Popen(args, env=env, cwd=cwd, stdin=stdin, stdout=stdout,
                         stderr=stderr)

  p.child_out = child_out
  return p
