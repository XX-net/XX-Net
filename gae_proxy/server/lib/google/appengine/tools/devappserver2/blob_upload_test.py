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
"""Tests for devappserver2.blob_upload."""



import base64
import cgi
import cStringIO
import datetime
import email
import email.message
import hashlib
import os
import re
import shutil
import StringIO
import tempfile
import unittest
import urlparse
import wsgiref.util

import google
import mox
import webob.exc

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore
from google.appengine.api import datastore_errors
from google.appengine.api import datastore_file_stub
from google.appengine.api import namespace_manager
from google.appengine.api import user_service_stub
from google.appengine.api.blobstore import blobstore_stub
from google.appengine.api.blobstore import file_blob_storage
from google.appengine.ext import blobstore
from google.appengine.tools.devappserver2 import blob_upload
from google.appengine.tools.devappserver2 import constants

EXPECTED_GENERATED_CONTENT_TYPE = (
    'multipart/form-data; boundary="================1234=="')
EXPECTED_GENERATED_MIME_MESSAGE = (
    """--================1234==
Content-Type: message/external-body; blob-key="item1"; \
access-type="X-AppEngine-BlobKey"
Content-Disposition: form-data; name="field1"; filename="stuff.png"

Content-Type: image/png; a="b"; x="y"
h2: v2
Content-MD5: ODI2ZTgxNDJlNmJhYWJlOGFmNzc5ZjVmNDkwY2Y1ZjU=
Content-Length: 5
h1: v1
X-AppEngine-Upload-Creation: 2008-11-12 10:40:00.000000
Content-Disposition: form-data; name="field1"; filename="stuff.png"


--================1234==
Content-Type: message/external-body; blob-key="item2"; \
access-type="X-AppEngine-BlobKey"
Content-Disposition: form-data; name="field2"; filename="stuff.pdf"

Content-Type: application/pdf
Content-Length: 5
Content-MD5: MWMxYzk2ZmQyY2Y4MzMwZGIwYmZhOTM2Y2U4MmYzYjk=
X-AppEngine-Upload-Creation: 2008-11-12 10:40:00.000000
Content-Disposition: form-data; name="field2"; filename="stuff.pdf"


--================1234==
Content-Type: message/external-body; blob-key="item3"; \
access-type="X-AppEngine-BlobKey"
Content-Disposition: form-data; name="field2"; filename="stuff.txt"

Content-Type: text/plain
Content-Length: 11
Content-MD5: YmRjMDNkMGEyMTQwMTRlNjMyM2EyNGQzZDkzOTczNWY=
X-AppEngine-Upload-Creation: 2008-11-12 10:40:00.000000
Content-Disposition: form-data; name="field2"; filename="stuff.txt"


--================1234==
Content-Type: text/plain
Content-Disposition: form-data; name="field3"

variable1
--================1234==--""").replace('\n', '\r\n')

EXPECTED_GENERATED_CONTENT_TYPE_WITH_BUCKET = (
    'multipart/form-data; boundary="================1234=="')
EXPECTED_GENERATED_MIME_MESSAGE_WITH_BUCKET = (
    """--================1234==
Content-Type: message/external-body; blob-key="encoded_gs_file:\
bXktdGVzdC1idWNrZXQvZmFrZS1leHBlY3RlZGtleQ=="; \
access-type="X-AppEngine-BlobKey"
Content-Disposition: form-data; name="field1"; filename="stuff.png"

Content-Type: image/png; a="b"; x="y"
h2: v2
Content-MD5: ODI2ZTgxNDJlNmJhYWJlOGFmNzc5ZjVmNDkwY2Y1ZjU=
Content-Length: 5
h1: v1
X-AppEngine-Upload-Creation: 2008-11-12 10:40:00.000000
X-AppEngine-Cloud-Storage-Object: /gs/my-test-bucket/fake-expectedkey
Content-Disposition: form-data; name="field1"; filename="stuff.png"


--================1234==--""").replace('\n', '\r\n')

EXPECTED_GENERATED_UTF8_CONTENT_TYPE = (
    'multipart/form-data; boundary="================1234=="')
EXPECTED_GENERATED_UTF8_MIME_MESSAGE = (
    """--================1234==
Content-Type: message/external-body; blob-key="item1"; \
access-type="X-AppEngine-BlobKey"
Content-Disposition: form-data; name="field1"; \
filename="chinese_char_name_\xe6\xb1\x89.txt"

Content-Type: text/plain; a="b"; x="y"
h2: v2
Content-MD5: ODI2ZTgxNDJlNmJhYWJlOGFmNzc5ZjVmNDkwY2Y1ZjU=
Content-Length: 5
h1: v1
X-AppEngine-Upload-Creation: 2008-11-12 10:40:00.000000
Content-Disposition: form-data; name="field1"; \
filename="chinese_char_name_\xe6\xb1\x89.txt"


--================1234==--""").replace('\n', '\r\n')

EXPECTED_GENERATED_CONTENT_TYPE_NO_HEADERS = (
    'multipart/form-data; boundary="================1234=="')
EXPECTED_GENERATED_MIME_MESSAGE_NO_HEADERS = (
    """--================1234==
Content-Type: message/external-body; blob-key="item1"; \
access-type="X-AppEngine-BlobKey"
Content-Disposition: form-data; name="field1"; filename="file1"

Content-Type: application/octet-stream
Content-Length: 5
Content-MD5: ODI2ZTgxNDJlNmJhYWJlOGFmNzc5ZjVmNDkwY2Y1ZjU=
X-AppEngine-Upload-Creation: 2008-11-12 10:40:00.000100
Content-Disposition: form-data; name="field1"; filename="file1"


--================1234==
Content-Type: text/plain
Content-Disposition: form-data; name="field2"

variable1
--================1234==--""").replace('\n', '\r\n')

EXPECTED_GENERATED_CONTENT_TYPE_ZERO_LENGTH_BLOB = (
    'multipart/form-data; boundary="================1234=="')
