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




"""An apiproxy stub that calls a remote handler via HTTP.

This allows easy remote access to the App Engine datastore, and potentially any
of the other App Engine APIs, using the same interface you use when accessing
the service locally.

An example Python script:
---
from google.appengine.ext import db
from google.appengine.ext.remote_api import remote_api_stub
from myapp import models
import getpass

def auth_func():
  return (raw_input('Username:'), getpass.getpass('Password:'))

remote_api_stub.ConfigureRemoteApi(None, '/_ah/remote_api', auth_func,
                                   'my-app.appspot.com')

# Now you can access the remote datastore just as if your code was running on
# App Engine!

houses = models.House.all().fetch(100)
for a_house in q:
  a_house.doors += 1
db.put(houses)
---

A few caveats:
- Where possible, avoid iterating over queries. Fetching as many results as you
  will need is faster and more efficient. If you don't know how many results
  you need, or you need 'all of them', iterating is fine.
- Likewise, it's a good idea to put entities in batches. Instead of calling put
  for each individual entity, accumulate them and put them in batches using
  db.put(), if you can.
- Requests and responses are still limited to 1MB each, so if you have large
  entities or try and fetch or put many of them at once, your requests may fail.
"""










import google
import os
import pickle
import random
import sys
import thread
import threading
import yaml
import hashlib


if os.environ.get('APPENGINE_RUNTIME') == 'python27':
  from google.appengine.api import apiproxy_rpc
  from google.appengine.api import apiproxy_stub_map
  from google.appengine.datastore import datastore_pb
  from google.appengine.ext.remote_api import remote_api_pb
  from google.appengine.ext.remote_api import remote_api_services
  from google.appengine.runtime import apiproxy_errors
else:
  from google.appengine.api import apiproxy_rpc
  from google.appengine.api import apiproxy_stub_map
  from google.appengine.datastore import datastore_pb
  from google.appengine.ext.remote_api import remote_api_pb
  from google.appengine.ext.remote_api import remote_api_services
  from google.appengine.runtime import apiproxy_errors

from google.appengine.tools import appengine_rpc


_REQUEST_ID_HEADER = 'HTTP_X_APPENGINE_REQUEST_ID'


class Error(Exception):
  """Base class for exceptions in this module."""


class ConfigurationError(Error):
  """Exception for configuration errors."""


class UnknownJavaServerError(Error):
  """Exception for exceptions returned from a Java remote_api handler."""


def GetUserAgent():
  """Determines the value of the 'User-agent' header to use for HTTP requests.

  Returns:
    String containing the 'user-agent' header value, which includes the SDK
    version, the platform information, and the version of Python;
    e.g., "remote_api/1.0.1 Darwin/9.2.0 Python/2.5.2".
  """
  product_tokens = []

  product_tokens.append("Google-remote_api/1.0")


  product_tokens.append(appengine_rpc.GetPlatformToken())


  python_version = ".".join(str(i) for i in sys.version_info)
  product_tokens.append("Python/%s" % python_version)

  return " ".join(product_tokens)


def GetSourceName():
  return "Google-remote_api-1.0"


def HashEntity(entity):
  """Return a very-likely-unique hash of an entity."""
  return hashlib.sha1(entity.Encode()).digest()


class TransactionData(object):
  """Encapsulates data about an individual transaction."""

  def __init__(self, thread_id, is_xg):


    self.thread_id = thread_id



    self.preconditions = {}




    self.entities = {}

    self.is_xg = is_xg


