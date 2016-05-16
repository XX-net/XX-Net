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




"""XMPP API.

This module allows AppEngine apps to interact with a bot representing that app
on the Google Talk network.

Functions defined in this module:
  send_message: Sends a chat message to any number of JIDs.
  send_invite: Sends an invitation to chat to a JID.
  send_presence: Sends a presence to a JID.

  get_presence: Method to get the presence for a JID.

Classes defined in this module:
  Message: A class to encapsulate received messages.
"""











from google.appengine.api import apiproxy_stub_map
from google.appengine.api.xmpp import xmpp_service_pb
from google.appengine.runtime import apiproxy_errors



NO_ERROR    = xmpp_service_pb.XmppMessageResponse.NO_ERROR
INVALID_JID = xmpp_service_pb.XmppMessageResponse.INVALID_JID
OTHER_ERROR = xmpp_service_pb.XmppMessageResponse.OTHER_ERROR




MESSAGE_TYPE_NONE = ""
MESSAGE_TYPE_CHAT = "chat"
MESSAGE_TYPE_ERROR = "error"
MESSAGE_TYPE_GROUPCHAT = "groupchat"
MESSAGE_TYPE_HEADLINE = "headline"
MESSAGE_TYPE_NORMAL = "normal"

_VALID_MESSAGE_TYPES = frozenset([MESSAGE_TYPE_NONE, MESSAGE_TYPE_CHAT,
                                  MESSAGE_TYPE_ERROR, MESSAGE_TYPE_GROUPCHAT,
                                  MESSAGE_TYPE_HEADLINE, MESSAGE_TYPE_NORMAL])




PRESENCE_TYPE_AVAILABLE = ""
PRESENCE_TYPE_UNAVAILABLE = "unavailable"
PRESENCE_TYPE_PROBE = "probe"
_VALID_PRESENCE_TYPES = frozenset([PRESENCE_TYPE_AVAILABLE,
                                   PRESENCE_TYPE_UNAVAILABLE,
                                   PRESENCE_TYPE_PROBE])




PRESENCE_SHOW_NONE = ""
PRESENCE_SHOW_AWAY = "away"
PRESENCE_SHOW_CHAT = "chat"
PRESENCE_SHOW_DND = "dnd"
PRESENCE_SHOW_XA = "xa"
_VALID_PRESENCE_SHOWS = frozenset([PRESENCE_SHOW_NONE, PRESENCE_SHOW_AWAY,
                                   PRESENCE_SHOW_CHAT, PRESENCE_SHOW_DND,
                                   PRESENCE_SHOW_XA])
_PRESENCE_SHOW_MAPPING = {
    xmpp_service_pb.PresenceResponse.NORMAL: PRESENCE_SHOW_NONE,
    xmpp_service_pb.PresenceResponse.AWAY: PRESENCE_SHOW_AWAY,
    xmpp_service_pb.PresenceResponse.DO_NOT_DISTURB: PRESENCE_SHOW_DND,
    xmpp_service_pb.PresenceResponse.CHAT: PRESENCE_SHOW_CHAT,
    xmpp_service_pb.PresenceResponse.EXTENDED_AWAY: PRESENCE_SHOW_XA,
}


MAX_STATUS_MESSAGE_SIZE = 1024

class Error(Exception):
  """Base error class for this module."""


class InvalidJidError(Error):
  """Error that indicates a request for an invalid JID."""


class InvalidTypeError(Error):
  """Error that indicates a request has an invalid type."""


class InvalidXmlError(Error):
  """Error that indicates a send message request has invalid XML."""


class NoBodyError(Error):
  """Error that indicates a send message request has no body."""


class InvalidMessageError(Error):
  """Error that indicates a received message was invalid or incomplete."""


class InvalidShowError(Error):
  """Error that indicates a send presence request has an invalid show."""


class InvalidStatusError(Error):
  """Error that indicates a send presence request has an invalid status."""


