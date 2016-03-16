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
"""Implementations of start_response callables as defined in PEP-333."""



import cStringIO


class CapturingStartResponse(object):
  """Capture the values passed to start_response."""

  def __init__(self):
    self.status = None
    self.response_headers = None
    self.exc_info = None
    self.response_stream = cStringIO.StringIO()

  def __call__(self, status, response_headers, exc_info=None):
    assert exc_info is not None or self.status is None, (
        'only one call to start_response allowed')
    self.status = status
    self.response_headers = response_headers
    self.exc_info = exc_info
    return self.response_stream

  def merged_response(self, response):
    """Merge the response stream and the values returned by the WSGI app."""
    return self.response_stream.getvalue() + ''.join(response)


def null_start_response(status, response_headers, exc_info=None):
  return cStringIO.StringIO()