class RemoteStub(object):
  """A stub for calling services on a remote server over HTTP.

  You can use this to stub out any service that the remote server supports.
  """


  _local = threading.local()

  def __init__(self, server, path, _test_stub_map=None):
    """Constructs a new RemoteStub that communicates with the specified server.

    Args:
      server: An instance of a subclass of
        google.appengine.tools.appengine_rpc.AbstractRpcServer.
      path: The path to the handler this stub should send requests to.
    """


    self._server = server
    self._path = path
    self._test_stub_map = _test_stub_map

  def _PreHookHandler(self, service, call, request, response):
    pass

  def _PostHookHandler(self, service, call, request, response):
    pass

  def MakeSyncCall(self, service, call, request, response):
    self._PreHookHandler(service, call, request, response)
    try:
      test_stub = self._test_stub_map and self._test_stub_map.GetStub(service)
      if test_stub:

        test_stub.MakeSyncCall(service, call, request, response)
      else:
        self._MakeRealSyncCall(service, call, request, response)
    finally:
      self._PostHookHandler(service, call, request, response)

  @classmethod
  def _GetRequestId(cls):
    """Returns the id of the request associated with the current thread."""
    return cls._local.request_id

  @classmethod
  def _SetRequestId(cls, request_id):
    """Set the id of the request associated with the current thread."""
    cls._local.request_id = request_id

  def _MakeRealSyncCall(self, service, call, request, response):
    request_pb = remote_api_pb.Request()
    request_pb.set_service_name(service)
    request_pb.set_method(call)
    request_pb.set_request(request.Encode())
    if hasattr(self._local, 'request_id'):


      request_pb.set_request_id(self._local.request_id)

    response_pb = remote_api_pb.Response()
    encoded_request = request_pb.Encode()
    encoded_response = self._server.Send(self._path, encoded_request)
    response_pb.ParseFromString(encoded_response)

    if response_pb.has_application_error():
      error_pb = response_pb.application_error()
      raise apiproxy_errors.ApplicationError(error_pb.code(),
                                             error_pb.detail())
    elif response_pb.has_exception():
      raise pickle.loads(response_pb.exception())
    elif response_pb.has_java_exception():
      raise UnknownJavaServerError("An unknown error has occured in the "
                                   "Java remote_api handler for this call.")
    else:
      response.ParseFromString(response_pb.response())

  def CreateRPC(self):
    return apiproxy_rpc.RPC(stub=self)


