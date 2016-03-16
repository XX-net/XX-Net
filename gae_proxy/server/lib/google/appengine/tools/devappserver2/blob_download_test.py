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
"""Tests for devappserver2.blob_download."""

import base64
import cStringIO
import datetime
import os
import shutil
import tempfile
import unittest

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import blobstore
from google.appengine.api import datastore
from google.appengine.api import datastore_file_stub
from google.appengine.api import namespace_manager
from google.appengine.api.blobstore import blobstore_stub
from google.appengine.api.blobstore import file_blob_storage
from google.appengine.ext.cloudstorage import cloudstorage_stub
from google.appengine.tools.devappserver2 import blob_download
from google.appengine.tools.devappserver2 import request_rewriter
from google.appengine.tools.devappserver2 import wsgi_test_utils


class DownloadTestBase(unittest.TestCase):
  """Base class for testing devappserver2 blob download rewriter."""

  def setUp(self):
    """Configure test harness."""
    # Configure os.environ to make it look like the relevant parts of the
    # CGI environment that the stub relies on.
    self.original_environ = dict(os.environ)
    os.environ.update({
        'APPLICATION_ID': 'app',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8080',
        'AUTH_DOMAIN': 'abcxyz.com',
        'USER_EMAIL': 'user@abcxyz.com',
        })

    # Set up testing blobstore files.
    self.tmpdir = tempfile.mkdtemp()
    storage_directory = os.path.join(self.tmpdir, 'blob_storage')
    self.blob_storage = file_blob_storage.FileBlobStorage(storage_directory,
                                                          'appid1')
    self.blobstore_stub = blobstore_stub.BlobstoreServiceStub(self.blob_storage)

    # Use a fresh file datastore stub.
    self.datastore_file = os.path.join(self.tmpdir, 'datastore_v3')
    self.history_file = os.path.join(self.tmpdir, 'history')
    for filename in [self.datastore_file, self.history_file]:
      if os.access(filename, os.F_OK):
        os.remove(filename)

    self.datastore_stub = datastore_file_stub.DatastoreFileStub(
        'app', self.datastore_file, self.history_file, use_atexit=False)

    self.apiproxy = apiproxy_stub_map.APIProxyStubMap()
    apiproxy_stub_map.apiproxy = self.apiproxy
    apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', self.datastore_stub)
    apiproxy_stub_map.apiproxy.RegisterStub('blobstore', self.blobstore_stub)

  def tearDown(self):
    """Restore original environment."""
    os.environ = self.original_environ
    shutil.rmtree(self.tmpdir)

  def create_blob(self):
    """Create a blob in the datastore and on disk.

    Returns:
      BlobKey of new blob.
    """
    contents = 'a blob'
    blob_key = blobstore.BlobKey('blob-key-1')
    self.blob_storage.StoreBlob(blob_key, cStringIO.StringIO(contents))
    entity = datastore.Entity(blobstore.BLOB_INFO_KIND,
                              name=str(blob_key),
                              namespace='')
    entity['content_type'] = 'image/png'
    entity['creation'] = datetime.datetime(1999, 10, 10, 8, 42, 0)
    entity['filename'] = 'largeblob.png'
    entity['size'] = len(contents)
    datastore.Put(entity)

    return blob_key


