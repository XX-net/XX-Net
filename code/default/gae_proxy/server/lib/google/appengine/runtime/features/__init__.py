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
"""features module.

This module simplifies the access to the appengine feature flags.
"""

import __builtin__






def IsEnabled(feature_name, default=False):
  """Indicates if a specific feature flag is enabled.

  Args:
    feature_name: The name of the feature flag to check.
    default: Default value if the flags are not initialized (In a test
             environment for example).

  Returns:
    True/False if the flag is set/not set or default if the feature flags
    were not initialized.
  """
  try:

    return feature_name in __builtin__._APPENGINE_FEATURE_FLAGS
  except AttributeError:
    return default
