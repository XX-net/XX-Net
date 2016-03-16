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
"""Socket exception classes.

These exception classes are used instead of those provided by the system.

They are in a separate file to avoid circular dependencies.
"""


class error(IOError):
  """Base error class."""


class gaierror(error):
  pass


class herror(error):
  pass


class timeout(error):
  pass
