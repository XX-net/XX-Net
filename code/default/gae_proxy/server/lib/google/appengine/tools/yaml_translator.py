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
"""Performs XML-to-YAML translation.

  TranslateXmlToYaml(): performs xml-to-yaml translation with
  string inputs and outputs
  AppYamlTranslator: Class that facilitates xml-to-yaml translation
"""

import os
import re

from google.appengine.tools import app_engine_web_xml_parser as aewxp
from google.appengine.tools import handler_generator
from google.appengine.tools.app_engine_web_xml_parser import AppEngineConfigException


NO_API_VERSION = 'none'


def TranslateXmlToYamlForDevAppServer(app_engine_web_xml,
                                      web_xml,
                                      war_root):
  """Does parsed-XML to YAML-string translation.

  This method is used in the Dev App Server context, where files are served
  directly from the input war directory, unlike the appcfg case where they are
  copied or linked into a parallel hierarchy.  This means that there is no
  __static__ directory containing exactly the files that are supposed to be
  served statically.

  Args:
    app_engine_web_xml: parsed AppEngineWebXml object corresponding to the
      contents of app-engine.web.xml.
    web_xml: parsed WebXml object corresponding to the contents of web.xml.
    war_root: the path to the root directory of the war hierarchy

  Returns:
    The full text of the app.yaml generated from the xml files.

  Raises:
    AppEngineConfigException: raised in processing stage for illegal XML.
  """
  translator = AppYamlTranslatorForDevAppServer(
      app_engine_web_xml, web_xml, war_root)
  return translator.GetYaml()


