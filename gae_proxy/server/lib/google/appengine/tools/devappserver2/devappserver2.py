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
"""The main entry point for the new development server."""



import argparse
import errno
import getpass
import itertools
import logging
import os
import sys
import tempfile
import time

from google.appengine.api import appinfo
from google.appengine.api import request_info
from google.appengine.datastore import datastore_stub_util
from google.appengine.tools import boolean_action
from google.appengine.tools.devappserver2 import api_server
from google.appengine.tools.devappserver2 import application_configuration
from google.appengine.tools.devappserver2 import dispatcher
from google.appengine.tools.devappserver2 import gcd_application
from google.appengine.tools.devappserver2 import login
from google.appengine.tools.devappserver2 import runtime_config_pb2
from google.appengine.tools.devappserver2 import runtime_factories
from google.appengine.tools.devappserver2 import shutdown
from google.appengine.tools.devappserver2 import update_checker
from google.appengine.tools.devappserver2 import wsgi_request_info
from google.appengine.tools.devappserver2.admin import admin_server

# Initialize logging early -- otherwise some library packages may
# pre-empt our log formatting.  NOTE: the level is provisional; it may
# be changed in main() based on the --debug flag.
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-8s %(asctime)s %(filename)s:%(lineno)s] %(message)s')

# Valid choices for --log_level and their corresponding constants in
# runtime_config_pb2.Config.stderr_log_level.
_LOG_LEVEL_TO_RUNTIME_CONSTANT = {
    'debug': 0,
    'info': 1,
    'warning': 2,
    'error': 3,
    'critical': 4,
}

# Valid choices for --dev_appserver_log_level and their corresponding Python
# logging levels
_LOG_LEVEL_TO_PYTHON_CONSTANT = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}

# The default encoding used by the production interpreter.
_PROD_DEFAULT_ENCODING = 'ascii'

# The environment variable exposed in the devshell.
_DEVSHELL_ENV = 'DEVSHELL_CLIENT_PORT'


def _generate_storage_paths(app_id):
  """Yield an infinite sequence of possible storage paths."""
  if sys.platform == 'win32':
    # The temp directory is per-user on Windows so there is no reason to add
    # the username to the generated directory name.
    user_format = ''
  else:
    try:
      user_name = getpass.getuser()
    except Exception:  # The possible set of exceptions is not documented.
      user_format = ''
    else:
      user_format = '.%s' % user_name

  tempdir = tempfile.gettempdir()
  yield os.path.join(tempdir, 'appengine.%s%s' % (app_id, user_format))
  for i in itertools.count(1):
    yield os.path.join(tempdir, 'appengine.%s%s.%d' % (app_id, user_format, i))


def _get_storage_path(path, app_id):
  """Returns a path to the directory where stub data can be stored."""
  _, _, app_id = app_id.replace(':', '_').rpartition('~')
  if path is None:
    for path in _generate_storage_paths(app_id):
      try:
        os.mkdir(path, 0700)
      except OSError, e:
        if e.errno == errno.EEXIST:
          # Check that the directory is only accessable by the current user to
          # protect against an attacker creating the directory in advance in
          # order to access any created files. Windows has per-user temporary
          # directories and st_mode does not include per-user permission
          # information so assume that it is safe.
          if sys.platform == 'win32' or (
              (os.stat(path).st_mode & 0777) == 0700 and os.path.isdir(path)):
            return path
          else:
            continue
        raise
      else:
        return path
  elif not os.path.exists(path):
    os.mkdir(path)
    return path
  elif not os.path.isdir(path):
    raise IOError('the given storage path %r is a file, a directory was '
                  'expected' % path)
  else:
    return path


class PortParser(object):
  """A parser for ints that represent ports."""

  def __init__(self, allow_port_zero=True):
    self._min_port = 0 if allow_port_zero else 1

  def __call__(self, value):
    try:
      port = int(value)
    except ValueError:
      raise argparse.ArgumentTypeError('Invalid port: %r' % value)
    if port < self._min_port or port >= (1 << 16):
      raise argparse.ArgumentTypeError('Invalid port: %d' % port)
    return port


