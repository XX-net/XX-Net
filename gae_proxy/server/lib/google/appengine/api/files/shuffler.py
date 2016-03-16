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

Files API Shuffler interface"""



import logging

from google.appengine.api.files import file as files
from google.appengine.api.files import blobstore
from google.appengine.api.files import file_service_pb
from google.appengine.runtime import apiproxy_errors

__all__ = [
           'shuffle',
           'available',
           ]


class ShufflerUnavailableError(files.Error):
  """Shuffler service is not available."""


def shuffle(job_name,
            input_file_list,
            output_file_list,
            callback):
  """Shuffle mapreduce files using the shuffler service.

  Args:
    job_name: unique shuffle job name as string.
    input_file_list: list of files api file names to shuffle. Files should be
      in records format with serialized KeyValue protocol buffer as record.
    output_file_list: list of files api file names to store shuffle result.
      Files should not be finalized. They will be of records format with
      serialized KeyValues protocol buffer as record.
    callback: shuffle service call back specification. Can be either
      url - the task in default queue with default parameters will be enqueued.
      It can also be a dict with following keys:
        url: url to call back
        version: app version to call
        method: HTTP method to use (POST or GET)
        queue: queue name to enqueue a task in.
  Raises:
    ShufflerUnavailableError if shuffler service is not available.
  """
  if not available():
    raise ShufflerUnavailableError()

  request = file_service_pb.ShuffleRequest()
  response = file_service_pb.ShuffleResponse()

  request.set_shuffle_name(job_name)

  if isinstance(callback, dict):
    request.mutable_callback().set_url(callback["url"])
    if "version" in callback:
      request.mutable_callback().set_app_version_id(callback["version"])
    if "method" in callback:
      request.mutable_callback().set_method(callback["method"])
    if "queue" in callback:
      request.mutable_callback().set_queue(callback["queue"])
  else:
    request.mutable_callback().set_url(callback)


  request.set_shuffle_size_bytes(0)

  for file_name in input_file_list:
    shuffle_input = request.add_input()
    shuffle_input.set_format(
        file_service_pb.ShuffleEnums.RECORDS_KEY_VALUE_PROTO_INPUT)
    shuffle_input.set_path(file_name)

  shuffle_output = request.mutable_output()
  shuffle_output.set_format(
      file_service_pb.ShuffleEnums.RECORDS_KEY_MULTI_VALUE_PROTO_OUTPUT)
  for file_name in output_file_list:
    shuffle_output.add_path(file_name)

  files._make_call("Shuffle", request, response)


def available():
  """Determine if shuffler service is available for the app.

  Returns:
    True if shuffler service is available, False otherwise.
  """
  return False
