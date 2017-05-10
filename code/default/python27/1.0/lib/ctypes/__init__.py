import os as _os, sys as _sys

__version__ = "1.1.0"

from _ctypes import Union, Structure, Array
from _ctypes import _Pointer
from _ctypes import CFuncPtr as _CFuncPtr
from _ctypes import __version__ as _ctypes_version
from _ctypes import RTLD_LOCAL, RTLD_GLOBAL
from _ctypes import ArgumentError

from struct import calcsize as _calcsize

if __version__ != _ctypes_version:
    raise Exception("Version number mismatch", __version__, _ctypes_version)

if _os.name in ("nt", "ce"):
    from _ctypes import FormatError

DEFAULT_MODE = RTLD_LOCAL
if _os.name == "posix" and _sys.platform == "darwin":

    if int(_os.uname()[2].split('.')[0]) < 8:
        DEFAULT_MODE = RTLD_GLOBAL

from _ctypes import FUNCFLAG_CDECL as _FUNCFLAG_CDECL, \
     FUNCFLAG_PYTHONAPI as _FUNCFLAG_PYTHONAPI, \
     FUNCFLAG_USE_ERRNO as _FUNCFLAG_USE_ERRNO, \
     FUNCFLAG_USE_LASTERROR as _FUNCFLAG_USE_LASTERROR

def create_string_buffer(init, size=None):
    if isinstance(init, (str, unicode)):
        if size is None:
            size = len(init)+1
        buftype = c_char * size
        buf = buftype()
        buf.value = init
        return buf
    elif isinstance(init, (int, long)):
        buftype = c_char * init
        buf = buftype()
        return buf
    raise TypeError(init)

def c_buffer(init, size=None):
    return create_string_buffer(init, size)

_c_functype_cache = {}
def CFUNCTYPE(restype, *argtypes, **kw):
    flags = _FUNCFLAG_CDECL
    if kw.pop("use_errno", False):
        flags |= _FUNCFLAG_USE_ERRNO
    if kw.pop("use_last_error", False):
        flags |= _FUNCFLAG_USE_LASTERROR
    if kw:
        raise ValueError("unexpected keyword argument(s) %s" % kw.keys())
    try:
        return _c_functype_cache[(restype, argtypes, flags)]
    except KeyError:
        class CFunctionType(_CFuncPtr):
            _argtypes_ = argtypes
            _restype_ = restype
            _flags_ = flags
        _c_functype_cache[(restype, argtypes, flags)] = CFunctionType
        return CFunctionType

if _os.name in ("nt", "ce"):
    from _ctypes import LoadLibrary as _dlopen
    from _ctypes import FUNCFLAG_STDCALL as _FUNCFLAG_STDCALL
    if _os.name == "ce":
        _FUNCFLAG_STDCALL = _FUNCFLAG_CDECL

    _win_functype_cache = {}
    def WINFUNCTYPE(restype, *argtypes, **kw):
        flags = _FUNCFLAG_STDCALL
        if kw.pop("use_errno", False):
            flags |= _FUNCFLAG_USE_ERRNO
        if kw.pop("use_last_error", False):
            flags |= _FUNCFLAG_USE_LASTERROR
        if kw:
            raise ValueError("unexpected keyword argument(s) %s" % kw.keys())
        try:
            return _win_functype_cache[(restype, argtypes, flags)]
        except KeyError:
            class WinFunctionType(_CFuncPtr):
                _argtypes_ = argtypes
                _restype_ = restype
                _flags_ = flags
            _win_functype_cache[(restype, argtypes, flags)] = WinFunctionType
            return WinFunctionType
    if WINFUNCTYPE.__doc__:
        WINFUNCTYPE.__doc__ = CFUNCTYPE.__doc__.replace("CFUNCTYPE", "WINFUNCTYPE")

elif _os.name == "posix":
    from _ctypes import dlopen as _dlopen

from _ctypes import sizeof, byref, addressof, alignment, resize
from _ctypes import get_errno, set_errno
from _ctypes import _SimpleCData

def _check_size(typ, typecode=None):
    from struct import calcsize
    if typecode is None:
        typecode = typ._type_
    actual, required = sizeof(typ), calcsize(typecode)
    if actual != required:
        raise SystemError("sizeof(%s) wrong: %d instead of %d" % \
                          (typ, actual, required))

class py_object(_SimpleCData):
    _type_ = "O"
    def __repr__(self):
        try:
            return super(py_object, self).__repr__()
        except ValueError:
            return "%s(<NULL>)" % type(self).__name__
_check_size(py_object, "P")

class c_short(_SimpleCData):
    _type_ = "h"
_check_size(c_short)

class c_ushort(_SimpleCData):
    _type_ = "H"
_check_size(c_ushort)

class c_long(_SimpleCData):
    _type_ = "l"
_check_size(c_long)

class c_ulong(_SimpleCData):
    _type_ = "L"
_check_size(c_ulong)

if _calcsize("i") == _calcsize("l"):
    c_int = c_long
    c_uint = c_ulong
