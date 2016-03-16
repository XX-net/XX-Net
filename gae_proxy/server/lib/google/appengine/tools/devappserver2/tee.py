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
"""A simple line-oriented "tee"."""



import collections
import threading


class Tee(threading.Thread):
  """A simple line-oriented "tee".

  This class connects two file-like objects, piping the output of one to the
  input of the other, and buffering the last 100 lines.
  """

  _MAX_LINES = 100

  def __init__(self, in_f, out_f):
    threading.Thread.__init__(self, name='Tee')
    self.__in = in_f
    self.__out = out_f
    self.__deque = collections.deque('', Tee._MAX_LINES)

  def run(self):
    while True:
      line = self.__in.readline()
      if not line:
        break
      self.__out.write(line)
      self.__out.flush()
      self.__deque.append(line)

  def get_buf(self):
    return ''.join(self.__deque)
