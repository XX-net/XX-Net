#
# Copyright 2008 The ndb Authors. All Rights Reserved.
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

"""Dynamically decide from where to import Google App Engine modules.

All other NDB code should import its Google App Engine modules from
this module.  If necessary, add new imports here (in both places).
"""

import os
import sys
try:
  import google
  GOOGLE_PACKAGE_PATH = set(google.__path__)
except ImportError:
  GOOGLE_PACKAGE_PATH = None


def set_appengine_imports():
  gae_path = os.getenv('GAE')
  if gae_path is None:
    return

  sys.path.insert(0, gae_path)
  sys.modules.pop('google', None)
  import dev_appserver
  dev_appserver.fix_sys_path()

  if GOOGLE_PACKAGE_PATH is not None:
    import google
    GOOGLE_PACKAGE_PATH.update(google.__path__)
    google.__path__ = list(GOOGLE_PACKAGE_PATH)


try:
  from google.appengine.datastore import entity_pb
  normal_environment = True
except ImportError:
  try:
    from google3.storage.onestore.v3 import entity_pb
    normal_environment = False
  except ImportError:
    # If we are running locally but outside the context of App Engine.
    try:
      set_appengine_imports()
      from google.appengine.datastore import entity_pb
      normal_environment = True
    except ImportError:
      raise ImportError('Unable to find the App Engine SDK. '
                        'Did you remember to set the "GAE" environment '
                        'variable to be the path to the App Engine SDK?')

if normal_environment:
  from google.appengine.api.blobstore import blobstore as api_blobstore
  from google.appengine.api import apiproxy_rpc
  from google.appengine.api import apiproxy_stub_map
  from google.appengine.api import datastore
  from google.appengine.api import datastore_errors
  from google.appengine.api import datastore_types
  from google.appengine.api import memcache
  from google.appengine.api import namespace_manager
  from google.appengine.api import prospective_search
  from google.appengine.api import taskqueue
  from google.appengine.api import urlfetch
  from google.appengine.api import users
  from google.appengine.api.prospective_search import prospective_search_pb
  from google.appengine.datastore import datastore_pbs
  from google.appengine.datastore import datastore_query
  from google.appengine.datastore import datastore_rpc
  # This line will fail miserably for any app using auto_import_fixer
  # because auto_import_fixer only set up simple alias between
  # google and google3. But entity_pb is move to a different path completely.
  from google.appengine.datastore import entity_pb
  from google.appengine.ext.blobstore import blobstore as ext_blobstore
  from google.appengine.ext import db
  from google.appengine.ext import gql
  from google.appengine.runtime import apiproxy_errors
  from google.net.proto import ProtocolBuffer
else:
  from google3.apphosting.api.blobstore import blobstore as api_blobstore
  from google3.apphosting.api import apiproxy_rpc
  from google3.apphosting.api import apiproxy_stub_map
  from google3.apphosting.api import datastore
  from google3.apphosting.api import datastore_errors
  from google3.apphosting.api import datastore_types
  from google3.apphosting.api import memcache
  from google3.apphosting.api import namespace_manager
  from google3.apphosting.api import taskqueue
  from google3.apphosting.api import urlfetch
  from google3.apphosting.api import users
  from google3.apphosting.datastore import datastore_pbs
  from google3.apphosting.datastore import datastore_query
  from google3.apphosting.datastore import datastore_rpc
  from google3.storage.onestore.v3 import entity_pb
  from google3.apphosting.ext.blobstore import blobstore as ext_blobstore
  from google3.apphosting.ext import db
  from google3.apphosting.ext import gql
  from google3.apphosting.runtime import apiproxy_errors
  from google3.net.proto import ProtocolBuffer
  # Prospective search is optional.
  try:
    from google3.apphosting.api import prospective_search
    from google3.apphosting.api.prospective_search import prospective_search_pb
  except ImportError:
    pass
