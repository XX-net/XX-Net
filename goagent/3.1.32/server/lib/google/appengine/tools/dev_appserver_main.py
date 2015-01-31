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



"""Runs a development application server for an application.

%(script)s [options] <application root>

Application root must be the path to the application to run in this server.
Must contain a valid app.yaml or app.yml file.

Options:
  --address=ADDRESS, -a ADDRESS
                             Address to which this server should bind. (Default
                             %(address)s).
  --clear_datastore, -c      Clear the Datastore on startup. (Default false)
  --debug, -d                Use debug logging. (Default false)
  --help, -h                 View this helpful message.
  --port=PORT, -p PORT       Port for the server to run on. (Default %(port)s)

  --allow_skipped_files      Allow access to files matched by app.yaml's
                             skipped_files (default False)
  --auth_domain              Authorization domain that this app runs in.
                             (Default gmail.com)
  --backends                 Run the dev_appserver with backends support
                             (multiprocess mode).
  --blobstore_path=DIR       Path to directory to use for storing Blobstore
                             file stub data.
  --clear_prospective_search Clear the Prospective Search subscription index
                             (Default false).
  --datastore_path=DS_FILE   Path to file to use for storing Datastore file
                             stub data.
                             (Default %(datastore_path)s)
  --debug_imports            Enables debug logging for module imports, showing
                             search paths used for finding modules and any
                             errors encountered during the import process.
  --default_partition        Default partition to use in the APPLICATION_ID.
                             (Default dev)
  --disable_static_caching   Never allow the browser to cache static files.
                             (Default enable if expiration set in app.yaml)
  --disable_task_running     When supplied, tasks will not be automatically
                             run after submission and must be run manually
                             in the local admin console.
  --enable_sendmail          Enable sendmail when SMTP not configured.
                             (Default false)
  --high_replication         Use the high replication datastore consistency
                             model. (Default false).
  --history_path=PATH        Path to use for storing Datastore history.
                             (Default %(history_path)s)
  --multiprocess_min_port    When running in multiprocess mode, specifies the
                             lowest port value to use when choosing ports. If
                             set to 0, select random ports.
                             (Default 9000)
  --mysql_host=HOSTNAME      MySQL database host.
                             Used by the Cloud SQL (rdbms) stub.
                             (Default '%(mysql_host)s')
  --mysql_port=PORT          MySQL port to connect to.
                             Used by the Cloud SQL (rdbms) stub.
                             (Default %(mysql_port)s)
  --mysql_user=USER          MySQL user to connect as.
                             Used by the Cloud SQL (rdbms) stub.
                             (Default %(mysql_user)s)
  --mysql_password=PASSWORD  MySQL password to use.
                             Used by the Cloud SQL (rdbms) stub.
                             (Default '%(mysql_password)s')
  --mysql_socket=PATH        MySQL Unix socket file path.
                             Used by the Cloud SQL (rdbms) stub.
                             (Default '%(mysql_socket)s')
  --require_indexes          Disallows queries that require composite indexes
                             not defined in index.yaml.
  --show_mail_body           Log the body of emails in mail stub.
                             (Default false)
  --skip_sdk_update_check    Skip checking for SDK updates. If false, fall back
                             to opt_in setting specified in .appcfg_nag
                             (Default false)
  --smtp_host=HOSTNAME       SMTP host to send test mail to.  Leaving this
                             unset will disable SMTP mail sending.
                             (Default '%(smtp_host)s')
  --smtp_port=PORT           SMTP port to send test mail to.
                             (Default %(smtp_port)s)
  --smtp_user=USER           SMTP user to connect as.  Stub will only attempt
                             to login if this field is non-empty.
                             (Default '%(smtp_user)s').
  --smtp_password=PASSWORD   Password for SMTP server.
                             (Default '%(smtp_password)s')
  --task_retry_seconds       How long to wait in seconds before retrying a
                             task after it fails during execution.
                             (Default '%(task_retry_seconds)s')
  --use_sqlite               Use the new, SQLite based datastore stub.
                             (Default false)
"""





























