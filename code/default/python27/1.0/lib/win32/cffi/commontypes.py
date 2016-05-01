import sys
from . import api, model


COMMON_TYPES = {
    'FILE': model.unknown_type('FILE', '_IO_FILE'),
    'bool': '_Bool',
    }

for _type in model.PrimitiveType.ALL_PRIMITIVE_TYPES:
    if _type.endswith('_t'):
        COMMON_TYPES[_type] = _type
del _type

_CACHE = {}

def resolve_common_type(commontype):
    try:
        return _CACHE[commontype]
    except KeyError:
        result = COMMON_TYPES.get(commontype, commontype)
        if not isinstance(result, str):
            pass    # result is already a BaseType
        elif result.endswith(' *'):
            if result.startswith('const '):
                result = model.ConstPointerType(
                    resolve_common_type(result[6:-2]))
            else:
                result = model.PointerType(resolve_common_type(result[:-2]))
        elif result in model.PrimitiveType.ALL_PRIMITIVE_TYPES:
            result = model.PrimitiveType(result)
        else:
            if commontype == result:
                raise api.FFIError("Unsupported type: %r.  Please file a bug "
                                   "if you think it should be." % (commontype,))
            result = resolve_common_type(result)   # recursively
        assert isinstance(result, model.BaseTypeByIdentity)
        _CACHE[commontype] = result
        return result


# ____________________________________________________________
# Windows common types


