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
"""Helper utilities for the endpoints package."""







import json


def send_wsgi_not_found_response(start_response, cors_handler=None):
  return send_wsgi_response('404', [('Content-Type', 'text/plain')],
                            'Not Found', start_response,
                            cors_handler=cors_handler)


def send_wsgi_error_response(message, start_response, cors_handler=None):
  body = json.dumps({'error': {'message': message}})
  return send_wsgi_response('500', [('Content-Type', 'application/json')], body,
                            start_response, cors_handler=cors_handler)


def send_wsgi_rejected_response(rejection_error, start_response,
                                cors_handler=None):
  body = rejection_error.to_json()
  return send_wsgi_response('400', [('Content-Type', 'application/json')], body,
                            start_response, cors_handler=cors_handler)


def send_wsgi_redirect_response(redirect_location, start_response,
                                cors_handler=None):
  return send_wsgi_response('302', [('Location', redirect_location)], '',
                            start_response, cors_handler=cors_handler)


def send_wsgi_no_content_response(start_response, cors_handler=None):
  return send_wsgi_response('204', [], '', start_response, cors_handler)


def send_wsgi_response(status, headers, content, start_response,
                       cors_handler=None):
  """Dump reformatted response to CGI start_response.

  This calls start_response and returns the response body.

  Args:
    status: A string containing the HTTP status code to send.
    headers: A list of (header, value) tuples, the headers to send in the
      response.
    content: A string containing the body content to write.
    start_response: A function with semantics defined in PEP-333.
    cors_handler: A handler to process CORS request headers and update the
      headers in the response.  Or this can be None, to bypass CORS checks.

  Returns:
    A string containing the response body.
  """
  if cors_handler:
    cors_handler.update_headers(headers)

  # Update content length.
  content_len = len(content) if content else 0
  headers = [(header, value) for header, value in headers
             if header.lower() != 'content-length']
  headers.append(('Content-Length', '%s' % content_len))

  start_response(status, headers)
  return content
