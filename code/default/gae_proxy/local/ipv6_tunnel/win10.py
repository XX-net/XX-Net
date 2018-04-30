#!/usr/bin/env python2
# coding:utf-8

import os
import sys
import time
import platform
from .common import *
from .pteredor import local_ip_startswith

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
netsh interface ipv6 reset

netsh interface teredo set state type=%s servername=%s.

# Keep teredo interface route
route DELETE ::/0
netsh interface ipv6 add route ::/0 "Teredo Tunneling Pseudo-Interface"

# Set IPv6 prefixpolicies
# 2001::/16 Aggregate global unicast address
# 2002::/16 6to4 tunnel
# 2001::/32 teredo tunnel
netsh interface ipv6 set prefixpolicies 2001::/16 35 1
netsh interface ipv6 set prefixpolicies 2002::/16 30 2
netsh interface ipv6 set prefixpolicies 2001::/32 25 2

# Fix look up AAAA on teredo
# http://technet.microsoft.com/en-us/library/bb727035.aspx
# http://ipv6-or-no-ipv6.blogspot.com/2009/02/teredo-ipv6-on-vista-no-aaaa-resolving.html
Reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\Dnscache\Parameters /v AddrConfigControl /t REG_DWORD /d 0 /f

# Enable all IPv6 parts
Reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters /v DisabledComponents /t REG_DWORD /d 0 /f

ipconfig /all
ipconfig /flushdns

netsh interface ipv6 show teredo
netsh interface ipv6 show route
netsh interface ipv6 show interface
netsh interface ipv6 show prefixpolicies
netsh interface ipv6 show address
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

client_ext = 'natawareclient' if float(platform.win32_ver()[0]) > 7 else 'enterpriseclient'

def client_type():
    ip = [line for line in run("route print").split("\r\n") if " 0.0.0.0 " in line][0].split()[-2]
    return client_ext if ip.startswith(local_ip_startswith) else 'client'


def get_teredo_interface():
    r = run("ifconfig /all")
    last_state = get_line_value(r, 6)


def state():
    global last_get_state_time, last_state
    if time.time() - last_get_state_time < 5:
        return last_state

    last_get_state_time = time.time()
    r = run("netsh interface teredo show state")
    xlog.debug("netsh state: %s", r)
    type = get_line_value(r, 2)
    last_state = get_line_value(r, 6)
    if type == "disabled" or last_state == "offline":
        last_state = "disable"
    elif last_state in ["qualified", "dormant"]:
        last_state = "enable"

    return last_state


def enable():
    new_enable_cmds = enable_cmds % (client_type(), best_server())
    r = run_cmds(new_enable_cmds)
    return r


def disable():
    r = run_cmds(disable_cmds)
    return r


def set_best_server():
    r = run("netsh interface teredo set state %s %s. default default default"
            % (client_type(), best_server()))
    return r


if __name__ == '__main__':
    print enable()