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




"""Define the DeadlineExceededError exception."""





try:
  BaseException
except NameError:
  BaseException = Exception


class DeadlineExceededError(BaseException):
  """Exception raised when the request reaches its overall time limit.

  This exception will be thrown by the original thread handling the request,
  shortly after the request reaches its deadline. Since the exception is
  asynchronously set on the thread by the App Engine runtime, it can appear
  to originate from any line of code that happens to be executing at that
  time.

  If the application catches this exception and does not generate a response
  very quickly afterwards, an error will be returned to the user and
  the application instance may be terminated.

  Not to be confused with runtime.apiproxy_errors.DeadlineExceededError.
  That one is raised when individual API calls take too long.
  """

  def __str__(self):
    return ('The overall deadline for responding to the HTTP request '
            'was exceeded.')
