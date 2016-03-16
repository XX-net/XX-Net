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




"""Simple, schema-based database abstraction layer for the datastore.

Modeled after Django's abstraction layer on top of SQL databases,
http://www.djangoproject.com/documentation/mode_api/. Ours is a little simpler
and a lot less code because the datastore is so much simpler than SQL
databases.

The programming model is to declare Python subclasses of the Model class,
declaring datastore properties as class members of that class. So if you want to
publish a story with title, body, and created date, you would do it like this:

    class Story(db.Model):
      title = db.StringProperty()
      body = db.TextProperty()
      created = db.DateTimeProperty(auto_now_add=True)

You can create a new Story in the datastore with this usage pattern:

    story = Story(title='My title')
    story.body = 'My body'
    story.put()

You query for Story entities using built in query interfaces that map directly
to the syntax and semantics of the datastore:

    stories = Story.all().filter('date >=', yesterday).order('-date')
    for story in stories:
      print story.title

The Property declarations enforce types by performing validation on assignment.
For example, the DateTimeProperty enforces that you assign valid datetime
objects, and if you supply the "required" option for a property, you will not
be able to assign None to that property.

We also support references between models, so if a story has comments, you
would represent it like this:

    class Comment(db.Model):
      story = db.ReferenceProperty(Story)
      body = db.TextProperty()

When you get a story out of the datastore, the story reference is resolved
automatically the first time it is referenced, which makes it easy to use
model instances without performing additional queries by hand:

    comment = Comment.get(key)
    print comment.story.title

Likewise, you can access the set of comments that refer to each story through
this property through a reverse reference called comment_set, which is a Query
preconfigured to return all matching comments:

    story = Story.get(key)
    for comment in story.comment_set:
       print comment.body

"""















import copy
import datetime
import logging
import re
import time
import urlparse
import warnings

from google.appengine.api import datastore
from google.appengine.api import datastore_errors
from google.appengine.api import datastore_types
from google.appengine.api import namespace_manager
from google.appengine.api import users
from google.appengine.datastore import datastore_rpc
from google.appengine.datastore import datastore_query


Error = datastore_errors.Error
BadValueError = datastore_errors.BadValueError
BadPropertyError = datastore_errors.BadPropertyError
BadRequestError = datastore_errors.BadRequestError
EntityNotFoundError = datastore_errors.EntityNotFoundError
BadArgumentError = datastore_errors.BadArgumentError
QueryNotFoundError = datastore_errors.QueryNotFoundError
TransactionNotFoundError = datastore_errors.TransactionNotFoundError
Rollback = datastore_errors.Rollback
TransactionFailedError = datastore_errors.TransactionFailedError
BadFilterError = datastore_errors.BadFilterError
BadQueryError = datastore_errors.BadQueryError
BadKeyError = datastore_errors.BadKeyError
InternalError = datastore_errors.InternalError
NeedIndexError = datastore_errors.NeedIndexError
ReferencePropertyResolveError = datastore_errors.ReferencePropertyResolveError
Timeout = datastore_errors.Timeout
CommittedButStillApplying = datastore_errors.CommittedButStillApplying

ValidationError = BadValueError


Key = datastore_types.Key
Category = datastore_types.Category
Link = datastore_types.Link
Email = datastore_types.Email
GeoPt = datastore_types.GeoPt
IM = datastore_types.IM
PhoneNumber = datastore_types.PhoneNumber
PostalAddress = datastore_types.PostalAddress
Rating = datastore_types.Rating
Text = datastore_types.Text
Blob = datastore_types.Blob
ByteString = datastore_types.ByteString
BlobKey = datastore_types.BlobKey


READ_CAPABILITY = datastore.READ_CAPABILITY
WRITE_CAPABILITY = datastore.WRITE_CAPABILITY


STRONG_CONSISTENCY = datastore.STRONG_CONSISTENCY
EVENTUAL_CONSISTENCY = datastore.EVENTUAL_CONSISTENCY


NESTED = datastore_rpc.TransactionOptions.NESTED
MANDATORY = datastore_rpc.TransactionOptions.MANDATORY
ALLOWED = datastore_rpc.TransactionOptions.ALLOWED
INDEPENDENT = datastore_rpc.TransactionOptions.INDEPENDENT


KEY_RANGE_EMPTY = "Empty"
"""Indicates the given key range is empty and the datastore's
automatic ID allocator will not assign keys in this range to new
entities.
"""

KEY_RANGE_CONTENTION = "Contention"
"""Indicates the given key range is empty but the datastore's
automatic ID allocator may assign new entities keys in this range.
However it is safe to manually assign keys in this range
if either of the following is true:

 - No other request will insert entities with the same kind and parent
   as the given key range until all entities with manually assigned
   keys from this range have been written.
 - Overwriting entities written by other requests with the same kind
   and parent as the given key range is acceptable.

The datastore's automatic ID allocator will not assign a key to a new
entity that will overwrite an existing entity, so once the range is
populated there will no longer be any contention.
"""

KEY_RANGE_COLLISION = "Collision"
"""Indicates that entities with keys inside the given key range
already exist and writing to this range will overwrite those entities.
Additionally the implications of KEY_RANGE_COLLISION apply. If
overwriting entities that exist in this range is acceptable it is safe
to use the given range.

The datastore's automatic ID allocator will never assign a key to
a new entity that will overwrite an existing entity so entities
written by the user to this range will never be overwritten by
an entity with an automatically assigned key.
"""



_kind_map = {}



_SELF_REFERENCE = object()




_RESERVED_WORDS = set(['key_name'])





class NotSavedError(Error):
  """Raised when a saved-object action is performed on a non-saved object."""


class KindError(BadValueError):
  """Raised when an entity is used with incorrect Model."""


class PropertyError(Error):
  """Raised when non-existent property is referenced."""


class DuplicatePropertyError(Error):
  """Raised when a property is duplicated in a model definition."""


class ConfigurationError(Error):
  """Raised when a property or model is improperly configured."""


class ReservedWordError(Error):
  """Raised when a property is defined for a reserved word."""


class DerivedPropertyError(Error):
  """Raised when attempting to assign a value to a derived property."""


_ALLOWED_PROPERTY_TYPES = set([
    basestring,
    str,
    unicode,
    bool,
    int,
    long,
    float,
    Key,
    datetime.datetime,
    datetime.date,
    datetime.time,
    Blob,
    datastore_types.EmbeddedEntity,
    ByteString,
    Text,
    users.User,
    Category,
    Link,
    Email,
    GeoPt,
    IM,
    PhoneNumber,
    PostalAddress,
    Rating,
    BlobKey,
    ])

_ALLOWED_EXPANDO_PROPERTY_TYPES = set(_ALLOWED_PROPERTY_TYPES)
_ALLOWED_EXPANDO_PROPERTY_TYPES.update((list, tuple, type(None)))



_OPERATORS = ['<', '<=', '>', '>=', '=', '==', '!=', 'in']
_FILTER_REGEX = re.compile(
    '^\s*([^\s]+)(\s+(%s)\s*)?$' % '|'.join(_OPERATORS),
    re.IGNORECASE | re.UNICODE)


def class_for_kind(kind):
  """Return base-class responsible for implementing kind.

  Necessary to recover the class responsible for implementing provided
  kind.

  Args:
    kind: Entity kind string.

  Returns:
    Class implementation for kind.

  Raises:
    KindError when there is no implementation for kind.
  """
  try:
    return _kind_map[kind]
  except KeyError:
    raise KindError('No implementation for kind \'%s\'' % kind)


def check_reserved_word(attr_name):
  """Raise an exception if attribute name is a reserved word.

  Args:
    attr_name: Name to check to see if it is a reserved word.

  Raises:
    ReservedWordError when attr_name is determined to be a reserved word.
  """
  if datastore_types.RESERVED_PROPERTY_NAME.match(attr_name):
    raise ReservedWordError(
        "Cannot define property.  All names both beginning and "
        "ending with '__' are reserved.")

  if attr_name in _RESERVED_WORDS or attr_name in dir(Model):
    raise ReservedWordError(
        "Cannot define property using reserved word '%(attr_name)s'. "
        "If you would like to use this name in the datastore consider "
        "using a different name like %(attr_name)s_ and adding "
        "name='%(attr_name)s' to the parameter list of the property "
        "definition." % locals())


def query_descendants(model_instance):
  """Returns a query for all the descendants of a model instance.

  Args:
    model_instance: Model instance to find the descendants of.

  Returns:
    Query that will retrieve all entities that have the given model instance
  as an ancestor. Unlike normal ancestor queries, this does not include the
  ancestor itself.
  """


  result = Query().ancestor(model_instance)

  result.filter(datastore_types.KEY_SPECIAL_PROPERTY + ' >',
                model_instance.key())
  return result


def model_to_protobuf(model_instance, _entity_class=datastore.Entity):
  """Encodes a model instance as a protocol buffer.

  Args:
    model_instance: Model instance to encode.
  Returns:
    entity_pb.EntityProto representation of the model instance
  """

  return model_instance._populate_entity(_entity_class).ToPb()


def model_from_protobuf(pb, _entity_class=datastore.Entity):
  """Decodes a model instance from a protocol buffer.

  Args:
    pb: The protocol buffer representation of the model instance. Can be an
        entity_pb.EntityProto or str encoding of an entity_bp.EntityProto

  Returns:
    Model instance resulting from decoding the protocol buffer
  """

  entity = _entity_class.FromPb(pb, default_kind=Expando.kind())
  return class_for_kind(entity.kind()).from_entity(entity)


def model_is_projection(model_instance):
  """Returns true if the given db.Model instance only contains a projection of
  the full entity.
  """
  return model_instance._entity and model_instance._entity.is_projection()


def _initialize_properties(model_class, name, bases, dct):
  """Initialize Property attributes for Model-class.

  Args:
    model_class: Model class to initialize properties for.
  """

  model_class._properties = {}


  property_source = {}

  def get_attr_source(name, cls):
    for src_cls  in cls.mro():
      if name in src_cls.__dict__:
        return src_cls

  defined = set()

  for base in bases:
    if hasattr(base, '_properties'):
      property_keys = set(base._properties.keys())
      duplicate_property_keys = defined & property_keys
      for dupe_prop_name in duplicate_property_keys:



        old_source = property_source[dupe_prop_name] = get_attr_source(
            dupe_prop_name, property_source[dupe_prop_name])
        new_source = get_attr_source(dupe_prop_name, base)
        if old_source != new_source:
          raise DuplicatePropertyError(
              'Duplicate property, %s, is inherited from both %s and %s.' %
              (dupe_prop_name, old_source.__name__, new_source.__name__))



      property_keys -= duplicate_property_keys
      if property_keys:
        defined |= property_keys


        property_source.update(dict.fromkeys(property_keys, base))
        model_class._properties.update(base._properties)


  for attr_name in dct.keys():
    attr = dct[attr_name]
    if isinstance(attr, Property):
      check_reserved_word(attr_name)
      if attr_name in defined:
        raise DuplicatePropertyError('Duplicate property: %s' % attr_name)
      defined.add(attr_name)
      model_class._properties[attr_name] = attr
      attr.__property_config__(model_class, attr_name)


  model_class._all_properties = frozenset(
      prop.name for name, prop in model_class._properties.items())


  model_class._unindexed_properties = frozenset(
    prop.name for name, prop in model_class._properties.items()
    if not prop.indexed)


def _coerce_to_key(value):
  """Returns the value's key.

  Args:
    value: a Model or Key instance or string encoded key or None

  Returns:
    The corresponding key, or None if value is None.
  """
  if value is None:
    return None

  value, multiple = datastore.NormalizeAndTypeCheck(
    value, (Model, Key, basestring))

  if len(value) > 1:
    raise datastore_errors.BadArgumentError('Expected only one model or key')
  value = value[0]

  if isinstance(value, Model):
    return value.key()
  elif isinstance(value, basestring):
    return Key(value)
  else:
    return value


class PropertiedClass(type):
  """Meta-class for initializing Model classes properties.

  Used for initializing Properties defined in the context of a model.
  By using a meta-class much of the configuration of a Property
  descriptor becomes implicit.  By using this meta-class, descriptors
  that are of class Model are notified about which class they
  belong to and what attribute they are associated with and can
  do appropriate initialization via __property_config__.

  Duplicate properties are not permitted.
  """

  def __init__(cls, name, bases, dct, map_kind=True):
    """Initializes a class that might have property definitions.

    This method is called when a class is created with the PropertiedClass
    meta-class.

    Loads all properties for this model and its base classes in to a dictionary
    for easy reflection via the 'properties' method.

    Configures each property defined in the new class.

    Duplicate properties, either defined in the new class or defined separately
    in two base classes are not permitted.

    Properties may not assigned to names which are in the list of
    _RESERVED_WORDS.  It is still possible to store a property using a reserved
    word in the datastore by using the 'name' keyword argument to the Property
    constructor.

    Args:
      cls: Class being initialized.
      name: Name of new class.
      bases: Base classes of new class.
      dct: Dictionary of new definitions for class.

    Raises:
      DuplicatePropertyError when a property is duplicated either in the new
        class or separately in two base classes.
      ReservedWordError when a property is given a name that is in the list of
        reserved words, attributes of Model and names of the form '__.*__'.
    """
    super(PropertiedClass, cls).__init__(name, bases, dct)

    _initialize_properties(cls, name, bases, dct)


    if map_kind:
      _kind_map[cls.kind()] = cls




