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
"""Serves the stub App Engine APIs (e.g. memcache, datastore) over HTTP.

The Remote API protocol is used for communication.
"""



import logging
import os
import pickle
import shutil
import socket
import sys
import tempfile
import threading
import time
import traceback
import urllib2
import urlparse

import google
import yaml

# Stubs
from google.appengine.api import datastore_file_stub
from google.appengine.api import mail_stub
from google.appengine.api import urlfetch_stub
from google.appengine.api import user_service_stub
from google.appengine.api.app_identity import app_identity_stub
from google.appengine.api.blobstore import blobstore_stub
from google.appengine.api.blobstore import file_blob_storage
from google.appengine.api.capabilities import capability_stub
from google.appengine.api.channel import channel_service_stub
from google.appengine.api.files import file_service_stub
from google.appengine.api.logservice import logservice_stub
from google.appengine.api.search import simple_search_stub
from google.appengine.api.taskqueue import taskqueue_stub
from google.appengine.api.prospective_search import prospective_search_stub
from google.appengine.api.memcache import memcache_stub
from google.appengine.api.modules import modules_stub
from google.appengine.api.remote_socket import _remote_socket_stub
from google.appengine.api.system import system_stub
from google.appengine.api.xmpp import xmpp_service_stub
from google.appengine.datastore import datastore_sqlite_stub
from google.appengine.datastore import datastore_stub_util
from google.appengine.datastore import datastore_v4_pb
from google.appengine.datastore import datastore_v4_stub

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore
from google.appengine.ext.remote_api import remote_api_pb
from google.appengine.ext.remote_api import remote_api_services
from google.appengine.runtime import apiproxy_errors
from google.appengine.tools.devappserver2 import wsgi_server


# TODO: Remove this lock when stubs have been audited for thread
# safety.
GLOBAL_API_LOCK = threading.RLock()


# We don't want to support datastore_v4 everywhere, because users are supposed
# to use the Cloud Datastore API going forward, so we don't want to put these
# entries in remote_api_servers.SERVICE_PB_MAP. But for our own implementation
# of the Cloud Datastore API we need those methods to work when an instance
# issues them, specifically the DatstoreApiServlet running as a module inside
# the app we are running. The consequence is that other app code can also
# issue datastore_v4 API requests, but since we don't document these requests
# or export them through any language bindings this is unlikely in practice.
_DATASTORE_V4_METHODS = {
    'AllocateIds': (datastore_v4_pb.AllocateIdsRequest,
                    datastore_v4_pb.AllocateIdsResponse),
    'BeginTransaction': (datastore_v4_pb.BeginTransactionRequest,
                         datastore_v4_pb.BeginTransactionResponse),
    'Commit': (datastore_v4_pb.CommitRequest,
               datastore_v4_pb.CommitResponse),
    'ContinueQuery': (datastore_v4_pb.ContinueQueryRequest,
                      datastore_v4_pb.ContinueQueryResponse),
    'Lookup': (datastore_v4_pb.LookupRequest,
               datastore_v4_pb.LookupResponse),
    'Rollback': (datastore_v4_pb.RollbackRequest,
                 datastore_v4_pb.RollbackResponse),
    'RunQuery': (datastore_v4_pb.RunQueryRequest,
                 datastore_v4_pb.RunQueryResponse),
}

# TODO: Remove after the Files API is really gone.
_FILESAPI_USE_TRACKER = None
_FILESAPI_ENABLED = True


def enable_filesapi_tracking(request_data):
  """Turns on per-request tracking of Files API use.

  Args:
    request_data: An object with a set_filesapi_used(request_id) method to
        track Files API use.
  """
  global _FILESAPI_USE_TRACKER
  _FILESAPI_USE_TRACKER = request_data


def set_filesapi_enabled(enabled):
  """Enables or disables the Files API."""
  global _FILESAPI_ENABLED
  _FILESAPI_ENABLED = enabled


