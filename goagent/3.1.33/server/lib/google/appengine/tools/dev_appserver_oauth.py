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




"""Helper CGI for OAuth in the development app server."""



import cgi



_GET_REQUEST_TOKEN_URL = '/_ah/OAuthGetRequestToken'
_AUTHORIZE_TOKEN_URL = '/_ah/OAuthAuthorizeToken'
_GET_ACCESS_TOKEN_URL = '/_ah/OAuthGetAccessToken'


_OAUTH_CALLBACK_PARAM = 'oauth_callback'


OAUTH_URL_PATTERN = (_GET_REQUEST_TOKEN_URL
                     + '|' + _AUTHORIZE_TOKEN_URL
                     + '|' + _GET_ACCESS_TOKEN_URL)



TOKEN_APPROVAL_TEMPLATE = """<html>
<head>
  <title>OAuth Access Request</title>
</head>
<body>

<form method="POST">
  <div style="width: 20em; margin: 1em auto;
              text-align: left;
              padding: 0 2em 1.25em 2em;
              background-color: #d6e9f8;
              font: 13px sans-serif;
              border: 2px solid #67a7e3">
    <h3>OAuth Access Request</h3>
    <input type="hidden" name="oauth_callback" value="%(oauth_callback)s"/>
    <p style="margin-left: 3em;">
      <input name="action" type="submit" value="Grant Access"/>
    </p>
  </div>
</form>

</body>
</html>
"""


TOKEN_APPROVED_TEMPLATE = """<html>
<head>
  <title>OAuth Access Granted</title>
</head>
<body>

<div style="width: 20em; margin: 1em auto;
            text-align: left;
            padding: 0 2em 1.25em 2em;
            background-color: #d6e9f8;
            font: 13px sans-serif;
            border: 2px solid #67a7e3">
  <h3>OAuth Access Granted</h3>
</div>

</body>
</html>
"""


def RenderTokenApprovalTemplate(oauth_callback):
  """Renders the token approval page.

  Args:
    oauth_callback: Parameter passed to OAuthAuthorizeTokenCGI.

  Returns:
    String containing the contents of the token approval page.
  """
  template_dict = {
      'oauth_callback': cgi.escape(oauth_callback, quote=True),
  }

  return TOKEN_APPROVAL_TEMPLATE % template_dict


def RenderTokenApprovedTemplate():
  """Renders the token approved page.

  Returns:
    String containing the contents of the token approved page.
  """
  return TOKEN_APPROVED_TEMPLATE


def OAuthGetRequestTokenCGI(outfile):
  """Runs the OAuthGetRequestToken CGI.

  Args:
    outfile: File-like object to which all output data should be written.
  """
  outfile.write('Status: 200\r\n')
  outfile.write('Content-Type: text/plain\r\n')
  outfile.write('\r\n')
  outfile.write('oauth_token=REQUEST_TOKEN')
  outfile.write('&')
  outfile.write('oauth_token_secret=REQUEST_TOKEN_SECRET')


def OAuthAuthorizeTokenCGI(method, parameters, outfile):
  """Runs the OAuthAuthorizeToken CGI.

  Args:
    method: HTTP method
    parameters: Dictionary of parameters from the request.
    outfile: File-like object to which all output data should be written.
  """
  oauth_callback = GetFirst(parameters, _OAUTH_CALLBACK_PARAM, '')
  if method == 'GET':
    outfile.write('Status: 200\r\n')
    outfile.write('Content-Type: text/html\r\n')
    outfile.write('\r\n')
    outfile.write(RenderTokenApprovalTemplate(oauth_callback))
  elif method == 'POST':
    if oauth_callback:
      outfile.write('Status: 302 Redirecting to callback URL\r\n')
      outfile.write('Location: %s\r\n' % oauth_callback)
      outfile.write('\r\n')
    else:
      outfile.write('Status: 200\r\n')
      outfile.write('Content-Type: text/html\r\n')
      outfile.write('\r\n')
      outfile.write(RenderTokenApprovedTemplate())
  else:
    outfile.write('Status: 400 Unsupported method\r\n')


def OAuthGetAccessTokenCGI(outfile):
  """Runs the OAuthGetAccessToken CGI.

  Args:
    outfile: File-like object to which all output data should be written.
  """
  outfile.write('Status: 200\r\n')
  outfile.write('Content-Type: text/plain\r\n')
  outfile.write('\r\n')
  outfile.write('oauth_token=ACCESS_TOKEN')
  outfile.write('&')
  outfile.write('oauth_token_secret=ACCESS_TOKEN_SECRET')


def GetFirst(parameters, key, default=None):
  """Returns the first value of the given key.

  Args:
    parameters: A dictionary of lists, {key: [value1, value2]}
    key: name of parameter to retrieve
    default: value to return if the key isn't found

  Returns:
    The first value in the list, or default.
  """
  if key in parameters:
    if parameters[key]:
      return parameters[key][0]
  return default


def MainCGI(method, path, unused_headers, parameters, outfile):
  """CGI for all OAuth handlers.

  Args:
    method: HTTP method
    path: Path of the request
    unused_headers: Instance of mimetools.Message with headers from the request.
    parameters: Dictionary of parameters from the request.
    outfile: File-like object to which all output data should be written.
  """
  if method != 'GET' and method != 'POST':
    outfile.write('Status: 400\r\n')
    return

  if path == _GET_REQUEST_TOKEN_URL:
    OAuthGetRequestTokenCGI(outfile)
  elif path == _AUTHORIZE_TOKEN_URL:
    OAuthAuthorizeTokenCGI(method, parameters, outfile)
  elif path == _GET_ACCESS_TOKEN_URL:
    OAuthGetAccessTokenCGI(outfile)
  else:
    outfile.write('Status: 404 Unknown OAuth handler\r\n')


def CreateOAuthDispatcher():
  """Function to create OAuth dispatcher.

  Returns:
    New dispatcher capable of handling requests to the built-in OAuth handlers.
  """



  from google.appengine.tools import dev_appserver

  class OAuthDispatcher(dev_appserver.URLDispatcher):
    """Dispatcher that handles requests to the built-in OAuth handlers."""

    def Dispatch(self,
                 request,
                 outfile,
                 base_env_dict=None):
      """Handles dispatch to OAuth handlers.

      Args:
        request: AppServerRequest.
        outfile: The response file.
        base_env_dict: Dictionary of CGI environment parameters if available.
          Defaults to None.
      """
      if not base_env_dict:
        outfile.write('Status: 500\r\n')
        return
      method, path, headers, parameters = self._Parse(request, base_env_dict)
      MainCGI(method, path, headers, parameters, outfile)

    def _Parse(self, request, base_env_dict):
      """Parses a request into convenient pieces.

      Args:
        request: AppServerRequest.
        base_env_dict: Dictionary of CGI environment parameters.

      Returns:
        A tuple (method, path, headers, parameters) of the HTTP method, the
        path (minus query string), an instance of mimetools.Message with
        headers from the request, and a dictionary of parameter lists from the
        body or query string (in the form of {key :[value1, value2]}).
      """
      method = base_env_dict['REQUEST_METHOD']
      path, query = dev_appserver.SplitURL(request.relative_url)
      parameters = {}
      if method == 'POST':
        form = cgi.FieldStorage(fp=request.infile,
                                headers=request.headers,
                                environ=base_env_dict)
        for key in form:
          if key not in parameters:
            parameters[key] = []
          for value in form.getlist(key):
            parameters[key].append(value)
      elif method == 'GET':
        parameters = cgi.parse_qs(query)
      return method, path, request.headers, parameters

  return OAuthDispatcher()
