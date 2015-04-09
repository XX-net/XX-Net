(/usr/bin/env python2.6 -x "$0" 2>&1 >/dev/null &);exit
# coding:utf-8
# Contributor:
#      Phus Lu        <phus.lu@gmail.com>

__version__ = '1.6'

GOAGENT_TITLE = "GoAgent OS X"
GOAGENT_ICON_DATA = """\
iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAADtklEQVR42r3UW0xbdRwH8PqiLz7Y
xTTEJwMSdVMX2nMprZBSeqFd6cQlBgPGxGVJSwschLpNjDMap9vUxIxgKbcNKgHWdcU55nSJOpEx
Wkav0DIvC0pgPiy6+dD2nPP/ethMk5kljD34S/7J/+mT3/93+ctkG8cD/zn3F1sP4MHyD74p0x3+
sdF06EKb6eAUp3v360bbx4ntm4bXMfbtsX79O+f+ULp92bKmvpyqyZdTOX05yt2bN3cn924KpQ58
WVzdeXpa9oTloYq9gfeZlgFCu31gXT7QDi9hnF3TxkOXH7tnkH1vppT2jKQq909M0S1DyzR3XMqu
l9CuPsI4uiXYu/CMZ7JkQ+i5Iz8pdB9FnqIcfdry9s+PsB1+r6p10Me6Bryq14dE2tVDWIcXpbsH
FrjDbi1y6qexqHscuMvzjUPXa5n9E9+znvHfWc6/yrT51xju2BrTPLjGtg6uSvUjt8AmL7bUj6Sy
YcswouyKMKuN48+6PXdgmqGbCqbzTI7yjIp0+yih2/y3DzdE6JZBCeqXathfABX1/tTqd/YgonSe
zDAiomoB0CgKYMXRpFnpCeak7MB6RkFzIxI4TChuWKBa+3mqpY+nmnt52vUZTzm6eJl18gskqPMI
awRc1IDM0jxuVlUXBtfYlXEpOwLZdZDuGCdKblh8sjnEK16duCRvOBWSNwZC8pdPTMjrAyGZ6fzB
5WmbCwnmOiLlIi6WQ5ym88gbHQXQ0L3kLGu/Dao6RsVi56lrr33yqYPcUJ4ly88v4iqbxlUmTX5V
ZsiS8i+kJShSIWJWi3UQM3QOWbO78GT90bRe+UYgz3gCZDs3JmxrDZ4lOfYcUi/kEbcKiFkERM0C
5o0Cma8WMacjiFSSdVC8pJbuTB5/6wwF0Naz8ijdeTpPecbINu4kb32r5wRWq9NI2UUkbJBQIFYD
RE3AZQMQroIEYh2UmkIQZrOA7uE7x+bYjTp63/i3z3LBhP7N491kxZhBwk6Q3EGQsBAhaooLcVNC
iBkSQliXFCKVSSFckcSs5gKws/aug62RBluxL148NelUk59tGSlDCbQSLFqJELMExbmakBg1niRR
sy8/p1UjqykB6KINNwbYVSou7Fq6lWHKRhCzEhIzSfUz/ELixpAwXxXDNX3JPe8y0FRErrz4AxI7
CeL/1jBuIbhi/vC3r7ZuwZLpDGAt2tQXBrjtyLzEY6GWR7Qmj3mT1HEjj6RJakCD/b4+Walzj4Bv
kFr7SjPQ6Ea2zgjskMv+z/gHq6RKE1cMAqYAAAAASUVORK5CYII="""

import sys
import subprocess
import pty
import os
import base64
import ctypes
import ctypes.util

from PyObjCTools import AppHelper
from AppKit import *

