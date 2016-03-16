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
"""Tests for devappserver2.admin.xmpp_request_handler."""



import unittest

import google
from lxml import doctestcompare
import mox
import webapp2

from google.appengine.tools.devappserver2 import dispatcher
from google.appengine.tools.devappserver2.admin import xmpp_request_handler


class CompareXml(mox.Comparator):
  """Compare XML using only semantic differences e.g. ignore attribute order."""

  def __init__(self, xml):
    self._xml = xml

  def equals(self, rhs):
    checker = doctestcompare.LXMLOutputChecker()
    return checker.check_output(self._xml, rhs, 0)


class TestFormData(unittest.TestCase):
  """Tests for xmpp_request_handler._FormData."""

  def test(self):
    form_data = xmpp_request_handler._FormData()
    form_data.add_text('message', u'\N{White Smiling Face}', 'plain')
    form_data.add_text('stanza', '<p>This is\na\ntest!</p>', 'xml')
    boundary, content = form_data.get_boundary_and_content()
    self.assertMultiLineEqual(
        '--{boundary}\r\n'
        'Content-Type: text/plain; charset="UTF-8"\r\n'
        'Content-Disposition: form-data; name="message"\r\n'
        '\r\n'
        '\xe2\x98\xba\r\n'
        '--{boundary}\r\n'
        'Content-Type: text/xml; charset="UTF-8"\r\n'
        'Content-Disposition: form-data; name="stanza"\r\n'
        '\r\n'
        '<p>This is\na\ntest!</p>\r\n'
        '--{boundary}--\r\n'.format(boundary=boundary),
        content
    )


class TestXmppRequestHandler(unittest.TestCase):
  """Tests for xmpp_request_handler.XmppRequestHandler."""

  def setUp(self):
    self.mox = mox.Mox()

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_send(self):
    self.mox.StubOutWithMock(xmpp_request_handler.XmppRequestHandler,
                             'dispatcher')

    handler = xmpp_request_handler.XmppRequestHandler()
    handler.dispatcher = self.mox.CreateMock(dispatcher.Dispatcher)
    handler.dispatcher.add_request(
        method='POST',
        relative_url='url',
        headers=[('Content-Type',
                  mox.Regex('multipart/form-data; boundary=".*?"'))],
        body=mox.IsA(str),
        source_ip='0.1.0.10',
        fake_login=True)

    data = xmpp_request_handler._FormData()
    self.mox.ReplayAll()
    handler._send('url', data)
    self.mox.VerifyAll()

  def test_chat(self):
    self.mox.StubOutWithMock(xmpp_request_handler.XmppRequestHandler, '_send')

    request = webapp2.Request.blank('/xmpp', POST={'message_type': 'chat',
                                                   'to': 'foo@example.com',
                                                   'from': 'baz@example.com',
                                                   'chat': 'Chat content'})
    response = webapp2.Response()
    handler = xmpp_request_handler.XmppRequestHandler(request, response)
    data = xmpp_request_handler._FormData()
    data.add_text('from', 'baz@example.com', 'plain')
    data.add_text('to', 'foo@example.com', 'plain')
    data.add_text('body', 'Chat content', 'plain')
    data.add_text(
        'stanza',
        CompareXml(
            '<ns0:message from="baz@example.com" to="foo@example.com" '
            'type="chat" xmlns:ns0="jabber:client">'
            '<ns0:body>Chat content</ns0:body>'
            '</ns0:message>'),
        'xml')

    handler._send('/_ah/xmpp/message/chat/', data).AndReturn(
        dispatcher.ResponseTuple('404 Not Found', [], 'Response'))
    self.mox.ReplayAll()
    handler.post()
    self.mox.VerifyAll()
    self.assertEqual('404 Not Found', response.status)

  def test_presence_available(self):
    self.mox.StubOutWithMock(xmpp_request_handler.XmppRequestHandler, '_send')

    request = webapp2.Request.blank('/xmpp', POST={'message_type': 'presence',
                                                   'to': 'foo@example.com',
                                                   'from': 'baz@example.com',
                                                   'presence': 'available'})
    response = webapp2.Response()
    handler = xmpp_request_handler.XmppRequestHandler(request, response)
    data = xmpp_request_handler._FormData()
    data.add_text('from', 'baz@example.com', 'plain')
    data.add_text('to', 'foo@example.com', 'plain')
    data.add_text(
        'stanza',
        CompareXml(
            '<ns0:presence from="baz@example.com" to="foo@example.com" '
            'xmlns:ns0="jabber:client" />'),
        'xml')

    handler._send('/_ah/xmpp/presence/available/', data).AndReturn(
        dispatcher.ResponseTuple('404 Not Found', [], 'Response'))
    self.mox.ReplayAll()
    handler.post()
    self.mox.VerifyAll()
    self.assertEqual('404 Not Found', response.status)

  def test_presence_unavailable(self):
    self.mox.StubOutWithMock(xmpp_request_handler.XmppRequestHandler, '_send')

    request = webapp2.Request.blank('/xmpp', POST={'message_type': 'presence',
                                                   'to': 'foo@example.com',
                                                   'from': 'baz@example.com',
                                                   'presence': 'unavailable'})
    response = webapp2.Response()
    handler = xmpp_request_handler.XmppRequestHandler(request, response)
    data = xmpp_request_handler._FormData()
    data.add_text('from', 'baz@example.com', 'plain')
    data.add_text('to', 'foo@example.com', 'plain')
    data.add_text(
        'stanza',
        CompareXml(
            '<ns0:presence from="baz@example.com" to="foo@example.com" '
            'type="unavailable" xmlns:ns0="jabber:client" />'),
        'xml')

    handler._send('/_ah/xmpp/presence/unavailable/', data).AndReturn(
        dispatcher.ResponseTuple('404 Not Found', [], 'Response'))
    self.mox.ReplayAll()
    handler.post()
    self.mox.VerifyAll()
    self.assertEqual('404 Not Found', response.status)

  def test_subscribe(self):
    self.mox.StubOutWithMock(xmpp_request_handler.XmppRequestHandler, '_send')

    request = webapp2.Request.blank('/xmpp',
                                    POST={'message_type': 'subscribe',
                                          'to': 'foo@example.com',
                                          'from': 'baz@example.com',
                                          'subscription_type': 'subscribe'})
    response = webapp2.Response()
    handler = xmpp_request_handler.XmppRequestHandler(request, response)
    data = xmpp_request_handler._FormData()
    data.add_text('from', 'baz@example.com', 'plain')
    data.add_text('to', 'foo@example.com', 'plain')
    data.add_text(
        'stanza',
        CompareXml(
            '<ns0:presence from="baz@example.com" to="foo@example.com" '
            'type="subscribe" xmlns:ns0="jabber:client" />'),
        'xml')

    handler._send('/_ah/xmpp/subscription/subscribe/', data).AndReturn(
        dispatcher.ResponseTuple('404 Not Found', [], 'Response'))
    self.mox.ReplayAll()
    handler.post()
    self.mox.VerifyAll()
    self.assertEqual('404 Not Found', response.status)


if __name__ == '__main__':
  unittest.main()
