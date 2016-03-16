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


"""A Python Search API used by app developers.

Contains methods used to interface with Search API.
Contains API classes that forward to apiproxy.
"""








import base64
import datetime
import logging
import re
import string
import sys
import warnings
from google.net.proto import ProtocolBuffer

from google.appengine.datastore import document_pb
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore_types
from google.appengine.api import namespace_manager
from google.appengine.api.search import expression_parser
from google.appengine.api.search import query_parser
from google.appengine.api.search import search_service_pb
from google.appengine.api.search import search_util
from google.appengine.datastore import datastore_rpc
from google.appengine.runtime import apiproxy_errors


__all__ = [
    'AtomField',
    'AtomFacet',
    'ConcurrentTransactionError',
    'Cursor',
    'DateField',
    'DeleteError',
    'DeleteResult',
    'Document',
    'DOCUMENT_ID_FIELD_NAME',
    'Error',
    'ExpressionError',
    'Facet',
    'FacetOptions',
    'FacetRange',
    'FacetRefinement',
    'FacetRequest',
    'FacetResult',
    'FacetResultValue',
    'Field',
    'FieldExpression',
    'HtmlField',
    'GeoField',
    'GeoPoint',
    'get_indexes',
    'get_indexes_async',
    'GetResponse',
    'Index',
    'InternalError',
    'InvalidRequest',
    'LANGUAGE_FIELD_NAME',
    'MatchScorer',
    'MAXIMUM_DOCUMENT_ID_LENGTH',
    'MAXIMUM_DOCUMENTS_PER_PUT_REQUEST',
    'MAXIMUM_DOCUMENTS_RETURNED_PER_SEARCH',
    'MAXIMUM_DEPTH_FOR_FACETED_SEARCH',
    'MAXIMUM_FACETS_TO_RETURN',
    'MAXIMUM_FACET_VALUES_TO_RETURN',
    'MAXIMUM_EXPRESSION_LENGTH',
    'MAXIMUM_FIELD_ATOM_LENGTH',
    'MAXIMUM_FIELD_NAME_LENGTH',
    'MAXIMUM_FIELD_PREFIX_LENGTH',
    'MAXIMUM_FIELD_VALUE_LENGTH',
    'MAXIMUM_FIELDS_RETURNED_PER_SEARCH',
    'MAXIMUM_GET_INDEXES_OFFSET',
    'MAXIMUM_INDEX_NAME_LENGTH',
    'MAXIMUM_INDEXES_RETURNED_PER_GET_REQUEST',
    'MAXIMUM_NUMBER_FOUND_ACCURACY',
    'MAXIMUM_QUERY_LENGTH',
    'MAXIMUM_SEARCH_OFFSET',
    'MAXIMUM_SORTED_DOCUMENTS',
    'MAX_DATE',
    'MAX_NUMBER_VALUE',
    'MIN_DATE',
    'MIN_NUMBER_VALUE',
    'NumberField',
    'NumberFacet',
    'OperationResult',
    'PutError',
    'PutResult',
    'Query',
    'QueryError',
    'QueryOptions',
    'RANK_FIELD_NAME',
    'RescoringMatchScorer',
    'SCORE_FIELD_NAME',
    'ScoredDocument',
    'SearchResults',
    'SortExpression',
    'SortOptions',
    'TextField',
    'Timeout',
    'TIMESTAMP_FIELD_NAME',
    'TokenizedPrefixField',
    'TransientError',
    'UntokenizedPrefixField',
    ]

MAXIMUM_INDEX_NAME_LENGTH = 100
MAXIMUM_FIELD_VALUE_LENGTH = 1024 * 1024
MAXIMUM_FIELD_ATOM_LENGTH = 500
MAXIMUM_FIELD_PREFIX_LENGTH = 500
MAXIMUM_FIELD_NAME_LENGTH = 500
MAXIMUM_DOCUMENT_ID_LENGTH = 500
MAXIMUM_DOCUMENTS_PER_PUT_REQUEST = 200
MAXIMUM_EXPRESSION_LENGTH = 5000
MAXIMUM_QUERY_LENGTH = 2000
MAXIMUM_DOCUMENTS_RETURNED_PER_SEARCH = 1000
MAXIMUM_DEPTH_FOR_FACETED_SEARCH = 10000
MAXIMUM_FACETS_TO_RETURN = 100
MAXIMUM_FACET_VALUES_TO_RETURN = 20
MAXIMUM_SEARCH_OFFSET = 1000

MAXIMUM_SORTED_DOCUMENTS = 10000
MAXIMUM_NUMBER_FOUND_ACCURACY = 25000
MAXIMUM_FIELDS_RETURNED_PER_SEARCH = 1000
MAXIMUM_INDEXES_RETURNED_PER_GET_REQUEST = 1000
MAXIMUM_GET_INDEXES_OFFSET = 1000


DOCUMENT_ID_FIELD_NAME = '_doc_id'

LANGUAGE_FIELD_NAME = '_lang'

RANK_FIELD_NAME = '_rank'

SCORE_FIELD_NAME = '_score'



TIMESTAMP_FIELD_NAME = '_timestamp'




_LANGUAGE_RE = re.compile('^(.{2}|.{2}_.{2})$')

_MAXIMUM_STRING_LENGTH = 500
_MAXIMUM_CURSOR_LENGTH = 10000

_VISIBLE_PRINTABLE_ASCII = frozenset(
    set(string.printable) - set(string.whitespace))
_FIELD_NAME_PATTERN = '^[A-Za-z][A-Za-z0-9_]*$'

MAX_DATE = datetime.datetime(
    datetime.MAXYEAR, 12, 31, 23, 59, 59, 999999, tzinfo=None)
MIN_DATE = datetime.datetime(
    datetime.MINYEAR, 1, 1, 0, 0, 0, 0, tzinfo=None)


MAX_NUMBER_VALUE = 2147483647
MIN_NUMBER_VALUE = -2147483647


_PROTO_FIELDS_STRING_VALUE = frozenset(
    [document_pb.FieldValue.TEXT,
     document_pb.FieldValue.HTML,
     document_pb.FieldValue.ATOM,
     document_pb.FieldValue.UNTOKENIZED_PREFIX,
     document_pb.FieldValue.TOKENIZED_PREFIX])


class Error(Exception):
  """Indicates a call on the search API has failed."""


class InternalError(Error):
  """Indicates a call on the search API has failed on the internal backend."""


class TransientError(Error):
  """Indicates a call on the search API has failed, but retrying may succeed."""


class InvalidRequest(Error):
  """Indicates an invalid request was made on the search API by the client."""


class QueryError(Error):
  """An error occurred while parsing a query input string."""


class ExpressionError(Error):
  """An error occurred while parsing an expression input string."""


class Timeout(Error):
  """Indicates a call on the search API could not finish before its deadline."""


class ConcurrentTransactionError(Error):
  """Indicates a call on the search API failed due to concurrent updates."""


def _ConvertToUnicode(some_string):
  """Convert UTF-8 encoded string to unicode."""
  if some_string is None:
    return None
  if isinstance(some_string, unicode):
    return some_string
  return unicode(some_string, 'utf-8')


def _ConcatenateErrorMessages(prefix, status):
  """Returns an error message combining prefix and status.error_detail()."""
  if status.error_detail():
    return prefix + ': ' + status.error_detail()
  return prefix


class _RpcOperationFuture(object):
  """Represents the future result a search RPC sent to a backend."""

  def __init__(self, call, request, response, deadline, get_result_hook):
    """Initializer.

    Args:
      call: Method name to call, as a string
      request: The request object
      response: The response object
      deadline: Deadline for RPC call in seconds; if None use the default.
      get_result_hook: Required result hook. Must be a function that takes
        no arguments. Its return value is returned by get_result().
    """
    _ValidateDeadline(deadline)
    self._get_result_hook = get_result_hook
    self._rpc = apiproxy_stub_map.UserRPC('search', deadline=deadline)
    self._rpc.make_call(call, request, response)

  def get_result(self):
    self._rpc.wait();
    try:
      self._rpc.check_success();
    except apiproxy_errors.ApplicationError, e:
      raise _ToSearchError(e)
    return self._get_result_hook()


class _SimpleOperationFuture(object):
  """Adapts a late-binding function to a future."""

  def __init__(self, future, function):
    self._future = future
    self._function = function

  def get_result(self):
    return self._function(self._future.get_result())


class _WrappedValueFuture(object):
  """Adapts an immediately-known result to a future."""

  def __init__(self, result):
    self._result = result

  def get_result(self):
    return self._result


def _ConvertToUTF8(value):
  if isinstance(value, float):
    value = repr(value)
    value = {'inf': 'Infinity',
             '-inf': '-Infinity',
             'nan': 'NaN'}.get(value, value)
  elif isinstance(value, (int, long)):
    value = str(value)
  return _ConvertToUnicode(value).encode("utf-8")


class OperationResult(object):
  """Represents result of individual operation of a batch index or removal.

  This is an abstract class.
  """

  (OK, INVALID_REQUEST, TRANSIENT_ERROR, INTERNAL_ERROR,
  TIMEOUT,  CONCURRENT_TRANSACTION) = (
      'OK', 'INVALID_REQUEST', 'TRANSIENT_ERROR', 'INTERNAL_ERROR',
      'TIMEOUT', 'CONCURRENT_TRANSACTION')

  _CODES = frozenset([OK, INVALID_REQUEST, TRANSIENT_ERROR, INTERNAL_ERROR,
                      TIMEOUT, CONCURRENT_TRANSACTION])

  def __init__(self, code, message=None, id=None):
    """Initializer.

    Args:
      code: The error or success code of the operation.
      message: An error message associated with any error.
      id: The id of the object some operation was performed on.

    Raises:
      TypeError: If an unknown attribute is passed.
      ValueError: If an unknown code is passed.
    """
    self._message = _ConvertToUnicode(message)
    self._code = code
    if self._code not in self._CODES:
      raise ValueError('Unknown operation result code %r, must be one of %s'
                       % (self._code, self._CODES))
    self._id = _ConvertToUnicode(id)

  @property
  def code(self):
    """Returns the code indicating the status of the operation."""
    return self._code

  @property
  def message(self):
    """Returns any associated error message if the operation was in error."""
    return self._message

  @property
  def id(self):
    """Returns the Id of the object the operation was performed on."""
    return self._id

  def __repr__(self):
    return _Repr(self, [('code', self.code), ('message', self.message),
                        ('id', self.id)])


_ERROR_OPERATION_CODE_MAP = {
    search_service_pb.SearchServiceError.OK: OperationResult.OK,
    search_service_pb.SearchServiceError.INVALID_REQUEST:
    OperationResult.INVALID_REQUEST,
    search_service_pb.SearchServiceError.TRANSIENT_ERROR:
    OperationResult.TRANSIENT_ERROR,
    search_service_pb.SearchServiceError.INTERNAL_ERROR:
    OperationResult.INTERNAL_ERROR,
    search_service_pb.SearchServiceError.TIMEOUT:
    OperationResult.TIMEOUT,
    search_service_pb.SearchServiceError.CONCURRENT_TRANSACTION:
    OperationResult.CONCURRENT_TRANSACTION,
    }


class PutResult(OperationResult):
  """The result of indexing a single object."""


class DeleteResult(OperationResult):
  """The result of deleting a single document."""


class PutError(Error):
  """Indicates some error occurred indexing one of the objects requested."""

  def __init__(self, message, results):
    """Initializer.

    Args:
      message: A message detailing the cause of the failure to index some
        document.
      results: A list of PutResult corresponding to the list of objects
        requested to be indexed.
    """
    super(PutError, self).__init__(message)
    self._results = results

  @property
  def results(self):
    """Returns PutResult list corresponding to objects indexed."""
    return self._results


class DeleteError(Error):
  """Indicates some error occured deleting one of the objects requested."""

  def __init__(self, message, results):
    """Initializer.

    Args:
      message: A message detailing the cause of the failure to delete some
        document.
      results: A list of DeleteResult corresponding to the list of Ids of
        objects requested to be deleted.
    """
    super(DeleteError, self).__init__(message)
    self._results = results

  @property
  def results(self):
    """Returns DeleteResult list corresponding to Documents deleted."""
    return self._results


_ERROR_MAP = {
    search_service_pb.SearchServiceError.INVALID_REQUEST: InvalidRequest,
    search_service_pb.SearchServiceError.TRANSIENT_ERROR: TransientError,
    search_service_pb.SearchServiceError.INTERNAL_ERROR: InternalError,
    search_service_pb.SearchServiceError.TIMEOUT: Timeout,
    search_service_pb.SearchServiceError.CONCURRENT_TRANSACTION:
    ConcurrentTransactionError,
    }


def _ToSearchError(error):
  """Translate an application error to a search Error, if possible.

  Args:
    error: An ApplicationError to translate.

  Returns:
    An Error if the error is known, otherwise the given
    apiproxy_errors.ApplicationError.
  """
  if error.application_error in _ERROR_MAP:
    return _ERROR_MAP[error.application_error](error.error_detail)
  return error


def _CheckInteger(value, name, zero_ok=True, upper_bound=None):
  """Checks whether value is an integer between the lower and upper bounds.

  Args:
    value: The value to check.
    name: The name of the value, to use in error messages.
    zero_ok: True if zero is allowed.
    upper_bound: The upper (inclusive) bound of the value. Optional.

  Returns:
    The checked value.

  Raises:
    ValueError: If the value is not a int or long, or is out of range.
  """
  datastore_types.ValidateInteger(value, name, ValueError, empty_ok=True,
                                  zero_ok=zero_ok)
  if upper_bound is not None and value > upper_bound:
    raise ValueError('%s, %d must be <= %d' % (name, value, upper_bound))
  return value


def _CheckEnum(value, name, values=None):
  """Checks whether value is a member of the set of values given.

  Args:
    value: The value to check.
    name: The name of the value, to use in error messages.
    values: The iterable of possible values.

  Returns:
    The checked value.

  Raises:
    ValueError: If the value is not one of the allowable values.
  """
  if value not in values:
    raise ValueError('%s, %r must be in %s' % (name, value, values))
  return value


def _IsFinite(value):
  """Returns whether a value is a finite number.

  Args:
    value: The value to check.

  Returns:
    True if the value is a finite number; otherwise False.
  """

  if isinstance(value, float) and -1e30000 < value < 1e30000:
    return True
  elif isinstance(value, (int, long)):
    return True
  else:
    return False


def _CheckNumber(value, name, should_be_finite=False):
  """Checks whether number value is of valid type and (optionally) finite.

  Args:
    value: The value to check.
    name: The name of the value, to use in error messages.
    should_be_finite: make sure the value is a finite number.

  Returns:
    The checked value.

  Raises:
    TypeError: If the value is not a number.
    ValueError: If should_be_finite is set and the value is not finite.
  """
  if not isinstance(value, (int, long, float)):
    raise TypeError('%s must be a int, long or float, got %s' %
                    (name, value.__class__.__name__))
  if should_be_finite and not _IsFinite(value):
    raise ValueError('%s must be a finite value (got %f)' % (name, value))
  return value


def _CheckStatus(status):
  """Checks whether a RequestStatus has a value of OK.

  Args:
    status: The RequestStatus to check.

  Raises:
    Error: A subclass of Error if the value of status is not OK.
      The subclass of Error is chosen based on value of the status code.
    InternalError: If the status value is unknown.
  """
  if status.code() != search_service_pb.SearchServiceError.OK:
    if status.code() in _ERROR_MAP:
      raise _ERROR_MAP[status.code()](status.error_detail())
    else:
      raise InternalError(status.error_detail())