EXPECTED_GENERATED_MIME_MESSAGE_ZERO_LENGTH_BLOB = (
    """--================1234==
Content-Type: message/external-body; blob-key="item1"; \
access-type="X-AppEngine-BlobKey"
Content-Disposition: form-data; name="field1"; filename="stuff.png"

Content-Type: image/png; a="b"; x="y"
h2: v2
Content-MD5: ODI2ZTgxNDJlNmJhYWJlOGFmNzc5ZjVmNDkwY2Y1ZjU=
Content-Length: 5
h1: v1
X-AppEngine-Upload-Creation: 2008-11-12 10:40:00.000000
Content-Disposition: form-data; name="field1"; filename="stuff.png"


--================1234==
Content-Type: message/external-body; blob-key="item2"; \
access-type="X-AppEngine-BlobKey"
Content-Disposition: form-data; name="field2"; filename="stuff.pdf"

Content-Type: application/pdf
Content-Length: 0
Content-MD5: ZDQxZDhjZDk4ZjAwYjIwNGU5ODAwOTk4ZWNmODQyN2U=
X-AppEngine-Upload-Creation: 2008-11-12 10:40:00.000000
Content-Disposition: form-data; name="field2"; filename="stuff.pdf"


--================1234==--""").replace('\n', '\r\n')

EXPECTED_GENERATED_CONTENT_TYPE_NO_FILENAME = (
    'multipart/form-data; boundary="================1234=="')
EXPECTED_GENERATED_MIME_MESSAGE_NO_FILENAME = (
    """--================1234==
Content-Type: message/external-body; blob-key="item1"; \
access-type="X-AppEngine-BlobKey"
Content-Disposition: form-data; name="field1"; filename="stuff.png"

Content-Type: image/png; a="b"; x="y"
h2: v2
Content-MD5: ODI2ZTgxNDJlNmJhYWJlOGFmNzc5ZjVmNDkwY2Y1ZjU=
Content-Length: 5
h1: v1
X-AppEngine-Upload-Creation: 2008-11-12 10:40:00.000000
Content-Disposition: form-data; name="field1"; filename="stuff.png"


--================1234==--""").replace('\n', '\r\n')

BAD_MIMES = ('/', 'image', 'image/', '/gif', 'app/monkey/banana')


class FakeForm(dict):
  """Simple assignable object for emulating cgi.FieldStorage."""

  def __init__(self, subforms=None, headers=None, **kwds):
    """Construct form from keywords."""
    super(FakeForm, self).__init__()
    self.update(subforms or {})
    self.headers = headers or email.Message.Message()
    for key, value in kwds.iteritems():
      setattr(self, key, value)


class UploadTestBase(unittest.TestCase):
  """Base class for testing dev-appserver upload library."""

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

    # Set up mox.
    self.mox = mox.Mox()

    # Use a fresh file datastore stub.
    self.tmpdir = tempfile.mkdtemp()
    self.datastore_file = os.path.join(self.tmpdir, 'datastore_v3')
    self.history_file = os.path.join(self.tmpdir, 'history')
    for filename in [self.datastore_file, self.history_file]:
      if os.access(filename, os.F_OK):
        os.remove(filename)

    self.stub = datastore_file_stub.DatastoreFileStub(
        'app', self.datastore_file, self.history_file, use_atexit=False)

    self.apiproxy = apiproxy_stub_map.APIProxyStubMap()
    apiproxy_stub_map.apiproxy = self.apiproxy
    apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', self.stub)

  def tearDown(self):
    """Restore original environment."""
    os.environ = self.original_environ
    shutil.rmtree(self.tmpdir)

  def assertMessageEqual(self, expected, actual):
    """Assert two strings representing messages are equal (equivalent).

    This normalizes the headers in both arguments and then compares
    them using assertMultiLineEqual().
    """
    expected = self.normalize_header_lines(expected)
    actual = self.normalize_header_lines(actual)
    return self.assertMultiLineEqual(expected, actual)

  def normalize_header_lines(self, message):
    """Normalize blocks of header lines in a message.

    This sorts blocks of consecutive header lines and then for certain
    headers (Content-Type and -Disposition) sorts the parameter values.
    """
    lines = message.splitlines(True)
    # Normalize groups of header-like lines.
    output = []
    headers = []
    for line in lines:
      if re.match(r'^\S+: ', line):
        # It's a header line.  Maybe normalize the parameter values.
        line = self.normalize_header(line)
        headers.append(line)
      else:
        # Not a header.  Flush the list of headers.
        if headers:
          headers.sort()
          output.extend(headers)
          headers = []
        output.append(line)
    # Flush the final list of headers.
    if headers:
      headers.sort()
      output.extend(headers)
    # Put it all back together.
    return ''.join(output)

  def normalize_header(self, line):
    """Normalize parameter values of Content-Type and -Disposition lines.

    This changes e.g.
      Content-Type: foo/bar; name="a"; file="b"
    into
      Content-Type: foo/bar; file="b"; name="a"

    It leaves other headers alone.
    """
    match = re.match(r'^(Content-(?:Type|Disposition): )(\S+; .*\S)(\s*)\Z',
                     line, re.IGNORECASE)
    if not match:
      return line
    value = match.group(2)
    value = self.normalize_parameter_order(value)
    return match.group(1) + value + match.group(3)

  def normalize_parameter_order(self, value):
    """Normalize the parameter values of a header.

    This changes e.g.
      foo/bar; name="a"; file="b"
    into
      foo/bar; file="b"; name="a"

    Note that the text before the first ';' is unaffected.
    """
    parts = value.split('; ')
    if len(parts) > 2:
      value = parts[0] + '; ' + '; '.join(sorted(parts[1:]))
    return value


