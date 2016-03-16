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
"""Tests for google.appengine.tools.devappserver2.tee."""



import cStringIO
import unittest

from google.appengine.tools.devappserver2 import tee


class Counter(object):
  def __init__(self, limit):
    self.__index = 0
    self.__limit = limit

  def readline(self):
    if self.__index < self.__limit:
      self.__index += 1
      return 'line%d\n' % self.__index
    return ''


class TeeTest(unittest.TestCase):
  def test_tee(self):
    output = cStringIO.StringIO()
    tee.Tee._MAX_LINES = 3
    t = tee.Tee(Counter(100), output)
    t.start()
    t.join()
    self.assertEqual('line98\nline99\nline100\n', t.get_buf())
    expected = ''
    for i in range(100):
      expected += 'line%d\n' % (i+1)
    self.assertEqual(expected, output.getvalue())


if __name__ == '__main__':
  unittest.main()
