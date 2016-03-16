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
"""Serves content for "script" handlers using the Java runtime."""




import os
import os.path
import sys
import tempfile
import threading

import google

from google.appengine.api import appinfo
from google.appengine.tools.devappserver2 import http_runtime
from google.appengine.tools.devappserver2 import instance
from google.appengine.tools.devappserver2 import java_application

# TODO: figure out what's needed to react to file changes


class JavaRuntimeInstanceFactory(instance.InstanceFactory):
  """A factory that creates new Java runtime Instances."""

  START_URL_MAP = appinfo.URLMap(
      url='/_ah/start',
      script='_java_app',
      login='admin')
  WARMUP_URL_MAP = appinfo.URLMap(
      url='/_ah/warmup',
      script='_java_app',
      login='admin')
  FILE_CHANGE_INSTANCE_RESTART_POLICY = instance.ALWAYS

  def __init__(self, request_data, runtime_config_getter, module_configuration):
    """Initializer for JavaRuntimeInstanceFactory.

    Args:
      request_data: A wsgi_request_info.WSGIRequestInfo that will be provided
          with request information for use by API stubs.
      runtime_config_getter: A function that can be called without arguments
          and returns the runtime_config_pb2.RuntimeConfig containing the
          configuration for the runtime.
      module_configuration: An application_configuration.ModuleConfiguration
          instance representing the configuration of the module that owns the
          runtime.
    """
    super(JavaRuntimeInstanceFactory, self).__init__(request_data, 1)
    self._runtime_config_getter = runtime_config_getter
    self._module_configuration = module_configuration
    self._application_lock = threading.Lock()
    self._java_application = java_application.JavaApplication(
        self._module_configuration)
    self._for_jetty9 = (module_configuration.runtime == 'vm' or
                        module_configuration.env == '2')
    self._java_command = self._make_java_command()

  def _make_java_command(self):
    # We should be in .../google/appengine/tools/devappserver2/java_runtime.py
    # and we want to find .../google/appengine/tools and thence
    # .../google/appengine/tools/java/lib

    java_home = os.environ.get('JAVA_HOME')

    if java_home and os.path.exists(java_home):
      java_bin = os.path.join(java_home, 'bin/java')
    else:
      java_bin = 'java'

    java_dir = os.environ.get('APP_ENGINE_JAVA_PATH', None)
    tools_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    if not java_dir or not os.path.exists(java_dir):
      java_dir = os.path.join(tools_dir, 'java')

    java_lib_dir = os.path.join(java_dir, 'lib')
    assert os.path.isdir(java_lib_dir), java_lib_dir
    class_path = os.path.join(java_lib_dir, 'appengine-tools-api.jar')
    assert os.path.isfile(class_path), class_path
    jdk_overrides_jar = os.path.join(java_lib_dir, 'override',
                                     'appengine-dev-jdk-overrides.jar')
    assert os.path.isfile(jdk_overrides_jar), jdk_overrides_jar

    if self._for_jetty9:
      jetty_home = os.environ.get('APP_ENGINE_JETTY_HOME', None)
      jetty_base = os.environ.get('APP_ENGINE_JETTY_BASE', None)
      if not jetty_home:
        jetty_home = os.path.join(java_lib_dir, 'java-managed-vm',
                                  'appengine-java-vmruntime')
      if not jetty_base:
        jetty_base = os.path.join(java_lib_dir, 'jetty-base-sdk')

      args = [
          java_bin,
          ('-Dgcloud.java.application=%s' %
           self._module_configuration.application_root),
          '-Djetty.home=%s' % jetty_home,
          '-Djetty.base=%s' % jetty_base,
      ]
      args.extend(self._runtime_config_getter().java_config.jvm_args)
      args.append('-jar')
      args.append('%s/start.jar' % jetty_home)
    else:
      args = [
          java_bin,
          '-cp', class_path,
          '-Dappengine.sdk.root=' + java_dir,
          '-Xbootclasspath/p:' + jdk_overrides_jar,
      ]
      if sys.platform == 'darwin':
        args.append('-XstartOnFirstThread')
      args.extend(self._runtime_config_getter().java_config.jvm_args)
      args.append(
          'com.google.appengine.tools.development.devappserver2.'
          'StandaloneInstance')
    return args

  def get_restart_directories(self):
    """Returns a list of directories where changes trigger a restart.

    Returns:
      A list of directories where changes trigger a restart.
    """
    # TODO: implement
    return []

  def files_changed(self):
    """Called when a file relevant to the factory *might* have changed."""
    # TODO: implement

  def configuration_changed(self, config_changes):
    """Called when the configuration of the module has changed.

    Args:
      config_changes: A set containing the changes that occured. See the
          *_CHANGED constants in the application_configuration module.
    """
    # TODO: implement

  def new_instance(self, instance_id, expect_ready_request=False):
    """Create and return a new Instance.

    Args:
      instance_id: A string or integer representing the unique (per module) id
          of the instance.
      expect_ready_request: If True then the instance will be sent a special
          request (i.e. /_ah/warmup or /_ah/start) before it can handle external
          requests.

    Returns:
      The newly created instance.Instance.
    """

    def instance_config_getter():
      runtime_config = self._runtime_config_getter()
      runtime_config.instance_id = str(instance_id)
      return runtime_config

    def extra_args_getter(port):
      return 'jetty.port=%s' % port

    env = self._java_application.get_environment()
    runtime_config = instance_config_getter()
    for env_entry in runtime_config.environ:
      env[env_entry.key] = env_entry.value

    if self._for_jetty9:
      start_process_flavor = http_runtime.START_PROCESS_REVERSE_NO_FILE
      env['APP_ENGINE_LOG_CONFIG_PATTERN'] = (
          os.path.join(tempfile.mkdtemp(suffix='gae'), 'log.%g'))
    else:
      start_process_flavor = http_runtime.START_PROCESS_FILE

    with self._application_lock:
      proxy = http_runtime.HttpRuntimeProxy(
          self._java_command,
          instance_config_getter,
          self._module_configuration,
          env=env,
          start_process_flavor=start_process_flavor,
          extra_args_getter=extra_args_getter)

    return instance.Instance(self.request_data,
                             instance_id,
                             proxy,
                             self.max_concurrent_requests,
                             self.max_background_threads,
                             expect_ready_request)