class RemoteDatastoreStub(RemoteStub):
  """A specialised stub for accessing the App Engine datastore remotely.

  A specialised stub is required because there are some datastore operations
  that preserve state between calls. This stub makes queries possible.
  Transactions on the remote datastore are unfortunately still impossible.
  """

  def __init__(self, server, path, default_result_count=20,
               _test_stub_map=None):
    """Constructor.

    Args:
      server: The server name to connect to.
      path: The URI path on the server.
      default_result_count: The number of items to fetch, by default, in a
        datastore Query or Next operation. This affects the batch size of
        query iterators.
    """
    super(RemoteDatastoreStub, self).__init__(server, path, _test_stub_map)
    self.default_result_count = default_result_count
    self.__queries = {}
    self.__transactions = {}




    self.__next_local_cursor = 1
    self.__local_cursor_lock = threading.Lock()
    self.__next_local_tx = 1
    self.__local_tx_lock = threading.Lock()

  def MakeSyncCall(self, service, call, request, response):
    assert service == 'datastore_v3'

    explanation = []
    assert request.IsInitialized(explanation), explanation

    handler = getattr(self, '_Dynamic_' + call, None)
    if handler:
      handler(request, response)
    else:
      super(RemoteDatastoreStub, self).MakeSyncCall(service, call, request,
                                                    response)

    assert response.IsInitialized(explanation), explanation

  def _Dynamic_RunQuery(self, query, query_result, cursor_id = None):
    if query.has_transaction():
      txdata = self.__transactions[query.transaction().handle()]
      tx_result = remote_api_pb.TransactionQueryResult()
      super(RemoteDatastoreStub, self).MakeSyncCall(
          'remote_datastore', 'TransactionQuery', query, tx_result)
      query_result.CopyFrom(tx_result.result())




      eg_key = tx_result.entity_group_key()
      encoded_eg_key = eg_key.Encode()
      eg_hash = None
      if tx_result.has_entity_group():
        eg_hash = HashEntity(tx_result.entity_group())
      old_key, old_hash = txdata.preconditions.get(encoded_eg_key, (None, None))
      if old_key is None:
        txdata.preconditions[encoded_eg_key] = (eg_key, eg_hash)
      elif old_hash != eg_hash:
        raise apiproxy_errors.ApplicationError(
            datastore_pb.Error.CONCURRENT_TRANSACTION,
            'Transaction precondition failed.')
    else:
      super(RemoteDatastoreStub, self).MakeSyncCall(
          'datastore_v3', 'RunQuery', query, query_result)

    if cursor_id is None:
      self.__local_cursor_lock.acquire()
      try:
        cursor_id = self.__next_local_cursor
        self.__next_local_cursor += 1
      finally:
        self.__local_cursor_lock.release()

    if query_result.more_results():
      query.set_offset(query.offset() + query_result.result_size())
      if query.has_limit():
        query.set_limit(query.limit() - query_result.result_size())
      self.__queries[cursor_id] = query
    else:
      self.__queries[cursor_id] = None


    query_result.mutable_cursor().set_cursor(cursor_id)

  def _Dynamic_Next(self, next_request, query_result):
    assert next_request.offset() == 0
    cursor_id = next_request.cursor().cursor()
    if cursor_id not in self.__queries:
      raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                             'Cursor %d not found' % cursor_id)
    query = self.__queries[cursor_id]

    if query is None:

      query_result.set_more_results(False)
      return
    else:
      if next_request.has_count():
        query.set_count(next_request.count())
      else:
        query.clear_count()

    self._Dynamic_RunQuery(query, query_result, cursor_id)




    query_result.set_skipped_results(0)

  def _Dynamic_Get(self, get_request, get_response):
    txid = None
    if get_request.has_transaction():

      txid = get_request.transaction().handle()
      txdata = self.__transactions[txid]
      assert (txdata.thread_id ==
          thread.get_ident()), "Transactions are single-threaded."


      keys = [(k, k.Encode()) for k in get_request.key_list()]


      new_request = datastore_pb.GetRequest()
      for key, enckey in keys:
        if enckey not in txdata.entities:
          new_request.add_key().CopyFrom(key)
    else:
      new_request = get_request

    if new_request.key_size() > 0:
      super(RemoteDatastoreStub, self).MakeSyncCall(
          'datastore_v3', 'Get', new_request, get_response)

    if txid is not None:

      newkeys = new_request.key_list()
      entities = get_response.entity_list()
      for key, entity in zip(newkeys, entities):
        entity_hash = None
        if entity.has_entity():
          entity_hash = HashEntity(entity.entity())
        txdata.preconditions[key.Encode()] = (key, entity_hash)





      new_response = datastore_pb.GetResponse()
      it = iter(get_response.entity_list())
      for key, enckey in keys:
        if enckey in txdata.entities:
          cached_entity = txdata.entities[enckey][1]
          if cached_entity:
            new_response.add_entity().mutable_entity().CopyFrom(cached_entity)
          else:
            new_response.add_entity()
        else:
          new_entity = it.next()
          if new_entity.has_entity():
            assert new_entity.entity().key() == key
            new_response.add_entity().CopyFrom(new_entity)
          else:
            new_response.add_entity()
      get_response.CopyFrom(new_response)

  def _Dynamic_Put(self, put_request, put_response):
    if put_request.has_transaction():
      entities = put_request.entity_list()


      requires_id = lambda x: x.id() == 0 and not x.has_name()
      new_ents = [e for e in entities
                  if requires_id(e.key().path().element_list()[-1])]
      id_request = datastore_pb.PutRequest()

      txid = put_request.transaction().handle()
      txdata = self.__transactions[txid]
      assert (txdata.thread_id ==
          thread.get_ident()), "Transactions are single-threaded."
      if new_ents:
        for ent in new_ents:
          e = id_request.add_entity()
          e.mutable_key().CopyFrom(ent.key())
          e.mutable_entity_group()
        id_response = datastore_pb.PutResponse()



        if txdata.is_xg:
          rpc_name = 'GetIDsXG'
        else:
          rpc_name = 'GetIDs'
        super(RemoteDatastoreStub, self).MakeSyncCall(
            'remote_datastore', rpc_name, id_request, id_response)
        assert id_request.entity_size() == id_response.key_size()
        for key, ent in zip(id_response.key_list(), new_ents):
          ent.mutable_key().CopyFrom(key)
          ent.mutable_entity_group().add_element().CopyFrom(
              key.path().element(0))

      for entity in entities:
        txdata.entities[entity.key().Encode()] = (entity.key(), entity)
        put_response.add_key().CopyFrom(entity.key())
    else:
      super(RemoteDatastoreStub, self).MakeSyncCall(
          'datastore_v3', 'Put', put_request, put_response)

  def _Dynamic_Delete(self, delete_request, response):
    if delete_request.has_transaction():
      txid = delete_request.transaction().handle()
      txdata = self.__transactions[txid]
      assert (txdata.thread_id ==
          thread.get_ident()), "Transactions are single-threaded."
      for key in delete_request.key_list():
        txdata.entities[key.Encode()] = (key, None)
    else:
      super(RemoteDatastoreStub, self).MakeSyncCall(
          'datastore_v3', 'Delete', delete_request, response)

  def _Dynamic_BeginTransaction(self, request, transaction):
    self.__local_tx_lock.acquire()
    try:
      txid = self.__next_local_tx
      self.__transactions[txid] = TransactionData(thread.get_ident(),
                                                  request.allow_multiple_eg())
      self.__next_local_tx += 1
    finally:
      self.__local_tx_lock.release()
    transaction.set_handle(txid)
    transaction.set_app(request.app())

  def _Dynamic_Commit(self, transaction, transaction_response):
    txid = transaction.handle()
    if txid not in self.__transactions:
      raise apiproxy_errors.ApplicationError(
          datastore_pb.Error.BAD_REQUEST,
          'Transaction %d not found.' % (txid,))

    txdata = self.__transactions[txid]
    assert (txdata.thread_id ==
        thread.get_ident()), "Transactions are single-threaded."
    del self.__transactions[txid]

    tx = remote_api_pb.TransactionRequest()
    tx.set_allow_multiple_eg(txdata.is_xg)
    for key, txhash in txdata.preconditions.values():
      precond = tx.add_precondition()
      precond.mutable_key().CopyFrom(key)
      if txhash:
        precond.set_hash(txhash)

    puts = tx.mutable_puts()
    deletes = tx.mutable_deletes()
    for key, entity in txdata.entities.values():
      if entity:
        puts.add_entity().CopyFrom(entity)
      else:
        deletes.add_key().CopyFrom(key)


    super(RemoteDatastoreStub, self).MakeSyncCall(
        'remote_datastore', 'Transaction',
        tx, datastore_pb.PutResponse())

  def _Dynamic_Rollback(self, transaction, transaction_response):
    txid = transaction.handle()
    self.__local_tx_lock.acquire()
    try:
      if txid not in self.__transactions:
        raise apiproxy_errors.ApplicationError(
            datastore_pb.Error.BAD_REQUEST,
            'Transaction %d not found.' % (txid,))

      txdata = self.__transactions[txid]
      assert (txdata.thread_id ==
          thread.get_ident()), "Transactions are single-threaded."
      del self.__transactions[txid]
    finally:
      self.__local_tx_lock.release()

  def _Dynamic_CreateIndex(self, index, id_response):
    raise apiproxy_errors.CapabilityDisabledError(
        'The remote datastore does not support index manipulation.')

  def _Dynamic_UpdateIndex(self, index, void):
    raise apiproxy_errors.CapabilityDisabledError(
        'The remote datastore does not support index manipulation.')

  def _Dynamic_DeleteIndex(self, index, void):
    raise apiproxy_errors.CapabilityDisabledError(
        'The remote datastore does not support index manipulation.')


