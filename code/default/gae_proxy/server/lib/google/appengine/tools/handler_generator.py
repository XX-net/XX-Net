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
"""Contains logic for writing handlers to app.yaml.

Information about handlers comes from static file paths, appengine-web.xml,
and web.xml. This information is packaged into Handler objects which specify
paths and properties about how they are handled.

In this module:
  GenerateYamlHandlers: Returns Yaml string with handlers.
  HandlerGenerator: Ancestor class for creating handler lists.
  DynamicHandlerGenerator: Creates handlers from web-xml servlet and filter
    mappings.
  StaticHandlerGenerator: Creates handlers from static file includes and
    static files.
"""

from google.appengine.api import appinfo
from google.appengine.tools import handler
from google.appengine.tools.app_engine_config_exception import AppEngineConfigException

API_ENDPOINT_REGEX = '/_ah/spi/*'


def GenerateYamlHandlersList(app_engine_web_xml, web_xml, static_files):
  """Produces a list of Yaml strings for dynamic and static handlers."""
  welcome_properties = _MakeWelcomeProperties(web_xml, static_files)
  static_handler_generator = StaticHandlerGenerator(
      app_engine_web_xml, web_xml, welcome_properties)
  dynamic_handler_generator = DynamicHandlerGenerator(
      app_engine_web_xml, web_xml)

  handler_length = len(dynamic_handler_generator.GenerateOrderedHandlerList())
  if static_files:
    handler_length += len(static_handler_generator.GenerateOrderedHandlerList())
  if handler_length > appinfo.MAX_URL_MAPS:




    dynamic_handler_generator.fall_through = True
    dynamic_handler_generator.welcome_properties = {}

  yaml_statements = ['handlers:']
  if static_files:
    yaml_statements += static_handler_generator.GetHandlerYaml()
  yaml_statements += dynamic_handler_generator.GetHandlerYaml()

  return yaml_statements


def GenerateYamlHandlersListForDevAppServer(
    app_engine_web_xml, web_xml, static_urls):
  r"""Produces a list of Yaml strings for dynamic and static handlers.

  This variant of GenerateYamlHandlersList is for the Dev App Server case.
  The key difference there is that we serve files directly from the war
  directory rather than constructing a parallel hierarchy with a special
  __static__ directory. Since app.yaml doesn't support excluding URL patterns
  and appengine-web.xml does, this means that we have to define patterns that
  cover exactly the set of static files we want without pulling in any files
  that are not supposed to be served as static files.

  Args:
    app_engine_web_xml: an app_engine_web_xml_parser.AppEngineWebXml object.
    web_xml: a web_xml_parser.WebXml object.
    static_urls: a list of two-item tuples where the first item is a URL pattern
      string for a static file, such as '/stylesheets/main\.css', and the
      second item is the app_engine_web_xml_parser.StaticFileInclude
      representing the <static-files><include> XML element that caused that URL
      pattern to be included in the list.

  Returns:
    A list of strings that together make up the lines of the generated app.yaml
    file.
  """







  appinfo.MAX_URL_MAPS = 10000
  static_handler_generator = StaticHandlerGeneratorForDevAppServer(
      app_engine_web_xml, web_xml, static_urls)
  dynamic_handler_generator = DynamicHandlerGenerator(
      app_engine_web_xml, web_xml)
  return (['handlers:'] +
          static_handler_generator.GetHandlerYaml() +
          dynamic_handler_generator.GetHandlerYaml())


def _MakeWelcomeProperties(web_xml, static_files):
  """Makes the welcome_properties dict given web_xml and the static files.

  Args:
    web_xml: a parsed web.xml that may contain a <welcome-file-list> clause.
    static_files: the list of all static files found in the app.

  Returns:
    A dict with a single entry where the key is 'welcome' and the value is
    either None or a tuple of the file names in all the <welcome-file> clauses
    that were retained.  A <welcome-file> clause is retained if its file name
    matches at least one actual file in static_files.

    For example, if the input looked like this:
      <welcome-file-list>
        <welcome-file>index.jsp</welcome-file>
        <welcome-file>index.html</welcome-file>
      </welcome-file-list>
    and if there was a file /foo/bar/index.html but no file called index.jsp
    anywhere in static_files, the result would be {'welcome': ('index.html',)}.
  """
  static_welcome_files = []
  for welcome_file in web_xml.welcome_files:
    if any(f.endswith('/' + welcome_file) for f in static_files):
      static_welcome_files.append(welcome_file)

  welcome_value = tuple(static_welcome_files) or None
  return {'welcome': welcome_value}


