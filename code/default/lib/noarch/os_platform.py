import sys
import os


current_path = os.path.dirname(os.path.abspath(__file__))
default_path = os.path.abspath(os.path.join(current_path, os.pardir))
has_desktop = False

if sys.platform.startswith("linux"):
    if os.path.isfile("/system/bin/dalvikvm") or os.path.isfile("/system/bin/dalvikvm64"):
        platform = "android"
        has_desktop = True
    else:
        platform = "linux"
elif sys.platform == "win32":
    has_desktop = True
    platform = "windows"

elif sys.platform == "darwin":
    has_desktop = True
    platform = "mac"
else:
    platform = sys.platform
