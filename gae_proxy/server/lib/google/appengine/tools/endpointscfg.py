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

"""External script for generating Cloud Endpoints related files.

The gen_discovery_doc subcommand takes a list of fully qualified ProtoRPC
service names and calls a cloud service which generates a discovery document in
REST or RPC style.

Example:
  endpointscfg.py gen_discovery_doc -o . -f rest postservice.GreetingsV1

The gen_client_lib subcommand takes a discovery document and calls a cloud
service to generate a client library for a target language (currently just Java)

Example:
  endpointscfg.py gen_client_lib java -o . greetings-v0.1.discovery

The get_client_lib subcommand does both of the above commands at once.

Example:
  endpointscfg.py get_client_lib java -o . postservice.GreetingsV1

The gen_api_config command outputs an .api configuration file for a service.

Example:
  endpointscfg.py gen_api_config -o . -a /path/to/app \
    --hostname myhost.appspot.com postservice.GreetingsV1
"""

from __future__ import with_statement



import argparse
import collections
import contextlib

try:
  import json
except ImportError:


  import simplejson as json
import os
import re
import sys
import urllib
import urllib2

from endpoints import api_config
from protorpc import remote
import yaml

from google.appengine.tools.devappserver2 import api_server



DISCOVERY_DOC_BASE = ('https://webapis-discovery.appspot.com/_ah/api/'
                      'discovery/v1/apis/generate/')
CLIENT_LIBRARY_BASE = 'https://google-api-client-libraries.appspot.com/generate'
_VISIBLE_COMMANDS = ('get_client_lib', 'get_discovery_doc')


class ServerRequestException(Exception):
  """Exception for problems with the request to a server."""

  def __init__(self, http_error):
    """Create a ServerRequestException from a given urllib2.HTTPError.

    Args:
      http_error: The HTTPError that the ServerRequestException will be
        based on.
    """
    error_details = None
    error_response = None
    if http_error.fp:
      try:
        error_response = http_error.fp.read()
        error_body = json.loads(error_response)
        error_details = ['%s: %s' % (detail['message'], detail['debug_info'])
                         for detail in error_body['error']['errors']]
      except (ValueError, TypeError, KeyError):
        pass
    if error_details:
      error_details_str = ', '.join(error_details)
      error_message = ('HTTP %s (%s) error when communicating with URL: %s.  '
                       'Details: %s' % (http_error.code, http_error.reason,
                                        http_error.filename, error_details_str))
    else:
      error_message = ('HTTP %s (%s) error when communicating with URL: %s. '
                       'Response: %s' % (http_error.code, http_error.reason,
                                         http_error.filename,
                                         error_response))
    super(ServerRequestException, self).__init__(error_message)


class _EndpointsParser(argparse.ArgumentParser):
  """Create a subclass of argparse.ArgumentParser for Endpoints."""

  def error(self, message):
    """Override superclass to support customized error message.

    Error message needs to be rewritten in order to display visible commands
    only, when invalid command is called by user. Otherwise, hidden commands
    will be displayed in stderr, which is not expected.

    Refer the following argparse python documentation for detailed method
    information:
      http://docs.python.org/2/library/argparse.html#exiting-methods

    Args:
      message: original error message that will be printed to stderr
    """




    subcommands_quoted = ', '.join(
        [repr(command) for command in _VISIBLE_COMMANDS])
    subcommands = ', '.join(_VISIBLE_COMMANDS)
    message = re.sub(
        r'(argument {%s}: invalid choice: .*) \(choose from (.*)\)$'
        % subcommands, r'\1 (choose from %s)' % subcommands_quoted, message)
    super(_EndpointsParser, self).error(message)


def _WriteFile(output_path, name, content):
  """Write given content to a file in a given directory.

  Args:
    output_path: The directory to store the file in.
    name: The name of the file to store the content in.
    content: The content to write to the file.close

  Returns:
    The full path to the written file.
  """
  path = os.path.join(output_path, name)
  with open(path, 'wb') as f:
    f.write(content)
  return path


