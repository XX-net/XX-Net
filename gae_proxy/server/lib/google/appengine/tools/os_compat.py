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
"""OS cross-platform compatibility tweaks.

This module will, on import, change some parts of the running evironment so
that other modules do not need special handling when running on different
operating systems, such as Linux/Mac OSX/Windows.

Some of these changes must be done before other modules are imported, so
always import this module first.
"""








import os
os.environ['TZ'] = 'UTC'
import time
if hasattr(time, 'tzset'):
  time.tzset()

import __builtin__






if 'WindowsError' in __builtin__.__dict__:
  WindowsError = WindowsError
else:
  class WindowsError(Exception):
    """A fake Windows Error exception which should never be thrown."""




ERROR_PATH_NOT_FOUND = 3
ERROR_ACCESS_DENIED = 5
ERROR_SHARING_VIOLATION = 32
ERROR_ALREADY_EXISTS = 183
WSAECONNABORTED = 10053
