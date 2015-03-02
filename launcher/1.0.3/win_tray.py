#!/usr/bin/env python
# coding:utf-8

import webbrowser
from systray import SysTrayIcon
import os
import ctypes

import module_init
import update

class Win_tray():
    def __init__(self):
        icon_path = os.path.join(os.path.dirname(__file__), "python.ico")
        self.systray = SysTrayIcon(icon_path, "XX-Net", self.make_menu(), self.on_quit, left_click=self.on_show)


    def make_menu(self):
        menu_options = (("Show", None, self.on_show),
                        ("Check update", None, self.on_check_update),
                        ("restart goagent", None, self.on_restart_goagent))
        return menu_options

    def on_show(self, widget=None, data=None):
        self.show_control_web()


    def on_restart_goagent(self, widget=None, data=None):
        module_init.stop()
        module_init.start()

    def on_check_update(self, widget=None, data=None):
        update.check_update()

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