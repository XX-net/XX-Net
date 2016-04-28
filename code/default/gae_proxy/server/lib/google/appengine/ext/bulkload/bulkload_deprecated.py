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




"""DEPRECATED mix-in handler for bulk loading data into an application.

Please use the new bulkloader.
"""










import Cookie
import StringIO
import csv
import httplib
import os
import traceback
import wsgiref.handlers

from google.appengine.api import datastore
from google.appengine.ext import webapp
from google.appengine.ext.bulkload import constants


def Validate(value, type):
  """ Checks that value is non-empty and of the right type.

  Raises ValueError if value is None or empty, TypeError if it's not the given
  type.

  Args:
    value: any value
    type: a type or tuple of types
  """
  if not value:
    raise ValueError('Value should not be empty; received %s.' % value)
  elif not isinstance(value, type):
    raise TypeError('Expected a %s, but received %s (a %s).' %
                    (type, value, value.__class__))


class Loader(object):
  """A base class for creating datastore entities from input data.

  To add a handler for bulk loading a new entity kind into your datastore,
  write a subclass of this class that calls Loader.__init__ from your
  class's __init__.

  If you need to run extra code to convert entities from the input
  data, create new properties, or otherwise modify the entities before
  they're inserted, override HandleEntity.

  See the CreateEntity method for the creation of entities from the
  (parsed) input data.
  """

  __loaders = {}
  __kind = None
  __properties = None

  def __init__(self, kind, properties):
    """ Constructor.

    Populates this Loader's kind and properties map. Also registers it with
    the bulk loader, so that all you need to do is instantiate your Loader,
    and the bulkload handler will automatically use it.

    Args:
      kind: a string containing the entity kind that this loader handles

      properties: list of (name, converter) tuples.

      This is used to automatically convert the CSV columns into properties.
      The converter should be a function that takes one argument, a string
      value from the CSV file, and returns a correctly typed property value
      that should be inserted. The tuples in this list should match the
      columns in your CSV file, in order.

      For example:
        [('name', str),
         ('id_number', int),
         ('email', datastore_types.Email),
         ('user', users.User),
         ('birthdate', lambda x: datetime.datetime.fromtimestamp(float(x))),
         ('description', datastore_types.Text),
         ]
    """
    Validate(kind, basestring)
    self.__kind = kind

    Validate(properties, list)
    for name, fn in properties:
      Validate(name, basestring)
      assert callable(fn), (
        'Conversion function %s for property %s is not callable.' % (fn, name))

    self.__properties = properties


    Loader.__loaders[kind] = self


  def kind(self):
    """ Return the entity kind that this Loader handes.
    """
    return self.__kind

  def CreateEntity(self, values, key_name=None):
    """ Creates an entity from a list of property values.

    Args:
      values: list/tuple of str
      key_name: if provided, the name for the (single) resulting Entity

    Returns:
      list of datastore.Entity

      The returned entities are populated with the property values from the
      argument, converted to native types using the properties map given in
      the constructor, and passed through HandleEntity. They're ready to be
      inserted.

    Raises:
      AssertionError if the number of values doesn't match the number
        of properties in the properties map.
    """
    Validate(values, (list, tuple))
    assert len(values) == len(self.__properties), (
      'Expected %d CSV columns, found %d.' %
      (len(self.__properties), len(values)))

    entity = datastore.Entity(self.__kind, name=key_name)
    for (name, converter), val in zip(self.__properties, values):
      if converter is bool and val.lower() in ('0', 'false', 'no'):
          val = False
      entity[name] = converter(val)

    entities = self.HandleEntity(entity)

    if entities is not None:
      if not isinstance(entities, (list, tuple)):
        entities = [entities]

      for entity in entities:
        if not isinstance(entity, datastore.Entity):
          raise TypeError('Expected a datastore.Entity, received %s (a %s).' %
                          (entity, entity.__class__))

    return entities


  def HandleEntity(self, entity):
    """ Subclasses can override this to add custom entity conversion code.

    This is called for each entity, after its properties are populated from
    CSV but before it is stored. Subclasses can override this to add custom
    entity handling code.

    The entity to be inserted should be returned. If multiple entities should
    be inserted, return a list of entities. If no entities should be inserted,
    return None or [].

    Args:
      entity: datastore.Entity

    Returns:
      datastore.Entity or list of datastore.Entity
    """
    return entity


  @staticmethod
  def RegisteredLoaders():
    """ Returns a list of the Loader instances that have been created.
    """

    return dict(Loader.__loaders)


