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
"""A handler that displays servers and their instances."""

from google.appengine.tools.devappserver2.admin import admin_request_handler


class ModulesHandler(admin_request_handler.AdminRequestHandler):

  def get(self):
    values = {'modules': self.dispatcher.modules}
    self.response.write(self.render('modules.html', values))
