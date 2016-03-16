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




"""Handler library for inbound Mail API.

Contains handlers to help with receiving mail and mail bounces.

  InboundMailHandler: Has helper method for easily setting up
    email receivers.
  BounceNotificationHandler: Has helper method for easily setting
    up bounce notification receiver. Will parse HTTP request to
    extract bounce notification.
"""










from google.appengine.api import mail
from google.appengine.ext import webapp


MAIL_HANDLER_URL_PATTERN = '/_ah/mail/.+'
BOUNCE_NOTIFICATION_HANDLER_URL_PATH = '/_ah/bounce'


class InboundMailHandler(webapp.RequestHandler):
  """Base class for inbound mail handlers.

  Example:

    # Sub-class overrides receive method.
    class HelloReceiver(InboundMailHandler):

      def receive(self, mail_message):
        logging.info('Received greeting from %s: %s' % (mail_message.sender,
                                                        mail_message.body))


    # Map mail handler to appliction.
    application = webapp.WSGIApplication([
        HelloReceiver.mapping(),
    ])
  """

  def post(self):
    """Transforms body to email request."""
    self.receive(mail.InboundEmailMessage(self.request.body))

  def receive(self, mail_message):
    """Receive an email message.

    Override this method to implement an email receiver.

    Args:
      mail_message: InboundEmailMessage instance representing received
        email.
    """
    pass

  @classmethod
  def mapping(cls):
    """Convenience method to map handler class to application.

    Returns:
      Mapping from email URL to inbound mail handler class.
    """
    return MAIL_HANDLER_URL_PATTERN, cls


class BounceNotificationHandler(webapp.RequestHandler):
  """Base class for bounce notification handlers.

  Example:

    # Sub-class overrides receive method.
    class BounceLogger(BounceNotificationHandler):

      def receive(self, bounce_notification):
        logging.info('Received bounce from ' %
            bounce_notification.notification_from)


    # Map bounce handler to application
    application = webapp.WSGIApplication([
        BounceLogger.mapping(),
    ])
  """

  def post(self):
    """Transforms POST body to bounce request."""
    self.receive(BounceNotification(self.request.POST))

  def receive(self, bounce_notification):
    pass

  @classmethod
  def mapping(cls):
    """Convenience method to map handler class to application.

    Returns:
      Mapping from bounce URL to bounce notification handler class.
    """
    return BOUNCE_NOTIFICATION_HANDLER_URL_PATH, cls


class BounceNotification(object):
  """Encapsulates a bounce notification received by the application."""

  def __init__(self, post_vars):
    """Constructs a new BounceNotification from an HTTP request.

    Properties:
      original: a dict describing the message that caused the bounce.
      notification: a dict describing the bounce itself.
      original_raw_message: the raw message that caused the bounce.

    The 'original' and 'notification' dicts contain the following keys:
      to, cc, bcc, from, subject, text

    Args:
      post_vars: a dict-like object containing bounce information.
          This is typically the self.request.POST variable of a RequestHandler
          object. The following keys are handled in the dict:
            original-from
            original-to
            original-cc
            original-bcc
            original-subject
            original-text
            notification-from
            notification-to
            notification-cc
            notification-bcc
            notification-subject
            notification-text
            raw-message
    """
    self.__original = {}
    self.__notification = {}
    for field in ['to', 'cc', 'bcc', 'from', 'subject', 'text']:
      self.__original[field] = post_vars.get('original-' + field, '')
      self.__notification[field] = post_vars.get('notification-' + field, '')

    self.__original_raw_message = mail.InboundEmailMessage(
        post_vars.get('raw-message', ''))

  @property
  def original(self):
    return self.__original

  @property
  def notification(self):
    return self.__notification

  @property
  def original_raw_message(self):
    return self.__original_raw_message
