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




"""Wrapper for ExpressionParser."""



from google.appengine._internal import antlr3
from google.appengine.api.search import ExpressionLexer
from google.appengine.api.search import ExpressionParser


class ExpressionException(Exception):
  """An error occurred while parsing the expression input string."""


class ExpressionLexerWithErrors(ExpressionLexer.ExpressionLexer):
  """An overridden Lexer that raises exceptions."""

  def emitErrorMessage(self, msg):
    """Raise an exception if the input fails to parse correctly.

    Overriding the default, which normally just prints a message to
    stderr.

    Arguments:
      msg: the error message
    Raises:
      ExpressionException: always.
    """
    raise ExpressionException(msg)


class ExpressionParserWithErrors(ExpressionParser.ExpressionParser):
  """An overridden Parser that raises exceptions."""

  def emitErrorMessage(self, msg):
    """Raise an exception if the input fails to parse correctly.

    Overriding the default, which normally just prints a message to
    stderr.

    Arguments:
      msg: the error message
    Raises:
      ExpressionException: always.
    """
    raise ExpressionException(msg)


def CreateParser(expression):
  """Creates a Expression Parser."""
  input_string = antlr3.ANTLRStringStream(expression)
  lexer = ExpressionLexerWithErrors(input_string)
  tokens = antlr3.CommonTokenStream(lexer)
  parser = ExpressionParserWithErrors(tokens)
  return parser


def Parse(expression):
  """Parses an expression and returns the ANTLR tree."""
  parser = CreateParser(expression)
  try:
    return parser.expression()
  except Exception, e:
    raise ExpressionException(e.message)