AUTO_UPDATE_UNCHANGED = object()


class Property(object):
  """A Property is an attribute of a Model.

  It defines the type of the attribute, which determines how it is stored
  in the datastore and how the property values are validated. Different property
  types support different options, which change validation rules, default
  values, etc.  The simplest example of a property is a StringProperty:

     class Story(db.Model):
       title = db.StringProperty()
  """


  creation_counter = 0

  def __init__(self,
               verbose_name=None,
               name=None,
               default=None,
               required=False,
               validator=None,
               choices=None,
               indexed=True):
    """Initializes this Property with the given options.

    Args:
      verbose_name: User friendly name of property.
      name: Storage name for property.  By default, uses attribute name
        as it is assigned in the Model sub-class.
      default: Default value for property if none is assigned.
      required: Whether property is required.
      validator: User provided method used for validation.
      choices: User provided set of valid property values.
      indexed: Whether property is indexed.
    """
    self.verbose_name = verbose_name
    self.name = name
    self.default = default
    self.required = required
    self.validator = validator
    self.choices = choices
    self.indexed = indexed
    self.creation_counter = Property.creation_counter
    Property.creation_counter += 1

  def __property_config__(self, model_class, property_name):
    """Configure property, connecting it to its model.

    Configure the property so that it knows its property name and what class
    it belongs to.

    Args:
      model_class: Model class which Property will belong to.
      property_name: Name of property within Model instance to store property
        values in.  By default this will be the property name preceded by
        an underscore, but may change for different subclasses.
    """
    self.model_class = model_class
    if self.name is None:
      self.name = property_name

  def __get__(self, model_instance, model_class):
    """Returns the value for this property on the given model instance.

    See http://docs.python.org/ref/descriptors.html for a description of
    the arguments to this class and what they mean."""



    if model_instance is None:
      return self





    try:
      return getattr(model_instance, self._attr_name())
    except AttributeError:
      return None

  def __set__(self, model_instance, value):
    """Sets the value for this property on the given model instance.

    See http://docs.python.org/ref/descriptors.html for a description of
    the arguments to this class and what they mean.
    """
    value = self.validate(value)
    setattr(model_instance, self._attr_name(), value)

  def default_value(self):
    """Default value for unassigned values.

    Returns:
      Default value as provided by __init__(default).
    """
    return self.default

  def validate(self, value):
    """Assert that provided value is compatible with this property.

    Args:
      value: Value to validate against this Property.

    Returns:
      A valid value, either the input unchanged or adapted to the
      required type.

    Raises:
      BadValueError if the value is not appropriate for this
      property in any way.
    """
    if self.empty(value):
      if self.required:
        raise BadValueError('Property %s is required' % self.name)
    else:
      if self.choices:
        if value not in self.choices:
          raise BadValueError('Property %s is %r; must be one of %r' %
                              (self.name, value, self.choices))
    if self.validator is not None:
      self.validator(value)
    return value

  def empty(self, value):
    """Determine if value is empty in the context of this property.

    For most kinds, this is equivalent to "not value", but for kinds like
    bool, the test is more subtle, so subclasses can override this method
    if necessary.

    Args:
      value: Value to validate against this Property.

    Returns:
      True if this value is considered empty in the context of this Property
      type, otherwise False.
    """
    return not value

  def get_value_for_datastore(self, model_instance):
    """Datastore representation of this property.

    Looks for this property in the given model instance, and returns the proper
    datastore representation of the value that can be stored in a datastore
    entity.  Most critically, it will fetch the datastore key value for
    reference properties.

    Some properies (e.g. DateTimeProperty, UserProperty) optionally update their
    value on every put(). This call must return the current value for such
    properties (get_updated_value_for_datastore returns the new value).

    Args:
      model_instance: Instance to fetch datastore value from.

    Returns:
      Datastore representation of the model value in a form that is
      appropriate for storing in the datastore.
    """
    return self.__get__(model_instance, model_instance.__class__)

  def get_updated_value_for_datastore(self, model_instance):
    """Determine new value for auto-updated property.

    Some properies (e.g. DateTimeProperty, UserProperty) optionally update their
    value on every put(). This call must return the new desired value for such
    properties. For all other properties, this call must return
    AUTO_UPDATE_UNCHANGED.

    Args:
      model_instance: Instance to get new value for.

    Returns:
      Datastore representation of the new model value in a form that is
      appropriate for storing in the datastore, or AUTO_UPDATE_UNCHANGED.
    """
    return AUTO_UPDATE_UNCHANGED

  def make_value_from_datastore_index_value(self, index_value):
    value = datastore_types.RestoreFromIndexValue(index_value, self.data_type)
    return self.make_value_from_datastore(value)

  def make_value_from_datastore(self, value):
    """Native representation of this property.

    Given a value retrieved from a datastore entity, return a value,
    possibly converted, to be stored on the model instance.  Usually
    this returns the value unchanged, but a property class may
    override this when it uses a different datatype on the model
    instance than on the entity.

    This API is not quite symmetric with get_value_for_datastore(),
    because the model instance on which to store the converted value
    may not exist yet -- we may be collecting values to be passed to a
    model constructor.

    Args:
      value: value retrieved from the datastore entity.

    Returns:
      The value converted for use as a model instance attribute.
    """
    return value

  def _require_parameter(self, kwds, parameter, value):
    """Sets kwds[parameter] to value.

    If kwds[parameter] exists and is not value, raises ConfigurationError.

    Args:
      kwds: The parameter dict, which maps parameter names (strings) to values.
      parameter: The name of the parameter to set.
      value: The value to set it to.
    """
    if parameter in kwds and kwds[parameter] != value:
      raise ConfigurationError('%s must be %s.' % (parameter, value))

    kwds[parameter] = value

  def _attr_name(self):
    """Attribute name we use for this property in model instances.

    DO NOT USE THIS METHOD.
    """

    return '_' + self.name





  data_type = str

  def datastore_type(self):
    """Deprecated backwards-compatible accessor method for self.data_type."""

    return self.data_type


class Index(datastore._BaseIndex):
  """A datastore index."""

  id = datastore._BaseIndex._Id
  kind = datastore._BaseIndex._Kind
  has_ancestor = datastore._BaseIndex._HasAncestor
  properties = datastore._BaseIndex._Properties


