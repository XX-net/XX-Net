#!/usr/bin/env python
# coding:utf-8

import os, sys
import logging

current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))
noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

if sys.platform == "linux" or sys.platform == "linux2":
    from gtk_tray import sys_tray
elif sys.platform == "win32":
    from win_tray import sys_tray
elif sys.platform == "darwin":
    darwin_lib = os.path.abspath( os.path.join(python_path, 'lib', 'darwin'))
    sys.path.append(darwin_lib)
    extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjc"
    sys.path.append(extra_lib)

    try:
        import mac_tray as sys_tray
    except:
        from non_tray import sys_tray
else:
    logging.warn("detect platform fail:%s", sys.platform)
    from non_tray import sys_tray

import time
import atexit
import webbrowser
import web_control
import module_init
import update
import config
import setup_win_python

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

    web_control.confirm_xxnet_exit()

    setup_win_python.check_setup()

    module_init.start_all_auto()

    web_control.start()


    if config.get(["modules", "launcher", "popup_webui"], 1) == 1:
        webbrowser.open("http://127.0.0.1:8085/")

    update.start()

    if config.get(["modules", "launcher", "show_systray"], 1):
        sys_tray.serve_forever()
    else:
        while True:
            time.sleep(100)

    module_init.stop_all()
    sys.exit()



if __name__ == '__main__':

    current_path = os.path.dirname(os.path.abspath(__file__))
    version = current_path.split(os.path.sep)[-1]
    logging.info("launcher version: %s", version)

    try:
        main()
    except KeyboardInterrupt: # Ctrl + C on console
        sys.exit
