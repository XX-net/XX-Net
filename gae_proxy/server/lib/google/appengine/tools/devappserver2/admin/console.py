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
"""A handler that provides an interactive console."""



import threading

from google.appengine.tools.devappserver2 import module
from google.appengine.tools.devappserver2.admin import admin_request_handler


class ConsoleRequestHandler(admin_request_handler.AdminRequestHandler):
  """Provides an interactive console for modules that support it."""

  _modulename_to_shell_module = {}
  _modulename_to_shell_module_lock = threading.Lock()

  def get(self):
    self.response.write(
        self.render('console.html',
                    {'modules': [modul for modul in self.dispatcher.modules
                                 if modul.supports_interactive_commands]}))

  def post(self):
    module_name = self.request.get('module_name')
    with self._modulename_to_shell_module_lock:
      if module_name in self._modulename_to_shell_module:
        modul = self._modulename_to_shell_module[module_name]
      else:
        modul = self.dispatcher.get_module_by_name(
            module_name).create_interactive_command_module()
        self._modulename_to_shell_module[module_name] = modul

    self.response.content_type = 'text/plain'
    try:
      response = modul.send_interactive_command(self.request.get('code'))
    except module.InteractiveCommandError, e:
      response = str(e)

    self.response.write(response)

  @classmethod
  def quit(cls):
    with cls._modulename_to_shell_module_lock:
      for shell_module in cls._modulename_to_shell_module.itervalues():
        shell_module.quit()

  @classmethod
  def restart(cls, request, module_name):
    with cls._modulename_to_shell_module_lock:
      if module_name in cls._modulename_to_shell_module:
        modul = cls._modulename_to_shell_module[module_name]
        modul.restart()
