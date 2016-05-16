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





"""Bulkloader CSV reading and writing.

Handle the CSV format specified in a bulkloader.yaml file.
"""












import codecs
import cStringIO
import csv
import encodings
import encodings.ascii
import encodings.cp1252
import encodings.latin_1
import encodings.utf_8

from google.appengine.ext.bulkload import bulkloader_errors
from google.appengine.ext.bulkload import connector_interface


def utf8_recoder(stream, encoding):
  """Generator that reads an encoded stream and reencodes to UTF-8."""


  for line in codecs.getreader(encoding)(stream):
    yield line.encode('utf-8')


class UnicodeDictWriter(object):
  """Based on UnicodeWriter in http://docs.python.org/library/csv.html."""

  def __init__(self, stream, fieldnames, encoding='utf-8', **kwds):
    """Initialzer.

    Args:
      stream: Stream to write to.
      fieldnames: Fieldnames to pass to the DictWriter.
      encoding: Desired encoding.
      kwds: Additional arguments to pass to the DictWriter.
    """

    writer = codecs.getwriter(encoding)



    if (writer is encodings.utf_8.StreamWriter or
        writer is encodings.ascii.StreamWriter or
        writer is encodings.latin_1.StreamWriter or
        writer is encodings.cp1252.StreamWriter):
      self.no_recoding = True
      self.encoder = codecs.getencoder(encoding)
      self.writer = csv.DictWriter(stream, fieldnames, **kwds)
    else:
      self.no_recoding = False
      self.encoder = codecs.getencoder('utf-8')
      self.queue = cStringIO.StringIO()
      self.writer = csv.DictWriter(self.queue, fieldnames, **kwds)
      self.stream = writer(stream)

  def writerow(self, row):
    """Wrap writerow method."""
    row_encoded = dict([(k, self.encoder(v)[0]) for (k, v) in row.iteritems()])
    self.writer.writerow(row_encoded)
    if self.no_recoding:
      return


    data = self.queue.getvalue()
    data = data.decode('utf-8')
    self.stream.write(data)

    self.queue.truncate(0)


class CsvConnector(connector_interface.ConnectorInterface):
  """Read/write a (possibly encoded) CSV file."""

  @classmethod
  def create_from_options(cls, options, name):
    """Factory using an options dictionary.

    Args:
      options: Dictionary of options:
        columns: 'from_header' or blank.
        column_list: overrides columns specifically.
        encoding: encoding of the file. e.g. 'utf-8' (default), 'windows-1252'.
        skip_import_header_row: True to ignore the header line on import.
          Defaults False, except must be True if columns=from_header.
        print_export_header_row: True to print a header line on export.
          Defaults to False except if columns=from_header.
        import_options: Other kwargs to pass in, like "dialect".
        export_options: Other kwargs to pass in, like "dialect".
      name: The name of this transformer, for use in error messages.

    Returns:
      CsvConnector object described by the specified options.

    Raises:
      InvalidConfiguration: If the config is invalid.
    """
    column_list = options.get('column_list', None)
    columns = None
    if not column_list:
      columns = options.get('columns', 'from_header')
      if columns != 'from_header':
        raise bulkloader_errors.InvalidConfiguration(
            'CSV columns must be "from_header", or a column_list '
            'must be specified. (In transformer name %s.)' % name)
    csv_encoding = options.get('encoding', 'utf-8')















    skip_import_header_row = options.get('skip_import_header_row',
                                         columns == 'from_header')
    if columns == 'from_header' and not skip_import_header_row:
      raise bulkloader_errors.InvalidConfiguration(
          'When CSV columns are "from_header", the header row must always '
          'be skipped. (In transformer name %s.)' % name)
    print_export_header_row = options.get('print_export_header_row',
                                          columns == 'from_header')
    import_options = options.get('import_options', {})
    export_options = options.get('export_options', {})
    return cls(columns, column_list, skip_import_header_row,
               print_export_header_row, csv_encoding, import_options,
               export_options)

  def __init__(self, columns, column_list, skip_import_header_row,
               print_export_header_row, csv_encoding=None,
               import_options=None, export_options=None):
    """Initializer.

    Args:
      columns: 'from_header' or blank
      column_list: overrides columns specifically.
      skip_import_header_row: True to ignore the header line on import.
        Defaults False, except must be True if columns=from_header.
      print_export_header_row: True to print a header line on export.
        Defaults to False except if columns=from_header.
      csv_encoding: encoding of the file.
      import_options: Other kwargs to pass in, like "dialect".
      export_options: Other kwargs to pass in, like "dialect".
    """

    self.columns = columns
    self.from_header = (columns == 'from_header')
    self.column_list = column_list
    self.skip_import_header_row = skip_import_header_row
    self.print_export_header_row = print_export_header_row
    self.csv_encoding = csv_encoding
    self.dict_generator = None
    self.output_stream = None
    self.csv_writer = None
    self.bulkload_state = None
    self.import_options = import_options or {}
    self.export_options = export_options or {}

  def generate_import_record(self, filename, bulkload_state):
    """Generator, yields dicts for nodes found as described in the options.

    Args:
      filename: Filename to read.
      bulkload_state: Passed bulkload_state.

    Yields:
      Neutral dict, one per row in the CSV file.
    """
    self.bulkload_state = bulkload_state
    input_stream = open(filename)
    input_stream = utf8_recoder(input_stream, self.csv_encoding)

    self.dict_generator = csv.DictReader(input_stream, self.column_list,
                                         **self.import_options)

    discard_line = self.skip_import_header_row and not self.from_header

    line_number = 0
    for input_dict in self.dict_generator:
      line_number = line_number + 1
      if discard_line:
        discard_line = False
        continue




      decoded_dict = {}
      for key, value in input_dict.iteritems():
        if key == None:
          raise bulkloader_errors.InvalidImportData(
              'Got more values in row than headers on line %d.'
              % (line_number))
        if not self.column_list:

          key = unicode(key, 'utf-8')
        if value:
          value = unicode(value, 'utf-8')
        decoded_dict[key] = value
      yield decoded_dict

  def initialize_export(self, filename, bulkload_state):
    """Initialize the output file.

    Args:
      filename: Filename to write.
      bulkload_state: Passed bulkload_state.
    """
    self.bulkload_state = bulkload_state

    self.output_stream = open(filename, 'wb')

  def __initialize_csv_writer(self, dictionary):
    """Actual initialization, happens on the first entity being written."""
    write_header = self.print_export_header_row
    if self.from_header:


      export_column_list = tuple(dictionary)
    else:
      export_column_list = self.column_list

    self.csv_writer = UnicodeDictWriter(self.output_stream, export_column_list,
                                        self.csv_encoding,
                                        **self.export_options)
    if write_header:
      self.csv_writer.writerow(dict(zip(export_column_list,
                                        export_column_list)))

  def write_dict(self, dictionary):
    """Write one record for the specified entity."""
    if not self.csv_writer:
      self.__initialize_csv_writer(dictionary)
    self.csv_writer.writerow(dictionary)

  def finalize_export(self):
    self.output_stream.close()