class Model(object):
  """Model is the superclass of all object entities in the datastore.

  The programming model is to declare Python subclasses of the Model class,
  declaring datastore properties as class members of that class. So if you want
  to publish a story with title, body, and created date, you would do it like
  this:

    class Story(db.Model):
      title = db.StringProperty()
      body = db.TextProperty()
      created = db.DateTimeProperty(auto_now_add=True)

  A model instance can have a single parent.  Model instances without any
  parent are root entities.  It is possible to efficiently query for
  instances by their shared parent.  All descendents of a single root
  instance also behave as a transaction group.  This means that when you
  work one member of the group within a transaction all descendents of that
  root join the transaction.  All operations within a transaction on this
  group are ACID.
  """


  __metaclass__ = PropertiedClass

  def __new__(*args, **unused_kwds):
    """Allow subclasses to call __new__() with arguments.

    Do NOT list 'cls' as the first argument, or in the case when
    the 'unused_kwds' dictionary contains the key 'cls', the function
    will complain about multiple argument values for 'cls'.

    Raises:
      TypeError if there are no positional arguments.
    """
    if args:
      cls = args[0]
    else:
      raise TypeError('object.__new__(): not enough arguments')



    return super(Model, cls).__new__(cls)

  def __init__(self,
               parent=None,
               key_name=None,
               _app=None,
               _from_entity=False,
               **kwds):
    """Creates a new instance of this model.

    To create a new entity, you instantiate a model and then call put(),
    which saves the entity to the datastore:

       person = Person()
       person.name = 'Bret'
       person.put()

    You can initialize properties in the model in the constructor with keyword
    arguments:

       person = Person(name='Bret')

    We initialize all other properties to the default value (as defined by the
    properties in the model definition) if they are not provided in the
    constructor.

    Args:
      parent: Parent instance for this instance or None, indicating a top-
        level instance.
      key_name: Name for new model instance.
      _from_entity: Intentionally undocumented.
      kwds: Keyword arguments mapping to properties of model.  Also:
        key: Key instance for this instance, if provided makes parent and
             key_name redundant (they do not need to be set but if they are
             they must match the key).
    """















    namespace = None
    if isinstance(_app, tuple):
      if len(_app) != 2:
        raise BadArgumentError('_app must have 2 values if type is tuple.')
      _app, namespace = _app
    key = kwds.get('key', None)
    if key is not None:
      if isinstance(key, (tuple, list)):
        key = Key.from_path(*key)
      if isinstance(key, basestring):
        key = Key(encoded=key)
      if not isinstance(key, Key):
        raise TypeError('Expected Key type; received %s (is %s)' %
                        (key, key.__class__.__name__))
      if not key.has_id_or_name():
        raise BadKeyError('Key must have an id or name')
      if key.kind() != self.kind():
        raise BadKeyError('Expected Key kind to be %s; received %s' %
                          (self.kind(), key.kind()))
      if _app is not None and key.app() != _app:
        raise BadKeyError('Expected Key app to be %s; received %s' %
                          (_app, key.app()))
      if namespace is not None and key.namespace() != namespace:
        raise BadKeyError('Expected Key namespace to be %s; received %s' %
                          (namespace, key.namespace()))
      if key_name and key_name != key.name():
        raise BadArgumentError('Cannot use key and key_name at the same time'
                               ' with different values')
      if parent and parent != key.parent():
        raise BadArgumentError('Cannot use key and parent at the same time'
                               ' with different values')
      namespace = key.namespace()
      self._key = key
      self._key_name = None
      self._parent = None
      self._parent_key = None
    else:
      if key_name == '':
        raise BadKeyError('Name cannot be empty.')
      elif key_name is not None and not isinstance(key_name, basestring):
        raise BadKeyError('Name must be string type, not %s' %
                          key_name.__class__.__name__)

      if parent is not None:
        if not isinstance(parent, (Model, Key)):
          raise TypeError('Expected Model type; received %s (is %s)' %
                          (parent, parent.__class__.__name__))
        if isinstance(parent, Model) and not parent.has_key():
          raise BadValueError(
              "%s instance must have a complete key before it can be used as a "
              "parent." % parent.kind())
        if isinstance(parent, Key):
          self._parent_key = parent
          self._parent = None
        else:
          self._parent_key = parent.key()
          self._parent = parent
      else:
        self._parent_key = None
        self._parent = None
      self._key_name = key_name
      self._key = None

    if self._parent_key is not None:
      if namespace is not None and self._parent_key.namespace() != namespace:
        raise BadArgumentError(
            'Expected parent namespace to be %r; received %r' %
            (namespace, self._parent_key.namespace()))
      namespace = self._parent_key.namespace()

    self._entity = None

    if _app is not None and isinstance(_app, Key):
      raise BadArgumentError('_app should be a string; received Key(\'%s\'):\n'
                             '  This may be the result of passing \'key\' as '
                             'a positional parameter in SDK 1.2.6.  Please '
                             'only pass \'key\' as a keyword parameter.' % _app)

    if namespace is None:
      namespace = namespace_manager.get_namespace()

    self._app = _app
    self.__namespace = namespace

    is_projection = False

    if isinstance(_from_entity, datastore.Entity) and _from_entity.is_saved():
      self._entity = _from_entity
      is_projection = _from_entity.is_projection()
      del self._key_name
      del self._key



    for prop in self.properties().values():
      if prop.name in kwds:
        value = kwds[prop.name]
      elif is_projection:
        continue
      else:
        value = prop.default_value()
      try:
        prop.__set__(self, value)
      except DerivedPropertyError:





        if prop.name in kwds and not _from_entity:
          raise

  def key(self):
    """Unique key for this entity.

    This property is only available if this entity is already stored in the
    datastore or if it has a full key, so it is available if this entity was
    fetched returned from a query, or after put() is called the first time
    for new entities, or if a complete key was given when constructed.

    Returns:
      Datastore key of persisted entity.

    Raises:
      NotSavedError when entity is not persistent.
    """
    if self.is_saved():
      return self._entity.key()
    elif self._key:
      return self._key
    elif self._key_name:
      parent = self._parent_key or (self._parent and self._parent.key())
      self._key = Key.from_path(self.kind(), self._key_name, parent=parent,
                                _app=self._app, namespace=self.__namespace)
      return self._key
    else:
      raise NotSavedError()

  def __set_property(self, entity, name, datastore_value):
    if datastore_value == []:
      prop = self.properties().get(name)
      if prop and isinstance(prop, ListProperty) and prop._write_empty_list:
        entity[name] = datastore_value
      else:



        entity.pop(name, None)
    else:
      entity[name] = datastore_value

  def _to_entity(self, entity):
    """Copies information from this model to provided entity.

    Args:
      entity: Entity to save information on.
    """

    for prop in self.properties().values():
      self.__set_property(entity, prop.name, prop.get_value_for_datastore(self))


    set_unindexed_properties = getattr(entity, 'set_unindexed_properties', None)
    if set_unindexed_properties:
      set_unindexed_properties(self._unindexed_properties)

  def _populate_internal_entity(self, _entity_class=datastore.Entity):
    """Populates self._entity, saving its state to the datastore.

    After this method is called, calling is_saved() will return True.

    Returns:
      Populated self._entity
    """
    self._entity = self._populate_entity(_entity_class=_entity_class)


    for prop in self.properties().values():
      new_value = prop.get_updated_value_for_datastore(self)
      if new_value is not AUTO_UPDATE_UNCHANGED:
        self.__set_property(self._entity, prop.name, new_value)

    for attr in ('_key_name', '_key'):
      try:
        delattr(self, attr)
      except AttributeError:
        pass
    return self._entity

  def put(self, **kwargs):
    """Writes this model instance to the datastore.

    If this instance is new, we add an entity to the datastore.
    Otherwise, we update this instance, and the key will remain the
    same.

    Args:
      config: datastore_rpc.Configuration to use for this request.

    Returns:
      The key of the instance (either the existing key or a new key).

    Raises:
      TransactionFailedError if the data could not be committed.
    """
    self._populate_internal_entity()
    return datastore.Put(self._entity, **kwargs)



  save = put

  def _populate_entity(self, _entity_class=datastore.Entity):
    """Internal helper -- Populate self._entity or create a new one
    if that one does not exist.  Does not change any state of the instance
    other than the internal state of the entity.

    This method is separate from _populate_internal_entity so that it is
    possible to call to_xml without changing the state of an unsaved entity
    to saved.

    Returns:
      self._entity or a new Entity which is not stored on the instance.
    """
    if self.is_saved():
      entity = self._entity
    else:
      kwds = {'_app': self._app, 'namespace': self.__namespace,
              'unindexed_properties': self._unindexed_properties}
      if self._key is not None:
        if self._key.id():
          kwds['id'] = self._key.id()
        else:
          kwds['name'] = self._key.name()
        if self._key.parent():
          kwds['parent'] = self._key.parent()
      else:
        if self._key_name is not None:
          kwds['name'] = self._key_name
        if self._parent_key is not None:
          kwds['parent'] = self._parent_key
        elif self._parent is not None:
          kwds['parent'] = self._parent._entity
      entity = _entity_class(self.kind(), **kwds)

    self._to_entity(entity)
    return entity

  def delete(self, **kwargs):
    """Deletes this entity from the datastore.

    Args:
      config: datastore_rpc.Configuration to use for this request.

    Raises:
      TransactionFailedError if the data could not be committed.
    """
    datastore.Delete(self.key(), **kwargs)


    self._key = self.key()
    self._key_name = None
    self._parent_key = None
    self._entity = None



  def is_saved(self):
    """Determine if entity is persisted in the datastore.

    New instances of Model do not start out saved in the data.  Objects which
    are saved to or loaded from the Datastore will have a True saved state.

    Returns:
      True if object has been persisted to the datastore, otherwise False.
    """
    return self._entity is not None

  def has_key(self):
    """Determine if this model instance has a complete key.

    When not using a fully self-assigned Key, ids are not assigned until the
    data is saved to the Datastore, but instances with a key name always have
    a full key.

    Returns:
      True if the object has been persisted to the datastore or has a key
      or has a key_name, otherwise False.
    """
    return self.is_saved() or self._key or self._key_name

  def dynamic_properties(self):
    """Returns a list of all dynamic properties defined for instance."""
    return []


  def instance_properties(self):
    """Alias for dyanmic_properties."""
    return self.dynamic_properties()

  def parent(self):
    """Get the parent of the model instance.

    Returns:
      Parent of contained entity or parent provided in constructor, None if
      instance has no parent.
    """
    if self._parent is None:
      parent_key = self.parent_key()
      if parent_key is not None:

        self._parent = get(parent_key)
    return self._parent

  def parent_key(self):
    """Get the parent's key.

    This method is useful for avoiding a potential fetch from the datastore
    but still get information about the instances parent.

    Returns:
      Parent key of entity, None if there is no parent.
    """
    if self._parent_key is not None:
      return self._parent_key
    elif self._parent is not None:
      return self._parent.key()
    elif self._entity is not None:
      return self._entity.parent()
    elif self._key is not None:
      return self._key.parent()
    else:
      return None

  def to_xml(self, _entity_class=datastore.Entity):
    """Generate an XML representation of this model instance.

    atom and gd:namespace properties are converted to XML according to their
    respective schemas. For more information, see:

      http://www.atomenabled.org/developers/syndication/
      http://code.google.com/apis/gdata/common-elements.html
    """
    entity = self._populate_entity(_entity_class)
    return entity.ToXml()

  @classmethod
  def get(cls, keys, **kwargs):
    """Fetch instance from the datastore of a specific Model type using key.

    We support Key objects and string keys (we convert them to Key objects
    automatically).

    Useful for ensuring that specific instance types are retrieved from the
    datastore.  It also helps that the source code clearly indicates what
    kind of object is being retreived.  Example:

      story = Story.get(story_key)

    Args:
      keys: Key within datastore entity collection to find; or string key;
        or list of Keys or string keys.
      config: datastore_rpc.Configuration to use for this request.

    Returns:
      If a single key was given: a Model instance associated with key
      for the provided class if it exists in the datastore, otherwise
      None. If a list of keys was given: a list where list[i] is the
      Model instance for keys[i], or None if no instance exists.

    Raises:
      KindError if any of the retreived objects are not instances of the
      type associated with call to 'get'.
    """
    results = get(keys, **kwargs)
    if results is None:
      return None

    if isinstance(results, Model):
      instances = [results]
    else:
      instances = results

    for instance in instances:
      if not(instance is None or isinstance(instance, cls)):
        raise KindError('Kind %r is not a subclass of kind %r' %
                        (instance.kind(), cls.kind()))

    return results

  @classmethod
  def get_by_key_name(cls, key_names, parent=None, **kwargs):
    """Get instance of Model class by its key's name.

    Args:
      key_names: A single key-name or a list of key-names.
      parent: Parent of instances to get.  Can be a model or key.
      config: datastore_rpc.Configuration to use for this request.
    """
    try:
      parent = _coerce_to_key(parent)
    except BadKeyError, e:

      raise BadArgumentError(str(e))

    key_names, multiple = datastore.NormalizeAndTypeCheck(key_names, basestring)
    keys = [datastore.Key.from_path(cls.kind(), name, parent=parent)
            for name in key_names]
    if multiple:
      return get(keys, **kwargs)
    else:
      return get(keys[0], **kwargs)

  @classmethod
  def get_by_id(cls, ids, parent=None, **kwargs):
    """Get instance of Model class by id.

    Args:
      key_names: A single id or a list of ids.
      parent: Parent of instances to get.  Can be a model or key.
      config: datastore_rpc.Configuration to use for this request.
    """
    if isinstance(parent, Model):
      parent = parent.key()
    ids, multiple = datastore.NormalizeAndTypeCheck(ids, (int, long))
    keys = [datastore.Key.from_path(cls.kind(), id, parent=parent)
            for id in ids]
    if multiple:
      return get(keys, **kwargs)
    else:
      return get(keys[0], **kwargs)




  @classmethod
  def get_or_insert(cls, key_name, **kwds):
    """Transactionally retrieve or create an instance of Model class.

    This acts much like the Python dictionary setdefault() method, where we
    first try to retrieve a Model instance with the given key name and parent.
    If it's not present, then we create a new instance (using the *kwds
    supplied) and insert that with the supplied key name.

    Subsequent calls to this method with the same key_name and parent will
    always yield the same entity (though not the same actual object instance),
    regardless of the *kwds supplied. If the specified entity has somehow
    been deleted separately, then the next call will create a new entity and
    return it.

    If the 'parent' keyword argument is supplied, it must be a Model instance.
    It will be used as the parent of the new instance of this Model class if
    one is created.

    This method is especially useful for having just one unique entity for
    a specific identifier. Insertion/retrieval is done transactionally, which
    guarantees uniqueness.

    Example usage:

      class WikiTopic(db.Model):
        creation_date = db.DatetimeProperty(auto_now_add=True)
        body = db.TextProperty(required=True)

      # The first time through we'll create the new topic.
      wiki_word = 'CommonIdioms'
      topic = WikiTopic.get_or_insert(wiki_word,
                                      body='This topic is totally new!')
      assert topic.key().name() == 'CommonIdioms'
      assert topic.body == 'This topic is totally new!'

      # The second time through will just retrieve the entity.
      overwrite_topic = WikiTopic.get_or_insert(wiki_word,
                                      body='A totally different message!')
      assert topic.key().name() == 'CommonIdioms'
      assert topic.body == 'This topic is totally new!'

    Args:
      key_name: Key name to retrieve or create.
      **kwds: Keyword arguments to pass to the constructor of the model class
        if an instance for the specified key name does not already exist. If
        an instance with the supplied key_name and parent already exists, the
        rest of these arguments will be discarded.

    Returns:
      Existing instance of Model class with the specified key_name and parent
      or a new one that has just been created.

    Raises:
      TransactionFailedError if the specified Model instance could not be
      retrieved or created transactionally (due to high contention, etc).
    """
    def txn():
      entity = cls.get_by_key_name(key_name, parent=kwds.get('parent'))
      if entity is None:
        entity = cls(key_name=key_name, **kwds)
        entity.put()
      return entity
    return run_in_transaction(txn)

  @classmethod
  def all(cls, **kwds):
    """Returns a query over all instances of this model from the datastore.

    Returns:
      Query that will retrieve all instances from entity collection.
    """
    return Query(cls, **kwds)

  @classmethod
  def gql(cls, query_string, *args, **kwds):
    """Returns a query using GQL query string.

    See appengine/ext/gql for more information about GQL.

    Args:
      query_string: properly formatted GQL query string with the
        'SELECT * FROM <entity>' part omitted
      *args: rest of the positional arguments used to bind numeric references
        in the query.
      **kwds: dictionary-based arguments (for named parameters).
    """


    return GqlQuery('SELECT * FROM %s %s' % (cls.kind(), query_string),
                    *args, **kwds)

  @classmethod
  def _load_entity_values(cls, entity):
    """Load dynamic properties from entity.

    Loads attributes which are not defined as part of the entity in
    to the model instance.

    Args:
      entity: Entity which contain values to search dyanmic properties for.
    """
    entity_values = {}
    for prop in cls.properties().values():
      if prop.name in entity:
        try:
          value = entity[prop.name]
        except KeyError:

          entity_values[prop.name] = []
        else:
          if entity.is_projection():
            value = prop.make_value_from_datastore_index_value(value)
          else:
            value = prop.make_value_from_datastore(value)
          entity_values[prop.name] = value


    return entity_values

  @classmethod
  def from_entity(cls, entity):
    """Converts the entity representation of this model to an instance.

    Converts datastore.Entity instance to an instance of cls.

    Args:
      entity: Entity loaded directly from datastore.

    Raises:
      KindError when cls is incorrect model for entity.
    """
    if cls.kind() != entity.kind():
      raise KindError('Class %s cannot handle kind \'%s\'' %
                      (repr(cls), entity.kind()))

    entity_values = cls._load_entity_values(entity)
    if entity.key().has_id_or_name():
      entity_values['key'] = entity.key()
    return cls(None, _from_entity=entity, **entity_values)

  @classmethod
  def kind(cls):
    """Returns the datastore kind we use for this model.

    We just use the name of the model for now, ignoring potential collisions.
    """
    return cls.__name__

  @classmethod
  def entity_type(cls):
    """Soon to be removed alias for kind."""
    return cls.kind()

  @classmethod
  def properties(cls):
    """Returns a dictionary of all the properties defined for this model."""
    return dict(cls._properties)

  @classmethod
  def fields(cls):
    """Soon to be removed alias for properties."""
    return cls.properties()


def create_rpc(deadline=None, callback=None, read_policy=STRONG_CONSISTENCY):
  """Create an rpc for use in configuring datastore calls.

  NOTE: This functions exists for backwards compatibility.  Please use
  create_config() instead.  NOTE: the latter uses 'on_completion',
  which is a function taking an argument, wherease create_rpc uses
  'callback' which is a function without arguments.

  Args:
    deadline: float, deadline for calls in seconds.
    callback: callable, a callback triggered when this rpc completes,
      accepts one argument: the returned rpc.
    read_policy: flag, set to EVENTUAL_CONSISTENCY to enable eventually
      consistent reads

  Returns:
    A datastore.DatastoreRPC instance.
  """
  return datastore.CreateRPC(
      deadline=deadline, callback=callback, read_policy=read_policy)


