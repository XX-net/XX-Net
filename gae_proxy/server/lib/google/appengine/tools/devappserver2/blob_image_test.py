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
"""Tests for google.appengine.tools.devappserver2.blob_image."""

import httplib
import os
import unittest

import google
import mox

from google.appengine.api import datastore
from google.appengine.api import datastore_errors
from google.appengine.api.images import images_service_pb
from google.appengine.api.images import images_stub
from google.appengine.ext import blobstore
from google.appengine.runtime import apiproxy_errors
from google.appengine.tools.devappserver2 import blob_download
from google.appengine.tools.devappserver2 import blob_image
from google.appengine.tools.devappserver2 import wsgi_test_utils


class MockImage(object):
  """A mock PIL Image object."""

  def __init__(self):
    self.format = None
    self.size = None


class BlobImageTest(wsgi_test_utils.WSGITestCase):
  """Tests image url handler."""

  def setUp(self):
    self.mox = mox.Mox()
    self._environ = {'PATH_INFO': 'http://test.com/_ah/img/SomeBlobKey',
                     'REQUEST_METHOD': 'GET'}
    self._has_working_images_stub = blob_image._HAS_WORKING_IMAGES_STUB
    blob_image._HAS_WORKING_IMAGES_STUB = True
    self._images_stub = self.mox.CreateMock(images_stub.ImagesServiceStub)
    self._mock_rewriter = self.mox.CreateMockAnything()
    self._image = MockImage()
    self.app = blob_image.Application()
    os.environ['APPLICATION_ID'] = 'testapp'
    self._get_images_stub = blob_image._get_images_stub
    blob_image._get_images_stub = lambda: self._images_stub
    self._blobstore_rewriter = blob_download.blobstore_download_rewriter
    blob_download.blobstore_download_rewriter = self._mock_rewriter

  def tearDown(self):
    blob_image._HAS_WORKING_IMAGES_STUB = self._has_working_images_stub
    blob_image._get_images_stub = self._get_images_stub
    blob_download.blobstore_download_rewriter = self._blobstore_rewriter
    self.mox.UnsetStubs()

  def expect_open_image(self, blob_key, dimensions=None, throw_exception=None,
                        mime_type='JPEG'):
    """Setup a mox expectation to images_stub._OpenImageData."""
    image_data = images_service_pb.ImageData()
    image_data.set_blob_key(blob_key)
    self._image.format = mime_type
    if throw_exception:
      self._images_stub._OpenImageData(image_data).AndRaise(throw_exception)
    else:
      self._images_stub._OpenImageData(image_data).AndReturn(self._image)
      self._image.size = dimensions

  def expect_crop(self, left_x=None, right_x=None, top_y=None, bottom_y=None):
    """Setup a mox expectation to images_stub._Crop."""
    crop_xform = images_service_pb.Transform()
    if left_x is not None:
      if not isinstance(left_x, float):
        raise self.failureException('Crop argument must be a float.')
      crop_xform.set_crop_left_x(left_x)
    if right_x is not None:
      if not isinstance(right_x, float):
        raise self.failureException('Crop argument must be a float.')
      crop_xform.set_crop_right_x(right_x)
    if top_y is not None:
      if not isinstance(top_y, float):
        raise self.failureException('Crop argument must be a float.')
      crop_xform.set_crop_top_y(top_y)
    if bottom_y is not None:
      if not isinstance(bottom_y, float):
        raise self.failureException('Crop argument must be a float.')
      crop_xform.set_crop_bottom_y(bottom_y)
    self._images_stub._Crop(mox.IsA(MockImage), crop_xform).AndReturn(
        self._image)

  def expect_resize(self, resize):
    """Setup a mox expectation to images_stub._Resize."""
    resize_xform = images_service_pb.Transform()
    resize_xform.set_width(resize)
    resize_xform.set_height(resize)
    self._images_stub._Resize(mox.IsA(MockImage),
                              resize_xform).AndReturn(self._image)

  def expect_encode_image(self, data,
                          mime_type=images_service_pb.OutputSettings.JPEG):
    """Setup a mox expectation to images_stub._EncodeImage."""
    output_settings = images_service_pb.OutputSettings()
    output_settings.set_mime_type(mime_type)
    self._images_stub._EncodeImage(mox.IsA(MockImage),
                                   output_settings).AndReturn(data)

  def expect_datatore_lookup(self, blob_key, expected_result):
    """Setup a mox expectation to datastore.Get."""
    self.mox.StubOutWithMock(datastore, 'Get')
    blob_url = datastore.Entity('__BlobServingUrl__',
                                name=blob_key)
    if expected_result:
      datastore.Get(blob_url.key()).AndReturn(True)
    else:
      datastore.Get(blob_url.key()).AndRaise(
          datastore_errors.EntityNotFoundError)

  def run_request(self, expected_mimetype, expected_content):
    self.mox.ReplayAll()
    self.assertResponse(
        '200 OK',
        [('Content-Type', expected_mimetype),
         ('Cache-Control', 'public, max-age=600, no-transform')],
        expected_content,
        self.app,
        self._environ)
    self.mox.VerifyAll()

  def run_blobstore_serving_request(self, blobkey):
    def _Validate(state):
      return state.headers.get(blobstore.BLOB_KEY_HEADER) == blobkey

    def _Rewrite(state):
      del state.headers[blobstore.BLOB_KEY_HEADER]
      state.headers['Content-Type'] = 'image/some-type'
      state.body = ['SomeBlobImage']

    self._mock_rewriter.__call__(mox.Func(_Validate)).WithSideEffects(_Rewrite)

    self.mox.ReplayAll()
    self.assertResponse(
        '200 OK',
        [('Content-Type', 'image/some-type')],
        'SomeBlobImage',
        self.app,
        self._environ)
    self.mox.VerifyAll()

  def test_parse_path(self):
    """Tests URL parsing."""
    self.assertEquals(('SomeBlobKey', ''),
                      self.app._parse_path(
                          'http://test.com/_ah/img/SomeBlobKey'))
    self.assertEquals(('SomeBlobKey', ''),
                      self.app._parse_path('/_ah/img/SomeBlobKey'))
    self.assertEquals(('SomeBlobKey', 's32'),
                      self.app._parse_path('/_ah/img/SomeBlobKey=s32'))
    self.assertEquals(('SomeBlobKey', 's32-c'),
                      self.app._parse_path('/_ah/img/SomeBlobKey=s32-c'))
    self.assertEquals(('foo', 's32-c'),
                      self.app._parse_path('/_ah/img/foo=s32-c'))
    # Google Storage keys have the format encoded_gs_file:key
    self.assertEquals(('encoded_gs_file:someblobkey', 's32-c'),
                      self.app._parse_path(
                          '/_ah/img/encoded_gs_file:someblobkey=s32-c'))
    # Dev blobkeys are padded with '='.
    self.assertEquals(('foo====', ''),
                      self.app._parse_path('/_ah/img/foo===='))
    self.assertEquals(('foo=', 's32-c'),
                      self.app._parse_path('/_ah/img/foo==s32-c'))
    self.assertEquals(('foo==', 's32-c'),
                      self.app._parse_path('/_ah/img/foo===s32-c'))
    self.assertRaises(blob_image.InvalidRequestError,
                      self.app._parse_path, 'SomeBlobKey')
    self.assertRaises(blob_image.InvalidRequestError,
                      self.app._parse_path, '/_ah/img')
    self.assertRaises(blob_image.InvalidRequestError,
                      self.app._parse_path, '/_ah/img/')

  def test_parse_options(self):
    """Tests Option parsing."""
    self.assertEquals((32, False), self.app._parse_options('s32'))
    self.assertEquals((32, True), self.app._parse_options('s32-c'))
    self.assertEquals((None, False), self.app._parse_options(''))
    self.assertEquals((None, False), self.app._parse_options('c-s32'))
    self.assertEquals((None, False), self.app._parse_options('s-c'))
    self.assertEquals((123, False), self.app._parse_options('s123'))
    self.assertEquals((512, True), self.app._parse_options('s512-c'))
    self.assertEquals((None, False), self.app._parse_options('s-100'))
    self.assertRaises(blob_image.InvalidRequestError,
                      self.app._parse_options, 's1601')
    self.assertRaises(blob_image.InvalidRequestError,
                      self.app._parse_options, 's1601-c')

  def test_open_image_throws(self):
    """Tests OpenImage raises an exception."""
    self.expect_open_image(
        'SomeBlobKey',
        throw_exception=apiproxy_errors.ApplicationError(
            images_service_pb.ImagesServiceError.INVALID_BLOB_KEY))
    self.mox.ReplayAll()
    try:
      self.app._transform_image('SomeBlobKey')
      raise self.failureException('Should have thrown ApplicationError')
    except apiproxy_errors.ApplicationError:
      pass
    self.mox.VerifyAll()

  def test_transform_image_no_resize(self):
    """Tests no resizing."""
    self.expect_open_image('SomeBlobKey', (1600, 1200))
    self.expect_resize(blob_image._DEFAULT_SERVING_SIZE)
    self.expect_encode_image('SomeImageInJpeg')
    self.mox.ReplayAll()
    self.assertEquals(('SomeImageInJpeg', 'image/jpeg'),
                      self.app._transform_image('SomeBlobKey'))
    self.mox.VerifyAll()

  def test_transform_image_not_upscaled(self):
    """Tests that an image smaller than default serving size is not upsized."""
    self.expect_open_image('SomeBlobKey', (400, 300))
    self.expect_encode_image('SomeImageInJpeg')
    self.mox.ReplayAll()
    self.assertEquals(('SomeImageInJpeg', 'image/jpeg'),
                      self.app._transform_image('SomeBlobKey'))
    self.mox.VerifyAll()

  def test_transform_image_no_resize_png(self):
    """Tests no resizing in PNG."""
    self.expect_open_image('SomeBlobKey', (1600, 1200), mime_type='PNG')
    self.expect_resize(blob_image._DEFAULT_SERVING_SIZE)
    self.expect_encode_image('SomeImageInPng',
                             images_service_pb.OutputSettings.PNG)
    self.mox.ReplayAll()
    self.assertEquals(('SomeImageInPng', 'image/png'),
                      self.app._transform_image('SomeBlobKey'))
    self.mox.VerifyAll()

  def test_transform_image_no_resize_tiff(self):
    """Tests no resizing in TIFF."""
    self.expect_open_image('SomeBlobKey', (1600, 1200), mime_type='TIFF')
    self.expect_resize(blob_image._DEFAULT_SERVING_SIZE)
    # TIFF is not servable, so we transcode to JPEG.
    self.expect_encode_image('SomeImageInJpeg')
    self.mox.ReplayAll()
    self.assertEquals(('SomeImageInJpeg', 'image/jpeg'),
                      self.app._transform_image('SomeBlobKey'))
    self.mox.VerifyAll()

  def test_transform_image_no_resize_gif(self):
    """Tests no resizing in GIF."""
    self.expect_open_image('SomeBlobKey', (1600, 1200), mime_type='GIF')
    self.expect_resize(blob_image._DEFAULT_SERVING_SIZE)
    # ImageService only supports PNG/JPEG encoding, so we transcode to PNG.
    self.expect_encode_image('SomeImageInPng',
                             images_service_pb.OutputSettings.PNG)
    self.mox.ReplayAll()
    self.assertEquals(('SomeImageInPng', 'image/png'),
                      self.app._transform_image('SomeBlobKey'))
    self.mox.VerifyAll()

  def test_transform_image_resize(self):
    """Tests resizing."""
    self.expect_open_image('SomeBlobKey', (1600, 1200))
    self.expect_resize(32)
    self.expect_encode_image('SomeImageSize32')
    self.mox.ReplayAll()
    self.assertEquals(('SomeImageSize32', 'image/jpeg'),
                      self.app._transform_image('SomeBlobKey', 32))
    self.mox.VerifyAll()

  def test_transform_image_original_size(self):
    """Tests that s0 parameter serves image at the original size."""
    self.expect_open_image('SomeBlobKey', (1600, 1200))
    self.expect_encode_image('SomeImageInJpeg')
    self.mox.ReplayAll()
    self.assertEquals(('SomeImageInJpeg', 'image/jpeg'),
                      self.app._transform_image('SomeBlobKey', 0))
    self.mox.VerifyAll()

  def test_transform_image_resize_png(self):
    """Tests resizing."""
    self.expect_open_image('SomeBlobKey', (1600, 1200), mime_type='PNG')
    self.expect_resize(32)
    self.expect_encode_image('SomeImageSize32',
                             images_service_pb.OutputSettings.PNG)
    self.mox.ReplayAll()
    self.assertEquals(('SomeImageSize32', 'image/png'),
                      self.app._transform_image('SomeBlobKey', 32))
    self.mox.VerifyAll()

  def test_transform_image_resize_and_crop_portrait(self):
    """Tests resizing and cropping on a portrait image."""
    self.expect_open_image('SomeBlobKey', (148, 215))
    self.expect_crop(top_y=0.0, bottom_y=0.68837209302325575)
    self.expect_resize(32)
    self.expect_encode_image('SomeImageSize32-c')
    self.mox.ReplayAll()
    self.assertEquals(('SomeImageSize32-c', 'image/jpeg'),
                      self.app._transform_image('SomeBlobKey', 32, True))
    self.mox.VerifyAll()

  def test_transform_image_resize_and_crop_portrait_png(self):
    """Tests resizing and cropping on a portrait PNG image."""
    self.expect_open_image('SomeBlobKey', (1600, 1200), mime_type='PNG')
    self.expect_crop(left_x=0.125, right_x=0.875)
    self.expect_resize(32)
    self.expect_encode_image('SomeImageSize32-c',
                             images_service_pb.OutputSettings.PNG)
    self.mox.ReplayAll()
    self.assertEquals(('SomeImageSize32-c', 'image/png'),
                      self.app._transform_image('SomeBlobKey', 32, True))
    self.mox.VerifyAll()

  def test_transform_image_resize_and_crop_landscape(self):
    """Tests resizing and cropping on a landscape image."""
    self.expect_open_image('SomeBlobKey', (1200, 1600))
    self.expect_crop(top_y=0.0, bottom_y=0.75)
    self.expect_resize(32)
    self.expect_encode_image('SomeImageSize32-c')
    self.mox.ReplayAll()
    self.assertEquals(('SomeImageSize32-c', 'image/jpeg'),
                      self.app._transform_image('SomeBlobKey', 32, True))
    self.mox.VerifyAll()

  def test_run_no_resize_no_crop(self):
    """Tests an image request without resizing or cropping."""
    self.expect_datatore_lookup('SomeBlobKey', True)

    # Should result in serving form blobstore directly.
    self.run_blobstore_serving_request('SomeBlobKey')

  def test_run_resize_without_working_images_stub(self):
    """Tests requesting a resized image without working images stub."""
    blob_image._HAS_WORKING_IMAGES_STUB = False
    self.expect_datatore_lookup('SomeBlobKey', True)
    self._environ['PATH_INFO'] += '=s32'

    # Should result in serving form blobstore directly.
    self.run_blobstore_serving_request('SomeBlobKey')

  def test_run_resize(self):
    """Tests an image request with resizing."""
    self.expect_datatore_lookup('SomeBlobKey', True)
    self.expect_open_image('SomeBlobKey', (1600, 1200))
    self.expect_resize(32)
    self.expect_encode_image('SomeImageSize32')
    self.mox.ReplayAll()
    self._environ['PATH_INFO'] += '=s32'
    self.run_request('image/jpeg', 'SomeImageSize32')

  def test_run_resize_with_padded_blobkey(self):
    """Tests an image request to resize with a padded blobkey."""
    padded_blobkey = 'SomeBlobKey==='
    self.expect_datatore_lookup(padded_blobkey, True)
    self.expect_open_image(padded_blobkey, (1600, 1200))
    self.expect_resize(32)
    self.expect_encode_image('SomeImageSize32')
    self.mox.ReplayAll()
    self._environ['PATH_INFO'] += '====s32'
    self.run_request('image/jpeg', 'SomeImageSize32')

  def test_run_resize_and_crop(self):
    """Tests an image request with a resize and crop."""
    self.expect_datatore_lookup('SomeBlobKey', True)
    self.expect_open_image('SomeBlobKey', (1600, 1200))
    self.expect_crop(left_x=0.125, right_x=0.875)
    self.expect_resize(32)
    self.expect_encode_image('SomeImageSize32')
    self.mox.ReplayAll()
    self._environ['PATH_INFO'] += '=s32-c'
    self.run_request('image/jpeg', 'SomeImageSize32')

  def test_run_resize_and_crop_png(self):
    """Tests an image request with a resize and crop in PNG."""
    self.expect_datatore_lookup('SomeBlobKey', True)
    self.expect_open_image('SomeBlobKey', (1600, 1200), mime_type='PNG')
    self.expect_crop(left_x=0.125, right_x=0.875)
    self.expect_resize(32)
    self.expect_encode_image('SomeImageSize32',
                             images_service_pb.OutputSettings.PNG)
    self.mox.ReplayAll()
    self._environ['PATH_INFO'] += '=s32-c'
    self.run_request('image/png', 'SomeImageSize32')

  def test_run_resize_and_crop_with_padded_blobkey(self):
    """Tests an image request with a resize and crop on a padded blobkey."""
    padded_blobkey = 'SomeBlobKey===='
    self.expect_datatore_lookup(padded_blobkey, True)
    self.expect_open_image(padded_blobkey, (1600, 1200))
    self.expect_crop(left_x=0.125, right_x=0.875)
    self.expect_resize(32)
    self.expect_encode_image('SomeImageSize32')
    self.mox.ReplayAll()
    self._environ['PATH_INFO'] += '=====s32-c'
    self.run_request('image/jpeg', 'SomeImageSize32')

  def test_not_get(self):
    """Tests POSTing to a url."""
    self._environ['REQUEST_METHOD'] = 'POST'
    self.assertResponse('405 %s' % httplib.responses[405], [], '', self.app,
                        self._environ)

  def test_key_not_found(self):
    """Tests an image request for a key that doesn't exist."""
    self.expect_datatore_lookup('SomeBlobKey', False)
    self.mox.ReplayAll()
    self.assertResponse('404 %s' % httplib.responses[404], [], '', self.app,
                        self._environ)

  def test_invalid_url(self):
    """Tests an image request with an invalid path."""
    self._environ['PATH_INFO'] = '/_ah/img/'
    self.mox.ReplayAll()
    self.assertResponse('400 %s' % httplib.responses[400], [], '', self.app,
                        self._environ)

  def test_invalid_options(self):
    """Tests an image request with an invalid size."""
    self.expect_datatore_lookup('SomeBlobKey', True)
    self.expect_open_image('SomeBlobKey', (1600, 1200))
    self._environ['PATH_INFO'] += '=s%s' % (blob_image._SIZE_LIMIT + 1)
    self.mox.ReplayAll()
    self.assertResponse('400 %s' % httplib.responses[400], [], '', self.app,
                        self._environ)


if __name__ == '__main__':
  unittest.main()