def _execute_request(request):
  """Executes an API method call and returns the response object.

  Args:
    request: A remote_api_pb.Request object representing the API call e.g. a
        call to memcache.Get.

  Returns:
    A ProtocolBuffer.ProtocolMessage representing the API response e.g. a
    memcache_service_pb.MemcacheGetResponse.

  Raises:
    apiproxy_errors.CallNotFoundError: if the requested method doesn't exist.
    apiproxy_errors.ApplicationError: if the API method calls fails.
  """
  service = request.service_name()
  method = request.method()
  if request.has_request_id():
    request_id = request.request_id()
  else:
    logging.error('Received a request without request_id: %s', request)
    request_id = None

  service_methods = (_DATASTORE_V4_METHODS if service == 'datastore_v4'
                     else remote_api_services.SERVICE_PB_MAP.get(service, {}))
  # We do this rather than making a new map that is a superset of
  # remote_api_services.SERVICE_PB_MAP because that map is not initialized
  # all in one place, so we would have to be careful about where we made
  # our new map.

  request_class, response_class = service_methods.get(method, (None, None))
  if not request_class:
    raise apiproxy_errors.CallNotFoundError('%s.%s does not exist' % (service,
                                                                      method))

  # TODO: Remove after the Files API is really gone.
  if not _FILESAPI_ENABLED and service == 'file':
    raise apiproxy_errors.CallNotFoundError(
        'Files API method %s.%s is disabled. Further information: '
        'https://cloud.google.com/appengine/docs/deprecations/files_api'
        % (service, method))

  request_data = request_class()
  request_data.ParseFromString(request.request())
  response_data = response_class()
  service_stub = apiproxy_stub_map.apiproxy.GetStub(service)

  def make_request():
    # TODO: Remove after the Files API is really gone.
    if (_FILESAPI_USE_TRACKER is not None
        and service == 'file' and request_id is not None):
      _FILESAPI_USE_TRACKER.set_filesapi_used(request_id)
    service_stub.MakeSyncCall(service,
                              method,
                              request_data,
                              response_data,
                              request_id)

  # If the service has not declared itself as threadsafe acquire
  # GLOBAL_API_LOCK.
  if service_stub.THREADSAFE:
    make_request()
  else:
    with GLOBAL_API_LOCK:
      make_request()
  return response_data


