#!/usr/bin/env python
# coding:utf-8

import os
import sys

current_path = os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))
    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)
    osx_lib = os.path.join(python_path, 'lib', 'osx')
    sys.path.append(osx_lib)

import rumps
import webbrowser
import module_init
import logging
import os

class Mac_tray(rumps.App):
    def __init__(self):
        icon_path = os.path.join(current_path, "Python.ico")
        super(Mac_tray, self).__init__("XX-Net", title="XX-Net", icon=icon_path, quit_button=None)
        self.menu = ["Config", "Enable Proxy", "Disable Proxy", "Reset", "Quit"]

    @rumps.clicked("Config")
    def on_config(self, _):
        webbrowser.open_new("http://127.0.0.1:8085/")

    @rumps.clicked("Reset")
    def on_reset(self, _):
        module_init.stop_all()
        module_init.start_all_auto()

    @rumps.clicked("Enable Proxy")
    def on_enable_proxy(self, _):
        cmd1 = "networksetup -setwebproxy Ethernet 127.0.0.1 8087"
        cmd2 = "networksetup -setwebproxy Wi-Fi 127.0.0.1 8087"
        cmd3 = "networksetup -setwebproxystate Ethernet on"
        cmd4 = "networksetup -setwebproxystate Wi-Fi on"
        cmd5 = "networksetup -setsecurewebproxy Ethernet 127.0.0.1 8087"
        cmd6 = "networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 8087"
        cmd7 = "networksetup -setsecurewebproxystate Ethernet on"
        cmd8 = "networksetup -setsecurewebproxystate Wi-Fi on"
        exec_command = "%s;%s;%s;%s;%s;%s;%s;%s" % (cmd1, cmd2, cmd3, cmd4, cmd5, cmd6, cmd7, cmd8)
        admin_command = """osascript -e 'do shell script "%s" with administrator privileges' """ % exec_command
        cmd = admin_command.encode('utf-8')
        logging.info("try enable proxy:%s", cmd)
        os.system(cmd)

    @rumps.clicked("Disable Proxy")
    def on_disable_proxy(self, _):
        cmd1 = "networksetup -setwebproxystate Ethernet off"
        cmd2 = "networksetup -setwebproxystate Wi-Fi off"
        cmd3 = "networksetup -setsecurewebproxystate Ethernet off"
        cmd4 = "networksetup -setsecurewebproxystate Wi-Fi off"
        exec_command = "%s;%s;%s;%s" % (cmd1, cmd2, cmd3, cmd4)
        admin_command = """osascript -e 'do shell script "%s" with administrator privileges' """ % exec_command
        cmd = admin_command.encode('utf-8')
        logging.info("try disable proxy:%s", cmd)
        os.system(cmd)

    @rumps.clicked("Quit")
    def on_quit(self, _):
        module_init.stop_all()
        rumps.quit_application()

    def notify_general(self, msg="msg", title="Title", buttons={}, timeout=3600):
        window = rumps.Window(title, msg)
        window.title = title
        window.message = msg
        window.default_text = 'eh'
        for button in buttons:
           window.add_buttons(button)
        res = window.run()
        return res

    def dialog_yes_no(self, msg="msg", title="Title", data=None, callback=None):
        if rumps.alert(title, msg):
           callback(data)


    def serve_forever(self):
        self.run()

sys_tray = Mac_tray()

def main():
    sys_tray.serve_forever()

if __name__ == '__main__':
    main()

