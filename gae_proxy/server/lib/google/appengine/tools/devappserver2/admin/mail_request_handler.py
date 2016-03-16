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
"""A handler that allows the user to send email to their application."""

import email.mime.multipart
import email.mime.text
import email.utils

from google.appengine.tools.devappserver2.admin import admin_request_handler

REMOTE_IP = '0.1.0.20'


class MailRequestHandler(admin_request_handler.AdminRequestHandler):

  def get(self):
    # TODO: Generate a warning if mail is not configured when the
    # configuration is sorted in the new servers world.
    self.response.write(self.render('mail.html', {}))

  def post(self):
    to = self.request.get('to')
    from_ = self.request.get('from')
    cc = self.request.get('cc')
    subject = self.request.get('subject')
    body = self.request.get('body')
    self._send_email(to, from_, cc, subject, body)

  @staticmethod
  def _generate_email(to, from_, cc, subject, body):
    message = email.mime.multipart.MIMEMultipart('alternative')
    message['To'] = to
    message['From'] = from_
    message['Cc'] = cc
    message['Subject'] = subject
    message['Date'] = email.utils.formatdate()
    plain_text = email.mime.Text.MIMEText(body, 'plain', 'utf-8')
    html_text = email.mime.Text.MIMEText(body, 'html', 'utf-8')
    message.attach(plain_text)
    message.attach(html_text)
    return message

  def _send_email(self, to, from_, cc, subject, body):
    mail_message = self._generate_email(to, from_, cc, subject, body)
    response = self._send('/_ah/mail/%s' % to, mail_message)
    self.response.status = response.status

  def _send(self, relative_url, mail_message):
    return self.dispatcher.add_request(
        method='POST',
        relative_url=relative_url,
        headers=[('Content-Type', 'message/rfc822')],
        body=mail_message.as_string(),
        source_ip=REMOTE_IP)
