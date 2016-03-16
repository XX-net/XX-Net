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
"""Tests for google.apphosting.tools.devappserver2.start_response_utils."""



import unittest

from google.appengine.tools.devappserver2 import start_response_utils


class TestCapturingStartResponse(unittest.TestCase):
  """Tests for start_response_util.CapturingStartResponse."""

  def test_success(self):
    start_response = start_response_utils.CapturingStartResponse()
    stream = start_response('200 OK', [('header1', 'value1')])
    stream.write('Hello World!')
    self.assertEqual('200 OK', start_response.status)
    self.assertEqual(None, start_response.exc_info)
    self.assertEqual([('header1', 'value1')], start_response.response_headers)
    self.assertEqual('Hello World!', start_response.response_stream.getvalue())

  def test_exception(self):
    exc_info = (object(), object(), object())

    start_response = start_response_utils.CapturingStartResponse()
    start_response('200 OK', [('header1', 'value1')])
    start_response('500 Internal Server Error', [], exc_info)

    self.assertEqual('500 Internal Server Error', start_response.status)
    self.assertEqual(exc_info, start_response.exc_info)
    self.assertEqual([], start_response.response_headers)

  def test_merged_response(self):
    start_response = start_response_utils.CapturingStartResponse()
    stream = start_response('200 OK', [('header1', 'value1')])
    stream.write('Hello World!')
    self.assertEqual('Hello World! Goodbye World!',
                     start_response.merged_response([' Goodbye ', 'World!']))

if __name__ == '__main__':
  unittest.main()
