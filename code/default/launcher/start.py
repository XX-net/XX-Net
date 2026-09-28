#!/usr/bin/env python3
# coding:utf-8
# =============================================================================
# XX-Net Launcher Module
# Version: v5.16.6-Security-R2
# Last Modified: 2026-07-02
# Modifications:
#   - v5.16.6-Security-R1: Added config validation, signal handling, resource cleanup
#   - v5.16.6-Security-R2: Added audit logging integration (startup/shutdown)
# =============================================================================

import platform
import os
import sys
import time
import traceback
import atexit
import signal
import socket

# reduce resource request for threading
# for OpenWrt
import threading
try:
    if sys.version_info >= (3, 14):
        # Python 3.14 checks C stack usage and raises RecursionError on 64K stacks.
        threading.stack_size(256 * 1024)
    else:
        threading.stack_size(64 * 1024)
except:
    pass


current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_path)
default_path = os.path.abspath(os.path.join(current_path, os.pardir))
noarch_lib = os.path.abspath(os.path.join(default_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

if sys.platform == "darwin":
    darwin_lib = os.path.abspath(os.path.join(default_path, 'lib', 'darwin'))
    if os.path.isdir(darwin_lib):
        sys.path.insert(0, darwin_lib)

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

from audit import get_audit, audit_startup, audit_shutdown
audit = get_audit(data_path)

import sys_platform
from config import config
import web_control
import module_init
import update
import update_from_github
import download_modules
import global_var


def validate_config():
    xlog.info("Validating configuration...")
    
    required_modules = ["launcher", "gae_proxy", "x_tunnel", "smart_router"]
    for module in required_modules:
        enable_key = f"enable_{module}"
        if not hasattr(config, enable_key):
            setattr(config, enable_key, 0 if module != "launcher" else 1)
            xlog.warn(f"Missing config {enable_key}, set to default")
    
    if not hasattr(config, 'control_port') or not isinstance(config.control_port, int):
        config.control_port = 8085
        xlog.warn("Invalid control_port, reset to 8085")
    
    if config.control_port < 1 or config.control_port > 65535:
        config.control_port = 8085
        xlog.warn("control_port out of range, reset to 8085")
    
    if not hasattr(config, 'control_ip'):
        config.control_ip = "127.0.0.1"
    
    if not hasattr(config, 'allow_remote_connect'):
        config.allow_remote_connect = 0
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        result = sock.bind(('127.0.0.1', config.control_port))
        sock.close()
    except socket.error as e:
        xlog.error(f"Port {config.control_port} is already in use: {e}")
        return False
    
    xlog.info("Configuration validation passed")
    return True


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
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)
    except Exception as e:
        xlog.debug(f"Failed to set signal handlers: {e}")


current_version = update_from_github.current_version()

xlog.info("=" * 60)
xlog.info(f"XX-Net Version: {current_version}")
xlog.info(f"Python version: {sys.version}")
xlog.info(f"System: {platform.system()} | {platform.version()} | {platform.architecture()}")
xlog.info(f"Data path: {data_path}")
xlog.info(f"Code path: {current_path}")
xlog.info("=" * 60)

from front_base import openssl_wrap
xlog.info(f"TLS implementation: {openssl_wrap.implementation}")

try:
    import OpenSSL
    xlog.info("pyOpenSSL loaded successfully")
except Exception as e2:
    xlog.warning(f"pyOpenSSL import failed: {e2}")

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
    sys.exit(1)


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
            xlog.warning(f"Failed to remove Running.Lck: {e}")
        
        audit_shutdown()
        
        xlog.info('XX-Net shutdown complete')
    except Exception as e:
        xlog.exception(f"exit_handler exception: {e}")
        try:
            os._exit(1)
        except:
            pass


atexit.register(exit_handler)
setup_signal_handlers()

has_desktop = sys_platform.has_desktop


def main():
    global __file__
    __file__ = os.path.abspath(__file__)
    if os.path.islink(__file__):
        __file__ = getattr(os, 'readlink', lambda x: x)(__file__)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    audit_startup()

    if not validate_config():
        xlog.error("Configuration validation failed, exiting")
        input("Press Enter to continue...")
        return

    if sys.platform == "win32":
        try:
            import win_compat_suggest
            if config.show_compat_suggest:
                win_compat_suggest.main()
            
            ports_resolve_solution = win_compat_suggest.Win10PortReserveSolution()
            if not ports_resolve_solution.check_and_resolve():
                xlog.error("Port reservation check failed")
                return
        except Exception as e:
            xlog.exception(f"Windows compatibility check failed: {e}")
            return
    elif sys.platform == "darwin":
        try:
            import resource
            new_soft_limit = 4096
            new_hard_limit = 4096
            resource.setrlimit(resource.RLIMIT_NOFILE, (new_soft_limit, new_hard_limit))
            xlog.info(f"New open file limits set to: Soft={new_soft_limit}, Hard={new_hard_limit}")
        except Exception as e:
            xlog.warning(f"Failed to set file limits on macOS: {e}")

    try:
        web_control.confirm_xxnet_not_running()
    except Exception as e:
        xlog.error(f"Failed to confirm XX-Net not running: {e}")
        return

    try:
        import post_update
        post_update.check()
    except Exception as e:
        xlog.warning(f"Post-update check failed: {e}")

    allow_remote = 0
    no_mess_system = 0
    no_popup = 0
    no_systray = 0
    
    for s in sys.argv[1:]:
        xlog.info(f"Command argument: {s}")
        if s == "-allow_remote":
            allow_remote = 1
        elif s == "-no_mess_system":
            no_mess_system = 1
        elif s == "-no_popup":
            no_popup = 1
        elif s == "-no_systray":
            no_systray = 1
        else:
            xlog.warning(f"Unknown argument: {s}")

    if allow_remote or config.allow_remote_connect:
        xlog.info("Starting with remote connections allowed")
        module_init.xargs["allow_remote"] = 1

    if os.getenv("NOT_MESS_SYSTEM", "0") != "0" or no_mess_system or config.no_mess_system:
        xlog.info("Starting in no_mess_system mode - no CA import, no desktop shortcuts")
        module_init.xargs["no_mess_system"] = 1
        update.should_create_desktop_shortcut = False

    restart_from_except = os.path.isfile(running_file)

    try:
        update.start()
        xlog.info("Update module started")
    except Exception as e:
        xlog.error(f"Failed to start update module: {e}")

    try:
        module_init.start_all_auto()
        xlog.info("All modules started successfully")
    except Exception as e:
        xlog.exception(f"Failed to start modules: {e}")
        module_init.stop_all()
        return

    try:
        web_control.start(allow_remote)
        xlog.info(f"Web control started on {config.control_ip}:{config.control_port}")
    except Exception as e:
        xlog.exception(f"Failed to start web control: {e}")
        module_init.stop_all()
        return

    if has_desktop and config.popup_webui == 1 and not restart_from_except and not no_popup:
        try:
            host_port = config.control_port
            import webbrowser
            url = f"http://localhost:{host_port}/"
            xlog.debug(f"Opening browser: {url}")
            webbrowser.open(url)
        except Exception as e:
            xlog.warning(f"Failed to open browser: {e}")

    if has_desktop:
        try:
            download_modules.start_download()
            xlog.info("Module download started")
        except Exception as e:
            xlog.warning(f"Failed to start module download: {e}")

    try:
        update_from_github.cleanup()
    except Exception as e:
        xlog.debug(f"Cleanup failed: {e}")

    try:
        if config.show_systray and not no_systray:
            xlog.info("Starting system tray")
            sys_platform.show_systray()
        else:
            xlog.info("Running in console mode")
            while global_var.running:
                time.sleep(10)
    except Exception as e:
        xlog.exception(f"Main loop exception: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        xlog.warn("KeyboardInterrupt received")
        global_var.running = False
        module_init.stop_all()
        web_control.stop()
        os._exit(0)
    except SystemExit as e:
        xlog.info(f"SystemExit: {e}")
        raise
    except Exception as e:
        xlog.exception(f"Launcher exception: {e}")
        try:
            input("Press Enter to continue...")
        except:
            pass
        os._exit(1)