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




"""Support for creating Django (new) forms from Datastore data models.

This is our best shot at supporting as much of Django as possible: you
won't be able to use Django's db package, but you can use our
db package instead, and create Django forms from it, either fully
automatically, or with overrides.

Note, you should not import these classes from this module.  Importing
this module patches the classes in place, and you should continue to
import them from google.appengine.db.

Some of the code here is strongly inspired by Django's own ModelForm
class (new in Django 0.97).  Our code also supports Django 0.96 (so as
to be maximally compatible).  Note that our API is always similar to
Django 0.97's API, even when used with Django 0.96 (which uses a
different API, chiefly form_for_model()).

Terminology notes:
  - forms: always refers to the Django newforms subpackage
  - field: always refers to a Django forms.Field instance
  - property: always refers to a db.Property instance

Mapping between properties and fields:

+====================+===================+==============+====================+
| Property subclass  | Field subclass    | datatype     | widget; notes      |
+====================+===================+==============+====================+
| StringProperty     | CharField         | unicode      | Textarea           |
|                    |                   |              | if multiline       |
+--------------------+-------------------+--------------+--------------------+
| TextProperty       | CharField         | unicode      | Textarea           |
+--------------------+-------------------+--------------+--------------------+
| BlobProperty       | FileField         | str          | skipped in v0.96   |
+--------------------+-------------------+--------------+--------------------+
| DateTimeProperty   | DateTimeField     | datetime     | skipped            |
|                    |                   |              | if auto_now[_add]  |
+--------------------+-------------------+--------------+--------------------+
| DateProperty       | DateField         | date         | ditto              |
+--------------------+-------------------+--------------+--------------------+
| TimeProperty       | TimeField         | time         | ditto              |
+--------------------+-------------------+--------------+--------------------+
| IntegerProperty    | IntegerField      | int or long  |                    |
+--------------------+-------------------+--------------+--------------------+
| FloatProperty      | FloatField        | float        | CharField in v0.96 |
+--------------------+-------------------+--------------+--------------------+
| BooleanProperty    | BooleanField      | bool         |                    |
+--------------------+-------------------+--------------+--------------------+
| UserProperty       | CharField         | users.User   |                    |
+--------------------+-------------------+--------------+--------------------+
| StringListProperty | CharField         | list of str  | Textarea           |
+--------------------+-------------------+--------------+--------------------+
| LinkProperty       | URLField          | str          |                    |
+--------------------+-------------------+--------------+--------------------+
| ReferenceProperty  | ModelChoiceField* | db.Model     |                    |
+--------------------+-------------------+--------------+--------------------+
| _ReverseReferenceP.| None              | <iterable>   | always skipped     |
+====================+===================+==============+====================+

Notes:
*: this Field subclasses is defined by us, not in Django.
"""









import itertools
import logging





import django.core.exceptions
import django.utils.datastructures



try:
  from django import newforms as forms
  have_uploadedfile = False
except ImportError:
  from django import forms
  from django.core.files import uploadedfile
  have_uploadedfile = True



try:
  from django.utils.translation import ugettext_lazy as _
except ImportError:
  pass


from google.appengine.api import users
from google.appengine.ext import db






def monkey_patch(name, bases, namespace):
  """A 'metaclass' for adding new methods to an existing class.

  This shouldn't be used to override existing methods.  However,
  because loading this module (like loading any module) should be
  idempotent, we don't assert that.

  Usage example:

    class PatchClass(TargetClass):
      __metaclass__ = monkey_patch
      def foo(self, ...): ...
      def bar(self, ...): ...

  This is equivalent to:

    def foo(self, ...): ...
    def bar(self, ...): ...
    TargetClass.foo = foo
    TargetClass.bar = bar
    PatchClass = TargetClass

  Note that PatchClass becomes an alias for TargetClass; by convention
  it is recommended to give PatchClass the same name as TargetClass.
  """


  assert len(bases) == 1, 'Exactly one base class is required'
  base = bases[0]
  for name, value in namespace.iteritems():
    if name not in ('__metaclass__', '__module__'):
      setattr(base, name, value)
  return base







