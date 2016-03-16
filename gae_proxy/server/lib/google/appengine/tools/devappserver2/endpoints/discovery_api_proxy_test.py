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
"""Unit tests for the discovery_api_proxy module."""







import httplib
import json
import os
import unittest

import google
import mox

from google.appengine.tools.devappserver2.endpoints import discovery_api_proxy
from google.appengine.tools.devappserver2.endpoints import test_utils


class DiscoveryApiProxyTest(unittest.TestCase):

  def setUp(self):
    self._common_setup()
    self.mox = mox.Mox()

  def tearDown(self):
    self.mox.UnsetStubs()

  def _common_setup(self):
    self.discovery_api = discovery_api_proxy.DiscoveryApiProxy()
    api_config_file = os.path.join(os.path.dirname(__file__),
                                   'testdata/tictactoe-v1.api')
    with open(api_config_file, 'r') as api_file:
      api_config = api_file.read()
    self.api_config_dict = json.loads(api_config)

  def connection_response(self):
    return self._response

  def prepare_discovery_request(self, status_code, body):
    self.mox.StubOutWithMock(httplib.HTTPSConnection, 'request')
    self.mox.StubOutWithMock(httplib.HTTPSConnection, 'getresponse')
    self.mox.StubOutWithMock(httplib.HTTPSConnection, 'close')

    httplib.HTTPSConnection.request(mox.IsA(basestring), mox.IsA(basestring),
                                    mox.IgnoreArg(), mox.IsA(dict))
    httplib.HTTPSConnection.getresponse().AndReturn(
        test_utils.MockConnectionResponse(status_code, body))
    httplib.HTTPSConnection.close()

  def test_generate_discovery_doc_rest(self):
    body = {'baseUrl': 'https://tictactoe.appspot.com/_ah/api/tictactoe/v1/'}
    self.prepare_discovery_request(200, json.dumps(body))

    self.mox.ReplayAll()
    doc = self.discovery_api.generate_discovery_doc(
        self.api_config_dict, 'rest')
    self.mox.VerifyAll()

    self.assertTrue(doc)
    api_config = json.loads(doc)
    self.assertEquals('https://tictactoe.appspot.com/_ah/api/tictactoe/v1/',
                      api_config['baseUrl'])

  def test_generate_discovery_doc_rpc(self):
    body = {'rpcUrl': 'https://tictactoe.appspot.com/_ah/api/rpc'}
    self.prepare_discovery_request(200, json.dumps(body))

    self.mox.ReplayAll()
    doc = self.discovery_api.generate_discovery_doc(
        self.api_config_dict, 'rpc')
    self.mox.VerifyAll()

    self.assertTrue(doc)
    api_config = json.loads(doc)
    self.assertEquals('https://tictactoe.appspot.com/_ah/api/rpc',
                      api_config['rpcUrl'])

  def test_generate_discovery_doc_invalid_format(self):
    self._response = test_utils.MockConnectionResponse(400, 'Error')
    self.assertRaises(ValueError,
                      self.discovery_api.generate_discovery_doc,
                      self.api_config_dict, 'blah')

  def test_generate_discovery_doc_bad_api_config(self):
    self.prepare_discovery_request(503, None)

    self.mox.ReplayAll()
    doc = self.discovery_api.generate_discovery_doc('{ "name": "none" }', 'rpc')
    self.mox.VerifyAll()

    self.assertIsNone(doc)

  def test_get_static_file_existing(self):
    body = 'static file body'
    self.prepare_discovery_request(200, body)

    self.mox.ReplayAll()
    response, response_body = self.discovery_api.get_static_file(
        '/_ah/api/static/proxy.html')
    self.mox.VerifyAll()

    self.assertEqual(200, response.status)
    self.assertEqual(body, response_body)

if __name__ == '__main__':
  unittest.main()
