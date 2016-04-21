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





"""Errors used in the Python appinfo API, used by app developers."""










class Error(Exception):
  """Base datastore AppInfo type."""


class EmptyConfigurationFile(Error):
  """Tried to load empty configuration file"""


class MultipleConfigurationFile(Error):
  """Tried to load configuration file with multiple AppInfo objects"""


class UnknownHandlerType(Error):
  """Raised when it is not possible to determine URL mapping type."""


class UnexpectedHandlerAttribute(Error):
  """Raised when a handler type has an attribute that it does not use."""


class MissingHandlerAttribute(Error):
  """Raised when a handler is missing an attribute required by its type."""


class MissingURLMapping(Error):
  """Raised when there are no URL mappings in external appinfo."""


class TooManyURLMappings(Error):
  """Raised when there are too many URL mappings in external appinfo."""


class PositionUsedInAppYamlHandler(Error):
  """Raised when position attribute is used in handler in AppInfoExternal."""


class InvalidBuiltinFormat(Error):
  """Raised when the name of the builtin in a list item cannot be identified."""


class MultipleBuiltinsSpecified(Error):
  """Raised when more than one builtin is specified in a single list element."""


class DuplicateBuiltinsSpecified(Error):
  """Raised when a builtin is specified more than once in the same file."""


class BackendNotFound(Error):
  """Raised when a Backend is required but not specified."""


class DuplicateBackend(Error):
  """Raised when a backend is found more than once in 'backends'."""


class MissingApiConfig(Error):
  """Raised if an api_endpoint handler is configured but no api_config."""


class RuntimeDoesNotSupportLibraries(Error):
  """Raised when 'libraries' is used in a runtime that does not support it."""


class DuplicateLibrary(Error):
  """Raised when a library is found more than once in 'libraries'."""


class InvalidLibraryVersion(Error):
  """Raised when a library uses a version that isn't supported."""


class InvalidLibraryName(Error):
  """Raised when a library is specified that isn't supported."""


class ThreadsafeWithCgiHandler(Error):
  """Raised when threadsafe is enabled with a CGI handler specified."""


class MissingThreadsafe(Error):
  """Raised when the runtime needs a threadsafe declaration and it's missing."""