class Property(db.Property):
  __metaclass__ = monkey_patch

  def get_form_field(self, form_class=forms.CharField, **kwargs):
    """Return a Django form field appropriate for this property.

    Args:
      form_class: a forms.Field subclass, default forms.CharField

    Additional keyword arguments are passed to the form_class constructor,
    with certain defaults:
      required: self.required
      label: prettified self.verbose_name, if not None
      widget: a forms.Select instance if self.choices is non-empty
      initial: self.default, if not None

    Returns:
       A fully configured instance of form_class, or None if no form
       field should be generated for this property.
    """
    defaults = {'required': self.required}
    if self.verbose_name:
      defaults['label'] = self.verbose_name.capitalize().replace('_', ' ')
    if self.choices:
      choices = []
      if not self.required or (self.default is None and
                               'initial' not in kwargs):
        choices.append(('', '---------'))
      for choice in self.choices:
        choices.append((str(choice), unicode(choice)))
      defaults['widget'] = forms.Select(choices=choices)
    if self.default is not None:
      defaults['initial'] = self.default
    defaults.update(kwargs)
    return form_class(**defaults)

  def get_value_for_form(self, instance):
    """Extract the property value from the instance for use in a form.

    Override this to do a property- or field-specific type conversion.

    Args:
      instance: a db.Model instance

    Returns:
      The property's value extracted from the instance, possibly
      converted to a type suitable for a form field; possibly None.

    By default this returns the instance attribute's value unchanged.
    """
    return getattr(instance, self.name)

  def make_value_from_form(self, value):
    """Convert a form value to a property value.

    Override this to do a property- or field-specific type conversion.

    Args:
      value: the cleaned value retrieved from the form field

    Returns:
      A value suitable for assignment to a model instance's property;
      possibly None.

    By default this converts the value to self.data_type if it
    isn't already an instance of that type, except if the value is
    empty, in which case we return None.
    """
    if value in (None, ''):
      return None
    if not isinstance(value, self.data_type):
      value = self.data_type(value)
    return value


class UserProperty(db.UserProperty):
  __metaclass__ = monkey_patch

  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for a User property.

    This defaults to a forms.EmailField instance, except if auto_current_user or
    auto_current_user_add is set, in which case None is returned, as such
    'auto' fields should not be rendered as part of the form.
    """
    if self.auto_current_user or self.auto_current_user_add:
      return None
    defaults = {'form_class': forms.EmailField}
    defaults.update(kwargs)
    return super(UserProperty, self).get_form_field(**defaults)

  def get_value_for_form(self, instance):
    """Extract the property value from the instance for use in a form.

    This returns the email address of the User.
    """
    value = super(UserProperty, self).get_value_for_form(instance)
    if not value:
      return None
    return value.email()


class StringProperty(db.StringProperty):
  __metaclass__ = monkey_patch

  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for a string property.

    This sets the widget default to forms.Textarea if the property's
    multiline attribute is set.
    """
    defaults = {}
    if self.multiline:
      defaults['widget'] = forms.Textarea
    defaults.update(kwargs)
    return super(StringProperty, self).get_form_field(**defaults)


class TextProperty(db.TextProperty):
  __metaclass__ = monkey_patch

  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for a text property.

    This sets the widget default to forms.Textarea.
    """
    defaults = {'widget': forms.Textarea}
    defaults.update(kwargs)
    return super(TextProperty, self).get_form_field(**defaults)


class BlobProperty(db.BlobProperty):
  __metaclass__ = monkey_patch

  def __init__(self, *args, **kwargs):
    super(BlobProperty, self).__init__(*args, **kwargs)
    self.form_value = None

  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for a blob property.

    This defaults to a forms.FileField instance when using Django 0.97
    or later.  For 0.96 this returns None, as file uploads are not
    really supported in that version.
    """
    if not hasattr(forms, 'FileField'):
      return None
    defaults = {'form_class': forms.FileField}
    defaults.update(kwargs)
    return super(BlobProperty, self).get_form_field(**defaults)

  def get_value_for_form(self, instance):
    """Extract the property value from the instance for use in a form.

    There is no way to convert a Blob into an initial value for a file
    upload, so we always return None.
    """
    return None

  def make_value_from_form(self, value):
    """Convert a form value to a property value.

    This extracts the content from the UploadedFile instance returned
    by the FileField instance.
    """
    if have_uploadedfile and isinstance(value, uploadedfile.UploadedFile):
      if not self.form_value:
        self.form_value = value.read()
      b = db.Blob(self.form_value)
      return b
    return super(BlobProperty, self).make_value_from_form(value)


