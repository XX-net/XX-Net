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
"""Stub implementation for Log Service that uses sqlite."""

import atexit
import codecs
import logging
import time

import sqlite3

from google.appengine.api import apiproxy_stub
from google.appengine.api import appinfo
from google.appengine.api.logservice import log_service_pb
from google.appengine.runtime import apiproxy_errors


_REQUEST_LOG_CREATE = """
CREATE TABLE IF NOT EXISTS RequestLogs (
  id INTEGER NOT NULL PRIMARY KEY,
  user_request_id TEXT NOT NULL,
  app_id TEXT NOT NULL,
  version_id TEXT NOT NULL,
  module TEXT NOT NULL,
  ip TEXT NOT NULL,
  nickname TEXT NOT NULL,
  start_time INTEGER NOT NULL,
  end_time INTEGER DEFAULT 0 NOT NULL,
  method TEXT NOT NULL,
  resource TEXT NOT NULL,
  http_version TEXT NOT NULL,
  status INTEGER DEFAULT 0 NOT NULL,
  response_size INTEGER DEFAULT 0 NOT NULL,
  user_agent TEXT NOT NULL,
  url_map_entry TEXT DEFAULT '' NOT NULL,
  host TEXT NOT NULL,
  task_queue_name TEXT DEFAULT '' NOT NULL,
  task_name TEXT DEFAULT '' NOT NULL,
  latency INTEGER DEFAULT 0 NOT NULL,
  mcycles INTEGER DEFAULT 0 NOT NULL,
  finished INTEGER DEFAULT 0 NOT NULL
);
"""

_REQUEST_LOG_ADD_MODULE_COLUMN = """
ALTER TABLE RequestLogs
  ADD COLUMN module TEXT DEFAULT '%s' NOT NULL;
""" % appinfo.DEFAULT_MODULE

_APP_LOG_CREATE = """
CREATE TABLE IF NOT EXISTS AppLogs (
  id INTEGER NOT NULL PRIMARY KEY,
  request_id INTEGER NOT NULL,
  timestamp INTEGER NOT NULL,
  level INTEGER NOT NULL,
  message TEXT NOT NULL,
  FOREIGN KEY(request_id) REFERENCES RequestLogs(id)
);
"""


