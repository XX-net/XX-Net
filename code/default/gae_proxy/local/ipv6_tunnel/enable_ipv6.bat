:: XX-Net
:: Enable IPV6
:: https://github.com/XX-net/XX-Net-dev/issues/53

:: https://www.zhihu.com/question/34541107/answer/137174053
@echo off
echo Get Admin
::ver|findstr "[6,10]\.[0-9]\.[0-9][0-9]*" > nul && (goto Main)
::ver|findstr "[3-5]\.[0-9]\.[0-9][0-9]*" > nul && (goto isBelowNT6)

:: :isBelowNT6

:Main
@echo off
cd /d "%~dp0"
cacls.exe "%SystemDrive%\System Volume Information" >nul 2>nul
if %errorlevel%==0 goto Admin
if exist "%temp%\getadmin.vbs" del /f /q "%temp%\getadmin.vbs"
echo Set RequestUAC = CreateObject^("Shell.Application"^)>"%temp%\getadmin.vbs"
echo RequestUAC.ShellExecute "%~s0","","","runas",1 >>"%temp%\getadmin.vbs"
echo WScript.Quit >>"%temp%\getadmin.vbs"
"%temp%\getadmin.vbs" /f
if exist "%temp%\getadmin.vbs" del /f /q "%temp%\getadmin.vbs"
exit

:Admin
@echo off


sc config RpcEptMapper start=auto
sc start RpcEptMapper

sc config DcomLaunch start=auto
sc start DcomLaunch

sc config RpcSs start=auto
sc start RpcSs

sc config nsi start=auto
sc start nsi
sc config Wingmt start=auto
sc start Winmgmt

sc config Dhcp start=auto
sc start Dhcp

sc config WinHttpAutoProxySvc start=auto
sc start WinHttpAutoProxySvc

sc config iphlpsvc start=auto
sc start iphlpsvc

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

Reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters /v DisabledComponents /t REG_DWORD /d 0 /f

:: Set Group Policy
:: HKLM\Software\Policies\Microsoft\Windows\TCPIP\v6Transition -Name Teredo_DefaultQualified 
:: HKLM\Software\Policies\Microsoft\Windows\TCPIP\v6Transition -Name Teredo_State 


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

ipconfig /flushdns

set time=%date:~0,4%-%date:~5,2%-%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
@call :output>..\..\..\..\..\data\gae_proxy\ipv6-state%time%.txt 
exit

:output
@echo off
ipconfig /all
netsh int ipv6 show teredo
netsh int ipv6 show route
netsh int ipv6 show int
netsh int ipv6 show prefix
netsh int ipv6 show address
route print
notepad ..\..\..\..\..\data\gae_proxy\ipv6-state%time%.txt
