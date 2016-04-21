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


"""This module adds support for multiple processes in the dev_appserver.

Each instance of the application is started as a separate process on a unique
port, for state isolation and parallel execution.  A load-balancing process is
also created for each Backend.  An API Server process is launched to handle all
memcache and datastore API requests, so that persistent state is shared across
all processes.  Application and Backend instances forward their memcache and
datastore requests to the API Server using the remote_api interface.

The base process is considered the Master.  It manages all subprocesses, assigns
them ports, and issues /_ah/start requests to Backend instances.  Ports are
either fixed (using the base value of --multiprocess_min_port) or randomly
chosen.  The Master listens on the --port specified by the user, and forwards
all requests to an App Instance process.

Each balancer forwards incoming requests to the next free instance,
or return with a HTTP 503 error if no free instance is available.
"""


import BaseHTTPServer
import copy
import cStringIO
import errno
import httplib
import logging
import os
import Queue
import signal
import socket
import subprocess
import sys
import threading
import time

from google.appengine.api import backendinfo
from google.appengine.api.backends import backends as backends_api
from google.appengine.ext.remote_api import remote_api_stub

ARG_ADDRESS = 'address'
ARG_PORT = 'port'

ARG_BACKENDS = 'backends'
ARG_MULTIPROCESS = 'multiprocess'
ARG_MULTIPROCESS_MIN_PORT = 'multiprocess_min_port'
ARG_MULTIPROCESS_API_PORT = 'multiprocess_api_port'
ARG_MULTIPROCESS_API_SERVER = 'multiprocess_api_server'
ARG_MULTIPROCESS_APP_INSTANCE_ID = 'multiprocess_app_instance'
ARG_MULTIPROCESS_BACKEND_ID = 'multiprocess_backend_id'
ARG_MULTIPROCESS_BACKEND_INSTANCE_ID = 'multiprocess_backend_instance_id'



API_SERVER_HOST = 'localhost'
PATH_DEV_API_SERVER = '/_ah/dev_api_server'

BACKEND_MAX_INSTANCES = 20


class Error(Exception): pass


def SetThreadName(thread, name):
  """Sets the name a of thread, including the GlobalProcess name."""
  thread.setName('[%s: %s]' % (GlobalProcess().Type(), name))


class StartInstance(threading.Thread):
  """Thread that periodically attempts to start a backend instance."""

  def __init__(self, child):
    threading.Thread.__init__(self)
    self.child = child
    self.setDaemon(True)
    SetThreadName(self, 'Start %s' % child)

  def run(self):
    while True:
      self.child.SendStartRequest()
      time.sleep(1)