from google.appengine.tools import os_compat

import getopt
import logging
import os
import signal
import sys
import tempfile
import traceback




logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s] %(message)s')

from google.appengine.api import yaml_errors
from google.appengine.dist import py_zipimport
from google.appengine.tools import appcfg
from google.appengine.tools import appengine_rpc
from google.appengine.tools import dev_appserver
from google.appengine.tools import dev_appserver_multiprocess as multiprocess





DEFAULT_ADMIN_CONSOLE_SERVER = 'appengine.google.com'


ARG_ADDRESS = 'address'
ARG_ADMIN_CONSOLE_HOST = 'admin_console_host'
ARG_ADMIN_CONSOLE_SERVER = 'admin_console_server'
ARG_ALLOW_SKIPPED_FILES = 'allow_skipped_files'
ARG_AUTH_DOMAIN = 'auth_domain'
ARG_BACKENDS = 'backends'
ARG_BLOBSTORE_PATH = 'blobstore_path'
ARG_CLEAR_DATASTORE = 'clear_datastore'
ARG_CLEAR_PROSPECTIVE_SEARCH = 'clear_prospective_search'
ARG_DATASTORE_PATH = 'datastore_path'
ARG_DEBUG_IMPORTS = 'debug_imports'
ARG_DEFAULT_PARTITION = 'default_partition'
ARG_DISABLE_TASK_RUNNING = 'disable_task_running'
ARG_ENABLE_SENDMAIL = 'enable_sendmail'
ARG_HIGH_REPLICATION = 'high_replication'
ARG_HISTORY_PATH = 'history_path'
ARG_LOGIN_URL = 'login_url'
ARG_LOG_LEVEL = 'log_level'
ARG_MULTIPROCESS = multiprocess.ARG_MULTIPROCESS
ARG_MULTIPROCESS_API_PORT = multiprocess.ARG_MULTIPROCESS_API_PORT
ARG_MULTIPROCESS_API_SERVER = multiprocess.ARG_MULTIPROCESS_API_SERVER
ARG_MULTIPROCESS_APP_INSTANCE_ID = multiprocess.ARG_MULTIPROCESS_APP_INSTANCE_ID
ARG_MULTIPROCESS_BACKEND_ID = multiprocess.ARG_MULTIPROCESS_BACKEND_ID
ARG_MULTIPROCESS_BACKEND_INSTANCE_ID = multiprocess.ARG_MULTIPROCESS_BACKEND_INSTANCE_ID
ARG_MULTIPROCESS_MIN_PORT = multiprocess.ARG_MULTIPROCESS_MIN_PORT
ARG_MYSQL_HOST = 'mysql_host'
ARG_MYSQL_PASSWORD = 'mysql_password'
ARG_MYSQL_PORT = 'mysql_port'
ARG_MYSQL_SOCKET = 'mysql_socket'
ARG_MYSQL_USER = 'mysql_user'
ARG_PORT = 'port'
ARG_PROSPECTIVE_SEARCH_PATH = 'prospective_search_path'
ARG_REQUIRE_INDEXES = 'require_indexes'
ARG_SHOW_MAIL_BODY = 'show_mail_body'
ARG_SKIP_SDK_UPDATE_CHECK = 'skip_sdk_update_check'
ARG_SMTP_HOST = 'smtp_host'
ARG_SMTP_PASSWORD = 'smtp_password'
ARG_SMTP_PORT = 'smtp_port'
ARG_SMTP_USER = 'smtp_user'
ARG_STATIC_CACHING = 'static_caching'
ARG_TASK_RETRY_SECONDS = 'task_retry_seconds'


ARG_TRUSTED = 'trusted'
ARG_USE_SQLITE = 'use_sqlite'


SDK_PATH = os.path.dirname(
             os.path.dirname(
               os.path.dirname(
                 os.path.dirname(os_compat.__file__)
               )
             )
           )


PRODUCTION_VERSION = (2, 5)
WARN_ABOUT_PYTHON_VERSION = True

