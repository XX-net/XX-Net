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





"""ProspectiveSearch API.

A service that enables AppEngine apps to match queries to documents.

Functions defined in this module:
  subscribe: Add a query to set of matching queries.
  unsubscribe: Remove query from set of matching queries.
  get_subscription: Retrieves subscription with particular id.
  list_subscriptions: Lists subscriptions on a particular topic.
  list_topics: Lists topics that have subscriptions.
  match: Match all subscribed queries to document.
"""















__all__ = ['get_document',
           'get_subscription',
           'list_subscriptions',
           'list_topics',
           'match',
           'unsubscribe',
           'subscribe',
           'subscription_state_name',
           'DEFAULT_RESULT_BATCH_SIZE',
           'DEFAULT_LEASE_DURATION_SEC',
           'DEFAULT_LIST_SUBSCRIPTIONS_MAX_RESULTS',
           'DEFAULT_LIST_TOPICS_MAX_RESULTS',
           'DocumentTypeError',
           'Error',
           'QuerySyntaxError',
           'SchemaError',
           'SubscriptionDoesNotExist',
           'SubscriptionState',
           'TopicNotSpecified']


import base64
import sys

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore
from google.appengine.api import datastore_types
from google.appengine.api.prospective_search import error_pb
from google.appengine.api.prospective_search import prospective_search_admin
from google.appengine.api.prospective_search import prospective_search_pb
from google.appengine.runtime import apiproxy_errors
from google.appengine.datastore import entity_pb

DEFAULT_RESULT_BATCH_SIZE = 100
DEFAULT_LEASE_DURATION_SEC = 0
DEFAULT_LIST_SUBSCRIPTIONS_MAX_RESULTS = 1000
DEFAULT_LIST_TOPICS_MAX_RESULTS = 1000

_doc_class = prospective_search_pb.MatchRequest
_schema_type = prospective_search_pb.SchemaEntry
_entity_meaning = entity_pb.Property


class SubscriptionState:
  OK = 0
  PENDING = 1
  ERROR = 2
  _State_NAMES = {
    0: "OK",
    1: "PENDING",
    2: "ERROR",
  }


def subscription_state_name(x):
  return SubscriptionState._State_NAMES.get(x, "")


def _GetSchemaEntryForPropertyType(property_type):
  """Converts db.Model type to internal schema type."""

  from google.appengine.ext import db
  _MODEL_TYPE_TO_SCHEMA_ENTRY = {
      db.StringProperty: (_schema_type.STRING, None),
      db.IntegerProperty: (_schema_type.INT32, None),
      db.BooleanProperty: (_schema_type.BOOLEAN, None),
      db.FloatProperty: (_schema_type.DOUBLE, None),
      db.TextProperty: (_schema_type.STRING, None)
  }
  return _MODEL_TYPE_TO_SCHEMA_ENTRY.get(property_type, (None, None))


def _GetModelTypeForListPropertyType(property_type):
  """Converts (supported) db.ListProperty type to db.Model type."""
  from google.appengine.ext import db
  _LISTPROPERTY_TYPE_TO_SCHEMA_ENTRY = {
      basestring: db.StringProperty,
      str: db.StringProperty,
      unicode: db.StringProperty,
      bool: db.BooleanProperty,
      int: db.IntegerProperty,
      float: db.FloatProperty,
      db.Text: db.TextProperty,
  }
  return _LISTPROPERTY_TYPE_TO_SCHEMA_ENTRY.get(property_type, None)


def _GetModelTypeForEntityType(python_type):
  """Converts python built in type to db.Model type."""

  from google.appengine.ext import db
  _PYTHON_TYPE_TO_MODEL_TYPE = {
      basestring: db.StringProperty,
      str: db.StringProperty,
      unicode: db.StringProperty,
      int: db.IntegerProperty,
      bool: db.BooleanProperty,
      float: db.FloatProperty,
      db.Text: db.TextProperty,
  }
  return _PYTHON_TYPE_TO_MODEL_TYPE.get(python_type, None)


class Error(Exception):
  """Base error class for this module."""


class TopicNotSpecified(Error):
  def __str__(self):
    return 'Topic must be specified.'


