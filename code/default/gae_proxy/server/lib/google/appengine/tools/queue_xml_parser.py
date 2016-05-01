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
"""Performs translation of queue.xml to queue.yaml."""

from xml.etree import ElementTree

from google.appengine.tools import xml_parser_utils
from google.appengine.tools.app_engine_config_exception import AppEngineConfigException

PUSH_QUEUE_TAGS = (
    'rate', 'bucket-size', 'max-concurrent-requests', 'target')

PUSH_QUEUE_RETRY_PARAMS = (
    'task-age-limit',
    'min-backoff-seconds',
    'max-backoff-seconds',
    'max-doublings')

RETRY_PARAMETER_TAGS = ('task-retry-limit',) + PUSH_QUEUE_RETRY_PARAMS

BAD_MODE_ERROR_MESSAGE = (
    'Mode, if specified, must be either push or pull'
    ' (defaults to push) for queue entries. Bad value'
    " '%s' in <queue> entry with name '%s'")

PULL_QUEUE_ERROR_MESSAGE = (
    'The element <%s> is not defined for pull '
    "queues; bad <queue> entry with name '%s'")
RETRY_PARAM_ERROR_MESSAGE = (
    'The element <%s> in <retry-parameters> is not '
    "defined for pull queue with name '%s'")


def GetQueueYaml(unused_application, queue_xml_str):
  queue_xml = QueueXmlParser().ProcessXml(queue_xml_str)
  return queue_xml.ToYaml()


class QueueXmlParser(object):
  """Provides logic for walking down XML tree and pulling data."""

  def ProcessXml(self, xml_str):
    """Parses XML string and returns object representation of relevant info.

    Args:
      xml_str: The XML string.
    Returns:
      A QueueXml object containing information about task queue
      specifications from the XML.
    Raises:
      AppEngineConfigException: In case of malformed XML or illegal inputs.
    """

    try:
      self.errors = []
      xml_root = ElementTree.fromstring(xml_str)

      if xml_parser_utils.GetTag(xml_root) != 'queue-entries':
        raise AppEngineConfigException('Root tag must be <queue-entries>')

      self.queue_xml = QueueXml()
      self.queue_xml.queues = []
      self.queue_xml.total_storage_limit = xml_parser_utils.GetChildNodeText(
          xml_root, 'total-storage-limit')
      for child in xml_parser_utils.GetNodes(xml_root, 'queue'):
        self.ProcessQueueNode(child)

      if self.errors:
        raise AppEngineConfigException('\n'.join(self.errors))

      return self.queue_xml

    except ElementTree.ParseError as e:
      raise AppEngineConfigException('Bad input -- not valid XML: %s' % e)

  def ProcessQueueNode(self, node):
    """Processes XML <queue> nodes into Queue objects.

    The following information is parsed out:
      name
      mode: can be either push or pull
      retry-parameters:
        task-retry-limit
    ---- push queues only ----
        task-age-limit
        min-backoff-seconds
        max-back-off-seconds
        max-doubling
      bucket-size
      max-concurrent-requests
      rate: how often tasks are processed on this queue.
      target: version of application on which tasks on this queue will be
        invoked.
    ---- pull queues only ----
      acl: access control list - lists user and writer email addresses.

    Args:
      node: Current <queue> XML node being processed.
    """

    name = xml_parser_utils.GetChildNodeText(node, 'name')
    if not name:
      self.errors.append('Must specify a name for each <queue> entry')
      return


    mode = xml_parser_utils.GetChildNodeText(node, 'mode', 'push')

    if mode not in ('push', 'pull'):
      self.errors.append(BAD_MODE_ERROR_MESSAGE % (mode, name))
      return
    if mode == 'pull':
      queue = PullQueue()
      queue.name = name
      self._ProcessPullQueueNode(node, queue)
    else:
      queue = PushQueue()
      queue.name = name
      self._ProcessPushQueueNode(node, queue)

    self.queue_xml.queues.append(queue)

  def _ProcessPushQueueNode(self, node, queue):
    if xml_parser_utils.GetChild(node, 'acl') is not None:
      self.errors.append(
          'The element <acl> is not defined for push '
          "queues; bad <queue> entry with name '%s'" % queue.name)
    for tag in PUSH_QUEUE_TAGS:
      field_name = tag.replace('-', '_')
      setattr(queue, field_name, xml_parser_utils.GetChildNodeText(node, tag))
    self._ProcessRetryParametersNode(node, queue)

  def _ProcessPullQueueNode(self, node, queue):
    """Populates PullQueue-specific fields from parsed XML."""
    for tag in PUSH_QUEUE_TAGS:
      if xml_parser_utils.GetChild(node, tag) is not None:
        self.errors.append(PULL_QUEUE_ERROR_MESSAGE % (tag, queue.name))

    acl_node = xml_parser_utils.GetChild(node, 'acl')

    if acl_node is not None:
      queue.acl = Acl()
      queue.acl.user_emails = [
          sub_node.text for sub_node in
          xml_parser_utils.GetNodes(acl_node, 'user-email')]
      queue.acl.writer_emails = [
          sub_node.text for sub_node in
          xml_parser_utils.GetNodes(acl_node, 'writer-email')]
    else:
      queue.acl = None

    self._ProcessRetryParametersNode(node, queue)

  def _ProcessRetryParametersNode(self, node, queue):
    """Pulls information out of <retry-parameters> node."""
    retry_parameters_node = xml_parser_utils.GetChild(
        node, 'retry-parameters')
    if retry_parameters_node is None:
      queue.retry_parameters = None
      return
    retry_parameters = RetryParameters()
    queue.retry_parameters = retry_parameters
    retry_parameters.task_retry_limit = xml_parser_utils.GetChildNodeText(
        retry_parameters_node, 'task-retry-limit')

    for tag in PUSH_QUEUE_RETRY_PARAMS:

      if xml_parser_utils.GetChild(retry_parameters_node, tag) is not None:
        if isinstance(queue, PullQueue):
          self.errors.append(RETRY_PARAM_ERROR_MESSAGE % (tag, queue.name))
        else:
          setattr(
              retry_parameters,
              tag.replace('-', '_'),
              xml_parser_utils.GetChildNodeText(retry_parameters_node, tag))