def GenApiConfig(service_class_names, config_string_generator=None,
                 hostname=None, application_path=None):
  """Write an API configuration for endpoints annotated ProtoRPC services.

  Args:
    service_class_names: A list of fully qualified ProtoRPC service classes.
    config_string_generator: A generator object that produces API config strings
      using its pretty_print_config_to_json method.
    hostname: A string hostname which will be used as the default version
      hostname. If no hostname is specificied in the @endpoints.api decorator,
      this value is the fallback.
    application_path: A string with the path to the AppEngine application.

  Raises:
    TypeError: If any service classes don't inherit from remote.Service.
    messages.DefinitionNotFoundError: If a service can't be found.

  Returns:
    A map from service names to a string containing the API configuration of the
      service in JSON format.
  """




  api_service_map = collections.OrderedDict()
  for service_class_name in service_class_names:
    module_name, base_service_class_name = service_class_name.rsplit('.', 1)
    module = __import__(module_name, fromlist=base_service_class_name)
    service = getattr(module, base_service_class_name)
    if not isinstance(service, type) or not issubclass(service, remote.Service):
      raise TypeError('%s is not a ProtoRPC service' % service_class_name)

    services = api_service_map.setdefault(
        (service.api_info.name, service.api_info.version), [])
    services.append(service)



  app_yaml_hostname = _GetAppYamlHostname(application_path)

  service_map = collections.OrderedDict()
  config_string_generator = (
      config_string_generator or api_config.ApiConfigGenerator())
  for api_info, services in api_service_map.iteritems():
    assert len(services) > 0, 'An API must have at least one ProtoRPC service'


    hostname = services[0].api_info.hostname or hostname or app_yaml_hostname


    service_map['%s-%s' % api_info] = (
        config_string_generator.pretty_print_config_to_json(
            services, hostname=hostname))

  return service_map


def _GetAppYamlHostname(application_path, open_func=open):
  """Build the hostname for this app based on the name in app.yaml.

  Args:
    application_path: A string with the path to the AppEngine application.  This
      should be the directory containing the app.yaml file.
    open_func: Function to call to open a file.  Used to override the default
      open function in unit tests.

  Returns:
    A hostname, usually in the form of "myapp.appspot.com", based on the
    application name in the app.yaml file.  If the file can't be found or
    there's a problem building the name, this will return None.
  """
  try:
    app_yaml_file = open_func(os.path.join(application_path or '.', 'app.yaml'))
    config = yaml.safe_load(app_yaml_file.read())
  except IOError:

    return None

  application = config.get('application')
  if not application:
    return None

  if ':' in application:

    return None


  tilde_index = application.rfind('~')
  if tilde_index >= 0:
    application = application[tilde_index + 1:]
    if not application:
      return None

  return '%s.appspot.com' % application


def _FetchDiscoveryDoc(config, doc_format):
  """Fetch discovery documents generated from a cloud service.

  Args:
    config: An API config.
    doc_format: The requested format for the discovery doc. (rest|rpc)

  Raises:
    ServerRequestException: If fetching the generated discovery doc fails.

  Returns:
    A list of discovery doc strings.
  """
  body = json.dumps({'config': config}, indent=2, sort_keys=True)
  request = urllib2.Request(DISCOVERY_DOC_BASE + doc_format, body)
  request.add_header('content-type', 'application/json')

  try:
    with contextlib.closing(urllib2.urlopen(request)) as response:
      return response.read()
  except urllib2.HTTPError, error:
    raise ServerRequestException(error)


def _GenDiscoveryDoc(service_class_names, doc_format,
                     output_path, hostname=None,
                     application_path=None):
  """Write discovery documents generated from a cloud service to file.

  Args:
    service_class_names: A list of fully qualified ProtoRPC service names.
    doc_format: The requested format for the discovery doc. (rest|rpc)
    output_path: The directory to output the discovery docs to.
    hostname: A string hostname which will be used as the default version
      hostname. If no hostname is specificied in the @endpoints.api decorator,
      this value is the fallback. Defaults to None.
    application_path: A string containing the path to the AppEngine app.

  Raises:
    ServerRequestException: If fetching the generated discovery doc fails.

  Returns:
    A list of discovery doc filenames.
  """
  output_files = []
  service_configs = GenApiConfig(service_class_names, hostname=hostname,
                                 application_path=application_path)
  for api_name_version, config in service_configs.iteritems():
    discovery_doc = _FetchDiscoveryDoc(config, doc_format)
    discovery_name = api_name_version + '.discovery'
    output_files.append(_WriteFile(output_path, discovery_name, discovery_doc))

  return output_files


