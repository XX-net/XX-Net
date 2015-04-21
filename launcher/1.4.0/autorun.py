#!/usr/bin/env python
"""A simple crossplatform autostart helper"""
from __future__ import with_statement

import os
import sys
import logging


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir))

if sys.platform == 'win32':
    import _winreg
    _registry = _winreg.ConnectRegistry(None, _winreg.HKEY_CURRENT_USER)
    def get_runonce():
        return _winreg.OpenKey(_registry,
                r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
        _winreg.KEY_ALL_ACCESS)

    def add(name, application):
        """add a new autostart entry"""
        key = get_runonce()
        _winreg.SetValueEx(key, name, 0, _winreg.REG_SZ, application)
        _winreg.CloseKey(key)

    def exists(name):
        """check if an autostart entry exists"""
        key = get_runonce()
        exists = True
        try:
            _winreg.QueryValueEx(key, name)
        except : #WindowsError
            exists = False
        _winreg.CloseKey(key)
        return exists

    def remove(name):
        if not exists(name):
            return

        """delete an autostart entry"""
        key = get_runonce()
        _winreg.DeleteValue(key, name)
        _winreg.CloseKey(key)

    run_cmd = "\"" + os.path.abspath( os.path.join(root_path, "python27", "1.0", "pythonw.exe")) + "\" \"" +\
              os.path.abspath( os.path.join(root_path, "launcher", "start.py")) + "\""
elif sys.platform == 'linux' or sys.platform == 'linux2':
    _xdg_config_home = os.environ.get("XDG_CONFIG_HOME", "~/.config")
    _xdg_user_autostart = os.path.join(os.path.expanduser(_xdg_config_home),
            "autostart")

    def getfilename(name):
        """get the filename of an autostart (.desktop) file"""
        return os.path.join(_xdg_user_autostart, name + ".desktop")

    def add(name, application):
        if not os.path.isdir(os.path.expanduser(_xdg_config_home)):
            logging.warn("autorun linux config path not found:%s", os.path.expanduser(_xdg_config_home))
            return

        if not os.path.isdir(_xdg_user_autostart):
            os.mkdir(_xdg_user_autostart)

        """add a new autostart entry"""
        desktop_entry = "[Desktop Entry]\n"\
            "Name=%s\n"\
            "Exec=%s\n"\
            "Type=Application\n"\
            "Terminal=false\n" % (name, application)
        with open(getfilename(name), "w") as f:
            f.write(desktop_entry)

    def exists(name):
        """check if an autostart entry exists"""
        return os.path.exists(getfilename(name))

    def remove(name):
        """delete an autostart entry"""
        if(exists(name)):
            os.unlink(getfilename(name))

    run_cmd = os.path.abspath( os.path.join(root_path, "start.sh"))
elif sys.platform == 'darwin':
    plist_template = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Label</key>
	<string>com.xxnet.launcher</string>

	<key>LimitLoadToSessionType</key>
	<string>Aqua</string>

	<key>ProgramArguments</key>
	<array>
	  <string>%s</string>
	</array>

	<key>RunAtLoad</key>
	<true/>

	<key>StandardErrorPath</key>
	<string>/dev/null</string>
	<key>StandardOutPath</key>
	<string>/dev/null</string>
</dict>
</plist>"""

    run_cmd = os.path.abspath( os.path.join(root_path, "start.sh"))
    from os.path import expanduser
    home = expanduser("~")

    plist_file_path = os.path.join(home, "Library/LaunchAgents/com.xxnet.launcher.plist")

    def add(name, cmd):
        file_content = plist_template % cmd
        logging.info("create file:%s", plist_file_path)
        with open(plist_file_path, "w") as f:
            f.write(file_content)
    def remove(name):
        if(os.path.isfile(plist_file_path)):
            os.unlink(plist_file_path)
            logging.info("remove file:%s", plist_file_path)
else:
    def add(name, cmd):
        pass
    def remove(name):
        pass

def enable():
    add("XX-Net", run_cmd)

def disable():
    remove("XX-Net")

def test():
    assert not exists("test_xxx")
    try:
        add("test_xxx", "test")
        assert exists("test_xxx")
    finally:
        remove("test_xxx")
    assert not exists("test_xxx")

if __name__ == "__main__":
    test()
