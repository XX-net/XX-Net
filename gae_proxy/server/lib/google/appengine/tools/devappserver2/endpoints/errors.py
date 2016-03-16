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
"""Error handling and exceptions used in the local Cloud Endpoints server."""








import json
import logging

from google.appengine.tools.devappserver2.endpoints import generated_error_info


__all__ = ['BackendError',
           'BasicTypeParameterError',
           'EnumRejectionError',
           'InvalidParameterError',
           'RequestError',
           'RequestRejectionError']

_INVALID_ENUM_TEMPLATE = 'Invalid string value: %r. Allowed values: %r'
_INVALID_BASIC_PARAM_TEMPLATE = 'Invalid %s value: %r.'


class RequestError(Exception):
  """Base class for errors that happen while processing a request."""

  def status_code(self):
    """HTTP status code number associated with this error.

    Subclasses must implement this, returning an integer with the status
    code number for the error.

    Example: 400

    Raises:
      NotImplementedError: Subclasses must override this function.
    """
    raise NotImplementedError

  def message(self):
    """Text message explaining the error.

    Subclasses must implement this, returning a string that explains the
    error.

    Raises:
      NotImplementedError: Subclasses must override this function.
    """
    raise NotImplementedError

  def reason(self):
    """Get the reason for the error.

    Error reason is a custom string in the Cloud Endpoints server.  When
    possible, this should match the reason that the live server will generate,
    based on the error's status code.  If this returns None, the error formatter
    will attempt to generate a reason from the status code.

    Returns:
      None, by default.  Subclasses can override this if they have a specific
      error reason.
    """
    raise NotImplementedError

  def domain(self):
    """Get the domain for this error.

    Returns:
      The string 'global' by default.  Subclasses can override this if they have
      a different domain.
    """
    return 'global'

  def extra_fields(self):
    """Return a dict of extra fields to add to the error response.

    Some errors have additional information.  This provides a way for subclasses
    to provide that information.

    Returns:
      None, by default.  Subclasses can return a dict with values to add
      to the error response.
    """
    return None

  def __format_error(self, error_list_tag):
    """Format this error into a JSON response.

    Args:
      error_list_tag: A string specifying the name of the tag to use for the
        error list.

    Returns:
      A dict containing the reformatted JSON error response.
    """
    error = {'domain': self.domain(),
             'reason': self.reason(),
             'message': self.message()}
    error.update(self.extra_fields() or {})
    return {'error': {error_list_tag: [error],
                      'code': self.status_code(),
                      'message': self.message()}}

  def rest_error(self):
    """Format this error into a response to a REST request.

    Returns:
      A string containing the reformatted error response.
    """
    error_json = self.__format_error('errors')
    return json.dumps(error_json, indent=1, sort_keys=True)

  def rpc_error(self):
    """Format this error into a response to a JSON RPC request.


    Returns:
      A dict containing the reformatted JSON error response.
    """
    return self.__format_error('data')


class RequestRejectionError(RequestError):
  """Base class for invalid/rejected requests.

  To be raised when parsing the request values and comparing them against the
  generated discovery document.
  """

  def status_code(self):
    return 400


class InvalidParameterError(RequestRejectionError):
  """Base class for invalid parameter errors.

  Child classes only need to implement the message() function.
  """

  def __init__(self, parameter_name, value):
    """Constructor for InvalidParameterError.

    Args:
      parameter_name: String; the name of the parameter which had a value
        rejected.
      value: The actual value passed in for the parameter. Usually string.
    """
    super(InvalidParameterError, self).__init__()
    self.parameter_name = parameter_name
    self.value = value

  def reason(self):
    """Returns the server's reason for this error.

    Returns:
      A string containing a short error reason.
    """
    return 'invalidParameter'

  def extra_fields(self):
    """Returns extra fields to add to the error response.

    Returns:
      A dict containing extra fields to add to the error response.
    """
    return {'locationType': 'parameter',
            'location': self.parameter_name}


class BasicTypeParameterError(InvalidParameterError):
  """Request rejection exception for basic types (int, float)."""

  def __init__(self, parameter_name, value, type_name):
    """Constructor for BasicTypeParameterError.

    Args:
      parameter_name: String; the name of the parameter which had a value
        rejected.
      value: The actual value passed in for the enum. Usually string.
      type_name: Descriptive name of the data type expected.
    """
    super(BasicTypeParameterError, self).__init__(parameter_name, value)
    self.type_name = type_name

  def message(self):
    """A descriptive message describing the error."""
    return _INVALID_BASIC_PARAM_TEMPLATE % (self.type_name, self.value)






class EnumRejectionError(InvalidParameterError):
  """Custom request rejection exception for enum values."""

  def __init__(self, parameter_name, value, allowed_values):
    """Constructor for EnumRejectionError.

    Args:
      parameter_name: String; the name of the enum parameter which had a value
        rejected.
      value: The actual value passed in for the enum. Usually string.
      allowed_values: List of strings allowed for the enum.
    """
    super(EnumRejectionError, self).__init__(parameter_name, value)
    self.allowed_values = allowed_values

  def message(self):
    """A descriptive message describing the error."""
    return _INVALID_ENUM_TEMPLATE % (self.value, self.allowed_values)


class BackendError(RequestError):
  """Exception raised when the backend SPI returns an error code."""

  def __init__(self, response):
    super(BackendError, self).__init__()
    # Convert backend error status to whatever the live server would return.
    status_code = self._get_status_code(response.status)
    self._error_info = generated_error_info.get_error_info(status_code)

    try:
      error_json = json.loads(response.content)
      self._message = error_json.get('error_message')
    except TypeError:
      self._message = response.content

  def _get_status_code(self, http_status):
    """Get the HTTP status code from an HTTP status string.

    Args:
      http_status: A string containing a HTTP status code and reason.

    Returns:
      An integer with the status code number from http_status.
    """
    try:
      return int(http_status.split(' ', 1)[0])
    except TypeError:
      logging.warning('Unable to find status code in HTTP status %r.',
                      http_status)
    return 500

  def status_code(self):
    """Return the HTTP status code number for this error.

    Returns:
      An integer containing the status code for this error.
    """
    return self._error_info.http_status

  def message(self):
    """Return a descriptive message for this error.

    Returns:
      A string containing a descriptive message for this error.
    """
    return self._message

  def reason(self):
    """Return the short reason for this error.

    Returns:
      A string with the reason for this error.
    """
    return self._error_info.reason

  def domain(self):
    """Return the remapped domain for this error.

    Returns:
      A string containing the remapped domain for this error.
    """
    return self._error_info.domain
