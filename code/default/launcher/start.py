#!/usr/bin/env python3
# coding:utf-8

import signal
import socket
import platform
import os
import sys
import time
import traceback
import atexit

# reduce resource request for threading
# for OpenWrt
import threading
try:
    threading.stack_size(64 * 1024)
except Exception:
    pass


current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_path)
default_path = os.path.abspath(os.path.join(current_path, os.path.pardir))
noarch_lib = os.path.abspath(os.path.join(default_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

import env_info
data_path = env_info.data_path
data_launcher_path = os.path.join(data_path, 'launcher')


def create_data_path():
    try:
        if not os.path.isdir(data_path):
            os.makedirs(data_path, exist_ok=True)

        if not os.path.isdir(data_launcher_path):
            os.makedirs(data_launcher_path, exist_ok=True)

        data_gae_proxy_path = os.path.join(data_path, 'gae_proxy')
        if not os.path.isdir(data_gae_proxy_path):
            os.makedirs(data_gae_proxy_path, exist_ok=True)

        data_x_tunnel_path = os.path.join(data_path, 'x_tunnel')
        if not os.path.isdir(data_x_tunnel_path):
            os.makedirs(data_x_tunnel_path, exist_ok=True)

        data_smart_router_path = os.path.join(data_path, 'smart_router')
        if not os.path.isdir(data_smart_router_path):
            os.makedirs(data_smart_router_path, exist_ok=True)
    except Exception as e:
        print(f"Failed to create data directories: {e}")
        sys.exit(1)


create_data_path()

from xlog import getLogger
log_file = os.path.join(data_launcher_path, "launcher.log")
xlog = getLogger("launcher", log_path=data_launcher_path, save_start_log=500, save_warning_log=True)
xlog.set_buffer(100)

import sys_platform
from config import config
import web_control
import module_init
import update
import update_from_github
import download_modules
import global_var


def setup_signal_handlers():
    def signal_handler(signum, frame):
        signal_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else f"signal {signum}"
        xlog.warn(f"Received {signal_name}, shutting down...")
        global_var.running = False
        module_init.stop_all()
        web_control.stop()
        time.sleep(1)
        os._exit(0)

    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except Exception as e:
        xlog.debug(f"Failed to set signal handlers: {e}")


current_version = update_from_github.current_version()

xlog.info("start Version %s", current_version)
xlog.info("Python version: %s", sys.version)
xlog.info("System: %s|%s|%s", platform.system(), platform.version(), platform.architecture())
xlog.info("data path: %s", data_path)

from front_base import openssl_wrap
xlog.info("TLS implementation: %s", openssl_wrap.implementation)

try:
    import OpenSSL
except Exception as e2:
    print("import pyOpenSSL fail:", e2)

running_file = os.path.join(data_launcher_path, "Running.Lck")


def uncaught_exception_handler(etype, value, tb):
    if etype == KeyboardInterrupt:
        xlog.warn("KeyboardInterrupt, exiting gracefully...")
        global_var.running = False
        module_init.stop_all()
        web_control.stop()
        os._exit(0)

    exc_info = ''.join(traceback.format_exception(etype, value, tb))
    print(f"Uncaught Exception:\n{exc_info}")
    xlog.error(f"Uncaught Exception - type: {etype}, value: {value}, traceback:\n{exc_info}")
    try:
        global_var.running = False
        module_init.stop_all()
        web_control.stop()
    except Exception:
        pass


sys.excepthook = uncaught_exception_handler


def exit_handler():
    try:
        xlog.info('Initiating graceful shutdown...')
        global_var.running = False
        
        web_control.stop()
        
        module_init.stop_all()
        
        try:
            if os.path.isfile(running_file):
                os.remove(running_file)
                xlog.debug("Removed Running.Lck")
        except Exception as e:
            xlog.debug(f"Failed to remove Running.Lck: {e}")
    except Exception as e:
        xlog.error(f"Error during shutdown: {e}")


atexit.register(exit_handler)

has_desktop = sys_platform.has_desktop


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
    elif sys.platform == "darwin":
        import resource
        new_soft_limit = 4096
        new_hard_limit = 4096
        resource.setrlimit(resource.RLIMIT_NOFILE, (new_soft_limit, new_hard_limit))
        xlog.info(f"New open file limits set to: Soft={new_soft_limit}, Hard={new_hard_limit}")

    web_control.confirm_xxnet_not_running()

    import post_update
    post_update.check()

    allow_remote = 0
    no_mess_system = 0
    no_popup = 0
    no_systray = 0
    if len(sys.argv) > 1:
        for s in sys.argv[1:]:
            xlog.info("command args:%s", s)
            if s == "-allow_remote":
                allow_remote = 1
            elif s == "-no_mess_system":
                no_mess_system = 1
            elif s == "-no_popup":
                no_popup = 1
            elif s == "-no_systray":
                no_systray = 1

    if allow_remote or config.allow_remote_connect:
        xlog.info("start with allow remote connect.")
        module_init.xargs["allow_remote"] = 1

    if os.getenv("NOT_MESS_SYSTEM", "0") != "0" or no_mess_system or config.no_mess_system:
        xlog.info("start with no_mess_system, no CA will be imported to system, not create desktop.")
        module_init.xargs["no_mess_system"] = 1
        update.should_create_desktop_shortcut = False

    if os.path.isfile(running_file):
        restart_from_except = True
    else:
        restart_from_except = False

    update.start()
    # put update before start all modules, generate uuid for x-tunnel.

    module_init.start_all_auto()
    web_control.start(allow_remote)

    if has_desktop and config.popup_webui == 1 and not restart_from_except and not no_popup:
        host_port = config.control_port
        import webbrowser
        url = "http://localhost:%s/" % host_port
        xlog.debug("Popup %s on startup", url)
        webbrowser.open(url)

    if has_desktop:
        download_modules.start_download()
    update_from_github.cleanup()

    if config.show_systray and not no_systray:
        sys_platform.show_systray()
    else:
        while global_var.running:
            time.sleep(10)


try:
    main()
except KeyboardInterrupt:  # Ctrl + C on console
    global_var.running = False
    module_init.stop_all()
    os._exit(0)
    sys.exit()
except Exception as e:
    xlog.exception("launcher except:%r", e)
    input("Press Enter to continue...")
