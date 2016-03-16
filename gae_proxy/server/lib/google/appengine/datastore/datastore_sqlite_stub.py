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





"""SQlite-based stub for the Python datastore API.

Entities are stored in an sqlite database in a similar fashion to the production
datastore.

Transactions are serialized through __tx_lock. Each transaction acquires it
when it begins and releases it when it commits or rolls back.
"""













import array
import itertools
import logging
import threading
import weakref

from google.appengine.datastore import entity_pb
from google.appengine.api import apiproxy_stub
from google.appengine.api import datastore_types
from google.appengine.datastore import datastore_pb
from google.appengine.datastore import datastore_stub_util
from google.appengine.datastore import sortable_pb_encoder
from google.appengine.runtime import apiproxy_errors

try:
  import pysqlite2.dbapi2 as sqlite3
except ImportError:
  import sqlite3


import __builtin__
buffer = __builtin__.buffer



datastore_pb.Query.__hash__ = lambda self: hash(self.Encode())



_MAX_TIMEOUT = 5.0




_OPERATOR_MAP = {
    datastore_pb.Query_Filter.LESS_THAN: '<',
    datastore_pb.Query_Filter.LESS_THAN_OR_EQUAL: '<=',
    datastore_pb.Query_Filter.EQUAL: '=',
    datastore_pb.Query_Filter.GREATER_THAN: '>',
    datastore_pb.Query_Filter.GREATER_THAN_OR_EQUAL: '>=',


    '!=': '!=',
}



_ORDER_MAP = {
    datastore_pb.Query_Order.ASCENDING: 'ASC',
    datastore_pb.Query_Order.DESCENDING: 'DESC',
}

_CORE_SCHEMA = """
CREATE TABLE IF NOT EXISTS Apps (
  app_id TEXT NOT NULL PRIMARY KEY,
  indexes BLOB);

CREATE TABLE IF NOT EXISTS Namespaces (
  app_id TEXT NOT NULL,
  name_space TEXT NOT NULL,
  PRIMARY KEY (app_id, name_space));

CREATE TABLE IF NOT EXISTS IdSeq (
  prefix TEXT NOT NULL PRIMARY KEY,
  next_id INT NOT NULL);

CREATE TABLE IF NOT EXISTS ScatteredIdCounters (
  prefix TEXT NOT NULL PRIMARY KEY,
  next_id INT NOT NULL);

CREATE TABLE IF NOT EXISTS CommitTimestamps (
  prefix TEXT NOT NULL PRIMARY KEY,
  commit_timestamp INT NOT NULL);
"""

_NAMESPACE_SCHEMA = """
CREATE TABLE "%(prefix)s!Entities" (
  __path__ BLOB NOT NULL PRIMARY KEY,
  kind TEXT NOT NULL,
  entity BLOB NOT NULL);
CREATE INDEX "%(prefix)s!EntitiesByKind" ON "%(prefix)s!Entities" (
  kind ASC,
  __path__ ASC);

CREATE TABLE "%(prefix)s!EntitiesByProperty" (
  kind TEXT NOT NULL,
  name TEXT NOT NULL,
  value BLOB NOT NULL,
  __path__ BLOB NOT NULL REFERENCES Entities,
  PRIMARY KEY(kind ASC, name ASC, value ASC, __path__ ASC) ON CONFLICT IGNORE);
CREATE INDEX "%(prefix)s!EntitiesByPropertyDesc"
  ON "%(prefix)s!EntitiesByProperty" (
  kind ASC,
  name ASC,
  value DESC,
  __path__ ASC);
CREATE INDEX "%(prefix)s!EntitiesByPropertyKey"
  ON "%(prefix)s!EntitiesByProperty" (
  __path__ ASC);

INSERT OR IGNORE INTO Apps (app_id) VALUES ('%(app_id)s');
INSERT INTO Namespaces (app_id, name_space)
  VALUES ('%(app_id)s', '%(name_space)s');
INSERT OR IGNORE INTO IdSeq VALUES ('%(prefix)s', 1);
INSERT OR IGNORE INTO ScatteredIdCounters VALUES ('%(prefix)s', 1);
"""


class SQLiteCursorWrapper(sqlite3.Cursor):
  """Substitutes sqlite3.Cursor, with a cursor that logs commands.

  Inherits from sqlite3.Cursor class and extends methods such as execute,
  executemany and execute script, so it logs SQL calls.
  """


  def execute(self, sql, *args):
    """Replaces execute() with a logging variant."""
    if args:
      parameters = []
      for arg in args:
        if isinstance(arg, buffer):
          parameters.append('<blob>')
        else:
          parameters.append(repr(arg))
      logging.debug('SQL Execute: %s - \n %s', sql,
                    '\n '.join(str(param) for param in parameters))
    else:
      logging.debug(sql)
    return super(SQLiteCursorWrapper, self).execute(sql, *args)

  def executemany(self, sql, seq_parameters):
    """Replaces executemany() with a logging variant."""
    seq_parameters_list = list(seq_parameters)
    logging.debug('SQL ExecuteMany: %s - \n %s', sql,
                  '\n '.join(str(param) for param in seq_parameters_list))
    return super(SQLiteCursorWrapper, self).executemany(sql,
                                                        seq_parameters_list)


  def executescript(self, sql):
    """Replaces executescript() with a logging variant."""
    logging.debug('SQL ExecuteScript: %s', sql)
    return super(SQLiteCursorWrapper, self).executescript(sql)


class SQLiteConnectionWrapper(sqlite3.Connection):
  """Substitutes sqlite3.Connection with a connection that logs commands.

  Inherits from sqlite3.Connection class and overrides cursor
  replacing the default cursor with an instance of SQLiteCursorWrapper. This
  automatically makes execute, executemany, executescript and others use the
  SQLiteCursorWrapper.
  """


  def cursor(self):
    """Substitutes standard cursor() with a SQLiteCursorWrapper to log queries.

    Substitutes the standard sqlite.Cursor with SQLiteCursorWrapper to ensure
    all cursor requests get intercepted.

    Returns:
      A SQLiteCursorWrapper Instance.
    """
    return super(SQLiteConnectionWrapper, self).cursor(SQLiteCursorWrapper)


