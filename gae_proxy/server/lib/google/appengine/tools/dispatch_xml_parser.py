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
"""Directly processes text of dispatch.xml.

DispatchXmlParser is called with an XML string to produce a list of
DispatchEntry objects containing the data from the XML.
"""

from xml.etree import ElementTree

from google.appengine.tools import xml_parser_utils
from google.appengine.tools.app_engine_config_exception import AppEngineConfigException

MISSING_URL = '<dispatch> node must contain a <url>'
MISSING_MODULE = '<dispatch> node must contain a <module>'


def GetDispatchYaml(application, dispatch_xml_str):
  return _MakeDispatchListIntoYaml(
      application, DispatchXmlParser().ProcessXml(dispatch_xml_str))


def _MakeDispatchListIntoYaml(application, dispatch_list):
  """Converts list of DispatchEntry objects into a YAML string."""
  statements = [
      'application: %s' % application,
      'dispatch:',
  ]
  for entry in dispatch_list:
    statements += entry.ToYaml()
  return '\n'.join(statements) + '\n'


class DispatchXmlParser(object):
  """Provides logic for walking down XML tree and pulling data."""

  def ProcessXml(self, xml_str):
    """Parses XML string and returns object representation of relevant info.

    Args:
      xml_str: The XML string.
    Returns:
      A list of DispatchEntry objects defining how URLs are dispatched to
      modules.
    Raises:
      AppEngineConfigException: In case of malformed XML or illegal inputs.
    """

    try:
      self.dispatch_entries = []
      self.errors = []
      xml_root = ElementTree.fromstring(xml_str)
      if xml_root.tag != 'dispatch-entries':
        raise AppEngineConfigException('Root tag must be <dispatch-entries>')

      for child in xml_root.getchildren():
        self.ProcessDispatchNode(child)

      if self.errors:
        raise AppEngineConfigException('\n'.join(self.errors))

      return self.dispatch_entries
    except ElementTree.ParseError:
      raise AppEngineConfigException('Bad input -- not valid XML')

  def ProcessDispatchNode(self, node):
    """Processes XML <dispatch> nodes into DispatchEntry objects.

    The following information is parsed out:
      url: The URL or URL pattern to route.
      module: The module to route it to.
    If there are no errors, the data is loaded into a DispatchEntry object
    and added to a list. Upon error, a description of the error is added to
    a list and the method terminates.

    Args:
      node: <dispatch> XML node in dos.xml.
    """
    tag = xml_parser_utils.GetTag(node)
    if tag != 'dispatch':
      self.errors.append('Unrecognized node: <%s>' % tag)
      return

    entry = DispatchEntry()
    entry.url = xml_parser_utils.GetChildNodeText(node, 'url')
    entry.module = xml_parser_utils.GetChildNodeText(node, 'module')

    validation = self._ValidateEntry(entry)
    if validation:
      self.errors.append(validation)
      return
    self.dispatch_entries.append(entry)

  def _ValidateEntry(self, entry):
    if not entry.url:
      return MISSING_URL
    if not entry.module:
      return MISSING_MODULE


class DispatchEntry(object):
  """Instances contain information about individual dispatch entries."""

  def ToYaml(self):
    return [
        "- url: '%s'" % self._SanitizeForYaml(self.url),
        '  module: %s' % self.module,
    ]

  def _SanitizeForYaml(self, dirty_str):
    return dirty_str.replace("'", r"\'")
