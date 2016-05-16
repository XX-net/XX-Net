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







"""Key range representation and splitting."""



import os


try:
  import json as simplejson
except ImportError:
  try:
    import simplejson
  except ImportError:
    simplejson = None

from google.appengine.api import datastore
from google.appengine.api import namespace_manager
from google.appengine.datastore import datastore_pb
from google.appengine.ext import db

try:
  from google.appengine.ext import ndb
except ImportError:
  ndb = None
# It is acceptable to set key_range.ndb to the ndb module,
# imported through some other way (e.g. from the app dir).


class Error(Exception):
  """Base class for exceptions in this module."""


class KeyRangeError(Error):
  """Error while trying to generate a KeyRange."""


class SimplejsonUnavailableError(Error):
  """Error using json functionality with unavailable json and simplejson."""


def _IsNdbQuery(query):
  return ndb is not None and isinstance(query, ndb.Query)


class KeyRange(object):
  """Represents a range of keys in the datastore.

  A KeyRange object represents a key range
    (key_start, include_start, key_end, include_end)
  and a scan direction (KeyRange.DESC or KeyRange.ASC).
  """


  DESC = "DESC"
  ASC = "ASC"

  def __init__(self,
               key_start=None,
               key_end=None,
               direction=None,
               include_start=True,
               include_end=True,
               namespace=None,
               _app=None):
    """Initialize a KeyRange object.

    Args:
      key_start: The starting key for this range (db.Key or ndb.Key).
      key_end: The ending key for this range (db.Key or ndb.Key).
      direction: The direction of the query for this range.
      include_start: Whether the start key should be included in the range.
      include_end: Whether the end key should be included in the range.
      namespace: The namespace for this range. If None then the current
          namespace is used.

    NOTE: If NDB keys are passed in, they are converted to db.Key
    instances before being stored.
    """




    if direction is None:
      direction = KeyRange.ASC
    assert direction in (KeyRange.ASC, KeyRange.DESC)
    self.direction = direction


    if ndb is not None:
      if isinstance(key_start, ndb.Key):
        key_start = key_start.to_old_key()
      if isinstance(key_end, ndb.Key):
        key_end = key_end.to_old_key()
    self.key_start = key_start
    self.key_end = key_end
    self.include_start = include_start
    self.include_end = include_end
    if namespace is not None:
      self.namespace = namespace
    else:
      self.namespace = namespace_manager.get_namespace()
    self._app = _app

  def __str__(self):
    if self.include_start:
      left_side = "["
    else:
      left_side = "("
    if self.include_end:
      right_side = "]"
    else:
      right_side = ")"
    return "%s%s%r to %r%s" % (self.direction, left_side, self.key_start,
                               self.key_end, right_side)

  def __repr__(self):
    return ("key_range.KeyRange(key_start=%r,key_end=%r,direction=%r,"
            "include_start=%r,include_end=%r, namespace=%r)") % (
                self.key_start,
                self.key_end,
                self.direction,
                self.include_start,
                self.include_end,
                self.namespace)

  def advance(self, key):
    """Updates the start of the range immediately past the specified key.

    Args:
      key: A db.Key or ndb.Key.
    """
    self.include_start = False
    if ndb is not None:
      if isinstance(key, ndb.Key):
        key = key.to_old_key()
    self.key_start = key

  def filter_query(self, query, filters=None):
    """Add query filter to restrict to this key range.

    Args:
      query: A db.Query or ndb.Query instance.
      filters: optional list of filters to apply to the query. Each filter is
        a tuple: (<property_name_as_str>, <query_operation_as_str>, <value>).
        User filters are applied first.

    Returns:
      The input query restricted to this key range.
    """
    if ndb is not None:
      if _IsNdbQuery(query):
        return self.filter_ndb_query(query, filters=filters)
    assert not _IsNdbQuery(query)


    if filters:
      for f in filters:
        query.filter("%s %s" % (f[0], f[1]), f[2])

    if self.include_start:
      start_comparator = ">="
    else:
      start_comparator = ">"
    if self.include_end:
      end_comparator = "<="
    else:
      end_comparator = "<"
    if self.key_start:
      query.filter("__key__ %s" % start_comparator, self.key_start)
    if self.key_end:
      query.filter("__key__ %s" % end_comparator, self.key_end)
    return query

  def filter_ndb_query(self, query, filters=None):
    """Add query filter to restrict to this key range.

    Args:
      query: An ndb.Query instance.
      filters: optional list of filters to apply to the query. Each filter is
        a tuple: (<property_name_as_str>, <query_operation_as_str>, <value>).
        User filters are applied first.

    Returns:
      The input query restricted to this key range.
    """
    assert _IsNdbQuery(query)


    if filters:
      for f in filters:
        query = query.filter(ndb.FilterNode(*f))

    if self.include_start:
      start_comparator = ">="
    else:
      start_comparator = ">"
    if self.include_end:
      end_comparator = "<="
    else:
      end_comparator = "<"
    if self.key_start:
      query = query.filter(ndb.FilterNode("__key__",
                                          start_comparator,
                                          self.key_start))
    if self.key_end:
      query = query.filter(ndb.FilterNode("__key__",
                                          end_comparator,
                                          self.key_end))
    return query

  def filter_datastore_query(self, query, filters=None):
    """Add query filter to restrict to this key range.

    Args:
      query: A datastore.Query instance.
      filters: optional list of filters to apply to the query. Each filter is
        a tuple: (<property_name_as_str>, <query_operation_as_str>, <value>).
        User filters are applied first.

    Returns:
      The input query restricted to this key range.
    """
    assert isinstance(query, datastore.Query)

    if filters:
      for f in filters:
        query.update({"%s %s" % (f[0], f[1]): f[2]})

    if self.include_start:
      start_comparator = ">="
    else:
      start_comparator = ">"
    if self.include_end:
      end_comparator = "<="
    else:
      end_comparator = "<"
    if self.key_start:
      query.update({"__key__ %s" % start_comparator: self.key_start})
    if self.key_end:
      query.update({"__key__ %s" % end_comparator: self.key_end})
    return query

  def __get_direction(self, asc, desc):
    """Check that self.direction is in (KeyRange.ASC, KeyRange.DESC).

    Args:
      asc: Argument to return if self.direction is KeyRange.ASC
      desc: Argument to return if self.direction is KeyRange.DESC

    Returns:
      asc or desc appropriately

    Raises:
      KeyRangeError: if self.direction is not in (KeyRange.ASC, KeyRange.DESC).
    """
    if self.direction == KeyRange.ASC:
      return asc
    elif self.direction == KeyRange.DESC:
      return desc
    else:
      raise KeyRangeError("KeyRange direction unexpected: %s", self.direction)

  def make_directed_query(self, kind_class, keys_only=False):
    """Construct a query for this key range, including the scan direction.

    Args:
      kind_class: A kind implementation class (a subclass of either
        db.Model or ndb.Model).
      keys_only: bool, default False, use keys_only on Query?

    Returns:
      A db.Query or ndb.Query instance (corresponding to kind_class).

    Raises:
      KeyRangeError: if self.direction is not in (KeyRange.ASC, KeyRange.DESC).
    """
    if ndb is not None:
      if issubclass(kind_class, ndb.Model):
        return self.make_directed_ndb_query(kind_class, keys_only=keys_only)
    assert self._app is None, '_app is not supported for db.Query'
    direction = self.__get_direction("", "-")
    query = db.Query(kind_class, namespace=self.namespace, keys_only=keys_only)
    query.order("%s__key__" % direction)

    query = self.filter_query(query)
    return query

  def make_directed_ndb_query(self, kind_class, keys_only=False):
    """Construct an NDB query for this key range, including the scan direction.

    Args:
      kind_class: An ndb.Model subclass.
      keys_only: bool, default False, use keys_only on Query?

    Returns:
      An ndb.Query instance.

    Raises:
      KeyRangeError: if self.direction is not in (KeyRange.ASC, KeyRange.DESC).
    """
    assert issubclass(kind_class, ndb.Model)
    if keys_only:
      default_options = ndb.QueryOptions(keys_only=True)
    else:
      default_options = None
    query = kind_class.query(app=self._app,
                             namespace=self.namespace,
                             default_options=default_options)
    query = self.filter_ndb_query(query)
    if self.__get_direction(True, False):
      query = query.order(kind_class._key)
    else:
      query = query.order(-kind_class._key)
    return query

  def make_directed_datastore_query(self, kind, keys_only=False):
    """Construct a query for this key range, including the scan direction.

    Args:
      kind: A string.
      keys_only: bool, default False, use keys_only on Query?

    Returns:
      A datastore.Query instance.

    Raises:
      KeyRangeError: if self.direction is not in (KeyRange.ASC, KeyRange.DESC).
    """
    direction = self.__get_direction(datastore.Query.ASCENDING,
                                     datastore.Query.DESCENDING)
    query = datastore.Query(kind, _app=self._app, keys_only=keys_only)
    query.Order(("__key__", direction))

    query = self.filter_datastore_query(query)
    return query

  def make_ascending_query(self, kind_class, keys_only=False, filters=None):
    """Construct a query for this key range without setting the scan direction.

    Args:
      kind_class: A kind implementation class (a subclass of either
        db.Model or ndb.Model).
      keys_only: bool, default False, query only for keys.
      filters: optional list of filters to apply to the query. Each filter is
        a tuple: (<property_name_as_str>, <query_operation_as_str>, <value>).
        User filters are applied first.

    Returns:
      A db.Query or ndb.Query instance (corresponding to kind_class).
    """
    if ndb is not None:
      if issubclass(kind_class, ndb.Model):
        return self.make_ascending_ndb_query(
            kind_class, keys_only=keys_only, filters=filters)
    assert self._app is None, '_app is not supported for db.Query'
    query = db.Query(kind_class, namespace=self.namespace, keys_only=keys_only)
    query.order("__key__")

    query = self.filter_query(query, filters=filters)
    return query

  def make_ascending_ndb_query(self, kind_class, keys_only=False, filters=None):
    """Construct an NDB query for this key range, without the scan direction.

    Args:
      kind_class: An ndb.Model subclass.
      keys_only: bool, default False, query only for keys.

    Returns:
      An ndb.Query instance.
    """
    assert issubclass(kind_class, ndb.Model)
    if keys_only:
      default_options = ndb.QueryOptions(keys_only=True)
    else:
      default_options = None
    query = kind_class.query(app=self._app,
                             namespace=self.namespace,
                             default_options=default_options)
    query = self.filter_ndb_query(query, filters=filters)
    query = query.order(kind_class._key)
    return query

  def make_ascending_datastore_query(self, kind, keys_only=False, filters=None):
    """Construct a query for this key range without setting the scan direction.

    Args:
      kind: A string.
      keys_only: bool, default False, use keys_only on Query?
      filters: optional list of filters to apply to the query. Each filter is
        a tuple: (<property_name_as_str>, <query_operation_as_str>, <value>).
        User filters are applied first.

    Returns:
      A datastore.Query instance.
    """
    query = datastore.Query(kind,
                            namespace=self.namespace,
                            _app=self._app,
                            keys_only=keys_only)
    query.Order(("__key__", datastore.Query.ASCENDING))

    query = self.filter_datastore_query(query, filters=filters)
    return query

  def split_range(self, batch_size=0):
    """Split this key range into a list of at most two ranges.

    This method attempts to split the key range approximately in half.
    Numeric ranges are split in the middle into two equal ranges and
    string ranges are split lexicographically in the middle.  If the
    key range is smaller than batch_size it is left unsplit.

    Note that splitting is done without knowledge of the distribution
    of actual entities in the key range, so there is no guarantee (nor
    any particular reason to believe) that the entities of the range
    are evenly split.

    Args:
      batch_size: The maximum size of a key range that should not be split.

    Returns:
      A list of one or two key ranges covering the same space as this range.
    """
    key_start = self.key_start
    key_end = self.key_end
    include_start = self.include_start
    include_end = self.include_end

    key_pairs = []
    if not key_start:
      key_pairs.append((key_start, include_start, key_end, include_end,
                        KeyRange.ASC))
    elif not key_end:
      key_pairs.append((key_start, include_start, key_end, include_end,
                        KeyRange.DESC))
    else:
      key_split = KeyRange.split_keys(key_start, key_end, batch_size)
      first_include_end = True

      if key_split == key_start:
        first_include_end = first_include_end and include_start

      key_pairs.append((key_start, include_start,
                        key_split, first_include_end,
                        KeyRange.DESC))

      second_include_end = include_end

      if key_split == key_end:
        second_include_end = False
      key_pairs.append((key_split, False,
                        key_end, second_include_end,
                        KeyRange.ASC))

    ranges = [KeyRange(key_start=start,
                       include_start=include_start,
                       key_end=end,
                       include_end=include_end,
                       direction=direction,
                       namespace=self.namespace,
                       _app=self._app)
              for (start, include_start, end, include_end, direction)
              in key_pairs]

    return ranges

  def __hash__(self):
    raise TypeError('KeyRange is unhashable')

  def __cmp__(self, other):
    """Compare two key ranges.

    Key ranges with a value of None for key_start or key_end, are always
    considered to have include_start=False or include_end=False, respectively,
    when comparing.  Since None indicates an unbounded side of the range,
    the include specifier is meaningless.  The ordering generated is total
    but somewhat arbitrary.

    Args:
      other: An object to compare to this one.

    Returns:
      -1: if this key range is less than other.
      0:  if this key range is equal to other.
      1: if this key range is greater than other.
    """
    if not isinstance(other, KeyRange):
      return 1

    self_list = [self.key_start, self.key_end, self.direction,
                 self.include_start, self.include_end, self._app,
                 self.namespace]
    if not self.key_start:
      self_list[3] = False
    if not self.key_end:
      self_list[4] = False

    other_list = [other.key_start,
                  other.key_end,
                  other.direction,
                  other.include_start,
                  other.include_end,
                  other._app,
                  other.namespace]
    if not other.key_start:
      other_list[3] = False
    if not other.key_end:
      other_list[4] = False

    return cmp(self_list, other_list)

  @staticmethod
  def bisect_string_range(start, end):
    """Returns a string that is approximately in the middle of the range.

    (start, end) is treated as a string range, and it is assumed
    start <= end in the usual lexicographic string ordering. The output key
    mid is guaranteed to satisfy start <= mid <= end.

    The method proceeds by comparing initial characters of start and
    end.  When the characters are equal, they are appended to the mid
    string.  In the first place that the characters differ, the
    difference characters are averaged and this average is appended to
    the mid string.  If averaging resulted in rounding down, and
    additional character is added to the mid string to make up for the
    rounding down.  This extra step is necessary for correctness in
    the case that the average of the two characters is equal to the
    character in the start string.

    This method makes the assumption that most keys are ascii and it
    attempts to perform splitting within the ascii range when that
    results in a valid split.

    Args:
      start: A string.
      end: A string such that start <= end.

    Returns:
      A string mid such that start <= mid <= end.
    """
    if start == end:
      return start
    start += "\0"
    end += "\0"
    midpoint = []


    expected_max = 127
    for i in xrange(min(len(start), len(end))):
      if start[i] == end[i]:
        midpoint.append(start[i])
      else:
        ord_sum = ord(start[i]) + ord(end[i])
        midpoint.append(unichr(ord_sum / 2))
        if ord_sum % 2:
          if len(start) > i + 1:
            ord_start = ord(start[i+1])
          else:
            ord_start = 0
          if ord_start < expected_max:


            ord_split = (expected_max + ord_start) / 2
          else:

            ord_split = (0xFFFF + ord_start) / 2
          midpoint.append(unichr(ord_split))
        break
    return "".join(midpoint)

  @staticmethod
  def split_keys(key_start, key_end, batch_size):
    """Return a key that is between key_start and key_end inclusive.

    This method compares components of the ancestor paths of key_start
    and key_end.  The first place in the path that differs is
    approximately split in half.  If the kind components differ, a new
    non-existent kind halfway between the two is used to split the
    space. If the id_or_name components differ, then a new id_or_name
    that is halfway between the two is selected.  If the lower
    id_or_name is numeric and the upper id_or_name is a string, then
    the minumum string key u'\0' is used as the split id_or_name.  The
    key that is returned is the shared portion of the ancestor path
    followed by the generated split component.

    Args:
      key_start: A db.Key or ndb.Key instance for the lower end of a range.
      key_end: A db.Key or ndb.Key instance for the upper end of a range.
      batch_size: The maximum size of a range that should not be split.

    Returns:
      A db.Key instance, k, such that key_start <= k <= key_end.

    NOTE: Even though ndb.Key instances are accepted as arguments,
    the return value is always a db.Key instance.
    """
    if ndb is not None:


      if isinstance(key_start, ndb.Key):
        key_start = key_start.to_old_key()
      if isinstance(key_end, ndb.Key):
        key_end = key_end.to_old_key()
    assert key_start.app() == key_end.app()
    assert key_start.namespace() == key_end.namespace()
    path1 = key_start.to_path()
    path2 = key_end.to_path()
    len1 = len(path1)
    len2 = len(path2)
    assert len1 % 2 == 0
    assert len2 % 2 == 0
    out_path = []
    min_path_len = min(len1, len2) / 2
    for i in xrange(min_path_len):
      kind1 = path1[2*i]
      kind2 = path2[2*i]

      if kind1 != kind2:
        split_kind = KeyRange.bisect_string_range(kind1, kind2)
        out_path.append(split_kind)
        out_path.append(unichr(0))
        break




      last = (len1 == len2 == 2*(i + 1))

      id_or_name1 = path1[2*i + 1]
      id_or_name2 = path2[2*i + 1]
      id_or_name_split = KeyRange._split_id_or_name(
          id_or_name1, id_or_name2, batch_size, last)
      if id_or_name1 == id_or_name_split:
        out_path.append(kind1)
        out_path.append(id_or_name1)
      else:
        out_path.append(kind1)
        out_path.append(id_or_name_split)
        break

    return db.Key.from_path(
        *out_path,
        **{"_app": key_start.app(), "namespace": key_start.namespace()})

  @staticmethod
  def _split_id_or_name(id_or_name1, id_or_name2, batch_size, maintain_batches):
    """Return an id_or_name that is between id_or_name1 an id_or_name2.

    Attempts to split the range [id_or_name1, id_or_name2] in half,
    unless maintain_batches is true and the size of the range
    [id_or_name1, id_or_name2] is less than or equal to batch_size.

    Args:
      id_or_name1: A number or string or the id_or_name component of a key
      id_or_name2: A number or string or the id_or_name component of a key
      batch_size: The range size that will not be split if maintain_batches
        is true.
      maintain_batches: A boolean for whether to keep small ranges intact.

    Returns:
      An id_or_name such that id_or_name1 <= id_or_name <= id_or_name2.
    """
    if (isinstance(id_or_name1, (int, long)) and
        isinstance(id_or_name2, (int, long))):
      if not maintain_batches or id_or_name2 - id_or_name1 > batch_size:
        return (id_or_name1 + id_or_name2) / 2
      else:
        return id_or_name1
    elif (isinstance(id_or_name1, basestring) and
          isinstance(id_or_name2, basestring)):
      return KeyRange.bisect_string_range(id_or_name1, id_or_name2)
    else:
      if (not isinstance(id_or_name1, (int, long)) or
          not isinstance(id_or_name2, basestring)):
        raise KeyRangeError("Wrong key order: %r, %r" %
                            (id_or_name1, id_or_name2))

      zero_ch = unichr(0)
      if id_or_name2 == zero_ch:
        return (id_or_name1 + 2**63 - 1) / 2
      return zero_ch

  @staticmethod
  def guess_end_key(kind,
                    key_start,
                    probe_count=30,
                    split_rate=5):
    """Guess the end of a key range with a binary search of probe queries.

    When the 'key_start' parameter has a key hierarchy, this function will
    only determine the key range for keys in a similar hierarchy. That means
    if the keys are in the form:

      kind=Foo, name=bar/kind=Stuff, name=meep

    only this range will be probed:

      kind=Foo, name=*/kind=Stuff, name=*

    That means other entities of kind 'Stuff' that are children of another
    parent entity kind will be skipped:

      kind=Other, name=cookie/kind=Stuff, name=meep

    Args:
      key_start: The starting key of the search range. In most cases this
        should be id = 0 or name = '\0'.  May be db.Key or ndb.Key.
      kind: String name of the entity kind.
      probe_count: Optional, how many probe queries to run.
      split_rate: Exponential rate to use for splitting the range on the
        way down from the full key space. For smaller ranges this should
        be higher so more of the keyspace is skipped on initial descent.

    Returns:
      db.Key that is guaranteed to be as high or higher than the
      highest key existing for this Kind. Doing a query between 'key_start' and
      this returned Key (inclusive) will contain all entities of this Kind.

    NOTE: Even though an ndb.Key instance is accepted as argument,
    the return value is always a db.Key instance.
    """
    if ndb is not None:


      if isinstance(key_start, ndb.Key):
        key_start = key_start.to_old_key()
    app = key_start.app()
    namespace = key_start.namespace()

    full_path = key_start.to_path()
    for index, piece in enumerate(full_path):
      if index % 2 == 0:

        continue
      elif isinstance(piece, basestring):

        full_path[index] = u"\xffff"
      else:

        full_path[index] = 2**63 - 1

    key_end = db.Key.from_path(*full_path,
                               **{"_app": app, "namespace": namespace})
    split_key = key_end

    for i in xrange(probe_count):
      for j in xrange(split_rate):
        split_key = KeyRange.split_keys(key_start, split_key, 1)
      results = datastore.Query(
          kind,
          {"__key__ >": split_key},
          namespace=namespace,
          _app=app,
          keys_only=True).Get(1)
      if results:
        if results[0].name() and not key_start.name():


          return KeyRange.guess_end_key(
              kind, results[0], probe_count - 1, split_rate)
        else:
          split_rate = 1
          key_start = results[0]
          split_key = key_end
      else:
        key_end = split_key

    return key_end

  @classmethod
  def compute_split_points(cls, kind, count):
    """Computes a set of KeyRanges that are split points for a kind.

    Args:
      kind: String with the entity kind to split.
      count: Number of non-overlapping KeyRanges to generate.

    Returns:
      A list of KeyRange objects that are non-overlapping. At most "count" + 1
      KeyRange objects will be returned. At least one will be returned.
    """
    query = datastore.Query(kind=kind, keys_only=True)
    query.Order("__scatter__")
    random_keys = query.Get(count)

    if not random_keys:

      return [cls()]

    random_keys.sort()



    key_ranges = []


    key_ranges.append(cls(
        key_start=None,
        key_end=random_keys[0],
        direction=cls.ASC,
        include_start=False,
        include_end=False))


    for i in xrange(0, len(random_keys) - 1):
      key_ranges.append(cls(
          key_start=random_keys[i],
          key_end=random_keys[i + 1],
          direction=cls.ASC,
          include_start=True,
          include_end=False))


    key_ranges.append(cls(
        key_start=random_keys[-1],
        key_end=None,
        direction=cls.ASC,
        include_start=True,
        include_end=False))

    return key_ranges

  def to_json(self):
    """Serialize KeyRange to json.

    Returns:
      string with KeyRange json representation.
    """
    if simplejson is None:
      raise SimplejsonUnavailableError(
          "JSON functionality requires json or simplejson to be available")

    def key_to_str(key):
      if key:
        return str(key)
      else:
        return None

    obj_dict = {
        "direction": self.direction,
        "key_start": key_to_str(self.key_start),
        "key_end": key_to_str(self.key_end),
        "include_start": self.include_start,
        "include_end": self.include_end,
        "namespace": self.namespace,
        }
    if self._app:
      obj_dict["_app"] = self._app

    return simplejson.dumps(obj_dict, sort_keys=True)


  @staticmethod
  def from_json(json_str):
    """Deserialize KeyRange from its json representation.

    Args:
      json_str: string with json representation created by key_range_to_json.

    Returns:
      deserialized KeyRange instance.
    """
    if simplejson is None:
      raise SimplejsonUnavailableError(
          "JSON functionality requires json or simplejson to be available")

    def key_from_str(key_str):
      if key_str:
        return db.Key(key_str)
      else:
        return None

    json = simplejson.loads(json_str)
    return KeyRange(key_from_str(json["key_start"]),
                    key_from_str(json["key_end"]),
                    json["direction"],
                    json["include_start"],
                    json["include_end"],
                    json.get("namespace"),
                    _app=json.get("_app"))
