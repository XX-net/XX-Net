#!/usr/bin/env python
# coding:utf-8

import os, sys
import time
import atexit

# reduce resource request for threading
# for OpenWrt
import threading
try:
    threading.stack_size(128*1024)
except:
    pass

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data'))
data_launcher_path = os.path.join(data_path, 'launcher')
python_path = os.path.join(root_path, 'python27', '1.0')
noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)


def create_data_path():
    if not os.path.isdir(data_path):
        os.mkdir(data_path)

    if not os.path.isdir(data_launcher_path):
        os.mkdir(data_launcher_path)

    data_gae_proxy_path = os.path.join(data_path, 'gae_proxy')
    if not os.path.isdir(data_gae_proxy_path):
        os.mkdir(data_gae_proxy_path)
create_data_path()

from instances import xlog

has_desktop = True
if sys.platform.startswith("linux"):
    def X_is_running():
        try:
            import pygtk
            pygtk.require('2.0')
            import gtk

            from subprocess import Popen, PIPE
            p = Popen(["xset", "-q"], stdout=PIPE, stderr=PIPE)
            p.communicate()
            return p.returncode == 0
        except:
            return False

    if X_is_running():
        from gtk_tray import sys_tray
    else:
        from non_tray import sys_tray
        has_desktop = False


    platform_lib = os.path.join(python_path, 'lib', 'linux')
    sys.path.append(platform_lib)
elif sys.platform == "win32":
    platform_lib = os.path.join(python_path, 'lib', 'win32')
    sys.path.append(platform_lib)
    from win_tray import sys_tray
elif sys.platform == "darwin":
    platform_lib = os.path.abspath( os.path.join(python_path, 'lib', 'darwin'))
    sys.path.append(platform_lib)
    extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjc"
    sys.path.append(extra_lib)

    try:
        import mac_tray as sys_tray
    except:
        from non_tray import sys_tray
else:
    print("detect platform fail:%s" % sys.platform)
    from non_tray import sys_tray
    has_desktop = False
    platform_lib = ""


def unload(module):
    for m in list(sys.modules.keys()):
        if m == module or m.startswith(module+"."):
            del sys.modules[m]

    for p in list(sys.path_importer_cache.keys()):
        if module in p:
            del sys.path_importer_cache[p]

    try:
        del module
    except:
        pass


try:
    sys.path.insert(0, noarch_lib)
    import OpenSSL as oss_test
    xlog.info("use build-in openssl lib")
except Exception as e1:
    xlog.info("import build-in openssl fail:%r", e1)
    
    sys.path.pop(0)
    del sys.path_importer_cache[noarch_lib]
    unload("OpenSSL")
    unload("cryptography")
    unload("cffi")
    try:
        import OpenSSL
    except Exception as e2:
        xlog.exception("import system python-OpenSSL fail:%r", e2)
        print("Try install python-openssl\r\n")
        raw_input("Press Enter to continue...")
        os._exit(0)


import config
import web_control
import module_init
import update
import setup_win_python
import update_from_github


def exit_handler():
    print 'Stopping all modules before exit!'
    module_init.stop_all()
    web_control.stop()

atexit.register(exit_handler)


def main():
    # change path to launcher
    global __file__
    __file__ = os.path.abspath(__file__)
    if os.path.islink(__file__):
        __file__ = getattr(os, 'readlink', lambda x: x)(__file__)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    current_version = update_from_github.current_version()

    xlog.info("start XX-Net %s", current_version)

    web_control.confirm_xxnet_exit()

    setup_win_python.check_setup()

    last_run_version = config.get(["modules", "launcher", "last_run_version"], "0.0.0")
    if last_run_version != current_version:
        import post_update
        post_update.run(last_run_version)
        config.set(["modules", "launcher", "last_run_version"], current_version)
        config.save()

    module_init.start_all_auto()

    web_control.start()

    if has_desktop and config.get(["modules", "launcher", "popup_webui"], 1) == 1:
        host_port = config.get(["modules", "launcher", "control_port"], 8085)
        import webbrowser
        webbrowser.open("http://127.0.0.1:%s/" % host_port)

    update.start()

    if config.get(["modules", "launcher", "show_systray"], 1):
        sys_tray.serve_forever()
    else:
        while True:
            time.sleep(100)

    module_init.stop_all()
    sys.exit()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt: # Ctrl + C on console
        module_init.stop_all()
        os._exit(0)
    except Exception as e:
        xlog.exception("launcher except:%r", e)

        raw_input("Press Enter to continue...")

