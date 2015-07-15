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




"""Channel support classes.

Classes:

  CreateChannelDispatcher:
    Creates a dispatcher that is added to dispatcher chain.  Handles polls from
    the client to retrieve messages for a given channel.
"""



import cgi
import os
import urlparse



CHANNEL_POLL_PATTERN = '/_ah/channel/dev(?:/.*)?'


CHANNEL_JSAPI_PATTERN = '/_ah/channel/jsapi'


def CreateChannelDispatcher(channel_service_stub):
  """Function to create channel dispatcher.

  Args:
    channel_service_stub: The service stub responsible for creating channels and
      sending messages. This stub stores messages destined for channels, so we
      query it when the client polls the _ah/channel/ dispatcher.

  Returns:
    New dispatcher capable of handling client polls for channel messages.
  """



  from google.appengine.tools import dev_appserver

  class ChannelDispatcher(dev_appserver.URLDispatcher):
    """Dispatcher that handles channel polls."""

    def __init__(self, channel_service_stub):
      """Constructor.

      Args:
        channel_service_stub: The channel service that receives channel messages
        from the application.
      """
      self._channel_service_stub = channel_service_stub


    def Dispatch(self,
                 request,
                 outfile,
                 base_env_dict=None):
      """Handle post dispatch.

      This dispatcher handles requests under the /_ah/channel/ path. Currently
      it handles 3 sub-paths:
        connect: place-holder for parity with the java dev channel.
        poll:    return pending messages for the channel identified by the
                 channel parameter.
        jsapi:   return the javascript library to retrieve messages for the
                 channel.

      Args:
        request: The HTTP request.
        outfile: The response file.
        base_env_dict: Dictionary of CGI environment parameters if available.
          Defaults to None.
      """

      outfile.write('Status: 200\r\n')

      (unused_scheme, unused_netloc,
       path, query,
       unused_fragment) = urlparse.urlsplit(request.relative_url)
      param_dict = cgi.parse_qs(query, True)

      page = path.rsplit('/', 1)[-1]

      if page == 'jsapi':
        path = os.path.join(os.path.dirname(__file__), 'dev-channel-js.js')
        outfile.write('Content-type: text/javascript\r\n\r\n')
        outfile.write(open(path).read())
      elif page == 'dev':
        outfile.write('\r\n')
        id = param_dict['channel'][0]
        command = param_dict['command'][0]

        if command == 'connect':
          self._channel_service_stub.connect_channel(id)
          outfile.write('1')
        elif command == 'poll':
          self._channel_service_stub.connect_channel(id)
          if self._channel_service_stub.has_channel_messages(id):
            outfile.write(self._channel_service_stub.pop_first_message(id))

  return ChannelDispatcher(channel_service_stub)