class LogServiceStub(apiproxy_stub.APIProxyStub):
  """Python stub for Log Service service."""

  THREADSAFE = True

  _ACCEPTS_REQUEST_ID = True


  _DEFAULT_READ_COUNT = 20


  _MIN_COMMIT_INTERVAL = 5

  def __init__(self, persist=False, logs_path=None, request_data=None):
    """Initializer.

    Args:
      persist: For backwards compatability. Has no effect.
      logs_path: A str containing the filename to use for logs storage. Defaults
        to in-memory if unset.
      request_data: A apiproxy_stub.RequestData instance used to look up state
        associated with the request that generated an API call.
    """

    super(LogServiceStub, self).__init__('logservice',
                                         request_data=request_data)
    self._request_id_to_request_row_id = {}
    if logs_path is None:
      logs_path = ':memory:'
    self._conn = sqlite3.connect(logs_path, check_same_thread=False)
    self._conn.row_factory = sqlite3.Row
    self._conn.execute(_REQUEST_LOG_CREATE)
    self._conn.execute(_APP_LOG_CREATE)

    column_names = set(c['name'] for c in
                       self._conn.execute('PRAGMA table_info(RequestLogs)'))
    if 'module' not in column_names:
      self._conn.execute(_REQUEST_LOG_ADD_MODULE_COLUMN)

    self._last_commit = time.time()
    atexit.register(self._conn.commit)

  @staticmethod
  def _get_time_usec():
    return int(time.time() * 1e6)

  def _maybe_commit(self):
    now = time.time()
    if (now - self._last_commit) > self._MIN_COMMIT_INTERVAL:
      self._conn.commit()
      self._last_commit = now

  @apiproxy_stub.Synchronized
  def start_request(self, request_id, user_request_id, ip, app_id, version_id,
                    nickname, user_agent, host, method, resource, http_version,
                    start_time=None, module=None):
    """Starts logging for a request.

    Each start_request call must be followed by a corresponding end_request call
    to cleanup resources allocated in start_request.

    Args:
      request_id: A unique string identifying the request associated with the
        API call.
      user_request_id: A user-visible unique string for retrieving the request
        log at a later time.
      ip: The user's IP address.
      app_id: A string representing the application ID that this request
        corresponds to.
      version_id: A string representing the version ID that this request
        corresponds to.
      nickname: A string representing the user that has made this request (that
        is, the user's nickname, e.g., 'foobar' for a user logged in as
        'foobar@gmail.com').
      user_agent: A string representing the agent used to make this request.
      host: A string representing the host that received this request.
      method: A string containing the HTTP method of this request.
      resource: A string containing the path and query string of this request.
      http_version: A string containing the HTTP version of this request.
      start_time: An int containing the start time in micro-seconds. If unset,
        the current time is used.
      module: The string name of the module handling this request.
    """
    if module is None:
      module = appinfo.DEFAULT_MODULE
    if version_id is None:
      version_id = 'NO-VERSION'
    major_version_id = version_id.split('.', 1)[0]
    if start_time is None:
      start_time = self._get_time_usec()
    cursor = self._conn.execute(
        'INSERT INTO RequestLogs (user_request_id, ip, app_id, version_id, '
        'nickname, user_agent, host, start_time, method, resource, '
        'http_version, module)'
        ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (
            user_request_id, ip, app_id, major_version_id, nickname, user_agent,
            host, start_time, method, resource, http_version, module))
    self._request_id_to_request_row_id[request_id] = cursor.lastrowid
    self._maybe_commit()

  @apiproxy_stub.Synchronized
  def end_request(self, request_id, status, response_size, end_time=None):
    """Ends logging for a request.

    Args:
      request_id: A unique string identifying the request associated with the
        API call.
      status: An int containing the HTTP status code for this request.
      response_size: An int containing the content length of the response.
      end_time: An int containing the end time in micro-seconds. If unset, the
        current time is used.
    """
    row_id = self._request_id_to_request_row_id.pop(request_id, None)
    if not row_id:
      return
    if end_time is None:
      end_time = self._get_time_usec()
    self._conn.execute(
        'UPDATE RequestLogs SET '
        'status = ?, response_size = ?, end_time = ?, finished = 1 '
        'WHERE id = ?', (
            status, response_size, end_time, row_id))
    self._maybe_commit()

  def _Dynamic_Flush(self, request, unused_response, request_id):
    """Writes application-level log messages for a request."""
    group = log_service_pb.UserAppLogGroup(request.logs())
    self._insert_app_logs(request_id, group.log_line_list())

  @apiproxy_stub.Synchronized
  def _insert_app_logs(self, request_id, log_lines):
    row_id = self._request_id_to_request_row_id.get(request_id)
    if row_id is None:
      return
    new_app_logs = (self._tuple_from_log_line(row_id, log_line)
                    for log_line in log_lines)
    self._conn.executemany(
        'INSERT INTO AppLogs (request_id, timestamp, level, message) VALUES '
        '(?, ?, ?, ?)', new_app_logs)
    self._maybe_commit()

  @staticmethod
  def _tuple_from_log_line(row_id, log_line):
    message = log_line.message()
    if isinstance(message, str):
      message = codecs.decode(message, 'utf-8', 'replace')
    return (row_id, log_line.timestamp_usec(), log_line.level(), message)

  @apiproxy_stub.Synchronized
  def _Dynamic_Read(self, request, response, request_id):
    if (request.module_version_size() < 1 and
        request.version_id_size() < 1 and
        request.request_id_size() < 1):
      raise apiproxy_errors.ApplicationError(
          log_service_pb.LogServiceError.INVALID_REQUEST)

    if request.module_version_size() > 0 and request.version_id_size() > 0:
      raise apiproxy_errors.ApplicationError(
          log_service_pb.LogServiceError.INVALID_REQUEST)

    if (request.request_id_size() and
        (request.has_start_time() or request.has_end_time() or
         request.has_offset())):
      raise apiproxy_errors.ApplicationError(
          log_service_pb.LogServiceError.INVALID_REQUEST)

    if request.request_id_size():
      for request_id in request.request_id_list():
        log_row = self._conn.execute(
            'SELECT * FROM RequestLogs WHERE user_request_id = ?',
            (request_id,)).fetchone()
        if log_row:
          log = response.add_log()
          self._fill_request_log(log_row, log, request.include_app_logs())
      return

    if request.has_count():
      count = request.count()
    else:
      count = self._DEFAULT_READ_COUNT
    filters, values = self._extract_read_filters(request)
    filter_string = ' WHERE %s' % ' and '.join(filters)

    if request.has_minimum_log_level():
      query = ('SELECT * FROM RequestLogs INNER JOIN AppLogs ON '
               'RequestLogs.id = AppLogs.request_id%s GROUP BY '
               'RequestLogs.id ORDER BY id DESC')
    else:
      query = 'SELECT * FROM RequestLogs%s ORDER BY id DESC'
    logs = self._conn.execute(query % filter_string,
                              values).fetchmany(count + 1)
    if logging.getLogger(__name__).isEnabledFor(logging.DEBUG):
      self._debug_query(filter_string, values, len(logs))
    for log_row in logs[:count]:
      log = response.add_log()
      self._fill_request_log(log_row, log, request.include_app_logs())
    if len(logs) > count:
      response.mutable_offset().set_request_id(str(logs[-2]['id']))

  def _debug_query(self, filter_string, values, result_count):
    logging.debug('\n\n')
    logging.debug(filter_string)
    logging.debug(values)
    logging.debug('%d results.', result_count)
    logging.debug('DB dump:')
    for l in self._conn.execute('SELECT * FROM RequestLogs'):
      logging.debug('%r %r %d %d %s', l['module'], l['version_id'],
                    l['start_time'], l['end_time'],
                    l['finished'] and 'COMPLETE' or 'INCOMPLETE')

  def _fill_request_log(self, log_row, log, include_app_logs):
    log.set_request_id(str(log_row['user_request_id']))
    log.set_app_id(log_row['app_id'])
    log.set_version_id(log_row['version_id'])
    log.set_module_id(log_row['module'])
    log.set_ip(log_row['ip'])
    log.set_nickname(log_row['nickname'])
    log.set_start_time(log_row['start_time'])
    log.set_host(log_row['host'])
    log.set_end_time(log_row['end_time'])
    log.set_method(log_row['method'])
    log.set_resource(log_row['resource'])
    log.set_status(log_row['status'])
    log.set_response_size(log_row['response_size'])
    log.set_http_version(log_row['http_version'])
    log.set_user_agent(log_row['user_agent'])
    log.set_url_map_entry(log_row['url_map_entry'])
    log.set_latency(log_row['latency'])
    log.set_mcycles(log_row['mcycles'])
    log.set_finished(log_row['finished'])
    log.mutable_offset().set_request_id(str(log_row['id']))
    time_seconds = (log_row['end_time'] or log_row['start_time']) / 10**6
    date_string = time.strftime('%d/%b/%Y:%H:%M:%S %z',
                                time.localtime(time_seconds))
    log.set_combined('%s - %s [%s] "%s %s %s" %d %d - "%s"' %
                     (log_row['ip'], log_row['nickname'], date_string,
                      log_row['method'], log_row['resource'],
                      log_row['http_version'], log_row['status'] or 0,
                      log_row['response_size'] or 0, log_row['user_agent']))
    if include_app_logs:
      log_messages = self._conn.execute(
          'SELECT timestamp, level, message FROM AppLogs '
          'WHERE request_id = ?',
          (log_row['id'],)).fetchall()
      for message in log_messages:
        line = log.add_line()
        line.set_time(message['timestamp'])
        line.set_level(message['level'])
        line.set_log_message(message['message'])

  @staticmethod
  def _extract_read_filters(request):
    """Extracts SQL filters from the LogReadRequest.

    Args:
      request: the incoming LogReadRequest.
    Returns:
      a pair of (filters, values); filters is a list of SQL filter expressions,
      to be joined by AND operators; values is a list of values to be
      interpolated into the filter expressions by the db library.
    """
    filters = []
    values = []

    module_filters = []
    module_values = []
    for module_version in request.module_version_list():
      module_filters.append('(version_id = ? AND module = ?)')
      module_values.append(module_version.version_id())
      module = appinfo.DEFAULT_MODULE
      if module_version.has_module_id():
        module = module_version.module_id()
      module_values.append(module)
    if module_filters:
      filters.append('(' + ' or '.join(module_filters) + ')')
      values += module_values

    if request.has_offset():
      try:
        filters.append('RequestLogs.id < ?')
        values.append(int(request.offset().request_id()))
      except ValueError:
        logging.error('Bad offset in log request: "%s"', request.offset())
        raise apiproxy_errors.ApplicationError(
            log_service_pb.LogServiceError.INVALID_REQUEST)
    if request.has_minimum_log_level():
      filters.append('AppLogs.level >= ?')
      values.append(request.minimum_log_level())






    finished_filter = 'finished = 1 '
    finished_filter_values = []
    unfinished_filter = 'finished = 0'
    unfinished_filter_values = []

    if request.has_start_time():
      finished_filter += ' and end_time >= ? '
      finished_filter_values.append(request.start_time())
      unfinished_filter += ' and start_time >= ? '
      unfinished_filter_values.append(request.start_time())
    if request.has_end_time():
      finished_filter += ' and end_time < ? '
      finished_filter_values.append(request.end_time())
      unfinished_filter += ' and start_time < ? '
      unfinished_filter_values.append(request.end_time())

    if request.include_incomplete():
      filters.append(
          '((' + finished_filter + ') or (' + unfinished_filter + '))')
      values += finished_filter_values + unfinished_filter_values
    else:
      filters.append(finished_filter)
      values += finished_filter_values

    return filters, values

  def _Dynamic_SetStatus(self, unused_request, unused_response,
                         unused_request_id):
    raise NotImplementedError

  def _Dynamic_Usage(self, unused_request, unused_response, unused_request_id):
    raise apiproxy_errors.CapabilityDisabledError('Usage not allowed in tests.')
