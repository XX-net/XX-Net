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
"""Client deploy info.

Library for parsing client_deploy.yaml files and working with these in memory.
"""






from google.appengine.api import appinfo
from google.appengine.api import validation
from google.appengine.api import yaml_builder
from google.appengine.api import yaml_listener
from google.appengine.api import yaml_object

RUNTIME = 'runtime'
START_TIME_USEC = 'start_time_usec'
END_TIME_USEC = 'end_time_usec'
REQUESTS = 'requests'
SUCCESS = 'success'
PATH = 'path'
RESPONSE_CODE = 'response_code'
REQUEST_SIZE_BYTES = 'request_size_bytes'
SDK_VERSION = 'sdk_version'


class Request(validation.Validated):
  """A Request describes a single http request within a deployment attempt."""
  ATTRIBUTES = {
      PATH: validation.TYPE_STR,
      RESPONSE_CODE: validation.Range(100, 599),
      START_TIME_USEC: validation.TYPE_LONG,
      END_TIME_USEC: validation.TYPE_LONG,
      REQUEST_SIZE_BYTES: validation.TYPE_LONG,
  }


class ClientDeployInfoExternal(validation.Validated):
  """Describes the format of a client_deployinfo.yaml file."""
  ATTRIBUTES = {
      RUNTIME: appinfo.RUNTIME_RE_STRING,
      START_TIME_USEC: validation.TYPE_LONG,
      END_TIME_USEC: validation.TYPE_LONG,
      REQUESTS: validation.Optional(validation.Repeated(Request)),
      SUCCESS: validation.TYPE_BOOL,
      SDK_VERSION: validation.Optional(validation.TYPE_STR)
  }


class Error(Exception):
  """Base ClientDeployInfo Exception type."""


class EmptyYaml(Error):
  """Tried to load an empty yaml."""


class MultipleClientDeployInfo(Error):
  """Tried to load a yaml containing multiple client deploy info definitions."""


def LoadSingleClientDeployInfo(client_deploy_info):
  """Returns a ClientDeployInfoExternal from a deploy_info.yaml file or string.

  Args:
    client_deploy_info: The contents of a client_deploy_info.yaml file or
      string, or an open file object.

  Returns:
    A ClientDeployInfoExternal instance which represents the contents of the
    parsed yaml.

  Raises:
    EmptyYaml: when there are no documents in yaml.
    MultipleClientDeployInfo: when there are multiple documents in yaml.
    yaml_errors.EventError: when an error occurs while parsing the yaml.
  """
  builder = yaml_object.ObjectBuilder(ClientDeployInfoExternal)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)
  listener.Parse(client_deploy_info)

  parsed_yaml = handler.GetResults()
  if not parsed_yaml:
    raise EmptyYaml()
  if len(parsed_yaml) > 1:
    raise MultipleClientDeployInfo()
  return parsed_yaml[0]
