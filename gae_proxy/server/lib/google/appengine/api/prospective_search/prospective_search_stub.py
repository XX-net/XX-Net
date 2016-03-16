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




"""In-memory persistent prospective_search API stub for dev_appserver."""








import base64
import bisect


import cPickle as pickle
import itertools
import logging
import os
import re
import time
import urllib

from google.appengine.api import apiproxy_stub
from google.appengine.api.prospective_search import error_pb
from google.appengine.api.prospective_search import prospective_search_pb
from google.appengine.api.search import query_parser
from google.appengine.api.search import QueryParser
from google.appengine.api.taskqueue import taskqueue_service_pb
from google.appengine.runtime import apiproxy_errors


def ValidateSubscriptionId(sub_id):
  if not sub_id:
    RaiseBadRequest('Invalid subscription id.')


def ValidateTopic(topic):
  if not topic:
    RaiseBadRequest('Invalid topic.')


def ValidateQuery(query):
  parser_return = query_parser.Parse(unicode(query, 'utf-8'))
  if parser_return.tree and parser_return.tree.getType() is QueryParser.EMPTY:
    raise query_parser.QueryException('Empty query.')


def RaiseBadRequest(message):
  raise apiproxy_errors.ApplicationError(error_pb.Error.BAD_REQUEST, message)


