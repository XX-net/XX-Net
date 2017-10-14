@echo off


netsh interface teredo set state disable
netsh interface 6to4 set state disabled
netsh interface isatap set state disabled