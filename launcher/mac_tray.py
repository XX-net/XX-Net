#!/usr/bin/env python
# coding:utf-8

import os
import sys

current_path = os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, 'python27', '1.0'))
    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)
    osx_lib = os.path.join(python_path, 'lib', 'darwin')
    sys.path.append(osx_lib)
    extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjC"
    sys.path.append(extra_lib)

import webbrowser
import module_init
import launcher_log

from PyObjCTools import AppHelper
from AppKit import *

class MacTrayObject(NSObject):
    def __init__(self):
        pass

    def applicationDidFinishLaunching_(self, notification):
        self.setupUI()
        self.registerObserver()

    def setupUI(self):
        self.statusbar = NSStatusBar.systemStatusBar()
        self.statusitem = self.statusbar.statusItemWithLength_(NSSquareStatusItemLength) #NSSquareStatusItemLength #NSVariableStatusItemLength

        # Set initial image icon
        icon_path = os.path.join(current_path, "web_ui", "favicon_MAC.ico")
        image = NSImage.alloc().initByReferencingFile_(icon_path)
        image.setScalesWhenResized_(True)
        image.setSize_((20, 20))
        self.statusitem.setImage_(image)

        # Let it highlight upon clicking
        self.statusitem.setHighlightMode_(1)

        self.statusitem.setToolTip_("XX-Net")

        # Build a very simple menu
        self.menu = NSMenu.alloc().init()

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Config', 'config:', '')
        self.menu.addItem_(menuitem)

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Enable Global Goagent Proxy', 'enableProxy:', '')
        self.menu.addItem_(menuitem)

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Disable Global Goagent Proxy', 'disableProxy:', '')
        self.menu.addItem_(menuitem)

        # Rest Menu Item
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Reload GAEProxy', 'resetGoagent:', '')
        self.menu.addItem_(menuitem)
        # Default event
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'windowWillClose:', '')
        self.menu.addItem_(menuitem)
        # Bind it to the status item
        self.statusitem.setMenu_(self.menu)

        # Hide dock icon
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyProhibited)

    def registerObserver(self):
        nc = NSWorkspace.sharedWorkspace().notificationCenter()
        nc.addObserver_selector_name_object_(self, 'windowWillClose:', NSWorkspaceWillPowerOffNotification, None)

    def windowWillClose_(self, notification):
        module_init.stop_all()
        NSApp.terminate_(self)

    def config_(self, notification):
        webbrowser.open_new("http://127.0.0.1:8085/")

    #Note: the function name for action can include '_'
    # limited by Mac cocoa
    def resetGoagent_(self, _):
        module_init.stop("gae_proxy")
        module_init.start("gae_proxy")

    def enableProxy_(self, _):
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
        launcher_log.info("try enable proxy:%s", cmd)
        os.system(cmd)

    def disableProxy_(self, _):
        cmd1 = "networksetup -setwebproxystate Ethernet off"
        cmd2 = "networksetup -setwebproxystate Wi-Fi off"
        cmd3 = "networksetup -setsecurewebproxystate Ethernet off"
        cmd4 = "networksetup -setsecurewebproxystate Wi-Fi off"
        exec_command = "%s;%s;%s;%s" % (cmd1, cmd2, cmd3, cmd4)
        admin_command = """osascript -e 'do shell script "%s" with administrator privileges' """ % exec_command
        cmd = admin_command.encode('utf-8')
        launcher_log.info("try disable proxy:%s", cmd)
        os.system(cmd)



class Mac_tray():
    def dialog_yes_no(self, msg="msg", title="Title", data=None, callback=None):
        msg = unicode(msg)
        title = unicode(title)
        alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(
            title, "OK", "Cancel", None, msg)
        alert.setAlertStyle_(0)  # informational style
        res = alert.runModal()
        launcher_log.debug("dialog_yes_no return %d", res)

        # The "ok" button is ``1`` and "cancel" is ``0``.
        if res == 0:
            res = 2
            return res

        # Yes:1 No:2
        if callback:
            callback(data, res)
        return res

    def notify_general(self, msg="msg", title="Title", buttons={}, timeout=3600):
        launcher_log.error("Mac notify_general not implemented.")


sys_tray = Mac_tray()

# Note: the following code can't run in class
def serve_forever():
    app = NSApplication.sharedApplication()
    delegate = MacTrayObject.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()

def main():
    serve_forever()

if __name__ == '__main__':
    main()
    #sys_tray.dialog_yes_no("test", "test message")

