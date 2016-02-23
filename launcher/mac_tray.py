#!/usr/bin/env python
# coding:utf-8

import os
import sys
import config

current_path = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, 'python27', '1.0'))
    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)
    osx_lib = os.path.join(python_path, 'lib', 'darwin')
    sys.path.append(osx_lib)
    extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjC"
    sys.path.append(extra_lib)

import config
import module_init
import subprocess
import webbrowser

from AppKit import *
from instances import xlog
from PyObjCTools import AppHelper

class MacTrayObject(NSObject):
    def __init__(self):
        pass

    def applicationDidFinishLaunching_(self, notification):
        self.setupUI()
        self.registerObserver()
        self.loadConfig()

    def loadConfig(self):
        proxySetting = config.get(["modules", "launcher", "proxy"], "pac")
        if proxySetting == "pac":
            self.on_enable_pac()
        elif proxySetting == "gae":
            self.on_enable_gae_proxy()
        elif proxySetting == "disable":
            # Don't disable proxy setting, just do nothing.
            pass
        else:
            xlog.warn("proxy_setting:%r", proxySetting)

    def getProxyState(self):
        # Check if auto proxy is enabled
        checkAutoProxyUrlEthernetCommand    =   "networksetup -getautoproxyurl Ethernet"
        checkAutoProxyUrlThunderboltCommand = "networksetup -getautoproxyurl \\\"Thunderbolt Ethernet\\\""
        checkAutoProxyUrlWiFiCommand        = "networksetup -getautoproxyurl Wi-Fi"

        executeCommand = "%s;%s;%s;" % (checkAutoProxyUrlEthernetCommand, checkAutoProxyUrlThunderboltCommand, checkAutoProxyUrlWiFiCommand)
        executeResult  = subprocess.check_output(executeCommand, shell=True)

        if ( executeResult.find('http://127.0.0.1:8086/proxy.pac\nEnabled: Yes') != -1 ):
            return "pac"

        # Check if global proxy is enabled
        checkGlobalProxyUrlEthernetCommand =   "networksetup -getwebproxy Ethernet"
        checkGlobalProxyUrlThunderboltCommand = "networksetup -getwebproxy \\\"Thunderbolt Ethernet\\\""
        checkGlobalProxyUrlWiFiCommand = "networksetup -getwebproxy Wi-Fi"

        executeCommand = "%s;%s;%s;" % (checkGlobalProxyUrlEthernetCommand, checkGlobalProxyUrlThunderboltCommand, checkGlobalProxyUrlWiFiCommand)
        executeResult  = subprocess.check_output(executeCommand, shell=True)
        if ( executeResult.find('Enabled: Yes\nServer: 127.0.0.1\nPort: 8087') != -1 ):
            return "gae"

        return "disable"

    def setupUI(self):
        self.statusbar = NSStatusBar.systemStatusBar()
        self.statusitem = self.statusbar.statusItemWithLength_(NSSquareStatusItemLength) #NSSquareStatusItemLength #NSVariableStatusItemLength

        # Set initial image icon
        icon_path = os.path.join(current_path, "web_ui", "favicon-mac.ico")
        image = NSImage.alloc().initByReferencingFile_(icon_path)
        image.setScalesWhenResized_(True)
        image.setSize_((20, 20))
        self.statusitem.setImage_(image)

        # Let it highlight upon clicking
        self.statusitem.setHighlightMode_(1)
        self.statusitem.setToolTip_("XX-Net")

        # Get current selected mode
        proxyState = self.getProxyState()

        # Build a very simple menu
        self.menu = NSMenu.alloc().initWithTitle_('XX-Net')

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Config', 'config:', '')
        self.menu.addItem_(menuitem)

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Enable Auto GAEProxy', 'enableAutoProxy:', '')
        if proxyState == 'pac':
            menuitem.setState_(NSOnState)
        self.menu.addItem_(menuitem)

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Enable Global GAEProxy', 'enableGlobalProxy:', '')
        if proxyState == 'gae':
            menuitem.setState_(NSOnState)
        self.menu.addItem_(menuitem)

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Disable GAEProxy', 'disableProxy:', '')
        if proxyState == 'disable':
            menuitem.setState_(NSOnState)
        self.menu.addItem_(menuitem)

        # Reset Menu Item
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Reload GAEProxy', 'resetGoagent:', '')
        self.menu.addItem_(menuitem)
        # Default event
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'windowWillClose:', '')
        self.menu.addItem_(menuitem)
        # Bind it to the status item
        self.statusitem.setMenu_(self.menu)

        # Hide dock icon
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyProhibited)

    def updateStatusBarMenu(self):
        autoGaeProxyMenuItem    = self.menu.itemWithTitle_('Enable Auto GAEProxy')
        globalGaeProxyMenuItem  = self.menu.itemWithTitle_('Enable Global GAEProxy')
        disableGaeProxyMenuItem = self.menu.itemWithTitle_('Disable GAEProxy')

        # Remove Tick before All Menu Items
        autoGaeProxyMenuItem.setState_(NSOffState)
        globalGaeProxyMenuItem.setState_(NSOffState)
        disableGaeProxyMenuItem.setState_(NSOffState)

        # Get current selected mode
        proxyState = self.getProxyState()

        # Update Tick before Menu Item
        if proxyState == 'pac':
            autoGaeProxyMenuItem.setState_(NSOnState)
        elif proxyState == 'gae':
            globalGaeProxyMenuItem.setState_(NSOnState)
        elif proxyState == 'disable':
            disableGaeProxyMenuItem.setState_(NSOnState)

    def updateConfig(self, newStatus):
        config.set(["modules", "launcher", "proxy"], newStatus)
        config.save()

    def registerObserver(self):
        nc = NSWorkspace.sharedWorkspace().notificationCenter()
        nc.addObserver_selector_name_object_(self, 'windowWillClose:', NSWorkspaceWillPowerOffNotification, None)

    def windowWillClose_(self, notification):
        self.disableProxy_(None)
        module_init.stop_all()
        os._exit(0)
        NSApp.terminate_(self)

    #Note: the function name for action can include '_'
    # limited by Mac cocoa
    def config_(self, notification):
        host_port = config.get(["modules", "launcher", "control_port"], 8085)
        webbrowser.open_new("http://127.0.0.1:%s/" % host_port)

    def resetGoagent_(self, _):
        module_init.stop("gae_proxy")
        module_init.start("gae_proxy")

    def enableAutoProxy_(self, _):
        disableProxyCommand                 = self.getDisableProxyCommand()
        enableAutoProxyCommand              = self.getEnableAutoProxyCommand()
        rootCommand                         = """osascript -e 'do shell script "%s;%s" with administrator privileges' """ % (disableProxyCommand, enableAutoProxyCommand)
        executeCommand                      = rootCommand.encode('utf-8')

        xlog.info("try enable proxy:%s", executeCommand)
        os.system(executeCommand)
        self.updateStatusBarMenu()
        self.updateConfig('pac')

    def getEnableAutoProxyCommand(self):
        enableAutoProxyEthernetCommand      = "networksetup -setautoproxyurl Ethernet \\\"http://127.0.0.1:8086/proxy.pac\\\""
        enableAutoProxyThunderboltCommand   = "networksetup -setautoproxyurl \\\"Thunderbolt Ethernet\\\" \\\"http://127.0.0.1:8086/proxy.pac\\\""
        enableAutoProxyWiFiCommand          = "networksetup -setautoproxyurl Wi-Fi \\\"http://127.0.0.1:8086/proxy.pac\\\""
        executeCommand                      = "%s;%s;%s" % (enableAutoProxyEthernetCommand, enableAutoProxyThunderboltCommand, enableAutoProxyWiFiCommand)

        return executeCommand

    def enableGlobalProxy_(self, _):
        disableProxyCommand                 = self.getDisableProxyCommand()
        enableGlobalProxyCommand            = self.getEnableGlobalProxyCommand()
        rootCommand                         = """osascript -e 'do shell script "%s;%s" with administrator privileges' """ % (disableProxyCommand, enableGlobalProxyCommand)
        executeCommand                      = rootCommand.encode('utf-8')

        xlog.info("try enable proxy:%s", executeCommand)
        os.system(executeCommand)
        self.updateStatusBarMenu()
        self.updateConfig('gae')

    def getEnableGlobalProxyCommand(self):
        enableHttpProxyEthernetCommand      = "networksetup -setwebproxy Ethernet 127.0.0.1 8087"
        enableHttpProxyThunderboltCommand   = "networksetup -setwebproxy \\\"Thunderbolt Ethernet\\\" 127.0.0.1 8087"
        enableHttpProxyWiFiCommand          = "networksetup -setwebproxy Wi-Fi 127.0.0.1 8087"
        enableHttpsProxyEthernetCommand     = "networksetup -setsecurewebproxy Ethernet 127.0.0.1 8087"
        enableHttpsProxyThunderboltCommand  = "networksetup -setsecurewebproxy \\\"Thunderbolt Ethernet\\\" 127.0.0.1 8087"
        enableHttpsProxyWiFiCommand         = "networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 8087"

        executeCommand = "%s;%s;%s;%s;%s;%s" % (enableHttpProxyEthernetCommand, enableHttpProxyThunderboltCommand, enableHttpProxyWiFiCommand,
                            enableHttpsProxyEthernetCommand, enableHttpsProxyThunderboltCommand, enableHttpsProxyWiFiCommand)
        return executeCommand

    def disableProxy_(self, _):
        disableProxyCommand                 = self.getDisableProxyCommand()
        rootCommand                         = """osascript -e 'do shell script "%s" with administrator privileges' """ % disableProxyCommand
        executeCommand                      = rootCommand.encode('utf-8')

        xlog.info("try disable proxy:%s", executeCommand)
        os.system(executeCommand)
        self.updateStatusBarMenu()
        self.updateConfig('disable')

    def getDisableProxyCommand(self):
        disableHttpProxyEthernetCommand     = "networksetup -setwebproxystate Ethernet off"
        disableHttpProxyThunderboltCommand  = "networksetup -setwebproxystate \\\"Thunderbolt Ethernet\\\" off"
        disableHttpProxyWiFiCommand         = "networksetup -setwebproxystate Wi-Fi off"
        disableHttpsProxyEthernetCommand    = "networksetup -setsecurewebproxystate Ethernet off"
        disableHttpsProxyThunderboltCommand = "networksetup -setsecurewebproxystate \\\"Thunderbolt Ethernet\\\" off"
        disableHttpsProxyWiFiCommand        = "networksetup -setsecurewebproxystate Wi-Fi off"
        disableAutoProxyEthernetCommand     = "networksetup -setautoproxystate Ethernet off"
        disableAutoProxyThunderboltCommand  = "networksetup -setautoproxystate \\\"Thunderbolt Ethernet\\\" off"
        disableAutoProxyWiFiCommand         = "networksetup -setautoproxystate Wi-Fi off"

        executeCommand = "%s;%s;%s;%s;%s;%s;%s;%s;%s" % (disableHttpProxyEthernetCommand, disableHttpProxyThunderboltCommand, disableHttpProxyWiFiCommand,
                            disableHttpsProxyEthernetCommand, disableHttpsProxyThunderboltCommand, disableHttpsProxyWiFiCommand,
                            disableAutoProxyEthernetCommand, disableAutoProxyThunderboltCommand, disableAutoProxyWiFiCommand)
        return executeCommand

class Mac_tray():
    def dialog_yes_no(self, msg="msg", title="Title", data=None, callback=None):
        msg = unicode(msg)
        title = unicode(title)
        alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(
            title, "OK", "Cancel", None, msg)
        alert.setAlertStyle_(0)  # informational style
        res = alert.runModal()
        xlog.debug("dialog_yes_no return %d", res)

        # The "ok" button is ``1`` and "cancel" is ``0``.
        if res == 0:
            res = 2
            return res

        # Yes:1 No:2
        if callback:
            callback(data, res)
        return res

    def notify_general(self, msg="msg", title="Title", buttons={}, timeout=3600):
        xlog.error("Mac notify_general not implemented.")


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
