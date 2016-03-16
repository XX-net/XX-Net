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
"""An abstraction around the source and classfiles for a Java application."""




import os
import os.path
import google


_SDKROOT = os.path.dirname(os.path.dirname(google.__file__))


class JavaApplication(object):
  """An abstraction around the compiled class files for a Java application."""

  def __init__(self, module_configuration):
    """Initializer for Module.

    Args:
      module_configuration: An application_configuration.ModuleConfiguration
          instance storing the configuration data for a module.
    """
    self._module_configuration = module_configuration

  def get_environment(self):
    """Return the environment that should be used to run the Java executable."""
    environ = {'SDKROOT': _SDKROOT,
               'PWD': self._module_configuration.application_root,
               'TZ': 'UTC',
               'APPLICATION_ID': self._module_configuration.application}
    # Most of the env variables are needed for a JVM on Windows.
    for var in ('PATH', 'SYSTEMROOT', 'USER', 'TMP', 'TEMP'):
      if var in os.environ:
        environ[var] = os.environ[var]
    return environ
