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
"""Handles Channel API requests.

Includes a WSGI application that serves the 'jsapi' JavaScript code and handles
channel polling HTTP requests, to connect and retrieve messages.
"""



import os

import google
import webapp2

from google.appengine.api import apiproxy_stub_map
from google.appengine.api.channel import channel_service_stub

# Regex for all requests routed through this module.
# Note: Other URLs in the _ah/channel namespace may be handled by the user.
CHANNEL_URL_PATTERN = '_ah/channel/(?:jsapi|dev)'

_JSAPI_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'dev-channel-js.js')

# These error statuses (including the message) are explicitly mandated in the
# Channel JavaScript documentation.
INVALID_TOKEN_STATUS = '401 Invalid+token.'
TOKEN_TIMED_OUT_STATUS = '401 Token+timed+out.'


def _get_channel_stub():
  """Gets the ChannelServiceStub instance from the API proxy stub map.

  Returns:
    The ChannelServiceStub instance as registered in the API stub map.
  """
  return apiproxy_stub_map.apiproxy.GetStub('channel')


class DevHandler(webapp2.RequestHandler):
  """The request handler for the 'connect' and 'poll' requests."""

  def get(self):
    # Remove the default Content-Type. If there is any content, the correct
    # Content-Type will be set later.
    del self.response.headers['Content-Type']
    stub = _get_channel_stub()

    command = self.request.get('command', None)
    token = self.request.get('channel', None)
    if command is None or token is None:
      self.response.status = 400
      return

    if command == 'connect':
      try:
        stub.connect_channel(token)
      except channel_service_stub.InvalidTokenError:
        self.response.status = INVALID_TOKEN_STATUS
        return
      except channel_service_stub.TokenTimedOutError:
        self.response.status = TOKEN_TIMED_OUT_STATUS
        return
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write('1')
    elif command == 'poll':
      try:
        # TODO: Wait up to N seconds for a message to arrive before
        # returning empty (long poll).
        message = stub.connect_and_pop_first_message(token)
      except channel_service_stub.InvalidTokenError:
        self.response.status = INVALID_TOKEN_STATUS
        return
      except channel_service_stub.TokenTimedOutError:
        self.response.status = TOKEN_TIMED_OUT_STATUS
        return
      if message is not None:
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(message)
    else:
      self.response.status = 400


class JSAPIHandler(webapp2.RequestHandler):
  """The request handler for the jsapi static JavaScript code."""

  def get(self):
    # TODO: Reuse code in static_files_handler to do cache control.
    self.response.headers['Content-Type'] = 'text/javascript'
    self.response.out.write(open(_JSAPI_PATH).read())


application = webapp2.WSGIApplication([
    ('/_ah/channel/dev', DevHandler),
    ('/_ah/channel/jsapi', JSAPIHandler),
], debug=True)
