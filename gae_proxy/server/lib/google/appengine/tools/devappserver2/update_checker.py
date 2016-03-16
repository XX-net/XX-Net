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
"""Checks for SDK updates."""



import sys

from google.appengine.tools import appengine_rpc
from google.appengine.tools import sdk_update_checker

SDK_PRODUCT = 'devappserver2_py'
# The server to use when checking for SDK updates.
_UPDATE_SERVER = 'appengine.google.com'


def _get_user_agent():
  """Returns the value of the 'User-Agent' header to use for update requests."""
  product_tokens = []
  version = sdk_update_checker.GetVersionObject()
  if version is None:
    release = 'unknown'
  else:
    release = version['release']

  product_tokens.append('%s/%s' % (SDK_PRODUCT, release))

  # Platform.
  product_tokens.append(appengine_rpc.GetPlatformToken())

  # Python version.
  python_version = '.'.join(str(i) for i in sys.version_info)
  product_tokens.append('Python/%s' % python_version)

  return ' '.join(product_tokens)


def _get_source_name():
  """Gets the name of this source version. Used for authentication."""
  version = sdk_update_checker.GetVersionObject()
  if version is None:
    release = 'unknown'
  else:
    release = version['release']
  return 'Google-appcfg-%s' % release


def check_for_updates(application_configuration):
  """Checks for updates to the SDK.

  A message will be printed on stdout if the SDK is not up-to-date.

  Args:
    application_configuration: The
        application_configuration.ApplicationConfiguration for the application.
        Used to check if the api_versions used by the modules are supported by
        the SDK.

  Raises:
    SystemExit: if the api_version used by a module is not supported by the
        SDK.
  """
  update_server = appengine_rpc.HttpRpcServer(
      _UPDATE_SERVER,
      lambda: ('unused_email', 'unused_password'),
      _get_user_agent(),
      _get_source_name())  # TODO: is the source name arg necessary?
  # Don't try to talk to ClientLogin.
  update_server.authenticated = True

  # TODO: Update check needs to be refactored so the api_version for
  # all runtimes can be checked without generating duplicate nag messages.
  if application_configuration.modules:
    update_check = sdk_update_checker.SDKUpdateChecker(
        update_server, application_configuration.modules)
    update_check.CheckSupportedVersion()  # Can raise SystemExit.
    if update_check.AllowedToCheckForUpdates():
      update_check.CheckForUpdates()
