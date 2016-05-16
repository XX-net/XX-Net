
import os
from instances import xlog
import yaml
from distutils.version import LooseVersion


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data'))
config_path = os.path.join(data_path, 'launcher', 'config.yaml')

config = {}
def load():
    global config, config_path
    try:
        config = yaml.load(file(config_path, 'r'))
        #print yaml.dump(config)
    except Exception as  exc:
        print "Error in configuration file:", exc


def save():
    global config, config_path
    try:
        yaml.dump(config, file(config_path, "w"))
    except Exception as e:
        xlog.warn("save config %s fail %s", config_path, e)


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


def recheck_module_path():
    global config
    need_save_config = False

    xxnet_port = get(["modules", "gae_proxy", "LISTEN_PORT"], 8087)

    modules = ["gae_proxy", "launcher", "php_proxy", "x_tunnel"]
    for module in modules:
        if module not in ["launcher", "php_proxy"]:
            if not os.path.isdir(os.path.join(root_path, module)):
                del config[module]
                continue

            if get(["modules", module, "auto_start"], -1) == -1:
                set(["modules", module, "auto_start"], 1)

    if get(["modules", "launcher", "xxnet_port"], 0) == 0:
        set(["modules", "launcher", "xxnet_port"], xxnet_port)

    if get(["modules", "launcher", "control_port"], 0) == 0:
        set(["modules", "launcher", "control_port"], 8085)
        set(["modules", "launcher", "allow_remote_connect"], 0)

    if get(["modules", "launcher", "proxy"], 0) == 0:
        # default enable PAC on startup.
        set(["modules", "launcher", "proxy"], "pac")

    #if get(["modules", "gae_proxy", "control_port"], 0) == 0:
    #    set(["modules", "gae_proxy", "control_port"], 8084)

    if get(["modules", "php_proxy", "control_port"], 0) == 0:
        set(["modules", "php_proxy", "control_port"], 8083)

    return need_save_config


def init():
    if os.path.isfile(config_path):
        load()

    if recheck_module_path():
        save()
init()
