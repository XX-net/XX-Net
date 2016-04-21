#!/usr/bin/env python
# coding:utf-8
# Contributor:
#      Phus Lu        <phus.lu@gmail.com>

import webbrowser
import os
import base64

import logging

import pygtk

pygtk.require('2.0')
import gtk
gtk.gdk.threads_init()

import pynotify
pynotify.init('XX-Net Notify')

import module_init

class Gtk_tray():
    notify_list = []
    def __init__(self):
        logo_filename = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'python.png')

        self.trayicon = gtk.StatusIcon()
        self.trayicon.set_from_file(logo_filename)

        self.trayicon.connect('popup-menu', lambda i, b, t: self.make_menu().popup(None, None, gtk.status_icon_position_menu, b, t, self.trayicon))
        self.trayicon.connect('activate', self.show_control_web)
        self.trayicon.set_tooltip('XX-Net')
        self.trayicon.set_visible(True)

    def make_menu(self):
        menu = gtk.Menu()
        itemlist = [(u'Config', self.on_show),
                    ('restart goagent', self.on_restart_goagent),
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
        n = pynotify.Notification('Test', msg)
        for k in buttons:
            data = buttons[k]["data"]
            label = buttons[k]["label"]
            callback = buttons[k]["callback"]
            n.add_action(data, label, callback)
        n.set_timeout(timeout)
        n.show()
        self.notify_list.append(n)

    def show_control_web(self, widget=None, data=None):
        webbrowser.open_new("http://127.0.0.1:8085/")

    def on_restart_goagent(self, widget=None, data=None):
        module_init.stop()
        module_init.start()

    def on_quit(self, widget, data=None):
        gtk.main_quit()

    def serve_forever(self):
        gtk.main()

sys_tray = Gtk_tray()

def main():
    sys_tray.serve_forever()

if __name__ == '__main__':
    main()

