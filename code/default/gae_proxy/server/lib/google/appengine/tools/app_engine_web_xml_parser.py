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
"""Directly processes text of appengine-web.xml.

AppEngineWebXmlParser is called with XML string to produce an AppEngineWebXml
object containing the data from that string.

AppEngineWebXmlParser: converts xml to AppEngineWebXml object
AppEngineWebXml: Contains relevant information from app_engine_web.xml

Dummy Classes:
ManualScaling
BasicScaling
UserPermission
AdminConsolePage
ErrorHandler
ApiConfig
PrioritySpecifierEntry
StaticFileInclude
AppEngineConfigException - generically reports illegal inputs.

"""

import os
import re
from xml.etree import ElementTree

from google.appengine.tools import xml_parser_utils
from google.appengine.tools.app_engine_config_exception import AppEngineConfigException
from google.appengine.tools.value_mixin import ValueMixin


class AppEngineWebXmlParser(object):
  """Provides logic for walking down XML tree and pulling data."""

  def ProcessXml(self, xml_str):
    """Parses XML string and returns object representation of relevant info.

    Uses ElementTree parser to return a tree representation of XML.
    Then walks down that tree and extracts important info and adds it
    to the object.

    Args:
      xml_str: The XML string itself

    Returns:
      If there is well-formed but illegal XML, returns a list of
      errors. Otherwise, returns an AppEngineWebXml object containing
      information from XML.

    Raises:
      AppEngineConfigException: In case of malformed XML or illegal inputs.
    """
    try:
      self.app_engine_web_xml = AppEngineWebXml()
      self.errors = []
      xml_root = ElementTree.fromstring(xml_str)

      for child in xml_root.getchildren():
        self.ProcessChildNode(child)
      self.CheckScalingConstraints()
      if self.errors:

        raise AppEngineConfigException('\n'.join(self.errors))
      return self.app_engine_web_xml
    except ElementTree.ParseError as e:
      raise AppEngineConfigException('Bad input -- not valid XML: %s' % e)

  def ProcessChildNode(self, child_node):
    """Processes second-level nodes one by one.

    According to the tag of the node passed in, processes it a certain way.

    Args:
      child_node: a "second-level" node in the appengine-web.xml tree

    Raises:
      AppEngineConfigException - in case tag is not recognized.
    """

    element_name = xml_parser_utils.GetTag(child_node)
    camel_case_name = ''.join(part.title() for part in element_name.split('-'))
    method_name = 'Process%sNode' % camel_case_name
    if hasattr(self, method_name) and method_name is not 'ProcessChildNode':
      getattr(self, method_name)(child_node)
    else:
      self.errors.append('Second-level tag not recognized: <%s>' % element_name)

  def ProcessSystemPropertiesNode(self, node):
    for sub_node in xml_parser_utils.GetNodes(node, 'property'):
      prop_name = xml_parser_utils.GetAttribute(sub_node, 'name')
      prop_value = xml_parser_utils.GetAttribute(sub_node, 'value')
      self.app_engine_web_xml.system_properties[prop_name] = prop_value

  def ProcessBetaSettingsNode(self, node):
    for sub_node in xml_parser_utils.GetNodes(node, 'setting'):
      prop_name = xml_parser_utils.GetAttribute(sub_node, 'name')
      prop_value = xml_parser_utils.GetAttribute(sub_node, 'value')
      self.app_engine_web_xml.beta_settings[prop_name] = prop_value

  def ProcessVmSettingsNode(self, node):
    for sub_node in xml_parser_utils.GetNodes(node, 'setting'):
      prop_name = xml_parser_utils.GetAttribute(sub_node, 'name')
      prop_value = xml_parser_utils.GetAttribute(sub_node, 'value')
      self.app_engine_web_xml.vm_settings[prop_name] = prop_value

  def ProcessEnvVariablesNode(self, node):
    for sub_node in xml_parser_utils.GetNodes(node, 'env-var'):
      prop_name = xml_parser_utils.GetAttribute(sub_node, 'name')
      prop_value = xml_parser_utils.GetAttribute(sub_node, 'value')
      self.app_engine_web_xml.env_variables[prop_name] = prop_value

  def ProcessApplicationNode(self, node):
    self.app_engine_web_xml.app_id = node.text

  def ProcessVersionNode(self, node):
    self.app_engine_web_xml.version_id = node.text

  def ProcessSourceLanguageNode(self, node):
    self.app_engine_web_xml.source_language = node.text

  def ProcessModuleNode(self, node):
    self.app_engine_web_xml.module = node.text

  def ProcessServiceNode(self, node):
    self.app_engine_web_xml.service = node.text

  def ProcessInstanceClassNode(self, node):
    self.app_engine_web_xml.instance_class = node.text

  def ProcessAutomaticScalingNode(self, node):
    """Sets automatic scaling settings."""
    automatic_scaling = AutomaticScaling()
    automatic_scaling.min_pending_latency = xml_parser_utils.GetChildNodeText(
        node, 'min-pending-latency').strip()
    automatic_scaling.max_pending_latency = xml_parser_utils.GetChildNodeText(
        node, 'max-pending-latency').strip()
    automatic_scaling.min_idle_instances = xml_parser_utils.GetChildNodeText(
        node, 'min-idle-instances').strip()
    automatic_scaling.max_idle_instances = xml_parser_utils.GetChildNodeText(
        node, 'max-idle-instances').strip()
    self.app_engine_web_xml.automatic_scaling = automatic_scaling

  def ProcessManualScalingNode(self, node):
    manual_scaling = ManualScaling()
    manual_scaling.instances = xml_parser_utils.GetChildNodeText(
        node, 'instances').strip()
    self.app_engine_web_xml.manual_scaling = manual_scaling

  def ProcessBasicScalingNode(self, node):
    basic_scaling = BasicScaling()
    basic_scaling.max_instances = xml_parser_utils.GetChildNodeText(
        node, 'max-instances').strip()
    basic_scaling.idle_timeout = xml_parser_utils.GetChildNodeText(
        node, 'idle-timeout').strip()
    self.app_engine_web_xml.basic_scaling = basic_scaling

  def ProcessStaticFilesNode(self, node):
    """Processes files according to filetype."""
    for sub_node in xml_parser_utils.GetNodes(node, 'include'):
      path = xml_parser_utils.GetAttribute(sub_node, 'path').strip()
      expiration = xml_parser_utils.GetAttribute(sub_node, 'expiration').strip()
      static_file_include = StaticFileInclude(path, expiration, {})

      for http_header_node in xml_parser_utils.GetNodes(
          sub_node, 'http-header'):
        name = xml_parser_utils.GetAttribute(http_header_node, 'name')
        value = xml_parser_utils.GetAttribute(http_header_node, 'value')

        if name in static_file_include.http_headers:
          self.errors.append('Headers can only be entered once; %s entered '
                             'more than once' % name)
        static_file_include.http_headers[name] = value
      self.app_engine_web_xml.static_file_includes.append(static_file_include)

    for sub_node in xml_parser_utils.GetNodes(node, 'exclude'):
      path = xml_parser_utils.GetAttribute(sub_node, 'path').strip()
      self.app_engine_web_xml.static_file_excludes.append(path)

  def ProcessResourceFilesNode(self, node):
    for sub_node in xml_parser_utils.GetNodes(node, 'include'):
      path = xml_parser_utils.GetAttribute(sub_node, 'path').strip()
      self.app_engine_web_xml.resource_file_includes.append(path)

    for sub_node in xml_parser_utils.GetNodes(node, 'exclude'):
      path = xml_parser_utils.GetAttribute(sub_node, 'path').strip()
      self.app_engine_web_xml.resource_file_excludes.append(path)

  def ProcessSslEnabledNode(self, node):
    value = xml_parser_utils.BooleanValue(node.text)
    self.app_engine_web_xml.ssl_enabled = value

  def ProcessSessionsEnabledNode(self, node):
    value = xml_parser_utils.BooleanValue(node.text)
    self.app_engine_web_xml.sessions_enabled = value

  def ProcessAsyncSessionPersistenceNode(self, node):
    enabled = xml_parser_utils.BooleanValue(
        xml_parser_utils.GetAttribute(node, 'enabled'))
    self.app_engine_web_xml.async_session_persistence = enabled
    queue_name = xml_parser_utils.GetAttribute(node, 'queue-name').strip()
    self.app_engine_web_xml.async_session_persistence_queue_name = queue_name

  def ProcessUserPermissionsNode(self, node):
    for node in xml_parser_utils.GetNodes(node, 'permission'):
      class_name = xml_parser_utils.GetAttribute(node, 'class-name').strip()
      name = xml_parser_utils.GetAttribute(node, 'name').strip()
      actions = xml_parser_utils.GetAttribute(node, 'actions').strip()
      if class_name.startswith('java.'):
        self.errors.append('Cannot specify user-permission for '
                           'classes in java.* packages.')
      user_permission = UserPermission()
      user_permission.class_name = class_name
      user_permission.name = name
      user_permission.actions = actions
      self.app_engine_web_xml.user_permissions.append(user_permission)

  def ProcessPublicRootNode(self, node):
    """Sets public root node so that it is of form "/foo"."""
    new_root = node.text
    if new_root:
      if '*' in new_root:
        self.errors.append('public-root cannot contain wildcards')
        return
      if new_root.endswith('/'):
        new_root = new_root[:-1]
      if not new_root.startswith('/'):
        new_root = '/' + new_root

      self.app_engine_web_xml.public_root = new_root

  def ProcessInboundServicesNode(self, node):
    for node in xml_parser_utils.GetNodes(node, 'service'):
      self.app_engine_web_xml.inbound_services.add(node.text)

  def ProcessPrecompilationEnabledNode(self, node):
    value = xml_parser_utils.BooleanValue(node.text)
    self.app_engine_web_xml.precompilation_enabled = value

  def ProcessAdminConsoleNode(self, node):
    for node in xml_parser_utils.GetNodes(node, 'page'):
      name = xml_parser_utils.GetAttribute(node, 'name').strip()
      url = xml_parser_utils.GetAttribute(node, 'url').strip()
      admin_console_page = AdminConsolePage()
      admin_console_page.name = name
      admin_console_page.url = url
      self.app_engine_web_xml.admin_console_pages.append(admin_console_page)

  def ProcessStaticErrorHandlersNode(self, node):
    for node in xml_parser_utils.GetNodes(node, 'handler'):
      filename = xml_parser_utils.GetAttribute(node, 'file').strip()
      error_code = xml_parser_utils.GetAttribute(node, 'error-code').strip()
      error_handler = ErrorHandler()
      error_handler.name = filename
      error_handler.code = error_code
      self.app_engine_web_xml.static_error_handlers.append(error_handler)

  def ProcessWarmupRequestsEnabledNode(self, node):
    warmup_requests_enabled = xml_parser_utils.BooleanValue(node.text)
    warmup_service = AppEngineWebXml.WARMUP_SERVICE
    if warmup_requests_enabled:
      self.app_engine_web_xml.inbound_services.add(warmup_service)
    else:
      self.app_engine_web_xml.inbound_services.remove(warmup_service)

  def ProcessThreadsafeNode(self, node):
    value = xml_parser_utils.BooleanValue(node.text)
    self.app_engine_web_xml.threadsafe = value
    self.app_engine_web_xml.threadsafe_value_provided = True

  def ProcessCodeLockNode(self, node):
    self.app_engine_web_xml.codelock = xml_parser_utils.BooleanValue(node.text)

  def ProcessVmNode(self, node):
    self.app_engine_web_xml.vm = xml_parser_utils.BooleanValue(node.text)

  def ProcessEnvNode(self, node):
    self.app_engine_web_xml.env = node.text

  def ProcessApiConfigNode(self, node):
    servlet = xml_parser_utils.GetAttribute(node, 'servlet-class').strip()
    url = xml_parser_utils.GetAttribute(node, 'url-pattern').strip()
    api_config = ApiConfig()
    api_config.servlet_class = servlet
    api_config.url = url
    self.app_engine_web_xml.api_config = api_config
    for sub_node in xml_parser_utils.GetNodes(
        node, 'endpoint-servlet-mapping-id'):
      api_id = sub_node.text.strip()
      if api_id:
        self.app_engine_web_xml.api_endpoint_ids.append(api_id)

  def ProcessPagespeedNode(self, node):
    """Processes URLs and puts them into the Pagespeed object."""
    pagespeed = Pagespeed()
    pagespeed.url_blacklist = [
        sub_node.text for sub_node in xml_parser_utils.GetNodes(
            node, 'url-blacklist')]
    pagespeed.domains_to_rewrite = [
        sub_node.text for sub_node in xml_parser_utils.GetNodes(
            node, 'domain-to-rewrite')]
    pagespeed.enabled_rewriters = [
        sub_node.text for sub_node in xml_parser_utils.GetNodes(
            node, 'enabled-rewriter')]
    pagespeed.disabled_rewriters = [
        sub_node.text for sub_node in xml_parser_utils.GetNodes(
            node, 'disabled-rewriter')]
    self.app_engine_web_xml.pagespeed = pagespeed

  def ProcessClassLoaderConfigNode(self, node):
    for node in xml_parser_utils.GetNodes(node, 'priority-specifier'):
      entry = PrioritySpecifierEntry()
      entry.filename = xml_parser_utils.GetAttribute(node, 'filename')
      if not entry.filename:
        self.errors.append('Filename needs to be provided for each '
                           'priority specifier')
      elif self.app_engine_web_xml.SpecifierEnteredAlready(entry.filename):
        self.errors.append('Cannot have more than one priority specifier with '
                           'the same filename: %s' % entry.filename)
      else:
        try:
          priority = xml_parser_utils.GetAttribute(node, 'priority')
          entry.priority = float(priority) if priority else 1.0
        except ValueError:
          self.errors.append('priority-specifiers must be numbers')
        self.app_engine_web_xml.class_loader_config.append(entry)

  def ProcessUrlStreamHandlerNode(self, node):
    """Processes url stream handler, makes sure it is correct type."""
    new_type = node.text
    urlfetch = self.app_engine_web_xml.URL_HANDLER_URLFETCH
    native = self.app_engine_web_xml.URL_HANDLER_NATIVE
    if new_type not in (urlfetch, native):
      exception_str = 'url-stream-handler must be %s or %s given %s' % (
          urlfetch, native, new_type)
      self.errors.append(exception_str)
    self.app_engine_web_xml.url_stream_handler_type = new_type

  def ProcessUseGoogleConnectorJNode(self, node):
    value = xml_parser_utils.BooleanValue(node.text)
    self.app_engine_web_xml.google_connector_j = value

  def ProcessAutoIdPolicyNode(self, node):
    policy = node.text
    if policy:
      default = self.app_engine_web_xml.DEFAULT_POLICY
      legacy = self.app_engine_web_xml.LEGACY_POLICY
      if policy not in (default, legacy):
        self.errors.append('auto-id-policy must be either "%s" or '
                           '"%s" given %s' % (default, legacy, policy))
        return
      self.app_engine_web_xml.auto_id_policy = policy

  def ProcessHealthCheckNode(self, node):
    health_check = HealthCheck()
    for child in node:
      tag = xml_parser_utils.GetTag(child)
      if tag == 'enable-health-check':
        health_check.enable_health_check = (
            xml_parser_utils.BooleanValue(child.text))
      elif tag == 'host':
        health_check.host = child.text
      elif tag in ('check-interval-sec', 'healthy-threshold',
                   'restart-threshold', 'timeout-sec', 'unhealthy-threshold'):
        text = child.text or ''
        try:
          value = self._PositiveInt(text)
          setattr(health_check, tag.replace('-', '_'), value)
        except ValueError:
          self.errors.append('value for %s must be a positive integer: "%s"' %
                             (tag, text))
      else:
        self.errors.append(
            'unrecognized element within <health-check>: <%s>' % tag)
    self.app_engine_web_xml.health_check = health_check

  def ProcessVmHealthCheckNode(self, node):
    self.ProcessHealthCheckNode(node)

  def ProcessResourcesNode(self, node):
    resources = Resources()
    for child in node:
      tag = xml_parser_utils.GetTag(child)
      if tag in ('cpu', 'memory-gb', 'disk-size-gb'):
        text = child.text or ''
        setattr(resources, tag.replace('-', '_'), text)
      else:
        self.errors.append(
            'unrecognized element within <resources>: <%s>' % tag)
    self.app_engine_web_xml.resources = resources

  def ProcessNetworkNode(self, node):
    network = Network()
    for child in node:
      tag = xml_parser_utils.GetTag(child)
      if tag in ('instance-tag', 'name'):
        text = child.text or ''
        setattr(network, tag.replace('-', '_'), text)
      elif tag == 'forwarded-port':
        if not hasattr(network, 'forwarded_ports'):
          network.forwarded_ports = []
        network.forwarded_ports.append(child.text or '')
      else:
        self.errors.append(
            'unrecognized element within <network>: <%s>' % tag)
    self.app_engine_web_xml.network = network

  def CheckScalingConstraints(self):
    """Checks that at most one type of scaling is enabled."""
    scaling_num = sum([x is not None for x in [
        self.app_engine_web_xml.basic_scaling,
        self.app_engine_web_xml.automatic_scaling,
        self.app_engine_web_xml.manual_scaling,
        ]])
    if scaling_num > 1:
      self.errors.append('Cannot enable more than one type of scaling')

  @staticmethod
  def _PositiveInt(text):
    """Parse the given text as a positive integer.

    Args:
      text: a string that should contain the decimal representation of a
        positive integer.

    Returns:
      An int that is the parsed value.

    Raises:
      ValueError: if text cannot be parsed as a positive integer.
    """
    value = int(text)
    if value > 0:
      return value
    raise ValueError('Not a positive integer: %s' % text)