def _ValidateString(value,
                    name='unused',
                    max_len=_MAXIMUM_STRING_LENGTH,
                    empty_ok=False,
                    type_exception=TypeError,
                    value_exception=ValueError):
  """Raises an exception if value is not a valid string or a subclass thereof.

  A string is valid if it's not empty, no more than _MAXIMUM_STRING_LENGTH
  bytes. The exception type can be specified with the exception
  arguments for type and value issues.

  Args:
    value: The value to validate.
    name: The name of this value; used in the exception message.
    max_len: The maximum allowed length, in bytes.
    empty_ok: Allow empty value.
    type_exception: The type of exception to raise if not a basestring.
    value_exception: The type of exception to raise if invalid value.

  Returns:
    The checked string.

  Raises:
    TypeError: If value is not a basestring or subclass.
    ValueError: If the value is None or longer than max_len.
  """
  if value is None and empty_ok:
    return
  if value is not None and not isinstance(value, basestring):
    raise type_exception('%s must be a basestring; got %s:' %
                         (name, value.__class__.__name__))
  if not value and not empty_ok:
    raise value_exception('%s must not be empty.' % name)

  if len(value.encode('utf-8')) > max_len:
    raise value_exception('%s must be under %d bytes.' % (name, max_len))
  return value


def _ValidateVisiblePrintableAsciiNotReserved(value, name):
  """Checks if value is a visible printable ASCII string not starting with '!'.

  Whitespace characters are excluded. Printable visible ASCII
  strings starting with '!' are reserved for internal use.

  Args:
    value: The string to validate.
    name: The name of this string; used in the exception message.

  Returns:
    The checked string.

  Raises:
    ValueError: If the string is not visible printable ASCII, or starts with
      '!'.
  """
  for char in value:
    if char not in _VISIBLE_PRINTABLE_ASCII:
      raise ValueError(
          '%r must be visible printable ASCII: %r'
          % (name, value))
  if value.startswith('!'):
    raise ValueError('%r must not start with "!": %r' % (name, value))
  return value


def _CheckIndexName(index_name):
  """Checks index_name is a string which is not too long, and returns it.

  Index names must be visible printable ASCII and not start with '!'.
  """
  _ValidateString(index_name, 'index name', MAXIMUM_INDEX_NAME_LENGTH)
  return _ValidateVisiblePrintableAsciiNotReserved(index_name, 'index_name')


def _CheckFacetName(name):
  """Checks facet name is not too long and matches facet name pattern.

  Facet name pattern: "[A-Za-z][A-Za-z0-9_]*".

  Args:
    name: the name string to validate.
  Returns:
    the valid name.
  """
  return _CheckFieldName(name)


def _CheckFieldName(name):
  """Checks field name is not too long and matches field name pattern.

  Field name pattern: "[A-Za-z][A-Za-z0-9_]*".
  """
  _ValidateString(name, 'name', MAXIMUM_FIELD_NAME_LENGTH)
  if not re.match(_FIELD_NAME_PATTERN, name):
    raise ValueError('field name "%s" should match pattern: %s' %
                     (name, _FIELD_NAME_PATTERN))
  return name


def _CheckExpression(expression):
  """Checks whether the expression is a string."""
  expression = _ValidateString(expression, max_len=MAXIMUM_EXPRESSION_LENGTH)
  try:
    expression_parser.Parse(expression)
  except expression_parser.ExpressionException, e:
    raise ExpressionError('Failed to parse expression "%s"' % expression)
  return expression


def _CheckFieldNames(names):
  """Checks each name in names is a valid field name."""
  for name in names:
    _CheckFieldName(name)
  return names


def _GetList(a_list):
  """Utility function that converts None to the empty list."""
  if a_list is None:
    return []
  else:
    return list(a_list)


def _ConvertToList(arg):
  """Converts arg to a list, empty if None, single element if not a list."""
  if isinstance(arg, basestring):
    return [arg]
  if arg is not None:
    try:
      return list(iter(arg))
    except TypeError:
      return [arg]
  return []


def _CheckType(obj, obj_type, obj_name):
  """Check the type of an object."""
  if not isinstance(obj, obj_type):
    raise TypeError('%s must be a %s, got %s'
                    % (obj_name, obj_type, obj.__class__.__name__))
  return obj


def _ConvertToListAndCheckType(arg, element_type, arg_name):
  """Converts args to a list and check its element type."""
  ret = _ConvertToList(arg)
  for element in ret:
    if not isinstance(element, element_type):
      raise TypeError('%s should be single element or list of type %s'
                      % (arg_name, element_type))
  return ret


def _ConvertToUnicodeList(arg):
  """Converts arg to a list of unicode objects."""
  return [_ConvertToUnicode(value) for value in _ConvertToList(arg)]


def _CheckDocumentId(doc_id):
  """Checks doc_id is a valid document identifier, and returns it.

  Document ids must be visible printable ASCII and not start with '!'.
  """
  _ValidateString(doc_id, 'doc_id', MAXIMUM_DOCUMENT_ID_LENGTH)
  _ValidateVisiblePrintableAsciiNotReserved(doc_id, 'doc_id')
  return doc_id


def _CheckText(value, name='value', empty_ok=True):
  """Checks the field text is a valid string."""
  return _ValidateString(value, name, MAXIMUM_FIELD_VALUE_LENGTH, empty_ok)


def _CheckHtml(html):
  """Checks the field html is a valid HTML string."""
  return _ValidateString(html, 'html', MAXIMUM_FIELD_VALUE_LENGTH,
                         empty_ok=True)


def _CheckAtom(atom):
  """Checks the field atom is a valid string."""
  return _ValidateString(atom, 'atom', MAXIMUM_FIELD_ATOM_LENGTH,
                         empty_ok=True)


def _CheckPrefix(prefix):
  """Checks if the untokenized or tokenized prefix field is a valid string."""
  return _ValidateString(prefix, 'prefix', MAXIMUM_FIELD_PREFIX_LENGTH,
                         empty_ok=True)


def _CheckDate(date):
  """Checks the date is in the correct range."""
  if isinstance(date, datetime.datetime):
    if date < MIN_DATE or date > MAX_DATE:
      raise TypeError('date must be between %s and %s (got %s)' %
                      (MIN_DATE, MAX_DATE, date))
  elif isinstance(date, datetime.date):
    if date < MIN_DATE.date() or date > MAX_DATE.date():
      raise TypeError('date must be between %s and %s (got %s)' %
                      (MIN_DATE, MAX_DATE, date))
  else:
    raise TypeError('date must be datetime.datetime or datetime.date')
  return date


def _CheckLanguage(language):
  """Checks language is None or a string that matches _LANGUAGE_RE."""
  if language is None:
    return None
  if not isinstance(language, basestring):
    raise TypeError('language must be a basestring, got %s' %
                    language.__class__.__name__)
  if not re.match(_LANGUAGE_RE, language):
    raise ValueError('invalid language %s. Languages should be two letters.'
                     % language)
  return language


def _CheckDocument(document):
  """Check that the document is valid.

  This checks for all server-side requirements on Documents. Currently, that
  means ensuring that there are no repeated number or date fields.

  Args:
    document: The search.Document to check for validity.

  Raises:
    ValueError if the document is invalid in a way that would trigger an
    PutError from the server.
  """
  no_repeat_date_names = set()
  no_repeat_number_names = set()
  for field in document.fields:
    if isinstance(field, NumberField):
      if field.name in no_repeat_number_names:
        raise ValueError(
            'Invalid document %s: field %s with type date or number may not '
            'be repeated.' % (document.doc_id, field.name))
      no_repeat_number_names.add(field.name)
    elif isinstance(field, DateField):
      if field.name in no_repeat_date_names:
        raise ValueError(
            'Invalid document %s: field %s with type date or number may not '
            'be repeated.' % (document.doc_id, field.name))
      no_repeat_date_names.add(field.name)


def _CheckSortLimit(limit):
  """Checks the limit on number of docs to score or sort is not too large."""
  return _CheckInteger(limit, 'limit', upper_bound=MAXIMUM_SORTED_DOCUMENTS)


def _Repr(class_instance, ordered_dictionary):
  """Generates an unambiguous representation for instance and ordered dict."""
  return u'search.%s(%s)' % (class_instance.__class__.__name__, ', '.join(
      ['%s=%r' % (key, value) for (key, value) in ordered_dictionary
       if value is not None and value != []]))


def _ListIndexesResponsePbToGetResponse(response, include_schema):
  """Returns a GetResponse constructed from get_indexes response pb."""
  return GetResponse(
      results=[_NewIndexFromPb(index, include_schema)
               for index in response.index_metadata_list()])


@datastore_rpc._positional(7)
def get_indexes(namespace='', offset=None, limit=20,
                start_index_name=None, include_start_index=True,
                index_name_prefix=None, fetch_schema=False, deadline=None,
                **kwargs):
  """Returns a list of available indexes.

  Args:
    namespace: The namespace of indexes to be returned. If not set
      then the current namespace is used.
    offset: The offset of the first returned index.
    limit: The number of indexes to return.
    start_index_name: The name of the first index to be returned.
    include_start_index: Whether or not to return the start index.
    index_name_prefix: The prefix used to select returned indexes.
    fetch_schema: Whether to retrieve Schema for each Index or not.

  Kwargs:
    deadline: Deadline for RPC call in seconds; if None use the default.

  Returns:
    The GetResponse containing a list of available indexes.

  Raises:
    InternalError: If the request fails on internal servers.
    TypeError: If any of the parameters have invalid types, or an unknown
      attribute is passed.
    ValueError: If any of the parameters have invalid values (e.g., a
      negative deadline).
  """
  return get_indexes_async(
      namespace, offset, limit, start_index_name, include_start_index,
      index_name_prefix, fetch_schema, deadline=deadline, **kwargs).get_result()


@datastore_rpc._positional(7)
def get_indexes_async(namespace='', offset=None, limit=20,
                      start_index_name=None, include_start_index=True,
                      index_name_prefix=None, fetch_schema=False, deadline=None,
                      **kwargs):
  """Asynchronously returns a list of available indexes.

  Identical to get_indexes() except that it returns a future. Call
  get_result() on the return value to block on the call and get its result.
  """

  app_id = kwargs.pop('app_id', None)
  if kwargs:
    raise TypeError('Invalid arguments: %s' % ', '.join(kwargs))

  request = search_service_pb.ListIndexesRequest()
  params = request.mutable_params()

  if namespace is None:
    namespace = namespace_manager.get_namespace()
  if namespace is None:
    namespace = u''
  namespace_manager.validate_namespace(namespace, exception=ValueError)
  params.set_namespace(namespace)
  if offset is not None:
    params.set_offset(_CheckInteger(offset, 'offset', zero_ok=True,
                                    upper_bound=MAXIMUM_GET_INDEXES_OFFSET))
  params.set_limit(_CheckInteger(
      limit, 'limit', zero_ok=False,
      upper_bound=MAXIMUM_INDEXES_RETURNED_PER_GET_REQUEST))
  if start_index_name is not None:
    params.set_start_index_name(
        _ValidateString(start_index_name, 'start_index_name',
                        MAXIMUM_INDEX_NAME_LENGTH,
                        empty_ok=False))
  if include_start_index is not None:
    params.set_include_start_index(bool(include_start_index))
  if index_name_prefix is not None:
    params.set_index_name_prefix(
        _ValidateString(index_name_prefix, 'index_name_prefix',
                        MAXIMUM_INDEX_NAME_LENGTH,
                        empty_ok=False))
  params.set_fetch_schema(fetch_schema)

  response = search_service_pb.ListIndexesResponse()
  if app_id:
    request.set_app_id(app_id)

  def hook():
    _CheckStatus(response.status())
    return _ListIndexesResponsePbToGetResponse(response, fetch_schema)
  return _RpcOperationFuture(
      'ListIndexes', request, response, deadline, hook)


class Field(object):
  """An abstract base class which represents a field of a document.

  This class should not be directly instantiated.
  """


  (TEXT, HTML, ATOM, DATE, NUMBER, GEO_POINT, UNTOKENIZED_PREFIX,
   TOKENIZED_PREFIX) = ('TEXT', 'HTML', 'ATOM', 'DATE', 'NUMBER', 'GEO_POINT',
                        'UNTOKENIZED_PREFIX', 'TOKENIZED_PREFIX')

  _FIELD_TYPES = frozenset([TEXT, HTML, ATOM, DATE, NUMBER, GEO_POINT,
                            UNTOKENIZED_PREFIX, TOKENIZED_PREFIX])

  def __init__(self, name, value, language=None):
    """Initializer.

    Args:
      name: The name of the field. Field names must have maximum length
        MAXIMUM_FIELD_NAME_LENGTH and match pattern "[A-Za-z][A-Za-z0-9_]*".
      value: The value of the field which can be a str, unicode or date.
      language: The ISO 693-1 two letter code of the language used in the value.
        See http://www.sil.org/iso639-3/codes.asp?order=639_1&letter=%25 for a
        list of valid codes. Correct specification of language code will assist
        in correct tokenization of the field. If None is given, then the
        language code of the document will be used.

    Raises:
      TypeError: If any of the parameters have invalid types, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have invalid values.
    """
    self._name = _CheckFieldName(_ConvertToUnicode(name))
    self._value = self._CheckValue(value)
    self._language = _CheckLanguage(_ConvertToUnicode(language))

  @property
  def name(self):
    """Returns the name of the field."""
    return self._name

  @property
  def language(self):
    """Returns the code of the language the content in value is written in."""
    return self._language

  @property
  def value(self):
    """Returns the value of the field."""
    return self._value

  def _CheckValue(self, value):
    """Checks the value is valid for the given type.

    Args:
      value: The value to check.

    Returns:
      The checked value.
    """
    raise NotImplementedError('_CheckValue is an abstract method')

  def __repr__(self):
    return _Repr(self, [('name', self.name), ('language', self.language),
                        ('value', self.value)])

  def __eq__(self, other):
    return isinstance(other, type(self)) and self.__key() == other.__key()

  def __ne__(self, other):
    return not self == other

  def __key(self):
    return (self.name, self.value, self.language)

  def __hash__(self):
    return hash(self.__key())

  def __str__(self):
    return repr(self)

  def _CopyStringValueToProtocolBuffer(self, field_value_pb):
    """Copies value to a string value in proto buf."""
    field_value_pb.set_string_value(self.value.encode('utf-8'))


class Facet(object):
  """An abstract base class which represents a facet of a document.

    This class should not be directly instantiated.
  """

  def __init__(self, name, value):
    """Initializer.

    Args:
      name: The name of the facet. Facet names must have maximum length
        MAXIMUM_FIELD_NAME_LENGTH and match pattern "[A-Za-z][A-Za-z0-9_]*".
      value: The value of the facet which can be a str, unicode or number.

    Raises:
      TypeError: If any of the parameters have invalid types, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have invalid values.
    """
    self._name = _CheckFacetName(_ConvertToUnicode(name))
    self._value = self._CheckValue(value)

  @property
  def name(self):
    """Returns the name of the facet."""
    return self._name

  @property
  def value(self):
    """Returns the value of the facet."""
    return self._value

  @classmethod
  def _CheckValue(cls, value):
    """Checks the value is valid for the given type.

    Args:
      value: The value to check.

    Returns:
      The checked value.
    """
    raise NotImplementedError('_CheckValue is an abstract method')

  def _CopyStringValueToProtocolBuffer(self, facet_value_pb):
    """Copies value to a string value in proto buf."""
    facet_value_pb.set_string_value(self.value.encode('utf-8'))

  def _CopyToProtocolBuffer(self, pb):
    """Copies facet's contents to a document_pb.Facet proto buffer."""
    pb.set_name(self.name)
    if self.value is not None:
      facet_value_pb = pb.mutable_value()
      self._CopyValueToProtocolBuffer(facet_value_pb)
    return pb

  def _AttributeValueList(self):
    return [self.name, self.value]

  def __eq__(self, other):
    return (isinstance(other, type(self)) and
            self._AttributeValueList() == other._AttributeValueList())

  def __ne__(self, other):
    return not self == other

  def __hash__(self):
    return hash(self._AttributeValueList())

  def __repr__(self):
    return _Repr(self, [('name', self.name), ('value', self.value)])


