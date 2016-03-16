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
"""A datastore indexes viewer UI."""

import collections

from google.appengine.api import datastore
from google.appengine.tools.devappserver2.admin import admin_request_handler


class DatastoreIndexesViewer(admin_request_handler.AdminRequestHandler):

  def get(self):
    indexes = collections.defaultdict(list)
    for index, _ in datastore.GetIndexes():
      properties = []
      for property_name, sort_direction in index.Properties():
        properties.append({
            'name': property_name,
            'sort_symbol': ('', '&#x25b2;', '&#x25bc;')[sort_direction],
            'sort_direction': ('', 'Ascending', 'Descending')[sort_direction],
        })
      kind = str(index.Kind())
      indexes[kind].append({
          'id': str(index.Id()),
          'has_ancestor': bool(index.HasAncestor()),
          'properties': properties
      })
    self.response.write(self.render('datastore_indexes_viewer.html',
                                    {'indexes': sorted(indexes.items())}))
