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
"""Utils for working with environment variables in devappserver2."""

from google.appengine.tools.devappserver2 import http_runtime_constants


_ENVIRONS_TO_PROPAGATE_FULL_NAMES = set([
    http_runtime_constants.APPENGINE_ENVIRON_PREFIX + x for x in
    http_runtime_constants.ENVIRONS_TO_PROPAGATE])


def propagate_environs(src, dst):
  """Propagates environment variables to the request handlers.

  Propagation rules:
      Environs that do not start with HTTP_ do not propagate.
      Environs formatted like APPENGINE_HEADER_PREFIX + name, where name is one
          of ENVIRONS_TO_PROPAGATE set have APPENGINE_HEADER_PREFIX cut out.
      Internal Dev AppServer environs starting with APPENGINE_DEV_ENVIRON_PREFIX
          do not propagate.

  Args:
      src: source environ dict.
      dst: destination environ dict.
  """
  for key, value in src.iteritems():
    if key in _ENVIRONS_TO_PROPAGATE_FULL_NAMES:
      dst[key[len(http_runtime_constants.APPENGINE_ENVIRON_PREFIX):]] = value
    elif (key.startswith('HTTP_') and not
          key.startswith(http_runtime_constants.APPENGINE_DEV_ENVIRON_PREFIX)):
      dst[key] = value
