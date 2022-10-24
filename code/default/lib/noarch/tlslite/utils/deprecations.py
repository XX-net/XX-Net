# Copyright (c) 2018 Hubert Kario
#
# See the LICENSE file for legal information regarding use of this file.
"""Methods for deprecating old names for arguments or attributes."""
import warnings
import inspect
from functools import wraps


def deprecated_class_name(old_name,
                          warn="Class name '{old_name}' is deprecated, "
                          "please use '{new_name}'"):
    """
    Class decorator to deprecate a use of class.

    :param str old_name: the deprecated name that will be registered, but
       will raise warnings if used.

    :param str warn: DeprecationWarning format string for informing the
       user what is the current class name, uses 'old_name' for the deprecated
       keyword name and the 'new_name' for the current one.
       Example: "Old name: {old_nam}, use '{new_name}' instead".
    """
    def _wrap(obj):
        assert callable(obj)

        def _warn():
            warnings.warn(warn.format(old_name=old_name,
                                      new_name=obj.__name__),
                          DeprecationWarning,
                          stacklevel=3)

        def _wrap_with_warn(func, is_inspect):
            @wraps(func)
            def _func(*args, **kwargs):
                if is_inspect:
                    # XXX: If use another name to call,
                    # you will not get the warning.
                    # we do this instead of subclassing or metaclass as
                    # we want to isinstance(new_name(), old_name) and
                    # isinstance(old_name(), new_name) to work
                    frame = inspect.currentframe().f_back
                    code = inspect.getframeinfo(frame).code_context
                    if [line for line in code
                            if '{0}('.format(old_name) in line]:
                        _warn()
                else:
                    _warn()
                return func(*args, **kwargs)
            return _func

        # Make old name available.
        frame = inspect.currentframe().f_back
        if old_name in frame.f_globals:
            raise NameError("Name '{0}' already in use.".format(old_name))

        if inspect.isclass(obj):
            obj.__init__ = _wrap_with_warn(obj.__init__, True)
            placeholder = obj
        else:
            placeholder = _wrap_with_warn(obj, False)

        frame.f_globals[old_name] = placeholder

        return obj
    return _wrap


def deprecated_params(names, warn="Param name '{old_name}' is deprecated, "
                                  "please use '{new_name}'"):
    """Decorator to translate obsolete names and warn about their use.

    :param dict names: dictionary with pairs of new_name: old_name
        that will be used for translating obsolete param names to new names

    :param str warn: DeprecationWarning format string for informing the user
        what is the current parameter name, uses 'old_name' for the
        deprecated keyword name and 'new_name' for the current one.
        Example: "Old name: {old_name}, use {new_name} instead".
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for new_name, old_name in names.items():
                if old_name in kwargs:
                    if new_name in kwargs:
                        raise TypeError("got multiple values for keyword "
                                        "argument '{0}'".format(new_name))
                    warnings.warn(warn.format(old_name=old_name,
                                              new_name=new_name),
                                  DeprecationWarning,
                                  stacklevel=2)
                    kwargs[new_name] = kwargs.pop(old_name)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def deprecated_instance_attrs(names,
                              warn="Attribute '{old_name}' is deprecated, "
                                   "please use '{new_name}'"):
    """Decorator to deprecate class instance attributes.

    Translates all names in `names` to use new names and emits warnings
    if the translation was necessary. Does apply only to instance variables
    and attributes (won't modify behaviour of class variables, static methods,
    etc.

    :param dict names: dictionary with paris of new_name: old_name that will
        be used to translate the calls
    :param str warn: DeprecationWarning format string for informing the user
        what is the current parameter name, uses 'old_name' for the
        deprecated keyword name and 'new_name' for the current one.
        Example: "Old name: {old_name}, use {new_name} instead".
    """
    # reverse the dict as we're looking for old attributes, not new ones
    names = dict((j, i) for i, j in names.items())

    def decorator(clazz):
        def getx(self, name, __old_getx=getattr(clazz, "__getattr__", None)):
            if name in names:
                warnings.warn(warn.format(old_name=name,
                                          new_name=names[name]),
                              DeprecationWarning,
                              stacklevel=2)
                return getattr(self, names[name])
            if __old_getx:
                if hasattr(__old_getx, "__func__"):
                    return __old_getx.__func__(self, name)
                return __old_getx(self, name)
            raise AttributeError("'{0}' object has no attribute '{1}'"
                                 .format(clazz.__name__, name))

        getx.__name__ = "__getattr__"
        clazz.__getattr__ = getx

        def setx(self, name, value, __old_setx=getattr(clazz, "__setattr__")):
            if name in names:
                warnings.warn(warn.format(old_name=name,
                                          new_name=names[name]),
                              DeprecationWarning,
                              stacklevel=2)
                setattr(self, names[name], value)
            else:
                __old_setx(self, name, value)

        setx.__name__ = "__setattr__"
        clazz.__setattr__ = setx

        def delx(self, name, __old_delx=getattr(clazz, "__delattr__")):
            if name in names:
                warnings.warn(warn.format(old_name=name,
                                          new_name=names[name]),
                              DeprecationWarning,
                              stacklevel=2)
                delattr(self, names[name])
            else:
                __old_delx(self, name)

        delx.__name__ = "__delattr__"
        clazz.__delattr__ = delx

        return clazz
    return decorator


def deprecated_attrs(names, warn="Attribute '{old_name}' is deprecated, "
                                 "please use '{new_name}'"):
    """Decorator to deprecate all specified attributes in class.

    Translates all names in `names` to use new names and emits warnings
    if the translation was necessary.

    Note: uses metaclass magic so is incompatible with other metaclass uses

    :param dict names: dictionary with paris of new_name: old_name that will
        be used to translate the calls
    :param str warn: DeprecationWarning format string for informing the user
        what is the current parameter name, uses 'old_name' for the
        deprecated keyword name and 'new_name' for the current one.
        Example: "Old name: {old_name}, use {new_name} instead".
    """
    # prepare metaclass for handling all the class methods, class variables
    # and static methods (as they don't go through instance's __getattr__)
    class DeprecatedProps(type):
        pass

    metaclass = deprecated_instance_attrs(names, warn)(DeprecatedProps)

    def wrapper(cls):
        cls = deprecated_instance_attrs(names, warn)(cls)

        # apply metaclass
        orig_vars = cls.__dict__.copy()
        slots = orig_vars.get('__slots__')
        if slots is not None:
            if isinstance(slots, str):
                slots = [slots]
            for slots_var in slots:
                orig_vars.pop(slots_var)
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper

def deprecated_method(message):
    """Decorator for deprecating methods.

    :param ste message: The message you want to display.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn("{0} is a deprecated method. {1}".format(func.__name__, message),
                          DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator
