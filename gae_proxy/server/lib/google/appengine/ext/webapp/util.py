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




"""Convience functions for the Webapp framework."""










__all__ = ['login_required',
           'run_wsgi_app',
           'add_wsgi_middleware',
           'run_bare_wsgi_app',
           ]

import logging
import os
import string
import sys
import wsgiref.util

from google.appengine.api import users
from google.appengine.ext import webapp


def login_required(handler_method):
  """A decorator to require that a user be logged in to access a handler.

  To use it, decorate your get() method like this:

    @login_required
    def get(self):
      user = users.get_current_user(self)
      self.response.out.write('Hello, ' + user.nickname())

  We will redirect to a login page if the user is not logged in. We always
  redirect to the request URI, and Google Accounts only redirects back as a GET
  request, so this should not be used for POSTs.
  """
  def check_login(self, *args):
    if self.request.method != 'GET':
      raise webapp.Error('The check_login decorator can only be used for GET '
                         'requests')
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return
    else:
      handler_method(self, *args)
  return check_login


def run_wsgi_app(application):
  """Runs your WSGI-compliant application object in a CGI environment.

  Compared to wsgiref.handlers.CGIHandler().run(application), this
  function takes some shortcuts.  Those are possible because the
  app server makes stronger promises than the CGI standard.

  Also, this function may wrap custom WSGI middleware around the
  application.  (You can use run_bare_wsgi_app() to run an application
  without adding WSGI middleware, and add_wsgi_middleware() to wrap
  the configured WSGI middleware around an application without running
  it.  This function is merely a convenient combination of the latter
  two.)

  To configure custom WSGI middleware, define a function
  webapp_add_wsgi_middleware(app) to your appengine_config.py file in
  your application root directory:

    def webapp_add_wsgi_middleware(app):
      app = MiddleWareClassOne(app)
      app = MiddleWareClassTwo(app)
      return app

  You must import the middleware classes elsewhere in the file.  If
  the function is not found, no WSGI middleware is added.
  """
  run_bare_wsgi_app(add_wsgi_middleware(application))


def add_wsgi_middleware(application):
  """Wrap WSGI middleware around a WSGI application object."""
  return webapp._config_handle.add_wsgi_middleware(application)


def run_bare_wsgi_app(application):
  """Like run_wsgi_app() but doesn't add WSGI middleware."""
  env = dict(os.environ)
  env["wsgi.input"] = sys.stdin
  env["wsgi.errors"] = sys.stderr
  env["wsgi.version"] = (1, 0)
  env["wsgi.run_once"] = True
  env["wsgi.url_scheme"] = wsgiref.util.guess_scheme(env)
  env["wsgi.multithread"] = False
  env["wsgi.multiprocess"] = False
  result = application(env, _start_response)
  try:
    if result is not None:
      for data in result:
        sys.stdout.write(data)
  finally:
    if hasattr(result, 'close'):
      result.close()

_LOW_RANGE = ''.join(chr(i) for i in range(0, 32))
_HIGH_RANGE = ''.join(chr(i) for i in range(128, 256))




_FORBIDDEN_HEADER_NAME_CHARACTERS = _LOW_RANGE + _HIGH_RANGE + ' :'


_FORBIDDEN_HEADER_VALUE_CHARACTERS = _LOW_RANGE + _HIGH_RANGE

_EMPTY_TRANSLATION_TABLE = (None if sys.version_info >= (2, 6) else
                            string.maketrans('', ''))


def _start_response(status, headers, exc_info=None):
  """A start_response() callable as specified by PEP 333."""
  if exc_info is not None:

    raise exc_info[0], exc_info[1], exc_info[2]
  print "Status: %s" % status
  for name, val in headers:

    try:
      if isinstance(name, unicode):
        name = name.encode('ascii')
    except UnicodeEncodeError:
      logging.warn('Stripped header "%s": invalid character.', name)
      continue

    try:
      if isinstance(val, unicode):
        val = val.encode('ascii')
    except UnicodeEncodeError:
      logging.warn('Stripped header "%s": invalid character in value "%s".',
                   name, val)
      continue

    if name != name.translate(_EMPTY_TRANSLATION_TABLE,
                              _FORBIDDEN_HEADER_NAME_CHARACTERS):
      logging.warn('Stripped header "%s": invalid character.', name)
      continue

    if val != val.translate(_EMPTY_TRANSLATION_TABLE,
                            _FORBIDDEN_HEADER_VALUE_CHARACTERS):
      logging.warn('Stripped header "%s": invalid character in value "%s".',
                   name, val)
      continue
    print "%s: %s" % (name, val)
  print
  return sys.stdout.write
