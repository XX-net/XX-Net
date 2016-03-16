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




"""Stub version of the XMPP API, writes messages to logs."""










import logging
import os

from google.appengine.api import apiproxy_stub
from google.appengine.api import app_identity
from google.appengine.api.xmpp import xmpp_service_pb
from google.appengine.runtime import apiproxy_errors



INVALID_JID_CHARACTERS = ',;()[]'


class XmppServiceStub(apiproxy_stub.APIProxyStub):
  """Python only xmpp service stub.

  This stub does not use an XMPP network. It prints messages to the console
  instead of sending any stanzas.
  """

  THREADSAFE = True

  def __init__(self, log=logging.info, service_name='xmpp'):
    """Initializer.

    Args:
      log: A logger, used for dependency injection.
      service_name: Service name expected for all calls.
    """
    super(XmppServiceStub, self).__init__(service_name)
    self.log = log

  def _Dynamic_GetPresence(self, request, response):
    """Implementation of XmppService::GetPresence.

    Returns online if the first character of the JID comes before 'm' in the
    alphabet, otherwise returns offline.

    Args:
      request: A PresenceRequest.
      response: A PresenceResponse.
    """
    self._GetFrom(request.from_jid())
    self._FillInPresenceResponse(request.jid(), response)

  def _Dynamic_BulkGetPresence(self, request, response):
    self._GetFrom(request.from_jid())
    for jid in request.jid_list():
      subresponse = response.add_presence_response()
      self._FillInPresenceResponse(jid, subresponse)

  def _FillInPresenceResponse(self, jid, response):
    """Arbitrarily fill in a presence response or subresponse."""
    response.set_is_available(jid[0] < 'm')
    response.set_valid(self._ValidateJid(jid))
    response.set_presence(1)

  def _Dynamic_SendMessage(self, request, response):
    """Implementation of XmppService::SendMessage.

    Args:
      request: An XmppMessageRequest.
      response: An XmppMessageResponse .
    """
    from_jid = self._GetFrom(request.from_jid())
    log_message = []
    log_message.append('Sending an XMPP Message:')
    log_message.append('    From:')
    log_message.append('       ' + from_jid)
    log_message.append('    Body:')
    log_message.append('       ' + request.body())
    log_message.append('    Type:')
    log_message.append('       ' + request.type())
    log_message.append('    Raw Xml:')
    log_message.append('       ' + str(request.raw_xml()))
    log_message.append('    To JIDs:')
    for jid in request.jid_list():
      log_message.append('       ' + jid)
    self.log('\n'.join(log_message))

    for jid in request.jid_list():
      if self._ValidateJid(jid):
        response.add_status(xmpp_service_pb.XmppMessageResponse.NO_ERROR)
      else:
        response.add_status(xmpp_service_pb.XmppMessageResponse.INVALID_JID)

  def _Dynamic_SendInvite(self, request, response):
    """Implementation of XmppService::SendInvite.

    Args:
      request: An XmppInviteRequest.
      response: An XmppInviteResponse .
    """
    from_jid = self._GetFrom(request.from_jid())
    self._ParseJid(request.jid())
    log_message = []
    log_message.append('Sending an XMPP Invite:')
    log_message.append('    From:')
    log_message.append('       ' + from_jid)
    log_message.append('    To: ' + request.jid())
    self.log('\n'.join(log_message))

  def _Dynamic_SendPresence(self, request, response):
    """Implementation of XmppService::SendPresence.

    Args:
      request: An XmppSendPresenceRequest.
      response: An XmppSendPresenceResponse .
    """
    from_jid = self._GetFrom(request.from_jid())
    log_message = []
    log_message.append('Sending an XMPP Presence:')
    log_message.append('    From:')
    log_message.append('       ' + from_jid)
    log_message.append('    To: ' + request.jid())
    if request.type():
      log_message.append('    Type: ' + request.type())
    if request.show():
      log_message.append('    Show: ' + request.show())
    if request.status():
      log_message.append('    Status: ' + request.status())
    self.log('\n'.join(log_message))

  def _ParseJid(self, jid):
    """Parse the given JID.

    Also tests that the given jid:

      * Contains one and only one @.
      * Has one or zero resources.
      * Has a node.
      * Does not contain any invalid characters.

    Args:
      jid: The JID to validate

    Returns:
      A tuple (node, domain, resource) representing the JID.

    Raises:
      apiproxy_errors.ApplicationError if the requested JID is invalid using the
        criteria listed above.
    """
    if set(jid).intersection(INVALID_JID_CHARACTERS):
      self.log('Invalid JID: characters "%s" not supported.  JID: %s',
               INVALID_JID_CHARACTERS,
               jid)
      raise apiproxy_errors.ApplicationError(
          xmpp_service_pb.XmppServiceError.INVALID_JID)

    node, domain, resource = ('', '', '')
    at = jid.find('@')
    if at == -1:
      self.log('Invalid JID: No \'@\' character found. JID: %s', jid)
      raise apiproxy_errors.ApplicationError(
          xmpp_service_pb.XmppServiceError.INVALID_JID)

    node = jid[:at]
    if not node:
      self.log('Invalid JID: No node. JID: %s', jid)
      raise apiproxy_errors.ApplicationError(
          xmpp_service_pb.XmppServiceError.INVALID_JID)

    rest = jid[at+1:]
    if rest.find('@') > -1:
      self.log('Invalid JID: Second \'@\' character found. JID: %s',
               jid)
      raise apiproxy_errors.ApplicationError(
          xmpp_service_pb.XmppServiceError.INVALID_JID)

    slash = rest.find('/')
    if slash == -1:
      domain = rest
      resource = 'bot'
    else:
      domain = rest[:slash]
      resource = rest[slash+1:]

    if resource.find('/') > -1:
      self.log('Invalid JID: Second \'/\' character found. JID: %s',
               jid)
      raise apiproxy_errors.ApplicationError(
          xmpp_service_pb.XmppServiceError.INVALID_JID)

    return node, domain, resource

  def _ValidateJid(self, jid):
    """Validate the given JID using self._ParseJid."""
    try:
      self._ParseJid(jid)
      return True
    except apiproxy_errors.ApplicationError:
      return False

  def _GetFrom(self, requested):
    """Validates that the from JID is valid.

    The JID uses the display-app-id for all apps to simulate a common case
    in production (alias === display-app-id).

    Args:
      requested: The requested from JID.

    Returns:
      string, The from JID.

    Raises:
      apiproxy_errors.ApplicationError if the requested JID is invalid.
    """

    full_appid = os.environ.get('APPLICATION_ID')
    partition, _, display_app_id = (
        app_identity.app_identity._ParseFullAppId(full_appid))
    if requested == None or requested == '':
      return display_app_id + '@appspot.com/bot'

    node, domain, resource = self._ParseJid(requested)

    if domain == 'appspot.com' and node == display_app_id:
      return node + '@' + domain + '/' + resource
    elif domain == display_app_id + '.appspotchat.com':
      return node + '@' + domain + '/' + resource

    self.log('Invalid From JID: Must be appid@appspot.com[/resource] or '
             'node@appid.appspotchat.com[/resource]. JID: %s', requested)
    raise apiproxy_errors.ApplicationError(
        xmpp_service_pb.XmppServiceError.INVALID_JID)

  def _Dynamic_CreateChannel(self, request, response):
    """Implementation of XmppService::CreateChannel.

    Args:
      request: A CreateChannelRequest.
      response: A CreateChannelResponse.
    """
    log_message = []
    log_message.append('Sending a Create Channel:')
    log_message.append('    Client ID:')
    log_message.append('       ' + request.application_key())
    if request.duration_minutes():
      log_message.append('    Duration minutes: ' +
                         str(request.duration_minutes()))
    self.log('\n'.join(log_message))

  def _Dynamic_SendChannelMessage(self, request, response):
    """Implementation of XmppService::SendChannelMessage.

    Args:
      request: A SendMessageRequest.
      response: A SendMessageRequest.
    """
    log_message = []
    log_message.append('Sending a Channel Message:')
    log_message.append('    Client ID:')
    log_message.append('       ' + request.application_key())
    log_message.append('    Message:')
    log_message.append('       ' + str(request.message()))
    self.log('\n'.join(log_message))
