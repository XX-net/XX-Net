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




"""Stub version of the capability service API, everything is always enabled."""








from google.appengine.api import apiproxy_stub
from google.appengine.api import capabilities


IsEnabledRequest = capabilities.IsEnabledRequest
IsEnabledResponse = capabilities.IsEnabledResponse
CapabilityConfig = capabilities.CapabilityConfig



SUPPORTED_CAPABILITIES = (
    'blobstore',
    'datastore_v3',
    'images',
    'mail',
    'memcache',
    'taskqueue',
    'urlfetch',
    'xmpp',
)


class CapabilityServiceStub(apiproxy_stub.APIProxyStub):
  """Python only capability service stub."""

  THREADSAFE = True

  def __init__(self, service_name='capability_service'):
    """Constructor.

    Args:
      service_name: Service name expected for all calls.
    """
    super(CapabilityServiceStub, self).__init__(service_name)


    self._packages = dict.fromkeys(SUPPORTED_CAPABILITIES, True)

  def SetPackageEnabled(self, package, enabled):
    """Set all features of a given package to enabled.

    This method is thread-unsafe, so should only be called during set-up, before
    multiple API server threads start.

    Args:
      package: Name of package.
      enabled: True to enable, False to disable.
    """

    self._packages[package] = enabled



  def _Dynamic_IsEnabled(self, request, response):
    """Implementation of CapabilityService::IsEnabled().

    Args:
      request: An IsEnabledRequest.
      response: An IsEnabledResponse.
    """
    default_config = response.add_config()
    default_config.set_package('')
    default_config.set_capability('')

    try:
      package_enabled = self._packages[request.package()]
    except KeyError:
      summary_status = IsEnabledResponse.UNKNOWN
      config_status = CapabilityConfig.UNKNOWN
    else:
      if package_enabled:
        summary_status = IsEnabledResponse.ENABLED
        config_status = CapabilityConfig.ENABLED
      else:
        summary_status = IsEnabledResponse.DISABLED
        config_status = CapabilityConfig.DISABLED
    response.set_summary_status(summary_status)
    default_config.set_status(config_status)
