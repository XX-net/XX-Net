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




"""Files API.

.. deprecated:: 1.8.1
   Use Google Cloud Storage Client library instead.

Testing utils for writing tests involving Files API."""



__all__ = ['TestFileServiceStub']


from google.appengine.api import apiproxy_stub
from google.appengine.api.files import file_service_pb


class TestFileServiceStub(apiproxy_stub.APIProxyStub):
  """A FileServiceStub to be used with tests.

  Doesn't perform any kind of file validation and stores all
  file content in memory.
  Can be used to test low-level file calls only, because it doesn't
  support all features (like blobstore files).
  """

  def __init__(self):
    super(TestFileServiceStub, self).__init__('file')
    self._file_content = {}

  def _Dynamic_Open(self, request, response):
    pass

  def _Dynamic_Close(self, request, response):
    pass

  def _Dynamic_Append(self, request, response):
    self._file_content[request.filename()] = (
        self.get_content(request.filename()) + request.data())

  def _Dynamic_Read(self, request, response):
    content = self._file_content[request.filename()]
    pos = request.pos()
    response.set_data(content[pos:pos + request.max_bytes()])

  def _Dynamic_Stat(self, request, response):
    file_stat = response.add_stat()
    file_stat.set_length(len(self.get_content(request.filename())))
    file_stat.set_filename(request.filename())
    file_stat.set_content_type(file_service_pb.FileContentType.RAW)
    file_stat.set_finalized(True)
    response.set_more_files_found(False)

  def get_content(self, filename):
    """Get current in-memory file content."""
    return self._file_content.get(filename, '')

  def set_content(self, filename, content):
    """Set current in-memory file content."""
    self._file_content[filename] = content
