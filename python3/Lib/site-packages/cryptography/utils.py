# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.


import abc
import enum
import inspect
import sys
import types
import typing
import warnings


# We use a UserWarning subclass, instead of DeprecationWarning, because CPython
# decided deprecation warnings should be invisble by default.
class CryptographyDeprecationWarning(UserWarning):
    pass


# Several APIs were deprecated with no specific end-of-life date because of the
# ubiquity of their use. They should not be removed until we agree on when that
# cycle ends.
PersistentlyDeprecated2019 = CryptographyDeprecationWarning
DeprecatedIn35 = CryptographyDeprecationWarning
DeprecatedIn36 = CryptographyDeprecationWarning
DeprecatedIn37 = CryptographyDeprecationWarning


def _check_bytes(name: str, value: bytes) -> None:
    if not isinstance(value, bytes):
        raise TypeError("{} must be bytes".format(name))


def _check_byteslike(name: str, value: bytes) -> None:
    try:
        memoryview(value)
    except TypeError:
        raise TypeError("{} must be bytes-like".format(name))


if typing.TYPE_CHECKING:
    from typing_extensions import Protocol

    _T_class = typing.TypeVar("_T_class", bound=type)

    class _RegisterDecoratorType(Protocol):
        def __call__(
            self, klass: _T_class, *, check_annotations: bool = False
        ) -> _T_class:
            ...


def register_interface(iface: abc.ABCMeta) -> "_RegisterDecoratorType":
    def register_decorator(
        klass: "_T_class", *, check_annotations: bool = False
    ) -> "_T_class":
        verify_interface(iface, klass, check_annotations=check_annotations)
        iface.register(klass)
        return klass

    return register_decorator


def int_to_bytes(integer: int, length: typing.Optional[int] = None) -> bytes:
    return integer.to_bytes(
        length or (integer.bit_length() + 7) // 8 or 1, "big"
    )


class InterfaceNotImplemented(Exception):
    pass


def strip_annotation(signature: inspect.Signature) -> inspect.Signature:
    return inspect.Signature(
        [
            param.replace(annotation=inspect.Parameter.empty)
            for param in signature.parameters.values()
        ]
    )


def verify_interface(
    iface: abc.ABCMeta, klass: object, *, check_annotations: bool = False
):
    for method in iface.__abstractmethods__:
        if not hasattr(klass, method):
            raise InterfaceNotImplemented(
                "{} is missing a {!r} method".format(klass, method)
            )
        if isinstance(getattr(iface, method), abc.abstractproperty):
            # Can't properly verify these yet.
            continue
        sig = inspect.signature(getattr(iface, method))
        actual = inspect.signature(getattr(klass, method))
        if check_annotations:
            ok = sig == actual
        else:
            ok = strip_annotation(sig) == strip_annotation(actual)
        if not ok:
            raise InterfaceNotImplemented(
                "{}.{}'s signature differs from the expected. Expected: "
                "{!r}. Received: {!r}".format(klass, method, sig, actual)
            )


class _DeprecatedValue:
    def __init__(self, value: object, message: str, warning_class):
        self.value = value
        self.message = message
        self.warning_class = warning_class


class _ModuleWithDeprecations(types.ModuleType):
    def __init__(self, module: types.ModuleType):
        super().__init__(module.__name__)
        self.__dict__["_module"] = module

    def __getattr__(self, attr: str) -> object:
        obj = getattr(self._module, attr)
        if isinstance(obj, _DeprecatedValue):
            warnings.warn(obj.message, obj.warning_class, stacklevel=2)
            obj = obj.value
        return obj

    def __setattr__(self, attr: str, value: object) -> None:
        setattr(self._module, attr, value)

    def __delattr__(self, attr: str) -> None:
        obj = getattr(self._module, attr)
        if isinstance(obj, _DeprecatedValue):
            warnings.warn(obj.message, obj.warning_class, stacklevel=2)

        delattr(self._module, attr)

    def __dir__(self) -> typing.Sequence[str]:
        return ["_module"] + dir(self._module)


def deprecated(
    value: object,
    module_name: str,
    message: str,
    warning_class: typing.Type[Warning],
    name: typing.Optional[str] = None,
) -> _DeprecatedValue:
    module = sys.modules[module_name]
    if not isinstance(module, _ModuleWithDeprecations):
        sys.modules[module_name] = module = _ModuleWithDeprecations(module)
    dv = _DeprecatedValue(value, message, warning_class)
    # Maintain backwards compatibility with `name is None` for pyOpenSSL.
    if name is not None:
        setattr(module, name, dv)
    return dv


def cached_property(func: typing.Callable) -> property:
    cached_name = "_cached_{}".format(func)
    sentinel = object()

    def inner(instance: object):
        cache = getattr(instance, cached_name, sentinel)
        if cache is not sentinel:
            return cache
        result = func(instance)
        setattr(instance, cached_name, result)
        return result

    return property(inner)


# Python 3.10 changed representation of enums. We use well-defined object
# representation and string representation from Python 3.9.
class Enum(enum.Enum):
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}.{self._name_}: {self._value_!r}>"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}.{self._name_}"