class ChildProcess(object):
  def __init__(self,
               host,
               port,
               api_server=False,
               app_instance=None,
               backend_id=None,
               instance_id=None):
    """Creates an object representing a child process.

    Only one of the given args should be provided (except for instance_id when
    backend_id is specified).

    Args:
      api_server: (bool) The process represents the multiprocess API Server.
      app_instance: (int) The process represents the indicated app instance.
      backend_id: (string) The process represents a backend.
      instance_id: (int) The process represents the given backend instance.
    """

    self.api_server = api_server
    self.app_instance = app_instance
    self.backend_id = backend_id
    self.instance_id = instance_id
    self.process = None
    self.argv = []
    self.started = False
    self.connection_handler = httplib.HTTPConnection
    self.SetHostPort(host, port)

  def __str__(self):
    if self.api_server:
      string = 'Remote API Server'
    elif self.app_instance is not None:
      string = 'App Instance'
    elif self.instance_id is not None:
      string = 'Backend Instance: %s.%d' % (self.backend_id, self.instance_id)
    elif self.backend_id:
      string = 'Backend Balancer: %s' % self.backend_id
    else:
      string = 'Unknown'
    return '%s [%s]' % (string, self.Address())

  def SetHostPort(self, host, port):
    """Sets the host and port that this process listens on."""
    self.host = host
    self.port = port
    if self.backend_id:
      backends_api._set_dev_port(self.port,
                                 self.backend_id,
                                 self.instance_id)

  def Address(self):
    """Returns the URL for this process."""
    return 'http://%s:%d' % self.HostPort()

  def HostPort(self):
    """Returns the address of this process as a (host, port) pair."""
    return (self.host, self.port)

  def Start(self, argv, api_port):
    """Starts the child process.

    Args:
      argv: The argv of the parent process. When starting the subprocess,
        we make a copy of the parent's argv, then modify it in accordance with
        how the ChildProcess is configured, to represent different processes in
        the multiprocess dev_appserver.
      api_port: The port on which the API Server listens.
    """
    self.argv = copy.deepcopy(argv)
    self.api_port = api_port

    self.SetFlag('--multiprocess')
    self.SetFlag('--address', short_flag='-a', value=self.host)
    self.SetFlag('--port', short_flag='-p', value=self.port)
    self.SetFlag('--multiprocess_api_port', value=self.api_port)

    if self.api_server:
      self.SetFlag('--multiprocess_api_server')
    if self.app_instance is not None:
      self.SetFlag('--multiprocess_app_instance_id', value=0)
    if self.backend_id is not None:
      self.SetFlag('--multiprocess_backend_id', value=self.backend_id)
    if self.instance_id is not None:
      self.SetFlag('--multiprocess_backend_instance_id', value=self.instance_id)
    if self.argv[0].endswith('.py'):



      self.argv.insert(0, sys.executable)

    logging.debug('Starting %s with args: %s', self, self.argv)
    self.process = subprocess.Popen(self.argv)

  def EnableStartRequests(self):
    """Starts a thread to periodically send /_ah/start to this instance.

    We need a thread to do this because we want to restart any resident Backends
    that have been shutdown, and because a backend instance is not considered
    to be ready for serving until it has successfully responded to /_ah/start.
    """
    if self.backend_id and self.instance_id is not None:
      self.start_thread = StartInstance(self)
      self.start_thread.start()

  def Connect(self):
    """Attempts to connect to the child process.

    Returns:
      bool: Whether a connection was made.
    """
    logging.debug('Attempting connection to %s', self)
    sock = None
    result = True
    try:
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.connect(self.HostPort())
    except:
      result = False
    if sock:
      sock.close()
    return result

  def WaitForConnection(self, timeout_s=30.0, poll_period_s=0.5):
    """Blocks until the child process has started.

    This method repeatedly attempts to connect to the process on its HTTP server
    port.  Returns when a connection has been successfully established or the
    timeout has been reached.

    Args:
      timeout_s: Amount of time to wait, in seconds.
      poll_period_s: Time to wait between connection attempts.
    """
    finish_time = time.time() + timeout_s
    while time.time() < finish_time:
      if self.Connect():
        return True
      time.sleep(poll_period_s)
    logging.info('%s took more than %d seconds to start.', self, timeout_s)
    return False

  def SendStartRequest(self):
    """If the process has not been started, sends a request to /_ah/start."""
    if self.started:
      return

    try:
      response = self.SendRequest('GET', '/_ah/start')
      rc = response.status
      if (rc >= 200 and rc < 300) or rc == 404:
        self.started = True
    except KeyboardInterrupt:
      pass
    except Exception, e:
      logging.error('Failed start request to %s: %s', self, e)

  def SendRequest(self, command, path, payload=None, headers=None):
    """Sends an HTTP request to this process.

    Args:
      command: The HTTP command (e.g., GET, POST)
      path: The URL path for the request.
      headers: A dictionary containing headers as key-value pairs.
    """
    logging.debug('send request: %s %s to %s' % (command, path, self))
    connection = self.connection_handler('%s:%d' % self.HostPort())
    connection.request(command, path, payload, headers or {})
    response = connection.getresponse()
    return response

  def SetFlag(self, flag, short_flag=None, value=None):
    """Add a flag to self.argv, replacing the existing value if set.

    Args:
      flag: flag to remove.
      short_flag: one letter short version of the flag (optional)
      value: Value of the flag (optional)
    """
    self.RemoveFlag(flag, short_flag=short_flag, has_value=(value is not None))
    if value is None:
      self.argv.append(flag)
    else:
      self.argv.append(flag + '=' + str(value))

  def RemoveFlag(self, flag, short_flag=None, has_value=False):
    """Removes an argument from self.argv.

    Args:
      flag: flag to remove.
      short_flag: one letter short version of the flag
      has_value: True if the next argument after the short flag is the value.
    """
    new_argv = []
    index = 0
    while index < len(self.argv):
      value = self.argv[index]
      index += 1


      if flag == value:

        if has_value:
          index += 1
        continue


      if has_value and value.startswith(flag + '='):
        continue


      if short_flag == value:

        if has_value:
          index += 1
        continue
      new_argv.append(value)


    self.argv = new_argv