ALL_SERVICES = set(remote_api_services.SERVICE_PB_MAP)


def GetRemoteAppIdFromServer(server, path, remote_token=None):
  """Return the app id from a connection to an existing server.

  Args:
    server: An appengine_rpc.AbstractRpcServer
    path: The path to the remote_api handler for your app
      (for example, '/_ah/remote_api').
    remote_token: Token to validate that the response was to this request.
  Returns:
    App ID as reported by the remote server.
  Raises:
    ConfigurationError: The server returned an invalid response.
  """
  if not remote_token:
    random.seed()
    remote_token = str(random.random())[2:]
  remote_token = str(remote_token)
  urlargs = {'rtok': remote_token}
  response = server.Send(path, payload=None, **urlargs)
  if not response.startswith('{'):
    raise ConfigurationError(
        'Invalid response received from server: %s' % response)
  app_info = yaml.load(response)
  if not app_info or 'rtok' not in app_info or 'app_id' not in app_info:
    raise ConfigurationError('Error parsing app_id lookup response')
  if str(app_info['rtok']) != remote_token:
    raise ConfigurationError('Token validation failed during app_id lookup. '
                             '(sent %s, got %s)' % (repr(remote_token),
                                                    repr(app_info['rtok'])))
  return app_info['app_id']


def ConfigureRemoteApiFromServer(server, path, app_id, services=None,
                                 default_auth_domain=None,
                                 use_remote_datastore=True):
  """Does necessary setup to allow easy remote access to App Engine APIs.

  Args:
    server: An AbstractRpcServer
    path: The path to the remote_api handler for your app
      (for example, '/_ah/remote_api').
    app_id: The app_id of your app, as declared in app.yaml.
    services: A list of services to set up stubs for. If specified, only those
      services are configured; by default all supported services are configured.
    default_auth_domain: The authentication domain to use by default.
    use_remote_datastore: Whether to use RemoteDatastoreStub instead of passing
      through datastore requests. RemoteDatastoreStub batches transactional
      datastore requests since, in production, datastore requires are scoped to
      a single request.

  Raises:
    urllib2.HTTPError: if app_id is not provided and there is an error while
      retrieving it.
    ConfigurationError: if there is a error configuring the Remote API.
  """
  if services is None:
    services = set(ALL_SERVICES)
  else:
    services = set(services)
    unsupported = services.difference(ALL_SERVICES)
    if unsupported:
      raise ConfigurationError('Unsupported service(s): %s'
                               % (', '.join(unsupported),))

  os.environ['APPLICATION_ID'] = app_id
  os.environ.setdefault('AUTH_DOMAIN', default_auth_domain or 'gmail.com')
  apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
  if 'datastore_v3' in services and use_remote_datastore:
    services.remove('datastore_v3')
    datastore_stub = RemoteDatastoreStub(server, path)
    apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', datastore_stub)
  stub = RemoteStub(server, path)
  for service in services:
    apiproxy_stub_map.apiproxy.RegisterStub(service, stub)