class SubscriptionDoesNotExist(Error):
  """Subscription does not exist."""

  def __init__(self, topic, sub_id):
    Exception.__init__(self)
    self.topic = topic
    self.sub_id = sub_id

  def __str__(self):
    return "Subscription '%s' on topic '%s' does not exist." % (self.sub_id,
                                                                self.topic)


class DocumentTypeError(Error):
  """Document type is not supported."""

  def __str__(self):
    return 'Document type is not supported.'


class SchemaError(Error):
  """Schema error."""

  def __init__(self, detail):
    Exception.__init__(self)
    self.detail = detail

  def __str__(self):
    return 'SchemaError: %s' % self.detail


class QuerySyntaxError(Error):
  """Query syntax not valid error."""

  def __init__(self, topic, sub_id, query, detail):
    Exception.__init__(self)
    self.topic = topic
    self.sub_id = sub_id
    self.query = query
    self.detail = detail

  def __str__(self):
    return "QuerySyntaxError: topic:'%s' sub_id:'%s' query:'%s' detail:'%s'" % (
        self.topic, self.sub_id, self.query, self.detail)


def _get_document_topic(document, topic):
  if topic:
    return topic
  return document.kind()


def _make_sync_call(service, call, request, response):
  """The APIProxy entry point for a synchronous API call.

  Args:
    service: string representing which service to call
    call: string representing which function to call
    request: protocol buffer for the request
    response: protocol buffer for the response

  Returns:
    Response protocol buffer. Caller should always use returned value
    which may or may not be same as passed in 'response'.

  Raises:
    apiproxy_errors.Error:
  """

  resp = apiproxy_stub_map.MakeSyncCall(service, call, request, response)
  if resp is not None:
    return resp
  return response


def _add_schema_entry(model_type, name, add_entry):
  """Add single entry to SchemaEntries by invoking add_entry."""
  schema_type, entity_meaning = _GetSchemaEntryForPropertyType(model_type)
  if not schema_type:
    return
  entry = add_entry()
  entry.set_name(name)
  entry.set_type(schema_type)
  if entity_meaning:
    entry.set_meaning(entity_meaning)


def _entity_schema_to_prospective_search_schema(schema, add_entry):
  """Produce SchemaEntries from python schema.

  Args:
    schema: dictionary mapping python type to field names.
    add_entry: sink function for prospective search schema entries.

  Raises:
    SchemaError: schema is invalid.
  """
  all_names = []
  for python_type, names in schema.items():
    all_names.extend(names)
    for name in names:
      model_type = _GetModelTypeForEntityType(python_type)
      if not model_type:
        continue
      _add_schema_entry(model_type, name, add_entry)
  if len(all_names) != len(set(all_names)):
    duplicate_names = all_names
    for name in set(all_names):
      duplicate_names.remove(name)
    raise SchemaError('Duplicate names in schema: %s' % duplicate_names)


def _model_to_prospective_search_schema(model, add_entry):
  """Produce SchemaEntries from db.Model class."""

  from google.appengine.ext import db
  for name, model_property in model.properties().iteritems():
    model_class = model_property.__class__
    if issubclass(model_class, db.ListProperty):
      model_class = _GetModelTypeForListPropertyType(model_property.item_type)
    _add_schema_entry(model_class, name, add_entry)