class APIServer(wsgi_server.WsgiServer):
  """Serves API calls over HTTP."""

  def __init__(self, host, port, app_id):
    self._app_id = app_id
    self._host = host
    super(APIServer, self).__init__((host, port), self)
    self.set_balanced_address('localhost:8080')

  def start(self):
    """Start the API Server."""
    super(APIServer, self).start()
    logging.info('Starting API server at: http://%s:%d', self._host, self.port)

  def quit(self):
    cleanup_stubs()
    super(APIServer, self).quit()

  def set_balanced_address(self, balanced_address):
    """Sets the balanced address from the dispatcher (e.g. "localhost:8080").

    This is used to enable APIs to build valid URLs.

    Args:
      balanced_address: string address of the balanced HTTP server.
    """
    self._balanced_address = balanced_address

  def _handle_POST(self, environ, start_response):
    start_response('200 OK', [('Content-Type', 'application/octet-stream')])

    start_time = time.time()
    response = remote_api_pb.Response()
    try:
      request = remote_api_pb.Request()
      # NOTE: Exceptions encountered when parsing the PB or handling the request
      # will be propagated back to the caller the same way as exceptions raised
      # by the actual API call.
      if environ.get('HTTP_TRANSFER_ENCODING') == 'chunked':
        # CherryPy concatenates all chunks  when 'wsgi.input' is read but v3.2.2
        # will not return even when all of the data in all chunks has been
        # read. See: https://bitbucket.org/cherrypy/cherrypy/issue/1131.
        wsgi_input = environ['wsgi.input'].read(2**32)
      else:
        wsgi_input = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))
      request.ParseFromString(wsgi_input)
      if request.has_request_id():
        request_id = request.request_id()
        service = request.service_name()
        service_stub = apiproxy_stub_map.apiproxy.GetStub(service)
        environ['HTTP_HOST'] = self._balanced_address
        op = getattr(service_stub.request_data, 'register_request_id', None)
        if callable(op):
          op(environ, request_id)
      api_response = _execute_request(request).Encode()
      response.set_response(api_response)
    except Exception, e:
      if isinstance(e, apiproxy_errors.ApplicationError):
        level = logging.DEBUG
        application_error = response.mutable_application_error()
        application_error.set_code(e.application_error)
        application_error.set_detail(e.error_detail)
      else:
        # If the runtime instance is not Python, it won't be able to unpickle
        # the exception so use level that won't be ignored by default.
        level = logging.ERROR
        # Even if the runtime is Python, the exception may be unpicklable if
        # it requires importing a class blocked by the sandbox so just send
        # back the exception representation.
        # But due to our use of the remote API, at least some apiproxy errors
        # are generated in the Dev App Server main instance and not in the
        # language runtime and wrapping them causes different behavior from
        # prod so don't wrap them.
        if not isinstance(e, apiproxy_errors.Error):
          e = RuntimeError(repr(e))
      # While not strictly necessary for ApplicationError, do this to limit
      # differences with remote_api:handler.py.
      response.set_exception(pickle.dumps(e))
      logging.log(level, 'Exception while handling %s\n%s', request,
                  traceback.format_exc())
    encoded_response = response.Encode()
    logging.debug('Handled %s.%s in %0.4f',
                  request.service_name(),
                  request.method(),
                  time.time() - start_time)
    return [encoded_response]

  def _handle_GET(self, environ, start_response):
    params = urlparse.parse_qs(environ['QUERY_STRING'])
    rtok = params.get('rtok', ['0'])[0]

    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [yaml.dump({'app_id': self._app_id,
                       'rtok': rtok})]

  def __call__(self, environ, start_response):
    if environ['REQUEST_METHOD'] == 'GET':
      return self._handle_GET(environ, start_response)
    elif environ['REQUEST_METHOD'] == 'POST':
      return self._handle_POST(environ, start_response)
    else:
      start_response('405 Method Not Allowed', [])
      return []