DEFAULT_ARGS = {
  ARG_ADDRESS: 'localhost',
  ARG_ADMIN_CONSOLE_HOST: None,
  ARG_ADMIN_CONSOLE_SERVER: DEFAULT_ADMIN_CONSOLE_SERVER,
  ARG_ALLOW_SKIPPED_FILES: False,
  ARG_AUTH_DOMAIN: 'gmail.com',
  ARG_BLOBSTORE_PATH: os.path.join(tempfile.gettempdir(),
                                   'dev_appserver.blobstore'),
  ARG_CLEAR_DATASTORE: False,
  ARG_CLEAR_PROSPECTIVE_SEARCH: False,
  ARG_DATASTORE_PATH: os.path.join(tempfile.gettempdir(),
                                   'dev_appserver.datastore'),
  ARG_DEFAULT_PARTITION: 'dev',
  ARG_DISABLE_TASK_RUNNING: False,
  ARG_ENABLE_SENDMAIL: False,
  ARG_HIGH_REPLICATION: False,
  ARG_HISTORY_PATH: os.path.join(tempfile.gettempdir(),
                                 'dev_appserver.datastore.history'),
  ARG_LOGIN_URL: '/_ah/login',
  ARG_LOG_LEVEL: logging.INFO,
  ARG_MYSQL_HOST: 'localhost',
  ARG_MYSQL_PASSWORD: '',
  ARG_MYSQL_PORT: 3306,
  ARG_MYSQL_SOCKET: '',
  ARG_MYSQL_USER: '',
  ARG_PORT: 8080,
  ARG_PROSPECTIVE_SEARCH_PATH: os.path.join(tempfile.gettempdir(),
                                            'dev_appserver.prospective_search'),
  ARG_REQUIRE_INDEXES: False,
  ARG_SHOW_MAIL_BODY: False,
  ARG_SKIP_SDK_UPDATE_CHECK: False,
  ARG_SMTP_HOST: '',
  ARG_SMTP_PASSWORD: '',
  ARG_SMTP_PORT: 25,
  ARG_SMTP_USER: '',
  ARG_STATIC_CACHING: True,
  ARG_TASK_RETRY_SECONDS: 30,
  ARG_TRUSTED: False,
  ARG_USE_SQLITE: False,
}


def PrintUsageExit(code):
  """Prints usage information and exits with a status code.

  Args:
    code: Status code to pass to sys.exit() after displaying usage information.
  """
  render_dict = DEFAULT_ARGS.copy()
  render_dict['script'] = os.path.basename(sys.argv[0])
  print sys.modules['__main__'].__doc__ % render_dict
  sys.stdout.flush()
  sys.exit(code)


