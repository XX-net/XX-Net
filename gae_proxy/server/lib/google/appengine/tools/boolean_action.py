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
"""Provides a flexible way of configuring Boolean flags using argparse.

This action behaves like the "store_const" action but allows the flag to accept
an optional value.

These syntaxes result a True value being assigned for the argument:
--boolean_flag=yes    # "yes" is not case sensitive.
--boolean_flag=true   # "true" is not case sensitive.
--boolean_flag=1

These syntaxes result a False value being assigned for the argument:
--boolean_flag=no     # "no" is not case sensitive.
--boolean_flag=false  # "false" is not case sensitive.
--boolean_flag=0

This syntax results in the value of the const parameter specified in the
call to add_argument being assigned for the argument:
--boolean_flag
"""

import argparse

_TRUE_VALUES = ['true', 'yes', '1']
_FALSE_VALUES = ['false', 'no', '0']


class BooleanAction(argparse.Action):

  def __init__(self,
               option_strings,
               dest,
               const,
               default=None,
               required=False,
               help=None,
               metavar=None):
    super(BooleanAction, self).__init__(
        option_strings=option_strings,
        dest=dest,
        nargs='?',
        const=const,
        default=default,
        required=required,
        help=help)

  def __call__(self, parser, namespace, values, option_string=None):
    setattr(namespace, self.dest, BooleanParse(values))


def BooleanParse(values):
  if isinstance(values, bool):
    return values
  if values:
    value = values.lower()
    if value in _TRUE_VALUES:
      return True
    if value in _FALSE_VALUES:
      return False
    repr_values = (repr(value) for value in _TRUE_VALUES + _FALSE_VALUES)

    raise ValueError('%r unrecognized boolean; known booleans are %s.' %
                     (values, ', '.join(repr_values)))

  return True