def setup_stubs(
    request_data,
    app_id,
    application_root,
    trusted,
    appidentity_email_address,
    appidentity_private_key_path,
    blobstore_path,
    datastore_consistency,
    datastore_path,
    datastore_require_indexes,
    datastore_auto_id_policy,
    images_host_prefix,
    logs_path,
    mail_smtp_host,
    mail_smtp_port,
    mail_smtp_user,
    mail_smtp_password,
    mail_enable_sendmail,
    mail_show_mail_body,
    mail_allow_tls,
    matcher_prospective_search_path,
    search_index_path,
    taskqueue_auto_run_tasks,
    taskqueue_default_http_server,
    user_login_url,
    user_logout_url,
    default_gcs_bucket_name,
    appidentity_oauth_url=None):
  """Configures the APIs hosted by this server.

  Args:
    request_data: An apiproxy_stub.RequestInformation instance used by the
        stubs to lookup information about the request associated with an API
        call.
    app_id: The str application id e.g. "guestbook".
    application_root: The path to the directory containing the user's
        application e.g. "/home/joe/myapp".
    trusted: A bool indicating if privileged APIs should be made available.
    appidentity_email_address: Email address associated with a service account
        that has a downloadable key. May be None for no local application
        identity.
    appidentity_private_key_path: Path to private key file associated with
        service account (.pem format). Must be set if appidentity_email_address
        is set.
    blobstore_path: The path to the file that should be used for blobstore
        storage.
    datastore_consistency: The datastore_stub_util.BaseConsistencyPolicy to
        use as the datastore consistency policy.
    datastore_path: The path to the file that should be used for datastore
        storage.
    datastore_require_indexes: A bool indicating if the same production
        datastore indexes requirements should be enforced i.e. if True then
        a google.appengine.ext.db.NeedIndexError will be be raised if a query
        is executed without the required indexes.
    datastore_auto_id_policy: The type of sequence from which the datastore
        stub assigns auto IDs, either datastore_stub_util.SEQUENTIAL or
        datastore_stub_util.SCATTERED.
    images_host_prefix: The URL prefix (protocol://host:port) to prepend to
        image urls on calls to images.GetUrlBase.
    logs_path: Path to the file to store the logs data in.
    mail_smtp_host: The SMTP hostname that should be used when sending e-mails.
        If None then the mail_enable_sendmail argument is considered.
    mail_smtp_port: The SMTP port number that should be used when sending
        e-mails. If this value is None then mail_smtp_host must also be None.
    mail_smtp_user: The username to use when authenticating with the
        SMTP server. This value may be None if mail_smtp_host is also None or if
        the SMTP server does not require authentication.
    mail_smtp_password: The password to use when authenticating with the
        SMTP server. This value may be None if mail_smtp_host or mail_smtp_user
        is also None.
    mail_enable_sendmail: A bool indicating if sendmail should be used when
        sending e-mails. This argument is ignored if mail_smtp_host is not None.
    mail_show_mail_body: A bool indicating whether the body of sent e-mails
        should be written to the logs.
    mail_allow_tls: A bool indicating whether TLS should be allowed when
        communicating with an SMTP server. This argument is ignored if
        mail_smtp_host is None.
    matcher_prospective_search_path: The path to the file that should be used to
        save prospective search subscriptions.
    search_index_path: The path to the file that should be used for search index
        storage.
    taskqueue_auto_run_tasks: A bool indicating whether taskqueue tasks should
        be run automatically or it the must be manually triggered.
    taskqueue_default_http_server: A str containing the address of the http
        server that should be used to execute tasks.
    user_login_url: A str containing the url that should be used for user login.
    user_logout_url: A str containing the url that should be used for user
        logout.
    default_gcs_bucket_name: A str, overriding the default bucket behavior.
    appidentity_oauth_url: A str containing the url to the oauth2 server to use
        to authenticate the private key. If set to None, then the standard
        google oauth2 server is used.
  """




  identity_stub = app_identity_stub.AppIdentityServiceStub.Create(
      email_address=appidentity_email_address,
      private_key_path=appidentity_private_key_path,
      oauth_url=appidentity_oauth_url)
  if default_gcs_bucket_name is not None:
    identity_stub.SetDefaultGcsBucketName(default_gcs_bucket_name)
  apiproxy_stub_map.apiproxy.RegisterStub('app_identity_service', identity_stub)

  blob_storage = file_blob_storage.FileBlobStorage(blobstore_path, app_id)
  apiproxy_stub_map.apiproxy.RegisterStub(
      'blobstore',
      blobstore_stub.BlobstoreServiceStub(blob_storage,
                                          request_data=request_data))

  apiproxy_stub_map.apiproxy.RegisterStub(
      'capability_service',
      capability_stub.CapabilityServiceStub())

  apiproxy_stub_map.apiproxy.RegisterStub(
      'channel',
      channel_service_stub.ChannelServiceStub(request_data=request_data))

  datastore_stub = datastore_sqlite_stub.DatastoreSqliteStub(
      app_id,
      datastore_path,
      datastore_require_indexes,
      trusted,
      root_path=application_root,
      auto_id_policy=datastore_auto_id_policy)

  datastore_stub.SetConsistencyPolicy(datastore_consistency)

  apiproxy_stub_map.apiproxy.ReplaceStub(
      'datastore_v3', datastore_stub)

  apiproxy_stub_map.apiproxy.RegisterStub(
      'datastore_v4',
      datastore_v4_stub.DatastoreV4Stub(app_id))

  apiproxy_stub_map.apiproxy.RegisterStub(
      'file',
      file_service_stub.FileServiceStub(blob_storage))

  try:
    from google.appengine.api.images import images_stub
  except ImportError:




    # We register a stub which throws a NotImplementedError for most RPCs.
    from google.appengine.api.images import images_not_implemented_stub
    apiproxy_stub_map.apiproxy.RegisterStub(
        'images',
        images_not_implemented_stub.ImagesNotImplementedServiceStub(
            host_prefix=images_host_prefix))
  else:
    apiproxy_stub_map.apiproxy.RegisterStub(
        'images',
        images_stub.ImagesServiceStub(host_prefix=images_host_prefix))

  apiproxy_stub_map.apiproxy.RegisterStub(
      'logservice',
      logservice_stub.LogServiceStub(logs_path=logs_path))

  apiproxy_stub_map.apiproxy.RegisterStub(
      'mail',
      mail_stub.MailServiceStub(mail_smtp_host,
                                mail_smtp_port,
                                mail_smtp_user,
                                mail_smtp_password,
                                enable_sendmail=mail_enable_sendmail,
                                show_mail_body=mail_show_mail_body,
                                allow_tls=mail_allow_tls))

  apiproxy_stub_map.apiproxy.RegisterStub(
      'memcache',
      memcache_stub.MemcacheServiceStub())

  apiproxy_stub_map.apiproxy.RegisterStub(
      'search',
      simple_search_stub.SearchServiceStub(index_file=search_index_path))

  apiproxy_stub_map.apiproxy.RegisterStub(
      'modules',
      modules_stub.ModulesServiceStub(request_data))

  apiproxy_stub_map.apiproxy.RegisterStub(
      'system',
      system_stub.SystemServiceStub(request_data=request_data))

  apiproxy_stub_map.apiproxy.RegisterStub(
      'taskqueue',
      taskqueue_stub.TaskQueueServiceStub(
          root_path=application_root,
          auto_task_running=taskqueue_auto_run_tasks,
          default_http_server=taskqueue_default_http_server,
          request_data=request_data))
  apiproxy_stub_map.apiproxy.GetStub('taskqueue').StartBackgroundExecution()

  apiproxy_stub_map.apiproxy.RegisterStub(
      'urlfetch',
      urlfetch_stub.URLFetchServiceStub())

  apiproxy_stub_map.apiproxy.RegisterStub(
      'user',
      user_service_stub.UserServiceStub(login_url=user_login_url,
                                        logout_url=user_logout_url,
                                        request_data=request_data))

  apiproxy_stub_map.apiproxy.RegisterStub(
      'xmpp',
      xmpp_service_stub.XmppServiceStub())

  apiproxy_stub_map.apiproxy.RegisterStub(
      'matcher',
      prospective_search_stub.ProspectiveSearchStub(
          matcher_prospective_search_path,
          apiproxy_stub_map.apiproxy.GetStub('taskqueue')))

  apiproxy_stub_map.apiproxy.RegisterStub(
      'remote_socket',
      _remote_socket_stub.RemoteSocketServiceStub())