class BlobDownloadTest(DownloadTestBase, wsgi_test_utils.WSGITestCase):
  """Test the download rewriter."""

  def test_non_download_response(self):
    """Response is not rewritten if missing download header."""
    environ = {'HTTP_RANGE': 'bytes=2-5'}   # Should be ignored.

    headers = [(blobstore.BLOB_RANGE_HEADER, 'bytes=1-4')]

    state = request_rewriter.RewriterState(environ, '200 original message',
                                           headers, 'original body')

    blob_download.blobstore_download_rewriter(state)

    self.assertEqual('200 original message', state.status)
    # X-AppEngine-BlobRange should not be removed if there is no BlobKey header.
    self.assertHeadersEqual(headers, state.headers)
    self.assertEqual('original body', ''.join(state.body))
    self.assertFalse(state.allow_large_response)

  def test_get_blob_storage(self):
    """Test getting blob storage from datastore stub."""
    blob_storage = blob_download._get_blob_storage()
    self.assertEquals(self.blobstore_stub.storage, blob_storage)

  def test_parse_range_header(self):
    """Test ParseRangeHeader function."""
    self.assertEquals(
        (None, None), blob_download._parse_range_header(''))
    self.assertEquals(
        (None, None), blob_download._parse_range_header('invalid'))
    self.assertEquals(
        (1, None), blob_download._parse_range_header('bytes=1-'))
    self.assertEquals(
        (10, 21), blob_download._parse_range_header('bytes=10-20'))
    self.assertEquals(
        (-30, None), blob_download._parse_range_header('bytes=-30'))
    self.assertEquals(
        (None, None), blob_download._parse_range_header('bytes=-30-'))
    self.assertEquals(
        (None, None), blob_download._parse_range_header('bytes=-30-40'))
    self.assertEquals(
        (None, None), blob_download._parse_range_header('bytes=0-1,2-3'))
    self.assertEquals(
        (None, None), blob_download._parse_range_header('bytes=-0'))
    self.assertEquals(
        (None, None), blob_download._parse_range_header('bits=0-20'))
    self.assertEquals(
        (None, None), blob_download._parse_range_header('bytes=a-20'))
    self.assertEquals(
        (None, None), blob_download._parse_range_header('bytes=0-a'))
    self.assertEquals(
        (None, None), blob_download._parse_range_header('bytes=0--'))
    self.assertEquals(
        (None, None), blob_download._parse_range_header('bytes=--10'))
    self.assertEquals(
        (None, None), blob_download._parse_range_header('bytes=0--10'))

  def test_rewrite_for_download_use_stored_content_type_auto_mime(self):
    """Use auto Content-Type to set the blob's stored mime type."""
    self.test_rewrite_for_download_use_stored_content_type(auto_mimetype=True)

  def test_rewrite_for_download_use_stored_content_type(self,
                                                        auto_mimetype=False):
    """Tests that downloads rewrite when using blob's original content-type."""
    blob_key = self.create_blob()

    headers = [(blobstore.BLOB_KEY_HEADER, str(blob_key))]
    if auto_mimetype:
      headers.append(('Content-Type', blob_download._AUTO_MIME_TYPE))
    state = request_rewriter.RewriterState({}, '200 original message', headers,
                                           'original body')

    blob_download.blobstore_download_rewriter(state)

    self.assertEqual('200 original message', state.status)
    expected_headers = {
        'Content-Length': '6',
        'Content-Type': 'image/png',
    }
    self.assertHeadersEqual(expected_headers, state.headers)
    # Ensure that Content-Type is a str, not a unicode.
    self.assertIsInstance(state.headers['Content-Type'], str)
    self.assertEqual('a blob', ''.join(state.body))
    self.assertTrue(state.allow_large_response)

  def test_rewrite_for_download_preserve_user_content_type(self):
    """Tests that the application's provided Content-Type is preserved."""
    blob_key = self.create_blob()

    headers = [
        (blobstore.BLOB_KEY_HEADER, str(blob_key)),
        ('Content-Type', 'image/jpg'),
    ]
    state = request_rewriter.RewriterState({}, '200 original message', headers,
                                           'original body')

    blob_download.blobstore_download_rewriter(state)

    self.assertEqual('200 original message', state.status)
    expected_headers = {
        'Content-Length': '6',
        'Content-Type': 'image/jpg',
    }
    self.assertHeadersEqual(expected_headers, state.headers)
    self.assertEqual('a blob', ''.join(state.body))
    self.assertTrue(state.allow_large_response)

  def test_rewrite_for_download_not_200(self):
    """Download requested, but status code is not 200."""
    blob_key = self.create_blob()

    headers = [(blobstore.BLOB_KEY_HEADER, str(blob_key))]
    state = request_rewriter.RewriterState({}, '201 original message', headers,
                                           'original body')

    blob_download.blobstore_download_rewriter(state)

    self.assertEqual('500 Internal Server Error', state.status)
    expected_headers = {'Content-Length': '0'}
    self.assertHeadersEqual(expected_headers, state.headers)
    self.assertEqual('', ''.join(state.body))
    self.assertFalse(state.allow_large_response)

  def test_rewrite_for_download_missing_blob(self):
    """Tests downloading a missing blob key."""
    environ = {'HTTP_RANGE': 'bytes=2-5'}   # Should be ignored.
    headers = [(blobstore.BLOB_KEY_HEADER, 'no such blob')]
    state = request_rewriter.RewriterState(environ, '200 original message',
                                           headers, 'original body')

    blob_download.blobstore_download_rewriter(state)

    self.assertEqual('500 Internal Server Error', state.status)
    expected_headers = {'Content-Length': '0'}
    self.assertHeadersEqual(expected_headers, state.headers)
    self.assertEqual('', ''.join(state.body))
    self.assertFalse(state.allow_large_response)

  def test_rewrite_for_download_missing_blob_delete_headers(self):
    """Tests that a missing blob deletes Content-Type and BlobRange headers."""
    environ = {'HTTP_RANGE': 'bytes=2-5'}   # Should be ignored.
    headers = [
        (blobstore.BLOB_KEY_HEADER, 'no such blob'),
        (blobstore.BLOB_RANGE_HEADER, 'bytes=1-4'),
        ('Content-Type', 'image/jpg'),
    ]
    state = request_rewriter.RewriterState(environ, '200 original message',
                                           headers, 'original body')

    blob_download.blobstore_download_rewriter(state)

    self.assertEqual('500 Internal Server Error', state.status)
    expected_headers = {'Content-Length': '0'}
    self.assertHeadersEqual(expected_headers, state.headers)
    self.assertEqual('', ''.join(state.body))
    self.assertFalse(state.allow_large_response)

  def do_blob_range_test(self, blobrange, expected_range, expected_body,
                         test_range_request=False, expect_unsatisfiable=False):
    """Performs a blob range response test.

    Args:
      blobrange: Value of the X-AppEngine-BlobRange response header.
      expected_range: Expected Content-Range.
      expected_body: Expected body.
      test_range_request: If True, tests with a Range request header instead of
        an X-AppEngine-BlobRange application response header.
      expect_unsatisfiable: If True, expects 416 Requested Range Not Satisfiable
        instead of 206 Partial Content.
    """
    blob_key = self.create_blob()

    environ = {}
    if test_range_request:
      environ['HTTP_RANGE'] = blobrange
    else:
      environ['HTTP_RANGE'] = 'bytes=2-5'   # Should be ignored.
    headers = [
        (blobstore.BLOB_KEY_HEADER, str(blob_key)),
        ('Content-Type', 'image/jpg'),
        ('Content-Range', 'bytes 1-2/6'),   # Should be ignored.
    ]
    if not test_range_request:
      headers.append((blobstore.BLOB_RANGE_HEADER, blobrange))
    state = request_rewriter.RewriterState(environ, '200 original message',
                                           headers, 'original body')

    blob_download.blobstore_download_rewriter(state)

    if expect_unsatisfiable:
      expected_status = '416 Requested Range Not Satisfiable'
    else:
      expected_status = '206 Partial Content'
    expected_headers = {
        'Content-Length': str(len(expected_body)),
        'Content-Range': expected_range,
    }
    if not expect_unsatisfiable:
      expected_headers['Content-Type'] = 'image/jpg'
    expected_allow_large_response = not expect_unsatisfiable

    self.assertEqual(expected_status, state.status)
    self.assertHeadersEqual(expected_headers, state.headers)
    self.assertEqual(expected_body, ''.join(state.body))
    self.assertEqual(expected_allow_large_response, state.allow_large_response)

  def test_download_range_blob_range_header(self):
    """Tests downloading range due to X-AppEngine-BlobRange response header."""
    self.do_blob_range_test('bytes=1-4', 'bytes 1-4/6', ' blo')

  def test_download_range_blob_range_header_start_before_start(self):
    """Tests downloading range when BlobRange start is before the blob start."""
    self.do_blob_range_test('bytes=-10', 'bytes 0-5/6', 'a blob')

  def test_download_range_blob_range_header_start_after_end(self):
    """Tests for error when BlobRange start is after the blob end."""
    self.do_blob_range_test('bytes=6-20', '*/6', '', expect_unsatisfiable=True)

  def test_download_range_blob_range_header_too_long(self):
    """Tests downloading range when BlobRange is larger than blob."""
    self.do_blob_range_test('bytes=1-400', 'bytes 1-5/6', ' blob')

  def test_download_range_blob_range_header_not_parseable(self):
    """Tests for error when BlobRange header is not parseable."""
    self.do_blob_range_test('bytes=xyz', '*/6', '', expect_unsatisfiable=True)

  def test_download_range_blob_range_header_no_end(self):
    """Tests downloading range when BlobRange only provides start index."""
    self.do_blob_range_test('bytes=2-', 'bytes 2-5/6', 'blob')

  def test_download_range_blob_range_header_negative_start(self):
    """Tests downloading range when BlobRange uses a negative start index."""
    self.do_blob_range_test('bytes=-1', 'bytes 5-5/6', 'b')
    self.do_blob_range_test('bytes=-2', 'bytes 4-5/6', 'ob')
    self.do_blob_range_test('bytes=-3', 'bytes 3-5/6', 'lob')
    self.do_blob_range_test('bytes=-4', 'bytes 2-5/6', 'blob')
    self.do_blob_range_test('bytes=-5', 'bytes 1-5/6', ' blob')
    self.do_blob_range_test('bytes=-6', 'bytes 0-5/6', 'a blob')

  def test_download_range_blob_range_header_single_byte(self):
    """Tests downloading range when BlobRange is a single byte."""
    self.do_blob_range_test('bytes=0-0', 'bytes 0-0/6', 'a')
    self.do_blob_range_test('bytes=1-1', 'bytes 1-1/6', ' ')
    self.do_blob_range_test('bytes=2-2', 'bytes 2-2/6', 'b')
    self.do_blob_range_test('bytes=3-3', 'bytes 3-3/6', 'l')
    self.do_blob_range_test('bytes=4-4', 'bytes 4-4/6', 'o')
    self.do_blob_range_test('bytes=5-5', 'bytes 5-5/6', 'b')

  def test_download_range_blob_range_header_empty(self):
    """Tests that whole blob is downloaded when BlobRange is empty."""
    blob_key = self.create_blob()

    environ = {'HTTP_RANGE': 'bytes=2-5'}   # Should be ignored.
    headers = [
        (blobstore.BLOB_KEY_HEADER, str(blob_key)),
        (blobstore.BLOB_RANGE_HEADER, ''),
        ('Content-Type', 'image/jpg'),
    ]
    state = request_rewriter.RewriterState(environ, '200 original message',
                                           headers, 'original body')

    blob_download.blobstore_download_rewriter(state)

    self.assertEqual('200 original message', state.status)
    expected_headers = {
        'Content-Length': '6',
        'Content-Type': 'image/jpg',
    }
    self.assertHeadersEqual(expected_headers, state.headers)
    self.assertEqual('a blob', ''.join(state.body))
    self.assertTrue(state.allow_large_response)

  def test_download_range_range_header(self):
    """Tests downloading range due to a Range request header."""
    self.do_blob_range_test('bytes=1-4', 'bytes 1-4/6', ' blo',
                            test_range_request=True)

  def test_download_range_request_range_header_start_before_start(self):
    """Tests downloading range when Range start is before the blob start."""
    self.do_blob_range_test('bytes=-10', 'bytes 0-5/6', 'a blob',
                            test_range_request=True)

  def test_download_range_request_range_header_start_after_end(self):
    """Tests for error when Range start is after the blob end."""
    self.do_blob_range_test('bytes=6-20', '*/6', '',
                            test_range_request=True, expect_unsatisfiable=True)

  def test_download_range_range_header_too_long(self):
    """Tests downloading range when Range is larger than blob."""
    self.do_blob_range_test('bytes=1-500', 'bytes 1-5/6', ' blob',
                            test_range_request=True)

  def test_download_range_request_range_header_not_parsable(self):
    """Tests for error when Range header is not parseable."""
    self.do_blob_range_test('bytes=half of it', '*/6', '',
                            test_range_request=True, expect_unsatisfiable=True)

  def test_download_range_range_header_no_end(self):
    """Tests downloading range when Range only provides start index."""
    self.do_blob_range_test('bytes=2-', 'bytes 2-5/6', 'blob',
                            test_range_request=True)

  def test_download_range_range_header_negative_start(self):
    """Tests downloading range when Range uses a negative start index."""
    self.do_blob_range_test('bytes=-1', 'bytes 5-5/6', 'b',
                            test_range_request=True)
    self.do_blob_range_test('bytes=-2', 'bytes 4-5/6', 'ob',
                            test_range_request=True)
    self.do_blob_range_test('bytes=-3', 'bytes 3-5/6', 'lob',
                            test_range_request=True)
    self.do_blob_range_test('bytes=-4', 'bytes 2-5/6', 'blob',
                            test_range_request=True)
    self.do_blob_range_test('bytes=-5', 'bytes 1-5/6', ' blob',
                            test_range_request=True)
    self.do_blob_range_test('bytes=-6', 'bytes 0-5/6', 'a blob',
                            test_range_request=True)

  def test_download_range_range_header_single_byte(self):
    """Tests downloading range when Range is a single byte."""
    self.do_blob_range_test('bytes=0-0', 'bytes 0-0/6', 'a',
                            test_range_request=True)
    self.do_blob_range_test('bytes=1-1', 'bytes 1-1/6', ' ',
                            test_range_request=True)
    self.do_blob_range_test('bytes=2-2', 'bytes 2-2/6', 'b',
                            test_range_request=True)
    self.do_blob_range_test('bytes=3-3', 'bytes 3-3/6', 'l',
                            test_range_request=True)
    self.do_blob_range_test('bytes=4-4', 'bytes 4-4/6', 'o',
                            test_range_request=True)
    self.do_blob_range_test('bytes=5-5', 'bytes 5-5/6', 'b',
                            test_range_request=True)

  def test_download_range_range_header_empty(self):
    """Tests that whole blob is downloaded when Range is empty."""
    blob_key = self.create_blob()

    environ = {'HTTP_RANGE': ''}
    headers = [
        (blobstore.BLOB_KEY_HEADER, str(blob_key)),
        ('Content-Type', 'image/jpg'),
    ]
    state = request_rewriter.RewriterState(environ, '200 original message',
                                           headers, 'original body')

    blob_download.blobstore_download_rewriter(state)

    self.assertEqual('200 original message', state.status)
    expected_headers = {
        'Content-Length': '6',
        'Content-Type': 'image/jpg',
    }
    self.assertHeadersEqual(expected_headers, state.headers)
    self.assertEqual('a blob', ''.join(state.body))
    self.assertTrue(state.allow_large_response)