def ParseArguments(argv):
  """Parses command-line arguments.

  Args:
    argv: Command-line arguments, including the executable name, used to
      execute this application.

  Returns:
    Tuple (args, option_dict) where:
      args: List of command-line arguments following the executable name.
      option_dict: Dictionary of parsed flags that maps keys from DEFAULT_ARGS
        to their values, which are either pulled from the defaults, or from
        command-line flags.
  """
  option_dict = DEFAULT_ARGS.copy()

  try:
    opts, args = getopt.gnu_getopt(
      argv[1:],
      'a:cdhp:',
      [ 'address=',
        'admin_console_host=',
        'admin_console_server=',
        'allow_skipped_files',
        'auth_domain=',
        'backends',
        'blobstore_path=',
        'clear_datastore',
        'clear_prospective_search',
        'datastore_path=',
        'debug',
        'debug_imports',
        'default_partition=',
        'disable_static_caching',
        'disable_task_running',
        'enable_sendmail',
        'help',
        'high_replication',
        'history_path=',
        'multiprocess',
        'multiprocess_api_port=',
        'multiprocess_api_server',
        'multiprocess_app_instance_id=',
        'multiprocess_backend_id=',
        'multiprocess_backend_instance_id=',
        'multiprocess_min_port=',
        'mysql_host=',
        'mysql_password=',
        'mysql_port=',
        'mysql_socket=',
        'mysql_user=',
        'port=',
        'require_indexes',
        'show_mail_body',
        'skip_sdk_update_check',
        'smtp_host=',
        'smtp_password=',
        'smtp_port=',
        'smtp_user=',
        'task_retry_seconds=',
        'trusted',
        'use_sqlite',
      ])
  except getopt.GetoptError, e:
    print >>sys.stderr, 'Error: %s' % e
    PrintUsageExit(1)

  for option, value in opts:
    if option in ('-h', '--help'):
      PrintUsageExit(0)

    if option in ('-d', '--debug'):
      option_dict[ARG_LOG_LEVEL] = logging.DEBUG

    if option in ('-p', '--port'):
      try:
        option_dict[ARG_PORT] = int(value)
        if not (65535 > option_dict[ARG_PORT] > 0):
          raise ValueError
      except ValueError:
        print >>sys.stderr, 'Invalid value supplied for port'
        PrintUsageExit(1)

    def expand_path(s):
      return os.path.abspath(os.path.expanduser(s))

    if option in ('-a', '--address'):
      option_dict[ARG_ADDRESS] = value

    if option == '--blobstore_path':
      option_dict[ARG_BLOBSTORE_PATH] = expand_path(value)

    if option == '--datastore_path':
      option_dict[ARG_DATASTORE_PATH] = expand_path(value)

    if option == '--prospective_search_path':
      option_dict[ARG_PROSPECTIVE_SEARCH_PATH] = expand_path(value)

    if option == '--skip_sdk_update_check':
      option_dict[ARG_SKIP_SDK_UPDATE_CHECK] = True

    if option == '--use_sqlite':
      option_dict[ARG_USE_SQLITE] = True

    if option == '--high_replication':
      option_dict[ARG_HIGH_REPLICATION] = True

    if option == '--history_path':
      option_dict[ARG_HISTORY_PATH] = expand_path(value)

    if option in ('-c', '--clear_datastore'):
      option_dict[ARG_CLEAR_DATASTORE] = True

    if option == '--clear_prospective_search':
      option_dict[ARG_CLEAR_PROSPECTIVE_SEARCH] = True

    if option == '--require_indexes':
      option_dict[ARG_REQUIRE_INDEXES] = True

    if option == '--mysql_host':
      option_dict[ARG_MYSQL_HOST] = value

    if option == '--mysql_port':
      option_dict[ARG_MYSQL_PORT] = _ParsePort(value, '--mysql_port')

    if option == '--mysql_user':
      option_dict[ARG_MYSQL_USER] = value

    if option == '--mysql_password':
      option_dict[ARG_MYSQL_PASSWORD] = value

    if option == '--mysql_socket':
      option_dict[ARG_MYSQL_SOCKET] = value

    if option == '--smtp_host':
      option_dict[ARG_SMTP_HOST] = value

    if option == '--smtp_port':
      option_dict[ARG_SMTP_PORT] = _ParsePort(value, '--smtp_port')

    if option == '--smtp_user':
      option_dict[ARG_SMTP_USER] = value

    if option == '--smtp_password':
      option_dict[ARG_SMTP_PASSWORD] = value

    if option == '--enable_sendmail':
      option_dict[ARG_ENABLE_SENDMAIL] = True

    if option == '--show_mail_body':
      option_dict[ARG_SHOW_MAIL_BODY] = True

    if option == '--auth_domain':
      option_dict['_DEFAULT_ENV_AUTH_DOMAIN'] = value

    if option == '--debug_imports':
      option_dict['_ENABLE_LOGGING'] = True

    if option == '--admin_console_server':
      option_dict[ARG_ADMIN_CONSOLE_SERVER] = value.strip()

    if option == '--admin_console_host':
      option_dict[ARG_ADMIN_CONSOLE_HOST] = value

    if option == '--allow_skipped_files':
      option_dict[ARG_ALLOW_SKIPPED_FILES] = True

    if option == '--disable_static_caching':
      option_dict[ARG_STATIC_CACHING] = False

    if option == '--disable_task_running':
      option_dict[ARG_DISABLE_TASK_RUNNING] = True

    if option == '--task_retry_seconds':
      try:
        option_dict[ARG_TASK_RETRY_SECONDS] = int(value)
        if option_dict[ARG_TASK_RETRY_SECONDS] < 0:
          raise ValueError
      except ValueError:
        print >>sys.stderr, 'Invalid value supplied for task_retry_seconds'
        PrintUsageExit(1)

    if option == '--trusted':
      option_dict[ARG_TRUSTED] = True

    if option == '--backends':
      option_dict[ARG_BACKENDS] = value
    if option == '--multiprocess':
      option_dict[ARG_MULTIPROCESS] = value
    if option == '--multiprocess_min_port':
      option_dict[ARG_MULTIPROCESS_MIN_PORT] = value
    if option == '--multiprocess_api_server':
      option_dict[ARG_MULTIPROCESS_API_SERVER] = value
    if option == '--multiprocess_api_port':
      option_dict[ARG_MULTIPROCESS_API_PORT] = value
    if option == '--multiprocess_app_instance_id':
      option_dict[ARG_MULTIPROCESS_APP_INSTANCE_ID] = value
    if option == '--multiprocess_backend_id':
      option_dict[ARG_MULTIPROCESS_BACKEND_ID] = value
    if option == '--multiprocess_backend_instance_id':
      option_dict[ARG_MULTIPROCESS_BACKEND_INSTANCE_ID] = value

    if option == '--default_partition':
      option_dict[ARG_DEFAULT_PARTITION] = value

  return args, option_dict


