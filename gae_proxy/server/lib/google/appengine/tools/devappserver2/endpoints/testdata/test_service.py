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
"""Test service for regression testing of Cloud Endpoints support."""



import logging

import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote


class TestRequest(messages.Message):
  """Simple ProtoRPC request, for testing."""
  name = messages.StringField(1)
  number = messages.IntegerField(2)


class TestResponse(messages.Message):
  """Simple ProtoRPC response with a text field."""
  text = messages.StringField(1)


class TestDateTime(messages.Message):
  """Simple ProtoRPC request/response with a datetime."""
  datetime_value = message_types.DateTimeField(1)


class TestIntegers(messages.Message):
  """Simple ProtoRPC request/response with a few integer types."""
  var_int32 = messages.IntegerField(1, variant=messages.Variant.INT32)
  var_int64 = messages.IntegerField(2, variant=messages.Variant.INT64)
  var_repeated_int64 = messages.IntegerField(3, variant=messages.Variant.INT64,
                                             repeated=True)
  var_sint64 = messages.IntegerField(4, variant=messages.Variant.SINT64)
  var_uint64 = messages.IntegerField(5, variant=messages.Variant.UINT64)


class TestBytes(messages.Message):
  """Simple ProtoRPC request/response with a bytes field."""
  bytes_value = messages.BytesField(1)


my_api = endpoints.api(name='test_service', version='v1')


@my_api.api_class()
class TestService(remote.Service):
  """ProtoRPC test class for Cloud Endpoints."""

  @endpoints.method(message_types.VoidMessage, TestResponse,
                    http_method='GET', scopes=[])
  def test(self, unused_request):
    return TestResponse(text='Test response')

  @endpoints.method(message_types.VoidMessage, TestResponse,
                    http_method='GET', scopes=[])
  def empty_test(self, unused_request):
    return TestResponse()

  @endpoints.method(TestRequest, TestResponse,
                    http_method='POST', name='t2name', path='t2path',
                    scopes=[])
  def getenviron(self, request):
    return TestResponse(text='%s %d' % (request.name, request.number))

  @endpoints.method(message_types.DateTimeMessage,
                    message_types.DateTimeMessage,
                    http_method='POST', name='echodtmsg', scopes=[])
  def echo_datetime_message(self, request):
    return request

  @endpoints.method(TestDateTime, TestDateTime,
                    http_method='POST', name='echodtfield',
                    path='echo_dt_field', scopes=[])
  def echo_datetime_field(self, request):
    # Make sure we can access the fields of the datetime object.
    logging.info('Year %d, Month %d', request.datetime_value.year,
                 request.datetime_value.month)
    return request

  @endpoints.method(TestIntegers, TestIntegers, http_method='POST', scopes=[])
  def increment_integers(self, request):
    response = TestIntegers(
        var_int32=request.var_int32 + 1,
        var_int64=request.var_int64 + 1,
        var_repeated_int64=[val + 1 for val in request.var_repeated_int64],
        var_sint64=request.var_sint64 + 1,
        var_uint64=request.var_uint64 + 1)
    return response

  @endpoints.method(TestBytes, TestBytes, scopes=[])
  def echo_bytes(self, request):
    logging.info('Found bytes: %s', request.bytes_value)
    return request

  @endpoints.method(message_types.VoidMessage, message_types.VoidMessage,
                    path='empty_response', http_method='GET', scopes=[])
  def empty_response(self, unused_request):
    return message_types.VoidMessage()


@my_api.api_class(resource_name='extraname', path='extrapath')
class ExtraMethods(remote.Service):
  """Some extra test methods in the test API."""

  @endpoints.method(message_types.VoidMessage, TestResponse,
                    http_method='GET', name='test', path='test',
                    scopes=[])
  def test(self, unused_request):
    return TestResponse(text='Extra test response')


@endpoints.api(name='second_service', version='v1')
class SecondService(remote.Service):
  """Second test class for Cloud Endpoints."""

  @endpoints.method(message_types.VoidMessage, TestResponse,
                    http_method='GET', name='test_name', path='test',
                    scopes=[])
  def second_test(self, unused_request):
    """Test a second API, same version, same path.  Shouldn't collide."""
    return TestResponse(text='Second response')


application = endpoints.api_server([TestService, ExtraMethods, SecondService])
