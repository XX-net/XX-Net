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
"""Tests for devappserver2.admin.mail_request_handler."""

import email.message
import unittest

import google

import mox
import webapp2

from google.appengine.tools.devappserver2 import dispatcher
from google.appengine.tools.devappserver2.admin import mail_request_handler


class MailRequestHandlerTest(unittest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_generate_email(self):
    message = mail_request_handler.MailRequestHandler._generate_email(
        'to', 'from', 'cc', 'subject', 'body')
    self.assertEqual('from', message['From'])
    self.assertEqual('to', message['To'])
    self.assertEqual('cc', message['Cc'])
    self.assertEqual('subject', message['Subject'])
    text, html = message.get_payload()
    self.assertEqual('text/plain', text.get_content_type())
    self.assertEqual('utf-8', text.get_content_charset())
    content = text.get_payload()
    if text['content-transfer-encoding'] != '7bit':
      content = content.decode(text['content-transfer-encoding'])
    self.assertEqual('body', content)

    self.assertEqual('text/html', html.get_content_type())
    self.assertEqual('utf-8', html.get_content_charset())
    content = html.get_payload()
    if html['content-transfer-encoding'] != '7bit':
      content = content.decode(html['content-transfer-encoding'])
    self.assertEqual('body', content)

  def test_send_email(self):
    response = webapp2.Response()
    handler = mail_request_handler.MailRequestHandler(None, response)
    message = object()
    self.mox.StubOutWithMock(handler, '_send')
    self.mox.StubOutWithMock(handler, '_generate_email')
    handler._generate_email('to', 'from', 'cc', 'subject', 'body').AndReturn(
        message)
    handler._send('/_ah/mail/to', message).AndReturn(
        dispatcher.ResponseTuple('500 Internal Server Error', [], 'Response'))
    self.mox.ReplayAll()
    handler._send_email('to', 'from', 'cc', 'subject', 'body')
    self.mox.VerifyAll()
    self.assertEqual(500, response.status_int)

  def test_send(self):
    self.mox.StubOutWithMock(mail_request_handler.MailRequestHandler,
                             'dispatcher')
    handler = mail_request_handler.MailRequestHandler(None, None)
    handler.dispatcher = self.mox.CreateMock(dispatcher.Dispatcher)
    handler.dispatcher.add_request(
        method='POST',
        relative_url='URL',
        headers=[('Content-Type', 'message/rfc822')],
        body='mail message',
        source_ip='0.1.0.20')
    message = self.mox.CreateMock(email.message.Message)
    message.as_string().AndReturn('mail message')
    self.mox.ReplayAll()
    handler._send('URL', message)
    self.mox.VerifyAll()

  def test_post(self):
    request = webapp2.Request.blank('/mail', POST={
        'to': 'to', 'from': 'from', 'cc': 'cc', 'subject': 'subject',
        'body': 'body'})
    response = webapp2.Response()
    handler = mail_request_handler.MailRequestHandler(request, response)
    self.mox.StubOutWithMock(handler, '_send_email')
    handler._send_email('to', 'from', 'cc', 'subject', 'body')
    self.mox.ReplayAll()
    handler.post()
    self.mox.VerifyAll()


if __name__ == '__main__':
  unittest.main()