def get_async(keys, **kwargs):
  """Asynchronously fetch the specified Model instance(s) from the datastore.

  Identical to db.get() except returns an asynchronous object. Call
  get_result() on the return value to block on the call and get the results.
  """
  keys, multiple = datastore.NormalizeAndTypeCheckKeys(keys)
  def extra_hook(entities):
    if not multiple and not entities:
      return None

    models = []
    for entity in entities:
      if entity is None:
        model = None
      else:
        cls1 = class_for_kind(entity.kind())
        model = cls1.from_entity(entity)
      models.append(model)

    if multiple:
      return models
    assert len(models) == 1
    return models[0]

  return datastore.GetAsync(keys, extra_hook=extra_hook, **kwargs)



def get(keys, **kwargs):
  """Fetch the specific Model instance with the given key from the datastore.

  We support Key objects and string keys (we convert them to Key objects
  automatically).

  Args:
    keys: Key within datastore entity collection to find; or string key;
      or list of Keys or string keys.
    config: datastore_rpc.Configuration to use for this request, must be
      specified as a keyword argument.

    Returns:
      If a single key was given: a Model instance associated with key
      if it exists in the datastore, otherwise None. If a list of keys was
      given: a list where list[i] is the Model instance for keys[i], or
      None if no instance exists.
  """
  return get_async(keys, **kwargs).get_result()


def put_async(models, **kwargs):
  """Asynchronously store one or more Model instances.

  Identical to db.put() except returns an asynchronous object. Call
  get_result() on the return value to block on the call and get the results.
  """
  models, multiple = datastore.NormalizeAndTypeCheck(models, Model)
  entities = [model._populate_internal_entity() for model in models]

  def extra_hook(keys):
    if multiple:
      return keys
    assert len(keys) == 1
    return keys[0]

  return datastore.PutAsync(entities, extra_hook=extra_hook, **kwargs)


def put(models, **kwargs):
  """Store one or more Model instances.

  Args:
    models: Model instance or list of Model instances.
    config: datastore_rpc.Configuration to use for this request, must be
      specified as a keyword argument.

  Returns:
    A Key if models is an instance, a list of Keys in the same order
    as models if models is a list.

  Raises:
    TransactionFailedError if the data could not be committed.
  """
  return put_async(models, **kwargs).get_result()




save = put


def delete_async(models, **kwargs):
  """Asynchronous version of delete one or more Model instances.

  Identical to db.delete() except returns an asynchronous object. Call
  get_result() on the return value to block on the call.
  """

  if isinstance(models, (basestring, Model, Key)):
    models = [models]
  else:
    try:
      models = iter(models)
    except TypeError:
      models = [models]
  keys = [_coerce_to_key(v) for v in models]

  return datastore.DeleteAsync(keys, **kwargs)


def delete(models, **kwargs):
  """Delete one or more Model instances.

  Args:
    models: Model instance, key, key string or iterable thereof.
    config: datastore_rpc.Configuration to use for this request, must be
      specified as a keyword argument.

  Raises:
    TransactionFailedError if the data could not be committed.
  """
  delete_async(models, **kwargs).get_result()


def allocate_ids_async(model, size, **kwargs):
  """Asynchronously allocates a range of IDs.

  Identical to allocate_ids() except returns an asynchronous object. Call
  get_result() on the return value to block on the call and return the result.
  """
  return datastore.AllocateIdsAsync(_coerce_to_key(model), size=size, **kwargs)


def allocate_ids(model, size, **kwargs):
  """Allocates a range of IDs of size for the model_key defined by model.

  Allocates a range of IDs in the datastore such that those IDs will not
  be automatically assigned to new entities. You can only allocate IDs
  for model keys from your app. If there is an error, raises a subclass of
  datastore_errors.Error.

  Args:
    model: Model instance, Key or string to serve as a template specifying the
      ID sequence in which to allocate IDs. Returned ids should only be used
      in entities with the same parent (if any) and kind as this key.
    size: Number of IDs to allocate.
    config: datastore_rpc.Configuration to use for this request.

  Returns:
    (start, end) of the allocated range, inclusive.
  """
  return allocate_ids_async(model, size, **kwargs).get_result()


def allocate_id_range(model, start, end, **kwargs):
  """Allocates a range of IDs with specific endpoints.

  Once these IDs have been allocated they may be provided manually to
  newly created entities.

  Since the datastore's automatic ID allocator will never assign
  a key to a new entity that will cause an existing entity to be
  overwritten, entities written to the given key range will never be
  overwritten. However, writing entities with manually assigned keys in this
  range may overwrite existing entities (or new entities written by a
  separate request) depending on the key range state returned.

  This method should only be used if you have an existing numeric id
  range that you want to reserve, e.g. bulk loading entities that already
  have IDs. If you don't care about which IDs you receive, use allocate_ids
  instead.

  Args:
    model: Model instance, Key or string to serve as a template specifying the
      ID sequence in which to allocate IDs. Allocated ids should only be used
      in entities with the same parent (if any) and kind as this key.
    start: first id of the range to allocate, inclusive.
    end: last id of the range to allocate, inclusive.
    config: datastore_rpc.Configuration to use for this request.

  Returns:
    One of (KEY_RANGE_EMPTY, KEY_RANGE_CONTENTION, KEY_RANGE_COLLISION). If not
    KEY_RANGE_EMPTY, this represents a potential issue with using the allocated
    key range.
  """
  key = _coerce_to_key(model)
  datastore.NormalizeAndTypeCheck((start, end), (int, long))
  if start < 1 or end < 1:
    raise BadArgumentError('Start %d and end %d must both be > 0.' %
                           (start, end))
  if start > end:
    raise BadArgumentError('Range end %d cannot be less than start %d.' %
                           (end, start))

  safe_start, _ = datastore.AllocateIds(key, max=end, **kwargs)



  race_condition = safe_start > start







  start_key = Key.from_path(key.kind(), start, parent=key.parent(),
                            _app=key.app(), namespace=key.namespace())
  end_key = Key.from_path(key.kind(), end, parent=key.parent(),
                          _app=key.app(), namespace=key.namespace())
  collision = (Query(keys_only=True, namespace=key.namespace(), _app=key.app())
                   .filter('__key__ >=', start_key)
                   .filter('__key__ <=', end_key).fetch(1))

  if collision:
    return KEY_RANGE_COLLISION
  elif race_condition:
    return KEY_RANGE_CONTENTION
  else:
    return KEY_RANGE_EMPTY


def _index_converter(index):
  return Index(index.Id(),
               index.Kind(),
               index.HasAncestor(),
               index.Properties())


def get_indexes_async(**kwargs):
  """Asynchronously retrieves the application indexes and their states.

  Identical to get_indexes() except returns an asynchronous object. Call
  get_result() on the return value to block on the call and get the results.
  """
  def extra_hook(indexes):
    return [(_index_converter(index), state) for index, state in indexes]

  return datastore.GetIndexesAsync(extra_hook=extra_hook, **kwargs)


def get_indexes(**kwargs):
  """Retrieves the application indexes and their states.

  Args:
    config: datastore_rpc.Configuration to use for this request, must be
      specified as a keyword argument.

  Returns:
    A list of (Index, Index.[BUILDING|SERVING|DELETING|ERROR]) tuples.
    An index can be in the following states:
      Index.BUILDING: Index is being built and therefore can not serve queries
      Index.SERVING: Index is ready to service queries
      Index.DELETING: Index is being deleted
      Index.ERROR: Index encounted an error in the BUILDING state
  """
  return get_indexes_async(**kwargs).get_result()


class Expando(Model):
  """Dynamically expandable model.

  An Expando does not require (but can still benefit from) the definition
  of any properties before it can be used to store information in the
  datastore.  Properties can be added to an expando object by simply
  performing an assignment.  The assignment of properties is done on
  an instance by instance basis, so it is possible for one object of an
  expando type to have different properties from another or even the same
  properties with different types.  It is still possible to define
  properties on an expando, allowing those properties to behave the same
  as on any other model.

  Example:
    import datetime

    class Song(db.Expando):
      title = db.StringProperty()

    crazy = Song(title='Crazy like a diamond',
                 author='Lucy Sky',
                 publish_date='yesterday',
                 rating=5.0)

    hoboken = Song(title='The man from Hoboken',
                   author=['Anthony', 'Lou'],
                   publish_date=datetime.datetime(1977, 5, 3))

    crazy.last_minute_note=db.Text('Get a train to the station.')

  Possible Uses:

    One use of an expando is to create an object without any specific
    structure and later, when your application mature and it in the right
    state, change it to a normal model object and define explicit properties.

  Additional exceptions for expando:

    Protected attributes (ones whose names begin with '_') cannot be used
    as dynamic properties.  These are names that are reserved for protected
    transient (non-persisted) attributes.

  Order of lookup:

    When trying to set or access an attribute value, any other defined
    properties, such as methods and other values in __dict__ take precedence
    over values in the datastore.

    1 - Because it is not possible for the datastore to know what kind of
        property to store on an undefined expando value, setting a property to
        None is the same as deleting it from the expando.

    2 - Persistent variables on Expando must not begin with '_'.  These
        variables considered to be 'protected' in Python, and are used
        internally.

    3 - Expando's dynamic properties are not able to store empty lists.
        Attempting to assign an empty list to a dynamic property will raise
        ValueError.  Static properties on Expando can still support empty
        lists but like normal Model properties is restricted from using
        None.
  """

  _dynamic_properties = None

  def __init__(self, parent=None, key_name=None, _app=None, **kwds):
    """Creates a new instance of this expando model.

    Args:
      parent: Parent instance for this instance or None, indicating a top-
        level instance.
      key_name: Name for new model instance.
      _app: Intentionally undocumented.
      args: Keyword arguments mapping to properties of model.
    """
    super(Expando, self).__init__(parent, key_name, _app, **kwds)
    self._dynamic_properties = {}
    for prop, value in kwds.iteritems():
      if prop not in self._all_properties and prop != 'key':



        if not (hasattr(getattr(type(self), prop, None), '__set__')):
          setattr(self, prop, value)
        else:
          check_reserved_word(prop)

  def __setattr__(self, key, value):
    """Dynamically set field values that are not defined.

    Tries to set the value on the object normally, but failing that
    sets the value on the contained entity.

    Args:
      key: Name of attribute.
      value: Value to set for attribute.  Must be compatible with
        datastore.

    Raises:
      ValueError on attempt to assign empty list.
    """
    check_reserved_word(key)
    if (key[:1] != '_' and



        not hasattr(getattr(type(self), key, None), '__set__')):
      if type(value) not in _ALLOWED_EXPANDO_PROPERTY_TYPES:
        raise TypeError("Expando cannot accept values of type '%s'." %
                        type(value).__name__)

      if self._dynamic_properties is None:
        self._dynamic_properties = {}
      self._dynamic_properties[key] = value
    else:
      super(Expando, self).__setattr__(key, value)

  def __getattribute__(self, key):
    """Get attribute from expando.

    Must be overridden to allow dynamic properties to obscure class attributes.
    Since all attributes are stored in self._dynamic_properties, the normal
    __getattribute__ does not attempt to access it until __setattr__ is called.
    By then, the static attribute being overwritten has already been located
    and returned from the call.

    This method short circuits the usual __getattribute__ call when finding a
    dynamic property and returns it to the user via __getattr__.  __getattr__
    is called to preserve backward compatibility with older Expando models
    that may have overridden the original __getattr__.

    NOTE: Access to properties defined by Python descriptors are not obscured
    because setting those attributes are done through the descriptor and does
    not place those attributes in self._dynamic_properties.
    """
    if not key.startswith('_'):
      dynamic_properties = self._dynamic_properties
      if dynamic_properties is not None and key in dynamic_properties:



        return self.__getattr__(key)

    return super(Expando, self).__getattribute__(key)



  def __getattr__(self, key):
    """If no explicit attribute defined, retrieve value from entity.

    Tries to get the value on the object normally, but failing that
    retrieves value from contained entity.

    Args:
      key: Name of attribute.

    Raises:
      AttributeError when there is no attribute for key on object or
        contained entity.
    """
    _dynamic_properties = self._dynamic_properties
    if _dynamic_properties is not None and key in _dynamic_properties:
      return _dynamic_properties[key]
    else:
      return getattr(super(Expando, self), key)

  def __delattr__(self, key):
    """Remove attribute from expando.

    Expando is not like normal entities in that undefined fields
    can be removed.

    Args:
      key: Dynamic property to be deleted.
    """
    if self._dynamic_properties and key in self._dynamic_properties:
      del self._dynamic_properties[key]
    else:
      object.__delattr__(self, key)

  def dynamic_properties(self):
    """Determine which properties are particular to instance of entity.

    Returns:
      Set of names which correspond only to the dynamic properties.
    """
    if self._dynamic_properties is None:
      return []
    return self._dynamic_properties.keys()

  def _to_entity(self, entity):
    """Store to entity, deleting dynamic properties that no longer exist.

    When the expando is saved, it is possible that a given property no longer
    exists.  In this case, the property will be removed from the saved instance.

    Args:
      entity: Entity which will receive dynamic properties.
    """
    super(Expando, self)._to_entity(entity)

    if self._dynamic_properties is None:
      self._dynamic_properties = {}

    for key, value in self._dynamic_properties.iteritems():
      entity[key] = value

    all_properties = set(self._dynamic_properties.iterkeys())
    all_properties.update(self._all_properties)
    for key in entity.keys():
      if key not in all_properties:
        del entity[key]

  @classmethod
  def _load_entity_values(cls, entity):
    """Load dynamic properties from entity.

    Expando needs to do a second pass to add the entity values which were
    ignored by Model because they didn't have an corresponding predefined
    property on the model.

    Args:
      entity: Entity which contain values to search dyanmic properties for.
    """
    entity_values = super(Expando, cls)._load_entity_values(entity)
    for key, value in entity.iteritems():
      if key not in entity_values:

        entity_values[str(key)] = value
    return entity_values


