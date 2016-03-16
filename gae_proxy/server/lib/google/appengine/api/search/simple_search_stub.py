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




"""Simple RAM backed Search API stub."""











import base64
import bisect
import copy
import cPickle as pickle
import datetime
import functools
import hashlib
import logging
import math
import os
import random
import string
import tempfile
import threading
import urllib
import uuid

from google.appengine.datastore import document_pb
from google.appengine.api import apiproxy_stub
from google.appengine.api.namespace_manager import namespace_manager
from google.appengine.api.search import query_parser
from google.appengine.api.search import QueryParser
from google.appengine.api.search import search
from google.appengine.api.search import search_service_pb
from google.appengine.api.search import search_util
from google.appengine.api.search.stub import document_matcher
from google.appengine.api.search.stub import expression_evaluator
from google.appengine.api.search.stub import simple_facet
from google.appengine.api.search.stub import simple_tokenizer
from google.appengine.api.search.stub import tokens
from google.appengine.runtime import apiproxy_errors

__all__ = ['IndexConsistencyError',
           'Posting',
           'PostingList',
           'RamInvertedIndex',
           'SearchServiceStub',
           'SimpleIndex',
           'FieldTypesDict',
          ]

_VISIBLE_PRINTABLE_ASCII = frozenset(
    set(string.printable) - set(string.whitespace))

_FAILED_TO_PARSE_SEARCH_REQUEST = 'Failed to parse search request \"%s\"; %s'

class _InvalidCursorException(Exception):
  """Raised when parsing a cursor fails."""

class IndexConsistencyError(Exception):
  """Deprecated 1.7.7. Accessed index with same name different consistency."""


class Posting(object):
  """Represents a occurrences of some token at positions in a document."""

  def __init__(self, doc_id):
    """Initializer.

    Args:
      doc_id: The identifier of the document with token occurrences.

    Raises:
      TypeError: If an unknown argument is passed.
    """
    self._doc_id = doc_id
    self._positions = []

  @property
  def doc_id(self):
    """Return id of the document that the token occurred in."""
    return self._doc_id

  def AddPosition(self, position):
    """Adds the position in token sequence to occurrences for token."""
    pos = bisect.bisect_left(self._positions, position)
    if pos < len(self._positions) and self._positions[pos] == position:
      return
    self._positions.insert(pos, position)

  def RemovePosition(self, position):
    """Removes the position in token sequence from occurrences for token."""
    pos = bisect.bisect_left(self._positions, position)
    if pos < len(self._positions) and self._positions[pos] == position:
      del self._positions[pos]

  def __cmp__(self, other):
    if not isinstance(other, Posting):
      return -2
    return cmp(self.doc_id, other.doc_id)

  @property
  def positions(self):
    return self._positions

  def __repr__(self):
    return search_util.Repr(
        self, [('doc_id', self.doc_id), ('positions', self.positions)])


class PostingList(object):
  """Represents ordered positions of some token in document.

  A PostingList consists of a document id and a sequence of positions
  that the same token occurs in the document.
  """

  def __init__(self):
    self._postings = []

  def Add(self, doc_id, position):
    """Adds the token position for the given doc_id."""
    posting = Posting(doc_id=doc_id)
    pos = bisect.bisect_left(self._postings, posting)
    if pos < len(self._postings) and self._postings[
        pos].doc_id == posting.doc_id:
      posting = self._postings[pos]
    else:
      self._postings.insert(pos, posting)
    posting.AddPosition(position)

  def Remove(self, doc_id, position):
    """Removes the token position for the given doc_id."""
    posting = Posting(doc_id=doc_id)
    pos = bisect.bisect_left(self._postings, posting)
    if pos < len(self._postings) and self._postings[
        pos].doc_id == posting.doc_id:
      posting = self._postings[pos]
      posting.RemovePosition(position)
      if not posting.positions:
        del self._postings[pos]

  @property
  def postings(self):
    return self._postings

  def __iter__(self):
    return iter(self._postings)

  def __repr__(self):
    return search_util.Repr(self, [('postings', self.postings)])


class _ScoredDocument(object):
  """A scored document_pb.Document."""

  def __init__(self, document, score):
    self._document = document
    self._score = score
    self._expressions = {}

  @property
  def document(self):
    return self._document

  @property
  def score(self):
    return self._score

  @property
  def expressions(self):
    return self._expressions

  def __repr__(self):
    return search_util.Repr(
        self, [('document', self.document), ('score', self.score)])