def ReferencePropertyToReference(refprop):
  ref = entity_pb.Reference()
  ref.set_app(refprop.app())
  if refprop.has_name_space():
    ref.set_name_space(refprop.name_space())
  for pathelem in refprop.pathelement_list():
    ref.mutable_path().add_element().CopyFrom(pathelem)
  return ref


def _DedupingEntityGenerator(cursor):
  """Generator that removes duplicate entities from the results.

  Generate datastore entities from a cursor, skipping the duplicates

  Args:
    cursor: a SQLite3.Cursor or subclass.

  Yields:
    Entities that do not share a key.
  """
  seen = set()
  for row in cursor:
    row_key, row_entity = row[:2]
    encoded_row_key = str(row_key)
    if encoded_row_key in seen:
      continue

    seen.add(encoded_row_key)
    storage_entity = entity_pb.EntityProto(row_entity)
    record = datastore_stub_util._FromStorageEntity(storage_entity)
    record = datastore_stub_util.LoadRecord(record)
    yield record


def _ProjectionPartialEntityGenerator(cursor):
  """Generator that creates partial entities for projection.

  Generate partial datastore entities from a cursor, holding only the values
  being projected. These entities might share a key.

  Args:
    cursor: a SQLite3.Cursor or subclass.

  Yields:
    Partial entities resulting from the projection.
  """
  for row in cursor:
    storage_entity = entity_pb.EntityProto(row[1])
    record = datastore_stub_util._FromStorageEntity(storage_entity)
    original_entity = record.entity

    entity = entity_pb.EntityProto()
    entity.mutable_key().MergeFrom(original_entity.key())
    entity.mutable_entity_group().MergeFrom(original_entity.entity_group())

    for name, value_data in zip(row[2::2], row[3::2]):
      prop_to_add = entity.add_property()
      prop_to_add.set_name(ToUtf8(name))


      value_decoder = sortable_pb_encoder.Decoder(
          array.array('B', str(value_data)))
      prop_to_add.mutable_value().Merge(value_decoder)
      prop_to_add.set_multiple(False)

    datastore_stub_util.PrepareSpecialPropertiesForLoad(entity)
    yield datastore_stub_util.EntityRecord(entity)


def MakeEntityForQuery(query, *path):
  """Make an entity to be returned by a pseudo-kind query.

  Args:
    query: the query which will return the entity.
    path: pairs of type/name-or-id values specifying the entity's key
  Returns:
    An entity_pb.EntityProto with app and namespace as in query and the key
    specified by path.
  """
  pseudo_pb = entity_pb.EntityProto()
  pseudo_pb.mutable_entity_group()
  pseudo_pk = pseudo_pb.mutable_key()
  pseudo_pk.set_app(query.app())
  if query.has_name_space():
    pseudo_pk.set_name_space(query.name_space())


  for i in xrange(0, len(path), 2):
    pseudo_pe = pseudo_pk.mutable_path().add_element()
    pseudo_pe.set_type(path[i])
    if isinstance(path[i + 1], basestring):
      pseudo_pe.set_name(path[i + 1])
    else:
      pseudo_pe.set_id(path[i + 1])

  return pseudo_pb


def ToUtf8(s):
  """Encoded s in utf-8 if it is an unicode string."""
  if isinstance(s, unicode):
    return s.encode('utf-8')
  else:
    return s


class KindPseudoKind(object):
  """Pseudo-kind for __kind__ queries.

  Provides a Query method to perform the actual query.

  Public properties:
    name: the pseudo-kind name
  """
  name = '__kind__'

  def Query(self, query, filters, orders):
    """Perform a query on this pseudo-kind.

    Args:
      query: the original datastore_pb.Query
      filters: the filters from query
      orders: the orders from query

    Returns:
      A query cursor to iterate over the query results, or None if the query
      is invalid.
    """
    kind_range = datastore_stub_util.ParseKindQuery(query, filters, orders)
    conn = self._stub._GetConnection()
    cursor = None
    try:
      prefix = self._stub._GetTablePrefix(query)
      filters = []

      def AddExtremeFilter(extreme, inclusive, is_end):
        """Add filter for kind start/end."""
        if not is_end:
          if inclusive:
            op = datastore_pb.Query_Filter.GREATER_THAN_OR_EQUAL
          else:
            op = datastore_pb.Query_Filter.GREATER_THAN
        else:
          if inclusive:
            op = datastore_pb.Query_Filter.LESS_THAN_OR_EQUAL
          else:
            op = datastore_pb.Query_Filter.LESS_THAN
        filters.append(('kind', op, extreme))
      kind_range.MapExtremes(AddExtremeFilter)

      params = []
      sql_filters = self._stub._CreateFilterString(filters, params)

      sql_stmt = ('SELECT kind FROM "%s!Entities" %s GROUP BY kind'
                  % (prefix, sql_filters))
      c = conn.execute(sql_stmt, params)

      kinds = []
      for row in c.fetchall():
        kinds.append(MakeEntityForQuery(query, self.name, ToUtf8(row[0])))

      records = map(datastore_stub_util.EntityRecord, kinds)
      cursor = datastore_stub_util._ExecuteQuery(records, query, [], [], [])
    finally:
      self._stub._ReleaseConnection(conn)

    return cursor


