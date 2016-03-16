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




"""Relational database API for production.

Note that rdbms_mysqldb is the module used in dev_appserver.
"""








import logging

from google.storage.speckle.python.api import rdbms_apiproxy


from google.storage.speckle.python.api.rdbms_apiproxy import *


_instance = None

def set_instance(instance):
  global _instance
  _instance = instance

def connect(instance=None, database=None, **kwargs):
  global _instance
  if not instance and _instance:
    instance = _instance

  if 'db' in kwargs and not database:
    database = kwargs.pop('db')

  user = None
  if 'user' in kwargs:
    user = kwargs.pop('user')

  password = None
  if 'password' in kwargs:
    password = kwargs.pop('password')

  if kwargs:
    logging.info('Ignoring extra kwargs to connect(): %r', kwargs)

  return rdbms_apiproxy.connect('unused_address',
                                instance,
                                database=database,
                                user=user,
                                password=password)