class HandlerGenerator(object):
  """Ancestor class for StaticHandlerGenerator and DynamicHandlerGenerator.

  Contains shared functionality. Both static and dynamic handler generators
  work in a similar way. Both obtain a list of patterns, static includes and
  web.xml servlet url patterns, respectively, add security constraint info to
  those lists, sort them, and then generate Yaml statements for each entry.
  """

  def __init__(self, app_engine_web_xml, web_xml):
    self.app_engine_web_xml = app_engine_web_xml
    self.web_xml = web_xml

  def GetHandlerYaml(self):
    handler_yaml = []
    for h in self.GenerateOrderedHandlerList():
      handler_yaml += self.TranslateHandler(h)
    return handler_yaml

  def GenerateSecurityConstraintHandlers(self):
    """Creates Handlers for security constraint information."""
    handler_list = []
    for constraint in self.web_xml.security_constraints:
      props = {'transport_guarantee': constraint.transport_guarantee,
               'required_role': constraint.required_role}
      for pattern in constraint.patterns:
        security_handler = handler.SimpleHandler(pattern, props)
        handler_list.append(security_handler)
        handler_list += self.CreateHandlerWithoutTrailingStar(security_handler)
    return handler_list

  def GenerateWelcomeFileHandlers(self):
    """Creates handlers for welcome files."""
    if not self.welcome_properties:
      return []



    return [handler.SimpleHandler('/', self.welcome_properties),
            handler.SimpleHandler('/*/', self.welcome_properties)]

  def TranslateAdditionalOptions(self, h):
    """Generates Yaml statements from security constraint information."""
    additional_statements = []

    required_role = h.GetProperty('required_role', default='none')
    required_role_translation = {'none': 'optional',
                                 '*': 'required',
                                 'admin': 'admin'}
    additional_statements.append(
        '  login: %s' % required_role_translation[required_role])

    transport_guarantee = h.GetProperty('transport_guarantee', default='none')

    if transport_guarantee == 'none':
      if self.app_engine_web_xml.ssl_enabled:
        additional_statements.append('  secure: optional')
      else:
        additional_statements.append('  secure: never')
    else:
      if self.app_engine_web_xml.ssl_enabled:
        additional_statements.append('  secure: always')
      else:
        raise AppEngineConfigException(
            'SSL must be enabled in appengine-web.xml to use '
            'transport-guarantee')

    handler_id = self.web_xml.pattern_to_id.get(h.pattern)
    if handler_id and handler_id in self.app_engine_web_xml.api_endpoints:
      additional_statements.append('  api_endpoint: True')
    return additional_statements

  def CreateHandlerWithoutTrailingStar(self, h):
    """Creates identical handler without trailing star in pattern.

    According to servlet spec, baz/* should match baz.

    Args:
      h: a Handler.
    Returns:
      If h.pattern is of form "baz/*", returns a singleton list with a
      SimpleHandler with pattern "baz" and the properties of h. Otherwise,
      returns an empty list.
    """
    if len(h.pattern) <= 2 or h.pattern[-2:] != '/*':
      return []
    return [handler.SimpleHandler(h.pattern[:-2], h.properties)]


class DynamicHandlerGenerator(HandlerGenerator):
  """Generates dynamic handler yaml entries for app.yaml."""

  def __init__(self, app_engine_web_xml, web_xml):
    super(DynamicHandlerGenerator, self).__init__(app_engine_web_xml, web_xml)
    if any([self.web_xml.fall_through_to_runtime,
            '/' in self.web_xml.patterns,
            '/*' in self.web_xml.patterns]):
      self.fall_through = True
      self.welcome_properties = {}
    else:
      self.fall_through = False
      self.welcome_properties = {'type': 'dynamic'}

    self.has_api_endpoint = API_ENDPOINT_REGEX in self.web_xml.patterns
    self.patterns = [pattern for pattern in self.web_xml.patterns if
                     pattern not in ('/', '/*', API_ENDPOINT_REGEX)]
    self.has_jsps = web_xml.has_jsps

  def MakeServletPatternsIntoHandlers(self):
    """Creates SimpleHandlers from servlet and filter mappings in web.xml."""
    handler_patterns = []
    has_jsps = self.has_jsps
    if self.fall_through:
      return [handler.SimpleHandler('/*', {'type': 'dynamic'})]

    for pattern in self.patterns:
      if pattern.endswith('.jsp'):
        has_jsps = True
      else:
        new_handler = handler.SimpleHandler(pattern, {'type': 'dynamic'})
        handler_patterns.append(new_handler)
        handler_patterns += self.CreateHandlerWithoutTrailingStar(new_handler)

    if has_jsps or self.app_engine_web_xml.vm:
      handler_patterns.append(
          handler.SimpleHandler('*.jsp', {'type': 'dynamic'}))

    handler_patterns.append(
        handler.SimpleHandler('/_ah/*', {'type': 'dynamic'}))
    return handler_patterns

  def GenerateOrderedHandlerList(self):
    handler_patterns = (self.MakeServletPatternsIntoHandlers()
                        + self.GenerateSecurityConstraintHandlers()
                        + self.GenerateWelcomeFileHandlers())
    ordered_handlers = handler.GetOrderedIntersection(handler_patterns)
    if self.has_api_endpoint:
      ordered_handlers.append(
          handler.SimpleHandler(API_ENDPOINT_REGEX, {'type': 'dynamic'}))
    return ordered_handlers

  def TranslateHandler(self, the_handler):
    """Converts a dynamic handler object to Yaml."""
    if the_handler.GetProperty('type') != 'dynamic':
      return []
    statements = ['- url: %s' % the_handler.Regexify(),
                  '  script: unused']
    return statements + self.TranslateAdditionalOptions(the_handler)


