# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This module holds the old run() function which is deprecated, the
tools.run_flow() function should be used in its place."""

from __future__ import print_function

import logging
import socket
import sys
import webbrowser

import gflags
from six.moves import input

from oauth2client import client
from oauth2client import util
from oauth2client.tools import ClientRedirectHandler
from oauth2client.tools import ClientRedirectServer


FLAGS = gflags.FLAGS

gflags.DEFINE_boolean('auth_local_webserver', True,
                      ('Run a local web server to handle redirects during '
                       'OAuth authorization.'))

gflags.DEFINE_string('auth_host_name', 'localhost',
                     ('Host name to use when running a local web server to '
                      'handle redirects during OAuth authorization.'))

gflags.DEFINE_multi_int('auth_host_port', [8080, 8090],
                        ('Port to use when running a local web server to '
                         'handle redirects during OAuth authorization.'))


@util.positional(2)
def run(flow, storage, http=None):
  """Core code for a command-line application.

  The ``run()`` function is called from your application and runs
  through all the steps to obtain credentials. It takes a ``Flow``
  argument and attempts to open an authorization server page in the
  user's default web browser. The server asks the user to grant your
  application access to the user's data. If the user grants access,
  the ``run()`` function returns new credentials. The new credentials
  are also stored in the ``storage`` argument, which updates the file
  associated with the ``Storage`` object.

  It presumes it is run from a command-line application and supports the
  following flags:

    ``--auth_host_name`` (string, default: ``localhost``)
       Host name to use when running a local web server to handle
       redirects during OAuth authorization.

    ``--auth_host_port`` (integer, default: ``[8080, 8090]``)
       Port to use when running a local web server to handle redirects
       during OAuth authorization. Repeat this option to specify a list
       of values.

    ``--[no]auth_local_webserver`` (boolean, default: ``True``)
       Run a local web server to handle redirects during OAuth authorization.

  Since it uses flags make sure to initialize the ``gflags`` module before
  calling ``run()``.

  Args:
    flow: Flow, an OAuth 2.0 Flow to step through.
    storage: Storage, a ``Storage`` to store the credential in.
    http: An instance of ``httplib2.Http.request`` or something that acts
        like it.

  Returns:
    Credentials, the obtained credential.
  """
  logging.warning('This function, oauth2client.tools.run(), and the use of '
      'the gflags library are deprecated and will be removed in a future '
      'version of the library.')
  if FLAGS.auth_local_webserver:
    success = False
    port_number = 0
    for port in FLAGS.auth_host_port:
      port_number = port
      try:
        httpd = ClientRedirectServer((FLAGS.auth_host_name, port),
                                     ClientRedirectHandler)
      except socket.error as e:
        pass
      else:
        success = True
        break
    FLAGS.auth_local_webserver = success
    if not success:
      print('Failed to start a local webserver listening on either port 8080')
      print('or port 9090. Please check your firewall settings and locally')
      print('running programs that may be blocking or using those ports.')
      print()
      print('Falling back to --noauth_local_webserver and continuing with')
      print('authorization.')
      print()

  if FLAGS.auth_local_webserver:
    oauth_callback = 'http://%s:%s/' % (FLAGS.auth_host_name, port_number)
  else:
    oauth_callback = client.OOB_CALLBACK_URN
  flow.redirect_uri = oauth_callback
  authorize_url = flow.step1_get_authorize_url()

  if FLAGS.auth_local_webserver:
    webbrowser.open(authorize_url, new=1, autoraise=True)
    print('Your browser has been opened to visit:')
    print()
    print('    ' + authorize_url)
    print()
    print('If your browser is on a different machine then exit and re-run')
    print('this application with the command-line parameter ')
    print()
    print('  --noauth_local_webserver')
    print()
  else:
    print('Go to the following link in your browser:')
    print()
    print('    ' + authorize_url)
    print()

  code = None
  if FLAGS.auth_local_webserver:
    httpd.handle_request()
    if 'error' in httpd.query_params:
      sys.exit('Authentication request was rejected.')
    if 'code' in httpd.query_params:
      code = httpd.query_params['code']
    else:
      print('Failed to find "code" in the query parameters of the redirect.')
      sys.exit('Try running with --noauth_local_webserver.')
  else:
    code = input('Enter verification code: ').strip()

  try:
    credential = flow.step2_exchange(code, http=http)
  except client.FlowExchangeError as e:
    sys.exit('Authentication has failed: %s' % e)

  storage.put(credential)
  credential.set_store(storage)
  print('Authentication successful.')

  return credential
