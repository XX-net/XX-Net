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







"""An extremely simple WSGI web application framework.

This module is an alias for the webapp2 module i.e. the following are
equivalent:

1. from google.appengine.ext import webapp
2. import webapp2 as webapp

It exports three primary classes: Request, Response, and RequestHandler. You
implement a web application by subclassing RequestHandler. As WSGI requests come
in, they are passed to instances of your RequestHandlers. The RequestHandler
class provides access to the easy-to-use Request and Response objects so you can
interpret the request and write the response with no knowledge of the esoteric
WSGI semantics.  Here is a simple example:

  from google.appengine.ext import webapp
  import wsgiref.simple_server

  class MainPage(webapp.RequestHandler):
    def get(self):
      self.response.out.write(
        '<html><body><form action="/hello" method="post">'
        'Name: <input name="name" type="text" size="20"> '
        '<input type="submit" value="Say Hello"></form></body></html>')

  class HelloPage(webapp.RequestHandler):
    def post(self):
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write('Hello, %s' % self.request.get('name'))

  application = webapp.WSGIApplication([
    ('/', MainPage),
    ('/hello', HelloPage)
  ], debug=True)

The WSGIApplication class maps URI regular expressions to your RequestHandler
classes.  It is a WSGI-compatible application object, so you can use it in
conjunction with wsgiref to make your web application into, e.g., a CGI
script or a simple HTTP server, as in the example above.

The framework does not support streaming output. All output from a response
is stored in memory before it is written.
"""



import logging
import os
import sys

from google.appengine.api import lib_config


def __django_version_setup():
  """Selects a particular Django version to load."""
  django_version = _config_handle.django_version

  if django_version is not None:


    from google.appengine.dist import use_library
    use_library('django', str(django_version))
  else:



    from google.appengine.dist import _library
    version, explicit = _library.installed.get('django', ('0.96', False))
    if not explicit:
      logging.warn('You are using the default Django version (%s). '
                   'The default Django version will change in an '
                   'App Engine release in the near future. '
                   'Please call use_library() to explicitly select a '
                   'Django version. '
                   'For more information see %s',
                   version,
                   'https://developers.google.com/appengine/docs/python/tools/'
                   'libraries#Django')































def _django_setup():
  """Imports and configures Django.

  This can be overridden by defining a function named
  webapp_django_setup() in the app's appengine_config.py file (see
  lib_config docs).  Such a function should import and configure
  Django.

  In the Python 2.5 runtime, you can also just configure the Django version to
  be used by setting webapp_django_version in that file.

  Finally, calling use_library('django', <version>) in that file
  should also work:

    # Example taken from from
    # https://developers.google.com/appengine/docs/python/tools/libraries#Django

    import os
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

    from google.appengine.dist import use_library
    use_library('django', '1.2')

  In the Python 2.7 runtime, the Django version is specified in you app.yaml
  file and use_library is not supported.

  If your application also imports Django directly it should ensure
  that the same code is executed before your app imports Django
  (directly or indirectly).  Perhaps the simplest way to ensure that
  is to include the following in your main.py (and in each alternate
  main script):

    from google.appengine.ext.webapp import template
    import django

  This will ensure that whatever Django setup code you have included
  in appengine_config.py is executed, as a side effect of importing
  the webapp.template module.
  """
  if os.environ.get('APPENGINE_RUNTIME') != 'python27':
    __django_version_setup()


  import django


  import django.conf
  try:


    getattr(django.conf.settings, 'FAKE_ATTR', None)
  except (ImportError, EnvironmentError), e:



    if os.getenv(django.conf.ENVIRONMENT_VARIABLE):


      logging.warning(e)

    try:
      django.conf.settings.configure(
        DEBUG=False,
        TEMPLATE_DEBUG=False,
        TEMPLATE_LOADERS=(
          'django.template.loaders.filesystem.load_template_source',
        ),
      )
    except (EnvironmentError, RuntimeError):



      pass



if os.environ.get('APPENGINE_RUNTIME') == 'python27':


  _config_handle = lib_config.register(
      'webapp',
      {'add_wsgi_middleware': lambda app: app,})
  from webapp2 import *
else:
  _config_handle = lib_config.register(
      'webapp',
      {'django_setup': _django_setup,
       'django_version': None,
       'add_wsgi_middleware': lambda app: app,
       })
  from google.appengine.ext.webapp._webapp25 import *
  from google.appengine.ext.webapp._webapp25 import __doc__
