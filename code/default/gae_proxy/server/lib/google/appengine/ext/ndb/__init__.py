#
# Copyright 2008 The ndb Authors. All Rights Reserved.
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

"""NDB -- A new datastore API for the Google App Engine Python runtime."""

__version__ = '1.0.10'

__all__ = []

from tasklets import *
__all__ += tasklets.__all__

from model import *  # This implies key.*
__all__ += model.__all__

from query import *
__all__ += query.__all__

from context import *
__all__ += context.__all__
