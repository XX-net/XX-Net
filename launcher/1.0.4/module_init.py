import subprocess
import logging
import os
import sys
import config


proc_handler = {}



current_path = os.path.dirname(os.path.abspath(__file__))

def start(module):

    try:
        #config.load()
        if not module in config.config["modules"]:
            logging.error("module not exist %s", module)
            raise

        if module in proc_handler:
            logging.error("module %s is running", module)
            return "module is running"

        version = config.config["modules"][module]["current_version"]
        logging.info("use %s version:%s", module, version)

        script_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, module, version, 'start.py'))
        proc_handler[module] = subprocess.Popen([sys.executable, script_path], shell=False)
        logging.info("%s %s started %s", module, version, script_path)

    except Exception as e:
        logging.exception("start module %s fail:%s", module, e)
        return "Except:%s" % e
    return "start success."

def stop(module):
    try:
        if not module in proc_handler:
            logging.error("module %s not running", module)
            return

        proc_handler[module].terminate()  # Sends SIGTERM
        proc_handler[module].wait()
        del proc_handler[module]

        logging.info("module %s stopped", module)
    except Exception as e:
        logging.exception("stop module %s fail:%s", module, e)
        return "Except:%s" % e
    return "stop success."

def start_all_auto():
    #config.load()
    for module in config.config["modules"]:
        if module == "launcher":
            continue
        if "auto_start" in config.config['modules'][module] and config.config['modules'][module]["auto_start"]:
            start(module)

def stop_all():
    running_modules = [k for k in proc_handler]
    for module in running_modules:
        stop(module)