class GenerateBlobKeyTest(UploadTestBase):
  """Tests the GenerateBlobKey function."""

  def check_key(self, blob_key, expected_time, expected_random):
    """Check that blob_key decodes to expected value.

    Args:
      blob_key: Blob key that was actually generated.
      expected_time: Time stamp that is expected to be in the md5 digest.
      expected_random: Random number that is expected to be in the md5 digest.
    """
    if blob_key is None:
      self.fail('Generated blob-key is None.')
    digester = hashlib.md5()
    digester.update(str(expected_time))
    digester.update(str(expected_random))
    actual_digest = base64.urlsafe_b64decode(blob_key)
    self.assertEquals(digester.digest(), actual_digest)

  def test_generate_key(self):
    """Basic test of key generation."""
    time_func = self.mox.CreateMockAnything()
    random_func = self.mox.CreateMockAnything()

    time_func().AndReturn(10)
    random_func().AndReturn(20)

    self.mox.ReplayAll()

    key = blob_upload._generate_blob_key(time_func, random_func)
    self.check_key(key, 10, 20)

    self.mox.VerifyAll()

  def test_generate_key_with_conflict(self):
    """Test what happens when there is conflict in key generation."""
    time_func = self.mox.CreateMockAnything()
    random_func = self.mox.CreateMockAnything()

    time_func().AndReturn(10)
    random_func().AndReturn(20)

    time_func().AndReturn(10)
    random_func().AndReturn(30)

    time_func().AndReturn(10)
    random_func().AndReturn(20)
    random_func().AndReturn(30)
    random_func().AndReturn(40)

    self.mox.ReplayAll()

    # Create a pair of conflicting records.
    entity = datastore.Entity(
        blobstore.BLOB_INFO_KIND,
        name=str(blob_upload._generate_blob_key(time_func, random_func)),
        namespace='')
    datastore.Put(entity)
    entity = datastore.Entity(
        blobstore.BLOB_INFO_KIND,
        name=str(blob_upload._generate_blob_key(time_func, random_func)),
        namespace='')
    datastore.Put(entity)

    key = blob_upload._generate_blob_key(time_func, random_func)
    self.check_key(key, 10, 40)

    self.mox.VerifyAll()

  def test_too_many_conflicts(self):
    """Test what happens when there are too many conflicts in key generation."""
    time_func = self.mox.CreateMockAnything()
    random_func = self.mox.CreateMockAnything()

    # Create first set of keys
    for i in range(10):
      time_func().AndReturn(10)
      random_func().AndReturn(10 + i)

    # Try to create duplicate keys
    time_func().AndReturn(10)
    for i in range(10):
      random_func().AndReturn(10 + i)

    self.mox.ReplayAll()

    # Create a pair of conflicting records.
    for i in range(10):
      entity = datastore.Entity(
          blobstore.BLOB_INFO_KIND,
          name=str(blob_upload._generate_blob_key(time_func, random_func)),
          namespace='')
      datastore.Put(entity)
    self.assertRaises(blob_upload._TooManyConflictsError,
                      blob_upload._generate_blob_key,
                      time_func, random_func)

    self.mox.VerifyAll()


class GenerateBlobKeyTestNamespace(GenerateBlobKeyTest):
  """Executes all of the superclass tests but with a namespace set."""

  def setUp(self):
    """Setup for namespaces test."""
    super(GenerateBlobKeyTestNamespace, self).setUp()
    # Set the namespace. Blobstore should ignore this.
    namespace_manager.set_namespace('abc')