class BulkLoad(webapp.RequestHandler):
  """A handler for bulk load requests.

  This class contains handlers for the bulkloading process. One for
  GET to provide cookie information for the upload script, and one
  handler for a POST request to upload the entities.

  In the POST request, the body contains the data representing the
  entities' property values. The original format was a sequences of
  lines of comma-separated values (and is handled by the Load
  method). The current (version 1) format is a binary format described
  in the Tools and Libraries section of the documentation, and is
  handled by the LoadV1 method).
  """

  def get(self):
    """ Handle a GET. Just show an info page.
    """
    page = self.InfoPage(self.request.uri)
    self.response.out.write(page)


  def post(self):
    """ Handle a POST. Reads CSV data, converts to entities, and stores them.
    """
    self.response.headers['Content-Type'] = 'text/plain'
    response, output = self.Load(self.request.get(constants.KIND_PARAM),
                                 self.request.get(constants.CSV_PARAM))
    self.response.set_status(response)
    self.response.out.write(output)


  def InfoPage(self, uri):
    """ Renders an information page with the POST endpoint and cookie flag.

    Args:
      uri: a string containing the request URI
    Returns:
      A string with the contents of the info page to be displayed
    """
    page = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html><head>
<title>Bulk Loader</title>
</head><body>"""

    page += ('The bulk load endpoint is: <a href="%s">%s</a><br />\n' %
            (uri, uri))


    cookies = os.environ.get('HTTP_COOKIE', None)
    if cookies:
      cookie = Cookie.BaseCookie(cookies)




      for param in ['ACSID', 'dev_appserver_login']:
        value = cookie.get(param)
        if value:
          page += ("Pass this flag to the client: --cookie='%s=%s'\n" %
                   (param, value.value))
          break

    else:
      page += 'No cookie found!\n'

    page += '</body></html>'
    return page

  def IterRows(self, reader):
    """ Yields a tuple of a line number and row for each row of the CSV data.

    Args:
      reader: a csv reader for the input data.
    """


    line_num = 1
    for columns in reader:
      yield (line_num, columns)
      line_num += 1

  def LoadEntities(self, iter, loader, key_format=None):
    """Generates entities and loads them into the datastore.  Returns
    a tuple of HTTP code and string reply.

    Args:
      iter: an iterator yielding pairs of a line number and row contents.
      key_format: a format string to convert a line number into an
        entity id. If None, then entity ID's are automatically generated.
      """
    entities = []
    output = []
    for line_num, columns in iter:
      key_name = None
      if key_format is not None:
        key_name = key_format % line_num
      if columns:
        try:
          output.append('\nLoading from line %d...' % line_num)
          new_entities = loader.CreateEntity(columns, key_name=key_name)
          if new_entities:
            entities.extend(new_entities)
          output.append('done.')
        except:
          stacktrace = traceback.format_exc()
          output.append('error:\n%s' % stacktrace)
          return (httplib.BAD_REQUEST, ''.join(output))

    datastore.Put(entities)

    return (httplib.OK, ''.join(output))

  def Load(self, kind, data):
    """Parses CSV data, uses a Loader to convert to entities, and stores them.

    On error, fails fast. Returns a "bad request" HTTP response code and
    includes the traceback in the output.

    Args:
      kind: a string containing the entity kind that this loader handles
      data: a string containing the CSV data to load

    Returns:
      tuple (response code, output) where:
        response code: integer HTTP response code to return
        output: string containing the HTTP response body
    """

    data = data.encode('utf-8')
    Validate(kind, basestring)
    Validate(data, basestring)
    output = []

    try:
      loader = Loader.RegisteredLoaders()[kind]
    except KeyError:
      output.append('Error: no Loader defined for kind %s.' % kind)
      return (httplib.BAD_REQUEST, ''.join(output))

    buffer = StringIO.StringIO(data)
    reader = csv.reader(buffer, skipinitialspace=True)

    try:
      csv.field_size_limit(800000)
    except AttributeError:

      pass

    return self.LoadEntities(self.IterRows(reader), loader)


def main(*loaders):
  """Starts bulk upload.

  Raises TypeError if not, at least one Loader instance is given.

  Args:
    loaders: One or more Loader instance.
  """
  if not loaders:
    raise TypeError('Expected at least one argument.')

  for loader in loaders:
    if not isinstance(loader, Loader):
      raise TypeError('Expected a Loader instance; received %r' % loader)

  application = webapp.WSGIApplication([('.*', BulkLoad)])
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