class AtomFacet(Facet):
  """A Facet that has content to be treated as a single token for indexing.

  The following example shows an atom facet named wine_type:
    AtomFacet(name='wine_type', value='Red')
  """

  def __init__(self, name, value=None):
    """Initializer.

    Args:
      name: The name of the facet.
      value: A str or unicode object to be treated as an indivisible text value.

    Raises:
      TypeError: If value is not a string.
      ValueError: If value is longer than allowed.
    """
    Facet.__init__(self, name, _ConvertToUnicode(value))

  @classmethod
  def _CheckValue(cls, value):
    return _CheckAtom(value)

  def _CopyValueToProtocolBuffer(self, facet_value_pb):
    facet_value_pb.set_type(document_pb.FacetValue.ATOM)
    self._CopyStringValueToProtocolBuffer(facet_value_pb)


class NumberFacet(Facet):
  """A Facet that has a numeric value.

  The following example shows a number facet named wine_vintage:
    NumberFacet(name='wine_vintage', value=2000)
  """

  def __init__(self, name, value=None):
    """Initializer.

    Args:
      name: The name of the facet.
      value: A numeric value.

    Raises:
      TypeError: If value is not numeric.
      ValueError: If value is out of range.
    """
    Facet.__init__(self, name, value)

  @classmethod
  def _CheckValue(cls, value):
    _CheckNumber(value, "number facet value", True)
    if value >= MIN_NUMBER_VALUE and value <= MAX_NUMBER_VALUE:
      return value
    raise ValueError('value must be between %f and %f (got %f)' %
                     (MIN_NUMBER_VALUE, MAX_NUMBER_VALUE, value))

  def _CopyValueToProtocolBuffer(self, facet_value_pb):
    facet_value_pb.set_type(document_pb.FacetValue.NUMBER)
    facet_value_pb.set_string_value(_ConvertToUTF8(self.value))


def _NewFacetFromPb(pb):
  """Constructs a Facet from a document_pb.Facet protocol buffer."""
  name = _DecodeUTF8(pb.name())
  val_type = pb.value().type()
  value = _DecodeValue(_GetValue(pb.value()), val_type)
  if val_type == document_pb.FacetValue.ATOM:
    return AtomFacet(name, value)
  elif val_type == document_pb.FacetValue.NUMBER:
    return NumberFacet(name, value)
  return InvalidRequest('Unknown facet value type %d' % val_type)


def _NewFacetsFromPb(facet_list):
  """Returns a list of Facet copied from a document_pb.Document proto buf."""
  return [_NewFacetFromPb(f) for f in facet_list]


class FacetRange(object):
  """A facet range with start and end values.

    An example of a FacetRange for good rating is:
    FacetRange(start=3.0, end=3.5)
  """

  @datastore_rpc._positional(1)
  def __init__(self, start=None, end=None):
    """Initializer.

    Args:
      start: Start value for the range, inclusive.
      end: End value for the range. exclusive.

    Raises:
      TypeError: If any of the parameters have invalid types, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have invalid values.
    """
    if start is None and end is None:
      raise ValueError(
          'Either start or end need to be provided for a facet range.')
    none_or_numeric_type = (type(None), int, float, long)
    self._start = _CheckType(start, none_or_numeric_type, 'start')
    self._end = _CheckType(end, none_or_numeric_type, 'end')
    if self._start is not None:
      NumberFacet._CheckValue(self._start)
    if self._end is not None:
      NumberFacet._CheckValue(self._end)

  @property
  def start(self):
    """Returns inclusive start of the range."""
    return self._start

  @property
  def end(self):
    """Returns exclusive end of the range."""
    return self._end

  def __repr__(self):
    return _Repr(self, [('start', self.start),
                        ('end', self.end)])

  def _CopyToProtocolBuffer(self, range_pb):
    if self.start is not None:
      range_pb.set_start(_ConvertToUTF8(self.start))
    if self.end is not None:
      range_pb.set_end(_ConvertToUTF8(self.end))


class FacetRequest(object):
  """A facet to be included in search result.

  An example of a request for a facet only with name:
    FacetRequest('ExpediteShipping')
  (in that case, results will always have this facet)
  Or with a value constraint:
    FacetRequest('Size', values=['XL','L','M']
  (results will have this facet with only specified values)
  Or ranges:
    FacetRequest('Rating', ranges=[
        FacetRange(1.0, 2.0),
        FacetRange(2.0, 3.5),
        FacetRange(3.5, 4.0)]
  (results will have this facet with specified ranges)
  """

  @datastore_rpc._positional(2)
  def __init__(self, name, value_limit=10, ranges=None, values=None):
    """Initializer.

    Args:
      name: The name of the facet.
      value_limit: Number of values to return if values is not specified.
      ranges: Range of values to return. Cannot be set with values.
      values: Specific values to return. Cannot be set with ranges.

    Raises:
      TypeError: If any of the parameters have invalid types, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have invalid values.
    """
    self._name = _CheckFacetName(_ConvertToUnicode(name))
    self._value_limit = _CheckFacetValueLimit(value_limit)
    if ranges is not None and values is not None:
      raise ValueError(
          'Cannot specify both ranges and values.')
    self._ranges = _ConvertToListAndCheckType(
        ranges, FacetRange, 'ranges')
    self._values = _ConvertToListAndCheckType(
        values, (basestring, int, float, long), 'values')
    for value in self._values:
      if isinstance(value, (int, float, long)):
        NumberFacet._CheckValue(value)

  @property
  def name(self):
    """Returns the name of the facet."""
    return self._name

  @property
  def value_limit(self):
    """Returns number of values to be included in the result."""
    return self._value_limit

  @property
  def ranges(self):
    """Returns FacetRanges of values to be included in the result."""
    return self._ranges

  @property
  def values(self):
    """Returns specific values to be included in the result."""
    return self._values

  def _CopyToProtocolBuffer(self, facet_request_pb):
    """Converts this object to a search_service_pb.FacetRequest proto buff."""
    facet_request_pb.set_name(self.name)
    request_param_pb = facet_request_pb.mutable_params()
    request_param_pb.set_value_limit(self.value_limit)
    for facet_range in self.ranges:
      facet_range._CopyToProtocolBuffer(request_param_pb.add_range())
    for constraint in self.values:
      request_param_pb.add_value_constraint(_ConvertToUTF8(constraint))

  def __repr__(self):
    return _Repr(self, [('name', self.name),
                        ('value_limit', self.value_limit),
                        ('ranges', self.ranges),
                        ('values', self.values)])


class FacetRefinement(object):
  """A Facet Refinement to filter out search results based on a facet value.

  NOTE: The recommended way to use facet refinement is to use the token
  string. Each FacetResult will have a token that is acceptable instead of this
  class. To provide manual FacetRefinement, an instance of this class can be
  passed to SearchOptions.
  NOTE: that either value or facet_range should be set but not both.
  Example: Request for a range refinement for a numeric facet:
    FacetRefinement(name='rating', facet_range=FacetRange(start=1.0,end=2.5))
  """

  @datastore_rpc._positional(2)
  def __init__(self, name, value=None, facet_range=None):
    """Initializer.

    Args:
      name: The name of the facet.
      value: Value of the facet.
      facet_range: A FacetRange to refine facet based on a range.

    Raises:
      TypeError: If any of the parameters have invalid types, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have invalid values.
    """
    self._name = _ConvertToUnicode(name)
    if (value is None) == (facet_range is None):
      raise ValueError('Either value or facet_range should be set but not '
                       'both.')
    self._value = value
    self._facet_range = facet_range

  @property
  def name(self):
    """Returns name of the facet refinement."""
    return self._name

  @property
  def value(self):
    """Returns value of the facet refinement."""
    return self._value

  @property
  def facet_range(self):
    """Returns range of the facet refinement."""
    return self._facet_range

  def ToTokenString(self):
    """Converts this refinement to a token string safe to be used in HTML.

    The format of this string may change.

    Returns:
      A token string safe to be used in HTML for this facet refinement.
    """
    facet_refinement = search_service_pb.FacetRefinement()
    self._CopyToProtocolBuffer(facet_refinement)
    return base64.b64encode(facet_refinement.SerializeToString())

  @staticmethod
  def FromTokenString(token_string):
    """Converts a token string to a FacetRefinement object.

    Do not store token strings between different versions of API as key could
    be incompatible.

    Args:
      token_string: A token string created by ToTokenString method or returned
      by a search result.
    Returns:
      A FacetRefinement object.
    Raises:
      ValueError: If the token_string is invalid.
    """
    ref_pb = search_service_pb.FacetRefinement()

    try:
      ref_pb.ParseFromString(base64.b64decode(token_string))
    except (ProtocolBuffer.ProtocolBufferDecodeError, TypeError), e:


      raise ValueError('Invalid refinement token %s' % token_string, e)

    facet_range = None
    if ref_pb.has_range():
      range_pb = ref_pb.range()
      facet_range = FacetRange(
          start=float(range_pb.start()) if range_pb.has_start() else None,
          end=float(range_pb.end()) if range_pb.has_end() else None)

    return FacetRefinement(ref_pb.name(),
                           value=ref_pb.value() if ref_pb.has_value() else None,
                           facet_range=facet_range)

  def _CopyToProtocolBuffer(self, facet_refinement_pb):
    """Copies This object to a search_service_pb.FacetRefinement."""
    facet_refinement_pb.set_name(self.name)
    if self.value is not None:
      facet_refinement_pb.set_value(_ConvertToUTF8(self.value))
    if self.facet_range is not None:
      self.facet_range._CopyToProtocolBuffer(
          facet_refinement_pb.mutable_range())

  def __repr__(self):
    return _Repr(self, [('name', self.name),
                        ('value', self.value),
                        ('facet_range', self.facet_range)])


def _CopyFieldToProtocolBuffer(field, pb):
  """Copies field's contents to a document_pb.Field protocol buffer."""
  pb.set_name(field.name.encode('utf-8'))
  field_value_pb = pb.mutable_value()
  if field.language:
    field_value_pb.set_language(field.language.encode('utf-8'))
  if field.value is not None:
    field._CopyValueToProtocolBuffer(field_value_pb)
  return pb


class TextField(Field):
  """A Field that has text content.

  The following example shows a text field named signature with Polish content:
    TextField(name='signature', value='brzydka pogoda', language='pl')
  """

  def __init__(self, name, value=None, language=None):
    """Initializer.

    Args:
      name: The name of the field.
      value: A str or unicode object containing text.
      language: The code of the language the value is encoded in.

    Raises:
      TypeError: If value is not a string.
      ValueError: If value is longer than allowed.
    """
    Field.__init__(self, name, _ConvertToUnicode(value), language)

  def _CheckValue(self, value):
    return _CheckText(value)

  def _CopyValueToProtocolBuffer(self, field_value_pb):
    field_value_pb.set_type(document_pb.FieldValue.TEXT)
    self._CopyStringValueToProtocolBuffer(field_value_pb)


class HtmlField(Field):
  """A Field that has HTML content.

  The following example shows an html field named content:
    HtmlField(name='content', value='<html>herbata, kawa</html>', language='pl')
  """

  def __init__(self, name, value=None, language=None):
    """Initializer.

    Args:
      name: The name of the field.
      value: A str or unicode object containing the searchable content of the
        Field.
      language: The code of the language the value is encoded in.

    Raises:
      TypeError: If value is not a string.
      ValueError: If value is longer than allowed.
    """
    Field.__init__(self, name, _ConvertToUnicode(value), language)

  def _CheckValue(self, value):
    return _CheckHtml(value)

  def _CopyValueToProtocolBuffer(self, field_value_pb):
    field_value_pb.set_type(document_pb.FieldValue.HTML)
    self._CopyStringValueToProtocolBuffer(field_value_pb)


class AtomField(Field):
  """A Field that has content to be treated as a single token for indexing.

  The following example shows an atom field named contributor:
    AtomField(name='contributor', value='foo@bar.com')
  """

  def __init__(self, name, value=None, language=None):
    """Initializer.

    Args:
      name: The name of the field.
      value: A str or unicode object to be treated as an indivisible text value.
      language: The code of the language the value is encoded in.

    Raises:
      TypeError: If value is not a string.
      ValueError: If value is longer than allowed.
    """
    Field.__init__(self, name, _ConvertToUnicode(value), language)

  def _CheckValue(self, value):
    return _CheckAtom(value)

  def _CopyValueToProtocolBuffer(self, field_value_pb):
    field_value_pb.set_type(document_pb.FieldValue.ATOM)
    self._CopyStringValueToProtocolBuffer(field_value_pb)


class UntokenizedPrefixField(Field):
  """A field that matches searches on prefixes of the whole field.

  The following example shows an untokenized prefix field named title:
    UntokenizedPrefixField(name='title', value='how to swim freestyle')
  """

  def __init__(self, name, value=None, language=None):
    """Initializer.

    Args:
      name: The name of the field.
      value: The untokenized prefix field value.
      language: The code of the language the value is encoded in.

    Raises:
      TypeError: If value is not a string.
      ValueError: If value is longer than allowed.
    """
    Field.__init__(self, name, _ConvertToUnicode(value), language)

  def _CheckValue(self, value):
    return _CheckPrefix(value)

  def _CopyValueToProtocolBuffer(self, field_value_pb):
    field_value_pb.set_type(document_pb.FieldValue.UNTOKENIZED_PREFIX)
    self._CopyStringValueToProtocolBuffer(field_value_pb)


class TokenizedPrefixField(Field):
  """A field that matches searches on prefixes of its individual terms.

  The following example shows a tokenized prefix field named title:
    TokenizedPrefixField(name='title', value='Goodwill Hunting')
  """

  def __init__(self, name, value=None, language=None):
    """Initializer.

    Args:
      name: The name of the field.
      value: The tokenized prefix field value.
      language: The code of the language the value is encoded in.

    Raises:
      TypeError: If value is not a string.
      ValueError: If value is longer than allowed.
    """
    Field.__init__(self, name, _ConvertToUnicode(value), language)

  def _CheckValue(self, value):
    return _CheckPrefix(value)

  def _CopyValueToProtocolBuffer(self, field_value_pb):
    field_value_pb.set_type(document_pb.FieldValue.TOKENIZED_PREFIX)
    self._CopyStringValueToProtocolBuffer(field_value_pb)


class DateField(Field):
  """A Field that has a date or datetime value.

  The following example shows a date field named creation_date:
    DateField(name='creation_date', value=datetime.date(2011, 03, 11))
  """

  def __init__(self, name, value=None):
    """Initializer.

    Args:
      name: The name of the field.
      value: A datetime.date or a datetime.datetime.

    Raises:
      TypeError: If value is not a datetime.date or a datetime.datetime.
    """
    Field.__init__(self, name, value)

  def _CheckValue(self, value):
    return _CheckDate(value)

  def _CopyValueToProtocolBuffer(self, field_value_pb):
    field_value_pb.set_type(document_pb.FieldValue.DATE)
    field_value_pb.set_string_value(search_util.SerializeDate(self.value))


