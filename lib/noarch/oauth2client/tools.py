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

"""Command-line tools for authenticating via OAuth 2.0

Do the OAuth 2.0 Web Server dance for a command line application. Stores the
generated credentials in a common file that is used by other example apps in
the same directory.
"""

from __future__ import print_function

import logging
import socket
import sys

from six.moves import BaseHTTPServer
from six.moves import http_client
from six.moves import urllib
from six.moves import input

from oauth2client import client
from oauth2client import util


__author__ = 'jcgregorio@google.com (Joe Gregorio)'
__all__ = ['argparser', 'run_flow', 'message_if_missing']

_CLIENT_SECRETS_MESSAGE = """WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the APIs Console <https://code.google.com/apis/console>.

"""


def _CreateArgumentParser():
    try:
        import argparse
    except ImportError:
        return None
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--auth_host_name', default='localhost',
                        help='Hostname when running a local web server.')
    parser.add_argument('--noauth_local_webserver', action='store_true',
                        default=False, help='Do not run a local web server.')
    parser.add_argument('--auth_host_port', default=[8080, 8090], type=int,
                        nargs='*', help='Port web server should listen on.')
    parser.add_argument(
        '--logging_level', default='ERROR',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level of detail.')
    return parser

# argparser is an ArgumentParser that contains command-line options expected
# by tools.run(). Pass it in as part of the 'parents' argument to your own
# ArgumentParser.
argparser = _CreateArgumentParser()


class ClientRedirectServer(BaseHTTPServer.HTTPServer):
    """A server to handle OAuth 2.0 redirects back to localhost.

    Waits for a single request and parses the query parameters
    into query_params and then stops serving.
    """
    query_params = {}


class ClientRedirectHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """A handler for OAuth 2.0 redirects back to localhost.

    Waits for a single request and parses the query parameters
    into the servers query_params and then stops serving.
    """

    def do_GET(self):
        """Handle a GET request.

        Parses the query parameters and prints a message
        if the flow has completed. Note that we can't detect
        if an error occurred.
        """
        self.send_response(http_client.OK)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        query = self.path.split('?', 1)[-1]
        query = dict(urllib.parse.parse_qsl(query))
        self.server.query_params = query
        self.wfile.write(
            b"<html><head><title>Authentication Status</title></head>")
        self.wfile.write(
            b"<body><p>The authentication flow has completed.</p>")
        self.wfile.write(b"</body></html>")

    def log_message(self, format, *args):
        """Do not log messages to stdout while running as cmd. line program."""


@util.positional(3)
def run_flow(flow, storage, flags=None, http=None):
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
           Run a local web server to handle redirects during OAuth
           authorization.

    The tools module defines an ``ArgumentParser`` the already contains the
    flag definitions that ``run()`` requires. You can pass that
    ``ArgumentParser`` to your ``ArgumentParser`` constructor::

        parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[tools.argparser])
        flags = parser.parse_args(argv)

    Args:
        flow: Flow, an OAuth 2.0 Flow to step through.
        storage: Storage, a ``Storage`` to store the credential in.
        flags: ``argparse.Namespace``, (Optional) The command-line flags. This
               is the object returned from calling ``parse_args()`` on
               ``argparse.ArgumentParser`` as described above. Defaults
               to ``argparser.parse_args()``.
        http: An instance of ``httplib2.Http.request`` or something that
              acts like it.

    Returns:
        Credentials, the obtained credential.
    """
    if flags is None:
        flags = argparser.parse_args()
    logging.getLogger().setLevel(getattr(logging, flags.logging_level))
    if not flags.noauth_local_webserver:
        success = False
        port_number = 0
        for port in flags.auth_host_port:
            port_number = port
            try:
                httpd = ClientRedirectServer((flags.auth_host_name, port),
                                             ClientRedirectHandler)
            except socket.error:
                pass
            else:
                success = True
                break
        flags.noauth_local_webserver = not success
        if not success:
            print('Failed to start a local webserver listening '
                  'on either port 8080')
            print('or port 8090. Please check your firewall settings and locally')
            print('running programs that may be blocking or using those ports.')
            print()
            print('Falling back to --noauth_local_webserver and continuing with')
            print('authorization.')
            print()

    if not flags.noauth_local_webserver:
        oauth_callback = 'http://%s:%s/' % (flags.auth_host_name, port_number)
    else:
        oauth_callback = client.OOB_CALLBACK_URN
    flow.redirect_uri = oauth_callback
    authorize_url = flow.step1_get_authorize_url()

    if not flags.noauth_local_webserver:
        import webbrowser
        webbrowser.open(authorize_url, new=1, autoraise=True)
        print('Your browser has been opened to visit:')
        print()
        print('    ' + authorize_url)
        print()
        print('If your browser is on a different machine then '
              'exit and re-run this')
        print('application with the command-line parameter ')
        print()
        print('  --noauth_local_webserver')
        print()
    else:
        print('Go to the following link in your browser:')
        print()
        print('    ' + authorize_url)
        print()

    code = None
    if not flags.noauth_local_webserver:
        httpd.handle_request()
        if 'error' in httpd.query_params:
            sys.exit('Authentication request was rejected.')
        if 'code' in httpd.query_params:
            code = httpd.query_params['code']
        else:
            print('Failed to find "code" in the query parameters '
                  'of the redirect.')
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


def message_if_missing(filename):
    """Helpful message to display if the CLIENT_SECRETS file is missing."""
    return _CLIENT_SECRETS_MESSAGE % filename
