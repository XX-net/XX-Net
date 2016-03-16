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
"""Expression evaluator for Full Text Search API stub.

An associated ExpressionEvaluator object is created for every scored document in
search results, and that object evaluates all expressions for that document. The
expression syntax is detailed here:

https://developers.google.com/appengine/docs/python/search/overview#Expressions

Usage examples:

  # Evaluate one expression for scored_doc
  expression = search_service_pb.FieldSpec_Expression()
  expression.set_name('total_value')
  expression.set_expression('max(0, 3 * value + _score)')
  ExpressionEvaluator(scored_doc, inverted_index).Evaluate(expression)
  # scored_doc.expressions['total_value'] is now set to the expression result.

  # Attach the result of all expressions for documents in scored_docs
  for scored_doc in scored_docs:
    evaluator = ExpressionEvaluator(scored_doc, inverted_index)
    for expression in expression_protos:
      evaluator.Evaluate(expression)

Note that this is not used for the production Full Text Search API; this
provides an approximation to the API for local testing with dev_appserver.

"""



import logging
import math

from google.appengine.datastore import document_pb

from google.appengine.api.search import expression_parser
from google.appengine.api.search import ExpressionParser
from google.appengine.api.search import geo_util
from google.appengine.api.search import query_parser
from google.appengine.api.search import search_util
from google.appengine.api.search.stub import simple_tokenizer
from google.appengine.api.search.stub import tokens




_SNIPPET_PREFIX = '...'
_SNIPPET_SUFFIX = '...'


class QueryExpressionEvaluationError(Exception):
  """ExpressionEvaluation Error that needs to return query as error status."""


class ExpressionEvaluationError(Exception):
  """Exposed version of _ExpressionError."""


class _ExpressionError(Exception):
  """Raised when evaluating an expression fails."""


