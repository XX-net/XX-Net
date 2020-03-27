#!/usr/bin/env python

import os

import xconfig

from xlog import getLogger
xlog = getLogger("launcher")

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data'))
config_path = os.path.join(data_path, 'launcher', 'config.json')


config = xconfig.Config(config_path)

config.set_var("control_ip", "127.0.0.1")
config.set_var("control_port", 8085)

# System config
config.set_var("language", "")
config.set_var("allow_remote_connect", 0)
config.set_var("show_systray", 1)
config.set_var("no_mess_system", 0)
config.set_var("auto_start", 0)
config.set_var("popup_webui", 1)

config.set_var("gae_show_detail", 0)
config.set_var("show_compat_suggest", 1)

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
config.set_var("enable_gae_proxy", 1)
config.set_var("enable_smart_router", 1)

config.set_var("os_proxy_mode", "pac") # can be: gae, x_tunnel, smart_router, disable

# Proxy
config.set_var("global_proxy_enable", 0)
config.set_var("global_proxy_type", "HTTP") # can be: HTTP/ SOCKS4/ SOCKs5
config.set_var("global_proxy_host", "")
config.set_var("global_proxy_port", 0)
config.set_var("global_proxy_username", "")
config.set_var("global_proxy_password", "")

config.load()


