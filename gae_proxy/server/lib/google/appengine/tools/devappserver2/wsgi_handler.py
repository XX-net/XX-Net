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
"""Base functionality for handling HTTP requests for built-in pages."""



import re

from google.appengine.tools.devappserver2 import url_handler


class WSGIHandler(url_handler.URLHandler):
  """Simple handler that matches a regex and runs a WSGI application.

  WSGIHandler does not perform authorization; the authorization check always
  succeeds.
  """

  def __init__(self, wsgi_app, url_pattern):
    """Initializer for WSGIHandler.

    Args:
      wsgi_app: A WSGI application function as defined in PEP-333.
      url_pattern: A regular expression string containing the pattern for URLs
          handled by this handler. Unlike user-provided patterns in app.yaml,
          the pattern is not required to match the whole URL, only the start.
          (End the pattern with '$' to explicitly match the whole string.)

    Raises:
      re.error: url_pattern was not a valid regular expression.
    """
    super(WSGIHandler, self).__init__(re.compile(url_pattern))
    self._wsgi_app = wsgi_app

  def handle(self, unused_match, environ, start_response):
    """Serves the content associated with this handler.

    Args:
      unused_match: Unused.
      environ: An environ dict for the current request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    return self._wsgi_app(environ, start_response)