class DevProcess(object):
  """Represents a process in the multiprocess dev_appserver."""

  TYPE_MASTER = 'Master'
  TYPE_API_SERVER = 'Remote API Server'
  TYPE_APP_INSTANCE = 'App Instance'
  TYPE_BACKEND_BALANCER = 'Backend Balancer'
  TYPE_BACKEND_INSTANCE = 'Backend Instance'
  TYPES = frozenset([TYPE_MASTER,
                     TYPE_API_SERVER,
                     TYPE_APP_INSTANCE,
                     TYPE_BACKEND_BALANCER,
                     TYPE_BACKEND_INSTANCE])

  def __init__(self):
    """Creates a DevProcess with a default configuration."""
    self.process_type = None


    self.desc = None


    self.http_server = None


    self.app_id = None


    self.backends = None



    self.app_instance = None


    self.backend_id = None


    self.instance_id = None


    self.backend_entry = None


    self.host = None


    self.port = None


    self.api_port = None


    self.multiprocess_min_port = 9000


    self.children = []


    self.child_app_instance = None


    self.child_api_server = None


    self.balance_set = None



    self.started = False

  def Init(self, appinfo, backends, options):
    """Supplies a list of backends for future use.

    Args:
      appinfo: An AppInfoExternal object.
      backends: List of BackendEntry objects.
      options: Dictionary of command-line options.
    """
    self.backends = backends
    self.options = options

    if not self.backends:
      raise Error('Entering multiprocess mode with no backends configured.')

    self.app_id = appinfo.application
    self.host = options[ARG_ADDRESS]
    self.port = options[ARG_PORT]


    if ARG_MULTIPROCESS_API_SERVER in options:
      self.SetType(DevProcess.TYPE_API_SERVER)
    if ARG_MULTIPROCESS_APP_INSTANCE_ID in options:
      self.SetType(DevProcess.TYPE_APP_INSTANCE)
      self.app_instance = options[ARG_MULTIPROCESS_APP_INSTANCE_ID]
      self.desc = str(self.app_instance)
    if ARG_MULTIPROCESS_BACKEND_ID in options:
      self.backend_id = options[ARG_MULTIPROCESS_BACKEND_ID]
      self.desc = self.backend_id
      if ARG_MULTIPROCESS_BACKEND_INSTANCE_ID in options:
        self.SetType(DevProcess.TYPE_BACKEND_INSTANCE)
        self.instance_id = int(options[ARG_MULTIPROCESS_BACKEND_INSTANCE_ID])
        self.desc += '.%d' % self.instance_id
      else:
        self.SetType(DevProcess.TYPE_BACKEND_BALANCER)

    if ARG_MULTIPROCESS_API_PORT in options:
      self.api_port = int(options[ARG_MULTIPROCESS_API_PORT])
    if ARG_MULTIPROCESS_MIN_PORT in options:
      self.multiprocess_min_port = int(options[ARG_MULTIPROCESS_MIN_PORT])

    if self.IsApiServer():
      assert self.port == self.api_port

    if self.IsBackend():
      self.InitBackendEntry()


    if not self.Type():
      self.SetType(DevProcess.TYPE_MASTER)

  def InitBackendEntry(self):
    """Finds the entry for the backend this process represents, if any."""
    for backend in self.backends:
      if backend.name == self.backend_id:
        self.backend_entry = backend

    if not self.backend_entry:
      raise Error('No backend entry found for: ' % self)

  def HttpServer(self):
    """Returns the HTTPServer used by this process."""
    return self.http_server

  def Address(self):
    """Returns the address of this process."""
    return 'http://%s:%d' % (self.host, self.port)

  def SetHttpServer(self, http_server):
    """Sets the http_server to be used when handling requests.

    Args:
      http_server: An HTTPServer that receives requests.
    """
    self.http_server = http_server
    self.handle_requests = HandleRequestThread()
    self.handle_requests.start()

  def StartChildren(self, argv):
    """Starts the set of child processes."""
    self.children = []


    base_port = self.multiprocess_min_port
    next_port = base_port
    self.child_app_instance = ChildProcess(self.host, next_port,
                                           app_instance=0)
    self.children.append(self.child_app_instance)
    next_port += 1


    for backend in self.backends:
      base_port += 100
      next_port = base_port


      for i in xrange(backend.instances):
        self.children.append(ChildProcess(self.host, next_port,
                                          backend_id=backend.name,
                                          instance_id=i))
        next_port += 1


      self.children.append(ChildProcess(self.host, base_port + 99,
                                        backend_id=backend.name))



    base_port += 100
    next_port = base_port


    self.child_api_server = ChildProcess(self.host, next_port, api_server=True)
    self.children.append(self.child_api_server)


    if self.multiprocess_min_port == 0:
      self.AssignPortsRandomly()


    self.child_api_server.host = API_SERVER_HOST


    self.api_port = self.child_api_server.port



    for child in self.children:
      child.Start(argv, self.api_port)


    for child in self.children:

      child.WaitForConnection()


    message = '\n\nMultiprocess Setup Complete:'
    for child in self.children:
      message += '\n  %s' % child
    message += '\n'
    logging.info(message)


    for child in self.children:
      child.EnableStartRequests()

  def AssignPortsRandomly(self):
    """Acquires a random port for each child process."""
    bound = []
    for child in self.children:
      sock = socket.socket()
      sock.bind(('localhost', 0))
      bound.append(sock)
      child.SetHostPort(self.host, sock.getsockname()[1])
    for sock in bound:
      sock.close()

  def __str__(self):
    result = '[%s]' % self.Type()
    if self.desc:
      result += ' [%s]' % self.desc
    return result

  def SetType(self, process_type):
    if process_type not in DevProcess.TYPES:
      raise Error('Unknown process type: %s' % process_type)
    if self.process_type is not None:
      raise Error('Process type cannot be set more than once.')
    self.process_type = process_type

  def Type(self):
    return self.process_type

  def IsDefault(self):
    """Indicates whether this is the default dev_appserver process."""
    return self.Type() is None

  def IsMaster(self):
    """Indicates whether this is the master process."""
    return self.Type() == DevProcess.TYPE_MASTER

  def IsSubprocess(self):
    """Indicates that this is a subprocessess of the dev_appserver."""
    return not (self.IsDefault() or self.IsMaster())

  def IsApiServer(self):
    """Indicates whether this is the api server process."""
    return self.Type() == DevProcess.TYPE_API_SERVER

  def IsAppInstance(self):
    """Indicates whether this process represents an application instance."""
    return self.Type() == DevProcess.TYPE_APP_INSTANCE

  def IsBackend(self):
    """Indicates whether this process represents a backend."""
    return self.IsBackendBalancer() or self.IsBackendInstance()

  def IsBackendBalancer(self):
    """Indicates whether this process represents a backend load balancer."""
    return self.Type() == DevProcess.TYPE_BACKEND_BALANCER

  def IsBackendInstance(self):
    """Indicates whether this process represents a backend instance."""
    return self.Type() == DevProcess.TYPE_BACKEND_INSTANCE

  def IsBalancer(self):
    """Indicates whether this process represents a load balancer."""
    return self.IsMaster() or self.IsBackendBalancer()

  def IsInstance(self):
    """Indicates whether this process represents an instance."""
    return self.IsAppInstance() or self.IsBackendInstance()

  def InitBalanceSet(self):
    """Construct a list of instances to balance traffic over."""
    if self.IsMaster():
      self.balance_set = [ self.child_app_instance.port ]

    if self.IsBackendBalancer():
      self.balance_set = []
      for instance in xrange(self.backend_entry.instances):
        port = backends_api._get_dev_port(self.backend_id, instance)
        self.balance_set.append(port)

  def GetBalanceSet(self):
    """Return the set of ports over which this process balances requests."""
    return self.balance_set

  def FailFast(self):
    """Indicates whether this process has fail-fast behavior."""
    if not self.backend_entry:
      return False
    if self.backend_entry.failfast:
      return True

    return False

  def PrintStartMessage(self, app_id, host, port):
    """Print the start message for processes that are started automatically."""
    url = 'http://%s:%d' % (host, port)
    if not self.IsSubprocess():

      logging.info('Running application %s on port %d: %s',
                   app_id, port, url)

  def Children(self):
    """Returns the children of this process."""
    return self.children

  def MaybeConfigureRemoteDataApis(self):
    """Set up stubs using remote_api as appropriate.

    If this is the API server (or is not multiprocess), return False.
    Otherwise, set up the stubs for data based APIs as remote stubs pointing at
    the to the API server and return True.
    """
    if self.IsDefault() or self.IsApiServer():
      return False

    services = ['datastore_v3', 'memcache', 'taskqueue']
    remote_api_stub.ConfigureRemoteApi(
        self.app_id, PATH_DEV_API_SERVER, lambda: ('', ''),
        servername='%s:%d' % (API_SERVER_HOST, self.api_port),
        services=services)
    return True

  def NewAppInfo(self, appinfo):
    """Called when a new appinfo is read from disk on each request.

    The only action we take is to apply backend settings, such as the 'start'
    directive, which adds a handler for /_ah/start.

    Args:
      appinfo: An AppInfoExternal to be used on the next request.
    """
    if self.backends:
      appinfo.backends = self.backends
      if self.IsBackend():
        appinfo.ApplyBackendSettings(self.backend_id)

  def UpdateEnv(self, env_dict):
    """Copies backend port information to the supplied environment dictionary.

    This information is used by the Backends API to resolve backend and instance
    addresses in the dev_appserver.

    User-supplied code has no access to the default environment. This method
    will copy the environment variables needed for the backends api from the
    default environment to the environment where user supplied code runs.

    Args:
      env_dict: Dictionary with the new environment.
    """
    if self.backend_id:
      env_dict['BACKEND_ID'] = self.backend_id
    if self.instance_id is not None:
      env_dict['INSTANCE_ID'] = str(self.instance_id)

    for key in os.environ:
      if key.startswith('BACKEND_PORT'):
        env_dict[key] = os.environ[key]

  def ProcessRequest(self, request, client_address):
    """Handles the SocketServer process_request call.

    If the request is to a backend the request will be handled by a separate
    thread. If the backend is busy a 503 response will be sent.

    If this is a balancer instance each incoming request will be forwarded to
    its own thread and handled there.

    If no backends are configured this override has no effect.

    Args:
      http_server: The http server handling the request
      request: the request to process
      client_address: the client address
    """
    assert not self.IsDefault()

    if self.IsBalancer():

      ForwardRequestThread(request, client_address).start()
      return
    elif self.IsApiServer():

      HandleRequestDirectly(request, client_address)
      return

    assert self.IsAppInstance() or self.IsBackendInstance()

    if self.handle_requests.Active():
      if self.FailFast():
        logging.info('respond busy')
        RespondBusyHandler(request, client_address)
        return

    self.handle_requests.Enqueue(request, client_address)

  def HandleRequest(self, request):
    """Hook that allows the DevProcess a chance to respond to requests.

    This hook is invoked just before normal request dispatch occurs in
    dev_appserver.py.

    Args:
      request: The request to be handled.

    Returns:
      bool: Indicates whether the request was handled here.  If False, normal
        request handling should proceed.
    """
    if self.IsBackendInstance() and not self.started:
      if request.path != '/_ah/start':
        request.send_response(httplib.FORBIDDEN,
                              'Waiting for start request to finish.')
        return True


    return False

  def RequestComplete(self, request, response):
    """Invoked when the process has finished handling a request."""
    rc = response.status_code

    if request.path == '/_ah/start':
      if (rc >= 200 and rc < 300) or rc == 404:
        self.started = True

  def UpdateSystemStub(self, system_service_stub):
    """Copies info about the backends into the system stub."""
    if self.IsDefault():
      return
    system_service_stub.set_backend_info(self.backends)