class ProspectiveSearchStub(apiproxy_stub.APIProxyStub):
  """Python only Prospective Search service stub."""

  def __init__(self, prospective_search_path, taskqueue_stub,
               service_name='matcher', openfile=open):
    """Initializer.

    Args:
      prospective_search_path: path for file that persists subscriptions.
      taskqueue_stub: taskqueue service stub for returning results.
      service_name: Service name expected for all calls.
      openfile: function to open the pickled subscription state.
    """
    super(ProspectiveSearchStub, self).__init__(service_name)
    self.prospective_search_path = prospective_search_path
    self.taskqueue_stub = taskqueue_stub
    self.topics = {}
    self.topics_schema = {}
    if os.path.isfile(self.prospective_search_path):
      stream = openfile(self.prospective_search_path, 'rb')

      stream.seek(0, os.SEEK_END)
      if stream.tell() != 0:
        stream.seek(0)
        self.topics, self.topics_schema = pickle.load(stream)

  def _Write(self, openfile=open):
    """Persist subscriptions."""
    persisted = openfile(self.prospective_search_path, 'wb')
    pickle.dump((self.topics, self.topics_schema), persisted)
    persisted.close()

  def _Get_Schema(self, schema_entries):
    """Converts a schema list to a schema dictionary.

    Args:
      schema_entries: list of SchemaEntry entries.
    Returns:
      Dictionary mapping field names to SchemaEntry types.
    """
    schema = {}
    for entry in schema_entries:
      schema[entry.name()] = entry.type()
    return schema

  def _Dynamic_Subscribe(self, request, response):
    """Subscribe a query.

    Args:
      request: SubscribeRequest
      response: SubscribeResponse (not used)
    """
    ValidateSubscriptionId(request.sub_id())
    ValidateTopic(request.topic())

    ValidateQuery(request.vanilla_query())
    schema = self._Get_Schema(request.schema_entry_list())
    self.topics_schema[request.topic()] = schema
    if request.lease_duration_sec() == 0:
      expires = time.time() + 0xffffffff
    else:
      expires = time.time() + request.lease_duration_sec()
    topic_subs = self.topics.setdefault(request.topic(), {})
    topic_subs[request.sub_id()] = (request.vanilla_query(), expires)
    self._Write()


  def _Dynamic_Unsubscribe(self, request, response):
    """Unsubscribe a query.

    Args:
      request: UnsubscribeRequest
      response: UnsubscribeResponse (not used)
    """
    ValidateSubscriptionId(request.sub_id())
    ValidateTopic(request.topic())
    try:
      del self.topics[request.topic()][request.sub_id()]
    except KeyError:
      pass
    self._Write()

  def _ExpireSubscriptions(self):
    """Remove expired subscriptions."""
    now = time.time()
    empty_topics = []
    for topic, topic_subs in self.topics.iteritems():
      expired_sub_ids = []
      for sub_id, entry in topic_subs.iteritems():
        _, expires = entry
        if expires < now:
          expired_sub_ids.append(sub_id)
      for sub_id in expired_sub_ids:
        del topic_subs[sub_id]
      if len(topic_subs) == 0:
        empty_topics.append(topic)
    for topic in empty_topics:
      del self.topics[topic]

  def _Dynamic_ListSubscriptions(self, request, response):
    """List subscriptions.

    Args:
      request: ListSubscriptionsRequest
      response: ListSubscriptionsResponse
    """
    ValidateTopic(request.topic())
    self._ExpireSubscriptions()
    topic_subs = self.topics.get(request.topic(), {})
    sub_ids = topic_subs.keys()
    sub_ids.sort()
    start = bisect.bisect_left(sub_ids, request.subscription_id_start())
    sub_ids = sub_ids[start:start + request.max_results()]
    for sub_id in sub_ids:
      vanilla_query, expires = topic_subs[sub_id]
      if request.has_expires_before() and expires > request.expires_before():
        continue
      record = response.add_subscription()
      record.set_id(sub_id)
      record.set_vanilla_query(vanilla_query)
      record.set_expiration_time_sec(expires)
      record.set_state(prospective_search_pb.SubscriptionRecord.OK)

  def _Dynamic_ListTopics(self, request, response):
    """List topics.

    Args:
      request: ListTopicsRequest
      response: ListTopicsResponse
    """
    topics = self.topics.keys()
    topics.sort()
    if request.has_topic_start():
      start = bisect.bisect_left(topics, request.topic_start())
    else:
      start = 0

    iter_topics = topics[start:start + request.max_results()]
    for topic in iter_topics:
      response.topic_list().append(topic)

  def _DeliverMatches(self, subscriptions, match_request):
    """Deliver list of subscriptions as batches using taskqueue.

    Args:
      subscriptions: list of subscription ids
      match_request: MatchRequest
    """
    parameters = {'topic': match_request.topic()}
    if match_request.has_result_python_document_class():
      python_document_class = match_request.result_python_document_class()
      parameters['python_document_class'] = python_document_class
      parameters['document'] = base64.urlsafe_b64encode(
          match_request.document().Encode())
    if match_request.has_result_key():
      parameters['key'] = match_request.result_key()
    taskqueue_request = taskqueue_service_pb.TaskQueueBulkAddRequest()
    batch_size = match_request.result_batch_size()
    for i in xrange(0, len(subscriptions), batch_size):
      add_request = taskqueue_request.add_add_request()
      add_request.set_queue_name(match_request.result_task_queue())
      add_request.set_task_name('')
      add_request.set_eta_usec(0)
      add_request.set_url(match_request.result_relative_url())
      add_request.set_description('prospective_search::matches')
      header = add_request.add_header()
      header.set_key('content-type')
      header.set_value('application/x-www-form-urlencoded; charset=utf-8')
      parameters['results_count'] = len(subscriptions)
      parameters['results_offset'] = i
      parameters['id'] = subscriptions[i:i+batch_size]
      add_request.set_body(urllib.urlencode(parameters, doseq=True))
    taskqueue_response = taskqueue_service_pb.TaskQueueBulkAddResponse()
    self.taskqueue_stub._Dynamic_BulkAdd(taskqueue_request, taskqueue_response)

  def _Dynamic_Match(self, request, response):
    """Match a document.

    Args:
      request: MatchRequest
      response: MatchResponse (not used)
    """
    self._ExpireSubscriptions()
    doc = {}
    properties = itertools.chain(request.document().property_list(),
                                 request.document().raw_property_list())
    for prop in properties:

      prop_name = unicode(prop.name(), 'utf-8')
      doc.setdefault(prop_name, [])
      if prop.value().has_int64value():
        value = prop.value().int64value()

        if (value < 2**32) and (value >= -2**32):
          doc[prop_name].append(prop.value().int64value())
      elif prop.value().has_stringvalue():

        unicode_value = unicode(prop.value().stringvalue(), 'utf-8')
        doc[prop_name].append(unicode_value)
      elif prop.value().has_doublevalue():
        doc[prop_name].append(prop.value().doublevalue())
      elif prop.value().has_booleanvalue():
        doc[prop_name].append(prop.value().booleanvalue())

    matches = []
    topic_subs = self.topics.get(request.topic(), {})
    sub_ids = topic_subs.keys()
    for sub_id in sub_ids:
      vanilla_query, _ = topic_subs[sub_id]
      if self._FindMatches(vanilla_query, doc):
        matches.append(sub_id)
    if matches:
      self._DeliverMatches(matches, request)

  def _FindMatches(self, query, doc):
    """Entry point for matching document against a query."""
    self._Debug('_FindMatches: query: %r, doc: %s' % (query, doc), 0)
    query_tree = self._Simplify(query_parser.Parse(unicode(query, 'utf-8')))
    match = self._WalkQueryTree(query_tree, doc)
    self._Debug('_FindMatches: result: %s' % match, 0)
    return match

  def ExtractGlobalEq(self, node):
    if node.getType() == QueryParser.EQ and len(node.children) >= 2:
      if node.children[0].getType() == QueryParser.GLOBAL:
        return node.children[1]
    return node

  def _WalkQueryTree(self, query_node, doc, query_field=None, level=0):
    """Recursive match of doc from query tree at the given node."""
    query_type = query_node.getType()
    query_text = query_node.getText()

    self._Debug('_WalkQueryTree: query type: %r, field: %r, text: %r'
                % (query_type, query_field, query_text), level=level)

    if query_type is QueryParser.CONJUNCTION:
      for child in query_node.children:
        if not self._WalkQueryTree(
            self.ExtractGlobalEq(child), doc, query_field, level=level + 1):
          return False
      return True

    elif query_type is QueryParser.DISJUNCTION:
      for child in query_node.children:
        if self._WalkQueryTree(
            self.ExtractGlobalEq(child), doc, query_field, level=level + 1):
          return True

    if query_type is QueryParser.NEGATION:
      self._Debug(('No such field so no match: field: %r, children: %r'
                   % (query_type, query_node.children[0])),
                  level)
      child = query_node.children[0]
      return not self._WalkQueryTree(
          self.ExtractGlobalEq(child), doc, query_field, level=level + 1)

    elif query_type is QueryParser.HAS:
      if query_node.children[0].getType() is not QueryParser.GLOBAL:
        query_field = query_node.children[0].getText()
        if query_field not in doc:
          self._Debug(('No such field so no match: field: %r' % query_field),
                      level)
          return False
      return self._WalkQueryTree(query_node.children[1], doc, query_field,
                                 level=level + 1)

    elif query_type is QueryParser.VALUE or query_type is QueryParser.TEXT:
      if query_parser.IsPhrase(query_node):
        query_text = query_parser.GetQueryNodeTextUnicode(query_node)
      if query_field is not None:
        return self._MatchField(doc, query_field, query_text, level=level)

      for field_name in doc:
        if self._MatchField(doc, field_name, query_text, level=level):
          return True

    elif query_type in query_parser.COMPARISON_TYPES:
      query_field = query_node.children[0].getText()
      query_text = query_node.children[1].getText()
      if query_field is not None:
        if query_field not in doc:
          self._Debug(('No such field so no match: field: %r' % query_field),
                      level)
          return False
        return self._MatchField(doc, query_field, query_text, query_type,
                                level=level)
      for field_name in doc:
        if self._MatchField(doc, field_name, query_text, query_type,
                            level=level):
          return True


    self._Debug('Fallthrough at %s returning false, query_node.children: %s'
                % (query_text, [n.getText() for n in query_node.children]),
                level)
    return False

  def _MatchField(self, doc, field_name, query_val, op=QueryParser.HAS,
                  level=0):
    """Returns true iff 'doc[field_name] op query_val' evaluates to true."""
    field_vals = doc[field_name]
    if type(field_vals) is not list:
      field_vals = list(field_vals)

    self._Debug('_MatchField: doc[%s]: %r %s %r'
                % (field_name, field_vals, op, query_val), level)

    if (op is QueryParser.HAS
        or (op is QueryParser.EQ
            and type(field_vals[0]) is unicode)):


      if query_val.startswith('"') and query_val.endswith('"'):
        query_val = query_val[1:-1]
      query_val = re.sub(r'\s+', r'\s+', query_val)
      re_query = re.compile(u'(^\\s*|\\s+)%s(\\s+|\\s*$)'
                            % query_val, re.IGNORECASE)
      for val in field_vals:
        value_text = ('%s' % val)
        if re_query.search(value_text):
          return True
    elif op is QueryParser.EQ:
      for val in field_vals:
        if (type(val) is int) or (type(val) is float):
          if val == float(query_val):
            return True
        elif type(val) is bool:
          query_bool = re.match('(?i)true', query_val) is not None
          if val == bool(query_bool):
            return True
    else:
      query_num = float(query_val)
      if op is QueryParser.GT:
        for val in field_vals:
          if val > query_num: return True
      elif op is QueryParser.GE:
        for val in field_vals:
          if val >= query_num: return True
      elif op is QueryParser.LESSTHAN:
        for val in field_vals:
          if val < query_num: return True
      elif op is QueryParser.LE:
        for val in field_vals:
          if val <= query_num: return True

    return False





  def _Simplify(self, parser_return):
    """Simplifies the output of the parser."""
    if parser_return.tree:
      return self._SimplifyNode(query_parser.SimplifyNode(parser_return.tree))
    return parser_return

  def _SimplifyNode(self, node):
    """Simplifies the node removing singleton conjunctions and others."""
    if not node.getType():
      return self._SimplifyNode(node.children[0])
    elif (node.getType() in query_parser.COMPARISON_TYPES
          and node.getChildCount() is 2
          and node.children[0].getType() is QueryParser.GLOBAL):
      return self._SimplifyNode(node.children[1])
    elif node.getType() is QueryParser.SEQUENCE:
      return self._SimplifyNode(query_parser.SequenceToConjunction(node))
    elif (node.getType() is QueryParser.VALUE
          and node.getChildCount() is 2 and
          (node.children[0].getType() is QueryParser.TEXT or
           node.children[0].getType() is QueryParser.STRING or
           node.children[0].getType() is QueryParser.NUMBER)):
      return self._SimplifyNode(node.children[1])
    elif (node.getType() is QueryParser.EQ and
          (node.children[0].getType() is QueryParser.CONJUNCTION
           or node.children[0].getType() is QueryParser.DISJUNCTION)):
      return self._SimplifyNode(node.children[0])
    for i, child in enumerate(node.children):
      node.setChild(i, self._SimplifyNode(child))
    return node

  def _Debug(self, msg, level):
    """Helper method to print out indented messages."""
    logging.info('%s%s', ''.join(' ' for _ in range(level)), msg)
