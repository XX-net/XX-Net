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




"""Bulkload package: Helpers for both bulkloader and bulkload_client.

For complete documentation, see the Tools and Libraries section of the
documentation.

This package contains two separate systems:
 * The historical and deprecated bulkload/bulkload_client server mix-in,
   in the 'bulkload.bulkload' module; exposed here for backwards compatability.
 * New helpers for the bulkloader client (appengine/tools/bulkloader.py).
   Many of these helpers can also run on the server though there is not
   (as of January 2010) any support for using them there.
"""







import bulkload_deprecated
Validate = bulkload_deprecated.Validate
Loader = bulkload_deprecated.Loader
BulkLoad = bulkload_deprecated.BulkLoad
main = bulkload_deprecated.main


