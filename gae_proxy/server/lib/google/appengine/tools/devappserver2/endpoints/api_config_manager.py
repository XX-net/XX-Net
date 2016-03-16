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
"""Configuration manager to store API configurations."""







import base64
import json
import logging
import re
import threading

from google.appengine.tools.devappserver2.endpoints import discovery_service


# Internal constants
_PATH_VARIABLE_PATTERN = r'[a-zA-Z_][a-zA-Z_.\d]*'
_PATH_VALUE_PATTERN = r'[^:/?#\[\]{}]*'


class ApiConfigManager(object):
  """Manages loading api configs and method lookup."""

  def __init__(self):
    self._rpc_method_dict = {}
    self._rest_methods = []
    self._configs = {}
    self._config_lock = threading.Lock()

  @property
  def configs(self):
    """Return a dict with the current configuration mappings.

    Returns:
      A dict with the current configuration mappings.
    """
    with self._config_lock:
      return self._configs.copy()

  def _convert_https_to_http(self, config):
    """Switch the URLs in one API configuration to use HTTP instead of HTTPS.

    When doing local development in the dev server, any requests to the API
    need to use HTTP rather than HTTPS.  This converts the API configuration
    to use HTTP.  With this change, client libraries that use the API
    configuration will now be able to communicate with the local server.

    This modifies the given dictionary in place.

    Args:
      config: A dict with the JSON configuration for an API.
    """
    if 'adapter' in config and 'bns' in config['adapter']:
      bns_adapter = config['adapter']['bns']
      if bns_adapter.startswith('https://'):
        config['adapter']['bns'] = bns_adapter.replace('https', 'http', 1)
    if 'root' in config and config['root'].startswith('https://'):
      config['root'] = config['root'].replace('https', 'http', 1)

  def parse_api_config_response(self, body):
    """Parses a json api config and registers methods for dispatch.

    Side effects:
      Parses method name, etc for all methods and updates the indexing
      datastructures with the information.

    Args:
      body: A string, the JSON body of the getApiConfigs response.
    """




    try:
      response_obj = json.loads(body)
    except ValueError, unused_err:
      logging.error('Cannot parse BackendService.getApiConfigs response: %s',
                    body)
    else:
      with self._config_lock:
        self._add_discovery_config()
        for api_config_json in response_obj.get('items', []):
          try:
            config = json.loads(api_config_json)
          except ValueError, unused_err:
            logging.error('Can not parse API config: %s',
                          api_config_json)
          else:
            lookup_key = config.get('name', ''), config.get('version', '')
            self._convert_https_to_http(config)
            self._configs[lookup_key] = config

        for config in self._configs.itervalues():
          name = config.get('name', '')
          version = config.get('version', '')
          sorted_methods = self._get_sorted_methods(config.get('methods', {}))

          for method_name, method in sorted_methods:
            self._save_rpc_method(method_name, version, method)
            self._save_rest_method(method_name, name, version, method)

  def _get_sorted_methods(self, methods):
    """Get a copy of 'methods' sorted the way they would be on the live server.

    Args:
      methods: JSON configuration of an API's methods.

    Returns:
      The same configuration with the methods sorted based on what order
      they'll be checked by the server.
    """
    if not methods:
      return methods

    # Comparison function we'll use to sort the methods:
    def _sorted_methods_comparison(method_info1, method_info2):
      """Sort method info by path and http_method.

      Args:
        method_info1: Method name and info for the first method to compare.
        method_info2: Method name and info for the method to compare to.

      Returns:
        Negative if the first method should come first, positive if the
        first method should come after the second.  Zero if they're
        equivalent.
      """

      def _score_path(path):
        """Calculate the score for this path, used for comparisons.

        Higher scores have priority, and if scores are equal, the path text
        is sorted alphabetically.  Scores are based on the number and location
        of the constant parts of the path.  The server has some special handling
        for variables with regexes, which we don't handle here.

        Args:
          path: The request path that we're calculating a score for.

        Returns:
          The score for the given path.
        """







        score = 0
        parts = path.split('/')
        for part in parts:
          score <<= 1
          if not part or part[0] != '{':
            # Found a constant.
            score += 1
        # Shift by 31 instead of 32 because some (!) versions of Python like
        # to convert the int to a long if we shift by 32, and the sorted()
        # function that uses this blows up if it receives anything but an int.
        score <<= 31 - len(parts)
        return score

      # Higher path scores come first.
      path_score1 = _score_path(method_info1[1].get('path', ''))
      path_score2 = _score_path(method_info2[1].get('path', ''))
      if path_score1 != path_score2:
        return path_score2 - path_score1

      # Compare by path text next, sorted alphabetically.
      path_result = cmp(method_info1[1].get('path', ''),
                        method_info2[1].get('path', ''))
      if path_result != 0:
        return path_result

      # All else being equal, sort by HTTP method.
      method_result = cmp(method_info1[1].get('httpMethod', ''),
                          method_info2[1].get('httpMethod', ''))
      return method_result

    return sorted(methods.items(), _sorted_methods_comparison)

  @staticmethod
  def _get_path_params(match):
    """Gets path parameters from a regular expression match.

    Args:
      match: A regular expression Match object for a path.

    Returns:
      A dictionary containing the variable names converted from base64.
    """
    result = {}
    for var_name, value in match.groupdict().iteritems():
      actual_var_name = ApiConfigManager._from_safe_path_param_name(var_name)
      result[actual_var_name] = value
    return result

  def lookup_rpc_method(self, method_name, version):
    """Lookup the JsonRPC method at call time.

    The method is looked up in self._rpc_method_dict, the dictionary that
    it is saved in for SaveRpcMethod().

    Args:
      method_name: A string containing the name of the method.
      version: A string containing the version of the API.

    Returns:
      Method descriptor as specified in the API configuration.
    """
    with self._config_lock:
      method = self._rpc_method_dict.get((method_name, version))
    return method

  def lookup_rest_method(self, path, http_method):
    """Look up the rest method at call time.

    The method is looked up in self._rest_methods, the list it is saved
    in for SaveRestMethod.

    Args:
      path: A string containing the path from the URL of the request.
      http_method: A string containing HTTP method of the request.

    Returns:
      Tuple of (<method name>, <method>, <params>)
      Where:
        <method name> is the string name of the method that was matched.
        <method> is the descriptor as specified in the API configuration. -and-
        <params> is a dict of path parameters matched in the rest request.
    """
    with self._config_lock:
      for compiled_path_pattern, unused_path, methods in self._rest_methods:
        match = compiled_path_pattern.match(path)
        if match:
          params = self._get_path_params(match)
          method_key = http_method.lower()
          method_name, method = methods.get(method_key, (None, None))
          if method:
            break
      else:
        logging.warn('No endpoint found for path: %s', path)
        method_name = None
        method = None
        params = None
    return method_name, method, params

  def _add_discovery_config(self):
    """Add the Discovery configuration to our list of configs.

    This should only be called with self._config_lock.  The code here assumes
    the lock is held.
    """
    lookup_key = (discovery_service.DiscoveryService.API_CONFIG['name'],
                  discovery_service.DiscoveryService.API_CONFIG['version'])
    self._configs[lookup_key] = discovery_service.DiscoveryService.API_CONFIG

  @staticmethod
  def _to_safe_path_param_name(matched_parameter):
    """Creates a safe string to be used as a regex group name.

    Only alphanumeric characters and underscore are allowed in variable name
    tokens, and numeric are not allowed as the first character.

    We cast the matched_parameter to base32 (since the alphabet is safe),
    strip the padding (= not safe) and prepend with _, since we know a token
    can begin with underscore.

    Args:
      matched_parameter: A string containing the parameter matched from the URL
        template.

    Returns:
      A string that's safe to be used as a regex group name.
    """
    return '_' + base64.b32encode(matched_parameter).rstrip('=')

  @staticmethod
  def _from_safe_path_param_name(safe_parameter):
    """Takes a safe regex group name and converts it back to the original value.

    Only alphanumeric characters and underscore are allowed in variable name
    tokens, and numeric are not allowed as the first character.

    The safe_parameter is a base32 representation of the actual value.

    Args:
      safe_parameter: A string that was generated by _to_safe_path_param_name.

    Returns:
      A string, the parameter matched from the URL template.
    """
    assert safe_parameter.startswith('_')
    safe_parameter_as_base32 = safe_parameter[1:]

    padding_length = - len(safe_parameter_as_base32) % 8
    padding = '=' * padding_length
    return base64.b32decode(safe_parameter_as_base32 + padding)

  @staticmethod
  def _compile_path_pattern(pattern):
    r"""Generates a compiled regex pattern for a path pattern.

    e.g. '/MyApi/v1/notes/{id}'
    returns re.compile(r'/MyApi/v1/notes/(?P<id>[^:/?#\[\]{}]*)')

    Args:
      pattern: A string, the parameterized path pattern to be checked.

    Returns:
      A compiled regex object to match this path pattern.
    """

    def replace_variable(match):
      """Replaces a {variable} with a regex to match it by name.

      Changes the string corresponding to the variable name to the base32
      representation of the string, prepended by an underscore. This is
      necessary because we can have message variable names in URL patterns
      (e.g. via {x.y}) but the character '.' can't be in a regex group name.

      Args:
        match: A regex match object, the matching regex group as sent by
          re.sub().

      Returns:
        A string regex to match the variable by name, if the full pattern was
        matched.
      """
      if match.lastindex > 1:
        var_name = ApiConfigManager._to_safe_path_param_name(match.group(2))
        return '%s(?P<%s>%s)' % (match.group(1), var_name,
                                 _PATH_VALUE_PATTERN)
      return match.group(0)

    pattern = re.sub('(/|^){(%s)}(?=/|$)' % _PATH_VARIABLE_PATTERN,
                     replace_variable, pattern)
    return re.compile(pattern + '/?$')

  def _save_rpc_method(self, method_name, version, method):
    """Store JsonRpc api methods in a map for lookup at call time.

    (rpcMethodName, apiVersion) => method.

    Args:
      method_name: A string containing the name of the API method.
      version: A string containing the version of the API.
      method: A dict containing the method descriptor (as in the api config
        file).
    """
    self._rpc_method_dict[(method_name, version)] = method

  def _save_rest_method(self, method_name, api_name, version, method):
    """Store Rest api methods in a list for lookup at call time.

    The list is self._rest_methods, a list of tuples:
      [(<compiled_path>, <path_pattern>, <method_dict>), ...]
    where:
      <compiled_path> is a compiled regex to match against the incoming URL
      <path_pattern> is a string representing the original path pattern,
        checked on insertion to prevent duplicates.     -and-
      <method_dict> is a dict of httpMethod => (method_name, method)

    This structure is a bit complex, it supports use in two contexts:
      Creation time:
        - SaveRestMethod is called repeatedly, each method will have a path,
          which we want to be compiled for fast lookup at call time
        - We want to prevent duplicate incoming path patterns, so store the
          un-compiled path, not counting on a compiled regex being a stable
          comparison as it is not documented as being stable for this use.
        - Need to store the method that will be mapped at calltime.
        - Different methods may have the same path but different http method.
      Call time:
        - Quickly scan through the list attempting .match(path) on each
          compiled regex to find the path that matches.
        - When a path is matched, look up the API method from the request
          and get the method name and method config for the matching
          API method and method name.

    Args:
      method_name: A string containing the name of the API method.
      api_name: A string containing the name of the API.
      version: A string containing the version of the API.
      method: A dict containing the method descriptor (as in the api config
        file).
    """
    path_pattern = '/'.join((api_name, version, method.get('path', '')))
    http_method = method.get('httpMethod', '').lower()
    for _, path, methods in self._rest_methods:
      if path == path_pattern:
        methods[http_method] = method_name, method
        break
    else:
      self._rest_methods.append(
          (self._compile_path_pattern(path_pattern),
           path_pattern,
           {http_method: (method_name, method)}))
