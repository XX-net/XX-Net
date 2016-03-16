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




"""Exceptions raised my mail API."""



class Error(Exception):
  """Base Mail error type."""

class BadRequestError(Error):
  """Email is not valid."""

class InvalidSenderError(Error):
  """Sender is not a permitted to send mail for this application."""

class InvalidEmailError(Error):
  """Bad email set on an email field."""

class InvalidAttachmentTypeError(Error):
  """Invalid file type for attachments.  We don't send viruses!"""

class InvalidHeaderNameError(Error):
  """Invalid name for mail header."""

class MissingRecipientsError(Error):
  """No recipients specified in message."""

class MissingSenderError(Error):
  """No sender specified in message."""

class MissingSubjectError(Error):
  """Subject not specified in message."""

class MissingBodyError(Error):
  """No body specified in message."""

class PayloadEncodingError(Error):
  """Unknown payload encoding."""

class UnknownEncodingError(PayloadEncodingError):
  """Raised when encoding is not known."""

class UnknownCharsetError(PayloadEncodingError):
  """Raised when charset is not known."""