class NondefaultModuleError(Error):
  """Error that indicates the XMPP API was used from a non-default module."""

  def __init__(self):
    super(NondefaultModuleError, self).__init__(
        'XMPP API does not support modules')


def get_presence(jid, from_jid=None, get_show=False):
  """Gets the presence for a JID.

  Args:
    jid: The JID of the contact whose presence is requested. This may also be a
      list of JIDs, which also implies get_show (below).
    from_jid: The optional custom JID to use for sending. Currently, the default
      is <appid>@appspot.com. This is supported as a value. Custom JIDs can be
      of the form <anything>@<appid>.appspotchat.com.
    get_show: if True, return a tuple of (is_available, show). If a list of jids
      is given, this will always be True.

  Returns:
    At minimum, a boolean is_available representing whether the requested JID
    is available.

    If get_show is specified, a tuple (is_available, show) will be given.

    If a list of JIDs is given, a list of tuples will be returned, including
    is_available, show, and an additional boolean indicating if that JID was
    valid.

  Raises:
    InvalidJidError: Raised if no JID passed in is valid.
    Error: if an unspecified error happens processing the request.
  """
  if not jid:
    raise InvalidJidError()

  request = xmpp_service_pb.BulkPresenceRequest()
  response = xmpp_service_pb.BulkPresenceResponse()

  if isinstance(jid, basestring):
    single_jid = True
    jidlist = [jid]
  else:

    single_jid = False
    get_show = True
    jidlist = jid

  for given_jid in jidlist:
    request.add_jid(_to_str(given_jid))

  if from_jid:
    request.set_from_jid(_to_str(from_jid))

  try:
    apiproxy_stub_map.MakeSyncCall("xmpp",
                                   "BulkGetPresence",
                                   request,
                                   response)
  except apiproxy_errors.ApplicationError, e:
    if (e.application_error ==
        xmpp_service_pb.XmppServiceError.INVALID_JID):





      raise InvalidJidError()
    elif (e.application_error ==
          xmpp_service_pb.XmppServiceError.NONDEFAULT_MODULE):
      raise NondefaultModuleError()
    else:
      raise Error()

  def HandleSubresponse(subresponse):
    if get_show:
      if subresponse.has_presence():
        presence = subresponse.presence()
        show = _PRESENCE_SHOW_MAPPING.get(presence, None)
      else:
        show = None
      return bool(subresponse.is_available()), show, subresponse.valid()
    else:
      return bool(subresponse.is_available()), subresponse.valid()

  results = [HandleSubresponse(s) for s in response.presence_response_list()]


  if not any(t[-1] for t in results):
    raise InvalidJidError()

  if single_jid:
    if get_show:
      return results[0][:-1]
    else:
      return results[0][0]
  else:
    return results


def send_invite(jid, from_jid=None):
  """Sends an invitation to chat to a JID.

  Args:
    jid: The JID of the contact to invite.
    from_jid: The optional custom JID to use for sending. Currently, the default
      is <appid>@appspot.com. This is supported as a value. Custom JIDs can be
      of the form <anything>@<appid>.appspotchat.com.

  Raises:
    InvalidJidError if the JID passed is invalid.
    Error if an unspecified error happens processing the request.
  """
  if not jid:
    raise InvalidJidError()

  request = xmpp_service_pb.XmppInviteRequest()
  response = xmpp_service_pb.XmppInviteResponse()

  request.set_jid(_to_str(jid))
  if from_jid:
    request.set_from_jid(_to_str(from_jid))

  try:
    apiproxy_stub_map.MakeSyncCall("xmpp",
                                   "SendInvite",
                                   request,
                                   response)
  except apiproxy_errors.ApplicationError, e:
    if (e.application_error ==
        xmpp_service_pb.XmppServiceError.INVALID_JID):
      raise InvalidJidError()
    elif (e.application_error ==
          xmpp_service_pb.XmppServiceError.NONDEFAULT_MODULE):
      raise NondefaultModuleError()
    else:
      raise Error()

  return