def GetRemoteAppId(servername,
                   path,
                   auth_func,
                   rpc_server_factory=appengine_rpc.HttpRpcServer,
                   rtok=None,
                   secure=False,
                   save_cookies=False):
  """Get the remote appid as reported at servername/path.

  This will also return an AbstractRpcServer server, which can be used with
  ConfigureRemoteApiFromServer.

  Args:
    servername: The hostname your app is deployed on.
    path: The path to the remote_api handler for your app
      (for example, '/_ah/remote_api').
    auth_func: A function that takes no arguments and returns a
      (username, password) tuple. This will be called if your application
      requires authentication to access the remote_api handler (it should!)
      and you do not already have a valid auth cookie.
      <app_id>.appspot.com.
    rpc_server_factory: A factory to construct the rpc server for the datastore.
    rtok: The validation token to sent with app_id lookups. If None, a random
      token is used.
    secure: Use SSL when communicating with the server.
    save_cookies: Forwarded to rpc_server_factory function.

  Returns:
    (app_id, server): The application ID and an AbstractRpcServer.
  """
  server = rpc_server_factory(servername, auth_func, GetUserAgent(),
                              GetSourceName(), save_cookies=save_cookies,
                              debug_data=False, secure=secure)
  app_id = GetRemoteAppIdFromServer(server, path, rtok)
  return app_id, server



