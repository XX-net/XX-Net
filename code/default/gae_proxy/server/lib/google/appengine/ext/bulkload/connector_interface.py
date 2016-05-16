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





"""Bulkloader interfaces for the format reader/writers."""












class ConnectorInterface(object):
  """Abstract base class describing the external Connector interface.

  The External Connector interface describes the transition between an external
  data source, e.g. CSV file, XML file, or some sort of database interface, and
  the intermediate bulkloader format, which is a dictionary or similar
  structure representing the external transformation of the data.

  On import, the generate_import_record generator is the only method called.

  On export, the initialize_export method is called once, followed by a call
  to write_dict for each record, followed by a call to finalize_export.

  The bulkload_state is a BulkloadState object from
  google.appengine.ext.bulkload.bulkload_config. The interesting properties
  to a Connector object are the loader_opts and exporter_opts, which are strings
  passed in from the bulkloader command line.
  """


  def generate_import_record(self, filename, bulkload_state):
    """A function which returns an iterator over dictionaries.

    This is the only method used on import.

    Args:
      filename: The --filename argument passed in on the bulkloader command
        line. This value is opaque to the bulkloader and thus could specify
        any sort of descriptor for your generator.
      bulkload_state: Passed in BulkloadConfig.BulkloadState object.

    Returns:
      An iterator describing an individual record. Typically a dictionary,
      to be used with dict_to_model. Typically implemented as a generator.
    """

    raise NotImplementedError


  def initialize_export(self, filename, bulkload_state):
    """Initialize the output file.

    Args:
      filename: The string given as the --filename flag argument.
      bulkload_state: Passed in BulkloadConfig.BulkloadState object.

    These values are opaque to the bulkloader and thus could specify
    any sort of descriptor for your exporter.
    """
    raise NotImplementedError

  def write_dict(self, dictionary):
    """Write one record for the specified entity.

    Args:
      dictionary: A post-transform dictionary.
    """
    raise NotImplementedError

  def finalize_export(self):
    """Performs finalization actions after every record is written."""
    raise NotImplementedError


def create_from_options(options, name='unknown'):
  """Factory using an options dictionary.

  This is frequently implemented as the constructor on the connector class,
  or a static or class method on the connector class.

  Args:
    options: Parsed dictionary from yaml file, interpretation is up to the
      implementor of this class.
    name: Identifier of this transform to be used in error messages.

  Returns:
    An object which implements the  ConnectorInterface interface.
  """
  raise NotImplementedError
