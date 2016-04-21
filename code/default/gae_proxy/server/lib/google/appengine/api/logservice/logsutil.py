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


"""Utility methods for working with logs."""



import os
import time



REQUEST_LOG_ID = 'REQUEST_LOG_ID'


_U_SEC = 1000000



FIXED_LOG_LINE_OVERHEAD = 15

LOG_LEVEL_DEBUG = 0
LOG_LEVEL_INFO = 1
LOG_LEVEL_WARNING = 2
LOG_LEVEL_ERROR = 3
LOG_LEVEL_CRITICAL = 4

LOG_LEVELS = [LOG_LEVEL_DEBUG,
              LOG_LEVEL_INFO,
              LOG_LEVEL_WARNING,
              LOG_LEVEL_ERROR,
              LOG_LEVEL_CRITICAL]



_DEFAULT_LEVEL = LOG_LEVEL_ERROR


def _CurrentTimeMicro():
  return int(time.time() * _U_SEC)


def _Clean(e):
  return e.replace('\0', '\n')


def Stripnl(message):
  if message and message[-1] == '\n':
    return message[:-1]
  return message


def RequestID():
  """Returns the ID of the current request assigned by App Engine."""
  return os.environ.get(REQUEST_LOG_ID, None)


def _StrictParseLogEntry(entry, clean_message=True):
  """Parses a single log entry emitted by app_logging.AppLogsHandler.

  Parses a log entry of the form LOG <level> <timestamp> <message> where the
  level is in the range [0, 4]. If the entry is not of that form, ValueError is
  raised.

  Args:
    entry: The log entry to parse.
    clean_message: should the message be cleaned (i.e. \0 -> \n).

  Returns:
    A (timestamp, level, message, source_location) tuple, where source_location
    is None.

  Raises:
    ValueError: if the entry failed to be parsed.
  """
  magic, level, timestamp, message = entry.split(' ', 3)
  if magic != 'LOG':
    raise ValueError()

  timestamp, level = int(timestamp), int(level)
  if level not in LOG_LEVELS:
    raise ValueError()

  return timestamp, level, _Clean(message), None if clean_message else message


def ParseLogEntry(entry):
  """Parses a single log entry emitted by app_logging.AppLogsHandler.

  Parses a log entry of the form LOG <level> <timestamp> <message> where the
  level is in the range [0, 4]. If the entry is not of that form, take the whole
  entry to be the message. Null characters in the entry are replaced by
  newlines.

  Args:
    entry: The log entry to parse.

  Returns:
    A (timestamp, level, message, source_location) tuple.
  """
  try:
    return _StrictParseLogEntry(entry)
  except ValueError:

    return _CurrentTimeMicro(), _DEFAULT_LEVEL, _Clean(entry), None


def ParseLogs(logs):
  """Parses a str containing newline separated log entries.

  Parses a series of log entries in the form LOG <level> <timestamp> <message>
  where the level is in the range [0, 4].  Null characters in the entry are
  replaced by newlines.

  Args:
    logs: A string containing the log entries.

  Returns:
    A list of (timestamp, level, message, source_location) tuples.
  """
  return [ParseLogEntry(line) for line in logs.split('\n') if line]


class LoggingRecord(object):
  """A record with all logging information.

  A record that came through the Python logging infrastructure that has various
  metadata in addition to the message itself.

  Note: the record may also come from stderr or logservice.write if the message
  matches the classic format used by streaming logservice.
  """

  def __init__(self, level, created, message, source_location):
    self.level = level
    self.created = created
    self.source_location = source_location
    self.message = message

  def IsBlank(self):
    return False

  def IsComplete(self):
    return True

  def Tuple(self):
    return self.level, self.created, self.source_location, self.message

  def __len__(self):
    return len(self.message) + FIXED_LOG_LINE_OVERHEAD

  def __str__(self):
    return 'LOG %d %d %s\n' % (self.level, self.created, self.message)

  def __eq__(self, x):
    return (self.level == x.level and self.created == x.created and
            self.source_location == x.source_location and
            self.message == x.message)


class StderrRecord(object):
  """A record with just a message.

  A record that came from stderr or logservice.write where only a message
  is available.
  """

  def __init__(self, message):
    self.message = message
    self._created = _CurrentTimeMicro()

  @property
  def level(self):
    return _DEFAULT_LEVEL

  @property
  def created(self):




    return self._created

  def Tuple(self):
    return self.level, self.created, Stripnl(self.message), self.source_location

  @property
  def source_location(self):
    return None

  def IsBlank(self):
    return self.message in ['', '\n']

  def IsComplete(self):
    return self.message and self.message[-1] == '\n'

  def __len__(self):
    return len(self.message)

  def __str__(self):
    return self.message


def RecordFromLine(line):
  """Create the correct type of record based on what the line looks like.

  With the classic streaming API, we did not distinguish between a message
  that came through the logging infrastructure and one that came throught stderr
  or logservice.write but had been written to look like it came from logging.

  Note that this code does not provide 100% accuracy with the old stream
  service. In the past, they could have written:
    sys.stderr.write('LOG %d %d' % (level, time))
    sys.stderr.write(' %s' % message)
  and that would have magically turned into a single full record. Trying to
  handle every single corner case seems like a poor use of time.

  Args:
    line: a single line written to stderr or logservice.write.

  Returns:
    The appropriate type of record.
  """
  try:
    created, level, unused_source_location, message = (
        _StrictParseLogEntry(line, clean_message=False))


    message = Stripnl(message)
    return LoggingRecord(level, created, message, None)
  except ValueError:
    return StderrRecord(line)
