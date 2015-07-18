#!/usr/bin/env python
# coding:utf-8
# Contributor:
#      Phus Lu        <phus.lu@gmail.com>

import webbrowser
import os
import base64

import launcher_log

import pygtk

if __name__ == "__main__":
    import os, sys
    current_path = os.path.dirname(os.path.abspath(__file__))
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, 'python27', '1.0'))
    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)

pygtk.require('2.0')
import gtk
gtk.gdk.threads_init()

try:
    import pynotify
    pynotify.init('XX-Net Notify')
except:
    launcher_log.warn("import pynotify fail, please install python-notify if possiable.")
    pynotify = None

import module_init

class Gtk_tray():
    notify_list = []
    def __init__(self):
        logo_filename = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'web_ui', 'favicon.ico')

        self.trayicon = gtk.StatusIcon()
        self.trayicon.set_from_file(logo_filename)

        self.trayicon.connect('popup-menu', lambda i, b, t: self.make_menu().popup(None, None, gtk.status_icon_position_menu, b, t, self.trayicon))
        self.trayicon.connect('activate', self.show_control_web)
        self.trayicon.set_tooltip('XX-Net')
        self.trayicon.set_visible(True)

    def make_menu(self):
        menu = gtk.Menu()
        itemlist = [(u'Config', self.on_show),
                    ('restart gae_proxy', self.on_restart_gae_proxy),
                    (u'Quit', self.on_quit)]
        for text, callback in itemlist:
            item = gtk.MenuItem(text)
            item.connect('activate', callback)
            item.show()
            menu.append(item)
        menu.show()
        return menu

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
        webbrowser.open_new("http://127.0.0.1:8085/")

    def on_restart_gae_proxy(self, widget=None, data=None):
        module_init.stop("gae_proxy")
        module_init.start("gae_proxy")

    def on_quit(self, widget, data=None):
        gtk.main_quit()

    def serve_forever(self):
        gtk.gdk.threads_enter()
        gtk.main()
        gtk.gdk.threads_leave()

sys_tray = Gtk_tray()

def main():
    sys_tray.serve_forever()

if __name__ == '__main__':
    main()

