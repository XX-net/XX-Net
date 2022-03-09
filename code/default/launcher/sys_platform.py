import platform
import sys
import os

from xlog import getLogger

xlog = getLogger("launcher")

current_path = os.path.dirname(os.path.abspath(__file__))
default_path = os.path.abspath(os.path.join(current_path, os.pardir))


if sys.platform.startswith("linux"):
    if os.path.isfile("/system/bin/dalvikvm"):
        xlog.info("This is Android")
        has_desktop = False
        platform = "android"
        platform_lib = ""
        from non_tray import sys_tray

    else:
        def X_is_running():
            try:
                from subprocess import Popen, PIPE
                p = Popen(["xset", "-q"], stdout=PIPE, stderr=PIPE)
                p.communicate()
                return p.returncode == 0
            except:
                return False


        def has_gi():
            try:
                import gi
                gi.require_version('Gtk', '3.0')
                from gi.repository import Gtk as gtk
                return True
            except Exception as e:
                xlog.warn("load gi fail:%r, SysTray will not show.", e)
                return False


        def has_pygtk():
            try:
                import pygtk
                pygtk.require('2.0')
                import gtk
                return True
            except:
                return False


        if X_is_running() and (has_pygtk() or has_gi()):
            has_desktop = True
            from gtk_tray import sys_tray
        else:
            from non_tray import sys_tray

            has_desktop = False

        platform = "linux"
        platform_lib = os.path.join(default_path, 'lib', 'linux')
        sys.path.append(platform_lib)

elif sys.platform == "win32":
    has_desktop = True

    platform = "windows"
    platform_lib = os.path.join(default_path, 'lib', 'win32')
    sys.path.append(platform_lib)

    from win_tray import sys_tray

elif sys.platform == "darwin":
    has_desktop = True
    platform = "mac"
    platform_lib = os.path.abspath(os.path.join(default_path, 'lib', 'darwin'))
    sys.path.append(platform_lib)

    extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjc"
    sys.path.append(extra_lib)

    try:
        import mac_tray as sys_tray
    except Exception as e:
        xlog.warn("import mac_tray except:%r, Please try run 'sudo pip3 install -U PyObjC Pillow' by yourself.", e)
        from non_tray import sys_tray
else:
    xlog.warn(("detect platform fail:%s" % sys.platform))
    from non_tray import sys_tray

    platform = "unknown"
    has_desktop = False
    platform_lib = ""