class AppEngineWebXml(ValueMixin):
  """Organizes and stores data from appengine-web.xml."""
  URL_HANDLER_URLFETCH = 'urlfetch'
  URL_HANDLER_NATIVE = 'native'
  WARMUP_SERVICE = 'warmup'
  DEFAULT_POLICY = 'default'
  LEGACY_POLICY = 'legacy'

  def __init__(self):
    """Initializes an empty AppEngineWebXml object."""
    self.app_id = None
    self.version_id = None
    self.source_language = None
    self.module = None
    self.service = None
    self.system_properties = {}
    self.beta_settings = {}
    self.vm_settings = {}
    self.health_check = None
    self.resources = None
    self.network = None
    self.env_variables = {}
    self.instance_class = None
    self.automatic_scaling = None
    self.manual_scaling = None
    self.basic_scaling = None
    self.ssl_enabled = True
    self.sessions_enabled = False
    self.async_session_persistence = False
    self.async_session_persistence_queue_name = None
    self.user_permissions = []
    self.public_root = ''
    self.static_include_pattern = None
    self.inbound_services = set([self.WARMUP_SERVICE])
    self.precompilation_enabled = True
    self.admin_console_pages = []
    self.static_error_handlers = []
    self.threadsafe = False
    self.threadsafe_value_provided = False
    self.codelock = None
    self.vm = False
    self.env = '1'
    self.api_config = None
    self.api_endpoint_ids = []
    self.pagespeed = None
    self.class_loader_config = []
    self.url_stream_handler_type = None
    self.use_google_connector_j = None
    self.static_file_includes = []
    self.static_file_excludes = ['WEB-INF/**', '**.jsp']
    self.resource_file_includes = []
    self.resource_file_excludes = []
    self.auto_id_policy = self.DEFAULT_POLICY
    self._app_root = ''
    self.static_include_pattern = None
    self.static_exclude_pattern = None
    self.resource_include_pattern = None
    self.resource_exclude_pattern = None

  def SpecifierEnteredAlready(self, filename):
    return filename in (entry.filename for entry in self.class_loader_config)

  def IncludesStatic(self, path):
    """Checks whether a given file should be classified as a static file."""
    path = self._UrlifyPath(path)
    if not self.static_include_pattern:

      includes_list = ([inc.pattern for inc in self.static_file_includes]
                       or [self.public_root + '/**'])
      self.static_include_pattern = self._CreatePatternListRegex(includes_list)

    if self.static_file_excludes:
      if not self.static_exclude_pattern:
        self.static_exclude_pattern = self._CreatePatternListRegex(
            self.static_file_excludes)
      if self.static_exclude_pattern.match(path):
        return False

    return self.static_include_pattern.match(path)

  def IncludesResource(self, path):
    """Checks whether a given file should be classified as a resource file."""
    path = self._UrlifyPath(path)
    if not self.resource_include_pattern:
      includes = self.resource_file_includes or ['**']
      self.resource_include_pattern = self._CreatePatternListRegex(includes)

    if self.resource_file_excludes:
      if not self.resource_exclude_pattern:
        self.resource_exclude_pattern = self._CreatePatternListRegex(
            self.resource_file_excludes)
      if self.resource_exclude_pattern.match(path):
        return False

    return self.resource_include_pattern.match(path)

  @staticmethod
  def _UrlifyPath(path):
    r"""Convert the path into a form compatible with URLs.

    On Unix-like systems, a path looks like foo/bar/baz.png, which is already
    compatible with the path part of a URL like
    http://myapp.appspot.com/foo/bar/baz.png
    But on Windows, a path can also look like foo\bar\baz.png, which will fail
    if we naively try to match it against a URL-style pattern like foo/**.png.
    So we convert \ into / in that case. On Windows, / is also accepted as
    a separator, so it is correct for that inputs foo\bar\baz.png
    and foo/bar/baz.png both produce output foo/bar/baz.png.

    Args:
      path: the path to a file

    Returns:
      The input path, but using / as separator even if the OS uses \.
    """
    return path if os.path.sep == '/' else path.replace(os.path.sep, '/')

  def _CreatePatternListRegex(self, patterns):
    """Converts a list of patterns into a regex.

    Args:
      patterns: A list of single and double wildcarded path specifying patterns.
    Returns:
      A regular expression matching any of the paths in patterns matching
      one of the files with the path in the subdirectory of the application
      basepath. Ex. if we have and basepath (app_root) of "approot" and
      patterns "foo" and "bar", this returns the compiled regular expression
      of '(^approot\\/foo$|^approot\\/bar$)'.
    """
    regexed_patterns = [self._CreateFileNameRegex(pat) for pat in patterns]
    def _StripLeadingSlashes(pat):
      while pat.startswith('/'):
        pat = pat[1:]
      return pat
    regexed_patterns = [self._CreateFileNameRegex(_StripLeadingSlashes(pat))
                        for pat in patterns]

    app_root_regex = self._CreateFileNameRegex(self._UrlifyPath(self.app_root))
    regexed_patterns = ['^%s\\/%s$' % (app_root_regex, pattern_regex)
                        for pattern_regex in regexed_patterns]
    return re.compile('(%s)' % '|'.join(regexed_patterns))

  def _CreateFileNameRegex(self, filename):
    """Converts the object's pattern into an unanchored regular expression.

    Static file patterns can contain single- and double-wildcards. '**'
    represents zero or more directories in a path, and '*' represents zero or
    more characters in a file or directory name.

    Args:
      filename: a resource or static file pattern.
    Returns:
      regular expression version of the pattern. For example, a filename of
      'foo/**.txt' becomes 'foo\\/.*\\.txt'.
    """
    return re.escape(filename).replace('\\*\\*', '.*').replace('\\*', '[^/]*')

  def _SetAppRoot(self, new_root):
    self._app_root = new_root


    self.static_include_pattern = None
    self.static_exclude_pattern = None
    self.resource_include_pattern = None
    self.resource_exclude_pattern = None

  def _GetAppRoot(self):
    return self._app_root

  app_root = property(_GetAppRoot, _SetAppRoot)