else:
    class c_int(_SimpleCData):
        _type_ = "i"
    _check_size(c_int)

    class c_uint(_SimpleCData):
        _type_ = "I"
    _check_size(c_uint)

class c_float(_SimpleCData):
    _type_ = "f"
_check_size(c_float)

class c_double(_SimpleCData):
    _type_ = "d"
_check_size(c_double)

class c_longdouble(_SimpleCData):
    _type_ = "g"
if sizeof(c_longdouble) == sizeof(c_double):
    c_longdouble = c_double

if _calcsize("l") == _calcsize("q"):
    c_longlong = c_long
    c_ulonglong = c_ulong
else:
    class c_longlong(_SimpleCData):
        _type_ = "q"
    _check_size(c_longlong)

    class c_ulonglong(_SimpleCData):
        _type_ = "Q"
    _check_size(c_ulonglong)

class c_ubyte(_SimpleCData):
    _type_ = "B"
c_ubyte.__ctype_le__ = c_ubyte.__ctype_be__ = c_ubyte
_check_size(c_ubyte)

class c_byte(_SimpleCData):
    _type_ = "b"
c_byte.__ctype_le__ = c_byte.__ctype_be__ = c_byte
_check_size(c_byte)

class c_char(_SimpleCData):
    _type_ = "c"
c_char.__ctype_le__ = c_char.__ctype_be__ = c_char
_check_size(c_char)

class c_char_p(_SimpleCData):
    _type_ = "z"
    if _os.name == "nt":
        def __repr__(self):
            if not windll.kernel32.IsBadStringPtrA(self, -1):
                return "%s(%r)" % (self.__class__.__name__, self.value)
            return "%s(%s)" % (self.__class__.__name__, cast(self, c_void_p).value)
    else:
        def __repr__(self):
            return "%s(%s)" % (self.__class__.__name__, cast(self, c_void_p).value)
_check_size(c_char_p, "P")

class c_void_p(_SimpleCData):
    _type_ = "P"
c_voidp = c_void_p
_check_size(c_void_p)

class c_bool(_SimpleCData):
    _type_ = "?"

from _ctypes import POINTER, pointer, _pointer_type_cache

def _reset_cache():
    _pointer_type_cache.clear()
    _c_functype_cache.clear()
    if _os.name in ("nt", "ce"):
        _win_functype_cache.clear()
    POINTER(c_wchar).from_param = c_wchar_p.from_param
    POINTER(c_char).from_param = c_char_p.from_param
    _pointer_type_cache[None] = c_void_p
    CFUNCTYPE(c_int)(lambda: None)

try:
    from _ctypes import set_conversion_mode
except ImportError:
    pass
else:
    if _os.name in ("nt", "ce"):
        set_conversion_mode("mbcs", "ignore")
    else:
        set_conversion_mode("ascii", "strict")

    class c_wchar_p(_SimpleCData):
        _type_ = "Z"

    class c_wchar(_SimpleCData):
        _type_ = "u"

    def create_unicode_buffer(init, size=None):
        """create_unicode_buffer(aString) -> character array
        create_unicode_buffer(anInteger) -> character array
        create_unicode_buffer(aString, anInteger) -> character array
        """
        if isinstance(init, (str, unicode)):
            if size is None:
                size = len(init)+1
            buftype = c_wchar * size
            buf = buftype()
            buf.value = init
            return buf
        elif isinstance(init, (int, long)):
            buftype = c_wchar * init
            buf = buftype()
            return buf
        raise TypeError(init)

def SetPointerType(pointer, cls):
    if _pointer_type_cache.get(cls, None) is not None:
        raise RuntimeError("This type already exists in the cache")
    if id(pointer) not in _pointer_type_cache:
        raise RuntimeError("What's this???")
    pointer.set_type(cls)
    _pointer_type_cache[cls] = pointer
    del _pointer_type_cache[id(pointer)]

def ARRAY(typ, len):
    return typ * len

################################################################


class CDLL(object):
    _func_flags_ = _FUNCFLAG_CDECL
    _func_restype_ = c_int

    def __init__(self, name, mode=DEFAULT_MODE, handle=None,
                 use_errno=False,
                 use_last_error=False):
        self._name = str(name)
        flags = self._func_flags_
        if use_errno:
            flags |= _FUNCFLAG_USE_ERRNO
        if use_last_error:
            flags |= _FUNCFLAG_USE_LASTERROR

        class _FuncPtr(_CFuncPtr):
            _flags_ = flags
            _restype_ = self._func_restype_
        self._FuncPtr = _FuncPtr

        if handle is None:
            self._handle = _dlopen(self._name, mode)
        else:
            self._handle = handle

    def __repr__(self):
        return "<%s '%s', handle %x at %x>" % \
               (self.__class__.__name__, self._name,
                (self._handle & (_sys.maxint*2 + 1)),
                id(self) & (_sys.maxint*2 + 1))

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)
        func = self.__getitem__(name)
        setattr(self, name, func)
        return func

    def __getitem__(self, name_or_ordinal):
        func = self._FuncPtr((name_or_ordinal, self))
        if not isinstance(name_or_ordinal, (int, long)):
            func.__name__ = name_or_ordinal
        return func