class HandleRequestThread(threading.Thread):
  """Thread for handling HTTP requests.

  Instances needs to be able to respond with 503 when busy with other requests,
  therefore requests are accepted in the main thread and forwarded to the
  serving thread for processing. If the serving thread is busy with other
  requests and the max pending queue length is reached a 503 error is sent back.

  Args:
    http_server: Http server class handling the request.
    max_pending_requests: The maximum number of pending requests in the queue.
  """

  def __init__(self):
    threading.Thread.__init__(self)
    self.setDaemon(True)
    SetThreadName(self, 'HandleRequestThread')


    self.active = False


    self.pending = Queue.Queue()

  def Active(self):
    """Indicates whether this thread is busy handling a request."""
    return self.active

  def Enqueue(self, request, client_address):
    """Adds the indicated request to the pending request queue."""
    self.pending.put_nowait((request, client_address))

  def run(self):
    """Takes requests from the queue and handles them."""
    while True:
      request, client_address = self.pending.get()
      self.active = True


      try:
        HandleRequestDirectly(request, client_address)
      except Exception, e:
        logging.info('Exception in HandleRequestThread', exc_info=1)
      finally:
        self.active = False


class RespondBusyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  """Handler that always will send back a 503 error."""

  def __init__(self, request, client_address):
    BaseHTTPServer.BaseHTTPRequestHandler.__init__(
        self, request, client_address, HttpServer())

  def handle_one_request(self):
    """Override."""
    self.raw_requestline = self.rfile.readline()
    if not self.raw_requestline:
      self.close_connection = 1
      return
    if not self.parse_request():
      return
    self.send_error(httplib.SERVICE_UNAVAILABLE, 'Busy.')