class AppYamlTranslator(object):
  """Object that contains relevant information for generating app.yaml.

  Attributes:
    app_engine_web_xml: AppEngineWebXml object containing relevant information
      from appengine-web.xml
  """

  def __init__(self,
               app_engine_web_xml,
               web_xml,
               static_files,
               api_version):

    self.app_engine_web_xml = app_engine_web_xml
    self.web_xml = web_xml
    self.static_files = static_files
    self.api_version = api_version

  def GetRuntime(self):
    return 'java7'

  def GetYaml(self):
    """Returns full yaml text."""
    self.VerifyRequiredEntriesPresent()
    stmnt_list = self.TranslateBasicEntries()
    stmnt_list += self.TranslateAutomaticScaling()
    stmnt_list += self.TranslateBasicScaling()
    stmnt_list += self.TranslateManualScaling()
    stmnt_list += self.TranslatePrecompilationEnabled()
    stmnt_list += self.TranslateInboundServices()
    stmnt_list += self.TranslateAdminConsolePages()
    stmnt_list += self.TranslateApiConfig()
    stmnt_list += self.TranslatePagespeed()
    stmnt_list += self.TranslateEnvVariables()
    stmnt_list += self.TranslateBetaSettings()
    stmnt_list += self.TranslateVmSettings()
    stmnt_list += self.TranslateHealthCheck()
    stmnt_list += self.TranslateResources()
    stmnt_list += self.TranslateNetwork()
    stmnt_list += self.TranslateErrorHandlers()
    stmnt_list += self.TranslateApiVersion()
    stmnt_list += self.TranslateHandlers()
    return '\n'.join(stmnt_list) + '\n'

  def SanitizeForYaml(self, the_string):
    return "'%s'" % the_string.replace("'", "''")

  def TranslateBasicEntries(self):
    """Produces yaml for entries requiring little formatting."""
    basic_statements = []

    for entry_name, field in [
        ('application', self.app_engine_web_xml.app_id),
        ('source_language', self.app_engine_web_xml.source_language),
        ('module', self.app_engine_web_xml.module),
        ('service', self.app_engine_web_xml.service),
        ('version', self.app_engine_web_xml.version_id)
    ]:
      if field:
        basic_statements.append(
            '%s: %s' % (entry_name, self.SanitizeForYaml(field)))
    for entry_name, field in [
        ('runtime', self.GetRuntime()),
        ('vm', self.app_engine_web_xml.vm),
        ('threadsafe', self.app_engine_web_xml.threadsafe),
        ('instance_class', self.app_engine_web_xml.instance_class),
        ('auto_id_policy', self.app_engine_web_xml.auto_id_policy),
        ('code_lock', self.app_engine_web_xml.codelock)]:
      if field:
        basic_statements.append('%s: %s' % (entry_name, field))
    if self.app_engine_web_xml.env != '1':
      basic_statements.append('env: %s' % self.app_engine_web_xml.env)
    return basic_statements

  def TranslateAutomaticScaling(self):
    """Translates automatic scaling settings to yaml."""
    if not self.app_engine_web_xml.automatic_scaling:
      return []
    statements = ['automatic_scaling:']
    for setting in ['min_pending_latency',
                    'max_pending_latency',
                    'min_idle_instances',
                    'max_idle_instances']:
      value = getattr(self.app_engine_web_xml.automatic_scaling, setting)
      if value:
        statements.append('  %s: %s' % (setting, value))
    return statements

  def TranslateBasicScaling(self):
    if not self.app_engine_web_xml.basic_scaling:
      return []
    statements = ['basic_scaling:']
    statements.append('  max_instances: ' +
                      self.app_engine_web_xml.basic_scaling.max_instances)
    if self.app_engine_web_xml.basic_scaling.idle_timeout:
      statements.append('  idle_timeout: ' +
                        self.app_engine_web_xml.basic_scaling.idle_timeout)
    return statements

  def TranslateManualScaling(self):
    if not self.app_engine_web_xml.manual_scaling:
      return []

    statements = ['manual_scaling:']
    statements.append('  instances: ' +
                      self.app_engine_web_xml.manual_scaling.instances)
    return statements

  def TranslatePrecompilationEnabled(self):
    if self.app_engine_web_xml.precompilation_enabled:
      return ['derived_file_type:', '- java_precompiled']
    return []

  def TranslateAdminConsolePages(self):
    if not self.app_engine_web_xml.admin_console_pages:
      return []
    statements = ['admin_console:', '  pages:']
    for admin_console_page in self.app_engine_web_xml.admin_console_pages:
      statements.append('  - name: %s' % admin_console_page.name)
      statements.append('    url: %s' % admin_console_page.url)
    return statements

  def TranslateApiConfig(self):

    if not self.app_engine_web_xml.api_config:
      return []
    return ['api_config:', '  url: %s' % self.app_engine_web_xml.api_config.url,
            '  script: unused']

  def TranslateApiVersion(self):
    return ['api_version: %s' % self.SanitizeForYaml(
        self.api_version or NO_API_VERSION)]

  def TranslatePagespeed(self):
    """Translates pagespeed settings in appengine-web.xml to yaml."""
    pagespeed = self.app_engine_web_xml.pagespeed
    if not pagespeed:
      return []
    statements = ['pagespeed:']
    for title, urls in [('domains_to_rewrite', pagespeed.domains_to_rewrite),
                        ('url_blacklist', pagespeed.url_blacklist),
                        ('enabled_rewriters', pagespeed.enabled_rewriters),
                        ('disabled_rewriters', pagespeed.disabled_rewriters)]:
      if urls:
        statements.append('  %s:' % title)
        statements += ['  - %s' % url for url in urls]
    return statements

  def TranslateEnvVariables(self):
    if not self.app_engine_web_xml.env_variables:
      return []

    variables = self.app_engine_web_xml.env_variables
    statements = ['env_variables:']
    for name, value in sorted(variables.iteritems()):
      statements.append(
          '  %s: %s' % (
              self.SanitizeForYaml(name), self.SanitizeForYaml(value)))
    return statements

  def TranslateBetaSettings(self):
    """Translates Beta settings in appengine-web.xml to yaml."""
    if ((not self.app_engine_web_xml.vm) and
        (self.app_engine_web_xml.env != '2')):
      return []

    settings = self.app_engine_web_xml.beta_settings or {}
    if 'java_quickstart' in settings:

      del settings['java_quickstart']
    statements = []
    if settings:
      statements = ['beta_settings:']
      for name in sorted(settings):
        statements.append(
            '  %s: %s' % (
                self.SanitizeForYaml(name),
                self.SanitizeForYaml(settings[name])))
    return statements

  def TranslateVmSettings(self):
    """Translates VM settings in appengine-web.xml to yaml."""
    if ((not self.app_engine_web_xml.vm) and
        (self.app_engine_web_xml.env != '2')):
      return []

    settings = self.app_engine_web_xml.vm_settings or {}
    settings['has_docker_image'] = 'True'
    statements = ['vm_settings:']
    for name in sorted(settings):
      statements.append(
          '  %s: %s' % (
              self.SanitizeForYaml(name), self.SanitizeForYaml(settings[name])))
    return statements

  def TranslateHealthCheck(self):
    """Translates <health-check> in appengine-web.xml to yaml."""
    health_check = self.app_engine_web_xml.health_check
    if not health_check:
      return []

    statements = ['health_check:']
    for attr in ('enable_health_check', 'check_interval_sec', 'timeout_sec',
                 'unhealthy_threshold', 'healthy_threshold',
                 'restart_threshold', 'host'):
      value = getattr(health_check, attr, None)
      if value is not None:
        statements.append('  %s: %s' % (attr, value))
    return statements

  def TranslateResources(self):
    """Translates <resources> in appengine-web.xml to yaml."""
    resources = self.app_engine_web_xml.resources
    if not resources:
      return []

    statements = ['resources:']
    for attr in ('cpu', 'memory_gb', 'disk_size_gb'):
      value = getattr(resources, attr, None)
      if value is not None:
        statements.append('  %s: %s' % (attr, value))
    return statements

  def TranslateNetwork(self):
    """Translates <network> in appengine-web.xml to yaml."""
    network = self.app_engine_web_xml.network
    if not network:
      return []

    statements = ['network:']
    for attr in ('instance_tag', 'name'):
      value = getattr(network, attr, None)
      if value is not None:
        statements.append('  %s: %s' % (attr, value))

    forwarded_ports = getattr(network, 'forwarded_ports', None)
    if forwarded_ports is not None:
      statements.append('  forwarded_ports:')
      for port in forwarded_ports:
        statements.append('  - ' + port)
    return statements

  def TranslateInboundServices(self):
    services = self.app_engine_web_xml.inbound_services
    if not services:
      return []

    statements = ['inbound_services:']
    for service in sorted(services):
      statements.append('- %s' % service)
    return statements

  def TranslateErrorHandlers(self):
    """Translates error handlers specified in appengine-web.xml to yaml."""
    if not self.app_engine_web_xml.static_error_handlers:
      return []
    statements = ['error_handlers:']
    for error_handler in self.app_engine_web_xml.static_error_handlers:

      path = self.ErrorHandlerPath(error_handler)
      statements.append('- file: %s' % path)
      if error_handler.code:
        statements.append('  error_code: %s' % error_handler.code)
      mime_type = self.web_xml.GetMimeTypeForPath(error_handler.name)
      if mime_type:
        statements.append('  mime_type: %s' % mime_type)

    return statements

  def ErrorHandlerPath(self, error_handler):
    """Returns the relative path name for the given error handler.

    Args:
      error_handler: an app_engine_web_xml.ErrorHandler.

    Returns:
      the relative path name for the handler.

    Raises:
      AppEngineConfigException: if the named file is not an existing static
        file.
    """
    name = error_handler.name
    if not name.startswith('/'):
      name = '/' + name
    path = '__static__' + name
    if path not in self.static_files:
      raise AppEngineConfigException(
          'No static file found for error handler: %s, out of %s' %
          (name, self.static_files))
    return path

  def TranslateHandlers(self):
    return handler_generator.GenerateYamlHandlersList(
        self.app_engine_web_xml,
        self.web_xml,
        self.static_files)

  def VerifyRequiredEntriesPresent(self):
    required = {
        'runtime': self.GetRuntime(),
        'threadsafe': self.app_engine_web_xml.threadsafe_value_provided,
    }
    missing = [field for (field, value) in required.items() if not value]
    if missing:
      raise AppEngineConfigException('Missing required fields: %s' %
                                     ', '.join(missing))