def maybe_convert_datastore_file_stub_data_to_sqlite(app_id, filename):
  if not os.access(filename, os.R_OK | os.W_OK):
    return
  try:
    with open(filename, 'rb') as f:
      if f.read(16) == 'SQLite format 3\x00':
        return
  except (IOError, OSError):
    return
  try:
    _convert_datastore_file_stub_data_to_sqlite(app_id, filename)
  except:
    logging.exception('Failed to convert datastore file stub data to sqlite.')
    raise


def _convert_datastore_file_stub_data_to_sqlite(app_id, datastore_path):
  logging.info('Converting datastore stub data to sqlite.')
  previous_stub = apiproxy_stub_map.apiproxy.GetStub('datastore_v3')
  try:
    apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
    datastore_stub = datastore_file_stub.DatastoreFileStub(
        app_id, datastore_path, trusted=True, save_changes=False)
    apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', datastore_stub)

    entities = _fetch_all_datastore_entities()
    sqlite_datastore_stub = datastore_sqlite_stub.DatastoreSqliteStub(
        app_id, datastore_path + '.sqlite', trusted=True)
    apiproxy_stub_map.apiproxy.ReplaceStub('datastore_v3',
                                           sqlite_datastore_stub)
    datastore.Put(entities)
    sqlite_datastore_stub.Close()
  finally:
    apiproxy_stub_map.apiproxy.ReplaceStub('datastore_v3', previous_stub)

  shutil.copy(datastore_path, datastore_path + '.filestub')
  os.remove(datastore_path)
  shutil.move(datastore_path + '.sqlite', datastore_path)
  logging.info('Datastore conversion complete. File stub data has been backed '
               'up in %s', datastore_path + '.filestub')


