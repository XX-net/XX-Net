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




"""Support for polymorphic models and queries.

The Model class on its own is only able to support functional polymorphism.
It is possible to create a subclass of Model and then subclass that one as
many generations as necessary and those classes will share all the same
properties and behaviors.  The problem is that subclassing Model in this way
places each subclass in their own Kind.  This means that it is not possible
to do polymorphic queries.  Building a query on a base class will only return
instances of that class from the Datastore, while queries on a subclass will
only return those instances.

This module allows applications to specify class hierarchies that support
polymorphic queries.
"""



from google.appengine.ext import db


_class_map = {}


_CLASS_KEY_PROPERTY = 'class'


class _ClassKeyProperty(db.ListProperty):
  """Property representing class-key property of a polymorphic class.

  The class key is a list of strings describing an polymorphic instances
  place within its class hierarchy.  This property is automatically calculated.
  For example:

    class Foo(PolyModel): ...
    class Bar(Foo): ...
    class Baz(Bar): ...

    Foo.class_key() == ['Foo']
    Bar.class_key() == ['Foo', 'Bar']
    Baz.class_key() == ['Foo', 'Bar', 'Baz']
  """

  def __init__(self, name):
    super(_ClassKeyProperty, self).__init__(name=name,
                                            item_type=str,
                                            default=None)

  def __set__(self, *args):
    raise db.DerivedPropertyError(
        'Class-key is a derived property and cannot be set.')

  def __get__(self, model_instance, model_class):
    if model_instance is None:
      return self
    return [cls.__name__ for cls in model_class.__class_hierarchy__]


class PolymorphicClass(db.PropertiedClass):
  """Meta-class for initializing PolymorphicClasses.

  This class extends PropertiedClass to add a few static attributes to
  new polymorphic classes necessary for their correct functioning.

  """

  def __init__(cls, name, bases, dct):
    """Initializes a class that belongs to a polymorphic hierarchy.

    This method configures a few built-in attributes of polymorphic
    models:

      __root_class__: If the new class is a root class, __root_class__ is set to
        itself so that it subclasses can quickly know what the root of
        their hierarchy is and what kind they are stored in.
      __class_hierarchy__: List of classes describing the new model's place
        in the class hierarchy in reverse MRO order.  The first element is
        always the root class while the last element is always the new class.

        MRO documentation: http://www.python.org/download/releases/2.3/mro/

        For example:
          class Foo(PolymorphicClass): ...

          class Bar(Foo): ...

          class Baz(Bar): ...

          Foo.__class_hierarchy__ == [Foo]
          Bar.__class_hierarchy__ == [Foo, Bar]
          Baz.__class_hierarchy__ == [Foo, Bar, Baz]

    Unless the class is a root class or PolyModel itself, it is not
    inserted in to the kind-map like other models.  However, all polymorphic
    classes, are inserted in to the class-map which maps the class-key to
    implementation.  This class key is consulted using the polymorphic instances
    discriminator (the 'class' property of the entity) when loading from the
    datastore.
    """



    if name == 'PolyModel':

      super(PolymorphicClass, cls).__init__(name, bases, dct, map_kind=False)
      return

    elif PolyModel in bases:
      if getattr(cls, '__class_hierarchy__', None):
        raise db.ConfigurationError(('%s cannot derive from PolyModel as '
            '__class_hierarchy__ is already defined.') % cls.__name__)
      cls.__class_hierarchy__ = [cls]


      cls.__root_class__ = cls

      super(PolymorphicClass, cls).__init__(name, bases, dct)
    else:

      super(PolymorphicClass, cls).__init__(name, bases, dct, map_kind=False)


      cls.__class_hierarchy__ = [c for c in reversed(cls.mro())
          if issubclass(c, PolyModel) and c != PolyModel]





      if cls.__class_hierarchy__[0] != cls.__root_class__:
        raise db.ConfigurationError(
            '%s cannot be derived from both root classes %s and %s' %
            (cls.__name__,
            cls.__class_hierarchy__[0].__name__,
            cls.__root_class__.__name__))

    _class_map[cls.class_key()] = cls