def send_message(jids, body, from_jid=None, message_type=MESSAGE_TYPE_CHAT,
                 raw_xml=False):
  """Sends a chat message to a list of JIDs.

  Args:
    jids: A list of JIDs to send the message to, or a single JID to send the
      message to.
    from_jid: The optional custom JID to use for sending. Currently, the default
      is <appid>@appspot.com. This is supported as a value. Custom JIDs can be
      of the form <anything>@<appid>.appspotchat.com.
    body: The body of the message.
    message_type: Optional type of the message. Should be one of the types
      specified in RFC 3921, section 2.1.1. An empty string will result in a
      message stanza without a type attribute. For convenience, all of the
      valid types are in the MESSAGE_TYPE_* constants in this file. The
      default is MESSAGE_TYPE_CHAT. Anything else will throw an exception.
    raw_xml: Optionally specifies that the body should be interpreted as XML. If
      this is false, the contents of the body will be escaped and placed inside
      of a body element inside of the message. If this is true, the contents
      will be made children of the message.

  Returns:
    list, A list of statuses, one for each JID, corresponding to the result of
      sending the message to that JID. Or, if a single JID was passed in,
      returns the status directly.

  Raises:
    InvalidJidError if there is no valid JID in the list.
    InvalidTypeError if the type argument is invalid.
    InvalidXmlError if the body is malformed XML and raw_xml is True.
    NoBodyError if there is no body.
    Error if another error occurs processing the request.
  """
  request = xmpp_service_pb.XmppMessageRequest()
  response = xmpp_service_pb.XmppMessageResponse()

  if not body:
    raise NoBodyError()

  if not jids:
    raise InvalidJidError()

  if not message_type in _VALID_MESSAGE_TYPES:
    raise InvalidTypeError()

  single_jid = False
  if isinstance(jids, basestring):
    single_jid = True
    jids = [jids]

  for jid in jids:
    if not jid:
      raise InvalidJidError()
    request.add_jid(_to_str(jid))

  request.set_body(_to_str(body))
  request.set_type(_to_str(message_type))
  request.set_raw_xml(raw_xml)
  if from_jid:
    request.set_from_jid(_to_str(from_jid))

  try:
    apiproxy_stub_map.MakeSyncCall("xmpp",
                                   "SendMessage",
                                   request,
                                   response)
  except apiproxy_errors.ApplicationError, e:
    if (e.application_error ==
        xmpp_service_pb.XmppServiceError.INVALID_JID):
      raise InvalidJidError()
    elif (e.application_error ==
          xmpp_service_pb.XmppServiceError.INVALID_TYPE):
      raise InvalidTypeError()
    elif (e.application_error ==
          xmpp_service_pb.XmppServiceError.INVALID_XML):
      raise InvalidXmlError()
    elif (e.application_error ==
          xmpp_service_pb.XmppServiceError.NO_BODY):
      raise NoBodyError()
    elif (e.application_error ==
          xmpp_service_pb.XmppServiceError.NONDEFAULT_MODULE):
      raise NondefaultModuleError()
    raise Error()

  if single_jid:
    return response.status_list()[0]
  return response.status_list()


