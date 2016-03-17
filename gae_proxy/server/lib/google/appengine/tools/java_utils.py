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
"""Utilities for handling Java code."""

import os


def JavaHomeAndSuffix():
  """Find the directory that the JDK is installed in.

  The JDK install directory is expected to have a bin directory that contains
  at a minimum the java and javac executables. If the environment variable
  JAVA_HOME is set then it must point to such a directory. Otherwise, we look
  for javac on the PATH and check that it is inside a JDK install directory.

  Returns:
    A tuple where the first element is the JDK install directory and the second
    element is a suffix that must be appended to executables in that directory
    ('' on Unix-like systems, '.exe' on Windows).

  Raises:
    RuntimeError: If JAVA_HOME is set but is not a JDK install directory, or
    otherwise if a JDK install directory cannot be found based on the PATH.
  """
  def ResultForJdkAt(path):
    """Return (path, suffix) if path is a JDK install directory, else None."""
    def IsExecutable(binary):
      return os.path.isfile(binary) and os.access(binary, os.X_OK)

    def ResultFor(path):
      for suffix in ['', '.exe']:
        if all(IsExecutable(os.path.join(path, 'bin', binary + suffix))
               for binary in ['java', 'javac', 'jar']):
          return (path, suffix)
      return None

    result = ResultFor(path)
    if not result:


      head, tail = os.path.split(path)
      if tail == 'jre':
        result = ResultFor(head)
    return result

  java_home = os.getenv('JAVA_HOME')
  if java_home:
    result = ResultForJdkAt(java_home)
    if result:
      return result
    else:
      raise RuntimeError(
          'JAVA_HOME is set but does not reference a valid JDK: %s' % java_home)
  for path_dir in os.environ['PATH'].split(os.pathsep):
    maybe_root, last = os.path.split(path_dir)
    if last == 'bin':
      result = ResultForJdkAt(maybe_root)
      if result:
        return result
  raise RuntimeError('Did not find JDK in PATH and JAVA_HOME is not set')
