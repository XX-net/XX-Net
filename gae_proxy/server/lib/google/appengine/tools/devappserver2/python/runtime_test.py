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
"""Tests for google.appengine.tools.devappserver2.python.runtime."""



import unittest

import google
import mox

from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.tools.devappserver2 import runtime_config_pb2
from google.appengine.tools.devappserver2.python import runtime


class SetupStubsTest(unittest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_setup_stubs(self):
    self.mox.StubOutWithMock(remote_api_stub, 'ConfigureRemoteApi')
    remote_api_stub.ConfigureRemoteApi('app', '/', mox.IgnoreArg(),
                                       'somehost:12345',
                                       use_remote_datastore=False)
    config = runtime_config_pb2.Config()
    config.app_id = 'app'
    config.api_host = 'somehost'
    config.api_port = 12345
    self.mox.ReplayAll()
    runtime.setup_stubs(config)
    self.mox.VerifyAll()

if __name__ == '__main__':
  unittest.main()
