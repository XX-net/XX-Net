#!/usr/bin/env python
# coding:utf-8
# Contributor:
#      Phus Lu        <phus.lu@gmail.com>
import os
import sys
import webbrowser

from instances import xlog

from gi.repository import Gtk, Gdk
import config
if __name__ == "__main__":
    current_path = os.path.dirname(os.path.abspath(__file__))
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, 'python27', '1.0'))
    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)

Gdk.threads_init()

try:
    import pynotify
    pynotify.init('XX-Net Notify')
except:
    xlog.warn("import pynotify fail, please install python-notify if possiable.")
    pynotify = None

import module_init

try:
    import platform
    import appindicator
except:
    platform = None
    appindicator = None


class Gtk_tray():
    notify_list = []
    def __init__(self):
        logo_filename = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'web_ui', 'favicon.ico')
        self.menu = self.make_menu()

        if platform and appindicator and platform.dist()[0].lower() == 'ubuntu':
            self.trayicon = self.ubuntu_trayicon(logo_filename)
        else:
            self.trayicon = self.gtk_trayicon(logo_filename)

    def ubuntu_trayicon(self, logo_filename):
        trayicon = appindicator.Indicator('XX-Net', 'indicator-messages', appindicator.CATEGORY_APPLICATION_STATUS)
        trayicon.set_status(appindicator.STATUS_ACTIVE)
        trayicon.set_attention_icon('indicator-messages-new')
        trayicon.set_icon(logo_filename)
        trayicon.set_menu(self.make_menu())

        return trayicon

    def gtk_trayicon(self, logo_filename):
        trayicon = Gtk.StatusIcon()
        trayicon.set_from_file(logo_filename)

        #trayicon.connect('popup-menu', lambda i, b, t: self.make_menu().popup(None, None, Gtk.status_icon_position_menu, b, t, self.trayicon))
        trayicon.connect('popup-menu', self.popup_menu)
        trayicon.connect('activate', self.show_control_web)
        trayicon.set_tooltip_text('XX-Net')
        trayicon.set_visible(True)

        return trayicon

    def make_menu(self):
        menu = Gtk.Menu()
        itemlist = [('Config', self.on_show),
                    ('restart gae_proxy', self.on_restart_gae_proxy),
                    ('Quit', self.on_quit)]
        for text, callback in itemlist:
            item = Gtk.MenuItem(text)
            item.connect('activate', callback)
            item.show()
            menu.append(item)
        menu.show()
        return menu

    def popup_menu(self, icon, button, time):
        menu = self.menu
        menu.show_all()
        menu.popup(None, None, None, None, button, time)

    def on_show(self, widget=None, data=None):
        self.show_control_web()

    def notify_general(self, msg="msg", title="Title", buttons={}, timeout=3600):
        if not pynotify:
            return False

        n = pynotify.Notification('Test', msg)
        for k in buttons:
            data = buttons[k]["data"]
            label = buttons[k]["label"]
            callback = buttons[k]["callback"]
            n.add_action(data, label, callback)
        n.set_timeout(timeout)
        n.show()
        self.notify_list.append(n)
        return True

    def show_control_web(self, widget=None, data=None):
        host_port = config.get(["modules", "launcher", "control_port"], 8085)
        webbrowser.open_new("http://127.0.0.1:%s/" % host_port)

    def on_restart_gae_proxy(self, widget=None, data=None):
        module_init.stop("gae_proxy")
        module_init.start("gae_proxy")

    def on_quit(self, widget, data=None):
        module_init.stop_all()
        os._exit(0)
        Gtk.main_quit()

    def serve_forever(self):
        Gdk.threads_enter()
        Gtk.main()
        Gdk.threads_leave()

sys_tray = Gtk_tray()

def main():
    sys_tray.serve_forever()

if __name__ == '__main__':
    main()

