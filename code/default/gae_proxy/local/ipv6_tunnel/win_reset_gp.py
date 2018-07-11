# coding:utf-8

import os
import sys
import platform
import locale
import ctypes
import subprocess
from ctypes import c_ulong, c_char_p, c_int, c_void_p
from ctypes.wintypes import HANDLE, DWORD, HWND, HINSTANCE, HKEY


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def encode_for_locale(s):
    if s is None:
        return
    return s.encode('mbcs')

if os.name == 'nt':
    class ShellExecuteInfo(ctypes.Structure):
        _fields_ = [('cbSize', DWORD),
                    ('fMask', c_ulong),
                    ('hwnd', HWND),
                    ('lpVerb', c_char_p),
                    ('lpFile', c_char_p),
                    ('lpParameters', c_char_p),
                    ('lpDirectory', c_char_p),
                    ('nShow', c_int),
                    ('hInstApp', HINSTANCE),
                    ('lpIDList', c_void_p),
                    ('lpClass', c_char_p),
                    ('hKeyClass', HKEY),
                    ('dwHotKey', DWORD),
                    ('hIcon', HANDLE),
                    ('hProcess', HANDLE)]

    SEE_MASK_NOCLOSEPROCESS = 0x00000040
    ShellExecuteEx = ctypes.windll.Shell32.ShellExecuteEx
    ShellExecuteEx.argtypes = ctypes.POINTER(ShellExecuteInfo),
    WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
    SE_ERR_CODES = {
        0: 'Out of memory or resources',
        2: 'File not found',
        3: 'Path not found',
        5: 'Access denied',
        8: 'Out of memory',
        26: 'Cannot share an open file',
        27: 'File association information not complete',
        28: 'DDE operation timed out',
        29: 'DDE operation failed',
        30: 'DDE operation is busy',
        31: 'File association not available',
        32: 'Dynamic-link library not found',
    }
    sys.argv[0] = os.path.abspath(sys.argv[0])

def runas(args=sys.argv, executable=sys.executable, cwd=None,
          nShow=1, waitClose=True, waitTimeout=-1):
    if not 0 <= nShow <= 10:
        nShow = 1
    err = None
    try:
        if args is not None and not isinstance(args, str):
            args = subprocess.list2cmdline(args)
        pExecInfo = ShellExecuteInfo()
        pExecInfo.cbSize = ctypes.sizeof(pExecInfo)
        pExecInfo.fMask |= SEE_MASK_NOCLOSEPROCESS
        pExecInfo.lpVerb = b'open' if is_admin() else b'runas'
        pExecInfo.lpFile = encode_for_locale(executable)
        pExecInfo.lpParameters = encode_for_locale(args)
        pExecInfo.lpDirectory = encode_for_locale(cwd)
        pExecInfo.nShow = nShow
        if ShellExecuteEx(pExecInfo):
            if waitClose:
                WaitForSingleObject(pExecInfo.hProcess, waitTimeout)
            else:
                return pExecInfo.hProcess
        else:
            err = SE_ERR_CODES.get(pExecInfo.hInstApp, 'unknown')
    except Exception as e:
        err = e
    if err:
        print('runas failed! error: %r' % err)

def win32_notify( msg='msg', title='Title'):
    res = ctypes.windll.user32.MessageBoxW(None, msg, title, 1)
    # Yes:1 No:2
    return res == 1

def reset_teredo():
    gp_split = b'[\x00'
    gp_teredo = 'v6Transition\x00;Teredo'
    gp_teredo = '\x00'.join(b for b in gp_teredo).encode()

    with open(gp_regpol_file, 'rb') as f:
        gp_regpol_old = f.read().split(gp_split)

    gp_regpol_new = [gp for gp in gp_regpol_old if gp_teredo not in gp]

    if len(gp_regpol_new) != len(gp_regpol_old) and \
            win32_notify(u'发现组策略 Teredo 设置，是否重置？', u'提醒'):
        with open(gp_regpol_file, 'wb') as f:
            f.write(gp_split.join(gp_regpol_new))
        os.system(sysnative + '\\gpupdate /target:computer /force')

if '__main__' == __name__:
    if os.name != 'nt':
        sys.exit(0)

    sysver = platform.version()
    if sysver < '6':
        # Teredo item was added to Group Policy starting with Windows Vista
        sys.exit(0)

    windir = os.environ.get('windir')
    if not windir:
        sys.exit(-1)

    sys64 = os.path.exists(windir + '\\SysWOW64')
    pe32 = platform.architecture()[0] == '32bit'
    sysalias = 'Sysnative' if sys64 and pe32 else 'System32'
    sysnative = '%s\\%s' % (windir, sysalias)
    gp_regpol_file = sysnative + '\\GroupPolicy\\Machine\\Registry.pol'

    if os.path.exists(gp_regpol_file):
        if not is_admin():
            runas()
            sys.exit(0)
        reset_teredo()
