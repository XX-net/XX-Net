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
"""Imports CSV data over HTTP.

Usage:
  %s [flags]

    --debug             Show debugging information. (Optional)
    --cookie=<string>   Whole Cookie header to supply to the server, including
                        the parameter name (e.g., "ACSID=..."). (Optional)
    --url=<string>      URL endpoint to post to for importing data. (Required)
    --batch_size=<int>  Number of Entity objects to include in each post to
                        the URL endpoint. The more data per row/Entity, the
                        smaller the batch size should be. (Default 10)
    --filename=<path>   Path to the CSV file to import. (Required)
    --kind=<string>     Name of the Entity object kind to put in the datastore.
                        (Required)

The exit status will be 0 on success, non-zero on import failure.

Works with the bulkload mix-in library for google.appengine.ext.bulkload.
Please look there for documentation about how to setup the server side.
"""



import StringIO
import httplib
import logging
import csv
import getopt
import socket
import sys
import urllib
import urlparse

from google.appengine.ext.bulkload import constants





class Error(Exception):
  """Base-class for exceptions in this module."""


class PostError(Error):
  """An error has occured while trying to post data to the server."""


class BadServerStatusError(PostError):
  """The server has returned an error while importing data."""



def ContentGenerator(csv_file,
                     batch_size,
                     create_csv_reader=csv.reader,
                     create_csv_writer=csv.writer):
  """Retrieves CSV data up to a batch size at a time.

  Args:
    csv_file: A file-like object for reading CSV data.
    batch_size: Maximum number of CSV rows to yield on each iteration.
    create_csv_reader, create_csv_writer: Used for dependency injection.

  Yields:
    Tuple (entity_count, csv_content) where:
      entity_count: Number of entities contained in the csv_content. Will be
        less than or equal to the batch_size and greater than 0.
      csv_content: String containing the CSV content containing the next
        entity_count entities.
  """
  try:
    csv.field_size_limit(800000)
  except AttributeError:

    pass

  reader = create_csv_reader(csv_file, skipinitialspace=True)
  exhausted = False

  while not exhausted:
    rows_written = 0
    content = StringIO.StringIO()
    writer = create_csv_writer(content)
    try:
      for i in xrange(batch_size):
        row = reader.next()
        writer.writerow(row)
        rows_written += 1
    except StopIteration:
      exhausted = True

    if rows_written > 0:
      yield rows_written, content.getvalue()


def PostEntities(host_port, uri, cookie, kind, content):
  """Posts Entity records to a remote endpoint over HTTP.

  Args:
   host_port: String containing the "host:port" pair; the port is optional.
   uri: Relative URI to access on the remote host (e.g., '/bulkload').
   cookie: String containing the Cookie header to use, if any.
   kind: Kind of the Entity records being posted.
   content: String containing the CSV data for the entities.

  Raises:
    BadServerStatusError if the server was contactable but returns an error.
    PostError If an error occurred while connecting to the server or reading
    or writing data.
  """
  logging.debug('Connecting to %s', host_port)
  try:
    body = urllib.urlencode({
      constants.KIND_PARAM: kind,
      constants.CSV_PARAM: content,
    })
    headers = {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Content-Length': len(body),
      'Cookie': cookie,
    }

    logging.debug('Posting %d bytes to http://%s%s', len(body), host_port, uri)
    connection = httplib.HTTPConnection(host_port)
    try:
      connection.request('POST', uri, body, headers)
      response = connection.getresponse()

      status = response.status
      reason = response.reason
      content = response.read()
      logging.debug('Received response code %d: %s', status, reason)
      if status != httplib.OK:
        raise BadServerStatusError('Received code %d: %s\n%s' % (
                                   status, reason, content))
    finally:
      connection.close()
  except (IOError, httplib.HTTPException, socket.error), e:
    logging.debug('Encountered exception accessing HTTP server: %s', e)
    raise PostError(e)


def SplitURL(url):
  """Splits an HTTP URL into pieces.

  Args:
    url: String containing a full URL string (e.g.,
      'http://blah.com:8080/stuff?param=1#foo')

  Returns:
    Tuple (netloc, uri) where:
      netloc: String containing the host/port combination from the URL. The
        port is optional. (e.g., 'blah.com:8080').
      uri: String containing the relative URI of the URL. (e.g., '/stuff').
  """
  scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
  return netloc, path


def ImportCSV(filename,
              post_url,
              cookie,
              batch_size,
              kind,
              split_url=SplitURL,
              openfile=file,
              create_content_generator=ContentGenerator,
              post_entities=PostEntities):
  """Imports CSV data using a series of HTTP posts.

  Args:
    filename: File on disk containing CSV data.
    post_url: URL to post the Entity data to.
    cookie: Full cookie header to use while connecting.
    batch_size: Maximum number of Entity objects to post with each request.
    kind: Entity kind of the objects being posted.
    split_url, openfile, create_content_generator, post_entities: Used for
      dependency injection.

  Returns:
    True if all entities were imported successfully; False otherwise.
  """
  host_port, uri = split_url(post_url)
  csv_file = openfile(filename, 'r')
  try:
    content_gen = create_content_generator(csv_file, batch_size)
    logging.info('Starting import; maximum %d entities per post', batch_size)
    for num_entities, content in content_gen:
      logging.info('Importing %d entities in %d bytes',
                   num_entities, len(content))
      try:
        content = post_entities(host_port, uri, cookie, kind, content)
      except PostError, e:
        logging.error('An error occurred while importing: %s', e)
        return False
  finally:
    csv_file.close()
  return True



def PrintUsageExit(code):
  """Prints usage information and exits with a status code.

  Args:
    code: Status code to pass to sys.exit() after displaying usage information.
  """
  print sys.modules['__main__'].__doc__ % sys.argv[0]
  sys.stdout.flush()
  sys.stderr.flush()
  sys.exit(code)


def ParseArguments(argv):
  """Parses command-line arguments.

  Prints out a help message if -h or --help is supplied.

  Args:
    argv: List of command-line arguments.

  Returns:
    Tuple (url, filename, cookie, batch_size, kind) containing the values from
    each corresponding command-line flag.
  """
  opts, args = getopt.getopt(
    argv[1:],
    'h',
    ['debug',
     'help',
     'url=',
     'filename=',
     'cookie=',
     'batch_size=',
     'kind='])

  url = None
  filename = None
  cookie = ''
  batch_size = 10
  kind = None
  encoding = None

  for option, value in opts:
    if option == '--debug':
      logging.getLogger().setLevel(logging.DEBUG)
    if option in ('-h', '--help'):
      PrintUsageExit(0)
    if option == '--url':
      url = value
    if option == '--filename':
      filename = value
    if option == '--cookie':
      cookie = value
    if option == '--batch_size':
      batch_size = int(value)
      if batch_size <= 0:
        print >>sys.stderr, 'batch_size must be 1 or larger'
        PrintUsageExit(1)
    if option == '--kind':
      kind = value

  return (url, filename, cookie, batch_size, kind)


def main(argv):
  """Runs the importer."""
  logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-8s %(asctime)s %(filename)s] %(message)s')


  args = ParseArguments(argv)
  if [arg for arg in args if arg is None]:
    print >>sys.stderr, 'Invalid arguments'
    PrintUsageExit(1)

  url, filename, cookie, batch_size, kind = args
  if ImportCSV(filename, url, cookie, batch_size, kind):
    logging.info('Import succcessful')
    return 0
  logging.error('Import failed')
  return 1



if __name__ == '__main__':
  sys.exit(main(sys.argv))