class _DocumentStatistics(object):
  """Statistics about terms occuring in a document."""

  def __init__(self):
    self._term_stats = {}

  def __iter__(self):
    for item in self._term_stats.items():
      yield item

  def IncrementTermCount(self, term):
    """Adds an occurrence of the term to the stats for the document."""
    count = 0
    if term in self._term_stats:
      count = self._term_stats[term]
    count += 1
    self._term_stats[term] = count

  def TermFrequency(self, term):
    """Returns the term frequency in the document."""
    if term not in self._term_stats:
      return 0
    return self._term_stats[term]

  @property
  def term_stats(self):
    """Returns the collection of term frequencies in the document."""
    return self._term_stats

  def __eq__(self, other):
    return self.term_stats == other.term_stats

  def __hash__(self):
    return hash(self.term_stats)

  def __repr__(self):
    return search_util.Repr(self, [('term_stats', self.term_stats)])


class FieldTypesDict(object):
  """Dictionary-like object for type mappings."""

  def __init__(self):
    self._field_types = []

  def __contains__(self, name):
    return name in [ f.name() for f in self._field_types ]

  def __getitem__(self, name):
    for f in self._field_types:
      if name == f.name():
        return f
    raise KeyError, name

  def IsType(self, name, field_type):
    if name not in self:
      return False
    schema_type = self[name]
    return field_type in schema_type.type_list()

  def AddFieldType(self, name, field_type):
    field_types = None
    for f in self._field_types:
      if name == f.name():
        field_types = f
    if field_types is None:
      field_types = document_pb.FieldTypes()
      field_types.set_name(name)
      self._field_types.append(field_types)
    if field_type not in field_types.type_list():
      field_types.add_type(field_type)

  def __iter__(self):
    return iter(sorted([f.name() for f in self._field_types]))

  def __repr__(self):
    return repr(self._field_types)

class RamInvertedIndex(object):
  """A simple RAM-resident inverted file over documents."""

  def __init__(self, tokenizer):
    self._tokenizer = tokenizer
    self._inverted_index = {}
    self._schema = FieldTypesDict()
    self._document_ids = set([])

  def _AddDocumentId(self, doc_id):
    """Adds the doc_id to set in index."""
    self._document_ids.add(doc_id)

  def _RemoveDocumentId(self, doc_id):
    """Removes the doc_id from the set in index."""
    if doc_id in self._document_ids:
      self._document_ids.remove(doc_id)

  @property
  def document_count(self):
    return len(self._document_ids)

  def _AddFieldType(self, name, field_type):
    """Adds the type to the list supported for a named field."""
    self._schema.AddFieldType(name, field_type)

  def GetDocumentStats(self, document):
    """Gets statistics about occurrences of terms in document."""
    document_stats = _DocumentStatistics()
    for field in document.field_list():
      for token in self._tokenizer.TokenizeValue(field_value=field.value()):
        document_stats.IncrementTermCount(token.chars)
    return document_stats

  def AddDocument(self, doc_id, document):
    """Adds a document into the index."""
    token_position = 0
    for field in document.field_list():
      self._AddFieldType(field.name(), field.value().type())
      self._AddTokens(doc_id, field.name(), field.value(), token_position)
    self._AddDocumentId(doc_id)

  def RemoveDocument(self, document):
    """Removes a document from the index."""
    doc_id = document.id()
    for field in document.field_list():
      self._RemoveTokens(doc_id, field.name(), field.value())
    self._RemoveDocumentId(doc_id)

  def _AddTokens(self, doc_id, field_name, field_value, token_position):
    """Adds token occurrences for a given doc's field value."""
    for token in self._tokenizer.TokenizeValue(field_value, token_position):
      self._AddToken(doc_id, token)
      self._AddToken(doc_id, token.RestrictField(field_name))

  def _RemoveTokens(self, doc_id, field_name, field_value):
    """Removes tokens occurrences for a given doc's field value."""
    for token in self._tokenizer.TokenizeValue(field_value=field_value):
      self._RemoveToken(doc_id, token)
      self._RemoveToken(doc_id, token.RestrictField(field_name))

  def _AddToken(self, doc_id, token):
    """Adds a token occurrence for a document."""
    postings = self._inverted_index.get(token)
    if postings is None:
      self._inverted_index[token] = postings = PostingList()
    postings.Add(doc_id, token.position)

  def _RemoveToken(self, doc_id, token):
    """Removes a token occurrence for a document."""
    if token in self._inverted_index:
      postings = self._inverted_index[token]
      postings.Remove(doc_id, token.position)
      if not postings.postings:
        del self._inverted_index[token]

  def GetPostingsForToken(self, token):
    """Returns all document postings which for the token."""
    if token in self._inverted_index:
      return self._inverted_index[token].postings
    return []

  def GetSchema(self):
    """Returns the schema for the index."""
    return self._schema

  def DeleteSchema(self):
    """Deletes the schema for the index."""
    self._schema = FieldTypesDict()

  def __repr__(self):
    return search_util.Repr(self, [('_inverted_index', self._inverted_index),
                                   ('_schema', self._schema),
                                   ('document_count', self.document_count)])