class PolyModel(db.Model):
  """Base-class for models that supports polymorphic queries.

  Use this class to build hierarchies that can be queried based
  on their types.

  Example:

    consider the following model hierarchy:

      +------+
      |Animal|
      +------+
        |
        +-----------------+
        |                 |
      +------+          +------+
      |Canine|          |Feline|
      +------+          +------+
        |                 |
        +-------+         +-------+
        |       |         |       |
      +---+   +----+    +---+   +-------+
      |Dog|   |Wolf|    |Cat|   |Panther|
      +---+   +----+    +---+   +-------+

    This class hierarchy has three levels.  The first is the "root class".
    All models in a single class hierarchy must inherit from this root.  All
    models in the hierarchy are stored as the same kind as the root class.
    For example, Panther entities when stored to the datastore are of the kind
    'Animal'.  Querying against the Animal kind will retrieve Cats, Dogs and
    Canines, for example, that match your query.  Different classes stored
    in the root class' kind are identified by their class-key.  When loaded
    from the datastore, it is mapped to the appropriate implementation class.

  Polymorphic properties:

    Properties that are defined in a given base-class within a hierarchy are
    stored in the datastore for all sub-casses only.  So, if the Feline class
    had a property called 'whiskers', the Cat and Panther enties would also
    have whiskers, but not Animal, Canine, Dog or Wolf.

  Polymorphic queries:

    When written to the datastore, all polymorphic objects automatically have
    a property called 'class' that you can query against.  Using this property
    it is possible to easily write a GQL query against any sub-hierarchy.  For
    example, to fetch only Canine objects, including all Dogs and Wolves:

      db.GqlQuery("SELECT * FROM Animal WHERE class='Canine'")

    And alternate method is to use the 'all' or 'gql' methods of the Canine
    class:

      Canine.all()
      Canine.gql('')

    The 'class' property is not meant to be used by your code other than
    for queries.  Since it is supposed to represents the real Python class
    it is intended to be hidden from view.

  Root class:

    The root class is the class from which all other classes of the hierarchy
    inherits from.  Each hierarchy has a single root class.  A class is a
    root class if it is an immediate child of PolyModel.  The subclasses of
    the root class are all the same kind as the root class. In other words:

      Animal.kind() == Feline.kind() == Panther.kind() == 'Animal'
  """

  __metaclass__ = PolymorphicClass



  _class = _ClassKeyProperty(name=_CLASS_KEY_PROPERTY)

  def __new__(*args, **kwds):
    """Prevents direct instantiation of PolyModel.

    Allow subclasses to call __new__() with arguments.

    Do NOT list 'cls' as the first argument, or in the case when
    the 'kwds' dictionary contains the key 'cls', the function
    will complain about multiple argument values for 'cls'.

    Raises:
      TypeError if there are no positional arguments.
    """
    if args:
      cls = args[0]
    else:
      raise TypeError('object.__new__(): not enough arguments')

    if cls is PolyModel:
      raise NotImplementedError()
    return super(PolyModel, cls).__new__(cls, *args, **kwds)

  @classmethod
  def kind(cls):
    """Get kind of polymorphic model.

    Overridden so that all subclasses of root classes are the same kind
    as the root.

    Returns:
      Kind of entity to write to datastore.
    """
    if cls is cls.__root_class__:
      return super(PolyModel, cls).kind()
    else:
      return cls.__root_class__.kind()

  @classmethod
  def class_key(cls):
    """Calculate the class-key for this class.

    Returns:
      Class key for class.  By default this is a the list of classes
      of the hierarchy, starting with the root class and walking its way
      down to cls.
    """
    if not hasattr(cls, '__class_hierarchy__'):
      raise NotImplementedError(
          'Cannot determine class key without class hierarchy')
    return tuple(cls.class_name() for cls in cls.__class_hierarchy__)

  @classmethod
  def class_name(cls):
    """Calculate class name for this class.

    Returns name to use for each classes element within its class-key.  Used
    to discriminate between different classes within a class hierarchy's
    Datastore kind.

    The presence of this method allows developers to use a different class
    name in the datastore from what is used in Python code.  This is useful,
    for example, for renaming classes without having to migrate instances
    already written to the datastore.  For example, to rename a polymorphic
    class Contact to SimpleContact, you could convert:

      # Class key is ['Information']
      class Information(PolyModel): ...

      # Class key is ['Information', 'Contact']
      class Contact(Information): ...

    to:

      # Class key is still ['Information', 'Contact']
      class SimpleContact(Information):
        ...
        @classmethod
        def class_name(cls):
          return 'Contact'

      # Class key is ['Information', 'Contact', 'ExtendedContact']
      class ExtendedContact(SimpleContact): ...

    This would ensure that all objects written previously using the old class
    name would still be loaded.

    Returns:
      Name of this class.
    """
    return cls.__name__

  @classmethod
  def from_entity(cls, entity):
    """Load from entity to class based on discriminator.

    Rather than instantiating a new Model instance based on the kind
    mapping, this creates an instance of the correct model class based
    on the entities class-key.

    Args:
      entity: Entity loaded directly from datastore.

    Raises:
      KindError when there is no class mapping based on discriminator.
    """
    if (_CLASS_KEY_PROPERTY in entity and
        tuple(entity[_CLASS_KEY_PROPERTY]) != cls.class_key()):
      key = tuple(entity[_CLASS_KEY_PROPERTY])
      try:
        poly_class = _class_map[key]
      except KeyError:
        raise db.KindError('No implementation for class \'%s\'' % (key,))
      return poly_class.from_entity(entity)
    return super(PolyModel, cls).from_entity(entity)

  @classmethod
  def all(cls, **kwds):
    """Get all instance of a class hierarchy.

    Args:
      kwds: Keyword parameters passed on to Model.all.

    Returns:
      Query with filter set to match this class' discriminator.
    """
    query = super(PolyModel, cls).all(**kwds)
    if cls != cls.__root_class__:
      query.filter(_CLASS_KEY_PROPERTY + ' =', cls.class_name())
    return query

  @classmethod
  def gql(cls, query_string, *args, **kwds):
    """Returns a polymorphic query using GQL query string.

    This query is polymorphic in that it has its filters configured in a way
    to retrieve instances of the model or an instance of a subclass of the
    model.

    Args:
      query_string: properly formatted GQL query string with the
        'SELECT * FROM <entity>' part omitted
      *args: rest of the positional arguments used to bind numeric references
        in the query.
      **kwds: dictionary-based arguments (for named parameters).
    """
    if cls == cls.__root_class__:
      return super(PolyModel, cls).gql(query_string, *args, **kwds)
    else:
      from google.appengine.ext import gql


      query = db.GqlQuery('SELECT * FROM %s %s' % (cls.kind(), query_string))










      query_filter = [('nop',
                       [gql.Literal(cls.class_name())])]
      query._proto_query.filters()[('class', '=')] = query_filter
      query.bind(*args, **kwds)
      return query