def _ParsePort(port, description):
  """Parses a port number from a string.

  Args:
    port: string
    description: string to use in error messages.

  Returns: integer between 0 and 65535

  Raises:
    ValueError if port is not a valid port number.
  """
  try:
    port = int(port)
    if not (65535 > port > 0):
      raise ValueError
    return port
  except ValueError:
    print >>sys.stderr, 'Invalid value %s supplied for %s' % (port, description)
    PrintUsageExit(1)


def MakeRpcServer(option_dict):
  """Create a new HttpRpcServer.

  Creates a new HttpRpcServer to check for updates to the SDK.

  Args:
    option_dict: The dict of command line options.

  Returns:
    A HttpRpcServer.
  """
  server = appengine_rpc.HttpRpcServer(
      option_dict[ARG_ADMIN_CONSOLE_SERVER],
      lambda: ('unused_email', 'unused_password'),
      appcfg.GetUserAgent(),
      appcfg.GetSourceName(),
      host_override=option_dict[ARG_ADMIN_CONSOLE_HOST])

  server.authenticated = True
  return server


def SigTermHandler(signum, frame):
  """Handler for TERM signal.

  Raises a KeyboardInterrupt to perform a graceful shutdown on SIGTERM signal.
  """
  raise KeyboardInterrupt()


