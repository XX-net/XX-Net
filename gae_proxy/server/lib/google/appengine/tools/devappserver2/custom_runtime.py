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
"""Serves content for "script" handlers using a custom runtime."""



import os
import shlex

import google
from google.appengine.api import appinfo
from google.appengine.tools.devappserver2 import http_runtime
from google.appengine.tools.devappserver2 import instance


class CustomRuntimeInstanceFactory(instance.InstanceFactory):
  """A factory that creates new custom runtime Instances."""

  SUPPORTS_INTERACTIVE_REQUESTS = True
  FILE_CHANGE_INSTANCE_RESTART_POLICY = instance.NEVER

  START_URL_MAP = appinfo.URLMap(
      url='/_ah/start',
      script='/dev/null',
      login='admin')
  WARMUP_URL_MAP = appinfo.URLMap(
      url='/_ah/warmup',
      script='/dev/null',
      login='admin')

  def __init__(self, request_data, runtime_config_getter, module_configuration):
    """Initializer for CustomRuntimeInstanceFactory.

    Args:
      request_data: A wsgi_request_info.WSGIRequestInfo that will be provided
          with request information for use by API stubs.
      runtime_config_getter: A function that can be called without arguments
          and returns the runtime_config_pb2.Config containing the configuration
          for the runtime.
      module_configuration: An application_configuration.ModuleConfiguration
          instance respresenting the configuration of the module that owns the
          runtime.
    """
    super(CustomRuntimeInstanceFactory, self).__init__(
        request_data, max_concurrent_requests=1, max_background_threads=0)
    self._runtime_config_getter = runtime_config_getter
    self._module_configuration = module_configuration

  def new_instance(self, instance_id, expect_ready_request=False):
    """Create and return a new Instance.

    Args:
      instance_id: A string or integer representing the unique (per module) id
          of the instance.
      expect_ready_request: If True then the instance will be sent a special
          request (i.e. /_ah/warmup or /_ah/start) before it can handle external
          requests.

    Returns:
      The newly created instance.Instance.
    """

    def instance_config_getter():
      runtime_config = self._runtime_config_getter()
      runtime_config.instance_id = str(instance_id)
      return runtime_config

    # This is also checked in a more user-friendly fashion earlier in execution.
    assert self._runtime_config_getter().custom_config.custom_entrypoint

    proxy = http_runtime.HttpRuntimeProxy(
        # Split the input from the command line into a Popen-compatible list.
        shlex.split(
            self._runtime_config_getter().custom_config.custom_entrypoint),
        instance_config_getter,
        self._module_configuration,
        env=dict(os.environ),
        start_process_flavor=http_runtime.START_PROCESS_REVERSE_NO_FILE)
    return instance.Instance(self.request_data, instance_id, proxy,
                             self.max_concurrent_requests,
                             self.max_background_threads, expect_ready_request)