class ForwardRequestThread(threading.Thread):
  """Forwards an incoming request in a separate thread."""

  def __init__(self, request, client_address):
    threading.Thread.__init__(self)
    self.request = request
    self.client_address = client_address
    self.setDaemon(True)
    SetThreadName(self, 'ForwardRequestThread')

  def run(self):
    ForwardRequestHandler(self.request, self.client_address)


class ForwardRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  """Forwards the incoming request to next free backend instance."""

  def __init__(self,
               request,
               client_address,
               connection_handler=httplib.HTTPConnection):
    """Constructor extending BaseHTTPRequestHandler.

    Args:
      request: The incoming request.
      client_address: A (ip, port) tuple with the address of the client.
      backend: The HTTPServer that received the request.
      connection_handler: http library to use when balancer the connection to
        the next available backend instance. Used for dependency injection.
    """
    self.connection_handler = connection_handler
    BaseHTTPServer.BaseHTTPRequestHandler.__init__(self,
                                                   request,
                                                   client_address,
                                                   HttpServer())

  def handle_one_request(self):
    """Override. Invoked from BaseHTTPRequestHandler constructor."""
    self.raw_requestline = self.rfile.readline()
    if not self.raw_requestline:
      self.close_connection = 1
      return
    if not self.parse_request():
      return

    process = GlobalProcess()
    balance_set = process.GetBalanceSet()
    request_size = int(self.headers.get('content-length', 0))
    payload = self.rfile.read(request_size)




    for port in balance_set:
      logging.debug('balancer to port %d',  port)
      connection = self.connection_handler(process.host, port=port)


      connection.response_class = ForwardResponse
      connection.request(self.command, self.path, payload, dict(self.headers))
      try:
        response = connection.getresponse()
      except httplib.HTTPException, e:


        self.send_error(httplib.INTERNAL_SERVER_ERROR, str(e))
        return

      if response.status != httplib.SERVICE_UNAVAILABLE:
        self.wfile.write(response.data)
        return


    self.send_error(httplib.SERVICE_UNAVAILABLE, 'Busy')