def parse_per_module_option(
    value, value_type, value_predicate,
    single_bad_type_error, single_bad_predicate_error,
    multiple_bad_type_error, multiple_bad_predicate_error,
    multiple_duplicate_module_error):
  """Parses command line options that may be specified per-module.

  Args:
    value: A str containing the flag value to parse. Two formats are supported:
        1. A universal value (may not contain a colon as that is use to
           indicate a per-module value).
        2. Per-module values. One or more comma separated module-value pairs.
           Each pair is a module_name:value. An empty module-name is shorthand
           for "default" to match how not specifying a module name in the yaml
           is the same as specifying "module: default".
    value_type: a callable that converts the string representation of the value
        to the actual value. Should raise ValueError if the string can not
        be converted.
    value_predicate: a predicate to call on the converted value to validate
        the converted value. Use "lambda _: True" if all values are valid.
    single_bad_type_error: the message to use if a universal value is provided
        and value_type throws a ValueError. The message must consume a single
        format parameter (the provided value).
    single_bad_predicate_error: the message to use if a universal value is
        provided and value_predicate returns False. The message does not
        get any format parameters.
    multiple_bad_type_error: the message to use if a per-module value
        either does not have two values separated by a single colon or if
        value_types throws a ValueError on the second string. The message must
        consume a single format parameter (the module_name:value pair).
    multiple_bad_predicate_error: the message to use if a per-module value if
        value_predicate returns False. The message must consume a single format
        parameter (the module name).
    multiple_duplicate_module_error: the message to use if the same module is
        repeated. The message must consume a single formater parameter (the
        module name).

  Returns:
    Either a single value of value_type for universal values or a dict of
    str->value_type for per-module values.

  Raises:
    argparse.ArgumentTypeError: the value is invalid.
  """
  if ':' not in value:
    try:
      single_value = value_type(value)
    except ValueError:
      raise argparse.ArgumentTypeError(single_bad_type_error % value)
    else:
      if not value_predicate(single_value):
        raise argparse.ArgumentTypeError(single_bad_predicate_error)
      return single_value
  else:
    module_to_value = {}
    for module_value in value.split(','):
      try:
        module_name, single_value = module_value.split(':')
        single_value = value_type(single_value)
      except ValueError:
        raise argparse.ArgumentTypeError(multiple_bad_type_error % module_value)
      else:
        module_name = module_name.strip()
        if not module_name:
          module_name = appinfo.DEFAULT_MODULE
        if module_name in module_to_value:
          raise argparse.ArgumentTypeError(
              multiple_duplicate_module_error % module_name)
        if not value_predicate(single_value):
          raise argparse.ArgumentTypeError(
              multiple_bad_predicate_error % module_name)
        module_to_value[module_name] = single_value
    return module_to_value


def parse_max_module_instances(value):
  """Returns the parsed value for the --max_module_instances flag.

  Args:
    value: A str containing the flag value for parse. The format should follow
        one of the following examples:
          1. "5" - All modules are limited to 5 instances.
          2. "default:3,backend:20" - The default module can have 3 instances,
             "backend" can have 20 instances and all other modules are
              unaffected. An empty name (i.e. ":3") is shorthand for default
              to match how not specifying a module name in the yaml is the
              same as specifying "module: default".
  Returns:
    The parsed value of the max_module_instances flag. May either be an int
    (for values of the form "5") or a dict of str->int (for values of the
    form "default:3,backend:20").

  Raises:
    argparse.ArgumentTypeError: the value is invalid.
  """
  return parse_per_module_option(
      value, int, lambda instances: instances > 0,
      'Invalid max instance count: %r',
      'Max instance count must be greater than zero',
      'Expected "module:max_instance_count": %r',
      'Max instance count for module %s must be greater than zero',
      'Duplicate max instance count for module %s')


def parse_threadsafe_override(value):
  """Returns the parsed value for the --threadsafe_override flag.

  Args:
    value: A str containing the flag value for parse. The format should follow
        one of the following examples:
          1. "False" - All modules override the YAML threadsafe configuration
             as if the YAML contained False.
          2. "default:False,backend:True" - The default module overrides the
             YAML threadsafe configuration as if the YAML contained False, the
             "backend" module overrides with a value of True and all other
             modules use the value in the YAML file. An empty name (i.e.
             ":True") is shorthand for default to match how not specifying a
             module name in the yaml is the same as specifying
             "module: default".
  Returns:
    The parsed value of the threadsafe_override flag. May either be a bool
    (for values of the form "False") or a dict of str->bool (for values of the
    form "default:False,backend:True").

  Raises:
    argparse.ArgumentTypeError: the value is invalid.
  """
  return parse_per_module_option(
      value, boolean_action.BooleanParse, lambda _: True,
      'Invalid threadsafe override: %r',
      None,
      'Expected "module:threadsafe_override": %r',
      None,
      'Duplicate threadsafe override value for module %s')


