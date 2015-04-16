
import os
import logging


import yaml


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir))
data_path = os.path.join(root_path, 'data', 'launcher', 'config.yaml')

config = {}
def load():
    global config, data_path
    try:
        config = yaml.load(file(data_path, 'r'))
        #print yaml.dump(config)
    except Exception as  exc:
        print "Error in configuration file:", exc


def save():
    global config, data_path
    try:
        yaml.dump(config, file(data_path, "w"))
    except Exception as e:
        logging.warn("save config %s fail %s", data_path, e)

def get(path, default_val=""):
    global config
    try:
        value = default_val
        cmd = "config"
        for p in path:
            cmd += '["%s"]' % p
        value = eval(cmd)
        return value
    except:
        return default_val

def _set(m, k_list, v):
    k0 = k_list[0]
    if len(k_list) == 1:
        m[k0] = v
        return
    if k0 not in m:
        m[k0] = {}
    _set(m[k0], k_list[1:], v)

def set(path, val):
    global config
    _set(config, path, val)


def scan_module_version(module):
    module_path = os.path.join(root_path, module)
    for filename in os.listdir(module_path):
        if os.path.isdir(os.path.join(module_path, filename)):
            return filename
    return False

def recheck_module_path():
    need_save_config = False

    modules = ["goagent", "launcher", "php_proxy"]
    for module in modules:
        current_version = get(["modules", module, "current_version"], "_")
        if os.path.isdir(os.path.join(root_path, module, current_version)):
            continue

        logging.info("module %s version %s not exist", module, current_version)
        current_version = scan_module_version(module)
        if not current_version:
            logging.error("recheck_module_path %s get version fail", module)
            continue

        set(["modules", module, "current_version"], current_version)
        logging.info("module %s auto upgrade to version %s", module, current_version)
        need_save_config = True

        if module != "launcher" and get(["modules", module, "auto_start"], -1) == -1:
            set(["modules", module, "auto_start"], 1)

    if get(["modules", "goagent", "control_port"], 0) == 0:
        set(["modules", "goagent", "control_port"], 8084)

    if get(["modules", "php_proxy", "control_port"], 0) == 0:
        set(["modules", "php_proxy", "control_port"], 8083)

    return need_save_config

def main():
    if os.path.isfile(data_path):
        load()

    if recheck_module_path():
        save()

main()

def test():
    load()
    val = get(["web_ui", "popup_webui"], 0)
    print val

def test2():
    set(["web_ui", "popup_webui"], 0)
    set(["web_ui", "popup"], 0)
    print config

if __name__ == "__main__":
    test2()
    #main()
    #a = eval('2*3')
    #eval("conf = {}")