class ForwardResponse(httplib.HTTPResponse):
  """Modifies the HTTPResponse class so the raw request data is saved.

  This class is used by balancer instances when balancer requests to a
  backend instance.
  """

  def __init__(self, sock, debuglevel=0, strict=0, method=None):
    httplib.HTTPResponse.__init__(self, sock, debuglevel, strict, method)
    self.data = self.fp.read()
    self.fp = cStringIO.StringIO(self.data)





_dev_process = DevProcess()


def GlobalProcess():
  """Returns a global DevProcess object representing the current process."""
  return _dev_process


def Enabled():
  """Indicates whether the dev_appserver is running in multiprocess mode."""
  return not GlobalProcess().IsDefault()


def HttpServer():
  """Returns the HTTPServer used by this process."""
  return GlobalProcess().HttpServer()


def HandleRequestDirectly(request, client_address):
  """Handles the indicated request directly, without additional processing."""
  BaseHTTPServer.HTTPServer.process_request(
      HttpServer(), request, client_address)


def PosixShutdown():
  """Kills a posix process with os.kill."""
  dev_process = GlobalProcess()
  children = dev_process.Children()
  for term_signal in (signal.SIGTERM, signal.SIGKILL):
    for child in children:
      if child.process is None:
        continue
      if child.process.returncode is not None:
        continue
      pid = child.process.pid
      try:
        logging.debug('posix kill %d with signal %d', pid, term_signal)
        os.kill(pid, term_signal)
      except OSError, err:
        logging.error('Error encountered sending pid %d signal %d:%s\n',
                      pid, term_signal, err)
        break

    time.sleep(0.2)


  for child in children:
    if child.process is None:
      continue
    if child.process.returncode is not None:
      continue
    try:
      child.process.wait()
    except OSError, e:
      if e.errno != errno.ECHILD:
        raise e


