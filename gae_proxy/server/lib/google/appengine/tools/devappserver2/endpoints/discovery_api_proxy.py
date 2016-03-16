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
"""Proxy that dispatches Discovery requests to the prod Discovery service."""







import httplib
import json
import logging


class DiscoveryApiProxy(object):
  """Proxies discovery service requests to a known cloud endpoint."""

  # The endpoint host we're using to proxy discovery and static requests.
  # Using separate constants to make it easier to change the discovery service.
  _DISCOVERY_PROXY_HOST = 'webapis-discovery.appspot.com'
  _STATIC_PROXY_HOST = 'webapis-discovery.appspot.com'
  _DISCOVERY_API_PATH_PREFIX = '/_ah/api/discovery/v1/'

  def _dispatch_request(self, path, body):
    """Proxies GET request to discovery service API.

    Args:
      path: A string containing the URL path relative to discovery service.
      body: A string containing the HTTP POST request body.

    Returns:
      HTTP response body or None if it failed.
    """
    full_path = self._DISCOVERY_API_PATH_PREFIX + path
    headers = {'Content-type': 'application/json'}
    connection = httplib.HTTPSConnection(self._DISCOVERY_PROXY_HOST)
    try:
      connection.request('POST', full_path, body, headers)
      response = connection.getresponse()
      response_body = response.read()
      if response.status != 200:
        logging.error('Discovery API proxy failed on %s with %d.\r\n'
                      'Request: %s\r\nResponse: %s',
                      full_path, response.status, body, response_body)
        return None
      return response_body
    finally:
      connection.close()

  def generate_discovery_doc(self, api_config, api_format):
    """Generates a discovery document from an API file.

    Args:
      api_config: A string containing the .api file contents.
      api_format: A string, either 'rest' or 'rpc' depending on the which kind
        of discvoery doc is requested.

    Returns:
      The discovery doc as JSON string.

    Raises:
      ValueError: When api_format is invalid.
    """
    if api_format not in ['rest', 'rpc']:
      raise ValueError('Invalid API format')
    path = 'apis/generate/' + api_format
    request_dict = {'config': json.dumps(api_config)}
    request_body = json.dumps(request_dict)
    return self._dispatch_request(path, request_body)

  def generate_directory(self, api_configs):
    """Generates an API directory from a list of API files.

    Args:
      api_configs: A list of strings which are the .api file contents.

    Returns:
      The API directory as JSON string.
    """
    request_dict = {'configs': api_configs}
    request_body = json.dumps(request_dict)
    return self._dispatch_request('apis/generate/directory', request_body)

  def get_static_file(self, path):
    """Returns static content via a GET request.

    Args:
      path: A string containing the URL path after the domain.

    Returns:
      A tuple of (response, response_body):
        response: A HTTPResponse object with the response from the static
          proxy host.
        response_body: A string containing the response body.
    """
    connection = httplib.HTTPSConnection(self._STATIC_PROXY_HOST)
    try:
      connection.request('GET', path, None, {})
      response = connection.getresponse()
      response_body = response.read()
    finally:
      connection.close()
    return response, response_body
