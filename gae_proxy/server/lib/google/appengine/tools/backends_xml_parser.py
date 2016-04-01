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
"""Directly processes text of backends.xml.

BackendsXmlParser is called with an XML string to produce a Backends object
containing the data from the XML.

BackendsXmlParser: converts XML to BackendsXml objct
Backend: describes a single backend specified in backends.xml

"""

from xml.etree import ElementTree

from google.appengine.tools import xml_parser_utils
from google.appengine.tools.app_engine_config_exception import AppEngineConfigException
from google.appengine.tools.value_mixin import ValueMixin


def GetBackendsYaml(unused_application, backends_xml_str):
  """Translates a backends.xml string into a backends.yaml string."""
  backend_list = BackendsXmlParser().ProcessXml(backends_xml_str)
  statements = ['backends:']
  for backend in backend_list:
    statements += backend.ToYaml()
  return '\n'.join(statements) + '\n'


class BackendsXmlParser(object):
  """Provides logic for walking down XML tree and pulling data."""

  def ProcessXml(self, xml_str):
    """Parses XML string and returns object representation of relevant info.

    Args:
      xml_str: The XML string.
    Returns:
      A list of Backend object containg information about backends from the XML.
    Raises:
      AppEngineConfigException: In case of malformed XML or illegal inputs.
    """
    try:
      self.backends = []
      self.errors = []
      xml_root = ElementTree.fromstring(xml_str)

      for child in xml_root.getchildren():
        self.ProcessBackendNode(child)

      if self.errors:
        raise AppEngineConfigException('\n'.join(self.errors))

      return self.backends
    except ElementTree.ParseError:
      raise AppEngineConfigException('Bad input -- not valid XML')

  def ProcessBackendNode(self, node):
    """Processes XML nodes labeled 'backend' into a Backends object."""
    tag = xml_parser_utils.GetTag(node)
    if tag != 'backend':
      self.errors.append('Unrecognized node: <%s>' % tag)
      return

    backend = Backend()
    name = xml_parser_utils.GetAttribute(node, 'name')
    if not name:
      self.errors.append('All backends must have names')
      backend.name = '-'
    else:
      backend.name = name
    instance_class = xml_parser_utils.GetChildNodeText(node, 'class')
    if instance_class:
      backend.instance_class = instance_class
    instances = xml_parser_utils.GetChildNodeText(node, 'instances')
    if instances:
      try:
        backend.instances = int(instances)
      except ValueError:
        self.errors.append(
            '<instances> must be an integer (bad value %s) in backend %s' %
            (instances, backend.name))
    max_concurrent_requests = xml_parser_utils.GetChildNodeText(
        node, 'max-concurrent-requests')
    if max_concurrent_requests:
      try:
        backend.max_concurrent_requests = int(max_concurrent_requests)
      except ValueError:
        self.errors.append('<max-concurrent-requests> must be an integer '
                           '(bad value %s) in backend %s' %
                           (max_concurrent_requests, backend.name))

    options_node = xml_parser_utils.GetChild(node, 'options')
    if options_node is not None:
      for sub_node in options_node.getchildren():
        tag = xml_parser_utils.GetTag(sub_node)
        if tag not in ('fail-fast', 'dynamic', 'public'):
          self.errors.append('<options> only supports values fail-fast, '
                             'dynamic, and public (bad value %s) in backend %s'
                             % (tag, backend.name))
          continue
        tag = tag.replace('-', '')
        if xml_parser_utils.BooleanValue(sub_node.text):
          backend.options.add(tag)
        else:
          if tag in backend.options:
            backend.options.remove(tag)

    self.backends.append(backend)


class Backend(ValueMixin):
  """Instances contain information about individual backend specifications."""

  def __init__(self):
    self.name = None
    self.instances = None
    self.instance_class = None
    self.max_concurrent_requests = None
    self.options = set()



  def ToYaml(self):
    """Convert the backend specification into a list of YAML lines."""
    statements = ['- name: %s' % self.name]
    for entry, field in [
        ('instances', self.instances),
        ('class', self.instance_class),
        ('max_concurrent_requests', self.max_concurrent_requests)]:
      if field is not None:
        statements += ['  %s: %s' % (entry, str(field))]

    if self.options:
      options_str = ', '.join(sorted(list(self.options)))
      statements += ['  options: %s' % options_str]

    return statements