class _BaseQuery(object):
  """Base class for both Query and GqlQuery."""

  _last_raw_query = None
  _last_index_list = None
  _cursor = None
  _end_cursor = None

  def __init__(self, model_class=None):
    """Constructor.

    Args:
      model_class: Model class from which entities are constructed.
      keys_only: Whether the query should return full entities or only keys.
      compile: Whether the query should also return a compiled query.
      cursor: A compiled query from which to resume.
      namespace: The namespace to query.
    """
    self._model_class = model_class

  def is_keys_only(self):
    """Returns whether this query is keys only.

    Returns:
      True if this query returns keys, False if it returns entities.
    """
    raise NotImplementedError

  def projection(self):
    """Returns the tuple of properties in the projection or None.

    Projected results differ from normal results in multiple ways:
    - they only contain a portion of the original entity and cannot be put;
    - properties defined on the model, but not included in the projections will
      have a value of None, even if the property is required or has a default
      value;
    - multi-valued properties (such as a ListProperty) will only contain a single
      value.
    - dynamic properties not included in the projection will not appear
      on the model instance.
    - dynamic properties included in the projection are deserialized into
      their indexed type. Specifically one of str, bool, long, float, GeoPt, Key
      or User. If the original type is known, it can be restored using
      datastore_types.RestoreFromIndexValue.

    However, projection queries are significantly faster than normal queries.

    Projection queries on entities with multi-valued properties will return the
    same entity multiple times, once for each unique combination of values for
    properties included in the order, an inequaly property, or the projected
    properties.

    Returns:
      The list of properties in the projection, or None if no projection is
      set on this query.
    """
    raise NotImplementedError

  def is_distinct(self):
    """Returns true if the projection query should be distinct.

    This is equivalent to the SQL syntax: SELECT DISTINCT. It is only available
    for projection queries, it is not valid to specify distinct without also
    specifying projection properties.

    Distinct projection queries on entities with multi-valued properties will
    return the same entity multiple times, once for each unique combination of
    properties included in the projection.

    Returns:
      True if this projection query is distinct.
    """
    raise NotImplementedError

  def _get_query(self):
    """Subclass must override (and not call their super method).

    Returns:
      A datastore.Query instance representing the query.
    """
    raise NotImplementedError

  def run(self, **kwargs):
    """Iterator for this query.

    If you know the number of results you need, use run(limit=...) instead,
    or use a GQL query with a LIMIT clause. It's more efficient. If you want
    all results use run(batch_size=<large number>).

    Args:
      kwargs: Any keyword arguments accepted by datastore_query.QueryOptions().

    Returns:
      Iterator for this query.
    """
    raw_query = self._get_query()
    iterator = raw_query.Run(**kwargs)
    self._last_raw_query = raw_query

    keys_only = kwargs.get('keys_only')
    if keys_only is None:
      keys_only = self.is_keys_only()

    if keys_only:
      return iterator
    else:
      return _QueryIterator(self._model_class, iter(iterator))

  def __iter__(self):
    """Iterator for this query.

    If you know the number of results you need, consider fetch() instead,
    or use a GQL query with a LIMIT clause. It's more efficient.
    """
    return self.run()

  def __getstate__(self):
    state = self.__dict__.copy()
    state['_last_raw_query'] = None
    return state

  def get(self, **kwargs):
    """Get first result from this.

    Beware: get() ignores the LIMIT clause on GQL queries.

    Args:
      kwargs: Any keyword arguments accepted by datastore_query.QueryOptions().

    Returns:
      First result from running the query if there are any, else None.
    """
    results = self.run(limit=1, **kwargs)
    try:
      return results.next()
    except StopIteration:
      return None

  def count(self, limit=1000, **kwargs):
    """Number of entities this query fetches.

    Beware: count() ignores the LIMIT clause on GQL queries.

    Args:
      limit: A number. If there are more results than this, stop short and
        just return this number. Providing this argument makes the count
        operation more efficient.
      kwargs: Any keyword arguments accepted by datastore_query.QueryOptions().

    Returns:
      Number of entities this query fetches.
    """
    raw_query = self._get_query()
    result = raw_query.Count(limit=limit, **kwargs)
    self._last_raw_query = raw_query

    return result

  def fetch(self, limit, offset=0, **kwargs):
    """Return a list of items selected using SQL-like limit and offset.

    Always use run(limit=...) instead of fetch() when iterating over a query.

    Beware: offset must read and discard all skipped entities. Use
    cursor()/with_cursor() instead.

    Args:
      limit: Maximum number of results to return.
      offset: Optional number of results to skip first; default zero.
      kwargs: Any keyword arguments accepted by datastore_query.QueryOptions().

    Returns:
      A list of db.Model instances.  There may be fewer than 'limit'
      results if there aren't enough results to satisfy the request.
    """
    if limit is None:
      kwargs.setdefault('batch_size', datastore._MAX_INT_32)
    return list(self.run(limit=limit, offset=offset, **kwargs))

  def index_list(self):
    """Get the index list for an already executed query.

    Returns:
      A list of indexes used by the query.

    Raises:
      AssertionError: If the query has not been executed.
    """
    if self._last_raw_query is None:
      raise AssertionError('No index list because query has not been run.')
    if self._last_index_list is None:
      raw_index_list = self._last_raw_query.GetIndexList()
      self._last_index_list = [_index_converter(raw_index)
                               for raw_index in raw_index_list]
    return self._last_index_list

  def cursor(self):
    """Get a serialized cursor for an already executed query.

    The returned cursor effectively lets a future invocation of a similar
    query to begin fetching results immediately after the last returned
    result from this query invocation.

    Returns:
      A base64-encoded serialized cursor.

    Raises:
      AssertionError: If the query has not been executed.
    """
    if self._last_raw_query is None:
      raise AssertionError('No cursor available.')
    cursor = self._last_raw_query.GetCursor()
    return websafe_encode_cursor(cursor)

  def with_cursor(self, start_cursor=None, end_cursor=None):
    """Set the start and end of this query using serialized cursors.

    Conceptually cursors point to the position between the last result returned
    and the next result so running a query with each of the following cursors
    combinations will return all results in four chunks with no duplicate
    results:

      query.with_cursor(end_cursor=cursor1)
      query.with_cursors(cursor1, cursor2)
      query.with_cursors(cursor2, cursor3)
      query.with_cursors(start_cursor=cursor3)

    For example if the cursors pointed to:
      cursor:    1   2   3
      result: a b c d e f g h

    The results returned by these queries would be [a, b], [c, d], [e, f],
    [g, h] respectively.

    Cursors are pinned to the position just after the previous result (last
    result, exclusive), so if results are inserted or deleted between the time
    the cursor was made and these queries are executed, the cursors stay pinned
    to these positions. For example:

      delete(b, f, g, h)
      put(a1, b1, c1, d1)
      cursor:     1(b)      2(d)   3(f)
      result: a a1 b1 c c1 d d1 e

    The results returned by these queries would now be: [a, a1], [b1, c, c1, d],
    [d1, e], [] respectively.

    Args:
      start_cursor: The cursor position at which to start or None
      end_cursor: The cursor position at which to end or None

    Returns:
      This Query instance, for chaining.

    Raises:
      BadValueError when cursor is not valid.
    """
    if start_cursor is None:
      self._cursor = None
    else:
      self._cursor = websafe_decode_cursor(start_cursor)

    if end_cursor is None:
      self._end_cursor = None
    else:
      self._end_cursor = websafe_decode_cursor(end_cursor)

    return self

  def __getitem__(self, arg):
    """Support for query[index] and query[start:stop].

    Beware: this ignores the LIMIT clause on GQL queries.

    Args:
      arg: Either a single integer, corresponding to the query[index]
        syntax, or a Python slice object, corresponding to the
        query[start:stop] or query[start:stop:step] syntax.

    Returns:
      A single Model instance when the argument is a single integer.
      A list of Model instances when the argument is a slice.
    """

    if isinstance(arg, slice):
      start, stop, step = arg.start, arg.stop, arg.step
      if start is None:
        start = 0
      if stop is None:
        raise ValueError('Open-ended slices are not supported')
      if step is None:
        step = 1
      if start < 0 or stop < 0 or step != 1:
        raise ValueError(
            'Only slices with start>=0, stop>=0, step==1 are supported')
      limit = stop - start
      if limit < 0:
        return []
      return self.fetch(limit, start)
    elif isinstance(arg, (int, long)):
      if arg < 0:
        raise ValueError('Only indices >= 0 are supported')
      results = self.fetch(1, arg)
      if results:
        return results[0]
      else:
        raise IndexError('The query returned fewer than %d results' % (arg+1))
    else:
      raise TypeError('Only integer indices and slices are supported')


class _QueryIterator(object):
  """Wraps the datastore iterator to return Model instances.

  The datastore returns entities. We wrap the datastore iterator to
  return Model instances instead.
  """

  def __init__(self, model_class, datastore_iterator):
    """Iterator constructor

    Args:
      model_class: Model class from which entities are constructed.
      datastore_iterator: Underlying datastore iterator.
    """
    self.__model_class = model_class
    self.__iterator = datastore_iterator

  def __iter__(self):
    """Iterator on self.

    Returns:
      Self.
    """
    return self

  def next(self):
    """Get next Model instance in query results.

    Returns:
      Next model instance.

    Raises:
      StopIteration when there are no more results in query.
    """
    if self.__model_class is not None:
      return self.__model_class.from_entity(self.__iterator.next())
    else:
      while True:
        entity = self.__iterator.next()
        try:
          model_class = class_for_kind(entity.kind())
        except KindError:

          if datastore_types.RESERVED_PROPERTY_NAME.match(entity.kind()):
            continue
          raise
        else:
          return model_class.from_entity(entity)


def _normalize_query_parameter(value):
  """Make any necessary type conversions to a query parameter.

  The following conversions are made:
    - Model instances are converted to Key instances.  This is necessary so
      that querying reference properties will work.
    - datetime.date objects are converted to datetime.datetime objects (see
      _date_to_datetime for details on this conversion).  This is necessary so
      that querying date properties with date objects will work.
    - datetime.time objects are converted to datetime.datetime objects (see
      _time_to_datetime for details on this conversion).  This is necessary so
      that querying time properties with time objects will work.

  Args:
    value: The query parameter value.

  Returns:
    The input value, or a converted value if value matches one of the
    conversions specified above.
  """



  if isinstance(value, Model):
    value = value.key()

  if (isinstance(value, datetime.date) and
      not isinstance(value, datetime.datetime)):
    value = _date_to_datetime(value)
  elif isinstance(value, datetime.time):
    value = _time_to_datetime(value)
  return value


