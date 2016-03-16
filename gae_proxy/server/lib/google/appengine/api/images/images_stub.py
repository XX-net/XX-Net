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




"""Stub version of the images API."""






import datetime
import logging
import re
import StringIO
import time



try:
  import json as simplejson
except ImportError:
  import simplejson

try:
  import PIL
  from PIL import _imaging
  from PIL import Image
except ImportError:
  import _imaging
  # Try importing the 'Image' module directly. If that fails, try
  # importing it from the 'PIL' package (this is necessary to also
  # cover "pillow" package installations).
  try:
    import Image
  except ImportError:
    from PIL import Image

from google.appengine.api import apiproxy_stub
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore
from google.appengine.api import datastore_errors
from google.appengine.api import datastore_types
from google.appengine.api import images
from google.appengine.api.blobstore import blobstore_stub
from google.appengine.api.images import images_blob_stub
from google.appengine.api.images import images_service_pb
from google.appengine.runtime import apiproxy_errors



BLOB_SERVING_URL_KIND = images_blob_stub.BLOB_SERVING_URL_KIND
BMP = 'BMP'
GIF = 'GIF'
GS_INFO_KIND = '__GsFileInfo__'
ICO = 'ICO'
JPEG = 'JPEG'
MAX_REQUEST_SIZE = 32 << 20  # 32MB
PNG = 'PNG'
RGB = 'RGB'
RGBA = 'RGBA'
TIFF = 'TIFF'
WEBP = 'WEBP'

FORMAT_LIST = [BMP, GIF, ICO, JPEG, PNG, TIFF, WEBP]
EXIF_TIME_REGEX = re.compile(r'^([0-9]{4}):([0-9]{1,2}):([0-9]{1,2})'
                             ' ([0-9]{1,2}):([0-9]{1,2})(?::([0-9]{1,2}))?')


# Orientation tag id in EXIF.
_EXIF_ORIENTATION_TAG = 274

# DateTimeOriginal tag in EXIF.
_EXIF_DATETIMEORIGINAL_TAG = 36867

# Subset of EXIF tags. The stub is only able to extract these fields.
_EXIF_TAGS = {
    256: 'ImageWidth',
    257: 'ImageLength',
    271: 'Make',
    272: 'Model',
    _EXIF_ORIENTATION_TAG: 'Orientation',
    305: 'Software',
    306: 'DateTime',
    34855: 'ISOSpeedRatings',
    _EXIF_DATETIMEORIGINAL_TAG: 'DateTimeOriginal',
    36868: 'DateTimeDigitized',
    37383: 'MeteringMode',
    37385: 'Flash',
    41987: 'WhiteBalance'}


def _ArgbToRgbaTuple(argb):
  """Convert from a single ARGB value to a tuple containing RGBA.

  Args:
    argb: Signed 32 bit integer containing an ARGB value.

  Returns:
    RGBA tuple.
  """

  unsigned_argb = argb % 0x100000000
  return ((unsigned_argb >> 16) & 0xFF,
          (unsigned_argb >> 8) & 0xFF,
          unsigned_argb & 0xFF,
          (unsigned_argb >> 24) & 0xFF)


def _BackendPremultiplication(color):
  """Apply premultiplication and unpremultiplication to match production.

  Args:
    color: color tuple as returned by _ArgbToRgbaTuple.

  Returns:
    RGBA tuple.
  """




  alpha = color[3]
  rgb = color[0:3]
  multiplied = [(x * (alpha + 1)) >> 8 for x in rgb]
  if alpha:
    alpha_inverse = 0xffffff / alpha
    unmultiplied = [(x * alpha_inverse) >> 16 for x in multiplied]
  else:
    unmultiplied = [0] * 3

  return tuple(unmultiplied + [alpha])