def _ScoreRequested(params):
  """Returns True if match scoring requested, False otherwise."""
  return params.has_scorer_spec() and params.scorer_spec().has_scorer()


class SimpleIndex(object):
  """A simple search service which uses a RAM-resident inverted file."""

  def __init__(self, index_spec):
    self._index_spec = index_spec
    self._documents = {}
    self._parser = simple_tokenizer.SimpleTokenizer(split_restricts=False)
    self._inverted_index = RamInvertedIndex(simple_tokenizer.SimpleTokenizer())

  @property
  def index_spec(self):
    """Returns the index specification for the index."""
    return self._index_spec

  def IndexDocuments(self, documents, response):
    """Indexes an iterable DocumentPb.Document."""
    for document in documents:
      doc_id = document.id()
      if not doc_id:
        doc_id = str(uuid.uuid4())
        document.set_id(doc_id)







      try:
        search._NewDocumentFromPb(document)
      except ValueError, e:
        new_status = response.add_status()
        new_status.set_code(search_service_pb.SearchServiceError.INVALID_REQUEST)
        new_status.set_error_detail(e.message)
        continue
      response.add_doc_id(doc_id)
      if doc_id in self._documents:
        old_document = self._documents[doc_id]
        self._inverted_index.RemoveDocument(old_document)
      self._documents[doc_id] = document
      new_status = response.add_status()
      new_status.set_code(search_service_pb.SearchServiceError.OK)
      self._inverted_index.AddDocument(doc_id, document)

  def DeleteDocuments(self, document_ids, response):
    """Deletes documents for the given document_ids."""
    for document_id in document_ids:
      self.DeleteDocument(document_id, response.add_status())

  def DeleteDocument(self, document_id, delete_status):
    """Deletes the document, if any, with the given document_id."""
    if document_id in self._documents:
      document = self._documents[document_id]
      self._inverted_index.RemoveDocument(document)
      del self._documents[document_id]
      delete_status.set_code(search_service_pb.SearchServiceError.OK)
    else:
      delete_status.set_code(search_service_pb.SearchServiceError.OK)
      delete_status.set_error_detail('Not found')

  def Documents(self):
    """Returns the documents in the index."""
    return self._documents.values()

  def _TermFrequency(self, term, document):
    """Return the term frequency in the document."""
    return self._inverted_index.GetDocumentStats(document).TermFrequency(term)

  @property
  def document_count(self):
    """Returns the count of documents in the index."""
    return self._inverted_index.document_count

  def _DocumentCountForTerm(self, term):
    """Returns the document count for documents containing the term."""
    return len(self._PostingsForToken(tokens.Token(chars=term)))

  def _InverseDocumentFrequency(self, term):
    """Returns inverse document frequency of term."""
    doc_count = self._DocumentCountForTerm(term)
    if doc_count:
      return math.log10(self.document_count / float(doc_count))
    else:
      return 0

  def _TermFrequencyInverseDocumentFrequency(self, term, document):
    """Returns the term frequency times inverse document frequency of term."""
    return (self._TermFrequency(term, document) *
            self._InverseDocumentFrequency(term))

  def _ScoreDocument(self, document, score, terms):
    """Scores a document for the given query."""
    if not score:
      return 0
    tf_idf = 0
    for term in terms:
      tf_idf += self._TermFrequencyInverseDocumentFrequency(term, document)
    return tf_idf

  def _PostingsForToken(self, token):
    """Returns the postings for the token."""
    return self._inverted_index.GetPostingsForToken(token)

  def _CollectTerms(self, node):
    """Get all search terms for scoring."""
    if node.getType() in search_util.TEXT_QUERY_TYPES:
      return set([query_parser.GetQueryNodeText(node).strip('"')])
    elif node.children:
      if node.getType() == QueryParser.EQ and len(node.children) > 1:
        children = node.children[1:]
      else:
        children = node.children

      result = set()
      for term_set in (self._CollectTerms(child) for child in children):
        result.update(term_set)
      return result
    return set()

  def _CollectFields(self, node):
    if node.getType() == QueryParser.EQ and node.children:
      return set([query_parser.GetQueryNodeText(node.children[0])])
    elif node.children:
      result = set()
      for term_set in (self._CollectFields(child) for child in node.children):
        result.update(term_set)
      return result
    return set()

  def _Evaluate(self, node, score=True):
    """Retrieve scored results for a search query."""
    doc_match = document_matcher.DocumentMatcher(node, self._inverted_index)

    matched_documents = doc_match.FilterDocuments(self._documents.itervalues())
    terms = self._CollectTerms(node)
    scored_documents = [
        _ScoredDocument(doc, self._ScoreDocument(doc, score, terms))
        for doc in matched_documents]
    return scored_documents

  def _Sort(self, docs, search_params, query, score):
    """Return sorted docs with score or evaluated search_params as sort key."""



    docs = sorted(docs, key=lambda doc: doc.document.order_id(), reverse=True)

    if not search_params.sort_spec_size():
      if score:
        return sorted(docs, key=lambda doc: doc.score, reverse=True)
      return docs

    def SortKey(scored_doc):
      """Return the sort key for a document based on the request parameters.

      Arguments:
        scored_doc: The document to score

      Returns:
        The sort key of a document. The sort key is a tuple, where the nth
        element in the tuple corresponds to the value of the nth sort expression
        evaluated on the document.

      Raises:
        Exception: if no default value is specified.
      """
      expr_vals = []
      for sort_spec in search_params.sort_spec_list():
        default_text = None
        default_numeric = None
        if sort_spec.has_default_value_text():
          default_text = sort_spec.default_value_text()
        if sort_spec.has_default_value_numeric():
          default_numeric = sort_spec.default_value_numeric()
        try:
          text_val = expression_evaluator.ExpressionEvaluator(
              scored_doc, self._inverted_index, True).ValueOf(
                  sort_spec.sort_expression(), default_value=default_text,
                  return_type=search_util.EXPRESSION_RETURN_TYPE_TEXT)
          num_val = expression_evaluator.ExpressionEvaluator(
              scored_doc, self._inverted_index, True).ValueOf(
                  sort_spec.sort_expression(), default_value=default_numeric,
                  return_type=search_util.EXPRESSION_RETURN_TYPE_NUMERIC)
        except expression_evaluator.QueryExpressionEvaluationError, e:
          raise expression_evaluator.ExpressionEvaluationError(
              _FAILED_TO_PARSE_SEARCH_REQUEST % (query, e))
        if isinstance(num_val, datetime.datetime):
          num_val = search_util.EpochTime(num_val)


        elif isinstance(text_val, datetime.datetime):
          num_val = search_util.EpochTime(text_val)

        if text_val is None:
          text_val = ''
        if num_val is None:
          num_val = 0
        expr_vals.append([text_val, num_val])
      return tuple(expr_vals)

    def SortCmp(x, y):
      """The comparison function for sort keys."""


      for i, val_tuple in enumerate(zip(x, y)):
        cmp_val = cmp(*val_tuple)
        if cmp_val:
          if search_params.sort_spec(i).sort_descending():
            return -cmp_val
          return cmp_val
      return 0
    return sorted(docs, key=SortKey, cmp=SortCmp)

  def _AttachExpressions(self, docs, search_params):
    if search_params.has_field_spec():
      for doc in docs:
        evaluator = expression_evaluator.ExpressionEvaluator(
            doc, self._inverted_index)
        for expr in search_params.field_spec().expression_list():
          evaluator.Evaluate(expr)
    return docs

  def Search(self, search_request):
    """Searches the simple index for ."""
    query = urllib.unquote(search_request.query())
    query = query.strip()
    score = _ScoreRequested(search_request)
    if not query:
      docs = [_ScoredDocument(doc, 0.0) for doc in self._documents.values()]
    else:
      if not isinstance(query, unicode):
        query = unicode(query, 'utf-8')
      query_tree = query_parser.ParseAndSimplify(query)
      docs = self._Evaluate(query_tree, score=score)
    docs = self._Sort(docs, search_request, query, score)
    docs = self._AttachExpressions(docs, search_request)
    return docs

  def GetSchema(self):
    """Returns the schema for the index."""
    return self._inverted_index.GetSchema()

  def DeleteSchema(self):
    """Deletes the schema for the index."""
    self._inverted_index.DeleteSchema()

  def __repr__(self):
    return search_util.Repr(self, [('_index_spec', self._index_spec),
                                   ('_documents', self._documents),
                                   ('_inverted_index', self._inverted_index)])


