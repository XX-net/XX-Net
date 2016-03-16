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




"""A NotImplemented Images API stub for when the PIL library is not found."""

from google.appengine.api import apiproxy_stub
from google.appengine.api.images import images_blob_stub

_SERVICE_NAME = 'images'


class ImagesNotImplementedServiceStub(apiproxy_stub.APIProxyStub):
  """Stub version of images API which raises a NotImplementedError."""

  def __init__(self, host_prefix=''):
    super(ImagesNotImplementedServiceStub, self).__init__(_SERVICE_NAME)
    self._blob_stub = images_blob_stub.ImagesBlobStub(host_prefix)

  def MakeSyncCall(self, service, call, request, response, request_id=None):
    """Main entry point.

    Args:
      service: str, must be 'images'.
      call: str, name of the RPC to make, must be part of ImagesService.
      request: pb object, corresponding args to the 'call' argument.
      response: pb object, return value for the 'call' argument.
      request_id: A unique string identifying the request associated with the
          API call.
    """
    if service == _SERVICE_NAME:
      if call == 'GetUrlBase':
        self._blob_stub.GetUrlBase(request, response)
        return
      elif call == 'DeleteUrlBase':
        self._blob_stub.DeleteUrlBase(request, response)
        return
    raise NotImplementedError('Unable to find the Python PIL library.  Please '
                              'view the SDK documentation for details about '
                              'installing PIL on your system.')
