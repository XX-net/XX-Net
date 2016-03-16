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
"""Constants used for communicating with the Python devappserver2 runtime."""



SERVER_SOFTWARE = 'Development/2.0'

# Internal AppEngine prefix for Headers (Environment variables)
# used in production. See apphosting/base/http_proto.cc for the full list.
APPENGINE_HEADER_PREFIX = 'X-Appengine-'
APPENGINE_ENVIRON_PREFIX = 'HTTP_X_APPENGINE_'

# Prefix for Headers (Environment variables) used in Dev AppServer only.
APPENGINE_DEV_HEADER_PREFIX = APPENGINE_HEADER_PREFIX + 'Dev-'
APPENGINE_DEV_ENVIRON_PREFIX = APPENGINE_ENVIRON_PREFIX + 'DEV_'

# These values are present in the VM runtime in production.
_VM_ENVIRONS_TO_PROPAGATE = {
    'API_HOST',
    'API_PORT',
    'GAE_LONG_APP_ID',
    'GAE_PARTITION',
    'GAE_MODULE_NAME',
    'GAE_MODULE_VERSION',
    'GAE_MINOR_VERSION',
    'GAE_MINOR_VERSION',
    'GAE_SERVER_PORT',
    'MODULE_YAML_PATH',
    'SERVER_SOFTWARE'
}

# These values are passed as part of UPRequest proto in Prod.
# Propagation rule: Cut the prefix.
ENVIRONS_TO_PROPAGATE = {
    'BACKEND_ID',
    'DEFAULT_VERSION_HOSTNAME',
    'USER_ID',
    'USER_IS_ADMIN',
    'USER_EMAIL',
    'USER_NICKNAME',
    'USER_ORGANIZATION',
    'REMOTE_ADDR',
    'REQUEST_ID_HASH',
    'REQUEST_LOG_ID',
    'SERVER_NAME',
    'SERVER_PORT',
    'SERVER_PROTOCOL',
}.union(_VM_ENVIRONS_TO_PROPAGATE)

REQUEST_ID_HEADER = APPENGINE_DEV_HEADER_PREFIX + 'Request-Id'
REQUEST_ID_ENVIRON = APPENGINE_DEV_ENVIRON_PREFIX + 'REQUEST_ID'

# TODO: rename to SCRIPT_ENVIRON
SCRIPT_HEADER = APPENGINE_DEV_ENVIRON_PREFIX + 'SCRIPT'

# TODO: rename to REQUEST_TYPE_ENVIRON
# A request header where the value is a string containing the request type, e.g.
# background.
REQUEST_TYPE_HEADER = APPENGINE_DEV_ENVIRON_PREFIX + 'REQUEST_TYPE'

# A response header used by the runtime to indicate that an uncaught error has
# ocurred and that a user-specified error handler should be used if available.
ERROR_CODE_HEADER = '%sError-Code' % APPENGINE_HEADER_PREFIX