class PropertyPseudoKind(object):
  """Pseudo-kind for __property__ queries.

  Provides a Query method to perform the actual query.

  Public properties:
    name: the pseudo-kind name
  """
  name = '__property__'

  def Query(self, query, filters, orders):
    """Perform a query on this pseudo-kind.

    Args:
      query: the original datastore_pb.Query
      filters: the filters from query
      orders: the orders from query

    Returns:
      A query cursor to iterate over the query results, or None if the query
      is invalid.
    """
    property_range = datastore_stub_util.ParsePropertyQuery(query, filters,
                                                            orders)
    keys_only = query.keys_only()
    conn = self._stub._GetConnection()
    cursor = None
    try:
      prefix = self._stub._GetTablePrefix(query)
      filters = []






      def AddExtremeFilter(extreme, inclusive, is_end):
        """Add filter for kind start/end."""
        if not is_end:
          op = datastore_pb.Query_Filter.GREATER_THAN_OR_EQUAL
        else:
          op = datastore_pb.Query_Filter.LESS_THAN_OR_EQUAL
        filters.append(('kind', op, extreme[0]))
      property_range.MapExtremes(AddExtremeFilter)


      for name in datastore_stub_util.GetInvisibleSpecialPropertyNames():
        filters.append(('name', '!=', name))

      params = []
      sql_filters = self._stub._CreateFilterString(filters, params)
      if not keys_only:




        sql_stmt = ('SELECT kind, name, value FROM "%s!EntitiesByProperty" %s '
                    'GROUP BY kind, name, substr(value, 1, 1) '
                    'ORDER BY kind, name'
                    % (prefix, sql_filters))
      else:

        sql_stmt = ('SELECT kind, name FROM "%s!EntitiesByProperty" %s '
                    'GROUP BY kind, name ORDER BY kind, name'
                    % (prefix, sql_filters))
      c = conn.execute(sql_stmt, params)

      properties = []
      kind = None
      name = None
      property_pb = None
      for row in c.fetchall():
        if not (row[0] == kind and row[1] == name):

          if not property_range.Contains((row[0], row[1])):
            continue
          kind, name = row[:2]

          if property_pb:
            properties.append(property_pb)
          property_pb = MakeEntityForQuery(query, KindPseudoKind.name,
                                           ToUtf8(kind),
                                           self.name, ToUtf8(name))

        if not keys_only:

          value_data = row[2]
          value_decoder = sortable_pb_encoder.Decoder(
              array.array('B', str(value_data)))
          raw_value_pb = entity_pb.PropertyValue()
          raw_value_pb.Merge(value_decoder)
          tag = datastore_types.GetPropertyValueTag(raw_value_pb)
          tag_name = datastore_stub_util._PROPERTY_TYPE_NAMES[tag]


          representation_pb = property_pb.add_property()
          representation_pb.set_name('property_representation')
          representation_pb.set_multiple(True)
          representation_pb.mutable_value().set_stringvalue(tag_name)

      if property_pb:
        properties.append(property_pb)

      records = map(datastore_stub_util.EntityRecord, properties)
      cursor = datastore_stub_util._ExecuteQuery(records, query, [], [], [])
    finally:
      self._stub._ReleaseConnection(conn)

    return cursor


class NamespacePseudoKind(object):
  """Pseudo-kind for __namespace__ queries.

  Provides a Query method to perform the actual query.

  Public properties:
    name: the pseudo-kind name
  """
  name = '__namespace__'

  def Query(self, query, filters, orders):
    """Perform a query on this pseudo-kind.

    Args:
      query: the original datastore_pb.Query
      filters: the filters from query
      orders: the orders from query

    Returns:
      A query cursor to iterate over the query results, or None if the query
      is invalid.
    """
    namespace_range = datastore_stub_util.ParseNamespaceQuery(query, filters,
                                                              orders)
    app_str = query.app()

    namespace_entities = []



    namespaces = self._stub._DatastoreSqliteStub__namespaces
    for app_id, namespace in sorted(namespaces):
      if app_id == app_str and namespace_range.Contains(namespace):
        if namespace:
          ns_id = namespace
        else:
          ns_id = datastore_types._EMPTY_NAMESPACE_ID
        namespace_entities.append(MakeEntityForQuery(query, self.name, ns_id))

    records = map(datastore_stub_util.EntityRecord, namespace_entities)
    return datastore_stub_util._ExecuteQuery(records, query, [], [], [])

