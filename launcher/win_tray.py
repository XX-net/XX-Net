#!/usr/bin/env python
# coding:utf-8


if __name__ == "__main__":
    import os, sys
    current_path = os.path.dirname(os.path.abspath(__file__))
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, 'python27', '1.0'))
    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)
    win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
    sys.path.append(win32_lib)

import webbrowser
from systray import SysTrayIcon
import systray.win32_adapter as win32_adapter
import os
import ctypes
import _winreg as winreg
import win32_proxy_manager

import module_init
import update
import launcher_log


class Win_tray():
    def __init__(self):
        icon_path = os.path.join(os.path.dirname(__file__), "web_ui", "favicon.ico")
        self.systray = SysTrayIcon(icon_path, "XX-Net", self.make_menu(), self.on_quit, left_click=self.on_show, right_click=self.on_right_click)

        reg_path = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
        self.INTERNET_SETTINGS = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            reg_path,
            0, winreg.KEY_ALL_ACCESS)

    def get_proxy_state(self):
        REG_PATH = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
        INTERNET_SETTINGS = winreg.OpenKey(winreg.HKEY_CURRENT_USER,REG_PATH,0, winreg.KEY_ALL_ACCESS)
        try:
            AutoConfigURL, reg_type = winreg.QueryValueEx(INTERNET_SETTINGS, 'AutoConfigURL')
            if AutoConfigURL:
                return "auto"
        except Exception as e:
            pass

        try:
            ProxyEnable, reg_type = winreg.QueryValueEx(INTERNET_SETTINGS, 'ProxyEnable')
            if ProxyEnable:
                return "enable"
        except Exception as e:
            pass
        return "disable"

    def on_right_click(self):
        self.systray.update(menu=self.make_menu())
        self.systray._show_menu()

    def make_menu(self):
        import locale
        lang_code, code_page = locale.getdefaultlocale()

        proxy_stat = self.get_proxy_state()
        enable_checked = win32_adapter.fState.MFS_CHECKED if proxy_stat=="enable" else 0
        auto_checked = win32_adapter.fState.MFS_CHECKED if proxy_stat=="auto" else 0
        disable_checked = win32_adapter.fState.MFS_CHECKED if proxy_stat=="disable" else 0

        if lang_code == "zh_CN":
            menu_options = ((u"设置", None, self.on_show, 0),
                        (u"全局通过GAEProxy代理", None, self.on_enable_proxy, enable_checked),
                        (u"全局PAC智能代理", None, self.on_enable_pac, auto_checked),
                        (u"取消全局代理", None, self.on_disable_proxy, disable_checked),
                        (u"重启 GAEProxy", None, self.on_restart_gae_proxy, 0))
        else:
            menu_options = ((u"Config", None, self.on_show, 0),
                        (u"Set Global GAEProxy Proxy", None, self.on_enable_proxy, enable_checked),
                        (u"Set Global PAC Proxy", None, self.on_enable_pac, auto_checked),
                        (u"Disable Global Proxy", None, self.on_disable_proxy, disable_checked),
                        (u"Reset GAEProxy", None, self.on_restart_gae_proxy, 0))
        return menu_options

    def on_show(self, widget=None, data=None):
        self.show_control_web()

    def on_restart_gae_proxy(self, widget=None, data=None):
        module_init.stop_all()
        module_init.start_all_auto()

    def on_check_update(self, widget=None, data=None):
        update.check_update()

    def on_enable_proxy(self, widget=None, data=None):
        win32_proxy_manager.set_proxy_server("127.0.0.1", 8087)

    def on_enable_pac(self, widget=None, data=None):
        win32_proxy_manager.set_proxy_auto("http://127.0.0.1:8086/proxy.pac")

    def on_disable_proxy(self, widget=None, data=None):
        win32_proxy_manager.disable_proxy()

    def show_control_web(self, widget=None, data=None):
        webbrowser.open("http://127.0.0.1:8085/")
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    def on_quit(self, widget, data=None):
        win32_proxy_manager.disable_proxy()

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
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    sys_tray.serve_forever()

if __name__ == '__main__':
    main()