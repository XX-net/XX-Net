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





"""ProspectiveSearch Admin API.

Admin functions (private to this module) for prospective search.

Functions defined in this module:
  list_subscriptions: Lists subscriptions, for a specified app_id and topic.
  list_topics: Lists topics that have subscriptions, for a specified app_id.
"""






from google.appengine.api import apiproxy_stub_map
from google.appengine.api.prospective_search import prospective_search_pb


def list_subscriptions(topic,
                       max_results,
                       app_id=None,
                       sub_id_start=None,
                       expires_before=None):
  """List subscriptions on a topic.

  Args:
    topic: required for datastore.Entity document_class, optional for db.Model.
    max_results: maximum number of subscriptions to return.
    app_id: if not None, use this app_id.
    sub_id_start: return only subscriptions that are lexicographically equal or
        greater than the specified value.
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

  request = prospective_search_pb.ListSubscriptionsRequest()
  if app_id:
    request.set_app_id(app_id)
  request.set_topic(topic)
  request.set_subscription_id_start(sub_id_start)
  request.set_max_results(max_results)
  if expires_before:
    request.set_expires_before(expires_before)
  response = prospective_search_pb.ListSubscriptionsResponse()
  apiproxy_stub_map.MakeSyncCall('matcher', 'ListSubscriptions',
                                 request, response)
  subscriptions = []
  for sub in response.subscription_list():
    subscriptions.append((sub.id(),
                          sub.vanilla_query(),
                          sub.expiration_time_sec(),
                          sub.state(),
                          sub.error_message()))
  return subscriptions


def list_topics(max_results, app_id=None, topic_start=None):
  """List topics, over-riding app_id.

  Args:
    max_results: maximum number of topics to return.
    app_id: if not None, use this app_id.
    topic_start: if not None, start listing topics from this one.
  Returns:
    List of topics (strings), or an empty list if the caller is not an
      administrator and the app_id does not match the app_id of the application.
  """

  request = prospective_search_pb.ListTopicsRequest()
  request.set_max_results(max_results)
  if app_id:
    request.set_app_id(app_id)
  if topic_start:
    request.set_topic_start(topic_start)
  response = prospective_search_pb.ListTopicsResponse()

  resp = apiproxy_stub_map.MakeSyncCall('matcher', 'ListTopics',
                                        request, response)
  if resp is not None:
    response = resp

  topics = []
  for topic in response.topic_list():
    topics.append(topic)
  return topics
