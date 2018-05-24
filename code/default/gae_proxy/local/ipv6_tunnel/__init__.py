
import sys
import platform

from .common import test_teredo

if "arm" in platform.machine():
    from .unknown import state, enable, disable, set_best_server
elif sys.platform == "win32" and platform.release() != "XP":
    from .win10 import state, enable, disable, set_best_server
elif sys.platform.startswith("linux"):
    from .linux import state, enable, disable, set_best_server
elif sys.platform == "darwin":
    from .darwin import state, enable, disable, set_best_server
else:
    from .unknown import state, enable, disable, set_best_server
