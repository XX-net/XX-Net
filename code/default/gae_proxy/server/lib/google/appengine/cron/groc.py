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









"""A wrapper around the generated Groc parser and lexer."""



import google

import antlr3

import GrocLexer
import GrocParser


class GrocException(Exception):
  """An error occurred while parsing the groc input string."""


class GrocLexerWithErrors(GrocLexer.GrocLexer):
  """An overridden Lexer that raises exceptions."""

  def emitErrorMessage(self, msg):
    """Raise an exception if the input fails to parse correctly.

    Overriding the default, which normally just prints a message to
    stderr.

    Arguments:
      msg: the error message
    Raises:
      GrocException: always.
    """
    raise GrocException(msg)


class GrocParserWithErrors(GrocParser.GrocParser):
  """An overridden Parser that raises exceptions."""

  def emitErrorMessage(self, msg):
    """Raise an exception if the input fails to parse correctly.

    Overriding the default, which normally just prints a message to
    stderr.

    Arguments:
      msg: the error message
    Raises:
      GrocException: always.
    """
    raise GrocException(msg)


def CreateParser(parse_string):
  """Creates a Groc Parser."""
  input_string = antlr3.ANTLRStringStream(parse_string)
  lexer = GrocLexerWithErrors(input_string)
  tokens = antlr3.CommonTokenStream(lexer)
  parser = GrocParserWithErrors(tokens)
  return parser
