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
"""Cloud Endpoints API request-related data and functions."""

from __future__ import with_statement







import cgi
import copy
import json
import logging
import urllib
import zlib

from google.appengine.tools.devappserver2 import util


class ApiRequest(object):
  """Simple data object representing an API request.

  Parses the request from environment variables into convenient pieces
  and stores them as members.
  """
  _API_PREFIX = '/_ah/api/'

  def __init__(self, environ):
    """Constructor.

    Args:
      environ: An environ dict for the request as defined in PEP-333.

    Raises:
      ValueError: If the path for the request is invalid.
    """
    self.headers = util.get_headers_from_environ(environ)
    self.http_method = environ['REQUEST_METHOD']
    self.server = environ['SERVER_NAME']
    self.port = environ['SERVER_PORT']
    self.path = environ['PATH_INFO']
    self.query = environ.get('QUERY_STRING')
    self.body = environ['wsgi.input'].read()
    if self.body and self.headers.get('CONTENT-ENCODING') == 'gzip':
      # Increasing wbits to 16 + MAX_WBITS is necessary to be able to decode
      # gzipped content (as opposed to zlib-encoded content).
      self.body = zlib.decompress(self.body, 16 + zlib.MAX_WBITS)
    self.source_ip = environ.get('REMOTE_ADDR')
    self.relative_url = self._reconstruct_relative_url(environ)

    if not self.path.startswith(self._API_PREFIX):
      raise ValueError('Invalid request path: %s' % self.path)
    self.path = self.path[len(self._API_PREFIX):]
    if self.query:
      self.parameters = cgi.parse_qs(self.query, keep_blank_values=True)
    else:
      self.parameters = {}
    self.body_json = json.loads(self.body) if self.body else {}
    self.request_id = None

    # Check if it's a batch request.  We'll only handle single-element batch
    # requests on the dev server (and we need to handle them because that's
    # what RPC and JS calls typically show up as).  Pull the request out of the
    # list and record the fact that we're processing a batch.
    if isinstance(self.body_json, list):
      if len(self.body_json) != 1:
        logging.warning('Batch requests with more than 1 element aren\'t '
                        'supported in devappserver2.  Only the first element '
                        'will be handled.  Found %d elements.',
                        len(self.body_json))
      else:
        logging.info('Converting batch request to single request.')
      self.body_json = self.body_json[0]
      self.body = json.dumps(self.body_json)
      self._is_batch = True
    else:
      self._is_batch = False

  def _reconstruct_relative_url(self, environ):
    """Reconstruct the relative URL of this request.

    This is based on the URL reconstruction code in Python PEP 333:
    http://www.python.org/dev/peps/pep-0333/#url-reconstruction.  Rebuild the
    URL from the pieces available in the environment.

    Args:
      environ: An environ dict for the request as defined in PEP-333.

    Returns:
      The portion of the URL from the request after the server and port.
    """
    url = urllib.quote(environ.get('SCRIPT_NAME', ''))
    url += urllib.quote(environ.get('PATH_INFO', ''))
    if environ.get('QUERY_STRING'):
      url += '?' + environ['QUERY_STRING']
    return url

  def copy(self):
    return copy.deepcopy(self)

  def is_rpc(self):
    # Google's JsonRPC protocol creates a handler at /rpc for any Cloud
    # Endpoints API, with api name, version, and method name being in the
    # body of the request.
    # If the request is sent to /rpc, we will treat it as JsonRPC.
    # The client libraries for iOS's Objective C use RPC and not the REST
    # versions of the API.
    return self.path == 'rpc'

  def is_batch(self):
    return self._is_batch
