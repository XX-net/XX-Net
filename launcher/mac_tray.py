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
from SystemConfiguration import *
from instances import xlog
from PyObjCTools import AppHelper

class MacTrayObject(NSObject):
    def __init__(self):
        pass

    def applicationDidFinishLaunching_(self, notification):
        self.setupUI()
        self.registerObserver()

    def getProxyState(self, service):
        if not service:
            return

        # Check if auto proxy is enabled
        checkAutoProxyUrlCommand = 'networksetup -getautoproxyurl "%s"' % service
        executeResult = subprocess.check_output(checkAutoProxyUrlCommand, shell=True)
        if ( executeResult.find('http://127.0.0.1:8086/proxy.pac\nEnabled: Yes') != -1 ):
            return "pac"

        # Check if global proxy is enabled
        checkGlobalProxyUrlCommand = 'networksetup -getwebproxy "%s"' % service
        executeResult = subprocess.check_output(checkGlobalProxyUrlCommand, shell=True)
        if ( executeResult.find('Enabled: Yes\nServer: 127.0.0.1\nPort: 8087') != -1 ):
            return "gae"

        return "disable"

    def getCurrentServiceMenuItemTitle(self):
        if currentService:
            return 'Connection: %s' % currentService
        else:
            return 'Connection: None'

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
        proxyState = self.getProxyState(currentService)

        # Build a very simple menu
        self.menu = NSMenu.alloc().initWithTitle_('XX-Net')

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Config', 'config:', '')
        self.menu.addItem_(menuitem)

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.getCurrentServiceMenuItemTitle(), None, '')
        self.menu.addItem_(menuitem)
        self.currentServiceMenuItem = menuitem

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Enable Auto GAEProxy', 'enableAutoProxy:', '')
        if proxyState == 'pac':
            menuitem.setState_(NSOnState)
        self.menu.addItem_(menuitem)
        self.autoGaeProxyMenuItem = menuitem

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Enable Global GAEProxy', 'enableGlobalProxy:', '')
        if proxyState == 'gae':
            menuitem.setState_(NSOnState)
        self.menu.addItem_(menuitem)
        self.globalGaeProxyMenuItem = menuitem

        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Disable GAEProxy', 'disableProxy:', '')
        if proxyState == 'disable':
            menuitem.setState_(NSOnState)
        self.menu.addItem_(menuitem)
        self.disableGaeProxyMenuItem = menuitem

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
        self.currentServiceMenuItem.setTitle_(self.getCurrentServiceMenuItemTitle())

        # Remove Tick before All Menu Items
        self.autoGaeProxyMenuItem.setState_(NSOffState)
        self.globalGaeProxyMenuItem.setState_(NSOffState)
        self.disableGaeProxyMenuItem.setState_(NSOffState)

        # Get current selected mode
        proxyState = self.getProxyState(currentService)

        # Update Tick before Menu Item
        if proxyState == 'pac':
            self.autoGaeProxyMenuItem.setState_(NSOnState)
        elif proxyState == 'gae':
            self.globalGaeProxyMenuItem.setState_(NSOnState)
        elif proxyState == 'disable':
            self.disableGaeProxyMenuItem.setState_(NSOnState)

        # Trigger autovalidation
        self.menu.update()

    def validateMenuItem_(self, menuItem):
        return currentService or (menuItem != self.autoGaeProxyMenuItem and
                                  menuItem != self.globalGaeProxyMenuItem and
                                  menuItem != self.disableGaeProxyMenuItem)

    def updateConfig(self, newStatus):
        config.set(["modules", "launcher", "proxy"], newStatus)
        config.save()

    def registerObserver(self):
        nc = NSWorkspace.sharedWorkspace().notificationCenter()
        nc.addObserver_selector_name_object_(self, 'windowWillClose:', NSWorkspaceWillPowerOffNotification, None)

    def windowWillClose_(self, notification):
        listNetworkServicesCommand = 'networksetup -listallnetworkservices'
        executeResult = subprocess.check_output(listNetworkServicesCommand, shell=True)
        services = executeResult.split('\n')
        services = filter(lambda service : service and service.find('*') == -1 and self.getProxyState(service) != 'disable', services) # Remove disabled services and empty lines

        if len(services) > 0:
            disableAutoProxyCommand   = ';'.join(map(self.getDisableAutoProxyCommand, services))
            disableGlobalProxyCommand = ';'.join(map(self.getDisableGlobalProxyCommand, services))
            rootCommand               = """osascript -e 'do shell script "%s;%s" with administrator privileges' """ % (disableAutoProxyCommand, disableGlobalProxyCommand)
            executeCommand            = rootCommand.encode('utf-8')

            xlog.info("try disable proxy:%s", executeCommand)
            os.system(executeCommand)

        self.updateConfig('disable')
        module_init.stop_all()
        os._exit(0)
        NSApp.terminate_(self)

    def config_(self, notification):
        host_port = config.get(["modules", "launcher", "control_port"], 8085)
        webbrowser.open_new("http://127.0.0.1:%s/" % host_port)

    def resetGoagent_(self, _):
        module_init.stop("gae_proxy")
        module_init.start("gae_proxy")

    def enableAutoProxy_(self, _):
        disableGlobalProxyCommand = self.getDisableGlobalProxyCommand(currentService)
        enableAutoProxyCommand    = self.getEnableAutoProxyCommand(currentService)
        rootCommand               = """osascript -e 'do shell script "%s;%s" with administrator privileges' """ % (disableGlobalProxyCommand, enableAutoProxyCommand)
        executeCommand            = rootCommand.encode('utf-8')

        xlog.info("try enable auto proxy:%s", executeCommand)
        os.system(executeCommand)
        self.updateStatusBarMenu()
        self.updateConfig('pac')

    def enableGlobalProxy_(self, _):
        disableAutoProxyCommand   = self.getDisableAutoProxyCommand(currentService)
        enableGlobalProxyCommand  = self.getEnableGlobalProxyCommand(currentService)
        rootCommand               = """osascript -e 'do shell script "%s;%s" with administrator privileges' """ % (disableAutoProxyCommand, enableGlobalProxyCommand)
        executeCommand            = rootCommand.encode('utf-8')

        xlog.info("try enable global proxy:%s", executeCommand)
        os.system(executeCommand)
        self.updateStatusBarMenu()
        self.updateConfig('gae')

    def disableProxy_(self, _):
        disableAutoProxyCommand   = self.getDisableAutoProxyCommand(currentService)
        disableGlobalProxyCommand = self.getDisableGlobalProxyCommand(currentService)
        rootCommand               = """osascript -e 'do shell script "%s;%s" with administrator privileges' """ % (disableAutoProxyCommand, disableGlobalProxyCommand)
        executeCommand            = rootCommand.encode('utf-8')

        xlog.info("try disable proxy:%s", executeCommand)
        os.system(executeCommand)
        self.updateStatusBarMenu()
        self.updateConfig('disable')

    # Generate commands for Apple Script
    def getEnableAutoProxyCommand(self, service):
        return "networksetup -setautoproxyurl \\\"%s\\\" \\\"http://127.0.0.1:8086/proxy.pac\\\"" % service

    def getDisableAutoProxyCommand(self, service):
        return "networksetup -setautoproxystate \\\"%s\\\" off" % service

    def getEnableGlobalProxyCommand(self, service):
        enableHttpProxyCommand   = "networksetup -setwebproxy \\\"%s\\\" 127.0.0.1 8087" % service
        enableHttpsProxyCommand  = "networksetup -setsecurewebproxy \\\"%s\\\" 127.0.0.1 8087" % service
        return "%s;%s" % (enableHttpProxyCommand, enableHttpsProxyCommand)

    def getDisableGlobalProxyCommand(self, service):
        disableHttpProxyCommand  = "networksetup -setwebproxystate \\\"%s\\\" off" % service
        disableHttpsProxyCommand = "networksetup -setsecurewebproxystate \\\"%s\\\" off" % service
        return "%s;%s" % (disableHttpProxyCommand, disableHttpsProxyCommand)


sys_tray = MacTrayObject.alloc().init()
currentService = None

def fetchCurrentService(protocol):
    global currentService
    status = SCDynamicStoreCopyValue(None, "State:/Network/Global/" + protocol)
    if not status:
        currentService = None
        return
    serviceID = status['PrimaryService']
    service = SCDynamicStoreCopyValue(None, "Setup:/Network/Service/" + serviceID)
    if not service:
        currentService = None
        return
    currentService = service['UserDefinedName']

@objc.callbackFor(CFNotificationCenterAddObserver)
def networkChanged(center, observer, name, object, userInfo):
    fetchCurrentService('IPv4')
    sys_tray.updateStatusBarMenu()

# Note: the following code can't run in class
def serve_forever():
    app = NSApplication.sharedApplication()
    app.setDelegate_(sys_tray)

    # Listen for network change
    nc = CFNotificationCenterGetDarwinNotifyCenter()
    CFNotificationCenterAddObserver(nc, None, networkChanged, "com.apple.system.config.network_change", None, CFNotificationSuspensionBehaviorDeliverImmediately)

    fetchCurrentService('IPv4')
    AppHelper.runEventLoop()

def main():
    serve_forever()

if __name__ == '__main__':
    main()