class Query(_BaseQuery):
  """A Query instance queries over instances of Models.

  You construct a query with a model class, like this:

     class Story(db.Model):
       title = db.StringProperty()
       date = db.DateTimeProperty()

     query = Query(Story)

  You modify a query with filters and orders like this:

     query.filter('title =', 'Foo')
     query.order('-date')
     query.ancestor(key_or_model_instance)

  Every query can return an iterator, so you access the results of a query
  by iterating over it:

     for story in query:
       print story.title

  For convenience, all of the filtering and ordering methods return "self",
  so the easiest way to use the query interface is to cascade all filters and
  orders in the iterator line like this:

     for story in Query(story).filter('title =', 'Foo').order('-date'):
       print story.title
  """


  _keys_only = False
  _distinct = False
  _projection = None
  _namespace = None
  _app = None
  __ancestor = None

  def __init__(self, model_class=None, keys_only=False, cursor=None,
               namespace=None, _app=None, distinct=False, projection=None):
    """Constructs a query over instances of the given Model.

    Args:
      model_class: Model class to build query for.
      keys_only: Whether the query should return full entities or only keys.
      projection: A tuple of strings representing the property names to include
        in the projection this query should produce or None. Setting a
        projection is similar to specifying 'SELECT prop1, prop2, ...' in SQL.
        See _BaseQuery.projection for details on projection queries.
      distinct: A boolean, true if the projection should be distinct.
        See _BaseQuery.is_distinct for details on distinct queries.
      cursor: A compiled query from which to resume.
      namespace: The namespace to use for this query.
    """
    super(Query, self).__init__(model_class)

    if keys_only:
      self._keys_only = True
    if projection:
      self._projection = projection
    if namespace is not None:
      self._namespace = namespace
    if _app is not None:
      self._app = _app
    if distinct:
      self._distinct = True

    self.__query_sets = [{}]
    self.__orderings = []
    self.with_cursor(cursor)

  def is_keys_only(self):
    return self._keys_only

  def projection(self):
    return self._projection

  def is_distinct(self):
    return self._distinct

  def _get_query(self,
                 _query_class=datastore.Query,
                 _multi_query_class=datastore.MultiQuery):






    queries = []
    for query_set in self.__query_sets:
      if self._model_class is not None:
        kind = self._model_class.kind()
      else:
        kind = None
      query = _query_class(kind,
                           query_set,
                           keys_only=self._keys_only,
                           projection=self._projection,
                           distinct=self._distinct,
                           compile=True,
                           cursor=self._cursor,
                           end_cursor=self._end_cursor,
                           namespace=self._namespace,
                           _app=self._app)
      query.Order(*self.__orderings)
      if self.__ancestor is not None:
        query.Ancestor(self.__ancestor)
      queries.append(query)


    if (_query_class != datastore.Query and
        _multi_query_class == datastore.MultiQuery):



      warnings.warn(
          'Custom _query_class specified without corresponding custom'
          ' _query_multi_class. Things will break if you use queries with'
          ' the "IN" or "!=" operators.', RuntimeWarning)
      if len(queries) > 1:
        raise datastore_errors.BadArgumentError(
            'Query requires multiple subqueries to satisfy. If _query_class'
            ' is overridden, _multi_query_class must also be overridden.')
    elif (_query_class == datastore.Query and
          _multi_query_class != datastore.MultiQuery):
      raise BadArgumentError('_query_class must also be overridden if'
                             ' _multi_query_class is overridden.')

    if len(queries) == 1:
      return queries[0]
    else:
      return _multi_query_class(queries, self.__orderings)

  def __filter_disjunction(self, operations, values):
    """Add a disjunction of several filters and several values to the query.

    This is implemented by duplicating queries and combining the
    results later.

    Args:
      operations: a string or list of strings. Each string contains a
        property name and an operator to filter by. The operators
        themselves must not require multiple queries to evaluate
        (currently, this means that 'in' and '!=' are invalid).

      values: a value or list of filter values, normalized by
        _normalize_query_parameter.
    """
    if not isinstance(operations, (list, tuple)):
      operations = [operations]
    if not isinstance(values, (list, tuple)):
      values = [values]

    new_query_sets = []
    for operation in operations:


      if operation.lower().endswith('in') or operation.endswith('!='):
        raise BadQueryError('Cannot use "in" or "!=" in a disjunction.')
      for query_set in self.__query_sets:
        for value in values:



          new_query_set = copy.deepcopy(query_set)
          datastore._AddOrAppend(new_query_set, operation, value)
          new_query_sets.append(new_query_set)
    self.__query_sets = new_query_sets

  def filter(self, property_operator, value):
    """Add filter to query.

    Args:
      property_operator: string with the property and operator to filter by.
      value: the filter value.

    Returns:
      Self to support method chaining.

    Raises:
      PropertyError if invalid property is provided.
    """
    match = _FILTER_REGEX.match(property_operator)
    prop = match.group(1)
    if match.group(3) is not None:
      operator = match.group(3)
    else:
      operator = '=='

    if self._model_class is None:
      if prop != datastore_types.KEY_SPECIAL_PROPERTY:
        raise BadQueryError(
            'Only %s filters are allowed on kindless queries.' %
            datastore_types.KEY_SPECIAL_PROPERTY)
    elif prop in self._model_class._unindexed_properties:
      raise PropertyError('Property \'%s\' is not indexed' % prop)

    if operator.lower() == 'in':
      if self._keys_only:
        raise BadQueryError('Keys only queries do not support IN filters.')
      elif not isinstance(value, (list, tuple)):
        raise BadValueError('Argument to the "in" operator must be a list')
      values = [_normalize_query_parameter(v) for v in value]
      self.__filter_disjunction(prop + ' =', values)
    else:
      if isinstance(value, (list, tuple)):
        raise BadValueError('Filtering on lists is not supported')
      if operator == '!=':
        if self._keys_only:
          raise BadQueryError('Keys only queries do not support != filters.')
        self.__filter_disjunction([prop + ' <', prop + ' >'],
                                  _normalize_query_parameter(value))
      else:
        value = _normalize_query_parameter(value)
        for query_set in self.__query_sets:
          datastore._AddOrAppend(query_set, property_operator, value)

    return self

  def order(self, property):
    """Set order of query result.

    To use descending order, prepend '-' (minus) to the property
    name, e.g., '-date' rather than 'date'.

    Args:
      property: Property to sort on.

    Returns:
      Self to support method chaining.

    Raises:
      PropertyError if invalid property is provided.
    """



    if property.startswith('-'):
      property = property[1:]
      order = datastore.Query.DESCENDING
    else:
      order = datastore.Query.ASCENDING

    if self._model_class is None:
      if (property != datastore_types.KEY_SPECIAL_PROPERTY or
          order != datastore.Query.ASCENDING):
        raise BadQueryError(
            'Only %s ascending orders are supported on kindless queries' %
            datastore_types.KEY_SPECIAL_PROPERTY)
    else:

      if not issubclass(self._model_class, Expando):
        if (property not in self._model_class._all_properties and
            property not in datastore_types._SPECIAL_PROPERTIES):
          raise PropertyError('Invalid property name \'%s\'' % property)

      if property in self._model_class._unindexed_properties:
        raise PropertyError('Property \'%s\' is not indexed' % property)

    self.__orderings.append((property, order))
    return self

  def ancestor(self, ancestor):
    """Sets an ancestor for this query.

    This restricts the query to only return results that descend from
    a given model instance. In other words, all of the results will
    have the ancestor as their parent, or parent's parent, etc.  The
    ancestor itself is also a possible result!

    Args:
      ancestor: Model or Key (that has already been saved)

    Returns:
      Self to support method chaining.

    Raises:
      TypeError if the argument isn't a Key or Model; NotSavedError
      if it is, but isn't saved yet.
    """
    if isinstance(ancestor, datastore.Key):
      if ancestor.has_id_or_name():
        self.__ancestor = ancestor
      else:
        raise NotSavedError()
    elif isinstance(ancestor, Model):
      if ancestor.has_key():
        self.__ancestor = ancestor.key()
      else:
        raise NotSavedError()
    else:
      raise TypeError('ancestor should be Key or Model')
    return self


class GqlQuery(_BaseQuery):
  """A Query class that uses GQL query syntax instead of .filter() etc."""



  def __init__(self, query_string, *args, **kwds):
    """Constructor.

    Args:
      query_string: Properly formatted GQL query string.
      *args: Positional arguments used to bind numeric references in the query.
      **kwds: Dictionary-based arguments for named references.

    Raises:
      PropertyError if the query filters or sorts on a property that's not
      indexed.
    """


    from google.appengine.ext import gql
    app = kwds.pop('_app', None)
    namespace = None
    if isinstance(app, tuple):
      if len(app) != 2:
        raise BadArgumentError('_app must have 2 values if type is tuple.')
      app, namespace = app

    self._proto_query = gql.GQL(query_string, _app=app, namespace=namespace)
    if self._proto_query._kind is not None:
      model_class = class_for_kind(self._proto_query._kind)
    else:
      model_class = None

    super(GqlQuery, self).__init__(model_class)

    if model_class is not None:

      for property, unused in (self._proto_query.filters().keys() +
                               self._proto_query.orderings()):
        if property in model_class._unindexed_properties:
          raise PropertyError('Property \'%s\' is not indexed' % property)

    self.bind(*args, **kwds)

  def is_keys_only(self):
    return self._proto_query._keys_only

  def projection(self):
    return self._proto_query.projection()

  def is_distinct(self):
    return self._proto_query.is_distinct()

  def bind(self, *args, **kwds):
    """Bind arguments (positional or keyword) to the query.

    Note that you can also pass arguments directly to the query
    constructor.  Each time you call bind() the previous set of
    arguments is replaced with the new set.  This is useful because
    the hard work in in parsing the query; so if you expect to be
    using the same query with different sets of arguments, you should
    hold on to the GqlQuery() object and call bind() on it each time.

    Args:
      *args: Positional arguments used to bind numeric references in the query.
      **kwds: Dictionary-based arguments for named references.
    """
    self._args = []
    for arg in args:
      self._args.append(_normalize_query_parameter(arg))
    self._kwds = {}
    for name, arg in kwds.iteritems():
      self._kwds[name] = _normalize_query_parameter(arg)

  def run(self, **kwargs):
    """Iterator for this query that handles the LIMIT clause property.

    If the GQL query string contains a LIMIT clause, this function fetches
    all results before returning an iterator. Otherwise results are retrieved
    in batches by the iterator.

    Args:
      kwargs: Any keyword arguments accepted by datastore_query.QueryOptions().

    Returns:
      Iterator for this query.
    """
    if self._proto_query.limit() > 0:
      kwargs.setdefault('limit', self._proto_query.limit())
    kwargs.setdefault('offset', self._proto_query.offset())
    return _BaseQuery.run(self, **kwargs)

  def _get_query(self):
    return self._proto_query.Bind(self._args, self._kwds,
                                  self._cursor, self._end_cursor)


class UnindexedProperty(Property):
  """A property that isn't indexed by either built-in or composite indices.

  TextProperty and BlobProperty derive from this class.
  """
  def __init__(self, *args, **kwds):
    """Construct property. See the Property class for details.

    Raises:
      ConfigurationError if indexed=True.
    """
    self._require_parameter(kwds, 'indexed', False)



    kwds['indexed'] = True
    super(UnindexedProperty, self).__init__(*args, **kwds)

  def validate(self, value):
    """Validate property.

    Returns:
      A valid value.

    Raises:
      BadValueError if property is not an instance of data_type.
    """
    if value is not None and not isinstance(value, self.data_type):
      try:
        value = self.data_type(value)
      except TypeError, err:



        raise BadValueError('Property %s must be convertible '
                            'to a %s instance (%s)' %
                            (self.name, self.data_type.__name__, err))
    value = super(UnindexedProperty, self).validate(value)
    if value is not None and not isinstance(value, self.data_type):
      raise BadValueError('Property %s must be a %s instance' %
                          (self.name, self.data_type.__name__))
    return value


class TextProperty(UnindexedProperty):
  """A string that can be longer than 1500 bytes."""

  data_type = Text


class StringProperty(Property):
  """A textual property, which can be multi- or single-line."""

  def __init__(self, verbose_name=None, multiline=False, **kwds):
    """Construct string property.

    Args:
      verbose_name: Verbose name is always first parameter.
      multi-line: Carriage returns permitted in property.
    """
    super(StringProperty, self).__init__(verbose_name, **kwds)
    self.multiline = multiline

  def validate(self, value):
    """Validate string property.

    Returns:
      A valid value.

    Raises:
      BadValueError if property is not multi-line but value is.
    """
    value = super(StringProperty, self).validate(value)
    if value is not None and not isinstance(value, basestring):
      raise BadValueError(
          'Property %s must be a str or unicode instance, not a %s'
          % (self.name, type(value).__name__))
    if not self.multiline and value and value.find('\n') != -1:
      raise BadValueError('Property %s is not multi-line' % self.name)
    if value is not None and len(value) > self.MAX_LENGTH:
      raise BadValueError(
          'Property %s is %d bytes long; it must be %d or less.'
          % (self.name, len(value), self.MAX_LENGTH))
    return value

  MAX_LENGTH = 1500
  data_type = basestring


class _CoercingProperty(Property):
  """A Property subclass that extends validate() to coerce to self.data_type."""

  def validate(self, value):
    """Coerce values (except None) to self.data_type.

    Args:
      value: The value to be validated and coerced.

    Returns:
      The coerced and validated value.  It is guaranteed that this is
      either None or an instance of self.data_type; otherwise an exception
      is raised.

    Raises:
      BadValueError if the value could not be validated or coerced.
    """
    value = super(_CoercingProperty, self).validate(value)
    if value is not None and not isinstance(value, self.data_type):

      value = self.data_type(value)
    return value


class CategoryProperty(_CoercingProperty):
  """A property whose values are Category instances."""

  data_type = Category


class LinkProperty(_CoercingProperty):
  """A property whose values are Link instances."""

  def validate(self, value):
    value = super(LinkProperty, self).validate(value)
    if value is not None:


      scheme, netloc, path, query, fragment = urlparse.urlsplit(value)
      if not scheme or not netloc:
        raise BadValueError('Property %s must be a full URL (\'%s\')' %
                            (self.name, value))
    return value

  data_type = Link

URLProperty = LinkProperty


class EmailProperty(_CoercingProperty):
  """A property whose values are Email instances."""

  data_type = Email


class GeoPtProperty(_CoercingProperty):
  """A property whose values are GeoPt instances."""

  data_type = GeoPt


class IMProperty(_CoercingProperty):
  """A property whose values are IM instances."""

  data_type = IM


class PhoneNumberProperty(_CoercingProperty):
  """A property whose values are PhoneNumber instances."""

  data_type = PhoneNumber


class PostalAddressProperty(_CoercingProperty):
  """A property whose values are PostalAddress instances."""

  data_type = PostalAddress