def send_presence(jid, status=None, from_jid=None,
                  presence_type=PRESENCE_TYPE_AVAILABLE,
                  presence_show=PRESENCE_SHOW_NONE):
  """Sends a presence to a given JID.

  Args:
    jid: A JID to send the presence to.
    status: The optional status message. Size is limited to 1KB.
    from_jid: The optional custom JID to use for sending. Currently, the default
      is <appid>@appspot.com. This is supported as a value. Custom JIDs can be
      of the form <anything>@<appid>.appspotchat.com.
    presence_type: Optional type of the presence. This accepts a subset of the
      types specified in RFC 3921, section 2.2.1. An empty string will result
      in a presence stanza without a type attribute. For convenience, all of the
      valid types are in the PRESENCE_TYPE_* constants in this file. The default
      is PRESENCE_TYPE_AVAILABLE. Anything else will throw an exception.
    presence_show: Optional show value for the presence. Should be one of the
      values specified in RFC 3921, section 2.2.2.1. An empty string will result
      in a presence stanza without a show element. For convenience, all of the
      valid types are in the PRESENCE_SHOW_* constants in this file. The
      default is PRESENCE_SHOW_NONE. Anything else will throw an exception.

  Raises:
    InvalidJidError if there is no valid JID in the list.
    InvalidTypeError if the type argument is invalid.
    InvalidShowError if the show argument is invalid.
    InvalidStatusError if the status argument is too large.
    Error if another error occurs processing the request.
  """
  request = xmpp_service_pb.XmppSendPresenceRequest()
  response = xmpp_service_pb.XmppSendPresenceResponse()

  if not jid:
    raise InvalidJidError()

  if presence_type and not _to_str(presence_type) in _VALID_PRESENCE_TYPES:
    raise InvalidTypeError()

  if presence_show and not _to_str(presence_show) in _VALID_PRESENCE_SHOWS:
    raise InvalidShowError()

  if status and len(status) > MAX_STATUS_MESSAGE_SIZE:
    raise InvalidStatusError()

  request.set_jid(_to_str(jid))
  if status:
    request.set_status(_to_str(status))
  if presence_type:
    request.set_type(_to_str(presence_type))
  if presence_show:
    request.set_show(_to_str(presence_show))
  if from_jid:
    request.set_from_jid(_to_str(from_jid))

  try:
    apiproxy_stub_map.MakeSyncCall("xmpp",
                                   "SendPresence",
                                   request,
                                   response)
  except apiproxy_errors.ApplicationError, e:
    if (e.application_error ==
        xmpp_service_pb.XmppServiceError.INVALID_JID):
      raise InvalidJidError()
    elif (e.application_error ==
          xmpp_service_pb.XmppServiceError.INVALID_TYPE):
      raise InvalidTypeError()
    elif (e.application_error ==
          xmpp_service_pb.XmppServiceError.INVALID_SHOW):
      raise InvalidShowError()
    elif (e.application_error ==
          xmpp_service_pb.XmppServiceError.NONDEFAULT_MODULE):
      raise NondefaultModuleError()
    raise Error()


class Message(object):
  """Encapsulates an XMPP message received by the application."""

  def __init__(self, vars):
    """Constructs a new XMPP Message from an HTTP request.

    Args:
      vars: A dict-like object to extract message arguments from.
    """
    try:
      self.__sender = vars["from"]
      self.__to = vars["to"]
      self.__body = vars["body"]
    except KeyError, e:
      raise InvalidMessageError(e[0])
    self.__command = None
    self.__arg = None

  @property
  def sender(self):
    return self.__sender

  @property
  def to(self):
    return self.__to

  @property
  def body(self):
    return self.__body

  def __parse_command(self):
    if self.__arg != None:
      return


    body = self.__body
    if body.startswith('\\'):
      body = '/' + body[1:]

    self.__arg = ''
    if body.startswith('/'):
      parts = body.split(' ', 1)
      self.__command = parts[0][1:]
      if len(parts) > 1:
        self.__arg = parts[1].strip()
    else:
      self.__arg = self.__body.strip()

  @property
  def command(self):
    self.__parse_command()
    return self.__command

  @property
  def arg(self):
    self.__parse_command()
    return self.__arg

  def reply(self, body, message_type=MESSAGE_TYPE_CHAT, raw_xml=False,
            send_message=send_message):
    """Convenience function to reply to a message.

    Args:
      body: str: The body of the message
      message_type, raw_xml: As per send_message.
      send_message: Used for testing.

    Returns:
      A status code as per send_message.

    Raises:
      See send_message.
    """
    return send_message([self.sender], body, from_jid=self.to,
                        message_type=message_type, raw_xml=raw_xml)


def _to_str(value):
  """Helper function to make sure unicode values converted to utf-8

  Args:
    value: str or unicode to convert to utf-8.

  Returns:
    UTF-8 encoded str of value, otherwise value unchanged.
  """
  if isinstance(value, unicode):
    return value.encode('utf-8')
  return value
