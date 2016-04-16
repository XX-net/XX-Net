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





"""Bulkloader XML reading and writing.

Handle the XML format specified in a bulkloader.yaml file.
"""











import codecs
import logging
import re

from xml.etree import cElementTree as ElementTree
from xml.sax import saxutils

from google.appengine.ext.bulkload import bulkloader_errors
from google.appengine.ext.bulkload import connector_interface


NODE_PATH_ONLY_RE = '(/[a-zA-Z][a-zA-Z0-9]*)+$'


class SimpleXmlConnector(connector_interface.ConnectorInterface):
  """Read/write a simply-structured XML file and convert dicts for each record.

  A simply-structed XML file is one where we can locate all interesting nodes
  with a simple (ElementTree supported) xpath, and each node contains either
  all the info we care about as child (and not grandchild) nodes with text or
  as attributes.
  We'll also pass the entire node in case the developer wants to do something
  more interesting with it (occasional grandchildren, parents, etc.).

  This is of course a fairly expensive way to read XML--we build a DOM, then
  copy parts of it into a dict. A pull model would work well with the interface
  too.
  """

  ELEMENT_CENTRIC = 1
  ATTRIBUTE_CENTRIC = 2

  @classmethod
  def create_from_options(cls, options, name):
    """Factory using an options dictionary.

    Args:
      options: Dictionary of options. Must contain:
        * xpath_to_nodes: The xpath to select a record.
        * style: 'element_centric' or 'attribute_centric'
      name: The name of this transformer, for use in error messages.

    Returns:
      XmlConnector connector object described by the specified options.

    Raises:
      InvalidConfiguration: If the config is invalid.
    """
    xpath_to_nodes = options.get('xpath_to_nodes')
    if not xpath_to_nodes:
      raise bulkloader_errors.InvalidConfiguration(
          'simplexml must specify xpath_to_nodes. (In transformer named %s)' %
          name)




    if not re.match(NODE_PATH_ONLY_RE, xpath_to_nodes):
      logging.warning('simplexml export only supports very simple '
                      '/root/to/node xpath_to_nodes for now.')

    xml_style = options.get('style')
    xml_style_mapping = {
        'element_centric': cls.ELEMENT_CENTRIC,
        'attribute_centric': cls.ATTRIBUTE_CENTRIC,
    }
    if xml_style not in xml_style_mapping:
      raise bulkloader_errors.InvalidConfiguration(
          'simplexml must specify one of these valid xml_style options: "%s". '
          'You specified %s in transformer named %s.' %
          ('", "'.join(xml_style_mapping.keys()), xml_style,
           name))
    return cls(xpath_to_nodes, xml_style_mapping[xml_style])

  def __init__(self, xpath_to_nodes, xml_style):
    """Constructor.

    Args:
      xpath_to_nodes: xpath to the nodes to run over.
      xml_style: ELEMENT_CENTRIC or ATTRIBUTE_CENTRIC--we'll
        either convert the list of elements to a dict (last element of the same
        name will be used) or the list of attributes.

    Raises:
      InvalidConfiguration: If the config is invalid.
    """
    self.xpath_to_nodes = xpath_to_nodes
    assert xml_style in (self.ELEMENT_CENTRIC, self.ATTRIBUTE_CENTRIC)
    self.xml_style = xml_style
    self.output_stream = None
    self.bulkload_state = None
    self.depth = 0


    if re.match(NODE_PATH_ONLY_RE, xpath_to_nodes):
      self.node_list = self.xpath_to_nodes.split('/')[1:]
      self.entity_node = self.node_list[-1]
      self.node_list = self.node_list[:-1]
    else:
      self.node_list = None
      self.entity_node = None
      self.node_list = None

  def generate_import_record(self, filename, bulkload_state):
    """Generator, yields dicts for nodes found as described in the options."""
    self.bulkload_state = bulkload_state
    tree = ElementTree.parse(filename)
    xpath_to_nodes = self.xpath_to_nodes
    if (len(xpath_to_nodes) > 1 and xpath_to_nodes[0] == '/'
        and xpath_to_nodes[1] != '/'):


      if not tree.getroot().tag == xpath_to_nodes.split('/')[1]:
        return
      xpath_to_nodes = '/' + xpath_to_nodes.split('/', 2)[2]
    nodes = tree.findall(xpath_to_nodes)

    for node in nodes:
      if self.xml_style == self.ELEMENT_CENTRIC:
        input_dict = {}
        for child in node.getchildren():

          if not child.tag in input_dict:
            input_dict[child.tag] = child.text
      else:

        input_dict = dict(node.items())
      input_dict['__node__'] = node
      yield input_dict

  def initialize_export(self, filename, bulkload_state):
    """Initialize the output file."""
    self.bulkload_state = bulkload_state
    if not self.node_list:
      raise bulkloader_errors.InvalidConfiguration(
          'simplexml export only supports simple /root/to/node xpath_to_nodes '
          'for now.')
    self.output_stream = codecs.open(filename, 'wb', 'utf-8')

    self.output_stream.write('<?xml version="1.0"?>\n')
    self.depth = 0
    for node in self.node_list:
      self.output_stream.write('%s<%s>\n' % (' ' * self.depth, node))
      self.depth += 1
    self.indent = ' ' * self.depth

  def write_iterable_as_elements(self, values):
    """Write a dict as elements, possibly recursively."""
    if isinstance(values, dict):
      values = values.iteritems()
    for (name, value) in values:
      if isinstance(value, basestring):
        self.output_stream.write('%s <%s>%s</%s>\n' % (self.indent, name,
                                                       saxutils.escape(value),
                                                       name))
      else:

        self.output_stream.write('%s <%s>\n' % (self.indent, name))
        self.depth += 1
        self.indent = ' ' * self.depth
        self.write_iterable_as_elements(value)
        self.depth -= 1
        self.indent = ' ' * self.depth
        self.output_stream.write('%s </%s>\n' % (self.indent, name))

  def write_dict(self, dictionary):
    """Write one record for the specified entity."""
    if self.xml_style == self.ELEMENT_CENTRIC:
      self.output_stream.write('%s<%s>\n' % (self.indent, self.entity_node))
      self.write_iterable_as_elements(dictionary)
      self.output_stream.write('%s</%s>\n' % (self.indent, self.entity_node))
    else:

      self.output_stream.write('%s<%s ' % (self.indent, self.entity_node))
      for (name, value) in dictionary.iteritems():
        self.output_stream.write('%s=%s ' % (name, saxutils.quoteattr(value)))
      self.output_stream.write('/>\n')

  def finalize_export(self):
    if not self.output_stream:
      return
    for node in reversed(self.node_list):
      self.depth -= 1
      self.output_stream.write('%s</%s>\n' % (' ' * self.depth, node))
    self.output_stream.close()
    self.output_stream = None