def subscribe(document_class,
              query,
              sub_id,
              schema=None,
              topic=None,
              lease_duration_sec=DEFAULT_LEASE_DURATION_SEC):
  """Subscribe a query.

  If the document_class is a datastore.Entity, a schema must be specified to
  map document_class member names to the prospective_search supported types.
  For example, the datastore.Entity 'person' has the following schema:

  person = datastore.Entity('person')
  person['first_name'] = 'Andrew'
  person['surname'] = 'Smith'
  person['height'] = 150

  person_schema = {
    str : ['first_name', 'surname'],
    int : ['height'],
  }

  Args:
    document_class: datastore.Entity or db.Model class.
    query: str or unicode query for documents of type document_class.
    sub_id: subscription id returned when this subscription is matched.
    schema: required for datastore.Entity document_class.
    topic: required for datastore.Entity document_class, optional for db.Model.
        If not specified for db.Model, topic is assumed to be the class name.
        Only documents of same topic will be matched against this subscription.
    lease_duration_sec: minimum number of seconds subscription should exist.
        0 indicates subscription never expires (default).

  Raises:
    DocumentTypeError: document type is unsupported.
    TopicNotSpecified: raised for datastore.Entity if topic is not specified.
    QuerySyntaxError: raised when query is invalid or does not match schema.
    SchemaError: schema is invalid.
    apiproxy_errors.Error: subscribe call failed.
  """

  from google.appengine.ext import db

  request = prospective_search_pb.SubscribeRequest()
  request.set_sub_id(sub_id)
  request.set_vanilla_query(unicode(query).encode('utf-8'))
  request.set_lease_duration_sec(lease_duration_sec)


  if issubclass(document_class, db.Model):
    topic = _get_document_topic(document_class, topic)
    _model_to_prospective_search_schema(document_class,
                                        request.add_schema_entry)

  elif issubclass(document_class, datastore.Entity):
    if not topic:
      raise TopicNotSpecified()
    _entity_schema_to_prospective_search_schema(schema,
                                                request.add_schema_entry)
  else:
    raise DocumentTypeError()
  request.set_topic(topic)

  response = prospective_search_pb.SubscribeResponse()
  try:
    _make_sync_call('matcher', 'Subscribe', request, response)
  except apiproxy_errors.ApplicationError, e:
    if e.application_error is error_pb.Error.BAD_REQUEST:
      raise QuerySyntaxError(sub_id, topic, query, e.error_detail)
    raise e


def unsubscribe(document_class, sub_id, topic=None):
  """Unsubscribe a query.

  Args:
    document_class: datastore.Entity or db.Model class.
    sub_id: subscription id to remove.
    topic: required for datastore.Entity document_class, optional for db.Model.
        Topic must be same as used in the subscribe call for this subscription.

  Raises:
    DocumentTypeError: document type is unsupported.
    TopicNotSpecified: raised for datastore.Entity if topic is not specified.
    apiproxy_errors.Error: unsubscribe call failed.
  """

  from google.appengine.ext import db

  request = prospective_search_pb.UnsubscribeRequest()
  if issubclass(document_class, db.Model):
    topic = _get_document_topic(document_class, topic)
  elif issubclass(document_class, datastore.Entity):
    if not topic:
      raise TopicNotSpecified()
  else:
    raise DocumentTypeError()
  request.set_topic(topic)
  request.set_sub_id(sub_id)
  response = prospective_search_pb.UnsubscribeResponse()
  _make_sync_call('matcher', 'Unsubscribe', request, response)


def get_subscription(document_class, sub_id, topic=None):
  """Get subscription information.

  Args:
    document_class: datastore.Entity or db.Model class.
    sub_id: subscription id to lookup.
    topic: required for datastore.Entity document_class, optional for db.Model.

  Returns:
    Tuple containing:
        subscription id
        query
        expiration time (secs after the Unix epoch when subscription expires)
        state (SubscriptionState = OK/PENDING/ERROR)
        error_message (if state is ERROR)

   Raises:
    DocumentTypeError: document type is unsupported.
    SubscriptionDoesNotExist: if subscription of specified id does not exist.
    TopicNotSpecified: raised for datastore.Entity if topic is not specified.
    apiproxy_errors.Error: call failed.
  """
  subscriptions = list_subscriptions(document_class, sub_id, topic=topic,
                                     max_results=1)
  if len(subscriptions) and subscriptions[0][0] == sub_id:
    return subscriptions[0]
  raise SubscriptionDoesNotExist(topic, sub_id)