class NumberField(Field):
  """A Field that has a numeric value.

  The following example shows a number field named size:
    NumberField(name='size', value=10)
  """

  def __init__(self, name, value=None):
    """Initializer.

    Args:
      name: The name of the field.
      value: A numeric value.

    Raises:
      TypeError: If value is not numeric.
      ValueError: If value is out of range.
    """
    Field.__init__(self, name, value)

  def _CheckValue(self, value):
    value = _CheckNumber(value, 'field value', True)
    if value is not None and (value < MIN_NUMBER_VALUE or
                              value > MAX_NUMBER_VALUE):
      raise ValueError('value, %d must be between %d and %d' %
                       (value, MIN_NUMBER_VALUE, MAX_NUMBER_VALUE))
    return value

  def _CopyValueToProtocolBuffer(self, field_value_pb):
    field_value_pb.set_type(document_pb.FieldValue.NUMBER)
    field_value_pb.set_string_value(str(self.value))


class GeoPoint(object):
  """Represents a point on the Earth's surface, in lat, long coordinates."""

  def __init__(self, latitude, longitude):
    """Initializer.

    Args:
      latitude: The angle between the equatorial plan and a line that passes
        through the GeoPoint, between -90 and 90 degrees.
      longitude: The angle east or west from a reference meridian to another
        meridian that passes through the GeoPoint, between -180 and 180 degrees.

    Raises:
      TypeError: If any of the parameters have invalid types, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have invalid values.
    """
    self._latitude = self._CheckLatitude(latitude)
    self._longitude = self._CheckLongitude(longitude)

  @property
  def latitude(self):
    """Returns the angle between equatorial plan and line thru the geo point."""
    return self._latitude

  @property
  def longitude(self):
    """Returns the angle from a reference meridian to another meridian."""
    return self._longitude

  def _CheckLatitude(self, value):
    _CheckNumber(value, 'latitude', True)
    if value < -90.0 or value > 90.0:
      raise ValueError('latitude must be between -90 and 90 degrees '
                       'inclusive, was %f' % value)
    return value

  def _CheckLongitude(self, value):
    _CheckNumber(value, 'longitude', True)
    if value < -180.0 or value > 180.0:
      raise ValueError('longitude must be between -180 and 180 degrees '
                       'inclusive, was %f' % value)
    return value

  def __eq__(self, other):
    return (self.latitude == other.latitude and
      self.longitude == other.longitude)

  def __repr__(self):
    return _Repr(self,
                 [('latitude', self.latitude),
                  ('longitude', self.longitude)])


def _CheckGeoPoint(geo_point):
  """Checks geo_point is a GeoPoint and returns it."""
  if not isinstance(geo_point, GeoPoint):
    raise TypeError('geo_point must be a GeoPoint, got %s' %
                    geo_point.__class__.__name__)
  return geo_point


class GeoField(Field):
  """A Field that has a GeoPoint value.

  The following example shows a geo field named place:

    GeoField(name='place', value=GeoPoint(latitude=-33.84, longitude=151.26))
  """

  def __init__(self, name, value=None):
    """Initializer.

    Args:
      name: The name of the field.
      value: A GeoPoint value.

    Raises:
      TypeError: If value is not numeric.
    """
    Field.__init__(self, name, value)

  def _CheckValue(self, value):
    return _CheckGeoPoint(value)

  def _CopyValueToProtocolBuffer(self, field_value_pb):
    field_value_pb.set_type(document_pb.FieldValue.GEO)
    geo_pb = field_value_pb.mutable_geo()
    geo_pb.set_lat(self.value.latitude)
    geo_pb.set_lng(self.value.longitude)


def _GetValue(value_pb):
  """Gets the value from the value_pb."""
  if value_pb.type() in _PROTO_FIELDS_STRING_VALUE:
    if value_pb.has_string_value():
      return value_pb.string_value()
    return None
  if value_pb.type() == document_pb.FieldValue.DATE:
    if value_pb.has_string_value():
      return search_util.DeserializeDate(value_pb.string_value())
    return None
  if value_pb.type() == document_pb.FieldValue.NUMBER:
    if value_pb.has_string_value():
      return float(value_pb.string_value())
    return None
  if value_pb.type() == document_pb.FieldValue.GEO:
    if value_pb.has_geo():
      geo_pb = value_pb.geo()
      return GeoPoint(latitude=geo_pb.lat(), longitude=geo_pb.lng())
    return None
  raise TypeError('unknown FieldValue type %d' % value_pb.type())


_STRING_TYPES = set([document_pb.FieldValue.TEXT,
                     document_pb.FieldValue.HTML,
                     document_pb.FieldValue.ATOM,
                     document_pb.FieldValue.UNTOKENIZED_PREFIX,
                     document_pb.FieldValue.TOKENIZED_PREFIX])


def _DecodeUTF8(pb_value):
  """Decodes a UTF-8 encoded string into unicode."""
  if pb_value is not None:
    return pb_value.decode('utf-8')
  return None


def _DecodeValue(pb_value, val_type):
  """Decodes a possible UTF-8 encoded string value to unicode."""
  if val_type in _STRING_TYPES:
    return _DecodeUTF8(pb_value)
  return pb_value


def _NewFieldFromPb(pb):
  """Constructs a Field from a document_pb.Field protocol buffer."""
  name = _DecodeUTF8(pb.name())
  val_type = pb.value().type()
  value = _DecodeValue(_GetValue(pb.value()), val_type)
  lang = None
  if pb.value().has_language():
    lang = _DecodeUTF8(pb.value().language())
  if val_type == document_pb.FieldValue.TEXT:
    return TextField(name, value, lang)
  elif val_type == document_pb.FieldValue.HTML:
    return HtmlField(name, value, lang)
  elif val_type == document_pb.FieldValue.ATOM:
    return AtomField(name, value, lang)
  elif val_type == document_pb.FieldValue.UNTOKENIZED_PREFIX:
    return UntokenizedPrefixField(name, value, lang)
  elif val_type == document_pb.FieldValue.TOKENIZED_PREFIX:
    return TokenizedPrefixField(name, value, lang)
  elif val_type == document_pb.FieldValue.DATE:
    return DateField(name, value)
  elif val_type == document_pb.FieldValue.NUMBER:
    return NumberField(name, value)
  elif val_type == document_pb.FieldValue.GEO:
    return GeoField(name, value)
  return InvalidRequest('Unknown field value type %d' % val_type)


class Document(object):
  """Represents a user generated document.

  The following example shows how to create a document consisting of a set
  of fields, some plain text and some in HTML.

  Document(doc_id='document_id',
           fields=[TextField(name='subject', value='going for dinner'),
                   HtmlField(name='body',
                             value='<html>I found a place.</html>'),
                   TextField(name='signature', value='brzydka pogoda',
                             language='pl')],
           facets=[AtomFacet(name='tag', value='food'),
                   NumberFacet(name='priority', value=5.0)],
           language='en')
  """
  _FIRST_JAN_2011 = datetime.datetime(2011, 1, 1)

  def __init__(self, doc_id=None, fields=None, language='en', rank=None,
               facets=None):
    """Initializer.

    Args:
      doc_id: The visible printable ASCII string identifying the document which
        does not start with '!'. Whitespace is excluded from ids. If no id is
        provided, the search service will provide one.
      fields: An iterable of Field instances representing the content of the
        document.
      language: The code of the language used in the field values.
      rank: The rank of this document used to specify the order in which
        documents are returned by search. Rank must be a non-negative integer.
        If not specified, the number of seconds since 1st Jan 2011 is used.
        Documents are returned in descending order of their rank, in absence
        of sorting or scoring options.
      facets: An iterable of Facet instances representing the facets for this
        document.

    Raises:
      TypeError: If any of the parameters have invalid types, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have invalid values.
    """
    doc_id = _ConvertToUnicode(doc_id)
    if doc_id is not None:
      _CheckDocumentId(doc_id)
    self._doc_id = doc_id
    self._fields = _GetList(fields)
    self._facets = _GetList(facets)
    self._language = _CheckLanguage(_ConvertToUnicode(language))


    self._field_map = None


    self._facet_map = None

    doc_rank = rank
    if doc_rank is None:
      doc_rank = self._GetDefaultRank()
    self._rank = self._CheckRank(doc_rank)

    _CheckDocument(self)

  @property
  def doc_id(self):
    """Returns the document identifier."""
    return self._doc_id

  @property
  def fields(self):
    """Returns a list of fields of the document."""
    return self._fields

  @property
  def facets(self):
    """Returns a list of facets of the document."""
    return self._facets

  @property
  def language(self):
    """Returns the code of the language the document fields are written in."""
    return self._language

  @property
  def rank(self):
    """Returns the rank of this document."""
    return self._rank

  def field(self, field_name):
    """Returns the field with the provided field name.

    Args:
      field_name: The name of the field to return.

    Returns:
      A field with the given name.

    Raises:
      ValueError: There is not exactly one field with the given name.
    """
    fields = self[field_name]
    if len(fields) == 1:
      return fields[0]
    raise ValueError(
        'Must have exactly one field with name %s, but found %d.' %
        (field_name, len(fields)))

  def facet(self, facet_name):
    """Returns list of facets with the provided name.

    Args:
      facet_name: The name of the facet to return.

    Returns:
      A list of facets with the given name.
    """
    return self._BuildFacetMap().get(facet_name, [])

  def __setstate__(self, state):
    self.__dict__ = {'_facets': [], '_facet_map': None}
    self.__dict__.update(state)

  def __getitem__(self, field_name):
    """Returns a list of all fields with the provided field name.

    Args:
      field_name: The name of the field to return.

    Returns:
      All fields with the given name, or an empty list if no field with that
      name exists.
    """
    return self._BuildFieldMap().get(field_name, [])

  def __iter__(self):
    """Documents do not support iteration.

    This is provided to raise an explicit exception.
    """
    raise TypeError('Documents do not support iteration.')

  def _BuildFieldMap(self):
    """Lazily build the field map."""
    if self._field_map is None:
      field_map = {}
      for field in self._fields:
        field_map.setdefault(field.name, []).append(field)
      self._field_map = field_map
    return self._field_map

  def _BuildFacetMap(self):
    """Lazily build the facet map."""
    if self._facet_map is None:
      facet_map = {}
      for facet in self._facets:
        facet_map.setdefault(facet.name, []).append(facet)
      self._facet_map = facet_map
    return self._facet_map

  def _CheckRank(self, rank):
    """Checks if rank is valid, then returns it."""
    return _CheckInteger(rank, 'rank', upper_bound=sys.maxint)

  def _GetDefaultRank(self):
    """Returns a default rank as total seconds since 1st Jan 2011."""
    td = datetime.datetime.now() - Document._FIRST_JAN_2011
    return td.seconds + (td.days * 24 * 3600)

  def __repr__(self):
    return _Repr(
        self, [('doc_id', self.doc_id), ('fields', self.fields),
               ('facets', self.facets), ('language', self.language),
               ('rank', self.rank)])

  def __eq__(self, other):
    return (isinstance(other, type(self)) and self.doc_id == other.doc_id and
            self.rank == other.rank and self.language == other.language
            and self.fields == other.fields and self.facets == other.facets)

  def __ne__(self, other):
    return not self == other

  def __key(self):
    return self.doc_id

  def __hash__(self):
    return hash(self.__key())

  def __str__(self):
    return repr(self)


def _CopyDocumentToProtocolBuffer(document, pb):
  """Copies Document to a document_pb.Document protocol buffer."""
  pb.set_storage(document_pb.Document.DISK)
  if document.doc_id:
    pb.set_id(document.doc_id.encode('utf-8'))
  if document.language:
    pb.set_language(document.language.encode('utf-8'))
  for field in document.fields:
    field_pb = pb.add_field()
    _CopyFieldToProtocolBuffer(field, field_pb)
  for facet in document.facets:
    facet_pb = pb.add_facet()
    facet._CopyToProtocolBuffer(facet_pb)
  pb.set_order_id(document.rank)
  return pb


def _NewFieldsFromPb(field_list):
  """Returns a list of Field copied from a document_pb.Document proto buf."""
  return [_NewFieldFromPb(f) for f in field_list]


def _NewDocumentFromPb(doc_pb):
  """Constructs a Document from a document_pb.Document protocol buffer."""
  lang = None
  if doc_pb.has_language():
    lang = _DecodeUTF8(doc_pb.language())
  return Document(doc_id=_DecodeUTF8(doc_pb.id()),
                  fields=_NewFieldsFromPb(doc_pb.field_list()),
                  language=lang,
                  rank=doc_pb.order_id(),
                  facets=_NewFacetsFromPb(doc_pb.facet_list()))


def _QuoteString(argument):
  return '"' + argument.replace('"', '\\\"') + '"'


class FieldExpression(object):
  """Represents an expression that will be computed for each result returned.

  For example,
    FieldExpression(name='content_snippet',
                    expression='snippet("very important", content)')
  means a computed field 'content_snippet' will be returned with each search
  result, which contains HTML snippets of the 'content' field which match
  the query 'very important'.
  """

  MAXIMUM_EXPRESSION_LENGTH = 1000
  MAXIMUM_OPERATOR_LENGTH = 100

  def __init__(self, name, expression):
    """Initializer.

    Args:
      name: The name of the computed field for the expression.
      expression: The expression to evaluate and return in a field with
        given name in results. See
        https://developers.google.com/appengine/docs/python/search/overview#Expressions
        for a list of legal expressions.

    Raises:
      TypeError: If any of the parameters has an invalid type, or an unknown
        attribute is passed.
      ValueError: If any of the parameters has an invalid value.
      ExpressionError: If the expression string is not parseable.
    """
    self._name = _CheckFieldName(_ConvertToUnicode(name))
    if expression is None:
      raise ValueError('expression must be a FieldExpression, got None')
    if not isinstance(expression, basestring):
      raise TypeError('expression must be a FieldExpression, got %s' %
                      expression.__class__.__name__)
    self._expression = _CheckExpression(_ConvertToUnicode(expression))

  @property
  def name(self):
    """Returns name of the expression to return in search results."""
    return self._name

  @property
  def expression(self):
    """Returns a string containing an expression returned in search results."""
    return self._expression

  def __repr__(self):
    return _Repr(
        self, [('name', self.name), ('expression', self.expression)])


def _CopyFieldExpressionToProtocolBuffer(field_expression, pb):
  """Copies FieldExpression to a search_service_pb.FieldSpec_Expression."""
  pb.set_name(field_expression.name.encode('utf-8'))
  pb.set_expression(field_expression.expression.encode('utf-8'))


