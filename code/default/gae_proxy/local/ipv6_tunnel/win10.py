#!/usr/bin/env python2
# coding:utf-8

import os
import sys
import time
from .common import *

current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data', "gae_proxy"))
if not os.path.isdir(data_path):
    data_path = current_path

if __name__ == "__main__":
    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)

    if sys.platform == "win32":
        win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
        sys.path.append(win32_lib)


from xlog import getLogger
xlog = getLogger("gae_proxy")


# TODO：Help to reset ipv6 if system Teredo Interface not exist
# download http://download.microsoft.com/download/3/F/3/3F3CA0F7-2FAF-4C51-8DDF-3516B4D91975/MicrosoftEasyFix20164.mini.diagcab


# TODO: Win7 need to change the interface name as the real one.
# can use ifconfig to get it.

# TODO; Win10 Home and Win10 Profession is different.

enable_cmds = """
# Start
net start "ip helper"
netsh int ipv6 reset

netsh int teredo set state default
netsh int 6to4 set state default
netsh int isatap set state default
netsh int teredo set state server=teredo.remlab.net
netsh int ipv6 set teredo enterpriseclient
netsh int ter set state enterpriseclient
route DELETE ::/0
netsh int ipv6 add route ::/0 "Teredo Tunneling Pseudo-Interface"
netsh int ipv6 set prefix 2002::/16 30 1
netsh int ipv6 set prefix 2001::/32 5 1
Reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\Dnscache\Parameters /v AddrConfigControl /t REG_DWORD /d 0 /f

netsh int teredo set state default
netsh int 6to4 set state default
netsh int isatap set state default
netsh int teredo set state server=teredo.remlab.net
netsh int ipv6 set teredo enterpriseclient
netsh int ter set state enterpriseclient
route DELETE ::/0
netsh int ipv6 add route ::/0 "Teredo Tunneling Pseudo-Interface"
netsh int ipv6 set prefix 2002::/16 30 1
netsh int ipv6 set prefix 2001::/32 5 1
Reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\Dnscache\Parameters /v AddrConfigControl /t REG_DWORD /d 0 /f

ipconfig /all
ipconfig /flushdns
netsh int ipv6 show teredo
netsh int ipv6 show route
netsh int ipv6 show int
netsh int ipv6 show prefix
netsh int ipv6 show address
route print

#
# reboot system at first time.
# 
"""


disable_cmds="""
netsh interface teredo set state disable
netsh interface 6to4 set state disabled
netsh interface isatap set state disabled
"""


def elevate(cmd):
    # use this if need admin
    import win32elevate
    try:
        win32elevate.elevateAdminRun(cmd)
    except Exception as e:
        xlog.warning('elevate e:%r', e)


last_get_state_time = 0
last_state = "unknown"


def get_teredo_interface():
    r = run("ifconfig /all")
    last_state = get_line_value(r, 6)


def state():
    global last_get_state_time, last_state
    if time.time() - last_get_state_time < 5:
        return last_state

    last_get_state_time = time.time()
    r = run("netsh interface Teredo show state")
    xlog.debug("netsh state: %s", r)
    last_state = get_line_value(r, 6)
    if last_state == "offline":
        last_state = "disable"
    elif last_state in ["qualified", "dormant"]:
        last_state = "enable"

    return last_state


def enable():
    new_enable_cmds = enable_cmds.replace("teredo.remlab.net", best_server())
    r = run_cmds(new_enable_cmds)
    return r


def disable():
    r = run_cmds(disable_cmds)
    return r


if __name__ == '__main__':
    print enable()