def main(argv):
  """Runs the development application server."""
  args, option_dict = ParseArguments(argv)

  if len(args) != 1:
    print >>sys.stderr, 'Invalid arguments'
    PrintUsageExit(1)

  root_path = args[0]

  if '_DEFAULT_ENV_AUTH_DOMAIN' in option_dict:
    auth_domain = option_dict['_DEFAULT_ENV_AUTH_DOMAIN']
    dev_appserver.DEFAULT_ENV['AUTH_DOMAIN'] = auth_domain
  if '_ENABLE_LOGGING' in option_dict:
    enable_logging = option_dict['_ENABLE_LOGGING']
    dev_appserver.HardenedModulesHook.ENABLE_LOGGING = enable_logging

  log_level = option_dict[ARG_LOG_LEVEL]



  option_dict['root_path'] = os.path.realpath(root_path)


  logging.getLogger().setLevel(log_level)

  default_partition = option_dict[ARG_DEFAULT_PARTITION]
  appinfo = None
  try:
    appinfo, matcher, _ = dev_appserver.LoadAppConfig(
        root_path, {}, default_partition=default_partition)
  except yaml_errors.EventListenerError, e:
    logging.error('Fatal error when loading application configuration:\n%s', e)
    return 1
  except dev_appserver.InvalidAppConfigError, e:
    logging.error('Application configuration file invalid:\n%s', e)
    return 1

  version_tuple = tuple(sys.version_info[:2])
  expected_version = PRODUCTION_VERSION
  if appinfo.runtime == 'python27':
    expected_version = (2, 7)

  if ARG_MULTIPROCESS not in option_dict and WARN_ABOUT_PYTHON_VERSION:
    if version_tuple < expected_version:
      sys.stderr.write('Warning: You are using a Python runtime (%d.%d) that '
                       'is older than the production runtime environment '
                       '(%d.%d). Your application may be dependent on Python '
                       'behaviors that have changed and may not work correctly '
                       'when deployed to production.\n' % (
                           version_tuple[0], version_tuple[1],
                           expected_version[0], expected_version[1]))

    if version_tuple > expected_version:
      sys.stderr.write('Warning: You are using a Python runtime (%d.%d) that '
                       'is more recent than the production runtime environment '
                       '(%d.%d). Your application may use features that are '
                       'not available in the production environment and may '
                       'not work correctly when deployed to production.\n' % (
                           version_tuple[0], version_tuple[1],
                           expected_version[0], expected_version[1]))

  multiprocess.Init(argv, option_dict, root_path, appinfo)
  dev_process = multiprocess.GlobalProcess()
  port = option_dict[ARG_PORT]
  login_url = option_dict[ARG_LOGIN_URL]
  address = option_dict[ARG_ADDRESS]
  require_indexes = option_dict[ARG_REQUIRE_INDEXES]
  allow_skipped_files = option_dict[ARG_ALLOW_SKIPPED_FILES]
  static_caching = option_dict[ARG_STATIC_CACHING]
  skip_sdk_update_check = option_dict[ARG_SKIP_SDK_UPDATE_CHECK]

  if (option_dict[ARG_ADMIN_CONSOLE_SERVER] != '' and
      not dev_process.IsSubprocess()):

    server = MakeRpcServer(option_dict)
    if skip_sdk_update_check:
      logging.info('Skipping update check.')
    else:
      update_check = appcfg.UpdateCheck(server, appinfo)
      update_check.CheckSupportedVersion()
      if update_check.AllowedToCheckForUpdates():
        update_check.CheckForUpdates()

  if dev_process.IsSubprocess():
    logging.getLogger().setLevel(logging.WARNING)

  try:
    dev_appserver.SetupStubs(appinfo.application, **option_dict)
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logging.error(str(exc_type) + ': ' + str(exc_value))
    logging.debug(''.join(traceback.format_exception(
          exc_type, exc_value, exc_traceback)))
    return 1

  http_server = dev_appserver.CreateServer(
      root_path,
      login_url,
      port,
      sdk_dir=SDK_PATH,
      serve_address=address,
      require_indexes=require_indexes,
      allow_skipped_files=allow_skipped_files,
      static_caching=static_caching,
      default_partition=default_partition)

  signal.signal(signal.SIGTERM, SigTermHandler)

  dev_process.PrintStartMessage(appinfo.application, address, port)

  if dev_process.IsInstance():
    logging.getLogger().setLevel(logging.INFO)

  try:
    try:
      http_server.serve_forever()
    except KeyboardInterrupt:
      if not dev_process.IsSubprocess():
        logging.info('Server interrupted by user, terminating')
    except:
      exc_info = sys.exc_info()
      info_string = '\n'.join(traceback.format_exception(*exc_info))
      logging.error('Error encountered:\n%s\nNow terminating.', info_string)
      return 1
    finally:
      http_server.server_close()
  finally:
    done = False
    while not done:
      try:
        multiprocess.Shutdown()
        done = True
      except KeyboardInterrupt:
        pass

  return 0



if __name__ == '__main__':
  sys.exit(main(sys.argv))