class SortOptions(object):
  """Represents a mulit-dimensional sort of Documents.

   The following code shows how to sort documents based on product rating
   in descending order and then cheapest product within similarly rated
   products, sorting at most 1000 documents:

     SortOptions(expressions=[
         SortExpression(expression='rating',
             direction=SortExpression.DESCENDING, default_value=0),
         SortExpression(expression='price + tax',
             direction=SortExpression.ASCENDING, default_value=999999.99)],
         limit=1000)
  """

  def __init__(self, expressions=None, match_scorer=None, limit=1000):
    """Initializer.

    Args:
      expressions: An iterable of SortExpression representing a
        multi-dimensional sort of Documents.
      match_scorer: A match scorer specification which may be used to
        score documents or in a SortExpression combined with other features.
      limit: The limit on the number of documents to score or sort.

    Raises:
      TypeError: If any of the parameters has an invalid type, or an unknown
        attribute is passed.
      ValueError: If any of the parameters has an invalid value.
    """
    self._match_scorer = match_scorer
    self._expressions = _GetList(expressions)
    for expression in self._expressions:
      if not isinstance(expression, SortExpression):
        raise TypeError('expression must be a SortExpression, got %s' %
                        expression.__class__.__name__)
    self._limit = _CheckSortLimit(limit)

  @property
  def expressions(self):
    """A list of SortExpression specifying a multi-dimensional sort."""
    return self._expressions

  @property
  def match_scorer(self):
    """Returns a match scorer to score documents with."""
    return self._match_scorer

  @property
  def limit(self):
    """Returns the limit on the number of documents to score or sort."""
    return self._limit

  def __repr__(self):
    return _Repr(
        self, [('match_scorer', self.match_scorer),
               ('expressions', self.expressions),
               ('limit', self.limit)])


class MatchScorer(object):
  """Assigns a document score based on term frequency.

  If you add a MatchScorer to a SortOptions as in the following code:

      sort_opts = search.SortOptions(match_scorer=search.MatchScorer())

  then, this will sort the documents in descending score order. The scores
  will be positive. If you want to sort in ascending order, then use the
  following code:

      sort_opts = search.SortOptions(match_scorer=search.MatchScorer(),
          expressions=[search.SortExpression(
              expression='_score', direction=search.SortExpression.ASCENDING,
              default_value=0.0)])

  The scores in this case will be negative.
  """

  def __init__(self):
    """Initializer.

    Raises:
      TypeError: If any of the parameters has an invalid type, or an unknown
        attribute is passed.
      ValueError: If any of the parameters has an invalid value.
    """

  def __repr__(self):
    return _Repr(self, [])


class RescoringMatchScorer(MatchScorer):
  """Assigns a document score based on term frequency weighted by doc parts.

  If you add a RescoringMatchScorer to a SortOptions as in the following code:

      sort_opts = search.SortOptions(match_scorer=search.RescoringMatchScorer())

  then, this will sort the documents in descending score order. The scores
  will be positive.  If you want to sort in ascending order, then use the
  following code:

      sort_opts = search.SortOptions(match_scorer=search.RescoringMatchScorer(),
          expressions=[search.SortExpression(
              expression='_score', direction=search.SortExpression.ASCENDING,
              default_value=0.0)])

  The scores in this case will be negative.
  """

  def __init__(self):
    """Initializer.

    Raises:
      TypeError: If any of the parameters has an invalid type, or an unknown
        attribute is passed.
      ValueError: If any of the parameters has an invalid value.
    """
    super(RescoringMatchScorer, self).__init__()


def _CopySortExpressionToProtocolBuffer(sort_expression, pb):
  """Copies a SortExpression to a search_service_pb.SortSpec protocol buffer."""
  pb.set_sort_expression(sort_expression.expression.encode('utf-8'))
  if sort_expression.direction == SortExpression.ASCENDING:
    pb.set_sort_descending(False)
  if sort_expression.default_value is not None:
    if isinstance(sort_expression.default_value, basestring):
      pb.set_default_value_text(sort_expression.default_value.encode('utf-8'))
    elif (isinstance(sort_expression.default_value, datetime.datetime) or
          isinstance(sort_expression.default_value, datetime.date)):
      pb.set_default_value_text(str(
          search_util.EpochTime(sort_expression.default_value)))
    else:
      pb.set_default_value_numeric(sort_expression.default_value)
  return pb


def _CopyMatchScorerToScorerSpecProtocolBuffer(match_scorer, limit, pb):
  """Copies a MatchScorer to a search_service_pb.ScorerSpec."""
  if isinstance(match_scorer, RescoringMatchScorer):
    pb.set_scorer(search_service_pb.ScorerSpec.RESCORING_MATCH_SCORER)
  elif isinstance(match_scorer, MatchScorer):
    pb.set_scorer(search_service_pb.ScorerSpec.MATCH_SCORER)
  else:
    raise TypeError(
        'match_scorer must be a MatchScorer or RescoringMatchRescorer, '
        'got %s' % match_scorer.__class__.__name__)
  pb.set_limit(limit)
  return pb


def _CopySortOptionsToProtocolBuffer(sort_options, params):
  """Copies the SortOptions into the SearchParams proto buf."""
  for expression in sort_options.expressions:
    sort_spec_pb = params.add_sort_spec()
    _CopySortExpressionToProtocolBuffer(expression, sort_spec_pb)
  if sort_options.match_scorer:
    scorer_spec = params.mutable_scorer_spec()
    _CopyMatchScorerToScorerSpecProtocolBuffer(
        sort_options.match_scorer, sort_options.limit, scorer_spec)
    scorer_spec.set_limit(sort_options.limit)
  else:
    params.mutable_scorer_spec().set_limit(sort_options.limit)


class SortExpression(object):
  """Sort by a user specified scoring expression.

  For example, the following will sort documents on a numeric field named
  'length' in ascending order, assigning a default value of sys.maxint for
  documents which do not specify a 'length' field.

    SortExpression(expression='length',
                   direction=sort.SortExpression.ASCENDING,
                   default_value=sys.maxint)

  The following example will sort documents on a date field named
  'published_date' in descending order, assigning a default value of
  1999-12-31 for documents which do not specify a 'published_date' field.

    SortExpression(expression='published_date',
                   default_value=datetime.date(year=1999, month=12, day=31))

  The following example will sort documents on a text field named 'subject'
  in descending order, assigning a default value of '' for documents which
  do not specify a 'subject' field.

    SortExpression(expression='subject')
  """


  try:
    MAX_FIELD_VALUE = unichr(0x10ffff) * 80
  except ValueError:

    MAX_FIELD_VALUE = unichr(0xffff) * 80

  MIN_FIELD_VALUE = u''


  ASCENDING, DESCENDING = ('ASCENDING', 'DESCENDING')

  _DIRECTIONS = frozenset([ASCENDING, DESCENDING])

  def __init__(self, expression, direction=DESCENDING, default_value=None):
    """Initializer.

    Args:
      expression: An expression to be evaluated on each matching document
        to sort by. The expression must evaluate to a text or numeric value.
        The expression can simply be a field name, or some compound expression
        such as "_score + count(likes) * 0.1" which will add the score from a
        scorer to a count of the values of a likes field times 0.1. See
        https://developers.google.com/appengine/docs/python/search/overview#Expressions
        for a list of legal expressions.
      direction: The direction to sort the search results, either ASCENDING
        or DESCENDING
      default_value: The default value of the expression. The default_value is
        returned if expression cannot be calculated, for example, if the
        expression is a field name and no value for that named field exists.
        A text value must be specified for text sorts. A numeric value must be
        specified for numeric sorts. A date value must be specified for date
        sorts.

    Raises:
      TypeError: If any of the parameters has an invalid type, or an unknown
        attribute is passed.
      ValueError: If any of the parameters has an invalid value.
      ExpressionError: If the expression string is not parseable.
    """
    self._expression = _ConvertToUnicode(expression)
    self._direction = self._CheckDirection(direction)
    if self._expression is None:
      raise TypeError('expression must be a SortExpression, got None')
    _CheckExpression(self._expression)
    self._default_value = default_value
    if self._default_value is not None:
      if isinstance(self.default_value, basestring):
        self._default_value = _ConvertToUnicode(default_value)
        _CheckText(self._default_value, 'default_value')
      elif not isinstance(self._default_value,
                          (int, long, float, datetime.date, datetime.datetime)):
        raise TypeError('default_value must be text, numeric or datetime, got '
                        '%s' % self._default_value.__class__.__name__)

  @property
  def expression(self):
    """Returns the expression to sort by."""
    return self._expression

  @property
  def direction(self):
    """Returns the direction to sort expression: ASCENDING or DESCENDING."""
    return self._direction

  @property
  def default_value(self):
    """Returns a default value for the expression if no value computed."""
    return self._default_value

  def _CheckDirection(self, direction):
    """Checks direction is a valid SortExpression direction and returns it."""
    return _CheckEnum(direction, 'direction', values=self._DIRECTIONS)

  def __repr__(self):
    return _Repr(
        self, [('expression', self.expression),
               ('direction', self.direction),
               ('default_value', self.default_value)])


class FacetResultValue(object):
  """A facet value as part of search result."""

  def __init__(self, label, count, refinement):
    """Initializer.

    Args:
      label: The label of the facet. Either the name of the facet, user
        provider range name, or system generated range name.
      count: Occurrence frequency of the label for the given facet.
      refinement: The FacetRefinement object for this value. Passing this object
        or its string token to the next query will refine the result based on
        this facet value.
    Raises:
      TypeError: If any of the parameters have invalid types, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have invalid values.
    """
    self._label = label
    self._count = count
    _CheckType(refinement, FacetRefinement, 'refinement')
    self._refinement_token = refinement.ToTokenString()
    self._refinement = refinement

  @property
  def label(self):
    """Returns the label for this facet value."""
    return self._label

  @property
  def count(self):
    """Returns the count for this facet value."""
    return self._count

  @property
  def refinement_token(self):
    """Returns the refinement token string for this facet value."""
    return self._refinement_token

  def __repr__(self):
    return _Repr(self, [('label', self.label),
                        ('count', self.count),
                        ('refinement', self._refinement)])


class FacetResult(object):
  """Represents a facet result returned from a search with faceted search."""

  def __init__(self, name, values=None):
    """Initializer.

    Args:
      name: The name of this facet result.
      values: An iterable of FacetResultValue instances representing values for
        this document.
    Raises:
      TypeError: If any of the parameters have invalid types, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have invalid values.
    """
    self._name = _ConvertToUnicode(name)
    self._values = values

  @property
  def name(self):
    """Returns the name of this facet result."""
    return self._name

  @property
  def values(self):
    """Returns values for this facet result."""
    return self._values

  def __repr__(self):
    return _Repr(self, [('name', self.name),
                        ('values', self.values)])


class ScoredDocument(Document):
  """Represents a scored document returned from a search."""

  def __init__(self, doc_id=None, fields=None, language='en',
               sort_scores=None, expressions=None, cursor=None, rank=None,
               facets=None):
    """Initializer.

    Args:
      doc_id: The visible printable ASCII string identifying the document which
        does not start with '!'. Whitespace is excluded from ids. If no id is
        provided, the search service will provide one.
      fields: An iterable of Field instances representing the content of the
        document.
      language: The code of the language used in the field values.
      sort_scores: The list of scores assigned during sort evaluation. Each
        sort dimension is included. Positive scores are used for ascending
        sorts; negative scores for descending.
      expressions: The list of computed fields which are the result of
        expressions requested.
      cursor: A cursor associated with the document.
      rank: The rank of this document. A rank must be a non-negative integer
        less than sys.maxint. If not specified, the number of seconds since
        1st Jan 2011 is used. Documents are returned in descending order of
        their rank.
      facets: An iterable of Facet instances representing the facets for this
        document.

    Raises:
      TypeError: If any of the parameters have invalid types, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have invalid values.
    """
    super(ScoredDocument, self).__init__(doc_id=doc_id, fields=fields,
                                         language=language, rank=rank,
                                         facets=facets)
    self._sort_scores = self._CheckSortScores(_GetList(sort_scores))
    self._expressions = _GetList(expressions)
    if cursor is not None and not isinstance(cursor, Cursor):
      raise TypeError('cursor must be a Cursor, got %s' %
                      cursor.__class__.__name__)
    self._cursor = cursor

  @property
  def sort_scores(self):
    """The list of scores assigned during sort evaluation.

    Each sort dimension is included. Positive scores are used for ascending
    sorts; negative scores for descending.

    Returns:
      The list of numeric sort scores.
    """
    return self._sort_scores

  @property
  def expressions(self):
    """The list of computed fields the result of expression evaluation.

    For example, if a request has
      FieldExpression(name='snippet', 'snippet("good story", content)')
    meaning to compute a snippet field containing HTML snippets extracted
    from the matching of the query 'good story' on the field 'content'.
    This means a field such as the following will be returned in expressions
    for the search result:
      HtmlField(name='snippet', value='that was a <b>good story</b> to finish')

    Returns:
      The computed fields.
    """
    return self._expressions

  @property
  def cursor(self):
    """A cursor associated with a result, a continued search starting point.

    To get this cursor to appear, set the Index.cursor_type to
    Index.RESULT_CURSOR, otherwise this will be None.

    Returns:
      The result cursor.
    """
    return self._cursor

  def _CheckSortScores(self, sort_scores):
    """Checks sort_scores is a list of floats, and returns it."""
    for sort_score in sort_scores:
      _CheckNumber(sort_score, 'sort_scores')
    return sort_scores

  def __repr__(self):
    return _Repr(self, [('doc_id', self.doc_id),
                        ('fields', self.fields),
                        ('language', self.language),
                        ('rank', self.rank),
                        ('sort_scores', self.sort_scores),
                        ('expressions', self.expressions),
                        ('cursor', self.cursor)])


class SearchResults(object):
  """Represents the result of executing a search request."""

  def __init__(self, number_found, results=None, cursor=None, facets=None):
    """Initializer.

    Args:
      number_found: The number of documents found for the query.
      results: The list of ScoredDocuments returned from executing a
        search request.
      cursor: A Cursor to continue the search from the end of the
        search results.
      facets: The list of FacetResults returned from executing a search request
        with faceted search enabled.

    Raises:
      TypeError: If any of the parameters have an invalid type, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have an invalid value.
    """
    self._number_found = _CheckInteger(number_found, 'number_found')
    self._results = _GetList(results)
    if cursor is not None and not isinstance(cursor, Cursor):
      raise TypeError('cursor must be a Cursor, got %s' %
                      cursor.__class__.__name__)
    self._cursor = cursor
    self._facets = _GetList(facets)

  def __iter__(self):

    for result in self.results:
      yield result

  @property
  def results(self):
    """Returns the list of ScoredDocuments that matched the query."""
    return self._results

  @property
  def number_found(self):
    """Returns the number of documents which were found for the search.

    Note that this is an approximation and not an exact count.
    If QueryOptions.number_found_accuracy parameter is set to 100
    for example, then number_found <= 100 is accurate.

    Returns:
      The number of documents found.
    """
    return self._number_found

  @property
  def cursor(self):
    """Returns a cursor that can be used to continue search from last result.

    This corresponds to using a ResultsCursor in QueryOptions,
    otherwise this will be None.

    Returns:
      The results cursor.
    """
    return self._cursor

  @property
  def facets(self):
    """Return the list of FacetResults that found in matched documents."""
    return self._facets

  def __setstate__(self, state):
    self.__dict__ = {'_facets': []}
    self.__dict__.update(state)

  def __repr__(self):
    return _Repr(self, [('results', self.results),
                        ('number_found', self.number_found),
                        ('cursor', self.cursor),
                        ('facets', self.facets)])


class GetResponse(object):
  """Represents the result of executing a get request.

  For example, the following code shows how a response could be used
  to determine which documents were successfully removed or not.

  response = index.get_range()
  for document in response:
    print "document ", document
  """

  def __init__(self, results=None):
    """Initializer.

    Args:
      results: The results returned from an index ordered by Id.

    Raises:
      TypeError: If any of the parameters have an invalid type, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have an invalid value.
    """
    self._results = _GetList(results)

  def __iter__(self):
    for result in self.results:
      yield result

  def __len__(self):
    return len(self.results)

  def __getitem__(self, index):
    return self.results[index]

  @property
  def results(self):
    """Returns a list of results ordered by Id from the index."""
    return self._results

  def __repr__(self):
    return _Repr(self, [('results', self.results)])