class AutomaticScaling(ValueMixin):
  """Instances contain information about automatic scaling settings."""
  pass


class ManualScaling(ValueMixin):
  """Instances contain information about manual scaling settings."""
  pass


class BasicScaling(ValueMixin):
  """Instances contain information about basic scaling settings."""
  pass


class UserPermission(ValueMixin):
  """Instances contain information about user permissions."""
  pass


class AdminConsolePage(ValueMixin):
  """Instances contain information about the admin console page settings."""
  pass


class ErrorHandler(ValueMixin):
  """Instances contain information about error handler settings."""
  pass


class ApiConfig(ValueMixin):
  """Instances contain information about the API config settings."""
  pass


class Pagespeed(ValueMixin):
  """Instances contain information about the pagespeed settings."""


class PrioritySpecifierEntry(ValueMixin):
  """Instances describe a priority specifier entry in appengine-web.xml."""
  pass


class StaticFileInclude(ValueMixin):
  """Instances describe static files to be included in app configuration."""

  def __init__(self, pattern, expiration, http_headers):
    self.pattern = pattern
    self.expiration = expiration
    self.http_headers = http_headers


class HealthCheck(ValueMixin):
  """Instances contain information about health check settings."""
  pass


class Resources(ValueMixin):
  """Instances contain information about resources settings."""
  pass


class BetaSettings(ValueMixin):
  """Instances contain information about beta settings."""
  pass


class Network(ValueMixin):
  """Instances contain information about network settings."""