def parse_path(value):
  """Returns the given path with ~ and environment variables expanded."""
  return os.path.expanduser(os.path.expandvars(value))


def create_command_line_parser():
  """Returns an argparse.ArgumentParser to parse command line arguments."""
  # TODO: Add more robust argument validation. Consider what flags
  # are actually needed.

  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  arg_name = 'yaml_path'
  arg_help = 'Path to a yaml file, or a directory containing yaml files'
  if application_configuration.java_supported():
    arg_name = 'yaml_or_war_path'
    arg_help += ', or a directory containing WEB-INF/web.xml'
  parser.add_argument(
      'config_paths', metavar=arg_name, nargs='+', help=arg_help)

  if _DEVSHELL_ENV in os.environ:
    default_server_host = '0.0.0.0'
  else:
    default_server_host = 'localhost'

  common_group = parser.add_argument_group('Common')
  common_group.add_argument(
      '-A', '--application', action='store', dest='app_id',
      help='Set the application, overriding the application value from the '
      'app.yaml file.')
  common_group.add_argument(
      '--host', default=default_server_host,
      help='host name to which application modules should bind')
  common_group.add_argument(
      '--port', type=PortParser(), default=8080,
      help='lowest port to which application modules should bind')
  common_group.add_argument(
      '--admin_host', default=default_server_host,
      help='host name to which the admin server should bind')
  common_group.add_argument(
      '--admin_port', type=PortParser(), default=8000,
      help='port to which the admin server should bind')
  # TODO: Change this. Eventually we want a way to associate ports
  # with external modules, with default values. For now we allow only one
  # external module, with a port number that must be passed in here.
  common_group.add_argument(
      '--external_port', type=PortParser(), default=None,
      help=argparse.SUPPRESS)
  common_group.add_argument(
      '--auth_domain', default='gmail.com',
      help='name of the authorization domain to use')
  common_group.add_argument(
      '--storage_path', metavar='PATH',
      type=parse_path,
      help='path to the data (datastore, blobstore, etc.) associated with the '
      'application.')
  common_group.add_argument(
      '--log_level', default='info',
      choices=_LOG_LEVEL_TO_RUNTIME_CONSTANT.keys(),
      help='the log level below which logging messages generated by '
      'application code will not be displayed on the console')
  common_group.add_argument(
      '--max_module_instances',
      type=parse_max_module_instances,
      help='the maximum number of runtime instances that can be started for a '
      'particular module - the value can be an integer, in what case all '
      'modules are limited to that number of instances or a comma-seperated '
      'list of module:max_instances e.g. "default:5,backend:3"')
  common_group.add_argument(
      '--use_mtime_file_watcher',
      action=boolean_action.BooleanAction,
      const=True,
      default=False,
      help='use mtime polling for detecting source code changes - useful if '
      'modifying code from a remote machine using a distributed file system')
  common_group.add_argument(
      '--threadsafe_override',
      type=parse_threadsafe_override,
      help='override the application\'s threadsafe configuration - the value '
      'can be a boolean, in which case all modules threadsafe setting will '
      'be overridden or a comma-separated list of module:threadsafe_override '
      'e.g. "default:False,backend:True"')
  common_group.add_argument('--enable_mvm_logs',
                            action=boolean_action.BooleanAction,
                            const=True,
                            default=False,
                            help=argparse.SUPPRESS)

  # PHP
  php_group = parser.add_argument_group('PHP')
  php_group.add_argument('--php_executable_path', metavar='PATH',
                         type=parse_path,
                         help='path to the PHP executable')
  php_group.add_argument('--php_remote_debugging',
                         action=boolean_action.BooleanAction,
                         const=True,
                         default=False,
                         help='enable XDebug remote debugging')
  php_group.add_argument('--php_gae_extension_path', metavar='PATH',
                         type=parse_path,
                         help='path to the GAE PHP extension')
  php_group.add_argument('--php_xdebug_extension_path', metavar='PATH',
                         type=parse_path,
                         help='path to the xdebug extension')

  # App Identity
  appidentity_group = parser.add_argument_group('Application Identity')
  appidentity_group.add_argument(
      '--appidentity_email_address',
      help='email address associated with a service account that has a '
      'downloadable key. May be None for no local application identity.')
  appidentity_group.add_argument(
      '--appidentity_private_key_path',
      help='path to private key file associated with service account '
      '(.pem format). Must be set if appidentity_email_address is set.')
  # Supressing the help text, as it is unlikely any typical user outside
  # of Google has an appropriately set up test oauth server that devappserver2
  # could talk to.
  # URL to the oauth server that devappserver2 should  use to authenticate the
  # appidentity private key (defaults to the standard Google production server.
  appidentity_group.add_argument(
      '--appidentity_oauth_url',
      help=argparse.SUPPRESS)

  # Python
  python_group = parser.add_argument_group('Python')
  python_group.add_argument(
      '--python_startup_script',
      help='the script to run at the startup of new Python runtime instances '
      '(useful for tools such as debuggers.')
  python_group.add_argument(
      '--python_startup_args',
      help='the arguments made available to the script specified in '
      '--python_startup_script.')

  # Java
  java_group = parser.add_argument_group('Java')
  java_group.add_argument(
      '--jvm_flag', action='append',
      help='additional arguments to pass to the java command when launching '
      'an instance of the app. May be specified more than once. Example: '
      '--jvm_flag=-Xmx1024m --jvm_flag=-Xms256m')

  # Custom
  custom_group = parser.add_argument_group('Custom VM Runtime')
  custom_group.add_argument(
      '--custom_entrypoint',
      help='specify an entrypoint for custom runtime modules. This is '
      'required when such modules are present. Include "{port}" in the '
      'string (without quotes) to pass the port number in as an argument. For '
      'instance: --custom_entrypoint="gunicorn -b localhost:{port} '
      'mymodule:application"',
      default='')
  custom_group.add_argument(
      '--runtime',
      help='specify the default runtimes you would like to use.  Valid '
      'runtimes are %s.' % runtime_factories.valid_runtimes(),
      default='')

  # Blobstore
  blobstore_group = parser.add_argument_group('Blobstore API')
  blobstore_group.add_argument(
      '--blobstore_path',
      type=parse_path,
      help='path to directory used to store blob contents '
      '(defaults to a subdirectory of --storage_path if not set)',
      default=None)
  # TODO: Remove after the Files API is really gone.
  blobstore_group.add_argument(
      '--blobstore_warn_on_files_api_use',
      action=boolean_action.BooleanAction,
      const=True,
      default=True,
      help=argparse.SUPPRESS)
  blobstore_group.add_argument(
      '--blobstore_enable_files_api',
      action=boolean_action.BooleanAction,
      const=True,
      default=False,
      help=argparse.SUPPRESS)

  # Cloud SQL
  cloud_sql_group = parser.add_argument_group('Cloud SQL')
  cloud_sql_group.add_argument(
      '--mysql_host',
      default='localhost',
      help='host name of a running MySQL server used for simulated Google '
      'Cloud SQL storage')
  cloud_sql_group.add_argument(
      '--mysql_port', type=PortParser(allow_port_zero=False),
      default=3306,
      help='port number of a running MySQL server used for simulated Google '
      'Cloud SQL storage')
  cloud_sql_group.add_argument(
      '--mysql_user',
      default='',
      help='username to use when connecting to the MySQL server specified in '
      '--mysql_host and --mysql_port or --mysql_socket')
  cloud_sql_group.add_argument(
      '--mysql_password',
      default='',
      help='password to use when connecting to the MySQL server specified in '
      '--mysql_host and --mysql_port or --mysql_socket')
  cloud_sql_group.add_argument(
      '--mysql_socket',
      help='path to a Unix socket file to use when connecting to a running '
      'MySQL server used for simulated Google Cloud SQL storage')

  # Datastore
  datastore_group = parser.add_argument_group('Datastore API')
  datastore_group.add_argument(
      '--datastore_path',
      type=parse_path,
      default=None,
      help='path to a file used to store datastore contents '
      '(defaults to a file in --storage_path if not set)',)
  datastore_group.add_argument('--clear_datastore',
                               action=boolean_action.BooleanAction,
                               const=True,
                               default=False,
                               help='clear the datastore on startup')
  datastore_group.add_argument(
      '--datastore_consistency_policy',
      default='time',
      choices=['consistent', 'random', 'time'],
      help='the policy to apply when deciding whether a datastore write should '
      'appear in global queries')
  datastore_group.add_argument(
      '--require_indexes',
      action=boolean_action.BooleanAction,
      const=True,
      default=False,
      help='generate an error on datastore queries that '
      'requires a composite index not found in index.yaml')
  datastore_group.add_argument(
      '--auto_id_policy',
      default=datastore_stub_util.SCATTERED,
      choices=[datastore_stub_util.SEQUENTIAL,
               datastore_stub_util.SCATTERED],
      help='the type of sequence from which the datastore stub '
      'assigns automatic IDs. NOTE: Sequential IDs are '
      'deprecated. This flag will be removed in a future '
      'release. Please do not rely on sequential IDs in your '
      'tests.')
  datastore_group.add_argument(
      '--enable_cloud_datastore',
      action=boolean_action.BooleanAction,
      const=True,
      default=False,
      help=argparse.SUPPRESS #'enable the Google Cloud Datastore API.'
      )

  # Logs
  logs_group = parser.add_argument_group('Logs API')
  logs_group.add_argument(
      '--logs_path', default=None,
      help='path to a file used to store request logs (defaults to a file in '
      '--storage_path if not set)',)

  # Mail
  mail_group = parser.add_argument_group('Mail API')
  mail_group.add_argument(
      '--show_mail_body',
      action=boolean_action.BooleanAction,
      const=True,
      default=False,
      help='logs the contents of e-mails sent using the Mail API')
  mail_group.add_argument(
      '--enable_sendmail',
      action=boolean_action.BooleanAction,
      const=True,
      default=False,
      help='use the "sendmail" tool to transmit e-mail sent '
      'using the Mail API (ignored if --smtp_host is set)')
  mail_group.add_argument(
      '--smtp_host', default='',
      help='host name of an SMTP server to use to transmit '
      'e-mail sent using the Mail API')
  mail_group.add_argument(
      '--smtp_port', default=25,
      type=PortParser(allow_port_zero=False),
      help='port number of an SMTP server to use to transmit '
      'e-mail sent using the Mail API (ignored if --smtp_host '
      'is not set)')
  mail_group.add_argument(
      '--smtp_user', default='',
      help='username to use when connecting to the SMTP server '
      'specified in --smtp_host and --smtp_port')
  mail_group.add_argument(
      '--smtp_password', default='',
      help='password to use when connecting to the SMTP server '
      'specified in --smtp_host and --smtp_port')
  mail_group.add_argument(
      '--smtp_allow_tls',
      action=boolean_action.BooleanAction,
      const=True,
      default=True,
      help='Allow TLS to be used when the SMTP server announces TLS support '
      '(ignored if --smtp_host is not set)')

  # Matcher
  prospective_search_group = parser.add_argument_group('Prospective Search API')
  prospective_search_group.add_argument(
      '--prospective_search_path', default=None,
      type=parse_path,
      help='path to a file used to store the prospective '
      'search subscription index (defaults to a file in '
      '--storage_path if not set)')
  prospective_search_group.add_argument(
      '--clear_prospective_search',
      action=boolean_action.BooleanAction,
      const=True,
      default=False,
      help='clear the prospective search subscription index')

  # Search
  search_group = parser.add_argument_group('Search API')
  search_group.add_argument(
      '--search_indexes_path', default=None,
      type=parse_path,
      help='path to a file used to store search indexes '
      '(defaults to a file in --storage_path if not set)',)
  search_group.add_argument(
      '--clear_search_indexes',
      action=boolean_action.BooleanAction,
      const=True,
      default=False,
      help='clear the search indexes')

  # Taskqueue
  taskqueue_group = parser.add_argument_group('Task Queue API')
  taskqueue_group.add_argument(
      '--enable_task_running',
      action=boolean_action.BooleanAction,
      const=True,
      default=True,
      help='run "push" tasks created using the taskqueue API automatically')

  # Misc
  misc_group = parser.add_argument_group('Miscellaneous')
  misc_group.add_argument(
      '--allow_skipped_files',
      action=boolean_action.BooleanAction,
      const=True,
      default=False,
      help='make files specified in the app.yaml "skip_files" or "static" '
      'handles readable by the application.')
  # No help to avoid lengthening help message for rarely used feature:
  # host name to which the server for API calls should bind.
  misc_group.add_argument(
      '--api_host', default=default_server_host,
      help=argparse.SUPPRESS)
  misc_group.add_argument(
      '--api_port', type=PortParser(), default=0,
      help='port to which the server for API calls should bind')
  misc_group.add_argument(
      '--automatic_restart',
      action=boolean_action.BooleanAction,
      const=True,
      default=True,
      help=('restart instances automatically when files relevant to their '
            'module are changed'))
  misc_group.add_argument(
      '--dev_appserver_log_level', default='info',
      choices=_LOG_LEVEL_TO_PYTHON_CONSTANT.keys(),
      help='the log level below which logging messages generated by '
      'the development server will not be displayed on the console (this '
      'flag is more useful for diagnosing problems in dev_appserver.py rather '
      'than in application code)')
  misc_group.add_argument(
      '--skip_sdk_update_check',
      action=boolean_action.BooleanAction,
      const=True,
      default=False,
      help='skip checking for SDK updates (if false, use .appcfg_nag to '
      'decide)')
  misc_group.add_argument(
      '--default_gcs_bucket_name', default=None,
      help='default Google Cloud Storage bucket name')







  return parser