class DateTimeProperty(db.DateTimeProperty):
  __metaclass__ = monkey_patch

  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for a date-time property.

    This defaults to a DateTimeField instance, except if auto_now or
    auto_now_add is set, in which case None is returned, as such
    'auto' fields should not be rendered as part of the form.
    """
    if self.auto_now or self.auto_now_add:
      return None
    defaults = {'form_class': forms.DateTimeField}
    defaults.update(kwargs)
    return super(DateTimeProperty, self).get_form_field(**defaults)


class DateProperty(db.DateProperty):
  __metaclass__ = monkey_patch

  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for a date property.

    This defaults to a DateField instance, except if auto_now or
    auto_now_add is set, in which case None is returned, as such
    'auto' fields should not be rendered as part of the form.
    """
    if self.auto_now or self.auto_now_add:
      return None
    defaults = {'form_class': forms.DateField}
    defaults.update(kwargs)
    return super(DateProperty, self).get_form_field(**defaults)


class TimeProperty(db.TimeProperty):
  __metaclass__ = monkey_patch

  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for a time property.

    This defaults to a TimeField instance, except if auto_now or
    auto_now_add is set, in which case None is returned, as such
    'auto' fields should not be rendered as part of the form.
    """
    if self.auto_now or self.auto_now_add:
      return None
    defaults = {'form_class': forms.TimeField}
    defaults.update(kwargs)
    return super(TimeProperty, self).get_form_field(**defaults)


class IntegerProperty(db.IntegerProperty):
  __metaclass__ = monkey_patch

  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for an integer property.

    This defaults to an IntegerField instance.
    """
    defaults = {'form_class': forms.IntegerField}
    defaults.update(kwargs)
    return super(IntegerProperty, self).get_form_field(**defaults)


class FloatProperty(db.FloatProperty):
  __metaclass__ = monkey_patch

  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for an integer property.

    This defaults to a FloatField instance when using Django 0.97 or
    later.  For 0.96 this defaults to the CharField class.
    """
    defaults = {}
    if hasattr(forms, 'FloatField'):
      defaults['form_class'] = forms.FloatField
    defaults.update(kwargs)
    return super(FloatProperty, self).get_form_field(**defaults)


class BooleanProperty(db.BooleanProperty):
  __metaclass__ = monkey_patch

  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for a boolean property.

    This defaults to a BooleanField.
    """
    defaults = {'form_class': forms.BooleanField}
    defaults.update(kwargs)
    return super(BooleanProperty, self).get_form_field(**defaults)

  def make_value_from_form(self, value):
    """Convert a form value to a property value.

    This is needed to ensure that False is not replaced with None.
    """
    if value is None:
      return None
    if isinstance(value, basestring) and value.lower() == 'false':


      return False
    return bool(value)


class StringListProperty(db.StringListProperty):
  __metaclass__ = monkey_patch





  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for a StringList property.

    This defaults to a Textarea widget with a blank initial value.
    """
    defaults = {'widget': forms.Textarea,
                'initial': ''}
    defaults.update(kwargs)
    return super(StringListProperty, self).get_form_field(**defaults)

  def get_value_for_form(self, instance):
    """Extract the property value from the instance for use in a form.

    This joins a list of strings with newlines.
    """
    value = super(StringListProperty, self).get_value_for_form(instance)
    if not value:
      return None
    if isinstance(value, list):
      value = '\n'.join(value)
    return value

  def make_value_from_form(self, value):
    """Convert a form value to a property value.

    This breaks the string into lines.
    """
    if not value:
      return []
    if isinstance(value, basestring):
      value = value.splitlines()
    return value


class LinkProperty(db.LinkProperty):
  __metaclass__ = monkey_patch

  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for a URL property.

    This defaults to a URLField instance.
    """
    defaults = {'form_class': forms.URLField}
    defaults.update(kwargs)
    return super(LinkProperty, self).get_form_field(**defaults)


class _WrapIter(object):
  """Helper class whose iter() calls a given function to get an iterator."""

  def __init__(self, function):
    self._function = function

  def __iter__(self):
    return self._function()


