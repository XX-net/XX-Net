#!/usr/bin/env python
# coding:utf-8


if __name__ == "__main__":
    import os, sys
    current_path = os.path.dirname(os.path.abspath(__file__))
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))
    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)

import webbrowser
from systray import SysTrayIcon
import os
import ctypes
import _winreg as winreg


import module_init
import update
import logging

class Win_tray():
    def __init__(self):
        icon_path = os.path.join(os.path.dirname(__file__), "web_ui", "favicon.ico")
        self.systray = SysTrayIcon(icon_path, "XX-Net", self.make_menu(), self.on_quit, left_click=self.on_show)

        reg_path = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
        self.INTERNET_SETTINGS = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            reg_path,
            0, winreg.KEY_ALL_ACCESS)

    def make_menu(self):
        import locale
        lang_code, code_page = locale.getdefaultlocale()
        if lang_code == "zh_CN":
            menu_options = ((u"设置", None, self.on_show),
                        (u"全局通过GoAgent代理上网", None, self.on_enable_proxy),
                        (u"全局PAC智能代理切换", None, self.on_enable_pac),
                        (u"取消全局代理", None, self.on_disable_proxy),
                        (u"重启 GoAgent", None, self.on_restart_goagent))
        else:
            menu_options = ((u"Config", None, self.on_show),
                        (u"Set Global GoAgent Proxy", None, self.on_enable_proxy),
                        (u"Set Global PAC Proxy", None, self.on_enable_pac),
                        (u"Disable Global Proxy", None, self.on_disable_proxy),
                        (u"Reset GoAgent", None, self.on_restart_goagent))
        return menu_options

    def on_show(self, widget=None, data=None):
        self.show_control_web()


    def on_restart_goagent(self, widget=None, data=None):
        module_init.stop_all()
        module_init.start_all_auto()

    def on_check_update(self, widget=None, data=None):
        update.check_update()

    def set_register(self, reg_path, name, reg_type, value):
        #_, reg_type = winreg.QueryValueEx(INTERNET_SETTINGS, name)
        winreg.SetValueEx(reg_path, name, 0, reg_type, value)
        logging.info("set register path:%r name:%s type:%d value:%s", reg_path, name, reg_type, value)

    def on_enable_proxy(self, widget=None, data=None):
        self.set_register(self.INTERNET_SETTINGS, 'AutoConfigURL', 1, "") # disable auto proxy
        self.set_register(self.INTERNET_SETTINGS, 'ProxyEnable', 4, 1)
        self.set_register(self.INTERNET_SETTINGS, 'ProxyOverride', 1, '*.local;<local>')  # Bypass the proxy for localhost
        self.set_register(self.INTERNET_SETTINGS, 'ProxyServer', 1, '127.0.0.1:8087')

    def on_enable_pac(self, widget=None, data=None):
        self.set_register(self.INTERNET_SETTINGS, 'ProxyEnable', 4, 0) # disable goagent proxy
        self.set_register(self.INTERNET_SETTINGS, 'AutoConfigURL', 1, "http://127.0.0.1:8086/proxy.pac")

    def on_disable_proxy(self, widget=None, data=None):
        self.set_register(self.INTERNET_SETTINGS, 'ProxyEnable', 4, 0) # disable goagent proxy
        self.set_register(self.INTERNET_SETTINGS, 'AutoConfigURL', 1, "") # disable auto proxy

    def show_control_web(self, widget=None, data=None):
        webbrowser.open("http://127.0.0.1:8085/")

    def on_quit(self, widget, data=None):
        pass

    def serve_forever(self):
        self.systray._message_loop_func()

    def dialog_yes_no(self, msg="msg", title="Title", data=None, callback=None):
        res = ctypes.windll.user32.MessageBoxW(None, msg, title, 1)
        # Yes:1 No:2
        if callback:
            callback(data, res)
        return res

sys_tray = Win_tray()

def main():
    sys_tray.serve_forever()

if __name__ == '__main__':
    main()