def _GenClientLib(discovery_path, language, output_path, build_system):
  """Write a client library from a discovery doc, using a cloud service to file.

  Args:
    discovery_path: Path to the discovery doc used to generate the client
      library.
    language: The client library language to generate. (java)
    output_path: The directory to output the client library zip to.
    build_system: The target build system for the client library language.

  Raises:
    IOError: If reading the discovery doc fails.
    ServerRequestException: If fetching the generated client library fails.

  Returns:
    The path to the zipped client library.
  """
  with open(discovery_path) as f:
    discovery_doc = f.read()

  client_name = re.sub(r'\.discovery$', '.zip',
                       os.path.basename(discovery_path))

  return _GenClientLibFromContents(discovery_doc, language, output_path,
                                   build_system, client_name)


def _GenClientLibFromContents(discovery_doc, language, output_path,
                              build_system, client_name):
  """Write a client library from a discovery doc, using a cloud service to file.

  Args:
    discovery_doc: A string, the contents of the discovery doc used to
      generate the client library.
    language: A string, the client library language to generate. (java)
    output_path: A string, the directory to output the client library zip to.
    build_system: A string, the target build system for the client language.
    client_name: A string, the filename used to save the client lib.

  Raises:
    IOError: If reading the discovery doc fails.
    ServerRequestException: If fetching the generated client library fails.

  Returns:
    The path to the zipped client library.
  """

  body = urllib.urlencode({'lang': language, 'content': discovery_doc,
                           'layout': build_system})
  request = urllib2.Request(CLIENT_LIBRARY_BASE, body)
  try:
    with contextlib.closing(urllib2.urlopen(request)) as response:
      content = response.read()
      return _WriteFile(output_path, client_name, content)
  except urllib2.HTTPError, error:
    raise ServerRequestException(error)


def _GetClientLib(service_class_names, language, output_path, build_system,
                  hostname=None, application_path=None):
  """Fetch client libraries from a cloud service.

  Args:
    service_class_names: A list of fully qualified ProtoRPC service names.
    language: The client library language to generate. (java)
    output_path: The directory to output the discovery docs to.
    build_system: The target build system for the client library language.
    hostname: A string hostname which will be used as the default version
      hostname. If no hostname is specificied in the @endpoints.api decorator,
      this value is the fallback. Defaults to None.
    application_path: A string containing the path to the AppEngine app.

  Returns:
    A list of paths to client libraries.
  """
  client_libs = []
  service_configs = GenApiConfig(service_class_names, hostname=hostname,
                                 application_path=application_path)
  for api_name_version, config in service_configs.iteritems():
    discovery_doc = _FetchDiscoveryDoc(config, 'rest')
    client_name = api_name_version + '.zip'
    client_libs.append(
        _GenClientLibFromContents(discovery_doc, language, output_path,
                                  build_system, client_name))
  return client_libs


def _GenApiConfigCallback(args, api_func=GenApiConfig):
  """Generate an api file.

  Args:
    args: An argparse.Namespace object to extract parameters from.
    api_func: A function that generates and returns an API configuration
      for a list of services.
  """
  service_configs = api_func(args.service,
                             hostname=args.hostname,
                             application_path=args.application)

  for api_name_version, config in service_configs.iteritems():
    _WriteFile(args.output, api_name_version + '.api', config)


def _GetClientLibCallback(args, client_func=_GetClientLib):
  """Generate discovery docs and client libraries to files.

  Args:
    args: An argparse.Namespace object to extract parameters from.
    client_func: A function that generates client libraries and stores them to
      files, accepting a list of service names, a client library language,
      an output directory, a build system for the client library language, and
      a hostname.
  """
  client_paths = client_func(
      args.service, args.language, args.output, args.build_system,
      hostname=args.hostname, application_path=args.application)

  for client_path in client_paths:
    print 'API client library written to %s' % client_path