class QueueXml(object):

  def __init__(self):
    self.queues = []
    self.total_storage_limit = None

  def ToYaml(self):
    statements = []
    if self.total_storage_limit:
      statements.append('total_storage_limit: %s\n' % self.total_storage_limit)
    statements.append('queue:')
    for queue in self.queues:
      statements += queue.GetYamlStatementsList()

    return '\n'.join(statements) + '\n'


class Queue(object):

  def GetYamlStatementsList(self):
    statements = ['- name: %s' % self.name]
    statements += self.GetAdditionalYamlStatementsList()

    if self.retry_parameters:
      statements += self.retry_parameters.GetYamlStatementsList()

    return statements


class PushQueue(Queue):

  def GetAdditionalYamlStatementsList(self):
    statements = ['  mode: push']
    fields = (tag.replace('-', '_') for tag in PUSH_QUEUE_TAGS)
    for field in fields:
      field_value = getattr(self, field)
      if field_value:
        statements.append('  %s: %s' % (field, field_value))

    return statements


class PullQueue(Queue):

  def GetAdditionalYamlStatementsList(self):
    statements = ['  mode: pull']
    if self.acl:
      statements += self.acl.GetYamlStatementsList()
    return statements


class Acl(object):

  def GetYamlStatementsList(self):
    statements = ['  acl:']
    statements += ['  - user_email: %s' % user_email for user_email in
                   self.user_emails]
    statements += ['  - writer_email: %s' % writer_email for writer_email in
                   self.writer_emails]
    return statements


class RetryParameters(object):

  def GetYamlStatementsList(self):
    statements = ['  retry_parameters:']
    field_names = (tag.replace('-', '_') for tag in RETRY_PARAMETER_TAGS)
    for field in field_names:
      field_value = getattr(self, field, None)
      if field_value:
        statements.append('    %s: %s' % (field, field_value))
    return statements
