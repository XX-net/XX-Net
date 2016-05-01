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





"""Errors used in the YAML API, which is used by app developers."""




class Error(Exception):
  """Base datastore yaml error type."""

class ProtocolBufferParseError(Error):
  """Error in protocol buffer parsing"""


class EmptyConfigurationFile(Error):
  """Tried to load empty configuration file."""


class MultipleConfigurationFile(Error):
  """Tried to load configuration file with multiple objects."""


class AmbiguousConfigurationFiles(Error):
  """Both YAML and XML files exist for the same configuration information."""


class UnexpectedAttribute(Error):
  """Raised when an unexpected attribute is encounted."""


class DuplicateAttribute(Error):
  """Generated when an attribute is assigned to twice."""


class ListenerConfigurationError(Error):
  """Generated when there is a parsing problem due to configuration."""


class IllegalEvent(Error):
  """Raised when an unexpected event type is received by listener."""


class InternalError(Error):
  """Raised when an internal implementation error is detected."""


class EventListenerError(Error):
  """Top level exception raised by YAML listener.

  Any exception raised within the process of parsing a YAML file via an
  EventListener is caught and wrapped in an EventListenerError.  The causing
  exception is maintained, but additional useful information is saved which
  can be used for reporting useful information to users.

  Attributes:
    cause: The original exception which caused the EventListenerError.
  """

  def __init__(self, cause):
    """Initialize event-listener error."""
    if hasattr(cause, 'args') and cause.args:
      Error.__init__(self, *cause.args)
    else:


      Error.__init__(self, str(cause))
    self.cause = cause


class EventListenerYAMLError(EventListenerError):
  """Generated specifically for yaml.error.YAMLError."""


class EventError(EventListenerError):
  """Generated specifically when an error occurs in event handler.

  Attributes:
    cause: The original exception which caused the EventListenerError.
    event: Event being handled when exception occured.
  """

  def __init__(self, cause, event):
    """Initialize event-listener error."""
    EventListenerError.__init__(self, cause)
    self.event = event

  def __str__(self):
    return '%s\n%s' % (self.cause, self.event.start_mark)