class StaticHandlerGenerator(HandlerGenerator):
  """Generates static handler yaml entries for app.yaml."""

  def __init__(self, app_engine_web_xml, web_xml, welcome_properties):
    super(StaticHandlerGenerator, self).__init__(app_engine_web_xml, web_xml)
    self.static_file_includes = self.app_engine_web_xml.static_file_includes
    self.welcome_properties = welcome_properties

  def MakeStaticFilePatternsIntoHandlers(self):
    """Creates SimpleHandlers out of XML-specified static file includes."""
    includes = self.static_file_includes
    if not includes:
      return [handler.SimpleHandler('/*', {'type': 'static'})]

    handler_patterns = []

    for include in includes:
      pattern = include.pattern.replace('**', '*')
      if pattern[0] != '/':
        pattern = '/' + pattern
      properties = {'type': 'static'}
      if include.expiration:
        properties['expiration'] = include.expiration
      if include.http_headers:

        properties['http_headers'] = tuple(sorted(include.http_headers.items()))
      handler_patterns.append(handler.SimpleHandler(pattern, properties))
    return handler_patterns

  def GenerateOrderedHandlerList(self):
    handler_patterns = (self.MakeStaticFilePatternsIntoHandlers()
                        + self.GenerateSecurityConstraintHandlers()
                        + self.GenerateWelcomeFileHandlers())
    return handler.GetOrderedIntersection(handler_patterns)

  def TranslateHandler(self, h):
    """Translates SimpleHandler to static handler yaml statements."""
    root = self.app_engine_web_xml.public_root
    regex_string = h.Regexify()
    if regex_string.startswith(root):
      regex_string = regex_string[len(root):]

    welcome_files = h.GetProperty('welcome')

    if welcome_files:
      statements = []
      for welcome_file in welcome_files:
        statements += ['- url: (%s)' % regex_string,
                       '  static_files: __static__%s\\1%s' %
                       (root, welcome_file),
                       '  upload: __NOT_USED__',
                       '  require_matching_file: True']
        statements += self.TranslateAdditionalOptions(h)
        statements += self.TranslateAdditionalStaticOptions(h)
      return statements

    if h.GetProperty('type') != 'static':
      return []

    statements = ['- url: (%s)' % regex_string,
                  '  static_files: __static__%s\\1' % root,
                  '  upload: __NOT_USED__',
                  '  require_matching_file: True']

    return (statements +
            self.TranslateAdditionalOptions(h) +
            self.TranslateAdditionalStaticOptions(h))

  def TranslateAdditionalStaticOptions(self, h):
    statements = []
    expiration = h.GetProperty('expiration')
    if expiration:
      statements.append('  expiration: %s' % expiration)
    http_headers = h.GetProperty('http_headers')
    if http_headers:
      statements.append('  http_headers:')
      statements += ['    %s: %s' % pair for pair in http_headers]
    return statements


class StaticHandlerGeneratorForDevAppServer(StaticHandlerGenerator):
  """Generates static handler yaml entries for app.yaml in Dev App Server.

  This class overrides the GenerateOrderedHanderList and TranslateHandler
  methods from its parent to work with the Dev App Server environment.
  See the GenerateYamlHandlersListForDevAppServer method above for further
  details.
  """

  def __init__(self, app_engine_web_xml, web_xml, static_urls):
    super(StaticHandlerGeneratorForDevAppServer, self).__init__(
        app_engine_web_xml, web_xml, {})
    self.static_urls = static_urls

  def GenerateOrderedHandlerList(self):
    handler_patterns = self.MakeStaticUrlsIntoHandlers()




    return handler.GetOrderedIntersection(handler_patterns)

  def MakeStaticUrlsIntoHandlers(self):
    handler_patterns = []
    for url, include in self.static_urls:
      properties = {'type': 'static'}
      if include.expiration:
        properties['expiration'] = include.expiration
      if include.http_headers:
        properties['http_headers'] = tuple(sorted(include.http_headers.items()))
      handler_patterns.append(handler.SimpleHandler(url, properties))
    return handler_patterns

  def TranslateHandler(self, h):
    """Translates SimpleHandler to static handler yaml statements."""

    root = self.app_engine_web_xml.public_root


    regex = h.Regexify()



    split = 1 if regex.startswith('/') else 0

    statements = ['- url: /(%s)' % regex[split:],
                  '  static_files: %s\\1' % root,
                  '  upload: __NOT_USED__',
                  '  require_matching_file: True']

    return (statements +
            self.TranslateAdditionalOptions(h) +
            self.TranslateAdditionalStaticOptions(h))
