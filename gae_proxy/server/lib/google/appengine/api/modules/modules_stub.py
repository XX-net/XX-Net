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
"""Stub implementation of the modules service."""

from google.appengine.api import apiproxy_stub
from google.appengine.api import request_info
from google.appengine.api.modules import modules_service_pb
from google.appengine.runtime import apiproxy_errors


class ModulesServiceStub(apiproxy_stub.APIProxyStub):


  _ACCEPTS_REQUEST_ID = True
  THREADSAFE = True

  def __init__(self, request_data):
    super(ModulesServiceStub, self).__init__('modules',
                                             request_data=request_data)

  def _GetModuleFromRequest(self, request, request_id):
    dispatcher = self.request_data.get_dispatcher()
    if request.has_module():
      module = request.module()
    else:
      module = self.request_data.get_module(request_id)
    return module, dispatcher

  def _GetModuleAndVersionFromRequest(self, request, request_id):
    module, dispatcher = self._GetModuleFromRequest(request, request_id)
    if request.has_version():
      version = request.version()
    else:
      version = self.request_data.get_version(request_id)
      if version not in dispatcher.get_versions(module):
        version = dispatcher.get_default_version(module)
    return module, version, dispatcher

  def _Dynamic_GetModules(self, request, response, request_id):
    dispatcher = self.request_data.get_dispatcher()
    for module in dispatcher.get_module_names():
      response.add_module(module)

  def _Dynamic_GetVersions(self, request, response, request_id):
    module, dispatcher = self._GetModuleFromRequest(request, request_id)
    try:
      for version in dispatcher.get_versions(module):
        response.add_version(version)
    except request_info.ModuleDoesNotExistError:
      raise apiproxy_errors.ApplicationError(
          modules_service_pb.ModulesServiceError.INVALID_MODULE)

  def _Dynamic_GetDefaultVersion(self, request, response, request_id):
    module, dispatcher = self._GetModuleFromRequest(request, request_id)
    try:
      response.set_version(dispatcher.get_default_version(module))
    except request_info.ModuleDoesNotExistError:
      raise apiproxy_errors.ApplicationError(
          modules_service_pb.ModulesServiceError.INVALID_MODULE)

  def _Dynamic_GetNumInstances(self, request, response, request_id):
    try:
      module, version, dispatcher = self._GetModuleAndVersionFromRequest(
          request, request_id)
      response.set_instances(dispatcher.get_num_instances(module, version))
    except (request_info.ModuleDoesNotExistError,
            request_info.VersionDoesNotExistError,
            request_info.NotSupportedWithAutoScalingError):
      raise apiproxy_errors.ApplicationError(
          modules_service_pb.ModulesServiceError.INVALID_VERSION)

  def _Dynamic_SetNumInstances(self, request, response, request_id):
    try:
      module, version, dispatcher = self._GetModuleAndVersionFromRequest(
          request, request_id)
      dispatcher.set_num_instances(module, version, request.instances())
    except (request_info.ModuleDoesNotExistError,
            request_info.VersionDoesNotExistError,
            request_info.NotSupportedWithAutoScalingError):
      raise apiproxy_errors.ApplicationError(
          modules_service_pb.ModulesServiceError.INVALID_VERSION)

  def _Dynamic_StartModule(self, request, response, request_id):
    module = request.module()
    version = request.version()
    dispatcher = self.request_data.get_dispatcher()
    try:
      dispatcher.start_version(module, version)
    except (request_info.ModuleDoesNotExistError,
            request_info.VersionDoesNotExistError,
            request_info.NotSupportedWithAutoScalingError):
      raise apiproxy_errors.ApplicationError(
          modules_service_pb.ModulesServiceError.INVALID_VERSION)
    except request_info.VersionAlreadyStartedError:
      raise apiproxy_errors.ApplicationError(
          modules_service_pb.ModulesServiceError.UNEXPECTED_STATE)

  def _Dynamic_StopModule(self, request, response, request_id):
    try:
      module, version, dispatcher = self._GetModuleAndVersionFromRequest(
          request, request_id)
      dispatcher.stop_version(module, version)
    except (request_info.ModuleDoesNotExistError,
            request_info.VersionDoesNotExistError,
            request_info.NotSupportedWithAutoScalingError):
      raise apiproxy_errors.ApplicationError(
          modules_service_pb.ModulesServiceError.INVALID_VERSION)
    except request_info.VersionAlreadyStoppedError:
      raise apiproxy_errors.ApplicationError(
          modules_service_pb.ModulesServiceError.UNEXPECTED_STATE)

  def _Dynamic_GetHostname(self, request, response, request_id):
    if request.has_instance():
      instance = request.instance()
    else:
      instance = None
    try:
      module, version, dispatcher = self._GetModuleAndVersionFromRequest(
          request, request_id)
      response.set_hostname(dispatcher.get_hostname(module, version, instance))
    except (request_info.ModuleDoesNotExistError,
            request_info.VersionDoesNotExistError):
      raise apiproxy_errors.ApplicationError(
          modules_service_pb.ModulesServiceError.INVALID_MODULE)
    except request_info.InvalidInstanceIdError:
      raise apiproxy_errors.ApplicationError(
          modules_service_pb.ModulesServiceError.INVALID_INSTANCES)
