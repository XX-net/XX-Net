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
"""Utilities to support geo fields on the Python dev server."""

import math


class LatLng(object):
  """A class representing a Latitude/Longitude pair."""

  _EARTH_RADIUS_METERS = 6371010

  def __init__(self, latitude, longitude):
    """Initializer.

    Args:
      latitude: The latitude in degrees.
      longitude: The longitude in degrees.

    Raises:
      TypeError: If a non-numeric latitude or longitude is passed.
    """
    self._lat = latitude
    self._lng = longitude

  @property
  def latitude(self):
    """Returns the latitude in degrees."""
    return self._lat

  @property
  def longitude(self):
    """Returns the longitude in degrees."""
    return self._lng

  def __sub__(self, other):
    """Subtraction.

    Args:
      other: the LatLng which this LatLng is subtracted by.

    Returns:
      the great circle distance between two LatLng objects as computed
      by the Haversine formula.
    """

    assert isinstance(other, LatLng)

    lat_rad = math.radians(self._lat)
    lng_rad = math.radians(self._lng)
    other_lat_rad = math.radians(other.latitude)
    other_lng_rad = math.radians(other.longitude)

    dlat = lat_rad - other_lat_rad
    dlng = lng_rad - other_lng_rad
    a1 = math.sin(dlat / 2)**2
    a2 = math.cos(lat_rad) * math.cos(other_lat_rad) * math.sin(dlng / 2)**2
    return 2 * self._EARTH_RADIUS_METERS * math.asin(math.sqrt(a1 + a2))
