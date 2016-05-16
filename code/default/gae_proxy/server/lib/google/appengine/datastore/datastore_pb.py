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





"""The Python datastore protocol buffer definition (old name)."""








from google.appengine.datastore.action_pb import Action
from google.appengine.datastore.entity_pb import CompositeIndex
from google.appengine.datastore.entity_pb import EntityProto
from google.appengine.datastore.entity_pb import Index
from google.appengine.datastore.entity_pb import Path
from google.appengine.datastore.entity_pb import Property
from google.appengine.datastore.entity_pb import PropertyValue
from google.appengine.datastore.entity_pb import Reference
from google.appengine.datastore.snapshot_pb import Snapshot

from google.appengine.api.api_base_pb import Integer64Proto
from google.appengine.api.api_base_pb import StringProto
from google.appengine.api.api_base_pb import VoidProto
from google.appengine.datastore import datastore_v3_pb
from google.appengine.datastore.datastore_v3_pb import *