def list_subscriptions(document_class,
                       sub_id_start='',
                       topic=None,
                       max_results=DEFAULT_LIST_SUBSCRIPTIONS_MAX_RESULTS,
                       expires_before=None):
  """List subscriptions on a topic.

  Args:
    document_class: datastore.Entity or db.Model class.
    sub_id_start: return only subscriptions that are lexicographically equal or
        greater than the specified value.
    topic: required for datastore.Entity document_class, optional for db.Model.
    max_results: maximum number of subscriptions to return.
    expires_before: when set, limits list to subscriptions which will
        expire no later than expires_before (epoch time).
  Returns:
    List of subscription tuples. The subscription tuple contains:
        subscription id
        query
        expiration time (secs after the Unix epoch when subscription expires)
        state (SubscriptionState = OK/PENDING/ERROR)
        error_message (if state is ERROR)

  Raises:
    DocumentTypeError: document type is unsupported.
    TopicNotSpecified: raised for datastore.Entity if topic is not specified.
    apiproxy_errors.Error: list call failed.
  """


  from google.appengine.ext import db

  if issubclass(document_class, db.Model):
    topic = _get_document_topic(document_class, topic)
  elif issubclass(document_class, datastore.Entity):
    if not topic:
      raise TopicNotSpecified()
  else:
    raise DocumentTypeError()

  return prospective_search_admin.list_subscriptions(topic, max_results, None,
                                                     sub_id_start,
                                                     expires_before)


def list_topics(max_results=DEFAULT_LIST_TOPICS_MAX_RESULTS,
                topic_start=None):
  """List topics.

  Args:
    max_results: maximum number of topics to return.
    topic_start: if not None, start listing topics from this one.
  Returns:
    List of topics (strings)
  """
  return prospective_search_admin.list_topics(max_results,
                                              topic_start=topic_start)


def match(document,
          topic=None,
          result_key=None,
          result_relative_url='/_ah/prospective_search',
          result_task_queue='default',
          result_batch_size=DEFAULT_RESULT_BATCH_SIZE,
          result_return_document=True):
  """Match document with all subscribed queries on specified topic.

  Args:
    document: instance of datastore.Entity or db.Model document.
    topic: required for datastore.Entity, optional for db.Model.
        Only subscriptions of this topic will be matched against this document.
    result_key: key to return in result, potentially to identify document.
    result_relative_url: url of taskqueue event handler for results.
    result_task_queue: name of taskqueue queue to put batched results on.
    result_batch_size: number of subscription ids per taskqueue task batch.
    result_return_document: returns document with match results if true.

  Raises:
    DocumentTypeError: document type is unsupported.
    TopicNotSpecified: raised for datastore.Entity if topic is not specified.
    apiproxy_errors.Error: match call failed.
  """

  from google.appengine.ext import db

  request = prospective_search_pb.MatchRequest()
  if isinstance(document, db.Model):
    topic = _get_document_topic(document, topic)
    doc_pb = db.model_to_protobuf(document)
    if result_return_document:
      request.set_result_python_document_class(_doc_class.MODEL)
  elif isinstance(document, datastore.Entity):
    topic = _get_document_topic(document, topic)
    doc_pb = document.ToPb()
    if result_return_document:
      request.set_result_python_document_class(_doc_class.ENTITY)
  else:
    raise DocumentTypeError()
  request.set_topic(topic)
  request.mutable_document().CopyFrom(doc_pb)
  if result_key:
    request.set_result_key(result_key)
  request.set_result_relative_url(result_relative_url)
  request.set_result_task_queue(result_task_queue)
  request.set_result_batch_size(result_batch_size)
  response = prospective_search_pb.MatchResponse()
  _make_sync_call('matcher', 'Match', request, response)


def get_document(request):
  """Decodes document from prospective_search result POST request.

  Args:
    request: received POST request

  Returns:
    document: original datastore.Entity or db.Model document from match call.

  Raises:
    DocumentTypeError:
  """

  from google.appengine.ext import db

  doc_class = request.get('python_document_class')
  if not doc_class:
    return None
  entity = entity_pb.EntityProto()
  entity.ParseFromString(base64.urlsafe_b64decode(
      request.get('document').encode('utf-8')))
  doc_class = int(doc_class)
  if doc_class is _doc_class.ENTITY:
    return datastore.Entity('temp-kind').FromPb(entity)
  elif doc_class is _doc_class.MODEL:
    return db.model_from_protobuf(entity)
  else:
    raise DocumentTypeError()
