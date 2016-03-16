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
"""A Cloud Datastore stub that connects to a remote Datastore service."""

from google.appengine.api import apiproxy_rpc
from google.appengine.api import datastore_errors
from google.appengine.datastore import datastore_pbs
from google.appengine.datastore import datastore_rpc

class CloudDatastoreV1RemoteStub(object):
  """A stub for calling Cloud Datastore via the Cloud Datastore API."""

  def __init__(self, datastore):
    """Constructs a new Cloud Datastore stub.

    Args:
      datastore: A googledatastore.Datastore object.
    """
    self._datastore = datastore

  def MakeSyncCall(self, service, call, request, response):
    assert service == 'cloud_datastore_v1beta3'


    call = call[0:1].lower() + call[1:]


    try:
      response.CopyFrom(
          self._datastore._call_method(call, request, response.__class__))
    except datastore_pbs.googledatastore.RPCError, e:
      raise datastore_rpc._DatastoreExceptionFromCanonicalErrorCodeAndDetail(
          e.code, e.message)
    except Exception, e:
      raise datastore_errors.InternalError(e)

  def CreateRPC(self):
    return apiproxy_rpc.RPC(stub=self)