_OAUTH_SCOPES = [
    'https://www.googleapis.com/auth/appengine.apis',
    'https://www.googleapis.com/auth/userinfo.email',
    ]


def ConfigureRemoteApiForOAuth(
    servername, path, secure=True, service_account=None, key_file_path=None,
    oauth2_parameters=None, save_cookies=False, auth_tries=3,
    rpc_server_factory=None, app_id=None):
  """Does necessary setup to allow easy remote access to App Engine APIs.

  This function uses OAuth2 with Application Default Credentials
  to communicate with App Engine APIs.

  For more information on Application Default Credentials, see:
  https://developers.google.com/accounts/docs/application-default-credentials

  Args:
    servername: The hostname your app is deployed on.
    path: The path to the remote_api handler for your app
      (for example, '/_ah/remote_api').
    secure: If true, will use SSL to communicate with server. Unlike
      ConfigureRemoteApi, this is true by default.
    service_account: The email address of the service account to use for
      making OAuth requests. If none, the application default will be used
      instead.
    key_file_path: The path to a .p12 file containing the private key for
      service_account. Must be set if service_account is provided.
    oauth2_parameters: None, or an
      appengine_rpc_httplib2.HttpRpcServerOAuth2.OAuth2Parameters object
      representing the OAuth2 parameters for this connection.
    save_cookies: If true, save OAuth2 information in a file.
    auth_tries: Number of attempts to make to authenticate.
    rpc_server_factory: Factory to make RPC server instances.
    app_id: The app_id of your app, as declared in app.yaml, or None.

  Returns:
    server, a server which may be useful for calling the application directly.

  Raises:
    urllib2.HTTPError: if there is an error while retrieving the app id.
    ConfigurationError: if there is a error configuring the DatstoreFileStub.
    ImportError: if the oauth2client or appengine_rpc_httplib2
      module is not available.
    ValueError: if only one of service_account and key_file_path is provided.
  """

  if bool(service_account) != bool(key_file_path):
    raise ValueError('Must provide both service_account and key_file_path.')

  try:

    from oauth2client import client
  except ImportError, e:
    raise ImportError('Use of OAuth credentials requires the '
                      'oauth2client module: %s' % e)

  try:

    from google.appengine.tools import appengine_rpc_httplib2
  except ImportError, e:
    raise ImportError('Use of OAuth credentials requires the '
                      'appengine_rpc_httplib2 module. %s' % e)

  rpc_server_factory = (rpc_server_factory
                        or appengine_rpc_httplib2.HttpRpcServerOAuth2)

  if not oauth2_parameters:
    if key_file_path:
      if not client.HAS_CRYPTO:
        raise ImportError('Use of a key file to access the Remote API '
                          'requires an encryption library. Please install '
                          'either PyOpenSSL or PyCrypto 2.6 or later.')

      with open(key_file_path, 'rb') as key_file:
        key = key_file.read()
        credentials = client.SignedJwtAssertionCredentials(
            service_account,
            key,
            _OAUTH_SCOPES)
    else:
      credentials = client.GoogleCredentials.get_application_default()
      credentials = credentials.create_scoped(_OAUTH_SCOPES)


    oauth2_parameters = (
        appengine_rpc_httplib2.HttpRpcServerOAuth2.OAuth2Parameters(
            access_token=None,
            client_id=None,
            client_secret=None,
            scope=_OAUTH_SCOPES,
            refresh_token=None,
            credential_file=None,
            credentials=credentials))

  return ConfigureRemoteApi(
      app_id=app_id,
      path=path,
      auth_func=oauth2_parameters,
      servername=servername,
      secure=secure,
      save_cookies=save_cookies,
      auth_tries=auth_tries,
      rpc_server_factory=rpc_server_factory)


