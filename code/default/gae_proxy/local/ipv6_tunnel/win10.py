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

enable_ipv6_temp = os.path.join(current_path, 'enable_ipv6_temp.bat')
disable_ipv6_temp = os.path.join(current_path, 'disable_ipv6_temp.bat')
set_best_server_temp = os.path.join(current_path, 'set_best_server_temp.bat')

enable_cmds = """
:: Start
@echo off

:: Config servers
sc config RpcEptMapper start= auto
sc start RpcEptMapper

sc config DcomLaunch start= auto
sc start DcomLaunch

sc config RpcSs start= auto
sc start RpcSs

sc config nsi start= auto
sc start nsi
sc config Winmgmt start= auto
sc start Winmgmt

sc config Dhcp start= auto
sc start Dhcp

sc config WinHttpAutoProxySvc start= auto
sc start WinHttpAutoProxySvc

sc config iphlpsvc start= auto
sc start iphlpsvc

:: Reset IPv6
netsh interface ipv6 reset

netsh interface teredo set state type=%s servername=%s.

:: Set IPv6 prefixpolicies
:: 2001::/16 Aggregate global unicast address
:: 2002::/16 6to4 tunnel
:: 2001::/32 teredo tunnel
netsh interface ipv6 set prefixpolicies 2001::/16 35 1
netsh interface ipv6 set prefixpolicies 2002::/16 30 2
netsh interface ipv6 set prefixpolicies 2001::/32 25 2

:: Fix look up AAAA on teredo
:: http://technet.microsoft.com/en-us/library/bb727035.aspx
:: http://ipv6-or-no-ipv6.blogspot.com/2009/02/teredo-ipv6-on-vista-no-aaaa-resolving.html
Reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\Dnscache\Parameters /v AddrConfigControl /t REG_DWORD /d 0 /f

:: Enable all IPv6 parts
Reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters /v DisabledComponents /t REG_DWORD /d 0 /f

ipconfig /flushdns

:: Over & show state
@echo on

ipconfig /all
netsh interface ipv6 show teredo
netsh interface ipv6 show route
netsh interface ipv6 show interface
netsh interface ipv6 show prefixpolicies
netsh interface ipv6 show address
route print

@echo reboot system at first time!
@pause
"""


disable_cmds="""
netsh interface teredo set state disable
netsh interface 6to4 set state disabled
netsh interface isatap set state disabled
"""


def elevate(script_path):
    # use this if need admin
    import win32elevate
    try:
        win32elevate.elevateAdminRun(script_path)
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


def enable(is_local=False):
    if is_local:
        new_enable_cmds = enable_cmds % (client_type(), best_server())
        with open(enable_ipv6_temp, 'w') as fp:
            fp.write(new_enable_cmds)
        elevate(enable_ipv6_temp)


def disable(is_local=False):
    if is_local:
        with open(disable_ipv6_temp, 'w') as fp:
            fp.write(disable_cmds)
        elevate(disable_ipv6_temp)


def set_best_server(is_local=False):
    if is_local:
        set_server_cmds = ("netsh interface teredo set state %s %s. default default default"
                           % (client_type(), best_server()))
        with open(set_best_server_temp, 'w') as fp:
            fp.write(set_server_cmds)
        elevate(set_best_server_temp)


if __name__ == '__main__':
    enable(True)