#!/usr/bin/env python3
# coding:utf-8
# =============================================================================
# XX-Net Config Module
# Version: v5.16.6-Security-R1
# Last Modified: 2026-07-02
# Modifications:
#   - v5.16.6-Security-R1: Added config validation, version migration, secure defaults
# =============================================================================

import os
import subprocess
import locale
import json
import hashlib
import time

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
backup_config_path = os.path.join(data_path, 'launcher', 'config.json.bak')

CONFIG_VERSION = "2.0"


def backup_config():
    if os.path.isfile(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(backup_config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            xlog.debug("Config backed up to %s", backup_config_path)
        except Exception as e:
            xlog.warning(f"Failed to backup config: {e}")


def validate_and_migrate_config():
    if not os.path.isfile(config_path):
        xlog.info("Config file not found, creating new one")
        return

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        xlog.error(f"Config file corrupted: {e}, restoring from backup")
        if os.path.isfile(backup_config_path):
            try:
                with open(backup_config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                xlog.info("Config restored from backup")
            except Exception as e2:
                xlog.error(f"Failed to restore from backup: {e2}")
                return
        return

    old_version = data.get("_config_version", "1.0")
    if old_version != CONFIG_VERSION:
        xlog.info(f"Migrating config from version {old_version} to {CONFIG_VERSION}")
        _migrate_config(data, old_version)
        data["_config_version"] = CONFIG_VERSION
        try:
            backup_config()
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            xlog.info("Config migration completed")
        except Exception as e:
            xlog.error(f"Failed to save migrated config: {e}")


def _migrate_config(data, old_version):
    if old_version == "1.0":
        if "webui_auth" not in data:
            data["webui_auth"] = {}
        if "no_mess_system" not in data:
            data["no_mess_system"] = 0
        if "enable_x_tunnel" not in data:
            data["enable_x_tunnel"] = 1


def validate_config_value(key, value):
    validations = {
        "control_port": lambda v: isinstance(v, int) and 1 <= v <= 65535,
        "control_ip": lambda v: isinstance(v, str) and (v == "127.0.0.1" or v == "0.0.0.0"),
        "allow_remote_connect": lambda v: isinstance(v, int) and v in (0, 1),
        "show_systray": lambda v: isinstance(v, int) and v in (0, 1),
        "popup_webui": lambda v: isinstance(v, int) and v in (0, 1),
        "auto_start": lambda v: isinstance(v, int) and v in (0, 1),
        "no_mess_system": lambda v: isinstance(v, int) and v in (0, 1),
        "check_update": lambda v: v in ("dont-check", "stable", "notice-stable", "test", "notice-test"),
        "os_proxy_mode": lambda v: v in ("pac", "gae", "x_tunnel", "smart_router", "disable"),
        "global_proxy_type": lambda v: v in ("HTTP", "SOCKS4", "SOCKS5"),
        "enable_gae_proxy": lambda v: isinstance(v, int) and v in (0, 1),
        "enable_x_tunnel": lambda v: isinstance(v, int) and v in (0, 1),
        "enable_smart_router": lambda v: isinstance(v, int) and v in (0, 1),
    }
    
    if key in validations:
        return validations[key](value)
    return True


validate_and_migrate_config()

config = xconfig.Config(config_path)

config.set_var("_config_version", CONFIG_VERSION)
config.set_var("control_ip", "127.0.0.1")
config.set_var("control_port", 8085)
config.set_var("allowed_refers", [""])

config.set_var("language", "")
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

config.set_var("check_update", "notice-stable")
config.set_var("keep_old_ver_num", 1)
config.set_var("postUpdateStat", "noChange")
config.set_var("current_version", "")
config.set_var("ignore_version", "")
config.set_var("last_run_version", "")
config.set_var("skip_stable_version", "")
config.set_var("skip_test_version", "")

config.set_var("last_path", "")
config.set_var("update_uuid", "")

config.set_var("clear_cache", 0)
config.set_var("del_win", 0)
config.set_var("del_mac", 0)
config.set_var("del_linux", 0)
config.set_var("del_gae", 0)
config.set_var("del_gae_server", 0)
config.set_var("del_xtunnel", 0)
config.set_var("del_smartroute", 0)

config.set_var("all_modules", ["launcher", "gae_proxy", "x_tunnel", "smart_router"])
config.set_var("enable_launcher", 1)
config.set_var("enable_x_tunnel", 1)
config.set_var("enable_gae_proxy", 0)
config.set_var("enable_smart_router", 1)

config.set_var("os_proxy_mode", "pac")

config.set_var("global_proxy_enable", 0)
config.set_var("global_proxy_type", "HTTP")
config.set_var("global_proxy_host", "")
config.set_var("global_proxy_port", 0)
config.set_var("global_proxy_username", "")
config.set_var("global_proxy_password", "")

_original_save = config.save


def secure_save():
    try:
        backup_config()
        _original_save()
        xlog.debug("Config saved securely")
    except Exception as e:
        xlog.error(f"Failed to save config: {e}")


config.save = secure_save

try:
    config.load()
except Exception as e:
    xlog.warn(f"Loading config failed: {e}")
    try:
        if os.path.isfile(backup_config_path):
            xlog.info("Trying to load from backup")
            with open(backup_config_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            for key, value in backup_data.items():
                if validate_config_value(key, value):
                    setattr(config, key, value)
            xlog.info("Config loaded from backup")
    except Exception as e2:
        xlog.error(f"Failed to load from backup: {e2}")

for key in dir(config):
    if not key.startswith('_'):
        try:
            value = getattr(config, key)
            if not validate_config_value(key, value):
                xlog.warning(f"Invalid config value for {key}: {value}, resetting to default")
                setattr(config, key, config._default_values.get(key, value))
        except Exception as e:
            xlog.debug(f"Error validating config {key}: {e}")

app_name = "XX-Net"
valid_language = ['en_US', 'fa_IR', 'zh_CN', 'ru_RU']
try:
    fp = os.path.join(root_path, "code", "app_info.json")
    with open(fp, "r", encoding='utf-8') as fd:
        app_info = json.load(fd)
        if isinstance(app_info, dict) and "app_name" in app_info:
            app_name = app_info["app_name"]
except Exception as e:
    xlog.debug(f"load app_info except: {e}")


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
        except Exception:
            pass
    elif sys_platform.platform == "android":
        try:
            res = request("GET", "http://localhost:8084/env/")
            dat = json.loads(res.text)
            lang_code = dat.get("lang_code", "")
            xlog.debug(f"lang_code: {lang_code}")
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
            xlog.warn(f"get lang except: {e}")
            return "zh_CN"
    elif sys_platform.platform == "ios":
        lang_code = os.environ.get("IOS_LANG", "")
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
            return lang_code
        except Exception:
            pass
    return None


def get_language():
    if config.language:
        lang = config.language
    else:
        lang = _get_os_language()

    if lang not in valid_language:
        lang = 'en_US'

    return lang


def generate_config_hash():
    try:
        config_data = {}
        for key in dir(config):
            if not key.startswith('_'):
                config_data[key] = getattr(config, key)
        config_str = json.dumps(config_data, sort_keys=True)
        return hashlib.sha256(config_str.encode('utf-8')).hexdigest()[:16]
    except Exception as e:
        xlog.debug(f"Failed to generate config hash: {e}")
        return ""


config_hash = generate_config_hash()
xlog.debug(f"Config hash: {config_hash}")