class ModelChoiceField(forms.Field):

  default_error_messages = {
      'invalid_choice': _(u'Please select a valid choice. '
                          u'That choice is not one of the available choices.'),
    }

  def __init__(self, reference_class, query=None, choices=None,
               empty_label=u'---------',
               required=True, widget=forms.Select, label=None, initial=None,
               help_text=None, *args, **kwargs):
    """Constructor.

    Args:
      reference_class: required; the db.Model subclass used in the reference
      query: optional db.Query; default db.Query(reference_class)
      choices: optional explicit list of (value, label) pairs representing
        available choices; defaults to dynamically iterating over the
        query argument (or its default)
      empty_label: label to be used for the default selection item in
        the widget; this is prepended to the choices
      required, widget, label, initial, help_text, *args, **kwargs:
        like for forms.Field.__init__(); widget defaults to forms.Select
    """
    assert issubclass(reference_class, db.Model)
    if query is None:
      query = db.Query(reference_class)
    assert isinstance(query, db.Query)
    super(ModelChoiceField, self).__init__(required, widget, label, initial,
                                           help_text, *args, **kwargs)
    self.empty_label = empty_label
    self.reference_class = reference_class

    self._query = query
    self._choices = choices
    self._update_widget_choices()

  def _update_widget_choices(self):
    """Helper to copy the choices to the widget."""
    self.widget.choices = self.choices



  def _get_query(self):
    """Getter for the query attribute."""
    return self._query

  def _set_query(self, query):
    """Setter for the query attribute.

    As a side effect, the widget's choices are updated.
    """
    self._query = query
    self._update_widget_choices()

  query = property(_get_query, _set_query)

  def _generate_choices(self):
    """Generator yielding (key, label) pairs from the query results."""


    yield ('', self.empty_label)


    for inst in self._query:
      yield (inst.key(), unicode(inst))



  def _get_choices(self):
    """Getter for the choices attribute.

    This is required to return an object that can be iterated over
    multiple times.
    """
    if self._choices is not None:
      return self._choices
    return _WrapIter(self._generate_choices)

  def _set_choices(self, choices):
    """Setter for the choices attribute.

    As a side effect, the widget's choices are updated.
    """
    self._choices = choices
    self._update_widget_choices()

  choices = property(_get_choices, _set_choices)

  def clean(self, value):
    """Override Field.clean() to do reference-specific value cleaning.

    This turns a non-empty value into a model instance.
    """

    value = super(ModelChoiceField, self).clean(value)
    if not value:
      return None
    instance = db.get(value)
    if instance is None:
      raise db.BadValueError(self.error_messages['invalid_choice'])
    return instance


class ReferenceProperty(db.ReferenceProperty):
  __metaclass__ = monkey_patch

  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for a reference property.

    This defaults to a ModelChoiceField instance.
    """
    defaults = {'form_class': ModelChoiceField,
                'reference_class': self.reference_class}
    defaults.update(kwargs)
    return super(ReferenceProperty, self).get_form_field(**defaults)

  def get_value_for_form(self, instance):
    """Extract the property value from the instance for use in a form.

    This return the key object for the referenced object, or None.
    """
    value = super(ReferenceProperty, self).get_value_for_form(instance)
    if value is not None:
      value = value.key()
    return value

  def make_value_from_form(self, value):
    """Convert a form value to a property value.

    This turns a key string or object into a model instance.
    """
    if value:
      if not isinstance(value, db.Model):
        value = db.get(value)
    return value


class _ReverseReferenceProperty(db._ReverseReferenceProperty):
  __metaclass__ = monkey_patch

  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for a reverse reference.

    This always returns None, since reverse references are always
    automatic.
    """
    return None


def property_clean(prop, value):
  """Apply Property level validation to value.

  Calls .make_value_from_form() and .validate() on the property and catches
  exceptions generated by either.  The exceptions are converted to
  forms.ValidationError exceptions.

  Args:
    prop: The property to validate against.
    value: The value to validate.

  Raises:
    forms.ValidationError if the value cannot be validated.
  """
  if value is not None:
    try:



      prop.validate(prop.make_value_from_form(value))
    except (db.BadValueError, ValueError), e:
      raise forms.ValidationError(unicode(e))


class ModelFormOptions(object):
  """A simple class to hold internal options for a ModelForm class.

  Instance attributes:
    model: a db.Model class, or None
    fields: list of field names to be defined, or None
    exclude: list of field names to be skipped, or None

  These instance attributes are copied from the 'Meta' class that is
  usually present in a ModelForm class, and all default to None.
  """




  def __init__(self, options=None):
    self.model = getattr(options, 'model', None)
    self.fields = getattr(options, 'fields', None)
    self.exclude = getattr(options, 'exclude', None)