class BlobProperty(UnindexedProperty):
  """A byte string that can be longer than 1500 bytes."""

  data_type = Blob


class ByteStringProperty(Property):
  """A short (<=1500 bytes) byte string.

  This type should be used for short binary values that need to be indexed. If
  you do not require indexing (regardless of length), use BlobProperty instead.
  """

  def validate(self, value):
    """Validate ByteString property.

    Returns:
      A valid value.

    Raises:
      BadValueError if property is not instance of 'ByteString'.
    """
    if value is not None and not isinstance(value, ByteString):
      try:
        value = ByteString(value)
      except TypeError, err:
        raise BadValueError('Property %s must be convertible '
                            'to a ByteString instance (%s)' % (self.name, err))
    value = super(ByteStringProperty, self).validate(value)
    if value is not None and not isinstance(value, ByteString):
      raise BadValueError('Property %s must be a ByteString instance'
                          % self.name)
    if value is not None and len(value) > self.MAX_LENGTH:
      raise BadValueError(
          'Property %s is %d bytes long; it must be %d or less.'
          % (self.name, len(value), self.MAX_LENGTH))
    return value

  MAX_LENGTH = 1500
  data_type = ByteString


class DateTimeProperty(Property):
  """The base class of all of our date/time properties.

  We handle common operations, like converting between time tuples and
  datetime instances.
  """

  def __init__(self, verbose_name=None, auto_now=False, auto_now_add=False,
               **kwds):
    """Construct a DateTimeProperty

    Args:
      verbose_name: Verbose name is always first parameter.
      auto_now: Date/time property is updated with the current time every time
        it is saved to the datastore.  Useful for properties that want to track
        the modification time of an instance.
      auto_now_add: Date/time is set to the when its instance is created.
        Useful for properties that record the creation time of an entity.
    """
    super(DateTimeProperty, self).__init__(verbose_name, **kwds)
    self.auto_now = auto_now
    self.auto_now_add = auto_now_add

  def validate(self, value):
    """Validate datetime.

    Returns:
      A valid value.

    Raises:
      BadValueError if property is not instance of 'datetime'.
    """
    value = super(DateTimeProperty, self).validate(value)
    if value and not isinstance(value, self.data_type):
      raise BadValueError('Property %s must be a %s, but was %r' %
                          (self.name, self.data_type.__name__, value))
    return value

  def default_value(self):
    """Default value for datetime.

    Returns:
      value of now() as appropriate to the date-time instance if auto_now
      or auto_now_add is set, else user configured default value implementation.
    """
    if self.auto_now or self.auto_now_add:
      return self.now()
    return Property.default_value(self)

  def get_updated_value_for_datastore(self, model_instance):
    """Get new value for property to send to datastore.

    Returns:
      now() as appropriate to the date-time instance in the odd case where
      auto_now is set to True, else AUTO_UPDATE_UNCHANGED.
    """
    if self.auto_now:
      return self.now()
    return AUTO_UPDATE_UNCHANGED

  data_type = datetime.datetime

  @staticmethod
  def now():
    """Get now as a full datetime value.

    Returns:
      'now' as a whole timestamp, including both time and date.
    """
    return datetime.datetime.utcnow()


def _date_to_datetime(value):
  """Convert a date to a datetime for datastore storage.

  Args:
    value: A datetime.date object.

  Returns:
    A datetime object with time set to 0:00.
  """
  assert isinstance(value, datetime.date)
  return datetime.datetime(value.year, value.month, value.day)


def _time_to_datetime(value):
  """Convert a time to a datetime for datastore storage.

  Args:
    value: A datetime.time object.

  Returns:
    A datetime object with date set to 1970-01-01.
  """
  assert isinstance(value, datetime.time)
  return datetime.datetime(1970, 1, 1,
                           value.hour, value.minute, value.second,
                           value.microsecond)


class DateProperty(DateTimeProperty):
  """A date property, which stores a date without a time."""








  @staticmethod
  def now():
    """Get now as a date datetime value.

    Returns:
      'date' part of 'now' only.
    """
    return datetime.datetime.utcnow().date()

  def validate(self, value):
    """Validate date.

    Returns:
      A valid value.

    Raises:
      BadValueError if property is not instance of 'date',
      or if it is an instance of 'datetime' (which is a subclass
      of 'date', but for all practical purposes a different type).
    """
    value = super(DateProperty, self).validate(value)
    if isinstance(value, datetime.datetime):
      raise BadValueError('Property %s must be a %s, not a datetime' %
                          (self.name, self.data_type.__name__))
    return value

  def get_updated_value_for_datastore(self, model_instance):
    """Get new value for property to send to datastore.

    Returns:
      now() as appropriate to the date instance in the odd case where
      auto_now is set to True, else AUTO_UPDATE_UNCHANGED.
    """
    if self.auto_now:
      return _date_to_datetime(self.now())
    return AUTO_UPDATE_UNCHANGED

  def get_value_for_datastore(self, model_instance):
    """Get value from property to send to datastore.

    We retrieve a datetime.date from the model instance and return a
    datetime.datetime instance with the time set to zero.

    See base class method documentation for details.
    """
    value = super(DateProperty, self).get_value_for_datastore(model_instance)
    if value is not None:
      assert isinstance(value, datetime.date)
      value = _date_to_datetime(value)
    return value

  def make_value_from_datastore(self, value):
    """Native representation of this property.

    We receive a datetime.datetime retrieved from the entity and return
    a datetime.date instance representing its date portion.

    See base class method documentation for details.
    """
    if value is not None:
      assert isinstance(value, datetime.datetime)
      value = value.date()
    return value

  data_type = datetime.date


class TimeProperty(DateTimeProperty):
  """A time property, which stores a time without a date."""








  @staticmethod
  def now():
    """Get now as a time datetime value.

    Returns:
      'time' part of 'now' only.
    """
    return datetime.datetime.utcnow().time()

  def empty(self, value):
    """Is time property empty.

    "0:0" (midnight) is not an empty value.

    Returns:
      True if value is None, else False.
    """
    return value is None

  def get_updated_value_for_datastore(self, model_instance):
    """Get new value for property to send to datastore.

    Returns:
      now() as appropriate to the time instance in the odd case where
      auto_now is set to True, else AUTO_UPDATE_UNCHANGED.
    """
    if self.auto_now:
      return _time_to_datetime(self.now())
    return AUTO_UPDATE_UNCHANGED

  def get_value_for_datastore(self, model_instance):
    """Get value from property to send to datastore.

    We retrieve a datetime.time from the model instance and return a
    datetime.datetime instance with the date set to 1/1/1970.

    See base class method documentation for details.
    """
    value = super(TimeProperty, self).get_value_for_datastore(model_instance)
    if value is not None:
      assert isinstance(value, datetime.time), repr(value)
      value = _time_to_datetime(value)
    return value

  def make_value_from_datastore(self, value):
    """Native representation of this property.

    We receive a datetime.datetime retrieved from the entity and return
    a datetime.date instance representing its time portion.

    See base class method documentation for details.
    """
    if value is not None:
      assert isinstance(value, datetime.datetime)
      value = value.time()
    return value

  data_type = datetime.time


class IntegerProperty(Property):
  """An integer property."""

  def validate(self, value):
    """Validate integer property.

    Returns:
      A valid value.

    Raises:
      BadValueError if value is not an integer or long instance.
    """
    value = super(IntegerProperty, self).validate(value)
    if value is None:
      return value





    if not isinstance(value, (int, long)) or isinstance(value, bool):
      raise BadValueError('Property %s must be an int or long, not a %s'
                          % (self.name, type(value).__name__))
    if value < -0x8000000000000000 or value > 0x7fffffffffffffff:
      raise BadValueError('Property %s must fit in 64 bits' % self.name)
    return value

  data_type = int

  def empty(self, value):
    """Is integer property empty.

    0 is not an empty value.

    Returns:
      True if value is None, else False.
    """
    return value is None


class RatingProperty(_CoercingProperty, IntegerProperty):
  """A property whose values are Rating instances."""

  data_type = Rating


class FloatProperty(Property):
  """A float property."""

  def validate(self, value):
    """Validate float.

    Returns:
      A valid value.

    Raises:
      BadValueError if property is not instance of 'float'.
    """
    value = super(FloatProperty, self).validate(value)
    if value is not None and not isinstance(value, float):
      raise BadValueError('Property %s must be a float' % self.name)
    return value

  data_type = float

  def empty(self, value):
    """Is float property empty.

    0.0 is not an empty value.

    Returns:
      True if value is None, else False.
    """
    return value is None


class BooleanProperty(Property):
  """A boolean property."""

  def validate(self, value):
    """Validate boolean.

    Returns:
      A valid value.

    Raises:
      BadValueError if property is not instance of 'bool'.
    """
    value = super(BooleanProperty, self).validate(value)
    if value is not None and not isinstance(value, bool):
      raise BadValueError('Property %s must be a bool' % self.name)
    return value

  data_type = bool

  def empty(self, value):
    """Is boolean property empty.

    False is not an empty value.

    Returns:
      True if value is None, else False.
    """
    return value is None


class UserProperty(Property):
  """A user property."""

  def __init__(self,
               verbose_name=None,
               name=None,
               required=False,
               validator=None,
               choices=None,
               auto_current_user=False,
               auto_current_user_add=False,
               indexed=True):
    """Initializes this Property with the given options.

    Note: this does *not* support the 'default' keyword argument.
    Use auto_current_user_add=True instead.

    Args:
      verbose_name: User friendly name of property.
      name: Storage name for property.  By default, uses attribute name
        as it is assigned in the Model sub-class.
      required: Whether property is required.
      validator: User provided method used for validation.
      choices: User provided set of valid property values.
      auto_current_user: If true, the value is set to the current user
        each time the entity is written to the datastore.
      auto_current_user_add: If true, the value is set to the current user
        the first time the entity is written to the datastore.
      indexed: Whether property is indexed.
    """
    super(UserProperty, self).__init__(verbose_name, name,
                                       required=required,
                                       validator=validator,
                                       choices=choices,
                                       indexed=indexed)
    self.auto_current_user = auto_current_user
    self.auto_current_user_add = auto_current_user_add

  def validate(self, value):
    """Validate user.

    Returns:
      A valid value.

    Raises:
      BadValueError if property is not instance of 'User'.
    """
    value = super(UserProperty, self).validate(value)
    if value is not None and not isinstance(value, users.User):
      raise BadValueError('Property %s must be a User' % self.name)
    return value

  def default_value(self):
    """Default value for user.

    Returns:
      Value of users.get_current_user() if auto_current_user or
      auto_current_user_add is set; else None. (But *not* the default
      implementation, since we don't support the 'default' keyword
      argument.)
    """
    if self.auto_current_user or self.auto_current_user_add:
      return users.get_current_user()
    return None

  def get_updated_value_for_datastore(self, model_instance):
    """Get new value for property to send to datastore.

    Returns:
      Value of users.get_current_user() if auto_current_user is set;
      else AUTO_UPDATE_UNCHANGED.
    """
    if self.auto_current_user:
      return users.get_current_user()
    return AUTO_UPDATE_UNCHANGED

  data_type = users.User