class GoAgentOSX(NSObject):

    def applicationDidFinishLaunching_(self, notification):
        self.setupUI()
        self.startGoAgent()
        self.registerObserver()

    def windowWillClose_(self, notification):
        self.stopGoAgent()
        NSApp.terminate_(self)

    def setupUI(self):
        self.statusbar = NSStatusBar.systemStatusBar()
        # Create the statusbar item
        self.statusitem = self.statusbar.statusItemWithLength_(NSVariableStatusItemLength)
        # Set initial image
        raw_data = base64.b64decode(''.join(GOAGENT_ICON_DATA.strip().splitlines()))
        self.image_data = NSData.dataWithBytes_length_(raw_data, len(raw_data))
        self.image = NSImage.alloc().initWithData_(self.image_data)
        self.statusitem.setImage_(self.image)
        # Let it highlight upon clicking
        self.statusitem.setHighlightMode_(1)
        # Set a tooltip
        self.statusitem.setToolTip_(GOAGENT_TITLE)

        # Build a very simple menu
        self.menu = NSMenu.alloc().init()
        # Show Menu Item
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Show', 'show:', '')
        self.menu.addItem_(menuitem)
        # Hide Menu Item
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Hide', 'hide2:', '')
        self.menu.addItem_(menuitem)
        # Rest Menu Item
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Reload', 'reset:', '')
        self.menu.addItem_(menuitem)
        # Default event
        menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'exit:', '')
        self.menu.addItem_(menuitem)
        # Bind it to the status item
        self.statusitem.setMenu_(self.menu)

        # Console window
        frame = NSMakeRect(0, 0, 550, 350)
        self.console_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(frame, NSClosableWindowMask | NSTitledWindowMask, NSBackingStoreBuffered, False)
        self.console_window.setTitle_(GOAGENT_TITLE)
        self.console_window.setDelegate_(self)

        # Console view inside a scrollview
        self.scroll_view = NSScrollView.alloc().initWithFrame_(frame)
        self.scroll_view.setBorderType_(NSNoBorder)
        self.scroll_view.setHasVerticalScroller_(True)
        self.scroll_view.setHasHorizontalScroller_(False)
        self.scroll_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)

        self.console_view = NSTextView.alloc().initWithFrame_(frame)
        self.console_view.setVerticallyResizable_(True)
        self.console_view.setHorizontallyResizable_(True)
        self.console_view.setAutoresizingMask_(NSViewWidthSizable)

        self.scroll_view.setDocumentView_(self.console_view)

        contentView = self.console_window.contentView()
        contentView.addSubview_(self.scroll_view)

        # Hide dock icon
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyProhibited)

    def registerObserver(self):
        nc = NSWorkspace.sharedWorkspace().notificationCenter()
        nc.addObserver_selector_name_object_(self, 'exit:', NSWorkspaceWillPowerOffNotification, None)

    def startGoAgent(self):
        for pycmd in ('python2.7', 'python2', 'python'):
            if os.system('which %s' % pycmd) == 0:
                cmd = '/usr/bin/env %s proxy.py' % pycmd
                break
        self.master, self.slave = pty.openpty()
        self.pipe = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=self.slave, stderr=self.slave, close_fds=True)
        self.pipe_fd = os.fdopen(self.master)

        self.performSelectorInBackground_withObject_('readProxyOutput', None)

    def stopGoAgent(self):
        self.pipe.terminate()

    def refreshDisplay_(self, line):
        #print line
        self.console_view.textStorage().mutableString().appendString_(line)
        need_scroll = NSMaxY(self.console_view.visibleRect()) >= NSMaxY(self.console_view.bounds())
        if need_scroll:
            range = NSMakeRange(len(self.console_view.textStorage().mutableString()), 0)
            self.console_view.scrollRangeToVisible_(range)

    def readProxyOutput(self):
        while(True):
            line = self.pipe_fd.readline()
            self.performSelectorOnMainThread_withObject_waitUntilDone_('refreshDisplay:', line, None)

    def show_(self, notification):
        self.console_window.center()
        self.console_window.orderFrontRegardless()
        self.console_window.setIsVisible_(True)

    def hide2_(self, notification):
        self.console_window.setIsVisible_(False)
        #self.console_window.orderOut(None)

    def reset_(self, notification):
        self.console_view.setString_('')
        self.stopGoAgent()
        self.startGoAgent()

    def exit_(self, notification):
        self.stopGoAgent()
        NSApp.terminate_(self)


def main():
    global __file__
    __file__ = os.path.abspath(__file__)
    if os.path.islink(__file__):
        __file__ = getattr(os, 'readlink', lambda x: x)(__file__)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    app = NSApplication.sharedApplication()
    delegate = GoAgentOSX.alloc().init()
    app.setDelegate_(delegate)

    AppHelper.runEventLoop()

if __name__ == '__main__':
    main()
