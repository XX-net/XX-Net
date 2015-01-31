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




"""Dispatcher for dynamic image serving requests.

Classes:

  CreateBlobImageDispatcher:
    Creates a dispatcher that will handle an image serving request. It will
    fetch an image from blobstore and dynamically resize it.
"""


import logging
import re
import urlparse

from google.appengine.api.images import images_service_pb

BLOBIMAGE_URL_PATTERN = '/_ah/img(?:/.*)?'

BLOBIMAGE_RESPONSE_TEMPLATE = ('Status: %(status)s\r\nContent-Type: %(content_type)s'
                               '\r\n\r\n%(data)s')

def CreateBlobImageDispatcher(images_stub):
  """Function to create a dynamic image serving stub.

  Args:
    images_stub: an images_stub to perform the image resizing on blobs.


  Returns:
    New dispatcher capable of dynamic image serving requests.
  """



  from google.appengine.tools import dev_appserver

  class BlobImageDispatcher(dev_appserver.URLDispatcher):
    """Dispatcher that handles image serving requests."""

    _size_limit = 1600
    _mime_type_map = {images_service_pb.OutputSettings.JPEG: 'image/jpeg',
                      images_service_pb.OutputSettings.PNG: 'image/png',
                      images_service_pb.OutputSettings.WEBP: 'image/webp'}

    def __init__(self, images_stub):
      """Constructor.

      Args:
        images_stub: an images_stub to perform the image resizing on blobs.
      """
      self._images_stub = images_stub

    def _TransformImage(self, blob_key, options):
      """Construct and execute transform request to the images stub.

      Args:
        blob_key: blob_key to the image to transform.
        options: resize and crop option string to apply to the image.

      Returns:
        The tranformed (if necessary) image bytes.
      """
      resize, crop = self._ParseOptions(options)

      image_data = images_service_pb.ImageData()
      image_data.set_blob_key(blob_key)
      image = self._images_stub._OpenImageData(image_data)
      original_mime_type = image.format


      if crop:
        width, height = image.size
        crop_xform = None
        if width > height:

          crop_xform = images_service_pb.Transform()
          delta = (width - height) / (width * 2.0)
          crop_xform.set_crop_left_x(delta)
          crop_xform.set_crop_right_x(1.0 - delta)
        elif width < height:

          crop_xform = images_service_pb.Transform()
          delta = (height - width) / (height * 2.0)
          top_delta = max(0.0, delta - 0.25)
          bottom_delta = 1.0 - (2.0 * delta) + top_delta
          crop_xform.set_crop_top_y(top_delta)
          crop_xform.set_crop_bottom_y(bottom_delta)
        if crop_xform:
          image = self._images_stub._Crop(image, crop_xform)


      if resize:
        resize_xform = images_service_pb.Transform()
        resize_xform.set_width(resize)
        resize_xform.set_height(resize)
        image = self._images_stub._Resize(image, resize_xform)

      output_settings = images_service_pb.OutputSettings()


      output_mime_type = images_service_pb.OutputSettings.JPEG
      if original_mime_type in ['PNG', 'GIF']:
        output_mime_type = images_service_pb.OutputSettings.PNG
      output_settings.set_mime_type(output_mime_type)
      return (self._images_stub._EncodeImage(image, output_settings),
              self._mime_type_map[output_mime_type])

    def _ParseOptions(self, options):
      """Currently only support resize and crop options.

      Args:
        options: the url resize and crop option string.

      Returns:
        (resize, crop) options parsed from the string.
      """
      match = re.search('^s(\\d+)(-c)?', options)
      resize = None
      crop = False
      if match:
        if match.group(1):
          resize = int(match.group(1))
        if match.group(2):
          crop = True


      if resize and (resize > BlobImageDispatcher._size_limit or
                     resize < 0):
        raise ValueError, 'Invalid resize'
      return (resize, crop)

    def _ParseUrl(self, url):
      """Parse the URL into the blobkey and option string.

      Args:
        url: a url as a string.

      Returns:
        (blob_key, option) tuple parsed out of the URL.
      """
      path = urlparse.urlsplit(url)[2]
      match = re.search('/_ah/img/([-\\w]+)([=]*)([-\\w]+)?', path)
      if not match or not match.group(1):
        raise ValueError, 'Failed to parse image url.'
      options = ''
      blobkey = match.group(1)
      if match.group(3):
        if match.group(2):
          blobkey = ''.join([blobkey, match.group(2)[1:]])
        options = match.group(3)
      elif match.group(2):
        blobkey = ''.join([blobkey, match.group(2)])
      return (blobkey, options)


    def Dispatch(self,
                 request,
                 outfile,
                 base_env_dict=None):
      """Handle GET image serving request.

      This dispatcher handles image requests under the /_ah/img/ path.
      The rest of the path should be a serialized blobkey used to retrieve
      the image from blobstore.

      Args:
        request: The HTTP request.
        outfile: The response file.
        base_env_dict: Dictionary of CGI environment parameters if available.
          Defaults to None.
      """
      try:
        if base_env_dict and base_env_dict['REQUEST_METHOD'] != 'GET':
          raise RuntimeError, 'BlobImage only handles GET requests.'

        blobkey, options = self._ParseUrl(request.relative_url)
        image, mime_type = self._TransformImage(blobkey, options)
        output_dict = { 'status': 200, 'content_type': mime_type,
                        'data': image }
        outfile.write(BLOBIMAGE_RESPONSE_TEMPLATE % output_dict)
      except ValueError:
        logging.exception('ValueError while serving image.')
        outfile.write('Status: 404\r\n')
      except RuntimeError:
        logging.exception('RuntimeError while serving image.')
        outfile.write('Status: 400\r\n')
      except:


        logging.exception('Exception while serving image.')
        outfile.write('Status: 500\r\n')

  return BlobImageDispatcher(images_stub)
