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
"""Unit tests for the api_config_manager module."""







import json
import re
import unittest

from google.appengine.tools.devappserver2.endpoints import api_config_manager


class ApiConfigManagerTest(unittest.TestCase):

  def setUp(self):
    """Make ApiConfigManager with a few helpful fakes."""
    self.config_manager = api_config_manager.ApiConfigManager()

  def test_parse_api_config_empty_response(self):
    self.config_manager.parse_api_config_response('')
    actual_method = self.config_manager.lookup_rpc_method('guestbook_api.get',
                                                          'v1')
    self.assertEqual(None, actual_method)

  def test_parse_api_config_invalid_response(self):
    self.config_manager.parse_api_config_response('{"name": "foo"}')
    actual_method = self.config_manager.lookup_rpc_method('guestbook_api.get',
                                                          'v1')
    self.assertEqual(None, actual_method)

  def test_parse_api_config(self):
    fake_method = {'httpMethod': 'GET',
                   'path': 'greetings/{gid}',
                   'rosyMethod': 'baz.bim'}
    config = json.dumps({'name': 'guestbook_api',
                         'version': 'X',
                         'methods': {'guestbook_api.foo.bar': fake_method}})
    self.config_manager.parse_api_config_response(
        json.dumps({'items': [config]}))
    actual_method = self.config_manager.lookup_rpc_method(
        'guestbook_api.foo.bar', 'X')
    self.assertEqual(fake_method, actual_method)

  def test_parse_api_config_order_length(self):
    test_method_info = (
        ('guestbook_api.foo.bar', 'greetings/{gid}', 'baz.bim'),
        ('guestbook_api.list', 'greetings', 'greetings.list'),
        ('guestbook_api.f3', 'greetings/{gid}/sender/property/blah',
         'greetings.f3'),
        ('guestbook_api.shortgreet', 'greet', 'greetings.short_greeting'))
    methods = {}
    for method_name, path, rosy_method in test_method_info:
      method = {'httpMethod': 'GET',
                'path': path,
                'rosyMethod': rosy_method}
      methods[method_name] = method
    config = json.dumps({'name': 'guestbook_api',
                         'version': 'X',
                         'methods': methods})
    self.config_manager.parse_api_config_response(
        json.dumps({'items': [config]}))
    # Make sure all methods appear in the result.
    for method_name, _, _ in test_method_info:
      self.assertIsNotNone(
          self.config_manager.lookup_rpc_method(method_name, 'X'))
    # Make sure paths and partial paths return the right methods.
    self.assertEqual(
        self.config_manager.lookup_rest_method(
            'guestbook_api/X/greetings', 'GET')[0],
        'guestbook_api.list')
    self.assertEqual(
        self.config_manager.lookup_rest_method(
            'guestbook_api/X/greetings/1', 'GET')[0],
        'guestbook_api.foo.bar')
    self.assertEqual(
        self.config_manager.lookup_rest_method(
            'guestbook_api/X/greetings/2/sender/property/blah', 'GET')[0],
        'guestbook_api.f3')
    self.assertEqual(
        self.config_manager.lookup_rest_method(
            'guestbook_api/X/greet', 'GET')[0],
        'guestbook_api.shortgreet')

  def test_get_sorted_methods1(self):
    test_method_info = (
        ('name1', 'greetings', 'POST'),
        ('name2', 'greetings', 'GET'),
        ('name3', 'short/but/many/constants', 'GET'),
        ('name4', 'greetings', ''),
        ('name5', 'greetings/{gid}', 'GET'),
        ('name6', 'greetings/{gid}', 'PUT'),
        ('name7', 'a/b/{var}/{var2}', 'GET'))
    methods = {}
    for method_name, path, http_method in test_method_info:
      method = {'httpMethod': http_method,
                'path': path}
      methods[method_name] = method
    sorted_methods = self.config_manager._get_sorted_methods(methods)

    expected_data = [
        ('name3', 'short/but/many/constants', 'GET'),
        ('name7', 'a/b/{var}/{var2}', 'GET'),
        ('name4', 'greetings', ''),
        ('name2', 'greetings', 'GET'),
        ('name1', 'greetings', 'POST'),
        ('name5', 'greetings/{gid}', 'GET'),
        ('name6', 'greetings/{gid}', 'PUT')]
    expected_methods = [(name, {'httpMethod': http_method, 'path': path})
                        for name, path, http_method in expected_data]
    self.assertEqual(expected_methods, sorted_methods)

  def test_get_sorted_methods2(self):
    test_method_info = (
        ('name1', 'abcdefghi', 'GET'),
        ('name2', 'foo', 'GET'),
        ('name3', 'greetings', 'GET'),
        ('name4', 'bar', 'POST'),
        ('name5', 'baz', 'GET'),
        ('name6', 'baz', 'PUT'),
        ('name7', 'baz', 'DELETE'))
    methods = {}
    for method_name, path, http_method in test_method_info:
      method = {'httpMethod': http_method,
                'path': path}
      methods[method_name] = method
    sorted_methods = self.config_manager._get_sorted_methods(methods)

    # Single-part paths should be sorted by path name, http_method.
    expected_data = [
        ('name1', 'abcdefghi', 'GET'),
        ('name4', 'bar', 'POST'),
        ('name7', 'baz', 'DELETE'),
        ('name5', 'baz', 'GET'),
        ('name6', 'baz', 'PUT'),
        ('name2', 'foo', 'GET'),
        ('name3', 'greetings', 'GET')]
    expected_methods = [(name, {'httpMethod': http_method, 'path': path})
                        for name, path, http_method in expected_data]
    self.assertEqual(expected_methods, sorted_methods)

  def test_parse_api_config_invalid_api_config(self):
    fake_method = {'httpMethod': 'GET',
                   'path': 'greetings/{gid}',
                   'rosyMethod': 'baz.bim'}
    config = json.dumps({'name': 'guestbook_api',
                         'version': 'X',
                         'methods': {'guestbook_api.foo.bar': fake_method}})
    # Invalid Json
    config2 = '{'
    self.config_manager.parse_api_config_response(
        json.dumps({'items': [config, config2]}))
    actual_method = self.config_manager.lookup_rpc_method(
        'guestbook_api.foo.bar', 'X')
    self.assertEqual(fake_method, actual_method)

  def test_parse_api_config_convert_https(self):
    """Test that the parsed API config has switched HTTPS to HTTP."""
    config = json.dumps({'name': 'guestbook_api',
                         'version': 'X',
                         'adapter': {'bns': 'https://localhost/_ah/spi',
                                     'type': 'lily'},
                         'root': 'https://localhost/_ah/api',
                         'methods': {}})
    self.config_manager.parse_api_config_response(
        json.dumps({'items': [config]}))

    self.assertEqual(
        'http://localhost/_ah/spi',
        self.config_manager.configs[('guestbook_api', 'X')]['adapter']['bns'])
    self.assertEqual(
        'http://localhost/_ah/api',
        self.config_manager.configs[('guestbook_api', 'X')]['root'])

  def test_convert_https_to_http(self):
    """Test that the _convert_https_to_http function works."""
    config = {'name': 'guestbook_api',
              'version': 'X',
              'adapter': {'bns': 'https://tictactoe.appspot.com/_ah/spi',
                          'type': 'lily'},
              'root': 'https://tictactoe.appspot.com/_ah/api',
              'methods': {}}
    self.config_manager._convert_https_to_http(config)

    self.assertEqual('http://tictactoe.appspot.com/_ah/spi',
                     config['adapter']['bns'])
    self.assertEqual('http://tictactoe.appspot.com/_ah/api', config['root'])

  def test_dont_convert_non_https_to_http(self):
    """Verify that we don't change non-HTTPS URLs."""
    config = {'name': 'guestbook_api',
              'version': 'X',
              'adapter': {'bns': 'http://https.appspot.com/_ah/spi',
                          'type': 'lily'},
              'root': 'ios://https.appspot.com/_ah/api',
              'methods': {}}
    self.config_manager._convert_https_to_http(config)

    self.assertEqual('http://https.appspot.com/_ah/spi',
                     config['adapter']['bns'])
    self.assertEqual('ios://https.appspot.com/_ah/api', config['root'])

  def test_save_lookup_rpc_method(self):
    # First attempt, guestbook.get does not exist
    actual_method = self.config_manager.lookup_rpc_method('guestbook_api.get',
                                                          'v1')
    self.assertEqual(None, actual_method)

    # Now we manually save it, and should find it
    fake_method = {'some': 'object'}
    self.config_manager._save_rpc_method('guestbook_api.get', 'v1', fake_method)
    actual_method = self.config_manager.lookup_rpc_method('guestbook_api.get',
                                                          'v1')
    self.assertEqual(fake_method, actual_method)

  def test_save_lookup_rest_method(self):
    # First attempt, guestbook.get does not exist
    method_spec = self.config_manager.lookup_rest_method(
        'guestbook_api/v1/greetings/i', 'GET')
    self.assertEqual((None, None, None), method_spec)

    # Now we manually save it, and should find it
    fake_method = {'httpMethod': 'GET',
                   'path': 'greetings/{id}'}
    self.config_manager._save_rest_method('guestbook_api.get', 'guestbook_api',
                                          'v1', fake_method)
    method_name, method_spec, params = self.config_manager.lookup_rest_method(
        'guestbook_api/v1/greetings/i', 'GET')
    self.assertEqual('guestbook_api.get', method_name)
    self.assertEqual(fake_method, method_spec)
    self.assertEqual({'id': 'i'}, params)

  def test_trailing_slash_optional(self):
    # Create a typical get resource URL.
    fake_method = {'httpMethod': 'GET', 'path': 'trailingslash'}
    self.config_manager._save_rest_method('guestbook_api.trailingslash',
                                          'guestbook_api', 'v1', fake_method)

    # Make sure we get this method when we query without a slash.
    method_name, method_spec, params = self.config_manager.lookup_rest_method(
        'guestbook_api/v1/trailingslash', 'GET')
    self.assertEqual('guestbook_api.trailingslash', method_name)
    self.assertEqual(fake_method, method_spec)
    self.assertEqual({}, params)

    # Make sure we get this method when we query with a slash.
    method_name, method_spec, params = self.config_manager.lookup_rest_method(
        'guestbook_api/v1/trailingslash/', 'GET')
    self.assertEqual('guestbook_api.trailingslash', method_name)
    self.assertEqual(fake_method, method_spec)
    self.assertEqual({}, params)