class ImagesServiceStub(apiproxy_stub.APIProxyStub):
  """Stub version of images API to be used with the dev_appserver."""

  def __init__(self, service_name='images', host_prefix=''):
    """Preloads PIL to load all modules in the unhardened environment.

    Args:
      service_name: Service name expected for all calls.
      host_prefix: the URL prefix (protocol://host:port) to preprend to
        image urls on a call to GetUrlBase.
    """
    super(ImagesServiceStub, self).__init__(
        service_name, max_request_size=MAX_REQUEST_SIZE)
    self._blob_stub = images_blob_stub.ImagesBlobStub(host_prefix)
    Image.init()

  def _Dynamic_Composite(self, request, response):
    """Implementation of ImagesService::Composite.

    Based off documentation of the PIL library at
    http://www.pythonware.com/library/pil/handbook/index.htm

    Args:
      request: ImagesCompositeRequest - Contains image request info.
      response: ImagesCompositeResponse - Contains transformed image.

    Raises:
      ApplicationError: Bad data was provided, likely data about the dimensions.
    """
    if (not request.canvas().width() or not request.canvas().height() or
        not request.image_size() or not request.options_size()):
      raise apiproxy_errors.ApplicationError(
          images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)
    if (request.canvas().width() > 4000 or
        request.canvas().height() > 4000 or
        request.options_size() > images.MAX_COMPOSITES_PER_REQUEST):
      raise apiproxy_errors.ApplicationError(
          images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)

    width = request.canvas().width()
    height = request.canvas().height()
    color = _ArgbToRgbaTuple(request.canvas().color())


    color = _BackendPremultiplication(color)
    canvas = Image.new(RGBA, (width, height), color)
    sources = []
    for image in request.image_list():
      sources.append(self._OpenImageData(image))

    for options in request.options_list():
      if (options.anchor() < images.TOP_LEFT or
          options.anchor() > images.BOTTOM_RIGHT):
        raise apiproxy_errors.ApplicationError(
            images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)
      if options.source_index() >= len(sources) or options.source_index() < 0:
        raise apiproxy_errors.ApplicationError(
            images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)
      if options.opacity() < 0 or options.opacity() > 1:
        raise apiproxy_errors.ApplicationError(
            images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)
      source = sources[options.source_index()]
      x_anchor = (options.anchor() % 3) * 0.5
      y_anchor = (options.anchor() / 3) * 0.5
      x_offset = int(options.x_offset() + x_anchor * (width - source.size[0]))
      y_offset = int(options.y_offset() + y_anchor * (height - source.size[1]))
      if source.mode == RGBA:
        canvas.paste(source, (x_offset, y_offset), source)
      else:
        alpha = options.opacity() * 255
        mask = Image.new('L', source.size, alpha)
        canvas.paste(source, (x_offset, y_offset), mask)
    response_value = self._EncodeImage(canvas, request.canvas().output())
    response.mutable_image().set_content(response_value)

  def _Dynamic_Histogram(self, request, response):
    """Trivial implementation of an API.

    Based off documentation of the PIL library at
    http://www.pythonware.com/library/pil/handbook/index.htm

    Args:
      request: ImagesHistogramRequest - Contains the image.
      response: ImagesHistogramResponse - Contains histogram of the image.

    Raises:
      ApplicationError: Image was of an unsupported format.
    """
    image = self._OpenImageData(request.image())

    img_format = image.format
    if img_format not in FORMAT_LIST:
      raise apiproxy_errors.ApplicationError(
          images_service_pb.ImagesServiceError.NOT_IMAGE)
    image = image.convert(RGBA)
    red = [0] * 256
    green = [0] * 256
    blue = [0] * 256




    for pixel in image.getdata():
      red[int((pixel[0] * pixel[3]) / 255)] += 1
      green[int((pixel[1] * pixel[3]) / 255)] += 1
      blue[int((pixel[2] * pixel[3]) / 255)] += 1
    histogram = response.mutable_histogram()
    for value in red:
      histogram.add_red(value)
    for value in green:
      histogram.add_green(value)
    for value in blue:
      histogram.add_blue(value)

  def _Dynamic_Transform(self, request, response):
    """Trivial implementation of ImagesService::Transform.

    Based off documentation of the PIL library at
    http://www.pythonware.com/library/pil/handbook/index.htm

    Args:
      request: ImagesTransformRequest, contains image request info.
      response: ImagesTransformResponse, contains transformed image.
    """
    original_image = self._OpenImageData(request.image())

    input_settings = request.input()
    correct_orientation = (
        input_settings.has_correct_exif_orientation() and
        input_settings.correct_exif_orientation() ==
        images_service_pb.InputSettings.CORRECT_ORIENTATION)



    source_metadata = self._ExtractMetadata(
        original_image, input_settings.parse_metadata())
    if input_settings.parse_metadata():
      logging.info(
          'Once the application is deployed, a more powerful metadata '
          'extraction will be performed which might return many more fields.')

    new_image = self._ProcessTransforms(
        original_image, request.transform_list(), correct_orientation)

    substitution_rgb = None
    if input_settings.has_transparent_substitution_rgb():
      substitution_rgb = input_settings.transparent_substitution_rgb()
    response_value = self._EncodeImage(
        new_image, request.output(), substitution_rgb)
    response.mutable_image().set_content(response_value)
    response.set_source_metadata(source_metadata)

  def _Dynamic_GetUrlBase(self, request, response):
    self._blob_stub.GetUrlBase(request, response)

  def _Dynamic_DeleteUrlBase(self, request, response):
    self._blob_stub.DeleteUrlBase(request, response)

  def _EncodeImage(self, image, output_encoding, substitution_rgb=None):
    """Encode the given image and return it in string form.

    Args:
      image: PIL Image object, image to encode.
      output_encoding: ImagesTransformRequest.OutputSettings object.
      substitution_rgb: The color to use for transparent pixels if the output
        format does not support transparency.

    Returns:
      str - Encoded image information in given encoding format.  Default is PNG.
    """
    image_string = StringIO.StringIO()
    image_encoding = PNG

    if output_encoding.mime_type() == images_service_pb.OutputSettings.WEBP:
      image_encoding = WEBP

    if output_encoding.mime_type() == images_service_pb.OutputSettings.JPEG:
      image_encoding = JPEG






      if substitution_rgb:



        blue = substitution_rgb & 0xFF
        green = (substitution_rgb >> 8) & 0xFF
        red = (substitution_rgb >> 16) & 0xFF
        background = Image.new(RGB, image.size, (red, green, blue))
        background.paste(image, mask=image.convert(RGBA).split()[3])
        image = background
      else:
        image = image.convert(RGB)

    image.save(image_string, image_encoding)
    return image_string.getvalue()

  def _OpenImageData(self, image_data):
    """Open image data from ImageData protocol buffer.

    Args:
      image_data: ImageData protocol buffer containing image data or blob
        reference.

    Returns:
      Image containing the image data passed in or reference by blob-key.

    Raises:
      ApplicationError: Both content and blob-key are provided.
      NOTE: 'content' must always be set because it is a required field,
      however, it must be the empty string when a blob-key is provided.
    """
    if image_data.content() and image_data.has_blob_key():
      raise apiproxy_errors.ApplicationError(
          images_service_pb.ImagesServiceError.INVALID_BLOB_KEY)

    if image_data.has_blob_key():
      image = self._OpenBlob(image_data.blob_key())
    else:
      image = self._OpenImage(image_data.content())


    img_format = image.format
    if img_format not in FORMAT_LIST:
      raise apiproxy_errors.ApplicationError(
          images_service_pb.ImagesServiceError.NOT_IMAGE)
    return image

  def _OpenImage(self, image):
    """Opens an image provided as a string.

    Args:
      image: Image data to be opened.

    Raises:
      ApplicationError: Image could not be opened or was an unsupported format.

    Returns:
      Image containing the image data passed in.
    """
    if not image:
      raise apiproxy_errors.ApplicationError(
          images_service_pb.ImagesServiceError.NOT_IMAGE)

    image = StringIO.StringIO(image)
    try:
      return Image.open(image)
    except IOError:

      raise apiproxy_errors.ApplicationError(
          images_service_pb.ImagesServiceError.BAD_IMAGE_DATA)

  def _OpenBlob(self, blob_key):
    """Create an Image from the blob data read from blob_key."""

    try:
      _ = datastore.Get(
          blobstore_stub.BlobstoreServiceStub.ToDatastoreBlobKey(blob_key))
    except datastore_errors.Error:


      logging.exception('Blob with key %r does not exist', blob_key)
      raise apiproxy_errors.ApplicationError(
          images_service_pb.ImagesServiceError.UNSPECIFIED_ERROR)

    blobstore_storage = apiproxy_stub_map.apiproxy.GetStub('blobstore')


    try:
      blob_file = blobstore_storage.storage.OpenBlob(blob_key)
    except IOError:
      logging.exception('Could not get file for blob_key %r', blob_key)

      raise apiproxy_errors.ApplicationError(
          images_service_pb.ImagesServiceError.BAD_IMAGE_DATA)

    try:
      return Image.open(blob_file)
    except IOError:
      logging.exception('Could not open image %r for blob_key %r',
                        blob_file, blob_key)

      raise apiproxy_errors.ApplicationError(
          images_service_pb.ImagesServiceError.BAD_IMAGE_DATA)

  def _ValidateCropArg(self, arg):
    """Check an argument for the Crop transform.

    Args:
      arg: float - Argument to Crop transform to check.

    Raises:
      ApplicationError: There was a problem with the provided argument.
    """
    if not isinstance(arg, float):
      raise apiproxy_errors.ApplicationError(
          images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)

    if 0 > arg or arg > 1.0:
      raise apiproxy_errors.ApplicationError(
          images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)

  def _CalculateNewDimensions(self,
                              current_width,
                              current_height,
                              req_width,
                              req_height,
                              crop_to_fit,
                              allow_stretch):
    """Get new resize dimensions keeping the current aspect ratio.

    This uses the more restricting of the two requested values to determine
    the new ratio. See also crop_to_fit.

    Args:
      current_width: int, current width of the image.
      current_height: int, current height of the image.
      req_width: int, requested new width of the image, 0 if unspecified.
      req_height: int, requested new height of the image, 0 if unspecified.
      crop_to_fit: bool, True if the less restricting dimension should be used.
      allow_stretch: bool, True is aspect ratio should be ignored.

    Raises:
      apiproxy_errors.ApplicationError: if crop_to_fit is True either req_width
        or req_height is 0.

    Returns:
      tuple (width, height) ints of the new dimensions.
    """


    width_ratio = float(req_width) / current_width
    height_ratio = float(req_height) / current_height

    height = req_height
    width = req_width
    if allow_stretch or crop_to_fit:

      if not req_width or not req_height:
        raise apiproxy_errors.ApplicationError(
            images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)
      if not allow_stretch:
        if width_ratio > height_ratio:
          height = int(width_ratio * current_height)
        else:
          width = int(height_ratio * current_width)
    else:



      if not req_width or (width_ratio > height_ratio and req_height):

        width = int(height_ratio * current_width)
      else:

        height = int(width_ratio * current_height)
    return width, height

  def _Resize(self, image, transform):
    """Use PIL to resize the given image with the given transform.

    Args:
      image: PIL.Image.Image object to resize.
      transform: images_service_pb.Transform to use when resizing.

    Returns:
      PIL.Image.Image with transforms performed on it.

    Raises:
      ApplicationError: The resize data given was bad.
    """
    width = 0
    height = 0

    if transform.has_width():
      width = transform.width()
      if width < 0 or 4000 < width:
        raise apiproxy_errors.ApplicationError(
            images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)

    if transform.has_height():
      height = transform.height()
      if height < 0 or 4000 < height:
        raise apiproxy_errors.ApplicationError(
            images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)

    crop_to_fit = transform.crop_to_fit()
    allow_stretch = transform.allow_stretch()

    current_width, current_height = image.size
    new_width, new_height = self._CalculateNewDimensions(
        current_width, current_height, width, height, crop_to_fit,
        allow_stretch)
    new_image = image.resize((new_width, new_height), Image.ANTIALIAS)
    if crop_to_fit and (new_width > width or new_height > height):

      left = int((new_width - width) * transform.crop_offset_x())
      top = int((new_height - height) * transform.crop_offset_y())
      right = left + width
      bottom = top + height
      new_image = new_image.crop((left, top, right, bottom))

    return new_image

  def _Rotate(self, image, transform):
    """Use PIL to rotate the given image with the given transform.

    Args:
      image: PIL.Image.Image object to rotate.
      transform: images_service_pb.Transform to use when rotating.

    Returns:
      PIL.Image.Image with transforms performed on it.

    Raises:
      ApplicationError: Given data for the rotate was bad.
    """
    degrees = transform.rotate()
    if degrees < 0 or degrees % 90 != 0:
      raise apiproxy_errors.ApplicationError(
          images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)
    degrees %= 360


    degrees = 360 - degrees
    return image.rotate(degrees)

  def _Crop(self, image, transform):
    """Use PIL to crop the given image with the given transform.

    Args:
      image: PIL.Image.Image object to crop.
      transform: images_service_pb.Transform to use when cropping.

    Returns:
      PIL.Image.Image with transforms performed on it.

    Raises:
      BadRequestError if the crop data given is bad.
    """
    left_x = 0.0
    top_y = 0.0
    right_x = 1.0
    bottom_y = 1.0

    if transform.has_crop_left_x():
      left_x = transform.crop_left_x()
      self._ValidateCropArg(left_x)

    if transform.has_crop_top_y():
      top_y = transform.crop_top_y()
      self._ValidateCropArg(top_y)

    if transform.has_crop_right_x():
      right_x = transform.crop_right_x()
      self._ValidateCropArg(right_x)

    if transform.has_crop_bottom_y():
      bottom_y = transform.crop_bottom_y()
      self._ValidateCropArg(bottom_y)


    width, height = image.size

    box = (int(round(left_x * width)),
           int(round(top_y * height)),
           int(round(right_x * width)),
           int(round(bottom_y * height)))

    return image.crop(box)

  @staticmethod
  def _GetExifFromImage(image):
    if hasattr(image, '_getexif'):





      try:

        from PIL import TiffImagePlugin

        return image._getexif()
      except ImportError:
        # We have not managed to get this to work in the SDK with Python
        # 2.5, so just catch the ImportError and pretend there is no
        # EXIF information of interest.
        logging.info('Sorry, TiffImagePlugin does not work in this environment')
    return None

  @staticmethod
  def _ExtractMetadata(image, parse_metadata):
    """Extract EXIF metadata from the image.

    Note that this is a much simplified version of metadata extraction. After
    deployment applications have access to a more powerful parser that can
    parse hundreds of fields from images.

    Args:
      image: PIL Image object.
      parse_metadata: bool, True if metadata parsing has been requested. If
        False the result will contain image dimensions.
    Returns:
      str - JSON encoded values with various metadata fields.
    """

    def ExifTimeToUnixtime(exif_time):
      """Convert time in EXIF to unix time.

      Args:
        exif_time: str - Time from the EXIF block formated by EXIF standard.
            Seconds are optional.  (Example: '2011:02:20 10:23:12')

      Returns:
        Integer, the time in unix fromat: seconds since the epoch.
      """
      match = EXIF_TIME_REGEX.match(exif_time)
      if not match:
        return None
      try:
        date = datetime.datetime(*map(int, filter(None, match.groups())))
      except ValueError:
        logging.info('Invalid date in EXIF: %s', exif_time)
        return None
      return int(time.mktime(date.timetuple()))

    metadata_dict = (
        parse_metadata and ImagesServiceStub._GetExifFromImage(image) or {})

    metadata_dict[256], metadata_dict[257] = image.size



    if _EXIF_DATETIMEORIGINAL_TAG in metadata_dict:
      date_ms = ExifTimeToUnixtime(metadata_dict[_EXIF_DATETIMEORIGINAL_TAG])
      if date_ms:
        metadata_dict[_EXIF_DATETIMEORIGINAL_TAG] = date_ms
      else:
        del metadata_dict[_EXIF_DATETIMEORIGINAL_TAG]
    metadata = dict(
        [(_EXIF_TAGS[k], v) for k, v in metadata_dict.iteritems()
         if k in _EXIF_TAGS])
    return simplejson.dumps(metadata)

  def _CorrectOrientation(self, image, orientation):
    """Use PIL to correct the image orientation based on its EXIF.

    See JEITA CP-3451 at http://www.exif.org/specifications.html,
    Exif 2.2, page 18.

    Args:
      image: source PIL.Image.Image object.
      orientation: integer in range (1,8) inclusive, corresponding the image
        orientation from EXIF.

    Returns:
      PIL.Image.Image with transforms performed on it. If no correction was
        done, it returns the input image.
    """


    if orientation == 2:
      image = image.transpose(Image.FLIP_LEFT_RIGHT)
    elif orientation == 3:
      image = image.rotate(180)
    elif orientation == 4:
      image = image.transpose(Image.FLIP_TOP_BOTTOM)
    elif orientation == 5:
      image = image.transpose(Image.FLIP_TOP_BOTTOM)
      image = image.rotate(270)
    elif orientation == 6:
      image = image.rotate(270)
    elif orientation == 7:
      image = image.transpose(Image.FLIP_LEFT_RIGHT)
      image = image.rotate(270)
    elif orientation == 8:
      image = image.rotate(90)

    return image

  def _ProcessTransforms(self, image, transforms, correct_orientation):
    """Execute PIL operations based on transform values.

    Args:
      image: PIL.Image.Image instance, image to manipulate.
      transforms: list of ImagesTransformRequest.Transform objects.
      correct_orientation: True to indicate that image orientation should be
        corrected based on its EXIF.
    Returns:
      PIL.Image.Image with transforms performed on it.

    Raises:
      ApplicationError: More than one of the same type of transform was present.
    """
    new_image = image
    if len(transforms) > images.MAX_TRANSFORMS_PER_REQUEST:
      raise apiproxy_errors.ApplicationError(
          images_service_pb.ImagesServiceError.BAD_TRANSFORM_DATA)

    orientation = 1
    if correct_orientation:


      exif = self._GetExifFromImage(image)
      if not exif or _EXIF_ORIENTATION_TAG not in exif:
        correct_orientation = False
      else:
        orientation = exif[_EXIF_ORIENTATION_TAG]

      width, height = new_image.size
      if height > width:
        orientation = 1

    for transform in transforms:







      if (correct_orientation and
          not (transform.has_crop_left_x() or
               transform.has_crop_top_y() or
               transform.has_crop_right_x() or
               transform.has_crop_bottom_y()) and
          not transform.has_horizontal_flip() and
          not transform.has_vertical_flip()):
        new_image = self._CorrectOrientation(new_image, orientation)
        correct_orientation = False

      if transform.has_width() or transform.has_height():

        new_image = self._Resize(new_image, transform)

      elif transform.has_rotate():

        new_image = self._Rotate(new_image, transform)

      elif transform.has_horizontal_flip():

        new_image = new_image.transpose(Image.FLIP_LEFT_RIGHT)

      elif transform.has_vertical_flip():

        new_image = new_image.transpose(Image.FLIP_TOP_BOTTOM)

      elif (transform.has_crop_left_x() or
            transform.has_crop_top_y() or
            transform.has_crop_right_x() or
            transform.has_crop_bottom_y()):

        new_image = self._Crop(new_image, transform)

      elif transform.has_autolevels():


        logging.info('I\'m Feeling Lucky autolevels will be visible once this '
                     'application is deployed.')
      else:
        logging.warn('Found no transformations found to perform.')

      if correct_orientation:


        new_image = self._CorrectOrientation(new_image, orientation)
        correct_orientation = False




    return new_image