class SearchServiceStub(apiproxy_stub.APIProxyStub):
  """Simple RAM backed Search service stub.

  This stub provides the search_service_pb.SearchService.  But this is
  NOT a subclass of SearchService itself.  Services are provided by
  the methods prefixed by "_Dynamic_".
  """




  _VERSION = 1





  _MAX_STORAGE_LIMIT = 1024 * 1024 * 1024

  def __init__(self, service_name='search', index_file=None):
    """Constructor.

    Args:
      service_name: Service name expected for all calls.
      index_file: The file to which search indexes will be persisted.
    """
    self.__indexes = {}
    self.__index_file = index_file
    self.__index_file_lock = threading.Lock()
    super(SearchServiceStub, self).__init__(service_name)

    self.Read()

  def _InvalidRequest(self, status, exception):
    status.set_code(search_service_pb.SearchServiceError.INVALID_REQUEST)
    status.set_error_detail(exception.message)

  def _UnknownIndex(self, status, index_spec):
    status.set_code(search_service_pb.SearchServiceError.OK)
    status.set_error_detail(
        "Index '%s' in namespace '%s' does not exist" %
        (index_spec.name(), index_spec.namespace()))

  def _GetNamespace(self, namespace):
    """Get namespace name.

    Args:
      namespace: Namespace provided in request arguments.

    Returns:
      If namespace is None, returns the name of the current global namespace. If
      namespace is not None, returns namespace.
    """
    if namespace is not None:
      return namespace
    return namespace_manager.get_namespace()

  def _GetIndex(self, index_spec, create=False):
    namespace = self._GetNamespace(index_spec.namespace())

    index = self.__indexes.setdefault(namespace, {}).get(index_spec.name())
    if index is None and create:
      index = SimpleIndex(index_spec)
      self.__indexes[namespace][index_spec.name()] = index
    return index

  def _Dynamic_IndexDocument(self, request, response):
    """A local implementation of SearchService.IndexDocument RPC.

    Index a new document or update an existing document.

    Args:
      request: A search_service_pb.IndexDocumentRequest.
      response: An search_service_pb.IndexDocumentResponse.
    """
    params = request.params()
    index = self._GetIndex(params.index_spec(), create=True)
    index.IndexDocuments(params.document_list(), response)

  def _Dynamic_DeleteDocument(self, request, response):
    """A local implementation of SearchService.DeleteDocument RPC.

    Args:
      request: A search_service_pb.DeleteDocumentRequest.
      response: An search_service_pb.DeleteDocumentResponse.
    """
    params = request.params()
    index_spec = params.index_spec()
    index = self._GetIndex(index_spec)
    for document_id in params.doc_id_list():
      delete_status = response.add_status()
      if index is None:
        delete_status.set_code(search_service_pb.SearchServiceError.OK)
        delete_status.set_error_detail('Not found')
      else:
        index.DeleteDocument(document_id, delete_status)

  def _Dynamic_ListIndexes(self, request, response):
    """A local implementation of SearchService.ListIndexes RPC.

    Args:
      request: A search_service_pb.ListIndexesRequest.
      response: An search_service_pb.ListIndexesResponse.

    Raises:
      ResponseTooLargeError: raised for testing admin console.
    """



    if request.has_app_id():
      if random.choice([True] + [False] * 9):
        raise apiproxy_errors.ResponseTooLargeError()

      for _ in xrange(random.randint(0, 2) * random.randint(5, 15)):
        new_index_spec = response.add_index_metadata().mutable_index_spec()
        new_index_spec.set_name(
            random.choice(list(_VISIBLE_PRINTABLE_ASCII - set('!'))) +
            ''.join(random.choice(list(_VISIBLE_PRINTABLE_ASCII))
                    for _ in xrange(random.randint(
                        0, search.MAXIMUM_INDEX_NAME_LENGTH))))
      response.mutable_status().set_code(
          random.choice([search_service_pb.SearchServiceError.OK] * 10 +
                        [search_service_pb.SearchServiceError.TRANSIENT_ERROR] +
                        [search_service_pb.SearchServiceError.INTERNAL_ERROR]))
      return

    response.mutable_status().set_code(
        search_service_pb.SearchServiceError.OK)

    namespace = self._GetNamespace(request.params().namespace())
    if namespace not in self.__indexes or not self.__indexes[namespace]:
      return

    keys, indexes = zip(*sorted(
        self.__indexes[namespace].iteritems(), key=lambda v: v[0]))
    position = 0
    params = request.params()
    if params.has_start_index_name():
      position = bisect.bisect_left(keys, params.start_index_name())
      if (not params.include_start_index() and position < len(keys)
          and keys[position] == params.start_index_name()):
        position += 1
    elif params.has_index_name_prefix():
      position = bisect.bisect_left(keys, params.index_name_prefix())
    if params.has_offset():
      position += params.offset()
    end_position = position + params.limit()
    prefix = params.index_name_prefix()
    for index in indexes[min(position, len(keys)):min(end_position, len(keys))]:
      index_spec = index.index_spec
      if prefix and not index_spec.name().startswith(prefix):
        break
      metadata = response.add_index_metadata()
      new_index_spec = metadata.mutable_index_spec()
      new_index_spec.set_name(index_spec.name())
      new_index_spec.set_namespace(index_spec.namespace())
      if params.fetch_schema():
        self._AddSchemaInformation(index, metadata)
      self._AddStorageInformation(index, metadata)

  def _Dynamic_DeleteSchema(self, request, response):
    """A local implementation of SearchService.DeleteSchema RPC.

    Args:
      request: A search_service_pb.DeleteSchemaRequest.
      response: An search_service_pb.DeleteSchemaResponse.
    """

    params = request.params()
    for index_spec in params.index_spec_list():
      index = self._GetIndex(index_spec)
      if index is not None:
        index.DeleteSchema()
      response.add_status().set_code(search_service_pb.SearchServiceError.OK)

  def _AddSchemaInformation(self, index, metadata_pb):
    schema = index.GetSchema()
    for name in schema:
      field_types = schema[name]
      new_field_types = metadata_pb.add_field()
      new_field_types.MergeFrom(field_types)

  def _AddStorageInformation(self, index, metadata_pb):
    total_usage = 0
    for document in index.Documents():



      for field in document.field_list():
        total_usage += field.ByteSize()
      total_usage += len(document.id())
    storage = metadata_pb.mutable_storage()
    storage.set_amount_used(total_usage)
    storage.set_limit(self._MAX_STORAGE_LIMIT)

  def _AddDocument(self, response, document, ids_only):
    doc = response.add_document()
    if ids_only:
      doc.set_id(document.id())
    else:
      doc.MergeFrom(document)

  def _Dynamic_ListDocuments(self, request, response):
    """A local implementation of SearchService.ListDocuments RPC.

    Args:
      request: A search_service_pb.ListDocumentsRequest.
      response: An search_service_pb.ListDocumentsResponse.
    """
    params = request.params()
    index = self._GetIndex(params.index_spec())
    if index is None:
      response.mutable_status().set_code(
          search_service_pb.SearchServiceError.OK)
      return

    num_docs = 0
    start = not params.has_start_doc_id()
    for document in sorted(index.Documents(), key=lambda doc: doc.id()):
      if start:
        if num_docs < params.limit():
          self._AddDocument(response, document, params.keys_only())
          num_docs += 1
      else:
        if document.id() >= params.start_doc_id():
          start = True
          if (document.id() != params.start_doc_id() or
              params.include_start_doc()):
            self._AddDocument(response, document, params.keys_only())
            num_docs += 1

    response.mutable_status().set_code(
        search_service_pb.SearchServiceError.OK)

  def _RandomSearchResponse(self, request, response):

    random.seed()
    if random.random() < 0.03:
      raise apiproxy_errors.ResponseTooLargeError()
    response.mutable_status().set_code(
        random.choice([search_service_pb.SearchServiceError.OK] * 30 +
                      [search_service_pb.SearchServiceError.TRANSIENT_ERROR] +
                      [search_service_pb.SearchServiceError.INTERNAL_ERROR]))

    params = request.params()
    random.seed(params.query())
    total = random.randint(0, 100)


    if random.random() < 0.3:
      total = 0

    offset = 0
    if params.has_offset():
      offset = params.offset()

    remaining = max(0, total - offset)
    nresults = min(remaining, params.limit())
    matched_count = offset + nresults
    if remaining > nresults:
      matched_count += random.randint(1, 100)

    def RandomText(charset, min_len, max_len):
      return ''.join(random.choice(charset)
                     for _ in xrange(random.randint(min_len, max_len)))

    for i in xrange(nresults):
      seed = '%s:%s' % (params.query(), i + offset)
      random.seed(seed)
      result = response.add_result()
      doc = result.mutable_document()
      doc_id = RandomText(string.letters + string.digits, 8, 10)
      doc.set_id(doc_id)
      random.seed(doc_id)
      for _ in params.sort_spec_list():
        result.add_score(random.random())

      for name, probability in [('creator', 0.90), ('last_change', 0.40)]:
        if random.random() < probability:
          field = doc.add_field()
          field.set_name(name)
          value = field.mutable_value()
          value.set_type(document_pb.FieldValue.TEXT)
          value.set_string_value(
              RandomText(string.letters + string.digits, 2, 10)
              + '@google.com')

      field = doc.add_field()
      field.set_name('content')
      value = field.mutable_value()
      value.set_type(document_pb.FieldValue.TEXT)
      value.set_string_value(
          RandomText(string.printable, 0, 15) + params.query() +
          RandomText(string.printable + 10 * string.whitespace, 5, 5000))

      for i in xrange(random.randint(0, 2)):
        field = doc.add_field()
        field.set_name(RandomText(string.letters, 3, 7))
        value = field.mutable_value()
        value.set_type(document_pb.FieldValue.TEXT)
        value.set_string_value(RandomText(string.printable, 0, 100))

    response.set_matched_count(matched_count)

  def _DefaultFillSearchResponse(self, params, results, response):
    """Fills the SearchResponse with the first set of results."""
    position_range = range(0, min(params.limit(), len(results)))
    self._FillSearchResponse(results, position_range, params.cursor_type(),
                             _ScoreRequested(params), response)

  def _CopyDocument(self, doc, doc_copy, field_names, ids_only=None):
    """Copies Document, doc, to doc_copy restricting fields to field_names."""
    doc_copy.set_id(doc.id())
    if ids_only:
      return
    if doc.has_language():
      doc_copy.set_language(doc.language())
    for field in doc.field_list():
      if not field_names or field.name() in field_names:
        doc_copy.add_field().CopyFrom(field)
    doc_copy.set_order_id(doc.order_id())

  def _FillSearchResponse(self, results, position_range, cursor_type, score,
                          response, field_names=None, ids_only=None):
    """Fills the SearchResponse with a selection of results."""
    for i in position_range:
      result = results[i]
      search_result = response.add_result()
      self._CopyDocument(result.document, search_result.mutable_document(),
                         field_names, ids_only)
      if cursor_type == search_service_pb.SearchParams.PER_RESULT:
        search_result.set_cursor(self._EncodeCursor(result.document))
      if score:
        search_result.add_score(result.score)
      for field, expression in result.expressions.iteritems():
        expr = search_result.add_expression()
        expr.set_name(field)
        if (isinstance(expression, float) or
            isinstance(expression, long) or
            isinstance(expression, int)):
          expr.mutable_value().set_string_value(repr(float(expression)))
          expr.mutable_value().set_type(document_pb.FieldValue.NUMBER)
        else:
          expr.mutable_value().set_string_value(expression)
          expr.mutable_value().set_type(document_pb.FieldValue.HTML)

  def _Dynamic_Search(self, request, response):
    """A local implementation of SearchService.Search RPC.

    Args:
      request: A search_service_pb.SearchRequest.
      response: An search_service_pb.SearchResponse.
    """
    if request.has_app_id():
      self._RandomSearchResponse(request, response)
      return

    index = self._GetIndex(request.params().index_spec())
    if index is None:
      self._UnknownIndex(response.mutable_status(),
                         request.params().index_spec())
      response.set_matched_count(0)
      return

    params = request.params()
    try:
      results = index.Search(params)
    except query_parser.QueryException, e:
      self._InvalidRequest(response.mutable_status(), e)
      response.set_matched_count(0)
      return
    except expression_evaluator.ExpressionEvaluationError, e:
      self._InvalidRequest(response.mutable_status(), e)
      response.set_matched_count(0)
      return
    except document_matcher.ExpressionTreeException, e:
      self._InvalidRequest(response.mutable_status(), e)
      response.set_matched_count(0)
      return

    facet_analyzer = simple_facet.SimpleFacet(params)
    results = facet_analyzer.RefineResults(results)
    response.set_matched_count(len(results))
    offset = 0
    if params.has_cursor():
      try:
        doc_id = self._DecodeCursor(params.cursor())
      except _InvalidCursorException, e:
        self._InvalidRequest(response.mutable_status(), e)
        response.set_matched_count(0)
        return
      for i, result in enumerate(results):
        if result.document.id() == doc_id:
          offset = i + 1
          break
    elif params.has_offset():
      offset = params.offset()



    if offset < len(results):


      limit = offset + params.limit()
      if limit >= len(results):


        range_end = len(results)
      else:



        range_end = limit
        if params.cursor_type() == search_service_pb.SearchParams.SINGLE:
          document = results[range_end - 1].document
          response.set_cursor(self._EncodeCursor(document))
      result_range = range(offset, range_end)
    else:
      result_range = range(0)
    field_names = params.field_spec().name_list()
    self._FillSearchResponse(results, result_range, params.cursor_type(),
                             _ScoreRequested(params), response, field_names,
                             params.keys_only())
    facet_analyzer.FillFacetResponse(results, response)

    response.mutable_status().set_code(search_service_pb.SearchServiceError.OK)

  def _EncodeCursor(self, document):
    doc_id_hash = hashlib.sha224(document.id()).hexdigest()
    cursor = doc_id_hash + '|' + document.id()
    return base64.urlsafe_b64encode(cursor)

  def _DecodeCursor(self, encoded_cursor):
    cursor = base64.urlsafe_b64decode(encoded_cursor)
    separator = cursor.find('|')
    if separator < 0:
      raise _InvalidCursorException('Invalid cursor string: ' + encoded_cursor)
    doc_id_hash = cursor[:separator]
    doc_id = cursor[separator+1:]
    if hashlib.sha224(doc_id).hexdigest() == doc_id_hash:
      return doc_id
    raise _InvalidCursorException('Invalid cursor string: ' + encoded_cursor)

  def __repr__(self):
    return search_util.Repr(self, [('__indexes', self.__indexes)])

  def Write(self):
    """Write search indexes to the index file.

    This method is a no-op if index_file is set to None.
    """
    if not self.__index_file:
      return





    descriptor, tmp_filename = tempfile.mkstemp(
        dir=os.path.dirname(self.__index_file))
    tmpfile = os.fdopen(descriptor, 'wb')

    pickler = pickle.Pickler(tmpfile, protocol=1)
    pickler.fast = True
    pickler.dump((self._VERSION, self.__indexes))

    tmpfile.close()

    self.__index_file_lock.acquire()
    try:
      try:

        os.rename(tmp_filename, self.__index_file)
      except OSError:


        os.remove(self.__index_file)
        os.rename(tmp_filename, self.__index_file)
    finally:
      self.__index_file_lock.release()

  def _ReadFromFile(self):
    self.__index_file_lock.acquire()
    try:
      if os.path.isfile(self.__index_file):
        version, indexes = pickle.load(open(self.__index_file, 'rb'))
        if version == self._VERSION:
          return indexes
        logging.warning(
            'Saved search indexes are not compatible with this version of the '
            'SDK. Search indexes have been cleared.')
      else:
        logging.warning(
            'Could not read search indexes from %s', self.__index_file)
    except (AttributeError, LookupError, ImportError, NameError, TypeError,
            ValueError, pickle.PickleError, IOError), e:
      logging.warning(
          'Could not read indexes from %s. Try running with the '
          '--clear_search_index flag. Cause:\n%r' % (self.__index_file, e))
    finally:
      self.__index_file_lock.release()

    return {}

  def Read(self):
    """Read search indexes from the index file.

    This method is a no-op if index_file is set to None.
    """
    if not self.__index_file:
      return
    read_indexes = self._ReadFromFile()
    if read_indexes:
      self.__indexes = read_indexes