PARSER = create_command_line_parser()


def _clear_datastore_storage(datastore_path):
  """Delete the datastore storage file at the given path."""
  # lexists() returns True for broken symlinks, where exists() returns False.
  if os.path.lexists(datastore_path):
    try:
      os.remove(datastore_path)
    except OSError, e:
      logging.warning('Failed to remove datastore file %r: %s',
                      datastore_path,
                      e)


def _clear_prospective_search_storage(prospective_search_path):
  """Delete the perspective search storage file at the given path."""
  # lexists() returns True for broken symlinks, where exists() returns False.
  if os.path.lexists(prospective_search_path):
    try:
      os.remove(prospective_search_path)
    except OSError, e:
      logging.warning('Failed to remove prospective search file %r: %s',
                      prospective_search_path,
                      e)


def _clear_search_indexes_storage(search_index_path):
  """Delete the search indexes storage file at the given path."""
  # lexists() returns True for broken symlinks, where exists() returns False.
  if os.path.lexists(search_index_path):
    try:
      os.remove(search_index_path)
    except OSError, e:
      logging.warning('Failed to remove search indexes file %r: %s',
                      search_index_path,
                      e)


def _setup_environ(app_id):
  """Sets up the os.environ dictionary for the front-end server and API server.

  This function should only be called once.

  Args:
    app_id: The id of the application.
  """
  os.environ['APPLICATION_ID'] = app_id