class DatastoreSqliteStub(datastore_stub_util.BaseDatastore,
                          apiproxy_stub.APIProxyStub,
                          datastore_stub_util.DatastoreStub):
  """Persistent stub for the Python datastore API.

  Stores all entities in an SQLite database. A DatastoreSqliteStub instance
  handles a single app's data.
  """





  _MAX_QUERY_COMPONENTS = 63

  READ_ERROR_MSG = ('Data in %s is corrupt or a different version. '
                    'Try running with the --clear_datastore flag.\n%r')

  def __init__(self,
               app_id,
               datastore_file,
               require_indexes=False,
               verbose=False,
               service_name='datastore_v3',
               trusted=False,
               consistency_policy=None,
               root_path=None,
               use_atexit=True,
               auto_id_policy=datastore_stub_util.SEQUENTIAL):
    """Constructor.

    Initializes the SQLite database if necessary.

    Args:
      app_id: string
      datastore_file: string, path to sqlite database. Use None to create an
          in-memory database.
      require_indexes: bool, default False. If True, composite indexes must
          exist in index.yaml for queries that need them.
      verbose: bool, default False. If True, logs all select statements.
      service_name: Service name expected for all calls.
      trusted: bool, default False. If True, this stub allows an app to access
          the data of another app.
      consistency_policy: The consistency policy to use or None to use the
        default. Consistency policies can be found in
        datastore_stub_util.*ConsistencyPolicy
      root_path: string, the root path of the app.
      use_atexit: bool, indicates if the stub should save itself atexit.
      auto_id_policy: enum, datastore_stub_util.SEQUENTIAL or .SCATTERED
    """
    datastore_stub_util.BaseDatastore.__init__(self, require_indexes,
                                               consistency_policy,
                                               use_atexit and datastore_file,
                                               auto_id_policy)
    apiproxy_stub.APIProxyStub.__init__(self, service_name)
    datastore_stub_util.DatastoreStub.__init__(self, weakref.proxy(self),
                                               app_id, trusted, root_path)

    self.__datastore_file = datastore_file

    self.__verbose = verbose


    self.__id_map_sequential = {}
    self.__id_map_scattered = {}
    self.__id_counter_tables = {
        datastore_stub_util.SEQUENTIAL: ('IdSeq', self.__id_map_sequential),
        datastore_stub_util.SCATTERED: ('ScatteredIdCounters',
                                         self.__id_map_scattered),
        }
    self.__id_lock = threading.Lock()

    if self.__verbose:
      sql_conn = SQLiteConnectionWrapper
    else:
      sql_conn = sqlite3.Connection

    self.__connection = sqlite3.connect(
        self.__datastore_file or ':memory:',
        timeout=_MAX_TIMEOUT,
        check_same_thread=False,
        factory=sql_conn)



    self.__connection.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')


    self.__connection_lock = threading.RLock()


    self.__namespaces = set()


    self.__query_history = {}

    self._RegisterPseudoKind(KindPseudoKind())
    self._RegisterPseudoKind(PropertyPseudoKind())
    self._RegisterPseudoKind(NamespacePseudoKind())
    self._RegisterPseudoKind(datastore_stub_util.EntityGroupPseudoKind())

    try:
      self.__Init()
    except sqlite3.DatabaseError, e:
      raise apiproxy_errors.ApplicationError(datastore_pb.Error.INTERNAL_ERROR,
                                             self.READ_ERROR_MSG %
                                                 (self.__datastore_file, e))

  def __Init(self):



    self.__connection.execute('PRAGMA synchronous = OFF')


    self.__connection.executescript(_CORE_SCHEMA)
    self.__connection.commit()


    c = self.__connection.execute('SELECT app_id, name_space FROM Namespaces')
    self.__namespaces = set(c.fetchall())


    for app_ns in self.__namespaces:
      prefix = ('%s!%s' % app_ns).replace('"', '""')
      self.__connection.execute(
          'INSERT OR IGNORE INTO ScatteredIdCounters VALUES (?, ?)',
          (prefix, 1))
    self.__connection.commit()

    c = self.__connection.execute(
        'SELECT commit_timestamp FROM CommitTimestamps WHERE prefix = ""')
    row = c.fetchone()
    if row:
      self._commit_timestamp = row[0]



    c = self.__connection.execute('SELECT app_id, indexes FROM Apps')
    for _, index_proto in c.fetchall():
      if not index_proto:
        continue
      indexes = datastore_pb.CompositeIndices(index_proto)
      for index in indexes.index_list():
        self._SideLoadIndex(index)

  def Clear(self):
    """Clears the datastore."""
    conn = self._GetConnection()
    try:
      datastore_stub_util.BaseDatastore.Clear(self)
      datastore_stub_util.DatastoreStub.Clear(self)
      c = conn.execute(
          "SELECT tbl_name FROM sqlite_master WHERE type = 'table'")
      for row in c.fetchall():
        conn.execute('DROP TABLE "%s"' % row)
    finally:
      self._ReleaseConnection(conn)

    self.__namespaces = set()
    self.__id_map_sequential = {}
    self.__id_map_scattered = {}
    self.__Init()

  def Read(self):
    """Reads the datastore from disk.

    Noop for compatibility with file stub.
    """
    pass

  def Close(self):
    """Closes the SQLite connection and releases the files."""
    datastore_stub_util.BaseDatastore.Close(self)
    conn = self._GetConnection()
    conn.close()

  @staticmethod
  def __MakeParamList(size):
    """Returns a comma separated list of sqlite substitution parameters.

    Args:
      size: Number of parameters in returned list.
    Returns:
      A comma separated list of substitution parameters.
    """
    return ','.join('?' * size)

  @staticmethod
  def __GetEntityKind(key):
    """Returns the kind of the Entity or Key.

    It selects the kind of the last element of the entity_group element
    list, as it contains the most specific type of the key.

    Args:
      key: A Key or EntityProto

    Returns:
      The kind of the sent Key or Entity
    """
    if isinstance(key, entity_pb.EntityProto):
      key = key.key()
    return key.path().element_list()[-1].type()

  @staticmethod
  def __EncodeIndexPB(pb):
    """Encodes a protobuf using sortable_pb_encoder to preserve entity order.

    Using sortable_pb_encoder, encodes the protobuf, while using
    the ordering semantics for the datastore, and validating for the special
    case of uservalues ordering.

    Args:
      pb: An Entity protobuf.

    Returns:
      A buffer holding the encoded protobuf.
    """
    if isinstance(pb, entity_pb.PropertyValue) and pb.has_uservalue():

      userval = entity_pb.PropertyValue()
      userval.mutable_uservalue().set_email(pb.uservalue().email())
      userval.mutable_uservalue().set_auth_domain(pb.uservalue().auth_domain())
      userval.mutable_uservalue().set_gaiaid(0)
      pb = userval
    encoder = sortable_pb_encoder.Encoder()
    pb.Output(encoder)
    return buffer(encoder.buffer().tostring())

  @staticmethod
  def __AddQueryParam(query_params, param):
    """Adds a parameter to the query parameters."""
    query_params.append(param)
    return len(query_params)

  @staticmethod
  def _CreateFilterString(filter_list, params):
    """Transforms a filter list into an SQL WHERE clause.

    Args:
      filter_list: The list of (property, operator, value) filters
        to transform. A value_type of -1 indicates no value type comparison
        should be done.
      params: out: A list of parameters to pass to the query.
    Returns:
      An SQL 'where' clause.
    """
    clauses = []
    for prop, operator, value in filter_list:
      if operator == datastore_pb.Query_Filter.EXISTS:
        continue
      sql_op = _OPERATOR_MAP[operator]

      value_index = DatastoreSqliteStub.__AddQueryParam(params, value)
      clauses.append('%s %s :%d' % (prop, sql_op, value_index))

    filters = ' AND '.join(clauses)
    if filters:
      filters = 'WHERE ' + filters
    return filters

  @staticmethod
  def __CreateOrderString(order_list):
    """Returns an 'ORDER BY' clause from the given list of orders.

    Args:
      order_list: A list of (field, order) tuples.
    Returns:
      An SQL ORDER BY clause.
    """
    orders = ', '.join('%s %s' % (x[0], _ORDER_MAP[x[1]]) for x in order_list)
    if orders:
      orders = 'ORDER BY ' + orders
    return orders

  def _GetConnection(self):
    """Retrieves a connection to the SQLite DB.

    Returns:
      An SQLite connection object.
    """
    self.__connection_lock.acquire()
    return self.__connection

  def _ReleaseConnection(self, conn):
    """Releases a connection for use by other operations.

    If a transaction is supplied, no action is taken.

    Args:
      conn: An SQLite connection object.
    """
    conn.commit()
    self.__connection_lock.release()

  def __ConfigureNamespace(self, conn, prefix, app_id, name_space):
    """Ensures the relevant tables and indexes exist.

    Args:
      conn: An SQLite database connection.
      prefix: The namespace prefix to configure.
      app_id: The app ID.
      name_space: The per-app namespace name.
    """
    format_args = {'app_id': app_id, 'name_space': name_space, 'prefix': prefix}
    conn.executescript(_NAMESPACE_SCHEMA % format_args)
    conn.commit()

  def __WriteIndexData(self, conn, app):
    """Writes index data to disk.

    Args:
      conn: An SQLite connection.
      app: The app ID to write indexes for.
    """
    indices = datastore_pb.CompositeIndices()
    for index in self.GetIndexes(app, True, self._app_id):
      indices.index_list().append(index)




    conn.execute('UPDATE Apps SET indexes = ? WHERE app_id = ?',
                 (app, buffer(indices.Encode())))

  def _GetTablePrefix(self, data):
    """Returns the namespace prefix for a query.

    Args:
      data: An Entity, Key or Query PB, or an (app_id, ns) tuple.
    Returns:
      A valid table prefix
    """
    if isinstance(data, entity_pb.EntityProto):
      data = data.key()
    if not isinstance(data, tuple):
      data = (data.app(), data.name_space())
    prefix = ('%s!%s' % data).replace('"', '""')
    if data not in self.__namespaces:
      self.__namespaces.add(data)
      self.__ConfigureNamespace(self.__connection, prefix, *data)
    return prefix

  def __DeleteRows(self, conn, paths, table):
    """Deletes rows from a table.

    Args:
      conn: An SQLite connection.
      paths: Paths to delete.
      table: The table to delete from.
    Returns:
      The number of rows deleted.
    """
    c = conn.execute('DELETE FROM "%s" WHERE __path__ IN (%s)'
                     % (table, self.__MakeParamList(len(paths))),
                     paths)
    return c.rowcount

  def __DeleteEntityRows(self, conn, keys, table):
    """Deletes rows from the specified table that index the keys provided.

    Args:
      conn: A database connection.
      keys: A list of keys to delete index entries for.
      table: The table to delete from.
    Returns:
      The number of rows deleted.
    """
    keys = sorted((x.app(), x.name_space(), x) for x in keys)
    for (app_id, ns), group in itertools.groupby(keys, lambda x: x[:2]):
      path_strings = [self.__EncodeIndexPB(x[2].path()) for x in group]
      prefix = self._GetTablePrefix((app_id, ns))
      return self.__DeleteRows(conn, path_strings, '%s!%s' % (prefix, table))

  def __DeleteIndexEntries(self, conn, keys):
    """Deletes entities from the index.

    Args:
      conn: An SQLite connection.
      keys: A list of keys to delete.
    """
    self.__DeleteEntityRows(conn, keys, 'EntitiesByProperty')

  def __InsertEntities(self, conn, entities):
    """Inserts or updates entities in the DB.

    Args:
      conn: A database connection.
      entities: A list of entities to store.
    """

    def RowGenerator(entities):
      for unused_prefix, e in entities:
        yield (self.__EncodeIndexPB(e.key().path()),
               self.__GetEntityKind(e),
               buffer(e.Encode()))

    entities = sorted((self._GetTablePrefix(x), x) for x in entities)
    for prefix, group in itertools.groupby(entities, lambda x: x[0]):
      conn.executemany(
          'INSERT OR REPLACE INTO "%s!Entities" VALUES (?, ?, ?)' % prefix,
          RowGenerator(group))

  def __InsertIndexEntries(self, conn, entities):
    """Inserts index entries for the supplied entities.

    Args:
      conn: A database connection.
      entities: A list of entities to create index entries for.
    """

    def RowGenerator(entities):
      for unused_prefix, e in entities:
        for p in e.property_list():
          yield (self.__GetEntityKind(e),
                 p.name(),
                 self.__EncodeIndexPB(p.value()),
                 self.__EncodeIndexPB(e.key().path()))
    entities = sorted((self._GetTablePrefix(x), x) for x in entities)
    for prefix, group in itertools.groupby(entities, lambda x: x[0]):
      conn.executemany(
          'INSERT INTO "%s!EntitiesByProperty" VALUES (?, ?, ?, ?)' % prefix,
          RowGenerator(group))

  def __PersistCommitTimestamp(self, conn, timestamp):
    conn.execute('INSERT OR REPLACE INTO "CommitTimestamps" VALUES ("", ?)',
                 (timestamp,))

  def MakeSyncCall(self, service, call, request, response, request_id=None):
    """The main RPC entry point. service must be 'datastore_v3'."""
    self.AssertPbIsInitialized(request)
    try:
      apiproxy_stub.APIProxyStub.MakeSyncCall(self, service, call, request,
                                              response, request_id)
    except sqlite3.OperationalError, e:
      raise apiproxy_errors.ApplicationError(datastore_pb.Error.INTERNAL_ERROR,
                                             e.args[0])
    self.AssertPbIsInitialized(response)

  def AssertPbIsInitialized(self, pb):
    """Raises an exception if the given PB is not initialized and valid."""
    explanation = []
    assert pb.IsInitialized(explanation), explanation

    pb.Encode()

  def __GenerateFilterInfo(self, filters, query):
    """Transform a list of filters into a more usable form.

    Args:
      filters: A list of filter PBs.
      query: The query to generate filter info for.
    Returns:
      A dict mapping property names to lists of (op, value) tuples.
    """
    filter_info = {}
    for filt in filters:
      assert filt.property_size() == 1
      prop = filt.property(0)
      value = prop.value()
      if prop.name() == '__key__':


        value = ReferencePropertyToReference(value.referencevalue())
        assert value.app() == query.app()
        assert value.name_space() == query.name_space()
        value = value.path()
      filter_info.setdefault(prop.name(), []).append(
          (filt.op(), self.__EncodeIndexPB(value)))
    return filter_info

  def __GenerateOrderInfo(self, orders):
    """Transform a list of orders into a more usable form.

    Args:
      orders: A list of order PBs.
    Returns:
      A list of (property, direction) tuples.
    """
    orders = [(order.property(), order.direction()) for order in orders]
    if orders and orders[-1] == ('__key__', datastore_pb.Query_Order.ASCENDING):

      orders.pop()
    return orders

  def __GetPrefixRange(self, prefix):
    """Returns a (min, max) range that encompasses the given prefix.

    Args:
      prefix: A string prefix to filter for. Must be a PB encodable using
        __EncodeIndexPB.
    Returns:
      (min, max): Start and end string values to filter on.
    """
    ancestor_min = self.__EncodeIndexPB(prefix)


    ancestor_max = buffer(str(ancestor_min) + '\xfb\xff\xff\xff\x89')
    return ancestor_min, ancestor_max

  def  __KindQuery(self, query, filter_info, order_info):
    """Performs kind only, kind and ancestor, and ancestor only queries."""

    if not (set(filter_info.keys()) |
            set(x[0] for x in order_info)).issubset(['__key__']):
      return None

    if len(order_info) > 1:
      return None

    filters = []

    filters.extend(('__path__', op, value) for op, value
                   in filter_info.get('__key__', []))
    if query.has_kind():

      filters.append(('kind', datastore_pb.Query_Filter.EQUAL, query.kind()))

    if query.has_ancestor():
      amin, amax = self.__GetPrefixRange(query.ancestor().path())
      filters.append(('__path__',
                      datastore_pb.Query_Filter.GREATER_THAN_OR_EQUAL, amin))
      filters.append(('__path__', datastore_pb.Query_Filter.LESS_THAN, amax))

    if order_info:
      orders = [('__path__', order_info[0][1])]
    else:
      orders = [('__path__', datastore_pb.Query_Order.ASCENDING)]

    params = []
    query = ('SELECT Entities.__path__, Entities.entity '
             'FROM "%s!Entities" AS Entities %s %s' % (
                 self._GetTablePrefix(query),
                 self._CreateFilterString(filters, params),
                 self.__CreateOrderString(orders)))
    return query, params

  def __SinglePropertyQuery(self, query, filter_info, order_info):
    """Performs queries satisfiable by the EntitiesByProperty table."""

    property_names = set(filter_info.keys())
    property_names.update(x[0] for x in order_info)
    if len(property_names) != 1:
      return None

    property_name = property_names.pop()
    filter_ops = filter_info.get(property_name, [])


    if len([1 for o, _ in filter_ops
            if o == datastore_pb.Query_Filter.EQUAL]) > 1:
      return None


    if len(order_info) > 1 or (order_info and order_info[0][0] == '__key__'):
      return None


    if query.has_ancestor():
      return None


    if not query.has_kind():
      return None

    prefix = self._GetTablePrefix(query)
    filters = []
    filters.append(('EntitiesByProperty.kind',
                    datastore_pb.Query_Filter.EQUAL, query.kind()))
    filters.append(('name', datastore_pb.Query_Filter.EQUAL, property_name))
    for op, value in filter_ops:
      if property_name == '__key__':
        filters.append(('EntitiesByProperty.__path__', op, value))
      else:
        filters.append(('value', op, value))

    orders = [('EntitiesByProperty.kind', datastore_pb.Query_Order.ASCENDING),
              ('name', datastore_pb.Query_Order.ASCENDING)]
    if order_info:
      orders.append(('value', order_info[0][1]))
    else:
      orders.append(('value', datastore_pb.Query_Order.ASCENDING))
    orders.append(('EntitiesByProperty.__path__',
                   datastore_pb.Query_Order.ASCENDING))

    params = []
    format_args = (
        prefix,
        prefix,
        self._CreateFilterString(filters, params),
        self.__CreateOrderString(orders))
    query = ('SELECT Entities.__path__, Entities.entity, '
             'EntitiesByProperty.name, EntitiesByProperty.value '
             'FROM "%s!EntitiesByProperty" AS EntitiesByProperty INNER JOIN '
             '"%s!Entities" AS Entities USING (__path__) %s %s' % format_args)
    return query, params

  def __StarSchemaQueryPlan(self, query, filter_info, order_info):
    """Executes a query using a 'star schema' based on EntitiesByProperty.

    A 'star schema' is a join between an objects table (Entities) and multiple
    instances of a facts table (EntitiesByProperty). Ideally, this will result
    in a merge join if the only filters are inequalities and the sort orders
    match those in the index for the facts table; otherwise, the DB will do its
    best to satisfy the query efficiently.

    Args:
      query: The datastore_pb.Query PB.
      filter_info: A dict mapping properties filtered on to (op, value) tuples.
      order_info: A list of (property, direction) tuples.
    Returns:
      (query, params): An SQL query string and list of parameters for it.
    """
    filter_sets = []
    for name, filter_ops in filter_info.items():

      filter_sets.extend((name, [x]) for x in filter_ops
                         if x[0] == datastore_pb.Query_Filter.EQUAL)

      ineq_ops = [x for x in filter_ops
                  if x[0] != datastore_pb.Query_Filter.EQUAL]
      if ineq_ops:
        filter_sets.append((name, ineq_ops))


    for prop, _ in order_info:
      if prop == '__key__':
        continue
      if prop not in filter_info:
        filter_sets.append((prop, []))

    prefix = self._GetTablePrefix(query)

    joins = []
    filters = []
    join_name_map = {}
    for name, filter_ops in filter_sets:
      if name == '__key__':
        for op, value in filter_ops:
          filters.append(('Entities.__path__', op, buffer(value)))
      else:
        join_name = 'ebp_%d' % (len(joins),)
        join_name_map.setdefault(name, join_name)
        joins.append(
            'INNER JOIN "%s!EntitiesByProperty" AS %s '
            'ON Entities.__path__ = %s.__path__'
            % (prefix, join_name, join_name))
        filters.append(('%s.kind' % join_name, datastore_pb.Query_Filter.EQUAL,
                        query.kind()))
        filters.append(('%s.name' % join_name, datastore_pb.Query_Filter.EQUAL,
                        name))
        for op, value in filter_ops:
          filters.append(('%s.value' % join_name, op, buffer(value)))

        if query.has_ancestor():
          amin, amax = self.__GetPrefixRange(query.ancestor().path())
          filters.append(('%s.__path__' % join_name,
                          datastore_pb.Query_Filter.GREATER_THAN_OR_EQUAL,
                          amin))
          filters.append(('%s.__path__' % join_name,
                          datastore_pb.Query_Filter.LESS_THAN, amax))

    orders = []
    for prop, order in order_info:
      if prop == '__key__':
        orders.append(('Entities.__path__', order))
      else:
        prop = '%s.value' % (join_name_map[prop],)
        orders.append((prop, order))
    if not order_info or order_info[-1][0] != '__key__':
      orders.append(('Entities.__path__', datastore_pb.Query_Order.ASCENDING))

    select_arg = 'Entities.__path__, Entities.entity '

    if query.property_name_list():
      for value_i in join_name_map.values():
        select_arg += ', %s.name, %s.value' % (value_i, value_i)

    params = []
    format_args = (
        select_arg,
        prefix,
        ' '.join(joins),
        self._CreateFilterString(filters, params),
        self.__CreateOrderString(orders))

    query = ('SELECT %s FROM "%s!Entities" AS Entities %s %s %s' % format_args)

    logging.debug(query)
    return query, params

  def __MergeJoinQuery(self, query, filter_info, order_info):

    if order_info:
      return None

    if query.has_ancestor():
      return None

    if not query.has_kind():
      return None

    for filter_ops in filter_info.values():
      for op, _ in filter_ops:
        if op != datastore_pb.Query_Filter.EQUAL:
          return None

    return self.__StarSchemaQueryPlan(query, filter_info, order_info)

  def __LastResortQuery(self, query, filter_info, order_info):
    """Last resort query plan that executes queries requring composite indexes.

    Args:
      query: The datastore_pb.Query PB.
      filter_info: A dict mapping properties filtered on to (op, value) tuples.
      order_info: A list of (property, direction) tuples.
    Returns:
      (query, params): An SQL query string and list of parameters for it.
    """
    return self.__StarSchemaQueryPlan(query, filter_info, order_info)

  _QUERY_STRATEGIES = [
      __KindQuery,
      __SinglePropertyQuery,
      __MergeJoinQuery,
      __LastResortQuery,
  ]



  def _Put(self, record, insert):
    conn = self._GetConnection()
    try:
      self.__DeleteIndexEntries(conn, [record.entity.key()])
      record = datastore_stub_util.StoreRecord(record)
      entity_stored = datastore_stub_util._ToStorageEntity(record)
      self.__InsertEntities(conn, [entity_stored])

      self.__InsertIndexEntries(conn, [record.entity])
      self.__PersistCommitTimestamp(conn, self._GetReadTimestamp())
    finally:
      self._ReleaseConnection(conn)

  def _Get(self, key):
    conn = self._GetConnection()
    try:
      prefix = self._GetTablePrefix(key)
      c = conn.execute(
          'SELECT entity FROM "%s!Entities" WHERE __path__ = ?' % (prefix,),
          (self.__EncodeIndexPB(key.path()),))
      row = c.fetchone()
      if row:
        entity = entity_pb.EntityProto()
        entity.ParseFromString(row[0])
        record = datastore_stub_util._FromStorageEntity(entity)
        return datastore_stub_util.LoadRecord(record)
    finally:
      self._ReleaseConnection(conn)

  def _Delete(self, key):
    conn = self._GetConnection()
    try:
      self.__DeleteIndexEntries(conn, [key])
      self.__DeleteEntityRows(conn, [key], 'Entities')
      self.__PersistCommitTimestamp(conn, self._GetReadTimestamp())
    finally:
      self._ReleaseConnection(conn)

  def _GetEntitiesInEntityGroup(self, entity_group):
    query = datastore_pb.Query()
    query.set_app(entity_group.app())
    if entity_group.name_space():
      query.set_name_space(entity_group.name_space())
    query.mutable_ancestor().CopyFrom(entity_group)

    filter_info = self.__GenerateFilterInfo(query.filter_list(), query)
    order_info = self.__GenerateOrderInfo(query.order_list())
    sql_stmt, params = self.__KindQuery(query, filter_info, order_info)






    conn = self._GetConnection()
    try:
      db_cursor = conn.execute(sql_stmt, params)
      entities = {}
      for row in db_cursor.fetchall():
        entity = entity_pb.EntityProto(row[1])
        key = datastore_types.ReferenceToKeyValue(entity.key())
        entities[key] = datastore_stub_util._FromStorageEntity(entity)
      return entities
    finally:

      self._ReleaseConnection(conn)

  def _GetQueryCursor(self, query, filters, orders, index_list):
    """Returns a query cursor for the provided query.

    Args:
      query: The datastore_pb.Query to run.
      filters: A list of filters that override the ones found on query.
      orders: A list of orders that override the ones found on query.
      index_list: A list of indexes used by the query.

    Returns:
      A QueryCursor object.
    """
    if query.has_kind() and query.kind() in self._pseudo_kinds:

      datastore_stub_util.NormalizeCursors(query,
                                           datastore_pb.Query_Order.ASCENDING)
      cursor = self._pseudo_kinds[query.kind()].Query(query, filters, orders)
      datastore_stub_util.Check(cursor,
                                'Could not create query for pseudo-kind')
    else:
      orders = datastore_stub_util._GuessOrders(filters, orders)


      datastore_stub_util.NormalizeCursors(query, orders[0].direction())
      filter_info = self.__GenerateFilterInfo(filters, query)
      order_info = self.__GenerateOrderInfo(orders)

      for strategy in DatastoreSqliteStub._QUERY_STRATEGIES:
        result = strategy(self, query, filter_info, order_info)
        if result:
          break
      else:
        raise apiproxy_errors.ApplicationError(
            datastore_pb.Error.BAD_REQUEST,
            'No strategy found to satisfy query.')

      sql_stmt, params = result

      conn = self._GetConnection()
      try:
        if query.property_name_list():
          db_cursor = _ProjectionPartialEntityGenerator(
              conn.execute(sql_stmt, params))
        else:
          db_cursor = _DedupingEntityGenerator(conn.execute(sql_stmt, params))
        dsquery = datastore_stub_util._MakeQuery(query, filters, orders)

        cursor = datastore_stub_util.ListCursor(query, dsquery, orders,
                                                index_list, list(db_cursor))
      finally:
        self._ReleaseConnection(conn)
    return cursor

  def __AllocateIdsFromBlock(self, conn, prefix, size, id_map, table):
    datastore_stub_util.Check(size > 0, 'Size must be greater than 0.')
    next_id, block_size = id_map.get(prefix, (0, 0))
    if not block_size:


      block_size = (size / 1000 + 1) * 1000
      c = conn.execute('SELECT next_id FROM %s WHERE prefix = ? LIMIT 1'
                       % table, (prefix,))
      next_id = c.fetchone()[0]
      c = conn.execute('UPDATE %s SET next_id = next_id + ? WHERE prefix = ?'
                       % table, (block_size, prefix))
      assert c.rowcount == 1

    if size > block_size:

      c = conn.execute('SELECT next_id FROM %s WHERE prefix = ? LIMIT 1'
                       % table, (prefix,))
      start = c.fetchone()[0]
      c = conn.execute('UPDATE %s SET next_id = next_id + ? WHERE prefix = ?'
                       % table, (size, prefix))
      assert c.rowcount == 1
    else:

      start = next_id;
      next_id += size
      block_size -= size
      id_map[prefix] = (next_id, block_size)
    end = start + size - 1
    return start, end

  def __AdvanceIdCounter(self, conn, prefix, max_id, table):
    datastore_stub_util.Check(max_id >=0,
                              'Max must be greater than or equal to 0.')
    c = conn.execute('SELECT next_id FROM %s WHERE prefix = ? LIMIT 1'
                     % table, (prefix,))
    start = c.fetchone()[0]
    if max_id >= start:
      c = conn.execute('UPDATE %s SET next_id = ? WHERE prefix = ?' % table,
                       (max_id + 1, prefix))
      assert c.rowcount == 1
    end = max(max_id, start - 1)
    return start, end

  def _AllocateSequentialIds(self, reference, size=1, max_id=None):
    conn = self._GetConnection()
    try:
      datastore_stub_util.CheckAppId(self._trusted, self._app_id,
                                     reference.app())
      datastore_stub_util.Check(not (size and max_id),
                                'Both size and max cannot be set.')

      prefix = self._GetTablePrefix(reference)



      if size:
        start, end = self.__AllocateIdsFromBlock(conn, prefix, size,
                                                 self.__id_map_sequential,
                                                 'IdSeq')
      else:
        start, end = self.__AdvanceIdCounter(conn, prefix, max_id, 'IdSeq')
      return long(start), long(end)
    finally:
      self._ReleaseConnection(conn)

  def _AllocateIds(self, references):
    conn = self._GetConnection()
    try:
      full_keys = []
      for key in references:
        datastore_stub_util.CheckAppId(self._trusted, self._app_id, key.app())
        prefix = self._GetTablePrefix(key)
        last_element = key.path().element_list()[-1]

        if last_element.id() or last_element.has_name():
          for el in key.path().element_list():
            if el.id():
              count, id_space = datastore_stub_util.IdToCounter(el.id())
              table, _ = self.__id_counter_tables[id_space]
              self.__AdvanceIdCounter(conn, prefix, count, table)

        else:
          count, _ = self.__AllocateIdsFromBlock(conn, prefix, 1,
                                                 self.__id_map_scattered,
                                                 'ScatteredIdCounters')
          last_element.set_id(datastore_stub_util.ToScatteredId(count))
          full_keys.append(key)
      return full_keys
    finally:
      self._ReleaseConnection(conn)

  def _OnIndexChange(self, app_id):
    conn = self._GetConnection()
    try:
      self.__WriteIndexData(conn, app_id)
    finally:
      self._ReleaseConnection(conn)
