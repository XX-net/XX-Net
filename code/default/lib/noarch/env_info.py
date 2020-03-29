import platform
import sys

import utils

def win32_version():
    import ctypes
    class OSVERSIONINFOEXW(ctypes.Structure):
        _fields_ = [('dwOSVersionInfoSize', ctypes.c_ulong),
                    ('dwMajorVersion', ctypes.c_ulong),
                    ('dwMinorVersion', ctypes.c_ulong),
                    ('dwBuildNumber', ctypes.c_ulong),
                    ('dwPlatformId', ctypes.c_ulong),
                    ('szCSDVersion', ctypes.c_wchar*128),
                    ('wServicePackMajor', ctypes.c_ushort),
                    ('wServicePackMinor', ctypes.c_ushort),
                    ('wSuiteMask', ctypes.c_ushort),
                    ('wProductType', ctypes.c_byte),
                    ('wReserved', ctypes.c_byte)]
    """
    Get's the OS major and minor versions.  Returns a tuple of
    (OS_MAJOR, OS_MINOR).
    """
    os_version = OSVERSIONINFOEXW()
    os_version.dwOSVersionInfoSize = ctypes.sizeof(os_version)
    retcode = ctypes.windll.Ntdll.RtlGetVersion(ctypes.byref(os_version))
    if retcode != 0:
        raise Exception("Failed to get OS version")

    return os_version.dwMajorVersion


def win32_version_string():
    import ctypes
    class OSVERSIONINFOEXW(ctypes.Structure):
        _fields_ = [('dwOSVersionInfoSize', ctypes.c_ulong),
                    ('dwMajorVersion', ctypes.c_ulong),
                    ('dwMinorVersion', ctypes.c_ulong),
                    ('dwBuildNumber', ctypes.c_ulong),
                    ('dwPlatformId', ctypes.c_ulong),
                    ('szCSDVersion', ctypes.c_wchar*128),
                    ('wServicePackMajor', ctypes.c_ushort),
                    ('wServicePackMinor', ctypes.c_ushort),
                    ('wSuiteMask', ctypes.c_ushort),
                    ('wProductType', ctypes.c_byte),
                    ('wReserved', ctypes.c_byte)]
    """
    Get's the OS major and minor versions.  Returns a tuple of
    (OS_MAJOR, OS_MINOR).
    """
    os_version = OSVERSIONINFOEXW()
    os_version.dwOSVersionInfoSize = ctypes.sizeof(os_version)
    retcode = ctypes.windll.Ntdll.RtlGetVersion(ctypes.byref(os_version))
    if retcode != 0:
        raise Exception("Failed to get OS version")

    version_string = "Version:%d-%d; Build:%d; Platform:%d; CSD:%s; ServicePack:%d-%d; Suite:%d; ProductType:%d" %  (
        os_version.dwMajorVersion, os_version.dwMinorVersion,
        os_version.dwBuildNumber,
        os_version.dwPlatformId,
        os_version.szCSDVersion,
        os_version.wServicePackMajor, os_version.wServicePackMinor,
        os_version.wSuiteMask,
        os_version.wReserved
    )

    return version_string


def linux_distribution():
    try:
        with open("/etc/os-release", "br") as fd:
            kvs = {}
            for line in fd.readlines():
                kv = line.split(b"=")
                if kv[0] == b"NAME":
                    v = kv[1].replace(b"\"", b"")
                    kvs[kv[0]] = v
        if b"PRETTY_NAME" in kvs:
            return kvs[b"PRETTY_NAME"]
        elif b"NAME" in kvs:
            return kvs[b"NAME"]
        else:
            return None
    except Exception as e:
        return None


def os_detail():
    if sys.platform == "win32":
        return win32_version_string()
    elif sys.platform.startswith("linux"):
        distribution = linux_distribution()
        if distribution is None:
            return "plat:%s release:%s ver:%s" % (platform.platform(), platform.release(), platform.version())
        else:
            return utils.to_str(distribution)
    elif sys.platform == "darwin":
        release, versioninfo, machine = platform.mac_ver()
        return "Release:%s; Version:%s Machine:%s" % (release, versioninfo, machine)
    else:
        return "None"
