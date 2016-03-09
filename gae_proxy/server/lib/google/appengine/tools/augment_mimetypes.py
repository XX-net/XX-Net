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
"""Augment the mimetypes provided by Python."""

import mimetypes


def init():
  mimetypes.add_type('application/dart', '.dart')
  mimetypes.add_type('text/css', '.gss')
  mimetypes.add_type('text/html', '.ng')
  mimetypes.add_type('application/x-font-ttf', '.ttf')
  mimetypes.add_type('application/font-woff', '.woff')
  mimetypes.add_type('application/font-woff2', '.woff2')
