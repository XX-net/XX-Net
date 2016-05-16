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





"""Bulkloader Simple Text writing.

Handle the simpletext format specified in a bulkloader.yaml file.
"""











from google.appengine.ext.bulkload import bulkloader_errors
from google.appengine.ext.bulkload import connector_interface


class SimpleTextConnector(connector_interface.ConnectorInterface):
  """Write a text file from dicts for each record. Does not support import."""

  VALID_MODES = ('text', 'nonewline', 'binary')

  @classmethod
  def create_from_options(cls, options, name):
    """Factory using an options dictionary.

    Args:
      options: Dictionary of options containing:
        template: A Python dict-interpolation string. Required.
        prolog: written before the per-record output.
        epilog: written after the per-record output.
        mode: one of the following, default is 'text'
          text: text file mode, newlines between records.
          nonewline: text file mode, no added newlines.
          binary: binary file mode, no added newlines.
      name: The name of this transformer, for use in error messages.

    Returns:
      SimpleTextConnector object described by the specified options.

    Raises:
      InvalidConfiguration: If the config is invalid.
    """
    template = options.get('template')
    if not template:
      raise bulkloader_errors.InvalidConfiguration(
          'simpletext must specify template. (In transformer named %s)' % name)

    prolog = options.get('prolog')
    epilog = options.get('epilog')
    mode = options.get('mode', 'text')
    return cls(template, prolog, epilog, mode, name)

  def __init__(self, template, prolog=None, epilog=None, mode='text', name=''):
    """Constructor.

    Args:
      template: A Python dict-interpolation string.
      prolog: written before the per-record output.
      epilog: written after the per-record output.
      mode: one of the following, default is 'text'
        text: text file mode, newlines between records.
        nonewline: text file mode, no added newlines.
        binary: binary file mode, no added newlines.
    """
    if mode not in self.VALID_MODES:
      raise bulkloader_errors.InvalidConfiguration(
          'simpletext mode must be one of "%s". (In transformer name %s.)' %
          ('", "'.join(self.VALID_MODES), name))
    self.template = template
    self.prolog = prolog
    self.epilog = epilog
    self.mode = mode
    self.export_file_pointer = None

  def initialize_export(self, filename, bulkload_state):
    """Open file and write prolog."""
    self.bulkload_state = bulkload_state
    mode = 'w'
    if self.mode == 'binary':
      mode = 'wb'
    self.export_file_pointer = open(filename, mode)
    if self.prolog:
      self.export_file_pointer.write(self.prolog)
      if self.mode == 'text':
        self.export_file_pointer.write('\n')

  def write_dict(self, dictionary):
    """Write one record for the specified entity."""
    self.export_file_pointer.write(self.template % dictionary)
    if self.mode == 'text':
      self.export_file_pointer.write('\n')

  def finalize_export(self):
    """Write epliog and close file after every record is written."""
    if self.epilog:
      self.export_file_pointer.write(self.epilog)
      if self.mode == 'text':
        self.export_file_pointer.write('\n')
    self.export_file_pointer.close()
