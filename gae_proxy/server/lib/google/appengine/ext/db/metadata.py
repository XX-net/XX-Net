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




"""Models and helper functions for access to app's datastore metadata.

These entities cannot be created by users, but are created as results of
__namespace__, __kind__ and __property__ metadata queries such as

  # Find all namespaces
  q = db.GqlQuery("SELECT * FROM __namespace__")
  for p in q.run():
    print "namespace:", repr(p.namespace_name)

or

  # Find all properties of A whose name starts with a lower-case letter
  q = db.GqlQuery("SELECT __key__ from __property__ " +
                  "WHERE __key__ >= :1 AND __key__ < :2",
                  Property.key_for_property("A", "a"),
                  Property.key_for_property("A", chr(ord("z") + 1)))
  for p in q.run():
    print "%s: %s" % (Property.key_to_kind(p), Property.key_to_property(p))

or, using Query objects

  # Find all kinds >= "a"
  q = metadata.Kind().all()
  q.filter("__key__ >=", metadata.Kind.key_for_kind("a"))
  for p in q.run():
    print "kind:", repr(p.kind_name)
"""








from google.appengine.api import datastore_types
from google.appengine.ext import db


class BaseMetadata(db.Model):
  """Base class for all metadata models."""


  KIND_NAME = '__BaseMetadata__'

  @classmethod
  def kind(cls):
    """Kind name override."""
    return cls.KIND_NAME


class Namespace(BaseMetadata):
  """Model for __namespace__ metadata query results."""

  KIND_NAME = '__namespace__'
  EMPTY_NAMESPACE_ID = datastore_types._EMPTY_NAMESPACE_ID

  @property
  def namespace_name(self):
    """Return the namespace name specified by this entity's key."""
    return self.key_to_namespace(self.key())

  @classmethod
  def key_for_namespace(cls, namespace):
    """Return the __namespace__ key for namespace.

    Args:
      namespace: namespace whose key is requested.

    Returns:
      The key for namespace.
    """
    if namespace:
      return db.Key.from_path(cls.KIND_NAME, namespace)
    else:
      return db.Key.from_path(cls.KIND_NAME, cls.EMPTY_NAMESPACE_ID)

  @classmethod
  def key_to_namespace(cls, key):
    """Return the namespace specified by a given __namespace__ key.

    Args:
      key: key whose name is requested.

    Returns:
      The namespace specified by key.
    """
    return key.name() or ''


class Kind(BaseMetadata):
  """Model for __kind__ metadata query results."""

  KIND_NAME = '__kind__'

  @property
  def kind_name(self):
    """Return the kind name specified by this entity's key."""
    return self.key_to_kind(self.key())

  @classmethod
  def key_for_kind(cls, kind):
    """Return the __kind__ key for kind.

    Args:
      kind: kind whose key is requested.

    Returns:
      The key for kind.
    """
    return db.Key.from_path(cls.KIND_NAME, kind)

  @classmethod
  def key_to_kind(cls, key):
    """Return the kind specified by a given __kind__ key.

    Args:
      key: key whose name is requested.

    Returns:
      The kind specified by key.
    """
    return key.name()


class Property(BaseMetadata):
  """Model for __property__ metadata query results."""

  KIND_NAME = '__property__'

  @property
  def property_name(self):
    """Return the property name specified by this entity's key."""
    return self.key_to_property(self.key())

  @property
  def kind_name(self):
    """Return the kind name specified by this entity's key."""
    return self.key_to_kind(self.key())

  property_representation = db.StringListProperty()

  @classmethod
  def key_for_kind(cls, kind):
    """Return the __property__ key for kind.

    Args:
      kind: kind whose key is requested.

    Returns:
      The parent key for __property__ keys of kind.
    """
    return db.Key.from_path(Kind.KIND_NAME, kind)

  @classmethod
  def key_for_property(cls, kind, property):
    """Return the __property__ key for property of kind.

    Args:
      kind: kind whose key is requested.
      property: property whose key is requested.

    Returns:
      The key for property of kind.
    """
    return db.Key.from_path(Kind.KIND_NAME, kind, Property.KIND_NAME, property)

  @classmethod
  def key_to_kind(cls, key):
    """Return the kind specified by a given __property__ key.

    Args:
      key: key whose kind name is requested.

    Returns:
      The kind specified by key.
    """
    if key.kind() == Kind.KIND_NAME:
      return key.name()
    else:
      return key.parent().name()

  @classmethod
  def key_to_property(cls, key):
    """Return the property specified by a given __property__ key.

    Args:
      key: key whose property name is requested.

    Returns:
      property specified by key, or None if the key specified only a kind.
    """
    if key.kind() == Kind.KIND_NAME:
      return None
    else:
      return key.name()