class Cursor(object):
  """Specifies how to get the next page of results in a search.

  A cursor returned in a previous set of search results to use as a starting
  point to retrieve the next set of results. This can get you better
  performance, and also improves the consistency of pagination through index
  updates.

  The following shows how to use the cursor to get the next page of results:

  # get the first set of results; the first cursor is used to specify
  # that cursors are to be returned in the SearchResults.
  results = index.search(Query(query_string='some stuff',
      QueryOptions(cursor=Cursor()))

  # get the next set of results
  results = index.search(Query(query_string='some stuff',
      QueryOptions(cursor=results.cursor)))

  If you want to continue search from any one of the ScoredDocuments in
  SearchResults, then you can set Cursor.per_result to True.

  # get the first set of results; the first cursor is used to specify
  # that cursors are to be returned in the SearchResults.
  results = index.search(Query(query_string='some stuff',
      QueryOptions(cursor=Cursor(per_result=True)))

  # this shows how to access the per_document cursors returned from a search
  per_document_cursor = None
  for scored_document in results:
    per_document_cursor = scored_document.cursor

  # get the next set of results
  results = index.search(Query(query_string='some stuff',
      QueryOptions(cursor=per_document_cursor)))
  """



  def __init__(self, web_safe_string=None, per_result=False):
    """Initializer.

    Args:
      web_safe_string: The cursor string returned from the search service to
        be interpreted by the search service to get the next set of results.
      per_result: A bool when true will return a cursor per ScoredDocument in
        SearchResults, otherwise will return a single cursor for the whole
        SearchResults. If using offset this is ignored, as the user is
        responsible for calculating a next offset if any.
    Raises:

      ValueError: if the web_safe_string is not of required format.
    """
    self._web_safe_string = _CheckCursor(_ConvertToUnicode(web_safe_string))
    self._per_result = per_result
    if self._web_safe_string:
      parts = self._web_safe_string.split(':', 1)
      if len(parts) != 2 or parts[0] not in ['True', 'False']:
        raise ValueError('invalid format for web_safe_string, got %s' %
                         self._web_safe_string)
      self._internal_cursor = parts[1]

      self._per_result = (parts[0] == 'True')

  @property
  def web_safe_string(self):
    """Returns the cursor string generated by the search service."""
    return self._web_safe_string

  @property
  def per_result(self):
    """Returns whether to return a cursor for each ScoredDocument in results."""
    return self._per_result

  def __repr__(self):
    return _Repr(self, [('web_safe_string', self.web_safe_string)])


def _ToWebSafeString(per_result, internal_cursor):
  """Returns the web safe string combining per_result with internal cursor."""
  return str(per_result) + ':' + internal_cursor


def _CheckQuery(query):
  """Checks a query is a valid query string."""
  _ValidateString(query, 'query', MAXIMUM_QUERY_LENGTH, empty_ok=True)
  if query is None:
    raise TypeError('query must be unicode, got None')
  if query.strip():
    try:
      query_parser.Parse(query)
    except query_parser.QueryException, e:
      raise QueryError('Failed to parse query "%s"' % query)
  return query


def _CheckLimit(limit):
  """Checks the limit of documents to return is an integer within range."""
  return _CheckInteger(
      limit, 'limit', zero_ok=False,
      upper_bound=MAXIMUM_DOCUMENTS_RETURNED_PER_SEARCH)


def _CheckFacetDepth(depth):
  """Checks the facet depth to return is an integer within range."""
  if depth is None:
    return None
  else:
    return _CheckInteger(
        depth, 'depth', zero_ok=False,
        upper_bound=MAXIMUM_DEPTH_FOR_FACETED_SEARCH)


def _CheckFacetDiscoveryLimit(facet_limit):
  """Checks the facet limit is an integer within range."""
  if facet_limit is None:
    return None
  else:
    return _CheckInteger(
        facet_limit, 'discover_facet_limit',
        upper_bound=MAXIMUM_FACETS_TO_RETURN)


def _CheckFacetValueLimit(value_limit):
  """Checks the facet value limit is an integer within range."""
  if value_limit is None:
    return None
  else:
    return _CheckInteger(
        value_limit, 'facet_value_limit', zero_ok=False,
        upper_bound=MAXIMUM_FACET_VALUES_TO_RETURN)


def _CheckOffset(offset):
  """Checks the offset in document list is an integer within range."""
  return _CheckInteger(
      offset, 'offset', zero_ok=True,
      upper_bound=MAXIMUM_SEARCH_OFFSET)


def _CheckNumberFoundAccuracy(number_found_accuracy):
  """Checks the accuracy is an integer within range."""
  return _CheckInteger(
      number_found_accuracy, 'number_found_accuracy',
      zero_ok=False, upper_bound=MAXIMUM_NUMBER_FOUND_ACCURACY)


def _CheckCursor(cursor):
  """Checks the cursor if specified is a string which is not too long."""
  return _ValidateString(cursor, 'cursor', _MAXIMUM_CURSOR_LENGTH,
                         empty_ok=True)


def _CheckNumberOfFields(returned_expressions, snippeted_fields,
                         returned_fields):
  """Checks the count of all field kinds is less than limit."""
  number_expressions = (len(returned_expressions) + len(snippeted_fields) +
                        len(returned_fields))
  if number_expressions > MAXIMUM_FIELDS_RETURNED_PER_SEARCH:
    raise ValueError(
        'too many fields, snippets or expressions to return  %d > maximum %d'
        % (number_expressions, MAXIMUM_FIELDS_RETURNED_PER_SEARCH))


class FacetOptions(object):
  """Options for processing facet reults of a query."""

  @datastore_rpc._positional(1)
  def __init__(self, discovery_limit=10, discovery_value_limit=None,
               depth=None):
    """Initializer.

    Options include number of facets to discover, number of values for each
    facet and the depth of the result to be considered for facet computation.

    If you wish to discovering 5 facets with 10 values each in 6000 search
    results, you can use a FacetOption object like this:

    facet_option = FacetOptions(discover_facet_limit=5,
                                discover_facet_value_limit=10,
                                depth=6000)

    Args:
      discovery_limit: Number of facets to discover if facet discovery is
        turned on. If None, discover facets will be disabled.
      discovery_value_limit: Number of values to be discovered for each of
        the top discovered facets.
      depth: Number of documents in query results to evaluate to gather
        facet information.
    Raises:
      TypeError: If an unknown attribute is passed.
      ValueError: If any of the parameters have invalid values (e.g., a
        negative depth).
    """
    self._discovery_limit = _CheckFacetDiscoveryLimit(discovery_limit)
    self._discovery_value_limit = _CheckFacetValueLimit(
        discovery_value_limit)
    self._depth = _CheckFacetDepth(depth)

  @property
  def discovery_limit(self):
    """Returns the number of facets to discover."""
    return self._discovery_limit

  @property
  def discovery_value_limit(self):
    """Returns the number of values to discover for each facet."""
    return self._discovery_value_limit

  @property
  def depth(self):
    """Returns the number of documents to analyze for facet discovery."""
    return self._depth

  def __repr__(self):
    return _Repr(
        self, [('discovery_limit', self.discovery_limit),
               ('discovery_value_limit', self.discovery_value_limit),
               ('depth', self._depth)])

  def _CopyToProtocolBuffer(self, params):
    """Copies a FacetOptions object to a SearchParams proto buff."""
    if self.discovery_limit is not None:
      params.set_auto_discover_facet_count(self.discovery_limit)
    if self.discovery_value_limit is not None:
      params.mutable_facet_auto_detect_param().set_value_limit(
          self.discovery_value_limit)
    if self.depth is not None:
      params.set_facet_depth(self.depth)


class QueryOptions(object):
  """Options for post-processing results for a query.

  Options include the ability to sort results, control which document fields
  to return, produce snippets of fields and compute and sort by complex
  scoring expressions.

  If you wish to randomly access pages of search results, you can use an
  offset:

  # get the first set of results
  page_size = 10
  results = index.search(Query(query_string='some stuff',
      QueryOptions(limit=page_size))

  # calculate pages
  pages = results.found_count / page_size

  # user chooses page and hence an offset into results
  next_page = ith * page_size

  # get the search results for that page
  results = index.search(Query(query_string='some stuff',
      QueryOptions(limit=page_size, offset=next_page))
  """

  def __init__(self, limit=20, number_found_accuracy=None, cursor=None,
               offset=None, sort_options=None, returned_fields=None,
               ids_only=False, snippeted_fields=None,
               returned_expressions=None):


    """Initializer.

    For example, the following code fragment requests a search for
    documents where 'first' occurs in subject and 'good' occurs anywhere,
    returning at most 20 documents, starting the search from 'cursor token',
    returning another single cursor for the SearchResults, sorting by subject in
    descending order, returning the author, subject, and summary fields as well
    as a snippeted field content.

      results = index.search(Query(
          query='subject:first good',
          options=QueryOptions(
            limit=20,
            cursor=Cursor(),
            sort_options=SortOptions(
                expressions=[
                    SortExpression(expression='subject')],
                limit=1000),
            returned_fields=['author', 'subject', 'summary'],
            snippeted_fields=['content'])))

    Args:
      limit: The limit on number of documents to return in results.
      number_found_accuracy: The minimum accuracy requirement for
        SearchResults.number_found. If set, the number_found will be
        accurate up to at least that number. For example, when set to 100,
        any SearchResults with number_found <= 100 is accurate. This option
        may add considerable latency/expense, especially when used with
        returned_fields.
      cursor: A Cursor describing where to get the next set of results,
        or to provide next cursors in SearchResults.
      offset: The offset is number of documents to skip in search results. This
        is an alternative to using a query cursor, but allows random access into
        the results. Using offsets rather than cursors are more expensive. You
        can only use either cursor or offset, but not both. Using an offset
        means that no cursor is returned in SearchResults.cursor, nor in each
        ScoredDocument.cursor.
      sort_options: A SortOptions specifying a multi-dimensional sort over
        search results.
      returned_fields: An iterable of names of fields to return in search
        results.
      ids_only: Only return document ids, do not return any fields.
      snippeted_fields: An iterable of names of fields to snippet and return
        in search result expressions.
      returned_expressions: An iterable of FieldExpression to evaluate and
        return in search results.
    Raises:
      TypeError: If an unknown iterator_options or sort_options is passed.
      ValueError: If ids_only and returned_fields are used together.
      ExpressionError: If one of the returned expression strings is not
        parseable.
    """
    self._limit = _CheckLimit(limit)
    self._number_found_accuracy = _CheckNumberFoundAccuracy(
        number_found_accuracy)
    if cursor is not None and not isinstance(cursor, Cursor):
      raise TypeError('cursor must be a Cursor, got %s' %
                      cursor.__class__.__name__)
    if cursor is not None and offset is not None:
      raise ValueError('cannot set cursor and offset together')
    self._cursor = cursor
    self._offset = _CheckOffset(offset)
    if sort_options is not None and not isinstance(sort_options, SortOptions):
      raise TypeError('sort_options must be a SortOptions, got %s' %
                      sort_options.__class__.__name__)
    self._sort_options = sort_options

    self._returned_fields = _ConvertToUnicodeList(returned_fields)
    _CheckFieldNames(self._returned_fields)
    self._ids_only = ids_only
    if self._ids_only and self._returned_fields:
      raise ValueError('cannot have ids_only and returned_fields set together')
    self._snippeted_fields = _ConvertToUnicodeList(snippeted_fields)
    _CheckFieldNames(self._snippeted_fields)
    self._returned_expressions = _ConvertToList(returned_expressions)
    for expression in self._returned_expressions:
      _CheckFieldName(_ConvertToUnicode(expression.name))
      _CheckExpression(_ConvertToUnicode(expression.expression))
    _CheckNumberOfFields(self._returned_expressions, self._snippeted_fields,
                         self._returned_fields)

  @property
  def limit(self):
    """Returns a limit on number of documents to return in results."""
    return self._limit

  @property
  def number_found_accuracy(self):
    """Returns minimum accuracy requirement for SearchResults.number_found."""
    return self._number_found_accuracy

  @property
  def cursor(self):
    """Returns the Cursor for the query."""
    return self._cursor

  @property
  def offset(self):
    """Returns the number of documents in search results to skip."""
    return self._offset

  @property
  def sort_options(self):
    """Returns a SortOptions."""
    return self._sort_options

  @property
  def returned_fields(self):
    """Returns an iterable of names of fields to return in search results."""
    return self._returned_fields

  @property
  def ids_only(self):
    """Returns whether to return only document ids in search results."""
    return self._ids_only

  @property
  def snippeted_fields(self):
    """Returns iterable of field names to snippet and return in results."""
    return self._snippeted_fields

  @property
  def returned_expressions(self):
    """Returns iterable of FieldExpression to return in results."""
    return self._returned_expressions

  def __repr__(self):
    return _Repr(self, [('limit', self.limit),
                        ('number_found_accuracy', self.number_found_accuracy),
                        ('cursor', self.cursor),
                        ('sort_options', self.sort_options),
                        ('returned_fields', self.returned_fields),
                        ('ids_only', self.ids_only),
                        ('snippeted_fields', self.snippeted_fields),
                        ('returned_expressions', self.returned_expressions)])


def _CopyQueryOptionsObjectToProtocolBuffer(query, options, params):
  """Copies a QueryOptions object to a SearchParams proto buff."""
  offset = 0
  web_safe_string = None
  cursor_type = None
  offset = options.offset
  if options.cursor:
    cursor = options.cursor
    if cursor.per_result:
      cursor_type = search_service_pb.SearchParams.PER_RESULT
    else:
      cursor_type = search_service_pb.SearchParams.SINGLE
    if isinstance(cursor, Cursor) and cursor.web_safe_string:
      web_safe_string = cursor._internal_cursor
  _CopyQueryOptionsToProtocolBuffer(
      query, offset, options.limit, options.number_found_accuracy,
      web_safe_string, cursor_type, options.ids_only, options.returned_fields,
      options.snippeted_fields, options.returned_expressions,
      options.sort_options, params)


def _CopyQueryOptionsToProtocolBuffer(
    query, offset, limit, number_found_accuracy, cursor, cursor_type, ids_only,
    returned_fields, snippeted_fields, returned_expressions, sort_options,
    params):
  """Copies fields of QueryOptions to params protobuf."""
  if offset:
    params.set_offset(offset)
  params.set_limit(limit)
  if number_found_accuracy is not None:
    params.set_matched_count_accuracy(number_found_accuracy)
  if cursor:
    params.set_cursor(cursor.encode('utf-8'))
  if cursor_type is not None:
    params.set_cursor_type(cursor_type)
  if ids_only:
    params.set_keys_only(ids_only)
  if returned_fields or snippeted_fields or returned_expressions:
    field_spec_pb = params.mutable_field_spec()
    for field in returned_fields:
      field_spec_pb.add_name(field.encode('utf-8'))
    for snippeted_field in snippeted_fields:
      expression = u'snippet(%s, %s)' % (_QuoteString(query), snippeted_field)
      _CopyFieldExpressionToProtocolBuffer(
          FieldExpression(name=snippeted_field, expression=expression),
          field_spec_pb.add_expression())
    for expression in returned_expressions:
      _CopyFieldExpressionToProtocolBuffer(
          expression, field_spec_pb.add_expression())

  if sort_options is not None:
    _CopySortOptionsToProtocolBuffer(sort_options, params)


