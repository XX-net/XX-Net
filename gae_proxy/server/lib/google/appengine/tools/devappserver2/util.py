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
"""General utility functions for devappserver2."""




import wsgiref.headers


def get_headers_from_environ(environ):
  """Get a wsgiref.headers.Headers object with headers from the environment.

  Headers in environ are prefixed with 'HTTP_', are all uppercase, and have
  had dashes replaced with underscores.  This strips the HTTP_ prefix and
  changes underscores back to dashes before adding them to the returned set
  of headers.

  Args:
    environ: An environ dict for the request as defined in PEP-333.

  Returns:
    A wsgiref.headers.Headers object that's been filled in with any HTTP
    headers found in environ.
  """
  headers = wsgiref.headers.Headers([])
  for header, value in environ.iteritems():
    if header.startswith('HTTP_'):
      headers[header[5:].replace('_', '-')] = value
  # Content-Type is special; it does not start with 'HTTP_'.
  if 'CONTENT_TYPE' in environ:
    headers['CONTENT-TYPE'] = environ['CONTENT_TYPE']
  return headers


def put_headers_in_environ(headers, environ):
  """Given a list of headers, put them into environ based on PEP-333.

  This converts headers to uppercase, prefixes them with 'HTTP_', and
  converts dashes to underscores before adding them to the environ dict.

  Args:
    headers: A list of (header, value) tuples.  The HTTP headers to add to the
      environment.
    environ: An environ dict for the request as defined in PEP-333.
  """
  for key, value in headers:
    environ['HTTP_%s' % key.upper().replace('-', '_')] = value
