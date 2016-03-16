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
"""Tests for google.apphosting.tools.devappserver2.wsgi_request_info."""



import re
import unittest
import wsgiref.util

from google.appengine.tools.devappserver2 import wsgi_request_info


class TestWSGIRequestInfo(unittest.TestCase):
  """Tests for WSGIRequestInfo."""

  def setUp(self):
    self.dispatcher = object()
    self.request_info = wsgi_request_info.WSGIRequestInfo(self.dispatcher)

  def _assert_request_id(self, request_id):
    self.assertTrue(re.match('[a-zA-Z]{10}$', request_id),
                    'invalid request id: %r' % request_id)

  def _create_environ(self, scheme, host, path='', query=''):
    environ = {'wsgi.url_scheme': scheme,
               'HTTP_HOST': host,
               'PATH_INFO': path,
               'QUERY_STRING': query}
    wsgiref.util.setup_testing_defaults(environ)
    return environ

  def _create_module_configuration(self, module_name, version_id):
    class ModuleConfiguration(object):
      pass

    config = ModuleConfiguration()
    config.major_version = version_id
    config.module_name = module_name
    return config

  def test_get_request_url(self):
    with self.request_info.request(
        self._create_environ('https', 'machine:8080',
                             '/foo', 'bar=baz'),
        self._create_module_configuration('default', '1')) as request_id:
      self._assert_request_id(request_id)
      self.assertEqual('https://machine:8080/foo?bar=baz',
                       self.request_info.get_request_url(request_id))

  def test_get_request_environ(self):
    environ = object()
    with self.request_info.request(
        environ,
        self._create_module_configuration('default', '1')) as request_id:
      self._assert_request_id(request_id)
      self.assertIs(environ, self.request_info.get_request_environ(request_id))

  def test_get_dispatcher(self):
    with self.request_info.request(
        self._create_environ('https', 'machine:8080',
                             '/foo', 'bar=baz'),
        self._create_module_configuration('default', '1')) as request_id:
      self._assert_request_id(request_id)
      self.assertEqual(self.dispatcher,
                       self.request_info.get_dispatcher())

  def test_get_module(self):
    with self.request_info.request(
        self._create_environ('https', 'machine:8080',
                             '/foo', 'bar=baz'),
        self._create_module_configuration('default', '1')) as request_id:
      self._assert_request_id(request_id)
      self.assertEqual('default', self.request_info.get_module(request_id))

  def test_get_version(self):
    with self.request_info.request(
        self._create_environ('https', 'machine:8080',
                             '/foo', 'bar=baz'),
        self._create_module_configuration('default', '1')) as request_id:
      self._assert_request_id(request_id)
      self.assertEqual('1', self.request_info.get_version(request_id))

  def test_get_instance_unset(self):
    with self.request_info.request(
        self._create_environ('https', 'machine:8080',
                             '/foo', 'bar=baz'),
        self._create_module_configuration('default', '1')) as request_id:
      self._assert_request_id(request_id)
      self.assertIsNone(self.request_info.get_instance(request_id))

  def test_get_instance(self):
    with self.request_info.request(
        self._create_environ('https', 'machine:8080',
                             '/foo', 'bar=baz'),
        self._create_module_configuration('default', '1')) as request_id:
      instance = object()
      self.request_info.set_request_instance(request_id, instance)
      self._assert_request_id(request_id)
      self.assertEqual(instance, self.request_info.get_instance(request_id))

  def test_concurrent_requests(self):
    request_id1 = self.request_info.start_request(
        self._create_environ('http', 'machine:8081'),
        self._create_module_configuration('default', '1'))
    request_id2 = self.request_info.start_request(
        self._create_environ('http', 'machine:8082'),
        self._create_module_configuration('default', '2'))
    request_id3 = self.request_info.start_request(
        self._create_environ('http', 'machine:8083'),
        self._create_module_configuration('other', '1'))

    self._assert_request_id(request_id1)
    self._assert_request_id(request_id2)
    self._assert_request_id(request_id3)
    self.assertTrue(request_id1 != request_id2 != request_id3)

    self.assertEqual('http://machine:8081/',
                     self.request_info.get_request_url(request_id1))
    self.assertEqual(self.dispatcher,
                     self.request_info.get_dispatcher())
    self.assertEqual('default', self.request_info.get_module(request_id1))
    self.assertEqual('1', self.request_info.get_version(request_id1))
    self.assertEqual('http://machine:8082/',
                     self.request_info.get_request_url(request_id2))
    self.assertEqual(self.dispatcher,
                     self.request_info.get_dispatcher())
    self.assertEqual('default', self.request_info.get_module(request_id2))
    self.assertEqual('2', self.request_info.get_version(request_id2))
    self.request_info.end_request(request_id1)
    self.request_info.end_request(request_id2)
    self.assertEqual('http://machine:8083/',
                     self.request_info.get_request_url(request_id3))
    self.assertEqual(self.dispatcher,
                     self.request_info.get_dispatcher())
    self.assertEqual('other', self.request_info.get_module(request_id3))
    self.assertEqual('1', self.request_info.get_version(request_id3))

if __name__ == '__main__':
  unittest.main()
