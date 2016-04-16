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
"""Provides ValueMixin.

ValueMixin provides comparison (including equality) methods and hashing
based on the values of fields.
"""


class ValueMixin(object):
  def __cmp__(self, other):






    if hasattr(other, '__dict__'):
      return self.__dict__.__cmp__(other.__dict__)
    else:
      return 1

  def __hash__(self):
    return hash(frozenset(self.__dict__.items()))

  def __repr__(self):

    d = self.__dict__
    attrs = ['%s=%r' % (key, d[key]) for key in sorted(d)]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(attrs))
