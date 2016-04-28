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
"""Directly processes text of dos.xml.

DosXmlParser is called with an XML string to produce a list of BlackListEntry
objects containing the data from the XML.

DosXmlParser: converts XML to list of BlackListEntrys.
BlacklistEntry: describes a blacklisted IP.
"""

import re
from xml.etree import ElementTree

import ipaddr

from google.appengine.tools import xml_parser_utils
from google.appengine.tools.app_engine_config_exception import AppEngineConfigException

MISSING_SUBNET = '<blacklist> node must have a subnet specified'
BAD_IPV_SUBNET = '"%s" is not a valid IPv4 or IPv6 subnet'
BAD_PREFIX_LENGTH = ('Prefix length of subnet "%s" must be an integer '
                     '(quad-dotted masks are not supported)')


def GetDosYaml(unused_application, dos_xml_str):
  return _MakeDosListIntoYaml(DosXmlParser().ProcessXml(dos_xml_str))


def _MakeDosListIntoYaml(dos_list):
  """Converts yaml statement list of blacklisted IP's into a string."""
  statements = ['blacklist:']
  for entry in dos_list:
    statements += entry.ToYaml()
  return '\n'.join(statements) + '\n'


class DosXmlParser(object):
  """Provides logic for walking down XML tree and pulling data."""

  def ProcessXml(self, xml_str):
    """Parses XML string and returns object representation of relevant info.

    Args:
      xml_str: The XML string.
    Returns:
      A list of BlacklistEntry objects containing information about blacklisted
      IP's specified in the XML.
    Raises:
      AppEngineConfigException: In case of malformed XML or illegal inputs.
    """

    try:
      self.blacklist_entries = []
      self.errors = []
      xml_root = ElementTree.fromstring(xml_str)
      if xml_root.tag != 'blacklistentries':
        raise AppEngineConfigException('Root tag must be <blacklistentries>')

      for child in xml_root.getchildren():
        self.ProcessBlacklistNode(child)

      if self.errors:
        raise AppEngineConfigException('\n'.join(self.errors))

      return self.blacklist_entries
    except ElementTree.ParseError:
      raise AppEngineConfigException('Bad input -- not valid XML')

  def ProcessBlacklistNode(self, node):
    """Processes XML <blacklist> nodes into BlacklistEntry objects.

    The following information is parsed out:
      subnet: The IP, in CIDR notation.
      description: (optional)
    If there are no errors, the data is loaded into a BlackListEntry object
    and added to a list. Upon error, a description of the error is added to
    a list and the method terminates.

    Args:
      node: <blacklist> XML node in dos.xml.
    """
    tag = xml_parser_utils.GetTag(node)
    if tag != 'blacklist':
      self.errors.append('Unrecognized node: <%s>' % tag)
      return

    entry = BlacklistEntry()
    entry.subnet = xml_parser_utils.GetChildNodeText(node, 'subnet')
    entry.description = xml_parser_utils.GetChildNodeText(node, 'description')

    validation = self._ValidateEntry(entry)
    if validation:
      self.errors.append(validation)
      return
    self.blacklist_entries.append(entry)

  def _ValidateEntry(self, entry):
    if not entry.subnet:
      return MISSING_SUBNET
    try:
      ipaddr.IPNetwork(entry.subnet)
    except ValueError:
      return BAD_IPV_SUBNET % entry.subnet
    parts = entry.subnet.split('/')
    if len(parts) == 2 and not re.match('^[0-9]+$', parts[1]):
      return BAD_PREFIX_LENGTH % entry.subnet


class BlacklistEntry(object):
  """Instances contain information about individual blacklist entries."""

  def ToYaml(self):
    statements = ['- subnet: %s' % self.subnet]
    if self.description:
      statements.append(
          '  description: %s' % self._SanitizeForYaml(self.description))
    return statements

  def _SanitizeForYaml(self, dirty_str):
    return "'%s'" % dirty_str.replace('\n', ' ')