class UploadHandlerUnitTest(UploadTestBase):
  """Test the UploadHandler class's individual methods."""

  def setUp(self):
    """Set up additional parts of the test framework."""
    UploadTestBase.setUp(self)

    # Create a phoney blob-generation method for predictable key generation.
    self.generate_blob_key = self.mox.CreateMockAnything()
    # Create a mock now function for predictable timestamp generation.
    self.now = self.mox.CreateMockAnything()

    # Create blob-storage to be used in tests.
    self.blob_storage_path = os.path.join(self.tmpdir, 'blobstore')
    self.storage = file_blob_storage.FileBlobStorage(
        self.blob_storage_path,
        os.environ['APPLICATION_ID'])

    def forward_app(unused_environ, unused_start_response):
      raise Exception('Unexpected call to forward_app')

    def get_storage():
      return self.storage

    # Create handler for testing.
    self.handler = blob_upload.Application(
        forward_app, get_storage, self.generate_blob_key, self.now)

  def execute_blob_test(self, blob_content, expected_result,
                        base64_encoding=False):
    """Execute a basic blob insertion."""
    expected_key = blobstore.BlobKey('expectedkey')
    expected_creation = datetime.datetime(2008, 11, 12)

    self.generate_blob_key().AndReturn(expected_key)

    self.mox.ReplayAll()
    content_type, blob_file, filename = self.handler._preprocess_data(
        'image/png; a="b"; m="n"',
        StringIO.StringIO(blob_content),
        'stuff.png',
        base64_encoding)
    self.handler.store_blob(content_type=content_type,
                            filename=filename,
                            md5_hash=hashlib.md5(),
                            blob_file=blob_file,
                            creation=expected_creation)

    self.assertEquals(expected_result,
                      self.storage.OpenBlob(expected_key).read())

    blob_info = blobstore.get(expected_key)
    self.assertFalse(blob_info is None)
    self.assertEquals(('image/png', {'a': 'b', 'm': 'n'}),
                      cgi.parse_header(blob_info.content_type))
    self.assertEquals(expected_creation, blob_info.creation)
    self.assertEquals('stuff.png', blob_info.filename)
    self.assertEquals(len(expected_result), blob_info.size)

    self.mox.VerifyAll()

  def test_store_blob(self):
    """Test blob creation."""
    self.execute_blob_test('blob content', 'blob content')

  def test_store_and_build_forward_message(self):
    """Test the high-level method to store a blob and build a MIME message."""
    self.generate_blob_key().AndReturn(blobstore.BlobKey('item1'))
    self.generate_blob_key().AndReturn(blobstore.BlobKey('item2'))
    self.generate_blob_key().AndReturn(blobstore.BlobKey('item3'))

    self.now().AndReturn(datetime.datetime(2008, 11, 12, 10, 40))

    self.mox.ReplayAll()

    form = FakeForm({
        'field1': FakeForm(name='field1',
                           file=StringIO.StringIO('file1'),
                           type='image/png',
                           type_options={'a': 'b', 'x': 'y'},
                           filename='stuff.png',
                           headers={'h1': 'v1',
                                    'h2': 'v2',
                                   }),
        'field2': [FakeForm(name='field2',
                            file=StringIO.StringIO('file2'),
                            type='application/pdf',
                            type_options={},
                            filename='stuff.pdf',
                            headers={}),
                   FakeForm(name='field2',
                            file=StringIO.StringIO('file3 extra'),
                            type='text/plain',
                            type_options={},
                            filename='stuff.txt',
                            headers={}),
                  ],
        'field3': FakeForm(name='field3',
                           value='variable1',
                           type='text/plain',
                           type_options={},
                           filename=None),
        })

    content_type, content_text = self.handler.store_and_build_forward_message(
        form, '================1234==')

    self.mox.VerifyAll()

    self.assertEqual(EXPECTED_GENERATED_CONTENT_TYPE, content_type)
    self.assertMessageEqual(EXPECTED_GENERATED_MIME_MESSAGE, content_text)

    blob1 = blobstore.get('item1')
    self.assertEquals('stuff.png', blob1.filename)
    self.assertEquals(('image/png', {'a': 'b', 'x': 'y'}),
                      cgi.parse_header(blob1.content_type))

    blob2 = blobstore.get('item2')
    self.assertEquals('stuff.pdf', blob2.filename)
    self.assertEquals('application/pdf', blob2.content_type)

    blob3 = blobstore.get('item3')
    self.assertEquals('stuff.txt', blob3.filename)
    self.assertEquals('text/plain', blob3.content_type)

  def test_store_and_build_forward_message_with_gs_bucket(self):
    """Test the high-level method to store a blob and build a MIME message."""
    self.now().AndReturn(datetime.datetime(2008, 11, 12, 10, 40))
    expected_key = blobstore.BlobKey('expectedkey')
    self.generate_blob_key().AndReturn(expected_key)

    self.mox.ReplayAll()

    form = FakeForm({
        'field1': FakeForm(name='field1',
                           file=StringIO.StringIO('file1'),
                           type='image/png',
                           type_options={'a': 'b', 'x': 'y'},
                           filename='stuff.png',
                           headers={'h1': 'v1',
                                    'h2': 'v2',
                                   }),
        })

    content_type, content_text = self.handler.store_and_build_forward_message(
        form, '================1234==', bucket_name='my-test-bucket')

    self.mox.VerifyAll()

    self.assertEqual(EXPECTED_GENERATED_CONTENT_TYPE_WITH_BUCKET, content_type)
    self.assertMessageEqual(EXPECTED_GENERATED_MIME_MESSAGE_WITH_BUCKET,
                            content_text)
    blobkey = ('encoded_gs_file:bXktdGVzdC1idWNrZXQvZmFrZS1leHBlY3RlZGtleQ==')
    blobkey = blobstore_stub.BlobstoreServiceStub.ToDatastoreBlobKey(blobkey)
    blob1 = datastore.Get(blobkey)
    self.assertTrue('my-test-bucket' in blob1['filename'])

  def test_store_and_build_forward_message_utf8_values(self):
    """Test store and build message method with UTF-8 values."""
    self.generate_blob_key().AndReturn(blobstore.BlobKey('item1'))

    self.now().AndReturn(datetime.datetime(2008, 11, 12, 10, 40))

    self.mox.ReplayAll()

    form = FakeForm({
        'field1': FakeForm(name='field1',
                           file=StringIO.StringIO('file1'),
                           type='text/plain',
                           type_options={'a': 'b', 'x': 'y'},
                           filename='chinese_char_name_\xe6\xb1\x89.txt',
                           headers={'h1': 'v1',
                                    'h2': 'v2',
                                   }),
        })

    content_type, content_text = self.handler.store_and_build_forward_message(
        form, '================1234==')

    self.mox.VerifyAll()

    self.assertEqual(EXPECTED_GENERATED_UTF8_CONTENT_TYPE, content_type)
    self.assertMessageEqual(EXPECTED_GENERATED_UTF8_MIME_MESSAGE,
                            content_text)

    blob1 = blobstore.get('item1')
    self.assertEquals(u'chinese_char_name_\u6c49.txt', blob1.filename)

  def test_store_and_build_forward_message_latin1_values(self):
    """Test store and build message method with Latin-1 values."""
    # There is a special exception class for this case. This is designed to
    # emulate production, which currently fails silently. See b/6722082.
    self.now().AndReturn(datetime.datetime(2008, 11, 12, 10, 40))

    self.mox.ReplayAll()

    form = FakeForm({
        'field1': FakeForm(name='field1',
                           file=StringIO.StringIO('file1'),
                           type='text/plain',
                           type_options={'a': 'b', 'x': 'y'},
                           filename='german_char_name_f\xfc\xdfe.txt',
                           headers={'h1': 'v1',
                                    'h2': 'v2',
                                   }),
        })

    self.assertRaises(blob_upload._InvalidMetadataError,
                      self.handler.store_and_build_forward_message, form,
                      '================1234==')

    self.mox.VerifyAll()

    blob1 = blobstore.get('item1')
    self.assertIsNone(blob1)

  def test_store_and_build_forward_message_no_headers(self):
    """Test default header generation when no headers are provided."""
    self.generate_blob_key().AndReturn(blobstore.BlobKey('item1'))

    self.now().AndReturn(datetime.datetime(2008, 11, 12, 10, 40, 0, 100))

    self.mox.ReplayAll()

    form = FakeForm({'field1': FakeForm(name='field1',
                                        file=StringIO.StringIO('file1'),
                                        type=None,
                                        type_options={},
                                        filename='file1',
                                        headers={}),
                     'field2': FakeForm(name='field2',
                                        value='variable1',
                                        type=None,
                                        type_options={},
                                        filename=None,
                                        headers={}),
                    })

    content_type, content_text = self.handler.store_and_build_forward_message(
        form, '================1234==')

    self.mox.VerifyAll()

    self.assertEqual(EXPECTED_GENERATED_CONTENT_TYPE_NO_HEADERS, content_type)
    self.assertMessageEqual(EXPECTED_GENERATED_MIME_MESSAGE_NO_HEADERS,
                            content_text)

  def test_store_and_build_forward_message_zero_length_blob(self):
    """Test upload with a zero length blob."""
    self.generate_blob_key().AndReturn(blobstore.BlobKey('item1'))
    self.generate_blob_key().AndReturn(blobstore.BlobKey('item2'))

    self.now().AndReturn(datetime.datetime(2008, 11, 12, 10, 40))

    self.mox.ReplayAll()

    form = FakeForm({
        'field1': FakeForm(name='field1',
                           file=StringIO.StringIO('file1'),
                           type='image/png',
                           type_options={'a': 'b', 'x': 'y'},
                           filename='stuff.png',
                           headers={'h1': 'v1',
                                    'h2': 'v2',
                                   }),
        'field2': FakeForm(name='field2',
                           file=StringIO.StringIO(''),
                           type='application/pdf',
                           type_options={},
                           filename='stuff.pdf',
                           headers={}),
        })

    content_type, content_text = self.handler.store_and_build_forward_message(
        form, '================1234==')

    self.mox.VerifyAll()

    self.assertEqual(EXPECTED_GENERATED_CONTENT_TYPE_ZERO_LENGTH_BLOB,
                     content_type)
    self.assertMessageEqual(EXPECTED_GENERATED_MIME_MESSAGE_ZERO_LENGTH_BLOB,
                            content_text)

    blob1 = blobstore.get('item1')
    self.assertEquals('stuff.png', blob1.filename)

    blob2 = blobstore.get('item2')
    self.assertEquals('stuff.pdf', blob2.filename)

  def test_store_and_build_forward_message_no_filename(self):
    """Test upload with no filename in content disposition."""
    self.generate_blob_key().AndReturn(blobstore.BlobKey('item1'))

    self.now().AndReturn(datetime.datetime(2008, 11, 12, 10, 40))

    self.mox.ReplayAll()

    form = FakeForm({
        'field1': FakeForm(name='field1',
                           file=StringIO.StringIO('file1'),
                           type='image/png',
                           type_options={'a': 'b', 'x': 'y'},
                           filename='stuff.png',
                           headers={'h1': 'v1',
                                    'h2': 'v2',
                                   }),
        'field2': FakeForm(name='field2',
                           file=StringIO.StringIO(''),
                           type='application/pdf',
                           type_options={},
                           filename='',
                           headers={}),
        })

    content_type, content_text = self.handler.store_and_build_forward_message(
        form, '================1234==')

    self.mox.VerifyAll()

    self.assertEqual(EXPECTED_GENERATED_CONTENT_TYPE_NO_FILENAME, content_type)
    self.assertMessageEqual(EXPECTED_GENERATED_MIME_MESSAGE_NO_FILENAME,
                            content_text)

    blob1 = blobstore.get('item1')
    self.assertEquals('stuff.png', blob1.filename)

    self.assertEquals(None, blobstore.get('item2'))

  def test_store_and_build_forward_message_bad_mimes(self):
    """Test upload with no headers provided."""
    for unused_mime in range(len(BAD_MIMES)):
      # Should not require actual time value upon failure.
      self.now()

    self.mox.ReplayAll()

    for mime_type in BAD_MIMES:
      form = FakeForm({'field1': FakeForm(name='field1',
                                          file=StringIO.StringIO('file1'),
                                          type=mime_type,
                                          type_options={},
                                          filename='file',
                                          headers={}),
                      })

      self.assertRaisesRegexp(
          webob.exc.HTTPClientError,
          'Incorrectly formatted MIME type: %s' % mime_type,
          self.handler.store_and_build_forward_message,
          form,
          '================1234==')

    self.mox.VerifyAll()

  def test_store_and_build_forward_message_max_blob_size_exceeded(self):
    """Test upload with a blob larger than the maximum blob size."""
    self.generate_blob_key().AndReturn(blobstore.BlobKey('item1'))

    self.now().AndReturn(datetime.datetime(2008, 11, 12, 10, 40))

    self.mox.ReplayAll()

    form = FakeForm({
        'field1': FakeForm(name='field1',
                           file=StringIO.StringIO('a'),
                           type='image/png',
                           type_options={'a': 'b', 'x': 'y'},
                           filename='stuff.png',
                           headers={'h1': 'v1',
                                    'h2': 'v2',
                                   }),
        'field2': FakeForm(name='field2',
                           file=StringIO.StringIO('longerfile'),
                           type='application/pdf',
                           type_options={},
                           filename='stuff.pdf',
                           headers={}),
        })

    self.assertRaises(webob.exc.HTTPRequestEntityTooLarge,
                      self.handler.store_and_build_forward_message,
                      form, '================1234==', max_bytes_per_blob=2)

    self.mox.VerifyAll()

    blob1 = blobstore.get('item1')
    self.assertIsNone(blob1)

  def test_store_and_build_forward_message_total_size_exceeded(self):
    """Test upload with all blobs larger than the total allowed size."""
    self.generate_blob_key().AndReturn(blobstore.BlobKey('item1'))

    self.now().AndReturn(datetime.datetime(2008, 11, 12, 10, 40))

    self.mox.ReplayAll()

    form = FakeForm({
        'field1': FakeForm(name='field1',
                           file=StringIO.StringIO('a'),
                           type='image/png',
                           type_options={'a': 'b', 'x': 'y'},
                           filename='stuff.png',
                           headers={'h1': 'v1',
                                    'h2': 'v2',
                                   }),
        'field2': FakeForm(name='field2',
                           file=StringIO.StringIO('longerfile'),
                           type='application/pdf',
                           type_options={},
                           filename='stuff.pdf',
                           headers={}),
        })

    self.assertRaises(webob.exc.HTTPRequestEntityTooLarge,
                      self.handler.store_and_build_forward_message,
                      form, '================1234==', max_bytes_total=3)

    self.mox.VerifyAll()

    blob1 = blobstore.get('item1')
    self.assertIsNone(blob1)

  def test_store_blob_base64(self):
    """Test blob creation with a base-64-encoded body."""
    expected_result = 'This is the blob content.'
    self.execute_blob_test(base64.urlsafe_b64encode(expected_result),
                           expected_result,
                           base64_encoding=True)

  def test_filename_too_large(self):
    """Test that exception is raised if the filename is too large."""
    self.now().AndReturn(datetime.datetime(2008, 11, 12, 10, 40))
    self.mox.ReplayAll()

    filename = 'a' * blob_upload._MAX_STRING_NAME_LENGTH + '.txt'

    form = FakeForm({
        'field1': FakeForm(name='field1',
                           file=StringIO.StringIO('a'),
                           type='image/png',
                           type_options={'a': 'b', 'x': 'y'},
                           filename=filename,
                           headers={}),
        })

    self.assertRaisesRegexp(
        webob.exc.HTTPClientError,
        'The filename exceeds the maximum allowed length of 500.',
        self.handler.store_and_build_forward_message,
        form, '================1234==')

    self.mox.VerifyAll()

  def test_content_type_too_large(self):
    """Test that exception is raised if the content-type is too large."""
    self.now().AndReturn(datetime.datetime(2008, 11, 12, 10, 40))
    self.mox.ReplayAll()

    content_type = 'text/' + 'a' * blob_upload._MAX_STRING_NAME_LENGTH

    form = FakeForm({
        'field1': FakeForm(name='field1',
                           file=StringIO.StringIO('a'),
                           type=content_type,
                           type_options={'a': 'b', 'x': 'y'},
                           filename='foobar.txt',
                           headers={}),
        })

    self.assertRaisesRegexp(
        webob.exc.HTTPClientError,
        'The Content-Type exceeds the maximum allowed length of 500.',
        self.handler.store_and_build_forward_message,
        form, '================1234==')

    self.mox.VerifyAll()