class DevelopmentServer(object):
  """Encapsulates the logic for the development server.

  Only a single instance of the class may be created per process. See
  _setup_environ.
  """

  def __init__(self):
    # A list of servers that are currently running.
    self._running_modules = []
    self._module_to_port = {}
    self._dispatcher = None

  def module_to_address(self, module_name, instance=None):
    """Returns the address of a module."""



    if module_name is None:
      return self._dispatcher.dispatch_address
    return self._dispatcher.get_hostname(
        module_name,
        self._dispatcher.get_default_version(module_name),
        instance)

  def start(self, options):
    """Start devappserver2 servers based on the provided command line arguments.

    Args:
      options: An argparse.Namespace containing the command line arguments.
    """
    logging.getLogger().setLevel(
        _LOG_LEVEL_TO_PYTHON_CONSTANT[options.dev_appserver_log_level])

    configuration = application_configuration.ApplicationConfiguration(
        options.config_paths, options.app_id)

    if options.enable_cloud_datastore:
      # This requires the oauth server stub to return that the logged in user
      # is in fact an admin.
      os.environ['OAUTH_IS_ADMIN'] = '1'
      gcd_module = application_configuration.ModuleConfiguration(
          gcd_application.generate_gcd_app(configuration.app_id.split('~')[1]))
      configuration.modules.append(gcd_module)

    if options.skip_sdk_update_check:
      logging.info('Skipping SDK update check.')
    else:
      update_checker.check_for_updates(configuration)

    # There is no good way to set the default encoding from application code
    # (it needs to be done during interpreter initialization in site.py or
    # sitecustomize.py) so just warn developers if they have a different
    # encoding than production.
    if sys.getdefaultencoding() != _PROD_DEFAULT_ENCODING:
      logging.warning(
          'The default encoding of your local Python interpreter is set to %r '
          'while App Engine\'s production environment uses %r; as a result '
          'your code may behave differently when deployed.',
          sys.getdefaultencoding(), _PROD_DEFAULT_ENCODING)

    if options.port == 0:
      logging.warn('DEFAULT_VERSION_HOSTNAME will not be set correctly with '
                   '--port=0')

    _setup_environ(configuration.app_id)

    self._dispatcher = dispatcher.Dispatcher(
        configuration,
        options.host,
        options.port,
        options.auth_domain,
        _LOG_LEVEL_TO_RUNTIME_CONSTANT[options.log_level],
        self._create_php_config(options),
        self._create_python_config(options),
        self._create_java_config(options),
        self._create_custom_config(options),
        self._create_cloud_sql_config(options),
        self._create_vm_config(options),
        self._create_module_to_setting(options.max_module_instances,
                                       configuration, '--max_module_instances'),
        options.use_mtime_file_watcher,
        options.automatic_restart,
        options.allow_skipped_files,
        self._create_module_to_setting(options.threadsafe_override,
                                       configuration, '--threadsafe_override'),
        options.external_port)

    request_data = wsgi_request_info.WSGIRequestInfo(self._dispatcher)
    storage_path = _get_storage_path(options.storage_path, configuration.app_id)

    # TODO: Remove after the Files API is really gone.
    api_server.set_filesapi_enabled(options.blobstore_enable_files_api)
    if options.blobstore_warn_on_files_api_use:
      api_server.enable_filesapi_tracking(request_data)

    apis = self._create_api_server(
        request_data, storage_path, options, configuration)
    apis.start()
    self._running_modules.append(apis)

    self._dispatcher.start(options.api_host, apis.port, request_data)

    xsrf_path = os.path.join(storage_path, 'xsrf')
    admin = admin_server.AdminServer(options.admin_host, options.admin_port,
                                     self._dispatcher, configuration, xsrf_path)
    admin.start()
    self._running_modules.append(admin)
    try:
      default = self._dispatcher.get_module_by_name('default')
      apis.set_balanced_address(default.balanced_address)
    except request_info.ModuleDoesNotExistError:
      logging.warning('No default module found. Ignoring.')

  def stop(self):
    """Stops all running devappserver2 modules."""
    while self._running_modules:
      self._running_modules.pop().quit()
    if self._dispatcher:
      self._dispatcher.quit()

  @staticmethod
  def _create_api_server(request_data, storage_path, options, configuration):
    datastore_path = options.datastore_path or os.path.join(storage_path,
                                                            'datastore.db')
    logs_path = options.logs_path or os.path.join(storage_path, 'logs.db')

    search_index_path = options.search_indexes_path or os.path.join(
        storage_path, 'search_indexes')

    prospective_search_path = options.prospective_search_path or os.path.join(
        storage_path, 'prospective-search')

    blobstore_path = options.blobstore_path or os.path.join(storage_path,
                                                            'blobs')

    if options.clear_datastore:
      _clear_datastore_storage(datastore_path)

    if options.clear_prospective_search:
      _clear_prospective_search_storage(prospective_search_path)

    if options.clear_search_indexes:
      _clear_search_indexes_storage(search_index_path)

    if options.auto_id_policy==datastore_stub_util.SEQUENTIAL:
      logging.warn("--auto_id_policy='sequential' is deprecated. This option "
                   "will be removed in a future release.")

    application_address = '%s' % options.host
    if options.port and options.port != 80:
      application_address += ':' + str(options.port)

    user_login_url = '/%s?%s=%%s' % (login.LOGIN_URL_RELATIVE,
                                     login.CONTINUE_PARAM)
    user_logout_url = '%s&%s=%s' % (user_login_url, login.ACTION_PARAM,
                                    login.LOGOUT_ACTION)

    if options.datastore_consistency_policy == 'time':
      consistency = datastore_stub_util.TimeBasedHRConsistencyPolicy()
    elif options.datastore_consistency_policy == 'random':
      consistency = datastore_stub_util.PseudoRandomHRConsistencyPolicy()
    elif options.datastore_consistency_policy == 'consistent':
      consistency = datastore_stub_util.PseudoRandomHRConsistencyPolicy(1.0)
    else:
      assert 0, ('unknown consistency policy: %r' %
                 options.datastore_consistency_policy)

    api_server.maybe_convert_datastore_file_stub_data_to_sqlite(
        configuration.app_id, datastore_path)
    api_server.setup_stubs(
        request_data=request_data,
        app_id=configuration.app_id,
        application_root=configuration.modules[0].application_root,
        # The "trusted" flag is only relevant for Google administrative
        # applications.
        trusted=getattr(options, 'trusted', False),
        appidentity_email_address=options.appidentity_email_address,
        appidentity_private_key_path=os.path.abspath(
            options.appidentity_private_key_path)
        if options.appidentity_private_key_path else None,
        blobstore_path=blobstore_path,
        datastore_path=datastore_path,
        datastore_consistency=consistency,
        datastore_require_indexes=options.require_indexes,
        datastore_auto_id_policy=options.auto_id_policy,
        images_host_prefix='http://%s' % application_address,
        logs_path=logs_path,
        mail_smtp_host=options.smtp_host,
        mail_smtp_port=options.smtp_port,
        mail_smtp_user=options.smtp_user,
        mail_smtp_password=options.smtp_password,
        mail_enable_sendmail=options.enable_sendmail,
        mail_show_mail_body=options.show_mail_body,
        mail_allow_tls=options.smtp_allow_tls,
        matcher_prospective_search_path=prospective_search_path,
        search_index_path=search_index_path,
        taskqueue_auto_run_tasks=options.enable_task_running,
        taskqueue_default_http_server=application_address,
        user_login_url=user_login_url,
        user_logout_url=user_logout_url,
        default_gcs_bucket_name=options.default_gcs_bucket_name,
        appidentity_oauth_url=options.appidentity_oauth_url)

    return api_server.APIServer(options.api_host, options.api_port,
                                configuration.app_id)

  @staticmethod
  def _create_php_config(options):
    php_config = runtime_config_pb2.PhpConfig()
    if options.php_executable_path:
      php_config.php_executable_path = os.path.abspath(
          options.php_executable_path)
    php_config.enable_debugger = options.php_remote_debugging
    if options.php_gae_extension_path:
      php_config.gae_extension_path = os.path.abspath(
          options.php_gae_extension_path)
    if options.php_xdebug_extension_path:
      php_config.xdebug_extension_path = os.path.abspath(
          options.php_xdebug_extension_path)

    return php_config

  @staticmethod
  def _create_python_config(options):
    python_config = runtime_config_pb2.PythonConfig()
    if options.python_startup_script:
      python_config.startup_script = os.path.abspath(
          options.python_startup_script)
      if options.python_startup_args:
        python_config.startup_args = options.python_startup_args
    return python_config

  @staticmethod
  def _create_java_config(options):
    java_config = runtime_config_pb2.JavaConfig()
    if options.jvm_flag:
      java_config.jvm_args.extend(options.jvm_flag)
    return java_config

  @staticmethod
  def _create_custom_config(options):
    custom_config = runtime_config_pb2.CustomConfig()
    custom_config.custom_entrypoint = options.custom_entrypoint
    custom_config.runtime = options.runtime
    return custom_config

  @staticmethod
  def _create_cloud_sql_config(options):
    cloud_sql_config = runtime_config_pb2.CloudSQL()
    cloud_sql_config.mysql_host = options.mysql_host
    cloud_sql_config.mysql_port = options.mysql_port
    cloud_sql_config.mysql_user = options.mysql_user
    cloud_sql_config.mysql_password = options.mysql_password
    if options.mysql_socket:
      cloud_sql_config.mysql_socket = options.mysql_socket
    return cloud_sql_config

  @staticmethod
  def _create_vm_config(options):
    vm_config = runtime_config_pb2.VMConfig()
    vm_config.enable_logs = options.enable_mvm_logs
    return vm_config

  @staticmethod
  def _create_module_to_setting(setting, configuration, option):
    """Create a per-module dictionary configuration.

    Creates a dictionary that maps a module name to a configuration
    setting. Used in conjunction with parse_per_module_option.

    Args:
      setting: a value that can be None, a dict of str->type or a single value.
      configuration: an ApplicationConfiguration object.
      option: the option name the setting came from.

    Returns:
      A dict of str->type.
    """
    if setting is None:
      return {}

    module_names = [module_configuration.module_name
                    for module_configuration in configuration.modules]
    if isinstance(setting, dict):
      # Warn and remove a setting if the module name is unknown.
      module_to_setting = {}
      for module_name, value in setting.items():
        if module_name in module_names:
          module_to_setting[module_name] = value
        else:
          logging.warning('Unknown module %r for %r', module_name, option)
      return module_to_setting

    # Create a dict with an entry for every module.
    return {module_name: setting for module_name in module_names}


def main():
  shutdown.install_signal_handlers()
  # The timezone must be set in the devappserver2 process rather than just in
  # the runtime so printed log timestamps are consistent and the taskqueue stub
  # expects the timezone to be UTC. The runtime inherits the environment.
  os.environ['TZ'] = 'UTC'
  if hasattr(time, 'tzset'):
    # time.tzet() should be called on Unix, but doesn't exist on Windows.
    time.tzset()
  options = PARSER.parse_args()
  dev_server = DevelopmentServer()
  try:
    dev_server.start(options)
    shutdown.wait_until_shutdown()
  finally:
    dev_server.stop()


if __name__ == '__main__':
  main()
