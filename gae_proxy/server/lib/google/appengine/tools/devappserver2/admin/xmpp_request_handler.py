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
"""A handler that allows the user to send XMPP messages to their application."""



import cStringIO
import random
import string
from xml.etree import ElementTree

from google.appengine.tools.devappserver2.admin import admin_request_handler

ElementTree.register_namespace('cli', 'jabber:client')

REMOTE_IP = '0.1.0.10'


class _FormData(object):
  def __init__(self):
    self._data = []

  def __eq__(self, o):
    return isinstance(o, _FormData) and self._data == o._data

  def __str__(self):
    _, content = self.get_boundary_and_content()
    return content
  __repr__ = __str__

  def add_text(self, name, value, sub_type):
    self._data.append((name, value, sub_type))

  def get_boundary_and_content(self):
    """Returns the message boundary and entire content body for the form."""
    boundary = '----=' + ''.join(random.choice(string.letters + string.digits)
                                 for _ in range(25))
    s = cStringIO.StringIO()

    for name, value, sub_type in self._data:
      s.write('--%s\r\n' % boundary)
      s.write('Content-Type: text/%s; charset="UTF-8"\r\n' % sub_type)
      s.write('Content-Disposition: form-data; name="%s"\r\n' % name)
      s.write('\r\n')
      s.write('%s\r\n' % value.encode('utf-8'))
    s.write('--%s--\r\n' % boundary)
    return boundary, s.getvalue()


class XmppRequestHandler(admin_request_handler.AdminRequestHandler):

  def get(self):
    # TODO: Generate a warning if XMPP is not configured when the
    # configuration is sorted in the new servers world.
    self.response.write(self.render('xmpp.html', {}))

  def post(self):
    message_type = self.request.get('message_type')
    to = self.request.get('to')
    from_ = self.request.get('from')

    if message_type == 'chat':
      self._send_chat(to, from_)
    elif message_type == 'presence':
      if self.request.get('presence') == 'available':
        self._send_presence_available(to, from_)
      elif self.request.get('presence') == 'unavailable':
        self._send_presence_unavailable(to, from_)
      else:
        assert 0
    elif message_type == 'subscribe':
      self._send_subscription(to, from_)
    else:
      assert 0

  def _generate_chat(self, to, from_, body):
    data = _FormData()
    data.add_text('from', from_, 'plain')
    data.add_text('to', to, 'plain')
    data.add_text('body', body, 'plain')

    message_element = ElementTree.Element(
        ElementTree.QName('jabber:client', 'message'),
        {'from': from_, 'to': to, 'type': 'chat'})
    body_element = ElementTree.SubElement(
        message_element,
        ElementTree.QName('jabber:client', 'body'))
    body_element.text = body

    data.add_text('stanza',
                  ElementTree.tostring(message_element, encoding='utf-8'),
                  'xml')
    return data

  def _send_chat(self, to, from_):
    body = self.request.get('chat')
    form_data = self._generate_chat(to, from_, body)
    response = self._send('/_ah/xmpp/message/chat/', form_data)
    self.response.status = response.status

  def _generate_presence_available(self, to, from_, show=None):
    data = _FormData()
    data.add_text('from', from_, 'plain')
    data.add_text('to', to, 'plain')

    # If the "presence" attribute is absent, "available" is assumed and it is
    # not sent by Google Talk.
    presence_element = ElementTree.Element(
        ElementTree.QName('jabber:client', 'presence'),
        {'from': from_, 'to': to})

    if show:  # This is currently a dead code path.
      # The show element is optional according to RFC 3921, 2.2.2.1.
      data.add_text('show', show, 'plain')
      show_element = ElementTree.SubElement(
          presence_element,
          ElementTree.QName('jabber:client', 'show'))
      show_element.text = show

    data.add_text('stanza',
                  ElementTree.tostring(presence_element, 'utf-8'),
                  'xml')
    return data

  def _send(self, relative_url, form_data):
    boundary, content = form_data.get_boundary_and_content()
    return self.dispatcher.add_request(
        method='POST',
        relative_url=relative_url,
        headers=[('Content-Type',
                  'multipart/form-data; boundary="%s"' % boundary)],
        body=content,
        source_ip=REMOTE_IP,
        fake_login=True)

  def _send_presence_available(self, to, from_):
    # TODO: Support "show" values i.e. "away", "chat" "dnd" and "xa".
    # See RFC 3921, 2.2.2.1.
    form_data = self._generate_presence_available(to, from_)
    response = self._send('/_ah/xmpp/presence/available/', form_data)
    self.response.status = response.status

  def _generate_presence_type(self, to, from_, presence_type):
    data = _FormData()

    data.add_text('from', from_, 'plain')
    data.add_text('to', to, 'plain')

    presence_element = ElementTree.Element(
        ElementTree.QName('jabber:client', 'presence'),
        {'from': from_, 'to': to, 'type': presence_type})
    data.add_text('stanza',
                  ElementTree.tostring(presence_element, 'utf-8'),
                  'xml')

    return data

  def _send_presence_unavailable(self, to, from_):
    form_data = self._generate_presence_type(to, from_, 'unavailable')
    response = self._send('/_ah/xmpp/presence/unavailable/', form_data)
    self.response.status = response.status

  def _send_subscription(self, to, from_):
    subscription_type = self.request.get('subscription_type')
    # The subscription types defined in RFC 3921, 2.2.1
    assert subscription_type in ['subscribe',
                                 'subscribed',
                                 'unsubscribe',
                                 'unsubscribed']

    form_data = self._generate_presence_type(to, from_, subscription_type)
    response = self._send('/_ah/xmpp/subscription/%s/' % subscription_type,
                          form_data)
    self.response.status = response.status