class BlobDownloadTestNamespace(BlobDownloadTest):
  """Executes all of the superclass tests but with a namespace set."""

  def setUp(self):
    """Setup for namespaces test."""
    super(BlobDownloadTestNamespace, self).setUp()
    # Set the namespace. Blobstore should ignore this.
    namespace_manager.set_namespace('abc')


class BlobDownloadTestGoogleStorage(BlobDownloadTest):
  """Executes all of the superclass tests with a Google Storage object."""

  def create_blob(self, content_type='image/png'):
    """Create a GS object in the datastore and on disk.

    Overrides the superclass create_blob method.

    Returns:
      The BlobKey of the new object."
    """
    data = 'a blob'
    filename = '/some_bucket/some_object'
    stub = cloudstorage_stub.CloudStorageStub(self.blob_storage)
    options = {}
    if content_type:
      options['content-type'] = content_type
    blob_key = stub.post_start_creation(filename, options)
    stub.put_continue_creation(blob_key, data, (0, len(data) - 1), len(data))
    self.blob_storage.StoreBlob(blob_key, cStringIO.StringIO(data))

    return blob_key

  def test_default_content_type(self):
    """Tests downloads when upload does not specify content-type."""
    blob_key = self.create_blob(content_type=None)

    headers = [(blobstore.BLOB_KEY_HEADER, str(blob_key))]
    state = request_rewriter.RewriterState({}, '200 original message', headers,
                                           'original body')

    blob_download.blobstore_download_rewriter(state)

    self.assertEqual('200 original message', state.status)
    expected_headers = {
        'Content-Length': '6',
        'Content-Type': cloudstorage_stub._GCS_DEFAULT_CONTENT_TYPE,
    }
    self.assertHeadersEqual(expected_headers, state.headers)
    self.assertEqual('a blob', ''.join(state.body))


