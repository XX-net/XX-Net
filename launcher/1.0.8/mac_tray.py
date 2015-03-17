#!/usr/bin/env python
# coding:utf-8

if __name__ == "__main__":
    import os
    import sys

    current_path = os.path.dirname(os.path.abspath(__file__))
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))
    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)
    osx_lib = os.path.join(python_path, 'lib', 'osx')
    sys.path.append(osx_lib)

import rumps
import webbrowser
import module_init

class Mac_tray(rumps.App):
    def __init__(self):
        super(Mac_tray, self).__init__("XX-Net", title="XX-Net", icon="Python.ico", quit_button=None)
        self.menu = ["Config", "Reset", "Quit"]

    @rumps.clicked("Config")
    def on_config(self, _):
        webbrowser.open_new("http://127.0.0.1:8085/")

    @rumps.clicked("Reset")
    def on_reset(self, _):
        module_init.stop_all()
        module_init.start_all_auto()

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

