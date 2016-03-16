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

from google.appengine.tools.devappserver2.endpoints import test_utils
from google.appengine.tools.devappserver2.endpoints import util


class WSGIHelpersTest(test_utils.TestsWithStartResponse):

  def test_send_wsgi_response(self):
    mock_headers = [('content-type', 'text/plain')]
    content = 'Test output'
    response = util.send_wsgi_response(
        '200', mock_headers, content, self.start_response)
    self.assert_http_match(response, 200,
                           [('content-type', 'text/plain'),
                            ('Content-Length', '11')],
                           content)

  def test_send_wsgi_redirect_response(self):
    response = util.send_wsgi_redirect_response(
        'http://www.google.com', self.start_response)
    self.assert_http_match(response, 302,
                           [('Location', 'http://www.google.com'),
                            ('Content-Length', '0')], '')

  def test_send_wsgi_no_content_response(self):
    response = util.send_wsgi_no_content_response(self.start_response)
    self.assert_http_match(response, 204, [('Content-Length', '0')], '')

if __name__ == '__main__':
  unittest.main()
