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




"""A handler that exports various App Engine services over HTTP.

You can export this handler in your app by adding it to the builtins section:

builtins:
- remote_api: on

This will add remote_api serving to the path /_ah/remote_api.

You can also add it to your handlers section, e.g.:

  handlers:
  - url: /remote_api(/.*)?
    script: $PYTHON_LIB/google/appengine/ext/remote_api/handler.py

You can use remote_api_stub to remotely access services exported by this
handler. See the documentation in remote_api_stub.py for details on how to do
this.

The handler supports several forms of authentication. By default, it
checks that the user is an admin using the Users API, similar to specifying
"login: admin" in the app.yaml file. It also supports a 'custom header' mode
which can be used in certain scenarios.

To configure the custom header mode, edit an appengine_config file (the same
one you may use to configure appstats) to include a line like this:

  remoteapi_CUSTOM_ENVIRONMENT_AUTHENTICATION = (
      'HTTP_X_APPENGINE_INBOUND_APPID', ['otherappid'] )

See the ConfigDefaults class below for the full set of options available.
"""










import google
import hashlib
import logging
import os
import pickle
import wsgiref.handlers
import yaml

from google.appengine.api import api_base_pb
from google.appengine.api import apiproxy_stub
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore_types
from google.appengine.api import lib_config
from google.appengine.api import oauth
from google.appengine.api import users
from google.appengine.datastore import datastore_pb
from google.appengine.datastore import datastore_rpc
from google.appengine.ext import webapp
from google.appengine.ext.db import metadata
from google.appengine.ext.remote_api import remote_api_pb
from google.appengine.ext.remote_api import remote_api_services
from google.appengine.runtime import apiproxy_errors
from google.appengine.datastore import entity_pb


class ConfigDefaults(object):
  """Configurable constants.

  To override remote_api configuration values, define values like this
  in your appengine_config.py file (in the root of your app):

    remoteapi_CUSTOM_ENVIRONMENT_AUTHENTICATION = (
        'HTTP_X_APPENGINE_INBOUND_APPID', ['otherappid'] )

  You may wish to base this file on sample_appengine_config.py.
  """

  # Allow other App Engine applications to use remote_api with special forms
  # of authentication which appear in the environment. This is a pair,
  # ( environment variable name, [ list of valid values ] ). Some examples:
  # * Allow other applications to use remote_api:
  #   remoteapi_CUSTOM_ENVIRONMENT_AUTHENTICATION = (
  #       'HTTP_X_APPENGINE_INBOUND_APPID', ['otherappid'] )
  # * Allow two specific users (who need not be admins):
  #   remoteapi_CUSTOM_ENVIRONMENT_AUTHENTICATION = ('USER_ID',
  #                                                  [ '1234', '1111' ] )





  # Note that this an alternate to the normal users.is_current_user_admin
  # check--either one may pass.
  CUSTOM_ENVIRONMENT_AUTHENTICATION = ()


config = lib_config.register('remoteapi', ConfigDefaults.__dict__)