def _GenDiscoveryDocCallback(args, discovery_func=_GenDiscoveryDoc):
  """Generate discovery docs to files.

  Args:
    args: An argparse.Namespace object to extract parameters from
    discovery_func: A function that generates discovery docs and stores them to
      files, accepting a list of service names, a discovery doc format, and an
      output directory.
  """
  discovery_paths = discovery_func(args.service, args.format,
                                   args.output, hostname=args.hostname,
                                   application_path=args.application)
  for discovery_path in discovery_paths:
    print 'API discovery document written to %s' % discovery_path


def _GenClientLibCallback(args, client_func=_GenClientLib):
  """Generate a client library to file.

  Args:
    args: An argparse.Namespace object to extract parameters from
    client_func: A function that generates client libraries and stores them to
      files, accepting a path to a discovery doc, a client library language, an
      output directory, and a build system for the client library language.
  """
  client_path = client_func(args.discovery_doc[0], args.language, args.output,
                            args.build_system)
  print 'API client library written to %s' % client_path


def MakeParser(prog):
  """Create an argument parser.

  Args:
    prog: The name of the program to use when outputting help text.

  Returns:
    An argparse.ArgumentParser built to specification.
  """

  def AddStandardOptions(parser, *args):
    """Add common endpoints options to a parser.

    Args:
      parser: The parser to add options to.
      *args: A list of option names to add. Possible names are: application,
        format, output, language, service, and discovery_doc.
    """
    if 'application' in args:
      parser.add_argument('-a', '--application', default='.',
                          help='The path to the Python App Engine App')
    if 'format' in args:
      parser.add_argument('-f', '--format', default='rest',
                          choices=['rest', 'rpc'],
                          help='The requested API protocol type')
    if 'hostname' in args:
      help_text = ('Default application hostname, if none is specified '
                   'for API service.')
      parser.add_argument('--hostname', help=help_text)
    if 'output' in args:
      parser.add_argument('-o', '--output', default='.',
                          help='The directory to store output files')
    if 'language' in args:
      parser.add_argument('language',
                          help='The target output programming language')
    if 'service' in args:
      parser.add_argument('service', nargs='+',
                          help='Fully qualified service class name')
    if 'discovery_doc' in args:
      parser.add_argument('discovery_doc', nargs=1,
                          help='Path to the discovery document')
    if 'build_system' in args:
      parser.add_argument('-bs', '--build_system', default='default',
                          help='The target build system')

  parser = _EndpointsParser(prog=prog)
  subparsers = parser.add_subparsers(
      title='subcommands', metavar='{%s}' % ', '.join(_VISIBLE_COMMANDS))

  get_client_lib = subparsers.add_parser(
      'get_client_lib', help=('Generates discovery documents and client '
                              'libraries from service classes'))
  get_client_lib.set_defaults(callback=_GetClientLibCallback)
  AddStandardOptions(get_client_lib, 'application', 'hostname', 'output',
                     'language', 'service', 'build_system')

  get_discovery_doc = subparsers.add_parser(
      'get_discovery_doc',
      help='Generates discovery documents from service classes')
  get_discovery_doc.set_defaults(callback=_GenDiscoveryDocCallback)
  AddStandardOptions(get_discovery_doc, 'application', 'format', 'hostname',
                     'output', 'service')



  gen_api_config = subparsers.add_parser('gen_api_config')
  gen_api_config.set_defaults(callback=_GenApiConfigCallback)
  AddStandardOptions(gen_api_config, 'application', 'hostname', 'output',
                     'service')

  gen_discovery_doc = subparsers.add_parser('gen_discovery_doc')
  gen_discovery_doc.set_defaults(callback=_GenDiscoveryDocCallback)
  AddStandardOptions(gen_discovery_doc, 'application', 'format', 'hostname',
                     'output', 'service')

  gen_client_lib = subparsers.add_parser('gen_client_lib')
  gen_client_lib.set_defaults(callback=_GenClientLibCallback)
  AddStandardOptions(gen_client_lib, 'output', 'language', 'discovery_doc',
                     'build_system')

  return parser


def main(argv):
  api_server.test_setup_stubs(app_id='_')

  parser = MakeParser(argv[0])
  args = parser.parse_args(argv[1:])



  application_path = getattr(args, 'application', None)
  if application_path is not None:
    sys.path.insert(0, os.path.abspath(application_path))

  args.callback(args)


if __name__ == '__main__':
  main(sys.argv)
