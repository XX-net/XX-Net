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





"""Errors used in the Python datastore API."""













class Error(Exception):
  """Base datastore error type.
  """

class BadValueError(Error):
  """Raised by Entity.__setitem__(), Query.__setitem__(), Get(), and others
  when a property value or filter value is invalid.
  """

class BadPropertyError(Error):
  """Raised by Entity.__setitem__() when a property name isn't a string.
  """

class BadRequestError(Error):
  """Raised by datastore calls when the parameter(s) are invalid.
  """

class EntityNotFoundError(Error):
  """DEPRECATED: Raised by Get() when the requested entity is not found.
  """

class BadArgumentError(Error):
  """Raised by Query.Order(), Iterator.Next(), and others when they're
  passed an invalid argument.
  """

class QueryNotFoundError(Error):
  """DEPRECATED: Raised by Iterator methods when the Iterator is invalid. This
  should not happen during normal usage; it protects against malicious users
  and system errors.
  """

class TransactionNotFoundError(Error):
  """DEPRECATED: Raised by RunInTransaction. This is an internal error; you
  should not see this.
  """

class Rollback(Error):
  """May be raised by transaction functions when they want to roll back
  instead of committing. Note that *any* exception raised by a transaction
  function will cause a rollback. This is purely for convenience. See
  datastore.RunInTransaction for details.
  """

class TransactionFailedError(Error):
  """Raised by RunInTransaction methods when the transaction could not be
  committed, even after retrying. This is usually due to high contention.
  """

class BadFilterError(Error):
  """Raised by Query.__setitem__() and Query.Run() when a filter string is
  invalid.
  """
  def __init__(self, filter):
    self.filter = filter
    message = (u'invalid filter: %s.' % self.filter).encode('utf-8')
    super(BadFilterError, self).__init__(message)

class BadQueryError(Error):
  """Raised by Query when a query or query string is invalid.
  """

class BadKeyError(Error):
  """Raised by Key.__str__ when the key is invalid.
  """

class InternalError(Error):
  """An internal datastore error. Please report this to Google.
  """

class NeedIndexError(Error):
  """No matching index was found for a query that requires an index. Check
  the Indexes page in the Admin Console and your index.yaml file.
  """

  def __init__(self, error, original_message=None, header=None, yaml_index=None,
               xml_index=None):
    super(NeedIndexError, self).__init__(error)
    self._original_message = original_message
    self._header = header
    self._yaml_index = yaml_index
    self._xml_index = xml_index

  def OriginalMessage(self):
    return self._original_message

  def Header(self):
    return self._header

  def YamlIndex(self):
    return self._yaml_index

  def XmlIndex(self):
    return self._xml_index

class ReferencePropertyResolveError(Error):
  """An error occurred while trying to resolve a ReferenceProperty."""


class Timeout(Error):
  """The datastore operation timed out, or the data was temporarily
  unavailable. This can happen when you attempt to put, get, or delete too
  many entities or an entity with too many properties, or if the datastore is
  overloaded or having trouble.
  """

class CommittedButStillApplying(Timeout):
  """The write or transaction was committed, but some entities or index rows
  may not have been fully updated. Those updates should automatically be
  applied soon. You can roll them forward immediately by reading one of the
  entities inside a transaction.
  """