class ModelFormMetaclass(type):
  """The metaclass for the ModelForm class defined below.

  This is our analog of Django's own ModelFormMetaclass.  (We
  can't conveniently subclass that class because there are quite a few
  differences.)

  See the docs for ModelForm below for a usage example.
  """

  def __new__(cls, class_name, bases, attrs):
    """Constructor for a new ModelForm class instance.

    The signature of this method is determined by Python internals.

    All Django Field instances are removed from attrs and added to
    the base_fields attribute instead.  Additional Field instances
    are added to this based on the Datastore Model class specified
    by the Meta attribute.
    """

    fields = sorted(((field_name, attrs.pop(field_name))
                     for field_name, obj in attrs.items()
                     if isinstance(obj, forms.Field)),
                    key=lambda obj: obj[1].creation_counter)



    for base in bases[::-1]:
      if hasattr(base, 'base_fields'):
        fields = base.base_fields.items() + fields
    declared_fields = django.utils.datastructures.SortedDict()
    for field_name, obj in fields:
      declared_fields[field_name] = obj

    opts = ModelFormOptions(attrs.get('Meta', None))
    attrs['_meta'] = opts




    base_models = []
    for base in bases:
      base_opts = getattr(base, '_meta', None)
      base_model = getattr(base_opts, 'model', None)
      if base_model is not None:
        base_models.append(base_model)
    if len(base_models) > 1:
      raise django.core.exceptions.ImproperlyConfigured(
          "%s's base classes define more than one model." % class_name)



    if opts.model is not None:



      if base_models and base_models[0] is not opts.model:
        raise django.core.exceptions.ImproperlyConfigured(
            '%s defines a different model than its parent.' % class_name)

      model_fields = django.utils.datastructures.SortedDict()
      for name, prop in sorted(opts.model.properties().iteritems(),
                               key=lambda prop: prop[1].creation_counter):
        if opts.fields and name not in opts.fields:
          continue
        if opts.exclude and name in opts.exclude:
          continue
        form_field = prop.get_form_field()
        if form_field is not None:
          model_fields[name] = form_field


      model_fields.update(declared_fields)
      attrs['base_fields'] = model_fields



      props = opts.model.properties()
      for name, field in model_fields.iteritems():
        prop = props.get(name)
        if prop:



          if hasattr(forms, 'FileField') and isinstance(field, forms.FileField):
            def clean_for_property_field(value, initial, prop=prop,
                                         old_clean=field.clean):
              value = old_clean(value, initial)
              property_clean(prop, value)
              return value
          else:
            def clean_for_property_field(value, prop=prop,
                                         old_clean=field.clean):
              value = old_clean(value)
              property_clean(prop, value)
              return value
          field.clean = clean_for_property_field
    else:
      attrs['base_fields'] = declared_fields

    return super(ModelFormMetaclass, cls).__new__(cls,
                                                  class_name, bases, attrs)