def _fetch_all_datastore_entities():
  """Returns all datastore entities from all namespaces as a list."""
  all_entities = []
  for namespace in datastore.Query('__namespace__').Run():
    namespace_name = namespace.key().name()
    for kind in datastore.Query('__kind__', namespace=namespace_name).Run():
      all_entities.extend(
          datastore.Query(kind.key().name(), namespace=namespace_name).Run())
  return all_entities


def test_setup_stubs(
    request_data=None,
    app_id='myapp',
    application_root='/tmp/root',
    trusted=False,
    appidentity_email_address=None,
    appidentity_private_key_path=None,
    # TODO: is this correct? If I'm following the flow correctly, this
    # should not be a file but a directory.
    blobstore_path='/dev/null',
    datastore_consistency=None,
    datastore_path=':memory:',
    datastore_require_indexes=False,
    datastore_auto_id_policy=datastore_stub_util.SCATTERED,
    images_host_prefix='http://localhost:8080',
    logs_path=':memory:',
    mail_smtp_host='',
    mail_smtp_port=25,
    mail_smtp_user='',
    mail_smtp_password='',
    mail_enable_sendmail=False,
    mail_show_mail_body=False,
    mail_allow_tls=True,
    matcher_prospective_search_path=os.devnull,
    search_index_path=None,
    taskqueue_auto_run_tasks=False,
    taskqueue_default_http_server='http://localhost:8080',
    user_login_url='/_ah/login?continue=%s',
    user_logout_url='/_ah/login?continue=%s',
    default_gcs_bucket_name=None,
    appidentity_oauth_url=None):
  """Similar to setup_stubs with reasonable test defaults and recallable."""

  # Reset the stub map between requests because a stub map only allows a
  # stub to be added once.
  apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()

  if datastore_consistency is None:
    datastore_consistency = (
        datastore_stub_util.PseudoRandomHRConsistencyPolicy())

  setup_stubs(request_data,
              app_id,
              application_root,
              trusted,
              appidentity_email_address,
              appidentity_private_key_path,
              blobstore_path,
              datastore_consistency,
              datastore_path,
              datastore_require_indexes,
              datastore_auto_id_policy,
              images_host_prefix,
              logs_path,
              mail_smtp_host,
              mail_smtp_port,
              mail_smtp_user,
              mail_smtp_password,
              mail_enable_sendmail,
              mail_show_mail_body,
              mail_allow_tls,
              matcher_prospective_search_path,
              search_index_path,
              taskqueue_auto_run_tasks,
              taskqueue_default_http_server,
              user_login_url,
              user_logout_url,
              default_gcs_bucket_name,
              appidentity_oauth_url)


def cleanup_stubs():
  """Do any necessary stub cleanup e.g. saving data."""
  # Saving datastore
  logging.info('Applying all pending transactions and saving the datastore')
  datastore_stub = apiproxy_stub_map.apiproxy.GetStub('datastore_v3')
  datastore_stub.Write()
  logging.info('Saving search indexes')
  apiproxy_stub_map.apiproxy.GetStub('search').Write()
  apiproxy_stub_map.apiproxy.GetStub('taskqueue').Shutdown()
