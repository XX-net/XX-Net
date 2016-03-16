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
"""Serves static content for "static_dir" and "static_files" handlers."""



import base64
import errno
import httplib
import mimetypes
import os
import os.path
import re
import zlib

from google.appengine.api import appinfo
from google.appengine.tools import augment_mimetypes
from google.appengine.tools.devappserver2 import errors
from google.appengine.tools.devappserver2 import url_handler

_FILE_MISSING_ERRNO_CONSTANTS = frozenset([errno.ENOENT, errno.ENOTDIR])

# Run at import time so we only do this once.
augment_mimetypes.init()


class StaticContentHandler(url_handler.UserConfiguredURLHandler):
  """Abstract base class for subclasses serving static content."""

  # Associate the full path of a static file with a 2-tuple containing the:
  # - mtime at which the file was last read from disk
  # - a etag constructed from a hash of the file's contents
  # Statting a small file to retrieve its mtime is approximately 20x faster than
  # reading it to generate a hash of its contents.
  _filename_to_mtime_and_etag = {}

  def __init__(self, root_path, url_map, url_pattern):
    """Initializer for StaticContentHandler.

    Args:
      root_path: A string containing the full path of the directory containing
          the application's app.yaml file.
      url_map: An appinfo.URLMap instance containing the configuration for this
          handler.
      url_pattern: A re.RegexObject that matches URLs that should be handled by
          this handler. It may also optionally bind groups.
    """
    super(StaticContentHandler, self).__init__(url_map, url_pattern)
    self._root_path = root_path

  def _get_mime_type(self, path):
    """Returns the mime type for the file at the given path."""
    if self._url_map.mime_type is not None:
      return self._url_map.mime_type

    _, extension = os.path.splitext(path)
    return mimetypes.types_map.get(extension, 'application/octet-stream')

  def _handle_io_exception(self, start_response, e):
    """Serves the response to an OSError or IOError.

    Args:
      start_response: A function with semantics defined in PEP-333. This
          function will be called with a status appropriate to the given
          exception.
      e: An instance of OSError or IOError used to generate an HTTP status.

    Returns:
      An emply iterable.
    """
    if e.errno in _FILE_MISSING_ERRNO_CONSTANTS:
      start_response('404 Not Found', [])
    else:
      start_response('403 Forbidden', [])
    return []

  @staticmethod
  def _calculate_etag(data):
    return base64.b64encode(str(zlib.crc32(data)))

  def _handle_path(self, full_path, environ, start_response):
    """Serves the response to a request for a particular file.

    Note that production App Engine treats all methods as "GET" except "HEAD".

    Unless set explicitly, the "Expires" and "Cache-Control" headers are
    deliberately different from their production values to make testing easier.
    If set explicitly then the values are preserved because the user may
    reasonably want to test for them.

    Args:
      full_path: A string containing the absolute path to the file to serve.
      environ: An environ dict for the current request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    data = None
    if full_path in self._filename_to_mtime_and_etag:
      last_mtime, etag = self._filename_to_mtime_and_etag[full_path]
    else:
      last_mtime = etag = None

    user_headers = self._url_map.http_headers or appinfo.HttpHeadersDict()

    if_match = environ.get('HTTP_IF_MATCH')
    if_none_match = environ.get('HTTP_IF_NONE_MATCH')

    try:
      mtime = os.path.getmtime(full_path)
    except (OSError, IOError) as e:
      # RFC-2616 section 14.24 says:
      # If none of the entity tags match, or if "*" is given and no current
      # entity exists, the server MUST NOT perform the requested method, and
      # MUST return a 412 (Precondition Failed) response.
      if if_match:
        start_response('412 Precondition Failed', [])
        return []
      elif self._url_map.require_matching_file:
        return None
      else:
        return self._handle_io_exception(start_response, e)

    if mtime != last_mtime:
      try:
        data = self._read_file(full_path)
      except (OSError, IOError) as e:
        return self._handle_io_exception(start_response, e)
      etag = self._calculate_etag(data)
      self._filename_to_mtime_and_etag[full_path] = mtime, etag

    if if_match and not self._check_etag_match(if_match,
                                               etag,
                                               allow_weak_match=False):
      # http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.24
      start_response('412 Precondition Failed',
                     [('ETag', '"%s"' % etag)])
      return []
    elif if_none_match and self._check_etag_match(if_none_match,
                                                  etag,
                                                  allow_weak_match=True):
      # http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.26
      start_response('304 Not Modified',
                     [('ETag', '"%s"' % etag)])
      return []
    else:
      if data is None:
        try:
          data = self._read_file(full_path)
        except (OSError, IOError) as e:
          return self._handle_io_exception(start_response, e)

        etag = self._calculate_etag(data)
        self._filename_to_mtime_and_etag[full_path] = mtime, etag

      headers = [('Content-length', str(len(data)))]

      if user_headers.Get('Content-type') is None:
        headers.append(('Content-type', self._get_mime_type(full_path)))

      if user_headers.Get('ETag') is None:
        headers.append(('ETag', '"%s"' % etag))

      if user_headers.Get('Expires') is None:
        headers.append(('Expires', 'Fri, 01 Jan 1990 00:00:00 GMT'))

      if user_headers.Get('Cache-Control') is None:
        headers.append(('Cache-Control', 'no-cache'))

      for name, value in user_headers.iteritems():
        # "name" will always be unicode due to the way that ValidatedDict works.
        headers.append((str(name), value))

      start_response('200 OK', headers)
      if environ['REQUEST_METHOD'] == 'HEAD':
        return []
      else:
        return [data]

  @staticmethod
  def _read_file(full_path):
    with open(full_path, 'rb') as f:
      return f.read()

  @staticmethod
  def _check_etag_match(etag_headers, etag, allow_weak_match):
    """Checks if an etag header matches a given etag.

    Args:
      etag_headers: A string representing an e-tag header value e.g.
          '"xyzzy", "r2d2xxxx", W/"c3piozzzz"' or '*'.
      etag: The etag to match the header to. If None then only the '*' header
          with match.
      allow_weak_match: If True then weak etags are allowed to match.

    Returns:
      True if there is a match, False otherwise.
    """
    # From RFC-2616:
    # entity-tag = [ weak ] opaque-tag
    # weak       = "W/"
    # opaque-tag = quoted-string
    # quoted-string  = ( <"> *(qdtext | quoted-pair ) <"> )
    # qdtext         = <any TEXT except <">>
    # quoted-pair    = "\" CHAR
    # TEXT           = <any OCTET except CTLs, but including LWS>
    # CHAR           = <any US-ASCII character (octets 0 - 127)>

    # This parsing is not actually correct since it assumes that commas cannot
    # appear in etags. But the generated etags do not contain commas so this
    # still works.
    for etag_header in etag_headers.split(','):
      if etag_header.startswith('W/'):
        if allow_weak_match:
          etag_header = etag_header[2:]
        else:
          continue
      etag_header = etag_header.strip().strip('"')
      if etag_header == '*' or etag_header == etag:
        return True
    return False

  @staticmethod
  def _is_relative_path_valid(path):
    """Check if the relative path for a file is valid.

    To match prod, redirection logic only fires on paths that contain a . or ..
    as an entry, but ignores redundant separators. Since Dev App Server simply
    passes the path to open, redundant separators are ignored (i.e. path/to/file
    and path//to///file both map to the same thing). Since prod uses logic
    that treats redundant separators as significant, we need to handle them
    specially.

    A related problem is that if a redundant separator is placed as the file
    relative path, it can be passed to a StaticHandler as an absolute path.
    As os.path.join causes an absolute path to throw away previous components
    that could allow an attacker to read any file on the file system (i.e.
    if there a static directory handle for /static and an attacker asks for the
    path '/static//etc/passwd', '/etc/passwd' is passed as the relative path and
    calling os.path.join([root_dir, '/etc/passwd']) returns '/etc/passwd'.)

    Args:
      path: a path relative to a static handler base.

    Returns:
      bool indicating whether the path is valid or not.
    """

    # Note: can't do something like path == os.path.normpath(path) as Windows
    # would normalize separators to backslashes.
    return not os.path.isabs(path) and '' not in path.split('/')

  @staticmethod
  def _not_found_404(environ, start_response):
    status = httplib.NOT_FOUND
    start_response('%d %s' % (status, httplib.responses[status]),
                   [('Content-Type', 'text/plain')])
    return ['%s not found' % environ['PATH_INFO']]


class StaticFilesHandler(StaticContentHandler):
  """Servers content for the "static_files" handler.

  For example:
    handlers:
    - url: /(.*)/(.*)
      static_files: \1/\2
      upload: (.*)/(.*)
  """

  def __init__(self, root_path, url_map):
    """Initializer for StaticFilesHandler.

    Args:
      root_path: A string containing the full path of the directory containing
          the application's app.yaml file.
      url_map: An appinfo.URLMap instance containing the configuration for this
          handler.
    """
    try:
      url_pattern = re.compile('%s$' % url_map.url)
    except re.error, e:
      raise errors.InvalidAppConfigError(
          'invalid url %r in static_files handler: %s' % (url_map.url, e))

    super(StaticFilesHandler, self).__init__(root_path,
                                             url_map,
                                             url_pattern)

  def handle(self, match, environ, start_response):
    """Serves the file content matching the request.

    Args:
      match: The re.MatchObject containing the result of matching the URL
        against this handler's URL pattern.
      environ: An environ dict for the current request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    relative_path = match.expand(self._url_map.static_files)
    if not self._is_relative_path_valid(relative_path):
      if self._url_map.require_matching_file:
        return None
      else:
        return self._not_found_404(environ, start_response)
    full_path = os.path.join(self._root_path, relative_path)
    return self._handle_path(full_path, environ, start_response)


class StaticDirHandler(StaticContentHandler):
  """Servers content for the "static_files" handler.

  For example:
    handlers:
    - url: /css
      static_dir: stylesheets
  """

  def __init__(self, root_path, url_map):
    """Initializer for StaticDirHandler.

    Args:
      root_path: A string containing the full path of the directory containing
          the application's app.yaml file.
      url_map: An appinfo.URLMap instance containing the configuration for this
          handler.
    """
    url = url_map.url
    # Take a url pattern like "/css" and transform it into a match pattern like
    # "/css/(?P<file>.*)$"
    if url[-1] != '/':
      url += '/'

    try:
      url_pattern = re.compile('%s(?P<file>.*)$' % url)
    except re.error, e:
      raise errors.InvalidAppConfigError(
          'invalid url %r in static_dir handler: %s' % (url, e))

    super(StaticDirHandler, self).__init__(root_path,
                                           url_map,
                                           url_pattern)

  def handle(self, match, environ, start_response):
    """Serves the file content matching the request.

    Args:
      match: The re.MatchObject containing the result of matching the URL
        against this handler's URL pattern.
      environ: An environ dict for the current request as defined in PEP-333.
      start_response: A function with semantics defined in PEP-333.

    Returns:
      An iterable over strings containing the body of the HTTP response.
    """
    relative_path = match.group('file')
    if not self._is_relative_path_valid(relative_path):
      return self._not_found_404(environ, start_response)
    full_path = os.path.join(self._root_path,
                             self._url_map.static_dir,
                             relative_path)
    return self._handle_path(full_path, environ, start_response)