class RemoteDatastoreStub(apiproxy_stub.APIProxyStub):
  """Provides a stub that permits execution of stateful datastore queries.

  Some operations aren't possible using the standard interface. Notably,
  datastore RunQuery operations internally store a cursor that is referenced in
  later Next calls, and cleaned up at the end of each request. Because every
  call to ApiCallHandler takes place in its own request, this isn't possible.

  To work around this, RemoteDatastoreStub provides its own implementation of
  RunQuery that immediately returns the query results.
  """

  def __init__(self, service='datastore_v3', _test_stub_map=None):
    """Constructor.

    Args:
      service: The name of the service
      _test_stub_map: An APIProxyStubMap to use for testing purposes.
    """
    super(RemoteDatastoreStub, self).__init__(service)
    if _test_stub_map:
      self.__call = _test_stub_map.MakeSyncCall
    else:
      self.__call = apiproxy_stub_map.MakeSyncCall

  def _Dynamic_RunQuery(self, request, response):
    """Handle a RunQuery request.

    We handle RunQuery by executing a Query and a Next and returning the result
    of the Next request.

    This method is DEPRECATED, but left in place for older clients.
    """
    runquery_response = datastore_pb.QueryResult()
    self.__call('datastore_v3', 'RunQuery', request, runquery_response)
    if runquery_response.result_size() > 0:

      response.CopyFrom(runquery_response)
      return


    next_request = datastore_pb.NextRequest()
    next_request.mutable_cursor().CopyFrom(runquery_response.cursor())
    next_request.set_count(request.limit())
    self.__call('datastore_v3', 'Next', next_request, response)

  def _Dynamic_TransactionQuery(self, request, response):
    if not request.has_ancestor():
      raise apiproxy_errors.ApplicationError(
          datastore_pb.Error.BAD_REQUEST,
          'No ancestor in transactional query.')

    app_id = datastore_types.ResolveAppId(None)
    if (datastore_rpc._GetDatastoreType(app_id) !=
        datastore_rpc.BaseConnection.HIGH_REPLICATION_DATASTORE):
      raise apiproxy_errors.ApplicationError(
          datastore_pb.Error.BAD_REQUEST,
          'remote_api supports transactional queries only in the '
          'high-replication datastore.')


    entity_group_key = entity_pb.Reference()
    entity_group_key.CopyFrom(request.ancestor())
    group_path = entity_group_key.mutable_path()
    root = entity_pb.Path_Element()
    root.MergeFrom(group_path.element(0))
    group_path.clear_element()
    group_path.add_element().CopyFrom(root)
    eg_element = group_path.add_element()
    eg_element.set_type(metadata.EntityGroup.KIND_NAME)
    eg_element.set_id(metadata.EntityGroup.ID)


    begin_request = datastore_pb.BeginTransactionRequest()
    begin_request.set_app(app_id)
    tx = datastore_pb.Transaction()
    self.__call('datastore_v3', 'BeginTransaction', begin_request, tx)


    request.mutable_transaction().CopyFrom(tx)
    self.__call('datastore_v3', 'RunQuery', request, response.mutable_result())


    get_request = datastore_pb.GetRequest()
    get_request.mutable_transaction().CopyFrom(tx)
    get_request.add_key().CopyFrom(entity_group_key)
    get_response = datastore_pb.GetResponse()
    self.__call('datastore_v3', 'Get', get_request, get_response)
    entity_group = get_response.entity(0)


    response.mutable_entity_group_key().CopyFrom(entity_group_key)
    if entity_group.has_entity():
      response.mutable_entity_group().CopyFrom(entity_group.entity())


    self.__call('datastore_v3', 'Commit', tx, datastore_pb.CommitResponse())

  def _Dynamic_Transaction(self, request, response):
    """Handle a Transaction request.

    We handle transactions by accumulating Put and Delete requests on the client
    end, as well as recording the key and hash of Get requests. When Commit is
    called, Transaction is invoked, which verifies that all the entities in the
    precondition list still exist and their hashes match, then performs a
    transaction of its own to make the updates.
    """

    begin_request = datastore_pb.BeginTransactionRequest()
    begin_request.set_app(os.environ['APPLICATION_ID'])
    begin_request.set_allow_multiple_eg(request.allow_multiple_eg())
    tx = datastore_pb.Transaction()
    self.__call('datastore_v3', 'BeginTransaction', begin_request, tx)


    preconditions = request.precondition_list()
    if preconditions:
      get_request = datastore_pb.GetRequest()
      get_request.mutable_transaction().CopyFrom(tx)
      for precondition in preconditions:
        key = get_request.add_key()
        key.CopyFrom(precondition.key())
      get_response = datastore_pb.GetResponse()
      self.__call('datastore_v3', 'Get', get_request, get_response)
      entities = get_response.entity_list()
      assert len(entities) == request.precondition_size()
      for precondition, entity in zip(preconditions, entities):
        if precondition.has_hash() != entity.has_entity():
          raise apiproxy_errors.ApplicationError(
              datastore_pb.Error.CONCURRENT_TRANSACTION,
              "Transaction precondition failed.")
        elif entity.has_entity():
          entity_hash = hashlib.sha1(entity.entity().Encode()).digest()
          if precondition.hash() != entity_hash:
            raise apiproxy_errors.ApplicationError(
                datastore_pb.Error.CONCURRENT_TRANSACTION,
                "Transaction precondition failed.")


    if request.has_puts():
      put_request = request.puts()
      put_request.mutable_transaction().CopyFrom(tx)
      self.__call('datastore_v3', 'Put', put_request, response)


    if request.has_deletes():
      delete_request = request.deletes()
      delete_request.mutable_transaction().CopyFrom(tx)
      self.__call('datastore_v3', 'Delete', delete_request,
                  datastore_pb.DeleteResponse())


    self.__call('datastore_v3', 'Commit', tx, datastore_pb.CommitResponse())

  def _Dynamic_GetIDsXG(self, request, response):
    self._Dynamic_GetIDs(request, response, is_xg=True)

  def _Dynamic_GetIDs(self, request, response, is_xg=False):
    """Fetch unique IDs for a set of paths."""

    for entity in request.entity_list():
      assert entity.property_size() == 0
      assert entity.raw_property_size() == 0
      assert entity.entity_group().element_size() == 0
      lastpart = entity.key().path().element_list()[-1]
      assert lastpart.id() == 0 and not lastpart.has_name()


    begin_request = datastore_pb.BeginTransactionRequest()
    begin_request.set_app(os.environ['APPLICATION_ID'])
    begin_request.set_allow_multiple_eg(is_xg)
    tx = datastore_pb.Transaction()
    self.__call('datastore_v3', 'BeginTransaction', begin_request, tx)


    self.__call('datastore_v3', 'Put', request, response)


    self.__call('datastore_v3', 'Rollback', tx, api_base_pb.VoidProto())