def _XmlPatternToRegEx(xml_pattern):
  r"""Translates an appengine-web.xml pattern into a regular expression.

  Specially, this applies to the patterns that appear in the <include> and
  <exclude> elements inside <static-files>. They look like '/**.png' or
  '/stylesheets/*.css', and are translated into expressions like
  '^/.*\.png$' or '^/stylesheets/.*\.css$'.

  Args:
    xml_pattern: a string like '/**.png'

  Returns:
    a compiled regular expression like re.compile('^/.*\.png$').
  """
  result = ['^']
  while xml_pattern:
    if xml_pattern.startswith('**'):
      result.append(r'.*')
      xml_pattern = xml_pattern[1:]
    elif xml_pattern.startswith('*'):
      result.append(r'[^/]*')
    elif xml_pattern.startswith('/'):


      result.append('/')
    else:
      result.append(re.escape(xml_pattern[0]))
    xml_pattern = xml_pattern[1:]
  result.append('$')
  return re.compile(''.join(result))


class AppYamlTranslatorForDevAppServer(AppYamlTranslator):
  """Subclass of AppYamlTranslator specialized for the Dev App Server case.

  The key difference is that static files are served directly from the war
  directory, which means that the app.yaml patterns we define must cover
  exactly those files in that directory hierarchy that are supposed to be static
  while not covering any files that are not supposed to be static.

  Attributes:
    war_root: the root directory of the war hierarchy.
    static_urls: a list of two-item tuples where the first item is a URL that
      should be served statically and the second item corresponds to the
      <include> element that caused that URL to be included.
  """

  def __init__(self,
               app_engine_web_xml,
               web_xml,
               war_root):
    super(AppYamlTranslatorForDevAppServer, self).__init__(
        app_engine_web_xml, web_xml, [], '1.0')
    self.war_root = war_root
    self.static_urls = self.IncludedStaticUrls()

  def IncludedStaticUrls(self):
    """Returns the URLs that should be resolved statically for this app.

    The result includes a URL for every file in the war hierarchy that is
    covered by one of the <include> elements for <static-files> and not covered
    by any of the <exclude> elements.

    Returns:
      a list of two-item tuples where the first item is a URL that should be
      served statically and the second item corresponds to the <include>
      element that caused that URL to be included.
    """






    includes = self.app_engine_web_xml.static_file_includes
    if not includes:



      includes = [aewxp.StaticFileInclude('**', None, {})]
    excludes = self.app_engine_web_xml.static_file_excludes
    files = os.listdir(self.war_root)
    web_inf_name = os.path.normcase('WEB-INF')
    files = [f for f in files if os.path.normcase(f) != web_inf_name]
    static_urls = []
    includes_and_res = [(include, _XmlPatternToRegEx(include.pattern))
                        for include in includes]
    exclude_res = [_XmlPatternToRegEx(exclude) for exclude in excludes]
    self.ComputeIncludedStaticUrls(
        static_urls, self.war_root, '/', files, includes_and_res, exclude_res)
    return static_urls




  def ComputeIncludedStaticUrls(
      self,
      static_urls, dirpath, url_prefix, files, includes_and_res, exclude_res):
    """Compute the URLs that should be resolved statically.

    This recursive method is called for the war directory and every
    subdirectory except the top-level WEB-INF directory. If we have arrived
    at the directory <war-root>/foo/bar then dirpath will be <war-root>/foo/bar
    and url_prefix will be /foo/bar.

    Args:
      static_urls: a list to be filled with the result, two-item tuples where
        the first item is a URL and the second is a parsed <include> element.
      dirpath: the path to the directory inside the war hierarchy that we have
        reached at this point in the recursion.
      url_prefix: the URL prefix that we have reached at this point in the
        recursion.
      files: the contents of the dirpath directory, minus the WEB-INF directory
        if dirpath is the war directory itself.
      includes_and_res: a list of two-item tuples where the first item is a
        parsed <include> element and the second item is a compiled regular
        expression corresponding to the path= pattern from that element.
      exclude_res: a list of compiled regular expressions corresponding to the
        path= patterns from <exclude> elements.
    """
    for f in files:
      path = os.path.join(dirpath, f)
      if os.path.isfile(path):
        url = url_prefix + f
        if not any(exclude_re.search(url) for exclude_re in exclude_res):
          for include, include_re in includes_and_res:
            if include_re.search(url):
              static_urls.append((url, include))
              break
      else:
        self.ComputeIncludedStaticUrls(
            static_urls, path, url_prefix + f + '/', os.listdir(path),
            includes_and_res, exclude_res)

  def TranslateHandlers(self):
    return handler_generator.GenerateYamlHandlersListForDevAppServer(
        self.app_engine_web_xml,
        self.web_xml,
        self.static_urls)

  def ErrorHandlerPath(self, error_handler):
    name = error_handler.name
    if name.startswith('/'):
      name = name[1:]
    if name not in self.static_files:
      raise AppEngineConfigException(
          'No static file found for error handler: %s, out of %s' %
          (name, self.static_files))
    return name
