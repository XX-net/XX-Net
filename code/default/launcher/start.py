#!/usr/bin/env python3
# coding:utf-8

import platform
import os
import sys
import time
import traceback
from datetime import datetime
import atexit

# reduce resource request for threading
# for OpenWrt
import threading
try:
    threading.stack_size(128 * 1024)
except:
    pass


current_path = os.path.dirname(os.path.abspath(__file__))
default_path = os.path.abspath(os.path.join(current_path, os.path.pardir))
data_path = os.path.abspath(os.path.join(default_path, os.path.pardir, os.path.pardir, 'data'))
data_launcher_path = os.path.join(data_path, 'launcher')
noarch_lib = os.path.abspath(os.path.join(default_path, 'lib', 'noarch'))
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


import sys_platform
from config import config
import web_control
import module_init
import update
import update_from_github
import download_modules

from xlog import getLogger

log_file = os.path.join(data_launcher_path, "launcher.log")
xlog = getLogger("launcher", file_name=log_file)

current_version = update_from_github.current_version()

xlog.info("start Version %s", current_version)
xlog.info("Python version: %s", sys.version)
xlog.info("System: %s|%s|%s", platform.system(), platform.version(), platform.architecture())

try:
    import OpenSSL
except Exception as e2:
    print("import pyOpenSSL fail:%r", e2)
    print("Try install python-openssl\r\n")
    input("Press Enter to continue...")
    os._exit(0)

running_file = os.path.join(data_launcher_path, "Running.Lck")


def uncaught_exception_handler(etype, value, tb):
    if etype == KeyboardInterrupt:  # Ctrl + C on console
        xlog.warn("KeyboardInterrupt, exiting...")
        module_init.stop_all()
        os._exit(0)

    exc_info = ''.join(traceback.format_exception(etype, value, tb))
    print(("uncaught Exception:\n" + exc_info))
    with open(os.path.join(data_launcher_path, "error.log"), "a") as fd:
        now = datetime.now()
        time_str = now.strftime("%b %d %H:%M:%S.%f")[:19]
        fd.write("%s type:%s value=%s traceback:%s" % (time_str, etype, value, exc_info))
    xlog.error("uncaught Exception, type=%s value=%s traceback:%s", etype, value, exc_info)
    # sys.exit(1)


sys.excepthook = uncaught_exception_handler


def exit_handler():
    xlog.info('Stopping all modules before exit!')
    module_init.stop_all()
    web_control.stop()


atexit.register(exit_handler)

has_desktop = True


def main():
    # change path to launcher
    global __file__
    __file__ = os.path.abspath(__file__)
    if os.path.islink(__file__):
        __file__ = getattr(os, 'readlink', lambda x: x)(__file__)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if sys.platform == "win32":
        import win_compat_suggest

        if config.show_compat_suggest:
            win_compat_suggest.main()

        ports_resolve_solution = win_compat_suggest.Win10PortReserveSolution()
        if not ports_resolve_solution.check_and_resolve():
            return

    web_control.confirm_xxnet_not_running()

    import post_update
    post_update.check()

    allow_remote = 0
    no_mess_system = 0
    if len(sys.argv) > 1:
        for s in sys.argv[1:]:
            xlog.info("command args:%s", s)
            if s == "-allow_remote":
                allow_remote = 1
            elif s == "-no_mess_system":
                no_mess_system = 1

    if allow_remote or config.allow_remote_connect:
        xlog.info("start with allow remote connect.")
        module_init.xargs["allow_remote"] = 1

    if os.getenv("NOT_MESS_SYSTEM", "0") != "0" or no_mess_system or config.no_mess_system:
        xlog.info("start with no_mess_system, no CA will be imported to system.")
        module_init.xargs["no_mess_system"] = 1

    if os.path.isfile(running_file):
        restart_from_except = True
    else:
        restart_from_except = False

    module_init.start_all_auto()
    web_control.start(allow_remote)

    if has_desktop and config.popup_webui == 1 and not restart_from_except:
        host_port = config.control_port
        import webbrowser
        webbrowser.open("http://localhost:%s/" % host_port)

    update.start()
    if has_desktop:
        download_modules.start_download()
    update_from_github.cleanup()

    if config.show_systray:
        sys_platform.show_systray()
    else:
        while True:
            time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:  # Ctrl + C on console
        module_init.stop_all()
        os._exit(0)
        sys.exit()
    except Exception as e:
        xlog.exception("launcher except:%r", e)
        input("Press Enter to continue...")
