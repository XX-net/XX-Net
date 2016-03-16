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




"""Stub version of the Channel API, queues messages and writes them to a log."""









import hashlib
import logging
import random
import time

from google.appengine.api import apiproxy_stub
from google.appengine.api.channel import channel_service_pb
from google.appengine.runtime import apiproxy_errors


def _GenerateTokenHash(token):
  """Returns a MD5 hash of a token for integrity checking."""
  return hashlib.md5(token).hexdigest()


class Error(Exception):
  pass


class InvalidTokenError(Error):
  """A stub method was called with a syntactically invalid token."""
  pass


class TokenTimedOutError(Error):
  """A stub method was called with a token that has expired or never existed."""
  pass


class ChannelServiceStub(apiproxy_stub.APIProxyStub):
  """Python only channel service stub.

  This stub does not use a browser channel to push messages to a client.
  Instead it queues messages internally.
  """

  THREADSAFE = True




  CHANNEL_TIMEOUT_SECONDS = 2




  XMPP_PUBLIC_IP = '0.1.0.10'


  CHANNEL_TOKEN_DEFAULT_DURATION = 120


  CHANNEL_TOKEN_IDENTIFIER = 'channel'

  def __init__(self, log=logging.debug, service_name='channel',
               time_func=time.time, request_data=None):
    """Initializer.

    Args:
      log: A logger, used for dependency injection.
      service_name: Service name expected for all calls.
      time_func: function to get the current time in seconds.
      request_data: A request_info.RequestInfo instance. If None, a
        request_info._LocalRequestInfo instance will be used.
    """
    apiproxy_stub.APIProxyStub.__init__(self, service_name,
                                        request_data=request_data)
    self._log = log
    self._time_func = time_func



    self._connected_channel_messages = {}


  def _Dynamic_CreateChannel(self, request, response):
    """Implementation of channel.create_channel.

    Args:
      request: A ChannelServiceRequest.
      response: A ChannelServiceResponse
    """

    client_id = request.application_key()
    if not client_id:
      raise apiproxy_errors.ApplicationError(
          channel_service_pb.ChannelServiceError.INVALID_CHANNEL_KEY)

    if request.has_duration_minutes():
      duration = request.duration_minutes()
    else:
      duration = ChannelServiceStub.CHANNEL_TOKEN_DEFAULT_DURATION


    expiration_sec = long(self._time_func() + duration * 60) + 1

    raw_token = '-'.join([ChannelServiceStub.CHANNEL_TOKEN_IDENTIFIER,
                          str(random.randint(0, 2 ** 32)),
                          str(expiration_sec),
                          client_id])



    token = '-'.join([_GenerateTokenHash(raw_token), raw_token])

    self._log('Creating channel token %s with client id %s and duration %s',
              token, request.application_key(), duration)

    response.set_token(token)


  @apiproxy_stub.Synchronized
  def _Dynamic_SendChannelMessage(self, request, response):
    """Implementation of channel.send_message.

    Queues a message to be retrieved by the client when it polls.

    Args:
      request: A SendMessageRequest.
      response: A VoidProto.
    """



    client_id = self.client_id_from_token(request.application_key())
    if client_id is None:
      client_id = request.application_key()

    if not request.message():
      raise apiproxy_errors.ApplicationError(
          channel_service_pb.ChannelServiceError.BAD_MESSAGE)

    if client_id in self._connected_channel_messages:
      self._log('Sending a message (%s) to channel with key (%s)',
                request.message(), client_id)
      self._connected_channel_messages[client_id].append(request.message())
    else:
      self._log('SKIPPING message (%s) to channel with key (%s): '
                'no clients connected',
                request.message(), client_id)

  def client_id_from_token(self, token):
    """Returns the client id from a given token.

    Args:
       token: A string representing an instance of a client connection to a
       client id, returned by CreateChannel.

    Returns:
       A string representing the client id used to create this token,
       or None if this token is incorrectly formed and doesn't map to a
       client id.
    """
    try:
      return self.validate_token_and_extract_client_id(token)
    except (InvalidTokenError, TokenTimedOutError):
      return None

  def validate_token_and_extract_client_id(self, token):
    """Ensures token is well-formed and hasn't expired, and extracts client_id.

    Args:
      token: a token returned by CreateChannel.

    Returns:
      A client_id, which is the value passed to CreateChannel.

    Raises:
      InvalidTokenError: The token is syntactically invalid.
      TokenTimedOutError: The token expired or does not exist.
    """

    pieces = token.split('-', 1)
    if len(pieces) != 2 or _GenerateTokenHash(pieces[1]) != pieces[0]:
      raise InvalidTokenError()
    raw_token = pieces[1]


    pieces = raw_token.split('-', 3)
    if len(pieces) != 4:
      raise InvalidTokenError()

    constant_id, unused_random_id, expiration_sec, client_id = pieces
    if (constant_id != ChannelServiceStub.CHANNEL_TOKEN_IDENTIFIER
        or not expiration_sec.isdigit()):
      raise InvalidTokenError()
    if long(expiration_sec) <= self._time_func():
      raise TokenTimedOutError()

    return client_id

  @apiproxy_stub.Synchronized
  def get_channel_messages(self, token):
    """Returns the pending messages for a given channel.

    Args:
      token: A string representing the channel. Note that this is the token
        returned by CreateChannel, not the client id.

    Returns:
      List of messages, or None if the channel doesn't exist. The messages are
      strings.
    """
    self._log('Received request for messages for channel: ' + token)
    client_id = self.client_id_from_token(token)
    if client_id in self._connected_channel_messages:
      return self._connected_channel_messages[client_id]

    return None

  @apiproxy_stub.Synchronized
  def has_channel_messages(self, token):
    """Checks to see if the given channel has any pending messages.

    Args:
      token: A string representing the channel. Note that this is the token
        returned by CreateChannel, not the client id.

    Returns:
      True if the channel exists and has pending messages.
    """
    client_id = self.client_id_from_token(token)
    has_messages = (client_id in self._connected_channel_messages and
                    bool(self._connected_channel_messages[client_id]))
    self._log('Checking for messages on channel (%s) (%s)',
              token, has_messages)
    return has_messages

  @apiproxy_stub.Synchronized
  def pop_first_message(self, token):
    """Returns and clears the first message from the message queue.

    Args:
      token: A string representing the channel. Note that this is the token
        returned by CreateChannel, not the client id.

    Returns:
      The first message in the queue (a string), or None if no messages.
    """
    if self.has_channel_messages(token):
      client_id = self.client_id_from_token(token)
      self._log('Popping first message of queue for channel (%s)', token)
      return self._connected_channel_messages[client_id].pop(0)

    return None

  @apiproxy_stub.Synchronized
  def clear_channel_messages(self, token):
    """Clears all messages from the channel.

    Args:
      token: A string representing the channel. Note that this is the token
        returned by CreateChannel, not the client id.
    """
    client_id = self.client_id_from_token(token)
    if client_id:
      self._log('Clearing messages on channel (' + client_id + ')')
      if client_id in self._connected_channel_messages:
        self._connected_channel_messages[client_id] = []
    else:
      self._log('Ignoring clear messages for nonexistent token (' +
                token + ')')

  def add_connect_event(self, client_id):
    """Tell the application that the client has connected."""
    self.request_data.get_dispatcher().add_async_request(
        'POST', '/_ah/channel/connected/',
        [('Content-Type', 'application/x-www-form-urlencoded')],
        'from=%s' % client_id,
        ChannelServiceStub.XMPP_PUBLIC_IP)

  @apiproxy_stub.Synchronized
  def disconnect_channel_event(self, client_id):
    """Removes the channel from the list of connected channels."""
    self._log('Removing channel %s', client_id)
    if client_id in self._connected_channel_messages:
      del self._connected_channel_messages[client_id]
    self.request_data.get_dispatcher().add_async_request(
        'POST', '/_ah/channel/disconnected/',
        [('Content-Type', 'application/x-www-form-urlencoded')],
        'from=%s' % client_id,
        ChannelServiceStub.XMPP_PUBLIC_IP)

  def add_disconnect_event(self, client_id):
    """Add an event to notify the app if a client has disconnected.

    Args:
      client_id:  A client ID used for a particular channel.
    """
    timeout = self._time_func() + ChannelServiceStub.CHANNEL_TIMEOUT_SECONDS


    def DefineDisconnectCallback(client_id):
      return lambda: self.disconnect_channel_event(client_id)


    self.request_data.get_dispatcher().add_event(
        DefineDisconnectCallback(client_id), timeout, 'channel-disconnect',
        client_id)

  @apiproxy_stub.Synchronized
  def connect_channel(self, token):
    """Marks the channel identified by the token (token) as connected.

    If the channel has not yet been connected, this triggers a connection event
    to let the application know that the channel has been connected to.

    If the channel has already been connected, this refreshes the channel's
    timeout so that it will not disconnect. This should be done at regular
    intervals to avoid automatic disconnection.

    Args:
      token: A string representing the channel. Note that this is the token
        returned by CreateChannel, not the client id.

    Raises:
      InvalidTokenError: The token is syntactically invalid.
      TokenTimedOutError: The token expired or does not exist.
    """
    client_id = self.validate_token_and_extract_client_id(token)



    if client_id in self._connected_channel_messages:
      timeout = self._time_func() + ChannelServiceStub.CHANNEL_TIMEOUT_SECONDS

      self.request_data.get_dispatcher().update_event(
          timeout, 'channel-disconnect', client_id)
      return



    self._connected_channel_messages[client_id] = []
    self.add_connect_event(client_id)
    self.add_disconnect_event(client_id)

  @apiproxy_stub.Synchronized
  def connect_and_pop_first_message(self, token):
    """Atomically performs a connect_channel and a pop_first_message.

    This is designed to be called after the channel has already been connected,
    so that it refreshes the channel's timeout, and retrieves a message, in a
    single atomic operation.

    Args:
      token: A string representing the channel. Note that this is the token
        returned by CreateChannel, not the client id.

    Returns:
      The first message in the queue (a string), or None if no messages.

    Raises:
      InvalidTokenError: The token is syntactically invalid.
      TokenTimedOutError: The token expired or does not exist.
    """
    self.connect_channel(token)
    return self.pop_first_message(token)
