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




"""Channel API.

This module allows App Engine apps to push messages to a client.

Functions defined in this module:
  create_channel: Creates a channel to send messages to.
  send_message: Send a message to any clients listening on the given channel.
"""







import os

from google.appengine.api import api_base_pb
from google.appengine.api import apiproxy_stub_map
from google.appengine.api.channel import channel_service_pb
from google.appengine.runtime import apiproxy_errors








MAXIMUM_CLIENT_ID_LENGTH = 256


MAXIMUM_TOKEN_DURATION_MINUTES = 24 * 60






MAXIMUM_MESSAGE_LENGTH = 32767


class Error(Exception):
  """Base error class for this module."""


class InvalidChannelClientIdError(Error):
  """Error that indicates a bad client id."""


class InvalidChannelTokenDurationError(Error):
  """Error that indicates the requested duration is invalid."""


class InvalidMessageError(Error):
  """Error that indicates a message is malformed."""


class AppIdAliasRequired(Error):
  """Error that indicates you must assign an application alias to your app."""


def _ToChannelError(error):
  """Translate an application error to a channel Error, if possible.

  Args:
    error: An ApplicationError to translate.

  Returns:
    The appropriate channel service error, if a match is found, or the original
    ApplicationError.
  """
  error_map = {
      channel_service_pb.ChannelServiceError.INVALID_CHANNEL_KEY:
        InvalidChannelClientIdError,
      channel_service_pb.ChannelServiceError.BAD_MESSAGE:
        InvalidMessageError,
      channel_service_pb.ChannelServiceError.APPID_ALIAS_REQUIRED:
        AppIdAliasRequired
      }

  if error.application_error in error_map:
    return error_map[error.application_error](error.error_detail)
  else:
    return error


def _GetService():
  """Gets the service name to use, based on if we're on the dev server."""
  server_software = os.environ.get('SERVER_SOFTWARE', '')
  if (server_software.startswith('Devel') or
      server_software.startswith('test')):


    return 'channel'
  else:
    return 'xmpp'


def _ValidateClientId(client_id):
  """Validates a client id.

  Args:
    client_id: The client id provided by the application.

  Returns:
    If the client id is of type str, returns the original client id.
    If the client id is of type unicode, returns the id encoded to utf-8.

  Raises:
    InvalidChannelClientIdError: if client id is not an instance of str or
        unicode, or if the (utf-8 encoded) string is longer than 64 characters.
  """
  if not isinstance(client_id, basestring):
    raise InvalidChannelClientIdError('"%s" is not a string.' % client_id)

  if isinstance(client_id, unicode):
    client_id = client_id.encode('utf-8')


  if len(client_id) > MAXIMUM_CLIENT_ID_LENGTH:
    msg = 'Client id length %d is greater than max length %d' % (
         len(client_id), MAXIMUM_CLIENT_ID_LENGTH)
    raise InvalidChannelClientIdError(msg)

  return client_id



def create_channel(client_id, duration_minutes=None):
  """Create a channel.

  Args:
    client_id: A string to identify this channel on the server side.
    duration_minutes: An int specifying the number of minutes for which the
        returned token should be valid.

  Returns:
    A token that the client can use to connect to the channel.

  Raises:
    InvalidChannelClientIdError: if clientid is not an instance of str or
        unicode, or if the (utf-8 encoded) string is longer than 64 characters.
    InvalidChannelTokenDurationError: if duration_minutes is not a number, less
        than 1, or greater than 1440 (the number of minutes in a day).
    Other errors returned by _ToChannelError
  """


  client_id = _ValidateClientId(client_id)

  if not duration_minutes is None:
    if not isinstance(duration_minutes, (int, long)):
      raise InvalidChannelTokenDurationError(
         'Argument duration_minutes must be integral')
    elif duration_minutes < 1:
      raise InvalidChannelTokenDurationError(
         'Argument duration_minutes must not be less than 1')
    elif duration_minutes > MAXIMUM_TOKEN_DURATION_MINUTES:
      msg = ('Argument duration_minutes must be less than %d'
             % (MAXIMUM_TOKEN_DURATION_MINUTES + 1))
      raise InvalidChannelTokenDurationError(msg)


  request = channel_service_pb.CreateChannelRequest()
  response = channel_service_pb.CreateChannelResponse()

  request.set_application_key(client_id)
  if not duration_minutes is None:
    request.set_duration_minutes(duration_minutes)

  try:
    apiproxy_stub_map.MakeSyncCall(_GetService(),
                                   'CreateChannel',
                                   request,
                                   response)
  except apiproxy_errors.ApplicationError, e:
    raise _ToChannelError(e)

  return response.token()



def send_message(client_id, message):
  """Send a message to a channel.

  Args:
    client_id: The client id passed to create_channel.
    message: A string representing the message to send.

  Raises:
    InvalidChannelClientIdError: if client_id is not an instance of str or
        unicode, or if the (utf-8 encoded) string is longer than 64 characters.
    InvalidMessageError: if the message isn't a string or is too long.
    Errors returned by _ToChannelError
  """

  client_id = _ValidateClientId(client_id)

  if isinstance(message, unicode):
    message = message.encode('utf-8')
  elif not isinstance(message, str):
    raise InvalidMessageError('Message must be a string')

  if len(message) > MAXIMUM_MESSAGE_LENGTH:
    raise InvalidMessageError(
        'Message must be no longer than %d chars' % MAXIMUM_MESSAGE_LENGTH)

  request = channel_service_pb.SendMessageRequest()
  response = api_base_pb.VoidProto()

  request.set_application_key(client_id)
  request.set_message(message)

  try:
    apiproxy_stub_map.MakeSyncCall(_GetService(),
                                   'SendChannelMessage',
                                   request,
                                   response)
  except apiproxy_errors.ApplicationError, e:
    raise _ToChannelError(e)
