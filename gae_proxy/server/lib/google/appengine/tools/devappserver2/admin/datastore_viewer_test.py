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
"""Tests for devappserver2.admin.datastore_viewer."""



import datetime
import os
import unittest

import google

import mox
import webapp2

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore
from google.appengine.api import datastore_types
from google.appengine.datastore import datastore_pb
from google.appengine.datastore import datastore_stub_util
from google.appengine.tools.devappserver2 import api_server
from google.appengine.tools.devappserver2.admin import admin_request_handler
from google.appengine.tools.devappserver2.admin import datastore_viewer


class PropertyNameToValuesTest(unittest.TestCase):
  """Tests for datastore_viewer._property_name_to_value(s)."""

  def setUp(self):
    self.app_id = 'myapp'

    self.entity1 = datastore.Entity('Kind1', id=123, _app=self.app_id)
    self.entity1['cat'] = 5
    self.entity1['dog'] = 10

    self.entity2 = datastore.Entity('Kind1', id=124, _app=self.app_id)
    self.entity2['dog'] = 15
    self.entity2['mouse'] = 'happy'

  def test_property_name_to_values(self):
    self.assertEqual({'cat': [5],
                      'dog': mox.SameElementsAs([10, 15]),
                      'mouse': ['happy']},
                     datastore_viewer._property_name_to_values([self.entity1,
                                                                self.entity2]))

  def test_property_name_to_value(self):
    self.assertEqual({'cat': 5,
                      'dog': mox.Func(lambda v: v in [10, 15]),
                      'mouse': 'happy'},
                     datastore_viewer._property_name_to_value([self.entity1,
                                                               self.entity2]))


