#!/usr/bin/env python

import os
import subprocess
import locale
import json

import sys_platform
from simple_http_client import request
import xconfig
from xlog import getLogger
xlog = getLogger("launcher")

current_path = os.path.dirname(os.path.abspath(__file__))
version_path = os.path.abspath(os.path.join(current_path, os.pardir))
root_path = os.path.abspath(os.path.join(version_path, os.pardir, os.pardir))

import env_info
data_path = env_info.data_path
config_path = os.path.join(data_path, 'launcher', 'config.json')


config = xconfig.Config(config_path)

config.set_var("control_ip", "127.0.0.1")
config.set_var("control_port", 8085)
config.set_var("allowed_refers", [""])

# System config
config.set_var("language", "")  # en_US,
config.set_var("allow_remote_connect", 0)
config.set_var("show_systray", 1)
config.set_var("show_android_notification", 1)
config.set_var("no_mess_system", 0)
config.set_var("auto_start", 0)
config.set_var("popup_webui", 1)
config.set_var("webui_auth", {})

config.set_var("gae_show_detail", 0)
config.set_var("show_compat_suggest", 1)
config.set_var("proxy_by_app", 0)
config.set_var("enabled_app_list", [])

# version control
config.set_var("check_update", "notice-stable") # can be: "dont-check", "stable", "notice-stable", "test", "notice-test"
config.set_var("keep_old_ver_num", 1)
config.set_var("postUpdateStat", "noChange") # "noChange", "isNew", "isPostUpdate"
config.set_var("current_version", "")
config.set_var("ignore_version", "")
config.set_var("last_run_version", "")
config.set_var("skip_stable_version", "")
config.set_var("skip_test_version", "")

# update:
config.set_var("last_path", "")
config.set_var("update_uuid", "")

# savedisk
config.set_var("clear_cache", 0)
config.set_var("del_win", 0)
config.set_var("del_mac", 0)
config.set_var("del_linux", 0)
config.set_var("del_gae", 0)
config.set_var("del_gae_server", 0)
config.set_var("del_xtunnel", 0)
config.set_var("del_smartroute", 0)

# Module
config.set_var("all_modules", ["launcher", "gae_proxy", "x_tunnel", "smart_router"])
config.set_var("enable_launcher", 1)
config.set_var("enable_x_tunnel", 1)
config.set_var("enable_gae_proxy", 0)
config.set_var("enable_smart_router", 1)

config.set_var("os_proxy_mode", "pac") # can be: gae, x_tunnel, smart_router, disable

# Proxy
config.set_var("global_proxy_enable", 0)
config.set_var("global_proxy_type", "HTTP") # can be: HTTP/ SOCKS4/ SOCKs5
config.set_var("global_proxy_host", "")
config.set_var("global_proxy_port", 0)
config.set_var("global_proxy_username", "")
config.set_var("global_proxy_password", "")

try:
    config.load()
except Exception as e:
    xlog.warn("loading config e:%r", e)

app_name = "XX-Net"
valid_language = ['en_US', 'fa_IR', 'zh_CN', 'ru_RU']
try:
    fp = os.path.join(root_path, "code", "app_info.json")
    with open(fp, "r") as fd:
        app_info = json.load(fd)
        app_name = app_info["app_name"]
except Exception as e:
    print("load app_info except:", e)
    pass


def _get_os_language():

    if sys_platform.platform == "mac":
        try:
            lang_code = subprocess.check_output(["/usr/bin/defaults", 'read', 'NSGlobalDomain', 'AppleLanguages'])
            if b'zh' in lang_code:
                return 'zh_CN'
            elif b'en' in lang_code:
                return 'en_US'
            elif b'fa' in lang_code:
                return 'fa_IR'
            elif b'ru' in lang_code:
                return 'ru_RU'

        except:
            pass
    elif sys_platform.platform == "android":
        try:
            res = request("GET", "http://localhost:8084/env/")
            dat = json.loads(res.text)
            lang_code = dat["lang_code"]
            xlog.debug("lang_code:%s", lang_code)
            if 'zh' in lang_code:
                return 'zh_CN'
            elif 'en' in lang_code:
                return 'en_US'
            elif 'fa' in lang_code:
                return 'fa_IR'
            elif 'ru' in lang_code:
                return 'ru_RU'
            else:
                return None
        except Exception as e:
            xlog.warn("get lang except:%r", e)
            return "zh_CN"
    elif sys_platform.platform == "ios":
        lang_code = os.environ["IOS_LANG"]
        if 'zh' in lang_code:
            return 'zh_CN'
        elif 'en' in lang_code:
            return 'en_US'
        elif 'fa' in lang_code:
            return 'fa_IR'
        elif 'ru' in lang_code:
            return 'ru_RU'
        else:
            return None
    else:
        try:
            lang_code, code_page = locale.getdefaultlocale()
            # ('en_GB', 'cp1252'), en_US,
            return lang_code
        except:
            # Mac fail to run this
            pass


def get_language():
    if config.language:
        lang = config.language
    else:
        lang = _get_os_language()

    if lang not in valid_language:
        lang = 'en_US'

    return lang