class BaseModelForm(forms.BaseForm):
  """Base class for ModelForm.

  This overrides the forms.BaseForm constructor and adds a save() method.

  This class does not have a special metaclass; the magic metaclass is
  added by the subclass ModelForm.
  """

  def __init__(self, data=None, files=None, auto_id=None, prefix=None,
               initial=None, error_class=None, label_suffix=None,
               instance=None):
    """Constructor.

    Args (all optional and defaulting to None):
      data: dict of data values, typically from a POST request)
      files: dict of file upload values; Django 0.97 or later only
      auto_id, prefix: see Django documentation
      initial: dict of initial values
      error_class, label_suffix: see Django 0.97 or later documentation
      instance: Model instance to be used for additional initial values

    Except for initial and instance, these arguments are passed on to
    the forms.BaseForm constructor unchanged, but only if not None.
    Some arguments (files, error_class, label_suffix) are only
    supported by Django 0.97 or later.  Leave these blank (i.e. None)
    when using Django 0.96.  Their default values will be used with
    Django 0.97 or later even when they are explicitly set to None.
    """
    opts = self._meta
    self.instance = instance
    object_data = {}
    if instance is not None:
      for name, prop in instance.properties().iteritems():
        if opts.fields and name not in opts.fields:
          continue
        if opts.exclude and name in opts.exclude:
          continue
        object_data[name] = prop.get_value_for_form(instance)
    if initial is not None:

      object_data.update(initial)




    kwargs = dict(data=data, files=files, auto_id=auto_id,
                  prefix=prefix, initial=object_data,
                  error_class=error_class, label_suffix=label_suffix)
    kwargs = dict((name, value)
                  for name, value in kwargs.iteritems()
                  if value is not None)
    super(BaseModelForm, self).__init__(**kwargs)

  def save(self, commit=True):
    """Save this form's cleaned data into a model instance.

    Args:
      commit: optional bool, default True; if true, the model instance
        is also saved to the datastore.

    Returns:
      A model instance.  If a model instance was already associated
      with this form instance (either passed to the constructor with
      instance=...  or by a previous save() call), that same instance
      is updated and returned; if no instance was associated yet, one
      is created by this call.

    Raises:
      ValueError if the data couldn't be validated.
    """
    if not self.is_bound:
      raise ValueError('Cannot save an unbound form')
    opts = self._meta
    instance = self.instance
    if instance is None:
      fail_message = 'created'
    else:
      fail_message = 'updated'
    if self.errors:
      raise ValueError("The %s could not be %s because the data didn't "
                       'validate.' % (opts.model.kind(), fail_message))
    cleaned_data = self._cleaned_data()
    converted_data = {}
    propiter = itertools.chain(
      opts.model.properties().iteritems(),
      iter([('key_name', StringProperty(name='key_name'))])
      )
    for name, prop in propiter:
      value = cleaned_data.get(name)
      if value is not None:
        converted_data[name] = prop.make_value_from_form(value)
    try:
      if instance is None:
        instance = opts.model(**converted_data)
        self.instance = instance
      else:

        for name, value in converted_data.iteritems():
          if name == 'key_name':

            continue
          setattr(instance, name, value)
    except db.BadValueError, err:
      raise ValueError('The %s could not be %s (%s)' %
                       (opts.model.kind(), fail_message, err))
    if commit:


      instance.put()
    return instance

  def _cleaned_data(self):
    """Helper to retrieve the cleaned data attribute.

    In Django 0.96 this attribute was called self.clean_data.  In 0.97
    and later it's been renamed to self.cleaned_data, to avoid a name
    conflict.  This helper abstracts the difference between the
    versions away from its caller.
    """
    try:
      return self.cleaned_data
    except AttributeError:
      return self.clean_data


class ModelForm(BaseModelForm):
  """A Django form tied to a Datastore model.

  Note that this particular class just sets the metaclass; all other
  functionality is defined in the base class, BaseModelForm, above.

  Usage example:

    from google.appengine.ext import db
    from google.appengine.ext.db import djangoforms

    # First, define a model class
    class MyModel(db.Model):
      foo = db.StringProperty()
      bar = db.IntegerProperty(required=True, default=42)

    # Now define a form class
    class MyForm(djangoforms.ModelForm):
      class Meta:
        model = MyModel

  You can now instantiate MyForm without arguments to create an
  unbound form, or with data from a POST request to create a bound
  form.  You can also pass a model instance with the instance=...
  keyword argument to create an unbound (!) form whose initial values
  are taken from the instance.  For bound forms, use the save() method
  to return a model instance.

  Like Django's own corresponding ModelForm class, the nested Meta
  class can have two other attributes:

    fields: if present and non-empty, a list of field names to be
            included in the form; properties not listed here are
            excluded from the form

    exclude: if present and non-empty, a list of field names to be
             excluded from the form

  If exclude and fields are both non-empty, names occurring in both
  are excluded (i.e. exclude wins).  By default all property in the
  model have a corresponding form field defined.

  It is also possible to define form fields explicitly.  This gives
  more control over the widget used, constraints, initial value, and
  so on.  Such form fields are not affected by the nested Meta class's
  fields and exclude attributes.

  If you define a form field named 'key_name' it will be treated
  specially and will be used as the value for the key_name parameter
  to the Model constructor. This allows you to create instances with
  named keys. The 'key_name' field will be ignored when updating an
  instance (although it will still be shown on the form).
  """

  __metaclass__ = ModelFormMetaclass