class PyDLL(CDLL):
    _func_flags_ = _FUNCFLAG_CDECL | _FUNCFLAG_PYTHONAPI

if _os.name in ("nt", "ce"):

    class WinDLL(CDLL):
        _func_flags_ = _FUNCFLAG_STDCALL

    from _ctypes import _check_HRESULT, _SimpleCData
    class HRESULT(_SimpleCData):
        _type_ = "l"
        _check_retval_ = _check_HRESULT

    class OleDLL(CDLL):
        _func_flags_ = _FUNCFLAG_STDCALL
        _func_restype_ = HRESULT

class LibraryLoader(object):
    def __init__(self, dlltype):
        self._dlltype = dlltype

    def __getattr__(self, name):
        if name[0] == '_':
            raise AttributeError(name)
        dll = self._dlltype(name)
        setattr(self, name, dll)
        return dll

    def __getitem__(self, name):
        return getattr(self, name)

    def LoadLibrary(self, name):
        return self._dlltype(name)

cdll = LibraryLoader(CDLL)
pydll = LibraryLoader(PyDLL)

if _os.name in ("nt", "ce"):
    pythonapi = PyDLL("python dll", None, _sys.dllhandle)
elif _sys.platform == "cygwin":
    pythonapi = PyDLL("libpython%d.%d.dll" % _sys.version_info[:2])
else:
    pythonapi = PyDLL(None)


if _os.name in ("nt", "ce"):
    windll = LibraryLoader(WinDLL)
    oledll = LibraryLoader(OleDLL)

    if _os.name == "nt":
        GetLastError = windll.kernel32.GetLastError
    else:
        GetLastError = windll.coredll.GetLastError
    from _ctypes import get_last_error, set_last_error

    def WinError(code=None, descr=None):
        if code is None:
            code = GetLastError()
        if descr is None:
            descr = FormatError(code).strip()
        return WindowsError(code, descr)

if sizeof(c_uint) == sizeof(c_void_p):
    c_size_t = c_uint
    c_ssize_t = c_int
elif sizeof(c_ulong) == sizeof(c_void_p):
    c_size_t = c_ulong
    c_ssize_t = c_long
elif sizeof(c_ulonglong) == sizeof(c_void_p):
    c_size_t = c_ulonglong
    c_ssize_t = c_longlong

from _ctypes import _memmove_addr, _memset_addr, _string_at_addr, _cast_addr

memmove = CFUNCTYPE(c_void_p, c_void_p, c_void_p, c_size_t)(_memmove_addr)

memset = CFUNCTYPE(c_void_p, c_void_p, c_int, c_size_t)(_memset_addr)

def PYFUNCTYPE(restype, *argtypes):
    class CFunctionType(_CFuncPtr):
        _argtypes_ = argtypes
        _restype_ = restype
        _flags_ = _FUNCFLAG_CDECL | _FUNCFLAG_PYTHONAPI
    return CFunctionType

_cast = PYFUNCTYPE(py_object, c_void_p, py_object, py_object)(_cast_addr)
def cast(obj, typ):
    return _cast(obj, obj, typ)

_string_at = PYFUNCTYPE(py_object, c_void_p, c_int)(_string_at_addr)
def string_at(ptr, size=-1):
    return _string_at(ptr, size)

try:
    from _ctypes import _wstring_at_addr
except ImportError:
    pass
else:
    _wstring_at = PYFUNCTYPE(py_object, c_void_p, c_int)(_wstring_at_addr)
    def wstring_at(ptr, size=-1):
        return _wstring_at(ptr, size)


if _os.name in ("nt", "ce"):
    def DllGetClassObject(rclsid, riid, ppv):
        try:
            ccom = __import__("comtypes.server.inprocserver", globals(), locals(), ['*'])
        except ImportError:
            return -2147221231
        else:
            return ccom.DllGetClassObject(rclsid, riid, ppv)

    def DllCanUnloadNow():
        try:
            ccom = __import__("comtypes.server.inprocserver", globals(), locals(), ['*'])
        except ImportError:
            return 0
        return ccom.DllCanUnloadNow()

from ctypes._endian import BigEndianStructure, LittleEndianStructure

c_int8 = c_byte
c_uint8 = c_ubyte
for kind in [c_short, c_int, c_long, c_longlong]:
    if sizeof(kind) == 2: c_int16 = kind
    elif sizeof(kind) == 4: c_int32 = kind
    elif sizeof(kind) == 8: c_int64 = kind
for kind in [c_ushort, c_uint, c_ulong, c_ulonglong]:
    if sizeof(kind) == 2: c_uint16 = kind
    elif sizeof(kind) == 4: c_uint32 = kind
    elif sizeof(kind) == 8: c_uint64 = kind
del(kind)

_reset_cache()