class ParameterizedPathTest(unittest.TestCase):




  def test_invalid_variable_name_leading_digit(self):
    self.assertEqual(
        None, re.match(api_config_manager._PATH_VARIABLE_PATTERN, '1abc'))

  # Ensure users can not add variables starting with !
  # This is used for reserved variables (e.g. !name and !version)
  def test_invalid_var_name_leading_exclamation(self):
    self.assertEqual(
        None, re.match(api_config_manager._PATH_VARIABLE_PATTERN, '!abc'))

  def test_valid_variable_name(self):
    self.assertEqual(
        'AbC1', re.match(api_config_manager._PATH_VARIABLE_PATTERN,
                         'AbC1').group(0))

  def assert_no_match(self, path, param_path):
    """Assert that the given path does not match param_path pattern.

    For example, /xyz/123 does not match /abc/{x}.

    Args:
      path: A string, the inbound request path.
      param_path: A string, the parameterized path pattern to match against
        this path.
    """
    config_manager = api_config_manager.ApiConfigManager
    params = config_manager._compile_path_pattern(param_path).match(path)
    self.assertEqual(None, params)

  def test_prefix_no_match(self):
    self.assert_no_match('/xyz/123', '/abc/{x}')

  def test_suffix_no_match(self):
    self.assert_no_match('/abc/123', '/abc/{x}/456')

  def test_suffix_no_match_with_more_variables(self):
    self.assert_no_match('/abc/456/123/789', '/abc/{x}/123/{y}/xyz')

  def test_no_match_collection_with_item(self):
    self.assert_no_match('/api/v1/resources/123', '/{name}/{version}/resources')

  def assert_match(self, path, param_path, param_count):
    """Assert that the given path does match param_path pattern.

    For example, /abc/123 does not match /abc/{x}.

    Args:
      path: A string, the inbound request path.
      param_path: A string, the parameterized path pattern to match against
        this path.
      param_count: An int, the expected number of parameters to match in
        pattern.

    Returns:
      Dict mapping path variable name to path variable value.
    """
    config_manager = api_config_manager.ApiConfigManager
    match = config_manager._compile_path_pattern(param_path).match(path)
    self.assertTrue(match is not None)   # Will be None if path was not matched
    params = config_manager._get_path_params(match)
    self.assertEquals(param_count, len(params))
    return params

  def test_one_variable_match(self):
    params = self.assert_match('/abc/123', '/abc/{x}', 1)
    self.assertEquals('123', params.get('x'))

  def test_two_variable_match(self):
    params = self.assert_match('/abc/456/123/789', '/abc/{x}/123/{y}', 2)
    self.assertEquals('456', params.get('x'))
    self.assertEquals('789', params.get('y'))

  def test_message_variable_match(self):
    params = self.assert_match('/abc/123', '/abc/{x.y}', 1)
    self.assertEquals('123', params.get('x.y'))

  def test_message_and_simple_variable_match(self):
    params = self.assert_match('/abc/123/456', '/abc/{x.y.z}/{t}', 2)
    self.assertEquals('123', params.get('x.y.z'))
    self.assertEquals('456', params.get('t'))

  def assert_invalid_value(self, value):
    """Assert that the path parameter value is not valid.

    For example, /abc/3!:2 is invalid for /abc/{x}.

    Args:
      value: A string containing a variable value to check for validity.
    """
    param_path = '/abc/{x}'
    path = '/abc/%s' % value
    config_manager = api_config_manager.ApiConfigManager
    params = config_manager._compile_path_pattern(param_path).match(path)
    self.assertEqual(None, params)

  def test_invalid_values(self):
    for reserved in [':', '?', '#', '[', ']', '{', '}']:
      self.assert_invalid_value('123%s' % reserved)

if __name__ == '__main__':
  unittest.main()