class Query(object):
  """Represents a request on the search service to query the index."""

  @datastore_rpc._positional(3)
  def __init__(self, query_string, options=None, enable_facet_discovery=False,
               return_facets=None, facet_options=None, facet_refinements=None):



    """Initializer.

    For example, the following code fragment requests a search for
    documents where 'first' occurs in subject and 'good' occurs anywhere,
    returning at most 20 documents, starting the search from 'cursor token',
    returning another single document cursor for the results, sorting by
    subject in descending order, returning the author, subject, and summary
    fields as well as a snippeted field content.

      results = index.search(Query(
          query_string='subject:first good',
          options=QueryOptions(
              limit=20,
              cursor=Cursor(),
              sort_options=SortOptions(
                  expressions=[
                      SortExpression(expression='subject')],
                  limit=1000),
              returned_fields=['author', 'subject', 'summary'],
              snippeted_fields=['content']),
          facet_refinements=[ref_key1, ref_key2]))

    In order to get a Cursor, you specify a Cursor in QueryOptions.cursor
    and extract the Cursor for the next request from results.cursor to
    continue from the last found document, as shown below:

      results = index.search(
          Query(query_string='subject:first good',
                options=QueryOptions(cursor=results.cursor)))

    To enable faceted search in the result, you can use
    enable_facet_discovery or return_facets, as shown below:

    # discover top facets
    results = index.search(
        Query(query_string='movies',
              enable_facet_discovery=true))

    # included specific facets with search result
    results = index.search(
        Query(query_string='movies',
              return_facets=['rating', 'shipping_method']))

    # discover only 5 facets and two manual facets with customized value
    facet_option = FacetOption(discovery_limit=5)
    facet1 = FacetRequest('Rating', ranges=[
        FacetRange(start=1.0, end=2.0),
        FacetRange(start=2.0, end=3.5),
        FacetRange(start=3.5, end=4.0)]
    results = index.search(
        Query(query_string='movies',
              enable_facet_discovery=true,
              facet_option=facet_option,
              return_facets=[facet1, 'shipping_method']))

    Args:
      query_string: The query to match against documents in the index. A query
        is a boolean expression containing terms.  For example, the query
          'job tag:"very important" sent <= 2011-02-28'
        finds documents with the term job in any field, that contain the
        phrase "very important" in a tag field, and a sent date up to and
        including 28th February, 2011.  You can use combinations of
          '(cat OR feline) food NOT dog'
        to find documents which contain the term cat or feline as well as food,
        but do not mention the term dog. A further example,
          'category:televisions brand:sony price >= 300 price < 400'
        will return documents which have televisions in a category field, a
        sony brand and a price field which is 300 (inclusive) to 400
        (exclusive).  See
        https://developers.google.com/appengine/docs/python/search/overview#Expressions
        for a list of expressions that can be used in queries.
      options: A QueryOptions describing post-processing of search results.
      enable_facet_discovery: discovery top relevent facets to this search query
        and return them.
      return_facets: An iterable of FacetRequest or basestring as facet name to
        return specific facet with the result.
      facet_options: A FacetOption describing processing of facets.
      facet_refinements: An iterable of FacetRefinement objects or refinement
        token strings used to filter out search results based on a facet value.
        refinements for different facets will be conjunction and refinements for
        the same facet will be disjunction.
    Raises:
      QueryError: If the query string is not parseable.
    """
    self._query_string = _ConvertToUnicode(query_string)
    _CheckQuery(self._query_string)
    self._options = options
    self._facet_options = facet_options
    self._enable_facet_discovery = enable_facet_discovery
    self._return_facets = _ConvertToListAndCheckType(
        return_facets, (basestring, FacetRequest), 'return_facet')
    for index, facet in enumerate(self._return_facets):
      if isinstance(facet, basestring):
        self._return_facets[index] = FacetRequest(self._return_facets[index])
    self._facet_refinements = _ConvertToListAndCheckType(
        facet_refinements, (basestring, FacetRefinement), 'facet_refinements')
    for index, refinement in enumerate(self._facet_refinements):
      if isinstance(refinement, basestring):
        self._facet_refinements[index] = FacetRefinement.FromTokenString(
            refinement)

  @property
  def query_string(self):
    """Returns the query string to be applied to search service."""
    return self._query_string

  @property
  def options(self):
    """Returns QueryOptions defining post-processing on the search results."""
    return self._options

  @property
  def facet_options(self):
    """Returns FacetOptions defining processing of facets."""
    return self._facet_options

  @property
  def facet_refinements(self):
    """Returns list of facet refinements."""
    return self._facet_refinements

  @property
  def enable_facet_discovery(self):
    """Returns true if facet disocery is on."""
    return self._enable_facet_discovery

  @property
  def return_facets(self):
    """Returns the list of specific facets to be included with the result."""
    return self._return_facets

  def __setstate__(self, state):
    self.__dict__ = {'_enable_facet_discovery': False,
                     '_facet_options': None,
                     '_return_facets': [],
                     '_facet_refinements': []}
    self.__dict__.update(state)


def _CopyQueryToProtocolBuffer(query, params):
  """Copies Query object to params protobuf."""
  params.set_query(query.encode('utf-8'))


def _CopyQueryObjectToProtocolBuffer(query, params):
  """Copy a query object to search_service_pb.SearchParams object."""
  _CopyQueryToProtocolBuffer(query.query_string, params)
  for refinement in query.facet_refinements:
    refinement._CopyToProtocolBuffer(params.add_facet_refinement())
  for return_facet in query.return_facets:
    return_facet._CopyToProtocolBuffer(params.add_include_facet())
  options = query.options
  if query.options is None:
    options = QueryOptions()
  _CopyQueryOptionsObjectToProtocolBuffer(query.query_string, options, params)
  facet_options = query.facet_options
  if facet_options is None:
    facet_options = FacetOptions(
        discovery_limit=10 if query.enable_facet_discovery else None)
  facet_options._CopyToProtocolBuffer(params)