SERVICE_PB_MAP = remote_api_services.SERVICE_PB_MAP

class ApiCallHandler(webapp.RequestHandler):
  """A webapp handler that accepts API calls over HTTP and executes them."""

  LOCAL_STUBS = {
      'remote_datastore': RemoteDatastoreStub('remote_datastore'),
  }

  OAUTH_SCOPES = [
      'https://www.googleapis.com/auth/appengine.apis',
      'https://www.googleapis.com/auth/cloud-platform',
  ]

  def CheckIsAdmin(self):
    user_is_authorized = False
    if users.is_current_user_admin():
      user_is_authorized = True
    if not user_is_authorized and config.CUSTOM_ENVIRONMENT_AUTHENTICATION:
      if len(config.CUSTOM_ENVIRONMENT_AUTHENTICATION) == 2:
        var, values = config.CUSTOM_ENVIRONMENT_AUTHENTICATION
        if os.getenv(var) in values:
          user_is_authorized = True
      else:
        logging.warning('remoteapi_CUSTOM_ENVIRONMENT_AUTHENTICATION is '
                        'configured incorrectly.')

    if not user_is_authorized:
      try:
        user_is_authorized = (
            oauth.is_current_user_admin(_scope=self.OAUTH_SCOPES))
      except oauth.OAuthRequestError:

        pass
    if not user_is_authorized:
      self.response.set_status(401)
      self.response.out.write(
          'You must be logged in as an administrator to access this.')
      self.response.headers['Content-Type'] = 'text/plain'
      return False
    if 'X-appcfg-api-version' not in self.request.headers:
      self.response.set_status(403)
      self.response.out.write('This request did not contain a necessary header')
      self.response.headers['Content-Type'] = 'text/plain'
      return False
    return True


  def get(self):
    """Handle a GET. Just show an info page."""
    if not self.CheckIsAdmin():
      return

    rtok = self.request.get('rtok', '0')
    app_info = {
        'app_id': os.environ['APPLICATION_ID'],
        'rtok': rtok
        }

    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write(yaml.dump(app_info))

  def post(self):
    """Handle POST requests by executing the API call."""
    if not self.CheckIsAdmin():
      return
















    self.response.headers['Content-Type'] = 'text/plain'

    response = remote_api_pb.Response()
    try:
      request = remote_api_pb.Request()



      request.ParseFromString(self.request.body)
      response_data = self.ExecuteRequest(request)
      response.set_response(response_data.Encode())
      self.response.set_status(200)
    except Exception, e:
      logging.exception('Exception while handling %s', request)
      self.response.set_status(200)



      response.set_exception(pickle.dumps(e))
      if isinstance(e, apiproxy_errors.ApplicationError):
        application_error = response.mutable_application_error()
        application_error.set_code(e.application_error)
        application_error.set_detail(e.error_detail)
    self.response.out.write(response.Encode())

  def ExecuteRequest(self, request):
    """Executes an API invocation and returns the response object."""
    service = request.service_name()
    method = request.method()
    service_methods = SERVICE_PB_MAP.get(service, {})
    request_class, response_class = service_methods.get(method, (None, None))
    if not request_class:
      raise apiproxy_errors.CallNotFoundError()

    request_data = request_class()
    request_data.ParseFromString(request.request())
    response_data = response_class()

    if service in self.LOCAL_STUBS:
      self.LOCAL_STUBS[service].MakeSyncCall(service, method, request_data,
                                             response_data)
    else:
      apiproxy_stub_map.MakeSyncCall(service, method, request_data,
                                     response_data)

    return response_data

  def InfoPage(self):
    """Renders an information page."""
    return """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html><head>
<title>App Engine API endpoint.</title>
</head><body>
<h1>App Engine API endpoint.</h1>
<p>This is an endpoint for the App Engine remote API interface.
Point your stubs (google.appengine.ext.remote_api.remote_api_stub) here.</p>
</body>
</html>"""

application = webapp.WSGIApplication([('.*', ApiCallHandler)])


def main():
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