class ExpressionEvaluator(object):
  """Evaluates an expression on scored documents."""

  def __init__(self, document, inverted_index, is_sort_expression=False):
    """Constructor.

    Args:
      document: The ScoredDocument to evaluate the expression for.
      inverted_index: The search index (used for snippeting).
      is_sort_expression: The flag indicates if this is a sort expression. Some
        operations (such as COUNT) are not supported in sort expressions.
    """
    self._doc = document
    self._doc_pb = document.document
    self._inverted_index = inverted_index
    self._tokenizer = simple_tokenizer.SimpleTokenizer(preserve_case=False)
    self._case_preserving_tokenizer = simple_tokenizer.SimpleTokenizer(
        preserve_case=True)
    self._function_table = {
        ExpressionParser.ABS: self._Abs,
        ExpressionParser.COUNT: self._Count,
        ExpressionParser.DISTANCE: self._Distance,
        ExpressionParser.GEOPOINT: self._Geopoint,
        ExpressionParser.LOG: self._Log,
        ExpressionParser.MAX: self._Max,
        ExpressionParser.MIN: self._Min,
        ExpressionParser.POW: self._Pow,
        ExpressionParser.SNIPPET: self._Snippet,
        ExpressionParser.SWITCH: self._Unsupported('switch'),
        }
    self._is_sort_expression = is_sort_expression

  @classmethod
  def _GetFieldValue(cls, field):
    """Returns the value of a field as the correct type.

    Args:
      field: The field whose value is extracted.  If the given field is None, this
        function also returns None. This is to make it easier to chain with
        GetFieldInDocument().

    Returns:
      The value of the field with the correct type (float for number fields,
      datetime.datetime for date fields, etc).

    Raises:
      TypeError: if the type of the field isn't recognized.
    """
    if not field:
      return None
    value_type = field.value().type()

    if value_type in search_util.TEXT_DOCUMENT_FIELD_TYPES:
      return field.value().string_value()
    if value_type == document_pb.FieldValue.DATE:
      value = field.value().string_value()
      return search_util.DeserializeDate(value)
    if value_type == document_pb.FieldValue.NUMBER:
      value = field.value().string_value()
      return float(value)
    if value_type == document_pb.FieldValue.GEO:
      value = field.value().geo()
      return geo_util.LatLng(value.lat(), value.lng())
    raise TypeError('No conversion defined for type %s' % value_type)

  def _Min(self, return_type, *nodes):
    if return_type == search_util.EXPRESSION_RETURN_TYPE_TEXT:
      raise _ExpressionError('Min cannot be converted to a text type')
    return min(self._Eval(
        node, document_pb.FieldValue.NUMBER) for node in nodes)

  def _Max(self, return_type, *nodes):
    if return_type == search_util.EXPRESSION_RETURN_TYPE_TEXT:
      raise _ExpressionError('Max cannot be converted to a text type')
    return max(self._Eval(
        node, document_pb.FieldValue.NUMBER) for node in nodes)

  def _Abs(self, return_type, node):
    if return_type == search_util.EXPRESSION_RETURN_TYPE_TEXT:
      raise _ExpressionError('Abs cannot be converted to a text type')
    return abs(self._Eval(node, document_pb.FieldValue.NUMBER))

  def _Log(self, return_type, node):
    if return_type == search_util.EXPRESSION_RETURN_TYPE_TEXT:
      raise _ExpressionError('Log cannot be converted to a text type')
    return math.log(self._Eval(node, document_pb.FieldValue.NUMBER))

  def _Pow(self, return_type, *nodes):
    if return_type == search_util.EXPRESSION_RETURN_TYPE_TEXT:
      raise _ExpressionError('Pow cannot be converted to a text type')
    lhs, rhs = nodes
    return pow(self._Eval(lhs, document_pb.FieldValue.NUMBER),
               self._Eval(rhs, document_pb.FieldValue.NUMBER))

  def _Distance(self, return_type, *nodes):
    if return_type == search_util.EXPRESSION_RETURN_TYPE_TEXT:
      raise _ExpressionError('Distance cannot be converted to a text type')
    lhs, rhs = nodes
    return (self._Eval(lhs, document_pb.FieldValue.GEO) -
            self._Eval(rhs, document_pb.FieldValue.GEO))

  def _Geopoint(self, return_type, *nodes):
    if return_type == search_util.EXPRESSION_RETURN_TYPE_TEXT:
      raise _ExpressionError('Geopoint cannot be converted to a text type')
    latitude, longitude = (self._Eval(
        node, document_pb.FieldValue.NUMBER) for node in nodes)
    return geo_util.LatLng(latitude, longitude)

  def _Count(self, return_type, node):






    if node.getType() != ExpressionParser.NAME:
      raise _ExpressionError(
          'The argument to count() must be a simple field name')
    if self._is_sort_expression:
      raise query_parser.QueryException(
          'Failed to parse sort expression \'count(' + node.getText() +
          ')\': count() is not supported in sort expressions')
    return search_util.GetFieldCountInDocument(
        self._doc_pb, query_parser.GetQueryNodeText(node))

  def _GenerateSnippet(self, doc_words, position, max_length):
    """Generate a snippet that fills a given length from a list of tokens.

    Args:
      doc_words: A list of tokens from the document.
      position: The index of the highlighted word.
      max_length: The maximum length of the output snippet.

    Returns:
      A summary of the given words with the word at index position highlighted.
    """
    snippet = '<b>%s</b>' % doc_words[position]

    next_len, prev_len = 0, 0
    if position + 1 < len(doc_words):

      next_len = len(doc_words[position+1]) + 1
    if position > 0:

      prev_len = len(doc_words[position-1]) + 1


    i = 1

    length_offset = len(_SNIPPET_PREFIX) + len(_SNIPPET_SUFFIX)
    while (len(snippet) + next_len + prev_len + length_offset < max_length and
           (position + i < len(doc_words) or position - i > 0)):
      if position + i < len(doc_words):
        snippet = '%s %s' % (snippet, doc_words[position+i])

        next_len = len(doc_words[position+i]) + 1
      else:
        next_len = 0

      if position - i >= 0:
        snippet = '%s %s' % (doc_words[position-i], snippet)

        prev_len = len(doc_words[position-i]) + 1
      else:
        prev_len = 0

      i += 1
    return '%s%s%s' % (_SNIPPET_PREFIX, snippet, _SNIPPET_SUFFIX)




  def _Snippet(self, return_type, query, field, *args):
    """Create a snippet given a query and the field to query on.

    Args:
      query: A query string containing only a bare term (no operators).
      field: The field name to query on.
      *args: Unused optional arguments. These are not used on dev_appserver.

    Returns:
      A snippet for the field with the query term bolded.

    Raises:
      ExpressionEvaluationError: if this is a sort expression.
    """
    field = query_parser.GetQueryNodeText(field)

    if self._is_sort_expression:
      raise ExpressionEvaluationError(
          'Failed to parse sort expression \'snippet(' +
          query_parser.GetQueryNodeText(query) + ', ' + field +
          ')\': snippet() is not supported in sort expressions')


    schema = self._inverted_index.GetSchema()
    if schema.IsType(field, document_pb.FieldValue.NUMBER):
      raise ExpressionEvaluationError(
          'Failed to parse field expression \'snippet(' +
          query_parser.GetQueryNodeText(query) + ', ' + field +
          ')\': snippet() argument 2 must be text')

    terms = self._tokenizer.TokenizeText(
        query_parser.GetQueryNodeText(query).strip('"'))
    for term in terms:
      search_token = tokens.Token(chars=u'%s:%s' % (field, term.chars))
      postings = self._inverted_index.GetPostingsForToken(search_token)
      for posting in postings:
        if posting.doc_id != self._doc_pb.id() or not posting.positions:
          continue
        field_val = self._GetFieldValue(
            search_util.GetFieldInDocument(self._doc_pb, field))
        if not field_val:
          continue
        doc_words = [token.chars for token in
                     self._case_preserving_tokenizer.TokenizeText(field_val)]

        position = posting.positions[0]
        return self._GenerateSnippet(
            doc_words, position, search_util.DEFAULT_MAX_SNIPPET_LENGTH)
      else:
        field_val = self._GetFieldValue(
            search_util.GetFieldInDocument(self._doc_pb, field))
        if not field_val:
          return ''
        return '%s...' % field_val[:search_util.DEFAULT_MAX_SNIPPET_LENGTH]

  def _Unsupported(self, method):
    """Returns a function that raises an unsupported error when called.

    This should be used for methods that are not yet implemented in
    dev_appserver but are present in the API. If users call this function, the
    expression will be skipped and a warning will be logged.

    Args:
      method: The name of the method that was called (used for logging).

    Returns:
      A function that raises a UnsupportedOnDevError when called.
    """




    def RaiseUnsupported(*args):
      raise search_util.UnsupportedOnDevError(
          '%s is currently unsupported on dev_appserver.' % method)
    return RaiseUnsupported

  def _EvalNumericBinaryOp(self, op, op_name, node, return_type):
    """Evaluate a Numeric Binary operator on the document.

    Args:
      op: The operator function. Must take exactly two arguments.
      op_name: The name of the operator. Used in error messages.
      node: The expression AST node representing the operator application.
      return_type: The type to retrieve for fields with multiple types
        in the expression. Used when the field type is ambiguous and cannot be
        inferred from the context. If None, we retrieve the first field type
        found in doc list.

    Returns:
      The result of applying op to node's two children.

    Raises:
      ValueError: The node does not have exactly two children.
      _ExpressionError: The return type is Text.
    """
    if return_type == search_util.EXPRESSION_RETURN_TYPE_TEXT:
      raise _ExpressionError('Expression cannot be converted to a text type')
    if len(node.children) != 2:
      raise ValueError('%s operator must always have two arguments' % op_name)
    n1, n2 = node.children
    return op(self._Eval(n1, document_pb.FieldValue.NUMBER),
              self._Eval(n2, document_pb.FieldValue.NUMBER))

  def _EvalNumericUnaryOp(self, op, op_name, node, return_type):
    """Evaluate a unary operator on the document.

    Args:
      op: The operator function. Must take exactly one argument.
      op_name: The name of the operator. Used in error messages.
      node: The expression AST node representing the operator application.
      return_type: The type to retrieve for fields with multiple types
        in the expression. Used when the field type is ambiguous and cannot be
        inferred from the context. If None, we retrieve the first field type
        found in doc list.

    Returns:
      The result of applying op to node's child.

    Raises:
      ValueError: The node does not have exactly one child.
      _ExpressionError: The return type is Text.
    """
    if return_type == search_util.EXPRESSION_RETURN_TYPE_TEXT:
      raise _ExpressionError('Expression cannot be converted to a text type')
    if len(node.children) != 1:
      raise ValueError('%s operator must always have one arguments' % op_name)
    return op(self._Eval(node.children[0], document_pb.FieldValue.NUMBER))

  def _Eval(self, node, return_type=None):
    """Evaluate an expression node on the document.

    Args:
      node: The expression AST node representing an expression subtree.
      return_type: The type to retrieve for fields with multiple types
        in the expression. Used when the field type is ambiguous and cannot be
        inferred from the context. If None, we retrieve the first field type
        found in doc list.

    Returns:
      The Python value that maps to the value of node. Types are inferred from
      the expression, so expressions with numeric results will return as python
      int/long/floats, textual results will be strings, and dates will be
      datetimes.

    Raises:
      _ExpressionError: The expression cannot be evaluated on this document
      because either the expression is malformed or the document does not
      contain the required fields. Callers of _Eval should catch
      _ExpressionErrors and optionally log them; these are not fatal in any way,
      and are used to indicate that this expression should not be set on this
      document.
    """
    if node.getType() in self._function_table:
      func = self._function_table[node.getType()]


      return func(return_type, *node.children)

    if node.getType() == ExpressionParser.PLUS:
      return self._EvalNumericBinaryOp(lambda a, b: a + b, 'addition', node,
                                       return_type)
    if node.getType() == ExpressionParser.MINUS:
      return self._EvalNumericBinaryOp(lambda a, b: a - b, 'subtraction', node,
                                       return_type)
    if node.getType() == ExpressionParser.DIV:
      return self._EvalNumericBinaryOp(lambda a, b: a / b, 'division', node,
                                       return_type)
    if node.getType() == ExpressionParser.TIMES:
      return self._EvalNumericBinaryOp(lambda a, b: a * b,
                                       'multiplication', node, return_type)
    if node.getType() == ExpressionParser.NEG:
      return self._EvalNumericUnaryOp(lambda a: -a, 'negation', node,
                                      return_type)
    if node.getType() in (ExpressionParser.INT, ExpressionParser.FLOAT):
      return float(query_parser.GetQueryNodeText(node))
    if node.getType() == ExpressionParser.PHRASE:
      return query_parser.GetQueryNodeText(node).strip('"')

    if node.getType() == ExpressionParser.NAME:
      name = query_parser.GetQueryNodeText(node)
      if name == '_score':
        return self._doc.score
      field = search_util.GetFieldInDocument(self._doc_pb, name,
                                             return_type)
      if field:
        return self._GetFieldValue(field)
      raise _ExpressionError('No field %s in document' % name)

    raise _ExpressionError('Unable to handle node %s' % node)

  def ValueOf(self, expression, default_value=None, return_type=None):
    """Returns the value of an expression on a document.

    Args:
      expression: The expression string.
      default_value: The value to return if the expression cannot be evaluated.
      return_type: The type the expression should evaluate to. Used to create
        multiple sorts for ambiguous expressions. If None, the expression
        evaluates to the inferred type or first type of a field it encounters in
        a document.

    Returns:
      The value of the expression on the evaluator's document, or default_value
      if the expression cannot be evaluated on the document.

    Raises:
      ExpressionEvaluationError: sort expression cannot be evaluated
      because the expression or default value is malformed. Callers of
      ValueOf should catch and return error to user in response.
      QueryExpressionEvaluationError: same as ExpressionEvaluationError but
      these errors should return query as error status to users.
    """
    expression_tree = Parse(expression)
    if not expression_tree.getType() and expression_tree.children:
      expression_tree = expression_tree.children[0]





    name = query_parser.GetQueryNodeText(expression_tree)
    schema = self._inverted_index.GetSchema()
    if (expression_tree.getType() == ExpressionParser.NAME and
        name in schema):
      contains_text_result = False
      for field_type in schema[name].type_list():
        if field_type in search_util.TEXT_DOCUMENT_FIELD_TYPES:
          contains_text_result = True


      if (schema.IsType(name, document_pb.FieldValue.DATE) and
          not contains_text_result):
        if isinstance(default_value, basestring):
          try:
            default_value = search_util.DeserializeDate(default_value)
          except ValueError:
            raise QueryExpressionEvaluationError(
                'Default text value is not appropriate for sort expression \'' +
                name + '\': failed to parse date \"' + default_value + '\"')
    result = default_value
    try:
      result = self._Eval(expression_tree, return_type=return_type)
    except _ExpressionError, e:


      logging.debug('Skipping expression %s: %s', expression, e)
    except search_util.UnsupportedOnDevError, e:


      logging.warning(e.args[0])

    return result

  def Evaluate(self, expression):
    """Evaluates the expression for a document and attaches the result.

    Args:
      expression: The Expression protobuffer object.
    """

    name = expression.name()
    result = self.ValueOf(expression.expression())
    if isinstance(result, unicode):
      result = result.encode('utf-8')
    if result != None:
      self._doc.expressions[name] = result


def Parse(expression):
  """Parse an expression and return its parse tree.

  Args:
    expression: An expression string.

  Returns:
    A parse tree for the expression, as generated by expression_parser.
  """
  return expression_parser.Parse(expression).tree