class Index(object):
  """Represents an index allowing indexing, deleting and searching documents.

  The following code fragment shows how to add documents, then search the
  index for documents matching a query.

    # Get the index.
    index = Index(name='index-name')

    # Create a document.
    doc = Document(doc_id='document-id',
                   fields=[TextField(name='subject', value='my first email'),
                           HtmlField(name='body',
                                     value='<html>some content here</html>')])

    # Index the document.
    try:
      index.put(doc)
    except search.Error, e:
      # possibly retry indexing or log error

    # Query the index.
    try:
      results = index.search('subject:first body:here')

      # Iterate through the search results.
      for scored_document in results:
         print scored_document

    except search.Error, e:
      # possibly log the failure

  Once an index is created with a given specification, that specification is
  immutable.

  Search results may contain some out of date documents. However, any two
  changes to any document stored in an index are applied in the correct order.
  """



  RESPONSE_CURSOR, RESULT_CURSOR = ('RESPONSE_CURSOR', 'RESULT_CURSOR')

  _CURSOR_TYPES = frozenset([RESPONSE_CURSOR, RESULT_CURSOR])

  SEARCH, DATASTORE, CLOUD_STORAGE = ('SEARCH', 'DATASTORE', 'CLOUD_STORAGE')

  _SOURCES = frozenset([SEARCH, DATASTORE, CLOUD_STORAGE])

  def __init__(self, name, namespace=None, source=SEARCH):
    """Initializer.

    Args:
      name: The name of the index. An index name must be a visible printable
        ASCII string not starting with '!'. Whitespace characters are excluded.
      namespace: The namespace of the index name. If not set, then the current
        namespace is used.
      source: Deprecated as of 1.7.6. The source of
        the index:
          SEARCH - The Index was created by adding documents throught this
            search API.
          DATASTORE - The Index was created as a side-effect of putting entities
            into Datastore.
          CLOUD_STORAGE - The Index was created as a side-effect of adding
            objects into a Cloud Storage bucket.
    Raises:
      TypeError: If an unknown attribute is passed.
      ValueError: If invalid namespace is given.
    """
    if source not in self._SOURCES:
      raise ValueError('source must be one of %s' % self._SOURCES)
    if source is not self.SEARCH:
      warnings.warn('source is deprecated.', DeprecationWarning, stacklevel=2)
    self._source = source
    self._name = _CheckIndexName(_ConvertToUnicode(name))
    self._namespace = _ConvertToUnicode(namespace)
    if self._namespace is None:
      self._namespace = _ConvertToUnicode(namespace_manager.get_namespace())
    if self._namespace is None:
      self._namespace = u''
    namespace_manager.validate_namespace(self._namespace, exception=ValueError)
    self._schema = None
    self._storage_usage = None
    self._storage_limit = None

  @property
  def schema(self):
    """Returns the schema mapping field names to list of types supported.

    Only valid for Indexes returned by search.get_indexes method."""
    return self._schema

  @property
  def storage_usage(self):
    """The approximate number of bytes used by this index.

    The number may be slightly stale, as it may not reflect the
    results of recent changes.

    Returns None for indexes not obtained from search.get_indexes.

    """
    return self._storage_usage

  @property
  def storage_limit(self):
    """The maximum allowable storage for this index, in bytes.

    Returns None for indexes not obtained from search.get_indexes."""
    return self._storage_limit

  @property
  def name(self):
    """Returns the name of the index."""
    return self._name

  @property
  def namespace(self):
    """Returns the namespace of the name of the index."""
    return self._namespace

  @property
  def source(self):
    """Returns the source of the index.

    Deprecated: from 1.7.6, source is no longer available."""
    warnings.warn('source is deprecated.', DeprecationWarning, stacklevel=2)
    return self._source

  def __eq__(self, other):
    return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

  def __ne__(self, other):
    return not self.__eq__(other)

  def __hash__(self):
    return hash((self._name, self._namespace))

  def __repr__(self):

    return _Repr(self, [('name', self.name), ('namespace', self.namespace),
                        ('source', self._source),
                        ('schema', self.schema),
                        ('storage_usage', self.storage_usage),
                        ('storage_limit', self.storage_limit)])

  def _NewPutResultFromPb(self, status_pb, doc_id):
    """Constructs PutResult from RequestStatus pb and doc_id."""
    message = None
    if status_pb.has_error_detail():
      message = _DecodeUTF8(status_pb.error_detail())
    code = _ERROR_OPERATION_CODE_MAP.get(status_pb.code(),
                                         OperationResult.INTERNAL_ERROR)
    return PutResult(code=code, message=message, id=_DecodeUTF8(doc_id))

  def _NewPutResultList(self, response):
    return [self._NewPutResultFromPb(status, doc_id)
            for status, doc_id in zip(response.status_list(),
                                      response.doc_id_list())]

  @datastore_rpc._positional(2)
  def put(self, documents, deadline=None):
    """Index the collection of documents.

    If any of the documents are already in the index, then reindex them with
    their corresponding fresh document.

    Args:
      documents: A Document or iterable of Documents to index.

    Kwargs:
      deadline: Deadline for RPC call in seconds; if None use the default.

    Returns:
      A list of PutResult, one per Document requested to be indexed.

    Raises:
      PutError: If one or more documents failed to index or
        number indexed did not match requested.
      TypeError: If an unknown attribute is passed.
      ValueError: If documents is not a Document or iterable of Document
        or number of the documents is larger than
        MAXIMUM_DOCUMENTS_PER_PUT_REQUEST or deadline is a negative number.
    """
    return self.put_async(documents, deadline=deadline).get_result()

  @datastore_rpc._positional(2)
  def put_async(self, documents, deadline=None):
    """Asynchronously indexes the collection of documents.

    Identical to put() except that it returns a future. Call
    get_result() on the return value to block on the call and get its result.
    """
    if isinstance(documents, basestring):
      raise TypeError('documents must be a Document or sequence of '
                      'Documents, got %s' % documents.__class__.__name__)
    try:
      docs = list(iter(documents))
    except TypeError:
      docs = [documents]

    if not docs:
      return _WrappedValueFuture([])

    if len(docs) > MAXIMUM_DOCUMENTS_PER_PUT_REQUEST:
      raise ValueError('too many documents to index')

    request = search_service_pb.IndexDocumentRequest()
    response = search_service_pb.IndexDocumentResponse()

    params = request.mutable_params()
    _CopyMetadataToProtocolBuffer(self, params.mutable_index_spec())

    seen_docs = {}
    for document in docs:
      doc_id = document.doc_id
      if doc_id:
        if doc_id in seen_docs:
          if document != seen_docs[doc_id]:
            raise ValueError(
                'Different documents with the same ID found in the '
                'same call to Index.put()')


          continue
        seen_docs[doc_id] = document
      doc_pb = params.add_document()
      _CopyDocumentToProtocolBuffer(document, doc_pb)

    def hook():
      results = self._NewPutResultList(response)

      if response.status_size() != len(params.document_list()):
        raise PutError('did not index requested number of documents', results)

      for status in response.status_list():
        if status.code() != search_service_pb.SearchServiceError.OK:
          raise PutError(
              _ConcatenateErrorMessages(
                  'one or more put document operations failed', status), results)
      return results
    return _RpcOperationFuture(
        'IndexDocument', request, response, deadline, hook)

  def _NewDeleteResultFromPb(self, status_pb, doc_id):
    """Constructs DeleteResult from RequestStatus pb and doc_id."""
    message = None
    if status_pb.has_error_detail():
      message = _DecodeUTF8(status_pb.error_detail())
    code = _ERROR_OPERATION_CODE_MAP.get(status_pb.code(),
                                         OperationResult.INTERNAL_ERROR)

    return DeleteResult(code=code, message=message, id=doc_id)

  def _NewDeleteResultList(self, document_ids, response):
    return [self._NewDeleteResultFromPb(status, doc_id)
            for status, doc_id in zip(response.status_list(), document_ids)]

  @datastore_rpc._positional(2)
  def delete(self, document_ids, deadline=None):
    """Delete the documents with the corresponding document ids from the index.

    If no document exists for the identifier in the list, then that document
    identifier is ignored.

    Args:
      document_ids: A single identifier or list of identifiers of documents
        to delete.

    Kwargs:
      deadline: Deadline for RPC call in seconds; if None use the default.

    Raises:
      DeleteError: If one or more documents failed to remove or
        number removed did not match requested.
      ValueError: If document_ids is not a string or iterable of valid document
        identifiers or number of document ids is larger than
        MAXIMUM_DOCUMENTS_PER_PUT_REQUEST or deadline is a negative number.
    """
    return self.delete_async(document_ids, deadline=deadline).get_result()

  @datastore_rpc._positional(2)
  def delete_async(self, document_ids, deadline=None):
    """Asynchronously deletes the documents with the corresponding document ids.

    Identical to delete() except that it returns a future. Call
    get_result() on the return value to block on the call and get its result.
    """
    doc_ids = _ConvertToList(document_ids)
    if not doc_ids:
      return _WrappedValueFuture([])

    if len(doc_ids) > MAXIMUM_DOCUMENTS_PER_PUT_REQUEST:
      raise ValueError('too many documents to delete')

    request = search_service_pb.DeleteDocumentRequest()
    response = search_service_pb.DeleteDocumentResponse()
    params = request.mutable_params()
    _CopyMetadataToProtocolBuffer(self, params.mutable_index_spec())
    for document_id in doc_ids:
      _CheckDocumentId(document_id)
      params.add_doc_id(document_id)

    def hook():
      results = self._NewDeleteResultList(doc_ids, response)

      if response.status_size() != len(doc_ids):
        raise DeleteError(
            'did not delete requested number of documents', results)

      for status in response.status_list():
        if status.code() != search_service_pb.SearchServiceError.OK:
          raise DeleteError(
              _ConcatenateErrorMessages(
                  'one or more delete document operations failed', status),
              results)
      return results
    return _RpcOperationFuture(
        'DeleteDocument', request, response, deadline, hook)

  def delete_schema(self):
    """Deprecated in 1.7.4. Delete the schema from the index.

    We are deprecating this method and replacing with more general schema
    and index managment.

    A possible use may be remove typed fields which are no longer used. After
    you delete the schema, you need to index one or more documents to rebuild
    the schema. Until you re-index some documents, searches may fail, especially
    searches using field restricts.

    Raises:
      DeleteError: If the schema failed to be deleted.
    """



    warnings.warn('delete_schema is deprecated in 1.7.4.',
                  DeprecationWarning, stacklevel=2)
    request = search_service_pb.DeleteSchemaRequest()
    response = search_service_pb.DeleteSchemaResponse()
    params = request.mutable_params()
    _CopyMetadataToProtocolBuffer(self, params.add_index_spec())

    def hook():

      results = self._NewDeleteResultList([self.name], response)

      if response.status_size() != 1:
        raise DeleteError('did not delete exactly one schema', results)

      status = response.status_list()[0]
      if status.code() != search_service_pb.SearchServiceError.OK:
        raise DeleteError(
            _ConcatenateErrorMessages('delete schema operation failed', status),
            results)
    return _RpcOperationFuture(
        'DeleteSchema', request, response, None, hook).get_result()

  def _NewScoredDocumentFromPb(self, doc_pb, sort_scores, expressions, cursor):
    """Constructs a Document from a document_pb.Document protocol buffer."""
    lang = None
    if doc_pb.has_language():
      lang = _DecodeUTF8(doc_pb.language())
    return ScoredDocument(
        doc_id=_DecodeUTF8(doc_pb.id()),
        fields=_NewFieldsFromPb(doc_pb.field_list()),
        facets=_NewFacetsFromPb(doc_pb.facet_list()),
        language=lang, rank=doc_pb.order_id(), sort_scores=sort_scores,
        expressions=_NewFieldsFromPb(expressions), cursor=cursor)

  def _NewFacetResultFromPb(self, facet_result_pb):
    """Returns a FacetResult populated from search_service FacetResult pb."""
    values = []
    for facet_value_pb in facet_result_pb.value_list():
      refinement_pb = facet_value_pb.refinement()
      if refinement_pb.has_range():
        range_pb = refinement_pb.range()
        facet_range = FacetRange(
            start=(float(range_pb.start()) if range_pb.has_start() else None),
            end=(float(range_pb.end()) if range_pb.has_end() else None))
      else:
        facet_range = None
      refinement = FacetRefinement(
          name=refinement_pb.name(),
          value=refinement_pb.value() if refinement_pb.has_value() else None,
          facet_range=facet_range)
      values.append(FacetResultValue(label=facet_value_pb.name(),
                                     count=facet_value_pb.count(),
                                     refinement=refinement))
    return FacetResult(name=facet_result_pb.name(), values=values)

  def _NewSearchResults(self, response, cursor):
    """Returns a SearchResults populated from a search_service response pb."""
    results = []
    for result_pb in response.result_list():
      per_result_cursor = None
      if result_pb.has_cursor():
        if isinstance(cursor, Cursor):

          per_result_cursor = Cursor(web_safe_string=_ToWebSafeString(
              cursor.per_result, _DecodeUTF8(result_pb.cursor())))
      results.append(
          self._NewScoredDocumentFromPb(
              result_pb.document(), result_pb.score_list(),
              result_pb.expression_list(), per_result_cursor))
    results_cursor = None
    if response.has_cursor():
      if isinstance(cursor, Cursor):

        results_cursor = Cursor(web_safe_string=_ToWebSafeString(
            cursor.per_result, _DecodeUTF8(response.cursor())))
    facets = []
    for facet_result in response.facet_result_list():
      facets.append(self._NewFacetResultFromPb(facet_result))
    return SearchResults(
        results=results, number_found=response.matched_count(),
        cursor=results_cursor, facets=facets)

  @datastore_rpc._positional(2)
  def get(self, doc_id, deadline=None):
    """Retrieve a document by document ID.

    Args:
      doc_id: The ID of the document to retreive.

    Kwargs:
      deadline: Deadline for RPC call in seconds; if None use the default.

    Returns:
      If the document ID exists, returns the associated document. Otherwise,
      returns None.

    Raises:
      TypeError: If any of the parameters have invalid types, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have invalid values (e.g., a
        negative deadline).
    """
    return self.get_async(doc_id, deadline=deadline).get_result()

  @datastore_rpc._positional(2)
  def get_async(self, doc_id, deadline=None):
    """Asynchronously retrieve a document by document ID.

    Identical to get() except that it returns a future. Call
    get_result() on the return value to block on the call and get its result.
    """
    future = self.get_range_async(start_id=doc_id, limit=1, deadline=deadline)
    def hook(response):
      if response.results and response.results[0].doc_id == doc_id:
        return response.results[0]
      return None
    return _SimpleOperationFuture(future, hook)

  @datastore_rpc._positional(2)
  def search(self, query, deadline=None, **kwargs):
    """Search the index for documents matching the query.

    For example, the following code fragment requests a search for
    documents where 'first' occurs in subject and 'good' occurs anywhere,
    returning at most 20 documents, starting the search from 'cursor token',
    returning another single cursor for the response, sorting by subject in
    descending order, returning the author, subject, and summary fields as well
    as a snippeted field content.

      results = index.search(
          query=Query('subject:first good',
              options=QueryOptions(limit=20,
                  cursor=Cursor(),
                  sort_options=SortOptions(
                      expressions=[SortExpression(expression='subject')],
                      limit=1000),
                  returned_fields=['author', 'subject', 'summary'],
                  snippeted_fields=['content'])))

    The following code fragment shows how to use a results cursor

      cursor = results.cursor
      for result in results:
         # process result

      results = index.search(
          Query('subject:first good', options=QueryOptions(cursor=cursor)))

    The following code fragment shows how to use a per_result cursor

      results = index.search(
          query=Query('subject:first good',
              options=QueryOptions(limit=20,
                  cursor=Cursor(per_result=True),
                  ...)))

      cursor = None
      for result in results:
         cursor = result.cursor

      results = index.search(
          Query('subject:first good', options=QueryOptions(cursor=cursor)))

    See http://developers.google.com/appengine/docs/python/search/query_strings
    for more information about query syntax.

    Args:
      query: The Query to match against documents in the index.

    Kwargs:
      deadline: Deadline for RPC call in seconds; if None use the default.

    Returns:
      A SearchResults containing a list of documents matched, number returned
      and number matched by the query.

    Raises:
      TypeError: If any of the parameters have invalid types, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have invalid values (e.g., a
        negative deadline).
    """
    return self.search_async(query, deadline=deadline, **kwargs).get_result()

  @datastore_rpc._positional(2)
  def search_async(self, query, deadline=None, **kwargs):
    """Asynchronously searches the index for documents matching the query.

    Identical to search() except that it returns a future. Call
    get_result() on the return value to block on the call and get its result.
    """
    if isinstance(query, basestring):
      query = Query(query_string=query)
    request = self._NewSearchRequest(query, deadline, **kwargs)
    response = search_service_pb.SearchResponse()
    def hook():
      _CheckStatus(response.status())
      cursor = None
      if query.options:
        cursor = query.options.cursor
      return self._NewSearchResults(response, cursor)
    return _RpcOperationFuture('Search', request, response, deadline, hook)

  def _NewSearchRequest(self, query, deadline, **kwargs):

    app_id = kwargs.pop('app_id', None)
    if kwargs:
      raise TypeError('Invalid arguments: %s' % ', '.join(kwargs))

    request = search_service_pb.SearchRequest()
    if app_id:
      request.set_app_id(app_id)

    params = request.mutable_params()
    if isinstance(query, basestring):
      query = Query(query_string=query)
    _CopyMetadataToProtocolBuffer(self, params.mutable_index_spec())
    _CopyQueryObjectToProtocolBuffer(query, params)
    return request

  def _NewGetResponse(self, response):
    """Returns a GetResponse from the list_documents response pb."""
    documents = []
    for doc_proto in response.document_list():
      documents.append(_NewDocumentFromPb(doc_proto))

    return GetResponse(results=documents)

  @datastore_rpc._positional(5)
  def get_range(self, start_id=None, include_start_object=True,
                limit=100, ids_only=False, deadline=None, **kwargs):
    """Get a range of Documents in the index, in id order.

    Args:
      start_id: String containing the Id from which to list
        Documents from. By default, starts at the first Id.
      include_start_object: If true, include the Document with the
        Id specified by the start_id parameter.
      limit: The maximum number of Documents to return.
      ids_only: If true, the Documents returned only contain their keys.

    Kwargs:
      deadline: Deadline for RPC call in seconds; if None use the default.

    Returns:
      A GetResponse containing a list of Documents, ordered by Id.

    Raises:
      Error: Some subclass of Error is raised if an error occurred processing
        the request.
      TypeError: If any of the parameters have invalid types, or an unknown
        attribute is passed.
      ValueError: If any of the parameters have invalid values (e.g., a
        negative deadline).
    """
    return self.get_range_async(
        start_id, include_start_object, limit, ids_only, deadline=deadline,
        **kwargs).get_result()

  @datastore_rpc._positional(5)
  def get_range_async(self, start_id=None, include_start_object=True,
                      limit=100, ids_only=False, deadline=None, **kwargs):
    """Asynchronously gets a range of Documents in the index, in id order.

    Identical to get_range() except that it returns a future. Call
    get_result() on the return value to block on the call and get its result.
    """

    app_id = kwargs.pop('app_id', None)
    if kwargs:
      raise TypeError('Invalid arguments: %s' % ', '.join(kwargs))
    request = search_service_pb.ListDocumentsRequest()
    if app_id:
      request.set_app_id(app_id)

    params = request.mutable_params()
    _CopyMetadataToProtocolBuffer(self, params.mutable_index_spec())

    if start_id:
      params.set_start_doc_id(start_id)
    params.set_include_start_doc(include_start_object)

    params.set_limit(_CheckInteger(
        limit, 'limit', zero_ok=False,
        upper_bound=MAXIMUM_DOCUMENTS_RETURNED_PER_SEARCH))
    params.set_keys_only(ids_only)

    response = search_service_pb.ListDocumentsResponse()
    def hook():
      _CheckStatus(response.status())
      return self._NewGetResponse(response)
    return _RpcOperationFuture(
        'ListDocuments', request, response, deadline, hook)


_CURSOR_TYPE_PB_MAP = {
  None: search_service_pb.SearchParams.NONE,
  Index.RESPONSE_CURSOR: search_service_pb.SearchParams.SINGLE,
  Index.RESULT_CURSOR: search_service_pb.SearchParams.PER_RESULT
  }



_SOURCES_TO_PB_MAP = {
    Index.SEARCH: search_service_pb.IndexSpec.SEARCH,
    Index.DATASTORE: search_service_pb.IndexSpec.DATASTORE,
    Index.CLOUD_STORAGE: search_service_pb.IndexSpec.CLOUD_STORAGE}



_SOURCE_PB_TO_SOURCES_MAP = {
    search_service_pb.IndexSpec.SEARCH: Index.SEARCH,
    search_service_pb.IndexSpec.DATASTORE: Index.DATASTORE,
    search_service_pb.IndexSpec.CLOUD_STORAGE: Index.CLOUD_STORAGE}


def _CopyMetadataToProtocolBuffer(index, spec_pb):
  """Copies Index specification to a search_service_pb.IndexSpec."""
  spec_pb.set_name(index.name.encode('utf-8'))
  spec_pb.set_namespace(index.namespace.encode('utf-8'))


  if index._source != Index.SEARCH:
    spec_pb.set_source(_SOURCES_TO_PB_MAP.get(index._source))


_FIELD_TYPE_MAP = {
    document_pb.FieldValue.TEXT: Field.TEXT,
    document_pb.FieldValue.HTML: Field.HTML,
    document_pb.FieldValue.ATOM: Field.ATOM,
    document_pb.FieldValue.UNTOKENIZED_PREFIX: Field.UNTOKENIZED_PREFIX,
    document_pb.FieldValue.TOKENIZED_PREFIX: Field.TOKENIZED_PREFIX,
    document_pb.FieldValue.DATE: Field.DATE,
    document_pb.FieldValue.NUMBER: Field.NUMBER,
    document_pb.FieldValue.GEO: Field.GEO_POINT,
    }


def _NewSchemaFromPb(field_type_pb_list):
  """Creates map of field name to type list from document_pb.FieldTypes list."""
  field_types = {}
  for field_type_pb in field_type_pb_list:
    for field_type in field_type_pb.type_list():
      public_type = _FIELD_TYPE_MAP[field_type]
      name = _DecodeUTF8(field_type_pb.name())
      if name in field_types:
        field_types[name].append(public_type)
      else:
        field_types[name] = [public_type]
  return field_types


def _NewIndexFromIndexSpecPb(index_spec_pb):
  """Creates an Index from a search_service_pb.IndexSpec."""
  source = _SOURCE_PB_TO_SOURCES_MAP.get(index_spec_pb.source())
  index = None
  if index_spec_pb.has_namespace():
    index = Index(name=index_spec_pb.name(),
                  namespace=index_spec_pb.namespace(),
                  source=source)
  else:
    index = Index(name=index_spec_pb.name(), source=source)
  return index


def _NewIndexFromPb(index_metadata_pb, include_schema):
  """Creates an Index from a search_service_pb.IndexMetadata."""
  index = _NewIndexFromIndexSpecPb(index_metadata_pb.index_spec())
  if include_schema:
    index._schema = _NewSchemaFromPb(index_metadata_pb.field_list())
  if index_metadata_pb.has_storage():
    index._storage_usage = index_metadata_pb.storage().amount_used()
    index._storage_limit = index_metadata_pb.storage().limit()
  return index


def _MakeSyncSearchServiceCall(call, request, response, deadline):
  """Deprecated: Make a synchronous call to search service.

  If the deadline is not None, waits only until the deadline expires.

  Args:
    call: Method name to call, as a string
    request: The request object
    response: The response object

  Kwargs:
    deadline: Deadline for RPC call in seconds; if None use the default.

  Raises:
    TypeError: if the deadline is not a number and is not None.
    ValueError: If the deadline is less than zero.
  """
  _ValidateDeadline(deadline)
  logging.warning("_MakeSyncSearchServiceCall is deprecated; please use API.")
  try:
    if deadline is None:
      apiproxy_stub_map.MakeSyncCall('search', call, request, response)
    else:


      rpc = apiproxy_stub_map.UserRPC('search', deadline=deadline)
      rpc.make_call(call, request, response)
      rpc.wait()
      rpc.check_success()
  except apiproxy_errors.ApplicationError, e:
    raise _ToSearchError(e)

def _ValidateDeadline(deadline):
  if deadline is None:
    return
  if (not isinstance(deadline, (int, long, float))
      or isinstance(deadline, (bool,))):
    raise TypeError('deadline argument should be int/long/float (%r)'
                    % (deadline,))
  if deadline <= 0:
    raise ValueError('deadline argument must be > 0 (%s)' % (deadline,))