class GetWriteOpsTest(unittest.TestCase):
  """Tests for DatastoreRequestHandler._get_write_ops."""

  def setUp(self):
    self.app_id = 'myapp'
    os.environ['APPLICATION_ID'] = self.app_id
    # Use a consistent replication strategy so the puts done in the test code
    # are seen immediately by the queries under test.
    consistent_policy = datastore_stub_util.MasterSlaveConsistencyPolicy()
    api_server.test_setup_stubs(
        app_id=self.app_id,
        application_root=None,  # Needed to allow index updates.
        datastore_consistency=consistent_policy)

  def test_no_properties(self):
    entity = datastore.Entity('Yar', id=123, _app=self.app_id)  # 2 writes.
    self.assertEquals(
        2, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

  def test_indexed_properties_no_composite_indexes(self):
    entity = datastore.Entity('Yar', id=123, _app=self.app_id)  # 2 writes.
    entity['p1'] = None  # 2 writes.
    entity['p2'] = None  # 2 writes.
    entity['p3'] = [1, 2, 3]  # 6 writes.
    self.assertEquals(
        12, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

  def test_unindexed_properties_no_composite_indexes(self):
    entity = datastore.Entity('Yar', id=123, _app=self.app_id)  # 2 writes.
    entity['u1'] = None  # 0 writes.
    entity['u2'] = None  # 0 writes.
    entity['u3'] = [1, 2, 3]  # 0 writes.
    entity.set_unindexed_properties(('u1', 'u2', 'u3'))

    # unindexed properties have no impact on cost
    self.assertEquals(
        2, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

  def test_composite_index(self):
    ci = datastore_pb.CompositeIndex()
    ci.set_app_id(datastore_types.ResolveAppId(None))
    ci.set_id(0)
    ci.set_state(ci.WRITE_ONLY)
    index = ci.mutable_definition()
    index.set_ancestor(0)
    index.set_entity_type('Yar')
    prop = index.add_property()
    prop.set_name('this')
    prop.set_direction(prop.ASCENDING)
    prop = index.add_property()
    prop.set_name('that')
    prop.set_direction(prop.DESCENDING)
    stub = apiproxy_stub_map.apiproxy.GetStub('datastore_v3')
    stub.CreateIndex(ci)
    self.assertEquals(1, len(datastore.GetIndexes()))

    # no properties, no composite indices.
    entity = datastore.Entity('Yar', id=123, _app=self.app_id)  # 2 writes.
    # We only have the 2 built-in index writes because the entity doesn't have
    # property values for any of the index properties.
    self.assertEquals(
        2, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    entity['this'] = 4
    # Unindexed property so no additional writes
    entity.set_unindexed_properties(('this',))
    self.assertEquals(
        2, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    entity['that'] = 4
    # Unindexed property so no additional writes
    entity.set_unindexed_properties(('this', 'that'))
    self.assertEquals(
        2, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    # no indexed property value on 'that'
    entity.set_unindexed_properties(('that',))
    # 2 writes for the entity.
    # 2 writes for the single indexed property.
    self.assertEquals(
        4, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    # indexed property value on both 'this' and 'that'
    entity.set_unindexed_properties(())
    # 2 writes for the entity
    # 4 writes for the indexed properties
    # 1 writes for the composite index
    self.assertEquals(
        7, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    # now run tests with null property values
    entity = datastore.Entity('Yar', id=123, _app=self.app_id)  # 2 writes.
    entity['this'] = None
    # 2 for the entity
    # 2 for the single indexed property
    self.assertEquals(
        4, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    entity['that'] = None
    # 2 for the entity
    # 4 for the indexed properties
    # 1 for the composite index
    self.assertEquals(
        7, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    # now run tests with a repeated property
    entity = datastore.Entity('Yar', id=123, _app=self.app_id)  # 2 writes.
    entity['this'] = [1, 2, 3]
    # 2 for the entity
    # 6 for the indexed properties
    self.assertEquals(
        8, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    entity['that'] = None
    # 2 for the entity
    # 8 for the indexed properties
    # 3 for the Composite index
    self.assertEquals(
        13, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    entity['that'] = [4, 5]
    # 2 for the entity
    # 10 for the indexed properties
    # 6 for the Composite index
    self.assertEquals(
        18, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

  def test_composite_index_no_properties(self):
    ci = datastore_pb.CompositeIndex()
    ci.set_app_id(datastore_types.ResolveAppId(None))
    ci.set_id(0)
    ci.set_state(ci.WRITE_ONLY)
    index = ci.mutable_definition()
    index.set_ancestor(0)
    index.set_entity_type('Yar')
    stub = apiproxy_stub_map.apiproxy.GetStub('datastore_v3')
    stub.CreateIndex(ci)
    self.assertEquals(1, len(datastore.GetIndexes()))

    # no properties, and composite index with no properties.
    entity = datastore.Entity('Yar', id=123, _app=self.app_id)  # 2 writes.
    # We have the 2 built-in index writes, and one for the entity key in the
    # composite index despite the fact that there are no proerties defined in
    # the index.
    self.assertEquals(
        3, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    # now with a repeated property
    entity = datastore.Entity('Yar', id=123, _app=self.app_id)  # 2 writes.
    entity['this'] = [1, 2, 3]
    # 2 for the entity
    # 6 for the indexed properties
    # 1 for the composite index
    self.assertEquals(
        9, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

  def test_composite_ancestor_index(self):
    ci = datastore_pb.CompositeIndex()
    ci.set_app_id(datastore_types.ResolveAppId(None))
    ci.set_id(0)
    ci.set_state(ci.WRITE_ONLY)
    index = ci.mutable_definition()
    index.set_ancestor(1)
    index.set_entity_type('Yar')
    prop = index.add_property()
    prop.set_name('this')
    prop.set_direction(prop.ASCENDING)
    prop = index.add_property()
    prop.set_name('that')
    prop.set_direction(prop.DESCENDING)
    stub = apiproxy_stub_map.apiproxy.GetStub('datastore_v3')
    stub.CreateIndex(ci)
    self.assertEquals(1, len(datastore.GetIndexes()))

    entity = datastore.Entity('Yar', id=123, _app=self.app_id)  # 2 writes.
    entity['this'] = 4
    entity['that'] = 4
    # 2 for the entity
    # 4 for the indexed properties
    # 1 for the composite index
    self.assertEquals(
        7, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    # Now use the same entity but give it an ancestor
    parent_entity = datastore.Entity('parent', id=123, _app=self.app_id)
    entity = datastore.Entity(
        'Yar',
        parent=parent_entity.key(),
        id=123,
        _app=self.app_id)  # 2 writes.
    entity['this'] = 4
    entity['that'] = 4
    # 2 writes for the entity.
    # 4 writes for the indexed properties.
    # 2 writes for the composite indices.
    self.assertEquals(
        8, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    # Now use the same entity but give it 2 ancestors.
    grandparent_entity = datastore.Entity(
        'grandparent', id=123, _app=self.app_id)
    parent_entity = datastore.Entity(
        'parent', parent=grandparent_entity.key(), id=123, _app=self.app_id)
    entity = datastore.Entity(
        'Yar',
        parent=parent_entity.key(),
        id=123,
        _app=self.app_id)  # 2 writes.
    entity['this'] = 4
    entity['that'] = 4
    # 2 writes for the entity.
    # 4 writes for the indexed properties.
    # 3 writes for the composite indices.
    self.assertEquals(
        9, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    # Now try it with a multi-value prop
    entity['this'] = [None, None, None]
    # 2 writes for the entity.
    # 8 writes for the indexed properties.
    # 9 writes for the composite indices.
    self.assertEquals(
        19, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    # Now try it with 2 multi-value props.
    entity['that'] = [None, None]
    # 2 writes for the entity.
    # 10 writes for the indexed properties.
    # 18 writes for the composite indices.
    self.assertEquals(
        30, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

  def test_composite_ancestor_index_no_properties(self):
    ci = datastore_pb.CompositeIndex()
    ci.set_app_id(datastore_types.ResolveAppId(None))
    ci.set_id(0)
    ci.set_state(ci.WRITE_ONLY)
    index = ci.mutable_definition()
    index.set_ancestor(1)
    index.set_entity_type('Yar')
    stub = apiproxy_stub_map.apiproxy.GetStub('datastore_v3')
    stub.CreateIndex(ci)
    self.assertEquals(1, len(datastore.GetIndexes()))

    entity = datastore.Entity('Yar', id=123, _app=self.app_id)  # 2 writes.
    entity['this'] = [None, None]
    # 2 writes for the entity.
    # 4 writes for the indexed properties.
    # 1 writes for the composite index.
    self.assertEquals(
        7, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))

    # Now use the same entity but give it an ancestor
    parent_entity = datastore.Entity('parent', id=123, _app=self.app_id)
    entity = datastore.Entity(
        'Yar',
        parent=parent_entity.key(),
        id=123,
        _app=self.app_id)  # 2 writes.
    entity['this'] = [None, None]
    # 2 writes for the entity.
    # 4 writes for the indexed properties.
    # 2 writes for the composite indices.
    self.assertEquals(
        8, datastore_viewer.DatastoreRequestHandler._get_write_ops(entity))


class GetEntitiesTest(unittest.TestCase):
  """Tests for DatastoreRequestHandler._get_entities."""

  def setUp(self):
    self.app_id = 'myapp'
    os.environ['APPLICATION_ID'] = self.app_id
    # Use a consistent replication strategy so the puts done in the test code
    # are seen immediately by the queries under test.
    consistent_policy = datastore_stub_util.MasterSlaveConsistencyPolicy()
    api_server.test_setup_stubs(
        app_id=self.app_id,
        datastore_consistency=consistent_policy)

    self.entity1 = datastore.Entity('Kind1', id=123, _app=self.app_id)
    self.entity1['intprop'] = 1
    self.entity1['listprop'] = [7, 8, 9]
    datastore.Put(self.entity1)

    self.entity2 = datastore.Entity('Kind1', id=124, _app=self.app_id)
    self.entity2['stringprop'] = 'value2'
    self.entity2['listprop'] = [4, 5, 6]
    datastore.Put(self.entity2)

    self.entity3 = datastore.Entity('Kind1', id=125, _app=self.app_id)
    self.entity3['intprop'] = 3
    self.entity3['stringprop'] = 'value3'
    self.entity3['listprop'] = [1, 2, 3]
    datastore.Put(self.entity3)

    self.entity4 = datastore.Entity('Kind1', id=126, _app=self.app_id)
    self.entity4['intprop'] = 4
    self.entity4['stringprop'] = 'value4'
    self.entity4['listprop'] = [10, 11, 12]
    datastore.Put(self.entity4)

  def test_ascending_int_order(self):
    entities, total = datastore_viewer._get_entities(kind='Kind1',
                                                     namespace='',
                                                     order='intprop',
                                                     start=0,
                                                     count=100)
    self.assertEqual([self.entity1, self.entity3, self.entity4], entities)
    self.assertEqual(3, total)

  def test_decending_string_order(self):
    entities, total = datastore_viewer._get_entities(kind='Kind1',
                                                     namespace='',
                                                     order='-stringprop',
                                                     start=0,
                                                     count=100)
    self.assertEqual([self.entity4, self.entity3, self.entity2], entities)
    self.assertEqual(3, total)

  def test_start_and_count(self):
    entities, total = datastore_viewer._get_entities(kind='Kind1',
                                                     namespace='',
                                                     order='listprop',
                                                     start=1,
                                                     count=2)
    self.assertEqual([self.entity2, self.entity1], entities)
    self.assertEqual(4, total)


class GetEntityTemplateDataTest(unittest.TestCase):
  def setUp(self):
    self.app_id = 'myapp'
    os.environ['APPLICATION_ID'] = self.app_id
    # Use a consistent replication strategy so the puts done in the test code
    # are seen immediately by the queries under test.
    consistent_policy = datastore_stub_util.MasterSlaveConsistencyPolicy()
    api_server.test_setup_stubs(
        app_id=self.app_id,
        datastore_consistency=consistent_policy)

    self.entity1 = datastore.Entity('Kind1', id=123, _app=self.app_id)
    self.entity1['intprop'] = 1
    self.entity1['listprop'] = [7, 8, 9]
    datastore.Put(self.entity1)

    self.entity2 = datastore.Entity('Kind1', id=124, _app=self.app_id)
    self.entity2['stringprop'] = 'value2'
    self.entity2['listprop'] = [4, 5, 6]
    datastore.Put(self.entity2)

    self.entity3 = datastore.Entity('Kind1', id=125, _app=self.app_id)
    self.entity3['intprop'] = 3
    self.entity3['listprop'] = [1, 2, 3]
    datastore.Put(self.entity3)

    self.entity4 = datastore.Entity('Kind1', id=126, _app=self.app_id)
    self.entity4['intprop'] = 4
    self.entity4['stringprop'] = 'value4'
    self.entity4['listprop'] = [10, 11]
    datastore.Put(self.entity4)

  def test(self):
    headers, entities, total_entities = (
        datastore_viewer.DatastoreRequestHandler._get_entity_template_data(
            request_uri='http://next/',
            kind='Kind1',
            namespace='',
            order='intprop',
            start=1))

    self.assertEqual(
        [{'name': 'intprop'}, {'name': 'listprop'}, {'name': 'stringprop'}],
        headers)

    self.assertEqual(
        [{'attributes': [{'name': u'intprop',
                          'short_value': '3',
                          'value': '3'},
                         {'name': u'listprop',
                          'short_value': mox.Regex(r'\[1L?, 2L?, 3L?\]'),
                          'value': mox.Regex(r'\[1L?, 2L?, 3L?\]')},
                         {'name': u'stringprop',
                          'short_value': '',
                          'value': ''}],
          'edit_uri': '/datastore/edit/{0}?next=http%3A//next/'.format(
              self.entity3.key()),
          'key': datastore_types.Key.from_path(u'Kind1', 125, _app=u'myapp'),
          'key_id': 125,
          'key_name': None,
          'shortened_key': 'agVteWFw...',
          'write_ops': 10},
         {'attributes': [{'name': u'intprop',
                          'short_value': '4',
                          'value': '4'},
                         {'name': u'listprop',
                          'short_value': mox.Regex(r'\[10L?, 11L?\]'),
                          'value': mox.Regex(r'\[10L?, 11L?\]')},
                         {'name': u'stringprop',
                          'short_value': u'value4',
                          'value': u'value4'}],
          'edit_uri': '/datastore/edit/{0}?next=http%3A//next/'.format(
              self.entity4.key()),
          'key': datastore_types.Key.from_path(u'Kind1', 126, _app=u'myapp'),
          'key_id': 126,
          'key_name': None,
          'shortened_key': 'agVteWFw...',
          'write_ops': 10}],
        entities)

    self.assertEqual(3, total_entities)


class DatastoreRequestHandlerGetTest(unittest.TestCase):
  """Tests for DatastoreRequestHandler.get."""

  def setUp(self):
    self.app_id = 'myapp'
    os.environ['APPLICATION_ID'] = self.app_id
    api_server.test_setup_stubs(app_id=self.app_id)

    self.mox = mox.Mox()
    self.mox.StubOutWithMock(admin_request_handler.AdminRequestHandler,
                             'render')

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_empty_request_and_empty_datastore(self):
    request = webapp2.Request.blank('/datastore')
    response = webapp2.Response()
    handler = datastore_viewer.DatastoreRequestHandler(request, response)

    handler.render('datastore_viewer.html',
                   {'entities': [],
                    'headers': [],
                    'kind': None,
                    'kinds': [],
                    'message': None,
                    'namespace': '',
                    'num_pages': 0,
                    'order': None,
                    'paging_base_url': '/datastore?',
                    'order_base_url': '/datastore?',
                    'page': 1,
                    'select_namespace_url': '/datastore?namespace=',
                    'show_namespace': False,
                    'start': 0,
                    'total_entities': 0})
    self.mox.ReplayAll()
    handler.get()
    self.mox.VerifyAll()

  def test_empty_request_and_populated_datastore(self):
    entity = datastore.Entity('Kind1', id=123, _app=self.app_id)
    entity['intprop'] = 1
    entity['listprop'] = [7, 8, 9]
    datastore.Put(entity)

    request = webapp2.Request.blank('/datastore')
    response = webapp2.Response()
    handler = datastore_viewer.DatastoreRequestHandler(request, response)

    self.mox.ReplayAll()
    handler.get()
    self.mox.VerifyAll()

    self.assertEqual(302, response.status_int)
    self.assertEqual('http://localhost/datastore?kind=Kind1',
                     response.location)

  def test_kind_request_and_populated_datastore(self):
    entity = datastore.Entity('Kind1', id=123, _app=self.app_id)
    entity['intprop'] = 1
    entity['listprop'] = [7, 8, 9]
    datastore.Put(entity)

    request = webapp2.Request.blank('/datastore?kind=Kind1')
    response = webapp2.Response()
    handler = datastore_viewer.DatastoreRequestHandler(request, response)

    handler.render(
        'datastore_viewer.html',
        {'entities': mox.IgnoreArg(),  # Tested with _get_entity_template_data.
         'headers': mox.IgnoreArg(),  # Tested with _get_entity_template_data.
         'kind': 'Kind1',
         'kinds': ['Kind1'],
         'message': None,
         'namespace': '',
         'num_pages': 1,
         'order': None,
         'order_base_url': '/datastore?kind=Kind1',
         'page': 1,
         'paging_base_url': '/datastore?kind=Kind1',
         'select_namespace_url': '/datastore?kind=Kind1&namespace=',
         'show_namespace': False,
         'start': 0,
         'total_entities': 1})

    self.mox.ReplayAll()
    handler.get()
    self.mox.VerifyAll()

  def test_order_request(self):
    entity = datastore.Entity('Kind1', id=123, _app=self.app_id)
    entity['intprop'] = 1
    entity['listprop'] = [7, 8, 9]
    datastore.Put(entity)

    request = webapp2.Request.blank(
        '/datastore?kind=Kind1&order=intprop')
    response = webapp2.Response()
    handler = datastore_viewer.DatastoreRequestHandler(request, response)

    handler.render(
        'datastore_viewer.html',
        {'entities': mox.IgnoreArg(),  # Tested with _get_entity_template_data.
         'headers': mox.IgnoreArg(),  # Tested with _get_entity_template_data.
         'kind': 'Kind1',
         'kinds': ['Kind1'],
         'message': None,
         'namespace': '',
         'num_pages': 1,
         'order': 'intprop',
         'order_base_url': '/datastore?kind=Kind1',
         'page': 1,
         'paging_base_url': '/datastore?kind=Kind1&order=intprop',
         'select_namespace_url':
         '/datastore?kind=Kind1&namespace=&order=intprop',
         'show_namespace': False,
         'start': 0,
         'total_entities': 1})

    self.mox.ReplayAll()
    handler.get()
    self.mox.VerifyAll()

  def test_namespace_request(self):
    entity = datastore.Entity('Kind1',
                              id=123,
                              _app=self.app_id,
                              _namespace='google')
    entity['intprop'] = 1
    entity['listprop'] = [7, 8, 9]
    datastore.Put(entity)

    request = webapp2.Request.blank(
        '/datastore?kind=Kind1&namespace=google')
    response = webapp2.Response()
    handler = datastore_viewer.DatastoreRequestHandler(request, response)

    handler.render(
        'datastore_viewer.html',
        {'entities': mox.IgnoreArg(),  # Tested with _get_entity_template_data.
         'headers': mox.IgnoreArg(),  # Tested with _get_entity_template_data.
         'kind': 'Kind1',
         'kinds': ['Kind1'],
         'message': None,
         'namespace': 'google',
         'num_pages': 1,
         'order': None,
         'order_base_url': '/datastore?kind=Kind1&namespace=google',
         'page': 1,
         'paging_base_url': '/datastore?kind=Kind1&namespace=google',
         'select_namespace_url':
         '/datastore?kind=Kind1&namespace=google',
         'show_namespace': True,
         'start': 0,
         'total_entities': 1})

    self.mox.ReplayAll()
    handler.get()
    self.mox.VerifyAll()

  def test_page_request(self):
    for i in range(1000):
      entity = datastore.Entity('Kind1', id=i+1, _app=self.app_id)
      entity['intprop'] = i
      datastore.Put(entity)

    request = webapp2.Request.blank(
        '/datastore?kind=Kind1&page=3')
    response = webapp2.Response()
    handler = datastore_viewer.DatastoreRequestHandler(request, response)

    handler.render(
        'datastore_viewer.html',
        {'entities': mox.IgnoreArg(),  # Tested with _get_entity_template_data.
         'headers': mox.IgnoreArg(),  # Tested with _get_entity_template_data.
         'kind': 'Kind1',
         'kinds': ['Kind1'],
         'message': None,
         'namespace': '',
         'num_pages': 50,
         'order': None,
         'order_base_url': '/datastore?kind=Kind1&page=3',
         'page': 3,
         'paging_base_url': '/datastore?kind=Kind1',
         'select_namespace_url':
         '/datastore?kind=Kind1&namespace=&page=3',
         'show_namespace': False,
         'start': 40,
         'total_entities': 1000})

    self.mox.ReplayAll()
    handler.get()
    self.mox.VerifyAll()


class DatastoreEditRequestHandlerTest(unittest.TestCase):
  """Tests for DatastoreEditRequestHandler."""

  def setUp(self):
    self.app_id = 'myapp'
    os.environ['APPLICATION_ID'] = self.app_id

    # Use a consistent replication strategy so that the test can use queries
    # to verify that an entity was written.
    consistent_policy = datastore_stub_util.MasterSlaveConsistencyPolicy()
    api_server.test_setup_stubs(
        app_id=self.app_id,
        datastore_consistency=consistent_policy)

    self.mox = mox.Mox()
    self.mox.StubOutWithMock(admin_request_handler.AdminRequestHandler,
                             'render')

    self.entity1 = datastore.Entity('Kind1', id=123, _app=self.app_id)
    self.entity1['intprop'] = 1
    self.entity1['listprop'] = [7, 8, 9]
    self.entity1['dateprop'] = datastore_types._OverflowDateTime(2**60)
    datastore.Put(self.entity1)

    self.entity2 = datastore.Entity('Kind1', id=124, _app=self.app_id)
    self.entity2['stringprop'] = 'value2'
    self.entity2['listprop'] = [4, 5, 6]
    datastore.Put(self.entity2)

    self.entity3 = datastore.Entity('Kind1', id=125, _app=self.app_id)
    self.entity3['intprop'] = 3
    self.entity3['listprop'] = [1, 2, 3]
    datastore.Put(self.entity3)

    self.entity4 = datastore.Entity('Kind1', id=126, _app=self.app_id)
    self.entity4['intprop'] = 4
    self.entity4['stringprop'] = 'value4'
    self.entity4['listprop'] = [10, 11]
    datastore.Put(self.entity4)

    self.entity5 = datastore.Entity('Kind1', id=127, _app=self.app_id)
    self.entity5['intprop'] = 0
    self.entity5['boolprop'] = False
    self.entity5['stringprop'] = ''
    self.entity5['floatprop'] = 0.0
    datastore.Put(self.entity5)

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_get_no_entity_key_string(self):
    request = webapp2.Request.blank(
        '/datastore/edit?kind=Kind1&next=http://next/')
    response = webapp2.Response()
    handler = datastore_viewer.DatastoreEditRequestHandler(request, response)

    handler.render(
        'datastore_edit.html',
        {'fields': [('boolprop',
                     'bool',
                     mox.Regex('^<select class="bool"(.|\n)*$')),
                    ('dateprop',
                     'overflowdatetime',
                     mox.Regex('^<input class="overflowdatetime".*'
                               'value="".*$')),
                    ('floatprop',
                     'float',
                     mox.Regex('^<input class="float".*value="".*$')),
                    ('intprop',
                     'int',
                     mox.Regex('^<input class="int".*value="".*$')),
                    ('listprop', 'list', ''),
                    ('stringprop',
                     'string',
                     mox.Regex('^<input class="string".*$'))],
         'key': None,
         'key_id': None,
         'key_name': None,
         'kind': 'Kind1',
         'namespace': '',
         'next': 'http://next/',
         'parent_key': None,
         'parent_key_string': None})

    self.mox.ReplayAll()
    handler.get()
    self.mox.VerifyAll()

  def test_get_no_entity_key_string_and_no_entities_in_namespace(self):
    request = webapp2.Request.blank(
        '/datastore/edit?kind=Kind1&namespace=cat&next=http://next/')
    response = webapp2.Response()
    handler = datastore_viewer.DatastoreEditRequestHandler(request, response)

    self.mox.ReplayAll()
    handler.get()
    self.mox.VerifyAll()

    self.assertEqual(302, response.status_int)
    self.assertRegexpMatches(
        response.location,
        r'/datastore\?kind=Kind1&message=Cannot+.*&namespace=cat')

  def test_get_entity_string(self):
    request = webapp2.Request.blank(
        '/datastore/edit/%s?next=http://next/' % self.entity1.key())
    response = webapp2.Response()
    handler = datastore_viewer.DatastoreEditRequestHandler(request, response)

    handler.render(
        'datastore_edit.html',
        {'fields': [('dateprop',
                     'overflowdatetime',
                     mox.Regex('^<input class="overflowdatetime".*'
                               'value="1152921504606846976".*$')),
                    ('intprop',
                     'int',
                     mox.Regex('^<input class="int".*value="1".*$')),
                    ('listprop', 'list', mox.Regex(r'\[7L?, 8L?, 9L?\]'))],
         'key': str(self.entity1.key()),
         'key_id': 123,
         'key_name': None,
         'kind': 'Kind1',
         'namespace': '',
         'next': 'http://next/',
         'parent_key': None,
         'parent_key_string': None})

    self.mox.ReplayAll()
    handler.get(str(self.entity1.key()))
    self.mox.VerifyAll()

  def test_get_entity_zero_props(self):
    request = webapp2.Request.blank(
        '/datastore/edit/%s?next=http://next/' % self.entity5.key())
    response = webapp2.Response()
    handler = datastore_viewer.DatastoreEditRequestHandler(request, response)

    handler.render(
        'datastore_edit.html',
        {'fields': [('boolprop',
                     'bool',
                     mox.Regex('^<select class="bool"(.|\n)*$')),
                    ('floatprop',
                     'float',
                     mox.Regex('^<input class="float".*value="0\.0".*$')),
                    ('intprop',
                     'int',
                     mox.Regex('^<input class="int".*value="0".*$')),
                    ('stringprop',
                     'string',
                     mox.Regex('^<input class="string".*value="".*$'))],
         'key': str(self.entity5.key()),
         'key_id': 127,
         'key_name': None,
         'kind': 'Kind1',
         'namespace': '',
         'next': 'http://next/',
         'parent_key': None,
         'parent_key_string': None})

    self.mox.ReplayAll()
    handler.get(str(self.entity5.key()))
    self.mox.VerifyAll()

  def test_post_no_entity_key_string(self):
    request = webapp2.Request.blank(
        '/datastore/edit',
        POST={'kind': 'Kind1',
              'overflowdatetime|dateprop': '2009-12-24 23:59:59',
              'int|intprop': '123',
              'string|stringprop': 'Hello',
              'next': 'http://redirect/'})
    response = webapp2.Response()
    handler = datastore_viewer.DatastoreEditRequestHandler(request, response)

    self.mox.ReplayAll()
    handler.post()
    self.mox.VerifyAll()

    self.assertEqual(302, response.status_int)
    self.assertEqual('http://redirect/', response.location)

    # Check that the entity was added.
    query = datastore.Query('Kind1')
    query.update({'dateprop': datetime.datetime(2009, 12, 24, 23, 59, 59),
                  'intprop': 123,
                  'stringprop': 'Hello'})
    self.assertEquals(1, query.Count())

  def test_post_entity_key_string(self):
    request = webapp2.Request.blank(
        '/datastore/edit/%s' % self.entity4.key(),
        POST={'overflowdatetime|dateprop': str(2**60),
              'int|intprop': '123',
              'string|stringprop': '',
              'next': 'http://redirect/'})
    response = webapp2.Response()
    handler = datastore_viewer.DatastoreEditRequestHandler(request, response)

    self.mox.ReplayAll()
    handler.post(str(self.entity4.key()))
    self.mox.VerifyAll()

    self.assertEqual(302, response.status_int)
    self.assertEqual('http://redirect/', response.location)

    # Check that the entity was updated.
    entity = datastore.Get(self.entity4.key())
    self.assertEqual(2**60, entity['dateprop'])
    self.assertEqual(123, entity['intprop'])
    self.assertEqual([10, 11], entity['listprop'])
    self.assertNotIn('stringprop', entity)


if __name__ == '__main__':
  unittest.main()
