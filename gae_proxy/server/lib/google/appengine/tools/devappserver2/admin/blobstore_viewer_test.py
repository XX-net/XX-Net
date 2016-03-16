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
"""Tests for devappserver2.admin.blobstore_viewer."""

import unittest

import google
import mox
import webapp2
from webob import multidict

from google.appengine.ext import blobstore
from google.appengine.ext import db

from google.appengine.tools.devappserver2.admin import admin_request_handler
from google.appengine.tools.devappserver2.admin import blobstore_viewer


BLOBS_PER_PAGE = blobstore_viewer.BlobstoreRequestHandler.BLOBS_PER_PAGE


class GetBlobsTest(unittest.TestCase):
  """Tests blobstore_viewer._get_blobs."""

  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutClassWithMocks(db, 'Query')

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_get_blobs(self):
    query = db.Query(
        model_class=blobstore.BlobInfo, namespace='')
    query.order('-creation').AndReturn(query)
    query.fetch(10, offset=40).AndReturn(['some blob'])

    self.mox.ReplayAll()
    self.assertEqual(['some blob'], blobstore_viewer._get_blobs(start=40,
                                                                limit=10))
    self.mox.VerifyAll()


class BlobstoreRequestHandlerTest(unittest.TestCase):
  """Tests blobstore_viewer.BlobstoreRequestHandler."""

  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(
        admin_request_handler.AdminRequestHandler, 'render')
    self.mox.StubOutWithMock(blobstore_viewer, '_get_blobs')

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_get_no_offset(self):
    request = webapp2.Request.blank('/blobstore')
    response = webapp2.Response()
    handler = blobstore_viewer.BlobstoreRequestHandler(request, response)

    blob_infos = [object() for _ in range(10)]
    blobstore_viewer._get_blobs(0, BLOBS_PER_PAGE+1).AndReturn(blob_infos)
    handler.render('blobstore_viewer.html',
                   {'previous': None,
                    'next': None,
                    'blob_infos': blob_infos,
                    'offset': 0,
                    'return_to': 'http://localhost/blobstore',
                   })

    self.mox.ReplayAll()
    handler.get()
    self.mox.VerifyAll()

  def test_get_with_offset(self):
    request = webapp2.Request.blank('/blobstore?offset=40')
    response = webapp2.Response()
    handler = blobstore_viewer.BlobstoreRequestHandler(request, response)

    blob_infos = [object() for _ in range(10)]
    blobstore_viewer._get_blobs(40, BLOBS_PER_PAGE+1).AndReturn(blob_infos)
    handler.render('blobstore_viewer.html',
                   {'previous': 20,
                    'next': None,
                    'blob_infos': blob_infos,
                    'offset': 40,
                    'return_to': 'http://localhost/blobstore?offset=40',
                   })

    self.mox.ReplayAll()
    handler.get()
    self.mox.VerifyAll()

  def test_get_with_data_in_next_page(self):
    request = webapp2.Request.blank('/blobstore')
    response = webapp2.Response()
    handler = blobstore_viewer.BlobstoreRequestHandler(request, response)

    blob_infos = [object() for _ in range(BLOBS_PER_PAGE+1)]
    blobstore_viewer._get_blobs(0, BLOBS_PER_PAGE+1).AndReturn(blob_infos)
    handler.render('blobstore_viewer.html',
                   {'previous': None,
                    'next': 20,
                    'blob_infos': blob_infos[:BLOBS_PER_PAGE],
                    'offset': 0,
                    'return_to': 'http://localhost/blobstore',
                   })

    self.mox.ReplayAll()
    handler.get()
    self.mox.VerifyAll()

  def test_post(self):
    request = webapp2.Request.blank(
        '/blobstore',
        method='POST',
        POST=multidict.MultiDict([('blob_key', 'a'),
                                  ('blob_key', 'b')]))
    response = webapp2.Response()
    handler = blobstore_viewer.BlobstoreRequestHandler(request, response)

    self.mox.StubOutWithMock(blobstore, 'delete')
    blobstore.delete(['a', 'b'])

    self.mox.ReplayAll()
    handler.post()
    self.mox.VerifyAll()
    self.assertEqual(302, response.status_int)
    self.assertEqual('http://localhost/blobstore',
                     response.headers.get('Location'))


