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




"""Stubs for System service."""








import random

from google.appengine.api import apiproxy_stub
from google.appengine.api import request_info
from google.appengine.api.system import system_service_pb
from google.appengine.runtime import apiproxy_errors


class SystemServiceStub(apiproxy_stub.APIProxyStub):
  """Python stub for System service.

  This stub is very simple at the moment; it only returns fixed values.

  It also provides a place for the dev_appserver to record backend info.
  """

  _ACCEPTS_REQUEST_ID = True

  def __init__(self, default_cpu=None, default_memory=None, request_data=None):
    """Constructor.

    Args:
      default_cpu: SystemStat; if set, value will be used for GetSystemStats.
      default_memory: SystemStat; if set, value will be used for GetSystemStats.
      request_data: A request_info.RequestInfo instance used to look up state
          associated with the request that generated an API call.
    """
    super(SystemServiceStub, self).__init__('system', request_data=request_data)
    self.default_cpu = default_cpu
    self.default_memory = default_memory


    self.num_calls = {}


    self._backend_info = None

  def _Dynamic_GetSystemStats(self, unused_request, response,
                              unused_request_id):
    """Mock version of System stats always returns fixed values."""

    cpu = response.mutable_cpu()
    if self.default_cpu:
      cpu.CopyFrom(self.default_cpu)

    memory = response.mutable_memory()
    if self.default_memory:
      memory.CopyFrom(self.default_memory)

    self.num_calls["GetSystemStats"] = (
        self.num_calls.get("GetSystemStats", 0) + 1)

  def _Dynamic_StartBackgroundRequest(self, unused_request, response,
                                      request_id):
    background_request_id = '%x' % random.randrange(1 << 64)
    try:
      self.request_data.get_dispatcher().send_background_request(
          self.request_data.get_module(request_id),
          self.request_data.get_version(request_id),
          self.request_data.get_instance(request_id),
          background_request_id)
    except request_info.NotSupportedWithAutoScalingError:
      raise apiproxy_errors.ApplicationError(
          system_service_pb.SystemServiceError.BACKEND_REQUIRED)
    except request_info.BackgroundThreadLimitReachedError:
      raise apiproxy_errors.ApplicationError(
          system_service_pb.SystemServiceError.LIMIT_REACHED)
    response.set_request_id(background_request_id)

  def set_backend_info(self, backend_info):
    """Set backend info. Typically a list of BackendEntry objects."""
    self._backend_info = backend_info

  def get_backend_info(self):
    """Set backend info. Typically a list of BackendEntry objects."""
    return self._backend_info
