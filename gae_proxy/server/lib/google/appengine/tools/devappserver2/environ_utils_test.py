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
import unittest

from google.appengine.tools.devappserver2 import environ_utils


class EnvironUtilsTest(unittest.TestCase):

  def test_propagate_environs(self):
    src = {
        'LALA': 'will not propagate',
        'HTTP_LALA': 'will propagate',
        'HTTP_X_APPENGINE_USER_ID': '12345',
        'HTTP_X_APPENGINE_DEV_MYENV': 'will not propagate either'
    }

    dst = {}
    environ_utils.propagate_environs(src, dst)
    self.assertEqual(dst, {'HTTP_LALA': 'will propagate',
                           'USER_ID': '12345'})


if __name__ == '__main__':
  unittest.main()