class BlobRequestHandlerTest(unittest.TestCase):
  """Tests blobstore_viewer.BlobRequestHandler."""

  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(
        admin_request_handler.AdminRequestHandler, 'render')
    self.mox.StubOutWithMock(blobstore.BlobInfo, 'get')

  def tearDown(self):
    self.mox.UnsetStubs()

  def test_blob_does_not_exist(self):
    request = webapp2.Request.blank('/blobstore/blob/non-existent')
    response = webapp2.Response()
    handler = blobstore_viewer.BlobRequestHandler(request, response)

    blobstore.BlobInfo.get('non-existent').AndReturn(None)

    self.mox.ReplayAll()
    handler.get('non-existent')
    self.mox.VerifyAll()
    self.assertEqual(302, response.status_int)
    self.assertEqual('http://localhost/blobstore',
                     response.headers.get('Location'))

  def test_display_blob_info_inlineable(self):
    request = webapp2.Request.blank('/blobstore/blob/blobkey')
    response = webapp2.Response()
    handler = blobstore_viewer.BlobRequestHandler(request, response)

    blob = self.mox.CreateMock(blobstore.BlobInfo)
    blob.content_type = 'image/png'

    blobstore.BlobInfo.get('blobkey').AndReturn(blob)
    handler.render('blob_viewer.html',
                   {'blob_info': blob,
                    'delete_uri': '/blobstore',
                    'download_uri': request.path + '?display=attachment',
                    'inline_uri': request.path + '?display=inline',
                    'inlineable': True,
                    'return_to': '/blobstore'
                   })

    self.mox.ReplayAll()
    handler.get('blobkey')
    self.mox.VerifyAll()

  def test_display_blob_info_non_inlineable(self):
    request = webapp2.Request.blank('/blobstore/blob/blobkey')
    response = webapp2.Response()
    handler = blobstore_viewer.BlobRequestHandler(request, response)

    blob = self.mox.CreateMock(blobstore.BlobInfo)
    blob.content_type = 'application/octet-stream'

    blobstore.BlobInfo.get('blobkey').AndReturn(blob)
    handler.render('blob_viewer.html',
                   {'blob_info': blob,
                    'delete_uri': '/blobstore',
                    'download_uri': request.path + '?display=attachment',
                    'inline_uri': request.path + '?display=inline',
                    'inlineable': False,
                    'return_to': '/blobstore'
                   })

    self.mox.ReplayAll()
    handler.get('blobkey')
    self.mox.VerifyAll()

  def test_display_blob_inline(self):
    request = webapp2.Request.blank('/blob/blobkey?display=inline')
    response = webapp2.Response()
    handler = blobstore_viewer.BlobRequestHandler(request, response)

    blob_info = self.mox.CreateMock(blobstore.BlobInfo)
    blob_info.content_type = 'image/jpeg'
    blobstore.BlobInfo.get('blobkey').AndReturn(blob_info)
    reader = self.mox.CreateMockAnything()
    blob_info.open().AndReturn(reader)
    reader.read().AndReturn('blob bytes')
    reader.close()

    self.mox.ReplayAll()
    handler.get('blobkey')
    self.mox.VerifyAll()

    self.assertEqual('image/jpeg', response.headers.get('Content-Type'))
    self.assertEqual('inline', response.headers.get('Content-Disposition'))
    self.assertEqual('blob bytes', response.body)

  def test_display_blob_inline_and_binary(self):
    request = webapp2.Request.blank('/blob/blobkey?display=inline')
    response = webapp2.Response()
    handler = blobstore_viewer.BlobRequestHandler(request, response)

    blob_info = self.mox.CreateMock(blobstore.BlobInfo)
    blob_info.content_type = 'application/octet-stream'
    blobstore.BlobInfo.get('blobkey').AndReturn(blob_info)
    reader = self.mox.CreateMockAnything()
    blob_info.open().AndReturn(reader)
    reader.read().AndReturn('blob bytes')
    reader.close()

    self.mox.ReplayAll()
    handler.get('blobkey')
    self.mox.VerifyAll()

    self.assertEqual('text/plain', response.headers.get('Content-Type'))
    self.assertEqual('inline', response.headers.get('Content-Disposition'))
    self.assertEqual('blob bytes', response.body)

  def test_display_blob_attachment(self):
    request = webapp2.Request.blank('/blob/blobkey?display=attachment')
    response = webapp2.Response()
    handler = blobstore_viewer.BlobRequestHandler(request, response)

    blob_info = self.mox.CreateMock(blobstore.BlobInfo)
    blob_info.content_type = 'image/png'
    blob_info.filename = 'profile.png'
    blobstore.BlobInfo.get('blobkey').AndReturn(blob_info)
    reader = self.mox.CreateMockAnything()
    blob_info.open().AndReturn(reader)
    reader.read().AndReturn('blob bytes')
    reader.close()

    self.mox.ReplayAll()
    handler.get('blobkey')
    self.mox.VerifyAll()

    self.assertEqual('image/png', response.headers.get('Content-Type'))
    self.assertEqual('attachment; filename=profile.png',
                     response.headers.get('Content-Disposition'))
    self.assertEqual('blob bytes', response.body)


if __name__ == '__main__':
  unittest.main()