class UploadHandlerUnitTestNamespace(UploadHandlerUnitTest):
  """Executes all of the superclass tests but with a namespace set."""

  def setUp(self):
    """Setup for namespaces test."""
    super(UploadHandlerUnitTestNamespace, self).setUp()
    # Set the namespace. Blobstore should ignore this.
    namespace_manager.set_namespace('abc')


class UploadHandlerWSGITest(UploadTestBase):
  """Test the upload handler as a whole, by making WSGI requests."""

  def setUp(self):
    """Set up test framework."""
    # Set up environment for Blobstore.
    self.original_environ = dict(os.environ)
    os.environ.update({
        'APPLICATION_ID': 'app',
        'USER_EMAIL': 'nobody@nowhere.com',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8080',
        })
    self.environ = {}
    wsgiref.util.setup_testing_defaults(self.environ)
    self.environ['REQUEST_METHOD'] = 'POST'

    # Set up user stub.
    self.user_stub = user_service_stub.UserServiceStub()

    self.tmpdir = tempfile.mkdtemp()

    ## Set up testing blobstore files.
    storage_directory = os.path.join(self.tmpdir, 'blobstore')
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
    apiproxy_stub_map.apiproxy.RegisterStub('user', self.user_stub)

    # Keep values given to forward_app.
    self.forward_request_dict = {}

    def forward_app(environ, start_response):
      self.forward_request_dict['environ'] = environ
      self.forward_request_dict['body'] = environ['wsgi.input'].read()
      # Return a dummy body
      start_response('200 OK', [('CONTENT_TYPE', 'text/plain')])
      return ['Forwarded successfully.']

    self.dispatcher = blob_upload.Application(forward_app)

  def tearDown(self):
    os.environ = self.original_environ
    shutil.rmtree(self.tmpdir)

  def run_dispatcher(self, request_body=''):
    """Runs self.dispatcher and returns the response.

    self.environ should already be initialised with the WSGI environment,
    including the HTTP_* headers.

    Args:
      request_body: String containing the body of the request.

    Returns:
      (status, headers, response_body, forward_environ, forward_body), where:
        status is the response status string,
        headers is a dict containing the response headers (with lowercase
          names),
        response_body is a string containing the response body,
        forward_environ is the WSGI environ passed to the forwarded request, or
          None if the forward application was not called,
        forward_body is the request body passed to the forwarded request, or
          None if the forward application was not called.

    Raises:
      AssertionError: start_response was not called.
      Exception: The WSGI application returned an exception.
    """

    response_dict = {}
    state_dict = {
        'start_response_already_called': False,
        'headers_already_sent': False,
    }

    self.environ['wsgi.input'] = cStringIO.StringIO(request_body)

    body = cStringIO.StringIO()

    def write_body(text):
      if not text:
        return
      assert state_dict['start_response_already_called']
      body.write(text)
      state_dict['headers_already_sent'] = True

    def start_response(status, response_headers, exc_info=None):
      if exc_info is None:
        assert not state_dict['start_response_already_called']
      if state_dict['headers_already_sent']:
        raise exc_info[0], exc_info[1], exc_info[2]
      state_dict['start_response_already_called'] = True
      response_dict['status'] = status
      response_dict['headers'] = dict((k.lower(), v) for (k, v) in
                                      response_headers)
      return write_body

    self.forward_request_dict['environ'] = None
    self.forward_request_dict['body'] = None

    for s in self.dispatcher(self.environ, start_response):
      write_body(s)

    if 'status' not in response_dict:
      self.fail('start_response was not called')

    return (response_dict['status'], response_dict['headers'], body.getvalue(),
            self.forward_request_dict['environ'],
            self.forward_request_dict['body'])

  def _run_test_success(self, upload_data, upload_url):
    """Basic dispatcher request flow."""
    request_path = urlparse.urlparse(upload_url)[2]

    # Get session key from upload url.
    session_key = upload_url.split('/')[-1]

    self.environ['PATH_INFO'] = request_path
    self.environ['CONTENT_TYPE'] = (
        'multipart/form-data; boundary="================1234=="')
    status, _, response_body, forward_environ, forward_body = (
        self.run_dispatcher(upload_data))

    self.assertEquals('200 OK', status)
    self.assertEquals('Forwarded successfully.', response_body)

    self.assertNotEquals(None, forward_environ)

    # These must NOT be unicode strings.
    self.assertIsInstance(forward_environ['PATH_INFO'], str)
    if 'QUERY_STRING' in forward_environ:
      self.assertIsInstance(forward_environ['QUERY_STRING'], str)
    self.assertRegexpMatches(forward_environ['CONTENT_TYPE'],
                             r'multipart/form-data; boundary="[^"]+"')
    self.assertEquals(len(forward_body), int(forward_environ['CONTENT_LENGTH']))
    self.assertIn(constants.FAKE_IS_ADMIN_HEADER, forward_environ)
    self.assertEquals('1', forward_environ[constants.FAKE_IS_ADMIN_HEADER])

    new_request = email.message_from_string(
        'Content-Type: %s\n\n%s' % (forward_environ['CONTENT_TYPE'],
                                    forward_body))
    (upload,) = new_request.get_payload()
    self.assertEquals('message/external-body', upload.get_content_type())

    message = email.message.Message()
    message.add_header('Content-Type', upload['Content-Type'])
    blob_key = message.get_param('blob-key')
    blob_contents = blobstore.BlobReader(blob_key).read()
    self.assertEquals('value', blob_contents)

    self.assertRaises(datastore_errors.EntityNotFoundError,
                      datastore.Get,
                      session_key)

    return upload, forward_environ, forward_body

  def test_success(self):
    """Basic dispatcher request flow."""
    # Create upload.
    upload_data = (
        """--================1234==
Content-Type: text/plain
MIME-Version: 1.0
Content-Disposition: form-data; name="field1"; filename="stuff.txt"

value
--================1234==--""")

    upload_url = blobstore.create_upload_url('/success?foo=bar')

    upload, forward_environ, _ = self._run_test_success(
        upload_data, upload_url)

    self.assertEquals('/success', forward_environ['PATH_INFO'])
    self.assertEquals('foo=bar', forward_environ['QUERY_STRING'])
    self.assertEquals(
        ('form-data', {'filename': 'stuff.txt', 'name': 'field1'}),
        cgi.parse_header(upload['content-disposition']))

  def test_success_with_bucket(self):
    """Basic dispatcher request flow."""
    # Create upload.
    upload_data = (
        """--================1234==
Content-Type: text/plain
MIME-Version: 1.0
Content-Disposition: form-data; name="field1"; filename="stuff.txt"

value
--================1234==--""")

    upload_url = blobstore.create_upload_url('/success?foo=bar',
                                             gs_bucket_name='my_test_bucket')

    upload, forward_environ, forward_body = self._run_test_success(
        upload_data, upload_url)

    self.assertEquals('/success', forward_environ['PATH_INFO'])
    self.assertEquals('foo=bar', forward_environ['QUERY_STRING'])
    self.assertEquals(
        ('form-data', {'filename': 'stuff.txt', 'name': 'field1'}),
        cgi.parse_header(upload['content-disposition']))
    self.assertIn('X-AppEngine-Cloud-Storage-Object: /gs/%s' % 'my_test_bucket',
                  forward_body)

  def test_success_full_success_url(self):
    """Request flow with a success url containing protocol, host and port."""
    # Create upload.
    upload_data = (
        """--================1234==
Content-Type: text/plain
MIME-Version: 1.0
Content-Disposition: form-data; name="field1"; filename="stuff.txt"

value
--================1234==--""")

    # The scheme, host and port should all be ignored.
    upload_url = blobstore.create_upload_url(
        'https://example.com:1234/success?foo=bar')

    upload, forward_environ, _ = self._run_test_success(
        upload_data, upload_url)

    self.assertEquals('/success', forward_environ['PATH_INFO'])
    self.assertEquals('foo=bar', forward_environ['QUERY_STRING'])
    self.assertEquals(
        ('form-data', {'filename': 'stuff.txt', 'name': 'field1'}),
        cgi.parse_header(upload['content-disposition']))

  def test_base64(self):
    """Test automatic decoding of a base-64-encoded message."""
    # Create upload.
    upload_data = (
        """--================1234==
Content-Type: text/plain
MIME-Version: 1.0
Content-Disposition: form-data; name="field1"; filename="stuff.txt"
Content-Transfer-Encoding: base64

%s
--================1234==--""" % base64.urlsafe_b64encode('value'))

    upload_url = blobstore.create_upload_url('/success')

    upload, forward_environ, _ = self._run_test_success(
        upload_data, upload_url)

    self.assertEquals('/success', forward_environ['PATH_INFO'])
    self.assertEquals(
        ('form-data', {'filename': 'stuff.txt', 'name': 'field1'}),
        cgi.parse_header(upload['content-disposition']))

  def test_wrong_method(self):
    """Using the wrong HTTP method on upload dispatcher causes an error."""
    self.environ['REQUEST_METHOD'] = 'GET'

    status, _, _, forward_environ, forward_body = self.run_dispatcher()

    self.assertEquals('405 Method Not Allowed', status)
    # Test that it did not forward.
    self.assertEquals(None, forward_environ)
    self.assertEquals(None, forward_body)

  def test_bad_session(self):
    """Using a non-existant upload session causes an error."""
    upload_url = blobstore.create_upload_url('/success')

    # Get session key from upload url.
    session_key = upload_url.split('/')[-1]
    datastore.Delete(session_key)

    request_path = urlparse.urlparse(upload_url)[2]
    self.environ['PATH_INFO'] = request_path
    status, _, response_body, forward_environ, forward_body = (
        self.run_dispatcher())

    self.assertEquals('404 Not Found', status)
    self.assertIn('No such upload session: %s' % session_key, response_body)
    # Test that it did not forward.
    self.assertEquals(None, forward_environ)
    self.assertEquals(None, forward_body)

  def test_bad_mime_format(self):
    """Using a bad mime type format causes an error."""
    # Create upload.
    upload_data = (
        """--================1234==
Content-Type: text/plain/error
MIME-Version: 1.0
Content-Disposition: form-data; name="field1"; filename="stuff.txt"

value
--================1234==--""")

    upload_url = blobstore.create_upload_url('/success')

    request_path = urlparse.urlparse(upload_url)[2]
    self.environ['PATH_INFO'] = request_path
    self.environ['CONTENT_TYPE'] = (
        'multipart/form-data; boundary="================1234=="')

    status, _, response_body, forward_environ, forward_body = (
        self.run_dispatcher(upload_data))

    self.assertEquals('400 Bad Request', status)
    self.assertIn('Incorrectly formatted MIME type: text/plain/error',
                  response_body)
    # Test that it did not forward.
    self.assertEquals(None, forward_environ)
    self.assertEquals(None, forward_body)

  def test_check_line_endings(self):
    """Ensure the upload message uses correct RFC-2821 line terminators."""
    # Create upload.
    upload_data = (
        """--================1234==
Content-Type: text/plain
MIME-Version: 1.0
Content-Disposition: form-data; name="field1"; filename="stuff.txt"

value
--================1234==--""")

    upload_url = blobstore.create_upload_url('/success')

    request_path = urlparse.urlparse(upload_url)[2]
    self.environ['PATH_INFO'] = request_path
    self.environ['CONTENT_TYPE'] = (
        'multipart/form-data; boundary="================1234=="')

    status, _, _, _, forward_body = self.run_dispatcher(upload_data)

    self.assertEquals('200 OK', status)
    forward_body = forward_body.replace('\r\n', '')
    self.assertEqual(forward_body.rfind('\n'), -1)

  def test_copy_headers(self):
    """Tests that headers are copied, except for ones that should not be."""
    # Create upload.
    upload_data = (
        """--================1234==
Content-Type: text/plain
MIME-Version: 1.0
Content-Disposition: form-data; name="field1"; filename="stuff.txt"

value
--================1234==--""")

    upload_url = blobstore.create_upload_url('/success')

    request_path = urlparse.urlparse(upload_url)[2]
    self.environ['PATH_INFO'] = request_path
    self.environ['CONTENT_TYPE'] = (
        'multipart/form-data; boundary="================1234=="')
    self.environ['HTTP_PLEASE_COPY_ME'] = 'I get copied'
    self.environ['HTTP_CONTENT_TYPE'] = 'I should not be copied'
    self.environ['HTTP_CONTENT_LENGTH'] = 'I should not be copied'
    self.environ['HTTP_CONTENT_MD5'] = 'I should not be copied'

    status, _, response_body, forward_environ, forward_body = (
        self.run_dispatcher(upload_data))

    self.assertEquals('200 OK', status)
    self.assertEquals('Forwarded successfully.', response_body)
    self.assertIn('HTTP_PLEASE_COPY_ME', forward_environ)
    self.assertEquals('I get copied', forward_environ['HTTP_PLEASE_COPY_ME'])
    self.assertNotIn('HTTP_CONTENT_TYPE', forward_environ)
    self.assertNotIn('HTTP_CONTENT_LENGTH', forward_environ)
    self.assertNotIn('HTTP_CONTENT_MD5', forward_environ)
    # These ones should have been modified.
    self.assertIn('CONTENT_TYPE', forward_environ)
    self.assertNotEquals(
        'multipart/form-data; boundary="================1234=="',
        forward_environ['CONTENT_TYPE'])
    self.assertIn('CONTENT_LENGTH', forward_environ)
    self.assertEquals(str(len(forward_body)), forward_environ['CONTENT_LENGTH'])

  def test_entity_too_large(self):
    """Ensure a 413 response is generated when upload size limit exceeded."""
    # Create upload.
    upload_data = (
        """--================1234==
Content-Type: text/plain
MIME-Version: 1.0
Content-Disposition: form-data; name="field1"; filename="stuff.txt"

Lots and Lots of Stuff
--================1234==--""")

    upload_url = blobstore.create_upload_url('/success1', max_bytes_per_blob=1)

    request_path = urlparse.urlparse(upload_url)[2]
    self.environ['PATH_INFO'] = request_path
    self.environ['CONTENT_TYPE'] = (
        'multipart/form-data; boundary="================1234=="')

    status, _, _, forward_environ, forward_body = (
        self.run_dispatcher(upload_data))

    self.assertEquals('413 Request Entity Too Large', status)
    # Test that it did not forward.
    self.assertEquals(None, forward_environ)
    self.assertEquals(None, forward_body)

  def test_filename_too_long(self):
    """Ensure a 400 response is generated when filename size limit exceeded."""
    filename = 'a' * 500 + '.txt'
    # Create upload.
    upload_data = (
        """Content-Type: multipart/form-data; boundary="================1234=="

--================1234==
Content-Type: text/plain
MIME-Version: 1.0
Content-Disposition: form-data; name="field1"; filename="%s"

Lots and Lots of Stuff
--================1234==--""" % filename)

    upload_url = blobstore.create_upload_url('/success1')

    request_path = urlparse.urlparse(upload_url)[2]
    self.environ['PATH_INFO'] = request_path
    self.environ['CONTENT_TYPE'] = (
        'multipart/form-data; boundary="================1234=="')

    status, _, response_body, forward_environ, forward_body = (
        self.run_dispatcher(upload_data))

    self.assertEquals('400 Bad Request', status)
    self.assertIn('The filename exceeds the maximum allowed length of 500.',
                  response_body)
    # Test that it did not forward.
    self.assertEquals(None, forward_environ)
    self.assertEquals(None, forward_body)

  def test_content_type_too_long(self):
    """Ensure a 400 response when content-type size limit exceeded."""
    content_type = 'text/' + 'a' * 500
    # Create upload.
    upload_data = (
        """Content-Type: multipart/form-data; boundary="================1234=="

--================1234==
Content-Type: %s
MIME-Version: 1.0
Content-Disposition: form-data; name="field1"; filename="stuff.txt"

Lots and Lots of Stuff
--================1234==--""" % content_type)

    upload_url = blobstore.create_upload_url('/success1')

    request_path = urlparse.urlparse(upload_url)[2]
    self.environ['PATH_INFO'] = request_path
    self.environ['CONTENT_TYPE'] = (
        'multipart/form-data; boundary="================1234=="')

    status, _, response_body, forward_environ, forward_body = (
        self.run_dispatcher(upload_data))

    self.assertEquals('400 Bad Request', status)
    self.assertIn('The Content-Type exceeds the maximum allowed length of 500.',
                  response_body)
    # Test that it did not forward.
    self.assertEquals(None, forward_environ)
    self.assertEquals(None, forward_body)

  def test_raise_uncaught_http_error(self):
    """Ensure that an uncaught HTTPError is not inadvertently caught."""

    def forward_app(unused_environ, unused_start_response):
      # Simulate raising a webob.exc.HTTPError in a user's application.
      # This should not be caught by our wrapper.
      raise webob.exc.HTTPLengthRequired()

    self.dispatcher = blob_upload.Application(forward_app)

    upload_url = blobstore.create_upload_url('/success')
    request_path = urlparse.urlparse(upload_url)[2]
    self.environ['PATH_INFO'] = request_path

    self.assertRaises(webob.exc.HTTPLengthRequired,
                      self.run_dispatcher)


if __name__ == '__main__':
  unittest.main()