def Shutdown():
  """Shut down any child processes started."""
  dev_process = GlobalProcess()
  if not dev_process.IsMaster():
    return



  if os.name == 'nt':

    import ctypes
    for child in dev_process.Children():
      logging.debug('windows kill ' + str(child.process.pid))
      ctypes.windll.kernel32.TerminateProcess(int(child.process._handle), -1)
  else:
    PosixShutdown()


def SetLogPrefix(prefix):
  """Adds a prefix to the log handler to identify the process.

  Args:
    prefix: The prefix string to append at the beginning of each line.
  """
  formatter = logging.Formatter(
      str(prefix) + ' [%(filename)s:%(lineno)d] %(levelname)s %(message)s')
  for handler in logging._handlerList:
    handler.setFormatter(formatter)


def Init(argv, options, root_path, appinfo):
  """Enter multiprocess mode, if required.

  The dev_appserver runs in multiprocess mode if any Backends are configured.
  The initial process becomes a "master" which acts as a router for the app, and
  centralized memcache/datastore API server for sharing persistent state.

  This method works by configuring the global DevProcess object, which is
  referenced by other files in the dev_appserver when necessary.  The DevProcess
  contains state indicating which role the current process plays in the
  multiprocess architecture.

  The master process creates and shuts down subprocesses.  A separate process is
  created to represent an instance of the application, and a separate process is
  created for each backend (to act as a load balancer) and for each backend
  instance.

  On shutdown, the master process kills all subprocesses before exiting.

  Args:
    argv:  The command line arguments used when starting the main application.
    options: Parsed dictionary of the command line arguments.
    root_path:  Root directory of the application.
    appinfo: An AppInfoExternal object representing a parsed app.yaml file.
  """
  if ARG_BACKENDS not in options:
    return

  backends_fh = None
  try:
    backends_fh = open(os.path.join(root_path, 'backends.yaml'))
  except IOError:
    return

  backend_info = None
  try:
    backend_info = backendinfo.LoadBackendInfo(backends_fh.read())
  finally:
    backends_fh.close()

  if not backend_info:
    logging.info('No backends, running in single-process mode.')
    return

  backends = backend_info.backends
  backend_set = set()
  for backend in backends:
    if backend.name in backend_set:
      raise Error('Duplicate backend: %s' % backend.name)
    if backend.instances is None:
      backend.instances = 1
    elif backend.instances > BACKEND_MAX_INSTANCES:
      raise Error('Maximum number of instances is %d', BACKEND_MAX_INSTANCES)
    backend_set.add(backend.name)

  process = _dev_process
  process.Init(appinfo, backends, options)

  if process.IsDefault():
    logging.info('Default process')
    return

  SetLogPrefix(process)
  if process.IsMaster():
    process.StartChildren(argv)

  process.InitBalanceSet()


  if process.IsMaster():
    options['require_indexes'] = False
  else:
    options['require_indexes'] = True

  options['clear_datastore'] = False
  options['clear_prospective_search'] = False
