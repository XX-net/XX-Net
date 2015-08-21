import subprocess
import threading
import launcher_log
import os
import sys
import config

import web_control
import time
proc_handler = {}


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir))
if root_path not in sys.path:
    sys.path.append(root_path)

def start(module):
    if not os.path.isdir(os.path.join(root_path, module)):
        return

    try:
        if not module in config.config["modules"]:
            launcher_log.error("module not exist %s", module)
            raise

        if module in proc_handler:
            launcher_log.error("module %s is running", module)
            return "module is running"

        if module not in proc_handler:
            proc_handler[module] = {}

        if os.path.isfile(os.path.join(root_path, module, "__init__.py")):
            if "imp" not in proc_handler[module]:
                proc_handler[module]["imp"] = __import__(module, globals(), locals(), ['local', 'start'], -1)

            _start = proc_handler[module]["imp"].start
            p = threading.Thread(target = _start.main)
            p.daemon = True
            p.start()
            proc_handler[module]["proc"] = p

            while not _start.client.ready:
                time.sleep(0.1)
        else:
            script_path = os.path.join(root_path, module, 'start.py')
            if not os.path.isfile(script_path):
                launcher_log.warn("start module script not exist:%s", script_path)
                return "fail"

            proc_handler[module]["proc"] = subprocess.Popen([sys.executable, script_path], shell=False)


        launcher_log.info("%s started", module)

    except Exception as e:
        launcher_log.exception("start module %s fail:%s", module, e)
        return "Except:%s" % e
    return "start success."

def stop(module):
    try:
        if not module in proc_handler:
            launcher_log.error("module %s not running", module)
            return

        if os.path.isfile(os.path.join(root_path, module, "__init__.py")):

            _start = proc_handler[module]["imp"].start
            _start.client.terminate()
            launcher_log.debug("module %s stopping", module)
            while _start.client.ready:
                time.sleep(0.1)
        else:
            proc_handler[module]["proc"].terminate()  # Sends SIGTERM
            proc_handler[module]["proc"].wait()

        del proc_handler[module]

        launcher_log.info("module %s stopped", module)
    except Exception as e:
        launcher_log.exception("stop module %s fail:%s", module, e)
        return "Except:%s" % e
    return "stop success."

def start_all_auto():
    for module in config.config["modules"]:
        if module == "launcher":
            continue
        if not os.path.isdir(os.path.join(root_path, module)):
            continue
        if "auto_start" in config.config['modules'][module] and config.config['modules'][module]["auto_start"]:
            start_time = time.time()
            start(module)
            #web_control.confirm_module_ready(config.get(["modules", module, "control_port"], 0))
            finished_time = time.time()
            launcher_log.info("start %s time cost %d", module, (finished_time - start_time) * 1000)

def stop_all():
    running_modules = [k for k in proc_handler]
    for module in running_modules:
        stop(module)

