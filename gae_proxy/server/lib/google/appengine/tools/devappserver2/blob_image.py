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
"""Handles dynamic serving of images from blobstore."""

import httplib
import logging
import re

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore
from google.appengine.api import datastore_errors
from google.appengine.api.images import images_service_pb
from google.appengine.ext import blobstore
from google.appengine.tools.devappserver2 import blob_download
from google.appengine.tools.devappserver2 import request_rewriter

BLOBIMAGE_URL_PATTERN = '_ah/img(?:/.*)?'
_BLOB_SERVING_URL_KIND = '__BlobServingUrl__'
_DEFAULT_SERVING_SIZE = 512
_SIZE_LIMIT = 1600
_OPTIONS_RE = re.compile(r'^s(\d+)(-c)?')
_PATH_RE = re.compile(r'/_ah/img/([-\w:]+)([=]*)([-\w]+)?')
_MIME_TYPE_MAP = {images_service_pb.OutputSettings.JPEG: 'image/jpeg',
                  images_service_pb.OutputSettings.PNG: 'image/png',
                  images_service_pb.OutputSettings.WEBP: 'image/webp'}

# Check there's a working images stub.
try:
  # pylint: disable=g-import-not-at-top, unused-import
  from google.appengine.api.images import images_stub
  _HAS_WORKING_IMAGES_STUB = True
except ImportError:
  _HAS_WORKING_IMAGES_STUB = False


def _get_images_stub():
  return apiproxy_stub_map.apiproxy.GetStub('images')


class Error(Exception):
  pass


class InvalidRequestError(Error):
  """The request was invalid."""


class Application(object):
  """A WSGI application that handles image serving requests."""

  def _transform_image(self, blob_key, resize=None, crop=False):
    """Construct and execute a transform request using the images stub.

    Args:
      blob_key: A str containing the blob_key of the image to transform.
      resize: An integer for the size of the resulting image.
      crop: A boolean determining if the image should be cropped or resized.

    Returns:
      A str containing the tranformed (if necessary) image.
    """
    image_data = images_service_pb.ImageData()
    image_data.set_blob_key(blob_key)
    image = _get_images_stub()._OpenImageData(image_data)
    original_mime_type = image.format
    width, height = image.size

    # Crop to square if necessary
    if crop:
      crop_xform = None
      if width > height:
        # landscape: slice the sides
        crop_xform = images_service_pb.Transform()
        delta = (width - height) / (width * 2.0)
        crop_xform.set_crop_left_x(delta)
        crop_xform.set_crop_right_x(1.0 - delta)
      elif width < height:
        # portrait: slice the top and bottom with bias
        crop_xform = images_service_pb.Transform()
        delta = (height - width) / (height * 2.0)
        top_delta = max(0.0, delta - 0.25)
        bottom_delta = 1.0 - (2.0 * delta) + top_delta
        crop_xform.set_crop_top_y(top_delta)
        crop_xform.set_crop_bottom_y(bottom_delta)
      if crop_xform:
        image = _get_images_stub()._Crop(image, crop_xform)

    # Resize
    if resize is None:
      if width > _DEFAULT_SERVING_SIZE or height > _DEFAULT_SERVING_SIZE:
        resize = _DEFAULT_SERVING_SIZE

    # resize value of 0 is valid and translates to 'serve at original size'.
    if resize:
      # Note that resize transform maintains the image aspect ratio.
      resize_xform = images_service_pb.Transform()
      resize_xform.set_width(resize)
      resize_xform.set_height(resize)
      image = _get_images_stub()._Resize(image, resize_xform)

    output_settings = images_service_pb.OutputSettings()
    # EncodeImage only saves out to JPEG or PNG. All image formats other than
    # GIF or PNG, will be served as a JPEG.
    output_mime_type = images_service_pb.OutputSettings.JPEG
    if original_mime_type in ['PNG', 'GIF']:
      output_mime_type = images_service_pb.OutputSettings.PNG
    output_settings.set_mime_type(output_mime_type)
    return (_get_images_stub()._EncodeImage(image, output_settings),
            _MIME_TYPE_MAP[output_mime_type])

  def _parse_options(self, options):
    """Parse an options string into a tuple containing the options.

    Currently this only supports resize and crop.

    Args:
      options: A str containing the url resize and crop options.

    Returns:
      A tuple (resize, crop) parsed from the string.

    Raises:
      InvalidRequestError: The requested resize is invalid.
    """
    match = _OPTIONS_RE.search(options)
    resize = None
    crop = False
    if match:
      if match.group(1):
        resize = int(match.group(1))
      if match.group(2):
        crop = True

    # Check size against whitelist
    if resize and (resize > _SIZE_LIMIT or resize < 0):
      logging.error('Invalid resize: %r', resize)
      raise InvalidRequestError()
    return (resize, crop)

  def _parse_path(self, path):
    """Parse the request path into the blobkey and option string.

    Args:
      path: A str containing the path of the request.

    Returns:
      A tuple (blob_key, option) parsed out of the path.

    Raises:
      InvalidRequestError: The request path is invalid.
    """
    match = _PATH_RE.search(path)
    if not match or not match.group(1):
      logging.error('Failed to parse image path "%s"', path)
      raise InvalidRequestError()
    options = ''
    blobkey = match.group(1)
    if match.group(3):
      if match.group(2):
        blobkey += match.group(2)[1:]
      options = match.group(3)
    elif match.group(2):
      blobkey += match.group(2)
    return (blobkey, options)

  def serve_unresized_image(self, blobkey, environ, start_response):
    """Use blob_download to rewrite and serve unresized image directly."""
    state = request_rewriter.RewriterState(environ, '200 OK', [
        (blobstore.BLOB_KEY_HEADER, blobkey)], [])
    blob_download.blobstore_download_rewriter(state)
    start_response(state.status, state.headers.items())
    return state.body

  def serve_image(self, environ, start_response):
    """Dynamically serve an image from blobstore."""
    blobkey, options = self._parse_path(environ['PATH_INFO'])
    # Make sure that the blob URL has been registered by
    # calling get_serving_url
    key = datastore.Key.from_path(_BLOB_SERVING_URL_KIND, blobkey, namespace='')
    try:
      datastore.Get(key)
    except datastore_errors.EntityNotFoundError:
      logging.error('The blobkey %s has not registered for image '
                    'serving. Please ensure get_serving_url is '
                    'called before attempting to serve blobs.', blobkey)
      start_response('404 %s' % httplib.responses[404], [])
      return []

    resize, crop = self._parse_options(options)

    if resize is None and not crop:
      return self.serve_unresized_image(blobkey, environ, start_response)
    elif not _HAS_WORKING_IMAGES_STUB:
      logging.warning('Serving resized images requires a working Python "PIL" '
                      'module. The image is served without resizing.')
      return self.serve_unresized_image(blobkey, environ, start_response)
    else:
      # Use Images service to transform blob.
      image, mime_type = self._transform_image(blobkey, resize, crop)
      start_response('200 OK', [
          ('Content-Type', mime_type),
          ('Cache-Control', 'public, max-age=600, no-transform')])
      return [image]

  def __call__(self, environ, start_response):
    if environ['REQUEST_METHOD'] != 'GET':
      start_response('405 %s' % httplib.responses[405], [])
      return []
    try:
      return self.serve_image(environ, start_response)
    except InvalidRequestError:
      start_response('400 %s' % httplib.responses[400], [])
      return []
