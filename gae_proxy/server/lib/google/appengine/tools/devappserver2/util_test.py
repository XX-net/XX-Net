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
"""Unit tests for the util module."""



import unittest
import wsgiref

from google.appengine.tools.devappserver2 import util


class UtilTest(unittest.TestCase):

  def test_get_headers_from_environ(self):
    environ = {'SERVER_PORT': '42', 'REQUEST_METHOD': 'GET',
               'SERVER_NAME': 'localhost',
               'CONTENT_TYPE': 'application/json',
               'HTTP_CONTENT_LENGTH': '0', 'HTTP_X_USER_IP': '127.0.0.1'}
    headers = util.get_headers_from_environ(environ)

    self.assertEqual(len(headers), 3)
    self.assertEqual(headers['Content-Type'], 'application/json')
    self.assertEqual(headers['Content-Length'], '0')
    self.assertEqual(headers['X-User-IP'], '127.0.0.1')

  def test_put_headers_in_environ(self):
    environ = {'SERVER_PORT': '42', 'REQUEST_METHOD': 'GET'}
    headers = wsgiref.headers.Headers([])
    headers['Content-Length'] = '2'
    headers['X-User-IP'] = '127.0.0.1'
    headers['Access-Control-Allow-Origin'] = 'google.com'
    util.put_headers_in_environ(headers.items(), environ)

    self.assertEqual(environ,
                     {'SERVER_PORT': '42', 'REQUEST_METHOD': 'GET',
                      'HTTP_CONTENT_LENGTH': '2',
                      'HTTP_X_USER_IP': '127.0.0.1',
                      'HTTP_ACCESS_CONTROL_ALLOW_ORIGIN': 'google.com'})

if __name__ == '__main__':
  unittest.main()
