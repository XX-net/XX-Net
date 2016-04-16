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
"""Directly processes text of web.xml.

WebXmlParser is called with Xml string to produce a WebXml object containing
the data from that string.

WebXmlParser: Converts xml to AppEngineWebXml object.
WebXml: Contains relevant information from web.xml.
SecurityConstraint: Contains information about specified security constraints.

"""

import logging

from xml.etree import ElementTree

from google.appengine.tools import xml_parser_utils
from google.appengine.tools.app_engine_config_exception import AppEngineConfigException
from google.appengine.tools.value_mixin import ValueMixin


class WebXmlParser(object):
  """Provides logic for walking down XML tree and pulling data."""

  def ProcessXml(self, xml_str, has_jsps=False):
    """Parses XML string and returns object representation of relevant info.

    Uses ElementTree parser to return a tree representation of XML.
    Then walks down that tree and extracts important info and adds it to the
    object.

    Args:
      xml_str: The XML string itself.
      has_jsps: True if the application has *.jsp files.

    Returns:
      If there is well-formed but illegal XML, returns a list of
      errors. Otherwise, returns an AppEngineWebXml object containing
      information from XML.

    Raises:
      AppEngineConfigException: In case of malformed XML or illegal inputs.
    """
    try:
      self.web_xml = WebXml()
      self.web_xml.has_jsps = has_jsps
      self.errors = []
      xml_root = ElementTree.fromstring(xml_str)
      for node in xml_root.getchildren():
        self.ProcessSecondLevelNode(node)

      if self.errors:
        raise AppEngineConfigException('\n'.join(self.errors))

      return self.web_xml

    except ElementTree.ParseError:
      raise AppEngineConfigException('Bad input -- not valid XML')





  _IGNORED_NODES = frozenset([
      'context-param', 'description', 'display-name', 'distributable',
      'ejb-local-ref', 'ejb-ref', 'env-entry', 'filter', 'icon',
      'jsp-config', 'listener', 'locale-encoding-mapping-list',
      'login-config', 'message-destination', 'message-destination-ref',
      'persistence-context-ref', 'persistence-unit-ref', 'post-construct',
      'pre-destroy', 'resource-env-ref', 'resource-ref', 'security-role',
      'service-ref', 'servlet', 'session-config', 'taglib',
  ])

  def ProcessSecondLevelNode(self, node):
    element_name = xml_parser_utils.GetTag(node)
    if element_name in self._IGNORED_NODES:


      return
    camel_case_name = ''.join(part.title() for part in element_name.split('-'))
    method_name = 'Process%sNode' % camel_case_name
    if (hasattr(self, method_name) and
        method_name is not 'ProcessSecondLevelNode'):
      getattr(self, method_name)(node)
    else:
      logging.warning('Second-level tag not recognized: %s', element_name)

  def ProcessServletMappingNode(self, node):
    self._ProcessUrlMappingNode(node)

  def ProcessFilterMappingNode(self, node):
    self._ProcessUrlMappingNode(node)

  def _ProcessUrlMappingNode(self, node):
    """Parses out URL and possible ID for filter-mapping and servlet-mapping.

    Pulls url-pattern text out of node and adds to WebXml object. If url-pattern
    has an id attribute, adds that as well. This is done for <servlet-mapping>
    and <filter-mapping> nodes.

    Args:
      node: An ElementTreeNode which looks something like the following:

        <servlet-mapping>
          <servlet-name>redteam</servlet-name>
          <url-pattern>/red/*</url-pattern>
        </servlet-mapping>
    """
    url_pattern_node = xml_parser_utils.GetChild(node, 'url-pattern')
    if url_pattern_node is not None:
      self.web_xml.patterns.append(url_pattern_node.text)
      id_attr = xml_parser_utils.GetAttribute(url_pattern_node, 'id')
      if id_attr:
        self.web_xml.pattern_to_id[url_pattern_node.text] = id_attr

  def ProcessErrorPageNode(self, node):
    """Process error page specifications.

    If one of the supplied error codes is 404, allow fall through to runtime.

    Args:
      node: An ElementTreeNode which looks something like the following.
        <error-page>
          <error-code>500</error-code>
          <location>/errors/servererror.jsp</location>
        </error-page>
    """

    error_code = xml_parser_utils.GetChildNodeText(node, 'error-code')
    if error_code == '404':
      self.web_xml.fall_through_to_runtime = True

  def ProcessWelcomeFileListNode(self, node):
    for welcome_node in xml_parser_utils.GetNodes(node, 'welcome-file'):
      welcome_file = welcome_node.text
      if welcome_file and welcome_file[0] == '/':
        self.errors.append('Welcome files must be relative paths: %s' %
                           welcome_file)
        continue
      self.web_xml.welcome_files.append(welcome_file)

  def ProcessMimeMappingNode(self, node):
    extension = xml_parser_utils.GetChildNodeText(node, 'extension')
    mime_type = xml_parser_utils.GetChildNodeText(node, 'mime-type')

    if not extension:
      self.errors.append('<mime-type> without extension')
      return
    self.web_xml.mime_mappings[extension] = mime_type

  def ProcessSecurityConstraintNode(self, node):
    """Pulls data from the security constraint node and adds to WebXml object.

    Args:
      node: An ElementTree Xml node that looks something like the following:

        <security-constraint>
          <web-resource-collection>
            <url-pattern>/profile/*</url-pattern>
          </web-resource-collection>
          <user-data-constraint>
            <transport-guarantee>CONFIDENTIAL</transport-guarantee>
          </user-data-constraint>
        </security-constraint>
    """
    security_constraint = SecurityConstraint()
    resources_node = xml_parser_utils.GetChild(node, 'web-resource-collection')
    security_constraint.patterns = [
        sub_node.text for sub_node in xml_parser_utils.GetNodes(
            resources_node, 'url-pattern')]
    constraint = xml_parser_utils.GetChild(node, 'auth-constraint')
    if constraint is not None:
      role_name = xml_parser_utils.GetChildNodeText(
          constraint, 'role-name').lower()
      if role_name:
        if role_name not in ('none', '*', 'admin'):
          self.errors.append('Bad value for <role-name> (%s), must be none, '
                             '*, or admin' % role_name)
        security_constraint.required_role = role_name

    user_constraint = xml_parser_utils.GetChild(node, 'user-data-constraint')
    if user_constraint is not None:
      guarantee = xml_parser_utils.GetChildNodeText(
          user_constraint, 'transport-guarantee').lower()
      if guarantee not in ('none', 'integral', 'confidential'):
        self.errors.append('Bad value for <transport-guarantee> (%s), must be'
                           ' none, integral, or confidential' % guarantee)
      security_constraint.transport_guarantee = guarantee

    self.web_xml.security_constraints.append(security_constraint)


class WebXml(ValueMixin):
  """Contains information about web.xml relevant for translation to app.yaml."""

  def __init__(self):
    self.patterns = []
    self.security_constraints = []
    self.welcome_files = []
    self.mime_mappings = {}
    self.pattern_to_id = {}
    self.fall_through_to_runtime = False
    self.has_jsps = False

  def GetMimeTypeForPath(self, path):
    if '.' not in path:
      return None
    return self.mime_mappings.get(path.split('.')[-1], None)


class SecurityConstraint(ValueMixin):
  """Contains information about security constraints in web.xml."""

  def __init__(self):
    self.patterns = []
    self.transport_guarantee = 'none'
    self.required_role = 'none'
