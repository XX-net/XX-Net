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




"""A request-local environment and logging stream."""








import collections
import os
import sys
import threading

_sys_stderr = sys.stderr


class RequestEnvironment(threading.local):
  """A thread local request environment.

  A thread local request environment that provides an error stream errors and a
  dict of the request environment environ as would be found in os.environ. A
  single error stream is shared between threads of a single request, but each
  thread accesses an independent copy of environ created when
  CloneRequestEnvironment is called. A request environment of one thread can be
  installed in another thread as follows:
    1. Call CloneRequestEnvironment in the first thread.
    2. Call the returned callable from the other thread.
  """

  def __init__(self):
    super(RequestEnvironment, self).__init__()
    self.Reset()

  def Reset(self):
    """Resets the error stream and environment for this request."""
    self.errors = _sys_stderr
    self.environ = {}

  def Init(self, errors, environ):
    self.errors = errors
    self.environ = environ

  def CloneRequestEnvironment(self):
    """Returns a callable that will install the environment in another thread.

    Returns:
      A callable that will duplicate the request environment of this thread in
      another thread that calls it.
    """
    errors = self.errors
    environ = dict(self.environ)
    return lambda: self.Init(errors, environ)

  def Clear(self):
    """Clears the thread locals."""
    self.__dict__.clear()
    self.Reset()


class RequestLocalStream(object):
  """A stream that delegates to a RequestEnvironment stream."""

  def __init__(self, request):
    self._request = request

  def close(self):
    pass

  def flush(self):
    self._request.errors.flush()

  def write(self, data):
    self._request.errors.write(data)

  def writelines(self, data):
    self._request.errors.writelines(data)


class RequestLocalEnviron(collections.MutableMapping):
  """A MutableMapping that delegates to a RequestEnvironment environ."""

  def __init__(self, request):
    self._request = request

  def __len__(self):
    return len(self._request.environ)

  def __iter__(self):
    return iter(self._request.environ)

  def __getitem__(self, key):
    return self._request.environ[key]

  def __setitem__(self, key, value):
    self._request.environ[key] = value

  def __delitem__(self, key):
    del self._request.environ[key]

  def __repr__(self):
    return repr(self._request.environ)

  def has_key(self, key):
    return key in self._request.environ

  def copy(self):
    return dict(self._request.environ)



  def viewitems(self):
    return collections.ItemsView(self)

  def viewkeys(self):
    return collections.KeysView(self)

  def viewvalues(self):
    return collections.ValuesView(self)


current_request = RequestEnvironment()




def PatchOsEnviron(os_module=os):
  """Replace os.environ by a RequestLocalEnviron instance.

  This is called from init.py when it modifies the execution
  environment (in the wider sense of the word).

  Args:
    os_module: An optional module to patch. Defaults to os.
  """
  os_module.environ = RequestLocalEnviron(current_request)
