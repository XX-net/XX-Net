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
"""Unit tests for the discovery_service module."""







import json
import os
import unittest

import google

import mox

from google.appengine.tools.devappserver2.endpoints import api_config_manager
from google.appengine.tools.devappserver2.endpoints import discovery_api_proxy
from google.appengine.tools.devappserver2.endpoints import discovery_service
from google.appengine.tools.devappserver2.endpoints import test_utils


class DiscoveryServiceTest(test_utils.TestsWithStartResponse):

  def setUp(self):
    super(DiscoveryServiceTest, self).setUp()
    self._common_setup()
    self.mox = mox.Mox()

  def tearDown(self):
    self.mox.UnsetStubs()

  def _common_setup(self):
    api_config_file = os.path.join(os.path.dirname(__file__),
                                   'testdata/tictactoe-v1.api')
    with open(api_config_file, 'r') as api_file:
      api_config = api_file.read()
    api_config_dict = {'items': [api_config]}
    self.api_config_manager = api_config_manager.ApiConfigManager()
    self.api_config_manager.parse_api_config_response(
        json.dumps(api_config_dict))
    self.api_request = test_utils.build_request(
        '/_ah/api/foo', '{"api": "tictactoe", "version": "v1"}')

  def prepare_discovery_request(self, response_body):
    self._response = test_utils.MockConnectionResponse(200, response_body)
    discovery = discovery_service.DiscoveryService(
        self.api_config_manager)
    discovery._discovery_proxy = self.mox.CreateMock(
        discovery_api_proxy.DiscoveryApiProxy)
    return discovery

  def test_generate_discovery_doc_rest(self):
    body = json.dumps(
        {'baseUrl': 'https://tictactoe.appspot.com/_ah/api/tictactoe/v1/'})
    discovery = self.prepare_discovery_request(body)
    discovery._discovery_proxy.generate_discovery_doc(
        mox.IsA(object), 'rest').AndReturn(body)

    self.mox.ReplayAll()
    response = discovery.handle_discovery_request(
        discovery_service.DiscoveryService._GET_REST_API, self.api_request,
        self.start_response)
    self.mox.VerifyAll()

    self.assert_http_match(response, 200,
                           [('Content-Type', 'application/json; charset=UTF-8'),
                            ('Content-Length', '%d' % len(body))],
                           body)

  def test_generate_discovery_doc_rpc(self):
    body = json.dumps({'rpcUrl': 'https://tictactoe.appspot.com/_ah/api/rpc'})
    discovery = self.prepare_discovery_request(body)
    discovery._discovery_proxy.generate_discovery_doc(
        mox.IsA(object), 'rpc').AndReturn(body)

    self.mox.ReplayAll()
    response = discovery.handle_discovery_request(
        discovery_service.DiscoveryService._GET_RPC_API, self.api_request,
        self.start_response)
    self.mox.VerifyAll()

    self.assert_http_match(response, 200,
                           [('Content-Type', 'application/json; charset=UTF-8'),
                            ('Content-Length', '%d' % len(body))],
                           body)

  def test_generate_discovery_doc_rest_unknown_api(self):
    request = test_utils.build_request('/_ah/api/foo',
                                       '{"api": "blah", "version": "v1"}')
    discovery_api = discovery_service.DiscoveryService(
        self.api_config_manager)
    discovery_api.handle_discovery_request(
        discovery_service.DiscoveryService._GET_REST_API, request,
        self.start_response)
    self.assertEquals(self.response_status, '404')

  def test_generate_directory(self):
    body = json.dumps({'kind': 'discovery#directoryItem'})
    discovery = self.prepare_discovery_request(body)
    discovery._discovery_proxy.generate_directory(
        mox.IsA(list)).AndReturn(body)

    self.mox.ReplayAll()
    response = discovery.handle_discovery_request(
        discovery_service.DiscoveryService._LIST_API, self.api_request,
        self.start_response)
    self.mox.VerifyAll()

    self.assert_http_match(response, 200,
                           [('Content-Type', 'application/json; charset=UTF-8'),
                            ('Content-Length', '%d' % len(body))],
                           body)

if __name__ == '__main__':
  unittest.main()
