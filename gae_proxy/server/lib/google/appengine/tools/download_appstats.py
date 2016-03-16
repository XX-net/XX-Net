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
"""Script for downloading Appstats data using remote_api.

Usage:
  %prog [-s HOSTNAME] [-p PATH] [-o OUTPUTFILE] [-j] [-q] [-m] [APPID]

If the -s HOSTNAME flag is not specified, the APPID must be specified.
"""




from google.appengine.tools import os_compat

import getpass
import logging
import optparse
import os
import sys

from google.appengine.ext.appstats import loader
from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.tools import appengine_rpc



DEFAULT_PATH_PYTHON = '/_ah/remote_api'
DEFAULT_PATH_JAVA = '/remote_api'
DEFAULT_FILE = 'appstats.pkl'


def auth_func():
  return (raw_input('Email: '), getpass.getpass('Password: '))


def download_appstats(servername, appid, path, secure,
                      rpc_server_factory, filename, appdir,
                      merge, java_application):
  """Invoke remote_api to download appstats data."""




  if os.path.isdir(appdir):
    sys.path.insert(0, appdir)
    try:
      logging.info('Importing appengine_config from %s', appdir)
      import appengine_config
    except ImportError, err:
      logging.warn('Failed to load appengine_config: %s', err)


  remote_api_stub.ConfigureRemoteApi(appid, path, auth_func,
                                     servername=servername,
                                     save_cookies=True, secure=secure,
                                     rpc_server_factory=rpc_server_factory)
  remote_api_stub.MaybeInvokeAuthentication()


  os.environ['SERVER_SOFTWARE'] = 'Development (remote_api_shell)/1.0'

  if not appid:

    appid = os.environ['APPLICATION_ID']
  download_data(filename, merge, java_application)


def download_data(filename, merge, java_application):
  """Download appstats data from memcache."""
  oldrecords = []
  oldfile = None



  if merge:
    try:
      oldfile = open(filename, 'rb')
    except IOError:
      logging.info('No file to merge. Creating new file %s',
                   filename)
  if oldfile:
    logging.info('Merging with existing file %s', filename)
    oldrecords = loader.UnpickleFromFile(oldfile)
    oldfile.close()
  if oldrecords:

    last_timestamp = oldrecords[0].start_timestamp_milliseconds()
    records = loader.FromMemcache(filter_timestamp=last_timestamp,
                                  java_application=java_application)
  else:
    records = loader.FromMemcache(java_application=java_application)

  merged_records = records + oldrecords
  try:
    outfile = open(filename, 'wb')
  except IOError:
    logging.error('Cannot open %s', filename)
    return
  loader.PickleToFile(merged_records, outfile)
  outfile.close()


def main(argv):
  """Parse arguments and run shell."""
  parser = optparse.OptionParser(usage=__doc__)
  parser.add_option('-s', '--server', dest='server',
                    help='The hostname your app is deployed on. '
                         'Defaults to <app_id>.appspot.com.')
  parser.add_option('-o', '--output', dest='filename', default=DEFAULT_FILE,
                    help='The file to which Appstats data must '
                         'be downloaded. A .pkl extension is '
                         'recommended. Defaults to %s.' % DEFAULT_FILE)
  parser.add_option('-p', '--path', dest='path',
                    help='The path on the server to the remote_api handler. '
                         'Defaults to %s for python and %s for java. '
                         % (DEFAULT_PATH_PYTHON, DEFAULT_PATH_JAVA))
  parser.add_option('-q', '--quiet',
                    action='store_false', dest='verbose', default=True,
                    help='do not print download status messages to stdout')
  parser.add_option('-j', '--java',
                    action='store_true', dest='java_application', default=False,
                    help='set this for downloading from a java application')
  parser.add_option('-m', '--merge',
                    action='store_true', dest='merge', default=False,
                    help='if file exists, merge rather than overwrite')
  parser.add_option('--secure', dest='secure', action='store_true',
                    default=False, help='Use HTTPS when communicating '
                                        'with the server.')
  parser.add_option('--appdir', dest='appdir', action='store', default='.',
                    help='application directory, for finding '
                         'appengine_config.py. Defaults to ".".')
  (options, args) = parser.parse_args()


  if ((not options.server and not args) or len(args) > 2
      or (options.path and len(args) > 1)):
    parser.print_usage(sys.stderr)
    if len(args) > 2:
      print >> sys.stderr, 'Unexpected arguments: %s' % args[2:]
    elif options.path and len(args) > 1:
      print >> sys.stderr, 'Path specified twice.'
    sys.exit(1)


  servername = options.server
  appid = None
  if options.java_application:
    default_path = DEFAULT_PATH_JAVA
  else:
    default_path = DEFAULT_PATH_PYTHON
  path = options.path or default_path
  if args:
    if servername:

      appid = args[0]
    else:

      servername = '%s.appspot.com' % args[0]
    if len(args) == 2:

      path = args[1]
  if options.verbose:


    logging.getLogger().setLevel(logging.INFO)
  download_appstats(servername, appid, path, options.secure,
                    appengine_rpc.HttpRpcServer, options.filename,
                    options.appdir, options.merge, options.java_application)


if __name__ == '__main__':
  main(sys.argv)