def ConfigureRemoteApi(app_id,
                       path,
                       auth_func,
                       servername=None,
                       rpc_server_factory=appengine_rpc.HttpRpcServer,
                       rtok=None,
                       secure=False,
                       services=None,
                       default_auth_domain=None,
                       save_cookies=False,
                       auth_tries=3,
                       use_remote_datastore=True):
  """Does necessary setup to allow easy remote access to App Engine APIs.

  Either servername must be provided or app_id must not be None.  If app_id
  is None and a servername is provided, this function will send a request
  to the server to retrieve the app_id.

  Note that if the app_id is specified, the internal appid must be used;
  this may include a partition and a domain. It is often easier to let
  remote_api_stub retrieve the app_id automatically.

  Args:
    app_id: The app_id of your app, as declared in app.yaml, or None.
    path: The path to the remote_api handler for your app
      (for example, '/_ah/remote_api').
    auth_func: A function that takes no arguments and returns a
      (username, password) tuple. This will be called if your application
      requires authentication to access the remote_api handler (it should!)
      and you do not already have a valid auth cookie.
    servername: The hostname your app is deployed on. Defaults to
      <app_id>.appspot.com.
    rpc_server_factory: A factory to construct the rpc server for the datastore.
    rtok: The validation token to sent with app_id lookups. If None, a random
      token is used.
    secure: Use SSL when communicating with the server.
    services: A list of services to set up stubs for. If specified, only those
      services are configured; by default all supported services are configured.
    default_auth_domain: The authentication domain to use by default.
    save_cookies: Forwarded to rpc_server_factory function.
    auth_tries: Number of attempts to make to authenticate.
    use_remote_datastore: Whether to use RemoteDatastoreStub instead of passing
      through datastore requests. RemoteDatastoreStub batches transactional
      datastore requests since, in production, datastore requires are scoped to
      a single request.

  Returns:
    server, the server created by rpc_server_factory, which may be useful for
      calling the application directly.

  Raises:
    urllib2.HTTPError: if app_id is not provided and there is an error while
      retrieving it.
    ConfigurationError: if there is a error configuring the DatstoreFileStub.
  """
  if not servername and not app_id:
    raise ConfigurationError('app_id or servername required')
  if not servername:
    servername = '%s.appspot.com' % (app_id,)
  server = rpc_server_factory(
      servername, auth_func, GetUserAgent(), GetSourceName(),
      save_cookies=save_cookies, auth_tries=auth_tries, debug_data=False,
      secure=secure)
  if not app_id:
    app_id = GetRemoteAppIdFromServer(server, path, rtok)

  ConfigureRemoteApiFromServer(server, path, app_id, services,
                               default_auth_domain, use_remote_datastore)
  return server


def MaybeInvokeAuthentication():
  """Sends an empty request through to the configured end-point.

  If authentication is necessary, this will cause the rpc_server to invoke
  interactive authentication.
  """
  datastore_stub = apiproxy_stub_map.apiproxy.GetStub('datastore_v3')
  if isinstance(datastore_stub, RemoteStub):
    datastore_stub._server.Send(datastore_stub._path, payload=None)
  else:
    raise ConfigurationError('remote_api is not configured.')



ConfigureRemoteDatastore = ConfigureRemoteApi