class BlobDownloadIntegrationTest(DownloadTestBase,
                                  wsgi_test_utils.RewriterTestCase):
  """Test that the rewriter chain properly rewrites blob downloads."""

  def test_rewrite_for_download_use_stored_content_type_auto_mime(self):
    """Use auto Content-Type to set the blob's stored mime type."""
    self.test_rewrite_for_download_use_stored_content_type(auto_mimetype=True)

  def test_rewrite_for_download_use_stored_content_type(self,
                                                        auto_mimetype=False):
    """Tests that downloads rewrite when using blob's original content-type."""
    blob_key = self.create_blob()

    headers = [(blobstore.BLOB_KEY_HEADER, str(blob_key))]
    if auto_mimetype:
      headers.append(('Content-Type', blob_download._AUTO_MIME_TYPE))
    application = wsgi_test_utils.constant_app('200 original message', headers,
                                               'original body')

    expected_status = '200 original message'

    expected_headers = {
        'Content-Length': '6',
        'Content-Type': 'image/png',
        'Cache-Control': 'no-cache',
        'Expires': 'Fri, 01 Jan 1990 00:00:00 GMT',
    }

    expected_body = 'a blob'

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

  def test_rewrite_for_download_missing_blob(self):
    """Tests that a missing blob key gives the default content-type."""
    headers = [
        (blobstore.BLOB_KEY_HEADER, 'no such blob'),
        ('Content-Type', 'text/x-my-content-type'),
    ]
    application = wsgi_test_utils.constant_app('200 original message', headers,
                                               'original body')

    expected_status = '500 Internal Server Error'

    # Note: The default Content-Type is expected, even though there is no
    # contents (this matches production).
    expected_headers = {
        'Content-Length': '0',
        'Content-Type': 'text/html',
        'Cache-Control': 'no-cache',
        'Expires': 'Fri, 01 Jan 1990 00:00:00 GMT',
    }

    expected_body = ''

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application)

  def test_download_range_blob_range_header_start_after_end(self):
    """Tests for error when BlobRange start is after the blob end."""
    blob_key = self.create_blob()

    environ = {'HTTP_RANGE': 'bytes=2-5'}   # Should be ignored.

    headers = [
        (blobstore.BLOB_KEY_HEADER, str(blob_key)),
        (blobstore.BLOB_RANGE_HEADER, 'bytes=6-20'),
        ('Content-Type', 'text/x-my-content-type'),   # Should be ignored.
        ('Content-Range', 'bytes 1-2/6'),             # Should be ignored.
    ]
    application = wsgi_test_utils.constant_app('200 original message', headers,
                                               'original body')

    expected_status = '416 Requested Range Not Satisfiable'

    # Note: The default Content-Type is expected, even though there is no
    # contents (this matches production).
    expected_headers = {
        'Content-Length': '0',
        'Content-Type': 'text/html',
        'Content-Range': '*/6',
        'Cache-Control': 'no-cache',
        'Expires': 'Fri, 01 Jan 1990 00:00:00 GMT',
    }

    expected_body = ''

    self.assert_rewritten_response(expected_status, expected_headers,
                                   expected_body, application, environ)


if __name__ == '__main__':
  unittest.main()
