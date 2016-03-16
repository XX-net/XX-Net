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
"""Hook into the live Discovery service and get API configuration info."""







import json
import logging

from google.appengine.tools.devappserver2.endpoints import discovery_api_proxy
from google.appengine.tools.devappserver2.endpoints import util


class DiscoveryService(object):
  """Implements the local devserver discovery service.

  This has a static minimal version of the discoverable part of the
  discovery .api file.

  It only handles returning the discovery doc and directory, and ignores
  directory parameters to filter the results.

  The discovery docs/directory are created by calling a cloud endpoint
  discovery service to generate the discovery docs/directory from an .api
  file/set of .api files.
  """

  _GET_REST_API = 'apisdev.getRest'
  _GET_RPC_API = 'apisdev.getRpc'
  _LIST_API = 'apisdev.list'
  API_CONFIG = {
      'name': 'discovery',
      'version': 'v1',
      'methods': {
          'discovery.apis.getRest': {
              'path': 'apis/{api}/{version}/rest',
              'httpMethod': 'GET',
              'rosyMethod': _GET_REST_API,
          },
          'discovery.apis.getRpc': {
              'path': 'apis/{api}/{version}/rpc',
              'httpMethod': 'GET',
              'rosyMethod': _GET_RPC_API,
          },
          'discovery.apis.list': {
              'path': 'apis',
              'httpMethod': 'GET',
              'rosyMethod': _LIST_API,
          },
      }
  }

  def __init__(self, config_manager):
    """Initializes an instance of the DiscoveryService.

    Args:
      config_manager: An instance of ApiConfigManager.
    """
    self._config_manager = config_manager
    self._discovery_proxy = discovery_api_proxy.DiscoveryApiProxy()

  def _send_success_response(self, response, start_response):
    """Sends an HTTP 200 json success response.

    This calls start_response and returns the response body.

    Args:
      response: A string containing the response body to return.
      start_response: A function with semantics defined in PEP-333.

    Returns:
      A string, the response body.
    """
    headers = [('Content-Type', 'application/json; charset=UTF-8')]
    return util.send_wsgi_response('200', headers, response, start_response)

  def _get_rpc_or_rest(self, api_format, request, start_response):
    """Sends back HTTP response with API directory.

    This calls start_response and returns the response body.  It will return
    the discovery doc for the requested api/version.

    Args:
      api_format: A string containing either 'rest' or 'rpc'.
      request: An ApiRequest, the transformed request sent to the Discovery SPI.
      start_response: A function with semantics defined in PEP-333.

    Returns:
      A string, the response body.
    """
    api = request.body_json['api']
    version = request.body_json['version']
    lookup_key = (api, version)
    api_config = self._config_manager.configs.get(lookup_key)
    if not api_config:
      logging.warn('No discovery doc for version %s of api %s', version, api)
      return util.send_wsgi_not_found_response(start_response)
    doc = self._discovery_proxy.generate_discovery_doc(api_config, api_format)
    if not doc:
      error_msg = ('Failed to convert .api to discovery doc for '
                   'version %s of api %s') % (version, api)
      logging.error('%s', error_msg)
      return util.send_wsgi_error_response(error_msg, start_response)
    return self._send_success_response(doc, start_response)

  def _list(self, start_response):
    """Sends HTTP response containing the API directory.

    This calls start_response and returns the response body.

    Args:
      start_response: A function with semantics defined in PEP-333.

    Returns:
      A string containing the response body.
    """
    api_configs = []
    for api_config in self._config_manager.configs.itervalues():
      if not api_config == self.API_CONFIG:
        api_configs.append(json.dumps(api_config))
    directory = self._discovery_proxy.generate_directory(api_configs)
    if not directory:
      logging.error('Failed to get API directory')
      # By returning a 404, code explorer still works if you select the
      # API in the URL
      return util.send_wsgi_not_found_response(start_response)
    return self._send_success_response(directory, start_response)

  def handle_discovery_request(self, path, request, start_response):
    """Returns the result of a discovery service request.

    This calls start_response and returns the response body.

    Args:
      path: A string containing the SPI API path (the portion of the path
        after /_ah/spi/).
      request: An ApiRequest, the transformed request sent to the Discovery SPI.
      start_response: A function with semantics defined in PEP-333.

    Returns:
      The response body.  Or returns False if the request wasn't handled by
      DiscoveryService.
    """
    if path == self._GET_REST_API:
      return self._get_rpc_or_rest('rest', request, start_response)
    elif path == self._GET_RPC_API:
      return self._get_rpc_or_rest('rpc', request, start_response)
    elif path == self._LIST_API:
      return self._list(start_response)
    return False
