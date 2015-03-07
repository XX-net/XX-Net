#!/usr/bin/env python
# coding:utf-8

import os, sys

current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))
noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

if sys.platform == "linux" or sys.platform == "linux2":
    from gtk_tray import sys_tray
elif sys.platform == "win32":
    current_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_path)
    from win_tray import sys_tray
else:
    from non_tray import sys_tray

import atexit
import logging
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

    #config.load()
    if config.get(["modules", "launcher", "popup_webui"], 1) == 1:
        webbrowser.open("http://127.0.0.1:8085/")

    update.start()


    sys_tray.serve_forever()

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