def win_common_types(maxsize):
    result = {}
    if maxsize < (1<<32):
        result.update({      # Windows 32-bits
            'HALF_PTR': 'short',
            'INT_PTR': 'int',
            'LONG_PTR': 'long',
            'UHALF_PTR': 'unsigned short',
            'UINT_PTR': 'unsigned int',
            'ULONG_PTR': 'unsigned long',
            })
    else:
        result.update({      # Windows 64-bits
            'HALF_PTR': 'int',
            'INT_PTR': 'long long',
            'LONG_PTR': 'long long',
            'UHALF_PTR': 'unsigned int',
            'UINT_PTR': 'unsigned long long',
            'ULONG_PTR': 'unsigned long long',
            })
    result.update({
        "BYTE": "unsigned char",
        "BOOL": "int",
        "CCHAR": "char",
        "CHAR": "char",
        "DWORD": "unsigned long",
        "DWORD32": "unsigned int",
        "DWORD64": "unsigned long long",
        "FLOAT": "float",
        "INT": "int",
        "INT8": "signed char",
        "INT16": "short",
        "INT32": "int",
        "INT64": "long long",
        "LONG": "long",
        "LONGLONG": "long long",
        "LONG32": "int",
        "LONG64": "long long",
        "WORD": "unsigned short",
        "PVOID": model.voidp_type,
        "ULONGLONG": "unsigned long long",
        "WCHAR": "wchar_t",
        "SHORT": "short",
        "TBYTE": "WCHAR",
        "TCHAR": "WCHAR",
        "UCHAR": "unsigned char",
        "UINT": "unsigned int",
        "UINT8": "unsigned char",
        "UINT16": "unsigned short",
        "UINT32": "unsigned int",
        "UINT64": "unsigned long long",
        "ULONG": "unsigned long",
        "ULONG32": "unsigned int",
        "ULONG64": "unsigned long long",
        "USHORT": "unsigned short",

        "SIZE_T": "ULONG_PTR",
        "SSIZE_T": "LONG_PTR",
        "ATOM": "WORD",
        "BOOLEAN": "BYTE",
        "COLORREF": "DWORD",

        "HANDLE": "PVOID",
        "DWORDLONG": "ULONGLONG",
        "DWORD_PTR": "ULONG_PTR",
        "HACCEL": "HANDLE",

        "HBITMAP": "HANDLE",
        "HBRUSH": "HANDLE",
        "HCOLORSPACE": "HANDLE",
        "HCONV": "HANDLE",
        "HCONVLIST": "HANDLE",
        "HDC": "HANDLE",
        "HDDEDATA": "HANDLE",
        "HDESK": "HANDLE",
        "HDROP": "HANDLE",
        "HDWP": "HANDLE",
        "HENHMETAFILE": "HANDLE",
        "HFILE": "int",
        "HFONT": "HANDLE",
        "HGDIOBJ": "HANDLE",
        "HGLOBAL": "HANDLE",
        "HHOOK": "HANDLE",
        "HICON": "HANDLE",
        "HCURSOR": "HICON",
        "HINSTANCE": "HANDLE",
        "HKEY": "HANDLE",
        "HKL": "HANDLE",
        "HLOCAL": "HANDLE",
        "HMENU": "HANDLE",
        "HMETAFILE": "HANDLE",
        "HMODULE": "HINSTANCE",
        "HMONITOR": "HANDLE",
        "HPALETTE": "HANDLE",
        "HPEN": "HANDLE",
        "HRESULT": "LONG",
        "HRGN": "HANDLE",
        "HRSRC": "HANDLE",
        "HSZ": "HANDLE",
        "WINSTA": "HANDLE",
        "HWND": "HANDLE",

        "LANGID": "WORD",
        "LCID": "DWORD",
        "LCTYPE": "DWORD",
        "LGRPID": "DWORD",
        "LPARAM": "LONG_PTR",
        "LPBOOL": "BOOL *",
        "LPBYTE": "BYTE *",
        "LPCOLORREF": "DWORD *",
        "LPCSTR": "const char *",

        "LPCVOID": model.const_voidp_type,
        "LPCWSTR": "const WCHAR *",
        "LPCTSTR": "LPCWSTR",
        "LPDWORD": "DWORD *",
        "LPHANDLE": "HANDLE *",
        "LPINT": "int *",
        "LPLONG": "long *",
        "LPSTR": "CHAR *",
        "LPWSTR": "WCHAR *",
        "LPTSTR": "LPWSTR",
        "LPVOID": model.voidp_type,
        "LPWORD": "WORD *",
        "LRESULT": "LONG_PTR",
        "PBOOL": "BOOL *",
        "PBOOLEAN": "BOOLEAN *",
        "PBYTE": "BYTE *",
        "PCHAR": "CHAR *",
        "PCSTR": "const CHAR *",
        "PCTSTR": "LPCWSTR",
        "PCWSTR": "const WCHAR *",
        "PDWORD": "DWORD *",
        "PDWORDLONG": "DWORDLONG *",
        "PDWORD_PTR": "DWORD_PTR *",
        "PDWORD32": "DWORD32 *",
        "PDWORD64": "DWORD64 *",
        "PFLOAT": "FLOAT *",
        "PHALF_PTR": "HALF_PTR *",
        "PHANDLE": "HANDLE *",
        "PHKEY": "HKEY *",
        "PINT": "int *",
        "PINT_PTR": "INT_PTR *",
        "PINT8": "INT8 *",
        "PINT16": "INT16 *",
        "PINT32": "INT32 *",
        "PINT64": "INT64 *",
        "PLCID": "PDWORD",
        "PLONG": "LONG *",
        "PLONGLONG": "LONGLONG *",
        "PLONG_PTR": "LONG_PTR *",
        "PLONG32": "LONG32 *",
        "PLONG64": "LONG64 *",
        "PSHORT": "SHORT *",
        "PSIZE_T": "SIZE_T *",
        "PSSIZE_T": "SSIZE_T *",
        "PSTR": "CHAR *",
        "PTBYTE": "TBYTE *",
        "PTCHAR": "TCHAR *",
        "PTSTR": "LPWSTR",
        "PUCHAR": "UCHAR *",
        "PUHALF_PTR": "UHALF_PTR *",
        "PUINT": "UINT *",
        "PUINT_PTR": "UINT_PTR *",
        "PUINT8": "UINT8 *",
        "PUINT16": "UINT16 *",
        "PUINT32": "UINT32 *",
        "PUINT64": "UINT64 *",
        "PULONG": "ULONG *",
        "PULONGLONG": "ULONGLONG *",
        "PULONG_PTR": "ULONG_PTR *",
        "PULONG32": "ULONG32 *",
        "PULONG64": "ULONG64 *",
        "PUSHORT": "USHORT *",
        "PWCHAR": "WCHAR *",
        "PWORD": "WORD *",
        "PWSTR": "WCHAR *",
        "QWORD": "unsigned long long",
        "SC_HANDLE": "HANDLE",
        "SC_LOCK": "LPVOID",
        "SERVICE_STATUS_HANDLE": "HANDLE",

        "UNICODE_STRING": model.StructType(
            "_UNICODE_STRING",
            ["Length",
             "MaximumLength",
             "Buffer"],
            [model.PrimitiveType("unsigned short"),
             model.PrimitiveType("unsigned short"),
             model.PointerType(model.PrimitiveType("wchar_t"))],
            [-1, -1, -1]),
        "PUNICODE_STRING": "UNICODE_STRING *",
        "PCUNICODE_STRING": "const UNICODE_STRING *",

        "USN": "LONGLONG",
        "VOID": model.void_type,
        "WPARAM": "UINT_PTR",
        })
    return result


if sys.platform == 'win32':
    COMMON_TYPES.update(win_common_types(sys.maxsize))
