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
"""One place for all runtime instance factories."""



from google.appengine.tools.devappserver2 import custom_runtime
from google.appengine.tools.devappserver2 import go_runtime
from google.appengine.tools.devappserver2 import php_runtime
from google.appengine.tools.devappserver2 import python_runtime
# pylint: disable=g-import-not-at-top
try:
  from google.appengine.tools.devappserver2 import java_runtime
except ImportError:
  java_runtime = None
# pylint: enable=g-import-not-at-top

FACTORIES = {
    'go': go_runtime.GoRuntimeInstanceFactory,
    'php55': php_runtime.PHPRuntimeInstanceFactory,
    'python': python_runtime.PythonRuntimeInstanceFactory,
    'python27': python_runtime.PythonRuntimeInstanceFactory,
    'python-compat': python_runtime.PythonRuntimeInstanceFactory,
    'custom': custom_runtime.CustomRuntimeInstanceFactory,
}
if java_runtime:
  FACTORIES.update({
      'java': java_runtime.JavaRuntimeInstanceFactory,
      'java7': java_runtime.JavaRuntimeInstanceFactory,
  })


def valid_runtimes():
  return FACTORIES.keys()