class ListProperty(Property):
  """A property that stores a list of things.

  This is a parameterized property; the parameter must be a valid
  non-list data type, and all items must conform to this type.
  """

  _write_empty_list = False

  def __init__(
      self, item_type, verbose_name=None, default=None,
      write_empty_list=None, **kwds):
    """Construct ListProperty.

    Args:
      item_type: Type for the list items; must be one of the allowed property
        types.
      verbose_name: Optional verbose name.
      write_empty_list: Optional whether to write empty list properties or no
        property
      default: Optional default value; if omitted, an empty list is used.
      **kwds: Optional additional keyword arguments, passed to base class.

    Note that the only permissible value for 'required' is True.
    """
    if item_type is str:
      item_type = basestring
    if not isinstance(item_type, type):
      raise TypeError('Item type should be a type object')
    if item_type not in _ALLOWED_PROPERTY_TYPES:
      raise ValueError('Item type %s is not acceptable' % item_type.__name__)
    if issubclass(item_type, (Blob, Text)):
      self._require_parameter(kwds, 'indexed', False)



      kwds['indexed'] = True
    self._require_parameter(kwds, 'required', True)
    if default is None:
      default = []
    self.item_type = item_type
    if write_empty_list is not None:
      self._write_empty_list = write_empty_list
    super(ListProperty, self).__init__(verbose_name,
                                       default=default,
                                       **kwds)

  def validate(self, value):
    """Validate list.

    Returns:
      A valid value.

    Raises:
      BadValueError if property is not a list whose items are instances of
      the item_type given to the constructor.
    """
    value = super(ListProperty, self).validate(value)
    if value is not None:
      if not isinstance(value, list):
        raise BadValueError('Property %s must be a list' % self.name)

      value = self.validate_list_contents(value)
    return value

  def _load(self, model_instance, value):

    if not isinstance(value, list):
      value = [value]
    return super(ListProperty, self)._load(model_instance, value)

  def validate_list_contents(self, value):
    """Validates that all items in the list are of the correct type.

    Returns:
      The validated list.

    Raises:
      BadValueError if the list has items are not instances of the
      item_type given to the constructor.
    """
    if self.item_type in (int, long):
      item_type = (int, long)
    else:
      item_type = self.item_type

    for item in value:
      if not isinstance(item, item_type):
        if item_type == (int, long):
          raise BadValueError('Items in the %s list must all be integers.' %
                              self.name)
        else:
          raise BadValueError(
              'Items in the %s list must all be %s instances' %
              (self.name, self.item_type.__name__))
    return value

  def empty(self, value):
    """Is list property empty.

    [] is not an empty value.

    Returns:
      True if value is None, else false.
    """
    return value is None

  data_type = list

  def default_value(self):
    """Default value for list.

    Because the property supplied to 'default' is a static value,
    that value must be shallow copied to prevent all fields with
    default values from sharing the same instance.

    Returns:
      Copy of the default value.
    """
    return list(super(ListProperty, self).default_value())

  def get_value_for_datastore(self, model_instance):
    """Get value from property to send to datastore.

    Returns:
      validated list appropriate to save in the datastore.
    """
    value = super(ListProperty, self).get_value_for_datastore(model_instance)
    if not value:
      return value
    value = self.validate_list_contents(value)
    if self.validator:
      self.validator(value)









    if self.item_type == datetime.date:
      value = map(_date_to_datetime, value)
    elif self.item_type == datetime.time:
      value = map(_time_to_datetime, value)

    return value

  def make_value_from_datastore(self, value):
    """Native representation of this property.

    If this list is a list of datetime.date or datetime.time, we convert
    the list of datetime.datetime retrieved from the entity into
    datetime.date or datetime.time.

    See base class method documentation for details.
    """

    if self.item_type == datetime.date:
      for v in value:
        assert isinstance(v, datetime.datetime)
      value = map(lambda x: x.date(), value)
    elif self.item_type == datetime.time:
      for v in value:
        assert isinstance(v, datetime.datetime)
      value = map(lambda x: x.time(), value)

    return value

  def make_value_from_datastore_index_value(self, index_value):
    value = [datastore_types.RestoreFromIndexValue(index_value, self.item_type)]
    return self.make_value_from_datastore(value)


class StringListProperty(ListProperty):
  """A property that stores a list of strings.

  A shorthand for the most common type of ListProperty.
  """

  def __init__(self, verbose_name=None, default=None, write_empty_list=None,
               **kwds):
    """Construct StringListProperty.

    Args:
      verbose_name: Optional verbose name.
      default: Optional default value; if omitted, an empty list is used.
      **kwds: Optional additional keyword arguments, passed to ListProperty().
    """
    super(StringListProperty, self).__init__(basestring,
                                             verbose_name=verbose_name,
                                             default=default,
                                             write_empty_list=write_empty_list,
                                             **kwds)


class ReferenceProperty(Property):
  """A property that represents a many-to-one reference to another model.

  For example, a reference property in model A that refers to model B forms
  a many-to-one relationship from A to B: every instance of A refers to a
  single B instance, and every B instance can have many A instances refer
  to it.
  """

  def __init__(self,
               reference_class=None,
               verbose_name=None,
               collection_name=None,
               **attrs):
    """Construct ReferenceProperty.

    Args:
      reference_class: Which model class this property references.
      verbose_name: User friendly name of property.
      collection_name: If provided, alternate name of collection on
        reference_class to store back references.  Use this to allow
        a Model to have multiple fields which refer to the same class.
    """
    super(ReferenceProperty, self).__init__(verbose_name, **attrs)

    self.collection_name = collection_name

    if reference_class is None:
      reference_class = Model
    if not ((isinstance(reference_class, type) and
             issubclass(reference_class, Model)) or
            reference_class is _SELF_REFERENCE):
      raise KindError('reference_class must be Model or _SELF_REFERENCE')

    self.reference_class = self.data_type = reference_class

  def make_value_from_datastore_index_value(self, index_value):
    value = datastore_types.RestoreFromIndexValue(index_value, Key)
    return self.make_value_from_datastore(value)

  def __property_config__(self, model_class, property_name):
    """Loads all of the references that point to this model.

    We need to do this to create the ReverseReferenceProperty properties for
    this model and create the <reference>_set attributes on the referenced
    model, e.g.:

       class Story(db.Model):
         title = db.StringProperty()
       class Comment(db.Model):
         story = db.ReferenceProperty(Story)
       story = Story.get(id)
       print [c for c in story.comment_set]

    In this example, the comment_set property was created based on the reference
    from Comment to Story (which is inherently one to many).

    Args:
      model_class: Model class which will have its reference properties
        initialized.
      property_name: Name of property being configured.

    Raises:
      DuplicatePropertyError if referenced class already has the provided
        collection name as a property.
    """
    super(ReferenceProperty, self).__property_config__(model_class,
                                                       property_name)

    if self.reference_class is _SELF_REFERENCE:
      self.reference_class = self.data_type = model_class

    if self.collection_name is None:
      self.collection_name = '%s_set' % (model_class.__name__.lower())
    existing_prop = getattr(self.reference_class, self.collection_name, None)
    if existing_prop is not None:






      if not (isinstance(existing_prop, _ReverseReferenceProperty) and
              existing_prop._prop_name == property_name and
              existing_prop._model.__name__ == model_class.__name__ and
              existing_prop._model.__module__ == model_class.__module__):
        raise DuplicatePropertyError('Class %s already has property %s '
                                   % (self.reference_class.__name__,
                                      self.collection_name))
    setattr(self.reference_class,
            self.collection_name,
            _ReverseReferenceProperty(model_class, property_name))

  def __get__(self, model_instance, model_class):
    """Get reference object.

    This method will fetch unresolved entities from the datastore if
    they are not already loaded.

    Returns:
      ReferenceProperty to Model object if property is set, else None.

    Raises:
      ReferencePropertyResolveError: if the referenced model does not exist.
    """
    if model_instance is None:
      return self


    if hasattr(model_instance, self.__id_attr_name()):
      reference_id = getattr(model_instance, self.__id_attr_name())
    else:
      reference_id = None
    if reference_id is not None:
      resolved = getattr(model_instance, self.__resolved_attr_name())
      if resolved is not None:
        return resolved
      else:
        instance = get(reference_id)
        if instance is None:
          raise ReferencePropertyResolveError(
              'ReferenceProperty failed to be resolved: %s' %
              reference_id.to_path())
        setattr(model_instance, self.__resolved_attr_name(), instance)
        return instance
    else:
      return None

  def __set__(self, model_instance, value):
    """Set reference."""



    value = self.validate(value)
    if value is not None:
      if isinstance(value, datastore.Key):

        setattr(model_instance, self.__id_attr_name(), value)
        setattr(model_instance, self.__resolved_attr_name(), None)
      else:
        setattr(model_instance, self.__id_attr_name(), value.key())
        setattr(model_instance, self.__resolved_attr_name(), value)
    else:
      setattr(model_instance, self.__id_attr_name(), None)
      setattr(model_instance, self.__resolved_attr_name(), None)

  def get_value_for_datastore(self, model_instance):
    """Get key of reference rather than reference itself."""

    return getattr(model_instance, self.__id_attr_name())

  def validate(self, value):
    """Validate reference.

    Returns:
      A valid value.

    Raises:
      BadValueError for the following reasons:
        - Value is not saved.
        - Object not of correct model type for reference.
    """
    if isinstance(value, datastore.Key):
      return value

    if value is not None and not value.has_key():
      raise BadValueError(
          '%s instance must have a complete key before it can be stored as a '
          'reference' % self.reference_class.kind())

    value = super(ReferenceProperty, self).validate(value)

    if value is not None and not isinstance(value, self.reference_class):
      raise KindError('Property %s must be an instance of %s' %
                      (self.name, self.reference_class.kind()))

    return value

  def __id_attr_name(self):
    """Get attribute of referenced id.

    Returns:
      Attribute where to store id of referenced entity.
    """
    return self._attr_name()

  def __resolved_attr_name(self):
    """Get attribute of resolved attribute.

    The resolved attribute is where the actual loaded reference instance is
    stored on the referring model instance.

    Returns:
      Attribute name of where to store resolved reference model instance.
    """
    return '_RESOLVED' + self._attr_name()



Reference = ReferenceProperty


def SelfReferenceProperty(verbose_name=None, collection_name=None, **attrs):
  """Create a self reference.

  Function for declaring a self referencing property on a model.

  Example:
    class HtmlNode(db.Model):
      parent = db.SelfReferenceProperty('Parent', 'children')

  Args:
    verbose_name: User friendly name of property.
    collection_name: Name of collection on model.

  Raises:
    ConfigurationError if reference_class provided as parameter.
  """
  if 'reference_class' in attrs:
    raise ConfigurationError(
        'Do not provide reference_class to self-reference.')
  return ReferenceProperty(_SELF_REFERENCE,
                           verbose_name,
                           collection_name,
                           **attrs)



SelfReference = SelfReferenceProperty


class _ReverseReferenceProperty(Property):
  """The inverse of the Reference property above.

  We construct reverse references automatically for the model to which
  the Reference property is pointing to create the one-to-many property for
  that model.  For example, if you put a Reference property in model A that
  refers to model B, we automatically create a _ReverseReference property in
  B called a_set that can fetch all of the model A instances that refer to
  that instance of model B.
  """

  def __init__(self, model, prop):
    """Constructor for reverse reference.

    Constructor does not take standard values of other property types.

    Args:
      model: Model class that this property is a collection of.
      property: Name of foreign property on referred model that points back
        to this properties entity.
    """
    self.__model = model
    self.__property = prop

  @property
  def _model(self):
    """Internal helper to access the model class, read-only."""
    return self.__model

  @property
  def _prop_name(self):
    """Internal helper to access the property name, read-only."""
    return self.__property

  def __get__(self, model_instance, model_class):
    """Fetches collection of model instances of this collection property."""
    if model_instance is not None:
      query = Query(self.__model)
      return query.filter(self.__property + ' =', model_instance.key())
    else:
      return self

  def __set__(self, model_instance, value):
    """Not possible to set a new collection."""

    raise BadValueError('Virtual property is read-only')


class ComputedProperty(Property):
  """Property used for creating properties derived from other values.

  Certain attributes should never be set by users but automatically
  calculated at run-time from other values of the same entity.  These
  values are implemented as persistent properties because they provide
  useful search keys.

  A computed property behaves the same as normal properties except that
  you may not set values on them.  Attempting to do so raises
  db.DerivedPropertyError which db.Model knows to ignore during entity
  loading time.  Whenever getattr is used for the property
  the value is recalculated.  This happens when the model calls
  get_value_for_datastore on the property.

  Example:

    import string

    class Person(Model):

      name = StringProperty(required=True)

      @db.ComputedProperty
      def lower_case_name(self):
        return self.name.lower()

    # Find all people regardless of case used in name.
    Person.gql('WHERE lower_case_name=:1' % name_to_search_for.lower())
  """

  def __init__(self, value_function, indexed=True):
    """Constructor.

    Args:
      value_function: Callable f(model_instance) -> value used to derive
        persistent property value for storage in datastore.
      indexed: Whether or not the attribute should be indexed.
    """
    super(ComputedProperty, self).__init__(indexed=indexed)
    self.__value_function = value_function

  def __set__(self, *args):
    """Disallow setting this value.

    Raises:
      DerivedPropertyError when developer attempts to set attribute manually.
      Model knows to ignore this exception when getting from datastore.
    """
    raise DerivedPropertyError(
        'Computed property %s cannot be set.' % self.name)

  def __get__(self, model_instance, model_class):
    """Derive property value.

    Args:
      model_instance: Instance to derive property for in bound method case,
        else None.
      model_class: Model class associated with this property descriptor.

    Returns:
      Result of calling self.__value_funcion as provided by property
      constructor.
    """
    if model_instance is None:
      return self
    return self.__value_function(model_instance)



def to_dict(model_instance, dictionary=None):
  """Convert model to dictionary.

  Args:
    model_instance: Model instance for which to make dictionary.
    dictionary: dict instance or compatible to receive model values.
      The dictionary is not cleared of original values.  Similar to using
      dictionary.update.  If dictionary is None, a new dictionary instance is
      created and returned.

    Returns:
      New dictionary appropriate populated with model instances values
      if entity is None, else entity.
  """
  if dictionary is None:
    dictionary = {}

  model_instance._to_entity(dictionary)
  return dictionary




run_in_transaction = datastore.RunInTransaction
run_in_transaction_custom_retries = datastore.RunInTransactionCustomRetries
run_in_transaction_options = datastore.RunInTransactionOptions



RunInTransaction = run_in_transaction
RunInTransactionCustomRetries = run_in_transaction_custom_retries
websafe_encode_cursor = datastore_query.Cursor.to_websafe_string
websafe_decode_cursor = datastore_query.Cursor.from_websafe_string


is_in_transaction = datastore.IsInTransaction


transactional = datastore.Transactional
non_transactional = datastore.NonTransactional


create_config = datastore.CreateConfig
create_transaction_options = datastore.CreateTransactionOptions