class EntityGroup(BaseMetadata):
  """Model for __entity_group__ metadata (available in HR datastore only).

  This metadata contains a numeric __version__ property that is guaranteed
  to increase on every change to the entity group. The version may increase
  even in the absence of user-visible changes to the entity group. The
  __entity_group__ entity may not exist None if the entity group was never
  written to.
  """

  KIND_NAME = '__entity_group__'
  ID = 1

  version = db.IntegerProperty(name='__version__')

  @classmethod
  def key_for_entity(cls, entity_or_key):
    """Return the metadata key for the entity group containing entity_or_key.

    Use this key to get() the __entity_group__ metadata entity for the
    entity group containing entity_or_key.

    Args:
      entity_or_key: a key or entity whose __entity_group__ key you want.

    Returns:
      The __entity_group__ key for the entity group containing entity_or_key.
    """
    if isinstance(entity_or_key, db.Model):
      key = entity_or_key.key()
    else:
      key = entity_or_key
    while key.parent():
      key = key.parent()
    return db.Key.from_path(cls.KIND_NAME, cls.ID, parent=key)


def get_namespaces(start=None, end=None):
  """Return all namespaces in the specified range.

  Args:
    start: only return namespaces >= start if start is not None.
    end: only return namespaces < end if end is not None.

  Returns:
    A list of namespace names between the (optional) start and end values.
  """
  q = Namespace.all()
  if start is not None:
    q.filter('__key__ >=', Namespace.key_for_namespace(start))
  if end is not None:
    q.filter('__key__ <', Namespace.key_for_namespace(end))

  return [x.namespace_name for x in q.run()]


def get_kinds(start=None, end=None):
  """Return all kinds in the specified range.

  Args:
    start: only return kinds >= start if start is not None.
    end: only return kinds < end if end is not None.

  Returns:
    A list of kind names between the (optional) start and end values.
  """
  q = Kind.all()
  if start is not None and start != '':
    q.filter('__key__ >=', Kind.key_for_kind(start))
  if end is not None:
    if end == '':
      return []
    q.filter('__key__ <', Kind.key_for_kind(end))

  return [x.kind_name for x in q.run()]


def get_properties_of_kind(kind, start=None, end=None):
  """Return all properties of kind in the specified range.

  NOTE: This function does not return unindexed properties.

  Args:
    kind: name of kind whose properties you want.
    start: only return properties >= start if start is not None.
    end: only return properties < end if end is not None.

  Returns:
    A list of property names of kind between the (optional) start and end
    values.
  """
  q = Property.all(keys_only=True)
  q.ancestor(Property.key_for_kind(kind))
  if start is not None and start != '':
    q.filter('__key__ >=', Property.key_for_property(kind, start))
  if end is not None:
    if end == '':
      return []
    q.filter('__key__ <', Property.key_for_property(kind, end))

  return [Property.key_to_property(x) for x in q.run()]


def get_representations_of_kind(kind, start=None, end=None):
  """Return all representations of properties of kind in the specified range.

  NOTE: This function does not return unindexed properties.

  Args:
    kind: name of kind whose properties you want.
    start: only return properties >= start if start is not None.
    end: only return properties < end if end is not None.

  Returns:
    A dictionary mapping property names to its list of representations.
  """
  q = Property.all()
  q.ancestor(Property.key_for_kind(kind))
  if start is not None and start != '':
    q.filter('__key__ >=', Property.key_for_property(kind, start))
  if end is not None:
    if end == '':
      return {}
    q.filter('__key__ <', Property.key_for_property(kind, end))

  result = {}
  for property in q.run():
    result[property.property_name] = property.property_representation

  return result


def get_entity_group_version(entity_or_key):
  """Return the version of the entity group containing entity_or_key.

  Args:
    entity_or_key: a key or entity whose version you want.

  Returns: The version of the entity group containing entity_or_key. This
    version is guaranteed to increase on every change to the entity
    group. The version may increase even in the absence of user-visible
    changes to the entity group. May return None if the entity group was
    never written to.

    On non-HR datatores, this function returns None.
  """

  eg = db.get(EntityGroup.key_for_entity(entity_or_key))
  if eg:
    return eg.version
  else:
    return None
